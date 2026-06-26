"""Gate A — Seam B (ingest-entry structural gate) characterization slice.

Tests/source-only. Codex/operator-authorized as the FIRST, bounded,
producer-independent Seam B characterization (see
``docs/TORMENT_GATE_A_WALL_ENFORCEMENT_PATH_AUTHORIZATION_REVIEW_v0.1.md``,
Tier-1). It characterizes the *chokepoint terrain* an eventual ingest-entry
structural gate would occupy, by extending the existing resting-state
characterizations:

  * ``58d5a49`` — ingest fan-out root inventory (T1 sole-entry shape).
  * ``8f8fa7a`` — no-tag-dependence (T2).
  * ``0dbe7cc`` / ``c73add5`` — inspection / projection-safety (T3).
  * ``2732f32`` — structural non-reachability (T4 deliberation containment).

Covered (Tier-1, producer-independent):
  T1  sole-entry shape only — TormentFabric.ingest is the ordinary ingest
      fan-out root, and the five landed Layer-4 negative-containment guards form
      the perimeter; a NEW unclassified candidate-refusal module trips the guard.
  L4  Layer-4 perimeter carry-forward — the five CandidateShapedValue refusal
      surfaces stay type-only / content-blind / contents-free / non-recursive /
      no tag-key-provenance-schema policing.
  T2  no-tag-dependence — the Seam B surfaces gate on NO reflection-exclusion tag.
  T3  inspection / non-reentry — the refusal guards reach no writer / prompt /
      retrieval / control path; audit packets stay non-control; the candidate
      perimeter is not exposed on any caller-visible app surface.
  T4  deliberation containment — AgentRunner / /agent/query / private generation
      owner / selected-items bridge / audit packet lane gain NO contained / candidate
      input; the candidate type's footprint excludes every deliberation surface.
  Postponed-surface classification — ArchiveStore / links / update_payload are
      recorded ONLY as proof-scope dependency questions for the sole-entry proof.

This slice characterizes chokepoint terrain only. It does NOT:
  * build the Gate A wall;
  * claim A-C1 is satisfied under a future live candidate producer;
  * claim Gate A wall completion, or that all writes are governed, or producer
    containment, or admission / promotion correctness;
  * open Gate D / private cognition;
  * authorize or create candidate producer / store / governed admission / promotion
    machinery;
  * fix writer hazards;
  * turn ArchiveStore / links / update_payload into a second Layer-4 brick series,
    add guards to them, fix them, or claim them closed.

Deferred / out of scope (each needs a separately authorized carrier): live-producer
A-C1 / A-C2, admission-sole-exit A-O3, staging/admission/promotion distinction
A-D1 / A-D2, candidate inspection surface, candidate store, governed admission,
promotion crossing, Seam C writer authority + all writer fixes, Gate D runtime,
database / substrate, endpoint / API / schema expansion.

If any guard here fails, do NOT patch production — return it as a gate decision.
"""

import ast
import os
import unittest


# --------------------------------------------------------------------------- #
# Seam B surface map — class / method / directly-guarded ordinary-write params
# --------------------------------------------------------------------------- #

_SEAM_B_SURFACES = {
    "fabric.py": ("TormentFabric", "ingest", {"text"}),
    "memory_graph.py": ("MemoryGraph", "spawn_memory", {"summary", "extra_payload"}),
    "environment_memory.py": ("EnvironmentStore", "write", {"value"}),
    "reference_memory.py": ("ReferenceStore", "ingest",
                            {"title", "body", "source_link", "source_kind", "metadata"}),
}

# Dict params whose IMMEDIATE values are scanned key-blind via `.values()`.
_IMMEDIATE_VALUE_PARAMS = {
    "memory_graph.py": ("MemoryGraph", "spawn_memory", "extra_payload"),
    "reference_memory.py": ("ReferenceStore", "ingest", "metadata"),
}

# The ONLY service modules that may reference the inert candidate type:
# its definition + the five landed refusal surfaces. (memory_graph holds two of
# the five surfaces.) A new referencing module trips the perimeter footprint guard.
_CANDIDATE_FOOTPRINT_MODULES = frozenset({
    "candidate_types.py",
    "fabric.py",
    "memory_graph.py",
    "environment_memory.py",
    "reference_memory.py",
})
_CANDIDATE_TOKEN = "CandidateShapedValue"

