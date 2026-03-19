"""
tests/test_collective_field.py — Collective field persistence and querying

Tests for:
    - CollectiveField append + read packets
    - Persistence across restart (re-instantiation)
    - Filtering by domain and agent
    - In-memory cache behavior
    - Event append + read
    - Status reporting
    - Thread safety (basic)
    - Empty state behavior
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.collective_models import ResonancePacket, ConvergenceEvent
from torment_service.collective_field import CollectiveField


def _make_packet(**kwargs) -> ResonancePacket:
    defaults = {
        "workspace_id": "ws1",
        "agent_id": "agent1",
        "domain_id": "personal",
        "summary": "Test memory",
        "coherence": 0.5,
        "cycle_stage": "S2",
    }
    defaults.update(kwargs)
    return ResonancePacket(**defaults)


class TestCollectiveFieldEmpty(unittest.TestCase):
    """Empty field behavior."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)

    def test_empty_recent_packets(self):
        self.assertEqual(self.field.recent_packets(), [])

    def test_empty_status(self):
        s = self.field.status()
        self.assertEqual(s["workspace_id"], "ws1")
        self.assertEqual(s["packet_count_cached"], 0)
        self.assertEqual(s["packet_count_total"], 0)
        self.assertEqual(s["event_count"], 0)
        self.assertEqual(s["active_agents"], [])

    def test_empty_events(self):
        self.assertEqual(self.field.recent_events(), [])


class TestCollectiveFieldPackets(unittest.TestCase):
    """Packet append, read, and filter operations."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)

    def test_append_and_read(self):
        p = _make_packet()
        self.field.append_packet(p)
        recent = self.field.recent_packets(limit=10)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["agent_id"], "agent1")

    def test_multiple_packets(self):
        for i in range(5):
            self.field.append_packet(_make_packet(agent_id=f"a{i}", summary=f"Memory {i}"))
        recent = self.field.recent_packets(limit=10)
        self.assertEqual(len(recent), 5)

    def test_limit(self):
        for i in range(10):
            self.field.append_packet(_make_packet(summary=f"M{i}"))
        recent = self.field.recent_packets(limit=3)
        self.assertEqual(len(recent), 3)
        # Should be the last 3
        self.assertEqual(recent[-1]["summary"], "M9")

    def test_filter_by_domain(self):
        self.field.append_packet(_make_packet(domain_id="personal"))
        self.field.append_packet(_make_packet(domain_id="work"))
        self.field.append_packet(_make_packet(domain_id="personal"))
        result = self.field.packets_by_domain("personal")
        self.assertEqual(len(result), 2)
        result_work = self.field.packets_by_domain("work")
        self.assertEqual(len(result_work), 1)

    def test_filter_by_agent(self):
        self.field.append_packet(_make_packet(agent_id="ryuki"))
        self.field.append_packet(_make_packet(agent_id="aria"))
        self.field.append_packet(_make_packet(agent_id="ryuki"))
        result = self.field.packets_by_agent("ryuki")
        self.assertEqual(len(result), 2)
        result_aria = self.field.packets_by_agent("aria")
        self.assertEqual(len(result_aria), 1)

    def test_filter_nonexistent_domain(self):
        self.field.append_packet(_make_packet(domain_id="personal"))
        result = self.field.packets_by_domain("nonexistent")
        self.assertEqual(len(result), 0)


class TestCollectiveFieldPersistence(unittest.TestCase):
    """Packets survive restart (re-instantiation from disk)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_persist_and_reload(self):
        # Write packets
        field1 = CollectiveField("ws1", self.tmp)
        field1.append_packet(_make_packet(summary="First"))
        field1.append_packet(_make_packet(summary="Second"))

        # Create new instance (simulates restart)
        field2 = CollectiveField("ws1", self.tmp)
        recent = field2.recent_packets(limit=10)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["summary"], "First")
        self.assertEqual(recent[1]["summary"], "Second")

    def test_persist_all_fields(self):
        field1 = CollectiveField("ws1", self.tmp)
        p = _make_packet(
            agent_id="ryuki",
            domain_id="personal",
            summary="Test",
            coherence=0.85,
            cycle_stage="S3",
            motifs=["m_01", "m_02"],
            state_symbol="◈",
            resonance_score=0.6,
            srg_band=2,
        )
        field1.append_packet(p)

        field2 = CollectiveField("ws1", self.tmp)
        recent = field2.recent_packets()
        self.assertEqual(len(recent), 1)
        loaded = recent[0]
        self.assertEqual(loaded["agent_id"], "ryuki")
        self.assertEqual(loaded["coherence"], 0.85)
        self.assertEqual(loaded["motifs"], ["m_01", "m_02"])
        self.assertEqual(loaded["state_symbol"], "◈")
        self.assertEqual(loaded["srg_band"], 2)

    def test_all_packets_from_disk(self):
        field1 = CollectiveField("ws1", self.tmp)
        for i in range(5):
            field1.append_packet(_make_packet(summary=f"M{i}"))

        field2 = CollectiveField("ws1", self.tmp)
        all_pkts = field2.all_packets()
        self.assertEqual(len(all_pkts), 5)


