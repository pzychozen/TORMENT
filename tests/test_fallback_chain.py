"""
Invariant 9 test: Fallback chain runs closed, not open.

Asserts that apply_legality enforces the Part 2.5 fallback chain:
1. governance-sensitive + GOVERNANCE_REVIEW legal → GOVERNANCE_REVIEW
2. high ambiguity + ASK_CLARIFICATION legal → ASK_CLARIFICATION
3. DEFER legal → DEFER
4. otherwise → NO_OP with reason

The chain never silently widens legality. Every fallback output is a
member of MODE_LEGAL_INTENTS[mode] for the current mode.

Acceptance for slice plan M2:
    mode=TOOL with no tool_need → choose_action returns ANSWER →
    apply_legality must downgrade to DEFER or NO_OP, never ANSWER.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 2.5 (fallback chain)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 (invariant 9)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md M2
"""
import pytest

from torment_service.action_policy import (
    MODE_LEGAL_INTENTS,
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
    identity_sensitive: bool = False,
):
    return TaskFrame(
        workspace_id="ws",
        agent_id="agent",
        raw_input="test",
        normalized_input="test",
        governance_sensitive=governance_sensitive,
        ambiguity_score=ambiguity_score,
        tool_need=tool_need,
        identity_sensitive=identity_sensitive,
    )


def _mode(m: CognitiveMode):
    return CognitiveModeDecision(chosen_mode=m, reason="test")


def _action(at: ActionType):
    return ActionDecision(action=at, reason="test")


# ---------------------------------------------------------------------------
# Legal action passes through unchanged
# ---------------------------------------------------------------------------


class TestLegalActionPassesThrough:
    """When action is legal for mode, apply_legality returns it unchanged."""

    def test_answer_in_fast_passes(self):
        result = apply_legality(
            _action(ActionType.ANSWER),
            _mode(CognitiveMode.FAST),
            _frame(),
        )
        assert result.action.action == ActionType.ANSWER
        assert result.original_action_type is None
        assert result.fallback_reason is None

    def test_use_tool_in_tool_mode_passes(self):
        result = apply_legality(
            _action(ActionType.USE_TOOL),
            _mode(CognitiveMode.TOOL),
            _frame(tool_need=True),
        )
        assert result.action.action == ActionType.USE_TOOL
        assert result.fallback_reason is None

    def test_governance_review_in_governed_passes(self):
        result = apply_legality(
            _action(ActionType.GOVERNANCE_REVIEW),
            _mode(CognitiveMode.GOVERNED),
            _frame(governance_sensitive=True),
        )
        assert result.action.action == ActionType.GOVERNANCE_REVIEW
        assert result.fallback_reason is None


# ---------------------------------------------------------------------------
# The M2 acceptance case
# ---------------------------------------------------------------------------


class TestM2AcceptanceCase:
    """Explicit acceptance from the slice plan.

    'A unit test with mode=TOOL and no tool-need-detected input
    receives NO_OP or DEFER (per fallback), never ANSWER.'
    """

    def test_tool_mode_answer_falls_to_defer_or_no_op_never_answer(self):
        result = apply_legality(
            _action(ActionType.ANSWER),
            _mode(CognitiveMode.TOOL),
            _frame(tool_need=False),
        )
        assert result.action.action in {ActionType.DEFER, ActionType.NO_OP}
        assert result.action.action != ActionType.ANSWER
        assert result.original_action_type == ActionType.ANSWER
        assert result.fallback_reason is not None


# ---------------------------------------------------------------------------
# Fallback chain step order
# ---------------------------------------------------------------------------


