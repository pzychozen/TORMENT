"""tests/test_dynamic_kernel_chirality_flip_reconstruction_contract.py

Tests-only CONTRACT for a FUTURE, separately-gated `chirality_flip` reconstruction
(Sim 2: chirality-flip hunting). It pins the admissible reconstruction SURFACE from
source — and pins the flip-hunting *mechanics* as future boundaries — WITHOUT
reconstructing anything and WITHOUT creating a reconstruction module.

Definition of "flip" used here (the ONLY source-supported one):
  the canonical `model_core.update_z` computes the signed triad area
  ``J_eff = Im(O1 * conj(O2) * O3)`` and ``jeff_norm = J_eff / (1 + |J_eff|)``.
  The *effective chirality sign* is ``sign(J_eff)``; a **flip** is a change of that
  sign across states. (`RESEARCH_simulation_findings.md`'s "J_eff Flips" column counts
  exactly these sign changes.) PNG curve reproduction is NOT authority and is asserted
  nowhere.

Source-backed and pinned here:
  * the signed-coupling surface admits positive AND negative `J_eff` (flips are
    well-defined on it);
  * `z_mem` / chirality-memory prerequisite exists and is a bounded, sign-following EMA;
  * the noise hook (`omega_noise_sigma`) exists but defaults to 0.0 (deterministic).

Future BOUNDARIES (HOLD; pinned as ABSENT from the surviving surface, not built):
  * the flip-hunting loop, the scenario sweep (A–D), seed-force reversal coupling, and
    flip COUNTING are not in the canonical kernel — they were the lost driver script's
    job (prose-only in the findings doc);
  * the noise levels / initial conditions of the flip scenarios are prose-only, not
    source — a reconstruction must not invent them;
  * `sim_chirality_flip.py` (and the other two driver scripts) remain absent.

This file passes NOW, before any chirality_flip reconstruction module exists. It reads
only the canonical `torment_service/kernel` source, runs only the already-safe
deterministic `update_z` surface, creates no files/plots/data, and reconstructs nothing.

Scope: tests-only. No production change. No reconstruction module. No runtime/outputs.
"""
from __future__ import annotations

import inspect
import math
import unittest
from pathlib import Path

import numpy as np

import torment_service.cognitive_core as _cc
# Canonical source (proven importable + safe by the archaeology/contract tests).
import torment_service.kernel.model_core as _mc
import torment_service.kernel.seed_entities as _se
from torment_service.cognitive_core import CognitiveCore, CognitiveCoreState
from torment_service.kernel.model_core import (
    ModelParams,
    ModelState,
    TriOctaPhaseLockModel,
)
from torment_service.kernel.seed_entities import SeedWorld

_REPO_ROOT = Path(__file__).resolve().parents[1]
_COGNITIVE_SRC = Path(_cc.__file__).read_text(encoding="utf-8")
_MODEL_CORE_SRC = Path(_mc.__file__).read_text(encoding="utf-8")
_SEED_SRC = Path(_se.__file__).read_text(encoding="utf-8")

# Signed-coupling inputs (deterministic): Im(1*1*+-1j) = +-1.
_OMEGA_POS = np.array([1 + 0j, 1 + 0j, 0 + 1j], dtype=complex)
_OMEGA_NEG = np.array([1 + 0j, 1 + 0j, 0 - 1j], dtype=complex)

# Mechanics that belong to the LOST flip-hunting loop, not the surviving surface.
_FLIP_BOUNDARY_TOKENS = ("flip", "scenario", "sweep", "reversal", "hunt", "count_flip")


def _jeff(omega) -> float:
    o1, o2, o3 = omega
    return float(np.imag(o1 * np.conj(o2) * o3))


def _jeff_norm(j: float) -> float:
    return j / (1.0 + abs(j))


def _chirality_sign(omega) -> int:
    j = _jeff(omega)
    return 0 if j == 0.0 else int(math.copysign(1, j))


def _is_flip(omega_a, omega_b) -> bool:
    sa, sb = _chirality_sign(omega_a), _chirality_sign(omega_b)
    return sa != 0 and sb != 0 and sa != sb


def _cognitive_response(omega, *, z_mem0: float = 0.0) -> CognitiveCoreState:
    state = ModelState(Omega=np.asarray(omega, dtype=complex).reshape(3).copy())
    cog = CognitiveCoreState(z_mem=float(z_mem0))
    CognitiveCore().update(cog, state=state, params=ModelParams())
    return cog


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
# 1. flip is defined ONLY as source-supported signed-J_eff sign behavior
# ---------------------------------------------------------------------------

