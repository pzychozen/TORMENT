"""
tests/test_cognition_router.py — Deterministic router + aperture builder (Patch 2)

Tests for:
    - Mode detection: keyword matching for identity, strategic, engineering, auto
    - Route function: correct roles, aperture, drift/skeptic flags per mode
    - Aperture config: top_k values, character modes, depth
    - Memory context builder: mock query integration, error resilience
    - Serialization round-trips for MemoryContext

See AGENT_SPINE_PLAN.md §6 (router policy), §8 (aperture builder), §11 Patch 2.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cognition.router import (
    detect_mode,
    route,
    _ROLES_ENGINEERING,
    _ROLES_STRATEGIC,
    _ROLES_IDENTITY,
)
from cognition.task_models import (
    TaskPacket,
    MODE_AUTO,
    MODE_ENGINEERING,
    MODE_STRATEGIC,
    MODE_IDENTITY,
    APERTURE_NARROW,
    APERTURE_BROAD,
    APERTURE_PROTECTED,
)
from cognition.apertures import (
    MemoryContext,
    APERTURE_CONFIGS,
    get_config,
    build_memory_context,
)


# ============================================================================
# detect_mode — keyword matching
# ============================================================================

class TestDetectMode(unittest.TestCase):
    """Mode detection must correctly classify user input by keyword."""

    # --- Identity keywords (highest priority) ---

    def test_identity_keyword_identity(self):
        self.assertEqual(detect_mode("Tell me about my identity"), MODE_IDENTITY)

    def test_identity_keyword_rewrite(self):
        self.assertEqual(detect_mode("I want to rewrite my core values"), MODE_IDENTITY)

    def test_identity_keyword_seed(self):
        self.assertEqual(detect_mode("Update the character seed"), MODE_IDENTITY)

    def test_identity_keyword_who_am_i(self):
        self.assertEqual(detect_mode("who am i really?"), MODE_IDENTITY)

    def test_identity_keyword_collective_submission(self):
        self.assertEqual(detect_mode("Prepare collective submission"), MODE_IDENTITY)

    def test_identity_keyword_change_personality(self):
        self.assertEqual(detect_mode("I want to change personality traits"), MODE_IDENTITY)

    def test_identity_keyword_governance(self):
        self.assertEqual(detect_mode("Review the governance policy"), MODE_IDENTITY)

    def test_identity_keyword_drift(self):
        self.assertEqual(detect_mode("Check my drift levels"), MODE_IDENTITY)

    def test_identity_keyword_persona(self):
        self.assertEqual(detect_mode("Define my persona"), MODE_IDENTITY)

    # --- Strategic keywords ---

    def test_strategic_keyword_what_should(self):
        self.assertEqual(detect_mode("What should we focus on?"), MODE_STRATEGIC)

    def test_strategic_keyword_roadmap(self):
        self.assertEqual(detect_mode("Show me the roadmap"), MODE_STRATEGIC)

    def test_strategic_keyword_future(self):
        self.assertEqual(detect_mode("Think about the future"), MODE_STRATEGIC)

    def test_strategic_keyword_next_step(self):
        self.assertEqual(detect_mode("What's the next step?"), MODE_STRATEGIC)

    def test_strategic_keyword_evolve(self):
        self.assertEqual(detect_mode("How should the system evolve?"), MODE_STRATEGIC)

    def test_strategic_keyword_direction(self):
        self.assertEqual(detect_mode("What direction should we take?"), MODE_STRATEGIC)

    def test_strategic_keyword_what_next(self):
        self.assertEqual(detect_mode("What next for the project?"), MODE_STRATEGIC)

    # --- Engineering keywords ---

    def test_engineering_keyword_implement(self):
        self.assertEqual(detect_mode("Implement the router module"), MODE_ENGINEERING)

    def test_engineering_keyword_fix(self):
        self.assertEqual(detect_mode("Fix the broken test"), MODE_ENGINEERING)

    def test_engineering_keyword_build(self):
        self.assertEqual(detect_mode("Build the aperture system"), MODE_ENGINEERING)

    def test_engineering_keyword_refactor(self):
        self.assertEqual(detect_mode("Refactor the memory pipeline"), MODE_ENGINEERING)

    def test_engineering_keyword_endpoint(self):
        self.assertEqual(detect_mode("Add a new endpoint"), MODE_ENGINEERING)

    def test_engineering_keyword_code(self):
        self.assertEqual(detect_mode("Write code for the parser"), MODE_ENGINEERING)

    def test_engineering_keyword_debug(self):
        self.assertEqual(detect_mode("Debug the ingest path"), MODE_ENGINEERING)

    # --- Auto fallback ---

    def test_auto_no_keywords(self):
        self.assertEqual(detect_mode("Hello there"), MODE_AUTO)

    def test_auto_empty_input(self):
        self.assertEqual(detect_mode(""), MODE_AUTO)

    def test_auto_whitespace_only(self):
        self.assertEqual(detect_mode("   "), MODE_AUTO)

    def test_auto_generic_question(self):
        self.assertEqual(detect_mode("How are you doing today?"), MODE_AUTO)

    # --- Priority: identity > strategic > engineering ---

    def test_identity_beats_engineering(self):
        """'rewrite' is identity, 'code' is engineering — identity wins."""
        self.assertEqual(detect_mode("Rewrite the code for the core"), MODE_IDENTITY)

    def test_identity_beats_strategic(self):
        """'identity' is identity, 'future' is strategic — identity wins."""
        self.assertEqual(detect_mode("What's the future of my identity?"), MODE_IDENTITY)

    def test_strategic_beats_engineering(self):
        """'roadmap' is strategic, 'build' is engineering — strategic wins."""
        self.assertEqual(detect_mode("Build a roadmap for the project"), MODE_STRATEGIC)

    # --- Case insensitivity ---

    def test_case_insensitive_identity(self):
        self.assertEqual(detect_mode("WHO AM I"), MODE_IDENTITY)

    def test_case_insensitive_strategic(self):
        self.assertEqual(detect_mode("ROADMAP for 2026"), MODE_STRATEGIC)

    def test_case_insensitive_engineering(self):
        self.assertEqual(detect_mode("IMPLEMENT the feature"), MODE_ENGINEERING)


# ============================================================================
# route() — full routing decisions
# ============================================================================

class TestRoute(unittest.TestCase):
    """Route function must produce correct RoutingDecision per mode."""

    def _make_task(self, user_input="test input", mode=MODE_AUTO):
        return TaskPacket(
            workspace_id="ws_test",
            agent_id="agent_test",
            user_input=user_input,
            mode=mode,
        )

    # --- Explicit mode routing ---

    def test_explicit_engineering_mode(self):
        task = self._make_task(mode=MODE_ENGINEERING)
        rd = route(task, primary_domains=["research"])
        self.assertEqual(rd.roles_to_activate, _ROLES_ENGINEERING)
        self.assertEqual(rd.aperture, APERTURE_NARROW)
        self.assertFalse(rd.require_drift_check)
        self.assertFalse(rd.require_skeptic_pass)
        self.assertTrue(rd.require_archival_review)

    def test_explicit_strategic_mode(self):
        task = self._make_task(mode=MODE_STRATEGIC)
        rd = route(task, primary_domains=["meta"])
        self.assertEqual(rd.roles_to_activate, _ROLES_STRATEGIC)
        self.assertEqual(rd.aperture, APERTURE_BROAD)
        self.assertFalse(rd.require_drift_check)

    def test_explicit_identity_mode(self):
        task = self._make_task(mode=MODE_IDENTITY)
        rd = route(task)
        self.assertEqual(rd.roles_to_activate, _ROLES_IDENTITY)
        self.assertEqual(rd.aperture, APERTURE_PROTECTED)
        self.assertTrue(rd.require_drift_check)
        self.assertTrue(rd.require_skeptic_pass)

    def test_identity_has_no_engineer(self):
        """Identity route skips engineer role."""
        task = self._make_task(mode=MODE_IDENTITY)
        rd = route(task)
        self.assertNotIn("engineer", rd.roles_to_activate)
        self.assertIn("interpreter", rd.roles_to_activate)
        self.assertIn("skeptic", rd.roles_to_activate)
        self.assertIn("archivist", rd.roles_to_activate)

    # --- Auto mode detection ---

    def test_auto_detects_engineering(self):
        task = self._make_task(user_input="Implement the new module")
        rd = route(task)
        self.assertEqual(rd.aperture, APERTURE_NARROW)
        self.assertEqual(rd.roles_to_activate, _ROLES_ENGINEERING)

    def test_auto_detects_strategic(self):
        task = self._make_task(user_input="What should we do next?")
        rd = route(task)
        self.assertEqual(rd.aperture, APERTURE_BROAD)

    def test_auto_detects_identity(self):
        task = self._make_task(user_input="Rewrite my core identity")
        rd = route(task)
        self.assertEqual(rd.aperture, APERTURE_PROTECTED)
        self.assertTrue(rd.require_drift_check)

    def test_auto_fallback_is_engineering(self):
        """When auto detection matches nothing, defaults to engineering."""
        task = self._make_task(user_input="Hello there")
        rd = route(task)
        self.assertEqual(rd.aperture, APERTURE_NARROW)
        self.assertEqual(rd.roles_to_activate, _ROLES_ENGINEERING)

    # --- Primary domains passed through ---

    def test_primary_domains_passed(self):
        task = self._make_task(mode=MODE_ENGINEERING)
        rd = route(task, primary_domains=["research", "engineering"])
        self.assertEqual(rd.primary_domains, ["research", "engineering"])

    def test_no_domains_defaults_empty(self):
        task = self._make_task(mode=MODE_ENGINEERING)
        rd = route(task)
        self.assertEqual(rd.primary_domains, [])

    # --- Invariants ---

    def test_conflict_policy_always_preserve(self):
        for mode in [MODE_ENGINEERING, MODE_STRATEGIC, MODE_IDENTITY]:
            task = self._make_task(mode=mode)
            rd = route(task)
            self.assertEqual(rd.conflict_policy, "preserve")

    def test_archival_review_always_true(self):
        for mode in [MODE_ENGINEERING, MODE_STRATEGIC, MODE_IDENTITY]:
            task = self._make_task(mode=mode)
            rd = route(task)
            self.assertTrue(rd.require_archival_review)

    # --- Route table immutability ---

    def test_roles_list_is_copy(self):
        """Caller mutation must not affect the route table."""
        task = self._make_task(mode=MODE_ENGINEERING)
        rd = route(task)
        rd.roles_to_activate.append("hacker")
        # Route again — should not have "hacker"
        rd2 = route(task)
        self.assertNotIn("hacker", rd2.roles_to_activate)


# ============================================================================
# Aperture config
# ============================================================================

class TestApertureConfig(unittest.TestCase):
    """Aperture configuration constants from AGENT_SPINE_PLAN §8."""

    def test_narrow_config(self):
        cfg = APERTURE_CONFIGS["narrow"]
        self.assertEqual(cfg.private_top_k, 6)
        self.assertEqual(cfg.shared_top_k, 3)
        self.assertEqual(cfg.depth, 1)
        self.assertEqual(cfg.character_mode, "seed_only")
        self.assertFalse(cfg.include_drift)
        self.assertFalse(cfg.include_full_character)

    def test_broad_config(self):
        cfg = APERTURE_CONFIGS["broad"]
        self.assertEqual(cfg.private_top_k, 12)
        self.assertEqual(cfg.shared_top_k, 8)
        self.assertEqual(cfg.depth, 2)
        self.assertEqual(cfg.character_mode, "full")
        self.assertFalse(cfg.include_drift)
        self.assertTrue(cfg.include_full_character)

    def test_protected_config(self):
        cfg = APERTURE_CONFIGS["protected"]
        self.assertEqual(cfg.private_top_k, 4)
        self.assertEqual(cfg.shared_top_k, 2)
        self.assertEqual(cfg.depth, 1)
        self.assertEqual(cfg.character_mode, "full_drift")
        self.assertTrue(cfg.include_drift)
        self.assertTrue(cfg.include_full_character)

    def test_get_config_valid(self):
        cfg = get_config("broad")
        self.assertEqual(cfg.name, "broad")

    def test_get_config_invalid(self):
        with self.assertRaises(ValueError):
            get_config("ultra_wide")

    def test_configs_are_frozen(self):
        """ApertureConfig is frozen — mutation should raise."""
        cfg = APERTURE_CONFIGS["narrow"]
        with self.assertRaises(AttributeError):
            cfg.private_top_k = 100


# ============================================================================
# build_memory_context — aperture builder
# ============================================================================

class TestBuildMemoryContext(unittest.TestCase):
    """Memory context builder with mock query functions."""

    def _mock_query_fn(self, workspace_id, agent_id, query_text, top_k, domain_id):
        """Returns a mock result with numbered entries up to top_k."""
        return {
            "results": [
                {"id": i, "text": f"Memory {i}", "score": 1.0 - i * 0.1}
                for i in range(top_k + 5)  # return more than requested
            ]
        }

    def _mock_character_fn(self, workspace_id, agent_id):
        return {"name": "Ryuki", "seed": "test_seed", "traits": ["curious"]}

    def _mock_drift_fn(self, workspace_id, agent_id):
        return {"total_drift": 0.15, "zone": "green"}

    # --- No query_fn (pipeline structure test) ---

    def test_no_query_fn_returns_empty_memories(self):
        ctx = build_memory_context("narrow", "ws1", "a1", "test query")
        self.assertEqual(ctx.private_memories, [])
        self.assertEqual(ctx.shared_memories, [])
        self.assertEqual(ctx.aperture_name, "narrow")
        self.assertEqual(ctx.total_memories, 0)

    # --- Narrow aperture ---

    def test_narrow_memory_limits(self):
        ctx = build_memory_context(
            "narrow", "ws1", "a1", "test query",
            query_fn=self._mock_query_fn,
        )
        self.assertLessEqual(len(ctx.private_memories), 6)
        self.assertLessEqual(len(ctx.shared_memories), 3)

    def test_narrow_character_seed_only(self):
        ctx = build_memory_context(
            "narrow", "ws1", "a1", "test query",
            query_fn=self._mock_query_fn,
            character_fn=self._mock_character_fn,
        )
        self.assertIsNotNone(ctx.character_context)
        self.assertTrue(ctx.character_context.get("seed_only", False))

    def test_narrow_no_drift(self):
        ctx = build_memory_context(
            "narrow", "ws1", "a1", "test query",
            query_fn=self._mock_query_fn,
            drift_fn=self._mock_drift_fn,
        )
        self.assertIsNone(ctx.drift_snapshot)

    # --- Broad aperture ---

    def test_broad_memory_limits(self):
        ctx = build_memory_context(
            "broad", "ws1", "a1", "test query",
            query_fn=self._mock_query_fn,
        )
        self.assertLessEqual(len(ctx.private_memories), 12)
        self.assertLessEqual(len(ctx.shared_memories), 8)

    def test_broad_full_character(self):
        ctx = build_memory_context(
            "broad", "ws1", "a1", "test query",
            character_fn=self._mock_character_fn,
        )
        self.assertIsNotNone(ctx.character_context)
        # Full character — no seed_only wrapper
        self.assertIn("name", ctx.character_context)

    def test_broad_no_drift(self):
        ctx = build_memory_context(
            "broad", "ws1", "a1", "test query",
            drift_fn=self._mock_drift_fn,
        )
        self.assertIsNone(ctx.drift_snapshot)

    # --- Protected aperture ---

    def test_protected_memory_limits(self):
        ctx = build_memory_context(
            "protected", "ws1", "a1", "test query",
            query_fn=self._mock_query_fn,
        )
        self.assertLessEqual(len(ctx.private_memories), 4)
        self.assertLessEqual(len(ctx.shared_memories), 2)

    def test_protected_full_character(self):
        ctx = build_memory_context(
            "protected", "ws1", "a1", "test query",
            character_fn=self._mock_character_fn,
        )
        self.assertIsNotNone(ctx.character_context)
        self.assertIn("name", ctx.character_context)

    def test_protected_includes_drift(self):
        ctx = build_memory_context(
            "protected", "ws1", "a1", "test query",
            drift_fn=self._mock_drift_fn,
        )
        self.assertIsNotNone(ctx.drift_snapshot)
        self.assertEqual(ctx.drift_snapshot["zone"], "green")

    # --- Error resilience ---

    def test_query_fn_exception_returns_empty(self):
        def bad_query(*args):
            raise RuntimeError("DB unavailable")

        ctx = build_memory_context(
            "broad", "ws1", "a1", "test query",
            query_fn=bad_query,
        )
        self.assertEqual(ctx.private_memories, [])
        self.assertEqual(ctx.shared_memories, [])

    def test_character_fn_exception_returns_none(self):
        def bad_char(*args):
            raise RuntimeError("Character service down")

        ctx = build_memory_context(
            "broad", "ws1", "a1", "test query",
            character_fn=bad_char,
        )
        self.assertIsNone(ctx.character_context)

    def test_drift_fn_exception_returns_none(self):
        def bad_drift(*args):
            raise RuntimeError("Drift service down")

        ctx = build_memory_context(
            "protected", "ws1", "a1", "test query",
            drift_fn=bad_drift,
        )
        self.assertIsNone(ctx.drift_snapshot)

    # --- Invalid aperture ---

    def test_invalid_aperture_rejected(self):
        with self.assertRaises(ValueError):
            build_memory_context("wide_open", "ws1", "a1", "test")

    # --- Domain and query_text pass-through ---

    def test_domain_and_query_stored(self):
        ctx = build_memory_context(
            "narrow", "ws1", "a1", "test query",
            domain_id="research",
        )
        self.assertEqual(ctx.domain_id, "research")
        self.assertEqual(ctx.query_text, "test query")

    # --- Serialization ---

    def test_memory_context_round_trip(self):
        ctx = build_memory_context(
            "broad", "ws1", "a1", "round trip test",
            query_fn=self._mock_query_fn,
            character_fn=self._mock_character_fn,
            domain_id="engineering",
        )
        d = ctx.to_dict()
        restored = MemoryContext.from_dict(d)
        self.assertEqual(restored.aperture_name, "broad")
        self.assertEqual(restored.domain_id, "engineering")
        self.assertEqual(restored.query_text, "round trip test")
        self.assertEqual(len(restored.private_memories), len(ctx.private_memories))
        self.assertEqual(restored.config.private_top_k, 12)

    def test_memory_context_from_dict_empty_rejected(self):
        with self.assertRaises(ValueError):
            MemoryContext.from_dict({})

    # --- _extract_memories edge cases ---

    def test_query_fn_returns_no_results_key(self):
        """If query returns dict without known keys, get empty list."""
        def weird_query(*args):
            return {"something_else": [1, 2, 3]}

        ctx = build_memory_context(
            "narrow", "ws1", "a1", "test",
            query_fn=weird_query,
        )
        self.assertEqual(ctx.private_memories, [])

    def test_query_fn_returns_non_dict(self):
        """If query returns non-dict, get empty list."""
        def string_query(*args):
            return "not a dict"

        ctx = build_memory_context(
            "narrow", "ws1", "a1", "test",
            query_fn=string_query,
        )
        self.assertEqual(ctx.private_memories, [])


if __name__ == "__main__":
    unittest.main()
