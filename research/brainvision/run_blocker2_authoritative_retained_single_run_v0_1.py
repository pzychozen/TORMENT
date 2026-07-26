from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence


MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

import blocker2_retained_absolute_path_control_v0_1 as retained


SCHEMA = "torment.brainvision.blocker2.operator_wrapper.authorization_input.v0.1"
DECLARATION_SCHEMA = (
    "torment.brainvision.blocker2.operator_wrapper."
    "authorization_input_declaration.v0.1"
)
WRAPPER_VERSION = "v0.1"

PREPARE_PATHS = "PREPARE_PATHS"
PREFLIGHT_ONLY = "PREFLIGHT_ONLY"
EXECUTE_EXACT_SINGLE_RUN = "EXECUTE_EXACT_SINGLE_RUN"
MODES = (PREPARE_PATHS, PREFLIGHT_ONLY, EXECUTE_EXACT_SINGLE_RUN)

PREPARATION_COMPLETE = "PREPARATION_COMPLETE"
PREFLIGHT_ACCEPTED_UNCONSUMED = "PREFLIGHT_ACCEPTED_UNCONSUMED"
PREFLIGHT_REJECTED_UNCONSUMED = "PREFLIGHT_REJECTED_UNCONSUMED"
AUTHORITATIVE_RUN_COMPLETE = "AUTHORITATIVE_RUN_COMPLETE"
AUTHORITATIVE_RUN_FAILED_CONSUMED = "AUTHORITATIVE_RUN_FAILED_CONSUMED"
AUTHORITATIVE_RUN_INTERRUPTED_CONSUMED = "AUTHORITATIVE_RUN_INTERRUPTED_CONSUMED"
AUTHORITY_ALREADY_CONSUMED = "AUTHORITY_ALREADY_CONSUMED"
INVALID_AUTHORIZATION_INPUT = "INVALID_AUTHORIZATION_INPUT"

REAL_EXECUTOR_SELECTOR = "REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1"

AUTHORITY_REGISTRY_ROOT = Path(r"C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3")
FIXTURE_ROOT = Path(r"C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3")
RESULT_PARENT = Path(r"C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3")

REQUIRED_CASE_ORDER = ("A1", "A2", "A3", "A5")
FORBIDDEN_CASES = {"A4", "A6", "A7", "A8"}
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
DRIVE_DOS_RE = re.compile(r"^[A-Za-z]:\\")

TOP_LEVEL_FIELDS = frozenset(
    {
        "schema",
        "authorization_status",
        "wrapper_mode",
        "operator_identity",
        "single_process_declaration",
        "single_attempt_declaration",
        "real_executor_selector",
        "retained_mode",
        "authoritative",
        "repository_identity",
        "source_identity_inventory",
        "document_identity_inventory",
        "runtime_declaration_identities",
        "path_model",
        "execution_authorization_identity_block",
        "retained_authorization",
        "repository_state",
        "source_observations",
        "case_set",
        "a6_selected",
        "authorization_input_identity",
        "execution_authorization_document_identity",
        "fault_injection_disabled",
    }
)

AUTHORIZATION_INPUT_IDENTITY_FIELDS = frozenset(
    {
        "schema",
        "authorization_input_sha256",
        "canonical_authorization_declaration_identity",
    }
)

RUNTIME_IDENTITY_FIELDS = frozenset(
    {
        "retained_orchestration_policy_sha256",
        "native_helper_policy_sha256",
        "retained_schema_sha256",
        "case_set_sha256",
        "fixture_profile_sha256",
        "authority_registry_profile_sha256",
        "evidence_chain_sha256",
        "retained_mode_identity",
    }
)

PATH_MODEL_FIELDS = frozenset(
    {
        "authority_registry_root",
        "fixture_root",
        "result_parent",
        "result_directory",
        "global_authority_entry_path",
        "local_gate_path",
        "run_result_path",
        "retained_completion_path",
    }
)

EXECUTION_AUTHORIZATION_DOCUMENT_FIELDS = frozenset(
    {
        "path",
        "git_blob_oid",
        "checked_out_byte_sha256",
        "canonical_authorization_declaration_identity",
        "authorization_status",
    }
)


class WrapperValidationError(ValueError):
    def __init__(self, terminal_label: str, detail: str):
        super().__init__(detail)
        self.terminal_label = terminal_label
        self.detail = detail


