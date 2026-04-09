"""
tests/test_spirit_return_voice.py — Character Prompt Layer for Spirit Return

Tests for:
    - Hit classification with spirit return mode + warmth
    - Voice cue injection and metadata enrichment
    - Warmth-based secondary sorting
    - Assembled text output with voice markers
    - Character context spirit return summary
    - Graceful degradation (non-spirit hits unaffected)
"""
from __future__ import annotations

import os
import sys
import unittest
from typing import Any, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.retrieval_assembler import (
    _classify_core_hit,
    _hit_to_block,
    _get_voice_cue,
    assemble_context,
    BLOCK_IDENTITY,
    BLOCK_RELATIONAL,
    BLOCK_SITUATIONAL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _spirit_hit(
    mode: str = "recollection",
    warmth: float = 0.2,
    flavor: str = "a memory returns",
    interaction: str = "echo",
    score: float = 0.5,
    summary: str = "we talked about the stars",
    **extra,
) -> Dict[str, Any]:
    """Create a spirit return hit dict."""
    h: Dict[str, Any] = {
        "eid": 42,
        "score": score,
        "final_score": score,
        "summary": summary,
        "type": "memory",
        "strength": 0.3,
        "confidence": 0.7,
        "step": 100,
        "memory_class": "core",
        "from_deep_memory": True,
        "from_spirit_return": True,
        "spirit_return_mode": mode,
        "spirit_return_flavor": flavor,
        "birth_symbol": "✧",
        "current_kernel_symbol": "✧",
        "symbol_interaction": interaction,
        "warmth_score": warmth,
        "resonance_confidence": 0.8,
    }
    h.update(extra)
    return h


def _normal_hit(
    half_life: float = 30.0,
    score: float = 0.5,
    summary: str = "a normal memory",
    **extra,
) -> Dict[str, Any]:
    """Create a normal (non-spirit-return) hit dict."""
    h: Dict[str, Any] = {
        "eid": 99,
        "score": score,
        "final_score": score,
        "summary": summary,
        "type": "memory",
        "strength": 0.5,
        "confidence": 0.8,
        "step": 50,
        "half_life": half_life,
    }
    h.update(extra)
    return h


# ===========================================================================
# Classification Tests
# ===========================================================================

class TestClassification(unittest.TestCase):

    def test_resonance_warm_is_identity(self):
        """Resonance + warmth >= 0.5 → BLOCK_IDENTITY."""
        hit = _spirit_hit(mode="resonance", warmth=0.6)
        self.assertEqual(_classify_core_hit(hit), BLOCK_IDENTITY)

    def test_resonance_cold_is_situational(self):
        """Resonance + warmth < 0.5 → BLOCK_SITUATIONAL."""
        hit = _spirit_hit(mode="resonance", warmth=0.3)
        self.assertEqual(_classify_core_hit(hit), BLOCK_SITUATIONAL)

    def test_surfacing_warm_is_relational(self):
        """Surfacing + warmth >= 0.3 → BLOCK_RELATIONAL."""
        hit = _spirit_hit(mode="surfacing", warmth=0.4)
        self.assertEqual(_classify_core_hit(hit), BLOCK_RELATIONAL)

    def test_surfacing_cold_is_situational(self):
        """Surfacing + warmth < 0.3 → BLOCK_SITUATIONAL."""
        hit = _spirit_hit(mode="surfacing", warmth=0.2)
        self.assertEqual(_classify_core_hit(hit), BLOCK_SITUATIONAL)

    def test_recollection_always_situational(self):
        """Recollection → BLOCK_SITUATIONAL regardless of warmth."""
        hit = _spirit_hit(mode="recollection", warmth=0.8)
        self.assertEqual(_classify_core_hit(hit), BLOCK_SITUATIONAL)

    def test_normal_hit_unaffected(self):
        """Non-spirit-return hit uses half_life classification."""
        hit = _normal_hit(half_life=400.0)
        self.assertEqual(_classify_core_hit(hit), BLOCK_IDENTITY)

        hit2 = _normal_hit(half_life=14.0)
        self.assertEqual(_classify_core_hit(hit2), BLOCK_RELATIONAL)

        hit3 = _normal_hit(half_life=3.0)
        self.assertEqual(_classify_core_hit(hit3), BLOCK_SITUATIONAL)

    def test_seed_canon_still_identity(self):
        """Seed canon hits still classified as identity."""
        hit = _normal_hit(half_life=1.0)
        hit["type"] = "seed_canon"
        self.assertEqual(_classify_core_hit(hit), BLOCK_IDENTITY)

    def test_missing_warmth_defaults_low(self):
        """Missing warmth_score defaults to 0.2 → situational."""
        hit = _spirit_hit(mode="resonance")
        del hit["warmth_score"]
        self.assertEqual(_classify_core_hit(hit), BLOCK_SITUATIONAL)

    def test_missing_mode_defaults_recollection(self):
        """Missing spirit_return_mode defaults to recollection → situational."""
        hit = _spirit_hit()
        del hit["spirit_return_mode"]
        self.assertEqual(_classify_core_hit(hit), BLOCK_SITUATIONAL)


# ===========================================================================
# Voice Cue Tests
# ===========================================================================

class TestVoiceCues(unittest.TestCase):

    def test_resonance_voice_cue(self):
        """Resonance mode produces vivid/déjà vu voice cue."""
        cue = _get_voice_cue("resonance")
        self.assertIn("vivid", cue)
        self.assertIn("déjà vu", cue)

    def test_surfacing_voice_cue(self):
        """Surfacing mode produces gentle voice cue."""
        cue = _get_voice_cue("surfacing")
        self.assertIn("gentle", cue)

    def test_recollection_voice_cue(self):
        """Recollection mode produces past-tense voice cue."""
        cue = _get_voice_cue("recollection")
        self.assertIn("past-tense", cue)

    def test_unknown_mode_defaults(self):
        """Unknown mode defaults to recollection cue."""
        cue = _get_voice_cue("unknown")
        self.assertEqual(cue, _get_voice_cue("recollection"))


# ===========================================================================
# Block Enrichment Tests
# ===========================================================================

class TestBlockEnrichment(unittest.TestCase):

    def test_spirit_block_has_voice_metadata(self):
        """Spirit return block has voice_cue in metadata."""
        hit = _spirit_hit(mode="resonance", warmth=0.6)
        block = _hit_to_block(hit, BLOCK_IDENTITY)
        self.assertTrue(block.metadata.get("from_spirit_return"))
        self.assertEqual(block.metadata["spirit_return_mode"], "resonance")
        self.assertIn("vivid", block.metadata["voice_cue"])

    def test_spirit_block_has_flavor(self):
        """Spirit return block preserves flavor in metadata."""
        hit = _spirit_hit(flavor="a difficult memory dissolves into clarity")
        block = _hit_to_block(hit, BLOCK_SITUATIONAL)
        self.assertEqual(
            block.metadata["spirit_return_flavor"],
            "a difficult memory dissolves into clarity",
        )

    def test_spirit_block_has_warmth(self):
        """Spirit return block stores warmth_score."""
        hit = _spirit_hit(warmth=0.7)
        block = _hit_to_block(hit, BLOCK_RELATIONAL)
        self.assertAlmostEqual(block.metadata["warmth_score"], 0.7)

    def test_spirit_block_has_interaction_type(self):
        """Spirit return block stores symbol_interaction_type (not raw symbols)."""
        hit = _spirit_hit(interaction="resolution")
        block = _hit_to_block(hit, BLOCK_SITUATIONAL)
        self.assertEqual(block.metadata["symbol_interaction_type"], "resolution")

    def test_spirit_block_text_has_voice_cue(self):
        """Spirit return block text includes [Returning Memory] and voice cue."""
        hit = _spirit_hit(mode="surfacing", summary="I liked that poem")
        block = _hit_to_block(hit, BLOCK_RELATIONAL)
        self.assertIn("[Returning Memory]", block.text)
        self.assertIn("[Voice:", block.text)
        self.assertIn("I liked that poem", block.text)

    def test_spirit_block_text_has_flavor(self):
        """Spirit return block text includes flavor line."""
        hit = _spirit_hit(flavor="tension finds a place to rest")
        block = _hit_to_block(hit, BLOCK_SITUATIONAL)
        self.assertIn("[Flavor: tension finds a place to rest]", block.text)

    def test_spirit_block_text_hides_symbols(self):
        """Symbols should NOT appear in block text."""
        hit = _spirit_hit()
        hit["birth_symbol"] = "✧"
        hit["current_kernel_symbol"] = "◠"
        block = _hit_to_block(hit, BLOCK_SITUATIONAL)
        self.assertNotIn("✧", block.text)
        self.assertNotIn("◠", block.text)

    def test_normal_block_unchanged(self):
        """Non-spirit-return blocks have no voice metadata."""
        hit = _normal_hit()
        block = _hit_to_block(hit, BLOCK_RELATIONAL)
        self.assertNotIn("from_spirit_return", block.metadata)
        self.assertNotIn("voice_cue", block.metadata)
        self.assertNotIn("[Returning Memory]", block.text)

    def test_spirit_reason_includes_mode(self):
        """Spirit return block reason includes mode and warmth."""
        hit = _spirit_hit(mode="resonance", warmth=0.7)
        block = _hit_to_block(hit, BLOCK_IDENTITY)
        self.assertIn("spirit return (resonance)", block.reason)
        self.assertIn("warmth=0.7", block.reason)


# ===========================================================================
# Sorting Tests
# ===========================================================================

class TestSorting(unittest.TestCase):

    def test_warmth_secondary_sort(self):
        """Within same score, warm spirit hit ranks above cold."""
        hot_hit = _spirit_hit(mode="surfacing", warmth=0.8, score=0.5, eid=1)
        cold_hit = _spirit_hit(mode="surfacing", warmth=0.2, score=0.5, eid=2)
        # assemble_context sorts blocks by (score, warmth) descending
        result = assemble_context(
            core_hits=[cold_hit, hot_hit],
            profile="balanced",
            token_budget=2000,
        )
        sit_blocks = result.blocks.get(BLOCK_SITUATIONAL, [])
        if len(sit_blocks) >= 2:
            # First block should be the warm one (same score, higher warmth)
            self.assertAlmostEqual(sit_blocks[0]["metadata"]["warmth_score"], 0.8)

    def test_score_still_primary(self):
        """Higher score beats higher warmth."""
        high_score = _spirit_hit(warmth=0.2, score=0.9, eid=1, summary="high score")
        high_warmth = _spirit_hit(warmth=0.8, score=0.3, eid=2, summary="high warmth")
        result = assemble_context(
            core_hits=[high_warmth, high_score],
            profile="balanced",
            token_budget=2000,
        )
        sit_blocks = result.blocks.get(BLOCK_SITUATIONAL, [])
        if len(sit_blocks) >= 2:
            self.assertGreater(sit_blocks[0]["score"], sit_blocks[1]["score"])


# ===========================================================================
# Assembly Integration Tests
# ===========================================================================

class TestAssembly(unittest.TestCase):

    def test_voice_cues_in_assembled_text(self):
        """Assembled text includes voice cue markers."""
        hit = _spirit_hit(mode="resonance", warmth=0.6, summary="the stars were bright")
        result = assemble_context(
            core_hits=[hit],
            profile="balanced",
            token_budget=2000,
        )
        self.assertIn("[Voice:", result.assembled_text)
        self.assertIn("the stars were bright", result.assembled_text)

    def test_flavor_in_assembled_text(self):
        """Assembled text includes flavor."""
        hit = _spirit_hit(flavor="old tension dissolves")
        result = assemble_context(
            core_hits=[hit],
            profile="balanced",
            token_budget=2000,
        )
        self.assertIn("[Flavor: old tension dissolves]", result.assembled_text)

    def test_returning_memory_marker(self):
        """Assembled text has [Returning Memory] marker."""
        hit = _spirit_hit()
        result = assemble_context(
            core_hits=[hit],
            profile="balanced",
            token_budget=2000,
        )
        self.assertIn("[Returning Memory]", result.assembled_text)

    def test_symbols_not_in_assembled_text(self):
        """Raw symbols never appear in assembled text."""
        hit = _spirit_hit()
        hit["birth_symbol"] = "⊗"
        hit["current_kernel_symbol"] = "⊘"
        result = assemble_context(
            core_hits=[hit],
            profile="balanced",
            token_budget=2000,
        )
        self.assertNotIn("⊗", result.assembled_text)
        self.assertNotIn("⊘", result.assembled_text)

    def test_mixed_hits_assemble(self):
        """Mix of spirit return and normal hits assembles correctly."""
        spirit = _spirit_hit(mode="surfacing", warmth=0.4, eid=1)
        normal = _normal_hit(half_life=14.0, eid=2)
        result = assemble_context(
            core_hits=[spirit, normal],
            profile="balanced",
            token_budget=4000,
        )
        self.assertIn("[Returning Memory]", result.assembled_text)
        self.assertIn("a normal memory", result.assembled_text)
        self.assertGreater(result.tokens_used, 0)

    def test_no_spirit_hits_no_change(self):
        """Without spirit return hits, assembled text has no voice markers."""
        normal = _normal_hit()
        result = assemble_context(
            core_hits=[normal],
            profile="balanced",
            token_budget=2000,
        )
        self.assertNotIn("[Voice:", result.assembled_text)
        self.assertNotIn("[Returning Memory]", result.assembled_text)
        self.assertNotIn("[Flavor:", result.assembled_text)


# ===========================================================================
# Character Context Tests
# ===========================================================================

class TestCharacterContext(unittest.TestCase):

    def _make_seed(self):
        """Create minimal CharacterSeed for testing."""
        from torment_service.character import CharacterSeed
        return CharacterSeed(
            seed_id="test_v1",
            character_name="Aria",
            seed_text="Aria is warm and curious.",
            seed_motif_id="m_seed",
            seed_eids=[1, 2],
        )

    def test_spirit_return_summary_present(self):
        """Spirit return summary included when spirit hits exist."""
        from torment_service.character import assemble_character_context

        hits = [
            _spirit_hit(mode="resonance", warmth=0.7),
            _spirit_hit(mode="surfacing", warmth=0.4, eid=43),
            _spirit_hit(mode="recollection", warmth=0.2, eid=44),
        ]
        result = assemble_character_context(
            graph=None, seed=self._make_seed(),
            agent_id="test", hits=hits,
        )
        self.assertIn("spirit_return_summary", result)
        summary = result["spirit_return_summary"]
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_mode"]["resonance"], 1)
        self.assertEqual(summary["by_mode"]["surfacing"], 1)
        self.assertEqual(summary["by_mode"]["recollection"], 1)
        self.assertGreater(summary["avg_warmth"], 0.0)

    def test_spirit_return_recommendations(self):
        """Recommendations include voice guidance for spirit return modes."""
        from torment_service.character import assemble_character_context

        hits = [
            _spirit_hit(mode="resonance", warmth=0.7),
            _spirit_hit(mode="recollection", warmth=0.2, eid=44),
        ]
        result = assemble_character_context(
            graph=None, seed=self._make_seed(),
            agent_id="test", hits=hits,
        )
        recs = result["recommendations"]
        rec_text = " ".join(recs)
        self.assertIn("vivid", rec_text)
        self.assertIn("déjà vu", rec_text)
        self.assertIn("distilled", rec_text)

    def test_no_spirit_hits_no_summary(self):
        """Without spirit hits, no spirit_return_summary."""
        from torment_service.character import assemble_character_context

        hits = [_normal_hit()]
        result = assemble_character_context(
            graph=None, seed=self._make_seed(),
            agent_id="test", hits=hits,
        )
        self.assertNotIn("spirit_return_summary", result)

    def test_empty_hits_no_crash(self):
        """Empty hit list doesn't crash."""
        from torment_service.character import assemble_character_context

        result = assemble_character_context(
            graph=None, seed=self._make_seed(),
            agent_id="test", hits=[],
        )
        self.assertNotIn("spirit_return_summary", result)
        self.assertEqual(result["recommendations"], [])


if __name__ == "__main__":
    unittest.main()
