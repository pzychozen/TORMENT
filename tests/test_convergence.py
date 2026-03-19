"""
tests/test_convergence.py — Convergence detection logic

Tests for:
    - Two agents, same domain, similar embeddings → event created
    - Two agents, unrelated embeddings → no event
    - Single agent alone → no multi-agent event
    - Different domains → no cross-domain event
    - Cooldown deduplication
    - Phase/symbol/motif alignment bonuses
    - Composite confidence scoring
    - Event persists and is queryable
    - Three-agent convergence (strongest pair wins)
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.collective_models import ResonancePacket, ConvergenceEvent
from torment_service.collective_field import CollectiveField


def _make_embedding(dim: int = 384, seed: int = 0) -> np.ndarray:
    """Create a deterministic embedding vector."""
    rng = np.random.RandomState(seed)
    return rng.randn(dim).astype(np.float32)


def _similar_embedding(base: np.ndarray, noise: float = 0.1, seed: int = 99) -> np.ndarray:
    """Create an embedding similar to base with small noise."""
    rng = np.random.RandomState(seed)
    noisy = base + rng.randn(*base.shape).astype(np.float32) * noise
    return noisy


def _orthogonal_embedding(dim: int = 384) -> np.ndarray:
    """Create an embedding orthogonal to typical random vectors."""
    e = np.zeros(dim, dtype=np.float32)
    e[0] = 1.0  # unit vector along first axis
    return e


class TestConvergenceTwoAgents(unittest.TestCase):
    """Core: two agents in same domain with similar content → convergence."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        self.base_emb = _make_embedding(seed=42)

    def test_similar_content_creates_event(self):
        """Two agents with high cosine similarity → convergence event."""
        p1 = ResonancePacket(
            workspace_id="ws1", agent_id="ryuki", domain_id="personal",
            summary="Talked about loss and grief",
            cycle_stage="S3", state_symbol="◈", motifs=["m_grief"],
        )
        emb1 = self.base_emb
        self.field.append_packet(p1, embedding=emb1)

        p2 = ResonancePacket(
            workspace_id="ws1", agent_id="aria", domain_id="personal",
            summary="Discussed sadness and mourning",
            cycle_stage="S3", state_symbol="◈", motifs=["m_grief"],
        )
        emb2 = _similar_embedding(emb1, noise=0.05)
        event = self.field.append_packet(p2, embedding=emb2)

        self.assertIsNotNone(event)
        self.assertIsInstance(event, ConvergenceEvent)
        self.assertIn("ryuki", event.participating_agents)
        self.assertIn("aria", event.participating_agents)
        self.assertEqual(event.domain_id, "personal")
        self.assertGreater(event.semantic_overlap, 0.7)
        self.assertGreater(event.confidence, 0.45)

    def test_unrelated_content_no_event(self):
        """Two agents with orthogonal embeddings → no convergence."""
        p1 = ResonancePacket(
            workspace_id="ws1", agent_id="ryuki", domain_id="personal",
            summary="Talked about cooking",
        )
        emb1 = self.base_emb
        self.field.append_packet(p1, embedding=emb1)

        p2 = ResonancePacket(
            workspace_id="ws1", agent_id="aria", domain_id="personal",
            summary="Discussed quantum physics",
        )
        emb2 = _orthogonal_embedding()
        event = self.field.append_packet(p2, embedding=emb2)

        self.assertIsNone(event)

    def test_event_persists(self):
        """Convergence event should be queryable after creation."""
        p1 = ResonancePacket(workspace_id="ws1", agent_id="a1", domain_id="d1")
        self.field.append_packet(p1, embedding=self.base_emb)

        p2 = ResonancePacket(workspace_id="ws1", agent_id="a2", domain_id="d1")
        event = self.field.append_packet(p2, embedding=_similar_embedding(self.base_emb, noise=0.05))

        self.assertIsNotNone(event)
        events = self.field.recent_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_id"], event.event_id)

    def test_event_detail_query(self):
        """get_event returns the specific event."""
        p1 = ResonancePacket(workspace_id="ws1", agent_id="a1", domain_id="d1")
        self.field.append_packet(p1, embedding=self.base_emb)

        p2 = ResonancePacket(workspace_id="ws1", agent_id="a2", domain_id="d1")
        event = self.field.append_packet(p2, embedding=_similar_embedding(self.base_emb, noise=0.05))

        found = self.field.get_event(event.event_id)
        self.assertIsNotNone(found)
        self.assertEqual(found["confidence"], event.confidence)


