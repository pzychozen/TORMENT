from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import ntpath
import os
from pathlib import Path
import stat
import sys
from typing import Any, Callable

import blocker2_r4_ordered_directory_creation_helper_v0_1 as authority_a
import durable_evidence_schema_v0_3 as durable_schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


VERSION = "v0.1"
EVIDENCE_RECORD_SCHEMA = (
    "torment.brainvision.blocker2.r4.corrected_path_creation_evidence_record.v0.1"
)
RECORD_KIND = "R4_CORRECTED_PATH_CREATION_AUTHORITY_B_EVIDENCE_RECORD"

CANONICAL_INPUT_STATUS = "NOT_PREPARED_NOT_PUBLISHED_AUTHORITIES_C_D_INACTIVE"

AUTHORITY_B_ACCEPTED = "CORRECTED_PATH_CREATION_EVIDENCE_ACCEPTED"
AUTHORITY_B_RECORD_INVALID = (
    "CORRECTED_PATH_CREATION_RECORD_INVALID_TERMINAL_FAILURE"
)
AUTHORITY_B_RECORD_UNPUBLISHED = (
    "CORRECTED_PATH_CREATION_COMPLETE_RECORD_UNPUBLISHED_TERMINAL_FAILURE"
)
AUTHORITY_A_PARTIAL = "CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE"

PUBLISH_CONTACT_READY = "AUTHORITY_B_PUBLICATION_CONTACT_READY"
PUBLISH_DURABLE = "AUTHORITY_B_RECORD_DURABLY_PUBLISHED"

GOVERNED_PREFIX = r"C:\TORMENT\brainvision_authoritative_inputs"
GOVERNED_EVIDENCE_RECORD_PATH = authority_a.GOVERNED_EVIDENCE_RECORD_PATH

PROHIBITED_RECORD_FIELDS = frozenset(
    (
        "canonical_input_identity",
        "canonical_input_publication",
        "canonical_input_candidate",
        "record_own_complete_file_byte_count",
        "record_own_complete_file_sha256",
        "stored_record_sha256",
        "whole_record_byte_count",
        "whole_record_sha256",
        "persisted_acceptance_receipt",
    )
)

REQUIRED_RECORD_FIELDS = frozenset(
    (
        "schema",
        "version",
        "record_kind",
        "evidence_body",
        "body_identity",
        "corrected_governance_chain_identities",
        "accepted_invocation_head",
        "commit_free_window_identity_or_declaration",
        "required_existing_root",
        "selected_directory_paths",
        "pre_creation_state_each_component",
        "creation_result_each_component",
        "post_creation_state_each_component",
        "strict_operation_order",
        "filesystem_and_drive_profile_evidence",
        "reparse_point_and_alias_rejection_evidence",
        "timestamps",
        "tool_or_primitive_identities",
        "operator_visible_result",
        "publication_location",
        "publication_durability_result",
        "authority_assertions",
        "canonical_input_status",
    )
)


class R4CanonicalizationError(ValueError):
    pass


class R4RecordConstructionError(ValueError):
    pass


@dataclass(frozen=True)
class R4AuthorityBPublicationResult:
    classification: str
    accepted_for_validation: bool
    detail: str
    raw_record_path: str
    contact_started: bool
    create_new_attempted: bool
    write_attempt_count: int
    byte_count: int | None = None
    intended_sha256: str | None = None
    file_identity: dict[str, Any] | None = None
    parent_directory: str | None = None
    absence_observation: dict[str, Any] | None = None
    parent_observation: dict[str, Any] | None = None
    durability_result: dict[str, Any] | None = None
    failure_code: str | None = None
    handle_closed: bool = False
    exception: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return _strip_none(asdict(self))


@dataclass(frozen=True)
class R4EvidenceValidationResult:
    classification: str
    accepted: bool
    detail: str
    raw_record_path: str
    whole_record_byte_count: int | None = None
    whole_record_sha256: str | None = None
    parsed_record: dict[str, Any] | None = None
    canonical_input_absence_observation: dict[str, Any] | None = None
    failure_code: str | None = None
    exception: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return _strip_none(asdict(self))


