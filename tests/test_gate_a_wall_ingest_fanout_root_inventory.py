"""Gate A wall — A-C1 ingest fan-out root inventory (PREREQUISITE INVENTORY ONLY).

Scope (Codex-authorized, one tests/source-only pre-implementation guard slice):
maps the CURRENT ordinary-ingest fan-out root and the known direct/bypass writer
surfaces, as a prerequisite inventory for a future A-C1 enforcement slice.

It does **not** claim A-C1 ("structural non-reachability at the ordinary ingest
fan-out root") is satisfied — least of all under a future live unadmitted-candidate
producer, which does not exist today. It only snapshots today's writer/fan-out
surfaces so a future enforcement slice (separately authorized) has an accurate
ground truth, and so a NEW unclassified live writer/fan-out root trips a guard for
trio classification rather than landing silently.

NAMING NOTE: Document A / the wall frame / the enforcement-path proposal call the
ordinary ingest fan-out root "MemoryFabric.ingest". The live class is
`TormentFabric` (fabric.py); there is no `MemoryFabric` class. This guard anchors
on the real class and records the mapping. (Reconciliation is a docs note for the
trio, not a code change here.)

Method: source/AST inventory of the allowed files with a writer/fan-out **verb**
filter, snapshotted into explicit allowlists. The verb filter is an inventory aid,
NOT an exhaustive writer detector — a future enforcement slice must prove A-C1
structurally under a live producer, not by name alone.

Guards fail ONLY when a new writer/fan-out root appears outside the allowlists
(i.e., `discovered - allowlist != {}`); removals do not fail, and existing parked
seams are allowlisted (classified, not solved). If a guard fails, do NOT patch
production — report it as a gate decision issue.

No production code, no docs, no wall mechanics, no fixes. See the no-go list in the
authorizing task; nothing here authorizes any of it.
"""

import ast
import os
import unittest


# Writer / fan-out verb filter (inventory aid only; not exhaustive).
_VERBS = ("ingest", "write", "save", "add", "spawn", "promote", "reinforce",
          "persist", "append", "create", "store", "flush", "emit", "plant",
          "seed", "record", "commit", "reingest", "gravity", "_maybe_emit",
          "update", "merge", "delete", "remove", "increment")

_FABRIC_ROOT_CLASS = "TormentFabric"          # live class; docs say "MemoryFabric"
_ROOT_METHOD = "ingest"

# --- Snapshotted writer-surface allowlists (current resting state) ---------- #
# A NEW name matching the verb filter that is NOT in these sets fails the guard.

_TORMENTFABRIC_WRITERS = frozenset({
    "_create_kernel_state_and_context", "_get_closure_store",
    "_get_environment_store", "_get_reference_store",
    "_maybe_emit_identity_anchor", "_maybe_emit_mood_drift", "_persist_job",
    "_resolve_srg_writeback_target",
    "commit_closure", "create_agent", "decide_motif_merge", "ingest",
    "ingest_reference", "list_motif_merges", "reinforce",
    "reingest_convergence", "write_environment",
})
_WORKSPACE_WRITERS = frozenset({"add_domain"})
_MEMORYGRAPH_WRITERS = frozenset({
    "_append_jsonl", "add_memory", "flush_node", "spawn_memory", "update_payload",
})
_PROMOTION_WRITERS = frozenset({
    "increment_retrieval_counts", "promote_chunk", "save_retrieval_counts",
})
_APP_MUTATION_HANDLERS = frozenset({
    "agent_create", "approve_domain", "archive_delete_document", "archive_query",
    "cancel_repair_job", "checkpoint_save", "cognition_run", "collective_reingest",
    "decide_bridge", "decide_conflict", "decide_motif_merge", "decide_proposal",
    "deep_memory_query", "feedback", "index_rebuild", "ingest", "ingest_document",
    "memory_chain", "memory_trace_bundle", "memory_trace_full", "memory_trace_view",
    "ingest_route_probe", "process_proposals", "process_spirit_reflections_endpoint",
    "promote_chunk_endpoint", "propose_share", "query", "retrieve_assembled",
    "set_governance_flags", "spine_submit_task", "thinking_debug",
    "tool_result_ingest", "trace", "trigger_compression", "workspace_clone",
    "workspace_create", "workspace_maintenance", "workspace_maintenance_job",
    "workspace_repair_embeddings", "workspace_repair_embeddings_job",
})

