"""D5A regression coverage for shared Character seed scope isolation."""
from __future__ import annotations

from dataclasses import asdict
import logging
from types import SimpleNamespace

import numpy as np

from torment_service.character import CharacterSeed, CharacterState, measure_drift
from torment_service.character_drift_runtime import (
    CharacterDriftMeasurementStatus,
    CharacterDriftPostWriteRequest,
    LegacyCharacterDriftRuntime,
)
from torment_service.character_gravity_runtime import CharacterGravityCorrectionResult, CharacterGravityCorrectionStatus
from torment_service.post_write_runtime import (
    FabricPostWriteContext,
    LegacyFabricPostWriteAdapter,
    LegacyFabricPostWriteDependencies,
    PostWriteStorageOutcome,
)


class _RecordingCache(dict[int, np.ndarray]):
    def __init__(self, values: dict[int, np.ndarray]) -> None:
        super().__init__(values)
        self.lookups: list[int] = []

    def get(self, key: int, default=None):  # type: ignore[override]
        self.lookups.append(int(key))
        return super().get(key, default)


class _RecordingMotifs(dict[str, object]):
    def __init__(self, values: dict[str, object]) -> None:
        super().__init__(values)
        self.lookups: list[str] = []

    def get(self, key: str, default=None):  # type: ignore[override]
        self.lookups.append(str(key))
        return super().get(key, default)


class _Store:
    def __init__(self, seed: CharacterSeed, state: CharacterState) -> None:
        self.seed = seed
        self.state = CharacterState.from_dict(state.to_dict())
        self.seed_loads = 0
        self.state_loads = 0
        self.saved: list[CharacterState] = []

    def load_seed(self, _workspace_id: str, seed_id: str) -> CharacterSeed | None:
        self.seed_loads += 1
        return self.seed if seed_id == self.seed.seed_id else None

    def load_state(self, _workspace_id: str, _agent_id: str) -> CharacterState:
        self.state_loads += 1
        return CharacterState.from_dict(self.state.to_dict())

    def save_state(self, _workspace_id: str, state: CharacterState) -> None:
        self.state = CharacterState.from_dict(state.to_dict())
        self.saved.append(self.state)


class _RecordingGravity:
    def __init__(self) -> None:
        self.requests = []

    def correct_for_post_write(self, request):
        self.requests.append(request)
        return CharacterGravityCorrectionResult(CharacterGravityCorrectionStatus.APPLIED, True)


def _seed(*, motif_id: str = "private-seed-motif") -> CharacterSeed:
    return CharacterSeed(
        seed_id="aria-private-seed",
        character_name="Aria",
        seed_text="An enduring private Character seed concept.",
        seed_motif_id=motif_id,
        seed_eids=[1, 2],
        drift_window_steps=50,
    )


def _state() -> CharacterState:
    return CharacterState(
        workspace_id="ws", agent_id="aria", seed_id="aria-private-seed",
        drift_score=-0.72, drift_direction="away_seed", distance_to_seed=0.40,
        drift_history=[(5, -0.72)],
    )


def _entity(*, user_id: str = "aria", born_step: int = 10) -> SimpleNamespace:
    return SimpleNamespace(payload={
        "type": "reflection", "user_id": user_id, "half_life": 30.0,
        "born_step": born_step,
    })


def _request(scope: str) -> CharacterDriftPostWriteRequest:
    return CharacterDriftPostWriteRequest(
        workspace_id="ws", agent_id="aria", current_step=20, stored=True,
        storage_outcome="CREATED_NEW", trigger_scope=scope,
    )


