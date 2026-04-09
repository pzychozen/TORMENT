"""
tests/test_cognition_schemas.py — Data contracts for TORMENT Agent Spine (Patch 1)

Tests for:
    - Provenance: creation, derivation chains, serialization round-trip, validation
    - DriftReport: zone policy, threshold boundaries, serialization round-trip
    - RoleOutput: creation, nested objects, serialization round-trip, validation
    - MemoryProposal: creation, approve/reject lifecycle, governance flags, round-trip
    - TaskPacket: creation, auto-generated fields, validation, round-trip
    - RoutingDecision: creation, aperture/scope validation, round-trip
    - ReintegrationResult: creation, dissent tracking, nested round-trip

See AGENT_SPINE_PLAN.md §11 Patch 1: "serialization round-trips, default values,
provenance chain validation."
"""
from __future__ import annotations

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.provenance import (
    Provenance,
    SOURCE_USER_INPUT,
    SOURCE_ROLE_OUTPUT,
    SOURCE_DERIVED,
    STATUS_UNVERIFIED,
)
from schemas.drift_report import (
    DriftReport,
    DRIFT_GREEN,
    DRIFT_YELLOW,
    DRIFT_RED,
)
from schemas.role_output import RoleOutput
from schemas.memory_proposal import (
    MemoryProposal,
    DEFAULT_GOVERNANCE_FLAGS,
)
from cognition.task_models import (
    TaskPacket,
    RoutingDecision,
    ReintegrationResult,
    MODE_AUTO,
    MODE_ENGINEERING,
    MODE_STRATEGIC,
    MODE_IDENTITY,
    PRIORITY_LOW,
    PRIORITY_NORMAL,
    PRIORITY_HIGH,
    APERTURE_NARROW,
    APERTURE_BROAD,
    APERTURE_PROTECTED,
    SCOPE_NONE,
    SCOPE_PRIVATE,
)


# ============================================================================
# Provenance
# ============================================================================

class TestProvenance(unittest.TestCase):
    """Provenance lineage metadata — Invariant B enforcement."""

    def test_from_user(self):
        p = Provenance.from_user("tsk_abc123")
        self.assertEqual(p.source_type, SOURCE_USER_INPUT)
        self.assertIsNone(p.source_role)
        self.assertEqual(p.parent_ids, ["tsk_abc123"])
        self.assertEqual(p.derivation_depth, 0)
        self.assertEqual(p.confidence, 1.0)
        self.assertEqual(p.verification_status, STATUS_UNVERIFIED)
        self.assertGreater(p.timestamp, 0)

    def test_from_role(self):
        p = Provenance.from_role("interpreter", "tsk_abc123", confidence=0.9)
        self.assertEqual(p.source_type, SOURCE_ROLE_OUTPUT)
        self.assertEqual(p.source_role, "interpreter")
        self.assertEqual(p.derivation_depth, 1)
        self.assertAlmostEqual(p.confidence, 0.9)

    def test_derive_chain(self):
        root = Provenance.from_user("tsk_001")
        child = root.derive("engineer", confidence=0.8)
        self.assertEqual(child.source_type, SOURCE_DERIVED)
        self.assertEqual(child.source_role, "engineer")
        self.assertEqual(child.derivation_depth, 1)
        self.assertAlmostEqual(child.confidence, 0.8)
        self.assertEqual(child.verification_status, STATUS_UNVERIFIED)

        grandchild = child.derive("skeptic", confidence=0.95)
        self.assertEqual(grandchild.derivation_depth, 2)
        # confidence = min(child.confidence, 0.95) = 0.8
        self.assertAlmostEqual(grandchild.confidence, 0.8)

    def test_derive_confidence_clamping(self):
        """derive() takes min(parent, new) — never inflates."""
        root = Provenance.from_role("engineer", "tsk_x", confidence=0.5)
        child = root.derive("skeptic", confidence=0.9)
        self.assertAlmostEqual(child.confidence, 0.5)

    def test_serialization_round_trip(self):
        original = Provenance.from_role("interpreter", "tsk_rt1", confidence=0.85)
        d = original.to_dict()
        restored = Provenance.from_dict(d)
        self.assertEqual(original.source_type, restored.source_type)
        self.assertEqual(original.source_role, restored.source_role)
        self.assertEqual(original.parent_ids, restored.parent_ids)
        self.assertEqual(original.derivation_depth, restored.derivation_depth)
        self.assertAlmostEqual(original.confidence, restored.confidence)
        self.assertEqual(original.verification_status, restored.verification_status)
        self.assertEqual(original.timestamp, restored.timestamp)

    def test_unknown_fields_ignored(self):
        d = {
            "source_type": SOURCE_USER_INPUT,
            "confidence": 0.7,
            "extra_field": "should be ignored",
            "another": 42,
        }
        p = Provenance.from_dict(d)
        self.assertEqual(p.source_type, SOURCE_USER_INPUT)
        self.assertAlmostEqual(p.confidence, 0.7)

    def test_invalid_source_type_rejected(self):
        with self.assertRaises(ValueError):
            Provenance(source_type="invented")

    def test_invalid_verification_status_rejected(self):
        with self.assertRaises(ValueError):
            Provenance(source_type=SOURCE_USER_INPUT, verification_status="invalid")

    def test_confidence_out_of_range(self):
        with self.assertRaises(ValueError):
            Provenance(source_type=SOURCE_USER_INPUT, confidence=1.5)
        with self.assertRaises(ValueError):
            Provenance(source_type=SOURCE_USER_INPUT, confidence=-0.1)

    def test_negative_derivation_depth_rejected(self):
        with self.assertRaises(ValueError):
            Provenance(source_type=SOURCE_USER_INPUT, derivation_depth=-1)

    def test_from_dict_empty_rejected(self):
        with self.assertRaises(ValueError):
            Provenance.from_dict({})
        with self.assertRaises(ValueError):
            Provenance.from_dict(None)

    def test_auto_timestamp(self):
        before = int(time.time())
        p = Provenance(source_type=SOURCE_USER_INPUT)
        after = int(time.time())
        self.assertGreaterEqual(p.timestamp, before)
        self.assertLessEqual(p.timestamp, after)

    def test_explicit_timestamp_preserved(self):
        p = Provenance(source_type=SOURCE_USER_INPUT, timestamp=1000)
        self.assertEqual(p.timestamp, 1000)


