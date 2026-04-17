"""
Invariant 4 test (first landing of the slice): assimilation outcomes
are not model-chosen intents.

`PROPOSE_SHARE` and `CREATE_ARCHIVE_NOTE` must not be emitted by
`choose_action` based on text hints in user input. They are
assimilation outcomes, reserved for Phase 7 controller/kernel
dispatch.

This test is the acceptance gate for M1. It must hold before M2,
S1, or any later slice component lands.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 3 (primary intents vs
      assimilation outcomes)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md M1 migration
"""
import pytest

from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ActionType


tc = ThinkingController()


def _choose(query: str):
    """Run the inner deliberation bundle (Phase 2-4 without review)
    and return the ActionDecision."""
    frame = tc.frame_task("ws_test", "agent_test", query)
    mode = tc.choose_mode(frame)
    plan = tc.build_memory_plan(frame, mode)
    return tc.choose_action(frame, mode, plan)


ASSIMILATION_OUTCOMES = {
    ActionType.WRITE_MEMORY,
    ActionType.PROPOSE_SHARE,
    ActionType.CREATE_ARCHIVE_NOTE,
}

PRIMARY_INTENTS = {
    ActionType.ANSWER,
    ActionType.ASK_CLARIFICATION,
    ActionType.DEFER,
    ActionType.USE_TOOL,
    ActionType.NO_OP,
    ActionType.GOVERNANCE_REVIEW,
}


class TestProposeShareNotDeliberative:
    """PROPOSE_SHARE must not be emitted from Phase 4 based on text hints."""

    def test_share_keyword_alone(self):
        d = _choose("Can we share the draft?")
        assert d.action != ActionType.PROPOSE_SHARE

    def test_proposal_keyword_alone(self):
        d = _choose("I have a proposal for the team")
        assert d.action != ActionType.PROPOSE_SHARE

    def test_share_proposal_together(self):
        d = _choose("Please share this proposal with the group")
        assert d.action != ActionType.PROPOSE_SHARE


class TestCreateArchiveNoteNotDeliberative:
    """CREATE_ARCHIVE_NOTE must not be emitted from Phase 4 based on text hints."""

    def test_note_keyword_alone(self):
        d = _choose("Make a note of this")
        assert d.action != ActionType.CREATE_ARCHIVE_NOTE

    def test_archive_keyword_alone(self):
        d = _choose("Check the archive for that document")
        assert d.action != ActionType.CREATE_ARCHIVE_NOTE

    def test_archive_note_together(self):
        d = _choose("Create an archive note for this decision")
        assert d.action != ActionType.CREATE_ARCHIVE_NOTE


class TestChooseActionOutputSet:
    """`choose_action` only emits primary runtime intents after M1."""

    @pytest.mark.parametrize("query", [
        "What's the time?",
        "Tell me about that",
        "Who is Ryuki?",
        "That's fine",
        "I have a proposal for the team",
        "Make a note of this please",
        "Share this with everyone",
        "Archive this section",
        "Write a note about the latest archived doc",
    ])
    def test_never_returns_assimilation_outcome(self, query):
        d = _choose(query)
        assert d.action not in ASSIMILATION_OUTCOMES, (
            f"choose_action emitted assimilation outcome {d.action.value!r} for "
            f"input {query!r}. After M1, assimilation outcomes belong at Phase 7, "
            f"not Phase 4."
        )

    @pytest.mark.parametrize("query", [
        "What's the time?",
        "Tell me about that",
        "I have a proposal for the team",
        "Share this with everyone",
        "Make a note of this please",
    ])
    def test_emits_primary_intent_only(self, query):
        d = _choose(query)
        assert d.action in PRIMARY_INTENTS, (
            f"choose_action emitted {d.action.value!r} for input {query!r}. "
            f"Expected a primary runtime intent from "
            f"{{ANSWER, ASK_CLARIFICATION, DEFER, USE_TOOL, NO_OP, GOVERNANCE_REVIEW}}."
        )


class TestPhase7ScaffoldStub:
    """Phase 7 assimilation-outcome dispatcher is a v0.1 skeleton."""

    def test_dispatcher_importable(self):
        from torment_service.agent_loop import (
            assimilation_outcomes,
            TurnContext,
        )
        assert callable(assimilation_outcomes)
        assert TurnContext is not None

    def test_dispatcher_returns_empty_list_in_v0_1(self):
        from torment_service.agent_loop import (
            assimilation_outcomes,
            TurnContext,
        )
        ctx = TurnContext(workspace_id="ws_test", agent_id="agent_test")
        result = assimilation_outcomes(ctx)
        assert result == []

    def test_turn_context_accepts_optional_fields(self):
        """TurnContext is incrementally populatable for phases 1-6."""
        from torment_service.agent_loop import TurnContext
        ctx = TurnContext(workspace_id="ws", agent_id="agent")
        assert ctx.task_frame is None
        assert ctx.mode_decision is None
        assert ctx.memory_plan is None
        assert ctx.action_decision is None
        assert ctx.response_text is None
        assert ctx.tool_result is None
        assert ctx.metadata == {}
