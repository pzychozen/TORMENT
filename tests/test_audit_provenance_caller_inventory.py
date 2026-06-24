"""Tests-only / source-only inventory: honest caller paths for
``audit_admitted_context_items``.

``TurnResult.audit_evidence_packet`` is an observation-only sink built from the
final reviewed ``response_text`` + caller-supplied ``audit_admitted_context_items``.
AgentRunner does NOT prove same-turn provenance. The open risk is *provenance
inflation*: implying the caller-supplied items are same-turn admitted context
without proving which caller owns that claim.

This file changes NO production code, adds NO schema field, adds NO provenance /
verification flag, and wires NOTHING. It only inventories — via AST / source
inspection — who currently calls ``AgentRunner.run_turn`` and whether any honest
live (endpoint / production-service) path supplies ``audit_admitted_context_items``
today.

Outcome it informs (decision belongs to Codex/operator): A) narrow internal
runner-owner contract, B) caller-supplied external orchestration contract,
C) actual wiring, or D) stop/branch because no honest live caller path exists yet.
"""

import ast
import os
import unittest
from functools import lru_cache


_PROVENANCE_FLAGS = (
    "same_turn_verified", "verified_same_turn", "provenance_verified",
    "truth_verified", "authority_verified", "same_turn_provenance",
)
_GENERATION_CALLS = {
    "complete", "completion", "completions", "chat", "chat_completion",
    "create_completion", "create_chat_completion", "generate", "predict", "infer",
}
_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}


def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.dirname(here)                                  # torment_fabric/


def _rel(path):
    return os.path.relpath(path, _repo_root()).replace("\\", "/")


def _parse_bytes(raw):
    # Null-strip defends against a mount-corruption artifact in some sandboxes;
    # the authoritative repo parses cleanly either way.
    return ast.parse(raw.replace(b"\x00", b""))


# The single approved private bridge authorized to supply
# ``audit_admitted_context_items`` into ``run_turn`` (observation-only). It is a
# sanctioned exception to the prior "no honest live caller" topology and gets its
# own category so the live/endpoint/runner-owner negatives stay intact.
_APPROVED_BRIDGE_REL = "torment_service/audit_selected_items_runner_bridge.py"


def _category(rel):
    if rel == _APPROVED_BRIDGE_REL:
        return "approved_bridge"
    if rel == "torment_service/app.py":
        return "endpoint"
    if rel == "torment_service/agent_loop.py":
        return "runner_owner"
    if rel.startswith("torment_service/"):
        return "production_service"
    if rel.startswith("tests/"):
        return "test"
    return "example_or_script"


def _is_run_turn_call(node):
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    return ((isinstance(f, ast.Name) and f.id == "run_turn")
            or (isinstance(f, ast.Attribute) and f.attr == "run_turn"))


@lru_cache(maxsize=1)
def _scan():
    root = _repo_root()
    run_turn_callers = {}            # rel -> list[ast.Call]
    audit_kw_callers = set()         # rel where a run_turn call passes the kw
    assembled_into_runturn = set()   # rel where a run_turn call passes AssembledContext
    flag_hits = set()                # (rel, flag) in torment_service source only
    parsed = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = _rel(path)
            try:
                with open(path, "rb") as fh:
                    raw = fh.read()
            except OSError:
                continue
            # Provenance-flag scan: torment_service source only (avoid matching
            # this inventory file's own assertion strings).
            if rel.startswith("torment_service/"):
                text = raw.decode("utf-8", "replace")
                for flag in _PROVENANCE_FLAGS:
                    if flag in text:
                        flag_hits.add((rel, flag))
            try:
                tree = _parse_bytes(raw)
            except (SyntaxError, ValueError):
                continue
            parsed.add(rel)
            calls = [n for n in ast.walk(tree) if _is_run_turn_call(n)]
            if not calls:
                continue
            run_turn_callers[rel] = calls
            for c in calls:
                if any(kw.arg == "audit_admitted_context_items" for kw in c.keywords):
                    audit_kw_callers.add(rel)
                values = list(c.args) + [kw.value for kw in c.keywords]
                for v in values:
                    if isinstance(v, ast.Name) and v.id == "AssembledContext":
                        assembled_into_runturn.add(rel)
    return {
        "run_turn_callers": run_turn_callers,
        "audit_kw_callers": audit_kw_callers,
        "assembled_into_runturn": assembled_into_runturn,
        "flag_hits": flag_hits,
        "parsed": parsed,
    }