@dataclass(frozen=True)
class R4AuthorityBAcceptanceResult:
    classification: str
    accepted: bool
    detail: str
    publication_result: R4AuthorityBPublicationResult
    validation_result: R4EvidenceValidationResult | None = None
    whole_record_byte_count: int | None = None
    whole_record_sha256: str | None = None
    authority_c_active: bool = False
    authority_d_active: bool = False
    authority_e_active: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _strip_none(
            {
                "classification": self.classification,
                "accepted": self.accepted,
                "detail": self.detail,
                "publication_result": self.publication_result.as_dict(),
                "validation_result": (
                    self.validation_result.as_dict()
                    if self.validation_result is not None
                    else None
                ),
                "whole_record_byte_count": self.whole_record_byte_count,
                "whole_record_sha256": self.whole_record_sha256,
                "authority_c_active": self.authority_c_active,
                "authority_d_active": self.authority_d_active,
                "authority_e_active": self.authority_e_active,
            }
        )


def build_path_creation_evidence_record(
    helper_result: Any,
    *,
    corrected_governance_chain_identities: Mapping[str, object],
    accepted_invocation_head: str,
    commit_free_window_declaration: Mapping[str, object],
    authority_assertions: Any,
    path_model: authority_a.PathModel,
    source_identities: Mapping[str, object],
) -> dict[str, Any]:
    _require_helper_ready(helper_result, accepted_invocation_head)
    evidence_body = _plain(getattr(helper_result, "evidence_body"))
    body_identity = _plain(getattr(helper_result, "body_identity"))
    _validate_body_identity(evidence_body, body_identity)
    operations = evidence_body.get("operations")
    if not isinstance(operations, Sequence) or isinstance(operations, (str, bytes)):
        raise R4RecordConstructionError("operations must be a sequence")
    if len(operations) != 3:
        raise R4RecordConstructionError("exactly three operations are required")

    selected_paths = list(path_model.components)
    record = {
        "schema": EVIDENCE_RECORD_SCHEMA,
        "version": VERSION,
        "record_kind": RECORD_KIND,
        "accepted_invocation_head": accepted_invocation_head,
        "authority_assertions": _plain(authority_assertions),
        "body_identity": body_identity,
        "canonical_input_status": CANONICAL_INPUT_STATUS,
        "commit_free_window_identity_or_declaration": _plain(
            commit_free_window_declaration
        ),
        "corrected_governance_chain_identities": _plain(
            corrected_governance_chain_identities
        ),
        "creation_result_each_component": [
            _creation_result(index, item) for index, item in enumerate(operations, start=1)
        ],
        "evidence_body": evidence_body,
        "filesystem_and_drive_profile_evidence": [
            _committed(item).get("filesystem_and_drive_profile", "NOT_OBSERVED")
            for item in operations
        ],
        "operator_visible_result": {
            "authority_a_classification": getattr(helper_result, "classification"),
            "authority_a_classification_kind": getattr(
                helper_result, "classification_kind"
            ),
            "authority_a_terminal": getattr(helper_result, "terminal"),
            "authority_b_record_publication": "PENDING_EXTERNAL_ACCEPTANCE",
            "canonical_input_status": CANONICAL_INPUT_STATUS,
        },
        "path_model": _plain(path_model),
        "post_creation_state_each_component": [
            _post_creation_state(index, item)
            for index, item in enumerate(operations, start=1)
        ],
        "pre_creation_state_each_component": [
            _pre_creation_state(index, item)
            for index, item in enumerate(operations, start=1)
        ],
        "publication_durability_result": {
            "stored_inside_record": False,
            "external_authority_b_acceptance_required": True,
            "directory_durability_policy_identity": (
                durable_schema.directory_durability_policy_identity()
            ),
        },
        "publication_location": {
            "raw_record_path": path_model.evidence_record_path,
            "path_role": "R4_AUTHORITY_B_EVIDENCE_RECORD",
            "create_new_only": True,
        },
        "reparse_point_and_alias_rejection_evidence": [
            {
                "ordinal": index,
                "parent_pre_reparse_status": _committed(item).get(
                    "parent_pre_reparse_status", "NOT_OBSERVED"
                ),
                "target_reparse_status": _committed(item).get(
                    "reparse_status", "NOT_OBSERVED"
                ),
            }
            for index, item in enumerate(operations, start=1)
        ],
        "required_existing_root": path_model.required_root,
        "selected_directory_paths": selected_paths,
        "source_identities": _plain(source_identities),
        "strict_operation_order": {
            "ordinals": [
                _committed(item).get("ordinal") for item in operations
            ],
            "expected_ordinals": [1, 2, 3],
            "mutation_succeeded_count": getattr(
                helper_result, "mutation_succeeded_count"
            ),
        },
        "timestamps": [
            {
                "ordinal": index,
                "operation_timestamp_utc": _committed(item).get(
                    "operation_timestamp_utc", "NOT_OBSERVED"
                ),
                "operation_monotonic_ns": _committed(item).get(
                    "operation_monotonic_ns", "NOT_OBSERVED"
                ),
            }
            for index, item in enumerate(operations, start=1)
        ],
        "tool_or_primitive_identities": evidence_body.get(
            "execution_seams", "NOT_OBSERVED"
        ),
    }
    _validate_record_shape(record, path_model, accepted_invocation_head)
    return record


