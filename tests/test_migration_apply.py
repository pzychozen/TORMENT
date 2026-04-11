# tests/test_migration_apply.py
"""
Unit tests for ``torment_service.migration.apply``.

One test per precondition branch of ``apply_row``, plus a happy-path
test per gate-1 outcome, plus a monotonicity property test, plus a
cursor-vs-row anomaly test that verifies the writer treats the cursor
as secondary and the row state as primary.

The tests use a ``StubGraph`` that records every ``update_payload``
call without touching any real storage. Tests that need a workspace
root use ``tempfile.TemporaryDirectory``.
"""
from __future__ import annotations

import tempfile
import unittest
from typing import Any, Dict, List, Optional, Tuple

from torment_service.provenance_v1 import (
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_DERIVED,
    SOURCE_GATE1_UNRECOVERABLE,
    SOURCE_MEMORY,
    SOURCE_USER_INPUT,
    WRITE_MIGRATION,
    ProvenanceV1,
)

from torment_service.migration.apply import (
    APPLY_ACTION_APPLIED,
    APPLY_ACTION_BLOCKED_REVIEW,
    APPLY_ACTION_SKIPPED_ALREADY_APPLIED,
    APPLY_ACTION_SKIPPED_ANOMALY,
    APPLY_ACTION_SKIPPED_BUMP_ONLY,
    APPLY_ACTION_SKIPPED_PRECONDITION,
    apply_row,
)
from torment_service.migration.constants import (
    ADMISSION_POLICY_VERSION,
    ADMISSION_REASON_GATE1_UNRECOVERABLE,
    ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET,
    GATE1_CLASS_ALREADY_CANONICAL,
    GATE1_CLASS_DEPRECATED_VOCABULARY,
    GATE1_CLASS_DICT_INVALID_TYPE,
    GATE1_CLASS_DICT_TRUNCATED,
    GATE1_CLASS_LEGACY_BARE_STRING,
    GATE1_CLASS_ZERO_EVENT_ARTIFACT,
    GATE1_OUTCOME_FAIL,
    GATE1_OUTCOME_RECOVER,
    GATE1_OUTCOME_SKIP,
    RERUN_DECISION_APPLY,
    RERUN_DECISION_BLOCK_AND_REVIEW,
    RERUN_DECISION_BUMP_ONLY,
    RERUN_DECISION_FIRST_EVALUATION,
)
from torment_service.migration.cursor import (
    CURSOR_ACTION_APPLIED,
    CursorEntry,
    append_entry,
    read_entries,
)
from torment_service.migration.gate1_recovery import Gate1Result
from torment_service.migration.gate2_admission import Gate2Result
from torment_service.migration.rerun_policy import RerunDecision
from torment_service.migration.review_queue import read_reviews


# ── Test fixtures ────────────────────────────────────────────────────

class StubGraph:
    """Recording stub for ``MemoryGraph.update_payload``. Does not touch
    any real storage. Each call is captured as a ``(eid, patch)`` tuple
    in ``calls`` so tests can assert exact call shape and ordering.
    """

    def __init__(self, fail_on: Optional[int] = None) -> None:
        self.calls: List[Tuple[int, Dict[str, Any]]] = []
        self.fail_on = fail_on

    def update_payload(self, eid: int, patch: Dict[str, Any]) -> None:
        if self.fail_on is not None and eid == self.fail_on:
            raise RuntimeError(f"stub graph: forced failure on eid={eid}")
        self.calls.append((int(eid), dict(patch)))


def _recover_gate1(
    *,
    class_id: int = GATE1_CLASS_DICT_TRUNCATED,
    source_type: str = SOURCE_MEMORY,
    source_role: Optional[str] = None,
    parent_eids: Optional[List[int]] = None,
) -> Gate1Result:
    return Gate1Result(
        class_id=class_id,
        outcome=GATE1_OUTCOME_RECOVER,
        recovered_source_type=source_type,
        recovered_source_role=source_role,
        recovered_parent_eids=list(parent_eids or []),
        recovery_notes="test_fixture_recover",
        raw_original={"source_type": source_type},
    )


