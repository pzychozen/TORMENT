from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
import hashlib
import json
import ntpath
import os
from pathlib import Path
import stat
import sys
import threading
from typing import Any

import durable_evidence_schema_v0_3 as durable_schema
import durable_evidence_windows_adapter_v0_3 as durability_adapter


BASELINE_COMMIT = "6c8b113d21a8e60b77739103bb1f1bbf03438882"
VALIDATION_VERSION = "v0.1"
VALIDATION_POLICY_SCHEMA = (
    "torment-brainvision-stage-s3b-blocker-2-windows-same-volume-"
    "no-replace-directory-promotion-validation-policy-v0.1"
)
ABSOLUTE_PATH_CONTROL_VERSION = "v0.1"
ABSOLUTE_PATH_CONTROL_MODE = "ABSOLUTE_PATH_CONTROL"
ROOTDIRECTORY_RELATIVE_MODE = "ROOTDIRECTORY_RELATIVE"
ABSOLUTE_PATH_CONTROL_POLICY_SCHEMA = (
    "torment-brainvision-stage-s3b-blocker-2-windows-same-volume-"
    "no-replace-directory-promotion-absolute-path-control-policy-v0.1"
)
PRIMITIVE_OPERATION_IDENTITY = (
    "win32-setfileinformationbyhandle-file-rename-info-rootdirectory-"
    "no-replace-directory-promotion-v0.1"
)
ABSOLUTE_PATH_CONTROL_OPERATION_IDENTITY = (
    "win32-setfileinformationbyhandle-file-rename-info-rootdirectory-null-"
    "absolute-path-no-replace-directory-promotion-control-v0.1"
)
VALIDATION_PROFILE_IDENTITY = (
    "windows-10-11-workstation-local-fixed-ntfs-same-volume-"
    "pytest-tmp-directory-promotion-v0.1"
)
ABSOLUTE_PATH_CONTROL_PROFILE_IDENTITY = (
    "windows-10-11-workstation-local-fixed-ntfs-same-volume-"
    "pytest-tmp-directory-absolute-path-promotion-control-v0.1"
)
IMPLEMENTATION_SURFACE_IDENTITY = (
    "blocker-2-bounded-windows-promotion-primitive-validation-three-file-surface-v0.1"
)
ABSOLUTE_PATH_CONTROL_AUTHORIZATION_COMMIT = (
    "e34d3d47bf2311c9443020fb85704f3cdbf85f82"
)
IMPLEMENTATION_VERDICT = "IMPLEMENTATION_BLOCKED_AND_HELD"
HELD_OUTCOME_WORDING = (
    "The authorised RootDirectory-relative FileRenameInfo contract was rejected by "
    "Windows with ERROR_INVALID_PARAMETER. The ABI and buffer construction have "
    "passed static review, but the native cause remains indeterminate. The "
    "primitive is neither validated nor falsified. No workaround was attempted."
)

PRIMITIVE_VALIDATION_CONFIRMED = "PRIMITIVE_VALIDATION_CONFIRMED"
FAILED = "FAILED"
UNSUPPORTED = "UNSUPPORTED"
SKIPPED = "SKIPPED"
INDETERMINATE = "INDETERMINATE"
FIXTURE_INVALID = "FIXTURE_INVALID"
IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
CONTENT_MISMATCH = "CONTENT_MISMATCH"
DESTINATION_REPLACED = "DESTINATION_REPLACED"
CROSS_VOLUME_COPY_DETECTED = "CROSS_VOLUME_COPY_DETECTED"
DURABILITY_UNCONFIRMED = "DURABILITY_UNCONFIRMED"

CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE = (
    "CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE"
)
CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE = (
    "CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE"
)
CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL = (
    "CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL"
)
CONTROL_ACCESS_REJECTED = "CONTROL_ACCESS_REJECTED"
CONTROL_COLLISION_OBSERVED = "CONTROL_COLLISION_OBSERVED"
CONTROL_FIXTURE_INVALID = "CONTROL_FIXTURE_INVALID"
CONTROL_SAME_VOLUME_REJECTED = "CONTROL_SAME_VOLUME_REJECTED"
CONTROL_REPARSE_REJECTED = "CONTROL_REPARSE_REJECTED"
CONTROL_CONTAINMENT_REJECTED = "CONTROL_CONTAINMENT_REJECTED"
CONTROL_SKIPPED_FIXTURE_UNAVAILABLE = "CONTROL_SKIPPED_FIXTURE_UNAVAILABLE"
CONTROL_NATIVE_ERROR_INDETERMINATE = "CONTROL_NATIVE_ERROR_INDETERMINATE"
CONTROL_FAULT_INJECTED = "CONTROL_FAULT_INJECTED"
CONTROL_IDENTITY_MISMATCH = "CONTROL_IDENTITY_MISMATCH"
CONTROL_CONTENT_MISMATCH = "CONTROL_CONTENT_MISMATCH"
CONTROL_DESTINATION_REPLACED = "CONTROL_DESTINATION_REPLACED"

STATUS_TAXONOMY = (
    PRIMITIVE_VALIDATION_CONFIRMED,
    FAILED,
    UNSUPPORTED,
    SKIPPED,
    INDETERMINATE,
    FIXTURE_INVALID,
    IDENTITY_MISMATCH,
    CONTENT_MISMATCH,
    DESTINATION_REPLACED,
    CROSS_VOLUME_COPY_DETECTED,
    DURABILITY_UNCONFIRMED,
)

CONTROL_STATUS_TAXONOMY = (
    CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE,
    CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE,
    CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL,
    CONTROL_ACCESS_REJECTED,
    CONTROL_COLLISION_OBSERVED,
    CONTROL_FIXTURE_INVALID,
    CONTROL_SAME_VOLUME_REJECTED,
    CONTROL_REPARSE_REJECTED,
    CONTROL_CONTAINMENT_REJECTED,
    CONTROL_SKIPPED_FIXTURE_UNAVAILABLE,
    CONTROL_NATIVE_ERROR_INDETERMINATE,
    CONTROL_FAULT_INJECTED,
    CONTROL_IDENTITY_MISMATCH,
    CONTROL_CONTENT_MISMATCH,
    CONTROL_DESTINATION_REPLACED,
)

NAME_INVALID = "NAME_INVALID"
FIXTURE_ROOT_INVALID = "FIXTURE_ROOT_INVALID"
PATH_OUTSIDE_FIXTURE_ROOT = "PATH_OUTSIDE_FIXTURE_ROOT"
PATH_DANGEROUS = "PATH_DANGEROUS"
PATH_NOT_DIRECTORY = "PATH_NOT_DIRECTORY"
PATH_REPARSE_POINT = "PATH_REPARSE_POINT"
PATH_MISSING = "PATH_MISSING"
SOURCE_EMPTY = "SOURCE_EMPTY"
SOURCE_MANIFEST_BOUNDS_EXCEEDED = "SOURCE_MANIFEST_BOUNDS_EXCEEDED"
UNSUPPORTED_PLATFORM = "UNSUPPORTED_PLATFORM"
UNSUPPORTED_WINDOWS_PROFILE = "UNSUPPORTED_WINDOWS_PROFILE"
UNSUPPORTED_DRIVE_PROFILE = "UNSUPPORTED_DRIVE_PROFILE"
UNSUPPORTED_FILESYSTEM_PROFILE = "UNSUPPORTED_FILESYSTEM_PROFILE"
UNSUPPORTED_VOLUME_RELATIONSHIP = "UNSUPPORTED_VOLUME_RELATIONSHIP"
NATIVE_OPEN_FAILED = "NATIVE_OPEN_FAILED"
NATIVE_RENAME_FAILED = "NATIVE_RENAME_FAILED"
NATIVE_IDENTITY_FAILED = "NATIVE_IDENTITY_FAILED"
NATIVE_DURABILITY_FAILED = "NATIVE_DURABILITY_FAILED"
DESTINATION_ALREADY_EXISTS = "DESTINATION_ALREADY_EXISTS"
SECOND_VOLUME_UNAVAILABLE = "SKIPPED_SECOND_VOLUME_UNAVAILABLE"
FAULT_INJECTED = "FAULT_INJECTED"

FAILURE_CODE_VOCABULARY = (
    NAME_INVALID,
    FIXTURE_ROOT_INVALID,
    PATH_OUTSIDE_FIXTURE_ROOT,
    PATH_DANGEROUS,
    PATH_NOT_DIRECTORY,
    PATH_REPARSE_POINT,
    PATH_MISSING,
    SOURCE_EMPTY,
    SOURCE_MANIFEST_BOUNDS_EXCEEDED,
    UNSUPPORTED_PLATFORM,
    UNSUPPORTED_WINDOWS_PROFILE,
    UNSUPPORTED_DRIVE_PROFILE,
    UNSUPPORTED_FILESYSTEM_PROFILE,
    UNSUPPORTED_VOLUME_RELATIONSHIP,
    NATIVE_OPEN_FAILED,
    NATIVE_RENAME_FAILED,
    NATIVE_IDENTITY_FAILED,
    NATIVE_DURABILITY_FAILED,
    DESTINATION_ALREADY_EXISTS,
    SECOND_VOLUME_UNAVAILABLE,
    FAULT_INJECTED,
)

FAULT_POINTS = (
    "F1_PRE_ADMISSION",
    "F2_AFTER_MANIFEST_BEFORE_HANDLE_OPEN",
    "F3_AFTER_HANDLE_OPEN_BEFORE_NATIVE_RENAME",
    "F4_AFTER_NATIVE_RENAME_BEFORE_IDENTITY_CHECK",
    "F5_AFTER_IDENTITY_BEFORE_DURABILITY",
    "F6_AFTER_DURABILITY_BEFORE_RESULT",
)

ABSOLUTE_PATH_CONTROL_FAULT_POINTS = (
    "A_FAULT_AFTER_FIXTURE_ADMISSION",
    "A_FAULT_AFTER_SOURCE_HANDLE_OPEN",
    "A_FAULT_AFTER_DESTINATION_PARENT_EVIDENCE",
    "A_FAULT_AFTER_ABSOLUTE_PATH_DERIVATION",
    "A_FAULT_AFTER_BUFFER_CONSTRUCTION",
    "A_FAULT_BEFORE_NATIVE_CALL",
    "A_FAULT_AFTER_NATIVE_SUCCESS",
    "A_FAULT_BEFORE_POST_TRANSITION_VERIFICATION",
)

MAX_FINAL_NAME_UTF16_BYTES = 240
MAX_ABSOLUTE_CONTROL_PATH_UTF16_BYTES = 4096
MAX_MANIFEST_ENTRIES = 64
MAX_MANIFEST_FILE_BYTES = 1024 * 1024
MAX_MANIFEST_TOTAL_BYTES = 4 * 1024 * 1024
MAX_MANIFEST_DEPTH = 8
RACE_ITERATION_COUNT = 8

DELETE = 0x00010000
FILE_LIST_DIRECTORY = 0x00000001
FILE_ADD_FILE = 0x00000002
FILE_ADD_SUBDIRECTORY = 0x00000004
FILE_READ_ATTRIBUTES = 0x00000080
GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_ATTRIBUTE_DIRECTORY = 0x00000010
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
DRIVE_FIXED = 3
MAX_PATH = 260
FileRenameInfo = 3

ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3
ERROR_ACCESS_DENIED = 5
ERROR_NOT_SAME_DEVICE = 17
ERROR_SHARING_VIOLATION = 32
ERROR_LOCK_VIOLATION = 33
ERROR_NOT_SUPPORTED = 50
ERROR_FILE_EXISTS = 80
ERROR_INVALID_PARAMETER = 87
ERROR_INVALID_NAME = 123
ERROR_DIR_NOT_EMPTY = 145
ERROR_ALREADY_EXISTS = 183
ERROR_PRIVILEGE_NOT_HELD = 1314

ERROR_NAMES = {
    ERROR_FILE_NOT_FOUND: "ERROR_FILE_NOT_FOUND",
    ERROR_PATH_NOT_FOUND: "ERROR_PATH_NOT_FOUND",
    ERROR_ACCESS_DENIED: "ERROR_ACCESS_DENIED",
    ERROR_NOT_SAME_DEVICE: "ERROR_NOT_SAME_DEVICE",
    ERROR_SHARING_VIOLATION: "ERROR_SHARING_VIOLATION",
    ERROR_LOCK_VIOLATION: "ERROR_LOCK_VIOLATION",
    ERROR_NOT_SUPPORTED: "ERROR_NOT_SUPPORTED",
    ERROR_FILE_EXISTS: "ERROR_FILE_EXISTS",
    ERROR_INVALID_PARAMETER: "ERROR_INVALID_PARAMETER",
    ERROR_INVALID_NAME: "ERROR_INVALID_NAME",
    ERROR_DIR_NOT_EMPTY: "ERROR_DIR_NOT_EMPTY",
    ERROR_ALREADY_EXISTS: "ERROR_ALREADY_EXISTS",
    ERROR_PRIVILEGE_NOT_HELD: "ERROR_PRIVILEGE_NOT_HELD",
}

COLLISION_ERROR_CODES = frozenset(
    (ERROR_FILE_EXISTS, ERROR_ALREADY_EXISTS, ERROR_ACCESS_DENIED, ERROR_DIR_NOT_EMPTY)
)

_KERNEL32 = None


class ValidationError(ValueError):
    pass


class FixtureInvalidError(ValidationError):
    pass


class UnsupportedProfileError(ValidationError):
    pass


@dataclass(frozen=True)
class FinalNameValidation:
    accepted: bool
    name: str
    reason: str | None = None


@dataclass(frozen=True)
class RenameInfoOffsets:
    replace_if_exists_or_flags: int
    root_directory: int
    file_name_length: int
    file_name: int
    root_directory_width: int
    file_name_length_width: int


@dataclass(frozen=True)
class RenameInfoBuffer:
    buffer: Any
    size: int
    final_name: str
    encoded_name: bytes
    offsets: RenameInfoOffsets

    @property
    def pointer(self) -> int:
        return ctypes.addressof(self.buffer)

    def as_bytes(self) -> bytes:
        return bytes(self.buffer.raw[: self.size])


@dataclass(frozen=True)
class ObjectIdentity:
    volume_serial_number: int
    file_index_high: int
    file_index_low: int

    def as_tuple(self) -> tuple[int, int, int]:
        return (
            self.volume_serial_number,
            self.file_index_high,
            self.file_index_low,
        )


@dataclass(frozen=True)
class ManifestEntry:
    relative_path: str
    entry_type: str
    size: int
    sha256: str | None = None


@dataclass(frozen=True)
class ContentManifest:
    entries: tuple[ManifestEntry, ...]
    entry_count: int
    total_file_bytes: int
    manifest_sha256: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "entries": [asdict(entry) for entry in self.entries],
            "entry_count": self.entry_count,
            "total_file_bytes": self.total_file_bytes,
            "manifest_sha256": self.manifest_sha256,
        }


@dataclass(frozen=True)
class SupportProfile:
    supported: bool
    status: str
    detail: str
    failure_code: str | None = None
    drive_type: int | None = None
    filesystem_name: str | None = None
    source_volume_serial_number: int | None = None
    destination_volume_serial_number: int | None = None


