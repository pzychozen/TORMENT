"""Preparation harness for BLOCKER-2 retained absolute-path validation.

This module is intentionally narrower than the existing ephemeral A-matrix.  It
binds a consumed gate, a selected retained case set, source identities, and a
canonical terminal artifact, while refusing authoritative retained execution in
this implementation-preparation phase.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import ntpath
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence

import durable_evidence_schema_v0_3 as durable_schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter
import validate_windows_same_volume_no_replace_promotion_v0_1 as validation


RETAINED_MODE = "BLOCKER2_ABSOLUTE_PATH_CONTROL_RETAINED_SINGLE_RUN_V0_1"
RETAINED_PREPARATION_PHASE = "IMPLEMENTATION_PREPARATION_NON_AUTHORITATIVE"

RETAINED_AUTHORIZATION_INPUT_SCHEMA = (
    "torment.brainvision.blocker2.retained.authorization_input.v0.1"
)
RETAINED_CASE_SET_SCHEMA = "torment.brainvision.blocker2.retained.case_set.v0.1"
RETAINED_GATE_ENTRY_SCHEMA = "torment.brainvision.blocker2.retained.gate_entry.v0.1"
RETAINED_TERMINAL_RECORD_SCHEMA = (
    "torment.brainvision.blocker2.retained.terminal_record.v0.1"
)
RETAINED_TERMINAL_ARTIFACT_SCHEMA = (
    "torment.brainvision.blocker2.retained.terminal_artifact.v0.1"
)
RETAINED_REPOSITORY_STATE_SCHEMA = (
    "torment.brainvision.blocker2.retained.repository_state.v0.1"
)
RETAINED_SOURCE_IDENTITY_SCHEMA = (
    "torment.brainvision.blocker2.retained.source_identity.v0.1"
)
RETAINED_FIXTURE_PROFILE_SCHEMA = (
    "torment.brainvision.blocker2.retained.fixture_profile.v0.1"
)

GATE_ENTRY_FILENAME = "gate_entry.canonical.json"
TERMINAL_ARTIFACT_FILENAME = "terminal_artifact.canonical.json"

PREFLIGHT_REJECTED = "PREFLIGHT_REJECTED"
GATE_ENTRY_FAILED = "GATE_ENTRY_FAILED"
GATE_ENTERED = "GATE_ENTERED"
RUN_COMPLETE = "RUN_COMPLETE"
RUN_FAILED = "RUN_FAILED"
RUN_INTERRUPTED = "RUN_INTERRUPTED"
ARTIFACT_PERSISTENCE_FAILED = "ARTIFACT_PERSISTENCE_FAILED"
ARTIFACT_REVERIFY_FAILED = "ARTIFACT_REVERIFY_FAILED"

TERMINAL_STATES = frozenset(
    {
        PREFLIGHT_REJECTED,
        GATE_ENTRY_FAILED,
        GATE_ENTERED,
        RUN_COMPLETE,
        RUN_FAILED,
        RUN_INTERRUPTED,
        ARTIFACT_PERSISTENCE_FAILED,
        ARTIFACT_REVERIFY_FAILED,
    }
)

IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
POLICY_MISMATCH = "POLICY_MISMATCH"
REPOSITORY_STATE_INVALID = "REPOSITORY_STATE_INVALID"
SOURCE_STATE_MISMATCH = "SOURCE_STATE_MISMATCH"
WORKING_TREE_DIRTY_AUTHORIZED_SURFACE = (
    "WORKING_TREE_DIRTY_AUTHORIZED_SURFACE"
)
WORKING_TREE_DIRTY_UNRELATED_DISALLOWED = (
    "WORKING_TREE_DIRTY_UNRELATED_DISALLOWED"
)
RESULT_DIRECTORY_NOT_ABSENT = "RESULT_DIRECTORY_NOT_ABSENT"
RESULT_DIRECTORY_INSIDE_REPOSITORY = "RESULT_DIRECTORY_INSIDE_REPOSITORY"
RESULT_DIRECTORY_REPARSE_POINT = "RESULT_DIRECTORY_REPARSE_POINT"
RESULT_DIRECTORY_NOT_DRIVE_QUALIFIED = "RESULT_DIRECTORY_NOT_DRIVE_QUALIFIED"
FIXTURE_PROFILE_UNSUPPORTED = "FIXTURE_PROFILE_UNSUPPORTED"
CASE_SELECTION_REJECTED = "CASE_SELECTION_REJECTED"
CASE_OUTCOME_MISSING = "CASE_OUTCOME_MISSING"
CASE_OUTCOME_REJECTED = "CASE_OUTCOME_REJECTED"
NATIVE_INVOCATION_NOT_CONFIGURED = "NATIVE_INVOCATION_NOT_CONFIGURED"
GATE_ENTRY_WRITE_FAILURE = "GATE_ENTRY_WRITE_FAILURE"
GATE_ENTRY_REVERIFY_FAILURE = "GATE_ENTRY_REVERIFY_FAILURE"
TERMINAL_ARTIFACT_WRITE_FAILURE = "TERMINAL_ARTIFACT_WRITE_FAILURE"
TERMINAL_ARTIFACT_REVERIFY_FAILURE = "TERMINAL_ARTIFACT_REVERIFY_FAILURE"
FAULT_INJECTION_TRIGGERED = "FAULT_INJECTION_TRIGGERED"
AUTHORITATIVE_RUN_NOT_AUTHORIZED = "AUTHORITATIVE_RUN_NOT_AUTHORIZED"

FAILURE_CODES = frozenset(
    {
        IDENTITY_MISMATCH,
        POLICY_MISMATCH,
        REPOSITORY_STATE_INVALID,
        SOURCE_STATE_MISMATCH,
        WORKING_TREE_DIRTY_AUTHORIZED_SURFACE,
        WORKING_TREE_DIRTY_UNRELATED_DISALLOWED,
        RESULT_DIRECTORY_NOT_ABSENT,
        RESULT_DIRECTORY_INSIDE_REPOSITORY,
        RESULT_DIRECTORY_REPARSE_POINT,
        RESULT_DIRECTORY_NOT_DRIVE_QUALIFIED,
        FIXTURE_PROFILE_UNSUPPORTED,
        CASE_SELECTION_REJECTED,
        CASE_OUTCOME_MISSING,
        CASE_OUTCOME_REJECTED,
        NATIVE_INVOCATION_NOT_CONFIGURED,
        GATE_ENTRY_WRITE_FAILURE,
        GATE_ENTRY_REVERIFY_FAILURE,
        TERMINAL_ARTIFACT_WRITE_FAILURE,
        TERMINAL_ARTIFACT_REVERIFY_FAILURE,
        FAULT_INJECTION_TRIGGERED,
        AUTHORITATIVE_RUN_NOT_AUTHORIZED,
        validation.CONTROL_COLLISION_OBSERVED,
        validation.CONTROL_DESTINATION_REPLACED,
        validation.CONTROL_IDENTITY_MISMATCH,
        validation.CONTROL_CONTENT_MISMATCH,
        validation.CONTROL_NATIVE_ERROR_INDETERMINATE,
        validation.CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE,
        validation.CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL,
        validation.CONTROL_ACCESS_REJECTED,
        validation.CONTROL_SKIPPED_FIXTURE_UNAVAILABLE,
        validation.CONTROL_FIXTURE_INVALID,
        validation.NATIVE_RENAME_FAILED,
    }
)

A1 = "A1"
A2 = "A2"
A3 = "A3"
A4 = "A4"
A5 = "A5"
A6 = "A6"
A7 = "A7"
A8 = "A8"

A1_CASE_ID = "A1_POSITIVE_ABSOLUTE_PATH_RENAME"
A2_CASE_ID = "A2_EXISTING_DESTINATION_DIRECTORY"
A3_CASE_ID = "A3_EXISTING_DESTINATION_FILE"
A4_CASE_ID = "A4_COORDINATED_DESTINATION_CLAIM"
A5_CASE_ID = "A5_SOURCE_TO_FINAL_IDENTITY_CONTINUITY"
A6_CASE_ID = "A6_NATIVE_ERROR_CHARACTERIZATION"
A7_CASE_ID = "A7_INVALID_OR_ESCAPING_ABSOLUTE_DESTINATION_REJECTED"
A8_CASE_ID = "A8_SAME_VOLUME_MISMATCH_REJECTED"

CASE_SHORT_TO_ID = {
    A1: A1_CASE_ID,
    A2: A2_CASE_ID,
    A3: A3_CASE_ID,
    A4: A4_CASE_ID,
    A5: A5_CASE_ID,
    A6: A6_CASE_ID,
    A7: A7_CASE_ID,
    A8: A8_CASE_ID,
}
CASE_ID_TO_SHORT = {case_id: short for short, case_id in CASE_SHORT_TO_ID.items()}

COMPLETION_GATING_CASES = (A1, A2, A3, A5)
OPTIONAL_NON_GATING_CASES = (A6,)
REJECTED_RETAINED_CASES = (A4, A7, A8)
DEFAULT_RETAINED_CASES = COMPLETION_GATING_CASES
CASE_EXECUTION_ORDER = (A1, A2, A3, A5, A6)

ABSOLUTE_POLICY_SHA256 = "3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531"
ROOTDIRECTORY_RELATIVE_POLICY_SHA256 = (
    "df91a9bcc3c5b37e938a086801dd2bca42f0290533a6cf2682055df475f663f3"
)
UNAVAILABLE_UNTIL_COMMIT = "UNAVAILABLE_UNTIL_COMMIT"

AUTHORIZED_SURFACE_PATHS = frozenset(
    {
        "research/brainvision/blocker2_retained_absolute_path_control_v0_1.py",
        "research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py",
        (
            "research/brainvision/"
            "test_blocker2_retained_absolute_path_control_integration_v0_1.py"
        ),
        (
            "research/brainvision/"
            "validate_windows_same_volume_no_replace_promotion_v0_1.py"
        ),
        (
            "research/brainvision/"
            "test_validate_windows_same_volume_no_replace_promotion_v0_1.py"
        ),
        (
            "research/brainvision/"
            "test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py"
        ),
    }
)

AUTHORIZED_PREPARATION_DOCUMENTS = frozenset(
    {
        (
            "docs/"
            "TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_"
            "AUTHORITATIVE_RETAINED_SINGLE_RUN_ASSESSMENT_v0.1.md"
        ),
        (
            "docs/"
            "TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_"
            "RETAINED_SINGLE_RUN_IMPLEMENTATION_PREPARATION_AUTHORIZATION_v0.1.md"
        ),
    }
)

FAULT_BEFORE_GATE_WRITE = "before_gate_write"
FAULT_DURING_GATE_FILE_WRITE = "during_gate_file_write"
FAULT_DURING_GATE_DIRECTORY_SYNC = "during_gate_directory_sync"
FAULT_DURING_GATE_REREAD = "during_gate_reread"
FAULT_AFTER_VERIFIED_GATE_BEFORE_NATIVE = "after_verified_gate_before_native"
FAULT_DURING_TERMINAL_FILE_WRITE = "during_terminal_file_write"
FAULT_DURING_TERMINAL_DIRECTORY_SYNC = "during_terminal_directory_sync"
FAULT_DURING_TERMINAL_REREAD = "during_terminal_reread"

FAULT_POINTS = frozenset(
    {
        FAULT_BEFORE_GATE_WRITE,
        FAULT_DURING_GATE_FILE_WRITE,
        FAULT_DURING_GATE_DIRECTORY_SYNC,
        FAULT_DURING_GATE_REREAD,
        FAULT_AFTER_VERIFIED_GATE_BEFORE_NATIVE,
        FAULT_DURING_TERMINAL_FILE_WRITE,
        FAULT_DURING_TERMINAL_DIRECTORY_SYNC,
        FAULT_DURING_TERMINAL_REREAD,
    }
)

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
HEX40_OR_64_RE = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")

CaseExecutor = Callable[[Path, tuple[str, ...]], Sequence[validation.ValidationCaseResult]]


class RetainedValidationError(ValueError):
    """Raised when retained-run input violates the fail-closed schema."""


class ArtifactPersistenceError(RuntimeError):
    def __init__(self, failure_code: str, detail: str):
        super().__init__(detail)
        self.failure_code = failure_code
        self.detail = detail


@dataclass(frozen=True)
class RepositoryState:
    schema: str
    repo_root: str
    branch: str
    head: str
    origin_main: str
    status_lines: tuple[str, ...]
    dirty_authorized_surfaces: tuple[str, ...]
    dirty_unrelated_surfaces: tuple[str, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "repo_root": self.repo_root,
            "branch": self.branch,
            "head": self.head,
            "origin_main": self.origin_main,
            "status_lines": list(self.status_lines),
            "dirty_authorized_surfaces": list(self.dirty_authorized_surfaces),
            "dirty_unrelated_surfaces": list(self.dirty_unrelated_surfaces),
        }


@dataclass(frozen=True)
class SourceIdentity:
    schema: str
    relative_path: str
    checked_out_byte_sha256: str
    checked_out_byte_length: int
    git_blob_oid: str
    git_blob_state: str

    def as_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceIdentityExpectation:
    relative_path: str
    checked_out_byte_sha256: str
    checked_out_byte_length: int
    git_blob_oid: str = UNAVAILABLE_UNTIL_COMMIT


@dataclass(frozen=True)
class RetainedAuthorization:
    mode: str
    authorization_identity: str
    assessment_identity: str
    expected_branch: str
    expected_head: str
    expected_origin_main: str
    result_directory: Path
    fixture_root: Path
    selected_cases: tuple[str, ...] = DEFAULT_RETAINED_CASES
    optional_cases: tuple[str, ...] = ()
    authoritative: bool = False
    allow_unrelated_outside_surfaces: bool = False
    enforce_fixture_profile: bool = False

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema": RETAINED_AUTHORIZATION_INPUT_SCHEMA,
            "mode": self.mode,
            "authorization_identity": self.authorization_identity,
            "assessment_identity": self.assessment_identity,
            "expected_branch": self.expected_branch,
            "expected_head": self.expected_head,
            "expected_origin_main": self.expected_origin_main,
            "result_directory": str(self.result_directory),
            "fixture_root": str(self.fixture_root),
            "selected_cases": list(self.selected_cases),
            "optional_cases": list(self.optional_cases),
            "authoritative": self.authoritative,
            "allow_unrelated_outside_surfaces": (
                self.allow_unrelated_outside_surfaces
            ),
            "enforce_fixture_profile": self.enforce_fixture_profile,
        }


@dataclass(frozen=True)
class ImmutableArtifactWriteResult:
    path: str
    byte_length: int
    sha256: str
    directory_sync: dict[str, Any]
    reread_verified: bool
    hash_verified: bool

    def as_payload(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            "directory_sync": self.directory_sync,
            "reread_verified": self.reread_verified,
            "hash_verified": self.hash_verified,
        }


@dataclass(frozen=True)
class RetainedRunResult:
    terminal_state: str
    retained_execution: bool
    authoritative: bool
    gate_consumed: bool
    native_invocation_started: bool
    primary_failure: str | None
    detail: str
    result_directory: str
    gate_artifact: ImmutableArtifactWriteResult | None = None
    terminal_artifact: ImmutableArtifactWriteResult | None = None
    terminal_record: dict[str, Any] | None = None

    def as_payload(self) -> dict[str, Any]:
        payload = {
            "terminal_state": self.terminal_state,
            "retained_execution": self.retained_execution,
            "authoritative": self.authoritative,
            "gate_consumed": self.gate_consumed,
            "native_invocation_started": self.native_invocation_started,
            "primary_failure": self.primary_failure or "NONE",
            "detail": self.detail,
            "result_directory": self.result_directory,
            "gate_artifact": (
                self.gate_artifact.as_payload()
                if self.gate_artifact is not None
                else "NOT_WRITTEN"
            ),
            "terminal_artifact": (
                self.terminal_artifact.as_payload()
                if self.terminal_artifact is not None
                else "NOT_WRITTEN"
            ),
            "terminal_record": self.terminal_record or "NOT_WRITTEN",
        }
        return payload


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json_domain(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_canonical_json_bytes(payload: bytes) -> Any:
    try:
        decoded = payload.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RetainedValidationError("invalid canonical JSON bytes") from exc
    if canonical_json_bytes(value) != payload:
        raise RetainedValidationError("JSON bytes are not canonical")
    return value


def require_retained_mode(mode: str) -> str:
    if mode != RETAINED_MODE:
        raise RetainedValidationError("retained mode must be explicit")
    return mode


def retained_schema_declaration() -> dict[str, Any]:
    return {
        "schema": "torment.brainvision.blocker2.retained.schemas.v0.1",
        "authorization_input_schema": RETAINED_AUTHORIZATION_INPUT_SCHEMA,
        "case_set_schema": RETAINED_CASE_SET_SCHEMA,
        "gate_entry_schema": RETAINED_GATE_ENTRY_SCHEMA,
        "terminal_record_schema": RETAINED_TERMINAL_RECORD_SCHEMA,
        "terminal_artifact_schema": RETAINED_TERMINAL_ARTIFACT_SCHEMA,
        "repository_state_schema": RETAINED_REPOSITORY_STATE_SCHEMA,
        "source_identity_schema": RETAINED_SOURCE_IDENTITY_SCHEMA,
        "fixture_profile_schema": RETAINED_FIXTURE_PROFILE_SCHEMA,
        "terminal_states": sorted(TERMINAL_STATES),
        "failure_codes": sorted(FAILURE_CODES),
    }


def retained_schema_identity() -> dict[str, str]:
    return {
        "schema": retained_schema_declaration()["schema"],
        "schema_sha256": canonical_sha256(retained_schema_declaration()),
    }


def retained_case_set_declaration(
    *,
    selected_cases: Sequence[str] = DEFAULT_RETAINED_CASES,
    optional_cases: Sequence[str] = (),
) -> dict[str, Any]:
    canonical_cases = validate_case_selection(selected_cases, optional_cases)
    return {
        "schema": RETAINED_CASE_SET_SCHEMA,
        "case_id_map": {short: CASE_SHORT_TO_ID[short] for short in sorted(CASE_SHORT_TO_ID)},
        "completion_gating_cases": list(COMPLETION_GATING_CASES),
        "optional_non_gating_cases": list(optional_cases),
        "rejected_retained_cases": list(REJECTED_RETAINED_CASES),
        "selected_cases": list(canonical_cases),
        "native_execution_order": [
            case for case in CASE_EXECUTION_ORDER if case in canonical_cases
        ],
    }


def retained_case_set_identity(
    *,
    selected_cases: Sequence[str] = DEFAULT_RETAINED_CASES,
    optional_cases: Sequence[str] = (),
) -> dict[str, str]:
    declaration = retained_case_set_declaration(
        selected_cases=selected_cases,
        optional_cases=optional_cases,
    )
    return {
        "schema": RETAINED_CASE_SET_SCHEMA,
        "case_set_sha256": canonical_sha256(declaration),
    }


def fixture_profile_declaration() -> dict[str, Any]:
    return {
        "schema": RETAINED_FIXTURE_PROFILE_SCHEMA,
        "host_os_family": "Windows",
        "host_versions": ["Windows 10", "Windows 11"],
        "filesystem": "local fixed NTFS",
        "root_location": "outside repository",
        "root_reparse_policy": "root and existing ancestors are ordinary",
        "source_destination_relation": "same volume",
        "destination_path_form": "drive-qualified DOS absolute path",
        "native_primitive": "SetFileInformationByHandle/FileRenameInfo",
        "file_rename_info": {
            "ReplaceIfExists": False,
            "RootDirectory": "NULL",
            "FileName": "absolute destination path",
        },
        "rejected_path_forms": [
            "relative",
            "UNC",
            "device",
            "volume-guid",
            "rootdirectory-relative",
        ],
    }


def fixture_profile_identity() -> dict[str, str]:
    return {
        "schema": RETAINED_FIXTURE_PROFILE_SCHEMA,
        "fixture_profile_sha256": canonical_sha256(fixture_profile_declaration()),
    }


def validate_case_selection(
    selected_cases: Sequence[str],
    optional_cases: Sequence[str] = (),
) -> tuple[str, ...]:
    selected = tuple(selected_cases)
    optional = tuple(optional_cases)
    if len(set(selected)) != len(selected):
        raise RetainedValidationError("duplicate retained case selection")
    if len(set(optional)) != len(optional):
        raise RetainedValidationError("duplicate optional case selection")
    unknown = set(selected).union(optional) - set(CASE_SHORT_TO_ID)
    if unknown:
        raise RetainedValidationError("unknown retained case selection")
    if set(selected) != set(COMPLETION_GATING_CASES):
        raise RetainedValidationError("A1/A2/A3/A5 are the only gating cases")
    if set(optional) - set(OPTIONAL_NON_GATING_CASES):
        raise RetainedValidationError("only A6 may be selected as optional")
    if set(selected).intersection(REJECTED_RETAINED_CASES):
        raise RetainedValidationError("A4/A7/A8 are rejected for retained mode")
    if set(optional).intersection(COMPLETION_GATING_CASES):
        raise RetainedValidationError("gating cases must not be optional")
    if set(optional).intersection(REJECTED_RETAINED_CASES):
        raise RetainedValidationError("A4/A7/A8 are rejected for retained mode")
    if A6 in selected:
        raise RetainedValidationError("A6 is optional and non-gating only")
    ordered = [case for case in CASE_EXECUTION_ORDER if case in selected]
    ordered.extend(case for case in CASE_EXECUTION_ORDER if case in optional)
    return tuple(ordered)


def validate_policy_identity(policy_identity: Mapping[str, Any]) -> dict[str, str]:
    if policy_identity.get("policy_sha256") == ROOTDIRECTORY_RELATIVE_POLICY_SHA256:
        raise RetainedValidationError(
            "RootDirectory-relative policy identity is rejected"
        )
    required = {
        "policy_schema_identity": validation.ABSOLUTE_PATH_CONTROL_POLICY_SCHEMA,
        "policy_sha256": ABSOLUTE_POLICY_SHA256,
    }
    if set(policy_identity) != set(required):
        raise RetainedValidationError("absolute-path policy identity shape mismatch")
    if policy_identity.get("policy_schema_identity") != required["policy_schema_identity"]:
        raise RetainedValidationError("absolute-path policy schema mismatch")
    if policy_identity.get("policy_sha256") != ABSOLUTE_POLICY_SHA256:
        raise RetainedValidationError("absolute-path policy identity mismatch")
    return dict(policy_identity)


def authorized_absolute_path_control_policy_identity() -> dict[str, str]:
    return {
        "policy_schema_identity": validation.ABSOLUTE_PATH_CONTROL_POLICY_SCHEMA,
        "policy_sha256": ABSOLUTE_POLICY_SHA256,
    }


def repository_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def collect_repository_state(repo_root: str | Path | None = None) -> RepositoryState:
    root = Path(repo_root).resolve() if repo_root is not None else repository_root_from_here()
    branch = _git_text(root, "rev-parse", "--abbrev-ref", "HEAD")
    head = _git_text(root, "rev-parse", "HEAD")
    origin_main = _git_text(root, "rev-parse", "origin/main")
    status_lines = tuple(
        line
        for line in _git_text(
            root,
            "status",
            "--short",
            "--untracked-files=all",
        ).splitlines()
        if line.strip()
    )
    dirty_authorized, dirty_unrelated = classify_working_tree_status(status_lines)
    return RepositoryState(
        schema=RETAINED_REPOSITORY_STATE_SCHEMA,
        repo_root=str(root),
        branch=branch,
        head=head,
        origin_main=origin_main,
        status_lines=status_lines,
        dirty_authorized_surfaces=tuple(sorted(dirty_authorized)),
        dirty_unrelated_surfaces=tuple(sorted(dirty_unrelated)),
    )


def classify_working_tree_status(
    status_lines: Sequence[str],
    *,
    authorized_surfaces: set[str] | frozenset[str] = AUTHORIZED_SURFACE_PATHS,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    dirty_authorized: set[str] = set()
    dirty_unrelated: set[str] = set()
    for line in status_lines:
        for status_path in _status_line_paths(line):
            normalized = status_path.replace("\\", "/")
            if normalized in authorized_surfaces:
                dirty_authorized.add(normalized)
            else:
                dirty_unrelated.add(normalized)
    return tuple(sorted(dirty_authorized)), tuple(sorted(dirty_unrelated))


def source_identity_for_path(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> SourceIdentity:
    root = Path(repo_root).resolve() if repo_root is not None else repository_root_from_here()
    source = Path(path).resolve()
    if not _is_relative_to(source, root):
        raise RetainedValidationError("source path must be inside repository")
    relative_path = source.relative_to(root).as_posix()
    data = source.read_bytes()
    git_blob_oid = _git_blob_oid(root, relative_path)
    git_blob_state = (
        "RECORDED_FROM_GIT_INDEX"
        if git_blob_oid != UNAVAILABLE_UNTIL_COMMIT
        else UNAVAILABLE_UNTIL_COMMIT
    )
    return SourceIdentity(
        schema=RETAINED_SOURCE_IDENTITY_SCHEMA,
        relative_path=relative_path,
        checked_out_byte_sha256=hashlib.sha256(data).hexdigest(),
        checked_out_byte_length=len(data),
        git_blob_oid=git_blob_oid,
        git_blob_state=git_blob_state,
    )


def admit_repository_state(
    authorization: RetainedAuthorization,
    repository_state: RepositoryState,
) -> dict[str, Any]:
    repo_root = Path(repository_state.repo_root)
    index_lock_path = repo_root / ".git" / "index.lock"
    if index_lock_path.exists():
        raise RetainedValidationError(
            "%s: repository index lock is present" % REPOSITORY_STATE_INVALID
        )
    if repository_state.head != repository_state.origin_main:
        raise RetainedValidationError(
            "%s: observed HEAD and origin/main differ" % REPOSITORY_STATE_INVALID
        )
    if repository_state.branch != authorization.expected_branch:
        raise RetainedValidationError(
            "%s: repository branch mismatch" % REPOSITORY_STATE_INVALID
        )
    if repository_state.head != authorization.expected_head:
        raise RetainedValidationError(
            "%s: repository HEAD mismatch" % REPOSITORY_STATE_INVALID
        )
    if repository_state.origin_main != authorization.expected_origin_main:
        raise RetainedValidationError(
            "%s: repository origin/main mismatch" % REPOSITORY_STATE_INVALID
        )
    if repository_state.dirty_authorized_surfaces:
        raise RetainedValidationError(WORKING_TREE_DIRTY_AUTHORIZED_SURFACE)
    if (
        repository_state.dirty_unrelated_surfaces
        and not authorization.allow_unrelated_outside_surfaces
    ):
        raise RetainedValidationError(WORKING_TREE_DIRTY_UNRELATED_DISALLOWED)
    payload = repository_state.as_payload()
    payload["head_origin_main_equal"] = True
    payload["index_lock_absent"] = True
    return payload


def admit_source_identities(
    expectations: Sequence[SourceIdentityExpectation],
    observations: Mapping[str, SourceIdentity],
) -> list[dict[str, Any]]:
    admitted: list[dict[str, Any]] = []
    for expected in expectations:
        observed = observations.get(expected.relative_path)
        if observed is None:
            raise RetainedValidationError("missing source identity observation")
        if observed.checked_out_byte_sha256 != expected.checked_out_byte_sha256:
            raise RetainedValidationError("checked-out byte SHA-256 mismatch")
        if observed.checked_out_byte_length != expected.checked_out_byte_length:
            raise RetainedValidationError("checked-out byte length mismatch")
        if expected.git_blob_oid != UNAVAILABLE_UNTIL_COMMIT:
            if observed.git_blob_oid != expected.git_blob_oid:
                raise RetainedValidationError("Git blob identity mismatch")
        elif observed.git_blob_oid != UNAVAILABLE_UNTIL_COMMIT:
            raise RetainedValidationError(
                "precommit Git blob expectation cannot bind a committed blob"
            )
        admitted.append(observed.as_payload())
    return admitted


def preflight_retained_authorization(
    authorization: RetainedAuthorization,
    *,
    repository_state: RepositoryState | None = None,
    source_expectations: Sequence[SourceIdentityExpectation] = (),
    source_observations: Mapping[str, SourceIdentity] | None = None,
    repo_root: str | Path | None = None,
    require_case_executor: bool = True,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else repository_root_from_here()
    require_retained_mode(authorization.mode)
    _require_hex64(authorization.authorization_identity, "authorization_identity")
    _require_hex64(authorization.assessment_identity, "assessment_identity")
    _require_head_oid(authorization.expected_head, "expected_head")
    _require_head_oid(authorization.expected_origin_main, "expected_origin_main")
    validate_case_selection(authorization.selected_cases, authorization.optional_cases)
    validate_policy_identity(authorized_absolute_path_control_policy_identity())
    if authorization.authoritative:
        raise RetainedValidationError(AUTHORITATIVE_RUN_NOT_AUTHORIZED)
    if require_case_executor:
        case_executor_present = True
    else:
        raise RetainedValidationError(NATIVE_INVOCATION_NOT_CONFIGURED)
    observed_repository_state = repository_state or collect_repository_state(root)
    admitted_repository = admit_repository_state(authorization, observed_repository_state)
    result_dir = _resolve_for_absent_child(authorization.result_directory)
    fixture_root = _resolve_for_absent_child(authorization.fixture_root)
    _admit_drive_qualified_dos_path(result_dir)
    _admit_drive_qualified_dos_path(fixture_root)
    if _is_relative_to(result_dir, root):
        raise RetainedValidationError(RESULT_DIRECTORY_INSIDE_REPOSITORY)
    if _is_relative_to(fixture_root, root):
        raise RetainedValidationError("fixture root must be outside repository")
    if result_dir.exists():
        raise RetainedValidationError(RESULT_DIRECTORY_NOT_ABSENT)
    if result_dir.parent.exists() and _is_reparse_point(result_dir.parent):
        raise RetainedValidationError(RESULT_DIRECTORY_REPARSE_POINT)
    if fixture_root.exists() and _is_reparse_point(fixture_root):
        raise RetainedValidationError(FIXTURE_PROFILE_UNSUPPORTED)
    admitted_sources = admit_source_identities(
        source_expectations,
        source_observations or {},
    )
    return {
        "schema": "torment.brainvision.blocker2.retained.preflight.v0.1",
        "authorization": authorization.as_payload(),
        "policy_identity": validate_policy_identity(
            authorized_absolute_path_control_policy_identity()
        ),
        "case_set_identity": retained_case_set_identity(
            selected_cases=authorization.selected_cases,
            optional_cases=authorization.optional_cases,
        ),
        "fixture_profile_identity": fixture_profile_identity(),
        "repository_state": admitted_repository,
        "source_identities": admitted_sources,
        "case_executor_present": case_executor_present,
        "preparation_phase": RETAINED_PREPARATION_PHASE,
    }


def run_retained_single_run(
    authorization: RetainedAuthorization,
    *,
    case_executor: CaseExecutor | None,
    repository_state: RepositoryState | None = None,
    source_expectations: Sequence[SourceIdentityExpectation] = (),
    source_observations: Mapping[str, SourceIdentity] | None = None,
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None = None,
    repo_root: str | Path | None = None,
    fault_point: str | None = None,
) -> RetainedRunResult:
    if fault_point is not None and fault_point not in FAULT_POINTS:
        raise RetainedValidationError("unknown retained fault point")
    adapter = durability_adapter or _default_durability_adapter()
    result_dir = _resolve_for_absent_child(authorization.result_directory)
    try:
        preflight = preflight_retained_authorization(
            authorization,
            repository_state=repository_state,
            source_expectations=source_expectations,
            source_observations=source_observations,
            repo_root=repo_root,
            require_case_executor=case_executor is not None,
        )
    except RetainedValidationError as exc:
        return _run_result(
            terminal_state=PREFLIGHT_REJECTED,
            authorization=authorization,
            result_directory=result_dir,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=_failure_from_exception(exc),
            detail=str(exc),
        )
    case_order = validate_case_selection(
        authorization.selected_cases,
        authorization.optional_cases,
    )
    if fault_point == FAULT_BEFORE_GATE_WRITE:
        return _run_result(
            terminal_state=GATE_ENTRY_FAILED,
            authorization=authorization,
            result_directory=result_dir,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=FAULT_INJECTION_TRIGGERED,
            detail="fault injected before durable gate entry write",
        )
    try:
        _admit_result_directory_for_creation(result_dir)
        result_dir.mkdir()
        gate_record = build_gate_entry_record(
            authorization=authorization,
            preflight=preflight,
        )
        validate_gate_entry_record(gate_record)
        gate_artifact = _write_canonical_file(
            result_dir / GATE_ENTRY_FILENAME,
            gate_record,
            adapter=adapter,
            fault_point=fault_point,
            fault_file_write=FAULT_DURING_GATE_FILE_WRITE,
            fault_directory_sync=FAULT_DURING_GATE_DIRECTORY_SYNC,
            fault_reread=FAULT_DURING_GATE_REREAD,
        )
        validate_gate_artifact(result_dir / GATE_ENTRY_FILENAME)
    except ArtifactPersistenceError as exc:
        return _run_result(
            terminal_state=GATE_ENTRY_FAILED,
            authorization=authorization,
            result_directory=result_dir,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=exc.failure_code,
            detail=exc.detail,
        )
    except (OSError, RetainedValidationError) as exc:
        return _run_result(
            terminal_state=GATE_ENTRY_FAILED,
            authorization=authorization,
            result_directory=result_dir,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=GATE_ENTRY_WRITE_FAILURE,
            detail=str(exc),
        )
    if fault_point == FAULT_AFTER_VERIFIED_GATE_BEFORE_NATIVE:
        return _terminalized_result(
            authorization=authorization,
            result_directory=result_dir,
            adapter=adapter,
            gate_artifact=gate_artifact,
            terminal_state=RUN_FAILED,
            gate_consumed=True,
            native_invocation_started=False,
            primary_failure=FAULT_INJECTION_TRIGGERED,
            detail="fault injected after verified durable gate before native call",
            case_outcomes=empty_case_outcomes(case_order),
            fault_point=fault_point,
        )
    try:
        assert case_executor is not None
        native_invocation_started = True
        case_results = tuple(case_executor(authorization.fixture_root, case_order))
        case_outcomes = evaluate_case_results(
            case_results,
            optional_cases=authorization.optional_cases,
        )
        terminal_state = RUN_COMPLETE if case_outcomes["gating_satisfied"] else RUN_FAILED
        primary_failure = (
            "NONE"
            if case_outcomes["gating_satisfied"]
            else CASE_OUTCOME_REJECTED
        )
        detail = (
            "retained case set completed in non-authoritative preparation mode"
            if case_outcomes["gating_satisfied"]
            else "retained case set did not satisfy all gating outcomes"
        )
    except KeyboardInterrupt:
        return _terminalized_result(
            authorization=authorization,
            result_directory=result_dir,
            adapter=adapter,
            gate_artifact=gate_artifact,
            terminal_state=RUN_INTERRUPTED,
            gate_consumed=True,
            native_invocation_started=True,
            primary_failure=RUN_INTERRUPTED,
            detail="KeyboardInterrupt observed after gate consumption",
            case_outcomes=empty_case_outcomes(case_order),
            fault_point=fault_point,
        )
    except Exception as exc:
        return _terminalized_result(
            authorization=authorization,
            result_directory=result_dir,
            adapter=adapter,
            gate_artifact=gate_artifact,
            terminal_state=RUN_FAILED,
            gate_consumed=True,
            native_invocation_started=True,
            primary_failure=CASE_OUTCOME_REJECTED,
            detail="case executor raised %s" % type(exc).__name__,
            case_outcomes=empty_case_outcomes(case_order),
            fault_point=fault_point,
        )
    return _terminalized_result(
        authorization=authorization,
        result_directory=result_dir,
        adapter=adapter,
        gate_artifact=gate_artifact,
        terminal_state=terminal_state,
        gate_consumed=True,
        native_invocation_started=native_invocation_started,
        primary_failure=primary_failure,
        detail=detail,
        case_outcomes=case_outcomes,
        fault_point=fault_point,
    )


def execute_existing_absolute_path_retained_case_set(
    fixture_root: str | Path,
    selected_cases: Sequence[str] = DEFAULT_RETAINED_CASES,
    optional_cases: Sequence[str] = (),
) -> tuple[validation.ValidationCaseResult, ...]:
    case_order = validate_case_selection(selected_cases, optional_cases)
    root = Path(fixture_root)
    results: list[validation.ValidationCaseResult] = []
    for case in case_order:
        if case == A1:
            results.append(validation.validate_a1_absolute_path_positive(root))
        elif case == A2:
            results.append(
                validation.validate_a2_existing_destination_directory_absolute_path(root)
            )
        elif case == A3:
            results.append(
                validation.validate_a3_existing_destination_file_absolute_path(root)
            )
        elif case == A5:
            results.append(
                validation.validate_a5_absolute_path_identity_continuity(root)
            )
        elif case == A6:
            results.append(
                validation.validate_a6_absolute_path_native_error_characterization(root)
            )
        else:
            raise RetainedValidationError("case is not admitted for retained execution")
    return tuple(results)


def evaluate_case_results(
    case_results: Sequence[validation.ValidationCaseResult],
    *,
    optional_cases: Sequence[str] = (),
) -> dict[str, Any]:
    expected = validate_case_selection(COMPLETION_GATING_CASES, optional_cases)
    result_by_short: dict[str, validation.ValidationCaseResult] = {}
    for result in case_results:
        short = CASE_ID_TO_SHORT.get(result.case_id)
        if short is None:
            raise RetainedValidationError("unknown result case id")
        if short in result_by_short:
            raise RetainedValidationError("duplicate result case id")
        if short in REJECTED_RETAINED_CASES:
            raise RetainedValidationError("rejected case appeared in retained result")
        result_by_short[short] = result
    missing = [case for case in COMPLETION_GATING_CASES if case not in result_by_short]
    if missing:
        raise RetainedValidationError(CASE_OUTCOME_MISSING)
    gating_satisfied_by_case = {
        case: _case_result_is_satisfied(case, result_by_short[case])
        for case in COMPLETION_GATING_CASES
    }
    optional_outcomes = {
        case: _optional_case_summary(result_by_short[case])
        for case in optional_cases
        if case in result_by_short
    }
    return {
        "schema": "torment.brainvision.blocker2.retained.case_outcomes.v0.1",
        "selected_cases": [CASE_SHORT_TO_ID[case] for case in expected],
        "selected_cases_short": list(expected),
        "completion_gating_cases": list(COMPLETION_GATING_CASES),
        "optional_non_gating_cases": list(optional_cases),
        "gating_satisfied_by_case": gating_satisfied_by_case,
        "gating_satisfied": all(gating_satisfied_by_case.values()),
        "optional_outcomes": optional_outcomes,
        "case_results": [
            _case_result_payload(result_by_short[case])
            for case in expected
            if case in result_by_short
        ],
    }


def empty_case_outcomes(case_order: Sequence[str]) -> dict[str, Any]:
    return {
        "schema": "torment.brainvision.blocker2.retained.case_outcomes.v0.1",
        "selected_cases": [CASE_SHORT_TO_ID[case] for case in case_order],
        "selected_cases_short": list(case_order),
        "completion_gating_cases": list(COMPLETION_GATING_CASES),
        "optional_non_gating_cases": [
            case for case in case_order if case in OPTIONAL_NON_GATING_CASES
        ],
        "gating_satisfied_by_case": {
            case: False for case in COMPLETION_GATING_CASES
        },
        "gating_satisfied": False,
        "optional_outcomes": {},
        "case_results": [],
    }


def build_gate_entry_record(
    *,
    authorization: RetainedAuthorization,
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": RETAINED_GATE_ENTRY_SCHEMA,
        "authorization_identity": authorization.authorization_identity,
        "assessment_identity": authorization.assessment_identity,
        "mode": authorization.mode,
        "control_mode": validation.ABSOLUTE_PATH_CONTROL_MODE,
        "policy_identity": validate_policy_identity(
            authorized_absolute_path_control_policy_identity()
        ),
        "case_set_identity": retained_case_set_identity(
            selected_cases=authorization.selected_cases,
            optional_cases=authorization.optional_cases,
        ),
        "fixture_profile_identity": fixture_profile_identity(),
        "preflight_sha256": canonical_sha256(dict(preflight)),
        "gate_consumed": True,
        "native_invocation_started": False,
        "retained_execution": False,
        "terminal_state": GATE_ENTERED,
        "preparation_phase": RETAINED_PREPARATION_PHASE,
    }


def validate_gate_entry_record(record: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "authorization_identity",
        "assessment_identity",
        "mode",
        "control_mode",
        "policy_identity",
        "case_set_identity",
        "fixture_profile_identity",
        "preflight_sha256",
        "gate_consumed",
        "native_invocation_started",
        "retained_execution",
        "terminal_state",
        "preparation_phase",
    }
    if set(record) != required:
        raise RetainedValidationError("gate entry has unexpected schema fields")
    if record["schema"] != RETAINED_GATE_ENTRY_SCHEMA:
        raise RetainedValidationError("gate entry schema mismatch")
    require_retained_mode(str(record["mode"]))
    if record["control_mode"] != validation.ABSOLUTE_PATH_CONTROL_MODE:
        raise RetainedValidationError("gate entry control mode mismatch")
    validate_policy_identity(record["policy_identity"])
    _require_hex64(str(record["authorization_identity"]), "authorization_identity")
    _require_hex64(str(record["assessment_identity"]), "assessment_identity")
    _require_hex64(str(record["preflight_sha256"]), "preflight_sha256")
    if record["gate_consumed"] is not True:
        raise RetainedValidationError("gate entry must be consumed")
    if record["native_invocation_started"] is not False:
        raise RetainedValidationError("native invocation cannot precede gate entry")
    if record["retained_execution"] is not False:
        raise RetainedValidationError("gate entry cannot claim retained execution")
    if record["terminal_state"] != GATE_ENTERED:
        raise RetainedValidationError("gate entry terminal state mismatch")


def validate_gate_artifact(path: str | Path) -> dict[str, Any]:
    payload = Path(path).read_bytes()
    record = load_canonical_json_bytes(payload)
    validate_gate_entry_record(record)
    return record


def build_terminal_record(
    *,
    authorization: RetainedAuthorization,
    terminal_state: str,
    gate_consumed: bool,
    native_invocation_started: bool,
    retained_execution: bool,
    primary_failure: str,
    detail: str,
    case_outcomes: Mapping[str, Any],
    gate_artifact: ImmutableArtifactWriteResult | None,
    artifact_state: Mapping[str, Any],
    fault_point: str | None = None,
) -> dict[str, Any]:
    return {
        "schema": RETAINED_TERMINAL_RECORD_SCHEMA,
        "authorization_identity": authorization.authorization_identity,
        "assessment_identity": authorization.assessment_identity,
        "mode": authorization.mode,
        "control_mode": validation.ABSOLUTE_PATH_CONTROL_MODE,
        "authoritative": authorization.authoritative,
        "preparation_phase": RETAINED_PREPARATION_PHASE,
        "policy_identity": validate_policy_identity(
            authorized_absolute_path_control_policy_identity()
        ),
        "case_set_identity": retained_case_set_identity(
            selected_cases=authorization.selected_cases,
            optional_cases=authorization.optional_cases,
        ),
        "fixture_profile_identity": fixture_profile_identity(),
        "native_boundary": native_boundary_declaration(),
        "gate_state": {
            "consumed": gate_consumed,
            "gate_record_sha256": gate_artifact.sha256
            if gate_artifact is not None
            else "NOT_WRITTEN",
            "gate_record_byte_length": gate_artifact.byte_length
            if gate_artifact is not None
            else 0,
        },
        "native_invocation_started": native_invocation_started,
        "case_outcomes": dict(case_outcomes),
        "artifact_state": dict(artifact_state),
        "fault_injection": {
            "active": fault_point is not None,
            "fault_point": fault_point or "NONE",
            "authoritative": False,
        },
        "primary_failure": primary_failure,
        "detail": detail,
        "terminal_state": terminal_state,
        "retained_execution": retained_execution,
    }


def validate_terminal_record(record: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "authorization_identity",
        "assessment_identity",
        "mode",
        "control_mode",
        "authoritative",
        "preparation_phase",
        "policy_identity",
        "case_set_identity",
        "fixture_profile_identity",
        "native_boundary",
        "gate_state",
        "native_invocation_started",
        "case_outcomes",
        "artifact_state",
        "fault_injection",
        "primary_failure",
        "detail",
        "terminal_state",
        "retained_execution",
    }
    if set(record) != required:
        raise RetainedValidationError("terminal record has unexpected schema fields")
    if record["schema"] != RETAINED_TERMINAL_RECORD_SCHEMA:
        raise RetainedValidationError("terminal schema mismatch")
    require_retained_mode(str(record["mode"]))
    if record["control_mode"] != validation.ABSOLUTE_PATH_CONTROL_MODE:
        raise RetainedValidationError("terminal control mode mismatch")
    validate_policy_identity(record["policy_identity"])
    _require_hex64(str(record["authorization_identity"]), "authorization_identity")
    _require_hex64(str(record["assessment_identity"]), "assessment_identity")
    terminal_state = record["terminal_state"]
    if terminal_state not in TERMINAL_STATES:
        raise RetainedValidationError("unknown terminal state")
    if not isinstance(record["native_invocation_started"], bool):
        raise RetainedValidationError("native invocation flag must be boolean")
    if not isinstance(record["retained_execution"], bool):
        raise RetainedValidationError("retained execution flag must be boolean")
    if not isinstance(record["authoritative"], bool):
        raise RetainedValidationError("authoritative flag must be boolean")
    gate_state = _require_mapping(record["gate_state"], "gate_state")
    if gate_state.get("consumed") is False and record["native_invocation_started"]:
        raise RetainedValidationError("native invocation cannot start before gate")
    case_outcomes = _require_mapping(record["case_outcomes"], "case_outcomes")
    _validate_terminal_case_outcomes(case_outcomes)
    artifact_state = _require_mapping(record["artifact_state"], "artifact_state")
    fault_injection = _require_mapping(record["fault_injection"], "fault_injection")
    if terminal_state == RUN_COMPLETE and not case_outcomes.get("gating_satisfied"):
        raise RetainedValidationError("RUN_COMPLETE requires satisfied gating cases")
    if record["retained_execution"]:
        if record["authoritative"] is not True:
            raise RetainedValidationError("retained execution requires authority")
        if terminal_state != RUN_COMPLETE:
            raise RetainedValidationError("retained execution requires RUN_COMPLETE")
        if gate_state.get("consumed") is not True:
            raise RetainedValidationError("retained execution requires consumed gate")
        if record["native_invocation_started"] is not True:
            raise RetainedValidationError("retained execution requires native call")
        if fault_injection.get("active") is not False:
            raise RetainedValidationError("fault injection cannot be authoritative")
        for key in (
            "terminal_record_serialized",
            "terminal_artifact_written",
            "file_flush_completed",
            "directory_entry_durability_completed",
            "reread_verified",
            "hash_verified",
        ):
            if artifact_state.get(key) is not True:
                raise RetainedValidationError(
                    "retained execution requires admitted terminal artifact"
                )


def build_artifact_wrapper(terminal_record: Mapping[str, Any]) -> dict[str, Any]:
    validate_terminal_record(terminal_record)
    record_bytes = canonical_json_bytes(dict(terminal_record))
    return {
        "schema": RETAINED_TERMINAL_ARTIFACT_SCHEMA,
        "terminal_record": dict(terminal_record),
        "terminal_record_byte_length": len(record_bytes),
        "terminal_record_sha256": hashlib.sha256(record_bytes).hexdigest(),
    }


def validate_terminal_artifact(path: str | Path) -> dict[str, Any]:
    payload = Path(path).read_bytes()
    wrapper = load_canonical_json_bytes(payload)
    required = {
        "schema",
        "terminal_record",
        "terminal_record_byte_length",
        "terminal_record_sha256",
    }
    if set(wrapper) != required:
        raise RetainedValidationError("terminal artifact has unexpected fields")
    if wrapper["schema"] != RETAINED_TERMINAL_ARTIFACT_SCHEMA:
        raise RetainedValidationError("terminal artifact schema mismatch")
    terminal_record = _require_mapping(wrapper["terminal_record"], "terminal_record")
    validate_terminal_record(terminal_record)
    terminal_bytes = canonical_json_bytes(terminal_record)
    if wrapper["terminal_record_byte_length"] != len(terminal_bytes):
        raise RetainedValidationError("terminal record byte length mismatch")
    if wrapper["terminal_record_sha256"] != hashlib.sha256(terminal_bytes).hexdigest():
        raise RetainedValidationError("terminal record SHA-256 mismatch")
    return wrapper


def pending_artifact_state() -> dict[str, Any]:
    return {
        "terminal_record_serialized": True,
        "terminal_artifact_written": False,
        "file_flush_completed": False,
        "directory_entry_durability_completed": False,
        "reread_verified": False,
        "hash_verified": False,
        "external_wrapper_sha256_recorded": False,
    }


def completed_artifact_state() -> dict[str, Any]:
    return {
        "terminal_record_serialized": True,
        "terminal_artifact_written": True,
        "file_flush_completed": True,
        "directory_entry_durability_completed": True,
        "reread_verified": True,
        "hash_verified": True,
        "external_wrapper_sha256_recorded": True,
    }


def native_boundary_declaration() -> dict[str, Any]:
    return {
        "primitive": "SetFileInformationByHandle",
        "information_class": "FileRenameInfo",
        "file_rename_info": {
            "ReplaceIfExists": False,
            "RootDirectory": "NULL",
            "FileName": "drive-qualified DOS absolute path",
        },
        "excluded_primitives": ["MoveFileExW", "ReplaceFileW", "RootDirectory-relative"],
    }


def synthetic_clean_repository_state(
    *,
    repo_root: str | Path = "C:/synthetic/repo",
    branch: str = "main",
    head: str = "0" * 40,
    origin_main: str = "0" * 40,
) -> RepositoryState:
    return RepositoryState(
        schema=RETAINED_REPOSITORY_STATE_SCHEMA,
        repo_root=str(repo_root),
        branch=branch,
        head=head,
        origin_main=origin_main,
        status_lines=(),
        dirty_authorized_surfaces=(),
        dirty_unrelated_surfaces=(),
    )


def synthetic_source_identity(
    relative_path: str,
    *,
    content: bytes = b"synthetic retained preparation source\n",
    git_blob_oid: str = UNAVAILABLE_UNTIL_COMMIT,
) -> SourceIdentity:
    return SourceIdentity(
        schema=RETAINED_SOURCE_IDENTITY_SCHEMA,
        relative_path=relative_path.replace("\\", "/"),
        checked_out_byte_sha256=hashlib.sha256(content).hexdigest(),
        checked_out_byte_length=len(content),
        git_blob_oid=git_blob_oid,
        git_blob_state=UNAVAILABLE_UNTIL_COMMIT
        if git_blob_oid == UNAVAILABLE_UNTIL_COMMIT
        else "RECORDED_FROM_GIT_INDEX",
    )


def _terminalized_result(
    *,
    authorization: RetainedAuthorization,
    result_directory: Path,
    adapter: windows_adapter.WindowsDurabilityAdapter,
    gate_artifact: ImmutableArtifactWriteResult,
    terminal_state: str,
    gate_consumed: bool,
    native_invocation_started: bool,
    primary_failure: str,
    detail: str,
    case_outcomes: Mapping[str, Any],
    fault_point: str | None,
) -> RetainedRunResult:
    retained_execution = False
    terminal_record = build_terminal_record(
        authorization=authorization,
        terminal_state=terminal_state,
        gate_consumed=gate_consumed,
        native_invocation_started=native_invocation_started,
        retained_execution=retained_execution,
        primary_failure=primary_failure,
        detail=detail,
        case_outcomes=case_outcomes,
        gate_artifact=gate_artifact,
        artifact_state=pending_artifact_state(),
        fault_point=fault_point,
    )
    validate_terminal_record(terminal_record)
    try:
        wrapper = build_artifact_wrapper(terminal_record)
        terminal_artifact = _write_canonical_file(
            result_directory / TERMINAL_ARTIFACT_FILENAME,
            wrapper,
            adapter=adapter,
            fault_point=fault_point,
            fault_file_write=FAULT_DURING_TERMINAL_FILE_WRITE,
            fault_directory_sync=FAULT_DURING_TERMINAL_DIRECTORY_SYNC,
            fault_reread=FAULT_DURING_TERMINAL_REREAD,
        )
        validate_terminal_artifact(result_directory / TERMINAL_ARTIFACT_FILENAME)
    except ArtifactPersistenceError as exc:
        return _run_result(
            terminal_state=ARTIFACT_PERSISTENCE_FAILED
            if exc.failure_code == TERMINAL_ARTIFACT_WRITE_FAILURE
            else ARTIFACT_REVERIFY_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=exc.failure_code,
            detail=exc.detail,
            gate_artifact=gate_artifact,
            terminal_record=terminal_record,
        )
    except RetainedValidationError as exc:
        return _run_result(
            terminal_state=ARTIFACT_REVERIFY_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=TERMINAL_ARTIFACT_REVERIFY_FAILURE,
            detail=str(exc),
            gate_artifact=gate_artifact,
            terminal_record=terminal_record,
        )
    return _run_result(
        terminal_state=terminal_state,
        authorization=authorization,
        result_directory=result_directory,
        gate_consumed=gate_consumed,
        native_invocation_started=native_invocation_started,
        primary_failure=primary_failure,
        detail=detail,
        gate_artifact=gate_artifact,
        terminal_artifact=terminal_artifact,
        terminal_record=terminal_record,
    )


def _write_canonical_file(
    path: Path,
    value: Mapping[str, Any],
    *,
    adapter: windows_adapter.WindowsDurabilityAdapter,
    fault_point: str | None,
    fault_file_write: str,
    fault_directory_sync: str,
    fault_reread: str,
) -> ImmutableArtifactWriteResult:
    if fault_point == fault_file_write:
        raise ArtifactPersistenceError(
            _write_failure_code_for(path),
            "fault injected during immutable file write",
        )
    payload = canonical_json_bytes(dict(value))
    try:
        with open(path, "xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise ArtifactPersistenceError(
            _write_failure_code_for(path),
            "immutable file write failed: %s" % type(exc).__name__,
        ) from exc
    if fault_point == fault_directory_sync:
        raise ArtifactPersistenceError(
            _write_failure_code_for(path),
            "fault injected during directory-entry durability sync",
        )
    directory_sync = adapter.sync_directory_entry(
        str(path.parent),
        context=windows_adapter.DirectoryDurabilityContext(
            target_role=durable_schema.ARTIFACT_PARENT_DIRECTORY
        ),
    )
    directory_payload = _durability_result_payload(directory_sync)
    if directory_sync.status != durable_schema.DIRECTORY_DURABILITY_CONFIRMED:
        raise ArtifactPersistenceError(
            _write_failure_code_for(path),
            "directory-entry durability was not confirmed: %s"
            % directory_sync.status,
        )
    if fault_point == fault_reread:
        raise ArtifactPersistenceError(
            _reread_failure_code_for(path),
            "fault injected during immutable artifact reread",
        )
    reread = path.read_bytes()
    if reread != payload:
        raise ArtifactPersistenceError(
            _reread_failure_code_for(path),
            "immutable artifact reread bytes differ",
        )
    digest = hashlib.sha256(reread).hexdigest()
    if digest != hashlib.sha256(payload).hexdigest():
        raise ArtifactPersistenceError(
            _reread_failure_code_for(path),
            "immutable artifact digest reverify failed",
        )
    return ImmutableArtifactWriteResult(
        path=str(path),
        byte_length=len(payload),
        sha256=digest,
        directory_sync=directory_payload,
        reread_verified=True,
        hash_verified=True,
    )


def _run_result(
    *,
    terminal_state: str,
    authorization: RetainedAuthorization,
    result_directory: Path,
    gate_consumed: bool,
    native_invocation_started: bool,
    primary_failure: str | None,
    detail: str,
    gate_artifact: ImmutableArtifactWriteResult | None = None,
    terminal_artifact: ImmutableArtifactWriteResult | None = None,
    terminal_record: dict[str, Any] | None = None,
) -> RetainedRunResult:
    if terminal_state not in TERMINAL_STATES:
        raise RetainedValidationError("unknown terminal state")
    return RetainedRunResult(
        terminal_state=terminal_state,
        retained_execution=False,
        authoritative=authorization.authoritative,
        gate_consumed=gate_consumed,
        native_invocation_started=native_invocation_started,
        primary_failure=primary_failure,
        detail=detail,
        result_directory=str(result_directory),
        gate_artifact=gate_artifact,
        terminal_artifact=terminal_artifact,
        terminal_record=terminal_record,
    )


def _case_result_is_satisfied(
    short_case: str,
    result: validation.ValidationCaseResult,
) -> bool:
    if short_case in {A1, A5}:
        return _positive_identity_case_satisfied(result)
    if short_case in {A2, A3}:
        return _collision_case_satisfied(result)
    raise RetainedValidationError("case is not a completion-gating case")


def _positive_identity_case_satisfied(result: validation.ValidationCaseResult) -> bool:
    if not _case_policy_is_authorized(result):
        return False
    if result.status != validation.CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE:
        return False
    identities = (
        result.source_identity_before,
        result.retained_handle_identity_after,
        result.final_identity_after,
    )
    if any(identity is None for identity in identities):
        return False
    if not (identities[0] == identities[1] == identities[2]):
        return False
    if result.manifest_before_sha256 is None or result.manifest_after_sha256 is None:
        return False
    return result.manifest_before_sha256 == result.manifest_after_sha256


def _collision_case_satisfied(result: validation.ValidationCaseResult) -> bool:
    if not _case_policy_is_authorized(result):
        return False
    if result.status != validation.CONTROL_COLLISION_OBSERVED:
        return False
    if result.native_error_code != validation.ERROR_ALREADY_EXISTS:
        return False
    if result.native_error_name != validation.ERROR_NAMES[validation.ERROR_ALREADY_EXISTS]:
        return False
    if result.source_exists_after_native_failure is not True:
        return False
    if result.final_exists_after_native_failure is not True:
        return False
    return True


def _case_policy_is_authorized(result: validation.ValidationCaseResult) -> bool:
    try:
        validate_policy_identity(result.policy_identity or {})
    except RetainedValidationError:
        return False
    return True


def _optional_case_summary(result: validation.ValidationCaseResult) -> dict[str, Any]:
    return {
        "case_id": result.case_id,
        "status": result.status,
        "native_error_code": result.native_error_code
        if result.native_error_code is not None
        else "NOT_RECORDED",
        "native_error_name": result.native_error_name or "NOT_RECORDED",
        "gating": False,
    }


def _case_result_payload(result: validation.ValidationCaseResult) -> dict[str, Any]:
    return _strip_none(result.as_payload())


def _strip_none(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_none(inner)
            for key, inner in value.items()
            if inner is not None
        }
    if isinstance(value, tuple):
        return [_strip_none(item) for item in value]
    if isinstance(value, list):
        return [_strip_none(item) for item in value]
    return value


def _validate_terminal_case_outcomes(case_outcomes: Mapping[str, Any]) -> None:
    selected = case_outcomes.get("selected_cases_short")
    if not isinstance(selected, list):
        raise RetainedValidationError("terminal case outcomes missing selected cases")
    if any(case in REJECTED_RETAINED_CASES for case in selected):
        raise RetainedValidationError("terminal case outcomes include rejected cases")
    gating = case_outcomes.get("completion_gating_cases")
    if gating != list(COMPLETION_GATING_CASES):
        raise RetainedValidationError("terminal gating case set mismatch")
    if A6 in gating:
        raise RetainedValidationError("A6 cannot be terminal gating evidence")
    satisfied_by_case = _require_mapping(
        case_outcomes.get("gating_satisfied_by_case"),
        "gating_satisfied_by_case",
    )
    for case in COMPLETION_GATING_CASES:
        if not isinstance(satisfied_by_case.get(case), bool):
            raise RetainedValidationError("gating outcome must be boolean")
    expected = all(satisfied_by_case[case] for case in COMPLETION_GATING_CASES)
    if case_outcomes.get("gating_satisfied") is not expected:
        raise RetainedValidationError("aggregate gating outcome mismatch")


def _durability_result_payload(
    result: windows_adapter.DirectoryDurabilityResult,
) -> dict[str, Any]:
    return _strip_none(asdict(result))


def _default_durability_adapter() -> windows_adapter.WindowsDurabilityAdapter:
    if sys.platform == "win32":
        return windows_adapter.Win32DirectoryDurabilityAdapter()
    return windows_adapter.FailClosedWindowsDurabilityAdapter()


def _admit_result_directory_for_creation(result_dir: Path) -> None:
    if result_dir.exists():
        raise RetainedValidationError(RESULT_DIRECTORY_NOT_ABSENT)
    if not result_dir.parent.exists():
        raise RetainedValidationError("result directory parent must exist")
    if _is_reparse_point(result_dir.parent):
        raise RetainedValidationError(RESULT_DIRECTORY_REPARSE_POINT)


def _admit_drive_qualified_dos_path(path: Path) -> None:
    text = str(path)
    drive, _tail = ntpath.splitdrive(text)
    if not ntpath.isabs(text) or not drive or not re.match(r"^[A-Za-z]:$", drive):
        raise RetainedValidationError(RESULT_DIRECTORY_NOT_DRIVE_QUALIFIED)
    normalized = text.replace("/", "\\")
    if normalized.startswith("\\\\"):
        raise RetainedValidationError(RESULT_DIRECTORY_NOT_DRIVE_QUALIFIED)
    lowered = normalized.lower()
    if lowered.startswith("\\\\?\\") or lowered.startswith("\\\\.\\"):
        raise RetainedValidationError(RESULT_DIRECTORY_NOT_DRIVE_QUALIFIED)
    if "\\\\?\\" in lowered or "\\\\.\\" in lowered or "\\volume{" in lowered:
        raise RetainedValidationError(RESULT_DIRECTORY_NOT_DRIVE_QUALIFIED)


def _resolve_for_absent_child(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate.resolve()
    parent = candidate.parent
    if parent and parent.exists():
        return parent.resolve() / candidate.name
    return candidate.absolute()


def _is_reparse_point(path: Path) -> bool:
    try:
        attrs = path.stat().st_file_attributes
    except AttributeError:
        attrs = 0
    except OSError:
        return True
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _git_text(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _git_blob_oid(repo_root: Path, relative_path: str) -> str:
    completed = subprocess.run(
        ["git", "ls-files", "-s", "--", relative_path],
        cwd=str(repo_root),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if not completed.stdout.strip():
        return UNAVAILABLE_UNTIL_COMMIT
    return completed.stdout.split()[1]


def _status_line_paths(line: str) -> tuple[str, ...]:
    body = line[3:] if len(line) > 3 else line.strip()
    if " -> " in body:
        old, new = body.split(" -> ", 1)
        return (old.strip().strip('"'), new.strip().strip('"'))
    return (body.strip().strip('"'),)


def _require_hex64(value: str, field_name: str) -> None:
    if not HEX64_RE.fullmatch(value):
        raise RetainedValidationError("%s must be lowercase hex64" % field_name)


def _require_head_oid(value: str, field_name: str) -> None:
    if not HEX40_OR_64_RE.fullmatch(value):
        raise RetainedValidationError("%s must be a Git object id" % field_name)


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RetainedValidationError("%s must be an object" % field_name)
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise RetainedValidationError("duplicate JSON object key")
        seen.add(key)
        output[key] = value
    return output


def _validate_json_domain(value: Any) -> None:
    if value is None:
        raise RetainedValidationError("canonical retained JSON rejects null values")
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        raise RetainedValidationError("canonical retained JSON rejects floats")
    if isinstance(value, str):
        if any(ord(char) < 0x20 for char in value):
            raise RetainedValidationError("canonical retained JSON rejects control text")
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_domain(item)
        return
    if isinstance(value, tuple):
        for item in value:
            _validate_json_domain(item)
        return
    if isinstance(value, Mapping):
        for key, inner in value.items():
            if not isinstance(key, str):
                raise RetainedValidationError("canonical JSON object keys must be text")
            _validate_json_domain(inner)
        return
    raise RetainedValidationError("unsupported canonical JSON value")


def _failure_from_exception(exc: RetainedValidationError) -> str:
    text = str(exc)
    for failure_code in FAILURE_CODES:
        if text == failure_code or failure_code in text:
            return failure_code
    if "policy" in text.lower():
        return POLICY_MISMATCH
    if "identity" in text.lower() or "sha" in text.lower():
        return IDENTITY_MISMATCH
    if "case" in text.lower():
        return CASE_SELECTION_REJECTED
    if "repository" in text.lower() or "working tree" in text.lower():
        return SOURCE_STATE_MISMATCH
    if "result directory" in text.lower():
        return RESULT_DIRECTORY_NOT_ABSENT
    return SOURCE_STATE_MISMATCH


def _write_failure_code_for(path: Path) -> str:
    if path.name == GATE_ENTRY_FILENAME:
        return GATE_ENTRY_WRITE_FAILURE
    return TERMINAL_ARTIFACT_WRITE_FAILURE


def _reread_failure_code_for(path: Path) -> str:
    if path.name == GATE_ENTRY_FILENAME:
        return GATE_ENTRY_REVERIFY_FAILURE
    return TERMINAL_ARTIFACT_REVERIFY_FAILURE


def runtime_platform_observation() -> dict[str, Any]:
    return {
        "schema": "torment.brainvision.blocker2.retained.platform.v0.1",
        "sys_platform": sys.platform,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
    }
