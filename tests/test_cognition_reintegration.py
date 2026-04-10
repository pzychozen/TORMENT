"""
tests/test_cognition_reintegration.py — Reintegration membrane + drift stub (Patch 4)

Tests for:
    - Reintegration: finding merge, dissent preservation (Invariant C),
      proposal collection, governance rejection (Invariant G), final answer
    - Drift stub: zero/stub/failing drift checks, DriftReport generation
    - Full pipeline integration: roles → reintegration with drift gating

See docs/archive/AGENT_SPINE_PLAN.md §9 and §11 Patch 4.
"""
from __future__ import annotations

import os
import sys
import unittest
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cognition.task_models import (
    TaskPacket, RoutingDecision, ReintegrationResult,
    MODE_AUTO, MODE_IDENTITY,
    APERTURE_NARROW, APERTURE_PROTECTED,
)
from cognition.apertures import MemoryContext, APERTURE_CONFIGS
from cognition.reintegration import reintegrate
from cognition.drift import (
    stub_drift_check,
    zero_drift_check,
    failing_drift_check,
)
from schemas.role_output import RoleOutput
from schemas.provenance import (
    Provenance,
    STATUS_SKEPTIC_PASSED,
)
from schemas.memory_proposal import MemoryProposal
from schemas.drift_report import DriftReport
from roles.interpreter import Interpreter
from roles.engineer import Engineer
from roles.skeptic import Skeptic
from roles.archivist import Archivist


# ============================================================================
# Helpers
# ============================================================================

def _make_task(user_input="Implement the router module", mode=MODE_AUTO):
    return TaskPacket(workspace_id="ws_test", agent_id="agent_test",
                      user_input=user_input, mode=mode)


def _make_routing(aperture=APERTURE_NARROW, drift_check=False, skeptic_pass=False):
    return RoutingDecision(
        roles_to_activate=["interpreter", "engineer", "skeptic", "archivist"],
        primary_domains=["research"],
        aperture=aperture,
        require_drift_check=drift_check,
        require_skeptic_pass=skeptic_pass,
    )


def _make_ctx(aperture="narrow", private=None, drift=None, character=None):
    config = APERTURE_CONFIGS[aperture]
    return MemoryContext(
        aperture_name=aperture, config=config,
        private_memories=private or [],
        shared_memories=[],
        character_context=character,
        drift_snapshot=drift,
        domain_id="research",
        query_text="test",
    )


def _make_memories(n):
    return [{"id": i, "text": f"Memory {i}", "score": 0.9} for i in range(n)]


def _make_role_output(name, summary="Test output", findings=None,
                      recommendations=None, contradictions=None,
                      proposals=None, confidence=0.9,
                      verification_status=STATUS_SKEPTIC_PASSED):
    prov = Provenance.from_role(name, "tsk_test", confidence=confidence)
    if name == "skeptic":
        prov.verification_status = verification_status
    return RoleOutput(
        role_name=name,
        summary=summary,
        findings=findings or [],
        recommendations=recommendations or [],
        contradictions=contradictions or [],
        memory_proposals=proposals or [],
        confidence=confidence,
        provenance=prov,
    )


def _make_proposal(strength=0.5, depth=0, memory_type="episode"):
    prov = Provenance.from_role("engineer", "tsk_test", confidence=0.7)
    prov.derivation_depth = depth
    return MemoryProposal.create(
        summary="Test proposal",
        content="Test content",
        target_domain="research",
        proposed_strength=strength,
        half_life_days=14.0,
        memory_type=memory_type,
        provenance=prov,
    )


# ============================================================================
# Reintegration — finding merge
# ============================================================================

class TestFindingMerge(unittest.TestCase):
    """Merged findings are deduplicated and role-tagged."""

    def test_findings_merged_with_role_prefix(self):
        outputs = [
            _make_role_output("interpreter", findings=["Found X"]),
            _make_role_output("engineer", findings=["Found Y"]),
        ]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertTrue(any("[interpreter] Found X" in f for f in result.merged_findings))
        self.assertTrue(any("[engineer] Found Y" in f for f in result.merged_findings))

    def test_duplicate_findings_deduplicated(self):
        outputs = [
            _make_role_output("interpreter", findings=["Same finding"]),
            _make_role_output("engineer", findings=["Same finding"]),
        ]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        matching = [f for f in result.merged_findings if "Same finding" in f]
        # Only one instance after dedup
        self.assertEqual(len(matching), 1)

    def test_empty_outputs_produce_empty_findings(self):
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, [], ctx)
        self.assertEqual(result.merged_findings, [])


