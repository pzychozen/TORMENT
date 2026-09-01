"""Shared read-only qualification for the native COMPAT_EMBEDDING lane.

The reader deliberately separates current selection from a known historical
representation read.  A3B geometry uses the former; A3C3 continuity needs the
latter after its source successor has made the old revision historical.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import sqlite3
from typing import Protocol
from uuid import UUID

import numpy as np

from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from .ids import native_id_to_bytes
from .schema import open_schema


MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
COMPAT_EMBEDDING_REPRESENTATION_CLASS = "COMPAT_EMBEDDING"
COMPAT_EMBEDDING_GENERATION = 1
COMPAT_EMBEDDING_DERIVATION_CONTRACT = "compat-embedding-v1"
COMPAT_EMBEDDING_ENCODING = "RAW_VECTOR"
COMPAT_EMBEDDING_DTYPE = "float32"


class _PayloadReader(Protocol):
    def read_representation_payload(self, representation_id: UUID) -> bytes: ...


class _UsablePayloadReader:
    """Small payload boundary used when no caller provides one."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def read_representation_payload(self, representation_id: UUID) -> bytes:
        row = self._connection.execute(
            """
            SELECT p.payload_bytes
            FROM representation_payloads p
            JOIN representation_current_state state USING(representation_id)
            WHERE p.representation_id=?
              AND state.readiness='READY'
              AND state.operational_disposition='USABLE'
            """,
            (native_id_to_bytes(representation_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("usable representation payload was not found")
        return row[0]


@dataclass(frozen=True)
class QualifiedCompatEmbedding:
    """The exact qualified representation lane and its byte witness."""

    representation_id: UUID
    source_object_id: UUID
    source_revision_id: UUID
    source_revision_ordinal: int
    representation_class: str
    generation: int
    derivation_contract_version: str
    encoding_id: str
    dtype: str
    dimension: int
    expected_payload_byte_length: int
    dependencies: tuple[UUID, ...]
    expectation_id: UUID
    selected_measurement_id: UUID
    readiness: str
    disposition: str
    payload_byte_length: int
    payload_sha256: str
    payload_bytes: bytes

    def intent(self) -> dict[str, object]:
        return {
            "representation_id": str(self.representation_id),
            "source_object_id": str(self.source_object_id),
            "source_revision_id": str(self.source_revision_id),
            "source_revision_ordinal": self.source_revision_ordinal,
            "representation_class": self.representation_class,
            "generation": self.generation,
            "derivation_contract_version": self.derivation_contract_version,
            "encoding_id": self.encoding_id,
            "dtype": self.dtype,
            "dimension": self.dimension,
            "expected_payload_byte_length": self.expected_payload_byte_length,
            "dependencies": [str(item) for item in self.dependencies],
            "expectation_id": str(self.expectation_id),
            "selected_measurement_id": str(self.selected_measurement_id),
            "readiness": self.readiness,
            "disposition": self.disposition,
            "payload_byte_length": self.payload_byte_length,
            "payload_sha256": self.payload_sha256,
        }

    @classmethod
    def from_intent(cls, value: dict[str, object], payload_bytes: bytes) -> "QualifiedCompatEmbedding":
        try:
            result = cls(
                representation_id=UUID(str(value["representation_id"])),
                source_object_id=UUID(str(value["source_object_id"])),
                source_revision_id=UUID(str(value["source_revision_id"])),
                source_revision_ordinal=int(value["source_revision_ordinal"]),
                representation_class=str(value["representation_class"]),
                generation=int(value["generation"]),
                derivation_contract_version=str(value["derivation_contract_version"]),
                encoding_id=str(value["encoding_id"]),
                dtype=str(value["dtype"]),
                dimension=int(value["dimension"]),
                expected_payload_byte_length=int(value["expected_payload_byte_length"]),
                dependencies=tuple(UUID(str(item)) for item in value["dependencies"]),  # type: ignore[arg-type]
                expectation_id=UUID(str(value["expectation_id"])),
                selected_measurement_id=UUID(str(value["selected_measurement_id"])),
                readiness=str(value["readiness"]),
                disposition=str(value["disposition"]),
                payload_byte_length=int(value["payload_byte_length"]),
                payload_sha256=str(value["payload_sha256"]),
                payload_bytes=payload_bytes,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SubstrateInvariantViolation("stored qualified embedding witness is malformed") from exc
        return result

    def float32_vector(self) -> np.ndarray:
        return _validate_payload(self, self.payload_bytes)


@dataclass(frozen=True)
class CurrentCompatEmbeddingWitness:
    """Immutable selected-row facts for a batched currentness recheck.

    The expectation, measurement, representation metadata, and payload bytes
    are immutable after qualified READY publication.  A hot read therefore
    proves their stable IDs and current operational state without reloading or
    rehashing the immutable payload bytes for every selected result.
    """

    eid: int
    source_object_id: UUID
    source_revision_id: UUID
    source_revision_ordinal: int
    representation_id: UUID
    expectation_id: UUID
    selected_measurement_id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.eid, int) or isinstance(self.eid, bool) or self.eid < 0:
            raise ValueError("embedding witness EID must be a non-negative integer")
        for value in (
            self.source_object_id,
            self.source_revision_id,
            self.representation_id,
            self.expectation_id,
            self.selected_measurement_id,
        ):
            _require_uuid("embedding witness identity", value)
        if (
            not isinstance(self.source_revision_ordinal, int)
            or isinstance(self.source_revision_ordinal, bool)
            or self.source_revision_ordinal < 1
        ):
            raise ValueError("embedding witness revision ordinal must be positive")


class NativeCompatEmbeddingReader:
    """Read exact qualified embeddings without allocation or mutation."""

    def __init__(self, connection: sqlite3.Connection, *, payload_reader: _PayloadReader | None = None) -> None:
        open_schema(connection, writable=False)
        self._connection = connection
        self._payload_reader = payload_reader or _UsablePayloadReader(connection)

    def read_current(
        self, object_id: UUID, *, expected_dimension: int
    ) -> QualifiedCompatEmbedding | None:
        """Select one current qualified vector or return ``None`` when absent."""
        _require_uuid("object_id", object_id)
        _positive_dimension(expected_dimension)
        current = self._connection.execute(
            "SELECT object_kind,current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
            (native_id_to_bytes(object_id),),
        ).fetchone()
        if current is None:
            raise SubstrateObjectNotFound("native embedding source object was not found")
        if current[0] != MEMORY_OBJECT_KIND:
            raise SubstrateInvariantViolation("qualified embedding source must be a LEGACY_CORE_NODE")
        return self._read_exact(
            object_id,
            UUID(bytes=current[1]),
            current[2],
            expected_dimension=expected_dimension,
            expected_representation_id=None,
            absent_is_none=True,
        )

    def read_historical(self, witness: QualifiedCompatEmbedding) -> QualifiedCompatEmbedding:
        """Revalidate and read a known old representation without currentness."""
        if not isinstance(witness, QualifiedCompatEmbedding):
            raise ValueError("a QualifiedCompatEmbedding witness is required")
        result = self._read_exact(
            witness.source_object_id,
            witness.source_revision_id,
            witness.source_revision_ordinal,
            expected_dimension=witness.dimension,
            expected_representation_id=witness.representation_id,
            absent_is_none=False,
        )
        if result is None or result.intent() != witness.intent():
            raise SubstrateInvariantViolation("known historical embedding no longer matches its durable witness")
        return result

    def validate_current_witnesses(
        self,
        *,
        legacy_source_namespace_id: UUID,
        identity_namespace_id: UUID,
        semantic_scope_id: UUID,
        witnesses: tuple[CurrentCompatEmbeddingWitness, ...],
    ) -> bool:
        """Batch-prove selected current rows without loading payload bytes.

        The query binds every requested EID, source revision, representation,
        expectation, and selected measurement.  It also requires the current
        ``representation_current_state`` to remain ``READY``/``USABLE`` with
        a ``MATCH`` measurement.  Reconciliation failures publish the same
        non-usable current disposition, so that direct current-state witness
        is the bounded proof that no non-usable reconciliation state remains.
        """
        _require_uuid("legacy_source_namespace_id", legacy_source_namespace_id)
        _require_uuid("identity_namespace_id", identity_namespace_id)
        _require_uuid("semantic_scope_id", semantic_scope_id)
        if not isinstance(witnesses, tuple):
            raise ValueError("embedding witnesses must be a tuple")
        if not witnesses:
            return True
        if len({item.eid for item in witnesses}) != len(witnesses):
            raise ValueError("embedding witnesses must have unique EIDs")
        if not all(isinstance(item, CurrentCompatEmbeddingWitness) for item in witnesses):
            raise ValueError("embedding witnesses must be CurrentCompatEmbeddingWitness values")

        values_sql = ",".join("(?,?,?,?,?,?,?,?)" for _ in witnesses)
        parameters: list[object] = []
        for ordinal, witness in enumerate(witnesses):
            parameters.extend((
                ordinal,
                witness.eid,
                native_id_to_bytes(witness.source_object_id),
                native_id_to_bytes(witness.source_revision_id),
                witness.source_revision_ordinal,
                native_id_to_bytes(witness.representation_id),
                native_id_to_bytes(witness.expectation_id),
                native_id_to_bytes(witness.selected_measurement_id),
            ))
        rows = self._connection.execute(
            f"""
            WITH requested(
                row_ordinal,eid,object_id,object_revision_id,
                revision_ordinal,representation_id,expectation_id,measurement_id
            ) AS MATERIALIZED (VALUES {values_sql})
            SELECT requested.row_ordinal
              FROM requested
              CROSS JOIN legacy_object_aliases alias
              JOIN objects object ON object.object_id=requested.object_id
              JOIN object_revisions source
                ON source.object_id=object.object_id
               AND source.object_revision_id=requested.object_revision_id
               AND source.revision_ordinal=requested.revision_ordinal
               AND object.current_revision_id=source.object_revision_id
               AND object.current_revision_ordinal=source.revision_ordinal
              JOIN representations representation
                ON representation.representation_id=requested.representation_id
               AND representation.source_kind='OBJECT_REVISION'
               AND representation.source_object_id=object.object_id
               AND representation.source_object_revision_id=source.object_revision_id
               AND representation.source_object_revision_ordinal=source.revision_ordinal
              JOIN integrity_expectations expectation
                ON expectation.expectation_id=requested.expectation_id
               AND expectation.subject_kind='REPRESENTATION'
               AND expectation.representation_id=representation.representation_id
              JOIN representation_current_state state
                ON state.representation_id=representation.representation_id
               AND state.selected_integrity_measurement_id=requested.measurement_id
              JOIN integrity_measurements measurement
                ON measurement.measurement_id=state.selected_integrity_measurement_id
               AND measurement.expectation_id=expectation.expectation_id
             WHERE alias.legacy_source_namespace_id=?
               AND alias.alias_kind='EID'
               AND alias.alias_value=CAST(requested.eid AS TEXT)
               AND alias.object_id=requested.object_id
               AND object.object_kind=?
               AND object.identity_namespace_id=?
               AND source.effective_semantic_scope_id=?
               AND state.readiness='READY'
               AND state.operational_disposition='USABLE'
               AND measurement.result='MATCH'
             ORDER BY requested.row_ordinal
            """,
            tuple(parameters) + (
                native_id_to_bytes(legacy_source_namespace_id),
                MEMORY_OBJECT_KIND,
                native_id_to_bytes(identity_namespace_id),
                native_id_to_bytes(semantic_scope_id),
            ),
        ).fetchall()
        return len(rows) == len(witnesses) and tuple(row[0] for row in rows) == tuple(range(len(witnesses)))

    def _read_exact(
        self,
        object_id: UUID,
        revision_id: UUID,
        revision_ordinal: int,
        *,
        expected_dimension: int,
        expected_representation_id: UUID | None,
        absent_is_none: bool,
    ) -> QualifiedCompatEmbedding | None:
        parameters: list[object] = [
            native_id_to_bytes(object_id),
            native_id_to_bytes(revision_id),
            revision_ordinal,
            COMPAT_EMBEDDING_REPRESENTATION_CLASS,
            COMPAT_EMBEDDING_GENERATION,
            COMPAT_EMBEDDING_DERIVATION_CONTRACT,
            COMPAT_EMBEDDING_ENCODING,
            COMPAT_EMBEDDING_DTYPE,
            expected_dimension,
        ]
        expected_blob = native_id_to_bytes(expected_representation_id) if expected_representation_id is not None else None
        parameters.extend((expected_blob, expected_blob))
        rows = self._connection.execute(
            """
            SELECT r.representation_id,r.source_object_id,r.source_object_revision_id,
                   r.source_object_revision_ordinal,r.representation_class,r.generation,
                   r.derivation_contract_version,r.encoding_id,r.dtype,r.dimension,
                   r.expected_payload_byte_length,expectation.expectation_id,
                   state.selected_integrity_measurement_id,state.readiness,state.operational_disposition
              FROM representations r
              JOIN representation_current_state state USING(representation_id)
              JOIN integrity_expectations expectation
                ON expectation.subject_kind='REPRESENTATION'
               AND expectation.representation_id=r.representation_id
              JOIN integrity_measurements measurement
                ON measurement.measurement_id=state.selected_integrity_measurement_id
               AND measurement.expectation_id=expectation.expectation_id
             WHERE r.source_kind='OBJECT_REVISION'
               AND r.source_object_id=?
               AND r.source_object_revision_id=?
               AND r.source_object_revision_ordinal=?
               AND r.representation_class=? AND r.generation=?
               AND r.derivation_contract_version=? AND r.encoding_id=?
               AND r.dtype=? AND r.dimension=?
               AND state.readiness='READY' AND state.operational_disposition='USABLE'
               AND measurement.result='MATCH'
               AND (
                   SELECT count(*) FROM integrity_expectations e
                    WHERE e.subject_kind='REPRESENTATION'
                      AND e.representation_id=r.representation_id
               )=1
               AND NOT EXISTS (
                   SELECT 1
                     FROM reconciliation_cases c
                     JOIN reconciliation_case_states reconciliation_state
                       ON reconciliation_state.reconciliation_case_id=c.reconciliation_case_id
                      AND reconciliation_state.reconciliation_state_id=c.current_state_id
                      AND reconciliation_state.state_ordinal=c.current_state_ordinal
                    WHERE c.subject_kind='REPRESENTATION'
                      AND c.representation_id=r.representation_id
                      AND reconciliation_state.operational_disposition<>'USABLE'
               )
               AND (? IS NULL OR r.representation_id=?)
            """,
            tuple(parameters),
        ).fetchall()
        if not rows:
            if absent_is_none:
                return None
            raise SubstrateInvariantViolation("known historical embedding is no longer qualified")
        if len(rows) != 1:
            raise SubstrateInvariantViolation("native embedding has contradictory qualified candidates")
        row = rows[0]
        expected_length = row[10]
        required_length = np.dtype(np.float32).itemsize * expected_dimension
        if not isinstance(expected_length, int) or isinstance(expected_length, bool) or expected_length != required_length:
            raise SubstrateInvariantViolation("qualified native embedding metadata has an invalid byte length")
        dependencies = tuple(
            UUID(bytes=item[0])
            for item in self._connection.execute(
                "SELECT dependency_representation_id FROM representation_dependencies WHERE representation_id=? ORDER BY dependency_representation_id",
                (row[0],),
            )
        )
        payload_row = self._connection.execute(
            "SELECT 1 FROM representation_payloads WHERE representation_id=?", (row[0],)
        ).fetchone()
        if payload_row is None:
            raise SubstrateInvariantViolation("qualified native embedding is READY without durable payload bytes")
        try:
            payload = self._payload_reader.read_representation_payload(UUID(bytes=row[0]))
        except SubstrateObjectNotFound as exc:
            raise SubstrateInvariantViolation("qualified native embedding became unavailable during payload read") from exc
        value = QualifiedCompatEmbedding(
            representation_id=UUID(bytes=row[0]), source_object_id=UUID(bytes=row[1]),
            source_revision_id=UUID(bytes=row[2]), source_revision_ordinal=row[3],
            representation_class=row[4], generation=row[5], derivation_contract_version=row[6],
            encoding_id=row[7], dtype=row[8], dimension=row[9],
            expected_payload_byte_length=expected_length, expectation_id=UUID(bytes=row[11]),
            selected_measurement_id=UUID(bytes=row[12]), readiness=row[13], disposition=row[14],
            dependencies=dependencies, payload_byte_length=len(payload),
            payload_sha256=hashlib.sha256(payload).hexdigest(), payload_bytes=payload,
        )
        _validate_payload(value, payload)
        return value


def _validate_payload(value: QualifiedCompatEmbedding, payload: bytes) -> np.ndarray:
    required_length = np.dtype(np.float32).itemsize * value.dimension
    if len(payload) != required_length or value.expected_payload_byte_length != required_length:
        raise SubstrateInvariantViolation("qualified native embedding payload length contradicts metadata")
    if value.payload_byte_length != len(payload) or hashlib.sha256(payload).hexdigest() != value.payload_sha256:
        raise SubstrateInvariantViolation("qualified native embedding payload contradicts its byte witness")
    vector = np.frombuffer(payload, dtype=np.float32)
    if vector.size != value.dimension:
        raise SubstrateInvariantViolation("qualified native embedding payload dimension contradicts metadata")
    if not np.all(np.isfinite(vector)):
        raise SubstrateInvariantViolation("qualified native embedding payload contains non-finite values")
    return vector


def _require_uuid(field: str, value: object) -> None:
    if not isinstance(value, UUID):
        raise ValueError(f"{field} must be a UUID")


def _positive_dimension(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError("expected_dimension must be a positive integer")


__all__ = [
    "COMPAT_EMBEDDING_DTYPE",
    "COMPAT_EMBEDDING_DERIVATION_CONTRACT",
    "COMPAT_EMBEDDING_ENCODING",
    "COMPAT_EMBEDDING_GENERATION",
    "COMPAT_EMBEDDING_REPRESENTATION_CLASS",
    "MEMORY_OBJECT_KIND",
    "CurrentCompatEmbeddingWitness",
    "NativeCompatEmbeddingReader",
    "QualifiedCompatEmbedding",
]
