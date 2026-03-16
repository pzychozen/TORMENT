"""
tests/test_srg_integration.py — SRG Phase 5 validation

End-to-end integration tests verifying:
    1. Flag OFF = zero SRG code, no SRG fields
    2. Old memories without SRG still work
    3. Flag ON = SRG state in payload, scoring bonuses, breathing, collision
    4. Compression: crystal never compresses, Class A resists
    5. Spirit return: crystal → resonance, Class A warmth boost
    6. Character band mapping
"""
from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.srg_engine import (
    SRGMemoryState, build_memory_srg, create_crystal_state,
    evolve_breathing, collision as srg_collision,
    golden_tower_frequency, master_equation_gamma,
    detect_character_mode, srg_enabled,
    R_STAR, L_0, GAMMA_SRG, PHI, OMEGA_0,
)


# ============================================================================
# 1. Flag OFF — zero SRG impact
# ============================================================================

class TestFlagOff(unittest.TestCase):
    """When TORMENT_SRG_ENABLE is off, nothing SRG should happen."""

    def setUp(self):
        self._old = os.environ.pop("TORMENT_SRG_ENABLE", None)
        os.environ["TORMENT_SRG_ENABLE"] = "0"

    def tearDown(self):
        if self._old is not None:
            os.environ["TORMENT_SRG_ENABLE"] = self._old
        else:
            os.environ.pop("TORMENT_SRG_ENABLE", None)

    def test_flag_reports_off(self):
        self.assertFalse(srg_enabled())

    def test_compression_ignores_missing_srg(self):
        """CompressionScorer with no SRG key behaves normally."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()
        payload = {
            "summary": "test memory",
            "strength": 0.3, "confidence": 0.5,
            "canon": False, "created_at": 10,
            "half_life": 30.0, "type": "memory",
            "kind": "experience", "tier": "relational",
            "memory_class": "core",
        }
        node = {"eid": 0, "born_step": 10, "payload": payload}
        candidate = scorer.score(node, 200)
        self.assertIsNotNone(candidate)

    def test_compression_ignores_none_srg(self):
        """CompressionScorer with srg=None behaves normally."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()
        payload = {
            "summary": "test memory",
            "strength": 0.3, "confidence": 0.5,
            "canon": False, "created_at": 10,
            "half_life": 30.0, "type": "memory",
            "kind": "experience", "tier": "relational",
            "memory_class": "core",
            "srg": None,
        }
        node = {"eid": 0, "born_step": 10, "payload": payload}
        candidate = scorer.score(node, 200)
        self.assertIsNotNone(candidate)

    def test_spirit_return_no_srg_metadata(self):
        """enrich_deep_memory_hit with no SRG metadata works normally."""
        from torment_service.spirit_return import enrich_deep_memory_hit, WarmupState
        from torment_service.deep_memory import DeepMemory
        dm = DeepMemory(
            eid=1, born_step=100, compressed_step=200,
            summary="test", metadata={"state_symbol": "◠"},
        )
        ws = WarmupState(
            eid=1, first_appearance_step=0, appearance_count=1,
            current_warmth=0.2, max_warmth=0.2, last_retrieved_step=0,
        )
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertIsNotNone(spirit)
        self.assertAlmostEqual(spirit.warmth_score, 0.2)

    def test_character_bands_empty_when_off(self):
        """derive_srg_character_bands returns empty dict when flag off."""
        from torment_service.character import derive_srg_character_bands, CharacterSeed
        seed = CharacterSeed(
            seed_id="test", character_name="TestChar",
            seed_text="A fierce protective guardian who is playful and curious",
        )
        result = derive_srg_character_bands(seed)
        self.assertEqual(result, {})


# ============================================================================
# 2. Backward compatibility — old memories without SRG
# ============================================================================

