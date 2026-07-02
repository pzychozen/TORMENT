"""Tests-only / source-only characterization: P4 O1/O2/O5 source-sameness
READINESS seams (substrate-independent, no P4 mechanics implemented).

Complements — and does NOT duplicate —
``tests/test_audit_read_side_projection_safety_noncoercion_characterization.py``,
which locks the P4 O3/O4 (projection / non-coercion) subset and EXPLICITLY defers
O1/O2 source-sameness / source-membership, carriers, and substrate. This file
characterizes only that missing readiness terrain: what the current read /
derive / mutate seams actually do today (presence / entity-existence based), so a
later P4 source-sameness reader policy has a source-grounded starting point.

Doctrine (carried, exact):
    Memory may shape context. Memory may not seize authority.
    Audit observes authority. Audit must not become authority.

What this file locks (readiness / absence only — NO mechanics):
  * ``_query_deep_lane`` is DeepMemoryEcho terrain gated by SOURCE-ROW PRESENCE /
    entity existence (orphan filtering against the private graph), NOT by any
    source-sameness conformance check.
  * ``_maybe_emit_identity_anchor`` derives an identity anchor from MOTIF-MEMBER
    PRESENCE (member eids present in the agent graph, count threshold), NOT from
    source-membership sameness conformance.
  * ``MemoryGraph.update_payload`` is same-eid payload mutation + nodes.jsonl
    reappend (loader treats the last record as canonical) — the terrain that a
    later reader trace / source-sameness (O1/O2) + committed-record (O5) policy
    would have to govern; no such policy exists here today.
  * NO runtime ``ReaderPolicy`` / ``source_sameness`` / ``source_membership`` /
    ``diagnostic_only`` gate / source fingerprint / source token / projection-
    eligibility mechanism is implemented in production source.
  * The existing O3/O4 characterization explicitly defers O1/O2 (so this file is
    the complement, not a duplicate).

Out of scope / NOT asserted satisfied here (readiness only): P4 O1/O2 runtime
enforcement, carrier / candidate store / schema / substrate, admission /
promotion, Gate D / Envelope-Audit / Document B chamber runtime, Dream / Regime-B
runtime, writer path, retrieval feedback, persistence changes, AgentRunner /
app / spine / MCP wiring, model/provider/API/prompt path.
"""

import ast
import os
import unittest


# --------------------------------------------------------------------------- #
# Source / AST helpers (mirrors the O3/O4 characterization file's style)
# --------------------------------------------------------------------------- #

def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _tests_dir():
    return os.path.join(_repo_root(), "tests")


def _read(path):
    with open(path, "rb") as fh:
        return fh.read().replace(b"\x00", b"").decode("utf-8-sig")


def _src(filename, base=None):
    return _read(os.path.join(base or _service_dir(), filename))


def _tree_and_src(filename, base=None):
    text = _src(filename, base=base)
    return ast.parse(text), text


def _find_func(tree, name):
    """First FunctionDef/AsyncFunctionDef with `name` anywhere in the tree
    (handles methods nested inside classes)."""
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _seg(text, node):
    return ast.get_source_segment(text, node) or ""


def _prod_trees():
    out = []
    root = _service_dir()
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            if fn.endswith(".py"):
                p = os.path.join(dp, fn)
                out.append((os.path.relpath(p, _repo_root()), ast.parse(_read(p))))
    return out


# P4 source-sameness / reader-policy mechanic IDENTIFIER tokens. Matched against
# real identifier names (class/def/name/attr/arg), NOT raw text, so a docstring
# or comment mention would not false-positive.
_P4_MECHANIC_TOKENS = (
    "source_sameness",
    "source_membership",
    "readerpolicy",
    "diagnostic_only",
    "source_fingerprint",
    "source_token",
    "projection_eligibility",
)


