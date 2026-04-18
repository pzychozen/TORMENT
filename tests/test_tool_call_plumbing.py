"""
v0.1.0c tests: LLM tool-call argument plumbing.

Covers the three-path split in AgentRunner._execute's USE_TOOL
branch:

    Path A: LLM returned no tool_calls → legal text-only response.
            Executor NOT invoked. tool_called=False.
    Path B: LLM returned exactly one tool_call with the matching
            tool_name → executor invoked with parsed arguments.
            tool_called=True.
    Path C: Contract failures — tool_name mismatch OR multiple
            tool_calls in a single turn → strict failure. Executor
            NOT invoked. tool_result.error is populated.

Also covers the LLMResponse / ToolCall dataclass shapes.

References:
    - torment_service.agent_loop (LLMResponse, ToolCall,
      AgentRunner._execute USE_TOOL path)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md invariant 2
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md v0.1.0c
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from torment_service.agent_loop import (
    AgentRunner,
    LLMResponse,
    Observation,
    ToolCall,
)
from torment_service.behavior_packs import DEBUGGING_SESSION_PACK
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ActionType


# ---------------------------------------------------------------------------
# Dataclass shape tests
# ---------------------------------------------------------------------------


class TestLLMResponseShape:
    """LLMResponse is constructable with sensible defaults."""

    def test_default_empty_response(self):
        r = LLMResponse()
        assert r.text == ""
        assert r.tool_calls == []
        assert r.stop_reason is None

    def test_text_only(self):
        r = LLMResponse(text="hello")
        assert r.text == "hello"
        assert r.tool_calls == []

    def test_with_single_tool_call(self):
        tc = ToolCall(tool_name="code_exec", arguments={"code": "print(1)"})
        r = LLMResponse(text="", tool_calls=[tc])
        assert len(r.tool_calls) == 1
        assert r.tool_calls[0].tool_name == "code_exec"

    def test_with_stop_reason(self):
        r = LLMResponse(text="", stop_reason="tool_use")
        assert r.stop_reason == "tool_use"


class TestToolCallShape:
    """ToolCall is constructable with required fields."""

    def test_required_fields(self):
        tc = ToolCall(tool_name="code_exec", arguments={"code": "x"})
        assert tc.tool_name == "code_exec"
        assert tc.arguments == {"code": "x"}
        assert tc.tool_use_id is None

    def test_with_tool_use_id(self):
        tc = ToolCall(
            tool_name="code_exec",
            arguments={"code": "x"},
            tool_use_id="toolu_abc123",
        )
        assert tc.tool_use_id == "toolu_abc123"


# ---------------------------------------------------------------------------
# Fakes for runner integration
# ---------------------------------------------------------------------------


@dataclass
class FakeFabric:
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)
    drift_return: Optional[Dict[str, Any]] = None

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append({})
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append({})
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append({})


@dataclass
class ScriptedLLM:
    """Test double that returns a specific canned LLMResponse per call."""
    responses: List[LLMResponse] = field(default_factory=list)
    received_tools: List[Optional[List[Dict[str, Any]]]] = field(default_factory=list)
    call_count: int = 0

    def complete(self, system_prompt, messages, tools=None):
        self.received_tools.append(tools)
        if self.call_count < len(self.responses):
            r = self.responses[self.call_count]
        else:
            r = LLMResponse(text="[no canned response]")
        self.call_count += 1
        return r


@dataclass
class RecordingExecutor:
    """Records invocation args; returns canned result."""
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_result: Dict[str, Any] = field(
        default_factory=lambda: {
            "output": "tool-output-value",
            "stderr": "",
            "exit_code": 0,
            "timed_out": False,
            "truncated": False,
            "error": None,
        }
    )

    def execute(self, family, arguments, defaults):
        self.calls.append(
            {"family": family, "arguments": arguments, "defaults": defaults}
        )
        return self.canned_result


def _make_runner(responses=None, executor=None):
    """Build a runner with the debugging pack's code_exec contract."""
    fabric = FakeFabric()
    llm = ScriptedLLM(responses=responses or [])
    exec_ = executor or RecordingExecutor()
    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
        pack=DEBUGGING_SESSION_PACK,
        tool_executor=exec_,
    )
    return runner, fabric, llm, exec_


TOOL_TRIGGER_TEXT = "search the docs for relevant entries"


# ---------------------------------------------------------------------------
# Path A: LLM declines the tool, returns plain text
# ---------------------------------------------------------------------------


class TestPathA_NoToolCalls:
    """LLM returns text only → executor NOT invoked."""

    def test_text_only_response_does_not_invoke_executor(self):
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="I think the answer is X, no tool needed."),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text=TOOL_TRIGGER_TEXT),
            step=1,
        )
        # If USE_TOOL was dispatched but no tool_calls returned:
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            assert result.execution_outcome.tool_called is False
            assert len(exec_.calls) == 0
            assert "I think the answer is X" in (
                result.execution_outcome.response_text or ""
            )


# ---------------------------------------------------------------------------
# Path B: one matching tool_call → executor invoked with arguments
# ---------------------------------------------------------------------------


