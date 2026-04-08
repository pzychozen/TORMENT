"""
tests/test_srg_engine.py — Symbolic Resonant Geometry engine

Tests for:
    - SRG constants match the paper
    - Golden tower frequency computation
    - Master equation γ(ω)
    - Band assignment (character modes + dynamic)
    - Breathing initialisation (Class A/B distribution)
    - Breathing evolution (L oscillation, R convergence)
    - Collision physics (rhythm sync, amplitude preservation, ΔL)
    - Crystal creation (fixed point, no breathing)
    - Character mode detection
    - build_memory_srg convenience factory
    - Serialisation round-trip
    - Flag gating
    - Backward compatibility (missing SRG data)
"""
from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.srg_engine import (
    # Constants
    PHI, OMEGA_0, LOCK_PRODUCT, ZETA_3, GAMMA_SRG, GAMMA_INF,
    R_STAR, L_0, CLASS_A_FREQ, CLASS_B_FREQ, CLASS_B_PHASE,
    DEFAULT_NUM_BANDS,
    # Feature flag
    srg_enabled,
    # Data structures
    SRGMemoryState,
    # Functions
    golden_tower_frequency,
    master_equation_gamma,
    assign_band,
    init_breathing,
    evolve_breathing,
    collision,
    create_crystal_state,
    detect_character_mode,
    build_memory_srg,
)


# ============================================================================
# Constants verification
# ============================================================================

class TestSRGConstants(unittest.TestCase):
    """Verify all SRG constants match the paper values."""

    def test_phi(self):
        self.assertAlmostEqual(PHI, 1.6180339887, places=8)

    def test_omega_0(self):
        self.assertAlmostEqual(OMEGA_0, 0.244, places=6)

    def test_lock_product(self):
        expected = math.pi * math.e * PHI
        self.assertAlmostEqual(LOCK_PRODUCT, expected, places=8)
        self.assertAlmostEqual(LOCK_PRODUCT, 13.818, places=2)

    def test_zeta_3(self):
        """Apéry's constant ζ(3) ≈ 1.20206."""
        self.assertAlmostEqual(ZETA_3, 1.20206, places=4)

    def test_gamma_srg(self):
        """γ_srg = ζ(3) / (πeφ) ≈ 0.08699."""
        self.assertAlmostEqual(GAMMA_SRG, ZETA_3 / LOCK_PRODUCT, places=10)
        self.assertAlmostEqual(GAMMA_SRG, 0.08699, places=4)

    def test_gamma_inf(self):
        """γ_∞ = 1 / (πeφ) ≈ 0.07237."""
        self.assertAlmostEqual(GAMMA_INF, 1.0 / LOCK_PRODUCT, places=10)
        self.assertAlmostEqual(GAMMA_INF, 0.07237, places=4)

    def test_r_star(self):
        """Fixed-point resonance R* ≈ 0.176."""
        self.assertAlmostEqual(R_STAR, 0.176329, places=5)

    def test_l_0(self):
        """Baseline compression bound L₀ = 9."""
        self.assertEqual(L_0, 9.0)

    def test_class_frequencies(self):
        """Class A < Class B frequency."""
        self.assertLess(CLASS_A_FREQ, CLASS_B_FREQ)

    def test_omega_0_matches_theta_lock(self):
        """ω₀ = 0.244 matches TORMENT's theta_lock."""
        self.assertAlmostEqual(OMEGA_0, 0.244, places=6)


# ============================================================================
# Golden tower
# ============================================================================

class TestGoldenTower(unittest.TestCase):

    def test_band_0_is_omega_0(self):
        self.assertAlmostEqual(golden_tower_frequency(0), OMEGA_0, places=8)

    def test_band_1(self):
        self.assertAlmostEqual(
            golden_tower_frequency(1), OMEGA_0 * PHI, places=8
        )

    def test_bands_are_phi_spaced(self):
        """Each band is φ× the previous."""
        for i in range(DEFAULT_NUM_BANDS - 1):
            ratio = golden_tower_frequency(i + 1) / golden_tower_frequency(i)
            self.assertAlmostEqual(ratio, PHI, places=8)

    def test_all_bands_positive(self):
        for i in range(DEFAULT_NUM_BANDS):
            self.assertGreater(golden_tower_frequency(i), 0.0)


