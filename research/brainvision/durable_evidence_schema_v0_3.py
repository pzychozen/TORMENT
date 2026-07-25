from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any


PROTOCOL_IDENTITY = "torment-brainvision-durable-evidence-v0.3"

SCIENTIFIC_LOGICAL_RECORD_SCHEMA = "scientific-logical-record-v0.3"
PUBLICATION_LOGICAL_RECORD_SCHEMA = "publication-logical-record-v0.3"
PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA = "publication-recovery-logical-record-v0.3"
STORED_RECORD_OBJECT_SCHEMA = "stored-record-object-v0.3"
IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA = "immutable-scientific-bundle-v0.3"
STORED_BUNDLE_OBJECT_SCHEMA = "stored-bundle-object-v0.3"
SCIENTIFIC_COMPLETION_RECEIPT_SCHEMA = "scientific-completion-receipt-v0.3"
PUBLICATION_PROJECTION_RECIPE_SCHEMA = "publication-projection-recipe-v0.3"

PASS_BUNDLE_SCHEMA = "torment-brainvision-synthetic-validation-pass-bundle-v0.3"

GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256 = "0" * 64

MAX_NESTING_DEPTH = 32
MAX_CONTAINER_MEMBER_COUNT = 4096
MAX_STORED_RECORD_OBJECT_BYTES = 65536
MAX_STORED_BUNDLE_OBJECT_BYTES = 4194304

MAX_RESOURCE_NESTING_DEPTH = MAX_NESTING_DEPTH
MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER = MAX_CONTAINER_MEMBER_COUNT
MAX_RESOURCE_TOTAL_NODE_COUNT = 16384
MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES = 1048576
MAX_RESOURCE_TOTAL_STRING_ASCII_BYTES = 4194304
MAX_RESOURCE_INTEGER_ABS = 9223372036854775807
MAX_PUBLICATION_SOURCE_BUNDLE_BYTES = 4194304

MAX_PUBLICATION_ARTIFACT_COUNT = 3
MAX_PUBLICATION_RESULT_ARTIFACT_BYTES = 16384
MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES = 8388608
MAX_PUBLICATION_SUMMARY_BYTES = 1024
MAX_PUBLICATION_ARTIFACT_SET_BYTES = 8406016
MAX_PUBLICATION_STAGING_WRITE_BYTES = 8406016
MAX_PUBLICATION_RECOVERY_VERIFICATION_BYTES = 8406016

DIRECTORY_DURABILITY_POLICY_SCHEMA = (
    "durable-evidence-windows-directory-durability-policy-v0.1"
)
DIRECTORY_DURABILITY_ADAPTER_IDENTITY = (
    "durable_evidence_windows_adapter_v0_3.Win32DirectoryDurabilityAdapter"
)
DIRECTORY_DURABILITY_OPERATION_IDENTITY = (
    "win32-createfilew-flushfilebuffers-directory-entry-v0.1"
)
DIRECTORY_DURABILITY_FAILURE_MAPPING_VERSION = (
    "windows-directory-durability-failure-mapping-v0.1"
)
DIRECTORY_DURABILITY_VALIDATION_PROFILE_IDENTITY = (
    "windows-10-11-local-fixed-ntfs-pytest-tmp-directory-v0.1"
)
ARTIFACT_PARENT_DIRECTORY = "ARTIFACT_PARENT_DIRECTORY"
STAGING_PARENT_DIRECTORY = "STAGING_PARENT_DIRECTORY"
STAGING_DIRECTORY = "STAGING_DIRECTORY"
FINAL_PARENT_DIRECTORY = "FINAL_PARENT_DIRECTORY"
DIRECTORY_DURABILITY_TARGET_ROLES = (
    ARTIFACT_PARENT_DIRECTORY,
    STAGING_PARENT_DIRECTORY,
    STAGING_DIRECTORY,
    FINAL_PARENT_DIRECTORY,
)
DIRECTORY_DURABILITY_CONFIRMED = "DIRECTORY_DURABILITY_CONFIRMED"
DIRECTORY_DURABILITY_UNSUPPORTED = "DIRECTORY_DURABILITY_UNSUPPORTED"
DIRECTORY_DURABILITY_DENIED = "DIRECTORY_DURABILITY_DENIED"
DIRECTORY_DURABILITY_INDETERMINATE = "DIRECTORY_DURABILITY_INDETERMINATE"
DIRECTORY_DURABILITY_TARGET_INVALID = "DIRECTORY_DURABILITY_TARGET_INVALID"
DIRECTORY_DURABILITY_IDENTITY_CHANGED = "DIRECTORY_DURABILITY_IDENTITY_CHANGED"
DIRECTORY_DURABILITY_OPERATION_FAILED = "DIRECTORY_DURABILITY_OPERATION_FAILED"
DIRECTORY_DURABILITY_STATUS_TAXONOMY = (
    DIRECTORY_DURABILITY_CONFIRMED,
    DIRECTORY_DURABILITY_UNSUPPORTED,
    DIRECTORY_DURABILITY_DENIED,
    DIRECTORY_DURABILITY_INDETERMINATE,
    DIRECTORY_DURABILITY_TARGET_INVALID,
    DIRECTORY_DURABILITY_IDENTITY_CHANGED,
    DIRECTORY_DURABILITY_OPERATION_FAILED,
)
ADAPTER_ABSENT = "ADAPTER_ABSENT"
NON_WINDOWS_PLATFORM = "NON_WINDOWS_PLATFORM"
WINDOWS_VERSION_UNSUPPORTED = "WINDOWS_VERSION_UNSUPPORTED"
DRIVE_TYPE_UNSUPPORTED = "DRIVE_TYPE_UNSUPPORTED"
FILESYSTEM_UNSUPPORTED = "FILESYSTEM_UNSUPPORTED"
TARGET_NOT_ABSOLUTE = "TARGET_NOT_ABSOLUTE"
TARGET_INVALID = "TARGET_INVALID"
TARGET_MISSING = "TARGET_MISSING"
TARGET_NOT_DIRECTORY = "TARGET_NOT_DIRECTORY"
TARGET_REPARSE_POINT = "TARGET_REPARSE_POINT"
TARGET_IDENTITY_UNAVAILABLE = "TARGET_IDENTITY_UNAVAILABLE"
TARGET_IDENTITY_CHANGED = "TARGET_IDENTITY_CHANGED"
DIRECTORY_OPEN_UNSUPPORTED = "DIRECTORY_OPEN_UNSUPPORTED"
DIRECTORY_OPEN_DENIED = "DIRECTORY_OPEN_DENIED"
DIRECTORY_OPEN_FAILED = "DIRECTORY_OPEN_FAILED"
DIRECTORY_FLUSH_UNSUPPORTED = "DIRECTORY_FLUSH_UNSUPPORTED"
DIRECTORY_FLUSH_DENIED = "DIRECTORY_FLUSH_DENIED"
DIRECTORY_FLUSH_FAILED = "DIRECTORY_FLUSH_FAILED"
DIRECTORY_CLOSE_INDETERMINATE = "DIRECTORY_CLOSE_INDETERMINATE"
UNKNOWN_NATIVE_ERROR = "UNKNOWN_NATIVE_ERROR"
UNEXPECTED_EXCEPTION = "UNEXPECTED_EXCEPTION"
POLICY_IDENTITY_MISMATCH = "POLICY_IDENTITY_MISMATCH"
DIRECTORY_DURABILITY_FAILURE_CODES = (
    ADAPTER_ABSENT,
    NON_WINDOWS_PLATFORM,
    WINDOWS_VERSION_UNSUPPORTED,
    DRIVE_TYPE_UNSUPPORTED,
    FILESYSTEM_UNSUPPORTED,
    TARGET_NOT_ABSOLUTE,
    TARGET_INVALID,
    TARGET_MISSING,
    TARGET_NOT_DIRECTORY,
    TARGET_REPARSE_POINT,
    TARGET_IDENTITY_UNAVAILABLE,
    TARGET_IDENTITY_CHANGED,
    DIRECTORY_OPEN_UNSUPPORTED,
    DIRECTORY_OPEN_DENIED,
    DIRECTORY_OPEN_FAILED,
    DIRECTORY_FLUSH_UNSUPPORTED,
    DIRECTORY_FLUSH_DENIED,
    DIRECTORY_FLUSH_FAILED,
    DIRECTORY_CLOSE_INDETERMINATE,
    UNKNOWN_NATIVE_ERROR,
    UNEXPECTED_EXCEPTION,
    POLICY_IDENTITY_MISMATCH,
)
DIRECTORY_DURABILITY_POLICY_DECLARATION_KEYS = (
    "policy_schema_identity",
    "adapter_identity",
    "operation_identity",
    "supported_windows_profile",
    "supported_filesystem_profile",
    "target_role_declaration",
    "status_taxonomy",
    "failure_mapping_version",
    "failure_code_vocabulary",
    "path_normalization_policy",
    "reparse_point_policy",
    "validation_profile_identity",
)
DIRECTORY_DURABILITY_POLICY_IDENTITY_KEYS = (
    "policy_schema_identity",
    "policy_sha256",
)

RESOURCE_ADMISSIBILITY_POLICY_SCHEMA = (
    "durable-evidence-resource-admissibility-policy-v0.3"
)
RESOURCE_ADMISSIBILITY_POLICY_DECLARATION_KEYS = (
    "policy_schema_identity",
    "max_resource_nesting_depth",
    "max_resource_container_members_per_container",
    "max_stored_record_object_bytes",
    "max_stored_bundle_object_bytes",
    "max_resource_total_node_count",
    "max_resource_single_string_ascii_bytes",
    "max_resource_total_string_ascii_bytes",
    "max_resource_integer_abs",
    "max_publication_source_bundle_bytes",
    "max_publication_artifact_count",
    "max_publication_result_artifact_bytes",
    "max_publication_execution_envelope_bytes",
    "max_publication_summary_bytes",
    "max_publication_artifact_set_bytes",
    "max_publication_staging_write_bytes",
    "max_publication_recovery_verification_bytes",
)
RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_KEYS = (
    "policy_schema_identity",
    "policy_sha256",
)

RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
ARTIFACT_SIZE_LIMIT_EXCEEDED = "ARTIFACT_SIZE_LIMIT_EXCEEDED"
ARTIFACT_SET_SIZE_LIMIT_EXCEEDED = "ARTIFACT_SET_SIZE_LIMIT_EXCEEDED"
SUMMARY_SIZE_LIMIT_EXCEEDED = "SUMMARY_SIZE_LIMIT_EXCEEDED"
CANONICAL_STRUCTURE_LIMIT_EXCEEDED = "CANONICAL_STRUCTURE_LIMIT_EXCEEDED"
STRING_SIZE_LIMIT_EXCEEDED = "STRING_SIZE_LIMIT_EXCEEDED"
INTEGER_MAGNITUDE_LIMIT_EXCEEDED = "INTEGER_MAGNITUDE_LIMIT_EXCEEDED"
RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH = (
    "RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH"
)
STAGING_SPACE_BUDGET_UNAVAILABLE = "STAGING_SPACE_BUDGET_UNAVAILABLE"
RESOURCE_ADMISSIBILITY_INDETERMINATE = "RESOURCE_ADMISSIBILITY_INDETERMINATE"
RECOVERY_VERIFICATION_BUDGET_EXCEEDED = "RECOVERY_VERIFICATION_BUDGET_EXCEEDED"
RECOVERY_ARTIFACT_TYPE_INVALID = "RECOVERY_ARTIFACT_TYPE_INVALID"
RECOVERY_ARTIFACT_READ_INDETERMINATE = "RECOVERY_ARTIFACT_READ_INDETERMINATE"

SCIENTIFIC_RESULT_KINDS = frozenset(
    ("SYNTHETIC_GATE_PASSED", "SYNTHETIC_GATE_FAILED")
)

SCIENTIFIC_RECORD_KINDS = frozenset(
    (
        "AUTHORITY_CONSUMED",
        "MANIFEST_CONTACT_ATTEMPT",
        "MANIFEST_READ_SUCCESS",
        "SCIENTIFIC_COMPLETION",
        "SCIENTIFIC_TERMINAL_STATUS",
    )
)

PUBLICATION_RECORD_KINDS = frozenset(
    (
        "PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED",
        "PUBLICATION_ATTEMPTED",
        "PUBLICATION_COMPLETED",
        "PUBLICATION_TERMINAL_STATUS",
    )
)

PUBLICATION_RECOVERY_RECORD_KINDS = frozenset(
    (
        "PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED",
        "PUBLICATION_RECOVERY_ATTEMPTED",
        "PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED",
        "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED",
        "PUBLICATION_RECOVERY_TERMINAL_STATUS",
    )
)

SCIENTIFIC_LOGICAL_RECORD_KEYS = (
    "protocol_identity",
    "record_schema_identity",
    "record_kind",
    "sequence_number",
    "execution_identity",
    "scientific_execution_authorization_identity",
    "predecessor_logical_record_sha256",
    "payload",
    "logical_record_sha256",
)

PUBLICATION_LOGICAL_RECORD_KEYS = (
    "protocol_identity",
    "record_schema_identity",
    "record_kind",
    "sequence_number",
    "execution_identity",
    "publication_projection_authorization_identity",
    "publication_chain_identity",
    "predecessor_logical_record_sha256",
    "payload",
    "logical_record_sha256",
)

PUBLICATION_RECOVERY_LOGICAL_RECORD_KEYS = (
    "protocol_identity",
    "record_schema_identity",
    "record_kind",
    "sequence_number",
    "execution_identity",
    "publication_recovery_authorization_identity",
    "publication_recovery_chain_identity",
    "predecessor_logical_record_sha256",
    "payload",
    "logical_record_sha256",
)

STORED_RECORD_OBJECT_KEYS = (
    "storage_schema_identity",
    "logical_record_sha256",
    "writer_identity",
    "writer_attempt_identity",
    "stored_object_sha256",
    "logical_record",
)

STORED_RECORD_OBJECT_PREIMAGE_KEYS = tuple(
    key for key in STORED_RECORD_OBJECT_KEYS if key != "stored_object_sha256"
)

BUNDLE_PAYLOAD_KEYS = (
    "bundle_schema_identity",
    "protocol_identity",
    "execution_identity",
    "scientific_execution_authorization_identity",
    "scientific_result_kind",
    "pass_bundle_sha256",
    "two_pass_canonical_identity_status",
    "configuration_identity",
    "manifest_identities",
    "implementation_identities",
    "descriptor_identity",
    "repository_execution_context",
    "publication_projection_source",
    "bundle_payload_sha256",
)

STORED_BUNDLE_OBJECT_KEYS = (
    "storage_schema_identity",
    "bundle_payload_sha256",
    "bundle_payload_byte_length",
    "writer_identity",
    "writer_attempt_identity",
    "stored_bundle_object_sha256",
    "bundle_payload",
)

STORED_BUNDLE_OBJECT_PREIMAGE_KEYS = tuple(
    key for key in STORED_BUNDLE_OBJECT_KEYS if key != "stored_bundle_object_sha256"
)

PUBLICATION_CHAIN_IDENTITY_KEYS = (
    "publication_projection_identity",
    "publication_projection_authorization_identity",
)

PUBLICATION_RECOVERY_CHAIN_IDENTITY_KEYS = (
    "original_publication_chain_identity",
    "publication_recovery_authorization_identity",
)
PUBLICATION_PROJECTION_IDENTITY_KEYS = (
    "execution_identity",
    "bundle_payload_sha256",
    "scientific_completion_logical_record_sha256",
    "publication_recipe_identity",
    "publication_utility_identities",
)

PUBLICATION_RESULT_ARTIFACT_SCHEMA = (
    "torment-brainvision-synthetic-validation-result-v0.3"
)
PUBLICATION_EXECUTION_ENVELOPE_SCHEMA = (
    "torment-brainvision-synthetic-validation-execution-envelope-v0.3"
)
PUBLICATION_RESULT_ARTIFACT_FILENAME = "iososv_v0_3_result.json"
PUBLICATION_EXECUTION_ENVELOPE_FILENAME = "iososv_v0_3_execution_envelope.json"
PUBLICATION_SUMMARY_FILENAME = "iososv_v0_3_summary.txt"
PUBLICATION_ARTIFACT_FILENAMES = (
    PUBLICATION_RESULT_ARTIFACT_FILENAME,
    PUBLICATION_EXECUTION_ENVELOPE_FILENAME,
    PUBLICATION_SUMMARY_FILENAME,
)
PUBLICATION_RESULT_ARTIFACT_KEYS = (
    "schema",
    "result_kind",
    "scientific_evaluation_reached",
    "descriptor_evaluation_reached",
    "pass_bundle_sha256",
    "strong_order_hypothesis",
    "formal_hold",
    "mode",
)
PUBLICATION_EXECUTION_ENVELOPE_KEYS = (
    "schema",
    "authority_consumed",
    "current_state",
    "repository_execution_head",
    "branch",
    "python_version",
    "runner_identity",
    "runner_test_identity",
    "schema_contract_identity",
    "descriptor_identity",
    "scientific_result_kind",
    "pass_bundle",
)

FORMAL_HOLD_VALUE = "active"
MODE_VALUE = "Mode_0"
STRONG_ORDER_HYPOTHESIS_VALUE = (
    "STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY"
)

SOURCE_IDENTITY_KEYS = ("source_path", "git_blob", "raw_sha256")
MANIFEST_IDENTITIES_KEYS = ("manifest_external_sha256", "manifest_payload_sha256")
IMPLEMENTATION_IDENTITIES_KEYS = (
    "runner_identity",
    "runner_test_identity",
    "schema_contract_identity",
)
REPOSITORY_EXECUTION_CONTEXT_KEYS = ("head", "branch", "python_version")
CURRENT_STATE_SNAPSHOT_KEYS = (
    "phase",
    "authority_consumed",
    "contact_armed",
    "manifest_contact_attempt_count",
    "manifest_read_success_count",
)
PUBLICATION_PROJECTION_SOURCE_KEYS = (
    "current_state_snapshot",
    "canonical_pass_bundle",
    "publication_recipe_identity",
)
PASS_BUNDLE_KEYS = (
    "schema",
    "fixed_positive",
    "controls",
    "accepted_family",
    "scientific_result_kind",
)
FIXED_POSITIVE_KEYS = ("distinguished",)
CONTROLS_KEYS = (
    "malformed_and_degenerate_controls_correct",
    "identity_controls_correct",
    "nuisance_controls_correct",
    "method_b_full_enumeration",
    "sampling_used",
    "malformed_and_degenerate_control_cases",
    "identity_control_cases",
    "method_b_counts",
    "method_b_required_counts",
    "method_b_unique_vectors_evaluated",
)
MALFORMED_CONTROL_CASE_KEYS = (
    "case",
    "expected_failure_code",
    "observed_failure_code",
    "observed_failure_stage",
    "correct",
)
IDENTITY_CONTROL_CASES_KEYS = (
    "raw_identity_behavior",
    "repeat_determinism",
    "independently_allocated_equal_input",
    "affine_identity_behavior",
    "affine_equivalent_behavior",
    "affine_plus_complement_identity_behavior",
    "affine_plus_complement_behavior",
)
METHOD_B_COUNTS_KEYS = (
    "rotations",
    "affine_transforms",
    "affine_plus_complement_transforms",
)
ACCEPTED_FAMILY_KEYS = (
    "required_count",
    "distinguished_count",
    "results",
)
ACCEPTED_FAMILY_RESULT_KEYS = (
    "family_index",
    "seed_order_position",
    "pair_duplicate_key",
    "distinguished",
)
SCIENTIFIC_COMPLETION_PAYLOAD_KEYS = (
    "scientific_result_kind",
    "bundle_payload_sha256",
    "bundle_payload_byte_length",
    "bundle_schema_identity",
    "accepted_stored_bundle_object_sha256",
    "scientific_pass_count",
    "two_pass_canonical_identity_status",
    "authority_consumed_status",
    "manifest_contact_attempt_count",
    "manifest_read_success_count",
    "implementation_identities",
    "configuration_identity",
    "manifest_identities",
    "execution_identity",
    "scientific_execution_authorization_identity",
    "protocol_identity",
    "completion_validity",
)

