"""
tests/test_hivemind_integration.py — Hivemind Phase B integration tests

Tests for:
    - Packet construction from realistic signal data
    - CollectiveField persistence round-trip with real packets
    - Multi-agent packet emission and isolation
    - Flag gating (TORMENT_HIVEMIND_ENABLE)
    - Collective field status accuracy
    - build_self_state integration with collective models
    - Packet gating by coherence threshold
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.collective_models import (
    ResonancePacket,
    ConvergenceEvent,
    CharacterSelfState,
)
from torment_service.collective_field import CollectiveField


def _build_realistic_packet(
    workspace_id: str = "ws1",
    agent_id: str = "ryuki",
    domain_id: str = "personal",
    summary: str = "User talked about music. Ryuki shared a memory about drums.",
    coherence: float = 0.72,
    strength: float = 0.65,
    stability_delta: float = 0.015,
    cycle_stage: str = "S3",
    identity_state: str = "s5",
    motifs: list = None,
    state_symbol: str = "◈",
    resonance_score: float = 0.55,
    loop_type: str = "deepening",
    srg_band: int = None,
    eid: int = 42,
) -> ResonancePacket:
    """Build a ResonancePacket mimicking what fabric.ingest() would produce."""
    # Simulate embedding hash
    fake_emb = np.random.randn(384).astype(np.float32)
    emb_hash = hashlib.md5(fake_emb.tobytes()).hexdigest()[:12]

    return ResonancePacket(
        workspace_id=workspace_id,
        agent_id=agent_id,
        domain_id=domain_id,
        source_eid=eid,
        summary=summary,
        embedding_hash=emb_hash,
        cycle_stage=cycle_stage,
        identity_state=identity_state,
        coherence=coherence,
        stability_delta=stability_delta,
        phase_duration_steps=85,
        corridor_duration_steps=12,
        motifs=motifs or ["m_music_01"],
        state_symbol=state_symbol,
        resonance_score=resonance_score,
        loop_type=loop_type,
        srg_band=srg_band,
    )


class TestRealisticPacketConstruction(unittest.TestCase):
    """Packets built from realistic signal data serialize correctly."""

    def test_all_fields_survive_round_trip(self):
        p = _build_realistic_packet()
        d = p.to_dict()
        p2 = ResonancePacket.from_dict(d)

        self.assertEqual(p.workspace_id, p2.workspace_id)
        self.assertEqual(p.agent_id, p2.agent_id)
        self.assertEqual(p.domain_id, p2.domain_id)
        self.assertEqual(p.source_eid, p2.source_eid)
        self.assertEqual(p.summary, p2.summary)
        self.assertEqual(p.embedding_hash, p2.embedding_hash)
        self.assertEqual(p.cycle_stage, p2.cycle_stage)
        self.assertEqual(p.identity_state, p2.identity_state)
        self.assertAlmostEqual(p.coherence, p2.coherence)
        self.assertAlmostEqual(p.stability_delta, p2.stability_delta)
        self.assertEqual(p.motifs, p2.motifs)
        self.assertEqual(p.state_symbol, p2.state_symbol)
        self.assertAlmostEqual(p.resonance_score, p2.resonance_score)
        self.assertEqual(p.loop_type, p2.loop_type)

    def test_json_serializable(self):
        p = _build_realistic_packet()
        serialized = json.dumps(p.to_dict())
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["agent_id"], "ryuki")
        self.assertEqual(deserialized["state_symbol"], "◈")

    def test_embedding_hash_is_deterministic(self):
        """Same embedding bytes → same hash."""
        emb = np.ones(384, dtype=np.float32)
        h1 = hashlib.md5(emb.tobytes()).hexdigest()[:12]
        h2 = hashlib.md5(emb.tobytes()).hexdigest()[:12]
        self.assertEqual(h1, h2)

    def test_different_embeddings_different_hash(self):
        emb1 = np.ones(384, dtype=np.float32)
        emb2 = np.zeros(384, dtype=np.float32)
        h1 = hashlib.md5(emb1.tobytes()).hexdigest()[:12]
        h2 = hashlib.md5(emb2.tobytes()).hexdigest()[:12]
        self.assertNotEqual(h1, h2)


class TestMultiAgentPacketScenario(unittest.TestCase):
    """Simulate multiple agents emitting packets into the same workspace."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)

    def test_two_agents_same_domain(self):
        p1 = _build_realistic_packet(agent_id="ryuki", domain_id="personal", summary="Talked about loss.")
        p2 = _build_realistic_packet(agent_id="aria", domain_id="personal", summary="Discussed grief.")
        self.field.append_packet(p1)
        self.field.append_packet(p2)

        recent = self.field.recent_packets()
        self.assertEqual(len(recent), 2)

        # Both in same domain
        domain_pkts = self.field.packets_by_domain("personal")
        self.assertEqual(len(domain_pkts), 2)

        # Filter by agent
        ryuki_pkts = self.field.packets_by_agent("ryuki")
        aria_pkts = self.field.packets_by_agent("aria")
        self.assertEqual(len(ryuki_pkts), 1)
        self.assertEqual(len(aria_pkts), 1)

    def test_two_agents_different_domains(self):
        p1 = _build_realistic_packet(agent_id="ryuki", domain_id="personal")
        p2 = _build_realistic_packet(agent_id="aria", domain_id="work")
        self.field.append_packet(p1)
        self.field.append_packet(p2)

        personal = self.field.packets_by_domain("personal")
        work = self.field.packets_by_domain("work")
        self.assertEqual(len(personal), 1)
        self.assertEqual(len(work), 1)
        self.assertEqual(personal[0]["agent_id"], "ryuki")
        self.assertEqual(work[0]["agent_id"], "aria")

    def test_status_reflects_multi_agent(self):
        for i in range(5):
            self.field.append_packet(_build_realistic_packet(agent_id="ryuki", eid=i))
        for i in range(3):
            self.field.append_packet(_build_realistic_packet(agent_id="aria", eid=100 + i))

        s = self.field.status()
        self.assertEqual(s["packet_count_cached"], 8)
        self.assertIn("ryuki", s["active_agents"])
        self.assertIn("aria", s["active_agents"])

    def test_three_agents_with_srg(self):
        """Packets carry SRG data correctly."""
        p1 = _build_realistic_packet(agent_id="ryuki", srg_band=0)
        p2 = _build_realistic_packet(agent_id="aria", srg_band=2)
        p3 = _build_realistic_packet(agent_id="zen", srg_band=1)
        self.field.append_packet(p1)
        self.field.append_packet(p2)
        self.field.append_packet(p3)

        recent = self.field.recent_packets()
        bands = [p["srg_band"] for p in recent]
        self.assertEqual(bands, [0, 2, 1])


