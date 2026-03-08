"""
tests/test_spirit_return.py — Spirit Return with Symbolic Resonance

Tests for:
    - Symbol interaction matrix (exact pairs, echo, contrast, custom rules)
    - Return mode selection (resonance, surfacing, recollection)
    - Warmth computation and capping
    - WarmupTracker persistence and stats
    - Full enrichment pipeline (enrich + inject)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.spirit_return import (
    SymbolInteractionRule,
    WarmupState,
    SpiritReturnMemory,
    build_symbol_interaction_matrix,
    compute_symbol_interaction,
    select_return_mode,
    compute_warmth,
    enrich_deep_memory_hit,
    inject_spirit_return_into_hit,
    WarmupTracker,
    WARMTH_FLOOR,
    WARMTH_INCREMENT,
    WARMTH_CAP,
    WARMTH_WINDOW_STEPS,
)
from torment_service.deep_memory import DeepMemory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_deep_memory(
    eid: int = 1,
    born_step: int = 100,
    summary: str = "test memory",
    state_symbol: str = "◯",
    **extra_meta,
) -> DeepMemory:
    metadata = {"state_symbol": state_symbol, "type": "memory"}
    metadata.update(extra_meta)
    return DeepMemory(
        eid=eid,
        born_step=born_step,
        compressed_step=200,
        summary=summary,
        compression_score=0.75,
        original_motif_id="m_1",
        memory_class="core",
        embedding_ref=None,
        metadata=metadata,
    )


def _make_warmup(
    eid: int = 1,
    count: int = 1,
    warmth: float = 0.2,
    first_step: int = 0,
    last_step: int = 0,
) -> WarmupState:
    return WarmupState(
        eid=eid,
        first_appearance_step=first_step,
        appearance_count=count,
        current_warmth=warmth,
        max_warmth=warmth,
        last_retrieved_step=last_step,
    )


# ===========================================================================
# Symbol Interaction Tests
# ===========================================================================

class TestSymbolInteraction(unittest.TestCase):

    def test_echo_same_symbol(self):
        """Same symbol produces echo interaction."""
        for sym in ["◯", "∿", "◈", "⊗", "⋮", "◠", "✧", "⊘"]:
            # Only test symbols that don't have an explicit self-rule
            result = compute_symbol_interaction(sym, sym)
            if sym == "✧":
                # ✧→✧ has an explicit rule: deepening
                self.assertEqual(result["interaction_type"], "deepening")
            else:
                self.assertEqual(result["interaction_type"], "echo", f"Failed for {sym}")
                self.assertTrue(result["is_resonance_candidate"])

    def test_resolution(self):
        """⊗→⊘ produces resolution."""
        result = compute_symbol_interaction("⊗", "⊘")
        self.assertEqual(result["interaction_type"], "resolution")
        self.assertGreater(result["confidence_boost"], 0.0)

    def test_integration(self):
        """⊗→◠ produces integration."""
        result = compute_symbol_interaction("⊗", "◠")
        self.assertEqual(result["interaction_type"], "integration")

    def test_nostalgia_under_stress(self):
        """◠→⊗ produces nostalgia_under_stress."""
        result = compute_symbol_interaction("◠", "⊗")
        self.assertEqual(result["interaction_type"], "nostalgia_under_stress")

    def test_deepening(self):
        """✧→✧ produces deepening."""
        result = compute_symbol_interaction("✧", "✧")
        self.assertEqual(result["interaction_type"], "deepening")
        self.assertTrue(result["is_resonance_candidate"])

    def test_fulfilled(self):
        """◯→◈ produces fulfilled."""
        result = compute_symbol_interaction("◯", "◈")
        self.assertEqual(result["interaction_type"], "fulfilled")

    def test_resurgence(self):
        """⊘→⊗ produces resurgence."""
        result = compute_symbol_interaction("⊘", "⊗")
        self.assertEqual(result["interaction_type"], "resurgence")

    def test_outgrown(self):
        """◠→∿ produces outgrown."""
        result = compute_symbol_interaction("◠", "∿")
        self.assertEqual(result["interaction_type"], "outgrown")

    def test_crystallized(self):
        """✧→◈ produces crystallized."""
        result = compute_symbol_interaction("✧", "◈")
        self.assertEqual(result["interaction_type"], "crystallized")

    def test_found_home(self):
        """∿→◠ produces found_home."""
        result = compute_symbol_interaction("∿", "◠")
        self.assertEqual(result["interaction_type"], "found_home")

    def test_breakthrough(self):
        """⋮→✧ produces breakthrough."""
        result = compute_symbol_interaction("⋮", "✧")
        self.assertEqual(result["interaction_type"], "breakthrough")

    def test_disrupted(self):
        """◈→⊗ produces disrupted."""
        result = compute_symbol_interaction("◈", "⊗")
        self.assertEqual(result["interaction_type"], "disrupted")

    def test_peace(self):
        """⊘→◠ produces peace."""
        result = compute_symbol_interaction("⊘", "◠")
        self.assertEqual(result["interaction_type"], "peace")

    def test_contrast_default(self):
        """Unmapped pair with different symbols produces contrast."""
        # ◈→∿ has no explicit rule and symbols differ
        result = compute_symbol_interaction("◈", "∿")
        self.assertEqual(result["interaction_type"], "contrast")
        self.assertFalse(result["is_resonance_candidate"])

    def test_custom_rules_override(self):
        """Custom rules take precedence over defaults."""
        custom = [
            SymbolInteractionRule("◯", "◯", "custom_echo",
                "a custom echo", 0.30),
        ]
        result = compute_symbol_interaction("◯", "◯", rules=custom)
        self.assertEqual(result["interaction_type"], "custom_echo")
        self.assertEqual(result["confidence_boost"], 0.30)

    def test_missing_symbols_default_to_potential(self):
        """Empty or None birth/current symbol defaults to ◯."""
        result = compute_symbol_interaction("", "")
        self.assertEqual(result["interaction_type"], "echo")
        result2 = compute_symbol_interaction(None, None)
        self.assertEqual(result2["interaction_type"], "echo")

    def test_all_rules_have_flavor(self):
        """Every rule in the matrix has a non-empty flavor template."""
        rules = build_symbol_interaction_matrix()
        for rule in rules:
            self.assertTrue(len(rule.flavor_template) > 0,
                f"Empty flavor for {rule.birth_symbol}→{rule.current_symbol}")

    def test_all_rules_have_valid_confidence_boost(self):
        """Confidence boost is in [0, 0.3] for all rules."""
        rules = build_symbol_interaction_matrix()
        for rule in rules:
            self.assertGreaterEqual(rule.confidence_boost, 0.0)
            self.assertLessEqual(rule.confidence_boost, 0.30)


# ===========================================================================
# Return Mode Tests
# ===========================================================================

class TestReturnMode(unittest.TestCase):

    def test_resonance_high_confidence(self):
        """High warmth + resonance candidate → resonance."""
        dm = _make_deep_memory()
        interaction = {
            "is_resonance_candidate": True,
            "confidence_boost": 0.25,
        }
        mode = select_return_mode(dm, False, interaction, warmth=0.6)
        self.assertEqual(mode, "resonance")

    def test_surfacing_in_core(self):
        """Compressed in core + warm → surfacing."""
        dm = _make_deep_memory()
        interaction = {
            "is_resonance_candidate": False,
            "confidence_boost": 0.0,
        }
        mode = select_return_mode(dm, True, interaction, warmth=0.4)
        self.assertEqual(mode, "surfacing")

    def test_recollection_default(self):
        """No special conditions → recollection."""
        dm = _make_deep_memory()
        interaction = {
            "is_resonance_candidate": False,
            "confidence_boost": 0.0,
        }
        mode = select_return_mode(dm, False, interaction, warmth=0.2)
        self.assertEqual(mode, "recollection")

    def test_resonance_requires_candidate(self):
        """High warmth but not candidate → not resonance."""
        dm = _make_deep_memory()
        interaction = {
            "is_resonance_candidate": False,
            "confidence_boost": 0.25,
        }
        mode = select_return_mode(dm, False, interaction, warmth=0.8)
        self.assertEqual(mode, "recollection")

    def test_resonance_requires_warmth(self):
        """Resonance candidate but low warmth → not resonance."""
        dm = _make_deep_memory()
        interaction = {
            "is_resonance_candidate": True,
            "confidence_boost": 0.25,
        }
        mode = select_return_mode(dm, False, interaction, warmth=0.3)
        self.assertNotEqual(mode, "resonance")

    def test_surfacing_requires_warmth(self):
        """In core but cold → recollection, not surfacing."""
        dm = _make_deep_memory()
        interaction = {
            "is_resonance_candidate": False,
            "confidence_boost": 0.0,
        }
        mode = select_return_mode(dm, True, interaction, warmth=0.2)
        self.assertEqual(mode, "recollection")

    def test_resonance_beats_surfacing(self):
        """When both conditions met, resonance wins."""
        dm = _make_deep_memory()
        interaction = {
            "is_resonance_candidate": True,
            "confidence_boost": 0.25,
        }
        mode = select_return_mode(dm, True, interaction, warmth=0.6)
        self.assertEqual(mode, "resonance")


# ===========================================================================
# Warmth Tests
# ===========================================================================

class TestWarmth(unittest.TestCase):

    def test_warmth_initial(self):
        """First appearance = 0.2."""
        self.assertAlmostEqual(compute_warmth(1, 0), WARMTH_FLOOR)

    def test_warmth_zero_count(self):
        """Zero appearances = floor."""
        self.assertAlmostEqual(compute_warmth(0, 0), WARMTH_FLOOR)

    def test_warmth_increases(self):
        """Repeated retrieval within window increases warmth."""
        w2 = compute_warmth(2, 50)
        w3 = compute_warmth(3, 50)
        self.assertGreater(w2, WARMTH_FLOOR)
        self.assertGreater(w3, w2)

    def test_warmth_caps_at_one(self):
        """Warmth saturates at 1.0."""
        w = compute_warmth(100, 50)
        self.assertAlmostEqual(w, WARMTH_CAP)

    def test_warmth_no_increase_outside_window(self):
        """No warmth increase if steps exceed window."""
        w = compute_warmth(5, WARMTH_WINDOW_STEPS + 100)
        self.assertAlmostEqual(w, WARMTH_FLOOR)

    def test_warmth_exact_values(self):
        """Verify exact warmth progression."""
        # count=2, within window: floor + 1*increment
        w2 = compute_warmth(2, 10)
        self.assertAlmostEqual(w2, WARMTH_FLOOR + WARMTH_INCREMENT)

        # count=3: floor + 2*increment
        w3 = compute_warmth(3, 10)
        self.assertAlmostEqual(w3, WARMTH_FLOOR + 2 * WARMTH_INCREMENT)


# ===========================================================================
# WarmupTracker Tests
# ===========================================================================

class TestWarmupTracker(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_new_state(self):
        """First access creates a new warmup state."""
        tracker = WarmupTracker(Path(self.tmpdir))
        ws = tracker.get_or_create(42, current_step=100)
        self.assertEqual(ws.eid, 42)
        self.assertEqual(ws.appearance_count, 1)
        self.assertAlmostEqual(ws.current_warmth, WARMTH_FLOOR)

    def test_increment_count(self):
        """Same EID increments appearance count."""
        tracker = WarmupTracker(Path(self.tmpdir))
        ws1 = tracker.get_or_create(42, current_step=100)
        ws2 = tracker.get_or_create(42, current_step=110)
        self.assertEqual(ws2.appearance_count, 2)
        self.assertGreater(ws2.current_warmth, ws1.current_warmth)

    def test_persistence_roundtrip(self):
        """Warmup state survives reload from disk."""
        tracker1 = WarmupTracker(Path(self.tmpdir))
        tracker1.get_or_create(10, current_step=50)
        tracker1.get_or_create(10, current_step=60)
        tracker1.get_or_create(20, current_step=70)

        # Create new tracker from same path
        tracker2 = WarmupTracker(Path(self.tmpdir))
        ws10 = tracker2.get_or_create(10, current_step=80)
        # Should have loaded previous state (count=2) and incremented to 3
        self.assertEqual(ws10.appearance_count, 3)

        ws20 = tracker2.get_or_create(20, current_step=80)
        # Should have loaded previous state (count=1) and incremented to 2
        self.assertEqual(ws20.appearance_count, 2)

    def test_stats_empty(self):
        """Empty tracker returns zero stats."""
        tracker = WarmupTracker(Path(self.tmpdir))
        s = tracker.stats()
        self.assertEqual(s["tracked_eids"], 0)
        self.assertEqual(s["total_appearances"], 0)

    def test_stats_with_data(self):
        """Stats reflect tracked data."""
        tracker = WarmupTracker(Path(self.tmpdir))
        tracker.get_or_create(1, 100)
        tracker.get_or_create(2, 100)
        tracker.get_or_create(1, 110)  # increment EID 1
        s = tracker.stats()
        self.assertEqual(s["tracked_eids"], 2)
        self.assertEqual(s["total_appearances"], 3)  # 2 for eid=1, 1 for eid=2
        self.assertGreater(s["avg_warmth"], 0.0)

    def test_different_eids_isolated(self):
        """Different EIDs don't affect each other."""
        tracker = WarmupTracker(Path(self.tmpdir))
        tracker.get_or_create(1, 100)
        tracker.get_or_create(1, 110)
        tracker.get_or_create(1, 120)  # 3 appearances for eid=1
        ws2 = tracker.get_or_create(2, 100)  # 1 appearance for eid=2
        self.assertEqual(ws2.appearance_count, 1)
        self.assertAlmostEqual(ws2.current_warmth, WARMTH_FLOOR)


