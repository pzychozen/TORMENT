"""tests/test_dynamic_kernel_continuous_kernel_reconstruction_contract.py

Tests-only CONTRACT for a future, separately-gated, standalone `continuous_kernel`
reconstruction (Sim 1: baseline continuous dynamics). It pins the deterministic
surfaces of the CANONICAL source (`torment_service/kernel/`) that such a
reconstruction MAY rely on -- and the boundaries it may NOT assume exist.

This file:
  * creates no simulation script (the three driver scripts stay absent -- see the
    HOLD boundary below);
  * implements no external Z-force coupling loop and no background runtime tick;
  * compares against no PNG curve and generates no plots / data / output files;
  * alters no production code and reads only the canonical kernel package.

It passes NOW against the current API (no expected-failure / placeholder tests).

HOLD boundary (future targets, NOT created or authorized here):
  - sim_continuous_kernel.py   (this target -- reconstruction still HOLD)
  - sim_chirality_flip.py       (separate target -- HOLD)
  - sim_conversation_shock.py   (separate target -- HOLD)
The external Z-force coupling loop and any background/continuous runtime tick are
likewise NOT part of the surviving surface and remain future-build boundaries.

Grounding: `torment_service/kernel` (canonical, per
docs/TORMENT_DYNAMIC_KERNEL_CHIRALITY_CANONICAL_SOURCE_DECISION_v0.1.md); the
recovery inventory + decision frames; the phase-1/phase-2 archaeology tests.

Scope: tests-only. No production change. No runtime. Deterministic, in-memory.
"""
from __future__ import annotations

import inspect
import math
import unittest
from pathlib import Path

import numpy as np

from torment_service.cognitive_core import CognitiveCore, CognitiveCoreState

# Canonical reference source (proven importable + safe in phase-1 archaeology).
from torment_service.kernel.model_core import (
    ModelParams,
    ModelState,
    TriOctaPhaseLockModel,
)
from torment_service.kernel.seed_entities import SeedWorld, SeedEntity

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Documented chirality primitive (model_core.update_z): the SIGNED triad area.
_OMEGA_POS = np.array([1 + 0j, 1 + 0j, 0 + 1j], dtype=complex)   # Im(1*1*1j) = +1
_OMEGA_NEG = np.array([1 + 0j, 1 + 0j, 0 - 1j], dtype=complex)   # Im(1*1*-1j) = -1
# A generic asymmetric initial Omega for continuous-dynamics stepping.
_OMEGA_ASYM = np.array([0.5 + 0.3j, 0.2 - 0.4j, 0.6 + 0.1j], dtype=complex)


def _jeff(omega) -> float:
    o1, o2, o3 = omega
    return float(np.imag(o1 * np.conj(o2) * o3))


def _jeff_norm(j: float) -> float:
    return j / (1.0 + abs(j))


def _cognitive_response(omega, *, z_mem0: float = 0.0, n: int = 1) -> CognitiveCoreState:
    params = ModelParams()
    state = ModelState(Omega=np.asarray(omega, dtype=complex).reshape(3).copy())
    cog = CognitiveCoreState(z_mem=float(z_mem0))
    core = CognitiveCore()
    for _ in range(n):
        core.update(cog, state=state, params=params)
    return cog


# ---------------------------------------------------------------------------
# C1. Canonical primitives are constructible and deterministic by default
# ---------------------------------------------------------------------------

class TestCanonicalSourceConstructible(unittest.TestCase):
    def test_model_and_state_construct_from_canonical_source(self):
        model = TriOctaPhaseLockModel(ModelParams())
        self.assertIsInstance(model, TriOctaPhaseLockModel)
        state = ModelState(Omega=_OMEGA_ASYM.copy())
        self.assertEqual(state.Omega.shape, (3,))

    def test_default_config_is_deterministic(self):
        # A reconstruction may rely on a noiseless default config (no stochastic
        # forcing) -> reproducible. Stochastic regimes are an explicit opt-in.
        self.assertEqual(float(ModelParams().omega_noise_sigma), 0.0)


