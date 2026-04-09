"""
tests/test_collective_proposals.py — Phase D4 proposal bridge tests

Tests covering:
    - Persistence tracking (pattern recording, counting, window)
    - Confidence gating (below/above threshold)
    - Persistence minimum enforcement
    - Event dedup (same event doesn't produce two proposals)
    - Domain cooldown
    - Max pending per domain
    - Proposal summary format
    - Proposal drafting with registry integration
    - Full cycle (multiple events → persistence → proposal drafted)
    - Bridge configuration
    - Tracker persistence across instances
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.collective_proposals import (
    CollectiveProposalBridge,
    ConvergencePersistenceTracker,
    _pattern_key,
    PROPOSAL_CONFIDENCE_THRESHOLD,
    PROPOSAL_PERSISTENCE_MIN,
    PROPOSAL_PERSISTENCE_WINDOW,
    PROPOSAL_DOMAIN_COOLDOWN,
    PROPOSAL_MAX_PENDING_PER_DOMAIN,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal convergence event dict
# ---------------------------------------------------------------------------

def _make_event(
    event_id: str = "cev_test001",
    domain_id: str = "research",
    confidence: float = 0.80,
    agents: list = None,
    motifs: list = None,
    summary: str = "Convergence between agent_a and agent_b",
) -> dict:
    agents = agents or ["agent_a", "agent_b"]
    motifs = motifs or ["motif_loss", "motif_grief"]
    return {
        "event_id": event_id,
        "workspace_id": "ws1",
        "domain_id": domain_id,
        "confidence": confidence,
        "participating_agents": agents,
        "source_packets": ["pkt_1", "pkt_2"],
        "source_eids": [10, 20],
        "dominant_motifs": motifs,
        "summary": summary,
        "semantic_overlap": 0.82,
        "phase_alignment": 0.60,
        "symbol_alignment": 0.40,
        "ts_end": int(time.time()),
    }


# ---------------------------------------------------------------------------
# Pattern key tests
# ---------------------------------------------------------------------------

class TestPatternKey(unittest.TestCase):

    def test_deterministic(self):
        k1 = _pattern_key("research", ["motif_a", "motif_b"])
        k2 = _pattern_key("research", ["motif_b", "motif_a"])
        self.assertEqual(k1, k2)

    def test_different_domains(self):
        k1 = _pattern_key("research", ["motif_a"])
        k2 = _pattern_key("creative", ["motif_a"])
        self.assertNotEqual(k1, k2)

    def test_different_motifs(self):
        k1 = _pattern_key("research", ["motif_a"])
        k2 = _pattern_key("research", ["motif_b"])
        self.assertNotEqual(k1, k2)

    def test_empty_motifs(self):
        k = _pattern_key("research", [])
        self.assertEqual(k, "research|")

    def test_dedup_motifs(self):
        k1 = _pattern_key("research", ["motif_a", "motif_a"])
        k2 = _pattern_key("research", ["motif_a"])
        self.assertEqual(k1, k2)


# ---------------------------------------------------------------------------
# Persistence tracker tests
# ---------------------------------------------------------------------------

class TestConvergencePersistenceTracker(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_record_and_count(self):
        t = ConvergencePersistenceTracker(self.tmp, "ws1")
        event = _make_event()
        t.record_event(event)
        count = t.count_recent("research", ["motif_loss", "motif_grief"], 3600)
        self.assertEqual(count, 1)

    def test_count_multiple_events(self):
        t = ConvergencePersistenceTracker(self.tmp, "ws1")
        for i in range(3):
            event = _make_event(event_id=f"cev_{i}")
            t.record_event(event)
        count = t.count_recent("research", ["motif_loss", "motif_grief"], 3600)
        self.assertEqual(count, 3)

    def test_count_different_pattern_separate(self):
        t = ConvergencePersistenceTracker(self.tmp, "ws1")
        t.record_event(_make_event(motifs=["motif_a"]))
        t.record_event(_make_event(motifs=["motif_b"]))
        self.assertEqual(t.count_recent("research", ["motif_a"], 3600), 1)
        self.assertEqual(t.count_recent("research", ["motif_b"], 3600), 1)

    def test_event_proposed_tracking(self):
        t = ConvergencePersistenceTracker(self.tmp, "ws1")
        self.assertFalse(t.is_event_proposed("cev_1"))
        t.record_proposed("cev_1", "research")
        self.assertTrue(t.is_event_proposed("cev_1"))
        self.assertFalse(t.is_event_proposed("cev_2"))

    def test_domain_cooldown(self):
        t = ConvergencePersistenceTracker(self.tmp, "ws1")
        t.record_proposed("cev_1", "research")
        # Should be on cooldown (just recorded)
        self.assertTrue(t.is_domain_on_cooldown("research", 60))
        # Different domain should not be on cooldown
        self.assertFalse(t.is_domain_on_cooldown("creative", 60))

    def test_persistence_across_instances(self):
        t1 = ConvergencePersistenceTracker(self.tmp, "ws1")
        t1.record_event(_make_event(event_id="cev_1"))
        t1.record_proposed("cev_1", "research")

        # New instance should read from disk
        t2 = ConvergencePersistenceTracker(self.tmp, "ws1")
        self.assertEqual(t2.count_recent("research", ["motif_loss", "motif_grief"], 3600), 1)
        self.assertTrue(t2.is_event_proposed("cev_1"))

    def test_workspace_isolation(self):
        t1 = ConvergencePersistenceTracker(self.tmp, "ws1")
        t2 = ConvergencePersistenceTracker(self.tmp, "ws2")
        t1.record_event(_make_event(event_id="cev_1"))
        self.assertEqual(t1.count_recent("research", ["motif_loss", "motif_grief"], 3600), 1)
        self.assertEqual(t2.count_recent("research", ["motif_loss", "motif_grief"], 3600), 0)


# ---------------------------------------------------------------------------
# Configuration defaults tests
# ---------------------------------------------------------------------------

class TestConfigDefaults(unittest.TestCase):

    def test_confidence_threshold(self):
        self.assertEqual(PROPOSAL_CONFIDENCE_THRESHOLD, 0.70)

    def test_persistence_min(self):
        self.assertEqual(PROPOSAL_PERSISTENCE_MIN, 2)

    def test_persistence_window(self):
        self.assertEqual(PROPOSAL_PERSISTENCE_WINDOW, 7200)

    def test_domain_cooldown(self):
        self.assertEqual(PROPOSAL_DOMAIN_COOLDOWN, 1800)

    def test_max_pending(self):
        self.assertEqual(PROPOSAL_MAX_PENDING_PER_DOMAIN, 5)


# ---------------------------------------------------------------------------
# Confidence gate tests
# ---------------------------------------------------------------------------

class TestConfidenceGate(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_low_confidence_rejected(self):
        bridge = CollectiveProposalBridge(self.tmp, "ws1")
        event = _make_event(confidence=0.50)
        result = bridge.maybe_draft_proposal(event)
        self.assertFalse(result.drafted)
        self.assertIn("Confidence", result.reason)

    def test_high_confidence_passes(self):
        """High confidence alone isn't enough — still needs persistence."""
        bridge = CollectiveProposalBridge(self.tmp, "ws1")
        event = _make_event(confidence=0.90)
        result = bridge.maybe_draft_proposal(event)
        # Should pass confidence but fail persistence (first event)
        self.assertFalse(result.drafted)
        self.assertIn("persistent", result.reason)

    def test_exact_threshold(self):
        bridge = CollectiveProposalBridge(self.tmp, "ws1", confidence_threshold=0.70)
        event = _make_event(confidence=0.70)
        result = bridge.maybe_draft_proposal(event)
        # Passes confidence, fails persistence
        self.assertFalse(result.drafted)
        self.assertNotIn("Confidence", result.reason)


