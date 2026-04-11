# tests/test_migration_gate1_recovery.py
"""
Tests for ``torment_service.migration.gate1_recovery.classify_row``.

Covers every row of the Question-1a recovery table in
``docs/WRITE_MIGRATION_FRAMING_v2.4.x.md`` and the corresponding rules
in ``docs/ADMISSION_POLICY_v2.4.x.md``. Gate 1 is purely deterministic,
so every test asserts an exact classification outcome.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.migration.constants import (
    GATE1_CLASS_ALREADY_CANONICAL,
    GATE1_CLASS_DEPRECATED_VOCABULARY,
    GATE1_CLASS_DICT_INVALID_TYPE,
    GATE1_CLASS_DICT_TRUNCATED,
    GATE1_CLASS_LEGACY_BARE_STRING,
    GATE1_CLASS_NULL_OR_EMPTY,
    GATE1_CLASS_ZERO_EVENT_ARTIFACT,
    GATE1_OUTCOME_FAIL,
    GATE1_OUTCOME_RECOVER,
    GATE1_OUTCOME_SKIP,
    ZERO_EVENT_ARTIFACT_PATTERNS,
)
from torment_service.migration.gate1_recovery import classify_row
from torment_service.provenance_v1 import (
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_GATE1_UNRECOVERABLE,
    SOURCE_MEMORY,
    SOURCE_USER_INPUT,
    WRITE_DIRECT_INGEST,
)


class TestClass1AlreadyCanonical(unittest.TestCase):

    def test_full_canonical_dict_skips(self) -> None:
        raw = {
            "schema_version": "1.0",
            "source_type": SOURCE_USER_INPUT,
            "source_role": None,
            "write_path": WRITE_DIRECT_INGEST,
            "parent_eids": [1, 2, 3],
            "created_at_step": 42,
            "created_at_ts": "2026-04-11T00:00:00Z",
        }
        result = classify_row(raw, eid=100)
        self.assertEqual(result.class_id, GATE1_CLASS_ALREADY_CANONICAL)
        self.assertEqual(result.outcome, GATE1_OUTCOME_SKIP)
        self.assertEqual(result.recovered_source_type, SOURCE_USER_INPUT)
        self.assertEqual(result.recovered_parent_eids, [1, 2, 3])


class TestClass2LegacyBareString(unittest.TestCase):

    def test_memory_bare_string_recovers(self) -> None:
        result = classify_row("memory", eid=101)
        self.assertEqual(result.class_id, GATE1_CLASS_LEGACY_BARE_STRING)
        self.assertEqual(result.outcome, GATE1_OUTCOME_RECOVER)
        self.assertEqual(result.recovered_source_type, SOURCE_MEMORY)
        self.assertIn("legacy_bare_string='memory'", result.recovery_notes)

    def test_collective_maps_to_collective_echo(self) -> None:
        # "collective" is a pre-rename artifact that must map to the
        # canonical collective_echo for later gate-2 refusal.
        result = classify_row("collective")
        self.assertEqual(result.class_id, GATE1_CLASS_LEGACY_BARE_STRING)
        self.assertEqual(result.outcome, GATE1_OUTCOME_RECOVER)
        self.assertEqual(
            result.recovered_source_type, SOURCE_COLLECTIVE_ECHO
        )

    def test_case_insensitive_match(self) -> None:
        result = classify_row("Memory")
        self.assertEqual(result.outcome, GATE1_OUTCOME_RECOVER)
        self.assertEqual(result.recovered_source_type, SOURCE_MEMORY)

    def test_unknown_bare_string_fails(self) -> None:
        result = classify_row("mystery_shape")
        self.assertEqual(result.class_id, GATE1_CLASS_DICT_INVALID_TYPE)
        self.assertEqual(result.outcome, GATE1_OUTCOME_FAIL)


class TestClass3DictTruncated(unittest.TestCase):

    def test_dict_missing_schema_fields_recovers(self) -> None:
        raw = {"source_type": SOURCE_USER_INPUT}
        result = classify_row(raw, eid=103)
        self.assertEqual(result.class_id, GATE1_CLASS_DICT_TRUNCATED)
        self.assertEqual(result.outcome, GATE1_OUTCOME_RECOVER)
        self.assertEqual(result.recovered_source_type, SOURCE_USER_INPUT)
        self.assertEqual(result.recovered_parent_eids, [])

    def test_dict_with_parent_eids_not_a_list_recovers_empty(self) -> None:
        raw = {"source_type": SOURCE_USER_INPUT, "parent_eids": "nonsense"}
        result = classify_row(raw)
        self.assertEqual(result.class_id, GATE1_CLASS_DICT_TRUNCATED)
        self.assertEqual(result.recovered_parent_eids, [])


class TestClass4DictInvalidType(unittest.TestCase):

    def test_dict_with_no_source_type_fails(self) -> None:
        result = classify_row({"parent_eids": [1]})
        self.assertEqual(result.class_id, GATE1_CLASS_DICT_INVALID_TYPE)
        self.assertEqual(result.outcome, GATE1_OUTCOME_FAIL)

    def test_dict_with_unknown_source_type_fails(self) -> None:
        # No deprecated mapping defined in commit A, so unknown types
        # fall through to class 4.
        result = classify_row({"source_type": "mystery_class"})
        self.assertEqual(result.class_id, GATE1_CLASS_DICT_INVALID_TYPE)
        self.assertEqual(result.outcome, GATE1_OUTCOME_FAIL)


class TestClass5NullOrEmpty(unittest.TestCase):

    def test_none_fails(self) -> None:
        result = classify_row(None, eid=105)
        self.assertEqual(result.class_id, GATE1_CLASS_NULL_OR_EMPTY)
        self.assertEqual(result.outcome, GATE1_OUTCOME_FAIL)

    def test_empty_string_fails(self) -> None:
        result = classify_row("")
        self.assertEqual(result.class_id, GATE1_CLASS_NULL_OR_EMPTY)

    def test_empty_dict_fails(self) -> None:
        result = classify_row({})
        self.assertEqual(result.class_id, GATE1_CLASS_NULL_OR_EMPTY)

    def test_integer_is_not_provenance(self) -> None:
        result = classify_row(42)
        self.assertEqual(result.class_id, GATE1_CLASS_NULL_OR_EMPTY)

    def test_list_is_not_provenance(self) -> None:
        result = classify_row([1, 2, 3])
        self.assertEqual(result.class_id, GATE1_CLASS_NULL_OR_EMPTY)


class TestClass6DeprecatedVocabulary(unittest.TestCase):
    """Commit A ships with no deprecated vocabulary mappings. The class
    exists so future dry-run findings can be registered without
    reshaping gate 1. These tests guard the empty-starting-state
    invariant."""

    def test_no_deprecated_mappings_in_commit_a(self) -> None:
        from torment_service.migration.gate1_recovery import (
            _DEPRECATED_VOCABULARY_MAPPING,
        )
        self.assertEqual(_DEPRECATED_VOCABULARY_MAPPING, {})

    def test_deprecated_class_never_fires_in_commit_a(self) -> None:
        # With the mapping empty, no row can be classified as class 6.
        # Try a plausible "deprecated" shape and confirm it falls to
        # class 4 instead.
        result = classify_row({"source_type": "legacy_tool_output"})
        self.assertEqual(result.class_id, GATE1_CLASS_DICT_INVALID_TYPE)
        self.assertNotEqual(
            result.class_id, GATE1_CLASS_DEPRECATED_VOCABULARY
        )


class TestClass7ZeroEventArtifact(unittest.TestCase):
    """Commit A ships the class-7 pattern list deliberately empty. This
    test guards that posture — adding a pattern here requires a
    doctrine policy version bump."""

    def test_pattern_list_empty_in_commit_a(self) -> None:
        self.assertEqual(ZERO_EVENT_ARTIFACT_PATTERNS, ())

    def test_class7_never_fires_in_commit_a(self) -> None:
        # Any dict that might have been a zero-event artifact must
        # classify as class 1 (canonical) or fall to classes 3/4.
        raw = {
            "source_type": SOURCE_USER_INPUT,
            "parent_eids": [],
            "schema_version": "1.0",
            "write_path": WRITE_DIRECT_INGEST,
            "notes": "test_seed_row",
        }
        result = classify_row(raw)
        self.assertNotEqual(
            result.class_id, GATE1_CLASS_ZERO_EVENT_ARTIFACT
        )


class TestSentinelRowHandling(unittest.TestCase):
    """Sentinel rows were produced by a previous migration run and must
    not be re-classified into a new outcome on subsequent runs. The
    re-run policy is responsible for deciding what to do with them;
    gate 1 only notes them."""

    def test_sentinel_row_skips(self) -> None:
        raw = {
            "schema_version": "1.0",
            "source_type": SOURCE_GATE1_UNRECOVERABLE,
            "source_role": None,
            "write_path": "migration",
            "parent_eids": [],
            "admission_refused": True,
            "admission_reason": "gate1_unrecoverable",
            "admission_policy_version": "v2.4.x-step6-a",
        }
        result = classify_row(raw)
        self.assertEqual(result.outcome, GATE1_OUTCOME_SKIP)
        self.assertEqual(
            result.recovered_source_type, SOURCE_GATE1_UNRECOVERABLE
        )


class TestDeterminism(unittest.TestCase):
    """Same input → same output. Gate 1 has no hidden state."""

    def test_determinism_over_many_shapes(self) -> None:
        shapes = [
            None,
            "",
            "memory",
            "collective",
            {"source_type": SOURCE_USER_INPUT},
            {"source_type": "unknown"},
            42,
            [1, 2, 3],
        ]
        for s in shapes:
            with self.subTest(shape=repr(s)):
                a = classify_row(s)
                b = classify_row(s)
                self.assertEqual(a.class_id, b.class_id)
                self.assertEqual(a.outcome, b.outcome)
                self.assertEqual(
                    a.recovered_source_type, b.recovered_source_type
                )


if __name__ == "__main__":
    unittest.main()
