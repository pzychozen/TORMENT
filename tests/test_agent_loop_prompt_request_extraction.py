"""Behavior-preserving AgentRunner prompt-request extraction/capture (#56 PASS).

`_execute` now builds an internal ``_LLMPromptRequest`` (``system_prompt`` /
``messages`` / ``tools``) via ``_build_llm_prompt_request`` and passes its fields
to ``llm_client.complete``. This is extraction/capture only — identical values as
before, no live memory wiring. The request object is local to ``_execute``: never
stored on ``self``, returned, or routed to review / ingest / fabric / writer /
metadata / TurnResult / persistence / retrieval / ranking / retry / output-control
/ endpoints. Its fields reach only ``llm_client.complete``.
"""

import ast
import os
import types
import unittest

from torment_service.agent_loop import AgentRunner, LLMResponse
from torment_service.thinking_models import ActionType


class _CapturingLLM:
    def __init__(self):
        self.calls = []

    def complete(self, *, system_prompt, messages, tools):
        self.calls.append({"system_prompt": system_prompt, "messages": messages, "tools": tools})
        return LLMResponse(text="captured-response")


def _runner(llm):
    # _execute uses only self.llm_client (and self.tool_executor, default None);
    # controller/fabric are stored but unused here.
    return AgentRunner(controller=object(), fabric=object(), llm_client=llm)


def _frame(text="the user input", agent_id="agentX"):
    return types.SimpleNamespace(raw_input=text, agent_id=agent_id)


def _mode(value="companion"):
    return types.SimpleNamespace(chosen_mode=types.SimpleNamespace(value=value))


class TestExecutePromptRequest(unittest.TestCase):

    def test_answer_path_complete_args_unchanged(self):
        llm = _CapturingLLM()
        runner = _runner(llm)
        frame, mode = _frame(), _mode()
        action = types.SimpleNamespace(action=ActionType.ANSWER, payload={})
        runner._execute(frame=frame, mode=mode, action=action)
        self.assertEqual(len(llm.calls), 1)
        call = llm.calls[0]
        self.assertEqual(call["system_prompt"], runner._build_system_prompt(frame, mode))
        self.assertEqual(call["messages"], [{"role": "user", "content": "the user input"}])
        self.assertIsNone(call["tools"])

    def test_use_tool_path_complete_args_unchanged(self):
        llm = _CapturingLLM()
        runner = _runner(llm)
        frame, mode = _frame(), _mode()
        sig = {"name": "sig"}
        action = types.SimpleNamespace(
            action=ActionType.USE_TOOL,
            payload={"tool_signature": sig, "tool_family": "fam", "tool_defaults": {}},
        )
        runner._execute(frame=frame, mode=mode, action=action)
        self.assertEqual(len(llm.calls), 1)
        call = llm.calls[0]
        self.assertEqual(call["system_prompt"], runner._build_system_prompt(frame, mode))
        self.assertEqual(call["messages"], [{"role": "user", "content": "the user input"}])
        self.assertEqual(call["tools"], [sig])

    def test_messages_is_fresh_user_list(self):
        llm = _CapturingLLM()
        runner = _runner(llm)
        frame = _frame("hello world")
        action = types.SimpleNamespace(action=ActionType.ANSWER, payload={})
        runner._execute(frame=frame, mode=_mode(), action=action)
        msgs = llm.calls[0]["messages"]
        self.assertEqual(msgs, [{"role": "user", "content": "hello world"}])
        self.assertEqual(len(msgs), 1)

    def test_build_llm_prompt_request_shape(self):
        runner = _runner(_CapturingLLM())
        frame, mode = _frame(), _mode()
        req = runner._build_llm_prompt_request(frame, mode, tools=None)
        self.assertEqual(req.system_prompt, runner._build_system_prompt(frame, mode))
        self.assertEqual(req.messages, [{"role": "user", "content": "the user input"}])
        self.assertIsNone(req.tools)
        req2 = runner._build_llm_prompt_request(frame, mode, tools=[{"name": "s"}])
        self.assertEqual(req2.tools, [{"name": "s"}])


