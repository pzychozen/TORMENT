"""Offline Phase 9C-R4 root-wide normalization composition qualification."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import numpy as np
import pytest

from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    DeclaredUnmaterializedDomain,
    EvidenceAbsenceReason,
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    ExpectedRootCensus,
    IdentityOnlyAgentObservation,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    MetadataLessB3BDispatch,
    MigrationRehearsalConfig,
    MigrationRuntimeMotifProjectionRequest,
    MigrationRuntimeMotifRegeometryProjectionRequest,
    MigrationRuntimeNormalizationRequest,
    MigrationRuntimeReembeddingBootstrapRequest,
    MigrationRuntimeRepresentationBootstrapRequest,
    MigrationRuntimeScopePlan,
    MigrationRuntimeZeroMemberMotifProjectionRequest,
    NativeLegacyMigrationRehearsal,
    NativeMigrationRuntimeNormalizationService,
    NativeRootWideNormalizationService,
    RepresentationDispositionCount,
    RootChildCompletionState,
    RootEvidenceManifest,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootNormalizationInterrupted,
    RootNormalizationInterruptionPoint,
    RootNormalizationRefused,
    RootNormalizationRequest,
    RootNormalizationScopeInput,
    RootRepresentationBootstrapKind,
    RootRepresentationDisposition,
    RootScopeKey,
    RootScopeKind,
    SourceOwnerClass,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
    capture_present_source_evidence,
    create_snapshot_manifest,
    qualify_metadata_less_per_eid_legacy_source,
)
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
)
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.migration.root_normalization import _validate_scope_dispatch
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from torment_service.substrate.schema import create_schema
from torment_service.substrate.root_blocker5_binding import (
    RootBlocker5BindingRefused,
    discover_canonical_root_layout,
    require_discovered_declared_census_parity,
)


def _id() -> UUID:
    return generate_native_id()


def _line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "st", "BAAI/bge-small-en-v1.5", 384,
        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


def _payload(label: str) -> dict[str, object]:
    return {
        "summary": f"root-normalization memory {label}",
        "type": "memory", "memory_class": "core", "strength": 0.7, "confidence": 0.9,
        "seed_pos0": [1, 2, 3], "seed_v0": [0.1, 0.2, 0.3],
        "governance": {
            "protected": False, "non_shareable": False, "collective_export_blocked": False,
            "collective_reingest_blocked": False, "decay_accelerated": False,
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


class _DeterministicEmbedder:
    provider = "st"
    model = "BAAI/bge-small-en-v1.5"
    dim = 384

    def __init__(self) -> None:
        self.calls: list[str] = []

    def embed(self, text: str) -> np.ndarray:
        self.calls.append(text)
        value = float(len(self.calls))
        return np.asarray([value] + [0.0] * 383, dtype=np.float32)


class _InertSideStore:
    def load_anchor_state(self, **_kwargs): return {}
    def load_affect_state(self, **_kwargs): return {}
    def save_anchor_state(self, **_kwargs): raise AssertionError("readiness must not write")
    def save_affect_state(self, **_kwargs): raise AssertionError("readiness must not write")


def _post_write_configuration(plan: MigrationRuntimeScopePlan) -> NativePostWriteQualificationConfiguration:
    runtime = NativeMemoryRuntimeScope(
        workspace_id=plan.workspace_id, scope_kind=plan.scope_kind,
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id,
        agent_id=plan.agent_id, domain_id=plan.domain_id,
    )
    routing = NativeFabricRoutingScope(
        runtime_scope=runtime, motif_alias_namespace_id=plan.motif_alias_namespace_id,
        motif_identity_namespace_id=plan.motif_identity_namespace_id,
        membership_identity_namespace_id=plan.membership_identity_namespace_id,
        idempotency_namespace_id=plan.idempotency_namespace_id,
    )
    template = NativeDerivedMemoryRuntimeConfiguration(
        workspace_id=plan.workspace_id, agent_id=plan.agent_id or "agent",
        domain_id=plan.motif_domain_id or plan.domain_id or "domain",
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        motif_alias_namespace_id=plan.motif_alias_namespace_id,
        memory_identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id,
        idempotency_namespace_id=plan.idempotency_namespace_id,
        parent_native_operation_key="R4-READINESS-NEVER-EXECUTED",
        expected_dimension=384,
        embed=lambda _value: (_ for _ in ()).throw(AssertionError("readiness must not embed")),
        embedder_provider="st", embedder_model="BAAI/bge-small-en-v1.5", side_store=_InertSideStore(),
    )
    return NativePostWriteQualificationConfiguration(
        routing_scope=routing,
        profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=SimpleNamespace(), workspace=SimpleNamespace(), identity=SimpleNamespace(),
            agent_key=plan.agent_id or "agent",
            detect_canon_conflict=lambda *_args: (_ for _ in ()).throw(AssertionError("must not post-write")),
            proposal_allowed=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not post-write")),
            hivemind_log=SimpleNamespace(info=lambda *_args, **_kwargs: None),
        ),
        derived_runtime_template=template,
        motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False,
        checkpoint_snapshots_required=False,
        bridge_suggestions_required=False,
        deep_memory_required=False,
    )


@dataclass(frozen=True)
class _ScopeFacts:
    scope_key: RootScopeKey
    plan: MigrationRuntimeScopePlan
    snapshot_root: Path
    manifest_path: Path
    snapshot_id: UUID
    r1: UUID | None
    r2: UUID | None
    motif_object_id: UUID | None
    motif_r1: UUID | None
    motif_id: str | None


def _stage_scope(
    connection,
    tmp_path: Path,
    core_id: UUID,
    *,
    workspace_id: str,
    scope_key: RootScopeKey,
    source_label: str,
    vector_provider: str,
    vector_model: str,
    has_memory: bool = True,
    include_vector: bool = True,
    motif_id: str | None = None,
    motif_members: list[int] | None = None,
) -> _ScopeFacts:
    object_ns, relationship_ns, motif_ns, alias_ns = (_id() for _ in range(4))
    unknown_scope, target_scope, idempotency, source_ns = (_id() for _ in range(4))
    for value, key in ((object_ns, "object"), (relationship_ns, "relationship"), (motif_ns, "motif")):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), f"{source_label}-{key}"),
        )
    for value, key in ((unknown_scope, "unknown"), (target_scope, "target")):
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(value), f"{source_label}-{key}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency), f"{source_label}-idem"),
    )
    connection.execute(
        "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(alias_ns), f"{source_label}-aliases"),
    )
    qualifier = scope_key.agent_id if scope_key.scope_kind is RootScopeKind.PRIVATE else scope_key.domain_id
    root = tmp_path / "snapshots" / workspace_id / f"{scope_key.scope_kind.value.lower()}-{qualifier}"
    root.mkdir(parents=True)
    if has_memory:
        node: dict[str, object] = {"eid": 7, "born_step": 1, "channel": 1, "payload": _payload(source_label)}
        if include_vector:
            node["embedding_ref"] = {
                "map": "embeddings/shard.map.jsonl", "shard": "embeddings/vectors.npy", "row": 0,
                "dimension": 384, "dtype": "float32",
            }
            embeddings = root / "embeddings"
            embeddings.mkdir()
            np.save(embeddings / "vectors.npy", np.asarray([[1.0] + [0.0] * 383], dtype=np.float32))
            (embeddings / "manifest.json").write_bytes(_line({
                "encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 384,
                "derivation_contract_version": "synthetic-capture-v1", "provider": vector_provider,
                "model": vector_model,
                "shards": [{"path": "embeddings/vectors.npy", "map": "embeddings/shard.map.jsonl"}],
            }))
            (embeddings / "shard.map.jsonl").write_bytes(_line({
                "eid": 7, "shard": "embeddings/vectors.npy", "row": 0, "dimension": 384,
            }))
        (root / "nodes.jsonl").write_bytes(_line(node))
    if motif_id is not None:
        workspace = root / "workspaces" / workspace_id
        workspace.mkdir(parents=True)
        (workspace / "workspace_meta.json").write_text(json.dumps({
            "embed_provider": vector_provider, "embed_model": vector_model, "embed_dim": 384,
        }), encoding="utf-8")
        domain = workspace / "domains" / (scope_key.domain_id or "missing")
        domain.mkdir(parents=True)
        (domain / "motifs.json").write_text(json.dumps({"motifs": {motif_id: {
            "motif_id": motif_id, "domain_id": scope_key.domain_id, "label": source_label,
            "centroid": [1.0] + [0.0] * 383, "strength": 0.8, "stability_score": 0.8,
            "contributing_agents": ["agent-0"], "created_ts": 1, "last_active_ts": 2,
            "members": motif_members if motif_members is not None else [7],
        }}}), encoding="utf-8")
    manifest_path = root.parent / f"{root.name}-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root, manifest_path=manifest_path,
        legacy_source_namespace_id=source_ns, legacy_source_namespace_key=f"{source_label}-source",
        capture_label="root normalization synthetic fixture",
    )
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=root, manifest_path=manifest_path,
        config=MigrationRehearsalConfig(
            native_core_id=core_id, idempotency_namespace_id=idempotency,
            object_identity_namespace_id=object_ns, relationship_identity_namespace_id=relationship_ns,
            unknown_semantic_scope_id=unknown_scope,
        ),
    )
    plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=source_ns, workspace_id=workspace_id,
        scope_kind="PRIVATE_AGENT" if scope_key.scope_kind is RootScopeKind.PRIVATE else "SHARED_DOMAIN",
        agent_id=scope_key.agent_id, domain_id=scope_key.domain_id,
        target_identity_namespace_id=object_ns, target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=alias_ns, motif_identity_namespace_id=motif_ns,
        membership_identity_namespace_id=relationship_ns, idempotency_namespace_id=idempotency,
        motif_domain_id=scope_key.domain_id,
    )
    r1 = r2 = None
    if has_memory:
        object_id, source_r1 = connection.execute(
            """SELECT object_id,current_revision_id FROM objects WHERE object_id=(
                 SELECT object_id FROM legacy_object_aliases
                  WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value='7'
            )""", (native_id_to_bytes(source_ns),),
        ).fetchone()
        del object_id
        r1 = UUID(bytes=source_r1)
        r2 = NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(
            MigrationRuntimeNormalizationRequest(
                root, manifest_path, manifest.legacy_snapshot_id, source_ns, core_id, 7, r1,
                (plan,), idempotency, f"{source_label}-b2",
            )
        ).revision_id
    motif_object = motif_r1 = None
    if motif_id is not None:
        source_motif, source_motif_r1 = connection.execute(
            """SELECT object_id,current_revision_id FROM objects WHERE object_id=(
                 SELECT object_id FROM legacy_object_aliases
                  WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?
            )""", (native_id_to_bytes(source_ns), motif_id),
        ).fetchone()
        motif_object, motif_r1 = UUID(bytes=source_motif), UUID(bytes=source_motif_r1)
    return _ScopeFacts(scope_key, plan, root, manifest_path, manifest.legacy_snapshot_id, r1, r2, motif_object, motif_r1, motif_id)


def _present(
    root: Path, owner_class: SourceOwnerClass, owner: EvidenceOwnerBoundary,
    locator: str, role: EvidenceSemanticRole, scope: RootScopeKey | None,
) -> ExplicitSourceEvidence:
    return capture_present_source_evidence(
        data_root=root, owner_class=owner_class, owner_boundary=owner,
        canonical_locator=locator, semantic_role=role, scope_key=scope,
    )


def _write_root_scope_evidence(
    root: Path, scope: RootScopeKey, *, has_memory: bool, has_motif: bool,
    metadata_less: bool = False, payload_label: str | None = None,
) -> list[ExplicitSourceEvidence]:
    if scope.scope_kind is RootScopeKind.PRIVATE:
        owner = EvidenceOwnerBoundary(scope.workspace_id, EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id=scope.agent_id)
        prefix = f"workspaces/{scope.workspace_id}/agents/{scope.agent_id}/private"
        owner_class = SourceOwnerClass.PRIVATE_GRAPH_SOURCE
    else:
        owner = EvidenceOwnerBoundary(scope.workspace_id, EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id=scope.domain_id)
        prefix = f"workspaces/{scope.workspace_id}/domains/{scope.domain_id}/shared"
        owner_class = SourceOwnerClass.SHARED_GRAPH_SOURCE
    entries: list[ExplicitSourceEvidence] = []
    if has_memory:
        path = root / prefix / "nodes.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_line({"eid": 7, "payload": _payload(payload_label or f"manifest-{scope.qualifier}")}))
        entries.append(_present(root, owner_class, owner, "nodes.jsonl", EvidenceSemanticRole.NODES, scope))
    else:
        entries.append(ExplicitSourceEvidence(
            owner_class, owner, "nodes.jsonl", EvidenceSemanticRole.NODES,
            EvidencePresenceExpectation.EXPECTED_ABSENT, scope,
            absence_reason=EvidenceAbsenceReason.EMPTY_GRAPH,
        ))
    if has_motif:
        motif_owner = EvidenceOwnerBoundary(scope.workspace_id, EvidenceOwnerBoundaryKind.DOMAIN, domain_id=scope.domain_id)
        motif_path = root / f"workspaces/{scope.workspace_id}/domains/{scope.domain_id}/motifs.json"
        motif_path.parent.mkdir(parents=True, exist_ok=True)
        motif_path.write_text("{}", encoding="utf-8")
        entries.append(_present(root, SourceOwnerClass.MOTIF_SOURCE, motif_owner, "motifs.json", EvidenceSemanticRole.MOTIFS, scope))
    if metadata_less:
        vector = root / prefix / "emb_7.npy"
        np.save(vector, np.asarray([3.0] + [0.0] * 383, dtype=np.float32))
        entries.append(_present(
            root, SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION, owner,
            "emb_7.npy", EvidenceSemanticRole.LEGACY_REPRESENTATION, scope,
        ))
    return entries


def _b3a(facts: _ScopeFacts, core_id: UUID, key: str) -> MigrationRuntimeRepresentationBootstrapRequest:
    assert facts.r1 is not None and facts.r2 is not None
    return MigrationRuntimeRepresentationBootstrapRequest(
        facts.snapshot_root, facts.manifest_path, facts.snapshot_id, facts.plan.legacy_source_namespace_id,
        core_id, 7, facts.r1, facts.r2, _lane(), facts.plan.idempotency_namespace_id, key,
    )


def _b3b(facts: _ScopeFacts, core_id: UUID, key: str) -> MigrationRuntimeReembeddingBootstrapRequest:
    assert facts.r1 is not None and facts.r2 is not None
    return MigrationRuntimeReembeddingBootstrapRequest(
        facts.snapshot_root, facts.manifest_path, facts.snapshot_id, facts.plan.legacy_source_namespace_id,
        core_id, 7, facts.r1, facts.r2, (facts.plan,), _lane(), facts.plan.idempotency_namespace_id, key,
    )


def _b4a(facts: _ScopeFacts, core_id: UUID, key: str) -> MigrationRuntimeMotifProjectionRequest:
    assert facts.motif_id and facts.motif_object_id and facts.motif_r1
    return MigrationRuntimeMotifProjectionRequest(
        facts.snapshot_root, facts.manifest_path, facts.snapshot_id, facts.plan.legacy_source_namespace_id,
        core_id, facts.motif_id, facts.motif_object_id, facts.motif_r1, (facts.plan,), _lane(),
        facts.plan.idempotency_namespace_id, key,
    )


def _b4b(facts: _ScopeFacts, core_id: UUID, key: str) -> MigrationRuntimeMotifRegeometryProjectionRequest:
    assert facts.motif_id and facts.motif_object_id and facts.motif_r1
    return MigrationRuntimeMotifRegeometryProjectionRequest(
        facts.snapshot_root, facts.manifest_path, facts.snapshot_id, facts.plan.legacy_source_namespace_id,
        core_id, facts.motif_id, facts.motif_object_id, facts.motif_r1, (facts.plan,), _lane(),
        facts.plan.idempotency_namespace_id, key,
    )


def _b4c(facts: _ScopeFacts, core_id: UUID, key: str) -> MigrationRuntimeZeroMemberMotifProjectionRequest:
    assert facts.motif_id and facts.motif_object_id and facts.motif_r1
    return MigrationRuntimeZeroMemberMotifProjectionRequest(
        facts.snapshot_root, facts.manifest_path, facts.snapshot_id, facts.plan.legacy_source_namespace_id,
        core_id, facts.motif_id, facts.motif_object_id, facts.motif_r1, (facts.plan,), _lane(),
        facts.plan.idempotency_namespace_id, key,
    )


def _description(root: Path, entries: list[ExplicitSourceEvidence], plans: tuple[WorkspaceRootAdmissionPlan, ...]) -> RootNativeProductionAdmissionDescription:
    materialized_scopes = [scope for workspace in plans for scope in workspace.materialized_scopes]
    scopes = [scope for workspace in plans for scope in workspace.runtime_scopes]
    counts = {
        disposition: sum(scope.representation_disposition is disposition for scope in scopes)
        for disposition in RootRepresentationDisposition
    }
    private_counts = [len(workspace.private_materialized_scopes) for workspace in plans]
    shared_counts = [len(workspace.shared_materialized_scopes) for workspace in plans]
    return RootNativeProductionAdmissionDescription(
        data_root_identity="synthetic-root-normalization", operator_identity="pytest-operator",
        workspace_plans=plans, target_representation_lane=_lane(),
        expected_census=ExpectedRootCensus(
            workspace_count=len(plans),
            materialized_private_scope_count=sum(
                scope.scope_key.scope_kind is RootScopeKind.PRIVATE for scope in materialized_scopes
            ),
            materialized_shared_scope_count=sum(
                scope.scope_key.scope_kind is RootScopeKind.SHARED for scope in materialized_scopes
            ),
            total_materialized_scope_count=len(materialized_scopes),
            representation_disposition_counts=tuple(
                RepresentationDispositionCount(disposition, counts[disposition])
                for disposition in RootRepresentationDisposition
            ),
            workspace_topology_counts=WorkspaceTopologyCounts(
                private_counts.count(0), private_counts.count(1), sum(item > 1 for item in private_counts),
                shared_counts.count(0), shared_counts.count(1), sum(item > 1 for item in shared_counts),
            ),
            declared_empty_shared_scope_count=sum(
                scope.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
                for scope in scopes
            ),
            empty_private_identity_scope_count=sum(
                scope.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE
                for scope in scopes
            ),
        ),
        explicit_source_manifest=RootEvidenceManifest(tuple(entries)), external_owner_observations=(),
        feature_posture=RootFeaturePosture("compression-deep-disabled", False, False),
    )


@dataclass
class _Fixture:
    qualified: object
    request: RootNormalizationRequest
    embedder: _DeterministicEmbedder
    data_root: Path
    metadata_vector: Path

    def close(self) -> None:
        self.qualified.close()


def _positive_fixture(tmp_path: Path) -> _Fixture:
    qualified = open_temporary_test_connection(tmp_path / "root-normalization.db")
    connection = qualified.connection
    metadata = create_schema(connection)
    core_id = UUID(bytes=metadata.core_id)
    root = tmp_path / "root-evidence"
    entries: list[ExplicitSourceEvidence] = []
    facts: dict[str, _ScopeFacts] = {}
    inputs: list[RootNormalizationScopeInput] = []
    private_plans: dict[str, list[MaterializedRootScopePlan]] = {"ws-a": [], "ws-b": [], "ws-c": [], "ws-d": []}
    shared_plans: dict[str, list[MaterializedRootScopePlan]] = {"ws-a": [], "ws-b": [], "ws-c": [], "ws-e": [], "ws-f": []}

    for index in range(5):
        key = RootScopeKey("ws-a", RootScopeKind.PRIVATE, agent_id=f"agent-{index}")
        fact = _stage_scope(connection, tmp_path, core_id, workspace_id="ws-a", scope_key=key,
                            source_label=f"ws-a-agent-{index}", vector_provider="st", vector_model="BAAI/bge-small-en-v1.5")
        facts[f"a-{index}"] = fact
        entries.extend(_write_root_scope_evidence(root, key, has_memory=True, has_motif=False))
        private_plans["ws-a"].append(MaterializedRootScopePlan(key, RootRepresentationDisposition.TARGET_COMPATIBLE))
        inputs.append(RootNormalizationScopeInput(key, fact.plan, fact.snapshot_id, b3a_requests=(_b3a(fact, core_id, f"a-{index}-b3a"),)))

    shared_a = RootScopeKey("ws-a", RootScopeKind.SHARED, domain_id="target-domain")
    fact_a = _stage_scope(connection, tmp_path, core_id, workspace_id="ws-a", scope_key=shared_a,
                           source_label="ws-a-target-domain", vector_provider="st", vector_model="BAAI/bge-small-en-v1.5",
                           motif_id="target-motif", motif_members=[7])
    entries.extend(_write_root_scope_evidence(root, shared_a, has_memory=True, has_motif=True))
    shared_plans["ws-a"].append(MaterializedRootScopePlan(shared_a, RootRepresentationDisposition.TARGET_COMPATIBLE))
    inputs.append(RootNormalizationScopeInput(shared_a, fact_a.plan, fact_a.snapshot_id,
        b3a_requests=(_b3a(fact_a, core_id, "shared-a-b3a"),), b4a_requests=(_b4a(fact_a, core_id, "shared-a-b4a"),)))

    shared_b = RootScopeKey("ws-a", RootScopeKind.SHARED, domain_id="regeometry-domain")
    fact_b = _stage_scope(connection, tmp_path, core_id, workspace_id="ws-a", scope_key=shared_b,
                           source_label="ws-a-regeometry-domain", vector_provider="hash", vector_model="legacy-hash",
                           motif_id="regeometry-motif", motif_members=[7])
    entries.extend(_write_root_scope_evidence(root, shared_b, has_memory=True, has_motif=True))
    shared_plans["ws-a"].append(MaterializedRootScopePlan(shared_b, RootRepresentationDisposition.REEMBED_REQUIRED))
    inputs.append(RootNormalizationScopeInput(shared_b, fact_b.plan, fact_b.snapshot_id,
        b3b_requests=(_b3b(fact_b, core_id, "shared-b-b3b"),), b4b_requests=(_b4b(fact_b, core_id, "shared-b-b4b"),)))

    private_b = RootScopeKey("ws-b", RootScopeKind.PRIVATE, agent_id="agent-0")
    fact_private_b = _stage_scope(connection, tmp_path, core_id, workspace_id="ws-b", scope_key=private_b,
                                   source_label="ws-b-agent", vector_provider="hash", vector_model="legacy-hash")
    entries.extend(_write_root_scope_evidence(root, private_b, has_memory=True, has_motif=False))
    private_plans["ws-b"].append(MaterializedRootScopePlan(private_b, RootRepresentationDisposition.REEMBED_REQUIRED))
    inputs.append(RootNormalizationScopeInput(private_b, fact_private_b.plan, fact_private_b.snapshot_id,
        b3b_requests=(_b3b(fact_private_b, core_id, "private-b-b3b"),)))

    empty_shared = RootScopeKey("ws-b", RootScopeKind.SHARED, domain_id="empty-domain")
    fact_empty = _stage_scope(connection, tmp_path, core_id, workspace_id="ws-b", scope_key=empty_shared,
                               source_label="ws-b-empty-domain", vector_provider="st", vector_model="BAAI/bge-small-en-v1.5",
                               has_memory=False, include_vector=False, motif_id="empty-motif", motif_members=[])
    entries.extend(_write_root_scope_evidence(root, empty_shared, has_memory=False, has_motif=True))
    (root / "workspaces/ws-b/domains/empty-domain/shared").mkdir(parents=True, exist_ok=True)
    shared_plans["ws-b"].append(MaterializedRootScopePlan(
        empty_shared, RootRepresentationDisposition.TARGET_COMPATIBLE, MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
    ))
    inputs.append(RootNormalizationScopeInput(empty_shared, fact_empty.plan, fact_empty.snapshot_id,
        b4c_requests=(_b4c(fact_empty, core_id, "empty-b4c"),)))

    empty_shared_without_motif = RootScopeKey(
        "ws-b", RootScopeKind.SHARED, domain_id="empty-without-motif",
    )
    fact_empty_without_motif = _stage_scope(
        connection, tmp_path, core_id, workspace_id="ws-b", scope_key=empty_shared_without_motif,
        source_label="ws-b-empty-without-motif", vector_provider="st",
        vector_model="BAAI/bge-small-en-v1.5", has_memory=False, include_vector=False,
    )
    entries.extend(_write_root_scope_evidence(
        root, empty_shared_without_motif, has_memory=False, has_motif=False,
    ))
    entries.append(ExplicitSourceEvidence(
        SourceOwnerClass.MOTIF_SOURCE,
        EvidenceOwnerBoundary("ws-b", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="empty-without-motif"),
        "motifs.json", EvidenceSemanticRole.MOTIFS, EvidencePresenceExpectation.EXPECTED_ABSENT,
        empty_shared_without_motif, absence_reason=EvidenceAbsenceReason.EMPTY_GRAPH,
    ))
    (root / "workspaces/ws-b/domains/empty-without-motif/shared").mkdir(parents=True, exist_ok=True)
    shared_plans["ws-b"].append(MaterializedRootScopePlan(
        empty_shared_without_motif, RootRepresentationDisposition.NO_VECTOR,
        MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF,
    ))
    inputs.append(RootNormalizationScopeInput(
        empty_shared_without_motif, fact_empty_without_motif.plan,
        fact_empty_without_motif.snapshot_id,
    ))

    private_c = RootScopeKey("ws-c", RootScopeKind.PRIVATE, agent_id="agent-0")
    fact_private_c = _stage_scope(connection, tmp_path, core_id, workspace_id="ws-c", scope_key=private_c,
                                   source_label="ws-c-agent", vector_provider="unknown", vector_model="unknown",
                                   include_vector=False)
    entries.extend(_write_root_scope_evidence(
        root, private_c, has_memory=True, has_motif=False, metadata_less=True,
        payload_label="ws-c-agent",
    ))
    private_plans["ws-c"].append(MaterializedRootScopePlan(private_c, RootRepresentationDisposition.UNKNOWN_IDENTITY))
    boundary = EvidenceOwnerBoundary("ws-c", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="agent-0")
    nodes, representation = (
        next(entry for entry in entries if entry.scope_key == private_c and entry.semantic_role is EvidenceSemanticRole.NODES),
        next(entry for entry in entries if entry.scope_key == private_c and entry.semantic_role is EvidenceSemanticRole.LEGACY_REPRESENTATION),
    )
    optional_edges = ExplicitSourceEvidence(
        SourceOwnerClass.PRIVATE_GRAPH_SOURCE, boundary, "edges.jsonl", EvidenceSemanticRole.EDGES,
        EvidencePresenceExpectation.EXPECTED_ABSENT, private_c,
        absence_reason=EvidenceAbsenceReason.OPTIONAL_EDGE_SOURCE,
    )
    metadata_source = qualify_metadata_less_per_eid_legacy_source(
        data_root=root, scope_key=private_c, legacy_eid=7,
        legacy_source_namespace_id=fact_private_c.plan.legacy_source_namespace_id,
        target_identity_namespace_id=fact_private_c.plan.target_identity_namespace_id,
        nodes_source=nodes, optional_edges_source=optional_edges, legacy_representation_source=representation,
    )
    inputs.append(RootNormalizationScopeInput(private_c, fact_private_c.plan, fact_private_c.snapshot_id,
        metadata_less_b3b_dispatches=(MetadataLessB3BDispatch(metadata_source, _b3b(fact_private_c, core_id, "private-c-b3b")),),
    ))

    for agent_id, total_rows in (("agent-zero", 0), ("agent-residue", 1)):
        empty_private = RootScopeKey("ws-d", RootScopeKind.PRIVATE, agent_id=agent_id)
        fact_empty_private = _stage_scope(
            connection, tmp_path, core_id, workspace_id="ws-d", scope_key=empty_private,
            source_label=f"ws-d-empty-private-{agent_id}", vector_provider="st",
            vector_model="BAAI/bge-small-en-v1.5", has_memory=False, include_vector=False,
        )
        private_root = root / "workspaces/ws-d/agents" / agent_id / "private"
        embeddings = private_root / "embeddings"
        embeddings.mkdir(parents=True, exist_ok=True)
        (embeddings / "manifest.json").write_text(
            json.dumps({"total_rows": total_rows}), encoding="utf-8",
        )
        if total_rows:
            np.save(embeddings / "orphan.npy", np.asarray([[1.0] + [0.0] * 383], dtype=np.float32))
        entries.extend(_write_root_scope_evidence(root, empty_private, has_memory=False, has_motif=False))
        private_owner = EvidenceOwnerBoundary(
            "ws-d", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id=agent_id,
        )
        entries.append(_present(
            root, SourceOwnerClass.EMBEDDING_MANIFEST, private_owner,
            "embeddings/manifest.json", EvidenceSemanticRole.EMBEDDING_MANIFEST, empty_private,
        ))
        if total_rows:
            entries.append(_present(
                root, SourceOwnerClass.LEGACY_REPRESENTATION_ARTIFACT, private_owner,
                "embeddings/orphan.npy", EvidenceSemanticRole.LEGACY_REPRESENTATION, empty_private,
            ))
        private_plans["ws-d"].append(MaterializedRootScopePlan(
            empty_private, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.EMPTY_PRIVATE,
        ))
        inputs.append(RootNormalizationScopeInput(
            empty_private, fact_empty_private.plan, fact_empty_private.snapshot_id,
        ))

    for workspace_id, domain_id, with_motif in (
        ("ws-e", "declared-no-motif", False),
        ("ws-f", "declared-with-motif", True),
    ):
        declared = RootScopeKey(workspace_id, RootScopeKind.SHARED, domain_id=domain_id)
        fact_declared = _stage_scope(
            connection, tmp_path, core_id, workspace_id=workspace_id, scope_key=declared,
            source_label=f"{workspace_id}-{domain_id}", vector_provider="st",
            vector_model="BAAI/bge-small-en-v1.5", has_memory=False, include_vector=False,
            motif_id="declared-empty-motif" if with_motif else None,
            motif_members=[] if with_motif else None,
        )
        domain_root = root / "workspaces" / workspace_id
        domain_root.mkdir(parents=True, exist_ok=True)
        (domain_root / "domains.json").write_text("{}", encoding="utf-8")
        entries.append(_present(
            root, SourceOwnerClass.DOMAIN_DECLARATION,
            EvidenceOwnerBoundary(workspace_id, EvidenceOwnerBoundaryKind.WORKSPACE),
            "domains.json", EvidenceSemanticRole.DOMAINS, None,
        ))
        shared_owner = EvidenceOwnerBoundary(
            workspace_id, EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id=domain_id,
        )
        entries.append(ExplicitSourceEvidence(
            SourceOwnerClass.SHARED_GRAPH_SOURCE, shared_owner, "nodes.jsonl", EvidenceSemanticRole.NODES,
            EvidencePresenceExpectation.EXPECTED_ABSENT, declared,
            absence_reason=EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION,
        ))
        if with_motif:
            entries.extend(_write_root_scope_evidence(root, declared, has_memory=False, has_motif=True)[1:])
        shared_plans[workspace_id].append(MaterializedRootScopePlan(
            declared, RootRepresentationDisposition.NO_VECTOR, MaterializedScopePosture.DECLARED_EMPTY_SHARED,
        ))
        inputs.append(RootNormalizationScopeInput(
            declared, fact_declared.plan, fact_declared.snapshot_id,
            b4c_requests=(_b4c(fact_declared, core_id, f"{workspace_id}-b4c"),) if with_motif else (),
        ))

    plans = (
        WorkspaceRootAdmissionPlan("ws-a", tuple(private_plans["ws-a"]), tuple(shared_plans["ws-a"])),
        WorkspaceRootAdmissionPlan("ws-b", tuple(private_plans["ws-b"]), tuple(shared_plans["ws-b"])),
        WorkspaceRootAdmissionPlan("ws-c", tuple(private_plans["ws-c"]), tuple(shared_plans["ws-c"])),
        WorkspaceRootAdmissionPlan(
            "ws-d", private_materialized_scopes=tuple(private_plans["ws-d"]),
            identity_only_agents=(
                IdentityOnlyAgentObservation("agent-residue", "identity-with-orphan-vector"),
                IdentityOnlyAgentObservation("agent-zero", "identity-with-zero-row-manifest"),
            ),
            declared_unmaterialized_domains=(DeclaredUnmaterializedDomain("future-domain", "declared-empty"),),
        ),
        WorkspaceRootAdmissionPlan(
            "ws-e", shared_materialized_scopes=tuple(shared_plans["ws-e"]),
            declared_unmaterialized_domains=(DeclaredUnmaterializedDomain("declared-no-motif", "declared-no-motif"),),
            no_memory_scope=True,
        ),
        WorkspaceRootAdmissionPlan(
            "ws-f", shared_materialized_scopes=tuple(shared_plans["ws-f"]),
            declared_unmaterialized_domains=(DeclaredUnmaterializedDomain("declared-with-motif", "declared-with-motif"),),
            no_memory_scope=True,
        ),
    )
    description = _description(root, entries, plans)
    embedder = _DeterministicEmbedder()
    request = RootNormalizationRequest(
        description=description, data_root=root, native_core_database_path=qualified.database_path,
        expected_native_core_id=core_id, scope_inputs=tuple(inputs),
        qualification_embedder_identity=WorkspaceNativeEmbedderIdentity("st", "BAAI/bge-small-en-v1.5", 384),
        b3b_embedder=embedder,
        post_write_configurations=tuple(
            _post_write_configuration(input_item.scope_plan)
            for input_item in inputs
            if input_item.scope_key.scope_kind is RootScopeKind.PRIVATE and input_item.all_b3_requests
        ),
    )
    return _Fixture(qualified, request, embedder, root, root / "workspaces/ws-c/agents/agent-0/private/emb_7.npy")


def test_root_wide_normalization_composes_b3_b4_and_generalized_readiness(tmp_path: Path) -> None:
    fixture = _positive_fixture(tmp_path)
    try:
        result = NativeRootWideNormalizationService(fixture.qualified.connection).normalize(fixture.request)

        assert result.root_normalization_complete and result.root_normalization_ready
        assert result.real_root_activation_ready is False and result.partial_activation is False
        assert result.expected_workspace_count == result.observed_workspace_closure == 6
        assert result.expected_materialized_scope_count == result.observed_materialized_scope_closure == 15
        assert result.generalized_readiness_result is not None
        assert result.generalized_readiness_result.generalized_staging_runtime_ready
        assert {item.lineage.value for scope in result.scope_results for item in scope.motif_results} == {"B4A", "B4B", "B4C"}
        assert {item.kind for scope in result.scope_results for item in scope.representation_results} == {
            RootRepresentationBootstrapKind.B3A, RootRepresentationBootstrapKind.B3B,
        }
        metadata_receipts = [
            item for scope in result.scope_results for item in scope.representation_results
            if item.metadata_less_source_evidence_identity is not None
        ]
        assert len(metadata_receipts) == 1 and metadata_receipts[0].state is RootChildCompletionState.COMPLETED
        assert len(fixture.embedder.calls) == 3
        assert "root-normalization memory ws-c-agent" in fixture.embedder.calls
        empty_results = {item.scope_key: item for item in result.scope_results}
        for agent_id in ("agent-zero", "agent-residue"):
            assert empty_results[RootScopeKey("ws-d", RootScopeKind.PRIVATE, agent_id=agent_id)].representation_results == ()
            assert empty_results[RootScopeKey("ws-d", RootScopeKind.PRIVATE, agent_id=agent_id)].motif_results == ()
        assert empty_results[RootScopeKey("ws-e", RootScopeKind.SHARED, domain_id="declared-no-motif")].representation_results == ()
        assert empty_results[RootScopeKey("ws-e", RootScopeKind.SHARED, domain_id="declared-no-motif")].motif_results == ()
        physical_no_motif = empty_results[RootScopeKey(
            "ws-b", RootScopeKind.SHARED, domain_id="empty-without-motif",
        )]
        assert physical_no_motif.representation_results == ()
        assert physical_no_motif.motif_results == ()
        readiness = next(item for item in result.generalized_readiness_result.scope_items if item.scope_key == physical_no_motif.scope_key)
        assert readiness.memory_fact_count == readiness.motif_fact_count == 0
        assert readiness.memory_closure_ready and readiness.motif_closure_ready
        assert readiness.empty_topology_reason.value == "ZERO_MOTIFS_EXPECTED"
        assert [item.lineage.value for item in empty_results[
            RootScopeKey("ws-f", RootScopeKind.SHARED, domain_id="declared-with-motif")
        ].motif_results] == ["B4C"]
        assert all(item.completed for item in result.workspace_results)
    finally:
        fixture.close()


def test_declared_empty_shared_is_runtime_membership_but_not_discovered_materialization(tmp_path: Path) -> None:
    fixture = _positive_fixture(tmp_path)
    try:
        description = fixture.request.description
        discovered = discover_canonical_root_layout(data_root=fixture.data_root)

        require_discovered_declared_census_parity(description=description, discovered=discovered)
        runtime_keys = {
            scope.scope_key
            for workspace in description.workspace_plans
            for scope in workspace.runtime_scopes
        }
        materialized_keys = set(discovered.materialized_scope_keys)
        no_motif = RootScopeKey("ws-e", RootScopeKind.SHARED, domain_id="declared-no-motif")
        with_motif = RootScopeKey("ws-f", RootScopeKind.SHARED, domain_id="declared-with-motif")
        assert {no_motif, with_motif} <= runtime_keys
        assert not {no_motif, with_motif} & materialized_keys

        (fixture.data_root / "workspaces/ws-e/domains/undeclared/shared").mkdir(parents=True)
        with pytest.raises(RootBlocker5BindingRefused, match="ROOT_DISCOVERED_DECLARED_SCOPE_CENSUS_MISMATCH"):
            require_discovered_declared_census_parity(
                description=description,
                discovered=discover_canonical_root_layout(data_root=fixture.data_root),
            )
    finally:
        fixture.close()


def test_physical_empty_shared_without_motif_refuses_b3_and_b4_dispatches(tmp_path: Path) -> None:
    fixture = _positive_fixture(tmp_path)
    try:
        key = RootScopeKey("ws-b", RootScopeKind.SHARED, domain_id="empty-without-motif")
        declared = next(
            scope
            for workspace in fixture.request.description.workspace_plans
            for scope in workspace.runtime_scopes
            if scope.scope_key == key
        )
        request = SimpleNamespace(
            expected_native_core_id=fixture.request.expected_native_core_id,
            target_lane=fixture.request.description.target_representation_lane,
        )
        baseline = SimpleNamespace(
            all_b3_requests=(), all_motif_requests=(),
            b3a_requests=(), b3b_requests=(), metadata_less_b3b_dispatches=(),
            b4a_requests=(), b4b_requests=(), b4c_requests=(),
        )
        _validate_scope_dispatch(
            declared, baseline, fixture.request.description.target_representation_lane,
            fixture.request.expected_native_core_id, fixture.request.description,
        )
        with pytest.raises(ValueError, match="cannot dispatch B3"):
            _validate_scope_dispatch(
                declared,
                SimpleNamespace(
                    all_b3_requests=(request,), all_motif_requests=(),
                    b3a_requests=(request,), b3b_requests=(), metadata_less_b3b_dispatches=(),
                    b4a_requests=(), b4b_requests=(), b4c_requests=(),
                ),
                fixture.request.description.target_representation_lane,
                fixture.request.expected_native_core_id,
                fixture.request.description,
            )
        with pytest.raises(ValueError, match="cannot dispatch B4"):
            _validate_scope_dispatch(
                declared,
                SimpleNamespace(
                    all_b3_requests=(), all_motif_requests=(request,),
                    b3a_requests=(), b3b_requests=(), metadata_less_b3b_dispatches=(),
                    b4a_requests=(), b4b_requests=(), b4c_requests=(request,),
                ),
                fixture.request.description.target_representation_lane,
                fixture.request.expected_native_core_id,
                fixture.request.description,
            )
    finally:
        fixture.close()


@pytest.mark.parametrize("point", tuple(RootNormalizationInterruptionPoint))
def test_root_normalization_resumes_all_authorized_checkpoints_without_reembedding(
    tmp_path: Path, point: RootNormalizationInterruptionPoint,
) -> None:
    fixture = _positive_fixture(tmp_path)
    try:
        service = NativeRootWideNormalizationService(fixture.qualified.connection)
        with pytest.raises(RootNormalizationInterrupted) as interrupted:
            service.normalize(fixture.request, _test_interrupt_after=point)
        resumed = service.normalize(replace(fixture.request, recovery_witness=interrupted.value.recovery_witness))
        assert resumed.root_normalization_complete
        assert len(fixture.embedder.calls) == 3
    finally:
        fixture.close()


def test_root_normalization_refuses_recovery_identity_and_source_drift(tmp_path: Path) -> None:
    fixture = _positive_fixture(tmp_path)
    try:
        service = NativeRootWideNormalizationService(fixture.qualified.connection)
        result = service.normalize(fixture.request)
        with pytest.raises(RootNormalizationRefused, match="ROOT_DESCRIPTION_DRIFT"):
            service.normalize(replace(
                fixture.request,
                description=replace(fixture.request.description, operator_identity="different-operator"),
                recovery_witness=result.recovery_witness,
            ))
        with pytest.raises(RootNormalizationRefused, match="ROOT_CENSUS_DRIFT"):
            service.normalize(replace(
                fixture.request,
                recovery_witness=replace(result.recovery_witness, expected_census_digest="0" * 64),
            ))
        with pytest.raises(RootNormalizationRefused, match="ROOT_TARGET_LANE_DRIFT"):
            service.normalize(replace(
                fixture.request,
                recovery_witness=replace(
                    result.recovery_witness,
                    target_lane=NativeRepresentationLane(
                        "st", "BAAI/bge-small-en-v1.5", 385,
                        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
                    ),
                ),
            ))
        fixture.metadata_vector.write_bytes(b"changed")
        with pytest.raises(RootNormalizationRefused, match="ROOT_SOURCE_MANIFEST_DRIFT"):
            service.normalize(replace(fixture.request, recovery_witness=result.recovery_witness))
    finally:
        fixture.close()


def test_incompatible_zero_member_root_refuses_b4c_and_never_becomes_partial_authority(tmp_path: Path) -> None:
    qualified = open_temporary_test_connection(tmp_path / "negative.db")
    try:
        connection = qualified.connection
        metadata = create_schema(connection)
        core_id = UUID(bytes=metadata.core_id)
        root = tmp_path / "negative-root"
        key = RootScopeKey("ws-negative", RootScopeKind.SHARED, domain_id="hash-domain")
        facts = _stage_scope(
            connection, tmp_path, core_id, workspace_id="ws-negative", scope_key=key,
            source_label="negative-empty", vector_provider="hash", vector_model="legacy-hash",
            has_memory=False, include_vector=False, motif_id="hash-empty", motif_members=[],
        )
        entries = _write_root_scope_evidence(root, key, has_memory=False, has_motif=True)
        plan = WorkspaceRootAdmissionPlan(
            "ws-negative", shared_materialized_scopes=(MaterializedRootScopePlan(
                key, RootRepresentationDisposition.TARGET_COMPATIBLE, MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
            ),),
        )
        request = RootNormalizationRequest(
            description=_description(root, entries, (plan,)), data_root=root,
            native_core_database_path=qualified.database_path, expected_native_core_id=core_id,
            scope_inputs=(RootNormalizationScopeInput(
                key, facts.plan, facts.snapshot_id, b4c_requests=(_b4c(facts, core_id, "negative-b4c"),),
            ),),
            qualification_embedder_identity=WorkspaceNativeEmbedderIdentity("st", "BAAI/bge-small-en-v1.5", 384),
            b3b_embedder=_DeterministicEmbedder(),
        )
        result = NativeRootWideNormalizationService(connection).normalize(request)
        motif = result.scope_results[0].motif_results[0]
        assert motif.lineage.value == "B4C" and motif.state is RootChildCompletionState.REFUSED
        assert result.root_normalization_complete is False
        assert result.root_normalization_ready is False
        assert result.real_root_activation_ready is False
        assert result.partial_activation is False
    finally:
        qualified.close()