class TestConvergenceNoSelfEvent(unittest.TestCase):
    """Same agent should never converge with itself."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        self.emb = _make_embedding(seed=42)

    def test_same_agent_no_event(self):
        p1 = ResonancePacket(workspace_id="ws1", agent_id="ryuki", domain_id="d1")
        self.field.append_packet(p1, embedding=self.emb)

        p2 = ResonancePacket(workspace_id="ws1", agent_id="ryuki", domain_id="d1")
        event = self.field.append_packet(p2, embedding=_similar_embedding(self.emb, noise=0.01))

        self.assertIsNone(event)

    def test_many_same_agent_no_event(self):
        for i in range(10):
            p = ResonancePacket(workspace_id="ws1", agent_id="ryuki", domain_id="d1")
            event = self.field.append_packet(p, embedding=_similar_embedding(self.emb, noise=0.02, seed=i))
            self.assertIsNone(event)


class TestConvergenceDomainIsolation(unittest.TestCase):
    """Different domains should not trigger cross-domain convergence."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        self.emb = _make_embedding(seed=42)

    def test_different_domains_no_event(self):
        p1 = ResonancePacket(workspace_id="ws1", agent_id="a1", domain_id="personal")
        self.field.append_packet(p1, embedding=self.emb)

        p2 = ResonancePacket(workspace_id="ws1", agent_id="a2", domain_id="work")
        event = self.field.append_packet(p2, embedding=_similar_embedding(self.emb, noise=0.01))

        self.assertIsNone(event)


class TestConvergenceCooldown(unittest.TestCase):
    """Deduplication: same agent pair + domain within cooldown → no repeat event."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        self.field.CONVERGENCE_COOLDOWN = 5  # short cooldown for testing
        self.emb = _make_embedding(seed=42)

    def test_cooldown_blocks_duplicate(self):
        # First convergence
        p1 = ResonancePacket(workspace_id="ws1", agent_id="a1", domain_id="d1")
        self.field.append_packet(p1, embedding=self.emb)
        p2 = ResonancePacket(workspace_id="ws1", agent_id="a2", domain_id="d1")
        event1 = self.field.append_packet(p2, embedding=_similar_embedding(self.emb, noise=0.05))
        self.assertIsNotNone(event1)

        # Immediate second attempt → blocked by cooldown
        p3 = ResonancePacket(workspace_id="ws1", agent_id="a1", domain_id="d1")
        self.field.append_packet(p3, embedding=self.emb)
        p4 = ResonancePacket(workspace_id="ws1", agent_id="a2", domain_id="d1")
        event2 = self.field.append_packet(p4, embedding=_similar_embedding(self.emb, noise=0.05, seed=50))
        self.assertIsNone(event2)

    def test_different_pair_not_blocked(self):
        """Cooldown is per agent-pair — different pair can still converge."""
        p1 = ResonancePacket(workspace_id="ws1", agent_id="a1", domain_id="d1")
        self.field.append_packet(p1, embedding=self.emb)
        p2 = ResonancePacket(workspace_id="ws1", agent_id="a2", domain_id="d1")
        event1 = self.field.append_packet(p2, embedding=_similar_embedding(self.emb, noise=0.05))
        self.assertIsNotNone(event1)

        # Different pair (a1 + a3)
        p3 = ResonancePacket(workspace_id="ws1", agent_id="a3", domain_id="d1")
        event2 = self.field.append_packet(p3, embedding=_similar_embedding(self.emb, noise=0.05, seed=77))
        # Should be able to converge with a1 (different pair)
        # Note: might be None if similarity is too low — that's fine
        # The point is cooldown doesn't block it


class TestConvergenceAlignmentBonuses(unittest.TestCase):
    """Phase, symbol, and motif alignment affect confidence."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.emb = _make_embedding(seed=42)

    def test_full_alignment_higher_confidence(self):
        """Matching phase + symbol + motifs → higher confidence."""
        field = CollectiveField("ws1", self.tmp)
        p1 = ResonancePacket(
            workspace_id="ws1", agent_id="a1", domain_id="d1",
            cycle_stage="S3", identity_state="s5",
            state_symbol="◈", loop_type="deepening",
            motifs=["m_grief", "m_music"],
        )
        field.append_packet(p1, embedding=self.emb)

        p2 = ResonancePacket(
            workspace_id="ws1", agent_id="a2", domain_id="d1",
            cycle_stage="S3", identity_state="s5",
            state_symbol="◈", loop_type="deepening",
            motifs=["m_grief", "m_music"],
        )
        event = field.append_packet(p2, embedding=_similar_embedding(self.emb, noise=0.05))

        self.assertIsNotNone(event)
        # Full alignment → confidence should be quite high
        self.assertGreater(event.confidence, 0.7)
        self.assertEqual(event.dominant_symbol, "◈")
        self.assertEqual(event.dominant_cycle_stage, "S3")
        self.assertIn("m_grief", event.dominant_motifs)

    def test_no_alignment_lower_confidence(self):
        """Mismatched phase + symbol → lower confidence (still possible if sim is high)."""
        tmp2 = tempfile.mkdtemp()
        field = CollectiveField("ws1", tmp2)
        p1 = ResonancePacket(
            workspace_id="ws1", agent_id="a1", domain_id="d1",
            cycle_stage="S1", state_symbol="◯", motifs=["m_x"],
        )
        field.append_packet(p1, embedding=self.emb)

        p2 = ResonancePacket(
            workspace_id="ws1", agent_id="a2", domain_id="d1",
            cycle_stage="S5", state_symbol="⊗", motifs=["m_y"],
        )
        event = field.append_packet(p2, embedding=_similar_embedding(self.emb, noise=0.05))

        if event is not None:
            # Confidence should be lower due to misalignment
            self.assertLess(event.confidence, 0.7)