# Reflection-exclusion / reflection-source tags (gate-position match only;
# the overloaded admit/admitted/admission vocabulary is deliberately excluded).
_EXCLUSION_TAGS = frozenset({
    "unadmitted", "from_reflection", "is_reflection", "reflection_candidate",
    "contained", "exclude_from_cognition", "do_not_admit",
})

# Writer / prompt / retrieval / control reaches a refusal guard must NOT take.
_FORBIDDEN_GUARD_CALLS = frozenset({
    "ingest", "spawn_memory", "add_memory", "update_payload", "flush_node",
    "write", "write_environment", "promote_chunk", "reinforce",
    "assemble_context", "run_turn", "complete", "_build_system_prompt",
    "_build_llm_prompt_request", "run_turn_with_selected_items_observation",
})

_OWNER_MODULE = "audit_private_generation_owner.py"
_BRIDGE_MODULE = "audit_selected_items_runner_bridge.py"
_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}

# Postponed surfaces — recorded ONLY as proof-scope dependency questions.
_POSTPONED = {
    "ArchiveStore.ingest_document": (
        "archive_memory.py",
        "alternate ordinary-memory ingress (HTTP document path); lower relevance; "
        "HTTP cannot carry a CandidateShapedValue; archive text self-defends"),
    "MemoryGraph.spawn_memory:links": (
        "memory_graph.py",
        "graph link param; structurally open but production-unreachable"),
    "MemoryGraph.update_payload": (
        "memory_graph.py",
        "mutation surface; current callers internally constructed"),
}


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _docs_dir():
    return os.path.join(_repo_root(), "docs")


def _src(basename):
    with open(os.path.join(_service_dir(), basename), "rb") as fh:
        return fh.read().replace(b"\x00", b"").decode("utf-8", "replace")


def _tree(basename):
    return ast.parse(_src(basename))


def _read_doc(name):
    with open(os.path.join(_docs_dir(), name), "r", encoding="utf-8") as fh:
        return fh.read()


