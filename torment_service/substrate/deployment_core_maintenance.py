"""Dedicated B5-A2 maintenance transitions for one contained native core.

The functions here are administration-only.  They use the existing core
metadata and CUTOVER maintenance evidence; they do not widen ordinary STAGING
writers or construct a public native capability.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from .connection import open_existing_native_core_connection
from .deployment_types import (
    AdmissionCompletionWitness,
    CompletionWitness,
    CoreDeploymentWitness,
    DeploymentState,
    RootAdmissionCompletionWitness,
    RootDispositionExecutionReceipt,
    canonical_json,
    completion_witness_from_payload,
    digest_mapping,
    require_digest,
    require_relative_core_path,
    root_disposition_receipt_from_payload,
)
from .errors import DeploymentAuthorityError, DeploymentIdempotencyConflict
from .ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from .schema import SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR, require_current_schema

if TYPE_CHECKING:
    from .root_blocker5_binding import (
        RootAdmissionEnvelope,
        RootAdmissionEnvelopeRecord,
        RootWriterFreezeEvidenceRecord,
        RootWriterFreezeWitness,
    )
    from .writer_freeze_evidence import RootWriterFreezeEvidencePayload


_CONTRACT = "TORMENT_B5_A2_CORE_MAINTENANCE_V1"
_ENTER_PENDING = "ENTER_CUTOVER_PENDING"
_ACTIVATE = "ACTIVATE_CORE"
_ABORT_PENDING = "ABORT_CUTOVER_PENDING"
_EVENT_KINDS = frozenset({_ENTER_PENDING, _ACTIVATE, _ABORT_PENDING})
# ``maintenance_events`` has a frozen kind CHECK constraint.  The receipt is
# part of the existing CUTOVER evidence stream and carries its own explicit
# contract, so no schema expansion or parallel ledger is introduced.
_ROOT_DISPOSITION_MAINTENANCE_KIND = "CUTOVER"
_ROOT_DISPOSITION_CONTRACT = "TORMENT_ROOT_DISPOSITION_EXECUTION_V1"
_ROOT_ENVELOPE_MAINTENANCE_KIND = "CUTOVER"
_ROOT_ENVELOPE_CONTRACT = "TORMENT_ROOT_ADMISSION_ENVELOPE_RECORD_V1"
_ROOT_WRITER_FREEZE_EVIDENCE_MAINTENANCE_KIND = "CUTOVER"
_ROOT_WRITER_FREEZE_EVIDENCE_CONTRACT = "TORMENT_ROOT_WRITER_FREEZE_EVIDENCE_RECORD_V1"


@dataclass(frozen=True)
class CoreDeploymentInspection:
    """Read-only contained-core facts used by selector and maintenance callers."""

    core_id: UUID
    core_role: str
    deployment_state: DeploymentState
    witness: CoreDeploymentWitness | None
    latest_maintenance_id: UUID | None
    ever_active: bool
    activation_completion_witness: CompletionWitness | None = None


@dataclass(frozen=True)
class CoreMaintenanceResult:
    """Committed core-side transition receipt; it grants no writer capability."""

    transition_kind: str
    maintenance_id: UUID
    witness: CoreDeploymentWitness
    selector_generation: int
    selector_witness_digest: str
    safe_abort_proven: bool = False
    completion_witness: CompletionWitness | None = None


def inspect_contained_core_deployment(
    *,
    data_root: str | Path,
    core_relative_path: str,
) -> CoreDeploymentInspection:
    """Read one controlled core path without creating it or changing it."""

    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True
    )
    # The resolver calls this function at startup.  It must not establish WAL,
    # create sidecars, or otherwise change a core merely to inspect authority
    # facts, so it deliberately does not reuse the rw maintenance boundary.
    connection = _open_readonly_core(path)
    try:
        return _inspect_connection(connection)
    finally:
        connection.close()


def contained_core_path(
    *,
    data_root: str | Path,
    core_relative_path: str,
    require_exists: bool,
) -> Path:
    """Resolve one selector-owned filename beneath data_root/substrate/cores."""

    name = require_relative_core_path(core_relative_path)
    root = _data_root(data_root)
    expected_root = root / "substrate" / "cores"
    if expected_root.is_symlink():
        raise DeploymentAuthorityError("contained core root must not be a symlink")
    if not expected_root.is_dir():
        if require_exists:
            raise DeploymentAuthorityError("contained core root is missing")
        return expected_root / name
    core_root = expected_root.resolve()
    if not _is_relative_to(core_root, root):
        raise DeploymentAuthorityError("contained core root escapes the data root")
    unresolved_path = expected_root / name
    if unresolved_path.is_symlink():
        raise DeploymentAuthorityError("selected contained core must not be a symlink")
    path = unresolved_path.resolve()
    if not _is_relative_to(path, core_root):
        raise DeploymentAuthorityError("selector core path escapes the contained core root")
    if require_exists and (not path.is_file() or path.suffix.lower() != ".db"):
        raise DeploymentAuthorityError("selected contained core is missing")
    return path


def staging_legacy_witness(
    inspection: CoreDeploymentInspection,
    *,
    descriptor_digest: str,
    profile_digest: str,
) -> CoreDeploymentWitness:
    """Bind supplied admission/profile evidence to an inert STAGING core."""

    require_digest(descriptor_digest, "descriptor_digest")
    require_digest(profile_digest, "profile_digest")
    if (
        inspection.core_role != "STAGING"
        or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE
    ):
        raise DeploymentAuthorityError("initial selector witness requires STAGING/LEGACY_ACTIVE core")
    return CoreDeploymentWitness(
        core_id=inspection.core_id,
        schema_id=SCHEMA_ID,
        schema_major=SCHEMA_MAJOR,
        schema_minor=SCHEMA_MINOR,
        core_role="STAGING",
        deployment_state=DeploymentState.LEGACY_ACTIVE,
        descriptor_digest=descriptor_digest,
        profile_digest=profile_digest,
    )


def enter_cutover_pending(
    *,
    data_root: str | Path,
    core_relative_path: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
) -> CoreMaintenanceResult:
    """Transition STAGING/LEGACY_ACTIVE to STAGING/CUTOVER_PENDING once."""

    if expected_witness.deployment_state is not DeploymentState.LEGACY_ACTIVE:
        raise DeploymentAuthorityError("pending maintenance requires LEGACY_ACTIVE predecessor witness")
    return _transition(
        data_root=data_root,
        core_relative_path=core_relative_path,
        transition_kind=_ENTER_PENDING,
        expected_witness=expected_witness,
        selector_generation=selector_generation,
        selector_witness_digest=selector_witness_digest,
        operation_key=operation_key,
    )


def activate_core(
    *,
    data_root: str | Path,
    core_relative_path: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
    completion_witness: CompletionWitness | None = None,
) -> CoreMaintenanceResult:
    """Transition STAGING/CUTOVER_PENDING to ACTIVE_CORE/NATIVE_ACTIVE once."""

    if expected_witness.deployment_state is not DeploymentState.CUTOVER_PENDING:
        raise DeploymentAuthorityError("activation maintenance requires CUTOVER_PENDING predecessor witness")
    if completion_witness is None:
        raise DeploymentAuthorityError("activation requires a completed admission witness")
    return _transition(
        data_root=data_root,
        core_relative_path=core_relative_path,
        transition_kind=_ACTIVATE,
        expected_witness=expected_witness,
        selector_generation=selector_generation,
        selector_witness_digest=selector_witness_digest,
        operation_key=operation_key,
        completion_witness=completion_witness,
    )


def record_root_admission_envelope(
    *,
    data_root: str | Path,
    core_relative_path: str,
    envelope: RootAdmissionEnvelope,
    operation_key: str,
) -> RootAdmissionEnvelopeRecord:
    """Persist one pre-P2 immutable root recovery record in core evidence."""

    from .root_blocker5_binding import RootAdmissionEnvelope, RootAdmissionEnvelopeRecord

    if not isinstance(envelope, RootAdmissionEnvelope):
        raise DeploymentAuthorityError("root envelope record requires a typed root envelope")
    _require_operation_key(operation_key)
    record = RootAdmissionEnvelopeRecord.from_envelope(envelope)
    record_digest = digest_mapping(record.payload())
    intent = {
        "contract": _ROOT_ENVELOPE_CONTRACT,
        "kind": "RECORD_ROOT_ADMISSION_ENVELOPE",
        "operation_key": operation_key,
        "root_admission_envelope_digest": envelope.digest,
        "record_digest": record_digest,
    }
    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True,
    )
    with open_existing_native_core_connection(path) as opened:
        connection = opened.connection
        inspection = _inspect_connection(connection)
        if (
            inspection.core_id != envelope.native_staging_core_id
            or inspection.core_role != "STAGING"
            or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE
            or inspection.witness is not None
            or inspection.ever_active
        ):
            raise DeploymentAuthorityError("root envelope record requires an inert staging core")
        existing = _root_envelope_events(connection)
        same_operation = next((item for item in existing if item["operation_key"] == operation_key), None)
        if same_operation is not None:
            if same_operation["canonical_intent"] != canonical_json(intent):
                raise DeploymentIdempotencyConflict("root envelope operation key was reused with different intent")
            return same_operation["record"]
        same_envelope = [
            item for item in existing
            if item["record"].envelope_digest == envelope.digest
        ]
        if same_envelope:
            if len(same_envelope) != 1 or same_envelope[0]["record"] != record:
                raise DeploymentAuthorityError("root envelope record conflicts with immutable admission evidence")
            return same_envelope[0]["record"]
        now_ns = time.time_ns()
        detail = {
            "canonical_intent": intent,
            "contract": _ROOT_ENVELOPE_CONTRACT,
            "core_id": str(inspection.core_id),
            "operation_key": operation_key,
            "record": record.payload(),
            "record_digest": record_digest,
            "recorded_at_ns": now_ns,
            "version": 1,
        }
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                "INSERT INTO maintenance_events VALUES (?, ?, ?, ?, ?)",
                (
                    native_id_to_bytes(generate_native_id()),
                    _ROOT_ENVELOPE_MAINTENANCE_KIND,
                    now_ns,
                    now_ns,
                    canonical_json(detail),
                ),
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
    return record


def read_root_admission_envelope_record(
    *,
    data_root: str | Path,
    core_relative_path: str,
    root_admission_envelope_digest: str,
) -> RootAdmissionEnvelopeRecord | None:
    """Read one exact immutable root envelope record without mutation."""

    require_digest(root_admission_envelope_digest, "root_admission_envelope_digest")
    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True,
    )
    connection = _open_readonly_core(path)
    try:
        inspection = _inspect_connection(connection)
        matches = [
            item["record"] for item in _root_envelope_events(connection)
            if item["record"].envelope_digest == root_admission_envelope_digest
        ]
        if len(matches) > 1:
            raise DeploymentAuthorityError("multiple root envelope records bind one admission identity")
        if not matches:
            return None
        record = matches[0]
        if record.envelope_payload.get("native_staging_core_id") != str(inspection.core_id):
            raise DeploymentAuthorityError("root envelope record names another core")
        return record
    finally:
        connection.close()


def record_root_writer_freeze_evidence(
    *,
    data_root: str | Path,
    core_relative_path: str,
    envelope: RootAdmissionEnvelope,
    writer_freeze_evidence: RootWriterFreezeEvidencePayload,
    writer_freeze: RootWriterFreezeWitness,
    operation_key: str,
) -> RootWriterFreezeEvidenceRecord:
    """Persist exact P2 writer-freeze recovery evidence after its envelope.

    This uses the existing immutable core maintenance stream.  It is
    subordinate evidence only and cannot alter selector or core authority.
    """

    from .root_blocker5_binding import (
        RootAdmissionEnvelope,
        RootWriterFreezeEvidenceRecord,
        RootWriterFreezeWitness,
    )
    from .writer_freeze_evidence import RootWriterFreezeEvidencePayload

    if not isinstance(envelope, RootAdmissionEnvelope):
        raise DeploymentAuthorityError("writer freeze evidence record requires a typed envelope")
    if not isinstance(writer_freeze_evidence, RootWriterFreezeEvidencePayload):
        raise DeploymentAuthorityError("writer freeze evidence record requires typed payload evidence")
    if not isinstance(writer_freeze, RootWriterFreezeWitness):
        raise DeploymentAuthorityError("writer freeze evidence record requires a typed witness")
    _require_operation_key(operation_key)
    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True,
    )
    with open_existing_native_core_connection(path) as opened:
        connection = opened.connection
        inspection = _inspect_connection(connection)
        if (
            inspection.core_id != envelope.native_staging_core_id
            or inspection.core_role != "STAGING"
            or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE
            or inspection.witness is not None
            or inspection.ever_active
        ):
            raise DeploymentAuthorityError("writer freeze evidence record requires an inert staging core")
        envelopes = [
            item["record"] for item in _root_envelope_events(connection)
            if item["record"].envelope_digest == envelope.digest
        ]
        if len(envelopes) != 1:
            raise DeploymentAuthorityError("writer freeze evidence record requires one persisted envelope")
        envelope_record = envelopes[0]
        record = RootWriterFreezeEvidenceRecord.from_evidence(
            root_admission_envelope_record=envelope_record,
            writer_freeze_evidence=writer_freeze_evidence,
            writer_freeze=writer_freeze,
        )
        record_digest = digest_mapping(record.payload())
        intent = {
            "contract": _ROOT_WRITER_FREEZE_EVIDENCE_CONTRACT,
            "kind": "RECORD_ROOT_WRITER_FREEZE_EVIDENCE",
            "operation_key": operation_key,
            "root_admission_envelope_digest": envelope.digest,
            "record_digest": record_digest,
        }
        existing = _root_writer_freeze_evidence_events(connection)
        same_operation = next((item for item in existing if item["operation_key"] == operation_key), None)
        if same_operation is not None:
            if same_operation["canonical_intent"] != canonical_json(intent):
                raise DeploymentIdempotencyConflict("writer freeze evidence operation key was reused with different intent")
            return same_operation["record"]
        same_envelope = [
            item for item in existing
            if item["record"].root_admission_envelope_digest == envelope.digest
        ]
        if same_envelope:
            if len(same_envelope) != 1 or same_envelope[0]["record"] != record:
                raise DeploymentAuthorityError("writer freeze evidence conflicts with immutable admission evidence")
            return same_envelope[0]["record"]
        now_ns = time.time_ns()
        detail = {
            "canonical_intent": intent,
            "contract": _ROOT_WRITER_FREEZE_EVIDENCE_CONTRACT,
            "core_id": str(inspection.core_id),
            "operation_key": operation_key,
            "record": record.payload(),
            "record_digest": record_digest,
            "recorded_at_ns": now_ns,
            "version": 1,
        }
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                "INSERT INTO maintenance_events VALUES (?, ?, ?, ?, ?)",
                (
                    native_id_to_bytes(generate_native_id()),
                    _ROOT_WRITER_FREEZE_EVIDENCE_MAINTENANCE_KIND,
                    now_ns,
                    now_ns,
                    canonical_json(detail),
                ),
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
    return record


def read_root_writer_freeze_evidence_record(
    *,
    data_root: str | Path,
    core_relative_path: str,
    root_admission_envelope_digest: str,
) -> RootWriterFreezeEvidenceRecord | None:
    """Read one exact subordinate writer-freeze record without mutation."""

    require_digest(root_admission_envelope_digest, "root_admission_envelope_digest")
    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True,
    )
    connection = _open_readonly_core(path)
    try:
        inspection = _inspect_connection(connection)
        matches = [
            item["record"] for item in _root_writer_freeze_evidence_events(connection)
            if item["record"].root_admission_envelope_digest == root_admission_envelope_digest
        ]
        if len(matches) > 1:
            raise DeploymentAuthorityError("multiple writer freeze evidence records bind one admission identity")
        if not matches:
            return None
        record = matches[0]
        if (
            record.root_admission_envelope_record.envelope_payload.get("native_staging_core_id")
            != str(inspection.core_id)
        ):
            raise DeploymentAuthorityError("writer freeze evidence record names another core")
        return record
    finally:
        connection.close()


def record_root_disposition_execution(
    *,
    data_root: str | Path,
    core_relative_path: str,
    completion_witness: RootAdmissionCompletionWitness,
    receipt: RootDispositionExecutionReceipt,
    operation_key: str,
) -> RootDispositionExecutionReceipt:
    """Persist the one post-P6 root disposition receipt in existing core evidence.

    This function is deliberately unavailable before the immutable P6 core
    activation event.  It appends evidence to the existing maintenance table;
    it neither changes selector authority nor introduces a progress ledger.
    """

    if not isinstance(completion_witness, RootAdmissionCompletionWitness):
        raise DeploymentAuthorityError("root disposition execution requires a v2 root completion witness")
    if not isinstance(receipt, RootDispositionExecutionReceipt):
        raise DeploymentAuthorityError("root disposition execution requires a typed receipt")
    _require_operation_key(operation_key)
    _require_root_receipt_matches_completion(receipt, completion_witness)
    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True
    )
    intent = {
        "contract": _ROOT_DISPOSITION_CONTRACT,
        "kind": "RECORD_ROOT_DISPOSITION_EXECUTION",
        "operation_key": operation_key,
        "receipt_digest": receipt.digest,
        "root_admission_envelope_digest": completion_witness.root_admission_envelope_digest,
    }
    with open_existing_native_core_connection(path) as opened:
        connection = opened.connection
        inspection = _inspect_connection(connection)
        if (
            inspection.core_role != "ACTIVE_CORE"
            or inspection.deployment_state is not DeploymentState.NATIVE_ACTIVE
            or inspection.activation_completion_witness != completion_witness
        ):
            raise DeploymentAuthorityError("root disposition execution requires the exact active P6 completion")
        existing = _root_disposition_events(connection)
        same_operation = next(
            (item for item in existing if item["operation_key"] == operation_key), None,
        )
        if same_operation is not None:
            if same_operation["canonical_intent"] != canonical_json(intent):
                raise DeploymentIdempotencyConflict("root disposition operation key was reused with different intent")
            return same_operation["receipt"]
        same_root = [
            item for item in existing
            if item["receipt"].root_admission_envelope_digest
            == completion_witness.root_admission_envelope_digest
        ]
        if same_root:
            if len(same_root) != 1 or same_root[0]["receipt"] != receipt:
                raise DeploymentAuthorityError("root disposition receipt conflicts with immutable root evidence")
            return same_root[0]["receipt"]
        detail = {
            "canonical_intent": intent,
            "contract": _ROOT_DISPOSITION_CONTRACT,
            "core_id": str(inspection.core_id),
            "operation_key": operation_key,
            "receipt": receipt.payload(),
            "receipt_digest": receipt.digest,
            "recorded_at_ns": time.time_ns(),
            "version": 1,
        }
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                "INSERT INTO maintenance_events VALUES (?, ?, ?, ?, ?)",
                (
                    native_id_to_bytes(generate_native_id()),
                    _ROOT_DISPOSITION_MAINTENANCE_KIND,
                    detail["recorded_at_ns"],
                    detail["recorded_at_ns"],
                    canonical_json(detail),
                ),
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
    return receipt


def read_root_disposition_execution_receipt(
    *,
    data_root: str | Path,
    core_relative_path: str,
    completion_witness: RootAdmissionCompletionWitness,
) -> RootDispositionExecutionReceipt | None:
    """Read the exact P6-to-P7 receipt without changing core state."""

    if not isinstance(completion_witness, RootAdmissionCompletionWitness):
        raise DeploymentAuthorityError("root disposition lookup requires a v2 root completion witness")
    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True
    )
    connection = _open_readonly_core(path)
    try:
        inspection = _inspect_connection(connection)
        if inspection.activation_completion_witness != completion_witness:
            raise DeploymentAuthorityError("root disposition lookup completion witness mismatch")
        matches = [
            item["receipt"]
            for item in _root_disposition_events(connection)
            if item["receipt"].root_admission_envelope_digest
            == completion_witness.root_admission_envelope_digest
        ]
        if len(matches) > 1:
            raise DeploymentAuthorityError("multiple root disposition receipts bind one completion")
        if matches:
            _require_root_receipt_matches_completion(matches[0], completion_witness)
            return matches[0]
        return None
    finally:
        connection.close()


def abort_cutover_pending(
    *,
    data_root: str | Path,
    core_relative_path: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
) -> CoreMaintenanceResult:
    """Safely return a never-active pending core to STAGING/LEGACY_ACTIVE."""

    if expected_witness.deployment_state is not DeploymentState.CUTOVER_PENDING:
        raise DeploymentAuthorityError("pending abort requires CUTOVER_PENDING predecessor witness")
    return _transition(
        data_root=data_root,
        core_relative_path=core_relative_path,
        transition_kind=_ABORT_PENDING,
        expected_witness=expected_witness,
        selector_generation=selector_generation,
        selector_witness_digest=selector_witness_digest,
        operation_key=operation_key,
    )


def _transition(
    *,
    data_root: str | Path,
    core_relative_path: str,
    transition_kind: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
    completion_witness: CompletionWitness | None = None,
) -> CoreMaintenanceResult:
    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True
    )
    _require_operation_key(operation_key)
    _require_selector_facts(selector_generation, selector_witness_digest)
    if completion_witness is not None:
        if transition_kind != _ACTIVATE:
            raise DeploymentAuthorityError("completion witness is valid only for core activation")
        if (
            completion_witness.admission_identity_digest != expected_witness.descriptor_digest
            or completion_witness.native_core_id != expected_witness.core_id
        ):
            raise DeploymentAuthorityError("completion witness does not match the selected admission identity")
        if completion_witness.profile_digest is None:
            raise DeploymentAuthorityError("activation requires a completion witness bound to the selected profile")
        if completion_witness.profile_digest != expected_witness.profile_digest:
            raise DeploymentAuthorityError("completion witness does not match the selected deployment profile")
    with open_existing_native_core_connection(path) as opened:
        connection = opened.connection
        before = _inspect_connection(connection)
        if before.core_id != expected_witness.core_id:
            raise DeploymentAuthorityError("core maintenance witness names another core")
        intent = _intent(
            transition_kind=transition_kind,
            expected_witness=expected_witness,
            selector_generation=selector_generation,
            selector_witness_digest=selector_witness_digest,
            operation_key=operation_key,
            completion_witness=completion_witness,
        )
        existing = _event_for_operation(connection, operation_key)
        if existing is not None:
            return _recover_existing_transition(
                inspection=before,
                event=existing,
                expected_intent=intent,
            )
        _require_predecessor(before, expected_witness, transition_kind)
        if transition_kind == _ABORT_PENDING and before.ever_active:
            raise DeploymentAuthorityError("post-native reverse transition is refused")

        result_witness = _result_witness(expected_witness, transition_kind)
        maintenance_id = generate_native_id()
        now_ns = time.time_ns()
        detail = _event_detail(
            transition_kind=transition_kind,
            maintenance_id=maintenance_id,
            intent=intent,
            previous=expected_witness,
            result=result_witness,
            selector_generation=selector_generation,
            selector_witness_digest=selector_witness_digest,
            recorded_at_ns=now_ns,
            completion_witness=completion_witness,
        )
        connection.execute("BEGIN IMMEDIATE")
        try:
            _write_core_state(connection, result_witness)
            connection.execute(
                "INSERT INTO maintenance_events VALUES (?, 'CUTOVER', ?, ?, ?)",
                (
                    native_id_to_bytes(maintenance_id),
                    now_ns,
                    now_ns,
                    canonical_json(detail),
                ),
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
    return CoreMaintenanceResult(
        transition_kind=transition_kind,
        maintenance_id=maintenance_id,
        witness=result_witness,
        selector_generation=selector_generation,
        selector_witness_digest=selector_witness_digest,
        safe_abort_proven=transition_kind == _ABORT_PENDING,
        completion_witness=completion_witness,
    )


def _inspect_connection(connection: sqlite3.Connection) -> CoreDeploymentInspection:
    metadata = require_current_schema(connection)
    core_id = native_id_from_bytes(metadata.core_id)
    rows = connection.execute(
        "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
    ).fetchall()
    if len(rows) != 1:
        raise DeploymentAuthorityError("core deployment metadata is not singleton")
    try:
        deployment_state = DeploymentState(rows[0][0])
    except (TypeError, ValueError) as exc:
        raise DeploymentAuthorityError("core deployment state is invalid") from exc
    referenced = rows[0][1]
    valid_pairs = {
        ("STAGING", DeploymentState.LEGACY_ACTIVE, None),
        ("STAGING", DeploymentState.CUTOVER_PENDING, native_id_to_bytes(core_id)),
        ("ACTIVE_CORE", DeploymentState.NATIVE_ACTIVE, native_id_to_bytes(core_id)),
    }
    if (metadata.core_role, deployment_state, referenced) not in valid_pairs:
        raise DeploymentAuthorityError("core role/deployment metadata is incompatible")

    events = _core_events(connection, core_id)
    latest = events[-1] if events else None
    if latest is None:
        return CoreDeploymentInspection(
            core_id=core_id,
            core_role=metadata.core_role,
            deployment_state=deployment_state,
            witness=None,
            latest_maintenance_id=None,
            ever_active=False,
        )
    expected_chain = ("STAGING", DeploymentState.LEGACY_ACTIVE)
    ever_active = False
    for event in events:
        previous = event["previous"]
        result = event["result"]
        if (
            previous["core_role"],
            DeploymentState(previous["deployment_state"]),
        ) != expected_chain:
            raise DeploymentAuthorityError("core maintenance evidence predecessor chain is inconsistent")
        kind = event["transition_kind"]
        expected_result = {
            _ENTER_PENDING: ("STAGING", DeploymentState.CUTOVER_PENDING),
            _ACTIVATE: ("ACTIVE_CORE", DeploymentState.NATIVE_ACTIVE),
            _ABORT_PENDING: ("STAGING", DeploymentState.LEGACY_ACTIVE),
        }[kind]
        if (
            result["core_role"],
            DeploymentState(result["deployment_state"]),
        ) != expected_result:
            raise DeploymentAuthorityError("core maintenance evidence transition is invalid")
        expected_chain = expected_result
        ever_active = ever_active or kind == _ACTIVATE
    if (metadata.core_role, deployment_state) != expected_chain:
        raise DeploymentAuthorityError("core metadata disagrees with immutable maintenance evidence")
    witness = _witness_from_event_result(latest["result"])
    activation_completion = next(
        (item.get("completion_witness") for item in reversed(events)
         if item["transition_kind"] == _ACTIVATE),
        None,
    )
    return CoreDeploymentInspection(
        core_id=core_id,
        core_role=metadata.core_role,
        deployment_state=deployment_state,
        witness=witness,
        latest_maintenance_id=latest["maintenance_id"],
        ever_active=ever_active,
        activation_completion_witness=activation_completion,
    )


def _core_events(connection: sqlite3.Connection, core_id: UUID) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT maintenance_id,completed_at_ns,detail_json FROM maintenance_events "
        "WHERE maintenance_kind='CUTOVER' ORDER BY completed_at_ns,maintenance_id"
    ).fetchall()
    events: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for maintenance_id_raw, _completed_at_ns, detail_raw in rows:
        try:
            detail = json.loads(detail_raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise DeploymentAuthorityError("core CUTOVER evidence is malformed") from exc
        if not isinstance(detail, dict) or detail.get("contract") != _CONTRACT:
            continue
        if canonical_json(detail) != detail_raw:
            raise DeploymentAuthorityError("core maintenance evidence is non-canonical")
        try:
            maintenance_id = native_id_from_bytes(maintenance_id_raw)
            kind = detail["transition_kind"]
            key = detail["operation_key"]
            intent = detail["canonical_intent"]
            previous = detail["previous"]
            result = detail["result"]
            completion = _completion_witness_from_payload(detail.get("completion_witness"))
            if (
                kind not in _EVENT_KINDS
                or not isinstance(key, str)
                or not key
                or not isinstance(intent, dict)
                or not isinstance(previous, dict)
                or not isinstance(result, dict)
                or detail["maintenance_id"] != str(maintenance_id)
                or detail["core_id"] != str(core_id)
                or (kind != _ACTIVATE and completion is not None)
            ):
                raise ValueError("invalid event shape")
            if key in seen_keys:
                raise ValueError("duplicate operation key")
            seen_keys.add(key)
            _witness_from_event_result(previous)
            _witness_from_event_result(result)
            if (
                UUID(previous["core_id"]) != core_id
                or UUID(result["core_id"]) != core_id
            ):
                raise ValueError("event witness names another core")
            if detail["selector_generation"] < 0:
                raise ValueError("invalid selector generation")
            require_digest(detail["selector_witness_digest"], "selector_witness_digest")
            if ("completion_witness" in detail) != ("completion_witness" in intent):
                raise ValueError("event completion witness is not intent-bound")
            expected_intent = _intent(
                transition_kind=kind,
                expected_witness=_witness_from_event_result(previous),
                selector_generation=detail["selector_generation"],
                selector_witness_digest=detail["selector_witness_digest"],
                operation_key=key,
                completion_witness=completion,
            )
            # Read old B5-A2 records exactly as written.  New records bind the
            # optional completion witness in both detail and canonical intent.
            if "completion_witness" not in intent:
                expected_intent.pop("completion_witness")
            if intent != expected_intent:
                raise ValueError("event intent does not bind its transition evidence")
        except (KeyError, TypeError, ValueError, DeploymentAuthorityError) as exc:
            raise DeploymentAuthorityError("core maintenance evidence is incompatible") from exc
        events.append({**detail, "maintenance_id": maintenance_id, "completion_witness": completion})
    return events


def _root_disposition_events(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT detail_json FROM maintenance_events WHERE maintenance_kind=? "
        "ORDER BY completed_at_ns,maintenance_id",
        (_ROOT_DISPOSITION_MAINTENANCE_KIND,),
    ).fetchall()
    events: list[dict[str, Any]] = []
    keys: set[str] = set()
    for (detail_raw,) in rows:
        try:
            detail = json.loads(detail_raw)
            if not isinstance(detail, dict) or detail.get("contract") != _ROOT_DISPOSITION_CONTRACT:
                continue
            if (
                detail.get("version") != 1
                or canonical_json(detail) != detail_raw
                or not isinstance(detail.get("operation_key"), str)
                or not detail["operation_key"]
                or not isinstance(detail.get("canonical_intent"), dict)
                or not isinstance(detail.get("receipt_digest"), str)
            ):
                raise ValueError("event shape")
            receipt = root_disposition_receipt_from_payload(detail.get("receipt"))
            if receipt.digest != detail["receipt_digest"]:
                raise ValueError("receipt digest")
            expected_intent = {
                "contract": _ROOT_DISPOSITION_CONTRACT,
                "kind": "RECORD_ROOT_DISPOSITION_EXECUTION",
                "operation_key": detail["operation_key"],
                "receipt_digest": receipt.digest,
                "root_admission_envelope_digest": receipt.root_admission_envelope_digest,
            }
            if detail["canonical_intent"] != expected_intent:
                raise ValueError("intent")
            if detail["operation_key"] in keys:
                raise ValueError("duplicate operation key")
            keys.add(detail["operation_key"])
        except (TypeError, ValueError, json.JSONDecodeError, DeploymentAuthorityError) as exc:
            raise DeploymentAuthorityError("root disposition execution evidence is malformed") from exc
        events.append({
            "operation_key": detail["operation_key"],
            "canonical_intent": canonical_json(detail["canonical_intent"]),
            "receipt": receipt,
        })
    return events


def _root_envelope_events(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Decode only explicit immutable root-envelope evidence records."""

    from .root_blocker5_binding import (
        RootBlocker5BindingRefused,
        root_admission_envelope_record_from_payload,
    )

    rows = connection.execute(
        "SELECT detail_json FROM maintenance_events WHERE maintenance_kind=? "
        "ORDER BY completed_at_ns,maintenance_id",
        (_ROOT_ENVELOPE_MAINTENANCE_KIND,),
    ).fetchall()
    events: list[dict[str, Any]] = []
    keys: set[str] = set()
    for (detail_raw,) in rows:
        try:
            detail = json.loads(detail_raw)
            if not isinstance(detail, dict) or detail.get("contract") != _ROOT_ENVELOPE_CONTRACT:
                continue
            if (
                detail.get("version") != 1
                or canonical_json(detail) != detail_raw
                or not isinstance(detail.get("operation_key"), str)
                or not detail["operation_key"]
                or not isinstance(detail.get("canonical_intent"), dict)
                or not isinstance(detail.get("record_digest"), str)
                or not isinstance(detail.get("core_id"), str)
            ):
                raise ValueError("event shape")
            record = root_admission_envelope_record_from_payload(detail.get("record"))
            record_digest = digest_mapping(record.payload())
            if record_digest != detail["record_digest"]:
                raise ValueError("record digest")
            expected_intent = {
                "contract": _ROOT_ENVELOPE_CONTRACT,
                "kind": "RECORD_ROOT_ADMISSION_ENVELOPE",
                "operation_key": detail["operation_key"],
                "root_admission_envelope_digest": record.envelope_digest,
                "record_digest": record_digest,
            }
            if detail["canonical_intent"] != expected_intent:
                raise ValueError("intent")
            if detail["operation_key"] in keys:
                raise ValueError("duplicate operation key")
            keys.add(detail["operation_key"])
        except (TypeError, ValueError, json.JSONDecodeError, DeploymentAuthorityError, RootBlocker5BindingRefused) as exc:
            raise DeploymentAuthorityError("root admission envelope evidence is malformed") from exc
        events.append({
            "operation_key": detail["operation_key"],
            "canonical_intent": canonical_json(detail["canonical_intent"]),
            "record": record,
        })
    return events


