"""Characterization: current output surfaces and the audit-packet co-occurrence gap.

SCOPE (read carefully):
    * This file characterizes EXISTING output surfaces and observation-only
      sidecar precedents as they are today. It attaches **no audit packet**,
      **selects no sink**, and performs **no production wiring**.
    * It is **not** a live evaluator / model / provider integration. The
      response-generation path is inspected by source/AST only; no model is
      called and no llm_client is exercised.
    * Updated finding (post ``audit_admitted_context_items`` staging seam):
      ``agent_loop.TurnResult`` can now STAGE the final reviewed ``response_text``
      (via ``execution_outcome``) alongside caller-supplied candidate admitted
      context (``audit_admitted_context_items``) — so the two halves CAN coexist
      on ``TurnResult``. The invariant this file now guards is therefore **no
      audit packet sidecar is built or attached in production**, NOT "no
      response/context coexistence anywhere". Staging is observation-only; it
      selects no sink and proves no same-turn provenance.
    * Endpoint surfaces are unchanged: ``app.py::retrieve_assembled``
      (``/retrieve``) holds assembler prompt context (``assemble_context`` /
      ``assembled.to_dict()``) but generates no ``response_text``;
      ``app.py::query`` (``/agent/query``) returns ``fabric.query(...)``, not
      generated text. ``AgentRunner.run_turn`` / ``_execute`` generate/review
      ``response_text`` and now accept the staging field, but still
      import/build no assembler context and no audit packet.
    * Explicitly NOT covered / NOT claimed: this does not select any surface as
      the future packet sink; it does not claim ``response_text`` and assembler
      context never coexist (``TurnResult`` staging is the explicit exception);
      and it does not assert any live response path uses assembled context.

The next implementation step after this characterization would CHOOSE or CREATE
an actual sink, and therefore requires a separate review/ratification.

All assertions use AST / source inspection only (files located via ``__file__``);
the module imports no ``torment_service`` code and exercises no runtime path.
"""

import ast
import os
import unittest


# --- file locations (no torment_service import) ----------------------------

def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _parse(filename):
    path = os.path.join(_torment_service_dir(), filename)
    with open(path, "r", encoding="utf-8") as fh:
        return ast.parse(fh.read())


# --- tiny AST helpers ------------------------------------------------------

# Names that would indicate live model response generation.
GENERATION_CALL_NAMES = {
    "generate", "complete", "completion", "completions",
    "chat", "chat_completion", "create_completion",
    "create_chat_completion", "predict", "infer",
}


def _top_func(tree, name):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _class(tree, name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _method(class_node, name):
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _idents(*nodes):
    """Union of Name ids, Attribute attrs, and keyword-arg names under nodes."""
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


def _calls_method_on(node, obj_name, method_name):
    for n in ast.walk(node):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == method_name
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == obj_name):
            return True
    return False


def _has_attr_load(tree, attr_name):
    for n in ast.walk(tree):
        if (isinstance(n, ast.Attribute) and n.attr == attr_name
                and isinstance(n.ctx, ast.Load)):
            return True
    return False


_ASSEMBLER_CONTEXT_NAMES = {"assemble_context", "AssembledContext", "assembled_text"}


