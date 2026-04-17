# torment_service/action_policy.py
"""
TORMENT agent Phase 5 action policy.

Enforces the Mode→legal-intents table from the ratified doctrine,
and applies the Part 2.5 fallback chain when the inner deliberation
proposes an action that is not legal for the current cognitive mode.

The policy layer is a pure function of (ActionDecision, mode, frame).
It does not mutate inputs and does not call out to the kernel or the
LLM. It is intended to be invoked by the outer-loop runner between
Phase 4 (Intent) and Phase 6 (Execute), per doctrine Part 2 R6 and
the slice plan's M2 scope.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 3 (Mode→legal-intents)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 2.5 (fallback chain)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 invariants 6, 7, 9
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md M2 migration

v0.1 incremental scope:
    M1:               Phase 7 assimilation-outcome scaffold (landed).
    M2 (this commit): Mode-legality table + fallback chain (this file).
    S1:               Outer-loop runner — will call apply_legality
                      between Phase 4 and Phase 5.
    S2:               Drift-regime veto layered on top of this module.
    S3:               Tool-family narrowing layered on top of this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Set

from .thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveMode,
    CognitiveModeDecision,
    TaskFrame,
)


# ---------------------------------------------------------------------------
# Mode → legal-intents table (doctrine Part 3, pre-execution legality)
# ---------------------------------------------------------------------------
#
# ⚠ cells in the doctrine table are represented as LEGAL here because
# "⚠" means "legal subject to additional policy gates" (e.g. USE_TOOL
# is legal in TOOL mode but must be family-narrowed by S3). The
# stricter-gate handling is layered on top, not baked into the
# legality set.
#
# ✗ cells in the doctrine table are what this module enforces as
# illegal for mode-legality purposes.
#
# Assimilation outcomes (WRITE_MEMORY, PROPOSE_SHARE, CREATE_ARCHIVE_NOTE)
# never appear in any legal set — doctrine Part 3 classifies them as
# Phase 7 outcomes, not primary runtime intents. Invariant 4 cross-
# check: no assimilation outcome is pre-execution-legal in any mode.

MODE_LEGAL_INTENTS: Dict[CognitiveMode, Set[ActionType]] = {
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
        ActionType.USE_TOOL,      # ⚠ - S3 narrowing still required
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
        ActionType.GOVERNANCE_REVIEW,  # ⚠ - co-signal requirement
    },
    CognitiveMode.LIVE_SOCIAL: {
        ActionType.ANSWER,
        ActionType.ASK_CLARIFICATION,
        ActionType.NO_OP,
    },
}


# Ambiguity threshold at which the fallback chain prefers
# ASK_CLARIFICATION over DEFER. Tuned to match the existing
# thinking_controller.choose_action ambiguity threshold (0.72)
# so fallbacks and primary deliberation agree on when ambiguity
# is high enough to warrant a scoped question back to the user.
_AMBIGUITY_CLARIFY_THRESHOLD = 0.60


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass
class ActionPolicyDecision:
    """Result of applying Phase 5 policy to a deliberation-side action.

    Fields:
        action: the (possibly downgraded) ActionDecision that Phase 6
            will execute.
        original_action_type: if a fallback fired, the Phase-4 action
            type that was downgraded; None otherwise.
        fallback_reason: named reason for the fallback; None if the
            original action passed through unchanged.
    """
    action: ActionDecision
    original_action_type: Optional[ActionType] = None
    fallback_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def is_legal(mode: CognitiveMode, action_type: ActionType) -> bool:
    """Return True if `action_type` is pre-execution-legal in `mode`."""
    return action_type in MODE_LEGAL_INTENTS.get(mode, set())


def apply_legality(
    action: ActionDecision,
    mode_decision: CognitiveModeDecision,
    frame: TaskFrame,
) -> ActionPolicyDecision:
    """Apply Phase 5 mode-legality enforcement and the Part 2.5 fallback chain.

    Contract:
        If `action` is legal for `mode_decision.chosen_mode`, returns
        it unchanged (original_action_type=None, fallback_reason=None).

        Otherwise, applies the Part 2.5 fallback chain:
            1. If frame.governance_sensitive AND GOVERNANCE_REVIEW is
               legal for the mode → route to GOVERNANCE_REVIEW.
            2. Else if ambiguity is high AND ASK_CLARIFICATION is legal
               for the mode → route to ASK_CLARIFICATION.
            3. Else if DEFER is legal for the mode → route to DEFER.
            4. Else → NO_OP with explicit `reason` field (fail-closed
               terminus).

    Invariants enforced:
        - Invariant 6 (governance narrows but never widens): the
          governance branch only selects GOVERNANCE_REVIEW if it is in
          the mode's legal set. Never widens legality.
        - Invariant 7 (mode legality respected): fallback outputs are
          always members of MODE_LEGAL_INTENTS[mode].
        - Invariant 9 (fail-closed): the chain never admits an illegal
          action. NO_OP with reason is the terminus.
    """
    mode = mode_decision.chosen_mode

    # Legal — pass through unchanged.
    if is_legal(mode, action.action):
        return ActionPolicyDecision(action=action)

    original = action.action
    legal_set = MODE_LEGAL_INTENTS.get(mode, set())

    # Step 1: governance-sensitive routes to GOVERNANCE_REVIEW when legal.
    if (
        frame.governance_sensitive
        and ActionType.GOVERNANCE_REVIEW in legal_set
    ):
        return ActionPolicyDecision(
            action=ActionDecision(
                action=ActionType.GOVERNANCE_REVIEW,
                reason=(
                    f"Mode-legality fallback: governance-sensitive input "
                    f"with illegal primary {original.value!r} in mode "
                    f"{mode.value!r}; routing to governance review."
                ),
                requires_execution=True,
                payload={
                    "route": "governed",
                    "original_action": original.value,
                    "fallback_reason": "governance_sensitive_narrowing",
                },
            ),
            original_action_type=original,
            fallback_reason="governance_sensitive_narrowing",
        )

    # Step 2: high ambiguity prefers ASK_CLARIFICATION when legal.
    if (
        frame.ambiguity_score >= _AMBIGUITY_CLARIFY_THRESHOLD
        and ActionType.ASK_CLARIFICATION in legal_set
    ):
        return ActionPolicyDecision(
            action=ActionDecision(
                action=ActionType.ASK_CLARIFICATION,
                reason=(
                    f"Mode-legality fallback: illegal primary "
                    f"{original.value!r} in mode {mode.value!r} with "
                    f"high ambiguity; asking for clarification."
                ),
                requires_execution=False,
                payload={
                    "original_action": original.value,
                    "fallback_reason": "ambiguity_clarification_fallback",
                },
            ),
            original_action_type=original,
            fallback_reason="ambiguity_clarification_fallback",
        )

    # Step 3: DEFER when legal.
    if ActionType.DEFER in legal_set:
        return ActionPolicyDecision(
            action=ActionDecision(
                action=ActionType.DEFER,
                reason=(
                    f"Mode-legality fallback: {original.value!r} not legal "
                    f"in mode {mode.value!r}; deferring."
                ),
                requires_execution=False,
                payload={
                    "original_action": original.value,
                    "fallback_reason": "defer_fallback",
                },
            ),
            original_action_type=original,
            fallback_reason="defer_fallback",
        )

    # Step 4: NO_OP fail-closed terminus.
    # Reached when no narrower-legal option exists. Invariant 9 says
    # the chain must run closed, not open — NO_OP with reason is the
    # correct answer here.
    return ActionPolicyDecision(
        action=ActionDecision(
            action=ActionType.NO_OP,
            reason=(
                f"Mode-legality fallback: no legal fallback for "
                f"{original.value!r} in mode {mode.value!r}; "
                f"no-op with reason."
            ),
            requires_execution=False,
            payload={
                "original_action": original.value,
                "fallback_reason": "no_op_failclosed",
                "reason_code": "no_legal_fallback",
            },
        ),
        original_action_type=original,
        fallback_reason="no_op_failclosed",
    )
