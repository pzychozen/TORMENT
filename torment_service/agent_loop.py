# torment_service/agent_loop.py
"""
TORMENT agent outer-loop runtime.

Builds the outer agent turn loop on top of the inner deliberation
scaffold provided by `thinking_controller`. In v0.1, the runner
proves the doctrine under real code; it is not a shippable agent.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md

v0.1 incremental scope:
    M1 (this commit): Phase 7 assimilation-outcome dispatcher scaffold.
                      Provides a well-defined place for the outcomes
                      (PROPOSE_SHARE, CREATE_ARCHIVE_NOTE, WRITE_MEMORY)
                      to be emitted by the controller/kernel at Phase 7,
                      now that the invalid Phase-4 emission has been
                      removed from `choose_action`.
    M2:               Mode-legality enforcement + fallback chain
                      (`action_policy.py`).
    S1:               Full `run_turn` orchestrator wiring phases 1-8.
    S2-S5:            Drift veto, tool gate, behavior pack, reflex.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveModeDecision,
    MemoryPlan,
    TaskFrame,
)


@dataclass
class TurnContext:
    """Opaque carrier for turn-level state read by Phase 7 outcome
    dispatch.

    Populated incrementally by the runner as it progresses through
    phases 1-6. Fields here are the minimum needed for the M1
    assimilation-outcome dispatcher scaffold; additional fields will
    be added as later slice components (S1 runner, S2 drift veto,
    S3 tool gate, S4 behavior pack, S5 reflex) land.
    """
    workspace_id: str
    agent_id: str

    # Populated during Phases 2-4 (inner deliberation, via
    # `thinking_controller.deliberate_only()` once S1 lands).
    task_frame: Optional[TaskFrame] = None
    mode_decision: Optional[CognitiveModeDecision] = None
    memory_plan: Optional[MemoryPlan] = None
    action_decision: Optional[ActionDecision] = None

    # Populated during Phase 6 (Execute).
    response_text: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None

    # Open bag for per-turn observability and v0.1.x extensions.
    metadata: Dict[str, Any] = field(default_factory=dict)


def assimilation_outcomes(ctx: TurnContext) -> List[ActionType]:
    """Emit Phase 7 assimilation outcomes based on controller-side
    turn state.

    Doctrine contract (Part 3 of TORMENT_AGENT_DOCTRINE_v0.1.md):
        `WRITE_MEMORY`, `PROPOSE_SHARE`, and `CREATE_ARCHIVE_NOTE`
        are controller/kernel/policy-decided, never LLM-chosen.
        They are assimilation outcomes, emitted at Phase 7 based on
        turn-result state and controller-side signals, never on text
        hints from user input.

    v0.1 scope (M1): skeleton only — returns an empty list.

    The function exists now so that:
        1. M1 removes the invalid Phase-4 emission of these outcomes
           from `choose_action`.
        2. Later migrations have a well-defined, named insertion point
           for emission rules driven by kernel and policy signals.
        3. Tests can verify nothing in the current path emits these
           as primary runtime intents.

    Concrete emission rules are deferred. Expected future increments:
        - WRITE_MEMORY: fired by kernel on `write_intent=True` with
          sufficient novelty/coherence (kernel already tracks this;
          wiring needed at Phase 7).
        - PROPOSE_SHARE: fired by the proposal bridge on persistent
          convergence-event patterns (existing collective_proposals
          infrastructure; wiring needed at Phase 7).
        - CREATE_ARCHIVE_NOTE: fired when the turn produced substantive
          archive-bound content as judged by controller heuristics on
          the response, not on user input text.
    """
    # v0.1 stub — no outcomes emitted yet. Concrete rules will live
    # here when the relevant kernel/policy signals are threaded
    # through TurnContext by the S1 runner and later increments.
    _ = ctx  # silence unused-arg lint until emission logic lands
    return []
