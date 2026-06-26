"""A-prime characterization: where an honest same-turn provenance owner could live.

Codex/operator decision REVISE-A → A-prime: an internal provenance owner must
control or OBSERVE the actual model-visible context used to generate the
response — not merely hold both halves in one call frame. Passing selected
admitted item dicts into ``AgentRunner.run_turn`` is NOT provenance proof, and
structural co-location on ``TurnResult`` is NOT provenance.

This file is tests-only / source-only. It wires NOTHING, defines NO live owner,
adds NO production code, NO harness claiming provenance, NO endpoint/schema/API,
and NO verification/provenance/truth/authority flag. It characterizes the current
architecture and states the A-prime obligation:

  * The model-visible context construction boundary today is
    ``AgentRunner._execute`` passing the local prompt request's fields
    (``req.system_prompt`` / ``req.messages`` / ``req.tools``) to
    ``LLMClient.complete(...)``; the request is built by
    ``_build_llm_prompt_request`` from ``_build_system_prompt(frame, mode)`` and
    ``messages`` derived from ``frame.raw_input``.
  * That prompt path consumes NO assembled context and NO
    ``audit_admitted_context_items`` — so the admitted items are NOT part of the
    model-visible context that produced the response.
  * Therefore a caller that retrieves/assembles then calls ``run_turn(...)`` would
    create structural co-location, not honest same-turn provenance.
  * No production owner currently sits at / observes that boundary while also
    supplying the same items, and no production caller supplies the items at all.
  * Obligation for ANY future owner: prove the selected item texts are actually
    present in the model-visible context used for that generated response
    (inclusion), never inferred from co-location.

All assertions use AST / source inspection (no ``torment_service`` import); a
small synthetic inclusion-predicate makes the A-prime obligation executable now.
"""

import ast
import os
import unittest


_ASSEMBLER_CTX_NAMES = {"assemble_context", "AssembledContext", "assembled_text"}
_PROVENANCE_FLAGS = (
    "same_turn_verified", "verified_same_turn", "provenance_verified",
    "truth_verified", "authority_verified", "same_turn_provenance",
)
_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}

# The single approved private bridge authorized to reference / pass
# ``audit_admitted_context_items`` into ``run_turn`` (observation-only; service-dir
# relative path, since this file walks torment_service/).
_APPROVED_BRIDGE = "audit_selected_items_runner_bridge.py"


def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def _torment_service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _parse_bytes(raw):
    return ast.parse(raw.replace(b"\x00", b""))  # null-strip: mount artifact only


def _parse_service(filename):
    with open(os.path.join(_torment_service_dir(), filename), "rb") as fh:
        return _parse_bytes(fh.read())


def _class(tree, name):
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


def _method(cls, name):
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


def _call_receivers(func_node, var_name):
    """Func names of every Call that receives ``var_name`` (Name) as an arg."""
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


def _calls_attr_on_self_attr(node, outer_attr, method):
    """True if node calls ``self.<outer_attr>.<method>(...)``."""
    for n in ast.walk(node):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == method
                and isinstance(n.func.value, ast.Attribute)
                and n.func.value.attr == outer_attr):
            return True
    return False


def _all_complete_calls_pass_req_fields(node):
    """Every ``self.llm_client.complete(...)`` in ``node`` passes
    ``system_prompt=req.system_prompt``, ``messages=req.messages``,
    ``tools=req.tools`` (the local prompt-request object's fields, unchanged)."""
    found = False
    for n in ast.walk(node):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "complete"
                and isinstance(n.func.value, ast.Attribute)
                and n.func.value.attr == "llm_client"):
            continue
        found = True
        kw = {k.arg: k.value for k in n.keywords if k.arg}
        for field in ("system_prompt", "messages", "tools"):
            v = kw.get(field)
            if not (isinstance(v, ast.Attribute) and v.attr == field
                    and isinstance(v.value, ast.Name) and v.value.id == "req"):
                return False
    return found


# --- A-prime obligation, made executable now (synthetic; no live owner) -------

def _proves_same_turn_inclusion(selected_item_texts, model_visible_context_text):
    """The inclusion predicate any future owner MUST satisfy: every selected
    admitted item text is actually present in the model-visible context used to
    generate the response. Co-location alone never satisfies this."""
    return all(t in model_visible_context_text for t in selected_item_texts)


