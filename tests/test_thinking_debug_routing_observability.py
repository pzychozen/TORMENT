"""tests/test_thinking_debug_routing_observability.py — Layer-1 debug/observability lock.

Tests-only characterization of the /thinking/debug-style serialization
(`ThinkingController().think(...).to_dict()`) for the non-governed / non-identity
Layer-1 routing lattice. Uses DIRECT ThinkingController calls only — no
endpoints, no TestClient.

For representative TOOL/USE_TOOL, RETRIEVAL/ANSWER, REFLECTIVE/ANSWER, and
FAST/ANSWER turns it asserts the observable debug surface stays COHERENT:
  * task_frame routing scalars (tool_need / memory_need / confidence_need),
  * mode_decision.chosen_mode and action_decision.action,
  * the reflection_trace coarse MIRRORS agree with the above,
and stays MINIMAL — debug carries only the controller-version marker, and no
MemoryPlan advisory / shaper / consumer field or duplicated metacognition map
appears anywhere in the serialized result (the maps live only on
reflection_trace).

Scope: tests-only. No production change. Introduces no new field / advisory /
shaper / consumer / debug key; asserts nothing about raw / private / provider /
output-decision content; touches no dynamic-kernel / conversation_shock /
provider / runtime / database / API / schema / private-runtime / prompt /
memory-write / transcript / identity / output-control surface.
"""
from __future__ import annotations

import json

import pytest

from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ActionType, CognitiveMode


# (prompt, expected mode value, expected action value) — confound-free prompts
# reused from the mode-routing boundary lock; each isolates one primary driver.
_CASES = [
    ("Calculate the total using python.",         CognitiveMode.TOOL.value,       ActionType.USE_TOOL.value),
    ("Search the wiki for the onboarding guide.", CognitiveMode.RETRIEVAL.value,  ActionType.ANSWER.value),
    ("Analyze the tradeoffs in this proposal.",   CognitiveMode.REFLECTIVE.value, ActionType.ANSWER.value),
    ("The weather is nice today.",                CognitiveMode.FAST.value,       ActionType.ANSWER.value),
]

# Names that would signal a MemoryPlan advisory/shaper/consumer or a duplicated
# ReflectionTrace metacognition map leaking into the debug serialization.
_FORBIDDEN_SURFACE_NAMES = (
    "memory_plan_sufficiency_advisory",
    "memory_plan_quality",
    "memory_plan_shaping_posture",
)


def _debug_dict(prompt: str) -> dict:
    """Direct /thinking/debug-shape serialization for a single turn."""
    return ThinkingController().think("ws_debug", "agent_debug", prompt).to_dict()


# ---------------------------------------------------------------------------
# 1. Mode / action / reflection_trace mirrors stay coherent per lane
# ---------------------------------------------------------------------------

class TestRoutingObservabilityCoherent:
    @pytest.mark.parametrize("prompt,mode_val,action_val", _CASES)
    def test_mode_and_action_serialized(self, prompt, mode_val, action_val):
        d = _debug_dict(prompt)
        assert d["mode_decision"]["chosen_mode"] == mode_val
        assert d["action_decision"]["action"] == action_val

    @pytest.mark.parametrize("prompt,mode_val,action_val", _CASES)
    def test_reflection_trace_mirrors_mode_and_action(self, prompt, mode_val, action_val):
        d = _debug_dict(prompt)
        rt = d["reflection_trace"]
        assert rt is not None, "think() should attach a reflection_trace"
        assert rt["chosen_mode"] == d["mode_decision"]["chosen_mode"] == mode_val
        assert rt["action"] == d["action_decision"]["action"] == action_val

    @pytest.mark.parametrize("prompt,mode_val,action_val", _CASES)
    def test_reflection_trace_scalar_mirrors_match_task_frame(self, prompt, mode_val, action_val):
        d = _debug_dict(prompt)
        tf, rt = d["task_frame"], d["reflection_trace"]
        for scalar in ("tool_need", "memory_need", "confidence_need",
                       "ambiguity_score", "source_type"):
            assert rt[scalar] == tf[scalar], (
                f"{prompt!r}: reflection_trace[{scalar!r}]={rt[scalar]!r} != "
                f"task_frame[{scalar!r}]={tf[scalar]!r}"
            )