class TestBackwardCompat(unittest.TestCase):
    """Old memories (pre-SRG) must score, compress, and return normally."""

    def test_scoring_without_srg_payload(self):
        """score_hit doesn't need SRG data."""
        from torment_service.scoring import score_hit
        s = score_hit(sim=0.8, strength=0.6, recency_days=5.0,
                      motif_alignment=0.0, contradiction_risk=0.0)
        self.assertGreater(s, 0.0)

    def test_compression_old_memory(self):
        """Pre-SRG memory compresses normally."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()
        payload = {
            "summary": "old memory from v2.0",
            "strength": 0.2, "confidence": 0.3,
            "canon": False, "created_at": 5,
            "half_life": 20.0, "type": "memory",
            "kind": "experience", "tier": "relational",
            "memory_class": "core",
            # No srg, no phase_duration_steps — old format
        }
        node = {"eid": 0, "born_step": 5, "payload": payload}
        candidate = scorer.score(node, 500)
        self.assertIsNotNone(candidate)

    def test_spirit_return_old_deep_memory(self):
        """Pre-SRG deep memory returns normally."""
        from torment_service.spirit_return import enrich_deep_memory_hit, WarmupState
        from torment_service.deep_memory import DeepMemory
        dm = DeepMemory(
            eid=1, born_step=50, compressed_step=100,
            summary="old deep memory", metadata={"state_symbol": "◯"},
        )
        ws = WarmupState(
            eid=1, first_appearance_step=0, appearance_count=3,
            current_warmth=0.5, max_warmth=0.5, last_retrieved_step=0,
        )
        spirit = enrich_deep_memory_hit(dm, "◯", ws, False)
        self.assertIsNotNone(spirit)
        self.assertIn(spirit.return_mode, ("surfacing", "recollection", "resonance"))

    def test_from_dict_none_graceful(self):
        """SRGMemoryState.from_dict(None) → defaults."""
        s = SRGMemoryState.from_dict(None)
        self.assertEqual(s.R, 0.0)
        self.assertFalse(s.is_crystal)

    def test_from_dict_empty_graceful(self):
        s = SRGMemoryState.from_dict({})
        self.assertEqual(s.R_band, 0)


# ============================================================================
# 3. Flag ON — full e2e SRG path
# ============================================================================

class TestSRGEnabled(unittest.TestCase):
    """With SRG enabled, memories get dual-field state."""

    def setUp(self):
        self._old = os.environ.get("TORMENT_SRG_ENABLE")
        os.environ["TORMENT_SRG_ENABLE"] = "1"

    def tearDown(self):
        if self._old is None:
            os.environ.pop("TORMENT_SRG_ENABLE", None)
        else:
            os.environ["TORMENT_SRG_ENABLE"] = self._old

    def test_flag_reports_on(self):
        self.assertTrue(srg_enabled())

    def test_build_memory_srg_produces_state(self):
        s = build_memory_srg(0.7, 0.8, 15, 42)
        self.assertIsInstance(s, SRGMemoryState)
        self.assertAlmostEqual(s.R, 0.7)
        self.assertGreater(s.gamma, 0)
        self.assertIn(s.heartbeat_class, ("A", "B"))

    def test_build_memory_srg_crystal(self):
        s = build_memory_srg(0.7, 0.8, 15, 42, is_seed=True)
        self.assertTrue(s.is_crystal)
        self.assertAlmostEqual(s.R, R_STAR)
        self.assertEqual(s.R_band, 2)
        self.assertEqual(s.heartbeat_class, "crystal")

    def test_build_with_character_mode(self):
        s = build_memory_srg(0.5, 0.6, 10, 99, character_mode="protector")
        self.assertEqual(s.R_band, 1)
        s2 = build_memory_srg(0.5, 0.6, 10, 99, character_mode="playful")
        self.assertEqual(s2.R_band, 0)
        s3 = build_memory_srg(0.5, 0.6, 10, 99, character_mode="self")
        self.assertEqual(s3.R_band, 2)

    def test_serialise_and_restore(self):
        s = build_memory_srg(0.6, 0.7, 20, 123)
        d = s.to_dict()
        s2 = SRGMemoryState.from_dict(d)
        self.assertAlmostEqual(s2.R, s.R)
        self.assertEqual(s2.R_band, s.R_band)
        self.assertEqual(s2.heartbeat_class, s.heartbeat_class)

    def test_breathing_evolves_L_and_R(self):
        s = build_memory_srg(0.1, 0.7, 10, 42)
        initial_R = s.R
        for _ in range(100):
            evolve_breathing(s)
        self.assertEqual(s.srg_step, 100)
        self.assertNotAlmostEqual(s.L, L_0, places=4)
        self.assertGreater(s.R, initial_R)  # converging toward R*

    def test_crystal_no_breathing(self):
        c = create_crystal_state()
        for _ in range(100):
            evolve_breathing(c)
        self.assertEqual(c.srg_step, 0)
        self.assertEqual(c.L, L_0)
        self.assertAlmostEqual(c.R, R_STAR)

    def test_collision_same_band(self):
        a = build_memory_srg(0.5, 0.7, 10, 100)
        b = build_memory_srg(0.6, 0.8, 15, 200)
        # Force same band
        b.R_band = a.R_band
        report = srg_collision(a, b, 0.85, 50)
        self.assertTrue(report["collision"])
        self.assertTrue(report["rhythm_synced"])
        self.assertEqual(a.last_collision_step, 50)
        self.assertEqual(b.last_collision_step, 50)
        # Incoming adopts existing's heartbeat class
        self.assertEqual(b.heartbeat_class, a.heartbeat_class)

    def test_collision_low_sim_rejected(self):
        a = build_memory_srg(0.5, 0.7, 10, 100)
        b = build_memory_srg(0.6, 0.8, 15, 200)
        b.R_band = a.R_band
        report = srg_collision(a, b, 0.5, 50)
        self.assertFalse(report["collision"])

    def test_collision_distant_bands_rejected(self):
        a = build_memory_srg(0.5, 0.7, 10, 100)
        b = build_memory_srg(0.6, 0.8, 15, 200)
        a.R_band = 0
        b.R_band = 4
        report = srg_collision(a, b, 0.9, 50)
        self.assertFalse(report["collision"])

    def test_character_bands_populated(self):
        from torment_service.character import derive_srg_character_bands, CharacterSeed
        seed = CharacterSeed(
            seed_id="test", character_name="TestChar",
            seed_text="A fierce protective guardian who is playful and curious",
        )
        result = derive_srg_character_bands(seed)
        self.assertIn("dominant_mode", result)
        self.assertIn("band_map", result)
        # Should have detected at least protector and playful
        self.assertIn("protector", result["band_map"])
        self.assertIn("playful", result["band_map"])
        self.assertEqual(result["band_map"]["protector"]["band"], 1)
        self.assertEqual(result["band_map"]["playful"]["band"], 0)


# ============================================================================
# 4. Compression with SRG
# ============================================================================

class TestSRGCompression(unittest.TestCase):

    def _make_node(self, srg_dict=None, strength=0.3):
        payload = {
            "summary": "test memory",
            "strength": strength, "confidence": 0.5,
            "canon": False, "created_at": 10,
            "half_life": 30.0, "type": "memory",
            "kind": "experience", "tier": "relational",
            "memory_class": "core",
        }
        if srg_dict is not None:
            payload["srg"] = srg_dict
        return {"eid": 0, "born_step": 10, "payload": payload}

    def test_crystal_never_compresses(self):
        """Crystal SRG state → compression returns None."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()
        crystal = create_crystal_state()
        node = self._make_node(crystal.to_dict())
        candidate = scorer.score(node, 500)
        self.assertIsNone(candidate)

    def test_class_a_resists_more_than_b(self):
        """Class A memory has lower j_score than Class B."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()

        state_a = build_memory_srg(0.3, 0.5, 10, 42)
        state_a.heartbeat_class = "A"
        state_a.R = 0.10  # below R threshold so only class matters

        state_b = build_memory_srg(0.3, 0.5, 10, 42)
        state_b.heartbeat_class = "B"
        state_b.R = 0.10

        node_a = self._make_node(state_a.to_dict())
        node_b = self._make_node(state_b.to_dict())

        ca = scorer.score(node_a, 500)
        cb = scorer.score(node_b, 500)
        self.assertIsNotNone(ca)
        self.assertIsNotNone(cb)
        self.assertLess(ca.score, cb.score)  # A harder to compress

    def test_high_R_resists_compression(self):
        """Memory near R* resists compression more than fresh memory."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()

        state_high = build_memory_srg(0.3, 0.5, 10, 42)
        state_high.heartbeat_class = "B"
        state_high.R = 0.17  # near R*

        state_low = build_memory_srg(0.3, 0.5, 10, 42)
        state_low.heartbeat_class = "B"
        state_low.R = 0.05  # far from R*

        ch = scorer.score(self._make_node(state_high.to_dict()), 500)
        cl = scorer.score(self._make_node(state_low.to_dict()), 500)
        self.assertIsNotNone(ch)
        self.assertIsNotNone(cl)
        self.assertLess(ch.score, cl.score)

    def test_no_srg_still_compresses(self):
        """Memory without SRG state compresses normally."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()
        node = self._make_node(srg_dict=None)
        candidate = scorer.score(node, 500)
        self.assertIsNotNone(candidate)


# ============================================================================
# 5. Spirit return with SRG
# ============================================================================

class TestSRGSpiritReturn(unittest.TestCase):

    def _make_dm(self, srg_dict=None):
        from torment_service.deep_memory import DeepMemory
        meta = {"state_symbol": "◠"}
        if srg_dict is not None:
            meta["srg"] = srg_dict
        return DeepMemory(
            eid=1, born_step=100, compressed_step=200,
            summary="test", metadata=meta,
        )

    def _make_warmup(self, warmth=0.2):
        from torment_service.spirit_return import WarmupState
        return WarmupState(
            eid=1, first_appearance_step=0, appearance_count=1,
            current_warmth=warmth, max_warmth=warmth, last_retrieved_step=0,
        )

    def test_crystal_forces_resonance(self):
        """Crystal memory always returns in resonance mode."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        crystal = create_crystal_state()
        dm = self._make_dm(crystal.to_dict())
        ws = self._make_warmup(warmth=0.1)  # low warmth normally → recollection
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertEqual(spirit.return_mode, "resonance")

    def test_class_a_warmth_boost(self):
        """Class A heartbeat adds +0.15 to warmth."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        state = build_memory_srg(0.5, 0.7, 10, 42)
        state.heartbeat_class = "A"
        dm = self._make_dm(state.to_dict())
        ws = self._make_warmup(warmth=0.2)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertGreaterEqual(spirit.warmth_score, 0.35)  # 0.2 + 0.15

    def test_class_b_no_warmth_boost(self):
        """Class B heartbeat doesn't boost warmth."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        state = build_memory_srg(0.5, 0.7, 10, 42)
        state.heartbeat_class = "B"
        dm = self._make_dm(state.to_dict())
        ws = self._make_warmup(warmth=0.2)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertAlmostEqual(spirit.warmth_score, 0.2)

    def test_warmth_boost_doesnt_exceed_1(self):
        """Warmth boost caps at 1.0."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        state = build_memory_srg(0.5, 0.7, 10, 42)
        state.heartbeat_class = "A"
        dm = self._make_dm(state.to_dict())
        ws = self._make_warmup(warmth=0.95)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertLessEqual(spirit.warmth_score, 1.0)

    def test_no_srg_no_boost(self):
        """Memory without SRG metadata returns normally."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        dm = self._make_dm(srg_dict=None)
        ws = self._make_warmup(warmth=0.2)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertAlmostEqual(spirit.warmth_score, 0.2)
        self.assertIn(spirit.return_mode, ("surfacing", "recollection", "resonance"))


