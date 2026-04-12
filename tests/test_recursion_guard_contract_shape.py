# tests/test_recursion_guard_contract_shape.py
"""
Negative-shape contract tests for recursion_guard_check's lookup_fn.

The guard's contract requires lookup_fn to return a **payload dict** where
``payload.get("provenance")`` yields the raw provenance dict. These tests
verify that the guard correctly rejects when a caller violates the contract
by returning the raw provenance directly (unwrapped).

This exact mistake caused the step-6 live-run failure (2026-04-11):
the live verifier returned raw provenance dicts instead of wrapping them
as ``{"provenance": raw}``, causing every refused row to report
``REASON_UNKNOWN_PARENT`` instead of ``REASON_MIGRATION_REFUSED``.

See RELEASE_NOTES_v2.4.4.md "Caller-side contract note" for the full
diagnosis.
"""
from __future__ import annotations

import unittest

from cognition.recursion_guard import (
    recursion_guard_check,
    REASON_UNKNOWN_PARENT,
    REASON_MIGRATION_REFUSED,
)
from torment_service.provenance_v1 import (
    SOURCE_GATE1_UNRECOVERABLE,
)


class TestLookupFnContractShape(unittest.TestCase):
    """Verify the guard's behavior when lookup_fn returns the wrong shape.

    These are all NEGATIVE tests: they prove the guard rejects with
    REASON_UNKNOWN_PARENT when the caller violates the contract. The
    correct behavior is not that these cases should succeed — the correct
    behavior is that callers should wrap their return values properly.
    These tests exist to catch future callers who get the wrapping wrong.
    """

    def test_raw_provenance_dict_yields_unknown_parent(self):
        """Returning the raw provenance dict directly (no wrapping) must
        produce REASON_UNKNOWN_PARENT, not a false pass or a crash."""
        raw_prov = {
            "source_type": "user_input",
            "parent_eids": [],
        }
        # Wrong shape: returns the provenance dict itself, not
        # {"provenance": raw_prov}
        def bad_lookup(ws, ag, eid):
            return raw_prov

        ok, reason = recursion_guard_check([1], bad_lookup, "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_UNKNOWN_PARENT)

    def test_raw_refused_provenance_yields_unknown_not_refused(self):
        """A refused row returned without wrapping must NOT produce
        REASON_MIGRATION_REFUSED — the guard never reaches the refusal
        check because payload.get("provenance") returns None first.

        This is the exact failure mode from the step-6 live run."""
        raw_prov = {
            "source_type": SOURCE_GATE1_UNRECOVERABLE,
            "admission_refused": True,
            "admission_reason": "gate2_ancestry_unrecoverable",
            "admission_policy_version": "v2.4.x-step6-a",
        }
        # Wrong shape: returns the provenance dict directly
        def bad_lookup(ws, ag, eid):
            return raw_prov

        ok, reason = recursion_guard_check([1], bad_lookup, "ws", "ag")
        self.assertFalse(ok)
        # The critical assertion: the guard says "unknown_parent", NOT
        # "migration_admission_refused". This proves the contract
        # violation silently misclassifies the row.
        self.assertEqual(reason, REASON_UNKNOWN_PARENT)

    def test_wrapped_provenance_yields_correct_refusal(self):
        """Contrast: the same refused row WITH correct wrapping must
        produce REASON_MIGRATION_REFUSED. This is the positive case
        that proves the wrapping is the only difference."""
        raw_prov = {
            "source_type": SOURCE_GATE1_UNRECOVERABLE,
            "admission_refused": True,
            "admission_reason": "gate2_ancestry_unrecoverable",
            "admission_policy_version": "v2.4.x-step6-a",
        }
        # Correct shape: wrapped in a payload dict
        def good_lookup(ws, ag, eid):
            return {"provenance": raw_prov}

        ok, reason = recursion_guard_check([1], good_lookup, "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_MIGRATION_REFUSED)

    def test_wrapped_clean_provenance_admits(self):
        """Further contrast: a clean row with correct wrapping admits.
        This closes the four-corner matrix: wrong-shape-clean (rejected),
        wrong-shape-refused (rejected-wrong-reason), right-shape-refused
        (rejected-right-reason), right-shape-clean (admitted)."""
        raw_prov = {
            "source_type": "user_input",
            "parent_eids": [],
        }
        def good_lookup(ws, ag, eid):
            return {"provenance": raw_prov}

        ok, reason = recursion_guard_check([1], good_lookup, "ws", "ag")
        self.assertTrue(ok, msg=f"rejected: {reason}")


if __name__ == "__main__":
    unittest.main()
