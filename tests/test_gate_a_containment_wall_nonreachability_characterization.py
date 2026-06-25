"""Tests-only / source-only structural non-reachability characterization for the
Gate A / Document A containment wall.

Records the CURRENT resting state: there is no live private-cognition / Document B
chamber, and the existing reflection-adjacent audit lane is observation-only and
unwired, so no contained/chamber artifact can reach live cognition, retrieval,
prompt projection, write, promotion, reinforcement, identity/canon, or AgentRunner
today. This is a resting-state characterization, NOT a permanent ban on a future
*governed* Document B implementation: governed admission (Document A A-O3) remains
the legitimate future crossing.

Grounded in: the Gate A containment-wall enforcement frame and the Document A
contract (A-O2/A-O3/A-C1/A-C2/A-C3); the Document B blueprint (the would-be
inhabitant). All assertions are source/AST over the live service tree — no
production code, no docs, no other tests, no runtime.

Properties locked:
  P1  No live Document B / private-cognition chamber entrypoint exists.
  P2  No live path feeds a chamber/private-cognition artifact into the fan-out
      (no producer exists; the audit-evidence lane reaches none of the sinks).
  P3  app.py and spine.py do not import or instantiate AgentRunner.
  P4  /agent/query is retrieval/advisory only (consumes MemoryPlan lane fields,
      not deliberation outputs).
  P5  The private generation owner remains unwired outside tests.
  P6  The selected-items bridge remains a dead-end outside tests.
  P7  Audit/observation packets remain non-control (drive no branch into prompt /
      output / review / ingest / retrieval / ranking / style / writes / persistence).

Deferred / not asserted satisfied: Gate D runtime, Envelope Audit runtime,
private-owner live wiring, Shape B, endpoint/schema/API, prompt exposure,
AgentRunner ownership expansion, database/substrate, carriers/schema/fields,
writer fixes, P4 O1/O2 mechanics, Seed-Gov mechanics, retrieval feedback,
persistence, autonomy, audit-to-control feedback.
"""

import ast
import os
import unittest


# Chamber / private-cognition / dream runtime entrypoint tokens (def-name match;
# deliberately NOT "reflection" alone — ReflectionTrace observation is allowed).
_CHAMBER_TOKENS = ("chamber", "dream", "incubation", "continued_thought",
                   "private_cognition", "reflection_chamber", "envelope_audit")

# Fan-out write / retrieval / promotion / identity sinks a contained artifact
# must never reach. (run_turn / query included; the audit-evidence lane below
# legitimately calls none of these — the bridge's run_turn use is handled by P6.)
_FANOUT_SINKS = {"ingest", "assemble_context", "promote_chunk",
                 "promote_chunk_endpoint", "reinforce", "gravity_correction",
                 "_maybe_emit_identity_anchor", "query", "run_turn"}

# The reflection-adjacent audit-evidence / observation modules (NOT the bridge).
_AUDIT_LANE_MODULES = (
    "audit_evidence_context.py",
    "audit_evidence_packet.py",
    "audit_evidence_sidecar.py",
    "audit_prompt_inclusion_observation.py",
    "audit_private_generation_owner.py",
)

_OWNER_MODULE = "audit_private_generation_owner.py"
_BRIDGE_MODULE = "audit_selected_items_runner_bridge.py"
_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _docs_dir():
    return os.path.join(_repo_root(), "docs")