@dataclass(frozen=True)
class NativePromotionOutcome:
    succeeded: bool
    detail: str
    native_error_code: int | None = None
    native_error_name: str | None = None


@dataclass(frozen=True)
class DurabilityProbe:
    probe_id: str
    status: str
    detail: str
    failure_code: str | None = None
    native_error_code: int | None = None
    native_error_name: str | None = None
    adapter_policy_identity: dict[str, str] | None = None


@dataclass(frozen=True)
class ValidationCaseResult:
    case_id: str
    status: str
    detail: str
    failure_code: str | None = None
    skip_reason: str | None = None
    native_error_code: int | None = None
    native_error_name: str | None = None
    policy_identity: dict[str, str] | None = None
    support_profile: SupportProfile | None = None
    source_identity_before: ObjectIdentity | None = None
    retained_handle_identity_after: ObjectIdentity | None = None
    final_identity_after: ObjectIdentity | None = None
    source_parent_identity_before: ObjectIdentity | None = None
    source_parent_identity_after: ObjectIdentity | None = None
    destination_parent_identity_before: ObjectIdentity | None = None
    destination_parent_identity_after: ObjectIdentity | None = None
    source_exists_after_native_failure: bool | None = None
    final_exists_after_native_failure: bool | None = None
    manifest_before_sha256: str | None = None
    manifest_after_sha256: str | None = None
    durability_probes: tuple[DurabilityProbe, ...] = ()

    def as_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["policy_identity"] = self.policy_identity or validation_policy_identity()
        return payload


class _FILETIME(ctypes.Structure):
    _fields_ = (
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    )


class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = (
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", _FILETIME),
        ("ftLastAccessTime", _FILETIME),
        ("ftLastWriteTime", _FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    )


class _RENAME_INFO_UNION(ctypes.Union):
    _fields_ = (
        ("ReplaceIfExists", wintypes.BOOL),
        ("Flags", wintypes.DWORD),
    )


class _FILE_RENAME_INFO_PROBE(ctypes.Structure):
    _fields_ = (
        ("replace_or_flags", _RENAME_INFO_UNION),
        ("RootDirectory", wintypes.HANDLE),
        ("FileNameLength", wintypes.DWORD),
        ("FileName", ctypes.c_uint16 * 1),
    )


class _Handle:
    def __init__(self, handle: int | None):
        self.handle = handle

    def __enter__(self) -> "_Handle":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def close(self) -> None:
        if self.handle is None:
            return
        kernel32 = _kernel32()
        kernel32.CloseHandle(self.handle)
        self.handle = None


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def validation_policy_declaration() -> dict[str, Any]:
    return {
        "policy_schema_identity": VALIDATION_POLICY_SCHEMA,
        "implementation_surface_identity": IMPLEMENTATION_SURFACE_IDENTITY,
        "operation_identity": PRIMITIVE_OPERATION_IDENTITY,
        "baseline_commit": BASELINE_COMMIT,
        "supported_platform_profile": {
            "os": "windows",
            "minimum_major_version": 10,
            "product_type": "workstation",
            "drive_type": "DRIVE_FIXED",
            "filesystem": "NTFS",
            "same_volume_required": True,
            "destination_name": "simple relative single component absent for positive",
        },
        "native_contract": {
            "source_desired_access": "DELETE",
            "share_mode": [
                "FILE_SHARE_READ",
                "FILE_SHARE_WRITE",
                "FILE_SHARE_DELETE",
            ],
            "creation_disposition": "OPEN_EXISTING",
            "source_flags": [
                "FILE_FLAG_BACKUP_SEMANTICS",
                "FILE_FLAG_OPEN_REPARSE_POINT",
            ],
            "file_information_class": "FileRenameInfo",
            "replace_if_exists": False,
            "destination_root_directory_handle": True,
        },
        "native_error_classification": {
            "ERROR_INVALID_PARAMETER": (
                "INDETERMINATE_NATIVE_CONTRACT_REJECTION_CAUSE_UNRESOLVED"
            ),
            "ERROR_NOT_SUPPORTED": "UNSUPPORTED_NATIVE_PRIMITIVE",
            "unknown_native_error": "FAILED_OR_INDETERMINATE_FAIL_CLOSED",
        },
        "held_outcome_wording": HELD_OUTCOME_WORDING,
        "file_rename_info_buffer_policy": {
            "variable_length_buffer": True,
            "utf16le_file_name_length_bytes": True,
            "no_fixed_wchar_one_write": True,
            "offsets_validated": True,
            "max_final_name_utf16_bytes": MAX_FINAL_NAME_UTF16_BYTES,
        },
        "fixture_containment_policy": {
            "requires_authorized_fixture_root": True,
            "rejects_repository_root": True,
            "rejects_git_component": True,
            "rejects_system_directories": True,
            "rejects_direct_user_profile_directories": True,
            "rejects_reparse_entries": True,
            "canonical_relationship_check": True,
        },
        "manifest_bounds": {
            "max_entries": MAX_MANIFEST_ENTRIES,
            "max_file_bytes": MAX_MANIFEST_FILE_BYTES,
            "max_total_file_bytes": MAX_MANIFEST_TOTAL_BYTES,
            "max_depth": MAX_MANIFEST_DEPTH,
        },
        "status_taxonomy": list(STATUS_TAXONOMY),
        "failure_code_vocabulary": list(FAILURE_CODE_VOCABULARY),
        "fault_points": list(FAULT_POINTS),
        "race_iteration_count": RACE_ITERATION_COUNT,
        "directory_durability_policy_identity": (
            durable_schema.directory_durability_policy_identity()
        ),
        "validation_profile_identity": VALIDATION_PROFILE_IDENTITY,
    }


def validation_policy_identity() -> dict[str, str]:
    return {
        "policy_schema_identity": VALIDATION_POLICY_SCHEMA,
        "policy_sha256": sha256_hex(canonical_json_bytes(validation_policy_declaration())),
    }


def absolute_path_control_policy_declaration() -> dict[str, Any]:
    return {
        "policy_schema_identity": ABSOLUTE_PATH_CONTROL_POLICY_SCHEMA,
        "control_version": ABSOLUTE_PATH_CONTROL_VERSION,
        "control_mode": ABSOLUTE_PATH_CONTROL_MODE,
        "authorization_commit": ABSOLUTE_PATH_CONTROL_AUTHORIZATION_COMMIT,
        "implementation_surface_identity": IMPLEMENTATION_SURFACE_IDENTITY,
        "authorized_implementation_files": list(_authorized_control_files()),
        "implementation_file_identities": _authorized_control_file_identities(),
        "prior_rootdirectory_relative_policy_identity": validation_policy_identity(),
        "native_contract": {
            "api": "SetFileInformationByHandle",
            "file_information_class": "FileRenameInfo",
            "structure": "FILE_RENAME_INFO",
            "replace_if_exists": False,
            "root_directory": None,
            "file_name": (
                "canonical fully qualified drive-qualified Win32 DOS absolute "
                "destination path"
            ),
            "copy_delete_fallback": False,
        },
        "file_rename_info_buffer_policy": {
            "file_name_length_utf16le_bytes": True,
            "file_name_length_excludes_terminating_nul": True,
            "absolute_path_allocation_terminating_nul": True,
            "rootdirectory_relative_buffer_unchanged": True,
        },
        "source_handle_contract": {
            "desired_access": "DELETE",
            "share_mode": [
                "FILE_SHARE_READ",
                "FILE_SHARE_WRITE",
                "FILE_SHARE_DELETE",
            ],
            "creation_disposition": "OPEN_EXISTING",
            "flags": [
                "FILE_FLAG_BACKUP_SEMANTICS",
                "FILE_FLAG_OPEN_REPARSE_POINT",
            ],
        },
        "path_policy": {
            "derived_from_fixture_objects_only": True,
            "fully_qualified": True,
            "drive_qualified": True,
            "local_win32_dos_form": True,
            "reject_unc": True,
            "reject_device_paths": True,
            "reject_nt_object_manager_paths": True,
            "reject_volume_guid_paths": True,
            "reject_extended_length_prefix": True,
            "component_boundary_containment": True,
            "max_utf16le_bytes": MAX_ABSOLUTE_CONTROL_PATH_UTF16_BYTES,
        },
        "fixture_admission_policy": {
            "os": "windows",
            "minimum_major_version": 10,
            "product_type": "workstation",
            "drive_type": "DRIVE_FIXED",
            "filesystem": "NTFS",
            "same_volume_required": True,
            "reject_repository_root": True,
            "reject_git_component": True,
            "reject_reparse_entries": True,
        },
        "same_volume_policy": {
            "textual_drive_letter_only_is_insufficient": True,
            "volume_serial_evidence": True,
            "filesystem_name_evidence": True,
            "drive_type_evidence": True,
            "source_identity_evidence": True,
            "destination_parent_identity_evidence": True,
        },
        "case_matrix": [
            "A1_POSITIVE_ABSOLUTE_PATH_RENAME",
            "A2_EXISTING_DESTINATION_DIRECTORY",
            "A3_EXISTING_DESTINATION_FILE",
            "A4_COORDINATED_DESTINATION_CLAIM",
            "A5_SOURCE_TO_FINAL_IDENTITY_CONTINUITY",
            "A6_NATIVE_ERROR_CHARACTERIZATION",
            "A7_INVALID_OR_ESCAPING_ABSOLUTE_DESTINATION_REJECTED",
            "A8_SAME_VOLUME_MISMATCH_REJECTED",
        ],
        "result_taxonomy": list(CONTROL_STATUS_TAXONOMY),
        "native_error_classification": {
            "ERROR_INVALID_PARAMETER": (
                "CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE"
            ),
            "ERROR_NOT_SUPPORTED": "CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL",
            "ERROR_ACCESS_DENIED": "CONTROL_ACCESS_REJECTED",
            "collision_error_codes": "CONTROL_COLLISION_OBSERVED",
            "unknown_native_error": "CONTROL_NATIVE_ERROR_INDETERMINATE",
        },
        "fault_points": list(ABSOLUTE_PATH_CONTROL_FAULT_POINTS),
        "test_authority": [
            "focused ephemeral unit tests",
            "focused ephemeral Windows integration tests",
            "relevant BLOCKER-1 regressions where needed",
        ],
        "retained_execution_prohibition": True,
        "validation_profile_identity": ABSOLUTE_PATH_CONTROL_PROFILE_IDENTITY,
    }


def absolute_path_control_policy_identity() -> dict[str, str]:
    return {
        "policy_schema_identity": ABSOLUTE_PATH_CONTROL_POLICY_SCHEMA,
        "policy_sha256": sha256_hex(
            canonical_json_bytes(absolute_path_control_policy_declaration())
        ),
    }


def validate_final_name(name: str) -> FinalNameValidation:
    if not isinstance(name, str):
        return FinalNameValidation(False, "", "name is not a string")
    if name == "":
        return FinalNameValidation(False, name, "name is empty")
    if "\x00" in name:
        return FinalNameValidation(False, name, "name contains embedded NUL")
    if name in (".", ".."):
        return FinalNameValidation(False, name, "name is dot component")
    if "/" in name or "\\" in name:
        return FinalNameValidation(False, name, "name contains a path separator")
    if ntpath.isabs(name) or ntpath.splitdrive(name)[0]:
        return FinalNameValidation(False, name, "name is absolute or drive-qualified")
    if name.startswith("\\\\") or name.startswith("\\\\?\\") or name.startswith("\\??\\"):
        return FinalNameValidation(False, name, "name is UNC or device qualified")
    if ":" in name:
        return FinalNameValidation(False, name, "name contains stream syntax")
    if any(char in name for char in "*?"):
        return FinalNameValidation(False, name, "name contains wildcard syntax")
    if any(char in name for char in '<>|"'):
        return FinalNameValidation(False, name, "name contains invalid syntax")
    encoded = name.encode("utf-16-le")
    if len(encoded) == 0:
        return FinalNameValidation(False, name, "name encodes to zero bytes")
    if len(encoded) > MAX_FINAL_NAME_UTF16_BYTES:
        return FinalNameValidation(False, name, "name exceeds bounded byte length")
    return FinalNameValidation(True, name)


def validate_absolute_win32_dos_path_text(path: str | Path) -> FinalNameValidation:
    if not isinstance(path, (str, Path)):
        return FinalNameValidation(False, "", "path is not string-like")
    text = str(path)
    if text == "":
        return FinalNameValidation(False, text, "absolute path is empty")
    if "\x00" in text:
        return FinalNameValidation(False, text, "absolute path contains embedded NUL")
    if "/" in text:
        return FinalNameValidation(False, text, "absolute path contains non-DOS separator")
    if text.startswith("\\\\?\\"):
        return FinalNameValidation(False, text, "extended-length path is forbidden")
    if text.startswith("\\??\\"):
        return FinalNameValidation(False, text, "NT object-manager path is forbidden")
    if text.startswith("\\\\.\\"):
        return FinalNameValidation(False, text, "device path is forbidden")
    if text.startswith("\\\\"):
        return FinalNameValidation(False, text, "UNC path is forbidden")
    drive, tail = ntpath.splitdrive(text)
    if len(drive) != 2 or drive[1] != ":" or not drive[0].isalpha():
        return FinalNameValidation(False, text, "path is not drive-qualified")
    if not ntpath.isabs(text):
        return FinalNameValidation(False, text, "path is not fully qualified")
    parts = tail.split("\\")
    if parts[:1] != [""]:
        return FinalNameValidation(False, text, "path root is malformed")
    components = parts[1:]
    if not components:
        return FinalNameValidation(False, text, "path has no final component")
    for component in components:
        if component in ("", ".", ".."):
            return FinalNameValidation(False, text, "path contains traversal or empty component")
        if ":" in component:
            return FinalNameValidation(False, text, "path contains stream syntax")
        if any(char in component for char in "*?"):
            return FinalNameValidation(False, text, "path contains wildcard syntax")
        if any(char in component for char in '<>|"'):
            return FinalNameValidation(False, text, "path contains invalid syntax")
    encoded = text.encode("utf-16-le")
    if len(encoded) == 0:
        return FinalNameValidation(False, text, "path encodes to zero bytes")
    if len(encoded) > MAX_ABSOLUTE_CONTROL_PATH_UTF16_BYTES:
        return FinalNameValidation(False, text, "path exceeds bounded byte length")
    return FinalNameValidation(True, text)


def rename_info_offsets() -> RenameInfoOffsets:
    return RenameInfoOffsets(
        replace_if_exists_or_flags=_FILE_RENAME_INFO_PROBE.replace_or_flags.offset,
        root_directory=_FILE_RENAME_INFO_PROBE.RootDirectory.offset,
        file_name_length=_FILE_RENAME_INFO_PROBE.FileNameLength.offset,
        file_name=_FILE_RENAME_INFO_PROBE.FileName.offset,
        root_directory_width=ctypes.sizeof(wintypes.HANDLE),
        file_name_length_width=ctypes.sizeof(wintypes.DWORD),
    )


def _root_directory_buffer_value(root_directory_handle: int | None) -> int | None:
    if root_directory_handle is None:
        return None
    value = int(root_directory_handle)
    if value == 0:
        return None
    return value


def _build_file_rename_info_buffer_from_text(
    *,
    root_directory_handle: int | None,
    file_name_text: str,
    append_nul_terminator: bool = False,
) -> RenameInfoBuffer:
    encoded = file_name_text.encode("utf-16-le")
    terminator = b"\x00\x00" if append_nul_terminator else b""
    offsets = rename_info_offsets()
    if offsets.replace_if_exists_or_flags != 0:
        raise ValidationError("FILE_RENAME_INFO union offset is invalid")
    if offsets.root_directory_width not in (4, 8):
        raise ValidationError("RootDirectory HANDLE width is invalid")
    if offsets.file_name_length_width != 4:
        raise ValidationError("FileNameLength DWORD width is invalid")
    if offsets.file_name <= offsets.file_name_length:
        raise ValidationError("FileName offset does not follow FileNameLength")
    size = offsets.file_name + len(encoded) + len(terminator)
    if size <= offsets.file_name:
        raise ValidationError("FILE_RENAME_INFO allocation size is invalid")
    buffer = ctypes.create_string_buffer(size)
    ctypes.c_uint32.from_buffer(
        buffer,
        offsets.replace_if_exists_or_flags,
    ).value = 0
    ctypes.c_void_p.from_buffer(buffer, offsets.root_directory).value = (
        _root_directory_buffer_value(root_directory_handle)
    )
    ctypes.c_uint32.from_buffer(buffer, offsets.file_name_length).value = len(encoded)
    ctypes.memmove(ctypes.addressof(buffer) + offsets.file_name, encoded, len(encoded))
    if terminator:
        ctypes.memmove(
            ctypes.addressof(buffer) + offsets.file_name + len(encoded),
            terminator,
            len(terminator),
        )
    result = RenameInfoBuffer(
        buffer=buffer,
        size=size,
        final_name=file_name_text,
        encoded_name=encoded,
        offsets=offsets,
    )
    validate_file_rename_info_buffer(
        result,
        root_directory_handle=root_directory_handle,
        allow_trailing_nul=append_nul_terminator,
    )
    return result


def build_file_rename_info_buffer(
    *,
    root_directory_handle: int,
    final_name: str,
) -> RenameInfoBuffer:
    validation = validate_final_name(final_name)
    if not validation.accepted:
        raise ValidationError(validation.reason or "invalid final name")
    return _build_file_rename_info_buffer_from_text(
        root_directory_handle=root_directory_handle,
        file_name_text=final_name,
    )


def build_absolute_path_file_rename_info_buffer(
    *,
    absolute_destination_path: str | Path,
) -> RenameInfoBuffer:
    validation = validate_absolute_win32_dos_path_text(absolute_destination_path)
    if not validation.accepted:
        raise ValidationError(validation.reason or "invalid absolute destination path")
    return _build_file_rename_info_buffer_from_text(
        root_directory_handle=None,
        file_name_text=validation.name,
        append_nul_terminator=True,
    )


def validate_file_rename_info_buffer(
    value: RenameInfoBuffer,
    *,
    root_directory_handle: int | None,
    allow_trailing_nul: bool = False,
) -> None:
    raw = value.as_bytes()
    offsets = value.offsets
    if len(raw) != value.size:
        raise ValidationError("buffer size mismatch")
    replace_value = ctypes.c_uint32.from_buffer_copy(
        raw,
        offsets.replace_if_exists_or_flags,
    ).value
    if replace_value != 0:
        raise ValidationError("ReplaceIfExists is not FALSE")
    observed_root = ctypes.c_void_p.from_buffer_copy(raw, offsets.root_directory).value
    expected_root = _root_directory_buffer_value(root_directory_handle)
    if observed_root != expected_root:
        raise ValidationError("RootDirectory handle mismatch")
    observed_length = ctypes.c_uint32.from_buffer_copy(
        raw,
        offsets.file_name_length,
    ).value
    if observed_length != len(value.encoded_name):
        raise ValidationError("FileNameLength byte length mismatch")
    expected_end = offsets.file_name + len(value.encoded_name)
    if raw[offsets.file_name : expected_end] != value.encoded_name:
        raise ValidationError("FileName payload mismatch")
    if allow_trailing_nul:
        if value.size != expected_end + 2:
            raise ValidationError("buffer trailing NUL size mismatch")
        if raw[expected_end:] != b"\x00\x00":
            raise ValidationError("buffer trailing NUL mismatch")
    elif value.size != expected_end:
        raise ValidationError("buffer contains trailing data")
    alignment = ctypes.alignment(_FILE_RENAME_INFO_PROBE)
    if alignment > 1 and value.pointer % alignment != 0:
        raise ValidationError("buffer pointer alignment is invalid")


def build_validation_record(
    *,
    case_results: tuple[ValidationCaseResult, ...],
) -> dict[str, Any]:
    return {
        "schema": "blocker-2-promotion-primitive-validation-record-v0.1",
        "baseline_commit": BASELINE_COMMIT,
        "validation_policy_identity": validation_policy_identity(),
        "source_identities": validation_source_identities(),
        "case_results": [case.as_payload() for case in case_results],
    }


def write_temporary_validation_record(
    *,
    fixture_root: str | Path,
    output_directory: str | Path,
    record: dict[str, Any],
) -> Path:
    root = validate_fixture_root(fixture_root)
    output = _canonical_path(output_directory, must_exist=False)
    _ensure_inside(output, root)
    if _has_git_component(output):
        raise FixtureInvalidError("output path contains .git")
    output.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(record)
    target = output / "blocker_2_promotion_validation_record_v0_1.json"
    target.write_bytes(payload + b"\n")
    return target


def module_source_sha256() -> str:
    return file_sha256(Path(__file__))


def validation_schema_source_sha256() -> str:
    return module_source_sha256()


def file_sha256(path: str | Path) -> str:
    return sha256_hex(Path(path).read_bytes())


def validation_source_identities() -> dict[str, Any]:
    docs = _document_identity_map()
    return {
        "runner_source_sha256": module_source_sha256(),
        "schema_source_sha256": validation_schema_source_sha256(),
        "policy_identity": validation_policy_identity(),
        "fixture_profile_identity": VALIDATION_PROFILE_IDENTITY,
        "primitive_research_doc_identity": docs["primitive_research"],
        "assessment_doc_identity": docs["assessment"],
        "authorization_doc_identity": docs["authorization"],
        "baseline_commit": BASELINE_COMMIT,
    }


def _document_identity_map() -> dict[str, dict[str, Any]]:
    repo = _repo_root()
    paths = {
        "primitive_research": repo
        / "docs"
        / (
            "TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_WINDOWS_SAME_VOLUME_"
            "NO_REPLACE_DIRECTORY_PROMOTION_PRIMARY_SOURCE_PRIMITIVE_RESEARCH_v0.1.md"
        ),
        "assessment": repo
        / "docs"
        / (
            "TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SAME_VOLUME_NO_REPLACE_"
            "PROMOTION_AND_FINAL_OWNERSHIP_ASSESSMENT_v0.1.md"
        ),
        "authorization": repo
        / "docs"
        / (
            "TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_BOUNDED_WINDOWS_SAME_"
            "VOLUME_NO_REPLACE_DIRECTORY_PROMOTION_PRIMITIVE_VALIDATION_"
            "AUTHORIZATION_v0.1.md"
        ),
    }
    result = {}
    for key, path in paths.items():
        result[key] = {
            "path": str(path),
            "raw_sha256": file_sha256(path) if path.exists() else None,
        }
    return result


def _authorized_control_files() -> tuple[str, ...]:
    return (
        "research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py",
        "research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py",
        (
            "research/brainvision/"
            "test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py"
        ),
    )


def _authorized_control_file_identities() -> dict[str, str | None]:
    repo = _repo_root()
    return {
        relative: file_sha256(repo / relative) if (repo / relative).exists() else None
        for relative in _authorized_control_files()
    }


def validate_fixture_root(path: str | Path) -> Path:
    raw = Path(path)
    if raw.is_absolute() and raw.exists() and _is_reparse_point(raw):
        raise FixtureInvalidError("fixture root is a reparse point")
    root = _canonical_path(path, must_exist=True)
    if not root.is_dir():
        raise FixtureInvalidError("fixture root is not a directory")
    if _has_git_component(root):
        raise FixtureInvalidError("fixture root contains .git")
    if _is_dangerous_root(root):
        raise FixtureInvalidError("fixture root is dangerous")
    if _is_reparse_point(root):
        raise FixtureInvalidError("fixture root is a reparse point")
    return root


def validate_child_path(
    path: str | Path,
    *,
    fixture_root: str | Path,
    must_exist: bool,
) -> Path:
    root = validate_fixture_root(fixture_root)
    raw = Path(path)
    if raw.is_absolute() and must_exist and raw.exists() and _is_reparse_point(raw):
        raise FixtureInvalidError("candidate path is a reparse point")
    candidate = _canonical_path(path, must_exist=must_exist)
    _ensure_inside(candidate, root)
    if _has_git_component(candidate):
        raise FixtureInvalidError("candidate path contains .git")
    if _is_dangerous_root(candidate):
        raise FixtureInvalidError("candidate path is dangerous")
    return candidate


def _canonical_path(path: str | Path, *, must_exist: bool) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise FixtureInvalidError("path is not absolute")
    try:
        return candidate.resolve(strict=must_exist)
    except OSError as exc:
        if must_exist:
            raise FixtureInvalidError("path does not exist") from exc
        existing_parent = candidate.parent.resolve(strict=True)
        return existing_parent / candidate.name


def _ensure_inside(candidate: Path, root: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise FixtureInvalidError("path is outside fixture root") from exc


def _ensure_existing_ancestors_non_reparse(candidate: Path, root: Path) -> None:
    current = candidate if candidate.exists() else candidate.parent
    while True:
        _ensure_inside(current, root)
        if _is_reparse_point(current):
            raise FixtureInvalidError("path ancestor is a reparse point")
        if current == root:
            break
        parent = current.parent
        if parent == current:
            raise FixtureInvalidError("path escaped before fixture root")
        current = parent


def derive_absolute_control_destination(
    *,
    fixture_root: str | Path,
    destination_parent: str | Path,
    final_name: str,
) -> tuple[Path, str]:
    final_name_validation = validate_final_name(final_name)
    if not final_name_validation.accepted:
        raise FixtureInvalidError(final_name_validation.reason or "invalid final name")
    root = validate_fixture_root(fixture_root)
    dest_parent = validate_child_path(
        destination_parent,
        fixture_root=root,
        must_exist=True,
    )
    _validate_ordinary_directory(dest_parent)
    _ensure_existing_ancestors_non_reparse(dest_parent, root)
    final_path = _canonical_path(dest_parent / final_name, must_exist=False)
    _ensure_inside(final_path, root)
    _ensure_inside(final_path, dest_parent)
    absolute_text = str(final_path)
    path_validation = validate_absolute_win32_dos_path_text(absolute_text)
    if not path_validation.accepted:
        raise FixtureInvalidError(path_validation.reason or "invalid absolute path")
    return final_path, path_validation.name


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _has_git_component(path: Path) -> bool:
    return any(part.lower() == ".git" for part in path.parts)


def _is_dangerous_root(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    repo = _repo_root()
    if resolved == repo or repo in resolved.parents:
        return True
    env_roots = []
    for name in ("SystemRoot", "WINDIR", "ProgramFiles", "ProgramFiles(x86)"):
        value = os.environ.get(name)
        if value:
            env_roots.append(Path(value).resolve(strict=False))
    for env_root in env_roots:
        if resolved == env_root or env_root in resolved.parents:
            return True
    home = Path.home().resolve(strict=False)
    profile_dirs = (
        home,
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Pictures",
        home / "Music",
        home / "Videos",
    )
    return any(resolved == directory for directory in profile_dirs)


def _is_windows() -> bool:
    return sys.platform == "win32"


def _kernel32():
    global _KERNEL32
    if not _is_windows():
        raise UnsupportedProfileError("native Win32 calls are unsupported here")
    if _KERNEL32 is not None:
        return _KERNEL32
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=False)
    kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.SetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.GetLastError.argtypes = ()
    kernel32.GetLastError.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.GetFileAttributesW.argtypes = (wintypes.LPCWSTR,)
    kernel32.GetFileAttributesW.restype = wintypes.DWORD
    kernel32.GetDriveTypeW.argtypes = (wintypes.LPCWSTR,)
    kernel32.GetDriveTypeW.restype = wintypes.UINT
    kernel32.GetVolumeInformationW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.LPDWORD,
        wintypes.LPDWORD,
        wintypes.LPDWORD,
        wintypes.LPWSTR,
        wintypes.DWORD,
    )
    kernel32.GetVolumeInformationW.restype = wintypes.BOOL
    kernel32.GetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION),
    )
    kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
    kernel32.FlushFileBuffers.restype = wintypes.BOOL
    _KERNEL32 = kernel32
    return kernel32