SCIENTIFIC_COMPLETION_PAYLOAD_KEYS_WITHOUT_OPTIONAL = tuple(
    key
    for key in SCIENTIFIC_COMPLETION_PAYLOAD_KEYS
    if key != "accepted_stored_bundle_object_sha256"
)

_HEX_64_RE = re.compile(r"^[0-9a-f]{64}$")
_HEX_40_RE = re.compile(r"^[0-9a-f]{40}$")
_HEX_32_RE = re.compile(r"^[0-9a-f]{32}$")


class EvidenceValidationError(ValueError):
    pass


class DuplicateKeyError(EvidenceValidationError):
    pass


class NonCanonicalBytesError(EvidenceValidationError):
    pass


class LogicalRecordIdentityError(EvidenceValidationError):
    pass


class StoredObjectIdentityError(EvidenceValidationError):
    pass


class BundlePayloadIdentityError(EvidenceValidationError):
    pass


class StoredBundleIdentityError(EvidenceValidationError):
    pass


class PublicationArtifactError(EvidenceValidationError):
    pass


class PublicationArtifactHashError(PublicationArtifactError):
    pass


class ResourceAdmissibilityError(EvidenceValidationError):
    failure_code = RESOURCE_LIMIT_EXCEEDED


class ResourceStructureLimitError(ResourceAdmissibilityError):
    def __init__(
        self,
        detail: str,
        failure_code: str = RESOURCE_LIMIT_EXCEEDED,
    ) -> None:
        self.failure_code = failure_code
        super().__init__(detail)


class ResourceStringLimitError(ResourceAdmissibilityError):
    failure_code = STRING_SIZE_LIMIT_EXCEEDED


class ResourceIntegerLimitError(ResourceAdmissibilityError):
    failure_code = INTEGER_MAGNITUDE_LIMIT_EXCEEDED


class PublicationArtifactSizeLimitError(ResourceAdmissibilityError):
    failure_code = ARTIFACT_SIZE_LIMIT_EXCEEDED

    def __init__(
        self,
        detail: str,
        failure_code: str = ARTIFACT_SIZE_LIMIT_EXCEEDED,
    ) -> None:
        self.failure_code = failure_code
        super().__init__(detail)


class PublicationArtifactSetSizeLimitError(ResourceAdmissibilityError):
    failure_code = ARTIFACT_SET_SIZE_LIMIT_EXCEEDED


class RecoveryVerificationBudgetError(ResourceAdmissibilityError):
    failure_code = RECOVERY_VERIFICATION_BUDGET_EXCEEDED


class ResourceAdmissibilityIndeterminateError(ResourceAdmissibilityError):
    failure_code = RESOURCE_ADMISSIBILITY_INDETERMINATE


class ResourcePolicyIdentityMismatchError(ResourceAdmissibilityError):
    failure_code = RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH


class DirectoryDurabilityPolicyIdentityMismatchError(EvidenceValidationError):
    failure_code = POLICY_IDENTITY_MISMATCH


class RecoveryArtifactTypeInvalidError(ResourceAdmissibilityError):
    failure_code = RECOVERY_ARTIFACT_TYPE_INVALID


class RecoveryArtifactReadIndeterminateError(ResourceAdmissibilityError):
    failure_code = RECOVERY_ARTIFACT_READ_INDETERMINATE


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any, *, max_bytes: int | None = None) -> bytes:
    validate_json_domain(value)
    payload = (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
        .encode("utf-8")
        + b"\n"
    )
    _validate_canonical_byte_envelope(payload, max_bytes=max_bytes)
    return payload


def directory_durability_policy_declaration() -> dict[str, Any]:
    declaration = {
        "policy_schema_identity": DIRECTORY_DURABILITY_POLICY_SCHEMA,
        "adapter_identity": DIRECTORY_DURABILITY_ADAPTER_IDENTITY,
        "operation_identity": DIRECTORY_DURABILITY_OPERATION_IDENTITY,
        "supported_windows_profile": {
            "windows_versions": ["Windows 10", "Windows 11"],
            "windows_product_type": "workstation",
            "drive_type": "local fixed volume",
        },
        "supported_filesystem_profile": {
            "filesystem": "NTFS",
            "directory": "ordinary non-reparse directory",
            "material": "pytest temporary-directory material",
        },
        "target_role_declaration": list(DIRECTORY_DURABILITY_TARGET_ROLES),
        "status_taxonomy": list(DIRECTORY_DURABILITY_STATUS_TAXONOMY),
        "failure_mapping_version": DIRECTORY_DURABILITY_FAILURE_MAPPING_VERSION,
        "failure_code_vocabulary": list(DIRECTORY_DURABILITY_FAILURE_CODES),
        "path_normalization_policy": {
            "absolute_path_required": True,
            "windows_extended_length_path_for_win32_calls": True,
            "unc_paths": "unsupported",
            "mapped_or_network_roots": "unsupported",
            "volatile_absolute_roots": "evidence_only_not_policy_material",
        },
        "reparse_point_policy": {
            "directory_symlink": "rejected",
            "junction": "rejected",
            "mount_point": "rejected",
            "unknown_reparse_point": "rejected",
        },
        "validation_profile_identity": (
            DIRECTORY_DURABILITY_VALIDATION_PROFILE_IDENTITY
        ),
    }
    _require_key_order(
        declaration,
        DIRECTORY_DURABILITY_POLICY_DECLARATION_KEYS,
        "directory durability policy",
    )
    return declaration


def directory_durability_policy_sha256() -> str:
    return sha256_hex(canonical_json_bytes(directory_durability_policy_declaration()))


def directory_durability_policy_identity() -> dict[str, str]:
    identity = {
        "policy_schema_identity": DIRECTORY_DURABILITY_POLICY_SCHEMA,
        "policy_sha256": directory_durability_policy_sha256(),
    }
    _require_key_order(
        identity,
        DIRECTORY_DURABILITY_POLICY_IDENTITY_KEYS,
        "directory durability policy identity",
    )
    return identity


def validate_directory_durability_policy_identity(value: Any) -> None:
    try:
        _require_key_order(
            value,
            DIRECTORY_DURABILITY_POLICY_IDENTITY_KEYS,
            "directory durability policy identity",
        )
        _require_constant(
            value["policy_schema_identity"],
            DIRECTORY_DURABILITY_POLICY_SCHEMA,
            "directory durability policy schema",
        )
        _require_hex64(value["policy_sha256"], "directory policy sha256")
        if value["policy_sha256"] != directory_durability_policy_sha256():
            raise DirectoryDurabilityPolicyIdentityMismatchError(
                "directory durability policy identity mismatch"
            )
    except DirectoryDurabilityPolicyIdentityMismatchError:
        raise
    except (EvidenceValidationError, KeyError, TypeError) as exc:
        raise DirectoryDurabilityPolicyIdentityMismatchError(
            "directory durability policy identity mismatch"
        ) from exc


def resource_admissibility_policy_declaration() -> dict[str, Any]:
    declaration = {
        "policy_schema_identity": RESOURCE_ADMISSIBILITY_POLICY_SCHEMA,
        "max_resource_nesting_depth": MAX_RESOURCE_NESTING_DEPTH,
        "max_resource_container_members_per_container": (
            MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER
        ),
        "max_stored_record_object_bytes": MAX_STORED_RECORD_OBJECT_BYTES,
        "max_stored_bundle_object_bytes": MAX_STORED_BUNDLE_OBJECT_BYTES,
        "max_resource_total_node_count": MAX_RESOURCE_TOTAL_NODE_COUNT,
        "max_resource_single_string_ascii_bytes": (
            MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES
        ),
        "max_resource_total_string_ascii_bytes": MAX_RESOURCE_TOTAL_STRING_ASCII_BYTES,
        "max_resource_integer_abs": MAX_RESOURCE_INTEGER_ABS,
        "max_publication_source_bundle_bytes": MAX_PUBLICATION_SOURCE_BUNDLE_BYTES,
        "max_publication_artifact_count": MAX_PUBLICATION_ARTIFACT_COUNT,
        "max_publication_result_artifact_bytes": (
            MAX_PUBLICATION_RESULT_ARTIFACT_BYTES
        ),
        "max_publication_execution_envelope_bytes": (
            MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES
        ),
        "max_publication_summary_bytes": MAX_PUBLICATION_SUMMARY_BYTES,
        "max_publication_artifact_set_bytes": MAX_PUBLICATION_ARTIFACT_SET_BYTES,
        "max_publication_staging_write_bytes": MAX_PUBLICATION_STAGING_WRITE_BYTES,
        "max_publication_recovery_verification_bytes": (
            MAX_PUBLICATION_RECOVERY_VERIFICATION_BYTES
        ),
    }
    _require_key_order(
        declaration,
        RESOURCE_ADMISSIBILITY_POLICY_DECLARATION_KEYS,
        "resource admissibility policy",
    )
    return declaration


def resource_admissibility_policy_sha256() -> str:
    return sha256_hex(canonical_json_bytes(resource_admissibility_policy_declaration()))


def resource_admissibility_policy_identity() -> dict[str, str]:
    identity = {
        "policy_schema_identity": RESOURCE_ADMISSIBILITY_POLICY_SCHEMA,
        "policy_sha256": resource_admissibility_policy_sha256(),
    }
    _require_key_order(
        identity,
        RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_KEYS,
        "resource admissibility policy identity",
    )
    return identity


