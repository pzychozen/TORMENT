from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
import copy
from datetime import datetime
from datetime import timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any
from typing import Callable

import validate_windows_same_volume_no_replace_promotion_v0_1 as validation


VERSION = "v0.1"
EVIDENCE_BODY_SCHEMA = (
    "torment.brainvision.blocker2.r4.ordered_directory_creation_evidence_body.v0.1"
)

GOVERNED_REQUIRED_ROOT = r"C:\TORMENT"
GOVERNED_COMPONENT_1 = r"C:\TORMENT\brainvision_authoritative_inputs"
GOVERNED_COMPONENT_2 = (
    r"C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3"
)
GOVERNED_COMPONENT_3 = (
    r"C:\TORMENT\brainvision_authoritative_inputs"
    r"\blocker2_s3b_v0_3\r4_prepare_paths"
)
GOVERNED_EVIDENCE_RECORD_PATH = (
    r"C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3"
    r"\r4_prepare_paths\r4_prepare_paths_path_creation_evidence_record_v0_1"
    r".canonical.json"
)
GOVERNED_CANONICAL_INPUT_PATH = (
    r"C:\TORMENT\brainvision_authoritative_inputs\blocker2_s3b_v0_3"
    r"\r4_prepare_paths\r4_prepare_paths_authorization_input_v0_1.canonical.json"
)
KNOWN_INERT_UNTRACKED_DRAFT = (
    "docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_PREPARE_PATHS_"
    "FRESH_ACCEPTED_INVOCATION_HEAD_NON_COMMIT_ESTABLISHMENT_DESIGN_v0.1.md"
)

TRI_TRUE = "TRUE"
TRI_FALSE = "FALSE"
TRI_INDETERMINATE = "INDETERMINATE"
INDEX_LOCK_ABSENT = "ABSENT"
INDEX_LOCK_PRESENT = "PRESENT"
INDEX_LOCK_INDETERMINATE = "INDETERMINATE"
_AUTO_INDEX_LOCK_STATE = "AUTO"
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
)

CORRECTED_PATH_CREATION_NOT_STARTED = "CORRECTED_PATH_CREATION_NOT_STARTED"
CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE = (
    "CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE"
)
CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION = (
    "CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION"
)
CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT = (
    "CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT"
)

CLASSIFICATION_COMMITTED_TERMINAL = "COMMITTED_TERMINAL"
CLASSIFICATION_DERIVED_NON_TERMINAL = "DERIVED_NON_TERMINAL"

EXECUTION_MODE_AUTHORITATIVE_DEFAULT = "AUTHORITATIVE_DEFAULT_ADAPTERS"
EXECUTION_MODE_TEST_OR_CUSTOM = "TEST_OR_CUSTOM_ADAPTERS"
EXECUTION_MODE_UNSUPPORTED_CUSTOM = "UNSUPPORTED_CUSTOM_CONFIGURATION"

DETAIL_PATH_MISMATCH = "path mismatch"
DETAIL_PARENT_ABSENT = "parent absent"
DETAIL_CHILD_PRE_EXISTS = "child pre-exists"
DETAIL_REPARSE_OR_ALIAS = "reparse or alias involvement"
DETAIL_UNEXPECTED_INTERMEDIATE = "unexpected intermediate creation"
DETAIL_ORDER_VIOLATION = "order violation"
DETAIL_VALIDATION_FAILURE = "validation failure"

PRIMITIVE_IDENTITY = "python-os-mkdir-raw-win32-path-one-component-create-v0.1"
PARENT_HANDLE_SHARE_LIMITATION = (
    "default Windows handle path uses FILE_SHARE_READ|FILE_SHARE_WRITE|"
    "FILE_SHARE_DELETE where the reviewed helper supplies the handle; the held "
    "handle is evidence continuity and must not be claimed to prevent rename or deletion"
)


@dataclass(frozen=True)
class PathModel:
    required_root: str
    components: tuple[str, str, str]
    evidence_record_path: str
    canonical_input_path: str

    def parents(self) -> tuple[str, str, str]:
        return (
            self.required_root,
            self.components[0],
            self.components[1],
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "required_root": self.required_root,
            "components": list(self.components),
            "evidence_record_path": self.evidence_record_path,
            "canonical_input_path": self.canonical_input_path,
        }


GOVERNED_PATH_MODEL = PathModel(
    required_root=GOVERNED_REQUIRED_ROOT,
    components=(GOVERNED_COMPONENT_1, GOVERNED_COMPONENT_2, GOVERNED_COMPONENT_3),
    evidence_record_path=GOVERNED_EVIDENCE_RECORD_PATH,
    canonical_input_path=GOVERNED_CANONICAL_INPUT_PATH,
)


@dataclass(frozen=True)
class AuthorityAssertions:
    window_open: bool
    authority_a_active: bool
    authority_b_active: bool
    authority_c_active: bool
    authority_d_active: bool
    authority_e_active: bool


@dataclass(frozen=True)
class RepositoryState:
    branch: str
    head: str
    origin_main: str
    index_lock_present: bool
    index_lock_state: str = _AUTO_INDEX_LOCK_STATE
    index_lock_observation_error: dict[str, Any] | None = None
    staged_changes: tuple[str, ...] = ()
    unstaged_tracked_changes: tuple[str, ...] = ()
    unmerged_entries: tuple[str, ...] = ()
    untracked_entries: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.index_lock_state == _AUTO_INDEX_LOCK_STATE:
            object.__setattr__(
                self,
                "index_lock_state",
                INDEX_LOCK_PRESENT if self.index_lock_present else INDEX_LOCK_ABSENT,
            )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ObjectIdentity:
    volume_serial_number: int
    file_index_high: int
    file_index_low: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class VolumeProfile:
    drive_type: int
    filesystem_name: str
    volume_serial_number: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NativeError:
    native_error_code: int | None
    native_error_name: str | None
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DirectoryHandleEvidence:
    raw_path: str
    identity: ObjectIdentity
    volume_profile: VolumeProfile
    is_directory: bool
    is_reparse_point: bool
    attributes_source: str
    native_handle_source: str
    share_limitations: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "raw_path": self.raw_path,
            "identity": self.identity.as_dict(),
            "volume_profile": self.volume_profile.as_dict(),
            "is_directory": self.is_directory,
            "is_reparse_point": self.is_reparse_point,
            "attributes_source": self.attributes_source,
            "native_handle_source": self.native_handle_source,
            "share_limitations": self.share_limitations,
        }


@dataclass
class DirectoryHandle:
    evidence: DirectoryHandleEvidence
    close_callback: Callable[[], None] | None = None
    closed: bool = False

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        if self.close_callback is not None:
            self.close_callback()


@dataclass(frozen=True)
class OpenDirectoryResult:
    opened: bool
    handle: DirectoryHandle | None = None
    error: NativeError | None = None


@dataclass(frozen=True)
class AbsenceResult:
    positively_absent: bool
    basis: str
    native_error_code: int | None = None
    native_error_name: str | None = None
    detail: str | None = None
    pre_existing_kind: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HelperResult:
    classification: str
    classification_kind: str
    terminal: bool
    committed_detail_label: str | None
    derived_subreason: str | None
    authority_active: bool
    contact_started: bool
    opportunity_consumed: bool
    mutation_succeeded_count: int
    sequence_terminal: bool
    evidence_body: dict[str, Any]
    body_identity: dict[str, Any]
    authority_assertions_observed: dict[str, bool]
    required_authority_gate_satisfied: bool
    execution_mode: str