def _fail_gate1(
    *,
    class_id: int = GATE1_CLASS_DICT_INVALID_TYPE,
) -> Gate1Result:
    return Gate1Result(
        class_id=class_id,
        outcome=GATE1_OUTCOME_FAIL,
        recovered_source_type=None,
        recovered_source_role=None,
        recovered_parent_eids=[],
        recovery_notes="test_fixture_fail",
        raw_original=None,
    )


def _skip_gate1() -> Gate1Result:
    return Gate1Result(
        class_id=GATE1_CLASS_ALREADY_CANONICAL,
        outcome=GATE1_OUTCOME_SKIP,
        recovered_source_type=None,
        recovered_source_role=None,
        recovered_parent_eids=[],
        recovery_notes="test_fixture_skip",
        raw_original={"source_type": SOURCE_USER_INPUT},
    )


def _admit_gate2() -> Gate2Result:
    return Gate2Result(
        admitted=True,
        reason="",
        policy_version=ADMISSION_POLICY_VERSION,
    )


def _refuse_gate2(reason: str = ADMISSION_REASON_GATE1_UNRECOVERABLE) -> Gate2Result:
    return Gate2Result(
        admitted=False,
        reason=reason,
        policy_version=ADMISSION_POLICY_VERSION,
    )


def _first_eval_admit() -> RerunDecision:
    return RerunDecision(
        action=RERUN_DECISION_FIRST_EVALUATION,
        new_admission_refused=False,
        new_admission_reason="",
        new_admission_policy_version=ADMISSION_POLICY_VERSION,
    )


def _first_eval_refuse(reason: str = ADMISSION_REASON_GATE1_UNRECOVERABLE) -> RerunDecision:
    return RerunDecision(
        action=RERUN_DECISION_FIRST_EVALUATION,
        new_admission_refused=True,
        new_admission_reason=reason,
        new_admission_policy_version=ADMISSION_POLICY_VERSION,
    )


def _apply_tighten(reason: str = ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET) -> RerunDecision:
    return RerunDecision(
        action=RERUN_DECISION_APPLY,
        new_admission_refused=True,
        new_admission_reason=reason,
        new_admission_policy_version=ADMISSION_POLICY_VERSION,
    )


def _bump_only() -> RerunDecision:
    return RerunDecision(
        action=RERUN_DECISION_BUMP_ONLY,
        new_admission_refused=False,
        new_admission_reason="",
        new_admission_policy_version=ADMISSION_POLICY_VERSION,
    )


def _block_and_review() -> RerunDecision:
    return RerunDecision(
        action=RERUN_DECISION_BLOCK_AND_REVIEW,
        new_admission_refused=True,  # stored refused is preserved
        new_admission_reason="legacy_refusal_reason",
        new_admission_policy_version="v2.4.x-step6-a",
    )


# ── Happy-path tests ─────────────────────────────────────────────────

