"""Root-atomic composition of the qualified Phase 9A/9B/B3/B4/R3 seams.

This module is deliberately administrative.  It receives one immutable Phase
9A root description plus already-admitted/B2-normalized child requests, then
rechecks source evidence and dispatches the established B3A, B3B, B4A, B4B,
B4C, and generalized-readiness owners.  It creates neither a core nor a
runtime/selector and contains no representation or motif mathematics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
from pathlib import Path
import sqlite3
from typing import TypeAlias
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateConfigurationError, SubstrateInvariantViolation
from ..native_post_write_runtime import NativePostWriteQualificationConfiguration
from ..runtime_binding import NativeRepresentationLane
from .explicit_source_evidence import ExplicitSourceEvidenceDrift
from .generalized_runtime_readiness import (
    GeneralizedNativeRuntimeReadinessReport,
    GeneralizedNativeRuntimeReadinessRequest,
    GeneralizedScopeReadinessInput,
    NativeGeneralizedRuntimeReadiness,
)
from .metadata_less_per_eid_legacy_source import QualifiedMetadataLessPerEidLegacySource
from .root_admission_description import (
    GeometryDerivedExternalStateDisposition,
    MaterializedRootScopePlan,
    MaterializedScopePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
)
from .root_scope import RootScopeKey
from .runtime_motif_projection import (
    MigrationRuntimeMotifProjectionRequest,
    MigrationRuntimeMotifProjectionResult,
    NativeMigrationRuntimeMotifProjectionService,
)
from .runtime_motif_regeometry_projection import (
    MigrationRuntimeMotifRegeometryProjectionRequest,
    MigrationRuntimeMotifRegeometryProjectionResult,
    NativeMigrationRuntimeMotifRegeometryProjectionService,
)
from .runtime_readiness import MigrationRuntimeReadinessRequest, MigrationRuntimeScopePlan
from .runtime_reembedding_bootstrap import (
    MigrationRuntimeReembeddingBootstrapRequest,
    MigrationRuntimeReembeddingBootstrapResult,
    NativeMigrationRuntimeReembeddingBootstrapService,
)
from .runtime_representation_bootstrap import (
    MigrationRuntimeRepresentationBootstrapRequest,
    MigrationRuntimeRepresentationBootstrapResult,
    NativeMigrationRuntimeRepresentationBootstrapService,
)
from .runtime_zero_member_motif_projection import (
    MigrationRuntimeZeroMemberMotifProjectionRequest,
    MigrationRuntimeZeroMemberMotifProjectionResult,
    NativeMigrationRuntimeZeroMemberMotifProjectionService,
)
from .snapshot import load_snapshot_manifest, verify_snapshot
from .workspace_runtime_readiness import MotifProjectionLineage, WorkspaceNativeEmbedderIdentity


class RootNormalizationRefused(SubstrateConfigurationError):
    """A fail-closed root-orchestration boundary refusal."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class RootNormalizationInterruptionPoint(StrEnum):
    """Focused test-only checkpoints; never persisted semantic inputs."""

    AFTER_FIRST_WORKSPACE = "AFTER_FIRST_WORKSPACE"
    INSIDE_WORKSPACE_AFTER_REPRESENTATION_NORMALIZATION = (
        "INSIDE_WORKSPACE_AFTER_REPRESENTATION_NORMALIZATION"
    )
    AFTER_B3_BEFORE_B4 = "AFTER_B3_BEFORE_B4"
    AFTER_B4_BEFORE_GENERALIZED_READINESS = "AFTER_B4_BEFORE_GENERALIZED_READINESS"
    AFTER_CHILD_COMPLETION_BEFORE_ROOT_WITNESS = "AFTER_CHILD_COMPLETION_BEFORE_ROOT_WITNESS"