def _windows_api_path(path: str | Path) -> str:
    text = str(path)
    if text.startswith("\\\\?\\"):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text.lstrip("\\")
    return "\\\\?\\" + text


def _drive_root(path: Path) -> str | None:
    drive = path.drive
    if len(drive) == 2 and drive[1] == ":":
        return drive + "\\"
    return None


def _is_invalid_handle(handle: int | None) -> bool:
    return handle in (None, 0, ctypes.c_void_p(-1).value)


def _error_name(error_code: int | None) -> str | None:
    if error_code is None:
        return None
    return ERROR_NAMES.get(int(error_code))


def _is_reparse_point(path: str | Path) -> bool:
    if not _is_windows():
        return Path(path).is_symlink()
    kernel32 = _kernel32()
    attributes = kernel32.GetFileAttributesW(_windows_api_path(path))
    if attributes == INVALID_FILE_ATTRIBUTES:
        return False
    return bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)


def _open_directory_handle(
    path: str | Path,
    *,
    desired_access: int,
) -> _Handle | NativePromotionOutcome:
    kernel32 = _kernel32()
    handle = kernel32.CreateFileW(
        _windows_api_path(path),
        desired_access,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if _is_invalid_handle(handle):
        error_code = int(kernel32.GetLastError())
        return NativePromotionOutcome(
            succeeded=False,
            detail="directory handle open failed",
            native_error_code=error_code,
            native_error_name=_error_name(error_code),
        )
    return _Handle(handle)


def identity_from_handle(handle: int) -> ObjectIdentity:
    info = _BY_HANDLE_FILE_INFORMATION()
    kernel32 = _kernel32()
    if not kernel32.GetFileInformationByHandle(handle, ctypes.byref(info)):
        error_code = int(kernel32.GetLastError())
        raise OSError(error_code, _error_name(error_code) or "native identity failed")
    return ObjectIdentity(
        volume_serial_number=int(info.dwVolumeSerialNumber),
        file_index_high=int(info.nFileIndexHigh),
        file_index_low=int(info.nFileIndexLow),
    )


def identity_from_path(path: str | Path) -> ObjectIdentity:
    handle = _open_directory_handle(path, desired_access=FILE_READ_ATTRIBUTES)
    if isinstance(handle, NativePromotionOutcome):
        raise OSError(
            handle.native_error_code or 0,
            handle.native_error_name or handle.detail,
        )
    with handle:
        return identity_from_handle(handle.handle)


def _volume_information(path: Path) -> tuple[int, str, int]:
    root = _drive_root(path)
    if root is None:
        raise UnsupportedProfileError("drive root is unsupported")
    kernel32 = _kernel32()
    drive_type = int(kernel32.GetDriveTypeW(root))
    volume_name = ctypes.create_unicode_buffer(MAX_PATH + 1)
    filesystem_name = ctypes.create_unicode_buffer(MAX_PATH + 1)
    serial = wintypes.DWORD()
    max_component = wintypes.DWORD()
    flags = wintypes.DWORD()
    ok = kernel32.GetVolumeInformationW(
        root,
        volume_name,
        len(volume_name),
        ctypes.byref(serial),
        ctypes.byref(max_component),
        ctypes.byref(flags),
        filesystem_name,
        len(filesystem_name),
    )
    if not ok:
        error_code = int(kernel32.GetLastError())
        raise OSError(error_code, _error_name(error_code) or "volume query failed")
    return drive_type, filesystem_name.value.upper(), int(serial.value)


def admit_support_profile(
    *,
    fixture_root: str | Path,
    source_directory: str | Path,
    destination_parent: str | Path,
) -> SupportProfile:
    if not _is_windows():
        return SupportProfile(
            supported=False,
            status=SKIPPED,
            detail="native validation is skipped on non-Windows platforms",
            failure_code=UNSUPPORTED_PLATFORM,
        )
    version = sys.getwindowsversion()
    if version.major < 10 or getattr(version, "product_type", None) != 1:
        return SupportProfile(
            supported=False,
            status=UNSUPPORTED,
            detail="Windows 10/11 workstation profile is required",
            failure_code=UNSUPPORTED_WINDOWS_PROFILE,
        )
    try:
        root = validate_fixture_root(fixture_root)
        source = validate_child_path(source_directory, fixture_root=root, must_exist=True)
        destination = validate_child_path(
            destination_parent,
            fixture_root=root,
            must_exist=True,
        )
        _validate_ordinary_directory(source)
        _validate_ordinary_directory(destination)
        drive_type, filesystem, source_volume = _volume_information(source)
        _, destination_filesystem, destination_volume = _volume_information(destination)
    except FixtureInvalidError as exc:
        return SupportProfile(
            supported=False,
            status=FIXTURE_INVALID,
            detail=str(exc),
            failure_code=FIXTURE_ROOT_INVALID,
        )
    except UnsupportedProfileError as exc:
        return SupportProfile(
            supported=False,
            status=UNSUPPORTED,
            detail=str(exc),
            failure_code=UNSUPPORTED_DRIVE_PROFILE,
        )
    except OSError as exc:
        return SupportProfile(
            supported=False,
            status=INDETERMINATE,
            detail="support profile could not be determined",
            failure_code=UNSUPPORTED_DRIVE_PROFILE,
            native_error_code=getattr(exc, "winerror", None),
        )
    if drive_type != DRIVE_FIXED:
        return SupportProfile(
            supported=False,
            status=UNSUPPORTED,
            detail="fixture is not on a fixed local drive",
            failure_code=UNSUPPORTED_DRIVE_PROFILE,
            drive_type=drive_type,
            filesystem_name=filesystem,
        )
    if filesystem != "NTFS" or destination_filesystem != "NTFS":
        return SupportProfile(
            supported=False,
            status=UNSUPPORTED,
            detail="fixture filesystem is not NTFS",
            failure_code=UNSUPPORTED_FILESYSTEM_PROFILE,
            drive_type=drive_type,
            filesystem_name=filesystem,
        )
    if source_volume != destination_volume:
        return SupportProfile(
            supported=False,
            status=UNSUPPORTED,
            detail="source and destination are not on the same volume",
            failure_code=UNSUPPORTED_VOLUME_RELATIONSHIP,
            drive_type=drive_type,
            filesystem_name=filesystem,
            source_volume_serial_number=source_volume,
            destination_volume_serial_number=destination_volume,
        )
    return SupportProfile(
        supported=True,
        status=PRIMITIVE_VALIDATION_CONFIRMED,
        detail="supported local fixed NTFS same-volume Windows profile admitted",
        drive_type=drive_type,
        filesystem_name=filesystem,
        source_volume_serial_number=source_volume,
        destination_volume_serial_number=destination_volume,
    )


def _validate_ordinary_directory(path: Path) -> None:
    if not path.exists():
        raise FixtureInvalidError("path is missing")
    if not path.is_dir():
        raise FixtureInvalidError("path is not a directory")
    if _is_reparse_point(path):
        raise FixtureInvalidError("path is a reparse point")


def build_content_manifest(root: str | Path) -> ContentManifest:
    root_path = _canonical_path(root, must_exist=True)
    if not root_path.is_dir():
        raise FixtureInvalidError("manifest root is not a directory")
    if _is_reparse_point(root_path):
        raise FixtureInvalidError("manifest root is a reparse point")
    entries: list[ManifestEntry] = []
    total_bytes = 0
    stack = [(root_path, 0)]
    while stack:
        directory, depth = stack.pop()
        if depth > MAX_MANIFEST_DEPTH:
            raise FixtureInvalidError("manifest depth bound exceeded")
        try:
            children = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise FixtureInvalidError("manifest scan failed") from exc
        for child in children:
            child_path = Path(child.path)
            if child.is_symlink() or _is_reparse_point(child_path):
                raise FixtureInvalidError("manifest entry is a reparse point")
            relative = child_path.relative_to(root_path).as_posix()
            try:
                child_stat = child.stat(follow_symlinks=False)
            except OSError as exc:
                raise FixtureInvalidError("manifest stat failed") from exc
            if stat.S_ISDIR(child_stat.st_mode):
                entries.append(ManifestEntry(relative, "directory", 0))
                stack.append((child_path, depth + 1))
            elif stat.S_ISREG(child_stat.st_mode):
                if child_stat.st_size > MAX_MANIFEST_FILE_BYTES:
                    raise FixtureInvalidError("manifest file byte bound exceeded")
                payload = child_path.read_bytes()
                if len(payload) != child_stat.st_size:
                    raise FixtureInvalidError("manifest file size changed during read")
                total_bytes += len(payload)
                if total_bytes > MAX_MANIFEST_TOTAL_BYTES:
                    raise FixtureInvalidError("manifest total byte bound exceeded")
                entries.append(
                    ManifestEntry(
                        relative_path=relative,
                        entry_type="file",
                        size=len(payload),
                        sha256=sha256_hex(payload),
                    )
                )
            else:
                raise FixtureInvalidError("manifest entry type is unsupported")
            if len(entries) > MAX_MANIFEST_ENTRIES:
                raise FixtureInvalidError("manifest entry count bound exceeded")
    entries_tuple = tuple(sorted(entries, key=lambda entry: entry.relative_path))
    preimage = {
        "entries": [asdict(entry) for entry in entries_tuple],
        "entry_count": len(entries_tuple),
        "total_file_bytes": total_bytes,
    }
    return ContentManifest(
        entries=entries_tuple,
        entry_count=len(entries_tuple),
        total_file_bytes=total_bytes,
        manifest_sha256=sha256_hex(canonical_json_bytes(preimage)),
    )


def require_absolute_path_control_mode(mode: str) -> str:
    if mode != ABSOLUTE_PATH_CONTROL_MODE:
        raise ValidationError("absolute-path control mode must be explicitly selected")
    return mode


def build_absolute_path_control_record(
    *,
    case_results: tuple[ValidationCaseResult, ...],
) -> dict[str, Any]:
    return {
        "schema": "blocker-2-absolute-path-promotion-control-record-v0.1",
        "authorization_commit": ABSOLUTE_PATH_CONTROL_AUTHORIZATION_COMMIT,
        "control_mode": ABSOLUTE_PATH_CONTROL_MODE,
        "control_policy_identity": absolute_path_control_policy_identity(),
        "case_results": [case.as_payload() for case in case_results],
        "retained_execution": False,
    }


def derive_absolute_control_fault_point_result(fault_point: str) -> ValidationCaseResult:
    if fault_point not in ABSOLUTE_PATH_CONTROL_FAULT_POINTS:
        return _case_result(
            "A_FAULT_POINT",
            CONTROL_FIXTURE_INVALID,
            "unknown absolute-path control fault point",
            CONTROL_FAULT_INJECTED,
            policy_identity=absolute_path_control_policy_identity(),
        )
    return _case_result(
        fault_point,
        CONTROL_FAULT_INJECTED,
        "synthetic absolute-path control fault point retained fail-closed result",
        CONTROL_FAULT_INJECTED,
        policy_identity=absolute_path_control_policy_identity(),
    )


def _absolute_fault_result_if_requested(
    fault_point: str | None,
    checkpoint: str,
) -> ValidationCaseResult | None:
    if fault_point is None:
        return None
    if fault_point not in ABSOLUTE_PATH_CONTROL_FAULT_POINTS:
        return derive_absolute_control_fault_point_result(fault_point)
    if fault_point == checkpoint:
        return derive_absolute_control_fault_point_result(fault_point)
    return None


def _absolute_control_fixture_status(detail: str) -> str:
    lowered = detail.lower()
    if "reparse" in lowered or "symlink" in lowered or "junction" in lowered:
        return CONTROL_REPARSE_REJECTED
    if "outside fixture root" in lowered or "escaped" in lowered:
        return CONTROL_CONTAINMENT_REJECTED
    if "same volume" in lowered:
        return CONTROL_SAME_VOLUME_REJECTED
    return CONTROL_FIXTURE_INVALID


def _absolute_control_support_status(profile: SupportProfile) -> str:
    if profile.failure_code == UNSUPPORTED_VOLUME_RELATIONSHIP:
        return CONTROL_SAME_VOLUME_REJECTED
    if profile.status == SKIPPED:
        return CONTROL_SKIPPED_FIXTURE_UNAVAILABLE
    return CONTROL_FIXTURE_INVALID


def _absolute_control_native_failure_status(error_code: int | None) -> str:
    if error_code == ERROR_INVALID_PARAMETER:
        return CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE
    if error_code == ERROR_NOT_SUPPORTED:
        return CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL
    if error_code == ERROR_ACCESS_DENIED:
        return CONTROL_ACCESS_REJECTED
    if error_code in COLLISION_ERROR_CODES:
        return CONTROL_COLLISION_OBSERVED
    return CONTROL_NATIVE_ERROR_INDETERMINATE


def _absolute_control_native_failure_detail(error_code: int | None) -> str:
    if error_code == ERROR_INVALID_PARAMETER:
        return (
            "absolute-path FileRenameInfo control returned ERROR_INVALID_PARAMETER; "
            "cause remains indeterminate"
        )
    if error_code == ERROR_NOT_SUPPORTED:
        return "absolute-path FileRenameInfo control returned ERROR_NOT_SUPPORTED"
    if error_code == ERROR_ACCESS_DENIED:
        return "absolute-path FileRenameInfo control was access-rejected"
    if error_code in COLLISION_ERROR_CODES:
        return "absolute-path FileRenameInfo control observed no-replace collision"
    return "absolute-path FileRenameInfo control returned an indeterminate native error"


def derive_absolute_control_success_status(
    *,
    source_identity_before: ObjectIdentity,
    retained_handle_identity_after: ObjectIdentity,
    final_identity_after: ObjectIdentity,
    manifest_before: ContentManifest,
    manifest_after: ContentManifest,
) -> str:
    if retained_handle_identity_after != source_identity_before:
        return CONTROL_IDENTITY_MISMATCH
    if final_identity_after != source_identity_before:
        return CONTROL_IDENTITY_MISMATCH
    if manifest_before.manifest_sha256 != manifest_after.manifest_sha256:
        return CONTROL_CONTENT_MISMATCH
    return CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE


def execute_absolute_path_control(
    *,
    fixture_root: str | Path,
    source_directory: str | Path,
    destination_parent: str | Path,
    final_name: str,
    mode: str,
    allow_existing_destination_for_negative: bool = False,
    fault_point: str | None = None,
) -> ValidationCaseResult:
    require_absolute_path_control_mode(mode)
    policy_identity = absolute_path_control_policy_identity()
    final_name_validation = validate_final_name(final_name)
    if not final_name_validation.accepted:
        return _case_result(
            "A_NATIVE_EXECUTION",
            CONTROL_FIXTURE_INVALID,
            final_name_validation.reason or "invalid final name",
            NAME_INVALID,
            policy_identity=policy_identity,
        )
    try:
        root = validate_fixture_root(fixture_root)
        source = validate_child_path(
            source_directory,
            fixture_root=root,
            must_exist=True,
        )
        dest_parent = validate_child_path(
            destination_parent,
            fixture_root=root,
            must_exist=True,
        )
        _validate_ordinary_directory(source)
        _validate_ordinary_directory(dest_parent)
        _ensure_existing_ancestors_non_reparse(source, root)
        _ensure_existing_ancestors_non_reparse(dest_parent, root)
        final_path, absolute_destination_text = derive_absolute_control_destination(
            fixture_root=root,
            destination_parent=dest_parent,
            final_name=final_name,
        )
    except FixtureInvalidError as exc:
        detail = str(exc)
        status = _absolute_control_fixture_status(detail)
        return _case_result(
            "A_NATIVE_EXECUTION",
            status,
            detail,
            status,
            policy_identity=policy_identity,
        )
    if final_path.exists() and not allow_existing_destination_for_negative:
        return _case_result(
            "A_NATIVE_EXECUTION",
            CONTROL_FIXTURE_INVALID,
            "destination already exists in positive profile",
            DESTINATION_ALREADY_EXISTS,
            policy_identity=policy_identity,
        )
    fault = _absolute_fault_result_if_requested(
        fault_point,
        "A_FAULT_AFTER_FIXTURE_ADMISSION",
    )
    if fault is not None:
        return fault
    support = admit_support_profile(
        fixture_root=root,
        source_directory=source,
        destination_parent=dest_parent,
    )
    if not support.supported:
        status = _absolute_control_support_status(support)
        return _case_result(
            "A_NATIVE_EXECUTION",
            status,
            support.detail,
            status,
            policy_identity=policy_identity,
            support_profile=support,
            skip_reason=support.failure_code
            if status == CONTROL_SKIPPED_FIXTURE_UNAVAILABLE
            else None,
        )
    fault = _absolute_fault_result_if_requested(
        fault_point,
        "A_FAULT_AFTER_ABSOLUTE_PATH_DERIVATION",
    )
    if fault is not None:
        return fault
    try:
        manifest_before = build_content_manifest(source)
        if manifest_before.entry_count == 0:
            return _case_result(
                "A_NATIVE_EXECUTION",
                CONTROL_FIXTURE_INVALID,
                "source directory is empty",
                SOURCE_EMPTY,
                policy_identity=policy_identity,
                support_profile=support,
            )
        source_parent_before = identity_from_path(source.parent)
        dest_parent_before = identity_from_path(dest_parent)
        source_path_identity_before = identity_from_path(source)
    except FixtureInvalidError as exc:
        return _case_result(
            "A_NATIVE_EXECUTION",
            _absolute_control_fixture_status(str(exc)),
            str(exc),
            SOURCE_MANIFEST_BOUNDS_EXCEEDED,
            policy_identity=policy_identity,
            support_profile=support,
        )
    except OSError as exc:
        error_code = getattr(exc, "winerror", None)
        return _case_result(
            "A_NATIVE_EXECUTION",
            _absolute_control_native_failure_status(error_code),
            "pre-operation identity capture failed",
            NATIVE_IDENTITY_FAILED,
            native_error_code=error_code,
            native_error_name=_error_name(error_code),
            policy_identity=policy_identity,
            support_profile=support,
        )

    source_handle = _open_directory_handle(source, desired_access=DELETE)
    if isinstance(source_handle, NativePromotionOutcome):
        status = _absolute_control_native_failure_status(source_handle.native_error_code)
        return _case_result(
            "A_NATIVE_EXECUTION",
            status,
            source_handle.detail,
            NATIVE_OPEN_FAILED,
            native_error_code=source_handle.native_error_code,
            native_error_name=source_handle.native_error_name,
            policy_identity=policy_identity,
            support_profile=support,
        )
    fault = _absolute_fault_result_if_requested(
        fault_point,
        "A_FAULT_AFTER_SOURCE_HANDLE_OPEN",
    )
    if fault is not None:
        source_handle.close()
        return fault

    dest_access = (
        FILE_LIST_DIRECTORY | FILE_ADD_FILE | FILE_ADD_SUBDIRECTORY | FILE_READ_ATTRIBUTES
    )
    dest_parent_handle = _open_directory_handle(dest_parent, desired_access=dest_access)
    if isinstance(dest_parent_handle, NativePromotionOutcome):
        source_handle.close()
        status = _absolute_control_native_failure_status(
            dest_parent_handle.native_error_code
        )
        return _case_result(
            "A_NATIVE_EXECUTION",
            status,
            dest_parent_handle.detail,
            NATIVE_OPEN_FAILED,
            native_error_code=dest_parent_handle.native_error_code,
            native_error_name=dest_parent_handle.native_error_name,
            policy_identity=policy_identity,
            support_profile=support,
        )

    with source_handle, dest_parent_handle:
        fault = _absolute_fault_result_if_requested(
            fault_point,
            "A_FAULT_AFTER_DESTINATION_PARENT_EVIDENCE",
        )
        if fault is not None:
            return fault
        try:
            retained_before = identity_from_handle(source_handle.handle)
            if retained_before != source_path_identity_before:
                return _case_result(
                    "A_NATIVE_EXECUTION",
                    CONTROL_IDENTITY_MISMATCH,
                    "retained source handle does not match source path before rename",
                    NATIVE_IDENTITY_FAILED,
                    policy_identity=policy_identity,
                    support_profile=support,
                    source_identity_before=source_path_identity_before,
                )
            rename_buffer = build_absolute_path_file_rename_info_buffer(
                absolute_destination_path=absolute_destination_text,
            )
        except (ValidationError, OSError) as exc:
            return _case_result(
                "A_NATIVE_EXECUTION",
                CONTROL_NATIVE_ERROR_INDETERMINATE,
                "absolute-path buffer or retained identity capture failed: %s"
                % type(exc).__name__,
                NATIVE_IDENTITY_FAILED,
                policy_identity=policy_identity,
                support_profile=support,
                source_identity_before=source_path_identity_before,
            )
        fault = _absolute_fault_result_if_requested(
            fault_point,
            "A_FAULT_AFTER_BUFFER_CONSTRUCTION",
        )
        if fault is not None:
            return fault
        fault = _absolute_fault_result_if_requested(
            fault_point,
            "A_FAULT_BEFORE_NATIVE_CALL",
        )
        if fault is not None:
            return fault
        kernel32 = _kernel32()
        ok = bool(
            kernel32.SetFileInformationByHandle(
                source_handle.handle,
                FileRenameInfo,
                ctypes.cast(rename_buffer.buffer, ctypes.c_void_p),
                rename_buffer.size,
            )
        )
        if not ok:
            error_code = int(kernel32.GetLastError())
            status = _absolute_control_native_failure_status(error_code)
            manifest_after_sha256 = None
            if source.exists():
                try:
                    manifest_after_sha256 = build_content_manifest(source).manifest_sha256
                except FixtureInvalidError:
                    manifest_after_sha256 = None
            return _case_result(
                "A_NATIVE_EXECUTION",
                status,
                _absolute_control_native_failure_detail(error_code),
                NATIVE_RENAME_FAILED,
                native_error_code=error_code,
                native_error_name=_error_name(error_code),
                policy_identity=policy_identity,
                support_profile=support,
                source_identity_before=source_path_identity_before,
                source_parent_identity_before=source_parent_before,
                destination_parent_identity_before=dest_parent_before,
                source_exists_after_native_failure=source.exists(),
                final_exists_after_native_failure=final_path.exists(),
                manifest_before_sha256=manifest_before.manifest_sha256,
                manifest_after_sha256=manifest_after_sha256,
            )
        fault = _absolute_fault_result_if_requested(
            fault_point,
            "A_FAULT_AFTER_NATIVE_SUCCESS",
        )
        if fault is not None:
            return fault
        fault = _absolute_fault_result_if_requested(
            fault_point,
            "A_FAULT_BEFORE_POST_TRANSITION_VERIFICATION",
        )
        if fault is not None:
            return fault
        try:
            retained_after = identity_from_handle(source_handle.handle)
            final_identity_after = identity_from_path(final_path)
            source_parent_after = identity_from_path(source.parent)
            dest_parent_after = identity_from_path(dest_parent)
            manifest_after = build_content_manifest(final_path)
        except (FixtureInvalidError, OSError) as exc:
            return _case_result(
                "A_NATIVE_EXECUTION",
                CONTROL_NATIVE_ERROR_INDETERMINATE,
                "post-operation validation failed: %s" % type(exc).__name__,
                NATIVE_IDENTITY_FAILED,
                policy_identity=policy_identity,
                support_profile=support,
                source_identity_before=source_path_identity_before,
                manifest_before_sha256=manifest_before.manifest_sha256,
            )

    status = derive_absolute_control_success_status(
        source_identity_before=source_path_identity_before,
        retained_handle_identity_after=retained_after,
        final_identity_after=final_identity_after,
        manifest_before=manifest_before,
        manifest_after=manifest_after,
    )
    failure_code = (
        None
        if status == CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE
        else status
    )
    return _case_result(
        "A_NATIVE_EXECUTION",
        status,
        "absolute-path FileRenameInfo diagnostic control completed",
        failure_code,
        policy_identity=policy_identity,
        support_profile=support,
        source_identity_before=source_path_identity_before,
        retained_handle_identity_after=retained_after,
        final_identity_after=final_identity_after,
        source_parent_identity_before=source_parent_before,
        source_parent_identity_after=source_parent_after,
        destination_parent_identity_before=dest_parent_before,
        destination_parent_identity_after=dest_parent_after,
        manifest_before_sha256=manifest_before.manifest_sha256,
        manifest_after_sha256=manifest_after.manifest_sha256,
    )


def execute_no_replace_promotion(
    *,
    fixture_root: str | Path,
    source_directory: str | Path,
    destination_parent: str | Path,
    final_name: str,
    allow_existing_destination_for_negative: bool = False,
) -> ValidationCaseResult:
    policy_identity = validation_policy_identity()
    final_name_validation = validate_final_name(final_name)
    if not final_name_validation.accepted:
        return _case_result(
            "NATIVE_EXECUTION",
            FIXTURE_INVALID,
            final_name_validation.reason or "invalid final name",
            NAME_INVALID,
            policy_identity=policy_identity,
        )
    try:
        root = validate_fixture_root(fixture_root)
        source = validate_child_path(
            source_directory,
            fixture_root=root,
            must_exist=True,
        )
        dest_parent = validate_child_path(
            destination_parent,
            fixture_root=root,
            must_exist=True,
        )
        _validate_ordinary_directory(source)
        _validate_ordinary_directory(dest_parent)
        final_path = validate_child_path(
            dest_parent / final_name,
            fixture_root=root,
            must_exist=False,
        )
    except FixtureInvalidError as exc:
        return _case_result(
            "NATIVE_EXECUTION",
            FIXTURE_INVALID,
            str(exc),
            FIXTURE_ROOT_INVALID,
            policy_identity=policy_identity,
        )
    if final_path.exists() and not allow_existing_destination_for_negative:
        return _case_result(
            "NATIVE_EXECUTION",
            FIXTURE_INVALID,
            "destination already exists in positive profile",
            DESTINATION_ALREADY_EXISTS,
            policy_identity=policy_identity,
        )
    support = admit_support_profile(
        fixture_root=root,
        source_directory=source,
        destination_parent=dest_parent,
    )
    if not support.supported:
        return _case_result(
            "NATIVE_EXECUTION",
            support.status,
            support.detail,
            support.failure_code,
            policy_identity=policy_identity,
            support_profile=support,
            skip_reason=support.failure_code
            if support.status in (SKIPPED, UNSUPPORTED)
            else None,
        )
    try:
        manifest_before = build_content_manifest(source)
        if manifest_before.entry_count == 0:
            return _case_result(
                "NATIVE_EXECUTION",
                FIXTURE_INVALID,
                "source directory is empty",
                SOURCE_EMPTY,
                policy_identity=policy_identity,
                support_profile=support,
            )
        source_parent_before = identity_from_path(source.parent)
        dest_parent_before = identity_from_path(dest_parent)
        source_path_identity_before = identity_from_path(source)
    except FixtureInvalidError as exc:
        return _case_result(
            "NATIVE_EXECUTION",
            FIXTURE_INVALID,
            str(exc),
            SOURCE_MANIFEST_BOUNDS_EXCEEDED,
            policy_identity=policy_identity,
            support_profile=support,
        )
    except OSError as exc:
        return _case_result(
            "NATIVE_EXECUTION",
            INDETERMINATE,
            "pre-operation identity capture failed",
            NATIVE_IDENTITY_FAILED,
            native_error_code=getattr(exc, "winerror", None),
            native_error_name=_error_name(getattr(exc, "winerror", None)),
            policy_identity=policy_identity,
            support_profile=support,
        )

    source_handle = _open_directory_handle(source, desired_access=DELETE)
    if isinstance(source_handle, NativePromotionOutcome):
        return _case_result(
            "NATIVE_EXECUTION",
            FAILED,
            source_handle.detail,
            NATIVE_OPEN_FAILED,
            native_error_code=source_handle.native_error_code,
            native_error_name=source_handle.native_error_name,
            policy_identity=policy_identity,
            support_profile=support,
        )
    dest_access = (
        FILE_LIST_DIRECTORY | FILE_ADD_FILE | FILE_ADD_SUBDIRECTORY | FILE_READ_ATTRIBUTES
    )
    dest_parent_handle = _open_directory_handle(dest_parent, desired_access=dest_access)
    if isinstance(dest_parent_handle, NativePromotionOutcome):
        source_handle.close()
        return _case_result(
            "NATIVE_EXECUTION",
            FAILED,
            dest_parent_handle.detail,
            NATIVE_OPEN_FAILED,
            native_error_code=dest_parent_handle.native_error_code,
            native_error_name=dest_parent_handle.native_error_name,
            policy_identity=policy_identity,
            support_profile=support,
        )

    with source_handle, dest_parent_handle:
        try:
            retained_before = identity_from_handle(source_handle.handle)
            if retained_before != source_path_identity_before:
                return _case_result(
                    "NATIVE_EXECUTION",
                    IDENTITY_MISMATCH,
                    "retained source handle does not match source path before rename",
                    NATIVE_IDENTITY_FAILED,
                    policy_identity=policy_identity,
                    support_profile=support,
                    source_identity_before=source_path_identity_before,
                )
            rename_buffer = build_file_rename_info_buffer(
                root_directory_handle=dest_parent_handle.handle,
                final_name=final_name,
            )
        except (ValidationError, OSError) as exc:
            return _case_result(
                "NATIVE_EXECUTION",
                INDETERMINATE,
                "rename buffer or retained identity capture failed: %s"
                % type(exc).__name__,
                NATIVE_IDENTITY_FAILED,
                policy_identity=policy_identity,
                support_profile=support,
                source_identity_before=source_path_identity_before,
            )
        kernel32 = _kernel32()
        ok = bool(
            kernel32.SetFileInformationByHandle(
                source_handle.handle,
                FileRenameInfo,
                ctypes.cast(rename_buffer.buffer, ctypes.c_void_p),
                rename_buffer.size,
            )
        )
        if not ok:
            error_code = int(kernel32.GetLastError())
            status = _native_rename_failure_status(error_code)
            manifest_after_sha256 = None
            if source.exists():
                try:
                    manifest_after_sha256 = build_content_manifest(source).manifest_sha256
                except FixtureInvalidError:
                    manifest_after_sha256 = None
            return _case_result(
                "NATIVE_EXECUTION",
                status,
                _native_rename_failure_detail(error_code),
                NATIVE_RENAME_FAILED,
                native_error_code=error_code,
                native_error_name=_error_name(error_code),
                policy_identity=policy_identity,
                support_profile=support,
                source_identity_before=source_path_identity_before,
                source_parent_identity_before=source_parent_before,
                destination_parent_identity_before=dest_parent_before,
                source_exists_after_native_failure=source.exists(),
                final_exists_after_native_failure=final_path.exists(),
                manifest_before_sha256=manifest_before.manifest_sha256,
                manifest_after_sha256=manifest_after_sha256,
            )
        try:
            retained_after = identity_from_handle(source_handle.handle)
            final_identity_after = identity_from_path(final_path)
            source_parent_after = identity_from_path(source.parent)
            dest_parent_after = identity_from_path(dest_parent)
            manifest_after = build_content_manifest(final_path)
        except (FixtureInvalidError, OSError) as exc:
            return _case_result(
                "NATIVE_EXECUTION",
                INDETERMINATE,
                "post-operation validation failed: %s" % type(exc).__name__,
                NATIVE_IDENTITY_FAILED,
                policy_identity=policy_identity,
                support_profile=support,
                source_identity_before=source_path_identity_before,
                manifest_before_sha256=manifest_before.manifest_sha256,
            )
        durability = investigate_directory_durability(
            final_parent=dest_parent,
            former_source_parent=source.parent,
            retained_directory_handle=source_handle.handle,
        )

    status = derive_success_status(
        source_identity_before=source_path_identity_before,
        retained_handle_identity_after=retained_after,
        final_identity_after=final_identity_after,
        manifest_before=manifest_before,
        manifest_after=manifest_after,
        durability_probes=durability,
    )
    failure_code = None if status == PRIMITIVE_VALIDATION_CONFIRMED else status
    return _case_result(
        "NATIVE_EXECUTION",
        status,
        "native no-replace same-volume directory promotion validation completed",
        failure_code,
        policy_identity=policy_identity,
        support_profile=support,
        source_identity_before=source_path_identity_before,
        retained_handle_identity_after=retained_after,
        final_identity_after=final_identity_after,
        source_parent_identity_before=source_parent_before,
        source_parent_identity_after=source_parent_after,
        destination_parent_identity_before=dest_parent_before,
        destination_parent_identity_after=dest_parent_after,
        manifest_before_sha256=manifest_before.manifest_sha256,
        manifest_after_sha256=manifest_after.manifest_sha256,
        durability_probes=durability,
    )


def derive_success_status(
    *,
    source_identity_before: ObjectIdentity,
    retained_handle_identity_after: ObjectIdentity,
    final_identity_after: ObjectIdentity,
    manifest_before: ContentManifest,
    manifest_after: ContentManifest,
    durability_probes: tuple[DurabilityProbe, ...],
) -> str:
    if retained_handle_identity_after != source_identity_before:
        return IDENTITY_MISMATCH
    if final_identity_after != source_identity_before:
        if final_identity_after.volume_serial_number != source_identity_before.volume_serial_number:
            return CROSS_VOLUME_COPY_DETECTED
        return IDENTITY_MISMATCH
    if manifest_before.manifest_sha256 != manifest_after.manifest_sha256:
        return CONTENT_MISMATCH
    if not required_durability_confirmed(durability_probes):
        return DURABILITY_UNCONFIRMED
    return PRIMITIVE_VALIDATION_CONFIRMED


def required_durability_confirmed(probes: tuple[DurabilityProbe, ...]) -> bool:
    required_ids = {
        "D1_FINAL_PARENT",
        "D2_FORMER_SOURCE_PARENT",
        "D3_FINAL_THEN_FORMER_PARENT_ORDER",
        "D3_FORMER_THEN_FINAL_PARENT_ORDER",
    }
    by_id = {probe.probe_id: probe for probe in probes}
    return all(
        by_id.get(probe_id) is not None
        and by_id[probe_id].status == durable_schema.DIRECTORY_DURABILITY_CONFIRMED
        for probe_id in required_ids
    )


def characterize_failed_collision(
    *,
    case_id: str,
    execution: ValidationCaseResult,
    source_directory: str | Path,
    destination_path: str | Path,
    destination_before: ObjectIdentity | None,
    destination_manifest_before: ContentManifest | None,
) -> ValidationCaseResult:
    policy_identity = validation_policy_identity()
    if _native_contract_rejection_gated(execution):
        return _case_result(
            case_id,
            execution.status,
            (
                "no-replace collision characterization was not reached after "
                "native contract rejection; cause remains unresolved among "
                "user-mode RootDirectory-relative contract rejection, "
                "destination-parent access/setup requirement, or another valid "
                "native parameter constraint"
            ),
            execution.failure_code,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=policy_identity,
            support_profile=execution.support_profile,
            source_identity_before=execution.source_identity_before,
            source_parent_identity_before=execution.source_parent_identity_before,
            destination_parent_identity_before=(
                execution.destination_parent_identity_before
            ),
            source_exists_after_native_failure=(
                execution.source_exists_after_native_failure
            ),
            final_exists_after_native_failure=(
                execution.final_exists_after_native_failure
            ),
            manifest_before_sha256=execution.manifest_before_sha256,
            manifest_after_sha256=execution.manifest_after_sha256,
        )
    if execution.status not in (FAILED, INDETERMINATE):
        return _case_result(
            case_id,
            DESTINATION_REPLACED,
            "native call unexpectedly succeeded against an existing destination",
            DESTINATION_REPLACED,
            policy_identity=policy_identity,
        )
    if execution.native_error_code not in COLLISION_ERROR_CODES:
        return _case_result(
            case_id,
            FAILED,
            "native failure was not characterized as a no-replace collision",
            NATIVE_RENAME_FAILED,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=policy_identity,
        )
    try:
        source_manifest_after = build_content_manifest(source_directory)
        if destination_before is not None:
            destination_after = identity_from_path(destination_path)
            if destination_after != destination_before:
                return _case_result(
                    case_id,
                    DESTINATION_REPLACED,
                    "destination identity changed after no-replace failure",
                    DESTINATION_REPLACED,
                    native_error_code=execution.native_error_code,
                    native_error_name=execution.native_error_name,
                    policy_identity=policy_identity,
                )
        if destination_manifest_before is not None:
            destination_manifest_after = build_content_manifest(destination_path)
            if (
                destination_manifest_after.manifest_sha256
                != destination_manifest_before.manifest_sha256
            ):
                return _case_result(
                    case_id,
                    DESTINATION_REPLACED,
                    "destination content changed after no-replace failure",
                    DESTINATION_REPLACED,
                    native_error_code=execution.native_error_code,
                    native_error_name=execution.native_error_name,
                    policy_identity=policy_identity,
                )
    except (FixtureInvalidError, OSError) as exc:
        return _case_result(
            case_id,
            INDETERMINATE,
            "collision characterization became indeterminate: %s"
            % type(exc).__name__,
            NATIVE_IDENTITY_FAILED,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=policy_identity,
        )
    return _case_result(
        case_id,
        PRIMITIVE_VALIDATION_CONFIRMED,
        "no-replace collision preserved source and destination",
        None,
        native_error_code=execution.native_error_code,
        native_error_name=execution.native_error_name,
        policy_identity=policy_identity,
        manifest_after_sha256=source_manifest_after.manifest_sha256,
    )


def _absolute_control_contract_rejection_gated(
    result: ValidationCaseResult,
) -> bool:
    if (
        result.status == CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE
        and result.native_error_code == ERROR_INVALID_PARAMETER
    ):
        return True
    return (
        result.status == CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL
        and result.native_error_code == ERROR_NOT_SUPPORTED
    )


def characterize_absolute_control_failed_collision(
    *,
    case_id: str,
    execution: ValidationCaseResult,
    source_directory: str | Path,
    destination_path: str | Path,
    destination_before: ObjectIdentity | None,
    destination_manifest_before: ContentManifest | None,
) -> ValidationCaseResult:
    policy_identity = absolute_path_control_policy_identity()
    if _absolute_control_contract_rejection_gated(execution):
        return _case_result(
            case_id,
            execution.status,
            (
                "absolute-path no-replace collision characterization was not "
                "reached after native control rejection"
            ),
            execution.failure_code,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=policy_identity,
            support_profile=execution.support_profile,
            source_identity_before=execution.source_identity_before,
            source_parent_identity_before=execution.source_parent_identity_before,
            destination_parent_identity_before=(
                execution.destination_parent_identity_before
            ),
            source_exists_after_native_failure=(
                execution.source_exists_after_native_failure
            ),
            final_exists_after_native_failure=(
                execution.final_exists_after_native_failure
            ),
            manifest_before_sha256=execution.manifest_before_sha256,
            manifest_after_sha256=execution.manifest_after_sha256,
        )
    if execution.native_error_code is None and execution.status in (
        CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE,
        CONTROL_IDENTITY_MISMATCH,
        CONTROL_CONTENT_MISMATCH,
    ):
        try:
            destination_preserved = True
            if destination_before is not None:
                destination_preserved = (
                    identity_from_path(destination_path) == destination_before
                )
            if destination_manifest_before is not None:
                destination_preserved = destination_preserved and (
                    build_content_manifest(destination_path).manifest_sha256
                    == destination_manifest_before.manifest_sha256
                )
        except (FixtureInvalidError, OSError):
            destination_preserved = False
        if destination_preserved and execution.status in (
            CONTROL_IDENTITY_MISMATCH,
            CONTROL_CONTENT_MISMATCH,
        ):
            return _case_result(
                case_id,
                execution.status,
                (
                    "absolute-path control completed without a native failure "
                    "but did not confirm the requested existing destination identity"
                ),
                execution.failure_code or execution.status,
                policy_identity=policy_identity,
                support_profile=execution.support_profile,
                source_identity_before=execution.source_identity_before,
                retained_handle_identity_after=(
                    execution.retained_handle_identity_after
                ),
                final_identity_after=execution.final_identity_after,
                source_parent_identity_before=execution.source_parent_identity_before,
                source_parent_identity_after=execution.source_parent_identity_after,
                destination_parent_identity_before=(
                    execution.destination_parent_identity_before
                ),
                destination_parent_identity_after=(
                    execution.destination_parent_identity_after
                ),
                manifest_before_sha256=execution.manifest_before_sha256,
                manifest_after_sha256=execution.manifest_after_sha256,
            )
        return _case_result(
            case_id,
            CONTROL_DESTINATION_REPLACED,
            "absolute-path control completed against an existing destination",
            CONTROL_DESTINATION_REPLACED,
            policy_identity=policy_identity,
        )
    if execution.status not in (
        CONTROL_COLLISION_OBSERVED,
        CONTROL_NATIVE_ERROR_INDETERMINATE,
        CONTROL_ACCESS_REJECTED,
    ):
        return _case_result(
            case_id,
            CONTROL_DESTINATION_REPLACED,
            "absolute-path control unexpectedly succeeded against an existing destination",
            CONTROL_DESTINATION_REPLACED,
            policy_identity=policy_identity,
        )
    if execution.native_error_code not in COLLISION_ERROR_CODES:
        return _case_result(
            case_id,
            execution.status,
            "native failure was not characterized as a no-replace collision",
            NATIVE_RENAME_FAILED,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=policy_identity,
        )
    try:
        source_manifest_after = build_content_manifest(source_directory)
        if destination_before is not None:
            destination_after = identity_from_path(destination_path)
            if destination_after != destination_before:
                return _case_result(
                    case_id,
                    CONTROL_DESTINATION_REPLACED,
                    "destination identity changed after no-replace failure",
                    CONTROL_DESTINATION_REPLACED,
                    native_error_code=execution.native_error_code,
                    native_error_name=execution.native_error_name,
                    policy_identity=policy_identity,
                )
        if destination_manifest_before is not None:
            destination_manifest_after = build_content_manifest(destination_path)
            if (
                destination_manifest_after.manifest_sha256
                != destination_manifest_before.manifest_sha256
            ):
                return _case_result(
                    case_id,
                    CONTROL_DESTINATION_REPLACED,
                    "destination content changed after no-replace failure",
                    CONTROL_DESTINATION_REPLACED,
                    native_error_code=execution.native_error_code,
                    native_error_name=execution.native_error_name,
                    policy_identity=policy_identity,
                )
    except (FixtureInvalidError, OSError) as exc:
        return _case_result(
            case_id,
            CONTROL_NATIVE_ERROR_INDETERMINATE,
            "collision characterization became indeterminate: %s"
            % type(exc).__name__,
            NATIVE_IDENTITY_FAILED,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=policy_identity,
        )
    return _case_result(
        case_id,
        CONTROL_COLLISION_OBSERVED,
        "absolute-path no-replace collision preserved source and destination",
        None,
        native_error_code=execution.native_error_code,
        native_error_name=execution.native_error_name,
        policy_identity=policy_identity,
        source_exists_after_native_failure=True,
        final_exists_after_native_failure=Path(destination_path).exists(),
        manifest_before_sha256=execution.manifest_before_sha256,
        manifest_after_sha256=source_manifest_after.manifest_sha256,
    )


def derive_fault_point_result(fault_point: str) -> ValidationCaseResult:
    if fault_point not in FAULT_POINTS:
        return _case_result(
            "FAULT_POINT",
            FIXTURE_INVALID,
            "unknown fault point",
            FAULT_INJECTED,
            policy_identity=validation_policy_identity(),
        )
    return _case_result(
        fault_point,
        INDETERMINATE,
        "synthetic in-process fault point retained fail-closed result",
        FAULT_INJECTED,
        policy_identity=validation_policy_identity(),
    )


def investigate_directory_durability(
    *,
    final_parent: str | Path,
    former_source_parent: str | Path,
    retained_directory_handle: int,
) -> tuple[DurabilityProbe, ...]:
    probes = [
        _adapter_directory_probe(
            "D1_FINAL_PARENT",
            final_parent,
            durable_schema.FINAL_PARENT_DIRECTORY,
        ),
        _adapter_directory_probe(
            "D2_FORMER_SOURCE_PARENT",
            former_source_parent,
            durable_schema.STAGING_PARENT_DIRECTORY,
        ),
    ]
    probes.append(
        _ordered_parent_probe(
            "D3_FINAL_THEN_FORMER_PARENT_ORDER",
            (final_parent, former_source_parent),
        )
    )
    probes.append(
        _ordered_parent_probe(
            "D3_FORMER_THEN_FINAL_PARENT_ORDER",
            (former_source_parent, final_parent),
        )
    )
    probes.append(_retained_handle_flush_probe(retained_directory_handle))
    return tuple(probes)


def _adapter_directory_probe(
    probe_id: str,
    path: str | Path,
    target_role: str,
) -> DurabilityProbe:
    context = durability_adapter.DirectoryDurabilityContext(target_role=target_role)
    result = durability_adapter.Win32DirectoryDurabilityAdapter().sync_directory_entry(
        str(path),
        context=context,
    )
    return DurabilityProbe(
        probe_id=probe_id,
        status=result.status,
        detail=result.detail,
        failure_code=result.failure_code,
        native_error_code=result.native_error_code,
        native_error_name=result.native_error_name,
        adapter_policy_identity=result.adapter_policy_identity,
    )


def _ordered_parent_probe(probe_id: str, paths: tuple[str | Path, str | Path]) -> DurabilityProbe:
    first = _adapter_directory_probe(
        probe_id + "_FIRST",
        paths[0],
        durable_schema.FINAL_PARENT_DIRECTORY,
    )
    second = _adapter_directory_probe(
        probe_id + "_SECOND",
        paths[1],
        durable_schema.STAGING_PARENT_DIRECTORY,
    )
    if (
        first.status == durable_schema.DIRECTORY_DURABILITY_CONFIRMED
        and second.status == durable_schema.DIRECTORY_DURABILITY_CONFIRMED
    ):
        status = durable_schema.DIRECTORY_DURABILITY_CONFIRMED
        detail = "ordered parent durability probes confirmed"
        failure_code = None
    else:
        status = DURABILITY_UNCONFIRMED
        detail = "ordered parent durability probes were not fully confirmed"
        failure_code = NATIVE_DURABILITY_FAILED
    return DurabilityProbe(
        probe_id=probe_id,
        status=status,
        detail=detail,
        failure_code=failure_code,
        native_error_code=first.native_error_code or second.native_error_code,
        native_error_name=first.native_error_name or second.native_error_name,
        adapter_policy_identity=durable_schema.directory_durability_policy_identity(),
    )


def _retained_handle_flush_probe(retained_directory_handle: int) -> DurabilityProbe:
    try:
        kernel32 = _kernel32()
        ok = bool(kernel32.FlushFileBuffers(retained_directory_handle))
        if ok:
            return DurabilityProbe(
                probe_id="D4_RETAINED_RENAMED_DIRECTORY_HANDLE_FLUSH",
                status=durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
                detail="retained renamed directory handle flush confirmed",
                adapter_policy_identity=durable_schema.directory_durability_policy_identity(),
            )
        error_code = int(kernel32.GetLastError())
        return DurabilityProbe(
            probe_id="D4_RETAINED_RENAMED_DIRECTORY_HANDLE_FLUSH",
            status=DURABILITY_UNCONFIRMED,
            detail="retained renamed directory handle flush was not confirmed",
            failure_code=NATIVE_DURABILITY_FAILED,
            native_error_code=error_code,
            native_error_name=_error_name(error_code),
            adapter_policy_identity=durable_schema.directory_durability_policy_identity(),
        )
    except UnsupportedProfileError:
        return DurabilityProbe(
            probe_id="D4_RETAINED_RENAMED_DIRECTORY_HANDLE_FLUSH",
            status=SKIPPED,
            detail="retained handle flush skipped outside Windows",
            failure_code=UNSUPPORTED_PLATFORM,
            adapter_policy_identity=durable_schema.directory_durability_policy_identity(),
        )


def make_bounded_source_tree(root: str | Path, name: str = "source") -> Path:
    source = Path(root) / name
    source.mkdir(parents=True, exist_ok=False)
    (source / "alpha.txt").write_bytes(b"alpha\n")
    nested = source / "nested"
    nested.mkdir()
    (nested / "beta.bin").write_bytes(b"beta\n")
    return source


def validate_v1_full_chain_positive(fixture_root: str | Path) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v1"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    result = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
    )
    return _replace_case_id(result, "V1_FULL_CHAIN_POSITIVE")


