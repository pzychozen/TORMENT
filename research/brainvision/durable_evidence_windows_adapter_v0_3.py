from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Any

import durable_evidence_schema_v0_3 as schema


DIRECTORY_DURABILITY_CONFIRMED = schema.DIRECTORY_DURABILITY_CONFIRMED
DIRECTORY_DURABILITY_UNSUPPORTED = schema.DIRECTORY_DURABILITY_UNSUPPORTED
DIRECTORY_DURABILITY_DENIED = schema.DIRECTORY_DURABILITY_DENIED
DIRECTORY_DURABILITY_INDETERMINATE = schema.DIRECTORY_DURABILITY_INDETERMINATE
DIRECTORY_DURABILITY_TARGET_INVALID = schema.DIRECTORY_DURABILITY_TARGET_INVALID
DIRECTORY_DURABILITY_IDENTITY_CHANGED = schema.DIRECTORY_DURABILITY_IDENTITY_CHANGED
DIRECTORY_DURABILITY_OPERATION_FAILED = schema.DIRECTORY_DURABILITY_OPERATION_FAILED

PROMOTION_CONFIRMED = "PROMOTION_CONFIRMED"
PROMOTION_UNCONFIRMED = "PROMOTION_UNCONFIRMED"


class PlatformPrimitiveUnvalidated(RuntimeError):
    pass


@dataclass(frozen=True)
class DirectoryDurabilityContext:
    target_role: str = schema.ARTIFACT_PARENT_DIRECTORY
    operation: str = schema.DIRECTORY_DURABILITY_OPERATION_IDENTITY
    event_kind: str = "DIRECTORY_ENTRY_DURABILITY"


@dataclass(frozen=True)
class DirectoryDurabilityResult:
    status: str
    detail: str
    failure_code: str | None = None
    platform: str | None = None
    operation: str = schema.DIRECTORY_DURABILITY_OPERATION_IDENTITY
    target_path_identity: dict[str, Any] | None = None
    native_error_code: int | None = None
    native_error_name: str | None = None
    adapter_identity: str = schema.DIRECTORY_DURABILITY_ADAPTER_IDENTITY
    adapter_policy_identity: dict[str, str] | None = None
    target_role: str | None = None
    validation_profile_identity: str = (
        schema.DIRECTORY_DURABILITY_VALIDATION_PROFILE_IDENTITY
    )


@dataclass(frozen=True)
class DirectoryPromotionResult:
    status: str
    detail: str


class WindowsDurabilityAdapter:
    def sync_directory_entry(
        self,
        directory_path: str,
        *,
        context: DirectoryDurabilityContext | None = None,
    ) -> DirectoryDurabilityResult:
        raise NotImplementedError


class SameVolumeNoReplacePromotionAdapter:
    def promote_verified_directory_no_replace(
        self, source_directory_path: str, destination_directory_path: str
    ) -> DirectoryPromotionResult:
        raise NotImplementedError


class FailClosedWindowsDurabilityAdapter(WindowsDurabilityAdapter):
    def sync_directory_entry(
        self,
        directory_path: str,
        *,
        context: DirectoryDurabilityContext | None = None,
    ) -> DirectoryDurabilityResult:
        context = _coerce_context(context)
        return _result(
            DIRECTORY_DURABILITY_UNSUPPORTED,
            "Windows directory-entry durability adapter is absent.",
            schema.ADAPTER_ABSENT,
            context=context,
            platform=_platform_name(),
        )


class Win32DirectoryDurabilityAdapter(WindowsDurabilityAdapter):
    def sync_directory_entry(
        self,
        directory_path: str,
        *,
        context: DirectoryDurabilityContext | None = None,
    ) -> DirectoryDurabilityResult:
        context = _coerce_context(context)
        try:
            return _sync_directory_entry(directory_path, context)
        except Exception as exc:  # fail closed across the adapter boundary
            return _result(
                DIRECTORY_DURABILITY_INDETERMINATE,
                "directory durability adapter exception: %s" % type(exc).__name__,
                schema.UNEXPECTED_EXCEPTION,
                context=context,
                platform=_platform_name(),
            )