def validate_resource_admissibility_policy_identity(value: Any) -> None:
    try:
        _require_key_order(
            value,
            RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_KEYS,
            "resource admissibility policy identity",
        )
        _require_constant(
            value["policy_schema_identity"],
            RESOURCE_ADMISSIBILITY_POLICY_SCHEMA,
            "resource admissibility policy schema",
        )
        _require_hex64(value["policy_sha256"], "resource policy sha256")
        if value["policy_sha256"] != resource_admissibility_policy_sha256():
            raise ResourcePolicyIdentityMismatchError(
                "resource admissibility policy identity mismatch"
            )
    except ResourcePolicyIdentityMismatchError:
        raise
    except (EvidenceValidationError, KeyError, TypeError) as exc:
        raise ResourcePolicyIdentityMismatchError(
            "resource admissibility policy identity mismatch"
        ) from exc


def validate_resource_domain(value: Any) -> None:
    state = {"nodes": 0, "string_bytes": 0}
    _validate_resource_value(value, "$", 0, state)


def canonical_json_bytes_bounded(value: Any, max_bytes: int) -> bytes:
    _require_strict_nonnegative_int(max_bytes, "max_bytes")
    try:
        validate_resource_domain(value)
        payload = canonical_json_bytes(value)
    except (MemoryError, OverflowError) as exc:
        raise ResourceAdmissibilityIndeterminateError(
            "resource admissibility became indeterminate"
        ) from exc
    if len(payload) > max_bytes:
        raise ResourceStructureLimitError(
            "canonical payload exceeds byte limit",
            CANONICAL_STRUCTURE_LIMIT_EXCEEDED,
        )
    return payload


def validate_publication_artifact_resource_map(
    artifact_bytes_by_name: Mapping[str, bytes],
) -> int:
    if not isinstance(artifact_bytes_by_name, Mapping):
        raise PublicationArtifactSetSizeLimitError("artifact byte map must be an object")
    if len(artifact_bytes_by_name) != MAX_PUBLICATION_ARTIFACT_COUNT:
        raise PublicationArtifactSetSizeLimitError("publication artifact count mismatch")
    _require_exact_artifact_keys(artifact_bytes_by_name.keys())
    total = 0
    for name in PUBLICATION_ARTIFACT_FILENAMES:
        payload = artifact_bytes_by_name[name]
        if not isinstance(payload, bytes):
            raise PublicationArtifactSizeLimitError("%s payload must be bytes" % name)
        limit = _publication_artifact_byte_limit(name)
        if len(payload) > limit:
            code = ARTIFACT_SIZE_LIMIT_EXCEEDED
            if name == PUBLICATION_SUMMARY_FILENAME:
                code = SUMMARY_SIZE_LIMIT_EXCEEDED
            raise PublicationArtifactSizeLimitError(
                "%s exceeds resource byte limit" % name,
                code,
            )
        total += len(payload)
        if total > MAX_PUBLICATION_ARTIFACT_SET_BYTES:
            raise PublicationArtifactSetSizeLimitError(
                "publication artifact set exceeds byte limit"
            )
    return total


def read_file_bytes_bounded(
    path: str | Path,
    max_bytes: int,
    *,
    over_limit_code: str = ARTIFACT_SIZE_LIMIT_EXCEEDED,
) -> bytes:
    _require_strict_nonnegative_int(max_bytes, "max_bytes")
    target = Path(path)
    try:
        before = os.lstat(target)
    except OSError as exc:
        raise RecoveryArtifactReadIndeterminateError(
            "artifact lstat was indeterminate"
        ) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise RecoveryArtifactTypeInvalidError("artifact is not a regular file")
    try:
        with target.open("rb") as handle:
            after = os.fstat(handle.fileno())
            if not stat.S_ISREG(after.st_mode):
                raise RecoveryArtifactTypeInvalidError(
                    "opened artifact is not a regular file"
                )
            if not os.path.samestat(before, after):
                raise RecoveryArtifactReadIndeterminateError(
                    "artifact identity changed during read admission"
                )
            payload = handle.read(max_bytes + 1)
    except RecoveryArtifactTypeInvalidError:
        raise
    except RecoveryArtifactReadIndeterminateError:
        raise
    except OSError as exc:
        raise RecoveryArtifactReadIndeterminateError(
            "artifact read was indeterminate"
        ) from exc
    if len(payload) > max_bytes:
        raise PublicationArtifactSizeLimitError(
            "artifact exceeds bounded read limit",
            over_limit_code,
        )
    return payload


def load_canonical_json_bytes(
    payload: bytes, *, max_bytes: int | None = None
) -> dict[str, Any]:
    _validate_canonical_byte_envelope(payload, max_bytes=max_bytes)
    text = payload[:-1].decode("utf-8")
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except json.JSONDecodeError as exc:
        raise NonCanonicalBytesError("invalid JSON") from exc
    if not isinstance(value, dict):
        raise NonCanonicalBytesError("canonical evidence root must be an object")
    try:
        expected = canonical_json_bytes(value, max_bytes=max_bytes)
    except EvidenceValidationError as exc:
        raise NonCanonicalBytesError(str(exc)) from exc
    if expected != payload:
        raise NonCanonicalBytesError("bytes are not canonical")
    return value


def validate_json_domain(value: Any, *, _path: str = "$", _depth: int = 0) -> None:
    if _depth > MAX_NESTING_DEPTH:
        raise EvidenceValidationError("maximum nesting depth exceeded at %s" % _path)
    if value is None:
        raise EvidenceValidationError("null is prohibited at %s" % _path)
    if type(value) is bool:
        return
    if type(value) is int:
        return
    if type(value) is float:
        raise EvidenceValidationError("float is prohibited at %s" % _path)
    if isinstance(value, str):
        _require_ascii_printable(value, _path)
        return
    if isinstance(value, list):
        if len(value) > MAX_CONTAINER_MEMBER_COUNT:
            raise EvidenceValidationError("array member count exceeded at %s" % _path)
        for index, item in enumerate(value):
            validate_json_domain(item, _path="%s[%d]" % (_path, index), _depth=_depth + 1)
        return
    if isinstance(value, Mapping):
        if len(value) > MAX_CONTAINER_MEMBER_COUNT:
            raise EvidenceValidationError("object member count exceeded at %s" % _path)
        for key, item in value.items():
            if not isinstance(key, str):
                raise EvidenceValidationError("object key is not a string at %s" % _path)
            _require_ascii_printable(key, "%s.<key>" % _path)
            validate_json_domain(item, _path="%s.%s" % (_path, key), _depth=_depth + 1)
        return
    raise EvidenceValidationError(
        "unsupported JSON-domain value at %s: %s" % (_path, type(value).__name__)
    )


def build_scientific_logical_record(
    *,
    record_kind: str,
    sequence_number: int,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
    predecessor_logical_record_sha256: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "protocol_identity": PROTOCOL_IDENTITY,
        "record_schema_identity": SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        "record_kind": record_kind,
        "sequence_number": sequence_number,
        "execution_identity": execution_identity,
        "scientific_execution_authorization_identity": scientific_execution_authorization_identity,
        "predecessor_logical_record_sha256": predecessor_logical_record_sha256,
        "payload": payload,
    }
    record["logical_record_sha256"] = compute_logical_record_sha256(record)
    return record


def build_publication_logical_record(
    *,
    record_kind: str,
    sequence_number: int,
    execution_identity: str,
    publication_projection_authorization_identity: str,
    publication_chain_identity: str,
    predecessor_logical_record_sha256: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "protocol_identity": PROTOCOL_IDENTITY,
        "record_schema_identity": PUBLICATION_LOGICAL_RECORD_SCHEMA,
        "record_kind": record_kind,
        "sequence_number": sequence_number,
        "execution_identity": execution_identity,
        "publication_projection_authorization_identity": publication_projection_authorization_identity,
        "publication_chain_identity": publication_chain_identity,
        "predecessor_logical_record_sha256": predecessor_logical_record_sha256,
        "payload": payload,
    }
    record["logical_record_sha256"] = compute_logical_record_sha256(record)
    return record


def build_publication_recovery_logical_record(
    *,
    record_kind: str,
    sequence_number: int,
    execution_identity: str,
    publication_recovery_authorization_identity: str,
    publication_recovery_chain_identity: str,
    predecessor_logical_record_sha256: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "protocol_identity": PROTOCOL_IDENTITY,
        "record_schema_identity": PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA,
        "record_kind": record_kind,
        "sequence_number": sequence_number,
        "execution_identity": execution_identity,
        "publication_recovery_authorization_identity": publication_recovery_authorization_identity,
        "publication_recovery_chain_identity": publication_recovery_chain_identity,
        "predecessor_logical_record_sha256": predecessor_logical_record_sha256,
        "payload": payload,
    }
    record["logical_record_sha256"] = compute_logical_record_sha256(record)
    return record


def compute_logical_record_sha256(record: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json_bytes(logical_record_preimage(record)))


def logical_record_preimage(record: Mapping[str, Any]) -> dict[str, Any]:
    keys = _logical_record_keys_for(record)
    preimage_keys = tuple(key for key in keys if key != "logical_record_sha256")
    observed_keys = tuple(record.keys())
    if observed_keys == keys:
        return {key: record[key] for key in preimage_keys}
    if observed_keys == preimage_keys:
        _validate_logical_record_fields(record, keys, require_hash=False)
        return dict(record)
    raise EvidenceValidationError("logical record key order mismatch")


def validate_logical_record(
    record: Mapping[str, Any],
    *,
    expected_schema_identity: str | None = None,
) -> None:
    keys = _logical_record_keys_for(record)
    _require_key_order(record, keys, "logical record")
    _validate_logical_record_fields(record, keys, require_hash=True)
    if expected_schema_identity is not None:
        _require_constant(
            record["record_schema_identity"],
            expected_schema_identity,
            "record_schema_identity",
        )
    expected_hash = compute_logical_record_sha256(record)
    if record["logical_record_sha256"] != expected_hash:
        raise LogicalRecordIdentityError("logical_record_sha256 mismatch")


