"""I4B-1 native primary-write and precommit-residue coordinator.

The native substrate has an intentionally generic object lifecycle.  This
module uses that existing lifecycle rather than adding a schema table: a
``PENDING`` core object reserves an EID and is eligible for motif attachment,
but it has neither a runtime-order witness nor a representation and is not a
canonical/queryable memory.  The later ``EXISTS`` successor is the native
counterpart of legacy ``flush_node``.  If that commit fails, an ``ABORTED``
successor keeps the reserved EID and the already-persisted motif membership
without manufacturing a canonical memory.

It is deliberately a small coordination layer.  It owns no reinforcement,
motif, query, or post-write mathematics.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from typing import Any, Mapping
from uuid import UUID

from .canonical_intent import canonical_intent_text
from .compat import _allocate_eid
from .errors import (
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from .ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from .memory_motif_composition import (
    NativeMemoryMotifCompositionRequest,
    _memory_state,
    _provenance_values,
    _request_retry_contract,
)
from .memory_runtime_order import allocate_next_runtime_ordinal, publish_runtime_order
from .object_revision_governance import _insert_published_governance_for_qualification
from .objects import NativeObjectService, ObjectResult, ObjectState, SubstrateTx, execute_semantic
from .schema import require_current_schema


_PENDING = "PENDING"
_ABORTED = "ABORTED"
_CONTRACT = "P9D_I4B1_PRIMARY_PRECOMMIT_V1"
_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"


@dataclass(frozen=True)
class NativePrecommitMemoryReservation:
    """Durable noncanonical source identity available to motif composition."""

    eid: int
    memory_object_id: UUID
    memory_revision_id: UUID
    memory_revision_ordinal: int
    transition_id: UUID
    operation_id: UUID


@dataclass(frozen=True)
class NativePrecommitMemoryCommit:
    """The canonical source successor published after precommit work succeeds."""

    eid: int
    memory_object_id: UUID
    memory_revision_id: UUID
    memory_revision_ordinal: int
    transition_id: UUID
    operation_id: UUID
    provenance_id: UUID


@dataclass(frozen=True)
class NativePrecommitMemoryAbort:
    """Recovered durable noncanonical outcome for an already-failed create."""

    reservation: NativePrecommitMemoryReservation
    disposition: str
    attempt_origin: str
    reinforcement_disposition: str


class NativePrimaryPrecommitService:
    """Persist and finalize the exact I4B-1 precommit primary-memory state."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        require_current_schema(connection)
        self._connection = connection
        self._objects = NativeObjectService(connection)

    def reserve(self, request: NativeMemoryMotifCompositionRequest) -> NativePrecommitMemoryReservation:
        """Persist a noncanonical, EID-reserving spawn before motif mutation."""
        self._require_request(request)
        intent = canonical_intent_text({
            "kind": "NATIVE_PRIMARY_PRECOMMIT_RESERVE",
            "request": _request_contract(request),
        })

        def mutate(tx: SubstrateTx) -> NativePrecommitMemoryReservation:
            eid = _allocate_eid(tx, request.legacy_source_namespace_id)
            state = ObjectState(
                request.memory_identity_namespace_id,
                request.semantic_scope_id,
                _MEMORY_OBJECT_KIND,
                _PENDING,
                "PRECOMMIT",
                False,
                "DERIVED",
                "NOT_APPLICABLE",
                _reservation_payload(request, eid),
                "JSON",
                None,
            )
            source = self._objects._create(tx, state, None)
            tx.execute(
                "INSERT INTO legacy_object_aliases VALUES (?,'EID',?,?)",
                (
                    native_id_to_bytes(request.legacy_source_namespace_id),
                    str(eid),
                    native_id_to_bytes(source.object_id),
                ),
            )
            return NativePrecommitMemoryReservation(
                eid,
                source.object_id,
                source.revision_id,
                1,
                source.transition_id,
                source.operation_id,
            )

        return execute_semantic(
            self._connection,
            request.idempotency_namespace_id,
            _key(request, "RESERVE"),
            "NATIVE_PRIMARY_PRECOMMIT_RESERVE",
            intent,
            lambda operation_id: self._reservation_for_operation(operation_id, request),
            mutate,
        )

    def recover_canonical(
        self, request: NativeMemoryMotifCompositionRequest,
    ) -> NativePrecommitMemoryCommit | None:
        """Recover a completed primary commit before duplicate selection runs."""
        self._require_request(request)
        row = self._connection.execute(
            """SELECT operation_id,canonical_intent_json FROM operations
               WHERE idempotency_namespace_id=? AND idempotency_key=?""",
            (
                native_id_to_bytes(request.idempotency_namespace_id),
                _canonical_commit_key(request),
            ),
        ).fetchone()
        if row is None:
            return None
        try:
            intent = json.loads(row[1])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("completed primary commit intent is malformed") from exc
        if (
            not isinstance(intent, dict)
            or intent.get("kind") != "NATIVE_PRIMARY_CANONICAL_COMMIT"
            or intent.get("request") != _request_contract(request)
        ):
            raise SubstrateIdempotencyConflict("primary precommit idempotency intent differs")
        result = self._objects._result(row[0])
        if result is None:
            raise SubstrateInvariantViolation("completed primary commit has no object output")
        details = self._connection.execute(
            """
            SELECT a.alias_value,r.revision_ordinal,r.existence_state,r.provenance_id
            FROM legacy_object_aliases a
            JOIN objects o ON o.object_id=a.object_id
            JOIN object_revisions r
              ON r.object_id=o.object_id
             AND r.object_revision_id=o.current_revision_id
             AND r.revision_ordinal=o.current_revision_ordinal
            WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID'
              AND a.object_id=?
            """,
            (
                native_id_to_bytes(request.legacy_source_namespace_id),
                native_id_to_bytes(result.object_id),
            ),
        ).fetchone()
        if (
            details is None
            or details[2] != "EXISTS"
            or details[3] is None
            or not isinstance(details[1], int)
        ):
            raise SubstrateInvariantViolation("completed primary commit is not canonical")
        try:
            eid = int(details[0])
        except (TypeError, ValueError) as exc:
            raise SubstrateInvariantViolation("completed primary commit EID is malformed") from exc
        return NativePrecommitMemoryCommit(
            eid, result.object_id, result.revision_id, details[1],
            result.transition_id, result.operation_id, UUID(bytes=details[3]),
        )

    def commit(
        self,
        *,
        request: NativeMemoryMotifCompositionRequest,
        reservation: NativePrecommitMemoryReservation,
        enrichment_patch: Mapping[str, Any],
    ) -> NativePrecommitMemoryCommit:
        """Publish the canonical ``EXISTS`` successor and its runtime witnesses."""
        self._require_request(request)
        self._require_reservation(reservation)
        if not isinstance(enrichment_patch, Mapping):
            raise ValueError("precommit enrichment_patch must be a mapping")
        intent = canonical_intent_text({
            "kind": "NATIVE_PRIMARY_CANONICAL_COMMIT",
            "request": _request_contract(request),
            "reservation": _reservation_contract(reservation),
            "enrichment_patch": dict(enrichment_patch),
        })

        def mutate(tx: SubstrateTx) -> NativePrecommitMemoryCommit:
            self._assert_pending_current(tx, request, reservation)
            provenance_id = native_id_to_bytes(generate_native_id())
            tx.execute(
                """
                INSERT INTO provenance_records(
                    provenance_id,origin_kind,source_channel,source_role,
                    derivation_status,uncertainty_state,source_time_ns,
                    capture_time_ns,memory_role,descriptive_notes
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (provenance_id, *_provenance_values(request.provenance)),
            )
            state = _memory_state(
                request,
                UUID(bytes=provenance_id),
                dict(enrichment_patch),
            )
            source = self._objects._successor(
                tx,
                reservation.memory_object_id,
                reservation.memory_revision_id,
                state,
            )
            ordinal = reservation.memory_revision_ordinal + 1
            _insert_published_governance_for_qualification(
                tx,
                object_id=native_id_to_bytes(source.object_id),
                object_revision_id=native_id_to_bytes(source.revision_id),
                object_revision_ordinal=ordinal,
                facts=request.governance,
            )
            publish_runtime_order(
                tx,
                legacy_source_namespace_id=request.legacy_source_namespace_id,
                object_id=source.object_id,
                runtime_ordinal=allocate_next_runtime_ordinal(
                    tx, request.legacy_source_namespace_id
                ),
            )
            return NativePrecommitMemoryCommit(
                reservation.eid,
                source.object_id,
                source.revision_id,
                ordinal,
                source.transition_id,
                source.operation_id,
                UUID(bytes=provenance_id),
            )

        return execute_semantic(
            self._connection,
            request.idempotency_namespace_id,
            _canonical_commit_key(request),
            "NATIVE_PRIMARY_CANONICAL_COMMIT",
            intent,
            lambda operation_id: self._commit_for_operation(operation_id, request, reservation),
            mutate,
        )

    def recover_aborted(
        self, request: NativeMemoryMotifCompositionRequest,
    ) -> NativePrecommitMemoryAbort | None:
        """Recover a prior failed primary attempt without retrying its effects."""
        self._require_request(request)
        row = self._connection.execute(
            """SELECT operation_id,canonical_intent_json FROM operations
               WHERE idempotency_namespace_id=? AND idempotency_key=?""",
            (native_id_to_bytes(request.idempotency_namespace_id), _key(request, "RESERVE")),
        ).fetchone()
        if row is None:
            return None
        try:
            intent = json.loads(row[1])
        except (TypeError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("precommit reservation intent is malformed") from exc
        if (
            not isinstance(intent, dict)
            or intent.get("kind") != "NATIVE_PRIMARY_PRECOMMIT_RESERVE"
            or intent.get("request") != _request_contract(request)
        ):
            raise SubstrateIdempotencyConflict("primary precommit idempotency intent differs")
        reservation = self._reservation_for_operation(row[0], request)
        if reservation is None:
            raise SubstrateInvariantViolation("completed precommit reservation has no recoverable source")
        current = self._connection.execute(
            """SELECT r.existence_state,r.payload_text FROM objects o
               JOIN object_revisions r ON r.object_id=o.object_id
                 AND r.object_revision_id=o.current_revision_id
                 AND r.revision_ordinal=o.current_revision_ordinal
               WHERE o.object_id=?""",
            (native_id_to_bytes(reservation.memory_object_id),),
        ).fetchone()
        if current is None or current[0] != _ABORTED:
            return None
        try:
            payload = json.loads(current[1])
            disposition = payload["failure_disposition"]
            attempt_origin = payload["attempt_origin"]
            reinforcement_disposition = payload["reinforcement_disposition"]
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise SubstrateInvariantViolation("aborted precommit outcome is malformed") from exc
        if any(
            not isinstance(value, str) or not value
            for value in (disposition, attempt_origin, reinforcement_disposition)
        ):
            raise SubstrateInvariantViolation("aborted precommit outcome has invalid disposition")
        return NativePrecommitMemoryAbort(
            reservation, disposition, attempt_origin, reinforcement_disposition,
        )

    def abort(
        self,
        *,
        request: NativeMemoryMotifCompositionRequest,
        reservation: NativePrecommitMemoryReservation,
        disposition: str,
        attempt_origin: str,
        reinforcement_disposition: str,
        failure_stage: str | None = None,
    ) -> ObjectResult:
        """Make a failed primary intent explicit without removing precommit truth."""
        self._require_request(request)
        self._require_reservation(reservation)
        if not isinstance(disposition, str) or not disposition:
            raise ValueError("precommit abort disposition must be non-empty text")
        if not isinstance(attempt_origin, str) or not attempt_origin:
            raise ValueError("precommit abort attempt_origin must be non-empty text")
        if not isinstance(reinforcement_disposition, str) or not reinforcement_disposition:
            raise ValueError("precommit abort reinforcement_disposition must be non-empty text")
        if failure_stage is not None and (
            not isinstance(failure_stage, str) or not failure_stage
        ):
            raise ValueError("precommit abort failure_stage must be non-empty text when supplied")
        intent = canonical_intent_text({
            "kind": "NATIVE_PRIMARY_PRECOMMIT_ABORT",
            "request": _request_contract(request),
            "reservation": _reservation_contract(reservation),
            "disposition": disposition,
            "attempt_origin": attempt_origin,
            "reinforcement_disposition": reinforcement_disposition,
            "failure_stage": failure_stage,
        })

        def mutate(tx: SubstrateTx) -> ObjectResult:
            self._assert_pending_current(tx, request, reservation)
            state = ObjectState(
                request.memory_identity_namespace_id,
                request.semantic_scope_id,
                _MEMORY_OBJECT_KIND,
                _ABORTED,
                "PRECOMMIT_ABORTED",
                False,
                "DERIVED",
                "NOT_APPLICABLE",
                {
                    **_reservation_payload(request, reservation.eid),
                    "failure_disposition": disposition,
                    "attempt_origin": attempt_origin,
                    "reinforcement_disposition": reinforcement_disposition,
                    **({} if failure_stage is None else {"failure_stage": failure_stage}),
                },
                "JSON",
                None,
            )
            return self._objects._successor(
                tx,
                reservation.memory_object_id,
                reservation.memory_revision_id,
                state,
            )

        return execute_semantic(
            self._connection,
            request.idempotency_namespace_id,
            _key(request, f"ABORT:{disposition}"),
            "NATIVE_PRIMARY_PRECOMMIT_ABORT",
            intent,
            NativeObjectService(self._connection)._result,
            mutate,
        )

    def _reservation_for_operation(
        self,
        operation_id: bytes,
        request: NativeMemoryMotifCompositionRequest,
    ) -> NativePrecommitMemoryReservation | None:
        result = self._objects._result(operation_id)
        if result is None:
            return None
        row = self._connection.execute(
            """
            SELECT a.alias_value,r.revision_ordinal,r.existence_state,r.payload_text
            FROM legacy_object_aliases a
            JOIN objects o ON o.object_id=a.object_id
            JOIN object_revisions r
              ON r.object_id=o.object_id
             AND r.object_revision_id=?
            WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID'
              AND a.object_id=?
            """,
            (
                native_id_to_bytes(result.revision_id),
                native_id_to_bytes(request.legacy_source_namespace_id),
                native_id_to_bytes(result.object_id),
            ),
        ).fetchone()
        if row is None:
            return None
        marker = _marker(row[3])
        if marker.get("contract") != _CONTRACT:
            return None
        try:
            eid = int(row[0])
        except (TypeError, ValueError):
            return None
        if eid != marker.get("reserved_eid") or not isinstance(row[1], int):
            return None
        return NativePrecommitMemoryReservation(
            eid, result.object_id, result.revision_id, row[1], result.transition_id, result.operation_id
        )

    def _commit_for_operation(
        self,
        operation_id: bytes,
        request: NativeMemoryMotifCompositionRequest,
        reservation: NativePrecommitMemoryReservation,
    ) -> NativePrecommitMemoryCommit | None:
        result = self._objects._result(operation_id)
        if result is None:
            return None
        row = self._connection.execute(
            """
            SELECT r.revision_ordinal,r.existence_state,r.provenance_id
            FROM objects o JOIN object_revisions r
              ON r.object_id=o.object_id
             AND r.object_revision_id=o.current_revision_id
             AND r.revision_ordinal=o.current_revision_ordinal
            WHERE o.object_id=?
            """,
            (native_id_to_bytes(result.object_id),),
        ).fetchone()
        if (
            row is None
            or result.object_id != reservation.memory_object_id
            or row[1] != "EXISTS"
            or row[2] is None
            or not isinstance(row[0], int)
        ):
            return None
        return NativePrecommitMemoryCommit(
            reservation.eid, result.object_id, result.revision_id, row[0],
            result.transition_id, result.operation_id, UUID(bytes=row[2]),
        )

    def _assert_pending_current(
        self,
        tx: SubstrateTx,
        request: NativeMemoryMotifCompositionRequest,
        reservation: NativePrecommitMemoryReservation,
    ) -> None:
        row = tx.execute(
            """
            SELECT o.object_kind,r.object_revision_id,r.revision_ordinal,r.existence_state,
                   r.effective_semantic_scope_id,r.payload_text
            FROM objects o JOIN object_revisions r
              ON r.object_id=o.object_id
             AND r.object_revision_id=o.current_revision_id
             AND r.revision_ordinal=o.current_revision_ordinal
            WHERE o.object_id=?
            """,
            (native_id_to_bytes(reservation.memory_object_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("precommit memory reservation was not found")
        if (
            row[0] != _MEMORY_OBJECT_KIND
            or row[1] != native_id_to_bytes(reservation.memory_revision_id)
            or row[2] != reservation.memory_revision_ordinal
            or row[3] != _PENDING
            or row[4] != native_id_to_bytes(request.semantic_scope_id)
        ):
            raise SubstrateRevisionConflict("precommit memory reservation is no longer pending")
        marker = _marker(row[5])
        if (
            marker.get("contract") != _CONTRACT
            or marker.get("reserved_eid") != reservation.eid
            or marker.get("request_key") != request.idempotency_key
        ):
            raise SubstrateInvariantViolation("precommit memory reservation marker differs")

    @staticmethod
    def _require_request(request: NativeMemoryMotifCompositionRequest) -> None:
        if not isinstance(request, NativeMemoryMotifCompositionRequest):
            raise ValueError("native precommit requires a composition request")

    @staticmethod
    def _require_reservation(reservation: NativePrecommitMemoryReservation) -> None:
        if not isinstance(reservation, NativePrecommitMemoryReservation):
            raise ValueError("native precommit requires a reservation")


def _key(request: NativeMemoryMotifCompositionRequest, phase: str) -> str:
    return f"I4B1:{phase}:{request.idempotency_key}"


def _canonical_commit_key(request: NativeMemoryMotifCompositionRequest) -> str:
    """Keep I4B-1's canonical revision under the qualified source owner.

    The pending reservation and abort remain I4B-1 evidence operations.  The
    successful ``EXISTS`` successor, however, is the same canonical memory
    operation consumed by the established native-public/post-write route.
    I4B-1 must therefore not introduce a second owning operation for it.
    """
    # ``_new_memory_composition_request`` has already translated the public
    # route key into ``NATIVE_FABRIC_NEW_MEMORY:SOURCE:<route-key>``.  Prefixing
    # it again would create an unowned sibling operation instead of restoring
    # the established source owner.
    return request.idempotency_key


def _request_contract(request: NativeMemoryMotifCompositionRequest) -> dict[str, Any]:
    """The stable facts whose changed retry must never repurpose a reservation."""
    return {
        "request_key": request.idempotency_key,
        # Keep this reservation exactly as strict as A3C2's source retry
        # contract.  The precommit split must never make a changed payload,
        # provenance, governance fact, symbol input, or geometry claim reuse
        # an earlier pending identity.
        "semantic_inputs": _request_retry_contract(request),
    }


def _reservation_contract(reservation: NativePrecommitMemoryReservation) -> dict[str, Any]:
    return {
        "eid": reservation.eid,
        "memory_object_id": str(reservation.memory_object_id),
        "memory_revision_id": str(reservation.memory_revision_id),
        "memory_revision_ordinal": reservation.memory_revision_ordinal,
    }


def _reservation_payload(request: NativeMemoryMotifCompositionRequest, eid: int) -> dict[str, Any]:
    return {
        "native_precommit": {
            "contract": _CONTRACT,
            "reserved_eid": eid,
            "request_key": request.idempotency_key,
            "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
        }
    }


def _marker(payload_text: Any) -> Mapping[str, Any]:
    try:
        payload = json.loads(payload_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise SubstrateInvariantViolation("precommit memory payload is malformed") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("native_precommit"), dict):
        raise SubstrateInvariantViolation("precommit memory payload has no marker")
    return payload["native_precommit"]


__all__ = [
    "NativePrecommitMemoryAbort",
    "NativePrecommitMemoryCommit",
    "NativePrecommitMemoryReservation",
    "NativePrimaryPrecommitService",
]