# ============================================================================
# Reintegration — dissent detection (Invariant C)
# ============================================================================

class TestDissentDetection(unittest.TestCase):
    """Contradictions are preserved as structured dissent."""

    def test_detects_should_vs_should_not(self):
        outputs = [
            _make_role_output("interpreter",
                              recommendations=["We should proceed"]),
            _make_role_output("engineer",
                              recommendations=["We should not proceed with this"]),
        ]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertTrue(result.has_dissent)
        self.assertGreater(len(result.dissent), 0)
        d = result.dissent[0]
        self.assertIn("role_a", d)
        self.assertIn("role_b", d)
        self.assertIn("claim_a", d)
        self.assertIn("claim_b", d)
        self.assertIn("topic", d)

    def test_detects_safe_vs_unsafe(self):
        outputs = [
            _make_role_output("engineer", findings=["This approach is safe"]),
            _make_role_output("skeptic", findings=["This approach is unsafe"]),
        ]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertTrue(result.has_dissent)

    def test_no_dissent_when_compatible(self):
        outputs = [
            _make_role_output("interpreter", findings=["Looks good"]),
            _make_role_output("engineer", findings=["All clear"]),
        ]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertFalse(result.has_dissent)

    def test_skeptic_contradictions_surfaced(self):
        outputs = [
            _make_role_output("skeptic",
                              contradictions=["Engineer says X but evidence shows Y"]),
        ]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertTrue(result.has_dissent)
        self.assertTrue(any("skeptic-detected" in d["topic"] for d in result.dissent))


# ============================================================================
# Reintegration — final invariant enforcement (circuit breaker)
# ============================================================================