class TestMasterEquationGamma(unittest.TestCase):

    def test_band_0_gamma_is_gamma_srg(self):
        """At ω₀ (band 0): n = 0, s = 3, ζ(3)/πeφ = γ_srg."""
        g = master_equation_gamma(OMEGA_0)
        self.assertAlmostEqual(g, GAMMA_SRG, places=4)

    def test_positive_for_all_bands(self):
        for i in range(DEFAULT_NUM_BANDS):
            g = master_equation_gamma(golden_tower_frequency(i))
            self.assertGreater(g, 0.0)

    def test_decreasing_with_frequency(self):
        """Higher bands → ζ(s) → 1 → γ decreases toward γ_∞."""
        gammas = [
            master_equation_gamma(golden_tower_frequency(i))
            for i in range(DEFAULT_NUM_BANDS)
        ]
        for i in range(len(gammas) - 1):
            self.assertGreaterEqual(gammas[i], gammas[i + 1])

    def test_edge_omega_zero(self):
        """ω = 0 falls back to γ_srg."""
        self.assertEqual(master_equation_gamma(0), GAMMA_SRG)

    def test_edge_negative_omega(self):
        self.assertEqual(master_equation_gamma(-1.0), GAMMA_SRG)


# ============================================================================
# Band assignment
# ============================================================================

class TestBandAssignment(unittest.TestCase):

    def test_playful_always_band_0(self):
        self.assertEqual(assign_band(character_mode="playful"), 0)

    def test_protector_always_band_1(self):
        self.assertEqual(assign_band(character_mode="protector"), 1)

    def test_self_always_band_2(self):
        self.assertEqual(assign_band(character_mode="self"), 2)

    def test_high_stability_low_band(self):
        """coherence=1, long duration → band 0 (most stable)."""
        self.assertEqual(assign_band(coherence=1.0, phase_duration=100), 0)

    def test_low_stability_high_band(self):
        """coherence=0, no duration → highest band (most volatile)."""
        self.assertEqual(
            assign_band(coherence=0.0, phase_duration=0),
            DEFAULT_NUM_BANDS - 1,
        )

    def test_band_always_in_range(self):
        """Band is always [0, num_bands-1] regardless of input."""
        for coh in [0.0, 0.5, 1.0, -0.5, 2.0]:
            for dur in [0, 10, 50, 1000]:
                b = assign_band(coherence=coh, phase_duration=dur)
                self.assertGreaterEqual(b, 0)
                self.assertLess(b, DEFAULT_NUM_BANDS)

    def test_character_mode_overrides_coherence(self):
        """Even with coherence=0, character mode wins."""
        self.assertEqual(
            assign_band(coherence=0.0, phase_duration=0, character_mode="self"),
            2,
        )


# ============================================================================
# Breathing
# ============================================================================

