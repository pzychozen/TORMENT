"""Regression tests for collective_field.py path-expression hardening.

Covers:
  1. Collective root stays inside canonical data root
  2. packets.jsonl stays inside collective root
  3. events.jsonl stays inside collective root
  4. Invalid workspace IDs are rejected
  5. Append/read/status still work after refactor
"""

import os
import shutil
import tempfile
import time
import unittest

import numpy as np

from torment_service.collective_field import CollectiveField, _validate_path_component
from torment_service.collective_models import ResonancePacket


def _make_packet(agent_id: str = "a1", domain_id: str = "research",
                 workspace_id: str = "test_ws",
                 **kwargs) -> ResonancePacket:
    """Build a minimal ResonancePacket for testing."""
    defaults = dict(
        packet_id=f"pkt_{agent_id}_{int(time.time())}",
        workspace_id=workspace_id,
        domain_id=domain_id,
        agent_id=agent_id,
        source_eid=1,
        ts=int(time.time()),
        coherence=0.5,
        cycle_stage="S0",
        identity_state="s0",
        summary="test packet",
    )
    defaults.update(kwargs)
    return ResonancePacket(**defaults)


class TestCollectiveFieldPathIntegrity(unittest.TestCase):
    """1, 2, 3. All paths stay inside their respective roots."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.cf = CollectiveField("test_ws", self._tmpdir)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_base_is_canonical(self):
        """1. Collective root is an absolute, canonical path."""
        self.assertTrue(os.path.isabs(self.cf._base))
        self.assertEqual(self.cf._base, os.path.realpath(self.cf._base))

    def test_base_inside_data_dir(self):
        """1. Collective root stays inside canonical data root."""
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(
            self.cf._base.startswith(canonical_data + os.sep),
            f"collective root {self.cf._base} not inside {canonical_data}",
        )

    def test_packets_path_inside_base(self):
        """2. packets.jsonl stays inside collective root."""
        self.assertTrue(
            self.cf._packets_path.startswith(self.cf._base + os.sep),
            f"packets path {self.cf._packets_path} not inside {self.cf._base}",
        )

    def test_events_path_inside_base(self):
        """3. events.jsonl stays inside collective root."""
        self.assertTrue(
            self.cf._events_path.startswith(self.cf._base + os.sep),
            f"events path {self.cf._events_path} not inside {self.cf._base}",
        )

    def test_packets_path_correct_name(self):
        self.assertTrue(self.cf._packets_path.endswith("packets.jsonl"))

    def test_events_path_correct_name(self):
        self.assertTrue(self.cf._events_path.endswith("events.jsonl"))

    def test_collective_dir_created(self):
        """Collective directory is created on init."""
        self.assertTrue(os.path.isdir(self.cf._base))

    def test_expected_directory_structure(self):
        """The path ends with workspaces/test_ws/collective."""
        self.assertTrue(self.cf._base.endswith(
            os.path.join("workspaces", "test_ws", "collective")
        ))


class TestCollectiveFieldInvalidPaths(unittest.TestCase):
    """4. Invalid workspace IDs are rejected."""

    def test_rejects_dotdot_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                CollectiveField("../escape", td)

    def test_rejects_slash_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                CollectiveField("ws/evil", td)

    def test_rejects_backslash_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                CollectiveField("ws\\evil", td)

    def test_rejects_empty_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                CollectiveField("", td)

    def test_validate_path_component_rejects_dotdot(self):
        with self.assertRaises(ValueError):
            _validate_path_component("..", "test")

    def test_validate_path_component_rejects_empty(self):
        with self.assertRaises(ValueError):
            _validate_path_component("", "test")


class TestCollectiveFieldBehavior(unittest.TestCase):
    """5. Append/read/status still work after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.cf = CollectiveField("test_ws", self._tmpdir)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_append_packet_persists(self):
        """Packet append writes to disk and appears in cache."""
        pkt = _make_packet()
        self.cf.append_packet(pkt)

        # Check in-memory cache
        recent = self.cf.recent_packets(limit=10)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["agent_id"], "a1")

        # Check file on disk
        self.assertTrue(os.path.exists(self.cf._packets_path))

    def test_append_event_persists(self):
        """Event append writes to disk and appears in reads."""
        from torment_service.collective_models import ConvergenceEvent
        evt = ConvergenceEvent(
            workspace_id="test_ws",
            domain_id="research",
            ts_start=100,
            ts_end=200,
            participating_agents=["a1", "a2"],
            source_packets=["p1", "p2"],
            source_eids=["e1", "e2"],
            confidence=0.8,
            persistence=0.0,
            semantic_overlap=0.75,
            phase_alignment=0.5,
            symbol_alignment=0.3,
            dominant_motifs=["m1"],
            summary="test convergence",
        )
        self.cf.append_event(evt)

        events = self.cf.recent_events(limit=10)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["domain_id"], "research")

    def test_status_works(self):
        """status() returns valid summary after appending data."""
        pkt = _make_packet()
        self.cf.append_packet(pkt)

        s = self.cf.status()
        self.assertEqual(s["workspace_id"], "test_ws")
        self.assertGreaterEqual(s["packet_count_cached"], 1)
        self.assertIn("a1", s["active_agents"])

    def test_reload_from_disk(self):
        """New CollectiveField instance warms cache from existing files."""
        pkt = _make_packet()
        self.cf.append_packet(pkt)

        # Create a fresh instance pointing at the same directory
        cf2 = CollectiveField("test_ws", self._tmpdir)
        recent = cf2.recent_packets(limit=10)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["agent_id"], "a1")

    def test_empty_field_loads_cleanly(self):
        """Fresh CollectiveField with no files on disk loads without error."""
        cf = CollectiveField("fresh_ws", self._tmpdir)
        self.assertEqual(cf.recent_packets(), [])
        self.assertEqual(cf.recent_events(), [])
        s = cf.status()
        self.assertEqual(s["packet_count_cached"], 0)
        self.assertEqual(s["event_count"], 0)


if __name__ == "__main__":
    unittest.main()