# ---------------------------------------------------------------------------
# C2. Chirality-memory surface (z_mem) -- a bounded slow EMA
# ---------------------------------------------------------------------------

class TestChiralityMemoryContract(unittest.TestCase):
    def test_z_mem_field_exists_and_defaults_zero(self):
        self.assertEqual(float(CognitiveCoreState().z_mem), 0.0)

    def test_z_mem_is_bounded_signed_memory_following_jeff(self):
        sp = _cognitive_response(_OMEGA_POS, z_mem0=0.0)
        sn = _cognitive_response(_OMEGA_NEG, z_mem0=0.0)
        # moves toward the sign of normalized J_eff, stays in the (-1, 1) band
        self.assertGreater(sp.z_mem, 0.0)
        self.assertLess(sn.z_mem, 0.0)
        self.assertTrue(-1.0 < sp.z_mem < 1.0 and -1.0 < sn.z_mem < 1.0)
        # contractive: a single update moves only a fraction toward jeff_norm
        self.assertLess(abs(sp.z_mem), abs(_jeff_norm(_jeff(_OMEGA_POS))))


# ---------------------------------------------------------------------------
# C3. J_eff-like signed coupling SURFACE exists (the loop that used it is lost)
# ---------------------------------------------------------------------------

class TestJeffSignedCouplingSurfaceContract(unittest.TestCase):
    def test_signed_triad_coupling_surface_is_sign_bearing_and_bounded(self):
        self.assertGreater(_jeff(_OMEGA_POS), 0.0)
        self.assertLess(_jeff(_OMEGA_NEG), 0.0)
        for omega in (_OMEGA_POS, _OMEGA_NEG, _OMEGA_ASYM):
            self.assertTrue(-1.0 < _jeff_norm(_jeff(omega)) < 1.0)
        # z_mem sign follows the surface sign (surface drives memory)
        s = _cognitive_response(_OMEGA_POS, z_mem0=0.0)
        self.assertEqual(math.copysign(1.0, s.z_mem),
                         math.copysign(1.0, _jeff_norm(_jeff(_OMEGA_POS))))


# ---------------------------------------------------------------------------
# C4. Seed position/velocity state (SeedWorld / SeedEntity)
# ---------------------------------------------------------------------------

class TestSeedStateContract(unittest.TestCase):
    def test_seed_world_integrates_pos_vel_deterministically(self):
        world = SeedWorld(dt=1.0, drag=0.02, drift=np.zeros(3))
        ent = world.spawn(born_step=0, channel=0,
                          pos=np.array([1.0, 0.0, 0.0]), vel=np.array([0.0, 1.0, 0.0]))
        self.assertIsInstance(ent, SeedEntity)
        world.step()
        # documented integrator: vel = (1-drag)*vel + drift ; pos += dt*vel
        np.testing.assert_allclose(ent.vel, [0.0, 0.98, 0.0])
        np.testing.assert_allclose(ent.pos, [1.0, 0.98, 0.0])
        np.testing.assert_allclose(ent.vel0, [0.0, 1.0, 0.0])  # frozen at birth


# ---------------------------------------------------------------------------
# C5. cycle_stage / identity_state surfaces (present in the current API)
# ---------------------------------------------------------------------------

class TestCycleIdentityStateContract(unittest.TestCase):
    def test_cycle_and_identity_states_present_and_bounded(self):
        model = TriOctaPhaseLockModel(ModelParams())
        s = ModelState(Omega=_OMEGA_ASYM.copy())
        for _ in range(40):
            model.step(s)
        self.assertIn(int(s.cycle_stage), range(0, 7))   # S0..S6
        self.assertIn(int(s.identity_state), range(0, 9))  # s0..s8


# ---------------------------------------------------------------------------
# C6. Continuous deterministic stepping (the heart of `continuous_kernel`)
# ---------------------------------------------------------------------------