class TestFinalInvariantEnforcement(unittest.TestCase):
    """Reintegration enforces only hard safety invariants.

    Semantic governance (strength assessment, skeptic evaluation, derivation
    depth) is the archivist's responsibility. Reintegration is the final
    circuit breaker: provenance, drift hard block, and respecting archivist
    rejections.
    """

    def test_clean_proposal_passes_through(self):
        """Proposal with provenance and no drift → not rejected by reintegration."""
        mp = _make_proposal(strength=0.5)
        # Simulate archivist having already approved this
        mp.approve()
        outputs = [_make_role_output("archivist", proposals=[mp])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertEqual(len(result.governance_rejections), 0)
        approved = [p for p in result.all_memory_proposals if p.is_approved]
        self.assertEqual(len(approved), 1)

    def test_missing_provenance_rejected(self):
        """Invariant B: reintegration catches missing provenance even if archivist missed it."""
        mp = MemoryProposal(
            proposal_id="no_prov", summary="Bad", content="C",
            target_domain="research", proposed_strength=0.5,
            half_life_days=14.0, memory_type="episode", provenance=None,
        )
        outputs = [_make_role_output("engineer", proposals=[mp])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertTrue(result.has_governance_rejections)
        self.assertIn("Invariant B", result.governance_rejections[0]["reason"])

    def test_drift_block_rejects_all(self):
        """Invariant E: drift hard block is enforced by reintegration as circuit breaker."""
        mp = _make_proposal(strength=0.5)
        outputs = [_make_role_output("engineer", proposals=[mp])]
        task = _make_task()
        routing = _make_routing(drift_check=True)
        ctx = _make_ctx()
        drift_fn = stub_drift_check(total_drift=0.55)
        result = reintegrate(task, routing, outputs, ctx, drift_check_fn=drift_fn)
        self.assertTrue(result.has_governance_rejections)
        self.assertIn("Drift block", result.governance_rejections[0]["reason"])

    def test_drift_yellow_not_enforced_by_reintegration(self):
        """Yellow drift is the archivist's domain, not reintegration's."""
        mp = _make_proposal(strength=0.8)
        outputs = [_make_role_output("engineer", proposals=[mp])]
        task = _make_task()
        routing = _make_routing(drift_check=True)
        ctx = _make_ctx()
        drift_fn = stub_drift_check(total_drift=0.25)
        result = reintegrate(task, routing, outputs, ctx, drift_check_fn=drift_fn)
        # Reintegration should NOT reject for yellow drift — that's archivist's job
        reint_rejections = [r for r in result.governance_rejections
                            if "Drift block" in r["reason"]]
        self.assertEqual(len(reint_rejections), 0)

    def test_drift_yellow_allows_low_strength(self):
        """Low strength under yellow drift passes reintegration's checks."""
        mp = _make_proposal(strength=0.4)
        outputs = [_make_role_output("engineer", proposals=[mp])]
        task = _make_task()
        routing = _make_routing(drift_check=True)
        ctx = _make_ctx()
        drift_fn = stub_drift_check(total_drift=0.25)
        result = reintegrate(task, routing, outputs, ctx, drift_check_fn=drift_fn)
        self.assertEqual(len(result.governance_rejections), 0)

    def test_archivist_rejection_respected(self):
        """Reintegration respects archivist's rejection — does not override."""
        mp = _make_proposal(strength=0.85)
        mp.reject("Skeptic flagged — archivist rejected")
        outputs = [_make_role_output("archivist", proposals=[mp])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertTrue(result.has_governance_rejections)
        self.assertIn("archivist", result.governance_rejections[0]["reason"].lower())

    def test_archivist_approval_not_overridden(self):
        """Reintegration does NOT call approve() — the archivist's decision stands."""
        mp = _make_proposal(strength=0.85)
        mp.approve()
        outputs = [_make_role_output("archivist", proposals=[mp])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertEqual(len(result.governance_rejections), 0)
        self.assertTrue(mp.is_approved)

    def test_deep_derivation_is_archivist_domain(self):
        """Deep derivation + high strength is archivist's concern, not reintegration's."""
        mp = _make_proposal(strength=0.8, depth=5)
        # Not pre-reviewed by archivist — passes reintegration (has provenance)
        outputs = [_make_role_output("engineer", proposals=[mp])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        # Reintegration only checks provenance and drift block
        invariant_rejections = [r for r in result.governance_rejections
                                if "Invariant B" in r["reason"] or "Drift block" in r["reason"]]
        self.assertEqual(len(invariant_rejections), 0)

    def test_multiple_proposals_mixed_decisions(self):
        """Mix of clean and provenance-less proposals."""
        good = _make_proposal(strength=0.5)
        bad = MemoryProposal(
            proposal_id="no_prov", summary="Bad", content="C",
            target_domain="research", proposed_strength=0.5,
            half_life_days=14.0, memory_type="episode", provenance=None,
        )
        outputs = [_make_role_output("engineer", proposals=[good, bad])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        # Only the provenance-less one should be rejected by reintegration
        self.assertEqual(len(result.governance_rejections), 1)
        self.assertIn("Invariant B", result.governance_rejections[0]["reason"])


# ============================================================================
# Reintegration — proposal deduplication
# ============================================================================

class TestProposalDedup(unittest.TestCase):
    """Proposals are deduplicated by proposal_id, preferring archivist-reviewed."""

    def test_duplicate_proposals_deduped(self):
        """Same proposal from engineer and archivist → only one in result."""
        mp = _make_proposal(strength=0.5)
        eng_out = _make_role_output("engineer", proposals=[mp])
        # Archivist collects same proposal, reviews it, re-emits
        mp_reviewed = mp  # same object, same proposal_id
        mp_reviewed.approve()
        arch_out = _make_role_output("archivist", proposals=[mp_reviewed])
        outputs = [eng_out, arch_out]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        # Should only appear once
        ids = [p.proposal_id for p in result.all_memory_proposals]
        self.assertEqual(len(ids), len(set(ids)),
                         f"Duplicate proposal_ids in result: {ids}")

    def test_archivist_version_preferred(self):
        """When duplicates exist, the archivist-reviewed version wins."""
        from schemas.memory_proposal import MemoryProposal as MP
        from schemas.provenance import Provenance
        prov = Provenance.from_role("engineer", "tsk_dedup", confidence=0.7)
        # Engineer's original (pending)
        mp_eng = MP.create(
            summary="Test dedup", content="C", target_domain="research",
            proposed_strength=0.5, half_life_days=14.0,
            memory_type="episode", provenance=prov,
        )
        # Archivist's copy with same ID but reviewed
        mp_arch = MP(
            proposal_id=mp_eng.proposal_id,
            summary="Test dedup", content="C", target_domain="research",
            proposed_strength=0.5, half_life_days=14.0,
            memory_type="episode", provenance=prov,
        )
        mp_arch.approve()

        eng_out = _make_role_output("engineer", proposals=[mp_eng])
        arch_out = _make_role_output("archivist", proposals=[mp_arch])
        outputs = [eng_out, arch_out]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertEqual(len(result.all_memory_proposals), 1)
        # The surviving version should be the archivist's (approved)
        self.assertTrue(result.all_memory_proposals[0].is_approved)

    def test_unique_proposals_not_affected(self):
        """Proposals with different IDs are all kept."""
        mp1 = _make_proposal(strength=0.5)
        mp2 = _make_proposal(strength=0.6)
        self.assertNotEqual(mp1.proposal_id, mp2.proposal_id)
        outputs = [_make_role_output("engineer", proposals=[mp1, mp2])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertEqual(len(result.all_memory_proposals), 2)


# ============================================================================
# Reintegration — final answer
# ============================================================================

class TestFinalAnswer(unittest.TestCase):
    """Final answer is built from role summaries."""

    def test_contains_interpreter_summary(self):
        outputs = [
            _make_role_output("interpreter", summary="Intent: engineering"),
            _make_role_output("engineer", summary="Plan: 3 steps"),
        ]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertIn("Interpreter", result.final_answer)
        self.assertIn("Engineer", result.final_answer)

    def test_empty_outputs_fallback(self):
        task = _make_task("Hello world")
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, [], ctx)
        self.assertIn("Hello world", result.final_answer)

    def test_dissent_noted_in_answer(self):
        outputs = [
            _make_role_output("interpreter",
                              recommendations=["We should proceed"]),
            _make_role_output("engineer",
                              recommendations=["We should not proceed"]),
        ]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertIn("dissent", result.final_answer.lower())


# ============================================================================
# Reintegration — memory effects
# ============================================================================

class TestMemoryEffects(unittest.TestCase):
    """Memory effects summary tracks approved and rejected proposals."""

    def test_memory_effects_structure(self):
        mp = _make_proposal(strength=0.5)
        outputs = [_make_role_output("engineer", proposals=[mp])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertIn("approved", result.memory_effects)
        self.assertIn("rejected", result.memory_effects)
        self.assertEqual(len(result.memory_effects["approved"]), 1)
        self.assertEqual(len(result.memory_effects["rejected"]), 0)

    def test_rejected_in_memory_effects(self):
        mp = MemoryProposal(
            proposal_id="no_prov", summary="Bad", content="C",
            target_domain="research", proposed_strength=0.5,
            half_life_days=14.0, memory_type="episode", provenance=None,
        )
        outputs = [_make_role_output("engineer", proposals=[mp])]
        task = _make_task()
        routing = _make_routing()
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertEqual(len(result.memory_effects["rejected"]), 1)
        self.assertIn("rejection_reason",
                       result.memory_effects["rejected"][0])


# ============================================================================
# Drift stub
# ============================================================================

class TestDriftStub(unittest.TestCase):
    """Drift check stubs for testing."""

    def test_zero_drift(self):
        fn = zero_drift_check()
        report = fn("ws1", "a1")
        self.assertIsInstance(report, DriftReport)
        self.assertEqual(report.total_drift, 0.0)
        self.assertEqual(report.zone, "green")

    def test_stub_drift_custom(self):
        fn = stub_drift_check(total_drift=0.30, domain_shift=0.1,
                              reasons=["test reason"])
        report = fn("ws1", "a1")
        self.assertAlmostEqual(report.total_drift, 0.30)
        self.assertEqual(report.zone, "yellow")
        self.assertEqual(report.reasons, ["test reason"])

    def test_failing_drift_raises(self):
        fn = failing_drift_check()
        with self.assertRaises(RuntimeError):
            fn("ws1", "a1")

    def test_drift_failure_in_reintegration_defaults_to_block(self):
        """When drift check fails, reintegration defaults to hard_block."""
        mp = _make_proposal(strength=0.5)
        outputs = [_make_role_output("engineer", proposals=[mp])]
        task = _make_task()
        routing = _make_routing(drift_check=True)
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx,
                             drift_check_fn=failing_drift_check())
        # Should have a drift report with hard_block
        self.assertIsNotNone(result.drift_report)
        self.assertEqual(result.drift_report.zone, "hard_block")

    def test_no_drift_fn_when_required_defaults_zero(self):
        """When drift_check_fn is None but required, defaults to zero drift."""
        outputs = [_make_role_output("interpreter")]
        task = _make_task()
        routing = _make_routing(drift_check=True)
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx, drift_check_fn=None)
        self.assertIsNotNone(result.drift_report)
        self.assertEqual(result.drift_report.zone, "green")

    def test_drift_not_called_when_not_required(self):
        """When routing doesn't require drift, drift_report is None."""
        outputs = [_make_role_output("interpreter")]
        task = _make_task()
        routing = _make_routing(drift_check=False)
        ctx = _make_ctx()
        result = reintegrate(task, routing, outputs, ctx)
        self.assertIsNone(result.drift_report)


# ============================================================================
# Full pipeline: roles → reintegration
# ============================================================================

class TestFullReintegrationPipeline(unittest.TestCase):
    """End-to-end: run all roles then reintegrate."""

    def test_engineering_pipeline(self):
        task = _make_task("Implement the new router module")
        ctx = _make_ctx(private=_make_memories(5))
        routing = _make_routing()

        outputs: List[RoleOutput] = []
        outputs.append(Interpreter().run(task, ctx, outputs))
        outputs.append(Engineer().run(task, ctx, outputs))
        outputs.append(Skeptic().run(task, ctx, outputs))
        outputs.append(Archivist().run(task, ctx, outputs))

        result = reintegrate(task, routing, outputs, ctx)

        self.assertIsInstance(result, ReintegrationResult)
        self.assertGreater(len(result.final_answer), 0)
        self.assertGreater(len(result.merged_findings), 0)
        self.assertEqual(len(result.role_outputs), 4)
        self.assertIsNone(result.drift_report)  # no drift check required

    def test_identity_pipeline_with_drift_block(self):
        task = _make_task("Rewrite my core identity", mode=MODE_IDENTITY)
        drift = {"total_drift": 0.40}
        ctx = _make_ctx(aperture="protected", private=_make_memories(3),
                        character={"name": "Ryuki"}, drift=drift)
        routing = _make_routing(aperture=APERTURE_PROTECTED, drift_check=True,
                                skeptic_pass=True)
        drift_fn = stub_drift_check(total_drift=0.45)

        outputs: List[RoleOutput] = []
        outputs.append(Interpreter().run(task, ctx, outputs))
        # No engineer in identity route
        outputs.append(Skeptic().run(task, ctx, outputs))
        outputs.append(Archivist().run(task, ctx, outputs))

        result = reintegrate(task, routing, outputs, ctx, drift_check_fn=drift_fn)

        self.assertIsNotNone(result.drift_report)
        self.assertEqual(result.drift_report.zone, "red")
        # All proposals should be rejected under drift block
        if result.all_memory_proposals:
            for p in result.all_memory_proposals:
                self.assertTrue(p.is_rejected)

    def test_result_serialization_round_trip(self):
        task = _make_task("Test round trip")
        ctx = _make_ctx(private=_make_memories(3))
        routing = _make_routing(drift_check=True)
        drift_fn = stub_drift_check(total_drift=0.15)

        outputs: List[RoleOutput] = []
        outputs.append(Interpreter().run(task, ctx, outputs))
        outputs.append(Engineer().run(task, ctx, outputs))
        outputs.append(Skeptic().run(task, ctx, outputs))
        outputs.append(Archivist().run(task, ctx, outputs))

        result = reintegrate(task, routing, outputs, ctx, drift_check_fn=drift_fn)

        d = result.to_dict()
        restored = ReintegrationResult.from_dict(d)
        self.assertEqual(restored.final_answer, result.final_answer)
        self.assertEqual(len(restored.merged_findings), len(result.merged_findings))
        self.assertEqual(len(restored.role_outputs), len(result.role_outputs))
        self.assertIsNotNone(restored.drift_report)


if __name__ == "__main__":
    unittest.main()