@dataclass(frozen=True)
class FileIdentity:
    git_blob_oid: str
    checked_out_byte_sha256: str
    checked_out_byte_length: int

    def as_payload(self) -> dict[str, Any]:
        return {
            "git_blob_oid": self.git_blob_oid,
            "checked_out_byte_sha256": self.checked_out_byte_sha256,
            "checked_out_byte_length": self.checked_out_byte_length,
        }


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reject_duplicate_pairs(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WrapperValidationError(
                INVALID_AUTHORIZATION_INPUT,
                "duplicate JSON object key: %s" % key,
            )
        result[key] = value
    return result


def load_canonical_json_file(path: str | Path) -> tuple[dict[str, Any], bytes]:
    source = Path(path)
    raw = source.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "UTF-8 BOM rejected")
    try:
        loaded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                WrapperValidationError(
                    INVALID_AUTHORIZATION_INPUT,
                    "non-finite JSON number rejected: %s" % value,
                )
            ),
        )
    except WrapperValidationError:
        raise
    except Exception as exc:
        raise WrapperValidationError(
            INVALID_AUTHORIZATION_INPUT,
            "authorization input JSON parse failed: %s" % type(exc).__name__,
        ) from exc
    if not isinstance(loaded, dict):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "top-level JSON must be object")
    canonical = canonical_json_bytes(loaded)
    if raw != canonical:
        raise WrapperValidationError(
            INVALID_AUTHORIZATION_INPUT,
            "authorization input is not canonical JSON",
        )
    return loaded, raw


def authorization_declaration(payload: Mapping[str, Any]) -> dict[str, Any]:
    declaration_payload = {
        key: payload[key] for key in sorted(payload) if key != "authorization_input_identity"
    }
    return {
        "schema": DECLARATION_SCHEMA,
        "authorization_input": declaration_payload,
    }


def computed_authorization_input_identity(payload: Mapping[str, Any]) -> dict[str, str]:
    declaration_payload = {
        key: payload[key] for key in sorted(payload) if key != "authorization_input_identity"
    }
    declaration = {
        "schema": DECLARATION_SCHEMA,
        "authorization_input": declaration_payload,
    }
    return {
        "schema": "torment.brainvision.blocker2.operator_wrapper.authorization_input_identity.v0.1",
        "authorization_input_sha256": sha256_hex(canonical_json_bytes(declaration_payload)),
        "canonical_authorization_declaration_identity": sha256_hex(
            canonical_json_bytes(declaration)
        ),
    }


def with_computed_authorization_input_identity(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(payload)
    result["authorization_input_identity"] = computed_authorization_input_identity(result)
    return result


def retained_mode_identity() -> str:
    return retained.canonical_sha256(
        {
            "schema": "torment.brainvision.blocker2.retained.mode_identity.v0.1",
            "retained_mode": retained.RETAINED_MODE,
        }
    )


def expected_runtime_identities() -> dict[str, str]:
    return {
        "retained_orchestration_policy_sha256": (
            retained.authorized_absolute_path_control_policy_identity()["policy_sha256"]
        ),
        "native_helper_policy_sha256": retained.native_helper_policy_identity()[
            "policy_sha256"
        ],
        "retained_schema_sha256": retained.retained_schema_identity()["schema_sha256"],
        "case_set_sha256": retained.retained_case_set_identity()["case_set_sha256"],
        "fixture_profile_sha256": retained.fixture_profile_identity()[
            "fixture_profile_sha256"
        ],
        "authority_registry_profile_sha256": (
            retained.authority_registry_profile_identity()[
                "authority_registry_profile_sha256"
            ]
        ),
        "evidence_chain_sha256": retained.evidence_chain_identity()[
            "evidence_chain_sha256"
        ],
        "retained_mode_identity": retained_mode_identity(),
    }


def _canonical_path_text(path: str | Path) -> str:
    return str(Path(path).resolve())


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _require_drive_qualified_dos_path(path: Path) -> None:
    text = str(path)
    if not DRIVE_DOS_RE.match(text):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "path is not drive-qualified")
    if text.startswith("\\\\") or text.startswith("\\\\?\\") or text.startswith("\\\\.\\"):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "device or UNC path rejected")
    if text.startswith("\\??\\") or "\\Volume{" in text:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "NT or volume path rejected")


def derived_path_model(execution_authorization_identity: str) -> dict[str, str]:
    result_directory = RESULT_PARENT / execution_authorization_identity
    return {
        "authority_registry_root": _canonical_path_text(AUTHORITY_REGISTRY_ROOT),
        "fixture_root": _canonical_path_text(FIXTURE_ROOT),
        "result_parent": _canonical_path_text(RESULT_PARENT),
        "result_directory": _canonical_path_text(result_directory),
        "global_authority_entry_path": _canonical_path_text(
            AUTHORITY_REGISTRY_ROOT
            / (execution_authorization_identity + retained.GLOBAL_AUTHORITY_ENTRY_SUFFIX)
        ),
        "local_gate_path": _canonical_path_text(result_directory / retained.GATE_ENTRY_FILENAME),
        "run_result_path": _canonical_path_text(result_directory / retained.RUN_RESULT_FILENAME),
        "retained_completion_path": _canonical_path_text(
            result_directory / retained.RETAINED_COMPLETION_FILENAME
        ),
    }


def _is_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    attrs = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attrs & getattr(os, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _drive_root_for(path: Path) -> str:
    drive = path.drive
    if not drive:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "path has no drive")
    return drive + "\\"