def canonical_record_bytes(record: Mapping[str, object]) -> bytes:
    _validate_json_value(record, "$")
    try:
        return json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise R4CanonicalizationError("record is not canonicalizable") from exc


def load_canonical_record_bytes(payload: bytes) -> dict[str, Any]:
    if not isinstance(payload, bytes):
        raise R4CanonicalizationError("payload must be bytes")
    try:
        text = payload.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, R4CanonicalizationError) as exc:
        raise R4CanonicalizationError("invalid canonical JSON bytes") from exc
    if not isinstance(value, dict):
        raise R4CanonicalizationError("canonical record root must be an object")
    if canonical_record_bytes(value) != payload:
        raise R4CanonicalizationError("bytes are not canonical")
    return value


def publish_record_create_new(
    *,
    raw_record_path: str,
    canonical_bytes: bytes,
    durability_adapter: Any = None,
    native_adapter: Any = None,
    expected_raw_record_path: str = GOVERNED_EVIDENCE_RECORD_PATH,
    allow_test_path_model: bool = False,
    file_opener: Callable[[str, str], Any] | None = None,
    fsync_callable: Callable[[int], None] = os.fsync,
) -> R4AuthorityBPublicationResult:
    if not isinstance(canonical_bytes, bytes):
        return _publication_failure(
            AUTHORITY_B_RECORD_UNPUBLISHED,
            "canonical bytes must be bytes",
            raw_record_path,
            contact_started=False,
            create_new_attempted=False,
            failure_code="CANONICAL_BYTES_INVALID",
        )
    path_failure = _path_admission_failure(
        raw_record_path,
        expected_raw_record_path=expected_raw_record_path,
        allow_test_path_model=allow_test_path_model,
    )
    if path_failure is not None:
        return _publication_failure(
            AUTHORITY_B_RECORD_UNPUBLISHED,
            path_failure,
            raw_record_path,
            contact_started=False,
            create_new_attempted=False,
            failure_code="RECORD_PATH_REJECTED",
        )
    adapter = native_adapter or authority_a.Win32DirectoryAdapter()
    parent_path = _parent_path_text(raw_record_path)
    parent_observation: dict[str, Any] | None = None
    parent_handle = None
    try:
        parent_open = adapter.open_directory(parent_path)
        if not parent_open.opened or parent_open.handle is None:
            return _publication_failure(
                AUTHORITY_B_RECORD_UNPUBLISHED,
                "record parent directory is not openable",
                raw_record_path,
                parent_directory=parent_path,
                contact_started=False,
                create_new_attempted=False,
                parent_observation=_plain(parent_open),
                failure_code="RECORD_PARENT_INVALID",
            )
        parent_handle = parent_open.handle
        parent_observation = _plain(parent_handle.evidence)
        parent_failure = _ordinary_directory_failure(parent_handle.evidence)
        if parent_failure is not None:
            return _publication_failure(
                AUTHORITY_B_RECORD_UNPUBLISHED,
                parent_failure,
                raw_record_path,
                parent_directory=parent_path,
                contact_started=False,
                create_new_attempted=False,
                parent_observation=parent_observation,
                failure_code="RECORD_PARENT_INVALID",
            )
    finally:
        _close_observed_handle(parent_handle)

    try:
        absence = adapter.check_absent(raw_record_path, allow_missing_ancestor=False)
    except Exception as exc:
        return _publication_failure(
            AUTHORITY_B_RECORD_UNPUBLISHED,
            "record target absence observation failed",
            raw_record_path,
            parent_directory=parent_path,
            contact_started=False,
            create_new_attempted=False,
            parent_observation=parent_observation,
            failure_code="RECORD_ABSENCE_INDETERMINATE",
            exception=_exception_dict(exc),
        )
    absence_payload = _plain(absence)
    if not getattr(absence, "positively_absent", False):
        classification = AUTHORITY_B_RECORD_INVALID
        failure_code = "RECORD_TARGET_PRE_EXISTS"
        detail = "record target already exists"
        if absence_payload.get("pre_existing_kind") is None:
            classification = AUTHORITY_B_RECORD_UNPUBLISHED
            failure_code = "RECORD_ABSENCE_NOT_POSITIVE"
            detail = "record target absence was not positive"
        return _publication_failure(
            classification,
            detail,
            raw_record_path,
            parent_directory=parent_path,
            contact_started=False,
            create_new_attempted=False,
            parent_observation=parent_observation,
            absence_observation=absence_payload,
            failure_code=failure_code,
        )

    handle = None
    contact_started = True
    create_new_attempted = True
    handle_closed = False
    file_identity: dict[str, Any] | None = None
    try:
        handle = _open_create_new(raw_record_path, file_opener)
        written = handle.write(canonical_bytes)
        if written is not None and int(written) != len(canonical_bytes):
            return _publication_failure(
                AUTHORITY_B_RECORD_INVALID,
                "short write during record publication",
                raw_record_path,
                parent_directory=parent_path,
                contact_started=contact_started,
                create_new_attempted=create_new_attempted,
                absence_observation=absence_payload,
                parent_observation=parent_observation,
                failure_code="RECORD_SHORT_WRITE",
            )
        handle.flush()
        fsync_callable(handle.fileno())
        file_identity = _file_identity_from_fd(handle.fileno())
    except FileExistsError as exc:
        return _publication_failure(
            AUTHORITY_B_RECORD_INVALID,
            "exclusive create-new collision",
            raw_record_path,
            parent_directory=parent_path,
            contact_started=contact_started,
            create_new_attempted=create_new_attempted,
            absence_observation=absence_payload,
            parent_observation=parent_observation,
            failure_code="RECORD_CREATE_NEW_COLLISION",
            exception=_exception_dict(exc),
        )
    except Exception as exc:
        return _publication_failure(
            AUTHORITY_B_RECORD_INVALID,
            "record publication write path failed",
            raw_record_path,
            parent_directory=parent_path,
            contact_started=contact_started,
            create_new_attempted=create_new_attempted,
            absence_observation=absence_payload,
            parent_observation=parent_observation,
            failure_code="RECORD_WRITE_PATH_FAILED",
            exception=_exception_dict(exc),
        )
    finally:
        if handle is not None:
            try:
                handle.close()
                handle_closed = True
            except Exception:
                handle_closed = False

    if not handle_closed:
        return _publication_failure(
            AUTHORITY_B_RECORD_INVALID,
            "record publication handle close failed",
            raw_record_path,
            parent_directory=parent_path,
            contact_started=contact_started,
            create_new_attempted=create_new_attempted,
            absence_observation=absence_payload,
            parent_observation=parent_observation,
            failure_code="RECORD_CLOSE_FAILED",
            handle_closed=False,
        )

    durability = _sync_parent_directory(
        durability_adapter,
        parent_path,
    )
    durability_payload = _plain(durability)
    if not _durability_confirmed(durability):
        return _publication_failure(
            AUTHORITY_B_RECORD_INVALID,
            "record parent directory durability was not confirmed",
            raw_record_path,
            parent_directory=parent_path,
            contact_started=contact_started,
            create_new_attempted=create_new_attempted,
            absence_observation=absence_payload,
            parent_observation=parent_observation,
            durability_result=durability_payload,
            file_identity=file_identity,
            byte_count=len(canonical_bytes),
            intended_sha256=hashlib.sha256(canonical_bytes).hexdigest(),
            failure_code="RECORD_DIRECTORY_DURABILITY_UNCONFIRMED",
            handle_closed=True,
        )

    return R4AuthorityBPublicationResult(
        classification=PUBLISH_DURABLE,
        accepted_for_validation=True,
        detail="record create-new write and parent directory durability confirmed",
        raw_record_path=raw_record_path,
        parent_directory=parent_path,
        contact_started=contact_started,
        create_new_attempted=create_new_attempted,
        write_attempt_count=1,
        byte_count=len(canonical_bytes),
        intended_sha256=hashlib.sha256(canonical_bytes).hexdigest(),
        file_identity=file_identity,
        absence_observation=absence_payload,
        parent_observation=parent_observation,
        durability_result=durability_payload,
        handle_closed=True,
    )


