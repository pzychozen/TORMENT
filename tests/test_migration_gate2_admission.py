# tests/test_migration_gate2_admission.py
"""
Tests for ``torment_service.migration.gate2_admission.decide_admission``.

Every admission rule in ``docs/ADMISSION_POLICY_v2.4.x.md`` is exercised
by a dedicated test. These tests feed hand-constructed ``Gate1Result``
values to isolate gate 2 from gate 1.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.migration.constants import (
    ADMISSION_POLICY_VERSION,
    ADMISSION_REASON_ARCHIVIST_ROLE,
    ADMISSION_REASON_BARE_STRING_REJECTED_CLASS,
    ADMISSION_REASON_GATE1_UNRECOVERABLE,
    ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET,
    ADMISSION_REASON_ZERO_EVENT_ARTIFACT,
    GATE1_CLASS_ALREADY_CANONICAL,
    GATE1_CLASS_DICT_INVALID_TYPE,
    GATE1_CLASS_DICT_TRUNCATED,
    GATE1_CLASS_LEGACY_BARE_STRING,
    GATE1_CLASS_NULL_OR_EMPTY,
    GATE1_CLASS_ZERO_EVENT_ARTIFACT,
    GATE1_OUTCOME_FAIL,
    GATE1_OUTCOME_RECOVER,
    GATE1_OUTCOME_SKIP,
)
from torment_service.migration.gate1_recovery import Gate1Result
from torment_service.migration.gate2_admission import decide_admission
from torment_service.provenance_v1 import (
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_DERIVED,
    SOURCE_MEMORY,
    SOURCE_ROLE_OUTPUT,
    SOURCE_TOOL_RESULT,
    SOURCE_USER_INPUT,
)


def _g1(
    *,
    class_id: int,
    outcome: str,
    recovered_source_type: str = None,
    recovered_source_role: str = None,
    recovered_parent_eids: list = None,
) -> Gate1Result:
    return Gate1Result(
        class_id=class_id,
        outcome=outcome,
        recovered_source_type=recovered_source_type,
        recovered_source_role=recovered_source_role,
        recovered_parent_eids=recovered_parent_eids or [],
        recovery_notes="test_fixture",
        raw_original=None,
    )


class TestCanonicalSkipAdmits(unittest.TestCase):

    def test_skip_always_admits(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_ALREADY_CANONICAL,
            outcome=GATE1_OUTCOME_SKIP,
            recovered_source_type=SOURCE_USER_INPUT,
        )
        g2 = decide_admission(g1)
        self.assertTrue(g2.admitted)
        self.assertEqual(g2.reason, "")
        self.assertEqual(g2.policy_version, ADMISSION_POLICY_VERSION)


class TestGate1FailRefusals(unittest.TestCase):

    def test_class4_fail_refused_as_unrecoverable(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_DICT_INVALID_TYPE,
            outcome=GATE1_OUTCOME_FAIL,
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(g2.reason, ADMISSION_REASON_GATE1_UNRECOVERABLE)

    def test_class5_fail_refused_as_unrecoverable(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_NULL_OR_EMPTY,
            outcome=GATE1_OUTCOME_FAIL,
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(g2.reason, ADMISSION_REASON_GATE1_UNRECOVERABLE)

    def test_class7_fail_refused_under_zero_event_reason(self) -> None:
        # Class 7 gets its own reason string so dry-run reports can
        # distinguish "no provenance at all" from "synthetic test row".
        g1 = _g1(
            class_id=GATE1_CLASS_ZERO_EVENT_ARTIFACT,
            outcome=GATE1_OUTCOME_FAIL,
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(g2.reason, ADMISSION_REASON_ZERO_EVENT_ARTIFACT)


class TestBareStringRejectedClass(unittest.TestCase):
    """A bare string that recovers to a rejected source_type
    (``collective_echo``, ``derived``) must be refused under the
    bare-string reason — rule 4 in the doctrine doc."""

    def test_collective_bare_string_refused(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_LEGACY_BARE_STRING,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_COLLECTIVE_ECHO,
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(
            g2.reason, ADMISSION_REASON_BARE_STRING_REJECTED_CLASS
        )

    def test_derived_bare_string_refused(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_LEGACY_BARE_STRING,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_DERIVED,
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(
            g2.reason, ADMISSION_REASON_BARE_STRING_REJECTED_CLASS
        )


class TestBareStringAdmits(unittest.TestCase):
    """Bare strings that recover to safe source_types must admit."""

    def test_memory_bare_string_admits(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_LEGACY_BARE_STRING,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_MEMORY,
        )
        g2 = decide_admission(g1)
        self.assertTrue(g2.admitted)
        self.assertEqual(g2.policy_version, ADMISSION_POLICY_VERSION)

    def test_user_input_bare_string_admits(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_LEGACY_BARE_STRING,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_USER_INPUT,
        )
        g2 = decide_admission(g1)
        self.assertTrue(g2.admitted)

    def test_tool_result_bare_string_admits(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_LEGACY_BARE_STRING,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_TOOL_RESULT,
        )
        g2 = decide_admission(g1)
        self.assertTrue(g2.admitted)


class TestDictTruncatedRejectedSet(unittest.TestCase):
    """Dict-shaped rows with source_type in the rejected set — rule 5."""

    def test_dict_collective_echo_refused(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_DICT_TRUNCATED,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_COLLECTIVE_ECHO,
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(
            g2.reason, ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET
        )

    def test_dict_derived_refused(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_DICT_TRUNCATED,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_DERIVED,
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(
            g2.reason, ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET
        )


class TestArchivistRoleRefusal(unittest.TestCase):
    """role_output + archivist source_role → refuse at any depth.
    Rule 6."""

    def test_archivist_exact_match_refused(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_DICT_TRUNCATED,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_ROLE_OUTPUT,
            recovered_source_role="archivist",
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(g2.reason, ADMISSION_REASON_ARCHIVIST_ROLE)

    def test_archivist_substring_refused(self) -> None:
        # The recursion guard uses substring matching; gate 2 must
        # match that behavior so the doctrine is consistent.
        g1 = _g1(
            class_id=GATE1_CLASS_DICT_TRUNCATED,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_ROLE_OUTPUT,
            recovered_source_role="deputy_archivist_v2",
        )
        g2 = decide_admission(g1)
        self.assertFalse(g2.admitted)
        self.assertEqual(g2.reason, ADMISSION_REASON_ARCHIVIST_ROLE)

    def test_non_archivist_role_admits(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_DICT_TRUNCATED,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_ROLE_OUTPUT,
            recovered_source_role="interpreter",
        )
        g2 = decide_admission(g1)
        self.assertTrue(g2.admitted)


class TestPolicyVersionAlwaysSet(unittest.TestCase):
    """Every gate-2 result must carry a policy version — both on
    admission and refusal — so the re-run policy can detect staleness."""

    def test_policy_version_on_admit(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_LEGACY_BARE_STRING,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_USER_INPUT,
        )
        g2 = decide_admission(g1)
        self.assertEqual(g2.policy_version, ADMISSION_POLICY_VERSION)

    def test_policy_version_on_refuse(self) -> None:
        g1 = _g1(
            class_id=GATE1_CLASS_DICT_TRUNCATED,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=SOURCE_COLLECTIVE_ECHO,
        )
        g2 = decide_admission(g1)
        self.assertEqual(g2.policy_version, ADMISSION_POLICY_VERSION)


if __name__ == "__main__":
    unittest.main()
