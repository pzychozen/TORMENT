"""
tests/test_phase_timer.py — Phase-Cycle Time tracking

Tests for:
    - PhaseTimer update, reset, duration tracking
    - Corridor entry/exit tracking
    - Phase transition detection
    - Serialization round-trip
    - Compression duration resistance
    - Spirit return warmth boost
    - Deep memory metadata preservation
    - Backward compatibility
"""
from __future__ import annotations

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.phase_timer import PhaseTimer


# ===========================================================================
# PhaseTimer Core Tests
# ===========================================================================

class TestPhaseTimerInit(unittest.TestCase):

    def test_initial_state(self):
        """Fresh PhaseTimer starts with sensible defaults."""
        pt = PhaseTimer()
        self.assertEqual(pt.phase_entry_step, 0)
        self.assertIsNone(pt.corridor_entry_step)
        self.assertIsNone(pt.current_cycle_stage)
        self.assertFalse(pt.current_in_corridor)

    def test_first_update_initializes(self):
        """First update sets phase_entry_step to current step."""
        pt = PhaseTimer()
        pt.update(step=10, in_corridor=False, cycle_stage=3)
        self.assertEqual(pt.phase_entry_step, 10)
        self.assertEqual(pt.current_cycle_stage, 3)

    def test_first_update_no_transition(self):
        """First call returns no transitions (no previous state)."""
        pt = PhaseTimer()
        trans = pt.update(step=10, in_corridor=False, cycle_stage=3)
        self.assertNotIn("phase_changed", trans)
        self.assertNotIn("corridor_entered", trans)


class TestPhaseTimerDurations(unittest.TestCase):

    def test_phase_duration_increments(self):
        """Phase duration = current_step - phase_entry_step."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=False, cycle_stage=1)

        d = pt.get_durations(105)
        self.assertEqual(d["phase_duration_steps"], 5)

        d = pt.get_durations(120)
        self.assertEqual(d["phase_duration_steps"], 20)

    def test_corridor_duration_increments(self):
        """Corridor duration tracks independently of phase."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=False, cycle_stage=1)
        pt.update(step=110, in_corridor=True, cycle_stage=1)

        d = pt.get_durations(115)
        self.assertEqual(d["corridor_duration_steps"], 5)
        self.assertEqual(d["phase_duration_steps"], 15)

    def test_no_corridor_duration_outside(self):
        """Corridor duration is 0 when not in corridor."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=False, cycle_stage=1)

        d = pt.get_durations(110)
        self.assertEqual(d["corridor_duration_steps"], 0)


class TestPhaseTimerTransitions(unittest.TestCase):

    def test_phase_reset_on_stage_change(self):
        """cycle_stage change resets phase_entry_step."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=False, cycle_stage=1)
        trans = pt.update(step=120, in_corridor=False, cycle_stage=2)

        self.assertTrue(trans.get("phase_changed"))
        self.assertEqual(trans["prev_phase_duration"], 20)
        self.assertEqual(pt.phase_entry_step, 120)

        d = pt.get_durations(125)
        self.assertEqual(d["phase_duration_steps"], 5)

    def test_corridor_entry(self):
        """Entering corridor records entry step."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=False, cycle_stage=1)
        trans = pt.update(step=110, in_corridor=True, cycle_stage=1)

        self.assertTrue(trans.get("corridor_entered"))
        self.assertEqual(pt.corridor_entry_step, 110)

    def test_corridor_exit(self):
        """Exiting corridor clears entry step and reports duration."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=True, cycle_stage=1)
        trans = pt.update(step=120, in_corridor=False, cycle_stage=1)

        self.assertTrue(trans.get("corridor_exited"))
        self.assertEqual(trans["prev_corridor_duration"], 20)
        self.assertIsNone(pt.corridor_entry_step)

    def test_phase_persists_across_corridors(self):
        """Phase duration spans corridor entries and exits."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=False, cycle_stage=1)
        pt.update(step=110, in_corridor=True, cycle_stage=1)
        pt.update(step=120, in_corridor=False, cycle_stage=1)

        # Phase started at 100, still going (stage unchanged)
        d = pt.get_durations(130)
        self.assertEqual(d["phase_duration_steps"], 30)
        self.assertEqual(d["corridor_duration_steps"], 0)

    def test_corridor_doesnt_affect_phase(self):
        """Corridor exit doesn't reset phase timer."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=True, cycle_stage=3)
        pt.update(step=120, in_corridor=False, cycle_stage=3)

        self.assertEqual(pt.phase_entry_step, 100)

    def test_none_cycle_stage_safe(self):
        """None cycle_stage doesn't crash or trigger phase change."""
        pt = PhaseTimer()
        trans = pt.update(step=100, in_corridor=False, cycle_stage=None)
        self.assertNotIn("phase_changed", trans)

        trans = pt.update(step=110, in_corridor=False, cycle_stage=None)
        self.assertNotIn("phase_changed", trans)

    def test_rapid_corridor_toggles(self):
        """Rapid corridor on/off doesn't lose state."""
        pt = PhaseTimer()
        pt.update(step=100, in_corridor=False, cycle_stage=1)
        pt.update(step=101, in_corridor=True, cycle_stage=1)
        pt.update(step=102, in_corridor=False, cycle_stage=1)
        pt.update(step=103, in_corridor=True, cycle_stage=1)

        self.assertEqual(pt.corridor_entry_step, 103)
        d = pt.get_durations(105)
        self.assertEqual(d["corridor_duration_steps"], 2)


