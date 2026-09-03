"""P9D-I3B native query-read parity over the frozen qualified adapters."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.fabric import dominant_thread
from torment_service.motif_decision import MotifReadModel
from torment_service.motifs import Motif, MotifRegistry
from torment_service.query_read_model import (
    LegacyQualifiedQueryReadModel,
    NativeQualifiedQueryReadModel,
    NativeQuerySnapshotReadRefused,
)

# These are intentionally imported as fixture registrations.  The established
# A2/A3 fixtures build the qualified synthetic core and the one query owner;
# I3B adds observations without duplicating that setup.
from tests.test_7g5e4e_native_query_read_model import (
    _Embedder,
    _RecoveredRuntime,
    _create_motif,
    _legacy_graph,
    _legacy_registry,
    _memory,
    _scope,
    qualified_models,
)
from tests.test_7g5e4e_query_cognition_parity import fabric_models
from tests.test_substrate_migration_runtime_zero_member_motif_projection import (
    _context as zero_member_context,
)


def _paired_query(fabric, native_model, query_text: str, **kwargs):
    """Exercise the one existing query owner over both read adapters."""
    legacy = fabric.query("orchard", "aria", query_text, **kwargs)
    native = fabric._query_with_read_model(
        "orchard", "aria", query_text, read_model=native_model, **kwargs,
    )
    assert native == legacy
    return native


def test_p9d_i3_domain_rank_order_parity(fabric_models):
    """Zero-score ties retain declared domain order, including an override."""
    fabric, native_model, native_embedder, legacy_embedders = fabric_models
    original_native = native_embedder.vector.copy()
    original_legacy = [embedder.vector.copy() for embedder in legacy_embedders]
    try:
        # A zero query produces the exact 0.0 score tie considered by I3B.
        # DomainRouter's stable sort must retain the declared research,
        # engineering, archive order before the top-two truncation.
        native_embedder.vector = np.zeros(3, dtype=np.float32)
        for embedder in legacy_embedders:
            embedder.vector = np.zeros(3, dtype=np.float32)
        result = _paired_query(
            fabric,
            native_model,
            "equal domain geometry",
            top_k=2,
            memory_plan={"top_k_by_lane": {"core": 0, "relational": 0, "deep": 0}},
        )
        assert [item["id"] for item in result["domains"]] == ["research", "engineering"]
        assert result["domain_used"] == ["research", "engineering"]

        override = _paired_query(
            fabric,
            native_model,
            "equal domain geometry",
            top_k=2,
            domain_id="archive",
            memory_plan={"top_k_by_lane": {"core": 0, "relational": 0, "deep": 0}},
        )
        assert override["domain_used"] == ["archive", "research"]
    finally:
        native_embedder.vector = original_native
        for embedder, original in zip(legacy_embedders, original_legacy, strict=True):
            embedder.vector = original


def test_p9d_i3_vector_normalization_and_decay_parity(qualified_models):
    """Native matrix rows preserve the legacy EID witness through top-k ties."""
    legacy, native, native_embedder, legacy_embedders = qualified_models
    legacy_lane = legacy.private_lane("orchard", "aria")
    native_lane = native.private_lane("orchard", "aria")
    graph = legacy_lane._graph  # fixture-owned differential witness

    # Give the two eligible vectors equal cosine against one query.  The
    # selection law (argpartition/argsort) is shared, so matching row order is
    # the observable condition at the top-k boundary.
    first = graph._emb_by_eid[0]
    second = graph._emb_by_eid[1]
    difference = first - second
    query = np.asarray((-difference[1], difference[0], 0.0), dtype=np.float32)
    assert np.isclose(float(np.dot(first, query)), float(np.dot(second, query)))
    original_native = native_embedder.vector.copy()
    original_legacy = legacy_embedders[0].vector.copy()
    try:
        native_embedder.vector = query
        legacy_embedders[0].vector = query
        expected_tie = legacy_lane.search("equal vector boundary", top_k=1)
        actual_tie = native_lane.search("equal vector boundary", top_k=1)
        assert [item.as_legacy_hit() for item in actual_tie] == [
            item.as_legacy_hit() for item in expected_tie
        ]

        snapshot = native_lane._runtime.snapshot
        assert snapshot is not None
        assert [row.eid for row in snapshot.rows] == graph._eid_list == [0, 1]

        # The second row exercises the existing one-day half-life decay.
        expected = legacy_lane.search("equal vector boundary", top_k=2)
        actual = native_lane.search("equal vector boundary", top_k=2)
        assert [item.as_legacy_hit() for item in actual] == [
            item.as_legacy_hit() for item in expected
        ]
        assert any(item.as_legacy_hit()["decay_factor"] < 1.0 for item in actual)
    finally:
        native_embedder.vector = original_native
        legacy_embedders[0].vector = original_legacy


def test_p9d_i3_motif_geometry_active_order_parity(qualified_models):
    """Persisted legacy motif order and native alias order are the same witness."""
    legacy, native, _native_embedder, _legacy_embedders = qualified_models
    legacy_geometry = legacy.domain_geometry("research")
    native_geometry = native.domain_geometry("research")
    legacy_ids = [item.identity.motif_id for item in legacy_geometry.motifs]
    native_ids = [item.identity.motif_id for item in native_geometry.motifs]

    # MotifRegistry.save uses JSON ``sort_keys=True``; its post-restart
    # iteration is lexical motif ID order.  Native reads the scoped MOTIF_ID
    # aliases in that same durable order, before float reduction.
    assert legacy_ids == native_ids == ["research-hot", "same-id"]
    np.testing.assert_array_equal(native_geometry.centroid, legacy_geometry.centroid)
    assert native.active_motifs("research", top_k=6) == legacy.active_motifs(
        "research", top_k=6
    )


def test_p9d_i3_active_motifs_vs_dominant_thread():
    """Active ranking includes gravity; dominant thread deliberately does not."""
    from torment_service.query_read_model import _active_summary

    gravity_first = MotifReadModel(
        "gravity-first", "research", "gravity first", (1.0, 0.0, 0.0),
        0.55, 128, ("aria",), 1.0, 1, 10,
    )
    raw_strength_first = MotifReadModel(
        "raw-strength-first", "research", "raw strength first", (0.0, 1.0, 0.0),
        0.62, 0, ("aria",), 0.0, 1, 10,
    )
    active = _active_summary(
        ((gravity_first, 0.0), (raw_strength_first, 0.0)), top_k=2,
    )
    assert [item["motif_id"] for item in active] == [
        "gravity-first", "raw-strength-first"
    ]
    assert dominant_thread({"research": active})["motif_id"] == "raw-strength-first"


def test_p9d_i3_zero_member_motif_geometry_active_and_fallback_parity(tmp_path):
    """A certified empty motif remains geometric and active at zero strength."""
    from torment_service.motif_decision import (
        CURRENT_MOTIF_DECISION_POLICY,
        motif_gravity_bonus,
    )
    from torment_service.query_read_model import _active_summary
    from torment_service.substrate.migration import (
        NativeMigrationRuntimeZeroMemberMotifProjectionService,
    )
    from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader

    qualified, facts = zero_member_context(tmp_path, motif_strength=0.0)
    try:
        result = NativeMigrationRuntimeZeroMemberMotifProjectionService(
            facts["connection"]
        ).project_target_compatible_zero_member_motif(facts["request"])
        reader = NativeMotifRuntimeReader(facts["connection"])
        catalog = reader.list_runtime_motifs(
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            domain_id="reflection",
            semantic_scope_id=facts["plan"].target_semantic_scope_id,
        )
        assert len(catalog) == 1
        native_state = catalog[0].read_model
        assert native_state.member_count == 0
        assert reader.list_ordered_current_motif_members(result.motif_object_id) == ()

        # The legacy formula admits a zero-strength centroid with its explicit
        # 1e-6 floor; no synthetic member is required for geometry, gravity,
        # active-context output, or motifless fallback alignment.
        legacy = MotifRegistry(str(tmp_path / "legacy-empty"), "orchard", "reflection")
        legacy.motifs = {
            "motif-b4c": Motif(
                "motif-b4c", "reflection", "qualified empty basin",
                list(facts["raw"]["centroid"]), 0.0, [], ["aria", "boris"],
                0.83, 4, 9,
            )
        }
        native_centroid = reader.domain_centroid(
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            domain_id="reflection",
            dimension=384,
            semantic_scope_id=facts["plan"].target_semantic_scope_id,
        )
        np.testing.assert_array_equal(native_centroid, legacy.domain_centroid(384))
        assert float(np.linalg.norm(native_centroid)) == pytest.approx(1.0)
        weight = max(1e-6, native_state.strength) * (
            1.0 + motif_gravity_bonus(native_state, CURRENT_MOTIF_DECISION_POLICY)
        )
        assert weight > 0.0
        native_active = _active_summary(
            ((native_state, reader.motif_radius(result.motif_object_id, expected_dimension=384)),),
            top_k=1,
        )
        assert native_active == legacy.active(top_k=1)
        # This is the same centroid a motifless hit sees during the existing
        # fallback alignment loop; its non-zero projection makes that fallback
        # semantically live despite having no memberships.
        assert float(np.dot(native_centroid, np.asarray(facts["raw"]["centroid"], dtype=np.float32))) > 0.0
    finally:
        qualified.close()


def test_p9d_i3_explain_decomposition_parity(fabric_models, monkeypatch):
    """The adapter changes storage only; all exposed score components match."""
    fabric, native_model, _native_embedder, _legacy_embedders = fabric_models
    workspace = fabric.get_workspace("orchard")
    workspace.conflicts["research"].add(
        1, 2, 0.91, 0.62, "I3B qualified conflict",
        origin_scope="shared", origin_domain_id="research",
    )
    original = fabric._query_read_hits_to_compatibility

    def mark_canonical(hits, *, read_model):
        values = original(hits, read_model=read_model)
        for value in values:
            if value.get("scope") == "shared" and value.get("domain_id") == "research":
                value["canon"] = True
        return values

    monkeypatch.setattr(fabric, "_query_read_hits_to_compatibility", mark_canonical)
    result = _paired_query(
        fabric,
        native_model,
        "qualified explain decomposition",
        top_k=6,
        domain_id="research",
        explain=True,
        continuity_debug=True,
        memory_plan={
            "top_k_by_lane": {"core": 2, "relational": 2, "deep": 0},
            "weight_by_lane": {"core": 1.1, "relational": 0.9},
        },
    )
    research = next(
        item for item in result["results"]
        if item.get("scope") == "shared" and item.get("domain_id") == "research"
    )
    assert research["explain"]["conflict_status"] == "open"
    assert research["explain"]["conflict_penalty"] == pytest.approx(0.62)
    assert {
        "sim", "motif_alignment", "continuity_total_adjustment",
        "conflict_penalty", "srg_total_multiplier", "lane_weight",
    } <= set(research["explain"])


def test_p9d_i3_effective_legacy_srg_source_matches_native_without_overlay(
    qualified_models,
):
    """Native SRG reads the same durable scoring source before any overlay."""
    legacy, native, _native_embedder, _legacy_embedders = qualified_models
    legacy_hit = next(
        item
        for item in legacy.private_lane("orchard", "aria").search("srg source", top_k=2)
        if item.memory_identity.eid == 0
    )
    native_hit = next(
        item
        for item in native.private_lane("orchard", "aria").search("srg source", top_k=2)
        if item.memory_identity.eid == 0
    )
    expected = legacy_hit.as_legacy_hit()["srg"]
    actual = native.effective_srg_state(native_hit)
    assert actual == expected
    assert {
        "R_band", "is_crystal", "heartbeat_class", "L_amplitude", "L_phase",
    } <= set(actual or {})


def test_p9d_i3_stale_snapshot_is_detectable_and_not_a_valid_empty(
    qualified_models, monkeypatch,
):
    """A raced selected-row validation is a named refusal, never ``()``."""
    _legacy, native, _native_embedder, _legacy_embedders = qualified_models
    lane = native.private_lane("orchard", "aria")

    # A filtered lane is a successful, valid empty result.
    assert lane.search("qualified empty lane", user_id="nobody") == ()
    runtime = lane._runtime
    monkeypatch.setattr(runtime, "_batch_project_current_rows", lambda _rows: None)
    with pytest.raises(
        NativeQuerySnapshotReadRefused,
        match="concurrent-currentness-change",
    ):
        lane.search("stale selected rows")


def test_p9d_i3_multi_workspace_same_local_ids_do_not_cross_contaminate(
    fabric_models, tmp_path,
):
    """Independent workspace-qualified adapters may reuse EIDs safely."""
    fabric, orchard_native, _orchard_embedder, _orchard_legacy_embedders = fabric_models
    connection = orchard_native._a3_fixture_connection
    idempotency = orchard_native._a3_fixture_idempotency
    orchard_runtime = orchard_native._a3_fixture_runtime
    database_path = orchard_runtime.scopes[0].core_database_path
    core_id = orchard_runtime.native_core_id

    private = _scope(
        connection, database_path, core_id, kind="PRIVATE_AGENT", qualifier="aria",
        idempotency=idempotency, workspace_id="grove",
    )
    research = _scope(
        connection, database_path, core_id, kind="SHARED_DOMAIN", qualifier="research",
        idempotency=idempotency, workspace_id="grove",
    )
    private_source, _ = _memory(
        connection, private, idempotency, "private", (1.0, 0.0, 0.0),
    )
    research_source, _ = _memory(
        connection, research, idempotency, "shared", (0.0, 1.0, 0.0),
    )
    # Each namespace starts its legacy EID sequence at zero.  Reusing both
    # the workspace-local EID and the agent/domain identifiers is intentional.
    assert private_source.eid == research_source.eid == 0
    _create_motif(
        connection, private, idempotency, motif_id="grove-private",
        domain_id="personal", source=private_source, centroid=(1.0, 0.0, 0.0),
        strength=.7, last_active_ts=100,
    )
    _create_motif(
        connection, research, idempotency, motif_id="grove-research",
        domain_id="research", source=research_source, centroid=(0.0, 1.0, 0.0),
        strength=.7, last_active_ts=100,
    )

    native_embedder = _Embedder()
    private_graph = _legacy_graph(
        tmp_path, connection, private,
        ((private_source, (1.0, 0.0, 0.0)),), _Embedder(),
    )
    research_graph = _legacy_graph(
        tmp_path, connection, research,
        ((research_source, (0.0, 1.0, 0.0)),), _Embedder(),
    )
    # Legacy graphs carry membership compatibility facts in their payload;
    # native reconstructs the same facts from scoped relationships.
    private_graph.entities[0].payload["motifs"] = ["grove-private"]
    research_graph.entities[0].payload["motifs"] = ["grove-research"]
    registries = {
        "personal": _legacy_registry(
            private_graph, "personal",
            [("grove-private", 0, (1.0, 0.0, 0.0), .7, 100)],
            workspace_id="grove",
        ),
        "research": _legacy_registry(
            research_graph, "research",
            [("grove-research", 0, (0.0, 1.0, 0.0), .7, 100)],
            workspace_id="grove",
        ),
    }
    legacy = LegacyQualifiedQueryReadModel(
        "grove", private_graphs={"aria": private_graph},
        shared_graphs={"research": research_graph}, motif_registries=registries,
        private_motif_domains={"aria": "personal"},
        shared_domain_order=("research",),
    )
    recovered = _RecoveredRuntime(
        "grove", core_id, orchard_runtime.representation_lane,
        (private, research),
        SimpleNamespace(payload={"lanes": [
            {"plan": {"scope_kind": "PRIVATE_AGENT", "agent_id": "aria", "motif_domain_id": "personal"}},
            {"plan": {"scope_kind": "SHARED_DOMAIN", "domain_id": "research", "motif_domain_id": "research"}},
        ]}),
    )
    native = NativeQualifiedQueryReadModel(recovered, embedder=native_embedder)
    workspace = fabric.get_workspace("grove", domains=["research"])
    fabric.create_agent("grove", "aria")
    agent_key = fabric._agent_key("grove", "aria")
    previous_private = fabric.private_graphs[agent_key]
    previous_shared = tuple(workspace.shared_graphs.values())
    prior_srg = fabric._srg_enable
    try:
        # The external fixture state is pre-existing.  The native read only
        # replaces its storage window; it does not initialize any legacy lane.
        previous_private.close()
        for graph in previous_shared:
            graph.close()
        fabric.private_graphs[agent_key] = private_graph
        workspace.shared_graphs = {"research": research_graph}
        workspace.motif_regs = registries
        workspace.embed_dim = 3
        workspace.meta["embed_dim"] = 3
        fabric._srg_enable = False

        expected = fabric.query("grove", "aria", "workspace-local query", top_k=4)
        actual = fabric._query_with_read_model(
            "grove", "aria", "workspace-local query", read_model=native, top_k=4,
        )
        assert actual == expected
        assert all(item["workspace_id"] == "grove" for item in actual["results"])
        assert [item["motif_id"] for item in actual["motifs"]["active"]] == [
            "grove-research"
        ]

        orchard_hit = next(
            item
            for item in orchard_native.private_lane("orchard", "aria").search(
                "workspace-local query", top_k=2,
            )
            if item.memory_identity.eid == 0
        )
        grove_hit = native.private_lane("grove", "aria").search(
            "workspace-local query", top_k=1,
        )[0]
        assert orchard_hit.memory_identity.eid == grove_hit.memory_identity.eid == 0
        assert orchard_hit.memory_identity.workspace_id == "orchard"
        assert grove_hit.memory_identity.workspace_id == "grove"
    finally:
        fabric._srg_enable = prior_srg
        fabric.private_graphs.pop(agent_key, None)
        fabric.workspaces.pop("grove", None)
        native.close()
        private_graph.close()
        research_graph.close()
