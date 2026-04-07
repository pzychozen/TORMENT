"""Regression tests for conflicts.py path-expression hardening.

Covers:
  1. Domain root stays inside canonical data root
  2. conflicts.jsonl stays inside domain root
  3. conflict_events.jsonl stays inside domain root
  4. Invalid workspace/domain IDs are rejected
  5. add/decide/apply_events/list behavior still works after refactor
"""

import os
import shutil
import tempfile
import unittest

from torment_service.conflicts import ConflictRegistry, _validate_path_component


class TestConflictRegistryPathIntegrity(unittest.TestCase):
    """1, 2, 3. All paths stay inside their respective roots."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.reg = ConflictRegistry(self._tmpdir, "test_ws", "research")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_data_dir_is_canonical(self):
        self.assertTrue(os.path.isabs(self.reg.data_dir))
        self.assertEqual(self.reg.data_dir, os.path.realpath(self.reg.data_dir))

    def test_conflicts_path_inside_data_dir(self):
        self.assertTrue(
            self.reg.path.startswith(self.reg.data_dir + os.sep),
            f"conflicts.jsonl {self.reg.path} not inside {self.reg.data_dir}",
        )

    def test_events_path_inside_data_dir(self):
        self.assertTrue(
            self.reg.events_path.startswith(self.reg.data_dir + os.sep),
            f"events path {self.reg.events_path} not inside {self.reg.data_dir}",
        )

    def test_conflicts_path_correct_name(self):
        self.assertTrue(self.reg.path.endswith("conflicts.jsonl"))

    def test_events_path_correct_name(self):
        self.assertTrue(self.reg.events_path.endswith("conflict_events.jsonl"))

    def test_domain_dir_created(self):
        domain_dir = os.path.dirname(self.reg.path)
        self.assertTrue(os.path.isdir(domain_dir))

    def test_expected_directory_structure(self):
        domain_dir = os.path.dirname(self.reg.path)
        self.assertTrue(domain_dir.endswith(
            os.path.join("workspaces", "test_ws", "domains", "research")
        ))


class TestConflictRegistryInvalidPaths(unittest.TestCase):
    """4. Invalid workspace/domain IDs are rejected."""

    def test_rejects_dotdot_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConflictRegistry(td, "../escape", "research")

    def test_rejects_slash_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConflictRegistry(td, "ws/evil", "research")

    def test_rejects_empty_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConflictRegistry(td, "", "research")

    def test_rejects_dotdot_domain_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConflictRegistry(td, "test_ws", "../escape")

    def test_rejects_slash_domain_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConflictRegistry(td, "test_ws", "dom/evil")

    def test_rejects_empty_domain_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ConflictRegistry(td, "test_ws", "")

    def test_validate_path_component_rejects_backslash(self):
        with self.assertRaises(ValueError):
            _validate_path_component("a\\b", "test")


class TestConflictRegistryBehavior(unittest.TestCase):
    """5. add/decide/apply_events/list behavior still works after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.reg = ConflictRegistry(self._tmpdir, "test_ws", "research")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_add_conflict(self):
        c = self.reg.add(eid_a=1, eid_b=2, sim=0.85, conflict_score=0.7, reason="test conflict")
        self.assertEqual(c.status, "open")
        self.assertEqual(c.eid_a, 1)
        self.assertEqual(c.eid_b, 2)
        self.assertTrue(os.path.exists(self.reg.path))

    def test_decide_conflict(self):
        c = self.reg.add(eid_a=1, eid_b=2, sim=0.85, conflict_score=0.7, reason="test")
        self.reg.decide(c.conflict_id, "keep_a", note="A is better")
        self.assertTrue(os.path.exists(self.reg.events_path))

    def test_apply_events_resolves(self):
        c = self.reg.add(eid_a=1, eid_b=2, sim=0.85, conflict_score=0.7, reason="test")
        self.reg.decide(c.conflict_id, "keep_a", note="A wins")
        resolved = self.reg.apply_events()
        self.assertEqual(resolved[c.conflict_id].status, "resolved")
        self.assertEqual(resolved[c.conflict_id].decision, "keep_a")

    def test_list_filters_by_status(self):
        c1 = self.reg.add(eid_a=1, eid_b=2, sim=0.85, conflict_score=0.7, reason="first")
        c2 = self.reg.add(eid_a=3, eid_b=4, sim=0.90, conflict_score=0.8, reason="second")
        self.reg.decide(c1.conflict_id, "keep_a")

        open_conflicts = self.reg.list(status="open")
        self.assertEqual(len(open_conflicts), 1)
        self.assertEqual(open_conflicts[0].conflict_id, c2.conflict_id)

        all_conflicts = self.reg.list(status="any")
        self.assertEqual(len(all_conflicts), 2)

    def test_empty_registry_loads_cleanly(self):
        reg = ConflictRegistry(self._tmpdir, "fresh_ws", "fresh_dom")
        self.assertEqual(len(reg.list(status="any")), 0)

    def test_reload_from_disk(self):
        c = self.reg.add(eid_a=1, eid_b=2, sim=0.85, conflict_score=0.7, reason="persist test")
        self.reg.decide(c.conflict_id, "merge", note="merged")

        reg2 = ConflictRegistry(self._tmpdir, "test_ws", "research")
        resolved = reg2.apply_events()
        self.assertIn(c.conflict_id, resolved)
        self.assertEqual(resolved[c.conflict_id].status, "resolved")


if __name__ == "__main__":
    unittest.main()
