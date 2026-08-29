"""Focused Phase 7E3 reconciliation and later-integrity proofs."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import (
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.objects import NativeObjectService, ObjectState, SubstrateTx
from torment_service.substrate.reconciliation import (
    INTEGRITY_MISMATCH_CONDITION,
    NativeReconciliationService,
    ReconciliationCaseRequest,
    ReconciliationSuccessorRequest,
)
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationIntegrityVerificationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.schema import create_schema, validate_schema


def _uuid():
    return generate_native_id()


def _state(namespace, scope):
    return ObjectState(namespace, scope, "NOTE", "EXISTS", "LIVE", True, "GOVERNED")


def _seed(connection):
    namespace, scope, idempotency_namespace = _uuid(), _uuid(), _uuid()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(namespace), "reconciliation-identity"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), "reconciliation-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "reconciliation-idempotency"),
    )
    return namespace, scope, idempotency_namespace


def _ready_representation(connection, idempotency_namespace, namespace, scope, *, payload=b"valid001"):
    objects = NativeObjectService(connection)
    source = objects.create_object(
        idempotency_namespace_id=idempotency_namespace,
        idempotency_key="source-object",
        state=_state(namespace, scope),
    )
    service = NativeRepresentationService(connection)
    pending = service.create_representation_pending(
        idempotency_namespace_id=idempotency_namespace,
        idempotency_key="representation-pending",
        request=RepresentationRequest(
            "OBJECT_REVISION",
            source.object_id,
            source.revision_id,
            None,
            None,
            "EMBEDDING",
            1,
            "v1",
            "raw",
            expected_payload_byte_length=len(payload),
        ),
    )
    service.establish_representation_integrity_expectation(
        idempotency_namespace_id=idempotency_namespace,
        idempotency_key="representation-expectation",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id,
            INTEGRITY_ALGORITHM_SHA256,
            sha256(payload).digest(),
            INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    ready = service.publish_representation_ready(
        idempotency_namespace_id=idempotency_namespace,
        idempotency_key="representation-ready",
        request=RepresentationReadyRequest(
            pending.representation_id, "EMBEDDING", 1, "v1", "raw", payload
        ),
    )
    return objects, source, service, ready


def _corrupt_stored_payload_for_fault_injection(connection, representation_id, replacement: bytes) -> None:
    """Simulate external durable-byte corruption; restore normal guards immediately."""
    connection.execute("DROP TRIGGER immutable_payload_update")
    try:
        connection.execute(
            "UPDATE representation_payloads SET payload_bytes=? WHERE representation_id=?",
            (replacement, native_id_to_bytes(representation_id)),
        )
    finally:
        connection.execute(
            """
            CREATE TRIGGER immutable_payload_update
            BEFORE UPDATE ON representation_payloads
            BEGIN SELECT RAISE(ABORT,'immutable representation payload'); END
            """
        )


def test_later_match_measurement_is_append_only_and_idempotent(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "later-match.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        _, _, service, ready = _ready_representation(
            connection, idempotency_namespace, namespace, scope
        )
        first_measurement = ready.selected_measurement_id
        request = RepresentationIntegrityVerificationRequest(ready.representation_id, "periodic check")
        verified = service.verify_published_representation_integrity(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="later-match",
            request=request,
        )
        retry = service.verify_published_representation_integrity(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="later-match",
            request=request,
        )
        current = service.get_representation_metadata(ready.representation_id)
        assert retry == verified
        assert (verified.result, current.readiness, current.disposition) == ("MATCH", "READY", "USABLE")
        assert current.selected_measurement_id == verified.measurement_id
        assert verified.measurement_id != first_measurement
        assert connection.execute(
            "SELECT result FROM integrity_measurements WHERE expectation_id=(SELECT expectation_id FROM integrity_measurements WHERE measurement_id=?) ORDER BY measured_at_ns",
            (native_id_to_bytes(first_measurement),),
        ).fetchall() == [("MATCH",), ("MATCH",)]
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE integrity_measurements SET result='MISMATCH' WHERE measurement_id=?",
                (native_id_to_bytes(first_measurement),),
            )
    finally:
        qualified.close()


def test_later_mismatch_withholds_use_opens_reconciliation_and_preserves_source_truth(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "later-mismatch.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        objects, source, service, ready = _ready_representation(
            connection, idempotency_namespace, namespace, scope
        )
        source_before = objects.get_current_object(source.object_id)
        source_revision_count = connection.execute(
            "SELECT count(*) FROM object_revisions WHERE object_id=?",
            (native_id_to_bytes(source.object_id),),
        ).fetchone()[0]
        source_transition = connection.execute(
            "SELECT transition_id,operation_id,transition_kind FROM semantic_transitions WHERE transition_id=?",
            (native_id_to_bytes(source.transition_id),),
        ).fetchone()
        ready_transition = connection.execute(
            "SELECT transition_id,operation_id,committed_at_ns FROM semantic_transitions WHERE transition_id=(SELECT t.transition_id FROM semantic_transitions t JOIN representation_state_effects e USING(transition_id) WHERE t.transition_kind='REPRESENTATION_READY' AND e.representation_id=?)",
            (native_id_to_bytes(ready.representation_id),),
        ).fetchone()
        first_measurement = ready.selected_measurement_id
        _corrupt_stored_payload_for_fault_injection(connection, ready.representation_id, b"broken01")

        verification_request = RepresentationIntegrityVerificationRequest(
            ready.representation_id, "durable bytes rechecked"
        )
        mismatch = service.verify_published_representation_integrity(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="later-mismatch",
            request=verification_request,
        )
        after_mismatch = service.get_representation_metadata(ready.representation_id)
        assert (mismatch.result, after_mismatch.readiness, after_mismatch.disposition) == (
            "MISMATCH",
            "READY",
            "RECONCILIATION_REQUIRED",
        )
        assert after_mismatch.selected_measurement_id == mismatch.measurement_id
        assert after_mismatch.active_reconciliation_case_id is None
        with pytest.raises(SubstrateObjectNotFound):
            service.read_representation_payload(ready.representation_id)

        reconciliations = NativeReconciliationService(connection)
        open_request = ReconciliationCaseRequest(
            ready.representation_id,
            INTEGRITY_MISMATCH_CONDITION,
            "later SHA256 measurement differs from immutable expectation",
            "WITHHELD",
            "OPEN_MISMATCH_REVIEW",
        )
        opened = reconciliations.open_reconciliation_case(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="open-reconciliation",
            request=open_request,
        )
        # Treat the first response as lost and reconstruct solely from durable identity/intent.
        retried = reconciliations.open_reconciliation_case(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="open-reconciliation",
            request=open_request,
        )
        current = service.get_representation_metadata(ready.representation_id)
        assert retried == opened
        assert connection.execute(
            "SELECT count(*) FROM reconciliation_cases WHERE representation_id=?",
            (native_id_to_bytes(ready.representation_id),),
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM reconciliation_state_effects WHERE reconciliation_case_id=?",
            (native_id_to_bytes(opened.case.reconciliation_case_id),),
        ).fetchone()[0] == 1
        assert (current.readiness, current.disposition) == ("READY", "WITHHELD")
        assert (current.active_reconciliation_case_id, current.active_reconciliation_state_id) == (
            opened.case.reconciliation_case_id,
            opened.case.current_state_id,
        )
        assert connection.execute(
            """
            SELECT count(*) FROM reconciliation_state_effects r
            JOIN representation_state_effects p USING(transition_id)
            WHERE r.transition_id=? AND p.representation_id=? AND p.operational_disposition='WITHHELD'
            """,
            (native_id_to_bytes(opened.transition_id), native_id_to_bytes(ready.representation_id)),
        ).fetchone()[0] == 1
        assert connection.execute(
            """
            SELECT count(*) FROM operation_outputs
            WHERE operation_id=? AND output_kind='RECONCILIATION_CASE'
              AND reconciliation_case_id=? AND reconciliation_state_id=? AND reconciliation_state_ordinal=1
            """,
            (
                native_id_to_bytes(opened.operation_id),
                native_id_to_bytes(opened.case.reconciliation_case_id),
                native_id_to_bytes(opened.case.current_state_id),
            ),
        ).fetchone()[0] == 1
        measurements = connection.execute(
            "SELECT measurement_id,result FROM integrity_measurements ORDER BY measured_at_ns"
        ).fetchall()
        assert measurements == [
            (native_id_to_bytes(first_measurement), "MATCH"),
            (native_id_to_bytes(mismatch.measurement_id), "MISMATCH"),
        ]
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "DELETE FROM integrity_measurements WHERE measurement_id=?",
                (native_id_to_bytes(first_measurement),),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE integrity_measurements SET result='MATCH' WHERE measurement_id=?",
                (native_id_to_bytes(mismatch.measurement_id),),
            )
        assert connection.execute(
            "SELECT transition_id,operation_id,committed_at_ns FROM semantic_transitions WHERE transition_id=?",
            (ready_transition[0],),
        ).fetchone() == ready_transition
        assert objects.get_current_object(source.object_id) == source_before
        assert connection.execute(
            "SELECT count(*) FROM object_revisions WHERE object_id=?",
            (native_id_to_bytes(source.object_id),),
        ).fetchone()[0] == source_revision_count
        assert connection.execute(
            "SELECT transition_id,operation_id,transition_kind FROM semantic_transitions WHERE transition_id=?",
            (native_id_to_bytes(source.transition_id),),
        ).fetchone() == source_transition
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE reconciliation_case_states SET determination='rewritten' WHERE reconciliation_state_id=?",
                (native_id_to_bytes(opened.case.current_state_id),),
            )
        validate_schema(connection)
    finally:
        qualified.close()


def test_reconciliation_successor_is_linear_idempotent_and_rejects_stale_state(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "successor.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        _, _, service, ready = _ready_representation(connection, idempotency_namespace, namespace, scope)
        _corrupt_stored_payload_for_fault_injection(connection, ready.representation_id, b"broken01")
        service.verify_published_representation_integrity(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="mismatch",
            request=RepresentationIntegrityVerificationRequest(ready.representation_id),
        )
        reconciliations = NativeReconciliationService(connection)
        opened = reconciliations.open_reconciliation_case(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="open",
            request=ReconciliationCaseRequest(
                ready.representation_id,
                INTEGRITY_MISMATCH_CONDITION,
                "mismatch evidence requires review",
            ),
        )
        successor_request = ReconciliationSuccessorRequest(
            opened.case.reconciliation_case_id,
            opened.case.current_state_id,
            opened.case.current_state_ordinal,
            "RETAINED_EVIDENCE",
            "CLOSED_WITH_RETAINED_EVIDENCE",
            "close bounded review without inventing a repair path",
        )
        successor = reconciliations.transition_reconciliation_case(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="successor",
            request=successor_request,
        )
        assert reconciliations.transition_reconciliation_case(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="successor",
            request=successor_request,
        ) == successor
        assert successor.case.current_state_ordinal == 2
        assert successor.case.operational_disposition == "RETAINED_EVIDENCE"
        assert service.get_representation_metadata(ready.representation_id).disposition == "RETAINED_EVIDENCE"
        with pytest.raises(SubstrateRevisionConflict, match="not current"):
            reconciliations.transition_reconciliation_case(
                idempotency_namespace_id=idempotency_namespace,
                idempotency_key="stale-successor",
                request=ReconciliationSuccessorRequest(
                    opened.case.reconciliation_case_id,
                    opened.case.current_state_id,
                    opened.case.current_state_ordinal,
                    "WITHHELD",
                    "STALE",
                    "must not fork the historical state",
                ),
            )
        assert reconciliations.get_reconciliation_case(opened.case.reconciliation_case_id) == successor.case
        assert connection.execute(
            "SELECT count(*) FROM reconciliation_case_states WHERE reconciliation_case_id=?",
            (native_id_to_bytes(opened.case.reconciliation_case_id),),
        ).fetchone()[0] == 2
        assert connection.execute(
            "SELECT count(*) FROM reconciliation_case_states WHERE reconciliation_case_id=? AND lineage_kind='NATIVE_ORDINARY'",
            (native_id_to_bytes(opened.case.reconciliation_case_id),),
        ).fetchone()[0] == 1
    finally:
        qualified.close()


def test_h6_refuses_incomplete_current_pointer_and_h2_requires_representation_effect(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "reconciliation-invariants.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        _, _, _, ready = _ready_representation(connection, idempotency_namespace, namespace, scope)
        representation_id = native_id_to_bytes(ready.representation_id)

        operation_id, case_id, state_id = _uuid(), _uuid(), _uuid()
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
                (
                    native_id_to_bytes(operation_id),
                    native_id_to_bytes(idempotency_namespace),
                    "incomplete-current",
                    "OPEN_RECONCILIATION_CASE",
                    "TMS-INTENT-1",
                    "{}",
                ),
            )
            connection.execute(
                "INSERT INTO reconciliation_cases(reconciliation_case_id,condition_code,reason_text,subject_kind,representation_id,opened_at_ns) VALUES (?,?,?,'REPRESENTATION',?,0)",
                (native_id_to_bytes(case_id), INTEGRITY_MISMATCH_CONDITION, "incomplete", representation_id),
            )
            connection.execute(
                "INSERT INTO reconciliation_case_states VALUES (?,?,?,?,?,?,?,?,?,0)",
                (native_id_to_bytes(state_id), native_id_to_bytes(case_id), 1, "NATIVE_CREATION", None, None, "WITHHELD", None, None),
            )
            tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
            tx.reconciliation_published.append(
                (native_id_to_bytes(case_id), native_id_to_bytes(state_id), 1, None, None)
            )
            with pytest.raises(SubstrateInvariantViolation, match="H6"):
                tx.validate()
        finally:
            connection.execute("ROLLBACK")

        operation_id, transition_id, case_id, state_id = _uuid(), _uuid(), _uuid(), _uuid()
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
                (
                    native_id_to_bytes(operation_id),
                    native_id_to_bytes(idempotency_namespace),
                    "missing-representation-effect",
                    "OPEN_RECONCILIATION_CASE",
                    "TMS-INTENT-1",
                    "{}",
                ),
            )
            connection.execute(
                """
                INSERT INTO reconciliation_cases(
                    reconciliation_case_id,condition_code,reason_text,subject_kind,representation_id,
                    current_state_id,current_state_ordinal,opened_at_ns
                ) VALUES (?,?,?,'REPRESENTATION',?,?,1,0)
                """,
                (
                    native_id_to_bytes(case_id),
                    INTEGRITY_MISMATCH_CONDITION,
                    "missing representation effect",
                    representation_id,
                    native_id_to_bytes(state_id),
                ),
            )
            connection.execute(
                "INSERT INTO reconciliation_case_states VALUES (?,?,?,?,?,?,?,?,?,0)",
                (native_id_to_bytes(state_id), native_id_to_bytes(case_id), 1, "NATIVE_CREATION", None, None, "WITHHELD", None, None),
            )
            connection.execute(
                "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
                (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "RECONCILIATION_CASE_OPENED", "NATIVE"),
            )
            connection.execute(
                "INSERT INTO reconciliation_state_effects VALUES (?,?,?,1)",
                (native_id_to_bytes(transition_id), native_id_to_bytes(case_id), native_id_to_bytes(state_id)),
            )
            connection.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,reconciliation_case_id,reconciliation_state_id,reconciliation_state_ordinal) VALUES (?,?,?,'RECONCILIATION_CASE',?,?,1)",
                (native_id_to_bytes(operation_id), 0, "RECONCILIATION_CASE_OPENED", native_id_to_bytes(case_id), native_id_to_bytes(state_id)),
            )
            tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
            tx.transitions.append(native_id_to_bytes(transition_id))
            tx.reconciliation_published.append(
                (native_id_to_bytes(case_id), native_id_to_bytes(state_id), 1, representation_id, "WITHHELD")
            )
            with pytest.raises(SubstrateInvariantViolation, match="H2 reconciliation representation effect"):
                tx.validate()
        finally:
            connection.execute("ROLLBACK")
    finally:
        qualified.close()


def test_phase_7e3_keeps_h7_legacy_admission_unimplemented():
    service_methods = set(dir(NativeReconciliationService))
    assert not {"admit_legacy_representation", "admit_legacy_reconciliation", "migrate_legacy_case"} & service_methods
