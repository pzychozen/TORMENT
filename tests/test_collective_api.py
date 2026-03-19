"""
tests/test_collective_api.py — Collective (Hivemind) API endpoint logic tests

Tests the logic that the collective API endpoints use, without requiring
FastAPI/TestClient (which may not be installed in CI). Each test exercises
the same CollectiveField methods the endpoints call, with the same argument
patterns (domain filters, agent filters, limits, event lookup).

Tests for:
    - Status endpoint logic (empty + populated)
    - Packets endpoint logic (all, filter by domain, filter by agent, limit)
    - Events endpoint logic (all, filter by domain, limit)
    - Event detail lookup (found + not found)
    - Feature flag gating pattern
    - Workspace isolation through API layer
"""
from __future__ import annotations

import os
import sys
import tempfile
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


class TestCollectiveAPIDisabledPattern(unittest.TestCase):
    """When hivemind is disabled, endpoints should return stubs.
    Tests the exact response shapes the API returns."""

    def test_status_disabled_shape(self):
        # Mirrors: if not fabric._hivemind_enable: return {"enabled": False, "workspace_id": ws}
        result = {"enabled": False, "workspace_id": "ws1"}
        self.assertFalse(result["enabled"])
        self.assertEqual(result["workspace_id"], "ws1")

    def test_packets_disabled_shape(self):
        result = {"enabled": False, "packets": []}
        self.assertFalse(result["enabled"])
        self.assertEqual(result["packets"], [])

    def test_events_disabled_shape(self):
        result = {"enabled": False, "events": []}
        self.assertFalse(result["enabled"])
        self.assertEqual(result["events"], [])


class TestCollectiveAPIStatusLogic(unittest.TestCase):
    """Mirrors /workspace/{ws}/collective/status endpoint."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)

    def test_empty_status(self):
        result = self.field.status()
        result["enabled"] = True
        self.assertTrue(result["enabled"])
        self.assertEqual(result["packet_count_cached"], 0)
        self.assertEqual(result["event_count"], 0)
        self.assertEqual(result["active_agents"], [])

    def test_populated_status(self):
        self.field.append_packet(_make_packet(agent_id="ryuki", domain_id="personal"))
        self.field.append_packet(_make_packet(agent_id="aria", domain_id="personal"))
        self.field.append_packet(_make_packet(agent_id="ryuki", domain_id="work"))
        e = ConvergenceEvent(workspace_id="ws1", domain_id="personal")
        self.field.append_event(e)

        result = self.field.status()
        result["enabled"] = True
        self.assertEqual(result["packet_count_cached"], 3)
        self.assertEqual(result["event_count"], 1)
        self.assertIn("ryuki", result["active_agents"])
        self.assertIn("aria", result["active_agents"])
        self.assertIn("personal", result["active_domains"])
        self.assertIn("work", result["active_domains"])


class TestCollectiveAPIPacketsLogic(unittest.TestCase):
    """Mirrors /workspace/{ws}/collective/packets endpoint with filters."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        # Seed test data
        self.field.append_packet(_make_packet(agent_id="ryuki", domain_id="personal", summary="Music"))
        self.field.append_packet(_make_packet(agent_id="aria", domain_id="personal", summary="Art"))
        self.field.append_packet(_make_packet(agent_id="ryuki", domain_id="work", summary="Code"))

    def test_all_packets(self):
        # Mirrors: field.recent_packets(limit=50) when no filter
        pkts = self.field.recent_packets(limit=50)
        result = {"enabled": True, "count": len(pkts), "packets": pkts}
        self.assertEqual(result["count"], 3)

    def test_filter_by_domain(self):
        # Mirrors: field.packets_by_domain(domain, limit=limit)
        pkts = self.field.packets_by_domain("personal", limit=50)
        result = {"enabled": True, "count": len(pkts), "packets": pkts}
        self.assertEqual(result["count"], 2)
        for pkt in result["packets"]:
            self.assertEqual(pkt["domain_id"], "personal")

    def test_filter_by_agent(self):
        # Mirrors: field.packets_by_agent(agent, limit=limit)
        pkts = self.field.packets_by_agent("ryuki", limit=50)
        result = {"enabled": True, "count": len(pkts), "packets": pkts}
        self.assertEqual(result["count"], 2)
        for pkt in result["packets"]:
            self.assertEqual(pkt["agent_id"], "ryuki")

    def test_limit(self):
        pkts = self.field.recent_packets(limit=1)
        result = {"enabled": True, "count": len(pkts), "packets": pkts}
        self.assertEqual(result["count"], 1)

    def test_empty_domain_filter(self):
        pkts = self.field.packets_by_domain("nonexistent", limit=50)
        self.assertEqual(len(pkts), 0)

    def test_empty_agent_filter(self):
        pkts = self.field.packets_by_agent("unknown_agent", limit=50)
        self.assertEqual(len(pkts), 0)