@dataclass(frozen=True)
class RootNormalizationRecoveryWitness:
    """Non-authorizing identity needed to resume child-idempotent work."""

    root_description_digest: str
    expected_census_digest: str
    source_manifest_digest: str
    native_staging_core_id: UUID
    target_lane: NativeRepresentationLane

    def __post_init__(self) -> None:
        for name in (
            "root_description_digest", "expected_census_digest", "source_manifest_digest",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(f"{name} must be a SHA-256 digest")
            try:
                int(value, 16)
            except ValueError as exc:
                raise ValueError(f"{name} must be a SHA-256 digest") from exc
        if not isinstance(self.native_staging_core_id, UUID):
            raise ValueError("native_staging_core_id must be UUID")
        if not isinstance(self.target_lane, NativeRepresentationLane):
            raise ValueError("target_lane must be NativeRepresentationLane")


class RootNormalizationInterrupted(RuntimeError):
    """Test-only interruption carrying the immutable recovery witness."""

    def __init__(
        self,
        point: RootNormalizationInterruptionPoint,
        recovery_witness: RootNormalizationRecoveryWitness,
    ) -> None:
        self.point = point
        self.recovery_witness = recovery_witness
        super().__init__(f"forced root normalization interruption at {point.value}")


@dataclass(frozen=True)
class MetadataLessB3BDispatch:
    """The Phase 9B evidence hand-off paired with its one existing B3B call."""

    source: QualifiedMetadataLessPerEidLegacySource
    b3b_request: MigrationRuntimeReembeddingBootstrapRequest

    def __post_init__(self) -> None:
        if not isinstance(self.source, QualifiedMetadataLessPerEidLegacySource):
            raise ValueError("metadata-less dispatch requires qualified Phase 9B evidence")
        if not isinstance(self.b3b_request, MigrationRuntimeReembeddingBootstrapRequest):
            raise ValueError("metadata-less dispatch requires a B3B request")
        if self.source.legacy_eid != self.b3b_request.eid:
            raise ValueError("metadata-less source EID must match its B3B request")
        if self.source.legacy_source_namespace_id != self.b3b_request.legacy_source_namespace_id:
            raise ValueError("metadata-less source namespace must match its B3B request")
        if len(self.b3b_request.scope_plans) != 1:
            raise ValueError("metadata-less B3B dispatch requires one scope plan")
        if self.source.target_identity_namespace_id != self.b3b_request.scope_plans[0].target_identity_namespace_id:
            raise ValueError("metadata-less source target namespace must match its B3B scope")


@dataclass(frozen=True)
class RootNormalizationScopeInput:
    """Caller-owned B3/B4 request bundle for exactly one declared RootScopeKey.

    B2/source admission is intentionally a precondition: this coordinator has
    no second admission or memory-normalization implementation.  Every child
    request must therefore bind its already-admitted source and B2 R2 facts.
    """

    scope_key: RootScopeKey
    scope_plan: MigrationRuntimeScopePlan
    legacy_snapshot_id: UUID
    b3a_requests: tuple[MigrationRuntimeRepresentationBootstrapRequest, ...] = ()
    b3b_requests: tuple[MigrationRuntimeReembeddingBootstrapRequest, ...] = ()
    metadata_less_b3b_dispatches: tuple[MetadataLessB3BDispatch, ...] = ()
    b4a_requests: tuple[MigrationRuntimeMotifProjectionRequest, ...] = ()
    b4b_requests: tuple[MigrationRuntimeMotifRegeometryProjectionRequest, ...] = ()
    b4c_requests: tuple[MigrationRuntimeZeroMemberMotifProjectionRequest, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey):
            raise ValueError("scope_key must be RootScopeKey")
        if not isinstance(self.scope_plan, MigrationRuntimeScopePlan):
            raise ValueError("scope_plan must be MigrationRuntimeScopePlan")
        if not isinstance(self.legacy_snapshot_id, UUID):
            raise ValueError("legacy_snapshot_id must be UUID")
        _typed_requests(
            self.b3a_requests, MigrationRuntimeRepresentationBootstrapRequest, "b3a_requests",
        )
        _typed_requests(
            self.b3b_requests, MigrationRuntimeReembeddingBootstrapRequest, "b3b_requests",
        )
        _typed_requests(
            self.metadata_less_b3b_dispatches, MetadataLessB3BDispatch,
            "metadata_less_b3b_dispatches",
        )
        _typed_requests(
            self.b4a_requests, MigrationRuntimeMotifProjectionRequest, "b4a_requests",
        )
        _typed_requests(
            self.b4b_requests, MigrationRuntimeMotifRegeometryProjectionRequest, "b4b_requests",
        )
        _typed_requests(
            self.b4c_requests, MigrationRuntimeZeroMemberMotifProjectionRequest, "b4c_requests",
        )
        if not _scope_plan_matches_key(self.scope_plan, self.scope_key):
            raise ValueError("scope_plan does not match its RootScopeKey")
        for request in self.b3a_requests:
            _validate_direct_request(request, self.scope_plan, self.legacy_snapshot_id)
        for request in (*self.b3b_requests, *(item.b3b_request for item in self.metadata_less_b3b_dispatches)):
            _validate_scoped_request(request, self.scope_plan, self.legacy_snapshot_id)
        for request in (*self.b4a_requests, *self.b4b_requests, *self.b4c_requests):
            _validate_scoped_request(request, self.scope_plan, self.legacy_snapshot_id)
        _no_duplicate_eids(self.all_b3_requests)
        _no_duplicate_motif_requests(self.b4a_requests, self.b4b_requests, self.b4c_requests)

    @property
    def all_b3_requests(
        self,
    ) -> tuple[MigrationRuntimeRepresentationBootstrapRequest | MigrationRuntimeReembeddingBootstrapRequest, ...]:
        return (*self.b3a_requests, *self.b3b_requests, *(item.b3b_request for item in self.metadata_less_b3b_dispatches))

    @property
    def all_motif_requests(
        self,
    ) -> tuple[
        MigrationRuntimeMotifProjectionRequest
        | MigrationRuntimeMotifRegeometryProjectionRequest
        | MigrationRuntimeZeroMemberMotifProjectionRequest,
        ...,
    ]:
        return (*self.b4a_requests, *self.b4b_requests, *self.b4c_requests)


@dataclass(frozen=True)
class RootNormalizationRequest:
    """One synthetic STAGING normalization over one declared root and one core."""

    description: RootNativeProductionAdmissionDescription
    data_root: str | Path
    native_core_database_path: str | Path
    expected_native_core_id: UUID
    scope_inputs: tuple[RootNormalizationScopeInput, ...]
    qualification_embedder_identity: WorkspaceNativeEmbedderIdentity
    b3b_embedder: object
    post_write_configurations: tuple[NativePostWriteQualificationConfiguration, ...] = ()
    recovery_witness: RootNormalizationRecoveryWitness | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.description, RootNativeProductionAdmissionDescription):
            raise ValueError("description must be RootNativeProductionAdmissionDescription")
        for field_name in ("data_root", "native_core_database_path"):
            value = getattr(self, field_name)
            if not isinstance(value, (str, Path)) or not str(value).strip():
                raise ValueError(f"{field_name} must be an explicit path")
        if not isinstance(self.expected_native_core_id, UUID):
            raise ValueError("expected_native_core_id must be UUID")
        _typed_requests(self.scope_inputs, RootNormalizationScopeInput, "scope_inputs")
        if len({item.scope_key for item in self.scope_inputs}) != len(self.scope_inputs):
            raise ValueError("scope_inputs must have unique RootScopeKeys")
        if not isinstance(self.qualification_embedder_identity, WorkspaceNativeEmbedderIdentity):
            raise ValueError("qualification_embedder_identity must be typed")
        if not callable(getattr(self.b3b_embedder, "embed", None)):
            raise ValueError("b3b_embedder must be an injected embedder")
        _typed_requests(
            self.post_write_configurations, NativePostWriteQualificationConfiguration,
            "post_write_configurations",
        )
        if self.recovery_witness is not None and not isinstance(
            self.recovery_witness, RootNormalizationRecoveryWitness,
        ):
            raise ValueError("recovery_witness must be RootNormalizationRecoveryWitness")
        declared = _declared_scopes(self.description)
        supplied = {item.scope_key: item for item in self.scope_inputs}
        if set(declared) != set(supplied):
            raise ValueError("scope_inputs must exactly match declared runtime scopes")
        for key, plan in declared.items():
            _validate_scope_dispatch(
                plan, supplied[key], self.description.target_representation_lane,
                self.expected_native_core_id, self.description,
            )


