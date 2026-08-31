"""Read-only whole-workspace native runtime readiness for Phase 7G5B5.

This is deliberately an observation and composition boundary.  It reuses B1
for admission-to-runtime classification, the A3B readers for actual current
facts, and the already-qualified inert A3D constructors.  It cannot migrate,
activate, route, generate an embedding, write a deployment state, or persist
an approval marker.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..compat_embedding_reader import NativeCompatEmbeddingReader
from ..errors import SubstrateConfigurationError, SubstrateInvariantViolation
from ..fabric_native_routing import (
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from ..ids import native_id_to_bytes
from ..motif_runtime_reader import NativeMotifRuntimeReader
from ..native_post_write_runtime import (
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    prepare_native_fabric_post_write_adapter,
)
from ..runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
    validate_fabric_embedder,
)
from ..schema import open_schema
from .rehearsal import _verify_whole_core
from .runtime_readiness import (
    EIDSideStoreReadiness,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeScopePlan,
    MotifRuntimeReadiness,
    NativeMigrationRuntimeReadinessPreflight,
    ObjectRuntimeReadiness,
    SideStoreDisposition,
    SideStoreReadinessItem,
    _scope_plan_digest,
)


_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
_LEGACY_MOTIF_OBJECT_KIND = "LEGACY_DERIVED_MOTIF"
_MIGRATION_B3A_KEY = "B3A_CAPTURE_BOOTSTRAP:PENDING:"
_MIGRATION_B3B_KEY = "B3B_REEMBED_BOOTSTRAP:PENDING:"
_B4A = "MIGRATION_RUNTIME_MOTIF_PROJECTION"
_B4B = "MIGRATION_RUNTIME_MOTIF_REGEOMETRY_PROJECTION"


class WorkspaceNativeReadinessVerdict(StrEnum):
    NOT_RUNTIME_READY = "NOT_RUNTIME_READY"
    CORE_STAGING_RUNTIME_READY = "CORE_STAGING_RUNTIME_READY"
    CORE_READY_PRODUCTION_PARITY_INCOMPLETE = "CORE_READY_PRODUCTION_PARITY_INCOMPLETE"
    PRODUCTION_PARITY_READY_DEPLOYMENT_UNQUALIFIED = "PRODUCTION_PARITY_READY_DEPLOYMENT_UNQUALIFIED"


class WorkspaceReadinessBlockerClass(StrEnum):
    MIGRATION_MEMORY_BLOCKER = "MIGRATION_MEMORY_BLOCKER"
    MIGRATION_MOTIF_BLOCKER = "MIGRATION_MOTIF_BLOCKER"
    RUNTIME_SCOPE_BLOCKER = "RUNTIME_SCOPE_BLOCKER"
    RUNTIME_BINDING_BLOCKER = "RUNTIME_BINDING_BLOCKER"
    A3D_CAPABILITY_BLOCKER = "A3D_CAPABILITY_BLOCKER"
    CONDITIONAL_FEATURE_PARITY_BLOCKER = "CONDITIONAL_FEATURE_PARITY_BLOCKER"
    OPERATIONAL_PARITY_BLOCKER = "OPERATIONAL_PARITY_BLOCKER"
    SIDE_STORE_COMPATIBILITY_BLOCKER = "SIDE_STORE_COMPATIBILITY_BLOCKER"
    DEPLOYMENT_ADMINISTRATION_BLOCKER = "DEPLOYMENT_ADMINISTRATION_BLOCKER"
    AUTHORITY_BLOCKER = "AUTHORITY_BLOCKER"


class MemoryNormalizationLineage(StrEnum):
    B2_B3A = "B2_B3A"
    B2_B3B = "B2_B3B"
    NATIVE_READY_WITHOUT_MIGRATION = "NATIVE_READY_WITHOUT_MIGRATION"
    NOT_RUNTIME_READY = "NOT_RUNTIME_READY"


class MotifProjectionLineage(StrEnum):
    B4A = "B4A"
    B4B = "B4B"
    NOT_RUNTIME_READY = "NOT_RUNTIME_READY"


@dataclass(frozen=True)
class WorkspaceNativeFeaturePosture:
    """Explicit requested behavior; no feature is inferred from code presence."""

    character_enabled: bool
    character_gravity_effective: bool
    compression_enabled: bool
    deep_memory_required: bool
    motif_auto_merge_enabled: bool
    motif_suggestions_required: bool
    checkpoint_required: bool
    trajectory_persistence_required: bool
    bridge_suggestions_required: bool

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a boolean")

    @classmethod
    def a3d10_core_staging(cls) -> "WorkspaceNativeFeaturePosture":
        return cls(False, False, False, False, False, False, False, False, False)

    def intent(self) -> dict[str, bool]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    def is_a3d10_core_staging(self) -> bool:
        return self == self.a3d10_core_staging()


@dataclass(frozen=True)
class WorkspaceNativeEmbedderIdentity:
    """A deliberately inert identity witness accepted by ``validate_fabric_embedder``."""

    provider: str
    model: str
    dim: int

    def __post_init__(self) -> None:
        if not isinstance(self.provider, str) or not self.provider:
            raise ValueError("provider must be non-empty text")
        if not isinstance(self.model, str) or not self.model:
            raise ValueError("model must be non-empty text")
        if not isinstance(self.dim, int) or isinstance(self.dim, bool) or self.dim < 1:
            raise ValueError("dim must be a positive integer")


@dataclass(frozen=True)
class RetainedSideStoreEIDReference:
    """A caller-observed retained side-store EID, always namespaced explicitly."""

    side_store: str
    legacy_source_namespace_id: UUID | None
    eid: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.side_store, str) or not self.side_store:
            raise ValueError("side_store must be non-empty text")
        if self.legacy_source_namespace_id is not None and not isinstance(
            self.legacy_source_namespace_id, UUID
        ):
            raise ValueError("legacy_source_namespace_id must be UUID or None")
        if self.eid is not None and (
            not isinstance(self.eid, int) or isinstance(self.eid, bool) or self.eid < 0
        ):
            raise ValueError("eid must be a non-negative integer or None")


@dataclass(frozen=True)
class WorkspaceNativeRuntimeReadinessRequest:
    """Immutable, caller-owned B5 qualification inputs.

    ``observed_file_roots`` are explicit observation targets only.  Their
    contents are never used to discover migration facts or to supply defaults.
    ``staging_feature_posture`` answers the controlled experiment question;
    ``production_feature_posture`` independently makes the full-cutover gaps
    explicit.
    """

    legacy_snapshot_id: UUID
    expected_native_core_id: UUID
    native_core_database_path: str | Path
    scope_plans: tuple[MigrationRuntimeScopePlan, ...]
    target_lane: NativeRepresentationLane
    expected_workspace_ids: tuple[str, ...]
    staging_feature_posture: WorkspaceNativeFeaturePosture
    production_feature_posture: WorkspaceNativeFeaturePosture
    qualification_embedder_identity: WorkspaceNativeEmbedderIdentity
    post_write_configuration: NativePostWriteQualificationConfiguration
    retained_side_store_eid_references: tuple[RetainedSideStoreEIDReference, ...] = ()
    observed_file_roots: tuple[str | Path, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.legacy_snapshot_id, UUID):
            raise ValueError("legacy_snapshot_id must be a UUID")
        if not isinstance(self.expected_native_core_id, UUID):
            raise ValueError("expected_native_core_id must be a UUID")
        if not isinstance(self.native_core_database_path, (str, Path)) or not str(self.native_core_database_path):
            raise ValueError("native_core_database_path must be explicit")
        if not isinstance(self.scope_plans, tuple) or not self.scope_plans or any(
            not isinstance(item, MigrationRuntimeScopePlan) for item in self.scope_plans
        ):
            raise ValueError("scope_plans must be a non-empty tuple of MigrationRuntimeScopePlan")
        if not isinstance(self.target_lane, NativeRepresentationLane):
            raise ValueError("target_lane must be NativeRepresentationLane")
        if not isinstance(self.expected_workspace_ids, tuple) or not self.expected_workspace_ids or any(
            not isinstance(value, str) or not value for value in self.expected_workspace_ids
        ):
            raise ValueError("expected_workspace_ids must be a non-empty tuple of text")
        if len(set(self.expected_workspace_ids)) != len(self.expected_workspace_ids):
            raise ValueError("expected_workspace_ids must be unique")
        if not isinstance(self.staging_feature_posture, WorkspaceNativeFeaturePosture):
            raise ValueError("staging_feature_posture must be typed")
        if not isinstance(self.production_feature_posture, WorkspaceNativeFeaturePosture):
            raise ValueError("production_feature_posture must be typed")
        if not isinstance(self.qualification_embedder_identity, WorkspaceNativeEmbedderIdentity):
            raise ValueError("qualification_embedder_identity must be typed")
        if not isinstance(self.post_write_configuration, NativePostWriteQualificationConfiguration):
            raise ValueError("post_write_configuration must be an explicit A3D10 configuration")
        if not isinstance(self.retained_side_store_eid_references, tuple) or any(
            not isinstance(item, RetainedSideStoreEIDReference)
            for item in self.retained_side_store_eid_references
        ):
            raise ValueError("retained_side_store_eid_references must be typed")
        if not isinstance(self.observed_file_roots, tuple) or any(
            not isinstance(item, (str, Path)) or not str(item) for item in self.observed_file_roots
        ):
            raise ValueError("observed_file_roots must contain explicit paths")


@dataclass(frozen=True)
class WorkspaceMemoryReadinessItem:
    object_id: UUID
    eid: int | None
    readiness: ObjectRuntimeReadiness
    lineage: MemoryNormalizationLineage
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class WorkspaceMotifReadinessItem:
    source_motif_object_id: UUID
    runtime_motif_id: str | None
    readiness: MotifRuntimeReadiness
    lineage: MotifProjectionLineage
    target_motif_object_id: UUID | None
    member_count: int
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class WorkspaceSideStoreReadinessItem:
    side_store: str
    owner: str
    disposition: SideStoreDisposition
    eid_readiness: EIDSideStoreReadiness
    required_for_staging_profile: bool
    migration_required: bool
    reference_count: int
    compatible: bool
    reason: str


@dataclass(frozen=True)
class WorkspaceNativeRuntimeReadinessReport:
    legacy_snapshot_id: UUID
    native_core_id: UUID
    schema_version: tuple[int, int]
    scope_plan_digest: str
    target_lane: NativeRepresentationLane
    staging_feature_posture_digest: str
    production_feature_posture_digest: str
    memory_items: tuple[WorkspaceMemoryReadinessItem, ...]
    motif_items: tuple[WorkspaceMotifReadinessItem, ...]
    side_stores: tuple[WorkspaceSideStoreReadinessItem, ...]
    memory_readiness_counts: tuple[tuple[str, int], ...]
    motif_readiness_counts: tuple[tuple[str, int], ...]
    b3a_ready_memory_count: int
    b3b_ready_memory_count: int
    native_ready_without_migration_count: int
    b4a_ready_motif_count: int
    b4b_ready_motif_count: int
    motif_unresolved_count: int
    motif_quarantined_count: int
    core_deployment_ready: bool
    workspace_scope_ready: bool
    memory_closure_ready: bool
    motif_closure_ready: bool
    member_reference_closure_ready: bool
    runtime_binding_constructible: bool
    routing_capability_constructible: bool
    post_write_adapter_constructible: bool
    a3d_binding_reason: str | None
    a3d_capability_reason: str | None
    a3d_post_write_reason: str | None
    staging_profile_accepted: bool
    controlled_native_staging_experiment_ready: bool
    core_staging_runtime_ready: bool
    full_production_behavior_parity_ready: bool
    production_native_route_ready: bool
    production_cutover_ready: bool
    verdict: WorkspaceNativeReadinessVerdict
    blockers: tuple[tuple[WorkspaceReadinessBlockerClass, str], ...]
    conditional_feature_blockers: tuple[str, ...]
    operational_parity_blockers: tuple[str, ...]
    deployment_blockers: tuple[str, ...]
    side_store_retention_ready: bool
    migration_object_active_authorization_count: int
    migration_relationship_active_authorization_count: int
    migration_active_authorization_count: int
    legacy_evidence_retained: bool
    invariant_verification_passed: bool
    report_digest: str
    durable_effect_count: int
    file_mutation_count: int
    embedder_call_count: int
    authority_expansion_count: int
    observed_core_fingerprint: tuple[tuple[str, int, str], ...]


class NativeWorkspaceRuntimeReadiness:
    """B5 read-only whole-workspace qualification service."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("B5 requires an already-open SQLite connection")
        self._connection = connection
        self._metadata = open_schema(connection, writable=False)

    def run(self, request: WorkspaceNativeRuntimeReadinessRequest) -> WorkspaceNativeRuntimeReadinessReport:
        if not isinstance(request, WorkspaceNativeRuntimeReadinessRequest):
            raise ValueError("request must be WorkspaceNativeRuntimeReadinessRequest")
        before = _whole_core_fingerprint(self._connection)
        files_before = _file_fingerprint(request.observed_file_roots)
        total_changes_before = self._connection.total_changes
        blockers: list[tuple[WorkspaceReadinessBlockerClass, str]] = []

        b1 = NativeMigrationRuntimeReadinessPreflight(self._connection).run(
            MigrationRuntimeReadinessRequest(
                request.legacy_snapshot_id,
                request.expected_native_core_id,
                request.scope_plans,
                request.target_lane,
            )
        )
        snapshot_plans = tuple(
            plan for plan in request.scope_plans
            if b1.legacy_source_namespace_id is not None
            and plan.legacy_source_namespace_id == b1.legacy_source_namespace_id
        )
        workspace_scope_ready = True
        if len(snapshot_plans) != len(request.scope_plans):
            workspace_scope_ready = False
            blockers.append((WorkspaceReadinessBlockerClass.RUNTIME_SCOPE_BLOCKER, "SCOPE_PLAN_SOURCE_NAMESPACE_MISMATCH"))
        if {plan.workspace_id for plan in request.scope_plans} != set(request.expected_workspace_ids):
            workspace_scope_ready = False
            blockers.append((WorkspaceReadinessBlockerClass.RUNTIME_SCOPE_BLOCKER, "EXPECTED_WORKSPACE_IDS_MISMATCH"))
        if not b1.deploy_gate_ready:
            blockers.extend(
                (WorkspaceReadinessBlockerClass.DEPLOYMENT_ADMINISTRATION_BLOCKER, item.value)
                for item in b1.core_readiness
            )

        invariant_ok = True
        try:
            _verify_whole_core(self._connection)
        except SubstrateInvariantViolation as exc:
            invariant_ok = False
            blockers.append((WorkspaceReadinessBlockerClass.AUTHORITY_BLOCKER, f"WHOLE_CORE_INVARIANT:{exc}"))

        memory_items = self._memory_items(b1, request, blockers)
        motif_items, member_closure = self._motif_items(b1, request, memory_items, blockers)
        side_stores = self._side_store_items(b1.side_stores, request, blockers)
        object_auth, relationship_auth = _migration_authorization_counts(self._connection)
        if object_auth or relationship_auth:
            blockers.append((WorkspaceReadinessBlockerClass.AUTHORITY_BLOCKER, "MIGRATION_ACTIVE_AUTHORIZATION_PRESENT"))
        evidence_retained = _legacy_evidence_retained(self._connection, request.legacy_snapshot_id)
        if not evidence_retained:
            blockers.append((WorkspaceReadinessBlockerClass.AUTHORITY_BLOCKER, "LEGACY_EVIDENCE_RETENTION_FAILED"))

        binding, capability, binding_reason, capability_reason = self._construct_a3d(
            request, snapshot_plans
        )
        if binding is None:
            blockers.append((WorkspaceReadinessBlockerClass.RUNTIME_BINDING_BLOCKER, binding_reason or "A3D_BINDING_REFUSED"))
        elif capability is None:
            blockers.append((WorkspaceReadinessBlockerClass.A3D_CAPABILITY_BLOCKER, capability_reason or "A3D_CAPABILITY_REFUSED"))
        adapter_reason: str | None = None
        adapter = None
        if capability is not None:
            try:
                self._validate_post_write_configuration(request, capability.routing_scopes)
                adapter = prepare_native_fabric_post_write_adapter(
                    capability=capability, configuration=request.post_write_configuration
                )
            except (SubstrateConfigurationError, ValueError) as exc:
                adapter_reason = str(exc)
                blockers.append((WorkspaceReadinessBlockerClass.A3D_CAPABILITY_BLOCKER, f"A3D_POST_WRITE:{exc}"))

        staging_profile_accepted = (
            request.staging_feature_posture.is_a3d10_core_staging()
            and request.post_write_configuration.profile == NativePostWriteQualificationProfile.core_staging()
            and _configuration_matches_staging_posture(request.post_write_configuration)
        )
        if not staging_profile_accepted:
            blockers.append((WorkspaceReadinessBlockerClass.A3D_CAPABILITY_BLOCKER, "A3D10_STAGING_FEATURE_POSTURE_MISMATCH"))
        conditional, operational = _feature_blockers(request.production_feature_posture)
        blockers.extend((WorkspaceReadinessBlockerClass.CONDITIONAL_FEATURE_PARITY_BLOCKER, item) for item in conditional)
        blockers.extend((WorkspaceReadinessBlockerClass.OPERATIONAL_PARITY_BLOCKER, item) for item in operational)

        memory_closure = bool(memory_items) and all(
            item.readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS and not item.reason_codes
            for item in memory_items
        )
        motif_closure = bool(motif_items) and all(
            item.readiness is MotifRuntimeReadiness.RUNTIME_READY_AS_IS for item in motif_items
        )
        if not memory_closure:
            blockers.append((WorkspaceReadinessBlockerClass.MIGRATION_MEMORY_BLOCKER, "WHOLE_WORKSPACE_MEMORY_CLOSURE_INCOMPLETE"))
        if not motif_closure:
            blockers.append((WorkspaceReadinessBlockerClass.MIGRATION_MOTIF_BLOCKER, "WHOLE_WORKSPACE_MOTIF_CLOSURE_INCOMPLETE"))
        if not member_closure:
            blockers.append((WorkspaceReadinessBlockerClass.MIGRATION_MOTIF_BLOCKER, "WHOLE_WORKSPACE_MEMBER_REFERENCE_CLOSURE_INCOMPLETE"))
        side_compatible = all(item.compatible for item in side_stores)
        core_ready = all((
            b1.deploy_gate_ready,
            workspace_scope_ready,
            invariant_ok,
            memory_closure,
            motif_closure,
            member_closure,
            side_compatible,
            object_auth == 0,
            relationship_auth == 0,
            evidence_retained,
            binding is not None,
            capability is not None,
            adapter is not None,
            staging_profile_accepted,
        ))
        controlled = core_ready
        full_parity = core_ready and not conditional and not operational
        # B5 does not add the selector, deployment-state writer, or cutover
        # protocol.  This is a permanent NO in this phase, even if callers ask
        # for no optional behaviors.
        production_route_ready = False
        production_cutover_ready = False
        deployment_blockers = (
            "PRODUCTION_NATIVE_ROUTE_NOT_WIRED",
            "DEPLOYMENT_STATE_TRANSITION_UNQUALIFIED",
            "CUTOVER_AND_ROLLBACK_REHEARSAL_UNQUALIFIED",
        )
        blockers.extend(
            (WorkspaceReadinessBlockerClass.DEPLOYMENT_ADMINISTRATION_BLOCKER, item)
            for item in deployment_blockers
        )
        if not core_ready:
            verdict = WorkspaceNativeReadinessVerdict.NOT_RUNTIME_READY
        elif not full_parity:
            verdict = WorkspaceNativeReadinessVerdict.CORE_READY_PRODUCTION_PARITY_INCOMPLETE
        else:
            verdict = WorkspaceNativeReadinessVerdict.PRODUCTION_PARITY_READY_DEPLOYMENT_UNQUALIFIED

        after = _whole_core_fingerprint(self._connection)
        files_after = _file_fingerprint(request.observed_file_roots)
        if before != after or total_changes_before != self._connection.total_changes:
            raise SubstrateInvariantViolation("B5 read-only qualification changed durable native state")
        if files_before != files_after:
            raise SubstrateInvariantViolation("B5 read-only qualification changed an observed external file")
        report_values = {
            "core_id": str(UUID(bytes=self._metadata.core_id)),
            "schema": [self._metadata.schema_major, self._metadata.schema_minor],
            "snapshot_id": str(request.legacy_snapshot_id),
            "scope_plan_digest": _scope_plan_digest(request.scope_plans),
            "target_lane": _lane_intent(request.target_lane),
            "staging_feature_posture": request.staging_feature_posture.intent(),
            "production_feature_posture": request.production_feature_posture.intent(),
            "memory": [(str(item.object_id), item.readiness.value, item.lineage.value) for item in memory_items],
            "motif": [(str(item.source_motif_object_id), item.readiness.value, item.lineage.value) for item in motif_items],
            "side_stores": [(item.side_store, item.compatible, item.reference_count) for item in side_stores],
        }
        return WorkspaceNativeRuntimeReadinessReport(
            legacy_snapshot_id=request.legacy_snapshot_id,
            native_core_id=UUID(bytes=self._metadata.core_id),
            schema_version=(self._metadata.schema_major, self._metadata.schema_minor),
            scope_plan_digest=_scope_plan_digest(request.scope_plans),
            target_lane=request.target_lane,
            staging_feature_posture_digest=_digest(request.staging_feature_posture.intent()),
            production_feature_posture_digest=_digest(request.production_feature_posture.intent()),
            memory_items=memory_items,
            motif_items=motif_items,
            side_stores=side_stores,
            memory_readiness_counts=_counts(item.readiness.value for item in memory_items),
            motif_readiness_counts=_counts(item.readiness.value for item in motif_items),
            b3a_ready_memory_count=sum(item.lineage is MemoryNormalizationLineage.B2_B3A for item in memory_items),
            b3b_ready_memory_count=sum(item.lineage is MemoryNormalizationLineage.B2_B3B for item in memory_items),
            native_ready_without_migration_count=sum(item.lineage is MemoryNormalizationLineage.NATIVE_READY_WITHOUT_MIGRATION for item in memory_items),
            b4a_ready_motif_count=sum(item.lineage is MotifProjectionLineage.B4A for item in motif_items),
            b4b_ready_motif_count=sum(item.lineage is MotifProjectionLineage.B4B for item in motif_items),
            motif_unresolved_count=sum(item.readiness is not MotifRuntimeReadiness.RUNTIME_READY_AS_IS for item in motif_items),
            motif_quarantined_count=sum(item.readiness is MotifRuntimeReadiness.QUARANTINED for item in motif_items),
            core_deployment_ready=b1.deploy_gate_ready,
            workspace_scope_ready=workspace_scope_ready,
            memory_closure_ready=memory_closure,
            motif_closure_ready=motif_closure,
            member_reference_closure_ready=member_closure,
            runtime_binding_constructible=binding is not None,
            routing_capability_constructible=capability is not None,
            post_write_adapter_constructible=adapter is not None,
            a3d_binding_reason=binding_reason,
            a3d_capability_reason=capability_reason,
            a3d_post_write_reason=adapter_reason,
            staging_profile_accepted=staging_profile_accepted,
            controlled_native_staging_experiment_ready=controlled,
            core_staging_runtime_ready=core_ready,
            full_production_behavior_parity_ready=full_parity,
            production_native_route_ready=production_route_ready,
            production_cutover_ready=production_cutover_ready,
            verdict=verdict,
            blockers=tuple(sorted(set(blockers), key=lambda item: (item[0].value, item[1]))),
            conditional_feature_blockers=conditional,
            operational_parity_blockers=operational,
            deployment_blockers=tuple(sorted(set(deployment_blockers) | {item.value for item in b1.core_readiness if item.value != "QUALIFIED_STAGING_LEGACY_ACTIVE"})),
            side_store_retention_ready=side_compatible,
            migration_object_active_authorization_count=object_auth,
            migration_relationship_active_authorization_count=relationship_auth,
            migration_active_authorization_count=object_auth + relationship_auth,
            legacy_evidence_retained=evidence_retained,
            invariant_verification_passed=invariant_ok,
            report_digest=_digest(report_values),
            durable_effect_count=0,
            file_mutation_count=0,
            embedder_call_count=0,
            authority_expansion_count=0,
            observed_core_fingerprint=after,
        )

    def _memory_items(
        self, b1: Any, request: WorkspaceNativeRuntimeReadinessRequest,
        blockers: list[tuple[WorkspaceReadinessBlockerClass, str]],
    ) -> tuple[WorkspaceMemoryReadinessItem, ...]:
        kinds = {
            UUID(bytes=row[0]): row[1]
            for row in self._connection.execute("SELECT object_id,object_kind FROM objects")
        }
        reader = NativeCompatEmbeddingReader(self._connection)
        result: list[WorkspaceMemoryReadinessItem] = []
        for item in b1.object_items:
            if kinds.get(item.object_id) != _MEMORY_OBJECT_KIND:
                continue
            reasons = list(item.reason_codes)
            if item.readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS:
                try:
                    witness = reader.read_current(item.object_id, expected_dimension=request.target_lane.dimension)
                    if witness is None or witness.source_revision_id != item.current_revision_id:
                        reasons.append("A3D_CURRENT_COMPAT_EMBEDDING_POSTCONDITION_FAILED")
                    elif not _representation_lane_matches(
                        self._connection, witness.representation_id, request.target_lane
                    ):
                        reasons.append("QUALIFIED_REPRESENTATION_TARGET_LANE_MISMATCH")
                except (SubstrateInvariantViolation, ValueError):
                    reasons.append("A3D_CURRENT_COMPAT_EMBEDDING_POSTCONDITION_FAILED")
            lineage = _memory_lineage(self._connection, item.qualified_representation_id)
            if reasons or item.readiness is not ObjectRuntimeReadiness.RUNTIME_READY_AS_IS:
                blockers.append((WorkspaceReadinessBlockerClass.MIGRATION_MEMORY_BLOCKER, f"MEMORY:{item.object_id}:{item.readiness.value}"))
            result.append(WorkspaceMemoryReadinessItem(
                item.object_id, item.eid,
                (
                    ObjectRuntimeReadiness.RUNTIME_READY_AS_IS
                    if not reasons and item.readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS
                    else ObjectRuntimeReadiness.QUARANTINED_OR_UNSUPPORTED
                ),
                lineage if not reasons else MemoryNormalizationLineage.NOT_RUNTIME_READY,
                tuple(sorted(set(reasons))),
            ))
        return tuple(sorted(result, key=lambda item: (item.eid is None, item.eid, str(item.object_id))))

    def _motif_items(
        self, b1: Any, request: WorkspaceNativeRuntimeReadinessRequest,
        memory_items: tuple[WorkspaceMemoryReadinessItem, ...],
        blockers: list[tuple[WorkspaceReadinessBlockerClass, str]],
    ) -> tuple[tuple[WorkspaceMotifReadinessItem, ...], bool]:
        ready_memory_ids = {
            item.object_id for item in memory_items
            if item.readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS
        }
        plans = {plan.target_semantic_scope_id: plan for plan in request.scope_plans}
        reader = NativeMotifRuntimeReader(self._connection)
        candidates = _motif_projection_candidates(self._connection, request.target_lane)
        result: list[WorkspaceMotifReadinessItem] = []
        member_closure = True
        for item in b1.motif_items:
            source_kind = self._connection.execute(
                "SELECT object_kind FROM objects WHERE object_id=?", (native_id_to_bytes(item.motif_object_id),)
            ).fetchone()
            if source_kind != (_LEGACY_MOTIF_OBJECT_KIND,):
                continue
            reasons = list(item.reason_codes)
            matches = tuple(
                candidate for candidate in candidates.get((item.motif_object_id, item.current_revision_id), ())
                if _candidate_matches_requested_plan(candidate[2], plans, item.runtime_motif_id)
            )
            if len(matches) > 1:
                reasons.append("WHOLE_WORKSPACE_MOTIF_PROJECTION_AMBIGUOUS")
            target_id: UUID | None = None
            lineage = MotifProjectionLineage.NOT_RUNTIME_READY
            if len(matches) == 1:
                target_id, kind, intent = matches[0]
                lineage = MotifProjectionLineage.B4A if kind == _B4A else MotifProjectionLineage.B4B
                plan = plans.get(UUID(str(intent.get("target_semantic_scope_id", ""))))
                if plan is None:
                    reasons.append("RUNTIME_SCOPE_PLAN_MISSING")
                else:
                    try:
                        runtime = [entry for entry in reader.list_runtime_motifs(
                            motif_alias_namespace_id=plan.motif_alias_namespace_id,
                            domain_id=plan.motif_domain_id or "",
                            semantic_scope_id=plan.target_semantic_scope_id,
                        ) if entry.motif_object_id == target_id]
                        if len(runtime) != 1 or runtime[0].read_model.runtime_motif_id != item.runtime_motif_id:
                            reasons.append("A3B_RUNTIME_MOTIF_READER_POSTCONDITION_FAILED")
                        else:
                            members = reader.list_ordered_current_motif_members(target_id)
                            if not members or len(members) != item.membership_count:
                                reasons.append("MOTIF_CURRENT_MEMBER_COUNT_MISMATCH")
                            for member in members:
                                if member.member_semantic_scope_id != plan.target_semantic_scope_id:
                                    reasons.append("MOTIF_MEMBER_WRONG_SCOPE")
                                    member_closure = False
                                if member.member_object_id not in ready_memory_ids:
                                    reasons.append("MOTIF_MEMBER_NOT_RUNTIME_READY")
                                    member_closure = False
                                if reader.read_current_compat_embedding(
                                    member.member_object_id, expected_dimension=request.target_lane.dimension
                                ) is None:
                                    reasons.append("MOTIF_MEMBER_REPRESENTATION_UNQUALIFIED")
                                    member_closure = False
                            reader.motif_radius(target_id, expected_dimension=request.target_lane.dimension)
                            reader.domain_centroid(
                                motif_alias_namespace_id=plan.motif_alias_namespace_id,
                                domain_id=plan.motif_domain_id or "",
                                dimension=request.target_lane.dimension,
                                semantic_scope_id=plan.target_semantic_scope_id,
                            )
                            reader.project_coherence_field_rows(
                                motif_alias_namespace_id=plan.motif_alias_namespace_id,
                                domain_id=plan.motif_domain_id or "",
                                expected_dimension=request.target_lane.dimension,
                                semantic_scope_id=plan.target_semantic_scope_id,
                            )
                    except (SubstrateInvariantViolation, ValueError):
                        reasons.append("A3B_RUNTIME_MOTIF_READER_POSTCONDITION_FAILED")
                        member_closure = False
            elif item.readiness is MotifRuntimeReadiness.RUNTIME_READY_AS_IS:
                reasons.append("MOTIF_PROJECTION_MAPPING_UNRESOLVED")
            readiness = item.readiness if not reasons else MotifRuntimeReadiness.QUARANTINED
            if readiness is not MotifRuntimeReadiness.RUNTIME_READY_AS_IS:
                blockers.append((WorkspaceReadinessBlockerClass.MIGRATION_MOTIF_BLOCKER, f"MOTIF:{item.motif_object_id}:{readiness.value}"))
            result.append(WorkspaceMotifReadinessItem(
                item.motif_object_id, item.runtime_motif_id, readiness,
                lineage if readiness is MotifRuntimeReadiness.RUNTIME_READY_AS_IS else MotifProjectionLineage.NOT_RUNTIME_READY,
                target_id, item.membership_count, tuple(sorted(set(reasons))),
            ))
        return tuple(sorted(result, key=lambda item: str(item.source_motif_object_id))), member_closure

    def _side_store_items(
        self, base: tuple[SideStoreReadinessItem, ...], request: WorkspaceNativeRuntimeReadinessRequest,
        blockers: list[tuple[WorkspaceReadinessBlockerClass, str]],
    ) -> tuple[WorkspaceSideStoreReadinessItem, ...]:
        result: list[WorkspaceSideStoreReadinessItem] = []
        for item in base:
            refs = tuple(ref for ref in request.retained_side_store_eid_references if ref.side_store == item.side_store)
            compatible = not (
                item.eid_readiness is not EIDSideStoreReadiness.NO_EID_REFERENCE and not refs
            )
            for ref in refs:
                if ref.legacy_source_namespace_id is None or ref.eid is None:
                    compatible = False
                    continue
                rows = self._connection.execute(
                    "SELECT object_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value=?",
                    (native_id_to_bytes(ref.legacy_source_namespace_id), str(ref.eid)),
                ).fetchall()
                if len(rows) != 1:
                    compatible = False
            if refs and item.eid_readiness is EIDSideStoreReadiness.NO_EID_REFERENCE:
                compatible = False
            if not compatible:
                code = (
                    f"SIDE_STORE_EID_OBSERVATION_REQUIRED:{item.side_store}"
                    if not refs else f"SIDE_STORE_EID_UNRESOLVED:{item.side_store}"
                )
                blockers.append((WorkspaceReadinessBlockerClass.SIDE_STORE_COMPATIBILITY_BLOCKER, code))
            result.append(WorkspaceSideStoreReadinessItem(
                side_store=item.side_store,
                owner=_side_store_owner(item.side_store),
                disposition=item.disposition,
                eid_readiness=item.eid_readiness,
                required_for_staging_profile=item.side_store in {
                    "conflicts", "anchors", "affect_history", "hivemind_collective", "identity_overlays", "proposals",
                },
                migration_required=False,
                reference_count=len(refs),
                compatible=compatible,
                reason=item.reason,
            ))
        return tuple(result)

    def _construct_a3d(
        self, request: WorkspaceNativeRuntimeReadinessRequest,
        plans: tuple[MigrationRuntimeScopePlan, ...],
    ) -> tuple[Any | None, Any | None, str | None, str | None]:
        if not plans:
            return None, None, "NO_SNAPSHOT_SCOPE_PLANS", None
        try:
            runtime_scopes = tuple(_runtime_scope(plan) for plan in plans)
            binding = prepare_native_memory_runtime_binding(
                connection=self._connection,
                core_database_path=request.native_core_database_path,
                expected_core_id=request.expected_native_core_id,
                scope_bindings=runtime_scopes,
                representation_lane=request.target_lane,
            )
            validate_fabric_embedder(binding, request.qualification_embedder_identity)
        except (SubstrateConfigurationError, ValueError) as exc:
            return None, None, str(exc), None
        try:
            routing_scopes = tuple(_routing_scope(plan) for plan in plans)
            capability = prepare_native_fabric_routing_capability(
                binding=binding,
                connection=self._connection,
                routing_scopes=routing_scopes,
                expected_core_id=request.expected_native_core_id,
            )
        except (SubstrateConfigurationError, ValueError) as exc:
            return binding, None, None, str(exc)
        return binding, capability, None, None

    @staticmethod
    def _validate_post_write_configuration(
        request: WorkspaceNativeRuntimeReadinessRequest, routing_scopes: tuple[NativeFabricRoutingScope, ...],
    ) -> None:
        configuration = request.post_write_configuration
        if configuration.profile != NativePostWriteQualificationProfile.core_staging():
            raise SubstrateConfigurationError("B5 requires the exact A3D10 core staging profile")
        if configuration.routing_scope not in routing_scopes:
            raise SubstrateConfigurationError("B5 post-write configuration claims no requested runtime scope")


