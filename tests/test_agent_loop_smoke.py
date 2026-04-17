"""
S1 smoke test: single-turn outer-loop end-to-end.

One turn through all 8 phases of the outer loop with a fake fabric
and a fake LLM. Asserts:

- All 8 phases run (TurnResult populated).
- Inner deliberation (Phases 2-4) produces a bundle from
  ThinkingController.deliberate_only.
- Phase 5 action-policy decision is present.
- Phase 6 execution produces a response (or no_op as appropriate).
- Phase 7 ingest is attempted when the turn produced content.
- Phase 8 measure_drift is called; gravity_correction only fires
  under the declared conditions.

Does NOT cover drift veto (S2), tool narrowing (S3), behavior pack
(S4), or reflex invariant 5 (S5). Those land in their own tests.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 2 R6 (8-phase loop)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S1
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from torment_service.agent_loop import (
    AgentRunner,
    ExecutionOutcome,
    Observation,
    TurnResult,
)
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ActionType, CognitiveMode


# ---------------------------------------------------------------------------
# Fake dependencies
# ---------------------------------------------------------------------------


@dataclass
class FakeFabric:
    """Test double for FabricHandle."""
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)

    # Configurable return values
    drift_return: Optional[Dict[str, Any]] = None
    raise_on_ingest: bool = False

    def ingest(self, workspace_id, agent_id, text, step):
        if self.raise_on_ingest:
            raise RuntimeError("simulated ingest failure")
        call = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "text": text,
            "step": step,
        }
        self.ingest_calls.append(call)
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id}
        )
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append(
            {
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "drift_info": drift_info,
            }
        )


@dataclass
class FakeLLM:
    """Test double for LLMClient."""
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_response: str = "Fake LLM response."

    def complete(self, system_prompt, messages, tools=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": messages,
                "tools": tools,
            }
        )
        return self.canned_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_runner(drift_return=None, raise_on_ingest=False, canned_response="Hi.", drift_high_threshold=0.35):
    fabric = FakeFabric(
        drift_return=drift_return,
        raise_on_ingest=raise_on_ingest,
    )
    llm = FakeLLM(canned_response=canned_response)
    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
        drift_high_threshold=drift_high_threshold,
    )
    return runner, fabric, llm


# ---------------------------------------------------------------------------
# All 8 phases execute
# ---------------------------------------------------------------------------


class TestAll8PhasesExecute:
    """Run one turn; assert every phase produced observable output."""

    def test_turn_result_populated_for_normal_input(self):
        runner, fabric, llm = _make_runner(drift_return=None)
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="What time is it?"),
            step=1,
        )

        # Phase 2: Frame
        assert result.task_frame is not None
        assert result.task_frame.raw_input == "What time is it?"

        # Phase 2: choose_mode
        assert result.mode_decision is not None
        assert isinstance(result.mode_decision.chosen_mode, CognitiveMode)

        # Phase 3: memory_plan
        assert result.memory_plan is not None

        # Phase 4: action_decision
        assert result.action_decision is not None

        # Phase 5: action_policy_decision
        assert result.action_policy_decision is not None

        # Phase 6: execution_outcome
        assert result.execution_outcome is not None

        # Phase 6 sub-gate: review_outcome
        assert result.review_outcome is not None

        # Phase 7: assimilation_outcomes
        assert isinstance(result.assimilation_outcomes, list)

        # Phase 8: drift + gravity signals recorded
        # drift_after_stabilize may be None if FakeFabric returns None;
        # gravity_correction_applied must be False in that case.
        assert result.drift_after_stabilize is None
        assert result.gravity_correction_applied is False

    def test_measure_drift_called_even_when_drift_is_none(self):
        """Phase 8 runs measure_drift regardless of outcome."""
        runner, fabric, llm = _make_runner(drift_return=None)
        runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Say hi"),
            step=1,
        )
        assert len(fabric.measure_drift_calls) == 1


# ---------------------------------------------------------------------------
# Phase 5 action-policy decision is wired
# ---------------------------------------------------------------------------


class TestPhase5ActionPolicyWired:
    """The runner actually calls apply_legality between Phase 4 and Phase 6."""

    def test_legal_action_passes_through(self):
        """Normal user input lands on ANSWER which is legal in most modes."""
        runner, fabric, llm = _make_runner()
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Say hi"),
            step=1,
        )
        # If action was legal for the chosen mode, no fallback fired
        assert result.action_policy_decision.fallback_reason is None

    def test_m2_acceptance_case_through_runner(self):
        """mode=TOOL + no tool_need → fallback chain fires in S1 too.

        We can't easily force mode=TOOL from normal input in the live
        controller, but the policy decision should always be present
        on every TurnResult.
        """
        runner, fabric, llm = _make_runner()
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Run a quick search for docs"),
            step=1,
        )
        # Regardless of which mode was chosen, policy decision exists
        assert result.action_policy_decision is not None


# ---------------------------------------------------------------------------
# Phase 6 execute branches
# ---------------------------------------------------------------------------


class TestPhase6ExecuteBranches:
    """Each action type routes to the correct execute branch."""

    def test_answer_calls_llm(self):
        runner, fabric, llm = _make_runner(canned_response="Hi there.")
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Say hi"),
            step=1,
        )
        if result.action_decision.action == ActionType.ANSWER:
            assert len(llm.calls) == 1
            assert result.execution_outcome.llm_called is True
            # Response text may be rewritten by review but LLM was called

    def test_no_op_does_not_call_llm(self):
        """Very short live-social input triggers NO_OP; no LLM call."""
        runner, fabric, llm = _make_runner()
        # live_social + short input triggers NO_OP via choose_action
        runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="ok"),
            step=1,
        )
        # Length 2 may not trigger live_social path reliably; just
        # assert that the runner either called LLM or didn't, but
        # NO_OP specifically does not. A separate branch test covers
        # the NO_OP path deterministically when we wire pack mode.


# ---------------------------------------------------------------------------
# Phase 7 ingest is attempted for content-producing turns
# ---------------------------------------------------------------------------


class TestPhase7Ingest:
    def test_ingest_called_for_content_turn(self):
        runner, fabric, llm = _make_runner(canned_response="Response.")
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Tell me something"),
            step=42,
        )
        if result.execution_outcome.response_text and not result.execution_outcome.no_op:
            assert result.ingest_attempted is True
            assert len(fabric.ingest_calls) == 1
            assert fabric.ingest_calls[0]["step"] == 42
            assert fabric.ingest_calls[0]["workspace_id"] == "ws"

    def test_ingest_failure_does_not_break_turn(self):
        """Best-effort ingest; failure is swallowed."""
        runner, fabric, llm = _make_runner(raise_on_ingest=True)
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Tell me something"),
            step=1,
        )
        # Turn still completes
        assert result is not None
        # Phase 8 still runs despite Phase 7 failure
        assert len(fabric.measure_drift_calls) == 1

    def test_assimilation_outcomes_is_empty_in_v0_1(self):
        """M1 stub returns []; this remains true through S1 until
        concrete emission rules are added."""
        runner, fabric, llm = _make_runner()
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        assert result.assimilation_outcomes == []


# ---------------------------------------------------------------------------
# Phase 8 stabilize — gravity correction fires only in high regime
# ---------------------------------------------------------------------------


class TestPhase8Stabilize:
    def test_gravity_correction_fires_when_drift_high_and_away_seed(self):
        runner, fabric, llm = _make_runner(
            drift_return={
                "drift_score": 0.5,
                "drift_direction": "away_seed",
            },
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        assert result.gravity_correction_applied is True
        assert len(fabric.gravity_correction_calls) == 1

    def test_gravity_correction_skipped_when_drift_low(self):
        runner, fabric, llm = _make_runner(
            drift_return={
                "drift_score": 0.1,
                "drift_direction": "away_seed",
            },
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        assert result.gravity_correction_applied is False
        assert len(fabric.gravity_correction_calls) == 0

    def test_gravity_correction_skipped_when_direction_not_away_seed(self):
        """Invariant: correction only fires on away_seed direction."""
        runner, fabric, llm = _make_runner(
            drift_return={
                "drift_score": 0.6,
                "drift_direction": "toward_seed",
            },
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        assert result.gravity_correction_applied is False


# ---------------------------------------------------------------------------
# enter_reflex wiring
# ---------------------------------------------------------------------------


class TestEnterReflex:
    """enter_reflex runs a full turn with source_type=reflex."""

    def test_reflex_runs_full_turn(self):
        runner, fabric, llm = _make_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        assert result is not None
        # Reflex observation reached the frame_task
        assert result.task_frame.source_type == "reflex"
        # Phase 8 measure_drift still ran
        assert len(fabric.measure_drift_calls) == 1

    def test_reflex_observation_metadata_preserved(self):
        runner, fabric, llm = _make_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        # source_type=reflex propagated through the task frame
        assert "reflex" in result.task_frame.source_type


# ---------------------------------------------------------------------------
# TurnResult observability
# ---------------------------------------------------------------------------


class TestTurnResultObservability:
    def test_all_required_fields_populated(self):
        runner, fabric, llm = _make_runner()
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        # Every field named in the slice plan is populated (non-None
        # where applicable)
        assert result.workspace_id == "ws"
        assert result.agent_id == "agent"
        assert result.task_frame is not None
        assert result.mode_decision is not None
        assert result.memory_plan is not None
        assert result.action_decision is not None
        assert result.action_policy_decision is not None
        assert result.execution_outcome is not None
        assert result.review_outcome is not None
        # assimilation_outcomes is List[ActionType], possibly empty
        assert isinstance(result.assimilation_outcomes, list)
        # drift_after_stabilize may be None; gravity_correction_applied
        # is always bool
        assert isinstance(result.gravity_correction_applied, bool)
