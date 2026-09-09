"""One structural gate for semantic use of current native memory revisions.

Legacy R1 admission is durable evidence, not a runtime semantic publication.
Every runtime owner that consumes a current memory must pass this gate instead
of treating a current EID alias as sufficient authority.
"""

from __future__ import annotations

import sqlite3
from uuid import UUID

from .errors import SubstrateInvariantViolation
from .ids import native_id_to_bytes


RUNTIME_SEMANTIC_ADMISSION_REFUSED = "RUNTIME_SEMANTIC_ADMISSION_REFUSED_LEGACY_PREDECESSOR_UNKNOWN"


def has_runtime_semantic_lineage(
    lineage_kind: object,
    revision_ordinal: object,
    predecessor_revision_id: object,
    predecessor_revision_ordinal: object,
) -> bool:
    """Evaluate the schema-level native-lineage shape without a database read."""

    if lineage_kind == "NATIVE_CREATION":
        return revision_ordinal == 1 and predecessor_revision_id is None and predecessor_revision_ordinal is None
    return (
        lineage_kind == "NATIVE_ORDINARY"
        and isinstance(revision_ordinal, int)
        and revision_ordinal > 1
        and isinstance(predecessor_revision_id, bytes)
        and len(predecessor_revision_id) == 16
        and predecessor_revision_ordinal == revision_ordinal - 1
    )


def is_runtime_semantically_admitted(
    connection: sqlite3.Connection,
    *,
    object_id: UUID | bytes,
    revision_id: UUID | bytes,
    revision_ordinal: int,
) -> bool:
    """Return whether one exact current revision has native semantic lineage.

    The schema already enforces native-successor predecessor arithmetic; this
    owner additionally checks the predecessor binding exists so callers can
    fail closed if a damaged database is opened outside normal validation.
    """

    object_blob = _blob(object_id)
    revision_blob = _blob(revision_id)
    row = connection.execute(
        """SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal
             FROM object_revisions
            WHERE object_id=? AND object_revision_id=? AND revision_ordinal=?""",
        (object_blob, revision_blob, revision_ordinal),
    ).fetchone()
    if row is None:
        raise SubstrateInvariantViolation("runtime semantic admission revision is absent")
    lineage, predecessor_id, predecessor_ordinal = row
    if not has_runtime_semantic_lineage(lineage, revision_ordinal, predecessor_id, predecessor_ordinal):
        return False
    if lineage == "NATIVE_CREATION":
        return True
    if not isinstance(predecessor_id, bytes) or not isinstance(predecessor_ordinal, int):
        return False
    if predecessor_ordinal != revision_ordinal - 1:
        return False
    return connection.execute(
        """SELECT 1 FROM object_revisions
             WHERE object_id=? AND object_revision_id=? AND revision_ordinal=?""",
        (object_blob, predecessor_id, predecessor_ordinal),
    ).fetchone() is not None


def require_runtime_semantic_admission(
    connection: sqlite3.Connection,
    *,
    object_id: UUID | bytes,
    revision_id: UUID | bytes,
    revision_ordinal: int,
) -> None:
    """Raise the named invariant when an evidence-only R1 is consumed."""

    if not is_runtime_semantically_admitted(
        connection,
        object_id=object_id,
        revision_id=revision_id,
        revision_ordinal=revision_ordinal,
    ):
        raise SubstrateInvariantViolation(RUNTIME_SEMANTIC_ADMISSION_REFUSED)


def _blob(value: UUID | bytes) -> bytes:
    if isinstance(value, UUID):
        return native_id_to_bytes(value)
    if isinstance(value, bytes) and len(value) == 16:
        return value
    raise ValueError("runtime semantic admission identity must be UUID or 16-byte BLOB")


__all__ = [
    "RUNTIME_SEMANTIC_ADMISSION_REFUSED",
    "has_runtime_semantic_lineage",
    "is_runtime_semantically_admitted",
    "require_runtime_semantic_admission",
]