class TestApplyRowHappyPath(unittest.TestCase):
    """One happy-path test per gate-1 outcome that reaches the writer."""

    def test_first_eval_admit_recover(self) -> None:
        """RECOVER + admit on a fresh row → APPLIED with recovered fields."""
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=42,
                stored_prov={},
                fresh_g1=_recover_gate1(source_type=SOURCE_MEMORY, parent_eids=[7, 11]),
                fresh_g2=_admit_gate2(),
                rerun_decision=_first_eval_admit(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_APPLIED)
            self.assertEqual(result.eid, 42)
            self.assertEqual(result.reason, "")
            self.assertIsNotNone(result.patch)
            assert result.patch is not None  # for type checker

            # update_payload called exactly once with a provenance patch.
            self.assertEqual(len(graph.calls), 1)
            called_eid, called_patch = graph.calls[0]
            self.assertEqual(called_eid, 42)
            self.assertIn("provenance", called_patch)
            prov_dict = called_patch["provenance"]
            self.assertEqual(prov_dict["source_type"], SOURCE_MEMORY)
            self.assertEqual(prov_dict["parent_eids"], [7, 11])
            self.assertEqual(prov_dict["write_path"], WRITE_MIGRATION)
            # Admit on first eval: to_dict strips defaults, but our
            # writer re-adds admission_policy_version so every
            # migration-rewritten row carries a version footprint.
            self.assertEqual(
                prov_dict.get("admission_policy_version"),
                ADMISSION_POLICY_VERSION,
            )
            # Admit means admission_refused is False; to_dict strips it.
            self.assertNotIn("admission_refused", prov_dict)

            # Cursor entry written after update_payload.
            entries = read_entries(ws_root)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].eid, 42)
            self.assertEqual(entries[0].action, CURSOR_ACTION_APPLIED)
            self.assertEqual(entries[0].policy_version, ADMISSION_POLICY_VERSION)

    def test_first_eval_refuse_gate1_fail(self) -> None:
        """FAIL gate 1 on a fresh row → APPLIED with sentinel source_type."""
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=99,
                stored_prov=None,  # pre-step-6 row with no provenance slot
                fresh_g1=_fail_gate1(),
                fresh_g2=_refuse_gate2(),
                rerun_decision=_first_eval_refuse(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_APPLIED)
            self.assertEqual(len(graph.calls), 1)
            _, patch = graph.calls[0]
            prov = patch["provenance"]
            self.assertEqual(prov["source_type"], SOURCE_GATE1_UNRECOVERABLE)
            self.assertEqual(prov["parent_eids"], [])
            self.assertTrue(prov["admission_refused"])
            self.assertEqual(
                prov["admission_reason"],
                ADMISSION_REASON_GATE1_UNRECOVERABLE,
            )
            self.assertEqual(prov["write_path"], WRITE_MIGRATION)

            # The constructed provenance round-trips through ProvenanceV1
            # invariants. Reconstructing it must not raise.
            ProvenanceV1.from_dict(prov)

    def test_apply_tighten_admit_to_refuse(self) -> None:
        """APPLY tighten on a previously admitted row → APPLIED with refused state."""
        stored_prov = {
            "schema_version": "1.0",
            "source_type": SOURCE_COLLECTIVE_ECHO,
            "write_path": "direct_ingest",
            "parent_eids": [1, 2],
            # No admission fields → implicit admitted on first eval of
            # the preceding policy version.
        }
        # Fresh classification: the row has a rejected source_type now.
        g1 = _recover_gate1(
            class_id=GATE1_CLASS_DICT_TRUNCATED,
            source_type=SOURCE_COLLECTIVE_ECHO,
            parent_eids=[1, 2],
        )
        g2 = _refuse_gate2(reason=ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET)
        rerun = _apply_tighten(reason=ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET)

        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=5,
                stored_prov=stored_prov,
                fresh_g1=g1,
                fresh_g2=g2,
                rerun_decision=rerun,
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_APPLIED)
            _, patch = graph.calls[0]
            prov = patch["provenance"]
            self.assertTrue(prov["admission_refused"])
            self.assertEqual(
                prov["admission_reason"],
                ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET,
            )
            self.assertEqual(
                prov["admission_policy_version"],
                ADMISSION_POLICY_VERSION,
            )


# ── Precondition branch tests ────────────────────────────────────────

