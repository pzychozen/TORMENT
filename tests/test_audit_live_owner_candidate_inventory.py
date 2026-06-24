"""Tests-only / source-only: candidate live-owner topology inventory.

After the selected-items runner bridge landed (`392caa2`), this file inventories —
by AST / source inspection ONLY — the current candidate owner topology BEFORE any
live owner path is selected. The bridge gate result was PASS, C only: do NOT
select, design, or implement a live owner here. This slice records the evidence a
later gate needs to compare candidate owner shapes without choosing one.

It imports NO `torment_service` module and executes NO service runtime; every
assertion parses source files with `ast`.

Locks (see class docstrings):
  1. Only the approved private bridge passes `audit_admitted_context_items` into
     `run_turn`.
  2. No endpoint / `app.py` / `agent_loop.py` caller becomes a live owner by
     accident.
  3. Candidate owners are inventoried by source for the five owner-relevant call
     sites: `assemble_context`, `AgentRunner.run_turn`, the selected-items bridge,
     the prompt-request / prompt builder, and model completion.
  4. `AgentRunner` owns prompt capture, but not retrieval / assembly / item
     extraction.
  5. The selected-items bridge forwards selected item dicts only and reads no
     result packet.
  6. Records the two — and only two — shapes a future owner could take; neither is
     selected in this slice.
  7. Audit packet presence/absence is consumed by nothing (prompt / review /
     output / ingest / retrieval / ranking / retry / style / writes / persistence).

No production code, no endpoint/schema/API, no prompt memory injection, no
persistence, no memory write, no writer path, no retrieval feedback, no
ranking/suppression/retry/style steering, no review/output control, no
database/substrate, no Gate D, no dream/private cognition, no Envelope Audit
runtime, and no authority wording.
"""

import ast
import os
import unittest


_BRIDGE = "audit_selected_items_runner_bridge.py"
_BRIDGE_REL = "torment_service/audit_selected_items_runner_bridge.py"
# The private generation owner (design shape A): a generation-owner candidate that
# extracts selected items and owns/captures its own prompt; unwired (tests-only).
_OWNER = "audit_private_generation_owner.py"
_OWNER_REL = "torment_service/audit_private_generation_owner.py"
_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}

# The five owner-relevant call sites this inventory tracks.
_OWNER_CALL_SITES = (
    "assemble_context",                            # retrieval / assembly
    "run_turn",                                    # AgentRunner generation entry
    "run_turn_with_selected_items_observation",    # selected-items bridge
    "_build_llm_prompt_request",                   # prompt-request builder
    "_build_system_prompt",                        # prompt builder
    "complete",                                    # model-completion boundary
)


# --------------------------------------------------------------------------- #
# AST / source helpers (no service import; mirrors sibling files' conventions)
# --------------------------------------------------------------------------- #

def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))   # tests/
    return os.path.dirname(here)                          # torment_fabric/


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _parse(path):
    with open(path, "rb") as fh:
        # null-strip tolerates a mount artifact in some sandboxes; the
        # authoritative Windows repo parses cleanly.
        return ast.parse(fh.read().replace(b"\x00", b""))


def _parse_service(filename):
    return _parse(os.path.join(_service_dir(), filename))


def _callee_name(call):
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
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
            nm = _callee_name(n)
            if nm:
                out.add(nm)
    return out