def _runtime_scope(plan: MigrationRuntimeScopePlan) -> NativeMemoryRuntimeScope:
    return NativeMemoryRuntimeScope(
        workspace_id=plan.workspace_id,
        scope_kind=plan.scope_kind,
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id,
        agent_id=plan.agent_id,
        domain_id=plan.domain_id,
    )


def _routing_scope(plan: MigrationRuntimeScopePlan) -> NativeFabricRoutingScope:
    return NativeFabricRoutingScope(
        runtime_scope=_runtime_scope(plan),
        motif_alias_namespace_id=plan.motif_alias_namespace_id,
        motif_identity_namespace_id=plan.motif_identity_namespace_id,
        membership_identity_namespace_id=plan.membership_identity_namespace_id,
        idempotency_namespace_id=plan.idempotency_namespace_id,
    )


def _memory_lineage(connection: sqlite3.Connection, representation_id: UUID | None) -> MemoryNormalizationLineage:
    if representation_id is None:
        return MemoryNormalizationLineage.NOT_RUNTIME_READY
    rows = connection.execute(
        """SELECT operation.idempotency_key
             FROM operation_outputs output
             JOIN operations operation ON operation.operation_id=output.operation_id
            WHERE output.output_kind='REPRESENTATION' AND output.representation_id=?""",
        (native_id_to_bytes(representation_id),),
    ).fetchall()
    keys = {row[0] for row in rows}
    if any(key.startswith(_MIGRATION_B3A_KEY) for key in keys):
        return MemoryNormalizationLineage.B2_B3A
    if any(key.startswith(_MIGRATION_B3B_KEY) for key in keys):
        return MemoryNormalizationLineage.B2_B3B
    return MemoryNormalizationLineage.NATIVE_READY_WITHOUT_MIGRATION


