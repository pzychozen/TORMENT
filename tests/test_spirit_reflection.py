"""Tests for the spirit reflection pipeline (post-response write-back).

Covers:
  - No reflection stored when influence is below threshold
  - Reflection stored when influence is strong
  - Duplicate suppression (same source + same step)
  - Cooldown enforcement (same cooldown_key within window)
  - Generation depth cap (reflections cannot spawn reflections)
  - eligible_for_spirit_return is always False
  - SpiritReflectionStore persistence and load
  - process_spirit_reflections end-to-end
  - Deep memory is never mutated by the reflection pipeline
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from torment_service.spirit_reflection import (
    SpiritReflectionEvent,
    SpiritReflectionStore,
    extract_spirit_return_candidates,
    score_spirit_return_influence,
    build_spirit_reflection_event,
    should_store_reflection,
    process_spirit_reflections,
    DEFAULT_INFLUENCE_THRESHOLD,
    DEFAULT_COOLDOWN_STEPS,
    MAX_GENERATION_DEPTH,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_spirit_hit(
    eid: int = 100,
    summary: str = "A vivid memory of walking through the old garden at sunset",
    mode: str = "resonance",
    warmth: float = 0.65,
    interaction: str = "fulfilled",
    flavor: str = "something that was once only potential has crystallized",
    **overrides,
) -> dict:
    """Build a synthetic spirit-return hit dict (as it appears in blocks)."""
    hit = {
        "eid": eid,
        "summary": summary,
        "from_spirit_return": True,
        "spirit_return_mode": mode,
        "warmth_score": warmth,
        "symbol_interaction": interaction,
        "spirit_return_flavor": flavor,
        "birth_symbol": "◯",
        "current_kernel_symbol": "◈",
        "resonance_confidence": 0.70,
        "from_deep_memory": True,
        "score": 0.85,
        "strength": 0.39,
        "type": "memory",
    }
    hit.update(overrides)
    return hit


def _make_non_spirit_hit(eid: int = 200) -> dict:
    """A regular hit without spirit return markers."""
    return {
        "eid": eid,
        "summary": "Just a normal memory",
        "from_spirit_return": False,
        "score": 0.5,
    }


def _tmp_store() -> SpiritReflectionStore:
    """Create a SpiritReflectionStore in a temp dir."""
    tmp = tempfile.mkdtemp()
    return SpiritReflectionStore(Path(tmp) / "spirit_reflections", base_dir=tmp)


# ---------------------------------------------------------------------------
# Stage 1 — Extraction
# ---------------------------------------------------------------------------

class TestExtractCandidates:

    def test_extracts_spirit_return_hits(self):
        blocks = [_make_spirit_hit(eid=1), _make_non_spirit_hit(eid=2), _make_spirit_hit(eid=3)]
        result = extract_spirit_return_candidates(blocks)
        assert len(result) == 2
        assert result[0]["eid"] == 1
        assert result[1]["eid"] == 3

    def test_empty_blocks_returns_empty(self):
        assert extract_spirit_return_candidates([]) == []

    def test_no_spirit_hits_returns_empty(self):
        blocks = [_make_non_spirit_hit()]
        assert extract_spirit_return_candidates(blocks) == []

    def test_filters_out_existing_reflections(self):
        """Reflections (generation_depth >= 1) must not spawn new reflections."""
        reflection_hit = _make_spirit_hit(
            eid=99, derived_from_spirit_return=True, generation_depth=1
        )
        blocks = [reflection_hit, _make_spirit_hit(eid=100)]
        result = extract_spirit_return_candidates(blocks)
        assert len(result) == 1
        assert result[0]["eid"] == 100


# ---------------------------------------------------------------------------
# Stage 2 — Influence scoring
# ---------------------------------------------------------------------------

class TestInfluenceScoring:

    def test_high_overlap_scores_high(self):
        candidate = _make_spirit_hit(
            summary="walking through the garden at sunset with old memories"
        )
        response = "I was walking through the garden at sunset, old memories flooding back"
        result = score_spirit_return_influence(candidate, response)
        assert result["influence_score"] > 0.3
        assert "lexical_overlap" in result["influence_reason_tags"]

    def test_no_overlap_scores_low(self):
        candidate = _make_spirit_hit(summary="quantum physics equations")
        response = "The weather is beautiful today, sunny and warm"
        result = score_spirit_return_influence(candidate, response)
        assert result["influence_score"] < DEFAULT_INFLUENCE_THRESHOLD

    def test_resonance_mode_bonus(self):
        candidate = _make_spirit_hit(mode="resonance", summary="test thing")
        response = "test thing"
        score_res = score_spirit_return_influence(candidate, response)

        candidate_rec = _make_spirit_hit(mode="recollection", summary="test thing")
        score_rec = score_spirit_return_influence(candidate_rec, response)

        assert score_res["influence_score"] > score_rec["influence_score"]

    def test_warmth_contributes_to_score(self):
        candidate_warm = _make_spirit_hit(warmth=0.9, summary="abc")
        candidate_cold = _make_spirit_hit(warmth=0.2, summary="abc")
        response = "abc"
        score_warm = score_spirit_return_influence(candidate_warm, response)
        score_cold = score_spirit_return_influence(candidate_cold, response)
        assert score_warm["influence_score"] >= score_cold["influence_score"]


# ---------------------------------------------------------------------------
# Stage 3 — Building reflection events
# ---------------------------------------------------------------------------

class TestBuildReflection:

    def test_basic_build(self):
        candidate = _make_spirit_hit(eid=42)
        event = build_spirit_reflection_event(
            candidate, "some response text", current_step=100, query_text="hello"
        )
        assert event.source_eid == 42
        assert event.derived_from_spirit_return is True
        assert event.generation_depth == 1
        assert event.eligible_for_spirit_return is False
        assert event.created_step == 100
        assert event.return_mode == "resonance"
        assert event.symbol_interaction == "fulfilled"
        assert "resurfaced" in event.summary

    def test_summary_is_derived_not_copied(self):
        """The reflection summary must describe the EVENT, not copy the original."""
        candidate = _make_spirit_hit(summary="Original deep memory content here")
        event = build_spirit_reflection_event(
            candidate, "response", current_step=1, query_text="q"
        )
        assert event.summary != "Original deep memory content here"
        assert "resurfaced" in event.summary or "deep memory" in event.summary

    def test_cooldown_key_format(self):
        candidate = _make_spirit_hit(eid=7, mode="resonance", interaction="fulfilled")
        event = build_spirit_reflection_event(
            candidate, "resp", current_step=1, query_text="q"
        )
        assert event.cooldown_key == "7:resonance:fulfilled"

    def test_response_excerpt_truncated(self):
        long_response = "x" * 500
        event = build_spirit_reflection_event(
            _make_spirit_hit(), long_response, current_step=1, query_text="q"
        )
        assert len(event.response_excerpt) <= 203  # 200 + "..."

    def test_eligible_for_spirit_return_always_false(self):
        event = build_spirit_reflection_event(
            _make_spirit_hit(), "resp", current_step=1, query_text="q"
        )
        assert event.eligible_for_spirit_return is False

    def test_from_dict_forces_eligible_false(self):
        """Even if someone tampers with the dict, eligible stays False."""
        d = build_spirit_reflection_event(
            _make_spirit_hit(), "resp", current_step=1, query_text="q"
        ).to_dict()
        d["eligible_for_spirit_return"] = True  # tamper
        restored = SpiritReflectionEvent.from_dict(d)
        assert restored.eligible_for_spirit_return is False


# ---------------------------------------------------------------------------
# Stage 4 — Anti-echo guard
# ---------------------------------------------------------------------------

class TestAntiEchoGuard:

    def _event(self, source_eid=1, step=100, influence=0.5, mode="resonance", interaction="echo"):
        return SpiritReflectionEvent(
            eid=999, source_eid=source_eid,
            derived_from_spirit_return=True, generation_depth=1,
            created_step=step, created_at=0.0,
            query_text="q", response_excerpt="r",
            return_mode=mode, warmth_score=0.5,
            symbol_interaction=interaction,
            spirit_return_flavor="flavor",
            influence_score=influence,
            influence_reason_tags=["lexical_overlap"],
            summary="test", cooldown_key=f"{source_eid}:{mode}:{interaction}",
            eligible_for_spirit_return=False,
        )

    def test_passes_when_all_clear(self):
        event = self._event(influence=0.5)
        result = should_store_reflection(event, [])
        assert result["store"] is True

    def test_rejects_below_threshold(self):
        event = self._event(influence=0.1)
        result = should_store_reflection(event, [])
        assert result["store"] is False
        assert "below_influence_threshold" in result["reason"]

    def test_rejects_generation_depth_exceeded(self):
        event = self._event()
        event.generation_depth = 2
        result = should_store_reflection(event, [])
        assert result["store"] is False
        assert "generation_depth_exceeded" in result["reason"]

    def test_rejects_cooldown_active(self):
        old_event = self._event(source_eid=1, step=80)
        new_event = self._event(source_eid=1, step=100)
        result = should_store_reflection(new_event, [old_event], cooldown_steps=50)
        assert result["store"] is False
        assert "cooldown_active" in result["reason"]

    def test_allows_after_cooldown_expires(self):
        old_event = self._event(source_eid=1, step=10)
        new_event = self._event(source_eid=1, step=100)
        result = should_store_reflection(new_event, [old_event], cooldown_steps=50)
        assert result["store"] is True

    def test_rejects_duplicate_same_step(self):
        """Same source + same step is rejected (cooldown fires at gap=0)."""
        existing = self._event(source_eid=1, step=100)
        duplicate = self._event(source_eid=1, step=100)
        result = should_store_reflection(duplicate, [existing])
        assert result["store"] is False
        # Cooldown fires first (gap=0 < cooldown), which is correct —
        # same-step duplicates are a subset of cooldown violations.
        assert "cooldown_active" in result["reason"] or "duplicate_same_step" in result["reason"]

    def test_different_source_no_cooldown(self):
        old = self._event(source_eid=1, step=95)
        new = self._event(source_eid=2, step=100)
        result = should_store_reflection(new, [old], cooldown_steps=50)
        assert result["store"] is True


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

class TestSpiritReflectionStore:

    def test_store_and_retrieve(self):
        store = _tmp_store()
        event = build_spirit_reflection_event(
            _make_spirit_hit(eid=10), "response text",
            current_step=5, query_text="hello",
            influence_result={"influence_score": 0.6, "influence_reason_tags": ["test"]},
        )
        assert store.store(event) is True
        assert len(store.all_events()) == 1
        assert store.all_events()[0].source_eid == 10

    def test_persistence_across_instances(self):
        tmp = tempfile.mkdtemp()
        path = Path(tmp) / "sr"

        store1 = SpiritReflectionStore(path, base_dir=tmp)
        event = build_spirit_reflection_event(
            _make_spirit_hit(eid=20), "resp", current_step=1, query_text="q",
            influence_result={"influence_score": 0.5, "influence_reason_tags": []},
        )
        store1.store(event)

        # New instance, same path — should load from disk
        store2 = SpiritReflectionStore(path, base_dir=tmp)
        events = store2.all_events()
        assert len(events) == 1
        assert events[0].source_eid == 20
        assert events[0].eligible_for_spirit_return is False

    def test_recent_returns_latest(self):
        store = _tmp_store()
        for i in range(10):
            event = build_spirit_reflection_event(
                _make_spirit_hit(eid=i), f"resp {i}",
                current_step=i, query_text="q",
                influence_result={"influence_score": 0.5, "influence_reason_tags": []},
            )
            store.store(event)
        recent = store.recent(n=3)
        assert len(recent) == 3
        assert recent[-1].source_eid == 9

    def test_stats(self):
        store = _tmp_store()
        for i in range(3):
            event = build_spirit_reflection_event(
                _make_spirit_hit(eid=i, mode="resonance" if i < 2 else "recollection"),
                "resp", current_step=i, query_text="q",
                influence_result={"influence_score": 0.5, "influence_reason_tags": []},
            )
            store.store(event)
        s = store.stats()
        assert s["total_reflections"] == 3
        assert s["unique_sources"] == 3
        assert s["mode_counts"]["resonance"] == 2
        assert s["mode_counts"]["recollection"] == 1

    def test_path_traversal_rejected(self):
        tmp = tempfile.mkdtemp()
        with pytest.raises(ValueError, match="escapes"):
            SpiritReflectionStore(Path("/etc/passwd"), base_dir=tmp)


# ---------------------------------------------------------------------------
# End-to-end: process_spirit_reflections
# ---------------------------------------------------------------------------

class TestProcessReflections:

    def test_no_spirit_hits_no_reflections(self):
        store = _tmp_store()
        blocks = [_make_non_spirit_hit()]
        result = process_spirit_reflections(
            blocks, "response", "query", current_step=1, store=store
        )
        assert result == []
        assert len(store.all_events()) == 0

    def test_low_influence_not_stored(self):
        store = _tmp_store()
        # Candidate summary has zero overlap with response
        blocks = [_make_spirit_hit(summary="quantum physics equations")]
        result = process_spirit_reflections(
            blocks, "The weather is sunny today", "query",
            current_step=1, store=store
        )
        assert result == []

    def test_high_influence_stored(self):
        store = _tmp_store()
        blocks = [_make_spirit_hit(
            eid=42,
            summary="walking through the garden at sunset",
            mode="resonance",
            warmth=0.8,
        )]
        result = process_spirit_reflections(
            blocks,
            "I remember walking through the garden at sunset, it was vivid",
            "tell me about the garden",
            current_step=10, store=store,
            influence_threshold=0.15,  # lower for test determinism
        )
        assert len(result) == 1
        assert result[0].source_eid == 42
        assert result[0].eligible_for_spirit_return is False
        assert len(store.all_events()) == 1

    def test_cooldown_prevents_second_reflection(self):
        store = _tmp_store()
        hit = _make_spirit_hit(eid=50, summary="garden sunset walk")
        response = "garden sunset walk memory returning vividly"

        # First pass stores
        r1 = process_spirit_reflections(
            [hit], response, "q", current_step=10, store=store,
            influence_threshold=0.1,
        )
        assert len(r1) == 1

        # Second pass within cooldown window — blocked
        r2 = process_spirit_reflections(
            [hit], response, "q", current_step=15, store=store,
            influence_threshold=0.1, cooldown_steps=50,
        )
        assert len(r2) == 0

    def test_deep_memory_not_mutated(self):
        """The original hit dict must not be modified by the reflection pipeline."""
        store = _tmp_store()
        hit = _make_spirit_hit(eid=77, summary="test memory content")
        original_keys = set(hit.keys())
        original_summary = hit["summary"]

        process_spirit_reflections(
            [hit], "test memory content returns", "q",
            current_step=1, store=store, influence_threshold=0.1,
        )

        # Original hit dict must be unchanged
        assert set(hit.keys()) == original_keys
        assert hit["summary"] == original_summary
        assert hit["eid"] == 77