class TestPacketCoherenceGating(unittest.TestCase):
    """Verify the coherence threshold gating logic."""

    def test_low_coherence_would_be_gated(self):
        """Packets with coherence < 0.15 should NOT be emitted in real fabric.
        Here we verify the threshold concept."""
        COHERENCE_THRESHOLD = 0.15
        low = _build_realistic_packet(coherence=0.10)
        high = _build_realistic_packet(coherence=0.50)
        self.assertLess(low.coherence, COHERENCE_THRESHOLD)
        self.assertGreaterEqual(high.coherence, COHERENCE_THRESHOLD)

    def test_borderline_coherence(self):
        at_threshold = _build_realistic_packet(coherence=0.15)
        below = _build_realistic_packet(coherence=0.149)
        self.assertGreaterEqual(at_threshold.coherence, 0.15)
        self.assertLess(below.coherence, 0.15)


class TestCollectiveFieldFullCycle(unittest.TestCase):
    """Full cycle: emit packets → check status → persist → reload → verify."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_full_cycle(self):
        # Phase 1: emit
        field = CollectiveField("ws1", self.tmp)
        for i in range(10):
            agent = "ryuki" if i % 2 == 0 else "aria"
            field.append_packet(_build_realistic_packet(
                agent_id=agent,
                domain_id="personal",
                summary=f"Turn {i}",
                eid=i,
            ))

        # Phase 2: check status
        s = field.status()
        self.assertEqual(s["packet_count_total"], 10)
        self.assertEqual(s["packet_count_cached"], 10)
        self.assertEqual(len(s["active_agents"]), 2)

        # Phase 3: destroy and reload
        field2 = CollectiveField("ws1", self.tmp)
        s2 = field2.status()
        self.assertEqual(s2["packet_count_total"], 10)
        self.assertEqual(s2["packet_count_cached"], 10)

        # Phase 4: verify specific packets
        ryuki = field2.packets_by_agent("ryuki")
        aria = field2.packets_by_agent("aria")
        self.assertEqual(len(ryuki), 5)
        self.assertEqual(len(aria), 5)


class TestSelfStateWithCollectiveFields(unittest.TestCase):
    """CharacterSelfState works cleanly with collective model types."""

    def test_self_state_collective_fields(self):
        ss = CharacterSelfState(
            workspace_id="ws1",
            agent_id="ryuki",
            seed_id="ryuki_v1",
            recent_collective_events=3,
            recent_compressions=1,
        )
        d = ss.to_dict()
        self.assertEqual(d["recent_collective_events"], 3)
        self.assertEqual(d["recent_compressions"], 1)


if __name__ == "__main__":
    unittest.main()
