# tests/test_migration_rerun_policy.py
"""
Tests for ``torment_service.migration.rerun_policy``.

Exhausts every branch of the re-run decision table in
``docs/ADMISSION_POLICY_v2.4.x.md`` and validates the
monotonic-in-tightness invariant at the unit level. Also covers the
version-ordering rule.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.migration.constants import (
    ADMISSION_POLICY_VERSION,
    ADMISSION_REASON_BARE_STRING_REJECTED_CLASS,
    ADMISSION_REASON_GATE1_UNRECOVERABLE,
    RERUN_DECISION_APPLY,
    RERUN_DECISION_BLOCK_AND_REVIEW,
    RERUN_DECISION_BUMP_ONLY,
    RERUN_DECISION_FIRST_EVALUATION,
)
from torment_service.migration.gate2_admission import Gate2Result
from torment_service.migration.rerun_policy import (
    StoredAdmissionState,
    decide_rerun,
    is_stale_version,
)


def _admit() -> Gate2Result:
    return Gate2Result(
        admitted=True, reason="", policy_version=ADMISSION_POLICY_VERSION
    )


def _refuse(reason: str = ADMISSION_REASON_GATE1_UNRECOVERABLE) -> Gate2Result:
    return Gate2Result(
        admitted=False,
        reason=reason,
        policy_version=ADMISSION_POLICY_VERSION,
    )


class TestFirstEvaluation(unittest.TestCase):

    def test_empty_stored_state_admit_is_first_evaluation(self) -> None:
        stored = StoredAdmissionState(
            admission_refused=False,
            admission_reason="",
            admission_policy_version="",
        )
        d = decide_rerun(stored, _admit())
        self.assertEqual(d.action, RERUN_DECISION_FIRST_EVALUATION)
        self.assertFalse(d.new_admission_refused)
        self.assertEqual(d.new_admission_policy_version, ADMISSION_POLICY_VERSION)

    def test_empty_stored_state_refuse_is_first_evaluation(self) -> None:
        stored = StoredAdmissionState(False, "", "")
        d = decide_rerun(stored, _refuse())
        self.assertEqual(d.action, RERUN_DECISION_FIRST_EVALUATION)
        self.assertTrue(d.new_admission_refused)
        self.assertEqual(
            d.new_admission_reason, ADMISSION_REASON_GATE1_UNRECOVERABLE
        )


class TestBumpOnly(unittest.TestCase):

    def test_admit_to_admit_bump_only(self) -> None:
        stored = StoredAdmissionState(
            admission_refused=False,
            admission_reason="",
            admission_policy_version="v2.4.x-step6-prior",
        )
        d = decide_rerun(stored, _admit())
        self.assertEqual(d.action, RERUN_DECISION_BUMP_ONLY)
        self.assertFalse(d.new_admission_refused)
        self.assertEqual(d.new_admission_policy_version, ADMISSION_POLICY_VERSION)

    def test_refuse_to_refuse_bump_only_preserves_stored_reason(self) -> None:
        stored = StoredAdmissionState(
            admission_refused=True,
            admission_reason=ADMISSION_REASON_BARE_STRING_REJECTED_CLASS,
            admission_policy_version="v2.4.x-step6-prior",
        )
        d = decide_rerun(stored, _refuse(ADMISSION_REASON_GATE1_UNRECOVERABLE))
        self.assertEqual(d.action, RERUN_DECISION_BUMP_ONLY)
        self.assertTrue(d.new_admission_refused)
        # Stored reason wins on bump-only so audit trail is preserved.
        self.assertEqual(
            d.new_admission_reason, ADMISSION_REASON_BARE_STRING_REJECTED_CLASS
        )


class TestApplyTightening(unittest.TestCase):

    def test_admit_to_refuse_applies_automatically(self) -> None:
        stored = StoredAdmissionState(
            admission_refused=False,
            admission_reason="",
            admission_policy_version="v2.4.x-step6-prior",
        )
        d = decide_rerun(stored, _refuse())
        self.assertEqual(d.action, RERUN_DECISION_APPLY)
        self.assertTrue(d.new_admission_refused)
        self.assertEqual(
            d.new_admission_reason, ADMISSION_REASON_GATE1_UNRECOVERABLE
        )


class TestBlockAndReviewLoosening(unittest.TestCase):

    def test_refuse_to_admit_blocks_and_reviews(self) -> None:
        stored = StoredAdmissionState(
            admission_refused=True,
            admission_reason=ADMISSION_REASON_GATE1_UNRECOVERABLE,
            admission_policy_version="v2.4.x-step6-prior",
        )
        d = decide_rerun(stored, _admit())
        self.assertEqual(d.action, RERUN_DECISION_BLOCK_AND_REVIEW)
        # Stored refusal stays in place — loosening is not applied
        # automatically. The row continues to carry the stored refusal
        # until a human ratifies the new policy version for it.
        self.assertTrue(d.new_admission_refused)
        self.assertEqual(
            d.new_admission_reason, ADMISSION_REASON_GATE1_UNRECOVERABLE
        )
        self.assertEqual(
            d.new_admission_policy_version, "v2.4.x-step6-prior"
        )


class TestMonotonicityInvariant(unittest.TestCase):
    """Whatever the row's state transitions through, the stored
    refusal flag must never automatically flip from True to False."""

    def test_no_auto_loosening_anywhere_in_table(self) -> None:
        cases = [
            (StoredAdmissionState(True, ADMISSION_REASON_GATE1_UNRECOVERABLE, "v2.4.x-step6-prior"), _admit()),
            (StoredAdmissionState(True, ADMISSION_REASON_BARE_STRING_REJECTED_CLASS, "v2.4.x-step6-prior"), _admit()),
        ]
        for stored, new in cases:
            with self.subTest(stored=stored):
                d = decide_rerun(stored, new)
                self.assertTrue(
                    d.new_admission_refused,
                    msg=(
                        "Loosening must not apply automatically. "
                        f"stored={stored} new={new}"
                    ),
                )


class TestIsStaleVersion(unittest.TestCase):

    def test_same_version_not_stale(self) -> None:
        self.assertFalse(is_stale_version("v2.4.x-step6-a", "v2.4.x-step6-a"))

    def test_lex_older_within_minor_line_is_stale(self) -> None:
        self.assertTrue(is_stale_version("v2.4.x-step6-a", "v2.4.x-step6-b"))

    def test_newer_within_minor_line_not_stale(self) -> None:
        self.assertFalse(is_stale_version("v2.4.x-step6-b", "v2.4.x-step6-a"))

    def test_cross_line_older_is_stale(self) -> None:
        # Any v2.5.x-* is newer than any v2.4.x-*
        self.assertTrue(is_stale_version("v2.4.x-step6-z", "v2.5.x-step1-a"))

    def test_cross_line_newer_not_stale(self) -> None:
        self.assertFalse(is_stale_version("v2.5.x-step1-a", "v2.4.x-step6-z"))

    def test_empty_always_stale(self) -> None:
        self.assertTrue(is_stale_version("", "v2.4.x-step6-a"))


if __name__ == "__main__":
    unittest.main()
