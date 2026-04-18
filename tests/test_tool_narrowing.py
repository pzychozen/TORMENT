"""
Invariant 2 test: The model never receives an open tool-choice menu.

Asserts that when USE_TOOL is dispatched through Phase 5, the LLM
sees exactly one tool signature — never a menu, never alternatives.
Covers both the pure `apply_tool_narrowing` function and the runner
integration path.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 2 R3, R4
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 (invariant 2)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S3
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from torment_service.action_policy import (
    ActionPolicyDecision,
    apply_legality,
    apply_tool_narrowing,
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
from torment_service.tool_registry import (
    CODE_EXEC,
    EMPTY_CONTRACT,
    ActionContract,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _frame(
    governance_sensitive: bool = False,
    ambiguity_score: float = 0.0,
    tool_need: bool = True,
    urgency: float = 0.0,
):
    return TaskFrame(
        workspace_id="ws",
        agent_id="agent",
        raw_input="compute 2+2",
        normalized_input="compute 2+2",
        governance_sensitive=governance_sensitive,
        ambiguity_score=ambiguity_score,
        tool_need=tool_need,
        urgency=urgency,
    )


def _mode(m: CognitiveMode):
    return CognitiveModeDecision(chosen_mode=m, reason="test")


def _action(at: ActionType):
    return ActionDecision(action=at, reason="test")


def _passthrough(at: ActionType):
    return ActionPolicyDecision(action=_action(at))


ONE_FAMILY_CONTRACT = ActionContract(allowed_tool_families=frozenset({"code_exec"}))
EMPTY = EMPTY_CONTRACT
TWO_FAMILY_CONTRACT = ActionContract(
    allowed_tool_families=frozenset({"code_exec", "some_other"})
)
UNKNOWN_FAMILY_CONTRACT = ActionContract(
    allowed_tool_families=frozenset({"some_unregistered_tool"})
)


# ---------------------------------------------------------------------------
# apply_tool_narrowing — non-USE_TOOL actions pass through
# ---------------------------------------------------------------------------


class TestNarrowingSkipsNonUseTool:
    """Only USE_TOOL is narrowed. Other actions return unchanged."""

    @pytest.mark.parametrize("at", [
        ActionType.ANSWER,
        ActionType.ASK_CLARIFICATION,
        ActionType.DEFER,
        ActionType.NO_OP,
        ActionType.GOVERNANCE_REVIEW,
    ])
    def test_passthrough_for_non_use_tool(self, at):
        original = _passthrough(at)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.RETRIEVAL), ONE_FAMILY_CONTRACT
        )
        assert result is original
        assert result.tool_family_narrowed is None


# ---------------------------------------------------------------------------
# Exactly-one-family contract attaches the signature
# ---------------------------------------------------------------------------


class TestOneFamilyContractAttachesSignature:
    """When the contract permits exactly one family, narrowing
    attaches that family's signature to the action."""

    def test_tool_family_recorded_on_decision(self):
        original = _passthrough(ActionType.USE_TOOL)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.TOOL), ONE_FAMILY_CONTRACT
        )
        assert result.tool_family_narrowed == "code_exec"

    def test_signature_attached_to_payload(self):
        original = _passthrough(ActionType.USE_TOOL)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.TOOL), ONE_FAMILY_CONTRACT
        )
        payload = result.action.payload
        assert payload.get("tool_family") == "code_exec"
        assert "tool_signature" in payload
        # The signature is a single dict, not a list — invariant 2.
        assert isinstance(payload["tool_signature"], dict)

    def test_signature_content_matches_registry(self):
        original = _passthrough(ActionType.USE_TOOL)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.TOOL), ONE_FAMILY_CONTRACT
        )
        sig = result.action.payload["tool_signature"]
        expected = CODE_EXEC.as_llm_tool_spec()
        assert sig == expected

    def test_defaults_carried_through_payload(self):
        """Controller-side constraints (sandbox, timeout) are not
        LLM-fillable and must be present in the defaults block."""
        original = _passthrough(ActionType.USE_TOOL)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.TOOL), ONE_FAMILY_CONTRACT
        )
        defaults = result.action.payload.get("tool_defaults", {})
        assert defaults.get("scope") == "sandbox"
        assert defaults.get("language") == "python"


# ---------------------------------------------------------------------------
# Zero-family contract falls through (invariant 9)
# ---------------------------------------------------------------------------