class TestAgentRunnerGenerationButNoAssembledContext(unittest.TestCase):
    """AgentRunner.run_turn / _execute generate+review response_text but
    reference no assembler prompt context. (The staging seam now lets the caller
    supply candidate admitted context via ``audit_admitted_context_items``, but
    AgentRunner itself still imports/builds no assembler context and no packet —
    see test_agent_runner_stages_admitted_context_but_builds_no_packet.)"""

    def test_agent_runner_has_response_generation_but_no_assembled_context(self):
        tree = _parse("agent_loop.py")
        runner = _class(tree, "AgentRunner")
        self.assertIsNotNone(runner, "AgentRunner class not found")
        run_turn = _method(runner, "run_turn")
        _execute = _method(runner, "_execute")
        self.assertIsNotNone(run_turn, "AgentRunner.run_turn not found")
        self.assertIsNotNone(_execute, "AgentRunner._execute not found")

        idents = _idents(run_turn, _execute)
        # Response-generation surface exists in the scoped methods.
        self.assertIn("complete", idents, "expected LLMClient.complete(...) surface")
        self.assertIn("ExecutionOutcome", idents, "expected ExecutionOutcome surface")
        self.assertIn("response_text", idents, "expected response_text surface")
        # ...but no assembler prompt context co-occurs in those methods (today).
        leaked = _ASSEMBLER_CONTEXT_NAMES & idents
        self.assertEqual(
            leaked, set(),
            msg=(
                "current co-occurrence gap violated: assembler context names "
                f"appeared in AgentRunner.run_turn/_execute: {sorted(leaked)}"
            ),
        )

    def test_agent_runner_stages_admitted_context_but_builds_no_packet(self):
        # Post-staging-seam invariant: AgentRunner can STAGE caller-supplied
        # candidate admitted context (audit_admitted_context_items) but builds /
        # attaches NO audit packet — no packet / sidecar / extractor builder is
        # referenced anywhere in agent_loop.py.
        tree = _parse("agent_loop.py")
        runner = _class(tree, "AgentRunner")
        run_turn = _method(runner, "run_turn")
        self.assertIn(
            "audit_admitted_context_items", _idents(run_turn),
            "expected the staging field on AgentRunner.run_turn",
        )
        module_idents = _idents(tree)
        for builder in ("build_audit_evidence_packet", "selected_admitted_items",
                        "build_audit_evidence_sidecar_from_items",
                        "build_audit_evidence_sidecar_from_assembled_context"):
            self.assertNotIn(
                builder, module_idents,
                msg=f"agent_loop.py references packet builder: {builder}",
            )


class TestRetrieveAssembledHasContextButNoGeneration(unittest.TestCase):
    """retrieve_assembled holds the assembler prompt context but produces no
    generated response_text (the current co-occurrence gap on the assembler
    side)."""

    def test_retrieve_assembled_has_context_but_no_generation_or_response_text(self):
        tree = _parse("app.py")
        fn = _top_func(tree, "retrieve_assembled")
        self.assertIsNotNone(fn, "retrieve_assembled handler not found")
        idents = _idents(fn)

        self.assertIn("assemble_context", idents, "expected assemble_context(...)")
        self.assertTrue(
            _calls_method_on(fn, "assembled", "to_dict"),
            "expected assembled.to_dict() usage",
        )
        offenders = idents & GENERATION_CALL_NAMES
        self.assertEqual(offenders, set(), f"unexpected generation call(s): {sorted(offenders)}")
        self.assertNotIn("response_text", idents, "retrieve_assembled should carry no response_text")


class TestAgentQueryReturnsFabricQuery(unittest.TestCase):
    """/agent/query returns fabric.query(...) — not generated response text."""

    def test_agent_query_returns_fabric_query_not_generation_response(self):
        tree = _parse("app.py")
        fn = _top_func(tree, "query")
        self.assertIsNotNone(fn, "query handler not found")
        idents = _idents(fn)

        self.assertTrue(
            _calls_method_on(fn, "fabric", "query"),
            "expected fabric.query(...) call",
        )
        offenders = idents & GENERATION_CALL_NAMES
        self.assertEqual(offenders, set(), f"unexpected generation call(s): {sorted(offenders)}")
        self.assertNotIn("response_text", idents, "query should carry no response_text")


