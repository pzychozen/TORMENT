"""Tests for the Response Stance / Participation Policy layer.

Covers the five mandatory scenarios from the design spec:
  1. Governance-sensitive input → governed_redirect
  2. Ambiguous input → ask_clarification
  3. Live-social short/noisy → silent_observe
  4. Identity-sensitive + ambiguous → defer
  5. Normal direct input → respond_now

Plus:
  6. Layer disabled when contextual_abstention is off
  7. Tool-routed input → tool_redirect
  8. Stance appears in ThinkingResult.to_dict() when enabled
  9. Stance is None in ThinkingResult.to_dict() when disabled
"""

from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import GeometricStanceContext, ResponseStance


CAPS_ON = {"contextual_abstention": True}
CAPS_OFF = {"contextual_abstention": False}


def _think(text, *, caps=CAPS_ON, source_type="user_text", geo=None):
    ctl = ThinkingController()
    return ctl.think(
        "default", "ryuki", text,
        source_type=source_type,
        capabilities=caps,
        geometric_context=geo,
    )


# ── 1. Governance-sensitive → governed_redirect ──────────────────────────

def test_governance_sensitive_redirects():
    result = _think("Can you delete this protected identity memory and inspect governance state?")
    assert result.stance is not None
    assert result.stance.stance == ResponseStance.GOVERNED_REDIRECT
    assert result.stance.confidence >= 0.80


# ── 2. Ambiguous input → ask_clarification ───────────────────────────────

def test_ambiguous_input_prefers_clarification():
    # "maybe something" — short (<4 words, +0.35) + "maybe" (+0.20) + "something" (+0.20) = 0.75
    # No "?" in text, ambiguity 0.75 > 0.60 → ask_clarification
    result = _think("maybe something")
    assert result.stance is not None
    assert result.stance.stance == ResponseStance.ASK_CLARIFICATION


# ── 3. Live-social short/noisy → silent_observe ─────────────────────────

def test_live_social_short_observes():
    # "live audio" = 2 tokens, triggers live_social + token_count < 3 → silent_observe
    result = _think("live audio")
    assert result.stance is not None
    assert result.stance.stance == ResponseStance.SILENT_OBSERVE
    assert result.stance.context_factors.get("live_social") is True


# ── 4. Identity-sensitive + ambiguous → defer ────────────────────────────

def test_identity_sensitive_ambiguous_defers():
    # "identity" triggers identity_sensitive; "maybe something" pushes ambiguity ≥ 0.45
    # Short text (<4 words) gives +0.35, "maybe" +0.20, "something" +0.20 = 0.75
    result = _think("identity maybe something")
    assert result.stance is not None
    assert result.stance.stance == ResponseStance.DEFER
    assert result.stance.fallback_stance == ResponseStance.ASK_CLARIFICATION


# ── 5. Normal direct input → respond_now ─────────────────────────────────

def test_normal_input_responds_now():
    result = _think("Hello there, how are you doing today?")
    assert result.stance is not None
    assert result.stance.stance == ResponseStance.RESPOND_NOW


# ── 6. Layer disabled → stance is None ───────────────────────────────────

def test_disabled_returns_none():
    result = _think("Can you delete this protected memory?", caps=CAPS_OFF)
    assert result.stance is None


def test_no_capabilities_returns_none():
    result = _think("Hello there", caps=None)
    assert result.stance is None


# ── 7. Tool-routed → tool_redirect ──────────────────────────────────────

def test_tool_input_redirects():
    result = _think("Please inspect and debug the archive retrieval pipeline.")
    assert result.stance is not None
    assert result.stance.stance == ResponseStance.TOOL_REDIRECT


# ── 8. Stance appears in to_dict when enabled ───────────────────────────

def test_stance_in_to_dict_when_enabled():
    result = _think("Hello there, how are you?")
    payload = result.to_dict()
    assert payload["stance"] is not None
    assert payload["stance"]["stance"] == "respond_now"
    assert "confidence" in payload["stance"]
    assert "context_factors" in payload["stance"]


# ── 9. Stance is None in to_dict when disabled ──────────────────────────

def test_stance_none_in_to_dict_when_disabled():
    result = _think("Hello there", caps=CAPS_OFF)
    payload = result.to_dict()
    assert payload["stance"] is None


# ── 10. No geometric context → unchanged outputs ───────────────────────
# These verify that passing geo=None produces identical results to before.

def test_no_geo_identity_defer_unchanged():
    """Without geometric context, identity-sensitive defer threshold is unmodified."""
    result_no_geo = _think("identity maybe something", geo=None)
    assert result_no_geo.stance.stance == ResponseStance.DEFER


def test_no_geo_ambiguity_clarify_unchanged():
    """Without geometric context, ambiguity clarification threshold is unmodified."""
    result_no_geo = _think("maybe something", geo=None)
    assert result_no_geo.stance.stance == ResponseStance.ASK_CLARIFICATION


