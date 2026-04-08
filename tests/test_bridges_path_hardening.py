"""Regression tests for bridges.py path-expression hardening.

Covers:
  1. Workspace root stays inside canonical data root
  2. bridges.json stays inside workspace root
  3. bridge_events.jsonl stays inside workspace root
  4. Invalid workspace IDs are rejected
  5. Load/save/event logging still work after refactor
"""

import os
import json
import tempfile
import unittest

from torment_service.bridges import BridgeRegistry


class TestBridgeRegistryPathIntegrity(unittest.TestCase):
    """1, 2, 3. All paths stay inside their respective roots."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.reg = BridgeRegistry(self._tmpdir, "test_ws")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_data_dir_is_canonical(self):
        self.assertTrue(os.path.isabs(self.reg.data_dir))
        self.assertEqual(self.reg.data_dir, os.path.realpath(self.reg.data_dir))

    def test_bridges_json_inside_data_dir(self):
        """2. bridges.json stays inside data root."""
        self.assertTrue(
            self.reg.path.startswith(self.reg.data_dir + os.sep),
            f"bridges.json path {self.reg.path} not inside {self.reg.data_dir}",
        )

    def test_events_path_inside_data_dir(self):
        """3. bridge_events.jsonl stays inside data root."""
        self.assertTrue(
            self.reg.events_path.startswith(self.reg.data_dir + os.sep),
            f"events path {self.reg.events_path} not inside {self.reg.data_dir}",
        )

    def test_bridges_json_correct_name(self):
        self.assertTrue(self.reg.path.endswith("bridges.json"))

    def test_events_path_correct_name(self):
        self.assertTrue(self.reg.events_path.endswith("bridge_events.jsonl"))

    def test_workspace_dir_created(self):
        ws_dir = os.path.dirname(self.reg.path)
        self.assertTrue(os.path.isdir(ws_dir))


class TestBridgeRegistryInvalidPaths(unittest.TestCase):
    """4. Invalid workspace IDs are rejected."""

    def test_rejects_dotdot_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                BridgeRegistry(td, "../escape")

    def test_rejects_slash_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                BridgeRegistry(td, "ws/evil")

    def test_rejects_empty_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                BridgeRegistry(td, "")


class TestBridgeRegistryBehavior(unittest.TestCase):
    """5. Load/save/event logging still work after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.reg = BridgeRegistry(self._tmpdir, "test_ws")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_and_reload(self):
        """Save bridges, then reload from disk."""
        from torment_service.bridges import Bridge, _now_ts
        b = Bridge(
            from_domain="d1", from_motif="m1",
            to_domain="d2", to_motif="m2",
            confidence=0.9, created_ts=_now_ts(),
            status="suggested", updated_ts=_now_ts(),
        )
        self.reg.bridges.append(b)
        self.reg.save()

        # Reload
        reg2 = BridgeRegistry(self._tmpdir, "test_ws")
        self.assertEqual(len(reg2.bridges), 1)
        self.assertEqual(reg2.bridges[0].from_domain, "d1")
        self.assertAlmostEqual(reg2.bridges[0].confidence, 0.9, places=2)

    def test_event_logging(self):
        """_log_event writes to bridge_events.jsonl."""
        self.reg._log_event({"type": "TEST_EVENT", "detail": "hello"})
        self.assertTrue(os.path.exists(self.reg.events_path))
        with open(self.reg.events_path, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        evt = json.loads(lines[0])
        self.assertEqual(evt["type"], "TEST_EVENT")
        self.assertEqual(evt["workspace_id"], "test_ws")

    def test_empty_registry_loads_cleanly(self):
        """Fresh registry with no file on disk loads with empty bridges."""
        reg = BridgeRegistry(self._tmpdir, "fresh_ws")
        self.assertEqual(len(reg.bridges), 0)


if __name__ == "__main__":
    unittest.main()
