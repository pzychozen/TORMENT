"""Disposable qualification for the recoverable P3 B1/B2 source carrier."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import numpy as np
import pytest

import torment_service.substrate.migration.root_p3_source_admission as p3_source_admission
import torment_service.substrate.migration.root_p3_character_witness_continuation as p3_character_continuation
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.character import CharacterSeed, CharacterStore, _split_seed_text
from torment_service.substrate.character_seed_witness import (
    CharacterSeedWitness, read_legacy_character_seed_witness,
    read_legacy_character_seed_witness_from_frozen_bytes,
)
from torment_service.substrate.canonical_intent import canonical_intent_text
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration.certified_refusal_runtime_proof import (
    CertifiedRefusalRuntimeProofFailed,
    CertifiedRefusalRuntimeSource,
    prove_certified_refusal_runtime_negative,
)
from torment_service.substrate.root_blocker5_binding import _require_normalization_complete
from torment_service.substrate.relationships import Endpoint, NativeRelationshipService, RelationshipState
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.migration import (
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidenceAbsenceReason,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExpectedRootCensus,
    ExternalOwnerObservation,
    ExternalOwnerObservationKind,
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
    RootB2CertifiedRefusalDisposition,
    RootNormalizationScopeInput,
    RootP3ScopeBinding,
    RootP3CertifiedRefusalSourceMember,
    RootP3CharacterWitnessInput,
    RootP3ExternalOwnerObservationAuthority,
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
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
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


def test_p3_certifies_source_semantic_gap_without_creating_b2_or_runtime_access(
    carrier_fixture,
) -> None:
    """A missing governance/lifecycle pair reaches terminal refusal, not R2."""

    connection, request = carrier_fixture
    nodes_path = request.root / "workspaces" / "ws" / "domains" / "domain" / "shared" / "nodes.jsonl"
    rows = [json.loads(line) for line in nodes_path.read_text(encoding="utf-8").splitlines()]
    refused_eid = min(_MULTI_MEMORY_EIDS)
    refused = next(item for item in rows if item["eid"] == refused_eid)
    refused["payload"].pop("governance")
    refused["payload"].pop("lifecycle_status")
    nodes_path.write_bytes(b"".join(_line(item) for item in rows))
    scope = request.source_scope_plans[0].scope_key
    refreshed_nodes = capture_present_source_evidence(
        data_root=request.root,
        owner_class=SourceOwnerClass.SHARED_GRAPH_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="domain"),
        canonical_locator="nodes.jsonl",
        semantic_role=EvidenceSemanticRole.NODES,
        scope_key=scope,
    )
    source_namespace = next(
        item for item in request.scope_bindings if item.scope_key == scope
    ).scope_plan.legacy_source_namespace_id
    selected_raw_row = next(
        line for line in nodes_path.read_bytes().splitlines(keepends=True)
        if json.loads(line.decode("utf-8"))["eid"] == refused_eid
    )
    refusal_member = RootP3CertifiedRefusalSourceMember(
        scope_key=scope,
        legacy_source_namespace_id=source_namespace,
        eid=refused_eid,
        selected_raw_row_sha256=hashlib.sha256(selected_raw_row).hexdigest(),
        nodes_source_artifact_sha256=refreshed_nodes.sha256_hex or "",
    )
    refused_request = replace(
        request,
        description=replace(
            request.description,
            explicit_source_manifest=RootEvidenceManifest(tuple(
                refreshed_nodes if item.scope_key == scope and item.semantic_role is EvidenceSemanticRole.NODES
                else item
                for item in request.description.explicit_source_manifest.entries
            )),
        ),
        carrier_directory=request.carrier_root.parent / "semantic-gap-carrier",
        operation_key="p3-source-semantic-gap",
        certified_refusal_source_members=(refusal_member,),
    )

    result = NativeRootP3SourceAdmissionService(connection).admit(refused_request)
    assert result.b1_memory_count == len(_MULTI_MEMORY_EIDS)
    assert result.b2_memory_count == len(_MULTI_MEMORY_EIDS) - 1
    assert result.b2_refused_memory_count == 1
    assert result.root_disposition_closed
    assert result.completion_class == "P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS"
    assert result.final_evidence_set_e_digest is not None
    assert p3_child_request_counts(result.normalization_request.scope_inputs)["b3a"] == len(_MULTI_MEMORY_EIDS) - 1
    refusal_input = next(item for item in result.normalization_request.scope_inputs if item.scope_key == scope)
    assert len(refusal_input.b2_refused_memory_dispositions) == 1
    root_result = NativeRootWideNormalizationService(connection).normalize(result.normalization_request)
    assert root_result.b2_certified_refused_memory_count == 1
    assert root_result.b3_completed_memory_count == len(_MULTI_MEMORY_EIDS) - 1
    assert root_result.root_memory_disposition_closed
    assert not root_result.root_normalization_ready
    # P4 consumes P3's complete source disposition, which is intentionally
    # distinct from generalized staging-runtime readiness in this B2 refusal.
    _require_normalization_complete(root_result, refused_request.description)

    carrier = json.loads(refused_request.record_path.read_text(encoding="utf-8"))["payload"]
    certification = carrier["b2_refusal_certification"]
    terminal_evidence = carrier["terminal_disposition_evidence"]
    assert terminal_evidence["final_evidence_set_e_digest"] == result.final_evidence_set_e_digest
    assert certification["final_evidence_set_e_digest"] != result.final_evidence_set_e_digest
    evidence = json.loads(Path(certification["evidence_path"]).read_text(encoding="utf-8"))
    certificate = json.loads(Path(certification["certificate_path"]).read_text(encoding="utf-8"))
    terminal = json.loads(Path(terminal_evidence["path"]).read_text(encoding="utf-8"))
    assert evidence["payload"]["exception_count"] == 1
    assert certificate["payload"]["final_evidence_set_e_digest"] == certification["final_evidence_set_e_digest"]
    assert terminal["payload"]["b4_partition"] == {
        "b4a": 0, "b4b": 0, "b4c": 3, "b4p": 0,
        "b4_refused_member_semantic_gap": 0, "total": 3,
        "unaccounted": 0, "overlap": 0,
    }

    b1 = next(item for item in carrier["scopes"] if item["scope_key"] == scope.identity_payload())["b1"]
    b2 = next(item for item in carrier["scopes"] if item["scope_key"] == scope.identity_payload())["b2"]
    refused_b1 = next(item for item in b1["memories"] if item["eid"] == refused_eid)
    refused_b2 = next(item for item in b2["memories"] if item["eid"] == refused_eid)
    assert refused_b1["normalization_kind"] == "B2_REFUSED_SOURCE_SEMANTIC_GAP"
    assert refused_b2["disposition"] == "B2_REFUSED_SOURCE_SEMANTIC_GAP"
    assert connection.execute(
        """SELECT lineage_kind FROM object_revisions
             WHERE object_id=? AND object_revision_id=? AND revision_ordinal=1""",
        (UUID(refused_b1["object_id"]).bytes, UUID(refused_b1["r1_revision_id"]).bytes),
    ).fetchone() == ("LEGACY_PREDECESSOR_UNKNOWN",)
    operation_id = UUID(refused_b2["receipt_operation_id"]).bytes
    assert connection.execute(
        "SELECT operation_kind FROM operations WHERE operation_id=?", (operation_id,)
    ).fetchone() == ("P3_B2_REFUSED_SOURCE_SEMANTIC_GAP",)
    assert connection.execute(
        "SELECT rejection_code FROM operation_rejections WHERE operation_id=?", (operation_id,)
    ).fetchone() == ("B2_REFUSED_SOURCE_SEMANTIC_GAP",)
    assert connection.execute(
        "SELECT count(*) FROM semantic_transitions WHERE operation_id=?", (operation_id,)
    ).fetchone() == (0,)
    assert connection.execute(
        "SELECT count(*) FROM operation_outputs WHERE operation_id=?", (operation_id,)
    ).fetchone() == (0,)
    with pytest.raises(SubstrateInvariantViolation, match="RUNTIME_SEMANTIC_ADMISSION_REFUSED"):
        NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
            legacy_source_namespace_id=source_namespace, eid=refused_eid,
        )

    # Existing identity relationships need not be deleted, but their semantic
    # compatibility projection must reject an endpoint whose current revision
    # remains only legacy R1 evidence.
    admitted_b1 = next(item for item in b1["memories"] if item["eid"] != refused_eid)
    binding = next(item for item in refused_request.scope_bindings if item.scope_key == scope).scope_plan
    admitted_object_id = UUID(bytes=connection.execute(
        """SELECT object_id FROM legacy_object_aliases
             WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value=?""",
        (native_id_to_bytes(binding.legacy_source_namespace_id), str(admitted_b1["eid"])),
    ).fetchone()[0])
    relationship = NativeRelationshipService(connection).create_relationship(
        idempotency_namespace_id=binding.idempotency_namespace_id,
        idempotency_key="refused-identity-link",
        state=RelationshipState(
            binding.target_identity_namespace_id,
            binding.target_semantic_scope_id,
            "LINK", "EXISTS", "UNSET", True, "QUALIFIED", "NOT_APPLICABLE",
            (
                Endpoint(0, "SOURCE", binding.target_semantic_scope_id, UUID(refused_b1["object_id"])),
                Endpoint(1, "TARGET", binding.target_semantic_scope_id, admitted_object_id),
            ),
            {"weight": 1.0}, "JSON",
        ),
    )
    assert connection.execute(
        "SELECT count(*) FROM relationships WHERE relationship_id=?",
        (native_id_to_bytes(relationship.relationship_id),),
    ).fetchone() == (1,)
    with pytest.raises(SubstrateInvariantViolation, match="RUNTIME_SEMANTIC_ADMISSION_REFUSED"):
        NativeMemoryCompatibilityFacade(connection).get_memory_relationship(
            relationship_id=relationship.relationship_id,
            source_legacy_source_namespace_id=source_namespace,
            target_legacy_source_namespace_id=source_namespace,
        )

    replay = NativeRootP3SourceAdmissionService(connection).admit(refused_request)
    assert replay.b2_memory_count == result.b2_memory_count
    assert replay.b2_refused_memory_count == 1
    assert connection.execute(
        "SELECT count(*) FROM operations WHERE operation_kind='P3_B2_REFUSED_SOURCE_SEMANTIC_GAP'"
    ).fetchone() == (1,)

    # B1 historical vector bytes are lawful evidence even though this source
    # has no B2 successor.  The proof intentionally separates those captures
    # from native runtime representations and exercises both runtime owners.
    runtime_scope = NativeMemoryRuntimeScope(
        workspace_id=binding.workspace_id,
        scope_kind=binding.scope_kind,
        legacy_source_namespace_id=binding.legacy_source_namespace_id,
        identity_namespace_id=binding.target_identity_namespace_id,
        semantic_scope_id=binding.target_semantic_scope_id,
        agent_id=binding.agent_id,
        domain_id=binding.domain_id,
    )
    refusal_source = CertifiedRefusalRuntimeSource(
        eid=refused_eid,
        object_id=UUID(refused_b1["object_id"]),
        r1_revision_id=UUID(refused_b1["r1_revision_id"]),
        scope=runtime_scope,
    )
    proof = prove_certified_refusal_runtime_negative(
        connection,
        sources=(refusal_source,),
        native_core_database_path=refused_request.native_core_database_path,
        expected_native_core_id=refused_request.expected_native_core_id,
        representation_lane=_lane(),
        vector_embedder=_Embedder(),
    )
    assert proof.legacy_current_r1_count == 1
    assert proof.native_ordinary_successor_count == 0
    assert proof.legacy_evidence_capture_count == 1
    assert proof.certified_refusal_with_no_capture_count == 0
    assert proof.other_representation_count == 0
    assert proof.runtime_compat_embedding_count == 0
    assert proof.ready_usable_runtime_representation_count == 0
    assert proof.qualified_embedding_reader_result_count == 0
    assert proof.qualified_embedding_reader_refusal_count == 1
    assert proof.native_vector_candidate_count == 0
    assert proof.native_vector_search_hit_count == 0

    # A READY/USABLE COMPAT_EMBEDDING on the same refused R1 must trip the
    # proof, even though the semantic reader gate remains independently
    # fail-closed on the legacy-only lineage.
    payload = np.asarray([1.0] + [0.0] * 383, dtype=np.float32).tobytes()
    representations = NativeRepresentationService(connection)
    pending = representations.create_representation_pending(
        idempotency_namespace_id=binding.idempotency_namespace_id,
        idempotency_key="certified-refusal-illegal-runtime-embedding",
        request=RepresentationRequest(
            "OBJECT_REVISION", refusal_source.object_id, refusal_source.r1_revision_id,
            None, None, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
            "float32", 384, (), None, len(payload),
        ),
    )
    representations.establish_representation_integrity_expectation(
        idempotency_namespace_id=binding.idempotency_namespace_id,
        idempotency_key="certified-refusal-illegal-runtime-embedding-expectation",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
            hashlib.sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    representations.publish_representation_ready(
        idempotency_namespace_id=binding.idempotency_namespace_id,
        idempotency_key="certified-refusal-illegal-runtime-embedding-ready",
        request=RepresentationReadyRequest(
            pending.representation_id, "COMPAT_EMBEDDING", 1, "compat-embedding-v1",
            "RAW_VECTOR", payload,
        ),
    )
    with pytest.raises(CertifiedRefusalRuntimeProofFailed) as error:
        prove_certified_refusal_runtime_negative(
            connection,
            sources=(refusal_source,),
            native_core_database_path=refused_request.native_core_database_path,
            expected_native_core_id=refused_request.expected_native_core_id,
            representation_lane=_lane(),
            vector_embedder=_Embedder(),
        )
    assert error.value.proof.runtime_compat_embedding_count == 1
    assert error.value.proof.ready_usable_runtime_representation_count == 1


def test_p3_refuses_dependent_exact_motifs_with_only_frozen_b2_gap_members(
    carrier_fixture,
) -> None:
    """B4 binds the resolved source member namespace, never the motif scope."""

    connection, request = carrier_fixture
    main_scope = next(item.scope_key for item in request.scope_bindings if item.scope_key.domain_id == "domain")
    motif_scope = next(item.scope_key for item in request.scope_bindings if item.scope_key.domain_id == "empty-domain")
    source_namespace = next(
        item.scope_plan.legacy_source_namespace_id
        for item in request.scope_bindings if item.scope_key == main_scope
    )
    motif_binding = next(item for item in request.scope_bindings if item.scope_key == motif_scope)

    nodes_path = request.root / "workspaces" / "ws" / "domains" / "domain" / "shared" / "nodes.jsonl"
    rows = [json.loads(line) for line in nodes_path.read_text(encoding="utf-8").splitlines()]
    refused_eids = (2, 5)
    for row in rows:
        if row["eid"] in refused_eids:
            row["payload"].pop("governance")
            row["payload"].pop("lifecycle_status")
    nodes_path.write_bytes(b"".join(_line(item) for item in rows))
    refreshed_nodes = capture_present_source_evidence(
        data_root=request.root,
        owner_class=SourceOwnerClass.SHARED_GRAPH_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="domain"),
        canonical_locator="nodes.jsonl", semantic_role=EvidenceSemanticRole.NODES,
        scope_key=main_scope,
    )

    motifs_path = request.root / "workspaces" / "ws" / "domains" / "empty-domain" / "motifs.json"
    motifs_path.write_text(json.dumps({"motifs": {
        "one-refused-member": {
            "motif_id": "one-refused-member", "domain_id": "empty-domain",
            "label": "one refused", "centroid": [1.0] + [0.0] * 383,
            "strength": 0.8, "stability_score": 0.8, "contributing_agents": [],
            "created_ts": 1, "last_active_ts": 2, "members": [2],
        },
        "several-refused-members": {
            "motif_id": "several-refused-members", "domain_id": "empty-domain",
            "label": "several refused", "centroid": [1.0] + [0.0] * 383,
            "strength": 0.8, "stability_score": 0.8, "contributing_agents": [],
            "created_ts": 1, "last_active_ts": 2, "members": [5, 2, 17],
        },
    }}), encoding="utf-8")
    refreshed_motifs = capture_present_source_evidence(
        data_root=request.root,
        owner_class=SourceOwnerClass.MOTIF_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="empty-domain"),
        canonical_locator="motifs.json", semantic_role=EvidenceSemanticRole.MOTIFS,
        scope_key=motif_scope,
    )
    raw_rows = {
        json.loads(line.decode("utf-8"))["eid"]: line
        for line in nodes_path.read_bytes().splitlines(keepends=True)
    }
    refusal_members = tuple(
        RootP3CertifiedRefusalSourceMember(
            scope_key=main_scope,
            legacy_source_namespace_id=source_namespace,
            eid=eid,
            selected_raw_row_sha256=hashlib.sha256(raw_rows[eid]).hexdigest(),
            nodes_source_artifact_sha256=refreshed_nodes.sha256_hex or "",
        )
        for eid in refused_eids
    )
    refused_request = replace(
        request,
        description=replace(
            request.description,
            explicit_source_manifest=RootEvidenceManifest(tuple(
                refreshed_nodes if item.scope_key == main_scope and item.semantic_role is EvidenceSemanticRole.NODES
                else refreshed_motifs if item.scope_key == motif_scope and item.semantic_role is EvidenceSemanticRole.MOTIFS
                else item
                for item in request.description.explicit_source_manifest.entries
            )),
        ),
        carrier_directory=request.carrier_root.parent / "dependent-motif-semantic-gap-carrier",
        operation_key="p3-dependent-motif-semantic-gap",
        certified_refusal_source_members=refusal_members,
    )

    admission = NativeRootP3SourceAdmissionService(connection).admit(refused_request)
    motif_input = next(
        item for item in admission.normalization_request.scope_inputs if item.scope_key == motif_scope
    )
    assert not (*motif_input.b4a_requests, *motif_input.b4b_requests, *motif_input.b4c_requests)
    assert [item.runtime_motif_id for item in motif_input.b4_refused_motif_dispositions] == [
        "one-refused-member", "several-refused-members",
    ]
    assert p3_child_request_counts(admission.normalization_request.scope_inputs)[
        "b4_refused_member_semantic_gap"
    ] == 2

    normalized = NativeRootWideNormalizationService(connection).normalize(admission.normalization_request)
    assert normalized.root_normalization_complete
    assert normalized.root_memory_disposition_closed
    assert normalized.root_motif_disposition_closed
    assert normalized.b4_certified_refused_motif_count == 2
    assert normalized.p3_completion_class == "P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS"
    assert not normalized.root_normalization_ready
    _require_normalization_complete(normalized, refused_request.description)

    carrier = json.loads(refused_request.record_path.read_text(encoding="utf-8"))["payload"]
    terminal = json.loads(Path(carrier["terminal_disposition_evidence"]["path"]).read_text(encoding="utf-8"))
    assert terminal["payload"]["b4_partition"] == {
        "b4a": 0, "b4b": 0, "b4c": 0, "b4p": 0,
        "b4_refused_member_semantic_gap": 2, "total": 2,
        "unaccounted": 0, "overlap": 0,
    }
    route_entry = next(item for item in carrier["b4_routes"]["scope_routes"] if item["scope_key"] == motif_scope.identity_payload())
    routes = {item["runtime_motif_id"]: item for item in route_entry["routes"]}
    assert [item["eid"] for item in routes["one-refused-member"]["refused_members"]] == [2]
    assert [item["eid"] for item in routes["several-refused-members"]["refused_members"]] == [2, 5]
    for route in routes.values():
        operation_id = UUID(route["receipt_operation_id"]).bytes
        assert connection.execute(
            "SELECT operation_kind FROM operations WHERE operation_id=?", (operation_id,)
        ).fetchone() == ("P3_B4_REFUSED_MEMBER_SEMANTIC_GAP",)
        assert connection.execute(
            "SELECT rejection_code FROM operation_rejections WHERE operation_id=?", (operation_id,)
        ).fetchone() == ("B4_REFUSED_MEMBER_SEMANTIC_GAP",)
        assert connection.execute(
            "SELECT count(*) FROM semantic_transitions WHERE operation_id=?", (operation_id,)
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT count(*) FROM operation_outputs WHERE operation_id=?", (operation_id,)
        ).fetchone() == (0,)
    assert connection.execute("SELECT count(*) FROM objects WHERE object_kind='DERIVED_MOTIF'").fetchone() == (0,)
    assert connection.execute(
        "SELECT count(*) FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID'",
        (native_id_to_bytes(motif_binding.scope_plan.motif_alias_namespace_id),),
    ).fetchone() == (0,)

    # A missing/nonterminal B2 member is not eligible for this narrow refusal.
    record = json.loads(refused_request.record_path.read_text(encoding="utf-8"))["payload"]
    motif_entry = next(item for item in record["scopes"] if item["scope_key"] == motif_scope.identity_payload())
    main_entry = next(item for item in record["scopes"] if item["scope_key"] == main_scope.identity_payload())
    b2_by_namespace = {
        str(source_namespace): p3_source_admission._carrier_b2_memory_evidence(main_entry["b2"]),
    }
    b2_by_namespace[str(source_namespace)].pop(17)
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_B4_ROUTE_MEMBER_B2_MISSING"):
        p3_source_admission._derive_b4_route(
            connection,
            refused_request,
            motif_entry,
            motif_binding,
            next(item for item in refused_request.source_scope_plans if item.scope_key == motif_scope),
            next(item for item in motif_entry["b1"]["motifs"] if item["runtime_motif_id"] == "several-refused-members"),
            next(item for item in motif_entry["b1"]["motif_dispositions"] if item["motif_id"] == "several-refused-members"),
            tuple(sorted(
                (item.scope_plan for item in refused_request.scope_bindings),
                key=lambda item: (item.workspace_id, item.scope_kind, item.qualifier),
            )),
            b2_by_namespace,
            carrier["b2_refusal_certification"],
        )

    replay = NativeRootP3SourceAdmissionService(connection).admit(refused_request)
    assert replay.child_request_counts == admission.child_request_counts
    assert connection.execute(
        "SELECT count(*) FROM operations WHERE operation_kind='P3_B4_REFUSED_MEMBER_SEMANTIC_GAP'"
    ).fetchone() == (2,)


def test_root_memory_disposition_closure_requires_an_exact_disjoint_b1_b2_partition(
    carrier_fixture,
) -> None:
    """A missing or contradictory terminal B2 disposition cannot claim closure."""

    connection, request = carrier_fixture
    admission = NativeRootP3SourceAdmissionService(connection).admit(request)
    normalized_request = admission.normalization_request
    service = NativeRootWideNormalizationService(connection)
    assert service.normalize(normalized_request).root_memory_disposition_closed

    admitted_scope = next(
        item for item in normalized_request.scope_inputs if len(item.b3a_requests) > 1
    )
    admitted_request = admitted_scope.b3a_requests[0]
    missing_scope = replace(
        admitted_scope, b3a_requests=admitted_scope.b3a_requests[1:],
    )
    missing_request = replace(
        normalized_request,
        scope_inputs=tuple(
            missing_scope if item.scope_key == admitted_scope.scope_key else item
            for item in normalized_request.scope_inputs
        ),
    )
    assert not service.normalize(missing_request).root_memory_disposition_closed

    object_id = UUID(bytes=connection.execute(
        """SELECT object_id FROM legacy_object_aliases
             WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value=?""",
        (
            native_id_to_bytes(admitted_request.legacy_source_namespace_id),
            str(admitted_request.eid),
        ),
    ).fetchone()[0])
    contradiction = RootB2CertifiedRefusalDisposition(
        legacy_source_namespace_id=admitted_request.legacy_source_namespace_id,
        eid=admitted_request.eid,
        object_id=object_id,
        r1_revision_id=admitted_request.expected_r1_revision_id,
        receipt_operation_id=generate_native_id(),
        certificate_digest="0" * 64,
    )
    with pytest.raises(ValueError, match="B3 EIDs must be unique"):
        replace(
            admitted_scope,
            b2_refused_memory_dispositions=(contradiction,),
        )


def test_p3_predecessor_core_supersession_retains_snapshots_but_recaptures_b1(carrier_fixture) -> None:
    connection, request = carrier_fixture
    predecessor = replace(
        request,
        carrier_directory=request.carrier_root.parent / "predecessor-core-carrier",
        operation_key="p3-predecessor-core-carrier",
    )
    NativeRootP3SourceAdmissionService(connection).admit(predecessor)
    predecessor_bytes = predecessor.record_path.read_bytes()

    successor_core_id = generate_native_id()
    successor = replace(
        request,
        expected_native_core_id=successor_core_id,
        carrier_directory=request.carrier_root.parent / "successor-core-carrier",
        predecessor_carrier_record_path=predecessor.record_path,
        operation_key="p3-successor-core-carrier",
    )
    completed = p3_source_admission._complete_predecessor_record(connection, successor)

    assert predecessor.record_path.read_bytes() == predecessor_bytes
    assert completed["expected_native_core_id"] == str(successor_core_id)
    assert all(item["b1"] is None for item in completed["scopes"])
    assert completed["carrier_completion"] == {
        "predecessor_record_path": str(predecessor.record_path),
        "predecessor_record_digest": json.loads(predecessor.record_path.read_text(encoding="utf-8"))["digest"],
        "predecessor_native_core_id": str(request.expected_native_core_id),
        "successor_native_core_id": str(successor_core_id),
        "predecessor_core_disposition": "PRESERVED_SUPERSEDED_PREDECESSOR_EVIDENCE",
        "completed_snapshots": [],
        "completed_manifests": [],
        "inherited_snapshots": [
            {
                "scope_key": item["scope_key"],
                "snapshot_root": item["snapshot_root"],
                "manifest_path": item["manifest_path"],
                "legacy_snapshot_id": item["legacy_snapshot_id"],
            }
            for item in completed["scopes"]
        ],
        "previous_b1_scope_reuse_candidate_count": 0,
        "predecessor_b1_revalidation_pending": False,
    }


def test_p3_partial_motif_uses_b1f_certificate_and_b4p_null_projection(carrier_fixture) -> None:
    """A duplicate source occurrence is retained, never partially admitted."""

    connection, request = carrier_fixture
    key = next(item.scope_key for item in request.scope_bindings if item.scope_key.domain_id == "domain")
    motif_path = request.root / "workspaces" / "ws" / "domains" / "domain" / "motifs.json"
    motif_path.parent.mkdir(parents=True, exist_ok=True)
    motif_path.write_text(json.dumps({"motifs": {
        "partial": {
            "motif_id": "partial", "domain_id": "domain", "label": "partial",
            "centroid": [1.0] + [0.0] * 383, "strength": .8, "stability_score": .7,
            "contributing_agents": ["not-an-identity-proof"], "created_ts": 1,
            "last_active_ts": 2, "members": [2, 2, 5],
        },
    }}), encoding="utf-8")
    motif_evidence = capture_present_source_evidence(
        data_root=request.root,
        owner_class=SourceOwnerClass.MOTIF_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="domain"),
        canonical_locator="motifs.json", semantic_role=EvidenceSemanticRole.MOTIFS,
        scope_key=key,
    )
    partial_request = replace(
        request,
        description=replace(
            request.description,
            explicit_source_manifest=RootEvidenceManifest(
                (*request.description.explicit_source_manifest.entries, motif_evidence),
            ),
        ),
        source_scope_plans=tuple(
            replace(item, motif_presence=SourceArtifactPresence.PRESENT)
            if item.scope_key == key else item
            for item in request.source_scope_plans
        ),
        carrier_directory=request.carrier_root.parent / "partial-source-carrier",
        partial_authority_continuation_directory=request.carrier_root.parent / "partial-continuation",
        operation_key="p3-partial-authority-fixture",
    )
    result = NativeRootP3SourceAdmissionService(connection).admit(partial_request)
    assert (
        result.b1f_total_motif_count,
        result.b1f_exact_motif_count,
        result.b1f_partial_motif_count,
        result.b1f_zero_member_motif_count,
    ) == (4, 0, 1, 3)
    assert result.partial_authority_continuation_path is not None
    continuation = json.loads(result.partial_authority_continuation_path.read_text(encoding="utf-8"))["payload"]
    certificate = continuation["partial_certifications"][0]["payload"]
    assert certificate["authority"] == "PARTIAL_LEGACY_OCCURRENCE_AUTHORITY"
    assert certificate["reason"] == "MULTIPLICITY_INCOMPATIBLE"
    assert certificate["raw_occurrence_count"] == 3
    assert certificate["ordered_occurrences"] == [
        {"ordinal": 0, "raw_eid": 2}, {"ordinal": 1, "raw_eid": 2}, {"ordinal": 2, "raw_eid": 5},
    ]
    assert not {
        "native_object_id", "candidate_object_ids", "candidate_namespace_ids",
        "chosen_candidate", "resolution_status",
    }.intersection(certificate)
    source_namespace = next(
        item.scope_plan.legacy_source_namespace_id
        for item in partial_request.scope_bindings if item.scope_key == key
    )
    assert connection.execute(
        "SELECT count(*) FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value='partial'",
        (native_id_to_bytes(source_namespace),),
    ).fetchone()[0] == 0
    assert connection.execute("SELECT count(*) FROM relationships WHERE relationship_kind='MOTIF_MEMBERSHIP'").fetchone()[0] == 0

    normalized = NativeRootWideNormalizationService(connection).normalize(result.normalization_request)
    assert normalized.root_normalization_complete is True
    assert normalized.root_normalization_ready is False
    assert normalized.partial_motif_authority_closure is True
    assert normalized.p3_completion_class == "PARTIAL_MOTIF_AUTHORITY_READY"
    continuation = json.loads(result.partial_authority_continuation_path.read_text(encoding="utf-8"))["payload"]
    assert continuation["b4p_proofs"] == [{
        "partial_certification_digest": continuation["partial_certifications"][0]["digest"],
        "source_motif_payload_digest": certificate["source_motif_payload_digest"],
        "b1m_identity_universe_digest": certificate["b1m_identity_universe_digest"],
        "derived_motif_count": 0,
        "motif_id_alias_count": 0,
        "membership_count": 0,
    }]


def test_b1m_never_calls_motif_admission(carrier_fixture, monkeypatch) -> None:
    connection, request = carrier_fixture
    service = NativeRootP3SourceAdmissionService(connection)
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        service.admit(request, _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION)
    record = json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]
    entry = next(item for item in record["scopes"] if item["scope_key"].get("domain_id") == "domain")

    class _ForbiddenMotifAdmission:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("B1M must not instantiate motif admission")

    monkeypatch.setattr(p3_source_admission, "NativeLegacyMotifAdmissionService", _ForbiddenMotifAdmission)
    p3_source_admission._run_b1m(connection, request, entry)
    namespace = UUID(entry["legacy_source_namespace_id"])
    assert connection.execute(
        "SELECT count(*) FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID'",
        (native_id_to_bytes(namespace),),
    ).fetchone()[0] == len(_MULTI_MEMORY_EIDS)


def test_nonmotif_b1_does_not_require_or_admit_a_motif_member_universe(carrier_fixture, monkeypatch) -> None:
    connection, request = carrier_fixture
    service = NativeRootP3SourceAdmissionService(connection)
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        service.admit(request, _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION)
    record = _completion_payload(request)
    motif_entry = next(item for item in record["scopes"] if item["scope_key"].get("domain_id") == "empty-domain")
    main_scope = RootScopeKey("ws", RootScopeKind.SHARED, domain_id="domain")
    no_member_universe = SimpleNamespace(
        expected_native_core_id=request.expected_native_core_id,
        source_scope_plans=tuple(item for item in request.source_scope_plans if item.scope_key != main_scope),
        scope_bindings=tuple(item for item in request.scope_bindings if item.scope_key != main_scope),
    )

    observed_configs = []
    original_run = p3_source_admission.NativeLegacyMigrationRehearsal.run

    def _observe_run(self, *args, **kwargs):
        observed_configs.append(kwargs["config"])
        return original_run(self, *args, **kwargs)

    def _forbidden_member_universe(*_args, **_kwargs):
        raise AssertionError("non-motif B1 must not ask for a motif member universe")

    monkeypatch.setattr(p3_source_admission.NativeLegacyMigrationRehearsal, "run", _observe_run)
    monkeypatch.setattr(p3_source_admission, "_eligible_member_source_namespace_ids", _forbidden_member_universe)
    before = (
        connection.execute("SELECT count(*) FROM objects WHERE object_kind='LEGACY_DERIVED_MOTIF'").fetchone()[0],
        connection.execute("SELECT count(*) FROM relationships WHERE relationship_kind='MOTIF_MEMBERSHIP'").fetchone()[0],
    )
    p3_source_admission._run_b1_nonmotif_evidence(connection, no_member_universe, motif_entry)
    after = (
        connection.execute("SELECT count(*) FROM objects WHERE object_kind='LEGACY_DERIVED_MOTIF'").fetchone()[0],
        connection.execute("SELECT count(*) FROM relationships WHERE relationship_kind='MOTIF_MEMBERSHIP'").fetchone()[0],
    )

    assert len(observed_configs) == 1
    assert observed_configs[0].include_motif_derivation is False
    assert observed_configs[0].eligible_member_source_namespace_ids is None
    assert after == before


def test_b1f_motif_path_keeps_empty_member_universe_fail_closed(carrier_fixture) -> None:
    connection, request = carrier_fixture
    service = NativeRootP3SourceAdmissionService(connection)
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        service.admit(request, _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION)
    record = _completion_payload(request)
    main_scope = RootScopeKey("ws", RootScopeKind.SHARED, domain_id="domain")
    no_member_universe = SimpleNamespace(
        expected_native_core_id=request.expected_native_core_id,
        source_scope_plans=tuple(item for item in request.source_scope_plans if item.scope_key != main_scope),
        scope_bindings=tuple(item for item in request.scope_bindings if item.scope_key != main_scope),
    )
    reduced_record = {
        **record,
        "scopes": [
            item for item in record["scopes"]
            if item["scope_key"].get("domain_id") != "domain"
        ],
    }
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CARRIER_MOTIF_MEMBER_SCOPE_UNIVERSE_EMPTY"):
        p3_source_admission._run_b1f(connection, no_member_universe, reduced_record, "sealed-universe")


def test_wrong_p1_plan_shape_remains_an_invalid_snapshot_manifest(tmp_path: Path) -> None:
    plan = tmp_path / "p1-bootstrap-plan.json"
    plan.write_text('{"runtime_scopes": []}\n', encoding="utf-8")
    with pytest.raises(SubstrateSnapshotManifestError, match="schema version is incompatible"):
        load_snapshot_manifest(plan)


def _character_p3_request(
    connection, request: RootP3SourceAdmissionRequest, *, motif_members: list[int] | None = None,
) -> tuple[RootP3SourceAdmissionRequest, bytes]:
    """Turn the disposable private-empty scope into a frozen Character source."""

    scope = next(item.scope_key for item in request.scope_bindings if item.scope_key.agent_id == "empty-agent")
    private = request.root / "workspaces" / "ws" / "agents" / "empty-agent" / "private"
    private.mkdir(parents=True)
    seed = CharacterSeed(
        "p3-character-seed-v1", "P3 Character",
        "A first P3 Character concept. A second P3 Character concept.", owner_agent_id="empty-agent",
    )
    concepts = _split_seed_text(seed.seed_text)
    seed.seed_eids = [101, 102]
    seed.seed_motif_id = "p3-character-motif"
    seed.created_ts = 1
    CharacterStore(str(request.root)).save_seed("ws", seed)
    seed_bytes = (request.root / "workspaces" / "ws" / "seeds" / seed.seed_id / "seed.json").read_bytes()
    payloads = [
        {
            "summary": concept, "type": "seed_canon", "mtype": "seed_canon", "memory_class": "core",
            "strength": .95, "confidence": .95, "half_life": seed.core_half_life, "canon": True,
            "user_id": "empty-agent", "created_at": 1, "created_ts": 1, "last_reinforced": 1,
            "seed_id": seed.seed_id, "character_name": seed.character_name, "tier": "core_identity",
            "seed_concept_index": index,
            "lifecycle_status": {"state": "protected", "is_authoritative_on_row": True, "requires_join": None,
                                 "set_by": {"actor": "system", "via": "canon_set", "at": 1}, "history_ref": None},
        }
        for index, concept in enumerate(concepts)
    ]
    (private / "nodes.jsonl").write_bytes(b"".join(
        _line({"eid": eid, "born_step": index + 1, "channel": 1, "payload": payload,
               "embedding_ref": {"shard": 0, "row": index, "dim": 384}})
        for index, (eid, payload) in enumerate(zip(seed.seed_eids, payloads, strict=True))
    ))
    embeddings = private / "embeddings"
    embeddings.mkdir()
    np.save(embeddings / "shard_000000.npy", np.asarray(
        [[1.0] + [0.0] * 383, [0.0, 1.0] + [0.0] * 382], dtype=np.float32,
    ))
    (embeddings / "manifest.json").write_bytes(_line({
        "version": 1, "embedding_dim": 384, "dtype": "float32", "rows_per_shard": 2,
        "active_shard": 0, "next_row": 2, "total_rows": 2,
    }))
    (embeddings / "shard_000000.map.jsonl").write_bytes(b"".join(
        _line({"eid": eid, "row": index, "dimension": 384})
        for index, eid in enumerate(seed.seed_eids)
    ))
    motifs = request.root / "workspaces" / "ws" / "domains" / "domain" / "motifs.json"
    motifs.parent.mkdir(parents=True, exist_ok=True)
    motifs.write_text(json.dumps({"motifs": {
        seed.seed_motif_id: {
            "motif_id": seed.seed_motif_id, "domain_id": "domain", "label": "P3 Character",
            "centroid": [1.0] + [0.0] * 383, "strength": .8, "stability_score": .8,
            "contributing_agents": ["empty-agent"], "created_ts": 1, "last_active_ts": 1,
            "members": seed.seed_eids if motif_members is None else motif_members,
        },
    }}), encoding="utf-8")
    witness = read_legacy_character_seed_witness(
        workspace_root=request.root / "workspaces" / "ws", workspace_id="ws", agent_id="empty-agent",
        domain_id="domain", requested_seed_id=seed.seed_id,
    )
    private_owner = EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="empty-agent")
    shared_key = next(item.scope_key for item in request.scope_bindings if item.scope_key.domain_id == "domain")
    motif_owner = EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="domain")
    private_evidence = tuple(
        capture_present_source_evidence(
            data_root=request.root, owner_class=owner_class, owner_boundary=private_owner,
            canonical_locator=locator, semantic_role=role, scope_key=scope,
        )
        for owner_class, locator, role in (
            (SourceOwnerClass.PRIVATE_GRAPH_SOURCE, "nodes.jsonl", EvidenceSemanticRole.NODES),
            (SourceOwnerClass.EMBEDDING_MANIFEST, "embeddings/manifest.json", EvidenceSemanticRole.EMBEDDING_MANIFEST),
            (SourceOwnerClass.EMBEDDING_SHARD_OR_MAP, "embeddings/shard_000000.map.jsonl", EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP),
            (SourceOwnerClass.LEGACY_REPRESENTATION_ARTIFACT, "embeddings/shard_000000.npy", EvidenceSemanticRole.LEGACY_REPRESENTATION),
        )
    )
    motif_evidence = capture_present_source_evidence(
        data_root=request.root, owner_class=SourceOwnerClass.MOTIF_SOURCE, owner_boundary=motif_owner,
        canonical_locator="motifs.json", semantic_role=EvidenceSemanticRole.MOTIFS, scope_key=shared_key,
    )
    observation = ExternalOwnerObservation(
        "ws", ExternalOwnerObservationKind.CHARACTER, f"seed:{seed.seed_id}",
        hashlib.sha256(seed_bytes).hexdigest(),
    )
    workspace = request.description.workspace_plans[0]
    description = replace(
        request.description,
        workspace_plans=(replace(
            workspace,
            private_materialized_scopes=(MaterializedRootScopePlan(
                scope, RootRepresentationDisposition.TARGET_COMPATIBLE,
            ),),
            identity_only_agents=(),
        ),),
        expected_census=replace(
            request.description.expected_census,
            empty_private_identity_scope_count=0,
            representation_disposition_counts=tuple(
                RepresentationDispositionCount(
                    disposition, 3 if disposition is RootRepresentationDisposition.TARGET_COMPATIBLE else 0,
                ) for disposition in RootRepresentationDisposition
            ),
        ),
        explicit_source_manifest=RootEvidenceManifest(tuple(
            item for item in request.description.explicit_source_manifest.entries
            if item.scope_key != scope and not (
                item.scope_key == shared_key and item.semantic_role is EvidenceSemanticRole.MOTIFS
            )
        ) + private_evidence + (motif_evidence,)),
        external_owner_observations=(observation,),
    )
    binding = next(item for item in request.scope_bindings if item.scope_key == scope)
    # The private plan intentionally carries no generic motif-domain hint.
    # Character derives its own bounded witness domain from the frozen P2/P3
    # evidence below; that result must not leak back into this generic plan.
    private_plan = binding.scope_plan
    authority = RootP3ExternalOwnerObservationAuthority(
        "0" * 64, description.external_owner_observation_digest, (observation,),
    )
    return replace(
        request,
        description=description,
        source_scope_plans=tuple(
            replace(item, materialization_posture=MaterializedScopePosture.MEMORY_GRAPH,
                    representation_disposition=RootRepresentationDisposition.TARGET_COMPATIBLE,
                    motif_domain_id=None) if item.scope_key == scope else
            replace(item, motif_presence=SourceArtifactPresence.PRESENT) if item.scope_key == shared_key else item
            for item in request.source_scope_plans
        ),
        scope_bindings=request.scope_bindings,
        carrier_directory=request.carrier_root.parent / "character-source-carrier",
        operation_key="p3-character-source-carrier",
        character_observation_authority=authority,
        character_witness_inputs=(RootP3CharacterWitnessInput(
            scope, private_plan.legacy_source_namespace_id, seed_bytes, witness.descriptor_payload(),
        ),),
        character_continuation_carrier_directory=request.carrier_root.parent / "character-continuation",
    ), seed_bytes


def _historical_descriptor_payload(witness: CharacterSeedWitness) -> dict[str, object]:
    """Produce the established descriptor checksum form predating P3 additions."""

    descriptor = witness.descriptor_payload()
    descriptor.pop("seed_definition_compatibility")
    descriptor.pop("derived_owner_agent_id")
    descriptor.pop("lifecycle_compatibility")
    historic_digest_payload = {
        "workspace_id": witness.workspace_id,
        "agent_id": witness.agent_id,
        "domain_id": witness.domain_id,
        "seed_definition_digest": witness.seed_definition_digest,
        "seed_id": witness.seed_id,
        "character_name": witness.character_name,
        "seed_eids": list(witness.seed_eids),
        "seed_motif_id": witness.seed_motif_id,
        "seed_motif_member_eids": list(witness.seed_motif_member_eids),
        "seed_motif_seed_eids": list(witness.seed_motif_seed_eids),
        "concept_summaries": list(witness.concept_summaries),
    }
    descriptor["witness_digest"] = hashlib.sha256(
        canonical_intent_text(historic_digest_payload).encode("utf-8"),
    ).hexdigest()
    return descriptor


def test_p3_character_historical_descriptor_digest_uses_character_compatibility_on_initial_and_reload(
    carrier_fixture,
) -> None:
    connection, request = carrier_fixture
    character_request, seed_bytes = _character_p3_request(connection, request)
    input_value = character_request.character_witness_inputs[0]
    current = CharacterSeedWitness.from_descriptor_payload(
        workspace_id=input_value.scope_key.workspace_id,
        agent_id=input_value.scope_key.agent_id or "",
        domain_id="domain",
        value=input_value.descriptor_payload,
    )
    historical_descriptor = _historical_descriptor_payload(current)
    historical = CharacterSeedWitness.from_descriptor_payload(
        workspace_id=input_value.scope_key.workspace_id,
        agent_id=input_value.scope_key.agent_id or "",
        domain_id="domain",
        value=historical_descriptor,
    )
    assert historical.witness_digest != current.witness_digest
    assert p3_character_continuation._character_witness_semantically_equivalent(historical, current)

    compatible_request = replace(
        character_request,
        character_witness_inputs=(replace(
            input_value,
            seed_definition_bytes=seed_bytes,
            descriptor_payload=historical_descriptor,
        ),),
        carrier_directory=character_request.carrier_root.parent / "historical-digest-source-carrier",
        character_continuation_carrier_directory=(
            character_request.carrier_root.parent / "historical-digest-continuation"
        ),
    )
    service = NativeRootP3SourceAdmissionService(connection)
    assert service.admit(compatible_request).b2_memory_count == len(_MULTI_MEMORY_EIDS) + 2
    continuation = json.loads((
        compatible_request.character_continuation_carrier_root
        / "p3_character_seed_witness_domain_derivation_continuation.json"
    ).read_text(encoding="utf-8"))
    assert continuation["payload"]["witnesses"][0]["character_witness"]["witness_digest"] == historical.witness_digest
    # A second admission reloads the immutable continuation through the same
    # semantic-equivalence seam rather than rewriting its historical digest.
    assert service.admit(compatible_request).b2_memory_count == len(_MULTI_MEMORY_EIDS) + 2


def test_p3_character_exact_contrarian_historical_digest_pair_is_semantically_equivalent() -> None:
    """Exercise the known descriptor compatibility pair from frozen P3 evidence."""

    descriptor = {
        "compatibility_status": "CHARACTER_SEED_WITNESS_QUALIFIED",
        "seed_definition": {
            "character_name": "Soren", "core_half_life": 3650.0, "core_weight": 0.5,
            "created_ts": 1787695390, "derived_weight": 0.42,
            "drift_correction_threshold": 0.35, "drift_gravity_strength": 0.12,
            "drift_window_steps": 500, "owner_agent_id": "contrarian",
            "relational_half_life": 30.0, "relational_weight": 0.35,
            "seed_eids": [1, 2], "seed_id": "hivemind_n5_contrarian_fluid_v1",
            "seed_motif_id": "motif_research_0001",
            "seed_text": (
                "Soren is difficult to convince too quickly. He enjoys finding the overlooked "
                "possibility, testing comfortable assumptions, and discovering when an apparently "
                "solid explanation has another side."
            ),
            "situational_half_life": 7.0, "situational_weight": 0.15, "version": "1.0.0",
        },
        "seed_definition_digest": "e124faff0855954266fb47accab69a19a1ded01a1d14a8c2b321dc95acb8008f",
        "seed_id": "hivemind_n5_contrarian_fluid_v1",
        "character_name": "Soren",
        "seed_text": (
            "Soren is difficult to convince too quickly. He enjoys finding the overlooked possibility, "
            "testing comfortable assumptions, and discovering when an apparently solid explanation has another side."
        ),
        "seed_eids": [1, 2],
        "seed_motif_id": "motif_research_0001",
        "seed_motif_member_eids": [
            1, 2, 1, 2, 1, 2, 1, 2, 1, 2,
            3, 3, 3, 3, 3, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6,
            7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9,
            10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 12, 12, 12,
            12, 12, 13,
        ],
        "seed_motif_seed_eids": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
        "concept_summaries": [
            "Soren is difficult to convince too quickly.",
            "He enjoys finding the overlooked possibility, testing comfortable assumptions, and "
            "discovering when an apparently solid explanation has another side.",
        ],
        "witness_digest": "ff18952a3e15213926867e75085f886fa7c762a6ce508b659ab67a6b9cd797e9",
    }
    descriptor_before = json.loads(json.dumps(descriptor, sort_keys=True))
    workspace_id = "hivemind-bounded-context-n5-v1-n5-20260825T220310Z-2af44f6c2e"
    historical = CharacterSeedWitness.from_descriptor_payload(
        workspace_id=workspace_id, agent_id="contrarian", domain_id="research", value=descriptor,
    )
    assert descriptor == descriptor_before

    lifecycle = {
        "state": "protected", "is_authoritative_on_row": True, "requires_join": None,
        "set_by": {"actor": "system", "via": "canon_set", "at": 1}, "history_ref": None,
    }
    nodes = b"".join(_line({
        "eid": eid,
        "payload": {
            "summary": descriptor["concept_summaries"][index], "type": "seed_canon",
            "mtype": "seed_canon", "memory_class": "core", "strength": .95,
            "confidence": .95, "half_life": descriptor["seed_definition"]["core_half_life"],
            "canon": True, "user_id": "contrarian", "created_at": 1,
            "last_reinforced": 1, "seed_id": descriptor["seed_id"],
            "character_name": descriptor["character_name"], "tier": "core_identity",
            "seed_concept_index": index, "lifecycle_status": lifecycle,
        },
    }) for index, eid in enumerate(descriptor["seed_eids"]))
    fresh = read_legacy_character_seed_witness_from_frozen_bytes(
        seed_definition_bytes=json.dumps(descriptor["seed_definition"], separators=(",", ":")).encode("utf-8"),
        private_nodes_bytes=nodes,
        motif_bytes=json.dumps({"motifs": {
            descriptor["seed_motif_id"]: {"members": descriptor["seed_motif_member_eids"]},
        }}, separators=(",", ":")).encode("utf-8"),
        workspace_id=workspace_id,
        agent_id="contrarian",
        domain_id="research",
        requested_seed_id=descriptor["seed_id"],
    )

    assert historical.witness_digest == "ff18952a3e15213926867e75085f886fa7c762a6ce508b659ab67a6b9cd797e9"
    assert fresh.witness_digest == "654ad518eb4296869bf81bb20f94e40d96b3358e8f4d23f03fb6e866b8539a9f"
    assert historical.domain_id == fresh.domain_id == "research"
    assert p3_character_continuation._character_witness_semantically_equivalent(historical, fresh)


@pytest.mark.parametrize("field,replacement", (
    ("workspace_id", "other-workspace"),
    ("agent_id", "other-agent"),
    ("domain_id", "other-domain"),
    ("seed_definition", {"seed_id": "different"}),
    ("seed_definition_compatibility", "LEGACY_MISSING_OWNER_AGENT_ID_V1"),
    ("derived_owner_agent_id", "other-agent"),
    ("lifecycle_compatibility", "LEGACY_PRE_Q2_PROTECTED_CANON_V1"),
    ("seed_definition_digest", "0" * 64),
    ("seed_id", "different-seed"),
    ("character_name", "Other"),
    ("seed_text", "Other text."),
    ("seed_eids", (99, 100)),
    ("seed_motif_id", "different-motif"),
    ("seed_motif_member_eids", (99, 100)),
    ("seed_motif_seed_eids", (99, 100)),
    ("concept_summaries", ("Other",)),
))
def test_p3_character_semantic_equivalence_refuses_every_non_digest_difference(
    field: str, replacement: object,
) -> None:
    seed = CharacterSeed(
        "semantic-equivalence-seed", "P3 Character",
        "A first semantic concept. A second semantic concept.", owner_agent_id="agent",
    )
    seed.seed_eids = [1, 2]
    seed.seed_motif_id = "semantic-equivalence-motif"
    seed.created_ts = 1
    definition = seed.to_dict()
    fresh = CharacterSeedWitness.from_descriptor_payload(
        workspace_id="workspace", agent_id="agent", domain_id="domain",
        value=read_legacy_character_seed_witness_from_frozen_bytes(
            seed_definition_bytes=json.dumps(definition, separators=(",", ":")).encode("utf-8"),
            private_nodes_bytes=b"".join(_line({
                "eid": eid,
                "payload": {
                    "summary": concept, "type": "seed_canon", "mtype": "seed_canon",
                    "memory_class": "core", "strength": .95, "confidence": .95,
                    "half_life": seed.core_half_life, "canon": True, "user_id": "agent",
                    "created_at": 1, "last_reinforced": 1, "seed_id": seed.seed_id,
                    "character_name": seed.character_name, "tier": "core_identity",
                    "seed_concept_index": index,
                    "lifecycle_status": {
                        "state": "protected", "is_authoritative_on_row": True, "requires_join": None,
                        "set_by": {"actor": "system", "via": "canon_set", "at": 1}, "history_ref": None,
                    },
                },
            }) for index, (eid, concept) in enumerate(zip(seed.seed_eids, _split_seed_text(seed.seed_text), strict=True))),
            motif_bytes=json.dumps({"motifs": {seed.seed_motif_id: {"members": seed.seed_eids}}}).encode("utf-8"),
            workspace_id="workspace", agent_id="agent", domain_id="domain", requested_seed_id=seed.seed_id,
        ).descriptor_payload(),
    )
    assert not p3_character_continuation._character_witness_semantically_equivalent(
        fresh, replace(fresh, **{field: replacement}),
    )


def test_p3_character_witness_continuation_routes_seed_rows_without_unknown_fallback(carrier_fixture) -> None:
    connection, request = carrier_fixture
    character_request, _seed_bytes = _character_p3_request(connection, request)
    result = NativeRootP3SourceAdmissionService(connection).admit(character_request)
    record = json.loads(character_request.record_path.read_text(encoding="utf-8"))["payload"]
    entry = next(item for item in record["scopes"] if item["scope_key"].get("agent_id") == "empty-agent")
    assert [(item["eid"], item["normalization_kind"]) for item in entry["b1"]["memories"]] == [
        (101, "CHARACTER_SEED"), (102, "CHARACTER_SEED"),
    ]
    assert result.b1_memory_count == result.b2_memory_count == len(_MULTI_MEMORY_EIDS) + 2
    assert p3_child_request_counts(result.normalization_request.scope_inputs) == {
        "b3a": 4, "ordinary_b3b": 2, "metadata_less_b3b": 0, "total_b3b": 2,
        "b4a": 1, "b4b": 0, "b4c": len(_MULTI_MOTIF_IDS), "b4p": 0,
    }
    dispatched_eids = [
        item.eid for scope_input in result.normalization_request.scope_inputs
        for item in (*scope_input.b3a_requests, *scope_input.b3b_requests)
    ]

    assert len(dispatched_eids) == len(set(dispatched_eids)) == len(_MULTI_MEMORY_EIDS) + 2
    provenance = connection.execute(
        """SELECT a.alias_value,p.origin_kind FROM legacy_object_aliases a
               JOIN objects o ON o.object_id=a.object_id
               JOIN object_revisions r ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
               JOIN provenance_records p ON p.provenance_id=r.provenance_id
             WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' ORDER BY a.alias_value""",
        (native_id_to_bytes(next(item.scope_plan.legacy_source_namespace_id for item in character_request.scope_bindings if item.scope_key.agent_id == "empty-agent")),),
    ).fetchall()
    assert provenance == [("101", "CHARACTER_SEED_PLANT"), ("102", "CHARACTER_SEED_PLANT")]
    continuation = character_request.character_continuation_carrier_root / "p3_character_seed_witness_domain_derivation_continuation.json"
    assert continuation.is_file()
    continuation_witness = json.loads(continuation.read_text(encoding="utf-8"))["payload"]["witnesses"][0]
    assert continuation_witness["character_domain_id"] == "domain"
    assert continuation_witness["character_domain_derivation_law"] == "UNIQUE_BOUNDED_CHARACTER_WITNESS_DOMAIN_V1"
    assert len(continuation_witness["character_domain_candidate_evidence"]) == 2
    assert continuation_witness["character_domain_candidate_evidence_digest"]
    assert next(
        item for item in character_request.scope_bindings
        if item.scope_key == character_request.character_witness_inputs[0].scope_key
    ).scope_plan.motif_domain_id is None
    counts = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "provenance_records", "operations",
    ))
    assert NativeRootP3SourceAdmissionService(connection).admit(character_request).b2_memory_count == len(_MULTI_MEMORY_EIDS) + 2
    assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "provenance_records", "operations",
    )) == counts
    frozen_only_root = character_request.carrier_root.parent / "frozen-p2-opened-root"
    frozen_only_root.mkdir()
    frozen_recovery = replace(
        character_request,
        data_root=frozen_only_root,
        recovered_p2_explicit_source_manifest_digest=character_request.description.explicit_source_manifest.digest,
    )
    assert NativeRootP3SourceAdmissionService(connection).admit(frozen_recovery).b2_memory_count == len(_MULTI_MEMORY_EIDS) + 2
    entry["b1"]["memories"][0]["normalization_kind"] = "ORDINARY"
    p3_source_admission._write_record(character_request.record_path, record)
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CARRIER_CHARACTER_B1_EID_MISMATCH"):
        NativeRootP3SourceAdmissionService(connection).admit(character_request)