class TestCollectiveFieldCache(unittest.TestCase):
    """In-memory cache limits."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        self.field._recent_max = 10  # small cache for testing

    def test_cache_eviction(self):
        for i in range(20):
            self.field.append_packet(_make_packet(summary=f"M{i}"))
        # Cache should only hold last 10
        recent = self.field.recent_packets(limit=100)
        self.assertEqual(len(recent), 10)
        self.assertEqual(recent[0]["summary"], "M10")  # oldest in cache
        self.assertEqual(recent[-1]["summary"], "M19")  # newest

    def test_disk_has_all(self):
        for i in range(20):
            self.field.append_packet(_make_packet(summary=f"M{i}"))
        # Disk has everything
        all_pkts = self.field.all_packets()
        self.assertEqual(len(all_pkts), 20)


class TestCollectiveFieldEvents(unittest.TestCase):
    """Convergence event operations."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)

    def test_append_and_read_event(self):
        e = ConvergenceEvent(
            workspace_id="ws1",
            domain_id="personal",
            participating_agents=["a1", "a2"],
            confidence=0.82,
            summary="Both discussed music",
        )
        self.field.append_event(e)
        events = self.field.recent_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["confidence"], 0.82)

    def test_get_event_by_id(self):
        e = ConvergenceEvent(
            workspace_id="ws1",
            domain_id="personal",
            summary="Test event",
        )
        self.field.append_event(e)
        found = self.field.get_event(e.event_id)
        self.assertIsNotNone(found)
        self.assertEqual(found["event_id"], e.event_id)

    def test_get_nonexistent_event(self):
        found = self.field.get_event("cev_nonexistent")
        self.assertIsNone(found)

    def test_events_by_domain(self):
        e1 = ConvergenceEvent(workspace_id="ws1", domain_id="personal")
        e2 = ConvergenceEvent(workspace_id="ws1", domain_id="work")
        self.field.append_event(e1)
        self.field.append_event(e2)
        personal = self.field.events_by_domain("personal")
        self.assertEqual(len(personal), 1)

    def test_events_persist(self):
        e = ConvergenceEvent(workspace_id="ws1", domain_id="d1", summary="Persist test")
        self.field.append_event(e)

        field2 = CollectiveField("ws1", self.tmp)
        events = field2.recent_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["summary"], "Persist test")


class TestCollectiveFieldStatus(unittest.TestCase):
    """Status reporting."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)

    def test_status_with_data(self):
        self.field.append_packet(_make_packet(agent_id="ryuki", domain_id="personal"))
        self.field.append_packet(_make_packet(agent_id="aria", domain_id="personal"))
        self.field.append_packet(_make_packet(agent_id="ryuki", domain_id="work"))

        e = ConvergenceEvent(workspace_id="ws1")
        self.field.append_event(e)

        s = self.field.status()
        self.assertEqual(s["packet_count_cached"], 3)
        self.assertEqual(s["packet_count_total"], 3)
        self.assertEqual(s["event_count"], 1)
        self.assertIn("aria", s["active_agents"])
        self.assertIn("ryuki", s["active_agents"])
        self.assertIn("personal", s["active_domains"])
        self.assertIn("work", s["active_domains"])


class TestCollectiveFieldThreadSafety(unittest.TestCase):
    """Basic thread safety for concurrent appends."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)

    def test_concurrent_appends(self):
        """Multiple threads appending simultaneously shouldn't corrupt data."""
        errors = []

        def worker(agent_id, count):
            try:
                for i in range(count):
                    self.field.append_packet(_make_packet(
                        agent_id=agent_id,
                        summary=f"{agent_id}_m{i}",
                    ))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=("a1", 20)),
            threading.Thread(target=worker, args=("a2", 20)),
            threading.Thread(target=worker, args=("a3", 20)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        # All 60 packets should be on disk
        all_pkts = self.field.all_packets()
        self.assertEqual(len(all_pkts), 60)


class TestCollectiveFieldIsolation(unittest.TestCase):
    """Different workspaces stay isolated."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field1 = CollectiveField("ws1", self.tmp)
        self.field2 = CollectiveField("ws2", self.tmp)

    def test_workspace_isolation(self):
        self.field1.append_packet(_make_packet(workspace_id="ws1", summary="WS1 only"))
        self.field2.append_packet(_make_packet(workspace_id="ws2", summary="WS2 only"))

        ws1_pkts = self.field1.recent_packets()
        ws2_pkts = self.field2.recent_packets()
        self.assertEqual(len(ws1_pkts), 1)
        self.assertEqual(len(ws2_pkts), 1)
        self.assertEqual(ws1_pkts[0]["summary"], "WS1 only")
        self.assertEqual(ws2_pkts[0]["summary"], "WS2 only")


if __name__ == "__main__":
    unittest.main()