def validate_published_record(
    *,
    raw_record_path: str,
    expected_canonical_bytes: bytes,
    expected_helper_body_identity: Mapping[str, object],
    expected_accepted_invocation_head: str,
    native_adapter: Any = None,
    path_model: authority_a.PathModel = authority_a.GOVERNED_PATH_MODEL,
    expected_raw_record_path: str = GOVERNED_EVIDENCE_RECORD_PATH,
    allow_test_path_model: bool = False,
    read_bytes_function: Callable[[str], bytes] | None = None,
) -> R4EvidenceValidationResult:
    path_failure = _path_admission_failure(
        raw_record_path,
        expected_raw_record_path=expected_raw_record_path,
        allow_test_path_model=allow_test_path_model,
    )
    if path_failure is not None:
        return _validation_failure(
            "record path rejected",
            raw_record_path,
            "RECORD_PATH_REJECTED",
        )
    try:
        payload = (
            read_bytes_function(raw_record_path)
            if read_bytes_function is not None
            else _read_stored_bytes(raw_record_path)
        )
    except Exception as exc:
        return _validation_failure(
            "record reread failed",
            raw_record_path,
            "RECORD_REREAD_FAILED",
            exception=_exception_dict(exc),
        )
    if payload != expected_canonical_bytes:
        return _validation_failure(
            "record reread bytes differ from intended canonical bytes",
            raw_record_path,
            "RECORD_STORED_BYTE_MISMATCH",
        )
    try:
        record = load_canonical_record_bytes(payload)
        _validate_record_shape(record, path_model, expected_accepted_invocation_head)
        _validate_body_identity(record["evidence_body"], expected_helper_body_identity)
        if dict(record["body_identity"]) != dict(expected_helper_body_identity):
            raise R4RecordConstructionError("body_identity mismatch")
    except (R4CanonicalizationError, R4RecordConstructionError) as exc:
        return _validation_failure(
            str(exc),
            raw_record_path,
            "RECORD_VALIDATION_FAILED",
        )
    adapter = native_adapter or authority_a.Win32DirectoryAdapter()
    try:
        canonical_input_absence = adapter.check_absent(
            path_model.canonical_input_path,
            allow_missing_ancestor=True,
        )
    except Exception as exc:
        return _validation_failure(
            "canonical-input absence observation failed",
            raw_record_path,
            "CANONICAL_INPUT_ABSENCE_INDETERMINATE",
            parsed_record=record,
            exception=_exception_dict(exc),
        )
    canonical_input_payload = _plain(canonical_input_absence)
    if not getattr(canonical_input_absence, "positively_absent", False):
        return _validation_failure(
            "canonical-input path is not positively absent",
            raw_record_path,
            "CANONICAL_INPUT_PATH_PRESENT",
            parsed_record=record,
            canonical_input_absence_observation=canonical_input_payload,
        )
    whole_hash = hashlib.sha256(payload).hexdigest()
    return R4EvidenceValidationResult(
        classification=AUTHORITY_B_ACCEPTED,
        accepted=True,
        detail="record reread, validation, and external identity completed",
        raw_record_path=raw_record_path,
        whole_record_byte_count=len(payload),
        whole_record_sha256=whole_hash,
        parsed_record=record,
        canonical_input_absence_observation=canonical_input_payload,
    )


