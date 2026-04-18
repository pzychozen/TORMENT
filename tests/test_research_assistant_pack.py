"""
v0.1.1 tests: RESEARCH_ASSISTANT_PACK shape + runner integration.

Ratified framing: outputs/RESEARCH_ASSISTANT_PACK_FRAMING_v0.1.md

The load-bearing architectural probe is:

    Can a behavior pack validly represent a capability it does not
    yet operationally possess, as long as it degrades cleanly to
    answer-only behavior?

Ratified answer: yes. These tests prove the pack-shape assertions
(retrieval-shaped aperture, forbid PROPOSE_SHARE, EMPTY_CONTRACT),
plus the live composability assertion: when the LLM deliberates
USE_TOOL under this pack, Phase 5 downgrades cleanly via
apply_tool_narrowing's zero-family path.

Also covers distinctness from DEBUGGING_SESSION_PACK: the two packs
are meaningfully different shapes of the same five-object bundle.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 5 (behavior packs)
    - outputs/RESEARCH_ASSISTANT_PACK_FRAMING_v0.1.md (ratified)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from torment_service.action_policy import apply_tool_narrowing
from torment_service.agent_loop import AgentRunner, Observation
from torment_service.behavior_packs import (
    DEBUGGING_SESSION_PACK,
    RESEARCH_ASSISTANT_PACK,
)
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveMode,
    CognitiveModeDecision,
)
from torment_service.tool_registry import EMPTY_CONTRACT


# ---------------------------------------------------------------------------
# Pack shape assertions — pins the v0.1.1 declaration
# ---------------------------------------------------------------------------


class TestResearchAssistantPackShape:
    """Pin the v0.1.1 pack's declared values. Changing these requires
    a deliberate review, and likely a new GPT-ratification round."""

    def test_pack_name(self):
        assert RESEARCH_ASSISTANT_PACK.name == "research_assistant"

    def test_pack_has_description(self):
        """Description documents retrieval-ready posture — the pack's
        declared-but-absent-capability stance is load-bearing, not
        just a code comment."""
        desc = RESEARCH_ASSISTANT_PACK.description.lower()
        assert "research" in desc
        assert "retrieval" in desc
        assert "empty_contract" in desc or "empty contract" in desc


class TestResearchAssistantAperture:
    """Privileges archive + deep over core + relational. Materially
    distinct from DEBUGGING_SESSION_PACK's aperture."""

    def _plan(self):
        return RESEARCH_ASSISTANT_PACK.aperture_recipe.memory_plan

    def test_aperture_recipe_name(self):
        assert RESEARCH_ASSISTANT_PACK.aperture_recipe.name == "research_assistant"

    def test_privileges_archive_and_deep(self):
        plan = self._plan()
        assert plan.retrieve_archive is True
        assert plan.retrieve_deep is True

    def test_de_emphasizes_core_keeps_on(self):
        """Core stays on (identity needs it) but is de-weighted vs. debugging."""
        plan = self._plan()
        assert plan.retrieve_core is True
        assert plan.weight_by_lane["core"] == 0.80

    def test_relational_lane_off(self):
        """Ratified: research is substantive over collaborative-episodic.
        A collaborative-research variant would be a separate pack."""
        plan = self._plan()
        assert plan.retrieve_relational is False

    def test_collective_off(self):
        """Default-off matches debugging — changing this is a doctrine
        concern, not a pack-#2 concern."""
        plan = self._plan()
        assert plan.retrieve_collective is False

    def test_character_state_on(self):
        """Identity must outrank archive — keep character state retrieval on."""
        plan = self._plan()
        assert plan.retrieve_character_state is True

    def test_top_k_by_lane(self):
        """Archive-dominant: archive=10 > deep=8 > core=4."""
        plan = self._plan()
        assert plan.top_k_by_lane == {"core": 4, "archive": 10, "deep": 8}

    def test_weight_by_lane(self):
        """Archive=1.00, deep=0.90, core=0.80. Archive is the anchor."""
        plan = self._plan()
        assert plan.weight_by_lane == {"core": 0.80, "archive": 1.00, "deep": 0.90}

    def test_max_token_budget_larger_than_debugging(self):
        """Research needs more context headroom than debugging (2400)."""
        plan = self._plan()
        assert plan.max_token_budget == 3600
        assert (
            plan.max_token_budget
            > DEBUGGING_SESSION_PACK.aperture_recipe.memory_plan.max_token_budget
        )

    def test_safety_constraint_preserved(self):
        """Identity must outrank archive — carried over from debugging's
        same constraint. Non-negotiable."""
        plan = self._plan()
        assert "identity_must_outrank_archive" in plan.safety_constraints