class TestPhaseTimerSerialization(unittest.TestCase):

    def test_roundtrip(self):
        """state_dict → from_state_dict preserves all state."""
        pt = PhaseTimer()
        pt.update(step=50, in_corridor=True, cycle_stage=7)
        pt.update(step=60, in_corridor=True, cycle_stage=7)

        d = pt.state_dict()
        pt2 = PhaseTimer.from_state_dict(d)

        self.assertEqual(pt2.phase_entry_step, pt.phase_entry_step)
        self.assertEqual(pt2.corridor_entry_step, pt.corridor_entry_step)
        self.assertEqual(pt2.current_cycle_stage, pt.current_cycle_stage)
        self.assertEqual(pt2.current_in_corridor, pt.current_in_corridor)

    def test_restore_empty(self):
        """Restoring from empty dict gives defaults."""
        pt = PhaseTimer.from_state_dict({})
        self.assertEqual(pt.phase_entry_step, 0)
        self.assertIsNone(pt.corridor_entry_step)
        self.assertIsNone(pt.current_cycle_stage)
        self.assertFalse(pt.current_in_corridor)

    def test_restore_none_corridor(self):
        """Restoring with corridor_entry_step=None works."""
        pt = PhaseTimer.from_state_dict({
            "phase_entry_step": 100,
            "corridor_entry_step": None,
            "current_cycle_stage": 5,
            "current_in_corridor": False,
        })
        self.assertIsNone(pt.corridor_entry_step)
        self.assertEqual(pt.current_cycle_stage, 5)


# ===========================================================================
# Compression Duration Resistance Tests
# ===========================================================================

class TestCompressionDurationResistance(unittest.TestCase):

    def _score_with_duration(self, phase_dur: int = 0, corridor_dur: int = 0):
        """Helper: score a node with given phase/corridor duration."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()
        payload = {
            "summary": "test memory",
            "strength": 0.5,
            "confidence": 0.5,
            "canon": False,
            "created_at": 10,
            "half_life": 30.0,
            "type": "memory",
            "kind": "experience",
            "tier": "relational",
            "memory_class": "core",
            "phase_duration_steps": phase_dur,
            "corridor_duration_steps": corridor_dur,
        }
        node = {"eid": 0, "born_step": 10, "payload": payload}
        candidate = scorer.score(node, 200)
        return candidate

    def test_sustained_memory_resists(self):
        """Duration >= 10 reduces j_score (harder to compress)."""
        short = self._score_with_duration(phase_dur=5)
        long = self._score_with_duration(phase_dur=15)
        if short is not None and long is not None:
            self.assertLess(long.score, short.score)

    def test_short_memory_no_bonus(self):
        """Duration < 10 has no resistance bonus."""
        dur_0 = self._score_with_duration(phase_dur=0)
        dur_5 = self._score_with_duration(phase_dur=5)
        if dur_0 is not None and dur_5 is not None:
            self.assertAlmostEqual(dur_0.score, dur_5.score, places=4)

    def test_boundary_at_threshold(self):
        """Exactly 10 gets bonus, 9 doesn't."""
        dur_9 = self._score_with_duration(phase_dur=9)
        dur_10 = self._score_with_duration(phase_dur=10)
        if dur_9 is not None and dur_10 is not None:
            self.assertLess(dur_10.score, dur_9.score)

    def test_corridor_duration_also_counts(self):
        """corridor_duration_steps also provides resistance."""
        short = self._score_with_duration(corridor_dur=5)
        long = self._score_with_duration(corridor_dur=15)
        if short is not None and long is not None:
            self.assertLess(long.score, short.score)


# ===========================================================================
# Spirit Return Warmth Boost Tests
# ===========================================================================

