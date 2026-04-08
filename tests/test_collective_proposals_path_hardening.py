"""Regression tests for collective_proposals.py path-expression hardening.

Covers:
  1. Collective root stays inside canonical data root
  2. convergence_patterns.jsonl stays inside collective root
  3. Invalid workspace IDs are rejected
  4. Record/load/count/proposed/cooldown behavior still works after refactor
  5. Tracker reload from disk still works
"""

import os
import shutil
import tempfile
import time
import unittest

from torment_service.collective_proposals import (
    ConvergencePersistenceTracker,
    CollectiveProposalBridge,
    ProposalDraftResult,
)
from torment_service.pathing import safe_slug


class TestTrackerPathIntegrity(unittest.TestCase):
    """1, 2. All paths stay inside their respective roots."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.tracker = ConvergencePersistenceTracker(self._tmpdir, "test_ws")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_base_is_canonical(self):
        self.assertTrue(os.path.isabs(self.tracker._base))
        self.assertEqual(self.tracker._base, os.path.realpath(self.tracker._base))

    def test_base_inside_data_dir(self):
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(
            self.tracker._base.startswith(canonical_data + os.sep),
            f"collective root {self.tracker._base} not inside {canonical_data}",
        )

    def test_log_path_inside_base(self):
        self.assertTrue(
            self.tracker._log_path.startswith(self.tracker._base + os.sep),
            f"log path {self.tracker._log_path} not inside {self.tracker._base}",
        )

    def test_log_path_correct_name(self):
        self.assertTrue(self.tracker._log_path.endswith("convergence_patterns.jsonl"))

    def test_collective_dir_created(self):
        self.assertTrue(os.path.isdir(self.tracker._base))

    def test_expected_directory_structure(self):
        self.assertTrue(self.tracker._base.endswith(
            os.path.join("workspaces", "test_ws", "collective")
        ))


class TestTrackerInvalidPaths(unittest.TestCase):
    """3. Invalid workspace IDs are rejected."""

    def test_rejects_dotdot_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConvergencePersistenceTracker(td, "../escape")

    def test_rejects_slash_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConvergencePersistenceTracker(td, "ws/evil")

    def test_rejects_backslash_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConvergencePersistenceTracker(td, "ws\\evil")

    def test_rejects_empty_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConvergencePersistenceTracker(td, "")

    def test_validate_path_component_rejects_dotdot(self):
        with self.assertRaises(ValueError):
            safe_slug("..")


class TestTrackerBehavior(unittest.TestCase):
    """4. Record/load/count/proposed/cooldown behavior still works."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.tracker = ConvergencePersistenceTracker(self._tmpdir, "test_ws")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _make_event(self, event_id="evt1", domain_id="research",
                    motifs=None, confidence=0.8):
        return {
            "event_id": event_id,
            "domain_id": domain_id,
            "dominant_motifs": motifs or ["m1"],
            "confidence": confidence,
            "ts_end": int(time.time()),
            "participating_agents": ["a1", "a2"],
            "semantic_overlap": 0.75,
        }

    def test_record_event_persists(self):
        evt = self._make_event()
        self.tracker.record_event(evt)
        self.assertTrue(os.path.exists(self.tracker._log_path))

    def test_count_recent(self):
        evt = self._make_event()
        self.tracker.record_event(evt)
        count = self.tracker.count_recent("research", ["m1"], window=3600)
        self.assertEqual(count, 1)

    def test_count_recent_different_domain(self):
        evt = self._make_event(domain_id="research")
        self.tracker.record_event(evt)
        count = self.tracker.count_recent("engineering", ["m1"], window=3600)
        self.assertEqual(count, 0)

    def test_is_event_proposed(self):
        self.assertFalse(self.tracker.is_event_proposed("evt1"))
        self.tracker.record_proposed("evt1", "research")
        self.assertTrue(self.tracker.is_event_proposed("evt1"))

    def test_domain_cooldown(self):
        self.assertFalse(self.tracker.is_domain_on_cooldown("research", 1800))
        self.tracker.record_proposed("evt1", "research")
        self.assertTrue(self.tracker.is_domain_on_cooldown("research", 1800))

    def test_empty_tracker_loads_cleanly(self):
        tracker = ConvergencePersistenceTracker(self._tmpdir, "fresh_ws")
        self.assertEqual(tracker.count_recent("x", ["y"], 3600), 0)
        self.assertFalse(tracker.is_event_proposed("anything"))
        self.assertFalse(tracker.is_domain_on_cooldown("anything", 1800))


class TestTrackerReload(unittest.TestCase):
    """5. Tracker reload from disk still works."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_reload_patterns_from_disk(self):
        tracker1 = ConvergencePersistenceTracker(self._tmpdir, "test_ws")
        evt = {
            "event_id": "evt1",
            "domain_id": "research",
            "dominant_motifs": ["m1"],
            "ts_end": int(time.time()),
        }
        tracker1.record_event(evt)
        tracker1.record_proposed("evt1", "research")

        # Create a new instance — should reload from JSONL
        tracker2 = ConvergencePersistenceTracker(self._tmpdir, "test_ws")
        self.assertEqual(tracker2.count_recent("research", ["m1"], window=3600), 1)
        self.assertTrue(tracker2.is_event_proposed("evt1"))

    def test_reload_domain_cooldown(self):
        tracker1 = ConvergencePersistenceTracker(self._tmpdir, "test_ws")
        tracker1.record_proposed("evt1", "research")

        tracker2 = ConvergencePersistenceTracker(self._tmpdir, "test_ws")
        self.assertTrue(tracker2.is_domain_on_cooldown("research", 1800))


class TestBridgePathIntegrity(unittest.TestCase):
    """CollectiveProposalBridge delegates path handling to the tracker."""

    def test_bridge_creates_tracker_with_valid_paths(self):
        with tempfile.TemporaryDirectory() as td:
            bridge = CollectiveProposalBridge(td, "test_ws")
            self.assertTrue(os.path.isabs(bridge.tracker._base))
            self.assertTrue(os.path.isdir(bridge.tracker._base))

    def test_bridge_rejects_invalid_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                CollectiveProposalBridge(td, "../escape")


if __name__ == "__main__":
    unittest.main()
