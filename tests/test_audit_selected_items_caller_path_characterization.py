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
import tempfile
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

# The single private bridge authorized (this slice) to pass
# ``audit_admitted_context_items`` into ``run_turn``. Historical fact: at ec17d2e
# NO ``torment_service`` module passed audit items into ``run_turn`` ("none
# exist"). This slice adds the first narrowly-scoped exception; the live
# invariant below locks the exception to exactly this module.
_APPROVED_AUDIT_ITEMS_BRIDGE = "audit_selected_items_runner_bridge.py"


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


def _alias_sets(tree, targets):
    """Guard hardening (2026-07-14, tests-only, Codex-required): local names
    bound (transitively) to each target — ``from ... import X as y`` plus
    ``y = obj.X`` / ``z = y`` rebinding chains, resolved to a fixpoint per
    module. Aliasing must not evade the both-halves guard."""
    alias = {t: {t} for t in targets}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            for x in n.names:
                if x.name in alias:
                    alias[x.name].add(x.asname or x.name)
    changed = True
    while changed:
        changed = False
        for n in ast.walk(tree):
            if (isinstance(n, ast.Assign) and len(n.targets) == 1
                    and isinstance(n.targets[0], ast.Name)):
                tgt = n.targets[0].id
                v = n.value
                for t, names in alias.items():
                    bound = ((isinstance(v, ast.Attribute) and v.attr == t)
                             or (isinstance(v, ast.Name) and v.id in names))
                    if bound and tgt not in names:
                        names.add(tgt)
                        changed = True
    return alias


def _called_targets(func_node, alias):
    """Which alias-set targets this function calls — directly (``X(...)`` /
    ``obj.X(...)``) or through any alias name from ``_alias_sets``."""
    called = set()
    for n in ast.walk(func_node):
        if isinstance(n, ast.Call):
            f = n.func
            for t, names in alias.items():
                if ((isinstance(f, ast.Name) and f.id in names)
                        or (isinstance(f, ast.Attribute) and f.attr == t)):
                    called.add(t)
    return called


def _orchestrator_importers(root):
    """Recursive, fail-closed dormancy scan (guard hardening, 2026-07-14,
    Codex-required): every ``.py`` under ``root`` (skipping caches /
    do_not_touch), reported by root-relative path, whose source bytes mention
    the dormant orchestrator module name — excluding the module itself."""
    importers = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in {"__pycache__", ".git", ".mypy_cache",
                                    ".pytest_cache", ".venv", "node_modules"}
                       and not d.startswith("do_not_touch")]
        for fn in sorted(filenames):
            if not fn.endswith(".py") or fn == "memory_context_orchestrator.py":
                continue
            path = os.path.join(dirpath, fn)
            with open(path, "rb") as fh:
                if b"memory_context_orchestrator" in fh.read():
                    importers.append(
                        os.path.relpath(path, root).replace("\\", "/"))
    return sorted(importers)


# --------------------------------------------------------------------------- #
# Source / AST characterization
# --------------------------------------------------------------------------- #

