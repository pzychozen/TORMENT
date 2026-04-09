"""
tests/test_collective_policy.py — Collective policy engine tests

Tests for all 7 gates in order, edge cases, drift budget logic,
dedup + rate limiting persistence, and agent opt-out.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.collective_policy import (
    CollectivePolicy,
    PolicyResult,
    ReingestTracker,
    check_drift_budget,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_RATE_LIMIT_MAX,
    DEFAULT_DRIFT_BUDGET,
    DEFAULT_ECHO_STRENGTH,
    DEFAULT_ECHO_STRENGTH_CAP,
)


def _make_event(**kwargs) -> dict:
    """Build a minimal convergence event dict that passes all gates by default."""
    defaults = {
        "event_id": "cev_test001",
        "workspace_id": "ws1",
        "domain_id": "personal",
        "participating_agents": ["ryuki", "aria"],
        "confidence": 0.80,
        "semantic_overlap": 0.85,
        "phase_alignment": 0.6,
        "symbol_alignment": 0.5,
        "dominant_motifs": ["motif_music"],
        "dominant_symbol": "✧",
        "summary": "Both discussed music deeply",
    }
    defaults.update(kwargs)
    return defaults


class TestPolicyResultShape(unittest.TestCase):

    def test_eligible_result(self):
        r = PolicyResult(eligible=True, reason="ok")
        d = r.to_dict()
        self.assertTrue(d["eligible"])
        self.assertIsNone(d["gate_failed"])

    def test_rejected_result(self):
        r = PolicyResult(eligible=False, gate_failed="confidence", reason="too low")
        d = r.to_dict()
        self.assertFalse(d["eligible"])
        self.assertEqual(d["gate_failed"], "confidence")


# ---------------------------------------------------------------------------
# Gate 1: Confidence threshold
# ---------------------------------------------------------------------------

class TestGate1Confidence(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policy = CollectivePolicy(self.tmp, "ws1")

    def test_high_confidence_passes(self):
        event = _make_event(confidence=0.80)
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertTrue(result.eligible)

    def test_exact_threshold_passes(self):
        event = _make_event(confidence=DEFAULT_CONFIDENCE_THRESHOLD)
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertTrue(result.eligible)

    def test_below_threshold_fails(self):
        event = _make_event(confidence=0.50)
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "confidence")

    def test_zero_confidence_fails(self):
        event = _make_event(confidence=0.0)
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "confidence")

    def test_custom_threshold(self):
        policy = CollectivePolicy(self.tmp, "ws1", confidence_threshold=0.90)
        event = _make_event(confidence=0.85)
        result = policy.evaluate(event, "ryuki", "personal")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "confidence")


# ---------------------------------------------------------------------------
# Gate 2: Agent opt-in
# ---------------------------------------------------------------------------

class TestGate2AgentOptIn(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policy = CollectivePolicy(self.tmp, "ws1")

    def test_default_opted_in(self):
        self.assertTrue(self.policy.is_agent_opted_in("ryuki"))

    def test_opt_out_blocks(self):
        self.policy.set_agent_opt_out("ryuki", True)
        event = _make_event(confidence=0.90)
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "agent_opt_in")

    def test_opt_back_in(self):
        self.policy.set_agent_opt_out("ryuki", True)
        self.policy.set_agent_opt_out("ryuki", False)
        event = _make_event(confidence=0.90)
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertTrue(result.eligible)

    def test_one_agent_out_other_in(self):
        self.policy.set_agent_opt_out("ryuki", True)
        event = _make_event(confidence=0.90)
        # ryuki blocked
        r1 = self.policy.evaluate(event, "ryuki", "personal")
        self.assertFalse(r1.eligible)
        # aria still allowed
        r2 = self.policy.evaluate(event, "aria", "personal")
        self.assertTrue(r2.eligible)


# ---------------------------------------------------------------------------
# Gate 3: Domain exact match
# ---------------------------------------------------------------------------

class TestGate3DomainMatch(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policy = CollectivePolicy(self.tmp, "ws1")

    def test_matching_domain_passes(self):
        event = _make_event(domain_id="personal")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertTrue(result.eligible)

    def test_mismatched_domain_fails(self):
        event = _make_event(domain_id="personal")
        result = self.policy.evaluate(event, "ryuki", "work")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "domain_match")

    def test_no_cross_domain(self):
        """Even similar domains are rejected — exact match only."""
        event = _make_event(domain_id="personal_v2")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "domain_match")


# ---------------------------------------------------------------------------
# Gate 4: Deduplication
# ---------------------------------------------------------------------------

class TestGate4Dedup(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policy = CollectivePolicy(self.tmp, "ws1")

    def test_first_time_passes(self):
        event = _make_event(event_id="cev_001")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertTrue(result.eligible)

    def test_duplicate_blocked(self):
        event = _make_event(event_id="cev_001")
        self.policy.record_reingest("ryuki", "cev_001")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "dedup")

    def test_same_event_different_agent_ok(self):
        """Same event can be reingested into a different agent."""
        self.policy.record_reingest("ryuki", "cev_001")
        event = _make_event(event_id="cev_001")
        result = self.policy.evaluate(event, "aria", "personal")
        self.assertTrue(result.eligible)

    def test_different_event_same_agent_ok(self):
        self.policy.record_reingest("ryuki", "cev_001")
        event = _make_event(event_id="cev_002")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertTrue(result.eligible)


# ---------------------------------------------------------------------------
# Gate 5: Rate limiting
# ---------------------------------------------------------------------------

class TestGate5RateLimit(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policy = CollectivePolicy(
            self.tmp, "ws1",
            rate_limit_max=2,
            rate_limit_window=3600,
        )

    def test_under_limit_passes(self):
        self.policy.record_reingest("ryuki", "cev_001")
        event = _make_event(event_id="cev_002")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertTrue(result.eligible)

    def test_at_limit_blocked(self):
        self.policy.record_reingest("ryuki", "cev_001")
        self.policy.record_reingest("ryuki", "cev_002")
        event = _make_event(event_id="cev_003")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "rate_limit")

    def test_different_agent_not_affected(self):
        """Rate limit is per-agent."""
        self.policy.record_reingest("ryuki", "cev_001")
        self.policy.record_reingest("ryuki", "cev_002")
        event = _make_event(event_id="cev_003")
        result = self.policy.evaluate(event, "aria", "personal")
        self.assertTrue(result.eligible)


# ---------------------------------------------------------------------------
# Gate 6: Drift budget / identity compatibility
# ---------------------------------------------------------------------------

class TestGate6DriftBudget(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policy = CollectivePolicy(self.tmp, "ws1")

    def test_stable_agent_passes(self):
        event = _make_event()
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=0.2,
            drift_direction="stable",
        )
        self.assertTrue(result.eligible)

    def test_toward_seed_passes(self):
        event = _make_event()
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=0.5,
            drift_direction="toward_seed",
        )
        self.assertTrue(result.eligible)

    def test_drifting_away_beyond_budget_fails(self):
        event = _make_event()
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=-0.35,
            drift_direction="away_seed",
        )
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "drift_budget")

    def test_very_negative_drift_fails_regardless_of_direction(self):
        """Even if direction is stable, extremely far drift should block."""
        event = _make_event()
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=-0.50,
            drift_direction="stable",
        )
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "drift_budget")

    def test_alien_motif_with_negative_drift_fails(self):
        """Event motifs don't match seed motif and agent is drifting."""
        event = _make_event(dominant_motifs=["motif_cooking"])
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=-0.1,
            drift_direction="stable",
            agent_seed_motif_id="motif_music",
        )
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "drift_budget")

    def test_alien_motif_with_positive_drift_passes(self):
        """If agent is stable near seed, diverse influences are ok."""
        event = _make_event(dominant_motifs=["motif_cooking"])
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=0.3,
            drift_direction="stable",
            agent_seed_motif_id="motif_music",
        )
        self.assertTrue(result.eligible)

    def test_matching_motif_passes(self):
        event = _make_event(dominant_motifs=["motif_music", "motif_art"])
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=-0.1,
            drift_direction="stable",
            agent_seed_motif_id="motif_music",
        )
        self.assertTrue(result.eligible)

    def test_no_seed_motif_passes(self):
        """Agents without a seed motif skip the motif compatibility check."""
        event = _make_event(dominant_motifs=["motif_anything"])
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=0.0,
            drift_direction="stable",
            agent_seed_motif_id=None,
        )
        self.assertTrue(result.eligible)

    def test_custom_drift_budget(self):
        policy = CollectivePolicy(self.tmp, "ws1", drift_budget=0.10)
        event = _make_event()
        result = policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=-0.15,
            drift_direction="away_seed",
        )
        self.assertFalse(result.eligible)


