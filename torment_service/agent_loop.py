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
    M1: Phase 7 assimilation-outcome dispatcher scaffold (landed).
    M2: Mode-legality enforcement + fallback chain in action_policy
        (landed).
    S1 (this commit): AgentRunner.run_turn orchestrator wiring Phases
        1-8. Uses controller.deliberate_only() for Phases 2-4; owns
        Phases 5-8 directly. LLM synthesis and fabric side-effects are
        delegated via FabricHandle + LLMClient protocols; tests use
        fakes. Live fabric hookup deferred to v0.1.0a.
    S2:               Drift-regime veto layered on Phase 5.
    S3:               Tool-policy gate + single-signature narrowing.
    S4:               Behavior pack (five-object bundle) constructed
                      and handed to AgentRunner.
    S5:               Drift-triggered stabilization reflex via
                      enter_reflex; proven with zero LLM calls.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from .action_policy import (
    ActionPolicyDecision,
    DriftRegime,
    apply_drift_veto,
    apply_legality,
    apply_tool_narrowing,
    classify_drift,
)
from .tool_registry import ActionContract, EMPTY_CONTRACT
from .thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveModeDecision,
    MemoryPlan,
    ReviewResult,
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


# ---------------------------------------------------------------------------
# S1 — Outer-loop runner
# ---------------------------------------------------------------------------


@dataclass
class Observation:
    """Phase 1 input to the outer-loop runner.

    A turn can be driven by any of:
        - user_text: ordinary user message
        - reflex: kernel-triggered reflex turn (see enter_reflex)
        - tool_result: post-Phase-6 continuation turn after a tool call
        - file_event: file-system or watcher-driven observation
        - scheduled: external scheduler-driven observation

    The source_type affects frame_task's shaping and can bias mode
    selection (e.g. reflex source_type tends toward IDENTITY_SENSITIVE).
    """
    text: str
    source_type: str = "user_text"
    governance_sensitive: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionOutcome:
    """Phase 6 execute output (pre-review).

    The runner populates this based on the effective action chosen by
    Phase 5. Review (also part of Phase 6) may revise response_text
    or cause the outcome to be suppressed (no_op=True) per R6.a.
    """
    response_text: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None
    llm_called: bool = False
    tool_called: bool = False
    no_op: bool = False


@dataclass
class TurnResult:
    """End-of-turn (Phase 8) snapshot surfaced by AgentRunner.run_turn.

    Populated progressively through the turn. All phase outputs are
    available on the result for observability; invariant-checking
    tests read from here.
    """
    workspace_id: str
    agent_id: str
    task_frame: TaskFrame
    mode_decision: CognitiveModeDecision
    memory_plan: MemoryPlan
    action_decision: ActionDecision
    action_policy_decision: ActionPolicyDecision
    execution_outcome: ExecutionOutcome
    review_outcome: Optional[ReviewResult]
    assimilation_outcomes: List[ActionType]
    drift_after_stabilize: Optional[Dict[str, Any]]
    gravity_correction_applied: bool
    ingest_attempted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Protocols for side-effecting dependencies (tests inject fakes)
# ---------------------------------------------------------------------------


class FabricHandle(Protocol):
    """Abstract interface for kernel-side operations the runner needs.

    v0.1 (S1): implemented as fakes in tests. Live wiring to
    `torment_service.fabric.TormentFabric` is v0.1.0a — deferred to
    keep this slice about proof-of-contract rather than integration
    breadth.
    """

    def ingest(
        self,
        workspace_id: str,
        agent_id: str,
        text: str,
        step: int,
    ) -> Dict[str, Any]:
        ...

    def measure_drift(
        self,
        workspace_id: str,
        agent_id: str,
    ) -> Optional[Dict[str, Any]]:
        ...

    def gravity_correction(
        self,
        workspace_id: str,
        agent_id: str,
        drift_info: Dict[str, Any],
    ) -> None:
        ...


