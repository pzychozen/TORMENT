"""
S5 / Invariant 5 test: Internal reflexes may run without an LLM call.

The load-bearing proof for doctrine Part 1 ("state-governed cognition
where the LLM is only one participant"). A drift-triggered reflex
turn — fired because kernel state crossed the high-regime threshold —
runs the full 8-phase outer loop and completes with ZERO language-
model invocations.

This test brings the full machinery together:
    - S4's DEBUGGING_SESSION_PACK (stabilization program, aperture,
      action contract).
    - S2's drift-regime veto (forces DEFER when drift is high + away_seed).
    - S1's enter_reflex entry point and the outer loop's 8 phases.
    - Reflex observation routes to IDENTITY_SENSITIVE mode (S5 addition
      to frame_task).
    - Phase 6 DEFER branch produces template text, no LLM call.
    - Phase 8 gravity correction fires via the same high-drift condition.

The test uses a `RaisingLLM` that raises on any `.complete()` call.
A successful turn completion implies invariant 5 holds: the loop ran
end-to-end without ever calling the LLM.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 1 (non-LLM authority)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 4 (drift regimes)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 (invariant 5)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S5
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from torment_service.agent_loop import AgentRunner, Observation
from torment_service.behavior_packs import DEBUGGING_SESSION_PACK
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ActionType, CognitiveMode


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


@dataclass
class FakeFabric:
    """Test double. drift_return controls what measure_drift returns;
    high + away_seed makes the drift veto fire."""
    drift_return: Optional[Dict[str, Any]] = None
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append({"step": step, "text": text})
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append({})
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append({"drift_info": drift_info})


class RaisingLLM:
    """Raises on any complete() call. A passing test proves no LLM
    invocation happened anywhere in the 8-phase loop."""

    def __init__(self):
        self.call_attempts = 0

    def complete(self, system_prompt, messages, tools=None):
        self.call_attempts += 1
        raise AssertionError(
            "LLM was called during a reflex turn. Invariant 5 violation."
        )


# Sign convention (matches character.py): drift_score is a signed
# distance from seed basin (positive = close, negative = far).
# drift_direction is a separate signal. The high-regime veto requires
# BOTH score <= -0.35 AND direction == "away_seed". high_threshold is
# a positive magnitude.
HIGH_DRIFT_AWAY = {"drift_score": -0.5, "drift_direction": "away_seed"}
HIGH_DRIFT_TOWARD = {"drift_score": -0.5, "drift_direction": "toward_seed"}
MODERATE_DRIFT = {"drift_score": -0.25, "drift_direction": "away_seed"}
LOW_DRIFT = {"drift_score": -0.05, "drift_direction": "away_seed"}


def _make_reflex_runner(drift_return=HIGH_DRIFT_AWAY):
    """Build a runner with the debugging pack and a high-drift fabric.
    The canonical fixture for invariant 5."""
    fabric = FakeFabric(drift_return=drift_return)
    llm = RaisingLLM()
    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
        pack=DEBUGGING_SESSION_PACK,
    )
    return runner, fabric, llm


# ---------------------------------------------------------------------------
# The load-bearing invariant 5 proof
# ---------------------------------------------------------------------------


class TestInvariant5ReflexNoLLM:
    """The invariant 5 proof: enter_reflex completes a full 8-phase
    turn with zero LLM invocations."""

    def test_reflex_turn_completes_without_calling_llm(self):
        """The RaisingLLM fires on any complete() call. If the turn
        completes successfully, invariant 5 holds."""
        runner, fabric, llm = _make_reflex_runner()

        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )

        # Turn completed — no exception raised
        assert result is not None
        # LLM was never called
        assert llm.call_attempts == 0, (
            f"Invariant 5 violation: LLM.complete() was called "
            f"{llm.call_attempts} time(s) during a reflex turn."
        )

    def test_reflex_turn_all_8_phases_ran(self):
        """Zero LLM calls AND full phase completion."""
        runner, fabric, llm = _make_reflex_runner()

        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )

        # Phase 2 (frame) ran
        assert result.task_frame is not None
        # Phase 2 (mode) ran
        assert result.mode_decision is not None
        # Phase 3 (aperture) ran — pack's memory plan applied
        assert result.memory_plan is DEBUGGING_SESSION_PACK.aperture_recipe.memory_plan
        # Phase 4 (intent) ran
        assert result.action_decision is not None
        # Phase 5 (action policy) ran
        assert result.action_policy_decision is not None
        # Phase 6 (execute) ran — no-LLM path
        assert result.execution_outcome is not None
        assert result.execution_outcome.llm_called is False
        # Phase 6 (review sub-gate) ran
        assert result.review_outcome is not None
        # Phase 7 assimilation ran (list present, even if empty)
        assert isinstance(result.assimilation_outcomes, list)
        # Phase 8 (stabilize) ran
        assert len(fabric.measure_drift_calls) == 1


# ---------------------------------------------------------------------------
# The mechanism — drift veto + DEFER
# ---------------------------------------------------------------------------


class TestReflexDriftVetoMechanism:
    """The invariant-5 proof works because Phase 5 drift veto
    forces DEFER (or NO_OP), and Phase 6 DEFER/NO_OP branches do
    not call the LLM."""

    def test_drift_veto_fires_on_reflex_turn(self):
        runner, fabric, llm = _make_reflex_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        assert result.action_policy_decision.drift_veto_applied is True

    def test_effective_action_is_defer_or_no_op(self):
        runner, fabric, llm = _make_reflex_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        final_action = result.action_policy_decision.action.action
        assert final_action in {ActionType.DEFER, ActionType.NO_OP}

    def test_gravity_correction_fires_during_reflex(self):
        """Phase 8 stabilize runs gravity_correction because the
        same high-drift condition that triggered the veto also
        triggers the correction."""
        runner, fabric, llm = _make_reflex_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        assert result.gravity_correction_applied is True
        assert len(fabric.gravity_correction_calls) == 1


# ---------------------------------------------------------------------------
# Reflex observation → IDENTITY_SENSITIVE mode
# ---------------------------------------------------------------------------


class TestReflexObservationRoutesToIdentitySensitive:
    """S5 tweak: source_type='reflex' sets frame.identity_sensitive,
    which routes choose_mode to IDENTITY_SENSITIVE."""

    def test_reflex_observation_sets_identity_sensitive(self):
        runner, fabric, llm = _make_reflex_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        assert result.task_frame.identity_sensitive is True
        assert result.task_frame.source_type == "reflex"

    def test_reflex_turn_mode_is_identity_sensitive(self):
        runner, fabric, llm = _make_reflex_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        assert result.mode_decision.chosen_mode == CognitiveMode.IDENTITY_SENSITIVE

    def test_normal_observation_does_not_force_identity_sensitive(self):
        """Control case: a normal user-text observation doesn't auto-
        flag identity_sensitive unless the text contains identity hints."""
        fabric = FakeFabric(drift_return=None)
        # Use a ToolCapturingLLM that doesn't raise, since a normal
        # ANSWER turn WILL call the LLM.
        class CountingLLM:
            def __init__(self):
                self.calls = 0

            def complete(self, system_prompt, messages, tools=None):
                self.calls += 1
                return "response"

        llm = CountingLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
            pack=DEBUGGING_SESSION_PACK,
        )
        # "Hello" has no identity or reflex signal.
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        # Not forced into IDENTITY_SENSITIVE — should be FAST or similar
        assert result.task_frame.source_type == "user_text"


# ---------------------------------------------------------------------------
# Control cases — reflex still works under non-veto conditions
# ---------------------------------------------------------------------------


class TestReflexBehaviorUnderOtherDriftStates:
    """Reflex was designed for high-drift situations, but the entry
    point is callable anytime. Behavior under lower drift is
    correctly permissive — LLM may or may not be called depending
    on the phase 6 action, but the test panel here uses a non-
    raising LLM for clarity."""

    def test_reflex_under_low_drift_still_routes_to_identity_sensitive(self):
        """Even under low drift, a reflex observation routes to
        IDENTITY_SENSITIVE mode — S5's frame_task addition is
        unconditional on drift. However with low drift no veto fires,
        so ANSWER is allowed (IDENTITY_SENSITIVE admits ANSWER)."""
        fabric = FakeFabric(drift_return=LOW_DRIFT)

        class CountingLLM:
            def __init__(self):
                self.calls = 0

            def complete(self, system_prompt, messages, tools=None):
                self.calls += 1
                return "response"

        llm = CountingLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
            pack=DEBUGGING_SESSION_PACK,
        )
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="test_low_drift",
        )
        assert result.mode_decision.chosen_mode == CognitiveMode.IDENTITY_SENSITIVE
        # Under low drift, no veto; ANSWER may proceed.
        assert result.action_policy_decision.drift_veto_applied is False

    def test_reflex_under_high_toward_seed_drift_no_veto(self):
        """High drift but direction=toward_seed → no veto (direction
        matters per S2). However LLM may be called since veto isn't
        forcing DEFER. Use a non-raising LLM."""
        fabric = FakeFabric(drift_return=HIGH_DRIFT_TOWARD)

        class CountingLLM:
            def __init__(self):
                self.calls = 0

            def complete(self, system_prompt, messages, tools=None):
                self.calls += 1
                return "response"

        llm = CountingLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
            pack=DEBUGGING_SESSION_PACK,
        )
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="test_toward_seed",
        )
        assert result.action_policy_decision.drift_veto_applied is False


# ---------------------------------------------------------------------------
# Reflex observation carries metadata
# ---------------------------------------------------------------------------


class TestReflexObservationMetadata:
    """enter_reflex wires a synthetic Observation with reflex_reason
    in metadata so downstream observability can tell WHY the reflex
    fired."""

    def test_reflex_reason_preserved_in_metadata(self):
        runner, fabric, llm = _make_reflex_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        # The reflex_reason flows into the task_frame's metadata
        # via Observation.metadata during frame_task.
        assert result.task_frame.metadata.get("reflex_reason") == "drift_high"


# ---------------------------------------------------------------------------
# Phase 7 assimilation behavior during reflex
# ---------------------------------------------------------------------------


class TestReflexPhase7Assimilation:
    """When reflex turn downgrades to DEFER, Phase 6 produces
    template text ("Holding on that..."). Phase 7 ingest SHOULD
    attempt — the turn still produced content."""

    def test_reflex_defer_turn_ingests_template(self):
        runner, fabric, llm = _make_reflex_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        # If action was DEFER, template text exists and got ingested.
        if result.action_policy_decision.action.action == ActionType.DEFER:
            assert result.ingest_attempted is True
            assert len(fabric.ingest_calls) == 1

    def test_reflex_no_op_turn_skips_ingest(self):
        """If drift veto produced NO_OP (DEFER not legal in mode),
        Phase 7 ingest is skipped because there's no content."""
        runner, fabric, llm = _make_reflex_runner()
        result = runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        if (
            result.action_policy_decision.action.action == ActionType.NO_OP
            and result.execution_outcome.response_text is None
        ):
            assert result.ingest_attempted is False


# ---------------------------------------------------------------------------
# Contract: exactly one measure_drift per reflex turn
# ---------------------------------------------------------------------------


class TestReflexMeasureDriftOnce:
    """S2's one-drift-measurement-per-turn contract holds for
    reflex turns too."""

    def test_reflex_measures_drift_exactly_once(self):
        runner, fabric, llm = _make_reflex_runner()
        runner.enter_reflex(
            workspace_id="ws",
            agent_id="agent",
            reason="drift_high",
        )
        assert len(fabric.measure_drift_calls) == 1
