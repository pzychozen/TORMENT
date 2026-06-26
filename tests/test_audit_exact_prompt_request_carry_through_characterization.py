"""Tests-only / source+AST + minimal fake-runtime CHARACTERIZATION of the exact
prompt-request carry-through terrain (audit / model-visible-context owner lane).

Subordinate to:
  docs/TORMENT_AUDIT_EXACT_PROMPT_REQUEST_CARRY_THROUGH_TEST_PROPOSAL_v0.1.md
  docs/TORMENT_AUDIT_PRIVATE_OWNER_W1_W8_LIVE_OWNER_REFACTOR_PROPOSAL_FRAME_v0.1.md
  docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md

This file CHARACTERIZES the exact prompt-request carry-through terrain AFTER the
behavior-preserving carry-through refactor. The gap/identity tests now prove
exact-object carry-through; the safety tests lock the invariants the refactor must
not change.

Terrain (read-only):
  AgentRunner._execute(...)
  AgentRunner._execute_with_prompt_request(...)
  AgentRunner._build_llm_prompt_request(...)
  AgentRunner._complete_llm_prompt_request(...)
  AgentRunner._observe_audit_evidence_from_prompt_request(...)  (downstream observer seam)
  _ExecutionWithPromptRequest, _LLMPromptRequest, ExecutionOutcome

CARRY-THROUGH (point 1, proven here): `_execute_with_prompt_request(...)` passes a
private one-slot capture list into `_execute(...)`; `_execute` writes the exact
`_LLMPromptRequest` object it built into that slot immediately before
`_complete_llm_prompt_request(...)`, and the wrapper carries that SAME object back.
No post-execution reconstruction via `_build_llm_prompt_request(frame, mode, tools=None)`.

EXACT-OBJECT IDENTITY (point 2, proven here): `_ExecutionWithPromptRequest.prompt_request`
IS the same `_LLMPromptRequest` object handed to `_complete_llm_prompt_request(...)`
(asserted via a test-local runner that captures the req passed to the completion
helper). ANSWER preserves `tools=None`; USE_TOOL preserves the exact sent
`tools=[signature_spec]` on the carried object — the prior reconstruction asymmetry is
closed. `ExecutionOutcome` stays free of any request field; the request rides on a
runner-local capture only.

This authorizes nothing: no production code, no W-7 resolution, no Shape B, no
PrivateGenerationOwner wiring, no prompt-surface change, no endpoint/API/schema, no
memory/retrieval/output-control/Gate A/Gate D/database/substrate/private-cognition.

Method: stdlib `unittest`. Source/AST parsing (no production execution) PLUS a
minimal fake runtime (a capturing fake LLM, SimpleNamespace frames/actions). If a
clause fails, do NOT patch production — return it as a gate decision.

Focused run (Windows cmd, from torment_fabric/):
  python -m unittest tests.test_audit_exact_prompt_request_carry_through_characterization
"""

import ast
import os
import types
import unittest

from torment_service.agent_loop import (
    AgentRunner,
    ExecutionOutcome,
    LLMResponse,
    _ExecutionWithPromptRequest,
    _LLMPromptRequest,
)
from torment_service.thinking_models import ActionType


_AGENT_LOOP = "agent_loop.py"
_APP = "app.py"
_OWNER_MODULE = "audit_private_generation_owner.py"

_EXECUTE = "_execute"
_CARRY = "_execute_with_prompt_request"
_PROMPT_BUILDER = "_build_llm_prompt_request"
_COMPLETE_HELPER = "_complete_llm_prompt_request"
_AUDIT_HELPER = "_observe_audit_evidence_from_prompt_request"
_OBSERVER = "observe_prompt_inclusion_packet"
_BUILT_PACKET = "_audit_evidence_packet"
_PROMPT_LOCAL = "_prompt_request"

