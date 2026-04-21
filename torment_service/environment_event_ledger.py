# torment_service/environment_event_ledger.py
"""
Per-workspace environment lifecycle event ledger.

Block B (docs/BLOCK_B_DESIGN.md §7.5). Audit trail only.

    EnvironmentStore's in-memory `_entries` dict (and its backing
    environment.jsonl) are the source of truth for current state.
    This ledger records the historical event stream (writes, probes,
    consults) for audit.

Per D.2 (per-workspace with ownership field), the ledger is
per-workspace — broader scope than the per-agent BatonLedger or
ReferenceLoadLedger. Environment facts are typically shared across
agents in a workspace.

Modeled on BatonLedger. Append-only JSONL.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


def _now_ts() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


@dataclass
class EnvironmentEvent:
    """One lifecycle event in a workspace's environment-memory history.

    Kinds:
        "written"   — new environment entry created (normal write).
        "probed"    — probe-on-fail path fired (observed evidence class).
                      Kept distinct from "written" so audit tooling can
                      tell which write originated from probe recovery.
        "consulted" — a consult call fired. Logged for audit; does NOT
                      modify any stored state.
    """
    event_id: str
    workspace_id: str
    kind: str
    ts: int
    env_id: Optional[str] = None          # populated for written / probed
    evidence_class: Optional[str] = None  # populated for written / probed
    operation: Optional[str] = None       # populated for consulted
    scope: Optional[str] = None           # populated for consulted
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


class EnvironmentEventLedger:
    """Per-workspace append-only environment event ledger.

    NOT a state store — EnvironmentStore entries are the source of
    truth for current state. This class records the event history.
    """

    def __init__(
        self,
        data_dir: str,
        workspace_id: str,
    ) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.data_dir = _canonical_storage_root(data_dir)

        workspace_root = os.path.realpath(
            os.path.join(self.data_dir, "workspaces", self.workspace_id,
                         "environment_memory")
        )
        if not workspace_root.startswith(self.data_dir + os.sep):
            raise ValueError(
                f"Workspace environment-memory path escapes base: "
                f"{workspace_root!r}"
            )
        os.makedirs(workspace_root, exist_ok=True)
        self._base = workspace_root

        # Colocated with the entries JSONL — the events file is already
        # used by EnvironmentStore for write/delete records; this ledger
        # appends its own events alongside. Same pattern as ArchiveStore.
        self.path = _child_path(workspace_root, "events.jsonl")

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes environment root: {rp!r}")
        return rp

    def add_event(self, event: EnvironmentEvent) -> None:
        """Append one event. The only write operation."""
        with open(self._guard(self.path), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    def list_events(
        self,
        kind: Optional[str] = None,
        env_id: Optional[str] = None,
        limit: int = 500,
    ) -> List[EnvironmentEvent]:
        """Read events with optional filters. Append-order (oldest first).

        Only events with recognized fields are returned; malformed
        JSONL lines and records with unknown keys (e.g.,
        ENVIRONMENT_WRITTEN records that EnvironmentStore writes for
        its own purposes) are skipped.
        """
        events: List[EnvironmentEvent] = []
        if not os.path.exists(self.path):
            return events
        with open(self._guard(self.path), "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    # EnvironmentStore writes records with "type" field
                    # (ENVIRONMENT_WRITTEN); we only surface ledger events
                    # with event_id as the discriminator.
                    if "event_id" not in obj:
                        continue
                    e = EnvironmentEvent(**obj)
                except Exception:
                    continue
                if kind is not None and e.kind != kind:
                    continue
                if env_id is not None and e.env_id != env_id:
                    continue
                events.append(e)
        if len(events) > limit:
            events = events[-limit:]
        return events

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    def build_written_event(
        self,
        env_id: str,
        evidence_class: str,
    ) -> EnvironmentEvent:
        return EnvironmentEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            kind="written",
            ts=_now_ts(),
            env_id=env_id,
            evidence_class=evidence_class,
        )

    def build_probed_event(
        self,
        env_id: str,
    ) -> EnvironmentEvent:
        return EnvironmentEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            kind="probed",
            ts=_now_ts(),
            env_id=env_id,
            evidence_class="observed",
        )

    def build_consulted_event(
        self,
        operation: str,
        scope: str,
    ) -> EnvironmentEvent:
        return EnvironmentEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            kind="consulted",
            ts=_now_ts(),
            operation=operation,
            scope=scope,
        )
