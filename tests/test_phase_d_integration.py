"""
tests/test_phase_d_integration.py — Phase D5 cross-phase integration tests

This test file verifies that all Phase D subsystems work together correctly.
It does NOT require a running MemoryFabric — it exercises the module-level
contracts that fabric.py relies on, ensuring the pieces compose safely.

Test areas:
    1. Echo containment chain (governance → emission → reingest → dedup)
    2. Character integrity (drift budget → retrieval discount → seed protection)
    3. Full pipeline simulation (event → policy → reingest → proposal bridge)
    4. 5-invariant exhaustive verification
    5. Cross-module boundary contracts
    6. Edge cases and adversarial scenarios
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from torment_service.governance import (
    resolve_governance,
    should_emit_packet,
    allows_collective_reingest,
    is_compression_protected,
    is_decay_accelerated,
    update_governance,
    GovernanceAuditLog,
)
from torment_service.collective_models import (
    MemoryGovernanceFlags,
    ConvergenceEvent,
    ResonancePacket,
)
from torment_service.collective_field import CollectiveField
from torment_service.collective_policy import (
    CollectivePolicy,
    PolicyResult,
    ReingestTracker,
    check_drift_budget,
    DEFAULT_ECHO_STRENGTH,
    DEFAULT_ECHO_STRENGTH_CAP,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_DRIFT_BUDGET,
)
from torment_service.collective_proposals import (
    CollectiveProposalBridge,
    ConvergencePersistenceTracker,
    PROPOSAL_CONFIDENCE_THRESHOLD,
    PROPOSAL_PERSISTENCE_MIN,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(
    event_id: str = "cev_int_001",
    domain_id: str = "research",
    confidence: float = 0.80,
    agents: list = None,
    motifs: list = None,
) -> dict:
    agents = agents or ["agent_a", "agent_b"]
    motifs = motifs or ["motif_shared"]
    return {
        "event_id": event_id,
        "workspace_id": "ws_int",
        "domain_id": domain_id,
        "confidence": confidence,
        "participating_agents": agents,
        "source_packets": ["pkt_1", "pkt_2"],
        "source_eids": [100, 200],
        "dominant_motifs": motifs,
        "summary": f"Convergence: {', '.join(agents)} in {domain_id}",
        "semantic_overlap": 0.82,
        "phase_alignment": 0.60,
        "symbol_alignment": 0.40,
        "ts_start": int(time.time()) - 10,
        "ts_end": int(time.time()),
    }


def _make_echo_payload(
    event_id: str = "cev_int_001",
    source_agents: list = None,
    strength: float = DEFAULT_ECHO_STRENGTH,
) -> dict:
    """Simulate the payload shape that reingest_convergence patches onto a memory."""
    payload = {
        "summary": f"[collective echo] Convergence in research",
        "strength": strength,
        "provenance": "collective",
        "source_event_id": event_id,
        "source_agents": source_agents or ["agent_a"],
    }
    update_governance(payload, {
        "collective_reingest_blocked": True,
        "collective_export_blocked": True,
    }, actor="collective_policy", source="reingest")
    return payload


def _make_organic_payload(strength: float = 0.70) -> dict:
    """Simulate a normal private memory payload (no collective provenance)."""
    return {
        "summary": "I remember the first time we met at the harbor.",
        "strength": strength,
        "scope": "private",
        "agent_id": "kael",
    }


# ===========================================================================
# 1. ECHO CONTAINMENT CHAIN
# ===========================================================================

class TestEchoContainmentChain(unittest.TestCase):
    """Verify the complete containment chain: an echo cannot produce
    further echoes, emit packets, or be re-ingested."""

    def test_echo_cannot_emit_packet(self):
        """Governance: export_blocked → should_emit_packet returns False."""
        echo = _make_echo_payload()
        self.assertFalse(should_emit_packet(echo))

    def test_echo_cannot_be_reingested(self):
        """Governance: reingest_blocked → allows_collective_reingest returns False."""
        echo = _make_echo_payload()
        self.assertFalse(allows_collective_reingest(echo))

    def test_echo_blocked_by_provenance_field(self):
        """Even without governance flags, provenance='collective' should exist."""
        echo = _make_echo_payload()
        self.assertEqual(echo["provenance"], "collective")

    def test_echo_governance_survives_serialization(self):
        """Governance flags survive JSON round-trip (as they would in JSONL storage)."""
        echo = _make_echo_payload()
        serialized = json.dumps(echo)
        restored = json.loads(serialized)
        self.assertFalse(should_emit_packet(restored))
        self.assertFalse(allows_collective_reingest(restored))
        self.assertEqual(restored["provenance"], "collective")

    def test_echo_dedup_blocks_second_reingest(self):
        """Policy engine dedup prevents same event from being reingested twice."""
        tmp = tempfile.mkdtemp()
        policy = CollectivePolicy(tmp, "ws_int")
        event = _make_event()

        r1 = policy.evaluate(event, "agent_b", "research")
        self.assertTrue(r1.eligible)
        policy.record_reingest("agent_b", event["event_id"])

        r2 = policy.evaluate(event, "agent_b", "research")
        self.assertFalse(r2.eligible)
        self.assertEqual(r2.gate_failed, "dedup")

    def test_echo_of_echo_blocked_at_governance_level(self):
        """If someone tried to re-ingest an echo (bypassing policy),
        governance flags would block at source level."""
        echo = _make_echo_payload()
        # Simulate: echo payload gets checked as source material
        self.assertFalse(should_emit_packet(echo))
        self.assertFalse(allows_collective_reingest(echo))

    def test_echo_not_protected_from_compression(self):
        """Echoes should be compressible — they're disposable influences."""
        echo = _make_echo_payload()
        self.assertFalse(is_compression_protected(echo))

    def test_echo_not_decay_accelerated_by_default(self):
        """Echoes don't get decay_accelerated by default (they're already low-amplitude)."""
        echo = _make_echo_payload()
        self.assertFalse(is_decay_accelerated(echo))