def _volume_profile(path: Path) -> dict[str, Any]:
    if os.name != "nt":
        raise WrapperValidationError(
            INVALID_AUTHORIZATION_INPUT,
            "Windows local fixed NTFS profile required",
        )
    root = _drive_root_for(path)
    kernel32 = ctypes.windll.kernel32
    drive_type = kernel32.GetDriveTypeW(ctypes.c_wchar_p(root))
    volume_name = ctypes.create_unicode_buffer(261)
    filesystem = ctypes.create_unicode_buffer(261)
    serial = ctypes.c_uint32(0)
    max_component = ctypes.c_uint32(0)
    flags = ctypes.c_uint32(0)
    ok = kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(root),
        volume_name,
        len(volume_name),
        ctypes.byref(serial),
        ctypes.byref(max_component),
        ctypes.byref(flags),
        filesystem,
        len(filesystem),
    )
    if not ok:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "volume query failed")
    if drive_type != 3:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "drive is not local fixed")
    if filesystem.value.upper() != "NTFS":
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "filesystem is not NTFS")
    return {
        "drive_root": root,
        "drive_type": "DRIVE_FIXED",
        "drive_type_code": drive_type,
        "filesystem_name": filesystem.value,
        "volume_serial_number": int(serial.value),
        "max_component_length": int(max_component.value),
    }


def _directory_identity(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "st_dev": int(stat.st_dev),
        "st_ino": int(stat.st_ino),
    }


def path_evidence(path: str | Path, *, role: str, repo_root: str | Path | None = None) -> dict[str, Any]:
    candidate = Path(path).resolve()
    _require_drive_qualified_dos_path(candidate)
    root = Path(repo_root).resolve() if repo_root is not None else retained.repository_root_from_here()
    if _is_relative_to(candidate, root):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s inside repository" % role)
    if not candidate.exists() or not candidate.is_dir():
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s is not directory" % role)
    if _is_reparse(candidate):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s is reparse" % role)
    return {
        "role": role,
        "canonical_path": str(candidate),
        "path_identity": retained.path_identity_for_role(candidate, role=role, must_exist=True)[
            "path_identity"
        ],
        "volume": _volume_profile(candidate),
        "directory_identity": _directory_identity(candidate),
        "reparse_status": "NOT_REPARSE_POINT",
        "repository_containment": "OUTSIDE_REPOSITORY",
    }


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s must be object" % name)
    return value


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s must be array" % name)
    return value


def _require_hex(value: Any, name: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str) or not pattern.match(value):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s must be hex" % name)
    if value == "0" * len(value) or value == "a" * len(value):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s placeholder rejected" % name)
    return value


def _reject_placeholder_text(value: Any, name: str) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if (
            value == retained.UNAVAILABLE_UNTIL_COMMIT
            or "placeholder" in lowered
            or "synthetic" in lowered
        ):
            raise WrapperValidationError(
                INVALID_AUTHORIZATION_INPUT,
                "%s placeholder or test value rejected" % name,
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_placeholder_text(item, "%s[%s]" % (name, index))
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_placeholder_text(item, "%s.%s" % (name, key))


def _validate_top_level(payload: Mapping[str, Any]) -> None:
    observed = set(payload)
    missing = TOP_LEVEL_FIELDS - observed
    extra = observed - TOP_LEVEL_FIELDS
    if missing:
        raise WrapperValidationError(
            INVALID_AUTHORIZATION_INPUT,
            "missing top-level fields: %s" % ",".join(sorted(missing)),
        )
    if extra:
        raise WrapperValidationError(
            INVALID_AUTHORIZATION_INPUT,
            "unknown top-level fields: %s" % ",".join(sorted(extra)),
        )
    if payload["schema"] != SCHEMA:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization schema mismatch")
    if payload["retained_mode"] != retained.RETAINED_MODE:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "retained mode mismatch")
    if payload["operator_identity"] != "Hilmir":
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "operator identity mismatch")
    if payload["single_process_declaration"] != "one Windows Command Prompt process":
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "single-process declaration mismatch")
    if payload["single_attempt_declaration"] != "one authoritative attempt":
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "single-attempt declaration mismatch")
    if payload["authoritative"] is not True:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authoritative input required")
    if payload["fault_injection_disabled"] is not True:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "fault controls rejected")
    if payload["a6_selected"] is not False:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "A6 rejected")
    if payload["real_executor_selector"] != REAL_EXECUTOR_SELECTOR:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "real executor selector mismatch")
    if payload["wrapper_mode"] not in MODES:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "unknown wrapper mode")


def _validate_authorization_input_identity(payload: Mapping[str, Any]) -> None:
    supplied = _require_mapping(payload["authorization_input_identity"], "authorization_input_identity")
    if set(supplied) != AUTHORIZATION_INPUT_IDENTITY_FIELDS:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization input identity shape mismatch")
    computed = computed_authorization_input_identity(payload)
    if dict(supplied) != computed:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization input identity mismatch")


def _validate_runtime_identities(payload: Mapping[str, Any]) -> None:
    supplied = _require_mapping(payload["runtime_declaration_identities"], "runtime_declaration_identities")
    if set(supplied) != RUNTIME_IDENTITY_FIELDS:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "runtime identity shape mismatch")
    expected = expected_runtime_identities()
    if dict(supplied) != expected:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "runtime identity mismatch")


