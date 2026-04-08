"""Tests for Phase 2A memory-quality tuning pass.

Verifies the three tuned constants:
1. Deep memory min_similarity default raised to 0.40
2. WARMTH_WINDOW_STEPS extended to 400
3. COMPRESS_PERIODIC_FLOOR lowered to 0.40
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torment_service.compression as comp_mod


# =========================================================================
# 1. Deep memory similarity threshold
# =========================================================================

class TestDeepMemorySimilarityThreshold(unittest.TestCase):
    """Verify the default min_similarity is 0.40."""

    def test_query_default_threshold_is_040(self):
        """DeepMemoryStore.query() default min_similarity should be 0.40."""
        import inspect
        from torment_service.deep_memory import DeepMemoryStore

        sig = inspect.signature(DeepMemoryStore.query)
        default = sig.parameters["min_similarity"].default
        self.assertAlmostEqual(default, 0.40, places=2,
                               msg="Deep memory default min_similarity should be 0.40")

    def test_old_threshold_was_030(self):
        """Verify the old default was 0.30 — confirming we changed it."""
        # This test documents the change: 0.30 → 0.40.
        # If someone lowers it back, this test catches it.
        import inspect
        from torment_service.deep_memory import DeepMemoryStore

        sig = inspect.signature(DeepMemoryStore.query)
        default = sig.parameters["min_similarity"].default
        self.assertGreater(default, 0.30,
                           "min_similarity default should be above the old 0.30 value")


# =========================================================================
# 2. Warmth window extension
# =========================================================================

class TestWarmthWindowExtension(unittest.TestCase):
    """Verify WARMTH_WINDOW_STEPS is 400."""

    def test_window_constant_is_400(self):
        """WARMTH_WINDOW_STEPS should be 400."""
        from torment_service.spirit_return import WARMTH_WINDOW_STEPS
        self.assertEqual(WARMTH_WINDOW_STEPS, 400)

    def test_warmth_increases_at_step_300(self):
        """Warmth should increase at step 300 (was outside old 200 window)."""
        from torment_service.spirit_return import compute_warmth, WARMTH_FLOOR
        w = compute_warmth(3, 300)
        self.assertGreater(w, WARMTH_FLOOR,
                           "3 appearances at step 300 should accumulate warmth "
                           "with the extended 400-step window")

    def test_warmth_resets_beyond_400(self):
        """Warmth should reset to floor beyond 400 steps."""
        from torment_service.spirit_return import compute_warmth, WARMTH_FLOOR
        w = compute_warmth(5, 500)
        self.assertAlmostEqual(w, WARMTH_FLOOR,
                               msg="Warmth should reset to floor beyond 400-step window")

    def test_warmth_still_works_within_window(self):
        """Warmth still accumulates normally within the window."""
        from torment_service.spirit_return import (
            compute_warmth, WARMTH_FLOOR, WARMTH_INCREMENT,
        )
        # 2 appearances at step 50 — well within window
        w = compute_warmth(2, 50)
        self.assertAlmostEqual(w, WARMTH_FLOOR + WARMTH_INCREMENT)


# =========================================================================
# 3. Periodic compression floor
# =========================================================================

class TestPeriodicCompressionFloor(unittest.TestCase):
    """Verify COMPRESS_PERIODIC_FLOOR is 0.40."""

    def test_floor_constant_is_040(self):
        """COMPRESS_PERIODIC_FLOOR should be 0.40."""
        self.assertAlmostEqual(comp_mod.COMPRESS_PERIODIC_FLOOR, 0.40, places=2)

    def test_floor_env_override(self):
        """Environment variable can still override the default."""
        import importlib

        old = os.environ.get("TORMENT_COMPRESS_PERIODIC_FLOOR")
        try:
            os.environ["TORMENT_COMPRESS_PERIODIC_FLOOR"] = "0.35"
            importlib.reload(comp_mod)
            self.assertAlmostEqual(comp_mod.COMPRESS_PERIODIC_FLOOR, 0.35, places=2)
        finally:
            if old is None:
                os.environ.pop("TORMENT_COMPRESS_PERIODIC_FLOOR", None)
            else:
                os.environ["TORMENT_COMPRESS_PERIODIC_FLOOR"] = old
            importlib.reload(comp_mod)
            self.assertAlmostEqual(comp_mod.COMPRESS_PERIODIC_FLOOR, 0.40, places=2,
                                   msg="Failed to restore COMPRESS_PERIODIC_FLOOR after env override test")

    def test_candidate_at_045_passes_floor(self):
        """A candidate with score 0.45 should pass the 0.40 floor."""
        from torment_service.compression import COMPRESS_PERIODIC_FLOOR
        score = 0.45
        self.assertGreaterEqual(score, COMPRESS_PERIODIC_FLOOR,
                                "Score 0.45 should pass the lowered 0.40 floor")

    def test_candidate_at_035_fails_floor(self):
        """A candidate with score 0.35 should still fail the 0.40 floor."""
        from torment_service.compression import COMPRESS_PERIODIC_FLOOR
        score = 0.35
        self.assertLess(score, COMPRESS_PERIODIC_FLOOR,
                        "Score 0.35 should still fail the 0.40 floor")


if __name__ == "__main__":
    unittest.main()