def validate_v2_existing_destination_directory(
    fixture_root: str | Path,
) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v2"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    destination = make_bounded_source_tree(destination_parent, "final")
    destination_before = identity_from_path(destination) if _is_windows() else None
    destination_manifest_before = build_content_manifest(destination)
    execution = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        allow_existing_destination_for_negative=True,
    )
    return characterize_failed_collision(
        case_id="V2_EXISTING_DESTINATION_DIRECTORY",
        execution=execution,
        source_directory=source,
        destination_path=destination,
        destination_before=destination_before,
        destination_manifest_before=destination_manifest_before,
    )


def validate_v3_existing_destination_file(fixture_root: str | Path) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v3"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    destination = destination_parent / "final"
    destination.write_bytes(b"existing file\n")
    execution = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        allow_existing_destination_for_negative=True,
    )
    if _native_contract_rejection_gated(execution):
        return _replace_case_id(execution, "V3_EXISTING_DESTINATION_FILE")
    if execution.status not in (FAILED, INDETERMINATE):
        return _case_result(
            "V3_EXISTING_DESTINATION_FILE",
            DESTINATION_REPLACED,
            "native call unexpectedly succeeded over an existing file",
            DESTINATION_REPLACED,
            policy_identity=validation_policy_identity(),
        )
    if not destination.is_file() or destination.read_bytes() != b"existing file\n":
        return _case_result(
            "V3_EXISTING_DESTINATION_FILE",
            DESTINATION_REPLACED,
            "existing file destination changed",
            DESTINATION_REPLACED,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=validation_policy_identity(),
        )
    if execution.native_error_code not in COLLISION_ERROR_CODES:
        return _case_result(
            "V3_EXISTING_DESTINATION_FILE",
            FAILED,
            "native failure was not characterized as a no-replace file collision",
            NATIVE_RENAME_FAILED,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=validation_policy_identity(),
        )
    return _case_result(
        "V3_EXISTING_DESTINATION_FILE",
        PRIMITIVE_VALIDATION_CONFIRMED,
        "no-replace collision preserved existing file destination",
        None,
        native_error_code=execution.native_error_code,
        native_error_name=execution.native_error_name,
        policy_identity=validation_policy_identity(),
    )