def _torment_service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _parse_service(filename):
    with open(os.path.join(_torment_service_dir(), filename), "rb") as fh:
        return _parse_bytes(fh.read())


def _func(tree, name):
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


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


def _import_leaves(tree):
    leaves = set()
    names = set()
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


def _calls_method_on(node, obj, method):
    for n in ast.walk(node):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == method and isinstance(n.func.value, ast.Name)
                and n.func.value.id == obj):
            return True
    return False


class TestSanity(unittest.TestCase):
    def test_key_production_files_parsed(self):
        parsed = _scan()["parsed"]
        # Guards against vacuous negatives from a parse skip.
        self.assertIn("torment_service/app.py", parsed)
        self.assertIn("torment_service/agent_loop.py", parsed)


class TestEndpointSurfaces(unittest.TestCase):

    def test_app_does_not_import_or_call_agent_runner(self):
        tree = _parse_service("app.py")
        leaves, names = _import_leaves(tree)
        self.assertNotIn("agent_loop", leaves, "app.py imports agent_loop")
        self.assertNotIn("AgentRunner", names, "app.py imports AgentRunner")
        self.assertNotIn("app.py", _scan()["run_turn_callers"],
                         "app.py calls run_turn")
        self.assertNotIn("audit_admitted_context_items", _idents(tree),
                         "app.py references audit_admitted_context_items")

    def test_retrieve_has_context_but_no_generation_or_runner(self):
        fn = _func(_parse_service("app.py"), "retrieve_assembled")
        self.assertIsNotNone(fn)
        idents = _idents(fn)
        self.assertIn("assemble_context", idents)
        self.assertTrue(_calls_method_on(fn, "assembled", "to_dict"))
        self.assertNotIn("response_text", idents)
        self.assertEqual(idents & _GENERATION_CALLS, set())
        self.assertNotIn("run_turn", idents)
        self.assertNotIn("AgentRunner", idents)

    def test_agent_query_returns_fabric_query_not_generation(self):
        fn = _func(_parse_service("app.py"), "query")
        self.assertIsNotNone(fn)
        idents = _idents(fn)
        self.assertTrue(_calls_method_on(fn, "fabric", "query"))
        self.assertNotIn("response_text", idents)
        self.assertEqual(idents & _GENERATION_CALLS, set())


class TestRunnerAcceptsItemsWithoutProvenance(unittest.TestCase):

    def test_run_turn_accepts_items_but_verifies_no_provenance(self):
        cls = _class(_parse_service("agent_loop.py"), "AgentRunner")
        run_turn = _method(cls, "run_turn")
        self.assertIsNotNone(run_turn)
        kwonly = {a.arg for a in run_turn.args.kwonlyargs}
        self.assertIn("audit_admitted_context_items", kwonly)
        idents = _idents(run_turn)
        for flag in _PROVENANCE_FLAGS:
            self.assertNotIn(flag, idents,
                             msg=f"run_turn references provenance flag: {flag}")


