"""Tests-only / source-only: PRE-WIRING CONTRACT GUARD for the named private-owner
handoff boundary (`AgentRunner._execute` -> `self.llm_client.complete(...)`).

This is a forward CONTRACT guard, not a re-characterization. The descriptive facts
of the boundary are already locked by
`tests/test_audit_private_owner_handoff_boundary_characterization.py` (`83567a3`)
and the topology by `tests/test_audit_live_owner_candidate_inventory.py` — this file
does NOT duplicate them. It states the small set of invariants that must REMAIN TRUE
**before and through** any later behavior-preserving refactor or wiring slice: a
future change that violates any clause here trips this guard.

It selects no implementation path and authorizes no wiring. Passing it authorizes NO
production behavior change, NO wiring of `PrivateGenerationOwner`, NO prompt mutation,
NO memory write, NO admission mechanics, NO output control, and NO audit-as-control.
Any future wiring is gated by W-1..W-8 of
`docs/TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md` under separate
Hilmir authorization + Codex review.

Source nuance locked deliberately: the packet-composition `if` in `run_turn`
legitimately keys on INPUT availability (`audit_admitted_context_items is not None`,
`_prompt_request is not None`) to decide *whether to build* a packet. The contract is
therefore that the BUILT packet VALUE (`_audit_evidence_packet`) drives no behavior —
not that no branch may mention audit inputs.

Method: pure `ast`/source parsing. Imports NO `torment_service` module and executes
NO service runtime. If a clause fails, do NOT patch production — return it as a gate
decision.
"""

import ast
import os
import unittest


_AGENT_LOOP = "agent_loop.py"
_OWNER = "audit_private_generation_owner.py"
_BOUNDARY_METHOD = "_execute"
_PROMPT_BUILDER = "_build_llm_prompt_request"
_HELPER = "_complete_llm_prompt_request"      # the thin model-call helper (post-extraction)
_AUDIT_HELPER = "_observe_audit_evidence_from_prompt_request"   # the audit-evidence helper (post-extraction)
_BUILT_PACKET = "_audit_evidence_packet"      # the BUILT packet value (not inputs)
_OBSERVER = "observe_prompt_inclusion_packet"
_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}

_WRITER_NAMES = frozenset({
    "spawn_memory", "add_memory", "update_payload", "flush_node", "ingest",
    "promote_chunk", "reinforce", "write_environment",
})
_RETRIEVAL_NAMES = frozenset({"assemble_context", "selected_admitted_items"})
_FORBIDDEN_IMPORT_LEAVES = frozenset({
    "retrieval_assembler", "candidate_types", "sqlite3", "sqlalchemy",
})
_FORBIDDEN_IMPORT_NAMES = frozenset({
    "CandidateShapedValue", "candidate_types", "AssembledContext",
})


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


def _attr_calls(node, attr):
    return [n for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == attr]


def _funcs_with_attr_call(tree, attr):
    return {fn.name for fn in _all_functions(tree) if _attr_calls(fn, attr)}


def _funcs_calling(tree, name):
    return {fn.name for fn in _all_functions(tree) if name in _called_names(fn)}


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


def _module_branch_uses(tree, var):
    """Lines where `var` (a Name) appears in an If/While/IfExp TEST anywhere."""
    uses = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.If, ast.While, ast.IfExp)):
            for sub in ast.walk(n.test):
                if isinstance(sub, ast.Name) and sub.id == var:
                    uses.append(getattr(n, "lineno", -1))
    return uses


def _module_call_receivers(tree, var):
    """Callee leaf-names of every Call that receives `var` (a Name) as arg/kw."""
    receivers = set()
    for n in ast.walk(tree):
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
# PW-1  Sole boundary remains named and singular
# --------------------------------------------------------------------------- #

class TestPW1SoleBoundaryRemains(unittest.TestCase):

    def test_complete_confined_to_completion_helper(self):
        # Post-extraction: the model call lives in the single thin helper, which is
        # invoked only by the _execute boundary (still a singular generation call).
        al = _parse_service(_AGENT_LOOP)
        self.assertEqual(
            _funcs_with_attr_call(al, "complete"), {_HELPER},
            msg="the model call is not confined to the single completion helper")
        self.assertEqual(
            _funcs_calling(al, _HELPER), {_BOUNDARY_METHOD},
            msg="the completion helper is called by something other than _execute")
        execute = _method(_class(al, "AgentRunner"), _BOUNDARY_METHOD)
        self.assertIsNotNone(execute, "AgentRunner._execute removed/renamed")
        ecalls = _called_names(execute)
        self.assertIn(_PROMPT_BUILDER, ecalls,
                      "the boundary no longer builds its prompt via _build_llm_prompt_request")
        self.assertIn(_HELPER, ecalls,
                      "the boundary no longer reaches the completion helper")

    def test_completion_helper_does_only_the_model_call(self):
        # The thin helper does NOTHING except the model call (no audit / owner /
        # review / writer / retrieval / branch).
        helper = _method(_class(_parse_service(_AGENT_LOOP), "AgentRunner"), _HELPER)
        self.assertIsNotNone(helper, "completion helper not found")
        self.assertEqual(_called_names(helper), {"complete"},
                         msg="completion helper does more than the model call")