def _validate_case_lock(payload: Mapping[str, Any]) -> None:
    case_set = _require_mapping(payload["case_set"], "case_set")
    selected = tuple(case_set.get("selected_cases", ()))
    execution_order = tuple(case_set.get("execution_order", ()))
    if selected != REQUIRED_CASE_ORDER or execution_order != REQUIRED_CASE_ORDER:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "case order mismatch")
    if set(selected) & FORBIDDEN_CASES:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "forbidden case selected")
    if len(set(selected)) != len(selected):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "duplicate case selected")
    if case_set.get("case_set_sha256") != retained.retained_case_set_identity()["case_set_sha256"]:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "case-set identity mismatch")


def _validate_execution_authorization_document(payload: Mapping[str, Any], *, mode: str) -> None:
    document = _require_mapping(
        payload["execution_authorization_document_identity"],
        "execution_authorization_document_identity",
    )
    if set(document) != EXECUTION_AUTHORIZATION_DOCUMENT_FIELDS:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization document identity shape mismatch")
    _require_hex(document["git_blob_oid"], "authorization document Git blob", HEX40_RE)
    _require_hex(document["checked_out_byte_sha256"], "authorization document bytes", HEX64_RE)
    _require_hex(document["canonical_authorization_declaration_identity"], "authorization declaration", HEX64_RE)
    if mode in (PREFLIGHT_ONLY, EXECUTE_EXACT_SINGLE_RUN):
        if document["authorization_status"] != "ACTIVE":
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization document is not ACTIVE")
        if payload["authorization_status"] != "ACTIVE":
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization status is not ACTIVE")


def _validate_execution_authorization_document_current_identity(
    payload: Mapping[str, Any],
    *,
    provider: FileIdentityProvider | None,
    repo_root: str | Path | None,
) -> None:
    document = _require_mapping(
        payload["execution_authorization_document_identity"],
        "execution_authorization_document_identity",
    )
    path = str(document["path"])
    current = provider(path) if provider is not None else _file_identity_from_disk(path, repo_root=repo_root)
    if current.git_blob_oid != document["git_blob_oid"]:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization document Git blob mismatch")
    if current.checked_out_byte_sha256 != document["checked_out_byte_sha256"]:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization document byte SHA mismatch")


def _validate_path_model(payload: Mapping[str, Any]) -> dict[str, str]:
    auth = _require_mapping(payload["retained_authorization"], "retained_authorization")
    auth_id = _require_hex(auth.get("authorization_identity"), "authorization identity", HEX64_RE)
    path_model = _require_mapping(payload["path_model"], "path_model")
    if set(path_model) != PATH_MODEL_FIELDS:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "path model shape mismatch")
    expected = derived_path_model(auth_id)
    if {key: str(path_model[key]) for key in sorted(path_model)} != expected:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "fixed path model mismatch")
    for key in ("authority_registry_root", "fixture_root", "result_parent", "result_directory"):
        _require_drive_qualified_dos_path(Path(path_model[key]))
    return expected


def _file_identity_from_disk(path: str | Path, *, repo_root: str | Path | None = None) -> FileIdentity:
    root = Path(repo_root).resolve() if repo_root is not None else retained.repository_root_from_here()
    file_path = Path(path)
    absolute = file_path if file_path.is_absolute() else root / file_path
    absolute = absolute.resolve()
    if not _is_relative_to(absolute, root):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "identity path outside repository")
    relative = absolute.relative_to(root).as_posix()
    data = absolute.read_bytes()
    blob = subprocess.run(
        ["git", "rev-parse", "HEAD:%s" % relative],
        cwd=str(root),
        text=True,
        capture_output=True,
        check=False,
    )
    if blob.returncode != 0:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "Git blob lookup failed")
    return FileIdentity(
        git_blob_oid=blob.stdout.strip(),
        checked_out_byte_sha256=sha256_hex(data),
        checked_out_byte_length=len(data),
    )


FileIdentityProvider = Callable[[str], FileIdentity]


def _validate_fixed_roots_outside_repository(repo_root: str | Path | None) -> None:
    root = Path(repo_root).resolve() if repo_root is not None else retained.repository_root_from_here()
    for name, fixed_root in (
        ("authority registry root", AUTHORITY_REGISTRY_ROOT),
        ("fixture root", FIXTURE_ROOT),
        ("result parent", RESULT_PARENT),
    ):
        if _is_relative_to(Path(fixed_root).resolve(), root):
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s is inside repository" % name)


