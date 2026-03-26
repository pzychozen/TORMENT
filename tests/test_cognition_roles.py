"""
tests/test_cognition_roles.py — Role executors (Patch 3)

Tests for:
    - RoleBase: abstract contract, provenance enforcement
    - Interpreter: intent classification, key phrase extraction, memory surfacing
    - Engineer: action step building, interpreter consumption, proposal generation
    - Skeptic: contradiction detection, proposal safety, drift awareness, contamination
    - Archivist: proposal review, invariant enforcement, drift gating
    - Full sequential pipeline: interpreter → engineer → skeptic → archivist

See AGENT_SPINE_PLAN.md §7 and §11 Patch 3.
"""
from __future__ import annotations

import os
import sys
import unittest
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cognition.task_models import TaskPacket, MODE_AUTO, MODE_ENGINEERING, MODE_IDENTITY
from cognition.apertures import MemoryContext, APERTURE_CONFIGS, build_memory_context
from schemas.role_output import RoleOutput
from schemas.provenance import (
    Provenance,
    SOURCE_ROLE_OUTPUT,
    STATUS_UNVERIFIED,
    STATUS_SKEPTIC_PASSED,
    STATUS_SKEPTIC_FLAGGED,
)
from schemas.memory_proposal import MemoryProposal
from roles.base import RoleBase
from roles.interpreter import Interpreter
from roles.engineer import Engineer
from roles.skeptic import Skeptic
from roles.archivist import Archivist
from roles import ROLE_REGISTRY, ROLE_EXECUTION_ORDER


# ============================================================================
# Helpers
# ============================================================================

def _make_task(user_input="Implement the router module", mode=MODE_AUTO, **kw):
    defaults = dict(workspace_id="ws_test", agent_id="agent_test")
    defaults.update(kw)
    return TaskPacket(user_input=user_input, mode=mode, **defaults)


def _make_memory_context(aperture="narrow", private=None, shared=None,
                         character=None, drift=None, domain_id=None):
    config = APERTURE_CONFIGS[aperture]
    return MemoryContext(
        aperture_name=aperture,
        config=config,
        private_memories=private or [],
        shared_memories=shared or [],
        character_context=character,
        drift_snapshot=drift,
        domain_id=domain_id or "research",
        query_text="test query",
    )


def _make_memories(n):
    return [{"id": i, "text": f"Memory about topic {i}", "score": 0.9 - i * 0.05}
            for i in range(n)]


def _make_proposal(strength=0.5, half_life=14.0, mtype="episode",
                   depth=0, task_id="tsk_test"):
    prov = Provenance.from_role("engineer", task_id, confidence=0.7)
    prov.derivation_depth = depth
    return MemoryProposal.create(
        summary="Test proposal",
        content="Test content",
        target_domain="research",
        proposed_strength=strength,
        half_life_days=half_life,
        memory_type=mtype,
        provenance=prov,
    )


# ============================================================================
# RoleBase
# ============================================================================

class TestRoleBase(unittest.TestCase):
    """RoleBase abstract contract."""

    def test_cannot_instantiate_directly(self):
        with self.assertRaises(TypeError):
            RoleBase()

    def test_run_attaches_provenance_if_missing(self):
        """If execute() returns output without provenance, run() adds it."""

        class BareRole(RoleBase):
            name = "bare"

            def execute(self, task, memory_context, prior_outputs):
                return RoleOutput(
                    role_name=self.name,
                    summary="No provenance attached",
                )

        role = BareRole()
        task = _make_task()
        ctx = _make_memory_context()
        out = role.run(task, ctx, [])
        self.assertIsNotNone(out.provenance)
        self.assertEqual(out.provenance.source_role, "bare")
        self.assertEqual(out.provenance.source_type, SOURCE_ROLE_OUTPUT)

    def test_run_preserves_existing_provenance(self):
        """If execute() already attached provenance, run() doesn't overwrite."""

        class GoodRole(RoleBase):
            name = "good"

            def execute(self, task, memory_context, prior_outputs):
                prov = Provenance.from_role("good", task.task_id, confidence=0.99)
                return RoleOutput(
                    role_name=self.name,
                    summary="Has provenance",
                    provenance=prov,
                )

        role = GoodRole()
        task = _make_task()
        ctx = _make_memory_context()
        out = role.run(task, ctx, [])
        self.assertAlmostEqual(out.provenance.confidence, 0.99)

    def test_all_roles_in_registry(self):
        self.assertEqual(set(ROLE_REGISTRY.keys()),
                         {"interpreter", "engineer", "skeptic", "archivist"})

    def test_execution_order(self):
        self.assertEqual(ROLE_EXECUTION_ORDER,
                         ["interpreter", "engineer", "skeptic", "archivist"])