class RootRepresentationBootstrapKind(StrEnum):
    B3A = "B3A"
    B3B = "B3B"


class RootChildCompletionState(StrEnum):
    COMPLETED = "COMPLETED"
    REFUSED = "REFUSED"


@dataclass(frozen=True)
class RootRepresentationNormalizationResult:
    kind: RootRepresentationBootstrapKind
    eid: int
    representation_id: UUID | None
    state: RootChildCompletionState
    reason_code: str | None
    metadata_less_source_evidence_identity: str | None = None


@dataclass(frozen=True)
class RootMotifNormalizationResult:
    lineage: MotifProjectionLineage
    runtime_motif_id: str
    motif_object_id: UUID | None
    state: RootChildCompletionState
    reason_code: str | None


@dataclass(frozen=True)
class RootScopeNormalizationResult:
    scope_key: RootScopeKey
    representation_disposition: RootRepresentationDisposition
    representation_results: tuple[RootRepresentationNormalizationResult, ...]
    motif_results: tuple[RootMotifNormalizationResult, ...]
    completed: bool


@dataclass(frozen=True)
class RootWorkspaceNormalizationResult:
    workspace_id: str
    declared_materialized_scope_count: int
    observed_materialized_scope_count: int
    completed: bool


@dataclass(frozen=True)
class RootNormalizationResult:
    """Immutable staging evidence; explicitly not deployment authority."""

    recovery_witness: RootNormalizationRecoveryWitness
    expected_workspace_count: int
    observed_workspace_closure: int
    expected_materialized_scope_count: int
    observed_materialized_scope_closure: int
    workspace_results: tuple[RootWorkspaceNormalizationResult, ...]
    scope_results: tuple[RootScopeNormalizationResult, ...]
    generalized_readiness_result: GeneralizedNativeRuntimeReadinessReport | None
    source_manifest_recheck_passed: bool
    unresolved_activation_gates: tuple[GeometryDerivedExternalStateDisposition, ...]
    root_normalization_complete: bool
    root_normalization_ready: bool
    real_root_activation_ready: bool
    partial_activation: bool
    reason_codes: tuple[str, ...]


