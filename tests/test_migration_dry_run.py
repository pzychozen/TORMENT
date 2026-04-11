# tests/test_migration_dry_run.py
"""
Tests for ``torment_service.migration.dry_run``.

Validates the four-section report shape, the no-corpus-write
invariant, resume-via-cursor semantics, and the reproducibility
anchor fields.
"""
from __future__ import annotations

import ast
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.migration.constants import (
    ADMISSION_POLICY_VERSION,
    ADMISSION_REASON_BARE_STRING_REJECTED_CLASS,
    ADMISSION_REASON_GATE1_UNRECOVERABLE,
    GATE1_CLASS_ALREADY_CANONICAL,
    GATE1_CLASS_LEGACY_BARE_STRING,
    GATE1_CLASS_NULL_OR_EMPTY,
)
from torment_service.migration.cursor import processed_eids
from torment_service.migration.dry_run import (
    DryRunReport,
    run_dry_run,
)
from torment_service.provenance_v1 import (
    SOURCE_USER_INPUT,
    WRITE_DIRECT_INGEST,
)


def _canonical_row(eid: int) -> tuple:
    return (
        eid,
        {
            "schema_version": "1.0",
            "source_type": SOURCE_USER_INPUT,
            "source_role": None,
            "write_path": WRITE_DIRECT_INGEST,
            "parent_eids": [],
            "created_at_step": 1,
            "created_at_ts": "2026-04-11T00:00:00Z",
        },
    )


class TestFourSectionReport(unittest.TestCase):

    def test_empty_iterable_produces_empty_report(self) -> None:
        report = run_dry_run([])
        self.assertEqual(report.row_count, 0)
        self.assertEqual(report.class_counts, {})
        self.assertEqual(report.gate1_fail_listing, [])
        self.assertEqual(report.gate2_refusal_listing, [])
        self.assertEqual(report.policy_version, ADMISSION_POLICY_VERSION)
        self.assertIsNotNone(report.generated_at)
        self.assertTrue(report.zero_event_artifact_patterns_empty)

    def test_canonical_rows_do_not_appear_in_listings(self) -> None:
        report = run_dry_run([_canonical_row(i) for i in range(5)])
        self.assertEqual(report.row_count, 5)
        self.assertEqual(
            report.class_counts, {GATE1_CLASS_ALREADY_CANONICAL: 5}
        )
        self.assertEqual(report.gate1_fail_listing, [])
        self.assertEqual(report.gate2_refusal_listing, [])

    def test_fail_row_populates_both_listings(self) -> None:
        # A null-provenance row is gate-1 FAIL and therefore also
        # gate-2 refused — it should appear in both section 2 and
        # section 3.
        report = run_dry_run([(42, None)])
        self.assertEqual(report.row_count, 1)
        self.assertEqual(len(report.gate1_fail_listing), 1)
        self.assertEqual(report.gate1_fail_listing[0].eid, 42)
        self.assertEqual(
            report.gate1_fail_listing[0].class_id, GATE1_CLASS_NULL_OR_EMPTY
        )
        self.assertEqual(len(report.gate2_refusal_listing), 1)
        self.assertEqual(
            report.gate2_refusal_listing[0].admission_reason,
            ADMISSION_REASON_GATE1_UNRECOVERABLE,
        )

    def test_recovered_then_refused_row_only_in_section_3(self) -> None:
        # A "collective" bare string recovers in gate 1 but refuses in
        # gate 2 (it maps to collective_echo). It must appear in
        # section 3 only, not section 2.
        report = run_dry_run([(7, "collective")])
        self.assertEqual(report.row_count, 1)
        self.assertEqual(report.gate1_fail_listing, [])
        self.assertEqual(len(report.gate2_refusal_listing), 1)
        entry = report.gate2_refusal_listing[0]
        self.assertEqual(entry.eid, 7)
        self.assertEqual(
            entry.admission_reason, ADMISSION_REASON_BARE_STRING_REJECTED_CLASS
        )
        self.assertEqual(entry.class_id, GATE1_CLASS_LEGACY_BARE_STRING)


class TestReproducibilityAnchor(unittest.TestCase):

    def test_anchor_contains_required_fields(self) -> None:
        report = run_dry_run([_canonical_row(1)])
        d = report.to_dict()
        anchor = d["reproducibility_anchor"]
        self.assertIn("policy_version", anchor)
        self.assertIn("generated_at", anchor)
        self.assertIn("row_count", anchor)
        self.assertIn("zero_event_artifact_patterns_empty", anchor)
        self.assertEqual(anchor["row_count"], 1)
        self.assertEqual(
            anchor["policy_version"], ADMISSION_POLICY_VERSION
        )
        self.assertTrue(anchor["zero_event_artifact_patterns_empty"])

    def test_report_to_json_is_parseable(self) -> None:
        report = run_dry_run([(1, "memory"), (2, None)])
        blob = report.to_json()
        import json
        parsed = json.loads(blob)
        self.assertIn("class_counts", parsed)
        self.assertIn("reproducibility_anchor", parsed)


class TestCursorBookkeepingAndResume(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_write_cursor_appends_one_entry_per_row(self) -> None:
        rows = [(1, "memory"), (2, None), (3, _canonical_row(3)[1])]
        run_dry_run(rows, workspace_root=self.root, write_cursor=True)
        self.assertEqual(processed_eids(self.root), {1, 2, 3})

    def test_skip_processed_resume(self) -> None:
        # First run processes rows 1 and 2.
        run_dry_run(
            [(1, "memory"), (2, None)],
            workspace_root=self.root,
            write_cursor=True,
        )
        # Second run supplies a stream including already-processed
        # rows plus new ones; skip_processed must exclude the first
        # two entirely.
        report2 = run_dry_run(
            [(1, "memory"), (2, None), (3, "tool_result"), (4, None)],
            workspace_root=self.root,
            write_cursor=True,
            skip_processed=True,
        )
        self.assertEqual(report2.row_count, 2)  # only 3 and 4 re-scanned
        self.assertEqual(processed_eids(self.root), {1, 2, 3, 4})


class TestNoCorpusWriteInvariant(unittest.TestCase):
    """Commit A's dry-run generator must not import or call any
    corpus-mutation API. This test parses ``dry_run.py`` as AST and
    asserts no forbidden imports are present."""

    FORBIDDEN_IMPORTS = (
        "torment_service.app",
        "torment_service.mcp_server",
        "torment_service.fabric",
        "torment_service.memory_graph",
        "torment_service.embedding_store",
        "torment_service.spine",
    )

    def test_dry_run_module_has_no_forbidden_imports(self) -> None:
        from torment_service.migration import dry_run
        source_path = dry_run.__file__
        with open(source_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        imported: list = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.append(node.module)
        for forbidden in self.FORBIDDEN_IMPORTS:
            for imp in imported:
                self.assertFalse(
                    imp == forbidden or imp.startswith(forbidden + "."),
                    msg=(
                        f"dry_run.py imports forbidden corpus-mutation "
                        f"module: {imp}"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