# ---------------------------------------------------------------------------
# Persistence gate tests
# ---------------------------------------------------------------------------

class TestPersistenceGate(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_single_event_not_persistent(self):
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=2)
        event = _make_event(confidence=0.80)
        result = bridge.maybe_draft_proposal(event)
        self.assertFalse(result.drafted)
        self.assertEqual(result.pattern_count, 1)

    def test_two_events_become_persistent(self):
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=2)
        # First event
        bridge.maybe_draft_proposal(_make_event(event_id="cev_1", confidence=0.80))
        # Second event with same pattern — should now be persistent
        result = bridge.maybe_draft_proposal(_make_event(event_id="cev_2", confidence=0.80))
        self.assertTrue(result.drafted)
        self.assertEqual(result.pattern_count, 2)

    def test_different_pattern_not_persistent(self):
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=2)
        bridge.maybe_draft_proposal(_make_event(event_id="cev_1", motifs=["motif_a"]))
        result = bridge.maybe_draft_proposal(_make_event(event_id="cev_2", motifs=["motif_b"]))
        self.assertFalse(result.drafted)

    def test_persistence_min_configurable(self):
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=3)
        # Events 1 and 2 — not enough
        bridge.maybe_draft_proposal(_make_event(event_id="cev_1"))
        result = bridge.maybe_draft_proposal(_make_event(event_id="cev_2"))
        self.assertFalse(result.drafted)
        # Event 3 — now persistent
        result = bridge.maybe_draft_proposal(_make_event(event_id="cev_3"))
        self.assertTrue(result.drafted)


