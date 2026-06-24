"""Characterization: selected-items caller-path topology after the live
prompt-inclusion observer connection (source/AST + one behavioral non-control
proof). Tests-only — NO production caller, NO wiring.

Codex returned PASS, narrowly, for Candidate A only as a tests-only / source-only
caller-path characterization FIRST. This file adds NO production code, NO
endpoint, NO `/retrieve` or `/agent/query` wiring, NO prompt-memory injection, NO
public API/schema, NO new ``TurnResult`` field, and NO prompt-request exposure.
It characterizes the current topology and the observation-only non-control
property of supplying selected items into ``AgentRunner`` before any
prompt-memory injection exists.

Why tests-only first: there is still no production path that owns both halves —
``/retrieve`` owns ``assemble_context(...)`` but produces no generated response;
``AgentRunner`` owns generation + prompt capture but consumes no assembler
output; ``/agent/query`` returns ``fabric.query(...)``, not ``run_turn(...)``.
Supplying selected items into ``AgentRunner`` is safe *only* as observation
input: the observer returns ``None`` unless the selected item text is actually
present in the captured prompt request.

It proves:
  1. No production caller both calls ``assemble_context(...)`` AND ``run_turn(...)``.
  2. No production caller passes ``audit_admitted_context_items``.
  3. ``app.py`` still does not import/call ``AgentRunner``.
  4. ``/retrieve`` has assembled context but no generation / ``response_text``.
  5. ``/agent/query`` has no assembled context and no ``AgentRunner`` generation.
  6. ``agent_loop.py`` does not import ``retrieval_assembler`` / ``audit_evidence_context``
     and does not call ``selected_admitted_items(...)``.
  7. Audit items in ``run_turn`` route only to ``observe_prompt_inclusion_packet(...)``
     and ``TurnResult``.
  8. Selected items whose text is absent from the captured prompt yield a ``None``
     packet while response / review / ingest / fabric proceed unchanged
     (packet absence is non-punitive).
  9. No forbidden proof/claim flag exists in the audit-relevant production surfaces.

No forbidden wording is introduced (the set below is a quoted guard list).
"""

import ast
import os
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from torment_service.agent_loop import AgentRunner, Observation
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ReviewResult


# Quoted guard list (allowed exception to the forbidden-wording rule).
_FORBIDDEN_FLAGS = {
    "same_turn_verified", "verified", "truth", "authority",
    "trusted", "certified", "honest",
}


def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _parse_service(filename):
    with open(os.path.join(_torment_service_dir(), filename), "rb") as fh:
        # null-strip tolerates a mount-corruption artifact in some sandboxes;
        # the authoritative Windows repo parses cleanly.
        return ast.parse(fh.read().replace(b"\x00", b""))


def _iter_service_trees():
    svc = _torment_service_dir()
    for fn in sorted(os.listdir(svc)):
        if not fn.endswith(".py"):
            continue
        try:
            yield fn, _parse_service(fn)
        except (SyntaxError, ValueError):
            continue


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
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
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


