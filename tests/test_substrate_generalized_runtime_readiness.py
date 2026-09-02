"""Declared-topology generalized readiness over synthetic multi-private roots."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import numpy as np

from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    ExpectedRootCensus,
    GeneralizedNativeRuntimeReadinessRequest,
    GeneralizedScopeReadinessInput,
    MaterializedRootScopePlan,
    MigrationRehearsalConfig,
    MigrationRuntimeNormalizationRequest,
    MigrationRuntimeMotifProjectionRequest,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeRepresentationBootstrapRequest,
    MigrationRuntimeScopePlan,
    NativeGeneralizedRuntimeReadiness,
    NativeLegacyMigrationRehearsal,
    NativeMigrationRuntimeNormalizationService,
    NativeMigrationRuntimeMotifProjectionService,
    NativeMigrationRuntimeRepresentationBootstrapService,
    RepresentationDispositionCount,
    RootEvidenceManifest,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
    RootScopeKey,
    RootScopeKind,
    SourceOwnerClass,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceRootAdmissionPlan,
    WorkspaceTopologyCounts,
    create_snapshot_manifest,
)
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
)
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "st", "BAAI/bge-small-en-v1.5", 384,
        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


def _payload(agent_id: str) -> dict[str, object]:
    return {
        "summary": f"qualified private memory for {agent_id}",
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


class _InertSideStore:
    def load_anchor_state(self, **_kwargs): return {}
    def load_affect_state(self, **_kwargs): return {}
    def save_anchor_state(self, **_kwargs): raise AssertionError("readiness must not write")
    def save_affect_state(self, **_kwargs): raise AssertionError("readiness must not write")


def _post_write_configuration(plan: MigrationRuntimeScopePlan, lane: NativeRepresentationLane):
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
        parent_native_operation_key="R3-READINESS-NEVER-EXECUTED",
        expected_dimension=lane.dimension,
        embed=lambda _value: (_ for _ in ()).throw(AssertionError("readiness must not embed")),
        embedder_provider=lane.provider, embedder_model=lane.model, side_store=_InertSideStore(),
    )
    return NativePostWriteQualificationConfiguration(
        routing_scope=routing,
        profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=SimpleNamespace(), workspace=SimpleNamespace(), identity=SimpleNamespace(),
            agent_key=plan.agent_id or "agent",
            detect_canon_conflict=lambda *_args: (_ for _ in ()).throw(AssertionError("readiness must not call post-write")),
            proposal_allowed=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("readiness must not call post-write")),
            hivemind_log=SimpleNamespace(info=lambda *_args, **_kwargs: None),
        ),
        derived_runtime_template=template,
        motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False,
        checkpoint_snapshots_required=False,
        bridge_suggestions_required=False,
        deep_memory_required=False,
    )


def _ready_private_scope(connection, tmp_path: Path, core_id: UUID, workspace_id: str, agent_id: str):
    lane = _lane()
    object_ns, relationship_ns, motif_ns, alias_ns = (_id() for _ in range(4))
    unknown_scope, target_scope, idempotency, source_ns = (_id() for _ in range(4))
    for value, key in ((object_ns, "object"), (relationship_ns, "relationship"), (motif_ns, "motif")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), f"{workspace_id}-{agent_id}-{key}"))
    for value, key in ((unknown_scope, "unknown"), (target_scope, "target")):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), f"{workspace_id}-{agent_id}-{key}"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), f"{workspace_id}-{agent_id}-idem"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(alias_ns), f"{workspace_id}-{agent_id}-aliases"))
    source_root = tmp_path / "snapshots" / workspace_id / agent_id
    source_root.mkdir(parents=True)
    (source_root / "nodes.jsonl").write_bytes(_line({
        "eid": 7, "born_step": 1, "channel": 1, "payload": _payload(agent_id),
        "embedding_ref": {"map": "embeddings/shard.map.jsonl", "shard": "embeddings/vectors.npy", "row": 0, "dimension": 384, "dtype": "float32"},
    }))
    embeddings = source_root / "embeddings"; embeddings.mkdir()
    np.save(embeddings / "vectors.npy", np.asarray([[1.0] + [0.0] * 383], dtype=np.float32))
    (embeddings / "manifest.json").write_bytes(_line({
        "encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 384,
        "derivation_contract_version": "synthetic-capture-v1", "provider": lane.provider,
        "model": lane.model, "shards": [{"path": "embeddings/vectors.npy", "map": "embeddings/shard.map.jsonl"}],
    }))
    (embeddings / "shard.map.jsonl").write_bytes(_line({"eid": 7, "shard": "embeddings/vectors.npy", "row": 0, "dimension": 384}))
    manifest_path = source_root.parent / f"{agent_id}-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=source_root, manifest_path=manifest_path,
        legacy_source_namespace_id=source_ns, legacy_source_namespace_key=f"{workspace_id}-{agent_id}-source",
        capture_label="generalized readiness private fixture",
    )
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=source_root, manifest_path=manifest_path,
        config=MigrationRehearsalConfig(
            native_core_id=core_id, idempotency_namespace_id=idempotency,
            object_identity_namespace_id=object_ns, relationship_identity_namespace_id=relationship_ns,
            unknown_semantic_scope_id=unknown_scope,
        ),
    )
    plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=source_ns, workspace_id=workspace_id,
        scope_kind="PRIVATE_AGENT", agent_id=agent_id,
        target_identity_namespace_id=object_ns, target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=alias_ns, motif_identity_namespace_id=motif_ns,
        membership_identity_namespace_id=relationship_ns, idempotency_namespace_id=idempotency,
    )
    source_object, source_r1 = connection.execute(
        """SELECT object_id,current_revision_id FROM objects WHERE object_id=(
             SELECT object_id FROM legacy_object_aliases
              WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value='7'
        )""", (native_id_to_bytes(source_ns),),
    ).fetchone()
    normalized = NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(
        MigrationRuntimeNormalizationRequest(
            source_root, manifest_path, manifest.legacy_snapshot_id, source_ns, core_id, 7,
            UUID(bytes=source_r1), (plan,), idempotency, f"{workspace_id}-{agent_id}-b2",
        )
    )
    NativeMigrationRuntimeRepresentationBootstrapService(connection).bootstrap_from_legacy_capture(
        MigrationRuntimeRepresentationBootstrapRequest(
            source_root, manifest_path, manifest.legacy_snapshot_id, source_ns, core_id, 7,
            UUID(bytes=source_r1), normalized.revision_id, lane, idempotency,
            f"{workspace_id}-{agent_id}-b3a",
        )
    )
    return plan, MigrationRuntimeReadinessRequest(manifest.legacy_snapshot_id, core_id, (plan,), lane)


def _ready_member_bearing_shared_scope(
    connection, tmp_path: Path, core_id: UUID, workspace_id: str, domain_id: str,
):
    """Build one synthetic B2/B3A/B4A shared scope without an embedder."""
    lane = _lane()
    object_ns, relationship_ns, motif_ns, alias_ns = (_id() for _ in range(4))
    unknown_scope, target_scope, idempotency, source_ns = (_id() for _ in range(4))
    for value, key in ((object_ns, "object"), (relationship_ns, "relationship"), (motif_ns, "motif")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), f"{workspace_id}-{domain_id}-{key}"))
    for value, key in ((unknown_scope, "unknown"), (target_scope, "target")):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), f"{workspace_id}-{domain_id}-{key}"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), f"{workspace_id}-{domain_id}-idem"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(alias_ns), f"{workspace_id}-{domain_id}-aliases"))
    source_root = tmp_path / "snapshots" / workspace_id / f"{domain_id}-shared"
    source_root.mkdir(parents=True)
    (source_root / "nodes.jsonl").write_bytes(_line({
        "eid": 7, "born_step": 1, "channel": 1, "payload": _payload("shared"),
        "embedding_ref": {"map": "embeddings/shard.map.jsonl", "shard": "embeddings/vectors.npy", "row": 0, "dimension": 384, "dtype": "float32"},
    }))
    embeddings = source_root / "embeddings"; embeddings.mkdir()
    np.save(embeddings / "vectors.npy", np.asarray([[1.0] + [0.0] * 383], dtype=np.float32))
    (embeddings / "manifest.json").write_bytes(_line({
        "encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 384,
        "derivation_contract_version": "synthetic-capture-v1", "provider": lane.provider,
        "model": lane.model, "shards": [{"path": "embeddings/vectors.npy", "map": "embeddings/shard.map.jsonl"}],
    }))
    (embeddings / "shard.map.jsonl").write_bytes(_line({"eid": 7, "shard": "embeddings/vectors.npy", "row": 0, "dimension": 384}))
    workspace = source_root / "workspaces" / workspace_id; workspace.mkdir(parents=True)
    (workspace / "workspace_meta.json").write_text(json.dumps({
        "embed_provider": lane.provider, "embed_model": lane.model, "embed_dim": lane.dimension,
    }), encoding="utf-8")
    motifs = workspace / "domains" / domain_id; motifs.mkdir(parents=True)
    motif_id = f"{domain_id}-member-bearing"
    (motifs / "motifs.json").write_text(json.dumps({"motifs": {motif_id: {
        "motif_id": motif_id, "domain_id": domain_id, "label": "synthetic shared cluster",
        "centroid": [1.0] + [0.0] * 383, "strength": 0.8, "stability_score": 0.8,
        "contributing_agents": ["agent-0"], "created_ts": 1, "last_active_ts": 2, "members": [7],
    }}}), encoding="utf-8")
    manifest_path = source_root.parent / f"{domain_id}-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=source_root, manifest_path=manifest_path,
        legacy_source_namespace_id=source_ns, legacy_source_namespace_key=f"{workspace_id}-{domain_id}-source",
        capture_label="generalized readiness shared motif fixture",
    )
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=source_root, manifest_path=manifest_path,
        config=MigrationRehearsalConfig(
            native_core_id=core_id, idempotency_namespace_id=idempotency,
            object_identity_namespace_id=object_ns, relationship_identity_namespace_id=relationship_ns,
            unknown_semantic_scope_id=unknown_scope,
        ),
    )
    plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=source_ns, workspace_id=workspace_id, scope_kind="SHARED_DOMAIN",
        domain_id=domain_id, target_identity_namespace_id=object_ns, target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=alias_ns, motif_identity_namespace_id=motif_ns,
        membership_identity_namespace_id=relationship_ns, idempotency_namespace_id=idempotency,
        motif_domain_id=domain_id,
    )
    source_object, source_r1 = connection.execute(
        """SELECT object_id,current_revision_id FROM objects WHERE object_id=(
             SELECT object_id FROM legacy_object_aliases
              WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value='7'
        )""", (native_id_to_bytes(source_ns),),
    ).fetchone()
    normalized = NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(
        MigrationRuntimeNormalizationRequest(
            source_root, manifest_path, manifest.legacy_snapshot_id, source_ns, core_id, 7,
            UUID(bytes=source_r1), (plan,), idempotency, f"{workspace_id}-{domain_id}-b2",
        )
    )
    NativeMigrationRuntimeRepresentationBootstrapService(connection).bootstrap_from_legacy_capture(
        MigrationRuntimeRepresentationBootstrapRequest(
            source_root, manifest_path, manifest.legacy_snapshot_id, source_ns, core_id, 7,
            UUID(bytes=source_r1), normalized.revision_id, lane, idempotency, f"{workspace_id}-{domain_id}-b3a",
        )
    )
    motif_object, motif_r1 = connection.execute(
        """SELECT object_id,current_revision_id FROM objects WHERE object_id=(
             SELECT object_id FROM legacy_object_aliases
              WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?
        )""", (native_id_to_bytes(source_ns), motif_id),
    ).fetchone()
    NativeMigrationRuntimeMotifProjectionService(connection).project_lane_preserving_legacy_motif(
        MigrationRuntimeMotifProjectionRequest(
            source_root, manifest_path, manifest.legacy_snapshot_id, source_ns, core_id, motif_id,
            UUID(bytes=motif_object), UUID(bytes=motif_r1), (plan,), lane, idempotency,
            f"{workspace_id}-{domain_id}-b4a",
        )
    )
    return (
        plan,
        MigrationRuntimeReadinessRequest(manifest.legacy_snapshot_id, core_id, (plan,), lane),
        motif_id,
    )


def test_generalized_readiness_qualifies_multi_private_and_private_only_root(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "generalized.db")
    try:
        metadata = create_schema(qualified.connection)
        core_id = UUID(bytes=metadata.core_id)
        pairs = [("w1", f"agent-{index}") for index in range(5)] + [("w2", "agent-0")]
        prepared = [_ready_private_scope(qualified.connection, tmp_path, core_id, *pair) for pair in pairs]
        data_root = tmp_path / "root-description"
        entries = []
        private_scopes: dict[str, list[MaterializedRootScopePlan]] = {"w1": [], "w2": []}
        shared_scopes: dict[str, list[MaterializedRootScopePlan]] = {"w1": [], "w2": []}
        inputs = []
        configurations = []
        for (workspace_id, agent_id), (plan, b1_request) in zip(pairs, prepared, strict=True):
            scope_key = RootScopeKey(workspace_id, RootScopeKind.PRIVATE, agent_id=agent_id)
            source = data_root / "workspaces" / workspace_id / "agents" / agent_id / "private" / "nodes.jsonl"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(_line({"eid": 7, "payload": _payload(agent_id)}))
            entries.append(ExplicitSourceEvidence(
                SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
                EvidenceOwnerBoundary(workspace_id, EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id=agent_id),
                "nodes.jsonl", EvidenceSemanticRole.NODES, EvidencePresenceExpectation.EXPECTED_PRESENT,
                scope_key=scope_key, byte_length=source.stat().st_size,
                sha256_hex=hashlib.sha256(source.read_bytes()).hexdigest(),
            ))
            private_scopes[workspace_id].append(MaterializedRootScopePlan(
                scope_key, RootRepresentationDisposition.TARGET_COMPATIBLE,
            ))
            inputs.append(GeneralizedScopeReadinessInput(scope_key, b1_request))
            configurations.append(_post_write_configuration(plan, _lane()))
        shared_plan, shared_b1_request, shared_motif_id = _ready_member_bearing_shared_scope(
            qualified.connection, tmp_path, core_id, "w1", "collaboration",
        )
        shared_key = RootScopeKey("w1", RootScopeKind.SHARED, domain_id="collaboration")
        shared_nodes = data_root / "workspaces" / "w1" / "domains" / "collaboration" / "shared" / "nodes.jsonl"
        shared_nodes.parent.mkdir(parents=True, exist_ok=True)
        shared_nodes.write_bytes(_line({"eid": 7, "payload": _payload("shared")}))
        shared_motifs = data_root / "workspaces" / "w1" / "domains" / "collaboration" / "motifs.json"
        shared_motifs.parent.mkdir(parents=True, exist_ok=True)
        shared_motifs.write_text(json.dumps({"motifs": {shared_motif_id: {"members": [7]}}}), encoding="utf-8")
        entries.extend((
            ExplicitSourceEvidence(
                SourceOwnerClass.SHARED_GRAPH_SOURCE,
                EvidenceOwnerBoundary("w1", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="collaboration"),
                "nodes.jsonl", EvidenceSemanticRole.NODES, EvidencePresenceExpectation.EXPECTED_PRESENT,
                scope_key=shared_key, byte_length=shared_nodes.stat().st_size,
                sha256_hex=hashlib.sha256(shared_nodes.read_bytes()).hexdigest(),
            ),
            ExplicitSourceEvidence(
                SourceOwnerClass.MOTIF_SOURCE,
                EvidenceOwnerBoundary("w1", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="collaboration"),
                "motifs.json", EvidenceSemanticRole.MOTIFS, EvidencePresenceExpectation.EXPECTED_PRESENT,
                scope_key=shared_key, byte_length=shared_motifs.stat().st_size,
                sha256_hex=hashlib.sha256(shared_motifs.read_bytes()).hexdigest(),
            ),
        ))
        shared_scopes["w1"].append(MaterializedRootScopePlan(
            shared_key, RootRepresentationDisposition.TARGET_COMPATIBLE,
        ))
        inputs.append(GeneralizedScopeReadinessInput(shared_key, shared_b1_request))
        description = RootNativeProductionAdmissionDescription(
            data_root_identity="synthetic-multi-private", operator_identity="offline-test",
            workspace_plans=tuple(
                WorkspaceRootAdmissionPlan(
                    workspace_id,
                    private_materialized_scopes=tuple(private_scopes[workspace_id]),
                    shared_materialized_scopes=tuple(shared_scopes[workspace_id]),
                )
                for workspace_id in sorted(private_scopes)
            ),
            target_representation_lane=_lane(),
            expected_census=ExpectedRootCensus(
                2, 6, 1, 7,
                tuple(RepresentationDispositionCount(item, 7 if item is RootRepresentationDisposition.TARGET_COMPATIBLE else 0)
                      for item in RootRepresentationDisposition),
                WorkspaceTopologyCounts(0, 1, 1, 1, 1, 0),
            ),
            explicit_source_manifest=RootEvidenceManifest(tuple(entries)),
            external_owner_observations=(), feature_posture=RootFeaturePosture("synthetic", False, False),
        )
        request = GeneralizedNativeRuntimeReadinessRequest(
            description=description, data_root=data_root,
            native_core_database_path=qualified.database_path, expected_native_core_id=core_id,
            scope_inputs=tuple(inputs),
            qualification_embedder_identity=WorkspaceNativeEmbedderIdentity("st", "BAAI/bge-small-en-v1.5", 384),
            post_write_configurations=tuple(configurations),
        )
        report = NativeGeneralizedRuntimeReadiness(qualified.connection).run(request)
        assert report.generalized_staging_runtime_ready, report.reason_codes
        assert report.census_closure_ready and report.declared_topology_ready
        assert [item.materialized_scope_count for item in report.workspace_items] == [6, 1]
        assert sum(item.motif_fact_count for item in report.scope_items) == 1
        assert all(item.motif_closure_ready for item in report.scope_items)
        assert all(item.memory_fact_count == 1 and item.memory_closure_ready for item in report.scope_items)
        missing = NativeGeneralizedRuntimeReadiness(qualified.connection).run(
            replace(request, scope_inputs=request.scope_inputs[:-1])
        )
        assert not missing.census_closure_ready
        assert "SCOPE_INPUT_SET_MISMATCH" in missing.reason_codes
        extra_scope = RootScopeKey("w2", RootScopeKind.PRIVATE, agent_id="undeclared")
        extra_plan = replace(prepared[-1][0], agent_id="undeclared")
        extra_input = GeneralizedScopeReadinessInput(
            extra_scope, replace(prepared[-1][1], scope_plans=(extra_plan,)),
        )
        extra = NativeGeneralizedRuntimeReadiness(qualified.connection).run(
            replace(request, scope_inputs=request.scope_inputs + (extra_input,))
        )
        assert not extra.census_closure_ready
        assert "SCOPE_INPUT_SET_MISMATCH" in extra.reason_codes
        no_motif_manifest = RootEvidenceManifest(tuple(
            entry for entry in entries if entry.semantic_role is not EvidenceSemanticRole.MOTIFS
        ))
        unexpected_motif = NativeGeneralizedRuntimeReadiness(qualified.connection).run(
            replace(request, description=replace(description, explicit_source_manifest=no_motif_manifest))
        )
        assert not unexpected_motif.generalized_staging_runtime_ready
        assert "DECLARED_ZERO_MOTIFS_HAS_RUNTIME_MOTIF" in unexpected_motif.reason_codes
    finally:
        qualified.close()


def test_generalized_readiness_refuses_declared_memory_graph_without_migrated_memory(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "missing-memory.db")
    try:
        metadata = create_schema(qualified.connection)
        core_id = UUID(bytes=metadata.core_id)
        object_ns, relationship_ns, motif_ns, alias_ns = (_id() for _ in range(4))
        unknown_scope, target_scope, idempotency, source_ns = (_id() for _ in range(4))
        for value, key in ((object_ns, "objects"), (relationship_ns, "relationships"), (motif_ns, "motifs")):
            qualified.connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
        for value, key in ((unknown_scope, "unknown"), (target_scope, "target")):
            qualified.connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key))
        qualified.connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "missing-memory-idempotency"))
        qualified.connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(alias_ns), "missing-memory-aliases"))
        plan = MigrationRuntimeScopePlan(
            legacy_source_namespace_id=source_ns, workspace_id="missing", scope_kind="PRIVATE_AGENT",
            agent_id="aria", target_identity_namespace_id=object_ns, target_semantic_scope_id=target_scope,
            motif_alias_namespace_id=alias_ns, motif_identity_namespace_id=motif_ns,
            membership_identity_namespace_id=relationship_ns, idempotency_namespace_id=idempotency,
        )
        scope_key = RootScopeKey("missing", RootScopeKind.PRIVATE, agent_id="aria")
        data_root = tmp_path / "missing-memory-root"
        nodes = data_root / "workspaces" / "missing" / "agents" / "aria" / "private" / "nodes.jsonl"
        nodes.parent.mkdir(parents=True)
        nodes.write_bytes(_line({"eid": 7, "payload": _payload("aria")}))
        description = RootNativeProductionAdmissionDescription(
            data_root_identity="synthetic-missing-memory", operator_identity="offline-test",
            workspace_plans=(WorkspaceRootAdmissionPlan(
                "missing", private_materialized_scopes=(MaterializedRootScopePlan(
                    scope_key, RootRepresentationDisposition.TARGET_COMPATIBLE,
                ),),
            ),),
            target_representation_lane=_lane(),
            expected_census=ExpectedRootCensus(
                1, 1, 0, 1,
                tuple(RepresentationDispositionCount(item, 1 if item is RootRepresentationDisposition.TARGET_COMPATIBLE else 0)
                      for item in RootRepresentationDisposition),
                WorkspaceTopologyCounts(0, 1, 0, 1, 0, 0),
            ),
            explicit_source_manifest=RootEvidenceManifest((ExplicitSourceEvidence(
                SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
                EvidenceOwnerBoundary("missing", EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, agent_id="aria"),
                "nodes.jsonl", EvidenceSemanticRole.NODES, EvidencePresenceExpectation.EXPECTED_PRESENT,
                scope_key=scope_key, byte_length=nodes.stat().st_size,
                sha256_hex=hashlib.sha256(nodes.read_bytes()).hexdigest(),
            ),)),
            external_owner_observations=(), feature_posture=RootFeaturePosture("synthetic", False, False),
        )
        request = GeneralizedNativeRuntimeReadinessRequest(
            description=description, data_root=data_root,
            native_core_database_path=qualified.database_path, expected_native_core_id=core_id,
            scope_inputs=(GeneralizedScopeReadinessInput(
                scope_key, MigrationRuntimeReadinessRequest(_id(), core_id, (plan,), _lane()),
            ),),
            qualification_embedder_identity=WorkspaceNativeEmbedderIdentity("st", "BAAI/bge-small-en-v1.5", 384),
        )
        report = NativeGeneralizedRuntimeReadiness(qualified.connection).run(request)
        assert not report.generalized_staging_runtime_ready
        assert report.scope_items[0].memory_fact_count == 0
        assert "DECLARED_MEMORY_GRAPH_HAS_NO_MIGRATED_MEMORY" in report.reason_codes
        changes_before = qualified.connection.total_changes
        nodes.write_bytes(_line({"eid": 8, "payload": _payload("aria")}))
        drift = NativeGeneralizedRuntimeReadiness(qualified.connection).run(request)
        assert not drift.source_manifest_valid
        assert "SOURCE_MANIFEST_DRIFT" in drift.reason_codes
        assert qualified.connection.total_changes == changes_before
    finally:
        qualified.close()