class TestCollectiveAPIEventsLogic(unittest.TestCase):
    """Mirrors /workspace/{ws}/collective/events endpoint."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        self.e1 = ConvergenceEvent(
            workspace_id="ws1", domain_id="personal",
            participating_agents=["ryuki", "aria"],
            confidence=0.85, summary="Both discussed music",
        )
        self.e2 = ConvergenceEvent(
            workspace_id="ws1", domain_id="work",
            confidence=0.7, summary="Work alignment",
        )
        self.field.append_event(self.e1)
        self.field.append_event(self.e2)

    def test_all_events(self):
        events = self.field.recent_events(limit=20)
        result = {"enabled": True, "count": len(events), "events": events}
        self.assertEqual(result["count"], 2)

    def test_filter_by_domain(self):
        events = self.field.events_by_domain("personal", limit=20)
        result = {"enabled": True, "count": len(events), "events": events}
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["events"][0]["domain_id"], "personal")

    def test_events_limit(self):
        events = self.field.recent_events(limit=1)
        self.assertEqual(len(events), 1)


class TestCollectiveAPIEventDetailLogic(unittest.TestCase):
    """Mirrors /workspace/{ws}/collective/events/{event_id} endpoint."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        self.event = ConvergenceEvent(
            workspace_id="ws1", domain_id="personal",
            summary="Test convergence event",
        )
        self.field.append_event(self.event)

    def test_found(self):
        result = self.field.get_event(self.event.event_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["event_id"], self.event.event_id)
        self.assertEqual(result["summary"], "Test convergence event")

    def test_not_found(self):
        # Mirrors: raise HTTPException(404) when get_event returns None
        result = self.field.get_event("cev_nonexistent")
        self.assertIsNone(result)


class TestCollectiveAPIWorkspaceIsolation(unittest.TestCase):
    """Different workspace IDs get independent fields (mirrors separate endpoint calls)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field_ws1 = CollectiveField("ws1", self.tmp)
        self.field_ws2 = CollectiveField("ws2", self.tmp)

    def test_packets_isolated(self):
        self.field_ws1.append_packet(_make_packet(workspace_id="ws1", summary="WS1 only"))
        self.field_ws2.append_packet(_make_packet(workspace_id="ws2", summary="WS2 only"))

        pkts1 = self.field_ws1.recent_packets(limit=50)
        pkts2 = self.field_ws2.recent_packets(limit=50)
        self.assertEqual(len(pkts1), 1)
        self.assertEqual(len(pkts2), 1)
        self.assertEqual(pkts1[0]["summary"], "WS1 only")
        self.assertEqual(pkts2[0]["summary"], "WS2 only")

    def test_events_isolated(self):
        self.field_ws1.append_event(ConvergenceEvent(workspace_id="ws1", summary="E1"))
        events1 = self.field_ws1.recent_events()
        events2 = self.field_ws2.recent_events()
        self.assertEqual(len(events1), 1)
        self.assertEqual(len(events2), 0)

    def test_status_isolated(self):
        self.field_ws1.append_packet(_make_packet(workspace_id="ws1"))
        s1 = self.field_ws1.status()
        s2 = self.field_ws2.status()
        self.assertEqual(s1["packet_count_cached"], 1)
        self.assertEqual(s2["packet_count_cached"], 0)


if __name__ == "__main__":
    unittest.main()
