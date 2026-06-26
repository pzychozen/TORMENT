"""Gate A — Seam C writer-authority risk: Tier-2 A-O2 producer-independent evidence.

Tests/source-only. Codex/operator-authorized as a CHARACTERIZATION pass only (see
``docs/TORMENT_GATE_A_WALL_ENFORCEMENT_PATH_AUTHORIZATION_REVIEW_v0.1.md``: Seam C
is routed to Gate B and parked; A-O2 is Tier-2 T8). This file is *evidence*, not
enforcement: it pins and classifies the four parked direct-writer hazards as the
A-O2 subject set and locks a "no NEW unclassified canon/identity writer" inventory
guard. It fixes nothing, blesses nothing, ranks nothing.

A-O2 (Document A): "no silent canon / identity-tier / seed / long-half-life writes
from cognition / reflection paths." The full A-O2 proof *against a live candidate
producer* is Tier-2 and DEFERRED (no producer exists / is authorized). What is
producer-independent — and all this file does — is to characterize that today's
canon/identity writers are a KNOWN, CLASSIFIED set, that the two derived-cognition
emitters write `canon=False`, and that a new unclassified canon/identity writer
trips a guard.

Cross-walk — Gate B Writer-Authority Hazard Inventory (H1-H4) == Gate A Seam C /
A-O2 Tier-2 evidence subjects:

  * H1  `gravity_correction` automatic `canon=True`
        -> character.py::gravity_correction (drift_correction, core_identity),
           reached from TormentFabric.ingest periodic drift check.
  * H2  `_maybe_emit_identity_anchor` derived identity writer (`canon=False`)
        -> fabric.py::_maybe_emit_identity_anchor (identity_anchor, derived).
  * H3  `POST /promote` force bypass (`canon=True`)
        -> app.py::promote_chunk_endpoint force route -> promotion.py::promote_chunk
           (identity / canon_promotion).
  * H4  `mood_drift -> canon` (topology only)
        -> fabric.py::_maybe_emit_mood_drift (mood_drift, `canon=False`) is eligible
           input to character.py::measure_drift (excludes only seed_canon), which
           gates H1. Topology/eligibility only — NO causal or magnitude claim.

Mirrors the structure/helpers of:
  * tests/test_gate_a_seam_b_ingest_entry_characterization.py (pure-AST helpers,
    classification dicts, doc-reading framing).
  * tests/test_gate_a_wall_ingest_fanout_root_inventory.py (allowlist /
    "fail only on a new unclassified surface" style).

Constraints honored: source-only / AST-only; no production import; no runtime
execution; no production code; no docs edits; no Gate A wall-completion claim; no
Gate D; no Gate B implementation; no writer fix; no candidate producer / store /
carrier / schema / field / API / runtime wiring; no governed admission / promotion;
no database / substrate; no endpoint / API / schema expansion; no recursive /
content / tag / provenance / key filtering; audit/inspection is not turned into
control. If any guard fails, do NOT patch production — return it as a gate decision.
"""

import ast
import os
import unittest


_MISSING = object()

# Modules scanned for canon=True writer sites.
_CANON_SCAN_MODULES = ("fabric.py", "character.py", "promotion.py", "memory_graph.py")

# Classified canon=True writer classes (each rule keys on a write-call keyword
# Constant). A canon=True write that matches NONE of these is unclassified and
# trips the inventory guard for re-inventory (gate decision; do NOT patch).
_CANON_CLASS_RULES = (
    ("mtype", "drift_correction", "drift_correction"),   # H1 gravity_correction
    ("mtype", "seed_canon", "seed_canon"),               # authored seed plant
    ("user_id", "promotion_system", "canon_promotion"),  # H3 promote_chunk writer
    ("user_id", "collective", "shared_collective"),      # shared/collective canon
)
_ALLOWED_CANON_CLASSES = frozenset(
    {"drift_correction", "seed_canon", "canon_promotion", "shared_collective"})

# Derived-cognition emitters that must NOT write canon=True (A-O2 evidence).
_DERIVED_COGNITION_EMITTERS = ("_maybe_emit_identity_anchor", "_maybe_emit_mood_drift")


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


def _func(tree, name):
    """First FunctionDef/AsyncFunctionDef with this name (method or top-level)."""
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
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


def _attrs(node):
    return {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}


