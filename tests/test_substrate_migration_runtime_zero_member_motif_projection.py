"""B4C target-compatible zero-member motif projection qualification."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest

from torment_service.motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    decide_attach_or_create,
    motif_density,
    motif_gravity_bonus,
    realize_attach_next_state,
)
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import (
    SubstrateEvidenceIntegrityMismatch,
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    MigrationRehearsalConfig,
    MigrationRuntimeMotifProjectionRefused,
    MigrationRuntimeMotifProjectionRequest,
    MigrationRuntimeMotifRegeometryProjectionRefused,
    MigrationRuntimeMotifRegeometryProjectionRequest,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeScopePlan,
    MigrationRuntimeZeroMemberMotifProjectionRefused,
    MigrationRuntimeZeroMemberMotifProjectionRequest,
    NativeLegacyMigrationRehearsal,
    NativeMigrationRuntimeMotifProjectionService,
    NativeMigrationRuntimeMotifRegeometryProjectionService,
    NativeMigrationRuntimeReadinessPreflight,
    EvidenceAbsenceReason,
    EvidenceOwnerBoundary,
    EvidenceOwnerBoundaryKind,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    GeneralizedNativeRuntimeReadinessRequest,
    GeneralizedScopeReadinessInput,
    IdentityOnlyAgentObservation,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    NativeGeneralizedRuntimeReadiness,
    RootEvidenceManifest,
    RootFeaturePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
    RootScopeKey,
    RootScopeKind,
    SourceOwnerClass,
    WorkspaceRootAdmissionPlan,
    ExpectedRootCensus,
    RepresentationDispositionCount,
    WorkspaceTopologyCounts,
    WorkspaceNativeEmbedderIdentity,
    NativeMigrationRuntimeZeroMemberMotifProjectionService,
    create_snapshot_manifest,
)
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.motifs import MotifState, NativeMotifService
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.schema import create_schema
from test_substrate_workspace_runtime_readiness import _configuration


_TARGET_PROVIDER = "st"
_TARGET_MODEL = "BAAI/bge-small-en-v1.5"
_TARGET_DIMENSION = 384


def _id():
    return generate_native_id()


def _line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"


def _payload() -> dict[str, object]:
    return {
        "summary": "B4C inert source node",
        "type": "memory",
        "memory_class": "core",
        "strength": 0.7,
        "confidence": 0.9,
        "seed_pos0": [1, 2, 3],
        "seed_v0": [0.1, 0.2, 0.3],
        "governance": {
            "protected": False,
            "non_shareable": False,
            "collective_export_blocked": False,
            "collective_reingest_blocked": False,
            "decay_accelerated": False,
        },
        "provenance": ProvenanceV1(
            source_type="role_output",
            source_role="tester",
            write_path="cognition_writeback",
            parent_eids=[],
            created_at_step=1,
            created_at_ts="2024-01-01T00:00:00Z",
        ).to_dict(),
        "lifecycle_status": {
            "state": "active",
            "is_authoritative_on_row": True,
            "requires_join": None,
            "set_by": {"actor": "user", "via": "api", "at": 1},
            "history_ref": None,
        },
    }


def _lane(provider=_TARGET_PROVIDER, model=_TARGET_MODEL, dimension=_TARGET_DIMENSION):
    return NativeRepresentationLane(
        provider,
        model,
        dimension,
        "COMPAT_EMBEDDING",
        1,
        "compat-embedding-v1",
        "RAW_VECTOR",
        "float32",
    )


def _context(
    tmp_path: Path,
    *,
    workspace_lane=(_TARGET_PROVIDER, _TARGET_MODEL, _TARGET_DIMENSION),
    include_workspace_meta=True,
    malformed_workspace_meta=False,
    include_extra=True,
    include_source_node=True,
    scope_kind="PRIVATE_AGENT",
    motif_strength: float = 0.91,
    motif_stability: float = 0.83,
):
    qualified = open_temporary_test_connection(tmp_path / "b4c.db")
    connection = qualified.connection
    metadata = create_schema(connection)
    object_ns, relationship_ns, motif_ns, target_alias_ns = (_id() for _ in range(4))
    unknown_scope, target_scope, idempotency = (_id() for _ in range(3))
    for value, key in (
        (object_ns, "b4c-objects"),
        (relationship_ns, "b4c-relationships"),
        (motif_ns, "b4c-motifs"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(value), key),
        )
    for value, key in ((unknown_scope, "b4c-unknown"), (target_scope, "b4c-target")):
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(value), key),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency), "b4c-idempotency"),
    )
    connection.execute(
        "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(target_alias_ns), "b4c-target-aliases"),
    )

    root = tmp_path / "frozen" / "legacy"
    root.mkdir(parents=True)
    if include_source_node:
        (root / "nodes.jsonl").write_bytes(
            _line({"eid": 7, "born_step": 1, "channel": 1, "payload": _payload()})
        )
    workspace = root / "workspaces" / "orchard"
    workspace.mkdir(parents=True)
    if include_workspace_meta:
        workspace_meta = "{" if malformed_workspace_meta else json.dumps(
            {
                "embed_provider": workspace_lane[0],
                "embed_model": workspace_lane[1],
                "embed_dim": workspace_lane[2],
            }
        )
        (workspace / "workspace_meta.json").write_text(workspace_meta, encoding="utf-8")
    motif_dir = workspace / "domains" / "reflection"
    motif_dir.mkdir(parents=True)
    raw_motif: dict[str, object] = {
        "motif_id": "motif-b4c",
        "domain_id": "reflection",
        "label": "qualified empty basin",
        "centroid": [1.0] + [0.0] * (_TARGET_DIMENSION - 1),
        "strength": motif_strength,
        "stability_score": motif_stability,
        "contributing_agents": ["aria", "boris"],
        "created_ts": 4,
        "last_active_ts": 9,
        "members": [],
    }
    if include_extra:
        raw_motif["derivation_metadata"] = {
            "kind": "LEGACY_AGGREGATE",
            "source": "current-registry",
        }
        raw_motif["qualified_marker"] = "preserve-exactly"
    motif_path = motif_dir / "motifs.json"
    motif_path.write_text(json.dumps({"motifs": {"motif-b4c": raw_motif}}), encoding="utf-8")
    source_ns = _id()
    manifest_path = root.parent / "manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=source_ns,
        legacy_source_namespace_key="b4c-source",
        capture_label="B4C fixture",
    )
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=root,
        manifest_path=manifest_path,
        config=MigrationRehearsalConfig(
            native_core_id=_id(),
            idempotency_namespace_id=idempotency,
            object_identity_namespace_id=object_ns,
            relationship_identity_namespace_id=relationship_ns,
            unknown_semantic_scope_id=unknown_scope,
        ),
    )
    plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=source_ns,
        workspace_id="orchard",
        scope_kind=scope_kind,
        agent_id="aria" if scope_kind == "PRIVATE_AGENT" else None,
        domain_id="reflection" if scope_kind == "SHARED_DOMAIN" else None,
        target_identity_namespace_id=object_ns,
        target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=target_alias_ns,
        motif_identity_namespace_id=motif_ns,
        membership_identity_namespace_id=relationship_ns,
        idempotency_namespace_id=idempotency,
        motif_domain_id="reflection",
    )
    source_object, source_r1 = connection.execute(
        """
        SELECT object_id,current_revision_id
          FROM objects
         WHERE object_id=(
            SELECT object_id FROM legacy_object_aliases
             WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID'
               AND alias_value='motif-b4c'
         )
        """,
        (native_id_to_bytes(source_ns),),
    ).fetchone()
    request = MigrationRuntimeZeroMemberMotifProjectionRequest(
        root,
        manifest_path,
        manifest.legacy_snapshot_id,
        source_ns,
        UUID(bytes=metadata.core_id),
        "motif-b4c",
        UUID(bytes=source_object),
        UUID(bytes=source_r1),
        (plan,),
        _lane(),
        idempotency,
        "b4c-project",
    )
    return qualified, {
        "connection": connection,
        "root": root,
        "motif_path": motif_path,
        "raw": raw_motif,
        "manifest": manifest,
        "plan": plan,
        "lane": _lane(),
        "request": request,
        "source": UUID(bytes=source_object),
        "source_r1": UUID(bytes=source_r1),
        "idempotency": idempotency,
    }


def _derived_count(connection) -> int:
    return connection.execute(
        "SELECT count(*) FROM objects WHERE object_kind='DERIVED_MOTIF'"
    ).fetchone()[0]


def _native_memory(facts, key: str):
    return NativeObjectService(facts["connection"]).create_object(
        idempotency_namespace_id=facts["idempotency"],
        idempotency_key=f"b4c-memory:{key}",
        state=ObjectState(
            facts["plan"].target_identity_namespace_id,
            facts["plan"].target_semantic_scope_id,
            "LEGACY_CORE_NODE",
            "EXISTS",
            "EXPLICIT",
            True,
            "DERIVED",
            "NOT_APPLICABLE",
            {"summary": f"B4C native member {key}"},
            "JSON",
        ),
    )


def test_b4c_projects_exact_active_zero_member_state_and_reader_parity(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]
        service = NativeMigrationRuntimeZeroMemberMotifProjectionService(connection)
        source_before = connection.execute(
            "SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
            (native_id_to_bytes(facts["source"]),),
        ).fetchone()
        result = service.project_target_compatible_zero_member_motif(facts["request"])
        assert service.project_target_compatible_zero_member_motif(facts["request"]) == result
        assert _derived_count(connection) == 1
        assert connection.execute(
            "SELECT count(*) FROM relationships WHERE creating_transition_id=?",
            (native_id_to_bytes(result.transition_id),),
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM relationship_revision_effects WHERE transition_id=?",
            (native_id_to_bytes(result.transition_id),),
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT output_role,output_kind FROM operation_outputs WHERE operation_id=?",
            (native_id_to_bytes(result.operation_id),),
        ).fetchall() == [("MIGRATION_RUNTIME_ZERO_MEMBER_MOTIF_PROJECTION", "OBJECT")]
        state = NativeMotifService(connection).get_current_motif(result.motif_object_id).state
        assert state.runtime_motif_id == facts["raw"]["motif_id"]
        assert state.domain_id == facts["raw"]["domain_id"]
        assert state.label == facts["raw"]["label"]
        assert list(state.centroid) == facts["raw"]["centroid"]
        assert state.strength == facts["raw"]["strength"]
        assert state.stability_score == facts["raw"]["stability_score"]
        assert list(state.contributing_agents) == facts["raw"]["contributing_agents"]
        assert state.created_ts == facts["raw"]["created_ts"]
        assert state.last_active_ts == facts["raw"]["last_active_ts"]
        assert dict(state.derivation_metadata or {}) == facts["raw"]["derivation_metadata"]
        assert dict(state.extra_payload or {}) == {"qualified_marker": "preserve-exactly"}
        assert connection.execute(
            "SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
            (native_id_to_bytes(facts["source"]),),
        ).fetchone() == source_before

        reader = NativeMotifRuntimeReader(connection)
        catalog = reader.list_runtime_motifs(
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            domain_id="reflection",
            semantic_scope_id=facts["plan"].target_semantic_scope_id,
        )
        assert len(catalog) == 1
        model = catalog[0].read_model
        assert model.member_count == 0
        assert motif_density(model.member_count) == 0.0
        assert motif_gravity_bonus(model, CURRENT_MOTIF_DECISION_POLICY) == pytest.approx(
            0.10 * facts["raw"]["strength"] + 0.05 * facts["raw"]["stability_score"]
        )
        assert reader.list_ordered_current_motif_members(result.motif_object_id) == ()
        assert reader.domain_centroid(
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            domain_id="reflection",
            dimension=_TARGET_DIMENSION,
            semantic_scope_id=facts["plan"].target_semantic_scope_id,
        ).shape == (_TARGET_DIMENSION,)
    finally:
        qualified.close()


def test_b1_recognizes_only_reader_certified_b4c_zero_member_lineage(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        NativeMigrationRuntimeZeroMemberMotifProjectionService(
            facts["connection"]
        ).project_target_compatible_zero_member_motif(facts["request"])
        report = NativeMigrationRuntimeReadinessPreflight(facts["connection"]).run(
            MigrationRuntimeReadinessRequest(
                facts["manifest"].legacy_snapshot_id,
                facts["request"].expected_native_core_id,
                (facts["plan"],),
                facts["lane"],
            )
        )
        motif = report.motif_items[0]
        assert motif.readiness.value == "RUNTIME_READY_AS_IS", motif.reason_codes
        assert motif.membership_count == 0
        assert "MOTIF_HAS_NO_CURRENT_MEMBERS" not in motif.reason_codes
    finally:
        qualified.close()


def test_b1_keeps_the_zero_member_blocker_without_b4c_certification(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        report = NativeMigrationRuntimeReadinessPreflight(facts["connection"]).run(
            MigrationRuntimeReadinessRequest(
                facts["manifest"].legacy_snapshot_id,
                facts["request"].expected_native_core_id,
                (facts["plan"],),
                facts["lane"],
            )
        )
        motif = report.motif_items[0]
        assert motif.readiness.value != "RUNTIME_READY_AS_IS"
        assert "MOTIF_HAS_NO_CURRENT_MEMBERS" in motif.reason_codes
    finally:
        qualified.close()


def test_generalized_readiness_accepts_declared_empty_shared_b4c_scope(tmp_path: Path):
    qualified, facts = _context(
        tmp_path,
        include_source_node=False,
        scope_kind="SHARED_DOMAIN",
    )
    try:
        NativeMigrationRuntimeZeroMemberMotifProjectionService(
            facts["connection"]
        ).project_target_compatible_zero_member_motif(facts["request"])
        scope_key = RootScopeKey("orchard", RootScopeKind.SHARED, domain_id="reflection")
        workspace_meta = facts["root"] / "workspaces" / "orchard" / "workspace_meta.json"
        manifest = RootEvidenceManifest((
            ExplicitSourceEvidence(
                SourceOwnerClass.WORKSPACE_IDENTITY_METADATA,
                EvidenceOwnerBoundary("orchard", EvidenceOwnerBoundaryKind.WORKSPACE),
                "workspace_meta.json", EvidenceSemanticRole.WORKSPACE_META,
                EvidencePresenceExpectation.EXPECTED_PRESENT,
                byte_length=workspace_meta.stat().st_size,
                sha256_hex=hashlib.sha256(workspace_meta.read_bytes()).hexdigest(),
            ),
            ExplicitSourceEvidence(
                SourceOwnerClass.SHARED_GRAPH_SOURCE,
                EvidenceOwnerBoundary("orchard", EvidenceOwnerBoundaryKind.SHARED_SCOPE, domain_id="reflection"),
                "nodes.jsonl", EvidenceSemanticRole.NODES,
                EvidencePresenceExpectation.EXPECTED_ABSENT,
                scope_key=scope_key,
                absence_reason=EvidenceAbsenceReason.EMPTY_GRAPH,
            ),
            ExplicitSourceEvidence(
                SourceOwnerClass.MOTIF_SOURCE,
                EvidenceOwnerBoundary("orchard", EvidenceOwnerBoundaryKind.DOMAIN, domain_id="reflection"),
                "motifs.json", EvidenceSemanticRole.MOTIFS,
                EvidencePresenceExpectation.EXPECTED_PRESENT,
                scope_key=scope_key,
                byte_length=facts["motif_path"].stat().st_size,
                sha256_hex=hashlib.sha256(facts["motif_path"].read_bytes()).hexdigest(),
            ),
        ))
        description = RootNativeProductionAdmissionDescription(
            data_root_identity="synthetic-generalized-b4c",
            operator_identity="offline-test",
            workspace_plans=(WorkspaceRootAdmissionPlan(
                "orchard",
                shared_materialized_scopes=(MaterializedRootScopePlan(
                    scope_key, RootRepresentationDisposition.TARGET_COMPATIBLE,
                    MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF,
                ),),
            ),),
            target_representation_lane=facts["lane"],
            expected_census=ExpectedRootCensus(
                1, 0, 1, 1,
                tuple(RepresentationDispositionCount(item, 1 if item is RootRepresentationDisposition.TARGET_COMPATIBLE else 0)
                      for item in RootRepresentationDisposition),
                WorkspaceTopologyCounts(1, 0, 0, 0, 1, 0),
            ),
            explicit_source_manifest=manifest,
            external_owner_observations=(),
            feature_posture=RootFeaturePosture("synthetic", False, False),
        )
        request = GeneralizedNativeRuntimeReadinessRequest(
            description=description,
            data_root=facts["root"],
            native_core_database_path=qualified.database_path,
            expected_native_core_id=facts["request"].expected_native_core_id,
            scope_inputs=(GeneralizedScopeReadinessInput(
                scope_key,
                MigrationRuntimeReadinessRequest(
                    facts["manifest"].legacy_snapshot_id,
                    facts["request"].expected_native_core_id,
                    (facts["plan"],),
                    facts["lane"],
                ),
            ),),
            qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(
                facts["lane"].provider, facts["lane"].model, facts["lane"].dimension,
            ),
            post_write_configurations=(),
        )
        report = NativeGeneralizedRuntimeReadiness(facts["connection"]).run(request)
        assert report.generalized_staging_runtime_ready, report.reason_codes
        assert report.activation_ready is False
        assert report.scope_items[0].memory_fact_count == 0
        assert report.scope_items[0].motif_lineages == ("B4C",)
        _native_memory(facts, "unexpected-empty-shared")
        unexpected_memory = NativeGeneralizedRuntimeReadiness(facts["connection"]).run(request)
        assert not unexpected_memory.generalized_staging_runtime_ready
        assert "DECLARED_EMPTY_SCOPE_HAS_MEMORY" in unexpected_memory.reason_codes
    finally:
        qualified.close()


def test_generalized_readiness_completes_no_memory_workspace_without_binding(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "no-memory.db")
    try:
        metadata = create_schema(qualified.connection)
        root = tmp_path / "no-memory-root"
        workspace = root / "workspaces" / "scaffold"
        workspace.mkdir(parents=True)
        workspace_meta = workspace / "workspace_meta.json"
        workspace_meta.write_text(json.dumps({
            "embed_provider": _TARGET_PROVIDER,
            "embed_model": _TARGET_MODEL,
            "embed_dim": _TARGET_DIMENSION,
        }), encoding="utf-8")
        manifest = RootEvidenceManifest((ExplicitSourceEvidence(
            SourceOwnerClass.WORKSPACE_IDENTITY_METADATA,
            EvidenceOwnerBoundary("scaffold", EvidenceOwnerBoundaryKind.WORKSPACE),
            "workspace_meta.json", EvidenceSemanticRole.WORKSPACE_META,
            EvidencePresenceExpectation.EXPECTED_PRESENT,
            byte_length=workspace_meta.stat().st_size,
            sha256_hex=hashlib.sha256(workspace_meta.read_bytes()).hexdigest(),
        ),))
        description = RootNativeProductionAdmissionDescription(
            data_root_identity="synthetic-no-memory",
            operator_identity="offline-test",
            workspace_plans=(WorkspaceRootAdmissionPlan(
                "scaffold",
                identity_only_agents=(IdentityOnlyAgentObservation("aria", "identity-observed"),),
                no_memory_scope=True,
            ),),
            target_representation_lane=_lane(),
            expected_census=ExpectedRootCensus(
                1, 0, 0, 0,
                tuple(RepresentationDispositionCount(item, 0) for item in RootRepresentationDisposition),
                WorkspaceTopologyCounts(1, 0, 0, 1, 0, 0),
            ),
            explicit_source_manifest=manifest,
            external_owner_observations=(),
            feature_posture=RootFeaturePosture("synthetic", False, False),
        )
        report = NativeGeneralizedRuntimeReadiness(qualified.connection).run(
            GeneralizedNativeRuntimeReadinessRequest(
                description=description,
                data_root=root,
                native_core_database_path=qualified.database_path,
                expected_native_core_id=UUID(bytes=metadata.core_id),
                scope_inputs=(),
                qualification_embedder_identity=WorkspaceNativeEmbedderIdentity(
                    _TARGET_PROVIDER, _TARGET_MODEL, _TARGET_DIMENSION,
                ),
            )
        )
        assert report.generalized_staging_runtime_ready, report.reason_codes
        assert report.a3d_binding_constructible and report.a3d_routing_constructible
        assert report.a3d_post_write_constructible
        assert report.workspace_items[0].materialized_scope_count == 0
        assert report.workspace_items[0].no_memory_scope_expected
    finally:
        qualified.close()


def test_b4c_first_future_member_uses_existing_decision_and_add_member_path(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]
        result = NativeMigrationRuntimeZeroMemberMotifProjectionService(connection).project_target_compatible_zero_member_motif(facts["request"])
        reader = NativeMotifRuntimeReader(connection)
        model = reader.list_runtime_motifs(
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            domain_id="reflection",
            semantic_scope_id=facts["plan"].target_semantic_scope_id,
        )[0].read_model
        decision = decide_attach_or_create(
            (model,), np.asarray(facts["raw"]["centroid"], dtype=np.float32), 0.62,
        )
        assert decision.kind == "ATTACH_EXISTING"
        assert decision.selected == model
        assert decision.pre_mutation_density == 0.0
        successor = realize_attach_next_state(decision, agent_id="cora", last_active_ts=10)
        member = _native_memory(facts, "first")
        current = NativeMotifService(connection).get_current_motif(result.motif_object_id)
        added = NativeMotifService(connection).add_motif_member(
            idempotency_namespace_id=facts["idempotency"],
            idempotency_key="b4c-first-future-member",
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            membership_identity_namespace_id=facts["plan"].membership_identity_namespace_id,
            motif_object_id=result.motif_object_id,
            expected_motif_revision_id=current.motif_revision_id,
            state=MotifState(
                current.state.semantic_scope_id,
                successor.runtime_motif_id,
                successor.domain_id,
                successor.label,
                successor.centroid,
                successor.strength,
                successor.stability_score,
                successor.contributing_agents,
                successor.created_ts,
                successor.last_active_ts,
                current.state.derivation_metadata,
                current.state.extra_payload,
            ),
            member_object_id=member.object_id,
        )
        assert added.motif_revision_ordinal == 2
        catalog = reader.list_runtime_motifs(
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            domain_id="reflection",
            semantic_scope_id=facts["plan"].target_semantic_scope_id,
        )
        assert catalog[0].read_model.member_count == 1
        assert [item.member_object_id for item in reader.list_ordered_current_motif_members(result.motif_object_id)] == [member.object_id]
    finally:
        qualified.close()


def test_b4c_recovery_retries_and_source_drift_refuse_without_partial_projection(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]
        service = NativeMigrationRuntimeZeroMemberMotifProjectionService(connection)
        with pytest.raises(RuntimeError, match="response loss"):
            service.project_target_compatible_zero_member_motif(
                facts["request"], _test_lose_response_after_commit=True,
            )
        recovered = service.project_target_compatible_zero_member_motif(facts["request"])
        assert _derived_count(connection) == 1
        with pytest.raises(SubstrateIdempotencyConflict):
            service.project_target_compatible_zero_member_motif(
                MigrationRuntimeZeroMemberMotifProjectionRequest(
                    **{**facts["request"].__dict__, "runtime_motif_id": "different"}
                )
            )
        source_payload = dict(facts["raw"])
        source_payload["strength"] = 0.11
        facts["motif_path"].write_text(
            json.dumps({"motifs": {"motif-b4c": source_payload}}), encoding="utf-8",
        )
        with pytest.raises(SubstrateEvidenceIntegrityMismatch):
            service.project_target_compatible_zero_member_motif(facts["request"])
        assert _derived_count(connection) == 1
        assert recovered.motif_object_id == NativeMotifService(connection).resolve_motif_alias(
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            runtime_motif_id="motif-b4c",
        )
    finally:
        qualified.close()


def test_b4c_refuses_changed_zero_member_source_snapshot_without_partial_projection(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]
        result = NativeMigrationRuntimeZeroMemberMotifProjectionService(connection).project_target_compatible_zero_member_motif(facts["request"])
        changed = dict(facts["raw"])
        changed["members"] = [7]
        facts["motif_path"].write_text(json.dumps({"motifs": {"motif-b4c": changed}}), encoding="utf-8")
        with pytest.raises(SubstrateEvidenceIntegrityMismatch):
            NativeMigrationRuntimeZeroMemberMotifProjectionService(connection).project_target_compatible_zero_member_motif(facts["request"])
        assert _derived_count(connection) == 1
        assert NativeMotifService(connection).resolve_motif_alias(
            motif_alias_namespace_id=facts["plan"].motif_alias_namespace_id,
            runtime_motif_id="motif-b4c",
        ) == result.motif_object_id
    finally:
        qualified.close()


@pytest.mark.parametrize(
    "workspace_lane",
    (
        ("wrong-provider", _TARGET_MODEL, _TARGET_DIMENSION),
        (_TARGET_PROVIDER, "wrong-model", _TARGET_DIMENSION),
        ("hash", "hash-space", _TARGET_DIMENSION),
        ("unknown", "unknown", _TARGET_DIMENSION),
    ),
)
def test_b4c_refuses_non_target_or_unknown_same_dimension_geometry_without_writes(tmp_path: Path, workspace_lane):
    qualified, facts = _context(tmp_path, workspace_lane=workspace_lane)
    try:
        connection = facts["connection"]
        before = (_derived_count(connection), connection.execute("SELECT count(*) FROM relationships").fetchone()[0])
        with pytest.raises(MigrationRuntimeZeroMemberMotifProjectionRefused, match="B4C_TARGET_GEOMETRY_LANE_UNQUALIFIED"):
            NativeMigrationRuntimeZeroMemberMotifProjectionService(connection).project_target_compatible_zero_member_motif(facts["request"])
        assert (_derived_count(connection), connection.execute("SELECT count(*) FROM relationships").fetchone()[0]) == before
    finally:
        qualified.close()


@pytest.mark.parametrize("kwargs", ({"include_workspace_meta": False}, {"malformed_workspace_meta": True}))
def test_b4c_refuses_missing_target_identity_proof_without_writes(tmp_path: Path, kwargs):
    qualified, facts = _context(tmp_path, **kwargs)
    try:
        assert _derived_count(facts["connection"]) == 0
        with pytest.raises(MigrationRuntimeZeroMemberMotifProjectionRefused, match="B4C_TARGET_IDENTITY_UNQUALIFIED"):
            NativeMigrationRuntimeZeroMemberMotifProjectionService(facts["connection"]).project_target_compatible_zero_member_motif(facts["request"])
        assert _derived_count(facts["connection"]) == 0
    finally:
        qualified.close()


@pytest.mark.parametrize("posture", ("active-core", "native-active-deployment"))
def test_b4c_requires_staging_legacy_active_migration_posture(tmp_path: Path, posture: str):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]
        if posture == "active-core":
            connection.execute("UPDATE core_metadata SET core_role='ACTIVE_CORE'")
            expected = "B4C_CORE_ROLE_NOT_STAGING"
        else:
            core_id = connection.execute("SELECT core_id FROM core_metadata").fetchone()[0]
            connection.execute(
                "UPDATE deployment_metadata SET deployment_state='NATIVE_ACTIVE',referenced_core_id=?",
                (core_id,),
            )
            expected = "B4C_DEPLOYMENT_NOT_LEGACY_ACTIVE"
        with pytest.raises(MigrationRuntimeZeroMemberMotifProjectionRefused, match=expected):
            NativeMigrationRuntimeZeroMemberMotifProjectionService(connection).project_target_compatible_zero_member_motif(facts["request"])
        assert _derived_count(connection) == 0
    finally:
        qualified.close()


def test_reader_refuses_uncertified_or_corrupt_zero_member_motifs(tmp_path: Path):
    qualified, facts = _context(tmp_path)
    try:
        connection = facts["connection"]
        invalid = NativeObjectService(connection).create_object(
            idempotency_namespace_id=facts["idempotency"],
            idempotency_key="ordinary-empty-corrupt",
            state=ObjectState(
                facts["plan"].motif_identity_namespace_id,
                facts["plan"].target_semantic_scope_id,
                "DERIVED_MOTIF",
                "EXISTS",
                "DERIVED",
                False,
                "DERIVED",
                "NOT_APPLICABLE",
                {
                    "motif_id": "ordinary-empty-corrupt",
                    "domain_id": "reflection",
                    "label": "corrupt",
                    "centroid": [1.0] + [0.0] * (_TARGET_DIMENSION - 1),
                    "strength": 0.5,
                    "stability_score": 0.5,
                    "contributing_agents": ["aria"],
                    "created_ts": 1,
                    "last_active_ts": 1,
                },
                "JSON",
            ),
        )
        connection.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (native_id_to_bytes(facts["plan"].motif_alias_namespace_id), "MOTIF_ID", "ordinary-empty-corrupt", native_id_to_bytes(invalid.object_id)),
        )
        reader = NativeMotifRuntimeReader(connection)
        with pytest.raises(SubstrateInvariantViolation, match="zero current memberships without certified"):
            reader.list_ordered_current_motif_members(invalid.object_id)

        result = NativeMigrationRuntimeZeroMemberMotifProjectionService(connection).project_target_compatible_zero_member_motif(facts["request"])
        connection.execute(
            "DELETE FROM object_revision_effects WHERE transition_id=?",
            (native_id_to_bytes(result.transition_id),),
        )
        with pytest.raises(SubstrateInvariantViolation, match="zero-member migration baseline motif effect"):
            reader.list_ordered_current_motif_members(result.motif_object_id)
    finally:
        qualified.close()


def test_b4a_and_b4b_empty_member_contracts_remain_refused(tmp_path: Path):
    qualified, facts = _context(tmp_path, include_extra=False)
    try:
        b4a_request = MigrationRuntimeMotifProjectionRequest(
            **facts["request"].__dict__
        )
        with pytest.raises(MigrationRuntimeMotifProjectionRefused, match="B4A_LEGACY_MEMBER_ORDER_UNRESOLVED"):
            NativeMigrationRuntimeMotifProjectionService(facts["connection"]).project_lane_preserving_legacy_motif(b4a_request)
        b4b_request = MigrationRuntimeMotifRegeometryProjectionRequest(
            **{**facts["request"].__dict__, "target_lane": _lane("new-provider", "new-model", 3)}
        )
        with pytest.raises(MigrationRuntimeMotifRegeometryProjectionRefused, match="B4B_MEMBER_ORDER_UNRESOLVED"):
            NativeMigrationRuntimeMotifRegeometryProjectionService(facts["connection"]).project_target_lane_regeometry(b4b_request)
        assert _derived_count(facts["connection"]) == 0
    finally:
        qualified.close()