class TestNoProductionCallerOwnsBothHalves(unittest.TestCase):

    # Guard reconciliation (2026-07-14, tests-only), after the dormant
    # memory-context orchestrator landing (`b3b5647`, candidate 6). Exactly ONE
    # production-directory function is recognized as owning both halves IN SHAPE
    # ONLY. It is NOT a live caller path: the module is imported and called by
    # no production module (proven below and fenced in
    # tests/test_memory_to_prompt_memory_context_orchestrator.py). This
    # recognition authorizes NO live caller ownership and must NOT be
    # generalized: the exemption is one module:function, valid only while the
    # module stays dormant.
    _DORMANT_ORCHESTRATOR_FILE = "memory_context_orchestrator.py"
    _DORMANT_BOTH_HALVES_SHAPE = (
        "memory_context_orchestrator.py:run_turn_with_memory_context"
    )

    def _orchestrator_production_importers(self):
        """Service modules (besides the orchestrator itself) that mention the
        orchestrator module name at all — fail-closed dormancy evidence.
        RECURSIVE under torment_service/ (Codex-required): subpackage
        references are reported service-relative."""
        return _orchestrator_importers(_torment_service_dir())

    def test_no_function_calls_assemble_context_and_run_turn(self):
        offenders = []
        for fn, tree in _iter_service_trees():
            # Alias-aware (Codex-required): module-level or local rebinding of
            # either half (``ac = assemble_context`` / ``rt = runner.run_turn``
            # / import-as) must not evade detection.
            alias = _alias_sets(tree, ("assemble_context", "run_turn"))
            for func in _all_functions(tree):
                called = _called_targets(func, alias)
                if "assemble_context" in called and "run_turn" in called:
                    offenders.append(f"{fn}:{func.name}")
        # The exemption below holds ONLY while the orchestrator is proven
        # dormant; any production reference voids it and this test goes red.
        self.assertEqual(
            self._orchestrator_production_importers(), [],
            msg="dormant-orchestrator exemption void: production references the "
                "orchestrator; both-halves ownership is no longer shape-only",
        )
        # Exactly the pinned dormant candidate shape — nothing else, ever,
        # without a fresh, separately authorized reconciliation.
        self.assertEqual(
            offenders, [self._DORMANT_BOTH_HALVES_SHAPE],
            msg=("production function owns both assemble_context + run_turn "
                 f"beyond the pinned dormant candidate shape: {offenders}"),
        )

    def test_only_approved_bridge_passes_audit_items_into_run_turn(self):
        """Historical fact (ec17d2e): NO ``torment_service`` module passed
        ``audit_admitted_context_items`` into ``run_turn`` -- "none exist". This
        slice authorizes EXACTLY ONE private bridge to do so. Live invariant: the
        only service module that passes ``audit_admitted_context_items`` into
        ``run_turn`` is the approved private selected-items runner bridge, and
        that module exists at the approved path. (Renamed from the prior
        ``test_no_production_caller_passes_audit_items_into_run_turn``; the
        absolute "none exist" claim was true only for the pre-bridge topology.)"""
        callers = set()
        for fn, tree in _iter_service_trees():
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "run_turn"
                        and any(k.arg == "audit_admitted_context_items" for k in n.keywords)):
                    callers.add(fn)
        self.assertEqual(
            sorted(callers), [_APPROVED_AUDIT_ITEMS_BRIDGE],
            msg=("exactly the approved private bridge may pass "
                 f"audit_admitted_context_items into run_turn; got: {sorted(callers)}"),
        )
        self.assertTrue(
            os.path.exists(os.path.join(_torment_service_dir(),
                                        _APPROVED_AUDIT_ITEMS_BRIDGE)),
            msg="approved selected-items runner bridge module is missing",
        )