def _string_consts(node):
    return {n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def _calls(node, names):
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            fid = (f.id if isinstance(f, ast.Name)
                   else f.attr if isinstance(f, ast.Attribute) else None)
            if fid in names:
                out.append(n)
    return out


def _kw(call, name):
    for k in call.keywords:
        if k.arg == name:
            return k.value
    return None


def _kw_const(call, name):
    v = _kw(call, name)
    return v.value if isinstance(v, ast.Constant) else _MISSING


def _has_canon_true(call):
    v = _kw(call, "canon")
    return isinstance(v, ast.Constant) and v.value is True


def _has_any_canon_true(func):
    return any(_has_canon_true(c) for c in _calls(func, {"spawn_memory", "add_memory"}))


def _dict_pairs(node):
    """{(key, value)} for string-keyed, constant-valued entries of a Dict literal."""
    pairs = set()
    if isinstance(node, ast.Dict):
        for k, val in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant) and isinstance(val, ast.Constant)):
                pairs.add((k.value, val.value))
    return pairs


def _write_call(func, mtype):
    """The spawn_memory/add_memory call in `func` whose mtype== the given constant."""
    for c in _calls(func, {"spawn_memory", "add_memory"}):
        if _kw_const(c, "mtype") == mtype:
            return c
    return None


def _classify_canon_call(call):
    mt = _kw_const(call, "mtype")
    uid = _kw_const(call, "user_id")
    for key, val, cls in _CANON_CLASS_RULES:
        if key == "mtype" and mt == val:
            return cls
        if key == "user_id" and uid == val:
            return cls
    return None


# --------------------------------------------------------------------------- #
# A — H1: gravity_correction automatic canon=True (core_identity)
# --------------------------------------------------------------------------- #

class TestH1GravityCorrectionCanonWriter(unittest.TestCase):

    def setUp(self):
        self.char = _tree("character.py")
        self.gc = _func(self.char, "gravity_correction")

    def test_gravity_correction_exists(self):
        self.assertIsNotNone(self.gc, "character.py::gravity_correction not found")

    def test_writes_drift_correction_canon_true(self):
        w = _write_call(self.gc, "drift_correction")
        self.assertIsNotNone(w, "gravity_correction has no mtype='drift_correction' write")
        self.assertTrue(_has_canon_true(w),
                        "gravity_correction drift_correction write is not canon=True")

    def test_carries_core_identity_tier(self):
        w = _write_call(self.gc, "drift_correction")
        self.assertIn(("tier", "core_identity"), _dict_pairs(_kw(w, "extra_payload")),
                      "gravity_correction write does not carry tier='core_identity'")

    def test_reachable_from_ingest(self):
        ingest = _func(_tree("fabric.py"), "ingest")
        self.assertIsNotNone(ingest, "TormentFabric.ingest not found")
        self.assertIn("gravity_correction", _called_names(ingest),
                      "gravity_correction not reached from TormentFabric.ingest")


# --------------------------------------------------------------------------- #
# B — H2: _maybe_emit_identity_anchor derived identity writer (canon=False)
# --------------------------------------------------------------------------- #

class TestH2IdentityAnchorDerivedWriter(unittest.TestCase):

    def setUp(self):
        self.fabric = _tree("fabric.py")
        self.ia = _func(self.fabric, "_maybe_emit_identity_anchor")

    def test_identity_anchor_emitter_exists(self):
        self.assertIsNotNone(self.ia, "fabric.py::_maybe_emit_identity_anchor not found")

    def test_writes_identity_anchor_canon_false(self):
        w = _write_call(self.ia, "identity_anchor")
        self.assertIsNotNone(w, "no mtype='identity_anchor' write found")
        canon = _kw(w, "canon")
        self.assertTrue(isinstance(canon, ast.Constant) and canon.value is False,
                        "identity_anchor write is not canon=False")

    def test_carries_derived_provenance(self):
        w = _write_call(self.ia, "identity_anchor")
        pairs = _dict_pairs(_kw(w, "extra_payload"))
        for expected in (("anchor_origin", "derived"),
                         ("anchor_source", "motif_cluster"),
                         ("scope", "private")):
            self.assertIn(expected, pairs,
                          msg=f"identity_anchor write missing provenance {expected}")

    def test_contains_no_canon_true(self):
        self.assertFalse(_has_any_canon_true(self.ia),
                         "_maybe_emit_identity_anchor unexpectedly emits canon=True")

    def test_reachable_from_ingest(self):
        ingest = _func(self.fabric, "ingest")
        self.assertIn("_maybe_emit_identity_anchor", _called_names(ingest),
                      "_maybe_emit_identity_anchor not reached from TormentFabric.ingest")