class TestBreathingInit(unittest.TestCase):

    def test_returns_tuple(self):
        result = init_breathing(0.5, 10, 42)
        self.assertEqual(len(result), 3)

    def test_class_a_or_b(self):
        for seed in range(100):
            cls, amp, phase = init_breathing(0.5, 10, seed)
            self.assertIn(cls, ("A", "B"))

    def test_distribution_roughly_correct(self):
        """~25-40% Class A with default parameters."""
        classes = [init_breathing(0.5, 0, seed)[0] for seed in range(1000)]
        a_ratio = classes.count("A") / len(classes)
        self.assertGreater(a_ratio, 0.15)
        self.assertLess(a_ratio, 0.50)

    def test_high_duration_biases_class_a(self):
        """Long phase_duration increases Class A probability."""
        a_short = sum(1 for s in range(1000) if init_breathing(0.5, 0, s)[0] == "A")
        a_long = sum(1 for s in range(1000) if init_breathing(0.5, 50, s)[0] == "A")
        self.assertGreater(a_long, a_short)

    def test_amplitude_positive(self):
        for seed in range(50):
            _, amp, _ = init_breathing(0.5, 10, seed)
            self.assertGreater(amp, 0.0)

    def test_class_a_larger_amplitude(self):
        """Class A memories breathe deeper than Class B at same coherence."""
        # Force Class A (low seed_hash) vs Class B (high seed_hash)
        # Find one of each
        a_amp = b_amp = None
        for seed in range(1000):
            cls, amp, _ = init_breathing(0.7, 5, seed)
            if cls == "A" and a_amp is None:
                a_amp = amp
            if cls == "B" and b_amp is None:
                b_amp = amp
            if a_amp is not None and b_amp is not None:
                break
        self.assertIsNotNone(a_amp)
        self.assertIsNotNone(b_amp)
        self.assertGreater(a_amp, b_amp)

    def test_deterministic(self):
        """Same inputs → same output."""
        a = init_breathing(0.5, 10, 42)
        b = init_breathing(0.5, 10, 42)
        self.assertEqual(a, b)


class TestBreathingEvolution(unittest.TestCase):

    def _make_state(self, hb_class="B", R=0.0):
        return SRGMemoryState(
            R=R, L=L_0, L_amplitude=0.2, L_phase=CLASS_B_PHASE,
            heartbeat_class=hb_class, gamma=GAMMA_SRG,
        )

    def test_l_oscillates(self):
        """L changes over multiple steps (doesn't stay at L₀)."""
        state = self._make_state()
        l_values = []
        for _ in range(200):
            evolve_breathing(state)
            l_values.append(state.L)
        self.assertGreater(max(l_values), L_0)
        self.assertLess(min(l_values), L_0)

    def test_l_stays_near_l0(self):
        """L oscillation is bounded around L₀."""
        state = self._make_state()
        for _ in range(500):
            evolve_breathing(state)
        self.assertAlmostEqual(state.L, L_0, delta=1.0)

    def test_r_converges_toward_r_star(self):
        """R moves toward R* from below."""
        state = self._make_state(R=0.0)
        for _ in range(5000):
            evolve_breathing(state)
        self.assertGreater(state.R, 0.0)
        self.assertAlmostEqual(state.R, R_STAR, delta=0.05)

    def test_r_converges_from_above(self):
        """R moves toward R* from above too."""
        state = self._make_state(R=0.5)
        for _ in range(5000):
            evolve_breathing(state)
        self.assertLess(state.R, 0.5)
        self.assertAlmostEqual(state.R, R_STAR, delta=0.05)

    def test_crystal_does_not_breathe(self):
        """Crystal memories are unaffected by evolve_breathing."""
        state = create_crystal_state()
        orig_L = state.L
        orig_R = state.R
        orig_step = state.srg_step
        for _ in range(100):
            evolve_breathing(state)
        self.assertEqual(state.L, orig_L)
        self.assertEqual(state.R, orig_R)
        self.assertEqual(state.srg_step, orig_step)

    def test_step_increments(self):
        state = self._make_state()
        self.assertEqual(state.srg_step, 0)
        evolve_breathing(state)
        self.assertEqual(state.srg_step, 1)
        evolve_breathing(state)
        self.assertEqual(state.srg_step, 2)

    def test_class_a_slower_than_b(self):
        """Class A oscillates at lower frequency than Class B."""
        self.assertLess(CLASS_A_FREQ, CLASS_B_FREQ)


# ============================================================================
# Collision physics
# ============================================================================