_TERRAIN_SYMBOLS = frozenset({
    _CARRY, _PROMPT_BUILDER, _COMPLETE_HELPER,
    "_LLMPromptRequest", "_ExecutionWithPromptRequest",
})
_WRITER_NAMES = frozenset({
    "spawn_memory", "add_memory", "update_payload", "flush_node", "ingest",
    "promote_chunk", "reinforce", "write_environment",
})
_RETRIEVAL_NAMES = frozenset({"assemble_context", "selected_admitted_items", "query"})
_OWNER_NAMES = frozenset({"PrivateGenerationOwner", "PrivateGenerationOwnerResult"})
_GATE_TOKENS = ("chamber", "dream", "private_cognition", "incubation")


# --------------------------------------------------------------------------- #
# AST / source helpers (no service import)
# --------------------------------------------------------------------------- #

def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _parse_service(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _class(tree, name):
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


def _method(cls, name):
    if cls is None:
        return None
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _runner_method(name):
    return _method(_class(_parse_service(_AGENT_LOOP), "AgentRunner"), name)


def _dataclass_fields(tree, name):
    cls = _class(tree, name)
    fields = []
    if cls is None:
        return fields
    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            fields.append(n.target.id)
    return fields


def _annotation_src(tree, class_name, field_name):
    cls = _class(tree, class_name)
    for n in (cls.body if cls else []):
        if (isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                and n.target.id == field_name):
            return ast.dump(n.annotation)
    return ""


def _called_names(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def _idents(node):
    out = set()
    if node is None:
        return out
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.keyword) and n.arg:
            out.add(n.arg)
    return out


def _all_functions(tree):
    return [n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _funcs_calling(tree, name):
    return {fn.name for fn in _all_functions(tree) if name in _called_names(fn)}


def _attr_reads(node, base_name):
    """attr names of every `<base_name>.<attr>` access within node."""
    out = set()
    for n in ast.walk(node):
        if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                and n.value.id == base_name):
            out.add(n.attr)
    return out


def _call_receivers_of(node, var):
    """Callee leaf-names of every Call receiving Name `var` as a positional/kw arg."""
    receivers = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            passed = [a.id for a in n.args if isinstance(a, ast.Name)]
            passed += [k.value.id for k in n.keywords if isinstance(k.value, ast.Name)]
            if var in passed:
                f = n.func
                receivers.add(f.id if isinstance(f, ast.Name)
                              else f.attr if isinstance(f, ast.Attribute) else "?")
    return receivers


def _branch_uses(node, var):
    """Lines where Name `var` appears in an If/While/IfExp TEST within node."""
    uses = []
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.While, ast.IfExp)):
            for sub in ast.walk(n.test):
                if isinstance(sub, ast.Name) and sub.id == var:
                    uses.append(getattr(n, "lineno", -1))
    return uses


def _import_leaves_names(tree):
    leaves, names = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for x in n.names:
                leaves.add(x.name.split(".")[-1])
                names.add(x.name.split(".")[-1])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                leaves.add(n.module.split(".")[-1])
            for x in n.names:
                names.add(x.name)
    return leaves, names


def _iter_service():
    skip = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}
    for dp, dns, fns in os.walk(_service_dir()):
        dns[:] = [d for d in dns if d not in skip and not d.startswith("do_not_touch")]
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            ab = os.path.join(dp, fn)
            try:
                with open(ab, "rb") as fh:
                    tree = ast.parse(fh.read().replace(b"\x00", b""))
            except (SyntaxError, ValueError, OSError):
                continue
            yield os.path.basename(ab), tree


# --------------------------------------------------------------------------- #
# Minimal fake runtime
# --------------------------------------------------------------------------- #

class _CapturingLLM:
    def __init__(self):
        self.calls = []

    def complete(self, *, system_prompt, messages, tools):
        self.calls.append({"system_prompt": system_prompt, "messages": messages, "tools": tools})
        return LLMResponse(text="captured-response")


