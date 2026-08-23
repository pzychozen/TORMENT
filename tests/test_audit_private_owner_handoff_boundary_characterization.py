"""Tests-only / source-only: the single candidate internal generation-call boundary
that could later serve as the future handoff point to `PrivateGenerationOwner`.

This characterization selects no implementation path and authorizes no wiring. It
proves current source facts only; passing it authorizes NO production behavior
change, NO wiring of `PrivateGenerationOwner`, NO prompt mutation, NO memory write,
NO admission mechanics, and NO runtime control. Any future connection is gated by
W-1..W-8 of
`docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md`
under separate Hilmir authorization + Codex review.

Question answered (current facts only):
  Is there exactly ONE admissible internal generation-call boundary in
  `torment_service/agent_loop.py` that could later serve as the future handoff
  point to `PrivateGenerationOwner`, while preserving W-1..W-8?

Named boundary (if source confirms): `AgentRunner._execute`'s
`self.llm_client.complete(...)` model call, fed by `self._build_llm_prompt_request`
(captured deterministically by `_execute_with_prompt_request`). The audit packet
itself lives downstream in `run_turn`, composed AFTER execution, fail-soft, and
returned only on `TurnResult`.

This is NOT another topology inventory (that already exists, green:
`tests/test_audit_live_owner_candidate_inventory.py` +
`tests/test_audit_live_owner_path_selection_characterization.py`). It narrows to the
single generation-call boundary and its W-property facts.

Method: pure `ast`/source parsing. Imports NO `torment_service` module and executes
NO service runtime. If any guard fails, do NOT patch production — return it as a
gate decision.
"""

import ast
import os
import unittest


_AGENT_LOOP = "agent_loop.py"
_OWNER = "audit_private_generation_owner.py"
_DECISION_DOC = "TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md"
_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}

# Generation-call boundary tokens.
_COMPLETE = "complete"
_PROMPT_BUILDER = "_build_llm_prompt_request"
_BOUNDARY_METHOD = "_execute"
_HELPER = "_complete_llm_prompt_request"       # the thin model-call helper (post-extraction)

# Reaches the generation boundary must NOT take (would break the W-properties).
_WRITER_NAMES = frozenset({
    "spawn_memory", "add_memory", "update_payload", "flush_node", "ingest",
    "promote_chunk", "reinforce", "write_environment",
})
_RETRIEVAL_NAMES = frozenset({"assemble_context", "selected_admitted_items"})
_CONTROL_NAMES = frozenset({
    "review", "rerank", "rank", "retry", "suppress", "suppression", "style",
})
_AUDIT_NAMES = frozenset({
    "audit_evidence_packet", "_audit_evidence_packet",
    "observe_prompt_inclusion_packet", "audit_admitted_context_items",
    "selected_admitted_items", "PrivateGenerationOwner", "audit_evidence_context",
})
_GATE_A_GATE_D_NAMES = frozenset({
    "CandidateShapedValue", "candidate_types", "AssembledContext",
})


# --------------------------------------------------------------------------- #
# AST / source helpers (no service import)
# --------------------------------------------------------------------------- #

def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _docs_dir():
    return os.path.join(_repo_root(), "docs")