def _representation_lane_matches(
    connection: sqlite3.Connection, representation_id: UUID, lane: NativeRepresentationLane,
) -> bool:
    """Read the immutable B3 pending-operation lane witness.

    The raw A3D representation identity intentionally does not store provider
    or model.  B3 records those caller-owned lane facts in its canonical
    administrative derivation.  B5 combines that immutable witness with the
    qualified reader result; it neither changes the reader contract nor adds a
    second representation selector.
    """
    rows = connection.execute(
        """SELECT operation.canonical_intent_json
             FROM operation_outputs output
             JOIN operations operation ON operation.operation_id=output.operation_id
            WHERE output.output_kind='REPRESENTATION'
              AND output.output_role='REPRESENTATION_PENDING'
              AND output.representation_id=?""",
        (native_id_to_bytes(representation_id),),
    ).fetchall()
    if len(rows) != 1:
        return False
    try:
        administrative = json.loads(rows[0][0])["administrative_derivation"]
    except (TypeError, KeyError, json.JSONDecodeError):
        return False
    return administrative.get("target_lane") == {
        "provider": lane.provider,
        "model": lane.model,
        "dimension": lane.dimension,
        "representation_class": lane.representation_class,
        "generation": lane.generation,
        "derivation_contract_version": lane.derivation_contract_version,
        "encoding_id": lane.encoding_id,
        "dtype": lane.dtype,
    } if isinstance(administrative, dict) else False


