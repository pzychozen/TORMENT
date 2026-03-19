"""
tests/test_collective_models.py — Data contracts for TORMENT Hivemind

Tests for:
    - ResonancePacket serialization round-trip
    - ConvergenceEvent serialization round-trip
    - CharacterSelfState serialization round-trip
    - MemoryGovernanceFlags serialization round-trip
    - Default field values
    - Auto-generated IDs and timestamps
    - Unknown fields gracefully ignored
"""
from __future__ import annotations

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.collective_models import (
    ResonancePacket,
    ConvergenceEvent,
    CharacterSelfState,
    MemoryGovernanceFlags,
)


class TestResonancePacket(unittest.TestCase):
    """ResonancePacket data contract."""

    def test_defaults(self):
        p = ResonancePacket()
        self.assertTrue(p.packet_id.startswith("pkt_"))
        self.assertGreater(p.ts, 0)
        self.assertEqual(p.workspace_id, "")
        self.assertEqual(p.coherence, 0.0)
        self.assertEqual(p.motifs, [])
        self.assertTrue(p.permissions["shareable"])
        self.assertTrue(p.permissions["reingestable"])

    def test_custom_fields(self):
        p = ResonancePacket(
            workspace_id="ws1",
            agent_id="ryuki",
            domain_id="personal",
            summary="Discussed music",
            coherence=0.85,
            cycle_stage="S3",
            motifs=["m_01", "m_02"],
            state_symbol="◈",
            srg_band=2,
            srg_heartbeat_class="A",
        )
        self.assertEqual(p.workspace_id, "ws1")
        self.assertEqual(p.agent_id, "ryuki")
        self.assertEqual(p.coherence, 0.85)
        self.assertEqual(p.motifs, ["m_01", "m_02"])
        self.assertEqual(p.srg_band, 2)

    def test_round_trip(self):
        p = ResonancePacket(
            workspace_id="ws1",
            agent_id="test",
            domain_id="d1",
            summary="Test packet",
            coherence=0.75,
            stability_delta=0.02,
            cycle_stage="S2",
            identity_state="s4",
            motifs=["m_01"],
            state_symbol="∿",
            resonance_score=0.6,
            loop_type="deepening",
            drift_score=-0.1,
            drift_direction="away_seed",
            srg_band=1,
            tags=["important"],
        )
        d = p.to_dict()
        p2 = ResonancePacket.from_dict(d)
        self.assertEqual(p.packet_id, p2.packet_id)
        self.assertEqual(p.workspace_id, p2.workspace_id)
        self.assertEqual(p.coherence, p2.coherence)
        self.assertEqual(p.motifs, p2.motifs)
        self.assertEqual(p.state_symbol, p2.state_symbol)
        self.assertEqual(p.srg_band, p2.srg_band)
        self.assertEqual(p.tags, p2.tags)

    def test_unknown_fields_ignored(self):
        d = {"packet_id": "pkt_test", "workspace_id": "ws1", "unknown_field": 999}
        p = ResonancePacket.from_dict(d)
        self.assertEqual(p.packet_id, "pkt_test")
        self.assertEqual(p.workspace_id, "ws1")

    def test_auto_id_unique(self):
        p1 = ResonancePacket()
        p2 = ResonancePacket()
        self.assertNotEqual(p1.packet_id, p2.packet_id)

    def test_permissions_defaults(self):
        p = ResonancePacket()
        self.assertTrue(p.permissions["shareable"])
        self.assertTrue(p.permissions["reingestable"])
        self.assertTrue(p.permissions["visible_to_workspace"])

    def test_permissions_custom(self):
        p = ResonancePacket(permissions={"shareable": False, "reingestable": False, "visible_to_workspace": True})
        self.assertFalse(p.permissions["shareable"])
        self.assertFalse(p.permissions["reingestable"])


class TestConvergenceEvent(unittest.TestCase):
    """ConvergenceEvent data contract."""

    def test_defaults(self):
        e = ConvergenceEvent()
        self.assertTrue(e.event_id.startswith("cev_"))
        self.assertGreater(e.ts_start, 0)
        self.assertEqual(e.ts_end, e.ts_start)
        self.assertEqual(e.participating_agents, [])
        self.assertEqual(e.confidence, 0.0)

    def test_custom_fields(self):
        e = ConvergenceEvent(
            workspace_id="ws1",
            domain_id="personal",
            participating_agents=["ryuki", "aria"],
            source_packets=["pkt_01", "pkt_02"],
            confidence=0.82,
            semantic_overlap=0.88,
            phase_alignment=0.7,
            dominant_motifs=["m_music"],
            dominant_symbol="◈",
            summary="Both agents discussed music themes",
        )
        self.assertEqual(len(e.participating_agents), 2)
        self.assertEqual(e.confidence, 0.82)
        self.assertEqual(e.semantic_overlap, 0.88)

    def test_round_trip(self):
        e = ConvergenceEvent(
            workspace_id="ws1",
            domain_id="d1",
            participating_agents=["a1", "a2"],
            source_packets=["pkt_x", "pkt_y"],
            source_eids=[10, 20],
            confidence=0.9,
            persistence=0.5,
            semantic_overlap=0.85,
            phase_alignment=0.6,
            symbol_alignment=0.4,
            dominant_motifs=["m1", "m2"],
            dominant_symbol="◯",
            dominant_cycle_stage="S3",
            summary="Test convergence",
        )
        d = e.to_dict()
        e2 = ConvergenceEvent.from_dict(d)
        self.assertEqual(e.event_id, e2.event_id)
        self.assertEqual(e.participating_agents, e2.participating_agents)
        self.assertEqual(e.confidence, e2.confidence)
        self.assertEqual(e.semantic_overlap, e2.semantic_overlap)
        self.assertEqual(e.dominant_motifs, e2.dominant_motifs)

    def test_unknown_fields_ignored(self):
        d = {"event_id": "cev_test", "workspace_id": "ws1", "future_field": True}
        e = ConvergenceEvent.from_dict(d)
        self.assertEqual(e.event_id, "cev_test")

    def test_policy_flags_default(self):
        e = ConvergenceEvent()
        self.assertTrue(e.policy_flags["reingestable"])
        self.assertFalse(e.policy_flags["proposal_eligible"])


