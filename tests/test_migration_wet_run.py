# tests/test_migration_wet_run.py
"""
End-to-end tests for ``torment_service.migration.wet_run``.

These tests cover the commit-B orchestrator against a synthetic graph
stub, plus three load-bearing properties of the whole commit:

  1. **Pipeline correctness** — for a handful of representative rows,
     the orchestrator produces the expected writer actions and the
     stored rows end up in the expected post-apply state.

  2. **Idempotency on resume** — running the orchestrator twice against
     the same graph produces no duplicate writes. The second run is
     short-circuited either by the cursor fast-skip (default
     ``skip_processed=True``) or by ``apply_row``'s precondition-6
     stored-row cross-check (``skip_processed=False``). Both paths
     must produce the same stored state.

  3. **Recursion-guard round-trip** — a row that wet-run refuses must
     be rejected by ``cognition.recursion_guard.recursion_guard_check``
     with ``REASON_MIGRATION_REFUSED`` when that row's EID is handed to
     the guard as a parent. This is the load-bearing invariant that
     makes step-6 writes actually close the laundering gap: the stored
     refusal the migration writes must match the shape the guard looks
     for at writeback time.

The stub graph is deliberately minimal: a dict of ``eid →
_StubEntity`` with a ``payload`` attribute, plus ``update_payload``.
No real ``MemoryGraph``, no file I/O beyond the ``.torment_migration``
cursor/review-queue files the writer itself manages.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cognition.recursion_guard import (
    REASON_MIGRATION_REFUSED,
    recursion_guard_check,
)

from torment_service.migration.apply import (
    APPLY_ACTION_APPLIED,
    APPLY_ACTION_BLOCKED_REVIEW,
    APPLY_ACTION_SKIPPED_ALREADY_APPLIED,
    APPLY_ACTION_SKIPPED_BUMP_ONLY,
    APPLY_ACTION_SKIPPED_PRECONDITION,
)
from torment_service.migration.constants import (
    ADMISSION_POLICY_VERSION,
    SOURCE_GATE1_UNRECOVERABLE,
)
from torment_service.migration.cursor import read_entries
from torment_service.migration.review_queue import read_reviews
from torment_service.migration.wet_run import (
    WetRunReport,
    iter_graph_rows,
    run_wet_run,
)
from torment_service.provenance_v1 import WRITE_MIGRATION


# ── Stub graph ──────────────────────────────────────────────────────

@dataclass
class _StubEntity:
    payload: Dict[str, Any] = field(default_factory=dict)


class _StubGraph:
    """Minimal ``MemoryGraph`` substitute for tests.

    Holds entities in a dict keyed by EID. ``update_payload`` merges
    the patch into the stored payload, mirroring ``MemoryGraph``'s
    behaviour, and appends to ``updates`` so tests can assert on the
    exact patch sequence the writer produced.
    """

    def __init__(self) -> None:
        self.entities: Dict[int, _StubEntity] = {}
        self.updates: List[Dict[str, Any]] = []

    def add(self, eid: int, provenance: Any) -> None:
        payload: Dict[str, Any] = {}
        if provenance is not None:
            payload["provenance"] = provenance
        self.entities[eid] = _StubEntity(payload=payload)

    def update_payload(self, eid: int, patch: Dict[str, Any]) -> None:
        if eid not in self.entities:
            raise KeyError(eid)
        self.entities[eid].payload.update(dict(patch))
        self.updates.append({"eid": eid, "patch": dict(patch)})


# ── Helpers ─────────────────────────────────────────────────────────

def _canonical_provenance(
    *,
    source_type: str,
    source_role: Optional[str] = None,
    parent_eids: Optional[List[int]] = None,
    write_path: str = "direct_ingest",
    **extra: Any,
) -> Dict[str, Any]:
    """Build a dict that gate-1 classify_row will see as already canonical."""
    d: Dict[str, Any] = {
        "schema_version": "v1",
        "source_type": source_type,
        "source_role": source_role,
        "parent_eids": list(parent_eids or []),
        "write_path": write_path,
    }
    d.update(extra)
    return d


def _truncated_provenance(source_type: str) -> Dict[str, Any]:
    """Build a dict that gate-1 classifies as class 3 (dict_truncated,
    RECOVER)."""
    # Missing ``schema_version`` and ``parent_eids`` — truncated.
    return {"source_type": source_type}


def _admission_triple_matches(
    payload: Dict[str, Any],
    *,
    refused: bool,
    reason: str,
    version: str = ADMISSION_POLICY_VERSION,
) -> bool:
    """True iff the row's stored provenance carries the admission triple
    given."""
    prov = payload.get("provenance") or {}
    return (
        bool(prov.get("admission_refused", False)) == refused
        and str(prov.get("admission_reason", "")) == reason
        and str(prov.get("admission_policy_version", "")) == version
    )


# ── Tests ───────────────────────────────────────────────────────────


class TestIterGraphRows(unittest.TestCase):
    """``iter_graph_rows`` produces ``(eid, raw)`` tuples from a graph."""

    def test_empty_graph_yields_nothing(self):
        g = _StubGraph()
        self.assertEqual(list(iter_graph_rows(g)), [])

    def test_rows_yielded_in_sorted_eid_order(self):
        g = _StubGraph()
        g.add(7, _canonical_provenance(source_type="user_input"))
        g.add(3, _canonical_provenance(source_type="memory"))
        g.add(10, None)
        rows = list(iter_graph_rows(g))
        self.assertEqual([eid for eid, _ in rows], [3, 7, 10])

    def test_non_dict_payload_yields_none_raw(self):
        g = _StubGraph()
        # An entity whose payload is outright missing or broken should
        # yield ``raw=None`` rather than raising — gate 1 handles the
        # null/empty case deliberately.
        ent = _StubEntity(payload={})  # no "provenance" key
        g.entities[1] = ent
        rows = list(iter_graph_rows(g))
        self.assertEqual(rows, [(1, None)])


class TestRunWetRunHappyPath(unittest.TestCase):
    """A hand-picked graph exercises each writer action once."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(self._cleanup)

        self.graph = _StubGraph()

        # EID 10: canonical user_input, admittable, first-eval apply
        # path goes through precondition-6 match (no prior apply), so
        # this is the only EID we expect to produce APPLIED.
        #
        # Except: an already-canonical row is GATE1_OUTCOME_SKIP, which
        # hits precondition-2's "class_1_already_canonical" guard and
        # returns SKIPPED_PRECONDITION. So to get APPLIED we need a
        # class-3 (truncated) or class-2 (bare string) row.
        self.graph.add(10, _truncated_provenance("user_input"))

        # EID 11: bare string "user" — class 2 legacy, RECOVER, admit,
        # first-eval → APPLIED.
        self.graph.add(11, "user")

        # EID 12: null provenance — class 5, FAIL, refused → APPLIED
        # with sentinel source_type.
        self.graph.add(12, None)

        # EID 13: already-canonical user_input — skipped by
        # precondition-2 ("class_1_already_canonical"), never written.
        self.graph.add(
            13,
            _canonical_provenance(source_type="user_input"),
        )

        # EID 14: stored refusal whose fresh gate-2 evaluation also
        # refuses (same outcome, new policy version) → BUMP_ONLY.
        # We use a class-3 truncated row with a rejected source_type
        # (collective_echo), which gate 1 RECOVERs and gate 2 refuses
        # under the rejected-set rule. The stored admission triple
        # already carries refused=True on an older policy version, so
        # the rerun decision is BUMP_ONLY (refuse→refuse).
        self.graph.add(
            14,
            {
                "source_type": "collective_echo",
                "admission_refused": True,
                "admission_reason": "source_type_rejected_set",
                "admission_policy_version": "v2.4.x-step5-old",
            },
        )

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_run_produces_expected_action_per_row(self):
        report = run_wet_run(
            self.graph,
            iter_graph_rows(self.graph),
            workspace_root=self.tmp,
        )

        self.assertIsInstance(report, WetRunReport)
        self.assertEqual(report.rows_scanned, 5)

        actions = {r.eid: r.action for r in report.rows}
        self.assertEqual(actions[10], APPLY_ACTION_APPLIED)
        self.assertEqual(actions[11], APPLY_ACTION_APPLIED)
        self.assertEqual(actions[12], APPLY_ACTION_APPLIED)
        self.assertEqual(actions[13], APPLY_ACTION_SKIPPED_PRECONDITION)
        self.assertEqual(actions[14], APPLY_ACTION_SKIPPED_BUMP_ONLY)

        self.assertEqual(report.applied, 3)
        self.assertEqual(report.skipped_precondition, 1)
        self.assertEqual(report.skipped_bump_only, 1)
        self.assertEqual(report.blocked_for_review, 0)
        self.assertEqual(report.skipped_anomaly, 0)
        self.assertEqual(report.skipped_already_applied, 0)

    def test_applied_rows_carry_admission_triple(self):
        run_wet_run(
            self.graph,
            iter_graph_rows(self.graph),
            workspace_root=self.tmp,
        )
        # EID 10 recovered to user_input, admitted.
        self.assertTrue(
            _admission_triple_matches(
                self.graph.entities[10].payload,
                refused=False,
                reason="",
            )
        )
        # EID 12 fell to FAIL → sentinel row with refused=True.
        prov_12 = self.graph.entities[12].payload["provenance"]
        self.assertTrue(prov_12["admission_refused"])
        self.assertEqual(prov_12["source_type"], SOURCE_GATE1_UNRECOVERABLE)
        self.assertEqual(prov_12["write_path"], WRITE_MIGRATION)

    def test_bump_only_row_is_not_rewritten(self):
        run_wet_run(
            self.graph,
            iter_graph_rows(self.graph),
            workspace_root=self.tmp,
        )
        # EID 14 was BUMP_ONLY — no patch sent.
        patches_for_14 = [u for u in self.graph.updates if u["eid"] == 14]
        self.assertEqual(patches_for_14, [])


