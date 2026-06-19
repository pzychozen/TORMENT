import pytest

from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ActionType, CognitiveMode


def test_governed_mode_has_priority_over_identity_and_tool():
    ctl = ThinkingController()
    result = ctl.think(
        "default",
        "ryuki",
        "Can you delete this protected identity memory and inspect governance state?",
    )
    assert result.mode_decision.chosen_mode == CognitiveMode.GOVERNED
    assert result.action_decision.action == ActionType.GOVERNANCE_REVIEW


def test_identity_sensitive_mode_beats_tool_and_retrieval():
    ctl = ThinkingController()
    result = ctl.think(
        "default",
        "ryuki",
        "I want to understand my identity drift and character seed history.",
    )
    assert result.mode_decision.chosen_mode == CognitiveMode.IDENTITY_SENSITIVE
    assert result.memory_plan.retrieve_character_state is True
    assert "identity_must_outrank_archive" in result.memory_plan.safety_constraints


def test_tool_mode_selected_for_execution_request():
    # v0.1.0d: tool-intent tuning relocated "inspect"/"debug" to
    # ANALYTICAL_DEPTH_HINT_WORDS (they push REFLECTIVE, not TOOL).
    # Use an explicit execution verb so the test still exercises
    # TOOL routing.
    ctl = ThinkingController()
    result = ctl.think(
        "default",
        "ryuki",
        "Please calculate and compute the sum of the first 100 primes using code.",
    )
    assert result.mode_decision.chosen_mode == CognitiveMode.TOOL
    assert result.action_decision.action == ActionType.USE_TOOL


def test_retrieval_mode_selected_for_archive_document_question():
    ctl = ThinkingController()
    # Avoid "transcript" — it's in both ARCHIVE and LIVE_SOCIAL hint words,
    # and live_social wins in mode priority. Use archive-only keywords.
    result = ctl.think(
        "default",
        "ryuki",
        "Can you look through the archive document notes and remember what was said before?",
    )
    assert result.mode_decision.chosen_mode == CognitiveMode.RETRIEVAL
    assert result.memory_plan.retrieve_archive is True
    assert result.memory_plan.retrieve_relational is True


def test_reflective_mode_selected_for_ambiguous_high_confidence_need_input():
    ctl = ThinkingController()
    # Need ambiguity >= 0.50 or confidence_need >= 0.60.
    # "maybe" (+0.20) + "something" (+0.20) + short text < 4 words (+0.35) = 0.75
    # Short input with vague words triggers reflective.
    result = ctl.think(
        "default",
        "ryuki",
        "maybe something off",
    )
    assert result.mode_decision.chosen_mode == CognitiveMode.REFLECTIVE
    assert result.mode_decision.requires_self_review is True


def test_fast_mode_is_default_fallback():
    ctl = ThinkingController()
    result = ctl.think(
        "default",
        "ryuki",
        "Hello there",
    )
    assert result.mode_decision.chosen_mode == CognitiveMode.FAST
    assert result.action_decision.action == ActionType.ANSWER


def test_high_ambiguity_without_question_triggers_clarification():
    ctl = ThinkingController()
    # Need ambiguity > 0.72 AND no "?" in text.
    # Short (<4 words, +0.35) + "maybe" (+0.20) + "something" (+0.20) = 0.75 > 0.72
    result = ctl.think(
        "default",
        "ryuki",
        "maybe something",
    )
    assert result.action_decision.action == ActionType.ASK_CLARIFICATION


def test_primary_does_not_clarify_below_0_72_intentional_divergence():
    # Provenance lock (NOT drift): the primary choose_action bar is 0.72,
    # deliberately HIGHER than the action-policy fallback bar (0.60). The
    # reachable non-"?" buckets of _estimate_ambiguity jump 0.55 -> 0.75, and
    # 0.72 sits in that gap. "maybe wrong" = short(<4, +0.35) + "maybe"(+0.20)
    # = 0.55 (< 0.72), no "?". Primary must NOT ask clarification here.
    # (The 0.60 bucket is only reachable with "??", which choose_action's
    # separate '?' guard excludes from clarification regardless.)
    ctl = ThinkingController()
    result = ctl.think("default", "ryuki", "maybe wrong")
    assert result.action_decision.action != ActionType.ASK_CLARIFICATION
    assert result.action_decision.action == ActionType.ANSWER


