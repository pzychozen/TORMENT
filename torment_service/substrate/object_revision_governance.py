"""Typed revision-bound memory-governance facts for schema v1.1.

This module deliberately does not depend on the legacy runtime's governance
DTO.  It provides exact structural reads and one internal qualification writer
for a governance row created alongside its owning object revision.
"""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import TYPE_CHECKING
from uuid import UUID

from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from .ids import native_id_to_bytes
from .schema import require_current_schema

if TYPE_CHECKING:
    from .objects import SubstrateTx


@dataclass(frozen=True)
class NativeMemoryGovernanceFacts:
    """The five independent runtime-governance facts on one exact revision."""

    protected: bool = False
    non_shareable: bool = False
    collective_export_blocked: bool = False
    collective_reingest_blocked: bool = False
    decay_accelerated: bool = False

    def as_storage_tuple(self) -> tuple[int, int, int, int, int]:
        _validate_facts(self)
        return (
            int(self.protected),
            int(self.non_shareable),
            int(self.collective_export_blocked),
            int(self.collective_reingest_blocked),
            int(self.decay_accelerated),
        )


@dataclass(frozen=True)
class ObjectRevisionGovernance:
    """One immutable, explicit governance vector bound to an object revision."""

    object_id: UUID
    object_revision_id: UUID
    object_revision_ordinal: int
    facts: NativeMemoryGovernanceFacts


class NativeObjectRevisionGovernanceService:
    """Read exact revision governance without payload parsing or defaults."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        require_current_schema(connection)
        self._connection = connection

    def get_object_revision_governance(
        self,
        *,
        object_id: UUID,
        object_revision_id: UUID,
        object_revision_ordinal: int,
    ) -> ObjectRevisionGovernance | None:
        """Return explicit facts, or ``None`` when the exact revision has none."""
        _validate_revision_identity(object_id, object_revision_id, object_revision_ordinal)
        identity = (
            native_id_to_bytes(object_id),
            native_id_to_bytes(object_revision_id),
            object_revision_ordinal,
        )
        if self._connection.execute(
            "SELECT 1 FROM object_revisions WHERE object_id=? AND object_revision_id=? AND revision_ordinal=?",
            identity,
        ).fetchone() is None:
            raise SubstrateObjectNotFound("native object revision was not found")
        rows = self._connection.execute(
            """
            SELECT protected,non_shareable,collective_export_blocked,
                   collective_reingest_blocked,decay_accelerated
            FROM object_revision_governance
            WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=?
            """,
            identity,
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise SubstrateInvariantViolation("exact object revision has duplicate governance rows")
        row = rows[0]
        if any(value not in (0, 1) for value in row):
            raise SubstrateInvariantViolation("stored governance facts are not exact booleans")
        return ObjectRevisionGovernance(
            object_id,
            object_revision_id,
            object_revision_ordinal,
            NativeMemoryGovernanceFacts(*(bool(value) for value in row)),
        )

    def get_current_object_governance(
        self, *, object_id: UUID
    ) -> ObjectRevisionGovernance | None:
        """Follow the selected current revision, preserving explicit absence."""
        if not isinstance(object_id, UUID):
            raise ValueError("object_id must be a UUID")
        row = self._connection.execute(
            "SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
            (native_id_to_bytes(object_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("native object was not found")
        if row[0] is None or row[1] is None:
            raise SubstrateInvariantViolation("native object has no selected current revision")
        return self.get_object_revision_governance(
            object_id=object_id,
            object_revision_id=UUID(bytes=row[0]),
            object_revision_ordinal=row[1],
        )


def _insert_published_governance_for_qualification(
    tx: SubstrateTx,
    *,
    object_id: bytes,
    object_revision_id: bytes,
    object_revision_ordinal: int,
    facts: NativeMemoryGovernanceFacts,
) -> None:
    """Attach facts inside the owning object operation; not a public mutation API."""
    if not isinstance(object_revision_ordinal, int) or isinstance(object_revision_ordinal, bool) or object_revision_ordinal < 1:
        raise ValueError("object_revision_ordinal must be a positive integer")
    stored = facts.as_storage_tuple()
    tx.execute(
        """
        INSERT INTO object_revision_governance(
            object_id,object_revision_id,object_revision_ordinal,protected,
            non_shareable,collective_export_blocked,collective_reingest_blocked,
            decay_accelerated
        ) VALUES (?,?,?,?,?,?,?,?)
        """,
        (object_id, object_revision_id, object_revision_ordinal, *stored),
    )
    tx.governance_published.append(
        (object_id, object_revision_id, object_revision_ordinal, stored)
    )


def _validate_facts(facts: NativeMemoryGovernanceFacts) -> None:
    if not isinstance(facts, NativeMemoryGovernanceFacts):
        raise ValueError("native memory governance facts are required")
    if any(
        type(value) is not bool
        for value in (
            facts.protected,
            facts.non_shareable,
            facts.collective_export_blocked,
            facts.collective_reingest_blocked,
            facts.decay_accelerated,
        )
    ):
        raise ValueError("native memory governance facts must be booleans")


def _validate_revision_identity(
    object_id: UUID, object_revision_id: UUID, object_revision_ordinal: int
) -> None:
    if not isinstance(object_id, UUID) or not isinstance(object_revision_id, UUID):
        raise ValueError("object and object revision IDs must be UUIDs")
    if (
        not isinstance(object_revision_ordinal, int)
        or isinstance(object_revision_ordinal, bool)
        or object_revision_ordinal < 1
    ):
        raise ValueError("object_revision_ordinal must be a positive integer")


__all__ = [
    "NativeMemoryGovernanceFacts",
    "NativeObjectRevisionGovernanceService",
    "ObjectRevisionGovernance",
]