# ===========================================================================
# Integration Tests
# ===========================================================================

class TestEnrichment(unittest.TestCase):

    def test_enrich_produces_all_fields(self):
        """Full enrichment pipeline produces complete SpiritReturnMemory."""
        dm = _make_deep_memory(state_symbol="⊗")
        ws = _make_warmup(warmth=0.4)
        spirit = enrich_deep_memory_hit(dm, "⊘", ws, False)

        self.assertIsInstance(spirit, SpiritReturnMemory)
        self.assertEqual(spirit.birth_symbol, "⊗")
        self.assertEqual(spirit.current_kernel_symbol, "⊘")
        self.assertEqual(spirit.symbol_interaction, "resolution")
        self.assertIn("dissolves", spirit.return_flavor)
        self.assertIn(spirit.return_mode, ["surfacing", "recollection", "resonance"])
        self.assertGreater(spirit.resonance_confidence, 0.0)

    def test_inject_hit_format(self):
        """Injected hit dict has all required fields."""
        dm = _make_deep_memory(state_symbol="⊗")
        ws = _make_warmup(warmth=0.4)
        spirit = enrich_deep_memory_hit(dm, "⊘", ws, False)
        hit = inject_spirit_return_into_hit(spirit)

        required_fields = [
            "eid", "score", "summary", "type", "strength", "confidence",
            "step", "memory_class", "from_deep_memory", "from_spirit_return",
            "spirit_return_mode", "spirit_return_flavor", "birth_symbol",
            "current_kernel_symbol", "symbol_interaction", "warmth_score",
            "resonance_confidence",
        ]
        for f in required_fields:
            self.assertIn(f, hit, f"Missing field: {f}")

        self.assertTrue(hit["from_deep_memory"])
        self.assertTrue(hit["from_spirit_return"])

    def test_strength_varies_by_mode(self):
        """Resonance > surfacing > recollection in strength."""
        dm = _make_deep_memory(state_symbol="✧", symbol_confidence=0.9)

        # Resonance: ✧→✧, high warmth
        ws_hot = _make_warmup(warmth=0.7)
        spirit_res = enrich_deep_memory_hit(dm, "✧", ws_hot, False)
        hit_res = inject_spirit_return_into_hit(spirit_res)

        # Surfacing: different symbol, in core, moderate warmth
        dm2 = _make_deep_memory(state_symbol="◯")
        ws_mid = _make_warmup(warmth=0.4)
        spirit_surf = enrich_deep_memory_hit(dm2, "⊗", ws_mid, True)
        hit_surf = inject_spirit_return_into_hit(spirit_surf)

        # Recollection: different symbol, not in core, low warmth
        ws_cold = _make_warmup(warmth=0.2)
        spirit_rec = enrich_deep_memory_hit(dm2, "⊗", ws_cold, False)
        hit_rec = inject_spirit_return_into_hit(spirit_rec)

        self.assertEqual(hit_res["spirit_return_mode"], "resonance")
        self.assertEqual(hit_surf["spirit_return_mode"], "surfacing")
        self.assertEqual(hit_rec["spirit_return_mode"], "recollection")
        self.assertGreater(hit_res["strength"], hit_surf["strength"])
        self.assertGreater(hit_surf["strength"], hit_rec["strength"])

    def test_missing_symbol_defaults(self):
        """Missing metadata state_symbol defaults to ◯."""
        dm = DeepMemory(
            eid=1, born_step=100, compressed_step=200,
            summary="no symbol", metadata={},
        )
        ws = _make_warmup()
        spirit = enrich_deep_memory_hit(dm, "⊗", ws, False)
        self.assertEqual(spirit.birth_symbol, "◯")

    def test_flavor_present(self):
        """return_flavor is always a non-empty string."""
        for birth in ["◯", "⊗", "◠", "✧", "⊘", "∿", "◈", "⋮"]:
            for current in ["◯", "⊗", "◠", "✧", "⊘", "∿", "◈", "⋮"]:
                result = compute_symbol_interaction(birth, current)
                self.assertTrue(len(result["flavor"]) > 0,
                    f"Empty flavor for {birth}→{current}")

    def test_warmup_state_serialization(self):
        """WarmupState round-trips through dict."""
        ws = WarmupState(
            eid=42, first_appearance_step=100,
            appearance_count=3, current_warmth=0.5,
            max_warmth=0.5, last_retrieved_step=150,
        )
        d = ws.to_dict()
        ws2 = WarmupState.from_dict(d)
        self.assertEqual(ws2.eid, 42)
        self.assertEqual(ws2.appearance_count, 3)
        self.assertAlmostEqual(ws2.current_warmth, 0.5)

    def test_deep_memory_metadata_keys_expanded(self):
        """Verify deep_memory.py now preserves symbolic trace fields."""
        # Import the export method and check metadata_keys includes new fields
        import inspect
        from torment_service.deep_memory import DeepMemoryStore
        source = inspect.getsource(DeepMemoryStore.export)
        for key in ["symbol_trace", "loop_type", "phase_shift",
                     "dominant_transition", "symbol_confidence", "half_life"]:
            self.assertIn(key, source,
                f"metadata_keys missing {key}")