def accept_authority_b_evidence(
    *,
    publication_result: R4AuthorityBPublicationResult,
    raw_record_path: str,
    expected_canonical_bytes: bytes,
    expected_helper_body_identity: Mapping[str, object],
    expected_accepted_invocation_head: str,
    native_adapter: Any = None,
    path_model: authority_a.PathModel = authority_a.GOVERNED_PATH_MODEL,
    expected_raw_record_path: str = GOVERNED_EVIDENCE_RECORD_PATH,
    allow_test_path_model: bool = False,
    read_bytes_function: Callable[[str], bytes] | None = None,
) -> R4AuthorityBAcceptanceResult:
    if not publication_result.accepted_for_validation:
        return R4AuthorityBAcceptanceResult(
            classification=publication_result.classification,
            accepted=False,
            detail=publication_result.detail,
            publication_result=publication_result,
        )
    validation = validate_published_record(
        raw_record_path=raw_record_path,
        expected_canonical_bytes=expected_canonical_bytes,
        expected_helper_body_identity=expected_helper_body_identity,
        expected_accepted_invocation_head=expected_accepted_invocation_head,
        native_adapter=native_adapter,
        path_model=path_model,
        expected_raw_record_path=expected_raw_record_path,
        allow_test_path_model=allow_test_path_model,
        read_bytes_function=read_bytes_function,
    )
    return R4AuthorityBAcceptanceResult(
        classification=validation.classification,
        accepted=validation.accepted,
        detail=validation.detail,
        publication_result=publication_result,
        validation_result=validation,
        whole_record_byte_count=validation.whole_record_byte_count,
        whole_record_sha256=validation.whole_record_sha256,
    )


