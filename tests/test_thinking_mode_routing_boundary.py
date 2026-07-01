"""tests/test_thinking_mode_routing_boundary.py — Layer-1 mode-routing lattice lock.

Tests-only CHARACTERIZATION of the CURRENT non-governed, non-identity Layer-1
routing lattice that ThinkingController produces for a single turn:

    TOOL       / USE_TOOL   (execution / tool intent  — frame.tool_need)
    RETRIEVAL  / ANSWER     (retrieval / memory intent — frame.memory_need)
    REFLECTIVE / ANSWER     (analytical depth — frame.confidence_need >= 0.60 floor)
    FAST       / ANSWER     (plain direct input — no stronger driver)

It pins BOTH the clean single-signal routing and the PRECEDENCE order that
choose_mode already implements for the non-governed / non-identity / non-live-
social slice:

    tool_need  >  memory_need  >  confidence_need(>=0.60)  >  (default FAST)

together with choose_action's "USE_TOOL only when tool_need" contract.

Scope: tests-only. No production change. This file introduces NO new TaskFrame /
MemoryPlan / ReflectionTrace field expectation, NO advisory / shaper / consumer
behavior, and asserts routing purely from the existing coarse scalar frame
fields (tool_need / memory_need / confidence_need / ambiguity_score) already
computed by frame_task. Governed / identity / live-social lanes are out of scope
(higher-priority branches, characterized elsewhere).
"""
from __future__ import annotations

import pytest

from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ActionType, CognitiveMode


_tc = ThinkingController()


def _route(query: str):
    """Full single-turn routing for a query (non-governed / non-identity)."""
    return _tc.think("ws_boundary", "agent_boundary", query)


# Representative, confound-free prompts — each isolates exactly one primary
# routing driver (except the explicit precedence-overlap prompts below).
_FAST_PLAIN = "The weather is nice today."
_ANALYTICAL_ONLY = "Analyze the tradeoffs in this proposal."
_RETRIEVAL_ONLY = "Search the wiki for the onboarding guide."
_TOOL_ONLY = "Calculate the total using python."

# Precedence-overlap prompts.
_TOOL_OVER_RETRIEVAL_ANALYTICAL = "Read the summary and analyze it using python."
_RETRIEVAL_OVER_ANALYTICAL = "Read the summary and analyze the tradeoffs."


# ---------------------------------------------------------------------------
# 1. Clean single-signal routing
# ---------------------------------------------------------------------------

class TestCleanRouting:
    def test_plain_direct_input_routes_fast_answer(self):
        r = _route(_FAST_PLAIN)
        assert r.mode_decision.chosen_mode == CognitiveMode.FAST
        assert r.action_decision.action == ActionType.ANSWER

    def test_analytical_only_routes_reflective_answer(self):
        r = _route(_ANALYTICAL_ONLY)
        assert r.mode_decision.chosen_mode == CognitiveMode.REFLECTIVE
        assert r.action_decision.action == ActionType.ANSWER

    def test_retrieval_only_routes_retrieval_answer(self):
        r = _route(_RETRIEVAL_ONLY)
        assert r.mode_decision.chosen_mode == CognitiveMode.RETRIEVAL
        assert r.action_decision.action == ActionType.ANSWER

    def test_execution_only_routes_tool_use_tool(self):
        r = _route(_TOOL_ONLY)
        assert r.mode_decision.chosen_mode == CognitiveMode.TOOL
        assert r.action_decision.action == ActionType.USE_TOOL


# ---------------------------------------------------------------------------
# 2. Precedence lattice: tool_need > memory_need > confidence_need > FAST
# ---------------------------------------------------------------------------

