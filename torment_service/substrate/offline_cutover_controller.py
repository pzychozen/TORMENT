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
from uuid import UUID

from .connection import open_existing_native_core_connection
from .deployment_core_maintenance import (
    CoreDeploymentInspection,
    CoreMaintenanceResult,
    abort_cutover_pending,
    activate_core,
    enter_cutover_pending,
    inspect_contained_core_deployment,
    read_root_disposition_execution_receipt,
    record_root_disposition_execution,
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
    RootAdmissionCompletionWitness,
    SelectorState,
)
from .errors import DeploymentAuthorityError, SubstrateConfigurationError
from .migration.root_admission_description import RootNativeProductionAdmissionDescription
from .migration.root_normalization import (
    NativeRootWideNormalizationService,
    RootNormalizationRequest,
    RootNormalizationResult,
)
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
from .root_blocker5_binding import (
    RootAdmissionEnvelope,
    RootBlocker5BindingRefused,
    RootCompletionVerification,
    RootGeometryDispositionPlan,
    RootWriterFreezeWitness,
    SyntheticRootDispositionAdapter,
    build_root_admission_envelope,
    execute_synthetic_root_disposition_plan,
    frozen_root_geometry_disposition_plan,
    verify_root_completion,
)
from .root_profile import RootProfileGenerationRef
from .runtime_binding import NativeMemoryRuntimeScope


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
class RootOfflineCutoverRequest:
    """Synthetic root-wide form using the existing offline controller authority."""

    data_root: Path
    description: RootNativeProductionAdmissionDescription
    normalization_request: RootNormalizationRequest
    effective_profile: QualifiedDeploymentProfile
    root_profile: RootProfileGenerationRef
    runtime_scopes: tuple[NativeMemoryRuntimeScope, ...]
    writer_freeze: RootWriterFreezeWitness
    operator_cutover_key: str
    geometry_disposition_plan: RootGeometryDispositionPlan | None = None

    def __post_init__(self) -> None:
        root = Path(self.data_root).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("root offline cutover data_root must already exist")
        if not isinstance(self.description, RootNativeProductionAdmissionDescription):
            raise ValueError("root offline cutover description must be typed")
        if not isinstance(self.normalization_request, RootNormalizationRequest):
            raise ValueError("root offline cutover normalization request must be typed")
        if self.normalization_request.description != self.description:
            raise ValueError("normalization request must bind the exact root description")
        if Path(self.normalization_request.data_root).expanduser().resolve() != root:
            raise ValueError("normalization request names another data root")
        if not isinstance(self.effective_profile, QualifiedDeploymentProfile):
            raise ValueError("root offline cutover profile must be typed")
        if not isinstance(self.root_profile, RootProfileGenerationRef):
            raise ValueError("root offline cutover root profile must be typed")
        if not isinstance(self.runtime_scopes, tuple) or any(
            not isinstance(item, NativeMemoryRuntimeScope) for item in self.runtime_scopes
        ):
            raise ValueError("root offline cutover runtime scopes must be typed")
        if not isinstance(self.writer_freeze, RootWriterFreezeWitness):
            raise ValueError("root offline cutover writer freeze must be typed")
        if self.writer_freeze.data_root_identity != self.description.data_root_identity:
            raise ValueError("root writer freeze names another root")
        if not isinstance(self.operator_cutover_key, str) or not self.operator_cutover_key or len(self.operator_cutover_key) > 160:
            raise ValueError("root operator_cutover_key must be bounded non-empty text")
        if self.geometry_disposition_plan is not None and not isinstance(
            self.geometry_disposition_plan, RootGeometryDispositionPlan,
        ):
            raise ValueError("root geometry disposition plan must be typed")
        core = Path(self.normalization_request.native_core_database_path).expanduser().resolve()
        core_root = root / "substrate" / "cores"
        try:
            relative = core.relative_to(core_root)
        except ValueError as exc:
            raise ValueError("root normalization core must be contained by data_root/substrate/cores") from exc
        if relative.parent != Path(".") or relative.suffix.lower() != ".db":
            raise ValueError("root normalization core must be one contained .db filename")
        if self.normalization_request.expected_native_core_id != self.root_profile.core_id:
            raise ValueError("root normalization and root profile name different cores")

    @property
    def root(self) -> Path:
        return Path(self.data_root).expanduser().resolve()

    @property
    def native_staging_core_id(self) -> UUID:
        return self.normalization_request.expected_native_core_id

    @property
    def core_relative_path(self) -> str:
        return Path(self.normalization_request.native_core_database_path).expanduser().resolve().name

    @property
    def resolved_geometry_disposition_plan(self) -> RootGeometryDispositionPlan:
        return self.geometry_disposition_plan or frozen_root_geometry_disposition_plan(
            external_owner_observation_digest=self.description.external_owner_observation_digest,
        )


