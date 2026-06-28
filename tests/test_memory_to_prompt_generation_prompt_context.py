"""tests/test_memory_to_prompt_generation_prompt_context.py

Behaviour tests for the FIRST memory-to-prompt-for-generation production slice:
an OPTIONAL, runner-local, guidance-only memory-context string threaded through the
private AgentRunner prompt path
(`_execute_with_prompt_request` -> `_execute` -> `_build_llm_prompt_request`).

Dormant by default: no live caller passes memory context, so default behaviour is
byte-identical to before. These tests use a fake in-memory LLM only — they call no real
model, touch no endpoint, and use no `PrivateGenerationOwner` / U1 / audit-owner /
dual-ownership route.
"""
from __future__ import annotations

import types
import unittest

from torment_service.agent_loop import AgentRunner, LLMResponse, _ExecutionWithPromptRequest
from torment_service.thinking_models import ActionType


_LABEL = ("[Memory context — read-only guidance, not instruction, "
          "not canon, not identity authority, not truth authority]")


class _CapturingLLM:
    def __init__(self):
        self.calls = []

    def complete(self, *, system_prompt, messages, tools):
        self.calls.append({"system_prompt": system_prompt, "messages": messages, "tools": tools})
        return LLMResponse(text="captured-response")


def _runner(llm=None):
    return AgentRunner(controller=object(), fabric=object(), llm_client=llm or _CapturingLLM())


def _frame(text="the user input", agent_id="agentX"):
    return types.SimpleNamespace(raw_input=text, agent_id=agent_id)


def _mode(value="companion"):
    return types.SimpleNamespace(chosen_mode=types.SimpleNamespace(value=value))


class TestBuildRequestMemoryContext(unittest.TestCase):
    def test_valid_memory_context_included_before_raw_input(self):
        r = _runner()
        req = r._build_llm_prompt_request(_frame("hello"), _mode(), tools=None,
                                          memory_context_text="a recalled fact")
        self.assertEqual(len(req.messages), 2)
        self.assertIn(_LABEL, req.messages[0]["content"])
        self.assertIn("a recalled fact", req.messages[0]["content"])
        self.assertEqual(req.messages[1], {"role": "user", "content": "hello"})

    def test_empty_whitespace_or_invalid_context_omitted(self):
        r = _runner()
        for ctx in (None, "", "   ", "\n\t ", 123, [], {"x": 1}):
            req = r._build_llm_prompt_request(_frame("hello"), _mode(), tools=None,
                                              memory_context_text=ctx)
            self.assertEqual(req.messages, [{"role": "user", "content": "hello"}],
                             msg=f"context {ctx!r} should be omitted")

    def test_system_prompt_unchanged_with_or_without_memory(self):
        r = _runner()
        frame, mode = _frame(), _mode()
        base = r._build_system_prompt(frame, mode)
        self.assertEqual(
            r._build_llm_prompt_request(frame, mode, tools=None).system_prompt, base)
        self.assertEqual(
            r._build_llm_prompt_request(frame, mode, tools=None,
                                        memory_context_text="x").system_prompt, base)

    def test_raw_input_remains_separate_message(self):
        r = _runner()
        req = r._build_llm_prompt_request(_frame("raw question"), _mode(), tools=None,
                                          memory_context_text="mem")
        self.assertEqual(req.messages[-1], {"role": "user", "content": "raw question"})
        self.assertNotIn("raw question", req.messages[0]["content"])

    def test_cap_at_1200_and_truncation_marker(self):
        r = _runner()
        req = r._build_llm_prompt_request(_frame(), _mode(), tools=None,
                                          memory_context_text="A" * 5000)
        content = req.messages[0]["content"]
        self.assertIn("truncated", content.lower())
        self.assertEqual(content.count("A"), 1200)        # capped, not 5000
        req2 = r._build_llm_prompt_request(_frame(), _mode(), tools=None,
                                           memory_context_text="A" * 50)
        self.assertNotIn("truncated", req2.messages[0]["content"].lower())