# Known CLASSIFIED parked / bypass writer surfaces — recorded as classified
# surfaces, NOT solved wall crossings. (No fix applied; cross-checked present.)
_CLASSIFIED_PARKED = {
    "_maybe_emit_identity_anchor": ("TormentFabric", "derived identity writer (parked non-conformance)"),
    "_maybe_emit_mood_drift": ("TormentFabric", "mood_drift -> centroid path (parked non-conformance)"),
    "promote_chunk": ("promotion", "promotion writer"),
    "promote_chunk_endpoint": ("app", "/promote force-bypass surface (parked non-conformance)"),
    "ingest_reference": ("TormentFabric", "reference writer path"),
    "write_environment": ("TormentFabric", "environment writer path"),
    "propose_share": ("app", "shared/proposal path"),
    "process_proposals": ("app", "proposal writer path"),
    "collective_reingest": ("app", "shared reingest path"),
}

_CLASSIFIED_READ_ONLY_POST_HANDLERS = {
    "ingest_route_probe": {
        "path": "/agent/ingest/route_probe",
        "classification": "read-only route prediction; non-mutating; authenticated identically to ingest",
        "evidence": "tests/test_ingest_route_probe_integration.py::test_positive_aligned_drift_route_probe_ingest_and_persistence",
    },
}


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