# ============================================================================
# Interpreter
# ============================================================================

class TestInterpreter(unittest.TestCase):
    """Interpreter role — intent classification and memory surfacing."""

    def setUp(self):
        self.role = Interpreter()

    def test_basic_execution(self):
        task = _make_task("What is the meaning of life?")
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        self.assertEqual(out.role_name, "interpreter")
        self.assertIsNotNone(out.provenance)
        self.assertTrue(len(out.findings) > 0)

    def test_classifies_question(self):
        task = _make_task("What should we focus on?")
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        found_intent = [f for f in out.findings if "Classified intent:" in f]
        self.assertTrue(len(found_intent) > 0)
        self.assertIn("question", found_intent[0].lower())

    def test_classifies_action(self):
        task = _make_task("Implement the new router module")
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        found_intent = [f for f in out.findings if "Classified intent:" in f]
        self.assertTrue(len(found_intent) > 0)
        self.assertIn("action", found_intent[0].lower())

    def test_classifies_reflection(self):
        task = _make_task("Who am I really? What are my values?")
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        found_intent = [f for f in out.findings if "Classified intent:" in f]
        self.assertTrue(len(found_intent) > 0)
        self.assertIn("reflection", found_intent[0].lower())

    def test_surfaces_memories(self):
        mems = _make_memories(5)
        ctx = _make_memory_context(private=mems)
        task = _make_task()
        out = self.role.run(task, ctx, [])
        mem_findings = [f for f in out.findings if "Relevant memory:" in f]
        self.assertTrue(len(mem_findings) > 0)

    def test_notes_missing_memory(self):
        ctx = _make_memory_context()
        task = _make_task()
        out = self.role.run(task, ctx, [])
        self.assertTrue(any("No memory context" in u for u in out.uncertainties))

    def test_extracts_quoted_phrases(self):
        task = _make_task('Implement "memory router" for the system')
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        key_findings = [f for f in out.findings if "Key phrases:" in f]
        self.assertTrue(len(key_findings) > 0)
        self.assertIn("memory router", key_findings[0])

    def test_confidence_higher_with_phrases(self):
        task_with = _make_task('Implement "router" module')
        task_without = _make_task("hello")
        ctx = _make_memory_context()
        out_with = self.role.run(task_with, ctx, [])
        out_without = self.role.run(task_without, ctx, [])
        self.assertGreater(out_with.confidence, out_without.confidence)


# ============================================================================
# Engineer
# ============================================================================