def _motif_projection_candidates(
    connection: sqlite3.Connection, lane: NativeRepresentationLane,
) -> dict[tuple[UUID, UUID], tuple[tuple[UUID, str, dict[str, Any]], ...]]:
    expected_lane = _lane_intent(lane)
    rows = connection.execute(
        """SELECT output.object_id,transition.transition_kind,operation.canonical_intent_json
             FROM semantic_transitions transition
             JOIN operations operation ON operation.operation_id=transition.operation_id
             JOIN operation_outputs output ON output.operation_id=operation.operation_id
            WHERE transition.origin_kind='NATIVE'
              AND transition.transition_kind IN (?,?)
              AND operation.operation_kind=transition.transition_kind
              AND output.output_kind='OBJECT' AND output.output_ordinal=0""",
        (_B4A, _B4B),
    ).fetchall()
    values: dict[tuple[UUID, UUID], list[tuple[UUID, str, dict[str, Any]]]] = {}
    for target, kind, intent_text in rows:
        try:
            intent = json.loads(intent_text)
            source = UUID(str(intent["source_motif_object_id"]))
            revision = UUID(str(intent["source_motif_revision_id"]))
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            continue
        if intent.get("target_lane") != expected_lane:
            continue
        values.setdefault((source, revision), []).append((UUID(bytes=target), kind, intent))
    return {key: tuple(value) for key, value in values.items()}


