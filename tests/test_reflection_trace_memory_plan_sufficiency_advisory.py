"""tests/test_reflection_trace_memory_plan_sufficiency_advisory.py

ReflectionTrace ``memory_plan_sufficiency_advisory`` (Layer-1 observability).

Locks a content-free, DERIVED advisory map that summarizes whether the MemoryPlan
looks thin / low-confidence / heavily-shaped, or nominal. It is computed in
``ReflectionTrace.__post_init__`` ONLY from the already-derived ``memory_plan_quality``
map — never from raw text or new inputs — and nothing branches on it.

    memory_plan_sufficiency_advisory = {
        "thin_context_candidate": bool,      # = memory_plan_quality["thin_context"]
        "low_confidence_candidate": bool,    # = memory_plan_quality["low_confidence_need"]
        "heavily_shaped_candidate": bool,    # = memory_plan_quality["heavily_shaped"]
        "nominal_plan_candidate": bool,      # True iff the other three are all False
    }

Obligations locked here: see the numbered tests (1..17).
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Dict, List

import pytest

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.reflection_trace import (
    ReflectionTrace,
    build_reflection_trace,
    _MEMORY_PLAN_SUFFICIENCY_ADVISORY_KEYS,
)

_ADVISORY_KEYS = {
    "thin_context_candidate", "low_confidence_candidate",
    "heavily_shaped_candidate", "nominal_plan_candidate",
}
_REL_FLAG = "_RELATIONAL_AMBIGUITY_PROMINENCE_V1_ENABLE"
_AMB_FLAG = "_AMBIGUITY_CONTEXT_DIVERSITY_V1_ENABLE"
_EL = "maybe remember stuff??"

# advisory identifiers that must never reach a model / side-effect surface
_ADVISORY_MARKERS = (
    "memory_plan_sufficiency_advisory",
    "thin_context_candidate", "low_confidence_candidate",
    "heavily_shaped_candidate", "nominal_plan_candidate",
)


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


# scenario builders driving the three candidate flags via memory_plan_quality
def _thin_trace():      # only core active -> thin_context True
    return _trace(top_k={"core": 6, "relational": 0, "deep": 0})


def _low_conf_trace():  # not thin, confidence_need >= 0.60
    return _trace(top_k={"core": 6, "relational": 4}, confidence_need=0.75)


def _heavy_trace():     # not thin, both shapers fired -> heavily_shaped True
    return _trace(top_k={"core": 6, "relational": 4}, posture={
        "relational_ambiguity_prominence": True, "ambiguity_context_diversity": True})


def _nominal_trace():   # not thin, confident, not heavy
    return _trace(top_k={"core": 6, "relational": 4}, confidence_need=0.0)


# ---------------------------------------------------------------------------
# 1-3. field shape: present in to_dict, exact keys, boolean values only
# ---------------------------------------------------------------------------

def test_advisory_appears_in_to_dict():
    assert "memory_plan_sufficiency_advisory" in _trace().to_dict()


def test_advisory_keys_are_exactly_the_four():
    a = _trace().to_dict()["memory_plan_sufficiency_advisory"]
    assert set(a.keys()) == _ADVISORY_KEYS
    assert set(_MEMORY_PLAN_SUFFICIENCY_ADVISORY_KEYS) == _ADVISORY_KEYS


def test_advisory_values_are_bool_only():
    a = _trace().to_dict()["memory_plan_sufficiency_advisory"]
    assert all(type(v) is bool for v in a.values())


# ---------------------------------------------------------------------------
# 4-6. read-only; to_dict plain copy; caller input ignored/replaced
# ---------------------------------------------------------------------------

def test_advisory_map_is_read_only():
    t = _trace()
    with pytest.raises((TypeError, AttributeError)):
        t.memory_plan_sufficiency_advisory["thin_context_candidate"] = True  # type: ignore[index]


def test_to_dict_returns_plain_copied_dict():
    t = _trace()
    d = t.to_dict()
    assert type(d["memory_plan_sufficiency_advisory"]) is dict
    before = dict(t.memory_plan_sufficiency_advisory)
    d["memory_plan_sufficiency_advisory"]["thin_context_candidate"] = True  # must NOT raise
    # mutating the returned copy leaves the internal read-only mapping unchanged
    assert dict(t.memory_plan_sufficiency_advisory) == before


def test_caller_provided_advisory_is_ignored_and_replaced():
    # direct construction with junk advisory + a KNOWN thin quality -> derived wins
    t = ReflectionTrace(
        chosen_mode="fast", action="answer",
        lane_budget_shape={"core": 6},        # only core active -> thin
        confidence_need=0.0,
        memory_plan_sufficiency_advisory={"junk": "ZZQ_text", "thin_context_candidate": "BAD"},
    )
    a = dict(t.memory_plan_sufficiency_advisory)
    assert set(a.keys()) == _ADVISORY_KEYS          # stray key dropped
    assert "junk" not in a
    assert all(type(v) is bool for v in a.values())
    assert a["thin_context_candidate"] is True       # derived, not the passed "BAD"


# ---------------------------------------------------------------------------
# 7-9. each candidate derives from the matching memory_plan_quality flag
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("builder", [_thin_trace, _low_conf_trace, _heavy_trace, _nominal_trace])
def test_candidates_mirror_memory_plan_quality(builder):
    t = builder()
    q, a = dict(t.memory_plan_quality), dict(t.memory_plan_sufficiency_advisory)
    assert a["thin_context_candidate"] == q["thin_context"]
    assert a["low_confidence_candidate"] == q["low_confidence_need"]
    assert a["heavily_shaped_candidate"] == q["heavily_shaped"]


def test_thin_candidate_true_case():
    a = dict(_thin_trace().memory_plan_sufficiency_advisory)
    assert a["thin_context_candidate"] is True and a["nominal_plan_candidate"] is False


def test_low_confidence_candidate_true_case():
    a = dict(_low_conf_trace().memory_plan_sufficiency_advisory)
    assert a["low_confidence_candidate"] is True and a["nominal_plan_candidate"] is False


def test_heavily_shaped_candidate_true_case():
    a = dict(_heavy_trace().memory_plan_sufficiency_advisory)
    assert a["heavily_shaped_candidate"] is True and a["nominal_plan_candidate"] is False


# ---------------------------------------------------------------------------
# 10. nominal_plan_candidate true only when all three others are false
# ---------------------------------------------------------------------------

def test_nominal_true_only_when_all_others_false():
    a = dict(_nominal_trace().memory_plan_sufficiency_advisory)
    assert (a["thin_context_candidate"], a["low_confidence_candidate"],
            a["heavily_shaped_candidate"]) == (False, False, False)
    assert a["nominal_plan_candidate"] is True


@pytest.mark.parametrize("builder", [_thin_trace, _low_conf_trace, _heavy_trace])
def test_nominal_false_when_any_candidate_true(builder):
    a = dict(builder().memory_plan_sufficiency_advisory)
    assert any([a["thin_context_candidate"], a["low_confidence_candidate"],
                a["heavily_shaped_candidate"]])
    assert a["nominal_plan_candidate"] is False


def test_advisory_depends_only_on_memory_plan_quality():
    # two traces with identical quality-driving inputs but different OTHER fields
    # produce identical advisories -> the advisory is a pure function of quality.
    common = dict(top_k={"core": 6, "relational": 4}, confidence_need=0.0)
    t1 = _trace(weight={"core": 1.0, "relational": 0.85}, ambiguity_score=0.1, **common)
    t2 = _trace(weight={"core": 1.7, "relational": 0.2}, ambiguity_score=0.9,
                action="no_op", **common)
    assert dict(t1.memory_plan_quality) == dict(t2.memory_plan_quality)
    assert dict(t1.memory_plan_sufficiency_advisory) == dict(t2.memory_plan_sufficiency_advisory)


# ---------------------------------------------------------------------------
# 11. direct construction, think(), and runner traces agree
# ---------------------------------------------------------------------------

def _advisory_from_plan(plan, confidence_need):
    t = build_reflection_trace(
        chosen_mode="reflective", action="answer", stance=None,
        review_status_flags={"approved": True},
        top_k_by_lane=plan.top_k_by_lane, weight_by_lane=plan.weight_by_lane,
        geometric_context_present=False, confidence_need=confidence_need,
        memory_plan_shaping_posture=getattr(plan, "_shaping_posture", None),
    )
    return dict(t.memory_plan_sufficiency_advisory)


def test_direct_think_and_runner_agree(monkeypatch):
    monkeypatch.setattr(tc, _REL_FLAG, True)
    monkeypatch.setattr(tc, _AMB_FLAG, True)
    # think() path
    tr_result = ThinkingController().think("ws", "agent", _EL)
    a_think = dict(tr_result.reflection_trace.memory_plan_sufficiency_advisory)
    # direct construction from the SAME effective plan
    a_direct = _advisory_from_plan(tr_result.memory_plan, tr_result.task_frame.confidence_need)
    # runner path
    from torment_service.agent_loop import AgentRunner, Observation, LLMResponse

    class _FakeFabric:
        def ingest(self, *a, **k): return {"status": "ok"}
        def measure_drift(self, *a, **k): return None
        def gravity_correction(self, *a, **k): return None

    class _FakeLLM:
        def complete(self, system_prompt, messages, tools=None): return LLMResponse(text="ok")

    class _FakeTool:
        def execute(self, family, arguments, defaults): return {"output": "x"}

    runner = AgentRunner(controller=ThinkingController(), fabric=_FakeFabric(),
                         llm_client=_FakeLLM(), tool_executor=_FakeTool())
    rr = runner.run_turn(workspace_id="ws", agent_id="agent",
                         observation=Observation(text=_EL, source_type="user_text"), step=1)
    a_runner = dict(rr.reflection_trace.memory_plan_sufficiency_advisory)

    assert a_think == a_direct == a_runner
    # non-vacuous: this input is heavily shaped, so it is NOT nominal
    assert a_think["heavily_shaped_candidate"] is True
    assert a_think["nominal_plan_candidate"] is False


# ---------------------------------------------------------------------------
# 12. JSON trace does not leak raw marker text
# ---------------------------------------------------------------------------

def test_no_raw_user_marker_in_json(monkeypatch):
    monkeypatch.setattr(tc, _REL_FLAG, True)
    monkeypatch.setattr(tc, _AMB_FLAG, True)
    marker = "ZZQ_ADVISORY_MARKER_4T"
    r = ThinkingController().think("ws", "agent", f"maybe remember stuff?? {marker}")
    blob = json.dumps(r.reflection_trace.to_dict())
    assert marker not in blob
    a = r.reflection_trace.to_dict()["memory_plan_sufficiency_advisory"]
    assert set(a.keys()) == _ADVISORY_KEYS
    assert all(type(v) is bool for v in a.values())


# ---------------------------------------------------------------------------
# 13-16. sibling fields' behavior is unchanged
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
    assert dict(t.memory_plan_shaping_posture) == {
        "relational_ambiguity_prominence": True, "ambiguity_context_diversity": False}


def test_memory_plan_quality_behavior_unchanged():
    t = _trace(top_k={"core": 6, "relational": 4, "deep": 3}, confidence_need=0.0)
    q = dict(t.memory_plan_quality)
    assert q["active_lane_count"] == 3 and q["non_core_active_lane_count"] == 2
    assert q["total_lane_budget"] == 13 and q["thin_context"] is False
    assert q["low_confidence_need"] is False and q["shaping_reflex_count"] == 0
    assert q["heavily_shaped"] is False


# ---------------------------------------------------------------------------
# 17. the advisory reaches no prompt/output/tool/fabric/TurnContext/outcome/assim
# ---------------------------------------------------------------------------

class _SpyFabric:
    def __init__(self):
        self.ingest_calls: List[Dict[str, Any]] = []
        self.measure_drift_calls: List[Dict[str, Any]] = []
        self.gravity_correction_calls: List[Dict[str, Any]] = []

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append({"workspace_id": workspace_id, "agent_id": agent_id,
                                  "text": text, "step": step})
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append({"workspace_id": workspace_id, "agent_id": agent_id})
        return None

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append({"workspace_id": workspace_id,
                                              "agent_id": agent_id, "drift_info": drift_info})


class _SpyLLM:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def complete(self, system_prompt, messages, tools=None):
        from torment_service.agent_loop import LLMResponse
        self.calls.append({"system_prompt": system_prompt, "messages": messages, "tools": tools})
        return LLMResponse(text="Plain answer.")


class _SpyTool:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def execute(self, family, arguments, defaults):
        self.calls.append({"family": family, "arguments": arguments, "defaults": defaults})
        return {"output": "tool output"}


def test_advisory_reaches_no_model_or_side_effect_surface(monkeypatch):
    monkeypatch.setattr(tc, _REL_FLAG, True)
    monkeypatch.setattr(tc, _AMB_FLAG, True)
    from torment_service.agent_loop import (
        AgentRunner, Observation, TurnContext, assimilation_outcomes,
    )
    fabric, llm, tool = _SpyFabric(), _SpyLLM(), _SpyTool()
    runner = AgentRunner(controller=ThinkingController(), fabric=fabric,
                         llm_client=llm, tool_executor=tool)
    result = runner.run_turn(workspace_id="ws", agent_id="agent",
                             observation=Observation(text="tell me something interesting",
                                                     source_type="user_text"), step=1)

    def _assert_clean(blob):
        for m in _ADVISORY_MARKERS:
            assert m not in blob

    assert llm.calls, "expected a model call this turn"
    for call in llm.calls:
        _assert_clean(json.dumps(call, default=str))
    for call in fabric.ingest_calls + fabric.measure_drift_calls + fabric.gravity_correction_calls:
        _assert_clean(json.dumps(call, default=str))
    for call in tool.calls:
        _assert_clean(json.dumps(call, default=str))

    # execution outcome carries no advisory / no trace field
    eo = result.execution_outcome
    assert not hasattr(eo, "reflection_trace")
    _assert_clean(json.dumps({"response_text": eo.response_text,
                              "tool_result": eo.tool_result}, default=str))

    # TurnContext + assimilation carry no advisory channel
    names = {f.name for f in dataclasses.fields(TurnContext)}
    assert "reflection_trace" not in names
    ctx = TurnContext(workspace_id="ws", agent_id="ag")
    assert assimilation_outcomes(ctx) == []
    _assert_clean(json.dumps(result.assimilation_outcomes, default=str))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