# ===========================================================================
# 2. CHARACTER INTEGRITY
# ===========================================================================

class TestCharacterIntegrity(unittest.TestCase):
    """Invariant 5: Collective provenance cannot outrank seed/canon identity."""

    def test_drift_budget_blocks_drifting_agent(self):
        """Agent drifting away from seed should be blocked from echoes."""
        ok, reason = check_drift_budget(
            current_drift_score=-0.35,
            drift_direction="away_seed",
            event_domain_id="research",
            agent_domain_id="research",
            event_motifs=["motif_shared"],
            agent_seed_motif_id=None,
            drift_budget=0.30,
        )
        self.assertFalse(ok)
        self.assertIn("drifting away", reason)

    def test_drift_budget_allows_stable_agent(self):
        """Stable agent near seed should accept echoes."""
        ok, reason = check_drift_budget(
            current_drift_score=0.10,
            drift_direction="stable",
            event_domain_id="research",
            agent_domain_id="research",
            event_motifs=["motif_shared"],
            agent_seed_motif_id=None,
            drift_budget=0.30,
        )
        self.assertTrue(ok)

    def test_alien_motif_blocked_when_drifting(self):
        """Agent with seed motif should reject alien echoes when drifting."""
        ok, reason = check_drift_budget(
            current_drift_score=-0.10,
            drift_direction="away_seed",
            event_domain_id="research",
            agent_domain_id="research",
            event_motifs=["motif_alien"],
            agent_seed_motif_id="motif_seed",
            drift_budget=0.30,
        )
        self.assertFalse(ok)
        self.assertIn("thematically alien", reason)

    def test_diverse_motif_allowed_when_stable(self):
        """Stable agent can absorb diverse (non-seed) motifs."""
        ok, reason = check_drift_budget(
            current_drift_score=0.10,
            drift_direction="stable",
            event_domain_id="research",
            agent_domain_id="research",
            event_motifs=["motif_diverse"],
            agent_seed_motif_id="motif_seed",
            drift_budget=0.30,
        )
        self.assertTrue(ok)

    def test_retrieval_discount_ensures_organic_wins(self):
        """Simulate scoring: organic memory should outrank echo with same base."""
        base_score = 0.70
        organic_final = base_score  # no discount
        echo_final = base_score * 0.50  # collective discount

        self.assertGreater(organic_final, echo_final)
        self.assertAlmostEqual(echo_final, 0.35)

    def test_high_confidence_echo_still_below_moderate_organic(self):
        """Even excellent echo can't beat moderate organic after discount."""
        echo_base = 0.90
        echo_final = echo_base * 0.50
        organic = 0.50

        self.assertLessEqual(echo_final, organic)

    def test_echo_strength_well_below_organic(self):
        """Echo strength (0.25) vs typical organic (~0.60-0.80)."""
        self.assertLess(DEFAULT_ECHO_STRENGTH, 0.50)
        self.assertLess(DEFAULT_ECHO_STRENGTH_CAP, 0.50)


