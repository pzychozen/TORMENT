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
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Protocol

from .action_policy import (
    ActionPolicyDecision,
    apply_drift_veto,
    apply_legality,
    apply_pack_intent_tightening,
    apply_tool_narrowing,
    classify_drift,
)
from .behavior_packs import BehaviorPack
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


@dataclass
class ToolCall:
    """A single tool-use block extracted from an LLM response.

    v0.1.0c: produced by `LLMClient` implementations that parse
    tool-calling responses (e.g. Anthropic `tool_use` blocks, OpenAI
    `tool_calls`). Consumed by `AgentRunner._execute` in the USE_TOOL
    path, which validates `tool_name` against the narrowed family
    (invariant 2) and passes `arguments` to `tool_executor.execute`.
    """
    tool_name: str
    arguments: Dict[str, Any]
    tool_use_id: Optional[str] = None  # some APIs round-trip this


@dataclass
class LLMResponse:
    """Structured response from an LLM complete() call.

    v0.1.0c (clean-break protocol change): `LLMClient.complete`
    returns this instead of a bare string. Old text-only responses
    become `LLMResponse(text="...")`; tool-calling responses carry
    `tool_calls` alongside.

    Fields:
        text: concatenated text content of the response.
        tool_calls: parsed tool-use blocks, in order of appearance
            in the response.
        stop_reason: LLM-reported stop reason ("end_turn", "tool_use",
            "max_tokens", etc.). Diagnostic only; runner does not
            branch on this.
    """
    text: str = ""
    tool_calls: List["ToolCall"] = field(default_factory=list)
    stop_reason: Optional[str] = None


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

    Return shape (v0.1.0c clean break): `LLMResponse` with `text`
    and `tool_calls`. Clients that don't support tool-calling return
    `LLMResponse(text="...")` with an empty tool_calls list. See
    `ToolCall` for the tool-use shape.
    """

    def complete(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
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

    v0.1 scope (post v0.1.0d):
        - Phase 5 is a four-layer gate:
            apply_legality
            → apply_pack_intent_tightening (v0.1.0d)
            → apply_drift_veto
            → apply_tool_narrowing
        - USE_TOOL execution is wired through the injected ToolExecutor
          (v0.1.0b hardened SubprocessPythonExecutor for code_exec).
        - LLM synthesis goes through the injected LLMClient (tests
          pass fakes; production wiring is the integrator's job).
        - Fabric side-effects go through the injected FabricHandle.
    """

    def __init__(
        self,
        controller: Any,  # ThinkingController; avoiding a circular import
        fabric: FabricHandle,
        llm_client: Optional[LLMClient] = None,
        pack: Optional[BehaviorPack] = None,
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

    # ---------------- pack-derived effective settings ----------------
    #
    # S4: when a pack is active, pack-derived values override the
    # runner's explicit constructor parameters. Computed per-turn
    # rather than cached, so swapping `self.pack` between turns
    # takes effect immediately without needing a rebuild. Per
    # doctrine Part 5, pack overrides may only TIGHTEN; these
    # helpers do not widen anything the base settings permit.

    def _effective_action_contract(self) -> ActionContract:
        if self.pack is not None:
            return self.pack.action_contract
        return self.action_contract

    def _effective_drift_threshold(self) -> float:
        if self.pack is not None:
            return self.pack.stabilization_program.high_threshold
        return self.drift_high_threshold

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

        # S4: if a behavior pack is active, its aperture recipe
        # replaces the controller's default memory plan. The pack
        # is the source of truth for context-specific retrieval
        # shaping. (Doctrine Part 5 / slice plan S4.)
        if self.pack is not None:
            bundle = replace(
                bundle,
                memory_plan=self.pack.aperture_recipe.memory_plan,
            )

        # Phase 5: Action Policy. Four-layer gate:
        # (a) mode legality + fallback chain (M2)
        # (b) pack intent-grammar tightening (v0.1.0d)
        # (c) drift-regime veto (S2)
        # (d) tool-family narrowing for USE_TOOL (S3)
        #
        # Order matters: legality runs first (broadest doctrinal rule),
        # then pack-specific tightening narrows further, then kernel-state
        # drift veto overlays, then tool-family narrowing attaches the
        # single signature (only meaningful for surviving USE_TOOL).
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
            drift_info, high_threshold=self._effective_drift_threshold()
        )

        policy_decision = apply_legality(
            bundle.action_decision,
            bundle.mode_decision,
            bundle.task_frame,
        )
        policy_decision = apply_pack_intent_tightening(
            policy_decision,
            bundle.mode_decision,
            self.pack,
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
            self._effective_action_contract(),
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
            # v0.1.0c: LLMResponse clean-break — use .text. Any
            # unexpected tool_calls on the ANSWER path are ignored
            # (we didn't request tools; model returning some is odd
            # but not a contract violation since we didn't narrow a
            # family for this turn).
            return ExecutionOutcome(response_text=response.text, llm_called=True)

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
            # arguments via a tool_use block in its response; we parse
            # that from LLMResponse.tool_calls.
            llm_response = self.llm_client.complete(
                system_prompt=self._build_system_prompt(frame, mode),
                messages=[{"role": "user", "content": frame.raw_input}],
                tools=[signature_spec],
            )

            # v0.1.0c: three-path split based on response shape.
            # Strict contract enforcement per doctrine invariant 2
            # and GPT's design-pass sign-off.

            # Path A: no tool_calls at all → model declined to use
            # the narrowed tool and returned plain text. Legal —
            # presenting one tool doesn't force calling it.
            if not llm_response.tool_calls:
                return ExecutionOutcome(
                    response_text=llm_response.text,
                    llm_called=True,
                    tool_called=False,
                )

            # Path B: more than one tool_call → strict contract
            # failure. One narrowed family, one call permitted per
            # turn. Tool NOT invoked.
            if len(llm_response.tool_calls) > 1:
                contract_error = (
                    f"multiple_tool_calls_in_single_turn: "
                    f"received {len(llm_response.tool_calls)} calls"
                )
                return ExecutionOutcome(
                    response_text=(
                        llm_response.text
                        or f"[{contract_error}]"
                    ),
                    tool_result={"error": contract_error},
                    llm_called=True,
                    tool_called=False,
                )

            # Exactly one tool_call. Validate name against narrowed
            # family (invariant 2 continuation).
            tool_call = llm_response.tool_calls[0]
            if tool_call.tool_name != tool_family:
                contract_error = (
                    f"tool_name_mismatch: "
                    f"expected {tool_family!r}, got {tool_call.tool_name!r}"
                )
                return ExecutionOutcome(
                    response_text=(
                        llm_response.text
                        or f"[{contract_error}]"
                    ),
                    tool_result={"error": contract_error},
                    llm_called=True,
                    tool_called=False,
                )

            # Path C: matching single tool_call. Invoke the executor
            # with the LLM-filled arguments.
            if self.tool_executor is None:
                return ExecutionOutcome(
                    response_text=(
                        llm_response.text
                        or "[tool_call received but no executor wired]"
                    ),
                    tool_result={"tool_call": {
                        "tool_name": tool_call.tool_name,
                        "arguments": tool_call.arguments,
                    }},
                    llm_called=True,
                    tool_called=False,
                )

            tool_result = self.tool_executor.execute(
                family=tool_family,
                arguments=tool_call.arguments,
                defaults=tool_defaults,
            )
            # response_text prefers tool output; falls back to LLM
            # text if the executor returned none.
            resp_text = (
                str(tool_result.get("output") or "").strip()
                or llm_response.text
                or ""
            )
            return ExecutionOutcome(
                tool_result=tool_result,
                response_text=resp_text,
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
