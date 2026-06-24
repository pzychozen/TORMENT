"""Characterization: current live-owner topology for a future model-visible
context owner (tests-only / source-only).

Codex REVISE on #56 → one narrow characterization BEFORE any live wiring. This
file wires nothing, connects nothing to ``AgentRunner``, touches no endpoint, and
changes no production code. It records, by AST/source inspection, where live
generation happens today and why no current path can honestly own the
model-visible inclusion claim — so a future owner must make an explicit design
choice.

What it characterizes:
  1. ``AgentRunner._execute`` is the only current live generation boundary.
  2. The exact live prompt boundary is still
     ``llm_client.complete(system_prompt=self._build_system_prompt(frame, mode),
     messages=[{"role": "user", "content": frame.raw_input}])``.
  3. No current path renders ``assembled_text`` into that boundary.
  4. Passing ``audit_admitted_context_items`` into ``run_turn`` before inclusion
     is observed is only co-location/staging, not proof of inclusion.
  5. ``audit_prompt_inclusion_observation`` is still called nowhere in production.
  6. Endpoint paths still do not own both assembled context and generated
     response together.
  7. A future live owner must choose ONE of two explicit designs: refactor/
     capture AgentRunner's prompt request, OR become the generation owner itself.

No forbidden wording is introduced.
"""

import ast
import os
import unittest


def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _parse_service(filename):
    with open(os.path.join(_torment_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))        # null-strip: mount artifact only


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


def _top_func(tree, name):
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _idents(*nodes):
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


_ASSEMBLER_CTX = {"assemble_context", "AssembledContext", "assembled_text"}


def _is_self_llm_complete(call):
    """True for ``self.llm_client.complete(...)``."""
    f = call.func
    return (isinstance(f, ast.Attribute) and f.attr == "complete"
            and isinstance(f.value, ast.Attribute) and f.value.attr == "llm_client"
            and isinstance(f.value.value, ast.Name) and f.value.value.id == "self")


def _complete_calls(node):
    return [n for n in ast.walk(node)
            if isinstance(n, ast.Call) and _is_self_llm_complete(n)]


def _kw(call, name):
    for k in call.keywords:
        if k.arg == name:
            return k.value
    return None


def _is_build_system_prompt_call(value):
    """``self._build_system_prompt(frame, mode)``."""
    if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
            and value.func.attr == "_build_system_prompt"
            and isinstance(value.func.value, ast.Name) and value.func.value.id == "self"):
        return False
    arg_names = [a.id for a in value.args if isinstance(a, ast.Name)]
    return "frame" in arg_names and "mode" in arg_names


def _messages_carry_frame_raw_input(value):
    """``[{"role": "user", "content": frame.raw_input}]`` (one user dict whose
    content is ``frame.raw_input``)."""
    if not (isinstance(value, ast.List) and value.elts):
        return False
    for elt in value.elts:
        if not isinstance(elt, ast.Dict):
            continue
        role = content = None
        for k, v in zip(elt.keys, elt.values):
            if isinstance(k, ast.Constant) and k.value == "role":
                role = v
            elif isinstance(k, ast.Constant) and k.value == "content":
                content = v
        role_ok = isinstance(role, ast.Constant) and role.value == "user"
        content_ok = (isinstance(content, ast.Attribute) and content.attr == "raw_input"
                      and isinstance(content.value, ast.Name) and content.value.id == "frame")
        if role_ok and content_ok:
            return True
    return False


def _is_req_field(value, field):
    """``req.<field>`` — the local prompt-request object's field access."""
    return (isinstance(value, ast.Attribute) and value.attr == field
            and isinstance(value.value, ast.Name) and value.value.id == "req")


def _build_request_calls(node):
    """All ``self._build_llm_prompt_request(...)`` calls under ``node``."""
    out = []
    for n in ast.walk(node):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "_build_llm_prompt_request"
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "self"):
            out.append(n)
    return out


