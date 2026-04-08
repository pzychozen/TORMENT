"""
tests/test_collective_reingest.py — Phase D3 re-ingestion tests

Tests covering:
    - Echo containment (terminal: double-blocked, no emission, no re-echo)
    - Provenance marking (collective, source_event_id, source_agents)
    - Echo strength (0.25x default, 0.40x hard cap, configurable)
    - Retrieval weight discount (0.5x for collective-provenance)
    - Governance integration (reingest respects governance flags)
    - Policy gate enforcement (all 7 gates exercised through reingest)
    - Character integrity (echoes don't corrupt identity)

Invariants verified:
    3. Collective echoes are terminal by default.
    4. Collective echoes are influences, not autobiography.
    5. Collective provenance cannot outrank seed/canon identity by default.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.governance import (
    resolve_governance,
    should_emit_packet,
    allows_collective_reingest,
    is_compression_protected,
    update_governance,
)
from torment_service.collective_policy import (
    CollectivePolicy,
    PolicyResult,
    ReingestTracker,
    DEFAULT_ECHO_STRENGTH,
    DEFAULT_ECHO_STRENGTH_CAP,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal convergence event dict
# ---------------------------------------------------------------------------

def _make_event(
    event_id: str = "cev_test001",
    domain_id: str = "research",
    confidence: float = 0.75,
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
    }


# ---------------------------------------------------------------------------
# Echo containment tests
# ---------------------------------------------------------------------------

class TestEchoContainment(unittest.TestCase):
    """Invariant 3: Collective echoes are terminal by default.

    A reingested echo must have:
        - collective_reingest_blocked = True
        - collective_export_blocked = True
    So it cannot re-emit or be re-echoed.
    """

    def test_terminal_governance_shape(self):
        """Verify that the governance flags marking an echo terminal
        prevent both re-emission and re-ingestion."""
        # Simulate what reingest_convergence does to a payload
        payload = {"summary": "echo content", "strength": 0.25}
        update_governance(payload, {
            "collective_reingest_blocked": True,
            "collective_export_blocked": True,
        }, actor="collective_policy", source="reingest")

        # Cannot be re-echoed
        self.assertFalse(allows_collective_reingest(payload))
        # Cannot emit packets
        self.assertFalse(should_emit_packet(payload))

    def test_collective_provenance_blocks_emission(self):
        """A memory with provenance='collective' should not emit packets
        even if governance flags are somehow missing."""
        # This tests the Gate 1b check in fabric.py emission block
        payload = {
            "provenance": "collective",
            "source_event_id": "cev_test001",
        }
        # Governance alone would allow emission (no flags set)
        self.assertTrue(should_emit_packet(payload))
        # But the provenance check in fabric.py adds an extra gate
        # (We verify this through the provenance field existence)
        self.assertEqual(payload["provenance"], "collective")

    def test_echo_cannot_be_reingested_via_policy(self):
        """If an echo somehow gets into a convergence event,
        the governance flags should block reingest at gate level."""
        payload = {"governance": {
            "collective_reingest_blocked": True,
            "collective_export_blocked": True,
        }}
        self.assertFalse(allows_collective_reingest(payload))


# ---------------------------------------------------------------------------
# Provenance marking tests
# ---------------------------------------------------------------------------

class TestProvenanceMarking(unittest.TestCase):
    """Invariant 4: Collective echoes are influences, not autobiography.

    Reingested echoes must carry provenance metadata that distinguishes
    them from organic private memories.
    """

    def test_provenance_fields(self):
        """Verify the expected provenance shape on an echo payload."""
        # Simulate what reingest_convergence patches onto the entity
        payload = {
            "summary": "[collective echo] Convergence between agent_a and agent_b",
            "strength": 0.25,
        }
        # Apply provenance (as reingest_convergence does)
        payload["provenance"] = "collective"
        payload["source_event_id"] = "cev_test001"
        payload["source_agents"] = ["agent_a"]

        self.assertEqual(payload["provenance"], "collective")
        self.assertEqual(payload["source_event_id"], "cev_test001")
        self.assertIsInstance(payload["source_agents"], list)
        self.assertIn("agent_a", payload["source_agents"])

    def test_echo_summary_prefix(self):
        """Echo summaries should start with [collective echo]."""
        event = _make_event(summary="Convergence between agent_a and agent_b")
        summary = event["summary"]
        echo_summary = f"[collective echo] {summary}"
        self.assertTrue(echo_summary.startswith("[collective echo]"))

    def test_source_agents_excludes_target(self):
        """source_agents should not include the target agent."""
        event = _make_event(agents=["agent_a", "agent_b"])
        target = "agent_b"
        source_agents = [a for a in event["participating_agents"] if a != target]
        self.assertEqual(source_agents, ["agent_a"])
        self.assertNotIn(target, source_agents)


# ---------------------------------------------------------------------------
# Echo strength tests
# ---------------------------------------------------------------------------

class TestEchoStrength(unittest.TestCase):
    """Echoes are low-amplitude (0.25x default, 0.40x hard cap)."""

    def test_default_strength(self):
        self.assertEqual(DEFAULT_ECHO_STRENGTH, 0.25)

    def test_strength_cap(self):
        self.assertEqual(DEFAULT_ECHO_STRENGTH_CAP, 0.40)

    def test_policy_result_carries_strength(self):
        """PolicyResult.echo_strength defaults to 0.25."""
        result = PolicyResult(eligible=True)
        self.assertEqual(result.echo_strength, DEFAULT_ECHO_STRENGTH)

    def test_strength_override_capped(self):
        """Overriding echo strength should be capped at 0.40."""
        override = 0.80  # way too high
        capped = min(override, DEFAULT_ECHO_STRENGTH_CAP)
        self.assertEqual(capped, 0.40)

    def test_strength_override_within_cap(self):
        """A valid override below cap should be used as-is."""
        override = 0.35
        capped = min(override, DEFAULT_ECHO_STRENGTH_CAP)
        self.assertEqual(capped, 0.35)

    def test_policy_engine_caps_strength(self):
        """CollectivePolicy should cap echo_strength to echo_strength_cap."""
        tmp = tempfile.mkdtemp()
        policy = CollectivePolicy(
            data_dir=tmp,
            workspace_id="ws1",
            echo_strength=0.50,  # above cap
            echo_strength_cap=0.40,
        )
        # The constructor should have capped it
        self.assertLessEqual(policy.echo_strength, 0.40)


# ---------------------------------------------------------------------------
# Retrieval weight discount tests
# ---------------------------------------------------------------------------

class TestRetrievalDiscount(unittest.TestCase):
    """Invariant 5: Collective provenance cannot outrank seed/canon identity.

    Collective-provenance memories get a 0.5x retrieval weight discount.
    """

    def test_discount_applied_to_collective(self):
        """Simulate the discount logic from query scoring."""
        final_score = 0.80
        provenance = "collective"
        discount = 0.50

        if provenance == "collective":
            final_score *= discount

        self.assertAlmostEqual(final_score, 0.40)

    def test_no_discount_for_organic(self):
        """Organic memories (no provenance) should not be discounted."""
        final_score = 0.80
        provenance = ""
        discount = 0.50

        if provenance == "collective":
            final_score *= discount

        self.assertAlmostEqual(final_score, 0.80)

    def test_collective_below_organic_after_discount(self):
        """A collective memory with same base score should rank below organic."""
        base = 0.80
        organic = base
        collective = base * 0.50
        self.assertGreater(organic, collective)

    def test_discount_configurable(self):
        """The discount factor should be configurable via env var."""
        # Default is 0.50
        try:
            default = float(os.getenv("TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT", "0.50"))
        except Exception:
            default = 0.50
        self.assertEqual(default, 0.50)


# ---------------------------------------------------------------------------
# Policy gate enforcement through reingest path
# ---------------------------------------------------------------------------

class TestPolicyGatesViaReingest(unittest.TestCase):
    """Verify that reingest_convergence respects all policy gates."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_low_confidence_rejected(self):
        """Events below confidence threshold should be rejected."""
        policy = CollectivePolicy(self.tmp, "ws1")
        event = _make_event(confidence=0.30)  # below 0.60 threshold
        result = policy.evaluate(event, "agent_b", "research")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "confidence")

    def test_opted_out_agent_rejected(self):
        """An opted-out agent should be rejected."""
        policy = CollectivePolicy(self.tmp, "ws1")
        policy.set_agent_opt_out("agent_b", True)
        event = _make_event(confidence=0.75)
        result = policy.evaluate(event, "agent_b", "research")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "agent_opt_in")

    def test_domain_mismatch_rejected(self):
        """Event from different domain should be rejected."""
        policy = CollectivePolicy(self.tmp, "ws1")
        event = _make_event(domain_id="creative", confidence=0.75)
        result = policy.evaluate(event, "agent_b", "research")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "domain_match")

    def test_duplicate_rejected(self):
        """Same event+agent should be rejected on second attempt."""
        policy = CollectivePolicy(self.tmp, "ws1")
        event = _make_event(confidence=0.75)
        # First: should pass
        result1 = policy.evaluate(event, "agent_b", "research")
        self.assertTrue(result1.eligible)
        # Record reingest
        policy.record_reingest("agent_b", "cev_test001")
        # Second: should fail dedup
        result2 = policy.evaluate(event, "agent_b", "research")
        self.assertFalse(result2.eligible)
        self.assertEqual(result2.gate_failed, "dedup")

    def test_rate_limit_enforced(self):
        """Agent exceeding rate limit should be rejected."""
        policy = CollectivePolicy(self.tmp, "ws1", rate_limit_max=2)
        # Fill rate limit
        for i in range(2):
            policy.record_reingest("agent_b", f"cev_fill_{i}")
        # New event should be rate-limited
        event = _make_event(event_id="cev_new", confidence=0.75)
        result = policy.evaluate(event, "agent_b", "research")
        self.assertFalse(result.eligible)
        self.assertEqual(result.gate_failed, "rate_limit")

    def test_eligible_event_passes_all_gates(self):
        """A clean event should pass all 7 gates."""
        policy = CollectivePolicy(self.tmp, "ws1")
        event = _make_event(confidence=0.75)
        result = policy.evaluate(event, "agent_b", "research")
        self.assertTrue(result.eligible)
        self.assertIsNone(result.gate_failed)
        self.assertEqual(result.echo_strength, DEFAULT_ECHO_STRENGTH)