def _identifier_hits(tree):
    hits = set()
    for n in ast.walk(tree):
        nm = None
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            nm = n.name
        elif isinstance(n, ast.Name):
            nm = n.id
        elif isinstance(n, ast.Attribute):
            nm = n.attr
        elif isinstance(n, ast.arg):
            nm = n.arg
        elif isinstance(n, ast.keyword) and n.arg:
            nm = n.arg
        if nm:
            low = nm.lower()
            if any(tok in low for tok in _P4_MECHANIC_TOKENS):
                hits.add(nm)
    return hits


# --------------------------------------------------------------------------- #
# 1. _query_deep_lane: DeepMemoryEcho terrain by source-row PRESENCE, not sameness
# --------------------------------------------------------------------------- #

class TestDeepLaneSourceRowPresenceTerrain(unittest.TestCase):
    def setUp(self):
        self.tree, self.text = _tree_and_src("fabric.py")
        self.fn = _find_func(self.tree, "_query_deep_lane")
        self.assertIsNotNone(self.fn, "_query_deep_lane not found in fabric.py")
        self.body = _seg(self.text, self.fn)

    def test_is_deep_memory_echo_terrain(self):
        # DeepMemoryEcho terrain: reads a deep store and stamps deep-scope hits.
        self.assertIn("_deep_store", self.body)
        self.assertIn("from_deep_memory", self.body)
        self.assertIn('scope="deep"', self.body)

    def test_gated_by_source_row_presence_entity_existence(self):
        # Orphan filtering is source-ROW PRESENCE / entity existence against the
        # private graph — not a source-sameness conformance check.
        self.assertIn("private_graphs", self.body)
        self.assertIn("entities", self.body)

    def test_no_source_sameness_conformance_in_deep_lane(self):
        hits = _identifier_hits(ast.parse(self.body))
        self.assertEqual(hits, set(),
                         f"_query_deep_lane already carries P4 sameness mechanics: {sorted(hits)}")


# --------------------------------------------------------------------------- #
# 2. _maybe_emit_identity_anchor: motif-member PRESENCE, not membership-sameness
# --------------------------------------------------------------------------- #

class TestIdentityAnchorMotifPresenceTerrain(unittest.TestCase):
    def setUp(self):
        self.tree, self.text = _tree_and_src("fabric.py")
        self.fn = _find_func(self.tree, "_maybe_emit_identity_anchor")
        self.assertIsNotNone(self.fn, "_maybe_emit_identity_anchor not found")
        self.body = _seg(self.text, self.fn)

    def test_derived_from_motif_member_presence(self):
        # Presence-based membership: member eids that are present in the agent's
        # own graph, gated by a recurrence-count threshold.
        self.assertIn("motif_ids", self.body)
        self.assertIn("members", self.body)
        self.assertIn("entities", self.body)
        self.assertIn("min_count", self.body)

    def test_emits_derived_identity_anchor(self):
        self.assertIn("identity_anchor", self.body)

    def test_no_source_membership_sameness_conformance(self):
        hits = _identifier_hits(ast.parse(self.body))
        self.assertEqual(hits, set(),
                         f"_maybe_emit_identity_anchor already carries sameness mechanics: {sorted(hits)}")


# --------------------------------------------------------------------------- #
# 3. MemoryGraph.update_payload: same-eid mutation + reappend (O1/O2 + O5 terrain)
# --------------------------------------------------------------------------- #