class TestLiveGenerationBoundary(unittest.TestCase):

    def setUp(self):
        self.tree = _parse_service("agent_loop.py")
        self.runner = _class(self.tree, "AgentRunner")
        self.execute = _method(self.runner, "_execute")

    def test_execute_is_the_live_generation_boundary(self):
        self.assertIsNotNone(self.execute, "AgentRunner._execute not found")
        calls = _complete_calls(self.execute)
        self.assertTrue(calls, "expected self.llm_client.complete(...) in _execute")

    def test_prompt_boundary_shape_in_execute(self):
        # Post-extraction: _execute passes the LOCAL request object's fields
        # unchanged into complete(...) (the boundary is preserved in the helper,
        # see test_build_llm_prompt_request_preserves_boundary).
        calls = _complete_calls(self.execute)
        self.assertTrue(calls)
        for call in calls:
            self.assertTrue(_is_req_field(_kw(call, "system_prompt"), "system_prompt"),
                            "system_prompt is not req.system_prompt")
            self.assertTrue(_is_req_field(_kw(call, "messages"), "messages"),
                            "messages is not req.messages")
            self.assertTrue(_is_req_field(_kw(call, "tools"), "tools"),
                            "tools is not req.tools")

    def test_execute_builds_request_via_helper(self):
        # _execute builds req via self._build_llm_prompt_request(frame, mode,
        # tools=...): tools=None on ANSWER, tools=[...] on USE_TOOL.
        calls = _build_request_calls(self.execute)
        self.assertGreaterEqual(len(calls), 2,
                                "expected _build_llm_prompt_request on ANSWER and USE_TOOL paths")
        tools_values = [_kw(c, "tools") for c in calls]
        self.assertTrue(any(isinstance(v, ast.Constant) and v.value is None for v in tools_values),
                        "expected a _build_llm_prompt_request(..., tools=None) call (ANSWER)")
        self.assertTrue(any(isinstance(v, ast.List) for v in tools_values),
                        "expected a _build_llm_prompt_request(..., tools=[...]) call (USE_TOOL)")
        for c in calls:
            arg_names = [a.id for a in c.args if isinstance(a, ast.Name)]
            self.assertIn("frame", arg_names)
            self.assertIn("mode", arg_names)

    def test_build_llm_prompt_request_preserves_boundary(self):
        # The helper is where the ORIGINAL prompt boundary is preserved.
        helper = _method(self.runner, "_build_llm_prompt_request")
        self.assertIsNotNone(helper, "_build_llm_prompt_request not found")
        ctor = next((n for n in ast.walk(helper)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                     and n.func.id == "_LLMPromptRequest"), None)
        self.assertIsNotNone(ctor, "_LLMPromptRequest(...) construction not found")
        self.assertTrue(_is_build_system_prompt_call(_kw(ctor, "system_prompt")),
                        "system_prompt is not self._build_system_prompt(frame, mode)")
        self.assertTrue(_messages_carry_frame_raw_input(_kw(ctor, "messages")),
                        "messages do not carry frame.raw_input as user content")
        tools_v = _kw(ctor, "tools")
        self.assertTrue(isinstance(tools_v, ast.Name) and tools_v.id == "tools",
                        "tools is not the explicit tools argument")

    def test_no_assembled_context_in_prompt_boundary(self):
        # Unchanged meaning, now applied to _execute, _build_system_prompt, AND
        # the new _build_llm_prompt_request.
        nodes = [self.execute,
                 _method(self.runner, "_build_system_prompt"),
                 _method(self.runner, "_build_llm_prompt_request")]
        ids = _idents(*nodes)
        self.assertEqual(ids & _ASSEMBLER_CTX, set(),
                         "prompt boundary consumes assembler context")
        self.assertNotIn("audit_admitted_context_items", ids,
                         "prompt boundary references audit_admitted_context_items")
        leaves, names = _import_leaves_names(self.tree)
        self.assertNotIn("retrieval_assembler", leaves)
        self.assertNotIn("AssembledContext", names)


class TestStagingIsNotInclusionProof(unittest.TestCase):

    def setUp(self):
        self.tree = _parse_service("agent_loop.py")
        self.runner = _class(self.tree, "AgentRunner")
        self.run_turn = _method(self.runner, "run_turn")

    def test_items_route_only_to_packet_builder_and_turnresult(self):
        receivers = set()
        for n in ast.walk(self.run_turn):
            if isinstance(n, ast.Call):
                passed = [a.id for a in n.args if isinstance(a, ast.Name)]
                passed += [k.value.id for k in n.keywords if isinstance(k.value, ast.Name)]
                if "audit_admitted_context_items" in passed:
                    f = n.func
                    receivers.add(f.id if isinstance(f, ast.Name)
                                  else f.attr if isinstance(f, ast.Attribute) else "?")
        # Items reach only the packet builder and TurnResult — never the prompt
        # path. So items on TurnResult are staging/co-location, not inclusion.
        self.assertTrue(receivers <= {"build_audit_evidence_sidecar_from_items", "TurnResult"},
                        msg=f"items routed unexpectedly: {sorted(receivers - {'build_audit_evidence_sidecar_from_items', 'TurnResult'})}")

    def test_inclusion_observer_not_used_in_live_path(self):
        # The helper that would PROVE inclusion is not imported or called by the
        # live runner — so the live path performs no inclusion proof.
        leaves, names = _import_leaves_names(self.tree)
        self.assertNotIn("audit_prompt_inclusion_observation", leaves)
        self.assertNotIn("observe_prompt_inclusion_packet", names)
        self.assertNotIn("observe_prompt_inclusion_packet", _idents(self.tree))


