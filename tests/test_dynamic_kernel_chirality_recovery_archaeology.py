"""tests/test_dynamic_kernel_chirality_recovery_archaeology.py

Tests-only ARCHAEOLOGY for the dynamic-kernel / chirality / seed-state lane.

After a PC crash lost the three out-of-repo driver scripts
(`sim_continuous_kernel.py`, `sim_chirality_flip.py`, `sim_conversation_shock.py` --
named only in `docs/RESEARCH_simulation_findings.md`, absent as code), this file
characterizes the DETERMINISTIC kernel primitives those sims were built on, which
DO survive in `torment_service/kernel/`. It establishes "source shape still
exists and is structurally usable" before any later reconstruction gate.

Strictly bounded:
  * characterizes only EXISTING public surfaces (`ModelState`, `update_z`,
    `step`, cycle/identity updates, `SeedWorld`) with the default deterministic
    config (`omega_noise_sigma == 0`);
  * uses the documented chirality formula `J_eff = Im(O1 * conj(O2) * O3)` only to
    assert the SIGN relationship to the surviving `z_mem` EMA -- it pins no magic
    constants and infers no lost mechanics;
  * does NOT compare against the PNG curves, does NOT reconstruct the external
    Z-force / conversation-shock / scenario loops, does NOT recreate the three
    sim scripts, and writes no files / plots / fixtures / output.

Scope: tests-only. No production code change. No runtime/coupling expansion.
"""
from __future__ import annotations

import importlib
import math
import unittest
from pathlib import Path

import numpy as np

from torment_service.cognitive_core import CognitiveCore, CognitiveCoreState
from torment_service.kernel.model_core import (
    ModelParams,
    ModelState,
    TriOctaPhaseLockModel,
)
from torment_service.kernel.seed_entities import SeedWorld, SeedEntity

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Documented chirality primitive (cognitive_core): the SIGNED triad area.
_OMEGA_POS_JEFF = np.array([1 + 0j, 1 + 0j, 0 + 1j], dtype=complex)   # Im(1*1*1j)=+1
_OMEGA_NEG_JEFF = np.array([1 + 0j, 1 + 0j, 0 - 1j], dtype=complex)   # Im(1*1*-1j)=-1


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
# 1. Primitives exist and are importable
# ---------------------------------------------------------------------------

class TestPrimitivesImportable(unittest.TestCase):
    def test_core_classes_present(self):
        self.assertTrue(isinstance(TriOctaPhaseLockModel, type))
        self.assertTrue(isinstance(ModelState, type))
        self.assertTrue(isinstance(ModelParams, type))
        self.assertTrue(isinstance(SeedWorld, type))
        self.assertTrue(isinstance(SeedEntity, type))

    def test_relevant_kernel_modules_import(self):
        for mod in (
            "torment_service.kernel",
            "torment_service.kernel.model_core",
            "torment_service.kernel.seed_entities",
            "torment_service.kernel.identity_rules",
            "torment_service.kernel.constants_selector",
        ):
            self.assertIsNotNone(importlib.import_module(mod), mod)

    def test_model_constructs_with_default_params(self):
        model = TriOctaPhaseLockModel(ModelParams())
        # default config is the DETERMINISTIC one (no stochastic forcing)
        self.assertEqual(float(model.p.omega_noise_sigma), 0.0)
        state = ModelState(Omega=_OMEGA_POS_JEFF.copy())
        self.assertEqual(state.Omega.shape, (3,))
        self.assertEqual(float(CognitiveCoreState().z_mem), 0.0)


# ---------------------------------------------------------------------------
# 2. Chirality-memory (z_mem) surface: a slow bounded EMA of normalized J_eff
# ---------------------------------------------------------------------------

