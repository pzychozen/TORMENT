"""v0.1.0d — tool-intent tuning tests.

Two concerns in one file:

1. Three-bucket routing panel (frame_task + choose_mode):
   Bucket A — explicit execution verbs/phrases → TOOL mode (tool_need=True).
   Bucket B — analytical depth verbs → REFLECTIVE mode (via confidence_need),
             tool_need MUST remain False.
   Bucket C — retrieval verbs → memory/RETRIEVAL intent (v0.1.0e). Tool_need
             MUST remain False; a non-tool retrieval request sets memory_need
             and routes to RETRIEVAL / ANSWER via the existing memory_need path.

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
        """Analytical QUESTIONS (with ?) reach REFLECTIVE via analytical-depth
        + has_question. As of v0.1.0f, NON-question analytical imperatives also
        reach REFLECTIVE through the analytical-depth confidence_need floor
        (>= 0.60) — see TestBucketB_AnalyticalImperativeReflectiveFloor. v0.1.0d's
        guarantee still holds: analytical verbs do not trigger TOOL."""
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
# Bucket B (v0.1.0f) — analytical-depth cues impose a confidence_need floor of
# >= 0.60, so NON-question analytical imperatives route to REFLECTIVE (not FAST)
# via the existing choose_mode branch. tool_need stays False; action stays ANSWER.
# ---------------------------------------------------------------------------

# Clean non-question analytical imperatives (>= 4 words, no "?", and no
# retrieval / tool / governance / identity / live-social / relational confounds),
# so the ONLY escalation signal is the analytical-depth confidence floor.
_ANALYTICAL_IMPERATIVE_QUERIES = [
    "Analyze the tradeoffs in this proposal.",
    "Explain how this module behaves.",
    "Debug the failing branch in this routine.",
    "Inspect the structure of this payload.",
    "Check the consistency of these outputs.",
]


class TestBucketB_AnalyticalImperativeReflectiveFloor:
    """v0.1.0f: analytical-depth cues impose a confidence_need floor of >= 0.60,
    so a NON-question analytical imperative routes to CognitiveMode.REFLECTIVE
    (not FAST) via the existing choose_mode branch — while tool_need stays False
    and the action stays ANSWER. No new frame / plan / trace field, shaper, or
    advisory."""

    @pytest.mark.parametrize("query", _ANALYTICAL_IMPERATIVE_QUERIES)
    def test_analytical_imperative_confidence_floor(self, query: str):
        assert _frame(query).confidence_need >= 0.60, (
            f"{query!r} should floor confidence_need to >= 0.60 (analytical depth)"
        )

    @pytest.mark.parametrize("query", _ANALYTICAL_IMPERATIVE_QUERIES)
    def test_analytical_imperative_routes_to_reflective(self, query: str):
        m = _mode(query)
        assert m == CognitiveMode.REFLECTIVE, (
            f"{query!r} should route to REFLECTIVE (got {m.value!r})"
        )

    @pytest.mark.parametrize("query", _ANALYTICAL_IMPERATIVE_QUERIES)
    def test_analytical_imperative_keeps_tool_need_false(self, query: str):
        assert _frame(query).tool_need is False, (
            f"{query!r} must NOT set tool_need=True (analytical is not tool intent)"
        )

    @pytest.mark.parametrize("query", _ANALYTICAL_IMPERATIVE_QUERIES)
    def test_analytical_imperative_action_is_answer(self, query: str):
        result = _tc.think("ws_test", "agent_test", query)
        assert result.action_decision.action != ActionType.USE_TOOL, (
            f"{query!r} routed to USE_TOOL — analytical intent must stay ANSWER"
        )
        assert result.action_decision.action == ActionType.ANSWER

    def test_execution_phrase_precedence_over_analytical(self):
        # Precedence: an analytical verb + explicit execution phrase still routes
        # TOOL / USE_TOOL (tool_need wins mode and action priority).
        result = _tc.think("ws_test", "agent_test", "Analyze this dataset using python.")
        assert result.task_frame.tool_need is True
        assert result.mode_decision.chosen_mode == CognitiveMode.TOOL
        assert result.action_decision.action == ActionType.USE_TOOL

    def test_retrieval_plus_analytical_overlap_stays_retrieval(self):
        # Overlap precedence: memory_need (retrieval verb) is checked BEFORE the
        # confidence_need REFLECTIVE branch in choose_mode, so a retrieval +
        # analytical prompt stays RETRIEVAL / ANSWER (retrieval-owned routing
        # wins) even though the analytical floor also raised confidence_need.
        result = _tc.think("ws_test", "agent_test", "Read the summary and analyze the tradeoffs.")
        assert result.task_frame.memory_need is True
        assert result.task_frame.tool_need is False
        assert result.task_frame.confidence_need >= 0.60
        assert result.mode_decision.chosen_mode == CognitiveMode.RETRIEVAL
        assert result.action_decision.action == ActionType.ANSWER


# ---------------------------------------------------------------------------
# Bucket C (v0.1.0e) — retrieval verbs express memory/RETRIEVAL intent and
# route to RETRIEVAL / ANSWER via the EXISTING memory_need path (never tool).
# ---------------------------------------------------------------------------

# Clean single-retrieval-verb prompts with NO archive/identity/relational/
# governance/live-social/tool confounds, so the only memory signal is the
# retrieval verb and the only routing consequence is the memory_need path.
_RETRIEVAL_ONLY_QUERIES = [
    "Search the wiki for the onboarding guide.",
    "Find the meeting slot in my calendar.",
    "Fetch the weather outlook for tomorrow.",
    "Read the summary of the quarterly budget.",
    "Open the file about the vacation itinerary.",
    "Scan the list for duplicate entries.",
    "Lookup the phone extension for the front desk.",
]


class TestBucketC_RetrievalRoutesViaMemoryNeed:
    """v0.1.0e: retrieval verbs contribute to frame.memory_need (NOT
    tool_need). A non-tool retrieval request therefore routes to
    CognitiveMode.RETRIEVAL and ActionType.ANSWER through the existing
    memory_need path — no new frame / plan / trace field, shaper, or advisory."""

    @pytest.mark.parametrize("query", _RETRIEVAL_ONLY_QUERIES)
    def test_retrieval_sets_memory_need(self, query: str):
        assert _frame(query).memory_need is True, (
            f"{query!r} should set memory_need=True via RETRIEVAL_HINT_WORDS"
        )

    @pytest.mark.parametrize("query", _RETRIEVAL_ONLY_QUERIES)
    def test_retrieval_keeps_tool_need_false(self, query: str):
        assert _frame(query).tool_need is False, (
            f"{query!r} must NOT set tool_need=True (retrieval is not tool intent)"
        )

    @pytest.mark.parametrize("query", _RETRIEVAL_ONLY_QUERIES)
    def test_retrieval_routes_to_retrieval_mode(self, query: str):
        m = _mode(query)
        assert m == CognitiveMode.RETRIEVAL, (
            f"{query!r} should route to RETRIEVAL (got {m.value!r})"
        )

    @pytest.mark.parametrize("query", _RETRIEVAL_ONLY_QUERIES)
    def test_retrieval_does_not_route_to_use_tool(self, query: str):
        result = _tc.think("ws_test", "agent_test", query)
        assert result.action_decision.action != ActionType.USE_TOOL, (
            f"{query!r} routed to USE_TOOL — retrieval intent must stay ANSWER"
        )
        assert result.action_decision.action == ActionType.ANSWER

    @pytest.mark.parametrize("query", _RETRIEVAL_ONLY_QUERIES)
    def test_retrieval_enables_existing_memoryplan_relational_lane(self, query: str):
        # The existing MemoryPlan retrieval lane is enabled through the existing
        # path: plan.retrieve_relational = memory_need or live_social. Prove the
        # lane is on and its budget/weight are nonzero — no new lane/field added.
        frame = _frame(query)
        mode = _tc.choose_mode(frame)
        plan = _tc.build_memory_plan(frame, mode)
        assert plan.retrieve_relational is True
        assert plan.top_k_by_lane["relational"] > 0
        assert plan.weight_by_lane["relational"] > 0.0

    def test_control_non_retrieval_leaves_relational_lane_off(self):
        # Negative control: a plain statement with no retrieval verb (and no
        # other memory signal) does not set memory_need or enable the relational
        # lane — so the activations above are attributable to the retrieval-verb
        # memory_need path, not an always-on default.
        frame = _frame("The sky is clear this afternoon.")
        assert frame.memory_need is False
        assert frame.tool_need is False
        mode = _tc.choose_mode(frame)
        plan = _tc.build_memory_plan(frame, mode)
        assert plan.retrieve_relational is False
        assert plan.top_k_by_lane["relational"] == 0


# ---------------------------------------------------------------------------
# Recall cue (v0.1.0g) — explicit "recall" is a memory_need cue: a recall-only
# prompt routes RETRIEVAL / ANSWER via the existing memory_need path (never tool).
# ---------------------------------------------------------------------------

_RECALL_ONLY_QUERIES = [
    "Recall the plan for tomorrow.",
    "Recall the address of the venue.",
    "Recall the details from the briefing.",
]


class TestRecallCueRoutesViaMemoryNeed:
    """v0.1.0g: an explicit "recall" cue contributes to frame.memory_need (NOT
    tool_need), so a recall-only request routes to CognitiveMode.RETRIEVAL and
    ActionType.ANSWER through the existing memory_need path and enables the
    existing relational MemoryPlan lane. No new frame / plan / trace field."""

    @pytest.mark.parametrize("query", _RECALL_ONLY_QUERIES)
    def test_recall_sets_memory_need(self, query: str):
        assert _frame(query).memory_need is True, (
            f"{query!r} should set memory_need=True via the 'recall' cue"
        )

    @pytest.mark.parametrize("query", _RECALL_ONLY_QUERIES)
    def test_recall_keeps_tool_need_false(self, query: str):
        assert _frame(query).tool_need is False, (
            f"{query!r} must NOT set tool_need=True (recall is not tool intent)"
        )

    @pytest.mark.parametrize("query", _RECALL_ONLY_QUERIES)
    def test_recall_routes_to_retrieval_answer(self, query: str):
        result = _tc.think("ws_test", "agent_test", query)
        assert result.mode_decision.chosen_mode == CognitiveMode.RETRIEVAL
        assert result.action_decision.action == ActionType.ANSWER

    @pytest.mark.parametrize("query", _RECALL_ONLY_QUERIES)
    def test_recall_enables_existing_relational_lane(self, query: str):
        # Existing MemoryPlan relational lane enabled through the existing path:
        # plan.retrieve_relational = memory_need or live_social. No new lane/field.
        frame = _frame(query)
        mode = _tc.choose_mode(frame)
        plan = _tc.build_memory_plan(frame, mode)
        assert plan.retrieve_relational is True
        assert plan.top_k_by_lane["relational"] > 0
        assert plan.weight_by_lane["relational"] > 0.0

    def test_recall_with_execution_phrase_still_tool(self):
        # Precedence: recall + explicit execution phrase still routes TOOL / USE_TOOL.
        result = _tc.think("ws_test", "agent_test", "Recall the figures and compute them using python.")
        assert result.task_frame.tool_need is True
        assert result.mode_decision.chosen_mode == CognitiveMode.TOOL
        assert result.action_decision.action == ActionType.USE_TOOL

    def test_recall_with_analytical_phrase_stays_retrieval(self):
        # Precedence: recall + analytical stays RETRIEVAL / ANSWER (memory_need is
        # checked before the confidence_need REFLECTIVE branch).
        result = _tc.think("ws_test", "agent_test", "Recall the design and analyze the tradeoffs.")
        assert result.task_frame.memory_need is True
        assert result.task_frame.tool_need is False
        assert result.task_frame.confidence_need >= 0.60
        assert result.mode_decision.chosen_mode == CognitiveMode.RETRIEVAL
        assert result.action_decision.action == ActionType.ANSWER


# ---------------------------------------------------------------------------
# Memory/retrieval cue WORD-BOUNDARY hardening (v0.1.0h) — real cues still route
# RETRIEVAL / ANSWER; accidental substrings (bread->read, pastel->past,
# scanline->scan, opening->open) do NOT set memory_need and stay FAST / ANSWER.
# ---------------------------------------------------------------------------

# Prompts whose ONLY apparent cue is an accidental substring of a real cue word;
# each has no other memory/tool/analytical signal, so it must stay FAST / ANSWER.
_SUBSTRING_NON_CUE_QUERIES = [
    "The bread is fresh today.",         # 'bread' contains 'read'
    "The pastel palette is pleasant.",   # 'pastel' contains 'past'
    "The scanline flickers on screen.",  # 'scanline' contains 'scan'
    "The opening ceremony was lovely.",  # 'opening' contains 'open'
]


class TestMemoryCueWordBoundary:
    """v0.1.0h: memory/retrieval cues match at WORD boundaries. Real cue words
    still route through memory_need -> RETRIEVAL / ANSWER (and enable the
    existing relational lane); accidental substrings do NOT set memory_need and
    stay FAST / ANSWER. tool_need and the mode lattice are unchanged; no new
    field / shaper / advisory / consumer."""

    # -- real cues still route retrieval --
    @pytest.mark.parametrize("query", _RETRIEVAL_ONLY_QUERIES)
    def test_real_retrieval_cue_still_routes_retrieval(self, query: str):
        f = _frame(query)
        assert f.memory_need is True
        assert f.tool_need is False
        assert _mode(query) == CognitiveMode.RETRIEVAL

    @pytest.mark.parametrize("query", _RECALL_ONLY_QUERIES)
    def test_real_recall_cue_still_routes_retrieval(self, query: str):
        f = _frame(query)
        assert f.memory_need is True
        assert f.tool_need is False
        result = _tc.think("ws_test", "agent_test", query)
        assert result.mode_decision.chosen_mode == CognitiveMode.RETRIEVAL
        assert result.action_decision.action == ActionType.ANSWER

    def test_real_memory_cue_enables_relational_lane(self):
        frame = _frame("Recall the plan for tomorrow.")
        plan = _tc.build_memory_plan(frame, _tc.choose_mode(frame))
        assert plan.retrieve_relational is True
        assert plan.top_k_by_lane["relational"] > 0
        assert plan.weight_by_lane["relational"] > 0.0

    def test_execution_phrase_still_wins(self):
        result = _tc.think("ws_test", "agent_test", "Recall the figures and compute them using python.")
        assert result.task_frame.tool_need is True
        assert result.mode_decision.chosen_mode == CognitiveMode.TOOL
        assert result.action_decision.action == ActionType.USE_TOOL

    # -- accidental substrings do NOT trigger memory intent --
    @pytest.mark.parametrize("query", _SUBSTRING_NON_CUE_QUERIES)
    def test_substring_does_not_set_memory_need(self, query: str):
        f = _frame(query)
        assert f.memory_need is False, (
            f"{query!r} must not set memory_need via an accidental cue substring"
        )
        assert f.tool_need is False

    @pytest.mark.parametrize("query", _SUBSTRING_NON_CUE_QUERIES)
    def test_substring_stays_fast_answer(self, query: str):
        result = _tc.think("ws_test", "agent_test", query)
        assert result.mode_decision.chosen_mode == CognitiveMode.FAST
        assert result.action_decision.action == ActionType.ANSWER

    def test_no_new_advisory_or_shaper_surface(self):
        # Boundary-hardening adds no field / advisory / shaper / consumer.
        f = _frame("Recall the plan for tomorrow.")
        for name in ("memory_plan_sufficiency_advisory", "memory_plan_quality",
                     "memory_plan_shaping_posture"):
            assert not hasattr(f, name)


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