def _candidate_matches_requested_plan(
    intent: dict[str, Any], plans: dict[UUID, MigrationRuntimeScopePlan], runtime_motif_id: str | None,
) -> bool:
    if runtime_motif_id is None or intent.get("runtime_motif_id") != runtime_motif_id:
        return False
    try:
        plan = plans[UUID(str(intent.get("target_semantic_scope_id")))]
    except (KeyError, TypeError, ValueError):
        return False
    return (
        intent.get("motif_alias_namespace_id") == str(plan.motif_alias_namespace_id)
        and intent.get("motif_identity_namespace_id") == str(plan.motif_identity_namespace_id)
        and intent.get("membership_identity_namespace_id") == str(plan.membership_identity_namespace_id)
    )


def _configuration_matches_staging_posture(configuration: NativePostWriteQualificationConfiguration) -> bool:
    return not any((
        configuration.motif_suggestion_maintenance_required,
        configuration.persistent_trajectory_evidence_required,
        configuration.checkpoint_snapshots_required,
        configuration.bridge_suggestions_required,
        configuration.deep_memory_required,
    ))


def _feature_blockers(posture: WorkspaceNativeFeaturePosture) -> tuple[tuple[str, ...], tuple[str, ...]]:
    conditional = tuple(name for name, required in (
        ("CHARACTER_PARITY", posture.character_enabled),
        ("CHARACTER_GRAVITY_PARITY", posture.character_gravity_effective),
        ("COMPRESSION_PARITY", posture.compression_enabled),
        ("DEEP_MEMORY_RUNTIME_PARITY", posture.deep_memory_required),
        ("MOTIF_AUTO_MERGE_PARITY", posture.motif_auto_merge_enabled),
    ) if required)
    operational = tuple(name for name, required in (
        ("MOTIF_SUGGESTION_MAINTENANCE_PARITY", posture.motif_suggestions_required),
        ("CHECKPOINT_PARITY", posture.checkpoint_required),
        ("PERSISTENT_TRAJECTORY_EVIDENCE_PARITY", posture.trajectory_persistence_required),
        ("BRIDGE_SUGGESTION_PARITY", posture.bridge_suggestions_required),
    ) if required)
    return conditional, operational