class TestPrecedence:
    def test_tool_beats_retrieval_and_analytical_overlap(self):
        # tool_need is checked before memory_need and confidence_need, so an
        # explicit execution phrase wins even when retrieval + analytical signals
        # co-occur in the same prompt.
        r = _route(_TOOL_OVER_RETRIEVAL_ANALYTICAL)
        f = r.task_frame
        assert f.tool_need is True
        assert f.memory_need is True          # retrieval signal present
        assert f.confidence_need >= 0.60      # analytical floor present
        assert r.mode_decision.chosen_mode == CognitiveMode.TOOL
        assert r.action_decision.action == ActionType.USE_TOOL

    def test_retrieval_beats_analytical_overlap(self):
        # memory_need is checked before the confidence_need REFLECTIVE branch,
        # so a retrieval + analytical prompt (no execution phrase) stays RETRIEVAL.
        r = _route(_RETRIEVAL_OVER_ANALYTICAL)
        f = r.task_frame
        assert f.tool_need is False
        assert f.memory_need is True
        assert f.confidence_need >= 0.60      # analytical floor also fired
        assert r.mode_decision.chosen_mode == CognitiveMode.RETRIEVAL
        assert r.action_decision.action == ActionType.ANSWER

    def test_analytical_beats_fast_only_through_confidence_floor(self):
        # Analytical depth reaches REFLECTIVE ONLY via the confidence_need floor
        # (>= 0.60), NOT via ambiguity: this prompt's ambiguity stays below the
        # 0.50 REFLECTIVE-by-ambiguity threshold, so the floor is doing the work.
        r = _route(_ANALYTICAL_ONLY)
        f = r.task_frame
        assert f.confidence_need >= 0.60
        assert f.ambiguity_score < 0.50
        assert f.tool_need is False
        assert f.memory_need is False
        assert r.mode_decision.chosen_mode == CognitiveMode.REFLECTIVE
        assert r.action_decision.action == ActionType.ANSWER


# ---------------------------------------------------------------------------
# 3. Scalar drivers behind each lane
# ---------------------------------------------------------------------------

class TestScalarDrivers:
    def test_tool_case_sets_tool_need(self):
        assert _route(_TOOL_ONLY).task_frame.tool_need is True

    def test_retrieval_case_sets_memory_need_and_no_tool_need(self):
        f = _route(_RETRIEVAL_ONLY).task_frame
        assert f.memory_need is True
        assert f.tool_need is False           # no execution phrase present

    def test_analytical_only_sets_confidence_floor_and_no_tool_need(self):
        f = _route(_ANALYTICAL_ONLY).task_frame
        assert f.confidence_need >= 0.60
        assert f.tool_need is False

    def test_fast_case_has_no_accidental_drivers(self):
        f = _route(_FAST_PLAIN).task_frame
        assert f.tool_need is False
        assert f.memory_need is False
        assert f.confidence_need < 0.60
        assert f.ambiguity_score < 0.50


# ---------------------------------------------------------------------------
# 4. Boundary — routing depends only on existing scalar frame fields; this file
#    introduces no new field / schema / advisory / shaper / consumer expectation.
# ---------------------------------------------------------------------------

_ADVISORY_SHAPER_NAMES = (
    "memory_plan_sufficiency_advisory",
    "memory_plan_quality",
    "memory_plan_shaping_posture",
)

_ALL_PROMPTS = [_FAST_PLAIN, _ANALYTICAL_ONLY, _RETRIEVAL_ONLY, _TOOL_ONLY]


class TestBoundaryNoSchemaExpansion:
    @pytest.mark.parametrize("query", _ALL_PROMPTS)
    def test_taskframe_carries_no_advisory_or_shaper_field(self, query: str):
        f = _route(query).task_frame
        for name in _ADVISORY_SHAPER_NAMES:
            assert not hasattr(f, name), f"TaskFrame unexpectedly exposes {name!r}"

    @pytest.mark.parametrize("query", _ALL_PROMPTS)
    def test_memoryplan_carries_no_advisory_or_shaper_field(self, query: str):
        plan = _route(query).memory_plan
        for name in _ADVISORY_SHAPER_NAMES:
            assert not hasattr(plan, name), f"MemoryPlan unexpectedly exposes {name!r}"

    def test_routing_scalars_are_plain_primitives(self):
        # The lattice is driven purely by coarse primitive scalars already on the
        # frame — bool flags and float scores — never an advisory/consumer object.
        f = _route(_ANALYTICAL_ONLY).task_frame
        assert type(f.tool_need) is bool
        assert type(f.memory_need) is bool
        assert type(f.confidence_need) is float
        assert type(f.ambiguity_score) is float