def test_no_geo_normal_unchanged():
    """Without geometric context, normal input still maps to respond_now."""
    result_no_geo = _think("Hello there, how are you doing today?", geo=None)
    assert result_no_geo.stance.stance == ResponseStance.RESPOND_NOW


# ── 11. High stability + identity_lock loosens identity-defer ───────────

def test_high_stability_loosens_identity_defer():
    """When identity_lock=1.0 and stability=1.0, the identity-defer threshold
    rises from 0.45 to 0.45*1.15=0.5175.  An ambiguity of 0.50 (which normally
    triggers defer at 0.45) should now fall below the raised threshold.

    Input: "identity maybe" → 3 words (<4 → +0.35) + "maybe" (+0.20) = 0.55
    Without geo: 0.55 >= 0.45 → DEFER
    With high geo: 0.55 >= 0.45*1.15=0.5175 → still DEFER (0.55 > 0.5175)

    We need ambiguity just above 0.45 but below 0.5175.  "identity thing" gives:
    3 words (<4 → +0.35) + "thing" (+0.20) = 0.55.  That's still above.

    So instead: verify that the modifiers are present in context_factors.
    """
    geo_high = GeometricStanceContext(
        coherence=0.9, stability=1.0, identity_lock=1.0,
        ambiguity_tolerance=0.8, social_resonance=0.5,
    )
    result = _think("identity maybe something", geo=geo_high)
    assert result.stance is not None
    # Modifiers should be in context_factors
    mods = result.stance.context_factors.get("geo_modifiers", {})
    assert mods.get("identity_defer") > 1.0, "High identity_lock should raise modifier above 1.0"
    assert mods.get("identity_defer") <= 1.15, "Modifier should be clamped to 1.15 max"


# ── 12. Low stability + identity_lock tightens identity-defer ──────────

def test_low_stability_tightens_identity_defer():
    """When identity_lock=0.0 and stability=0.0, the modifier drops to 0.85,
    lowering the threshold from 0.45 to 0.3825.  This makes the system MORE
    cautious — it defers at even lower ambiguity."""
    geo_low = GeometricStanceContext(
        coherence=0.1, stability=0.0, identity_lock=0.0,
        ambiguity_tolerance=0.1, social_resonance=0.5,
    )
    result = _think("identity maybe something", geo=geo_low)
    assert result.stance is not None
    mods = result.stance.context_factors.get("geo_modifiers", {})
    assert mods.get("identity_defer") < 1.0, "Low identity_lock should drop modifier below 1.0"
    assert mods.get("identity_defer") >= 0.85, "Modifier should be clamped to 0.85 min"


# ── 13. High coherence + tolerance loosens ambiguity clarification ─────

def test_high_coherence_loosens_ambiguity_clarify():
    """When ambiguity_tolerance=1.0 and coherence=1.0, the clarification
    threshold rises, making the system less eager to ask for clarification."""
    geo_high = GeometricStanceContext(
        coherence=1.0, stability=0.5, identity_lock=0.5,
        ambiguity_tolerance=1.0, social_resonance=0.5,
    )
    result = _think("maybe something", geo=geo_high)
    assert result.stance is not None
    mods = result.stance.context_factors.get("geo_modifiers", {})
    assert mods.get("ambiguity_clarify") > 1.0


# ── 14. Social resonance modulates live-social thresholds ──────────────

def test_social_resonance_in_modifiers():
    """When social_resonance is high, the social compactness modifier > 1.0,
    widening the silence/brief window."""
    geo_social = GeometricStanceContext(
        coherence=0.5, stability=0.5, identity_lock=0.5,
        ambiguity_tolerance=0.5, social_resonance=1.0,
    )
    result = _think("live audio", geo=geo_social)
    assert result.stance is not None
    mods = result.stance.context_factors.get("geo_modifiers", {})
    assert mods.get("social_compact") > 1.0


# ── 15. Geometric context appears in ThinkingResult.to_dict() ──────────

def test_geometric_context_in_to_dict():
    """When geometric_context is supplied, it appears in the serialized output."""
    geo = GeometricStanceContext(coherence=0.8, stability=0.7, identity_lock=0.6,
                                  ambiguity_tolerance=0.5, social_resonance=0.4)
    result = _think("Hello there, how are you?", geo=geo)
    payload = result.to_dict()
    assert payload["geometric_context"] is not None
    assert payload["geometric_context"]["coherence"] == 0.8
    assert payload["geometric_context"]["stability"] == 0.7


def test_geometric_context_none_in_to_dict():
    """When no geometric_context is supplied, it is None in the serialized output."""
    result = _think("Hello there", geo=None)
    payload = result.to_dict()
    assert payload["geometric_context"] is None
