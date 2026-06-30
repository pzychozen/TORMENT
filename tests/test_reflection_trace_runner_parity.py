"""
tests/test_reflection_trace_runner_parity.py — runner-path ReflectionTrace parity.

Codex-approved bounded slice: ``AgentRunner.run_turn()`` now attaches an
observation-only ``ReflectionTrace`` to ``TurnResult``, built from
already-computed runner locals after review, using the Phase-5 *effective*
action. These tests lock the parity guarantees and the boundaries that must
remain parked:

  - the trace is present on ``TurnResult`` with ``scope="per_turn_ephemeral"``;
  - it tracks the Phase-5 *effective* action (``action_policy_decision``), not
    the Phase-4 deliberation action, when policy downgrades the action;
  - ``review_status_flags`` carry only the five coarse booleans — no
    notes / revised_text / response text;
  - ``TurnContext`` does not gain a ``reflection_trace`` and the Phase-7
    assimilation dispatcher has no channel to consume one;
  - no trace object or marker reaches fabric (ingest / measure_drift /
    gravity_correction), the LLM (system prompt / messages / tools), the tool
    executor, or the execution outcome;
  - repeated turns produce independent trace objects;
  - ``agent_loop.py`` never *reads* ``.reflection_trace`` — construction is a
    constructor keyword, so the production non-reentry source scan in
    ``test_reflection_trace.py`` stays green without modification.

Companion guarantees (unchanged here, asserted in ``test_reflection_trace.py``):
the model-visible absence tests (``/agent/query``, ``/retrieve``) and the
``reflection_trace.py`` writer/storage-free AST lock remain green because this
slice touches neither surface.
"""
from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from torment_service.agent_loop import (
    AgentRunner,
    LLMResponse,
    Observation,
    TurnContext,
    TurnResult,
    assimilation_outcomes,
)
from torment_service.reflection_trace import ReflectionTrace
from torment_service.thinking_controller import ThinkingController

_SERVICE_DIR = Path(__file__).resolve().parents[1] / "torment_service"
_MARKERS = ("reflection_trace", "per_turn_ephemeral")


# ---------------------------------------------------------------------------
# Recording spies — capture every value handed to a side-effecting dependency
# ---------------------------------------------------------------------------


class SpyFabric:
    """FabricHandle double that records every call's arguments."""

    def __init__(self, drift_return: Optional[Dict[str, Any]] = None):
        self.drift_return = drift_return
        self.ingest_calls: List[Dict[str, Any]] = []
        self.measure_drift_calls: List[Dict[str, Any]] = []
        self.gravity_correction_calls: List[Dict[str, Any]] = []

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id,
             "text": text, "step": step}
        )
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id}
        )
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id,
             "drift_info": drift_info}
        )


class SpyLLM:
    """LLMClient double that records every complete() call."""

    def __init__(self, canned: str = "Fake response."):
        self.canned = canned
        self.calls: List[Dict[str, Any]] = []

    def complete(self, system_prompt, messages, tools=None):
        self.calls.append(
            {"system_prompt": system_prompt, "messages": messages, "tools": tools}
        )
        return LLMResponse(text=self.canned)


class SpyToolExecutor:
    """ToolExecutor double that records every execute() call."""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def execute(self, family, arguments, defaults):
        self.calls.append(
            {"family": family, "arguments": arguments, "defaults": defaults}
        )
        return {"output": "tool output"}


def _make_runner(drift_return=None, canned="Hi."):
    fabric = SpyFabric(drift_return=drift_return)
    llm = SpyLLM(canned=canned)
    tool = SpyToolExecutor()
    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
        tool_executor=tool,
    )
    return runner, fabric, llm, tool


def _run(runner, text="Hello", source_type="user_text", step=1) -> TurnResult:
    return runner.run_turn(
        workspace_id="ws",
        agent_id="agent",
        observation=Observation(text=text, source_type=source_type),
        step=step,
    )


# ---------------------------------------------------------------------------
# 1. Trace present on TurnResult with ephemeral scope; shape mirrors locals
# ---------------------------------------------------------------------------