# ============================================================================
# DriftReport
# ============================================================================

class TestDriftReport(unittest.TestCase):
    """Drift zone policy — threshold boundaries from AGENT_SPINE_PLAN §15.3."""

    def test_green_zone(self):
        dr = DriftReport(total_drift=0.10)
        self.assertEqual(dr.zone, "green")
        self.assertTrue(dr.allows_durable_write)
        self.assertTrue(dr.allows_provisional_write)
        self.assertFalse(dr.requires_block)

    def test_yellow_zone(self):
        dr = DriftReport(total_drift=0.25)
        self.assertEqual(dr.zone, "yellow")
        self.assertFalse(dr.allows_durable_write)
        self.assertTrue(dr.allows_provisional_write)
        self.assertFalse(dr.requires_block)

    def test_red_zone(self):
        dr = DriftReport(total_drift=0.40)
        self.assertEqual(dr.zone, "red")
        self.assertFalse(dr.allows_durable_write)
        self.assertFalse(dr.allows_provisional_write)
        self.assertTrue(dr.requires_block)

    def test_hard_block_zone(self):
        dr = DriftReport(total_drift=0.55)
        self.assertEqual(dr.zone, "hard_block")
        self.assertFalse(dr.allows_durable_write)
        self.assertFalse(dr.allows_provisional_write)
        self.assertTrue(dr.requires_block)

    def test_boundary_green_yellow(self):
        """Exactly at 0.20 is yellow, not green."""
        dr = DriftReport(total_drift=DRIFT_GREEN)
        self.assertEqual(dr.zone, "yellow")

    def test_boundary_yellow_red(self):
        """Exactly at 0.35 is red, not yellow."""
        dr = DriftReport(total_drift=DRIFT_YELLOW)
        self.assertEqual(dr.zone, "red")

    def test_boundary_red_hard_block(self):
        """Exactly at 0.50 is hard_block, not red."""
        dr = DriftReport(total_drift=DRIFT_RED)
        self.assertEqual(dr.zone, "hard_block")

    def test_governance_breach_overrides(self):
        """Any governance breach forces block regardless of drift value."""
        dr = DriftReport(total_drift=0.05, governance_breach=True)
        self.assertEqual(dr.zone, "green")  # zone itself is green...
        self.assertFalse(dr.allows_durable_write)  # ...but breach blocks writes
        self.assertFalse(dr.allows_provisional_write)
        self.assertTrue(dr.requires_block)

    def test_defaults_are_green(self):
        dr = DriftReport()
        self.assertEqual(dr.total_drift, 0.0)
        self.assertEqual(dr.zone, "green")
        self.assertTrue(dr.allows_durable_write)

    def test_serialization_round_trip(self):
        original = DriftReport(
            total_drift=0.30,
            domain_shift=0.10,
            motif_shift=0.15,
            style_shift=0.05,
            reasons=["motif divergence detected"],
        )
        d = original.to_dict()
        # to_dict adds computed properties
        self.assertIn("zone", d)
        self.assertEqual(d["zone"], "yellow")
        # round-trip through from_dict (computed props ignored)
        restored = DriftReport.from_dict(d)
        self.assertAlmostEqual(restored.total_drift, 0.30)
        self.assertAlmostEqual(restored.domain_shift, 0.10)
        self.assertEqual(restored.reasons, ["motif divergence detected"])

    def test_from_dict_empty_returns_default(self):
        dr = DriftReport.from_dict({})
        self.assertEqual(dr.total_drift, 0.0)
        self.assertEqual(dr.zone, "green")


