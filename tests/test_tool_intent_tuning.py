"""v0.1.0d — tool-intent tuning tests.

Two concerns in one file:

1. Three-bucket routing panel (frame_task + choose_mode):
   Bucket A — explicit execution verbs/phrases → TOOL mode (tool_need=True).
   Bucket B — analytical depth verbs → REFLECTIVE mode (via confidence_need),
             tool_need MUST remain False.
   Bucket C — retrieval verbs → unmapped in v0.1. Tool_need MUST remain False;
             mode may be anything non-TOOL (FAST/RETRIEVAL acceptable — the
             contract is "no bogus TOOL routing").

2. apply_pack_intent_tightening unit tests:
   - No-op paths (pack=None / empty grammar / action not forbidden)
   - Fallback chain: governance → clarify → defer → answer → no_op
   - Invariant 6 preserved (only narrows; never widens)

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 5 (behavior packs, grammar)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 invariants 6, 9
    - thinking_controller.TOOL_HINT_WORDS / TOOL_HINT_PHRASES /
      ANALYTICAL_DEPTH_HINT_WORDS / RETRIEVAL_HINT_WORDS
"""
from __future__ import annotations

import pytest

from torment_service.action_policy import (
    ActionPolicyDecision,
    apply_pack_intent_tightening,
)
from torment_service.behavior_packs import (
    ApertureRecipe,
    BehaviorPack,
    EventReflex,
    IntentGrammar,
    StabilizationProgram,
)
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveMode,
    CognitiveModeDecision,
    MemoryPlan,
    TaskFrame,
)
from torment_service.tool_registry import ActionContract


_tc = ThinkingController()


def _frame(query: str) -> TaskFrame:
    return _tc.frame_task("ws_test", "agent_test", query)


def _mode(query: str) -> CognitiveMode:
    return _tc.choose_mode(_frame(query)).chosen_mode


# ---------------------------------------------------------------------------
# Bucket A — execution verbs & phrases should route to TOOL mode
# ---------------------------------------------------------------------------


class TestBucketA_ExecutionTriggersTool:
    """Execution verbs and phrases must set tool_need=True and route to TOOL."""

    @pytest.mark.parametrize("query", [
        "Calculate the sum of the first 100 primes using code.",
        "Compute this in Python.",
        "Run Python code to solve this.",
        "Execute a short script to verify this.",
        "Write and run Python to find the answer.",
        "Evaluate this expression programmatically.",
    ])
    def test_execution_triggers_tool_need(self, query: str):
        frame = _frame(query)
        assert frame.tool_need is True, (
            f"{query!r} should set tool_need=True with v0.1.0d TOOL_HINT_WORDS "
            f"/ TOOL_HINT_PHRASES; tool_need={frame.tool_need}"
        )

    @pytest.mark.parametrize("query", [
        "Calculate the sum of the first 100 primes using code.",
        "Compute this in Python.",
        "Run Python code to solve this.",
        "Execute a short script to verify this.",
        "Write and run Python to find the answer.",
        "Evaluate this expression programmatically.",
    ])
    def test_execution_routes_to_tool_mode(self, query: str):
        mode = _mode(query)
        assert mode == CognitiveMode.TOOL, (
            f"{query!r} should route to TOOL mode (got {mode.value!r})"
        )


# ---------------------------------------------------------------------------
# Bucket B — analytical depth must NOT trigger tool_need, routes to REFLECTIVE
# ---------------------------------------------------------------------------


