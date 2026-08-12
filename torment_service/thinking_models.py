from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .reflection_trace import ReflectionTrace


@dataclass
class GeometricStanceContext:
    """Derived, normalized geometric state from the TORMENT kernel.

    All fields are 0.0–1.0 normalized.  This is a *derived* interface — the
    stance layer never touches raw kernel internals (kappa, phi, Omega, etc.).
    Instead, a harvester reads available agent/kernel state and maps it into
    these high-level signals.

    When no geometric context is supplied (``None``), the stance policy
    behaves exactly as before — pure deterministic scaffold.

    Fields
    ------
    coherence : float  (0–1)
        Kernel-wide phase synchrony.  High = system can think cleanly.
        Derived from ``coh_ema``.
    stability : float  (0–1)
        Whether coherence is sitting in a healthy basin or structurally
        stressed.  Combines tearing risk (inverted) and seed basin role.
        High = safely settled, low = on a ridge or tearing.
    identity_lock : float  (0–1)
        How anchored the character is to its seed right now.
        Derived from ``drift_score`` + ``drift_direction``.
        High = firmly on identity, low = drifting away.
    ambiguity_tolerance : float  (0–1)
        Capacity to absorb uncertain or incomplete input without identity
        risk.  Derived from ``seed_basin_phi`` (reinforcement − tension).
        Healthy basin = more tolerance, stressed basin = less.
    social_resonance : float  (0–1)  **provisional**
        Willingness to enter or sustain social interaction.  Currently a
        composite of live_social flag, corridor survival, and coherence.
        Clearly marked as transitional — may later be informed by collective
        field or genuine SRG signals.
    """

    coherence: float = 0.5
    stability: float = 0.5
    identity_lock: float = 0.5
    ambiguity_tolerance: float = 0.5
    social_resonance: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CognitiveMode(str, Enum):
    FAST = "fast"
    RETRIEVAL = "retrieval"
    REFLECTIVE = "reflective"
    TOOL = "tool"
    GOVERNED = "governed"
    IDENTITY_SENSITIVE = "identity_sensitive"
    LIVE_SOCIAL = "live_social"


class ActionType(str, Enum):
    ANSWER = "answer"
    ASK_CLARIFICATION = "ask_clarification"
    DEFER = "defer"
    USE_TOOL = "use_tool"
    WRITE_MEMORY = "write_memory"
    PROPOSE_SHARE = "propose_share"
    GOVERNANCE_REVIEW = "governance_review"
    CREATE_ARCHIVE_NOTE = "create_archive_note"
    NO_OP = "no_op"


@dataclass
class TaskFrame:
    workspace_id: str
    agent_id: str
    raw_input: str
    normalized_input: str
    source_type: str = "user_text"
    context_tags: List[str] = field(default_factory=list)
    urgency: float = 0.0
    ambiguity_score: float = 0.0
    confidence_need: float = 0.0
    action_need: bool = False
    memory_need: bool = False
    tool_need: bool = False
    governance_sensitive: bool = False
    identity_sensitive: bool = False
    live_social: bool = False
    tone_hints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CognitiveModeDecision:
    chosen_mode: CognitiveMode
    reason: str
    allowed_depth: int = 1
    requires_self_review: bool = False
    may_escalate: bool = False
    confidence_floor: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["chosen_mode"] = self.chosen_mode.value
        return d