# ============================================================================
# MemoryProposal
# ============================================================================

class TestMemoryProposal(unittest.TestCase):
    """Archivist memory proposals — Invariants A and G."""

    def _make_proposal(self, **overrides):
        prov = Provenance.from_role("archivist", "tsk_mp1")
        defaults = dict(
            proposal_id="prop_001",
            summary="Test insight",
            content="Detailed content about test insight",
            target_domain="research",
            proposed_strength=0.8,
            half_life_days=30.0,
            memory_type="insight",
            provenance=prov,
        )
        defaults.update(overrides)
        return MemoryProposal(**defaults)

    def test_creation_defaults(self):
        mp = self._make_proposal()
        self.assertEqual(mp.decision, "pending")
        self.assertIsNone(mp.rejection_reason)
        self.assertFalse(mp.is_approved)
        self.assertFalse(mp.is_rejected)
        self.assertEqual(mp.governance_flags, DEFAULT_GOVERNANCE_FLAGS)

    def test_approve_lifecycle(self):
        mp = self._make_proposal()
        mp.approve()
        self.assertTrue(mp.is_approved)
        self.assertFalse(mp.is_rejected)
        self.assertEqual(mp.decision, "approved")
        self.assertIsNone(mp.rejection_reason)

    def test_reject_lifecycle(self):
        mp = self._make_proposal()
        mp.reject("drift too high")
        self.assertTrue(mp.is_rejected)
        self.assertFalse(mp.is_approved)
        self.assertEqual(mp.rejection_reason, "drift too high")

    def test_auto_proposal_id(self):
        mp = MemoryProposal(
            proposal_id="",
            summary="Auto ID test",
            content="Content",
            target_domain="meta",
            proposed_strength=0.5,
            half_life_days=7.0,
            memory_type="episode",
        )
        self.assertGreater(len(mp.proposal_id), 0)

    def test_create_factory(self):
        prov = Provenance.from_role("archivist", "tsk_f1")
        mp = MemoryProposal.create(
            summary="Factory test",
            content="Content from factory",
            target_domain="engineering",
            proposed_strength=0.7,
            half_life_days=14.0,
            memory_type="motif_seed",
            provenance=prov,
        )
        self.assertGreater(len(mp.proposal_id), 0)
        self.assertEqual(mp.decision, "pending")
        self.assertEqual(mp.memory_type, "motif_seed")

    def test_strength_validation(self):
        with self.assertRaises(ValueError):
            self._make_proposal(proposed_strength=1.5)
        with self.assertRaises(ValueError):
            self._make_proposal(proposed_strength=-0.1)

    def test_half_life_validation(self):
        with self.assertRaises(ValueError):
            self._make_proposal(half_life_days=0)
        with self.assertRaises(ValueError):
            self._make_proposal(half_life_days=-5)

    def test_serialization_round_trip(self):
        mp = self._make_proposal()
        mp.approve()
        d = mp.to_dict()
        restored = MemoryProposal.from_dict(d)
        self.assertEqual(restored.summary, mp.summary)
        self.assertEqual(restored.target_domain, mp.target_domain)
        self.assertEqual(restored.decision, "approved")
        self.assertAlmostEqual(restored.proposed_strength, 0.8)
        # nested provenance restored
        self.assertIsNotNone(restored.provenance)
        self.assertEqual(restored.provenance.source_role, "archivist")

    def test_governance_flags_independent(self):
        """Each proposal gets its own copy of governance flags."""
        mp1 = self._make_proposal()
        mp2 = self._make_proposal()
        mp1.governance_flags["protected"] = True
        self.assertFalse(mp2.governance_flags["protected"])

    def test_from_dict_empty_rejected(self):
        with self.assertRaises(ValueError):
            MemoryProposal.from_dict({})