def test_frozen_pre_repair_shared_bare_eid_collision_witness_consumes_unrelated_shared_geometry():
    """The unguarded legacy measurement body shows the old cross-scope leak."""
    seed = _seed()
    shared_cache = _RecordingCache({
        1: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),  # unrelated shared X
        2: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),  # unrelated shared Y
        3: np.asarray((0.0, 1.0, 0.0), dtype=np.float32),
    })
    shared_graph = SimpleNamespace(
        entities={1: _entity(), 2: _entity(), 3: _entity()},
        _emb_by_eid=shared_cache,
    )

    # This is the exact legacy geometry body that was previously reached from
    # a shared post-write trigger.  The selected domain has no seed motif.
    drift = measure_drift(
        graph=shared_graph, motif_registry=SimpleNamespace(motifs=_RecordingMotifs({})),
        coherence_field=None, seed=seed, agent_id="aria", current_step=20,
        previous_state=CharacterState("ws", "aria", seed.seed_id, distance_to_seed=0.0),
    )

    assert shared_cache.lookups == [1, 2, 3, 1, 2]
    assert drift["drift_direction"] == "away_seed"
    assert drift["distance_to_seed"] > 0.03
    assert drift["drift_score"] != 0.0


def test_frozen_pre_repair_shared_motif_id_collision_witness_accepts_shared_geometry():
    """The old body accepted a same-string motif ID across unrelated scopes."""
    seed = _seed(motif_id="motif_x")
    shared_cache = _RecordingCache({
        1: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
        2: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
        3: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
    })
    shared_motifs = _RecordingMotifs({
        "motif_x": SimpleNamespace(centroid_np=lambda: np.asarray((0.0, 1.0, 0.0), dtype=np.float32)),
    })
    drift = measure_drift(
        graph=SimpleNamespace(
            entities={1: _entity(), 2: _entity(), 3: _entity()},
            _emb_by_eid=shared_cache,
        ),
        motif_registry=SimpleNamespace(motifs=shared_motifs), coherence_field=None,
        seed=seed, agent_id="aria", current_step=20,
        previous_state=CharacterState("ws", "aria", seed.seed_id, distance_to_seed=0.0),
    )

    assert shared_motifs.lookups == ["motif_x"]
    assert shared_cache.lookups == [1, 2, 3]
    assert drift["distance_to_seed"] == 1.0
    assert drift["drift_score"] == -1.0
    assert drift["drift_direction"] == "away_seed"


def _assert_shared_scope_noop(*, seed: CharacterSeed, motifs: _RecordingMotifs) -> None:
    state = _state()
    store = _Store(seed, state)
    shared_cache = _RecordingCache({
        1: np.asarray((0.0, 1.0, 0.0), dtype=np.float32),
        2: np.asarray((0.0, 0.0, 1.0), dtype=np.float32),
    })
    runtime = LegacyCharacterDriftRuntime(
        character_enabled=True, drift_every=5, seed_id=seed.seed_id, store=store,
        graph=SimpleNamespace(entities={1: _entity(), 2: _entity()}, _emb_by_eid=shared_cache),
        motif_registry=SimpleNamespace(motifs=motifs),
    )
    before = asdict(store.state)

    result = runtime.measure_for_post_write(_request("shared"))

    assert result.status is CharacterDriftMeasurementStatus.NOT_APPLICABLE_SCOPE
    assert not result.measured and result.seed is None and result.drift is None
    assert store.seed_loads == store.state_loads == 0 and store.saved == []
    assert asdict(store.state) == before
    assert shared_cache.lookups == []
    assert motifs.lookups == []


def test_shared_trigger_eliminates_private_seed_eid_collision_lookup():
    _assert_shared_scope_noop(seed=_seed(), motifs=_RecordingMotifs({}))


def test_shared_trigger_eliminates_private_seed_motif_id_collision_lookup():
    _assert_shared_scope_noop(
        seed=_seed(motif_id="motif_x"),
        motifs=_RecordingMotifs({"motif_x": SimpleNamespace(centroid_np=lambda: np.ones(3))}),
    )