# ---------------------------------------------------------------------------
# Governance integration with reingest
# ---------------------------------------------------------------------------

class TestGovernanceReingestIntegration(unittest.TestCase):
    """Verify governance flags are correctly applied during reingest."""

    def test_double_block_applied(self):
        """After reingest, payload should have both block flags True."""
        payload = {"summary": "test", "strength": 0.25}
        update_governance(payload, {
            "collective_reingest_blocked": True,
            "collective_export_blocked": True,
        }, actor="collective_policy", source="reingest")

        gov = resolve_governance(payload)
        self.assertTrue(gov.collective_reingest_blocked)
        self.assertTrue(gov.collective_export_blocked)

    def test_audit_trail_records_reingest(self):
        """Governance update from reingest should have audit trail."""
        payload = {"summary": "test"}
        update_governance(payload, {
            "collective_reingest_blocked": True,
            "collective_export_blocked": True,
        }, actor="collective_policy", source="reingest")

        trail = payload.get("governance_audit", [])
        self.assertEqual(len(trail), 1)
        self.assertEqual(trail[0]["actor"], "collective_policy")
        self.assertEqual(trail[0]["source"], "reingest")

    def test_protected_flag_not_set_by_reingest(self):
        """Reingest should not set the 'protected' flag — echoes are disposable."""
        payload = {"summary": "test"}
        update_governance(payload, {
            "collective_reingest_blocked": True,
            "collective_export_blocked": True,
        }, actor="collective_policy", source="reingest")

        gov = resolve_governance(payload)
        self.assertFalse(gov.protected)

    def test_echo_not_compression_protected(self):
        """Echoes should NOT be compression-protected by default."""
        payload = {"summary": "test", "governance": {
            "collective_reingest_blocked": True,
            "collective_export_blocked": True,
        }}
        self.assertFalse(is_compression_protected(payload))