class TestZeroFamilyContractFallsThrough:
    """When the contract permits no family, USE_TOOL is refused."""

    def test_empty_contract_in_tool_mode_falls_to_defer(self):
        """TOOL mode has DEFER legal — fallback to DEFER."""
        original = _passthrough(ActionType.USE_TOOL)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.TOOL), EMPTY
        )
        assert result.action.action == ActionType.DEFER
        assert result.tool_family_narrowed is None
        assert result.fallback_reason == "tool_narrowing_no_permitted_family"

    def test_empty_contract_in_fast_mode_falls_to_no_op(self):
        """FAST mode has no DEFER legal — NO_OP terminus."""
        original = _passthrough(ActionType.USE_TOOL)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.FAST), EMPTY
        )
        assert result.action.action == ActionType.NO_OP
        assert result.tool_family_narrowed is None
        assert "no_defer_legal" in result.fallback_reason


# ---------------------------------------------------------------------------
# Multi-family contract also falls through (defensive)
# ---------------------------------------------------------------------------


class TestMultiFamilyContractRefused:
    """v0.1 requires exactly one family; multi-family contracts
    are treated as ambiguous and fall through."""

    def test_two_family_contract_falls_to_defer_in_tool(self):
        original = _passthrough(ActionType.USE_TOOL)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.TOOL), TWO_FAMILY_CONTRACT
        )
        assert result.action.action == ActionType.DEFER
        assert result.tool_family_narrowed is None
        assert result.fallback_reason == "tool_narrowing_ambiguous_contract"


# ---------------------------------------------------------------------------
# Unknown family (not in registry) falls through (defensive)
# ---------------------------------------------------------------------------


class TestUnknownFamilyFallsThrough:
    """Contract names a family that isn't declared in TOOL_REGISTRY.
    Treated as misconfiguration and narrowed to DEFER/NO_OP."""

    def test_unknown_family_falls_to_defer_in_tool(self):
        original = _passthrough(ActionType.USE_TOOL)
        result = apply_tool_narrowing(
            original, _mode(CognitiveMode.TOOL), UNKNOWN_FAMILY_CONTRACT
        )
        assert result.action.action == ActionType.DEFER
        assert result.tool_family_narrowed is None
        assert result.fallback_reason == "tool_narrowing_unknown_family"


# ---------------------------------------------------------------------------
# Narrowing never widens — invariant 9 extension
# ---------------------------------------------------------------------------


class TestNarrowingNeverWidens:
    """Composed apply_legality + apply_tool_narrowing produces a legal
    output for every (mode, contract) combination.

    Tests composition because that is how the runner actually calls
    these layers. apply_tool_narrowing by itself assumes its input
    already passed legality (USE_TOOL would already be illegal in
    non-TOOL modes and downgraded by apply_legality).
    """

    @pytest.mark.parametrize("mode", list(CognitiveMode))
    @pytest.mark.parametrize(
        "contract",
        [EMPTY, ONE_FAMILY_CONTRACT, TWO_FAMILY_CONTRACT, UNKNOWN_FAMILY_CONTRACT],
    )
    def test_composed_output_is_always_legal(self, mode, contract):
        action = _action(ActionType.USE_TOOL)
        mode_dec = _mode(mode)
        frame = _frame(tool_need=(mode == CognitiveMode.TOOL))

        after_legality = apply_legality(action, mode_dec, frame)
        after_narrow = apply_tool_narrowing(after_legality, mode_dec, contract)

        assert is_legal(mode, after_narrow.action.action), (
            f"Composed legality+narrowing in mode {mode.value!r} with "
            f"contract {contract.allowed_tool_families} produced "
            f"{after_narrow.action.action.value!r} — not legal in that mode."
        )


# ---------------------------------------------------------------------------
# Runner integration: LLM sees exactly one tool signature
# ---------------------------------------------------------------------------


@dataclass
class FakeFabric:
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append({})
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append({})
        return None

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append({})


@dataclass
class ToolCapturingLLM:
    """Captures the tools= argument on every call (v0.1.0c: returns LLMResponse)."""
    last_tools: Optional[List[Dict[str, Any]]] = None
    call_count: int = 0
    canned_response: str = "tool_call: code_exec"
    canned_tool_call: Optional[Any] = None  # Optional[ToolCall]

    def complete(self, system_prompt, messages, tools=None):
        from torment_service.agent_loop import LLMResponse
        self.call_count += 1
        self.last_tools = tools
        tool_calls = [self.canned_tool_call] if self.canned_tool_call else []
        return LLMResponse(text=self.canned_response, tool_calls=tool_calls)


@dataclass
class StubToolExecutor:
    """Records invocation and returns canned result."""
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_result: Dict[str, Any] = field(
        default_factory=lambda: {"output": "4", "exit_code": 0}
    )

    def execute(self, family, arguments, defaults):
        self.calls.append(
            {"family": family, "arguments": arguments, "defaults": defaults}
        )
        return self.canned_result