# ============================================================================
# 6. Golden tower math validation against paper
# ============================================================================

class TestGoldenTowerMath(unittest.TestCase):
    """Validate SRG constants and equations against paper values."""

    def test_lock_equation(self):
        """πeφ = γ⁻¹ζ(3) → γ_srg ≈ 0.08699."""
        lock = math.pi * math.e * PHI
        gamma = 1.2020569031595942 / lock  # ζ(3) / πeφ
        self.assertAlmostEqual(gamma, GAMMA_SRG, places=8)
        self.assertAlmostEqual(gamma, 0.08699, places=4)

    def test_master_equation_at_omega_0(self):
        """At ω₀: s=3, so γ(ω₀) = ζ(3)/πeφ = γ_srg."""
        g = master_equation_gamma(OMEGA_0)
        self.assertAlmostEqual(g, GAMMA_SRG, places=4)

    def test_golden_tower_phi_spacing(self):
        """ω_n / ω_{n-1} = φ for all bands."""
        for i in range(4):
            ratio = golden_tower_frequency(i + 1) / golden_tower_frequency(i)
            self.assertAlmostEqual(ratio, PHI, places=8)

    def test_band_0_equals_omega_0(self):
        self.assertAlmostEqual(golden_tower_frequency(0), OMEGA_0, places=8)

    def test_r_star_convergence(self):
        """R converges toward R* ≈ 0.176 from any starting point."""
        # From below
        s1 = SRGMemoryState(R=0.0, gamma=GAMMA_SRG)
        for _ in range(10000):
            evolve_breathing(s1)
        self.assertAlmostEqual(s1.R, R_STAR, delta=0.01)

        # From above
        s2 = SRGMemoryState(R=1.0, gamma=GAMMA_SRG)
        for _ in range(10000):
            evolve_breathing(s2)
        self.assertAlmostEqual(s2.R, R_STAR, delta=0.01)

    def test_breathing_self_sustaining(self):
        """L oscillates continuously — doesn't decay to flat."""
        s = SRGMemoryState(R=0.1, L=L_0, L_amplitude=0.3,
                           heartbeat_class="B", gamma=GAMMA_SRG)
        l_values = set()
        for _ in range(500):
            evolve_breathing(s)
            l_values.add(round(s.L, 6))
        # Should have many distinct L values (oscillating, not flat)
        self.assertGreater(len(l_values), 20)

    def test_class_a_b_different_frequencies(self):
        """Class A and B produce different oscillation patterns."""
        sa = SRGMemoryState(R=0.1, L=L_0, L_amplitude=0.3,
                            heartbeat_class="A", gamma=GAMMA_SRG)
        sb = SRGMemoryState(R=0.1, L=L_0, L_amplitude=0.3,
                            heartbeat_class="B", gamma=GAMMA_SRG)
        la, lb = [], []
        for _ in range(200):
            evolve_breathing(sa)
            evolve_breathing(sb)
            la.append(round(sa.L, 6))
            lb.append(round(sb.L, 6))
        # They should differ (different frequencies)
        self.assertNotEqual(la, lb)