class TestTracePresentOnTurnResult:
    def test_run_turn_attaches_trace_with_ephemeral_scope(self):
        runner, *_ = _make_runner()
        result = _run(runner)
        assert isinstance(result, TurnResult)
        assert isinstance(result.reflection_trace, ReflectionTrace)
        assert result.reflection_trace.scope == "per_turn_ephemeral"

    def test_trace_shape_matches_runner_locals(self):
        runner, *_ = _make_runner()
        result = _run(runner)
        rt = result.reflection_trace
        # decision identity — effective (Phase 5) action, surfaced via policy
        assert rt.chosen_mode == result.mode_decision.chosen_mode.value
        assert rt.action == result.action_policy_decision.action.action.value
        # the runner has no geometric context local; must not be invented
        assert rt.geometric_context_present is False
        # mode shape
        assert rt.allowed_depth == result.mode_decision.allowed_depth
        assert rt.requires_self_review == result.mode_decision.requires_self_review
        assert rt.may_escalate == result.mode_decision.may_escalate
        assert rt.confidence_floor == result.mode_decision.confidence_floor
        # frame shape
        f = result.task_frame
        assert rt.source_type == f.source_type
        assert rt.action_need == f.action_need
        assert rt.memory_need == f.memory_need
        assert rt.tool_need == f.tool_need
        assert rt.governance_sensitive == f.governance_sensitive
        assert rt.identity_sensitive == f.identity_sensitive
        assert rt.live_social == f.live_social
        assert rt.urgency == f.urgency
        assert rt.ambiguity_score == f.ambiguity_score
        assert rt.confidence_need == f.confidence_need

    def test_lane_weight_shape_matches_effective_memory_plan(self):
        # runner path populates lane_weight_shape ONLY from the effective
        # MemoryPlan.weight_by_lane (content-free lane->weight numbers).
        runner, *_ = _make_runner()
        result = _run(runner)
        rt = result.reflection_trace
        expected = {
            str(k): float(v)
            for k, v in result.memory_plan.weight_by_lane.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        }
        assert dict(rt.lane_weight_shape) == expected
        assert all(isinstance(v, float) for v in rt.lane_weight_shape.values())


# ---------------------------------------------------------------------------
# 2. Trace tracks the Phase-5 EFFECTIVE action, not the Phase-4 action
# ---------------------------------------------------------------------------


class TestTraceTracksEffectiveAction:
    def test_drift_veto_downgrade_is_reflected_in_trace(self):
        # FAST mode's legal set is {ANSWER, NO_OP} (no DEFER). High away-seed
        # drift triggers the Phase-5 drift veto, which — unable to fall back to
        # DEFER — downgrades the Phase-4 ANSWER to NO_OP. The trace must follow
        # the effective NO_OP, not the original ANSWER.
        runner, *_ = _make_runner(
            drift_return={"drift_score": -0.5, "drift_direction": "away_seed"},
        )
        result = _run(runner, text="Hello")

        # sanity: a real Phase-4 → Phase-5 divergence occurred
        assert result.action_decision.action.value == "answer"
        assert result.action_policy_decision.action.action.value == "no_op"
        assert result.action_policy_decision.drift_veto_applied is True

        # the trace tracks the EFFECTIVE action, never the original
        assert result.reflection_trace.action == "no_op"
        assert result.reflection_trace.action != result.action_decision.action.value
        # requires_execution likewise comes from the effective action
        assert (
            result.reflection_trace.requires_execution
            == result.action_policy_decision.action.requires_execution
        )


# ---------------------------------------------------------------------------
# 3. review_status_flags are the five coarse booleans only — no content
# ---------------------------------------------------------------------------


class TestReviewFlagsAreCoarseOnly:
    _ALLOWED = {"approved", "revised", "escalate", "ask_user", "blocked"}

    def test_review_status_flags_keys_exact(self):
        runner, *_ = _make_runner()
        flags = _run(runner).reflection_trace.to_dict()["review_status_flags"]
        assert set(flags.keys()) == self._ALLOWED
        assert all(isinstance(v, bool) for v in flags.values())

    def test_review_status_flags_match_review_outcome(self):
        runner, *_ = _make_runner()
        result = _run(runner)
        ro = result.review_outcome
        flags = result.reflection_trace.to_dict()["review_status_flags"]
        assert flags == {
            "approved": bool(ro.approved),
            "revised": bool(ro.revised),
            "escalate": bool(ro.escalate),
            "ask_user": bool(ro.ask_user),
            "blocked": bool(ro.blocked),
        }

    def test_no_review_text_notes_or_draft_in_trace(self):
        # The canned response text must never appear in the trace, and the
        # trace must expose none of review's free-text surfaces as keys.
        secret = "TOPSECRET_DRAFT_ABC123"
        runner, *_ = _make_runner(canned=secret)
        d = _run(runner, text="Tell me something").reflection_trace.to_dict()
        assert secret not in json.dumps(d)
        for banned in ("notes", "revised_text", "response_draft", "reason", "payload"):
            assert banned not in d


