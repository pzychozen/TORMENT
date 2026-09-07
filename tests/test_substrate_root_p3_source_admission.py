"""Disposable qualification for the recoverable P3 B1/B2 source carrier."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest

import torment_service.substrate.migration.root_p3_source_admission as p3_source_admission
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
    RootP3SourceAdmissionRefused,
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
    pre_b1_p3_scope_shape_counts,
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


_MULTI_MEMORY_EIDS = (17, 2, 29, 5)
_MULTI_MOTIF_IDS = ("empty-motif-z", "empty-motif-a", "empty-motif-k")


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
    (source / "nodes.jsonl").write_bytes(b"".join(
        _line({
            "eid": eid,
            "born_step": index + 1,
            "channel": 1,
            "payload": {
                **_payload(),
                "embedding_ref": {"shard": 0, "row": index, "dim": 384},
            },
        })
        for index, eid in enumerate(_MULTI_MEMORY_EIDS)
    ))
    np.save(
        embeddings / "shard_000000.npy",
        np.asarray(
            [[float(index + 1)] + [0.0] * 383 for index in range(len(_MULTI_MEMORY_EIDS))],
            dtype=np.float32,
        ),
    )
    (embeddings / "manifest.json").write_bytes(_line({
        "version": 1, "embedding_dim": 384, "dtype": "float32",
        "rows_per_shard": len(_MULTI_MEMORY_EIDS), "active_shard": 0,
        "next_row": len(_MULTI_MEMORY_EIDS), "total_rows": len(_MULTI_MEMORY_EIDS),
    }))
    (embeddings / "shard_000000.map.jsonl").write_bytes(b"".join(
        _line({
            "eid": eid, "row": index, "dimension": 384,
        })
        for index, eid in enumerate(_MULTI_MEMORY_EIDS)
    ))

    key = RootScopeKey("ws", RootScopeKind.SHARED, domain_id="domain")
    empty_key = RootScopeKey("ws", RootScopeKind.PRIVATE, agent_id="empty-agent")
    motif_key = RootScopeKey("ws", RootScopeKind.SHARED, domain_id="empty-domain")
    workspace = root / "workspaces" / "ws"
    (workspace / "workspace_meta.json").write_text(json.dumps({
        "embed_provider": "st", "embed_model": "BAAI/bge-small-en-v1.5", "embed_dim": 384,
    }), encoding="utf-8")
    motif_path = workspace / "domains" / "empty-domain" / "motifs.json"
    motif_path.parent.mkdir(parents=True)
    motif_path.write_text(json.dumps({"motifs": {
        motif_id: {
            "motif_id": motif_id, "domain_id": "empty-domain", "label": motif_id,
            "centroid": [1.0] + [0.0] * 383, "strength": 0.8, "stability_score": 0.8,
            "contributing_agents": [], "created_ts": 1, "last_active_ts": 2, "members": [],
        }
        for motif_id in _MULTI_MOTIF_IDS
    }}), encoding="utf-8")
    owner = EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="domain")
    entries = tuple(
        capture_present_source_evidence(
            data_root=root, owner_class=owner_class, owner_boundary=owner,
            canonical_locator=locator, semantic_role=role, scope_key=key,
        )
        for owner_class, locator, role in (
            (SourceOwnerClass.SHARED_GRAPH_SOURCE, "nodes.jsonl", EvidenceSemanticRole.NODES),
            (SourceOwnerClass.EMBEDDING_MANIFEST, "embeddings/manifest.json", EvidenceSemanticRole.EMBEDDING_MANIFEST),
            (SourceOwnerClass.EMBEDDING_SHARD_OR_MAP, "embeddings/shard_000000.map.jsonl", EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP),
            (SourceOwnerClass.LEGACY_REPRESENTATION_ARTIFACT, "embeddings/shard_000000.npy", EvidenceSemanticRole.LEGACY_REPRESENTATION),
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
    _insert(connection, "legacy_source_namespaces", source_namespace, "p1:fixture:ws:shared:domain", reserved=True)
    _insert(connection, "idempotency_namespaces", idempotency, "idempotency")
    _insert(connection, "identity_namespaces", empty_target_identity, "empty-target", reserved=True)
    _insert(connection, "identity_namespaces", empty_motif_identity, "empty-motif", reserved=True)
    _insert(connection, "identity_namespaces", empty_membership_identity, "empty-membership", reserved=True)
    _insert(connection, "semantic_scopes", empty_target_scope, "empty-target", reserved=True)
    _insert(connection, "semantic_scopes", empty_unknown_scope, "empty-unknown", reserved=True)
    _insert(connection, "legacy_source_namespaces", empty_motif_alias, "empty-motif-alias", reserved=True)
    _insert(connection, "legacy_source_namespaces", empty_source_namespace, "p1:fixture:ws:private:empty-agent", reserved=True)
    _insert(connection, "idempotency_namespaces", empty_idempotency, "empty-idempotency")
    _insert(connection, "identity_namespaces", motif_target_identity, "motif-target", reserved=True)
    _insert(connection, "identity_namespaces", motif_motif_identity, "motif-motif", reserved=True)
    _insert(connection, "identity_namespaces", motif_membership_identity, "motif-membership", reserved=True)
    _insert(connection, "semantic_scopes", motif_target_scope, "motif-target", reserved=True)
    _insert(connection, "semantic_scopes", motif_unknown_scope, "motif-unknown", reserved=True)
    _insert(connection, "legacy_source_namespaces", motif_motif_alias, "motif-motif-alias", reserved=True)
    _insert(connection, "legacy_source_namespaces", motif_source_namespace, "p1:fixture:ws:shared:empty-domain", reserved=True)
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


def test_p3_carrier_accepts_cross_scope_members_when_the_root_topology_has_one_candidate(carrier_fixture) -> None:
    connection, request = carrier_fixture
    motif_key = RootScopeKey("ws", RootScopeKind.SHARED, domain_id="empty-domain")
    motif_path = request.root / "workspaces" / "ws" / "domains" / "empty-domain" / "motifs.json"
    motif_path.write_text(json.dumps({"motifs": {
        "cross-scope-carrier-motif": {
            "motif_id": "cross-scope-carrier-motif", "domain_id": "empty-domain",
            "label": "cross scope carrier", "centroid": [1.0] + [0.0] * 383,
            "strength": 0.8, "stability_score": 0.8, "contributing_agents": ["smoke_runner"],
            "created_ts": 1, "last_active_ts": 2, "members": list(sorted(_MULTI_MEMORY_EIDS)),
        },
    }}), encoding="utf-8")
    refreshed_motif_evidence = capture_present_source_evidence(
        data_root=request.root,
        owner_class=SourceOwnerClass.MOTIF_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="empty-domain"),
        canonical_locator="motifs.json", semantic_role=EvidenceSemanticRole.MOTIFS, scope_key=motif_key,
    )
    description = replace(
        request.description,
        explicit_source_manifest=RootEvidenceManifest(tuple(
            refreshed_motif_evidence if item.semantic_role is EvidenceSemanticRole.MOTIFS else item
            for item in request.description.explicit_source_manifest.entries
        )),
    )
    cross_scope_request = replace(
        request,
        description=description,
        carrier_directory=request.carrier_root.parent / "cross-scope-member-carrier",
        operation_key="p3-source-carrier-cross-scope-members",
    )
    result = NativeRootP3SourceAdmissionService(connection).admit(cross_scope_request)
    assert result.b1_memory_count == result.b2_memory_count == len(_MULTI_MEMORY_EIDS)
    record = json.loads(result.carrier_record_path.read_text(encoding="utf-8"))
    motif_entry = next(item for item in record["payload"]["scopes"] if item["scope_key"]["domain_id"] == "empty-domain")
    assert [item["runtime_motif_id"] for item in motif_entry["b1"]["motifs"]] == ["cross-scope-carrier-motif"]
    source_binding = next(item for item in cross_scope_request.scope_bindings if item.scope_key.domain_id == "domain")
    motif_binding = next(item for item in cross_scope_request.scope_bindings if item.scope_key == motif_key)
    expected = dict(connection.execute(
        "SELECT alias_value,object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID'",
        (native_id_to_bytes(source_binding.scope_plan.legacy_source_namespace_id),),
    ).fetchall())
    motif_object_id = connection.execute(
        "SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?",
        (native_id_to_bytes(motif_binding.scope_plan.legacy_source_namespace_id), "cross-scope-carrier-motif"),
    ).fetchone()[0]
    endpoints = connection.execute(
        """
        SELECT member.object_id,member.endpoint_semantic_scope_id
        FROM relationships relationship
        JOIN relationship_revision_endpoints motif
          ON motif.relationship_revision_id=relationship.current_revision_id
         AND motif.endpoint_ordinal=0 AND motif.endpoint_role='MOTIF'
        JOIN relationship_revision_endpoints member
          ON member.relationship_revision_id=relationship.current_revision_id
         AND member.endpoint_ordinal=1 AND member.endpoint_role='MEMBER'
        WHERE relationship.relationship_kind='MOTIF_MEMBERSHIP' AND motif.object_id=?
        """,
        (motif_object_id,),
    ).fetchall()
    assert {row[0] for row in endpoints} == {expected[str(eid)] for eid in _MULTI_MEMORY_EIDS}
    assert {row[1] for row in endpoints} == {native_id_to_bytes(source_binding.unknown_semantic_scope_id)}
    assert {row[1] for row in endpoints} != {native_id_to_bytes(motif_binding.unknown_semantic_scope_id)}


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
    expected_p1_keys = {
        ("PRIVATE", "empty-agent"): "p1:fixture:ws:private:empty-agent",
        ("SHARED", "domain"): "p1:fixture:ws:shared:domain",
        ("SHARED", "empty-domain"): "p1:fixture:ws:shared:empty-domain",
    }
    for entry in scopes:
        scope = entry["scope_key"]
        qualifier = scope["agent_id"] or scope["domain_id"]
        manifest = load_snapshot_manifest(Path(entry["manifest_path"]))
        assert manifest.legacy_source_namespace_key == expected_p1_keys[(scope["scope_kind"], qualifier)]
        assert entry["legacy_source_namespace_key"] == manifest.legacy_source_namespace_key
    assert connection.execute(
        "SELECT count(*) FROM legacy_source_namespaces WHERE source_key LIKE 'p1:fixture:%'"
    ).fetchone()[0] == 3
    selected = next(item for item in scopes if item["scope_key"].get("domain_id") == "domain")
    selected_snapshot_id = selected["legacy_snapshot_id"]
    selected_manifest = load_snapshot_manifest(Path(selected["manifest_path"]))
    assert {item.observed_relative_locator for item in selected_manifest.artifacts} >= {
        "nodes.jsonl",
        "embeddings/manifest.json",
        "embeddings/shard_000000.map.jsonl",
        "embeddings/shard_000000.npy",
        "workspaces/ws/workspace_meta.json",
    }
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
    assert [item["eid"] for item in current["b1"]["memories"]] == sorted(_MULTI_MEMORY_EIDS)
    assert {
        item["legacy_vector_strategy"] for item in current["b1"]["memories"]
    } == {"BYTE_DERIVATION_POSSIBLE"}
    assert [item["eid"] for item in current["b2"]["memories"]] == sorted(_MULTI_MEMORY_EIDS)
    assert empty["b1"] == {"memories": [], "motifs": []}
    assert empty["b2"] == {"memories": []}
    assert motif["b1"]["memories"] == []
    assert [item["runtime_motif_id"] for item in motif["b1"]["motifs"]] == sorted(_MULTI_MOTIF_IDS)
    assert motif["b2"] == {"memories": []}
    assert recovered.snapshot_scope_count == 3
    assert recovered.b1_memory_count == recovered.b2_memory_count == len(_MULTI_MEMORY_EIDS)
    current_input = next(
        item for item in recovered.normalization_request.scope_inputs
        if item.scope_key.domain_id == "domain"
    )
    assert [item.eid for item in current_input.b3a_requests] == sorted(_MULTI_MEMORY_EIDS)
    assert len({item.idempotency_key for item in current_input.b3a_requests}) == len(_MULTI_MEMORY_EIDS)
    motif_input = next(
        item for item in recovered.normalization_request.scope_inputs
        if item.scope_key.domain_id == "empty-domain"
    )
    assert [item.runtime_motif_id for item in motif_input.b4c_requests] == sorted(_MULTI_MOTIF_IDS)
    assert len({item.idempotency_key for item in motif_input.b4c_requests}) == len(_MULTI_MOTIF_IDS)
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
        "b3a": 4, "ordinary_b3b": 0, "metadata_less_b3b": 0,
        "total_b3b": 0, "b4a": 0, "b4b": 0, "b4c": 3,
    }
    result = NativeRootWideNormalizationService(connection).normalize(recovered.normalization_request)
    assert result.root_normalization_complete and result.root_normalization_ready


def test_multi_object_recovery_replays_admitted_b1_without_new_snapshot_or_objects(carrier_fixture) -> None:
    connection, request = carrier_fixture
    service = NativeRootP3SourceAdmissionService(connection)
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        service.admit(
            request,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    selected_record = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]
    selected = next(
        item for item in selected_record["scopes"]
        if item["scope_key"].get("domain_id") == "domain"
    )
    selected_snapshot_id = selected["legacy_snapshot_id"]
    selected_manifest_digest = selected["manifest_digest"]
    selected_namespace_id = selected["legacy_source_namespace_id"]
    selected_namespace_key = selected["legacy_source_namespace_key"]

    # This is the real partial-recovery shape: B1 has committed, but no B1
    # carrier payload has been written yet.
    p3_source_admission._run_b1(connection, request, selected)
    object_count_after_first_b1 = connection.execute("SELECT count(*) FROM objects").fetchone()[0]
    p3_source_admission._run_b1(connection, request, selected)
    assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == object_count_after_first_b1
    persisted_before_recovery = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]
    selected_before_recovery = next(
        item for item in persisted_before_recovery["scopes"]
        if item["scope_key"].get("domain_id") == "domain"
    )
    assert selected_before_recovery["b1"] is None
    assert selected_before_recovery["b2"] == {"memories": []}

    recovered = service.admit(request)
    persisted_after_recovery = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]
    selected_after_recovery = next(
        item for item in persisted_after_recovery["scopes"]
        if item["scope_key"].get("domain_id") == "domain"
    )
    assert selected_after_recovery["legacy_snapshot_id"] == selected_snapshot_id
    assert selected_after_recovery["manifest_digest"] == selected_manifest_digest
    assert selected_after_recovery["legacy_source_namespace_id"] == selected_namespace_id
    assert selected_after_recovery["legacy_source_namespace_key"] == selected_namespace_key
    assert [item["eid"] for item in selected_after_recovery["b1"]["memories"]] == sorted(_MULTI_MEMORY_EIDS)
    assert [item["eid"] for item in selected_after_recovery["b2"]["memories"]] == sorted(_MULTI_MEMORY_EIDS)
    assert recovered.b1_memory_count == recovered.b2_memory_count == len(_MULTI_MEMORY_EIDS)
    current_input = next(
        item for item in recovered.normalization_request.scope_inputs
        if item.scope_key.domain_id == "domain"
    )
    assert [item.eid for item in current_input.b3a_requests] == sorted(_MULTI_MEMORY_EIDS)
    assert len({item.idempotency_key for item in current_input.b3a_requests}) == len(_MULTI_MEMORY_EIDS)


def test_per_eid_legacy_vector_strategy_routes_mixed_b3a_and_b3b(carrier_fixture) -> None:
    """A workspace lock is not a shortcut around per-object B1 evidence."""

    connection, request = carrier_fixture
    service = NativeRootP3SourceAdmissionService(connection)
    service.admit(request)
    record = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]
    selected = next(item for item in record["scopes"] if item["scope_key"].get("domain_id") == "domain")
    strategies = {
        2: "BYTE_DERIVATION_POSSIBLE",
        5: "BYTE_DERIVATION_POSSIBLE",
        17: "NO_VECTOR_PRESENT",
        29: "REEMBED_REQUIRED",
    }
    for item in selected["b1"]["memories"]:
        item["legacy_vector_strategy"] = strategies[item["eid"]]
    p3_source_admission._write_record(request.record_path, record)

    routed = service.admit(request)
    scope = next(item for item in routed.normalization_request.scope_inputs if item.scope_key.domain_id == "domain")
    assert [item.eid for item in scope.b3a_requests] == [2, 5]
    assert [item.eid for item in scope.b3b_requests] == [17, 29]
    assert p3_child_request_counts(routed.normalization_request.scope_inputs) == {
        "b3a": 2, "ordinary_b3b": 2, "metadata_less_b3b": 0,
        "total_b3b": 2, "b4a": 0, "b4b": 0, "b4c": 3,
    }


def test_last_jsonl_record_per_eid_preserves_history_without_admitting_an_extra_memory(carrier_fixture) -> None:
    connection, request = carrier_fixture
    source = request.root / "workspaces" / "ws" / "domains" / "domain" / "shared"
    with (source / "nodes.jsonl").open("ab") as stream:
        stream.write(_line({
            "eid": 2,
            "born_step": 99,
            "channel": 1,
            "payload": {
                **_payload(),
                "summary": "latest logical EID 2 record",
            },
        }))
    scope = request.source_scope_plans[0].scope_key
    current_nodes = capture_present_source_evidence(
        data_root=request.root,
        owner_class=SourceOwnerClass.SHARED_GRAPH_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="domain"),
        canonical_locator="nodes.jsonl",
        semantic_role=EvidenceSemanticRole.NODES,
        scope_key=scope,
    )
    history_description = replace(
        request.description,
        explicit_source_manifest=RootEvidenceManifest(tuple(
            item for item in request.description.explicit_source_manifest.entries
            if not (item.scope_key == scope and item.semantic_role is EvidenceSemanticRole.NODES)
        ) + (current_nodes,)),
    )
    history_request = replace(
        request,
        description=history_description,
        carrier_directory=request.carrier_root.parent / "history-carrier",
        operation_key="p3-source-carrier-history",
    )

    result = NativeRootP3SourceAdmissionService(connection).admit(history_request)
    record = json.loads(history_request.record_path.read_text(encoding="utf-8"))["payload"]
    entry = next(item for item in record["scopes"] if item["scope_key"].get("domain_id") == "domain")
    manifest = load_snapshot_manifest(Path(entry["manifest_path"]))
    snapshot = Path(entry["snapshot_root"]) / "nodes.jsonl"

    assert [item["eid"] for item in entry["b1"]["memories"]] == sorted(_MULTI_MEMORY_EIDS)
    assert next(item for item in entry["b1"]["memories"] if item["eid"] == 2)[
        "legacy_vector_strategy"
    ] == "NO_VECTOR_PRESENT"
    assert len(snapshot.read_bytes().splitlines()) == len(_MULTI_MEMORY_EIDS) + 1
    assert any(item.observed_relative_locator == "nodes.jsonl" for item in manifest.artifacts)
    assert result.b1_memory_count == len(_MULTI_MEMORY_EIDS)
    assert connection.execute(
        "SELECT count(*) FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID'",
        (native_id_to_bytes(UUID(entry["legacy_source_namespace_id"])),),
    ).fetchone()[0] == len(_MULTI_MEMORY_EIDS)


def test_completed_carrier_reuses_snapshot_id_and_recovers_partial_b1_with_added_evidence(carrier_fixture) -> None:
    """Complete old snapshots separately; never rewrite their carrier record."""

    connection, request = carrier_fixture
    old_manifest = RootEvidenceManifest(tuple(
        item for item in request.description.explicit_source_manifest.entries
        if item.semantic_role not in {
            EvidenceSemanticRole.WORKSPACE_META,
            EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
            EvidenceSemanticRole.LEGACY_REPRESENTATION,
        }
    ))
    predecessor = replace(
        request,
        description=replace(request.description, explicit_source_manifest=old_manifest),
        carrier_directory=request.carrier_root.parent / "predecessor-carrier",
        operation_key="p3-source-carrier-predecessor",
    )
    service = NativeRootP3SourceAdmissionService(connection)
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        service.admit(
            predecessor,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    predecessor_payload = json.loads(predecessor.record_path.read_text(encoding="utf-8"))["payload"]
    predecessor_entry = next(
        item for item in predecessor_payload["scopes"] if item["scope_key"].get("domain_id") == "domain"
    )
    predecessor_record_bytes = predecessor.record_path.read_bytes()
    predecessor_manifest_bytes = Path(predecessor_entry["manifest_path"]).read_bytes()
    predecessor_snapshot_id = predecessor_entry["legacy_snapshot_id"]
    p3_source_admission._run_b1(connection, predecessor, predecessor_entry)
    first_object_count = connection.execute("SELECT count(*) FROM objects").fetchone()[0]
    first_aliases = connection.execute(
        "SELECT alias_value,object_id FROM legacy_object_aliases "
        "WHERE legacy_source_namespace_id=? AND alias_kind='EID' ORDER BY alias_value",
        (native_id_to_bytes(UUID(predecessor_entry["legacy_source_namespace_id"])),),
    ).fetchall()
    assert predecessor_entry["b1"] is None

    completed_request = replace(
        request,
        carrier_directory=request.carrier_root.parent / "carrier-completion",
        operation_key="p3-source-carrier-completion",
        predecessor_carrier_record_path=predecessor.record_path,
    )
    recovered = service.admit(completed_request)
    completed_record = json.loads(completed_request.record_path.read_text(encoding="utf-8"))["payload"]
    completed_entry = next(
        item for item in completed_record["scopes"] if item["scope_key"].get("domain_id") == "domain"
    )
    completed_manifest = load_snapshot_manifest(Path(completed_entry["manifest_path"]))

    assert predecessor.record_path.read_bytes() == predecessor_record_bytes
    assert Path(predecessor_entry["manifest_path"]).read_bytes() == predecessor_manifest_bytes
    assert completed_entry["legacy_snapshot_id"] == predecessor_snapshot_id
    assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] >= first_object_count
    assert connection.execute(
        "SELECT alias_value,object_id FROM legacy_object_aliases "
        "WHERE legacy_source_namespace_id=? AND alias_kind='EID' ORDER BY alias_value",
        (native_id_to_bytes(UUID(predecessor_entry["legacy_source_namespace_id"])),),
    ).fetchall() == first_aliases
    assert [item["eid"] for item in completed_entry["b1"]["memories"]] == sorted(_MULTI_MEMORY_EIDS)
    assert {
        item["legacy_vector_strategy"] for item in completed_entry["b1"]["memories"]
    } == {"BYTE_DERIVATION_POSSIBLE"}
    assert {item.observed_relative_locator for item in completed_manifest.artifacts} >= {
        "workspaces/ws/workspace_meta.json",
        "embeddings/shard_000000.map.jsonl",
        "embeddings/shard_000000.npy",
    }
    completion = completed_record["carrier_completion"]
    assert completion["predecessor_record_path"] == str(predecessor.record_path)
    assert any(item["legacy_snapshot_id"] == predecessor_snapshot_id for item in completion["completed_snapshots"])
    assert recovered.b1_memory_count == recovered.b2_memory_count == len(_MULTI_MEMORY_EIDS)


def test_multi_motif_carrier_evidence_composes_one_b4c_per_motif(carrier_fixture) -> None:
    connection, request = carrier_fixture
    result = NativeRootP3SourceAdmissionService(connection).admit(request)
    scopes = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]["scopes"]
    motif = next(item for item in scopes if item["scope_key"].get("domain_id") == "empty-domain")
    assert [item["runtime_motif_id"] for item in motif["b1"]["motifs"]] == sorted(_MULTI_MOTIF_IDS)
    motif_input = next(
        item for item in result.normalization_request.scope_inputs
        if item.scope_key.domain_id == "empty-domain"
    )
    assert len(motif_input.b4c_requests) == len(_MULTI_MOTIF_IDS)
    assert len({item.idempotency_key for item in motif_input.b4c_requests}) == len(_MULTI_MOTIF_IDS)


def test_hash_source_geometry_composes_b4b_from_each_admitted_motif(carrier_fixture) -> None:
    connection, request = carrier_fixture
    workspace = request.root / "workspaces" / "ws"
    (workspace / "workspace_meta.json").write_text(json.dumps({
        "embed_provider": "hash", "embed_model": "hash:384:torment", "embed_dim": 384,
    }), encoding="utf-8")
    motifs_path = workspace / "domains" / "domain" / "motifs.json"
    motifs_path.parent.mkdir(parents=True, exist_ok=True)
    motifs_path.write_text(json.dumps({"motifs": {
        motif_id: {
            "motif_id": motif_id, "domain_id": "domain", "label": motif_id,
            "centroid": [1.0] + [0.0] * 383, "strength": 0.8, "stability_score": 0.8,
            "contributing_agents": [], "created_ts": 1, "last_active_ts": 2, "members": [],
        }
        for motif_id in ("hash-motif-a", "hash-motif-b", "hash-motif-c")
    }}), encoding="utf-8")
    main_scope = request.source_scope_plans[0].scope_key
    current_meta = capture_present_source_evidence(
        data_root=request.root,
        owner_class=SourceOwnerClass.WORKSPACE_IDENTITY_METADATA,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.WORKSPACE),
        canonical_locator="workspace_meta.json",
        semantic_role=EvidenceSemanticRole.WORKSPACE_META,
    )
    motif_evidence = capture_present_source_evidence(
        data_root=request.root,
        owner_class=SourceOwnerClass.MOTIF_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="domain"),
        canonical_locator="motifs.json",
        semantic_role=EvidenceSemanticRole.MOTIFS,
        scope_key=main_scope,
    )
    corrected_manifest = RootEvidenceManifest(tuple(
        item for item in request.description.explicit_source_manifest.entries
        if item.semantic_role is not EvidenceSemanticRole.WORKSPACE_META
    ) + (current_meta, motif_evidence))
    workspace_plan = request.description.workspace_plans[0]
    corrected_workspace = replace(
        workspace_plan,
        shared_materialized_scopes=(
            replace(
                workspace_plan.shared_materialized_scopes[0],
                representation_disposition=RootRepresentationDisposition.REEMBED_REQUIRED,
            ),
            *workspace_plan.shared_materialized_scopes[1:],
        ),
    )
    corrected_description = replace(
        request.description,
        workspace_plans=(corrected_workspace,),
        expected_census=replace(
            request.description.expected_census,
            representation_disposition_counts=tuple(
                RepresentationDispositionCount(
                    disposition,
                    1 if disposition in {
                        RootRepresentationDisposition.TARGET_COMPATIBLE,
                        RootRepresentationDisposition.REEMBED_REQUIRED,
                        RootRepresentationDisposition.NO_VECTOR,
                    } else 0,
                )
                for disposition in RootRepresentationDisposition
            ),
        ),
        explicit_source_manifest=corrected_manifest,
    )
    hash_request = replace(
        request,
        description=corrected_description,
        source_scope_plans=(
            replace(
                request.source_scope_plans[0],
                representation_disposition=RootRepresentationDisposition.REEMBED_REQUIRED,
                motif_presence=SourceArtifactPresence.PRESENT,
            ),
            *request.source_scope_plans[1:],
        ),
        carrier_directory=request.carrier_root.parent / "hash-regeometry-carrier",
        operation_key="p3-source-carrier-hash-regeometry",
    )

    result = NativeRootP3SourceAdmissionService(connection).admit(hash_request)
    scope = next(item for item in result.normalization_request.scope_inputs if item.scope_key == main_scope)
    assert not scope.b3a_requests
    assert len(scope.b3b_requests) == len(_MULTI_MEMORY_EIDS)
    assert not scope.b4a_requests
    assert [item.runtime_motif_id for item in scope.b4b_requests] == [
        "hash-motif-a", "hash-motif-b", "hash-motif-c",
    ]


def test_unknown_identity_carrier_requires_exact_b1_eid_evidence_set(carrier_fixture) -> None:
    connection, request = carrier_fixture
    source_plan = request.source_scope_plans[0]
    workspace_plan = request.description.workspace_plans[0]
    unknown_description = replace(
        request.description,
        workspace_plans=(replace(
            workspace_plan,
            shared_materialized_scopes=(
                replace(
                    workspace_plan.shared_materialized_scopes[0],
                    representation_disposition=RootRepresentationDisposition.UNKNOWN_IDENTITY,
                ),
                *workspace_plan.shared_materialized_scopes[1:],
            ),
        ),),
        expected_census=replace(
            request.description.expected_census,
            representation_disposition_counts=tuple(
                RepresentationDispositionCount(
                    disposition,
                    1 if disposition in {
                        RootRepresentationDisposition.TARGET_COMPATIBLE,
                        RootRepresentationDisposition.UNKNOWN_IDENTITY,
                        RootRepresentationDisposition.NO_VECTOR,
                    } else 0,
                )
                for disposition in RootRepresentationDisposition
            ),
        ),
    )
    nodes = next(
        item for item in request.description.explicit_source_manifest.entries
        if item.scope_key == source_plan.scope_key and item.semantic_role is EvidenceSemanticRole.NODES
    )
    vectors = next(
        item for item in request.description.explicit_source_manifest.entries
        if item.scope_key == source_plan.scope_key
        and item.semantic_role is EvidenceSemanticRole.LEGACY_REPRESENTATION
    )
    incomplete_evidence = tuple(
        MetadataLessPerEidEvidence(
            scope_key=source_plan.scope_key,
            eid=eid,
            vector_evidence=vectors,
            canonical_text_evidence=nodes,
            dtype="float32",
            shape=(384,),
            metadata_less_source_evidence_identity=f"fixture-eid-{eid}",
        )
        for eid in sorted(_MULTI_MEMORY_EIDS)[:-1]
    )
    unknown_request = replace(
        request,
        description=unknown_description,
        source_scope_plans=(
            replace(
                source_plan,
                representation_disposition=RootRepresentationDisposition.UNKNOWN_IDENTITY,
            ),
            *request.source_scope_plans[1:],
        ),
        unknown_identity_evidence=incomplete_evidence,
        carrier_directory=request.carrier_root.parent / "unknown-eid-mismatch",
    )
    with pytest.raises(
        RootP3SourceAdmissionRefused,
        match="P3_CARRIER_UNKNOWN_IDENTITY_EID_SET_MISMATCH",
    ):
        NativeRootP3SourceAdmissionService(connection).admit(unknown_request)


def test_missing_p1_namespace_refuses_before_carrier_or_b1_mutation(carrier_fixture) -> None:
    connection, request = carrier_fixture
    binding = request.scope_bindings[0]
    missing_plan = replace(
        binding.scope_plan,
        legacy_source_namespace_id=generate_native_id(),
    )
    missing_request = replace(
        request,
        scope_bindings=(
            replace(binding, scope_plan=missing_plan),
            *request.scope_bindings[1:],
        ),
        carrier_directory=request.carrier_root.parent / "missing-p1-namespace",
    )
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CARRIER_P1_SOURCE_NAMESPACE_MISSING"):
        NativeRootP3SourceAdmissionService(connection).admit(missing_request)
    assert not missing_request.carrier_root.exists()
    assert connection.execute("SELECT count(*) FROM legacy_snapshots").fetchone()[0] == 0


def test_recovery_refuses_manifest_key_that_contradicts_p1(carrier_fixture) -> None:
    connection, request = carrier_fixture
    service = NativeRootP3SourceAdmissionService(connection)
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        service.admit(
            request,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    entry = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]["scopes"][0]
    manifest_path = Path(entry["manifest_path"])
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["legacy_source_namespace"]["source_key"] = "contradictory-p1-namespace-key"
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(
        RootP3SourceAdmissionRefused,
        match="P3_CARRIER_P1_SOURCE_NAMESPACE_BINDING_MISMATCH",
    ):
        service.admit(request)
    assert connection.execute("SELECT count(*) FROM legacy_snapshots").fetchone()[0] == 0


def test_frozen_real_p3_pre_b1_scope_shape_counts_remain_closed() -> None:
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
    assert pre_b1_p3_scope_shape_counts(tuple(plans), tuple(unknown)) == {
        "target_compatible_memory_scope_count": 47,
        "ordinary_reembed_memory_scope_count": 25,
        "unknown_identity_evidence_count": 3,
        "motif_present_scope_count": 47,
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
