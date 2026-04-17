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
        fallback_reason: named reason for the last fallback applied;
            None if the original action passed through unchanged.
        drift_veto_applied: True if the S2 drift-regime veto further
            downgraded the action beyond what mode-legality required.
        tool_family_narrowed: name of the tool family the S3 narrowing
            step attached to the action; None if narrowing was not
            performed (non-USE_TOOL action) or the contract permitted
            no family (which falls through to the fallback chain).
    """
    action: ActionDecision
    original_action_type: Optional[ActionType] = None
    fallback_reason: Optional[str] = None
    drift_veto_applied: bool = False
    tool_family_narrowed: Optional[str] = None


@dataclass
class DriftRegime:
    """Classification of the current drift state against the v0.1
    three-regime structure (doctrine Part 4).

    Sign convention (matches `torment_service.character.measure_drift`
    and doctrine Appendix A as amended 2026-04-17):

        * `score` indicates distance from seed basin along a signed
          axis: positive values mean close/centered, negative values
          indicate distance from seed. Range approximately -1.0 to +1.0.
        * `direction` is a SEPARATE explicit signal — "away_seed",
          "toward_seed", or "stable" — indicating whether the last
          observed motion moved toward or away from the seed.

    The high-regime veto condition requires BOTH: `score <= -high_threshold`
    (drift magnitude past the threshold) AND `direction == "away_seed"`
    (motion is outbound). Sign alone is insufficient; both signals
    combine via `vetoes_outward_action`. This matches `character.py`'s
    `gravity_correction` trigger, which also requires both conditions.

    Only the high regime gates action in v0.1 (S2); moderate-regime
    intent promotion is deferred. Low regime shapes aperture only.
    """
    score: float
    direction: str
    is_high: bool
    is_away_seed: bool

    @property
    def vetoes_outward_action(self) -> bool:
        """True iff drift is high AND away from seed — the S2 veto
        condition per the slice plan."""
        return self.is_high and self.is_away_seed


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


# ---------------------------------------------------------------------------
# S2 — Drift-regime veto
# ---------------------------------------------------------------------------
#
# Doctrine Part 4, three-regime structure. Sign convention per
# character.py: drift_score is a signed distance from seed basin
# (positive = close, negative = far). The high-regime veto also
# requires direction == "away_seed" — score sign alone is not
# sufficient. Thresholds below are POSITIVE magnitudes.
#
#     - Low drift (score > -0.15):            aperture shaping only,
#       no action veto.
#     - Moderate drift (-0.35 < score <= -0.15): intent promotion
#       toward stabilization (deferred to later increment; v0.1/S2
#       does not enforce).
#     - High drift (score <= -0.35) AND direction == "away_seed":
#       Action Policy blocks outward actions. USE_TOOL refused.
#       Primary intent forced to DEFER (or NO_OP if DEFER not legal)
#       unless GOVERNANCE_REVIEW is active.
#
# Override: if frame.governance_sensitive AND frame.urgency > 0.7, the
# veto is bypassed; governance review takes precedence over drift. This
# is the explicit doctrinal escape hatch (slice plan S2 / invariant 6).

# Threshold mirrors doctrine Appendix A / TORMENT_CHARACTER_CORRECTION_THRESHOLD.
_DEFAULT_HIGH_DRIFT_THRESHOLD = 0.35
_OVERRIDE_URGENCY_THRESHOLD = 0.7


def classify_drift(
    drift_info: Optional[Dict[str, Any]],
    high_threshold: float = _DEFAULT_HIGH_DRIFT_THRESHOLD,
) -> DriftRegime:
    """Extract a DriftRegime from raw drift state.

    Sign convention (matches `torment_service.character.measure_drift`):
    `drift_score` is a signed distance from the seed basin (positive =
    close/centered, negative = far). The high-regime veto combines this
    with an explicit `drift_direction == "away_seed"` signal; the score
    sign alone is not sufficient. `high_threshold` is a positive
    magnitude; `is_high = score <= -high_threshold`.

    Accepts None or a dict from `character.measure_drift` / fabric.
    None or missing keys degrade gracefully to a low-regime classification.
    """
    if drift_info is None:
        return DriftRegime(
            score=0.0,
            direction="unknown",
            is_high=False,
            is_away_seed=False,
        )
    score = float(drift_info.get("drift_score", 0.0))
    direction = str(drift_info.get("drift_direction", ""))
    return DriftRegime(
        score=score,
        direction=direction,
        # character.py convention: score <= -threshold means "drift
        # has crossed the correction threshold in the away-from-seed
        # direction." Combined with direction=="away_seed" this is
        # the high-regime veto condition per doctrine Part 4.
        is_high=score <= -high_threshold,
        is_away_seed=direction == "away_seed",
    )


def apply_drift_veto(
    policy_decision: ActionPolicyDecision,
    mode_decision: CognitiveModeDecision,
    drift_regime: DriftRegime,
    frame: TaskFrame,
) -> ActionPolicyDecision:
    """Apply Phase 5 drift-regime veto after apply_legality.

    Runs AFTER `apply_legality`. Takes its output, the current mode
    decision (for legality re-check after any veto downgrade), the
    classified drift regime, and the frame (for the governance-urgency
    override check).

    Returns:
        ActionPolicyDecision — the input passed through unchanged when
        the veto is not applicable, or a further-downgraded decision
        when the high regime vetoes outward action.

    Veto conditions (all must hold):
        1. `drift_regime.vetoes_outward_action` — high regime + away_seed.
        2. Current action is NOT already GOVERNANCE_REVIEW (preserved).
        3. NOT overridden by governance_sensitive + urgency > 0.7.

    When the veto fires, the new action is:
        - DEFER if DEFER is legal for the current mode, else
        - NO_OP as the fail-closed terminus (invariant 9).

    Preserves invariants:
        - Invariant 3: high-regime drift vetoes outward action.
        - Invariant 6: governance override narrows (bypass → keep
          current GOVERNANCE_REVIEW or legality-derived action); never
          widens.
        - Invariant 9: veto output is always legal for the mode.
    """
    # Early exits — veto not applicable.
    if not drift_regime.vetoes_outward_action:
        # Low or moderate regime, or high-but-toward-seed — no action veto.
        return policy_decision

    current_action = policy_decision.action.action

    # GOVERNANCE_REVIEW always preserved: governance is narrowing, not widening.
    if current_action == ActionType.GOVERNANCE_REVIEW:
        return policy_decision

    # Override: governance_sensitive + urgency → bypass veto so governance
    # path takes precedence. apply_legality already routed to governance
    # where possible; drift does not second-guess that.
    if (
        frame.governance_sensitive
        and frame.urgency > _OVERRIDE_URGENCY_THRESHOLD
    ):
        return policy_decision

    # Apply veto: downgrade to DEFER if legal, else NO_OP.
    mode = mode_decision.chosen_mode
    legal_set = MODE_LEGAL_INTENTS.get(mode, set())
    pre_veto_action_type = (
        policy_decision.original_action_type
        if policy_decision.original_action_type is not None
        else current_action
    )

    if ActionType.DEFER in legal_set:
        return ActionPolicyDecision(
            action=ActionDecision(
                action=ActionType.DEFER,
                reason=(
                    f"Drift-veto fallback: drift_score={drift_regime.score:.2f} "
                    f"crossed high-drift threshold (score <= -{_DEFAULT_HIGH_DRIFT_THRESHOLD:.2f}) "
                    f"with direction=away_seed; {current_action.value!r} "
                    f"downgraded to DEFER for stabilization."
                ),
                requires_execution=False,
                payload={
                    "original_action": pre_veto_action_type.value,
                    "pre_drift_action": current_action.value,
                    "drift_score": drift_regime.score,
                    "drift_direction": drift_regime.direction,
                    "fallback_reason": "drift_high_regime_veto",
                },
            ),
            original_action_type=pre_veto_action_type,
            fallback_reason="drift_high_regime_veto",
            drift_veto_applied=True,
        )

    # DEFER not legal for this mode — NO_OP terminus (fail-closed).
    return ActionPolicyDecision(
        action=ActionDecision(
            action=ActionType.NO_OP,
            reason=(
                f"Drift-veto fallback: drift high (score={drift_regime.score:.2f}, "
                f"direction=away_seed); {current_action.value!r} not stabilizable "
                f"via DEFER in mode {mode.value!r}; no-op terminus."
            ),
            requires_execution=False,
            payload={
                "original_action": pre_veto_action_type.value,
                "pre_drift_action": current_action.value,
                "drift_score": drift_regime.score,
                "drift_direction": drift_regime.direction,
                "fallback_reason": "drift_high_regime_veto_no_defer_legal",
                "reason_code": "drift_veto_no_stabilization_path",
            },
        ),
        original_action_type=pre_veto_action_type,
        fallback_reason="drift_high_regime_veto_no_defer_legal",
        drift_veto_applied=True,
    )


# ---------------------------------------------------------------------------
# S3 — Tool-family narrowing
# ---------------------------------------------------------------------------
#
# Doctrine Part 9 invariant 2: the model never receives an open
# tool-choice menu. When the inner deliberation proposes USE_TOOL,
# Phase 5 must narrow it to exactly one approved tool family before
# the LLM ever sees a signature. If the active behavior pack's action
# contract permits no family, USE_TOOL is refused and falls through
# to the legality fallback chain (DEFER or NO_OP).
#
# This layer runs AFTER apply_legality (which admits USE_TOOL as
# legal in TOOL mode) and AFTER apply_drift_veto (which may downgrade
# USE_TOOL to DEFER in the high drift regime). When it runs, the
# input action is guaranteed to be USE_TOOL that both the legality
# table and the drift regime have permitted.

from .tool_registry import (
    ActionContract,
    ToolSignature,
    get_tool_signature,
)


def apply_tool_narrowing(
    policy_decision: ActionPolicyDecision,
    mode_decision: CognitiveModeDecision,
    action_contract: ActionContract,
) -> ActionPolicyDecision:
    """Apply Phase 5 tool-family narrowing.

    Runs AFTER `apply_legality` and `apply_drift_veto`. Only applies
    when the current action is USE_TOOL. Contract:
        - Exactly one permitted family → attach the tool signature
          to the action's payload; ActionPolicyDecision records the
          narrowed family name. The LLM will see this single signature
          at Phase 6 — no menu, no alternatives (invariant 2).
        - Zero permitted families → USE_TOOL is refused; fall through
          to DEFER (if legal for the mode) or NO_OP terminus
          (invariant 9).
        - More than one permitted family → in v0.1, this is treated
          as a narrowing failure and falls through to the same
          zero-family path. Behavior packs are expected to declare
          a single family per active contract (S4); this branch is
          defensive against misconfiguration.

    Invariants preserved:
        - Invariant 1: no open-ended memory search tool is ever
          attachable because TOOL_REGISTRY declares none.
        - Invariant 2: exactly one signature is attached (or none,
          and the action is downgraded).
        - Invariant 9: failure-to-narrow falls through closed to
          DEFER or NO_OP, never widens.
    """
    current_action = policy_decision.action.action

    # Only USE_TOOL is narrowed. Everything else passes through.
    if current_action != ActionType.USE_TOOL:
        return policy_decision

    allowed = action_contract.allowed_tool_families
    mode = mode_decision.chosen_mode
    legal_set = MODE_LEGAL_INTENTS.get(mode, set())
    pre_narrow_action_type = (
        policy_decision.original_action_type
        if policy_decision.original_action_type is not None
        else current_action
    )

    # Zero or more-than-one permitted families → refuse USE_TOOL.
    if len(allowed) != 1:
        fallback_reason = (
            "tool_narrowing_no_permitted_family"
            if len(allowed) == 0
            else "tool_narrowing_ambiguous_contract"
        )
        if ActionType.DEFER in legal_set:
            return ActionPolicyDecision(
                action=ActionDecision(
                    action=ActionType.DEFER,
                    reason=(
                        f"Tool-narrowing fallback: "
                        f"contract permits {len(allowed)} families "
                        f"(need exactly 1); deferring."
                    ),
                    requires_execution=False,
                    payload={
                        "original_action": pre_narrow_action_type.value,
                        "pre_narrow_action": current_action.value,
                        "fallback_reason": fallback_reason,
                    },
                ),
                original_action_type=pre_narrow_action_type,
                fallback_reason=fallback_reason,
                drift_veto_applied=policy_decision.drift_veto_applied,
                tool_family_narrowed=None,
            )
        # DEFER not legal → NO_OP terminus.
        return ActionPolicyDecision(
            action=ActionDecision(
                action=ActionType.NO_OP,
                reason=(
                    f"Tool-narrowing fallback: contract permits "
                    f"{len(allowed)} families in mode {mode.value!r}; "
                    f"DEFER not legal, no-op terminus."
                ),
                requires_execution=False,
                payload={
                    "original_action": pre_narrow_action_type.value,
                    "pre_narrow_action": current_action.value,
                    "fallback_reason": f"{fallback_reason}_no_defer_legal",
                    "reason_code": "tool_narrowing_no_stabilization_path",
                },
            ),
            original_action_type=pre_narrow_action_type,
            fallback_reason=f"{fallback_reason}_no_defer_legal",
            drift_veto_applied=policy_decision.drift_veto_applied,
            tool_family_narrowed=None,
        )

    # Exactly one permitted family — attach its signature.
    family_name = next(iter(allowed))
    signature: Optional[ToolSignature] = get_tool_signature(family_name)

    if signature is None:
        # Contract names a family that is not declared in the
        # registry. Defensive: treat as ambiguous and fall through.
        fallback_reason = "tool_narrowing_unknown_family"
        if ActionType.DEFER in legal_set:
            return ActionPolicyDecision(
                action=ActionDecision(
                    action=ActionType.DEFER,
                    reason=(
                        f"Tool-narrowing fallback: contract permits "
                        f"{family_name!r} which is not in the tool "
                        f"registry; deferring."
                    ),
                    requires_execution=False,
                    payload={
                        "original_action": pre_narrow_action_type.value,
                        "unknown_family": family_name,
                        "fallback_reason": fallback_reason,
                    },
                ),
                original_action_type=pre_narrow_action_type,
                fallback_reason=fallback_reason,
                drift_veto_applied=policy_decision.drift_veto_applied,
                tool_family_narrowed=None,
            )
        return ActionPolicyDecision(
            action=ActionDecision(
                action=ActionType.NO_OP,
                reason=(
                    f"Tool-narrowing fallback: unknown family "
                    f"{family_name!r}; no-op terminus."
                ),
                requires_execution=False,
                payload={
                    "original_action": pre_narrow_action_type.value,
                    "unknown_family": family_name,
                    "fallback_reason": f"{fallback_reason}_no_defer_legal",
                },
            ),
            original_action_type=pre_narrow_action_type,
            fallback_reason=f"{fallback_reason}_no_defer_legal",
            drift_veto_applied=policy_decision.drift_veto_applied,
            tool_family_narrowed=None,
        )

    # Narrowing succeeded: attach the single signature.
    new_payload = dict(policy_decision.action.payload)
    new_payload["tool_family"] = signature.name
    new_payload["tool_signature"] = signature.as_llm_tool_spec()
    new_payload["tool_defaults"] = dict(signature.defaults)

    return ActionPolicyDecision(
        action=ActionDecision(
            action=ActionType.USE_TOOL,
            reason=policy_decision.action.reason,
            requires_execution=True,
            payload=new_payload,
        ),
        original_action_type=policy_decision.original_action_type,
        fallback_reason=policy_decision.fallback_reason,
        drift_veto_applied=policy_decision.drift_veto_applied,
        tool_family_narrowed=signature.name,
    )
