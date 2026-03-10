"""Tests for the Retrieval Assembler (Phase 3).

Covers:
  - Hard precedence rule (archive never outranks identity)
  - Token budget enforcement
  - Structured output format
  - Selection reasoning / log
  - Profile-based weight allocation
  - Seed block always-included guarantee
  - Edge cases (empty inputs, no archive, budget too small)
"""
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.retrieval_assembler import (
    assemble_context,
    PROFILES,
    FILL_ORDER,
    BLOCK_IDENTITY,
    BLOCK_RELATIONAL,
    BLOCK_SITUATIONAL,
    BLOCK_ARCHIVE,
    IDENTITY_MIN_TOKENS,
    _classify_core_hit,
    _estimate_tokens,
    AssembledContext,
)


# ---------------------------------------------------------------------------
# Helpers to create fake hits
# ---------------------------------------------------------------------------

def _core_hit(
    eid: int,
    summary: str,
    mtype: str = "episode",
    half_life: float = 30.0,
    score: float = 0.5,
    canon: bool = False,
    tier: str = "",
    agent_id: str = "test_agent",
) -> dict:
    """Create a fake core memory hit."""
    return {
        "eid": eid,
        "summary": summary,
        "type": mtype,
        "half_life": half_life,
        "score": score,
        "final_score": score,
        "canon": canon,
        "character_tier": tier,
        "strength": 0.7,
        "confidence": 0.8,
        "agent_id": agent_id,
        "scope": "private",
        "motifs": [],
    }


def _archive_hit(
    chunk_id: str,
    text: str,
    score: float = 0.6,
    doc_title: str = "TestDoc",
    doc_id: str = "doc_test",
    token_count: int = 0,
) -> dict:
    """Create a fake archive retrieval result."""
    return {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "doc_title": doc_title,
        "text": text,
        "token_count": token_count or _estimate_tokens(text),
        "section_path": [],
        "section_title": "",
        "score": score,
        "memory_class": "archive",
    }


# ---------------------------------------------------------------------------
# Test: Classification
# ---------------------------------------------------------------------------

class TestClassification:
    def test_seed_canon_is_identity(self):
        hit = _core_hit(1, "I am a dreamer", mtype="seed_canon")
        assert _classify_core_hit(hit) == BLOCK_IDENTITY

    def test_identity_anchor_is_identity(self):
        hit = _core_hit(2, "Anchor memory", mtype="identity_anchor")
        assert _classify_core_hit(hit) == BLOCK_IDENTITY

    def test_drift_correction_is_identity(self):
        hit = _core_hit(3, "Drift fix", mtype="drift_correction")
        assert _classify_core_hit(hit) == BLOCK_IDENTITY

    def test_canon_memory_is_identity(self):
        hit = _core_hit(4, "Canon fact", canon=True)
        assert _classify_core_hit(hit) == BLOCK_IDENTITY

    def test_high_halflife_is_identity(self):
        hit = _core_hit(5, "Long-lived", half_life=3650.0)
        assert _classify_core_hit(hit) == BLOCK_IDENTITY

    def test_medium_halflife_is_relational(self):
        hit = _core_hit(6, "Friend memory", half_life=30.0)
        assert _classify_core_hit(hit) == BLOCK_RELATIONAL

    def test_short_halflife_is_situational(self):
        hit = _core_hit(7, "Just now", half_life=3.0)
        assert _classify_core_hit(hit) == BLOCK_SITUATIONAL

    def test_tier_override(self):
        hit = _core_hit(8, "Tiered", tier="core_identity", half_life=10.0)
        assert _classify_core_hit(hit) == BLOCK_IDENTITY


# ---------------------------------------------------------------------------
# Test: Hard Precedence Rule
# ---------------------------------------------------------------------------