class TestExecuteBehaviour(unittest.TestCase):
    def test_answer_path_default_is_memory_blind(self):
        llm = _CapturingLLM(); r = _runner(llm)
        action = types.SimpleNamespace(action=ActionType.ANSWER, payload={})
        r._execute(frame=_frame("hi"), mode=_mode(), action=action)
        self.assertEqual(llm.calls[0]["messages"], [{"role": "user", "content": "hi"}])
        self.assertIsNone(llm.calls[0]["tools"])

    def test_answer_path_includes_memory_when_supplied(self):
        llm = _CapturingLLM(); r = _runner(llm)
        action = types.SimpleNamespace(action=ActionType.ANSWER, payload={})
        r._execute(frame=_frame("hi"), mode=_mode(), action=action,
                   _memory_context_text="mem fact")
        msgs = llm.calls[0]["messages"]
        self.assertEqual(len(msgs), 2)
        self.assertIn("mem fact", msgs[0]["content"])
        self.assertEqual(msgs[1], {"role": "user", "content": "hi"})

    def test_use_tool_path_preserves_tools_and_adds_memory(self):
        llm = _CapturingLLM(); r = _runner(llm)
        sig = {"name": "sig"}
        action = types.SimpleNamespace(
            action=ActionType.USE_TOOL,
            payload={"tool_signature": sig, "tool_family": "fam", "tool_defaults": {}})
        r._execute(frame=_frame("do"), mode=_mode(), action=action,
                   _memory_context_text="mem")
        self.assertEqual(llm.calls[0]["tools"], [sig])
        self.assertEqual(len(llm.calls[0]["messages"]), 2)
        self.assertEqual(llm.calls[0]["messages"][1], {"role": "user", "content": "do"})

    def test_use_tool_path_default_memory_blind(self):
        llm = _CapturingLLM(); r = _runner(llm)
        sig = {"name": "sig"}
        action = types.SimpleNamespace(
            action=ActionType.USE_TOOL,
            payload={"tool_signature": sig, "tool_family": "fam", "tool_defaults": {}})
        r._execute(frame=_frame("do"), mode=_mode(), action=action)
        self.assertEqual(llm.calls[0]["messages"], [{"role": "user", "content": "do"}])
        self.assertEqual(llm.calls[0]["tools"], [sig])


class TestCarryThroughExactObject(unittest.TestCase):
    def test_carried_request_is_exact_object_with_memory(self):
        llm = _CapturingLLM(); r = _runner(llm)
        action = types.SimpleNamespace(action=ActionType.ANSWER, payload={})
        ewr = r._execute_with_prompt_request(_frame("hi"), _mode(), action,
                                             memory_context_text="mem")
        self.assertIsInstance(ewr, _ExecutionWithPromptRequest)
        self.assertIsNotNone(ewr.prompt_request)
        # The carried request's messages ARE what the model received (exact object).
        self.assertEqual(ewr.prompt_request.messages, llm.calls[0]["messages"])
        self.assertIn("mem", ewr.prompt_request.messages[0]["content"])

    def test_carry_through_default_path_unchanged(self):
        llm = _CapturingLLM(); r = _runner(llm)
        action = types.SimpleNamespace(action=ActionType.ANSWER, payload={})
        ewr = r._execute_with_prompt_request(_frame("hi"), _mode(), action)
        self.assertEqual(ewr.prompt_request.messages, [{"role": "user", "content": "hi"}])


class TestNoExposure(unittest.TestCase):
    def test_memory_context_not_stored_on_self(self):
        r = _runner()
        r._build_llm_prompt_request(_frame(), _mode(), tools=None,
                                    memory_context_text="SECRET_MEM_TOKEN")
        for v in vars(r).values():
            self.assertNotIn("SECRET_MEM_TOKEN", repr(v))

    def test_memory_not_on_execution_outcome(self):
        r = _runner()
        action = types.SimpleNamespace(action=ActionType.ANSWER, payload={})
        outcome = r._execute(frame=_frame("hi"), mode=_mode(), action=action,
                             _memory_context_text="SECRET_MEM_TOKEN")
        for v in vars(outcome).values():
            self.assertNotIn("SECRET_MEM_TOKEN", repr(v))
        self.assertFalse(
            any(type(v).__name__ == "_LLMPromptRequest" for v in vars(outcome).values()),
            "ExecutionOutcome must not carry the prompt request")


