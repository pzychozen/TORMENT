"""Declared-topology successor readiness for a Phase 9A root description.

This is deliberately a read-only composition boundary.  It adds the root
profile's explicit empty/topology policy around existing B1 facts, the native
motif reader, and A3D constructors.  It does not replace the historical B5
whole-workspace contract or create another migration/readiness fact engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
import sqlite3
from typing import Any
from uuid import UUID

from ..errors import (
    SubstrateConfigurationError,
    SubstrateEvidenceIntegrityMismatch,
    SubstrateInvariantViolation,
)
from ..motif_runtime_reader import NativeMotifRuntimeReader
from ..native_post_write_runtime import (
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    prepare_native_fabric_post_write_adapter,
)
from ..runtime_binding import NativeRepresentationLane
from .root_admission_description import (
    GeometryDerivedExternalStateDisposition,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    RootNativeProductionAdmissionDescription,
)
from .root_scope import RootScopeKey, RootScopeKind
from .runtime_readiness import (
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeReadinessReport,
    MigrationRuntimeScopePlan,
    MotifRuntimeReadiness,
    NativeMigrationRuntimeReadinessPreflight,
    ObjectRuntimeReadiness,
    read_core_runtime_readiness,
)
from .workspace_runtime_readiness import (
    MotifProjectionLineage,
    WorkspaceNativeEmbedderIdentity,
    _whole_core_fingerprint,
    construct_read_only_runtime_capability,
)


class GeneralizedReadinessReason(StrEnum):
    SOURCE_MANIFEST_DRIFT = "SOURCE_MANIFEST_DRIFT"
    SCOPE_INPUT_SET_MISMATCH = "SCOPE_INPUT_SET_MISMATCH"
    SCOPE_INPUT_PLAN_MISMATCH = "SCOPE_INPUT_PLAN_MISMATCH"
    TARGET_LANE_MISMATCH = "TARGET_LANE_MISMATCH"
    CORE_ID_MISMATCH = "CORE_ID_MISMATCH"
    DECLARED_MEMORY_GRAPH_HAS_NO_MIGRATED_MEMORY = "DECLARED_MEMORY_GRAPH_HAS_NO_MIGRATED_MEMORY"
    DECLARED_MEMORY_GRAPH_MEMORY_NOT_READY = "DECLARED_MEMORY_GRAPH_MEMORY_NOT_READY"
    DECLARED_EMPTY_SCOPE_HAS_MEMORY = "DECLARED_EMPTY_SCOPE_HAS_MEMORY"
    DECLARED_EMPTY_SCOPE_HAS_ACTIVE_REPRESENTATION = "DECLARED_EMPTY_SCOPE_HAS_ACTIVE_REPRESENTATION"
    DECLARED_MOTIF_SOURCE_HAS_NO_MOTIF = "DECLARED_MOTIF_SOURCE_HAS_NO_MOTIF"
    DECLARED_ZERO_MOTIFS_HAS_SOURCE_MOTIF = "DECLARED_ZERO_MOTIFS_HAS_SOURCE_MOTIF"
    DECLARED_ZERO_MOTIFS_HAS_RUNTIME_MOTIF = "DECLARED_ZERO_MOTIFS_HAS_RUNTIME_MOTIF"
    MOTIF_NOT_RUNTIME_READY = "MOTIF_NOT_RUNTIME_READY"
    B4C_ZERO_MEMBER_CERTIFICATION_MISSING = "B4C_ZERO_MEMBER_CERTIFICATION_MISSING"
    B4C_CURRENT_MEMBERS_NOT_ZERO = "B4C_CURRENT_MEMBERS_NOT_ZERO"
    MEMBER_BEARING_MOTIF_HAS_NO_CURRENT_MEMBERS = "MEMBER_BEARING_MOTIF_HAS_NO_CURRENT_MEMBERS"
    NO_MEMORY_WORKSPACE_HAS_MATERIALIZED_SCOPE = "NO_MEMORY_WORKSPACE_HAS_MATERIALIZED_SCOPE"
    A3D_BINDING_REFUSED = "A3D_BINDING_REFUSED"
    A3D_ROUTING_REFUSED = "A3D_ROUTING_REFUSED"
    A3D_POST_WRITE_CONFIGURATION_MISMATCH = "A3D_POST_WRITE_CONFIGURATION_MISMATCH"
    A3D_POST_WRITE_ADAPTER_REFUSED = "A3D_POST_WRITE_ADAPTER_REFUSED"


class GeneralizedTopologyReason(StrEnum):
    MEMORY_FACTS_REQUIRED = "MEMORY_FACTS_REQUIRED"
    ZERO_MEMORY_EXPECTED = "ZERO_MEMORY_EXPECTED"
    MOTIF_FACTS_REQUIRED = "MOTIF_FACTS_REQUIRED"
    ZERO_MOTIFS_EXPECTED = "ZERO_MOTIFS_EXPECTED"
    B4C_ZERO_MEMBERS_CERTIFIED = "B4C_ZERO_MEMBERS_CERTIFIED"
    NO_MATERIALIZED_SCOPES_EXPECTED = "NO_MATERIALIZED_SCOPES_EXPECTED"


@dataclass(frozen=True)
class GeneralizedScopeReadinessInput:
    """One B1 request explicitly bound to one declared root scope."""

    scope_key: RootScopeKey
    readiness_request: MigrationRuntimeReadinessRequest

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey):
            raise ValueError("scope_key must be a RootScopeKey")
        if not isinstance(self.readiness_request, MigrationRuntimeReadinessRequest):
            raise ValueError("readiness_request must be a MigrationRuntimeReadinessRequest")
        if len(self.readiness_request.scope_plans) != 1:
            raise ValueError("a generalized scope input requires exactly one scope plan")
        if not _plan_matches_scope(self.readiness_request.scope_plans[0], self.scope_key):
            raise ValueError("readiness request plan does not match its RootScopeKey")

    @property
    def scope_plan(self) -> MigrationRuntimeScopePlan:
        return self.readiness_request.scope_plans[0]


@dataclass(frozen=True)
class GeneralizedNativeRuntimeReadinessRequest:
    """Caller-owned, root-wide, read-only generalized readiness input."""

    description: RootNativeProductionAdmissionDescription
    data_root: str | Path
    native_core_database_path: str | Path
    expected_native_core_id: UUID
    scope_inputs: tuple[GeneralizedScopeReadinessInput, ...]
    qualification_embedder_identity: WorkspaceNativeEmbedderIdentity
    post_write_configurations: tuple[NativePostWriteQualificationConfiguration, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.description, RootNativeProductionAdmissionDescription):
            raise ValueError("description must be a RootNativeProductionAdmissionDescription")
        if not isinstance(self.data_root, (str, Path)) or not str(self.data_root).strip():
            raise ValueError("data_root must be explicit")
        if not isinstance(self.native_core_database_path, (str, Path)) or not str(self.native_core_database_path).strip():
            raise ValueError("native_core_database_path must be explicit")
        if not isinstance(self.expected_native_core_id, UUID):
            raise ValueError("expected_native_core_id must be a UUID")
        if not isinstance(self.scope_inputs, tuple) or any(
            not isinstance(item, GeneralizedScopeReadinessInput) for item in self.scope_inputs
        ):
            raise ValueError("scope_inputs must be typed")
        if len({item.scope_key for item in self.scope_inputs}) != len(self.scope_inputs):
            raise ValueError("scope_inputs must have unique RootScopeKey values")
        if not isinstance(self.qualification_embedder_identity, WorkspaceNativeEmbedderIdentity):
            raise ValueError("qualification_embedder_identity must be typed")
        if not isinstance(self.post_write_configurations, tuple) or any(
            not isinstance(item, NativePostWriteQualificationConfiguration)
            for item in self.post_write_configurations
        ):
            raise ValueError("post_write_configurations must be typed")


@dataclass(frozen=True)
class GeneralizedScopeReadinessItem:
    scope_key: RootScopeKey
    materialization_posture: MaterializedScopePosture
    memory_fact_count: int
    motif_fact_count: int
    memory_closure_ready: bool
    motif_closure_ready: bool
    member_reference_closure_ready: bool
    empty_topology_reason: GeneralizedTopologyReason | None
    motif_lineages: tuple[MotifProjectionLineage, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class GeneralizedWorkspaceReadinessItem:
    workspace_id: str
    materialized_scope_count: int
    topology_complete: bool
    no_memory_scope_expected: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class GeneralizedNativeRuntimeReadinessReport:
    root_description_digest: str
    source_manifest_digest: str
    source_manifest_valid: bool
    native_core_id: UUID
    target_lane: NativeRepresentationLane
    scope_items: tuple[GeneralizedScopeReadinessItem, ...]
    workspace_items: tuple[GeneralizedWorkspaceReadinessItem, ...]
    census_closure_ready: bool
    declared_topology_ready: bool
    a3d_binding_constructible: bool
    a3d_routing_constructible: bool
    a3d_post_write_constructible: bool
    generalized_staging_runtime_ready: bool
    activation_ready: bool
    geometry_derived_external_state_disposition: GeometryDerivedExternalStateDisposition
    reason_codes: tuple[str, ...]
    durable_effect_count: int
    authority_expansion_count: int
    observed_core_fingerprint: tuple[tuple[str, int, str], ...]


class NativeGeneralizedRuntimeReadiness:
    """Compose B1, B4 reader certification, Phase 9A topology, and A3D reads."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("generalized readiness requires an already-open SQLite connection")
        self._connection = connection

    def run(
        self, request: GeneralizedNativeRuntimeReadinessRequest,
    ) -> GeneralizedNativeRuntimeReadinessReport:
        if not isinstance(request, GeneralizedNativeRuntimeReadinessRequest):
            raise ValueError("request must be a GeneralizedNativeRuntimeReadinessRequest")
        before = _whole_core_fingerprint(self._connection)
        total_changes = self._connection.total_changes
        description = request.description
        root_reasons: list[str] = []
        core_readiness = read_core_runtime_readiness(
            self._connection, request.expected_native_core_id,
        )
        if len(core_readiness) != 1 or core_readiness[0].value != "QUALIFIED_STAGING_LEGACY_ACTIVE":
            root_reasons.extend(item.value for item in core_readiness)
        manifest_valid = True
        try:
            description.explicit_source_manifest.verify(data_root=request.data_root)
        except SubstrateEvidenceIntegrityMismatch:
            manifest_valid = False
            root_reasons.append(GeneralizedReadinessReason.SOURCE_MANIFEST_DRIFT.value)

        declared_scopes = _declared_scopes(description)
        inputs = {item.scope_key: item for item in request.scope_inputs}
        census_ready = set(declared_scopes) == set(inputs)
        if not census_ready:
            root_reasons.append(GeneralizedReadinessReason.SCOPE_INPUT_SET_MISMATCH.value)

        reports: dict[RootScopeKey, MigrationRuntimeReadinessReport] = {}
        for scope_key, item in inputs.items():
            if scope_key not in declared_scopes:
                continue
            if item.readiness_request.target_lane != description.target_representation_lane:
                root_reasons.append(GeneralizedReadinessReason.TARGET_LANE_MISMATCH.value)
                continue
            if item.readiness_request.expected_native_core_id != request.expected_native_core_id:
                root_reasons.append(GeneralizedReadinessReason.CORE_ID_MISMATCH.value)
                continue
            reports[scope_key] = NativeMigrationRuntimeReadinessPreflight(self._connection).run(
                item.readiness_request
            )

        scope_items: list[GeneralizedScopeReadinessItem] = []
        for scope_key, declared in declared_scopes.items():
            report = reports.get(scope_key)
            if report is None:
                scope_items.append(_missing_scope_item(declared))
                continue
            scope_items.append(self._scope_item(declared, inputs[scope_key], report, description))

        workspace_items = _workspace_items(description, tuple(scope_items))
        topology_ready = all(
            item.memory_closure_ready
            and item.motif_closure_ready
            and item.member_reference_closure_ready
            and not item.reason_codes
            for item in scope_items
        ) and all(item.topology_complete for item in workspace_items)

        plans = tuple(inputs[key].scope_plan for key in sorted(reports, key=lambda value: value.canonical_key))
        post_write_plans = tuple(
            inputs[scope_key].scope_plan
            for scope_key, declared in declared_scopes.items()
            if declared.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH
            and scope_key in reports
            # The frozen core-staging adapter has a qualified generic form only
            # for private writes.  A shared adapter must name one separately
            # qualified shared consumer (which this readiness report cannot
            # invent, especially while geometry remains unresolved).  Binding
            # and routing still cover every declared materialized scope above.
            and inputs[scope_key].scope_plan.scope_kind == "PRIVATE_AGENT"
        )
        binding_ready, routing_ready, post_write_ready, construction_reasons = self._construct_a3d(
            request, plans, post_write_plans
        )
        root_reasons.extend(construction_reasons)
        if before != _whole_core_fingerprint(self._connection) or total_changes != self._connection.total_changes:
            raise SubstrateInvariantViolation("generalized readiness changed durable native state")
        reasons = tuple(sorted(set(root_reasons + [
            code for item in scope_items for code in item.reason_codes
        ] + [code for item in workspace_items for code in item.reason_codes])))
        ready = bool(manifest_valid and census_ready and topology_ready and binding_ready and routing_ready and post_write_ready and not reasons)
        return GeneralizedNativeRuntimeReadinessReport(
            root_description_digest=description.identity_digest,
            source_manifest_digest=description.explicit_source_manifest.digest,
            source_manifest_valid=manifest_valid,
            native_core_id=request.expected_native_core_id,
            target_lane=description.target_representation_lane,
            scope_items=tuple(sorted(scope_items, key=lambda item: item.scope_key.canonical_key)),
            workspace_items=workspace_items,
            census_closure_ready=census_ready,
            declared_topology_ready=topology_ready,
            a3d_binding_constructible=binding_ready,
            a3d_routing_constructible=routing_ready,
            a3d_post_write_constructible=post_write_ready,
            generalized_staging_runtime_ready=ready,
            activation_ready=False,
            geometry_derived_external_state_disposition=(
                description.feature_posture.geometry_derived_external_state_disposition
            ),
            reason_codes=reasons,
            durable_effect_count=0,
            authority_expansion_count=0,
            observed_core_fingerprint=before,
        )

    def _scope_item(
        self,
        declared: MaterializedRootScopePlan,
        input_item: GeneralizedScopeReadinessInput,
        report: MigrationRuntimeReadinessReport,
        description: RootNativeProductionAdmissionDescription,
    ) -> GeneralizedScopeReadinessItem:
        reasons: list[str] = []
        memory = tuple(
            item for item in report.object_items
            if item.readiness is not ObjectRuntimeReadiness.EVIDENCE_ONLY_NOT_RUNTIME_OBJECT
        )
        native_memory_count, active_representation_count = _current_scope_memory_counts(
            self._connection, input_item.scope_plan,
        )
        if declared.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
            empty_reason: GeneralizedTopologyReason | None = GeneralizedTopologyReason.MEMORY_FACTS_REQUIRED
            memory_ready = bool(memory) and all(
                item.readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS and not item.reason_codes
                for item in memory
            )
            if not memory:
                reasons.append(GeneralizedReadinessReason.DECLARED_MEMORY_GRAPH_HAS_NO_MIGRATED_MEMORY.value)
            elif not memory_ready:
                reasons.append(GeneralizedReadinessReason.DECLARED_MEMORY_GRAPH_MEMORY_NOT_READY.value)
        else:
            empty_reason = GeneralizedTopologyReason.ZERO_MEMORY_EXPECTED
            memory_ready = native_memory_count == 0 and active_representation_count == 0
            if native_memory_count:
                reasons.append(GeneralizedReadinessReason.DECLARED_EMPTY_SCOPE_HAS_MEMORY.value)
            if active_representation_count:
                reasons.append(
                    GeneralizedReadinessReason.DECLARED_EMPTY_SCOPE_HAS_ACTIVE_REPRESENTATION.value
                )

        motif_source_declared = _motif_source_declared(description, declared.scope_key)
        motifs = report.motif_items
        reader = NativeMotifRuntimeReader(self._connection)
        lineages: list[MotifProjectionLineage] = []
        member_ready = True
        if motif_source_declared:
            motif_empty_reason: GeneralizedTopologyReason | None = GeneralizedTopologyReason.MOTIF_FACTS_REQUIRED
            motif_ready = bool(motifs)
            if not motifs:
                reasons.append(GeneralizedReadinessReason.DECLARED_MOTIF_SOURCE_HAS_NO_MOTIF.value)
            for motif in motifs:
                if motif.readiness is not MotifRuntimeReadiness.RUNTIME_READY_AS_IS:
                    motif_ready = False
                    reasons.append(GeneralizedReadinessReason.MOTIF_NOT_RUNTIME_READY.value)
                    continue
                target = reader.resolve_certified_zero_member_migration_baseline(
                    source_motif_object_id=motif.motif_object_id,
                    source_motif_revision_id=motif.current_revision_id,
                    runtime_motif_id=motif.runtime_motif_id or "",
                    source_state_payload=_motif_source_state(self._connection, motif.motif_object_id),
                    target_lane_identity=_lane_identity(description.target_representation_lane),
                    motif_alias_namespace_id=input_item.scope_plan.motif_alias_namespace_id,
                    motif_identity_namespace_id=input_item.scope_plan.motif_identity_namespace_id,
                    membership_identity_namespace_id=input_item.scope_plan.membership_identity_namespace_id,
                    target_semantic_scope_id=input_item.scope_plan.target_semantic_scope_id,
                )
                if target is not None:
                    lineages.append(MotifProjectionLineage.B4C)
                    if not reader.is_certified_zero_member_migration_baseline(target):
                        motif_ready = member_ready = False
                        reasons.append(GeneralizedReadinessReason.B4C_ZERO_MEMBER_CERTIFICATION_MISSING.value)
                    elif reader.list_ordered_current_motif_members(target):
                        motif_ready = member_ready = False
                        reasons.append(GeneralizedReadinessReason.B4C_CURRENT_MEMBERS_NOT_ZERO.value)
                else:
                    lineages.append(MotifProjectionLineage.B4A)
                    if motif.membership_count < 1:
                        motif_ready = member_ready = False
                        reasons.append(GeneralizedReadinessReason.MEMBER_BEARING_MOTIF_HAS_NO_CURRENT_MEMBERS.value)
        else:
            motif_empty_reason = GeneralizedTopologyReason.ZERO_MOTIFS_EXPECTED
            motif_ready = not motifs
            if motifs:
                reasons.append(GeneralizedReadinessReason.DECLARED_ZERO_MOTIFS_HAS_SOURCE_MOTIF.value)
            if reader.has_runtime_motif_in_scope(
                motif_alias_namespace_id=input_item.scope_plan.motif_alias_namespace_id,
                semantic_scope_id=input_item.scope_plan.target_semantic_scope_id,
            ):
                motif_ready = False
                reasons.append(GeneralizedReadinessReason.DECLARED_ZERO_MOTIFS_HAS_RUNTIME_MOTIF.value)

        return GeneralizedScopeReadinessItem(
            scope_key=declared.scope_key,
            materialization_posture=declared.materialization_posture,
            memory_fact_count=native_memory_count,
            motif_fact_count=len(motifs),
            memory_closure_ready=memory_ready,
            motif_closure_ready=motif_ready,
            member_reference_closure_ready=member_ready,
            empty_topology_reason=(
                GeneralizedTopologyReason.B4C_ZERO_MEMBERS_CERTIFIED
                if MotifProjectionLineage.B4C in lineages and not reasons
                else empty_reason if declared.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF
                else motif_empty_reason if not motif_source_declared
                else None
            ),
            motif_lineages=tuple(lineages),
            reason_codes=tuple(sorted(set(reasons))),
        )

    def _construct_a3d(
        self,
        request: GeneralizedNativeRuntimeReadinessRequest,
        plans: tuple[MigrationRuntimeScopePlan, ...],
        post_write_plans: tuple[MigrationRuntimeScopePlan, ...],
    ) -> tuple[bool, bool, bool, tuple[str, ...]]:
        if not plans:
            if request.post_write_configurations:
                return True, True, False, (
                    GeneralizedReadinessReason.A3D_POST_WRITE_CONFIGURATION_MISMATCH.value,
                )
            return True, True, True, ()
        construction = construct_read_only_runtime_capability(
            connection=self._connection,
            native_core_database_path=request.native_core_database_path,
            expected_native_core_id=request.expected_native_core_id,
            plans=plans,
            target_lane=request.description.target_representation_lane,
            qualification_embedder_identity=request.qualification_embedder_identity,
        )
        if construction.binding is None:
            return False, False, False, (GeneralizedReadinessReason.A3D_BINDING_REFUSED.value,)
        if construction.capability is None:
            return True, False, False, (GeneralizedReadinessReason.A3D_ROUTING_REFUSED.value,)
        routing_scopes = tuple(construction.capability.routing_scopes)
        required_routing_scopes = {
            next(
                scope for scope in routing_scopes
                if scope.runtime_scope.semantic_scope_id == plan.target_semantic_scope_id
            )
            for plan in post_write_plans
        }
        if len(request.post_write_configurations) != len(required_routing_scopes) or {
            item.routing_scope for item in request.post_write_configurations
        } != required_routing_scopes:
            return True, True, False, (GeneralizedReadinessReason.A3D_POST_WRITE_CONFIGURATION_MISMATCH.value,)
        try:
            for configuration in request.post_write_configurations:
                if configuration.profile != NativePostWriteQualificationProfile.core_staging():
                    raise ValueError("not core staging")
                prepare_native_fabric_post_write_adapter(
                    capability=construction.capability, configuration=configuration,
                )
        except (SubstrateConfigurationError, ValueError, SubstrateInvariantViolation):
            return True, True, False, (GeneralizedReadinessReason.A3D_POST_WRITE_ADAPTER_REFUSED.value,)
        return True, True, True, ()