def test_shared_scope_noop_skips_gravity_reflex_and_characterstate_mutation():
    seed = _seed(motif_id="motif_x")
    store = _Store(seed, _state())
    cache = _RecordingCache({1: np.ones(3, dtype=np.float32), 2: np.ones(3, dtype=np.float32)})
    runtime = LegacyCharacterDriftRuntime(
        character_enabled=True, drift_every=5, seed_id=seed.seed_id, store=store,
        graph=SimpleNamespace(entities={1: _entity(), 2: _entity()}, _emb_by_eid=cache),
        motif_registry=SimpleNamespace(motifs=_RecordingMotifs({"motif_x": object()})),
    )
    gravity = _RecordingGravity()
    reflex_calls: list[tuple[str, str, dict]] = []
    owner = SimpleNamespace(
        _log=logging.getLogger("d5a.owner"), _character_enable=True,
        _character_drift_every=5, character_store=store, kernel=SimpleNamespace(embedder=None),
        _last_drift_was_high={},
        drift_reflex_callback=lambda workspace_id, agent_id, drift: reflex_calls.append((workspace_id, agent_id, drift)),
    )
    forbidden = SimpleNamespace()
    adapter = LegacyFabricPostWriteAdapter(LegacyFabricPostWriteDependencies(
        owner=owner, workspace=forbidden, graph=forbidden, world_runtime=forbidden,
        derived_memory_runtime=forbidden, memory_access=forbidden, memory_enumeration=forbidden,
        srg_runtime=forbidden, embedding_dimension=3, identity=SimpleNamespace(seed={"seed_id": seed.seed_id}),
        motif_registry=None, motif_runtime=None, model_state=None, kernel_context=None, agent_key="ws/aria",
        detect_canon_conflict=lambda *_args: (False, 0.0, "unused"),
        proposal_allowed=lambda *_args, **_kwargs: False, random_chance=lambda _value: False,
        save_checkpoint=lambda **_kwargs: None, build_motif_summary=lambda *_args: None,
        build_shard_snapshot=lambda *_args, **_kwargs: None, hivemind_log=logging.getLogger("d5a.hivemind"),
        character_drift_runtime=runtime, character_gravity_runtime=gravity,
    ))
    context = FabricPostWriteContext.make(
        workspace_id="ws", agent_id="aria", scope="shared", chosen_domain="research", step=20,
        storage_outcome=PostWriteStorageOutcome.CREATED_NEW, stored=True, eid=3, created_motif=None,
        motif_ids=(), half_life_days=30.0, summary="shared trigger", embedding=np.zeros(3, dtype=np.float32),
        memory_class="core", memory_type="reflection", strength=.8, confidence=.9,
        promotion_score=.0, stability_delta=.0, tri_mod={}, debug={}, srg_state=None,
        phase_durations={}, state_symbol=None, affect_tag=None, affect_conf=None,
        skip_packet_emission=False,
    )
    before = asdict(store.state)

    adapter._run_character_drift(context)

    assert store.seed_loads == store.state_loads == 0 and store.saved == []
    assert asdict(store.state) == before
    assert gravity.requests == [] and reflex_calls == [] and owner._last_drift_was_high == {}
    assert cache.lookups == []


def test_private_trigger_retains_existing_seed_eid_fallback_and_state_persistence():
    seed = _seed(motif_id="missing-private-motif")
    store = _Store(seed, CharacterState("ws", "aria", seed.seed_id, distance_to_seed=0.0))
    cache = _RecordingCache({
        1: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
        2: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
        3: np.asarray((1.0, 0.0, 0.0), dtype=np.float32),
    })
    graph = SimpleNamespace(
        entities={
            1: SimpleNamespace(payload={"type": "seed_canon", "user_id": "aria", "born_step": 0}),
            2: _entity(), 3: _entity(),
        },
        _emb_by_eid=cache,
    )
    runtime = LegacyCharacterDriftRuntime(
        character_enabled=True, drift_every=5, seed_id=seed.seed_id, store=store,
        graph=graph, motif_registry=SimpleNamespace(motifs=_RecordingMotifs({})),
    )

    result = runtime.measure_for_post_write(_request("private"))

    assert result.status is CharacterDriftMeasurementStatus.MEASURED
    assert result.measured and result.drift is not None
    assert cache.lookups == [2, 3, 1, 2]
    assert store.seed_loads == store.state_loads == 1 and len(store.saved) == 1
    assert store.state.drift_history[-1][0] == 20