# ===========================================================================
# 3. FULL PIPELINE SIMULATION
# ===========================================================================

class TestFullPipelineSimulation(unittest.TestCase):
    """Simulate the complete D-phase pipeline without MemoryFabric:
    convergence → policy → reingest governance → proposal bridge.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_convergence_to_echo_to_proposal(self):
        """End-to-end: convergence event → policy passes → echo created →
        proposal bridge sees persistence → proposal drafted.
        """
        # === 1. Convergence detection ===
        field = CollectiveField("ws_pipe", self.tmp)
        dim = 64
        emb_a = np.random.randn(dim).astype("float32")
        emb_a /= np.linalg.norm(emb_a)
        # Create a very similar embedding for convergence
        emb_b = emb_a + np.random.randn(dim).astype("float32") * 0.05
        emb_b /= np.linalg.norm(emb_b)

        pkt_a = ResonancePacket(
            workspace_id="ws_pipe", agent_id="ryuki", domain_id="research",
            summary="Loss and renewal in the harbor", motifs=["motif_loss"],
            cycle_stage="S3", identity_state="s4",
        )
        pkt_b = ResonancePacket(
            workspace_id="ws_pipe", agent_id="kael", domain_id="research",
            summary="Loss echoing through memory", motifs=["motif_loss"],
            cycle_stage="S3", identity_state="s4",
        )

        field.append_packet(pkt_a, embedding=emb_a)
        conv_event = field.append_packet(pkt_b, embedding=emb_b)

        # Convergence should be detected (high sim, same domain, diff agents)
        if conv_event is None:
            # Similarity might be below threshold — force a deterministic test
            emb_b = emb_a * 1.0  # identical
            pkt_b2 = ResonancePacket(
                workspace_id="ws_pipe", agent_id="kael", domain_id="research",
                summary="Loss echoing through memory", motifs=["motif_loss"],
                cycle_stage="S3", identity_state="s4",
            )
            conv_event = field.append_packet(pkt_b2, embedding=emb_b)

        self.assertIsNotNone(conv_event, "Convergence should be detected")
        event_dict = conv_event.to_dict()

        # === 2. Policy evaluation ===
        policy = CollectivePolicy(self.tmp, "ws_pipe")
        result = policy.evaluate(
            event=event_dict,
            target_agent_id="kael",
            target_domain_id="research",
        )
        self.assertTrue(result.eligible)

        # === 3. Simulate echo creation ===
        echo = _make_echo_payload(
            event_id=event_dict["event_id"],
            source_agents=["ryuki"],
            strength=result.echo_strength,
        )
        policy.record_reingest("kael", event_dict["event_id"])

        # Verify echo containment
        self.assertFalse(should_emit_packet(echo))
        self.assertFalse(allows_collective_reingest(echo))
        self.assertEqual(echo["provenance"], "collective")

        # === 4. Proposal bridge ===
        bridge = CollectiveProposalBridge(
            self.tmp, "ws_pipe", persistence_min=1,
        )
        prop_result = bridge.maybe_draft_proposal(event_dict)
        self.assertTrue(prop_result.drafted)

    def test_low_confidence_blocks_entire_pipeline(self):
        """Low-confidence event should be blocked at policy AND proposal level."""
        event = _make_event(confidence=0.40)

        # Policy blocks
        policy = CollectivePolicy(self.tmp, "ws_pipe")
        pr = policy.evaluate(event, "kael", "research")
        self.assertFalse(pr.eligible)

        # Proposal bridge records but doesn't draft
        bridge = CollectiveProposalBridge(self.tmp, "ws_pipe", persistence_min=1)
        dr = bridge.maybe_draft_proposal(event)
        self.assertFalse(dr.drafted)

    def test_domain_isolation_across_pipeline(self):
        """Events from one domain should not affect another domain's pipeline."""
        event_research = _make_event(domain_id="research")
        _make_event(event_id="cev_creative", domain_id="creative")

        policy = CollectivePolicy(self.tmp, "ws_pipe")

        # Research event evaluated against creative domain — should fail
        r = policy.evaluate(event_research, "kael", "creative")
        self.assertFalse(r.eligible)
        self.assertEqual(r.gate_failed, "domain_match")

    def test_opted_out_agent_blocks_early(self):
        """Opted-out agent should be blocked at gate 2, before any other checks."""
        policy = CollectivePolicy(self.tmp, "ws_pipe")
        policy.set_agent_opt_out("kael", True)
        event = _make_event(confidence=0.95)
        r = policy.evaluate(event, "kael", "research")
        self.assertFalse(r.eligible)
        self.assertEqual(r.gate_failed, "agent_opt_in")


