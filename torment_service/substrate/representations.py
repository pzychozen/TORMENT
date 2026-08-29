"""Native representation readiness, later integrity verification, and facts.

This module deliberately stops before legacy admission, embedding generation,
and caller wiring.  Reconciliation case lineage is owned by the separate
``reconciliation`` module; this boundary owns representation state and its
append-only integrity evidence.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import sqlite3
import time
from uuid import UUID

from .canonical_intent import canonical_intent_text
from .errors import (
    SubstrateIntegrityMismatch,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from .ids import generate_native_id, native_id_to_bytes
from .objects import SubstrateTx, execute_semantic
from .schema import open_schema


INTEGRITY_ALGORITHM_SHA256 = "SHA256"
INTEGRITY_VALUE_ENCODING_RAW = "RAW"


@dataclass(frozen=True)
class RepresentationRequest:
    """Immutable identity and source facts for a PENDING representation."""

    source_kind: str
    object_id: UUID | None
    object_revision_id: UUID | None
    relationship_id: UUID | None
    relationship_revision_id: UUID | None
    representation_class: str
    generation: int
    derivation_contract_version: str
    encoding_id: str
    dtype: str | None = None
    dimension: int | None = None
    dependencies: tuple[UUID, ...] = ()
    representation_id: UUID | None = None
    expected_payload_byte_length: int | None = None


@dataclass(frozen=True)
class RepresentationIntegrityExpectationRequest:
    """One pre-payload, immutable SHA-256 expectation for a representation."""

    representation_id: UUID
    algorithm_id: str
    expected_value: bytes
    value_encoding: str


@dataclass(frozen=True)
class RepresentationIntegrityExpectation:
    expectation_id: UUID
    representation_id: UUID
    algorithm_id: str
    expected_value: bytes
    value_encoding: str


@dataclass(frozen=True)
class RepresentationReadyRequest:
    """Payload and derivation identity required to publish an expected result."""

    representation_id: UUID
    representation_class: str
    generation: int
    derivation_contract_version: str
    encoding_id: str
    payload_bytes: bytes


@dataclass(frozen=True)
class RepresentationFailureRequest:
    """An explicit durable failure; failed READY attempts do not create this."""

    representation_id: UUID
    failure_code: str
    failure_reason: str | None = None


@dataclass(frozen=True)
class RepresentationIntegrityVerificationRequest:
    """Request a new append-only measurement of an already READY payload."""

    representation_id: UUID
    reason: str | None = None


@dataclass(frozen=True)
class RepresentationIntegrityVerification:
    representation_id: UUID
    measurement_id: UUID
    result: str
    transition_id: UUID
    operation_id: UUID


@dataclass(frozen=True)
class RepresentationMetadata:
    representation_id: UUID
    source_kind: str
    representation_class: str
    generation: int
    readiness: str
    disposition: str
    dependencies: tuple[UUID, ...]
    integrity_expectation_id: UUID | None = None
    selected_measurement_id: UUID | None = None
    active_reconciliation_case_id: UUID | None = None
    active_reconciliation_state_id: UUID | None = None


class NativeRepresentationService:
    """The native representation boundary; all writes use ``SubstrateTx``."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection

    def create_representation_pending(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request: RepresentationRequest,
    ) -> RepresentationMetadata:
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "CREATE_REPRESENTATION_PENDING",
            self._pending_intent(request),
            self._pending_result,
            lambda tx: self._create_pending(tx, request),
        )

    def establish_representation_integrity_expectation(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request: RepresentationIntegrityExpectationRequest,
    ) -> RepresentationIntegrityExpectation:
        """Persist the one immutable expectation before any payload is accepted."""
        self._validate_expectation_request(request)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "ESTABLISH_REPRESENTATION_INTEGRITY_EXPECTATION",
            self._expectation_intent(request),
            lambda operation_id: self._expectation_result(operation_id, request.representation_id),
            lambda tx: self._establish_expectation(tx, request),
        )

    def publish_representation_ready(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request: RepresentationReadyRequest,
    ) -> RepresentationMetadata:
        """Publish payload and matching integrity measurement atomically as READY."""
        self._validate_ready_request(request)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "PUBLISH_REPRESENTATION_READY",
            self._ready_intent(request),
            self._ready_result,
            lambda tx: self._publish_ready(tx, request),
        )

    def mark_representation_ready(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request: RepresentationReadyRequest,
    ) -> RepresentationMetadata:
        """Compatibility spelling for the explicit READY-publication operation."""
        return self.publish_representation_ready(
            idempotency_namespace_id=idempotency_namespace_id,
            idempotency_key=idempotency_key,
            request=request,
        )

    def fail_representation(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request: RepresentationFailureRequest,
    ) -> RepresentationMetadata:
        """Durably mark one PENDING representation failed without publishing bytes."""
        self._validate_failure_request(request)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "FAIL_REPRESENTATION",
            self._failure_intent(request),
            self._failure_result,
            lambda tx: self._fail(tx, request),
        )

    def verify_published_representation_integrity(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        request: RepresentationIntegrityVerificationRequest,
    ) -> RepresentationIntegrityVerification:
        """Append a fresh measurement and withhold use on a later mismatch.

        This reads the durable payload inside the semantic transaction; ordinary
        callers still only obtain payload bytes through the explicit usable read.
        """
        self._validate_verification_request(request)
        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "VERIFY_PUBLISHED_REPRESENTATION_INTEGRITY",
            self._verification_intent(request),
            self._verification_result,
            lambda tx: self._verify_published_integrity(tx, request),
        )

    def get_representation_metadata(self, representation_id: UUID) -> RepresentationMetadata:
        """Read identity/state metadata only; payload bytes are never selected here."""
        row = self._connection.execute(
            """
            SELECT r.representation_id,r.source_kind,r.representation_class,r.generation,
                   s.readiness,s.operational_disposition,s.selected_integrity_measurement_id
            FROM representations r
            JOIN representation_current_state s USING(representation_id)
            WHERE r.representation_id=?
            """,
            (_blob(representation_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("representation was not found")
        dependencies = tuple(
            UUID(bytes=dependency_row[0])
            for dependency_row in self._connection.execute(
                """
                SELECT dependency_representation_id
                FROM representation_dependencies
                WHERE representation_id=?
                ORDER BY dependency_representation_id
                """,
                (row[0],),
            )
        )
        expectation_rows = self._connection.execute(
            "SELECT expectation_id FROM integrity_expectations WHERE subject_kind='REPRESENTATION' AND representation_id=?",
            (row[0],),
        ).fetchall()
        if len(expectation_rows) > 1:
            raise SubstrateInvariantViolation("representation has multiple integrity expectations")
        reconciliation_rows = self._connection.execute(
            """
            SELECT current_state_id,current_state_ordinal
            FROM reconciliation_cases
            WHERE subject_kind='REPRESENTATION' AND representation_id=?
            ORDER BY opened_at_ns DESC,reconciliation_case_id DESC
            """,
            (row[0],),
        ).fetchall()
        if len(reconciliation_rows) > 1:
            raise SubstrateInvariantViolation("representation has multiple active reconciliation cases")
        active_case_id = None
        active_state_id = None
        if reconciliation_rows:
            active_case = self._connection.execute(
                """
                SELECT reconciliation_case_id,current_state_id
                FROM reconciliation_cases
                WHERE subject_kind='REPRESENTATION' AND representation_id=?
                """,
                (row[0],),
            ).fetchone()
            if active_case is None or active_case[1] is None:
                raise SubstrateInvariantViolation("reconciliation case has no current state")
            active_case_id = UUID(bytes=active_case[0])
            active_state_id = UUID(bytes=active_case[1])
        return RepresentationMetadata(
            representation_id=UUID(bytes=row[0]),
            source_kind=row[1],
            representation_class=row[2],
            generation=row[3],
            readiness=row[4],
            disposition=row[5],
            dependencies=dependencies,
            integrity_expectation_id=UUID(bytes=expectation_rows[0][0]) if expectation_rows else None,
            selected_measurement_id=UUID(bytes=row[6]) if row[6] is not None else None,
            active_reconciliation_case_id=active_case_id,
            active_reconciliation_state_id=active_state_id,
        )

    def get_representation_integrity_expectation(
        self, representation_id: UUID
    ) -> RepresentationIntegrityExpectation:
        rows = self._connection.execute(
            """
            SELECT expectation_id,representation_id,algorithm_id,expected_value,value_encoding
            FROM integrity_expectations
            WHERE subject_kind='REPRESENTATION' AND representation_id=?
            """,
            (_blob(representation_id),),
        ).fetchall()
        if not rows:
            raise SubstrateObjectNotFound("representation integrity expectation was not found")
        if len(rows) != 1:
            raise SubstrateInvariantViolation("representation has multiple integrity expectations")
        row = rows[0]
        return RepresentationIntegrityExpectation(
            expectation_id=UUID(bytes=row[0]),
            representation_id=UUID(bytes=row[1]),
            algorithm_id=row[2],
            expected_value=row[3],
            value_encoding=row[4],
        )

    def read_representation_payload(self, representation_id: UUID) -> bytes:
        """Explicitly load bytes from one published and usable representation."""
        row = self._connection.execute(
            """
            SELECT p.payload_bytes
            FROM representation_payloads p
            JOIN representation_current_state s USING(representation_id)
            WHERE p.representation_id=?
              AND s.readiness='READY'
              AND s.operational_disposition='USABLE'
            """,
            (_blob(representation_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("usable representation payload was not found")
        return row[0]

    def _create_pending(
        self, tx: SubstrateTx, request: RepresentationRequest
    ) -> RepresentationMetadata:
        representation_id = _blob(request.representation_id) if request.representation_id else _new()
        self._validate_pending_request(request, tx, representation_id)
        if request.source_kind == "OBJECT_REVISION":
            tx.execute(
                """
                INSERT INTO representations(
                    representation_id,source_kind,source_object_id,source_object_revision_id,
                    source_object_revision_ordinal,representation_class,generation,
                    derivation_contract_version,encoding_id,dtype,dimension,
                    expected_payload_byte_length,created_at_ns
                )
                SELECT ?,'OBJECT_REVISION',object_id,object_revision_id,revision_ordinal,
                       ?,?,?,?,?,?,?,0
                FROM object_revisions
                WHERE object_id=? AND object_revision_id=?
                """,
                (
                    representation_id,
                    request.representation_class,
                    request.generation,
                    request.derivation_contract_version,
                    request.encoding_id,
                    request.dtype,
                    request.dimension,
                    request.expected_payload_byte_length,
                    _blob(request.object_id),
                    _blob(request.object_revision_id),
                ),
            )
        else:
            tx.execute(
                """
                INSERT INTO representations(
                    representation_id,source_kind,source_relationship_id,
                    source_relationship_revision_id,source_relationship_revision_ordinal,
                    representation_class,generation,derivation_contract_version,encoding_id,
                    dtype,dimension,expected_payload_byte_length,created_at_ns
                )
                SELECT ?,'RELATIONSHIP_REVISION',relationship_id,relationship_revision_id,
                       revision_ordinal,?,?,?,?,?,?,?,0
                FROM relationship_revisions
                WHERE relationship_id=? AND relationship_revision_id=?
                """,
                (
                    representation_id,
                    request.representation_class,
                    request.generation,
                    request.derivation_contract_version,
                    request.encoding_id,
                    request.dtype,
                    request.dimension,
                    request.expected_payload_byte_length,
                    _blob(request.relationship_id),
                    _blob(request.relationship_revision_id),
                ),
            )
        if tx.execute(
            "SELECT 1 FROM representations WHERE representation_id=?", (representation_id,)
        ).fetchone() is None:
            raise SubstrateRevisionConflict("exact representation source does not exist")
        for dependency_id in request.dependencies:
            tx.execute(
                "INSERT INTO representation_dependencies VALUES (?,?,?)",
                (representation_id, _blob(dependency_id), "DECLARED"),
            )
        tx.execute(
            "INSERT INTO representation_current_state VALUES (?,'PENDING','WITHHELD',NULL)",
            (representation_id,),
        )
        transition_id = _new()
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (transition_id, tx.operation_id, "REPRESENTATION_PENDING", "NATIVE"),
        )
        tx.execute(
            "INSERT INTO representation_state_effects VALUES (?,?,?, ?,NULL)",
            (transition_id, representation_id, "PENDING", "WITHHELD"),
        )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,representation_id
            ) VALUES (?,?,?,?,?)
            """,
            (tx.operation_id, 0, "REPRESENTATION_PENDING", "REPRESENTATION", representation_id),
        )
        tx.transitions.append(transition_id)
        tx.representation_published.append(representation_id)
        return self.get_representation_metadata(UUID(bytes=representation_id))

    def _establish_expectation(
        self, tx: SubstrateTx, request: RepresentationIntegrityExpectationRequest
    ) -> RepresentationIntegrityExpectation:
        representation_id = _blob(request.representation_id)
        state = tx.execute(
            "SELECT readiness,operational_disposition FROM representation_current_state WHERE representation_id=?",
            (representation_id,),
        ).fetchone()
        if state is None:
            raise SubstrateObjectNotFound("representation was not found")
        if state != ("PENDING", "WITHHELD"):
            raise SubstrateRevisionConflict("integrity expectation requires a pending representation")
        if tx.execute(
            "SELECT 1 FROM representation_payloads WHERE representation_id=?", (representation_id,)
        ).fetchone() is not None:
            raise SubstrateInvariantViolation("integrity expectation must precede payload publication")
        if tx.execute(
            "SELECT 1 FROM integrity_expectations WHERE subject_kind='REPRESENTATION' AND representation_id=?",
            (representation_id,),
        ).fetchone() is not None:
            raise SubstrateRevisionConflict("representation integrity expectation already exists")
        expectation_id = _new()
        tx.execute(
            """
            INSERT INTO integrity_expectations(
                expectation_id,subject_kind,representation_id,algorithm_id,expected_value,
                value_encoding,established_at_ns
            ) VALUES (?,'REPRESENTATION',?,?,?,?,?)
            """,
            (
                expectation_id,
                representation_id,
                request.algorithm_id,
                request.expected_value,
                request.value_encoding,
                time.time_ns(),
            ),
        )
        return self.get_representation_integrity_expectation(request.representation_id)

    def _publish_ready(
        self, tx: SubstrateTx, request: RepresentationReadyRequest
    ) -> RepresentationMetadata:
        representation_id = _blob(request.representation_id)
        row = tx.execute(
            """
            SELECT r.representation_class,r.generation,r.derivation_contract_version,
                   r.encoding_id,r.expected_payload_byte_length,s.readiness,
                   s.operational_disposition
            FROM representations r
            JOIN representation_current_state s USING(representation_id)
            WHERE r.representation_id=?
            """,
            (representation_id,),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("representation was not found")
        if row[5:] != ("PENDING", "WITHHELD"):
            raise SubstrateRevisionConflict("representation is not pending publication")
        if row[:4] != (
            request.representation_class,
            request.generation,
            request.derivation_contract_version,
            request.encoding_id,
        ):
            raise SubstrateRevisionConflict("representation generation or contract is incompatible")
        if row[4] is not None and row[4] != len(request.payload_bytes):
            raise ValueError("payload length differs from the pre-established expectation")
        expectation = self._expectation_for_representation(tx, representation_id)
        observed_value = _measure_payload(
            request.payload_bytes, expectation.algorithm_id, expectation.value_encoding
        )
        if observed_value != expectation.expected_value:
            raise SubstrateIntegrityMismatch("payload does not match the pre-established integrity expectation")
        if tx.execute(
            """
            SELECT 1
            FROM representation_dependencies d
            JOIN representation_current_state s
              ON s.representation_id=d.dependency_representation_id
            WHERE d.representation_id=?
              AND (s.readiness!='READY' OR s.operational_disposition!='USABLE')
            """,
            (representation_id,),
        ).fetchone() is not None:
            raise SubstrateRevisionConflict("representation dependencies are not ready")
        measurement_id, transition_id = _new(), _new()
        now_ns = time.time_ns()
        tx.execute(
            "INSERT INTO representation_payloads VALUES (?,?,?,?)",
            (representation_id, request.payload_bytes, len(request.payload_bytes), now_ns),
        )
        tx.execute(
            "INSERT INTO integrity_measurements VALUES (?,?,?,?,?,?)",
            (
                measurement_id,
                _blob(expectation.expectation_id),
                "MATCH",
                observed_value,
                None,
                now_ns,
            ),
        )
        tx.execute(
            """
            UPDATE representation_current_state
            SET readiness='READY',operational_disposition='USABLE',
                selected_integrity_measurement_id=?
            WHERE representation_id=?
            """,
            (measurement_id, representation_id),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "REPRESENTATION_READY", "NATIVE", now_ns),
        )
        tx.execute(
            "INSERT INTO representation_state_effects VALUES (?,?,?,?,?)",
            (transition_id, representation_id, "READY", "USABLE", measurement_id),
        )
        tx.execute(
            "INSERT INTO integrity_measurement_effects VALUES (?,?)",
            (transition_id, measurement_id),
        )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,representation_id
            ) VALUES (?,?,?,?,?)
            """,
            (tx.operation_id, 0, "REPRESENTATION_READY", "REPRESENTATION", representation_id),
        )
        tx.transitions.append(transition_id)
        tx.representation_ready.append(
            (representation_id, _blob(expectation.expectation_id), measurement_id)
        )
        return self.get_representation_metadata(request.representation_id)

    def _fail(self, tx: SubstrateTx, request: RepresentationFailureRequest) -> RepresentationMetadata:
        representation_id = _blob(request.representation_id)
        state = tx.execute(
            "SELECT readiness,operational_disposition FROM representation_current_state WHERE representation_id=?",
            (representation_id,),
        ).fetchone()
        if state is None:
            raise SubstrateObjectNotFound("representation was not found")
        if state != ("PENDING", "WITHHELD"):
            raise SubstrateRevisionConflict("only a pending representation can be failed")
        if tx.execute(
            "SELECT 1 FROM representation_payloads WHERE representation_id=?", (representation_id,)
        ).fetchone() is not None:
            raise SubstrateInvariantViolation("a failed representation cannot publish a payload")
        transition_id = _new()
        now_ns = time.time_ns()
        tx.execute(
            """
            UPDATE representation_current_state
            SET readiness='FAILED',operational_disposition='WITHHELD',
                selected_integrity_measurement_id=NULL
            WHERE representation_id=?
            """,
            (representation_id,),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "REPRESENTATION_FAILED", "NATIVE", now_ns),
        )
        tx.execute(
            "INSERT INTO representation_state_effects VALUES (?,?,?, ?,NULL)",
            (transition_id, representation_id, "FAILED", "WITHHELD"),
        )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,representation_id
            ) VALUES (?,?,?,?,?)
            """,
            (tx.operation_id, 0, "REPRESENTATION_FAILED", "REPRESENTATION", representation_id),
        )
        tx.transitions.append(transition_id)
        tx.representation_failed.append((representation_id, None))
        return self.get_representation_metadata(request.representation_id)

    def _verify_published_integrity(
        self, tx: SubstrateTx, request: RepresentationIntegrityVerificationRequest
    ) -> RepresentationIntegrityVerification:
        representation_id = _blob(request.representation_id)
        state = tx.execute(
            "SELECT readiness,operational_disposition FROM representation_current_state WHERE representation_id=?",
            (representation_id,),
        ).fetchone()
        if state is None:
            raise SubstrateObjectNotFound("representation was not found")
        if state[0] != "READY":
            raise SubstrateRevisionConflict("later integrity verification requires a ready representation")
        payload = tx.execute(
            """
            SELECT p.payload_bytes,p.observed_payload_byte_length,r.expected_payload_byte_length
            FROM representation_payloads p
            JOIN representations r USING(representation_id)
            WHERE p.representation_id=?
            """,
            (representation_id,),
        ).fetchone()
        if payload is None or payload[1] != len(payload[0]) or (
            payload[2] is not None and payload[2] != payload[1]
        ):
            raise SubstrateInvariantViolation("published representation payload is not exact")
        expectation = self._expectation_for_representation(tx, representation_id)
        observed_value = _measure_payload(
            payload[0], expectation.algorithm_id, expectation.value_encoding
        )
        result = "MATCH" if observed_value == expectation.expected_value else "MISMATCH"
        disposition = state[1] if result == "MATCH" else "RECONCILIATION_REQUIRED"
        measurement_id, transition_id = _new(), _new()
        now_ns = time.time_ns()
        tx.execute(
            "INSERT INTO integrity_measurements VALUES (?,?,?,?,?,?)",
            (
                measurement_id,
                _blob(expectation.expectation_id),
                result,
                observed_value,
                request.reason,
                now_ns,
            ),
        )
        tx.execute(
            """
            UPDATE representation_current_state
            SET operational_disposition=?,selected_integrity_measurement_id=?
            WHERE representation_id=?
            """,
            (disposition, measurement_id, representation_id),
        )
        tx.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,?)",
            (transition_id, tx.operation_id, "REPRESENTATION_INTEGRITY_VERIFIED", "NATIVE", now_ns),
        )
        tx.execute(
            "INSERT INTO representation_state_effects VALUES (?,?,?,?,?)",
            (transition_id, representation_id, "READY", disposition, measurement_id),
        )
        tx.execute(
            "INSERT INTO integrity_measurement_effects VALUES (?,?)",
            (transition_id, measurement_id),
        )
        tx.execute(
            """
            INSERT INTO operation_outputs(
                operation_id,output_ordinal,output_role,output_kind,representation_id
            ) VALUES (?,?,?,?,?)
            """,
            (
                tx.operation_id,
                0,
                "REPRESENTATION_INTEGRITY_VERIFIED",
                "REPRESENTATION",
                representation_id,
            ),
        )
        tx.transitions.append(transition_id)
        tx.representation_published.append(representation_id)
        tx.representation_verified.append(
            (
                representation_id,
                _blob(expectation.expectation_id),
                measurement_id,
                result,
                disposition,
            )
        )
        return RepresentationIntegrityVerification(
            request.representation_id,
            UUID(bytes=measurement_id),
            result,
            UUID(bytes=transition_id),
            UUID(bytes=tx.operation_id),
        )

    def _expectation_for_representation(
        self, tx: SubstrateTx, representation_id: bytes
    ) -> RepresentationIntegrityExpectation:
        rows = tx.execute(
            """
            SELECT expectation_id,representation_id,algorithm_id,expected_value,value_encoding
            FROM integrity_expectations
            WHERE subject_kind='REPRESENTATION' AND representation_id=?
            """,
            (representation_id,),
        ).fetchall()
        if not rows:
            raise SubstrateRevisionConflict("ready publication requires a pre-established integrity expectation")
        if len(rows) != 1:
            raise SubstrateInvariantViolation("representation has multiple integrity expectations")
        row = rows[0]
        return RepresentationIntegrityExpectation(
            expectation_id=UUID(bytes=row[0]),
            representation_id=UUID(bytes=row[1]),
            algorithm_id=row[2],
            expected_value=row[3],
            value_encoding=row[4],
        )

    def _validate_pending_request(
        self, request: RepresentationRequest, tx: SubstrateTx, representation_id: bytes
    ) -> None:
        if request.source_kind not in {"OBJECT_REVISION", "RELATIONSHIP_REVISION"}:
            raise ValueError("invalid representation source kind")
        _validate_positive_int(request.generation, "representation generation")
        if request.dimension is not None:
            _validate_positive_int(request.dimension, "representation dimension")
        if request.expected_payload_byte_length is not None and (
            not isinstance(request.expected_payload_byte_length, int)
            or isinstance(request.expected_payload_byte_length, bool)
            or request.expected_payload_byte_length < 0
        ):
            raise ValueError("expected payload byte length must be non-negative when supplied")
        if not _nonempty_strings(
            request.representation_class,
            request.derivation_contract_version,
            request.encoding_id,
        ):
            raise ValueError("representation identity fields must be non-empty strings")
        if request.source_kind == "OBJECT_REVISION" and (
            request.object_id is None
            or request.object_revision_id is None
            or request.relationship_id is not None
            or request.relationship_revision_id is not None
        ):
            raise ValueError("invalid object representation source shape")
        if request.source_kind == "RELATIONSHIP_REVISION" and (
            request.relationship_id is None
            or request.relationship_revision_id is None
            or request.object_id is not None
            or request.object_revision_id is not None
        ):
            raise ValueError("invalid relationship representation source shape")
        if len(set(request.dependencies)) != len(request.dependencies):
            raise ValueError("duplicate representation dependency")
        for dependency_id in request.dependencies:
            if _blob(dependency_id) == representation_id:
                raise ValueError("representation cannot depend on itself")
            if tx.execute(
                "SELECT 1 FROM representations WHERE representation_id=?", (_blob(dependency_id),)
            ).fetchone() is None:
                raise SubstrateObjectNotFound("dependency representation was not found")

    @staticmethod
    def _validate_expectation_request(request: RepresentationIntegrityExpectationRequest) -> None:
        if not _nonempty_strings(request.algorithm_id, request.value_encoding):
            raise ValueError("integrity algorithm and value encoding must be non-empty strings")
        if type(request.expected_value) is not bytes:
            raise ValueError("integrity expectation must be immutable bytes")
        _validate_integrity_shape(request.algorithm_id, request.expected_value, request.value_encoding)

    @staticmethod
    def _validate_ready_request(request: RepresentationReadyRequest) -> None:
        _validate_positive_int(request.generation, "representation generation")
        if not _nonempty_strings(
            request.representation_class,
            request.derivation_contract_version,
            request.encoding_id,
        ):
            raise ValueError("ready publication fields must be non-empty strings")
        if type(request.payload_bytes) is not bytes:
            raise ValueError("representation payload must be immutable bytes")

    @staticmethod
    def _validate_failure_request(request: RepresentationFailureRequest) -> None:
        if not _nonempty_strings(request.failure_code):
            raise ValueError("representation failure code must be a non-empty string")
        if request.failure_reason is not None and not isinstance(request.failure_reason, str):
            raise ValueError("representation failure reason must be a string when supplied")

    @staticmethod
    def _validate_verification_request(
        request: RepresentationIntegrityVerificationRequest,
    ) -> None:
        if request.reason is not None and not isinstance(request.reason, str):
            raise ValueError("integrity verification reason must be a string when supplied")

    @staticmethod
    def _pending_intent(request: RepresentationRequest) -> str:
        return canonical_intent_text(
            {
                "kind": "PENDING_REPRESENTATION",
                "representation_id": str(request.representation_id) if request.representation_id else None,
                "source_kind": request.source_kind,
                "object_id": str(request.object_id) if request.object_id else None,
                "object_revision_id": str(request.object_revision_id) if request.object_revision_id else None,
                "relationship_id": str(request.relationship_id) if request.relationship_id else None,
                "relationship_revision_id": str(request.relationship_revision_id) if request.relationship_revision_id else None,
                "class": request.representation_class,
                "generation": request.generation,
                "contract": request.derivation_contract_version,
                "encoding": request.encoding_id,
                "dtype": request.dtype,
                "dimension": request.dimension,
                "dependencies": [str(dependency_id) for dependency_id in request.dependencies],
                "expected_payload_byte_length": request.expected_payload_byte_length,
            }
        )

    @staticmethod
    def _expectation_intent(request: RepresentationIntegrityExpectationRequest) -> str:
        return canonical_intent_text(
            {
                "kind": "REPRESENTATION_INTEGRITY_EXPECTATION",
                "representation_id": str(request.representation_id),
                "algorithm_id": request.algorithm_id,
                "expected_value": _encode_bytes(request.expected_value),
                "value_encoding": request.value_encoding,
            }
        )

    @staticmethod
    def _ready_intent(request: RepresentationReadyRequest) -> str:
        return canonical_intent_text(
            {
                "kind": "READY_REPRESENTATION",
                "representation_id": str(request.representation_id),
                "class": request.representation_class,
                "generation": request.generation,
                "contract": request.derivation_contract_version,
                "encoding": request.encoding_id,
                "payload_bytes": _encode_bytes(request.payload_bytes),
            }
        )

    @staticmethod
    def _failure_intent(request: RepresentationFailureRequest) -> str:
        return canonical_intent_text(
            {
                "kind": "FAILED_REPRESENTATION",
                "representation_id": str(request.representation_id),
                "failure_code": request.failure_code,
                "failure_reason": request.failure_reason,
            }
        )

    @staticmethod
    def _verification_intent(request: RepresentationIntegrityVerificationRequest) -> str:
        return canonical_intent_text(
            {
                "kind": "VERIFY_PUBLISHED_REPRESENTATION_INTEGRITY",
                "representation_id": str(request.representation_id),
                "reason": request.reason,
            }
        )

    def _pending_result(self, operation_id: bytes) -> RepresentationMetadata | None:
        row = self._connection.execute(
            """
            SELECT representation_id FROM operation_outputs
            WHERE operation_id=? AND output_kind='REPRESENTATION'
              AND output_role='REPRESENTATION_PENDING'
            """,
            (operation_id,),
        ).fetchone()
        return self.get_representation_metadata(UUID(bytes=row[0])) if row else None

    def _expectation_result(
        self, operation_id: bytes, representation_id: UUID
    ) -> RepresentationIntegrityExpectation | None:
        if self._connection.execute(
            "SELECT 1 FROM operations WHERE operation_id=?", (operation_id,)
        ).fetchone() is None:
            return None
        try:
            return self.get_representation_integrity_expectation(representation_id)
        except SubstrateObjectNotFound:
            return None

    def _ready_result(self, operation_id: bytes) -> RepresentationMetadata | None:
        row = self._connection.execute(
            """
            SELECT o.representation_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN representation_state_effects e ON e.transition_id=t.transition_id
            WHERE o.operation_id=? AND o.output_kind='REPRESENTATION'
              AND o.output_role='REPRESENTATION_READY'
              AND e.representation_id=o.representation_id AND e.readiness='READY'
            """,
            (operation_id,),
        ).fetchone()
        return self.get_representation_metadata(UUID(bytes=row[0])) if row else None

    def _failure_result(self, operation_id: bytes) -> RepresentationMetadata | None:
        row = self._connection.execute(
            """
            SELECT o.representation_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN representation_state_effects e ON e.transition_id=t.transition_id
            WHERE o.operation_id=? AND o.output_kind='REPRESENTATION'
              AND o.output_role='REPRESENTATION_FAILED'
              AND e.representation_id=o.representation_id AND e.readiness='FAILED'
            """,
            (operation_id,),
        ).fetchone()
        return self.get_representation_metadata(UUID(bytes=row[0])) if row else None

    def _verification_result(
        self, operation_id: bytes
    ) -> RepresentationIntegrityVerification | None:
        row = self._connection.execute(
            """
            SELECT o.representation_id,m.measurement_id,m.result,t.transition_id,t.operation_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN representation_state_effects s ON s.transition_id=t.transition_id
            JOIN integrity_measurement_effects e ON e.transition_id=t.transition_id
            JOIN integrity_measurements m ON m.measurement_id=e.measurement_id
            WHERE o.operation_id=? AND o.output_kind='REPRESENTATION'
              AND o.output_role='REPRESENTATION_INTEGRITY_VERIFIED'
              AND s.representation_id=o.representation_id
              AND s.selected_measurement_id=m.measurement_id
            """,
            (operation_id,),
        ).fetchone()
        return (
            RepresentationIntegrityVerification(
                UUID(bytes=row[0]), UUID(bytes=row[1]), row[2], UUID(bytes=row[3]), UUID(bytes=row[4])
            )
            if row
            else None
        )


def _measure_payload(payload_bytes: bytes, algorithm_id: str, value_encoding: str) -> bytes:
    _validate_integrity_shape(algorithm_id, b"\0" * hashlib.sha256().digest_size, value_encoding)
    return hashlib.sha256(payload_bytes).digest()


def _validate_integrity_shape(algorithm_id: str, value: bytes, value_encoding: str) -> None:
    if (algorithm_id, value_encoding) != (INTEGRITY_ALGORITHM_SHA256, INTEGRITY_VALUE_ENCODING_RAW):
        raise ValueError("only SHA256/RAW representation integrity is qualified in Phase 7E2")
    if len(value) != hashlib.sha256().digest_size:
        raise ValueError("SHA256/RAW integrity values must be exactly 32 bytes")


def _validate_positive_int(value: object, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _nonempty_strings(*values: object) -> bool:
    return all(isinstance(value, str) and value for value in values)


def _blob(value: UUID) -> bytes:
    return native_id_to_bytes(value)


def _new() -> bytes:
    return native_id_to_bytes(generate_native_id())


def _encode_bytes(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")