class _BoomRequest:
    """A non-None 'prompt request' whose field access raises, to exercise the
    fail-soft try/except in the downstream observer helper."""
    messages = [{"role": "user", "content": "x"}]

    @property
    def system_prompt(self):
        raise RuntimeError("boom")


def _runner(llm=None):
    return AgentRunner(controller=object(), fabric=object(), llm_client=llm or _CapturingLLM())


def _frame(text="the user input", agent_id="agentX"):
    return types.SimpleNamespace(raw_input=text, agent_id=agent_id)


def _mode(value="companion"):
    return types.SimpleNamespace(chosen_mode=types.SimpleNamespace(value=value))


def _answer():
    return types.SimpleNamespace(action=ActionType.ANSWER, payload={})


def _no_op():
    return types.SimpleNamespace(action=ActionType.NO_OP, payload={})


def _use_tool(sig=None):
    sig = sig or {"name": "demo_tool", "description": "demo", "parameters": {}}
    return types.SimpleNamespace(
        action=ActionType.USE_TOOL,
        payload={"tool_signature": sig, "tool_family": "fam", "tool_defaults": {}},
    )


class _CapturingReqRunner(AgentRunner):
    """Runner that records the EXACT `_LLMPromptRequest` object passed into the model
    completion helper, so tests can assert exact-object carry-through identity
    (`ewpr.prompt_request is captured_req`). It delegates to the real helper, so the
    underlying capturing LLM still records the sent system_prompt/messages/tools."""

    def __init__(self, llm=None):
        super().__init__(controller=object(), fabric=object(), llm_client=llm or _CapturingLLM())
        self.captured_reqs = []

    def _complete_llm_prompt_request(self, req):
        self.captured_reqs.append(req)
        return super()._complete_llm_prompt_request(req)


# --------------------------------------------------------------------------- #
# 1. No reconstruction after _execute (point 1: carry-through is implemented)
# --------------------------------------------------------------------------- #

class TestNoReconstructionAfterExecute(unittest.TestCase):

    def test_carry_no_longer_reconstructs_after_execute(self):
        # Carry-through: the seam calls _execute (passing a private capture) and NO
        # LONGER reconstructs the request via _build_llm_prompt_request after
        # execution.
        carry = _runner_method(_CARRY)
        self.assertIsNotNone(carry, "_execute_with_prompt_request missing")
        called = _called_names(carry)
        self.assertIn(_EXECUTE, called, "carry seam no longer calls _execute")
        self.assertNotIn(_PROMPT_BUILDER, called,
                         "carry seam still reconstructs via _build_llm_prompt_request")

    def test_request_rides_on_local_capture_not_the_outcome(self):
        # The request is carried via a runner-local capture, never read off the
        # ExecutionOutcome (which stays free of any request field).
        carry = _runner_method(_CARRY)
        outcome_attrs = _attr_reads(carry, "outcome")
        self.assertNotIn("prompt_request", outcome_attrs)
        self.assertNotIn("req", outcome_attrs)

    def test_execution_outcome_carries_no_prompt_request(self):
        al = _parse_service(_AGENT_LOOP)
        fields = _dataclass_fields(al, "ExecutionOutcome")
        self.assertNotIn("prompt_request", fields)
        self.assertNotIn("req", fields)


# --------------------------------------------------------------------------- #
# 2. `_execute` returns ExecutionOutcome, not `_ExecutionWithPromptRequest`
# --------------------------------------------------------------------------- #

class TestExecuteReturnsExecutionOutcome(unittest.TestCase):

    def test_execute_return_annotation_is_execution_outcome(self):
        execute = _runner_method(_EXECUTE)
        self.assertIsNotNone(execute)
        self.assertIsInstance(execute.returns, ast.Name)
        self.assertEqual(execute.returns.id, "ExecutionOutcome")

    def test_runtime_execute_returns_execution_outcome(self):
        runner = _runner()
        out = runner._execute(frame=_frame(), mode=_mode(), action=_answer())
        self.assertIsInstance(out, ExecutionOutcome)
        self.assertNotIsInstance(out, _ExecutionWithPromptRequest)
        self.assertTrue(out.llm_called)

    def test_runtime_carry_returns_pairing(self):
        runner = _runner()
        ewpr = runner._execute_with_prompt_request(frame=_frame(), mode=_mode(), action=_answer())
        self.assertIsInstance(ewpr, _ExecutionWithPromptRequest)
        self.assertIsInstance(ewpr.outcome, ExecutionOutcome)