def _called_names(node):
    """Every called function's leaf name (``foo`` or ``x.foo``) under ``node``."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.id if isinstance(f, ast.Name)
                    else f.attr if isinstance(f, ast.Attribute) else "")
    return out


def _all_functions(tree):
    return [n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _call_receivers(func_node, var_name):
    """Func leaf-names of every Call that receives ``var_name`` (a Name) as a
    positional or keyword-value argument."""
    receivers = set()
    for n in ast.walk(func_node):
        if isinstance(n, ast.Call):
            passed = [a.id for a in n.args if isinstance(a, ast.Name)]
            passed += [k.value.id for k in n.keywords if isinstance(k.value, ast.Name)]
            if var_name in passed:
                f = n.func
                receivers.add(f.id if isinstance(f, ast.Name)
                              else f.attr if isinstance(f, ast.Attribute) else "?")
    return receivers


# --------------------------------------------------------------------------- #
# Source / AST characterization
# --------------------------------------------------------------------------- #

class TestNoProductionCallerOwnsBothHalves(unittest.TestCase):

    def test_no_function_calls_assemble_context_and_run_turn(self):
        offenders = []
        for fn, tree in _iter_service_trees():
            for func in _all_functions(tree):
                calls = _called_names(func)
                if "assemble_context" in calls and "run_turn" in calls:
                    offenders.append(f"{fn}:{func.name}")
        self.assertEqual(
            offenders, [],
            msg=f"production function owns both assemble_context + run_turn: {offenders}",
        )

    def test_no_production_caller_passes_audit_items_into_run_turn(self):
        offenders = []
        for fn, tree in _iter_service_trees():
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "run_turn"
                        and any(k.arg == "audit_admitted_context_items" for k in n.keywords)):
                    offenders.append(fn)
        self.assertEqual(
            offenders, [],
            msg=f"production run_turn caller passes audit_admitted_context_items: {offenders}",
        )


class TestEndpointHalves(unittest.TestCase):

    def setUp(self):
        self.app = _parse_service("app.py")

    def test_app_does_not_import_or_call_agent_runner(self):
        leaves, names = _import_leaves_names(self.app)
        self.assertNotIn("agent_loop", leaves, "app.py imports agent_loop")
        self.assertNotIn("AgentRunner", names, "app.py imports AgentRunner")
        app_idents = _idents(self.app)
        self.assertNotIn("AgentRunner", app_idents)
        self.assertNotIn("run_turn", app_idents)

    def test_retrieve_has_assembled_context_but_no_generation(self):
        ra = _top_func(self.app, "retrieve_assembled")
        self.assertIsNotNone(ra, "retrieve_assembled handler not found")
        idents = _idents(ra)
        self.assertIn("assemble_context", idents)
        self.assertNotIn("response_text", idents)
        self.assertNotIn("complete", idents)
        self.assertNotIn("run_turn", idents)
        self.assertNotIn("AgentRunner", idents)

    def test_agent_query_has_no_assembled_context_or_generation(self):
        q = _top_func(self.app, "query")
        self.assertIsNotNone(q, "query handler not found")
        idents = _idents(q)
        self.assertNotIn("assemble_context", idents)
        self.assertNotIn("AssembledContext", idents)
        self.assertNotIn("response_text", idents)
        self.assertNotIn("complete", idents)
        self.assertNotIn("run_turn", idents)
        self.assertNotIn("AgentRunner", idents)


class TestAgentLoopOwnsNoAssemblerOrExtractor(unittest.TestCase):

    def setUp(self):
        self.tree = _parse_service("agent_loop.py")
        self.runner = _class(self.tree, "AgentRunner")
        self.run_turn = _method(self.runner, "run_turn")

    def test_agent_loop_imports_no_assembler_or_extractor(self):
        leaves, names = _import_leaves_names(self.tree)
        self.assertNotIn("retrieval_assembler", leaves)
        self.assertNotIn("audit_evidence_context", leaves)
        self.assertNotIn("AssembledContext", names)

    def test_agent_loop_does_not_call_selected_admitted_items(self):
        self.assertNotIn("selected_admitted_items", _called_names(self.tree))

    def test_audit_items_route_only_to_observer_and_turnresult(self):
        self.assertIsNotNone(self.run_turn, "run_turn not found")
        receivers = _call_receivers(self.run_turn, "audit_admitted_context_items")
        allowed = {"observe_prompt_inclusion_packet", "TurnResult"}
        self.assertTrue(
            receivers <= allowed,
            msg=f"audit items routed to unexpected call(s): {sorted(receivers - allowed)}",
        )


class TestNoForbiddenFlagInAuditSurfaces(unittest.TestCase):

    def test_no_forbidden_proof_or_claim_flag(self):
        # AST identifier-EXACT match (Name/Attribute/keyword), so legitimate
        # tokens like ``authority_status`` do not false-match ``authority`` and
        # docstring/comment prose is ignored.
        surfaces = set()
        for fn in ("audit_prompt_inclusion_observation.py", "audit_evidence_sidecar.py",
                   "audit_evidence_packet.py", "audit_evidence_context.py"):
            try:
                surfaces |= _idents(_parse_service(fn))
            except (SyntaxError, ValueError):
                pass
        runner = _class(_parse_service("agent_loop.py"), "AgentRunner")
        surfaces |= _idents(_method(runner, "run_turn"))
        offenders = surfaces & _FORBIDDEN_FLAGS
        self.assertEqual(
            offenders, set(),
            msg=f"forbidden proof/claim flag in audit-relevant surfaces: {sorted(offenders)}",
        )


# --------------------------------------------------------------------------- #
# Behavioral non-control proof (fake fabric + fake LLM + forced review)
# --------------------------------------------------------------------------- #

@dataclass
class _FakeFabric:
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)
    drift_return: Optional[Dict[str, Any]] = None

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append({"text": text, "step": step})
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append({"workspace_id": workspace_id})
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append({"drift_info": drift_info})


@dataclass
class _FakeLLM:
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_response: str = "A clean reply."

    def complete(self, system_prompt, messages, tools=None):
        from torment_service.agent_loop import LLMResponse
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        return LLMResponse(text=self.canned_response)


class _ForcedReview(ThinkingController):
    def __init__(self, forced):
        super().__init__()
        self._forced = forced
        self.review_drafts: List[Any] = []

    def review(self, *, frame, mode, action, response_draft):
        self.review_drafts.append(response_draft)
        return self._forced


_OBS = "a benign user question with nothing notable"
_ABSENT_ITEM = "ZZABSENT selected admitted item text not in the prompt"


def _items(text):
    return [{"eid": 1, "block_type": "relational_context", "text": text}]


def _run(audit_items):
    fabric = _FakeFabric()
    controller = _ForcedReview(ReviewResult(approved=True, revised=True,
                                            revised_text="a reviewed reply"))
    runner = AgentRunner(controller=controller, fabric=fabric, llm_client=_FakeLLM())
    kwargs = {}
    if audit_items is not None:
        kwargs["audit_admitted_context_items"] = audit_items
    result = runner.run_turn(
        workspace_id="ws", agent_id="agent",
        observation=Observation(text=_OBS), step=1, **kwargs,
    )
    return result, fabric, controller


class TestSupplyingAbsentItemsIsNonControl(unittest.TestCase):
    """Supplying selected items whose text is absent from the captured prompt is
    observation input only: it yields no packet and changes nothing about
    response / review / ingest / fabric versus the no-items control."""

    def test_absent_items_yield_no_packet_and_change_nothing(self):
        ctrl_result, ctrl_fabric, ctrl_controller = _run(None)
        exp_result, exp_fabric, exp_controller = _run(_items(_ABSENT_ITEM))

        # Item text absent from the prompt -> no packet, in both runs.
        self.assertIsNone(ctrl_result.audit_evidence_packet)
        self.assertIsNone(exp_result.audit_evidence_packet)

        # Packet absence is non-punitive: the turn produced the normal reviewed
        # response (not blocked / suppressed / emptied).
        self.assertEqual(exp_result.execution_outcome.response_text, "a reviewed reply")

        # Response unchanged vs control.
        self.assertEqual(exp_result.execution_outcome.response_text,
                         ctrl_result.execution_outcome.response_text)
        # Review behavior unchanged (same number of review passes, same drafts).
        self.assertEqual(exp_controller.review_drafts, ctrl_controller.review_drafts)
        # Ingest behavior unchanged.
        self.assertEqual(exp_fabric.ingest_calls, ctrl_fabric.ingest_calls)
        # Fabric drift / gravity behavior unchanged.
        self.assertEqual(len(exp_fabric.measure_drift_calls),
                         len(ctrl_fabric.measure_drift_calls))
        self.assertEqual(exp_fabric.gravity_correction_calls,
                         ctrl_fabric.gravity_correction_calls)

    def test_absent_items_never_enter_prompt_review_or_ingest(self):
        # The supplied item text never reaches the model-visible prompt, the
        # review input, the ingest text, or any fabric side effect.
        fabric = _FakeFabric()
        controller = _ForcedReview(ReviewResult(approved=True, revised=True,
                                                revised_text="a reviewed reply"))
        llm = _FakeLLM()
        runner = AgentRunner(controller=controller, fabric=fabric, llm_client=llm)
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS), step=1,
            audit_admitted_context_items=_items(_ABSENT_ITEM),
        )
        for call in llm.calls:
            self.assertNotIn(_ABSENT_ITEM, str(call.get("system_prompt", "")))
            self.assertNotIn(_ABSENT_ITEM, str(call.get("messages", "")))
        self.assertNotIn(_ABSENT_ITEM, str(controller.review_drafts))
        for call in fabric.ingest_calls:
            self.assertNotIn(_ABSENT_ITEM, str(call.get("text", "")))
        self.assertNotIn(_ABSENT_ITEM, str(fabric.measure_drift_calls))
        self.assertNotIn(_ABSENT_ITEM, str(fabric.gravity_correction_calls))
        self.assertNotIn(_ABSENT_ITEM, (result.execution_outcome.response_text or ""))
        self.assertNotIn(_ABSENT_ITEM, str(result.metadata))
        self.assertIsNone(result.audit_evidence_packet)


if __name__ == "__main__":
    unittest.main()