# ---------------------------------------------------------------------------
# Event dedup tests
# ---------------------------------------------------------------------------

class TestEventDedup(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_same_event_not_proposed_twice(self):
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=1)
        event = _make_event(event_id="cev_1", confidence=0.80)
        # First: should draft
        r1 = bridge.maybe_draft_proposal(event)
        self.assertTrue(r1.drafted)
        # Second: same event — should be deduped
        r2 = bridge.maybe_draft_proposal(event)
        self.assertFalse(r2.drafted)
        self.assertIn("already generated", r2.reason)


# ---------------------------------------------------------------------------
# Domain cooldown tests
# ---------------------------------------------------------------------------

class TestDomainCooldown(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_domain_cooldown_blocks(self):
        bridge = CollectiveProposalBridge(
            self.tmp, "ws1",
            persistence_min=1,
            domain_cooldown=9999,  # long cooldown
        )
        # First: should draft
        r1 = bridge.maybe_draft_proposal(_make_event(event_id="cev_1"))
        self.assertTrue(r1.drafted)
        # Second: different event, same domain — cooldown should block
        r2 = bridge.maybe_draft_proposal(_make_event(event_id="cev_2"))
        self.assertFalse(r2.drafted)
        self.assertIn("cooldown", r2.reason)

    def test_different_domain_not_cooldown(self):
        bridge = CollectiveProposalBridge(
            self.tmp, "ws1",
            persistence_min=1,
            domain_cooldown=9999,
        )
        # Draft in research
        bridge.maybe_draft_proposal(_make_event(event_id="cev_1", domain_id="research"))
        # Different domain should not be on cooldown
        # But needs persistence in creative domain
        bridge.tracker.record_event(_make_event(event_id="cev_pre", domain_id="creative"))
        r2 = bridge.maybe_draft_proposal(_make_event(event_id="cev_2", domain_id="creative"))
        self.assertTrue(r2.drafted)


# ---------------------------------------------------------------------------
# Proposal summary format tests
# ---------------------------------------------------------------------------

class TestProposalSummary(unittest.TestCase):

    def test_summary_contains_collective_marker(self):
        summary = CollectiveProposalBridge._build_proposal_summary(
            _make_event(agents=["ryuki", "kael"], motifs=["motif_loss"])
        )
        self.assertIn("[collective proposal]", summary)

    def test_summary_contains_agents(self):
        summary = CollectiveProposalBridge._build_proposal_summary(
            _make_event(agents=["ryuki", "kael"])
        )
        self.assertIn("ryuki", summary)
        self.assertIn("kael", summary)

    def test_summary_contains_domain(self):
        summary = CollectiveProposalBridge._build_proposal_summary(
            _make_event(domain_id="narrative")
        )
        self.assertIn("narrative", summary)

    def test_summary_contains_source_tag(self):
        summary = CollectiveProposalBridge._build_proposal_summary(
            _make_event(event_id="cev_xyz")
        )
        self.assertIn("[collective_source:cev_xyz]", summary)

    def test_summary_contains_confidence(self):
        summary = CollectiveProposalBridge._build_proposal_summary(
            _make_event(confidence=0.85)
        )
        self.assertIn("0.85", summary)


# ---------------------------------------------------------------------------
# Proposal registry integration tests
# ---------------------------------------------------------------------------

class TestProposalRegistryIntegration(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_draft_with_mock_registry(self):
        """Proposal is submitted to registry when available."""
        import numpy as np
        mock_reg = MagicMock()
        mock_proposal = MagicMock()
        mock_proposal.proposal_id = "prop_123"
        mock_reg.submit.return_value = mock_proposal
        mock_reg.list_pending.return_value = []

        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=1)
        event = _make_event(confidence=0.80)
        emb = np.random.randn(128).astype("float32")

        result = bridge.maybe_draft_proposal(event, proposal_registry=mock_reg, embedding=emb)
        self.assertTrue(result.drafted)
        self.assertEqual(result.proposal_id, "prop_123")
        mock_reg.submit.assert_called_once()

    def test_draft_without_registry(self):
        """Proposal is tracked even without a registry."""
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=1)
        event = _make_event(confidence=0.80)
        result = bridge.maybe_draft_proposal(event)
        self.assertTrue(result.drafted)
        self.assertIsNone(result.proposal_id)

    def test_max_pending_enforced(self):
        """If domain has too many pending collective proposals, block."""
        import numpy as np

        # Create mock proposals with collective_source note
        mock_proposals = []
        for i in range(5):
            p = MagicMock()
            p.note = f"[collective_source:cev_{i}]"
            mock_proposals.append(p)

        mock_reg = MagicMock()
        mock_reg.list_pending.return_value = mock_proposals

        bridge = CollectiveProposalBridge(
            self.tmp, "ws1",
            persistence_min=1,
            max_pending_per_domain=5,
        )
        event = _make_event(confidence=0.80)
        emb = np.random.randn(128).astype("float32")
        result = bridge.maybe_draft_proposal(event, proposal_registry=mock_reg, embedding=emb)
        self.assertFalse(result.drafted)
        self.assertIn("pending collective proposals", result.reason)