class TestEngineer(unittest.TestCase):
    """Engineer role — action planning and interpreter consumption."""

    def setUp(self):
        self.role = Engineer()

    def test_basic_execution(self):
        task = _make_task("Build a new API endpoint")
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        self.assertEqual(out.role_name, "engineer")
        self.assertIsNotNone(out.provenance)
        self.assertTrue(len(out.recommendations) > 0)

    def test_consumes_interpreter_output(self):
        task = _make_task()
        ctx = _make_memory_context()
        interp_out = Interpreter().run(task, ctx, [])
        out = self.role.run(task, ctx, [interp_out])
        consumed = [f for f in out.findings if "[from interpreter]" in f]
        self.assertTrue(len(consumed) > 0)

    def test_notes_missing_interpreter(self):
        task = _make_task()
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        self.assertTrue(any("No interpreter" in u for u in out.uncertainties))

    def test_produces_action_steps(self):
        task = _make_task("Build the memory router then test it")
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        step_recs = [r for r in out.recommendations if r.startswith("Step")]
        self.assertTrue(len(step_recs) > 0)

    def test_proposes_memory_for_large_tasks(self):
        # Enough words to be "medium" scope + steps
        task = _make_task(
            "Build the new memory router module then add tests "
            "then integrate with the fabric layer and verify all edge cases"
        )
        ctx = _make_memory_context(private=_make_memories(3))
        interp_out = Interpreter().run(task, ctx, [])
        out = self.role.run(task, ctx, [interp_out])
        self.assertTrue(out.has_memory_proposals or len(out.recommendations) > 2)

    def test_scope_assessment(self):
        short_task = _make_task("Fix bug")
        long_task = _make_task(
            "We need to completely redesign the memory architecture "
            "including the retrieval assembler, the compression pipeline, "
            "the SRG engine integration, and all downstream consumers "
            "while maintaining backward compatibility with existing data"
        )
        ctx = _make_memory_context()
        out_short = self.role.run(short_task, ctx, [])
        out_long = self.role.run(long_task, ctx, [])
        short_scope = [f for f in out_short.findings if "Scope assessment:" in f]
        long_scope = [f for f in out_long.findings if "Scope assessment:" in f]
        self.assertTrue(len(short_scope) > 0)
        self.assertTrue(len(long_scope) > 0)


# ============================================================================
# Skeptic
# ============================================================================

