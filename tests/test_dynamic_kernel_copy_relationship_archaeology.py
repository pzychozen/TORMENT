"""tests/test_dynamic_kernel_copy_relationship_archaeology.py

Tests-only ARCHAEOLOGY (phase 2) — dynamic-kernel / chirality COPY RELATIONSHIP MAP.

Four copies of the TriOcta dynamic-kernel primitives survive in the tree. This
file characterizes their relationship **statically** (file presence + AST symbol
surfaces + token presence + CRLF-normalized content hashes) so a later
reconstruction decision frame is grounded — WITHOUT selecting a canonical source,
without ranking the copies, and without reconstructing any lost simulation.

Copies inspected (read-only, no sibling runtime executed):
  - production:        torment_fabric/torment_service/kernel/
  - v4.0:              v4.0/
  - epistemic_kernel:  epistemic_kernel/kernel/
  - zenodo:            Zenodo_research/tri_octagon_Model/17766958/

Ground-truth relationship this file pins (observed, not chosen):
  * `model_core.py` exists in ALL four copies, but every copy's body differs
    (four distinct content hashes) — they DIVERGE; no copy is declared canonical.
  * `seed_entities.py` (SeedWorld / SeedEntity) is byte-identical across
    {production, v4.0, epistemic_kernel} and ABSENT in zenodo.
  * `identity_rules.py` is byte-identical across all four.
  * The shared CLASS / METHOD surface (ModelParams, ModelState,
    TriOctaPhaseLockModel.{phase_lock_step, advance_phi, update_z,
    update_cycle_stage, update_identity_state, step, run}) is present in all four.
  * The chirality-MEMORY primitive (`z_mem` + `jeff` EMA, the surface the lost
    sims used) survives ONLY in {production, epistemic_kernel}. v4.0 keeps the
    `Z_chiral` vector but not the `z_mem`/`jeff` memory; zenodo has neither.

This is a MAP, not a decision. It infers no lost simulation mechanics, selects no
canonical copy, and begins no reconstruction.

Scope: tests-only. No production change. No sibling-copy edits. No runtime,
provider, persistence, or generated output. Pure static reads.
"""
from __future__ import annotations

import ast
import hashlib
import unittest
from pathlib import Path

# parents[2] == TORMENT-fabric_v2 (the dir that holds all four copies).
_OUTER = Path(__file__).resolve().parents[2]

_COPIES = {
    "production": _OUTER / "torment_fabric" / "torment_service" / "kernel",
    "v4_0": _OUTER / "v4.0",
    "epistemic_kernel": _OUTER / "epistemic_kernel" / "kernel",
    "zenodo": _OUTER / "Zenodo_research" / "tri_octagon_Model" / "17766958",
}

_FULL_COPIES = ("production", "v4_0", "epistemic_kernel")  # the three with seed_entities


# --------------------------------------------------------------------------- #
# static helpers (no execution of any copy)
# --------------------------------------------------------------------------- #

def _src(copy: str, fname: str):
    p = _COPIES[copy] / fname
    # utf-8-sig: strip a leading BOM if present (seed_entities.py carries one),
    # so ast.parse / token / hash comparisons are over consistent logical content.
    return p.read_text(encoding="utf-8-sig") if p.exists() else None


