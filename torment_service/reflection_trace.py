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


# Fixed, content-free keys for the MemoryPlan shaping posture. One boolean per
# default-off MemoryPlan shaping reflex, recording whether that reflex ACTUALLY
# changed the effective plan this turn. These keys are ALWAYS present and their
# values are ALWAYS plain booleans (normalized in ``ReflectionTrace.__post_init__``).
_MEMORY_PLAN_SHAPING_POSTURE_KEYS = (
    "relational_ambiguity_prominence",
    "ambiguity_context_diversity",
)

# Fixed, content-free keys for the derived MemoryPlan quality/thinness summary.
# Every value is a plain int or bool DERIVED from already-normalized, content-free
# trace fields (lane budgets, confidence_need, and the shaping posture). These keys
# are ALWAYS present (computed in ``ReflectionTrace.__post_init__``); no value is
# ever supplied by a caller, so no stray key or raw text can enter this map.
_MEMORY_PLAN_QUALITY_KEYS = (
    "active_lane_count",
    "non_core_active_lane_count",
    "total_lane_budget",
    "thin_context",
    "low_confidence_need",
    "shaping_reflex_count",
    "heavily_shaped",
)

# Fixed, content-free keys for the derived MemoryPlan sufficiency advisory. Each is
# a plain bool DERIVED ONLY from the already-normalized ``memory_plan_quality`` map
# (thin_context / low_confidence_need / heavily_shaped), plus a ``nominal`` flag that
# is True only when none of those three candidates fire. These keys are ALWAYS
# present (computed in ``ReflectionTrace.__post_init__``); no value is ever supplied
# by a caller, so no stray key or raw text can enter this map. Advisory / observation
# only — nothing branches on it.
_MEMORY_PLAN_SUFFICIENCY_ADVISORY_KEYS = (
    "thin_context_candidate",
    "low_confidence_candidate",
    "heavily_shaped_candidate",
    "nominal_plan_candidate",
)


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

    # --- MemoryPlan shaping posture (content-free fixed-key boolean map) ---
    # Which default-off MemoryPlan shaping reflex ACTUALLY changed the effective
    # plan this turn (True) vs. was disabled / ineligible / skipped / no-op (False).
    # Booleans only; the two fixed keys are always present (normalized in
    # ``__post_init__``). Carries NO raw input / prompt / reasoning / provider /
    # output-decision / candidate content — only whether each reflex moved the plan.
    memory_plan_shaping_posture: Mapping[str, bool] = field(default_factory=dict)

    # --- MemoryPlan quality/thinness summary (content-free, DERIVED) ---
    # Coarse int/bool summary of plan thinness + shaping intensity, derived in
    # ``__post_init__`` from the already-normalized content-free fields. Fixed keys,
    # primitive values only; any value passed for this field is IGNORED and replaced
    # by the derived map. Carries no raw text / prompt / reasoning / provider /
    # output-decision / candidate content, and nothing branches on it.
    memory_plan_quality: Mapping[str, Any] = field(default_factory=dict)

    # --- MemoryPlan sufficiency advisory (content-free, DERIVED) ---
    # Coarse bool advisory of whether the plan looks thin / low-confidence / heavily
    # shaped, or nominal — derived in ``__post_init__`` ONLY from the already-derived
    # ``memory_plan_quality`` map. Fixed keys, bool values only; any value passed for
    # this field is IGNORED and replaced by the derived map. Advisory / observation
    # only: nothing branches on it, and it carries no raw text / prompt / reasoning /
    # provider / output-decision / candidate content.
    memory_plan_sufficiency_advisory: Mapping[str, bool] = field(default_factory=dict)

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
        # Normalize the shaping posture to the fixed keys with plain-bool values so
        # the surface is always exactly the two booleans (no missing keys, no stray
        # keys, no non-bool / text values), then wrap read-only like the siblings.
        _posture_src = dict(self.memory_plan_shaping_posture)
        object.__setattr__(
            self,
            "memory_plan_shaping_posture",
            MappingProxyType(
                {k: bool(_posture_src.get(k, False))
                 for k in _MEMORY_PLAN_SHAPING_POSTURE_KEYS}
            ),
        )
        # Derive the content-free plan-quality/thinness summary from the ALREADY-
        # normalized fields above — never from raw text or new inputs. lane_budget_shape
        # is the int projection of ``top_k_by_lane``; the shaping posture is the two
        # normalized booleans; confidence_need is a coarse float. Any value passed in
        # for ``memory_plan_quality`` is ignored and replaced by this derived map, so
        # it can carry no stray keys and no raw text. int/bool primitives only.
        _budgets = {
            k: v for k, v in dict(self.lane_budget_shape).items()
            if isinstance(v, int) and not isinstance(v, bool)
        }
        _active = {k: v for k, v in _budgets.items() if v > 0}
        _active_lane_count = len(_active)
        _non_core_active = sum(1 for k in _active if k != "core")
        _total_lane_budget = sum(_active.values())
        _thin_context = (_non_core_active == 0) or (_active_lane_count == 1)
        _low_confidence_need = float(self.confidence_need) >= 0.60
        _shaping_reflex_count = sum(
            1 for v in dict(self.memory_plan_shaping_posture).values() if v is True
        )
        _heavily_shaped = _shaping_reflex_count >= 2
        object.__setattr__(
            self,
            "memory_plan_quality",
            MappingProxyType({
                "active_lane_count": int(_active_lane_count),
                "non_core_active_lane_count": int(_non_core_active),
                "total_lane_budget": int(_total_lane_budget),
                "thin_context": bool(_thin_context),
                "low_confidence_need": bool(_low_confidence_need),
                "shaping_reflex_count": int(_shaping_reflex_count),
                "heavily_shaped": bool(_heavily_shaped),
            }),
        )
        # Derive the content-free sufficiency advisory ONLY from the just-derived
        # ``memory_plan_quality`` map above — no raw text, no new inputs. The three
        # candidates mirror quality flags; ``nominal`` is True only when none fire.
        # Any value passed in for this field is ignored and replaced. bool only.
        _q = self.memory_plan_quality
        _thin_cand = bool(_q["thin_context"])
        _low_cand = bool(_q["low_confidence_need"])
        _heavy_cand = bool(_q["heavily_shaped"])
        object.__setattr__(
            self,
            "memory_plan_sufficiency_advisory",
            MappingProxyType({
                "thin_context_candidate": _thin_cand,
                "low_confidence_candidate": _low_cand,
                "heavily_shaped_candidate": _heavy_cand,
                "nominal_plan_candidate": not (_thin_cand or _low_cand or _heavy_cand),
            }),
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
            "memory_plan_shaping_posture": dict(self.memory_plan_shaping_posture),
            "memory_plan_quality": dict(self.memory_plan_quality),
            "memory_plan_sufficiency_advisory": dict(self.memory_plan_sufficiency_advisory),
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
    memory_plan_shaping_posture: Optional[Mapping[str, bool]] = None,
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
        # Content-free fixed-key boolean posture; normalized again in
        # ``__post_init__`` so the two keys are always present as plain booleans.
        memory_plan_shaping_posture=(memory_plan_shaping_posture or {}),
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
