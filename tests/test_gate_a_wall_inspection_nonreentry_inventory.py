"""Gate A wall — A-I1 inspection read-only / non-reentrant inventory
(PREREQUISITE INVENTORY ONLY).

Scope (Codex-authorized, one tests/source-only pre-implementation guard slice):
inventories and classifies the CURRENT inspection / debug / audit / trace surfaces
adjacent to memory, audit packets, projection, or wall language, and locks that
none of them reaches a writer / prompt / retrieval / control path.

A-I1 ("inspection ≠ projection"): inspection defaults to operator/governance-
auditable visibility only; it must not create prompt-visible / caller-visible /
retrieval-visible / cognition-visible exposure unless separately surface-classified
and governed.

This does **not** prove A-I1 for a *future real candidate inspection surface* —
no contained-candidate inspection surface exists today. It only snapshots and
classifies today's inspection surfaces so a future enforcement slice (separately
authorized) has accurate ground truth, and so a NEW unclassified inspection
surface — or a classified read-only surface that grows a forbidden reach — trips a
guard for trio classification rather than landing silently.

Classification vocabulary per surface: read-only / caller-visible / prompt-visible
/ retrieval-visible / writer-reaching / reentrant-by-action. **reentrant-by-action
is a classification, not automatically a violation** (a caller may always re-feed
data it received; the hazard A-I1 guards is *silent* projection/re-entry, not a
caller choosing to resubmit).

Guards fail ONLY when (a) a new unclassified inspection/debug/audit/trace surface
appears, or (b) a classified inspection surface reaches a forbidden writer / prompt
/ retrieval / control path. If a guard fails, do NOT patch production — report it
as a gate issue.

No production code, no docs, no wall mechanics, no fixes (see the authorizing
task's no-go list; nothing here authorizes any of it).
"""

import ast
import os
import unittest


# Name/path hints that mark an inspection / debug / audit / trace surface.
_INSPECT_HINTS = ("trace", "debug", "audit", "inspect", "explain", "chain",
                  "alignment", "profiles", "roles", "view", "bundle", "provenance")

# Writer / prompt / retrieval / control reach an inspection surface must NOT take.
_FORBIDDEN_CALLS = frozenset({
    "ingest", "promote_chunk", "reinforce", "assemble_context", "run_turn",
    "complete", "spawn_memory", "add_memory", "update_payload", "write_environment",
    "_build_llm_prompt_request", "_build_system_prompt",
    "run_turn_with_selected_items_observation",
})
_FORBIDDEN_IDENTS = frozenset({"AgentRunner", "PrivateGenerationOwner"})

_VALID_LABELS = frozenset({
    "read-only", "caller-visible", "prompt-visible", "retrieval-visible",
    "writer-reaching", "reentrant-by-action",
})

# --- Snapshotted inspection-surface inventory (current resting state) -------- #
# Every value is a read-only, caller-visible surface that returns data (hence
# reentrant-by-action by caller choice); none is prompt-visible, retrieval-visible,
# or writer-reaching. A NEW inspection-named handler not in this set fails the
# guard (classify it). Labels are descriptive; the enforced locks are §2/§3 below.
_APP_INSPECTION_SURFACES = {
    "workspace_embed_audit": {"read-only", "caller-visible", "reentrant-by-action"},
    "workspaces_embed_audit_summary": {"read-only", "caller-visible", "reentrant-by-action"},
    "profiles": {"read-only", "caller-visible", "reentrant-by-action"},
    "get_roles": {"read-only", "caller-visible", "reentrant-by-action"},
    "governance_audit": {"read-only", "caller-visible", "reentrant-by-action"},
    "trace": {"read-only", "caller-visible", "reentrant-by-action"},
    "memory_chain": {"read-only", "caller-visible", "reentrant-by-action"},
    "memory_trace_full": {"read-only", "caller-visible", "reentrant-by-action"},
    "memory_trace_bundle": {"read-only", "caller-visible", "reentrant-by-action"},
    "memory_trace_view": {"read-only", "caller-visible", "reentrant-by-action"},
    "list_retrieval_profiles": {"read-only", "caller-visible", "reentrant-by-action"},
    "list_geo_profiles": {"read-only", "caller-visible", "reentrant-by-action"},
    "thinking_debug": {"read-only", "caller-visible", "reentrant-by-action"},
    "thinking_alignment_recent": {"read-only", "caller-visible", "reentrant-by-action"},
    "debug_metrics": {"read-only", "caller-visible", "reentrant-by-action"},
    "debug_provenance": {"read-only", "caller-visible", "reentrant-by-action"},
}