class TestFlipDefinitionSourceBacked(unittest.TestCase):
    def test_signed_coupling_surface_admits_both_signs(self):
        self.assertGreater(_jeff(_OMEGA_POS), 0.0)
        self.assertLess(_jeff(_OMEGA_NEG), 0.0)
        self.assertEqual(_chirality_sign(_OMEGA_POS), +1)
        self.assertEqual(_chirality_sign(_OMEGA_NEG), -1)

    def test_flip_is_a_sign_change_of_jeff(self):
        # a flip := opposite effective chirality sign (the only source-backed meaning)
        self.assertTrue(_is_flip(_OMEGA_POS, _OMEGA_NEG))
        self.assertFalse(_is_flip(_OMEGA_POS, _OMEGA_POS))

    def test_jeff_formula_is_the_canonical_one(self):
        # the contract's J_eff matches the extracted cognitive primitive (source token).
        self.assertIn("np.imag", _COGNITIVE_SRC)
        self.assertIn("z_mem", _COGNITIVE_SRC)
        # bounded normalization stays in (-1, 1)
        for omega in (_OMEGA_POS, _OMEGA_NEG, np.array([3 + 2j, -1 + 0j, 0 + 5j], dtype=complex)):
            self.assertTrue(-1.0 < _jeff_norm(_jeff(omega)) < 1.0)


# ---------------------------------------------------------------------------
# 2. chirality-memory (z_mem) prerequisite: bounded sign-following EMA
# ---------------------------------------------------------------------------

class TestChiralityMemoryPrerequisite(unittest.TestCase):
    def test_z_mem_field_exists_default_zero(self):
        self.assertEqual(float(CognitiveCoreState().z_mem), 0.0)

    def test_z_mem_follows_sign_and_stays_bounded(self):
        sp = _cognitive_response(_OMEGA_POS, z_mem0=0.0)
        sn = _cognitive_response(_OMEGA_NEG, z_mem0=0.0)
        self.assertGreater(sp.z_mem, 0.0)
        self.assertLess(sn.z_mem, 0.0)
        self.assertTrue(-1.0 < sp.z_mem < 1.0 and -1.0 < sn.z_mem < 1.0)
        # contractive: a single update moves only a fraction toward jeff_norm
        self.assertLess(abs(sp.z_mem), abs(_jeff_norm(_jeff(_OMEGA_POS))))


# ---------------------------------------------------------------------------
# 3. the noise hook exists but defaults to deterministic
# ---------------------------------------------------------------------------

class TestNoiseHookDeterministicByDefault(unittest.TestCase):
    def test_omega_noise_sigma_hook_present_and_off_by_default(self):
        # flips in the findings doc are a NOISE-regime phenomenon. The surviving
        # surface exposes the noise hook but defaults it OFF (deterministic). The
        # scenario noise levels / ICs themselves are prose-only (see §4).
        self.assertEqual(float(ModelParams().omega_noise_sigma), 0.0)
        self.assertIn("omega_noise_sigma", _MODEL_CORE_SRC)

    def test_no_scenario_noise_schedule_baked_into_kernel(self):
        # the kernel applies at most a single per-step sigma; it bakes in no
        # multi-scenario noise sweep (that schedule is the lost loop's job).
        for tok in ("scenario", "sweep"):
            self.assertNotIn(tok, _MODEL_CORE_SRC.lower())


# ---------------------------------------------------------------------------
# 4. flip-hunting MECHANICS are a future boundary (pinned ABSENT, not built)
# ---------------------------------------------------------------------------

class TestFlipHuntingMechanicsAreBoundary(unittest.TestCase):
    def test_no_flip_hunting_tokens_in_canonical_kernel(self):
        # loop / scenario sweep / seed-force reversal / flip counting are NOT in
        # the surviving surface -- they were the lost driver script's job.
        for tok in _FLIP_BOUNDARY_TOKENS:
            self.assertNotIn(tok, _MODEL_CORE_SRC.lower(), f"{tok!r} in model_core")
            self.assertNotIn(tok, _SEED_SRC.lower(), f"{tok!r} in seed_entities")

    def test_no_flip_counter_on_the_surviving_surface(self):
        # z_mem is a bounded EMA, not a flip counter; the surviving model exposes
        # no flip-count API.
        self.assertFalse(hasattr(TriOctaPhaseLockModel, "count_flips"))
        self.assertFalse(hasattr(ModelState, "flip_count"))

    def test_seed_force_reversal_coupling_is_absent(self):
        # the "Relational channel force reversal during chirality flips" was an
        # EXTERNAL coupling; SeedWorld.step() takes no kernel/chirality state.
        self.assertEqual(list(inspect.signature(SeedWorld.step).parameters), ["self"])


# ---------------------------------------------------------------------------
# 5. lost script absent; no artifacts; nothing reconstructed
# ---------------------------------------------------------------------------

class TestLostScriptAndNoArtifacts(unittest.TestCase):
    def test_lost_driver_scripts_remain_absent(self):
        for name in ("sim_chirality_flip.py", "sim_continuous_kernel.py",
                     "sim_conversation_shock.py"):
            hits = [p for p in _REPO_ROOT.rglob(name) if "__pycache__" not in p.parts]
            self.assertEqual(hits, [], f"{name} unexpectedly present: {hits}")

    def test_exercising_the_surface_creates_no_files(self):
        before = _snapshot_repo_files()
        for omega in (_OMEGA_POS, _OMEGA_NEG):
            _cognitive_response(omega, z_mem0=0.0)
        after = _snapshot_repo_files()
        self.assertEqual(after - before, set(),
                         f"contract checks created artifacts: {after - before}")


if __name__ == "__main__":
    unittest.main()