class TestContinuousDeterministicSteppingContract(unittest.TestCase):
    def test_step_advances_state_without_external_input(self):
        params = ModelParams()
        model = TriOctaPhaseLockModel(params)
        s = ModelState(Omega=_OMEGA_ASYM.copy())
        core = CognitiveCore()
        cog = CognitiveCoreState()
        omega0 = s.Omega.copy()
        for _ in range(100):
            model.step(s)
            core.update(cog, state=s, params=params)
        # the kernel has its own continuous internal dynamics (no conversation /
        # external input needed): state evolves and stays finite + bounded.
        self.assertEqual(int(s.step), 100)
        self.assertTrue(math.isclose(s.t, 100 * 0.1, rel_tol=1e-9))
        self.assertTrue(np.all(np.isfinite(s.Omega)))
        self.assertFalse(np.allclose(s.Omega, omega0))
        self.assertTrue(-1.0 < float(cog.z_mem) < 1.0)

    def test_default_config_stepping_is_reproducible(self):
        params = ModelParams()  # shared -> identical params on both models
        a = ModelState(Omega=_OMEGA_ASYM.copy())
        b = ModelState(Omega=_OMEGA_ASYM.copy())
        ma = TriOctaPhaseLockModel(params)
        mb = TriOctaPhaseLockModel(params)
        ca = CognitiveCore()
        cb = CognitiveCore()
        csa = CognitiveCoreState()
        csb = CognitiveCoreState()
        for _ in range(100):
            ma.step(a)
            mb.step(b)
            ca.update(csa, state=a, params=params)
            cb.update(csb, state=b, params=params)
        np.testing.assert_allclose(a.Omega, b.Omega, rtol=1e-12, atol=1e-12)
        self.assertEqual(float(a.z), float(b.z))
        self.assertEqual(float(csa.z_mem), float(csb.z_mem))
        self.assertEqual(int(a.cycle_stage), int(b.cycle_stage))
        self.assertEqual(int(a.identity_state), int(b.identity_state))


# ---------------------------------------------------------------------------
# C7. Reconstruction BOUNDARY (HOLD): what the surviving surface does NOT provide
# ---------------------------------------------------------------------------

class TestReconstructionBoundaryHold(unittest.TestCase):
    def test_no_background_tick_state_is_caller_driven(self):
        # The kernel does not advance on its own -- continuous motion is EXPLICIT
        # via step(). A reconstruction must drive stepping; there is no hidden
        # background runtime tick to rely on (and none is added here).
        s = ModelState(Omega=_OMEGA_ASYM.copy())
        omega0 = s.Omega.copy()
        _ = TriOctaPhaseLockModel(ModelParams())  # constructing the model does nothing
        self.assertEqual(int(s.step), 0)
        self.assertEqual(float(s.t), 0.0)
        np.testing.assert_array_equal(s.Omega, omega0)

    def test_seed_world_is_decoupled_from_the_kernel(self):
        # SeedWorld.step() takes NO kernel state: the Z-force coupling between the
        # kernel Z field and the seeds was applied EXTERNALLY in the lost driver
        # script. That coupling is NOT in the surviving surface and stays a
        # future-build boundary (HOLD) -- not implemented here.
        params = list(inspect.signature(SeedWorld.step).parameters)
        self.assertEqual(params, ["self"])
        # a SeedWorld integrates with no reference to any TriOctaPhaseLockModel
        world = SeedWorld()
        world.spawn(born_step=0, channel=0, pos=np.zeros(3), vel=np.ones(3))
        world.step()  # runs without any kernel object
        self.assertEqual(len(world.entities), 1)

    def test_lost_driver_scripts_remain_absent(self):
        for name in ("sim_continuous_kernel.py", "sim_chirality_flip.py",
                     "sim_conversation_shock.py"):
            hits = [p for p in _REPO_ROOT.rglob(name) if "__pycache__" not in p.parts]
            self.assertEqual(hits, [], f"{name} unexpectedly present: {hits}")


if __name__ == "__main__":
    unittest.main()