@dataclass(frozen=True)
class RootOfflineCutoverEvidence:
    """Read-only root bridge evidence derived from the same controller lifecycle."""

    stage: OfflineCutoverStage
    envelope: RootAdmissionEnvelope
    selector_state: SelectorState | None
    core: CoreDeploymentInspection
    normalization: RootNormalizationResult | None = None
    completion_verification: RootCompletionVerification | None = None


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

    def prepare_root(self, request: RootOfflineCutoverRequest) -> RootOfflineCutoverEvidence:
        """P1 for the generalized form: freeze only root evidence, no authority."""

        envelope = self._root_envelope(request)
        inspection = self._root_inert_core(request)
        resolution = resolve_deployment_agreement(
            data_root=request.root, effective_profile=request.effective_profile,
        )
        if resolution.mode is not DeploymentResolutionMode.LEGACY_PUBLIC:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_PREPARE_REQUIRES_LEGACY_AUTHORITY")
        return RootOfflineCutoverEvidence(
            OfflineCutoverStage.PREPARED,
            envelope,
            resolution.selector_state,
            inspection,
        )

    def enter_root_external_pending(
        self, request: RootOfflineCutoverRequest,
    ) -> RootOfflineCutoverEvidence:
        """P2: bind the root envelope in the existing selector pending state."""

        envelope = self._root_envelope(request)
        self._root_inert_core(request)
        state = self._ensure_selector(request)
        if state.deployment_state is DeploymentState.LEGACY_ACTIVE:
            state = begin_cutover_pending(
                data_root=request.root,
                core_relative_path=request.core_relative_path,
                descriptor_digest=envelope.digest,
                profile=request.effective_profile,
                expected_generation=state.generation,
                operation_key=self._key(request, "root-external-pending"),
            )
        self._require_root_pending(
            request, envelope, state, core_state=DeploymentState.LEGACY_ACTIVE,
        )
        return RootOfflineCutoverEvidence(
            OfflineCutoverStage.EXTERNAL_PENDING,
            envelope,
            state,
            self._inspection(request),
        )

    def normalize_root_under_external_fence(
        self,
        request: RootOfflineCutoverRequest,
        *,
        _test_interrupt_after: object | None = None,
    ) -> RootNormalizationResult:
        """P3: run the established root normalizer under maintenance-only authority."""

        envelope = self._root_envelope(request)
        state = self._selector_state(request)
        self._require_root_pending(
            request, envelope, state, core_state=DeploymentState.LEGACY_ACTIVE,
        )
        try:
            with open_existing_native_core_connection(
                request.normalization_request.native_core_database_path,
            ) as opened:
                return NativeRootWideNormalizationService(opened.connection).normalize(
                    request.normalization_request,
                    _test_interrupt_after=_test_interrupt_after,  # type: ignore[arg-type]
                )
        except RootBlocker5BindingRefused:
            raise
        except Exception as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_NORMALIZATION_REFUSED") from exc

    def verify_root_completion(
        self,
        request: RootOfflineCutoverRequest,
        normalization: RootNormalizationResult,
    ) -> RootOfflineCutoverEvidence:
        """P4: recheck manifest/census/membership before constructing v2 evidence."""

        envelope = self._root_envelope(request)
        state = self._selector_state(request)
        self._require_root_pending(request, envelope, state)
        inspection = self._inspection(request)
        if inspection.deployment_state not in {
            DeploymentState.LEGACY_ACTIVE,
            DeploymentState.CUTOVER_PENDING,
            DeploymentState.NATIVE_ACTIVE,
        }:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_COMPLETION_CORE_STAGE_MISMATCH")
        verification = self._root_verification(request, envelope, normalization)
        return RootOfflineCutoverEvidence(
            OfflineCutoverStage.ADMISSION_COMPLETE,
            envelope,
            state,
            inspection,
            normalization,
            verification,
        )

    def enter_root_core_pending(
        self,
        request: RootOfflineCutoverRequest,
        normalization: RootNormalizationResult,
    ) -> CoreMaintenanceResult:
        """P5: retain the existing core transition with the root envelope digest."""

        evidence = self.verify_root_completion(request, normalization)
        assert evidence.completion_verification is not None and evidence.selector_state is not None
        state = evidence.selector_state
        inspection = evidence.core
        if inspection.deployment_state is DeploymentState.CUTOVER_PENDING:
            if inspection.witness is None or inspection.core_role != "STAGING":
                raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_CORE_PENDING_EVIDENCE_MISMATCH")
            return CoreMaintenanceResult(
                transition_kind="ENTER_CUTOVER_PENDING",
                maintenance_id=inspection.latest_maintenance_id,  # type: ignore[arg-type]
                witness=inspection.witness,
                selector_generation=state.generation,
                selector_witness_digest=state.core_witness_digest or "",
            )
        predecessor = staging_legacy_witness(
            inspection,
            descriptor_digest=evidence.envelope.digest,
            profile_digest=request.effective_profile.digest,
        )
        return enter_cutover_pending(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            expected_witness=predecessor,
            selector_generation=state.generation,
            selector_witness_digest=state.core_witness_digest or "",
            operation_key=self._key(request, "root-core-pending"),
        )

    def activate_root_core(
        self,
        request: RootOfflineCutoverRequest,
        normalization: RootNormalizationResult,
    ) -> CoreMaintenanceResult:
        """P6: immediately re-verify the manifest then commit the existing core PONR."""

        # This second verification is the required immediately-pre-P6 manifest
        # recheck.  It also rejects census or membership drift after P4.
        evidence = self.verify_root_completion(request, normalization)
        assert evidence.completion_verification is not None and evidence.selector_state is not None
        completion = evidence.completion_verification.completion_witness
        state = evidence.selector_state
        inspection = evidence.core
        if inspection.core_role == "ACTIVE_CORE" and inspection.deployment_state is DeploymentState.NATIVE_ACTIVE:
            return self._root_active_receipt(request, state, completion)
        if inspection.deployment_state is not DeploymentState.CUTOVER_PENDING or inspection.witness is None:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_CORE_PENDING_REQUIRED")
        return activate_core(
            data_root=request.root,
            core_relative_path=request.core_relative_path,
            expected_witness=inspection.witness,
            selector_generation=state.generation,
            selector_witness_digest=state.core_witness_digest or "",
            operation_key=self._key(request, "root-core-active"),
            completion_witness=completion,
        )

    def execute_root_disposition_plan(
        self,
        request: RootOfflineCutoverRequest,
        normalization: RootNormalizationResult,
        *,
        adapter: SyntheticRootDispositionAdapter,
    ) -> RootDispositionExecutionReceipt:
        """Post-P6 only: create or recover the immutable root receipt."""

        envelope = self._root_envelope(request)
        verification = self._root_verification(request, envelope, normalization)
        state = self._selector_state(request)
        active = self._root_active_receipt(request, state, verification.completion_witness)
        del active
        try:
            existing = read_root_disposition_execution_receipt(
                data_root=request.root,
                core_relative_path=request.core_relative_path,
                completion_witness=verification.completion_witness,
            )
        except DeploymentAuthorityError as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_DISPOSITION_EVIDENCE_REFUSED") from exc
        if existing is not None:
            return existing
        try:
            receipt = execute_synthetic_root_disposition_plan(
                envelope=envelope, adapter=adapter,
            )
            return record_root_disposition_execution(
                data_root=request.root,
                core_relative_path=request.core_relative_path,
                completion_witness=verification.completion_witness,
                receipt=receipt,
                operation_key=self._key(request, "root-disposition-execution"),
            )
        except DeploymentAuthorityError as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_DISPOSITION_EXECUTION_REFUSED") from exc

    def activate_root_external_selector(
        self,
        request: RootOfflineCutoverRequest,
        normalization: RootNormalizationResult,
    ) -> SelectorState:
        """P7: selector activation requires the exact durable post-P6 receipt."""

        envelope = self._root_envelope(request)
        verification = self._root_verification(request, envelope, normalization)
        state = self._selector_state(request)
        if state.deployment_state is DeploymentState.NATIVE_ACTIVE:
            self._require_root_native_agreement(request, verification.completion_witness)
            return state
        active = self._root_active_receipt(request, state, verification.completion_witness)
        try:
            receipt = read_root_disposition_execution_receipt(
                data_root=request.root,
                core_relative_path=request.core_relative_path,
                completion_witness=verification.completion_witness,
            )
        except DeploymentAuthorityError as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_P7_RECEIPT_REFUSED") from exc
        if receipt is None:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_P7_RECEIPT_REQUIRED")
        try:
            result = activate_selector_native(
                data_root=request.root,
                core_relative_path=request.core_relative_path,
                core_result=active,
                expected_generation=state.generation,
                operation_key=self._key(request, "root-external-active"),
                disposition_execution_receipt_digest=receipt.digest,
            )
        except DeploymentAuthorityError as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_P7_REFUSED") from exc
        self._require_root_native_agreement(request, verification.completion_witness)
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

    def root_current_stage(self, request: RootOfflineCutoverRequest) -> OfflineCutoverStage:
        """Recover root lifecycle state from the existing selector/core authorities."""

        envelope = self._root_envelope(request)
        inspection = self._inspection(request)
        try:
            state = self._selector_state(request)
        except OfflineCutoverRefused:
            return OfflineCutoverStage.PREPARED
        if state.deployment_state is DeploymentState.LEGACY_ACTIVE:
            self._root_inert_core(request)
            return OfflineCutoverStage.PREPARED
        if state.deployment_state is DeploymentState.NATIVE_ACTIVE:
            if (
                state.core_id != request.native_staging_core_id
                or state.descriptor_digest != envelope.digest
                or inspection.core_role != "ACTIVE_CORE"
                or inspection.deployment_state is not DeploymentState.NATIVE_ACTIVE
            ):
                raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_NATIVE_RECOVERY_MISMATCH")
            return OfflineCutoverStage.NATIVE_ACTIVE
        self._require_root_pending(request, envelope, state)
        if inspection.deployment_state is DeploymentState.NATIVE_ACTIVE:
            return OfflineCutoverStage.CORE_ACTIVE_EXTERNAL_PENDING
        if inspection.deployment_state is DeploymentState.CUTOVER_PENDING:
            return OfflineCutoverStage.CORE_PENDING
        return OfflineCutoverStage.EXTERNAL_PENDING

    def _root_envelope(self, request: RootOfflineCutoverRequest) -> RootAdmissionEnvelope:
        try:
            with open_existing_native_core_connection(
                request.normalization_request.native_core_database_path,
            ) as opened:
                return build_root_admission_envelope(
                    data_root=request.root,
                    description=request.description,
                    writer_freeze=request.writer_freeze,
                    geometry_disposition_plan=request.resolved_geometry_disposition_plan,
                    effective_profile=request.effective_profile,
                    native_staging_core_id=request.native_staging_core_id,
                    root_profile=request.root_profile,
                    runtime_scopes=request.runtime_scopes,
                    connection=opened.connection,
                )
        except RootBlocker5BindingRefused as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_ENVELOPE_REFUSED") from exc
        except Exception as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_ENVELOPE_UNAVAILABLE") from exc

    def _root_verification(
        self,
        request: RootOfflineCutoverRequest,
        envelope: RootAdmissionEnvelope,
        normalization: RootNormalizationResult,
    ) -> RootCompletionVerification:
        try:
            with open_existing_native_core_connection(
                request.normalization_request.native_core_database_path,
            ) as opened:
                verification = verify_root_completion(
                    data_root=request.root,
                    envelope=envelope,
                    normalization=normalization,
                    runtime_scopes=request.runtime_scopes,
                    connection=opened.connection,
                )
        except RootBlocker5BindingRefused as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_COMPLETION_REFUSED") from exc
        except Exception as exc:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_COMPLETION_UNAVAILABLE") from exc
        if verification.completion_witness.admission_identity_digest != envelope.digest:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_COMPLETION_ENVELOPE_MISMATCH")
        return verification

    def _root_inert_core(self, request: RootOfflineCutoverRequest) -> CoreDeploymentInspection:
        inspection = self._inspection(request)
        if (
            inspection.core_id != request.native_staging_core_id
            or inspection.core_role != "STAGING"
            or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE
            or inspection.witness is not None
            or inspection.ever_active
        ):
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_PREPARED_CORE_NOT_INERT")
        return inspection

    def _require_root_pending(
        self,
        request: RootOfflineCutoverRequest,
        envelope: RootAdmissionEnvelope,
        state: SelectorState,
        *,
        core_state: DeploymentState | None = None,
    ) -> None:
        inspection = self._inspection(request)
        if (
            state.deployment_state is not DeploymentState.CUTOVER_PENDING
            or state.core_id != request.native_staging_core_id
            or state.core_relative_path != request.core_relative_path
            or state.descriptor_digest != envelope.digest
            or state.profile_digest != request.effective_profile.digest
            or inspection.core_id != request.native_staging_core_id
        ):
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_EXTERNAL_PENDING_BINDING_MISMATCH")
        if core_state is not None and inspection.deployment_state is not core_state:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_UNEXPECTED_CORE_STAGE")
        resolution = resolve_deployment_agreement(
            data_root=request.root, effective_profile=request.effective_profile,
        )
        if resolution.mode is not DeploymentResolutionMode.MAINTENANCE_ONLY:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_PENDING_PUBLIC_FENCE_MISSING")

    def _root_active_receipt(
        self,
        request: RootOfflineCutoverRequest,
        state: SelectorState,
        completion: RootAdmissionCompletionWitness,
    ) -> CoreMaintenanceResult:
        inspection = self._inspection(request)
        if (
            inspection.core_role != "ACTIVE_CORE"
            or inspection.deployment_state is not DeploymentState.NATIVE_ACTIVE
            or inspection.witness is None
            or inspection.latest_maintenance_id is None
            or inspection.activation_completion_witness != completion
        ):
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_ACTIVE_CORE_EVIDENCE_MISMATCH")
        return CoreMaintenanceResult(
            transition_kind="ACTIVATE_CORE",
            maintenance_id=inspection.latest_maintenance_id,
            witness=inspection.witness,
            selector_generation=state.generation,
            selector_witness_digest=state.core_witness_digest or "",
            completion_witness=completion,
        )

    def _require_root_native_agreement(
        self,
        request: RootOfflineCutoverRequest,
        completion: RootAdmissionCompletionWitness,
    ) -> None:
        resolution = resolve_deployment_agreement(
            data_root=request.root, effective_profile=request.effective_profile,
        )
        if resolution.mode is not DeploymentResolutionMode.NATIVE_AGREEMENT:
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_NATIVE_AGREEMENT_MISSING")
        state = resolution.selector_state
        witness = resolution.core_witness
        if (
            state is None
            or witness is None
            or state.core_id != completion.native_staging_core_id
            or state.descriptor_digest != completion.root_admission_envelope_digest
            or state.profile_digest != completion.qualified_deployment_profile_digest
            or witness.descriptor_digest != completion.root_admission_envelope_digest
            or witness.profile_digest != completion.qualified_deployment_profile_digest
        ):
            raise OfflineCutoverRefused("ROOT_OFFLINE_CUTOVER_NATIVE_AGREEMENT_MISMATCH")

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
    "RootOfflineCutoverEvidence",
    "RootOfflineCutoverRequest",
]