class FailClosedSameVolumeNoReplacePromotionAdapter(SameVolumeNoReplacePromotionAdapter):
    def promote_verified_directory_no_replace(
        self, source_directory_path: str, destination_directory_path: str
    ) -> DirectoryPromotionResult:
        return DirectoryPromotionResult(
            PROMOTION_UNCONFIRMED,
            "Same-volume no-replace directory promotion primitive is unvalidated.",
        )


ERROR_INVALID_FUNCTION = 1
ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3
ERROR_ACCESS_DENIED = 5
ERROR_NOT_READY = 21
ERROR_GEN_FAILURE = 31
ERROR_SHARING_VIOLATION = 32
ERROR_LOCK_VIOLATION = 33
ERROR_NOT_SUPPORTED = 50
ERROR_INVALID_PARAMETER = 87
ERROR_DEVICE_NOT_CONNECTED = 1167
ERROR_PRIVILEGE_NOT_HELD = 1314

ERROR_NAMES = {
    ERROR_INVALID_FUNCTION: "ERROR_INVALID_FUNCTION",
    ERROR_FILE_NOT_FOUND: "ERROR_FILE_NOT_FOUND",
    ERROR_PATH_NOT_FOUND: "ERROR_PATH_NOT_FOUND",
    ERROR_ACCESS_DENIED: "ERROR_ACCESS_DENIED",
    ERROR_NOT_READY: "ERROR_NOT_READY",
    ERROR_GEN_FAILURE: "ERROR_GEN_FAILURE",
    ERROR_SHARING_VIOLATION: "ERROR_SHARING_VIOLATION",
    ERROR_LOCK_VIOLATION: "ERROR_LOCK_VIOLATION",
    ERROR_NOT_SUPPORTED: "ERROR_NOT_SUPPORTED",
    ERROR_INVALID_PARAMETER: "ERROR_INVALID_PARAMETER",
    ERROR_DEVICE_NOT_CONNECTED: "ERROR_DEVICE_NOT_CONNECTED",
    ERROR_PRIVILEGE_NOT_HELD: "ERROR_PRIVILEGE_NOT_HELD",
}

GENERIC_WRITE = 0x40000000
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


