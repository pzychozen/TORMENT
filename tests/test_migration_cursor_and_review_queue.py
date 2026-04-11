# tests/test_migration_cursor_and_review_queue.py
"""
Tests for ``torment_service.migration.cursor`` and
``torment_service.migration.review_queue``. Uses tempfile-based
workspaces so nothing touches the real corpus.

The tests focus on:
  - Append semantics and file ordering
  - Round-trip serialization
  - Crash-safe resume helper (``processed_eids``)
  - Directory auto-creation
  - Rejection of unknown cursor actions
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.migration.cursor import (
    CURSOR_ACTION_APPLIED,
    CURSOR_ACTION_BLOCKED_REVIEW,
    CURSOR_ACTION_DRY_RUN_CLASSIFIED,
    CURSOR_ACTION_SKIPPED,
    CursorEntry,
    append_entry,
    cursor_dir,
    cursor_path,
    processed_eids,
    read_entries,
)
from torment_service.migration.review_queue import (
    ReviewEntry,
    append_review,
    read_reviews,
    review_queue_path,
)


class CursorFileTests(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_empty_workspace_has_no_entries(self) -> None:
        self.assertEqual(read_entries(self.root), [])
        self.assertEqual(processed_eids(self.root), set())

    def test_append_creates_directory(self) -> None:
        self.assertFalse(os.path.exists(cursor_dir(self.root)))
        entry = CursorEntry(
            eid=1,
            action=CURSOR_ACTION_DRY_RUN_CLASSIFIED,
            gate1_class_id=2,
            gate2_admitted=True,
        )
        append_entry(self.root, entry)
        self.assertTrue(os.path.exists(cursor_dir(self.root)))
        self.assertTrue(os.path.exists(cursor_path(self.root)))

    def test_round_trip_single_entry(self) -> None:
        entry = CursorEntry(
            eid=42,
            action=CURSOR_ACTION_DRY_RUN_CLASSIFIED,
            gate1_class_id=3,
            gate2_admitted=False,
            committed_at="2026-04-11T00:00:00Z",
        )
        append_entry(self.root, entry)
        entries = read_entries(self.root)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e.eid, 42)
        self.assertEqual(e.action, CURSOR_ACTION_DRY_RUN_CLASSIFIED)
        self.assertEqual(e.gate1_class_id, 3)
        self.assertFalse(e.gate2_admitted)
        self.assertEqual(e.committed_at, "2026-04-11T00:00:00Z")

    def test_append_preserves_order(self) -> None:
        for eid in (10, 20, 30, 40):
            append_entry(
                self.root,
                CursorEntry(
                    eid=eid,
                    action=CURSOR_ACTION_DRY_RUN_CLASSIFIED,
                    gate1_class_id=1,
                    gate2_admitted=True,
                ),
            )
        entries = read_entries(self.root)
        self.assertEqual([e.eid for e in entries], [10, 20, 30, 40])

    def test_processed_eids_is_union_of_all_entries(self) -> None:
        append_entry(
            self.root,
            CursorEntry(eid=1, action=CURSOR_ACTION_SKIPPED,
                        gate1_class_id=1, gate2_admitted=True),
        )
        append_entry(
            self.root,
            CursorEntry(eid=2, action=CURSOR_ACTION_DRY_RUN_CLASSIFIED,
                        gate1_class_id=2, gate2_admitted=False),
        )
        # Even a future APPLIED / BLOCKED_REVIEW action counts toward
        # "processed" on resume — the writer is the only producer and
        # an entry on file means the row transition is durable.
        append_entry(
            self.root,
            CursorEntry(eid=3, action=CURSOR_ACTION_APPLIED,
                        gate1_class_id=3, gate2_admitted=False),
        )
        append_entry(
            self.root,
            CursorEntry(eid=4, action=CURSOR_ACTION_BLOCKED_REVIEW,
                        gate1_class_id=3, gate2_admitted=True),
        )
        self.assertEqual(processed_eids(self.root), {1, 2, 3, 4})

    def test_invalid_action_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CursorEntry(
                eid=1,
                action="NOT_A_REAL_ACTION",
                gate1_class_id=1,
                gate2_admitted=True,
            )


class ReviewQueueTests(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_empty_workspace_has_no_reviews(self) -> None:
        self.assertEqual(read_reviews(self.root), [])

    def test_round_trip_review_entry(self) -> None:
        entry = ReviewEntry(
            eid=100,
            stored_admission_refused=True,
            stored_admission_reason="gate1_unrecoverable",
            stored_admission_policy_version="v2.4.x-step6-a",
            current_admission_refused=False,
            current_admission_reason="",
            current_admission_policy_version="v2.4.x-step6-b",
            recovered_source_type="memory",
            gate1_class_id=3,
            enqueued_at="2026-04-11T00:00:00Z",
        )
        append_review(self.root, entry)
        out = read_reviews(self.root)
        self.assertEqual(len(out), 1)
        got = out[0]
        self.assertEqual(got.eid, 100)
        self.assertTrue(got.stored_admission_refused)
        self.assertFalse(got.current_admission_refused)
        self.assertEqual(got.recovered_source_type, "memory")
        self.assertEqual(got.gate1_class_id, 3)
        self.assertEqual(
            got.stored_admission_policy_version, "v2.4.x-step6-a"
        )
        self.assertEqual(
            got.current_admission_policy_version, "v2.4.x-step6-b"
        )

    def test_review_queue_path_under_torment_migration(self) -> None:
        # Path discipline: review queue MUST live under the same
        # .torment_migration directory as the cursor file, so cleanup
        # is symmetric and the layout is discoverable.
        p = review_queue_path(self.root)
        self.assertIn(".torment_migration", p)
        self.assertTrue(p.endswith("review_queue.jsonl"))


if __name__ == "__main__":
    unittest.main()