def test_p3_character_b1_agreement_uses_readiness_subset_not_full_seed_set() -> None:
    """A witness authorizes seeds; frozen readiness selects Character rows."""

    scope = RootScopeKey("workspace", RootScopeKind.PRIVATE, agent_id="agent")
    entry = {
        "scope_key": scope.identity_payload(),
        "b1": {
            "memories": [
                {
                    "eid": 1,
                    "r1_revision_id": str(UUID(int=1)),
                    "legacy_vector_strategy": "BYTE_DERIVATION_POSSIBLE",
                    "normalization_kind": "ORDINARY",
                },
                {
                    "eid": 2,
                    "r1_revision_id": str(UUID(int=2)),
                    "legacy_vector_strategy": "BYTE_DERIVATION_POSSIBLE",
                    "normalization_kind": "CHARACTER_SEED",
                },
            ],
        },
    }
    witnesses = {scope: SimpleNamespace(witness=SimpleNamespace(seed_eids=(1, 2)))}

    p3_source_admission._validate_character_b1_eid_agreement(
        entry, witnesses, expected_character_eids={2},
    )
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CARRIER_CHARACTER_B1_EID_MISMATCH"):
        p3_source_admission._validate_character_b1_eid_agreement(
            entry, witnesses, expected_character_eids={1, 2},
        )
    entry["b1"]["memories"][1]["eid"] = 3
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CARRIER_CHARACTER_B1_EID_MISMATCH"):
        p3_source_admission._validate_character_b1_eid_agreement(
            entry, witnesses, expected_character_eids={3},
        )


