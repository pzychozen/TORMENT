# tests/test_migration_cli.py
"""
Tests for ``torment_service.migration.cli``.

Commit B ships a read/write CLI with three subcommands:

  - ``dry-run``  — classify rows from a JSONL file, emit the
                   four-section report
  - ``status``   — summarise cursor + review queue counts
  - ``apply``    — run the wet-run orchestrator against the row
                   source, rewrite admissible rows, and write the
                   updated state back to a JSONL file. Gated behind
                   ``--confirm-i-have-reviewed-dry-run``.

These tests drive the CLI via its ``main(argv)`` entry point with
synthetic JSONL input under tempdirs, so nothing touches the real
corpus and nothing depends on a packaged console-script install.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.migration.cli import main
from torment_service.migration.constants import (
    ADMISSION_POLICY_VERSION,
    CURSOR_DIRNAME,
    CURSOR_FILENAME,
)
from torment_service.migration.cursor import processed_eids
from torment_service.provenance_v1 import (
    SOURCE_USER_INPUT,
    WRITE_DIRECT_INGEST,
)


def _canonical_provenance() -> dict:
    return {
        "schema_version": "1.0",
        "source_type": SOURCE_USER_INPUT,
        "source_role": None,
        "write_path": WRITE_DIRECT_INGEST,
        "parent_eids": [],
        "created_at_step": 1,
        "created_at_ts": "2026-04-11T00:00:00Z",
    }


def _write_jsonl(path: str, rows: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for eid, raw in rows:
            f.write(json.dumps({"eid": eid, "provenance": raw}))
            f.write("\n")


class CLIDryRunTests(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.rows_path = os.path.join(self.root, "rows.jsonl")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_dry_run_to_stdout_produces_valid_four_section_json(self) -> None:
        _write_jsonl(
            self.rows_path,
            [
                (1, _canonical_provenance()),
                (2, None),
                (3, "memory"),
            ],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["dry-run", "--rows-from-jsonl", self.rows_path])
        self.assertEqual(rc, 0)
        parsed = json.loads(buf.getvalue())
        # Section 1
        self.assertIn("class_counts", parsed)
        # Section 2
        self.assertIn("gate1_fail_listing", parsed)
        # Section 3
        self.assertIn("gate2_refusal_listing", parsed)
        # Section 4
        self.assertIn("reproducibility_anchor", parsed)
        anchor = parsed["reproducibility_anchor"]
        self.assertEqual(anchor["row_count"], 3)
        self.assertEqual(anchor["policy_version"], ADMISSION_POLICY_VERSION)
        self.assertTrue(anchor["zero_event_artifact_patterns_empty"])
        # Row 2 (None) is gate-1 FAIL → appears in section 2
        self.assertEqual(len(parsed["gate1_fail_listing"]), 1)
        self.assertEqual(parsed["gate1_fail_listing"][0]["eid"], 2)

    def test_dry_run_to_output_file_writes_same_report(self) -> None:
        _write_jsonl(self.rows_path, [(1, _canonical_provenance())])
        out_path = os.path.join(self.root, "report.json")
        rc = main(
            [
                "dry-run",
                "--rows-from-jsonl", self.rows_path,
                "--output", out_path,
            ]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r", encoding="utf-8") as f:
            parsed = json.loads(f.read())
        self.assertEqual(parsed["reproducibility_anchor"]["row_count"], 1)

    def test_dry_run_write_cursor_populates_cursor_file(self) -> None:
        _write_jsonl(
            self.rows_path,
            [(1, "memory"), (2, None), (3, _canonical_provenance())],
        )
        workspace = os.path.join(self.root, "ws")
        os.makedirs(workspace)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(
                [
                    "dry-run",
                    "--rows-from-jsonl", self.rows_path,
                    "--workspace-root", workspace,
                    "--write-cursor",
                ]
            )
        self.assertEqual(rc, 0)
        cursor_file = os.path.join(workspace, CURSOR_DIRNAME, CURSOR_FILENAME)
        self.assertTrue(os.path.exists(cursor_file))
        self.assertEqual(processed_eids(workspace), {1, 2, 3})

    def test_dry_run_resume_skips_processed_eids(self) -> None:
        # First run: process EIDs 1 and 2 and write cursor.
        _write_jsonl(self.rows_path, [(1, "memory"), (2, None)])
        workspace = os.path.join(self.root, "ws")
        os.makedirs(workspace)
        with redirect_stdout(io.StringIO()):
            rc = main(
                [
                    "dry-run",
                    "--rows-from-jsonl", self.rows_path,
                    "--workspace-root", workspace,
                    "--write-cursor",
                ]
            )
        self.assertEqual(rc, 0)
        # Second run: a superset of rows with --resume should only
        # re-classify the two NEW rows (3 and 4).
        rows_path_2 = os.path.join(self.root, "rows2.jsonl")
        _write_jsonl(
            rows_path_2,
            [(1, "memory"), (2, None), (3, "tool_result"), (4, None)],
        )
        out_path = os.path.join(self.root, "report2.json")
        rc = main(
            [
                "dry-run",
                "--rows-from-jsonl", rows_path_2,
                "--workspace-root", workspace,
                "--write-cursor",
                "--resume",
                "--output", out_path,
            ]
        )
        self.assertEqual(rc, 0)
        with open(out_path, "r", encoding="utf-8") as f:
            parsed = json.loads(f.read())
        self.assertEqual(parsed["reproducibility_anchor"]["row_count"], 2)
        self.assertEqual(processed_eids(workspace), {1, 2, 3, 4})

    def test_dry_run_without_rows_flag_is_argparse_error(self) -> None:
        # argparse errors exit with code 2 and print to stderr.
        err = io.StringIO()
        with redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                main(["dry-run"])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("--rows-from-jsonl", err.getvalue())

    def test_dry_run_invalid_jsonl_line_raises_value_error(self) -> None:
        # A line that is not valid JSON should bubble up as ValueError
        # from the row stream, not a silent empty run.
        with open(self.rows_path, "w", encoding="utf-8") as f:
            f.write("{this is not json\n")
        with self.assertRaises(ValueError) as cm:
            with redirect_stdout(io.StringIO()):
                main(["dry-run", "--rows-from-jsonl", self.rows_path])
        self.assertIn("invalid JSON line", str(cm.exception))

    def test_dry_run_jsonl_missing_eid_raises_value_error(self) -> None:
        with open(self.rows_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"provenance": None}) + "\n")
        with self.assertRaises(ValueError) as cm:
            with redirect_stdout(io.StringIO()):
                main(["dry-run", "--rows-from-jsonl", self.rows_path])
        self.assertIn("eid", str(cm.exception))


class CLIStatusTests(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_status_on_empty_workspace_reports_zeros(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["status", "--workspace-root", self.root])
        self.assertEqual(rc, 0)
        parsed = json.loads(buf.getvalue())
        self.assertEqual(parsed["cursor_entries"], 0)
        self.assertEqual(parsed["review_queue_entries"], 0)
        self.assertEqual(parsed["processed_eid_count"], 0)
        self.assertTrue(parsed["workspace_root"].endswith(
            os.path.basename(self.root)
        ))

    def test_status_after_dry_run_reports_nonzero_counts(self) -> None:
        rows_path = os.path.join(self.root, "rows.jsonl")
        _write_jsonl(rows_path, [(1, "memory"), (2, None), (3, "tool_result")])
        # First, a dry-run writes cursor entries.
        with redirect_stdout(io.StringIO()):
            rc = main(
                [
                    "dry-run",
                    "--rows-from-jsonl", rows_path,
                    "--workspace-root", self.root,
                    "--write-cursor",
                ]
            )
        self.assertEqual(rc, 0)
        # Then status reports them.
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["status", "--workspace-root", self.root])
        self.assertEqual(rc, 0)
        parsed = json.loads(buf.getvalue())
        self.assertEqual(parsed["cursor_entries"], 3)
        self.assertEqual(parsed["processed_eid_count"], 3)

    def test_status_without_workspace_is_argparse_error(self) -> None:
        err = io.StringIO()
        with redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                main(["status"])
        self.assertEqual(cm.exception.code, 2)


class CLIApplyTests(unittest.TestCase):
    """Commit B writer path through the CLI."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.rows_path = os.path.join(self.root, "rows.jsonl")
        self.out_path = os.path.join(self.root, "rows.out.jsonl")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_apply_without_confirmation_flag_exits_nonzero(self) -> None:
        _write_jsonl(self.rows_path, [(1, "memory")])
        err = io.StringIO()
        with redirect_stderr(err):
            rc = main(
                [
                    "apply",
                    "--rows-from-jsonl", self.rows_path,
                    "--workspace-root", self.root,
                ]
            )
        self.assertEqual(rc, 3)
        self.assertIn("--confirm-i-have-reviewed-dry-run", err.getvalue())

    def test_apply_with_confirmation_writes_updated_rows(self) -> None:
        # A class-3 truncated row that gate 1 RECOVERs and gate 2 admits.
        _write_jsonl(
            self.rows_path,
            [
                (1, {"source_type": "user_input"}),
                (2, None),  # class-5 FAIL → refused sentinel
            ],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(
                [
                    "apply",
                    "--rows-from-jsonl", self.rows_path,
                    "--workspace-root", self.root,
                    "--output-jsonl", self.out_path,
                    "--confirm-i-have-reviewed-dry-run",
                ]
            )
        self.assertEqual(rc, 0)

        report = json.loads(buf.getvalue())
        self.assertEqual(report["policy_version"], ADMISSION_POLICY_VERSION)
        self.assertEqual(report["counts"]["rows_scanned"], 2)
        self.assertEqual(report["counts"]["applied"], 2)

        # Rows-by-default are NOT included in the report.
        self.assertNotIn("rows", report)

        # Output JSONL contains both rows in their post-apply state.
        with open(self.out_path, "r", encoding="utf-8") as f:
            out_lines = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(len(out_lines), 2)
        by_eid = {o["eid"]: o for o in out_lines}
        self.assertEqual(by_eid[1]["provenance"]["source_type"], "user_input")
        self.assertTrue(by_eid[2]["provenance"]["admission_refused"])

        # Cursor file is populated.
        cursor_path = os.path.join(
            self.root, CURSOR_DIRNAME, CURSOR_FILENAME
        )
        self.assertTrue(os.path.exists(cursor_path))

    def test_apply_without_workspace_root_is_argparse_error(self) -> None:
        _write_jsonl(self.rows_path, [(1, "memory")])
        err = io.StringIO()
        with redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "apply",
                        "--rows-from-jsonl", self.rows_path,
                        "--confirm-i-have-reviewed-dry-run",
                    ]
                )
        self.assertEqual(cm.exception.code, 2)

    def test_apply_report_include_rows_opt_in(self) -> None:
        _write_jsonl(self.rows_path, [(1, "memory")])
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(
                [
                    "apply",
                    "--rows-from-jsonl", self.rows_path,
                    "--workspace-root", self.root,
                    "--confirm-i-have-reviewed-dry-run",
                    "--report-include-rows",
                ]
            )
        self.assertEqual(rc, 0)
        report = json.loads(buf.getvalue())
        self.assertIn("rows", report)
        self.assertEqual(len(report["rows"]), 1)


class CLIMissingCommandTests(unittest.TestCase):

    def test_no_subcommand_is_argparse_error(self) -> None:
        err = io.StringIO()
        with redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                main([])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
