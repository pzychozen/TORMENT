"""P9D-I3C offline characterization of query/external-owner composition.

The tests preserve the single existing Fabric query owner.  They use only
synthetic SQLite cores and temporary legacy data directories; no service,
provider, real root, or post-write migration path is involved.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.fabric import TormentFabric
from torment_service.query_read_model import (
    LegacyQualifiedQueryReadModel,
    NativeQualifiedQueryReadModel,
    NativeQueryReadRefused,
    NativeQuerySnapshotReadRefused,
)
from torment_service.public_runtime import NativePublicOperationRefused
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.native_srg_runtime import NativeSRGProcessState

from tests.test_7g5e4e_native_query_read_model import (
    _Embedder,
    _RecoveredRuntime,
    _legacy_graph,
    _legacy_registry,
    _memory,
    _representation,
    _scope,
    qualified_models,
)
from tests.test_7g5e4e_query_cognition_parity import fabric_models
from tests.test_p9d_i3b0_native_materialization_fencing import (
    _native_runtime as _native_public_runtime,
)


def _paired_query(fabric, native_model, query_text: str, **kwargs):
    legacy = fabric.query("orchard", "aria", query_text, **kwargs)
    native = fabric._query_with_read_model(
        "orchard", "aria", query_text, read_model=native_model, **kwargs,
    )
    assert native == legacy
    return native


def _nested_srg_compatibility_patch(fabric, monkeypatch, state: dict[str, object]):
    """Retain the historical nested-only breathing gate in a synthetic hit."""
    original = fabric._query_read_hits_to_compatibility

    def patched(hits, *, read_model):
        values = original(hits, read_model=read_model)
        for value in values:
            value.pop("srg", None)
            value["payload"] = {"srg": dict(state)}
        return values

    monkeypatch.setattr(fabric, "_query_read_hits_to_compatibility", patched)


def test_p9d_i3c_non_contiguous_eid_order_is_numeric_not_adoption_order(
    qualified_models, tmp_path,
):
    """A missing EID and a late R2 update cannot perturb candidate order."""
    legacy, native, native_embedder, _legacy_embedders = qualified_models
    connection = native._a3_fixture_connection
    idempotency = native._a3_fixture_idempotency
    runtime = native._a3_fixture_runtime
    scope = _scope(
        connection,
        runtime.scopes[0].core_database_path,
        runtime.native_core_id,
        kind="PRIVATE_AGENT",
        qualifier="order-witness",
        idempotency=idempotency,
    )
    rows = tuple(
        _memory(connection, scope, idempotency, label, (1.0, 0.0, 0.0), pending=pending)
        for label, pending in (
            ("first", False),
            ("middle", False),
            ("unusable-gap", True),
            ("higher", False),
        )
    )
    assert [source.eid for source, _representation_state in rows] == [0, 1, 2, 3]

    # The middle candidate receives a new current revision only after the
    # higher EID exists.  Its durable runtime position and EID must not move.
    middle_r2 = NativeMemoryCompatibilityFacade(connection).patch_memory_state(
        legacy_source_namespace_id=scope.memory_runtime_scope.legacy_source_namespace_id,
        eid=1,
        patch={"reinforcement_count": 9, "fixture_tag": "middle-r2"},
        idempotency_namespace_id=idempotency,
        idempotency_key="i3c:order-witness:middle-r2",
        expected_revision_id=rows[1][0].revision_id,
    )
    _representation(
        connection, middle_r2, idempotency, "i3c:order-witness:middle-r2",
        (1.0, 0.0, 0.0), publish=True,
    )
    current_rows = (rows[0], (middle_r2, rows[1][1]), rows[2], rows[3])
    graph = _legacy_graph(
        tmp_path, connection, scope,
        tuple((source, (1.0, 0.0, 0.0)) for source, _state in current_rows),
        _Embedder(),
    )
    model = None
    try:
        # EID 2 has a pending native representation.  The equivalent legacy
        # graph has no usable vector for it, yielding a non-contiguous
        # candidate set [0, 1, 3].
        graph._emb_by_eid.pop(2)
        graph._rebuild_matrix()
        assert graph._eid_list == [0, 1, 3]

        descriptor = SimpleNamespace(payload={"lanes": [
            *runtime.descriptor.payload["lanes"],
            {"plan": {
                "scope_kind": "PRIVATE_AGENT",
                "agent_id": "order-witness",
                "motif_domain_id": "personal",
            }},
        ]})
        recovered = _RecoveredRuntime(
            "orchard", runtime.native_core_id, runtime.representation_lane,
            (*runtime.scopes, scope), descriptor,
        )
        model = NativeQualifiedQueryReadModel(recovered, embedder=native_embedder)
        legacy_order = LegacyQualifiedQueryReadModel(
            "orchard",
            private_graphs={"order-witness": graph},
            shared_graphs={
                domain_id: lane._graph
                for domain_id, lane in legacy._shared.items()
            },
            motif_registries=legacy._registries,
            private_motif_domains={"order-witness": "personal"},
            shared_domain_order=legacy.domain_ids(),
        )
        legacy_hits = legacy_order.private_lane("orchard", "order-witness").search(
            "eid ordering", top_k=3,
        )
        native_lane = model.private_lane("orchard", "order-witness")
        native_hits = native_lane.search("eid ordering", top_k=3)
        assert [item.memory_identity.eid for item in legacy_hits] == [0, 1, 3]
        assert [item.memory_identity.eid for item in native_hits] == [0, 1, 3]
        assert [row.eid for row in native_lane._runtime.snapshot.rows] == [0, 1, 3]
        assert native_hits[1].compatibility_hit["reinforcement_count"] == 9
    finally:
        if model is not None:
            model.close()
        graph.close()


def test_p9d_i3c_first_snapshot_rebuild_refusal_reaches_public_boundary(
    fabric_models, tmp_path, monkeypatch,
):
    """The first native cache rebuild cannot be relabeled as an empty query."""
    _fabric, native_model, _embedder, _legacy_embedders = fabric_models
    lane = native_model.private_lane("orchard", "aria")
    runtime = lane._runtime

    def unrebuildable(*_args, **_kwargs):
        raise SubstrateInvariantViolation("synthetic malformed vector rebuild")

    monkeypatch.setattr(runtime, "_build_snapshot", unrebuildable)
    with pytest.raises(NativeQuerySnapshotReadRefused, match="candidate-rebuild-failed"):
        lane.search("first native snapshot")

    root, public_runtime = _native_public_runtime(tmp_path / "public", monkeypatch)

    @contextmanager
    def failing_context(**_kwargs):
        yield native_model

    monkeypatch.setattr(public_runtime.native_owner, "open_query_context", failing_context)
    try:
        with pytest.raises(
            NativePublicOperationRefused,
            match="qualified read evidence is unavailable",
        ):
            public_runtime.query("orchard", "aria", "first native snapshot")
    finally:
        from torment_service.public_runtime import close_public_runtime

        close_public_runtime(root)


def test_p9d_i3c_zero_budget_does_not_claim_unused_lane_currentness(
    fabric_models, monkeypatch,
):
    """An unused lane is not read merely to discover its stale snapshot state."""
    fabric, native_model, _embedder, _legacy_embedders = fabric_models
    runtime = native_model.private_lane("orchard", "aria")._runtime
    calls = 0

    def unrebuildable(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise SubstrateInvariantViolation("unused lane should not rebuild")

    monkeypatch.setattr(runtime, "_build_snapshot", unrebuildable)
    result = fabric._query_with_read_model(
        "orchard", "aria", "unused native lane", read_model=native_model,
        memory_plan={"top_k_by_lane": {"core": 0, "relational": 0, "deep": 0}},
    )
    assert result["results"] == []
    assert calls == 0


def test_p9d_i3c_malformed_vector_has_a_documented_asymmetric_disposition(
    qualified_models, monkeypatch,
):
    """Legacy can expose NaN scores; qualified native geometry refuses them."""
    legacy, native, _embedder, _legacy_embedders = qualified_models
    legacy_lane = legacy.private_lane("orchard", "aria")
    graph = legacy_lane._graph
    graph._emb_by_eid[0] = np.asarray((np.nan, 0.0, 0.0), dtype=np.float32)
    graph._rebuild_matrix()
    legacy_hits = legacy_lane.search("malformed vector", top_k=2)
    assert legacy_hits
    assert any(np.isnan(item.compatibility_hit["raw_score"]) for item in legacy_hits)

    native_runtime = native.private_lane("orchard", "aria")._runtime

    def malformed_native_geometry():
        raise SubstrateInvariantViolation("qualified vector payload is not finite float32 geometry")

    monkeypatch.setattr(native_runtime, "_enumerate_qualified_vectors", malformed_native_geometry)
    with pytest.raises(NativeQuerySnapshotReadRefused, match="candidate-rebuild-failed"):
        native.private_lane("orchard", "aria").search("malformed vector", top_k=2)


def test_p9d_i3c_srg_overlay_keys_include_lane_namespace_for_colliding_eids(
    qualified_models,
):
    """Two workspaces may reuse EID zero without sharing native SRG overlays."""
    _legacy, orchard_existing, orchard_embedder, _legacy_embedders = qualified_models
    connection = orchard_existing._a3_fixture_connection
    idempotency = orchard_existing._a3_fixture_idempotency
    orchard_runtime = orchard_existing._a3_fixture_runtime
    database_path = orchard_runtime.scopes[0].core_database_path
    private = _scope(
        connection, database_path, orchard_runtime.native_core_id,
        kind="PRIVATE_AGENT", qualifier="aria", idempotency=idempotency,
        workspace_id="grove",
    )
    research = _scope(
        connection, database_path, orchard_runtime.native_core_id,
        kind="SHARED_DOMAIN", qualifier="research", idempotency=idempotency,
        workspace_id="grove",
    )
    grove_source, _ = _memory(
        connection, private, idempotency, "grove-private", (1.0, 0.0, 0.0),
    )
    _memory(connection, research, idempotency, "grove-research", (0.0, 1.0, 0.0))
    shared_process = NativeSRGProcessState()
    orchard = NativeQualifiedQueryReadModel(
        orchard_runtime, embedder=orchard_embedder, srg_process_state=shared_process,
    )
    grove = NativeQualifiedQueryReadModel(
        _RecoveredRuntime(
            "grove", orchard_runtime.native_core_id,
            orchard_runtime.representation_lane, (private, research),
            SimpleNamespace(payload={"lanes": [
                {"plan": {"scope_kind": "PRIVATE_AGENT", "agent_id": "aria", "motif_domain_id": "personal"}},
                {"plan": {"scope_kind": "SHARED_DOMAIN", "domain_id": "research", "motif_domain_id": "research"}},
            ]}),
        ),
        embedder=_Embedder(), srg_process_state=shared_process,
    )
    try:
        orchard_hit = next(
            item
            for item in orchard.private_lane("orchard", "aria").search("srg collision", top_k=2)
            if item.memory_identity.eid == 0
        )
        grove_hit = grove.private_lane("grove", "aria").search("srg collision", top_k=1)[0]
        assert orchard_hit.memory_identity.eid == grove_hit.memory_identity.eid == grove_source.eid == 0

        orchard_state = {"R_band": 1, "heartbeat_class": "A", "overlay": "orchard"}
        grove_state = {"R_band": 9, "heartbeat_class": "B", "overlay": "grove"}
        orchard.replace_srg_state(orchard_hit, orchard_state)
        assert orchard.effective_srg_state(orchard_hit) == orchard_state
        assert grove.effective_srg_state(grove_hit) != orchard_state

        grove.replace_srg_state(grove_hit, grove_state)
        assert orchard.effective_srg_state(orchard_hit) == orchard_state
        assert grove.effective_srg_state(grove_hit) == grove_state
    finally:
        orchard.close()
        grove.close()


def test_p9d_i3c_srg_all_scoring_modifiers_have_native_explain_parity(
    fabric_models, monkeypatch,
):
    """Same-band, crystal, and heartbeat-A retain their literal multipliers."""
    fabric, native_model, _embedder, _legacy_embedders = fabric_models
    source = {
        "R_band": 4,
        "is_crystal": True,
        "heartbeat_class": "A",
        "L_amplitude": 0.25,
        "L_phase": 0.1,
    }
    fabric._srg_enable = True
    fabric._srg_last_ingest_band_by_agent[("orchard", "aria")] = 4
    original = native_model.effective_srg_state

    def effective_with_all_modifiers(hit):
        state = dict(original(hit) or {})
        state.update(source)
        return state

    monkeypatch.setattr(native_model, "effective_srg_state", effective_with_all_modifiers)
    _nested_srg_compatibility_patch(fabric, monkeypatch, source)
    result = _paired_query(fabric, native_model, "all SRG modifiers", explain=True)
    explain = result["results"][0]["explain"]
    assert explain["srg_same_band_bonus"] == pytest.approx(1.08)
    assert explain["srg_crystal_bonus"] == pytest.approx(1.05)
    assert explain["srg_heartbeat_bonus"] == pytest.approx(1.03)
    assert explain["srg_total_multiplier"] == pytest.approx(1.08 * 1.05 * 1.03)


def test_p9d_i3c_native_srg_refusal_is_not_swallowed_by_optional_scoring(
    fabric_models, monkeypatch,
):
    """A named native SRG read refusal remains a qualified query refusal."""
    fabric, native_model, _embedder, _legacy_embedders = fabric_models
    fabric._srg_enable = True

    def refuse(_hit):
        raise NativeQueryReadRefused("synthetic native SRG currentness refusal")

    monkeypatch.setattr(native_model, "effective_srg_state", refuse)
    with pytest.raises(NativeQueryReadRefused, match="SRG currentness refusal"):
        fabric._query_with_read_model(
            "orchard", "aria", "native SRG refusal", read_model=native_model,
        )


def test_p9d_i3c_character_absence_and_store_failure_are_equally_fail_soft(
    fabric_models, monkeypatch,
):
    """The existing external Character boundary does not expose failure detail."""
    fabric, native_model, _embedder, _legacy_embedders = fabric_models
    identity = fabric.ident_store.load("orchard", "aria")
    assert identity is not None
    identity.seed = {"seed_id": "missing-character-seed"}
    fabric.ident_store.save(identity)
    fabric._character_enable = True

    absent = _paired_query(fabric, native_model, "character boundary")
    assert "character_context" not in absent

    def unreadable_seed(*_args, **_kwargs):
        raise OSError("synthetic CharacterStore read failure")

    monkeypatch.setattr(fabric.character_store, "load_seed", unreadable_seed)
    unreadable = _paired_query(fabric, native_model, "character boundary")
    assert "character_context" not in unreadable
    assert unreadable == absent


def _legacy_breathing_fixture(data_dir: Path, *, workspace_id: str, agent_id: str):
    fabric = TormentFabric(data_dir=str(data_dir))
    fabric.get_workspace(workspace_id)
    fabric.create_agent(workspace_id, agent_id)
    eid = fabric.ingest(
        workspace_id=workspace_id, agent_id=agent_id,
        text="I3C nested breathing witness", step=10,
    )["eid"]
    graph = fabric.private_graphs[fabric._agent_key(workspace_id, agent_id)]
    entity = graph.entities[eid]
    baseline = deepcopy(entity.payload["srg"])
    baseline.update({"is_crystal": False, "R_band": 4, "heartbeat_class": "A"})
    entity.payload["srg"] = deepcopy(baseline)
    entity.payload["payload"] = {"srg": deepcopy(baseline)}
    # Fixture setup is an existing durable legacy fact.  Subsequent tests can
    # therefore distinguish query-only mutation from a later write of it.
    graph.update_payload(eid, {})
    fabric._srg_enable = True
    fabric._srg_last_ingest_band_by_agent[(workspace_id, agent_id)] = 4
    return fabric, graph, eid, baseline


def _query_legacy_breathing(fabric, workspace_id: str, agent_id: str):
    return fabric.query(
        workspace_id, agent_id, "I3C nested breathing witness", top_k=12, explain=True,
    )


def test_p9d_i3c_legacy_breathing_same_process_restart_and_later_write_behavior(
    tmp_path, monkeypatch,
):
    """Pin legacy live-payload mutation and exactly which later writes persist it."""
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "1")

    no_write_dir = tmp_path / "legacy-no-write"
    fabric, graph, eid, baseline = _legacy_breathing_fixture(
        no_write_dir, workspace_id="orchard", agent_id="aria",
    )
    try:
        first = _query_legacy_breathing(fabric, "orchard", "aria")
        first_state = deepcopy(graph.entities[eid].payload["srg"])
        assert first_state != baseline
        second = _query_legacy_breathing(fabric, "orchard", "aria")
        # The next query observes the live top-level state for scoring, but
        # breathing still evolves from the untouched nested source.  Thus the
        # mutation is visible without a second increment of the stored step.
        assert graph.entities[eid].payload["srg"] == first_state
        first_hit = next(item for item in first["results"] if item["eid"] == eid)
        second_hit = next(item for item in second["results"] if item["eid"] == eid)
        assert first_hit["explain"]["srg_same_band_bonus"] == pytest.approx(1.08)
        assert second_hit["srg"] == first_state
        assert second_hit["explain"]["srg_heartbeat_bonus"] == pytest.approx(1.03)
    finally:
        fabric.close()
    restarted = TormentFabric(data_dir=str(no_write_dir))
    try:
        restarted.get_workspace("orchard")
        restarted.create_agent("orchard", "aria")
        restored = restarted.private_graphs[restarted._agent_key("orchard", "aria")].entities[eid]
        assert restored.payload["srg"] == baseline
    finally:
        restarted.close()

    unrelated_dir = tmp_path / "legacy-unrelated-write"
    fabric, graph, eid, baseline = _legacy_breathing_fixture(
        unrelated_dir, workspace_id="orchard", agent_id="aria",
    )
    try:
        _query_legacy_breathing(fabric, "orchard", "aria")
        assert graph.entities[eid].payload["srg"] != baseline
        # Creating and flushing another entity does not serialize the target's
        # query-only live mutation.
        fabric.ingest(
            workspace_id="orchard", agent_id="aria", text="unrelated lawful write", step=11,
        )
    finally:
        fabric.close()
    restarted = TormentFabric(data_dir=str(unrelated_dir))
    try:
        restarted.get_workspace("orchard")
        restarted.create_agent("orchard", "aria")
        restored = restarted.private_graphs[restarted._agent_key("orchard", "aria")].entities[eid]
        assert restored.payload["srg"] == baseline
    finally:
        restarted.close()

    target_write_dir = tmp_path / "legacy-target-write"
    fabric, graph, eid, _baseline = _legacy_breathing_fixture(
        target_write_dir, workspace_id="orchard", agent_id="aria",
    )
    try:
        _query_legacy_breathing(fabric, "orchard", "aria")
        evolved = deepcopy(graph.entities[eid].payload["srg"])
        # A later ordinary update of the same entity serializes its entire
        # then-current payload, including the pre-existing breathing state.
        graph.update_payload(eid, {"reinforcement_count": 1, "last_reinforced_ts": 12})
    finally:
        fabric.close()
    restarted = TormentFabric(data_dir=str(target_write_dir))
    try:
        restarted.get_workspace("orchard")
        restarted.create_agent("orchard", "aria")
        restored = restarted.private_graphs[restarted._agent_key("orchard", "aria")].entities[eid]
        assert restored.payload["srg"] == evolved
    finally:
        restarted.close()


def test_p9d_i3c_legacy_breathing_is_scoped_by_workspace_and_agent(
    tmp_path, monkeypatch,
):
    """Same local EIDs in two workspaces cannot share a live SRG mutation."""
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "1")
    fabric = TormentFabric(data_dir=str(tmp_path / "legacy-workspaces"))
    try:
        eids = {}
        for workspace in ("alpha", "grove"):
            fabric.get_workspace(workspace)
            fabric.create_agent(workspace, "aria")
            eid = fabric.ingest(
                workspace_id=workspace, agent_id="aria",
                text="workspace-scoped breathing", step=10,
            )["eid"]
            graph = fabric.private_graphs[fabric._agent_key(workspace, "aria")]
            state = deepcopy(graph.entities[eid].payload["srg"])
            state.update({"is_crystal": False, "R_band": 4, "heartbeat_class": "A"})
            graph.entities[eid].payload["srg"] = deepcopy(state)
            graph.entities[eid].payload["payload"] = {"srg": deepcopy(state)}
            fabric._srg_last_ingest_band_by_agent[(workspace, "aria")] = 4
            eids[workspace] = eid
        fabric._srg_enable = True

        alpha_graph = fabric.private_graphs[fabric._agent_key("alpha", "aria")]
        grove_graph = fabric.private_graphs[fabric._agent_key("grove", "aria")]
        alpha_before = deepcopy(alpha_graph.entities[eids["alpha"]].payload["srg"])
        grove_before = deepcopy(grove_graph.entities[eids["grove"]].payload["srg"])
        _query_legacy_breathing(fabric, "alpha", "aria")
        assert alpha_graph.entities[eids["alpha"]].payload["srg"] != alpha_before
        assert grove_graph.entities[eids["grove"]].payload["srg"] == grove_before
    finally:
        fabric.close()


def test_p9d_i3c_native_breathing_overlay_is_same_process_only(
    fabric_models, monkeypatch,
):
    """Native query breathing keeps its existing overlay-only durability scope."""
    fabric, native_model, native_embedder, _legacy_embedders = fabric_models
    from torment_service.srg_engine import SRGMemoryState

    source = SRGMemoryState(
        R=0.1, R_band=4, L_amplitude=0.25, L_phase=0.1,
        heartbeat_class="A", is_crystal=False,
    ).to_dict()
    fabric._srg_enable = True
    fabric._srg_last_ingest_band_by_agent[("orchard", "aria")] = 4
    _nested_srg_compatibility_patch(fabric, monkeypatch, source)
    before = native_model.private_lane("orchard", "aria").search("native breathing", top_k=1)[0]
    # The synthetic A2 durable payload deliberately contains only the fields
    # needed for read-source parity.  Install a full pre-existing process
    # overlay to characterize the real SRG breathing state machine without
    # pretending that this is a durable native successor.
    native_model.replace_srg_state(before, source)
    baseline = native_model.effective_srg_state(before)
    assert baseline is not None

    fabric._query_with_read_model(
        "orchard", "aria", "native breathing", read_model=native_model,
        memory_plan={"top_k_by_lane": {"core": 1, "relational": 0, "deep": 0}},
    )
    after = native_model.private_lane("orchard", "aria").search("native breathing", top_k=1)[0]
    evolved = native_model.effective_srg_state(after)
    assert evolved is not None and evolved != baseline
    assert evolved["srg_step"] >= 1

    restarted = NativeQualifiedQueryReadModel(
        native_model._a3_fixture_runtime, embedder=native_embedder,
    )
    try:
        fresh = restarted.private_lane("orchard", "aria").search("native breathing", top_k=1)[0]
        assert restarted.effective_srg_state(fresh) != evolved
    finally:
        restarted.close()


def test_p9d_i3c_live_legacy_motif_insertion_remains_an_i4_order_witness(tmp_path):
    """A restarted registry is lexical, while new live motifs append in creation order."""
    registry = _legacy_registry(
        type("Graph", (), {"data_dir": str(tmp_path), "entities": {}, "_shard_reader": None,
                             "_a3_fixture_embedding_refs": {}})(),
        "research",
        [
            ("zeta", 1, (-1.0, 0.0, 0.0), 0.5, 10),
            ("alpha", 2, (1.0, 0.0, 0.0), 0.5, 10),
        ],
    )
    registry.save()
    reloaded = registry.__class__(str(tmp_path), "orchard", "research")
    try:
        assert list(reloaded.motifs) == ["alpha", "zeta"]
        created, new_id = reloaded.attach_or_create(
            np.asarray((0.0, 0.0, 1.0), dtype=np.float32),
            memory_eid=99, agent_id="aria", summary="live insertion witness",
        )
        assert created == [new_id]
        assert new_id is not None
        assert list(reloaded.motifs) == ["alpha", "zeta", new_id]
        assert new_id < "zeta"  # lexical re-sorting would have changed the witness.
        # The active and centroid loops both consume the same live dict order;
        # native currently reconstructs only durable motif aliases, so I4 must
        # preserve an explicit live-order witness before native post-write.
        assert reloaded.active(top_k=3)
        assert np.isfinite(reloaded.domain_centroid(3)).all()
    finally:
        # Registry has no close operation; keeping the explicit local lifetime
        # documents that this is a stopped, synthetic legacy-only witness.
        pass