class TestModelVisibleContextBoundary(unittest.TestCase):
    """The model-visible context boundary is AgentRunner._execute → the local
    prompt request's fields passed to llm_client.complete(...); the request is
    built by _build_llm_prompt_request from _build_system_prompt + frame.raw_input.
    It consumes no assembled context and no admitted items."""

    def setUp(self):
        self.tree = _parse_service("agent_loop.py")
        self.runner = _class(self.tree, "AgentRunner")
        self.execute = _method(self.runner, "_execute")
        self.build_prompt = _method(self.runner, "_build_system_prompt")
        self.build_request = _method(self.runner, "_build_llm_prompt_request")
        self.complete_helper = _method(self.runner, "_complete_llm_prompt_request")

    def test_boundary_is_llmclient_complete_via_completion_helper(self):
        self.assertIsNotNone(self.execute)
        self.assertIsNotNone(self.complete_helper, "_complete_llm_prompt_request not found")
        # (1) Post-extraction: the model-visible boundary self.llm_client.complete(...)
        # lives in the thin completion helper, which _execute invokes.
        self.assertTrue(
            _calls_attr_on_self_attr(self.complete_helper, "llm_client", "complete"),
            "expected self.llm_client.complete(...) in the completion helper",
        )
        exec_idents = _idents(self.execute)
        helper_idents = _idents(self.complete_helper)
        self.assertIn("_complete_llm_prompt_request", exec_idents)
        self.assertIn("complete", helper_idents)
        # (2) _execute builds the prompt via the local request helper and (3) the
        # completion helper passes its fields to complete unchanged.
        self.assertIn("_build_llm_prompt_request", exec_idents)
        self.assertTrue(
            _all_complete_calls_pass_req_fields(self.complete_helper),
            "expected complete(system_prompt=req.system_prompt, messages=req.messages, tools=req.tools)",
        )
        # (4) The request helper preserves the ORIGINAL prompt source:
        # system_prompt via _build_system_prompt(frame, mode), messages from
        # frame.raw_input.
        self.assertIsNotNone(self.build_request, "_build_llm_prompt_request not found")
        req_idents = _idents(self.build_request)
        self.assertIn("_build_system_prompt", req_idents)
        self.assertIn("raw_input", req_idents)
        # (5) The boundary (execute + request helper + completion helper) is the
        # prompt request + complete — NOT assembled context, audit packet snippets,
        # or admitted items.
        boundary_idents = exec_idents | req_idents | helper_idents
        self.assertEqual(boundary_idents & _ASSEMBLER_CTX_NAMES, set(),
                         "prompt boundary consumes assembler context")
        self.assertNotIn("audit_admitted_context_items", boundary_idents)
        self.assertNotIn("audit_evidence_packet", boundary_idents)
        self.assertNotIn("evidence_items", boundary_idents)

    def test_execute_does_not_consume_assembled_context_or_audit_items(self):
        idents = _idents(self.execute)
        self.assertEqual(idents & _ASSEMBLER_CTX_NAMES, set(),
                         "_execute consumes assembler context")
        self.assertNotIn("audit_admitted_context_items", idents,
                         "_execute consumes audit_admitted_context_items")
        self.assertNotIn("audit_evidence_packet", idents)

    def test_build_system_prompt_does_not_consume_assembled_or_audit(self):
        self.assertIsNotNone(self.build_prompt)
        idents = _idents(self.build_prompt)
        self.assertEqual(idents & _ASSEMBLER_CTX_NAMES, set())
        self.assertNotIn("audit_admitted_context_items", idents)


class TestColocationIsNotProvenance(unittest.TestCase):
    """Supplying items to run_turn places them on TurnResult only — never into
    the model-visible prompt path — so co-location is not provenance."""

    def setUp(self):
        self.tree = _parse_service("agent_loop.py")
        self.runner = _class(self.tree, "AgentRunner")
        self.run_turn = _method(self.runner, "run_turn")

    def test_audit_items_reach_only_observer_and_turnresult(self):
        # Post-extraction: items now feed the audit-evidence helper (the
        # observation-only sink, which routes them only to the inclusion observer)
        # and TurnResult — never the prompt / review / ingest / fabric path.
        receivers = _call_receivers(self.run_turn, "audit_admitted_context_items")
        allowed = {"_observe_audit_evidence_from_prompt_request", "TurnResult"}
        self.assertTrue(
            receivers <= allowed,
            msg=f"audit items routed to unexpected call(s): {sorted(receivers - allowed)}",
        )

    def test_packet_reaches_only_turnresult(self):
        receivers = _call_receivers(self.run_turn, "_audit_evidence_packet")
        self.assertTrue(receivers <= {"TurnResult"},
                        msg=f"packet routed beyond TurnResult: {sorted(receivers)}")

    def test_a_wrapper_calling_runturn_would_not_prove_inclusion(self):
        # Mirror how _execute builds the model-visible context: system prompt +
        # the user input only — NOT the admitted items. A wrapper that retrieved
        # those items and then called run_turn(...) achieves co-location, not
        # inclusion: the predicate is False.
        selected_item_texts = ["ZZITEM alpha admitted fact", "ZZITEM beta admitted fact"]
        model_visible_context = "[system prompt built from frame+mode]\nuser: what time is it?"
        self.assertFalse(
            _proves_same_turn_inclusion(selected_item_texts, model_visible_context),
            "co-location must NOT satisfy the inclusion predicate",
        )


