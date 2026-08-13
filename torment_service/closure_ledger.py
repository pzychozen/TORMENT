# torment_service/closure_ledger.py
"""
Append-only per-workspace closure lifecycle event ledger.

Block C (docs/BLOCK_C_DESIGN.md §5.3 + §6.6). Audit trail + raw lifecycle
evidence. The non-mutating Closure reconciler derives trusted operational
state only when Store payload and Ledger evidence agree.

=== WATCH-ITEM HONORED LITERALLY ===
`get_latest_event_kind(closure_id)` remains a literal forensic lookup of the
last event appended for the closure. Trusted operational state is a separate,
explicit reconciliation projection over Store + Ledger evidence; raw rows are
never rewritten or hidden by that projection.

=== §7.3 HONORED LITERALLY ===
Distinct JSONL file at
`<data_dir>/workspaces/<ws>/closure_memory/closure_events.jsonl`.
NEVER shared with:
    - <ws>/agents/<agent>/baton_events.jsonl
    - <ws>/agents/<agent>/reference_load_events.jsonl
    - <ws>/environment_memory/events.jsonl
    - any archivist / writeback audit file
    - ClosureStore's `events.jsonl` (that's internal store events,
      not lifecycle events)

Modeled on BatonLedger / ReferenceLoadLedger / EnvironmentEventLedger.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


def _now_ts() -> int:
    return int(time.time())


# Valid lifecycle event kinds — literal vocabulary, no free-text. The
# fabric methods each append exactly one kind from this set.
EVENT_PROPOSED  = "proposed"
EVENT_RATIFIED  = "ratified"
EVENT_COMMITTED = "committed"
EVENT_REVISED   = "revised"

VALID_EVENT_KINDS = frozenset({
    EVENT_PROPOSED,
    EVENT_RATIFIED,
    EVENT_COMMITTED,
    EVENT_REVISED,
})


@dataclass
class ClosureEvent:
    """One lifecycle event for one closure.

    Each event carries the ProvenanceV1 dict for the event and the
    ratifier (populated for ratified / committed / revised; None on
    the initial proposed event). ``version_id`` pairs proposed,
    committed, and revised events to payload versions; ratification
    is intentionally closure-bound and versionless.
    """
    event_id: str
    workspace_id: str
    closure_id: str
    version_id: Optional[str]     # proposed / committed / revised → version
    kind: str                     # one of VALID_EVENT_KINDS
    ts: int
    ratifier: Optional[str]       # required on ratified/committed/revised
    provenance: Dict[str, Any]    # ProvenanceV1.for_closure_* dict
    notes: Optional[str] = None


class ClosureLedger:
    """Append-only per-workspace closure lifecycle ledger.

    Two roles:
        1. Audit trail — every lifecycle state change appends one event.
        2. Raw lifecycle evidence — `get_latest_event_kind(closure_id)`
           returns the literal last-event kind for forensic inspection.

    There is NO in-memory event cache. Every read walks the JSONL.
    This keeps the ledger a flat truth source; any concurrent writer
    (future milestone) that appends a new event is immediately visible
    to subsequent reads without a separate invalidate step.
    """

    def __init__(self, data_dir: str, workspace_id: str) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.data_dir = _canonical_storage_root(data_dir)

        workspace_root = os.path.realpath(
            os.path.join(self.data_dir, "workspaces",
                         self.workspace_id, "closure_memory")
        )
        if not workspace_root.startswith(self.data_dir + os.sep):
            raise ValueError(
                f"Workspace closure-ledger path escapes base: "
                f"{workspace_root!r}"
            )
        os.makedirs(workspace_root, exist_ok=True)
        self._base = workspace_root

        # Distinct file per §7.3. Never shared with ClosureStore's
        # internal events.jsonl.
        self.path = _child_path(workspace_root, "closure_events.jsonl")

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes closure ledger root: {rp!r}")
        return rp

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def add_event(self, event: ClosureEvent) -> None:
        """Append one event. Rejects unknown kinds."""
        if event.kind not in VALID_EVENT_KINDS:
            raise ValueError(
                f"Invalid closure event kind {event.kind!r}; "
                f"must be one of {sorted(VALID_EVENT_KINDS)}"
            )
        with open(self._guard(self.path), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Reads — literal event-kind lookup, no inference
    # ------------------------------------------------------------------

    def list_events(
        self,
        closure_id: Optional[str] = None,
        kind: Optional[str] = None,
        limit: Optional[int] = 500,
    ) -> List[ClosureEvent]:
        """Read events from the ledger with optional filters.

        Order: append order (oldest first). If the filtered result
        exceeds `limit`, the LAST `limit` events are returned
        (most recent), matching the BatonLedger pattern. Pass ``None``
        for the complete forensic history.

        Malformed JSONL lines are skipped silently — a corrupted event
        cannot hide the rest of the history.
        """
        events: List[ClosureEvent] = []
        if not os.path.exists(self.path):
            return events
        with open(self._guard(self.path), "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    e = ClosureEvent(
                        event_id=obj["event_id"],
                        workspace_id=obj["workspace_id"],
                        closure_id=obj["closure_id"],
                        version_id=obj.get("version_id"),
                        kind=obj["kind"],
                        ts=int(obj.get("ts", 0)),
                        ratifier=obj.get("ratifier"),
                        provenance=obj.get("provenance", {}),
                        notes=obj.get("notes"),
                    )
                except Exception:
                    continue
                if closure_id is not None and e.closure_id != closure_id:
                    continue
                if kind is not None and e.kind != kind:
                    continue
                events.append(e)
        if limit is not None and len(events) > limit:
            events = events[-limit:]
        return events

    def get_latest_event_kind(self, closure_id: str) -> Optional[str]:
        """Return the `kind` of the last event for this closure_id.

        This is the LITERAL forensic event-kind lookup. It performs no
        Store/Ledger validation or reconstruction; use Fabric's named
        trusted-current read for operational lifecycle state.

        Returns None if no events exist for this closure_id (i.e., the
        closure does not exist).
        """
        events = self.list_events(closure_id=closure_id)
        if not events:
            return None
        return events[-1].kind

    def has_ratification(self, closure_id: str) -> bool:
        """Return True iff raw forensic history contains `ratified`.

        Trusted mutation gates use Closure reconciliation rather than this
        raw-history predicate.
        """
        return any(
            e.kind == EVENT_RATIFIED
            for e in self.list_events(closure_id=closure_id)
        )

    # ------------------------------------------------------------------
    # Build helpers — small constructors so fabric method bodies stay
    # focused on policy, not event-assembly boilerplate. Same pattern
    # as BatonLedger.build_consumed_event.
    # ------------------------------------------------------------------

    def build_proposed_event(
        self,
        closure_id: str,
        version_id: str,
        provenance: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> ClosureEvent:
        return ClosureEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            closure_id=closure_id,
            version_id=version_id,
            kind=EVENT_PROPOSED,
            ts=_now_ts(),
            ratifier=None,
            provenance=provenance,
            notes=notes,
        )

    def build_ratified_event(
        self,
        closure_id: str,
        ratifier: str,
        provenance: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> ClosureEvent:
        return ClosureEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            closure_id=closure_id,
            version_id=None,
            kind=EVENT_RATIFIED,
            ts=_now_ts(),
            ratifier=ratifier,
            provenance=provenance,
            notes=notes,
        )

    def build_committed_event(
        self,
        closure_id: str,
        version_id: str,
        ratifier: str,
        provenance: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> ClosureEvent:
        return ClosureEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            closure_id=closure_id,
            version_id=version_id,
            kind=EVENT_COMMITTED,
            ts=_now_ts(),
            ratifier=ratifier,
            provenance=provenance,
            notes=notes,
        )

    def build_revised_event(
        self,
        closure_id: str,
        version_id: str,
        ratifier: str,
        provenance: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> ClosureEvent:
        return ClosureEvent(
            event_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            closure_id=closure_id,
            version_id=version_id,
            kind=EVENT_REVISED,
            ts=_now_ts(),
            ratifier=ratifier,
            provenance=provenance,
            notes=notes,
        )
