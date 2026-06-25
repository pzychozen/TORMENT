"""Tests-only / source-only no-tag-dependence characterization for the Gate A /
Document A containment wall (A-C2).

A-C2 requires that containment hold **by construction**, not by every downstream
reader/writer remembering to honor an exclusion tag (the `ws_section_2a_v1`
lesson: once material enters the ordinary fan-out, auto-emitted identity pressure
can occur even when the material was not intended as identity-bearing).

This file records the CURRENT resting state: no live fan-out root branches,
filters, early-returns, routes, promotes, projects, writes, or suppresses based on
a reflection-exclusion / reflection-source tag. Today's non-reachability holds by
**absence-of-producer and unwired topology** (already characterized in
`test_gate_a_containment_wall_nonreachability_characterization.py`), not by a
honored exclusion tag.

This is a resting-state characterization, NOT a ban on a future *governed*
Document B containment/admission mechanism: governed admission (Document A A-O3)
remains the legitimate future crossing. The next substantive gate is the wall
enforcement-path authorization — not more wall mechanics by implication.

Scope discipline:
  * Matches the exact reflection-exclusion / source tags only, and only in
    **gate positions** (identifier / attribute / keyword arg / dict key /
    subscript key / `.get(...)` key) — not as raw substrings.
  * Explicitly does NOT match the overloaded, unrelated `admit` / `admitted` /
    `admission` vocabulary (migration gate2 admission, deep/core admission,
    `audit_admitted_context_items`, `selected_admitted_items`).

Does NOT assert: no future wall mechanism; admission-sole-exit; staging/promotion
bars; zero raw occurrences of any word; or any production safety beyond the scoped
source topology.

If this test ever fails (a live fan-out path gates on one of these tags), do NOT
patch production — return for an enforcement-path decision.
"""

import ast
import os
import unittest


# Exact reflection-exclusion / reflection-source tags (gate-position match only).
# NB: deliberately excludes admit / admitted / admission and the audit-item names.
_EXCLUSION_TAGS = frozenset({
    "unadmitted",
    "from_reflection",
    "is_reflection",
    "reflection_candidate",
    "contained",
    "exclude_from_cognition",
    "do_not_admit",
})

# Live fan-out roots + advisory/query/projection + the sealed audit edge.
_FANOUT_SURFACES = (
    "app.py",
    "spine.py",
    "fabric.py",
    "retrieval_assembler.py",
    "agent_loop.py",
    "thinking_controller.py",
    "audit_private_generation_owner.py",
    "audit_selected_items_runner_bridge.py",
)

_OWNER_MODULE = "audit_private_generation_owner.py"
_BRIDGE_MODULE = "audit_selected_items_runner_bridge.py"
_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}


# --------------------------------------------------------------------------- #
# Helpers
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


def _gate_position_tags(tree):
    """Return {(kind, tag)} for any exclusion tag used in a GATE position:
    identifier, attribute, keyword arg, dict key, subscript key, or `.get(...)`
    key. (Gate positions are the ones a branch/filter/route would key on; raw
    string occurrences in comments/docstrings are intentionally ignored.)"""
    hits = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            if n.id in _EXCLUSION_TAGS:
                hits.add(("name", n.id))
        elif isinstance(n, ast.Attribute):
            if n.attr in _EXCLUSION_TAGS:
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


def _called_names(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


# --------------------------------------------------------------------------- #
# P1 / P2 — fan-out roots and live paths do not gate on exclusion tags
# --------------------------------------------------------------------------- #

class TestFanoutDoesNotGateOnExclusionTags(unittest.TestCase):

    def test_named_fanout_surfaces_have_no_exclusion_tag_gate(self):
        offenders = {}
        for fname in _FANOUT_SURFACES:
            hits = _gate_position_tags(_service_tree(fname))
            if hits:
                offenders[fname] = sorted(hits)
        self.assertEqual(
            offenders, {},
            msg=("fan-out surface gates on reflection-exclusion tag(s) "
                 f"(do NOT patch production — enforcement-path decision): {offenders}"))

    def test_no_service_module_gates_on_exclusion_tag(self):
        offenders = {}
        for rel, tree in _iter_service():
            hits = _gate_position_tags(tree)
            if hits:
                offenders[rel] = sorted(hits)
        self.assertEqual(
            offenders, {},
            msg=f"service module gates on reflection-exclusion tag(s): {offenders}")


# --------------------------------------------------------------------------- #
# P3 — owner / bridge non-reachable by UNWIRED TOPOLOGY, not tag filtering
# --------------------------------------------------------------------------- #

class TestOwnerBridgeUnwiredNotTagFiltered(unittest.TestCase):

    def test_private_owner_unwired_by_topology(self):
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

    def test_selected_items_bridge_dead_end_by_topology(self):
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

    def test_owner_and_bridge_do_not_gate_on_exclusion_tags(self):
        # Their non-reachability is topological (unwired), not tag-filtered.
        for fname in (_OWNER_MODULE, _BRIDGE_MODULE):
            self.assertEqual(_gate_position_tags(_service_tree(fname)), set(),
                             msg=f"{fname} gates on a reflection-exclusion tag")


# --------------------------------------------------------------------------- #
# Framing — resting state, not a permanent ban on governed Document B
# --------------------------------------------------------------------------- #

class TestRestingStateNotPermanentBan(unittest.TestCase):

    def test_governed_admission_remains_legitimate_future_path(self):
        frame = _read(os.path.join(
            _docs_dir(),
            "TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md")).lower()
        self.assertIn("governed admission", frame)


if __name__ == "__main__":
    unittest.main()