# --------------------------------------------------------------------------- #
# 3. Exact-object carry-through: carried request IS the object sent to the model
# --------------------------------------------------------------------------- #

class TestExactObjectCarryThrough(unittest.TestCase):

    def test_answer_path_carries_the_exact_object_sent(self):
        # The carried prompt_request IS the same _LLMPromptRequest object _execute
        # built and passed to _complete_llm_prompt_request — exact-object
        # carry-through, not a reconstruction.
        llm = _CapturingLLM()
        runner = _CapturingReqRunner(llm)
        frame, mode = _frame(), _mode()
        ewpr = runner._execute_with_prompt_request(frame=frame, mode=mode, action=_answer())
        self.assertEqual(len(runner.captured_reqs), 1)
        captured_req = runner.captured_reqs[0]
        self.assertIsInstance(ewpr.prompt_request, _LLMPromptRequest)
        self.assertIs(ewpr.prompt_request, captured_req)

    def test_carried_values_match_what_was_sent_answer_path(self):
        # The carried (now exact) object's system_prompt/messages equal what the
        # model boundary received this turn.
        llm = _CapturingLLM()
        runner = _runner(llm)
        frame, mode = _frame(), _mode()
        ewpr = runner._execute_with_prompt_request(frame=frame, mode=mode, action=_answer())
        self.assertEqual(len(llm.calls), 1)
        sent = llm.calls[0]
        self.assertEqual(ewpr.prompt_request.system_prompt, sent["system_prompt"])
        self.assertEqual(ewpr.prompt_request.messages, sent["messages"])

    def test_use_tool_path_carries_exact_object_with_tools(self):
        # USE_TOOL: the model boundary receives tools=[sig], and the carried
        # prompt_request is the SAME object with tools=[sig] — the prior asymmetry
        # (reconstructed tools=None) is closed.
        llm = _CapturingLLM()
        runner = _CapturingReqRunner(llm)
        frame, mode = _frame(), _mode()
        sig = {"name": "demo_tool", "description": "demo", "parameters": {}}
        ewpr = runner._execute_with_prompt_request(frame=frame, mode=mode, action=_use_tool(sig))
        self.assertTrue(ewpr.outcome.llm_called)
        self.assertEqual(len(runner.captured_reqs), 1)
        captured_req = runner.captured_reqs[0]
        sent = llm.calls[0]
        self.assertEqual(sent["tools"], [sig])
        self.assertEqual(ewpr.prompt_request.tools, [sig])
        self.assertIs(ewpr.prompt_request, captured_req)


# --------------------------------------------------------------------------- #
# 4. `_ExecutionWithPromptRequest.prompt_request` slot exists and is optional
# --------------------------------------------------------------------------- #

class TestPromptRequestSlot(unittest.TestCase):

    def test_pairing_has_outcome_and_prompt_request_fields(self):
        al = _parse_service(_AGENT_LOOP)
        self.assertEqual(_dataclass_fields(al, "_ExecutionWithPromptRequest"),
                         ["outcome", "prompt_request"])

    def test_prompt_request_annotation_is_optional(self):
        al = _parse_service(_AGENT_LOOP)
        ann = _annotation_src(al, "_ExecutionWithPromptRequest", "prompt_request")
        self.assertIn("Optional", ann)
        self.assertIn("_LLMPromptRequest", ann)

    def test_prompt_request_is_none_when_no_model_call(self):
        runner = _runner()
        ewpr = runner._execute_with_prompt_request(frame=_frame(), mode=_mode(), action=_no_op())
        self.assertFalse(ewpr.outcome.llm_called)
        self.assertIsNone(ewpr.prompt_request)

    def test_pairing_accepts_none_prompt_request(self):
        pair = _ExecutionWithPromptRequest(outcome=ExecutionOutcome(no_op=True), prompt_request=None)
        self.assertIsNone(pair.prompt_request)