class TestBucketB_AnalyticalNotTool:
    """Analytical verbs (analyze/explain/debug/trace/inspect/check) must
    NOT raise tool_need. They live in ANALYTICAL_DEPTH_HINT_WORDS and
    should push confidence_need toward REFLECTIVE."""

    @pytest.mark.parametrize("query", [
        "Analyze why this recursive pattern keeps appearing in the code.",
        "Explain what this code is doing conceptually.",
        "Why might this bug be happening?",
        "Debug the logic in this function.",
        "Trace through this algorithm mentally.",
    ])
    def test_analytical_does_not_trigger_tool_need(self, query: str):
        frame = _frame(query)
        assert frame.tool_need is False, (
            f"{query!r} must NOT set tool_need=True under v0.1.0d; "
            f"analytical verbs are not execution triggers."
        )

    @pytest.mark.parametrize("query", [
        "Analyze why this recursive pattern keeps appearing in the code.",
        "Explain what this code is doing conceptually.",
        "Why might this bug be happening?",
        "Debug the logic in this function.",
        "Trace through this algorithm mentally.",
    ])
    def test_analytical_does_not_route_to_tool_mode(self, query: str):
        mode = _mode(query)
        assert mode != CognitiveMode.TOOL, (
            f"{query!r} routed to TOOL — analytical queries should not. "
            f"got {mode.value!r}"
        )

    def test_analytical_question_reaches_reflective(self):
        """Analytical QUESTIONS (with ?) should reach REFLECTIVE via
        analytical-depth + has_question combining into
        confidence_need >= 0.60. Non-question analytical statements
        may stay in FAST — that's §2A / choose_mode behavior, not a
        v0.1.0d contract. v0.1.0d's guarantee is: analytical verbs
        do not trigger TOOL."""
        mode = _mode("Why does this recursive pattern keep reappearing?")
        assert mode == CognitiveMode.REFLECTIVE, (
            f"expected REFLECTIVE, got {mode.value!r}"
        )


# ---------------------------------------------------------------------------
# Bucket C — retrieval verbs are unmapped in v0.1; must NOT trigger tool_need
# ---------------------------------------------------------------------------


class TestBucketC_RetrievalUnmapped:
    """Retrieval verbs (search/find/lookup/fetch/read/open/scan) are
    declared in RETRIEVAL_HINT_WORDS but NOT mapped to any tool family
    in v0.1. They must not cause TOOL routing. When a retrieval tool
    family is added post-v0.1, this contract will change."""

    @pytest.mark.parametrize("query", [
        "Find the relevant documentation for phase 5 narrowing.",
        "Search the docs for gravity correction.",
        "Look up the API reference for ingest.",
        "Read the spec on drift classification.",
    ])
    def test_retrieval_does_not_trigger_tool_need(self, query: str):
        frame = _frame(query)
        assert frame.tool_need is False, (
            f"{query!r} must NOT set tool_need=True; retrieval verbs are "
            f"unmapped in v0.1 (no retrieval tool family exists)."
        )

    @pytest.mark.parametrize("query", [
        "Find the relevant documentation for phase 5 narrowing.",
        "Search the docs for gravity correction.",
        "Look up the API reference for ingest.",
        "Read the spec on drift classification.",
    ])
    def test_retrieval_does_not_route_to_tool_mode(self, query: str):
        mode = _mode(query)
        assert mode != CognitiveMode.TOOL, (
            f"{query!r} routed to TOOL — retrieval verbs should not, "
            f"they're unmapped. got {mode.value!r}"
        )


# ---------------------------------------------------------------------------
# Phrase overrides — "using python" etc. should fire tool_need even if
# the sentence also contains analytical/retrieval verbs.
# ---------------------------------------------------------------------------


class TestPhraseOverrides:
    """TOOL_HINT_PHRASES matches as strongly as a word in TOOL_HINT_WORDS
    and deliberately overrides ambiguous surrounding context."""

    def test_analyze_with_python_phrase_triggers_tool(self):
        """'analyze' alone → REFLECTIVE. But 'analyze ... using python'
        adds an explicit execution phrase, which should flip tool_need on."""
        frame = _frame("Analyze the primes distribution using python.")
        assert frame.tool_need is True, (
            "'using python' phrase should force tool_need=True even alongside "
            "analytical verbs"
        )

    def test_find_with_run_code_phrase_triggers_tool(self):
        """'find' alone → retrieval (unmapped). But with 'run code', the
        phrase trigger fires."""
        frame = _frame("Find the answer; run code to verify it.")
        assert frame.tool_need is True


# ---------------------------------------------------------------------------
# apply_pack_intent_tightening unit tests
# ---------------------------------------------------------------------------