def test_p3_character_witness_accepts_only_the_exact_legacy_missing_owner_raw_shape(carrier_fixture) -> None:
    connection, request = carrier_fixture
    character_request, seed_bytes = _character_p3_request(connection, request)
    input_value = character_request.character_witness_inputs[0]
    raw_seed = json.loads(seed_bytes.decode("utf-8"))
    raw_seed.pop("owner_agent_id")
    legacy_seed_bytes = json.dumps(raw_seed, separators=(",", ":")).encode("utf-8")
    private = request.root / "workspaces" / "ws" / "agents" / "empty-agent" / "private"
    motif = request.root / "workspaces" / "ws" / "domains" / "domain" / "motifs.json"
    witness = read_legacy_character_seed_witness_from_frozen_bytes(
        seed_definition_bytes=legacy_seed_bytes, private_nodes_bytes=(private / "nodes.jsonl").read_bytes(),
        motif_bytes=motif.read_bytes(), workspace_id="ws", agent_id="empty-agent",
        domain_id="domain", requested_seed_id="p3-character-seed-v1",
    )
    assert witness.seed_definition_compatibility == "LEGACY_MISSING_OWNER_AGENT_ID_V1"
    assert witness.derived_owner_agent_id == "empty-agent"
    observation = character_request.character_observation_authority.opened_character_observations[0]
    changed_observation = ExternalOwnerObservation(
        observation.workspace_id, observation.owner_kind, observation.observation_key,
        hashlib.sha256(legacy_seed_bytes).hexdigest(),
    )
    description = replace(
        character_request.description, external_owner_observations=(changed_observation,),
    )
    authority = RootP3ExternalOwnerObservationAuthority(
        character_request.character_observation_authority.envelope_c_digest,
        description.external_owner_observation_digest, (changed_observation,),
    )
    legacy_request = replace(
        character_request, description=description, character_observation_authority=authority,
        character_witness_inputs=(replace(
            input_value, seed_definition_bytes=legacy_seed_bytes,
            descriptor_payload=witness.descriptor_payload(),
        ),),
        carrier_directory=character_request.carrier_root.parent / "legacy-owner-source-carrier",
        character_continuation_carrier_directory=character_request.carrier_root.parent / "legacy-owner-continuation",
    )

    result = NativeRootP3SourceAdmissionService(connection).admit(legacy_request)

    assert result.b1_memory_count == result.b2_memory_count == len(_MULTI_MEMORY_EIDS) + 2


