"""Qualification-only 7G5E4D proposal orchestration over native shared truth."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from torment_service.fabric import TormentFabric
from torment_service.motif_geometry_port import (
    LegacyMotifGeometryAdapter,
    NativeScopedMotifGeometryAdapter,
)
from torment_service.motif_maintenance import NativeMotifMaintenanceAdapter
from torment_service.motifs import Motif
from torment_service.proposal_shared_storage import (
    LegacyAuthorizedSharedProposalStorage,
    NativeAuthorizedSharedProposalStorage,
)
from torment_service.proposals import ShareProposal
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.motifs import MotifState, NativeMotifService
from torment_service.substrate.native_memory_vector_runtime import (
    NativeMemoryVectorRuntime,
    NativeMemoryVectorRuntimeConfiguration,
)
from torment_service.substrate.native_motif_merge_runtime import NativeMotifMergeRuntime
from torment_service.substrate.shared_proposal_materialization import (
    NativeAuthorizedSharedProposalMaterializer,
)

from test_substrate_fabric_native_routing import _prepared


WORKSPACE = "qualified-workspace"
DOMAIN = "research"
PROVIDER = "hash"
MODEL = "hash:3:torment"


class _NativeLaneEmbedder:
    provider = "synthetic"
    model = "synthetic-v1"
    dim = 3

    def embed(self, _text: str) -> list[float]:
        return _embed()


def _embed(second: float = 0.0) -> list[float]:
    vector = np.asarray((1.0, second, 0.0), dtype=np.float32)
    return (vector / np.linalg.norm(vector)).tolist()


@pytest.fixture
def fabric(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", PROVIDER)
    monkeypatch.setenv("TORMENT_HASH_DIM", "3")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    with TormentFabric(data_dir=str(tmp_path / "legacy")) as instance:
        instance.get_workspace(WORKSPACE, domains=[DOMAIN])
        yield instance


def _submit(
    fabric: TormentFabric,
    *,
    agent_id: str,
    summary: str,
    mtype: str = "fact",
    strength: float = .8,
    confidence: float = .9,
    embedding: list[float] | None = None,
) -> str:
    return fabric.propose_share(
        workspace_id=WORKSPACE,
        agent_id=agent_id,
        summary=summary,
        embedding=embedding or _embed(),
        domain_id=DOMAIN,
        mtype=mtype,
        strength=strength,
        confidence=confidence,
    )["proposal"]["proposal_id"]


def _legacy_storage(fabric: TormentFabric) -> LegacyAuthorizedSharedProposalStorage:
    workspace = fabric.get_workspace(WORKSPACE)
    return LegacyAuthorizedSharedProposalStorage(
        shared_graph=workspace.shared_graphs[DOMAIN],
        motif_registry=workspace.motif_regs[DOMAIN],
        geometry=LegacyMotifGeometryAdapter(workspace.motif_regs),
    )


@dataclass
class _NativeHarness:
    qualified: Any
    capability: Any
    connection: Any
    scope: NativeFabricRoutingScope
    vector: NativeMemoryVectorRuntime
    storage: NativeAuthorizedSharedProposalStorage

    def close(self) -> None:
        self.vector.close()
        self.qualified.close()


def _native_harness(fabric: TormentFabric, tmp_path: Path) -> _NativeHarness:
    native_root = tmp_path / "native"
    native_root.mkdir()
    qualified, connection, capability, _private, scope = _prepared(native_root, include_shared=True)
    assert scope is not None
    geometry = NativeScopedMotifGeometryAdapter(
        NativeMotifRuntimeReader(connection),
        domain_id=DOMAIN,
        motif_alias_namespace_id=scope.motif_alias_namespace_id,
        semantic_scope_id=scope.runtime_scope.semantic_scope_id,
        expected_dimension=capability.binding.representation_lane.dimension,
    )
    maintenance = NativeMotifMaintenanceAdapter(
        geometry,
        data_dir=fabric.data_dir,
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        merge_mutator=NativeMotifMergeRuntime(
            connection,
            routing_scope=scope,
            domain_id=DOMAIN,
            process_order=capability.process_order,
        ),
    )
    vector = NativeMemoryVectorRuntime(
        NativeMemoryVectorRuntimeConfiguration(
            capability.core_database_path,
            capability.core_id,
            scope.runtime_scope,
            capability.binding.representation_lane,
        ),
        embedder=_NativeLaneEmbedder(),
    )
    storage = NativeAuthorizedSharedProposalStorage(
        materializer=NativeAuthorizedSharedProposalMaterializer(capability),
        vector_runtime=vector,
        geometry=geometry,
        motif_maintenance=maintenance,
    )
    return _NativeHarness(qualified, capability, connection, scope, vector, storage)


def _reopen_native_harness(fabric: TormentFabric, previous: _NativeHarness) -> _NativeHarness:
    """Recreate only readers/runtimes; retained capability has no open handle."""
    capability, scope = previous.capability, previous.scope
    qualified = open_existing_native_core_connection(capability.core_database_path)
    connection = qualified.connection
    geometry = NativeScopedMotifGeometryAdapter(
        NativeMotifRuntimeReader(connection),
        domain_id=DOMAIN,
        motif_alias_namespace_id=scope.motif_alias_namespace_id,
        semantic_scope_id=scope.runtime_scope.semantic_scope_id,
        expected_dimension=capability.binding.representation_lane.dimension,
    )
    maintenance = NativeMotifMaintenanceAdapter(
        geometry,
        data_dir=fabric.data_dir,
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        merge_mutator=NativeMotifMergeRuntime(
            connection,
            routing_scope=scope,
            domain_id=DOMAIN,
            process_order=capability.process_order,
        ),
    )
    vector = NativeMemoryVectorRuntime(
        NativeMemoryVectorRuntimeConfiguration(
            capability.core_database_path,
            capability.core_id,
            scope.runtime_scope,
            capability.binding.representation_lane,
        ),
        embedder=_NativeLaneEmbedder(),
    )
    storage = NativeAuthorizedSharedProposalStorage(
        materializer=NativeAuthorizedSharedProposalMaterializer(capability),
        vector_runtime=vector,
        geometry=geometry,
        motif_maintenance=maintenance,
    )
    return _NativeHarness(qualified, capability, connection, scope, vector, storage)


def _statuses(fabric: TormentFabric) -> dict[str, str]:
    return {
        proposal_id: proposal.status
        for proposal_id, proposal in fabric.get_workspace(WORKSPACE).proposals[DOMAIN].apply_events().items()
    }


def _proposal_event_count(fabric: TormentFabric) -> int:
    path = Path(fabric.data_dir) / "workspaces" / WORKSPACE / "domains" / DOMAIN / "proposal_events.jsonl"
    return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0


def _proposal_group(fabric: TormentFabric) -> tuple[str, str, str]:
    return (
        _submit(
            fabric, agent_id="genuine_a", summary="Genuine claim is true.",
            strength=.85, confidence=.91, embedding=_embed(.0),
        ),
        _submit(
            fabric, agent_id="genuine_b", summary="Second genuine claim is true.",
            strength=.75, confidence=.95, embedding=_embed(.01),
        ),
        _submit(
            fabric, agent_id="collective_evidence", summary="Collective echo claim is true.",
            mtype="collective_echo", strength=.99, confidence=.99, embedding=_embed(.02),
        ),
    )


def _seed_canon(storage: Any) -> int:
    proposal = ShareProposal(
        proposal_id="baseline-canon",
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        agent_id="baseline",
        summary="Genuine claim is not true.",
        embedding=_embed(),
        mtype="fact",
        confidence=.9,
        strength=.8,
        created_ts=999,
        status="approved",
    )
    materialized = storage.materialize_operator(
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        proposal=proposal,
        embedding_provider=PROVIDER,
        embedding_model=MODEL,
    )
    storage.ensure_motif_current(
        embedding=np.asarray(proposal.embedding, dtype=np.float32),
        eid=materialized.eid,
        summary=proposal.summary,
    )
    return materialized.eid


def _seed_ignored_canon(storage: Any) -> int:
    proposal = ShareProposal(
        proposal_id="ignored-baseline-canon",
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        agent_id="baseline",
        summary="Unrelated baseline fact.",
        embedding=_embed(),
        mtype="fact",
        confidence=.9,
        strength=.8,
        created_ts=998,
        status="approved",
    )
    materialized = storage.materialize_operator(
        workspace_id=WORKSPACE,
        domain_id=DOMAIN,
        proposal=proposal,
        embedding_provider=PROVIDER,
        embedding_model=MODEL,
    )
    storage.ensure_motif_current(
        embedding=np.asarray(proposal.embedding, dtype=np.float32),
        eid=materialized.eid,
        summary=proposal.summary,
    )
    return materialized.eid


def _event_types(fabric: TormentFabric) -> list[str]:
    path = Path(fabric.data_dir) / "workspaces" / WORKSPACE / "domains" / DOMAIN / "motif_events.jsonl"
    if not path.exists():
        return []
    import json

    return [json.loads(line)["type"] for line in path.read_text(encoding="utf-8").splitlines()]


def _seed_legacy_mergeable_motifs(fabric: TormentFabric) -> None:
    registry = fabric.get_workspace(WORKSPACE).motif_regs[DOMAIN]
    registry.motifs["motif_research_0001"] = Motif(
        motif_id="motif_research_0001", domain_id=DOMAIN, label="First basin",
        centroid=[1.0, 0.0, 0.0], strength=.1, members=[101],
        contributing_agents=["baseline"], stability_score=.6, created_ts=900, last_active_ts=900,
    )
    registry.motifs["motif_research_0002"] = Motif(
        motif_id="motif_research_0002", domain_id=DOMAIN, label="Second basin",
        centroid=[.999, .001, 0.0], strength=.7, members=[101, 102],
        contributing_agents=["baseline", "seed"], stability_score=.6, created_ts=901, last_active_ts=901,
    )
    registry.save()


def _seed_native_mergeable_motifs(harness: _NativeHarness) -> None:
    scope = harness.scope
    first = ShareProposal(
        "native-auto-seed-1", WORKSPACE, DOMAIN, "baseline", "seed first",
        _embed(), "fact", .9, .8, 900, "approved",
    )
    second = ShareProposal(
        "native-auto-seed-2", WORKSPACE, DOMAIN, "seed", "seed second",
        [0.0, 1.0, 0.0], "fact", .9, .7, 901, "approved",
    )
    first_result = harness.storage.materialize_operator(
        workspace_id=WORKSPACE, domain_id=DOMAIN, proposal=first,
        embedding_provider=PROVIDER, embedding_model=MODEL,
    )
    second_result = harness.storage.materialize_operator(
        workspace_id=WORKSPACE, domain_id=DOMAIN, proposal=second,
        embedding_provider=PROVIDER, embedding_model=MODEL,
    )
    reader = NativeMotifRuntimeReader(harness.connection)
    motifs = reader.list_runtime_motifs(
        motif_alias_namespace_id=scope.motif_alias_namespace_id,
        domain_id=DOMAIN,
        semantic_scope_id=scope.runtime_scope.semantic_scope_id,
    )
    assert [item.read_model.runtime_motif_id for item in motifs] == [
        "motif_research_0001", "motif_research_0002",
    ]
    second_motif = motifs[1]
    service = NativeMotifService(harness.connection)
    service.add_motif_member(
        idempotency_namespace_id=scope.idempotency_namespace_id,
        idempotency_key="proposal-orchestration-seed-align-second",
        motif_alias_namespace_id=scope.motif_alias_namespace_id,
        membership_identity_namespace_id=scope.membership_identity_namespace_id,
        motif_object_id=second_motif.motif_object_id,
        expected_motif_revision_id=second_motif.motif_revision_id,
        state=MotifState(
            scope.runtime_scope.semantic_scope_id, "motif_research_0002", DOMAIN,
            second_motif.read_model.label, (.999, .001, 0.0), .7,
            .6, ("baseline", "seed"), second_motif.read_model.created_ts, 3_000,
        ),
        member_object_id=reader.list_ordered_current_motif_members(motifs[0].motif_object_id)[0].member_object_id,
    )
    assert (first_result.eid, second_result.eid) == (0, 1)


def test_legacy_and_native_process_default_policy_have_equivalent_outer_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.time", lambda: 1_000)
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", PROVIDER)
    monkeypatch.setenv("TORMENT_HASH_DIM", "3")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    legacy = TormentFabric(data_dir=str(tmp_path / "legacy-parity"))
    native = TormentFabric(data_dir=str(tmp_path / "native-parity"))
    harness: _NativeHarness | None = None
    try:
        legacy.get_workspace(WORKSPACE, domains=[DOMAIN])
        native.get_workspace(WORKSPACE, domains=[DOMAIN])
        legacy_storage = _legacy_storage(legacy)
        _seed_ignored_canon(legacy_storage)
        _seed_canon(legacy_storage)
        harness = _native_harness(native, tmp_path)
        _seed_ignored_canon(harness.storage)
        _seed_canon(harness.storage)

        _proposal_group(legacy)
        _proposal_group(native)
        legacy_trace: list[str] = []
        native_trace: list[str] = []
        legacy_result = legacy._process_proposals_impl(
            workspace_id=WORKSPACE, domain_id=DOMAIN, max_to_process=200,
            sim_threshold=.99, min_distinct_agents=2, step=41,
            storage=legacy_storage, _side_effect_trace=legacy_trace,
        )
        native_result = native._process_proposals_with_qualified_native_storage(
            WORKSPACE, DOMAIN, storage=harness.storage, sim_threshold=.99,
            min_distinct_agents=2, step=41, _side_effect_trace=native_trace,
        )

        assert {key: value for key, value in legacy_result.items() if key != "created_shared_eids"} == {
            key: value for key, value in native_result.items() if key != "created_shared_eids"
        } == {"ok": True, "processed": 3, "approved_groups": 1, "approved": 3}
        # Each carrier retains its own EID namespace; return-envelope parity
        # here is one newly-created shared EID, not equal numeric aliases.
        assert len(legacy_result["created_shared_eids"]) == len(native_result["created_shared_eids"]) == 1
        assert legacy_trace == native_trace == [
            "AUTHORITY_DECIDED", "PRE_CONFLICT_READ", "STORAGE_COMMITTED",
            "CONFLICT_SIDE_EFFECT", "MOTIF_MAINTENANCE", "PROPOSAL_MARK",
            "BRIDGE_SUGGEST", "DOMAIN_SUGGEST", "RETURN",
        ]
        assert sorted(_statuses(legacy).values()) == sorted(_statuses(native).values()) == [
            "approved", "approved", "approved",
        ]
        legacy_hits = legacy_storage.pre_conflict_read(_embed())
        native_hits = harness.storage.pre_conflict_read(_embed())
        assert len(native_hits) == len(legacy_hits)
        assert [item["raw_score"] for item in native_hits] == pytest.approx(
            [item["raw_score"] for item in legacy_hits]
        )
        assert [item["score"] for item in native_hits] == pytest.approx(
            [item["score"] for item in legacy_hits]
        )
        assert [item["summary"] for item in native_hits] == [item["summary"] for item in legacy_hits]
        # The legacy attachment event is storage-specific.  The subsequent M1
        # workflow event is the same external workflow result in both lanes.
        assert _event_types(legacy)[-1:] == _event_types(native)[-1:] == ["MOTIF_ENTROPY"]
        assert len(legacy.get_workspace(WORKSPACE).conflicts[DOMAIN].list()) == 1
        assert len(native.get_workspace(WORKSPACE).conflicts[DOMAIN].list()) == 1
    finally:
        if harness is not None:
            harness.close()
        legacy.close()
        native.close()


def test_legacy_and_native_process_auto_merge_executes_meaningful_native_m2_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.time", lambda: 3_000)
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", PROVIDER)
    monkeypatch.setenv("TORMENT_HASH_DIM", "3")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    legacy = TormentFabric(data_dir=str(tmp_path / "legacy-auto"))
    native = TormentFabric(data_dir=str(tmp_path / "native-auto"))
    harness: _NativeHarness | None = None
    try:
        for instance in (legacy, native):
            workspace = instance.get_workspace(WORKSPACE, domains=[DOMAIN])
            workspace.domain_policies[DOMAIN].update({
                "motif_entropy_target_n": 2,
                "motif_entropy_high": .0,
                "motif_merge_similarity": .9,
                "motif_merge_max_suggestions": 20,
                "auto_merge_motifs": True,
                "auto_merge_entropy_trigger": .0,
            })
        _seed_legacy_mergeable_motifs(legacy)
        harness = _native_harness(native, tmp_path)
        _seed_native_mergeable_motifs(harness)
        _proposal_group(legacy)
        _proposal_group(native)
        legacy_trace: list[str] = []
        native_trace: list[str] = []
        legacy_result = legacy._process_proposals_impl(
            workspace_id=WORKSPACE, domain_id=DOMAIN, max_to_process=200,
            sim_threshold=.99, min_distinct_agents=2, step=73,
            storage=_legacy_storage(legacy), _side_effect_trace=legacy_trace,
        )
        native_result = native._process_proposals_with_qualified_native_storage(
            WORKSPACE, DOMAIN, storage=harness.storage, sim_threshold=.99,
            min_distinct_agents=2, step=73, _side_effect_trace=native_trace,
        )
        assert {key: value for key, value in legacy_result.items() if key != "created_shared_eids"} == {
            key: value for key, value in native_result.items() if key != "created_shared_eids"
        } == {"ok": True, "processed": 3, "approved_groups": 1, "approved": 3}
        assert len(legacy_result["created_shared_eids"]) == len(native_result["created_shared_eids"]) == 1
        assert legacy_trace == native_trace == [
            "AUTHORITY_DECIDED", "PRE_CONFLICT_READ", "STORAGE_COMMITTED",
            "CONFLICT_SIDE_EFFECT", "MOTIF_MAINTENANCE", "AUTO_MERGE_IF_ANY",
            "PROPOSAL_MARK", "BRIDGE_SUGGEST", "DOMAIN_SUGGEST", "RETURN",
        ]
        assert sorted(_statuses(legacy).values()) == sorted(_statuses(native).values()) == [
            "approved", "approved", "approved",
        ]
        legacy_motifs = legacy.get_workspace(WORKSPACE).motif_regs[DOMAIN].motifs
        native_motifs = harness.storage.geometry.list_motifs(DOMAIN)
        assert list(legacy_motifs) == ["motif_research_0002"]
        assert [motif.runtime_motif_id for motif in native_motifs] == ["motif_research_0002"]
        assert native_motifs[0].centroid == pytest.approx(tuple(legacy_motifs["motif_research_0002"].centroid))
        assert native_motifs[0].strength == pytest.approx(legacy_motifs["motif_research_0002"].strength)
        assert _event_types(legacy)[-2:] == _event_types(native)[-2:] == [
            "MOTIF_MERGE_SUGGESTED", "MOTIF_MERGED",
        ]
        assert not (Path(native.data_dir) / "workspaces" / WORKSPACE / "domains" / DOMAIN / "motifs.json").exists()
    finally:
        if harness is not None:
            harness.close()
        legacy.close()
        native.close()


@pytest.mark.parametrize(
    ("boundary", "pending_after_failure", "conflicts_after_natural_retry", "entropy_events"),
    [
        ("storage_commit", 3, 1, 1),
        ("conflict", 3, 2, 1),
        ("motif_maintenance", 3, 2, 2),
        ("proposal_mark_after_first", 2, 1, 1),
        ("proposal_mark", 0, 1, 1),
        ("bridge", 0, 1, 1),
        ("domain_suggestion", 0, 1, 1),
    ],
)
def test_native_process_fault_boundaries_characterize_natural_retry(
    fabric: TormentFabric,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    pending_after_failure: int,
    conflicts_after_natural_retry: int,
    entropy_events: int,
) -> None:
    monkeypatch.setattr("time.time", lambda: 4_000)
    _proposal_group(fabric)
    harness = _native_harness(fabric, tmp_path)
    try:
        # The first native EID is intentionally ignored by the existing
        # conflict guard, so a second canon makes conflict replay observable.
        _seed_ignored_canon(harness.storage)
        _seed_canon(harness.storage)
        with pytest.raises(RuntimeError, match=f"after {boundary}"):
            fabric._process_proposals_with_qualified_native_storage(
                WORKSPACE, DOMAIN, storage=harness.storage, sim_threshold=.99,
                min_distinct_agents=2, step=89, _test_fail_after=boundary,
            )
        statuses_after_failure = _statuses(fabric)
        assert sum(value == "pending" for value in statuses_after_failure.values()) == pending_after_failure

        retry = fabric._process_proposals_with_qualified_native_storage(
            WORKSPACE, DOMAIN, storage=harness.storage, sim_threshold=.99,
            min_distinct_agents=2, step=89,
        )
        hits = harness.storage.pre_conflict_read(_embed())
        # The storage operation key is stable: every natural retry sees the
        # one committed proposal memory rather than duplicating it.
        assert len(hits) == 3
        assert len(fabric.get_workspace(WORKSPACE).conflicts[DOMAIN].list()) == conflicts_after_natural_retry
        assert _event_types(fabric).count("MOTIF_ENTROPY") == entropy_events
        if boundary in {"storage_commit", "conflict", "motif_maintenance"}:
            assert retry["approved"] == 3
            assert set(_statuses(fabric).values()) == {"approved"}
            assert _proposal_event_count(fabric) == 3
        elif boundary == "proposal_mark_after_first":
            assert retry == {"ok": True, "processed": 2, "approved_groups": 0, "approved": 0, "created_shared_eids": []}
            assert sorted(_statuses(fabric).values()) == ["approved", "pending", "pending"]
            assert _proposal_event_count(fabric) == 1
        else:
            # Once every proposal has been marked, ordinary list_pending()
            # cannot reconstruct the group or resume post-mark callbacks.
            assert retry == {"ok": True, "processed": 0, "approved_groups": 0, "approved": 0}
            assert set(_statuses(fabric).values()) == {"approved"}
            assert _proposal_event_count(fabric) == 3
    finally:
        harness.close()


def test_native_same_authorized_group_replay_recovers_one_committed_memory(
    fabric: TormentFabric, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.time", lambda: 4_500)
    _proposal_group(fabric)
    harness = _native_harness(fabric, tmp_path)
    try:
        pending = tuple(fabric.get_workspace(WORKSPACE).proposals[DOMAIN].list_pending())
        representative = max(
            (proposal for proposal in pending if proposal.mtype != "collective_echo"),
            key=lambda proposal: (proposal.strength, proposal.confidence),
        )
        with pytest.raises(RuntimeError, match="after storage_commit"):
            fabric._process_proposals_with_qualified_native_storage(
                WORKSPACE, DOMAIN, storage=harness.storage, sim_threshold=.99,
                min_distinct_agents=2, step=91, _test_fail_after="storage_commit",
            )
        replay = harness.storage.materialize_quorum(
            workspace_id=WORKSPACE,
            domain_id=DOMAIN,
            representative=representative,
            participating_proposals=pending,
            support_agents=("genuine_a", "genuine_b"),
            embedding_provider=PROVIDER,
            embedding_model=MODEL,
            step=91,
        )
        assert (replay.eid, replay.created_new) == (0, True)
        assert len(harness.storage.pre_conflict_read(_embed())) == 1
        # Replay owns no conflict, proposal-status, bridge, or domain effect.
        assert _proposal_event_count(fabric) == 0
        assert fabric.get_workspace(WORKSPACE).conflicts[DOMAIN].list() == []
        assert fabric._process_proposals_with_qualified_native_storage(
            WORKSPACE, DOMAIN, storage=harness.storage, sim_threshold=.99,
            min_distinct_agents=2, step=91,
        )["approved"] == 3
        assert len(harness.storage.pre_conflict_read(_embed())) == 1
    finally:
        harness.close()


@pytest.mark.parametrize(
    ("boundary", "expected_marks", "expected_bridge_calls", "expected_domain_calls"),
    [
        ("operator_storage_commit", 1, 1, 1),
        ("operator_proposal_mark", 2, 1, 1),
        ("operator_bridge", 2, 2, 1),
        ("operator_domain_suggestion", 2, 2, 2),
    ],
)
def test_native_operator_fault_boundaries_characterize_natural_retry(
    fabric: TormentFabric,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    expected_marks: int,
    expected_bridge_calls: int,
    expected_domain_calls: int,
) -> None:
    monkeypatch.setattr("time.time", lambda: 4_600)
    proposal_id = _submit(fabric, agent_id="operator", summary="Operator retry claim.")
    harness = _native_harness(fabric, tmp_path)
    try:
        workspace = fabric.get_workspace(WORKSPACE)
        bridge_calls: list[tuple[float, int]] = []
        domain_calls: list[str] = []
        original_bridge = workspace.bridges.suggest
        original_domain = fabric._maybe_suggest_domain

        def bridge_observer(geometry, sim_threshold=.82, max_new=10):
            bridge_calls.append((sim_threshold, max_new))
            return original_bridge(geometry, sim_threshold=sim_threshold, max_new=max_new)

        def domain_observer(ws, domain_id, *, geometry=None):
            domain_calls.append(domain_id)
            return original_domain(ws, domain_id, geometry=geometry)

        monkeypatch.setattr(workspace.bridges, "suggest", bridge_observer)
        monkeypatch.setattr(fabric, "_maybe_suggest_domain", domain_observer)
        with pytest.raises(RuntimeError, match=f"after {boundary}"):
            fabric._decide_proposal_with_qualified_native_storage(
                WORKSPACE, DOMAIN, proposal_id, "approve", storage=harness.storage,
                _test_fail_after=boundary,
            )
        retry = fabric._decide_proposal_with_qualified_native_storage(
            WORKSPACE, DOMAIN, proposal_id, "approve", storage=harness.storage,
        )
        assert retry["created_shared_eid"] == 0
        assert len(harness.storage.pre_conflict_read(_embed())) == 1
        assert _proposal_event_count(fabric) == expected_marks
        assert bridge_calls == [(.86, 5)] * expected_bridge_calls
        assert domain_calls == [DOMAIN] * expected_domain_calls
    finally:
        harness.close()


def test_partial_group_mark_hazard_survives_cold_restart_without_a_repair(
    fabric: TormentFabric, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.time", lambda: 4_700)
    _proposal_group(fabric)
    harness = _native_harness(fabric, tmp_path)
    data_dir = fabric.data_dir
    replacement: TormentFabric | None = None
    reopened: _NativeHarness | None = None
    try:
        with pytest.raises(RuntimeError, match="after proposal_mark_after_first"):
            fabric._process_proposals_with_qualified_native_storage(
                WORKSPACE, DOMAIN, storage=harness.storage, sim_threshold=.99,
                min_distinct_agents=2, step=93, _test_fail_after="proposal_mark_after_first",
            )
        assert sorted(_statuses(fabric).values()) == ["approved", "pending", "pending"]
        harness.close()
        fabric.close()

        replacement = TormentFabric(data_dir=data_dir)
        replacement.get_workspace(WORKSPACE, domains=[DOMAIN])
        reopened = _reopen_native_harness(replacement, harness)
        retry = replacement._process_proposals_with_qualified_native_storage(
            WORKSPACE, DOMAIN, storage=reopened.storage, sim_threshold=.99,
            min_distinct_agents=2, step=93,
        )
        assert retry == {"ok": True, "processed": 2, "approved_groups": 0, "approved": 0, "created_shared_eids": []}
        assert sorted(_statuses(replacement).values()) == ["approved", "pending", "pending"]
        assert len(reopened.storage.pre_conflict_read(_embed())) == 1
        assert _proposal_event_count(replacement) == 1
    finally:
        if reopened is not None:
            reopened.close()
        if replacement is not None:
            replacement.close()
        # close() is idempotent, including after the deliberate restart above.
        harness.close()


def test_qualified_native_process_preserves_authority_trace_and_external_ownership(
    fabric: TormentFabric, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.time", lambda: 1_000)
    _proposal_group(fabric)
    harness = _native_harness(fabric, tmp_path)
    try:
        workspace = fabric.get_workspace(WORKSPACE)

        # A qualified native caller has no permission to consult the retained
        # legacy motif registry as current motif truth.
        class _ForbiddenLegacyMotifs(dict):
            def __getitem__(self, _key):
                raise AssertionError("qualified native orchestration consulted legacy motif truth")

            def items(self):
                raise AssertionError("qualified native orchestration consulted legacy motif truth")

        workspace.motif_regs = _ForbiddenLegacyMotifs()
        trace: list[str] = []
        result = fabric._process_proposals_with_qualified_native_storage(
            WORKSPACE, DOMAIN, storage=harness.storage, sim_threshold=.99,
            min_distinct_agents=2, step=41, _side_effect_trace=trace,
        )
        assert result == {
            "ok": True, "processed": 3, "approved_groups": 1, "approved": 3,
            "created_shared_eids": [0],
        }
        assert trace == [
            "AUTHORITY_DECIDED", "PRE_CONFLICT_READ", "STORAGE_COMMITTED",
            "CONFLICT_SIDE_EFFECT", "MOTIF_MAINTENANCE", "PROPOSAL_MARK",
            "BRIDGE_SUGGEST", "DOMAIN_SUGGEST", "RETURN",
        ]
        assert set(_statuses(fabric).values()) == {"approved"}
        # Native materialization owns the motif; no retained motifs.json was
        # created by the qualified path.  Proposal events remain Fabric-owned.
        base = Path(fabric.data_dir) / "workspaces" / WORKSPACE / "domains" / DOMAIN
        assert not (base / "motifs.json").exists()
        assert (base / "proposal_events.jsonl").exists()
        assert len(harness.storage.pre_conflict_read(_embed())) == 1
    finally:
        harness.close()


def test_qualified_native_operator_approve_reject_and_collective_refusal(
    fabric: TormentFabric, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.time", lambda: 2_000)
    approve = _submit(fabric, agent_id="operator", summary="Operator claim.", embedding=_embed(.3))
    reject = _submit(fabric, agent_id="reject", summary="Reject claim.", embedding=_embed(.4))
    echo = _submit(
        fabric, agent_id="collective_evidence", summary="Echo claim.", mtype="collective_echo", embedding=_embed(.5),
    )
    harness = _native_harness(fabric, tmp_path)
    try:
        trace: list[str] = []
        approved = fabric._decide_proposal_with_qualified_native_storage(
            WORKSPACE, DOMAIN, approve, "approve", storage=harness.storage,
            _side_effect_trace=trace,
        )
        assert approved == {
            "ok": True, "decision": "approved", "proposal_id": approve,
            "created_shared_eid": 0,
        }
        assert trace == [
            "AUTHORITY_DECIDED", "STORAGE_COMMITTED", "PROPOSAL_MARK",
            "BRIDGE_SUGGEST", "DOMAIN_SUGGEST", "RETURN",
        ]
        assert fabric._decide_proposal_with_qualified_native_storage(
            WORKSPACE, DOMAIN, reject, "reject", storage=harness.storage,
        )["decision"] == "rejected"
        with pytest.raises(ValueError, match="collective-derived proposals require"):
            fabric._decide_proposal_with_qualified_native_storage(
                WORKSPACE, DOMAIN, echo, "approve", storage=harness.storage,
            )
        assert _statuses(fabric)[approve] == "approved"
        assert _statuses(fabric)[reject] == "rejected"
        assert _statuses(fabric)[echo] == "pending"
    finally:
        harness.close()