def _root_writer_freeze_evidence_events(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Decode subordinate payload records against immutable envelope records."""

    from .root_blocker5_binding import (
        RootBlocker5BindingRefused,
        root_writer_freeze_evidence_record_from_payload,
    )

    envelopes = {
        item["record"].envelope_digest: item["record"]
        for item in _root_envelope_events(connection)
    }
    rows = connection.execute(
        "SELECT detail_json FROM maintenance_events WHERE maintenance_kind=? "
        "ORDER BY completed_at_ns,maintenance_id",
        (_ROOT_WRITER_FREEZE_EVIDENCE_MAINTENANCE_KIND,),
    ).fetchall()
    events: list[dict[str, Any]] = []
    keys: set[str] = set()
    for (detail_raw,) in rows:
        try:
            detail = json.loads(detail_raw)
            if not isinstance(detail, dict) or detail.get("contract") != _ROOT_WRITER_FREEZE_EVIDENCE_CONTRACT:
                continue
            if (
                detail.get("version") != 1
                or canonical_json(detail) != detail_raw
                or not isinstance(detail.get("operation_key"), str)
                or not detail["operation_key"]
                or not isinstance(detail.get("canonical_intent"), dict)
                or not isinstance(detail.get("record_digest"), str)
                or not isinstance(detail.get("core_id"), str)
            ):
                raise ValueError("event shape")
            raw_record = detail.get("record")
            if not isinstance(raw_record, dict):
                raise ValueError("record shape")
            digest = raw_record.get("root_admission_envelope_digest")
            if not isinstance(digest, str) or digest not in envelopes:
                raise ValueError("missing envelope")
            record = root_writer_freeze_evidence_record_from_payload(
                raw_record,
                root_admission_envelope_record=envelopes[digest],
            )
            record_digest = digest_mapping(record.payload())
            if record_digest != detail["record_digest"]:
                raise ValueError("record digest")
            expected_intent = {
                "contract": _ROOT_WRITER_FREEZE_EVIDENCE_CONTRACT,
                "kind": "RECORD_ROOT_WRITER_FREEZE_EVIDENCE",
                "operation_key": detail["operation_key"],
                "root_admission_envelope_digest": record.root_admission_envelope_digest,
                "record_digest": record_digest,
            }
            if detail["canonical_intent"] != expected_intent:
                raise ValueError("intent")
            if detail["operation_key"] in keys:
                raise ValueError("duplicate operation key")
            keys.add(detail["operation_key"])
        except (TypeError, ValueError, json.JSONDecodeError, DeploymentAuthorityError, RootBlocker5BindingRefused) as exc:
            raise DeploymentAuthorityError("root writer freeze evidence is malformed") from exc
        events.append({
            "operation_key": detail["operation_key"],
            "canonical_intent": canonical_json(detail["canonical_intent"]),
            "record": record,
        })
    return events


def _require_root_receipt_matches_completion(
    receipt: RootDispositionExecutionReceipt,
    completion: RootAdmissionCompletionWitness,
) -> None:
    if (
        receipt.root_admission_envelope_digest != completion.root_admission_envelope_digest
        or receipt.native_staging_core_id != completion.native_staging_core_id
        or receipt.geometry_disposition_table_digest != completion.geometry_disposition_table_digest
    ):
        raise DeploymentAuthorityError("root disposition receipt does not match root completion evidence")


def _event_for_operation(connection: sqlite3.Connection, operation_key: str) -> dict[str, Any] | None:
    rows = connection.execute(
        "SELECT maintenance_id,detail_json FROM maintenance_events WHERE maintenance_kind='CUTOVER'"
    ).fetchall()
    matches: list[dict[str, Any]] = []
    for maintenance_id_raw, detail_raw in rows:
        try:
            detail = json.loads(detail_raw)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(detail, dict) and detail.get("contract") == _CONTRACT and detail.get("operation_key") == operation_key:
            detail = dict(detail)
            detail["maintenance_id"] = native_id_from_bytes(maintenance_id_raw)
            matches.append(detail)
    if len(matches) > 1:
        raise DeploymentAuthorityError("core maintenance operation key is not unique")
    return matches[0] if matches else None


def _recover_existing_transition(
    *,
    inspection: CoreDeploymentInspection,
    event: dict[str, Any],
    expected_intent: dict[str, Any],
) -> CoreMaintenanceResult:
    if canonical_json(event.get("canonical_intent", {})) != canonical_json(expected_intent):
        raise DeploymentIdempotencyConflict("core maintenance operation key was reused with different intent")
    witness = _witness_from_event_result(event["result"])
    # A later, separately authorized maintenance event may have advanced the
    # core after this caller lost its response.  The inspected evidence chain
    # has already proved that the historic event remains genuine, so return its
    # immutable receipt rather than allocating a second transition.
    del inspection
    return CoreMaintenanceResult(
        transition_kind=event["transition_kind"],
        maintenance_id=event["maintenance_id"],
        witness=witness,
        selector_generation=event["selector_generation"],
        selector_witness_digest=event["selector_witness_digest"],
        safe_abort_proven=event["transition_kind"] == _ABORT_PENDING,
        completion_witness=_completion_witness_from_payload(event.get("completion_witness")),
    )


def _require_predecessor(
    inspection: CoreDeploymentInspection,
    expected_witness: CoreDeploymentWitness,
    transition_kind: str,
) -> None:
    if inspection.witness is None:
        actual = staging_legacy_witness(
            inspection,
            descriptor_digest=expected_witness.descriptor_digest,
            profile_digest=expected_witness.profile_digest,
        )
    else:
        actual = inspection.witness
    if actual != expected_witness:
        raise DeploymentAuthorityError("core maintenance predecessor witness mismatch")
    required = {
        _ENTER_PENDING: ("STAGING", DeploymentState.LEGACY_ACTIVE),
        _ACTIVATE: ("STAGING", DeploymentState.CUTOVER_PENDING),
        _ABORT_PENDING: ("STAGING", DeploymentState.CUTOVER_PENDING),
    }[transition_kind]
    if (inspection.core_role, inspection.deployment_state) != required:
        raise DeploymentAuthorityError("core maintenance predecessor state is not eligible")


def _result_witness(
    predecessor: CoreDeploymentWitness, transition_kind: str
) -> CoreDeploymentWitness:
    role, state = {
        _ENTER_PENDING: ("STAGING", DeploymentState.CUTOVER_PENDING),
        _ACTIVATE: ("ACTIVE_CORE", DeploymentState.NATIVE_ACTIVE),
        _ABORT_PENDING: ("STAGING", DeploymentState.LEGACY_ACTIVE),
    }[transition_kind]
    return CoreDeploymentWitness(
        core_id=predecessor.core_id,
        schema_id=predecessor.schema_id,
        schema_major=predecessor.schema_major,
        schema_minor=predecessor.schema_minor,
        core_role=role,
        deployment_state=state,
        descriptor_digest=predecessor.descriptor_digest,
        profile_digest=predecessor.profile_digest,
    )


def _write_core_state(connection: sqlite3.Connection, witness: CoreDeploymentWitness) -> None:
    connection.execute(
        "UPDATE core_metadata SET core_role=? WHERE singleton=1",
        (witness.core_role,),
    )
    reference = (
        None
        if witness.deployment_state is DeploymentState.LEGACY_ACTIVE
        else native_id_to_bytes(witness.core_id)
    )
    connection.execute(
        "UPDATE deployment_metadata SET deployment_state=?,referenced_core_id=?,updated_at_ns=? WHERE singleton=1",
        (witness.deployment_state.value, reference, time.time_ns()),
    )


def _intent(
    *,
    transition_kind: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
    completion_witness: CompletionWitness | None,
) -> dict[str, Any]:
    return {
        "contract": _CONTRACT,
        "transition_kind": transition_kind,
        "operation_key": operation_key,
        "expected_witness_digest": expected_witness.digest,
        "selector_generation": selector_generation,
        "selector_witness_digest": selector_witness_digest,
        "completion_witness": (
            None if completion_witness is None else completion_witness.payload()
        ),
    }


def _event_detail(
    *,
    transition_kind: str,
    maintenance_id: UUID,
    intent: dict[str, Any],
    previous: CoreDeploymentWitness,
    result: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    recorded_at_ns: int,
    completion_witness: CompletionWitness | None,
) -> dict[str, Any]:
    return {
        "canonical_intent": intent,
        "completion_witness": (
            None if completion_witness is None else completion_witness.payload()
        ),
        "contract": _CONTRACT,
        "core_id": str(result.core_id),
        "maintenance_id": str(maintenance_id),
        "operation_key": intent["operation_key"],
        "previous": _witness_payload(previous),
        "recorded_at_ns": recorded_at_ns,
        "result": _witness_payload(result),
        "selector_generation": selector_generation,
        "selector_witness_digest": selector_witness_digest,
        "transition_kind": transition_kind,
    }


def _completion_witness_from_payload(value: Any) -> CompletionWitness | None:
    if value is None:
        return None
    try:
        return completion_witness_from_payload(value)
    except DeploymentAuthorityError as exc:
        raise DeploymentAuthorityError("core activation completion witness is malformed") from exc


def _witness_payload(witness: CoreDeploymentWitness) -> dict[str, Any]:
    return {
        "core_id": str(witness.core_id),
        "core_role": witness.core_role,
        "deployment_state": witness.deployment_state.value,
        "descriptor_digest": witness.descriptor_digest,
        "profile_digest": witness.profile_digest,
        "schema_id": witness.schema_id,
        "schema_major": witness.schema_major,
        "schema_minor": witness.schema_minor,
    }


def _witness_from_event_result(value: dict[str, Any]) -> CoreDeploymentWitness:
    return CoreDeploymentWitness(
        core_id=UUID(value["core_id"]),
        schema_id=value["schema_id"],
        schema_major=value["schema_major"],
        schema_minor=value["schema_minor"],
        core_role=value["core_role"],
        deployment_state=DeploymentState(value["deployment_state"]),
        descriptor_digest=value["descriptor_digest"],
        profile_digest=value["profile_digest"],
    )


def _data_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DeploymentAuthorityError("deployment data root is required")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise DeploymentAuthorityError("deployment data root must already exist")
    return root


def _open_readonly_core(path: Path) -> sqlite3.Connection:
    """Open a qualified core solely for resolver inspection, with no WAL setup."""

    from .runtime_qualification import qualify_runtime

    qualify_runtime()
    try:
        connection = sqlite3.connect(
            f"{path.as_uri()}?mode=ro",
            uri=True,
            isolation_level=None,
            check_same_thread=True,
        )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA query_only = ON")
        return connection
    except sqlite3.Error as exc:
        raise DeploymentAuthorityError("contained core cannot be opened read-only") from exc


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_operation_key(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise DeploymentAuthorityError("maintenance operation_key must be bounded non-empty text")
    return value


def _require_selector_facts(generation: object, witness_digest: object) -> None:
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise DeploymentAuthorityError("selector_generation must be non-negative")
    require_digest(witness_digest, "selector_witness_digest")


__all__ = [
    "CoreDeploymentInspection",
    "CoreMaintenanceResult",
    "abort_cutover_pending",
    "activate_core",
    "contained_core_path",
    "enter_cutover_pending",
    "inspect_contained_core_deployment",
    "read_root_admission_envelope_record",
    "read_root_writer_freeze_evidence_record",
    "read_root_disposition_execution_receipt",
    "record_root_admission_envelope",
    "record_root_writer_freeze_evidence",
    "record_root_disposition_execution",
    "staging_legacy_witness",
]