# Fabric read-only trace/inspection methods (TormentFabric).
_FABRIC_TRACE_SURFACES = frozenset({
    "trace", "trace_full_graph", "trace_bundle", "_trace_narrative", "trace_view",
})

# The inert observation helper (explicit-input, returns packet-or-None).
_OBSERVER_MODULE = "audit_prompt_inclusion_observation.py"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _service_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "torment_service")


def _tree(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _class(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


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
    return out


def _route_handlers(tree):
    """{name: node} for top-level functions decorated with an HTTP verb."""
    out = {}
    for n in tree.body:
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for d in n.decorator_list:
            if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                    and d.func.attr in ("get", "post", "put", "delete", "patch")):
                paths = " ".join(str(a.value) for a in d.args if isinstance(a, ast.Constant))
                out[n.name] = (n, f"{n.name} {paths}".lower())
    return out


def _inspection_handlers(tree):
    """{name: node} for route handlers whose name/path marks them inspection-ish."""
    return {name: node for name, (node, blob) in _route_handlers(tree).items()
            if any(h in blob for h in _INSPECT_HINTS)}


def _iter_service():
    for dp, dns, fns in os.walk(_service_dir()):
        dns[:] = [d for d in dns if d not in {".git", "__pycache__"} and not d.startswith("do_not_touch")]
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            ab = os.path.join(dp, fn)
            try:
                with open(ab, "rb") as fh:
                    src = fh.read()
                tree = ast.parse(src.replace(b"\x00", b""))
            except (SyntaxError, ValueError, OSError):
                continue
            yield os.path.basename(ab), tree


# --------------------------------------------------------------------------- #
# 1. Inventory completeness — no new unclassified inspection surface
# --------------------------------------------------------------------------- #

class TestInspectionSurfaceInventory(unittest.TestCase):

    def test_no_new_unclassified_app_inspection_surface(self):
        discovered = set(_inspection_handlers(_tree("app.py")))
        new = discovered - set(_APP_INSPECTION_SURFACES)
        self.assertEqual(
            new, set(),
            msg=(f"NEW unclassified inspection/debug/audit/trace surface(s): "
                 f"{sorted(new)} — classify (gate issue); do NOT patch production"))

    def test_no_new_unclassified_fabric_trace_surface(self):
        tf = _class(_tree("fabric.py"), "TormentFabric")
        discovered = {m.name for m in tf.body
                      if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and any(h in m.name.lower() for h in ("trace", "explain", "inspect", "audit"))}
        new = discovered - _FABRIC_TRACE_SURFACES
        self.assertEqual(new, set(),
                         msg=f"NEW unclassified fabric trace surface(s): {sorted(new)}")

    def test_inventory_labels_are_valid(self):
        for name, labels in _APP_INSPECTION_SURFACES.items():
            self.assertLessEqual(labels, _VALID_LABELS,
                            msg=f"{name}: invalid label(s) {sorted(labels - _VALID_LABELS)}")
            self.assertIn("read-only", labels, msg=f"{name}: not classified read-only")


# --------------------------------------------------------------------------- #
# 2. Inspection surfaces reach no writer / prompt / retrieval / control path
# --------------------------------------------------------------------------- #

class TestInspectionSurfacesReachNoForbiddenPath(unittest.TestCase):

    def test_app_inspection_handlers_reach_nothing_forbidden(self):
        handlers = _route_handlers(_tree("app.py"))
        offenders = {}
        for name in _APP_INSPECTION_SURFACES:
            node = handlers.get(name, (None,))[0]
            if node is None:
                continue   # absence handled by inventory-completeness tests
            bad = (_called_names(node) & _FORBIDDEN_CALLS) | (_idents(node) & _FORBIDDEN_IDENTS)
            if bad:
                offenders[name] = sorted(bad)
        self.assertEqual(offenders, {},
                         msg=(f"inspection surface reaches forbidden writer/prompt/"
                              f"retrieval/control path: {offenders} — gate issue"))

    def test_fabric_trace_methods_reach_nothing_forbidden(self):
        tf = _class(_tree("fabric.py"), "TormentFabric")
        offenders = {}
        for m in tf.body:
            if (isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and m.name in _FABRIC_TRACE_SURFACES):
                bad = sorted((_called_names(m) & _FORBIDDEN_CALLS)
                             | (_idents(m) & _FORBIDDEN_IDENTS))
                if bad:
                    offenders[m.name] = bad
        self.assertEqual(offenders, {}, msg=f"fabric trace reaches forbidden: {offenders}")

    def test_inert_observer_reaches_nothing_forbidden(self):
        t = _tree(_OBSERVER_MODULE)
        bad = sorted((_called_names(t) & _FORBIDDEN_CALLS) | (_idents(t) & _FORBIDDEN_IDENTS))
        self.assertEqual(bad, [], msg=f"observer reaches forbidden: {bad}")


# --------------------------------------------------------------------------- #
# 3. Audit producers (owner/bridge) classified as unwired — not inspection
# --------------------------------------------------------------------------- #

class TestAuditProducersClassifiedNotInspection(unittest.TestCase):
    """The private generation owner and selected-items bridge call their own
    mechanics (`complete`, `run_turn`) and are therefore NOT inspection surfaces;
    they are classified as unwired/dead-end audit producers (non-reachable by
    topology). They are excluded from the §2 inspection forbidden-reach lock by
    construction, and locked here as unwired instead."""

    def test_private_owner_unwired(self):
        importers = []
        for base, tree in _iter_service():
            if base == "audit_private_generation_owner.py":
                continue
            if ("PrivateGenerationOwner" in _idents(tree)
                    or "audit_private_generation_owner" in _idents(tree)):
                importers.append(base)
        self.assertEqual(importers, [], msg=f"owner wired into: {importers}")

    def test_selected_items_bridge_dead_end(self):
        callers = []
        for base, tree in _iter_service():
            if base == "audit_selected_items_runner_bridge.py":
                continue
            if "run_turn_with_selected_items_observation" in _called_names(tree):
                callers.append(base)
        self.assertEqual(callers, [], msg=f"bridge called by: {callers}")


# --------------------------------------------------------------------------- #
# 4. Audit packet presence/absence remains non-control
# --------------------------------------------------------------------------- #

class TestAuditPacketNonControl(unittest.TestCase):

    def _branch_uses(self, func, var):
        uses = []
        for n in ast.walk(func):
            if isinstance(n, (ast.If, ast.While, ast.IfExp)):
                for sub in ast.walk(n.test):
                    if isinstance(sub, ast.Name) and sub.id == var:
                        uses.append(getattr(n, "lineno", -1))
        return uses

    def _method(self, tree, cls, name):
        c = _class(tree, cls)
        for m in (c.body if c else []):
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == name:
                return m
        return None

    def test_packet_identifier_confined(self):
        refs = {base for base, tree in _iter_service()
                if "audit_evidence_packet" in _idents(tree)}
        self.assertEqual(refs, {"agent_loop.py", "audit_private_generation_owner.py"},
                         msg=f"unexpected audit_evidence_packet references: {sorted(refs)}")

    def test_runner_packet_drives_no_branch(self):
        run_turn = self._method(_tree("agent_loop.py"), "AgentRunner", "run_turn")
        self.assertIsNotNone(run_turn)
        self.assertEqual(self._branch_uses(run_turn, "_audit_evidence_packet"), [],
                         msg="runner packet drives a control branch")

    def test_owner_packet_drives_no_branch(self):
        run = self._method(_tree("audit_private_generation_owner.py"),
                           "PrivateGenerationOwner", "run")
        self.assertIsNotNone(run)
        self.assertEqual(self._branch_uses(run, "audit_packet"), [],
                         msg="owner packet drives a control branch")


if __name__ == "__main__":
    unittest.main()