def build_stored_record_object(
    *,
    logical_record: dict[str, Any],
    writer_identity: str,
    writer_attempt_identity: str,
) -> dict[str, Any]:
    validate_logical_record(logical_record)
    _require_ascii_printable(writer_identity, "writer_identity")
    _require_hex32(writer_attempt_identity, "writer_attempt_identity")
    stored = {
        "storage_schema_identity": STORED_RECORD_OBJECT_SCHEMA,
        "logical_record_sha256": logical_record["logical_record_sha256"],
        "writer_identity": writer_identity,
        "writer_attempt_identity": writer_attempt_identity,
        "logical_record": logical_record,
    }
    stored_hash = compute_stored_record_object_sha256(stored)
    return {
        "storage_schema_identity": STORED_RECORD_OBJECT_SCHEMA,
        "logical_record_sha256": logical_record["logical_record_sha256"],
        "writer_identity": writer_identity,
        "writer_attempt_identity": writer_attempt_identity,
        "stored_object_sha256": stored_hash,
        "logical_record": logical_record,
    }


def stored_record_object_preimage(stored_object: Mapping[str, Any]) -> dict[str, Any]:
    observed_keys = tuple(stored_object.keys())
    if observed_keys == STORED_RECORD_OBJECT_KEYS:
        return {key: stored_object[key] for key in STORED_RECORD_OBJECT_PREIMAGE_KEYS}
    if observed_keys == STORED_RECORD_OBJECT_PREIMAGE_KEYS:
        return dict(stored_object)
    raise EvidenceValidationError("stored record-object key order mismatch")


def compute_stored_record_object_sha256(stored_object: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json_bytes(stored_record_object_preimage(stored_object)))


def validate_stored_record_object(stored_object: Mapping[str, Any]) -> None:
    _require_key_order(stored_object, STORED_RECORD_OBJECT_KEYS, "stored record object")
    _require_constant(
        stored_object["storage_schema_identity"],
        STORED_RECORD_OBJECT_SCHEMA,
        "storage_schema_identity",
    )
    _require_hex64(stored_object["logical_record_sha256"], "logical_record_sha256")
    _require_ascii_printable(stored_object["writer_identity"], "writer_identity")
    _require_hex32(stored_object["writer_attempt_identity"], "writer_attempt_identity")
    validate_logical_record(stored_object["logical_record"])
    if (
        stored_object["logical_record_sha256"]
        != stored_object["logical_record"]["logical_record_sha256"]
    ):
        raise StoredObjectIdentityError("stored logical_record_sha256 mismatch")
    expected_hash = compute_stored_record_object_sha256(stored_object)
    if stored_object["stored_object_sha256"] != expected_hash:
        raise StoredObjectIdentityError("stored_object_sha256 mismatch")
    canonical_json_bytes(stored_object, max_bytes=MAX_STORED_RECORD_OBJECT_BYTES)


def build_bundle_payload(base_payload_without_hash: Mapping[str, Any]) -> dict[str, Any]:
    observed_keys = tuple(base_payload_without_hash.keys())
    expected_keys = tuple(key for key in BUNDLE_PAYLOAD_KEYS if key != "bundle_payload_sha256")
    if observed_keys != expected_keys:
        raise EvidenceValidationError("bundle payload preimage key order mismatch")
    payload = dict(base_payload_without_hash)
    payload["bundle_payload_sha256"] = compute_bundle_payload_sha256(payload)
    validate_bundle_payload(payload)
    return payload


def bundle_payload_preimage(bundle_payload: Mapping[str, Any]) -> dict[str, Any]:
    observed_keys = tuple(bundle_payload.keys())
    preimage_keys = tuple(key for key in BUNDLE_PAYLOAD_KEYS if key != "bundle_payload_sha256")
    if observed_keys == BUNDLE_PAYLOAD_KEYS:
        return {key: bundle_payload[key] for key in preimage_keys}
    if observed_keys == preimage_keys:
        _validate_bundle_payload_fields(bundle_payload, require_hash=False)
        return dict(bundle_payload)
    raise EvidenceValidationError("bundle payload key order mismatch")


def compute_bundle_payload_sha256(bundle_payload: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json_bytes(bundle_payload_preimage(bundle_payload)))


def validate_bundle_payload(bundle_payload: Mapping[str, Any]) -> None:
    _require_key_order(bundle_payload, BUNDLE_PAYLOAD_KEYS, "bundle payload")
    _validate_bundle_payload_fields(bundle_payload, require_hash=True)
    expected_hash = compute_bundle_payload_sha256(bundle_payload)
    if bundle_payload["bundle_payload_sha256"] != expected_hash:
        raise BundlePayloadIdentityError("bundle_payload_sha256 mismatch")


def build_stored_bundle_object(
    *,
    bundle_payload: dict[str, Any],
    writer_identity: str,
    writer_attempt_identity: str,
) -> dict[str, Any]:
    validate_bundle_payload(bundle_payload)
    _require_ascii_printable(writer_identity, "writer_identity")
    _require_hex32(writer_attempt_identity, "writer_attempt_identity")
    bundle_bytes = canonical_json_bytes(bundle_payload)
    stored = {
        "storage_schema_identity": STORED_BUNDLE_OBJECT_SCHEMA,
        "bundle_payload_sha256": bundle_payload["bundle_payload_sha256"],
        "bundle_payload_byte_length": len(bundle_bytes),
        "writer_identity": writer_identity,
        "writer_attempt_identity": writer_attempt_identity,
        "bundle_payload": bundle_payload,
    }
    stored_hash = compute_stored_bundle_object_sha256(stored)
    return {
        "storage_schema_identity": STORED_BUNDLE_OBJECT_SCHEMA,
        "bundle_payload_sha256": bundle_payload["bundle_payload_sha256"],
        "bundle_payload_byte_length": len(bundle_bytes),
        "writer_identity": writer_identity,
        "writer_attempt_identity": writer_attempt_identity,
        "stored_bundle_object_sha256": stored_hash,
        "bundle_payload": bundle_payload,
    }


def stored_bundle_object_preimage(stored_bundle_object: Mapping[str, Any]) -> dict[str, Any]:
    observed_keys = tuple(stored_bundle_object.keys())
    if observed_keys == STORED_BUNDLE_OBJECT_KEYS:
        return {
            key: stored_bundle_object[key]
            for key in STORED_BUNDLE_OBJECT_PREIMAGE_KEYS
        }
    if observed_keys == STORED_BUNDLE_OBJECT_PREIMAGE_KEYS:
        return dict(stored_bundle_object)
    raise EvidenceValidationError("stored bundle-object key order mismatch")


def compute_stored_bundle_object_sha256(
    stored_bundle_object: Mapping[str, Any],
) -> str:
    return sha256_hex(canonical_json_bytes(stored_bundle_object_preimage(stored_bundle_object)))


def validate_stored_bundle_object(stored_bundle_object: Mapping[str, Any]) -> None:
    _require_key_order(stored_bundle_object, STORED_BUNDLE_OBJECT_KEYS, "stored bundle object")
    _require_constant(
        stored_bundle_object["storage_schema_identity"],
        STORED_BUNDLE_OBJECT_SCHEMA,
        "storage_schema_identity",
    )
    _require_hex64(stored_bundle_object["bundle_payload_sha256"], "bundle_payload_sha256")
    _require_strict_nonnegative_int(
        stored_bundle_object["bundle_payload_byte_length"],
        "bundle_payload_byte_length",
    )
    _require_ascii_printable(stored_bundle_object["writer_identity"], "writer_identity")
    _require_hex32(stored_bundle_object["writer_attempt_identity"], "writer_attempt_identity")
    validate_bundle_payload(stored_bundle_object["bundle_payload"])
    if (
        stored_bundle_object["bundle_payload_sha256"]
        != stored_bundle_object["bundle_payload"]["bundle_payload_sha256"]
    ):
        raise StoredBundleIdentityError("stored bundle_payload_sha256 mismatch")
    bundle_bytes = canonical_json_bytes(stored_bundle_object["bundle_payload"])
    if stored_bundle_object["bundle_payload_byte_length"] != len(bundle_bytes):
        raise StoredBundleIdentityError("stored bundle_payload_byte_length mismatch")
    expected_hash = compute_stored_bundle_object_sha256(stored_bundle_object)
    if stored_bundle_object["stored_bundle_object_sha256"] != expected_hash:
        raise StoredBundleIdentityError("stored_bundle_object_sha256 mismatch")
    canonical_json_bytes(stored_bundle_object, max_bytes=MAX_STORED_BUNDLE_OBJECT_BYTES)


def publication_chain_identity(
    *,
    publication_projection_identity: str,
    publication_projection_authorization_identity: str,
) -> str:
    _require_hex64(
        publication_projection_identity, "publication_projection_identity"
    )
    _require_hex64(
        publication_projection_authorization_identity,
        "publication_projection_authorization_identity",
    )
    payload = {
        "publication_projection_identity": publication_projection_identity,
        "publication_projection_authorization_identity": publication_projection_authorization_identity,
    }
    return sha256_hex(canonical_json_bytes(payload))


def _publication_projection_identity(
    *,
    execution_identity: str,
    bundle_payload_sha256: str,
    scientific_completion_logical_record_sha256: str,
    publication_recipe_identity: str,
    publication_utility_identities: Mapping[str, Any],
) -> str:
    _require_hex64(execution_identity, "execution_identity")
    _require_hex64(bundle_payload_sha256, "bundle_payload_sha256")
    _require_hex64(
        scientific_completion_logical_record_sha256,
        "scientific_completion_logical_record_sha256",
    )
    _require_hex64(publication_recipe_identity, "publication_recipe_identity")
    if not isinstance(publication_utility_identities, Mapping):
        raise EvidenceValidationError("publication_utility_identities must be an object")
    validate_json_domain(publication_utility_identities)
    payload = {
        "execution_identity": execution_identity,
        "bundle_payload_sha256": bundle_payload_sha256,
        "scientific_completion_logical_record_sha256": (
            scientific_completion_logical_record_sha256
        ),
        "publication_recipe_identity": publication_recipe_identity,
        "publication_utility_identities": dict(publication_utility_identities),
    }
    _require_key_order(payload, PUBLICATION_PROJECTION_IDENTITY_KEYS, "projection identity")
    return sha256_hex(canonical_json_bytes(payload))