class TestRunWetRunIdempotencyOnResume(unittest.TestCase):
    """Running the orchestrator twice produces no duplicate writes.

    Covered twice:
      - with ``skip_processed=True``  — cursor fast-skip path
      - with ``skip_processed=False`` — precondition-6 stored-row cross-check
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(self._cleanup)
        self.graph = _StubGraph()
        self.graph.add(101, _truncated_provenance("memory"))
        self.graph.add(102, None)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_resume_with_cursor_skip_no_double_write(self):
        run_wet_run(
            self.graph,
            iter_graph_rows(self.graph),
            workspace_root=self.tmp,
            skip_processed=True,
        )
        first_update_count = len(self.graph.updates)
        first_cursor_count = len(read_entries(self.tmp))

        # Second pass against the same graph + workspace.
        report2 = run_wet_run(
            self.graph,
            iter_graph_rows(self.graph),
            workspace_root=self.tmp,
            skip_processed=True,
        )

        # No extra updates. No extra cursor entries. Second report
        # sees zero rows (they were pre-skipped by the iterator).
        self.assertEqual(len(self.graph.updates), first_update_count)
        self.assertEqual(len(read_entries(self.tmp)), first_cursor_count)
        self.assertEqual(report2.rows_scanned, 0)

    def test_resume_without_cursor_skip_preconditions_hold_the_line(self):
        run_wet_run(
            self.graph,
            iter_graph_rows(self.graph),
            workspace_root=self.tmp,
            skip_processed=False,
        )
        first_update_count = len(self.graph.updates)

        # Second pass: every row re-enters apply_row because we are
        # not using the cursor fast-skip. Both rows are now in a
        # post-apply state that gate 1 sees as class 1 (canonical or
        # sentinel), which apply_row refuses via precondition 2's
        # ``class_1_already_canonical`` branch — that is the narrower
        # structural guarantee than a BUMP_ONLY rerun decision would
        # give, and it is what makes sentinel rows resumable without
        # spuriously tripping loosening review.
        report2 = run_wet_run(
            self.graph,
            iter_graph_rows(self.graph),
            workspace_root=self.tmp,
            skip_processed=False,
        )

        self.assertEqual(len(self.graph.updates), first_update_count)
        self.assertEqual(report2.rows_scanned, 2)
        self.assertEqual(report2.applied, 0)
        self.assertEqual(report2.blocked_for_review, 0)
        self.assertEqual(report2.skipped_anomaly, 0)
        # Both rows are canonical post-apply → class 1 → precondition 2.
        self.assertEqual(report2.skipped_precondition, 2)


class TestRunWetRunRecursionGuardRoundTrip(unittest.TestCase):
    """A wet-run refusal must be rejected by the recursion guard.

    Round-trip flow:
      1. Build a graph with one row that gate 1 cannot recover
         (``None`` provenance, class 5 FAIL).
      2. Run the wet-run orchestrator. The row's stored state now
         carries ``admission_refused=True`` and the sentinel
         ``source_type``.
      3. Feed that EID into ``recursion_guard_check`` as a parent,
         with a ``lookup_fn`` that pulls from the same graph.
      4. Assert the guard returns ``(False, REASON_MIGRATION_REFUSED)``.

    This is the load-bearing end-to-end invariant for the whole commit:
    the migration writes the refusal in the exact shape the guard reads
    at writeback time. Breaking either end breaks the laundering gap.
    """

    def test_refused_row_blocks_recursion_guard(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))

        graph = _StubGraph()
        graph.add(501, None)  # class 5 FAIL → refused by gate 2.

        report = run_wet_run(
            graph,
            iter_graph_rows(graph),
            workspace_root=tmp,
        )
        self.assertEqual(report.applied, 1)

        # Guard lookup_fn pulls the stored payload out of the stub
        # graph exactly like the live guard pulls from ``MemoryGraph``.
        def lookup_fn(_workspace_id: str, _agent_id: str, eid: int) -> Any:
            ent = graph.entities.get(int(eid))
            return ent.payload if ent is not None else None

        ok, reason = recursion_guard_check(
            seed_eids=[501],
            lookup_fn=lookup_fn,
            workspace_id="ws",
            agent_id="agent",
        )
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_MIGRATION_REFUSED)

    def test_admitted_row_passes_recursion_guard(self):
        """Contrast case: a wet-run admit does NOT trip the guard.

        Without this test the round-trip above would pass even if the
        guard unconditionally refused everything. We need both ends of
        the invariant."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))

        graph = _StubGraph()
        graph.add(
            502,
            _truncated_provenance("user_input"),
        )  # class 3 RECOVER → admitted.

        run_wet_run(
            graph,
            iter_graph_rows(graph),
            workspace_root=tmp,
        )

        def lookup_fn(_workspace_id: str, _agent_id: str, eid: int) -> Any:
            ent = graph.entities.get(int(eid))
            return ent.payload if ent is not None else None

        ok, reason = recursion_guard_check(
            seed_eids=[502],
            lookup_fn=lookup_fn,
            workspace_id="ws",
            agent_id="agent",
        )
        # The guard may still reject for other reasons (e.g. the row
        # isn't fully canonical by its own rules), but it must not
        # reject with REASON_MIGRATION_REFUSED — that reason is
        # reserved for rows the migration itself refused.
        self.assertNotEqual(reason, REASON_MIGRATION_REFUSED)