class TestFallbackChainOrder:
    """Fallback chain applies in the declared Part 2.5 order."""

    def test_step_1_governance_sensitive_prefers_governance_review(self):
        """Governance route beats DEFER/ASK_CLARIFICATION/NO_OP."""
        result = apply_legality(
            _action(ActionType.ANSWER),
            _mode(CognitiveMode.GOVERNED),
            _frame(governance_sensitive=True, ambiguity_score=0.8),
        )
        assert result.action.action == ActionType.GOVERNANCE_REVIEW
        assert result.fallback_reason == "governance_sensitive_narrowing"

    def test_step_2_high_ambiguity_prefers_ask_clarification(self):
        """High ambiguity beats DEFER when governance is not active."""
        result = apply_legality(
            _action(ActionType.ANSWER),
            _mode(CognitiveMode.TOOL),
            _frame(governance_sensitive=False, ambiguity_score=0.75),
        )
        assert result.action.action == ActionType.ASK_CLARIFICATION
        assert result.fallback_reason == "ambiguity_clarification_fallback"

    def test_step_3_defer_when_legal(self):
        """DEFER when no governance and no high ambiguity."""
        result = apply_legality(
            _action(ActionType.ANSWER),
            _mode(CognitiveMode.TOOL),
            _frame(governance_sensitive=False, ambiguity_score=0.1),
        )
        assert result.action.action == ActionType.DEFER
        assert result.fallback_reason == "defer_fallback"

    def test_step_4_no_op_failclosed(self):
        """NO_OP terminus when nothing else is legal.

        FAST has {ANSWER, NO_OP}. USE_TOOL is illegal. No DEFER,
        no ASK_CLARIFICATION, no GOVERNANCE_REVIEW legal. Terminus.
        """
        result = apply_legality(
            _action(ActionType.USE_TOOL),
            _mode(CognitiveMode.FAST),
            _frame(),
        )
        assert result.action.action == ActionType.NO_OP
        assert result.fallback_reason == "no_op_failclosed"
        assert (
            result.action.payload.get("reason_code") == "no_legal_fallback"
        )


# ---------------------------------------------------------------------------
# Fallback never widens — cross-cutting invariant check
# ---------------------------------------------------------------------------


class TestFallbackNeverWidens:
    """Whatever the fallback produces, it must be legal for the mode."""

    @pytest.mark.parametrize("mode", list(CognitiveMode))
    @pytest.mark.parametrize(
        "original_action",
        [
            ActionType.ANSWER,
            ActionType.USE_TOOL,
            ActionType.GOVERNANCE_REVIEW,
            ActionType.DEFER,
            ActionType.ASK_CLARIFICATION,
        ],
    )
    @pytest.mark.parametrize(
        "governance,ambiguity",
        [
            (False, 0.0),
            (True, 0.0),
            (False, 0.8),
            (True, 0.8),
        ],
    )
    def test_fallback_output_is_always_legal(
        self, mode, original_action, governance, ambiguity
    ):
        """Under every (mode, action, governance, ambiguity) combo,
        apply_legality's output must be legal for the mode."""
        result = apply_legality(
            _action(original_action),
            _mode(mode),
            _frame(governance_sensitive=governance, ambiguity_score=ambiguity),
        )
        assert is_legal(mode, result.action.action), (
            f"apply_legality produced {result.action.action.value!r} in "
            f"mode {mode.value!r}. Not in legal set "
            f"{[a.value for a in MODE_LEGAL_INTENTS[mode]]}. "
            f"Invariant 9 violation: fallback widened legality."
        )


# ---------------------------------------------------------------------------
# Observability: original_action_type + fallback_reason set on fallback
# ---------------------------------------------------------------------------


class TestObservability:
    """Fallback decisions expose what was downgraded and why."""

    def test_downgrade_records_original_action(self):
        result = apply_legality(
            _action(ActionType.USE_TOOL),
            _mode(CognitiveMode.FAST),
            _frame(),
        )
        assert result.original_action_type == ActionType.USE_TOOL

    def test_downgrade_records_fallback_reason(self):
        result = apply_legality(
            _action(ActionType.USE_TOOL),
            _mode(CognitiveMode.FAST),
            _frame(),
        )
        assert result.fallback_reason is not None

    def test_payload_includes_original_action(self):
        """The downgraded ActionDecision's payload names the original
        action so downstream observability can show 'X was downgraded
        to Y because Z'."""
        result = apply_legality(
            _action(ActionType.USE_TOOL),
            _mode(CognitiveMode.FAST),
            _frame(),
        )
        assert result.action.payload.get("original_action") == ActionType.USE_TOOL.value
