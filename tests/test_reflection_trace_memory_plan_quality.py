"""tests/test_reflection_trace_memory_plan_quality.py

ReflectionTrace ``memory_plan_quality`` (Layer-1 observability).

Locks a content-free, DERIVED summary of MemoryPlan plan-quality / thinness on
ReflectionTrace. It is computed in ``ReflectionTrace.__post_init__`` from the
already-normalized, content-free trace fields (lane budgets, confidence_need, and
the shaping posture) — never from raw text or new inputs, and nothing branches on
it. Fixed exact keys; primitive int/bool values only.

    memory_plan_quality = {
        "active_lane_count": int,             # lanes with top_k > 0
        "non_core_active_lane_count": int,    # active lanes excluding "core"
        "total_lane_budget": int,             # sum of positive top_k values
        "thin_context": bool,                 # no active non-core lane OR one lane total
        "low_confidence_need": bool,          # confidence_need >= 0.60
        "shaping_reflex_count": int,          # count of True in shaping posture
        "heavily_shaped": bool,               # shaping_reflex_count >= 2
    }

Obligations locked here: see the numbered tests (1..16).
"""
from __future__ import annotations

import json

import pytest

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.reflection_trace import (
    ReflectionTrace,
    build_reflection_trace,
    _MEMORY_PLAN_QUALITY_KEYS,
)

_QUALITY_KEYS = {
    "active_lane_count", "non_core_active_lane_count", "total_lane_budget",
    "thin_context", "low_confidence_need", "shaping_reflex_count", "heavily_shaped",
}


def _trace(*, top_k=None, weight=None, confidence_need=0.0, posture=None, **over):
    kw = dict(
        chosen_mode="reflective", action="answer", stance=None,
        review_status_flags={"approved": True},
        top_k_by_lane=(top_k if top_k is not None else {"core": 6, "relational": 4}),
        weight_by_lane=(weight if weight is not None else {"core": 1.0, "relational": 0.85}),
        geometric_context_present=False,
        confidence_need=confidence_need,
    )
    if posture is not None:
        kw["memory_plan_shaping_posture"] = posture
    kw.update(over)
    return build_reflection_trace(**kw)


# ---------------------------------------------------------------------------
# 1-3. field shape: present in to_dict, exact keys, primitive int/bool values
# ---------------------------------------------------------------------------

def test_quality_appears_in_to_dict():
    assert "memory_plan_quality" in _trace().to_dict()


def test_quality_keys_are_exactly_the_seven():
    q = _trace().to_dict()["memory_plan_quality"]
    assert set(q.keys()) == _QUALITY_KEYS
    assert set(_MEMORY_PLAN_QUALITY_KEYS) == _QUALITY_KEYS   # module constant is source of truth


def test_quality_values_are_primitive_int_or_bool_only():
    q = _trace().to_dict()["memory_plan_quality"]
    assert all(type(v) in (int, bool) for v in q.values())


# ---------------------------------------------------------------------------
# 4-5. read-only instance mapping; to_dict returns a plain copied dict
# ---------------------------------------------------------------------------

def test_quality_map_is_read_only():
    t = _trace()
    with pytest.raises((TypeError, AttributeError)):
        t.memory_plan_quality["active_lane_count"] = 999  # type: ignore[index]


def test_to_dict_returns_plain_copied_dict():
    t = _trace()
    d = t.to_dict()
    assert type(d["memory_plan_quality"]) is dict
    d["memory_plan_quality"]["active_lane_count"] = -1     # must NOT raise
    assert t.memory_plan_quality["active_lane_count"] != -1   # internal unaffected


def test_passed_quality_input_is_ignored_and_normalized():
    # missing/stray/nonprimitive inputs must not create arbitrary keys or leak text.
    # (build_reflection_trace has no such kwarg — the field is derived — so this is
    # exercised at the dataclass constructor, whose __post_init__ replaces any input.)
    t = ReflectionTrace(
        chosen_mode="reflective", action="answer",
        lane_budget_shape={"core": 6, "relational": 4},
        confidence_need=0.0,
        memory_plan_quality={"junk": "ZZQ_should_drop", "active_lane_count": "BAD"},
    )
    q = dict(t.memory_plan_quality)
    assert set(q.keys()) == _QUALITY_KEYS               # stray key dropped
    assert "junk" not in q
    assert all(type(v) in (int, bool) for v in q.values())
    assert q["active_lane_count"] == 2                  # derived, not the passed "BAD"


# ---------------------------------------------------------------------------
# 6. raw user marker text does not leak into JSON
# ---------------------------------------------------------------------------

def test_no_raw_user_marker_in_json(monkeypatch):
    monkeypatch.setattr(tc, "_RELATIONAL_AMBIGUITY_PROMINENCE_V1_ENABLE", True)
    monkeypatch.setattr(tc, "_AMBIGUITY_CONTEXT_DIVERSITY_V1_ENABLE", True)
    marker = "ZZQ_QUALITY_MARKER_5R"
    r = ThinkingController().think("ws", "ag", f"maybe remember stuff?? {marker}")
    blob = json.dumps(r.reflection_trace.to_dict())
    assert marker not in blob
    q = r.reflection_trace.to_dict()["memory_plan_quality"]
    assert set(q.keys()) == _QUALITY_KEYS
    assert all(type(v) in (int, bool) for v in q.values())


# ---------------------------------------------------------------------------
# counts / budget derivation
# ---------------------------------------------------------------------------