def validate_v4_coordinated_destination_claim(
    fixture_root: str | Path,
) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v4"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    final_path = destination_parent / "final"
    ready = threading.Event()
    done = threading.Event()
    error: list[BaseException] = []

    def claim_destination() -> None:
        ready.wait(timeout=5)
        try:
            final_path.mkdir()
            (final_path / "owner.txt").write_bytes(b"competitor\n")
        except BaseException as exc:  # pragma: no cover - defensive capture
            error.append(exc)
        finally:
            done.set()

    thread = threading.Thread(target=claim_destination)
    thread.start()
    ready.set()
    done.wait(timeout=5)
    thread.join(timeout=5)
    if error:
        return _case_result(
            "V4_COORDINATED_DESTINATION_CLAIM",
            INDETERMINATE,
            "coordinated destination claim failed",
            FAULT_INJECTED,
            policy_identity=validation_policy_identity(),
        )
    destination_before = identity_from_path(final_path) if _is_windows() else None
    destination_manifest_before = build_content_manifest(final_path)
    execution = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        allow_existing_destination_for_negative=True,
    )
    return characterize_failed_collision(
        case_id="V4_COORDINATED_DESTINATION_CLAIM",
        execution=execution,
        source_directory=source,
        destination_path=final_path,
        destination_before=destination_before,
        destination_manifest_before=destination_manifest_before,
    )