def _parse_service(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _read_doc(name):
    with open(os.path.join(_docs_dir(), name), "r", encoding="utf-8") as fh:
        return fh.read()


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


def _all_functions(tree):
    return [n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


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


def _attr_calls(node, attr):
    return [n for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == attr]


def _funcs_with_attr_call(tree, attr):
    out = set()
    for fn in _all_functions(tree):
        if _attr_calls(fn, attr):
            out.add(fn.name)
    return out


def _kw(call, name):
    for k in call.keywords:
        if k.arg == name:
            return k.value
    return None


def _branch_uses(func, var):
    uses = []
    for n in ast.walk(func):
        if isinstance(n, (ast.If, ast.While, ast.IfExp)):
            for sub in ast.walk(n.test):
                if isinstance(sub, ast.Name) and sub.id == var:
                    uses.append(getattr(n, "lineno", -1))
    return uses


def _call_receivers(func, var):
    receivers = set()
    for n in ast.walk(func):
        if isinstance(n, ast.Call):
            passed = [a.id for a in n.args if isinstance(a, ast.Name)]
            passed += [k.value.id for k in n.keywords if isinstance(k.value, ast.Name)]
            if var in passed:
                f = n.func
                receivers.add(f.id if isinstance(f, ast.Name)
                              else f.attr if isinstance(f, ast.Attribute) else "?")
    return receivers


def _iter_service():
    for dp, dns, fns in os.walk(_service_dir()):
        dns[:] = [d for d in dns if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
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
# 1. Exactly one generation-call boundary, and it is AgentRunner._execute
# --------------------------------------------------------------------------- #

class TestExactlyOneBoundary(unittest.TestCase):

    def setUp(self):
        self.al = _parse_service(_AGENT_LOOP)

    def test_complete_is_confined_to_the_single_completion_helper(self):
        # Post-extraction: the model-completion call (`.complete(...)`) appears in
        # exactly one method — the thin `_complete_llm_prompt_request` helper — so
        # the generation-call boundary stays singular.
        self.assertEqual(
            _funcs_with_attr_call(self.al, _COMPLETE), {_HELPER},
            msg="`.complete(...)` is not confined to the single completion helper")

    def test_execute_builds_prompt_then_reaches_completion_helper(self):
        runner = _class(self.al, "AgentRunner")
        execute = _method(runner, _BOUNDARY_METHOD)
        self.assertIsNotNone(execute, "AgentRunner._execute not found")
        called = _called_names(execute)
        self.assertIn(_PROMPT_BUILDER, called,
                      "_execute does not build the prompt request")
        self.assertIn(_HELPER, called, "_execute does not reach the completion helper")
        # The model call (now in the helper) consumes the built request `req`
        # fields — prompt prepared BEFORE the model call.
        helper = _method(runner, _HELPER)
        self.assertIsNotNone(helper, "completion helper not found")
        for call in _attr_calls(helper, _COMPLETE):
            for kw in ("system_prompt", "messages"):
                val = _kw(call, kw)
                self.assertIsNotNone(val, f"complete() missing {kw}")
                names = {n.id for n in ast.walk(val) if isinstance(n, ast.Name)}
                self.assertIn("req", names,
                              msg=f"complete()'s {kw} is not fed from the built prompt request")


# --------------------------------------------------------------------------- #
# 2. The boundary is in agent_loop.py — not app/endpoint/DB/retrieval/GateA/GateD/writer
# --------------------------------------------------------------------------- #

class TestBoundaryLocationAndExclusions(unittest.TestCase):

    def test_boundary_lives_in_agent_loop_not_app(self):
        al = _parse_service(_AGENT_LOOP)
        self.assertIn(_BOUNDARY_METHOD, {f.name for f in _all_functions(al)})
        self.assertIn(_PROMPT_BUILDER, {f.name for f in _all_functions(al)})
        app = _parse_service("app.py")
        leaves, names = _import_leaves_names(app)
        self.assertNotIn("agent_loop", leaves, "app.py imports agent_loop")
        self.assertNotIn("AgentRunner", names, "app.py imports AgentRunner")
        app_ids = _idents(app)
        self.assertNotIn(_BOUNDARY_METHOD, app_ids, "app.py references _execute")
        self.assertNotIn(_PROMPT_BUILDER, app_ids, "app.py references the prompt builder")
        # The model call is not owned by an endpoint.
        self.assertEqual(_funcs_with_attr_call(app, _COMPLETE), set(),
                         msg="app.py owns a model-completion call")

    def test_boundary_module_excludes_db_retrieval_gatea_gated(self):
        al = _parse_service(_AGENT_LOOP)
        leaves, names = _import_leaves_names(al)
        for forbidden in ("retrieval_assembler", "candidate_types",
                          "sqlite3", "sqlalchemy"):
            self.assertNotIn(forbidden, leaves, f"agent_loop imports {forbidden}")
        for forbidden in _GATE_A_GATE_D_NAMES:
            self.assertNotIn(forbidden, names, f"agent_loop imports {forbidden}")
        # No Gate D chamber/dream/private-cognition entrypoint in the boundary module.
        for fn in _all_functions(al):
            low = fn.name.lower()
            for tok in ("chamber", "dream", "private_cognition", "incubation"):
                self.assertNotIn(tok, low, f"agent_loop defines a {tok} entrypoint")

    def test_execute_reaches_no_writer_or_retrieval_path(self):
        execute = _method(_class(_parse_service(_AGENT_LOOP), "AgentRunner"), _BOUNDARY_METHOD)
        called = _called_names(execute)
        self.assertEqual(called & _WRITER_NAMES, set(),
                         msg=f"_execute reaches a writer path: {sorted(called & _WRITER_NAMES)}")
        self.assertEqual(called & _RETRIEVAL_NAMES, set(),
                         msg=f"_execute reaches a retrieval path: {sorted(called & _RETRIEVAL_NAMES)}")


# --------------------------------------------------------------------------- #
# 3. The boundary is not inside selection/ranking/retry/suppression/style/review/memory-write
# --------------------------------------------------------------------------- #

class TestBoundaryNotInControlLogic(unittest.TestCase):

    def test_execute_calls_no_review_ranking_retry_suppression_style(self):
        execute = _method(_class(_parse_service(_AGENT_LOOP), "AgentRunner"), _BOUNDARY_METHOD)
        called = _called_names(execute)
        bad = called & _CONTROL_NAMES
        self.assertEqual(bad, set(),
                         msg=f"_execute sits inside control logic: {sorted(bad)}")


# --------------------------------------------------------------------------- #
# 4. The boundary is audit-blind; the downstream packet drives no control
# --------------------------------------------------------------------------- #

class TestAuditBlindBoundaryAndEvidenceOnlyPacket(unittest.TestCase):

    def setUp(self):
        self.al = _parse_service(_AGENT_LOOP)
        self.runner = _class(self.al, "AgentRunner")

    def test_execute_is_audit_blind(self):
        # The generation boundary references no audit packet / observer / owner —
        # so an audit packet cannot drive any branch FROM the boundary.
        execute = _method(self.runner, _BOUNDARY_METHOD)
        ids = _idents(execute)
        leak = ids & _AUDIT_NAMES
        self.assertEqual(leak, set(),
                         msg=f"_execute references audit machinery: {sorted(leak)}")

    def test_run_turn_packet_is_evidence_only_not_control(self):
        # Any future connection routes audit evidence the way run_turn already
        # does: composed AFTER execution by the audit-evidence helper, driving no
        # branch, returned only on TurnResult — observation-only, never control.
        run_turn = _method(self.runner, "run_turn")
        self.assertIsNotNone(run_turn)
        self.assertIn("_observe_audit_evidence_from_prompt_request", _called_names(run_turn))
        helper = _method(self.runner, "_observe_audit_evidence_from_prompt_request")
        self.assertIsNotNone(helper, "audit-evidence helper not found")
        self.assertIn("observe_prompt_inclusion_packet", _called_names(helper))
        self.assertEqual(_branch_uses(run_turn, "_audit_evidence_packet"), [],
                         msg="audit packet drives a control branch in run_turn")
        receivers = _call_receivers(run_turn, "_audit_evidence_packet")
        self.assertLessEqual(receivers, {"TurnResult"},
                        msg=f"audit packet routed beyond TurnResult: {sorted(receivers)}")


# --------------------------------------------------------------------------- #
# 5. Owner stays unwired; prompt surface pinned (no prompt mutation)
# --------------------------------------------------------------------------- #

class TestOwnerUnwiredAndPromptSurfacePinned(unittest.TestCase):

    def test_owner_remains_unwired(self):
        importers = []
        for base, tree in _iter_service():
            if base == _OWNER:
                continue
            leaves, names = _import_leaves_names(tree)
            if ("audit_private_generation_owner" in leaves
                    or "PrivateGenerationOwner" in names
                    or "PrivateGenerationOwnerResult" in names):
                importers.append(base)
        self.assertEqual(importers, [], msg=f"owner wired into: {importers}")

    def test_prompt_surface_is_pinned_unchanged(self):
        # Pin the CURRENT model-visible prompt surface so any future change must be
        # explicit (W-6). messages == [{"role": "user", "content": frame.raw_input}];
        # system prompt is the minimal builder. This test mutates nothing.
        runner = _class(_parse_service(_AGENT_LOOP), "AgentRunner")
        builder = _method(runner, _PROMPT_BUILDER)
        self.assertIsNotNone(builder, "_build_llm_prompt_request not found")
        dict_keys = set()
        has_user = has_raw_input = False
        for n in ast.walk(builder):
            if isinstance(n, ast.Dict):
                dict_keys = {k.value for k in n.keys if isinstance(k, ast.Constant)}
            if isinstance(n, ast.Constant) and n.value == "user":
                has_user = True
            if isinstance(n, ast.Attribute) and n.attr == "raw_input":
                has_raw_input = True
        self.assertEqual(dict_keys, {"role", "content"},
                         msg=f"prompt messages dict shape changed: {sorted(dict_keys)}")
        self.assertTrue(has_user, "prompt messages no longer role 'user'")
        self.assertTrue(has_raw_input, "prompt content no longer frame.raw_input")
        sysp = _method(runner, "_build_system_prompt")
        self.assertIsNotNone(sysp, "_build_system_prompt not found")
        self.assertTrue(any(isinstance(n, ast.JoinedStr) for n in ast.walk(sysp)),
                        "system prompt is no longer the minimal f-string builder")


# --------------------------------------------------------------------------- #
# 6. Framing — ties to the decision frame; authorizes no production change
# --------------------------------------------------------------------------- #

class TestFraming(unittest.TestCase):

    def test_decision_frame_admits_only_guarded_wiring(self):
        doc = _read_doc(_DECISION_DOC).lower()
        self.assertIn("admissible-for-future-guarded-wiring", doc)
        self.assertIn("w-1", doc)
        self.assertIn("privategenerationowner", doc)


if __name__ == "__main__":
    unittest.main()