def _validate_identity_inventory(
    inventory: Any,
    *,
    name: str,
    provider: FileIdentityProvider | None,
    repo_root: str | Path | None,
) -> None:
    for entry in _require_list(inventory, name):
        item = _require_mapping(entry, name + " entry")
        path = item.get("path") or item.get("relative_path")
        if not isinstance(path, str):
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "identity path missing")
        expected_blob = _require_hex(item.get("git_blob_oid"), "%s git blob" % path, HEX40_RE)
        expected_sha = _require_hex(item.get("checked_out_byte_sha256"), "%s bytes" % path, HEX64_RE)
        if item.get("git_blob_oid") == retained.UNAVAILABLE_UNTIL_COMMIT:
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "precommit source identity rejected")
        expected_len = item.get("checked_out_byte_length")
        current = provider(path) if provider is not None else _file_identity_from_disk(path, repo_root=repo_root)
        if current.git_blob_oid != expected_blob:
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s Git blob mismatch" % path)
        if current.checked_out_byte_sha256 != expected_sha:
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s byte SHA mismatch" % path)
        if expected_len is not None and current.checked_out_byte_length != expected_len:
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "%s byte length mismatch" % path)


def _repository_state_from_payload(payload: Mapping[str, Any]) -> retained.RepositoryState:
    state = _require_mapping(payload["repository_state"], "repository_state")
    return retained.RepositoryState(
        schema=str(state["schema"]),
        repo_root=str(state["repo_root"]),
        branch=str(state["branch"]),
        head=str(state["head"]),
        origin_main=str(state["origin_main"]),
        status_lines=tuple(state.get("status_lines", ())),
        dirty_authorized_surfaces=tuple(state.get("dirty_authorized_surfaces", ())),
        dirty_unrelated_surfaces=tuple(state.get("dirty_unrelated_surfaces", ())),
    )


def _source_expectation_from_payload(entry: Mapping[str, Any]) -> retained.SourceIdentityExpectation:
    return retained.SourceIdentityExpectation(
        relative_path=str(entry["relative_path"]),
        checked_out_byte_sha256=str(entry["checked_out_byte_sha256"]),
        checked_out_byte_length=int(entry["checked_out_byte_length"]),
        git_blob_oid=str(entry["git_blob_oid"]),
    )


def _source_observation_from_payload(entry: Mapping[str, Any]) -> retained.SourceIdentity:
    return retained.SourceIdentity(
        schema=str(entry["schema"]),
        relative_path=str(entry["relative_path"]),
        checked_out_byte_sha256=str(entry["checked_out_byte_sha256"]),
        checked_out_byte_length=int(entry["checked_out_byte_length"]),
        git_blob_oid=str(entry["git_blob_oid"]),
        git_blob_state=str(entry["git_blob_state"]),
    )


def _execution_block_from_payload(payload: Mapping[str, Any]) -> retained.ExecutionAuthorizationIdentityBlock:
    block = _require_mapping(
        payload["execution_authorization_identity_block"],
        "execution_authorization_identity_block",
    )
    sources = tuple(
        _source_expectation_from_payload(_require_mapping(item, "source identity expectation"))
        for item in _require_list(block["source_identities"], "execution source identities")
    )
    return retained.ExecutionAuthorizationIdentityBlock(
        execution_authorization_identity=str(block["execution_authorization_identity"]),
        retained_run_assessment_identity=str(block["retained_run_assessment_identity"]),
        implementation_preparation_authorization_identity=str(
            block["implementation_preparation_authorization_identity"]
        ),
        runtime_correction_authorization_identity=str(
            block["runtime_correction_authorization_identity"]
        ),
        expected_branch=str(block["expected_branch"]),
        expected_head=str(block["expected_head"]),
        expected_origin_main=str(block["expected_origin_main"]),
        retained_orchestration_policy_sha256=str(block["retained_orchestration_policy_sha256"]),
        native_helper_policy_sha256=str(block["native_helper_policy_sha256"]),
        retained_schema_sha256=str(block["retained_schema_sha256"]),
        case_set_sha256=str(block["case_set_sha256"]),
        fixture_profile_sha256=str(block["fixture_profile_sha256"]),
        authority_registry_root=Path(str(block["authority_registry_root"])),
        authority_registry_root_identity=str(block["authority_registry_root_identity"]),
        fixture_root_identity=str(block["fixture_root_identity"]),
        result_parent_identity=str(block["result_parent_identity"]),
        result_directory_identity=str(block["result_directory_identity"]),
        host_identity=str(block["host_identity"]),
        volume_identity=str(block["volume_identity"]),
        run_identity=str(block["run_identity"]),
        selected_a6=bool(block["selected_a6"]),
        source_identities=sources,
    )


def _retained_authorization_from_payload(payload: Mapping[str, Any]) -> retained.RetainedAuthorization:
    auth = _require_mapping(payload["retained_authorization"], "retained_authorization")
    return retained.RetainedAuthorization(
        mode=str(auth["mode"]),
        authorization_identity=str(auth["authorization_identity"]),
        assessment_identity=str(auth["assessment_identity"]),
        expected_branch=str(auth["expected_branch"]),
        expected_head=str(auth["expected_head"]),
        expected_origin_main=str(auth["expected_origin_main"]),
        result_directory=Path(str(auth["result_directory"])),
        fixture_root=Path(str(auth["fixture_root"])),
        selected_cases=tuple(auth.get("selected_cases", ())),
        optional_cases=tuple(auth.get("optional_cases", ())),
        authoritative=bool(auth["authoritative"]),
        allow_unrelated_outside_surfaces=bool(auth.get("allow_unrelated_outside_surfaces", False)),
        enforce_fixture_profile=bool(auth.get("enforce_fixture_profile", False)),
        execution_authorization=_execution_block_from_payload(payload),
    )