def _norm(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _sha(s: str) -> str:
    return hashlib.sha256(_norm(s).encode("utf-8")).hexdigest()


def _toplevel_symbols(s: str):
    out = set()
    for node in ast.parse(s).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
    return out


def _class_methods(s: str, cls: str):
    for node in ast.walk(ast.parse(s)):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return {m.name for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return None


_MODEL_METHODS = {
    "phase_lock_step", "advance_phi", "update_z",
    "update_cycle_stage", "update_identity_state", "step", "run",
}


# --------------------------------------------------------------------------- #
# 0. the four copy directories are present (this repo)
# --------------------------------------------------------------------------- #

class TestCopiesPresent(unittest.TestCase):
    def test_all_four_copy_dirs_exist(self):
        missing = [name for name, d in _COPIES.items() if not d.is_dir()]
        self.assertEqual(missing, [], f"expected copy dirs missing: {missing}")


# --------------------------------------------------------------------------- #
# 1. file presence map
# --------------------------------------------------------------------------- #

class TestFilePresenceMap(unittest.TestCase):
    def test_model_core_present_in_all_four(self):
        for copy in _COPIES:
            self.assertIsNotNone(_src(copy, "model_core.py"), f"{copy} model_core.py")

    def test_seed_entities_present_in_full_copies_absent_in_zenodo(self):
        for copy in _FULL_COPIES:
            self.assertIsNotNone(_src(copy, "seed_entities.py"), f"{copy} seed_entities.py")
        self.assertIsNone(_src("zenodo", "seed_entities.py"),
                          "zenodo unexpectedly has seed_entities.py")

    def test_identity_rules_present_in_all_four(self):
        for copy in _COPIES:
            self.assertIsNotNone(_src(copy, "identity_rules.py"), f"{copy} identity_rules.py")


# --------------------------------------------------------------------------- #
# 2. symbol surfaces compared WITHOUT declaring a winner
# --------------------------------------------------------------------------- #

class TestSymbolSurfaces(unittest.TestCase):
    def test_core_classes_present_in_all_four(self):
        for copy in _COPIES:
            syms = _toplevel_symbols(_src(copy, "model_core.py"))
            for cls in ("ModelParams", "ModelState", "TriOctaPhaseLockModel"):
                self.assertIn(cls, syms, f"{copy}.model_core missing {cls}")

    def test_full_copies_share_model_core_toplevel_surface(self):
        surfaces = {c: _toplevel_symbols(_src(c, "model_core.py")) for c in _FULL_COPIES}
        ref = surfaces["production"]
        for c in _FULL_COPIES:
            self.assertEqual(surfaces[c], ref,
                             f"{c} model_core top-level symbol surface differs from production")

    def test_zenodo_model_core_is_a_reduced_subset(self):
        # zenodo lacks the diagnostic helpers (_unit/_mirror_z/_make_history_meta)
        # that the three full copies share — a strictly smaller surface.
        prod = _toplevel_symbols(_src("production", "model_core.py"))
        zen = _toplevel_symbols(_src("zenodo", "model_core.py"))
        self.assertTrue(zen < prod, "zenodo model_core surface is not a strict subset of production")
        self.assertEqual(prod - zen, {"_unit", "_mirror_z", "_make_history_meta"})

    def test_seed_entities_surface_identical_in_full_copies(self):
        surfaces = {c: _toplevel_symbols(_src(c, "seed_entities.py")) for c in _FULL_COPIES}
        for c in _FULL_COPIES:
            self.assertIn("SeedWorld", surfaces[c])
            self.assertIn("SeedEntity", surfaces[c])
            self.assertEqual(surfaces[c], surfaces["production"])


# --------------------------------------------------------------------------- #
# 3. TriOctaPhaseLockModel method surface is shared across all four (bodies aside)
# --------------------------------------------------------------------------- #

class TestModelMethodSurface(unittest.TestCase):
    def test_all_copies_share_model_method_surface(self):
        for copy in _COPIES:
            methods = _class_methods(_src(copy, "model_core.py"), "TriOctaPhaseLockModel")
            self.assertIsNotNone(methods, f"{copy} has no TriOctaPhaseLockModel")
            self.assertTrue(
                _MODEL_METHODS <= methods,
                f"{copy} TriOctaPhaseLockModel missing methods: {_MODEL_METHODS - methods}",
            )


# --------------------------------------------------------------------------- #
# 4. chirality / chiral-memory primitive DISTRIBUTION across copies
# --------------------------------------------------------------------------- #

class TestChiralityPrimitiveDistribution(unittest.TestCase):
    """Maps which copy carries which chirality primitive. No copy is preferred."""

    def _has(self, copy: str, token: str) -> bool:
        return token in _src(copy, "model_core.py")

    def test_chiral_memory_surface_only_in_production_and_epistemic(self):
        # z_mem + jeff (the chirality-MEMORY EMA the lost sims relied on)
        for token in ("z_mem", "jeff"):
            present = {c for c in _COPIES if self._has(c, token)}
            self.assertEqual(
                present, {"production", "epistemic_kernel"},
                f"{token!r} chirality-memory surface distribution: {sorted(present)}",
            )

    def test_z_chiral_vector_in_full_copies_not_zenodo(self):
        present = {c for c in _COPIES if self._has(c, "Z_chiral")}
        self.assertEqual(present, set(_FULL_COPIES))
        # any 'chiral' geometry token follows the same distribution
        present_chiral = {c for c in _COPIES if self._has(c, "chiral")}
        self.assertEqual(present_chiral, set(_FULL_COPIES))

    def test_cycle_and_identity_state_in_all_four(self):
        for token in ("cycle_stage", "identity_state"):
            present = {c for c in _COPIES if self._has(c, token)}
            self.assertEqual(present, set(_COPIES), f"{token} not universal: {sorted(present)}")

    def test_v4_0_has_z_chiral_but_not_z_mem(self):
        # records the specific divergence: v4.0 kept the chiral vector, dropped memory
        self.assertTrue(self._has("v4_0", "Z_chiral"))
        self.assertFalse(self._has("v4_0", "z_mem"))
        self.assertFalse(self._has("v4_0", "jeff"))


# --------------------------------------------------------------------------- #
# 5. content identity vs divergence (preserve uncertainty; pick no winner)
# --------------------------------------------------------------------------- #

class TestContentIdentityAndDivergence(unittest.TestCase):
    def test_model_core_diverges_across_all_four(self):
        shas = {c: _sha(_src(c, "model_core.py")) for c in _COPIES}
        self.assertEqual(
            len(set(shas.values())), 4,
            f"expected 4 distinct model_core bodies; got {shas}",
        )

    def test_seed_entities_identical_across_full_copies(self):
        shas = {c: _sha(_src(c, "seed_entities.py")) for c in _FULL_COPIES}
        self.assertEqual(len(set(shas.values())), 1,
                         f"seed_entities.py expected identical across full copies; got {shas}")

    def test_identity_rules_identical_across_all_four(self):
        shas = {c: _sha(_src(c, "identity_rules.py")) for c in _COPIES}
        self.assertEqual(len(set(shas.values())), 1,
                         f"identity_rules.py expected identical across copies; got {shas}")


# --------------------------------------------------------------------------- #
# 6. no canonical selection / no reconstruction (uncertainty preserved)
# --------------------------------------------------------------------------- #

class TestNoCanonicalSelectionNoReconstruction(unittest.TestCase):
    def test_chiral_memory_surface_has_more_than_one_candidate(self):
        # >= 2 copies carry the chirality-memory surface => this map does NOT
        # force a single canonical source; the choice stays OPEN for a later gate.
        candidates = {c for c in _COPIES if "z_mem" in _src(c, "model_core.py")}
        self.assertGreaterEqual(len(candidates), 2,
                                "expected the canonical choice to remain undecided (>=2 candidates)")

    def test_no_lost_sim_scripts_recreated_in_any_copy(self):
        for copy, d in _COPIES.items():
            for name in ("sim_continuous_kernel.py", "sim_chirality_flip.py",
                         "sim_conversation_shock.py"):
                hits = [p for p in d.rglob(name) if "__pycache__" not in p.parts]
                self.assertEqual(hits, [], f"{name} unexpectedly present under {copy}: {hits}")


if __name__ == "__main__":
    unittest.main()
