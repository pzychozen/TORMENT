"""tests/test_dynamic_kernel_chirality_flip_reconstruction.py

Proves the standalone `chirality_flip` SURFACE reconstruction module
(tests/research/dynamic_kernel_chirality_flip.py) follows the accepted contract and
reconstructs ONLY the signed-chirality transition surface: J_eff / normalized
chirality / chirality sign / pairwise sign-change (flip) / canonical z_mem response.

It proves the boundaries hold: no kernel trajectory stepping, no A-D scenario sweep,
no seed-force reversal, no flip-count table, no plot/data/output, no lost-simulator
behavior, lost driver scripts absent, and `conversation_shock` unopened.

Bounded: imports the module by file path (test-adjacent research module) and the
canonical kernel (safe, per the archaeology tests). Touches no production code,
creates no files.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

from torment_service.cognitive_core import CognitiveCore, CognitiveCoreState
from torment_service.kernel.model_core import ModelParams, ModelState

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent  # torment_fabric
_MODULE_PATH = _TESTS_DIR / "research" / "dynamic_kernel_chirality_flip.py"

_OMEGA_POS = (1 + 0j, 1 + 0j, 0 + 1j)   # Im(1*1*+1j) = +1
_OMEGA_NEG = (1 + 0j, 1 + 0j, 0 - 1j)   # Im(1*1*-1j) = -1
_OMEGA_ZERO = (1 + 0j, 1 + 0j, 1 + 0j)  # Im(real) = 0


def _load_module():
    name = "ck_flip_module_under_test"
    spec = importlib.util.spec_from_file_location(name, _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # register so the module's dataclasses resolve annotations
    spec.loader.exec_module(mod)
    return mod


_CF = _load_module()


def _cognitive_zmem(omega, z_mem0=0.0):
    s = ModelState(Omega=np.asarray(omega, dtype=complex).reshape(3).copy())
    cog = CognitiveCoreState(z_mem=float(z_mem0))
    CognitiveCore().update(cog, state=s, params=ModelParams())
    return float(cog.z_mem)


def _snapshot_repo_files():
    out = set()
    for p in _REPO_ROOT.rglob("*"):
        parts = p.parts
        if "__pycache__" in parts or ".git" in parts or p.suffix == ".pyc":
            continue
        if p.is_file():
            out.add(p.relative_to(_REPO_ROOT).as_posix())
    return out


# ---------------------------------------------------------------------------
# 1. module follows the accepted contract (same source-backed definitions)
# ---------------------------------------------------------------------------

class TestFollowsContract(unittest.TestCase):
    def test_jeff_matches_canonical_signed_triad_area(self):
        for omega in (_OMEGA_POS, _OMEGA_NEG, (0.5 + 0.3j, 0.2 - 0.4j, 0.6 + 0.1j)):
            o1, o2, o3 = np.asarray(omega, dtype=complex)
            self.assertAlmostEqual(_CF.jeff(omega), float(np.imag(o1 * np.conj(o2) * o3)))

    def test_normalized_chirality_is_bounded_ratio(self):
        for omega in (_OMEGA_POS, _OMEGA_NEG, (3 + 2j, -1 + 0j, 0 + 5j)):
            j = _CF.jeff(omega)
            self.assertAlmostEqual(_CF.normalized_chirality(omega), j / (1.0 + abs(j)))
            self.assertTrue(-1.0 < _CF.normalized_chirality(omega) < 1.0)

    def test_public_surface_is_exactly_the_contract_helpers(self):
        allowed = {"jeff", "normalized_chirality", "chirality_sign", "is_flip",
                   "ChiralitySample", "chirality_sample", "ZMemResponse", "z_mem_response"}
        defined = set()
        for node in ast.parse(_MODULE_PATH.read_text(encoding="utf-8")).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name)
        self.assertEqual(defined, allowed,
                         f"module surface drifted from the contract helpers: {defined ^ allowed}")


# ---------------------------------------------------------------------------
# 2. positive / negative J_eff -> expected signs
# ---------------------------------------------------------------------------

class TestSignedInputs(unittest.TestCase):
    def test_positive_and_negative_and_zero_signs(self):
        self.assertGreater(_CF.jeff(_OMEGA_POS), 0.0)
        self.assertLess(_CF.jeff(_OMEGA_NEG), 0.0)
        self.assertEqual(_CF.jeff(_OMEGA_ZERO), 0.0)
        self.assertEqual(_CF.chirality_sign(_OMEGA_POS), 1)
        self.assertEqual(_CF.chirality_sign(_OMEGA_NEG), -1)
        self.assertEqual(_CF.chirality_sign(_OMEGA_ZERO), 0)

    def test_chirality_sample_structure(self):
        s = _CF.chirality_sample(_OMEGA_POS)
        self.assertIsInstance(s, _CF.ChiralitySample)
        self.assertEqual(s.sign, 1)
        self.assertGreater(s.jeff, 0.0)
        self.assertTrue(-1.0 < s.normalized < 1.0)


# ---------------------------------------------------------------------------
# 3. pairwise flip means ONLY a signed-J_eff sign change (nothing else)
# ---------------------------------------------------------------------------

class TestPairwiseFlipIsSignChangeOnly(unittest.TestCase):
    def test_flip_iff_opposite_nonzero_signs(self):
        self.assertTrue(_CF.is_flip(_OMEGA_POS, _OMEGA_NEG))
        self.assertTrue(_CF.is_flip(_OMEGA_NEG, _OMEGA_POS))
        self.assertFalse(_CF.is_flip(_OMEGA_POS, _OMEGA_POS))
        self.assertFalse(_CF.is_flip(_OMEGA_NEG, _OMEGA_NEG))
        # a zero-chirality state is not a flip on either side
        self.assertFalse(_CF.is_flip(_OMEGA_POS, _OMEGA_ZERO))
        self.assertFalse(_CF.is_flip(_OMEGA_ZERO, _OMEGA_NEG))

    def test_flip_depends_on_sign_only_not_magnitude(self):
        # same sign, wildly different magnitudes -> NOT a flip
        big_pos = (10 + 0j, 10 + 0j, 0 + 10j)   # jeff = +1000, sign +1
        self.assertGreater(_CF.jeff(big_pos), 0.0)
        self.assertFalse(_CF.is_flip(_OMEGA_POS, big_pos))
        # opposite sign regardless of magnitude -> IS a flip
        big_neg = (10 + 0j, 10 + 0j, 0 - 10j)   # sign -1
        self.assertTrue(_CF.is_flip(big_pos, big_neg))


# ---------------------------------------------------------------------------
# 4. z_mem bounded + sign-following via CANONICAL kernel update_z
# ---------------------------------------------------------------------------

class TestZMemBoundedSignFollowing(unittest.TestCase):
    def test_z_mem_response_matches_canonical_update_z(self):
        for omega in (_OMEGA_POS, _OMEGA_NEG):
            r = _CF.z_mem_response(omega, z_mem0=0.0)
            self.assertIsInstance(r, _CF.ZMemResponse)
            self.assertAlmostEqual(r.z_mem_after, _cognitive_zmem(omega, 0.0))

    def test_z_mem_is_bounded_and_sign_following_and_contractive(self):
        rp = _CF.z_mem_response(_OMEGA_POS, z_mem0=0.0)
        rn = _CF.z_mem_response(_OMEGA_NEG, z_mem0=0.0)
        self.assertGreater(rp.z_mem_after, 0.0)
        self.assertLess(rn.z_mem_after, 0.0)
        self.assertTrue(-1.0 < rp.z_mem_after < 1.0 and -1.0 < rn.z_mem_after < 1.0)
        # contractive: one update moves only a fraction toward normalized chirality
        self.assertLess(abs(rp.z_mem_after), abs(rp.normalized))


# ---------------------------------------------------------------------------
# 5. module boundaries: canonical-only imports, no stepping/output/CLI tokens
# ---------------------------------------------------------------------------

class TestModuleBoundaries(unittest.TestCase):
    _ALLOWED_IMPORT_ROOTS = {"__future__", "dataclasses", "typing", "numpy", "torment_service"}
    _FORBIDDEN_CODE_TOKENS = (
        "open(", ".write(", "savefig", "matplotlib", "pyplot", "plt.",
        "argparse", "sys.argv", "to_csv", "csv.", "json.dump", "logging", "print(",
        ".step(",            # no kernel trajectory stepping / flip-hunting loop
        "SeedWorld", "seed_entities",  # no seed-force reversal
        "conversation_shock",          # conversation_shock stays unopened
    )

    def _src(self):
        return _MODULE_PATH.read_text(encoding="utf-8")

    def test_imports_extracted_cognition_and_canonical_model_state_only(self):
        roots = set()
        for node in ast.walk(ast.parse(self._src())):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertEqual(roots - self._ALLOWED_IMPORT_ROOTS, set())
        src = self._src()
        self.assertIn("torment_service.cognitive_core", src)
        self.assertIn("torment_service.kernel.model_core", src)
        self.assertNotIn("torment_service.kernel.seed_entities", src)  # no seeds

    def test_no_forbidden_output_cli_step_or_lost_target_tokens(self):
        present = [t for t in self._FORBIDDEN_CODE_TOKENS if t in self._src()]
        self.assertEqual(present, [], f"forbidden tokens in module: {present}")

    def test_module_is_not_a_runnable_script(self):
        self.assertNotIn("if __name__", self._src())


# ---------------------------------------------------------------------------
# 6. no artifacts; lost scripts absent; conversation_shock unopened
# ---------------------------------------------------------------------------

class TestNoArtifactsNoReconstruction(unittest.TestCase):
    def test_exercising_all_helpers_creates_no_files(self):
        before = _snapshot_repo_files()
        _CF.chirality_sample(_OMEGA_POS)
        _CF.is_flip(_OMEGA_POS, _OMEGA_NEG)
        _CF.z_mem_response(_OMEGA_POS)
        _CF.z_mem_response(_OMEGA_NEG, z_mem0=0.2)
        after = _snapshot_repo_files()
        self.assertEqual(after - before, set(), f"created artifacts: {after - before}")

    def test_lost_driver_scripts_remain_absent(self):
        for name in ("sim_chirality_flip.py", "sim_continuous_kernel.py",
                     "sim_conversation_shock.py"):
            hits = [p for p in _REPO_ROOT.rglob(name) if "__pycache__" not in p.parts]
            self.assertEqual(hits, [], f"{name} unexpectedly present: {hits}")

    def test_conversation_shock_remains_unopened(self):
        # no conversation_shock module/script exists and the reconstruction module
        # references none.
        self.assertEqual(
            [p for p in _REPO_ROOT.rglob("sim_conversation_shock.py")
             if "__pycache__" not in p.parts], [])
        self.assertNotIn("conversation_shock", _MODULE_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
