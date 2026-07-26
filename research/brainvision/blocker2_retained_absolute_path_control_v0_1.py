"""Retained harness for BLOCKER-2 absolute-path validation.

This module is intentionally narrower than the existing ephemeral A-matrix.  It
binds a consumed gate, a selected retained case set, source identities, and a
canonical evidence chain.  Authoritative retained execution is reachable only
through a complete identity-bound authorization block.
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
RETAINED_GLOBAL_AUTHORITY_ENTRY_SCHEMA = (
    "torment.brainvision.blocker2.retained.global_authority_entry.v0.1"
)
RETAINED_RUN_RESULT_SCHEMA = "torment.brainvision.blocker2.retained.run_result.v0.1"
RETAINED_COMPLETION_SCHEMA = "torment.brainvision.blocker2.retained.completion.v0.1"
RETAINED_CASE_ENVELOPE_SCHEMA = (
    "torment.brainvision.blocker2.retained.case_envelope.v0.1"
)
RETAINED_AUTHORITY_REGISTRY_PROFILE_SCHEMA = (
    "torment.brainvision.blocker2.retained.authority_registry_profile.v0.1"
)
RETAINED_EVIDENCE_CHAIN_SCHEMA = (
    "torment.brainvision.blocker2.retained.evidence_chain.v0.1"
)
RETAINED_TERMINAL_RECORD_SCHEMA = RETAINED_RUN_RESULT_SCHEMA
RETAINED_TERMINAL_ARTIFACT_SCHEMA = RETAINED_RUN_RESULT_SCHEMA
RETAINED_REPOSITORY_STATE_SCHEMA = (
    "torment.brainvision.blocker2.retained.repository_state.v0.1"
)
RETAINED_SOURCE_IDENTITY_SCHEMA = (
    "torment.brainvision.blocker2.retained.source_identity.v0.1"
)
RETAINED_FIXTURE_PROFILE_SCHEMA = (
    "torment.brainvision.blocker2.retained.fixture_profile.v0.1"
)
RETAINED_EXECUTION_AUTHORIZATION_IDENTITY_SCHEMA = (
    "torment.brainvision.blocker2.retained.execution_authorization_identity.v0.2"
)
RETAINED_EXECUTION_AUTHORIZATION_IDENTITY_BLOCK_SCHEMA = (
    "torment.brainvision.blocker2.retained."
    "execution_authorization_identity_block.v0.2"
)
RETAINED_RUN_IDENTITY_SCHEMA = (
    "torment.brainvision.blocker2.retained.run_identity.v0.2"
)
RETAINED_RESULT_DIRECTORY_DERIVATION_RULE_SCHEMA = (
    "torment.brainvision.blocker2.retained."
    "result_directory_derivation_rule.v0.1"
)
RESULT_DIRECTORY_DERIVATION_RULE = (
    "result_directory = result_parent / execution_authorization_identity"
)
OPERATOR_WRAPPER_AUTHORIZATION_INPUT_SCHEMA = (
    "torment.brainvision.blocker2.operator_wrapper.authorization_input.v0.2"
)
OPERATOR_WRAPPER_AUTHORIZATION_INPUT_DECLARATION_SCHEMA = (
    "torment.brainvision.blocker2.operator_wrapper."
    "authorization_input_declaration.v0.2"
)
OPERATOR_WRAPPER_IDENTITY_SCHEMA = (
    "torment.brainvision.blocker2.operator_wrapper.identity.v0.1"
)
OPERATOR_WRAPPER_VERSION = "v0.2"
OPERATOR_IDENTITY = "Hilmir"
SINGLE_PROCESS_DECLARATION = "one Windows Command Prompt process"
SINGLE_ATTEMPT_DECLARATION = "one authoritative attempt"
REAL_EXECUTOR_SELECTOR = "REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1"
IDENTITY_DERIVATION_CYCLE_CORRECTION_AUTHORIZATION_SHA256 = (
    "a8da21fc9884299d847b7cc29ba877987bc11c06baa77cbd9ebe10ad63e0aa68"
)

GLOBAL_AUTHORITY_ENTRY_SUFFIX = ".global_authority_entry.canonical.json"
GATE_ENTRY_FILENAME = "gate_entry.canonical.json"
RUN_RESULT_FILENAME = "run_result.canonical.json"
RETAINED_COMPLETION_FILENAME = "retained_completion.canonical.json"
TERMINAL_ARTIFACT_FILENAME = RUN_RESULT_FILENAME

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
GLOBAL_AUTHORITY_ENTRY_EXISTS = "GLOBAL_AUTHORITY_ENTRY_EXISTS"
GLOBAL_AUTHORITY_ENTRY_PERSISTENCE_FAILURE = (
    "GLOBAL_AUTHORITY_ENTRY_PERSISTENCE_FAILURE"
)
GLOBAL_AUTHORITY_ENTRY_REVERIFY_FAILURE = "GLOBAL_AUTHORITY_ENTRY_REVERIFY_FAILURE"
GLOBAL_AUTHORITY_IDENTITY_MISMATCH = "GLOBAL_AUTHORITY_IDENTITY_MISMATCH"
LOCAL_GATE_LINKAGE_FAILURE = "LOCAL_GATE_LINKAGE_FAILURE"
RUN_RESULT_SERIALIZATION_FAILURE = "RUN_RESULT_SERIALIZATION_FAILURE"
RUN_RESULT_PERSISTENCE_FAILURE = "RUN_RESULT_PERSISTENCE_FAILURE"
RUN_RESULT_REVERIFY_FAILURE = "RUN_RESULT_REVERIFY_FAILURE"
RETAINED_COMPLETION_PRECONDITION_FAILURE = (
    "RETAINED_COMPLETION_PRECONDITION_FAILURE"
)
RETAINED_COMPLETION_SERIALIZATION_FAILURE = (
    "RETAINED_COMPLETION_SERIALIZATION_FAILURE"
)
RETAINED_COMPLETION_PERSISTENCE_FAILURE = (
    "RETAINED_COMPLETION_PERSISTENCE_FAILURE"
)
RETAINED_COMPLETION_REVERIFY_FAILURE = "RETAINED_COMPLETION_REVERIFY_FAILURE"
EVIDENCE_CHAIN_LINKAGE_FAILURE = "EVIDENCE_CHAIN_LINKAGE_FAILURE"
NATIVE_HELPER_POLICY_MISMATCH = "NATIVE_HELPER_POLICY_MISMATCH"
RETAINED_POLICY_MISMATCH = "RETAINED_POLICY_MISMATCH"
CROSS_LOCATION_REPLAY_REJECTED = "CROSS_LOCATION_REPLAY_REJECTED"
AUTHORITATIVE_AUTHORIZATION_MISSING = "AUTHORITATIVE_AUTHORIZATION_MISSING"
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
        GLOBAL_AUTHORITY_ENTRY_EXISTS,
        GLOBAL_AUTHORITY_ENTRY_PERSISTENCE_FAILURE,
        GLOBAL_AUTHORITY_ENTRY_REVERIFY_FAILURE,
        GLOBAL_AUTHORITY_IDENTITY_MISMATCH,
        LOCAL_GATE_LINKAGE_FAILURE,
        RUN_RESULT_SERIALIZATION_FAILURE,
        RUN_RESULT_PERSISTENCE_FAILURE,
        RUN_RESULT_REVERIFY_FAILURE,
        RETAINED_COMPLETION_PRECONDITION_FAILURE,
        RETAINED_COMPLETION_SERIALIZATION_FAILURE,
        RETAINED_COMPLETION_PERSISTENCE_FAILURE,
        RETAINED_COMPLETION_REVERIFY_FAILURE,
        EVIDENCE_CHAIN_LINKAGE_FAILURE,
        NATIVE_HELPER_POLICY_MISMATCH,
        RETAINED_POLICY_MISMATCH,
        CROSS_LOCATION_REPLAY_REJECTED,
        AUTHORITATIVE_AUTHORIZATION_MISSING,
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
RETAINED_RUN_ASSESSMENT_SHA256 = (
    "71b4e96da222461c16caea6494719183504e758b6e883b44c4db8df9b636f51d"
)
IMPLEMENTATION_PREPARATION_AUTHORIZATION_SHA256 = (
    "0ea41794b6d6503576afa84a14f629ca25baff5b7d78c0a2f8a4bbb806d1959e"
)
RUNTIME_CORRECTION_AUTHORIZATION_SHA256 = (
    "6e593ca45773f8fab880ba3cf3209dcd8db1e6e9dcf17bf1f2c6d69535a29a92"
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

REQUIRED_SOURCE_IDENTITY_PATHS = tuple(sorted(AUTHORIZED_SURFACE_PATHS))

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
        (
            "docs/"
            "TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_"
            "POST_COMMIT_IDENTITY_BINDING_AND_EXECUTION_READINESS_ASSESSMENT_v0.1.md"
        ),
        (
            "docs/"
            "TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_"
            "POST_COMMIT_RUNTIME_CORRECTION_AUTHORIZATION_v0.1.md"
        ),
        (
            "docs/"
            "TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_"
            "IDENTITY_DERIVATION_CYCLE_CORRECTION_AUTHORIZATION_v0.1.md"
        ),
    }
)

FAULT_BEFORE_GLOBAL_AUTHORITY_WRITE = "before_global_authority_write"
FAULT_DURING_GLOBAL_AUTHORITY_FILE_WRITE = "during_global_authority_file_write"
FAULT_DURING_GLOBAL_AUTHORITY_DIRECTORY_SYNC = (
    "during_global_authority_directory_sync"
)
FAULT_DURING_GLOBAL_AUTHORITY_REREAD = "during_global_authority_reread"
FAULT_AFTER_GLOBAL_AUTHORITY_VERIFICATION_BEFORE_LOCAL_GATE = (
    "after_global_authority_verification_before_local_gate"
)
FAULT_BEFORE_GATE_WRITE = "before_gate_write"
FAULT_DURING_GATE_FILE_WRITE = "during_gate_file_write"
FAULT_DURING_GATE_DIRECTORY_SYNC = "during_gate_directory_sync"
FAULT_DURING_GATE_REREAD = "during_gate_reread"
FAULT_AFTER_VERIFIED_GATE_BEFORE_NATIVE = "after_verified_gate_before_native"
FAULT_AFTER_NATIVE_BEFORE_RUN_RESULT = "after_native_before_run_result"
FAULT_DURING_RUN_RESULT_SERIALIZATION = "during_run_result_serialization"
FAULT_DURING_RUN_RESULT_FILE_WRITE = "during_run_result_file_write"
FAULT_DURING_RUN_RESULT_DIRECTORY_SYNC = "during_run_result_directory_sync"
FAULT_DURING_RUN_RESULT_REREAD = "during_run_result_reread"
FAULT_BEFORE_RETAINED_COMPLETION_CREATION = "before_retained_completion_creation"
FAULT_DURING_COMPLETION_SERIALIZATION = "during_completion_serialization"
FAULT_DURING_COMPLETION_FILE_WRITE = "during_completion_file_write"
FAULT_DURING_COMPLETION_DIRECTORY_SYNC = "during_completion_directory_sync"
FAULT_DURING_COMPLETION_REREAD = "during_completion_reread"
FAULT_DURING_TERMINAL_FILE_WRITE = "during_terminal_file_write"
FAULT_DURING_TERMINAL_DIRECTORY_SYNC = "during_terminal_directory_sync"
FAULT_DURING_TERMINAL_REREAD = "during_terminal_reread"

FAULT_POINTS = frozenset(
    {
        FAULT_BEFORE_GLOBAL_AUTHORITY_WRITE,
        FAULT_DURING_GLOBAL_AUTHORITY_FILE_WRITE,
        FAULT_DURING_GLOBAL_AUTHORITY_DIRECTORY_SYNC,
        FAULT_DURING_GLOBAL_AUTHORITY_REREAD,
        FAULT_AFTER_GLOBAL_AUTHORITY_VERIFICATION_BEFORE_LOCAL_GATE,
        FAULT_BEFORE_GATE_WRITE,
        FAULT_DURING_GATE_FILE_WRITE,
        FAULT_DURING_GATE_DIRECTORY_SYNC,
        FAULT_DURING_GATE_REREAD,
        FAULT_AFTER_VERIFIED_GATE_BEFORE_NATIVE,
        FAULT_AFTER_NATIVE_BEFORE_RUN_RESULT,
        FAULT_DURING_RUN_RESULT_SERIALIZATION,
        FAULT_DURING_RUN_RESULT_FILE_WRITE,
        FAULT_DURING_RUN_RESULT_DIRECTORY_SYNC,
        FAULT_DURING_RUN_RESULT_REREAD,
        FAULT_BEFORE_RETAINED_COMPLETION_CREATION,
        FAULT_DURING_COMPLETION_SERIALIZATION,
        FAULT_DURING_COMPLETION_FILE_WRITE,
        FAULT_DURING_COMPLETION_DIRECTORY_SYNC,
        FAULT_DURING_COMPLETION_REREAD,
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

    def as_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionAuthorizationIdentityBlock:
    execution_authorization_identity: str
    retained_run_assessment_identity: str
    implementation_preparation_authorization_identity: str
    runtime_correction_authorization_identity: str
    expected_branch: str
    expected_head: str
    expected_origin_main: str
    retained_orchestration_policy_sha256: str
    native_helper_policy_sha256: str
    retained_schema_sha256: str
    case_set_sha256: str
    fixture_profile_sha256: str
    authority_registry_root: Path
    authority_registry_root_identity: str
    fixture_root_identity: str
    result_parent_identity: str
    result_directory_identity: str
    host_identity: str
    volume_identity: str
    run_identity: str
    selected_a6: bool
    source_identities: tuple[SourceIdentityExpectation, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema": RETAINED_EXECUTION_AUTHORIZATION_IDENTITY_BLOCK_SCHEMA,
            "execution_authorization_identity": self.execution_authorization_identity,
            "retained_run_assessment_identity": self.retained_run_assessment_identity,
            "implementation_preparation_authorization_identity": (
                self.implementation_preparation_authorization_identity
            ),
            "runtime_correction_authorization_identity": (
                self.runtime_correction_authorization_identity
            ),
            "expected_branch": self.expected_branch,
            "expected_head": self.expected_head,
            "expected_origin_main": self.expected_origin_main,
            "retained_orchestration_policy_sha256": (
                self.retained_orchestration_policy_sha256
            ),
            "native_helper_policy_sha256": self.native_helper_policy_sha256,
            "retained_schema_sha256": self.retained_schema_sha256,
            "case_set_sha256": self.case_set_sha256,
            "fixture_profile_sha256": self.fixture_profile_sha256,
            "authority_registry_root": str(self.authority_registry_root),
            "authority_registry_root_identity": (
                self.authority_registry_root_identity
            ),
            "fixture_root_identity": self.fixture_root_identity,
            "result_parent_identity": self.result_parent_identity,
            "result_directory_identity": self.result_directory_identity,
            "host_identity": self.host_identity,
            "volume_identity": self.volume_identity,
            "run_identity": self.run_identity,
            "selected_a6": self.selected_a6,
            "source_identities": [
                identity.as_payload() for identity in self.source_identities
            ],
        }


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
    execution_authorization: ExecutionAuthorizationIdentityBlock | None = None

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
            "execution_authorization": (
                self.execution_authorization.as_payload()
                if self.execution_authorization is not None
                else "NOT_SUPPLIED"
            ),
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
    global_authority_consumed: bool
    gate_consumed: bool
    native_invocation_started: bool
    primary_failure: str | None
    detail: str
    result_directory: str
    global_authority_artifact: ImmutableArtifactWriteResult | None = None
    gate_artifact: ImmutableArtifactWriteResult | None = None
    run_result_artifact: ImmutableArtifactWriteResult | None = None
    retained_completion_artifact: ImmutableArtifactWriteResult | None = None
    terminal_artifact: ImmutableArtifactWriteResult | None = None
    run_result_record: dict[str, Any] | None = None
    retained_completion_record: dict[str, Any] | None = None
    terminal_record: dict[str, Any] | None = None

    def as_payload(self) -> dict[str, Any]:
        payload = {
            "terminal_state": self.terminal_state,
            "retained_execution": self.retained_execution,
            "authoritative": self.authoritative,
            "global_authority_consumed": self.global_authority_consumed,
            "gate_consumed": self.gate_consumed,
            "native_invocation_started": self.native_invocation_started,
            "primary_failure": self.primary_failure or "NONE",
            "detail": self.detail,
            "result_directory": self.result_directory,
            "global_authority_artifact": (
                self.global_authority_artifact.as_payload()
                if self.global_authority_artifact is not None
                else "NOT_WRITTEN"
            ),
            "gate_artifact": (
                self.gate_artifact.as_payload()
                if self.gate_artifact is not None
                else "NOT_WRITTEN"
            ),
            "run_result_artifact": (
                self.run_result_artifact.as_payload()
                if self.run_result_artifact is not None
                else "NOT_WRITTEN"
            ),
            "retained_completion_artifact": (
                self.retained_completion_artifact.as_payload()
                if self.retained_completion_artifact is not None
                else "NOT_WRITTEN"
            ),
            "terminal_artifact": (
                self.terminal_artifact.as_payload()
                if self.terminal_artifact is not None
                else "NOT_WRITTEN"
            ),
            "run_result_record": self.run_result_record or "NOT_WRITTEN",
            "retained_completion_record": (
                self.retained_completion_record or "NOT_WRITTEN"
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
        "schema": "torment.brainvision.blocker2.retained.schemas.v0.2",
        "authorization_input_schema": RETAINED_AUTHORIZATION_INPUT_SCHEMA,
        "case_set_schema": RETAINED_CASE_SET_SCHEMA,
        "case_envelope_schema": RETAINED_CASE_ENVELOPE_SCHEMA,
        "execution_authorization_identity_schema": (
            RETAINED_EXECUTION_AUTHORIZATION_IDENTITY_SCHEMA
        ),
        "execution_authorization_identity_block_schema": (
            RETAINED_EXECUTION_AUTHORIZATION_IDENTITY_BLOCK_SCHEMA
        ),
        "run_identity_schema": RETAINED_RUN_IDENTITY_SCHEMA,
        "result_directory_derivation_rule_schema": (
            RETAINED_RESULT_DIRECTORY_DERIVATION_RULE_SCHEMA
        ),
        "authority_registry_profile_schema": (
            RETAINED_AUTHORITY_REGISTRY_PROFILE_SCHEMA
        ),
        "evidence_chain_schema": RETAINED_EVIDENCE_CHAIN_SCHEMA,
        "global_authority_entry_schema": RETAINED_GLOBAL_AUTHORITY_ENTRY_SCHEMA,
        "gate_entry_schema": RETAINED_GATE_ENTRY_SCHEMA,
        "run_result_schema": RETAINED_RUN_RESULT_SCHEMA,
        "retained_completion_schema": RETAINED_COMPLETION_SCHEMA,
        "repository_state_schema": RETAINED_REPOSITORY_STATE_SCHEMA,
        "source_identity_schema": RETAINED_SOURCE_IDENTITY_SCHEMA,
        "fixture_profile_schema": RETAINED_FIXTURE_PROFILE_SCHEMA,
        "evidence_chain": evidence_chain_declaration()["records"],
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


def authority_registry_profile_declaration() -> dict[str, Any]:
    return {
        "schema": RETAINED_AUTHORITY_REGISTRY_PROFILE_SCHEMA,
        "root_supply": "explicit future authorization input",
        "root_location": "outside repository",
        "root_kind": "ordinary non-reparse local fixed NTFS directory",
        "entry_path_derivation": "execution authorization identity",
        "entry_write_semantics": "exclusive-create canonical JSON",
        "durability": "BLOCKER-1 directory durability confirmed",
        "reuse_policy": "same authorization identity is rejected after entry exists",
        "release_policy": "no release, repair, resume, or automatic reset",
    }


def authority_registry_profile_identity() -> dict[str, str]:
    return {
        "schema": RETAINED_AUTHORITY_REGISTRY_PROFILE_SCHEMA,
        "authority_registry_profile_sha256": canonical_sha256(
            authority_registry_profile_declaration()
        ),
    }


def evidence_chain_declaration() -> dict[str, Any]:
    return {
        "schema": RETAINED_EVIDENCE_CHAIN_SCHEMA,
        "records": [
            "GLOBAL_AUTHORITY_ENTRY",
            "LOCAL_GATE_ENTRY",
            "RUN_RESULT",
            "RETAINED_COMPLETION",
        ],
        "linkage_hashes": [
            "global_authority_entry_hash",
            "local_gate_hash",
            "run_result_hash",
        ],
        "completion_source": "verified durable RUN_RESULT plus verified durable RETAINED_COMPLETION",
    }


def evidence_chain_identity() -> dict[str, str]:
    return {
        "schema": RETAINED_EVIDENCE_CHAIN_SCHEMA,
        "evidence_chain_sha256": canonical_sha256(evidence_chain_declaration()),
    }


def native_helper_policy_identity() -> dict[str, str]:
    return validation.absolute_path_control_policy_identity()


def validate_native_helper_policy_identity(
    policy_identity: Mapping[str, Any],
) -> dict[str, str]:
    required = native_helper_policy_identity()
    if policy_identity.get("policy_sha256") == ABSOLUTE_POLICY_SHA256:
        raise RetainedValidationError(NATIVE_HELPER_POLICY_MISMATCH)
    if set(policy_identity) != set(required):
        raise RetainedValidationError(NATIVE_HELPER_POLICY_MISMATCH)
    if policy_identity.get("policy_schema_identity") != required["policy_schema_identity"]:
        raise RetainedValidationError(NATIVE_HELPER_POLICY_MISMATCH)
    if policy_identity.get("policy_sha256") != required["policy_sha256"]:
        raise RetainedValidationError(NATIVE_HELPER_POLICY_MISMATCH)
    return dict(policy_identity)


def host_profile_identity() -> dict[str, str]:
    declaration = runtime_platform_observation()
    return {
        "schema": "torment.brainvision.blocker2.retained.host_profile.v0.1",
        "host_identity": canonical_sha256(declaration),
    }


def volume_identity_for_path(path: str | Path) -> dict[str, str]:
    resolved = _resolve_for_absent_child(path)
    drive, _tail = ntpath.splitdrive(str(resolved))
    declaration = {
        "schema": "torment.brainvision.blocker2.retained.volume_identity.v0.1",
        "drive_root": drive.lower() + "\\",
    }
    return {
        "schema": declaration["schema"],
        "volume_identity": canonical_sha256(declaration),
    }


def path_identity_for_role(
    path: str | Path,
    *,
    role: str,
    must_exist: bool = False,
) -> dict[str, str]:
    if must_exist and not Path(path).exists():
        raise RetainedValidationError("%s path must exist" % role)
    resolved = Path(path).resolve() if must_exist else _resolve_for_absent_child(path)
    declaration = {
        "schema": "torment.brainvision.blocker2.retained.path_identity.v0.1",
        "role": role,
        "path": str(resolved),
    }
    return {
        "schema": declaration["schema"],
        "role": role,
        "path": str(resolved),
        "path_identity": canonical_sha256(declaration),
    }


def result_directory_derivation_rule_declaration() -> dict[str, Any]:
    return {
        "schema": RETAINED_RESULT_DIRECTORY_DERIVATION_RULE_SCHEMA,
        "rule": RESULT_DIRECTORY_DERIVATION_RULE,
        "result_parent_input": "result_parent_identity",
        "result_child_input": "execution_authorization_identity",
        "caller_selectable": False,
    }


def derive_result_directory(
    result_parent: str | Path,
    execution_authorization_identity: str,
) -> Path:
    _require_hex64(
        execution_authorization_identity,
        "execution_authorization_identity",
    )
    return Path(result_parent).resolve() / execution_authorization_identity


def result_directory_identity(result_directory: str | Path) -> dict[str, str]:
    return path_identity_for_role(
        result_directory,
        role="result_directory",
        must_exist=False,
    )


def operator_wrapper_identity() -> dict[str, str]:
    declaration = {
        "schema": OPERATOR_WRAPPER_IDENTITY_SCHEMA,
        "authorization_input_schema": OPERATOR_WRAPPER_AUTHORIZATION_INPUT_SCHEMA,
        "authorization_input_declaration_schema": (
            OPERATOR_WRAPPER_AUTHORIZATION_INPUT_DECLARATION_SCHEMA
        ),
        "wrapper_version": OPERATOR_WRAPPER_VERSION,
        "real_executor_selector": REAL_EXECUTOR_SELECTOR,
    }
    return {
        "schema": OPERATOR_WRAPPER_IDENTITY_SCHEMA,
        "operator_wrapper_sha256": canonical_sha256(declaration),
    }


def execution_authorization_identity_declaration(
    *,
    retained_run_assessment_identity: str,
    implementation_preparation_authorization_identity: str,
    runtime_correction_authorization_identity: str,
    identity_derivation_cycle_correction_authorization_identity: str = (
        IDENTITY_DERIVATION_CYCLE_CORRECTION_AUTHORIZATION_SHA256
    ),
    expected_branch: str,
    expected_head: str,
    expected_origin_main: str,
    retained_orchestration_policy_sha256: str,
    native_helper_policy_sha256: str,
    retained_schema_sha256: str,
    case_set_sha256: str,
    fixture_profile_sha256: str,
    authority_registry_root_identity: str,
    fixture_root_identity: str,
    result_parent_identity: str,
    host_identity: str,
    volume_identity: str,
    case_execution_order: Sequence[str],
    selected_a6: bool,
    source_identities: Sequence[SourceIdentityExpectation],
    result_directory_derivation_rule: Mapping[str, Any] | None = None,
    operator_identity: str = OPERATOR_IDENTITY,
    single_process_declaration: str = SINGLE_PROCESS_DECLARATION,
    single_attempt_declaration: str = SINGLE_ATTEMPT_DECLARATION,
    real_executor_selector: str = REAL_EXECUTOR_SELECTOR,
    fault_injection_disabled: bool = True,
) -> dict[str, Any]:
    return {
        "schema": RETAINED_EXECUTION_AUTHORIZATION_IDENTITY_SCHEMA,
        "retained_mode": RETAINED_MODE,
        "authoritative": True,
        "retained_run_assessment_identity": retained_run_assessment_identity,
        "implementation_preparation_authorization_identity": (
            implementation_preparation_authorization_identity
        ),
        "runtime_correction_authorization_identity": (
            runtime_correction_authorization_identity
        ),
        "identity_derivation_cycle_correction_authorization_identity": (
            identity_derivation_cycle_correction_authorization_identity
        ),
        "controlling_document_identities": {
            "retained_run_assessment": retained_run_assessment_identity,
            "implementation_preparation_authorization": (
                implementation_preparation_authorization_identity
            ),
            "post_commit_runtime_correction_authorization": (
                runtime_correction_authorization_identity
            ),
            "identity_derivation_cycle_correction_authorization": (
                identity_derivation_cycle_correction_authorization_identity
            ),
        },
        "expected_branch": expected_branch,
        "expected_head": expected_head,
        "expected_origin_main": expected_origin_main,
        "retained_orchestration_policy_sha256": (
            retained_orchestration_policy_sha256
        ),
        "native_helper_policy_sha256": native_helper_policy_sha256,
        "retained_schema_sha256": retained_schema_sha256,
        "case_set_sha256": case_set_sha256,
        "fixture_profile_sha256": fixture_profile_sha256,
        "authority_registry_root_identity": authority_registry_root_identity,
        "fixture_root_identity": fixture_root_identity,
        "result_parent_identity": result_parent_identity,
        "result_directory_derivation_rule": dict(
            result_directory_derivation_rule
            or result_directory_derivation_rule_declaration()
        ),
        "operator_wrapper_identity": operator_wrapper_identity()[
            "operator_wrapper_sha256"
        ],
        "operator_identity": operator_identity,
        "single_process_declaration": single_process_declaration,
        "single_attempt_declaration": single_attempt_declaration,
        "real_executor_selector": real_executor_selector,
        "fault_injection_disabled": fault_injection_disabled,
        "host_identity": host_identity,
        "volume_identity": volume_identity,
        "case_execution_order": list(case_execution_order),
        "selected_a6": selected_a6,
        "source_identities": [
            identity.as_payload()
            for identity in sorted(
                source_identities,
                key=lambda item: item.relative_path,
            )
        ],
    }


def execution_authorization_identity_from_declaration(
    declaration: Mapping[str, Any],
) -> str:
    return canonical_sha256(dict(declaration))


def run_identity_declaration(
    *,
    execution_authorization_identity: str,
    expected_branch: str,
    expected_head: str,
    expected_origin_main: str,
    case_set_sha256: str,
    case_execution_order: Sequence[str],
    fixture_root_identity: str,
    result_parent_identity: str,
    result_directory_identity: str,
    authority_registry_root_identity: str,
    operator_identity: str = OPERATOR_IDENTITY,
    single_attempt_declaration: str = SINGLE_ATTEMPT_DECLARATION,
    real_executor_selector: str = REAL_EXECUTOR_SELECTOR,
    selected_a6: bool,
) -> dict[str, Any]:
    return {
        "schema": RETAINED_RUN_IDENTITY_SCHEMA,
        "execution_authorization_identity": execution_authorization_identity,
        "expected_branch": expected_branch,
        "expected_head": expected_head,
        "expected_origin_main": expected_origin_main,
        "case_set_sha256": case_set_sha256,
        "case_execution_order": list(case_execution_order),
        "fixture_root_identity": fixture_root_identity,
        "result_parent_identity": result_parent_identity,
        "result_directory_identity": result_directory_identity,
        "authority_registry_root_identity": authority_registry_root_identity,
        "operator_identity": operator_identity,
        "single_attempt_declaration": single_attempt_declaration,
        "real_executor_selector": real_executor_selector,
        "selected_a6": selected_a6,
    }


def run_identity_from_declaration(declaration: Mapping[str, Any]) -> str:
    return canonical_sha256(dict(declaration))


def build_execution_authorization_identity_block(
    *,
    assessment_identity: str,
    implementation_preparation_authorization_identity: str,
    runtime_correction_authorization_identity: str,
    expected_branch: str,
    expected_head: str,
    expected_origin_main: str,
    fixture_root: str | Path,
    authority_registry_root: str | Path,
    source_identities: Sequence[SourceIdentityExpectation],
    result_parent: str | Path | None = None,
    result_directory: str | Path | None = None,
    selected_cases: Sequence[str] = DEFAULT_RETAINED_CASES,
    optional_cases: Sequence[str] = (),
    run_identity: str | None = None,
    authorization_identity: str | None = None,
) -> ExecutionAuthorizationIdentityBlock:
    case_set = retained_case_set_identity(
        selected_cases=selected_cases,
        optional_cases=optional_cases,
    )
    case_declaration = retained_case_set_declaration(
        selected_cases=selected_cases,
        optional_cases=optional_cases,
    )
    case_execution_order = case_declaration["native_execution_order"]
    authority_root_identity = path_identity_for_role(
        authority_registry_root,
        role="authority_registry_root",
        must_exist=True,
    )
    fixture_identity = path_identity_for_role(
        fixture_root,
        role="fixture_root",
        must_exist=False,
    )
    if result_parent is None:
        if result_directory is None:
            raise RetainedValidationError("result parent is required")
        supplied_result_dir = _resolve_for_absent_child(result_directory)
        result_parent_path = supplied_result_dir.parent
    else:
        result_parent_path = Path(result_parent).resolve()
        supplied_result_dir = (
            _resolve_for_absent_child(result_directory)
            if result_directory is not None
            else None
        )
    result_parent_identity = path_identity_for_role(
        result_parent_path,
        role="result_parent",
        must_exist=True,
    )
    result_parent_volume_identity = volume_identity_for_path(result_parent_path)
    identity_declaration = execution_authorization_identity_declaration(
        retained_run_assessment_identity=assessment_identity,
        implementation_preparation_authorization_identity=(
            implementation_preparation_authorization_identity
        ),
        runtime_correction_authorization_identity=(
            runtime_correction_authorization_identity
        ),
        expected_branch=expected_branch,
        expected_head=expected_head,
        expected_origin_main=expected_origin_main,
        retained_orchestration_policy_sha256=ABSOLUTE_POLICY_SHA256,
        native_helper_policy_sha256=native_helper_policy_identity()["policy_sha256"],
        retained_schema_sha256=retained_schema_identity()["schema_sha256"],
        case_set_sha256=case_set["case_set_sha256"],
        fixture_profile_sha256=fixture_profile_identity()["fixture_profile_sha256"],
        authority_registry_root_identity=authority_root_identity["path_identity"],
        fixture_root_identity=fixture_identity["path_identity"],
        result_parent_identity=result_parent_identity["path_identity"],
        host_identity=host_profile_identity()["host_identity"],
        volume_identity=result_parent_volume_identity["volume_identity"],
        case_execution_order=case_execution_order,
        selected_a6=A6 in optional_cases,
        source_identities=source_identities,
    )
    derived_authorization_identity = (
        execution_authorization_identity_from_declaration(identity_declaration)
    )
    if (
        authorization_identity is not None
        and authorization_identity != derived_authorization_identity
    ):
        raise RetainedValidationError(GLOBAL_AUTHORITY_IDENTITY_MISMATCH)
    derived_result_dir = derive_result_directory(
        result_parent_path,
        derived_authorization_identity,
    )
    if supplied_result_dir is not None and supplied_result_dir != derived_result_dir:
        raise RetainedValidationError(IDENTITY_MISMATCH)
    result_directory_identity_payload = result_directory_identity(derived_result_dir)
    derived_run_identity = run_identity_from_declaration(
        run_identity_declaration(
            execution_authorization_identity=derived_authorization_identity,
            expected_branch=expected_branch,
            expected_head=expected_head,
            expected_origin_main=expected_origin_main,
            case_set_sha256=case_set["case_set_sha256"],
            case_execution_order=case_execution_order,
            fixture_root_identity=fixture_identity["path_identity"],
            result_parent_identity=result_parent_identity["path_identity"],
            result_directory_identity=(
                result_directory_identity_payload["path_identity"]
            ),
            authority_registry_root_identity=authority_root_identity["path_identity"],
            selected_a6=A6 in optional_cases,
        )
    )
    if run_identity is not None and run_identity != derived_run_identity:
        raise RetainedValidationError(GLOBAL_AUTHORITY_IDENTITY_MISMATCH)
    return ExecutionAuthorizationIdentityBlock(
        execution_authorization_identity=derived_authorization_identity,
        retained_run_assessment_identity=assessment_identity,
        implementation_preparation_authorization_identity=(
            implementation_preparation_authorization_identity
        ),
        runtime_correction_authorization_identity=(
            runtime_correction_authorization_identity
        ),
        expected_branch=expected_branch,
        expected_head=expected_head,
        expected_origin_main=expected_origin_main,
        retained_orchestration_policy_sha256=ABSOLUTE_POLICY_SHA256,
        native_helper_policy_sha256=native_helper_policy_identity()["policy_sha256"],
        retained_schema_sha256=retained_schema_identity()["schema_sha256"],
        case_set_sha256=case_set["case_set_sha256"],
        fixture_profile_sha256=fixture_profile_identity()["fixture_profile_sha256"],
        authority_registry_root=Path(authority_registry_root),
        authority_registry_root_identity=authority_root_identity["path_identity"],
        fixture_root_identity=fixture_identity["path_identity"],
        result_parent_identity=result_parent_identity["path_identity"],
        result_directory_identity=result_directory_identity_payload["path_identity"],
        host_identity=host_profile_identity()["host_identity"],
        volume_identity=result_parent_volume_identity["volume_identity"],
        run_identity=derived_run_identity,
        selected_a6=A6 in optional_cases,
        source_identities=tuple(source_identities),
    )


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


def validate_execution_authorization_identity_block(
    authorization: RetainedAuthorization,
    block: ExecutionAuthorizationIdentityBlock,
    *,
    repo_root: Path,
    source_observations: Mapping[str, SourceIdentity],
) -> dict[str, Any]:
    _require_hex64(block.execution_authorization_identity, "execution_authorization_identity")
    _require_hex64(
        block.retained_run_assessment_identity,
        "retained_run_assessment_identity",
    )
    _require_hex64(
        block.implementation_preparation_authorization_identity,
        "implementation_preparation_authorization_identity",
    )
    _require_hex64(
        block.runtime_correction_authorization_identity,
        "runtime_correction_authorization_identity",
    )
    _require_hex64(block.run_identity, "run_identity")
    if block.execution_authorization_identity != authorization.authorization_identity:
        raise RetainedValidationError(IDENTITY_MISMATCH)
    if block.retained_run_assessment_identity != authorization.assessment_identity:
        raise RetainedValidationError(IDENTITY_MISMATCH)
    if block.retained_run_assessment_identity != RETAINED_RUN_ASSESSMENT_SHA256:
        raise RetainedValidationError(IDENTITY_MISMATCH)
    if (
        block.implementation_preparation_authorization_identity
        != IMPLEMENTATION_PREPARATION_AUTHORIZATION_SHA256
    ):
        raise RetainedValidationError(IDENTITY_MISMATCH)
    if (
        block.runtime_correction_authorization_identity
        != RUNTIME_CORRECTION_AUTHORIZATION_SHA256
    ):
        raise RetainedValidationError(IDENTITY_MISMATCH)
    if block.expected_branch != authorization.expected_branch:
        raise RetainedValidationError(REPOSITORY_STATE_INVALID)
    if block.expected_head != authorization.expected_head:
        raise RetainedValidationError(REPOSITORY_STATE_INVALID)
    if block.expected_origin_main != authorization.expected_origin_main:
        raise RetainedValidationError(REPOSITORY_STATE_INVALID)
    if block.retained_orchestration_policy_sha256 != ABSOLUTE_POLICY_SHA256:
        raise RetainedValidationError(RETAINED_POLICY_MISMATCH)
    if (
        block.native_helper_policy_sha256
        != native_helper_policy_identity()["policy_sha256"]
    ):
        raise RetainedValidationError(NATIVE_HELPER_POLICY_MISMATCH)
    if block.retained_schema_sha256 != retained_schema_identity()["schema_sha256"]:
        raise RetainedValidationError(IDENTITY_MISMATCH)
    expected_case_set = retained_case_set_identity(
        selected_cases=authorization.selected_cases,
        optional_cases=authorization.optional_cases,
    )["case_set_sha256"]
    if block.case_set_sha256 != expected_case_set:
        raise RetainedValidationError(IDENTITY_MISMATCH)
    if (
        block.fixture_profile_sha256
        != fixture_profile_identity()["fixture_profile_sha256"]
    ):
        raise RetainedValidationError(IDENTITY_MISMATCH)
    if block.selected_a6 is not (A6 in authorization.optional_cases):
        raise RetainedValidationError(IDENTITY_MISMATCH)
    _admit_authority_registry_root(block.authority_registry_root, repo_root=repo_root)
    computed = build_execution_authorization_identity_block(
        authorization_identity=authorization.authorization_identity,
        assessment_identity=authorization.assessment_identity,
        implementation_preparation_authorization_identity=(
            block.implementation_preparation_authorization_identity
        ),
        runtime_correction_authorization_identity=(
            block.runtime_correction_authorization_identity
        ),
        expected_branch=authorization.expected_branch,
        expected_head=authorization.expected_head,
        expected_origin_main=authorization.expected_origin_main,
        result_directory=authorization.result_directory,
        fixture_root=authorization.fixture_root,
        authority_registry_root=block.authority_registry_root,
        source_identities=block.source_identities,
        selected_cases=authorization.selected_cases,
        optional_cases=authorization.optional_cases,
        run_identity=block.run_identity,
    )
    expected_path_identities = {
        "authority_registry_root_identity": computed.authority_registry_root_identity,
        "fixture_root_identity": computed.fixture_root_identity,
        "result_parent_identity": computed.result_parent_identity,
        "result_directory_identity": computed.result_directory_identity,
        "host_identity": computed.host_identity,
        "volume_identity": computed.volume_identity,
    }
    observed_path_identities = {
        key: getattr(block, key) for key in expected_path_identities
    }
    if observed_path_identities != expected_path_identities:
        raise RetainedValidationError(IDENTITY_MISMATCH)
    expected_source_paths = {identity.relative_path for identity in block.source_identities}
    if expected_source_paths != set(REQUIRED_SOURCE_IDENTITY_PATHS):
        raise RetainedValidationError("complete source identity set required")
    for expectation in block.source_identities:
        if expectation.git_blob_oid == UNAVAILABLE_UNTIL_COMMIT:
            raise RetainedValidationError("precommit placeholders rejected")
        _require_head_oid(expectation.git_blob_oid, "source Git blob identity")
    admitted_sources = admit_source_identities(
        block.source_identities,
        source_observations,
    )
    return {
        "schema": (
            "torment.brainvision.blocker2.retained."
            "execution_authorization_identity_block.admitted.v0.2"
        ),
        "identity_block": block.as_payload(),
        "source_identities": admitted_sources,
        "path_identities": expected_path_identities,
    }


def global_authority_entry_path(
    authorization: RetainedAuthorization,
) -> Path:
    block = authorization.execution_authorization
    if block is None:
        raise RetainedValidationError(AUTHORITATIVE_AUTHORIZATION_MISSING)
    root = Path(block.authority_registry_root).resolve()
    return root / (authorization.authorization_identity + GLOBAL_AUTHORITY_ENTRY_SUFFIX)


def _authorization_path_bindings_match(
    authorization: RetainedAuthorization,
) -> bool:
    block = authorization.execution_authorization
    if block is None:
        return False
    try:
        computed = build_execution_authorization_identity_block(
            authorization_identity=authorization.authorization_identity,
            assessment_identity=authorization.assessment_identity,
            implementation_preparation_authorization_identity=(
                block.implementation_preparation_authorization_identity
            ),
            runtime_correction_authorization_identity=(
                block.runtime_correction_authorization_identity
            ),
            expected_branch=authorization.expected_branch,
            expected_head=authorization.expected_head,
            expected_origin_main=authorization.expected_origin_main,
            result_directory=authorization.result_directory,
            fixture_root=authorization.fixture_root,
            authority_registry_root=block.authority_registry_root,
            source_identities=block.source_identities,
            selected_cases=authorization.selected_cases,
            optional_cases=authorization.optional_cases,
            run_identity=block.run_identity,
        )
    except RetainedValidationError:
        return False
    return (
        block.fixture_root_identity == computed.fixture_root_identity
        and block.result_parent_identity == computed.result_parent_identity
        and block.result_directory_identity == computed.result_directory_identity
        and block.authority_registry_root_identity
        == computed.authority_registry_root_identity
        and block.host_identity == computed.host_identity
        and block.volume_identity == computed.volume_identity
        and block.selected_a6 is (A6 in authorization.optional_cases)
    )


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
    observed_sources = source_observations or {}
    execution_identity: dict[str, Any] | str = "NOT_AUTHORITATIVE"
    if authorization.authoritative:
        if authorization.execution_authorization is None:
            raise RetainedValidationError(AUTHORITATIVE_AUTHORIZATION_MISSING)
        execution_identity = validate_execution_authorization_identity_block(
            authorization,
            authorization.execution_authorization,
            repo_root=root,
            source_observations=observed_sources,
        )
        admitted_sources = execution_identity["source_identities"]
    else:
        admitted_sources = admit_source_identities(
            source_expectations,
            observed_sources,
        )
    if result_dir.exists():
        raise RetainedValidationError(RESULT_DIRECTORY_NOT_ABSENT)
    if result_dir.parent.exists() and _is_reparse_point(result_dir.parent):
        raise RetainedValidationError(RESULT_DIRECTORY_REPARSE_POINT)
    if fixture_root.exists() and _is_reparse_point(fixture_root):
        raise RetainedValidationError(FIXTURE_PROFILE_UNSUPPORTED)
    return {
        "schema": "torment.brainvision.blocker2.retained.preflight.v0.1",
        "authorization": authorization.as_payload(),
        "execution_authorization": execution_identity,
        "policy_identity": validate_policy_identity(
            authorized_absolute_path_control_policy_identity()
        ),
        "native_helper_policy_identity": validate_native_helper_policy_identity(
            native_helper_policy_identity()
        ),
        "schema_identity": retained_schema_identity(),
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
    if authorization.authoritative and authorization.execution_authorization is not None:
        try:
            authority_path = global_authority_entry_path(authorization)
            if authority_path.exists():
                replay_failure = (
                    GLOBAL_AUTHORITY_ENTRY_EXISTS
                    if _authorization_path_bindings_match(authorization)
                    else CROSS_LOCATION_REPLAY_REJECTED
                )
                return _run_result(
                    terminal_state=PREFLIGHT_REJECTED,
                    authorization=authorization,
                    result_directory=result_dir,
                    global_authority_consumed=True,
                    gate_consumed=False,
                    native_invocation_started=False,
                    primary_failure=replay_failure,
                    detail="global authority entry already exists",
                )
        except RetainedValidationError:
            pass
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
            global_authority_consumed=False,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=_failure_from_exception(exc),
            detail=str(exc),
        )
    case_order = validate_case_selection(
        authorization.selected_cases,
        authorization.optional_cases,
    )
    global_authority_artifact: ImmutableArtifactWriteResult | None = None
    global_authority_consumed = False
    if fault_point == FAULT_BEFORE_GLOBAL_AUTHORITY_WRITE:
        return _run_result(
            terminal_state=PREFLIGHT_REJECTED,
            authorization=authorization,
            result_directory=result_dir,
            global_authority_consumed=False,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=FAULT_INJECTION_TRIGGERED,
            detail="fault injected before durable global authority write",
        )
    if authorization.authoritative:
        try:
            authority_path = global_authority_entry_path(authorization)
            if authority_path.exists():
                return _run_result(
                    terminal_state=PREFLIGHT_REJECTED,
                    authorization=authorization,
                    result_directory=result_dir,
                    global_authority_consumed=True,
                    gate_consumed=False,
                    native_invocation_started=False,
                    primary_failure=GLOBAL_AUTHORITY_ENTRY_EXISTS,
                    detail="global authority entry already exists",
                )
            global_record = build_global_authority_entry_record(
                authorization=authorization,
                preflight=preflight,
            )
            validate_global_authority_entry_record(global_record)
            global_authority_artifact = _write_canonical_file(
                authority_path,
                global_record,
                adapter=adapter,
                fault_point=fault_point,
                fault_file_write=FAULT_DURING_GLOBAL_AUTHORITY_FILE_WRITE,
                fault_directory_sync=FAULT_DURING_GLOBAL_AUTHORITY_DIRECTORY_SYNC,
                fault_reread=FAULT_DURING_GLOBAL_AUTHORITY_REREAD,
            )
            validate_global_authority_artifact(authority_path)
            global_authority_consumed = True
        except ArtifactPersistenceError as exc:
            return _run_result(
                terminal_state=GATE_ENTRY_FAILED,
                authorization=authorization,
                result_directory=result_dir,
                global_authority_consumed=False,
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
                global_authority_consumed=False,
                gate_consumed=False,
                native_invocation_started=False,
                primary_failure=GLOBAL_AUTHORITY_ENTRY_PERSISTENCE_FAILURE,
                detail=str(exc),
            )
    if (
        authorization.authoritative
        and fault_point
        in {
            FAULT_AFTER_GLOBAL_AUTHORITY_VERIFICATION_BEFORE_LOCAL_GATE,
            FAULT_BEFORE_GATE_WRITE,
        }
    ):
        return _run_result(
            terminal_state=GATE_ENTRY_FAILED,
            authorization=authorization,
            result_directory=result_dir,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=FAULT_INJECTION_TRIGGERED,
            detail="fault injected after durable global authority verification",
            global_authority_artifact=global_authority_artifact,
        )
    if not authorization.authoritative and fault_point == FAULT_BEFORE_GATE_WRITE:
        return _run_result(
            terminal_state=GATE_ENTRY_FAILED,
            authorization=authorization,
            result_directory=result_dir,
            global_authority_consumed=False,
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
            global_authority_artifact=global_authority_artifact,
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
            global_authority_consumed=global_authority_consumed,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=exc.failure_code,
            detail=exc.detail,
            global_authority_artifact=global_authority_artifact,
        )
    except (OSError, RetainedValidationError) as exc:
        return _run_result(
            terminal_state=GATE_ENTRY_FAILED,
            authorization=authorization,
            result_directory=result_dir,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=GATE_ENTRY_WRITE_FAILURE,
            detail=str(exc),
            global_authority_artifact=global_authority_artifact,
        )
    if fault_point == FAULT_AFTER_VERIFIED_GATE_BEFORE_NATIVE:
        return _terminalized_result(
            authorization=authorization,
            result_directory=result_dir,
            adapter=adapter,
            preflight=preflight,
            global_authority_artifact=global_authority_artifact,
            global_authority_consumed=global_authority_consumed,
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
        if fault_point == FAULT_AFTER_NATIVE_BEFORE_RUN_RESULT:
            return _run_result(
                terminal_state=RUN_FAILED,
                authorization=authorization,
                result_directory=result_dir,
                global_authority_consumed=global_authority_consumed,
                gate_consumed=True,
                native_invocation_started=True,
                primary_failure=FAULT_INJECTION_TRIGGERED,
                detail="fault injected after native cases before RUN_RESULT",
                global_authority_artifact=global_authority_artifact,
                gate_artifact=gate_artifact,
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
            preflight=preflight,
            global_authority_artifact=global_authority_artifact,
            global_authority_consumed=global_authority_consumed,
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
            preflight=preflight,
            global_authority_artifact=global_authority_artifact,
            global_authority_consumed=global_authority_consumed,
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
        preflight=preflight,
        global_authority_artifact=global_authority_artifact,
        global_authority_consumed=global_authority_consumed,
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


def retained_case_envelope(
    result: validation.ValidationCaseResult,
    *,
    short_case: str,
    satisfied: bool,
) -> dict[str, Any]:
    native_policy = validate_native_helper_policy_identity(result.policy_identity or {})
    retained_policy = validate_policy_identity(
        authorized_absolute_path_control_policy_identity()
    )
    raw_numeric_error: int | str = (
        result.native_error_code
        if result.native_error_code is not None
        else "NOT_RECORDED"
    )
    raw_symbolic_error = result.native_error_name or "NOT_RECORDED"
    identity_continuity = {
        "source_identity_before": _strip_none(
            asdict(result.source_identity_before)
            if result.source_identity_before is not None
            else "NOT_RECORDED"
        ),
        "retained_handle_identity_after": _strip_none(
            asdict(result.retained_handle_identity_after)
            if result.retained_handle_identity_after is not None
            else "NOT_RECORDED"
        ),
        "final_identity_after": _strip_none(
            asdict(result.final_identity_after)
            if result.final_identity_after is not None
            else "NOT_RECORDED"
        ),
    }
    content_continuity = {
        "manifest_before_sha256": result.manifest_before_sha256 or "NOT_RECORDED",
        "manifest_after_sha256": result.manifest_after_sha256 or "NOT_RECORDED",
        "content_manifest_preserved": (
            result.manifest_before_sha256 is not None
            and result.manifest_before_sha256 == result.manifest_after_sha256
        ),
    }
    preservation = {
        "source_exists_after_native_failure": (
            result.source_exists_after_native_failure
            if result.source_exists_after_native_failure is not None
            else "NOT_RECORDED"
        ),
        "final_exists_after_native_failure": (
            result.final_exists_after_native_failure
            if result.final_exists_after_native_failure is not None
            else "NOT_RECORDED"
        ),
    }
    return {
        "schema": RETAINED_CASE_ENVELOPE_SCHEMA,
        "case_short": short_case,
        "case_id": result.case_id,
        "case_identity": canonical_sha256(
            {
                "schema": "torment.brainvision.blocker2.retained.case_identity.v0.1",
                "case_short": short_case,
                "case_id": result.case_id,
            }
        ),
        "fixture_identity": fixture_profile_identity()["fixture_profile_sha256"],
        "native_helper_policy_identity": native_policy,
        "retained_orchestration_policy_identity": retained_policy,
        "raw_native_observation": _case_result_payload(result),
        "retained_case_classification": {
            "gating": short_case in COMPLETION_GATING_CASES,
            "satisfied": satisfied,
            "status": result.status,
        },
        "source_final_preservation_evidence": preservation,
        "identity_continuity_evidence": identity_continuity,
        "content_continuity_evidence": content_continuity,
        "raw_numeric_error": raw_numeric_error,
        "raw_symbolic_error": raw_symbolic_error,
    }


def validate_retained_case_envelope(envelope: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "case_short",
        "case_id",
        "case_identity",
        "fixture_identity",
        "native_helper_policy_identity",
        "retained_orchestration_policy_identity",
        "raw_native_observation",
        "retained_case_classification",
        "source_final_preservation_evidence",
        "identity_continuity_evidence",
        "content_continuity_evidence",
        "raw_numeric_error",
        "raw_symbolic_error",
    }
    if set(envelope) != required:
        raise RetainedValidationError("retained case envelope has unexpected fields")
    if envelope["schema"] != RETAINED_CASE_ENVELOPE_SCHEMA:
        raise RetainedValidationError("retained case envelope schema mismatch")
    validate_native_helper_policy_identity(envelope["native_helper_policy_identity"])
    validate_policy_identity(envelope["retained_orchestration_policy_identity"])
    if envelope["fixture_identity"] != fixture_profile_identity()["fixture_profile_sha256"]:
        raise RetainedValidationError("retained case fixture identity mismatch")
    _require_hex64(str(envelope["case_identity"]), "case_identity")


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
    envelopes = [
        retained_case_envelope(
            result_by_short[case],
            short_case=case,
            satisfied=(
                gating_satisfied_by_case[case]
                if case in COMPLETION_GATING_CASES
                else False
            ),
        )
        for case in expected
        if case in result_by_short
    ]
    for envelope in envelopes:
        validate_retained_case_envelope(envelope)
    return {
        "schema": "torment.brainvision.blocker2.retained.case_outcomes.v0.1",
        "selected_cases": [CASE_SHORT_TO_ID[case] for case in expected],
        "selected_cases_short": list(expected),
        "completion_gating_cases": list(COMPLETION_GATING_CASES),
        "optional_non_gating_cases": list(optional_cases),
        "gating_satisfied_by_case": gating_satisfied_by_case,
        "gating_satisfied": all(gating_satisfied_by_case.values()),
        "optional_outcomes": optional_outcomes,
        "case_results": envelopes,
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


def build_global_authority_entry_record(
    *,
    authorization: RetainedAuthorization,
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    block = authorization.execution_authorization
    if block is None:
        raise RetainedValidationError(AUTHORITATIVE_AUTHORIZATION_MISSING)
    return {
        "schema": RETAINED_GLOBAL_AUTHORITY_ENTRY_SCHEMA,
        "record_type": "GLOBAL_AUTHORITY_ENTRY",
        "execution_authorization_identity": authorization.authorization_identity,
        "assessment_identity": authorization.assessment_identity,
        "implementation_preparation_authorization_identity": (
            block.implementation_preparation_authorization_identity
        ),
        "runtime_correction_authorization_identity": (
            block.runtime_correction_authorization_identity
        ),
        "repository_state": dict(preflight["repository_state"]),
        "source_identities": list(preflight["source_identities"]),
        "retained_orchestration_policy_identity": validate_policy_identity(
            authorized_absolute_path_control_policy_identity()
        ),
        "native_helper_policy_identity": validate_native_helper_policy_identity(
            native_helper_policy_identity()
        ),
        "schema_identity": retained_schema_identity(),
        "case_set_identity": retained_case_set_identity(
            selected_cases=authorization.selected_cases,
            optional_cases=authorization.optional_cases,
        ),
        "fixture_profile_identity": fixture_profile_identity(),
        "path_identities": dict(preflight["execution_authorization"]["path_identities"]),
        "authority_registry_entry_path": str(global_authority_entry_path(authorization)),
        "run_identity": block.run_identity,
        "selected_a6": block.selected_a6,
        "authoritative": True,
        "retained_execution": False,
        "native_invocation_started": False,
        "terminal_completion": "ABSENT",
    }


def validate_global_authority_entry_record(record: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "record_type",
        "execution_authorization_identity",
        "assessment_identity",
        "implementation_preparation_authorization_identity",
        "runtime_correction_authorization_identity",
        "repository_state",
        "source_identities",
        "retained_orchestration_policy_identity",
        "native_helper_policy_identity",
        "schema_identity",
        "case_set_identity",
        "fixture_profile_identity",
        "path_identities",
        "authority_registry_entry_path",
        "run_identity",
        "selected_a6",
        "authoritative",
        "retained_execution",
        "native_invocation_started",
        "terminal_completion",
    }
    if set(record) != required:
        raise RetainedValidationError("global authority entry has unexpected fields")
    if record["schema"] != RETAINED_GLOBAL_AUTHORITY_ENTRY_SCHEMA:
        raise RetainedValidationError("global authority schema mismatch")
    if record["record_type"] != "GLOBAL_AUTHORITY_ENTRY":
        raise RetainedValidationError("global authority record type mismatch")
    _require_hex64(
        str(record["execution_authorization_identity"]),
        "execution_authorization_identity",
    )
    _require_hex64(str(record["assessment_identity"]), "assessment_identity")
    _require_hex64(str(record["run_identity"]), "run_identity")
    validate_policy_identity(record["retained_orchestration_policy_identity"])
    validate_native_helper_policy_identity(record["native_helper_policy_identity"])
    if record["schema_identity"] != retained_schema_identity():
        raise RetainedValidationError(GLOBAL_AUTHORITY_IDENTITY_MISMATCH)
    if record["fixture_profile_identity"] != fixture_profile_identity():
        raise RetainedValidationError(GLOBAL_AUTHORITY_IDENTITY_MISMATCH)
    if record["authoritative"] is not True:
        raise RetainedValidationError("global authority must be authoritative")
    if record["retained_execution"] is not False:
        raise RetainedValidationError("global authority cannot claim completion")
    if record["native_invocation_started"] is not False:
        raise RetainedValidationError("native invocation cannot precede local gate")
    if record["terminal_completion"] != "ABSENT":
        raise RetainedValidationError("global authority completion must be absent")


def validate_global_authority_artifact(path: str | Path) -> dict[str, Any]:
    payload = Path(path).read_bytes()
    record = load_canonical_json_bytes(payload)
    validate_global_authority_entry_record(record)
    return record


def build_gate_entry_record(
    *,
    authorization: RetainedAuthorization,
    preflight: Mapping[str, Any],
    global_authority_artifact: ImmutableArtifactWriteResult | None = None,
) -> dict[str, Any]:
    return {
        "schema": RETAINED_GATE_ENTRY_SCHEMA,
        "record_type": "LOCAL_GATE_ENTRY",
        "authorization_identity": authorization.authorization_identity,
        "assessment_identity": authorization.assessment_identity,
        "mode": authorization.mode,
        "control_mode": validation.ABSOLUTE_PATH_CONTROL_MODE,
        "authoritative": authorization.authoritative,
        "global_authority_state": (
            {
                "path": global_authority_artifact.path,
                "sha256": global_authority_artifact.sha256,
                "byte_length": global_authority_artifact.byte_length,
            }
            if global_authority_artifact is not None
            else "NOT_AUTHORITATIVE"
        ),
        "policy_identity": validate_policy_identity(
            authorized_absolute_path_control_policy_identity()
        ),
        "native_helper_policy_identity": validate_native_helper_policy_identity(
            native_helper_policy_identity()
        ),
        "schema_identity": retained_schema_identity(),
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
        "record_type",
        "authorization_identity",
        "assessment_identity",
        "mode",
        "control_mode",
        "authoritative",
        "global_authority_state",
        "policy_identity",
        "native_helper_policy_identity",
        "schema_identity",
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
    if record["record_type"] != "LOCAL_GATE_ENTRY":
        raise RetainedValidationError("gate entry record type mismatch")
    require_retained_mode(str(record["mode"]))
    if record["control_mode"] != validation.ABSOLUTE_PATH_CONTROL_MODE:
        raise RetainedValidationError("gate entry control mode mismatch")
    validate_policy_identity(record["policy_identity"])
    validate_native_helper_policy_identity(record["native_helper_policy_identity"])
    if record["schema_identity"] != retained_schema_identity():
        raise RetainedValidationError(LOCAL_GATE_LINKAGE_FAILURE)
    if record["authoritative"] is True:
        global_state = _require_mapping(
            record["global_authority_state"],
            "global_authority_state",
        )
        _require_hex64(str(global_state.get("sha256")), "global authority hash")
    elif record["global_authority_state"] != "NOT_AUTHORITATIVE":
        raise RetainedValidationError("non-authoritative gate cannot bind authority")
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
    preflight: Mapping[str, Any] | None = None,
    global_authority_artifact: ImmutableArtifactWriteResult | None = None,
    fault_point: str | None = None,
) -> dict[str, Any]:
    preflight_payload = preflight or {}
    return {
        "schema": RETAINED_RUN_RESULT_SCHEMA,
        "record_type": "RUN_RESULT",
        "authorization_identity": authorization.authorization_identity,
        "assessment_identity": authorization.assessment_identity,
        "mode": authorization.mode,
        "control_mode": validation.ABSOLUTE_PATH_CONTROL_MODE,
        "authoritative": authorization.authoritative,
        "preparation_phase": RETAINED_PREPARATION_PHASE,
        "repository_state": dict(
            preflight_payload.get("repository_state", {"state": "NOT_RECORDED"})
        ),
        "source_identities": list(preflight_payload.get("source_identities", [])),
        "retained_orchestration_policy_identity": validate_policy_identity(
            authorized_absolute_path_control_policy_identity()
        ),
        "native_helper_policy_identity": validate_native_helper_policy_identity(
            native_helper_policy_identity()
        ),
        "schema_identity": retained_schema_identity(),
        "case_set_identity": retained_case_set_identity(
            selected_cases=authorization.selected_cases,
            optional_cases=authorization.optional_cases,
        ),
        "fixture_profile_identity": fixture_profile_identity(),
        "global_authority_state": (
            {
                "path": global_authority_artifact.path,
                "sha256": global_authority_artifact.sha256,
                "byte_length": global_authority_artifact.byte_length,
            }
            if global_authority_artifact is not None
            else "NOT_AUTHORITATIVE"
        ),
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
        "completion_receipt": "ABSENT",
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
        "record_type",
        "authorization_identity",
        "assessment_identity",
        "mode",
        "control_mode",
        "authoritative",
        "preparation_phase",
        "repository_state",
        "source_identities",
        "retained_orchestration_policy_identity",
        "native_helper_policy_identity",
        "schema_identity",
        "case_set_identity",
        "fixture_profile_identity",
        "global_authority_state",
        "native_boundary",
        "gate_state",
        "native_invocation_started",
        "case_outcomes",
        "artifact_state",
        "completion_receipt",
        "fault_injection",
        "primary_failure",
        "detail",
        "terminal_state",
        "retained_execution",
    }
    if set(record) != required:
        raise RetainedValidationError("RUN_RESULT has unexpected schema fields")
    if record["schema"] != RETAINED_RUN_RESULT_SCHEMA:
        raise RetainedValidationError("RUN_RESULT schema mismatch")
    if record["record_type"] != "RUN_RESULT":
        raise RetainedValidationError("RUN_RESULT record type mismatch")
    require_retained_mode(str(record["mode"]))
    if record["control_mode"] != validation.ABSOLUTE_PATH_CONTROL_MODE:
        raise RetainedValidationError("RUN_RESULT control mode mismatch")
    validate_policy_identity(record["retained_orchestration_policy_identity"])
    validate_native_helper_policy_identity(record["native_helper_policy_identity"])
    if record["schema_identity"] != retained_schema_identity():
        raise RetainedValidationError("RUN_RESULT schema identity mismatch")
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
    if record["retained_execution"] is not False:
        raise RetainedValidationError("RUN_RESULT cannot claim retained execution")
    if record["completion_receipt"] != "ABSENT":
        raise RetainedValidationError("RUN_RESULT completion receipt must be absent")
    if record["authoritative"] is True:
        global_state = _require_mapping(
            record["global_authority_state"],
            "global_authority_state",
        )
        _require_hex64(str(global_state.get("sha256")), "global authority hash")
    elif record["global_authority_state"] != "NOT_AUTHORITATIVE":
        raise RetainedValidationError("non-authoritative RUN_RESULT cannot bind authority")
    gate_state = _require_mapping(record["gate_state"], "gate_state")
    if gate_state.get("consumed") is False and record["native_invocation_started"]:
        raise RetainedValidationError("native invocation cannot start before gate")
    case_outcomes = _require_mapping(record["case_outcomes"], "case_outcomes")
    _validate_terminal_case_outcomes(case_outcomes)
    artifact_state = _require_mapping(record["artifact_state"], "artifact_state")
    fault_injection = _require_mapping(record["fault_injection"], "fault_injection")
    if terminal_state == RUN_COMPLETE and not case_outcomes.get("gating_satisfied"):
        raise RetainedValidationError("RUN_COMPLETE requires satisfied gating cases")
    if terminal_state == RUN_COMPLETE and record["native_invocation_started"] is not True:
        raise RetainedValidationError("RUN_COMPLETE requires native invocation")
    if fault_injection.get("active") is True and terminal_state == RUN_COMPLETE:
        if artifact_state.get("terminal_artifact_written") is True:
            raise RetainedValidationError("fault injection cannot complete RUN_RESULT")
    _require_mapping(artifact_state, "artifact_state")


def build_artifact_wrapper(terminal_record: Mapping[str, Any]) -> dict[str, Any]:
    validate_terminal_record(terminal_record)
    record_bytes = canonical_json_bytes(dict(terminal_record))
    return {
        "schema": RETAINED_TERMINAL_ARTIFACT_SCHEMA,
        "terminal_record": dict(terminal_record),
        "terminal_record_byte_length": len(record_bytes),
        "terminal_record_sha256": hashlib.sha256(record_bytes).hexdigest(),
    }


def validate_run_result_artifact(path: str | Path) -> dict[str, Any]:
    payload = Path(path).read_bytes()
    record = load_canonical_json_bytes(payload)
    validate_terminal_record(record)
    return record


def validate_terminal_artifact(path: str | Path) -> dict[str, Any]:
    payload = Path(path).read_bytes()
    loaded = load_canonical_json_bytes(payload)
    if isinstance(loaded, Mapping) and loaded.get("record_type") == "RUN_RESULT":
        validate_terminal_record(loaded)
        terminal_bytes = canonical_json_bytes(loaded)
        return {
            "schema": RETAINED_TERMINAL_ARTIFACT_SCHEMA,
            "terminal_record": dict(loaded),
            "terminal_record_byte_length": len(terminal_bytes),
            "terminal_record_sha256": hashlib.sha256(terminal_bytes).hexdigest(),
        }
    wrapper = loaded
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


def build_retained_completion_record(
    *,
    authorization: RetainedAuthorization,
    run_result_record: Mapping[str, Any],
    run_result_artifact: ImmutableArtifactWriteResult,
    gate_artifact: ImmutableArtifactWriteResult,
    global_authority_artifact: ImmutableArtifactWriteResult,
) -> dict[str, Any]:
    validate_terminal_record(run_result_record)
    if authorization.execution_authorization is None:
        raise RetainedValidationError(AUTHORITATIVE_AUTHORIZATION_MISSING)
    if authorization.authoritative is not True:
        raise RetainedValidationError(RETAINED_COMPLETION_PRECONDITION_FAILURE)
    if run_result_record["terminal_state"] != RUN_COMPLETE:
        raise RetainedValidationError(RETAINED_COMPLETION_PRECONDITION_FAILURE)
    if run_result_record["case_outcomes"]["gating_satisfied"] is not True:
        raise RetainedValidationError(RETAINED_COMPLETION_PRECONDITION_FAILURE)
    if run_result_artifact.reread_verified is not True:
        raise RetainedValidationError(RETAINED_COMPLETION_PRECONDITION_FAILURE)
    return {
        "schema": RETAINED_COMPLETION_SCHEMA,
        "record_type": "RETAINED_COMPLETION",
        "execution_authorization_identity": authorization.authorization_identity,
        "assessment_identity": authorization.assessment_identity,
        "mode": authorization.mode,
        "authoritative": True,
        "retained_execution": True,
        "global_authority_entry_hash": global_authority_artifact.sha256,
        "local_gate_hash": gate_artifact.sha256,
        "run_result_hash": run_result_artifact.sha256,
        "run_result_byte_length": run_result_artifact.byte_length,
        "repository_state": dict(
            run_result_record.get("repository_state", "NOT_RECORDED")
            if isinstance(run_result_record.get("repository_state"), Mapping)
            else {"state": "BOUND_BY_GLOBAL_AUTHORITY_ENTRY"}
        ),
        "retained_orchestration_policy_identity": validate_policy_identity(
            authorized_absolute_path_control_policy_identity()
        ),
        "native_helper_policy_identity": validate_native_helper_policy_identity(
            native_helper_policy_identity()
        ),
        "schema_identity": retained_schema_identity(),
        "case_set_identity": retained_case_set_identity(
            selected_cases=authorization.selected_cases,
            optional_cases=authorization.optional_cases,
        ),
        "fixture_profile_identity": fixture_profile_identity(),
        "path_identities": (
            authorization.execution_authorization.as_payload()
        ),
        "run_identity": authorization.execution_authorization.run_identity,
        "all_gating_outcomes_satisfied": True,
        "a5_identity_continuity_satisfied": (
            run_result_record["case_outcomes"]["gating_satisfied_by_case"][A5]
        ),
        "a2_a3_preservation_satisfied": (
            run_result_record["case_outcomes"]["gating_satisfied_by_case"][A2]
            and run_result_record["case_outcomes"]["gating_satisfied_by_case"][A3]
        ),
        "content_continuity_satisfied": True,
        "run_result_durability_verified": True,
        "run_result_reread_verified": run_result_artifact.reread_verified,
        "run_result_hash_verified": run_result_artifact.hash_verified,
    }


def validate_retained_completion_record(record: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "record_type",
        "execution_authorization_identity",
        "assessment_identity",
        "mode",
        "authoritative",
        "retained_execution",
        "global_authority_entry_hash",
        "local_gate_hash",
        "run_result_hash",
        "run_result_byte_length",
        "repository_state",
        "retained_orchestration_policy_identity",
        "native_helper_policy_identity",
        "schema_identity",
        "case_set_identity",
        "fixture_profile_identity",
        "path_identities",
        "run_identity",
        "all_gating_outcomes_satisfied",
        "a5_identity_continuity_satisfied",
        "a2_a3_preservation_satisfied",
        "content_continuity_satisfied",
        "run_result_durability_verified",
        "run_result_reread_verified",
        "run_result_hash_verified",
    }
    if set(record) != required:
        raise RetainedValidationError("retained completion has unexpected fields")
    if record["schema"] != RETAINED_COMPLETION_SCHEMA:
        raise RetainedValidationError("retained completion schema mismatch")
    if record["record_type"] != "RETAINED_COMPLETION":
        raise RetainedValidationError("retained completion record type mismatch")
    require_retained_mode(str(record["mode"]))
    if record["authoritative"] is not True:
        raise RetainedValidationError("retained completion requires authority")
    if record["retained_execution"] is not True:
        raise RetainedValidationError("completion must declare retained execution")
    for key in ("global_authority_entry_hash", "local_gate_hash", "run_result_hash"):
        _require_hex64(str(record[key]), key)
    validate_policy_identity(record["retained_orchestration_policy_identity"])
    validate_native_helper_policy_identity(record["native_helper_policy_identity"])
    if record["schema_identity"] != retained_schema_identity():
        raise RetainedValidationError("completion schema identity mismatch")
    for key in (
        "all_gating_outcomes_satisfied",
        "a5_identity_continuity_satisfied",
        "a2_a3_preservation_satisfied",
        "content_continuity_satisfied",
        "run_result_durability_verified",
        "run_result_reread_verified",
        "run_result_hash_verified",
    ):
        if record[key] is not True:
            raise RetainedValidationError(RETAINED_COMPLETION_PRECONDITION_FAILURE)


def validate_retained_completion_artifact(path: str | Path) -> dict[str, Any]:
    payload = Path(path).read_bytes()
    record = load_canonical_json_bytes(payload)
    validate_retained_completion_record(record)
    return record


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
    preflight: Mapping[str, Any],
    global_authority_artifact: ImmutableArtifactWriteResult | None,
    global_authority_consumed: bool,
    gate_artifact: ImmutableArtifactWriteResult,
    terminal_state: str,
    gate_consumed: bool,
    native_invocation_started: bool,
    primary_failure: str,
    detail: str,
    case_outcomes: Mapping[str, Any],
    fault_point: str | None,
) -> RetainedRunResult:
    effective_fault_point = _normalize_run_result_fault_point(fault_point)
    run_result_record = build_terminal_record(
        authorization=authorization,
        terminal_state=terminal_state,
        gate_consumed=gate_consumed,
        native_invocation_started=native_invocation_started,
        retained_execution=False,
        primary_failure=primary_failure,
        detail=detail,
        case_outcomes=case_outcomes,
        gate_artifact=gate_artifact,
        artifact_state=pending_artifact_state(),
        preflight=preflight,
        global_authority_artifact=global_authority_artifact,
        fault_point=effective_fault_point,
    )
    if effective_fault_point == FAULT_DURING_RUN_RESULT_SERIALIZATION:
        return _run_result(
            terminal_state=ARTIFACT_PERSISTENCE_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=RUN_RESULT_SERIALIZATION_FAILURE,
            detail="fault injected during RUN_RESULT serialization",
            global_authority_artifact=global_authority_artifact,
            gate_artifact=gate_artifact,
            run_result_record=run_result_record,
        )
    validate_terminal_record(run_result_record)
    try:
        run_result_artifact = _write_canonical_file(
            result_directory / RUN_RESULT_FILENAME,
            run_result_record,
            adapter=adapter,
            fault_point=effective_fault_point,
            fault_file_write=FAULT_DURING_RUN_RESULT_FILE_WRITE,
            fault_directory_sync=FAULT_DURING_RUN_RESULT_DIRECTORY_SYNC,
            fault_reread=FAULT_DURING_RUN_RESULT_REREAD,
        )
        validate_run_result_artifact(result_directory / RUN_RESULT_FILENAME)
    except ArtifactPersistenceError as exc:
        return _run_result(
            terminal_state=ARTIFACT_PERSISTENCE_FAILED
            if exc.failure_code == RUN_RESULT_PERSISTENCE_FAILURE
            else ARTIFACT_REVERIFY_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=exc.failure_code,
            detail=exc.detail,
            global_authority_artifact=global_authority_artifact,
            gate_artifact=gate_artifact,
            run_result_record=run_result_record,
            terminal_record=run_result_record,
        )
    except RetainedValidationError as exc:
        return _run_result(
            terminal_state=ARTIFACT_REVERIFY_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=RUN_RESULT_REVERIFY_FAILURE,
            detail=str(exc),
            global_authority_artifact=global_authority_artifact,
            gate_artifact=gate_artifact,
            run_result_record=run_result_record,
            terminal_record=run_result_record,
        )
    if (
        authorization.authoritative is not True
        or terminal_state != RUN_COMPLETE
        or primary_failure != "NONE"
        or effective_fault_point is not None
    ):
        return _run_result(
            terminal_state=terminal_state,
            authorization=authorization,
            result_directory=result_directory,
            retained_execution=False,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=primary_failure,
            detail=detail,
            global_authority_artifact=global_authority_artifact,
            gate_artifact=gate_artifact,
            run_result_artifact=run_result_artifact,
            terminal_artifact=run_result_artifact,
            run_result_record=run_result_record,
            terminal_record=run_result_record,
        )
    if global_authority_artifact is None:
        return _run_result(
            terminal_state=ARTIFACT_PERSISTENCE_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            retained_execution=False,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=EVIDENCE_CHAIN_LINKAGE_FAILURE,
            detail="authoritative completion requires global authority artifact",
            gate_artifact=gate_artifact,
            run_result_artifact=run_result_artifact,
            terminal_artifact=run_result_artifact,
            run_result_record=run_result_record,
            terminal_record=run_result_record,
        )
    if fault_point == FAULT_BEFORE_RETAINED_COMPLETION_CREATION:
        return _run_result(
            terminal_state=ARTIFACT_PERSISTENCE_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            retained_execution=False,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=FAULT_INJECTION_TRIGGERED,
            detail="fault injected before RETAINED_COMPLETION creation",
            global_authority_artifact=global_authority_artifact,
            gate_artifact=gate_artifact,
            run_result_artifact=run_result_artifact,
            terminal_artifact=run_result_artifact,
            run_result_record=run_result_record,
            terminal_record=run_result_record,
        )
    if fault_point == FAULT_DURING_COMPLETION_SERIALIZATION:
        return _run_result(
            terminal_state=ARTIFACT_PERSISTENCE_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            retained_execution=False,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=RETAINED_COMPLETION_SERIALIZATION_FAILURE,
            detail="fault injected during RETAINED_COMPLETION serialization",
            global_authority_artifact=global_authority_artifact,
            gate_artifact=gate_artifact,
            run_result_artifact=run_result_artifact,
            terminal_artifact=run_result_artifact,
            run_result_record=run_result_record,
            terminal_record=run_result_record,
        )
    try:
        completion_record = build_retained_completion_record(
            authorization=authorization,
            run_result_record=run_result_record,
            run_result_artifact=run_result_artifact,
            gate_artifact=gate_artifact,
            global_authority_artifact=global_authority_artifact,
        )
        validate_retained_completion_record(completion_record)
        completion_artifact = _write_canonical_file(
            result_directory / RETAINED_COMPLETION_FILENAME,
            completion_record,
            adapter=adapter,
            fault_point=fault_point,
            fault_file_write=FAULT_DURING_COMPLETION_FILE_WRITE,
            fault_directory_sync=FAULT_DURING_COMPLETION_DIRECTORY_SYNC,
            fault_reread=FAULT_DURING_COMPLETION_REREAD,
        )
        validate_retained_completion_artifact(
            result_directory / RETAINED_COMPLETION_FILENAME
        )
    except ArtifactPersistenceError as exc:
        return _run_result(
            terminal_state=ARTIFACT_PERSISTENCE_FAILED
            if exc.failure_code == RETAINED_COMPLETION_PERSISTENCE_FAILURE
            else ARTIFACT_REVERIFY_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            retained_execution=False,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=exc.failure_code,
            detail=exc.detail,
            global_authority_artifact=global_authority_artifact,
            gate_artifact=gate_artifact,
            run_result_artifact=run_result_artifact,
            terminal_artifact=run_result_artifact,
            run_result_record=run_result_record,
            terminal_record=run_result_record,
        )
    except RetainedValidationError as exc:
        return _run_result(
            terminal_state=ARTIFACT_REVERIFY_FAILED,
            authorization=authorization,
            result_directory=result_directory,
            retained_execution=False,
            global_authority_consumed=global_authority_consumed,
            gate_consumed=gate_consumed,
            native_invocation_started=native_invocation_started,
            primary_failure=RETAINED_COMPLETION_REVERIFY_FAILURE,
            detail=str(exc),
            global_authority_artifact=global_authority_artifact,
            gate_artifact=gate_artifact,
            run_result_artifact=run_result_artifact,
            terminal_artifact=run_result_artifact,
            run_result_record=run_result_record,
            terminal_record=run_result_record,
        )
    return _run_result(
        terminal_state=terminal_state,
        authorization=authorization,
        result_directory=result_directory,
        retained_execution=completion_record["retained_execution"],
        global_authority_consumed=global_authority_consumed,
        gate_consumed=gate_consumed,
        native_invocation_started=native_invocation_started,
        primary_failure=primary_failure,
        detail=detail,
        global_authority_artifact=global_authority_artifact,
        gate_artifact=gate_artifact,
        run_result_artifact=run_result_artifact,
        retained_completion_artifact=completion_artifact,
        terminal_artifact=run_result_artifact,
        run_result_record=run_result_record,
        retained_completion_record=completion_record,
        terminal_record=run_result_record,
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
    global_authority_consumed: bool,
    retained_execution: bool = False,
    gate_consumed: bool,
    native_invocation_started: bool,
    primary_failure: str | None,
    detail: str,
    global_authority_artifact: ImmutableArtifactWriteResult | None = None,
    gate_artifact: ImmutableArtifactWriteResult | None = None,
    run_result_artifact: ImmutableArtifactWriteResult | None = None,
    retained_completion_artifact: ImmutableArtifactWriteResult | None = None,
    terminal_artifact: ImmutableArtifactWriteResult | None = None,
    run_result_record: dict[str, Any] | None = None,
    retained_completion_record: dict[str, Any] | None = None,
    terminal_record: dict[str, Any] | None = None,
) -> RetainedRunResult:
    if terminal_state not in TERMINAL_STATES:
        raise RetainedValidationError("unknown terminal state")
    return RetainedRunResult(
        terminal_state=terminal_state,
        retained_execution=retained_execution,
        authoritative=authorization.authoritative,
        global_authority_consumed=global_authority_consumed,
        gate_consumed=gate_consumed,
        native_invocation_started=native_invocation_started,
        primary_failure=primary_failure,
        detail=detail,
        result_directory=str(result_directory),
        global_authority_artifact=global_authority_artifact,
        gate_artifact=gate_artifact,
        run_result_artifact=run_result_artifact,
        retained_completion_artifact=retained_completion_artifact,
        terminal_artifact=terminal_artifact,
        run_result_record=run_result_record,
        retained_completion_record=retained_completion_record,
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
        validate_native_helper_policy_identity(result.policy_identity or {})
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


def _admit_authority_registry_root(
    authority_root: str | Path,
    *,
    repo_root: Path,
) -> Path:
    root = Path(authority_root).resolve()
    _admit_drive_qualified_dos_path(root)
    if not root.exists() or not root.is_dir():
        raise RetainedValidationError("authority registry root must exist")
    if _is_relative_to(root, repo_root):
        raise RetainedValidationError("authority registry root must be outside repository")
    if _is_reparse_point(root):
        raise RetainedValidationError("authority registry root must not be reparse")
    return root


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
        if text == failure_code:
            return failure_code
    for failure_code in sorted(FAILURE_CODES, key=len, reverse=True):
        if failure_code in text:
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
    if path.name.endswith(GLOBAL_AUTHORITY_ENTRY_SUFFIX):
        return GLOBAL_AUTHORITY_ENTRY_PERSISTENCE_FAILURE
    if path.name == GATE_ENTRY_FILENAME:
        return GATE_ENTRY_WRITE_FAILURE
    if path.name == RUN_RESULT_FILENAME:
        return RUN_RESULT_PERSISTENCE_FAILURE
    if path.name == RETAINED_COMPLETION_FILENAME:
        return RETAINED_COMPLETION_PERSISTENCE_FAILURE
    return TERMINAL_ARTIFACT_WRITE_FAILURE


def _reread_failure_code_for(path: Path) -> str:
    if path.name.endswith(GLOBAL_AUTHORITY_ENTRY_SUFFIX):
        return GLOBAL_AUTHORITY_ENTRY_REVERIFY_FAILURE
    if path.name == GATE_ENTRY_FILENAME:
        return GATE_ENTRY_REVERIFY_FAILURE
    if path.name == RUN_RESULT_FILENAME:
        return RUN_RESULT_REVERIFY_FAILURE
    if path.name == RETAINED_COMPLETION_FILENAME:
        return RETAINED_COMPLETION_REVERIFY_FAILURE
    return TERMINAL_ARTIFACT_REVERIFY_FAILURE


def _normalize_run_result_fault_point(fault_point: str | None) -> str | None:
    if fault_point in {
        FAULT_BEFORE_RETAINED_COMPLETION_CREATION,
        FAULT_DURING_COMPLETION_SERIALIZATION,
        FAULT_DURING_COMPLETION_FILE_WRITE,
        FAULT_DURING_COMPLETION_DIRECTORY_SYNC,
        FAULT_DURING_COMPLETION_REREAD,
    }:
        return None
    aliases = {
        FAULT_DURING_TERMINAL_FILE_WRITE: FAULT_DURING_RUN_RESULT_FILE_WRITE,
        FAULT_DURING_TERMINAL_DIRECTORY_SYNC: FAULT_DURING_RUN_RESULT_DIRECTORY_SYNC,
        FAULT_DURING_TERMINAL_REREAD: FAULT_DURING_RUN_RESULT_REREAD,
    }
    return aliases.get(fault_point, fault_point)


def runtime_platform_observation() -> dict[str, Any]:
    return {
        "schema": "torment.brainvision.blocker2.retained.platform.v0.1",
        "sys_platform": sys.platform,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
    }