# --------------------------------------------------------------------------- #
# 5. Prompt surface pinned (point 3): same system_prompt / messages / tools
# --------------------------------------------------------------------------- #

class TestPromptSurfacePinned(unittest.TestCase):

    def test_builder_pins_system_prompt_and_user_messages(self):
        runner = _runner()
        frame, mode = _frame("hello pin"), _mode()
        req = runner._build_llm_prompt_request(frame, mode, tools=None)
        self.assertEqual(req.system_prompt, runner._build_system_prompt(frame, mode))
        self.assertEqual(req.messages, [{"role": "user", "content": "hello pin"}])
        self.assertIsNone(req.tools)

    def test_builder_source_uses_only_build_system_prompt_and_raw_input(self):
        builder = _runner_method(_PROMPT_BUILDER)
        idents = _idents(builder)
        self.assertIn("_build_system_prompt", idents)
        self.assertIn("raw_input", idents)
        # explicit `tools` argument only — no inline tool discovery / assembly.
        for forbidden in ("assemble_context", "AssembledContext", "assembled_text",
                          "selected_admitted_items", "audit_admitted_context_items"):
            self.assertNotIn(forbidden, idents)

    def test_answer_path_sends_pinned_surface(self):
        llm = _CapturingLLM()
        runner = _runner(llm)
        frame, mode = _frame("surface text"), _mode()
        runner._execute(frame=frame, mode=mode, action=_answer())
        sent = llm.calls[0]
        self.assertEqual(sent["system_prompt"], runner._build_system_prompt(frame, mode))
        self.assertEqual(sent["messages"], [{"role": "user", "content": "surface text"}])
        self.assertIsNone(sent["tools"])

    def test_use_tool_path_sends_explicit_tool_surface(self):
        # On USE_TOOL the model boundary receives the explicit single-tool surface.
        llm = _CapturingLLM()
        runner = _runner(llm)
        frame, mode = _frame("surface text"), _mode()
        sig = {"name": "demo_tool", "description": "demo", "parameters": {}}
        runner._execute(frame=frame, mode=mode, action=_use_tool(sig))
        sent = llm.calls[0]
        self.assertEqual(sent["system_prompt"], runner._build_system_prompt(frame, mode))
        self.assertEqual(sent["messages"], [{"role": "user", "content": "surface text"}])
        self.assertEqual(sent["tools"], [sig])


# --------------------------------------------------------------------------- #
# 6. No prompt exposure (point 4): request never surfaces beyond the observer seam
# --------------------------------------------------------------------------- #

class TestNoPromptExposure(unittest.TestCase):

    def test_local_prompt_request_routes_only_to_audit_helper(self):
        run_turn = _runner_method("run_turn")
        self.assertIsNotNone(run_turn)
        receivers = _call_receivers_of(run_turn, _PROMPT_LOCAL)
        self.assertTrue(receivers <= {_AUDIT_HELPER},
                        msg=f"_prompt_request routed beyond the audit helper: {sorted(receivers)}")

    def test_prompt_request_not_passed_to_turnresult(self):
        run_turn = _runner_method("run_turn")
        for n in ast.walk(run_turn):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "TurnResult"):
                kw_value_names = {k.value.id for k in n.keywords
                                  if isinstance(k.value, ast.Name)}
                self.assertNotIn(_PROMPT_LOCAL, kw_value_names)
                self.assertNotIn("prompt_request", {k.arg for k in n.keywords})

    def test_turnresult_and_outcome_have_no_prompt_request_field(self):
        al = _parse_service(_AGENT_LOOP)
        self.assertNotIn("prompt_request", _dataclass_fields(al, "TurnResult"))
        self.assertNotIn("prompt_request", _dataclass_fields(al, "ExecutionOutcome"))

    def test_request_never_stored_on_self(self):
        al = _parse_service(_AGENT_LOOP)
        for n in ast.walk(al):
            targets = []
            if isinstance(n, ast.Assign):
                targets = n.targets
            elif isinstance(n, ast.AnnAssign):
                targets = [n.target]
            for t in targets:
                if (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                        and t.value.id == "self"):
                    self.assertNotIn("prompt_request", t.attr,
                                     msg="a prompt request is stored on self")