class R4DirectoryCreationError(RuntimeError):
    pass


class Win32DirectoryAdapter:
    """Windows native observation adapter for the R4 helper.

    The adapter uses the reviewed private helpers from the same research lane.
    Callers should still treat every indeterminate result as fail-closed.
    """

    def open_directory(self, raw_path: str) -> OpenDirectoryResult:
        if not validation._is_windows():
            return OpenDirectoryResult(
                opened=False,
                error=NativeError(None, "UNSUPPORTED_PLATFORM", "non-Windows platform"),
            )
        handle = validation._open_directory_handle(
            raw_path,
            desired_access=validation.FILE_READ_ATTRIBUTES,
        )
        if isinstance(handle, validation.NativePromotionOutcome):
            return OpenDirectoryResult(
                opened=False,
                error=NativeError(
                    handle.native_error_code,
                    handle.native_error_name,
                    handle.detail,
                ),
            )
        try:
            evidence = self._evidence_from_handle(raw_path, handle.handle)
        except OSError as exc:
            _close_private_handle(handle)
            return OpenDirectoryResult(
                opened=False,
                error=NativeError(
                    getattr(exc, "winerror", None) or getattr(exc, "errno", None),
                    _error_name(getattr(exc, "winerror", None) or getattr(exc, "errno", None)),
                    "directory handle evidence failed",
                ),
            )
        return OpenDirectoryResult(
            opened=True,
            handle=DirectoryHandle(
                evidence=evidence,
                close_callback=lambda: _close_private_handle(handle),
            ),
        )

    def check_absent(
        self,
        raw_path: str,
        *,
        allow_missing_ancestor: bool = False,
    ) -> AbsenceResult:
        if not validation._is_windows():
            return AbsenceResult(
                False,
                "unsupported_platform",
                detail="non-Windows platform",
            )
        handle = validation._open_directory_handle(
            raw_path,
            desired_access=validation.FILE_READ_ATTRIBUTES,
        )
        if not isinstance(handle, validation.NativePromotionOutcome):
            _close_private_handle(handle)
            return AbsenceResult(
                False,
                "handle_opened_target_pre_exists",
                pre_existing_kind="object",
            )
        code = handle.native_error_code
        name = handle.native_error_name
        if code == validation.ERROR_FILE_NOT_FOUND:
            return AbsenceResult(True, "final_child_absent", code, name)
        if code == validation.ERROR_PATH_NOT_FOUND and allow_missing_ancestor:
            return AbsenceResult(True, "ancestor_absent", code, name)
        if code == validation.ERROR_PATH_NOT_FOUND:
            return AbsenceResult(False, "parent_or_ancestor_absent", code, name)
        if code in (
            validation.ERROR_ACCESS_DENIED,
            validation.ERROR_SHARING_VIOLATION,
            validation.ERROR_INVALID_NAME,
        ):
            return AbsenceResult(False, "indeterminate_absence", code, name)
        return AbsenceResult(False, "unexpected_native_error", code, name)

    def _evidence_from_handle(self, raw_path: str, handle: int) -> DirectoryHandleEvidence:
        info = validation._BY_HANDLE_FILE_INFORMATION()
        kernel32 = validation._kernel32()
        if not kernel32.GetFileInformationByHandle(handle, validation.ctypes.byref(info)):
            code = int(kernel32.GetLastError())
            raise OSError(code, _error_name(code) or "GetFileInformationByHandle failed")
        identity = ObjectIdentity(
            volume_serial_number=int(info.dwVolumeSerialNumber),
            file_index_high=int(info.nFileIndexHigh),
            file_index_low=int(info.nFileIndexLow),
        )
        attributes = int(info.dwFileAttributes)
        drive_type, filesystem_name, volume_serial = validation._volume_information(
            Path(raw_path)
        )
        return DirectoryHandleEvidence(
            raw_path=raw_path,
            identity=identity,
            volume_profile=VolumeProfile(
                drive_type=drive_type,
                filesystem_name=filesystem_name,
                volume_serial_number=volume_serial,
            ),
            is_directory=bool(attributes & validation.FILE_ATTRIBUTE_DIRECTORY),
            is_reparse_point=bool(attributes & validation.FILE_ATTRIBUTE_REPARSE_POINT),
            attributes_source="GetFileInformationByHandle.dwFileAttributes",
            native_handle_source="CreateFileW(FILE_FLAG_OPEN_REPARSE_POINT)",
            share_limitations=PARENT_HANDLE_SHARE_LIMITATION,
        )