# ============================================================================
# RoleOutput
# ============================================================================

class TestRoleOutput(unittest.TestCase):
    """Structured role output — Invariant C (contradictions preserved)."""

    def test_creation_defaults(self):
        ro = RoleOutput(role_name="interpreter", summary="Parsed user intent")
        self.assertEqual(ro.role_name, "interpreter")
        self.assertEqual(ro.findings, [])
        self.assertEqual(ro.contradictions, [])
        self.assertAlmostEqual(ro.confidence, 1.0)
        self.assertFalse(ro.has_contradictions)
        self.assertFalse(ro.has_memory_proposals)

    def test_with_contradictions(self):
        ro = RoleOutput(
            role_name="skeptic",
            summary="Found issues",
            contradictions=["Claim A conflicts with Claim B"],
        )
        self.assertTrue(ro.has_contradictions)

    def test_with_memory_proposals(self):
        prov = Provenance.from_role("archivist", "tsk_ro1")
        mp = MemoryProposal.create(
            summary="Store this",
            content="Content",
            target_domain="research",
            proposed_strength=0.6,
            half_life_days=14.0,
            memory_type="episode",
            provenance=prov,
        )
        ro = RoleOutput(
            role_name="archivist",
            summary="Proposing memory write",
            memory_proposals=[mp],
        )
        self.assertTrue(ro.has_memory_proposals)

    def test_empty_role_name_rejected(self):
        with self.assertRaises(ValueError):
            RoleOutput(role_name="", summary="Nothing")

    def test_confidence_validation(self):
        with self.assertRaises(ValueError):
            RoleOutput(role_name="test", summary="Bad", confidence=1.1)
        with self.assertRaises(ValueError):
            RoleOutput(role_name="test", summary="Bad", confidence=-0.01)

    def test_serialization_round_trip(self):
        prov = Provenance.from_role("engineer", "tsk_ro2")
        mp = MemoryProposal.create(
            summary="Insight",
            content="Detail",
            target_domain="engineering",
            proposed_strength=0.75,
            half_life_days=21.0,
            memory_type="insight",
            provenance=prov,
        )
        original = RoleOutput(
            role_name="engineer",
            summary="Analysis complete",
            findings=["Finding 1", "Finding 2"],
            recommendations=["Rec 1"],
            uncertainties=["Uncertain about X"],
            contradictions=["Contradiction with interpreter"],
            memory_proposals=[mp],
            confidence=0.85,
            provenance=prov,
        )
        d = original.to_dict()
        restored = RoleOutput.from_dict(d)
        self.assertEqual(restored.role_name, "engineer")
        self.assertEqual(len(restored.findings), 2)
        self.assertEqual(len(restored.memory_proposals), 1)
        self.assertAlmostEqual(restored.confidence, 0.85)
        self.assertIsNotNone(restored.provenance)
        self.assertEqual(restored.provenance.source_role, "engineer")

    def test_from_dict_empty_rejected(self):
        with self.assertRaises(ValueError):
            RoleOutput.from_dict({})


# ============================================================================
# TaskPacket
# ============================================================================