class TestApprovedBridgeShape(unittest.TestCase):
    """Locks the SHAPE of the single authorized exception (the private
    selected-items runner bridge): it CALLS the pure extractor and forwards the
    extractor's selected item dicts -- never a raw parameter such as the whole
    caller-supplied ``AssembledContext``."""

    def setUp(self):
        self.bridge = _parse_service(_APPROVED_AUDIT_ITEMS_BRIDGE)

    def test_bridge_calls_selected_items_extractor(self):
        self.assertIn(
            "selected_admitted_items", _called_names(self.bridge),
            msg="approved bridge does not call selected_admitted_items",
        )

    def test_bridge_forwards_extracted_items_not_a_raw_parameter(self):
        # The value forwarded as ``audit_admitted_context_items`` must NOT be one
        # of the bridge function's own parameters (which include the whole
        # caller-supplied assembled context). It must be a local -- the extractor
        # output -- proving only selected item dicts are forwarded.
        offenders = []
        for fn_node in _all_functions(self.bridge):
            param_names = {a.arg for a in fn_node.args.args}
            param_names |= {a.arg for a in fn_node.args.kwonlyargs}
            param_names |= {a.arg for a in fn_node.args.posonlyargs}
            for n in ast.walk(fn_node):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "run_turn"):
                    for k in n.keywords:
                        if (k.arg == "audit_admitted_context_items"
                                and isinstance(k.value, ast.Name)
                                and k.value.id in param_names):
                            offenders.append((fn_node.name, k.value.id))
        self.assertEqual(
            offenders, [],
            msg=f"bridge forwards a raw parameter as audit items: {offenders}",
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
        # Post-extraction: items route to the audit-evidence helper (which routes
        # them only to the inclusion observer) and TurnResult.
        receivers = _call_receivers(self.run_turn, "audit_admitted_context_items")
        allowed = {"_observe_audit_evidence_from_prompt_request", "TurnResult"}
        self.assertLessEqual(
            receivers, allowed,
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


class TestGuardTeethAliasedBothHalves(unittest.TestCase):
    """Teeth (Codex-required): aliased / rebound halves are detected as
    both-halves ownership; a single half is not flagged. Synthetic sources
    only — no production code involved."""

    def _called(self, src):
        tree = ast.parse(src)
        alias = _alias_sets(tree, ("assemble_context", "run_turn"))
        func = _all_functions(tree)[0]
        return _called_targets(func, alias)

    def test_local_rebinding_of_both_halves_detected(self):
        src = (
            "def f(runner, ctx):\n"
            "    rt = runner.run_turn\n"
            "    ac = assemble_context\n"
            "    ac(ctx)\n"
            "    rt()\n"
        )
        self.assertEqual(self._called(src), {"assemble_context", "run_turn"})

    def test_imported_alias_of_assemble_context_detected(self):
        src = (
            "from torment_service.retrieval_assembler "
            "import assemble_context as ac\n"
            "def f(runner, ctx):\n"
            "    rt = runner.run_turn\n"
            "    ac(ctx)\n"
            "    rt()\n"
        )
        self.assertEqual(self._called(src), {"assemble_context", "run_turn"})

    def test_transitive_rebinding_detected(self):
        src = (
            "def f(runner, ctx):\n"
            "    rt = runner.run_turn\n"
            "    rt2 = rt\n"
            "    ac = assemble_context\n"
            "    ac2 = ac\n"
            "    ac2(ctx)\n"
            "    rt2()\n"
        )
        self.assertEqual(self._called(src), {"assemble_context", "run_turn"})

    def test_one_half_only_not_flagged_as_both(self):
        src = (
            "def f(runner, ctx):\n"
            "    rt = runner.run_turn\n"
            "    rt()\n"
        )
        self.assertEqual(self._called(src), {"run_turn"})


class TestGuardTeethRecursiveImporterScan(unittest.TestCase):
    """Teeth (Codex-required): the dormancy importer scan is recursive and
    reports root-relative paths; the orchestrator itself never counts."""

    def test_subpackage_reference_detected(self):
        with tempfile.TemporaryDirectory() as root:
            sub = os.path.join(root, "some_subdir")
            os.makedirs(sub)
            with open(os.path.join(sub, "sneaky.py"), "w", encoding="utf-8") as fh:
                fh.write("from torment_service import memory_context_orchestrator\n")
            self.assertEqual(_orchestrator_importers(root),
                             ["some_subdir/sneaky.py"])

    def test_module_itself_and_clean_files_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "memory_context_orchestrator.py"),
                      "w", encoding="utf-8") as fh:
                fh.write("# self\n")
            with open(os.path.join(root, "clean.py"), "w", encoding="utf-8") as fh:
                fh.write("x = 1\n")
            self.assertEqual(_orchestrator_importers(root), [])


if __name__ == "__main__":
    unittest.main()