class TestNoHonestLiveCallerSuppliesItems(unittest.TestCase):

    def test_no_production_or_endpoint_caller_passes_audit_items(self):
        scan = _scan()
        offenders = {rel for rel in scan["audit_kw_callers"]
                     if _category(rel) in {"endpoint", "production_service", "runner_owner"}}
        self.assertEqual(
            offenders, set(),
            msg=f"production/endpoint run_turn caller passes audit_admitted_context_items: {sorted(offenders)}",
        )

    def test_audit_items_into_run_turn_only_in_tests_or_approved_bridge(self):
        scan = _scan()
        # Only tests and the single approved private bridge may pass the items.
        other = {rel for rel in scan["audit_kw_callers"]
                 if _category(rel) not in {"test", "approved_bridge"}}
        self.assertEqual(
            other, set(),
            msg=f"unexpected run_turn caller passes audit_admitted_context_items: {sorted(other)}",
        )
        # Lock the exception narrowly: the approved-bridge category resolves to
        # exactly the one approved bridge file.
        approved = {rel for rel in scan["audit_kw_callers"]
                    if _category(rel) == "approved_bridge"}
        self.assertEqual(
            approved, {_APPROVED_BRIDGE_REL},
            msg=f"approved-bridge caller set must be exactly the bridge; got: {sorted(approved)}",
        )

    def test_no_production_passes_assembledcontext_into_runner(self):
        scan = _scan()
        non_test = {rel for rel in scan["assembled_into_runturn"] if _category(rel) != "test"}
        self.assertEqual(non_test, set(),
                         msg=f"non-test run_turn caller passes AssembledContext: {sorted(non_test)}")
        # The runner module itself imports/references no AssembledContext.
        leaves, names = _import_leaves(_parse_service("agent_loop.py"))
        self.assertNotIn("AssembledContext", names)
        self.assertNotIn("retrieval_assembler", leaves)


class TestRunTurnCallerInventory(unittest.TestCase):
    """Enumerate + classify every run_turn caller. Encodes the conclusion: the
    only callers are the runner-owner self-call, the demo/example, and tests —
    there is NO honest live (endpoint / production-service) caller path today."""

    def test_classify_run_turn_callers(self):
        scan = _scan()
        by_cat = {}
        for rel in scan["run_turn_callers"]:
            by_cat.setdefault(_category(rel), set()).add(rel)

        endpoint = by_cat.get("endpoint", set())
        prod_service = by_cat.get("production_service", set())
        owner = by_cat.get("runner_owner", set())
        examples = by_cat.get("example_or_script", set())
        approved = by_cat.get("approved_bridge", set())

        # No endpoint and no (non-owner) production-service caller exists.
        self.assertEqual(endpoint, set(), f"endpoint calls run_turn: {sorted(endpoint)}")
        self.assertEqual(prod_service, set(),
                         f"production-service module calls run_turn: {sorted(prod_service)}")
        # The runner owns an internal self-call (enter_reflex); demo/example
        # callers may exist. Neither supplies audit items (asserted elsewhere).
        self.assertIn("torment_service/agent_loop.py", owner)
        # The approved private bridge is the one sanctioned run_turn caller that
        # MAY supply audit items; it resolves to exactly the bridge file.
        self.assertEqual(approved, {_APPROVED_BRIDGE_REL},
                         f"approved-bridge run_turn callers: {sorted(approved)}")
        for rel in examples:
            self.assertNotIn(rel, scan["audit_kw_callers"],
                             msg=f"example/demo {rel} passes audit_admitted_context_items")


class TestNoProvenanceFlagExists(unittest.TestCase):

    def test_no_provenance_or_verification_flag_in_production(self):
        hits = _scan()["flag_hits"]
        self.assertEqual(hits, set(),
                         msg=f"provenance/verification flag present in production: {sorted(hits)}")


class TestObservationSinkPreserved(unittest.TestCase):

    def test_turnresult_audit_evidence_packet_is_observation_field(self):
        cls = _class(_parse_service("agent_loop.py"), "TurnResult")
        fld = None
        for n in cls.body:
            if (isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                    and n.target.id == "audit_evidence_packet"):
                fld = n
                break
        self.assertIsNotNone(fld, "TurnResult.audit_evidence_packet field missing")
        self.assertTrue(
            isinstance(fld.value, ast.Constant) and fld.value.value is None,
            "audit_evidence_packet should default to None (observation sink)",
        )


if __name__ == "__main__":
    unittest.main()
