# torment_service/contest_ledger.py
"""ContestLedger — Track B v0.2 B2-S3 append-only storage + literal replay only.

B2-S3 append-only storage + literal replay only.

NOT load-bearing.
No production caller imports or uses ContestLedger.

No resolver.
No authority overlay.
No target linkage.
No row mutation.
No retrieval influence.
No prompt influence.
No cognition coupling.
No MCP exposure.
No automatic firing.

This module persists immutable ``ContestRecord`` memos (B2-S2) to a single
workspace-scoped append-only JSONL ledger, and reads them back literally. It
mirrors the existing single-file JSONL ledger family
(``closure_ledger.py`` / ``baton_ledger.py``): path-safe construction, append
is the only write, every read walks the file, no in-memory cache.

Two deliberate departures from the event-ledger precedents, for governance
integrity (a contest must never be silently hidden — Inv 14):

  - the reader **fails closed** on a malformed JSON line or an invalid
    ``ContestRecord`` (the event ledgers skip malformed lines silently);
  - the reader **raises** on a duplicate ``contest_id`` rather than silently
    collapsing it.

No fsync and no file locking — matching the existing JSONL ledger precedent.
Storage hardening (``JSONL-NO-FSYNC``, ``NO-MULTI-PROCESS-WRITE-COORDINATION``)
remains parked under Cluster 5.

``ContestRecord`` (and ``ContestLedger``) are provisional working names. This
slice does not open counter-contest events (``contest_events.jsonl``),
target linkage, candidate_handle->eid binding, or any resolver / consumer
wiring — all parked (B2-S4+).
"""
from __future__ import annotations

import json
import os
from typing import List

from .contest_record import ContestRecord
from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


class ContestLedgerError(ValueError):
    """Raised when the ledger detects a storage-integrity violation on read.

    Inherits ``ValueError``. Carries a short ``reason`` code (e.g.
    ``"malformed_line"``, ``"duplicate_contest_id"``) so the failure is
    identifiable without re-inspecting the ledger.
    """

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = str(reason)
        msg = f"ContestLedgerError: {self.reason}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)


class ContestLedger:
    """Append-only, workspace-scoped contest-record ledger.

    Storage:
        ``<data_dir>/workspaces/<workspace_id>/contest_memory/contest_records.jsonl``

    There is NO in-memory cache; every read walks the JSONL. Append is the
    only write. The ledger neither resolves authority nor touches any memory
    row — it persists and returns ``ContestRecord`` memos, nothing else.
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
                f"Workspace contest-ledger path escapes base: {workspace_root!r}"
            )
        os.makedirs(workspace_root, exist_ok=True)
        self._base = workspace_root
        self.path = _child_path(workspace_root, "contest_records.jsonl")

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes contest ledger root: {rp!r}")
        return rp

    # ------------------------------------------------------------------
    # Write — append is the only write operation.
    # ------------------------------------------------------------------

    def append_record(self, record: ContestRecord) -> None:
        """Append one validated ContestRecord. The only write operation.

        Accepts an already-validated ``ContestRecord`` instance ONLY. A raw
        dict is rejected — validation belongs to ``ContestRecord`` (B2-S2),
        and this writer must not become a second schema/validation engine or
        a validation bypass. No duplicate scan, no fsync, no lock.
        """
        if not isinstance(record, ContestRecord):
            raise TypeError(
                "append_record requires a ContestRecord instance, not "
                f"{type(record).__name__}; validate before appending"
            )
        line = json.dumps(record.to_dict(), ensure_ascii=False) + "\n"
        with open(self._guard(self.path), "a", encoding="utf-8") as f:
            f.write(line)

    # ------------------------------------------------------------------
    # Read — literal full-file replay. No cache, no index, no aggregation.
    # ------------------------------------------------------------------

    def list_records(self) -> List[ContestRecord]:
        """Read the full ledger literally, in append order.

        Reconstructs each non-empty line through ``ContestRecord.from_dict``.
        Fails closed: a malformed JSON line or an invalid record raises
        immediately (a malformed line must never silently hide a contest).
        A duplicate ``contest_id`` raises loudly. Empty lines are skipped.
        Returns the literal list of records — never a status view, per-eid
        query, aggregation, or resolved-authority projection.
        """
        records: List[ContestRecord] = []
        if not os.path.exists(self.path):
            return records

        seen_ids: set = set()
        with open(self._guard(self.path), "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ContestLedgerError(
                        "malformed_line", f"line {lineno}: {exc}"
                    ) from None
                # Invalid records raise ContestRecordError (a ValueError)
                # from from_dict — propagated loudly, not swallowed.
                record = ContestRecord.from_dict(obj)
                if record.contest_id in seen_ids:
                    raise ContestLedgerError(
                        "duplicate_contest_id",
                        f"line {lineno}: {record.contest_id}",
                    )
                seen_ids.add(record.contest_id)
                records.append(record)
        return records
