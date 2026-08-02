"""Stage S3B v0.2 synthetic-validation runner.

The public CLI is fail-closed while the v0.2 implementation, test, schema, and
execution identities remain UNBOUND.  Bounded tests call the internal in-process
seams with injected manifest bytes, temporary paths, and injected descriptor
callables; those seams are not exposed through CLI flags or environment values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import independent_order_sensitive_descriptor_v0_1 as descriptor
import independent_order_sensitive_synthetic_validation_schema_contract_v0_2 as schema


UNBOUND = "UNBOUND"

EXIT_PUBLISHED_PASS = 0
EXIT_PUBLISHED_FAIL = 1
EXIT_PRECONTACT_REFUSAL = 2
EXIT_CONTROLLED_INVALID = 3
EXIT_CONSUMED_INFRASTRUCTURE_FAILURE = 4
EXIT_CONSUMED_PUBLICATION_FAILURE = 5

RESULT_KIND_PASSED = "SYNTHETIC_GATE_PASSED"
RESULT_KIND_FAILED = "SYNTHETIC_GATE_FAILED"
CONTROLLED_KIND_INVALID = "SYNTHETIC_GATE_INVALID"

TERMINAL_STATUS_REFUSED_PRE_CONTACT = "REFUSED_PRE_CONTACT"
TERMINAL_STATUS_INVALID_POST_CONTACT = "INVALID_POST_CONTACT"
TERMINAL_STATUS_FAILED_EVIDENCE_UPDATE = "FAILED_EVIDENCE_UPDATE_AFTER_CONSUMPTION"
TERMINAL_STATUS_COMPLETE = "COMPLETE"
TERMINAL_STATUS_OPERATIONAL_FAILURE = "OPERATIONAL_FAILURE_AFTER_CONSUMPTION"
TERMINAL_STATUS_PUBLICATION_FAILURE = "PUBLICATION_FAILURE_AFTER_CONSUMPTION"

FAIL_PRECONTACT_REPOSITORY_STATE = "PRECONTACT_REPOSITORY_STATE_REFUSED"
FAIL_PRECONTACT_AUTHORIZATION = "PRECONTACT_AUTHORIZATION_REFUSED"
FAIL_PRECONTACT_IDENTITY = "PRECONTACT_IDENTITY_REFUSED"
FAIL_PRECONTACT_SCHEMA_CONTRACT = "PRECONTACT_SCHEMA_CONTRACT_REFUSED"
FAIL_PRECONTACT_MANIFEST_EXPECTATION = "PRECONTACT_MANIFEST_EXPECTATION_REFUSED"
FAIL_PRECONTACT_CLI = "PRECONTACT_CLI_REFUSED"
FAIL_PRECONTACT_STDIN = "PRECONTACT_STDIN_REFUSED"
FAIL_PRECONTACT_OUTPUT_PATH_PRESENT = "PRECONTACT_OUTPUT_PATH_PRESENT_REFUSED"
FAIL_PRECONTACT_BOUNDARY = "PRECONTACT_BOUNDARY_REFUSED"
FAIL_EVIDENCE_ARMING = "EVIDENCE_ARMING_FAILED"
FAIL_CONTACT_ARM_PROMOTION = "CONTACT_ARM_PROMOTION_FAILED"

FAIL_MANIFEST_READ_AFTER_CONSUMPTION = "MANIFEST_READ_FAILED_AFTER_CONSUMPTION"
FAIL_POSTCONTACT_SCHEMA_INVALID = "POSTCONTACT_SCHEMA_INVALID"
FAIL_POSTCONTACT_IDENTITY_INVALID = "POSTCONTACT_IDENTITY_INVALID"
FAIL_POSTCONTACT_IMPLEMENTATION_EXCEPTION = "POSTCONTACT_IMPLEMENTATION_EXCEPTION"
FAIL_SCIENTIFIC_EVALUATION_EXCEPTION = "SCIENTIFIC_EVALUATION_EXCEPTION"
FAIL_RESULT_CONSTRUCTION = "RESULT_CONSTRUCTION_FAILED"
FAIL_STAGING_WRITE = "STAGING_WRITE_FAILED"
FAIL_STAGING_VERIFICATION = "STAGING_VERIFICATION_FAILED"
FAIL_PROMOTION = "PROMOTION_FAILED"
FAIL_FINAL_VERIFICATION = "FINAL_VERIFICATION_FAILED"
FAIL_EVIDENCE_UPDATE_AFTER_CONSUMPTION = "EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION"

PHASE_PRE_CONTACT = "PRE_CONTACT"
PHASE_CONTACT_ARMED = "CONTACT_ARMED"
PHASE_RESULT_CONSTRUCTING = "RESULT_CONSTRUCTING"
PHASE_STAGING_WRITING = "STAGING_WRITING"
PHASE_STAGING_VERIFYING = "STAGING_VERIFYING"
PHASE_PROMOTING = "PROMOTING"
PHASE_FINAL_VERIFICATION = "FINAL_VERIFICATION"
PHASE_COMPLETE = "COMPLETE"

RUNNER_SOURCE_PATH = (
    "research/brainvision/"
    "run_independent_order_sensitive_synthetic_validation_v0_2.py"
)
RUNNER_TEST_SOURCE_PATH = (
    "research/brainvision/"
    "test_independent_order_sensitive_synthetic_fixtures_v0_2.py"
)
SCHEMA_CONTRACT_SOURCE_PATH = (
    "research/brainvision/"
    "independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py"
)
DESCRIPTOR_SOURCE_PATH = (
    "research/brainvision/independent_order_sensitive_descriptor_v0_1.py"
)
DESCRIPTOR_TEST_SOURCE_PATH = (
    "research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py"
)
EXPECTED_MANIFEST_PATH = (
    "research/brainvision/results/"
    "independent_order_sensitive_synthetic_fixture_freeze_v0_1/"
    "independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json"
)
AUTHORIZATION_DOCUMENT_PATH = (
    "docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_"
    "V0_2_EXECUTION_AUTHORIZATION_v0.1.md"
)

EXECUTION_ARMING_PATH = (
    "research/brainvision/results/"
    ".independent_order_sensitive_synthetic_validation_v0_2.arming"
)
EXECUTION_JOURNAL_DIR = (
    "research/brainvision/results/"
    ".independent_order_sensitive_synthetic_validation_v0_2.execution_journal"
)
SCIENTIFIC_RESULT_STAGING_DIR = (
    "research/brainvision/results/"
    ".independent_order_sensitive_synthetic_validation_v0_2.staging"
)
FINAL_PUBLICATION_DIR = (
    "research/brainvision/results/"
    "independent_order_sensitive_synthetic_validation_v0_2"
)
RETAINED_V0_1_STAGING_DIR = (
    "research/brainvision/results/"
    ".independent_order_sensitive_synthetic_validation_v0_1.staging"
)

RESULT_FILE_NAME = "independent_order_sensitive_synthetic_validation_v0_2_result.json"
ENVELOPE_FILE_NAME = (
    "independent_order_sensitive_synthetic_validation_v0_2_execution_envelope.json"
)
SUMMARY_FILE_NAME = "independent_order_sensitive_synthetic_validation_v0_2_summary.txt"
SCIENTIFIC_FILE_SET: Tuple[str, ...] = (
    RESULT_FILE_NAME,
    ENVELOPE_FILE_NAME,
    SUMMARY_FILE_NAME,
)

AUTHORITATIVE_IDENTITIES: Mapping[str, str] = {
    "later_execution_authorization_identity": UNBOUND,
    "runner_git_blob": UNBOUND,
    "runner_raw_sha256": UNBOUND,
    "runner_test_git_blob": UNBOUND,
    "runner_test_raw_sha256": UNBOUND,
    "schema_contract_git_blob": UNBOUND,
    "schema_contract_raw_sha256": UNBOUND,
    "expected_manifest_external_sha256": UNBOUND,
    "expected_manifest_payload_sha256": UNBOUND,
    "v0_2_configuration_identity": UNBOUND,
}

BINDING_BEGIN = (
    "BEGIN-SYNTHETIC-VALIDATION-V0-2-EXECUTION-AUTHORIZATION-BINDING-v0.1"
)
BINDING_END = (
    "END-SYNTHETIC-VALIDATION-V0-2-EXECUTION-AUTHORIZATION-BINDING-v0.1"
)
BINDING_SCHEMA = (
    "TORMENT_BRAINVISION_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_BINDING"
)
BINDING_VERSION = "v0.2"
BINDING_FIELDS: Tuple[str, ...] = (
    "authorization_schema",
    "authorization_version",
    "later_execution_authorization_identity",
    "runner_git_blob",
    "runner_raw_sha256",
    "runner_test_git_blob",
    "runner_test_raw_sha256",
    "schema_contract_git_blob",
    "schema_contract_raw_sha256",
    "v0_2_configuration_identity",
    "expected_manifest_external_sha256",
    "expected_manifest_payload_sha256",
)
AUTHORIZATION_IDENTITY_FIELD_ORDER: Tuple[str, ...] = (
    "authorization_schema",
    "authorization_version",
    "runner_git_blob",
    "runner_raw_sha256",
    "runner_test_git_blob",
    "runner_test_raw_sha256",
    "schema_contract_git_blob",
    "schema_contract_raw_sha256",
    "v0_2_configuration_identity",
    "expected_manifest_external_sha256",
    "expected_manifest_payload_sha256",
)
AUTHORIZATION_IDENTITY_PAYLOAD_FIELDS: Tuple[str, ...] = (
    "domain_label",
    "authorization_document_path",
    "begin_marker",
    "end_marker",
    "field_order_without_later_execution_authorization_identity",
    "authorization_schema",
    "authorization_version",
    "runner_path",
    "runner_git_blob",
    "runner_raw_sha256",
    "runner_test_path",
    "runner_test_git_blob",
    "runner_test_raw_sha256",
    "schema_contract_path",
    "schema_contract_git_blob",
    "schema_contract_raw_sha256",
    "v0_2_configuration_identity",
    "expected_manifest_external_sha256",
    "expected_manifest_payload_sha256",
)
AUTHORIZATION_IDENTITY_DOMAIN_LABEL = (
    "TORMENT_BRAINVISION_S3B_V0_2_EXECUTION_AUTHORIZATION_BINDING_IDENTITY_v0.1"
)
EXPECTED_V0_2_CONFIGURATION_IDENTITY = (
    "fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9"
)
EXPECTED_MANIFEST_EXTERNAL_SHA256 = (
    "05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404"
)
EXPECTED_MANIFEST_PAYLOAD_SHA256 = (
    "56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9"
)
_HEX40_FIELDS: Tuple[str, ...] = (
    "runner_git_blob",
    "runner_test_git_blob",
    "schema_contract_git_blob",
)
_HEX64_FIELDS: Tuple[str, ...] = (
    "later_execution_authorization_identity",
    "runner_raw_sha256",
    "runner_test_raw_sha256",
    "schema_contract_raw_sha256",
    "v0_2_configuration_identity",
    "expected_manifest_external_sha256",
    "expected_manifest_payload_sha256",
)
_IMPLEMENTATION_IDENTITY_PATHS: Tuple[Tuple[str, str, str], ...] = (
    ("runner", RUNNER_SOURCE_PATH, "runner_git_blob"),
    ("runner-test", RUNNER_TEST_SOURCE_PATH, "runner_test_git_blob"),
    ("schema-contract", SCHEMA_CONTRACT_SOURCE_PATH, "schema_contract_git_blob"),
)
_PROHIBITED_AUTHORIZATION_ENVIRONMENT_NAMES: Tuple[str, ...] = (
    "TORMENT_SYNTHETIC_VALIDATION_IDENTITY",
    "TORMENT_SYNTHETIC_VALIDATION_AUTHORIZATION_PATH",
    "TORMENT_SYNTHETIC_VALIDATION_AUTHORIZATION_DOCUMENT",
    "TORMENT_SYNTHETIC_VALIDATION_AUTHORIZATION_DOCUMENT_PATH",
    "TORMENT_SYNTHETIC_VALIDATION_MANIFEST_PATH",
)


class PreContactRefusal(Exception):
    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.detail = detail


class ControlledInvalidity(Exception):
    def __init__(self, failure_code: str, detail: str) -> None:
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.detail = detail


class ConsumedInfrastructureFailure(Exception):
    def __init__(self, failure_code: str, detail: str,
                 stage: str = "post_contact") -> None:
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.detail = detail
        self.stage = stage


class PublicationFailure(Exception):
    def __init__(self, failure_code: str, detail: str,
                 stage: str = "publication") -> None:
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.detail = detail
        self.stage = stage


class EvidenceUpdateFailedAfterConsumption(Exception):
    def __init__(self, detail: str, last_verified_state: Mapping[str, Any]) -> None:
        super().__init__(FAIL_EVIDENCE_UPDATE_AFTER_CONSUMPTION)
        self.failure_code = FAIL_EVIDENCE_UPDATE_AFTER_CONSUMPTION
        self.detail = detail
        self.last_verified_state = dict(last_verified_state)


@dataclass(frozen=True)
class ExecutionPaths:
    execution_arming_path: str
    execution_journal_dir: str
    scientific_result_staging_dir: str
    final_publication_dir: str


@dataclass(frozen=True)
class RepositoryState:
    repository_root: str
    branch: str
    clean: bool
    head: str
    origin_main: str
    python_version: str


@dataclass(frozen=True)
class PreContactContext:
    repository_state: RepositoryState
    identities: Mapping[str, str]


@dataclass(frozen=True)
class FileSystemOps:
    path_exists: Callable[[str], bool] = os.path.exists
    path_is_dir: Callable[[str], bool] = os.path.isdir
    make_directory: Callable[[str], None] = os.mkdir
    rename_directory: Callable[[str, str], None] = os.rename
    replace_file: Callable[[str, str], None] = os.replace
    list_directory: Callable[[str], List[str]] = os.listdir
    open_file: Callable[..., Any] = open
    sync_directory: Callable[[str], None] = lambda path: _sync_directory_best_effort(path)


@dataclass(frozen=True)
class BoundedRunConfig:
    paths: ExecutionPaths
    read_manifest_bytes: Callable[[int], bytes]
    repository_state: RepositoryState
    descriptor_callable: Callable[[Sequence[int]], Any] = descriptor.affine_plus_complement_signature
    raw_signature_callable: Callable[[Sequence[int]], Any] = descriptor.raw_labeled_signature
    affine_signature_callable: Callable[[Sequence[int]], Any] = descriptor.affine_only_signature
    descriptor_result_callable: Callable[[Sequence[int]], Mapping[str, Any]] = descriptor.descriptor_result
    fs_ops: FileSystemOps = field(default_factory=FileSystemOps)
    clock: Callable[[], str] = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    expected_external_manifest_sha256: Optional[str] = None
    expected_manifest_payload_sha256: Optional[str] = None
    expected_freeze_configuration_sha256: str = schema.FROZEN_CONFIGURATION_SHA256
    precontact_authorized: bool = True
    simulate_result_construction_failure: bool = False
    simulate_staging_write_failure: bool = False
    simulate_staging_verification_failure: bool = False
    simulate_promotion_failure: bool = False
    simulate_final_verification_failure: bool = False
    simulate_terminal_evidence_failure: bool = False


@dataclass(frozen=True)
class RunOutcome:
    exit_code: int
    stdout: bytes = b""
    stderr: bytes = b""
    authority_consumed: bool = False
    terminal_status: Optional[str] = None
    failure_code: Optional[str] = None
    scientific_result_kind: Optional[str] = None
    controlled_outcome_kind: Optional[str] = None
    scientific_evaluation_reached: bool = False
    descriptor_evaluation_reached: bool = False
    final_publication_available: bool = False
    terminal_evidence_written: bool = False
    last_verified_durable_state: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ArmResult:
    authority_consumed: bool
    state: Dict[str, Any]


def default_authoritative_paths() -> ExecutionPaths:
    return ExecutionPaths(
        EXECUTION_ARMING_PATH,
        EXECUTION_JOURNAL_DIR,
        SCIENTIFIC_RESULT_STAGING_DIR,
        FINAL_PUBLICATION_DIR,
    )


def default_descriptor_callable(vector: Sequence[int]) -> Tuple[int, Tuple[int, ...]]:
    return descriptor.affine_plus_complement_signature(list(vector))


def _sync_directory_best_effort(path: str) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _safe_detail(exc: BaseException) -> str:
    message = "%s:%s" % (exc.__class__.__name__, str(exc))
    message = " ".join(message.split())
    return message[:180]


def _require_same_filesystem_path(source: str, destination: str) -> None:
    abs_source = os.path.abspath(source)
    abs_destination = os.path.abspath(destination)
    source_drive = os.path.splitdrive(abs_source)[0].lower()
    destination_drive = os.path.splitdrive(abs_destination)[0].lower()
    if source_drive != destination_drive:
        raise PreContactRefusal(
            FAIL_CONTACT_ARM_PROMOTION,
            "arming and journal paths are not on the same filesystem",
        )


def _current_state_path(journal_or_arming_dir: str) -> str:
    return os.path.join(journal_or_arming_dir, "current_state.json")


def _terminal_evidence_path(journal_dir: str) -> str:
    return os.path.join(journal_dir, "terminal_evidence.json")


def contact_armed_state() -> Dict[str, Any]:
    return {
        "phase": PHASE_CONTACT_ARMED,
        "authority_consumed": True,
        "contact_armed": True,
        "manifest_contact_attempt_count": 0,
        "manifest_read_success_count": 0,
    }


def _validate_state_invariants(state: Mapping[str, Any]) -> None:
    required = (
        "phase",
        "authority_consumed",
        "contact_armed",
        "manifest_contact_attempt_count",
        "manifest_read_success_count",
    )
    if tuple(state.keys()) != required:
        raise ValueError("current_state key order invalid")
    attempts = state["manifest_contact_attempt_count"]
    successes = state["manifest_read_success_count"]
    if state["authority_consumed"] is not True or state["contact_armed"] is not True:
        raise ValueError("current_state authority flags invalid")
    if not schema.is_strict_int(attempts) or not schema.is_strict_int(successes):
        raise ValueError("manifest contact counters are not strict integers")
    if not (0 <= successes <= attempts <= 2):
        raise ValueError("manifest contact counter invariant violated")


def _read_bytes(path: str, fs_ops: FileSystemOps) -> bytes:
    with fs_ops.open_file(path, "rb") as handle:
        return handle.read()


def _write_bytes_exclusive(path: str, payload: bytes, fs_ops: FileSystemOps) -> None:
    with fs_ops.open_file(path, "xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    if _read_bytes(path, fs_ops) != payload:
        raise IOError("exclusive write read-back mismatch")
    fs_ops.sync_directory(os.path.dirname(path))


def _write_json_exclusive(path: str, value: Any, fs_ops: FileSystemOps) -> None:
    _write_bytes_exclusive(path, schema.canonical_json_bytes(value), fs_ops)


def _read_json(path: str, fs_ops: FileSystemOps) -> Dict[str, Any]:
    payload = _read_bytes(path, fs_ops)
    loaded = json.loads(payload.decode("utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("JSON document is not an object")
    return loaded


def _write_current_state_atomic(journal_dir: str, state: Mapping[str, Any],
                                fs_ops: FileSystemOps,
                                last_verified_state: Mapping[str, Any]) -> Dict[str, Any]:
    try:
        _validate_state_invariants(state)
        target = _current_state_path(journal_dir)
        temp_path = target + ".tmp"
        payload = schema.canonical_json_bytes(state)
        _write_bytes_exclusive(temp_path, payload, fs_ops)
        fs_ops.replace_file(temp_path, target)
        if _read_bytes(target, fs_ops) != payload:
            raise IOError("current_state read-back mismatch")
        fs_ops.sync_directory(journal_dir)
    except Exception as exc:
        raise EvidenceUpdateFailedAfterConsumption(_safe_detail(exc), last_verified_state)
    return dict(state)


def _read_current_state(journal_dir: str, fs_ops: FileSystemOps) -> Dict[str, Any]:
    state = _read_json(_current_state_path(journal_dir), fs_ops)
    _validate_state_invariants(state)
    return state


def arm_authority(paths: ExecutionPaths,
                  fs_ops: FileSystemOps = FileSystemOps()) -> ArmResult:
    """Prepare CONTACT_ARMED state and consume authority by one directory rename."""
    _require_same_filesystem_path(paths.execution_arming_path, paths.execution_journal_dir)
    if fs_ops.path_exists(paths.execution_arming_path):
        raise PreContactRefusal(FAIL_EVIDENCE_ARMING, "arming path already exists")
    if fs_ops.path_exists(paths.execution_journal_dir):
        raise PreContactRefusal(FAIL_CONTACT_ARM_PROMOTION, "journal path already exists")
    state = contact_armed_state()
    try:
        fs_ops.make_directory(paths.execution_arming_path)
        if not fs_ops.path_is_dir(paths.execution_arming_path):
            raise IOError("arming path is not a directory")
        fs_ops.sync_directory(os.path.dirname(paths.execution_arming_path))
        _write_json_exclusive(_current_state_path(paths.execution_arming_path), state, fs_ops)
        _validate_state_invariants(_read_json(_current_state_path(paths.execution_arming_path), fs_ops))
    except Exception as exc:
        raise PreContactRefusal(FAIL_EVIDENCE_ARMING, _safe_detail(exc))

    if fs_ops.path_exists(paths.execution_journal_dir):
        raise PreContactRefusal(FAIL_CONTACT_ARM_PROMOTION, "journal path appeared before rename")
    try:
        fs_ops.rename_directory(paths.execution_arming_path, paths.execution_journal_dir)
        fs_ops.sync_directory(os.path.dirname(paths.execution_journal_dir))
        if fs_ops.path_exists(paths.execution_arming_path):
            raise IOError("arming path remains after rename")
        if not fs_ops.path_is_dir(paths.execution_journal_dir):
            raise IOError("journal directory was not created by rename")
        promoted_state = _read_json(_current_state_path(paths.execution_journal_dir), fs_ops)
        if promoted_state != state:
            raise IOError("promoted current_state read-back mismatch")
        _validate_state_invariants(promoted_state)
    except Exception as exc:
        raise PreContactRefusal(FAIL_CONTACT_ARM_PROMOTION, _safe_detail(exc))
    return ArmResult(True, state)


def _replace_state_phase(journal_dir: str, state: Mapping[str, Any], phase: str,
                         fs_ops: FileSystemOps) -> Dict[str, Any]:
    next_state = dict(state)
    next_state["phase"] = phase
    return _write_current_state_atomic(journal_dir, next_state, fs_ops, state)


def _record_manifest_contact_attempt(journal_dir: str, state: Mapping[str, Any],
                                     pass_index: int,
                                     fs_ops: FileSystemOps) -> Dict[str, Any]:
    attempts = state["manifest_contact_attempt_count"]
    if attempts >= 2:
        raise ConsumedInfrastructureFailure(
            FAIL_MANIFEST_READ_AFTER_CONSUMPTION,
            "third manifest contact attempt prohibited",
        )
    next_state = dict(state)
    next_state["phase"] = "MANIFEST_CONTACT_STARTED_PASS_%d" % pass_index
    next_state["manifest_contact_attempt_count"] = attempts + 1
    return _write_current_state_atomic(journal_dir, next_state, fs_ops, state)


def _record_manifest_read_success(journal_dir: str, state: Mapping[str, Any],
                                  pass_index: int,
                                  fs_ops: FileSystemOps) -> Dict[str, Any]:
    successes = state["manifest_read_success_count"]
    if successes >= 2:
        raise ConsumedInfrastructureFailure(
            FAIL_MANIFEST_READ_AFTER_CONSUMPTION,
            "third manifest read success prohibited",
        )
    next_state = dict(state)
    next_state["phase"] = "MANIFEST_READ_SUCCEEDED_PASS_%d" % pass_index
    next_state["manifest_read_success_count"] = successes + 1
    return _write_current_state_atomic(journal_dir, next_state, fs_ops, state)


def read_manifest_with_accounting(journal_dir: str,
                                  state: Mapping[str, Any],
                                  pass_index: int,
                                  read_manifest_bytes: Callable[[int], bytes],
                                  fs_ops: FileSystemOps = FileSystemOps()
                                  ) -> Tuple[bytes, Dict[str, Any]]:
    state_after_attempt = _record_manifest_contact_attempt(
        journal_dir,
        state,
        pass_index,
        fs_ops,
    )
    try:
        manifest_bytes = read_manifest_bytes(pass_index)
    except Exception as exc:
        raise ConsumedInfrastructureFailure(
            FAIL_MANIFEST_READ_AFTER_CONSUMPTION,
            _safe_detail(exc),
            "manifest_read",
        )
    if not isinstance(manifest_bytes, bytes):
        raise ConsumedInfrastructureFailure(
            FAIL_MANIFEST_READ_AFTER_CONSUMPTION,
            "manifest reader returned non-bytes",
            "manifest_read",
        )
    state_after_success = _record_manifest_read_success(
        journal_dir,
        state_after_attempt,
        pass_index,
        fs_ops,
    )
    return manifest_bytes, state_after_success


def _call_descriptor(descriptor_callable: Callable[[Sequence[int]], Any],
                     vector: Sequence[int]) -> Any:
    return descriptor_callable(list(vector))


def _validated_scientific_vector(vector: Sequence[int]) -> List[int]:
    if not isinstance(vector, list) or len(vector) != schema.N:
        raise ControlledInvalidity(FAIL_POSTCONTACT_SCHEMA_INVALID, "scientific vector shape invalid")
    validated: List[int] = []
    for value in vector:
        if not schema.is_strict_int(value) or value not in (0, 1):
            raise ControlledInvalidity(FAIL_POSTCONTACT_SCHEMA_INVALID, "scientific vector domain invalid")
        validated.append(value)
    total = sum(validated)
    if total == 0 or total == schema.N:
        raise ControlledInvalidity(FAIL_POSTCONTACT_SCHEMA_INVALID, "scientific vector degenerate")
    return validated


def _exact_signature(value: Any, label: str) -> Tuple[int, Tuple[int, ...]]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise ConsumedInfrastructureFailure(
            FAIL_SCIENTIFIC_EVALUATION_EXCEPTION,
            "%s signature container invalid" % label,
            "scientific_evaluation",
        )
    denominator, numerators = value
    if not schema.is_strict_int(denominator):
        raise ConsumedInfrastructureFailure(
            FAIL_SCIENTIFIC_EVALUATION_EXCEPTION,
            "%s signature denominator invalid" % label,
            "scientific_evaluation",
        )
    if not isinstance(numerators, tuple) or len(numerators) != descriptor.ENTRY_COUNT:
        raise ConsumedInfrastructureFailure(
            FAIL_SCIENTIFIC_EVALUATION_EXCEPTION,
            "%s signature numerator vector invalid" % label,
            "scientific_evaluation",
        )
    for numerator in numerators:
        if not schema.is_strict_int(numerator):
            raise ConsumedInfrastructureFailure(
                FAIL_SCIENTIFIC_EVALUATION_EXCEPTION,
                "%s signature numerator type invalid" % label,
                "scientific_evaluation",
            )
    return denominator, numerators


def _scientific_signature(signature_callable: Callable[[Sequence[int]], Any],
                          vector: Sequence[int],
                          label: str) -> Tuple[int, Tuple[int, ...]]:
    return _exact_signature(
        _call_descriptor(signature_callable, _validated_scientific_vector(vector)),
        label,
    )


def _distinguished_by_signature(signature_callable: Callable[[Sequence[int]], Any],
                                left_vector: Sequence[int],
                                right_vector: Sequence[int],
                                label: str) -> bool:
    left_signature = _scientific_signature(signature_callable, left_vector, label + ".left")
    right_signature = _scientific_signature(signature_callable, right_vector, label + ".right")
    return left_signature != right_signature


def _rotate_vector(vector: Sequence[int], shift: int) -> List[int]:
    return [vector[(index - shift) % schema.N] for index in range(schema.N)]


def _units_mod_n() -> Tuple[int, ...]:
    return tuple(value for value in range(schema.N) if math.gcd(value, schema.N) == 1)


def _affine_transform_vector(vector: Sequence[int], unit: int, shift: int) -> List[int]:
    inverse = pow(unit, -1, schema.N)
    return [vector[(inverse * (index - shift)) % schema.N] for index in range(schema.N)]


def _complement_vector(vector: Sequence[int]) -> List[int]:
    return [1 - value for value in vector]


def _method_b_control_vector() -> List[int]:
    return [1 if index % 2 == 0 else 0 for index in range(schema.N)]


def _signature_cache_lookup(cache: Dict[Tuple[int, ...], Tuple[int, Tuple[int, ...]]],
                            signature_callable: Callable[[Sequence[int]], Any],
                            vector: Sequence[int],
                            label: str) -> Tuple[int, Tuple[int, ...]]:
    key = tuple(_validated_scientific_vector(list(vector)))
    if key not in cache:
        cache[key] = _scientific_signature(signature_callable, list(key), label)
    return cache[key]


def _evaluate_malformed_and_degenerate_controls(
        descriptor_result_callable: Callable[[Sequence[int]], Mapping[str, Any]]
        ) -> Dict[str, Any]:
    cases = (
        ("wrong_length_below", [0] * (schema.N - 1), "INPUT_LENGTH_INVALID"),
        ("wrong_length_above", [0] * (schema.N + 1), "INPUT_LENGTH_INVALID"),
        ("non_integer_entry", [0] * (schema.N - 1) + ["1"], "INPUT_ELEMENT_TYPE_INVALID"),
        ("bool_entry", [0] * (schema.N - 1) + [True], "INPUT_ELEMENT_TYPE_INVALID"),
        ("negative_entry", [0] * (schema.N - 1) + [-1], "INPUT_BINARY_DOMAIN_INVALID"),
        ("greater_than_one_entry", [0] * (schema.N - 1) + [2], "INPUT_BINARY_DOMAIN_INVALID"),
        ("all_zero_sequence", [0] * schema.N, "DEGENERATE_SEQUENCE"),
        ("all_one_sequence", [1] * schema.N, "DEGENERATE_SEQUENCE"),
    )
    observed = []
    all_correct = True
    for name, vector, expected_code in cases:
        try:
            payload = descriptor_result_callable(list(vector))
            validation = payload.get("validation") if isinstance(payload, dict) else None
            observed_code = validation.get("failure_code") if isinstance(validation, dict) else None
            observed_stage = validation.get("failure_stage") if isinstance(validation, dict) else None
            valid = validation.get("valid") if isinstance(validation, dict) else None
            correct = (
                valid is False and
                observed_code == expected_code and
                observed_stage == "input_validation"
            )
        except Exception as exc:
            observed_code = exc.__class__.__name__
            observed_stage = "exception"
            correct = False
        observed.append({
            "case": name,
            "expected_failure_code": expected_code,
            "observed_failure_code": observed_code,
            "observed_failure_stage": observed_stage,
            "correct": correct,
        })
        all_correct = all_correct and correct
    return {"correct": all_correct, "cases": observed}


def _evaluate_identity_controls(config: BoundedRunConfig,
                                vectors: Sequence[Sequence[int]]) -> Dict[str, Any]:
    base_vector = _validated_scientific_vector(vectors[0])
    independent_copy = list(base_vector)
    identity_affine = _affine_transform_vector(base_vector, 1, 0)
    nontrivial_affine = _affine_transform_vector(base_vector, 3, 5)
    affine_plus_complement = _complement_vector(_affine_transform_vector(base_vector, 5, 7))

    raw_base = _scientific_signature(config.raw_signature_callable, base_vector, "identity.raw.base")
    affine_base = _scientific_signature(config.affine_signature_callable, base_vector, "identity.affine.base")
    plus_base = _scientific_signature(config.descriptor_callable, base_vector, "identity.plus.base")
    repeat_first = _scientific_signature(config.descriptor_callable, base_vector, "identity.repeat.first")
    repeat_second = _scientific_signature(config.descriptor_callable, base_vector, "identity.repeat.second")

    cases = {
        "raw_identity_behavior": (
            raw_base ==
            _scientific_signature(config.raw_signature_callable, identity_affine, "identity.raw.identity")
        ),
        "repeat_determinism": repeat_first == repeat_second,
        "independently_allocated_equal_input": (
            id(base_vector) != id(independent_copy) and
            plus_base == _scientific_signature(
                config.descriptor_callable,
                independent_copy,
                "identity.plus.independent",
            )
        ),
        "affine_identity_behavior": (
            affine_base ==
            _scientific_signature(
                config.affine_signature_callable,
                identity_affine,
                "identity.affine.identity",
            )
        ),
        "affine_equivalent_behavior": (
            affine_base ==
            _scientific_signature(
                config.affine_signature_callable,
                nontrivial_affine,
                "identity.affine.nontrivial",
            )
        ),
        "affine_plus_complement_identity_behavior": (
            plus_base ==
            _scientific_signature(
                config.descriptor_callable,
                identity_affine,
                "identity.plus.identity",
            )
        ),
        "affine_plus_complement_behavior": (
            plus_base ==
            _scientific_signature(
                config.descriptor_callable,
                affine_plus_complement,
                "identity.plus.complement",
            )
        ),
    }
    return {"correct": all(cases.values()), "cases": cases}


def _evaluate_method_b_nuisance_controls(config: BoundedRunConfig) -> Dict[str, Any]:
    base_vector = _method_b_control_vector()
    cache: Dict[Tuple[int, ...], Tuple[int, Tuple[int, ...]]] = {}
    base_signature = _signature_cache_lookup(
        cache,
        config.descriptor_callable,
        base_vector,
        "method_b.base",
    )
    units = _units_mod_n()
    counts = {
        "rotations": 0,
        "affine_transforms": 0,
        "affine_plus_complement_transforms": 0,
    }
    required = {
        "rotations": schema.N,
        "affine_transforms": len(units) * schema.N,
        "affine_plus_complement_transforms": len(units) * schema.N * 2,
    }
    all_correct = True
    for shift in range(schema.N):
        transformed = _rotate_vector(base_vector, shift)
        signature = _signature_cache_lookup(
            cache,
            config.descriptor_callable,
            transformed,
            "method_b.rotation",
        )
        all_correct = all_correct and (signature == base_signature)
        counts["rotations"] += 1

    for unit in units:
        for shift in range(schema.N):
            transformed = _affine_transform_vector(base_vector, unit, shift)
            signature = _signature_cache_lookup(
                cache,
                config.descriptor_callable,
                transformed,
                "method_b.affine",
            )
            all_correct = all_correct and (signature == base_signature)
            counts["affine_transforms"] += 1

            complement = _complement_vector(transformed)
            complement_signature = _signature_cache_lookup(
                cache,
                config.descriptor_callable,
                complement,
                "method_b.affine_plus_complement",
            )
            all_correct = all_correct and (complement_signature == base_signature)
            counts["affine_plus_complement_transforms"] += 2

    method_b_full_enumeration = counts == required
    return {
        "correct": all_correct and method_b_full_enumeration,
        "counts": counts,
        "required_counts": required,
        "unique_vectors_evaluated": len(cache),
        "method_b_full_enumeration": method_b_full_enumeration,
        "sampling_used": False,
    }


def _evaluate_scientific_bundle(manifest: Mapping[str, Any],
                                config: BoundedRunConfig
                                ) -> Dict[str, Any]:
    fixed_fixture = manifest["fixed_fixture"]
    fixed_vectors = [
        fixed_fixture[schema.FIXED_MEMBER_BINARY_KEYS[0]],
        fixed_fixture[schema.FIXED_MEMBER_BINARY_KEYS[1]],
    ]
    fixed_distinguished = _distinguished_by_signature(
        config.descriptor_callable,
        fixed_vectors[0],
        fixed_vectors[1],
        "fixed_positive",
    )

    accepted_results: List[Dict[str, Any]] = []
    accepted_vectors: List[Sequence[int]] = []
    for fixture in manifest["accepted_fixtures"]:
        left_vector = fixture[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]]
        right_vector = fixture[schema.ACCEPTED_MEMBER_BINARY_KEYS[1]]
        accepted_vectors.extend([left_vector, right_vector])
        distinguished = _distinguished_by_signature(
            config.descriptor_callable,
            left_vector,
            right_vector,
            "accepted_%d" % fixture["family_index"],
        )
        accepted_results.append({
            "family_index": fixture["family_index"],
            "seed_order_position": fixture["seed_order_position"],
            "pair_duplicate_key": fixture["pair_duplicate_key"],
            "distinguished": distinguished,
        })

    all_vectors = list(fixed_vectors) + accepted_vectors
    malformed_controls = _evaluate_malformed_and_degenerate_controls(
        config.descriptor_result_callable,
    )
    identity_controls = _evaluate_identity_controls(config, all_vectors)
    nuisance_controls = _evaluate_method_b_nuisance_controls(config)
    accepted_distinguished_count = sum(
        1 for result in accepted_results if result["distinguished"]
    )
    method_b_full_enumeration = nuisance_controls["method_b_full_enumeration"]
    sampling_used = nuisance_controls["sampling_used"]
    malformed_and_degenerate_controls_correct = malformed_controls["correct"]
    identity_controls_correct = identity_controls["correct"]
    nuisance_controls_correct = nuisance_controls["correct"]

    all_scientific_checks_pass = all((
        fixed_distinguished,
        malformed_and_degenerate_controls_correct,
        identity_controls_correct,
        nuisance_controls_correct,
        method_b_full_enumeration,
        not sampling_used,
        accepted_distinguished_count == schema.K_SYNTHETIC,
    ))
    result_kind = RESULT_KIND_PASSED if all_scientific_checks_pass else RESULT_KIND_FAILED
    return {
        "schema": "torment-brainvision-synthetic-validation-pass-bundle-v0.2",
        "fixed_positive": {
            "distinguished": fixed_distinguished,
        },
        "controls": {
            "malformed_and_degenerate_controls_correct": (
                malformed_and_degenerate_controls_correct
            ),
            "identity_controls_correct": identity_controls_correct,
            "nuisance_controls_correct": nuisance_controls_correct,
            "method_b_full_enumeration": method_b_full_enumeration,
            "sampling_used": sampling_used,
            "malformed_and_degenerate_control_cases": malformed_controls["cases"],
            "identity_control_cases": identity_controls["cases"],
            "method_b_counts": nuisance_controls["counts"],
            "method_b_required_counts": nuisance_controls["required_counts"],
            "method_b_unique_vectors_evaluated": nuisance_controls["unique_vectors_evaluated"],
        },
        "accepted_family": {
            "required_count": schema.K_SYNTHETIC,
            "distinguished_count": accepted_distinguished_count,
            "results": accepted_results,
        },
        "scientific_result_kind": result_kind,
    }


def _parse_manifest_fresh(manifest_bytes: bytes) -> Dict[str, Any]:
    try:
        parsed = json.loads(manifest_bytes.decode("utf-8"))
    except Exception as exc:
        raise ControlledInvalidity(FAIL_POSTCONTACT_SCHEMA_INVALID, _safe_detail(exc))
    if not isinstance(parsed, dict):
        raise ControlledInvalidity(FAIL_POSTCONTACT_SCHEMA_INVALID, "manifest is not an object")
    return parsed


def _validate_manifest_or_raise(manifest: Mapping[str, Any]) -> None:
    result = schema.validate_manifest_payload(manifest)
    if result.valid:
        return
    failure_code = FAIL_POSTCONTACT_SCHEMA_INVALID
    if result.failure_code == "HASH_IDENTITY_FAILURE":
        failure_code = FAIL_POSTCONTACT_IDENTITY_INVALID
    raise ControlledInvalidity(failure_code, result.detail or "manifest validation failed")


def _run_single_pass(journal_dir: str,
                     state: Mapping[str, Any],
                     pass_index: int,
                     config: BoundedRunConfig) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    manifest_bytes, state = read_manifest_with_accounting(
        journal_dir,
        state,
        pass_index,
        config.read_manifest_bytes,
        config.fs_ops,
    )
    observed_external = schema.sha256_hex(manifest_bytes)
    if config.expected_external_manifest_sha256 is not None and (
            observed_external != config.expected_external_manifest_sha256):
        raise ControlledInvalidity(
            FAIL_POSTCONTACT_IDENTITY_INVALID,
            "observed external manifest SHA-256 mismatch",
        )

    state = _replace_state_phase(
        journal_dir,
        state,
        "MANIFEST_VALIDATING_PASS_%d" % pass_index,
        config.fs_ops,
    )
    manifest = _parse_manifest_fresh(manifest_bytes)
    observed_payload = schema.manifest_payload_sha256(manifest)
    if config.expected_manifest_payload_sha256 is not None and (
            observed_payload != config.expected_manifest_payload_sha256):
        raise ControlledInvalidity(
            FAIL_POSTCONTACT_IDENTITY_INVALID,
            "observed manifest payload SHA-256 mismatch",
        )
    if (manifest.get("configuration_identity", {}).get("configuration_sha256")
            != config.expected_freeze_configuration_sha256):
        raise ControlledInvalidity(
            FAIL_POSTCONTACT_IDENTITY_INVALID,
            "freeze configuration identity mismatch",
        )
    _validate_manifest_or_raise(manifest)
    state = _replace_state_phase(
        journal_dir,
        state,
        "MANIFEST_VALIDATED_PASS_%d" % pass_index,
        config.fs_ops,
    )

    state = _replace_state_phase(
        journal_dir,
        state,
        "SCIENTIFIC_EVALUATING_PASS_%d" % pass_index,
        config.fs_ops,
    )
    try:
        scientific_bundle = _evaluate_scientific_bundle(
            manifest,
            config,
        )
    except ControlledInvalidity:
        raise
    except Exception as exc:
        raise ConsumedInfrastructureFailure(
            FAIL_SCIENTIFIC_EVALUATION_EXCEPTION,
            _safe_detail(exc),
            "scientific_evaluation",
        )
    return scientific_bundle, state


def run_two_pass_validation(journal_dir: str, state: Mapping[str, Any],
                            config: BoundedRunConfig
                            ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    pass_one_bundle, state = _run_single_pass(journal_dir, state, 1, config)
    pass_two_bundle, state = _run_single_pass(journal_dir, state, 2, config)
    if schema.canonical_json_bytes(pass_one_bundle) != schema.canonical_json_bytes(pass_two_bundle):
        raise ConsumedInfrastructureFailure(
            FAIL_POSTCONTACT_IMPLEMENTATION_EXCEPTION,
            "two-pass scientific bundles are not byte-identical",
            "replay_comparison",
        )
    return pass_two_bundle, state


def _result_artifacts(result_kind: str, pass_bundle: Mapping[str, Any],
                      state: Mapping[str, Any],
                      repository_state: RepositoryState) -> Mapping[str, bytes]:
    result_payload = {
        "schema": "torment-brainvision-synthetic-validation-result-v0.2",
        "result_kind": result_kind,
        "scientific_evaluation_reached": True,
        "descriptor_evaluation_reached": True,
        "pass_bundle_sha256": schema.sha256_hex(schema.canonical_json_bytes(pass_bundle)),
        "strong_order_hypothesis": "STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY",
        "formal_hold": "active",
        "mode": "Mode_0",
    }
    envelope_payload = {
        "schema": "torment-brainvision-synthetic-validation-execution-envelope-v0.2",
        "authority_consumed": True,
        "current_state": dict(state),
        "repository_execution_head": repository_state.head,
        "branch": repository_state.branch,
        "python_version": repository_state.python_version,
        "runner_identity": {
            "source_path": RUNNER_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "runner_test_identity": {
            "source_path": RUNNER_TEST_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "schema_contract_identity": {
            "source_path": SCHEMA_CONTRACT_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "descriptor_identity": {
            "source_path": DESCRIPTOR_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "scientific_result_kind": result_kind,
        "pass_bundle": pass_bundle,
    }
    summary = (
        "Stage S3B v0.2 synthetic validation\n"
        "result_kind = %s\n"
        "FORMAL_HOLD = active\n"
        "Mode_0 = active\n"
        "STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY\n"
    ) % result_kind
    return {
        RESULT_FILE_NAME: schema.canonical_json_bytes(result_payload),
        ENVELOPE_FILE_NAME: schema.canonical_json_bytes(envelope_payload),
        SUMMARY_FILE_NAME: summary.encode("utf-8"),
    }


def publish_scientific_artifacts(paths: ExecutionPaths,
                                 artifacts: Mapping[str, bytes],
                                 fs_ops: FileSystemOps = FileSystemOps(),
                                 simulate_staging_write_failure: bool = False,
                                 simulate_staging_verification_failure: bool = False,
                                 simulate_promotion_failure: bool = False,
                                 simulate_final_verification_failure: bool = False) -> None:
    if tuple(artifacts.keys()) != SCIENTIFIC_FILE_SET:
        raise PublicationFailure(FAIL_RESULT_CONSTRUCTION, "scientific file set invalid")
    if fs_ops.path_exists(paths.scientific_result_staging_dir):
        raise PublicationFailure(FAIL_STAGING_WRITE, "staging directory already exists")
    if fs_ops.path_exists(paths.final_publication_dir):
        raise PublicationFailure(FAIL_PROMOTION, "final publication directory already exists")
    try:
        fs_ops.make_directory(paths.scientific_result_staging_dir)
        if fs_ops.list_directory(paths.scientific_result_staging_dir):
            raise IOError("staging directory is not empty")
        if simulate_staging_write_failure:
            raise IOError("simulated staging write failure")
        for file_name in SCIENTIFIC_FILE_SET:
            _write_bytes_exclusive(
                os.path.join(paths.scientific_result_staging_dir, file_name),
                artifacts[file_name],
                fs_ops,
            )
    except PublicationFailure:
        raise
    except Exception as exc:
        raise PublicationFailure(FAIL_STAGING_WRITE, _safe_detail(exc))

    try:
        if simulate_staging_verification_failure:
            raise IOError("simulated staging verification failure")
        actual_names = tuple(sorted(fs_ops.list_directory(paths.scientific_result_staging_dir)))
        if actual_names != tuple(sorted(SCIENTIFIC_FILE_SET)):
            raise IOError("staging file set mismatch")
        for file_name in SCIENTIFIC_FILE_SET:
            path = os.path.join(paths.scientific_result_staging_dir, file_name)
            if _read_bytes(path, fs_ops) != artifacts[file_name]:
                raise IOError("staging bytes mismatch")
    except Exception as exc:
        raise PublicationFailure(FAIL_STAGING_VERIFICATION, _safe_detail(exc))

    try:
        if simulate_promotion_failure:
            raise IOError("simulated promotion failure")
        if fs_ops.path_exists(paths.final_publication_dir):
            raise IOError("final publication directory already exists")
        fs_ops.rename_directory(paths.scientific_result_staging_dir, paths.final_publication_dir)
        fs_ops.sync_directory(os.path.dirname(paths.final_publication_dir))
    except Exception as exc:
        raise PublicationFailure(FAIL_PROMOTION, _safe_detail(exc))

    try:
        if simulate_final_verification_failure:
            raise IOError("simulated final verification failure")
        if not fs_ops.path_is_dir(paths.final_publication_dir):
            raise IOError("final publication directory missing")
        actual_names = tuple(sorted(fs_ops.list_directory(paths.final_publication_dir)))
        if actual_names != tuple(sorted(SCIENTIFIC_FILE_SET)):
            raise IOError("final file set mismatch")
        for file_name in SCIENTIFIC_FILE_SET:
            path = os.path.join(paths.final_publication_dir, file_name)
            if _read_bytes(path, fs_ops) != artifacts[file_name]:
                raise IOError("final bytes mismatch")
    except Exception as exc:
        raise PublicationFailure(FAIL_FINAL_VERIFICATION, _safe_detail(exc))


def _terminal_payload(state: Mapping[str, Any],
                      repository_state: RepositoryState,
                      terminal_status: str,
                      failure_category: Optional[str],
                      failure_code: Optional[str],
                      failure_stage: Optional[str],
                      exit_code: int,
                      controlled_outcome_available: bool,
                      controlled_outcome_kind: Optional[str],
                      scientific_result_available: bool,
                      scientific_result_kind: Optional[str],
                      scientific_evaluation_reached: bool,
                      descriptor_evaluation_reached: bool,
                      final_publication_available: bool,
                      publication_status: str,
                      staging_status: str,
                      timestamp: str,
                      observed_identities: Optional[Mapping[str, Any]] = None
                      ) -> Dict[str, Any]:
    return {
        "format_identifier": "torment-brainvision-synthetic-validation-terminal-v0.2",
        "schema_version": "0.2",
        "operation_version": "v0.2",
        "authority_consumed": True,
        "contact_armed": True,
        "manifest_contact_attempt_count": state["manifest_contact_attempt_count"],
        "manifest_read_success_count": state["manifest_read_success_count"],
        "execution_phase": state["phase"],
        "terminal_status": terminal_status,
        "failure_category": failure_category,
        "canonical_failure_code": failure_code,
        "failure_stage": failure_stage,
        "exit_code": exit_code,
        "controlled_outcome_available": controlled_outcome_available,
        "controlled_outcome_kind": controlled_outcome_kind,
        "scientific_result_available": scientific_result_available,
        "scientific_result_kind": scientific_result_kind,
        "scientific_evaluation_reached": scientific_evaluation_reached,
        "descriptor_evaluation_reached": descriptor_evaluation_reached,
        "final_publication_available": final_publication_available,
        "repository_execution_head": repository_state.head,
        "branch": repository_state.branch,
        "python_version": repository_state.python_version,
        "runner_identity": {
            "source_path": RUNNER_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "runner_test_identity": {
            "source_path": RUNNER_TEST_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "descriptor_identity": {
            "source_path": DESCRIPTOR_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "descriptor_test_identity": {
            "source_path": DESCRIPTOR_TEST_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "schema_contract_identity": {
            "source_path": SCHEMA_CONTRACT_SOURCE_PATH,
            "git_blob": UNBOUND,
            "raw_sha256": UNBOUND,
        },
        "expected_manifest_path": EXPECTED_MANIFEST_PATH,
        "expected_external_manifest_identity": UNBOUND,
        "expected_payload_identity": UNBOUND,
        "expected_freeze_configuration_identity": schema.FROZEN_CONFIGURATION_SHA256,
        "observed_identities": dict(observed_identities or {}),
        "publication_status": publication_status,
        "staging_status": staging_status,
        "timestamps": {"terminalized_at": timestamp},
    }


def _write_terminal_evidence(journal_dir: str, payload: Mapping[str, Any],
                             fs_ops: FileSystemOps,
                             last_verified_state: Mapping[str, Any],
                             simulate_failure: bool = False) -> None:
    try:
        if simulate_failure:
            raise IOError("simulated terminal evidence failure")
        payload_bytes = schema.canonical_json_bytes(payload)
        wrapper = {
            "payload": dict(payload),
            "payload_sha256": schema.sha256_hex(payload_bytes),
        }
        wrapper_bytes = schema.canonical_json_bytes(wrapper)
        _write_bytes_exclusive(_terminal_evidence_path(journal_dir), wrapper_bytes, fs_ops)
        reread = _read_json(_terminal_evidence_path(journal_dir), fs_ops)
        if tuple(reread.keys()) != ("payload", "payload_sha256"):
            raise IOError("terminal evidence wrapper key order invalid")
        if reread["payload_sha256"] != schema.sha256_hex(
                schema.canonical_json_bytes(reread["payload"])):
            raise IOError("terminal evidence payload digest mismatch")
    except Exception as exc:
        raise EvidenceUpdateFailedAfterConsumption(_safe_detail(exc), last_verified_state)


def _fallback_evidence_line(last_state: Mapping[str, Any]) -> bytes:
    line = (
        "%s last_verified_phase=%s authority_consumed=true "
        "manifest_contact_attempt_count=%s manifest_read_success_count=%s exit=4\n"
    ) % (
        FAIL_EVIDENCE_UPDATE_AFTER_CONSUMPTION,
        last_state.get("phase"),
        last_state.get("manifest_contact_attempt_count"),
        last_state.get("manifest_read_success_count"),
    )
    return line.encode("utf-8")


def _terminalize_failure(config: BoundedRunConfig,
                         state: Mapping[str, Any],
                         terminal_status: str,
                         failure_category: str,
                         failure_code: str,
                         failure_stage: str,
                         exit_code: int,
                         detail: str = "",
                         controlled: bool = False,
                         scientific_reached: bool = False,
                         descriptor_reached: bool = False,
                         final_available: bool = False,
                         publication_status: str = "NO_SCIENTIFIC_PUBLICATION_OPERATIONAL_EVIDENCE_RETAINED",
                         staging_status: str = "NOT_CREATED") -> RunOutcome:
    payload = _terminal_payload(
        state,
        config.repository_state,
        terminal_status,
        failure_category,
        failure_code,
        failure_stage,
        exit_code,
        controlled,
        CONTROLLED_KIND_INVALID if controlled else None,
        False,
        None,
        scientific_reached,
        descriptor_reached,
        final_available,
        publication_status,
        staging_status,
        config.clock(),
        {"bounded_diagnostic": detail[:180]},
    )
    try:
        _write_terminal_evidence(
            config.paths.execution_journal_dir,
            payload,
            config.fs_ops,
            state,
            config.simulate_terminal_evidence_failure,
        )
    except EvidenceUpdateFailedAfterConsumption as exc:
        fallback = _fallback_evidence_line(exc.last_verified_state)
        return RunOutcome(
            EXIT_CONSUMED_INFRASTRUCTURE_FAILURE,
            stderr=fallback,
            authority_consumed=True,
            terminal_status=TERMINAL_STATUS_FAILED_EVIDENCE_UPDATE,
            failure_code=FAIL_EVIDENCE_UPDATE_AFTER_CONSUMPTION,
            terminal_evidence_written=False,
            last_verified_durable_state=exc.last_verified_state,
        )
    return RunOutcome(
        exit_code,
        authority_consumed=True,
        terminal_status=terminal_status,
        failure_code=failure_code,
        controlled_outcome_kind=CONTROLLED_KIND_INVALID if controlled else None,
        scientific_evaluation_reached=scientific_reached,
        descriptor_evaluation_reached=descriptor_reached,
        final_publication_available=final_available,
        terminal_evidence_written=True,
        last_verified_durable_state=dict(state),
    )


def run_bounded_validation(config: BoundedRunConfig) -> RunOutcome:
    if not config.precontact_authorized:
        return RunOutcome(
            EXIT_PRECONTACT_REFUSAL,
            stderr=b"SYNTHETIC_VALIDATION_REFUSED PRECONTACT_AUTHORIZATION_REFUSED\n",
            authority_consumed=False,
            terminal_status=TERMINAL_STATUS_REFUSED_PRE_CONTACT,
            failure_code=FAIL_PRECONTACT_AUTHORIZATION,
        )

    try:
        arm_result = arm_authority(config.paths, config.fs_ops)
    except PreContactRefusal as exc:
        return RunOutcome(
            EXIT_PRECONTACT_REFUSAL,
            stderr=("SYNTHETIC_VALIDATION_REFUSED %s\n" % exc.failure_code).encode("utf-8"),
            authority_consumed=False,
            terminal_status=TERMINAL_STATUS_REFUSED_PRE_CONTACT,
            failure_code=exc.failure_code,
        )

    state = dict(arm_result.state)
    try:
        pass_bundle, state = run_two_pass_validation(
            config.paths.execution_journal_dir,
            state,
            config,
        )
        state = _replace_state_phase(
            config.paths.execution_journal_dir,
            state,
            PHASE_RESULT_CONSTRUCTING,
            config.fs_ops,
        )
        if config.simulate_result_construction_failure:
            raise PublicationFailure(FAIL_RESULT_CONSTRUCTION,
                                     "simulated result construction failure")
        result_kind = pass_bundle["scientific_result_kind"]
        artifacts = _result_artifacts(result_kind, pass_bundle, state, config.repository_state)
        state = _replace_state_phase(
            config.paths.execution_journal_dir,
            state,
            PHASE_STAGING_WRITING,
            config.fs_ops,
        )
        state = _replace_state_phase(
            config.paths.execution_journal_dir,
            state,
            PHASE_STAGING_VERIFYING,
            config.fs_ops,
        )
        state = _replace_state_phase(
            config.paths.execution_journal_dir,
            state,
            PHASE_PROMOTING,
            config.fs_ops,
        )
        publish_scientific_artifacts(
            config.paths,
            artifacts,
            config.fs_ops,
            config.simulate_staging_write_failure,
            config.simulate_staging_verification_failure,
            config.simulate_promotion_failure,
            config.simulate_final_verification_failure,
        )
        state = _replace_state_phase(
            config.paths.execution_journal_dir,
            state,
            PHASE_FINAL_VERIFICATION,
            config.fs_ops,
        )
        state = _replace_state_phase(
            config.paths.execution_journal_dir,
            state,
            PHASE_COMPLETE,
            config.fs_ops,
        )
        exit_code = EXIT_PUBLISHED_PASS if result_kind == RESULT_KIND_PASSED else EXIT_PUBLISHED_FAIL
        payload = _terminal_payload(
            state,
            config.repository_state,
            TERMINAL_STATUS_COMPLETE,
            None,
            None,
            None,
            exit_code,
            False,
            None,
            True,
            result_kind,
            True,
            True,
            True,
            "PUBLISHED",
            "PROMOTED",
            config.clock(),
        )
        _write_terminal_evidence(
            config.paths.execution_journal_dir,
            payload,
            config.fs_ops,
            state,
            config.simulate_terminal_evidence_failure,
        )
        return RunOutcome(
            exit_code,
            stdout=("scientific_result_kind=%s\n" % result_kind).encode("utf-8"),
            authority_consumed=True,
            terminal_status=TERMINAL_STATUS_COMPLETE,
            scientific_result_kind=result_kind,
            scientific_evaluation_reached=True,
            descriptor_evaluation_reached=True,
            final_publication_available=True,
            terminal_evidence_written=True,
            last_verified_durable_state=dict(state),
        )
    except ControlledInvalidity as exc:
        return _terminalize_failure(
            config,
            _read_current_state(config.paths.execution_journal_dir, config.fs_ops),
            TERMINAL_STATUS_INVALID_POST_CONTACT,
            "controlled_invalidity",
            exc.failure_code,
            "post_contact_validation",
            EXIT_CONTROLLED_INVALID,
            exc.detail,
            controlled=True,
            publication_status="NO_SCIENTIFIC_PUBLICATION_OPERATIONAL_EVIDENCE_RETAINED",
            staging_status="NOT_CREATED",
        )
    except EvidenceUpdateFailedAfterConsumption as exc:
        return RunOutcome(
            EXIT_CONSUMED_INFRASTRUCTURE_FAILURE,
            stderr=_fallback_evidence_line(exc.last_verified_state),
            authority_consumed=True,
            terminal_status=TERMINAL_STATUS_FAILED_EVIDENCE_UPDATE,
            failure_code=FAIL_EVIDENCE_UPDATE_AFTER_CONSUMPTION,
            terminal_evidence_written=False,
            last_verified_durable_state=exc.last_verified_state,
        )
    except PublicationFailure as exc:
        return _terminalize_failure(
            config,
            _read_current_state(config.paths.execution_journal_dir, config.fs_ops),
            TERMINAL_STATUS_PUBLICATION_FAILURE,
            "publication_failure",
            exc.failure_code,
            exc.stage,
            EXIT_CONSUMED_PUBLICATION_FAILURE,
            exc.detail,
            scientific_reached=True,
            descriptor_reached=True,
            publication_status="FAILED",
            staging_status="RETAINED_OR_NOT_CREATED",
        )
    except ConsumedInfrastructureFailure as exc:
        return _terminalize_failure(
            config,
            _read_current_state(config.paths.execution_journal_dir, config.fs_ops),
            TERMINAL_STATUS_OPERATIONAL_FAILURE,
            "infrastructure_failure",
            exc.failure_code,
            exc.stage,
            EXIT_CONSUMED_INFRASTRUCTURE_FAILURE,
            exc.detail,
        )
    except Exception as exc:
        return _terminalize_failure(
            config,
            _read_current_state(config.paths.execution_journal_dir, config.fs_ops),
            TERMINAL_STATUS_OPERATIONAL_FAILURE,
            "implementation_failure",
            FAIL_POSTCONTACT_IMPLEMENTATION_EXCEPTION,
            "post_contact",
            EXIT_CONSUMED_INFRASTRUCTURE_FAILURE,
            _safe_detail(exc),
        )


def _is_lower_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and all(
        character in "0123456789abcdef" for character in value
    )


def _binding_failure(detail: str) -> PreContactRefusal:
    return PreContactRefusal(FAIL_PRECONTACT_AUTHORIZATION, detail)


def _is_key_token(value: str) -> bool:
    if not value:
        return False
    return all(
        character == "_" or character.isalpha() or character.isdigit()
        for character in value
    )


def _outside_binding_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped in (BINDING_BEGIN, BINDING_END):
        return True
    key, separator, _value = stripped.partition("=")
    if separator != "=":
        return False
    key = key.strip()
    if key in BINDING_FIELDS or key == "authorization_schema":
        return True
    return _is_key_token(key)


def parse_authorization_binding(document_bytes: bytes) -> Dict[str, str]:
    if not isinstance(document_bytes, (bytes, bytearray)):
        raise _binding_failure("authorization document is not bytes")
    try:
        text = bytes(document_bytes).decode("utf-8")
    except UnicodeDecodeError:
        raise _binding_failure("authorization document is not UTF-8")
    if "\r" in text:
        raise _binding_failure("authorization document contains CR")
    lines = text.split("\n")
    begins = [index for index, line in enumerate(lines) if line == BINDING_BEGIN]
    ends = [index for index, line in enumerate(lines) if line == BINDING_END]
    if len(begins) != 1:
        raise _binding_failure("binding begin marker missing or duplicated")
    if len(ends) != 1:
        raise _binding_failure("binding end marker missing or duplicated")
    if ends[0] <= begins[0]:
        raise _binding_failure("binding markers out of order")
    outside = lines[:begins[0]] + lines[ends[0] + 1:]
    if any(_outside_binding_line(line) for line in outside):
        raise _binding_failure("binding-like content outside block")
    body = lines[begins[0] + 1:ends[0]]
    if len(body) != len(BINDING_FIELDS):
        raise _binding_failure("binding field count invalid")
    parsed: Dict[str, str] = {}
    for index, line in enumerate(body):
        if line != line.strip() or line.count("=") != 1:
            raise _binding_failure("binding line malformed")
        key, _separator, value = line.partition("=")
        if key != BINDING_FIELDS[index]:
            raise _binding_failure("binding key order invalid")
        if key in parsed:
            raise _binding_failure("binding key duplicated")
        if value != value.strip() or value == "":
            raise _binding_failure("binding value invalid")
        parsed[key] = value
    if parsed["authorization_schema"] != BINDING_SCHEMA:
        raise _binding_failure("authorization schema invalid")
    if parsed["authorization_version"] != BINDING_VERSION:
        raise _binding_failure("authorization version invalid")
    for key in _HEX40_FIELDS:
        if not _is_lower_hex(parsed[key], 40):
            raise _binding_failure("%s is not lowercase 40-hex" % key)
    for key in _HEX64_FIELDS:
        if not _is_lower_hex(parsed[key], 64):
            raise _binding_failure("%s is not lowercase 64-hex" % key)
    return parsed


def authorization_identity_payload(binding: Mapping[str, str]) -> Dict[str, Any]:
    payload = {
        "domain_label": AUTHORIZATION_IDENTITY_DOMAIN_LABEL,
        "authorization_document_path": AUTHORIZATION_DOCUMENT_PATH,
        "begin_marker": BINDING_BEGIN,
        "end_marker": BINDING_END,
        "field_order_without_later_execution_authorization_identity": list(
            AUTHORIZATION_IDENTITY_FIELD_ORDER
        ),
        "authorization_schema": BINDING_SCHEMA,
        "authorization_version": BINDING_VERSION,
        "runner_path": RUNNER_SOURCE_PATH,
        "runner_git_blob": binding["runner_git_blob"],
        "runner_raw_sha256": binding["runner_raw_sha256"],
        "runner_test_path": RUNNER_TEST_SOURCE_PATH,
        "runner_test_git_blob": binding["runner_test_git_blob"],
        "runner_test_raw_sha256": binding["runner_test_raw_sha256"],
        "schema_contract_path": SCHEMA_CONTRACT_SOURCE_PATH,
        "schema_contract_git_blob": binding["schema_contract_git_blob"],
        "schema_contract_raw_sha256": binding["schema_contract_raw_sha256"],
        "v0_2_configuration_identity": binding["v0_2_configuration_identity"],
        "expected_manifest_external_sha256": binding["expected_manifest_external_sha256"],
        "expected_manifest_payload_sha256": binding["expected_manifest_payload_sha256"],
    }
    if tuple(payload.keys()) != AUTHORIZATION_IDENTITY_PAYLOAD_FIELDS:
        raise PreContactRefusal(FAIL_PRECONTACT_AUTHORIZATION, "authorization payload order invalid")
    return payload


def canonical_authorization_identity_bytes(binding: Mapping[str, str]) -> bytes:
    text = json.dumps(
        authorization_identity_payload(binding),
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
        sort_keys=False,
    )
    return text.encode("utf-8") + b"\n"


def authorization_binding_identity(binding: Mapping[str, str]) -> str:
    return hashlib.sha256(canonical_authorization_identity_bytes(binding)).hexdigest()


def _verify_runner_owned_anchors(binding: Mapping[str, str]) -> None:
    expected = (
        ("v0_2_configuration_identity", EXPECTED_V0_2_CONFIGURATION_IDENTITY),
        ("expected_manifest_external_sha256", EXPECTED_MANIFEST_EXTERNAL_SHA256),
        ("expected_manifest_payload_sha256", EXPECTED_MANIFEST_PAYLOAD_SHA256),
    )
    for key, value in expected:
        if binding.get(key) != value:
            raise PreContactRefusal(
                FAIL_PRECONTACT_IDENTITY,
                "%s does not match runner-owned anchor" % key,
            )


def _verify_authorization_binding_identity(binding: Mapping[str, str]) -> None:
    if binding.get("later_execution_authorization_identity") != authorization_binding_identity(binding):
        raise PreContactRefusal(
            FAIL_PRECONTACT_AUTHORIZATION,
            "later execution authorization identity mismatch",
        )


def _decode_git_single_line(payload: bytes) -> str:
    text = payload.decode("utf-8", "replace")
    if text.endswith("\r\n"):
        text = text[:-2]
    elif text.endswith("\n"):
        text = text[:-1]
    if "\r" in text or "\n" in text:
        raise PreContactRefusal(FAIL_PRECONTACT_REPOSITORY_STATE, "git output is not one line")
    return text


def _run_git(args: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git"] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise PreContactRefusal(
            FAIL_PRECONTACT_REPOSITORY_STATE,
            completed.stderr.decode("utf-8", "replace").strip()[:180],
        )
    return _decode_git_single_line(completed.stdout)


def _run_git_status_porcelain() -> str:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise PreContactRefusal(
            FAIL_PRECONTACT_REPOSITORY_STATE,
            completed.stderr.decode("utf-8", "replace").strip()[:180],
        )
    return completed.stdout.decode("utf-8", "replace")


def _repository_path(repository_root: str, relative_path: str) -> str:
    if os.path.isabs(relative_path):
        raise PreContactRefusal(FAIL_PRECONTACT_BOUNDARY, "repository path is absolute")
    normalized_relative = relative_path.replace("/", os.sep)
    candidate = os.path.abspath(os.path.join(repository_root, normalized_relative))
    root_abs = os.path.abspath(repository_root)
    root_real = os.path.normcase(os.path.realpath(root_abs))
    candidate_real = os.path.normcase(os.path.realpath(candidate))
    try:
        if os.path.commonpath([root_real, candidate_real]) != root_real:
            raise PreContactRefusal(FAIL_PRECONTACT_BOUNDARY, "repository path escapes root")
    except ValueError:
        raise PreContactRefusal(FAIL_PRECONTACT_BOUNDARY, "repository path drive mismatch")
    return candidate


def _read_repository_file_bytes(repository_root: str, relative_path: str) -> bytes:
    path = _repository_path(repository_root, relative_path)
    if not os.path.isfile(path):
        raise PreContactRefusal(FAIL_PRECONTACT_BOUNDARY, "%s is not a regular file" % relative_path)
    with open(path, "rb") as handle:
        return handle.read()


def _raw_sha256_for_path(repository_root: str, relative_path: str) -> str:
    return hashlib.sha256(_read_repository_file_bytes(repository_root, relative_path)).hexdigest()


def _git_blob_for_path(relative_path: str) -> str:
    blob = _run_git(["rev-parse", "HEAD:%s" % relative_path])
    if not _is_lower_hex(blob, 40):
        raise PreContactRefusal(FAIL_PRECONTACT_IDENTITY, "%s Git blob malformed" % relative_path)
    return blob


def _latest_commit_for_authorization_path() -> str:
    latest = _run_git(["log", "-1", "--format=%H", "--", AUTHORIZATION_DOCUMENT_PATH])
    if not _is_lower_hex(latest, 40):
        raise PreContactRefusal(
            FAIL_PRECONTACT_AUTHORIZATION,
            "authorization path history missing",
        )
    return latest


def _validate_repository_root(repository_root: str) -> None:
    if not repository_root or not os.path.exists(os.path.join(repository_root, ".git")):
        raise PreContactRefusal(FAIL_PRECONTACT_REPOSITORY_STATE, "unsupported repository root")
    for relative_path in (
            AUTHORIZATION_DOCUMENT_PATH,
            RUNNER_SOURCE_PATH,
            RUNNER_TEST_SOURCE_PATH,
            SCHEMA_CONTRACT_SOURCE_PATH):
        _repository_path(repository_root, relative_path)


def _verify_latest_authorization_commit(state: RepositoryState) -> None:
    latest = _latest_commit_for_authorization_path()
    if latest != state.head:
        raise PreContactRefusal(
            FAIL_PRECONTACT_AUTHORIZATION,
            "authorization path latest commit is not HEAD",
        )


def _verify_implementation_identities(repository_root: str,
                                      binding: Mapping[str, str]) -> None:
    for label, relative_path, blob_key in _IMPLEMENTATION_IDENTITY_PATHS:
        raw_key = blob_key.replace("_git_blob", "_raw_sha256")
        observed_blob = _git_blob_for_path(relative_path)
        observed_raw = _raw_sha256_for_path(repository_root, relative_path)
        if observed_blob != binding[blob_key]:
            raise PreContactRefusal(FAIL_PRECONTACT_IDENTITY, "%s Git blob mismatch" % label)
        if observed_raw != binding[raw_key]:
            raise PreContactRefusal(FAIL_PRECONTACT_IDENTITY, "%s raw SHA-256 mismatch" % label)


def _reject_authoritative_overrides(argv: Sequence[str], stdin_bytes: bytes) -> None:
    if len(argv) != 1:
        raise PreContactRefusal(FAIL_PRECONTACT_CLI, "unexpected CLI arguments")
    if stdin_bytes:
        raise PreContactRefusal(FAIL_PRECONTACT_STDIN, "stdin is not empty")
    for name in _PROHIBITED_AUTHORIZATION_ENVIRONMENT_NAMES:
        if name in os.environ:
            raise PreContactRefusal(
                FAIL_PRECONTACT_AUTHORIZATION,
                "authorization environment override is prohibited",
            )


def _validate_identity_seam(identities: Mapping[str, str]) -> Dict[str, str]:
    parsed = dict(identities)
    for name in BINDING_FIELDS:
        if name not in parsed or parsed[name] == UNBOUND:
            raise PreContactRefusal(FAIL_PRECONTACT_IDENTITY, "%s is UNBOUND" % name)
    _verify_runner_owned_anchors(parsed)
    return parsed


def _load_authorization_identities(repository_root: str,
                                   state: RepositoryState) -> Dict[str, str]:
    document_bytes = _read_repository_file_bytes(repository_root, AUTHORIZATION_DOCUMENT_PATH)
    binding = parse_authorization_binding(document_bytes)
    _verify_runner_owned_anchors(binding)
    _verify_authorization_binding_identity(binding)
    _verify_latest_authorization_commit(state)
    _verify_implementation_identities(repository_root, binding)
    return binding


def observe_repository_state() -> RepositoryState:
    root = _run_git(["rev-parse", "--show-toplevel"])
    branch = _run_git(["symbolic-ref", "--short", "HEAD"])
    clean = _run_git_status_porcelain() == ""
    head = _run_git(["rev-parse", "HEAD"])
    origin_main = _run_git(["rev-parse", "origin/main"])
    python_version = "%d.%d.%d" % sys.version_info[:3]
    return RepositoryState(root, branch, clean, head, origin_main, python_version)


def perform_precontact_validation(argv: Sequence[str],
                                  stdin_bytes: bytes,
                                  repository_state: Optional[RepositoryState] = None,
                                  identities: Optional[Mapping[str, str]] = None,
                                  paths: Optional[ExecutionPaths] = None
                                  ) -> PreContactContext:
    paths = default_authoritative_paths() if paths is None else paths
    _reject_authoritative_overrides(argv, stdin_bytes)
    state = repository_state if repository_state is not None else observe_repository_state()
    _validate_repository_root(state.repository_root)
    if state.branch != "main" or not state.clean or state.head != state.origin_main:
        raise PreContactRefusal(FAIL_PRECONTACT_REPOSITORY_STATE, "repository not synchronized")
    if not _is_lower_hex(state.head, 40) or not _is_lower_hex(state.origin_main, 40):
        raise PreContactRefusal(FAIL_PRECONTACT_REPOSITORY_STATE, "repository HEAD malformed")
    if state.python_version != "3.11.15":
        raise PreContactRefusal(FAIL_PRECONTACT_REPOSITORY_STATE, "unsupported Python version")

    authorized_identities = (
        _load_authorization_identities(state.repository_root, state)
        if identities is None
        else _validate_identity_seam(identities)
    )
    if schema.FIXED_MEMBER_BINARY_KEYS != (
            schema.FIXED_FIXTURE_KEYS[4],
            schema.FIXED_FIXTURE_KEYS[5],
    ):
        raise PreContactRefusal(FAIL_PRECONTACT_SCHEMA_CONTRACT, "fixed field contract invalid")
    if schema.ACCEPTED_MEMBER_BINARY_KEYS != (
            schema.ACCEPTED_FIXTURE_KEYS[7],
            schema.ACCEPTED_FIXTURE_KEYS[8],
    ):
        raise PreContactRefusal(FAIL_PRECONTACT_SCHEMA_CONTRACT, "accepted field contract invalid")
    for output_path in (
            paths.execution_arming_path,
            paths.execution_journal_dir,
            paths.scientific_result_staging_dir,
            paths.final_publication_dir):
        if os.path.exists(output_path):
            raise PreContactRefusal(
                FAIL_PRECONTACT_OUTPUT_PATH_PRESENT,
                "%s already exists" % output_path,
            )
    if RETAINED_V0_1_STAGING_DIR in (
            paths.execution_arming_path,
            paths.execution_journal_dir,
            paths.scientific_result_staging_dir,
            paths.final_publication_dir):
        raise PreContactRefusal(FAIL_PRECONTACT_BOUNDARY, "v0.1 staging path reused")
    return PreContactContext(state, authorized_identities)


def authoritative_manifest_reader(manifest_path: str = EXPECTED_MANIFEST_PATH
                                  ) -> Callable[[int], bytes]:
    def read_manifest_bytes(_pass_index: int) -> bytes:
        with open(manifest_path, "rb") as handle:
            return handle.read()
    return read_manifest_bytes


def construct_authoritative_run_config(
        repository_state: RepositoryState,
        identities: Mapping[str, str] = AUTHORITATIVE_IDENTITIES,
        paths: Optional[ExecutionPaths] = None) -> BoundedRunConfig:
    paths = default_authoritative_paths() if paths is None else paths
    return BoundedRunConfig(
        paths=paths,
        read_manifest_bytes=authoritative_manifest_reader(EXPECTED_MANIFEST_PATH),
        repository_state=repository_state,
        descriptor_callable=default_descriptor_callable,
        raw_signature_callable=descriptor.raw_labeled_signature,
        affine_signature_callable=descriptor.affine_only_signature,
        descriptor_result_callable=descriptor.descriptor_result,
        fs_ops=FileSystemOps(),
        expected_external_manifest_sha256=identities["expected_manifest_external_sha256"],
        expected_manifest_payload_sha256=identities["expected_manifest_payload_sha256"],
        expected_freeze_configuration_sha256=schema.FROZEN_CONFIGURATION_SHA256,
        precontact_authorized=True,
    )


def run_authoritative(argv: Optional[Sequence[str]] = None,
                      stdin_bytes: bytes = b"",
                      repository_state: Optional[RepositoryState] = None,
                      identities: Optional[Mapping[str, str]] = None,
                      paths: Optional[ExecutionPaths] = None) -> RunOutcome:
    argv = list(sys.argv if argv is None else argv)
    paths = default_authoritative_paths() if paths is None else paths
    try:
        precontact = perform_precontact_validation(
            argv,
            stdin_bytes,
            repository_state=repository_state,
            identities=identities,
            paths=paths,
        )
    except PreContactRefusal as exc:
        return RunOutcome(
            EXIT_PRECONTACT_REFUSAL,
            stderr=("SYNTHETIC_VALIDATION_REFUSED %s\n" % exc.failure_code).encode("utf-8"),
            authority_consumed=False,
            terminal_status=TERMINAL_STATUS_REFUSED_PRE_CONTACT,
            failure_code=exc.failure_code,
        )
    config = construct_authoritative_run_config(
        precontact.repository_state,
        precontact.identities,
        paths,
    )
    return run_bounded_validation(config)


def main() -> int:
    stdin_bytes = sys.stdin.buffer.read()
    outcome = run_authoritative(sys.argv, stdin_bytes)
    if outcome.stdout:
        sys.stdout.buffer.write(outcome.stdout)
    if outcome.stderr:
        sys.stderr.buffer.write(outcome.stderr)
    return outcome.exit_code


if __name__ == "__main__":  # pragma: no cover - authoritative CLI not used by tests
    raise SystemExit(main())