def _parse(path):
    with open(path, "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _service_tree(filename):
    return _parse(os.path.join(_service_dir(), filename))


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _iter_service():
    for dp, dns, fns in os.walk(_service_dir()):
        dns[:] = [d for d in dns if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            ab = os.path.join(dp, fn)
            try:
                yield os.path.relpath(ab, _service_dir()).replace("\\", "/"), _parse(ab)
            except (SyntaxError, ValueError):
                continue


def _idents(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


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


def _top_func(tree, name):
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _class(tree, name):
    for n in ast.walk(tree):
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


def _call_receivers(func_node, var_name):
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


def _branch_uses(func_node, var_name):
    uses = []
    for n in ast.walk(func_node):
        if isinstance(n, (ast.If, ast.While, ast.IfExp)):
            for sub in ast.walk(n.test):
                if isinstance(sub, ast.Name) and sub.id == var_name:
                    uses.append(getattr(n, "lineno", -1))
    return uses


# --------------------------------------------------------------------------- #
# P1 — no live private-cognition / chamber entrypoint
# --------------------------------------------------------------------------- #

class TestNoLiveChamberEntrypoint(unittest.TestCase):

    def test_no_chamber_or_dream_definition_in_service(self):
        offenders = []
        for rel, tree in _iter_service():
            for n in ast.walk(tree):
                if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    low = n.name.lower()
                    if any(tok in low for tok in _CHAMBER_TOKENS):
                        offenders.append(f"{rel}::{n.name}")
        self.assertEqual(offenders, [],
                         msg=f"live chamber/private-cognition entrypoint(s): {offenders}")

    def test_no_chamber_or_dream_module_file(self):
        mods = [rel for rel, _ in _iter_service()
                if any(tok in os.path.basename(rel).lower() for tok in _CHAMBER_TOKENS)]
        self.assertEqual(mods, [], msg=f"chamber/dream module file(s): {mods}")


# --------------------------------------------------------------------------- #
# P2 — the reflection-adjacent audit lane reaches no fan-out sink
# --------------------------------------------------------------------------- #

class TestAuditLaneReachesNoFanout(unittest.TestCase):

    def test_audit_lane_modules_call_no_fanout_sink(self):
        offenders = {}
        for mod in _AUDIT_LANE_MODULES:
            called = _called_names(_service_tree(mod))
            hit = called & _FANOUT_SINKS
            if hit:
                offenders[mod] = sorted(hit)
        self.assertEqual(offenders, {},
                         msg=f"audit lane reaches fan-out sink(s): {offenders}")


# --------------------------------------------------------------------------- #
# P3 — app.py and spine.py do not import/instantiate AgentRunner
# --------------------------------------------------------------------------- #

class TestRunnerNotInAppOrSpine(unittest.TestCase):

    def test_app_and_spine_have_no_agent_runner(self):
        for fname in ("app.py", "spine.py"):
            tree = _service_tree(fname)
            leaves, names = _import_leaves_names(tree)
            self.assertNotIn("agent_loop", leaves, f"{fname} imports agent_loop")
            self.assertNotIn("AgentRunner", names, f"{fname} imports AgentRunner")
            ids = _idents(tree)
            self.assertNotIn("AgentRunner", ids, f"{fname} references AgentRunner")
            self.assertNotIn("run_turn", ids, f"{fname} references run_turn")


# --------------------------------------------------------------------------- #
# P4 — /agent/query is retrieval/advisory only
# --------------------------------------------------------------------------- #

class TestAgentQueryAdvisoryOnly(unittest.TestCase):

    def test_query_consumes_memoryplan_not_deliberation(self):
        q = _top_func(_service_tree("app.py"), "query")
        self.assertIsNotNone(q, "/agent/query handler not found")
        ids = _idents(q)
        # consumes MemoryPlan lane fields
        self.assertIn("memory_plan", ids)
        # does not consume deliberation outputs / become a generation owner
        for forbidden in ("response_draft", "review_result", "stance",
                          "run_turn", "complete", "AgentRunner"):
            self.assertNotIn(forbidden, ids,
                             msg=f"/agent/query consumes deliberation output: {forbidden}")


# --------------------------------------------------------------------------- #
# P5 / P6 — owner unwired; bridge dead-end (outside tests)
# --------------------------------------------------------------------------- #

class TestSealedOwnerAndBridgeUnwired(unittest.TestCase):

    def test_private_owner_has_no_service_importer(self):
        importers = []
        for rel, tree in _iter_service():
            if os.path.basename(rel) == _OWNER_MODULE:
                continue
            leaves, names = _import_leaves_names(tree)
            if ("audit_private_generation_owner" in leaves
                    or "PrivateGenerationOwner" in names
                    or "PrivateGenerationOwnerResult" in names):
                importers.append(rel)
        self.assertEqual(importers, [], msg=f"owner wired into: {importers}")

    def test_selected_items_bridge_is_dead_end(self):
        offenders = []
        for rel, tree in _iter_service():
            if os.path.basename(rel) == _BRIDGE_MODULE:
                continue
            leaves, names = _import_leaves_names(tree)
            if ("audit_selected_items_runner_bridge" in leaves
                    or "run_turn_with_selected_items_observation" in names
                    or "run_turn_with_selected_items_observation" in _called_names(tree)):
                offenders.append(rel)
        self.assertEqual(offenders, [], msg=f"bridge wired into: {offenders}")


# --------------------------------------------------------------------------- #
# P7 — audit/observation packets are non-control
# --------------------------------------------------------------------------- #

class TestAuditPacketsNonControl(unittest.TestCase):

    def test_packet_identifier_only_in_runner_sink_and_owner(self):
        refs = set()
        for rel, tree in _iter_service():
            if "audit_evidence_packet" in _idents(tree):
                refs.add(os.path.basename(rel))
        self.assertEqual(refs, {"agent_loop.py", _OWNER_MODULE},
                         msg=f"unexpected audit_evidence_packet references: {sorted(refs)}")

    def test_runner_sink_packet_drives_no_branch_and_routes_only_to_turnresult(self):
        runner = _class(_service_tree("agent_loop.py"), "AgentRunner")
        run_turn = _method(runner, "run_turn")
        self.assertIsNotNone(run_turn)
        self.assertEqual(_branch_uses(run_turn, "_audit_evidence_packet"), [],
                         msg="runner packet drives a control branch")
        receivers = _call_receivers(run_turn, "_audit_evidence_packet")
        self.assertTrue(receivers <= {"TurnResult"},
                        msg=f"runner packet routed beyond TurnResult: {sorted(receivers)}")

    def test_owner_packet_drives_no_branch(self):
        owner = _class(_service_tree(_OWNER_MODULE), "PrivateGenerationOwner")
        run = _method(owner, "run")
        self.assertIsNotNone(run)
        self.assertEqual(_branch_uses(run, "audit_packet"), [],
                         msg="owner packet drives a control branch")


# --------------------------------------------------------------------------- #
# Framing: resting-state characterization, not a permanent ban
# --------------------------------------------------------------------------- #

class TestRestingStateNotPermanentBan(unittest.TestCase):

    def test_governed_admission_remains_the_legitimate_future_path(self):
        # A future *governed* Document B crossing stays legitimate (Document A
        # A-O3): this file characterizes the current resting state, it does not
        # forbid future governed implementation.
        contract = _read(os.path.join(
            _docs_dir(),
            "TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md")).lower()
        frame = _read(os.path.join(
            _docs_dir(),
            "TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md")).lower()
        self.assertIn("governed admission", contract)
        self.assertIn("governed admission", frame)


if __name__ == "__main__":
    unittest.main()