def _require_helper_ready(helper_result: Any, accepted_invocation_head: str) -> None:
    required = authority_a.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION
    if getattr(helper_result, "classification", None) != required:
        raise R4RecordConstructionError("Authority-A helper did not reach publication state")
    if getattr(helper_result, "mutation_succeeded_count", None) != 3:
        raise R4RecordConstructionError("Authority-A mutation count must be exactly three")
    if getattr(helper_result, "opportunity_consumed", None) is not True:
        raise R4RecordConstructionError("Authority-A opportunity must be consumed")
    if getattr(helper_result, "sequence_terminal", None) is not False:
        raise R4RecordConstructionError("Authority-A sequence must remain non-terminal")
    evidence_body = getattr(helper_result, "evidence_body", None)
    if not isinstance(evidence_body, Mapping):
        raise R4RecordConstructionError("Authority-A evidence body is invalid")
    if evidence_body.get("accepted_invocation_head") != accepted_invocation_head:
        raise R4RecordConstructionError("accepted invocation HEAD mismatch")


def _validate_record_shape(
    record: Mapping[str, Any],
    path_model: authority_a.PathModel,
    accepted_invocation_head: str,
) -> None:
    missing = REQUIRED_RECORD_FIELDS.difference(record.keys())
    if missing:
        raise R4RecordConstructionError("record missing required field: %s" % sorted(missing)[0])
    for key in PROHIBITED_RECORD_FIELDS:
        if key in record:
            raise R4RecordConstructionError("prohibited record field present: %s" % key)
    if record["schema"] != EVIDENCE_RECORD_SCHEMA:
        raise R4RecordConstructionError("schema mismatch")
    if record["version"] != VERSION:
        raise R4RecordConstructionError("version mismatch")
    if record["record_kind"] != RECORD_KIND:
        raise R4RecordConstructionError("record_kind mismatch")
    if record["accepted_invocation_head"] != accepted_invocation_head:
        raise R4RecordConstructionError("accepted invocation HEAD mismatch")
    if record["required_existing_root"] != path_model.required_root:
        raise R4RecordConstructionError("required root mismatch")
    if tuple(record["selected_directory_paths"]) != tuple(path_model.components):
        raise R4RecordConstructionError("selected directory path mismatch")
    if record["publication_location"]["raw_record_path"] != path_model.evidence_record_path:
        raise R4RecordConstructionError("publication path mismatch")
    if record["canonical_input_status"] != CANONICAL_INPUT_STATUS:
        raise R4RecordConstructionError("canonical-input status mismatch")
    evidence_body = record["evidence_body"]
    if not isinstance(evidence_body, Mapping):
        raise R4RecordConstructionError("evidence body must be an object")
    aggregate = evidence_body.get("aggregate")
    if not isinstance(aggregate, Mapping):
        raise R4RecordConstructionError("evidence aggregate must be an object")
    if aggregate.get("mutation_succeeded_count") != 3:
        raise R4RecordConstructionError("mutation count mismatch")
    if aggregate.get("opportunity_consumed") is not True:
        raise R4RecordConstructionError("opportunity accounting mismatch")
    if aggregate.get("sequence_terminal") is not False:
        raise R4RecordConstructionError("sequence terminal mismatch")
    if record["strict_operation_order"]["ordinals"] != [1, 2, 3]:
        raise R4RecordConstructionError("operation order mismatch")
    _validate_body_identity(evidence_body, record["body_identity"])


def _validate_body_identity(
    evidence_body: Mapping[str, Any],
    body_identity: Mapping[str, Any],
) -> None:
    expected = authority_a.body_identity_for_evidence_body(dict(evidence_body))
    if body_identity.get("body_byte_count") != expected["body_byte_count"]:
        raise R4RecordConstructionError("body byte count mismatch")
    if body_identity.get("body_sha256") != expected["body_sha256"]:
        raise R4RecordConstructionError("body sha256 mismatch")
    if body_identity.get("whole_record_identity_stored_inside_record") is not False:
        raise R4RecordConstructionError("body identity scope mismatch")


def _pre_creation_state(index: int, operation: Any) -> dict[str, Any]:
    committed = _committed(operation)
    return {
        "ordinal": index,
        "exact_absolute_path": committed.get("exact_absolute_path"),
        "immediate_parent_path": committed.get("immediate_parent_path"),
        "target_absence_before": committed.get("target_absence_before"),
        "later_component_absence_pre": committed.get("later_component_absence_pre"),
        "repository_pre_state": committed.get("repository_pre_state"),
    }


def _creation_result(index: int, operation: Any) -> dict[str, Any]:
    committed = _committed(operation)
    derived = _derived(operation)
    return {
        "ordinal": index,
        "creation_call": derived.get("creation_call"),
        "operator_process_result": committed.get("operator_process_result"),
        "target_presence_after": committed.get("target_presence_after"),
    }