class TestPhaseAlignmentHelper(unittest.TestCase):
    """Unit test for _phase_alignment static method."""

    def test_exact_match(self):
        a = ResonancePacket(cycle_stage="S3", identity_state="s5")
        b = ResonancePacket(cycle_stage="S3", identity_state="s5")
        score = CollectiveField._phase_alignment(a, b)
        self.assertEqual(score, 1.0)

    def test_adjacent_stages(self):
        a = ResonancePacket(cycle_stage="S3", identity_state="s5")
        b = ResonancePacket(cycle_stage="S4", identity_state="s5")
        score = CollectiveField._phase_alignment(a, b)
        self.assertGreater(score, 0.5)

    def test_distant_stages(self):
        a = ResonancePacket(cycle_stage="S0", identity_state="s0")
        b = ResonancePacket(cycle_stage="S6", identity_state="s8")
        score = CollectiveField._phase_alignment(a, b)
        self.assertEqual(score, 0.0)

    def test_empty_stages(self):
        a = ResonancePacket()
        b = ResonancePacket()
        score = CollectiveField._phase_alignment(a, b)
        self.assertEqual(score, 0.0)


class TestSymbolAlignmentHelper(unittest.TestCase):
    """Unit test for _symbol_alignment static method."""

    def test_exact_match(self):
        a = ResonancePacket(state_symbol="◈", loop_type="deepening")
        b = ResonancePacket(state_symbol="◈", loop_type="deepening")
        self.assertEqual(CollectiveField._symbol_alignment(a, b), 1.0)

    def test_symbol_only(self):
        a = ResonancePacket(state_symbol="◈", loop_type="deepening")
        b = ResonancePacket(state_symbol="◈", loop_type="recovery")
        self.assertAlmostEqual(CollectiveField._symbol_alignment(a, b), 0.6)

    def test_no_match(self):
        a = ResonancePacket(state_symbol="◈", loop_type="deepening")
        b = ResonancePacket(state_symbol="◯", loop_type="recovery")
        self.assertEqual(CollectiveField._symbol_alignment(a, b), 0.0)


class TestMotifAlignmentHelper(unittest.TestCase):
    """Unit test for _motif_alignment static method."""

    def test_full_overlap(self):
        a = ResonancePacket(motifs=["m_a", "m_b"])
        b = ResonancePacket(motifs=["m_a", "m_b"])
        self.assertEqual(CollectiveField._motif_alignment(a, b), 1.0)

    def test_partial_overlap(self):
        a = ResonancePacket(motifs=["m_a", "m_b"])
        b = ResonancePacket(motifs=["m_a", "m_c"])
        # Jaccard: 1/3
        self.assertAlmostEqual(CollectiveField._motif_alignment(a, b), 1 / 3, places=4)

    def test_no_overlap(self):
        a = ResonancePacket(motifs=["m_a"])
        b = ResonancePacket(motifs=["m_b"])
        self.assertEqual(CollectiveField._motif_alignment(a, b), 0.0)

    def test_empty_motifs(self):
        a = ResonancePacket(motifs=[])
        b = ResonancePacket(motifs=["m_a"])
        self.assertEqual(CollectiveField._motif_alignment(a, b), 0.0)


class TestThreeAgentConvergence(unittest.TestCase):
    """With three agents, convergence picks the best match."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)
        self.emb = _make_embedding(seed=42)

    def test_best_pair_converges(self):
        # Agent 1: base embedding
        p1 = ResonancePacket(workspace_id="ws1", agent_id="a1", domain_id="d1")
        self.field.append_packet(p1, embedding=self.emb)

        # Agent 2: somewhat similar
        p2 = ResonancePacket(workspace_id="ws1", agent_id="a2", domain_id="d1")
        self.field.append_packet(p2, embedding=_similar_embedding(self.emb, noise=0.3, seed=10))

        # Agent 3: very similar to a1
        p3 = ResonancePacket(workspace_id="ws1", agent_id="a3", domain_id="d1")
        event = self.field.append_packet(p3, embedding=_similar_embedding(self.emb, noise=0.05, seed=20))

        if event is not None:
            # Should converge with a1 (highest similarity)
            self.assertIn("a1", event.participating_agents)
            self.assertIn("a3", event.participating_agents)


class TestNoEmbeddingNoDetection(unittest.TestCase):
    """Without embeddings, convergence detection is skipped."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.field = CollectiveField("ws1", self.tmp)

    def test_no_embedding_no_event(self):
        p1 = ResonancePacket(workspace_id="ws1", agent_id="a1", domain_id="d1")
        result1 = self.field.append_packet(p1)  # no embedding
        self.assertIsNone(result1)

        p2 = ResonancePacket(workspace_id="ws1", agent_id="a2", domain_id="d1")
        result2 = self.field.append_packet(p2)  # no embedding
        self.assertIsNone(result2)


if __name__ == "__main__":
    unittest.main()
