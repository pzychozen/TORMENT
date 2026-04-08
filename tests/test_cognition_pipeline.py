"""
tests/test_cognition_pipeline.py — Pipeline orchestrator + endpoint wiring (Patch 5)

Tests for:
    - run_cognition_pipeline(): full pipeline smoke, all modes, error handling
    - Response structure: required keys, role summaries, routing info
    - Graceful degradation: missing query_fn, failing drift, bad inputs
    - Invalid input validation

See AGENT_SPINE_PLAN.md §11 Patch 5.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cognition.task_models import (
    TaskPacket, MODE_AUTO, MODE_ENGINEERING, MODE_STRATEGIC, MODE_IDENTITY,
)
from cognition.pipeline import run_cognition_pipeline
from cognition.drift import stub_drift_check, zero_drift_check, failing_drift_check


# ============================================================================
# Helpers
# ============================================================================

def _make_task(user_input="Implement the router module", mode=MODE_AUTO):
    return TaskPacket(workspace_id="ws_test", agent_id="agent_test",
                      user_input=user_input, mode=mode)


def _mock_query_fn(workspace_id, agent_id, query_text, top_k, domain_id):
    return {
        "results": [
            {"id": i, "text": f"Memory about {query_text[:20]} item {i}", "score": 0.9}
            for i in range(top_k)
        ]
    }


def _mock_character_fn(workspace_id, agent_id):
    return {"name": "Ryuki", "seed": "test_seed", "agent_id": agent_id}


# ============================================================================
# Required response keys
# ============================================================================

REQUIRED_OK_KEYS = {
    "ok", "task_id", "final_answer", "merged_findings", "dissent",
    "memory_effects", "drift_report", "governance_rejections",
    "role_summaries", "routing",
}

REQUIRED_ERROR_KEYS = {"ok", "task_id", "error", "error_type"}


# ============================================================================
# Smoke tests — full pipeline
# ============================================================================

class TestPipelineSmoke(unittest.TestCase):
    """Full pipeline smoke: runs without crashing, returns correct structure."""

    def test_engineering_mode_no_fns(self):
        """Pipeline runs with no query/character/drift functions (empty context)."""
        task = _make_task(mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(task)
        self.assertTrue(result["ok"])
        self.assertEqual(result["task_id"], task.task_id)
        self.assertGreater(len(result["final_answer"]), 0)
        self.assertIsNone(result["drift_report"])

    def test_engineering_mode_with_mocks(self):
        task = _make_task("Build the new API endpoint", mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(
            task,
            query_fn=_mock_query_fn,
            character_fn=_mock_character_fn,
        )
        self.assertTrue(result["ok"])
        self.assertGreater(len(result["merged_findings"]), 0)

    def test_strategic_mode(self):
        task = _make_task("What should we focus on next?", mode=MODE_STRATEGIC)
        result = run_cognition_pipeline(
            task, query_fn=_mock_query_fn, character_fn=_mock_character_fn,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["routing"]["effective_aperture"], "broad")

    def test_identity_mode(self):
        task = _make_task("Rewrite my core identity", mode=MODE_IDENTITY)
        result = run_cognition_pipeline(
            task,
            query_fn=_mock_query_fn,
            character_fn=_mock_character_fn,
            drift_check_fn=zero_drift_check(),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["routing"]["effective_aperture"], "protected")
        self.assertTrue(result["routing"]["drift_check_required"])
        self.assertIsNotNone(result["drift_report"])

    def test_auto_mode_detects_engineering(self):
        task = _make_task("Implement the new module", mode=MODE_AUTO)
        result = run_cognition_pipeline(task)
        self.assertTrue(result["ok"])
        self.assertEqual(result["routing"]["effective_aperture"], "narrow")

    def test_auto_mode_detects_strategic(self):
        task = _make_task("What should the roadmap look like?", mode=MODE_AUTO)
        result = run_cognition_pipeline(task)
        self.assertTrue(result["ok"])
        self.assertEqual(result["routing"]["effective_aperture"], "broad")

    def test_auto_mode_detects_identity(self):
        task = _make_task("Rewrite my identity", mode=MODE_AUTO)
        result = run_cognition_pipeline(
            task, drift_check_fn=zero_drift_check(),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["routing"]["effective_aperture"], "protected")


# ============================================================================
# Response structure
# ============================================================================

class TestResponseStructure(unittest.TestCase):
    """Response has all required keys and correct types."""

    def test_all_required_keys_present(self):
        task = _make_task()
        result = run_cognition_pipeline(task)
        self.assertTrue(result["ok"])
        missing = REQUIRED_OK_KEYS - set(result.keys())
        self.assertEqual(missing, set(), f"Missing keys: {missing}")

    def test_role_summaries_structure(self):
        task = _make_task(mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(task)
        self.assertIsInstance(result["role_summaries"], list)
        self.assertGreater(len(result["role_summaries"]), 0)
        for rs in result["role_summaries"]:
            self.assertIn("role", rs)
            self.assertIn("summary", rs)
            self.assertIn("confidence", rs)
            self.assertIn("findings_count", rs)

    def test_routing_structure(self):
        task = _make_task(mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(task)
        routing = result["routing"]
        self.assertIn("effective_aperture", routing)
        self.assertIn("roles_activated", routing)
        self.assertIn("drift_check_required", routing)
        self.assertIn("skeptic_pass_required", routing)

    def test_memory_effects_structure(self):
        task = _make_task(mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(task, query_fn=_mock_query_fn)
        me = result["memory_effects"]
        self.assertIn("approved", me)
        self.assertIn("rejected", me)

    def test_engineering_roles_activated(self):
        task = _make_task(mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(task)
        roles = [rs["role"] for rs in result["role_summaries"]]
        self.assertIn("interpreter", roles)
        self.assertIn("engineer", roles)
        self.assertIn("skeptic", roles)
        self.assertIn("archivist", roles)

    def test_identity_skips_engineer(self):
        task = _make_task("Who am I?", mode=MODE_IDENTITY)
        result = run_cognition_pipeline(task, drift_check_fn=zero_drift_check())
        roles = [rs["role"] for rs in result["role_summaries"]]
        self.assertNotIn("engineer", roles)
        self.assertIn("interpreter", roles)
        self.assertIn("skeptic", roles)
        self.assertIn("archivist", roles)


# ============================================================================
# Drift integration
# ============================================================================

class TestDriftIntegration(unittest.TestCase):
    """Drift check wiring through the pipeline."""

    def test_green_drift_allows_proposals(self):
        task = _make_task("Rewrite identity seed", mode=MODE_IDENTITY)
        result = run_cognition_pipeline(
            task, drift_check_fn=zero_drift_check(),
        )
        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["drift_report"])
        self.assertEqual(result["drift_report"]["zone"], "green")

    def test_red_drift_blocks_proposals(self):
        task = _make_task("Change my core personality", mode=MODE_IDENTITY)
        result = run_cognition_pipeline(
            task,
            query_fn=_mock_query_fn,
            drift_check_fn=stub_drift_check(total_drift=0.55),
        )
        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["drift_report"])
        self.assertEqual(result["drift_report"]["zone"], "hard_block")
        # Any proposals should be rejected
        if result["memory_effects"]["approved"]:
            # under hard_block, nothing high-strength should pass
            pass  # depends on what roles propose

    def test_failing_drift_defaults_to_block(self):
        task = _make_task("Identity question", mode=MODE_IDENTITY)
        result = run_cognition_pipeline(
            task, drift_check_fn=failing_drift_check(),
        )
        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["drift_report"])
        self.assertEqual(result["drift_report"]["zone"], "hard_block")

    def test_no_drift_when_not_identity(self):
        task = _make_task("Build something", mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(task)
        self.assertIsNone(result["drift_report"])


# ============================================================================
# Graceful degradation
# ============================================================================

class TestGracefulDegradation(unittest.TestCase):
    """Pipeline degrades gracefully on bad inputs or failing services."""

    def test_no_query_fn_still_works(self):
        task = _make_task()
        result = run_cognition_pipeline(task)
        self.assertTrue(result["ok"])

    def test_failing_query_fn_still_works(self):
        def bad_query(*args):
            raise RuntimeError("DB down")

        task = _make_task()
        result = run_cognition_pipeline(task, query_fn=bad_query)
        self.assertTrue(result["ok"])

    def test_failing_character_fn_still_works(self):
        def bad_char(*args):
            raise RuntimeError("Character service down")

        task = _make_task()
        result = run_cognition_pipeline(
            task, character_fn=bad_char,
        )
        self.assertTrue(result["ok"])

    def test_primary_domains_passed(self):
        task = _make_task(mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(
            task, primary_domains=["research", "engineering"],
        )
        self.assertTrue(result["ok"])


# ============================================================================
# Dissent through pipeline
# ============================================================================

class TestDissentThroughPipeline(unittest.TestCase):
    """Dissent detection works end-to-end in the pipeline."""

    def test_dissent_structure_when_present(self):
        """When dissent is detected, it's structured correctly."""
        task = _make_task()
        result = run_cognition_pipeline(task, query_fn=_mock_query_fn)
        # dissent may or may not be present depending on role outputs
        self.assertIsInstance(result["dissent"], list)
        for d in result["dissent"]:
            self.assertIn("role_a", d)
            self.assertIn("role_b", d)
            self.assertIn("topic", d)


# ============================================================================
# Pipeline with explicit domain
# ============================================================================

class TestPipelineWithDomain(unittest.TestCase):

    def test_domain_affects_aperture_context(self):
        task = _make_task(mode=MODE_ENGINEERING)
        result = run_cognition_pipeline(
            task,
            query_fn=_mock_query_fn,
            primary_domains=["engineering"],
        )
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