class TestUpdatePayloadSameEidReappendTerrain(unittest.TestCase):
    def setUp(self):
        self.tree, self.text = _tree_and_src("memory_graph.py")
        self.fn = _find_func(self.tree, "update_payload")
        self.assertIsNotNone(self.fn, "update_payload not found in memory_graph.py")
        self.body = _seg(self.text, self.fn)

    def test_mutates_same_eid_payload(self):
        # Same eid, in place: requires the eid to already exist, then updates its
        # payload (no new eid, no source distinction created).
        self.assertIn("self.entities", self.body)
        self.assertIn("payload", self.body)
        self.assertRegex(self.body, r"payload\.update|payload = dict\(patch\)")

    def test_reappends_canonical_last_record(self):
        # Reappend terrain: a new jsonl record is appended and the loader treats
        # the last record as canonical — the committed-record (O5) + reader-trace
        # (O1/O2) surface a later source-sameness policy would have to govern.
        self.assertIn("_append_jsonl", self.body)
        self.assertRegex(self.body.lower(), r"nodes\.jsonl|canonical")

    def test_no_source_sameness_policy_present_today(self):
        hits = _identifier_hits(ast.parse(self.body))
        self.assertEqual(hits, set(),
                         f"update_payload already carries a source-sameness policy: {sorted(hits)}")


# --------------------------------------------------------------------------- #
# 4. No runtime P4 source-sameness / reader-policy mechanics in production
# --------------------------------------------------------------------------- #

class TestNoRuntimeP4Mechanics(unittest.TestCase):
    def test_no_p4_mechanic_identifier_in_production(self):
        offenders = {}
        for rel, tree in _prod_trees():
            hits = _identifier_hits(tree)
            if hits:
                offenders[rel] = sorted(hits)
        self.assertEqual(
            offenders, {},
            f"production already implements a P4 source-sameness / reader-policy "
            f"mechanic (readiness-only expected): {offenders}",
        )


# --------------------------------------------------------------------------- #
# 5. Complement, not duplicate: the O3/O4 file explicitly defers O1/O2
# --------------------------------------------------------------------------- #

class TestComplementsNotDuplicatesO3O4(unittest.TestCase):
    def setUp(self):
        self.o34 = _src(
            "test_audit_read_side_projection_safety_noncoercion_characterization.py",
            base=_tests_dir(),
        )

    def test_existing_o3_o4_file_defers_o1_o2_source_sameness(self):
        low = self.o34.lower()
        self.assertIn("o3/o4", low)
        self.assertIn("o1/o2", low)
        self.assertIn("source-sameness", low)
        self.assertIn("deferred", low)

    def test_existing_o3_o4_file_has_deferred_scope_boundary(self):
        # The concrete deferral test exists there — so O1/O2 readiness is genuinely
        # uncovered until this file, not double-locked.
        self.assertIn("test_p4_contract_keeps_o1_o2_source_sameness_carrier_dependent", self.o34)


# --------------------------------------------------------------------------- #
# 6. Teeth — the detector catches real P4 mechanic identifiers, not benign shape
# --------------------------------------------------------------------------- #

class TestMatcherHasTeeth(unittest.TestCase):
    def test_flags_synthetic_p4_mechanics(self):
        snippet = (
            "class ReaderPolicy:\n"
            "    pass\n"
            "def check_source_sameness(row, other):\n"
            "    return row.source_fingerprint == other.source_token\n"
            "def project(x):\n"
            "    diagnostic_only = True\n"
            "    return diagnostic_only\n"
        )
        hits = {h.lower() for h in _identifier_hits(ast.parse(snippet))}
        self.assertIn("readerpolicy", hits)
        self.assertIn("check_source_sameness", hits)
        self.assertIn("source_fingerprint", hits)
        self.assertIn("source_token", hits)
        self.assertIn("diagnostic_only", hits)

    def test_benign_presence_shape_not_flagged(self):
        # A deep-lane-style presence/existence check carries no P4 sameness token.
        benign = (
            "def _query_deep_lane_like(self, ak, q):\n"
            "    store = self._deep_stores.get(ak)\n"
            "    if store is None:\n"
            "        return []\n"
            "    pg = self.private_graphs.get(ak)\n"
            "    return [h for h in store.query(q) if int(h['eid']) in pg.entities]\n"
        )
        self.assertEqual(_identifier_hits(ast.parse(benign)), set())


if __name__ == "__main__":
    unittest.main()