@dataclass
class MemoryPlan:
    retrieve_core: bool = True
    retrieve_relational: bool = False
    retrieve_archive: bool = False
    retrieve_deep: bool = False
    retrieve_collective: bool = False
    retrieve_character_state: bool = True
    retrieve_srg_state: bool = False
    top_k_by_lane: Dict[str, int] = field(default_factory=dict)
    weight_by_lane: Dict[str, float] = field(default_factory=dict)
    max_token_budget: int = 2000
    safety_constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EphemeralCognitionState:
    """Per-turn, content-free, deterministic routing state (Slice 1).

    A frozen, primitive-only snapshot of the *shape* of a single
    deliberation turn — the already-computed scalar signals that drive
    ``ThinkingController.build_memory_plan`` retrieval shaping. It is the
    same boundary class as ``ReflectionTrace``:

      * **Ephemeral** — built per call, never persisted, never reentered.
      * **Content-free** — holds NO raw or normalized input, no reasons,
        no payloads, no tone hints, no drafts, no notes, no memory/seed
        text, no vectors, no collections. Every field is a bare
        ``bool`` / ``int`` / ``float`` / ``str`` scalar.
      * **Deterministic** — a pure function of ``(TaskFrame,
        CognitiveModeDecision)``; it reads no environment, clock, or
        external state of its own.
      * **Advisory / observation-shape only** — it shapes nothing on its
        own. ``build_memory_plan`` routes its decisions *through* this
        state, but the resulting ``MemoryPlan`` is byte-for-byte what it
        was before this struct existed.

    Slice-1 hard lines (see the pre-database status board §5): this struct
    is intentionally NOT serialized, NOT attached to ``ThinkingResult``,
    NOT exposed by ``/thinking/debug`` or ``/agent/query``, and carries no
    durable or content-bearing state. ``chosen_mode`` is stored as the
    plain ``str`` mode value (not the enum) to keep the struct trivially
    primitive.

    The ``*_context_signal`` fields are raw content/mode-derived detection
    predicates; the ``*_context_eligible`` fields are mode-derived
    eligibility predicates. Both are pre-environment-flag — the
    ``_SRG_COGNITION_ENABLE`` / ``_ARCHIVE_RECALL_ENABLE`` gates are applied
    downstream to their respective SRG and Archive lanes in
    ``build_memory_plan``. Deep eligibility remains mode-derived, keeping
    this state independent of runtime configuration.
    """

    # mode-decision shape (already-computed scalars)
    chosen_mode: str
    allowed_depth: int
    requires_self_review: bool
    may_escalate: bool
    confidence_floor: float
    # task-frame shape (already-computed scalars)
    urgency: float
    ambiguity_score: float
    confidence_need: float
    action_need: bool
    memory_need: bool
    tool_need: bool
    governance_sensitive: bool
    identity_sensitive: bool
    live_social: bool
    # derived retrieval-shaping predicates (pre-environment-flag)
    archive_context_signal: bool
    collective_context_signal: bool
    character_state_context_eligible: bool
    deep_context_eligible: bool


@dataclass
class ActionDecision:
    action: ActionType
    reason: str
    requires_execution: bool = False
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["action"] = self.action.value
        return d


class ResponseStance(str, Enum):
    """How the character chooses to participate in this interaction.

    Advisory only — never blocks Spine execution.  When the stance layer
    is disabled (default), the thinking pipeline behaves as before.
    """

    RESPOND_NOW = "respond_now"
    RESPOND_BRIEFLY = "respond_briefly"
    ASK_CLARIFICATION = "ask_clarification"
    DEFER = "defer"
    ABSTAIN = "abstain"
    SILENT_OBSERVE = "silent_observe"
    REQUEST_TURN = "request_turn"
    GOVERNED_REDIRECT = "governed_redirect"
    TOOL_REDIRECT = "tool_redirect"


@dataclass
class ResponseStanceDecision:
    """Optional participation decision attached to a ThinkingResult.

    This is advisory metadata — it suggests whether the character *should*
    respond, defer, stay silent, etc.  It never overrides Spine routing or
    trust/governance execution.
    """

    stance: ResponseStance
    reason: str
    confidence: float = 0.5
    fallback_stance: Optional[ResponseStance] = None
    context_factors: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["stance"] = self.stance.value
        d["fallback_stance"] = self.fallback_stance.value if self.fallback_stance else None
        return d


# ---------------------------------------------------------------------------
# Participation guidance v1 (visible advisory only — NEVER output control).
# Maps (TaskFrame, optional ResponseStanceDecision) to a single advisory
# candidate string surfaced on ThinkingResult.to_dict() / the advisory audit.
# It does NOT suppress, block, veto, finalize, or empty a response, and touches
# no dispatch / review.blocked / authority / memory path. The final response
# path stays free to ignore, soften, or express it. See
# docs/TORMENT_PARTICIPATION_GUIDANCE_FRAME_v0.1.md.
# ---------------------------------------------------------------------------