# ---------------------------------------------------------------------------
# Full cycle simulation
# ---------------------------------------------------------------------------

class TestFullCycleSimulation(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_multi_event_persistence_to_proposal(self):
        """Simulate: 3 similar events → persistence met → proposal drafted."""
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=3)

        # Events 1 and 2: not persistent enough
        r1 = bridge.maybe_draft_proposal(_make_event(event_id="cev_1"))
        self.assertFalse(r1.drafted)
        r2 = bridge.maybe_draft_proposal(_make_event(event_id="cev_2"))
        self.assertFalse(r2.drafted)

        # Event 3: persistence met, proposal drafted
        r3 = bridge.maybe_draft_proposal(_make_event(event_id="cev_3"))
        self.assertTrue(r3.drafted)
        self.assertEqual(r3.pattern_count, 3)
        self.assertEqual(r3.event_id, "cev_3")

    def test_mixed_patterns_independent(self):
        """Different motif patterns are tracked independently."""
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=2, domain_cooldown=0)

        # Pattern A
        bridge.maybe_draft_proposal(_make_event(event_id="cev_a1", motifs=["loss"]))
        # Pattern B
        bridge.maybe_draft_proposal(_make_event(event_id="cev_b1", motifs=["joy"]))

        # Pattern A gets second event — should draft
        r_a2 = bridge.maybe_draft_proposal(_make_event(event_id="cev_a2", motifs=["loss"]))
        self.assertTrue(r_a2.drafted)

        # Pattern B still needs one more
        r_b2 = bridge.maybe_draft_proposal(
            _make_event(event_id="cev_b2", motifs=["joy"], domain_id="research")
        )
        # This should also draft since "joy" pattern now has 2 events
        self.assertTrue(r_b2.drafted)

    def test_draft_result_shape(self):
        """Verify ProposalDraftResult has all expected fields."""
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=1)
        result = bridge.maybe_draft_proposal(_make_event(confidence=0.80))
        d = result.to_dict()
        self.assertIn("drafted", d)
        self.assertIn("reason", d)
        self.assertIn("proposal_id", d)
        self.assertIn("event_id", d)
        self.assertIn("domain_id", d)
        self.assertIn("pattern_count", d)


