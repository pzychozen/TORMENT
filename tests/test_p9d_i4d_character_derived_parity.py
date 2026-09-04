"""P9D-I4D private native-public Character and derived-tail qualification."""
from __future__ import annotations

from pathlib import Path

import pytest

from torment_service.character import CharacterSeed, CharacterState, CharacterStore
from torment_service.post_write_runtime import LegacyFabricPostWriteAdapter
from torment_service.public_runtime import close_public_runtime
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.native_character_gravity_runtime import (
    NativeCharacterGravityCorrectionRuntime,
)
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.native_public_ingest_executor import NativePublicIngestRequest

from tests.test_p9d_i3b0_native_materialization_fencing import _native_runtime


def _request(key: str, text: str, vector: list[float], *, step: int) -> NativePublicIngestRequest:
    return NativePublicIngestRequest(
        workspace_id="orchard", agent_id="aria", text=text, public_mutation_key=key,
        step=step, domain_id="personal", supplied_embedding=vector,
    )


def _enable_character(
    runtime,
    *,
    seed_eid: int,
    seed_motif_id: str,
    threshold: float = 0.10,
) -> CharacterSeed:
    """Install only synthetic external Character facts under the test root."""
    fabric = runtime.cognition_fabric
    identity = fabric.ident_store.load("orchard", "aria")
    assert identity is not None
    identity.seed.update({
        "seed_id": "i4d-aria-v1",
        "character_name": "Aria",
        "seed_text": "Aria is patient and enduring. Aria remains carefully grounded.",
    })
    fabric.ident_store.save(identity)
    seed = CharacterSeed(
        seed_id="i4d-aria-v1",
        character_name="Aria",
        seed_text=str(identity.seed["seed_text"]),
        seed_motif_id=seed_motif_id,
        seed_eids=[seed_eid],
        drift_window_steps=500,
        drift_correction_threshold=threshold,
    )
    fabric.character_store.save_seed("orchard", seed)
    fabric.character_store.save_state(
        "orchard", CharacterState("orchard", "aria", seed.seed_id, distance_to_seed=0.0),
    )
    fabric._character_enable = True
    fabric._character_drift_every = 1
    return seed


def test_i4d_full_public_created_memory_updates_external_character_state_and_gravity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A qualified CREATE reaches state, correction, then the existing reflex edge."""
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        runtime.cognition_fabric._hivemind_enable = False
        seed_result = runtime._executor.execute(  # noqa: SLF001 - public boundary fixture setup
            _request("i4d-character-seed", "character seed geometry", [1.0, 0.0, 0.0], step=1)
        )
        assert seed_result["stored"] is True and seed_result["motifs"]
        seed = _enable_character(
            runtime,
            seed_eid=int(seed_result["eid"]),
            seed_motif_id=str(seed_result["motifs"][0]),
        )
        corrections: list[object] = []
        reflexes: list[tuple[str, str, dict[str, object]]] = []
        original_correction = NativeCharacterGravityCorrectionRuntime.correct_for_post_write

        def observe_correction(adapter, request):
            corrections.append(request)
            return original_correction(adapter, request)

        runtime.cognition_fabric.drift_reflex_callback = (
            lambda workspace_id, agent_id, drift: reflexes.append(
                (workspace_id, agent_id, dict(drift))
            )
        )
        monkeypatch.setattr(
            NativeCharacterGravityCorrectionRuntime,
            "correct_for_post_write",
            observe_correction,
        )

        result = runtime._executor.execute(  # noqa: SLF001 - required public-executor boundary
            _request("i4d-character-drift", "character receives an orthogonal memory", [0.0, 1.0, 0.0], step=2)
        )

        assert result["stored"] is True and result["reinforced"] is False
        state = runtime.cognition_fabric.character_store.load_state("orchard", "aria")
        assert state is not None and state.seed_id == seed.seed_id
        assert state.drift_history and state.drift_history[-1][0] == 2
        assert state.drift_score < -seed.drift_correction_threshold
        assert state.drift_direction == "away_seed"
        assert len(corrections) == 1
        assert len(reflexes) == 1
        reflex_workspace, reflex_agent, reflex_drift = reflexes[0]
        assert (reflex_workspace, reflex_agent) == ("orchard", "aria")
        assert reflex_drift["drift_score"] == pytest.approx(state.drift_score)
        assert reflex_drift["distance_to_seed"] == pytest.approx(state.distance_to_seed)
        scope = runtime._active_runtime().lookup_private("aria").fabric_routing_scope  # noqa: SLF001
        with open_existing_native_core_connection(runtime.native_owner.authority_facts.core_database_path) as opened:
            views = NativePostWriteMemoryAccess(
                opened.connection,
                legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
                expected_dimension=3,
            ).list_current()
        assert sum(view.payload.get("type") == "drift_correction" for view in views) == 1

        replay = runtime._executor.execute(  # noqa: SLF001 - receipt replay must not re-enter Character
            _request("i4d-character-drift", "character receives an orthogonal memory", [0.0, 1.0, 0.0], step=2)
        )
        assert replay == result and len(corrections) == 1 and len(reflexes) == 1

        # A fresh external owner reads the same durable JSON state; the
        # qualified Character runtime owns no SQLite state shadow to rebuild.
        reloaded = CharacterStore(str(root)).load_state("orchard", "aria")
        assert reloaded is not None
        assert reloaded.to_dict() == state.to_dict()
    finally:
        close_public_runtime(root)


def test_i4d_full_public_character_boundary_observes_outcomes_but_canonical_failure_stops_before_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CREATE, reinforcement, and NO_WRITE retain their legacy adapter gates."""
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        seen: list[str] = []
        original = LegacyFabricPostWriteAdapter._run_character_drift

        def observe(adapter, context):
            seen.append(context.storage_outcome.value)
            return original(adapter, context)

        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_character_drift", observe)
        create = _request("i4d-gate-create", "outcome gate source", [1.0, 0.0, 0.0], step=1)
        reinforce = _request("i4d-gate-reinforce", "outcome gate source", [1.0, 0.0, 0.0], step=2)
        no_write = _request("i4d-gate-no-write", "", [1.0, 0.0, 0.0], step=3)
        failed = _request("i4d-gate-canonical-failure", "canonical failure", [0.0, 1.0, 0.0], step=4)

        assert runtime._executor.execute(create)["stored"] is True  # noqa: SLF001
        assert runtime._executor.execute(reinforce)["reinforced"] is True  # noqa: SLF001
        assert runtime._executor.execute(no_write)["stored"] is False  # noqa: SLF001
        failure = runtime._executor.execute(  # noqa: SLF001
            failed, _test_storage_stop_after="precommit_canonical_failure",
        )

        assert failure["failure_code"] == "canonical_commit_failed"
        assert seen == ["CREATED_NEW", "REINFORCED_EXISTING", "NO_WRITE"]
    finally:
        close_public_runtime(root)


