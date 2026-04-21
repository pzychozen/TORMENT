# torment_service/baton_ledger.py
"""
Append-only per-(workspace, agent) baton lifecycle event ledger.

Block A (docs/BLOCK_A_DESIGN.md §6.4). Audit trail, not current state.

    The memory entity's payload["baton_lifecycle"] is the source of
    truth for current baton status. This ledger records the historical
    event stream (created, consumed, expired_notice) for audit, debugging,
    and future tooling (session-start aging signal, v0.1.0-sessions).

    Payload and ledger must NOT be treated as competing state stores —
    if they ever appear to disagree, the payload wins and the ledger
    stays re-derivable from its append-only event history.

Modeled on ConflictRegistry (torment_service/conflicts.py):
    - per-scope append-only JSONL
    - path-safe construction via safe_slug + _canonical_storage_root
    - no LLM involvement, no automation beyond caller-requested writes
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


@dataclass
class BatonEvent:
    """One lifecycle event in a baton's history.

    Kinds:
        "created"        — baton ingested (optional; not all ingests log).
        "consumed"       — resolve_baton fired. Primary Block A kind.
        "expired_notice" — reserved for future session-start aging hook.
                           Not emitted by Block A.
    """
    event_id: str
    workspace_id: str
    agent_id: str
    eid: int
    kind: str
    ts: int
    outcome: Optional[str] = None
    resolver: Optional[str] = None
    owner: Optional[str] = None


class BatonLedger:
    """Append-only per-(workspace, agent) baton lifecycle event store.

    NOT a state store — payload["baton_lifecycle"] is the source of
    truth for current status. This class exists purely to record the
    event history.
    """

    def __init__(self, data_dir: str, workspace_id: str, agent_id: str) -> None:
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
        self.path = _child_path(agent_root, "baton_events.jsonl")

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes agent root: {rp!r}")
        return rp

    def add_event(self, event: BatonEvent) -> None:
        """Append one event to the ledger. The only write operation."""
        with open(self._guard(self.path), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    def list_events(
        self,
        eid: Optional[int] = None,
        kind: Optional[str] = None,
        limit: int = 500,
    ) -> List[BatonEvent]:
        """Read events from the ledger with optional filters.

        Order: append order (oldest first). If the file contains more
        than `limit` events after filtering, the last `limit` are
        returned (most recent).

        Malformed JSONL lines are skipped silently — the ledger is
        read-forgiving so a single corrupted event cannot hide the
        rest of the history.
        """
        events: List[BatonEvent] = []
        if not os.path.exists(self.path):
            return events
        with open(self._guard(self.path), "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    e = BatonEvent(**obj)
                except Exception:
                    continue
                if eid is not None and int(e.eid) != int(eid):
                    continue
                if kind is not None and e.kind != kind:
                    continue
                events.append(e)
        if len(events) > limit:
            events = events[-limit:]
        return events

    # ------------------------------------------------------------------
    # Helpers — convenient constructors. Callers can build BatonEvent
    # directly; these just fill in event_id + ts so the call site stays
    # small. No other behavior difference.
    # ------------------------------------------------------------------

    def build_consumed_event(
        self,
        eid: int,
        outcome: str,
        resolver: str,
        owner: Optional[str] = None,
    ) -> BatonEvent:
        return BatonEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            agent_id=self.agent_id,
            eid=int(eid),
            kind="consumed",
            ts=_now_ts(),
            outcome=outcome,
            resolver=resolver,
            owner=owner,
        )