def _replace_character_motif_evidence(
    request: RootP3SourceAdmissionRequest, *, domain_id: str, motifs: dict[str, object], suffix: str,
) -> RootP3SourceAdmissionRequest:
    """Refresh only the test fixture's declared P2 motif source before P3 capture."""

    scope = next(item.scope_key for item in request.scope_bindings if item.scope_key.domain_id == domain_id)
    path = request.root / "workspaces" / "ws" / "domains" / domain_id / "motifs.json"
    path.write_text(json.dumps({"motifs": motifs}), encoding="utf-8")
    evidence = capture_present_source_evidence(
        data_root=request.root, owner_class=SourceOwnerClass.MOTIF_SOURCE,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.DOMAIN, domain_id=domain_id),
        canonical_locator="motifs.json", semantic_role=EvidenceSemanticRole.MOTIFS, scope_key=scope,
    )
    description = replace(
        request.description,
        explicit_source_manifest=RootEvidenceManifest(tuple(
            item for item in request.description.explicit_source_manifest.entries
            if not (item.scope_key == scope and item.semantic_role is EvidenceSemanticRole.MOTIFS)
        ) + (evidence,)),
    )
    return replace(
        request, description=description,
        carrier_directory=request.carrier_root.parent / f"character-{suffix}-carrier",
        character_continuation_carrier_directory=request.carrier_root.parent / f"character-{suffix}-continuation",
        operation_key=f"p3-character-{suffix}",
    )