def test_live_social_short_turn_becomes_no_op():
    ctl = ThinkingController()
    ctl.think(
        "default",
        "ryuki",
        "yo",
        source_type="live_transcript",
        metadata={"live_social": True},
    )
    # phrase includes too little signal; heuristic may still fast-path unless social words present
    # so explicitly exercise frame_task path through live-social wording
    result2 = ctl.think(
        "default",
        "ryuki",
        "live audio yo",
        source_type="live_transcript",
    )
    assert result2.mode_decision.chosen_mode == CognitiveMode.LIVE_SOCIAL
    assert result2.action_decision.action in {ActionType.NO_OP, ActionType.ANSWER}


def test_memory_plan_collective_is_non_dominant_when_collective_governance_input():
    ctl = ThinkingController()
    result = ctl.think(
        "default",
        "ryuki",
        "Should we approve collective reingest for this protected memory?",
    )
    assert result.mode_decision.chosen_mode == CognitiveMode.GOVERNED
    assert "governance_review_before_execution" in result.memory_plan.safety_constraints


def test_transcript_defaults_to_archive_retrieval_not_live_social():
    ctl = ThinkingController()
    # "transcript" should route to archive/retrieval, not live-social.
    # Avoid tool-hint words like "search" since tool beats retrieval in priority.
    result = ctl.think(
        "default",
        "ryuki",
        "Look through the archive transcript for what was said before.",
    )
    assert result.mode_decision.chosen_mode == CognitiveMode.RETRIEVAL
    assert result.memory_plan.retrieve_archive is True
    assert "archive" in result.task_frame.context_tags
    assert "live_social" not in result.task_frame.context_tags


def test_to_dict_is_serializable_shape():
    ctl = ThinkingController()
    result = ctl.think("default", "ryuki", "Can you inspect the archive notes?")
    payload = result.to_dict()
    assert "task_frame" in payload
    assert "mode_decision" in payload
    assert "memory_plan" in payload
    assert "action_decision" in payload
    assert "review_result" in payload


# ---------------------------------------------------------------------------
# Tuned-scoring provenance lock (current-behavior characterization).
#
# These tests pin the CURRENT scoring behavior of _estimate_ambiguity and
# _estimate_urgency through the public frame_task seam. They are the
# calibration basis underneath the already-locked ambiguity-clarify thresholds
# (primary 0.72 / fallback 0.60) and the drift-veto urgency override (> 0.7).
# This is a provenance / drift lock — NOT a claim that these tuned values are
# permanently correct. Do not change any scoring value without provenance
# archaeology (source / tests / docs / history / operator context).
#
# Reachable public buckets (current implementation; neither reaches 1.0):
#   ambiguity: {0.0, 0.20, 0.35, 0.40, 0.55, 0.60, 0.75, 0.95}
#   urgency:   {0.0, 0.1, 0.2, 0.3, 0.6, 0.7, 0.8, 0.9}
# ---------------------------------------------------------------------------


def _amb(text: str) -> float:
    return ThinkingController().frame_task("ws", "agent", text).ambiguity_score


def _urg(text: str) -> float:
    return ThinkingController().frame_task("ws", "agent", text).urgency


def test_ambiguity_signal_contributions_provenance_lock():
    # Each ambiguity signal contributes its documented points, isolated (>= 4
    # words so the short bonus is excluded except where it is the signal under
    # test). Inputs avoid urgency words so urgency stays 0.0.
    assert _amb("the report here") == pytest.approx(0.35)              # short (<4 words)
    assert _amb("maybe the report is fine") == pytest.approx(0.20)     # "maybe"
    assert _amb("is the report fine??") == pytest.approx(0.20)         # count("?") > 1
    assert _amb("the report has stuff inside") == pytest.approx(0.20)  # "stuff" (something-family)