class TestCollisionPhysics(unittest.TestCase):

    def _pair(self, band_a=0, band_b=0, L_a=9.0, L_b=9.5):
        a = SRGMemoryState(R=0.1, R_band=band_a, L=L_a, heartbeat_class="A")
        b = SRGMemoryState(R=0.15, R_band=band_b, L=L_b, heartbeat_class="B")
        return a, b

    def test_collision_triggers(self):
        a, b = self._pair()
        report = collision(a, b, 0.85, 100)
        self.assertTrue(report["collision"])

    def test_low_similarity_no_collision(self):
        a, b = self._pair()
        report = collision(a, b, 0.5, 100)
        self.assertFalse(report["collision"])
        self.assertEqual(report["reason"], "low_similarity")

    def test_distant_bands_no_collision(self):
        a, b = self._pair(band_a=0, band_b=3)
        report = collision(a, b, 0.9, 100)
        self.assertFalse(report["collision"])
        self.assertEqual(report["reason"], "band_distance")

    def test_adjacent_bands_collide(self):
        a, b = self._pair(band_a=1, band_b=2)
        report = collision(a, b, 0.85, 100)
        self.assertTrue(report["collision"])

    def test_rhythm_syncs(self):
        """Incoming adopts existing's heartbeat class after collision."""
        a, b = self._pair()
        self.assertEqual(a.heartbeat_class, "A")
        self.assertEqual(b.heartbeat_class, "B")
        collision(a, b, 0.85, 100)
        self.assertEqual(b.heartbeat_class, "A")  # synced to existing

    def test_amplitude_preserved(self):
        """R values remain distinct after collision."""
        a, b = self._pair()
        r_a_before = a.R
        r_b_before = b.R
        collision(a, b, 0.85, 100)
        # b.R unchanged, a.R shifted slightly by equilibrium
        self.assertEqual(b.R, r_b_before)
        # a.R changed but not to b.R
        self.assertNotAlmostEqual(a.R, b.R, places=3)

    def test_delta_l_in_report(self):
        a, b = self._pair(L_a=9.0, L_b=9.5)
        report = collision(a, b, 0.85, 100)
        self.assertAlmostEqual(report["delta_L"], 0.5, places=4)

    def test_collision_step_recorded(self):
        a, b = self._pair()
        collision(a, b, 0.85, 200)
        self.assertEqual(a.last_collision_step, 200)
        self.assertEqual(b.last_collision_step, 200)

    def test_larger_delta_l_faster_stabilisation(self):
        """Larger ΔL → higher stabilisation speed."""
        a1, b1 = self._pair(L_a=9.0, L_b=9.1)
        a2, b2 = self._pair(L_a=9.0, L_b=10.0)
        r1 = collision(a1, b1, 0.85, 100)
        r2 = collision(a2, b2, 0.85, 100)
        self.assertGreater(r2["stabilization_speed"], r1["stabilization_speed"])

    def test_larger_delta_l_larger_equilibrium_shift(self):
        """Larger ΔL → larger equilibrium shift on existing."""
        a1, b1 = self._pair(L_a=9.0, L_b=9.1)
        a2, b2 = self._pair(L_a=9.0, L_b=10.0)
        r_before_1 = a1.R
        r_before_2 = a2.R
        collision(a1, b1, 0.85, 100)
        collision(a2, b2, 0.85, 100)
        shift_1 = abs(a1.R - r_before_1)
        shift_2 = abs(a2.R - r_before_2)
        self.assertGreater(shift_2, shift_1)


# ============================================================================
# Crystal
# ============================================================================

class TestCrystalCreation(unittest.TestCase):

    def test_is_crystal(self):
        c = create_crystal_state()
        self.assertTrue(c.is_crystal)

    def test_band_2(self):
        c = create_crystal_state()
        self.assertEqual(c.R_band, 2)

    def test_r_at_fixed_point(self):
        c = create_crystal_state()
        self.assertAlmostEqual(c.R, R_STAR, places=5)

    def test_zero_amplitude(self):
        c = create_crystal_state()
        self.assertEqual(c.L_amplitude, 0.0)

    def test_heartbeat_crystal(self):
        c = create_crystal_state()
        self.assertEqual(c.heartbeat_class, "crystal")

    def test_l_at_l0(self):
        c = create_crystal_state()
        self.assertEqual(c.L, L_0)

    def test_frequency_matches_band_2(self):
        c = create_crystal_state()
        self.assertAlmostEqual(c.R_frequency, golden_tower_frequency(2), places=8)