class TestTaskPacket(unittest.TestCase):
    """TaskPacket — incoming request context for cognition pipeline."""

    def test_creation_defaults(self):
        tp = TaskPacket(
            workspace_id="ws_test",
            agent_id="ryuki",
            user_input="What is the meaning of life?",
        )
        self.assertTrue(tp.task_id.startswith("tsk_"))
        self.assertEqual(tp.mode, MODE_AUTO)
        self.assertEqual(tp.priority, PRIORITY_NORMAL)
        self.assertGreater(tp.timestamp, 0)

    def test_all_modes(self):
        for mode in [MODE_AUTO, MODE_ENGINEERING, MODE_STRATEGIC, MODE_IDENTITY]:
            tp = TaskPacket(
                workspace_id="ws1", agent_id="a1",
                user_input="test", mode=mode,
            )
            self.assertEqual(tp.mode, mode)

    def test_all_priorities(self):
        for priority in [PRIORITY_LOW, PRIORITY_NORMAL, PRIORITY_HIGH]:
            tp = TaskPacket(
                workspace_id="ws1", agent_id="a1",
                user_input="test", priority=priority,
            )
            self.assertEqual(tp.priority, priority)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            TaskPacket(
                workspace_id="ws1", agent_id="a1",
                user_input="test", mode="invalid",
            )

    def test_invalid_priority_rejected(self):
        with self.assertRaises(ValueError):
            TaskPacket(
                workspace_id="ws1", agent_id="a1",
                user_input="test", priority="critical",
            )

    def test_empty_workspace_rejected(self):
        with self.assertRaises(ValueError):
            TaskPacket(workspace_id="", agent_id="a1", user_input="test")

    def test_empty_agent_rejected(self):
        with self.assertRaises(ValueError):
            TaskPacket(workspace_id="ws1", agent_id="", user_input="test")

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            TaskPacket(workspace_id="ws1", agent_id="a1", user_input="")

    def test_custom_task_id_preserved(self):
        tp = TaskPacket(
            workspace_id="ws1", agent_id="a1",
            user_input="test", task_id="tsk_custom",
        )
        self.assertEqual(tp.task_id, "tsk_custom")

    def test_explicit_timestamp_preserved(self):
        tp = TaskPacket(
            workspace_id="ws1", agent_id="a1",
            user_input="test", timestamp=999,
        )
        self.assertEqual(tp.timestamp, 999)

    def test_serialization_round_trip(self):
        original = TaskPacket(
            workspace_id="ws_rt",
            agent_id="agent_rt",
            user_input="Round trip test",
            mode=MODE_STRATEGIC,
            priority=PRIORITY_HIGH,
        )
        d = original.to_dict()
        restored = TaskPacket.from_dict(d)
        self.assertEqual(restored.workspace_id, original.workspace_id)
        self.assertEqual(restored.agent_id, original.agent_id)
        self.assertEqual(restored.user_input, original.user_input)
        self.assertEqual(restored.mode, MODE_STRATEGIC)
        self.assertEqual(restored.priority, PRIORITY_HIGH)
        self.assertEqual(restored.task_id, original.task_id)
        self.assertEqual(restored.timestamp, original.timestamp)

    def test_from_dict_ignores_unknown_fields(self):
        d = {
            "workspace_id": "ws1",
            "agent_id": "a1",
            "user_input": "test",
            "unknown_field": "ignore me",
        }
        tp = TaskPacket.from_dict(d)
        self.assertEqual(tp.workspace_id, "ws1")

    def test_from_dict_empty_rejected(self):
        with self.assertRaises(ValueError):
            TaskPacket.from_dict({})
        with self.assertRaises(ValueError):
            TaskPacket.from_dict(None)


# ============================================================================
# RoutingDecision
# ============================================================================

class TestRoutingDecision(unittest.TestCase):
    """RoutingDecision — router output: roles, aperture, constraints."""

    def _make_decision(self, **overrides):
        defaults = dict(
            roles_to_activate=["interpreter", "engineer"],
            primary_domains=["research"],
            aperture=APERTURE_NARROW,
        )
        defaults.update(overrides)
        return RoutingDecision(**defaults)

    def test_creation_defaults(self):
        rd = self._make_decision()
        self.assertEqual(rd.aperture, APERTURE_NARROW)
        self.assertEqual(rd.memory_sources, ["private", "shared"])
        self.assertEqual(rd.archival_scope, SCOPE_PRIVATE)
        self.assertEqual(rd.conflict_policy, "preserve")
        self.assertFalse(rd.require_skeptic_pass)
        self.assertFalse(rd.require_drift_check)
        self.assertTrue(rd.require_archival_review)

    def test_all_apertures(self):
        for ap in [APERTURE_NARROW, APERTURE_BROAD, APERTURE_PROTECTED]:
            rd = self._make_decision(aperture=ap)
            self.assertEqual(rd.aperture, ap)

    def test_invalid_aperture_rejected(self):
        with self.assertRaises(ValueError):
            self._make_decision(aperture="wide_open")

    def test_invalid_archival_scope_rejected(self):
        with self.assertRaises(ValueError):
            self._make_decision(archival_scope="shared")

    def test_conflict_policy_locked_to_preserve(self):
        """v0.1 only supports 'preserve' — any other value is rejected."""
        with self.assertRaises(ValueError):
            self._make_decision(conflict_policy="override")

    def test_empty_roles_rejected(self):
        with self.assertRaises(ValueError):
            self._make_decision(roles_to_activate=[])

    def test_serialization_round_trip(self):
        original = self._make_decision(
            roles_to_activate=["interpreter", "engineer", "skeptic", "archivist"],
            primary_domains=["engineering", "meta"],
            aperture=APERTURE_PROTECTED,
            archival_scope=SCOPE_NONE,
            require_skeptic_pass=True,
            require_drift_check=True,
        )
        d = original.to_dict()
        restored = RoutingDecision.from_dict(d)
        self.assertEqual(restored.roles_to_activate, original.roles_to_activate)
        self.assertEqual(restored.primary_domains, original.primary_domains)
        self.assertEqual(restored.aperture, APERTURE_PROTECTED)
        self.assertEqual(restored.archival_scope, SCOPE_NONE)
        self.assertTrue(restored.require_skeptic_pass)
        self.assertTrue(restored.require_drift_check)

    def test_from_dict_empty_rejected(self):
        with self.assertRaises(ValueError):
            RoutingDecision.from_dict({})


