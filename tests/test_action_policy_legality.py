"""
Invariant 7 test: pre-execution Mode→legal-intents table enforcement.

Asserts the shape and contents of MODE_LEGAL_INTENTS match the
ratified doctrine Part 3 table, and that is_legal() correctly
reports per-cell legality.

Cross-checks invariant 4: no assimilation outcome (WRITE_MEMORY,
PROPOSE_SHARE, CREATE_ARCHIVE_NOTE) appears as pre-execution-legal
in any mode.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 3
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 (invariant 7)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S2 / M2
"""
import pytest

from torment_service.action_policy import MODE_LEGAL_INTENTS, is_legal
from torment_service.thinking_models import ActionType, CognitiveMode


# ---------------------------------------------------------------------------
# Canonical doctrine Part 3 table (pre-execution legality)
# ---------------------------------------------------------------------------

EXPECTED_LEGAL = {
    CognitiveMode.FAST: {
        ActionType.ANSWER,
        ActionType.NO_OP,
    },
    CognitiveMode.RETRIEVAL: {
        ActionType.ANSWER,
        ActionType.ASK_CLARIFICATION,
        ActionType.DEFER,
        ActionType.NO_OP,
    },
    CognitiveMode.REFLECTIVE: {
        ActionType.ANSWER,
        ActionType.ASK_CLARIFICATION,
        ActionType.DEFER,
        ActionType.NO_OP,
    },
    CognitiveMode.TOOL: {
        ActionType.ASK_CLARIFICATION,
        ActionType.DEFER,
        ActionType.USE_TOOL,
        ActionType.NO_OP,
    },
    CognitiveMode.GOVERNED: {
        ActionType.ASK_CLARIFICATION,
        ActionType.DEFER,
        ActionType.NO_OP,
        ActionType.GOVERNANCE_REVIEW,
    },
    CognitiveMode.IDENTITY_SENSITIVE: {
        ActionType.ANSWER,
        ActionType.ASK_CLARIFICATION,
        ActionType.DEFER,
        ActionType.NO_OP,
        ActionType.GOVERNANCE_REVIEW,
    },
    CognitiveMode.LIVE_SOCIAL: {
        ActionType.ANSWER,
        ActionType.ASK_CLARIFICATION,
        ActionType.NO_OP,
    },
}


# ---------------------------------------------------------------------------
# Table shape
# ---------------------------------------------------------------------------


def test_mode_legal_intents_table_matches_doctrine_part_3():
    """The enforcement table matches the ratified doctrine Part 3 exactly."""
    assert MODE_LEGAL_INTENTS == EXPECTED_LEGAL


def test_every_cognitive_mode_has_legal_set():
    """Every mode has at least one legal intent."""
    for mode in tuple(CognitiveMode):
        assert mode in MODE_LEGAL_INTENTS
        assert len(MODE_LEGAL_INTENTS[mode]) > 0


def test_no_op_is_legal_in_every_mode():
    """NO_OP is the terminal fail-closed option and must be legal everywhere."""
    for mode in tuple(CognitiveMode):
        assert ActionType.NO_OP in MODE_LEGAL_INTENTS[mode]


# ---------------------------------------------------------------------------
# Per-cell legality (is_legal)
# ---------------------------------------------------------------------------


class TestIsLegal:
    """is_legal() correctly reports per-cell legality."""

    def test_answer_legal_in_fast(self):
        assert is_legal(CognitiveMode.FAST, ActionType.ANSWER)

    def test_answer_illegal_in_tool(self):
        assert not is_legal(CognitiveMode.TOOL, ActionType.ANSWER)

    def test_answer_illegal_in_governed(self):
        assert not is_legal(CognitiveMode.GOVERNED, ActionType.ANSWER)

    def test_use_tool_legal_only_in_tool_mode(self):
        for mode in tuple(CognitiveMode):
            if mode == CognitiveMode.TOOL:
                assert is_legal(mode, ActionType.USE_TOOL)
            else:
                assert not is_legal(mode, ActionType.USE_TOOL), (
                    f"USE_TOOL must be illegal in {mode.value}, "
                    f"but is_legal returned True"
                )

    def test_defer_not_legal_in_fast(self):
        assert not is_legal(CognitiveMode.FAST, ActionType.DEFER)

    def test_defer_not_legal_in_live_social(self):
        assert not is_legal(CognitiveMode.LIVE_SOCIAL, ActionType.DEFER)

    def test_governance_review_legal_in_governed(self):
        assert is_legal(CognitiveMode.GOVERNED, ActionType.GOVERNANCE_REVIEW)

    def test_governance_review_legal_in_identity_sensitive(self):
        assert is_legal(
            CognitiveMode.IDENTITY_SENSITIVE, ActionType.GOVERNANCE_REVIEW
        )

    def test_governance_review_illegal_in_fast(self):
        assert not is_legal(CognitiveMode.FAST, ActionType.GOVERNANCE_REVIEW)


# ---------------------------------------------------------------------------
# Invariant 4 cross-check: assimilation outcomes never pre-execution-legal
# ---------------------------------------------------------------------------


class TestAssimilationOutcomesNeverLegal:
    """Invariant 4 cross-check via the legality table."""

    ASSIMILATION_OUTCOMES = {
        ActionType.WRITE_MEMORY,
        ActionType.PROPOSE_SHARE,
        ActionType.CREATE_ARCHIVE_NOTE,
    }

    def test_no_assimilation_outcome_in_any_legal_set(self):
        """Assimilation outcomes never appear as pre-execution-legal."""
        for mode in tuple(CognitiveMode):
            for outcome in self.ASSIMILATION_OUTCOMES:
                assert outcome not in MODE_LEGAL_INTENTS[mode], (
                    f"Assimilation outcome {outcome.value!r} in "
                    f"legal set for mode {mode.value!r}. "
                    f"Violates invariant 4."
                )

    @pytest.mark.parametrize(
        "mode", list(CognitiveMode)
    )
    @pytest.mark.parametrize(
        "outcome",
        [
            ActionType.WRITE_MEMORY,
            ActionType.PROPOSE_SHARE,
            ActionType.CREATE_ARCHIVE_NOTE,
        ],
    )
    def test_is_legal_rejects_assimilation_outcome(self, mode, outcome):
        assert not is_legal(mode, outcome), (
            f"is_legal({mode.value}, {outcome.value}) returned True; "
            f"violates invariant 4."
        )