def test_p3_character_domain_refuses_when_no_candidate_passes_complete_witness(carrier_fixture) -> None:
    connection, request = carrier_fixture
    character_request, _seed_bytes = _character_p3_request(connection, request)
    wrong_members = _replace_character_motif_evidence(
        character_request,
        domain_id="domain",
        motifs={
            "p3-character-motif": {
                "motif_id": "p3-character-motif", "domain_id": "domain", "label": "wrong members",
                "centroid": [1.0] + [0.0] * 383, "strength": .8, "stability_score": .8,
                "contributing_agents": ["empty-agent"], "created_ts": 1, "last_active_ts": 1,
                "members": [55],
            },
        },
        suffix="no-domain",
    )
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CHARACTER_WITNESS_DOMAIN_UNRESOLVED"):
        NativeRootP3SourceAdmissionService(connection).admit(wrong_members)


def test_p3_character_domain_refuses_when_two_frozen_domains_pass_complete_witness(carrier_fixture) -> None:
    connection, request = carrier_fixture
    character_request, _seed_bytes = _character_p3_request(connection, request)
    two_domains = _replace_character_motif_evidence(
        character_request,
        domain_id="empty-domain",
        motifs={
            "p3-character-motif": {
                "motif_id": "p3-character-motif", "domain_id": "empty-domain", "label": "second candidate",
                "centroid": [1.0] + [0.0] * 383, "strength": .8, "stability_score": .8,
                "contributing_agents": ["empty-agent"], "created_ts": 1, "last_active_ts": 1,
                "members": [101, 102],
            },
        },
        suffix="two-domains",
    )
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CHARACTER_WITNESS_DOMAIN_AMBIGUOUS"):
        NativeRootP3SourceAdmissionService(connection).admit(two_domains)
    record = json.loads(two_domains.record_path.read_text(encoding="utf-8"))["payload"]
    assert all(entry["b1"] is None for entry in record["scopes"])