def _class(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


def _method(tree, cls, name):
    c = _class(tree, cls)
    for m in (c.body if c else []):
        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == name:
            return m
    return None


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


def _iter_service():
    for dp, dns, fns in os.walk(_service_dir()):
        dns[:] = [d for d in dns
                  if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            ab = os.path.join(dp, fn)
            try:
                with open(ab, "rb") as fh:
                    tree = ast.parse(fh.read().replace(b"\x00", b""))
            except (SyntaxError, ValueError, OSError):
                continue
            yield os.path.relpath(ab, _service_dir()).replace("\\", "/"), tree


def _is_candidate_isinstance(test):
    """True if `test` is exactly isinstance(<x>, CandidateShapedValue)."""
    return (isinstance(test, ast.Call)
            and isinstance(test.func, ast.Name) and test.func.id == "isinstance"
            and len(test.args) == 2
            and isinstance(test.args[1], ast.Name)
            and test.args[1].id == _CANDIDATE_TOKEN)


def _candidate_guards(func):
    """[(guarded_name_or_None, if_node)] for every candidate-refusal guard in func."""
    out = []
    for n in ast.walk(func):
        if isinstance(n, ast.If) and _is_candidate_isinstance(n.test):
            arg0 = n.test.args[0]
            name = arg0.id if isinstance(arg0, ast.Name) else None
            out.append((name, n))
    return out


def _gate_position_tags(tree):
    """{(kind, tag)} for any exclusion tag in a GATE position (identifier /
    attribute / keyword / dict key / subscript key / `.get(...)` key). Raw string
    occurrences in comments/docstrings are intentionally ignored."""
    hits = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id in _EXCLUSION_TAGS:
            hits.add(("name", n.id))
        elif isinstance(n, ast.Attribute) and n.attr in _EXCLUSION_TAGS:
            hits.add(("attr", n.attr))
        elif isinstance(n, ast.keyword) and n.arg in _EXCLUSION_TAGS:
            hits.add(("keyword", n.arg))
        elif isinstance(n, ast.Dict):
            for k in n.keys:
                if isinstance(k, ast.Constant) and k.value in _EXCLUSION_TAGS:
                    hits.add(("dict_key", k.value))
        elif isinstance(n, ast.Subscript):
            sl = n.slice
            if isinstance(sl, ast.Index):           # py < 3.9
                sl = sl.value
            if isinstance(sl, ast.Constant) and sl.value in _EXCLUSION_TAGS:
                hits.add(("subscript", sl.value))
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "get" and n.args):
            a0 = n.args[0]
            if isinstance(a0, ast.Constant) and a0.value in _EXCLUSION_TAGS:
                hits.add(("get", a0.value))
    return hits


# --------------------------------------------------------------------------- #
# T1 — sole-entry shape only (extends 58d5a49)
# --------------------------------------------------------------------------- #

class TestSoleEntryShape(unittest.TestCase):

    def test_ingest_fanout_root_is_tormentfabric_ingest(self):
        ft = _tree("fabric.py")
        self.assertIsNotNone(_class(ft, "TormentFabric"), "TormentFabric not found")
        self.assertIsNotNone(_method(ft, "TormentFabric", "ingest"),
                             "ordinary ingest fan-out root TormentFabric.ingest not found")

    def test_no_memoryfabric_class(self):
        # Carry forward the 58d5a49 naming mapping: docs say "MemoryFabric.ingest";
        # the live class is TormentFabric. There is no MemoryFabric class.
        self.assertIsNone(_class(_tree("fabric.py"), "MemoryFabric"),
                          "unexpected MemoryFabric class — update the naming mapping")

    def test_negative_perimeter_sits_at_the_ingest_entry(self):
        # The first statement of the fan-out root is the type-only text refusal:
        # the negative perimeter sits AT the ingest entry, not deeper in the graph.
        ingest = _method(_tree("fabric.py"), "TormentFabric", "ingest")
        guard = ingest.body[0]
        self.assertIsInstance(guard, ast.If,
                              "ingest's first statement is not the candidate-refusal guard")
        self.assertTrue(_is_candidate_isinstance(guard.test),
                        "ingest's first guard is not isinstance(text, CandidateShapedValue)")
        self.assertIsInstance(guard.test.args[0], ast.Name)
        self.assertEqual(guard.test.args[0].id, "text")

    def test_candidate_perimeter_footprint_is_exactly_the_classified_five(self):
        # The only service modules referencing the inert candidate type are its
        # definition + the five landed refusal surfaces. A NEW referencing module
        # is an unclassified candidate-refusal/write surface => classify (gate
        # issue), do NOT patch production. This is the Seam B "new unclassified
        # write/fan-out surface fails the characterization" guard.
        bearing = set()
        for rel, _tree_ in _iter_service():
            if _CANDIDATE_TOKEN in _src_rel(rel):
                bearing.add(os.path.basename(rel))
        new = bearing - _CANDIDATE_FOOTPRINT_MODULES
        self.assertEqual(
            new, set(),
            msg=(f"NEW unclassified candidate-refusal/write module(s): {sorted(new)} "
                 f"— classify (gate issue); do NOT patch production"))
        missing = _CANDIDATE_FOOTPRINT_MODULES - bearing
        self.assertEqual(missing, set(),
                         msg=f"classified perimeter module(s) no longer present: {sorted(missing)}")

    def test_does_not_claim_wall_built_or_acceptance_under_a_producer(self):
        # Negative scope lock: this slice must not assert a live candidate producer,
        # governed admission, or promotion machinery exists. None of those tokens is
        # introduced as a live def/class anywhere in the service tree by this slice's
        # subject area (their absence is also locked by 2732f32 and T4 below).
        forbidden_live = ("CandidateProducer", "GovernedAdmission", "AdmissionCrossing",
                          "PromotionCrossing", "CandidateStore")
        present = []
        for rel, tree in _iter_service():
            for n in ast.walk(tree):
                if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    if n.name in forbidden_live:
                        present.append(f"{rel}::{n.name}")
        self.assertEqual(present, [],
                         msg=f"unexpected producer/admission/promotion machinery: {present}")


def _src_rel(rel):
    with open(os.path.join(_service_dir(), rel), "rb") as fh:
        return fh.read().replace(b"\x00", b"").decode("utf-8", "replace")


# --------------------------------------------------------------------------- #
# L4 — Layer-4 perimeter carry-forward (the five refusal surfaces stay shaped)
# --------------------------------------------------------------------------- #

class TestLayer4PerimeterCarryForward(unittest.TestCase):

    def _guards_for(self, basename):
        cls, meth, _params = _SEAM_B_SURFACES[basename]
        func = _method(_tree(basename), cls, meth)
        self.assertIsNotNone(func, f"{cls}.{meth} not found in {basename}")
        return func, _candidate_guards(func)

    def test_each_surface_guards_its_classified_params(self):
        for basename, (cls, meth, params) in _SEAM_B_SURFACES.items():
            _func, guards = self._guards_for(basename)
            guarded_names = {name for name, _node in guards if name is not None}
            missing = params - guarded_names
            self.assertEqual(
                missing, set(),
                msg=f"{cls}.{meth} no longer refuses candidate-shaped param(s): {sorted(missing)}")

    def test_guards_are_type_only_isinstance(self):
        # The guard test is EXACTLY isinstance(x, CandidateShapedValue): no Compare,
        # no BoolOp, no tag/marker/key/schema test mixed in (type-only, no schema policing).
        for basename in _SEAM_B_SURFACES:
            _func, guards = self._guards_for(basename)
            self.assertTrue(guards, f"{basename}: no candidate guard found")
            for _name, node in guards:
                self.assertTrue(_is_candidate_isinstance(node.test),
                                msg=f"{basename}: a candidate guard is not a type-only isinstance")
                self.assertNotIsInstance(node.test, (ast.BoolOp, ast.Compare))

    def test_guards_are_content_blind(self):
        # No attribute access, subscript, or `.get(...)` on the inspected value
        # inside the guard test => never reads contents / metadata / tags / payload
        # keys / provenance / markers.
        for basename in _SEAM_B_SURFACES:
            _func, guards = self._guards_for(basename)
            for _name, node in guards:
                for sub in ast.walk(node.test):
                    self.assertNotIsInstance(
                        sub, (ast.Attribute, ast.Subscript),
                        msg=f"{basename}: candidate guard test reads contents (attr/subscript)")

    def test_guard_body_is_single_contents_free_typeerror(self):
        # Single `raise TypeError("...")` with a constant message that never
        # interpolates the inspected value (no f-string, no Name of the value).
        for basename, (_cls, _meth, _params) in _SEAM_B_SURFACES.items():
            _func, guards = self._guards_for(basename)
            for name, node in guards:
                self.assertEqual(len(node.body), 1,
                                 msg=f"{basename}: candidate guard body is not a single statement")
                raise_node = node.body[0]
                self.assertIsInstance(raise_node, ast.Raise)
                self.assertIsInstance(raise_node.exc, ast.Call)
                self.assertIsInstance(raise_node.exc.func, ast.Name)
                self.assertEqual(raise_node.exc.func.id, "TypeError",
                                 msg=f"{basename}: candidate guard does not raise TypeError")
                for sub in ast.walk(raise_node):
                    self.assertNotIsInstance(
                        sub, ast.JoinedStr,
                        msg=f"{basename}: TypeError message must not be an f-string")
                    if isinstance(sub, ast.Name) and name is not None:
                        self.assertNotEqual(
                            sub.id, name,
                            msg=f"{basename}: TypeError message references the inspected value")

    def test_dict_value_scans_are_non_recursive_and_key_blind(self):
        # extra_payload / metadata immediate-value scans iterate `.values()` only
        # (key-blind), with no nested loop (non-recursive) and no key / subscript
        # access in the loop body.
        for basename, (cls, meth, param) in _IMMEDIATE_VALUE_PARAMS.items():
            func = _method(_tree(basename), cls, meth)
            value_loops = []
            for n in ast.walk(func):
                if (isinstance(n, ast.For)
                        and isinstance(n.iter, ast.Call)
                        and isinstance(n.iter.func, ast.Attribute)
                        and n.iter.func.attr == "values"
                        and isinstance(n.iter.func.value, ast.Name)
                        and n.iter.func.value.id == param):
                    value_loops.append(n)
            self.assertTrue(value_loops,
                            msg=f"{basename}: no `{param}.values()` immediate-value scan found")
            for loop in value_loops:
                # non-recursive: no nested For inside the values() loop body
                for sub in ast.walk(loop):
                    if sub is loop:
                        continue
                    self.assertNotIsInstance(
                        sub, ast.For, msg=f"{basename}: `{param}` value scan is recursive")
                # key-blind: the loop never iterates `.keys()` / `.items()` of the param
                self.assertNotIn("keys", _called_names(loop))
                self.assertNotIn("items", _called_names(loop))


# --------------------------------------------------------------------------- #
# T2 — no-tag-dependence (extends 8f8fa7a to the Seam B perimeter)
# --------------------------------------------------------------------------- #

class TestNoTagDependence(unittest.TestCase):

    def test_seam_b_surfaces_have_no_exclusion_tag_gate(self):
        offenders = {}
        for basename in _SEAM_B_SURFACES:
            hits = _gate_position_tags(_tree(basename))
            if hits:
                offenders[basename] = sorted(hits)
        self.assertEqual(
            offenders, {},
            msg=("Seam B surface gates on reflection-exclusion tag(s) "
                 f"(do NOT patch production — enforcement-path decision): {offenders}"))

    def test_candidate_guards_key_on_type_not_tags(self):
        # Each refusal guard branches on the candidate TYPE alone — never on an
        # exclusion tag, marker, provenance, or payload key. (Reinforces that
        # containment shape here is structural, not tag-honoring.)
        for basename in _SEAM_B_SURFACES:
            cls, meth, _params = _SEAM_B_SURFACES[basename]
            func = _method(_tree(basename), cls, meth)
            for _name, node in _candidate_guards(func):
                self.assertEqual(_gate_position_tags(node), set(),
                                 msg=f"{basename}: candidate guard references an exclusion tag")


# --------------------------------------------------------------------------- #
# T3 — inspection / non-reentry carry-forward (extends 0dbe7cc / c73add5)
# --------------------------------------------------------------------------- #

class TestInspectionNonReentryCarryForward(unittest.TestCase):

    def test_refusal_guards_reach_no_writer_prompt_retrieval_control_path(self):
        # The guards themselves only call isinstance / TypeError — they reach no
        # writer / prompt / retrieval / control path (refuse-and-stop, not a
        # projection or control surface).
        for basename in _SEAM_B_SURFACES:
            cls, meth, _params = _SEAM_B_SURFACES[basename]
            func = _method(_tree(basename), cls, meth)
            for _name, node in _candidate_guards(func):
                bad = _called_names(node) & _FORBIDDEN_GUARD_CALLS
                self.assertEqual(
                    bad, set(),
                    msg=f"{basename}: candidate guard reaches forbidden path(s): {sorted(bad)}")

    def test_candidate_perimeter_not_exposed_on_caller_visible_app_surface(self):
        # The inert candidate type and its module are not referenced by app.py:
        # the perimeter is an internal write-side refusal, not a caller-visible /
        # inspection / endpoint-schema surface (carry-forward of A-I1 inspection
        # ≠ projection).
        app_src = _src("app.py")
        self.assertNotIn(_CANDIDATE_TOKEN, app_src,
                         msg="app.py references the candidate type (caller-visible exposure)")
        self.assertNotIn("candidate_types", app_src,
                         msg="app.py imports candidate_types (caller-visible exposure)")

    def test_audit_packet_identifier_stays_non_control(self):
        # Carry-forward of the sealed audit posture: the audit packet identifier
        # stays confined to the runner sink + the unwired private owner; it is not
        # consumed by the Seam B perimeter or any new surface.
        refs = {os.path.basename(rel) for rel, tree in _iter_service()
                if "audit_evidence_packet" in _idents(tree)}
        self.assertEqual(
            refs, {"agent_loop.py", _OWNER_MODULE},
            msg=f"unexpected audit_evidence_packet references: {sorted(refs)}")


# --------------------------------------------------------------------------- #
# T4 — deliberation containment (extends 2732f32)
# --------------------------------------------------------------------------- #

class TestDeliberationContainment(unittest.TestCase):

    def test_candidate_type_footprint_excludes_every_deliberation_surface(self):
        # The candidate type is referenced only by its definition + the five
        # write-side refusal surfaces — NEVER by a deliberation / generation /
        # audit surface. So no contained / candidate value is an INPUT to
        # AgentRunner, /agent/query, the owner, the bridge, the sidecar, the
        # observer, or the evidence lane.
        deliberation = {
            "agent_loop.py", "app.py", "spine.py",
            "retrieval_assembler.py",
            _OWNER_MODULE, _BRIDGE_MODULE,
            "audit_evidence_sidecar.py", "audit_evidence_packet.py",
            "audit_evidence_context.py", "audit_prompt_inclusion_observation.py",
        }
        bearing = {os.path.basename(rel) for rel, _t in _iter_service()
                   if _CANDIDATE_TOKEN in _src_rel(rel)}
        leaked = deliberation & bearing
        self.assertEqual(
            leaked, set(),
            msg=f"candidate type referenced by deliberation/audit surface(s): {sorted(leaked)}")

    def test_private_owner_unwired_outside_tests(self):
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

    def test_selected_items_bridge_dead_end_outside_tests(self):
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

    def test_app_and_spine_have_no_agent_runner(self):
        for fname in ("app.py", "spine.py"):
            tree = _tree(fname)
            leaves, names = _import_leaves_names(tree)
            self.assertNotIn("agent_loop", leaves, f"{fname} imports agent_loop")
            self.assertNotIn("AgentRunner", names, f"{fname} imports AgentRunner")
            ids = _idents(tree)
            self.assertNotIn("AgentRunner", ids, f"{fname} references AgentRunner")
            self.assertNotIn("run_turn", ids, f"{fname} references run_turn")

    def test_agent_query_stays_advisory_not_a_generation_owner(self):
        q = None
        for n in _tree("app.py").body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "query":
                q = n
                break
        self.assertIsNotNone(q, "/agent/query handler not found")
        ids = _idents(q)
        for forbidden in ("run_turn", "AgentRunner", "complete"):
            self.assertNotIn(forbidden, ids,
                             msg=f"/agent/query became a generation owner via {forbidden}")


# --------------------------------------------------------------------------- #
# Postponed-surface classification — proof-scope dependency questions ONLY
# --------------------------------------------------------------------------- #

class TestPostponedSurfaceClassification(unittest.TestCase):
    """ArchiveStore / links / update_payload are classified ONLY as proof-scope
    dependency questions for the future sole-entry proof. This slice records that
    they exist and remain UNGUARDED (postponed) — it does NOT brick them, add
    guards, fix them, or claim them closed."""

    def test_archivestore_ingest_document_exists_and_is_unguarded(self):
        at = _tree("archive_memory.py")
        self.assertIsNotNone(_class(at, "ArchiveStore"), "ArchiveStore not found")
        self.assertIsNotNone(_method(at, "ArchiveStore", "ingest_document"),
                             "ArchiveStore.ingest_document not found")
        # Postponed (recorded, not closed): no candidate refusal here today.
        self.assertNotIn(_CANDIDATE_TOKEN, _src("archive_memory.py"),
                         msg="archive_memory grew a candidate guard — that would be a "
                             "second brick series; not authorized by this slice")

    def test_links_param_exists_and_is_unguarded(self):
        spawn = _method(_tree("memory_graph.py"), "MemoryGraph", "spawn_memory")
        arg_names = {a.arg for a in spawn.args.args} | {a.arg for a in spawn.args.kwonlyargs}
        self.assertIn("links", arg_names, "spawn_memory no longer has a `links` param")
        guarded = {name for name, _n in _candidate_guards(spawn)}
        self.assertNotIn("links", guarded,
                         msg="`links` grew a candidate guard — not authorized by this slice")

    def test_update_payload_exists_and_is_unguarded(self):
        up = _method(_tree("memory_graph.py"), "MemoryGraph", "update_payload")
        self.assertIsNotNone(up, "MemoryGraph.update_payload not found")
        self.assertEqual(_candidate_guards(up), [],
                         msg="update_payload grew a candidate guard — not authorized by this slice")

    def test_classification_is_recorded_for_each_postponed_surface(self):
        # Inventory cross-check: each classified postponed surface still lives where
        # we classified it (so the proof-scope dependency list stays accurate).
        self.assertEqual(sorted(_POSTPONED),
                         ["ArchiveStore.ingest_document",
                          "MemoryGraph.spawn_memory:links",
                          "MemoryGraph.update_payload"])
        for _target, (basename, _desc) in _POSTPONED.items():
            self.assertTrue(os.path.exists(os.path.join(_service_dir(), basename)),
                            msg=f"classified surface module missing: {basename}")


# --------------------------------------------------------------------------- #
# Framing — chokepoint terrain only; governed admission remains the future exit
# --------------------------------------------------------------------------- #

class TestScopeFraming(unittest.TestCase):

    def test_governed_admission_remains_the_legitimate_future_crossing(self):
        frame = _read_doc(
            "TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md").lower()
        self.assertIn("governed admission", frame)

    def test_authorization_review_scopes_this_slice_to_tier_1(self):
        review = _read_doc(
            "TORMENT_GATE_A_WALL_ENFORCEMENT_PATH_AUTHORIZATION_REVIEW_v0.1.md").lower()
        self.assertIn("seam b", review)
        self.assertIn("tier-1", review)


if __name__ == "__main__":
    unittest.main()