def _base_decision(action_type: ActionType) -> ActionPolicyDecision:
    """Build a minimal ActionPolicyDecision wrapping the given action."""
    return ActionPolicyDecision(
        action=ActionDecision(
            action=action_type,
            reason="test-seed",
            requires_execution=action_type
            in {ActionType.USE_TOOL, ActionType.ANSWER, ActionType.GOVERNANCE_REVIEW},
        )
    )


def _mode_decision(mode: CognitiveMode) -> CognitiveModeDecision:
    return CognitiveModeDecision(chosen_mode=mode, reason="test-mode")


def _tframe(
    *,
    governance_sensitive: bool = False,
    ambiguity_score: float = 0.0,
    urgency: float = 0.0,
) -> TaskFrame:
    return TaskFrame(
        workspace_id="ws",
        agent_id="agent",
        raw_input="test",
        normalized_input="test",
        governance_sensitive=governance_sensitive,
        ambiguity_score=ambiguity_score,
        urgency=urgency,
    )


def _pack_forbidding(
    mode: CognitiveMode,
    forbidden: set,
    name: str = "test_pack",
) -> BehaviorPack:
    """Build a BehaviorPack that forbids `forbidden` intents in `mode`.
    All other fields are permissive defaults sufficient for Phase 5 tests."""
    return BehaviorPack(
        name=name,
        description="test pack",
        aperture_recipe=ApertureRecipe(name="t", memory_plan=MemoryPlan()),
        intent_grammar=IntentGrammar(
            forbidden_intents_by_mode={mode: frozenset(forbidden)},
        ),
        stabilization_program=StabilizationProgram(),
        action_contract=ActionContract(allowed_tool_families=frozenset({"code_exec"})),
        event_reflex=EventReflex(
            name="t-reflex", trigger="never", description=""
        ),
    )


class TestPackTightening_NoOpPaths:
    def test_none_pack_is_passthrough(self):
        original = _base_decision(ActionType.USE_TOOL)
        result = apply_pack_intent_tightening(
            original,
            _mode_decision(CognitiveMode.TOOL),
            None,  # no pack
            _tframe(),
        )
        assert result is original

    def test_empty_grammar_is_passthrough(self):
        pack = _pack_forbidding(CognitiveMode.TOOL, set())  # empty forbidden set
        original = _base_decision(ActionType.USE_TOOL)
        result = apply_pack_intent_tightening(
            original,
            _mode_decision(CognitiveMode.TOOL),
            pack,
            _tframe(),
        )
        assert result is original

    def test_action_not_in_forbidden_set_is_passthrough(self):
        pack = _pack_forbidding(CognitiveMode.TOOL, {ActionType.USE_TOOL})
        original = _base_decision(ActionType.ASK_CLARIFICATION)
        result = apply_pack_intent_tightening(
            original,
            _mode_decision(CognitiveMode.TOOL),
            pack,
            _tframe(),
        )
        # USE_TOOL is forbidden but we're asking for clarification; passthrough.
        assert result is original

    def test_forbidden_mode_mismatch_is_passthrough(self):
        # Pack forbids USE_TOOL in TOOL mode, but current mode is RETRIEVAL.
        pack = _pack_forbidding(CognitiveMode.TOOL, {ActionType.USE_TOOL})
        original = _base_decision(ActionType.USE_TOOL)
        result = apply_pack_intent_tightening(
            original,
            _mode_decision(CognitiveMode.RETRIEVAL),
            pack,
            _tframe(),
        )
        assert result is original