class LLMClient(Protocol):
    """Abstract interface for Phase 6 LLM synthesis.

    v0.1 (S1): implemented as fake in tests. Production client
    adapters can target Anthropic, OpenAI, Ollama, or any other
    LLM — that's agent-integrator territory, not doctrine.

    `tools` (S3): when USE_TOOL has been narrowed at Phase 5, the
    runner passes the single approved tool signature as a list of
    length 1. Clients that do not support tool-calling may ignore
    this parameter; the runner still records that narrowing
    happened on `TurnResult.action_policy_decision.tool_family_narrowed`.
    """

    def complete(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        ...


class ToolExecutor(Protocol):
    """Abstract interface for executing a narrowed tool family.

    v0.1 (S3): implemented as a stub in tests. Real executors
    (sandboxed Python subprocess, HTTP adapters, etc.) are integrator
    concerns and land in post-slice increments. v0.1.0b is the
    hardened code_exec sandbox.

    The runner invokes `execute(family, arguments, defaults)` after
    Phase 5 narrowing when a tool executor is wired. `family` is the
    narrowed tool family name; `arguments` is whatever the LLM filled
    into the signature's parameters; `defaults` carries the
    controller-side constraints (language, timeout, sandbox scope)
    from the ToolSignature.
    """

    def execute(
        self,
        family: str,
        arguments: Dict[str, Any],
        defaults: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...


# ---------------------------------------------------------------------------
# AgentRunner — the outer-loop orchestrator
# ---------------------------------------------------------------------------


# v0.1 drift regime — default high-regime threshold for Phase 8
# gravity correction. Matches TORMENT_CHARACTER_CORRECTION_THRESHOLD
# from character.py. S2 will layer drift-regime action veto at
# Phase 5 using the same constant. Doctrine Appendix A.
_DEFAULT_DRIFT_HIGH_THRESHOLD = 0.35


class AgentRunner:
    """Outer-loop runner for a single TORMENT agent turn.

    Implements the 8-phase loop specified in doctrine Part 2 R6:
        1. Observe
        2. Frame         — via ThinkingController.deliberate_only
        3. Aperture      — via ThinkingController.deliberate_only
        4. Intent        — via ThinkingController.deliberate_only
        5. Action Policy — via action_policy.apply_legality
        6. Execute + review sub-gate
        7. Assimilate (ingest + assimilation_outcomes)
        8. Stabilize (measure_drift + conditional gravity_correction)

    The runner visibly owns Phases 5-8. Phases 2-4 are delegated to
    the controller's `deliberate_only()` as a clean seam — per doctrine
    R6.a and the S1 seam fix in the ratified slice plan.

    v0.1 scope:
        - No behavior pack wiring (S4 will add that).
        - No drift-regime veto in Phase 5 (S2 will add that).
        - No tool narrowing in Phase 5 (S3 will add that).
        - USE_TOOL execution is stubbed (S3).
        - LLM synthesis goes through the injected LLMClient (tests
          pass fakes; production wiring is the integrator's job).
        - Fabric side-effects go through the injected FabricHandle.
    """

    def __init__(
        self,
        controller: Any,  # ThinkingController; avoiding a circular import
        fabric: FabricHandle,
        llm_client: Optional[LLMClient] = None,
        pack: Optional[Any] = None,  # BehaviorPack (S4); None in S1
        action_contract: ActionContract = EMPTY_CONTRACT,
        tool_executor: Optional[ToolExecutor] = None,
        drift_high_threshold: float = _DEFAULT_DRIFT_HIGH_THRESHOLD,
    ):
        self.controller = controller
        self.fabric = fabric
        self.llm_client = llm_client
        self.pack = pack
        self.action_contract = action_contract
        self.tool_executor = tool_executor
        self.drift_high_threshold = drift_high_threshold

    def run_turn(
        self,
        workspace_id: str,
        agent_id: str,
        observation: Observation,
        step: int,
    ) -> TurnResult:
        """Execute one full agent turn through all 8 phases."""
        # Phase 1: Observe — input has arrived. Nothing to do here
        # beyond acknowledging the observation; kept explicit so the
        # phase seam is visible.

        # Phases 2-4: Frame → Aperture → Intent via the inner scaffold.
        bundle = self.controller.deliberate_only(
            workspace_id=workspace_id,
            agent_id=agent_id,
            raw_input=observation.text,
            source_type=observation.source_type,
            metadata=observation.metadata,
        )

        # Phase 5: Action Policy. Three-layer gate:
        # (a) mode legality + fallback chain (M2)
        # (b) drift-regime veto (S2)
        # (c) tool-family narrowing for USE_TOOL (S3 — not yet wired)
        #
        # Drift is measured once here and reused in Phase 8 so the turn
        # makes exactly one measure_drift call per turn.
        drift_info: Optional[Dict[str, Any]] = None
        try:
            drift_info = self.fabric.measure_drift(
                workspace_id=workspace_id,
                agent_id=agent_id,
            )
        except Exception:
            drift_info = None
        drift_regime = classify_drift(
            drift_info, high_threshold=self.drift_high_threshold
        )

        policy_decision = apply_legality(
            bundle.action_decision,
            bundle.mode_decision,
            bundle.task_frame,
        )
        policy_decision = apply_drift_veto(
            policy_decision,
            bundle.mode_decision,
            drift_regime,
            bundle.task_frame,
        )
        policy_decision = apply_tool_narrowing(
            policy_decision,
            bundle.mode_decision,
            self.action_contract,
        )
        effective_action = policy_decision.action

        # Phase 6: Execute + review sub-gate (R6.a).
        execution_outcome = self._execute(
            frame=bundle.task_frame,
            mode=bundle.mode_decision,
            action=effective_action,
        )

        review_outcome = self.controller.review(
            frame=bundle.task_frame,
            mode=bundle.mode_decision,
            action=effective_action,
            response_draft=execution_outcome.response_text,
        )

        # R6.a: review may revise text or veto. It never re-enters
        # earlier phases — the runner simply applies its result here.
        if review_outcome.revised and review_outcome.revised_text is not None:
            execution_outcome.response_text = review_outcome.revised_text

        if review_outcome.blocked:
            # Review vetoes Phase 7 advancement. Output is suppressed;
            # Phase 8 still runs for drift bookkeeping.
            execution_outcome.response_text = None
            execution_outcome.no_op = True

        # Phase 7: Assimilate — ingest turn summary, emit assimilation
        # outcomes. Skipped if review blocked.
        assimilation_outcomes_list: List[ActionType] = []
        ingest_attempted = False
        if not review_outcome.blocked:
            ctx = TurnContext(
                workspace_id=workspace_id,
                agent_id=agent_id,
                task_frame=bundle.task_frame,
                mode_decision=bundle.mode_decision,
                memory_plan=bundle.memory_plan,
                action_decision=effective_action,
                response_text=execution_outcome.response_text,
                tool_result=execution_outcome.tool_result,
            )
            assimilation_outcomes_list = assimilation_outcomes(ctx)

            if execution_outcome.response_text and not execution_outcome.no_op:
                summary = self._build_ingest_summary(
                    observation=observation,
                    response_text=execution_outcome.response_text,
                )
                try:
                    self.fabric.ingest(
                        workspace_id=workspace_id,
                        agent_id=agent_id,
                        text=summary,
                        step=step,
                    )
                    ingest_attempted = True
                except Exception:
                    # Best-effort: ingest failure does not abort the
                    # turn. Phase 8 still runs.
                    pass

        # Phase 8: Stabilize — reuse the Phase 5 drift measurement to
        # decide gravity correction. One measure_drift call per turn.
        # Best-effort: failures here are recorded but do not raise.
        gravity_applied = False
        if drift_info is not None and drift_regime.vetoes_outward_action:
            try:
                self.fabric.gravity_correction(
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    drift_info=drift_info,
                )
                gravity_applied = True
            except Exception:
                pass

        return TurnResult(
            workspace_id=workspace_id,
            agent_id=agent_id,
            task_frame=bundle.task_frame,
            mode_decision=bundle.mode_decision,
            memory_plan=bundle.memory_plan,
            action_decision=bundle.action_decision,
            action_policy_decision=policy_decision,
            execution_outcome=execution_outcome,
            review_outcome=review_outcome,
            assimilation_outcomes=assimilation_outcomes_list,
            drift_after_stabilize=drift_info,
            gravity_correction_applied=gravity_applied,
            ingest_attempted=ingest_attempted,
        )

    def enter_reflex(
        self,
        workspace_id: str,
        agent_id: str,
        reason: str,
        step: Optional[int] = None,
    ) -> TurnResult:
        """S5 entry point: trigger a reflex turn.

        Constructs a synthetic observation marked `source_type="reflex"`
        and runs it through `run_turn`. The downstream behavior that
        forces DEFER and skips LLM synthesis depends on the behavior
        pack (S4) being present on this runner. Without S4's pack,
        this method still completes a full turn but the intent may
        not be forced to DEFER.

        Live-fabric hookup from `fabric.py`'s drift check to this
        entry point is v0.1.0a.
        """
        reflex_obs = Observation(
            text=f"[reflex: {reason}]",
            source_type="reflex",
            metadata={"reflex_reason": reason},
        )
        return self.run_turn(
            workspace_id=workspace_id,
            agent_id=agent_id,
            observation=reflex_obs,
            step=step if step is not None else int(time.time()),
        )

    # ---------------- private helpers ----------------

    def _execute(
        self,
        frame: TaskFrame,
        mode: CognitiveModeDecision,
        action: ActionDecision,
    ) -> ExecutionOutcome:
        """Phase 6 Execute (pre-review)."""
        at = action.action

        if at == ActionType.NO_OP:
            return ExecutionOutcome(no_op=True)

        if at == ActionType.DEFER:
            return ExecutionOutcome(
                response_text=(
                    "Holding on that — waiting for more context before acting."
                ),
            )

        if at == ActionType.ASK_CLARIFICATION:
            return ExecutionOutcome(
                response_text=(
                    "Can you say a little more so I can pick the right move?"
                ),
            )

        if at == ActionType.GOVERNANCE_REVIEW:
            return ExecutionOutcome(
                response_text=(
                    "This looks like a governance-sensitive operation and "
                    "should route through the controlled path."
                ),
            )

        if at == ActionType.ANSWER:
            if self.llm_client is None:
                # v0.1 stub path for tests that don't wire an LLM.
                return ExecutionOutcome(
                    response_text="[no llm client wired — v0.1 stub]",
                )
            response = self.llm_client.complete(
                system_prompt=self._build_system_prompt(frame, mode),
                messages=[{"role": "user", "content": frame.raw_input}],
                tools=None,
            )
            return ExecutionOutcome(response_text=response, llm_called=True)

        if at == ActionType.USE_TOOL:
            # After S3 narrowing, the action payload carries exactly
            # one tool signature (invariant 2). The runner passes it
            # to the LLM as a single-element tools list.
            signature_spec = action.payload.get("tool_signature")
            tool_family = action.payload.get("tool_family")
            tool_defaults = action.payload.get("tool_defaults", {})

            if signature_spec is None or tool_family is None:
                # Narrowing should have attached these; if they're
                # absent, something upstream is misconfigured. Return
                # no-op rather than invent a menu.
                return ExecutionOutcome(
                    response_text=(
                        "[tool signature missing after narrowing — "
                        "no execution]"
                    ),
                    tool_called=False,
                )

            if self.llm_client is None:
                # Stub path — narrowing proved, but nothing to execute.
                return ExecutionOutcome(
                    response_text="[no llm client wired — v0.1 stub]",
                    tool_called=False,
                )

            # Call LLM with the single narrowed signature. LLM fills
            # arguments; tests may use a fake that ignores this.
            llm_response = self.llm_client.complete(
                system_prompt=self._build_system_prompt(frame, mode),
                messages=[{"role": "user", "content": frame.raw_input}],
                tools=[signature_spec],
            )

            if self.tool_executor is None:
                # No executor wired — v0.1 path returns the LLM
                # response as text. Real tool dispatch is v0.1.0b.
                return ExecutionOutcome(
                    response_text=llm_response,
                    llm_called=True,
                    tool_called=False,
                )

            # Executor wired: invoke with LLM-filled arguments. For
            # v0.1 the runner does not parse tool_call structures out
            # of the LLM response — fakes return canned results;
            # production integrators will add the parse step.
            tool_result = self.tool_executor.execute(
                family=tool_family,
                arguments={},  # production: parse from llm_response
                defaults=tool_defaults,
            )
            return ExecutionOutcome(
                tool_result=tool_result,
                response_text=str(
                    tool_result.get("output", llm_response or "")
                ),
                llm_called=True,
                tool_called=True,
            )

        # Unexpected action type (should not happen given Phase 5
        # legality enforcement). Treat as no-op.
        return ExecutionOutcome(no_op=True)

    def _build_system_prompt(
        self,
        frame: TaskFrame,
        mode: CognitiveModeDecision,
    ) -> str:
        """v0.1 minimal system prompt. S4's behavior pack will shape
        this via aperture recipe + character context."""
        return (
            f"You are agent {frame.agent_id} operating in mode "
            f"{mode.chosen_mode.value}."
        )

    def _build_ingest_summary(
        self,
        observation: Observation,
        response_text: str,
    ) -> str:
        """Compact turn summary for Phase 7 memory ingestion."""
        return (
            f"User ({observation.source_type}): {observation.text[:200]}\n"
            f"Agent: {response_text[:300]}"
        )