def publication_recovery_chain_identity(
    *,
    original_publication_chain_identity: str,
    publication_recovery_authorization_identity: str,
) -> str:
    _require_hex64(
        original_publication_chain_identity, "original_publication_chain_identity"
    )
    _require_hex64(
        publication_recovery_authorization_identity,
        "publication_recovery_authorization_identity",
    )
    payload = {
        "original_publication_chain_identity": original_publication_chain_identity,
        "publication_recovery_authorization_identity": publication_recovery_authorization_identity,
    }
    return sha256_hex(canonical_json_bytes(payload))


def publication_artifact_byte_map_for_bundle(
    bundle_payload: Mapping[str, Any],
) -> dict[str, bytes]:
    validate_bundle_payload(bundle_payload)
    artifacts = {
        PUBLICATION_RESULT_ARTIFACT_FILENAME: canonical_json_bytes_bounded(
            _publication_result_artifact(bundle_payload),
            MAX_PUBLICATION_RESULT_ARTIFACT_BYTES,
        ),
        PUBLICATION_EXECUTION_ENVELOPE_FILENAME: canonical_json_bytes_bounded(
            _publication_execution_envelope(bundle_payload),
            MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES,
        ),
        PUBLICATION_SUMMARY_FILENAME: _publication_summary_bytes(bundle_payload),
    }
    _require_exact_artifact_keys(artifacts.keys())
    validate_publication_artifact_resource_map(artifacts)
    return artifacts


def publication_artifact_sha256s_for_bundle(
    bundle_payload: Mapping[str, Any],
) -> dict[str, str]:
    return {
        name: sha256_hex(payload)
        for name, payload in publication_artifact_byte_map_for_bundle(
            bundle_payload
        ).items()
    }


def validate_publication_artifact_byte_map(
    artifact_bytes_by_name: Mapping[str, bytes],
    *,
    bundle_payload: Mapping[str, Any],
    expected_artifact_sha256s: Mapping[str, str] | None = None,
) -> dict[str, str]:
    if not isinstance(artifact_bytes_by_name, Mapping):
        raise PublicationArtifactError("artifact byte map must be an object")
    _require_exact_artifact_keys(artifact_bytes_by_name.keys())
    validate_publication_artifact_resource_map(artifact_bytes_by_name)
    if expected_artifact_sha256s is not None:
        _require_exact_artifact_keys(expected_artifact_sha256s.keys())
        for name in PUBLICATION_ARTIFACT_FILENAMES:
            _require_hex64(expected_artifact_sha256s[name], "%s sha256" % name)
    expected = publication_artifact_byte_map_for_bundle(bundle_payload)
    observed_hashes: dict[str, str] = {}
    for name in PUBLICATION_ARTIFACT_FILENAMES:
        payload = artifact_bytes_by_name[name]
        if not isinstance(payload, bytes):
            raise PublicationArtifactError("%s payload must be bytes" % name)
        _validate_publication_artifact_payload_shape(name, payload)
        observed_hash = sha256_hex(payload)
        observed_hashes[name] = observed_hash
        if (
            expected_artifact_sha256s is not None
            and observed_hash != expected_artifact_sha256s[name]
        ):
            raise PublicationArtifactHashError("%s SHA-256 mismatch" % name)
        if payload != expected[name]:
            raise PublicationArtifactError("%s bytes mismatch" % name)
    return observed_hashes


def validate_publication_artifact_sha256s(
    artifact_sha256s: Mapping[str, str],
) -> None:
    _require_exact_artifact_keys(artifact_sha256s.keys())
    for name in PUBLICATION_ARTIFACT_FILENAMES:
        _require_hex64(artifact_sha256s[name], "%s sha256" % name)


def record_authorization_identity(record: Mapping[str, Any]) -> str:
    schema_identity = record["record_schema_identity"]
    if schema_identity == SCIENTIFIC_LOGICAL_RECORD_SCHEMA:
        return record["scientific_execution_authorization_identity"]
    if schema_identity == PUBLICATION_LOGICAL_RECORD_SCHEMA:
        return record["publication_projection_authorization_identity"]
    if schema_identity == PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA:
        return record["publication_recovery_authorization_identity"]
    raise EvidenceValidationError("unknown record_schema_identity")


def record_chain_identity(record: Mapping[str, Any]) -> str | None:
    schema_identity = record["record_schema_identity"]
    if schema_identity == SCIENTIFIC_LOGICAL_RECORD_SCHEMA:
        return None
    if schema_identity == PUBLICATION_LOGICAL_RECORD_SCHEMA:
        return record["publication_chain_identity"]
    if schema_identity == PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA:
        return record["publication_recovery_chain_identity"]
    raise EvidenceValidationError("unknown record_schema_identity")


def validate_scientific_completion_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise EvidenceValidationError("scientific completion must be an object")
    observed_keys = tuple(payload.keys())
    if observed_keys not in (
        SCIENTIFIC_COMPLETION_PAYLOAD_KEYS,
        SCIENTIFIC_COMPLETION_PAYLOAD_KEYS_WITHOUT_OPTIONAL,
    ):
        raise EvidenceValidationError("scientific completion key order mismatch")
    _require_scientific_result_kind(payload["scientific_result_kind"])
    _require_hex64(payload["bundle_payload_sha256"], "bundle_payload_sha256")
    _require_strict_nonnegative_int(
        payload["bundle_payload_byte_length"], "bundle_payload_byte_length"
    )
    _require_constant(
        payload["bundle_schema_identity"],
        IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA,
        "bundle_schema_identity",
    )
    if "accepted_stored_bundle_object_sha256" in payload:
        _require_hex64(
            payload["accepted_stored_bundle_object_sha256"],
            "accepted_stored_bundle_object_sha256",
        )
    _require_strict_int_equal(payload["scientific_pass_count"], 2, "scientific_pass_count")
    _require_constant(
        payload["two_pass_canonical_identity_status"],
        "identical",
        "two_pass_canonical_identity_status",
    )
    _require_constant(
        payload["authority_consumed_status"],
        "AUTHORITY_CONSUMED",
        "authority_consumed_status",
    )
    _require_strict_int_equal(
        payload["manifest_contact_attempt_count"],
        2,
        "manifest_contact_attempt_count",
    )
    _require_strict_int_equal(
        payload["manifest_read_success_count"],
        2,
        "manifest_read_success_count",
    )
    _validate_implementation_identities(payload["implementation_identities"])
    _require_hex64(payload["configuration_identity"], "configuration_identity")
    _validate_manifest_identities(payload["manifest_identities"])
    _require_hex64(payload["execution_identity"], "execution_identity")
    _require_hex64(
        payload["scientific_execution_authorization_identity"],
        "scientific_execution_authorization_identity",
    )
    _require_constant(payload["protocol_identity"], PROTOCOL_IDENTITY, "protocol_identity")
    _require_constant(payload["completion_validity"], "VALID", "completion_validity")
    validate_json_domain(payload)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError("duplicate key: %s" % key)
        result[key] = value
    return result


def _validate_resource_value(
    value: Any,
    path: str,
    depth: int,
    state: dict[str, int],
) -> None:
    if depth > MAX_RESOURCE_NESTING_DEPTH:
        raise ResourceStructureLimitError("maximum resource nesting depth exceeded")
    if value is None:
        raise EvidenceValidationError("null is prohibited at %s" % path)
    if type(value) is bool:
        _count_resource_node(state)
        return
    if type(value) is int:
        if abs(value) > MAX_RESOURCE_INTEGER_ABS:
            raise ResourceIntegerLimitError("integer magnitude exceeds resource limit")
        _count_resource_node(state)
        return
    if type(value) is float:
        raise EvidenceValidationError("float is prohibited at %s" % path)
    if isinstance(value, str):
        _require_ascii_printable(value, path)
        _count_resource_node(state)
        _count_resource_string(value, state)
        return
    if isinstance(value, list):
        if len(value) > MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER:
            raise ResourceStructureLimitError("container member count exceeds limit")
        _count_resource_node(state)
        for index, item in enumerate(value):
            _validate_resource_value(item, "%s[%d]" % (path, index), depth + 1, state)
        return
    if isinstance(value, Mapping):
        if len(value) > MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER:
            raise ResourceStructureLimitError("container member count exceeds limit")
        _count_resource_node(state)
        for key, item in value.items():
            if not isinstance(key, str):
                raise EvidenceValidationError("object key is not a string at %s" % path)
            _require_ascii_printable(key, "%s.<key>" % path)
            _count_resource_string(key, state)
            _validate_resource_value(item, "%s.%s" % (path, key), depth + 1, state)
        return
    raise EvidenceValidationError(
        "unsupported JSON-domain value at %s: %s" % (path, type(value).__name__)
    )


def _count_resource_node(state: dict[str, int]) -> None:
    state["nodes"] += 1
    if state["nodes"] > MAX_RESOURCE_TOTAL_NODE_COUNT:
        raise ResourceStructureLimitError("resource node count exceeds limit")


def _count_resource_string(value: str, state: dict[str, int]) -> None:
    byte_length = len(value.encode("ascii"))
    if byte_length > MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES:
        raise ResourceStringLimitError("single string exceeds resource byte limit")
    state["string_bytes"] += byte_length
    if state["string_bytes"] > MAX_RESOURCE_TOTAL_STRING_ASCII_BYTES:
        raise ResourceStringLimitError("total string bytes exceed resource limit")


def _validate_canonical_byte_envelope(
    payload: bytes, *, max_bytes: int | None = None
) -> None:
    if not isinstance(payload, bytes):
        raise NonCanonicalBytesError("canonical payload must be bytes")
    if max_bytes is not None and len(payload) > max_bytes:
        raise NonCanonicalBytesError("canonical payload exceeds byte limit")
    if payload.startswith(b"\xef\xbb\xbf"):
        raise NonCanonicalBytesError("BOM is prohibited")
    if b"\r" in payload:
        raise NonCanonicalBytesError("CR is prohibited")
    if not payload.endswith(b"\n"):
        raise NonCanonicalBytesError("missing terminal LF")
    if payload.count(b"\n") != 1:
        raise NonCanonicalBytesError("canonical payload must contain exactly one LF")
    try:
        payload[:-1].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise NonCanonicalBytesError("canonical payload is not UTF-8") from exc


