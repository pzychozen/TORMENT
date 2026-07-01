"""tests/test_reflection_trace_memory_plan_observability_parity.py

Runner-vs-think() ReflectionTrace observability parity for the MemoryPlan shaping
posture and its posture-derived quality fields.

Fix under test: ``AgentRunner.run_turn()`` now forwards
``bundle.memory_plan._shaping_posture`` into ``build_reflection_trace(...)`` (mirroring
``ThinkingController.think()``). Previously the runner trace defaulted the posture to
both-False, so ``memory_plan_quality.shaping_reflex_count`` / ``heavily_shaped``
under-reported shaping intensity even when the effective plan WAS shaped.

This locks:
  - the runner trace and the direct think()/ReflectionTrace path agree on
    memory_plan_shaping_posture, memory_plan_quality.shaping_reflex_count /
    heavily_shaped, lane_budget_shape, and lane_weight_shape;
  - the posture/quality observation never leaks into a model-visible or
    side-effecting surface (LLM prompt/messages, fabric ingest/drift/gravity, the
    tool executor, TurnContext, the execution outcome, or assimilation), and no raw
    user marker text reaches the runner trace JSON.
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Dict, List

import pytest

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.agent_loop import (
    AgentRunner,
    LLMResponse,
    Observation,
    TurnContext,
    TurnResult,
    assimilation_outcomes,
)

_REL_FLAG = "_RELATIONAL_AMBIGUITY_PROMINENCE_V1_ENABLE"
_AMB_FLAG = "_AMBIGUITY_CONTEXT_DIVERSITY_V1_ENABLE"
# high ambiguity (maybe + stuff + "??") + memory_need ("remember") -> relational
# lane enabled and both shapers eligible.
_EL = "maybe remember stuff??"

# Internal observation identifiers that must never reach model / side-effect surfaces.
_LEAK_MARKERS = (
    "_shaping_posture",
    "memory_plan_shaping_posture",
    "memory_plan_quality",
    "shaping_reflex_count",
    "heavily_shaped",
)


# ---------------------------------------------------------------------------
# recording spies (mirror tests/test_reflection_trace_runner_parity.py)
# ---------------------------------------------------------------------------

class SpyFabric:
    def __init__(self):
        self.ingest_calls: List[Dict[str, Any]] = []
        self.measure_drift_calls: List[Dict[str, Any]] = []
        self.gravity_correction_calls: List[Dict[str, Any]] = []

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id, "text": text, "step": step}
        )
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append({"workspace_id": workspace_id, "agent_id": agent_id})
        return None

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id, "drift_info": drift_info}
        )


class SpyLLM:
    def __init__(self, canned="Fake response."):
        self.canned = canned
        self.calls: List[Dict[str, Any]] = []

    def complete(self, system_prompt, messages, tools=None):
        self.calls.append({"system_prompt": system_prompt, "messages": messages, "tools": tools})
        return LLMResponse(text=self.canned)


class SpyToolExecutor:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def execute(self, family, arguments, defaults):
        self.calls.append({"family": family, "arguments": arguments, "defaults": defaults})
        return {"output": "tool output"}


def _make_runner(canned="Hi."):
    fabric, llm, tool = SpyFabric(), SpyLLM(canned=canned), SpyToolExecutor()
    runner = AgentRunner(
        controller=ThinkingController(), fabric=fabric, llm_client=llm, tool_executor=tool
    )
    return runner, fabric, llm, tool


def _run(runner, text="Hello", source_type="user_text", step=1) -> TurnResult:
    return runner.run_turn(
        workspace_id="ws", agent_id="agent",
        observation=Observation(text=text, source_type=source_type), step=step,
    )


def _enable(monkeypatch):
    monkeypatch.setattr(tc, _REL_FLAG, True)
    monkeypatch.setattr(tc, _AMB_FLAG, True)


# ---------------------------------------------------------------------------
# parity: runner trace agrees with think()/ReflectionTrace
# ---------------------------------------------------------------------------

def test_runner_matches_think_on_posture_and_derived_quality(monkeypatch):
    _enable(monkeypatch)
    tr = ThinkingController().think("ws", "agent", _EL).reflection_trace
    runner, *_ = _make_runner()
    rr = _run(runner, text=_EL).reflection_trace

    # precondition: shaping actually fired both ways (non-vacuous parity)
    assert dict(tr.memory_plan_shaping_posture) == {
        "relational_ambiguity_prominence": True,
        "ambiguity_context_diversity": True,
    }

    # posture parity
    assert dict(rr.memory_plan_shaping_posture) == dict(tr.memory_plan_shaping_posture)
    # posture-derived quality parity
    assert rr.memory_plan_quality["shaping_reflex_count"] == 2
    assert tr.memory_plan_quality["shaping_reflex_count"] == 2
    assert rr.memory_plan_quality["heavily_shaped"] is True
    assert tr.memory_plan_quality["heavily_shaped"] is True
    # lane shape parity
    assert dict(rr.lane_budget_shape) == dict(tr.lane_budget_shape)
    assert dict(rr.lane_weight_shape) == dict(tr.lane_weight_shape)


def test_runner_trace_posture_matches_effective_plan_attribute(monkeypatch):
    _enable(monkeypatch)
    runner, *_ = _make_runner()
    result = _run(runner, text=_EL)
    plan_posture = getattr(result.memory_plan, "_shaping_posture", None)
    assert plan_posture is not None
    assert dict(result.reflection_trace.memory_plan_shaping_posture) == dict(plan_posture)


def test_without_shapers_both_paths_report_zero_shaping(monkeypatch):
    # flags off (default): both paths report the same empty posture / zero quality.
    monkeypatch.setattr(tc, _REL_FLAG, False)
    monkeypatch.setattr(tc, _AMB_FLAG, False)
    tr = ThinkingController().think("ws", "agent", _EL).reflection_trace
    runner, *_ = _make_runner()
    rr = _run(runner, text=_EL).reflection_trace
    assert dict(rr.memory_plan_shaping_posture) == dict(tr.memory_plan_shaping_posture)
    assert rr.memory_plan_quality["shaping_reflex_count"] == 0
    assert rr.memory_plan_quality["heavily_shaped"] is False


# ---------------------------------------------------------------------------
# no raw user marker text leaks into the runner trace JSON
# ---------------------------------------------------------------------------

def test_no_raw_user_marker_leaks_into_runner_trace_json(monkeypatch):
    _enable(monkeypatch)
    marker = "ZZQ_RUNNER_MARKER_8W"
    runner, *_ = _make_runner()
    r = _run(runner, text=f"maybe remember stuff?? {marker}")
    assert marker not in json.dumps(r.reflection_trace.to_dict())


# ---------------------------------------------------------------------------
# the posture/quality observation reaches no model / side-effect surface
# ---------------------------------------------------------------------------

def test_posture_quality_markers_do_not_reach_llm(monkeypatch):
    _enable(monkeypatch)
    runner, fabric, llm, tool = _make_runner(canned="Plain answer.")
    _run(runner, text="tell me something interesting")
    assert llm.calls, "expected a model call this turn"
    for call in llm.calls:
        blob = json.dumps(call, default=str)
        for m in _LEAK_MARKERS:
            assert m not in blob


def test_posture_quality_markers_do_not_reach_fabric_tool_or_outcome(monkeypatch):
    _enable(monkeypatch)
    runner, fabric, llm, tool = _make_runner(canned="Plain answer.")
    result = _run(runner, text="tell me something interesting")
    trace = result.reflection_trace

    # fabric.ingest — text/args carry no marker; no value is the trace object
    for call in fabric.ingest_calls:
        blob = json.dumps(call, default=str)
        for m in _LEAK_MARKERS:
            assert m not in blob
        for v in call.values():
            assert v is not trace

    # measure_drift / gravity_correction
    for call in fabric.measure_drift_calls + fabric.gravity_correction_calls:
        blob = json.dumps(call, default=str)
        for m in _LEAK_MARKERS:
            assert m not in blob

    # tool executor
    for call in tool.calls:
        blob = json.dumps(call, default=str)
        for m in _LEAK_MARKERS:
            assert m not in blob

    # execution outcome — no trace field, no markers
    eo = result.execution_outcome
    assert not hasattr(eo, "reflection_trace")
    blob = json.dumps(
        {"response_text": eo.response_text, "tool_result": eo.tool_result}, default=str
    )
    for m in _LEAK_MARKERS:
        assert m not in blob


def test_posture_quality_markers_do_not_reach_turncontext_or_assimilation(monkeypatch):
    # TurnContext has no reflection_trace/posture channel
    names = {f.name for f in dataclasses.fields(TurnContext)}
    assert "reflection_trace" not in names
    ctx = TurnContext(workspace_id="ws", agent_id="ag")
    assert not hasattr(ctx, "reflection_trace")
    assert assimilation_outcomes(ctx) == []
    ctx.metadata["memory_plan_shaping_posture"] = "smuggled"
    assert assimilation_outcomes(ctx) == []  # dispatcher does not act on it

    # a real turn's assimilation outcomes carry no marker either
    _enable(monkeypatch)
    runner, *_ = _make_runner()
    result = _run(runner, text=_EL)
    blob = json.dumps(result.assimilation_outcomes, default=str)
    for m in _LEAK_MARKERS:
        assert m not in blob


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
