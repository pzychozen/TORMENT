"""Read-only native implementation of the post-write memory access contract.

The caller supplies an already-open, qualified v1.1 connection and one legacy
source namespace.  This module never owns that connection and never creates a
semantic transaction.  Search delegates unchanged to the established native
compatibility search owner; embedding eligibility delegates to its dedicated
read-only reader.
"""
from __future__ import annotations

import math
import sqlite3
from typing import Any, Mapping
from uuid import UUID

from torment_service.memory_runtime_access import (
    RuntimeMemoryEmbedding,
    RuntimeMemoryGovernanceView,
    RuntimeMemoryProvenanceView,
    RuntimeMemorySearchHit,
    RuntimeMemorySearchOutcome,
    RuntimeMemoryView,
    classify_post_write_query,
    project_runtime_payload,
)

from .compat import LegacyMemoryView, NativeMemoryCompatibilityFacade
from .compat_embedding_reader import NativeCompatEmbeddingReader
from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from .ids import native_id_to_bytes
from .object_revision_governance import NativeObjectRevisionGovernanceService
from .schema import require_current_schema


class NativePostWriteMemoryAccess:
    """One namespace-bound, read-only view of current native core memories."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        legacy_source_namespace_id: UUID,
        expected_dimension: int,
    ) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("connection must be an already-open sqlite connection")
        if not isinstance(legacy_source_namespace_id, UUID):
            raise ValueError("legacy_source_namespace_id must be a UUID")
        if not isinstance(expected_dimension, int) or isinstance(expected_dimension, bool) or expected_dimension < 1:
            raise ValueError("expected_dimension must be a positive integer")
        require_current_schema(connection)
        self._connection = connection
        self._legacy_source_namespace_id = legacy_source_namespace_id
        self._expected_dimension = expected_dimension
        # The existing facade is the only native owner of current candidate
        # eligibility and ranking.  This adapter exposes no mutation methods.
        self._compatibility_reads = NativeMemoryCompatibilityFacade(connection)
        self._embeddings = NativeCompatEmbeddingReader(connection)
        self._governance = NativeObjectRevisionGovernanceService(connection)

    def get_current(self, eid: int) -> RuntimeMemoryView | None:
        source = self._get_native_current(eid)
        if source is None:
            return None
        return self._project_current(source)

    def list_current(self) -> tuple[RuntimeMemoryView, ...]:
        """Return all current compatibility memories in their qualified order.

        The carrier is not inferred from EID, SQLite row order, timestamps, or
        UUIDs.  Any discrepancy between aliases, current objects, and the
        immutable namespace order fails closed rather than inventing a tail.
        """
        namespace = native_id_to_bytes(self._legacy_source_namespace_id)
        alias_rows = self._connection.execute(
            """
            SELECT a.alias_value,a.object_id
              FROM legacy_object_aliases a
              JOIN objects o ON o.object_id=a.object_id
              JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
             WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID'
               AND r.existence_state='EXISTS'
            """,
            (namespace,),
        ).fetchall()
        aliases: dict[bytes, int] = {}
        for alias_value, object_id in alias_rows:
            eid = _canonical_eid_alias(alias_value)
            if not isinstance(object_id, bytes) or len(object_id) != 16:
                raise SubstrateInvariantViolation("runtime EID alias has an invalid object identity")
            if object_id in aliases:
                raise SubstrateInvariantViolation("runtime enumeration has an ambiguous object alias")
            aliases[object_id] = eid

        order_rows = self._connection.execute(
            """
            SELECT object_id,runtime_ordinal
              FROM memory_runtime_enumeration_orders
             WHERE legacy_source_namespace_id=?
             ORDER BY runtime_ordinal
            """,
            (namespace,),
        ).fetchall()
        ordered: list[tuple[bytes, int]] = []
        seen_ordinals: set[int] = set()
        seen_objects: set[bytes] = set()
        for object_id, ordinal in order_rows:
            if not isinstance(object_id, bytes) or len(object_id) != 16:
                raise SubstrateInvariantViolation("runtime enumeration order has an invalid object identity")
            if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
                raise SubstrateInvariantViolation("runtime enumeration order has an invalid ordinal")
            if ordinal in seen_ordinals or object_id in seen_objects:
                raise SubstrateInvariantViolation("runtime enumeration order is ambiguous")
            kind = self._connection.execute(
                "SELECT object_kind FROM objects WHERE object_id=?", (object_id,)
            ).fetchone()
            if kind is None or kind != ("LEGACY_CORE_NODE",):
                raise SubstrateInvariantViolation("runtime enumeration order does not point at a core memory")
            seen_ordinals.add(ordinal)
            seen_objects.add(object_id)
            ordered.append((object_id, ordinal))
        if seen_objects != set(aliases):
            raise SubstrateInvariantViolation("current memory aliases and runtime enumeration order disagree")

        views: list[RuntimeMemoryView] = []
        seen_eids: set[int] = set()
        for object_id, _ordinal in ordered:
            eid = aliases.get(object_id)
            if eid is None:
                raise SubstrateInvariantViolation("runtime enumeration order has no EID alias")
            if eid in seen_eids:
                raise SubstrateInvariantViolation("runtime enumeration has duplicate EIDs")
            source = self._get_native_current(eid)
            if source is None or native_id_to_bytes(source.object_id) != object_id:
                raise SubstrateInvariantViolation("runtime enumeration current memory is absent or ambiguous")
            views.append(self._project_current(source))
            seen_eids.add(eid)
        return tuple(views)

    def search_by_embedding(
        self, embedding: Any, *, top_k: int, user_id: str | None = None,
    ) -> RuntimeMemorySearchOutcome:
        status = classify_post_write_query(embedding, expected_dimension=self._expected_dimension)
        if status == "ZERO_NORM":
            return RuntimeMemorySearchOutcome(status, ())
        results = self._compatibility_reads.search_by_embedding(
            legacy_source_namespace_id=self._legacy_source_namespace_id,
            embedding=embedding,
            dimension=self._expected_dimension,
            top_k=top_k,
            user_id=user_id,
        )
        hits: list[RuntimeMemorySearchHit] = []
        for result in results:
            source = self._get_native_current(result.eid)
            if source is None:
                # The compatibility search already refuses a source that
                # advanced during its candidate scan.  A disappearance here is
                # therefore a concurrent-read race, not a historical fallback.
                continue
            hits.append(RuntimeMemorySearchHit(
                view=self._project_current(source),
                raw_score=result.raw_score,
                score=result.score,
                decay_factor=result.decay_factor,
            ))
        return RuntimeMemorySearchOutcome(status, tuple(hits))

    def read_current_embedding(
        self, eid: int, *, expected_dimension: int,
    ) -> RuntimeMemoryEmbedding | None:
        self._require_dimension(expected_dimension)
        source = self._get_native_current(eid)
        if source is None:
            return None
        qualified = self._embeddings.read_current(
            source.object_id, expected_dimension=expected_dimension,
        )
        if qualified is None:
            return None
        # NativeCompatEmbeddingReader has already validated exact currentness,
        # lane identity, READY/USABLE/MATCH evidence, reconciliation, length,
        # hash witness, and finite float32 bytes.
        return RuntimeMemoryEmbedding(
            dtype=qualified.dtype,
            dimension=qualified.dimension,
            payload_bytes=qualified.payload_bytes,
            byte_length=qualified.payload_byte_length,
            payload_sha256=qualified.payload_sha256,
        )

    def _get_native_current(self, eid: int) -> LegacyMemoryView | None:
        _validate_eid(eid)
        try:
            return self._compatibility_reads.get_memory_by_eid(
                legacy_source_namespace_id=self._legacy_source_namespace_id, eid=eid,
            )
        except SubstrateObjectNotFound:
            return None

    def _project_current(self, source: LegacyMemoryView) -> RuntimeMemoryView:
        payload = source.payload
        if not isinstance(payload, Mapping):
            raise SubstrateInvariantViolation("native current memory payload is not a mapping")
        summary = _required_text(payload, "summary")
        memory_type = _required_text(payload, "type")
        memory_class = _required_text(payload, "memory_class")
        governance = self._governance.get_object_revision_governance(
            object_id=source.object_id,
            object_revision_id=source.revision_id,
            object_revision_ordinal=source.revision_ordinal,
        )
        if governance is None:
            governance_view = RuntimeMemoryGovernanceView(
                False, False, False, False, False, False,
            )
        else:
            facts = governance.facts
            governance_view = RuntimeMemoryGovernanceView(
                facts.protected,
                facts.non_shareable,
                facts.collective_export_blocked,
                facts.collective_reingest_blocked,
                facts.decay_accelerated,
                True,
            )
        return RuntimeMemoryView(
            eid=source.eid,
            summary=summary,
            memory_type=memory_type,
            memory_class=memory_class,
            strength=_required_number(payload, "strength"),
            confidence=_required_number(payload, "confidence"),
            payload=project_runtime_payload(payload),
            governance=governance_view,
            provenance=self._provenance(source),
        )

    def _provenance(self, source: LegacyMemoryView) -> RuntimeMemoryProvenanceView:
        if source.provenance_id is None:
            raise SubstrateInvariantViolation("native current memory has no structural provenance")
        rows = self._connection.execute(
            """
            SELECT origin_kind,source_channel,derivation_status
              FROM provenance_records
             WHERE provenance_id=?
            """,
            (native_id_to_bytes(source.provenance_id),),
        ).fetchall()
        if len(rows) != 1:
            raise SubstrateInvariantViolation("native current memory provenance is missing or ambiguous")
        origin_kind, source_channel, derivation_status = rows[0]
        if not isinstance(origin_kind, str) or not origin_kind:
            raise SubstrateInvariantViolation("native structural provenance has invalid origin kind")
        if source_channel is not None and not isinstance(source_channel, str):
            raise SubstrateInvariantViolation("native structural provenance has invalid source channel")
        if not isinstance(derivation_status, str) or not derivation_status:
            raise SubstrateInvariantViolation("native structural provenance has invalid derivation status")
        # A3C1 maps ProvenanceV1.source_type into source_channel and write_path
        # into derivation_status.  Other existing native origin kinds retain
        # their frozen source channel rather than fabricating a ProvenanceV1.
        source_type = source_channel
        return RuntimeMemoryProvenanceView(
            source_type=source_type,
            source_channel=source_channel,
            write_path=derivation_status,
            collective_echo=source_type == "collective_echo",
            structurally_explicit=True,
        )

    def _require_dimension(self, expected_dimension: int) -> None:
        if expected_dimension != self._expected_dimension:
            raise ValueError("requested embedding dimension does not match this access adapter")


def _validate_eid(eid: object) -> None:
    if not isinstance(eid, int) or isinstance(eid, bool) or eid < 0:
        raise ValueError("eid must be a non-negative integer")


def _canonical_eid_alias(value: object) -> int:
    if not isinstance(value, str) or not value:
        raise SubstrateInvariantViolation("runtime EID alias is invalid")
    try:
        eid = int(value)
    except ValueError as exc:
        raise SubstrateInvariantViolation("runtime EID alias is invalid") from exc
    if str(eid) != value:
        raise SubstrateInvariantViolation("runtime EID alias is not canonical")
    _validate_eid(eid)
    return eid


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str):
        raise SubstrateInvariantViolation(f"native current memory payload has no {field} text")
    return value


def _required_number(payload: Mapping[str, Any], field: str) -> float:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise SubstrateInvariantViolation(f"native current memory payload has no finite {field}")
    return float(value)


__all__ = ["NativePostWriteMemoryAccess"]