def test_p3_character_domain_rejects_same_seed_eids_under_the_wrong_motif_id(carrier_fixture) -> None:
    connection, request = carrier_fixture
    character_request, _seed_bytes = _character_p3_request(connection, request)
    wrong_motif = _replace_character_motif_evidence(
        character_request,
        domain_id="domain",
        motifs={
            "not-the-character-motif": {
                "motif_id": "not-the-character-motif", "domain_id": "domain", "label": "wrong motif id",
                "centroid": [1.0] + [0.0] * 383, "strength": .8, "stability_score": .8,
                "contributing_agents": ["empty-agent"], "created_ts": 1, "last_active_ts": 1,
                "members": [101, 102],
            },
        },
        suffix="wrong-motif-id",
    )
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CHARACTER_WITNESS_DOMAIN_UNRESOLVED"):
        NativeRootP3SourceAdmissionService(connection).admit(wrong_motif)


def test_p3_character_candidate_intersection_excludes_unmanifested_unfrozen_and_other_workspace_domains(carrier_fixture) -> None:
    connection, request = carrier_fixture
    character_request, _seed_bytes = _character_p3_request(connection, request)
    NativeRootP3SourceAdmissionService(connection).admit(character_request)
    record = json.loads(character_request.record_path.read_text(encoding="utf-8"))["payload"]
    entries_by_scope = {
        p3_source_admission._scope_key_from_payload(entry["scope_key"]): entry
        for entry in record["scopes"]
    }
    domain_scope = RootScopeKey("ws", RootScopeKind.SHARED, domain_id="domain")
    domain_evidence = next(
        item for item in character_request.description.explicit_source_manifest.entries
        if item.scope_key == domain_scope and item.semantic_role is EvidenceSemanticRole.MOTIFS
    )
    without_domain = replace(
        character_request.description,
        explicit_source_manifest=RootEvidenceManifest(tuple(
            item for item in character_request.description.explicit_source_manifest.entries if item != domain_evidence
        )),
    )
    assert "domain" not in {
        item[0].domain_id for item in p3_source_admission._character_domain_candidates(
            request=replace(character_request, description=without_domain),
            entries_by_scope=entries_by_scope, workspace_id="ws",
        )
    }
    unrepresented = replace(
        domain_evidence,
        owner_boundary=EvidenceOwnerBoundary("ws", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="unrepresented"),
        scope_key=RootScopeKey("ws", RootScopeKind.SHARED, domain_id="unrepresented"),
    )
    other_workspace = replace(
        domain_evidence,
        owner_boundary=EvidenceOwnerBoundary("other", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="other-domain"),
        scope_key=RootScopeKey("other", RootScopeKind.SHARED, domain_id="other-domain"),
    )
    # The candidate builder is bounded before root-description topology is
    # consulted: even an otherwise well-formed foreign-workspace P2 entry is
    # ignored for the target workspace rather than becoming search authority.
    extended = SimpleNamespace(description=SimpleNamespace(
        explicit_source_manifest=RootEvidenceManifest(
            character_request.description.explicit_source_manifest.entries + (unrepresented, other_workspace),
        ),
    ))
    candidates = p3_source_admission._character_domain_candidates(
        request=extended,
        entries_by_scope=entries_by_scope, workspace_id="ws",
    )
    assert {item[0].domain_id for item in candidates} == {"domain", "empty-domain"}