# --------------------------------------------------------------------------- #
# C — H3: /promote force bypass -> promote_chunk canon=True
# --------------------------------------------------------------------------- #

class TestH3PromoteForceBypass(unittest.TestCase):

    def setUp(self):
        self.app = _tree("app.py")
        self.endpoint = _func(self.app, "promote_chunk_endpoint")

    def test_promotereq_force_defaults_false(self):
        pr = _class(self.app, "PromoteReq")
        self.assertIsNotNone(pr, "PromoteReq not found")
        force_default = _MISSING
        for stmt in pr.body:
            if (isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
                    and stmt.target.id == "force"):
                force_default = (stmt.value.value
                                 if isinstance(stmt.value, ast.Constant) else _MISSING)
        self.assertIs(force_default, False, "PromoteReq.force does not default to False")

    def test_force_preloads_is_canon_and_user_approved(self):
        self.assertIsNotNone(self.endpoint, "promote_chunk_endpoint not found")
        ev = _calls(self.endpoint, {"evaluate_promotion"})
        self.assertTrue(ev, "promote_chunk_endpoint does not call evaluate_promotion")
        call = ev[0]
        for kwname in ("is_canon", "user_approved"):
            val = _kw(call, kwname)
            self.assertIsNotNone(val, f"evaluate_promotion missing {kwname}")
            self.assertTrue(
                any(isinstance(s, ast.Attribute) and s.attr == "force"
                    for s in ast.walk(val)),
                msg=f"{kwname} is not derived from req.force")

    def test_execution_guard_references_promote_and_force(self):
        found = False
        for n in ast.walk(self.endpoint):
            if isinstance(n, ast.If) and isinstance(n.test, ast.BoolOp):
                a = _attrs(n.test)
                if {"promote", "force"} <= a:
                    found = True
        self.assertTrue(
            found, "no `if result.promote or req.force:`-style guard found in endpoint")

    def test_promote_chunk_writes_canon_promotion(self):
        pc = _func(_tree("promotion.py"), "promote_chunk")
        self.assertIsNotNone(pc, "promotion.py::promote_chunk not found")
        w = _write_call(pc, "identity")
        self.assertIsNotNone(w, "promote_chunk has no mtype='identity' write")
        self.assertTrue(_has_canon_true(w), "promote_chunk identity write is not canon=True")
        self.assertIn("canon_promotion", _string_consts(pc),
                      "promote_chunk does not mark kind='canon_promotion'")

    def test_force_route_provenance_is_provenance_only(self):
        # The provenance stamps exist, but characterize them as provenance-only:
        # they are not consumed by any branch in the endpoint (drive no control).
        # (Behavior/provenance correctness is covered by the existing H3 provenance
        # tests; this only locks the non-control posture.)
        stamps = {"promotion_force_requested", "promotion_evaluator_promote"}
        self.assertTrue(stamps <= _string_consts(self.endpoint),
                        "force-route provenance stamps missing")
        for n in ast.walk(self.endpoint):
            if isinstance(n, (ast.If, ast.While, ast.IfExp)):
                self.assertEqual(
                    _string_consts(n.test) & stamps, set(),
                    msg="force-route provenance stamp drives a control branch")


# --------------------------------------------------------------------------- #
# D — H4: mood_drift -> canon topology (eligibility only)
# --------------------------------------------------------------------------- #

