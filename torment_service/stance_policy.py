"""Response Stance Policy — optional participation decision layer for TORMENT.

This module determines *whether and how* a character should participate in a
given interaction.  It sits on top of the thinking pipeline (task frame,
cognitive mode, memory plan, action decision, review result) and produces
a :class:`ResponseStanceDecision`.

Design constraints:
  * Heuristic-first, deterministic, no ML calls.
  * Advisory only — never blocks Spine execution.
  * Only active when ``contextual_abstention`` capability is enabled for the
    character.  When disabled, :func:`determine_stance` returns ``None``.
  * No hardcoded response text, no persistent writes, no refusal logic.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveModeDecision,
    GeometricStanceContext,
    MemoryPlan,
    ResponseStance,
    ResponseStanceDecision,
    ReviewResult,
    TaskFrame,
)

# ── Geometric modulation helpers ────────────────────────────────────────
#
# These produce bounded multipliers in [_MOD_LO, _MOD_HI] that nudge
# thresholds without ever flipping a decision on their own.  When no
# geometric context is available every modifier returns 1.0 (no-op).

_MOD_LO = 0.85
_MOD_HI = 1.15


def _clamp_mod(v: float) -> float:
    """Clamp a raw modifier into the safe band."""
    return max(_MOD_LO, min(_MOD_HI, v))


def _identity_defer_modifier(geo: GeometricStanceContext) -> float:
    """Modifier for the identity-sensitive defer threshold (rule 4).

    When identity_lock is high and stability is good, the character is
    firmly anchored — raise the threshold so it defers less readily.
    When identity_lock is low, lower the threshold → defer sooner.
    """
    # identity_lock 0..1, stability 0..1
    # composite: high → loosen (raise threshold), low → tighten (lower threshold)
    composite = 0.6 * geo.identity_lock + 0.4 * geo.stability
    # Map 0..1 composite to modifier range: 0.0 → 0.85, 0.5 → 1.0, 1.0 → 1.15
    return _clamp_mod(0.85 + composite * 0.30)


def _ambiguity_clarify_modifier(geo: GeometricStanceContext) -> float:
    """Modifier for the ambiguity clarification threshold (rule 5).

    High ambiguity_tolerance + high coherence → raise threshold (less
    eager to ask clarification).  Low tolerance → lower it.
    """
    composite = 0.7 * geo.ambiguity_tolerance + 0.3 * geo.coherence
    return _clamp_mod(0.85 + composite * 0.30)


def _social_compactness_modifier(geo: GeometricStanceContext) -> float:
    """Modifier for live-social thresholds (rules 6–7).

    High social_resonance → raise token/urgency thresholds (more willing
    to stay silent or brief).  Low resonance → lower thresholds (more
    willing to speak up).
    """
    return _clamp_mod(0.85 + geo.social_resonance * 0.30)


def determine_stance(
    frame: TaskFrame,
    mode: CognitiveModeDecision,
    memory_plan: MemoryPlan,
    action: ActionDecision,
    review: ReviewResult,
    *,
    capabilities: Optional[Dict[str, bool]] = None,
    geometric_context: Optional[GeometricStanceContext] = None,
) -> Optional[ResponseStanceDecision]:
    """Determine the character's participation stance for this interaction.

    Parameters
    ----------
    frame, mode, memory_plan, action, review
        The full thinking pipeline output up to this point.
    capabilities
        Optional character capability flags (from the creator / runtime config).
        If ``capabilities.get("contextual_abstention")`` is falsy, the function
        returns ``None`` immediately (layer disabled).
    geometric_context
        Optional derived geometric state from the TORMENT kernel.  When
        supplied, bounded multiplicative modifiers (0.85–1.15) are applied
        to key thresholds so the living kernel can gently nudge stance
        decisions.  When ``None``, all modifiers are 1.0 (pure scaffold).

    Returns
    -------
    ResponseStanceDecision or None
        ``None`` means the stance layer is inactive — the system should behave
        as if this layer does not exist.
    """
    caps = capabilities or {}
    if not caps.get("contextual_abstention", False):
        return None

    # ── Collect signals ──────────────────────────────────────────────────

    governed = frame.governance_sensitive
    identity = frame.identity_sensitive
    live_social = frame.live_social
    ambiguity = frame.ambiguity_score
    urgency = frame.urgency
    token_count = frame.tone_hints.get("length_tokens", 0)
    mode_val = mode.chosen_mode
    action_val = action.action
    review_blocked = review.blocked
    review_escalate = review.escalate

    # ── Geometric modulation (bounded multipliers) ────────────────────────

    geo = geometric_context
    id_mod = _identity_defer_modifier(geo) if geo else 1.0
    amb_mod = _ambiguity_clarify_modifier(geo) if geo else 1.0
    soc_mod = _social_compactness_modifier(geo) if geo else 1.0

    factors: Dict[str, Any] = {
        "governed": governed,
        "identity": identity,
        "live_social": live_social,
        "ambiguity": ambiguity,
        "urgency": urgency,
        "token_count": token_count,
        "mode": mode_val.value,
        "action": action_val.value,
        "geo_modifiers": {"identity_defer": id_mod, "ambiguity_clarify": amb_mod, "social_compact": soc_mod},
    }

    # ── Rule cascade (order matters — highest priority first) ────────────

    # 1. Review blocked → governed redirect (something is seriously wrong)
    if review_blocked or review_escalate:
        return ResponseStanceDecision(
            stance=ResponseStance.GOVERNED_REDIRECT,
            reason="Review flagged block or escalation — redirect to governed path.",
            confidence=0.90,
            fallback_stance=ResponseStance.DEFER,
            context_factors=factors,
        )

    # 2. Governance-sensitive → governed redirect
    if governed and action_val == ActionType.GOVERNANCE_REVIEW:
        return ResponseStanceDecision(
            stance=ResponseStance.GOVERNED_REDIRECT,
            reason="Governance-sensitive request should be handled by governed execution, not free response.",
            confidence=0.85,
            fallback_stance=ResponseStance.DEFER,
            context_factors=factors,
        )

    # 3. Tool-routed → tool redirect
    if action_val == ActionType.USE_TOOL:
        return ResponseStanceDecision(
            stance=ResponseStance.TOOL_REDIRECT,
            reason="Action requires tool use — character should redirect rather than guess.",
            confidence=0.80,
            fallback_stance=ResponseStance.RESPOND_BRIEFLY,
            context_factors=factors,
        )

    # 4. Identity-sensitive with high ambiguity → defer rather than overstate
    #    Geometric modulation: high identity_lock + stability raises threshold
    #    (defer less readily when firmly anchored).
    if identity and ambiguity >= 0.45 * id_mod:
        return ResponseStanceDecision(
            stance=ResponseStance.DEFER,
            reason="Identity-sensitive context with significant ambiguity — safer to defer than risk drift.",
            confidence=0.70,
            fallback_stance=ResponseStance.ASK_CLARIFICATION,
            context_factors=factors,
        )

    # 5. High ambiguity, no question mark → ask clarification
    #    Geometric modulation: high ambiguity_tolerance + coherence raises
    #    threshold (less eager to clarify when kernel is coherent).
    if ambiguity > 0.60 * amb_mod and "?" not in frame.normalized_input:
        return ResponseStanceDecision(
            stance=ResponseStance.ASK_CLARIFICATION,
            reason="Ambiguous input without a clear question — clarification is safer than guessing.",
            confidence=0.65,
            fallback_stance=ResponseStance.RESPOND_BRIEFLY,
            context_factors=factors,
        )

    # 6. Live-social very short/noisy → silent observe
    #    Geometric modulation: high social_resonance raises token threshold
    #    (more willing to stay silent even with slightly longer input).
    if live_social and token_count < 3 * soc_mod:
        return ResponseStanceDecision(
            stance=ResponseStance.SILENT_OBSERVE,
            reason="Very short live-social turn — observing rather than interrupting.",
            confidence=0.75,
            fallback_stance=ResponseStance.ABSTAIN,
            context_factors=factors,
        )

    # 7. Live-social with low urgency → respond briefly (don't dominate)
    #    Geometric modulation: high social_resonance raises urgency threshold
    #    (more willing to stay brief when socially engaged).
    if live_social and urgency < 0.3 * soc_mod:
        return ResponseStanceDecision(
            stance=ResponseStance.RESPOND_BRIEFLY,
            reason="Live-social context with low urgency — keep response compact.",
            confidence=0.60,
            fallback_stance=ResponseStance.RESPOND_NOW,
            context_factors=factors,
        )

    # 8. Action is already NO_OP → abstain
    if action_val == ActionType.NO_OP:
        return ResponseStanceDecision(
            stance=ResponseStance.ABSTAIN,
            reason="Thinking pipeline already chose no-op — character should abstain.",
            confidence=0.80,
            fallback_stance=ResponseStance.SILENT_OBSERVE,
            context_factors=factors,
        )

    # 9. Action is clarification → mirror that
    if action_val == ActionType.ASK_CLARIFICATION:
        return ResponseStanceDecision(
            stance=ResponseStance.ASK_CLARIFICATION,
            reason="Thinking pipeline wants clarification — stance agrees.",
            confidence=0.75,
            fallback_stance=ResponseStance.RESPOND_BRIEFLY,
            context_factors=factors,
        )

    # 10. Default: respond now
    return ResponseStanceDecision(
        stance=ResponseStance.RESPOND_NOW,
        reason="No special conditions detected — standard response path.",
        confidence=0.50,
        context_factors=factors,
    )