def _post_creation_state(index: int, operation: Any) -> dict[str, Any]:
    committed = _committed(operation)
    return {
        "ordinal": index,
        "directory_type": committed.get("directory_type"),
        "reparse_status": committed.get("reparse_status"),
        "volume_identity": committed.get("volume_identity"),
        "directory_file_identity": committed.get("directory_file_identity"),
        "post_create_observed_identity": committed.get("post_create_observed_identity"),
        "parent_post_identity": committed.get("parent_post_identity"),
        "later_component_absence_post": committed.get("later_component_absence_post"),
    }


def _committed(operation: Any) -> Mapping[str, Any]:
    if not isinstance(operation, Mapping):
        raise R4RecordConstructionError("operation must be an object")
    value = operation.get("committed_required")
    if not isinstance(value, Mapping):
        raise R4RecordConstructionError("operation committed payload must be an object")
    return value


def _derived(operation: Any) -> Mapping[str, Any]:
    if not isinstance(operation, Mapping):
        raise R4RecordConstructionError("operation must be an object")
    value = operation.get("derived_implementation")
    if not isinstance(value, Mapping):
        return {}
    return value


def _path_admission_failure(
    raw_record_path: str,
    *,
    expected_raw_record_path: str,
    allow_test_path_model: bool,
) -> str | None:
    if not isinstance(raw_record_path, str):
        return "record path must be a string"
    if raw_record_path != expected_raw_record_path:
        return "record path does not match expected evidence path"
    if allow_test_path_model and _is_governed_path(raw_record_path):
        return "test path model targets governed path"
    if not allow_test_path_model and raw_record_path != GOVERNED_EVIDENCE_RECORD_PATH:
        return "authoritative record path is not governed evidence path"
    return None


def _is_governed_path(raw_path: str) -> bool:
    return raw_path.casefold().startswith(GOVERNED_PREFIX.casefold())


def _parent_path_text(raw_path: str) -> str:
    if "\\" in raw_path or ntpath.splitdrive(raw_path)[0]:
        return ntpath.dirname(raw_path)
    return str(Path(raw_path).parent)


def _ordinary_directory_failure(evidence: Any) -> str | None:
    if getattr(evidence, "is_directory", True) is not True:
        return "record parent is not a directory"
    if getattr(evidence, "is_reparse_point", False):
        return "record parent is a reparse point"
    profile = getattr(evidence, "volume_profile", None)
    identity = getattr(evidence, "identity", None)
    if profile is not None and getattr(profile, "drive_type", None) != 3:
        return "record parent is not on a local fixed drive"
    if profile is not None and str(getattr(profile, "filesystem_name", "")).upper() != "NTFS":
        return "record parent filesystem is not NTFS"
    if (
        profile is not None
        and identity is not None
        and getattr(profile, "volume_serial_number", None)
        != getattr(identity, "volume_serial_number", None)
    ):
        return "record parent volume identity mismatch"
    return None


def _open_create_new(raw_record_path: str, file_opener: Callable[[str, str], Any] | None):
    if file_opener is not None:
        return file_opener(raw_record_path, "xb")
    return open(raw_record_path, "xb")


def _file_identity_from_fd(fd: int) -> dict[str, Any]:
    observed = os.fstat(fd)
    return {
        "st_dev": int(observed.st_dev),
        "st_ino": int(observed.st_ino),
        "st_size": int(observed.st_size),
        "mode_is_regular_file": stat.S_ISREG(observed.st_mode),
    }


def _sync_parent_directory(
    durability_adapter: Any,
    parent_path: str,
) -> windows_adapter.DirectoryDurabilityResult:
    adapter = durability_adapter
    if adapter is None:
        if sys.platform == "win32":
            adapter = windows_adapter.Win32DirectoryDurabilityAdapter()
        else:
            adapter = windows_adapter.FailClosedWindowsDurabilityAdapter()
    context = windows_adapter.DirectoryDurabilityContext(
        target_role=durable_schema.ARTIFACT_PARENT_DIRECTORY
    )
    try:
        return adapter.sync_directory_entry(parent_path, context=context)
    except Exception as exc:
        return windows_adapter.DirectoryDurabilityResult(
            status=durable_schema.DIRECTORY_DURABILITY_INDETERMINATE,
            detail="directory durability adapter exception: %s" % type(exc).__name__,
            failure_code=durable_schema.UNEXPECTED_EXCEPTION,
            adapter_policy_identity=durable_schema.directory_durability_policy_identity(),
            target_role=durable_schema.ARTIFACT_PARENT_DIRECTORY,
        )