def validate_v5_source_reparse_rejected(fixture_root: str | Path) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v5"
    case_root.mkdir()
    target = make_bounded_source_tree(case_root, "target")
    link = case_root / "source_link"
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        return _case_result(
            "V5_SOURCE_REPARSE_REJECTED",
            SKIPPED,
            "source reparse fixture could not be created",
            UNSUPPORTED_PLATFORM,
            skip_reason="SYMLINK_UNAVAILABLE",
            policy_identity=validation_policy_identity(),
        )
    result = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=link,
        destination_parent=destination_parent,
        final_name="final",
    )
    if result.status == FIXTURE_INVALID:
        return _replace_case_id(result, "V5_SOURCE_REPARSE_REJECTED")
    return _case_result(
        "V5_SOURCE_REPARSE_REJECTED",
        FAILED,
        "source reparse point was not rejected before native promotion",
        PATH_REPARSE_POINT,
        policy_identity=validation_policy_identity(),
    )


def validate_v6_destination_parent_reparse_rejected(
    fixture_root: str | Path,
) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v6"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    target = case_root / "dest_target"
    target.mkdir()
    link = case_root / "dest_link"
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        return _case_result(
            "V6_DESTINATION_PARENT_REPARSE_REJECTED",
            SKIPPED,
            "destination reparse fixture could not be created",
            UNSUPPORTED_PLATFORM,
            skip_reason="SYMLINK_UNAVAILABLE",
            policy_identity=validation_policy_identity(),
        )
    result = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=link,
        final_name="final",
    )
    if result.status == FIXTURE_INVALID:
        return _replace_case_id(result, "V6_DESTINATION_PARENT_REPARSE_REJECTED")
    return _case_result(
        "V6_DESTINATION_PARENT_REPARSE_REJECTED",
        FAILED,
        "destination parent reparse point was not rejected before native promotion",
        PATH_REPARSE_POINT,
        policy_identity=validation_policy_identity(),
    )