class TestRunTurnBehaviorPreserved(unittest.TestCase):
    """End-to-end: a full turn still completes, and the existing TurnResult audit
    packet sink still builds only after review from the final response + supplied
    items (extraction did not change run_turn behavior)."""

    def test_turn_completes_and_packet_sink_unchanged(self):
        from dataclasses import dataclass, field
        from typing import Any, Dict, List, Optional
        from torment_service.thinking_controller import ThinkingController
        from torment_service.thinking_models import ReviewResult
        from torment_service.agent_loop import Observation
        from torment_service.audit_evidence_sidecar import build_audit_evidence_sidecar_from_items

        @dataclass
        class _FakeFabric:
            ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
            measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
            gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)
            drift_return: Optional[Dict[str, Any]] = None

            def ingest(self, workspace_id, agent_id, text, step):
                self.ingest_calls.append({"text": text})
                return {"status": "ok"}

            def measure_drift(self, workspace_id, agent_id):
                self.measure_drift_calls.append({})
                return self.drift_return

            def gravity_correction(self, workspace_id, agent_id, drift_info):
                self.gravity_correction_calls.append({})

        class _ForcedReview(ThinkingController):
            def __init__(self, forced):
                super().__init__()
                self._forced = forced

            def review(self, *, frame, mode, action, response_draft):
                return self._forced

        forced = ReviewResult(approved=True, revised=True, revised_text="FINAL reply")
        runner = AgentRunner(
            controller=_ForcedReview(forced),
            fabric=_FakeFabric(),
            llm_client=_CapturingLLM(),
        )
        items = [{"eid": 1, "block_type": "relational_context", "text": "ordinary fact"}]
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=Observation(text="tell me something"), step=1,
            audit_admitted_context_items=items,
        )
        # Review-finalized response is used; turn completed.
        self.assertEqual(result.execution_outcome.response_text, "FINAL reply")
        # Existing sink builds the packet from the final response + supplied items.
        self.assertEqual(
            result.audit_evidence_packet,
            build_audit_evidence_sidecar_from_items("FINAL reply", items),
        )


class TestSourceGuards(unittest.TestCase):

    def _agent_loop_tree(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "torment_service", "agent_loop.py")
        with open(path, "rb") as fh:
            return ast.parse(fh.read().replace(b"\x00", b""))

    def _class(self, tree, name):
        return next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name), None)

    def _method(self, cls, name):
        return next((n for n in cls.body
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name), None)

    def _idents(self, *nodes):
        out = set()
        for node in nodes:
            if node is None:
                continue
            for n in ast.walk(node):
                if isinstance(n, ast.Name):
                    out.add(n.id)
                elif isinstance(n, ast.Attribute):
                    out.add(n.attr)
                elif isinstance(n, ast.keyword) and n.arg:
                    out.add(n.arg)
        return out

    def test_agent_loop_does_not_import_or_call_observer(self):
        tree = self._agent_loop_tree()
        leaves = set()
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                if n.module:
                    leaves.add(n.module.split(".")[-1])
                for x in n.names:
                    names.add(x.name)
            elif isinstance(n, ast.Import):
                for x in n.names:
                    leaves.add(x.name.split(".")[-1])
        self.assertNotIn("audit_prompt_inclusion_observation", leaves)
        self.assertNotIn("observe_prompt_inclusion_packet", names)
        self.assertNotIn("observe_prompt_inclusion_packet", self._idents(tree))

    def test_prompt_request_helper_has_no_assembler_or_audit_refs(self):
        cls = self._class(self._agent_loop_tree(), "AgentRunner")
        helper = self._method(cls, "_build_llm_prompt_request")
        self.assertIsNotNone(helper)
        idents = self._idents(helper)
        for forbidden in ("assemble_context", "AssembledContext", "assembled_text",
                          "selected_admitted_items", "audit_admitted_context_items"):
            self.assertNotIn(forbidden, idents)

    def test_audit_items_absent_from_execute_and_prompt_helpers(self):
        cls = self._class(self._agent_loop_tree(), "AgentRunner")
        nodes = [self._method(cls, "_execute"),
                 self._method(cls, "_build_system_prompt"),
                 self._method(cls, "_build_llm_prompt_request")]
        self.assertNotIn("audit_admitted_context_items", self._idents(*nodes))

    def test_request_object_reaches_only_complete(self):
        cls = self._class(self._agent_loop_tree(), "AgentRunner")
        execute = self._method(cls, "_execute")
        self.assertIsNotNone(execute)
        # The `req` object is never passed as an argument to any call (only its
        # fields req.* are read), so it cannot be routed anywhere.
        for n in ast.walk(execute):
            if isinstance(n, ast.Call):
                arg_names = [a.id for a in n.args if isinstance(a, ast.Name)]
                arg_names += [k.value.id for k in n.keywords if isinstance(k.value, ast.Name)]
                self.assertNotIn("req", arg_names,
                                 msg="req object passed as an argument to a call")
        # Every req.<field> access is an argument of a self.llm_client.complete call.
        complete_calls = [
            n for n in ast.walk(execute)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "complete"
            and isinstance(n.func.value, ast.Attribute) and n.func.value.attr == "llm_client"
        ]
        allowed_req_attrs = set()
        for c in complete_calls:
            for v in list(c.args) + [k.value for k in c.keywords]:
                if isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name) and v.value.id == "req":
                    allowed_req_attrs.add(id(v))
        for n in ast.walk(execute):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id == "req"):
                self.assertIn(id(n), allowed_req_attrs,
                              msg="req.<field> used outside llm_client.complete(...)")


if __name__ == "__main__":
    unittest.main()