class TestResearchAssistantIntentGrammar:
    """Empty forbidden_intents_by_mode (EMPTY_CONTRACT handles narrowing);
    forbid PROPOSE_SHARE; CREATE_ARCHIVE_NOTE is documented-only posture."""

    def test_forbidden_intents_by_mode_empty(self):
        """Ratified: do not belt-and-suspenders forbid USE_TOOL in TOOL
        mode at the pack level; EMPTY_CONTRACT already handles this via
        apply_tool_narrowing."""
        g = RESEARCH_ASSISTANT_PACK.intent_grammar
        assert g.forbidden_intents_by_mode == {}

    def test_forbids_propose_share(self):
        """Draft research shouldn't auto-propose cross-domain sharing
        until a review boundary is crossed."""
        g = RESEARCH_ASSISTANT_PACK.intent_grammar
        assert ActionType.PROPOSE_SHARE in g.forbidden_assimilation_outcomes

    def test_does_not_forbid_write_memory(self):
        """Research turns should be able to produce memories."""
        g = RESEARCH_ASSISTANT_PACK.intent_grammar
        assert ActionType.WRITE_MEMORY not in g.forbidden_assimilation_outcomes

    def test_does_not_forbid_create_archive_note(self):
        """CREATE_ARCHIVE_NOTE is ENCOURAGED posture — declarative only
        until Phase 7 dispatcher has real emission rules. Must not be
        in the forbidden set."""
        g = RESEARCH_ASSISTANT_PACK.intent_grammar
        assert (
            ActionType.CREATE_ARCHIVE_NOTE
            not in g.forbidden_assimilation_outcomes
        )


class TestResearchAssistantStabilizationProgram:
    """Ratified: identical to DEBUGGING_SESSION_PACK. Drift thresholds
    are doctrinal (character.py Appendix A), not task-shaped."""

    def test_matches_appendix_a_thresholds(self):
        p = RESEARCH_ASSISTANT_PACK.stabilization_program
        assert p.low_threshold == 0.15
        assert p.high_threshold == 0.35

    def test_high_regime_action_is_defer(self):
        p = RESEARCH_ASSISTANT_PACK.stabilization_program
        assert p.high_regime_action == ActionType.DEFER

    def test_identical_to_debugging_pack(self):
        """Packs may only NARROW doctrine. Changing thresholds without
        a concrete drift-profile argument would widen an Appendix A
        constant."""
        ours = RESEARCH_ASSISTANT_PACK.stabilization_program
        theirs = DEBUGGING_SESSION_PACK.stabilization_program
        assert ours.low_threshold == theirs.low_threshold
        assert ours.high_threshold == theirs.high_threshold
        assert ours.high_regime_action == theirs.high_regime_action


class TestResearchAssistantActionContract:
    """THE load-bearing field: EMPTY_CONTRACT. Retrieval-ready, not
    retrieval-dependent. This test is the structural proof of that
    design stance."""

    def test_action_contract_is_empty_contract(self):
        """The ratified design uses EMPTY_CONTRACT exactly — not an
        equivalent frozenset() construction. Future edits that swap
        these should be deliberate."""
        assert RESEARCH_ASSISTANT_PACK.action_contract is EMPTY_CONTRACT

    def test_allowed_tool_families_empty(self):
        c = RESEARCH_ASSISTANT_PACK.action_contract
        assert c.allowed_tool_families == frozenset()


class TestResearchAssistantEventReflex:
    """Same drift_stabilization as debugging; kernel-level, not pack-specific."""

    def test_reflex_name(self):
        assert RESEARCH_ASSISTANT_PACK.event_reflex.name == "drift_stabilization"

    def test_reflex_forces_defer(self):
        assert (
            RESEARCH_ASSISTANT_PACK.event_reflex.forced_intent
            == ActionType.DEFER
        )

    def test_reflex_trigger_mentions_drift(self):
        trigger = RESEARCH_ASSISTANT_PACK.event_reflex.trigger
        assert "drift_score" in trigger
        assert "away_seed" in trigger


# ---------------------------------------------------------------------------
# Distinctness from DEBUGGING_SESSION_PACK
# ---------------------------------------------------------------------------