def _class_method_names(tree, cls):
    c = _class(tree, cls)
    if c is None:
        return []
    return [m.name for m in c.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _top_func(tree, name):
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _top_func_names(tree):
    return [n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _writish(names):
    return {m for m in names if any(v in m for v in _VERBS)}


def _app_mutation_handlers(tree):
    out = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in n.decorator_list:
                if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                        and d.func.attr in ("post", "put", "delete", "patch")):
                    out.add(n.name)
    return out


def _app_route_decorators(tree, name):
    func = _top_func(tree, name)
    if func is None:
        return set()
    out = set()
    for d in func.decorator_list:
        if not (
            isinstance(d, ast.Call)
            and isinstance(d.func, ast.Attribute)
            and d.args
            and isinstance(d.args[0], ast.Constant)
            and isinstance(d.args[0].value, str)
        ):
            continue
        out.add((d.func.attr, d.args[0].value))
    return out


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
# Root identity
# --------------------------------------------------------------------------- #

class TestIngestFanoutRootIdentity(unittest.TestCase):

    def test_root_is_tormentfabric_ingest(self):
        ft = _tree("fabric.py")
        self.assertIsNotNone(_class(ft, _FABRIC_ROOT_CLASS),
                             f"{_FABRIC_ROOT_CLASS} class not found")
        self.assertIn(_ROOT_METHOD, _class_method_names(ft, _FABRIC_ROOT_CLASS),
                      "ordinary ingest fan-out root TormentFabric.ingest not found")

    def test_naming_mapping_no_memoryfabric_class(self):
        # Records the doc/reality mapping: docs say "MemoryFabric.ingest"; the
        # live class is TormentFabric. (Reconciliation is a docs note, not code.)
        ft = _tree("fabric.py")
        self.assertIsNone(_class(ft, "MemoryFabric"),
                          "unexpected MemoryFabric class — update the naming mapping")


# --------------------------------------------------------------------------- #
# Writer-surface inventories — fail only on NEW unclassified roots
# --------------------------------------------------------------------------- #

class TestWriterSurfaceInventory(unittest.TestCase):

    def _assert_no_new(self, discovered, allowlist, where):
        new = discovered - allowlist
        self.assertEqual(
            new, set(),
            msg=(f"NEW unclassified live writer/fan-out root in {where}: "
                 f"{sorted(new)} — gate decision required; do NOT patch production"))

    def test_tormentfabric_writer_surface(self):
        ft = _tree("fabric.py")
        self._assert_no_new(_writish(_class_method_names(ft, "TormentFabric")),
                            _TORMENTFABRIC_WRITERS, "TormentFabric")

    def test_workspace_writer_surface(self):
        ft = _tree("fabric.py")
        self._assert_no_new(_writish(_class_method_names(ft, "Workspace")),
                            _WORKSPACE_WRITERS, "Workspace")

    def test_memorygraph_writer_surface(self):
        gt = _tree("memory_graph.py")
        self._assert_no_new(_writish(_class_method_names(gt, "MemoryGraph")),
                            _MEMORYGRAPH_WRITERS, "MemoryGraph")

    def test_promotion_writer_surface(self):
        pt = _tree("promotion.py")
        self._assert_no_new(_writish(_top_func_names(pt)),
                            _PROMOTION_WRITERS, "promotion")

    def test_app_mutation_endpoint_surface(self):
        # API mutation-verb (POST/PUT/DELETE/PATCH) handlers. NB: some are
        # read-over-POST; this is an API-surface snapshot, not a write verdict.
        at = _tree("app.py")
        self._assert_no_new(_app_mutation_handlers(at),
                            _APP_MUTATION_HANDLERS, "app.py mutation endpoints")

    def test_route_probe_post_surface_is_explicitly_classified_read_only(self):
        at = _tree("app.py")
        classified = _CLASSIFIED_READ_ONLY_POST_HANDLERS["ingest_route_probe"]
        probe = _top_func(at, "ingest_route_probe")
        ingest = _top_func(at, "ingest")

        self.assertEqual(set(_CLASSIFIED_READ_ONLY_POST_HANDLERS), {"ingest_route_probe"})
        self.assertIn("ingest_route_probe", _APP_MUTATION_HANDLERS)
        self.assertIn(("post", classified["path"]), _app_route_decorators(at, "ingest_route_probe"))
        self.assertIsNotNone(probe)
        self.assertIsNotNone(ingest)
        self.assertIn("read-only route prediction", classified["classification"])
        self.assertIn("non-mutating", classified["classification"])
        self.assertIn("authenticated identically to ingest", classified["classification"])
        self.assertIn("resolve_request_context", _called_names(probe))
        self.assertIn("resolve_request_context", _called_names(ingest))
        self.assertIn("preview_route_decision", _idents(probe))
        self.assertNotIn("submit_task", _idents(probe))
        self.assertNotIn("create_agent", _called_names(probe))


# --------------------------------------------------------------------------- #
# Classified parked / bypass surfaces (recorded, not solved)
# --------------------------------------------------------------------------- #

class TestClassifiedParkedSurfaces(unittest.TestCase):

    def test_parked_and_bypass_surfaces_are_classified(self):
        ft = _tree("fabric.py")
        pt = _tree("promotion.py")
        at = _tree("app.py")
        present = {
            "TormentFabric": set(_class_method_names(ft, "TormentFabric")),
            "promotion": set(_top_func_names(pt)),
            "app": _app_mutation_handlers(at),
        }
        missing = [name for name, (where, _desc) in _CLASSIFIED_PARKED.items()
                   if name not in present.get(where, set())]
        # Each classified surface must still exist where we classified it; this is
        # an inventory cross-check, NOT a claim any of them is a solved crossing.
        self.assertEqual(missing, [],
                         msg=f"classified surface(s) no longer found (re-inventory): {missing}")


# --------------------------------------------------------------------------- #
# Outside wall mechanics — query/owner/bridge/packets are not writers/fan-out
# --------------------------------------------------------------------------- #

class TestOutsideWallMechanics(unittest.TestCase):

    _WRITER_CALLS = {"ingest", "spawn_memory", "add_memory", "update_payload",
                     "flush_node", "promote_chunk", "reinforce", "write_environment"}

    def test_agent_query_is_not_a_writer_or_fanout_root(self):
        q = _top_func(_tree("app.py"), "query")
        self.assertIsNotNone(q, "/agent/query handler not found")
        ids = _idents(q)
        for forbidden in ("run_turn", "AgentRunner", "complete"):
            self.assertNotIn(forbidden, ids)
        self.assertEqual(_called_names(q) & self._WRITER_CALLS, set(),
                         msg="/agent/query calls a writer/fan-out method")

    def test_private_owner_unwired(self):
        importers = []
        for base, tree in _iter_service():
            if base == "audit_private_generation_owner.py":
                continue
            ids = _idents(tree)
            if "PrivateGenerationOwner" in ids or "audit_private_generation_owner" in ids:
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

    def test_audit_packets_stay_non_control(self):
        refs = {base for base, tree in _iter_service()
                if "audit_evidence_packet" in _idents(tree)}
        self.assertEqual(refs, {"agent_loop.py", "audit_private_generation_owner.py"},
                         msg=f"unexpected audit_evidence_packet references: {sorted(refs)}")


if __name__ == "__main__":
    unittest.main()
