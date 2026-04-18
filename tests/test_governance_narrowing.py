"""
Invariant 6 test: Governance can narrow legality but never widen it.

Asserts that governance-sensitive signal can only take the action
toward GOVERNANCE_REVIEW / DEFER / NO_OP (narrower outcomes), never
toward a more permissive action family than what the mode's legal
set allows.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 (invariant 6)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md M2 / S2
"""
import pytest

from torment_service.action_policy import (
    apply_legality,
    is_legal,
)
from torment_service.thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveMode,
    CognitiveModeDecision,
    TaskFrame,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _frame(
    governance_sensitive: bool = False,
    ambiguity_score: float = 0.0,
    tool_need: bool = False,
):
    return TaskFrame(
        workspace_id="ws",
        agent_id="agent",
        raw_input="test",
        normalized_input="test",
        governance_sensitive=governance_sensitive,
        ambiguity_score=ambiguity_score,
        tool_need=tool_need,
    )


def _mode(m: CognitiveMode):
    return CognitiveModeDecision(chosen_mode=m, reason="test")


def _action(at: ActionType):
    return ActionDecision(action=at, reason="test")


# Narrowing outcome set — governance can only move toward these.
NARROWING_TARGETS = {
    ActionType.GOVERNANCE_REVIEW,
    ActionType.DEFER,
    ActionType.ASK_CLARIFICATION,
    ActionType.NO_OP,
}


# ---------------------------------------------------------------------------
# Governance narrows
# ---------------------------------------------------------------------------


class TestGovernanceNarrows:
    """Governance-sensitive input narrows to GOVERNANCE_REVIEW / DEFER / ASK_CLARIFICATION / NO_OP."""

    def test_governed_mode_illegal_answer_routes_to_review(self):
        """In GOVERNED mode, governance-sensitive + illegal ANSWER
        produces GOVERNANCE_REVIEW."""
        result = apply_legality(
            _action(ActionType.ANSWER),
            _mode(CognitiveMode.GOVERNED),
            _frame(governance_sensitive=True),
        )
        assert result.action.action == ActionType.GOVERNANCE_REVIEW

    def test_identity_sensitive_illegal_use_tool_routes_to_review(self):
        """USE_TOOL is illegal in IDENTITY_SENSITIVE. Governance-
        sensitive signal routes to GOVERNANCE_REVIEW (which IS legal
        there with the ⚠ qualifier)."""
        result = apply_legality(
            _action(ActionType.USE_TOOL),
            _mode(CognitiveMode.IDENTITY_SENSITIVE),
            _frame(governance_sensitive=True),
        )
        assert result.action.action == ActionType.GOVERNANCE_REVIEW


# ---------------------------------------------------------------------------
# Governance never widens — the core invariant 6 check
# ---------------------------------------------------------------------------


class TestGovernanceNeverWidens:
    """Governance-sensitive flag cannot produce an action outside the mode's legal set."""

    @pytest.mark.parametrize("mode", list(CognitiveMode))
    @pytest.mark.parametrize(
        "original_action",
        [
            ActionType.ANSWER,
            ActionType.USE_TOOL,
            ActionType.WRITE_MEMORY,  # assimilation outcome (never legal anywhere)
            ActionType.PROPOSE_SHARE,  # assimilation outcome
        ],
    )
    def test_governance_output_always_legal_for_mode(
        self, mode, original_action
    ):
        """Under any (mode, original_action) combo with governance-
        sensitive=True, apply_legality's output must be legal for mode."""
        result = apply_legality(
            _action(original_action),
            _mode(mode),
            _frame(governance_sensitive=True),
        )
        assert is_legal(mode, result.action.action), (
            f"Governance-sensitive fallback in mode {mode.value!r} "
            f"from {original_action.value!r} produced "
            f"{result.action.action.value!r}, which is NOT in legal set. "
            f"Invariant 6 violation: governance widened legality."
        )

    @pytest.mark.parametrize("mode", list(CognitiveMode))
    def test_governance_output_within_narrowing_set(self, mode):
        """Governance fallback output is always one of the narrowing
        targets (GOVERNANCE_REVIEW, DEFER, ASK_CLARIFICATION, NO_OP),
        never ANSWER or USE_TOOL etc."""
        result = apply_legality(
            _action(ActionType.USE_TOOL),  # illegal in most modes
            _mode(mode),
            _frame(governance_sensitive=True),
        )
        # USE_TOOL is legal only in TOOL mode; for TOOL mode the
        # legal action passes through (not a fallback case).
        if result.fallback_reason is None:
            # legal passthrough; only happens in TOOL mode
            assert mode == CognitiveMode.TOOL
        else:
            assert result.action.action in NARROWING_TARGETS, (
                f"Governance fallback in {mode.value!r} produced "
                f"{result.action.action.value!r}, which is not one of "
                f"the narrowing targets {[a.value for a in NARROWING_TARGETS]}."
            )


# ---------------------------------------------------------------------------
# Governance prefers GOVERNANCE_REVIEW when available
# ---------------------------------------------------------------------------


class TestGovernancePrefersReview:
    """When GOVERNANCE_REVIEW is legal for the mode, governance
    fallback prefers it over DEFER or ASK_CLARIFICATION."""

    @pytest.mark.parametrize(
        "mode",
        [CognitiveMode.GOVERNED, CognitiveMode.IDENTITY_SENSITIVE],
    )
    def test_prefers_governance_review_where_legal(self, mode):
        result = apply_legality(
            _action(ActionType.USE_TOOL),
            _mode(mode),
            _frame(governance_sensitive=True, ambiguity_score=0.9),
        )
        assert result.action.action == ActionType.GOVERNANCE_REVIEW, (
            f"Governance fallback in {mode.value!r} should prefer "
            f"GOVERNANCE_REVIEW over any other narrowing target, "
            f"got {result.action.action.value!r}."
        )

    def test_falls_back_when_governance_review_not_legal(self):
        """Modes without GOVERNANCE_REVIEW legal fall to the next step."""
        # FAST has {ANSWER, NO_OP}. GOVERNANCE_REVIEW not legal.
        # USE_TOOL illegal. No DEFER, no ASK_CLARIFICATION legal.
        # → NO_OP terminus.
        result = apply_legality(
            _action(ActionType.USE_TOOL),
            _mode(CognitiveMode.FAST),
            _frame(governance_sensitive=True),
        )
        assert result.action.action == ActionType.NO_OP
        # Must not have widened
        assert is_legal(CognitiveMode.FAST, result.action.action)