def test_ambiguity_reachable_buckets_provenance_lock():
    # One representative input per reachable public bucket. Max is 0.95;
    # 1.0 is NOT reachable through current public text signals.
    assert _amb("the report covers data") == pytest.approx(0.0)
    assert _amb("maybe the report is fine") == pytest.approx(0.20)
    assert _amb("the report here") == pytest.approx(0.35)
    assert _amb("maybe the report has stuff inside") == pytest.approx(0.40)  # maybe + stuff
    assert _amb("maybe here ok") == pytest.approx(0.55)                      # short + maybe
    assert _amb("maybe the stuff here?? really") == pytest.approx(0.60)      # maybe + stuff + ?? (no short)
    assert _amb("maybe something") == pytest.approx(0.75)                    # short + maybe + something
    assert _amb("maybe stuff??") == pytest.approx(0.95)                      # short + maybe + stuff + ??


def test_high_ambiguity_via_double_question_is_guarded_from_primary_clarify():
    # Provenance distinction: a reachable high-ambiguity bucket is NOT the same
    # as a primary-clarify-triggering case. "maybe stuff??" scores 0.95
    # (> 0.72) but contains "?", so choose_action's separate `"?" not in lower`
    # guard blocks primary clarification. (Contrast: the no-"?" 0.75 case DOES
    # clarify — see test_high_ambiguity_without_question_triggers_clarification.)
    ctl = ThinkingController()
    assert ctl.frame_task("ws", "agent", "maybe stuff??").ambiguity_score == pytest.approx(0.95)
    result = ctl.think("default", "ryuki", "maybe stuff??")
    assert result.action_decision.action != ActionType.ASK_CLARIFICATION


def test_urgency_signal_contributions_provenance_lock():
    # Each urgency signal contributes its documented points, isolated.
    assert _urg("please handle this urgent matter") == pytest.approx(0.6)  # "urgent"
    assert _urg("please respond right now") == pytest.approx(0.2)          # "now"
    assert _urg("please respond very quickly") == pytest.approx(0.2)       # "quickly"
    assert _urg("please handle this matter!") == pytest.approx(0.1)        # "!"


def test_urgency_reachable_buckets_provenance_lock():
    # One representative input per reachable public bucket. Max is 0.9;
    # 1.0 is NOT reachable through current public text signals.
    assert _urg("the report covers data") == pytest.approx(0.0)
    assert _urg("please handle this matter!") == pytest.approx(0.1)
    assert _urg("please respond right now") == pytest.approx(0.2)
    assert _urg("please respond right now!") == pytest.approx(0.3)              # now + !
    assert _urg("please handle this urgent matter") == pytest.approx(0.6)       # urgent
    assert _urg("please handle this urgent matter!") == pytest.approx(0.7)      # urgent + !
    assert _urg("please handle this urgent matter now") == pytest.approx(0.8)   # urgent + now
    assert _urg("please handle this urgent matter now!") == pytest.approx(0.9)  # urgent + now + !


def test_urgency_override_boundary_provenance_lock():
    # Locks the current scoring relative to the drift-veto governance override
    # (action_policy bypasses the veto when governance_sensitive AND
    # urgency > 0.7; see tests/test_drift_veto.py for the override at 0.7).
    # "urgent" alone = 0.6 (below the bar); "urgent now" = 0.8 and
    # "urgent now!" = 0.9 (above). "urgent!" = 0.7 sits exactly at the bar.
    assert _urg("please handle this urgent matter") == pytest.approx(0.6)
    assert _urg("please handle this urgent matter") < 0.7                        # urgent alone does not cross
    assert _urg("please handle this urgent matter!") == pytest.approx(0.7)       # boundary == 0.7
    assert _urg("please handle this urgent matter now") == pytest.approx(0.8)
    assert _urg("please handle this urgent matter now") > 0.7                    # urgent + now crosses
    assert _urg("please handle this urgent matter now!") == pytest.approx(0.9)
    assert _urg("please handle this urgent matter now!") > 0.7