def _side_store_owner(name: str) -> str:
    return {
        "conflicts": "external conflict registry",
        "anchors": "external derived-memory side store",
        "affect_history": "external derived-memory side store",
        "hivemind_collective": "external collective/Hivemind owner",
        "character_store": "external CharacterStore",
        "bridges": "external BridgeRegistry",
        "checkpoints": "external checkpoint store",
        "trajectory_evidence": "external trajectory store",
        "deep_memory": "native evidence plus retained deep-memory store",
        "identity_overlays": "7F admitted primary identity facts",
        "proposals": "7F admitted primary proposal facts",
        "role_state": "external role owner",
    }.get(name, "retained external owner")


def _migration_authorization_counts(connection: sqlite3.Connection) -> tuple[int, int]:
    objects = connection.execute(
        """SELECT count(*) FROM object_revision_effects effect
             JOIN object_revisions revision ON revision.object_revision_id=effect.object_revision_id
             JOIN semantic_transitions transition ON transition.transition_id=effect.transition_id
            WHERE revision.authority_category='ACTIVE_AUTHORIZATION'
              AND transition.transition_kind LIKE 'MIGRATION_%'"""
    ).fetchone()[0]
    relationships = connection.execute(
        """SELECT count(*) FROM relationship_revision_effects effect
             JOIN relationship_revisions revision ON revision.relationship_revision_id=effect.relationship_revision_id
             JOIN semantic_transitions transition ON transition.transition_id=effect.transition_id
            WHERE revision.authority_category='ACTIVE_AUTHORIZATION'
              AND transition.transition_kind LIKE 'MIGRATION_%'"""
    ).fetchone()[0]
    return int(objects), int(relationships)