# ---------------------------------------------------------------------------
# 2. Per-lane routing scalars on the serialized task_frame
# ---------------------------------------------------------------------------

class TestRoutingScalarsPerLane:
    def test_tool_case_scalars(self):
        tf = _debug_dict("Calculate the total using python.")["task_frame"]
        assert tf["tool_need"] is True

    def test_retrieval_case_scalars(self):
        tf = _debug_dict("Search the wiki for the onboarding guide.")["task_frame"]
        assert tf["memory_need"] is True
        assert tf["tool_need"] is False

    def test_reflective_case_scalars(self):
        tf = _debug_dict("Analyze the tradeoffs in this proposal.")["task_frame"]
        assert tf["confidence_need"] >= 0.60
        assert tf["tool_need"] is False
        assert tf["memory_need"] is False

    def test_fast_case_scalars(self):
        tf = _debug_dict("The weather is nice today.")["task_frame"]
        assert tf["tool_need"] is False
        assert tf["memory_need"] is False
        assert tf["confidence_need"] < 0.60


# ---------------------------------------------------------------------------
# 3. Debug surface stays minimal; no advisory/shaper/consumer/duplication
# ---------------------------------------------------------------------------

class TestDebugMinimalNoDuplication:
    @pytest.mark.parametrize("prompt,mode_val,action_val", _CASES)
    def test_debug_is_minimal_version_marker_only(self, prompt, mode_val, action_val):
        d = _debug_dict(prompt)
        # debug carries ONLY the controller-version marker — no routing payload,
        # no advisory, no duplicated reflection_trace / memory_plan observation.
        assert isinstance(d["debug"], dict)
        assert set(d["debug"].keys()) == {"controller_version"}

    @pytest.mark.parametrize("prompt,mode_val,action_val", _CASES)
    def test_no_advisory_or_shaper_surface_in_plan_or_debug(self, prompt, mode_val, action_val):
        d = _debug_dict(prompt)
        for name in _FORBIDDEN_SURFACE_NAMES:
            assert name not in d["memory_plan"], f"memory_plan leaked {name!r}"
            assert name not in d["debug"], f"debug leaked {name!r}"
            assert name not in d, f"top-level result leaked {name!r}"
        # No stringified duplication either (defends against nested duplication).
        mp_blob = json.dumps(d["memory_plan"])
        dbg_blob = json.dumps(d["debug"])
        for name in _FORBIDDEN_SURFACE_NAMES:
            assert name not in mp_blob, f"memory_plan blob leaked {name!r}"
            assert name not in dbg_blob, f"debug blob leaked {name!r}"

    def test_metacognition_maps_live_only_on_reflection_trace(self):
        # Positive anchor: the three maps DO exist on reflection_trace (their sole
        # surface), so the "absent from memory_plan/debug" checks above are a real
        # no-duplication lock, not the maps being globally missing.
        rt = _debug_dict("The weather is nice today.")["reflection_trace"]
        for name in _FORBIDDEN_SURFACE_NAMES:
            assert name in rt, f"reflection_trace should expose {name!r}"


# ---------------------------------------------------------------------------
# 4. Boundary — no new top-level debug surface is introduced
# ---------------------------------------------------------------------------

class TestBoundaryNoNewTopLevelSurface:
    _KNOWN_TOP_LEVEL = {
        "task_frame", "mode_decision", "memory_plan", "action_decision",
        "review_result", "response_draft", "stance", "geometric_context",
        "debug", "reflection_trace", "participation_guidance",
    }

    @pytest.mark.parametrize("prompt,mode_val,action_val", _CASES)
    def test_to_dict_top_level_keys_are_known(self, prompt, mode_val, action_val):
        d = _debug_dict(prompt)
        extra = set(d.keys()) - self._KNOWN_TOP_LEVEL
        assert extra == set(), f"unexpected new top-level debug surface: {extra!r}"
