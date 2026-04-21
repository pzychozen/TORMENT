# torment_service/reference_load_ledger.py
"""
Per-(workspace, agent) reference load lifecycle event ledger.

Block B (docs/BLOCK_B_DESIGN.md §6.4). Audit trail only.

    The in-memory ActiveLoad is the source of truth for current load
    state. This ledger records the historical event stream (loaded /
    unloaded) for audit. Payload and ledger must NOT be treated as
    competing state stores — if they ever appear to disagree, the
    ActiveLoad wins and the ledger stays re-derivable from its
    append-only history.

Modeled on BatonLedger (torment_service/baton_ledger.py):
    - per-(workspace, agent) scope — append-only JSONL
    - path-safe construction via safe_slug + _canonical_storage_root
    - no LLM involvement, no automation beyond caller-requested writes

CARRY-FORWARD CAUTION (ratified 2026-04-21): event identity is
separate from reference identity. Each load or unload is its own
event with its own event_id; the underlying ref_id is a reference,
not an echo of identity.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from typing import List, Optional

from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


def _now_ts() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


@dataclass
class ReferenceLoadEvent:
    """One lifecycle event in a reference's load history.

    Kinds:
        "loaded"    — load_reference call succeeded; stale_at_load
                      records the staleness result for THIS load.
        "unloaded"  — unload_reference call marked the load consumed.
    """
    event_id: str
    workspace_id: str
    agent_id: str
    ref_id: str
    load_id: str
    kind: str
    ts: int
    scope_tag: str
    stale_at_load: Optional[bool] = None  # populated only for "loaded"


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


class ReferenceLoadLedger:
    """Append-only per-(workspace, agent) reference load ledger.

    NOT a state store — the in-memory ActiveLoad dict on TormentFabric
    is the source of truth for current state. This class exists
    purely to record the event history.
    """

    def __init__(
        self,
        data_dir: str,
        workspace_id: str,
        agent_id: str,
    ) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.agent_id = safe_slug(agent_id, "agent_id")

        self.data_dir = _canonical_storage_root(data_dir)
        agent_root = os.path.realpath(
            os.path.join(self.data_dir, "workspaces",
                         self.workspace_id, "agents", self.agent_id)
        )
        if not agent_root.startswith(self.data_dir + os.sep):
            raise ValueError(f"Agent path escapes base: {agent_root!r}")
        os.makedirs(agent_root, exist_ok=True)
        self._base = agent_root
        self.path = _child_path(agent_root, "reference_load_events.jsonl")

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes agent root: {rp!r}")
        return rp

    def add_event(self, event: ReferenceLoadEvent) -> None:
        """Append one event. The only write operation."""
        with open(self._guard(self.path), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    def list_events(
        self,
        ref_id: Optional[str] = None,
        kind: Optional[str] = None,
        load_id: Optional[str] = None,
        limit: int = 500,
    ) -> List[ReferenceLoadEvent]:
        """Read events with optional filters.

        Order: append order (oldest first). If more than `limit` events
        remain after filtering, the last `limit` are returned (most
        recent).

        Malformed JSONL lines are skipped silently — read-forgiving so
        a single corrupted event can't hide the rest of the history.
        """
        events: List[ReferenceLoadEvent] = []
        if not os.path.exists(self.path):
            return events
        with open(self._guard(self.path), "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    e = ReferenceLoadEvent(**obj)
                except Exception:
                    continue
                if ref_id is not None and e.ref_id != ref_id:
                    continue
                if kind is not None and e.kind != kind:
                    continue
                if load_id is not None and e.load_id != load_id:
                    continue
                events.append(e)
        if len(events) > limit:
            events = events[-limit:]
        return events

    # ------------------------------------------------------------------
    # Convenience constructors — fill event_id + ts so call sites stay
    # small. No behavior difference.
    # ------------------------------------------------------------------

    def build_loaded_event(
        self,
        ref_id: str,
        load_id: str,
        scope_tag: str,
        stale_at_load: bool,
    ) -> ReferenceLoadEvent:
        return ReferenceLoadEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            agent_id=self.agent_id,
            ref_id=ref_id,
            load_id=load_id,
            kind="loaded",
            ts=_now_ts(),
            scope_tag=scope_tag,
            stale_at_load=stale_at_load,
        )

    def build_unloaded_event(
        self,
        ref_id: str,
        load_id: str,
        scope_tag: str,
    ) -> ReferenceLoadEvent:
        return ReferenceLoadEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            agent_id=self.agent_id,
            ref_id=ref_id,
            load_id=load_id,
            kind="unloaded",
            ts=_now_ts(),
            scope_tag=scope_tag,
        )
