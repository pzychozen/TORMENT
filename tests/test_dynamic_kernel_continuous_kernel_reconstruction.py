"""tests/test_dynamic_kernel_continuous_kernel_reconstruction.py

Proves the standalone, deterministic, in-memory `continuous_kernel` reconstruction
module (tests/research/dynamic_kernel_continuous_kernel.py) behaves per the locked
contract: deterministic, bounded chirality memory, expected step/time progression,
canonical-only imports, no lost-script recreation, and no output artifacts.

Bounded: imports the module by file path (test-adjacent research module). Touches
no production code, creates no files/plots/data, and reconstructs only the baseline
continuous-kernel target (chirality_flip / conversation_shock / Z-force loop /
runtime tick all remain HOLD and are not built or tested here).
"""
from __future__ import annotations

import ast
import importlib.util
import math
import sys
import unittest
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent  # torment_fabric
_MODULE_PATH = _TESTS_DIR / "research" / "dynamic_kernel_continuous_kernel.py"


def _load_module():
    name = "ck_recon_module_under_test"
    spec = importlib.util.spec_from_file_location(name, _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so the module's dataclasses can resolve their own
    # string annotations (from __future__ import annotations) via sys.modules.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_CK = _load_module()
run_continuous_kernel_reconstruction = _CK.run_continuous_kernel_reconstruction
ContinuousKernelResult = _CK.ContinuousKernelResult
KernelSample = _CK.KernelSample


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
# 1. structured-output shape + ranges
# ---------------------------------------------------------------------------

class TestReconstructionShape(unittest.TestCase):
    def test_returns_structured_samples(self):
        r = run_continuous_kernel_reconstruction(n_steps=50)
        self.assertIsInstance(r, ContinuousKernelResult)
        self.assertEqual(r.n_steps, 50)
        self.assertEqual(len(r.samples), 50)
        self.assertEqual(r.seed_samples, ())  # no seeds requested -> none
        s0 = r.samples[0]
        self.assertIsInstance(s0, KernelSample)
        # the contract-covered surfaces are all present per sample
        for attr in ("step", "t", "omega", "kappa", "z", "z_mem", "jeff",
                     "cycle_stage", "identity_state"):
            self.assertTrue(hasattr(s0, attr), attr)

    def test_sample_values_in_documented_ranges(self):
        r = run_continuous_kernel_reconstruction(n_steps=120)
        for s in r.samples:
            self.assertEqual(len(s.omega), 3)
            self.assertTrue(all(math.isfinite(c.real) and math.isfinite(c.imag) for c in s.omega))
            self.assertTrue(math.isfinite(s.z))
            self.assertTrue(math.isfinite(s.jeff))
            self.assertIn(int(s.cycle_stage), range(0, 7))    # S0..S6
            self.assertIn(int(s.identity_state), range(0, 9))  # s0..s8


# ---------------------------------------------------------------------------
# 2. determinism
# ---------------------------------------------------------------------------

class TestDeterminism(unittest.TestCase):
    def test_identical_args_give_identical_result(self):
        a = run_continuous_kernel_reconstruction(n_steps=80)
        b = run_continuous_kernel_reconstruction(n_steps=80)
        self.assertEqual(a, b)  # frozen dataclasses compare field-by-field

    def test_explicit_omega0_is_reproducible(self):
        kw = dict(omega0=(0.4 + 0.1j, -0.2 + 0.3j, 0.5 - 0.2j), n_steps=60, dt=0.05)
        self.assertEqual(
            run_continuous_kernel_reconstruction(**kw),
            run_continuous_kernel_reconstruction(**kw),
        )


# ---------------------------------------------------------------------------
# 3. bounded chirality memory (z_mem)
# ---------------------------------------------------------------------------

class TestBoundedChiralityMemory(unittest.TestCase):
    def test_z_mem_stays_within_bounded_band(self):
        r = run_continuous_kernel_reconstruction(n_steps=300)
        for s in r.samples:
            self.assertTrue(-1.0 < float(s.z_mem) < 1.0, f"z_mem out of band: {s.z_mem}")


# ---------------------------------------------------------------------------
# 4. step / time progression
# ---------------------------------------------------------------------------

class TestStepTimeProgression(unittest.TestCase):
    def test_step_and_time_advance_as_expected(self):
        dt = 0.1
        r = run_continuous_kernel_reconstruction(n_steps=100, dt=dt)
        for i, s in enumerate(r.samples):
            self.assertEqual(s.step, i + 1)
            self.assertTrue(math.isclose(s.t, (i + 1) * dt, rel_tol=1e-9, abs_tol=1e-12))
        # the kernel actually evolves (continuous internal dynamics, no input)
        self.assertNotEqual(r.samples[0].omega, r.samples[-1].omega)


# ---------------------------------------------------------------------------
# 5. optional DECOUPLED seed state
# ---------------------------------------------------------------------------

class TestDecoupledSeedState(unittest.TestCase):
    def test_seed_samples_are_produced_and_deterministic(self):
        seeds = [(0, [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
                 (1, [0.0, 1.0, 0.0], [1.0, 0.0, 0.0])]
        a = run_continuous_kernel_reconstruction(n_steps=40, seeds=seeds)
        b = run_continuous_kernel_reconstruction(n_steps=40, seeds=seeds)
        self.assertEqual(len(a.seed_samples), 40)
        self.assertEqual(len(a.seed_samples[0].positions), 2)
        self.assertEqual(a, b)  # deterministic incl. seed trajectory

    def test_seed_trajectory_is_independent_of_kernel_omega(self):
        # decoupling: changing the kernel initial Omega must NOT change the seed
        # trajectory (no kernel->seed coupling exists in the reconstruction).
        seeds = [(0, [1.0, 0.0, 0.0], [0.0, 1.0, 0.0])]
        r1 = run_continuous_kernel_reconstruction(
            omega0=(0.5 + 0.3j, 0.2 - 0.4j, 0.6 + 0.1j), n_steps=30, seeds=seeds)
        r2 = run_continuous_kernel_reconstruction(
            omega0=(1.0 + 0.0j, 0.0 + 1.0j, -0.5 + 0.2j), n_steps=30, seeds=seeds)
        self.assertNotEqual(r1.samples, r2.samples)        # kernel differs ...
        self.assertEqual(r1.seed_samples, r2.seed_samples)  # ... seeds identical


# ---------------------------------------------------------------------------
# 6. canonical-only imports / no omitted-mechanic or output tokens in the module
# ---------------------------------------------------------------------------

class TestModuleBoundaries(unittest.TestCase):
    _ALLOWED_IMPORT_ROOTS = {"__future__", "dataclasses", "typing", "numpy", "torment_service"}
    _FORBIDDEN_TOKENS = (
        "open(", ".write(", "savefig", "matplotlib", "pyplot", "plt.",
        "argparse", "sys.argv", "to_csv", "csv.", "json.dump", "logging", "print(",
        "sim_continuous_kernel", "sim_chirality_flip", "sim_conversation_shock",
    )

    def _src(self):
        return _MODULE_PATH.read_text(encoding="utf-8")

    def test_module_imports_canonical_kernel_only(self):
        roots = set()
        for node in ast.walk(ast.parse(self._src())):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertEqual(roots - self._ALLOWED_IMPORT_ROOTS, set(),
                         f"unexpected imports: {roots - self._ALLOWED_IMPORT_ROOTS}")
        # only the canonical kernel submodules are used
        srctext = self._src()
        self.assertIn("torment_service.kernel.model_core", srctext)
        self.assertIn("torment_service.kernel.seed_entities", srctext)

    def test_module_has_no_output_cli_or_lost_script_tokens(self):
        src = self._src()
        present = [t for t in self._FORBIDDEN_TOKENS if t in src]
        self.assertEqual(present, [], f"forbidden tokens in module: {present}")

    def test_module_is_not_a_runnable_script(self):
        # a module, not a script: no `if __name__ == "__main__"` run guard
        # (the docstring may mention __main__, so check for the guard itself)
        self.assertNotIn("if __name__", self._src())


# ---------------------------------------------------------------------------
# 7. no output artifacts at runtime; lost scripts stay absent
# ---------------------------------------------------------------------------

class TestNoArtifactsNoReconstruction(unittest.TestCase):
    def test_running_reconstruction_creates_no_files(self):
        before = _snapshot_repo_files()
        run_continuous_kernel_reconstruction(n_steps=50)
        run_continuous_kernel_reconstruction(
            n_steps=20, seeds=[(0, [0, 0, 0], [1, 1, 1])])
        after = _snapshot_repo_files()
        self.assertEqual(after - before, set(),
                         f"reconstruction created artifacts: {after - before}")

    def test_lost_driver_scripts_remain_absent(self):
        for name in ("sim_continuous_kernel.py", "sim_chirality_flip.py",
                     "sim_conversation_shock.py"):
            hits = [p for p in _REPO_ROOT.rglob(name) if "__pycache__" not in p.parts]
            self.assertEqual(hits, [], f"{name} unexpectedly present: {hits}")


if __name__ == "__main__":
    unittest.main()
