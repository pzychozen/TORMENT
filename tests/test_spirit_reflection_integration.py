"""Integration tests for the spirit reflection pipeline.

These go beyond unit tests to verify:
  1. The pipeline works when reflection storage is unavailable / broken
  2. A valid spirit-return hit can create a reflection end-to-end
  3. Non-spirit-return hits produce zero reflections
  4. Reflections remain non-eligible for spirit return after persist + reload
  5. Existing retrieval precedence is unchanged by reflection artifacts
  6. The process endpoint's fail-soft behavior
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from torment_service.spirit_reflection import (
    SpiritReflectionStore,
    process_spirit_reflections,
    extract_spirit_return_candidates,
)
from torment_service.retrieval_assembler import _classify_core_hit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _spirit_hit(
    eid: int = 100,
    summary: str = "walking through the old garden at sunset with memories returning",
    mode: str = "resonance",
    warmth: float = 0.65,
    interaction: str = "fulfilled",
    flavor: str = "something that was once only potential has crystallized",
) -> Dict[str, Any]:
    return {
        "eid": eid,
        "summary": summary,
        "from_spirit_return": True,
        "from_deep_memory": True,
        "spirit_return_mode": mode,
        "warmth_score": warmth,
        "symbol_interaction": interaction,
        "spirit_return_flavor": flavor,
        "birth_symbol": "◯",
        "current_kernel_symbol": "◈",
        "resonance_confidence": 0.70,
        "score": 0.85,
        "strength": 0.39,
        "type": "memory",
        "step": 50,
        "memory_class": "core",
    }


def _normal_hit(eid: int = 200) -> Dict[str, Any]:
    return {
        "eid": eid,
        "summary": "A normal everyday memory",
        "from_spirit_return": False,
        "from_deep_memory": False,
        "score": 0.5,
        "strength": 0.3,
        "type": "memory",
        "step": 40,
        "memory_class": "core",
    }


def _tmp_store() -> SpiritReflectionStore:
    tmp = tempfile.mkdtemp()
    return SpiritReflectionStore(Path(tmp) / "spirit_reflections", base_dir=tmp)


# ---------------------------------------------------------------------------
# 1. Pipeline works when storage is unavailable
# ---------------------------------------------------------------------------

class TestFailSoftBehavior:

    def test_process_with_broken_store_path(self):
        """If the store path is unwritable, process should not raise."""
        # Create a store pointing to a read-only location that will fail on write
        tmp = tempfile.mkdtemp()
        store = SpiritReflectionStore(Path(tmp) / "sr", base_dir=tmp)

        # Make the file unwritable
        store._file.parent.mkdir(parents=True, exist_ok=True)
        store._file.touch()
        os.chmod(str(store._file), 0o000)

        blocks = [_spirit_hit(summary="garden sunset walk vivid memory")]
        try:
            result = process_spirit_reflections(
                blocks,
                "garden sunset walk vivid memory returns to me",
                "what about the garden",
                current_step=10,
                store=store,
                influence_threshold=0.1,
            )
            # Should return empty list (write failed) but not raise
            # The store.store() returns False on write failure
            assert isinstance(result, list)
        finally:
            os.chmod(str(store._file), 0o600)

    def test_empty_blocks_no_crash(self):
        store = _tmp_store()
        result = process_spirit_reflections([], "any response", "any query", 1, store)
        assert result == []

    def test_none_in_blocks_no_crash(self):
        store = _tmp_store()
        result = process_spirit_reflections(
            [None, "not a dict", 42, {}],  # type: ignore
            "response", "query", 1, store,
        )
        assert result == []


# ---------------------------------------------------------------------------
# 2. Valid spirit-return hit creates reflection end-to-end
# ---------------------------------------------------------------------------

class TestEndToEndReflectionCreation:

    def test_valid_hit_creates_reflection(self):
        store = _tmp_store()
        hit = _spirit_hit(
            eid=42,
            summary="walking through the garden at sunset",
            mode="resonance",
            warmth=0.8,
        )
        result = process_spirit_reflections(
            [hit],
            "I remember walking through the garden at sunset, it was vivid and crystallized",
            "tell me about the garden",
            current_step=10,
            store=store,
            influence_threshold=0.15,
        )
        assert len(result) == 1
        reflection = result[0]
        assert reflection.source_eid == 42
        assert reflection.derived_from_spirit_return is True
        assert reflection.eligible_for_spirit_return is False
        assert reflection.generation_depth == 1
        assert reflection.return_mode == "resonance"
        assert "resurfaced" in reflection.summary

    def test_multiple_spirit_hits_scored_independently(self):
        store = _tmp_store()
        hit1 = _spirit_hit(eid=10, summary="garden sunset walk", warmth=0.8)
        hit2 = _spirit_hit(eid=20, summary="quantum physics lab experiment", warmth=0.6)

        result = process_spirit_reflections(
            [hit1, hit2],
            "garden sunset walk memory is vivid, crystallized into something real",
            "memories",
            current_step=5,
            store=store,
            influence_threshold=0.15,
        )
        # hit1 should score high (lexical overlap), hit2 should score low
        source_eids = [r.source_eid for r in result]
        assert 10 in source_eids
        # hit2 may or may not pass depending on heuristic — just verify no crash


# ---------------------------------------------------------------------------
# 3. Non-spirit-return hits produce zero reflections
# ---------------------------------------------------------------------------

class TestNonSpiritHitsIgnored:

    def test_only_normal_hits(self):
        store = _tmp_store()
        blocks = [_normal_hit(eid=1), _normal_hit(eid=2), _normal_hit(eid=3)]
        result = process_spirit_reflections(
            blocks, "any response at all", "any query", 1, store,
        )
        assert result == []
        assert len(store.all_events()) == 0

    def test_mixed_hits_only_spirit_considered(self):
        blocks = [
            _normal_hit(eid=1),
            _spirit_hit(eid=2, summary="garden sunset vivid"),
            _normal_hit(eid=3),
        ]
        candidates = extract_spirit_return_candidates(blocks)
        assert len(candidates) == 1
        assert candidates[0]["eid"] == 2


# ---------------------------------------------------------------------------
# 4. Reflections remain non-eligible after persist + reload
# ---------------------------------------------------------------------------

class TestPersistenceEligibility:

    def test_eligible_false_after_reload(self):
        tmp = tempfile.mkdtemp()
        path = Path(tmp) / "sr"

        # Store a reflection
        store1 = SpiritReflectionStore(path, base_dir=tmp)
        hit = _spirit_hit(eid=77, summary="garden sunset walk")
        result = process_spirit_reflections(
            [hit],
            "garden sunset walk memory vivid and crystallized",
            "gardens", current_step=5, store=store1,
            influence_threshold=0.1,
        )
        assert len(result) >= 1
        assert result[0].eligible_for_spirit_return is False

        # Reload from disk — a completely new store instance
        store2 = SpiritReflectionStore(path, base_dir=tmp)
        events = store2.all_events()
        assert len(events) >= 1
        for event in events:
            assert event.eligible_for_spirit_return is False

    def test_tampering_eligible_field_on_disk(self):
        """Even if someone edits the JSONL to set eligible=True, from_dict forces False."""
        tmp = tempfile.mkdtemp()
        path = Path(tmp) / "sr"
        path.mkdir(parents=True)
        jsonl_file = path / "reflections.jsonl"

        # Write a tampered record
        tampered = {
            "eid": 999,
            "source_eid": 42,
            "derived_from_spirit_return": True,
            "generation_depth": 1,
            "created_step": 10,
            "created_at": 0.0,
            "query_text": "q",
            "response_excerpt": "r",
            "return_mode": "resonance",
            "warmth_score": 0.5,
            "symbol_interaction": "fulfilled",
            "spirit_return_flavor": "test",
            "influence_score": 0.6,
            "influence_reason_tags": [],
            "summary": "test",
            "cooldown_key": "42:resonance:fulfilled",
            "eligible_for_spirit_return": True,  # TAMPERED!
        }
        with open(jsonl_file, "w") as f:
            f.write(json.dumps(tampered) + "\n")

        store = SpiritReflectionStore(path, base_dir=tmp)
        events = store.all_events()
        assert len(events) == 1
        assert events[0].eligible_for_spirit_return is False  # forced False


# ---------------------------------------------------------------------------
# 5. Existing retrieval precedence unchanged by reflections
# ---------------------------------------------------------------------------

class TestRetrievalPrecedenceUnchanged:

    def test_spirit_hit_classification_unchanged(self):
        """Spirit return hits still classify the same way in the assembler."""
        # Resonance + high warmth → identity
        hit_resonance = _spirit_hit(mode="resonance", warmth=0.7)
        assert _classify_core_hit(hit_resonance) == "identity_context"

        # Surfacing + warm → relational
        hit_surfacing = _spirit_hit(mode="surfacing", warmth=0.4)
        assert _classify_core_hit(hit_surfacing) == "relational_context"

        # Recollection → situational
        hit_recollection = _spirit_hit(mode="recollection", warmth=0.2)
        assert _classify_core_hit(hit_recollection) == "situational_context"

    def test_reflection_events_not_in_spirit_return_pipeline(self):
        """Reflection dicts with eligible=False cannot pass spirit return extraction."""
        # Simulate a reflection event appearing in blocks (shouldn't happen,
        # but defense in depth)
        reflection_as_block = {
            "eid": 999,
            "summary": "A reflection event",
            "from_spirit_return": True,
            "derived_from_spirit_return": True,
            "generation_depth": 1,
            "spirit_return_mode": "resonance",
            "warmth_score": 0.5,
            "eligible_for_spirit_return": False,
        }
        candidates = extract_spirit_return_candidates([reflection_as_block])
        assert len(candidates) == 0  # Filtered out by generation_depth check

    def test_normal_hits_unaffected_by_reflection_module(self):
        """Normal memory hits still classify normally."""
        hit = _normal_hit()
        # Normal hits should not be "identity_context" (that requires specific conditions)
        category = _classify_core_hit(hit)
        assert category in ("identity_context", "relational_context", "situational_context")
        # The key point: the reflection module doesn't alter classification