class TestNoCurrentEndpointIsSameTurnAuditPacketSink(unittest.TestCase):
    """Of the two model-audit-relevant endpoint candidates, neither carries
    BOTH a generated response_text and the assembler prompt context.

    Out of scope (and deliberately NOT claimed here): other post-response
    write-back endpoints. Those are not same-turn generation sinks; this test
    inspects only ``query`` and ``retrieve_assembled``."""

    def test_no_current_app_endpoint_is_a_same_turn_audit_packet_sink(self):
        tree = _parse("app.py")
        for name in ("query", "retrieve_assembled"):
            fn = _top_func(tree, name)
            self.assertIsNotNone(fn, f"{name} handler not found")
            idents = _idents(fn)
            has_response_text = "response_text" in idents
            has_assembled_context = bool(_ASSEMBLER_CONTEXT_NAMES & idents)
            self.assertFalse(
                has_response_text and has_assembled_context,
                msg=(
                    f"{name} unexpectedly carries BOTH response_text and assembler "
                    "context; the current co-occurrence gap would be closed here"
                ),
            )


class TestTurnResultReflectionTraceIsOptionalObservationSidecar(unittest.TestCase):
    """TurnResult.reflection_trace is an optional, default-None observation-only
    sidecar that is never read back as an attribute in agent_loop.py.

    This characterizes an existing precedent shape only; it does NOT select
    TurnResult as the future audit-packet sink."""

    def test_turn_result_reflection_trace_is_optional_observation_sidecar(self):
        tree = _parse("agent_loop.py")
        turn_result = _class(tree, "TurnResult")
        self.assertIsNotNone(turn_result, "TurnResult dataclass not found")

        ann = None
        for node in turn_result.body:
            if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                    and node.target.id == "reflection_trace"):
                ann = node
                break
        self.assertIsNotNone(ann, "TurnResult.reflection_trace field not found")

        # Default is None.
        self.assertTrue(
            isinstance(ann.value, ast.Constant) and ann.value.value is None,
            "reflection_trace default should be None",
        )
        # Annotation is Optional-shaped.
        ann_names = {n.id for n in ast.walk(ann.annotation) if isinstance(n, ast.Name)}
        self.assertIn("Optional", ann_names, "reflection_trace should be Optional[...]")

        # Coarse non-reentry: it is never read back via `<obj>.reflection_trace`
        # (it is only constructed/assigned, never consumed in a decision path).
        self.assertFalse(
            _has_attr_load(tree, "reflection_trace"),
            "reflection_trace appears to be read back as an attribute in agent_loop.py",
        )


class TestRetrieveAssemblyAuditIsOptInSidecar(unittest.TestCase):
    """The assembly_audit sidecar on /retrieve is opt-in: default False on the
    request model, and only attached inside the include_assembly_audit guard.
    Coarse precedent check only."""

    def test_retrieve_assembly_audit_is_opt_in_sidecar(self):
        path = os.path.join(_torment_service_dir(), "app.py")
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src)

        # Default-false on the request model (targeted source check, not a scan).
        self.assertIn(
            "include_assembly_audit: bool = False", src,
            "expected include_assembly_audit to default to False",
        )

        fn = _top_func(tree, "retrieve_assembled")
        self.assertIsNotNone(fn, "retrieve_assembled handler not found")

        # Every assignment of response["assembly_audit"] must sit under an
        # `if ... include_assembly_audit ...` guard.
        guard_ifs = [
            n for n in ast.walk(fn)
            if isinstance(n, ast.If) and "include_assembly_audit" in _idents(n.test)
        ]
        self.assertTrue(guard_ifs, "expected an include_assembly_audit guard in retrieve_assembled")

        def _is_assembly_audit_store(node):
            return (
                isinstance(node, ast.Subscript)
                and isinstance(node.ctx, ast.Store)
                and isinstance(node.slice, ast.Constant)
                and node.slice.value == "assembly_audit"
            )

        all_stores = [n for n in ast.walk(fn) if _is_assembly_audit_store(n)]
        guarded_stores = [
            n for g in guard_ifs for n in ast.walk(g) if _is_assembly_audit_store(n)
        ]
        self.assertTrue(all_stores, "expected response['assembly_audit'] assignment")
        self.assertEqual(
            len(all_stores), len(guarded_stores),
            "response['assembly_audit'] must only be set behind the include_assembly_audit guard",
        )


if __name__ == "__main__":
    unittest.main()
