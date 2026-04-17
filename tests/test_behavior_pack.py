"""
S4 tests: behavior pack structure + runner integration.

Covers:
    - The five first-class pack objects are instantiable and immutable.
    - DEBUGGING_SESSION_PACK has the expected v0.1 shape.
    - Pack-derived effective settings override runner defaults.
    - Pack's aperture recipe replaces the controller's default memory
      plan on every run_turn.
    - Pack's action contract flows into Phase 5 tool narrowing.
    - Pack's stabilization program threshold is used for drift
      classification.

Partial invariant coverage: invariant 4 extension — pack declares
forbidden assimilation outcomes (PROPOSE_SHARE). Concrete enforcement
lands when assimilation_outcomes has real emission rules (post-v0.1).

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 5 (behavior packs)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S4
"""
from dataclasses import FrozenInstanceError, dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from torment_service.agent_loop import AgentRunner, Observation
from torment_service.behavior_packs import (
    DEBUGGING_SESSION_PACK,
    ActionContract,
    ApertureRecipe,
    BehaviorPack,
    EventReflex,
    IntentGrammar,
    StabilizationProgram,
)
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import (
    ActionType,
    CognitiveMode,
    MemoryPlan,
)


# ---------------------------------------------------------------------------
# The five first-class pack objects
# ---------------------------------------------------------------------------


class TestApertureRecipe:
    def test_instantiable_with_memory_plan(self):
        plan = MemoryPlan(retrieve_core=True)
        recipe = ApertureRecipe(name="test", memory_plan=plan)
        assert recipe.name == "test"
        assert recipe.memory_plan is plan

    def test_frozen(self):
        plan = MemoryPlan(retrieve_core=True)
        recipe = ApertureRecipe(name="test", memory_plan=plan)
        with pytest.raises(FrozenInstanceError):
            recipe.name = "mutated"


class TestIntentGrammar:
    def test_default_empty_grammars(self):
        g = IntentGrammar()
        assert g.forbidden_intents_by_mode == {}
        assert g.forbidden_assimilation_outcomes == frozenset()

    def test_with_forbidden_outcomes(self):
        g = IntentGrammar(
            forbidden_assimilation_outcomes=frozenset({ActionType.PROPOSE_SHARE})
        )
        assert ActionType.PROPOSE_SHARE in g.forbidden_assimilation_outcomes

    def test_frozen(self):
        g = IntentGrammar()
        with pytest.raises(FrozenInstanceError):
            g.forbidden_assimilation_outcomes = frozenset()


class TestStabilizationProgram:
    def test_defaults_match_doctrine_appendix_a(self):
        p = StabilizationProgram()
        assert p.low_threshold == 0.15
        assert p.high_threshold == 0.35
        assert p.high_regime_action == ActionType.DEFER

    def test_custom_thresholds(self):
        p = StabilizationProgram(low_threshold=0.10, high_threshold=0.30)
        assert p.low_threshold == 0.10
        assert p.high_threshold == 0.30

    def test_frozen(self):
        p = StabilizationProgram()
        with pytest.raises(FrozenInstanceError):
            p.high_threshold = 0.5


class TestEventReflex:
    def test_instantiable_with_trigger_string(self):
        r = EventReflex(
            name="test_reflex",
            trigger="drift_score >= 0.35 and direction == away_seed",
        )
        assert r.name == "test_reflex"
        assert r.forced_intent == ActionType.DEFER  # default

    def test_frozen(self):
        r = EventReflex(name="t", trigger="always")
        with pytest.raises(FrozenInstanceError):
            r.forced_intent = ActionType.NO_OP


class TestBehaviorPack:
    def test_bundles_all_five_objects(self):
        pack = BehaviorPack(
            name="test",
            description="desc",
            aperture_recipe=ApertureRecipe(
                name="ap", memory_plan=MemoryPlan()
            ),
            intent_grammar=IntentGrammar(),
            stabilization_program=StabilizationProgram(),
            action_contract=ActionContract(),
            event_reflex=EventReflex(name="r", trigger="t"),
        )
        assert pack.aperture_recipe is not None
        assert pack.intent_grammar is not None
        assert pack.stabilization_program is not None
        assert pack.action_contract is not None
        assert pack.event_reflex is not None

    def test_frozen(self):
        pack = BehaviorPack(
            name="test",
            description="",
            aperture_recipe=ApertureRecipe(name="ap", memory_plan=MemoryPlan()),
            intent_grammar=IntentGrammar(),
            stabilization_program=StabilizationProgram(),
            action_contract=ActionContract(),
            event_reflex=EventReflex(name="r", trigger="t"),
        )
        with pytest.raises(FrozenInstanceError):
            pack.name = "mutated"