def _legacy_evidence_retained(connection: sqlite3.Connection, snapshot_id: UUID) -> bool:
    snapshot = native_id_to_bytes(snapshot_id)
    rows = connection.execute(
        """SELECT admission.admission_record_id
             FROM legacy_admission_records admission
             JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
            WHERE batch.legacy_snapshot_id=? AND admission.admission_status='ADMITTED'""",
        (snapshot,),
    ).fetchall()
    if not rows:
        return False
    for (record_id,) in rows:
        effect = connection.execute(
            "SELECT 1 FROM legacy_admission_effects WHERE admission_record_id=?", (record_id,)
        ).fetchone()
        if effect is None:
            return False
    # B2/B3/B4 may advance current pointers, but each imported R1, membership,
    # capture, and source alias must remain as immutable evidence.
    source_row = connection.execute(
        "SELECT legacy_source_namespace_id FROM legacy_snapshots WHERE legacy_snapshot_id=?", (snapshot,)
    ).fetchone()
    if source_row is None:
        return False
    source = source_row[0]
    missing_object_r1 = connection.execute(
        """SELECT 1 FROM objects object_row
             JOIN semantic_transitions transition ON transition.transition_id=object_row.creating_transition_id
             JOIN legacy_admission_effects effect ON effect.transition_id=transition.transition_id
             JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
             JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
            WHERE batch.legacy_snapshot_id=? AND admission.admission_status='ADMITTED'
              AND NOT EXISTS (
                    SELECT 1 FROM object_revisions revision
                     WHERE revision.object_id=object_row.object_id
                       AND revision.lineage_kind='LEGACY_PREDECESSOR_UNKNOWN'
              ) LIMIT 1""",
        (snapshot,),
    ).fetchone()
    missing_membership_r1 = connection.execute(
        """SELECT 1 FROM relationships relationship_row
             JOIN semantic_transitions transition ON transition.transition_id=relationship_row.creating_transition_id
             JOIN legacy_admission_effects effect ON effect.transition_id=transition.transition_id
             JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
             JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
            WHERE batch.legacy_snapshot_id=? AND admission.admission_status='ADMITTED'
              AND relationship_row.relationship_kind='MOTIF_MEMBERSHIP'
              AND NOT EXISTS (
                    SELECT 1 FROM relationship_revisions revision
                     WHERE revision.relationship_id=relationship_row.relationship_id
                       AND revision.lineage_kind='LEGACY_PREDECESSOR_UNKNOWN'
              ) LIMIT 1""",
        (snapshot,),
    ).fetchone()
    missing_core_alias = connection.execute(
        """SELECT 1 FROM objects object_row
             JOIN semantic_transitions transition ON transition.transition_id=object_row.creating_transition_id
             JOIN legacy_admission_effects effect ON effect.transition_id=transition.transition_id
             JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
             JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
            WHERE batch.legacy_snapshot_id=? AND admission.admission_status='ADMITTED'
              AND object_row.object_kind=? AND NOT EXISTS (
                    SELECT 1 FROM legacy_object_aliases alias
                     WHERE alias.legacy_source_namespace_id=? AND alias.alias_kind='EID'
                       AND alias.object_id=object_row.object_id
              ) LIMIT 1""",
        (snapshot, _MEMORY_OBJECT_KIND, source),
    ).fetchone()
    missing_motif_alias = connection.execute(
        """SELECT 1 FROM objects object_row
             JOIN semantic_transitions transition ON transition.transition_id=object_row.creating_transition_id
             JOIN legacy_admission_effects effect ON effect.transition_id=transition.transition_id
             JOIN legacy_admission_records admission ON admission.admission_record_id=effect.admission_record_id
             JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
            WHERE batch.legacy_snapshot_id=? AND admission.admission_status='ADMITTED'
              AND object_row.object_kind=? AND NOT EXISTS (
                    SELECT 1 FROM legacy_object_aliases alias
                     WHERE alias.legacy_source_namespace_id=? AND alias.alias_kind='MOTIF_ID'
                       AND alias.object_id=object_row.object_id
              ) LIMIT 1""",
        (snapshot, _LEGACY_MOTIF_OBJECT_KIND, source),
    ).fetchone()
    missing_capture = connection.execute(
        """SELECT 1 FROM representation_state_effects effect
             JOIN semantic_transitions transition ON transition.transition_id=effect.transition_id
             JOIN legacy_admission_effects admission_effect ON admission_effect.transition_id=transition.transition_id
             JOIN legacy_admission_records admission ON admission.admission_record_id=admission_effect.admission_record_id
             JOIN legacy_admission_batches batch ON batch.admission_batch_id=admission.admission_batch_id
             JOIN representations representation ON representation.representation_id=effect.representation_id
            WHERE batch.legacy_snapshot_id=? AND admission.admission_status='ADMITTED'
              AND transition.transition_kind='LEGACY_REPRESENTATION_ADMISSION'
              AND (representation.representation_class<>'LEGACY_EMBEDDING_CAPTURE'
                   OR NOT EXISTS (
                       SELECT 1 FROM object_revisions revision
                        WHERE revision.object_id=representation.source_object_id
                          AND revision.object_revision_id=representation.source_object_revision_id
                          AND revision.lineage_kind='LEGACY_PREDECESSOR_UNKNOWN'
                   )) LIMIT 1""",
        (snapshot,),
    ).fetchone()
    return not any((missing_object_r1, missing_membership_r1, missing_core_alias, missing_motif_alias, missing_capture))