# --------------------------------------------------------------------------- #
# PW-2  Owner remains unwired (production never calls PrivateGenerationOwner)
# --------------------------------------------------------------------------- #

class TestPW2OwnerUnwired(unittest.TestCase):

    def test_no_production_import_or_construction_of_owner(self):
        offenders = []
        for base, tree in _iter_service():
            if base == _OWNER:
                continue
            leaves, names = _import_leaves_names(tree)
            if ("audit_private_generation_owner" in leaves
                    or "PrivateGenerationOwner" in names
                    or "PrivateGenerationOwnerResult" in names):
                offenders.append(base)
            # construction (PrivateGenerationOwner(...)) anywhere in production
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        and n.func.id == "PrivateGenerationOwner"):
                    offenders.append(f"{base}::construct")
        self.assertEqual(offenders, [], msg=f"owner wired/constructed in: {offenders}")


# --------------------------------------------------------------------------- #
# PW-3  No prompt-surface mutation is bundled into the handoff site
# --------------------------------------------------------------------------- #

class TestPW3NoPromptMutationBundledIntoBoundary(unittest.TestCase):

    def test_execute_builds_no_inline_prompt_surface(self):
        # The boundary `_execute` must obtain its prompt ONLY via the named builder;
        # it must not inline-construct a model-visible message/prompt surface (that
        # would bundle prompt mutation into the future handoff site).
        execute = _method(_class(_parse_service(_AGENT_LOOP), "AgentRunner"), _BOUNDARY_METHOD)
        for n in ast.walk(execute):
            if isinstance(n, ast.Dict):
                keys = {k.value for k in n.keys if isinstance(k, ast.Constant)}
                self.assertNotIn("role", keys, "_execute inline-constructs a prompt message dict")
                self.assertNotIn("content", keys, "_execute inline-constructs a prompt message dict")
            if isinstance(n, ast.Constant) and n.value == "user":
                self.fail("_execute inline-references a 'user' prompt role")


# --------------------------------------------------------------------------- #
# PW-4  The BUILT audit packet value drives no behaviour (module-wide)
# --------------------------------------------------------------------------- #

class TestPW4BuiltPacketDrivesNothing(unittest.TestCase):

    def test_built_packet_drives_no_branch_anywhere(self):
        al = _parse_service(_AGENT_LOOP)
        self.assertEqual(
            _module_branch_uses(al, _BUILT_PACKET), [],
            msg="the built audit packet drives a control branch in agent_loop")

    def test_built_packet_routes_only_to_turnresult(self):
        al = _parse_service(_AGENT_LOOP)
        receivers = _module_call_receivers(al, _BUILT_PACKET)
        self.assertTrue(receivers <= {"TurnResult"},
                        msg=f"built audit packet routed beyond TurnResult: {sorted(receivers)}")


# --------------------------------------------------------------------------- #
# PW-5  Packet absence is non-punitive
# --------------------------------------------------------------------------- #

class TestPW5PacketAbsenceNonPunitive(unittest.TestCase):

    def test_no_punitive_branch_on_packet_presence(self):
        # Since the built packet value drives NO branch at all (PW-4), its absence
        # (None) can trigger nothing — non-punitive by construction. Lock that the
        # packet name never appears in an If/While test guarding any divergent path.
        al = _parse_service(_AGENT_LOOP)
        self.assertEqual(_module_branch_uses(al, _BUILT_PACKET), [],
                         msg="packet presence/absence guards a divergent path (punitive)")
        # The observation is fail-soft: the observer call sits under a try/except in
        # the audit-evidence helper (composition extracted from run_turn), so an
        # observer error yields no packet and no error path.
        helper = _method(_class(al, "AgentRunner"), _AUDIT_HELPER)
        self.assertIsNotNone(helper, "audit-evidence helper not found")
        observed_under_try = any(
            isinstance(n, ast.Try) and _OBSERVER in _called_names(n)
            for n in ast.walk(helper))
        self.assertTrue(observed_under_try,
                        "audit observation is not fail-soft (not under try/except)")


# --------------------------------------------------------------------------- #
# PW-6  No writer / memory / retrieval / Gate A / Gate D / DB reachability
# --------------------------------------------------------------------------- #