class TestCharacterSelfState(unittest.TestCase):
    """CharacterSelfState data contract."""

    def test_defaults(self):
        ss = CharacterSelfState()
        self.assertEqual(ss.workspace_id, "")
        self.assertEqual(ss.drift_score, 0.0)
        self.assertEqual(ss.drift_direction, "stable")
        self.assertEqual(ss.seed_basin_role, "plateau")
        self.assertEqual(ss.core_count, 0)
        self.assertFalse(ss.srg_enabled)
        self.assertIsNone(ss.seed_id)

    def test_populated(self):
        ss = CharacterSelfState(
            workspace_id="ws1",
            agent_id="ryuki",
            seed_id="ryuki_v1",
            character_name="Ryuki Nox",
            drift_score=-0.12,
            drift_direction="away_seed",
            distance_to_seed=0.25,
            seed_basin_role="basin",
            seed_basin_phi=0.8,
            core_count=5,
            relational_count=42,
            situational_count=120,
            phase_duration_steps=85,
            last_cycle_stage="S3",
            srg_enabled=True,
            srg_dominant_band=2,
        )
        self.assertEqual(ss.character_name, "Ryuki Nox")
        self.assertEqual(ss.drift_score, -0.12)
        self.assertEqual(ss.core_count, 5)
        self.assertTrue(ss.srg_enabled)

    def test_round_trip(self):
        ss = CharacterSelfState(
            workspace_id="ws1",
            agent_id="test",
            seed_id="s1",
            drift_score=0.05,
            core_count=3,
            relational_count=10,
            situational_count=50,
        )
        d = ss.to_dict()
        ss2 = CharacterSelfState.from_dict(d)
        self.assertEqual(ss.workspace_id, ss2.workspace_id)
        self.assertEqual(ss.seed_id, ss2.seed_id)
        self.assertEqual(ss.drift_score, ss2.drift_score)
        self.assertEqual(ss.core_count, ss2.core_count)

    def test_unknown_fields_ignored(self):
        d = {"workspace_id": "ws1", "agent_id": "a1", "nonexistent": 42}
        ss = CharacterSelfState.from_dict(d)
        self.assertEqual(ss.workspace_id, "ws1")


class TestMemoryGovernanceFlags(unittest.TestCase):
    """MemoryGovernanceFlags data contract."""

    def test_defaults_all_false(self):
        g = MemoryGovernanceFlags()
        self.assertFalse(g.protected)
        self.assertFalse(g.non_shareable)
        self.assertFalse(g.decay_accelerated)
        self.assertFalse(g.collective_export_blocked)
        self.assertFalse(g.collective_reingest_blocked)

    def test_custom(self):
        g = MemoryGovernanceFlags(protected=True, non_shareable=True)
        self.assertTrue(g.protected)
        self.assertTrue(g.non_shareable)
        self.assertFalse(g.decay_accelerated)

    def test_round_trip(self):
        g = MemoryGovernanceFlags(
            protected=True,
            non_shareable=False,
            decay_accelerated=True,
            collective_export_blocked=True,
            collective_reingest_blocked=False,
        )
        d = g.to_dict()
        g2 = MemoryGovernanceFlags.from_dict(d)
        self.assertEqual(g.protected, g2.protected)
        self.assertEqual(g.decay_accelerated, g2.decay_accelerated)
        self.assertEqual(g.collective_export_blocked, g2.collective_export_blocked)

    def test_unknown_fields_ignored(self):
        d = {"protected": True, "future_flag": True}
        g = MemoryGovernanceFlags.from_dict(d)
        self.assertTrue(g.protected)


class TestCrossModelInteraction(unittest.TestCase):
    """Verify models can reference each other's IDs cleanly."""

    def test_packet_ids_in_event(self):
        p1 = ResonancePacket(workspace_id="ws1", agent_id="a1")
        p2 = ResonancePacket(workspace_id="ws1", agent_id="a2")
        e = ConvergenceEvent(
            workspace_id="ws1",
            source_packets=[p1.packet_id, p2.packet_id],
            participating_agents=[p1.agent_id, p2.agent_id],
        )
        self.assertIn(p1.packet_id, e.source_packets)
        self.assertIn("a1", e.participating_agents)
        self.assertIn("a2", e.participating_agents)

    def test_governance_in_packet_permissions(self):
        """Governance flags should map cleanly to packet permission decisions."""
        g = MemoryGovernanceFlags(non_shareable=True)
        p = ResonancePacket(
            permissions={
                "shareable": not g.non_shareable,
                "reingestable": not g.collective_reingest_blocked,
                "visible_to_workspace": not g.collective_export_blocked,
            }
        )
        self.assertFalse(p.permissions["shareable"])
        self.assertTrue(p.permissions["reingestable"])


if __name__ == "__main__":
    unittest.main()