class TestObserverCalledNowhereInProduction(unittest.TestCase):

    def test_no_production_module_imports_or_calls_observer(self):
        svc = _torment_service_dir()
        offenders = []
        for fn in os.listdir(svc):
            if not fn.endswith(".py") or fn == "audit_prompt_inclusion_observation.py":
                continue
            try:
                tree = _parse_service(fn)
            except (SyntaxError, ValueError):
                continue
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[-1] == "audit_prompt_inclusion_observation":
                    offenders.append(f"{fn}: import")
                elif isinstance(n, ast.Import) and any(x.name.split(".")[-1] == "audit_prompt_inclusion_observation" for x in n.names):
                    offenders.append(f"{fn}: import")
                elif isinstance(n, ast.Call):
                    f = n.func
                    nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
                    if nm == "observe_prompt_inclusion_packet":
                        offenders.append(f"{fn}: call")
        self.assertEqual(offenders, [], msg=f"observer has production caller(s): {offenders}")


class TestEndpointsOwnNeitherBothHalves(unittest.TestCase):

    def setUp(self):
        self.app = _parse_service("app.py")

    def test_app_does_not_own_generation_and_assembled_context_together(self):
        app_idents = _idents(self.app)
        # No generation ownership in app (no AgentRunner / run_turn).
        self.assertNotIn("AgentRunner", app_idents)
        self.assertNotIn("run_turn", app_idents)
        # retrieve_assembled owns assembled context but no generation/response.
        ra = _top_func(self.app, "retrieve_assembled")
        self.assertIsNotNone(ra)
        ra_idents = _idents(ra)
        self.assertIn("assemble_context", ra_idents)
        self.assertNotIn("complete", ra_idents)
        self.assertNotIn("response_text", ra_idents)
        # query owns neither generation nor assembled context.
        q = _top_func(self.app, "query")
        self.assertIsNotNone(q)
        q_idents = _idents(q)
        self.assertNotIn("complete", q_idents)
        self.assertNotIn("response_text", q_idents)
        self.assertNotIn("assemble_context", q_idents)

    def test_no_production_caller_passes_items_as_inclusion_proof(self):
        # Across torment_service, no run_turn call passes audit_admitted_context_items
        # (it would be co-location, not inclusion proof). Tests may; production must not.
        svc = _torment_service_dir()
        offenders = []
        for fn in os.listdir(svc):
            if not fn.endswith(".py"):
                continue
            try:
                tree = _parse_service(fn)
            except (SyntaxError, ValueError):
                continue
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "run_turn"
                        and any(k.arg == "audit_admitted_context_items" for k in n.keywords)):
                    offenders.append(fn)
        self.assertEqual(offenders, [], msg=f"production run_turn caller passes items: {offenders}")


class TestFutureOwnerMustChooseOneOfTwoDesigns(unittest.TestCase):
    """Generation ownership and assembled-context ownership live in DISJOINT
    functions today, so a future owner must EITHER (A) refactor/capture
    AgentRunner's prompt request, OR (B) become the generation owner itself.
    Neither exists yet; this records the fork (it selects nothing)."""

    def test_generation_and_assembled_context_are_disjoint_today(self):
        al = _parse_service("agent_loop.py")
        runner = _class(al, "AgentRunner")
        execute = _method(runner, "_execute")
        exec_idents = _idents(execute)
        # _execute owns generation but not assembled context.
        self.assertTrue(_complete_calls(execute))
        self.assertEqual(exec_idents & _ASSEMBLER_CTX, set())

        app = _parse_service("app.py")
        ra = _top_func(app, "retrieve_assembled")
        ra_idents = _idents(ra)
        # retrieve_assembled owns assembled context but not generation.
        self.assertIn("assemble_context", ra_idents)
        self.assertNotIn("complete", ra_idents)
        self.assertNotIn("run_turn", ra_idents)


if __name__ == "__main__":
    unittest.main()