def validate_v7_mutation_content_mismatch(fixture_root: str | Path) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v7"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    before = build_content_manifest(source)
    (source / "alpha.txt").write_bytes(b"mutated\n")
    after = build_content_manifest(source)
    status = CONTENT_MISMATCH if before.manifest_sha256 != after.manifest_sha256 else FAILED
    return _case_result(
        "V7_MUTATION_CONTENT_MISMATCH",
        status,
        "synthetic metadata/content mutation was detected before confirmation",
        None if status == CONTENT_MISMATCH else SOURCE_MANIFEST_BOUNDS_EXCEEDED,
        policy_identity=validation_policy_identity(),
        manifest_before_sha256=before.manifest_sha256,
        manifest_after_sha256=after.manifest_sha256,
    )


def validate_v8_identity_continuity(fixture_root: str | Path) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v8"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    result = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
    )
    return _replace_case_id(result, "V8_IDENTITY_CONTINUITY")


def validate_v9_invalid_names() -> tuple[ValidationCaseResult, ...]:
    invalid_names = (
        "",
        ".",
        "..",
        "a/b",
        "a\\b",
        "C:drive",
        "stream:name",
        "*",
        "?",
        "\\\\server",
        "\\\\?\\C:\\x",
        "x\x00y",
    )
    return tuple(
        _case_result(
            "V9_INVALID_NAME_%02d" % index,
            FIXTURE_INVALID
            if not validate_final_name(name).accepted
            else FAILED,
            validate_final_name(name).reason or "invalid name was accepted",
            NAME_INVALID,
            policy_identity=validation_policy_identity(),
        )
        for index, name in enumerate(invalid_names)
    )


def validate_v10_unsupported_profile(fixture_root: str | Path) -> ValidationCaseResult:
    if not _is_windows():
        return _case_result(
            "V10_UNSUPPORTED_PROFILE",
            SKIPPED,
            "non-Windows platform is explicitly skipped",
            UNSUPPORTED_PLATFORM,
            skip_reason=UNSUPPORTED_PLATFORM,
            policy_identity=validation_policy_identity(),
        )
    source = Path(fixture_root) / "v10_missing_source"
    dest = Path(fixture_root) / "v10_dest"
    dest.mkdir()
    profile = admit_support_profile(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=dest,
    )
    return _case_result(
        "V10_UNSUPPORTED_PROFILE",
        profile.status,
        profile.detail,
        profile.failure_code,
        policy_identity=validation_policy_identity(),
        support_profile=profile,
    )


def validate_v11_cross_volume_optional(
    fixture_root: str | Path,
    second_volume_root: str | Path | None = None,
) -> ValidationCaseResult:
    if second_volume_root is None:
        return _case_result(
            "V11_CROSS_VOLUME_OPTIONAL",
            SKIPPED,
            "second local fixed NTFS fixture root was not injected",
            SECOND_VOLUME_UNAVAILABLE,
            skip_reason=SECOND_VOLUME_UNAVAILABLE,
            policy_identity=validation_policy_identity(),
        )
    case_root = Path(fixture_root) / "v11"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    dest_parent = Path(second_volume_root) / "v11_dest"
    dest_parent.mkdir()
    result = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=dest_parent,
        final_name="final",
    )
    return _replace_case_id(result, "V11_CROSS_VOLUME_OPTIONAL")


def validate_v12_native_error_retention(fixture_root: str | Path) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "v12"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    destination = make_bounded_source_tree(destination_parent, "final")
    execution = execute_no_replace_promotion(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        allow_existing_destination_for_negative=True,
    )
    if _native_contract_rejection_gated(execution):
        return _replace_case_id(execution, "V12_NATIVE_ERROR_RETENTION")
    if execution.native_error_code is None:
        return _case_result(
            "V12_NATIVE_ERROR_RETENTION",
            FAILED,
            "native error code was not retained",
            NATIVE_RENAME_FAILED,
            policy_identity=validation_policy_identity(),
        )
    preserved = destination.exists() and build_content_manifest(destination).entry_count > 0
    return _case_result(
        "V12_NATIVE_ERROR_RETENTION",
        PRIMITIVE_VALIDATION_CONFIRMED if preserved else DESTINATION_REPLACED,
        "native failure code and destination state were retained",
        None if preserved else DESTINATION_REPLACED,
        native_error_code=execution.native_error_code,
        native_error_name=execution.native_error_name,
        policy_identity=validation_policy_identity(),
    )


def validate_a1_absolute_path_positive(fixture_root: str | Path) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "a1"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    result = execute_absolute_path_control(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        mode=ABSOLUTE_PATH_CONTROL_MODE,
    )
    return _replace_case_id(result, "A1_POSITIVE_ABSOLUTE_PATH_RENAME")


def validate_a2_existing_destination_directory_absolute_path(
    fixture_root: str | Path,
) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "a2"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    destination = make_bounded_source_tree(destination_parent, "final")
    destination_before = identity_from_path(destination) if _is_windows() else None
    destination_manifest_before = build_content_manifest(destination)
    execution = execute_absolute_path_control(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        mode=ABSOLUTE_PATH_CONTROL_MODE,
        allow_existing_destination_for_negative=True,
    )
    return characterize_absolute_control_failed_collision(
        case_id="A2_EXISTING_DESTINATION_DIRECTORY",
        execution=execution,
        source_directory=source,
        destination_path=destination,
        destination_before=destination_before,
        destination_manifest_before=destination_manifest_before,
    )


def validate_a3_existing_destination_file_absolute_path(
    fixture_root: str | Path,
) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "a3"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    destination = destination_parent / "final"
    destination_before = b"existing file\n"
    destination.write_bytes(destination_before)
    execution = execute_absolute_path_control(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        mode=ABSOLUTE_PATH_CONTROL_MODE,
        allow_existing_destination_for_negative=True,
    )
    if _absolute_control_contract_rejection_gated(execution):
        return _replace_case_id(execution, "A3_EXISTING_DESTINATION_FILE")
    if execution.status not in (
        CONTROL_COLLISION_OBSERVED,
        CONTROL_NATIVE_ERROR_INDETERMINATE,
        CONTROL_ACCESS_REJECTED,
    ):
        return _case_result(
            "A3_EXISTING_DESTINATION_FILE",
            CONTROL_DESTINATION_REPLACED,
            "absolute-path control unexpectedly succeeded over an existing file",
            CONTROL_DESTINATION_REPLACED,
            policy_identity=absolute_path_control_policy_identity(),
        )
    if not destination.is_file() or destination.read_bytes() != destination_before:
        return _case_result(
            "A3_EXISTING_DESTINATION_FILE",
            CONTROL_DESTINATION_REPLACED,
            "existing file destination changed",
            CONTROL_DESTINATION_REPLACED,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=absolute_path_control_policy_identity(),
        )
    if execution.native_error_code not in COLLISION_ERROR_CODES:
        if execution.native_error_code is None and not source.exists():
            return _case_result(
                "A3_EXISTING_DESTINATION_FILE",
                CONTROL_IDENTITY_MISMATCH,
                (
                    "absolute-path control moved the source without replacing "
                    "the requested existing file destination"
                ),
                CONTROL_IDENTITY_MISMATCH,
                policy_identity=absolute_path_control_policy_identity(),
            )
        return _case_result(
            "A3_EXISTING_DESTINATION_FILE",
            execution.status,
            "native failure was not characterized as a no-replace file collision",
            NATIVE_RENAME_FAILED,
            native_error_code=execution.native_error_code,
            native_error_name=execution.native_error_name,
            policy_identity=absolute_path_control_policy_identity(),
        )
    return _case_result(
        "A3_EXISTING_DESTINATION_FILE",
        CONTROL_COLLISION_OBSERVED,
        "absolute-path no-replace collision preserved existing file destination",
        None,
        native_error_code=execution.native_error_code,
        native_error_name=execution.native_error_name,
        policy_identity=absolute_path_control_policy_identity(),
    )