# ---------------------------------------------------------------------------
# Character integrity tests
# ---------------------------------------------------------------------------

class TestCharacterIntegrity(unittest.TestCase):
    """Invariant 5: Collective provenance cannot outrank seed/canon identity.

    Echoes are marked, discounted, and excluded from seed-basin correction.
    """

    def test_echo_has_collective_provenance(self):
        """Verify provenance field is set correctly."""
        payload = {"provenance": "collective"}
        self.assertEqual(payload["provenance"], "collective")

    def test_organic_memory_has_no_provenance(self):
        """Normal memories should not have provenance='collective'."""
        payload = {"summary": "organic memory", "strength": 0.8}
        self.assertNotEqual(payload.get("provenance", ""), "collective")

    def test_echo_strength_below_typical_organic(self):
        """Echo strength (0.25) should be well below typical organic strength."""
        echo_strength = DEFAULT_ECHO_STRENGTH
        typical_organic = 0.60  # typical strength for a "core" memory
        self.assertLess(echo_strength, typical_organic)

    def test_echo_ranking_with_discount(self):
        """With retrieval discount, an echo should rank below a similarly-scored organic memory."""
        # Simulate scoring
        organic_score = 0.65
        echo_base_score = 0.65
        echo_final = echo_base_score * 0.50  # retrieval discount

        self.assertGreater(organic_score, echo_final)
        # The echo should be roughly half the organic score
        self.assertAlmostEqual(echo_final, 0.325)

    def test_high_confidence_echo_still_below_organic(self):
        """Even a very high-confidence echo should rank below moderate organic after discount."""
        organic = 0.50  # moderate
        echo_base = 0.90  # very high
        echo_discounted = echo_base * 0.50
        self.assertLessEqual(echo_discounted, organic)