def _logical_record_keys_for(record: Mapping[str, Any]) -> tuple[str, ...]:
    if "record_schema_identity" not in record:
        raise EvidenceValidationError("missing record_schema_identity")
    schema_identity = record["record_schema_identity"]
    if schema_identity == SCIENTIFIC_LOGICAL_RECORD_SCHEMA:
        return SCIENTIFIC_LOGICAL_RECORD_KEYS
    if schema_identity == PUBLICATION_LOGICAL_RECORD_SCHEMA:
        return PUBLICATION_LOGICAL_RECORD_KEYS
    if schema_identity == PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA:
        return PUBLICATION_RECOVERY_LOGICAL_RECORD_KEYS
    raise EvidenceValidationError("unknown record_schema_identity")


def _validate_logical_record_fields(
    record: Mapping[str, Any], keys: tuple[str, ...], *, require_hash: bool
) -> None:
    _require_constant(record["protocol_identity"], PROTOCOL_IDENTITY, "protocol_identity")
    schema_identity = record["record_schema_identity"]
    _require_strict_nonnegative_int(record["sequence_number"], "sequence_number")
    _require_hex64(record["execution_identity"], "execution_identity")
    _require_hex64(
        record["predecessor_logical_record_sha256"],
        "predecessor_logical_record_sha256",
    )
    if not isinstance(record["payload"], dict):
        raise EvidenceValidationError("payload must be a dictionary")
    validate_json_domain(record["payload"])
    if schema_identity == SCIENTIFIC_LOGICAL_RECORD_SCHEMA:
        _require_member(record["record_kind"], SCIENTIFIC_RECORD_KINDS, "record_kind")
        _require_hex64(
            record["scientific_execution_authorization_identity"],
            "scientific_execution_authorization_identity",
        )
    elif schema_identity == PUBLICATION_LOGICAL_RECORD_SCHEMA:
        _require_member(record["record_kind"], PUBLICATION_RECORD_KINDS, "record_kind")
        _require_hex64(
            record["publication_projection_authorization_identity"],
            "publication_projection_authorization_identity",
        )
        _require_hex64(record["publication_chain_identity"], "publication_chain_identity")
    elif schema_identity == PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA:
        _require_member(
            record["record_kind"], PUBLICATION_RECOVERY_RECORD_KINDS, "record_kind"
        )
        _require_hex64(
            record["publication_recovery_authorization_identity"],
            "publication_recovery_authorization_identity",
        )
        _require_hex64(
            record["publication_recovery_chain_identity"],
            "publication_recovery_chain_identity",
        )
    else:
        raise EvidenceValidationError("unknown record_schema_identity")
    if require_hash:
        _require_hex64(record["logical_record_sha256"], "logical_record_sha256")
        _require_key_order(record, keys, "logical record")
    validate_json_domain(record)


def _validate_bundle_payload_fields(
    payload: Mapping[str, Any], *, require_hash: bool
) -> None:
    _require_constant(
        payload["bundle_schema_identity"],
        IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA,
        "bundle_schema_identity",
    )
    _require_constant(payload["protocol_identity"], PROTOCOL_IDENTITY, "protocol_identity")
    _require_hex64(payload["execution_identity"], "execution_identity")
    _require_hex64(
        payload["scientific_execution_authorization_identity"],
        "scientific_execution_authorization_identity",
    )
    _require_scientific_result_kind(payload["scientific_result_kind"])
    _require_hex64(payload["pass_bundle_sha256"], "pass_bundle_sha256")
    _require_constant(
        payload["two_pass_canonical_identity_status"],
        "identical",
        "two_pass_canonical_identity_status",
    )
    _require_hex64(payload["configuration_identity"], "configuration_identity")
    _validate_manifest_identities(payload["manifest_identities"])
    _validate_implementation_identities(payload["implementation_identities"])
    _validate_source_identity(payload["descriptor_identity"], "descriptor_identity")
    _validate_repository_execution_context(payload["repository_execution_context"])
    _validate_publication_projection_source(
        payload["publication_projection_source"],
        payload["scientific_result_kind"],
        payload["pass_bundle_sha256"],
    )
    if require_hash:
        _require_hex64(payload["bundle_payload_sha256"], "bundle_payload_sha256")
    validate_json_domain(payload)


def _validate_manifest_identities(value: Mapping[str, Any]) -> None:
    _require_key_order(value, MANIFEST_IDENTITIES_KEYS, "manifest identities")
    _require_hex64(value["manifest_external_sha256"], "manifest_external_sha256")
    _require_hex64(value["manifest_payload_sha256"], "manifest_payload_sha256")


def _validate_implementation_identities(value: Mapping[str, Any]) -> None:
    _require_key_order(value, IMPLEMENTATION_IDENTITIES_KEYS, "implementation identities")
    for key in IMPLEMENTATION_IDENTITIES_KEYS:
        _validate_source_identity(value[key], key)


def _validate_source_identity(value: Mapping[str, Any], label: str) -> None:
    _require_key_order(value, SOURCE_IDENTITY_KEYS, label)
    _require_ascii_printable(value["source_path"], "%s.source_path" % label)
    _require_hex40(value["git_blob"], "%s.git_blob" % label)
    _require_hex64(value["raw_sha256"], "%s.raw_sha256" % label)


def _validate_repository_execution_context(value: Mapping[str, Any]) -> None:
    _require_key_order(
        value, REPOSITORY_EXECUTION_CONTEXT_KEYS, "repository execution context"
    )
    _require_hex40(value["head"], "repository_execution_context.head")
    _require_ascii_printable(value["branch"], "repository_execution_context.branch")
    _require_ascii_printable(
        value["python_version"], "repository_execution_context.python_version"
    )


def _validate_publication_projection_source(
    value: Mapping[str, Any],
    scientific_result_kind: str,
    pass_bundle_sha256: str,
) -> None:
    _require_key_order(
        value, PUBLICATION_PROJECTION_SOURCE_KEYS, "publication projection source"
    )
    _validate_current_state_snapshot(value["current_state_snapshot"])
    _validate_pass_bundle(value["canonical_pass_bundle"], scientific_result_kind)
    computed_pass_bundle_sha256 = sha256_hex(
        canonical_json_bytes(value["canonical_pass_bundle"])
    )
    if computed_pass_bundle_sha256 != pass_bundle_sha256:
        raise BundlePayloadIdentityError("pass_bundle_sha256 mismatch")
    _require_hex64(value["publication_recipe_identity"], "publication_recipe_identity")


def _publication_result_artifact(bundle_payload: Mapping[str, Any]) -> dict[str, Any]:
    result = {
        "schema": PUBLICATION_RESULT_ARTIFACT_SCHEMA,
        "result_kind": bundle_payload["scientific_result_kind"],
        "scientific_evaluation_reached": True,
        "descriptor_evaluation_reached": True,
        "pass_bundle_sha256": bundle_payload["pass_bundle_sha256"],
        "strong_order_hypothesis": STRONG_ORDER_HYPOTHESIS_VALUE,
        "formal_hold": FORMAL_HOLD_VALUE,
        "mode": MODE_VALUE,
    }
    _require_key_order(result, PUBLICATION_RESULT_ARTIFACT_KEYS, "result artifact")
    return result


def _publication_execution_envelope(
    bundle_payload: Mapping[str, Any]
) -> dict[str, Any]:
    repository_context = bundle_payload["repository_execution_context"]
    implementation_identities = bundle_payload["implementation_identities"]
    projection_source = bundle_payload["publication_projection_source"]
    envelope = {
        "schema": PUBLICATION_EXECUTION_ENVELOPE_SCHEMA,
        "authority_consumed": True,
        "current_state": projection_source["current_state_snapshot"],
        "repository_execution_head": repository_context["head"],
        "branch": repository_context["branch"],
        "python_version": repository_context["python_version"],
        "runner_identity": implementation_identities["runner_identity"],
        "runner_test_identity": implementation_identities["runner_test_identity"],
        "schema_contract_identity": implementation_identities[
            "schema_contract_identity"
        ],
        "descriptor_identity": bundle_payload["descriptor_identity"],
        "scientific_result_kind": bundle_payload["scientific_result_kind"],
        "pass_bundle": projection_source["canonical_pass_bundle"],
    }
    _require_key_order(
        envelope, PUBLICATION_EXECUTION_ENVELOPE_KEYS, "execution envelope"
    )
    return envelope


def _publication_summary_bytes(bundle_payload: Mapping[str, Any]) -> bytes:
    summary = (
        "Stage S3B v0.3 synthetic validation\n"
        "result_kind = %s\n"
        "FORMAL_HOLD = active\n"
        "Mode_0 = active\n"
        "STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY\n"
    ) % bundle_payload["scientific_result_kind"]
    payload = summary.encode("ascii")
    if payload.count(b"\n") != 5 or not payload.endswith(b"\n") or b"\r" in payload:
        raise PublicationArtifactError("summary byte envelope is invalid")
    if len(payload) > MAX_PUBLICATION_SUMMARY_BYTES:
        raise PublicationArtifactSizeLimitError(
            "summary exceeds resource byte limit",
            SUMMARY_SIZE_LIMIT_EXCEEDED,
        )
    return payload


def _require_exact_artifact_keys(keys: Any) -> None:
    observed = tuple(keys)
    if observed != PUBLICATION_ARTIFACT_FILENAMES:
        raise PublicationArtifactError("publication artifact inventory mismatch")