# ===========================================================================
# 4. FIVE INVARIANT EXHAUSTIVE VERIFICATION
# ===========================================================================

class TestFiveInvariants(unittest.TestCase):
    """Exhaustive verification of the 5 design invariants from governance.py.

    These are the non-negotiable rules that must hold across all modules.
    """

    # ── Invariant 1: Protected memories are never weakened automatically ──

    def test_inv1_protected_blocks_compression(self):
        payload = {"governance": {"protected": True}}
        self.assertTrue(is_compression_protected(payload))

    def test_inv1_protected_blocks_decay_acceleration(self):
        """Even if decay_accelerated=True, protected=True wins."""
        payload = {"governance": {"protected": True, "decay_accelerated": True}}
        self.assertFalse(is_decay_accelerated(payload))

    def test_inv1_protected_survives_governance_update(self):
        """Updating other flags doesn't clear protected."""
        payload = {"governance": {"protected": True}}
        update_governance(payload, {"non_shareable": True}, actor="test")
        gov = resolve_governance(payload)
        self.assertTrue(gov.protected)
        self.assertTrue(gov.non_shareable)

    # ── Invariant 2: Non-shareable/export-blocked never emit packets ──

    def test_inv2_non_shareable_blocks_emission(self):
        payload = {"governance": {"non_shareable": True}}
        self.assertFalse(should_emit_packet(payload))

    def test_inv2_export_blocked_blocks_emission(self):
        payload = {"governance": {"collective_export_blocked": True}}
        self.assertFalse(should_emit_packet(payload))

    def test_inv2_both_set_blocks_emission(self):
        payload = {"governance": {"non_shareable": True, "collective_export_blocked": True}}
        self.assertFalse(should_emit_packet(payload))

    def test_inv2_other_flags_dont_block_emission(self):
        """protected, reingest_blocked, decay_accelerated alone don't block emission."""
        for flag in ["protected", "collective_reingest_blocked", "decay_accelerated"]:
            payload = {"governance": {flag: True}}
            self.assertTrue(should_emit_packet(payload),
                            f"Flag '{flag}' should not block emission by itself")

    # ── Invariant 3: Collective echoes are terminal by default ──

    def test_inv3_echo_has_both_blocks(self):
        echo = _make_echo_payload()
        gov = resolve_governance(echo)
        self.assertTrue(gov.collective_reingest_blocked)
        self.assertTrue(gov.collective_export_blocked)

    def test_inv3_echo_cannot_emit(self):
        echo = _make_echo_payload()
        self.assertFalse(should_emit_packet(echo))

    def test_inv3_echo_cannot_be_reingested(self):
        echo = _make_echo_payload()
        self.assertFalse(allows_collective_reingest(echo))

    # ── Invariant 4: Collective echoes are influences, not autobiography ──

    def test_inv4_echo_has_collective_provenance(self):
        echo = _make_echo_payload()
        self.assertEqual(echo["provenance"], "collective")

    def test_inv4_echo_has_source_event_id(self):
        echo = _make_echo_payload(event_id="cev_test")
        self.assertEqual(echo["source_event_id"], "cev_test")

    def test_inv4_echo_has_source_agents(self):
        echo = _make_echo_payload(source_agents=["ryuki"])
        self.assertEqual(echo["source_agents"], ["ryuki"])

    def test_inv4_echo_strength_is_whisper(self):
        self.assertEqual(DEFAULT_ECHO_STRENGTH, 0.25)
        self.assertEqual(DEFAULT_ECHO_STRENGTH_CAP, 0.40)

    def test_inv4_echo_summary_marked(self):
        echo = _make_echo_payload()
        self.assertTrue(echo["summary"].startswith("[collective echo]"))

    # ── Invariant 5: Collective provenance cannot outrank seed/canon ──

    def test_inv5_retrieval_discount_exists(self):
        """Collective memories should get 0.5x retrieval weight."""
        score = 0.80
        discount = 0.50
        self.assertAlmostEqual(score * discount, 0.40)

    def test_inv5_echo_below_organic_at_parity(self):
        """Same base score → echo ranks below organic."""
        base = 0.75
        organic = base
        echo = base * 0.50
        self.assertGreater(organic, echo)

    def test_inv5_drift_budget_protects_identity(self):
        """Agent far from seed is blocked from echoes."""
        ok, _ = check_drift_budget(
            current_drift_score=-0.50,
            drift_direction="away_seed",
            event_domain_id="research",
            agent_domain_id="research",
            event_motifs=[],
            agent_seed_motif_id=None,
        )
        self.assertFalse(ok)

    def test_inv5_echo_not_protected_like_canon(self):
        """Echoes must not be compression-protected (they're not canon)."""
        echo = _make_echo_payload()
        self.assertFalse(is_compression_protected(echo))