def _call_receivers(func_node, var_name):
    """Callee leaf-names of every Call that receives ``var_name`` (a Name) as a
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


def _iter_py(base):
    """Yield (rel_to_repo, abspath) for every .py under base, skipping junk."""
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns
                  if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
        for fn in fns:
            if fn.endswith(".py"):
                ab = os.path.join(dp, fn)
                yield os.path.relpath(ab, _repo_root()).replace("\\", "/"), ab


def _service_callers_of(name):
    """Service-relative filenames (under torment_service/) that CALL ``name``."""
    out = set()
    for dp, dns, fns in os.walk(_service_dir()):
        dns[:] = [d for d in dns
                  if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            ab = os.path.join(dp, fn)
            try:
                tree = _parse(ab)
            except (SyntaxError, ValueError):
                continue
            if name in _called_names(tree):
                out.add(os.path.relpath(ab, _service_dir()).replace("\\", "/"))
    return out


# --------------------------------------------------------------------------- #
# 1. Only the approved private bridge passes audit_admitted_context_items
# --------------------------------------------------------------------------- #

class TestInvariant1OnlyBridgePassesAuditItems(unittest.TestCase):

    def test_only_bridge_passes_audit_items_into_run_turn(self):
        non_test = set()
        for rel, ab in _iter_py(_repo_root()):
            if rel.startswith("tests/"):
                continue
            try:
                tree = _parse(ab)
            except (SyntaxError, ValueError):
                continue
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "run_turn"
                        and any(k.arg == "audit_admitted_context_items"
                                for k in n.keywords)):
                    non_test.add(rel)
        self.assertEqual(
            sorted(non_test), [_BRIDGE_REL],
            msg=f"non-test run_turn callers passing audit items: {sorted(non_test)}")


# --------------------------------------------------------------------------- #
# 2. No endpoint / app.py / agent_loop.py becomes a live owner by accident
# --------------------------------------------------------------------------- #

class TestInvariant2NoAccidentalLiveOwner(unittest.TestCase):

    def test_endpoint_app_is_not_a_runner_owner(self):
        app = _parse_service("app.py")
        leaves, names = _import_leaves_names(app)
        self.assertNotIn("agent_loop", leaves)
        self.assertNotIn("AgentRunner", names)
        ids = _idents(app)
        self.assertNotIn("AgentRunner", ids)
        self.assertNotIn("run_turn", ids)
        self.assertNotIn("run_turn_with_selected_items_observation", ids)

    def test_runner_owner_does_not_retrieve_assemble_or_extract(self):
        al = _parse_service("agent_loop.py")
        leaves, names = _import_leaves_names(al)
        self.assertNotIn("retrieval_assembler", leaves)
        self.assertNotIn("audit_evidence_context", leaves)
        self.assertNotIn("AssembledContext", names)
        called = _called_names(al)
        self.assertNotIn("assemble_context", called)
        self.assertNotIn("selected_admitted_items", called)
        self.assertNotIn("AssembledContext", _idents(al))

    def test_no_endpoint_or_runner_function_fuses_assembly_and_generation(self):
        # In app.py + agent_loop.py specifically, no single function both
        # assembles/extracts AND generates — so neither pole accidentally becomes
        # a live owner. (The recognized bridge candidate is handled in §6.)
        assemble = {"assemble_context", "selected_admitted_items",
                    "run_turn_with_selected_items_observation"}
        generate = {"run_turn", "complete", "_build_llm_prompt_request"}
        offenders = []
        for fname in ("app.py", "agent_loop.py"):
            tree = _parse_service(fname)
            for fn in _all_functions(tree):
                calls = _called_names(fn)
                if (calls & assemble) and (calls & generate):
                    offenders.append(f"{fname}::{fn.name}")
        self.assertEqual(
            offenders, [],
            msg=f"endpoint/runner function fuses assembly and generation: {offenders}")


# --------------------------------------------------------------------------- #
# 3. Candidate-owner inventory by source (production service scope)
# --------------------------------------------------------------------------- #

class TestInvariant3CandidateOwnerInventory(unittest.TestCase):
    """Explicit by-source inventory of the five owner-relevant call sites, scoped
    to production service modules (torment_service/). Recorded as exact sets so a
    later gate can compare candidate owner shapes with evidence."""

    def test_assemble_context_caller_inventory(self):
        # Retrieval / assembly is owned only by the /retrieve endpoint handler.
        self.assertEqual(_service_callers_of("assemble_context"), {"app.py"})

    def test_run_turn_caller_inventory(self):
        # Generation entry is reached only by the runner's own reflex self-call
        # and the approved private bridge — no endpoint, no other service module.
        self.assertEqual(_service_callers_of("run_turn"),
                         {"agent_loop.py", _BRIDGE})

    def test_selected_items_bridge_caller_inventory(self):
        # The bridge is a dead-end in production: no service module calls it.
        self.assertEqual(
            _service_callers_of("run_turn_with_selected_items_observation"), set())

    def test_prompt_request_and_builder_caller_inventory(self):
        # The prompt request + system-prompt builder are owned only by the runner.
        self.assertEqual(_service_callers_of("_build_llm_prompt_request"),
                         {"agent_loop.py"})
        self.assertEqual(_service_callers_of("_build_system_prompt"),
                         {"agent_loop.py"})

    def test_model_completion_caller_inventory(self):
        # The model-completion boundary is reached by the runner and the private
        # generation owner (design shape A; unwired, tests-only). No endpoint or
        # other service module.
        self.assertEqual(_service_callers_of("complete"),
                         {"agent_loop.py", _OWNER})

    def test_inventory_snapshot_is_exact(self):
        # One explicit snapshot for the next gate's A-vs-B comparison.
        snapshot = {name: sorted(_service_callers_of(name))
                    for name in _OWNER_CALL_SITES}
        self.assertEqual(snapshot, {
            "assemble_context": ["app.py"],
            "run_turn": ["agent_loop.py", _BRIDGE],
            "run_turn_with_selected_items_observation": [],
            "_build_llm_prompt_request": ["agent_loop.py"],
            "_build_system_prompt": ["agent_loop.py"],
            "complete": ["agent_loop.py", _OWNER],
        })


# --------------------------------------------------------------------------- #
# 4. AgentRunner owns prompt capture only
# --------------------------------------------------------------------------- #

class TestInvariant4RunnerOwnsPromptCaptureOnly(unittest.TestCase):

    def setUp(self):
        self.al = _parse_service("agent_loop.py")
        self.runner = _class(self.al, "AgentRunner")

    def test_runner_owns_prompt_capture(self):
        # Prompt building / capture lives inside AgentRunner.
        self.assertIsNotNone(_method(self.runner, "_build_llm_prompt_request"))
        self.assertIsNotNone(_method(self.runner, "_build_system_prompt"))
        execute = _method(self.runner, "_execute")
        self.assertIsNotNone(execute)
        ecalls = _called_names(execute)
        self.assertIn("_build_llm_prompt_request", ecalls)
        self.assertIn("complete", ecalls)

    def test_runner_does_not_own_retrieval_assembly_or_extraction(self):
        called = _called_names(self.al)
        self.assertNotIn("assemble_context", called)
        self.assertNotIn("selected_admitted_items", called)
        self.assertNotIn("run_turn_with_selected_items_observation", called)
        leaves, names = _import_leaves_names(self.al)
        self.assertNotIn("retrieval_assembler", leaves)
        self.assertNotIn("audit_evidence_context", leaves)
        self.assertNotIn("AssembledContext", names)


# --------------------------------------------------------------------------- #
# 5. Bridge forwards selected item dicts only and reads no result packet
# --------------------------------------------------------------------------- #

class TestInvariant5BridgeForwardsItemsOnlyReadsNoPacket(unittest.TestCase):

    def setUp(self):
        self.bridge = _parse_service(_BRIDGE)

    def test_bridge_calls_extractor_and_forwards_a_local_not_a_parameter(self):
        self.assertIn("selected_admitted_items", _called_names(self.bridge))
        offenders = []
        for fn in _all_functions(self.bridge):
            params = {a.arg for a in fn.args.args}
            params |= {a.arg for a in fn.args.kwonlyargs}
            params |= {a.arg for a in fn.args.posonlyargs}
            for n in ast.walk(fn):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "run_turn"):
                    for k in n.keywords:
                        if (k.arg == "audit_admitted_context_items"
                                and isinstance(k.value, ast.Name)
                                and k.value.id in params):
                            offenders.append((fn.name, k.value.id))
        self.assertEqual(
            offenders, [],
            msg=f"bridge forwards a raw parameter as audit items: {offenders}")

    def test_bridge_reads_no_result_packet(self):
        # The bridge returns run_turn's result directly and never reads a packet
        # off it.
        ids = _idents(self.bridge)
        self.assertNotIn("audit_evidence_packet", ids)
        self.assertNotIn("evidence_items", ids)
        returns_runturn = [
            getattr(n, "lineno", -1) for n in ast.walk(self.bridge)
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Attribute)
            and n.value.func.attr == "run_turn"
        ]
        self.assertTrue(returns_runturn,
                        "bridge does not return run_turn(...) result directly")

    def test_bridge_import_surface_is_closed(self):
        leaves, _ = _import_leaves_names(self.bridge)
        self.assertEqual(
            leaves - {"__future__", "typing", "audit_evidence_context"}, set())


# --------------------------------------------------------------------------- #
# 6. Two candidate future-owner shapes recorded; neither selected here
# --------------------------------------------------------------------------- #

class TestInvariant6FutureOwnerShapesRecordedNeitherSelected(unittest.TestCase):
    """Records the two — and only two — shapes a future LIVE owner could take, and
    proves neither is a live (wired) owner today. Shape A (private generation
    owner) now exists as an UNWIRED private module; shape B (runner delegation
    seam) remains deferred. Selection of a live owner is out of scope here."""

    # Documented for the next gate (record only; NOT authorization):
    #   * a private generation owner that holds the captured prompt/messages, or
    #   * a private runner delegation seam.
    CANDIDATE_OWNER_SHAPES = (
        "private_generation_owner_with_captured_prompt_messages",
        "private_runner_delegation_seam",
    )

    def test_exactly_two_candidate_shapes_recorded(self):
        self.assertEqual(len(self.CANDIDATE_OWNER_SHAPES), 2)
        self.assertEqual(len(set(self.CANDIDATE_OWNER_SHAPES)), 2)

    def test_only_unwired_seams_fuse_assembly_and_generation(self):
        # Extraction/assembly ownership and generation/prompt ownership are
        # DISJOINT across production EXCEPT in the two recognized UNWIRED
        # candidates: the runner delegation-seam bridge (shape B candidate) and the
        # private generation owner (shape A). Neither is a live owner.
        assemble = {"assemble_context", "selected_admitted_items"}
        generate = {"run_turn", "complete", "_build_llm_prompt_request",
                    "_build_system_prompt"}
        fusing = set()
        for rel, ab in _iter_py(_service_dir()):
            try:
                tree = _parse(ab)
            except (SyntaxError, ValueError):
                continue
            for fn in _all_functions(tree):
                calls = _called_names(fn)
                if (calls & assemble) and (calls & generate):
                    fusing.add(rel)
        self.assertEqual(
            fusing, {_BRIDGE_REL, _OWNER_REL},
            msg=f"unexpected assembly+generation fusion: {sorted(fusing)}")
        # Bridge candidate: called nowhere, packet-blind.
        self.assertEqual(
            _service_callers_of("run_turn_with_selected_items_observation"), set())
        self.assertNotIn("audit_evidence_packet", _idents(_parse_service(_BRIDGE)))
        # Owner candidate: no service module imports it (unwired, tests-only).
        owner_importers = set()
        for rel, ab in _iter_py(_service_dir()):
            if os.path.basename(ab) == _OWNER:
                continue
            try:
                leaves, names = _import_leaves_names(_parse(ab))
            except (SyntaxError, ValueError):
                continue
            if ("audit_private_generation_owner" in leaves
                    or "PrivateGenerationOwner" in names):
                owner_importers.add(rel)
        self.assertEqual(owner_importers, set(),
                         msg=f"owner wired into: {sorted(owner_importers)}")

    def test_generation_owner_exists_as_module_but_is_unwired(self):
        # Shape A now EXISTS as a private module, but it is UNWIRED: no service
        # module imports it (tests-only). The live runner (agent_loop.py) still
        # owns prompt capture + completion and does NOT fuse retrieval/extraction,
        # so it is not itself a generation owner.
        self.assertTrue(os.path.exists(os.path.join(_service_dir(), _OWNER)))
        al = _parse_service("agent_loop.py")
        called = _called_names(al)
        self.assertIn("complete", called)
        self.assertIn("_build_llm_prompt_request", called)
        self.assertFalse(called & {"assemble_context", "selected_admitted_items"})


# --------------------------------------------------------------------------- #
# 7. Audit packet presence/absence consumed by nothing
# --------------------------------------------------------------------------- #

class TestInvariant7PacketPresenceUnused(unittest.TestCase):
    """The audit evidence packet is observation-only: its presence or absence is
    consumed by no prompt / review / output / ingest / retrieval / ranking / retry
    / style / write / persistence path."""

    def test_packet_identifier_only_in_runner_sink_or_owner_result(self):
        # The packet identifier appears only in the runner sink (agent_loop.py) and
        # the private generation owner's result (audit_private_generation_owner.py).
        # Both are observation-only: the owner returns the packet and drives no
        # branch on it (proven in tests/test_audit_private_generation_owner.py).
        refs = set()
        for rel, ab in _iter_py(_service_dir()):
            try:
                tree = _parse(ab)
            except (SyntaxError, ValueError):
                continue
            if "audit_evidence_packet" in _idents(tree):
                refs.add(os.path.relpath(ab, _service_dir()).replace("\\", "/"))
        self.assertEqual(
            refs, {"agent_loop.py", _OWNER},
            msg=f"unexpected audit_evidence_packet references: {sorted(refs)}")

    def test_built_packet_routes_only_to_turnresult_and_drives_no_branch(self):
        runner = _class(_parse_service("agent_loop.py"), "AgentRunner")
        run_turn = _method(runner, "run_turn")
        self.assertIsNotNone(run_turn)
        # The built packet local flows only into TurnResult(...).
        receivers = _call_receivers(run_turn, "_audit_evidence_packet")
        self.assertTrue(receivers <= {"TurnResult"},
                        msg=f"packet routed beyond TurnResult: {sorted(receivers)}")
        # The packet local is never used as a control-branch condition.
        branch_uses = []
        for n in ast.walk(run_turn):
            tests = []
            if isinstance(n, (ast.If, ast.While, ast.IfExp)):
                tests.append(n.test)
            for t in tests:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Name) and sub.id == "_audit_evidence_packet":
                        branch_uses.append(getattr(n, "lineno", -1))
        self.assertEqual(branch_uses, [],
                         msg=f"packet used as a control branch at lines: {branch_uses}")


if __name__ == "__main__":
    unittest.main()