# --------------------------------------------------------------------------- #
# 7. Packet inertness (point 5): built packet drives no branch, routes only to TurnResult
# --------------------------------------------------------------------------- #

class TestPacketInertness(unittest.TestCase):

    def test_built_packet_drives_no_branch(self):
        al = _parse_service(_AGENT_LOOP)
        self.assertEqual(_branch_uses(al, _BUILT_PACKET), [],
                         msg="the built audit packet drives a control branch")

    def test_built_packet_routes_only_to_turnresult(self):
        run_turn = _runner_method("run_turn")
        receivers = _call_receivers_of(run_turn, _BUILT_PACKET)
        self.assertTrue(receivers <= {"TurnResult"},
                        msg=f"built audit packet routed beyond TurnResult: {sorted(receivers)}")


# --------------------------------------------------------------------------- #
# 8. Downstream observer confinement (point 6)
# --------------------------------------------------------------------------- #

class TestObserverConfinement(unittest.TestCase):

    def test_observer_called_only_in_audit_helper(self):
        al = _parse_service(_AGENT_LOOP)
        self.assertEqual(_funcs_calling(al, _OBSERVER), {_AUDIT_HELPER},
                         msg="observer is not confined to the audit-evidence helper")

    def test_audit_helper_called_only_by_run_turn(self):
        al = _parse_service(_AGENT_LOOP)
        self.assertEqual(_funcs_calling(al, _AUDIT_HELPER), {"run_turn"},
                         msg="audit helper called by something other than run_turn")

    def test_generation_terrain_does_not_observe(self):
        for name in (_EXECUTE, _COMPLETE_HELPER, _CARRY, _PROMPT_BUILDER):
            called = _called_names(_runner_method(name))
            self.assertNotIn(_OBSERVER, called,
                             msg=f"{name} composes audit evidence (control-of-generation risk)")


# --------------------------------------------------------------------------- #
# 9. Fail-soft / absence non-punitive (point 10)
# --------------------------------------------------------------------------- #

class TestFailSoftAbsenceNonPunitive(unittest.TestCase):

    def test_none_when_inputs_insufficient(self):
        runner = _runner()
        req = runner._build_llm_prompt_request(_frame(), _mode(), tools=None)
        items = [{"eid": 1, "text": "ordinary fact"}]
        # no captured request -> None
        self.assertIsNone(runner._observe_audit_evidence_from_prompt_request(None, items, "resp"))
        # no caller-supplied items -> None
        self.assertIsNone(runner._observe_audit_evidence_from_prompt_request(req, None, "resp"))
        # no final response text -> None
        self.assertIsNone(runner._observe_audit_evidence_from_prompt_request(req, items, ""))
        self.assertIsNone(runner._observe_audit_evidence_from_prompt_request(req, items, None))

    def test_observer_error_is_fail_soft(self):
        runner = _runner()
        items = [{"eid": 1, "text": "ordinary fact"}]
        # field access on the request raises inside the try -> None, no exception out.
        self.assertIsNone(
            runner._observe_audit_evidence_from_prompt_request(_BoomRequest(), items, "resp"))

    def test_audit_helper_source_is_fail_soft(self):
        helper = _runner_method(_AUDIT_HELPER)
        self.assertIsNotNone(helper)
        observed_under_try = any(
            isinstance(n, ast.Try) and _OBSERVER in _called_names(n)
            for n in ast.walk(helper))
        self.assertTrue(observed_under_try,
                        "observer call is not under try/except (not fail-soft)")
        # built packet drives no branch => its absence (None) is non-punitive.
        al = _parse_service(_AGENT_LOOP)
        self.assertEqual(_branch_uses(al, _BUILT_PACKET), [])