def validate_authorization_payload(
    payload: Mapping[str, Any],
    *,
    mode: str,
    raw_bytes: bytes | None = None,
    repo_root: str | Path | None = None,
    file_identity_provider: FileIdentityProvider | None = None,
    repository_state: retained.RepositoryState | None = None,
) -> dict[str, Any]:
    _validate_top_level(payload)
    _reject_placeholder_text(payload, "authorization input")
    if payload["wrapper_mode"] != mode:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "wrapper mode mismatch")
    _validate_authorization_input_identity(payload)
    _validate_runtime_identities(payload)
    _validate_case_lock(payload)
    _validate_execution_authorization_document(payload, mode=mode)
    path_model = _validate_path_model(payload)
    _validate_fixed_roots_outside_repository(repo_root)
    _validate_identity_inventory(
        payload["source_identity_inventory"],
        name="source_identity_inventory",
        provider=file_identity_provider,
        repo_root=repo_root,
    )
    _validate_identity_inventory(
        payload["document_identity_inventory"],
        name="document_identity_inventory",
        provider=file_identity_provider,
        repo_root=repo_root,
    )
    _validate_execution_authorization_document_current_identity(
        payload,
        provider=file_identity_provider,
        repo_root=repo_root,
    )
    state = repository_state if repository_state is not None else retained.collect_repository_state(repo_root)
    repo_identity = _require_mapping(payload["repository_identity"], "repository_identity")
    if state.branch != repo_identity.get("branch"):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "repository branch mismatch")
    if state.head != repo_identity.get("head"):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "repository HEAD mismatch")
    if state.origin_main != repo_identity.get("origin_main"):
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "repository origin/main mismatch")
    if state.head != state.origin_main:
        raise WrapperValidationError(PREFLIGHT_REJECTED_UNCONSUMED, "HEAD and origin/main differ")
    if (Path(state.repo_root) / ".git" / "index.lock").exists():
        raise WrapperValidationError(PREFLIGHT_REJECTED_UNCONSUMED, "repository index lock present")
    auth = _retained_authorization_from_payload(payload)
    if tuple(auth.selected_cases) != REQUIRED_CASE_ORDER or tuple(auth.optional_cases) != ():
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "retained case lock mismatch")
    if auth.authorization_identity != auth.execution_authorization.execution_authorization_identity:
        raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "authorization identity mismatch")
    source_observations = {
        str(item["relative_path"]): _source_observation_from_payload(_require_mapping(item, "source observation"))
        for item in _require_list(payload["source_observations"], "source_observations")
    }
    return {
        "authorization": auth,
        "repository_state": state,
        "path_model": path_model,
        "source_observations": source_observations,
        "authorization_input_file_sha256": sha256_hex(raw_bytes or canonical_json_bytes(payload)),
        "authorization_input_identity": dict(payload["authorization_input_identity"]),
    }


def _evidence_existence(path_model: Mapping[str, str]) -> dict[str, bool]:
    return {
        "result_directory_exists": Path(path_model["result_directory"]).exists(),
        "global_authority_entry_exists": Path(path_model["global_authority_entry_path"]).exists(),
        "local_gate_exists": Path(path_model["local_gate_path"]).exists(),
        "run_result_exists": Path(path_model["run_result_path"]).exists(),
        "retained_completion_exists": Path(path_model["retained_completion_path"]).exists(),
    }


def result_record(
    *,
    mode: str,
    terminal_label: str,
    authoritative: bool,
    retained_execution: bool,
    authority_consumed: bool,
    authorization_input_file_sha256: str | None,
    path_model: Mapping[str, str] | None,
    case_set_identity: str | None,
    a6_selected: bool,
    error_classification: str = "NONE",
    detail: str = "OK",
    repository_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": "torment.brainvision.blocker2.operator_wrapper.result.v0.1",
        "wrapper_version": WRAPPER_VERSION,
        "mode": mode,
        "terminal_label": terminal_label,
        "authoritative": authoritative,
        "retained_execution": retained_execution,
        "authority_consumed": authority_consumed,
        "repository_identity": dict(repository_identity or {}),
        "authorization_input_sha256": authorization_input_file_sha256 or "NOT_SUPPLIED",
        "path_identities": dict(path_model or {}),
        "real_executor_selector": REAL_EXECUTOR_SELECTOR,
        "case_set_identity": case_set_identity or "NOT_VALIDATED",
        "a6_selected": a6_selected,
        "evidence_object_existence": _evidence_existence(path_model or {}) if path_model else {},
        "error_classification": error_classification,
        "detail": detail,
    }