_B3Result: TypeAlias = (
    MigrationRuntimeRepresentationBootstrapResult | MigrationRuntimeReembeddingBootstrapResult
)
_B4Result: TypeAlias = (
    MigrationRuntimeMotifProjectionResult
    | MigrationRuntimeMotifRegeometryProjectionResult
    | MigrationRuntimeZeroMemberMotifProjectionResult
)


class NativeRootWideNormalizationService:
    """Sequence existing normalization primitives under root-atomic completion law."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("root normalization requires an already-open SQLite connection")
        self._connection = connection

    def normalize(
        self,
        request: RootNormalizationRequest,
        *,
        _test_interrupt_after: RootNormalizationInterruptionPoint | None = None,
    ) -> RootNormalizationResult:
        if not isinstance(request, RootNormalizationRequest):
            raise ValueError("request must be RootNormalizationRequest")
        if _test_interrupt_after is not None and not isinstance(
            _test_interrupt_after, RootNormalizationInterruptionPoint,
        ):
            raise ValueError("_test_interrupt_after must be RootNormalizationInterruptionPoint")
        witness = _recovery_witness(request)
        _validate_recovery_witness(request.recovery_witness, witness)
        _verify_root_source_manifest(request)
        self._recheck_metadata_less_sources(request)

        results: list[RootScopeNormalizationResult] = []
        interrupted_inside_workspace = False
        interrupted_after_b3 = False
        workspaces = {item.workspace_id: [] for item in request.description.workspace_plans}
        by_scope = {item.scope_key: item for item in request.scope_inputs}
        for workspace in request.description.workspace_plans:
            workspace_scope_results: list[RootScopeNormalizationResult] = []
            for declared in workspace.runtime_scopes:
                input_item = by_scope[declared.scope_key]
                representation_results = self._dispatch_b3(input_item, request.b3b_embedder)
                if (
                    _test_interrupt_after
                    is RootNormalizationInterruptionPoint.INSIDE_WORKSPACE_AFTER_REPRESENTATION_NORMALIZATION
                    and not interrupted_inside_workspace
                ):
                    raise RootNormalizationInterrupted(_test_interrupt_after, witness)
                interrupted_inside_workspace = True
                if (
                    _test_interrupt_after is RootNormalizationInterruptionPoint.AFTER_B3_BEFORE_B4
                    and not interrupted_after_b3
                ):
                    raise RootNormalizationInterrupted(_test_interrupt_after, witness)
                interrupted_after_b3 = True
                motif_results = self._dispatch_b4(input_item)
                result = RootScopeNormalizationResult(
                    scope_key=declared.scope_key,
                    representation_disposition=declared.representation_disposition,
                    representation_results=representation_results,
                    motif_results=motif_results,
                    completed=all(item.state is RootChildCompletionState.COMPLETED for item in (*representation_results, *motif_results)),
                )
                workspace_scope_results.append(result)
                results.append(result)
            workspaces[workspace.workspace_id] = workspace_scope_results
            if (
                _test_interrupt_after is RootNormalizationInterruptionPoint.AFTER_FIRST_WORKSPACE
                and workspace.workspace_id == request.description.workspace_plans[0].workspace_id
            ):
                raise RootNormalizationInterrupted(_test_interrupt_after, witness)

        if _test_interrupt_after is RootNormalizationInterruptionPoint.AFTER_B4_BEFORE_GENERALIZED_READINESS:
            raise RootNormalizationInterrupted(_test_interrupt_after, witness)
        readiness, readiness_reason = self._run_generalized_readiness(request)
        if _test_interrupt_after is RootNormalizationInterruptionPoint.AFTER_CHILD_COMPLETION_BEFORE_ROOT_WITNESS:
            raise RootNormalizationInterrupted(_test_interrupt_after, witness)
        return _aggregate_result(request, witness, tuple(results), readiness, readiness_reason)

    def _recheck_metadata_less_sources(self, request: RootNormalizationRequest) -> None:
        for scope_input in request.scope_inputs:
            for dispatch in scope_input.metadata_less_b3b_dispatches:
                try:
                    rechecked = dispatch.source.recheck(data_root=request.data_root)
                except (SubstrateConfigurationError, OSError, ValueError) as exc:
                    raise RootNormalizationRefused("ROOT_METADATA_LESS_SOURCE_DRIFT") from exc
                if rechecked.source_evidence_identity != dispatch.source.source_evidence_identity:
                    raise RootNormalizationRefused("ROOT_METADATA_LESS_SOURCE_DRIFT")

    def _dispatch_b3(
        self, input_item: RootNormalizationScopeInput, embedder: object,
    ) -> tuple[RootRepresentationNormalizationResult, ...]:
        results: list[RootRepresentationNormalizationResult] = []
        service_a = NativeMigrationRuntimeRepresentationBootstrapService(self._connection)
        service_b = NativeMigrationRuntimeReembeddingBootstrapService(self._connection)
        for child in input_item.b3a_requests:
            results.append(_b3_receipt(
                RootRepresentationBootstrapKind.B3A, child.eid,
                _attempt(lambda: service_a.bootstrap_from_legacy_capture(child)), None,
            ))
        for child in input_item.b3b_requests:
            results.append(_b3_receipt(
                RootRepresentationBootstrapKind.B3B, child.eid,
                _attempt(lambda: service_b.bootstrap_from_qualified_text(child, embedder=embedder)), None,
            ))
        for dispatch in input_item.metadata_less_b3b_dispatches:
            results.append(_b3_receipt(
                RootRepresentationBootstrapKind.B3B, dispatch.b3b_request.eid,
                _attempt(lambda: service_b.bootstrap_from_qualified_text(dispatch.b3b_request, embedder=embedder)),
                dispatch.source.source_evidence_identity,
            ))
        return tuple(sorted(results, key=lambda item: (item.eid, item.kind.value)))

    def _dispatch_b4(
        self, input_item: RootNormalizationScopeInput) -> tuple[RootMotifNormalizationResult, ...]:
        results: list[RootMotifNormalizationResult] = []
        service_a = NativeMigrationRuntimeMotifProjectionService(self._connection)
        service_b = NativeMigrationRuntimeMotifRegeometryProjectionService(self._connection)
        service_c = NativeMigrationRuntimeZeroMemberMotifProjectionService(self._connection)
        for child in input_item.b4a_requests:
            results.append(_b4_receipt(
                MotifProjectionLineage.B4A, child.runtime_motif_id,
                _attempt(lambda: service_a.project_lane_preserving_legacy_motif(child)),
            ))
        for child in input_item.b4b_requests:
            results.append(_b4_receipt(
                MotifProjectionLineage.B4B, child.runtime_motif_id,
                _attempt(lambda: service_b.project_target_lane_regeometry(child)),
            ))
        for child in input_item.b4c_requests:
            results.append(_b4_receipt(
                MotifProjectionLineage.B4C, child.runtime_motif_id,
                _attempt(lambda: service_c.project_target_compatible_zero_member_motif(child)),
            ))
        return tuple(sorted(results, key=lambda item: (item.runtime_motif_id, item.lineage.value)))

    def _run_generalized_readiness(
        self, request: RootNormalizationRequest,
    ) -> tuple[GeneralizedNativeRuntimeReadinessReport | None, str | None]:
        generalized_request = GeneralizedNativeRuntimeReadinessRequest(
            description=request.description,
            data_root=request.data_root,
            native_core_database_path=request.native_core_database_path,
            expected_native_core_id=request.expected_native_core_id,
            scope_inputs=tuple(
                GeneralizedScopeReadinessInput(
                    item.scope_key,
                    MigrationRuntimeReadinessRequest(
                        item.legacy_snapshot_id, request.expected_native_core_id,
                        (item.scope_plan,), request.description.target_representation_lane,
                    ),
                )
                for item in request.scope_inputs
            ),
            qualification_embedder_identity=request.qualification_embedder_identity,
            post_write_configurations=request.post_write_configurations,
        )
        try:
            return NativeGeneralizedRuntimeReadiness(self._connection).run(generalized_request), None
        except (SubstrateConfigurationError, SubstrateInvariantViolation, ValueError):
            return None, "GENERALIZED_READINESS_REFUSED"


def _attempt(operation: object) -> _B3Result | _B4Result | str:
    try:
        return operation()  # type: ignore[operator]
    except (SubstrateConfigurationError, SubstrateInvariantViolation) as exc:
        return _reason_code(exc)


def _b3_receipt(
    kind: RootRepresentationBootstrapKind,
    eid: int,
    outcome: _B3Result | _B4Result | str,
    metadata_less_source_evidence_identity: str | None,
) -> RootRepresentationNormalizationResult:
    if isinstance(outcome, str):
        return RootRepresentationNormalizationResult(
            kind, eid, None, RootChildCompletionState.REFUSED, outcome,
            metadata_less_source_evidence_identity,
        )
    if not isinstance(
        outcome,
        (MigrationRuntimeRepresentationBootstrapResult, MigrationRuntimeReembeddingBootstrapResult),
    ):
        raise AssertionError("B3 dispatch returned a non-B3 result")
    return RootRepresentationNormalizationResult(
        kind, eid, outcome.representation_id, RootChildCompletionState.COMPLETED, None,
        metadata_less_source_evidence_identity,
    )


def _b4_receipt(
    lineage: MotifProjectionLineage,
    runtime_motif_id: str,
    outcome: _B3Result | _B4Result | str,
) -> RootMotifNormalizationResult:
    if isinstance(outcome, str):
        return RootMotifNormalizationResult(
            lineage, runtime_motif_id, None, RootChildCompletionState.REFUSED, outcome,
        )
    if not isinstance(
        outcome,
        (
            MigrationRuntimeMotifProjectionResult,
            MigrationRuntimeMotifRegeometryProjectionResult,
            MigrationRuntimeZeroMemberMotifProjectionResult,
        ),
    ):
        raise AssertionError("B4 dispatch returned a non-B4 result")
    return RootMotifNormalizationResult(
        lineage, runtime_motif_id, outcome.motif_object_id,
        RootChildCompletionState.COMPLETED, None,
    )


def _aggregate_result(
    request: RootNormalizationRequest,
    witness: RootNormalizationRecoveryWitness,
    scope_results: tuple[RootScopeNormalizationResult, ...],
    readiness: GeneralizedNativeRuntimeReadinessReport | None,
    readiness_reason: str | None,
) -> RootNormalizationResult:
    scope_by_key = {item.scope_key: item for item in scope_results}
    workspaces = tuple(
        RootWorkspaceNormalizationResult(
            workspace_id=workspace.workspace_id,
            declared_materialized_scope_count=len(workspace.runtime_scopes),
            observed_materialized_scope_count=sum(
                item.scope_key in scope_by_key for item in workspace.runtime_scopes
            ),
            completed=all(
                scope_by_key.get(item.scope_key) is not None and scope_by_key[item.scope_key].completed
                for item in workspace.runtime_scopes
            ),
        )
        for workspace in request.description.workspace_plans
    )
    child_complete = all(item.completed for item in scope_results)
    workspace_complete = all(item.completed for item in workspaces)
    readiness_complete = readiness is not None and readiness.generalized_staging_runtime_ready
    reasons = [
        receipt.reason_code
        for scope in scope_results
        for receipt in (*scope.representation_results, *scope.motif_results)
        if receipt.reason_code is not None
    ]
    if readiness is not None:
        reasons.extend(readiness.reason_codes)
    if readiness_reason is not None:
        reasons.append(readiness_reason)
    complete = bool(child_complete and workspace_complete and readiness_complete and not reasons)
    expected = request.description.expected_census
    return RootNormalizationResult(
        recovery_witness=witness,
        expected_workspace_count=expected.workspace_count,
        observed_workspace_closure=len(workspaces),
        expected_materialized_scope_count=expected.total_runtime_scope_count,
        observed_materialized_scope_closure=len(scope_results),
        workspace_results=workspaces,
        scope_results=tuple(sorted(scope_results, key=lambda item: item.scope_key.canonical_key)),
        generalized_readiness_result=readiness,
        source_manifest_recheck_passed=True,
        unresolved_activation_gates=(
            request.description.feature_posture.geometry_derived_external_state_disposition,
        ),
        root_normalization_complete=complete,
        root_normalization_ready=complete,
        real_root_activation_ready=False,
        partial_activation=False,
        reason_codes=tuple(sorted(set(reasons))),
    )


def _recovery_witness(request: RootNormalizationRequest) -> RootNormalizationRecoveryWitness:
    return RootNormalizationRecoveryWitness(
        root_description_digest=request.description.identity_digest,
        expected_census_digest=_census_digest(request.description),
        source_manifest_digest=request.description.explicit_source_manifest.digest,
        native_staging_core_id=request.expected_native_core_id,
        target_lane=request.description.target_representation_lane,
    )


def _validate_recovery_witness(
    previous: RootNormalizationRecoveryWitness | None,
    current: RootNormalizationRecoveryWitness,
) -> None:
    if previous is None:
        return
    if previous.root_description_digest != current.root_description_digest:
        raise RootNormalizationRefused("ROOT_DESCRIPTION_DRIFT")
    if previous.expected_census_digest != current.expected_census_digest:
        raise RootNormalizationRefused("ROOT_CENSUS_DRIFT")
    if previous.source_manifest_digest != current.source_manifest_digest:
        raise RootNormalizationRefused("ROOT_SOURCE_MANIFEST_DRIFT")
    if previous.native_staging_core_id != current.native_staging_core_id:
        raise RootNormalizationRefused("ROOT_STAGING_CORE_DRIFT")
    if previous.target_lane != current.target_lane:
        raise RootNormalizationRefused("ROOT_TARGET_LANE_DRIFT")


def _verify_root_source_manifest(request: RootNormalizationRequest) -> None:
    try:
        request.description.explicit_source_manifest.verify(data_root=request.data_root)
    except (ExplicitSourceEvidenceDrift, OSError, ValueError) as exc:
        raise RootNormalizationRefused("ROOT_SOURCE_MANIFEST_DRIFT") from exc


def _validate_scope_dispatch(
    declared: MaterializedRootScopePlan,
    input_item: RootNormalizationScopeInput,
    target_lane: NativeRepresentationLane,
    expected_native_core_id: UUID,
    description: RootNativeProductionAdmissionDescription,
) -> None:
    for request in input_item.all_b3_requests:
        if (
            request.expected_native_core_id != expected_native_core_id
            or request.target_lane != target_lane
        ):
            raise ValueError("every B3 request must use the one root core and target lane")
    for request in input_item.all_motif_requests:
        if (
            request.expected_native_core_id != expected_native_core_id
            or request.target_lane != target_lane
        ):
            raise ValueError("every B4 request must use the one root core and target lane")
    has_b3a = bool(input_item.b3a_requests)
    has_b3b = bool(input_item.b3b_requests or input_item.metadata_less_b3b_dispatches)
    motif_source_declared = any(
        entry.scope_key == declared.scope_key
        and entry.semantic_role.value == "MOTIFS"
        and entry.presence_expectation.value == "EXPECTED_PRESENT"
        for entry in description.explicit_source_manifest.entries
    )
    empty_scope = declared.materialization_posture is not MaterializedScopePosture.MEMORY_GRAPH
    if declared.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF:
        if input_item.all_b3_requests:
            raise ValueError("declared empty shared motif scope cannot dispatch B3")
        if (
            declared.representation_disposition is not RootRepresentationDisposition.TARGET_COMPATIBLE
            or input_item.b4a_requests
            or input_item.b4b_requests
            or not input_item.b4c_requests
        ):
            raise ValueError("declared empty shared motif scope requires only target-compatible B4C")
    elif empty_scope:
        if input_item.all_b3_requests:
            raise ValueError("declared empty scope cannot dispatch B3")
        if declared.representation_disposition is not RootRepresentationDisposition.NO_VECTOR:
            raise ValueError("declared empty scope requires NO_VECTOR disposition")
        if declared.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED:
            if motif_source_declared:
                if input_item.b4a_requests or input_item.b4b_requests or not input_item.b4c_requests:
                    raise ValueError("declared empty shared motif scope requires only B4C")
            elif input_item.all_motif_requests:
                raise ValueError("declared empty shared without motif evidence cannot dispatch B4")
        elif declared.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF:
            if motif_source_declared or input_item.all_motif_requests:
                raise ValueError("physical empty shared without motif cannot dispatch B4")
        elif input_item.all_motif_requests:
            raise ValueError("NO_VECTOR declared empty private scope cannot dispatch B4")
    elif not input_item.all_b3_requests:
        raise ValueError("declared MEMORY_GRAPH scope requires B3 completion requests")
    if empty_scope:
        if declared.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF and not motif_source_declared:
            raise ValueError("empty shared motif scope requires declared motif source evidence")
    elif declared.representation_disposition is RootRepresentationDisposition.TARGET_COMPATIBLE:
        # The workspace lock describes the source lane, while B3 is decided
        # per admitted EID from its qualified retained-vector evidence.  A
        # target-compatible scope can therefore lawfully contain both exact
        # byte derivations and B3B re-embeds/no-vector work.
        if input_item.metadata_less_b3b_dispatches:
            raise ValueError("TARGET_COMPATIBLE scope cannot dispatch metadata-less B3B")
        if (
            declared.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH
            and not (has_b3a or input_item.b3b_requests)
        ):
            raise ValueError("MEMORY_GRAPH scope requires at least one ordinary B3 request")
    elif declared.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
        if has_b3a or input_item.b3b_requests or not input_item.metadata_less_b3b_dispatches:
            raise ValueError("UNKNOWN_IDENTITY scope requires Phase 9B metadata-less B3B dispatch")
    else:
        if input_item.metadata_less_b3b_dispatches:
            raise ValueError("ordinary vector disposition cannot dispatch metadata-less B3B")
        if (
            declared.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH
            and not (has_b3a or input_item.b3b_requests)
        ):
            raise ValueError("MEMORY_GRAPH scope requires at least one ordinary B3 request")
    if motif_source_declared != bool(input_item.all_motif_requests):
        raise ValueError("B4 dispatches must exactly correspond to declared motif source evidence")


def _declared_scopes(
    description: RootNativeProductionAdmissionDescription,
) -> dict[RootScopeKey, MaterializedRootScopePlan]:
    return {
        scope.scope_key: scope
        for workspace in description.workspace_plans
        for scope in workspace.runtime_scopes
    }


def _scope_plan_matches_key(plan: MigrationRuntimeScopePlan, key: RootScopeKey) -> bool:
    if plan.workspace_id != key.workspace_id:
        return False
    if key.scope_kind.value == "PRIVATE":
        return plan.scope_kind == "PRIVATE_AGENT" and plan.agent_id == key.agent_id
    return plan.scope_kind == "SHARED_DOMAIN" and plan.domain_id == key.domain_id


def _validate_direct_request(
    request: MigrationRuntimeRepresentationBootstrapRequest,
    plan: MigrationRuntimeScopePlan,
    snapshot_id: UUID,
) -> None:
    if (
        request.legacy_snapshot_id != snapshot_id
        or request.legacy_source_namespace_id != plan.legacy_source_namespace_id
    ):
        raise ValueError("B3A request does not match its scope source")


def _validate_scoped_request(
    request: object,
    plan: MigrationRuntimeScopePlan,
    snapshot_id: UUID,
) -> None:
    if (
        getattr(request, "legacy_snapshot_id") != snapshot_id
        or getattr(request, "legacy_source_namespace_id") != plan.legacy_source_namespace_id
        or getattr(request, "scope_plans") != (plan,)
    ):
        raise ValueError("child request does not match its declared scope source")


def _typed_requests(values: object, expected_type: type[object], name: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(value, expected_type) for value in values):
        raise ValueError(f"{name} must be a tuple of {expected_type.__name__}")


def _no_duplicate_eids(values: tuple[object, ...]) -> None:
    eids = [getattr(value, "eid") for value in values]
    if len(set(eids)) != len(eids):
        raise ValueError("B3 EIDs must be unique within one root scope")


def _no_duplicate_motif_requests(*groups: tuple[object, ...]) -> None:
    motifs = [getattr(value, "runtime_motif_id") for group in groups for value in group]
    if len(set(motifs)) != len(motifs):
        raise ValueError("B4 runtime motif IDs must be unique within one root scope")


def _reason_code(exc: BaseException) -> str:
    code = getattr(exc, "code", None)
    return code if isinstance(code, str) and code else exc.__class__.__name__


def _census_digest(description: RootNativeProductionAdmissionDescription) -> str:
    return hashlib.sha256(
        canonical_intent_text(description.expected_census.identity_payload()).encode("utf-8")
    ).hexdigest()


__all__ = [
    "MetadataLessB3BDispatch",
    "NativeRootWideNormalizationService",
    "RootChildCompletionState",
    "RootMotifNormalizationResult",
    "RootNormalizationInterrupted",
    "RootNormalizationInterruptionPoint",
    "RootNormalizationRecoveryWitness",
    "RootNormalizationRefused",
    "RootNormalizationRequest",
    "RootNormalizationResult",
    "RootNormalizationScopeInput",
    "RootRepresentationBootstrapKind",
    "RootRepresentationNormalizationResult",
    "RootScopeNormalizationResult",
    "RootWorkspaceNormalizationResult",
]