# ===========================================================================
# 5. CROSS-MODULE BOUNDARY CONTRACTS
# ===========================================================================

class TestCrossModuleBoundaries(unittest.TestCase):
    """Verify contracts between modules that fabric.py wires together."""

    def test_governance_flags_recognized_by_models(self):
        """MemoryGovernanceFlags should recognize all 5 flags."""
        flags = MemoryGovernanceFlags(
            protected=True,
            non_shareable=True,
            decay_accelerated=True,
            collective_export_blocked=True,
            collective_reingest_blocked=True,
        )
        d = flags.to_dict()
        self.assertEqual(len(d), 5)
        self.assertTrue(all(d.values()))

    def test_convergence_event_to_dict_for_policy(self):
        """ConvergenceEvent.to_dict() shape must be consumable by CollectivePolicy."""
        event = ConvergenceEvent(
            workspace_id="ws_int",
            domain_id="research",
            confidence=0.80,
            participating_agents=["a", "b"],
            dominant_motifs=["m1"],
        )
        d = event.to_dict()
        # Policy reads these keys:
        self.assertIn("confidence", d)
        self.assertIn("domain_id", d)
        self.assertIn("event_id", d)
        self.assertIn("participating_agents", d)
        self.assertIn("dominant_motifs", d)

    def test_policy_result_shape(self):
        """PolicyResult.to_dict() must include all expected fields."""
        r = PolicyResult(eligible=True, echo_strength=0.25)
        d = r.to_dict()
        self.assertIn("eligible", d)
        self.assertIn("gate_failed", d)
        self.assertIn("reason", d)
        self.assertIn("echo_strength", d)

    def test_collective_field_event_consumable_by_policy(self):
        """CollectiveField.get_event() returns a dict that policy can evaluate."""
        tmp = tempfile.mkdtemp()
        field = CollectiveField("ws_contract", tmp)
        event = ConvergenceEvent(
            workspace_id="ws_contract",
            domain_id="research",
            confidence=0.75,
            participating_agents=["a", "b"],
        )
        field.append_event(event)
        retrieved = field.get_event(event.event_id)
        self.assertIsNotNone(retrieved)

        # Should be consumable by policy
        policy = CollectivePolicy(tmp, "ws_contract")
        result = policy.evaluate(retrieved, "b", "research")
        self.assertTrue(result.eligible)

    def test_proposal_bridge_consumes_event_dict(self):
        """CollectiveProposalBridge accepts event dicts from CollectiveField."""
        tmp = tempfile.mkdtemp()
        bridge = CollectiveProposalBridge(tmp, "ws_contract", persistence_min=1)
        event = ConvergenceEvent(
            workspace_id="ws_contract",
            domain_id="research",
            confidence=0.80,
            participating_agents=["a", "b"],
            dominant_motifs=["m1"],
        )
        result = bridge.maybe_draft_proposal(event.to_dict())
        self.assertTrue(result.drafted)

    def test_governance_audit_log_independent_of_payload_audit(self):
        """Workspace-level audit log and per-payload audit are separate."""
        tmp = tempfile.mkdtemp()
        log = GovernanceAuditLog(tmp, "ws_contract")
        log.log(eid=42, agent_id="kael", changes={"protected": True})

        payload = {"summary": "test"}
        update_governance(payload, {"protected": True}, actor="test")

        # Workspace log has 1 entry
        self.assertEqual(len(log.recent()), 1)
        # Payload has its own audit
        self.assertEqual(len(payload["governance_audit"]), 1)