class TestChiralityMemorySurface(unittest.TestCase):
    def test_z_mem_moves_toward_jeff_sign(self):
        # positive-chirality Omega -> z_mem moves positive
        sp = _cognitive_response(_OMEGA_POS_JEFF, z_mem0=0.0)
        self.assertGreater(sp.z_mem, 0.0)
        self.assertEqual(math.copysign(1.0, sp.z_mem),
                         math.copysign(1.0, _jeff_norm(_jeff(_OMEGA_POS_JEFF))))
        # negative-chirality Omega -> z_mem moves negative
        sn = _cognitive_response(_OMEGA_NEG_JEFF, z_mem0=0.0)
        self.assertLess(sn.z_mem, 0.0)

    def test_z_mem_is_slow_contractive_memory(self):
        s = _cognitive_response(_OMEGA_POS_JEFF, z_mem0=0.0)
        one_step = s.z_mem
        jn = _jeff_norm(_jeff(_OMEGA_POS_JEFF))
        # a single update moves only a small fraction toward jeff_norm
        self.assertLess(abs(one_step), abs(jn))

    def test_z_mem_accumulates_but_stays_bounded(self):
        after_one = _cognitive_response(_OMEGA_POS_JEFF, z_mem0=0.0).z_mem
        s = _cognitive_response(_OMEGA_POS_JEFF, z_mem0=0.0, n=401)
        jn = _jeff_norm(_jeff(_OMEGA_POS_JEFF))
        # accumulates toward jeff_norm from below, never reaching/exceeding it,
        # and always within the bounded chirality-memory band (-1, 1).
        self.assertGreater(s.z_mem, after_one)
        self.assertLess(s.z_mem, jn)
        self.assertTrue(-1.0 < s.z_mem < 1.0)


# ---------------------------------------------------------------------------
# 3. J_eff-like effective-coupling surface is sign-bearing (chirality)
# ---------------------------------------------------------------------------

class TestJeffEffectiveCouplingSurface(unittest.TestCase):
    def test_jeff_surface_supports_both_signs(self):
        # The chirality surface (signed triad area) can be positive or negative
        # depending on Omega -- the structural prerequisite for "J_eff sign
        # changes". This characterizes only the sign-bearing surface; it does NOT
        # reconstruct any flip-hunting scenario.
        self.assertGreater(_jeff(_OMEGA_POS_JEFF), 0.0)
        self.assertLess(_jeff(_OMEGA_NEG_JEFF), 0.0)

    def test_jeff_norm_is_bounded(self):
        for omega in (_OMEGA_POS_JEFF, _OMEGA_NEG_JEFF,
                      np.array([3 + 2j, -1 + 0j, 0 + 5j], dtype=complex)):
            jn = _jeff_norm(_jeff(omega))
            self.assertTrue(-1.0 < jn < 1.0)


# ---------------------------------------------------------------------------
# 4. Seed position/velocity state (decoupled integrator)
# ---------------------------------------------------------------------------

class TestSeedPositionVelocityState(unittest.TestCase):
    def test_spawn_records_initial_state(self):
        world = SeedWorld(dt=1.0, drag=0.02, drift=np.zeros(3))
        ent = world.spawn(born_step=0, channel=1,
                          pos=np.array([1.0, 0.0, 0.0]), vel=np.array([0.0, 1.0, 0.0]))
        self.assertEqual(ent.channel, 1)
        np.testing.assert_allclose(ent.pos, [1.0, 0.0, 0.0])
        np.testing.assert_allclose(ent.vel, [0.0, 1.0, 0.0])
        np.testing.assert_allclose(ent.vel0, [0.0, 1.0, 0.0])  # frozen at birth

    def test_step_integrates_velocity_and_position_deterministically(self):
        world = SeedWorld(dt=1.0, drag=0.02, drift=np.zeros(3))
        ent = world.spawn(born_step=0, channel=0,
                          pos=np.array([1.0, 0.0, 0.0]), vel=np.array([0.0, 1.0, 0.0]))
        world.step()
        # documented integrator: vel = (1-drag)*vel + drift ; pos += dt*vel
        np.testing.assert_allclose(ent.vel, [0.0, 0.98, 0.0])
        np.testing.assert_allclose(ent.pos, [1.0, 0.98, 0.0])
        # vel0 stays frozen; diagnostic histories grow
        np.testing.assert_allclose(ent.vel0, [0.0, 1.0, 0.0])
        self.assertEqual(len(ent.z_history), 2)
        self.assertGreaterEqual(len(ent.trail), 2)

    def test_seed_world_holds_seed_state_not_omega(self):
        # SeedWorld is the surviving seed-orbit state surface, deliberately
        # decoupled from Omega (no kernel coupling here -- that external coupling
        # is the LOST part and is not reconstructed).
        world = SeedWorld()
        self.assertEqual(world.entities, [])
        world.spawn(born_step=0, channel=2, pos=np.zeros(3), vel=np.ones(3))
        self.assertEqual(len(world.entities), 1)