class TestSkeptic(unittest.TestCase):
    """Skeptic role — flags, contradictions, contamination, drift checks."""

    def setUp(self):
        self.role = Skeptic()

    def test_basic_execution_no_priors(self):
        task = _make_task()
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        self.assertEqual(out.role_name, "skeptic")
        self.assertIsNotNone(out.provenance)
        self.assertTrue(any("No prior" in u for u in out.uncertainties))

    def test_passes_clean_outputs(self):
        task = _make_task()
        ctx = _make_memory_context()
        clean_output = RoleOutput(
            role_name="interpreter",
            summary="Clean analysis",
            confidence=0.9,
            provenance=Provenance.from_role("interpreter", task.task_id),
        )
        out = self.role.run(task, ctx, [clean_output])
        self.assertIn(STATUS_SKEPTIC_PASSED, out.provenance.verification_status)

    def test_flags_low_confidence(self):
        task = _make_task()
        ctx = _make_memory_context()
        low_conf = RoleOutput(
            role_name="engineer",
            summary="Low confidence analysis",
            confidence=0.3,
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [low_conf])
        self.assertTrue(any("LOW CONFIDENCE" in f for f in out.findings))

    def test_detects_contradiction(self):
        task = _make_task()
        ctx = _make_memory_context()
        out_a = RoleOutput(
            role_name="interpreter",
            summary="Should proceed",
            recommendations=["We should proceed with the plan"],
            provenance=Provenance.from_role("interpreter", task.task_id),
        )
        out_b = RoleOutput(
            role_name="engineer",
            summary="Should not proceed",
            recommendations=["We should not proceed — too risky"],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [out_a, out_b])
        self.assertTrue(len(out.contradictions) > 0)

    def test_flags_proposal_missing_provenance(self):
        task = _make_task()
        ctx = _make_memory_context()
        mp = MemoryProposal(
            proposal_id="test_prop",
            summary="Bad proposal",
            content="No provenance",
            target_domain="research",
            proposed_strength=0.5,
            half_life_days=14.0,
            memory_type="episode",
            provenance=None,  # missing!
        )
        prior = RoleOutput(
            role_name="engineer",
            summary="Has bad proposal",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        self.assertTrue(any("Missing provenance" in f for f in out.findings))

    def test_flags_high_strength_proposal(self):
        task = _make_task()
        ctx = _make_memory_context()
        mp = _make_proposal(strength=0.95)
        prior = RoleOutput(
            role_name="engineer",
            summary="Has high strength proposal",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        self.assertTrue(any("high proposed_strength" in f.lower() for f in out.findings))

    def test_drift_alert_in_protected(self):
        task = _make_task(mode=MODE_IDENTITY)
        drift = {"total_drift": 0.40, "zone": "red"}
        ctx = _make_memory_context(aperture="protected", drift=drift)
        out = self.role.run(task, ctx, [])
        self.assertTrue(any("DRIFT ALERT" in f for f in out.findings))

    def test_identity_contamination_check(self):
        task = _make_task("Rewrite my personality", mode=MODE_IDENTITY)
        ctx = _make_memory_context(aperture="protected")
        prior = RoleOutput(
            role_name="interpreter",
            summary="Wants to rewrite identity",
            recommendations=["Rewrite the core personality completely"],
            provenance=Provenance.from_role("interpreter", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        self.assertTrue(any("CONTAMINATION" in f for f in out.findings))

    def test_skeptic_verdict_in_provenance(self):
        task = _make_task()
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        self.assertIn(out.provenance.verification_status,
                      [STATUS_SKEPTIC_PASSED, STATUS_SKEPTIC_FLAGGED])


# ============================================================================
# Archivist
# ============================================================================

class TestArchivist(unittest.TestCase):
    """Archivist role — proposal review and invariant enforcement."""

    def setUp(self):
        self.role = Archivist()

    def test_basic_execution_no_proposals(self):
        task = _make_task()
        ctx = _make_memory_context()
        out = self.role.run(task, ctx, [])
        self.assertEqual(out.role_name, "archivist")
        self.assertTrue(any("No memory proposals" in f for f in out.findings))

    def test_approves_clean_proposal(self):
        task = _make_task()
        ctx = _make_memory_context()
        mp = _make_proposal(strength=0.5, task_id=task.task_id)
        prior = RoleOutput(
            role_name="engineer",
            summary="Has proposal",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        approved = [p for p in out.memory_proposals if p.is_approved]
        self.assertEqual(len(approved), 1)

    def test_rejects_missing_provenance(self):
        task = _make_task()
        ctx = _make_memory_context()
        mp = MemoryProposal(
            proposal_id="no_prov",
            summary="No provenance",
            content="Content",
            target_domain="research",
            proposed_strength=0.5,
            half_life_days=14.0,
            memory_type="episode",
            provenance=None,
        )
        prior = RoleOutput(
            role_name="engineer",
            summary="Bad proposal",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        rejected = [p for p in out.memory_proposals if p.is_rejected]
        self.assertEqual(len(rejected), 1)
        self.assertIn("Invariant B", rejected[0].rejection_reason)

    def test_rejects_under_drift_block(self):
        task = _make_task()
        drift = {"total_drift": 0.55, "governance_breach": False}
        ctx = _make_memory_context(aperture="protected", drift=drift)
        mp = _make_proposal(strength=0.5, task_id=task.task_id)
        prior = RoleOutput(
            role_name="engineer",
            summary="Proposal during drift",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        rejected = [p for p in out.memory_proposals if p.is_rejected]
        self.assertEqual(len(rejected), 1)
        self.assertIn("Drift block", rejected[0].rejection_reason)

    def test_rejects_high_strength_when_skeptic_flagged(self):
        task = _make_task()
        ctx = _make_memory_context()
        mp = _make_proposal(strength=0.85, task_id=task.task_id)

        skeptic_prov = Provenance.from_role("skeptic", task.task_id)
        skeptic_prov.verification_status = STATUS_SKEPTIC_FLAGGED
        skeptic_out = RoleOutput(
            role_name="skeptic",
            summary="Flagged issues",
            findings=["LOW CONFIDENCE: something"],
            provenance=skeptic_prov,
        )
        engineer_out = RoleOutput(
            role_name="engineer",
            summary="Has proposal",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [engineer_out, skeptic_out])
        rejected = [p for p in out.memory_proposals if p.is_rejected]
        self.assertTrue(len(rejected) > 0)

    def test_rejects_deep_derivation_high_strength(self):
        task = _make_task()
        ctx = _make_memory_context()
        mp = _make_proposal(strength=0.8, depth=5, task_id=task.task_id)
        prior = RoleOutput(
            role_name="engineer",
            summary="Deep derivation",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        rejected = [p for p in out.memory_proposals if p.is_rejected]
        self.assertTrue(len(rejected) > 0)
        self.assertIn("Invariant G", rejected[0].rejection_reason)

    def test_rejects_near_max_episode(self):
        task = _make_task()
        ctx = _make_memory_context()
        mp = _make_proposal(strength=0.96, mtype="episode", task_id=task.task_id)
        prior = RoleOutput(
            role_name="engineer",
            summary="Max strength episode",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        rejected = [p for p in out.memory_proposals if p.is_rejected]
        self.assertTrue(len(rejected) > 0)

    def test_allows_low_strength_in_yellow_drift(self):
        task = _make_task()
        drift = {"total_drift": 0.25}
        ctx = _make_memory_context(aperture="narrow", drift=drift)
        mp = _make_proposal(strength=0.4, task_id=task.task_id)
        prior = RoleOutput(
            role_name="engineer",
            summary="Low strength ok",
            memory_proposals=[mp],
            provenance=Provenance.from_role("engineer", task.task_id),
        )
        out = self.role.run(task, ctx, [prior])
        approved = [p for p in out.memory_proposals if p.is_approved]
        self.assertEqual(len(approved), 1)


# ============================================================================
# Full Sequential Pipeline
# ============================================================================

class TestFullPipeline(unittest.TestCase):
    """End-to-end: interpreter → engineer → skeptic → archivist."""

    def test_engineering_pipeline(self):
        task = _make_task("Implement the new router module")
        ctx = _make_memory_context(private=_make_memories(5))

        outputs: List[RoleOutput] = []

        # 1. Interpreter
        interp = Interpreter()
        interp_out = interp.run(task, ctx, outputs)
        self.assertEqual(interp_out.role_name, "interpreter")
        self.assertIsNotNone(interp_out.provenance)
        outputs.append(interp_out)

        # 2. Engineer
        eng = Engineer()
        eng_out = eng.run(task, ctx, outputs)
        self.assertEqual(eng_out.role_name, "engineer")
        self.assertIsNotNone(eng_out.provenance)
        outputs.append(eng_out)

        # 3. Skeptic
        skep = Skeptic()
        skep_out = skep.run(task, ctx, outputs)
        self.assertEqual(skep_out.role_name, "skeptic")
        self.assertIsNotNone(skep_out.provenance)
        outputs.append(skep_out)

        # 4. Archivist
        arch = Archivist()
        arch_out = arch.run(task, ctx, outputs)
        self.assertEqual(arch_out.role_name, "archivist")
        self.assertIsNotNone(arch_out.provenance)

        # All outputs have provenance (Invariant B)
        for out in outputs + [arch_out]:
            self.assertIsNotNone(out.provenance)
            self.assertEqual(out.provenance.source_type, SOURCE_ROLE_OUTPUT)

    def test_identity_pipeline_with_drift(self):
        task = _make_task("Who am I? Reflect on my identity.", mode=MODE_IDENTITY)
        drift = {"total_drift": 0.40}
        ctx = _make_memory_context(
            aperture="protected",
            private=_make_memories(3),
            character={"name": "Ryuki", "seed": "test"},
            drift=drift,
        )

        outputs: List[RoleOutput] = []

        # Interpreter
        interp_out = Interpreter().run(task, ctx, outputs)
        outputs.append(interp_out)

        # No engineer in identity route — skip to skeptic
        skep_out = Skeptic().run(task, ctx, outputs)
        outputs.append(skep_out)

        # Skeptic should flag drift
        self.assertTrue(any("DRIFT" in f for f in skep_out.findings))

        # Archivist
        arch_out = Archivist().run(task, ctx, outputs)

        # Any proposals under high drift should be rejected
        if arch_out.memory_proposals:
            for mp in arch_out.memory_proposals:
                if mp.proposed_strength > 0.7:
                    self.assertTrue(mp.is_rejected)


if __name__ == "__main__":
    unittest.main()