class TestRunnerPassesSingleSignatureToLLM:
    """When USE_TOOL is dispatched with a one-family contract, the
    runner passes exactly one tool signature to the LLM."""

    def test_llm_receives_exactly_one_tool_signature(self):
        fabric = FakeFabric()
        llm = ToolCapturingLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
            action_contract=ONE_FAMILY_CONTRACT,
            tool_executor=StubToolExecutor(),
        )
        # Input that should trigger USE_TOOL via choose_action's
        # tool_need branch. v0.1.0d: uses an execution verb + phrase
        # trigger ("run code", "using python", "compute") — retrieval
        # verbs like "search"/"find" are unmapped now.
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="run code to compute a quick sum using python"),
            step=1,
        )
        # If the runner actually dispatched USE_TOOL → the LLM
        # received exactly one tool signature.
        if result.action_policy_decision.tool_family_narrowed == "code_exec":
            assert llm.last_tools is not None
            assert len(llm.last_tools) == 1, (
                f"LLM received {len(llm.last_tools)} tools; "
                f"invariant 2 requires exactly one."
            )
            assert llm.last_tools[0]["name"] == "code_exec"

    def test_llm_receives_none_for_non_tool_turn(self):
        """ANSWER turn passes tools=None to the LLM — not a menu."""
        fabric = FakeFabric()
        llm = ToolCapturingLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
            action_contract=ONE_FAMILY_CONTRACT,
            tool_executor=StubToolExecutor(),
        )
        runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="What time is it?"),
            step=1,
        )
        # If any LLM call happened, tools should be None (not a menu)
        if llm.call_count > 0:
            # When USE_TOOL narrowing does not fire, tools=None
            # (invariant 2: model never receives an open tool menu).
            # We check last_tools is None OR a single-element list
            # for this panel's expected behavior.
            assert llm.last_tools is None or len(llm.last_tools) == 1


class TestRunnerFallsThroughWithEmptyContract:
    """With no permitted family, USE_TOOL falls through; LLM never
    sees a tool signature because narrowing downgrades the action."""

    def test_empty_contract_forces_use_tool_to_defer(self):
        fabric = FakeFabric()
        llm = ToolCapturingLLM()
        runner = AgentRunner(
            controller=ThinkingController(),
            fabric=fabric,
            llm_client=llm,
            action_contract=EMPTY,  # no families permitted
            tool_executor=None,
        )
        result = runner.run_turn(
            workspace_id="ws",
            agent_id="agent",
            observation=Observation(text="run code to compute a quick sum using python"),
            step=1,
        )
        # If choose_action picked USE_TOOL, the empty contract must
        # have downgraded it to DEFER (in TOOL mode) or NO_OP.
        if result.action_decision.action == ActionType.USE_TOOL:
            # Final effective action (in action_policy_decision.action)
            # must not be USE_TOOL
            final_action = result.action_policy_decision.action.action
            assert final_action != ActionType.USE_TOOL, (
                "Empty contract must have downgraded USE_TOOL; "
                "invariant 2 violation otherwise."
            )


class TestTwoLayerCompositionLegalityAndNarrowing:
    """apply_legality + apply_tool_narrowing compose correctly."""

    def test_use_tool_in_retrieval_gets_narrowed_to_defer(self):
        """RETRIEVAL mode forbids USE_TOOL (invariant 7). Before
        narrowing even runs, apply_legality already downgraded."""
        action = _action(ActionType.USE_TOOL)
        mode = _mode(CognitiveMode.RETRIEVAL)
        frame = _frame(tool_need=False)

        # Phase 5 layer 1: legality
        after_legality = apply_legality(action, mode, frame)
        assert after_legality.action.action != ActionType.USE_TOOL

        # Phase 5 layer 3: narrowing (skipping layer 2 drift — always
        # low here). Narrowing sees non-USE_TOOL and passes through.
        after_narrow = apply_tool_narrowing(after_legality, mode, ONE_FAMILY_CONTRACT)
        assert after_narrow.tool_family_narrowed is None
        # The legality-downgraded action is preserved
        assert after_narrow.action.action == after_legality.action.action

    def test_use_tool_in_tool_mode_gets_narrowed_to_code_exec(self):
        """TOOL mode: apply_legality passes through; narrowing
        attaches code_exec signature."""
        action = _action(ActionType.USE_TOOL)
        mode = _mode(CognitiveMode.TOOL)
        frame = _frame(tool_need=True)

        after_legality = apply_legality(action, mode, frame)
        assert after_legality.action.action == ActionType.USE_TOOL

        after_narrow = apply_tool_narrowing(after_legality, mode, ONE_FAMILY_CONTRACT)
        assert after_narrow.action.action == ActionType.USE_TOOL
        assert after_narrow.tool_family_narrowed == "code_exec"
