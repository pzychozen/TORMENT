"""
Invariant 3 test: Drift in the high regime can veto outward action.

Covers S2 — the drift-regime veto layered on top of the Phase 5
mode-legality gate. Tests both the pure `apply_drift_veto` function
and the integration through `AgentRunner.run_turn`.

This is the first test that directly exercises the load-bearing
"math moves the system" claim: drift score + direction crossing a
kernel-state threshold causes the runner to refuse outward actions
and force a stabilization path. Invariant 3 has to pass for the
doctrine to hold.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 4 (three drift regimes)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 (invariants 3, 6, 9)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S2
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Appendix A (thresholds)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from torment_service.action_policy import (
    ActionPolicyDecision,
    DriftRegime,
    MODE_LEGAL_INTENTS,
    apply_drift_veto,
    apply_legality,
    classify_drift,
    is_legal,
)
from torment_service.agent_loop import AgentRunner, Observation
from torment_service.thinking_controller import ThinkingController
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
    urgency: float = 0.0,
):
    return TaskFrame(
        workspace_id="ws",
        agent_id="agent",
        raw_input="test",
        normalized_input="test",
        governance_sensitive=governance_sensitive,
        ambiguity_score=ambiguity_score,
        tool_need=tool_need,
        urgency=urgency,
    )


def _mode(m: CognitiveMode):
    return CognitiveModeDecision(chosen_mode=m, reason="test")


def _action_decision(at: ActionType):
    return ActionDecision(action=at, reason="test")


def _passthrough_policy(at: ActionType):
    """Build a passthrough ActionPolicyDecision (no legality fallback)."""
    return ActionPolicyDecision(action=_action_decision(at))


def _high_away() -> DriftRegime:
    # Sign convention: score is signed distance from seed basin
    # (negative = far); veto also requires direction == "away_seed".
    return DriftRegime(
        score=-0.5,
        direction="away_seed",
        is_high=True,
        is_away_seed=True,
    )


def _high_toward() -> DriftRegime:
    return DriftRegime(
        score=-0.5,
        direction="toward_seed",
        is_high=True,
        is_away_seed=False,
    )


def _moderate() -> DriftRegime:
    return DriftRegime(
        score=-0.25,
        direction="away_seed",
        is_high=False,
        is_away_seed=True,
    )


def _low() -> DriftRegime:
    return DriftRegime(
        score=-0.05,
        direction="away_seed",
        is_high=False,
        is_away_seed=True,
    )


# ---------------------------------------------------------------------------
# classify_drift
# ---------------------------------------------------------------------------


class TestClassifyDrift:
    """Raw drift info → DriftRegime."""

    def test_none_returns_low_unknown(self):
        r = classify_drift(None)
        assert r.is_high is False
        assert r.is_away_seed is False
        assert r.vetoes_outward_action is False

    def test_high_away_seed(self):
        # Sign convention: negative score = drifted.
        r = classify_drift(
            {"drift_score": -0.5, "drift_direction": "away_seed"}
        )
        assert r.is_high is True
        assert r.is_away_seed is True
        assert r.vetoes_outward_action is True

    def test_high_toward_seed(self):
        # High magnitude but direction says toward_seed.
        r = classify_drift(
            {"drift_score": -0.6, "drift_direction": "toward_seed"}
        )
        assert r.is_high is True
        assert r.is_away_seed is False
        assert r.vetoes_outward_action is False

    def test_at_threshold(self):
        """Exactly -0.35 is high (score <= -threshold)."""
        r = classify_drift(
            {"drift_score": -0.35, "drift_direction": "away_seed"}
        )
        assert r.is_high is True

    def test_just_inside_threshold(self):
        """-0.349 is NOT yet high (score > -0.35)."""
        r = classify_drift(
            {"drift_score": -0.349, "drift_direction": "away_seed"}
        )
        assert r.is_high is False

    def test_positive_score_never_high(self):
        """Positive drift_score means healthy/centered; never high."""
        r = classify_drift(
            {"drift_score": 0.5, "drift_direction": "away_seed"}
        )
        assert r.is_high is False

    def test_custom_threshold(self):
        r = classify_drift(
            {"drift_score": -0.3, "drift_direction": "away_seed"},
            high_threshold=0.2,
        )
        assert r.is_high is True


# ---------------------------------------------------------------------------
# apply_drift_veto — early exits (no veto)
# ---------------------------------------------------------------------------


class TestDriftVetoEarlyExits:
    """Low/moderate drift and high-but-toward-seed pass through unchanged."""

    def test_low_drift_passes_through(self):
        original = _passthrough_policy(ActionType.USE_TOOL)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _low(), _frame()
        )
        assert result is original  # same instance, not just equal
        assert result.drift_veto_applied is False

    def test_moderate_drift_passes_through(self):
        original = _passthrough_policy(ActionType.USE_TOOL)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _moderate(), _frame()
        )
        assert result is original
        assert result.drift_veto_applied is False

    def test_high_toward_seed_passes_through(self):
        """Direction matters: toward_seed → no veto even if score is high."""
        original = _passthrough_policy(ActionType.USE_TOOL)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _high_toward(), _frame()
        )
        assert result is original
        assert result.drift_veto_applied is False

    def test_governance_review_preserved_under_high_drift(self):
        """GOVERNANCE_REVIEW is never vetoed — governance is narrowing."""
        original = _passthrough_policy(ActionType.GOVERNANCE_REVIEW)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.GOVERNED), _high_away(), _frame()
        )
        assert result is original
        assert result.drift_veto_applied is False


# ---------------------------------------------------------------------------
# apply_drift_veto — high regime vetoes outward action
# ---------------------------------------------------------------------------


class TestDriftVetoHighRegime:
    """High regime + away_seed forces outward actions to DEFER or NO_OP."""

    def test_use_tool_in_tool_mode_vetoed_to_defer(self):
        original = _passthrough_policy(ActionType.USE_TOOL)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _high_away(), _frame()
        )
        assert result.action.action == ActionType.DEFER
        assert result.drift_veto_applied is True
        assert result.fallback_reason == "drift_high_regime_veto"

    def test_answer_in_retrieval_vetoed_to_defer(self):
        original = _passthrough_policy(ActionType.ANSWER)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.RETRIEVAL), _high_away(), _frame()
        )
        assert result.action.action == ActionType.DEFER
        assert result.drift_veto_applied is True

    def test_answer_in_fast_vetoed_to_no_op(self):
        """FAST has no DEFER legal, so veto terminus is NO_OP."""
        original = _passthrough_policy(ActionType.ANSWER)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.FAST), _high_away(), _frame()
        )
        assert result.action.action == ActionType.NO_OP
        assert result.drift_veto_applied is True
        assert result.fallback_reason == "drift_high_regime_veto_no_defer_legal"

    def test_answer_in_live_social_vetoed_to_no_op(self):
        """LIVE_SOCIAL has no DEFER legal either → NO_OP terminus."""
        original = _passthrough_policy(ActionType.ANSWER)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.LIVE_SOCIAL), _high_away(), _frame()
        )
        assert result.action.action == ActionType.NO_OP
        assert result.drift_veto_applied is True

    def test_veto_records_drift_state_in_payload(self):
        """Observability: payload carries the drift score + direction
        that caused the veto."""
        original = _passthrough_policy(ActionType.USE_TOOL)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _high_away(), _frame()
        )
        assert result.action.payload.get("drift_score") == -0.5
        assert result.action.payload.get("drift_direction") == "away_seed"
        assert result.action.payload.get("pre_drift_action") == "use_tool"


# ---------------------------------------------------------------------------
# apply_drift_veto — governance + urgency override
# ---------------------------------------------------------------------------


class TestDriftVetoOverride:
    """Governance + urgency bypasses drift veto."""

    def test_governance_and_high_urgency_bypasses_veto(self):
        original = _passthrough_policy(ActionType.USE_TOOL)
        frame = _frame(governance_sensitive=True, urgency=0.9)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _high_away(), frame
        )
        # Override fires: veto bypassed, original policy decision returned.
        assert result is original
        assert result.drift_veto_applied is False
        assert result.action.action == ActionType.USE_TOOL

    def test_governance_without_urgency_does_not_override(self):
        """Both flags required: governance alone is insufficient."""
        original = _passthrough_policy(ActionType.USE_TOOL)
        frame = _frame(governance_sensitive=True, urgency=0.5)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _high_away(), frame
        )
        # No override; veto fires.
        assert result.drift_veto_applied is True

    def test_urgency_without_governance_does_not_override(self):
        """Both flags required: urgency alone is insufficient."""
        original = _passthrough_policy(ActionType.USE_TOOL)
        frame = _frame(governance_sensitive=False, urgency=0.9)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _high_away(), frame
        )
        assert result.drift_veto_applied is True

    def test_urgency_at_boundary_does_not_override(self):
        """Boundary: urgency > 0.7 required, not >=."""
        original = _passthrough_policy(ActionType.USE_TOOL)
        frame = _frame(governance_sensitive=True, urgency=0.7)
        result = apply_drift_veto(
            original, _mode(CognitiveMode.TOOL), _high_away(), frame
        )
        assert result.drift_veto_applied is True


# ---------------------------------------------------------------------------
# apply_drift_veto — invariant 6: veto never widens
# ---------------------------------------------------------------------------


class TestDriftVetoNeverWidens:
    """Whatever the veto produces, it must be legal for the current mode."""

    @pytest.mark.parametrize("mode", list(CognitiveMode))
    @pytest.mark.parametrize(
        "original_action",
        [
            ActionType.ANSWER,
            ActionType.USE_TOOL,
            ActionType.ASK_CLARIFICATION,
            ActionType.DEFER,
        ],
    )
    def test_veto_output_is_always_legal_for_mode(
        self, mode, original_action
    ):
        original = _passthrough_policy(original_action)
        # Not passing governance override, so veto fires when applicable
        result = apply_drift_veto(
            original, _mode(mode), _high_away(), _frame()
        )
        assert is_legal(mode, result.action.action), (
            f"apply_drift_veto produced {result.action.action.value!r} in "
            f"mode {mode.value!r}, which is not in legal set "
            f"{[a.value for a in MODE_LEGAL_INTENTS[mode]]}. "
            f"Invariant 9 violation: drift veto widened legality."
        )


# ---------------------------------------------------------------------------
# apply_drift_veto — composition with apply_legality
# ---------------------------------------------------------------------------


class TestDriftVetoComposedWithLegality:
    """Phase 5 is `apply_legality` then `apply_drift_veto`. Composition
    is tested here to show the two gates work together."""

    def test_composition_tool_mode_answer_high_drift(self):
        """mode=TOOL + ANSWER (illegal pre-veto) + high drift away_seed.

        apply_legality: ANSWER illegal in TOOL → fallback to DEFER.
        apply_drift_veto: DEFER is legal in TOOL and is already a
        stabilization intent; no further downgrade.
        """
        action = _action_decision(ActionType.ANSWER)
        mode = _mode(CognitiveMode.TOOL)
        frame = _frame()

        after_legality = apply_legality(action, mode, frame)
        assert after_legality.action.action == ActionType.DEFER

        after_veto = apply_drift_veto(after_legality, mode, _high_away(), frame)
        # DEFER is already in the stabilization set; veto doesn't need
        # to do more. But it DOES note drift_veto for observability?
        # Per current impl, DEFER is not GOVERNANCE_REVIEW so veto
        # applies; DEFER → DEFER (same action, but veto "fired" since
        # the primary action isn't GOVERNANCE_REVIEW). Let me check:
        # Actually, per the logic, DEFER → DEFER via the "legal set has
        # DEFER, produce DEFER" branch. drift_veto_applied is True.
        assert after_veto.action.action == ActionType.DEFER
        assert after_veto.drift_veto_applied is True

    def test_composition_fast_mode_answer_high_drift(self):
        """mode=FAST + ANSWER (legal) + high drift away_seed.

        apply_legality: ANSWER legal in FAST → passes through.
        apply_drift_veto: ANSWER in FAST under high drift → DEFER not
        legal in FAST → NO_OP terminus.
        """
        action = _action_decision(ActionType.ANSWER)
        mode = _mode(CognitiveMode.FAST)
        frame = _frame()

        after_legality = apply_legality(action, mode, frame)
        assert after_legality.action.action == ActionType.ANSWER

        after_veto = apply_drift_veto(after_legality, mode, _high_away(), frame)
        assert after_veto.action.action == ActionType.NO_OP
        assert after_veto.drift_veto_applied is True


# ---------------------------------------------------------------------------
# AgentRunner integration — drift veto wired in Phase 5
# ---------------------------------------------------------------------------


@dataclass
class FakeFabric:
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)
    drift_return: Optional[Dict[str, Any]] = None

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append({"step": step})
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append({})
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append({"drift_info": drift_info})


@dataclass
class FakeLLM:
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def complete(self, system_prompt, messages, tools=None):
        self.calls.append({"tools": tools})
        return "LLM response."


class TestRunnerDriftVetoIntegration:
    """Drift veto is wired in Phase 5 inside AgentRunner.run_turn."""

    def test_high_drift_veto_causes_defer_through_runner(self):
        fabric = FakeFabric(
            drift_return={"drift_score": -0.5, "drift_direction": "away_seed"}
        )
        llm = FakeLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Say something"),
            step=1,
        )
        # Drift veto should have fired for any outward action
        assert result.action_policy_decision.drift_veto_applied is True

    def test_high_drift_no_llm_called(self):
        """When drift veto forces DEFER, the LLM is not called."""
        fabric = FakeFabric(
            drift_return={"drift_score": -0.5, "drift_direction": "away_seed"}
        )
        llm = FakeLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
        )
        runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Tell me a story"),
            step=1,
        )
        # No LLM call because DEFER path uses template text
        assert len(llm.calls) == 0

    def test_high_drift_gravity_correction_still_fires(self):
        """Phase 8 gravity correction still runs when Phase 5 veto fires."""
        fabric = FakeFabric(
            drift_return={"drift_score": -0.5, "drift_direction": "away_seed"}
        )
        llm = FakeLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Say something"),
            step=1,
        )
        assert result.gravity_correction_applied is True
        assert len(fabric.gravity_correction_calls) == 1

    def test_low_drift_no_veto_llm_called_for_answer(self):
        """Under low drift, normal ANSWER flow proceeds; LLM is called."""
        fabric = FakeFabric(
            drift_return={"drift_score": 0.05, "drift_direction": "away_seed"}
        )
        llm = FakeLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Say something"),
            step=1,
        )
        if result.action_decision.action == ActionType.ANSWER:
            assert len(llm.calls) == 1
        assert result.action_policy_decision.drift_veto_applied is False

    def test_measure_drift_called_exactly_once_per_turn(self):
        """Phase 5 measurement is reused in Phase 8; no double call."""
        fabric = FakeFabric(
            drift_return={"drift_score": -0.2, "drift_direction": "away_seed"}
        )
        llm = FakeLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
        )
        runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        assert len(fabric.measure_drift_calls) == 1

    def test_high_drift_turn_records_original_action_in_policy(self):
        """When veto fires, the pre-veto action type is preserved."""
        fabric = FakeFabric(
            drift_return={"drift_score": -0.5, "drift_direction": "away_seed"}
        )
        llm = FakeLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Give me an answer"),
            step=1,
        )
        # original_action_type is populated on the policy decision
        if result.action_policy_decision.drift_veto_applied:
            assert result.action_policy_decision.original_action_type is not None
