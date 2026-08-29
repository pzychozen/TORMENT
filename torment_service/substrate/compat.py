"""Read-only, namespaced EID compatibility views over the native substrate.

This facade is deliberately independent of ``MemoryGraph`` and legacy files.
It resolves only a previously admitted ``EID`` alias to a native core-memory
object and projects that object's selected immutable revision.  It provides no
search, write, authorization, fallback, or cutover behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID
import sqlite3

from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from .ids import native_id_from_bytes, native_id_to_bytes
from .schema import open_schema

_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"


@dataclass(frozen=True)
class LegacyRepresentationReference:
    representation_id: UUID; representation_class: str; generation: int; readiness: str; operational_disposition: str; usable: bool


@dataclass(frozen=True)
class LegacyMemoryView:
    """An immutable compatibility projection, never a persisted shadow record."""
    eid: int; object_id: UUID; revision_id: UUID; revision_ordinal: int; semantic_scope_id: UUID
    existence_state: str; lifecycle_state: str; lifecycle_authoritative: bool; governance_state: str
    authority_category: str; provenance_id: UUID | None; payload: Mapping[str, Any]
    representation_references: tuple[LegacyRepresentationReference, ...]

    @property
    def summary(self) -> str | None:
        value = self.payload.get("summary", self.payload.get("text"))
        return value if isinstance(value, str) else None

    def to_legacy_dict(self) -> dict[str, Any]:
        """Return a fresh legacy-shaped read view without leaking SQLite rows."""
        value = dict(self.payload)
        value.update({"eid": self.eid, "summary": self.summary, "lifecycle_state": self.lifecycle_state,
                      "lifecycle_authoritative": self.lifecycle_authoritative, "governance_state": self.governance_state,
                      "authority_category": self.authority_category, "exists": self.existence_state == "EXISTS",
                      "representation_refs": [{"representation_class": item.representation_class, "generation": item.generation,
                          "readiness": item.readiness, "operational_disposition": item.operational_disposition, "usable": item.usable}
                          for item in self.representation_references]})
        return value


class NativeMemoryCompatibilityFacade:
    """Substrate-owned, read-only EID facade; a namespace is always required."""
    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection); self._connection = connection

    def resolve_memory_eid(self, *, legacy_source_namespace_id: UUID, eid: int) -> UUID:
        return native_id_from_bytes(self._current_row(legacy_source_namespace_id, eid)[0])

    def resolve_native_memory_legacy_eid(self, *, legacy_source_namespace_id: UUID, native_object_id: UUID) -> int:
        object_id = native_id_to_bytes(native_object_id)
        kind = self._connection.execute("SELECT object_kind FROM objects WHERE object_id=?", (object_id,)).fetchone()
        if kind is None: raise SubstrateObjectNotFound("native object was not found")
        if kind[0] != _MEMORY_OBJECT_KIND: raise SubstrateInvariantViolation("native object is not an admissible core memory")
        aliases = self._connection.execute("SELECT alias_value FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND object_id=? ORDER BY alias_value", (native_id_to_bytes(legacy_source_namespace_id), object_id)).fetchall()
        if not aliases: raise SubstrateObjectNotFound("native core memory has no EID compatibility alias in this namespace")
        if len(aliases) != 1: raise SubstrateInvariantViolation("native core memory has ambiguous EID aliases in this namespace")
        try: eid = int(aliases[0][0])
        except (TypeError, ValueError) as exc: raise SubstrateInvariantViolation("EID alias is not an integer") from exc
        if str(eid) != aliases[0][0] or eid < 0: raise SubstrateInvariantViolation("EID alias is not canonical non-negative integer text")
        self._current_row(legacy_source_namespace_id, eid)
        return eid

    def get_memory_by_eid(self, *, legacy_source_namespace_id: UUID, eid: int) -> LegacyMemoryView:
        return self._view(eid, self._current_row(legacy_source_namespace_id, eid))

    def get_memory_revision(self, *, legacy_source_namespace_id: UUID, eid: int, revision_id: UUID) -> LegacyMemoryView:
        object_id = self.resolve_memory_eid(legacy_source_namespace_id=legacy_source_namespace_id, eid=eid)
        row = self._connection.execute("""SELECT o.object_id,r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,r.existence_state,r.lifecycle_state,r.lifecycle_authoritative,r.governance_state,r.authority_category,r.provenance_id,r.payload_format,r.payload_text FROM objects o JOIN object_revisions r ON r.object_id=o.object_id WHERE o.object_id=? AND r.object_revision_id=? AND o.object_kind=?""", (native_id_to_bytes(object_id), native_id_to_bytes(revision_id), _MEMORY_OBJECT_KIND)).fetchone()
        if row is None: raise SubstrateObjectNotFound("native core-memory revision was not found")
        return self._view(eid, row)

    def _current_row(self, namespace: UUID, eid: int) -> tuple[Any, ...]:
        if not isinstance(eid, int) or isinstance(eid, bool) or eid < 0: raise ValueError("compatibility EID must be a non-negative integer")
        row = self._connection.execute("""SELECT o.object_id,r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,r.existence_state,r.lifecycle_state,r.lifecycle_authoritative,r.governance_state,r.authority_category,r.provenance_id,r.payload_format,r.payload_text FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id JOIN object_revisions r ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id AND r.revision_ordinal=o.current_revision_ordinal WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?""", (native_id_to_bytes(namespace), str(eid))).fetchone()
        if row is None: raise SubstrateObjectNotFound("namespaced EID compatibility alias was not found")
        if self._connection.execute("SELECT object_kind FROM objects WHERE object_id=?", (row[0],)).fetchone()[0] != _MEMORY_OBJECT_KIND: raise SubstrateInvariantViolation("EID alias does not target an admissible core memory")
        return row

    def _view(self, eid: int, row: tuple[Any, ...]) -> LegacyMemoryView:
        refs = tuple(LegacyRepresentationReference(native_id_from_bytes(item[0]), item[1], item[2], item[3], item[4], item[3] == "READY" and item[4] == "USABLE") for item in self._connection.execute("""SELECT r.representation_id,r.representation_class,r.generation,s.readiness,s.operational_disposition FROM representations r JOIN representation_current_state s USING(representation_id) WHERE r.source_kind='OBJECT_REVISION' AND r.source_object_id=? AND r.source_object_revision_id=? AND r.source_object_revision_ordinal=? ORDER BY r.representation_class,r.generation,r.representation_id""", (row[0], row[1], row[2])))
        return LegacyMemoryView(eid, native_id_from_bytes(row[0]), native_id_from_bytes(row[1]), row[2], native_id_from_bytes(row[3]), row[4], row[5], bool(row[6]), row[7], row[8], native_id_from_bytes(row[9]) if row[9] is not None else None, MappingProxyType(_payload_mapping(row[10], row[11])), refs)


def _payload_mapping(payload_format: str, payload_text: str | None) -> dict[str, Any]:
    if payload_text is None: return {}
    if payload_format in {"JSON", "TEXT"}:
        try: value = json.loads(payload_text)
        except json.JSONDecodeError: return {"content": payload_text}
        return value if isinstance(value, dict) else {"content": payload_text}
    return {}