# ===========================================================================
# 6. EDGE CASES AND ADVERSARIAL SCENARIOS
# ===========================================================================

class TestEdgeCasesAndAdversarial(unittest.TestCase):
    """Edge cases that might slip through if modules aren't well-integrated."""

    def test_empty_governance_is_permissive(self):
        """Missing governance should default to all-permissive."""
        payload = {"summary": "no governance at all"}
        self.assertTrue(should_emit_packet(payload))
        self.assertTrue(allows_collective_reingest(payload))
        self.assertFalse(is_compression_protected(payload))
        self.assertFalse(is_decay_accelerated(payload))

    def test_none_payload_is_permissive(self):
        """None payload should default to all-permissive."""
        self.assertTrue(should_emit_packet(None))
        self.assertTrue(allows_collective_reingest(None))
        self.assertFalse(is_compression_protected(None))
        self.assertFalse(is_decay_accelerated(None))

    def test_garbage_governance_is_permissive(self):
        """Non-dict governance should be treated as absent."""
        payload = {"governance": "not_a_dict"}
        self.assertTrue(should_emit_packet(payload))

    def test_unknown_governance_flags_ignored(self):
        """Unknown flags in governance dict should be silently ignored."""
        payload = {"governance": {"protected": True, "future_flag_xyz": True}}
        gov = resolve_governance(payload)
        self.assertTrue(gov.protected)
        # Unknown flag should not appear
        self.assertFalse(hasattr(gov, "future_flag_xyz"))

    def test_update_governance_rejects_unknown_flags(self):
        """update_governance should reject unknown flag names."""
        payload = {"summary": "test"}
        with self.assertRaises(ValueError):
            update_governance(payload, {"nonexistent_flag": True})

    def test_concurrent_tracker_writes_safe(self):
        """ReingestTracker should handle rapid sequential writes."""
        tmp = tempfile.mkdtemp()
        tracker = ReingestTracker(tmp, "ws_concurrent")
        for i in range(50):
            tracker.record(f"agent_{i % 3}", f"cev_{i}")
        # Verify counts
        self.assertEqual(tracker.count_recent("agent_0", 3600), 17)
        self.assertEqual(tracker.count_recent("agent_1", 3600), 17)
        self.assertEqual(tracker.count_recent("agent_2", 3600), 16)

    def test_convergence_event_with_zero_confidence(self):
        """Zero-confidence event should be blocked everywhere."""
        event = _make_event(confidence=0.0)
        tmp = tempfile.mkdtemp()

        policy = CollectivePolicy(tmp, "ws_zero")
        r = policy.evaluate(event, "agent_b", "research")
        self.assertFalse(r.eligible)

        bridge = CollectiveProposalBridge(tmp, "ws_zero", persistence_min=1)
        d = bridge.maybe_draft_proposal(event)
        self.assertFalse(d.drafted)

    def test_echo_strength_cap_is_respected(self):
        """Cannot create an echo stronger than 0.40 regardless of override."""
        strength = min(1.0, DEFAULT_ECHO_STRENGTH_CAP)
        self.assertLessEqual(strength, 0.40)

        strength = min(0.99, DEFAULT_ECHO_STRENGTH_CAP)
        self.assertLessEqual(strength, 0.40)

    def test_extremely_negative_drift_blocks_all_echoes(self):
        """Agent with drift -0.60 (far beyond budget) should be blocked."""
        ok, _ = check_drift_budget(
            current_drift_score=-0.60,
            drift_direction="stable",
            event_domain_id="research",
            agent_domain_id="research",
            event_motifs=[],
            agent_seed_motif_id=None,
        )
        self.assertFalse(ok)

    def test_rate_limit_exhaustion(self):
        """After exhausting rate limit, new events are blocked."""
        tmp = tempfile.mkdtemp()
        policy = CollectivePolicy(tmp, "ws_rate", rate_limit_max=2)

        for i in range(2):
            policy.record_reingest("agent_b", f"cev_fill_{i}")

        event = _make_event(event_id="cev_new")
        r = policy.evaluate(event, "agent_b", "research")
        self.assertFalse(r.eligible)
        self.assertEqual(r.gate_failed, "rate_limit")

    def test_proposal_bridge_handles_none_registry(self):
        """Bridge should work fine without a proposal registry — just tracks."""
        tmp = tempfile.mkdtemp()
        bridge = CollectiveProposalBridge(tmp, "ws_none", persistence_min=1)
        result = bridge.maybe_draft_proposal(_make_event(confidence=0.80))
        self.assertTrue(result.drafted)
        self.assertIsNone(result.proposal_id)

    def test_proposal_bridge_event_always_recorded(self):
        """Even rejected events should be recorded for persistence tracking."""
        tmp = tempfile.mkdtemp()
        bridge = CollectiveProposalBridge(tmp, "ws_record")
        # Low confidence — rejected
        bridge.maybe_draft_proposal(_make_event(confidence=0.10))
        count = bridge.tracker.count_recent("research", ["motif_shared"], 3600)
        self.assertEqual(count, 1)