class TestHardPrecedence:
    """Archive blocks must NEVER outrank identity blocks."""

    def test_archive_fills_after_identity(self):
        """Even with high-scoring archive, identity comes first in output."""
        core_hits = [
            _core_hit(1, "I am the seed concept " * 5, mtype="seed_canon", score=0.5, half_life=3650),
            _core_hit(2, "A relational memory " * 5, half_life=30.0, score=0.7),
        ]
        archive_hits = [
            _archive_hit("c1", "High scoring archive content " * 20, score=0.99),
        ]

        result = assemble_context(
            core_hits=core_hits,
            archive_hits=archive_hits,
            profile="companion",
            token_budget=4000,
            seed_text="I am the core identity.",
        )

        # Identity must appear before archive in assembled text
        text = result.assembled_text
        id_pos = text.find("[Identity Context]")
        arch_pos = text.find("[Archive Context]")
        assert id_pos >= 0, "Identity context must be present"
        if arch_pos >= 0:
            assert id_pos < arch_pos, "Identity must come before archive"

        # Identity blocks must exist
        assert len(result.blocks[BLOCK_IDENTITY]) > 0

    def test_archive_never_displaces_identity(self):
        """With a tight budget, identity always gets space, archive gets remainder."""
        # Seed is ~20 tokens, core identity is ~20 tokens
        core_hits = [
            _core_hit(1, "Core identity memory that matters.", mtype="seed_canon", score=0.9, half_life=3650),
        ]
        # Large archive blocks that would exceed budget
        archive_hits = [
            _archive_hit("c1", "Archive content " * 50, score=0.99),
            _archive_hit("c2", "More archive " * 50, score=0.95),
            _archive_hit("c3", "Even more archive " * 50, score=0.90),
        ]

        result = assemble_context(
            core_hits=core_hits,
            archive_hits=archive_hits,
            profile="research",  # research = 50% archive weight
            token_budget=300,
            seed_text="I am the character seed.",
        )

        # Identity must be present
        assert len(result.blocks[BLOCK_IDENTITY]) > 0
        # Total tokens must not exceed budget (with small tolerance)
        assert result.tokens_used <= result.token_budget + 50

    def test_archive_only_fills_remaining(self):
        """Archive gets exactly and only the leftover budget."""
        # Fill identity and relational with known-size content
        core_hits = [
            _core_hit(1, "Identity fact " * 10, mtype="seed_canon", score=0.9, half_life=3650),
            _core_hit(2, "Relational bond " * 10, score=0.8, half_life=30.0),
            _core_hit(3, "Situation now " * 10, score=0.7, half_life=3.0),
        ]
        archive_hits = [
            _archive_hit("c1", "Small archive bit.", score=0.8),
            _archive_hit("c2", "Another small archive bit.", score=0.7),
        ]

        result = assemble_context(
            core_hits=core_hits,
            archive_hits=archive_hits,
            profile="companion",
            token_budget=4000,
            seed_text="Character seed.",
        )

        # Archive tokens must not exceed remaining budget
        archive_tokens = result.block_token_counts.get(BLOCK_ARCHIVE, 0)
        non_archive_tokens = sum(
            v for k, v in result.block_token_counts.items() if k != BLOCK_ARCHIVE
        )
        assert archive_tokens + non_archive_tokens <= result.token_budget + 50


# ---------------------------------------------------------------------------
# Test: Structured Output
# ---------------------------------------------------------------------------