# ============================================================================
# ReintegrationResult
# ============================================================================

class TestReintegrationResult(unittest.TestCase):
    """ReintegrationResult — merged output, Invariant C (disagreement preserved)."""

    def test_creation_defaults(self):
        rr = ReintegrationResult(final_answer="The answer is 42.")
        self.assertEqual(rr.merged_findings, [])
        self.assertEqual(rr.dissent, [])
        self.assertEqual(rr.role_outputs, [])
        self.assertEqual(rr.all_memory_proposals, [])
        self.assertEqual(rr.governance_rejections, [])
        self.assertIsNone(rr.drift_report)
        self.assertIsNone(rr.memory_effects)
        self.assertFalse(rr.has_dissent)
        self.assertFalse(rr.has_governance_rejections)

    def test_with_dissent(self):
        dissent_entry = {
            "role_a": "interpreter",
            "role_b": "engineer",
            "claim_a": "This is creative work",
            "claim_b": "This is engineering work",
            "topic": "task classification",
        }
        rr = ReintegrationResult(
            final_answer="Compromise answer",
            dissent=[dissent_entry],
        )
        self.assertTrue(rr.has_dissent)
        self.assertEqual(len(rr.dissent), 1)

    def test_with_governance_rejections(self):
        rejection = {"proposal_id": "prop_001", "reason": "drift too high"}
        rr = ReintegrationResult(
            final_answer="Answer with rejected proposals",
            governance_rejections=[rejection],
        )
        self.assertTrue(rr.has_governance_rejections)

    def test_full_serialization_round_trip(self):
        """Round-trip with nested RoleOutputs, MemoryProposals, and DriftReport."""
        prov = Provenance.from_role("engineer", "tsk_rr1")
        mp = MemoryProposal.create(
            summary="Store insight",
            content="Detail",
            target_domain="research",
            proposed_strength=0.7,
            half_life_days=14.0,
            memory_type="insight",
            provenance=prov,
        )
        ro = RoleOutput(
            role_name="engineer",
            summary="Analysis done",
            findings=["Found A"],
            confidence=0.9,
            provenance=prov,
        )
        dr = DriftReport(total_drift=0.15, domain_shift=0.05, motif_shift=0.10)

        original = ReintegrationResult(
            final_answer="Comprehensive answer",
            merged_findings=["Finding from merge"],
            dissent=[{
                "role_a": "interpreter",
                "role_b": "skeptic",
                "claim_a": "X",
                "claim_b": "Y",
                "topic": "test",
            }],
            role_outputs=[ro],
            all_memory_proposals=[mp],
            governance_rejections=[{"proposal_id": "p1", "reason": "test"}],
            drift_report=dr,
            memory_effects={"approved": [], "rejected": [{"id": "p1"}]},
        )

        d = original.to_dict()
        restored = ReintegrationResult.from_dict(d)

        self.assertEqual(restored.final_answer, "Comprehensive answer")
        self.assertEqual(len(restored.merged_findings), 1)
        self.assertTrue(restored.has_dissent)
        self.assertTrue(restored.has_governance_rejections)

        # Nested objects restored
        self.assertEqual(len(restored.role_outputs), 1)
        self.assertEqual(restored.role_outputs[0].role_name, "engineer")
        self.assertEqual(len(restored.all_memory_proposals), 1)
        self.assertEqual(restored.all_memory_proposals[0].target_domain, "research")

        # DriftReport restored
        self.assertIsNotNone(restored.drift_report)
        self.assertAlmostEqual(restored.drift_report.total_drift, 0.15)
        self.assertEqual(restored.drift_report.zone, "green")

    def test_from_dict_empty_rejected(self):
        with self.assertRaises(ValueError):
            ReintegrationResult.from_dict({})


if __name__ == "__main__":
    unittest.main()