# ---------------------------------------------------------------------------
# Bridge configuration tests
# ---------------------------------------------------------------------------

class TestBridgeConfiguration(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_custom_thresholds(self):
        bridge = CollectiveProposalBridge(
            self.tmp, "ws1",
            confidence_threshold=0.90,
            persistence_min=5,
            persistence_window=1200,
            domain_cooldown=600,
            max_pending_per_domain=3,
        )
        self.assertEqual(bridge.confidence_threshold, 0.90)
        self.assertEqual(bridge.persistence_min, 5)
        self.assertEqual(bridge.persistence_window, 1200)
        self.assertEqual(bridge.domain_cooldown, 600)
        self.assertEqual(bridge.max_pending_per_domain, 3)

    def test_low_persistence_min_allows_immediate_draft(self):
        """With persistence_min=1, first high-confidence event drafts a proposal."""
        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=1)
        result = bridge.maybe_draft_proposal(_make_event(confidence=0.80))
        self.assertTrue(result.drafted)


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestInvariants(unittest.TestCase):
    """Key design invariants for the proposal bridge."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_proposals_are_always_pending(self):
        """Collective proposals are never auto-approved.
        They must go through the normal operator review queue."""
        import numpy as np
        mock_reg = MagicMock()
        mock_proposal = MagicMock()
        mock_proposal.proposal_id = "prop_1"
        mock_reg.submit.return_value = mock_proposal
        mock_reg.list_pending.return_value = []

        bridge = CollectiveProposalBridge(self.tmp, "ws1", persistence_min=1)
        event = _make_event(confidence=0.80)
        emb = np.random.randn(128).astype("float32")

        bridge.maybe_draft_proposal(event, proposal_registry=mock_reg, embedding=emb)

        # Verify submit was called — the proposal was submitted, not approved
        mock_reg.submit.assert_called_once()
        # Verify mark() was NOT called (no auto-approval)
        mock_reg.mark.assert_not_called()

    def test_always_records_event_even_if_rejected(self):
        """Event should be recorded for persistence tracking even if
        confidence is too low for a proposal."""
        bridge = CollectiveProposalBridge(self.tmp, "ws1")
        event = _make_event(confidence=0.10)  # way too low
        bridge.maybe_draft_proposal(event)

        # Event should still be tracked
        count = bridge.tracker.count_recent(
            "research", ["motif_loss", "motif_grief"], 3600,
        )
        self.assertEqual(count, 1)

    def test_proposal_summary_traceable(self):
        """Proposal summary must contain collective_source tag
        for traceability back to the convergence event."""
        summary = CollectiveProposalBridge._build_proposal_summary(
            _make_event(event_id="cev_trace_001")
        )
        self.assertIn("[collective_source:cev_trace_001]", summary)


if __name__ == "__main__":
    unittest.main()
