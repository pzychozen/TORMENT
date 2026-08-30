"""Qualification-only proof for provenance and governance as revision children.

This is not a Fabric writer or a general memory-mutation API.  It proves that
one native object operation can recover an immutable provenance child from its
published memory R1 without a standalone provenance transition/output family.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import sqlite3
from uuid import UUID

from .canonical_intent import canonical_intent_text
from .errors import SubstrateInvariantViolation
from .ids import generate_native_id, native_id_to_bytes
from .object_revision_governance import (
    NativeMemoryGovernanceFacts,
    _insert_published_governance_for_qualification,
)
from .objects import ObjectState, NativeObjectService, SubstrateTx, execute_semantic
from .schema import require_current_schema


@dataclass(frozen=True)
class NativeProvenanceRecord:
    """Exact existing provenance-row fields for closed-child qualification."""

    origin_kind: str
    source_channel: str | None
    source_role: str | None
    derivation_status: str
    uncertainty_state: str
    source_time_ns: int | None = None
    capture_time_ns: int | None = None
    memory_role: str | None = None
    descriptive_notes: str | None = None


@dataclass(frozen=True)
class ClosedChildMemoryResult:
    """The memory output plus the exact immutable provenance child it references."""

    object_id: UUID
    revision_id: UUID
    revision_ordinal: int
    transition_id: UUID
    operation_id: UUID
    provenance_id: UUID


class NativeClosedChildQualificationService:
    """Narrow foundation that proves closed-child provenance and governance."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        require_current_schema(connection)
        self._connection = connection
        self._objects = NativeObjectService(connection)

    def create_memory_with_closed_children(
        self,
        *,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        state: ObjectState,
        provenance: NativeProvenanceRecord,
        governance: NativeMemoryGovernanceFacts,
        _test_fail_after_provenance: bool = False,
    ) -> ClosedChildMemoryResult:
        """Create provenance + R1 + governance under the single memory operation.

        ``_test_fail_after_provenance`` is an intentionally private rollback
        seam; it has no production caller and no durable semantic meaning.
        """
        _validate_request(idempotency_namespace_id, idempotency_key, state, provenance, governance)
        intent = _intent(state, provenance, governance)

        def mutate(tx: SubstrateTx) -> ClosedChildMemoryResult:
            provenance_id = native_id_to_bytes(generate_native_id())
            tx.execute(
                """
                INSERT INTO provenance_records(
                    provenance_id,origin_kind,source_channel,source_role,
                    derivation_status,uncertainty_state,source_time_ns,
                    capture_time_ns,memory_role,descriptive_notes
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (provenance_id, *_provenance_values(provenance)),
            )
            if _test_fail_after_provenance:
                raise RuntimeError("forced closed-child qualification rollback")
            result = self._objects._create(
                tx,
                replace(state, provenance_id=UUID(bytes=provenance_id)),
                None,
            )
            _insert_published_governance_for_qualification(
                tx,
                object_id=native_id_to_bytes(result.object_id),
                object_revision_id=native_id_to_bytes(result.revision_id),
                object_revision_ordinal=1,
                facts=governance,
            )
            return ClosedChildMemoryResult(
                result.object_id,
                result.revision_id,
                1,
                result.transition_id,
                result.operation_id,
                UUID(bytes=provenance_id),
            )

        return execute_semantic(
            self._connection,
            idempotency_namespace_id,
            idempotency_key,
            "QUALIFICATION_MEMORY_CLOSED_CHILDREN",
            intent,
            self._result_for_operation,
            mutate,
        )

    def _result_for_operation(self, operation_id: bytes) -> ClosedChildMemoryResult | None:
        row = self._connection.execute(
            """
            SELECT o.object_id,o.object_revision_id,o.object_revision_ordinal,
                   t.transition_id,t.operation_id,r.provenance_id
            FROM operation_outputs o
            JOIN semantic_transitions t ON t.operation_id=o.operation_id
            JOIN object_revisions r
              ON r.object_id=o.object_id
             AND r.object_revision_id=o.object_revision_id
             AND r.revision_ordinal=o.object_revision_ordinal
            WHERE o.operation_id=? AND o.output_kind='OBJECT' AND o.output_role='OBJECT'
            """,
            (operation_id,),
        ).fetchall()
        if not row:
            return None
        if len(row) != 1 or row[0][5] is None:
            raise SubstrateInvariantViolation("closed-child memory result is incomplete")
        value = row[0]
        provenance = self._connection.execute(
            "SELECT 1 FROM provenance_records WHERE provenance_id=?", (value[5],)
        ).fetchone()
        if provenance is None:
            raise SubstrateInvariantViolation("memory revision references missing provenance")
        return ClosedChildMemoryResult(
            UUID(bytes=value[0]),
            UUID(bytes=value[1]),
            value[2],
            UUID(bytes=value[3]),
            UUID(bytes=value[4]),
            UUID(bytes=value[5]),
        )


def _intent(
    state: ObjectState,
    provenance: NativeProvenanceRecord,
    governance: NativeMemoryGovernanceFacts,
) -> str:
    return canonical_intent_text(
        {
            "kind": "QUALIFICATION_MEMORY_CLOSED_CHILDREN",
            "object_state": {
                "identity_namespace_id": str(state.identity_namespace_id),
                "semantic_scope_id": str(state.semantic_scope_id),
                "object_kind": state.object_kind,
                "existence_state": state.existence_state,
                "lifecycle_state": state.lifecycle_state,
                "lifecycle_authoritative": state.lifecycle_authoritative,
                "governance_state": state.governance_state,
                "authority_category": state.authority_category,
                "payload": state.payload,
                "payload_format": state.payload_format,
            },
            "provenance": {
                "origin_kind": provenance.origin_kind,
                "source_channel": provenance.source_channel,
                "source_role": provenance.source_role,
                "derivation_status": provenance.derivation_status,
                "uncertainty_state": provenance.uncertainty_state,
                "source_time_ns": provenance.source_time_ns,
                "capture_time_ns": provenance.capture_time_ns,
                "memory_role": provenance.memory_role,
                "descriptive_notes": provenance.descriptive_notes,
            },
            "governance": {
                "protected": governance.protected,
                "non_shareable": governance.non_shareable,
                "collective_export_blocked": governance.collective_export_blocked,
                "collective_reingest_blocked": governance.collective_reingest_blocked,
                "decay_accelerated": governance.decay_accelerated,
            },
        }
    )


def _validate_request(
    idempotency_namespace_id: UUID,
    idempotency_key: str,
    state: ObjectState,
    provenance: NativeProvenanceRecord,
    governance: NativeMemoryGovernanceFacts,
) -> None:
    if not isinstance(idempotency_namespace_id, UUID):
        raise ValueError("idempotency_namespace_id must be a UUID")
    if not isinstance(idempotency_key, str) or not idempotency_key:
        raise ValueError("idempotency_key must be a non-empty string")
    if not isinstance(state, ObjectState):
        raise ValueError("object state is required")
    if state.object_kind != "LEGACY_CORE_NODE":
        raise ValueError("closed-child qualification is limited to ordinary native memories")
    if state.authority_category != "NOT_APPLICABLE":
        raise ValueError("ordinary memory qualification cannot grant authority")
    if state.provenance_id is not None:
        raise ValueError("closed-child qualification allocates its exact provenance child")
    if not isinstance(provenance, NativeProvenanceRecord):
        raise ValueError("native provenance record is required")
    if not isinstance(provenance.origin_kind, str) or not provenance.origin_kind:
        raise ValueError("provenance origin_kind must be a non-empty string")
    if not isinstance(provenance.derivation_status, str) or not provenance.derivation_status:
        raise ValueError("provenance derivation_status must be a non-empty string")
    if not isinstance(provenance.uncertainty_state, str) or not provenance.uncertainty_state:
        raise ValueError("provenance uncertainty_state must be a non-empty string")
    for value in (
        provenance.source_channel,
        provenance.source_role,
        provenance.memory_role,
        provenance.descriptive_notes,
    ):
        if value is not None and not isinstance(value, str):
            raise ValueError("optional provenance text must be a string")
    for value in (provenance.source_time_ns, provenance.capture_time_ns):
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            raise ValueError("optional provenance timestamps must be integers")
    governance.as_storage_tuple()


def _provenance_values(provenance: NativeProvenanceRecord) -> tuple[object, ...]:
    return (
        provenance.origin_kind,
        provenance.source_channel,
        provenance.source_role,
        provenance.derivation_status,
        provenance.uncertainty_state,
        provenance.source_time_ns,
        provenance.capture_time_ns,
        provenance.memory_role,
        provenance.descriptive_notes,
    )


__all__ = [
    "ClosedChildMemoryResult",
    "NativeClosedChildQualificationService",
    "NativeProvenanceRecord",
]