# ---------------------------------------------------------------------------
# 5. Identity / cycle state surface
# ---------------------------------------------------------------------------

class TestIdentityCycleStateSurface(unittest.TestCase):
    def test_cycle_and_identity_states_in_documented_ranges(self):
        model = TriOctaPhaseLockModel(ModelParams())
        s = ModelState(Omega=np.array([0.5 + 0.3j, 0.2 - 0.4j, 0.6 + 0.1j], dtype=complex))
        for _ in range(40):
            model.step(s)
        # cycle stage S0..S6 -> 0..6 ; identity state s0..s8 -> 0..8
        self.assertIn(int(s.cycle_stage), range(0, 7))
        self.assertIn(int(s.identity_state), range(0, 9))

    def test_cycle_stage_is_monotone_nondecreasing_in_kappa(self):
        model = TriOctaPhaseLockModel(ModelParams())
        lo = ModelState(Omega=np.array([0.1 + 0j, 0.1 + 0j, 0.1 + 0j], dtype=complex))
        hi = ModelState(Omega=np.array([2.0 + 0j, 2.0 + 0j, 2.0 + 0j], dtype=complex))
        model.update_cycle_stage(lo)
        model.update_cycle_stage(hi)
        self.assertLessEqual(lo.kappa(), hi.kappa())
        self.assertLessEqual(int(lo.cycle_stage), int(hi.cycle_stage))


# ---------------------------------------------------------------------------
# 6. Z-vector blend + deterministic stepping (no hidden randomness)
# ---------------------------------------------------------------------------

class TestZVectorBlendAndDeterminism(unittest.TestCase):
    def test_z_vec_is_documented_blend_of_macro_and_chiral(self):
        params = ModelParams()
        model = TriOctaPhaseLockModel(params)
        s = ModelState(Omega=np.array([0.5 + 0.3j, 0.2 - 0.4j, 0.6 + 0.1j], dtype=complex))
        model.update_z(s)
        for v in (s.Z_macro, s.Z_chiral, s.Z_vec):
            self.assertEqual(np.asarray(v).shape, (3,))
        np.testing.assert_allclose(
            s.Z_vec, params.z_alpha * s.Z_macro + params.z_beta * s.Z_chiral, rtol=1e-9)

    def test_default_config_step_is_deterministic(self):
        # omega_noise_sigma == 0 -> no stochastic forcing -> reproducible.
        omega0 = np.array([0.5 + 0.3j, 0.2 - 0.4j, 0.6 + 0.1j], dtype=complex)
        a = ModelState(Omega=omega0.copy())
        b = ModelState(Omega=omega0.copy())
        params = ModelParams()  # shared -> identical params on both models
        ma = TriOctaPhaseLockModel(params)
        mb = TriOctaPhaseLockModel(params)
        ca = CognitiveCore()
        cb = CognitiveCore()
        csa = CognitiveCoreState()
        csb = CognitiveCoreState()
        for _ in range(60):
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
# 7. Non-reconstruction lock: the three lost driver scripts stay absent
# ---------------------------------------------------------------------------

class TestLostScriptsRemainAbsent(unittest.TestCase):
    def test_three_named_sim_scripts_not_recreated(self):
        # This archaeology slice must not (and does not) recreate the lost driver
        # scripts; lock that they remain absent under the package tree.
        for name in ("sim_continuous_kernel.py", "sim_chirality_flip.py",
                     "sim_conversation_shock.py"):
            hits = [p for p in _REPO_ROOT.rglob(name) if "__pycache__" not in p.parts]
            self.assertEqual(hits, [], f"{name} unexpectedly present: {hits}")


if __name__ == "__main__":
    unittest.main()