def _whole_core_fingerprint(connection: sqlite3.Connection) -> tuple[tuple[str, int, str], ...]:
    tables = tuple(
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    )
    values: list[tuple[str, int, str]] = []
    for table in tables:
        quoted = '"' + table.replace('"', '""') + '"'
        digest = hashlib.sha256()
        count = 0
        for row in connection.execute(f"SELECT * FROM {quoted} ORDER BY rowid"):
            count += 1
            for value in row:
                if value is None:
                    digest.update(b"N")
                elif isinstance(value, bytes):
                    digest.update(b"B" + len(value).to_bytes(8, "big") + value)
                else:
                    encoded = str(value).encode("utf-8")
                    digest.update(b"T" + len(encoded).to_bytes(8, "big") + encoded)
        values.append((table, count, digest.hexdigest()))
    return tuple(values)


def _file_fingerprint(roots: tuple[str | Path, ...]) -> tuple[tuple[str, str], ...]:
    entries: list[tuple[str, str]] = []
    for raw in roots:
        root = Path(raw).resolve()
        if not root.exists():
            raise ValueError(f"observed file root does not exist: {root}")
        paths = (root,) if root.is_file() else tuple(sorted((item for item in root.rglob("*") if item.is_file()), key=str))
        for path in paths:
            entries.append((str(path), hashlib.sha256(path.read_bytes()).hexdigest()))
    return tuple(entries)


def _counts(values: Any) -> tuple[tuple[str, int], ...]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return tuple(sorted(result.items()))


def _lane_intent(lane: NativeRepresentationLane) -> list[object]:
    return [
        lane.provider, lane.model, lane.dimension, lane.representation_class,
        lane.generation, lane.derivation_contract_version, lane.encoding_id, lane.dtype,
    ]


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


__all__ = [
    "MemoryNormalizationLineage", "MotifProjectionLineage", "NativeWorkspaceRuntimeReadiness",
    "RetainedSideStoreEIDReference", "WorkspaceMemoryReadinessItem",
    "WorkspaceMotifReadinessItem", "WorkspaceNativeEmbedderIdentity",
    "WorkspaceNativeFeaturePosture", "WorkspaceNativeReadinessVerdict",
    "WorkspaceNativeRuntimeReadinessReport", "WorkspaceNativeRuntimeReadinessRequest",
    "WorkspaceReadinessBlockerClass", "WorkspaceSideStoreReadinessItem",
]