def prepare_paths(
    payload: Mapping[str, Any],
    *,
    raw_bytes: bytes | None = None,
    repo_root: str | Path | None = None,
    file_identity_provider: FileIdentityProvider | None = None,
    repository_state: retained.RepositoryState | None = None,
) -> dict[str, Any]:
    validated = validate_authorization_payload(
        payload,
        mode=PREPARE_PATHS,
        raw_bytes=raw_bytes,
        repo_root=repo_root,
        file_identity_provider=file_identity_provider,
        repository_state=repository_state,
    )
    for root in (AUTHORITY_REGISTRY_ROOT, FIXTURE_ROOT, RESULT_PARENT):
        if root.exists() and not root.is_dir():
            raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "fixed root is not directory")
        root.mkdir(parents=True, exist_ok=True)
    path_model = validated["path_model"]
    evidence = {
        "authority_registry_root": path_evidence(
            AUTHORITY_REGISTRY_ROOT,
            role="authority_registry_root",
            repo_root=repo_root,
        ),
        "fixture_root": path_evidence(FIXTURE_ROOT, role="fixture_root", repo_root=repo_root),
        "result_parent": path_evidence(RESULT_PARENT, role="result_parent", repo_root=repo_root),
        "result_directory_absent": not Path(path_model["result_directory"]).exists(),
        "global_authority_entry_absent": not Path(path_model["global_authority_entry_path"]).exists(),
    }
    if not evidence["result_directory_absent"]:
        raise WrapperValidationError(PREFLIGHT_REJECTED_UNCONSUMED, "result directory exists")
    if not evidence["global_authority_entry_absent"]:
        raise WrapperValidationError(AUTHORITY_ALREADY_CONSUMED, "global authority entry exists")
    record = result_record(
        mode=PREPARE_PATHS,
        terminal_label=PREPARATION_COMPLETE,
        authoritative=False,
        retained_execution=False,
        authority_consumed=False,
        authorization_input_file_sha256=validated["authorization_input_file_sha256"],
        path_model=path_model,
        case_set_identity=expected_runtime_identities()["case_set_sha256"],
        a6_selected=False,
        repository_identity=payload["repository_identity"],
    )
    record["path_preparation"] = evidence
    return record


def preflight_only(
    payload: Mapping[str, Any],
    *,
    raw_bytes: bytes | None = None,
    repo_root: str | Path | None = None,
    file_identity_provider: FileIdentityProvider | None = None,
    repository_state: retained.RepositoryState | None = None,
) -> dict[str, Any]:
    try:
        validated = validate_authorization_payload(
            payload,
            mode=PREFLIGHT_ONLY,
            raw_bytes=raw_bytes,
            repo_root=repo_root,
            file_identity_provider=file_identity_provider,
            repository_state=repository_state,
        )
        path_model = validated["path_model"]
        for key in (
            "result_directory",
            "global_authority_entry_path",
            "local_gate_path",
            "run_result_path",
            "retained_completion_path",
        ):
            if Path(path_model[key]).exists():
                raise WrapperValidationError(PREFLIGHT_REJECTED_UNCONSUMED, "%s exists" % key)
        retained.preflight_retained_authorization(
            validated["authorization"],
            repository_state=validated["repository_state"],
            source_observations=validated["source_observations"],
            repo_root=repo_root,
            require_case_executor=True,
        )
        return result_record(
            mode=PREFLIGHT_ONLY,
            terminal_label=PREFLIGHT_ACCEPTED_UNCONSUMED,
            authoritative=False,
            retained_execution=False,
            authority_consumed=False,
            authorization_input_file_sha256=validated["authorization_input_file_sha256"],
            path_model=path_model,
            case_set_identity=expected_runtime_identities()["case_set_sha256"],
            a6_selected=False,
            repository_identity=payload["repository_identity"],
        )
    except WrapperValidationError as exc:
        if exc.terminal_label == INVALID_AUTHORIZATION_INPUT:
            raise
        return result_record(
            mode=PREFLIGHT_ONLY,
            terminal_label=PREFLIGHT_REJECTED_UNCONSUMED,
            authoritative=False,
            retained_execution=False,
            authority_consumed=False,
            authorization_input_file_sha256=sha256_hex(raw_bytes or canonical_json_bytes(payload)),
            path_model=payload.get("path_model") if isinstance(payload.get("path_model"), dict) else None,
            case_set_identity=None,
            a6_selected=False,
            error_classification=exc.terminal_label,
            detail=exc.detail,
            repository_identity=payload.get("repository_identity") if isinstance(payload.get("repository_identity"), dict) else None,
        )
    except retained.RetainedValidationError as exc:
        return result_record(
            mode=PREFLIGHT_ONLY,
            terminal_label=PREFLIGHT_REJECTED_UNCONSUMED,
            authoritative=False,
            retained_execution=False,
            authority_consumed=False,
            authorization_input_file_sha256=sha256_hex(raw_bytes or canonical_json_bytes(payload)),
            path_model=payload.get("path_model") if isinstance(payload.get("path_model"), dict) else None,
            case_set_identity=None,
            a6_selected=False,
            error_classification="RETAINED_PREFLIGHT_REJECTED",
            detail=str(exc),
            repository_identity=payload.get("repository_identity") if isinstance(payload.get("repository_identity"), dict) else None,
        )