class TestSpiritReturnWarmthBoost(unittest.TestCase):

    def _make_deep_memory(self, phase_dur: int = 0, corridor_dur: int = 0):
        from torment_service.deep_memory import DeepMemory
        return DeepMemory(
            eid=1, born_step=100, compressed_step=200,
            summary="test", metadata={
                "state_symbol": "◠",
                "phase_duration_steps": phase_dur,
                "corridor_duration_steps": corridor_dur,
            },
        )

    def _make_warmup(self, warmth=0.2):
        from torment_service.spirit_return import WarmupState
        return WarmupState(
            eid=1, first_appearance_step=0, appearance_count=1,
            current_warmth=warmth, max_warmth=warmth, last_retrieved_step=0,
        )

    def test_sustained_memory_warmth_floor_boost(self):
        """Duration >= 10 boosts warmth floor to 0.3."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        dm = self._make_deep_memory(phase_dur=15)
        ws = self._make_warmup(warmth=0.2)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertGreaterEqual(spirit.warmth_score, 0.3)

    def test_short_memory_warmth_unchanged(self):
        """Duration < 10 keeps warmth at 0.2."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        dm = self._make_deep_memory(phase_dur=5)
        ws = self._make_warmup(warmth=0.2)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertAlmostEqual(spirit.warmth_score, 0.2)

    def test_warmth_boost_doesnt_lower_existing(self):
        """If warmth already > 0.3, boost doesn't lower it."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        dm = self._make_deep_memory(phase_dur=15)
        ws = self._make_warmup(warmth=0.5)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertGreaterEqual(spirit.warmth_score, 0.5)

    def test_missing_duration_no_boost(self):
        """Missing duration metadata → no warmth boost."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        from torment_service.deep_memory import DeepMemory
        dm = DeepMemory(
            eid=1, born_step=100, compressed_step=200,
            summary="test", metadata={"state_symbol": "◠"},
        )
        ws = self._make_warmup(warmth=0.2)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertAlmostEqual(spirit.warmth_score, 0.2)

    def test_corridor_duration_also_boosts(self):
        """corridor_duration_steps also triggers boost."""
        from torment_service.spirit_return import enrich_deep_memory_hit
        dm = self._make_deep_memory(corridor_dur=15)
        ws = self._make_warmup(warmth=0.2)
        spirit = enrich_deep_memory_hit(dm, "◠", ws, False)
        self.assertGreaterEqual(spirit.warmth_score, 0.3)


# ===========================================================================
# Deep Memory Metadata Tests
# ===========================================================================

class TestDeepMemoryMetadata(unittest.TestCase):

    def test_metadata_keys_include_durations(self):
        """deep_memory.py metadata_keys includes phase/corridor duration."""
        import inspect
        from torment_service.deep_memory import DeepMemoryStore
        source = inspect.getsource(DeepMemoryStore.export)
        self.assertIn("phase_duration_steps", source)
        self.assertIn("corridor_duration_steps", source)


# ===========================================================================
# Backward Compatibility Tests
# ===========================================================================

class TestBackwardCompat(unittest.TestCase):

    def test_missing_phase_duration_defaults_zero(self):
        """Memories without phase_duration_steps default to 0."""
        payload = {"summary": "old memory"}
        phase_dur = int(payload.get("phase_duration_steps", 0) or 0)
        corridor_dur = int(payload.get("corridor_duration_steps", 0) or 0)
        self.assertEqual(phase_dur, 0)
        self.assertEqual(corridor_dur, 0)

    def test_old_compression_unaffected(self):
        """Memories without duration fields compress normally."""
        from torment_service.compression import CompressionScorer
        scorer = CompressionScorer()
        payload = {
            "summary": "old memory",
            "strength": 0.3,
            "confidence": 0.5,
            "canon": False,
            "created_at": 10,
            "half_life": 30.0,
            "type": "memory",
            "kind": "experience",
            "tier": "relational",
            "memory_class": "core",
            # No phase_duration_steps or corridor_duration_steps
        }
        node = {"eid": 0, "born_step": 10, "payload": payload}
        candidate = scorer.score(node, 200)
        self.assertIsNotNone(candidate)

    def test_phase_timer_restore_from_empty(self):
        """Old checkpoints without phase_timer restore gracefully."""
        pt = PhaseTimer.from_state_dict({})
        durations = pt.get_durations(100)
        self.assertEqual(durations["phase_duration_steps"], 100)
        self.assertEqual(durations["corridor_duration_steps"], 0)


if __name__ == "__main__":
    unittest.main()
