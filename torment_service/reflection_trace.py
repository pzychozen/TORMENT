"""
torment_service/reflection_trace.py — ReflectionTrace (v0.2).

Ephemeral, in-memory, per-turn observation surface for the CURRENT deterministic
decision-shape structure of the thinking layer. Observation only.

Scope:
- Records coarse decision-shape LABELS / flags / counts / scores only. It carries
  NO raw reasoning, raw input text, normalized input, response draft, review
  rationale text, revised text, action reason, payload, tone hints, prompt text,
  memory content, seed text, retrieved context, or raw kernel/SRG values.
- It does NOT persist, write memory, write canon/identity, touch
  database/schema/storage, block or finalize output, or create durable private
  state. It is built from values the controller already computed and attached to
  the per-call ThinkingResult; nothing in the runtime branches on it.
- It is NOT Layer-2 reflection, NOT temporally extended reflection, NOT
  chosen-silence mechanics, and NOT governed-memory candidacy.

v0.2 enriches the surface with additional coarse mode/action/frame fields (all
scalars/booleans). No content-bearing field is ever added.

This module imports ONLY the standard library by design (no fabric / spine /
graph / storage / kernel), so its non-reachability is structural, not promised.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple


@dataclass(frozen=True)
class ReflectionTrace:
    """Immutable, shape-only record of one turn's decision structure.

    Frozen: field reassignment raises, and the inner mapping fields are wrapped
    in read-only ``MappingProxyType`` views in ``__post_init__`` (backed by a
    private copy), so mutating a constructed trace's containers also raises. All
    fields are coarse labels / counts / flags / scores — never raw text or
    content.
    """

    # --- decision identity (required) ---
    chosen_mode: str
    action: str

    # --- existing v0.1 shape ---
    stance: Optional[str] = None
    review_status_flags: Mapping[str, bool] = field(default_factory=dict)
    active_lanes: Tuple[str, ...] = ()
    lane_budget_shape: Mapping[str, int] = field(default_factory=dict)
    lane_weight_shape: Mapping[str, float] = field(default_factory=dict)
    geometric_context_present: bool = False

    # --- v0.2 coarse mode shape (CognitiveModeDecision) ---
    allowed_depth: int = 1
    requires_self_review: bool = False
    may_escalate: bool = False
    confidence_floor: float = 0.0

    # --- v0.2 coarse action shape (ActionDecision) ---
    requires_execution: bool = False

    # --- v0.2 coarse frame shape (TaskFrame) ---
    source_type: str = "user_text"
    action_need: bool = False
    memory_need: bool = False
    tool_need: bool = False
    governance_sensitive: bool = False
    identity_sensitive: bool = False
    live_social: bool = False
    urgency: float = 0.0
    ambiguity_score: float = 0.0
    confidence_need: float = 0.0

    scope: str = "per_turn_ephemeral"

    def __post_init__(self) -> None:
        # ``frozen=True`` blocks attribute *reassignment* but not mutation of the
        # inner containers; wrap the mapping fields in read-only views backed by a
        # private copy so the record is genuinely immutable after construction.
        object.__setattr__(
            self, "review_status_flags", MappingProxyType(dict(self.review_status_flags))
        )
        object.__setattr__(
            self, "lane_budget_shape", MappingProxyType(dict(self.lane_budget_shape))
        )
        object.__setattr__(
            self, "lane_weight_shape", MappingProxyType(dict(self.lane_weight_shape))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain primitives for inspection surfaces only
        (e.g. /thinking/debug). Returns copies; never raw content."""
        return {
            "chosen_mode": self.chosen_mode,
            "action": self.action,
            "stance": self.stance,
            "review_status_flags": dict(self.review_status_flags),
            "active_lanes": list(self.active_lanes),
            "lane_budget_shape": dict(self.lane_budget_shape),
            "lane_weight_shape": dict(self.lane_weight_shape),
            "geometric_context_present": self.geometric_context_present,
            "allowed_depth": self.allowed_depth,
            "requires_self_review": self.requires_self_review,
            "may_escalate": self.may_escalate,
            "confidence_floor": self.confidence_floor,
            "requires_execution": self.requires_execution,
            "source_type": self.source_type,
            "action_need": self.action_need,
            "memory_need": self.memory_need,
            "tool_need": self.tool_need,
            "governance_sensitive": self.governance_sensitive,
            "identity_sensitive": self.identity_sensitive,
            "live_social": self.live_social,
            "urgency": self.urgency,
            "ambiguity_score": self.ambiguity_score,
            "confidence_need": self.confidence_need,
            "scope": self.scope,
        }


def build_reflection_trace(
    *,
    chosen_mode: str,
    action: str,
    stance: Optional[str],
    review_status_flags: Mapping[str, bool],
    top_k_by_lane: Mapping[str, int],
    weight_by_lane: Optional[Mapping[str, float]] = None,
    geometric_context_present: bool,
    allowed_depth: int = 1,
    requires_self_review: bool = False,
    may_escalate: bool = False,
    confidence_floor: float = 0.0,
    requires_execution: bool = False,
    source_type: str = "user_text",
    action_need: bool = False,
    memory_need: bool = False,
    tool_need: bool = False,
    governance_sensitive: bool = False,
    identity_sensitive: bool = False,
    live_social: bool = False,
    urgency: float = 0.0,
    ambiguity_score: float = 0.0,
    confidence_need: float = 0.0,
) -> ReflectionTrace:
    """Pure constructor for a ReflectionTrace from already-computed, coarse
    decision values.

    No side effects, no I/O, no writers, no storage. Inputs are expected to be
    plain labels / ints / floats / bools the caller already holds; this function
    copies and normalizes them into an immutable record. It reads no raw text and
    derives nothing from memory content or kernel internals.
    """
    active_lanes = tuple(
        sorted(str(k) for k, v in top_k_by_lane.items() if isinstance(v, int) and v > 0)
    )
    lane_budget_shape = {
        str(k): int(v) for k, v in top_k_by_lane.items() if isinstance(v, int)
    }
    # Content-free lane->weight shape, sourced ONLY from the already-computed
    # MemoryPlan.weight_by_lane. Numeric weights only — never text/payload/raw
    # SRG/kernel values, reasons, or retrieved context. (bool excluded.)
    lane_weight_shape = {
        str(k): float(v)
        for k, v in (weight_by_lane or {}).items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }
    return ReflectionTrace(
        chosen_mode=str(chosen_mode),
        action=str(action),
        stance=(str(stance) if stance is not None else None),
        review_status_flags={str(k): bool(v) for k, v in review_status_flags.items()},
        active_lanes=active_lanes,
        lane_budget_shape=lane_budget_shape,
        lane_weight_shape=lane_weight_shape,
        geometric_context_present=bool(geometric_context_present),
        allowed_depth=int(allowed_depth),
        requires_self_review=bool(requires_self_review),
        may_escalate=bool(may_escalate),
        confidence_floor=float(confidence_floor),
        requires_execution=bool(requires_execution),
        source_type=str(source_type),
        action_need=bool(action_need),
        memory_need=bool(memory_need),
        tool_need=bool(tool_need),
        governance_sensitive=bool(governance_sensitive),
        identity_sensitive=bool(identity_sensitive),
        live_social=bool(live_social),
        urgency=float(urgency),
        ambiguity_score=float(ambiguity_score),
        confidence_need=float(confidence_need),
        scope="per_turn_ephemeral",
    )