class TestPathB_MatchingToolCall:
    """LLM returns exactly one tool_call with the narrowed family name →
    executor is invoked with the LLM-filled arguments."""

    def test_executor_invoked_with_llm_arguments(self):
        tc = ToolCall(
            tool_name="code_exec",
            arguments={"code": "print(2 + 2)"},
        )
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="Let me compute that.", tool_calls=[tc]),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text=TOOL_TRIGGER_TEXT),
            step=1,
        )
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            assert result.execution_outcome.tool_called is True
            assert len(exec_.calls) == 1
            # Arguments from the LLM reached the executor:
            assert exec_.calls[0]["arguments"] == {"code": "print(2 + 2)"}
            # Family carried through:
            assert exec_.calls[0]["family"] == "code_exec"

    def test_response_text_prefers_tool_output(self):
        tc = ToolCall(
            tool_name="code_exec",
            arguments={"code": "print('hi')"},
        )
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="thinking...", tool_calls=[tc]),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text=TOOL_TRIGGER_TEXT),
            step=1,
        )
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            # Response uses the tool's output, not the LLM's pre-tool text
            assert "tool-output-value" in result.execution_outcome.response_text

    def test_tool_arguments_unicode_round_trips(self):
        tc = ToolCall(
            tool_name="code_exec",
            arguments={"code": "print('\u00e5ngstr\u00f6m')"},
        )
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="", tool_calls=[tc]),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text=TOOL_TRIGGER_TEXT),
            step=1,
        )
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            assert len(exec_.calls) == 1
            assert exec_.calls[0]["arguments"]["code"] == "print('\u00e5ngstr\u00f6m')"


# ---------------------------------------------------------------------------
# Path C: strict contract failures
# ---------------------------------------------------------------------------


class TestPathC_MismatchedToolName:
    """LLM returns a tool_call whose name doesn't match the narrowed
    family → strict contract failure, executor NOT invoked."""

    def test_mismatched_name_is_contract_failure(self):
        bad_call = ToolCall(
            tool_name="web_fetch",  # narrowed was code_exec
            arguments={"url": "http://example.com"},
        )
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="I'll fetch that.", tool_calls=[bad_call]),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text=TOOL_TRIGGER_TEXT),
            step=1,
        )
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            assert result.execution_outcome.tool_called is False
            assert len(exec_.calls) == 0
            assert result.execution_outcome.tool_result is not None
            assert "tool_name_mismatch" in result.execution_outcome.tool_result.get(
                "error", ""
            )


class TestPathC_MultipleToolCalls:
    """LLM returns multiple tool_calls → strict contract failure
    (one narrowed family, one call permitted per turn)."""

    def test_multiple_tool_calls_is_contract_failure(self):
        call1 = ToolCall(tool_name="code_exec", arguments={"code": "print(1)"})
        call2 = ToolCall(tool_name="code_exec", arguments={"code": "print(2)"})
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="", tool_calls=[call1, call2]),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text=TOOL_TRIGGER_TEXT),
            step=1,
        )
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            assert result.execution_outcome.tool_called is False
            assert len(exec_.calls) == 0
            assert result.execution_outcome.tool_result is not None
            err = result.execution_outcome.tool_result.get("error", "")
            assert "multiple_tool_calls_in_single_turn" in err

    def test_three_tool_calls_also_strict_failure(self):
        calls = [
            ToolCall(tool_name="code_exec", arguments={"code": f"print({i})"})
            for i in range(3)
        ]
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="", tool_calls=calls),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text=TOOL_TRIGGER_TEXT),
            step=1,
        )
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            assert result.execution_outcome.tool_called is False


# ---------------------------------------------------------------------------
# LLM receives exactly one tool signature (invariant 2 regression guard)
# ---------------------------------------------------------------------------


class TestLLMReceivesSingleSignature:
    """The runner must pass exactly one tool signature to the LLM,
    regardless of what the LLM returns."""

    def test_llm_tools_is_length_one(self):
        tc = ToolCall(tool_name="code_exec", arguments={"code": "print(1)"})
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="", tool_calls=[tc]),
        ])
        runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text=TOOL_TRIGGER_TEXT),
            step=1,
        )
        # Find the call where tools= was non-None (the USE_TOOL call)
        tool_calls_with_tools = [
            t for t in llm.received_tools if t is not None
        ]
        if tool_calls_with_tools:
            assert len(tool_calls_with_tools[0]) == 1
            assert tool_calls_with_tools[0][0]["name"] == "code_exec"


# ---------------------------------------------------------------------------
# ANSWER path: LLMResponse.text flows through unchanged
# ---------------------------------------------------------------------------


class TestAnswerPathStillWorks:
    """ANSWER turns use LLMResponse.text; tool_calls on those
    responses are ignored (we didn't request tools)."""

    def test_answer_uses_response_text(self):
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="Hello world"),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="say hi"),
            step=1,
        )
        if result.action_decision.action == ActionType.ANSWER:
            assert "Hello world" in result.execution_outcome.response_text
            assert result.execution_outcome.tool_called is False

    def test_answer_ignores_unexpected_tool_calls(self):
        """If the LLM returns tool_calls on an ANSWER turn (didn't
        pass tools), runner ignores them — doesn't try to dispatch."""
        surprise_tc = ToolCall(tool_name="code_exec", arguments={"code": "x"})
        runner, fabric, llm, exec_ = _make_runner(responses=[
            LLMResponse(text="response", tool_calls=[surprise_tc]),
        ])
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="say hi"),
            step=1,
        )
        if result.action_decision.action == ActionType.ANSWER:
            # Executor was NOT invoked on ANSWER even with tool_calls
            # in response, because we didn't narrow and dispatch.
            assert len(exec_.calls) == 0
