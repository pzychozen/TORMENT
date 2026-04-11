# torment_service/migration/wet_run.py
"""
Wet-run orchestrator for WRITE_MIGRATION commit B.

This module is the thin bridge between a live ``MemoryGraph`` (or any
row-source that yields ``(eid, raw_provenance)`` tuples) and the
already-ratified decision pipeline:

    classify_row  →  decide_admission  →  decide_rerun  →  apply_row

No new decision logic lives here. The orchestrator's only job is to
walk rows, invoke the pipeline in the fixed order, and accumulate a
``WetRunReport`` of what the writer did. All monotonicity, class-6/7
evidence-gating, and cursor-vs-row anomaly handling stays inside
``apply_row`` where it can be tested in isolation.

Graph iterator
--------------

Per the Decision 6 choice ratified by the user, the graph-coupled
iterator lives **inside** this module rather than being pushed into
``dry_run.py``. ``dry_run.py`` is corpus-agnostic — it takes any
iterable of ``(eid, raw)`` tuples — and we keep it that way. ``wet_run``
adds a single helper, ``iter_graph_rows``, that knows how to read a
live ``MemoryGraph`` and produce the same tuple shape. Tests can either
pass a synthetic iterator directly to ``run_wet_run`` or wrap a stub
graph with ``iter_graph_rows``.

Cursor is a resume aid, not primary truth
-----------------------------------------

When ``skip_processed=True``, rows whose EID appears anywhere in the
cursor file are not yielded by the iterator at all — this is the fast
path that lets a wet-run resume after a crash without re-entering
``apply_row`` for already-processed rows. The authoritative idempotency
check still lives in ``apply_row`` precondition 6 (stored row state
must match the expected post-apply admission triple). So the cursor
skip here is only an optimisation: even if it were disabled, the
writer would still produce the same outcome — it would just do more
work.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from .apply import (
    APPLY_ACTION_APPLIED,
    APPLY_ACTION_BLOCKED_REVIEW,
    APPLY_ACTION_SKIPPED_ALREADY_APPLIED,
    APPLY_ACTION_SKIPPED_ANOMALY,
    APPLY_ACTION_SKIPPED_BUMP_ONLY,
    APPLY_ACTION_SKIPPED_PRECONDITION,
    ApplyResult,
    apply_row,
)
from .constants import ADMISSION_POLICY_VERSION
from .cursor import processed_eids
from .gate1_recovery import classify_row
from .gate2_admission import decide_admission
from .rerun_policy import StoredAdmissionState, decide_rerun


# ── Graph iterator ──────────────────────────────────────────────────

def iter_graph_rows(graph: Any) -> Iterator[Tuple[int, Any]]:
    """Yield ``(eid, raw_provenance)`` tuples from a live ``MemoryGraph``.

    The iterator reads ``graph.entities`` and, for each entity, pulls
    the raw provenance value out of ``entity.payload``. ``raw`` is
    whatever is stored — a dict, a legacy bare string, ``None``, or a
    truncated artifact — exactly as the classifier will see it on the
    next run. No coercion, no filtering.

    Walked in sorted EID order so the wet-run is deterministic across
    runs on the same graph.
    """
    entities = getattr(graph, "entities", None)
    if entities is None:
        return
    for eid in sorted(entities.keys()):
        ent = entities[eid]
        payload = getattr(ent, "payload", None) or {}
        raw = payload.get("provenance") if isinstance(payload, dict) else None
        yield (int(eid), raw)


# ── Report shapes ───────────────────────────────────────────────────

@dataclass
class WetRunRowOutcome:
    """One writer decision, suitable for JSON serialisation."""
    eid: int
    action: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {"eid": self.eid, "action": self.action, "reason": self.reason}


@dataclass
class WetRunReport:
    """Structured summary of a wet-run pass.

    Counts mirror the writer action vocabulary one-for-one plus a
    ``rows_scanned`` total, so operators can reconcile the numbers
    without re-reading every per-row outcome.

    ``rows`` is the per-row breakdown. It is populated unconditionally
    and used by tests to assert specific EIDs got the expected action;
    the CLI can opt to strip it before writing the report if it grows
    unwieldy on large corpora.
    """
    policy_version: str = ADMISSION_POLICY_VERSION
    generated_at: Optional[str] = None

    rows_scanned: int = 0
    applied: int = 0
    blocked_for_review: int = 0
    skipped_bump_only: int = 0
    skipped_already_applied: int = 0
    skipped_precondition: int = 0
    skipped_anomaly: int = 0

    rows: List[WetRunRowOutcome] = field(default_factory=list)

    def record(self, result: ApplyResult) -> None:
        """Increment the counter matching ``result.action`` and append
        the per-row outcome."""
        self.rows_scanned += 1
        self.rows.append(
            WetRunRowOutcome(
                eid=result.eid,
                action=result.action,
                reason=result.reason,
            )
        )
        if result.action == APPLY_ACTION_APPLIED:
            self.applied += 1
        elif result.action == APPLY_ACTION_BLOCKED_REVIEW:
            self.blocked_for_review += 1
        elif result.action == APPLY_ACTION_SKIPPED_BUMP_ONLY:
            self.skipped_bump_only += 1
        elif result.action == APPLY_ACTION_SKIPPED_ALREADY_APPLIED:
            self.skipped_already_applied += 1
        elif result.action == APPLY_ACTION_SKIPPED_PRECONDITION:
            self.skipped_precondition += 1
        elif result.action == APPLY_ACTION_SKIPPED_ANOMALY:
            self.skipped_anomaly += 1
        # Unknown actions are intentionally not silently counted: if
        # apply.py ever grows a new action, the mismatch between
        # rows_scanned and the bucket sum will surface it in tests.

    def to_dict(self, include_rows: bool = True) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "policy_version": self.policy_version,
            "generated_at": self.generated_at,
            "counts": {
                "rows_scanned": self.rows_scanned,
                "applied": self.applied,
                "blocked_for_review": self.blocked_for_review,
                "skipped_bump_only": self.skipped_bump_only,
                "skipped_already_applied": self.skipped_already_applied,
                "skipped_precondition": self.skipped_precondition,
                "skipped_anomaly": self.skipped_anomaly,
            },
        }
        if include_rows:
            out["rows"] = [r.to_dict() for r in self.rows]
        return out

    def to_json(self, indent: int = 2, include_rows: bool = True) -> str:
        return json.dumps(
            self.to_dict(include_rows=include_rows),
            indent=indent,
            ensure_ascii=False,
        )


# ── Orchestrator ────────────────────────────────────────────────────

def run_wet_run(
    graph: Any,
    rows: Iterable[Tuple[int, Any]],
    *,
    workspace_root: str,
    skip_processed: bool = True,
) -> WetRunReport:
    """Run the writer pipeline over ``rows`` against ``graph``.

    Parameters
    ----------
    graph
        The row-writing primitive target. Must expose
        ``update_payload(eid, patch)``. In live runs this is a
        ``MemoryGraph``; in tests it can be any stub with the same
        method.
    rows
        An iterable of ``(eid, raw_provenance)`` tuples. In live use,
        the caller passes ``iter_graph_rows(graph)``. In tests, the
        caller can pass any generator — which is why the graph and the
        row source are separate parameters rather than the orchestrator
        deriving one from the other.
    workspace_root
        The workspace directory under which
        ``.torment_migration/cursor.jsonl`` and
        ``.torment_migration/review_queue.jsonl`` live. Passed straight
        through to ``apply_row``.
    skip_processed
        When True (default), rows whose EID already has any cursor
        entry are skipped by the orchestrator without entering
        ``apply_row``. This is the fast-resume path. When False, every
        row in ``rows`` is sent through ``apply_row``; the writer's
        own precondition-6 cross-check still guarantees idempotency.

    Returns
    -------
    WetRunReport
        Populated with per-row outcomes and aggregate counts. The
        report is returned even if ``apply_row`` logged anomalies — the
        orchestrator never aborts early on individual-row failures.
    """
    report = WetRunReport()
    report.generated_at = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    skip_set: set = set()
    if skip_processed:
        skip_set = processed_eids(workspace_root)

    for eid, raw in rows:
        if eid in skip_set:
            # Fast-resume skip. The row is not counted in rows_scanned
            # because it was not actually scanned this pass — it was
            # resolved by a prior pass. The cursor file is the audit
            # record for it.
            continue

        # Decision pipeline — identical to the dry-run order. If any
        # of these raise, the exception propagates: the orchestrator
        # does not swallow pipeline bugs, it only tolerates per-row
        # writer refusals (which come back as ApplyResult actions).
        g1 = classify_row(raw, eid=eid)
        g2 = decide_admission(g1)

        stored_state = _stored_admission_state(raw)
        rerun_decision = decide_rerun(stored_state, g2)

        result = apply_row(
            graph,
            eid,
            raw if isinstance(raw, dict) else None,
            g1,
            g2,
            rerun_decision,
            workspace_root=workspace_root,
        )
        report.record(result)

    return report


def _stored_admission_state(raw: Any) -> StoredAdmissionState:
    """Extract the admission triple from a raw provenance value.

    For non-dict rows (legacy bare strings, ``None``, etc.) returns the
    all-default state, which ``decide_rerun`` interprets as
    ``FIRST_EVALUATION``. This mirrors the dry-run behaviour so the
    wet-run and dry-run reach the same re-run decision on the same
    row.
    """
    if not isinstance(raw, dict):
        return StoredAdmissionState(
            admission_refused=False,
            admission_reason="",
            admission_policy_version="",
        )
    return StoredAdmissionState(
        admission_refused=bool(raw.get("admission_refused", False)),
        admission_reason=str(raw.get("admission_reason", "")),
        admission_policy_version=str(raw.get("admission_policy_version", "")),
    )