def execute_ordered_directory_creation(
    *,
    authority: AuthorityAssertions,
    accepted_invocation_head: str,
    path_model: PathModel = GOVERNED_PATH_MODEL,
    repository_reader: Callable[[], RepositoryState] | None = None,
    native_adapter: Any | None = None,
    creation_primitive: Callable[[str], None] | None = None,
    clock: Callable[[], str] | None = None,
    utc_clock: Callable[[], Any] | None = None,
    monotonic_clock: Callable[[], int] | None = None,
    allow_test_path_model: bool = False,
    prove_not_started_absence: bool = False,
    repository_root: str | Path = ".",
    expected_branch: str = "main",
    expected_untracked_entries: tuple[str, ...] = (KNOWN_INERT_UNTRACKED_DRAFT,),
) -> HelperResult:
    seam_injection = {
        "repository_reader": repository_reader is not None,
        "native_adapter": native_adapter is not None,
        "creation_primitive": creation_primitive is not None,
        "clock": clock is not None,
        "utc_clock": utc_clock is not None,
        "monotonic_clock": monotonic_clock is not None,
    }
    repository_reader_callable = repository_reader or (
        lambda: read_repository_state(repository_root)
    )
    native_adapter_object = native_adapter or Win32DirectoryAdapter()
    creation_primitive_callable = creation_primitive or _default_creation_primitive
    utc_clock_callable = utc_clock or clock or _default_utc_clock
    monotonic_clock_callable = monotonic_clock or _default_monotonic_clock
    execution_mode = _execution_mode(
        path_model=path_model,
        allow_test_path_model=allow_test_path_model,
        seam_injection=seam_injection,
    )
    execution_seams = _execution_seam_evidence(
        repository_reader_callable=repository_reader_callable,
        native_adapter_object=native_adapter_object,
        creation_primitive_callable=creation_primitive_callable,
        utc_clock_callable=utc_clock_callable,
        monotonic_clock_callable=monotonic_clock_callable,
        seam_injection=seam_injection,
        execution_mode=execution_mode,
        repository_root=repository_root,
    )
    default_seam_mismatch = None
    if execution_mode == EXECUTION_MODE_AUTHORITATIVE_DEFAULT:
        default_seam_mismatch = _authoritative_default_seam_identity_mismatch(
            execution_seams
        )
        if default_seam_mismatch is not None:
            execution_mode = EXECUTION_MODE_UNSUPPORTED_CUSTOM
            execution_seams["execution_mode"] = execution_mode
            execution_seams["authoritative_default_seam_identity_mismatch"] = (
                default_seam_mismatch
            )

    evidence_body = _initial_evidence_body(
        authority=authority,
        accepted_invocation_head=accepted_invocation_head,
        path_model=path_model,
        allow_test_path_model=allow_test_path_model,
        execution_seams=execution_seams,
    )
    contact_started = False
    mutation_succeeded_count = 0
    previous_child_identity: ObjectIdentity | None = None

    test_governed_failure = _test_mode_governed_path_failure(
        path_model,
        allow_test_path_model,
    )
    if test_governed_failure is not None:
        return _failure_result(
            evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            committed_detail_label=DETAIL_PATH_MISMATCH,
            derived_subreason=test_governed_failure,
            contact_started=contact_started,
            mutation_succeeded_count=mutation_succeeded_count,
        )

    if default_seam_mismatch is not None:
        return _failure_result(
            evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            committed_detail_label=DETAIL_VALIDATION_FAILURE,
            derived_subreason="authoritative_default_seam_identity_mismatch",
            contact_started=contact_started,
            mutation_succeeded_count=mutation_succeeded_count,
            diagnostic=default_seam_mismatch,
        )

    path_model_failure = _path_model_failure(path_model, allow_test_path_model)
    if path_model_failure is not None:
        return _failure_result(
            evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            committed_detail_label=DETAIL_PATH_MISMATCH,
            derived_subreason=path_model_failure,
            contact_started=contact_started,
            mutation_succeeded_count=mutation_succeeded_count,
        )

    validation_failure = _validate_all_raw_paths(path_model, allow_test_path_model)
    if validation_failure is not None:
        return _failure_result(
            evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            committed_detail_label=DETAIL_PATH_MISMATCH,
            derived_subreason=validation_failure,
            contact_started=contact_started,
            mutation_succeeded_count=mutation_succeeded_count,
        )

    precondition_failure = _authority_precondition_failure(authority)
    if precondition_failure is not None:
        return _failure_result(
            evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            committed_detail_label=DETAIL_VALIDATION_FAILURE,
            derived_subreason=precondition_failure,
            contact_started=contact_started,
            mutation_succeeded_count=mutation_succeeded_count,
        )

    custom_seam_failure = _custom_seam_failure(
        path_model=path_model,
        seam_injection=seam_injection,
    )
    if custom_seam_failure is not None:
        return _failure_result(
            evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            committed_detail_label=DETAIL_PATH_MISMATCH,
            derived_subreason=custom_seam_failure,
            contact_started=contact_started,
            mutation_succeeded_count=mutation_succeeded_count,
        )

    if prove_not_started_absence:
        return _not_started_absence_result(
            evidence_body=evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            native_adapter=native_adapter_object,
            path_model=path_model,
        )

    for index, raw_target in enumerate(path_model.components, start=1):
        raw_parent = path_model.parents()[index - 1]
        operation: dict[str, Any] = _initial_operation(index, raw_parent, raw_target)
        evidence_body["operations"].append(operation)
        parent_handle: DirectoryHandle | None = None
        child_handle: DirectoryHandle | None = None
        parent_post: DirectoryHandle | None = None
        phase = "ordinal_start"
        try:
            phase = "repository_pre_state"
            repo_state = repository_reader_callable()
            repo_failure = _repository_failure(
                repo_state,
                accepted_invocation_head,
                expected_branch,
                expected_untracked_entries,
            )
            operation["committed_required"]["repository_pre_state"] = repo_state.as_dict()
            if repo_failure is not None:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_VALIDATION_FAILURE,
                    derived_subreason=repo_failure,
                    contact_started=contact_started,
                    mutation_succeeded_count=mutation_succeeded_count,
                )

            phase = "parent_open"
            parent_open = native_adapter_object.open_directory(raw_parent)
            if not parent_open.opened or parent_open.handle is None:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=_parent_open_detail(parent_open.error),
                    derived_subreason="parent_open_failed",
                    contact_started=contact_started,
                    mutation_succeeded_count=mutation_succeeded_count,
                    diagnostic=_native_error_dict(parent_open.error),
                )
            parent_handle = parent_open.handle
            operation["committed_required"]["immediate_parent_identity"] = (
                parent_handle.evidence.identity.as_dict()
            )
            operation["committed_required"]["parent_pre_identity"] = (
                parent_handle.evidence.identity.as_dict()
            )
            operation["committed_required"]["filesystem_and_drive_profile"] = (
                parent_handle.evidence.volume_profile.as_dict()
            )
            operation["committed_required"]["parent_pre_reparse_status"] = _tri(
                parent_handle.evidence.is_reparse_point
            )
            operation["derived_implementation"]["held_parent_handle"] = (
                parent_handle.evidence.as_dict()
            )
            phase = "parent_profile_validation"
            parent_valid_failure = _ordinary_local_ntfs_failure(parent_handle.evidence)
            if parent_valid_failure is not None:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=parent_valid_failure[0],
                    derived_subreason=parent_valid_failure[1],
                    contact_started=contact_started,
                    mutation_succeeded_count=mutation_succeeded_count,
                )
            if previous_child_identity is not None and (
                parent_handle.evidence.identity != previous_child_identity
            ):
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_ORDER_VIOLATION,
                    derived_subreason="chained_identity_mismatch",
                    contact_started=contact_started,
                    mutation_succeeded_count=mutation_succeeded_count,
                )

            phase = "target_absence"
            immediate_absence = native_adapter_object.check_absent(
                raw_target,
                allow_missing_ancestor=False,
            )
            operation["committed_required"]["target_absence_before"] = (
                immediate_absence.as_dict()
            )
            if not immediate_absence.positively_absent:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=_absence_detail(immediate_absence),
                    derived_subreason="target_not_positively_absent",
                    contact_started=contact_started,
                    mutation_succeeded_count=mutation_succeeded_count,
                )

            phase = "later_component_absence_pre"
            later_pre_failure = _verify_later_components_absent(
                native_adapter_object,
                path_model,
                index,
                operation,
                phase="pre",
            )
            if later_pre_failure is not None:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_UNEXPECTED_INTERMEDIATE,
                    derived_subreason=later_pre_failure,
                    contact_started=contact_started,
                    mutation_succeeded_count=mutation_succeeded_count,
                )

            phase = "clock"
            operation["committed_required"]["operation_timestamp_utc"] = (
                _canonical_utc_timestamp(utc_clock_callable())
            )
            operation["committed_required"]["operation_monotonic_ns"] = (
                _canonical_monotonic_ns(monotonic_clock_callable())
            )
            operation["derived_implementation"]["creation_call"] = {
                "primitive": "os.mkdir",
                "raw_target_passed_exactly": raw_target,
                "attempt_count_for_ordinal": 1,
                "exclusive_create_success": False,
                "mutation_ownership": "NOT_CLAIMED_BEFORE_SUCCESS",
            }
            try:
                phase = "creation_primitive"
                contact_started = True
                evidence_body["aggregate"]["contact_started"] = True
                evidence_body["aggregate"]["opportunity_consumed"] = True
                creation_primitive_callable(raw_target)
            except KeyboardInterrupt:
                operation["derived_implementation"]["creation_call"]["outcome"] = (
                    "operator_interruption"
                )
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_VALIDATION_FAILURE,
                    derived_subreason="operator_interruption_after_contact",
                    contact_started=True,
                    mutation_succeeded_count=mutation_succeeded_count,
                    diagnostic=_exception_event(
                        KeyboardInterrupt(),
                        ordinal=index,
                        phase=phase,
                        contact_started=True,
                        mutation_succeeded_count=mutation_succeeded_count,
                    ),
                )
            except FileExistsError as exc:
                operation["derived_implementation"]["creation_call"]["outcome"] = (
                    "file_exists_error"
                )
                operation["optional_diagnostic"]["creation_exception"] = (
                    _exception_dict(exc)
                )
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_CHILD_PRE_EXISTS,
                    derived_subreason="concurrent_creation_or_collision",
                    contact_started=True,
                    mutation_succeeded_count=mutation_succeeded_count,
                )
            except OSError as exc:
                operation["derived_implementation"]["creation_call"]["outcome"] = (
                    "os_error"
                )
                operation["optional_diagnostic"]["creation_exception"] = (
                    _exception_dict(exc)
                )
                try:
                    operation["optional_diagnostic"]["post_error_target_absence_probe"] = (
                        native_adapter_object.check_absent(
                            raw_target,
                            allow_missing_ancestor=False,
                        ).as_dict()
                    )
                except Exception as probe_exc:
                    operation["optional_diagnostic"][
                        "post_error_target_absence_probe_exception"
                    ] = _exception_event(
                        probe_exc,
                        ordinal=index,
                        phase="post_error_target_absence_probe",
                        contact_started=True,
                        mutation_succeeded_count=mutation_succeeded_count,
                    )
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=_os_error_detail(exc),
                    derived_subreason="create_call_failed_no_success_conversion",
                    contact_started=True,
                    mutation_succeeded_count=mutation_succeeded_count,
                )

            mutation_succeeded_count += 1
            operation["derived_implementation"]["creation_call"].update(
                {
                    "outcome": "returned_success",
                    "exclusive_create_success": True,
                    "mutation_ownership": (
                        "attributed_to_this_invocation_because_os_mkdir_returned_success"
                    ),
                    "creation_time_object_identity": "NOT_OBSERVED",
                }
            )

            phase = "child_open"
            child_open = native_adapter_object.open_directory(raw_target)
            if not child_open.opened or child_open.handle is None:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_VALIDATION_FAILURE,
                    derived_subreason="post_create_child_identity_unavailable",
                    contact_started=True,
                    mutation_succeeded_count=mutation_succeeded_count,
                    diagnostic=_native_error_dict(child_open.error),
                )
            child_handle = child_open.handle
            phase = "child_profile_validation"
            child_failure = _ordinary_local_ntfs_failure(child_handle.evidence)
            if child_failure is not None:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=child_failure[0],
                    derived_subreason=child_failure[1],
                    contact_started=True,
                    mutation_succeeded_count=mutation_succeeded_count,
                )

            phase = "parent_reopen"
            reopened_parent = native_adapter_object.open_directory(raw_parent)
            if not reopened_parent.opened or reopened_parent.handle is None:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_VALIDATION_FAILURE,
                    derived_subreason="parent_reopen_failed_after_creation",
                    contact_started=True,
                    mutation_succeeded_count=mutation_succeeded_count,
                    diagnostic=_native_error_dict(reopened_parent.error),
                )
            parent_post = reopened_parent.handle
            if parent_post.evidence.identity != parent_handle.evidence.identity:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_VALIDATION_FAILURE,
                    derived_subreason="parent_identity_drift",
                    contact_started=True,
                    mutation_succeeded_count=mutation_succeeded_count,
                )

            phase = "later_component_absence_post"
            later_post_failure = _verify_later_components_absent(
                native_adapter_object,
                path_model,
                index,
                operation,
                phase="post",
            )
            if later_post_failure is not None:
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=DETAIL_UNEXPECTED_INTERMEDIATE,
                    derived_subreason=later_post_failure,
                    contact_started=True,
                    mutation_succeeded_count=mutation_succeeded_count,
                )

            operation["committed_required"].update(
                {
                    "target_presence_after": TRI_TRUE,
                    "directory_type": "ordinary_directory",
                    "reparse_status": TRI_FALSE,
                    "local_fixed_drive": (
                        child_handle.evidence.volume_profile.drive_type
                        == validation.DRIVE_FIXED
                    ),
                    "ntfs_filesystem": (
                        child_handle.evidence.volume_profile.filesystem_name.upper()
                        == "NTFS"
                    ),
                    "volume_identity": child_handle.evidence.volume_profile.as_dict(),
                    "directory_file_identity": child_handle.evidence.identity.as_dict(),
                    "post_create_observed_identity": (
                        child_handle.evidence.identity.as_dict()
                    ),
                    "parent_post_identity": parent_post.evidence.identity.as_dict(),
                    "operator_process_result": "os.mkdir_returned_success",
                    "unexpected_intermediate_creation_check": "PASS",
                    "unexpected_intermediate_creation_method": (
                        "later_component_absence_falsifier_and_chained_identity"
                    ),
                    "unexpected_sibling_creation_check": "NOT_PERFORMED",
                    "unexpected_sibling_creation_check_class": (
                        "OPTIONAL_DIAGNOSTIC_NOT_OBSERVED"
                    ),
                    "tool_or_primitive_identities": execution_seams,
                    "accepted_invocation_head": accepted_invocation_head,
                    "branch": repo_state.branch,
                    "local_origin_main": repo_state.origin_main,
                    "index_lock_state": repo_state.index_lock_state,
                    "index_lock_observation_error": (
                        repo_state.index_lock_observation_error
                    ),
                }
            )
            operation["derived_implementation"]["child_handle"] = (
                child_handle.evidence.as_dict()
            )
            operation["derived_implementation"]["parent_reopened_after_creation"] = (
                parent_post.evidence.as_dict()
            )
            previous_child_identity = child_handle.evidence.identity
        except KeyboardInterrupt:
            return _failure_result(
                evidence_body,
                authority=authority,
                execution_mode=execution_mode,
                committed_detail_label=DETAIL_VALIDATION_FAILURE,
                derived_subreason=(
                    "operator_interruption_after_contact"
                    if contact_started
                    else "operator_interruption_before_contact"
                ),
                contact_started=contact_started,
                mutation_succeeded_count=mutation_succeeded_count,
            )
        except Exception as exc:
            return _unexpected_exception_result(
                evidence_body=evidence_body,
                authority=authority,
                execution_mode=execution_mode,
                exc=exc,
                ordinal=index,
                phase=phase,
                contact_started=contact_started,
                mutation_succeeded_count=mutation_succeeded_count,
            )
        finally:
            _close_handles_once(parent_post, child_handle, parent_handle)

    evidence_body["aggregate"].update(
        {
            "mutation_succeeded_count": mutation_succeeded_count,
            "full_ordered_sequence_succeeded": True,
            "opportunity_consumed": True,
            "sequence_terminal": False,
            "derived_execution_state": CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION,
            "derived_execution_state_kind": CLASSIFICATION_DERIVED_NON_TERMINAL,
        }
    )
    return _success_result(
        evidence_body,
        mutation_succeeded_count,
        authority=authority,
        execution_mode=execution_mode,
    )