def _declared_scopes(
    description: RootNativeProductionAdmissionDescription,
) -> dict[RootScopeKey, MaterializedRootScopePlan]:
    return {
        scope.scope_key: scope
        for workspace in description.workspace_plans
        for scope in workspace.runtime_scopes
    }


def _plan_matches_scope(plan: MigrationRuntimeScopePlan, scope_key: RootScopeKey) -> bool:
    if plan.workspace_id != scope_key.workspace_id:
        return False
    if scope_key.scope_kind is RootScopeKind.PRIVATE:
        return plan.scope_kind == "PRIVATE_AGENT" and plan.agent_id == scope_key.agent_id
    return plan.scope_kind == "SHARED_DOMAIN" and plan.domain_id == scope_key.domain_id


def _motif_source_declared(
    description: RootNativeProductionAdmissionDescription, scope_key: RootScopeKey,
) -> bool:
    return any(
        entry.scope_key == scope_key
        and entry.semantic_role.value == "MOTIFS"
        and entry.presence_expectation.value == "EXPECTED_PRESENT"
        for entry in description.explicit_source_manifest.entries
    )


def _motif_source_state(connection: sqlite3.Connection, motif_object_id: UUID) -> dict[str, Any]:
    row = connection.execute(
        """SELECT payload_text FROM object_revisions
             WHERE object_id=? AND object_revision_id=(
                 SELECT current_revision_id FROM objects WHERE object_id=?
             )""",
        (motif_object_id.bytes, motif_object_id.bytes),
    ).fetchone()
    if row is None:
        raise SubstrateInvariantViolation("admitted motif source state is missing")
    import json
    try:
        payload = json.loads(row[0])
    except (TypeError, json.JSONDecodeError) as exc:
        raise SubstrateInvariantViolation("admitted motif source state is malformed") from exc
    if not isinstance(payload, dict):
        raise SubstrateInvariantViolation("admitted motif source state is malformed")
    return payload