class TestH4MoodDriftTopology(unittest.TestCase):

    def setUp(self):
        self.fabric = _tree("fabric.py")
        self.char = _tree("character.py")
        self.md = _func(self.fabric, "_maybe_emit_mood_drift")

    def test_mood_drift_emitter_exists(self):
        self.assertIsNotNone(self.md, "fabric.py::_maybe_emit_mood_drift not found")

    def test_emits_mood_drift_canon_false(self):
        w = _write_call(self.md, "mood_drift")
        self.assertIsNotNone(w, "no mtype='mood_drift' write found")
        canon = _kw(w, "canon")
        self.assertTrue(isinstance(canon, ast.Constant) and canon.value is False,
                        "mood_drift write is not canon=False")

    def test_contains_no_canon_true(self):
        self.assertFalse(_has_any_canon_true(self.md),
                         "_maybe_emit_mood_drift unexpectedly emits canon=True "
                         "(the '-> canon' link is indirect/topology only)")

    def test_measure_drift_excludes_only_seed_canon(self):
        mdrift = _func(self.char, "measure_drift")
        self.assertIsNotNone(mdrift, "character.py::measure_drift not found")
        consts = _string_consts(mdrift)
        self.assertIn("seed_canon", consts,
                      "measure_drift does not reference the seed_canon exclusion")
        # 'excludes ONLY seed_canon' => mood_drift / identity_anchor are NOT excluded
        # (they remain eligible centroid inputs). Topology, not causality.
        for not_excluded in ("mood_drift", "identity_anchor"):
            self.assertNotIn(not_excluded, consts,
                             msg=f"measure_drift unexpectedly references {not_excluded}")

    def test_both_mood_drift_and_gravity_path_reachable_from_ingest(self):
        ingest = _func(self.fabric, "ingest")
        called = _called_names(ingest)
        self.assertIn("_maybe_emit_mood_drift", called,
                      "_maybe_emit_mood_drift not reached from ingest")
        self.assertIn("gravity_correction", called,
                      "gravity path not reached from ingest")


# --------------------------------------------------------------------------- #
# E — inventory guard: no NEW unclassified canon/identity writer
# --------------------------------------------------------------------------- #

class TestCanonWriterInventoryGuard(unittest.TestCase):

    def _discover(self):
        found = []
        for mod in _CANON_SCAN_MODULES:
            for c in _calls(_tree(mod), {"spawn_memory", "add_memory"}):
                if _has_canon_true(c):
                    found.append((mod, getattr(c, "lineno", -1), _classify_canon_call(c)))
        return found

    def test_every_canon_true_write_is_classified(self):
        discovered = self._discover()
        self.assertTrue(discovered, "no canon=True writer sites discovered (re-inventory)")
        unclassified = [(m, ln) for (m, ln, cls) in discovered if cls is None]
        self.assertEqual(
            unclassified, [],
            msg=("NEW unclassified canon/identity writer site(s): "
                 f"{unclassified} — classify (gate decision); do NOT patch production"))

    def test_discovered_classes_within_allowlist(self):
        classes = {cls for (_m, _ln, cls) in self._discover() if cls is not None}
        extra = classes - _ALLOWED_CANON_CLASSES
        self.assertEqual(extra, set(),
                         msg=f"canon writer class outside the allowlist: {sorted(extra)}")
        # The two canon hazards (H1 / H3) remain accounted within the inventory.
        self.assertIn("drift_correction", classes, "H1 canon writer missing from inventory")
        self.assertIn("canon_promotion", classes, "H3 canon writer missing from inventory")

    def test_derived_cognition_emitters_emit_no_canon_true(self):
        fabric = _tree("fabric.py")
        for name in _DERIVED_COGNITION_EMITTERS:
            fn = _func(fabric, name)
            self.assertIsNotNone(fn, f"{name} not found")
            self.assertFalse(_has_any_canon_true(fn),
                             msg=f"derived cognition emitter {name} emits canon=True")


# --------------------------------------------------------------------------- #
# F — framing: cross-walk anchored in existing docs (doc-reading only)
# --------------------------------------------------------------------------- #

class TestFramingCrossWalk(unittest.TestCase):

    def test_gate_b_inventory_names_h1_through_h4(self):
        doc = _read_doc("TORMENT_GATE_B_WRITER_AUTHORITY_HAZARD_INVENTORY_v0.1.md").lower()
        for hid in ("h1 —", "h2 —", "h3 —", "h4 —"):
            self.assertIn(hid, doc, msg=f"Gate B inventory no longer names {hid!r}")
        for symbol in ("gravity_correction", "_maybe_emit_identity_anchor",
                       "/promote", "mood_drift"):
            self.assertIn(symbol, doc, msg=f"Gate B inventory no longer names {symbol}")

    def test_authorization_review_routes_seam_c_ao2_tier2(self):
        doc = _read_doc(
            "TORMENT_GATE_A_WALL_ENFORCEMENT_PATH_AUTHORIZATION_REVIEW_v0.1.md").lower()
        for token in ("seam c", "a-o2", "tier-2"):
            self.assertIn(token, doc,
                          msg=f"authorization review no longer routes {token!r}")


if __name__ == "__main__":
    unittest.main()