def _publication_artifact_byte_limit(name: str) -> int:
    if name == PUBLICATION_RESULT_ARTIFACT_FILENAME:
        return MAX_PUBLICATION_RESULT_ARTIFACT_BYTES
    if name == PUBLICATION_EXECUTION_ENVELOPE_FILENAME:
        return MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES
    if name == PUBLICATION_SUMMARY_FILENAME:
        return MAX_PUBLICATION_SUMMARY_BYTES
    raise PublicationArtifactError("unsupported artifact filename")


def _validate_publication_artifact_payload_shape(name: str, payload: bytes) -> None:
    if name == PUBLICATION_SUMMARY_FILENAME:
        try:
            payload.decode("ascii")
        except UnicodeDecodeError as exc:
            raise PublicationArtifactError("summary is not ASCII") from exc
        if b"\r" in payload or not payload.endswith(b"\n"):
            raise PublicationArtifactError("summary terminal newline mismatch")
        return
    try:
        value = load_canonical_json_bytes(payload)
        if name == PUBLICATION_RESULT_ARTIFACT_FILENAME:
            _require_key_order(
                value, PUBLICATION_RESULT_ARTIFACT_KEYS, "result artifact"
            )
            _require_constant(
                value["schema"], PUBLICATION_RESULT_ARTIFACT_SCHEMA, "result schema"
            )
            _require_bool_true(
                value["scientific_evaluation_reached"],
                "scientific_evaluation_reached",
            )
            _require_bool_true(
                value["descriptor_evaluation_reached"],
                "descriptor_evaluation_reached",
            )
            _require_scientific_result_kind(value["result_kind"])
            _require_hex64(value["pass_bundle_sha256"], "pass_bundle_sha256")
            _require_constant(
                value["strong_order_hypothesis"],
                STRONG_ORDER_HYPOTHESIS_VALUE,
                "strong_order_hypothesis",
            )
            _require_constant(value["formal_hold"], FORMAL_HOLD_VALUE, "formal_hold")
            _require_constant(value["mode"], MODE_VALUE, "mode")
            return
        if name == PUBLICATION_EXECUTION_ENVELOPE_FILENAME:
            _require_key_order(
                value, PUBLICATION_EXECUTION_ENVELOPE_KEYS, "execution envelope"
            )
            _require_constant(
                value["schema"],
                PUBLICATION_EXECUTION_ENVELOPE_SCHEMA,
                "execution envelope schema",
            )
            _require_bool_true(value["authority_consumed"], "authority_consumed")
            _validate_current_state_snapshot(value["current_state"])
            _require_hex40(
                value["repository_execution_head"], "repository_execution_head"
            )
            _require_ascii_printable(value["branch"], "branch")
            _require_ascii_printable(value["python_version"], "python_version")
            _validate_source_identity(value["runner_identity"], "runner_identity")
            _validate_source_identity(
                value["runner_test_identity"], "runner_test_identity"
            )
            _validate_source_identity(
                value["schema_contract_identity"], "schema_contract_identity"
            )
            _validate_source_identity(
                value["descriptor_identity"], "descriptor_identity"
            )
            _require_scientific_result_kind(value["scientific_result_kind"])
            _validate_pass_bundle(value["pass_bundle"], value["scientific_result_kind"])
            return
    except (EvidenceValidationError, KeyError, TypeError) as exc:
        raise PublicationArtifactError("%s payload shape is invalid" % name) from exc
    raise PublicationArtifactError("unsupported artifact filename")


def _validate_current_state_snapshot(value: Mapping[str, Any]) -> None:
    _require_key_order(value, CURRENT_STATE_SNAPSHOT_KEYS, "current state snapshot")
    _require_constant(value["phase"], "SCIENTIFIC_COMPLETE", "current_state_snapshot.phase")
    _require_bool_true(
        value["authority_consumed"], "current_state_snapshot.authority_consumed"
    )
    _require_bool_true(value["contact_armed"], "current_state_snapshot.contact_armed")
    _require_strict_int_equal(
        value["manifest_contact_attempt_count"],
        2,
        "current_state_snapshot.manifest_contact_attempt_count",
    )
    _require_strict_int_equal(
        value["manifest_read_success_count"],
        2,
        "current_state_snapshot.manifest_read_success_count",
    )


def _validate_pass_bundle(value: Mapping[str, Any], scientific_result_kind: str) -> None:
    _require_key_order(value, PASS_BUNDLE_KEYS, "canonical pass bundle")
    _require_constant(value["schema"], PASS_BUNDLE_SCHEMA, "canonical_pass_bundle.schema")
    _require_key_order(value["fixed_positive"], FIXED_POSITIVE_KEYS, "fixed positive")
    _require_bool(value["fixed_positive"]["distinguished"], "fixed_positive.distinguished")
    _validate_controls(value["controls"])
    _validate_accepted_family(value["accepted_family"])
    _require_constant(
        value["scientific_result_kind"],
        scientific_result_kind,
        "canonical_pass_bundle.scientific_result_kind",
    )
    _require_scientific_result_kind(value["scientific_result_kind"])


def _validate_controls(value: Mapping[str, Any]) -> None:
    _require_key_order(value, CONTROLS_KEYS, "controls")
    for key in CONTROLS_KEYS[:5]:
        _require_bool(value[key], "controls.%s" % key)
    if not isinstance(value["malformed_and_degenerate_control_cases"], list):
        raise EvidenceValidationError("malformed control cases must be a list")
    for index, case in enumerate(value["malformed_and_degenerate_control_cases"]):
        _require_key_order(
            case,
            MALFORMED_CONTROL_CASE_KEYS,
            "malformed control case %d" % index,
        )
        for key in MALFORMED_CONTROL_CASE_KEYS[:4]:
            _require_ascii_printable(case[key], "malformed_control_case.%s" % key)
        _require_bool(case["correct"], "malformed_control_case.correct")
    _require_key_order(
        value["identity_control_cases"],
        IDENTITY_CONTROL_CASES_KEYS,
        "identity control cases",
    )
    for key in IDENTITY_CONTROL_CASES_KEYS:
        _require_bool(value["identity_control_cases"][key], "identity_control_cases.%s" % key)
    _validate_method_b_counts(value["method_b_counts"], "method_b_counts")
    _validate_method_b_counts(
        value["method_b_required_counts"], "method_b_required_counts"
    )
    _require_strict_nonnegative_int(
        value["method_b_unique_vectors_evaluated"],
        "method_b_unique_vectors_evaluated",
    )


def _validate_method_b_counts(value: Mapping[str, Any], label: str) -> None:
    _require_key_order(value, METHOD_B_COUNTS_KEYS, label)
    for key in METHOD_B_COUNTS_KEYS:
        _require_strict_nonnegative_int(value[key], "%s.%s" % (label, key))


def _validate_accepted_family(value: Mapping[str, Any]) -> None:
    _require_key_order(value, ACCEPTED_FAMILY_KEYS, "accepted family")
    _require_strict_nonnegative_int(value["required_count"], "accepted_family.required_count")
    _require_strict_nonnegative_int(
        value["distinguished_count"], "accepted_family.distinguished_count"
    )
    if not isinstance(value["results"], list):
        raise EvidenceValidationError("accepted_family.results must be a list")
    for index, result in enumerate(value["results"]):
        _require_key_order(
            result,
            ACCEPTED_FAMILY_RESULT_KEYS,
            "accepted family result %d" % index,
        )
        _require_strict_nonnegative_int(
            result["family_index"], "accepted_family.results.family_index"
        )
        _require_strict_nonnegative_int(
            result["seed_order_position"],
            "accepted_family.results.seed_order_position",
        )
        _require_ascii_printable(
            result["pair_duplicate_key"], "accepted_family.results.pair_duplicate_key"
        )
        _require_bool(result["distinguished"], "accepted_family.results.distinguished")


def _require_key_order(
    value: Mapping[str, Any], expected_keys: tuple[str, ...], label: str
) -> None:
    if not isinstance(value, Mapping):
        raise EvidenceValidationError("%s must be an object" % label)
    observed_keys = tuple(value.keys())
    if observed_keys != expected_keys:
        raise EvidenceValidationError("%s key order mismatch" % label)


def _require_constant(value: Any, expected: str, label: str) -> None:
    if value != expected:
        raise EvidenceValidationError("%s must be %r" % (label, expected))


def _require_member(value: Any, expected: frozenset[str], label: str) -> None:
    if value not in expected:
        raise EvidenceValidationError("%s has unsupported value" % label)


def _require_scientific_result_kind(value: Any) -> None:
    _require_member(value, SCIENTIFIC_RESULT_KINDS, "scientific_result_kind")


def _require_ascii_printable(value: Any, label: str) -> None:
    if not isinstance(value, str):
        raise EvidenceValidationError("%s must be a string" % label)
    for char in value:
        codepoint = ord(char)
        if codepoint < 0x20 or codepoint > 0x7E:
            raise EvidenceValidationError("%s contains non-ASCII/control character" % label)


def _require_strict_nonnegative_int(value: Any, label: str) -> None:
    if type(value) is not int or value < 0:
        raise EvidenceValidationError("%s must be a non-negative strict int" % label)


def _require_strict_int_equal(value: Any, expected: int, label: str) -> None:
    if type(value) is not int or value != expected:
        raise EvidenceValidationError("%s must be strict int %d" % (label, expected))


def _require_bool(value: Any, label: str) -> None:
    if type(value) is not bool:
        raise EvidenceValidationError("%s must be bool" % label)


def _require_bool_true(value: Any, label: str) -> None:
    if value is not True:
        raise EvidenceValidationError("%s must be true" % label)


def _require_hex64(value: Any, label: str) -> None:
    if not isinstance(value, str) or _HEX_64_RE.fullmatch(value) is None:
        raise EvidenceValidationError("%s must be lowercase 64-hex" % label)


def _require_hex40(value: Any, label: str) -> None:
    if not isinstance(value, str) or _HEX_40_RE.fullmatch(value) is None:
        raise EvidenceValidationError("%s must be lowercase 40-hex" % label)


def _require_hex32(value: Any, label: str) -> None:
    if not isinstance(value, str) or _HEX_32_RE.fullmatch(value) is None:
        raise EvidenceValidationError("%s must be lowercase 32-hex" % label)