_PARTICIPATION_GUIDANCE_WHITELIST: Dict[ResponseStance, str] = {
    ResponseStance.RESPOND_BRIEFLY: "respond_briefly_candidate",
    ResponseStance.DEFER: "defer_candidate",
    ResponseStance.SILENT_OBSERVE: "silent_observe_candidate",
}


def map_participation_guidance(
    frame: TaskFrame,
    stance: Optional[ResponseStanceDecision],
) -> str:
    """Map (frame, stance) -> an advisory participation-guidance candidate.

    Returns exactly one of: ``"none"``, ``"respond_briefly_candidate"``,
    ``"defer_candidate"``, ``"silent_observe_candidate"``.

    Non-ordinary turns map to ``"none"``: a missing frame; any non-``user_text``
    source (operator / system / reflex-like); or governance-/identity-sensitive
    turns. A missing stance, or any stance outside the explicit whitelist, also
    maps to ``"none"``.

    Visible advisory ONLY — this is a label, not a control. It never suppresses,
    blocks, vetoes, or empties a response and never reads/writes review.blocked,
    dispatch, authority, or memory.
    """
    if frame is None:
        return "none"
    if getattr(frame, "source_type", "user_text") != "user_text":
        return "none"
    if getattr(frame, "governance_sensitive", False) or getattr(frame, "identity_sensitive", False):
        return "none"
    if stance is None:
        return "none"
    return _PARTICIPATION_GUIDANCE_WHITELIST.get(stance.stance, "none")


@dataclass
class ReviewResult:
    approved: bool = True
    revised: bool = False
    escalate: bool = False
    ask_user: bool = False
    blocked: bool = False
    notes: List[str] = field(default_factory=list)
    revised_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeliberationBundle:
    """Output of `ThinkingController.deliberate_only()` — inner Phases 2-4.

    Produced by the inner deliberation loop (frame_task → choose_mode
    → build_memory_plan → choose_action). Consumed by the outer-loop
    runner for Phases 5-8. Does NOT include review (Phase 6 sub-gate,
    runner-owned), draft (Phase 6 execute, runner-owned), or stance.

    Reference: docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 2 R6, R6.a.
    """
    task_frame: TaskFrame
    mode_decision: CognitiveModeDecision
    memory_plan: MemoryPlan
    action_decision: ActionDecision

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_frame": self.task_frame.to_dict(),
            "mode_decision": self.mode_decision.to_dict(),
            "memory_plan": self.memory_plan.to_dict(),
            "action_decision": self.action_decision.to_dict(),
        }


@dataclass
class ThinkingResult:
    task_frame: TaskFrame
    mode_decision: CognitiveModeDecision
    memory_plan: MemoryPlan
    action_decision: ActionDecision
    review_result: ReviewResult
    response_draft: Optional[str] = None
    stance: Optional[ResponseStanceDecision] = None
    geometric_context: Optional[GeometricStanceContext] = None
    debug: Dict[str, Any] = field(default_factory=dict)
    # ReflectionTrace v0.1: ephemeral, observation-only decision-shape record.
    # Surfaced only through to_dict() (e.g. /thinking/debug); never consumed by
    # retrieval, prompt assembly, writers, or any decision path.
    reflection_trace: Optional[ReflectionTrace] = None
    # Participation guidance v1 (visible advisory only): a single candidate
    # string set by the controller ONLY when the flag is on. ``None`` ⇒ omitted
    # from ``to_dict()`` entirely (flag off ⇒ exact parity). Never output control.
    participation_guidance: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "task_frame": self.task_frame.to_dict(),
            "mode_decision": self.mode_decision.to_dict(),
            "memory_plan": self.memory_plan.to_dict(),
            "action_decision": self.action_decision.to_dict(),
            "review_result": self.review_result.to_dict(),
            "response_draft": self.response_draft,
            "stance": self.stance.to_dict() if self.stance else None,
            "geometric_context": self.geometric_context.to_dict() if self.geometric_context else None,
            "debug": self.debug,
            "reflection_trace": self.reflection_trace.to_dict() if self.reflection_trace else None,
        }
        # Visible advisory only; omitted entirely when unset (flag off ⇒ parity).
        if self.participation_guidance is not None:
            d["participation_guidance"] = self.participation_guidance
        return d