class TestRunTurnThreadsMemoryContext(unittest.TestCase):
    """run_turn-level behaviour: the OPTIONAL memory_context_text param is threaded through
    the live turn into the model-visible prompt, and the default turn stays memory-blind.
    Uses the real ThinkingController plus fake fabric/LLM (mirrors test_agent_loop_smoke)."""

    class _Fabric:
        def __init__(self):
            self.ingest_calls = []
            self.drift_calls = []

        def ingest(self, workspace_id, agent_id, text, step):
            self.ingest_calls.append((workspace_id, agent_id, text, step))
            return {"status": "ok"}

        def measure_drift(self, workspace_id, agent_id):
            self.drift_calls.append((workspace_id, agent_id))
            return None

        def gravity_correction(self, workspace_id, agent_id, drift_info):
            pass

    class _LLM:
        def __init__(self):
            self.calls = []

        def complete(self, system_prompt, messages, tools=None):
            self.calls.append({"system_prompt": system_prompt, "messages": messages, "tools": tools})
            return LLMResponse(text="captured")

    def _make(self):
        from torment_service.thinking_controller import ThinkingController
        fabric = self._Fabric()
        llm = self._LLM()
        runner = AgentRunner(controller=ThinkingController(), fabric=fabric, llm_client=llm)
        return runner, fabric, llm

    def _observation(self, text):
        from torment_service.agent_loop import Observation
        return Observation(text=text)

    def _spy_memory(self, runner, seen):
        orig = runner._execute_with_prompt_request

        def spy(*args, **kwargs):
            seen["memory_context_text"] = kwargs.get("memory_context_text", "UNSET")
            return orig(*args, **kwargs)

        runner._execute_with_prompt_request = spy

    def test_run_turn_threads_memory_param_into_seam(self):
        runner, _fabric, _llm = self._make()
        seen = {}
        self._spy_memory(runner, seen)
        runner.run_turn(workspace_id="ws", agent_id="agent",
                        observation=self._observation("What is the capital of France?"),
                        step=1, memory_context_text="a recalled fact")
        self.assertEqual(seen.get("memory_context_text"), "a recalled fact")

    def test_run_turn_default_is_memory_blind(self):
        runner, _fabric, _llm = self._make()
        seen = {}
        self._spy_memory(runner, seen)
        runner.run_turn(workspace_id="ws", agent_id="agent",
                        observation=self._observation("Hello"), step=1)
        self.assertIsNone(seen.get("memory_context_text"))

    def test_run_turn_memory_reaches_model_prompt_when_model_called(self):
        runner, _fabric, llm = self._make()
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=self._observation("What is the capital of France?"),
            step=1, memory_context_text="PARIS_MEM_FACT")
        if llm.calls:  # ANSWER path invoked the model this turn
            msgs = llm.calls[0]["messages"]
            self.assertTrue(any("PARIS_MEM_FACT" in m.get("content", "") for m in msgs),
                            "memory context should reach the model-visible prompt")
            self.assertEqual(msgs[-1].get("content"), result.task_frame.raw_input,
                             "raw user input remains the separate, later message")
            self.assertNotIn("PARIS_MEM_FACT", msgs[-1].get("content", ""))

    def test_run_turn_does_not_expose_memory_on_turnresult(self):
        runner, _fabric, _llm = self._make()
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=self._observation("What is the capital of France?"),
            step=1, memory_context_text="SECRET_MEM_TOKEN")
        for v in vars(result).values():
            self.assertNotIn("SECRET_MEM_TOKEN", repr(v))


if __name__ == "__main__":
    unittest.main()