def test_p3_character_domain_refuses_changed_frozen_motif_bytes_on_recovery(carrier_fixture) -> None:
    connection, request = carrier_fixture
    character_request, _seed_bytes = _character_p3_request(connection, request)
    NativeRootP3SourceAdmissionService(connection).admit(character_request)
    record = json.loads(character_request.record_path.read_text(encoding="utf-8"))["payload"]
    domain_entry = next(item for item in record["scopes"] if item["scope_key"].get("domain_id") == "domain")
    manifest = load_snapshot_manifest(domain_entry["manifest_path"])
    motif = next(item for item in manifest.artifacts if item.observed_relative_locator.endswith("motifs.json"))
    path = Path(domain_entry["snapshot_root"]) / motif.observed_relative_locator
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CARRIER_SNAPSHOT_RECOVERY_REFUSED"):
        NativeRootP3SourceAdmissionService(connection).admit(character_request)


def test_p3_character_witness_preserves_raw_occurrences_without_rewriting_generic_motif_routing(carrier_fixture) -> None:
    connection, request = carrier_fixture
    raw_members = [101, 55, 101, 102, 55, 102]
    character_request, _seed_bytes = _character_p3_request(
        connection, request, motif_members=raw_members,
    )

    # The Character predicate accepts the raw occurrence sequence.  The
    # The B1F predicate independently finds a zero candidate, so P3 stops at
    # terminal blocking quarantine without rewriting Character witness bytes.
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_B1F_BLOCKING_QUARANTINE"):
        NativeRootP3SourceAdmissionService(connection).admit(character_request)
    record = json.loads(character_request.record_path.read_text(encoding="utf-8"))["payload"]
    private = next(item for item in record["scopes"] if item["scope_key"].get("agent_id") == "empty-agent")
    assert private["b1"] is None
    private_binding = next(item for item in character_request.scope_bindings if item.scope_key == character_request.character_witness_inputs[0].scope_key)
    assert private_binding.scope_plan.motif_domain_id is None


@pytest.mark.parametrize("case,code", (
    ("seed_bytes", "P3_CHARACTER_P2_OBSERVATION_DIGEST_MISMATCH"),
    ("descriptor", "CHARACTER_DESCRIPTOR_WITNESS_DIGEST_MISMATCH"),
    ("observation_key", "P3_CHARACTER_P2_OBSERVATION_MISSING"),
))
def test_p3_character_witness_requires_exact_p2_anchor_before_b1(
    carrier_fixture, case: str, code: str,
) -> None:
    connection, request = carrier_fixture
    character_request, seed_bytes = _character_p3_request(connection, request)
    input_value = character_request.character_witness_inputs[0]
    if case == "seed_bytes":
        character_request = replace(
            character_request,
            character_witness_inputs=(replace(input_value, seed_definition_bytes=b"\n" + seed_bytes),),
            carrier_directory=character_request.carrier_root.parent / "bad-seed-bytes-carrier",
            character_continuation_carrier_directory=character_request.carrier_root.parent / "bad-seed-bytes-continuation",
        )
    elif case == "descriptor":
        descriptor = dict(input_value.descriptor_payload)
        descriptor["witness_digest"] = "0" * 64
        character_request = replace(
            character_request,
            character_witness_inputs=(replace(input_value, descriptor_payload=descriptor),),
            carrier_directory=character_request.carrier_root.parent / "bad-descriptor-carrier",
            character_continuation_carrier_directory=character_request.carrier_root.parent / "bad-descriptor-continuation",
        )
    else:
        observation = character_request.character_observation_authority.opened_character_observations[0]
        changed = ExternalOwnerObservation(
            observation.workspace_id, observation.owner_kind, "seed:not-the-witness-seed", observation.observation_digest,
        )
        description = replace(character_request.description, external_owner_observations=(changed,))
        authority = RootP3ExternalOwnerObservationAuthority(
            character_request.character_observation_authority.envelope_c_digest,
            description.external_owner_observation_digest, (changed,),
        )
        character_request = replace(
            character_request, description=description, character_observation_authority=authority,
            carrier_directory=character_request.carrier_root.parent / "bad-observation-key-carrier",
            character_continuation_carrier_directory=character_request.carrier_root.parent / "bad-observation-key-continuation",
        )
    with pytest.raises(RootP3SourceAdmissionRefused, match=code):
        NativeRootP3SourceAdmissionService(connection).admit(character_request)
    # Candidate-domain evidence is frozen before the existing Character
    # descriptor/P2 checks, but those checks still stop before every B1 write.
    record = json.loads(character_request.record_path.read_text(encoding="utf-8"))["payload"]
    assert all(entry["b1"] is None for entry in record["scopes"])


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
    motif_scope = next(
        item for item in result.normalization_request.scope_inputs if item.scope_key == motif_key
    )
    assert [item.runtime_motif_id for item in motif_scope.b4a_requests] == ["cross-scope-carrier-motif"]
    assert not motif_scope.b4b_requests
    assert not motif_scope.b4c_requests
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
    normalized = NativeRootWideNormalizationService(connection).normalize(result.normalization_request)
    assert normalized.root_normalization_complete


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
    assert empty["b1"] is None
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
    assert empty["b1"] == {"memories": [], "motifs": [], "motif_dispositions": []}
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
        "total_b3b": 0, "b4a": 0, "b4b": 0, "b4c": 3, "b4p": 0,
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
        "total_b3b": 2, "b4a": 0, "b4b": 0, "b4c": 3, "b4p": 0,
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