class TestRunWetRunBlockAndReviewPath(unittest.TestCase):
    """A stale-refusal row that would loosen under the current policy
    gets enqueued for review, not written."""

    def test_loosening_row_enqueues_review_and_skips_write(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))

        graph = _StubGraph()
        # A row whose stored state says "refused" but whose current
        # gate-2 evaluation says "admit". We build a canonical
        # user_input row (gate 1 SKIP, gate 2 admit) with a stored
        # refusal flag on top — the rerun_policy sees this as loosening.
        #
        # NOTE: a GATE1_OUTCOME_SKIP row hits precondition-2's
        # already_canonical guard before the rerun branch is reached,
        # so we use a class-3 truncated row instead. gate 1 RECOVERs it
        # to user_input; gate 2 admits it. Stored state says refused →
        # rerun decision is BLOCK_AND_REVIEW.
        graph.add(
            601,
            {
                "source_type": "user_input",  # class 3 — missing canonical markers
                "admission_refused": True,
                "admission_reason": "some_old_reason",
                "admission_policy_version": "v2.4.x-step5-old",
            },
        )

        report = run_wet_run(
            graph,
            iter_graph_rows(graph),
            workspace_root=tmp,
        )

        actions = {r.eid: r.action for r in report.rows}
        self.assertEqual(actions[601], APPLY_ACTION_BLOCKED_REVIEW)

        # No update sent to the graph for this row.
        self.assertEqual(
            [u for u in graph.updates if u["eid"] == 601],
            [],
        )

        # Exactly one review queue entry, for EID 601.
        reviews = read_reviews(tmp)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].eid, 601)
        self.assertTrue(reviews[0].stored_admission_refused)
        self.assertFalse(reviews[0].current_admission_refused)


class TestWetRunReportSerialisation(unittest.TestCase):
    """The report's ``to_dict`` shape is stable and covers the counter
    vocabulary."""

    def test_to_dict_includes_all_counters(self):
        r = WetRunReport()
        d = r.to_dict(include_rows=True)
        self.assertIn("counts", d)
        counts = d["counts"]
        expected_keys = {
            "rows_scanned",
            "applied",
            "blocked_for_review",
            "skipped_bump_only",
            "skipped_already_applied",
            "skipped_precondition",
            "skipped_anomaly",
        }
        self.assertEqual(set(counts.keys()), expected_keys)
        self.assertIn("policy_version", d)
        self.assertEqual(d["policy_version"], ADMISSION_POLICY_VERSION)

    def test_to_dict_can_exclude_rows(self):
        r = WetRunReport()
        d = r.to_dict(include_rows=False)
        self.assertNotIn("rows", d)


if __name__ == "__main__":
    unittest.main()