# --------------------------------------------------------------------------- #
# 10. Owner remains unwired (point 7)
# --------------------------------------------------------------------------- #

class TestOwnerUnwired(unittest.TestCase):

    def test_no_production_import_or_construction_of_owner(self):
        offenders = []
        for base, tree in _iter_service():
            if base == _OWNER_MODULE:
                continue
            leaves, names = _import_leaves_names(tree)
            if ("audit_private_generation_owner" in leaves
                    or names & _OWNER_NAMES):
                offenders.append(base)
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        and n.func.id in _OWNER_NAMES):
                    offenders.append(f"{base}::construct")
        self.assertEqual(offenders, [], msg=f"owner wired/constructed in: {offenders}")


# --------------------------------------------------------------------------- #
# 11. app.py / endpoints are non-callers of the carry-through terrain (point 8)
# --------------------------------------------------------------------------- #

class TestAppEndpointsNonCallers(unittest.TestCase):

    def test_app_does_not_reference_terrain_or_runner(self):
        app = _parse_service(_APP)
        leaves, names = _import_leaves_names(app)
        self.assertNotIn("AgentRunner", names, "app.py imports AgentRunner")
        idents = _idents(app)
        for sym in _TERRAIN_SYMBOLS:
            self.assertNotIn(sym, idents, msg=f"app.py references terrain symbol {sym}")
        for sym in _OWNER_NAMES:
            self.assertNotIn(sym, names, msg=f"app.py imports {sym}")


# --------------------------------------------------------------------------- #
# 12. No forbidden reachability from the exact-request terrain (point 9)
# --------------------------------------------------------------------------- #

class TestNoForbiddenReachabilityFromTerrain(unittest.TestCase):

    def test_terrain_helpers_reach_no_writer_retrieval_or_owner(self):
        for name in (_PROMPT_BUILDER, _COMPLETE_HELPER, _AUDIT_HELPER):
            called = _called_names(_runner_method(name))
            self.assertEqual(called & _WRITER_NAMES, set(),
                             msg=f"{name} reaches writer(s): {sorted(called & _WRITER_NAMES)}")
            self.assertEqual(called & _RETRIEVAL_NAMES, set(),
                             msg=f"{name} reaches retrieval: {sorted(called & _RETRIEVAL_NAMES)}")
            self.assertEqual(_idents(_runner_method(name)) & _OWNER_NAMES, set(),
                             msg=f"{name} references the private owner")

    def test_carry_seam_own_body_is_a_thin_wrapper(self):
        # _execute_with_prompt_request directly calls ONLY _execute and the
        # reconstruction builder, and constructs the pairing; it composes no audit
        # packet and reaches no writer/retrieval/owner of its own.
        carry = _runner_method(_CARRY)
        self.assertTrue(
            _called_names(carry) <= {_EXECUTE, _PROMPT_BUILDER, "_ExecutionWithPromptRequest"},
            msg=f"carry seam calls beyond the thin wrapper set: {sorted(_called_names(carry))}")
        idents = _idents(carry)
        self.assertNotIn(_OBSERVER, idents)
        self.assertNotIn(_BUILT_PACKET, idents)
        self.assertEqual(idents & _OWNER_NAMES, set())

    def test_no_gate_d_entrypoint_named_in_module(self):
        al = _parse_service(_AGENT_LOOP)
        for fn in _all_functions(al):
            low = fn.name.lower()
            for tok in _GATE_TOKENS:
                self.assertNotIn(tok, low, f"agent_loop defines a {tok} entrypoint")


if __name__ == "__main__":
    unittest.main()