def _lane_identity(lane: NativeRepresentationLane) -> tuple[str, str, int, str, int, str, str, str]:
    return (
        lane.provider, lane.model, lane.dimension, lane.representation_class,
        lane.generation, lane.derivation_contract_version, lane.encoding_id, lane.dtype,
    )


def _current_scope_memory_counts(
    connection: sqlite3.Connection, plan: MigrationRuntimeScopePlan,
) -> tuple[int, int]:
    """Observe only declared target-scope topology, not a second B1 verdict.

    B1 remains the authority for whether each expected admitted source memory is
    migration- and representation-ready.  This separate, intentionally small
    inventory closes the distinct declared-empty law: an out-of-band current
    memory or READY representation in a target scope is observable even when it
    was not part of B1's source snapshot.
    """
    parameters = (plan.target_identity_namespace_id.bytes, plan.target_semantic_scope_id.bytes)
    object_count = connection.execute(
        """SELECT count(*)
             FROM objects object
             JOIN object_revisions revision
               ON revision.object_id=object.object_id
              AND revision.object_revision_id=object.current_revision_id
              AND revision.revision_ordinal=object.current_revision_ordinal
            WHERE object.identity_namespace_id=?
              AND revision.effective_semantic_scope_id=?
              AND object.object_kind='LEGACY_CORE_NODE'
              AND revision.existence_state='EXISTS'""",
        parameters,
    ).fetchone()[0]
    active_representation_count = connection.execute(
        """SELECT count(*)
             FROM representations representation
             JOIN objects object ON object.object_id=representation.source_object_id
             JOIN object_revisions revision
               ON revision.object_id=object.object_id
              AND revision.object_revision_id=object.current_revision_id
              AND revision.revision_ordinal=object.current_revision_ordinal
             JOIN representation_current_state state
               ON state.representation_id=representation.representation_id
            WHERE object.identity_namespace_id=?
              AND revision.effective_semantic_scope_id=?
              AND object.object_kind='LEGACY_CORE_NODE'
              AND representation.source_object_revision_id=object.current_revision_id
              AND representation.representation_class='COMPAT_EMBEDDING'
              AND state.readiness='READY'
              AND state.operational_disposition='USABLE'""",
        parameters,
    ).fetchone()[0]
    return int(object_count), int(active_representation_count)