def test_counts_and_total_budget_derivation():
    t = _trace(top_k={"core": 6, "relational": 4, "deep": 3, "archive": 0, "collective": 0})
    q = dict(t.memory_plan_quality)
    assert q["active_lane_count"] == 3            # core, relational, deep
    assert q["non_core_active_lane_count"] == 2   # relational, deep
    assert q["total_lane_budget"] == 13           # 6 + 4 + 3


# ---------------------------------------------------------------------------
# 7-9. thin_context semantics
# ---------------------------------------------------------------------------

def test_thin_context_true_when_only_core_active():
    t = _trace(top_k={"core": 6, "relational": 0, "deep": 0})
    q = dict(t.memory_plan_quality)
    assert q["active_lane_count"] == 1 and q["non_core_active_lane_count"] == 0
    assert q["thin_context"] is True


def test_thin_context_true_when_no_non_core_lanes_active():
    # nothing active at all -> no non-core lane active -> thin
    t = _trace(top_k={"core": 0, "relational": 0, "deep": 0})
    q = dict(t.memory_plan_quality)
    assert q["non_core_active_lane_count"] == 0
    assert q["thin_context"] is True


def test_thin_context_false_when_non_core_active_and_multiple_lanes():
    t = _trace(top_k={"core": 6, "relational": 4})
    q = dict(t.memory_plan_quality)
    assert q["active_lane_count"] == 2 and q["non_core_active_lane_count"] == 1
    assert q["thin_context"] is False


# ---------------------------------------------------------------------------
# 10. low_confidence_need threshold is confidence_need >= 0.60
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cn,expected", [(0.0, False), (0.59, False),
                                         (0.60, True), (0.61, True), (1.0, True)])
def test_low_confidence_need_threshold(cn, expected):
    q = dict(_trace(confidence_need=cn).memory_plan_quality)
    assert q["low_confidence_need"] is expected


# ---------------------------------------------------------------------------
# 11-12. shaping_reflex_count from posture; heavily_shaped when >= 2
# ---------------------------------------------------------------------------

def test_shaping_reflex_count_zero_by_default():
    q = dict(_trace().memory_plan_quality)
    assert q["shaping_reflex_count"] == 0
    assert q["heavily_shaped"] is False


def test_shaping_reflex_count_one_not_heavy():
    q = dict(_trace(posture={"relational_ambiguity_prominence": True}).memory_plan_quality)
    assert q["shaping_reflex_count"] == 1
    assert q["heavily_shaped"] is False


def test_shaping_reflex_count_two_is_heavy():
    q = dict(_trace(posture={
        "relational_ambiguity_prominence": True,
        "ambiguity_context_diversity": True,
    }).memory_plan_quality)
    assert q["shaping_reflex_count"] == 2
    assert q["heavily_shaped"] is True


# ---------------------------------------------------------------------------
# 13-15. lane_budget_shape / lane_weight_shape / posture behavior unchanged
# ---------------------------------------------------------------------------

def test_lane_budget_shape_behavior_unchanged():
    t = _trace(top_k={"core": 6, "relational": 4, "deep": 0})
    assert dict(t.lane_budget_shape) == {"core": 6, "relational": 4, "deep": 0}
    assert all(isinstance(v, int) for v in t.lane_budget_shape.values())


def test_lane_weight_shape_behavior_unchanged():
    t = _trace(weight={"core": 1.0, "relational": 0.85, "deep": 0.0})
    assert dict(t.lane_weight_shape) == {"core": 1.0, "relational": 0.85, "deep": 0.0}
    assert all(isinstance(v, float) for v in t.lane_weight_shape.values())


def test_shaping_posture_behavior_unchanged():
    t = _trace(posture={"relational_ambiguity_prominence": True})
    p = dict(t.memory_plan_shaping_posture)
    assert p == {"relational_ambiguity_prominence": True,
                 "ambiguity_context_diversity": False}


# ---------------------------------------------------------------------------
# 16. runner parity: run_turn produces a consistent memory_plan_quality
# ---------------------------------------------------------------------------

class _FakeFabric:
    def ingest(self, *a, **k):
        return {"status": "ok"}

    def measure_drift(self, *a, **k):
        return None

    def gravity_correction(self, *a, **k):
        return None


def test_runner_path_emits_consistent_memory_plan_quality():
    from torment_service.agent_loop import AgentRunner, Observation, LLMResponse

    class _FakeLLM:
        def complete(self, system_prompt, messages, tools=None):
            return LLMResponse(text="ok")

    class _FakeTool:
        def execute(self, family, arguments, defaults):
            return {"output": "x"}

    runner = AgentRunner(
        controller=ThinkingController(), fabric=_FakeFabric(),
        llm_client=_FakeLLM(), tool_executor=_FakeTool(),
    )
    result = runner.run_turn(
        workspace_id="ws", agent_id="ag",
        observation=Observation(text="Hello there", source_type="user_text"), step=1,
    )
    q = result.reflection_trace.to_dict()["memory_plan_quality"]
    assert set(q.keys()) == _QUALITY_KEYS
    assert all(type(v) in (int, bool) for v in q.values())
    # parity: quality mirrors the effective MemoryPlan the runner actually used
    plan = result.memory_plan
    active = {k: v for k, v in plan.top_k_by_lane.items()
              if isinstance(v, int) and not isinstance(v, bool) and v > 0}
    assert q["active_lane_count"] == len(active)
    assert q["total_lane_budget"] == sum(active.values())
    assert q["non_core_active_lane_count"] == sum(1 for k in active if k != "core")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