def _durability_confirmed(result: windows_adapter.DirectoryDurabilityResult) -> bool:
    if result.status != durable_schema.DIRECTORY_DURABILITY_CONFIRMED:
        return False
    if result.failure_code is not None:
        return False
    try:
        durable_schema.validate_directory_durability_policy_identity(
            result.adapter_policy_identity
        )
    except durable_schema.EvidenceValidationError:
        return False
    return (
        dict(result.adapter_policy_identity)
        == durable_schema.directory_durability_policy_identity()
    )


def _read_stored_bytes(raw_record_path: str) -> bytes:
    with open(raw_record_path, "rb") as handle:
        return handle.read()


def _publication_failure(
    classification: str,
    detail: str,
    raw_record_path: str,
    *,
    contact_started: bool,
    create_new_attempted: bool,
    failure_code: str,
    write_attempt_count: int = 0,
    byte_count: int | None = None,
    intended_sha256: str | None = None,
    file_identity: dict[str, Any] | None = None,
    parent_directory: str | None = None,
    absence_observation: dict[str, Any] | None = None,
    parent_observation: dict[str, Any] | None = None,
    durability_result: dict[str, Any] | None = None,
    handle_closed: bool = False,
    exception: dict[str, Any] | None = None,
) -> R4AuthorityBPublicationResult:
    return R4AuthorityBPublicationResult(
        classification=classification,
        accepted_for_validation=False,
        detail=detail,
        raw_record_path=raw_record_path,
        parent_directory=parent_directory,
        contact_started=contact_started,
        create_new_attempted=create_new_attempted,
        write_attempt_count=write_attempt_count,
        byte_count=byte_count,
        intended_sha256=intended_sha256,
        file_identity=file_identity,
        absence_observation=absence_observation,
        parent_observation=parent_observation,
        durability_result=durability_result,
        failure_code=failure_code,
        handle_closed=handle_closed,
        exception=exception,
    )


def _validation_failure(
    detail: str,
    raw_record_path: str,
    failure_code: str,
    *,
    parsed_record: dict[str, Any] | None = None,
    canonical_input_absence_observation: dict[str, Any] | None = None,
    exception: dict[str, Any] | None = None,
) -> R4EvidenceValidationResult:
    return R4EvidenceValidationResult(
        classification=AUTHORITY_B_RECORD_INVALID,
        accepted=False,
        detail=detail,
        raw_record_path=raw_record_path,
        parsed_record=parsed_record,
        canonical_input_absence_observation=canonical_input_absence_observation,
        failure_code=failure_code,
        exception=exception,
    )


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise R4CanonicalizationError("duplicate JSON key rejected")
        result[key] = value
    return result


def _validate_json_value(value: Any, path: str) -> None:
    if value is None:
        return
    if type(value) is bool:
        return
    if type(value) is int:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise R4CanonicalizationError("non-finite number at %s" % path)
        return
    if isinstance(value, str):
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_json_value(item, "%s[%d]" % (path, index))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise R4CanonicalizationError("non-string object key at %s" % path)
            _validate_json_value(item, "%s.%s" % (path, key))
        return
    raise R4CanonicalizationError("unsupported value at %s" % path)


def _plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _strip_none(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_none(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_strip_none(item) for item in value]
    return value


def _close_observed_handle(handle: Any) -> None:
    if handle is not None and hasattr(handle, "close"):
        handle.close()


def _exception_dict(exc: BaseException) -> dict[str, Any]:
    return {
        "exception_type": type(exc).__name__,
        "message": str(exc)[:240],
    }


__all__ = [
    "AUTHORITY_A_PARTIAL",
    "AUTHORITY_B_ACCEPTED",
    "AUTHORITY_B_RECORD_INVALID",
    "AUTHORITY_B_RECORD_UNPUBLISHED",
    "CANONICAL_INPUT_STATUS",
    "EVIDENCE_RECORD_SCHEMA",
    "GOVERNED_EVIDENCE_RECORD_PATH",
    "R4AuthorityBAcceptanceResult",
    "R4AuthorityBPublicationResult",
    "R4CanonicalizationError",
    "R4EvidenceValidationResult",
    "R4RecordConstructionError",
    "accept_authority_b_evidence",
    "build_path_creation_evidence_record",
    "canonical_record_bytes",
    "load_canonical_record_bytes",
    "publish_record_create_new",
    "validate_published_record",
]
