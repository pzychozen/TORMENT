"""Phase 7E3 native reconciliation lineage for representation integrity failures.

The service is deliberately narrow: a case has a typed representation subject,
an immutable linear state lineage, and one selected current state.  It does not
admit legacy data, perform migration, or attach the substrate to live callers.
"""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
import time
from uuid import UUID

from .canonical_intent import canonical_intent_text
from .errors import (
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from .ids import generate_native_id, native_id_to_bytes
from .objects import SubstrateTx, execute_semantic
from .schema import open_schema


INTEGRITY_MISMATCH_CONDITION = "REPRESENTATION_INTEGRITY_MISMATCH"
_NONUSABLE_DISPOSITIONS = frozenset(
    {"WITHHELD", "RECONCILIATION_REQUIRED", "QUARANTINED", "RETAINED_EVIDENCE"}
)
_ALL_DISPOSITIONS = _NONUSABLE_DISPOSITIONS | {"USABLE"}


@dataclass(frozen=True)
class ReconciliationCaseRequest:
    """Open a case for the currently selected mismatching representation evidence."""

    representation_id: UUID
    condition_code: str
    reason_text: str
    operational_disposition: str = "WITHHELD"
    determination: str | None = None


@dataclass(frozen=True)
class ReconciliationSuccessorRequest:
    """Advance exactly the current state of one native reconciliation case."""

    reconciliation_case_id: UUID
    expected_state_id: UUID
    expected_state_ordinal: int
    operational_disposition: str
    determination: str
    resolution_reason: str


@dataclass(frozen=True)
class ReconciliationCaseView:
    reconciliation_case_id: UUID
    representation_id: UUID
    condition_code: str
    reason_text: str
    current_state_id: UUID
    current_state_ordinal: int
    operational_disposition: str
    determination: str | None
    resolution_reason: str | None


@dataclass(frozen=True)
class ReconciliationOperationResult:
    case: ReconciliationCaseView
    transition_id: UUID
    operation_id: UUID


class NativeReconciliationService:
    """Native-only reconciliation mutations, all in one ``SubstrateTx``."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def open_reconciliation_case(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request: ReconciliationCaseRequest,
    ) -> ReconciliationOperationResult:
        self._validate_open_request(request)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "OPEN_RECONCILIATION_CASE",
            self._open_intent(request),
            self._operation_result,
            lambda tx: self._open(tx, request),
        )

    def transition_reconciliation_case(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request: ReconciliationSuccessorRequest,
    ) -> ReconciliationOperationResult:
        self._validate_successor_request(request)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "TRANSITION_RECONCILIATION_CASE",
            self._successor_intent(request),
            self._operation_result,
            lambda tx: self._successor(tx, request),
        )

    def get_reconciliation_case(self, reconciliation_case_id: UUID) -> ReconciliationCaseView:
        row = self._connection.execute(
            """
            SELECT c.reconciliation_case_id,c.representation_id,c.condition_code,c.reason_text,
                   c.current_state_id,c.current_state_ordinal,s.operational_disposition,
                   s.determination,s.resolution_reason
            FROM reconciliation_cases c
            JOIN reconciliation_case_states s
              ON s.reconciliation_case_id=c.reconciliation_case_id
             AND s.reconciliation_state_id=c.current_state_id
             AND s.state_ordinal=c.current_state_ordinal
            WHERE c.reconciliation_case_id=? AND c.subject_kind='REPRESENTATION'
            """,
            (_blob(reconciliation_case_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("native reconciliation case was not found")
        return _case_view(row)

    def _open(self, tx: SubstrateTx, request: ReconciliationCaseRequest) -> ReconciliationOperationResult:
        representation_id = _blob(request.representation_id)
        state = tx.execute(
            """
            SELECT s.readiness,s.operational_disposition,s.selected_integrity_measurement_id,m.result
            FROM representation_current_state s
            LEFT JOIN integrity_measurements m ON m.measurement_id=s.selected_integrity_measurement_id
            WHERE s.representation_id=?
            """,
            (representation_id,),
        ).fetchone()
        if state is None:
            raise SubstrateObjectNotFound("representation was not found")
        if state[0] != "READY" or state[2] is None or state[3] != "MISMATCH":
            raise SubstrateRevisionConflict("reconciliation case requires selected mismatch evidence")
        if tx.execute(
            """
            SELECT 1 FROM reconciliation_cases
            WHERE subject_kind='REPRESENTATION' AND representation_id=?
            """,
            (representation_id,),
        ).fetchone() is not None:
            raise SubstrateRevisionConflict("representation already has a reconciliation case")

        case_id, state_id, transition_id = _new(), _new(), _new()
        now_ns = time.time_ns()
        tx.execute(
            """
            INSERT INTO reconciliation_cases(
                reconciliation_case_id,condition_code,reason_text,subject_kind,representation_id,
                current_state_id,current_state_ordinal,opened_at_ns
            ) VALUES (?,?,?,'REPRESENTATION',?,?,?,?)
            """,
            (case_id, request.condition_code, request.reason_text, representation_id, state_id, 1, now_ns),
        )
        tx.execute(
            """
            INSERT INTO reconciliation_case_states(
                reconciliation_state_id,reconciliation_case_id,state_ordinal,lineage_kind,
                predecessor_state_id,predecessor_state_ordinal,operational_disposition,
                determination,resolution_reason,created_at_ns
            ) VALUES (?, ?, 1, 'NATIVE_CREATION', NULL, NULL, ?, ?, NULL, ?)
            """,
            (state_id, case_id, request.operational_disposition, request.determination, now_ns),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "RECONCILIATION_CASE_OPENED", "NATIVE", now_ns),
        )
        tx.execute(
            "INSERT INTO reconciliation_state_effects VALUES (?,?,?,?)",
            (transition_id, case_id, state_id, 1),
        )
        changed_disposition = state[1] != request.operational_disposition
        if changed_disposition:
            tx.execute(
                "UPDATE representation_current_state SET operational_disposition=? WHERE representation_id=?",
                (request.operational_disposition, representation_id),
            )
            tx.execute(
                "INSERT INTO representation_state_effects VALUES (?,?,?,?,?)",
                (
                    transition_id,
                    representation_id,
                    "READY",
                    request.operational_disposition,
                    state[2],
                ),
            )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,reconciliation_case_id,
                reconciliation_state_id,reconciliation_state_ordinal
            ) VALUES (?,?,?,'RECONCILIATION_CASE',?,?,?)
            """,
            (tx.operation_id, 0, "RECONCILIATION_CASE_OPENED", case_id, state_id, 1),
        )
        tx.transitions.append(transition_id)
        tx.reconciliation_published.append(
            (
                case_id,
                state_id,
                1,
                representation_id if changed_disposition else None,
                request.operational_disposition if changed_disposition else None,
            )
        )
        result = self._operation_result(tx.operation_id)
        if result is None:
            raise SubstrateInvariantViolation("reconciliation output was not durably published")
        return result

    def _successor(
        self, tx: SubstrateTx, request: ReconciliationSuccessorRequest
    ) -> ReconciliationOperationResult:
        case_id = _blob(request.reconciliation_case_id)
        expected_state_id = _blob(request.expected_state_id)
        row = tx.execute(
            """
            SELECT c.representation_id,c.current_state_id,c.current_state_ordinal,
                   s.operational_disposition,r.readiness,r.selected_integrity_measurement_id,m.result
            FROM reconciliation_cases c
            JOIN reconciliation_case_states s
              ON s.reconciliation_case_id=c.reconciliation_case_id
             AND s.reconciliation_state_id=c.current_state_id
             AND s.state_ordinal=c.current_state_ordinal
            JOIN representation_current_state r ON r.representation_id=c.representation_id
            LEFT JOIN integrity_measurements m ON m.measurement_id=r.selected_integrity_measurement_id
            WHERE c.reconciliation_case_id=? AND c.subject_kind='REPRESENTATION'
            """,
            (case_id,),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("native reconciliation case was not found")
        representation_id, current_state_id, current_ordinal = row[:3]
        if (current_state_id, current_ordinal) != (
            expected_state_id,
            request.expected_state_ordinal,
        ):
            raise SubstrateRevisionConflict("expected reconciliation state is not current")
        if request.operational_disposition == "USABLE" and (
            row[4] != "READY" or row[6] != "MATCH"
        ):
            raise SubstrateRevisionConflict("usable reconciliation resolution requires current MATCH evidence")
        next_state_id, transition_id = _new(), _new()
        next_ordinal = current_ordinal + 1
        now_ns = time.time_ns()
        tx.execute(
            """
            INSERT INTO reconciliation_case_states(
                reconciliation_state_id,reconciliation_case_id,state_ordinal,lineage_kind,
                predecessor_state_id,predecessor_state_ordinal,operational_disposition,
                determination,resolution_reason,created_at_ns
            ) VALUES (?, ?, ?, 'NATIVE_ORDINARY', ?, ?, ?, ?, ?, ?)
            """,
            (
                next_state_id,
                case_id,
                next_ordinal,
                current_state_id,
                current_ordinal,
                request.operational_disposition,
                request.determination,
                request.resolution_reason,
                now_ns,
            ),
        )
        tx.execute(
            """
            UPDATE reconciliation_cases
            SET current_state_id=?,current_state_ordinal=?
            WHERE reconciliation_case_id=?
            """,
            (next_state_id, next_ordinal, case_id),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "RECONCILIATION_CASE_SUCCESSOR", "NATIVE", now_ns),
        )
        tx.execute(
            "INSERT INTO reconciliation_state_effects VALUES (?,?,?,?)",
            (transition_id, case_id, next_state_id, next_ordinal),
        )
        changed_disposition = row[3] != request.operational_disposition
        if changed_disposition:
            tx.execute(
                "UPDATE representation_current_state SET operational_disposition=? WHERE representation_id=?",
                (request.operational_disposition, representation_id),
            )
            tx.execute(
                "INSERT INTO representation_state_effects VALUES (?,?,?,?,?)",
                (
                    transition_id,
                    representation_id,
                    row[4],
                    request.operational_disposition,
                    row[5],
                ),
            )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,reconciliation_case_id,
                reconciliation_state_id,reconciliation_state_ordinal
            ) VALUES (?,?,?,'RECONCILIATION_CASE',?,?,?)
            """,
            (
                tx.operation_id,
                0,
                "RECONCILIATION_CASE_SUCCESSOR",
                case_id,
                next_state_id,
                next_ordinal,
            ),
        )
        tx.transitions.append(transition_id)
        tx.reconciliation_published.append(
            (
                case_id,
                next_state_id,
                next_ordinal,
                representation_id if changed_disposition else None,
                request.operational_disposition if changed_disposition else None,
            )
        )
        result = self._operation_result(tx.operation_id)
        if result is None:
            raise SubstrateInvariantViolation("reconciliation output was not durably published")
        return result

    @staticmethod
    def _validate_open_request(request: ReconciliationCaseRequest) -> None:
        if request.condition_code != INTEGRITY_MISMATCH_CONDITION:
            raise ValueError("only representation integrity mismatch reconciliation is native in Phase 7E3")
        if not _nonempty(request.condition_code, request.reason_text):
            raise ValueError("reconciliation condition and reason must be non-empty strings")
        if request.operational_disposition not in _NONUSABLE_DISPOSITIONS:
            raise ValueError("a new mismatch reconciliation case must be non-usable")
        if request.determination is not None and not isinstance(request.determination, str):
            raise ValueError("reconciliation determination must be a string when supplied")

    @staticmethod
    def _validate_successor_request(request: ReconciliationSuccessorRequest) -> None:
        if not isinstance(request.expected_state_ordinal, int) or isinstance(
            request.expected_state_ordinal, bool
        ) or request.expected_state_ordinal < 1:
            raise ValueError("expected reconciliation state ordinal must be positive")
        if request.operational_disposition not in _ALL_DISPOSITIONS:
            raise ValueError("invalid reconciliation operational disposition")
        if not _nonempty(request.determination, request.resolution_reason):
            raise ValueError("reconciliation determination and resolution reason must be non-empty strings")

    @staticmethod
    def _open_intent(request: ReconciliationCaseRequest) -> str:
        return canonical_intent_text(
            {
                "kind": "OPEN_RECONCILIATION_CASE",
                "representation_id": str(request.representation_id),
                "condition_code": request.condition_code,
                "reason_text": request.reason_text,
                "operational_disposition": request.operational_disposition,
                "determination": request.determination,
            }
        )

    @staticmethod
    def _successor_intent(request: ReconciliationSuccessorRequest) -> str:
        return canonical_intent_text(
            {
                "kind": "TRANSITION_RECONCILIATION_CASE",
                "reconciliation_case_id": str(request.reconciliation_case_id),
                "expected_state_id": str(request.expected_state_id),
                "expected_state_ordinal": request.expected_state_ordinal,
                "operational_disposition": request.operational_disposition,
                "determination": request.determination,
                "resolution_reason": request.resolution_reason,
            }
        )

    def _operation_result(self, operation_id: bytes) -> ReconciliationOperationResult | None:
        row = self._connection.execute(
            """
            SELECT c.reconciliation_case_id,c.representation_id,c.condition_code,c.reason_text,
                   s.reconciliation_state_id,s.state_ordinal,s.operational_disposition,
                   s.determination,s.resolution_reason,t.transition_id,t.operation_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN reconciliation_state_effects e ON e.transition_id=t.transition_id
            JOIN reconciliation_cases c ON c.reconciliation_case_id=e.reconciliation_case_id
            JOIN reconciliation_case_states s
              ON s.reconciliation_case_id=e.reconciliation_case_id
             AND s.reconciliation_state_id=e.reconciliation_state_id
             AND s.state_ordinal=e.reconciliation_state_ordinal
            WHERE o.operation_id=? AND o.output_kind='RECONCILIATION_CASE'
              AND o.reconciliation_case_id=e.reconciliation_case_id
              AND o.reconciliation_state_id=e.reconciliation_state_id
              AND o.reconciliation_state_ordinal=e.reconciliation_state_ordinal
            """,
            (operation_id,),
        ).fetchone()
        if row is None:
            return None
        case = ReconciliationCaseView(
            reconciliation_case_id=UUID(bytes=row[0]),
            representation_id=UUID(bytes=row[1]),
            condition_code=row[2],
            reason_text=row[3],
            current_state_id=UUID(bytes=row[4]),
            current_state_ordinal=row[5],
            operational_disposition=row[6],
            determination=row[7],
            resolution_reason=row[8],
        )
        return ReconciliationOperationResult(case, UUID(bytes=row[9]), UUID(bytes=row[10]))


def _nonempty(*values: object) -> bool:
    return all(isinstance(value, str) and value for value in values)


def _blob(value: UUID) -> bytes:
    return native_id_to_bytes(value)


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())


def _case_view(row: tuple[object, ...]) -> ReconciliationCaseView:
    return ReconciliationCaseView(
        reconciliation_case_id=UUID(bytes=row[0]),
        representation_id=UUID(bytes=row[1]),
        condition_code=row[2],
        reason_text=row[3],
        current_state_id=UUID(bytes=row[4]),
        current_state_ordinal=row[5],
        operational_disposition=row[6],
        determination=row[7],
        resolution_reason=row[8],
    )