def _missing_scope_item(declared: MaterializedRootScopePlan) -> GeneralizedScopeReadinessItem:
    return GeneralizedScopeReadinessItem(
        scope_key=declared.scope_key,
        materialization_posture=declared.materialization_posture,
        memory_fact_count=0,
        motif_fact_count=0,
        memory_closure_ready=False,
        motif_closure_ready=False,
        member_reference_closure_ready=False,
        empty_topology_reason=None,
        motif_lineages=(),
        reason_codes=(GeneralizedReadinessReason.SCOPE_INPUT_SET_MISMATCH.value,),
    )


def _workspace_items(
    description: RootNativeProductionAdmissionDescription,
    scope_items: tuple[GeneralizedScopeReadinessItem, ...],
) -> tuple[GeneralizedWorkspaceReadinessItem, ...]:
    by_scope = {item.scope_key: item for item in scope_items}
    result: list[GeneralizedWorkspaceReadinessItem] = []
    for workspace in description.workspace_plans:
        declared = workspace.runtime_scopes
        reasons: list[str] = []
        if workspace.no_memory_scope and workspace.materialized_scopes:
            reasons.append(GeneralizedReadinessReason.NO_MEMORY_WORKSPACE_HAS_MATERIALIZED_SCOPE.value)
        if not declared:
            result.append(GeneralizedWorkspaceReadinessItem(
                workspace.workspace_id, 0, not reasons, workspace.no_memory_scope,
                tuple(sorted(set(reasons))),
            ))
            continue
        complete = all(
            by_scope.get(scope.scope_key) is not None
            and by_scope[scope.scope_key].memory_closure_ready
            and by_scope[scope.scope_key].motif_closure_ready
            and by_scope[scope.scope_key].member_reference_closure_ready
            and not by_scope[scope.scope_key].reason_codes
            for scope in declared
        ) and not reasons
        result.append(GeneralizedWorkspaceReadinessItem(
            workspace.workspace_id, len(declared), complete, workspace.no_memory_scope,
            tuple(sorted(set(reasons))),
        ))
    return tuple(result)


__all__ = [
    "GeneralizedNativeRuntimeReadinessReport",
    "GeneralizedNativeRuntimeReadinessRequest",
    "GeneralizedReadinessReason",
    "GeneralizedScopeReadinessInput",
    "GeneralizedScopeReadinessItem",
    "GeneralizedTopologyReason",
    "GeneralizedWorkspaceReadinessItem",
    "NativeGeneralizedRuntimeReadiness",
]