class TestApplyRowPreconditions(unittest.TestCase):

    def test_precondition_1_stored_prov_not_dict(self) -> None:
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=1,
                stored_prov="not a dict",  # type: ignore[arg-type]
                fresh_g1=_recover_gate1(),
                fresh_g2=_admit_gate2(),
                rerun_decision=_first_eval_admit(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_PRECONDITION)
            self.assertEqual(result.reason, "stored_prov_not_dict")
            self.assertEqual(graph.calls, [])
            self.assertEqual(read_entries(ws_root), [])

    def test_precondition_2_bump_only(self) -> None:
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=2,
                stored_prov={},
                fresh_g1=_recover_gate1(),
                fresh_g2=_admit_gate2(),
                rerun_decision=_bump_only(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_BUMP_ONLY)
            self.assertEqual(graph.calls, [])
            self.assertEqual(read_entries(ws_root), [])

    def test_precondition_2_block_and_review_enqueues(self) -> None:
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=3,
                stored_prov={
                    "admission_refused": True,
                    "admission_reason": "legacy_refusal_reason",
                    "admission_policy_version": "v2.4.x-step6-a",
                },
                fresh_g1=_recover_gate1(),
                fresh_g2=_admit_gate2(),
                rerun_decision=_block_and_review(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_BLOCKED_REVIEW)
            self.assertEqual(graph.calls, [])  # no row write
            self.assertEqual(read_entries(ws_root), [])  # no cursor entry
            reviews = read_reviews(ws_root)
            self.assertEqual(len(reviews), 1)
            self.assertEqual(reviews[0].eid, 3)
            self.assertTrue(reviews[0].stored_admission_refused)
            self.assertFalse(reviews[0].current_admission_refused)

    def test_precondition_2_unknown_rerun_action(self) -> None:
        graph = StubGraph()
        bogus = RerunDecision(
            action="NOT_A_REAL_ACTION",
            new_admission_refused=False,
            new_admission_reason="",
            new_admission_policy_version=ADMISSION_POLICY_VERSION,
        )
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=4,
                stored_prov={},
                fresh_g1=_recover_gate1(),
                fresh_g2=_admit_gate2(),
                rerun_decision=bogus,
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_PRECONDITION)
            self.assertTrue(result.reason.startswith("unknown_rerun_action"))
            self.assertEqual(graph.calls, [])

    def test_skip_class_1_already_canonical(self) -> None:
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=5,
                stored_prov={"source_type": SOURCE_USER_INPUT, "write_path": "direct_ingest"},
                fresh_g1=_skip_gate1(),
                fresh_g2=_admit_gate2(),
                rerun_decision=_first_eval_admit(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_PRECONDITION)
            self.assertEqual(result.reason, "class_1_already_canonical")
            self.assertEqual(graph.calls, [])

    def test_precondition_3_monotonicity_refuses_loosening(self) -> None:
        """A stored refused row with a fresh admitted decision must be
        refused by the writer's independent monotonicity re-check, even
        if the re-run policy upstream handed an APPLY action.
        """
        graph = StubGraph()
        # Bogus upstream: claims APPLY (tighten) but actually loosens.
        loosen = RerunDecision(
            action=RERUN_DECISION_APPLY,
            new_admission_refused=False,
            new_admission_reason="",
            new_admission_policy_version=ADMISSION_POLICY_VERSION,
        )
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=6,
                stored_prov={
                    "admission_refused": True,
                    "admission_reason": "legacy_refusal_reason",
                    "admission_policy_version": "v2.4.x-step6-a",
                },
                fresh_g1=_recover_gate1(),
                fresh_g2=_admit_gate2(),
                rerun_decision=loosen,
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_PRECONDITION)
            self.assertEqual(
                result.reason,
                "loosening_refused_by_writer_monotonicity_check",
            )
            self.assertEqual(graph.calls, [])

    def test_precondition_4_refused_with_empty_reason(self) -> None:
        graph = StubGraph()
        bad = RerunDecision(
            action=RERUN_DECISION_FIRST_EVALUATION,
            new_admission_refused=True,
            new_admission_reason="",  # malformed
            new_admission_policy_version=ADMISSION_POLICY_VERSION,
        )
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=7,
                stored_prov={},
                fresh_g1=_fail_gate1(),
                fresh_g2=_refuse_gate2(),
                rerun_decision=bad,
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_PRECONDITION)
            self.assertEqual(result.reason, "empty_reason_for_refused_decision")

    def test_precondition_4_refused_with_empty_policy_version(self) -> None:
        graph = StubGraph()
        bad = RerunDecision(
            action=RERUN_DECISION_FIRST_EVALUATION,
            new_admission_refused=True,
            new_admission_reason=ADMISSION_REASON_GATE1_UNRECOVERABLE,
            new_admission_policy_version="",  # malformed
        )
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=8,
                stored_prov={},
                fresh_g1=_fail_gate1(),
                fresh_g2=_refuse_gate2(),
                rerun_decision=bad,
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_PRECONDITION)
            self.assertEqual(
                result.reason,
                "empty_policy_version_for_refused_decision",
            )

    def test_precondition_5_class_6_refused_when_table_empty(self) -> None:
        """A class-6 classification with the doctrinal empty mapping table
        must be refused as an upstream-bug cross-check, even though
        upstream gate 1 would normally never route a class-6 row here
        when the table is empty.
        """
        graph = StubGraph()
        g1 = Gate1Result(
            class_id=GATE1_CLASS_DEPRECATED_VOCABULARY,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_MEMORY,
            recovered_source_role=None,
            recovered_parent_eids=[],
            recovery_notes="test_upstream_bug_class_6",
            raw_original={"source_type": "old_name"},
        )
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=9,
                stored_prov={},
                fresh_g1=g1,
                fresh_g2=_admit_gate2(),
                rerun_decision=_first_eval_admit(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_PRECONDITION)
            self.assertEqual(
                result.reason,
                "class_6_evidence_gate_table_empty",
            )
            self.assertEqual(graph.calls, [])

    def test_precondition_5_class_7_refused_when_patterns_empty(self) -> None:
        graph = StubGraph()
        g1 = Gate1Result(
            class_id=GATE1_CLASS_ZERO_EVENT_ARTIFACT,
            outcome=GATE1_OUTCOME_FAIL,
            recovered_source_type=None,
            recovered_source_role=None,
            recovered_parent_eids=[],
            recovery_notes="test_upstream_bug_class_7",
            raw_original={"source_type": "zero_event"},
        )
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=10,
                stored_prov={},
                fresh_g1=g1,
                fresh_g2=_refuse_gate2(),
                rerun_decision=_first_eval_refuse(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_PRECONDITION)
            self.assertEqual(
                result.reason,
                "class_7_evidence_gate_patterns_empty",
            )
            self.assertEqual(graph.calls, [])