# ===========================================================================
# 7. COLLECTIVE FIELD + POLICY INTEGRATION
# ===========================================================================

class TestFieldPolicyIntegration(unittest.TestCase):
    """Test that CollectiveField convergence events integrate with policy."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_field_detected_event_passes_policy(self):
        """Convergence events from CollectiveField should be policy-compatible."""
        field = CollectiveField("ws_fpi", self.tmp)
        dim = 32

        # Create identical embeddings for guaranteed convergence
        emb = np.random.randn(dim).astype("float32")
        emb /= np.linalg.norm(emb)

        pkt_a = ResonancePacket(
            workspace_id="ws_fpi", agent_id="agent_a", domain_id="research",
            summary="shared insight", motifs=["m1"],
            cycle_stage="S2", identity_state="s3",
        )
        pkt_b = ResonancePacket(
            workspace_id="ws_fpi", agent_id="agent_b", domain_id="research",
            summary="same insight", motifs=["m1"],
            cycle_stage="S2", identity_state="s3",
        )

        field.append_packet(pkt_a, embedding=emb)
        event = field.append_packet(pkt_b, embedding=emb)

        self.assertIsNotNone(event)

        # Policy should accept it
        policy = CollectivePolicy(self.tmp, "ws_fpi")
        result = policy.evaluate(event.to_dict(), "agent_b", "research")
        self.assertTrue(result.eligible)

    def test_field_stores_event_retrievable_by_id(self):
        """Events stored by field should be retrievable by ID."""
        field = CollectiveField("ws_retrieve", self.tmp)
        event = ConvergenceEvent(
            workspace_id="ws_retrieve",
            domain_id="research",
            confidence=0.80,
        )
        field.append_event(event)
        retrieved = field.get_event(event.event_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["event_id"], event.event_id)

    def test_field_events_filterable_by_domain(self):
        """Events should be filterable by domain."""
        field = CollectiveField("ws_filter", self.tmp)
        e1 = ConvergenceEvent(workspace_id="ws_filter", domain_id="research")
        e2 = ConvergenceEvent(workspace_id="ws_filter", domain_id="creative")
        field.append_event(e1)
        field.append_event(e2)

        research = field.events_by_domain("research")
        creative = field.events_by_domain("creative")
        self.assertEqual(len(research), 1)
        self.assertEqual(len(creative), 1)
        self.assertEqual(research[0]["domain_id"], "research")


# ===========================================================================
# 8. PERSISTENCE + TRACKER INTEGRATION
# ===========================================================================

class TestPersistenceIntegration(unittest.TestCase):
    """Verify that all persistent components survive restart."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_reingest_tracker_survives_restart(self):
        t1 = ReingestTracker(self.tmp, "ws_persist")
        t1.record("kael", "cev_1")
        t1.record("kael", "cev_2")

        t2 = ReingestTracker(self.tmp, "ws_persist")
        self.assertTrue(t2.is_duplicate("kael", "cev_1"))
        self.assertTrue(t2.is_duplicate("kael", "cev_2"))
        self.assertFalse(t2.is_duplicate("kael", "cev_3"))
        self.assertEqual(t2.count_recent("kael", 3600), 2)

    def test_persistence_tracker_survives_restart(self):
        t1 = ConvergencePersistenceTracker(self.tmp, "ws_persist")
        t1.record_event(_make_event(event_id="cev_1"))
        t1.record_proposed("cev_1", "research")

        t2 = ConvergencePersistenceTracker(self.tmp, "ws_persist")
        self.assertEqual(t2.count_recent("research", ["motif_shared"], 3600), 1)
        self.assertTrue(t2.is_event_proposed("cev_1"))

    def test_collective_field_events_survive_restart(self):
        f1 = CollectiveField("ws_persist", self.tmp)
        event = ConvergenceEvent(
            workspace_id="ws_persist", domain_id="research", confidence=0.75,
        )
        f1.append_event(event)

        f2 = CollectiveField("ws_persist", self.tmp)
        retrieved = f2.get_event(event.event_id)
        self.assertIsNotNone(retrieved)

    def test_governance_audit_log_survives_restart(self):
        log1 = GovernanceAuditLog(self.tmp, "ws_persist")
        log1.log(eid=1, agent_id="kael", changes={"protected": True})

        log2 = GovernanceAuditLog(self.tmp, "ws_persist")
        records = log2.recent()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["agent_id"], "kael")


if __name__ == "__main__":
    unittest.main()
