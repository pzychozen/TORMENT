# torment_service/behavior_packs.py
"""
TORMENT agent behavior packs.

A behavior pack bundles five first-class objects under a named
identity. The runner treats the pack as the source of truth for
context-specific behavior tightenings at each phase of the 8-phase
loop.

Per doctrine Part 5, a pack is:

    1. Aperture recipe — named MemoryPlan profile (Phase 3 override)
    2. Intent grammar — narrowing of Mode→legal-intents table
       + forbidden assimilation outcomes (Phase 4 / Phase 7 shaping)
    3. Stabilization program — drift thresholds + high-regime action
       (Phase 5 / Phase 8 tuning)
    4. Action contract — approved tool families (Phase 5 narrowing)
    5. Event reflex — non-LLM trigger rule declaration

v0.1 scope (S4):
    - Five first-class dataclass types.
    - One concrete pack: DEBUGGING_SESSION_PACK, instantiated
      directly in this module.
    - No registry, no file-format, no overlays. Those are v0.2.

Composition boundary (doctrine Part 5):
    - One primary pack active at a time.
    - Narrow overlays may extend the action contract by one family,
      tighten the intent grammar, or add a reflex rule. Overlays
      may never widen anything. v0.1/S4 does not implement overlays;
      composition rules are enforced by the runner holding exactly
      one pack at a time.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 5 (behavior packs)
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 (invariants 4, 9)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S4
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet

from .thinking_models import ActionType, CognitiveMode, MemoryPlan
from .tool_registry import ActionContract


# ---------------------------------------------------------------------------
# The five first-class pack objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ApertureRecipe:
    """Named MemoryPlan profile for a class of situations.

    The recipe's MemoryPlan replaces the controller's default
    `build_memory_plan` output when a pack is active. The pack
    declares what retrieval shaping this class of work wants;
    mode-specific defaults from `build_memory_plan` are overridden
    wholesale. (S4 explicit design: pack owns aperture. S4+ may
    introduce merge rules if packs need mode-specific behavior.)
    """
    name: str
    memory_plan: MemoryPlan


@dataclass(frozen=True)
class IntentGrammar:
    """Narrowing of the doctrinal Mode→legal-intents table.

    A pack's grammar may only TIGHTEN legality — it can forbid
    intents the base table permits, but cannot admit intents the
    base table forbids. This preserves doctrine invariant 6
    (governance narrows never widens) at the pack layer.

    Fields:
        forbidden_intents_by_mode: per-mode set of primary intents
            that THIS pack additionally forbids (on top of the base
            MODE_LEGAL_INTENTS table). Applied at Phase 5 as a
            layer on top of `apply_legality`.
        forbidden_assimilation_outcomes: assimilation-outcome
            ActionTypes (WRITE_MEMORY, PROPOSE_SHARE,
            CREATE_ARCHIVE_NOTE) that this pack forbids at Phase 7
            regardless of kernel/policy signal. Consumed by the
            Phase 7 assimilation dispatcher when concrete emission
            rules land. v0.1/M1 stub returns [] so this set is
            declarative for now.

    v0.1: both fields may be empty; the debugging_session pack uses
    only `forbidden_assimilation_outcomes` (forbids PROPOSE_SHARE).
    """
    forbidden_intents_by_mode: Dict[CognitiveMode, FrozenSet[ActionType]] = field(
        default_factory=dict
    )
    forbidden_assimilation_outcomes: FrozenSet[ActionType] = frozenset()


@dataclass(frozen=True)
class StabilizationProgram:
    """Per-pack drift thresholds and high-regime action.

    Overrides the runner's default `drift_high_threshold` when a
    pack is active. Also declares what action to force when drift
    enters the high regime.

    Fields:
        low_threshold: boundary below which drift shapes aperture
            only (doctrine Part 4 low regime). v0.1 is informational
            since the moderate-regime intent promotion is deferred.
        high_threshold: boundary at and above which the drift veto
            fires at Phase 5 (doctrine Part 4 high regime). Reused
            by Phase 8 gravity correction.
        high_regime_action: the primary intent the drift veto
            forces when the high regime triggers. v0.1 supports
            DEFER (default — stabilizing) and NO_OP (fail-closed
            terminus when DEFER is not legal for the mode).
    """
    low_threshold: float = 0.15
    high_threshold: float = 0.35
    high_regime_action: ActionType = ActionType.DEFER


@dataclass(frozen=True)
class EventReflex:
    """Non-LLM trigger rule declaration.

    Describes when this pack wants a reflex turn fired. v0.1 stores
    this declaratively; the live reflex dispatcher (v0.1.0a fabric
    hookup) will read declared reflexes and call
    `AgentRunner.enter_reflex` when the trigger condition is met.

    Fields:
        name: identifier for this reflex within the pack.
        trigger: human-readable trigger description. v0.1: not
            parsed at runtime. Post-slice: a structured predicate
            tree or DSL.
        forced_intent: the ActionType the reflex turn should
            produce. Typically DEFER for stabilization reflexes.
        description: human text explaining the reflex's purpose.
    """
    name: str
    trigger: str
    forced_intent: ActionType = ActionType.DEFER
    description: str = ""


@dataclass(frozen=True)
class BehaviorPack:
    """A named bundle of five first-class objects declaring a
    class of agent behavior.

    Instantiated directly in code for v0.1 (no registry). The
    runner accepts a pack via its `pack` constructor parameter;
    pack-derived settings override the runner's explicit parameter
    defaults for action_contract, drift_high_threshold, and the
    aperture memory plan.
    """
    name: str
    description: str
    aperture_recipe: ApertureRecipe
    intent_grammar: IntentGrammar
    stabilization_program: StabilizationProgram
    action_contract: ActionContract
    event_reflex: EventReflex


# ---------------------------------------------------------------------------
# v0.1 pack: debugging-session
# ---------------------------------------------------------------------------
#
# The first concrete v0.1 pack. Chosen per the ratified slice plan
# because it naturally exercises all five objects:
#
#   - Aperture recipe: analytical bias (core + relational + deep).
#   - Intent grammar: forbid PROPOSE_SHARE (debug state should not
#     cross domains automatically).
#   - Stabilization program: standard Appendix A thresholds; force
#     DEFER in high regime (debugging is already self-correcting;
#     stacking self-correct is doctrinally pointless).
#   - Action contract: code_exec only; nothing else approved.
#   - Event reflex: drift-threshold stabilization.
#
# Post-slice increments (v0.1.1+) will add a second pack (e.g.
# companion, research-assistant) to exercise the composition boundary.


_DEBUGGING_APERTURE_MEMORY_PLAN = MemoryPlan(
    retrieve_core=True,
    retrieve_relational=True,
    retrieve_archive=False,
    retrieve_deep=True,
    retrieve_collective=False,
    retrieve_character_state=True,
    retrieve_srg_state=False,
    top_k_by_lane={
        "core": 8,
        "relational": 4,
        "deep": 3,
    },
    weight_by_lane={
        "core": 1.0,
        "relational": 0.85,
        "deep": 0.60,
    },
    max_token_budget=2400,
    safety_constraints=["identity_must_outrank_archive"],
)


DEBUGGING_SESSION_PACK = BehaviorPack(
    name="debugging_session",
    description=(
        "Analytical debugging context. Emphasizes core + relational "
        "+ deep retrieval. Forbids cross-domain sharing of debug "
        "state (no PROPOSE_SHARE). High-drift turns force DEFER; "
        "code_exec is the single approved external action family."
    ),
    aperture_recipe=ApertureRecipe(
        name="debugging",
        memory_plan=_DEBUGGING_APERTURE_MEMORY_PLAN,
    ),
    intent_grammar=IntentGrammar(
        forbidden_intents_by_mode={},
        forbidden_assimilation_outcomes=frozenset({ActionType.PROPOSE_SHARE}),
    ),
    stabilization_program=StabilizationProgram(
        low_threshold=0.15,
        high_threshold=0.35,
        high_regime_action=ActionType.DEFER,
    ),
    action_contract=ActionContract(
        allowed_tool_families=frozenset({"code_exec"}),
    ),
    event_reflex=EventReflex(
        name="drift_stabilization",
        trigger="drift_score >= high_threshold and direction == away_seed",
        forced_intent=ActionType.DEFER,
        description=(
            "When drift crosses the high threshold in the away-seed "
            "direction, fire a no-LLM stabilization turn that forces "
            "DEFER via the Phase 5 drift veto and runs "
            "gravity_correction at Phase 8. Exercises invariant 5 "
            "(reflexes run without LLM) when combined with S5."
        ),
    ),
)