def test_i4d_full_public_mood_drift_is_private_durable_and_replay_stable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mood drift retains the private derived child and external affect owner."""
    monkeypatch.setenv("TORMENT_MOOD_DRIFT_MIN_GAP_STEPS", "1")
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        runtime.cognition_fabric._hivemind_enable = False
        runtime._side_store.save_affect_state(  # noqa: SLF001 - retained external owner fixture
            workspace_id="orchard",
            agent_id="aria",
            state={"last_tag": "sad", "last_conf": 0.8, "last_step": 1, "drift_hist": []},
        )
        request = _request(
            "i4d-mood-success",
            "I feel calm and grounded today.",
            [1.0, 0.0, 0.0],
            step=2,
        )

        result = runtime._executor.execute(request)  # noqa: SLF001 - required public-executor boundary
        state = runtime._side_store.load_affect_state(workspace_id="orchard", agent_id="aria")  # noqa: SLF001

        assert result["stored"] is True
        assert state["last_tag"] == "calm" and state["last_step"] == 2
        assert state["drift_hist"] == [{"from": "sad", "to": "calm", "step": 2, "conf": pytest.approx(2 / 3)}]
        scope = runtime._active_runtime().lookup_private("aria").fabric_routing_scope  # noqa: SLF001
        with open_existing_native_core_connection(runtime.native_owner.authority_facts.core_database_path) as opened:
            views = NativePostWriteMemoryAccess(
                opened.connection,
                legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
                expected_dimension=3,
        ).list_current()
        moods = [view for view in views if view.payload.get("type") == "mood_drift"]
        assert len(moods) == 1
        assert (moods[0].payload["mood_from"], moods[0].payload["mood_to"]) == ("sad", "calm")

        assert runtime._executor.execute(request) == result  # noqa: SLF001 - receipt replay
        neutral = runtime._executor.execute(  # noqa: SLF001 - ordinary later CREATE
            _request("i4d-mood-miss", "an ordinary neutral memory", [0.0, 1.0, 0.0], step=3)
        )
        assert neutral["stored"] is True
        with open_existing_native_core_connection(runtime.native_owner.authority_facts.core_database_path) as opened:
            later_views = NativePostWriteMemoryAccess(
                opened.connection,
                legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
                expected_dimension=3,
            ).list_current()
        assert sum(view.payload.get("type") == "mood_drift" for view in later_views) == 1
    finally:
        close_public_runtime(root)


def test_i4d_mood_affect_state_failure_is_soft_after_the_canonical_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The retained external state save cannot withhold a qualified mood child."""
    monkeypatch.setenv("TORMENT_MOOD_DRIFT_MIN_GAP_STEPS", "1")
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        runtime.cognition_fabric._hivemind_enable = False
        runtime._side_store.save_affect_state(  # noqa: SLF001 - retained external owner fixture
            workspace_id="orchard",
            agent_id="aria",
            state={"last_tag": "sad", "last_conf": 0.8, "last_step": 1, "drift_hist": []},
        )
        monkeypatch.setattr(
            runtime._side_store,  # noqa: SLF001 - force the retained owner failure boundary
            "save_affect_state",
            lambda **_kwargs: (_ for _ in ()).throw(OSError("forced affect owner failure")),
        )

        result = runtime._executor.execute(  # noqa: SLF001 - required public-executor boundary
            _request("i4d-mood-failure", "I feel calm and grounded today.", [1.0, 0.0, 0.0], step=2)
        )

        assert result["stored"] is True
        scope = runtime._active_runtime().lookup_private("aria").fabric_routing_scope  # noqa: SLF001
        with open_existing_native_core_connection(runtime.native_owner.authority_facts.core_database_path) as opened:
            views = NativePostWriteMemoryAccess(
                opened.connection,
                legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
                expected_dimension=3,
            ).list_current()
        assert sum(view.payload.get("type") == "mood_drift" for view in views) == 1
    finally:
        close_public_runtime(root)