# ============================================================================
# 7. Collision physics validation
# ============================================================================

class TestCollisionPhysicsValidation(unittest.TestCase):

    def test_rhythm_sync_post_collision(self):
        """After collision, incoming has same heartbeat class and phase as existing."""
        a = SRGMemoryState(R=0.1, R_band=0, heartbeat_class="A",
                           L_phase=-1.1, L=9.0)
        b = SRGMemoryState(R=0.15, R_band=0, heartbeat_class="B",
                           L_phase=-1.9, L=9.3)
        report = srg_collision(a, b, 0.85, 100)
        self.assertTrue(report["collision"])
        self.assertEqual(b.heartbeat_class, "A")
        self.assertEqual(b.L_phase, a.L_phase)

    def test_amplitude_preserved(self):
        """R values remain distinct after collision (7.25% diversity)."""
        a = SRGMemoryState(R=0.10, R_band=0, L=9.0)
        b = SRGMemoryState(R=0.15, R_band=0, L=9.5)
        srg_collision(a, b, 0.85, 100)
        # b.R unchanged, a.R shifted slightly
        self.assertAlmostEqual(b.R, 0.15)
        self.assertNotAlmostEqual(a.R, b.R, places=3)

    def test_delta_L_determines_stabilization(self):
        """Larger ΔL → faster stabilization (r = -0.42)."""
        a1 = SRGMemoryState(R=0.1, R_band=0, L=9.0)
        b1 = SRGMemoryState(R=0.15, R_band=0, L=9.1)
        r1 = srg_collision(a1, b1, 0.85, 100)

        a2 = SRGMemoryState(R=0.1, R_band=0, L=9.0)
        b2 = SRGMemoryState(R=0.15, R_band=0, L=11.0)
        r2 = srg_collision(a2, b2, 0.85, 100)

        self.assertGreater(r2["stabilization_speed"], r1["stabilization_speed"])

    def test_delta_L_determines_equilibrium(self):
        """Larger ΔL → larger equilibrium shift (r = -0.86)."""
        a1 = SRGMemoryState(R=0.1, R_band=0, L=9.0)
        b1 = SRGMemoryState(R=0.15, R_band=0, L=9.1)
        r1_before = a1.R
        srg_collision(a1, b1, 0.85, 100)
        shift1 = abs(a1.R - r1_before)

        a2 = SRGMemoryState(R=0.1, R_band=0, L=9.0)
        b2 = SRGMemoryState(R=0.15, R_band=0, L=11.0)
        r2_before = a2.R
        srg_collision(a2, b2, 0.85, 100)
        shift2 = abs(a2.R - r2_before)

        self.assertGreater(shift2, shift1)


# ============================================================================
# 8. Character mode detection
# ============================================================================

class TestCharacterModeDetectionIntegration(unittest.TestCase):

    def test_playful_text(self):
        self.assertEqual(
            detect_character_mode("playful and curious about everything"),
            "playful"
        )

    def test_protector_text(self):
        self.assertEqual(
            detect_character_mode("fierce protective guardian with intensity"),
            "protector"
        )

    def test_self_text(self):
        self.assertEqual(
            detect_character_mode("the core bond that is authentic and true"),
            "self"
        )

    def test_mixed_text_highest_wins(self):
        mode = detect_character_mode(
            "fierce protective loyal guardian who is also playful"
        )
        # protector: fierce, protective, loyal, guardian = 4 hits
        # playful: playful = 1 hit
        self.assertEqual(mode, "protector")

    def test_generic_text_empty(self):
        self.assertEqual(detect_character_mode("hello how are you today"), "")


if __name__ == "__main__":
    unittest.main()