def execute_exact_single_run(
    payload: Mapping[str, Any],
    *,
    raw_bytes: bytes | None = None,
    repo_root: str | Path | None = None,
    file_identity_provider: FileIdentityProvider | None = None,
    repository_state: retained.RepositoryState | None = None,
    run_invoker: Callable[..., retained.RetainedRunResult] = retained.run_retained_single_run,
) -> dict[str, Any]:
    validated = validate_authorization_payload(
        payload,
        mode=EXECUTE_EXACT_SINGLE_RUN,
        raw_bytes=raw_bytes,
        repo_root=repo_root,
        file_identity_provider=file_identity_provider,
        repository_state=repository_state,
    )
    preflight_payload = with_computed_authorization_input_identity(
        {**payload, "wrapper_mode": PREFLIGHT_ONLY}
    )
    preflight = preflight_only(
        preflight_payload,
        raw_bytes=None,
        repo_root=repo_root,
        file_identity_provider=file_identity_provider,
        repository_state=repository_state,
    )
    if preflight["terminal_label"] != PREFLIGHT_ACCEPTED_UNCONSUMED:
        return preflight
    result = run_invoker(
        validated["authorization"],
        case_executor=retained.execute_existing_absolute_path_retained_case_set,
        repository_state=validated["repository_state"],
        source_observations=validated["source_observations"],
        repo_root=repo_root,
        fault_point=None,
    )
    if result.terminal_state == retained.RUN_COMPLETE and result.retained_execution is True:
        label = AUTHORITATIVE_RUN_COMPLETE
    elif result.primary_failure == retained.GLOBAL_AUTHORITY_ENTRY_EXISTS:
        label = AUTHORITY_ALREADY_CONSUMED
    elif result.terminal_state == retained.RUN_INTERRUPTED:
        label = AUTHORITATIVE_RUN_INTERRUPTED_CONSUMED
    else:
        label = AUTHORITATIVE_RUN_FAILED_CONSUMED
    return result_record(
        mode=EXECUTE_EXACT_SINGLE_RUN,
        terminal_label=label,
        authoritative=True,
        retained_execution=bool(result.retained_execution),
        authority_consumed=bool(result.global_authority_consumed),
        authorization_input_file_sha256=validated["authorization_input_file_sha256"],
        path_model=validated["path_model"],
        case_set_identity=expected_runtime_identities()["case_set_sha256"],
        a6_selected=False,
        error_classification=result.primary_failure or "NONE",
        detail=result.detail,
        repository_identity=payload["repository_identity"],
    )


def run_mode_from_file(
    mode: str,
    authorization_input: str | Path,
) -> dict[str, Any]:
    payload, raw = load_canonical_json_file(authorization_input)
    if mode == PREPARE_PATHS:
        return prepare_paths(payload, raw_bytes=raw)
    if mode == PREFLIGHT_ONLY:
        return preflight_only(payload, raw_bytes=raw)
    if mode == EXECUTE_EXACT_SINGLE_RUN:
        return execute_exact_single_run(payload, raw_bytes=raw)
    raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "unknown wrapper mode")


EXIT_CODES = {
    PREPARATION_COMPLETE: 0,
    PREFLIGHT_ACCEPTED_UNCONSUMED: 0,
    AUTHORITATIVE_RUN_COMPLETE: 0,
    INVALID_AUTHORIZATION_INPUT: 2,
    PREFLIGHT_REJECTED_UNCONSUMED: 2,
    AUTHORITATIVE_RUN_FAILED_CONSUMED: 3,
    AUTHORITATIVE_RUN_INTERRUPTED_CONSUMED: 3,
    AUTHORITY_ALREADY_CONSUMED: 3,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BLOCKER-2 authoritative retained single-run operator wrapper"
    )
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--authorization-input", required=True)
    parser.add_argument("--format", choices=("json", "human", "both"), default="json")
    return parser


def _print_record(record: Mapping[str, Any], output_format: str) -> None:
    if output_format in ("json", "both"):
        sys.stdout.write(canonical_json_bytes(record).decode("utf-8") + "\n")
    if output_format in ("human", "both"):
        sys.stdout.write("%s\n" % record["terminal_label"])


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        record = run_mode_from_file(args.mode, args.authorization_input)
    except WrapperValidationError as exc:
        record = result_record(
            mode=args.mode if args.mode in MODES else "INVALID",
            terminal_label=exc.terminal_label,
            authoritative=False,
            retained_execution=False,
            authority_consumed=False,
            authorization_input_file_sha256=None,
            path_model=None,
            case_set_identity=None,
            a6_selected=False,
            error_classification=exc.terminal_label,
            detail=exc.detail,
        )
    _print_record(record, args.format)
    return EXIT_CODES.get(str(record["terminal_label"]), 2)


if __name__ == "__main__":
    raise SystemExit(main())