# ── Cursor-vs-row cross-check tests ──────────────────────────────────

class TestApplyRowCursorVsRow(unittest.TestCase):
    """Precondition 6: cursor is secondary, row state is primary."""

    def test_prior_applied_matching_row_state_clean_skips(self) -> None:
        """Cursor says APPLIED + stored row matches expected → clean skip."""
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            # Pre-seed the cursor with a prior APPLIED entry.
            append_entry(
                ws_root,
                CursorEntry(
                    eid=11,
                    action=CURSOR_ACTION_APPLIED,
                    gate1_class_id=GATE1_CLASS_DICT_TRUNCATED,
                    gate2_admitted=True,
                    policy_version=ADMISSION_POLICY_VERSION,
                ),
            )
            # Stored row reflects the already-applied state: admit with
            # policy version set (how a migration-rewritten admit row
            # looks after to_dict round-trip).
            stored = {
                "source_type": SOURCE_MEMORY,
                "write_path": WRITE_MIGRATION,
                "parent_eids": [],
                "admission_policy_version": ADMISSION_POLICY_VERSION,
            }
            result = apply_row(
                graph=graph,
                eid=11,
                stored_prov=stored,
                fresh_g1=_recover_gate1(source_type=SOURCE_MEMORY),
                fresh_g2=_admit_gate2(),
                rerun_decision=_first_eval_admit(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_ALREADY_APPLIED)
            self.assertEqual(result.reason, "already_applied_idempotent")
            self.assertEqual(graph.calls, [])

    def test_prior_applied_mismatching_row_state_logs_anomaly(self) -> None:
        """Cursor says APPLIED + stored row disagrees → anomaly, never write."""
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            append_entry(
                ws_root,
                CursorEntry(
                    eid=12,
                    action=CURSOR_ACTION_APPLIED,
                    gate1_class_id=GATE1_CLASS_DICT_INVALID_TYPE,
                    gate2_admitted=False,
                    policy_version=ADMISSION_POLICY_VERSION,
                ),
            )
            # Stored row does NOT match the expected post-apply state:
            # cursor claims we wrote a gate-1 FAIL refusal, but the row
            # has no admission fields at all (as if the writer never
            # ran, or the row was manually rolled back).
            stored = {
                "source_type": SOURCE_USER_INPUT,
                "write_path": "direct_ingest",
                "parent_eids": [],
            }
            result = apply_row(
                graph=graph,
                eid=12,
                stored_prov=stored,
                fresh_g1=_fail_gate1(),
                fresh_g2=_refuse_gate2(),
                rerun_decision=_first_eval_refuse(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_ANOMALY)
            self.assertEqual(result.reason, "cursor_vs_row_mismatch")
            self.assertEqual(graph.calls, [])

    def test_row_first_then_cursor_ordering(self) -> None:
        """On successful apply, update_payload is called before the cursor
        entry is appended. Assertion: if update_payload raises, no cursor
        entry is written.
        """
        graph = StubGraph(fail_on=13)
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=13,
                stored_prov={},
                fresh_g1=_recover_gate1(),
                fresh_g2=_admit_gate2(),
                rerun_decision=_first_eval_admit(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_SKIPPED_ANOMALY)
            self.assertEqual(result.reason, "update_payload_failed")
            self.assertEqual(read_entries(ws_root), [])


# ── Property tests ───────────────────────────────────────────────────

class TestApplyRowMonotonicity(unittest.TestCase):
    """Property: the writer NEVER produces an APPLIED result for a
    transition that loosens a stored refusal. Enumerated over every
    gate-1 class and every valid rerun decision shape.
    """

    def test_no_loosening_ever_applies(self) -> None:
        with tempfile.TemporaryDirectory() as ws_root:
            graph = StubGraph()
            rerun_loose = RerunDecision(
                action=RERUN_DECISION_APPLY,
                new_admission_refused=False,
                new_admission_reason="",
                new_admission_policy_version=ADMISSION_POLICY_VERSION,
            )
            stored_refused = {
                "admission_refused": True,
                "admission_reason": "legacy_refusal_reason",
                "admission_policy_version": "v2.4.x-step6-a",
            }
            for class_id in (
                GATE1_CLASS_LEGACY_BARE_STRING,
                GATE1_CLASS_DICT_TRUNCATED,
                GATE1_CLASS_DICT_INVALID_TYPE,
            ):
                with self.subTest(class_id=class_id):
                    g1 = _recover_gate1(class_id=class_id)
                    result = apply_row(
                        graph=graph,
                        eid=100 + class_id,
                        stored_prov=stored_refused,
                        fresh_g1=g1,
                        fresh_g2=_admit_gate2(),
                        rerun_decision=rerun_loose,
                        workspace_root=ws_root,
                    )
                    self.assertNotEqual(result.action, APPLY_ACTION_APPLIED)
            self.assertEqual(graph.calls, [])


class TestApplyRowSentinelInvariant(unittest.TestCase):
    """Property: rows written with the sentinel source_type always also
    carry admission_refused=True, matching ProvenanceV1.__post_init__.
    """

    def test_sentinel_requires_refused(self) -> None:
        graph = StubGraph()
        with tempfile.TemporaryDirectory() as ws_root:
            result = apply_row(
                graph=graph,
                eid=14,
                stored_prov={},
                fresh_g1=_fail_gate1(),
                fresh_g2=_refuse_gate2(),
                rerun_decision=_first_eval_refuse(),
                workspace_root=ws_root,
            )
            self.assertEqual(result.action, APPLY_ACTION_APPLIED)
            _, patch = graph.calls[0]
            prov = patch["provenance"]
            self.assertEqual(prov["source_type"], SOURCE_GATE1_UNRECOVERABLE)
            self.assertTrue(prov["admission_refused"])
            # Round-trip proves the ProvenanceV1 invariant holds.
            ProvenanceV1.from_dict(prov)


if __name__ == "__main__":
    unittest.main()