def validate_a4_coordinated_destination_claim_absolute_path(
    fixture_root: str | Path,
) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "a4"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    final_path = destination_parent / "final"
    ready = threading.Event()
    done = threading.Event()
    error: list[BaseException] = []

    def claim_destination() -> None:
        ready.wait(timeout=5)
        try:
            final_path.mkdir()
            (final_path / "owner.txt").write_bytes(b"competitor\n")
        except BaseException as exc:  # pragma: no cover - defensive capture
            error.append(exc)
        finally:
            done.set()

    thread = threading.Thread(target=claim_destination)
    thread.start()
    ready.set()
    done.wait(timeout=5)
    thread.join(timeout=5)
    if error:
        return _case_result(
            "A4_COORDINATED_DESTINATION_CLAIM",
            CONTROL_NATIVE_ERROR_INDETERMINATE,
            "coordinated destination claim failed",
            CONTROL_FAULT_INJECTED,
            policy_identity=absolute_path_control_policy_identity(),
        )
    destination_before = identity_from_path(final_path) if _is_windows() else None
    destination_manifest_before = build_content_manifest(final_path)
    execution = execute_absolute_path_control(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        mode=ABSOLUTE_PATH_CONTROL_MODE,
        allow_existing_destination_for_negative=True,
    )
    return characterize_absolute_control_failed_collision(
        case_id="A4_COORDINATED_DESTINATION_CLAIM",
        execution=execution,
        source_directory=source,
        destination_path=final_path,
        destination_before=destination_before,
        destination_manifest_before=destination_manifest_before,
    )


def validate_a5_absolute_path_identity_continuity(
    fixture_root: str | Path,
) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "a5"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    result = execute_absolute_path_control(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        mode=ABSOLUTE_PATH_CONTROL_MODE,
    )
    return _replace_case_id(result, "A5_SOURCE_TO_FINAL_IDENTITY_CONTINUITY")


def validate_a6_absolute_path_native_error_characterization(
    fixture_root: str | Path,
) -> ValidationCaseResult:
    case_root = Path(fixture_root) / "a6"
    case_root.mkdir()
    source = make_bounded_source_tree(case_root)
    destination_parent = case_root / "dest"
    destination_parent.mkdir()
    destination = make_bounded_source_tree(destination_parent, "final")
    destination_manifest_before = build_content_manifest(destination)
    execution = execute_absolute_path_control(
        fixture_root=fixture_root,
        source_directory=source,
        destination_parent=destination_parent,
        final_name="final",
        mode=ABSOLUTE_PATH_CONTROL_MODE,
        allow_existing_destination_for_negative=True,
    )
    if execution.native_error_code is None:
        try:
            destination_manifest_after = build_content_manifest(destination)
            preserved = (
                destination_manifest_after.manifest_sha256
                == destination_manifest_before.manifest_sha256
            )
        except FixtureInvalidError:
            preserved = False
        status = (
            execution.status
            if preserved
            and execution.status
            in (
                CONTROL_IDENTITY_MISMATCH,
                CONTROL_CONTENT_MISMATCH,
                CONTROL_NATIVE_ERROR_INDETERMINATE,
            )
            else CONTROL_DESTINATION_REPLACED
        )
        failure_code = (
            execution.failure_code
            if preserved
            and execution.status
            in (
                CONTROL_IDENTITY_MISMATCH,
                CONTROL_CONTENT_MISMATCH,
                CONTROL_NATIVE_ERROR_INDETERMINATE,
            )
            else CONTROL_DESTINATION_REPLACED
        )
        detail = (
            (
                "absolute-path control completed without a native failure but "
                "did not confirm the requested existing destination identity"
            )
            if preserved
            and execution.status
            in (
                CONTROL_IDENTITY_MISMATCH,
                CONTROL_CONTENT_MISMATCH,
                CONTROL_NATIVE_ERROR_INDETERMINATE,
            )
            else "absolute-path control completed against an existing destination"
        )
        return _case_result(
            "A6_NATIVE_ERROR_CHARACTERIZATION",
            status,
            detail,
            failure_code,
            policy_identity=absolute_path_control_policy_identity(),
        )
    preserved = destination.exists() and build_content_manifest(destination).entry_count > 0
    status = execution.status if preserved else CONTROL_DESTINATION_REPLACED
    return _case_result(
        "A6_NATIVE_ERROR_CHARACTERIZATION",
        status,
        "absolute-path native failure code and destination state were retained",
        execution.failure_code if preserved else CONTROL_DESTINATION_REPLACED,
        native_error_code=execution.native_error_code,
        native_error_name=execution.native_error_name,
        policy_identity=absolute_path_control_policy_identity(),
    )


def validate_a7_invalid_or_escaping_absolute_destinations(
    fixture_root: str | Path,
) -> tuple[ValidationCaseResult, ...]:
    policy_identity = absolute_path_control_policy_identity()
    invalid_names = (
        "",
        ".",
        "..",
        "a/b",
        "a\\b",
        "C:drive",
        "stream:name",
        "*",
        "?",
        "\\\\server",
        "\\\\?\\C:\\x",
        "x\x00y",
    )
    results: list[ValidationCaseResult] = []
    for index, name in enumerate(invalid_names):
        validation = validate_final_name(name)
        accepted = validation.accepted
        results.append(
            _case_result(
                "A7_INVALID_OR_ESCAPING_ABSOLUTE_DESTINATION_REJECTED_%02d"
                % index,
                CONTROL_FIXTURE_INVALID
                if not accepted
                else CONTROL_NATIVE_ERROR_INDETERMINATE,
                validation.reason or "invalid destination was accepted",
                NAME_INVALID,
                policy_identity=policy_identity,
            )
        )

    case_root = Path(fixture_root) / "a7_escape"
    sibling = Path(str(case_root) + "_sibling")
    case_root.mkdir()
    sibling.mkdir()
    try:
        derive_absolute_control_destination(
            fixture_root=case_root,
            destination_parent=sibling,
            final_name="final",
        )
    except FixtureInvalidError as exc:
        status = _absolute_control_fixture_status(str(exc))
        results.append(
            _case_result(
                "A7_INVALID_OR_ESCAPING_ABSOLUTE_DESTINATION_REJECTED_ESCAPE",
                status,
                str(exc),
                status,
                policy_identity=policy_identity,
            )
        )
    else:
        results.append(
            _case_result(
                "A7_INVALID_OR_ESCAPING_ABSOLUTE_DESTINATION_REJECTED_ESCAPE",
                CONTROL_NATIVE_ERROR_INDETERMINATE,
                "sibling-prefix destination escape was accepted",
                PATH_OUTSIDE_FIXTURE_ROOT,
                policy_identity=policy_identity,
            )
        )
    return tuple(results)


def validate_a8_same_volume_mismatch_rejected(
    fixture_root: str | Path,
    second_volume_root: str | Path | None = None,
) -> ValidationCaseResult:
    policy_identity = absolute_path_control_policy_identity()
    if second_volume_root is None:
        return _case_result(
            "A8_SAME_VOLUME_MISMATCH_REJECTED",
            CONTROL_SKIPPED_FIXTURE_UNAVAILABLE,
            "second local fixed NTFS fixture root was not injected",
            SECOND_VOLUME_UNAVAILABLE,
            skip_reason=SECOND_VOLUME_UNAVAILABLE,
            policy_identity=policy_identity,
        )
    try:
        root = validate_fixture_root(fixture_root)
        second_root = validate_fixture_root(second_volume_root)
        case_root = root / "a8"
        case_root.mkdir()
        source = make_bounded_source_tree(case_root)
        destination_parent = second_root / "a8_dest"
        destination_parent.mkdir()
        source_drive_type, source_filesystem, source_volume = _volume_information(source)
        (
            destination_drive_type,
            destination_filesystem,
            destination_volume,
        ) = _volume_information(destination_parent)
    except FixtureInvalidError as exc:
        status = _absolute_control_fixture_status(str(exc))
        return _case_result(
            "A8_SAME_VOLUME_MISMATCH_REJECTED",
            status,
            str(exc),
            status,
            policy_identity=policy_identity,
        )
    except UnsupportedProfileError as exc:
        return _case_result(
            "A8_SAME_VOLUME_MISMATCH_REJECTED",
            CONTROL_SKIPPED_FIXTURE_UNAVAILABLE,
            str(exc),
            UNSUPPORTED_DRIVE_PROFILE,
            skip_reason=UNSUPPORTED_DRIVE_PROFILE,
            policy_identity=policy_identity,
        )
    except OSError as exc:
        error_code = getattr(exc, "winerror", None)
        return _case_result(
            "A8_SAME_VOLUME_MISMATCH_REJECTED",
            CONTROL_NATIVE_ERROR_INDETERMINATE,
            "volume evidence could not be determined",
            UNSUPPORTED_DRIVE_PROFILE,
            native_error_code=error_code,
            native_error_name=_error_name(error_code),
            policy_identity=policy_identity,
        )
    if source_volume != destination_volume:
        return _case_result(
            "A8_SAME_VOLUME_MISMATCH_REJECTED",
            CONTROL_SAME_VOLUME_REJECTED,
            "source and absolute destination parent are not on the same volume",
            UNSUPPORTED_VOLUME_RELATIONSHIP,
            policy_identity=policy_identity,
            support_profile=SupportProfile(
                supported=False,
                status=UNSUPPORTED,
                detail="source and destination are not on the same volume",
                failure_code=UNSUPPORTED_VOLUME_RELATIONSHIP,
                drive_type=source_drive_type,
                filesystem_name=source_filesystem,
                source_volume_serial_number=source_volume,
                destination_volume_serial_number=destination_volume,
            ),
        )
    if (
        source_drive_type != DRIVE_FIXED
        or destination_drive_type != DRIVE_FIXED
        or source_filesystem != "NTFS"
        or destination_filesystem != "NTFS"
    ):
        return _case_result(
            "A8_SAME_VOLUME_MISMATCH_REJECTED",
            CONTROL_SKIPPED_FIXTURE_UNAVAILABLE,
            "second volume fixture is not a local fixed NTFS profile",
            UNSUPPORTED_DRIVE_PROFILE,
            skip_reason=UNSUPPORTED_DRIVE_PROFILE,
            policy_identity=policy_identity,
        )
    return _case_result(
        "A8_SAME_VOLUME_MISMATCH_REJECTED",
        CONTROL_FIXTURE_INVALID,
        "second volume fixture resolved to the same volume",
        SECOND_VOLUME_UNAVAILABLE,
        policy_identity=policy_identity,
    )


def run_absolute_path_control_matrix(
    fixture_root: str | Path,
    *,
    mode: str,
    second_volume_root: str | Path | None = None,
) -> tuple[ValidationCaseResult, ...]:
    require_absolute_path_control_mode(mode)
    return (
        validate_a1_absolute_path_positive(fixture_root),
        validate_a2_existing_destination_directory_absolute_path(fixture_root),
        validate_a3_existing_destination_file_absolute_path(fixture_root),
        validate_a4_coordinated_destination_claim_absolute_path(fixture_root),
        validate_a5_absolute_path_identity_continuity(fixture_root),
        validate_a6_absolute_path_native_error_characterization(fixture_root),
        *validate_a7_invalid_or_escaping_absolute_destinations(fixture_root),
        validate_a8_same_volume_mismatch_rejected(
            fixture_root,
            second_volume_root=second_volume_root,
        ),
    )


def run_blocker2_retained_single_run(*args: Any, **kwargs: Any) -> Any:
    import blocker2_retained_absolute_path_control_v0_1 as retained

    return retained.run_retained_single_run(*args, **kwargs)


def run_validation_matrix(
    fixture_root: str | Path,
    *,
    second_volume_root: str | Path | None = None,
) -> tuple[ValidationCaseResult, ...]:
    return (
        validate_v1_full_chain_positive(fixture_root),
        validate_v2_existing_destination_directory(fixture_root),
        validate_v3_existing_destination_file(fixture_root),
        validate_v4_coordinated_destination_claim(fixture_root),
        validate_v5_source_reparse_rejected(fixture_root),
        validate_v6_destination_parent_reparse_rejected(fixture_root),
        validate_v7_mutation_content_mismatch(fixture_root),
        validate_v8_identity_continuity(fixture_root),
        *validate_v9_invalid_names(),
        validate_v10_unsupported_profile(fixture_root),
        validate_v11_cross_volume_optional(
            fixture_root,
            second_volume_root=second_volume_root,
        ),
        validate_v12_native_error_retention(fixture_root),
    )


def _replace_case_id(result: ValidationCaseResult, case_id: str) -> ValidationCaseResult:
    return replace(result, case_id=case_id)


def _case_result(
    case_id: str,
    status: str,
    detail: str,
    failure_code: str | None,
    *,
    skip_reason: str | None = None,
    native_error_code: int | None = None,
    native_error_name: str | None = None,
    policy_identity: dict[str, str] | None = None,
    support_profile: SupportProfile | None = None,
    source_identity_before: ObjectIdentity | None = None,
    retained_handle_identity_after: ObjectIdentity | None = None,
    final_identity_after: ObjectIdentity | None = None,
    source_parent_identity_before: ObjectIdentity | None = None,
    source_parent_identity_after: ObjectIdentity | None = None,
    destination_parent_identity_before: ObjectIdentity | None = None,
    destination_parent_identity_after: ObjectIdentity | None = None,
    source_exists_after_native_failure: bool | None = None,
    final_exists_after_native_failure: bool | None = None,
    manifest_before_sha256: str | None = None,
    manifest_after_sha256: str | None = None,
    durability_probes: tuple[DurabilityProbe, ...] = (),
) -> ValidationCaseResult:
    if (
        status not in STATUS_TAXONOMY
        and status not in CONTROL_STATUS_TAXONOMY
        and not status.startswith("DIRECTORY_DURABILITY_")
    ):
        raise ValidationError("unknown status")
    return ValidationCaseResult(
        case_id=case_id,
        status=status,
        detail=detail,
        failure_code=failure_code,
        skip_reason=skip_reason,
        native_error_code=native_error_code,
        native_error_name=native_error_name,
        policy_identity=policy_identity or validation_policy_identity(),
        support_profile=support_profile,
        source_identity_before=source_identity_before,
        retained_handle_identity_after=retained_handle_identity_after,
        final_identity_after=final_identity_after,
        source_parent_identity_before=source_parent_identity_before,
        source_parent_identity_after=source_parent_identity_after,
        destination_parent_identity_before=destination_parent_identity_before,
        destination_parent_identity_after=destination_parent_identity_after,
        source_exists_after_native_failure=source_exists_after_native_failure,
        final_exists_after_native_failure=final_exists_after_native_failure,
        manifest_before_sha256=manifest_before_sha256,
        manifest_after_sha256=manifest_after_sha256,
        durability_probes=durability_probes,
    )


def _native_contract_rejection_gated(result: ValidationCaseResult) -> bool:
    if result.status == INDETERMINATE and result.native_error_code == ERROR_INVALID_PARAMETER:
        return True
    return result.status == UNSUPPORTED and result.native_error_code == ERROR_NOT_SUPPORTED


def _native_rename_failure_status(error_code: int) -> str:
    if error_code == ERROR_INVALID_PARAMETER:
        return INDETERMINATE
    if error_code == ERROR_NOT_SUPPORTED:
        return UNSUPPORTED
    return FAILED


def _native_rename_failure_detail(error_code: int) -> str:
    if error_code == ERROR_INVALID_PARAMETER:
        return (
            "native rename phase returned ERROR_INVALID_PARAMETER; cause remains "
            "unresolved among user-mode RootDirectory-relative contract rejection, "
            "destination-parent access/setup requirement, or another valid native "
            "parameter constraint"
        )
    if error_code == ERROR_NOT_SUPPORTED:
        return "native FileRenameInfo call is unsupported"
    return "native no-replace rename failed"