def _sync_directory_entry(
    directory_path: str,
    context: DirectoryDurabilityContext,
) -> DirectoryDurabilityResult:
    if sys.platform != "win32":
        return _result(
            DIRECTORY_DURABILITY_UNSUPPORTED,
            "directory durability is unsupported on non-Windows platforms",
            schema.NON_WINDOWS_PLATFORM,
            context=context,
            platform=_platform_name(),
        )
    version = sys.getwindowsversion()
    product_type = getattr(version, "product_type", None)
    if version.major < 10 or product_type != 1:
        return _result(
            DIRECTORY_DURABILITY_UNSUPPORTED,
            "directory durability is unsupported outside Windows 10/11 workstation",
            schema.WINDOWS_VERSION_UNSUPPORTED,
            context=context,
            platform="windows",
        )
    if not os.path.isabs(str(directory_path)):
        return _result(
            DIRECTORY_DURABILITY_TARGET_INVALID,
            "directory durability target is not absolute",
            schema.TARGET_NOT_ABSOLUTE,
            context=context,
            platform="windows",
        )
    normalized = os.path.abspath(str(directory_path))
    if _is_unc_path(normalized):
        return _result(
            DIRECTORY_DURABILITY_UNSUPPORTED,
            "UNC directory durability targets are unsupported",
            schema.DRIVE_TYPE_UNSUPPORTED,
            context=context,
            platform="windows",
        )
    root = _drive_root(normalized)
    if root is None:
        return _result(
            DIRECTORY_DURABILITY_UNSUPPORTED,
            "directory durability target drive root is unsupported",
            schema.DRIVE_TYPE_UNSUPPORTED,
            context=context,
            platform="windows",
        )
    kernel32 = _kernel32()
    drive_type = kernel32.GetDriveTypeW(root)
    if drive_type != DRIVE_FIXED:
        return _result(
            DIRECTORY_DURABILITY_UNSUPPORTED,
            "directory durability target is not on a fixed local drive",
            schema.DRIVE_TYPE_UNSUPPORTED,
            context=context,
            platform="windows",
        )
    filesystem_result = _check_ntfs(kernel32, root, context)
    if filesystem_result is not None:
        return filesystem_result
    win32_path = _windows_api_path(normalized)
    attributes = kernel32.GetFileAttributesW(win32_path)
    if attributes == INVALID_FILE_ATTRIBUTES:
        error_code = kernel32.GetLastError()
        return _attribute_failure(error_code, context)
    if (attributes & FILE_ATTRIBUTE_DIRECTORY) == 0:
        return _result(
            DIRECTORY_DURABILITY_TARGET_INVALID,
            "directory durability target is not a directory",
            schema.TARGET_NOT_DIRECTORY,
            context=context,
            platform="windows",
        )
    if (attributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0:
        return _result(
            DIRECTORY_DURABILITY_TARGET_INVALID,
            "directory durability target is a reparse point",
            schema.TARGET_REPARSE_POINT,
            context=context,
            platform="windows",
        )

    preflight = _identity_from_new_handle(kernel32, win32_path, context, "preflight")
    if isinstance(preflight, DirectoryDurabilityResult):
        return preflight
    flush_handle = _open_directory_handle(kernel32, win32_path, context)
    if isinstance(flush_handle, DirectoryDurabilityResult):
        return flush_handle
    flush_identity = _identity_from_handle(kernel32, flush_handle, context)
    if isinstance(flush_identity, DirectoryDurabilityResult):
        _close_identity_handle(kernel32, flush_handle, context)
        return flush_identity
    if flush_identity != preflight:
        _close_identity_handle(kernel32, flush_handle, context)
        return _result(
            DIRECTORY_DURABILITY_IDENTITY_CHANGED,
            "directory identity changed before flush",
            schema.TARGET_IDENTITY_CHANGED,
            context=context,
            platform="windows",
        )
    if not kernel32.FlushFileBuffers(flush_handle):
        error_code = kernel32.GetLastError()
        close_result = _close_identity_handle(kernel32, flush_handle, context)
        if close_result is not None:
            return close_result
        return _native_failure(error_code, "flush", context)
    close_result = _close_identity_handle(kernel32, flush_handle, context)
    if close_result is not None:
        return close_result
    post = _identity_from_new_handle(kernel32, win32_path, context, "post-flush")
    if isinstance(post, DirectoryDurabilityResult):
        return post
    if post != flush_identity:
        return _result(
            DIRECTORY_DURABILITY_IDENTITY_CHANGED,
            "directory identity changed after flush",
            schema.TARGET_IDENTITY_CHANGED,
            context=context,
            platform="windows",
        )
    return _result(
        DIRECTORY_DURABILITY_CONFIRMED,
        "Windows directory-entry durability confirmed",
        None,
        context=context,
        platform="windows",
        target_path_identity=_target_identity(normalized, flush_identity),
    )


def _coerce_context(
    context: DirectoryDurabilityContext | None,
) -> DirectoryDurabilityContext:
    if context is None:
        return DirectoryDurabilityContext()
    if context.target_role not in schema.DIRECTORY_DURABILITY_TARGET_ROLES:
        return DirectoryDurabilityContext(target_role=schema.ARTIFACT_PARENT_DIRECTORY)
    return context


def _kernel32():
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
    kernel32.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
    kernel32.FlushFileBuffers.restype = wintypes.BOOL
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
    return kernel32


def _open_directory_handle(
    kernel32,
    win32_path: str,
    context: DirectoryDurabilityContext,
):
    handle = kernel32.CreateFileW(
        win32_path,
        GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if _is_invalid_handle(handle):
        error_code = kernel32.GetLastError()
        return _native_failure(error_code, "open", context)
    return handle


def _identity_from_new_handle(
    kernel32,
    win32_path: str,
    context: DirectoryDurabilityContext,
    phase: str,
):
    handle = kernel32.CreateFileW(
        win32_path,
        GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if _is_invalid_handle(handle):
        error_code = kernel32.GetLastError()
        return _identity_unavailable(
            "directory identity handle open failed during %s" % phase,
            context,
            error_code,
        )
    identity = _identity_from_handle(kernel32, handle, context)
    close_result = _close_identity_handle(kernel32, handle, context)
    if isinstance(identity, DirectoryDurabilityResult):
        return identity
    if close_result is not None:
        return close_result
    return identity


def _identity_from_handle(kernel32, handle, context: DirectoryDurabilityContext):
    info = _BY_HANDLE_FILE_INFORMATION()
    if not kernel32.GetFileInformationByHandle(handle, ctypes.byref(info)):
        error_code = kernel32.GetLastError()
        return _identity_unavailable(
            "directory identity query failed",
            context,
            error_code,
        )
    return (
        int(info.dwVolumeSerialNumber),
        int(info.nFileIndexHigh),
        int(info.nFileIndexLow),
    )


def _close_identity_handle(kernel32, handle, context: DirectoryDurabilityContext):
    if kernel32.CloseHandle(handle):
        return None
    error_code = kernel32.GetLastError()
    return _result(
        DIRECTORY_DURABILITY_INDETERMINATE,
        "directory handle close result is indeterminate",
        schema.DIRECTORY_CLOSE_INDETERMINATE,
        context=context,
        platform="windows",
        native_error_code=error_code,
        native_error_name=_error_name(error_code),
    )


def _check_ntfs(kernel32, root: str, context: DirectoryDurabilityContext):
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
        error_code = kernel32.GetLastError()
        return _result(
            DIRECTORY_DURABILITY_INDETERMINATE,
            "filesystem support could not be determined",
            schema.UNKNOWN_NATIVE_ERROR,
            context=context,
            platform="windows",
            native_error_code=error_code,
            native_error_name=_error_name(error_code),
        )
    if filesystem_name.value.upper() != "NTFS":
        return _result(
            DIRECTORY_DURABILITY_UNSUPPORTED,
            "directory durability target filesystem is unsupported",
            schema.FILESYSTEM_UNSUPPORTED,
            context=context,
            platform="windows",
        )
    return None


def _attribute_failure(
    error_code: int,
    context: DirectoryDurabilityContext,
) -> DirectoryDurabilityResult:
    if error_code in (ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND):
        return _result(
            DIRECTORY_DURABILITY_TARGET_INVALID,
            "directory durability target is missing",
            schema.TARGET_MISSING,
            context=context,
            platform="windows",
            native_error_code=error_code,
            native_error_name=_error_name(error_code),
        )
    return _result(
        DIRECTORY_DURABILITY_INDETERMINATE,
        "directory target attributes could not be determined",
        schema.UNKNOWN_NATIVE_ERROR,
        context=context,
        platform="windows",
        native_error_code=error_code,
        native_error_name=_error_name(error_code),
    )


def _native_failure(
    error_code: int,
    phase: str,
    context: DirectoryDurabilityContext,
) -> DirectoryDurabilityResult:
    if error_code in (ERROR_ACCESS_DENIED, ERROR_SHARING_VIOLATION):
        return _phase_failure(
            DIRECTORY_DURABILITY_DENIED,
            phase,
            context,
            error_code,
            "directory durability operation was denied",
        )
    if error_code in (ERROR_LOCK_VIOLATION, ERROR_PRIVILEGE_NOT_HELD):
        return _phase_failure(
            DIRECTORY_DURABILITY_DENIED,
            phase,
            context,
            error_code,
            "directory durability operation was denied",
        )
    if error_code in (ERROR_INVALID_FUNCTION, ERROR_NOT_SUPPORTED):
        return _phase_failure(
            DIRECTORY_DURABILITY_UNSUPPORTED,
            phase,
            context,
            error_code,
            "directory durability operation is unsupported",
        )
    if error_code in (ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND):
        return _result(
            DIRECTORY_DURABILITY_TARGET_INVALID,
            "directory durability target is missing",
            schema.TARGET_MISSING,
            context=context,
            platform="windows",
            native_error_code=error_code,
            native_error_name=_error_name(error_code),
        )
    if error_code in (
        ERROR_INVALID_PARAMETER,
        ERROR_NOT_READY,
        ERROR_DEVICE_NOT_CONNECTED,
        ERROR_GEN_FAILURE,
    ):
        return _phase_failure(
            DIRECTORY_DURABILITY_OPERATION_FAILED,
            phase,
            context,
            error_code,
            "directory durability operation failed",
        )
    return _result(
        DIRECTORY_DURABILITY_INDETERMINATE,
        "unknown native directory durability error",
        schema.UNKNOWN_NATIVE_ERROR,
        context=context,
        platform="windows",
        native_error_code=error_code,
        native_error_name=_error_name(error_code),
    )


def _phase_failure(
    status: str,
    phase: str,
    context: DirectoryDurabilityContext,
    error_code: int,
    detail: str,
) -> DirectoryDurabilityResult:
    if phase == "flush":
        code_by_status = {
            DIRECTORY_DURABILITY_DENIED: schema.DIRECTORY_FLUSH_DENIED,
            DIRECTORY_DURABILITY_UNSUPPORTED: schema.DIRECTORY_FLUSH_UNSUPPORTED,
            DIRECTORY_DURABILITY_OPERATION_FAILED: schema.DIRECTORY_FLUSH_FAILED,
        }
    else:
        code_by_status = {
            DIRECTORY_DURABILITY_DENIED: schema.DIRECTORY_OPEN_DENIED,
            DIRECTORY_DURABILITY_UNSUPPORTED: schema.DIRECTORY_OPEN_UNSUPPORTED,
            DIRECTORY_DURABILITY_OPERATION_FAILED: schema.DIRECTORY_OPEN_FAILED,
        }
    return _result(
        status,
        detail,
        code_by_status[status],
        context=context,
        platform="windows",
        native_error_code=error_code,
        native_error_name=_error_name(error_code),
    )


def _identity_unavailable(
    detail: str,
    context: DirectoryDurabilityContext,
    error_code: int,
) -> DirectoryDurabilityResult:
    return _result(
        DIRECTORY_DURABILITY_INDETERMINATE,
        detail,
        schema.TARGET_IDENTITY_UNAVAILABLE,
        context=context,
        platform="windows",
        native_error_code=error_code,
        native_error_name=_error_name(error_code),
    )


def _result(
    status: str,
    detail: str,
    failure_code: str | None,
    *,
    context: DirectoryDurabilityContext,
    platform: str | None,
    target_path_identity: dict[str, Any] | None = None,
    native_error_code: int | None = None,
    native_error_name: str | None = None,
) -> DirectoryDurabilityResult:
    return DirectoryDurabilityResult(
        status=status,
        detail=detail,
        failure_code=failure_code,
        platform=platform,
        operation=context.operation,
        target_path_identity=target_path_identity,
        native_error_code=native_error_code,
        native_error_name=native_error_name,
        adapter_identity=schema.DIRECTORY_DURABILITY_ADAPTER_IDENTITY,
        adapter_policy_identity=schema.directory_durability_policy_identity(),
        target_role=context.target_role,
        validation_profile_identity=(
            schema.DIRECTORY_DURABILITY_VALIDATION_PROFILE_IDENTITY
        ),
    )


def _target_identity(normalized: str, identity: tuple[int, int, int]) -> dict[str, Any]:
    return {
        "normalized_path": normalized,
        "volume_serial_number": identity[0],
        "file_index_high": identity[1],
        "file_index_low": identity[2],
    }


def _platform_name() -> str:
    if sys.platform == "win32":
        return "windows"
    return sys.platform


def _is_unc_path(path_text: str) -> bool:
    return path_text.startswith("\\\\") and not path_text.startswith("\\\\?\\")


def _drive_root(path_text: str) -> str | None:
    drive = Path(path_text).drive
    if len(drive) == 2 and drive[1] == ":":
        return drive + "\\"
    return None


def _windows_api_path(path_text: str) -> str:
    prefix = "\\\\?\\"
    if path_text.startswith(prefix):
        return path_text
    return prefix + path_text


def _is_invalid_handle(handle) -> bool:
    return handle == ctypes.c_void_p(-1).value


def _error_name(error_code: int | None) -> str | None:
    if error_code is None:
        return None
    return ERROR_NAMES.get(int(error_code))