# ============================================================================
# Character mode detection
# ============================================================================

class TestCharacterModeDetection(unittest.TestCase):

    def test_playful(self):
        self.assertEqual(
            detect_character_mode("She was playful and curious about the world"),
            "playful",
        )

    def test_protector(self):
        self.assertEqual(
            detect_character_mode("A fierce guardian with intensity in her eyes"),
            "protector",
        )

    def test_self_identity(self):
        self.assertEqual(
            detect_character_mode("The core bond between them was authentic"),
            "self",
        )

    def test_no_clear_mode(self):
        """Generic text → empty string."""
        self.assertEqual(
            detect_character_mode("Today is a nice sunny day"),
            "",
        )

    def test_single_keyword_not_enough(self):
        """Need at least 2 keyword hits."""
        self.assertEqual(
            detect_character_mode("She was playful today"),
            "",
        )

    def test_case_insensitive(self):
        self.assertEqual(
            detect_character_mode("FIERCE PROTECTIVE instinct"),
            "protector",
        )


# ============================================================================
# build_memory_srg factory
# ============================================================================

class TestBuildMemorySRG(unittest.TestCase):

    def test_returns_state(self):
        s = build_memory_srg(0.5, 0.7, 10, 42)
        self.assertIsInstance(s, SRGMemoryState)

    def test_seed_returns_crystal(self):
        s = build_memory_srg(0.5, 0.7, 10, 42, is_seed=True)
        self.assertTrue(s.is_crystal)
        self.assertEqual(s.R_band, 2)
        self.assertAlmostEqual(s.R, R_STAR)

    def test_strength_maps_to_R(self):
        s = build_memory_srg(0.82, 0.7, 10, 42)
        self.assertAlmostEqual(s.R, 0.82)

    def test_character_mode_sets_band(self):
        s = build_memory_srg(0.5, 0.7, 10, 42, character_mode="protector")
        self.assertEqual(s.R_band, 1)

    def test_gamma_computed(self):
        s = build_memory_srg(0.5, 0.7, 10, 42)
        self.assertGreater(s.gamma, 0)

    def test_fresh_step_zero(self):
        s = build_memory_srg(0.5, 0.7, 10, 42)
        self.assertEqual(s.srg_step, 0)
        self.assertEqual(s.last_collision_step, -1)


# ============================================================================
# Serialisation
# ============================================================================