# ---------------------------------------------------------------------------
# 4/5. TurnContext gains no trace; assimilation cannot consume one
# ---------------------------------------------------------------------------


class TestTurnContextAndAssimilationParked:
    def test_turncontext_dataclass_has_no_reflection_trace_field(self):
        names = {f.name for f in dataclasses.fields(TurnContext)}
        assert "reflection_trace" not in names

    def test_constructed_turncontext_has_no_trace_attr(self):
        ctx = TurnContext(workspace_id="ws", agent_id="ag")
        assert not hasattr(ctx, "reflection_trace")

    def test_assimilation_outcomes_has_no_trace_channel(self):
        # assimilation_outcomes takes only a TurnContext (no trace field), so it
        # cannot consume the reflection trace. Even a smuggled metadata entry is
        # not acted on (the dispatcher returns [] in v0.1).
        ctx = TurnContext(workspace_id="ws", agent_id="ag")
        assert assimilation_outcomes(ctx) == []
        ctx.metadata["reflection_trace"] = "smuggled"
        assert assimilation_outcomes(ctx) == []


# ---------------------------------------------------------------------------
# 6. No trace object or marker reaches any side-effecting dependency
# ---------------------------------------------------------------------------


class TestNoTraceLeakIntoSideEffects:
    def test_no_marker_or_trace_object_reaches_dependencies(self):
        runner, fabric, llm, tool = _make_runner(canned="Plain answer.")
        result = _run(runner, text="Tell me something interesting")
        trace = result.reflection_trace
        assert trace is not None

        # fabric.ingest — text carries no markers; no value is the trace object
        for call in fabric.ingest_calls:
            for m in _MARKERS:
                assert m not in call["text"]
            for v in call.values():
                assert v is not trace

        # measure_drift / gravity_correction — args carry no trace
        for call in fabric.measure_drift_calls + fabric.gravity_correction_calls:
            blob = json.dumps(call, default=str)
            for m in _MARKERS:
                assert m not in blob
            for v in call.values():
                assert v is not trace

        # LLM — system prompt, messages, tools carry no markers/object
        for call in llm.calls:
            blob = json.dumps(call, default=str)
            for m in _MARKERS:
                assert m not in blob
            assert call["system_prompt"] is not trace
            assert call["messages"] is not trace
            assert call["tools"] is not trace

        # tool executor — no trace reached execution
        for call in tool.calls:
            blob = json.dumps(call, default=str)
            for m in _MARKERS:
                assert m not in blob

        # execution outcome — no trace field, no markers
        eo = result.execution_outcome
        assert not hasattr(eo, "reflection_trace")
        blob = json.dumps(
            {"response_text": eo.response_text, "tool_result": eo.tool_result},
            default=str,
        )
        for m in _MARKERS:
            assert m not in blob


# ---------------------------------------------------------------------------
# 7. Independence across turns (no shared object, no accumulation)
# ---------------------------------------------------------------------------


class TestTraceIndependenceAcrossTurns:
    def test_repeated_turns_produce_independent_traces(self):
        runner, *_ = _make_runner()
        r1 = _run(runner, text="one", step=1)
        r2 = _run(runner, text="two", step=2)
        assert r1.reflection_trace is not r2.reflection_trace

    def test_many_turns_have_distinct_identities(self):
        runner, *_ = _make_runner()
        traces = [
            _run(runner, text=f"msg {i}", step=i).reflection_trace
            for i in range(10)
        ]
        assert len({id(t) for t in traces}) == 10


# ---------------------------------------------------------------------------
# 8. agent_loop.py builds the trace but never READS .reflection_trace
# ---------------------------------------------------------------------------


class TestAgentLoopNeverReadsTrace:
    def test_agent_loop_has_no_reflection_trace_attribute_read(self):
        # Parity guarantee: the runner constructs the trace via a keyword and
        # never reads it back, so the production non-reentry scan in
        # test_reflection_trace.py stays green WITHOUT modification.
        tree = ast.parse(
            (_SERVICE_DIR / "agent_loop.py").read_text(encoding="utf-8"),
            filename="agent_loop.py",
        )
        reads = sorted(
            n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.Attribute) and n.attr == "reflection_trace"
        )
        assert reads == [], (
            f"agent_loop.py reads .reflection_trace at lines {reads}; "
            "construction must be keyword-only to satisfy the non-reentry scan"
        )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
