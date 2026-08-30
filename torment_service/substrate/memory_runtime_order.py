"""Immutable structural ordering facts for post-write memory enumeration.

The table owned here carries compatibility order only.  It is deliberately not
an object revision, semantic transition, EID alias, or payload mutation.
Callers publish it inside the same semantic transaction that creates/adopts a
memory, so a current memory cannot be committed without its required order.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from .errors import SubstrateInvariantViolation
from .ids import native_id_to_bytes

if TYPE_CHECKING:
    from .objects import SubstrateTx


def allocate_next_runtime_ordinal(tx: "SubstrateTx", legacy_source_namespace_id: UUID) -> int:
    """Return the next namespace-local ordinal while ``tx`` holds BEGIN IMMEDIATE."""
    _require_uuid("legacy_source_namespace_id", legacy_source_namespace_id)
    rows = tx.execute(
        "SELECT runtime_ordinal FROM memory_runtime_enumeration_orders "
        "WHERE legacy_source_namespace_id=?",
        (native_id_to_bytes(legacy_source_namespace_id),),
    ).fetchall()
    ordinals = tuple(row[0] for row in rows)
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in ordinals
    ):
        raise SubstrateInvariantViolation("runtime enumeration carrier has an invalid ordinal")
    if len(set(ordinals)) != len(ordinals):
        raise SubstrateInvariantViolation("runtime enumeration carrier has duplicate ordinals")
    return max(ordinals, default=-1) + 1


def publish_runtime_order(
    tx: "SubstrateTx",
    *,
    legacy_source_namespace_id: UUID,
    object_id: UUID,
    runtime_ordinal: int,
) -> None:
    """Publish and immediately witness one immutable namespace/object ordinal."""
    _require_uuid("legacy_source_namespace_id", legacy_source_namespace_id)
    _require_uuid("object_id", object_id)
    if (
        not isinstance(runtime_ordinal, int)
        or isinstance(runtime_ordinal, bool)
        or runtime_ordinal < 0
    ):
        raise ValueError("runtime_ordinal must be a non-negative integer")
    namespace = native_id_to_bytes(legacy_source_namespace_id)
    object_blob = native_id_to_bytes(object_id)
    tx.execute(
        "INSERT INTO memory_runtime_enumeration_orders "
        "(legacy_source_namespace_id,object_id,runtime_ordinal) VALUES (?,?,?)",
        (namespace, object_blob, runtime_ordinal),
    )
    actual = tx.execute(
        "SELECT runtime_ordinal FROM memory_runtime_enumeration_orders "
        "WHERE legacy_source_namespace_id=? AND object_id=?",
        (namespace, object_blob),
    ).fetchone()
    if actual != (runtime_ordinal,):
        raise SubstrateInvariantViolation("runtime enumeration order publication is incomplete")


def _require_uuid(name: str, value: object) -> None:
    if not isinstance(value, UUID):
        raise ValueError(f"{name} must be a UUID")


__all__ = ["allocate_next_runtime_ordinal", "publish_runtime_order"]