class TestPW6NoForbiddenReachability(unittest.TestCase):

    def test_boundary_module_and_owner_import_nothing_forbidden(self):
        for mod in (_AGENT_LOOP, _OWNER):
            leaves, names = _import_leaves_names(_parse_service(mod))
            bad_leaves = leaves & _FORBIDDEN_IMPORT_LEAVES
            bad_names = names & _FORBIDDEN_IMPORT_NAMES
            self.assertEqual(bad_leaves, set(), msg=f"{mod} imports {sorted(bad_leaves)}")
            self.assertEqual(bad_names, set(), msg=f"{mod} imports {sorted(bad_names)}")

    def test_execute_reaches_no_writer_or_retrieval(self):
        execute = _method(_class(_parse_service(_AGENT_LOOP), "AgentRunner"), _BOUNDARY_METHOD)
        called = _called_names(execute)
        self.assertEqual(called & _WRITER_NAMES, set(),
                         msg=f"_execute reaches writer(s): {sorted(called & _WRITER_NAMES)}")
        self.assertEqual(called & _RETRIEVAL_NAMES, set(),
                         msg=f"_execute reaches retrieval: {sorted(called & _RETRIEVAL_NAMES)}")

    def test_no_gate_d_entrypoint_in_boundary_module(self):
        al = _parse_service(_AGENT_LOOP)
        for fn in _all_functions(al):
            low = fn.name.lower()
            for tok in ("chamber", "dream", "private_cognition", "incubation"):
                self.assertNotIn(tok, low, f"agent_loop defines a {tok} entrypoint")


# --------------------------------------------------------------------------- #
# PW-7  Integration shape: evidence is observed AROUND generation, never inside it
# --------------------------------------------------------------------------- #

class TestPW7ObservationAroundNotControlOfGeneration(unittest.TestCase):

    def test_observer_runs_in_audit_helper_only_never_in_the_generation_method(self):
        al = _parse_service(_AGENT_LOOP)
        # The evidence observer is composed ONLY in the audit-evidence helper
        # (downstream, called by run_turn), and NEVER inside _execute (the
        # generation control flow). Evidence sits AROUND generation, not in it.
        self.assertEqual(_funcs_calling(al, _OBSERVER), {_AUDIT_HELPER},
                         msg="audit observation is not confined to the audit-evidence helper")
        self.assertEqual(_funcs_calling(al, _AUDIT_HELPER), {"run_turn"},
                         msg="the audit-evidence helper is called by something other than run_turn")
        execute = _method(_class(al, "AgentRunner"), _BOUNDARY_METHOD)
        self.assertNotIn(_OBSERVER, _called_names(execute),
                         msg="generation method composes audit evidence (control-of-generation risk)")
        self.assertNotIn(_AUDIT_HELPER, _called_names(execute),
                         msg="generation method composes audit evidence via the helper")

    def test_observer_composes_from_final_response(self):
        # The packet is composed only after a final response exists (downstream of
        # generation): the observer call (now in the audit-evidence helper) passes a
        # response_text-derived argument.
        helper = _method(_class(_parse_service(_AGENT_LOOP), "AgentRunner"), _AUDIT_HELPER)
        self.assertIsNotNone(helper, "audit-evidence helper not found")
        name_calls = [n for n in ast.walk(helper)
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                      and n.func.id == _OBSERVER]
        self.assertTrue(name_calls, "observer not called in the audit-evidence helper")
        kw_names = set()
        for c in name_calls:
            kw_names |= {k.arg for k in c.keywords}
        self.assertIn("response_text", kw_names,
                      "observer is not fed the final response_text (not downstream of generation)")


# --------------------------------------------------------------------------- #
# PW-8  This guard binds future change; ties to the decision frame
# --------------------------------------------------------------------------- #

class TestPW8GuardBindsFutureChange(unittest.TestCase):

    def test_named_boundary_still_present(self):
        # If a future refactor removes/renames the named boundary or its builder,
        # this trips — forcing the change through the gate.
        runner = _class(_parse_service(_AGENT_LOOP), "AgentRunner")
        self.assertIsNotNone(_method(runner, _BOUNDARY_METHOD), "boundary method gone")
        self.assertIsNotNone(_method(runner, _PROMPT_BUILDER), "prompt builder gone")
        self.assertIsNotNone(_method(runner, _HELPER), "completion helper gone")

    def test_decision_frame_gates_any_wiring(self):
        path = os.path.join(_repo_root(), "docs",
                            "TORMENT_AUDIT_PRIVATE_OWNER_LIVE_WIRING_DECISION_FRAME_v0.1.md")
        with open(path, "r", encoding="utf-8") as fh:
            doc = fh.read().lower()
        self.assertIn("admissible-for-future-guarded-wiring", doc)
        self.assertIn("w-1", doc)


if __name__ == "__main__":
    unittest.main()
