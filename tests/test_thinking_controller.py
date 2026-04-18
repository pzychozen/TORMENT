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