class TestSameTurnInclusionObligation(unittest.TestCase):
    """The A-prime obligation, executable now against synthetic data. Any future
    owner's tests MUST use this kind of inclusion proof (item texts present in
    the real model-visible context), never co-location."""

    def test_inclusion_predicate_true_only_when_items_in_model_visible_context(self):
        items = ["ZZX present fact", "ZZY present fact"]
        included = "system... ZZX present fact ... ZZY present fact ... user input"
        self.assertTrue(_proves_same_turn_inclusion(items, included))

    def test_inclusion_predicate_false_when_any_item_absent(self):
        items = ["ZZX present fact", "ZZMISSING absent fact"]
        partial = "system... ZZX present fact ... user input"
        self.assertFalse(_proves_same_turn_inclusion(items, partial))

    def test_obligation_is_defined_but_currently_unmet(self):
        # The predicate exists and is required of any future owner; but no live
        # owner exists yet (see TestNoCurrentOwner), so the obligation is defined
        # and currently has nothing to apply to. This is intentional.
        self.assertTrue(callable(_proves_same_turn_inclusion))


class TestNoCurrentOwner(unittest.TestCase):
    """No production code today connects the admitted items to the model-visible
    context boundary, no production caller supplies them, no endpoint supplies
    them, no AssembledContext enters the runner, and no provenance flag exists."""

    def _service_files(self):
        out = []
        for dirpath, dirnames, filenames in os.walk(_torment_service_dir()):
            dirnames[:] = [d for d in dirnames
                           if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
            for fn in filenames:
                if fn.endswith(".py"):
                    out.append(os.path.join(dirpath, fn))
        return out

    def _trees(self):
        for path in self._service_files():
            rel = os.path.relpath(path, _torment_service_dir()).replace("\\", "/")
            with open(path, "rb") as fh:
                raw = fh.read()
            try:
                yield rel, raw, _parse_bytes(raw)
            except (SyntaxError, ValueError):
                continue

    def test_audit_items_referenced_only_by_agent_loop_and_approved_bridge(self):
        # The admitted-items token appears in production ONLY in agent_loop (the
        # observation-only sink) and the approved private bridge (which forwards
        # selected item dicts into that sink). Within agent_loop it is absent from
        # the prompt-construction path — so nothing connects the items to the
        # model-visible context as a generation owner. Historical fact (ec17d2e):
        # before the approved bridge, agent_loop.py was the ONLY referent.
        referencing = set()
        for rel, raw, tree in self._trees():
            idents = _idents(tree)
            if "audit_admitted_context_items" in idents:
                referencing.add(rel)
        self.assertEqual(
            referencing, {"agent_loop.py", _APPROVED_BRIDGE},
            msg=f"unexpected production references to audit items: {sorted(referencing)}")
        runner = _class(_parse_service("agent_loop.py"), "AgentRunner")
        execute_idents = _idents(_method(runner, "_execute"),
                                 _method(runner, "_build_system_prompt"))
        self.assertNotIn("audit_admitted_context_items", execute_idents)

    def test_only_approved_bridge_run_turn_caller_passes_audit_items(self):
        # New invariant: the only service module that passes audit items into
        # run_turn is the approved private bridge. Historical fact (ec17d2e): none did.
        callers = []
        for rel, raw, tree in self._trees():
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "run_turn"):
                    if any(k.arg == "audit_admitted_context_items" for k in n.keywords):
                        callers.append(rel)
        self.assertEqual(
            sorted(callers), [_APPROVED_BRIDGE],
            msg=f"only the approved bridge may pass audit items into run_turn; got: {sorted(callers)}")

    def test_app_does_not_import_or_call_agent_runner(self):
        tree = _parse_service("app.py")
        idents = _idents(tree)
        self.assertNotIn("AgentRunner", idents)
        self.assertNotIn("run_turn", idents)
        self.assertNotIn("audit_admitted_context_items", idents)

    def test_no_assembledcontext_into_runner(self):
        leaves = set()
        names = set()
        tree = _parse_service("agent_loop.py")
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                leaves.add(n.module.split(".")[-1])
                for x in n.names:
                    names.add(x.name)
            elif isinstance(n, ast.Import):
                for x in n.names:
                    leaves.add(x.name.split(".")[-1])
        self.assertNotIn("retrieval_assembler", leaves)
        self.assertNotIn("AssembledContext", names)
        self.assertNotIn("AssembledContext", _idents(tree))

    def test_no_provenance_or_verification_flag_in_production(self):
        hits = []
        for rel, raw, tree in self._trees():
            text = raw.decode("utf-8", "replace")
            for flag in _PROVENANCE_FLAGS:
                if flag in text:
                    hits.append((rel, flag))
        self.assertEqual(hits, [], msg=f"provenance/verification flag in production: {hits}")


if __name__ == "__main__":
    unittest.main()