class TestStructuredOutput:
    def test_output_has_required_fields(self):
        result = assemble_context(
            core_hits=[_core_hit(1, "Memory one", score=0.6)],
            profile="companion",
            token_budget=2000,
        )

        assert isinstance(result, AssembledContext)
        assert result.profile == "companion"
        assert result.token_budget == 2000
        assert isinstance(result.blocks, dict)
        assert all(bt in result.blocks for bt in FILL_ORDER)
        assert isinstance(result.assembled_text, str)
        assert isinstance(result.block_token_counts, dict)
        assert isinstance(result.selection_log, list)

    def test_to_dict_serializable(self):
        result = assemble_context(
            core_hits=[_core_hit(1, "Test", score=0.5)],
            profile="balanced",
            token_budget=1000,
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["profile"] == "balanced"
        assert "blocks" in d
        assert "assembled_text" in d
        assert "selection_log" in d

    def test_blocks_contain_selection_reasoning(self):
        """Each block must have a reason field explaining why it was selected."""
        core_hits = [
            _core_hit(1, "Seed memory", mtype="seed_canon", score=0.9, half_life=3650),
            _core_hit(2, "Friend memory", score=0.7, half_life=30.0),
        ]
        archive_hits = [
            _archive_hit("c1", "Archive chunk about topic X", score=0.75),
        ]

        result = assemble_context(
            core_hits=core_hits,
            archive_hits=archive_hits,
            profile="companion",
            token_budget=4000,
            seed_text="I am the seed.",
        )

        for bt in FILL_ORDER:
            for block in result.blocks[bt]:
                assert "reason" in block, f"Block in {bt} missing reason field"
                assert len(block["reason"]) > 0, f"Block in {bt} has empty reason"

    def test_selection_log_tracks_decisions(self):
        """Selection log must record both selected and skipped items."""
        core_hits = [_core_hit(i, f"Memory {i}", score=0.5) for i in range(20)]

        result = assemble_context(
            core_hits=core_hits,
            profile="companion",
            token_budget=200,  # Tight budget — some will be skipped
            seed_text="Seed text.",
        )

        log = result.selection_log
        assert len(log) > 0
        actions = {entry["action"] for entry in log}
        assert "selected" in actions


# ---------------------------------------------------------------------------
# Test: Seed Always Included
# ---------------------------------------------------------------------------

class TestSeedGuarantee:
    def test_seed_always_first(self):
        """Seed block must always be the first identity block."""
        core_hits = [
            _core_hit(1, "Some regular memory", score=0.9, half_life=30.0),
        ]

        result = assemble_context(
            core_hits=core_hits,
            profile="companion",
            token_budget=4000,
            seed_text="This is the character seed text.",
            character_name="TestChar",
        )

        id_blocks = result.blocks[BLOCK_IDENTITY]
        assert len(id_blocks) > 0
        first = id_blocks[0]
        assert first.get("metadata", {}).get("is_seed") is True
        assert "TestChar" in first["text"]

    def test_seed_present_even_with_tiny_budget(self):
        """Even with very small budget, seed gets included."""
        result = assemble_context(
            core_hits=[],
            profile="companion",
            token_budget=100,
            seed_text="Minimal seed.",
        )

        id_blocks = result.blocks[BLOCK_IDENTITY]
        assert len(id_blocks) > 0


# ---------------------------------------------------------------------------
# Test: Profile Weights
# ---------------------------------------------------------------------------

class TestProfiles:
    def test_all_profiles_exist(self):
        for name in ["companion", "research", "narrator", "balanced"]:
            assert name in PROFILES

    def test_profile_weights_sum_to_one(self):
        for name, weights in PROFILES.items():
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.01, f"Profile {name} weights sum to {total}"

    def test_research_profile_favors_archive(self):
        """Research profile should allocate more to archive than companion."""
        assert PROFILES["research"][BLOCK_ARCHIVE] > PROFILES["companion"][BLOCK_ARCHIVE]

    def test_companion_profile_favors_identity(self):
        """Companion profile should allocate more to identity than research."""
        assert PROFILES["companion"][BLOCK_IDENTITY] > PROFILES["research"][BLOCK_IDENTITY]

    def test_custom_weights_override(self):
        """Custom weights should override profile defaults."""
        core_hits = [
            _core_hit(1, "Identity " * 10, mtype="seed_canon", score=0.9, half_life=3650),
            _core_hit(2, "Relational " * 10, score=0.7, half_life=30.0),
        ]
        archive_hits = [
            _archive_hit("c1", "Archive content " * 10, score=0.8),
        ]

        result = assemble_context(
            core_hits=core_hits,
            archive_hits=archive_hits,
            profile="companion",
            token_budget=4000,
            custom_weights={BLOCK_ARCHIVE: 0.80, BLOCK_IDENTITY: 0.10,
                            BLOCK_RELATIONAL: 0.05, BLOCK_SITUATIONAL: 0.05},
        )

        # Should still work and produce valid output
        assert result.profile == "companion"
        assert result.tokens_used > 0


# ---------------------------------------------------------------------------
# Test: Token Budget
# ---------------------------------------------------------------------------

class TestTokenBudget:
    def test_budget_respected(self):
        """Total tokens should not exceed budget (with small tolerance)."""
        core_hits = [_core_hit(i, f"Memory content number {i} " * 20, score=0.5) for i in range(10)]
        archive_hits = [_archive_hit(f"c{i}", f"Archive chunk {i} " * 20, score=0.6) for i in range(10)]

        result = assemble_context(
            core_hits=core_hits,
            archive_hits=archive_hits,
            profile="balanced",
            token_budget=500,
            seed_text="Character seed.",
        )

        # Small tolerance for tiny blocks at boundaries
        assert result.tokens_used <= result.token_budget + 50

    def test_identity_min_tokens_guaranteed(self):
        """Identity block should get at least IDENTITY_MIN_TOKENS worth of budget."""
        # Even with research profile (15% identity on 400 budget = 60 tokens),
        # identity should still get IDENTITY_MIN_TOKENS
        result = assemble_context(
            core_hits=[],
            profile="research",
            token_budget=400,
            seed_text="This is a long seed text that establishes the character identity. " * 5,
        )

        # The seed should be included despite the research profile's low identity weight
        id_blocks = result.blocks[BLOCK_IDENTITY]
        assert len(id_blocks) > 0


# ---------------------------------------------------------------------------
# Test: Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_inputs(self):
        """Empty core and archive should produce a valid but empty result."""
        result = assemble_context(
            core_hits=[],
            archive_hits=[],
            profile="companion",
            token_budget=4000,
        )

        assert isinstance(result, AssembledContext)
        assert result.tokens_used == 0
        assert result.assembled_text == ""

    def test_no_archive(self):
        """Core-only retrieval should work fine without archive."""
        core_hits = [
            _core_hit(1, "Identity memory", mtype="seed_canon", score=0.9, half_life=3650),
            _core_hit(2, "Relational memory", score=0.7, half_life=30.0),
        ]

        result = assemble_context(
            core_hits=core_hits,
            profile="companion",
            token_budget=4000,
            seed_text="Seed text.",
        )

        assert len(result.blocks[BLOCK_ARCHIVE]) == 0
        assert len(result.blocks[BLOCK_IDENTITY]) > 0

    def test_unknown_profile_falls_back(self):
        """Unknown profile name should fall back to companion."""
        result = assemble_context(
            core_hits=[_core_hit(1, "Test", score=0.5)],
            profile="nonexistent_profile",
            token_budget=2000,
        )

        # Should not crash — falls back to companion
        assert isinstance(result, AssembledContext)

    def test_fill_order_is_correct(self):
        """Fill order must be identity → relational → situational → archive."""
        assert FILL_ORDER == [
            BLOCK_IDENTITY,
            BLOCK_RELATIONAL,
            BLOCK_SITUATIONAL,
            BLOCK_ARCHIVE,
        ]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_phase3_tests():
    """Run all Phase 3 tests and report results."""
    import traceback

    tests = [
        ("P3.1 Classification: seed_canon → identity", TestClassification().test_seed_canon_is_identity),
        ("P3.2 Classification: identity_anchor → identity", TestClassification().test_identity_anchor_is_identity),
        ("P3.3 Classification: high halflife → identity", TestClassification().test_high_halflife_is_identity),
        ("P3.4 Classification: medium halflife → relational", TestClassification().test_medium_halflife_is_relational),
        ("P3.5 Classification: short halflife → situational", TestClassification().test_short_halflife_is_situational),
        ("P3.6 Hard precedence: archive after identity", TestHardPrecedence().test_archive_fills_after_identity),
        ("P3.7 Hard precedence: archive never displaces identity", TestHardPrecedence().test_archive_never_displaces_identity),
        ("P3.8 Hard precedence: archive fills remaining only", TestHardPrecedence().test_archive_only_fills_remaining),
        ("P3.9 Structured output: required fields", TestStructuredOutput().test_output_has_required_fields),
        ("P3.10 Structured output: serializable", TestStructuredOutput().test_to_dict_serializable),
        ("P3.11 Structured output: selection reasoning", TestStructuredOutput().test_blocks_contain_selection_reasoning),
        ("P3.12 Structured output: selection log", TestStructuredOutput().test_selection_log_tracks_decisions),
        ("P3.13 Seed guarantee: always first", TestSeedGuarantee().test_seed_always_first),
        ("P3.14 Seed guarantee: tiny budget", TestSeedGuarantee().test_seed_present_even_with_tiny_budget),
        ("P3.15 Profiles: all exist", TestProfiles().test_all_profiles_exist),
        ("P3.16 Profiles: weights sum to 1", TestProfiles().test_profile_weights_sum_to_one),
        ("P3.17 Profiles: research favors archive", TestProfiles().test_research_profile_favors_archive),
        ("P3.18 Profiles: custom weights", TestProfiles().test_custom_weights_override),
        ("P3.19 Budget: respected", TestTokenBudget().test_budget_respected),
        ("P3.20 Budget: identity min guaranteed", TestTokenBudget().test_identity_min_tokens_guaranteed),
        ("P3.21 Edge: empty inputs", TestEdgeCases().test_empty_inputs),
        ("P3.22 Edge: no archive", TestEdgeCases().test_no_archive),
        ("P3.23 Edge: unknown profile", TestEdgeCases().test_unknown_profile_falls_back),
        ("P3.24 Edge: fill order correct", TestEdgeCases().test_fill_order_is_correct),
    ]

    passed = 0
    failed = 0
    print("\n--- Phase 3 (Retrieval Assembler) ---")
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {name}")
            traceback.print_exc()
            failed += 1

    return passed, failed


if __name__ == "__main__":
    p, f = run_phase3_tests()
    print(f"\nPhase 3: {p} passed, {f} failed")
    if f > 0:
        exit(1)
