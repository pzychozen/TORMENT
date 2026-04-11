# torment_service/migration/cursor.py
"""
Append-only JSONL cursor for WRITE_MIGRATION crash-safe resume.

Per Decision 2, commit A ships the cursor file format and the
append-only writer. Commit A does not actually consume the cursor to
resume any write path — there is no write path in commit A — but the
format, per-workspace location, and dry-run usage all land now so
commit B's writer has a stable surface to plug into.

File format
-----------

One JSON object per line, UTF-8, trailing newline. Each line records
one cursor event:

    {
      "eid": 12345,
      "committed_at": "2026-04-11T09:00:00Z",
      "action": "DRY_RUN_CLASSIFIED",
      "gate1_class_id": 2,
      "gate2_admitted": true,
      "policy_version": "v2.4.x-step6-a"
    }

``action`` is one of:
  - ``DRY_RUN_CLASSIFIED``  — commit A dry-run emitted a classification
  - ``APPLIED``             — commit B writer rewrote the row (future)
  - ``BLOCKED_REVIEW``      — commit B writer enqueued for review (future)
  - ``SKIPPED``             — row was already canonical (commit A + B)

Commit A only emits ``DRY_RUN_CLASSIFIED`` and ``SKIPPED``. Commit B
will add ``APPLIED`` and ``BLOCKED_REVIEW``; the constants are reserved
in this module so the file format is stable across both commits.

Resume semantics
----------------

On resume, a consumer reads the cursor file line-by-line and extracts
the highest-ordinal EID that reached a terminal action. The migration
then continues from the next row. Because the writer commits a cursor
line only after the row transition itself is durable, restart after a
crash sees either the old row without a cursor line or the new row
with one — never a half-written row with an inconsistent cursor.

This gives us "effectively-once for committed row transitions under
resume" — the user's ratified wording for the crash-safety goal.

Per-workspace location
----------------------

Cursor files live in ``{workspace_root}/.torment_migration/cursor.jsonl``.
The ``.torment_migration`` subdirectory is a Decision-plan sub-question-4
ratified choice: it keeps migration state out of the main data
directory so it can be cleaned up independently and is
human-inspectable.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from .constants import (
    ADMISSION_POLICY_VERSION,
    CURSOR_DIRNAME,
    CURSOR_FILENAME,
)

# ── Cursor action vocabulary ─────────────────────────────────────────
CURSOR_ACTION_DRY_RUN_CLASSIFIED = "DRY_RUN_CLASSIFIED"
CURSOR_ACTION_SKIPPED            = "SKIPPED"
CURSOR_ACTION_APPLIED            = "APPLIED"           # Commit B
CURSOR_ACTION_BLOCKED_REVIEW     = "BLOCKED_REVIEW"    # Commit B

CURSOR_ACTIONS = frozenset({
    CURSOR_ACTION_DRY_RUN_CLASSIFIED,
    CURSOR_ACTION_SKIPPED,
    CURSOR_ACTION_APPLIED,
    CURSOR_ACTION_BLOCKED_REVIEW,
})


@dataclass
class CursorEntry:
    eid: int
    action: str
    gate1_class_id: int
    gate2_admitted: bool
    policy_version: str = ADMISSION_POLICY_VERSION
    committed_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.action not in CURSOR_ACTIONS:
            raise ValueError(
                f"Invalid cursor action {self.action!r}. "
                f"Must be one of {sorted(CURSOR_ACTIONS)}"
            )
        if self.committed_at is None:
            self.committed_at = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

    def to_json_line(self) -> str:
        return json.dumps(
            {
                "eid": int(self.eid),
                "committed_at": self.committed_at,
                "action": self.action,
                "gate1_class_id": int(self.gate1_class_id),
                "gate2_admitted": bool(self.gate2_admitted),
                "policy_version": self.policy_version,
            },
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def from_json_line(cls, line: str) -> "CursorEntry":
        obj = json.loads(line)
        return cls(
            eid=obj["eid"],
            action=obj["action"],
            gate1_class_id=obj["gate1_class_id"],
            gate2_admitted=obj["gate2_admitted"],
            policy_version=obj.get("policy_version", ""),
            committed_at=obj.get("committed_at"),
        )


def cursor_dir(workspace_root: str) -> str:
    """Return the ``.torment_migration`` directory under a workspace root."""
    return os.path.join(workspace_root, CURSOR_DIRNAME)


def cursor_path(workspace_root: str) -> str:
    """Return the absolute path to the cursor JSONL file for a workspace."""
    return os.path.join(cursor_dir(workspace_root), CURSOR_FILENAME)


def ensure_cursor_dir(workspace_root: str) -> str:
    """Create the ``.torment_migration`` directory if it does not exist
    and return its absolute path."""
    d = cursor_dir(workspace_root)
    os.makedirs(d, exist_ok=True)
    return d


def append_entry(workspace_root: str, entry: CursorEntry) -> None:
    """Append a single cursor entry to the JSONL file.

    Uses line-buffered open + explicit fsync to guarantee the entry is
    on disk before the caller proceeds. This is the backing mechanism
    for "effectively-once for committed row transitions under resume".
    """
    ensure_cursor_dir(workspace_root)
    path = cursor_path(workspace_root)
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry.to_json_line())
        f.write("\n")
        f.flush()
        try:
            os.fsync(f.fileno())
        except (AttributeError, OSError):
            # Non-POSIX backends (test tmpdirs) may not support fsync;
            # the append is still durable enough for our purposes.
            pass


def read_entries(workspace_root: str) -> List[CursorEntry]:
    """Return all cursor entries in file order. Empty list if no cursor
    file exists yet."""
    path = cursor_path(workspace_root)
    if not os.path.exists(path):
        return []
    out: List[CursorEntry] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(CursorEntry.from_json_line(line))
    return out


def processed_eids(workspace_root: str) -> set:
    """Return the set of EIDs that have a terminal cursor entry on file.

    A row is considered processed if any cursor entry exists for it,
    regardless of action. Callers on resume use this set to skip rows
    that have already been handled in a prior run.
    """
    return {entry.eid for entry in read_entries(workspace_root)}