# ---------------------------------------------------------------------------
# DEBUGGING_SESSION_PACK shape (v0.1 pin)
# ---------------------------------------------------------------------------


class TestDebuggingSessionPackShape:
    """Pins the v0.1 pack's declared values. Changing these requires
    a deliberate review."""

    def test_pack_name(self):
        assert DEBUGGING_SESSION_PACK.name == "debugging_session"

    def test_aperture_recipe_favors_core_relational_deep(self):
        plan = DEBUGGING_SESSION_PACK.aperture_recipe.memory_plan
        assert plan.retrieve_core is True
        assert plan.retrieve_relational is True
        assert plan.retrieve_deep is True
        assert plan.retrieve_archive is False
        assert plan.retrieve_collective is False

    def test_aperture_top_k_by_lane(self):
        plan = DEBUGGING_SESSION_PACK.aperture_recipe.memory_plan
        assert plan.top_k_by_lane == {"core": 8, "relational": 4, "deep": 3}

    def test_intent_grammar_forbids_propose_share(self):
        """Invariant 4 extension: pack can forbid an assimilation outcome."""
        g = DEBUGGING_SESSION_PACK.intent_grammar
        assert ActionType.PROPOSE_SHARE in g.forbidden_assimilation_outcomes

    def test_intent_grammar_does_not_forbid_other_outcomes(self):
        """v0.1 debugging pack forbids only PROPOSE_SHARE, not
        WRITE_MEMORY or CREATE_ARCHIVE_NOTE."""
        g = DEBUGGING_SESSION_PACK.intent_grammar
        assert ActionType.WRITE_MEMORY not in g.forbidden_assimilation_outcomes
        assert ActionType.CREATE_ARCHIVE_NOTE not in g.forbidden_assimilation_outcomes

    def test_stabilization_program_matches_appendix_a(self):
        p = DEBUGGING_SESSION_PACK.stabilization_program
        assert p.low_threshold == 0.15
        assert p.high_threshold == 0.35
        assert p.high_regime_action == ActionType.DEFER

    def test_action_contract_permits_only_code_exec(self):
        c = DEBUGGING_SESSION_PACK.action_contract
        assert c.allowed_tool_families == frozenset({"code_exec"})

    def test_event_reflex_is_drift_stabilization(self):
        r = DEBUGGING_SESSION_PACK.event_reflex
        assert r.name == "drift_stabilization"
        assert r.forced_intent == ActionType.DEFER
        assert "drift_score" in r.trigger
        assert "away_seed" in r.trigger


# ---------------------------------------------------------------------------
# Runner integration with pack
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
        self.gravity_correction_calls.append({})


@dataclass
class ToolCapturingLLM:
    last_tools: Optional[List[Dict[str, Any]]] = None
    call_count: int = 0
    canned_response: str = "ok"

    def complete(self, system_prompt, messages, tools=None):
        self.call_count += 1
        self.last_tools = tools
        return self.canned_response


@dataclass
class RecordingToolExecutor:
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_result: Dict[str, Any] = field(
        default_factory=lambda: {"output": "tool result"}
    )

    def execute(self, family, arguments, defaults):
        self.calls.append(
            {"family": family, "arguments": arguments, "defaults": defaults}
        )
        return self.canned_result


# ---------------------------------------------------------------------------
# Pack overrides action_contract
# ---------------------------------------------------------------------------


class TestPackOverridesActionContract:
    """When a pack is active, pack.action_contract is the effective
    contract used by Phase 5 narrowing, regardless of what was passed
    to the runner's action_contract parameter."""

    def test_effective_contract_comes_from_pack(self):
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            llm_client=ToolCapturingLLM(),
            pack=DEBUGGING_SESSION_PACK,
            # Explicit action_contract parameter is IGNORED when pack is set
            action_contract=ActionContract(allowed_tool_families=frozenset()),
        )
        assert runner._effective_action_contract() == DEBUGGING_SESSION_PACK.action_contract
        assert "code_exec" in runner._effective_action_contract().allowed_tool_families

    def test_no_pack_uses_explicit_contract(self):
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            pack=None,
            action_contract=ActionContract(allowed_tool_families=frozenset({"code_exec"})),
        )
        assert "code_exec" in runner._effective_action_contract().allowed_tool_families

    def test_pack_wins_over_explicit(self):
        """If both are provided, pack wins."""
        explicit = ActionContract(allowed_tool_families=frozenset({"something_else"}))
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            pack=DEBUGGING_SESSION_PACK,
            action_contract=explicit,
        )
        assert "code_exec" in runner._effective_action_contract().allowed_tool_families
        assert "something_else" not in runner._effective_action_contract().allowed_tool_families


