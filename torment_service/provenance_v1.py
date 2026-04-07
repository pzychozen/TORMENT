# torment_service/provenance_v1.py
"""
ProvenanceV1 — ingest-level lineage metadata for every stored memory.

First-pass schema (v2.4.x) per DOCTRINE_v2.4.x.md rule #1:
"Provenance is a hard boundary."

This is NOT the spine-level Provenance (schemas/provenance.py) which tracks
role outputs and derivation depth through the cognition pipeline.
ProvenanceV1 lives at the storage layer and answers:
  - where did this memory come from?
  - what path wrote it?
  - what memories did it derive from?
  - is this safe to write again?

See ROADMAP_v2.4.x.md §2.2 for design goals.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional


# ── Enum constants ──────────────────────────────────────────────────

SOURCE_USER_INPUT   = "user_input"
SOURCE_ROLE_OUTPUT  = "role_output"
SOURCE_DERIVED      = "derived"
SOURCE_MEMORY       = "memory"
SOURCE_TOOL_RESULT      = "tool_result"
SOURCE_COLLECTIVE_ECHO  = "collective_echo"

VALID_SOURCE_TYPES = frozenset({
    SOURCE_USER_INPUT,
    SOURCE_ROLE_OUTPUT,
    SOURCE_DERIVED,
    SOURCE_MEMORY,
    SOURCE_TOOL_RESULT,
    SOURCE_COLLECTIVE_ECHO,
})

WRITE_DIRECT_INGEST       = "direct_ingest"
WRITE_COGNITION_WRITEBACK = "cognition_writeback"
WRITE_REFLECTION_WRITEBACK = "reflection_writeback"
WRITE_TOOL_INGEST         = "tool_ingest"
WRITE_MIGRATION           = "migration"
WRITE_SYSTEM_IMPORT       = "system_import"
WRITE_COLLECTIVE_REINGEST = "collective_reingest"

VALID_WRITE_PATHS = frozenset({
    WRITE_DIRECT_INGEST,
    WRITE_COGNITION_WRITEBACK,
    WRITE_REFLECTION_WRITEBACK,
    WRITE_TOOL_INGEST,
    WRITE_MIGRATION,
    WRITE_SYSTEM_IMPORT,
    WRITE_COLLECTIVE_REINGEST,
})

SCHEMA_VERSION = "1.0"


# ── Dataclass ───────────────────────────────────────────────────────

@dataclass
class ProvenanceV1:
    """Ingest-level provenance for stored memories.

    Required fields (all have sensible defaults for plain user ingest):
        schema_version, source_type, source_role, write_path,
        parent_eids, created_at_step, created_at_ts

    Optional fields:
        tool_name, session_id, notes
    """

    schema_version: str = SCHEMA_VERSION
    source_type: str = SOURCE_USER_INPUT
    source_role: Optional[str] = None
    write_path: str = WRITE_DIRECT_INGEST
    parent_eids: List[int] = field(default_factory=list)
    created_at_step: Optional[int] = None
    created_at_ts: Optional[str] = None

    # Optional fields — cheap to support now
    tool_name: Optional[str] = None
    session_id: Optional[str] = None
    notes: Optional[str] = None

    # ── Validation (Rule 3, 4, 5, 6) ───────────────────────────────

    def __post_init__(self) -> None:
        # Rule 6: reject unknown enum values
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type '{self.source_type}'. "
                f"Must be one of: {sorted(VALID_SOURCE_TYPES)}"
            )
        if self.write_path not in VALID_WRITE_PATHS:
            raise ValueError(
                f"Invalid write_path '{self.write_path}'. "
                f"Must be one of: {sorted(VALID_WRITE_PATHS)}"
            )
        # Rule 3: role_output requires source_role
        if self.source_type == SOURCE_ROLE_OUTPUT and not self.source_role:
            raise ValueError(
                "source_role must not be null when source_type is 'role_output'"
            )
        # Rule 5: parent_eids must exist (default factory handles this,
        # but guard against None assignment)
        if self.parent_eids is None:
            self.parent_eids = []
        # Deduplicate parent_eids, preserve order
        seen: set = set()
        deduped: List[int] = []
        for eid in self.parent_eids:
            eid_int = int(eid)
            if eid_int not in seen:
                seen.add(eid_int)
                deduped.append(eid_int)
        self.parent_eids = deduped
        # Auto-fill timestamp if not provided
        if self.created_at_ts is None:
            self.created_at_ts = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

    # ── Serialization ───────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-safe dict. Omits None optional fields."""
        d = asdict(self)
        # Strip None optional fields to keep payloads compact
        for k in ("tool_name", "session_id", "notes"):
            if d.get(k) is None:
                del d[k]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProvenanceV1":
        """Deserialize from dict, ignoring unknown keys."""
        if not d:
            raise ValueError("Cannot create ProvenanceV1 from empty dict")
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)

    # ── Factory methods ─────────────────────────────────────────────

    @classmethod
    def for_user_ingest(
        cls,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Default provenance for plain user input (Rule 2)."""
        return cls(
            source_type=SOURCE_USER_INPUT,
            source_role=None,
            write_path=WRITE_DIRECT_INGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
        )

    @classmethod
    def for_cognition_writeback(
        cls,
        source_role: str,
        parent_eids: Optional[List[int]] = None,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for archivist / cognition pipeline write-back."""
        return cls(
            source_type=SOURCE_ROLE_OUTPUT,
            source_role=source_role,
            write_path=WRITE_COGNITION_WRITEBACK,
            parent_eids=parent_eids or [],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
        )

    @classmethod
    def for_tool_result(
        cls,
        tool_name: str,
        parent_eids: Optional[List[int]] = None,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for content produced by an external MCP/tool call."""
        return cls(
            source_type=SOURCE_TOOL_RESULT,
            source_role=None,
            write_path=WRITE_TOOL_INGEST,
            parent_eids=parent_eids or [],
            created_at_step=step,
            tool_name=tool_name,
            session_id=session_id,
        )

    @classmethod
    def for_collective_echo(
        cls,
        step: Optional[int] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ProvenanceV1":
        """Provenance for a collective/hivemind echo reingested into an agent."""
        return cls(
            source_type=SOURCE_COLLECTIVE_ECHO,
            source_role=None,
            write_path=WRITE_COLLECTIVE_REINGEST,
            parent_eids=[],
            created_at_step=step,
            session_id=session_id,
            notes=notes,
        )

    # ── Safety checks ───────────────────────────────────────────────

    def is_archivist_writeback(self) -> bool:
        """Check if this provenance indicates archivist write-back origin."""
        return (
            self.write_path == WRITE_COGNITION_WRITEBACK
            and self.source_role is not None
            and "archivist" in self.source_role.lower()
        )

    @staticmethod
    def check_recursion_safe(
        new_provenance: "ProvenanceV1",
        parent_provenances: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """First-pass recursion guard for archivist write-back.

        Returns True if the write is safe (no archivist chain detected).
        Returns False if:
          - The new write is archivist write-back AND any parent memory
            was also archivist write-back.
        """
        if not new_provenance.is_archivist_writeback():
            return True  # Not archivist, always safe
        if not parent_provenances:
            return True  # No parents to check
        for parent_prov in parent_provenances:
            if not parent_prov:
                continue
            p_write_path = parent_prov.get("write_path", "")
            p_source_role = parent_prov.get("source_role", "") or ""
            if (p_write_path == WRITE_COGNITION_WRITEBACK
                    and "archivist" in p_source_role.lower()):
                return False  # Parent was also archivist write-back → block
        return True