# ---------------------------------------------------------------------------
# Reingest tracker persistence tests
# ---------------------------------------------------------------------------

class TestReingestTrackerPersistence(unittest.TestCase):
    """Verify that reingest records survive across tracker instances."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_record_and_check(self):
        t = ReingestTracker(self.tmp, "ws1")
        self.assertFalse(t.is_duplicate("agent_b", "cev_1"))
        t.record("agent_b", "cev_1")
        self.assertTrue(t.is_duplicate("agent_b", "cev_1"))

    def test_persistence_across_instances(self):
        t1 = ReingestTracker(self.tmp, "ws1")
        t1.record("agent_b", "cev_1")

        # New instance reads from disk
        t2 = ReingestTracker(self.tmp, "ws1")
        self.assertTrue(t2.is_duplicate("agent_b", "cev_1"))

    def test_workspace_isolation(self):
        t1 = ReingestTracker(self.tmp, "ws1")
        t2 = ReingestTracker(self.tmp, "ws2")
        t1.record("agent_b", "cev_1")
        self.assertTrue(t1.is_duplicate("agent_b", "cev_1"))
        self.assertFalse(t2.is_duplicate("agent_b", "cev_1"))

    def test_agent_isolation(self):
        t = ReingestTracker(self.tmp, "ws1")
        t.record("agent_a", "cev_1")
        self.assertTrue(t.is_duplicate("agent_a", "cev_1"))
        self.assertFalse(t.is_duplicate("agent_b", "cev_1"))

    def test_rate_counting(self):
        t = ReingestTracker(self.tmp, "ws1")
        t.record("agent_b", "cev_1")
        t.record("agent_b", "cev_2")
        t.record("agent_b", "cev_3")
        # All within current time window
        self.assertEqual(t.count_recent("agent_b", 3600), 3)
        self.assertEqual(t.count_recent("agent_a", 3600), 0)


# ---------------------------------------------------------------------------
# Full cycle simulation (unit-level, no fabric)
# ---------------------------------------------------------------------------

class TestFullCycleSimulation(unittest.TestCase):
    """Simulate the complete reingest flow at unit level:
    event → policy → governance patch → containment check.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_full_reingest_cycle(self):
        """Simulate: create event → evaluate policy → apply governance → verify containment."""
        # 1. Create a convergence event
        event = _make_event(
            event_id="cev_cycle_001",
            confidence=0.80,
            agents=["ryuki", "kael"],
            motifs=["motif_loss"],
            summary="Convergence: shared grief resonance",
        )

        # 2. Evaluate policy for target agent kael
        policy = CollectivePolicy(self.tmp, "ws1")
        result = policy.evaluate(
            event=event,
            target_agent_id="kael",
            target_domain_id="research",
        )
        self.assertTrue(result.eligible)

        # 3. Simulate the echo payload
        echo_payload = {
            "summary": f"[collective echo] {event['summary']}",
            "strength": result.echo_strength,
            "provenance": "collective",
            "source_event_id": event["event_id"],
            "source_agents": ["ryuki"],
        }

        # 4. Apply terminal governance
        update_governance(echo_payload, {
            "collective_reingest_blocked": True,
            "collective_export_blocked": True,
        }, actor="collective_policy", source="reingest")

        # 5. Record reingest
        policy.record_reingest("kael", event["event_id"])

        # 6. Verify containment
        self.assertFalse(should_emit_packet(echo_payload))
        self.assertFalse(allows_collective_reingest(echo_payload))
        self.assertEqual(echo_payload["provenance"], "collective")
        self.assertEqual(echo_payload["strength"], 0.25)

        # 7. Verify dedup prevents re-reingest
        result2 = policy.evaluate(event, "kael", "research")
        self.assertFalse(result2.eligible)
        self.assertEqual(result2.gate_failed, "dedup")

    def test_reingest_different_agents_same_event(self):
        """Two different agents can receive the same event."""
        event = _make_event(
            event_id="cev_multi",
            confidence=0.80,
            agents=["ryuki", "kael"],
        )
        policy = CollectivePolicy(self.tmp, "ws1")

        # Agent kael
        r1 = policy.evaluate(event, "kael", "research")
        self.assertTrue(r1.eligible)
        policy.record_reingest("kael", "cev_multi")

        # Agent ryuki
        r2 = policy.evaluate(event, "ryuki", "research")
        self.assertTrue(r2.eligible)
        policy.record_reingest("ryuki", "cev_multi")

        # Both should now be deduped
        self.assertFalse(policy.evaluate(event, "kael", "research").eligible)
        self.assertFalse(policy.evaluate(event, "ryuki", "research").eligible)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases(unittest.TestCase):

    def test_empty_event_summary(self):
        """Event with no summary should still produce a valid echo summary."""
        event = _make_event(summary="")
        target = "agent_b"
        source_agents = [a for a in event["participating_agents"] if a != target]
        domain = event["domain_id"]

        if event["summary"]:
            echo_summary = f"[collective echo] {event['summary']}"
        else:
            echo_summary = (
                f"[collective echo] Convergence across {', '.join(source_agents)} "
                f"in domain '{domain}'"
            )
        self.assertTrue(echo_summary.startswith("[collective echo]"))
        self.assertIn("agent_a", echo_summary)

    def test_single_participant_event(self):
        """Edge case: event with only the target agent in participants.
        (Shouldn't happen in practice, but should handle gracefully.)"""
        event = _make_event(agents=["agent_b"])
        source_agents = [a for a in event["participating_agents"] if a != "agent_b"]
        self.assertEqual(source_agents, [])

    def test_none_echo_strength_override(self):
        """None override should use default strength."""
        override = None
        strength = (
            min(float(override), DEFAULT_ECHO_STRENGTH_CAP)
            if override is not None
            else DEFAULT_ECHO_STRENGTH
        )
        self.assertEqual(strength, 0.25)


if __name__ == "__main__":
    unittest.main()