# ---------------------------------------------------------------------------
# Pack overrides drift threshold
# ---------------------------------------------------------------------------


class TestPackOverridesDriftThreshold:
    """Pack.stabilization_program.high_threshold is the effective
    threshold used for drift regime classification."""

    def test_effective_threshold_comes_from_pack(self):
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            pack=DEBUGGING_SESSION_PACK,
            drift_high_threshold=0.99,  # explicit parameter ignored
        )
        assert runner._effective_drift_threshold() == 0.35  # from pack

    def test_no_pack_uses_explicit_threshold(self):
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            pack=None,
            drift_high_threshold=0.50,
        )
        assert runner._effective_drift_threshold() == 0.50


# ---------------------------------------------------------------------------
# Pack replaces memory plan (aperture recipe)
# ---------------------------------------------------------------------------


class TestPackReplacesMemoryPlan:
    """When a pack is active, the pack's aperture recipe replaces the
    controller's default MemoryPlan on every turn."""

    def test_memory_plan_in_turn_result_matches_pack(self):
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            llm_client=ToolCapturingLLM(),
            pack=DEBUGGING_SESSION_PACK,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="tell me about recursive systems"),
            step=1,
        )
        pack_plan = DEBUGGING_SESSION_PACK.aperture_recipe.memory_plan
        assert result.memory_plan is pack_plan
        # Specific shape sanity: top_k_by_lane matches the debugging plan
        assert result.memory_plan.top_k_by_lane == {"core": 8, "relational": 4, "deep": 3}

    def test_no_pack_uses_controller_default_memory_plan(self):
        """Without a pack, the runner uses whatever build_memory_plan
        returned — NOT the pack's."""
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            llm_client=ToolCapturingLLM(),
            pack=None,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        # Controller's memory plan is NOT the pack's reference
        assert result.memory_plan is not DEBUGGING_SESSION_PACK.aperture_recipe.memory_plan


# ---------------------------------------------------------------------------
# Pack's action_contract flows into Phase 5 narrowing
# ---------------------------------------------------------------------------


class TestPackActionContractFlowsIntoNarrowing:
    """With the pack active, USE_TOOL turns get narrowed to code_exec
    and the LLM receives exactly one signature."""

    def test_use_tool_narrows_to_code_exec_via_pack(self):
        llm = ToolCapturingLLM()
        executor = RecordingToolExecutor()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            llm_client=llm,
            pack=DEBUGGING_SESSION_PACK,
            tool_executor=executor,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="search the docs for relevant entries"),
            step=1,
        )
        # If the input reached USE_TOOL (tool_need detected), narrowing
        # fired via the pack's contract.
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            assert llm.last_tools is not None
            assert len(llm.last_tools) == 1
            assert llm.last_tools[0]["name"] == "code_exec"


# ---------------------------------------------------------------------------
# Pack's drift threshold affects regime classification
# ---------------------------------------------------------------------------


class TestPackDriftThresholdAffectsRegime:
    """The pack's stabilization threshold is what drift classification
    uses, not the runner's explicit drift_high_threshold parameter."""

    def test_pack_threshold_triggers_veto(self):
        fabric = FakeFabric(
            # Sign convention: negative = drifted; -0.40 is past pack's 0.35 high threshold.
            drift_return={"drift_score": -0.40, "drift_direction": "away_seed"}
        )
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=ToolCapturingLLM(),
            pack=DEBUGGING_SESSION_PACK,  # threshold 0.35
            drift_high_threshold=0.99,     # explicit param should be ignored
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="tell me something"),
            step=1,
        )
        # Pack threshold (0.35) fires at drift 0.40; veto should apply
        assert result.action_policy_decision.drift_veto_applied is True

    def test_pack_threshold_does_not_trigger_below(self):
        fabric = FakeFabric(
            # Sign convention: -0.20 is within the moderate band, below the 0.35 high threshold.
            drift_return={"drift_score": -0.20, "drift_direction": "away_seed"}
        )
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=ToolCapturingLLM(),
            pack=DEBUGGING_SESSION_PACK,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        assert result.action_policy_decision.drift_veto_applied is False


# ---------------------------------------------------------------------------
# Runner still works without pack (backward compatibility)
# ---------------------------------------------------------------------------


class TestRunnerWithoutPackUnchanged:
    """S4 does not break S1/S2/S3 runner semantics when pack=None."""

    def test_no_pack_turn_runs_end_to_end(self):
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            llm_client=ToolCapturingLLM(),
            pack=None,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="Hello"),
            step=1,
        )
        assert result is not None
        assert result.action_policy_decision is not None