# ===========================================================================
# Edge Cases
# ===========================================================================

class TestEdgeCases(unittest.TestCase):

    def test_none_metadata(self):
        """DeepMemory with None metadata doesn't crash enrichment."""
        dm = DeepMemory(
            eid=1, born_step=100, compressed_step=200,
            summary="test", metadata=None,
        )
        ws = _make_warmup()
        spirit = enrich_deep_memory_hit(dm, "◯", ws, False)
        self.assertEqual(spirit.birth_symbol, "◯")

    def test_empty_kernel_symbol(self):
        """Empty current kernel symbol defaults to ◯."""
        dm = _make_deep_memory(state_symbol="⊗")
        ws = _make_warmup()
        spirit = enrich_deep_memory_hit(dm, "", ws, False)
        self.assertEqual(spirit.current_kernel_symbol, "◯")

    def test_symbol_interaction_rule_matching(self):
        """SymbolInteractionRule.matches() works correctly."""
        rule = SymbolInteractionRule("⊗", "⊘", "test", "test", 0.1)
        self.assertTrue(rule.matches("⊗", "⊘"))
        self.assertFalse(rule.matches("⊗", "◯"))
        self.assertFalse(rule.matches("◯", "⊘"))

        wildcard = SymbolInteractionRule("*", "⊘", "test", "test", 0.1)
        self.assertTrue(wildcard.matches("⊗", "⊘"))
        self.assertTrue(wildcard.matches("◯", "⊘"))
        self.assertFalse(wildcard.matches("◯", "◯"))

    def test_all_8_symbols_as_birth_and_current(self):
        """No crash for any symbol combination."""
        symbols = ["◯", "∿", "◈", "⊗", "⋮", "◠", "✧", "⊘"]
        for b in symbols:
            for c in symbols:
                result = compute_symbol_interaction(b, c)
                self.assertIn("interaction_type", result)
                self.assertIn("flavor", result)

    def test_warmup_tracker_empty_file(self):
        """Tracker handles empty file gracefully."""
        tmpdir = tempfile.mkdtemp()
        try:
            # Create empty file
            f = Path(tmpdir) / "warmup_state.jsonl"
            f.write_text("")
            tracker = WarmupTracker(Path(tmpdir))
            ws = tracker.get_or_create(1, 100)
            self.assertEqual(ws.appearance_count, 1)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_warmup_tracker_corrupted_line(self):
        """Tracker skips corrupted lines."""
        tmpdir = tempfile.mkdtemp()
        try:
            f = Path(tmpdir) / "warmup_state.jsonl"
            f.write_text("not valid json\n{\"eid\":5,\"appearance_count\":2,\"current_warmth\":0.35,\"max_warmth\":0.35,\"first_appearance_step\":10,\"last_retrieved_step\":20}\n")
            tracker = WarmupTracker(Path(tmpdir))
            # Should have loaded eid=5 and skipped corrupt line
            ws = tracker.get_or_create(5, 30)
            self.assertEqual(ws.appearance_count, 3)  # loaded 2 + 1 new
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ===========================================================================
# Matrix Coverage
# ===========================================================================

class TestMatrixCoverage(unittest.TestCase):

    def test_matrix_has_minimum_rules(self):
        """Matrix has at least 15 explicit rules."""
        rules = build_symbol_interaction_matrix()
        self.assertGreaterEqual(len(rules), 15)

    def test_no_duplicate_rules(self):
        """No duplicate birth×current pairs in the matrix."""
        rules = build_symbol_interaction_matrix()
        pairs = set()
        for rule in rules:
            pair = (rule.birth_symbol, rule.current_symbol)
            self.assertNotIn(pair, pairs,
                f"Duplicate rule for {pair}")
            pairs.add(pair)

    def test_interaction_types_unique_per_pair(self):
        """Each rule has a unique interaction type."""
        rules = build_symbol_interaction_matrix()
        # It's ok for different pairs to share an interaction type,
        # but within the matrix each should have a distinct name
        # (this test ensures no copy-paste errors)
        types_seen = {}
        for rule in rules:
            pair = (rule.birth_symbol, rule.current_symbol)
            types_seen[pair] = rule.interaction_type

        # At least 10 unique interaction types
        unique_types = set(types_seen.values())
        self.assertGreaterEqual(len(unique_types), 10)


if __name__ == "__main__":
    unittest.main()