class TestPackTightening_FallbackChain:
    """The fallback chain narrows (legal_set − forbidden_set) via
    governance → clarify → defer → answer → no_op."""

    def test_governance_sensitive_routes_to_governance_review_if_legal(self):
        # In IDENTITY_SENSITIVE mode, ANSWER is legal AND GOVERNANCE_REVIEW
        # is legal. Forbid ANSWER under a governance-sensitive frame, expect
        # GOVERNANCE_REVIEW.
        pack = _pack_forbidding(
            CognitiveMode.IDENTITY_SENSITIVE, {ActionType.ANSWER}
        )
        result = apply_pack_intent_tightening(
            _base_decision(ActionType.ANSWER),
            _mode_decision(CognitiveMode.IDENTITY_SENSITIVE),
            pack,
            _tframe(governance_sensitive=True),
        )
        assert result.action.action == ActionType.GOVERNANCE_REVIEW
        assert result.fallback_reason == "pack_intent_tightening_governance"
        assert result.action.payload["pack"] == "test_pack"
        assert result.action.payload["pre_tighten_action"] == "answer"

    def test_high_ambiguity_routes_to_ask_clarification_if_legal(self):
        # REFLECTIVE mode: ANSWER + ASK_CLARIFICATION + DEFER all legal.
        # Forbid ANSWER, no governance, high ambiguity → ASK_CLARIFICATION.
        pack = _pack_forbidding(
            CognitiveMode.REFLECTIVE, {ActionType.ANSWER}
        )
        result = apply_pack_intent_tightening(
            _base_decision(ActionType.ANSWER),
            _mode_decision(CognitiveMode.REFLECTIVE),
            pack,
            _tframe(ambiguity_score=0.9),
        )
        assert result.action.action == ActionType.ASK_CLARIFICATION
        assert result.fallback_reason == "pack_intent_tightening_ambiguity"

    def test_defer_selected_when_neither_governance_nor_ambiguity(self):
        # TOOL mode: forbid USE_TOOL; DEFER remains in pack_legal_set.
        pack = _pack_forbidding(CognitiveMode.TOOL, {ActionType.USE_TOOL})
        result = apply_pack_intent_tightening(
            _base_decision(ActionType.USE_TOOL),
            _mode_decision(CognitiveMode.TOOL),
            pack,
            _tframe(),  # ambiguity low, not governance-sensitive
        )
        assert result.action.action == ActionType.DEFER
        assert result.fallback_reason == "pack_intent_tightening_defer"

    def test_answer_fallback_when_defer_not_legal(self):
        # FAST mode: only ANSWER + NO_OP legal. Forbidding NO_OP leaves
        # ANSWER as the only narrower option. (Artificial but validates
        # the chain step.)
        pack = _pack_forbidding(CognitiveMode.FAST, {ActionType.NO_OP})
        result = apply_pack_intent_tightening(
            _base_decision(ActionType.NO_OP),
            _mode_decision(CognitiveMode.FAST),
            pack,
            _tframe(),
        )
        assert result.action.action == ActionType.ANSWER
        assert result.fallback_reason == "pack_intent_tightening_answer"

    def test_no_op_terminus_when_no_narrower_legal(self):
        # Forbid ALL legal intents for FAST (ANSWER + NO_OP) → no_op
        # fail-closed. Seed with ANSWER; pack forbids it along with NO_OP.
        pack = _pack_forbidding(
            CognitiveMode.FAST, {ActionType.ANSWER, ActionType.NO_OP}
        )
        result = apply_pack_intent_tightening(
            _base_decision(ActionType.ANSWER),
            _mode_decision(CognitiveMode.FAST),
            pack,
            _tframe(),
        )
        assert result.action.action == ActionType.NO_OP
        assert result.fallback_reason == "pack_intent_tightening_no_op_failclosed"


class TestPackTightening_InvariantPreservation:
    """Invariant 6: pack tightening narrows but never widens. The
    fallback chain's output must be a member of the pre-pack legal
    set for the mode (minus pack-forbidden)."""

    def test_fallback_respects_base_legality_minus_forbidden(self):
        # RETRIEVAL legal set is {ANSWER, ASK_CLARIFICATION, DEFER, NO_OP}.
        # Forbid ANSWER + ASK_CLARIFICATION + DEFER → only NO_OP remains.
        pack = _pack_forbidding(
            CognitiveMode.RETRIEVAL,
            {ActionType.ANSWER, ActionType.ASK_CLARIFICATION, ActionType.DEFER},
        )
        result = apply_pack_intent_tightening(
            _base_decision(ActionType.ANSWER),
            _mode_decision(CognitiveMode.RETRIEVAL),
            pack,
            _tframe(governance_sensitive=True),  # governance path offered
        )
        # GOVERNANCE_REVIEW is NOT in RETRIEVAL legal set → governance
        # path is NOT selected. Fallback must terminate in NO_OP.
        assert result.action.action == ActionType.NO_OP