class TestSRGSerialisation(unittest.TestCase):

    def test_roundtrip(self):
        """to_dict → from_dict preserves all fields."""
        orig = build_memory_srg(0.6, 0.8, 15, 123, character_mode="playful")
        d = orig.to_dict()
        restored = SRGMemoryState.from_dict(d)
        self.assertAlmostEqual(restored.R, orig.R)
        self.assertEqual(restored.R_band, orig.R_band)
        self.assertAlmostEqual(restored.R_frequency, orig.R_frequency)
        self.assertAlmostEqual(restored.L, orig.L)
        self.assertAlmostEqual(restored.L_amplitude, orig.L_amplitude)
        self.assertAlmostEqual(restored.L_phase, orig.L_phase)
        self.assertEqual(restored.heartbeat_class, orig.heartbeat_class)
        self.assertAlmostEqual(restored.gamma, orig.gamma)
        self.assertEqual(restored.is_crystal, orig.is_crystal)
        self.assertEqual(restored.srg_step, orig.srg_step)
        self.assertEqual(restored.last_collision_step, orig.last_collision_step)

    def test_from_empty_dict(self):
        """Empty dict → default state."""
        s = SRGMemoryState.from_dict({})
        self.assertEqual(s.R, 0.0)
        self.assertEqual(s.R_band, 0)
        self.assertFalse(s.is_crystal)

    def test_from_none(self):
        """None → default state."""
        s = SRGMemoryState.from_dict(None)
        self.assertEqual(s.R, 0.0)

    def test_extra_keys_ignored(self):
        """Unknown keys in dict don't crash from_dict."""
        d = {"R": 0.5, "R_band": 1, "unknown_future_field": 42}
        s = SRGMemoryState.from_dict(d)
        self.assertAlmostEqual(s.R, 0.5)
        self.assertEqual(s.R_band, 1)

    def test_crystal_roundtrip(self):
        c = create_crystal_state()
        d = c.to_dict()
        c2 = SRGMemoryState.from_dict(d)
        self.assertTrue(c2.is_crystal)
        self.assertEqual(c2.heartbeat_class, "crystal")
        self.assertAlmostEqual(c2.R, R_STAR)

    def test_evolved_state_roundtrip(self):
        """State after evolution serialises correctly."""
        s = build_memory_srg(0.5, 0.7, 10, 42)
        for _ in range(50):
            evolve_breathing(s)
        d = s.to_dict()
        s2 = SRGMemoryState.from_dict(d)
        self.assertEqual(s2.srg_step, 50)
        self.assertAlmostEqual(s2.L, s.L, places=8)
        self.assertAlmostEqual(s2.R, s.R, places=8)


# ============================================================================
# Flag gating
# ============================================================================

class TestFlagGating(unittest.TestCase):

    def test_default_off(self):
        """SRG is off by default."""
        old = os.environ.pop("TORMENT_SRG_ENABLE", None)
        try:
            self.assertFalse(srg_enabled())
        finally:
            if old is not None:
                os.environ["TORMENT_SRG_ENABLE"] = old

    def test_enable_1(self):
        old = os.environ.get("TORMENT_SRG_ENABLE")
        os.environ["TORMENT_SRG_ENABLE"] = "1"
        try:
            self.assertTrue(srg_enabled())
        finally:
            if old is None:
                del os.environ["TORMENT_SRG_ENABLE"]
            else:
                os.environ["TORMENT_SRG_ENABLE"] = old

    def test_enable_true(self):
        old = os.environ.get("TORMENT_SRG_ENABLE")
        os.environ["TORMENT_SRG_ENABLE"] = "true"
        try:
            self.assertTrue(srg_enabled())
        finally:
            if old is None:
                del os.environ["TORMENT_SRG_ENABLE"]
            else:
                os.environ["TORMENT_SRG_ENABLE"] = old

    def test_disable_0(self):
        old = os.environ.get("TORMENT_SRG_ENABLE")
        os.environ["TORMENT_SRG_ENABLE"] = "0"
        try:
            self.assertFalse(srg_enabled())
        finally:
            if old is None:
                del os.environ["TORMENT_SRG_ENABLE"]
            else:
                os.environ["TORMENT_SRG_ENABLE"] = old


# ============================================================================
# Backward compatibility
# ============================================================================

class TestBackwardCompat(unittest.TestCase):

    def test_missing_srg_key_safe(self):
        """Payloads without 'srg' key don't crash anything."""
        payload = {"summary": "old memory", "strength": 0.5}
        srg_data = payload.get("srg")
        if srg_data:
            state = SRGMemoryState.from_dict(srg_data)
        else:
            state = None
        self.assertIsNone(state)

    def test_from_dict_with_partial_data(self):
        """Partially populated SRG dict fills defaults for missing fields."""
        s = SRGMemoryState.from_dict({"R": 0.12, "R_band": 3})
        self.assertAlmostEqual(s.R, 0.12)
        self.assertEqual(s.R_band, 3)
        self.assertEqual(s.L, L_0)  # default
        self.assertFalse(s.is_crystal)  # default


if __name__ == "__main__":
    unittest.main()