# ---------------------------------------------------------------------------
# check_drift_budget standalone tests
# ---------------------------------------------------------------------------

class TestCheckDriftBudgetStandalone(unittest.TestCase):

    def test_domain_mismatch(self):
        ok, reason = check_drift_budget(
            current_drift_score=0.0, drift_direction="stable",
            event_domain_id="work", agent_domain_id="personal",
            event_motifs=[], agent_seed_motif_id=None,
        )
        self.assertFalse(ok)
        self.assertIn("Domain mismatch", reason)

    def test_healthy_agent(self):
        ok, reason = check_drift_budget(
            current_drift_score=0.2, drift_direction="toward_seed",
            event_domain_id="personal", agent_domain_id="personal",
            event_motifs=["m1"], agent_seed_motif_id="m1",
        )
        self.assertTrue(ok)

    def test_empty_motifs_no_seed_passes(self):
        ok, _ = check_drift_budget(
            current_drift_score=0.0, drift_direction="stable",
            event_domain_id="personal", agent_domain_id="personal",
            event_motifs=[], agent_seed_motif_id=None,
        )
        self.assertTrue(ok)


# ---------------------------------------------------------------------------
# ReingestTracker persistence tests
# ---------------------------------------------------------------------------

class TestReingestTracker(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_record_and_check_duplicate(self):
        tracker = ReingestTracker(self.tmp, "ws1")
        self.assertFalse(tracker.is_duplicate("ryuki", "cev_001"))
        tracker.record("ryuki", "cev_001")
        self.assertTrue(tracker.is_duplicate("ryuki", "cev_001"))

    def test_count_recent(self):
        tracker = ReingestTracker(self.tmp, "ws1")
        tracker.record("ryuki", "cev_001")
        tracker.record("ryuki", "cev_002")
        self.assertEqual(tracker.count_recent("ryuki", 3600), 2)
        self.assertEqual(tracker.count_recent("aria", 3600), 0)

    def test_persistence(self):
        tracker1 = ReingestTracker(self.tmp, "ws1")
        tracker1.record("ryuki", "cev_001")

        # New instance reads from disk
        tracker2 = ReingestTracker(self.tmp, "ws1")
        self.assertTrue(tracker2.is_duplicate("ryuki", "cev_001"))
        self.assertEqual(tracker2.count_recent("ryuki", 3600), 1)

    def test_workspace_isolation(self):
        t1 = ReingestTracker(self.tmp, "ws1")
        t2 = ReingestTracker(self.tmp, "ws2")
        t1.record("ryuki", "cev_001")
        self.assertTrue(t1.is_duplicate("ryuki", "cev_001"))
        self.assertFalse(t2.is_duplicate("ryuki", "cev_001"))


# ---------------------------------------------------------------------------
# Full pipeline: all gates in sequence
# ---------------------------------------------------------------------------

class TestFullPipeline(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policy = CollectivePolicy(self.tmp, "ws1")

    def test_perfect_event_passes_all_gates(self):
        event = _make_event(confidence=0.90)
        result = self.policy.evaluate(
            event, "ryuki", "personal",
            current_drift_score=0.2,
            drift_direction="toward_seed",
            agent_seed_motif_id="motif_music",
        )
        self.assertTrue(result.eligible)
        self.assertIsNone(result.gate_failed)
        self.assertEqual(result.echo_strength, DEFAULT_ECHO_STRENGTH)

    def test_gates_checked_in_order(self):
        """If confidence fails, we never get to domain check."""
        event = _make_event(confidence=0.10, domain_id="wrong_domain")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertEqual(result.gate_failed, "confidence")

    def test_second_gate_when_first_passes(self):
        """Confidence passes but agent is opted out."""
        self.policy.set_agent_opt_out("ryuki", True)
        event = _make_event(confidence=0.90, domain_id="wrong_domain")
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertEqual(result.gate_failed, "agent_opt_in")

    def test_echo_strength_default(self):
        event = _make_event()
        result = self.policy.evaluate(event, "ryuki", "personal")
        self.assertEqual(result.echo_strength, DEFAULT_ECHO_STRENGTH)

    def test_echo_strength_capped(self):
        """Strength cannot exceed cap even if configured higher."""
        policy = CollectivePolicy(
            self.tmp, "ws1",
            echo_strength=0.60,
            echo_strength_cap=0.40,
        )
        event = _make_event()
        result = policy.evaluate(event, "ryuki", "personal")
        self.assertEqual(result.echo_strength, DEFAULT_ECHO_STRENGTH_CAP)


# ---------------------------------------------------------------------------
# Invariant: policy defaults are conservative
# ---------------------------------------------------------------------------

class TestPolicyDefaults(unittest.TestCase):
    """Verify the defaults reflect the conservative design intent."""

    def test_confidence_threshold_above_detection(self):
        """Re-ingestion threshold must be higher than detection threshold (0.45)."""
        self.assertGreater(DEFAULT_CONFIDENCE_THRESHOLD, 0.45)

    def test_echo_strength_is_whisper(self):
        """Default echo strength should be a whisper, not a memory."""
        self.assertLessEqual(DEFAULT_ECHO_STRENGTH, 0.30)

    def test_echo_strength_cap_is_conservative(self):
        self.assertLessEqual(DEFAULT_ECHO_STRENGTH_CAP, 0.50)

    def test_rate_limit_is_restrictive(self):
        self.assertLessEqual(DEFAULT_RATE_LIMIT_MAX, 5)

    def test_drift_budget_is_meaningful(self):
        """Budget should be meaningful but not trivially permissive."""
        self.assertGreater(DEFAULT_DRIFT_BUDGET, 0.1)
        self.assertLess(DEFAULT_DRIFT_BUDGET, 0.8)


if __name__ == "__main__":
    unittest.main()