def _completion_payload(request: RootP3SourceAdmissionRequest) -> dict[str, object]:
    return json.loads(request.record_path.read_text(encoding="utf-8"))["payload"]


def _persisted_b1_predecessor(
    connection, request: RootP3SourceAdmissionRequest,
) -> RootP3SourceAdmissionRequest:
    predecessor = replace(
        request,
        carrier_directory=request.carrier_root.parent / "completion-reload-predecessor",
        operation_key="p3-completion-reload-predecessor",
    )
    NativeRootP3SourceAdmissionService(connection).admit(predecessor)
    assert all(entry["b1"] is not None for entry in _completion_payload(predecessor)["scopes"])
    return predecessor


def _pending_completion_successor(
    connection, request: RootP3SourceAdmissionRequest, predecessor: RootP3SourceAdmissionRequest,
) -> RootP3SourceAdmissionRequest:
    successor = replace(
        request,
        carrier_directory=request.carrier_root.parent / "completion-reload-successor",
        predecessor_carrier_record_path=predecessor.record_path,
        operation_key="p3-completion-reload-successor",
    )
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        NativeRootP3SourceAdmissionService(connection).admit(
            successor,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    return successor


def _align_pending_successor_b1_evidence(
    connection, successor: RootP3SourceAdmissionRequest,
) -> None:
    """Stage the fixture's inherited records at the current frozen B1 evidence.

    The small fixture's predecessor and successor use distinct admission
    passes, so its persisted revision IDs need this explicit stable replay
    before the test can exercise the *carrier* revalidation transition.
    """

    record = _completion_payload(successor)
    ordered = p3_source_admission._ordered_scope_entries(record)
    for entry in ordered:
        p3_source_admission._run_b1m(connection, successor, entry)
    b1m = p3_source_admission._seal_b1m_identity_universe(connection, successor, record)
    p3_source_admission._run_b1f(connection, successor, record, b1m["identity_universe_digest"])
    for entry in ordered:
        p3_source_admission._run_b1_nonmotif_evidence(connection, successor, entry)
        entry["b1"]["memories"] = p3_source_admission._read_b1_memory_evidence(
            connection, successor, entry, {},
        )
    p3_source_admission._write_record(successor.record_path, record)


def test_completion_carrier_cold_reload_preserves_pending_and_qualified_reuse_states(
    carrier_fixture, monkeypatch,
) -> None:
    """A successor survives reload before and after inherited-B1 qualification."""

    connection, request = carrier_fixture
    predecessor = _persisted_b1_predecessor(connection, request)
    successor = _pending_completion_successor(connection, request, predecessor)
    pending = _completion_payload(successor)["carrier_completion"]
    assert set(pending) == {
        "predecessor_record_path", "predecessor_record_digest", "completed_snapshots",
        "completed_manifests", "inherited_snapshots",
        "previous_b1_scope_reuse_candidate_count", "predecessor_b1_revalidation_pending",
    }
    assert pending["previous_b1_scope_reuse_candidate_count"] == 3
    assert pending["predecessor_b1_revalidation_pending"] is True

    # The first cold reload must accept the pending shape before any B1 write.
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        NativeRootP3SourceAdmissionService(connection).admit(
            successor,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    assert _completion_payload(successor)["carrier_completion"] == pending

    _align_pending_successor_b1_evidence(connection, successor)

    def _stop_after_b1_revalidation(*_args, **_kwargs):
        raise RootP3SourceAdmissionRefused("TEST_STOP_AFTER_B1_REVALIDATION")

    monkeypatch.setattr(p3_source_admission, "_b2_normalization_request", _stop_after_b1_revalidation)
    with pytest.raises(RootP3SourceAdmissionRefused, match="TEST_STOP_AFTER_B1_REVALIDATION"):
        NativeRootP3SourceAdmissionService(connection).admit(successor)
    qualified = _completion_payload(successor)["carrier_completion"]
    assert set(qualified) == set(pending) | {"previous_b1_scope_reuse"}
    assert qualified["previous_b1_scope_reuse_candidate_count"] == 3
    assert qualified["predecessor_b1_revalidation_pending"] is False
    assert qualified["previous_b1_scope_reuse"] == "QUALIFIED"

    # A second cold reload must accept the persisted qualified state before
    # B1M; the interruption is the test boundary, not a reload failure.
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        NativeRootP3SourceAdmissionService(connection).admit(
            successor,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    assert _completion_payload(successor)["carrier_completion"] == qualified


def test_legacy_completion_derives_pending_revalidation_and_refuses_bad_inherited_b1(carrier_fixture) -> None:
    """Five-field legacy metadata stays readable but cannot bypass B1 revalidation."""

    connection, request = carrier_fixture
    predecessor = _persisted_b1_predecessor(connection, request)
    successor = _pending_completion_successor(connection, request, predecessor)
    legacy = _completion_payload(successor)
    completion = legacy["carrier_completion"]
    completion.pop("previous_b1_scope_reuse_candidate_count")
    completion.pop("predecessor_b1_revalidation_pending")
    p3_source_admission._write_record(successor.record_path, legacy)

    loaded = p3_source_admission._load_record(successor.record_path, successor)
    derived = loaded["carrier_completion"]
    assert derived["previous_b1_scope_reuse_candidate_count"] == 3
    assert derived["predecessor_b1_revalidation_pending"] is True
    assert set(_completion_payload(successor)["carrier_completion"]) == {
        "predecessor_record_path", "predecessor_record_digest", "completed_snapshots",
        "completed_manifests", "inherited_snapshots",
    }

    _align_pending_successor_b1_evidence(connection, successor)
    # A tampered inherited B1 record must reach and fail strict revalidation,
    # rather than being silently reused by the legacy completion shape.
    tampered = _completion_payload(successor)
    scope = next(item for item in tampered["scopes"] if item["scope_key"].get("domain_id") == "domain")
    scope["b1"]["memories"][0]["r1_revision_id"] = str(UUID(int=0))
    p3_source_admission._write_record(successor.record_path, tampered)
    with pytest.raises(
        RootP3SourceAdmissionRefused,
        match="P3_CARRIER_PREVIOUS_B1_MEMORY_REVALIDATION_FAILED",
    ):
        NativeRootP3SourceAdmissionService(connection).admit(successor)


def test_completion_carrier_no_reuse_candidate_cold_reloads_as_nonpending(carrier_fixture) -> None:
    connection, request = carrier_fixture
    predecessor = replace(
        request,
        carrier_directory=request.carrier_root.parent / "completion-no-reuse-predecessor",
        operation_key="p3-completion-no-reuse-predecessor",
    )
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        NativeRootP3SourceAdmissionService(connection).admit(
            predecessor,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    successor = replace(
        request,
        carrier_directory=request.carrier_root.parent / "completion-no-reuse-successor",
        predecessor_carrier_record_path=predecessor.record_path,
        operation_key="p3-completion-no-reuse-successor",
    )
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        NativeRootP3SourceAdmissionService(connection).admit(
            successor,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )
    completion = _completion_payload(successor)["carrier_completion"]
    assert completion["previous_b1_scope_reuse_candidate_count"] == 0
    assert completion["predecessor_b1_revalidation_pending"] is False
    assert "previous_b1_scope_reuse" not in completion
    with pytest.raises(RootP3SourceAdmissionInterrupted):
        NativeRootP3SourceAdmissionService(connection).admit(
            successor,
            _test_interrupt_after=RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION,
        )


@pytest.mark.parametrize("change", (
    lambda completion: completion.update({"unrecognized": "value"}),
    lambda completion: completion.pop("inherited_snapshots"),
    lambda completion: completion.update({"previous_b1_scope_reuse_candidate_count": -1}),
    lambda completion: completion.update({"previous_b1_scope_reuse_candidate_count": True}),
    lambda completion: completion.update({"predecessor_b1_revalidation_pending": "true"}),
    lambda completion: completion.update({"predecessor_b1_revalidation_pending": False}),
    lambda completion: completion.update({"previous_b1_scope_reuse_candidate_count": 0}),
    lambda completion: completion.update({"previous_b1_scope_reuse": "UNQUALIFIED"}),
    lambda completion: completion.update({
        "previous_b1_scope_reuse": "QUALIFIED",
        "predecessor_b1_revalidation_pending": True,
    }),
    lambda completion: completion.update({
        "previous_b1_scope_reuse_candidate_count": 0,
        "predecessor_b1_revalidation_pending": False,
        "previous_b1_scope_reuse": "QUALIFIED",
    }),
))
def test_completion_carrier_rejects_invalid_reuse_metadata(carrier_fixture, change) -> None:
    connection, request = carrier_fixture
    predecessor = _persisted_b1_predecessor(connection, request)
    successor = _pending_completion_successor(connection, request, predecessor)
    invalid = _completion_payload(successor)
    change(invalid["carrier_completion"])
    p3_source_admission._write_record(successor.record_path, invalid)
    with pytest.raises(RootP3SourceAdmissionRefused, match="P3_CARRIER_COMPLETION_SHAPE_INVALID"):
        p3_source_admission._load_record(successor.record_path, successor)


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
            "contributing_agents": [], "created_ts": 1, "last_active_ts": 2,
            "members": list(sorted(_MULTI_MEMORY_EIDS)),
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
    assert not scope.b4c_requests
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
