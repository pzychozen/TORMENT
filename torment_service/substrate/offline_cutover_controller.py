"""Offline-only orchestration of the already-qualified Blocker-5 cutover facts.

This coordinator deliberately owns no durable progress ledger.  Selector
ledger entries, the mutable admission descriptor, immutable snapshots, and
core maintenance evidence remain the authority and recovery records.  Its
only new input is an explicit operator writer-drain attestation: a process
cannot prove that arbitrary legacy writers have been stopped, so it must not
pretend to do so or try to terminate them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .deployment_core_maintenance import (
    CoreDeploymentInspection,
    CoreMaintenanceResult,
    abort_cutover_pending,
    activate_core,
    enter_cutover_pending,
    inspect_contained_core_deployment,
    staging_legacy_witness,
)
from .deployment_selector import (
    activate_selector_native,
    abort_selector_pending,
    begin_cutover_pending,
    establish_selector_era,
    initialize_selector,
    read_selector_state,
    resolve_deployment_agreement,
)
from .deployment_types import (
    AdmissionCompletionWitness,
    DeploymentResolutionMode,
    DeploymentState,
    QualifiedDeploymentProfile,
    SelectorState,
)
from .errors import DeploymentAuthorityError, SubstrateConfigurationError
from .migration.existing_workspace_multi_scope_admission import (
    ExistingWorkspaceMultiScopeAdmissionRefused,
    ExistingWorkspaceNativeMultiScopeAdmissionRequest,
    ExistingWorkspaceNativeMultiScopeAdmissionService,
    ExistingWorkspaceNativeMultiScopeDescriptor,
    ExistingWorkspaceNativeMultiScopePreparedAdmission,
    ExistingWorkspaceNativeMultiScopeAdmissionResult,
    RecoveredExistingWorkspaceNativeMultiScopeRuntime,
    recover_existing_workspace_native_multi_scope_runtime,
)


class OfflineCutoverRefused(SubstrateConfigurationError):
    """The isolated administrator does not have enough exact offline evidence."""


class OfflineCutoverStage(str, Enum):
    LEGACY = "LEGACY"
    PREPARED = "PREPARED"
    EXTERNAL_PENDING = "EXTERNAL_PENDING"
    ADMISSION_COMPLETE = "ADMISSION_COMPLETE"
    CORE_PENDING = "CORE_PENDING"
    CORE_ACTIVE_EXTERNAL_PENDING = "CORE_ACTIVE_EXTERNAL_PENDING"
    NATIVE_ACTIVE = "NATIVE_ACTIVE"


@dataclass(frozen=True)
class OfflineWriterDrainWitness:
    """An explicit operator attestation after legacy writers were stopped.

    This is intentionally not durable authority and does not name processes.
    It prevents accidental use of the controller without the required offline
    administrative precondition; the caller remains responsible for draining
    REST, MCP, and any other legacy writer before constructing it.
    """

    workspace_id: str
    operator_drain_key: str

    def __post_init__(self) -> None:
        for name in ("workspace_id", "operator_drain_key"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 160:
                raise ValueError(f"{name} must be bounded non-empty text")


@dataclass(frozen=True)
class OfflineCutoverRequest:
    """One isolated root and its already-qualified admission request."""

    data_root: Path
    admission_request: ExistingWorkspaceNativeMultiScopeAdmissionRequest
    effective_profile: QualifiedDeploymentProfile
    operator_cutover_key: str
    writer_drain: OfflineWriterDrainWitness

    def __post_init__(self) -> None:
        root = Path(self.data_root).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("offline cutover data_root must already exist")
        if not isinstance(self.admission_request, ExistingWorkspaceNativeMultiScopeAdmissionRequest):
            raise ValueError("admission_request must be typed")
        if not isinstance(self.effective_profile, QualifiedDeploymentProfile):
            raise ValueError("effective_profile must be typed")
        if not self.effective_profile.is_qualified:
            raise ValueError("offline cutover requires a qualified deployment profile")
        if self.admission_request.effective_deployment_profile != self.effective_profile:
            raise ValueError("admission request must freeze the exact deployment profile")
        if not isinstance(self.operator_cutover_key, str) or not self.operator_cutover_key or len(self.operator_cutover_key) > 160:
            raise ValueError("operator_cutover_key must be bounded non-empty text")
        if not isinstance(self.writer_drain, OfflineWriterDrainWitness):
            raise ValueError("writer_drain must be typed")
        if self.writer_drain.workspace_id != self.admission_request.workspace_id:
            raise ValueError("writer drain witness names another workspace")
        core = Path(self.admission_request.native_core_database_path).expanduser().resolve()
        core_root = root / "substrate" / "cores"
        try:
            relative = core.relative_to(core_root)
        except ValueError as exc:
            raise ValueError("admission core must be contained by data_root/substrate/cores") from exc
        if relative.parent != Path(".") or relative.suffix.lower() != ".db":
            raise ValueError("admission core must be one contained .db filename")

    @property
    def root(self) -> Path:
        return Path(self.data_root).expanduser().resolve()

    @property
    def core_relative_path(self) -> str:
        return Path(self.admission_request.native_core_database_path).expanduser().resolve().name


@dataclass(frozen=True)
class OfflineCutoverEvidence:
    """A read-only summary derived from the pre-existing durable evidence."""

    stage: OfflineCutoverStage
    descriptor: ExistingWorkspaceNativeMultiScopeDescriptor
    selector_state: SelectorState | None
    core: CoreDeploymentInspection
    admission_identity_digest: str
    completion_witness: AdmissionCompletionWitness | None = None


class OfflineCutoverController:
    """Offline coordinator over B5-A2/R0 APIs; it never routes public traffic."""

    def __init__(self, admission_service: ExistingWorkspaceNativeMultiScopeAdmissionService | None = None) -> None:
        self._admission_service = admission_service or ExistingWorkspaceNativeMultiScopeAdmissionService()

    def prepare(self, request: OfflineCutoverRequest) -> OfflineCutoverEvidence:
        """P1: require a writer-drain attestation and create inert evidence only."""

        prepared = self._prepare(request)
        descriptor = prepared.descriptor
        if descriptor.state.value != "ADMISSION_INCOMPLETE_RESUMABLE":
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_PREPARE_ALREADY_SEMANTICALLY_ADVANCED")
        resolution = resolve_deployment_agreement(
            data_root=request.root, effective_profile=request.effective_profile,
        )
        if resolution.mode is not DeploymentResolutionMode.LEGACY_PUBLIC:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_PREPARE_REQUIRES_LEGACY_AUTHORITY")
        return OfflineCutoverEvidence(
            OfflineCutoverStage.PREPARED,
            descriptor,
            resolution.selector_state,
            self._inert_core(request, descriptor),
            prepared.admission_identity_digest,
        )

    def enter_external_pending(self, request: OfflineCutoverRequest) -> OfflineCutoverEvidence:
        """P2: bind the prepared identity into external maintenance-only authority."""

        prepared = self._prepare(request)
        descriptor = prepared.descriptor
        if descriptor.state.value != "ADMISSION_INCOMPLETE_RESUMABLE":
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_PENDING_REQUIRES_UNFINISHED_ADMISSION")
        self._inert_core(request, descriptor)
        state = self._ensure_selector(request)
        if state.deployment_state is DeploymentState.LEGACY_ACTIVE:
            state = begin_cutover_pending(
                data_root=request.root,
                core_relative_path=request.core_relative_path,
                descriptor_digest=prepared.admission_identity_digest,
                profile=request.effective_profile,
                expected_generation=state.generation,
                operation_key=self._key(request, "external-pending"),
            )
        self._require_pending(request, descriptor, state, core_state=DeploymentState.LEGACY_ACTIVE)
        return OfflineCutoverEvidence(
            OfflineCutoverStage.EXTERNAL_PENDING,
            descriptor,
            state,
            self._inspection(request),
            prepared.admission_identity_digest,
        )

    def admit_under_external_fence(
        self,
        request: OfflineCutoverRequest,
        *,
        _test_interrupt_after: str | None = None,
        _test_lose_response_after: str | None = None,
    ) -> ExistingWorkspaceNativeMultiScopeAdmissionResult:
        """P3: run only the established admission while external authority is pending."""

        prepared = self._prepare(request)
        state = self._selector_state(request)
        self._require_pending(
            request, prepared.descriptor, state, core_state=DeploymentState.LEGACY_ACTIVE,
        )
        try:
            result = self._admission_service.admit(
                request.admission_request,
                _test_interrupt_after=_test_interrupt_after,
                _test_lose_response_after=_test_lose_response_after,
            )
        except ExistingWorkspaceMultiScopeAdmissionRefused:
            raise
        finally:
            current = self._selector_state(request)
            descriptor = self._descriptor(request)
            self._require_pending(
                request, descriptor, current, core_state=DeploymentState.LEGACY_ACTIVE,
            )
        return result

    def verify_completion(self, request: OfflineCutoverRequest) -> OfflineCutoverEvidence:
        """P4: fully re-verify the completed descriptor before any core transition."""

        descriptor, completion = self._completed_descriptor(request)
        state = self._selector_state(request)
        self._require_pending(request, descriptor, state, core_state=DeploymentState.LEGACY_ACTIVE)
        runtime = self.staging_read_model(request)
        if len(runtime.scopes) != len(request.admission_request.ordered_lane_plans):
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_COMPLETION_SCOPE_COUNT_MISMATCH")
        return OfflineCutoverEvidence(
            OfflineCutoverStage.ADMISSION_COMPLETE,
            descriptor,
            state,
            self._inspection(request),
            completion.admission_identity_digest,
            completion,
        )

    def staging_read_model(
        self, request: OfflineCutoverRequest,
    ) -> RecoveredExistingWorkspaceNativeMultiScopeRuntime:
        """Recover the qualified, non-public STAGING readers for P4 verification."""

        descriptor, _completion = self._completed_descriptor(request)
        runtime = recover_existing_workspace_native_multi_scope_runtime(
            native_core_database_path=request.admission_request.native_core_database_path,
            admission_descriptor_path=request.admission_request.admission_descriptor_path,
            expected_representation_lane=descriptor.representation_lane,
        )
        return runtime

    def enter_core_pending(self, request: OfflineCutoverRequest) -> CoreMaintenanceResult:
        """P5: advance only the core while external authority remains pending."""

        descriptor, completion = self._completed_descriptor(request)
        state = self._selector_state(request)
        self._require_pending(request, descriptor, state)
        inspection = self._inspection(request)
        if inspection.deployment_state is DeploymentState.CUTOVER_PENDING:
            if (
                inspection.core_role != "STAGING"
                or inspection.witness is None
                or inspection.latest_maintenance_id is None
            ):
                raise OfflineCutoverRefused("OFFLINE_CUTOVER_CORE_PENDING_EVIDENCE_MISMATCH")
            return CoreMaintenanceResult(
                transition_kind="ENTER_CUTOVER_PENDING",
                maintenance_id=inspection.latest_maintenance_id,
                witness=inspection.witness,
                selector_generation=state.generation,
                selector_witness_digest=state.core_witness_digest or "",
            )
        if inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_UNEXPECTED_CORE_STAGE")
        predecessor = staging_legacy_witness(
            inspection,
            descriptor_digest=completion.admission_identity_digest,
            profile_digest=request.effective_profile.digest,
        )
        return enter_cutover_pending(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            expected_witness=predecessor,
            selector_generation=state.generation,
            selector_witness_digest=state.core_witness_digest or "",
            operation_key=self._key(request, "core-pending"),
        )

    def activate_core(self, request: OfflineCutoverRequest) -> CoreMaintenanceResult:
        """P6: record the immutable completed-admission receipt in core evidence."""

        descriptor, completion = self._completed_descriptor(request)
        state = self._selector_state(request)
        self._require_pending(request, descriptor, state)
        inspection = self._inspection(request)
        witness = inspection.witness
        if witness is None:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_CORE_PENDING_WITNESS_MISSING")
        if inspection.core_role == "ACTIVE_CORE" and inspection.deployment_state is DeploymentState.NATIVE_ACTIVE:
            return self._active_receipt(request, state, completion)
        if inspection.deployment_state is not DeploymentState.CUTOVER_PENDING:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_UNEXPECTED_CORE_STAGE")
        return activate_core(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            expected_witness=witness,
            selector_generation=state.generation,
            selector_witness_digest=state.core_witness_digest or "",
            operation_key=self._key(request, "core-active"),
            completion_witness=completion,
        )

    def activate_external_selector(self, request: OfflineCutoverRequest) -> SelectorState:
        """P7: activate external NATIVE authority last, from exact active evidence."""

        descriptor, completion = self._completed_descriptor(request)
        state = self._selector_state(request)
        if state.deployment_state is DeploymentState.NATIVE_ACTIVE:
            self._require_native_agreement(request, descriptor, completion)
            return state
        self._require_pending(request, descriptor, state, core_state=DeploymentState.NATIVE_ACTIVE)
        receipt = self._active_receipt(request, state, completion)
        result = activate_selector_native(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            core_result=receipt,
            expected_generation=state.generation,
            operation_key=self._key(request, "external-active"),
        )
        self._require_native_agreement(request, descriptor, completion)
        return result

    def safe_pending_abort(self, request: OfflineCutoverRequest) -> SelectorState:
        """Abort an unactivated P5 core; post-active rollback remains impossible."""

        descriptor, completion = self._completed_descriptor(request)
        state = self._selector_state(request)
        if state.deployment_state is DeploymentState.LEGACY_ACTIVE:
            inspection = self._inspection(request)
            if (
                inspection.core_role != "STAGING"
                or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE
                or inspection.ever_active
            ):
                raise OfflineCutoverRefused("OFFLINE_CUTOVER_ABORT_STATE_MISMATCH")
            return state
        self._require_pending(request, descriptor, state)
        inspection = self._inspection(request)
        if inspection.deployment_state is DeploymentState.LEGACY_ACTIVE:
            if inspection.witness is None or inspection.latest_maintenance_id is None or inspection.ever_active:
                raise OfflineCutoverRefused("OFFLINE_CUTOVER_ABORT_EVIDENCE_MISMATCH")
            aborted = CoreMaintenanceResult(
                transition_kind="ABORT_CUTOVER_PENDING",
                maintenance_id=inspection.latest_maintenance_id,
                witness=inspection.witness,
                selector_generation=state.generation,
                selector_witness_digest=state.core_witness_digest or "",
                safe_abort_proven=True,
            )
        elif inspection.deployment_state is DeploymentState.CUTOVER_PENDING and inspection.witness is not None:
            aborted = abort_cutover_pending(
                data_root=request.root,
                core_relative_path=request.core_relative_path,
                expected_witness=inspection.witness,
                selector_generation=state.generation,
                selector_witness_digest=state.core_witness_digest or "",
                operation_key=self._key(request, "core-abort"),
            )
        else:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_ABORT_PENDING_WITNESS_MISSING")
        result = abort_selector_pending(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            core_result=aborted,
            expected_generation=state.generation,
            operation_key=self._key(request, "external-abort"),
        )
        if result.deployment_state is not DeploymentState.LEGACY_ACTIVE:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_ABORT_DID_NOT_RESTORE_LEGACY")
        return result

    def current_stage(self, request: OfflineCutoverRequest) -> OfflineCutoverStage:
        """Derive the recoverable stage from authority records; never guess it."""

        descriptor = self._descriptor(request)
        inspection = self._inspection(request)
        try:
            state = self._selector_state(request)
        except OfflineCutoverRefused:
            return OfflineCutoverStage.PREPARED
        if state.deployment_state is DeploymentState.LEGACY_ACTIVE:
            return OfflineCutoverStage.PREPARED if descriptor.admission_identity_digest else OfflineCutoverStage.LEGACY
        if state.deployment_state is DeploymentState.NATIVE_ACTIVE:
            completion = descriptor.completed_admission_witness()
            self._require_native_agreement(request, descriptor, completion)
            return OfflineCutoverStage.NATIVE_ACTIVE
        self._require_pending(request, descriptor, state)
        if inspection.deployment_state is DeploymentState.NATIVE_ACTIVE:
            self._completed_descriptor(request)
            return OfflineCutoverStage.CORE_ACTIVE_EXTERNAL_PENDING
        if inspection.deployment_state is DeploymentState.CUTOVER_PENDING:
            self._completed_descriptor(request)
            return OfflineCutoverStage.CORE_PENDING
        if descriptor.state.value == "ADMISSION_COMPLETE":
            self._completed_descriptor(request)
            return OfflineCutoverStage.ADMISSION_COMPLETE
        return OfflineCutoverStage.EXTERNAL_PENDING

    def _prepare(self, request: OfflineCutoverRequest) -> ExistingWorkspaceNativeMultiScopePreparedAdmission:
        self._require_writer_drain(request)
        try:
            prepared = self._admission_service.prepare(request.admission_request)
        except (ExistingWorkspaceMultiScopeAdmissionRefused, ValueError) as exc:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_PREPARATION_REFUSED") from exc
        if prepared.admission_identity_digest != prepared.descriptor.admission_identity_digest:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_PREPARATION_IDENTITY_MISMATCH")
        if prepared.native_core_id != prepared.descriptor.native_core_id:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_PREPARATION_CORE_MISMATCH")
        return prepared

    def _completed_descriptor(
        self, request: OfflineCutoverRequest,
    ) -> tuple[ExistingWorkspaceNativeMultiScopeDescriptor, AdmissionCompletionWitness]:
        prepared = self._prepare(request)
        descriptor = prepared.descriptor
        try:
            completion = descriptor.completed_admission_witness()
        except ExistingWorkspaceMultiScopeAdmissionRefused as exc:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_COMPLETION_REQUIRED") from exc
        if (
            completion.admission_identity_digest != prepared.admission_identity_digest
            or completion.native_core_id != prepared.native_core_id
            or completion.profile_digest != request.effective_profile.digest
        ):
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_COMPLETION_BINDING_MISMATCH")
        return descriptor, completion

    def _ensure_selector(self, request: OfflineCutoverRequest) -> SelectorState:
        try:
            return self._selector_state(request)
        except OfflineCutoverRefused:
            try:
                establish_selector_era(data_root=request.root)
                return initialize_selector(
                    data_root=request.root,
                    operation_key=self._key(request, "selector-init"),
                )
            except DeploymentAuthorityError as exc:
                raise OfflineCutoverRefused("OFFLINE_CUTOVER_SELECTOR_INITIALIZATION_REFUSED") from exc

    def _selector_state(self, request: OfflineCutoverRequest) -> SelectorState:
        try:
            return read_selector_state(data_root=request.root)
        except DeploymentAuthorityError as exc:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_SELECTOR_UNAVAILABLE") from exc

    def _descriptor(self, request: OfflineCutoverRequest) -> ExistingWorkspaceNativeMultiScopeDescriptor:
        return self._prepare(request).descriptor

    def _inspection(self, request: OfflineCutoverRequest) -> CoreDeploymentInspection:
        try:
            return inspect_contained_core_deployment(
                data_root=request.root,
                core_relative_path=request.core_relative_path,
            )
        except DeploymentAuthorityError as exc:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_CORE_INSPECTION_REFUSED") from exc

    def _inert_core(
        self,
        request: OfflineCutoverRequest,
        descriptor: ExistingWorkspaceNativeMultiScopeDescriptor,
    ) -> CoreDeploymentInspection:
        inspection = self._inspection(request)
        if (
            inspection.core_id != descriptor.native_core_id
            or inspection.core_role != "STAGING"
            or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE
            or inspection.witness is not None
            or inspection.ever_active
        ):
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_PREPARED_CORE_NOT_INERT")
        return inspection

    def _require_pending(
        self,
        request: OfflineCutoverRequest,
        descriptor: ExistingWorkspaceNativeMultiScopeDescriptor,
        state: SelectorState,
        *,
        core_state: DeploymentState | None = None,
    ) -> None:
        inspection = self._inspection(request)
        if (
            state.deployment_state is not DeploymentState.CUTOVER_PENDING
            or state.core_id != descriptor.native_core_id
            or state.core_relative_path != request.core_relative_path
            or state.descriptor_digest != descriptor.admission_identity_digest
            or state.profile_digest != request.effective_profile.digest
            or inspection.core_id != descriptor.native_core_id
        ):
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_EXTERNAL_PENDING_BINDING_MISMATCH")
        if core_state is not None and inspection.deployment_state is not core_state:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_UNEXPECTED_CORE_STAGE")
        resolution = resolve_deployment_agreement(
            data_root=request.root, effective_profile=request.effective_profile,
        )
        if resolution.mode is not DeploymentResolutionMode.MAINTENANCE_ONLY:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_PENDING_PUBLIC_FENCE_MISSING")

    def _active_receipt(
        self,
        request: OfflineCutoverRequest,
        state: SelectorState,
        completion: AdmissionCompletionWitness,
    ) -> CoreMaintenanceResult:
        inspection = self._inspection(request)
        if (
            inspection.core_role != "ACTIVE_CORE"
            or inspection.deployment_state is not DeploymentState.NATIVE_ACTIVE
            or inspection.witness is None
            or inspection.latest_maintenance_id is None
            or inspection.activation_completion_witness != completion
        ):
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_ACTIVE_CORE_EVIDENCE_MISMATCH")
        return CoreMaintenanceResult(
            transition_kind="ACTIVATE_CORE",
            maintenance_id=inspection.latest_maintenance_id,
            witness=inspection.witness,
            selector_generation=state.generation,
            selector_witness_digest=state.core_witness_digest or "",
            completion_witness=completion,
        )

    def _require_native_agreement(
        self,
        request: OfflineCutoverRequest,
        descriptor: ExistingWorkspaceNativeMultiScopeDescriptor,
        completion: AdmissionCompletionWitness,
    ) -> None:
        resolution = resolve_deployment_agreement(
            data_root=request.root, effective_profile=request.effective_profile,
        )
        if resolution.mode is not DeploymentResolutionMode.NATIVE_AGREEMENT:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_NATIVE_AGREEMENT_MISSING")
        state = resolution.selector_state
        witness = resolution.core_witness
        if (
            state is None
            or witness is None
            or state.core_id != completion.native_core_id
            or state.descriptor_digest != completion.admission_identity_digest
            or state.profile_digest != completion.profile_digest
            or witness.descriptor_digest != completion.admission_identity_digest
            or witness.profile_digest != completion.profile_digest
        ):
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_NATIVE_AGREEMENT_MISMATCH")

    @staticmethod
    def _require_writer_drain(request: OfflineCutoverRequest) -> None:
        if request.writer_drain.workspace_id != request.admission_request.workspace_id:
            raise OfflineCutoverRefused("OFFLINE_CUTOVER_WRITER_DRAIN_REQUIRED")

    @staticmethod
    def _key(request: OfflineCutoverRequest, phase: str) -> str:
        return f"B5-A5:{request.operator_cutover_key}:{phase}"


__all__ = [
    "OfflineCutoverController",
    "OfflineCutoverEvidence",
    "OfflineCutoverRefused",
    "OfflineCutoverRequest",
    "OfflineCutoverStage",
    "OfflineWriterDrainWitness",
]
