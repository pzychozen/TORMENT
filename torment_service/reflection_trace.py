"""
torment_service/reflection_trace.py — ReflectionTrace v0.1.

Ephemeral, in-memory, per-turn observation surface for the CURRENT deterministic
decision-shape structure of the thinking layer. Observation only.

Scope (v0.1):
- Records coarse decision-shape LABELS only. It carries NO raw reasoning, raw
  input text, response draft, review rationale text, revised text, prompt text,
  memory content, seed text, kernel raw values (kappa/phi/Omega/drift/...), or
  retrieved context.
- It does NOT persist, write memory, write canon/identity, touch
  database/schema/storage, block or finalize output, or create durable private
  state. It is built from values the controller already computed and attached to
  the per-call ThinkingResult; nothing in the runtime branches on it.
- It is NOT Layer-2 reflection, NOT temporally extended reflection, NOT
  chosen-silence mechanics, and NOT governed-memory candidacy.

This module imports ONLY the standard library by design (no fabric / spine /
graph / storage / kernel), so its non-reachability is structural, not promised.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple


@dataclass(frozen=True)
class ReflectionTrace:
    """Immutable, shape-only record of one turn's decision structure.

    Frozen: field reassignment raises. All fields are coarse labels / counts /
    flags — never raw text or content.
    """

    chosen_mode: str
    action: str
    stance: Optional[str] = None
    review_status_flags: Dict[str, bool] = field(default_factory=dict)
    active_lanes: Tuple[str, ...] = ()
    lane_budget_shape: Dict[str, int] = field(default_factory=dict)
    geometric_context_present: bool = False
    scope: str = "per_turn_ephemeral"

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
            "geometric_context_present": self.geometric_context_present,
            "scope": self.scope,
        }


def build_reflection_trace(
    *,
    chosen_mode: str,
    action: str,
    stance: Optional[str],
    review_status_flags: Mapping[str, bool],
    top_k_by_lane: Mapping[str, int],
    geometric_context_present: bool,
) -> ReflectionTrace:
    """Pure constructor for a ReflectionTrace from already-computed, coarse
    decision values.

    No side effects, no I/O, no writers, no storage. Inputs are expected to be
    plain labels / ints / bools the caller already holds; this function copies
    and normalizes them into an immutable record. It reads no raw text and
    derives nothing from memory content or kernel internals.
    """
    active_lanes = tuple(
        sorted(str(k) for k, v in top_k_by_lane.items() if isinstance(v, int) and v > 0)
    )
    lane_budget_shape = {
        str(k): int(v) for k, v in top_k_by_lane.items() if isinstance(v, int)
    }
    return ReflectionTrace(
        chosen_mode=str(chosen_mode),
        action=str(action),
        stance=(str(stance) if stance is not None else None),
        review_status_flags={str(k): bool(v) for k, v in review_status_flags.items()},
        active_lanes=active_lanes,
        lane_budget_shape=lane_budget_shape,
        geometric_context_present=bool(geometric_context_present),
        scope="per_turn_ephemeral",
    )