class TestDistinctnessFromDebuggingPack:
    """Second-pack composability probe: the two packs are materially
    distinct shapes of the same five-object bundle."""

    def test_names_differ(self):
        assert (
            RESEARCH_ASSISTANT_PACK.name != DEBUGGING_SESSION_PACK.name
        )

    def test_aperture_lanes_differ(self):
        """Archive is the central difference — research privileges
        archive; debugging does not retrieve from it at all."""
        rp = RESEARCH_ASSISTANT_PACK.aperture_recipe.memory_plan
        dp = DEBUGGING_SESSION_PACK.aperture_recipe.memory_plan
        assert rp.retrieve_archive is True and dp.retrieve_archive is False
        assert rp.retrieve_relational is False and dp.retrieve_relational is True

    def test_action_contracts_differ(self):
        """Debugging permits code_exec; research permits nothing yet.
        THIS is the declared-but-absent-capability assertion."""
        assert (
            DEBUGGING_SESSION_PACK.action_contract.allowed_tool_families
            == frozenset({"code_exec"})
        )
        assert (
            RESEARCH_ASSISTANT_PACK.action_contract.allowed_tool_families
            == frozenset()
        )

    def test_token_budgets_differ(self):
        rp = RESEARCH_ASSISTANT_PACK.aperture_recipe.memory_plan
        dp = DEBUGGING_SESSION_PACK.aperture_recipe.memory_plan
        assert rp.max_token_budget != dp.max_token_budget


# ---------------------------------------------------------------------------
# Runner integration — EMPTY_CONTRACT causes clean USE_TOOL downgrade
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
    """Records the tools list (if any) the runner passed."""
    last_tools: Optional[List[Dict[str, Any]]] = None
    call_count: int = 0
    canned_response: str = "ok"

    def complete(self, system_prompt, messages, tools=None):
        from torment_service.agent_loop import LLMResponse
        self.call_count += 1
        self.last_tools = tools
        return LLMResponse(text=self.canned_response)


class TestUseToolUnderEmptyContractDowngrades:
    """The load-bearing live assertion.

    When deliberation produces USE_TOOL but the active pack's
    action_contract is EMPTY_CONTRACT, apply_tool_narrowing must
    downgrade cleanly — either to DEFER (if legal for the mode) or
    to NO_OP (fail-closed terminus). The LLM must not receive a
    tool signature list because no family is approved.
    """

    def test_use_tool_in_tool_mode_downgrades_to_defer(self):
        """Direct unit-level assertion on apply_tool_narrowing behavior
        with the research-assistant pack's action contract."""
        # Seed a USE_TOOL policy decision that has already survived
        # apply_legality and apply_drift_veto.
        from torment_service.action_policy import ActionPolicyDecision

        seeded = ActionPolicyDecision(
            action=ActionDecision(
                action=ActionType.USE_TOOL,
                reason="test-seed",
                requires_execution=True,
            )
        )
        mode_decision = CognitiveModeDecision(
            chosen_mode=CognitiveMode.TOOL,
            reason="test-mode",
        )

        result = apply_tool_narrowing(
            seeded,
            mode_decision,
            RESEARCH_ASSISTANT_PACK.action_contract,
        )

        # TOOL mode permits DEFER → fallback picks DEFER, not NO_OP.
        assert result.action.action == ActionType.DEFER
        assert result.tool_family_narrowed is None
        assert result.fallback_reason == "tool_narrowing_no_permitted_family"

    def test_runner_with_pack_passes_no_tools_to_llm(self):
        """End-to-end: when the research-assistant pack is active and
        the runner takes a turn, the LLM must not see a tool list."""
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            llm_client=ToolCapturingLLM(),
            pack=RESEARCH_ASSISTANT_PACK,
        )

        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            # Execution-shaped input: under debugging pack this would
            # narrow to code_exec and execute. Under research-assistant
            # it must downgrade because EMPTY_CONTRACT.
            observation=Observation(
                text="Calculate the sum of the first 100 primes using python code."
            ),
            step=1,
        )

        # No tool narrowing should have happened.
        assert result.action_policy_decision.tool_family_narrowed is None

        # The effective action is NOT USE_TOOL (it was downgraded).
        assert result.action_policy_decision.action.action != ActionType.USE_TOOL

        # Invariant 2: LLM never received an open menu. With
        # EMPTY_CONTRACT, the LLM either wasn't called at all
        # (DEFER path skips LLM) or was called with tools=None.
        llm = runner.llm_client
        if llm.call_count > 0:
            assert llm.last_tools is None, (
                f"LLM received a tools list of {len(llm.last_tools)} "
                f"under EMPTY_CONTRACT pack — invariant 2 violation."
            )


class TestPackReplacesMemoryPlanOnTurn:
    """When the research-assistant pack is active, the turn's
    memory_plan must be the pack's aperture recipe, not the
    controller's default."""

    def test_memory_plan_matches_pack_aperture(self):
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=FakeFabric(),
            llm_client=ToolCapturingLLM(),
            pack=RESEARCH_ASSISTANT_PACK,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="tell me about the phase 5 architecture"),
            step=1,
        )
        # The memory plan on the turn result is the pack's plan, not
        # whatever controller.build_memory_plan would have produced.
        expected = RESEARCH_ASSISTANT_PACK.aperture_recipe.memory_plan
        assert result.memory_plan is expected
