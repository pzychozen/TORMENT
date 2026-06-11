# torment_service/contest_event_ledger.py
"""ContestEventLedger — Track B v0.2 B2-S4 append-only counter-contest event
storage + literal replay only.

B2-S4 append-only counter-contest event storage + literal replay only.

NOT load-bearing.
No production caller imports or uses ContestEventLedger.

No resolver.
No effective-authority computation.
No status / verdict / precedence derivation.
No latest-wins behavior.
No count-as-signal behavior.
No target-existence lookup.
No row mutation.
No retrieval influence.
No prompt influence.
No cognition coupling.
No MCP exposure.
No automatic firing.

This module persists immutable ``CounterContestEvent`` records (B2-S4) to a
single workspace-scoped append-only JSONL ledger, sibling to the B2-S3
``contest_records.jsonl``, and reads them back literally. It mirrors the
existing single-file JSONL ledger family (``closure_ledger.py`` /
``baton_ledger.py``) and the B2-S3 ``contest_ledger.py``: path-safe
construction, append is the only write, every read walks the file, no in-memory
cache.

The reader is purely literal and observational. ``list_events`` returns the
full append-ordered history; ``list_events_for_contest`` returns the literal
events whose ``target_contest_id`` matches, in append order, and NOTHING more.
Append order is *chronology only* — it is never precedence, ranking weight, or
authority. *Literal linked-event replay != authority resolver.*

Two deliberate departures from the event-ledger precedents, for governance
integrity (a contest must never be silently hidden — Track B v0.1 Inv 14,
carried by B2-S3):

  - the reader **fails closed** on a malformed JSON line or an invalid
    ``CounterContestEvent`` (the closure/baton event ledgers skip malformed
    lines silently);
  - the reader **raises** on a duplicate ``event_id`` rather than silently
    collapsing it.

No fsync and no file locking — matching the existing JSONL ledger precedent.
Storage hardening (``JSONL-NO-FSYNC``, ``NO-MULTI-PROCESS-WRITE-COORDINATION``)
remains parked under Cluster 5.

This slice does not resolve, rank, or apply anything; target-existence policy,
dangling-linkage policy, counter-contest result routing, candidate_handle->eid
binding, and any consumer wiring are all parked.
"""
from __future__ import annotations

import json
import os
from typing import List

from .counter_contest_event import CounterContestEvent
from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


def _is_uuid_shaped(value) -> bool:
    """True iff ``value`` is a non-empty string parseable as a UUID.

    Used only to structurally validate the ``contest_id`` *query argument* of
    ``list_events_for_contest``. This is a query-shape check, NOT a
    target-existence check (existence is parked).
    """
    import uuid as _uuid
    if not isinstance(value, str) or not value:
        return False
    try:
        _uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return True


class ContestEventLedgerError(ValueError):
    """Raised when the ledger detects a storage-integrity violation on read,
    or a malformed query argument.

    Inherits ``ValueError``. Carries a short ``reason`` code (e.g.
    ``"malformed_line"``, ``"duplicate_event_id"``,
    ``"bad_target_contest_id"``) so the failure is identifiable without
    re-inspecting the ledger.
    """

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = str(reason)
        msg = f"ContestEventLedgerError: {self.reason}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)


class ContestEventLedger:
    """Append-only, workspace-scoped counter-contest event ledger.

    Storage:
        ``<data_dir>/workspaces/<workspace_id>/contest_memory/contest_events.jsonl``

    There is NO in-memory cache; every read walks the JSONL. Append is the only
    write. The ledger neither resolves authority nor touches any memory row or
    ContestRecord — it persists and returns ``CounterContestEvent`` records,
    nothing else.
    """

    def __init__(self, data_dir: str, workspace_id: str) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.data_dir = _canonical_storage_root(data_dir)

        workspace_root = os.path.realpath(
            os.path.join(self.data_dir, "workspaces",
                         self.workspace_id, "contest_memory")
        )
        if not workspace_root.startswith(self.data_dir + os.sep):
            raise ValueError(
                f"Workspace contest-event-ledger path escapes base: {workspace_root!r}"
            )
        os.makedirs(workspace_root, exist_ok=True)
        self._base = workspace_root
        self.path = _child_path(workspace_root, "contest_events.jsonl")

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes contest event ledger root: {rp!r}")
        return rp

    # ------------------------------------------------------------------
    # Write — append is the only write operation.
    # ------------------------------------------------------------------

    def append_event(self, event: CounterContestEvent) -> None:
        """Append one validated CounterContestEvent. The only write operation.

        Accepts an already-validated ``CounterContestEvent`` instance ONLY. A
        raw dict is rejected — validation belongs to ``CounterContestEvent``
        (B2-S4), and this writer must not become a second validation engine or
        a validation bypass. No ID generation, no duplicate scan, no target
        lookup, no fsync, no lock.
        """
        if not isinstance(event, CounterContestEvent):
            raise TypeError(
                "append_event requires a CounterContestEvent instance, not "
                f"{type(event).__name__}; validate before appending"
            )
        line = json.dumps(event.to_dict(), ensure_ascii=False) + "\n"
        with open(self._guard(self.path), "a", encoding="utf-8") as f:
            f.write(line)

    # ------------------------------------------------------------------
    # Read — literal full-file replay. No cache, no index, no aggregation,
    # no derived status, no latest-wins, no count-as-signal.
    # ------------------------------------------------------------------

    def list_events(self) -> List[CounterContestEvent]:
        """Read the full ledger literally, in append order (chronology only).

        Reconstructs each non-empty line through ``CounterContestEvent.from_dict``.
        Fails closed: a malformed JSON line or an invalid event raises
        immediately (a malformed line must never silently hide a contest). A
        duplicate ``event_id`` raises loudly. Empty lines are skipped. Returns
        the literal list of events — never a status view, effective view,
        winner, precedence, or resolved-authority projection.
        """
        events: List[CounterContestEvent] = []
        if not os.path.exists(self.path):
            return events

        seen_ids: set = set()
        with open(self._guard(self.path), "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ContestEventLedgerError(
                        "malformed_line", f"line {lineno}: {exc}"
                    ) from None
                # Invalid events raise CounterContestEventError (a ValueError)
                # from from_dict — propagated loudly, not swallowed.
                event = CounterContestEvent.from_dict(obj)
                if event.event_id in seen_ids:
                    raise ContestEventLedgerError(
                        "duplicate_event_id",
                        f"line {lineno}: {event.event_id}",
                    )
                seen_ids.add(event.event_id)
                events.append(event)
        return events

    def list_events_for_contest(self, contest_id: str) -> List[CounterContestEvent]:
        """Return the literal events whose ``target_contest_id`` matches
        ``contest_id``, in append order.

        ``contest_id`` is validated for UUID shape only (a query-shape check,
        NOT a target-existence check — existence is parked). This is linkage
        observation, not status derivation: append order is chronology only,
        never precedence; there is no latest-wins behavior, no count-as-signal,
        and no target-existence lookup. A structurally valid ``contest_id`` that
        matches no ContestRecord simply yields its literal linked events (which
        may be empty) — dangling linkage remains representable, never resolved.
        """
        if not _is_uuid_shaped(contest_id):
            raise ContestEventLedgerError(
                "bad_target_contest_id", repr(contest_id)
            )
        return [
            event for event in self.list_events()
            if event.target_contest_id == contest_id
        ]
