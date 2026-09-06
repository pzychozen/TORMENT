"""Disposable qualification for the recoverable P3 B1/B2 source carrier."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest

from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidenceAbsenceReason,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExpectedRootCensus,
    ExplicitSourceEvidence,
    IdentityOnlyAgentObservation,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    MigrationRuntimeRepresentationBootstrapRequest,
    MigrationRuntimeScopePlan,
    NativeRootP3SourceAdmissionService,
    NativeRootWideNormalizationService,
    RepresentationDispositionCount,
    RootEvidenceManifest,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootNormalizationScopeInput,
    RootP3ScopeBinding,
    RootP3SourceAdmissionInterrupted,
    RootP3SourceAdmissionInterruptionPoint,
    RootP3SourceAdmissionRequest,
    RootRepresentationDisposition,
    RootScopeKey,
    RootScopeKind,
    SourceOwnerClass,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
    capture_present_source_evidence,
    load_snapshot_manifest,
    p3_child_request_counts,
    planned_p3_child_request_counts,
)
from torment_service.substrate.errors import SubstrateSnapshotManifestError
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.schema import create_schema
from torment_service.substrate.corrective_freeze_packet import (
    MetadataLessPerEidEvidence,
    RootSourceScopePlan,
    SourceArtifactPresence,
)


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "st", "BAAI/bge-small-en-v1.5", 384,
        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


class _Embedder:
    provider = "st"
    model = "BAAI/bge-small-en-v1.5"
    dim = 384

    def embed(self, _text: str) -> np.ndarray:
        return np.asarray([1.0] + [0.0] * 383, dtype=np.float32)


def _line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"


def _payload() -> dict[str, object]:
    return {
        "summary": "P3 source-carrier qualification memory",
        "type": "memory", "memory_class": "core", "strength": 0.7, "confidence": 0.9,
        "seed_pos0": [1, 2, 3], "seed_v0": [0.1, 0.2, 0.3],
        "governance": {
            "protected": False, "non_shareable": False,
            "collective_export_blocked": False, "collective_reingest_blocked": False,
            "decay_accelerated": False,
        },
        "provenance": ProvenanceV1(
            source_type="role_output", source_role="test", write_path="cognition_writeback",
            parent_eids=[], created_at_step=1, created_at_ts="2024-01-01T00:00:00Z",
        ).to_dict(),
        "lifecycle_status": {
            "state": "active", "is_authoritative_on_row": True, "requires_join": None,
            "set_by": {"actor": "user", "via": "api", "at": 1}, "history_ref": None,
        },
    }


def _insert(connection, table: str, value: UUID, label: str, *, reserved: bool = False) -> None:
    connection.execute(
        f"INSERT INTO {table} VALUES ({'?,?,0' if reserved else '?,?'})",
        (native_id_to_bytes(value), label),
    )


@pytest.fixture
def carrier_fixture(tmp_path: Path):
    root = tmp_path / "root"
    source = root / "workspaces" / "ws" / "domains" / "domain" / "shared"
    source.mkdir(parents=True)
    embeddings = source / "embeddings"
    embeddings.mkdir()
    (source / "nodes.jsonl").write_bytes(_line({
        "eid": 0, "born_step": 1, "channel": 1, "payload": _payload(),
        "embedding_ref": {
            "map": "embeddings/shard.map.jsonl", "shard": "embeddings/vectors.npy",
            "row": 0, "dimension": 384, "dtype": "float32",
        },
    }))
    np.save(embeddings / "vectors.npy", np.asarray([[1.0] + [0.0] * 383], dtype=np.float32))
    (embeddings / "manifest.json").write_bytes(_line({
        "encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 384,
        "derivation_contract_version": "fixture-v1", "provider": "st",
        "model": "BAAI/bge-small-en-v1.5",
        "shards": [{"path": "embeddings/vectors.npy", "map": "embeddings/shard.map.jsonl"}],
    }))
    (embeddings / "shard.map.jsonl").write_bytes(_line({
        "eid": 0, "shard": "embeddings/vectors.npy", "row": 0, "dimension": 384,
    }))

    key = RootScopeKey("ws", RootScopeKind.SHARED, domain_id="domain")
    empty_key = RootScopeKey("ws", RootScopeKind.PRIVATE, agent_id="empty-agent")
    motif_key = RootScopeKey("ws", RootScopeKind.SHARED, domain_id="empty-domain")
    workspace = root / "workspaces" / "ws"
    (workspace / "workspace_meta.json").write_text(json.dumps({
        "embed_provider": "st", "embed_model": "BAAI/bge-small-en-v1.5", "embed_dim": 384,
    }), encoding="utf-8")
    motif_path = workspace / "domains" / "empty-domain" / "motifs.json"
    motif_path.parent.mkdir(parents=True)
    motif_path.write_text(json.dumps({"motifs": {"empty-motif": {
        "motif_id": "empty-motif", "domain_id": "empty-domain", "label": "empty motif",
        "centroid": [1.0] + [0.0] * 383, "strength": 0.8, "stability_score": 0.8,
        "contributing_agents": [], "created_ts": 1, "last_active_ts": 2, "members": [],
    }}}), encoding="utf-8")
    owner = EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="domain")
    entries = tuple(
        capture_present_source_evidence(
            data_root=root, owner_class=owner_class, owner_boundary=owner,
            canonical_locator=locator, semantic_role=role, scope_key=key,
        )
        for owner_class, locator, role in (
            (SourceOwnerClass.SHARED_GRAPH_SOURCE, "nodes.jsonl", EvidenceSemanticRole.NODES),
            (SourceOwnerClass.EMBEDDING_MANIFEST, "embeddings/manifest.json", EvidenceSemanticRole.EMBEDDING_MANIFEST),
            (SourceOwnerClass.EMBEDDING_SHARD_OR_MAP, "embeddings/shard.map.jsonl", EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP),
            (SourceOwnerClass.LEGACY_REPRESENTATION_ARTIFACT, "embeddings/vectors.npy", EvidenceSemanticRole.LEGACY_REPRESENTATION),
        )
    ) + (ExplicitSourceEvidence(
        SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
        EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="empty-agent"),
        "nodes.jsonl", EvidenceSemanticRole.NODES, EvidencePresenceExpectation.EXPECTED_ABSENT,
        empty_key, absence_reason=EvidenceAbsenceReason.EMPTY_GRAPH,
    ), capture_present_source_evidence(
        data_root=root,
        owner_class=SourceOwnerClass.WORKSPACE_IDENTITY_METADATA,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.WORKSPACE),
        canonical_locator="workspace_meta.json", semantic_role=EvidenceSemanticRole.WORKSPACE_META,
    ), ExplicitSourceEvidence(
        SourceOwnerClass.SHARED_GRAPH_SOURCE,
        EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="empty-domain"),
        "nodes.jsonl", EvidenceSemanticRole.NODES, EvidencePresenceExpectation.EXPECTED_ABSENT,
        motif_key, absence_reason=EvidenceAbsenceReason.EMPTY_GRAPH,
    ), capture_present_source_evidence(
        data_root=root,
        owner_class=SourceOwnerClass.MOTIF_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="empty-domain"),
        canonical_locator="motifs.json", semantic_role=EvidenceSemanticRole.MOTIFS, scope_key=motif_key,
    ),)
    description = RootNativeProductionAdmissionDescription(
        data_root_identity="p3-source-carrier-fixture",
        operator_identity="pytest",
        workspace_plans=(WorkspaceRootAdmissionPlan(
            "ws",
            private_materialized_scopes=(MaterializedRootScopePlan(
                empty_key, RootRepresentationDisposition.NO_VECTOR,
                MaterializedScopePosture.EMPTY_PRIVATE,
            ),),
            shared_materialized_scopes=(MaterializedRootScopePlan(
                key, RootRepresentationDisposition.TARGET_COMPATIBLE,
            ), MaterializedRootScopePlan(
                motif_key, RootRepresentationDisposition.TARGET_COMPATIBLE,
                MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
            )),
            identity_only_agents=(IdentityOnlyAgentObservation("empty-agent", "empty-private"),),
        ),),
        target_representation_lane=_lane(),
        expected_census=ExpectedRootCensus(
            workspace_count=1, materialized_private_scope_count=1,
            materialized_shared_scope_count=2, total_materialized_scope_count=3,
            representation_disposition_counts=tuple(
                RepresentationDispositionCount(
                    disposition,
                    2 if disposition is RootRepresentationDisposition.TARGET_COMPATIBLE
                    else 1 if disposition is RootRepresentationDisposition.NO_VECTOR else 0,
                ) for disposition in RootRepresentationDisposition
            ),
            workspace_topology_counts=WorkspaceTopologyCounts(0, 1, 0, 0, 0, 1),
            empty_private_identity_scope_count=1,
        ),
        explicit_source_manifest=RootEvidenceManifest(entries),
        external_owner_observations=(),
        feature_posture=RootFeaturePosture("p3-carrier-test", False, False),
    )
    qualified = open_temporary_test_connection(tmp_path / "core.db")
    connection = qualified.connection
    metadata = create_schema(connection)
    core_id = UUID(bytes=metadata.core_id)
    target_identity = generate_native_id()
    target_scope = generate_native_id()
    motif_alias = generate_native_id()
    motif_identity = generate_native_id()
    membership_identity = generate_native_id()
    source_namespace = generate_native_id()
    idempotency = generate_native_id()
    unknown_scope = generate_native_id()
    empty_target_identity = generate_native_id()
    empty_target_scope = generate_native_id()
    empty_motif_alias = generate_native_id()
    empty_motif_identity = generate_native_id()
    empty_membership_identity = generate_native_id()
    empty_source_namespace = generate_native_id()
    empty_idempotency = generate_native_id()
    empty_unknown_scope = generate_native_id()
    motif_target_identity = generate_native_id()
    motif_target_scope = generate_native_id()
    motif_motif_alias = generate_native_id()
    motif_motif_identity = generate_native_id()
    motif_membership_identity = generate_native_id()
    motif_source_namespace = generate_native_id()
    motif_idempotency = generate_native_id()
    motif_unknown_scope = generate_native_id()
    _insert(connection, "identity_namespaces", target_identity, "target", reserved=True)
    _insert(connection, "identity_namespaces", motif_identity, "motif", reserved=True)
    _insert(connection, "identity_namespaces", membership_identity, "membership", reserved=True)
    _insert(connection, "semantic_scopes", target_scope, "target", reserved=True)
    _insert(connection, "semantic_scopes", unknown_scope, "unknown", reserved=True)
    _insert(connection, "legacy_source_namespaces", motif_alias, "motif-alias", reserved=True)
    _insert(connection, "idempotency_namespaces", idempotency, "idempotency")
    _insert(connection, "identity_namespaces", empty_target_identity, "empty-target", reserved=True)
    _insert(connection, "identity_namespaces", empty_motif_identity, "empty-motif", reserved=True)
    _insert(connection, "identity_namespaces", empty_membership_identity, "empty-membership", reserved=True)
    _insert(connection, "semantic_scopes", empty_target_scope, "empty-target", reserved=True)
    _insert(connection, "semantic_scopes", empty_unknown_scope, "empty-unknown", reserved=True)
    _insert(connection, "legacy_source_namespaces", empty_motif_alias, "empty-motif-alias", reserved=True)
    _insert(connection, "idempotency_namespaces", empty_idempotency, "empty-idempotency")
    _insert(connection, "identity_namespaces", motif_target_identity, "motif-target", reserved=True)
    _insert(connection, "identity_namespaces", motif_motif_identity, "motif-motif", reserved=True)
    _insert(connection, "identity_namespaces", motif_membership_identity, "motif-membership", reserved=True)
    _insert(connection, "semantic_scopes", motif_target_scope, "motif-target", reserved=True)
    _insert(connection, "semantic_scopes", motif_unknown_scope, "motif-unknown", reserved=True)
    _insert(connection, "legacy_source_namespaces", motif_motif_alias, "motif-motif-alias", reserved=True)
    _insert(connection, "idempotency_namespaces", motif_idempotency, "motif-idempotency")
    plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=source_namespace, workspace_id="ws", scope_kind="SHARED_DOMAIN",
        target_identity_namespace_id=target_identity, target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=motif_alias, motif_identity_namespace_id=motif_identity,
        membership_identity_namespace_id=membership_identity, idempotency_namespace_id=idempotency,
        domain_id="domain", motif_domain_id="domain",
    )
    source_plan = RootSourceScopePlan(
        scope_key=key, materialization_posture=MaterializedScopePosture.MEMORY_GRAPH,
        representation_disposition=RootRepresentationDisposition.TARGET_COMPATIBLE,
        motif_domain_id="domain", target_representation_lane=_lane(),
    )
    empty_plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=empty_source_namespace, workspace_id="ws", scope_kind="PRIVATE_AGENT",
        target_identity_namespace_id=empty_target_identity, target_semantic_scope_id=empty_target_scope,
        motif_alias_namespace_id=empty_motif_alias, motif_identity_namespace_id=empty_motif_identity,
        membership_identity_namespace_id=empty_membership_identity, idempotency_namespace_id=empty_idempotency,
        agent_id="empty-agent",
    )
    empty_source_plan = RootSourceScopePlan(
        scope_key=empty_key, materialization_posture=MaterializedScopePosture.EMPTY_PRIVATE,
        representation_disposition=RootRepresentationDisposition.NO_VECTOR,
        motif_domain_id=None, target_representation_lane=_lane(),
    )
    motif_plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=motif_source_namespace, workspace_id="ws", scope_kind="SHARED_DOMAIN",
        target_identity_namespace_id=motif_target_identity, target_semantic_scope_id=motif_target_scope,
        motif_alias_namespace_id=motif_motif_alias, motif_identity_namespace_id=motif_motif_identity,
        membership_identity_namespace_id=motif_membership_identity, idempotency_namespace_id=motif_idempotency,
        domain_id="empty-domain", motif_domain_id="empty-domain",
    )
    motif_source_plan = RootSourceScopePlan(
        scope_key=motif_key, materialization_posture=MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
        representation_disposition=RootRepresentationDisposition.TARGET_COMPATIBLE,
        motif_domain_id="empty-domain", target_representation_lane=_lane(),
        motif_presence=SourceArtifactPresence.PRESENT,
    )
    (tmp_path / "administration").mkdir()
    request = RootP3SourceAdmissionRequest(
        data_root=root, native_core_database_path=qualified.database_path,
        expected_native_core_id=core_id, description=description,
        source_scope_plans=(source_plan, empty_source_plan, motif_source_plan),
        scope_bindings=(
            RootP3ScopeBinding(key, plan, unknown_scope),
            RootP3ScopeBinding(empty_key, empty_plan, empty_unknown_scope),
            RootP3ScopeBinding(motif_key, motif_plan, motif_unknown_scope),
        ),
        unknown_identity_evidence=(), carrier_directory=tmp_path / "administration" / "carrier",
        operation_key="p3-source-carrier-fixture",
        qualification_embedder_identity=WorkspaceNativeEmbedderIdentity("st", "BAAI/bge-small-en-v1.5", 384),
        b3b_embedder=_Embedder(),
    )
    try:
        yield connection, request
    finally:
        qualified.close()


def test_wrong_p1_plan_shape_remains_an_invalid_snapshot_manifest(tmp_path: Path) -> None:
    plan = tmp_path / "p1-bootstrap-plan.json"
    plan.write_text('{"runtime_scopes": []}\n', encoding="utf-8")
    with pytest.raises(SubstrateSnapshotManifestError, match="schema version is incompatible"):
        load_snapshot_manifest(plan)


def test_source_carrier_recovers_snapshot_b1_and_b2_then_composes_b3b4(carrier_fixture) -> None:
    connection, request = carrier_fixture
    service = NativeRootP3SourceAdmissionService(connection)
    with pytest.raises(RootP3SourceAdmissionInterrupted) as after_snapshot:
        service.admit(
            request,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    assert after_snapshot.value.point is RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION
    scopes = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]["scopes"]
    selected = next(item for item in scopes if item["scope_key"].get("domain_id") == "domain")
    selected_snapshot_id = selected["legacy_snapshot_id"]
    assert all(item["b1"] is None and item["b2"]["memories"] == [] for item in scopes)
    with pytest.raises(RootP3SourceAdmissionInterrupted) as after_b1:
        service.admit(
            request,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_B1,
        )
    assert after_b1.value.point is RootP3SourceAdmissionInterruptionPoint.AFTER_B1
    scopes = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]["scopes"]
    selected = next(item for item in scopes if item["scope_key"].get("domain_id") == "domain")
    empty = next(item for item in scopes if item["scope_key"]["scope_kind"] == "PRIVATE")
    assert selected["legacy_snapshot_id"] == selected_snapshot_id
    assert selected["b1"] is None and selected["b2"]["memories"] == []
    assert empty["b1"] == {"memories": [], "motifs": []}
    with pytest.raises(RuntimeError, match="forced response loss after committed normalization"):
        service.admit(request, _test_lose_response_after_b2=True)
    recovered = service.admit(request)
    scopes = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]["scopes"]
    current = next(item for item in scopes if item["scope_key"].get("domain_id") == "domain")
    empty = next(item for item in scopes if item["scope_key"]["scope_kind"] == "PRIVATE")
    motif = next(item for item in scopes if item["scope_key"].get("domain_id") == "empty-domain")
    assert current["legacy_snapshot_id"] == selected_snapshot_id
    assert current["b1"]["memories"][0]["eid"] == 0
    assert current["b2"]["memories"][0]["eid"] == 0
    assert empty["b1"] == {"memories": [], "motifs": []}
    assert empty["b2"] == {"memories": []}
    assert motif["b1"]["memories"] == [] and len(motif["b1"]["motifs"]) == 1
    assert motif["b2"] == {"memories": []}
    assert recovered.snapshot_scope_count == 3
    assert recovered.b1_memory_count == recovered.b2_memory_count == 1
    empty_input = next(
        item for item in recovered.normalization_request.scope_inputs
        if item.scope_key.scope_kind is RootScopeKind.PRIVATE
    )
    assert not (
        empty_input.b3a_requests
        or empty_input.b3b_requests
        or empty_input.metadata_less_b3b_dispatches
        or empty_input.b4a_requests
        or empty_input.b4c_requests
    )
    assert p3_child_request_counts(recovered.normalization_request.scope_inputs) == {
        "b3a": 1, "ordinary_b3b": 0, "metadata_less_b3b": 0,
        "total_b3b": 0, "b4a": 0, "b4b": 0, "b4c": 1,
    }
    result = NativeRootWideNormalizationService(connection).normalize(recovered.normalization_request)
    assert result.root_normalization_complete and result.root_normalization_ready


def test_frozen_real_p3_child_shape_counts_remain_closed() -> None:
    lane = _lane()
    plans: list[RootSourceScopePlan] = []
    unknown: list[MetadataLessPerEidEvidence] = []
    for index in range(47):
        plans.append(RootSourceScopePlan(
            RootScopeKey(f"a{index}", RootScopeKind.PRIVATE, agent_id="p"),
            MaterializedScopePosture.MEMORY_GRAPH, RootRepresentationDisposition.TARGET_COMPATIBLE,
            None, lane,
        ))
    for index in range(25):
        plans.append(RootSourceScopePlan(
            RootScopeKey(f"b{index}", RootScopeKind.PRIVATE, agent_id="p"),
            MaterializedScopePosture.MEMORY_GRAPH, RootRepresentationDisposition.REEMBED_REQUIRED,
            None, lane,
        ))
    for index in range(3):
        key = RootScopeKey(f"u{index}", RootScopeKind.PRIVATE, agent_id="p")
        plans.append(RootSourceScopePlan(
            key, MaterializedScopePosture.MEMORY_GRAPH,
            RootRepresentationDisposition.UNKNOWN_IDENTITY, None, lane,
        ))
        owner = EvidenceOwnerBoundary(key.workspace_id, EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="p")
        vector = _synthetic_evidence(owner, "emb_1.npy", EvidenceSemanticRole.LEGACY_REPRESENTATION, key)
        nodes = _synthetic_evidence(owner, "nodes.jsonl", EvidenceSemanticRole.NODES, key)
        unknown.append(MetadataLessPerEidEvidence(
            scope_key=key, eid=1, vector_evidence=vector, canonical_text_evidence=nodes,
            dtype="float32", shape=(384,), metadata_less_source_evidence_identity="a" * 64,
        ))
    for index in range(47):
        plans.append(RootSourceScopePlan(
            RootScopeKey(f"m{index}", RootScopeKind.SHARED, domain_id="d"),
            MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
            RootRepresentationDisposition.TARGET_COMPATIBLE, "d", lane,
            SourceArtifactPresence.PRESENT,
        ))
    plans.append(RootSourceScopePlan(
        RootScopeKey("empty-private", RootScopeKind.PRIVATE, agent_id="p"),
        MaterializedScopePosture.EMPTY_PRIVATE, RootRepresentationDisposition.NO_VECTOR, None, lane,
    ))
    plans.append(RootSourceScopePlan(
        RootScopeKey("empty-shared", RootScopeKind.SHARED, domain_id="d"),
        MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF, RootRepresentationDisposition.NO_VECTOR,
        "d", lane,
    ))
    for index in range(30):
        plans.append(RootSourceScopePlan(
            RootScopeKey(f"declared{index}", RootScopeKind.SHARED, domain_id="d"),
            MaterializedScopePosture.DECLARED_EMPTY_SHARED,
            RootRepresentationDisposition.NO_VECTOR, "d", lane,
        ))
    assert len(plans) == 154
    assert planned_p3_child_request_counts(tuple(plans), tuple(unknown)) == {
        "b3a": 47, "ordinary_b3b": 25, "metadata_less_b3b": 3,
        "total_b3b": 28, "b4a": 0, "b4b": 0, "b4c": 47,
    }


def _synthetic_evidence(
    owner: EvidenceOwnerBoundary, locator: str, role: EvidenceSemanticRole, key: RootScopeKey,
):
    from torment_service.substrate.migration import ExplicitSourceEvidence

    return ExplicitSourceEvidence(
        SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION
        if role is EvidenceSemanticRole.LEGACY_REPRESENTATION else SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
        owner, locator, role, EvidencePresenceExpectation.EXPECTED_PRESENT, key,
        byte_length=1, sha256_hex="0" * 64,
    )