def read_repository_state(
    repo_root: str | Path = ".",
    *,
    git_runner: Callable[..., Any] | None = None,
    index_lock_observer: Callable[[Path], Any] | None = None,
) -> RepositoryState:
    root = Path(repo_root)
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    runner = git_runner or subprocess.run

    def git_lines(*args: str) -> tuple[str, ...]:
        result = runner(
            ["git", "--no-optional-locks", "-c", "core.quotePath=false", *args],
            cwd=root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return tuple(line for line in result.stdout.splitlines() if line)

    branch = git_lines("symbolic-ref", "--quiet", "--short", "HEAD")[0]
    head = git_lines("rev-parse", "HEAD")[0]
    origin_main = git_lines("rev-parse", "refs/remotes/origin/main")[0]
    staged = git_lines("diff", "--cached", "--name-only", "--no-ext-diff")
    modified = git_lines("ls-files", "--modified", "--deleted")
    unmerged = git_lines("ls-files", "-u")
    untracked = git_lines("ls-files", "--others", "--exclude-standard")
    lock_state, lock_error = _observe_index_lock_state(
        root,
        observer=index_lock_observer,
    )
    return RepositoryState(
        branch=branch,
        head=head,
        origin_main=origin_main,
        index_lock_present=(lock_state == INDEX_LOCK_PRESENT),
        index_lock_state=lock_state,
        index_lock_observation_error=lock_error,
        staged_changes=staged,
        unstaged_tracked_changes=modified,
        unmerged_entries=unmerged,
        untracked_entries=untracked,
    )


def _observe_index_lock_state(
    repo_root: Path,
    *,
    observer: Callable[[Path], Any] | None = None,
) -> tuple[str, dict[str, Any] | None]:
    lock_path = repo_root / ".git" / "index.lock"
    observe = observer or os.lstat
    try:
        observe(lock_path)
        return INDEX_LOCK_PRESENT, None
    except FileNotFoundError:
        return INDEX_LOCK_ABSENT, None
    except PermissionError as exc:
        return INDEX_LOCK_INDETERMINATE, _exception_dict(exc)
    except OSError as exc:
        return INDEX_LOCK_INDETERMINATE, _exception_dict(exc)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def body_identity_for_evidence_body(evidence_body: dict[str, Any]) -> dict[str, Any]:
    payload = canonical_json_bytes(evidence_body)
    return {
        "body_byte_count": len(payload),
        "body_sha256": hashlib.sha256(payload).hexdigest(),
        "identity_scope": "canonical evidence_body bytes only",
        "whole_record_identity_stored_inside_record": False,
    }


def _initial_evidence_body(
    *,
    authority: AuthorityAssertions,
    accepted_invocation_head: str,
    path_model: PathModel,
    allow_test_path_model: bool,
    execution_seams: dict[str, Any],
) -> dict[str, Any]:
    authority_state = _authority_state(authority)
    return {
        "schema": EVIDENCE_BODY_SCHEMA,
        "version": VERSION,
        "authority_assertions": asdict(authority),
        "authority_state": authority_state,
        "accepted_invocation_head": accepted_invocation_head,
        "path_model": path_model.as_dict(),
        "test_path_model": allow_test_path_model,
        "execution_seams": execution_seams,
        "publication_boundary": {
            "publishes_evidence_record": False,
            "publishes_canonical_input": False,
            "invokes_runner": False,
            "successful_return_is_unpublished_record_candidate": True,
        },
        "path_interpretation": {
            "creation_receives_raw_governed_string": True,
            "creation_uses": "ordinary Win32 path interpretation via os.mkdir",
            "verification_helpers_may_use_extended_length_paths": True,
            "identical_resolution_mechanics_claimed": False,
        },
        "field_classes": {
            "committed_required": [
                "exact absolute path",
                "ordinal and operation ordering",
                "immediate parent identity",
                "target absence before",
                "target presence after",
                "directory type",
                "reparse status",
                "local fixed drive",
                "NTFS filesystem",
                "volume identity",
                "directory file identity",
                "operation timestamp UTC",
                "operation monotonic nanoseconds",
                "operator/process result",
                "tool or primitive identities",
                "unexpected intermediate creation check",
                "accepted invocation HEAD",
                "branch",
                "local origin/main",
                "index-lock state",
            ],
            "derived_implementation": [
                "raw path literal validation",
                "held parent handle continuity",
                "creation call outcome",
                "mutation counter",
                "classification",
                "derived subreason",
            ],
            "optional_diagnostic": [
                "native error code",
                "native error name",
                "exception class",
                "bounded absence probes",
            ],
        },
        "operations": [],
        "aggregate": {
            "contact_started": False,
            "opportunity_consumed": False,
            "mutation_succeeded_count": 0,
            "sequence_terminal": False,
        },
    }


def _initial_operation(ordinal: int, raw_parent: str, raw_target: str) -> dict[str, Any]:
    return {
        "committed_required": {
            "ordinal": ordinal,
            "operation_ordering": ordinal,
            "exact_absolute_path": raw_target,
            "immediate_parent_path": raw_parent,
            "target_presence_after": TRI_FALSE,
        },
        "derived_implementation": {
            "raw_target_literal": raw_target,
            "raw_parent_literal": raw_parent,
            "raw_target_literal_matches_path_model": True,
            "raw_parent_literal_matches_path_model": True,
        },
        "optional_diagnostic": {},
    }


def _authority_precondition_failure(authority: AuthorityAssertions) -> str | None:
    required = {
        "window_open": True,
        "authority_a_active": True,
        "authority_b_active": True,
        "authority_c_active": False,
        "authority_d_active": False,
        "authority_e_active": False,
    }
    observed = asdict(authority)
    for key, expected in required.items():
        if observed[key] is not expected:
            return "authority_assertion_mismatch_" + key
    return None


def _authority_state(authority: AuthorityAssertions) -> dict[str, Any]:
    observed = asdict(authority)
    return {
        "authority_assertions_observed": observed,
        "required_authority_gate_satisfied": _required_authority_gate_satisfied(
            authority
        ),
        "window_open": authority.window_open,
        "authority_a_active": authority.authority_a_active,
        "authority_b_active": authority.authority_b_active,
        "authority_c_inactive": not authority.authority_c_active,
        "authority_d_inactive": not authority.authority_d_active,
        "authority_e_inactive": not authority.authority_e_active,
    }


def _required_authority_gate_satisfied(authority: AuthorityAssertions) -> bool:
    return _authority_precondition_failure(authority) is None


def _path_model_failure(path_model: PathModel, allow_test_path_model: bool) -> str | None:
    if allow_test_path_model:
        return None
    if path_model != GOVERNED_PATH_MODEL:
        return "path_model_not_exact_governed_constants"
    return None


def _path_model_paths(path_model: PathModel) -> tuple[str, ...]:
    return (
        path_model.required_root,
        *path_model.components,
        path_model.evidence_record_path,
        path_model.canonical_input_path,
    )


def _test_mode_governed_path_failure(
    path_model: PathModel,
    allow_test_path_model: bool,
) -> str | None:
    if not allow_test_path_model:
        return None
    for raw_path in _path_model_paths(path_model):
        if _is_governed_prefix_or_descendant(raw_path):
            return "governed_path_forbidden_in_test_mode"
    return None


def _is_governed_prefix_or_descendant(raw_path: str) -> bool:
    selected = _governed_compare_text(raw_path)
    prefix = _governed_compare_text(GOVERNED_COMPONENT_1)
    return selected == prefix or selected.startswith(prefix + "\\")


def _governed_compare_text(raw_path: str) -> str:
    normalized = str(raw_path).replace("/", "\\")
    while len(normalized) > 3 and normalized.endswith("\\"):
        normalized = normalized[:-1]
    return normalized.casefold()


def _uses_governed_path_model(path_model: PathModel) -> bool:
    return path_model == GOVERNED_PATH_MODEL


def _custom_seam_failure(
    *,
    path_model: PathModel,
    seam_injection: dict[str, bool],
) -> str | None:
    if _uses_governed_path_model(path_model) and any(seam_injection.values()):
        return "custom_seam_forbidden_for_governed_path_model"
    return None


def _execution_mode(
    *,
    path_model: PathModel,
    allow_test_path_model: bool,
    seam_injection: dict[str, bool],
) -> str:
    if _uses_governed_path_model(path_model) and any(seam_injection.values()):
        return EXECUTION_MODE_UNSUPPORTED_CUSTOM
    if (
        _uses_governed_path_model(path_model)
        and not allow_test_path_model
        and not any(seam_injection.values())
    ):
        return EXECUTION_MODE_AUTHORITATIVE_DEFAULT
    return EXECUTION_MODE_TEST_OR_CUSTOM


def _execution_seam_evidence(
    *,
    repository_reader_callable: Callable[[], RepositoryState],
    native_adapter_object: Any,
    creation_primitive_callable: Callable[[str], None],
    utc_clock_callable: Callable[[], Any],
    monotonic_clock_callable: Callable[[], int],
    seam_injection: dict[str, bool],
    execution_mode: str,
    repository_root: str | Path,
) -> dict[str, Any]:
    return {
        "creation_primitive_module": _callable_module(creation_primitive_callable),
        "creation_primitive_qualname": _callable_qualname(
            creation_primitive_callable
        ),
        "native_adapter_module": native_adapter_object.__class__.__module__,
        "native_adapter_class": native_adapter_object.__class__.__qualname__,
        "repository_reader_module": (
            read_repository_state.__module__
            if not seam_injection["repository_reader"]
            else _callable_module(repository_reader_callable)
        ),
        "repository_reader_qualname": (
            read_repository_state.__qualname__
            if not seam_injection["repository_reader"]
            else _callable_qualname(repository_reader_callable)
        ),
        "utc_clock_module": (
            _default_utc_clock.__module__
            if not seam_injection["clock"] and not seam_injection["utc_clock"]
            else _callable_module(utc_clock_callable)
        ),
        "utc_clock_qualname": (
            _default_utc_clock.__qualname__
            if not seam_injection["clock"] and not seam_injection["utc_clock"]
            else _callable_qualname(utc_clock_callable)
        ),
        "monotonic_clock_module": (
            _default_monotonic_clock.__module__
            if not seam_injection["monotonic_clock"]
            else _callable_module(monotonic_clock_callable)
        ),
        "monotonic_clock_qualname": (
            _default_monotonic_clock.__qualname__
            if not seam_injection["monotonic_clock"]
            else _callable_qualname(monotonic_clock_callable)
        ),
        "custom_seams_present": any(seam_injection.values()),
        "seam_injection": dict(seam_injection),
        "execution_mode": execution_mode,
        "repository_root": str(repository_root),
    }


def _authoritative_default_seam_identity_mismatch(
    execution_seams: dict[str, Any],
) -> dict[str, Any] | None:
    approved = _approved_authoritative_default_seam_identities()
    mismatches = {}
    for key, expected_value in approved.items():
        observed_value = execution_seams.get(key)
        if observed_value != expected_value:
            mismatches[key] = {
                "expected": expected_value,
                "observed": observed_value,
            }
    if not mismatches:
        return None
    return {
        "mismatched_seams": mismatches,
        "observed_execution_seams": copy.deepcopy(execution_seams),
        "approved_execution_seams": approved,
    }


def _approved_authoritative_default_seam_identities() -> dict[str, str]:
    return {
        "creation_primitive_module": __name__,
        "creation_primitive_qualname": "_default_creation_primitive",
        "native_adapter_module": __name__,
        "native_adapter_class": "Win32DirectoryAdapter",
        "repository_reader_module": __name__,
        "repository_reader_qualname": "read_repository_state",
        "utc_clock_module": __name__,
        "utc_clock_qualname": "_default_utc_clock",
        "monotonic_clock_module": __name__,
        "monotonic_clock_qualname": "_default_monotonic_clock",
    }


def _callable_module(value: Callable[..., Any]) -> str:
    return getattr(value, "__module__", type(value).__module__)


def _callable_qualname(value: Callable[..., Any]) -> str:
    return getattr(value, "__qualname__", type(value).__qualname__)


def _validate_all_raw_paths(
    path_model: PathModel,
    allow_test_path_model: bool,
) -> str | None:
    for raw in _path_model_paths(path_model):
        failure = _validate_raw_path_text(raw, allow_test_path_model)
        if failure is not None:
            return failure + ":" + raw
    return None


def _validate_raw_path_text(raw_path: str, allow_test_path_model: bool) -> str | None:
    if "/" in raw_path:
        return "forward_slash_present"
    if raw_path.startswith("\\\\?\\") or raw_path.startswith("\\\\.\\"):
        return "device_or_extended_path"
    if raw_path.startswith("\\??\\"):
        return "nt_object_manager_path"
    if raw_path.startswith("\\\\"):
        return "unc_path"
    if "\\Volume{" in raw_path:
        return "volume_guid_path"
    drive, tail = ntpath.splitdrive(raw_path)
    if not allow_test_path_model and drive != "C:":
        return "drive_not_exact_literal_C"
    if not ntpath.isabs(raw_path):
        return "drive_relative_path"
    components = tail.split("\\")[1:]
    for component in components:
        if component in ("", ".", ".."):
            return "dot_or_empty_path_component"
        if component.endswith(".") or component.endswith(" "):
            return "trailing_dot_or_space_component"
        if ":" in component:
            return "alternate_data_stream_component"
        if any(char in component for char in "*?"):
            return "wildcard_component"
        if any(char in component for char in '<>|"'):
            return "illegal_component_character"
    result = validation.validate_absolute_win32_dos_path_text(raw_path)
    if not result.accepted:
        return "absolute_path_validation_rejected_" + str(result.reason)
    return None


def _repository_failure(
    state: RepositoryState,
    accepted_invocation_head: str,
    expected_branch: str,
    expected_untracked_entries: tuple[str, ...],
) -> str | None:
    if state.branch != expected_branch:
        return "branch_drift"
    if state.head != accepted_invocation_head:
        return "head_drift"
    if state.origin_main != accepted_invocation_head:
        return "origin_main_drift"
    if state.index_lock_state == INDEX_LOCK_INDETERMINATE:
        return "index_lock_indeterminate"
    if state.index_lock_state == INDEX_LOCK_PRESENT or state.index_lock_present:
        return "index_lock_present"
    if state.staged_changes:
        return "staged_changes_present"
    if state.unstaged_tracked_changes:
        return "unstaged_tracked_changes_present"
    if state.unmerged_entries:
        return "unmerged_entries_present"
    if tuple(sorted(state.untracked_entries)) != tuple(sorted(expected_untracked_entries)):
        return "unexpected_untracked_state"
    return None


def _verify_later_components_absent(
    native_adapter: Any,
    path_model: PathModel,
    ordinal: int,
    operation: dict[str, Any],
    *,
    phase: str,
) -> str | None:
    checks = []
    for later_ordinal, later_path in enumerate(path_model.components[ordinal:], start=ordinal + 1):
        absence = native_adapter.check_absent(
            later_path,
            allow_missing_ancestor=True,
        )
        checks.append(
            {
                "ordinal": later_ordinal,
                "path": later_path,
                "absence": absence.as_dict(),
            }
        )
        if not absence.positively_absent:
            operation["committed_required"][
                "later_component_absence_%s" % phase
            ] = checks
            return "later_component_not_absent_%s_ordinal_%s" % (
                phase,
                later_ordinal,
            )
    operation["committed_required"]["later_component_absence_%s" % phase] = checks
    return None


def _ordinary_local_ntfs_failure(
    evidence: DirectoryHandleEvidence,
) -> tuple[str, str] | None:
    if not evidence.is_directory:
        return DETAIL_VALIDATION_FAILURE, "path_is_not_directory"
    if evidence.is_reparse_point:
        return DETAIL_REPARSE_OR_ALIAS, "path_is_reparse_point"
    if evidence.volume_profile.drive_type != validation.DRIVE_FIXED:
        return DETAIL_VALIDATION_FAILURE, "drive_not_local_fixed"
    if evidence.volume_profile.filesystem_name.upper() != "NTFS":
        return DETAIL_VALIDATION_FAILURE, "filesystem_not_ntfs"
    if evidence.volume_profile.volume_serial_number != evidence.identity.volume_serial_number:
        return DETAIL_VALIDATION_FAILURE, "volume_identity_mismatch"
    return None


def _parent_open_detail(error: NativeError | None) -> str:
    if error is None:
        return DETAIL_VALIDATION_FAILURE
    if error.native_error_code == validation.ERROR_PATH_NOT_FOUND:
        return DETAIL_PARENT_ABSENT
    if error.native_error_code == validation.ERROR_FILE_NOT_FOUND:
        return DETAIL_PARENT_ABSENT
    if error.native_error_code in (
        validation.ERROR_ACCESS_DENIED,
        validation.ERROR_SHARING_VIOLATION,
    ):
        return DETAIL_VALIDATION_FAILURE
    return DETAIL_VALIDATION_FAILURE


def _absence_detail(absence: AbsenceResult) -> str:
    if absence.basis == "handle_opened_target_pre_exists":
        return DETAIL_CHILD_PRE_EXISTS
    if absence.native_error_code == validation.ERROR_PATH_NOT_FOUND:
        return DETAIL_PARENT_ABSENT
    if absence.native_error_code == validation.ERROR_INVALID_NAME:
        return DETAIL_PATH_MISMATCH
    return DETAIL_VALIDATION_FAILURE


def _os_error_detail(exc: OSError) -> str:
    code = getattr(exc, "winerror", None) or getattr(exc, "errno", None)
    if code in (validation.ERROR_ALREADY_EXISTS, validation.ERROR_FILE_EXISTS):
        return DETAIL_CHILD_PRE_EXISTS
    if code in (validation.ERROR_FILE_NOT_FOUND, validation.ERROR_PATH_NOT_FOUND):
        return DETAIL_PARENT_ABSENT
    if code == validation.ERROR_INVALID_NAME:
        return DETAIL_PATH_MISMATCH
    return DETAIL_VALIDATION_FAILURE


def _success_result(
    evidence_body: dict[str, Any],
    mutation_succeeded_count: int,
    *,
    authority: AuthorityAssertions,
    execution_mode: str,
) -> HelperResult:
    identity, identity_error = _safe_body_identity_for_result(evidence_body)
    if identity_error is not None:
        evidence_body["aggregate"]["success_body_identity_failure"] = identity_error
        return _failure_result(
            evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            committed_detail_label=DETAIL_VALIDATION_FAILURE,
            derived_subreason="unexpected_exception_after_contact",
            contact_started=True,
            mutation_succeeded_count=mutation_succeeded_count,
            diagnostic=identity_error,
        )
    return HelperResult(
        classification=CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION,
        classification_kind=CLASSIFICATION_DERIVED_NON_TERMINAL,
        terminal=False,
        committed_detail_label=None,
        derived_subreason=None,
        authority_active=_required_authority_gate_satisfied(authority),
        contact_started=True,
        opportunity_consumed=True,
        mutation_succeeded_count=mutation_succeeded_count,
        sequence_terminal=False,
        evidence_body=copy.deepcopy(evidence_body),
        body_identity=identity,
        authority_assertions_observed=asdict(authority),
        required_authority_gate_satisfied=_required_authority_gate_satisfied(authority),
        execution_mode=execution_mode,
    )


def _failure_result(
    evidence_body: dict[str, Any],
    *,
    authority: AuthorityAssertions,
    execution_mode: str,
    committed_detail_label: str,
    derived_subreason: str,
    contact_started: bool,
    mutation_succeeded_count: int,
    diagnostic: dict[str, Any] | None = None,
    not_started_proven: bool = False,
) -> HelperResult:
    if not_started_proven:
        classification = CORRECTED_PATH_CREATION_NOT_STARTED
        classification_kind = CLASSIFICATION_COMMITTED_TERMINAL
        terminal = True
        sequence_terminal = True
    elif contact_started:
        classification = CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
        classification_kind = CLASSIFICATION_COMMITTED_TERMINAL
        terminal = True
        sequence_terminal = True
    else:
        classification = CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
        classification_kind = CLASSIFICATION_DERIVED_NON_TERMINAL
        terminal = False
        sequence_terminal = False
    evidence_body["aggregate"].update(
        {
            "contact_started": contact_started,
            "opportunity_consumed": contact_started,
            "mutation_succeeded_count": mutation_succeeded_count,
            "sequence_terminal": sequence_terminal,
            "classification": classification,
            "classification_kind": classification_kind,
            "committed_detail_label": committed_detail_label,
            "derived_subreason": {
                "kind": "DERIVED_IMPLEMENTATION_SUBREASON",
                "value": derived_subreason,
            },
        }
    )
    if diagnostic is not None:
        evidence_body["aggregate"]["failure_diagnostic"] = diagnostic
    identity, identity_error = _safe_body_identity_for_result(evidence_body)
    if identity_error is not None:
        evidence_body["aggregate"]["body_identity_failure"] = identity_error
        identity = _fallback_body_identity(identity_error)
    return HelperResult(
        classification=classification,
        classification_kind=classification_kind,
        terminal=terminal,
        committed_detail_label=committed_detail_label,
        derived_subreason=derived_subreason,
        authority_active=_required_authority_gate_satisfied(authority),
        contact_started=contact_started,
        opportunity_consumed=contact_started,
        mutation_succeeded_count=mutation_succeeded_count,
        sequence_terminal=sequence_terminal,
        evidence_body=copy.deepcopy(evidence_body),
        body_identity=identity,
        authority_assertions_observed=asdict(authority),
        required_authority_gate_satisfied=_required_authority_gate_satisfied(authority),
        execution_mode=execution_mode,
    )


def _not_started_absence_result(
    *,
    evidence_body: dict[str, Any],
    authority: AuthorityAssertions,
    execution_mode: str,
    native_adapter: Any,
    path_model: PathModel,
) -> HelperResult:
    checks = []
    required_paths = (
        ("component_1", path_model.components[0]),
        ("component_2", path_model.components[1]),
        ("component_3", path_model.components[2]),
        ("evidence_record_path", path_model.evidence_record_path),
    )
    canonical_input_check = None
    try:
        for label, raw_path in required_paths:
            absence = native_adapter.check_absent(
                raw_path,
                allow_missing_ancestor=True,
            )
            checks.append(
                {
                    "label": label,
                    "path": raw_path,
                    "absence": absence.as_dict(),
                    "required_for_not_started": True,
                }
            )
            if not absence.positively_absent:
                evidence_body["aggregate"]["not_started_absence_checks"] = checks
                return _failure_result(
                    evidence_body,
                    authority=authority,
                    execution_mode=execution_mode,
                    committed_detail_label=_absence_detail(absence),
                    derived_subreason="not_started_absence_not_proven",
                    contact_started=False,
                    mutation_succeeded_count=0,
                )
        canonical_absence = native_adapter.check_absent(
            path_model.canonical_input_path,
            allow_missing_ancestor=True,
        )
        canonical_input_check = {
            "label": "canonical_input_path",
            "path": path_model.canonical_input_path,
            "absence": canonical_absence.as_dict(),
            "required_for_not_started": False,
        }
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        return _unexpected_exception_result(
            evidence_body=evidence_body,
            authority=authority,
            execution_mode=execution_mode,
            exc=exc,
            ordinal=0,
            phase="not_started_absence_proof",
            contact_started=False,
            mutation_succeeded_count=0,
        )
    evidence_body["aggregate"]["not_started_absence_checks"] = checks
    evidence_body["aggregate"]["canonical_input_absence_observation"] = (
        canonical_input_check
    )
    return _failure_result(
        evidence_body,
        authority=authority,
        execution_mode=execution_mode,
        committed_detail_label=DETAIL_VALIDATION_FAILURE,
        derived_subreason="not_started_absence_proven",
        contact_started=False,
        mutation_succeeded_count=0,
        not_started_proven=True,
    )


def _unexpected_exception_result(
    *,
    evidence_body: dict[str, Any],
    authority: AuthorityAssertions,
    execution_mode: str,
    exc: Exception,
    ordinal: int,
    phase: str,
    contact_started: bool,
    mutation_succeeded_count: int,
) -> HelperResult:
    return _failure_result(
        evidence_body,
        authority=authority,
        execution_mode=execution_mode,
        committed_detail_label=DETAIL_VALIDATION_FAILURE,
        derived_subreason=(
            "unexpected_exception_after_contact"
            if contact_started
            else "unexpected_exception_before_contact"
        ),
        contact_started=contact_started,
        mutation_succeeded_count=mutation_succeeded_count,
        diagnostic=_exception_event(
            exc,
            ordinal=ordinal,
            phase=phase,
            contact_started=contact_started,
            mutation_succeeded_count=mutation_succeeded_count,
        ),
    )


def _safe_body_identity_for_result(
    evidence_body: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        return body_identity_for_evidence_body(evidence_body), None
    except Exception as exc:
        diagnostic = _exception_event(
            exc,
            ordinal=0,
            phase="body_identity",
            contact_started=bool(evidence_body.get("aggregate", {}).get("contact_started")),
            mutation_succeeded_count=int(
                evidence_body.get("aggregate", {}).get("mutation_succeeded_count", 0)
            ),
        )
        return _fallback_body_identity(diagnostic), diagnostic


def _fallback_body_identity(diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "body_byte_count": None,
        "body_sha256": None,
        "identity_scope": "canonical evidence_body bytes only",
        "whole_record_identity_stored_inside_record": False,
        "identity_unavailable": True,
        "identity_failure": diagnostic,
    }


def _tri(value: bool | None) -> str:
    if value is True:
        return TRI_TRUE
    if value is False:
        return TRI_FALSE
    return TRI_INDETERMINATE


def _native_error_dict(error: NativeError | None) -> dict[str, Any]:
    return error.as_dict() if error is not None else {"native_error": None}


def _exception_dict(exc: BaseException) -> dict[str, Any]:
    return {
        "exception_type": type(exc).__name__,
        "message": _sanitize_exception_message(str(exc)),
        "errno": getattr(exc, "errno", None),
        "winerror": getattr(exc, "winerror", None),
    }


def _canonical_utc_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("UTC timestamp datetime must be timezone-aware")
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, str):
        if not UTC_TIMESTAMP_PATTERN.fullmatch(value):
            raise ValueError("UTC timestamp string is not canonical RFC3339 Z form")
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        canonical = parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        if canonical != value:
            raise ValueError("UTC timestamp string is not canonical UTC")
        return value
    raise TypeError("UTC timestamp clock must return datetime or canonical string")


def _canonical_monotonic_ns(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("monotonic clock must return an integer nanosecond value")
    if value < 0:
        raise ValueError("monotonic clock must be non-negative")
    return value


def _exception_event(
    exc: BaseException,
    *,
    ordinal: int,
    phase: str,
    contact_started: bool,
    mutation_succeeded_count: int,
) -> dict[str, Any]:
    return {
        "exception_type": type(exc).__name__,
        "message": _sanitize_exception_message(str(exc)),
        "ordinal": ordinal,
        "phase": phase,
        "contact_started": contact_started,
        "mutation_succeeded_count": mutation_succeeded_count,
    }


def _sanitize_exception_message(message: str) -> str:
    stable = "".join(
        character if 32 <= ord(character) < 127 else "?"
        for character in message
    )
    return stable[:240]


def _error_name(error_code: int | None) -> str | None:
    if error_code is None:
        return None
    return validation.ERROR_NAMES.get(int(error_code))


def _close_private_handle(handle: Any) -> None:
    if hasattr(handle, "close"):
        handle.close()
        return
    if hasattr(handle, "__exit__"):
        handle.__exit__(None, None, None)


def _close_handles_once(*handles: DirectoryHandle | None) -> None:
    seen: set[int] = set()
    for handle in handles:
        if handle is None:
            continue
        marker = id(handle)
        if marker in seen:
            continue
        seen.add(marker)
        handle.close()


def _default_creation_primitive(raw_path: str) -> None:
    os.mkdir(raw_path)


def _default_utc_clock() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _default_monotonic_clock() -> int:
    return time.monotonic_ns()


__all__ = [
    "AuthorityAssertions",
    "DirectoryHandle",
    "DirectoryHandleEvidence",
    "GOVERNED_PATH_MODEL",
    "HelperResult",
    "ObjectIdentity",
    "PathModel",
    "RepositoryState",
    "VolumeProfile",
    "Win32DirectoryAdapter",
    "body_identity_for_evidence_body",
    "canonical_json_bytes",
    "execute_ordered_directory_creation",
    "read_repository_state",
    "CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION",
    "CORRECTED_PATH_CREATION_NOT_STARTED",
    "CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE",
]
