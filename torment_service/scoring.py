# scoring.py
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple
import numpy as np
from .motifs import cosine


def score_hit(
    sim: float,
    strength: float,
    recency_days: float,
    motif_alignment: float,
    contradiction_risk: float,
    alpha: float = 0.35,
    beta: float = 0.10,
    gamma: float = 0.20,
    delta: float = 0.30,
    type_bonus: float = 0.0,
) -> float:
    rec_bonus = 1.0 / (1.0 + max(0.0, recency_days))
    base = float(sim * (1.0 + alpha*strength + beta*rec_bonus + gamma*motif_alignment) - delta*contradiction_risk)
    return float(base + float(type_bonus))


# ---------------------------------------------------------------------------
# Continuity bonus helpers — shared by query() and trace()
# ---------------------------------------------------------------------------

@dataclass
class ContinuityContext:
    """Pre-computed, per-query context for continuity scoring.

    Computed once per query/trace call, then passed to
    ``compute_continuity_bonuses`` for each hit.
    """
    agent_id: str = ""
    canonical_step: int = -1
    # affect
    affect_personal: bool = False
    q_affect_tag: str = "neutral"
    q_affect_conf: float = 0.0
    affect_match_bonus: float = 0.05
    affect_min_conf: float = 0.40
    # thread-window
    thread_window_steps: int = 50
    thread_window_bonus: float = 0.08
    # mood-drift
    mood_drift_bonus: float = 0.04
    # mood-spiral
    spiral_enable: bool = True
    spiral_neg_recent: int = 0
    spiral_min_drifts: int = 2
    spiral_older_than: int = 250
    spiral_window: int = 800
    spiral_penalty_max: float = 0.08
    # self-thread bonus
    self_thread_bonus_val: float = 0.06
    # identity-anchor bonus
    anchor_base_bonus: float = 0.12
    self_anchor_bonus_val: float = 0.04
    # anchor top-k dominance cap
    anchor_topk: int = 3
    anchor_rest_mult: float = 0.35
    anchor_full_boost_eids: FrozenSet[int] = field(default_factory=frozenset)

    @classmethod
    def from_env(
        cls,
        agent_id: str,
        canonical_step: int,
        affect_personal: bool,
        q_affect_tag: str,
        q_affect_conf: float,
        spiral_neg_recent: int,
        anchor_full_boost_eids: FrozenSet[int] = frozenset(),
    ) -> "ContinuityContext":
        """Build from environment variables + caller-supplied values."""
        def _env_float(key: str, default: str) -> float:
            try:
                return float(os.getenv(key, default))
            except Exception:
                return float(default)

        def _env_int(key: str, default: str) -> int:
            try:
                return int(os.getenv(key, default))
            except Exception:
                return int(default)

        def _env_bool(key: str, default: str) -> bool:
            try:
                return str(os.getenv(key, default)).strip().lower() not in ("0", "false", "no")
            except Exception:
                return True

        return cls(
            agent_id=agent_id,
            canonical_step=canonical_step,
            affect_personal=affect_personal,
            q_affect_tag=q_affect_tag,
            q_affect_conf=q_affect_conf,
            affect_match_bonus=_env_float("TORMENT_AFFECT_MATCH_BONUS", "0.05"),
            affect_min_conf=_env_float("TORMENT_AFFECT_MIN_CONF", "0.40"),
            thread_window_steps=_env_int("TORMENT_THREAD_WINDOW_STEPS", "50"),
            thread_window_bonus=_env_float("TORMENT_THREAD_WINDOW_BONUS", "0.08"),
            mood_drift_bonus=_env_float("TORMENT_MOOD_DRIFT_QUERY_BONUS", "0.04"),
            spiral_enable=_env_bool("TORMENT_MOOD_SPIRAL_ENABLE", "1"),
            spiral_neg_recent=spiral_neg_recent,
            spiral_min_drifts=_env_int("TORMENT_MOOD_SPIRAL_MIN_NEG_DRIFTS", "2"),
            spiral_older_than=_env_int("TORMENT_MOOD_SPIRAL_OLDER_THAN_STEPS", "250"),
            spiral_window=_env_int("TORMENT_MOOD_SPIRAL_WINDOW_STEPS", "800"),
            spiral_penalty_max=_env_float("TORMENT_MOOD_SPIRAL_PENALTY_MAX", "0.08"),
            self_thread_bonus_val=_env_float("TORMENT_SELF_MEMORY_BONUS", "0.06"),
            anchor_base_bonus=0.12,
            self_anchor_bonus_val=_env_float("TORMENT_SELF_ANCHOR_BONUS", "0.04"),
            anchor_topk=_env_int("TORMENT_ANCHOR_BOOST_TOPK", "3"),
            anchor_rest_mult=_env_float("TORMENT_ANCHOR_BOOST_REST_MULT", "0.35"),
            anchor_full_boost_eids=anchor_full_boost_eids,
        )


@dataclass
class ContinuityResult:
    """Per-hit continuity bonus breakdown."""
    thread_window_bonus: float = 0.0
    affect_match_bonus: float = 0.0
    mood_drift_bonus: float = 0.0
    mood_spiral_penalty: float = 0.0
    self_thread_bonus: float = 0.0
    self_anchor_bonus: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.thread_window_bonus
            + self.affect_match_bonus
            + self.mood_drift_bonus
            - self.mood_spiral_penalty
            + self.self_thread_bonus
            + self.self_anchor_bonus
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "thread_window_bonus": self.thread_window_bonus,
            "affect_match_bonus": self.affect_match_bonus,
            "mood_drift_bonus": self.mood_drift_bonus,
            "mood_spiral_penalty": self.mood_spiral_penalty,
            "self_thread_bonus": self.self_thread_bonus,
            "self_anchor_bonus": self.self_anchor_bonus,
        }


def compute_continuity_bonuses(
    hit: Dict[str, Any],
    ctx: ContinuityContext,
    *,
    is_tool_result: bool = False,
) -> ContinuityResult:
    """Compute all continuity-related type_bonus adjustments for a hit.

    This is a pure function — no side effects, no I/O, no graph access.
    Used by both ``query()`` and ``trace()`` to ensure parity.

    Args:
        hit: dict with at least: scope, agent_id, step, type, affect_tag,
            affect_conf, eid
        ctx: pre-computed per-query continuity context
        is_tool_result: True if the hit has tool_result provenance (excluded
            from self-thread and thread-window bonus, matching query() behavior)
    """
    r = ContinuityResult()

    hit_scope = str(hit.get("scope", ""))
    hit_agent = str(hit.get("agent_id", ""))
    mtype = str(hit.get("type") or "")
    is_own_private = (
        hit_scope == "private"
        and hit_agent == ctx.agent_id
        and not is_tool_result
    )

    # --- Self-thread bonus ---
    if is_own_private and ctx.self_thread_bonus_val > 0.0:
        r.self_thread_bonus = ctx.self_thread_bonus_val

    # --- Identity-anchor bonus ---
    if mtype == "identity_anchor":
        _ab = ctx.anchor_base_bonus
        # Top-k dominance cap: reduce bonus for non-top anchors
        try:
            _eid = int(hit.get("eid", -1))
        except Exception:
            _eid = -1
        if ctx.anchor_full_boost_eids and _eid not in ctx.anchor_full_boost_eids:
            _ab = float(_ab) * float(ctx.anchor_rest_mult)
        r.self_anchor_bonus = float(_ab)
        # Additional lift when anchor belongs to querying agent's private thread
        if hit_scope == "private" and hit_agent == ctx.agent_id:
            r.self_anchor_bonus += ctx.self_anchor_bonus_val

    # --- Thread-window bonus ---
    if (
        ctx.thread_window_steps > 0
        and ctx.thread_window_bonus > 0.0
        and is_own_private
    ):
        try:
            hit_step = int(hit.get("step", -1))
        except Exception:
            hit_step = -1
        if ctx.canonical_step >= 0 and hit_step >= 0:
            delta = max(0, ctx.canonical_step - hit_step)
            if delta <= ctx.thread_window_steps:
                r.thread_window_bonus = ctx.thread_window_bonus * (
                    1.0 - (float(delta) / float(max(1, ctx.thread_window_steps)))
                )

    # --- Affect-match bonus ---
    if (
        ctx.affect_personal
        and ctx.q_affect_tag
        and ctx.q_affect_tag != "neutral"
        and ctx.q_affect_conf >= ctx.affect_min_conf
    ):
        try:
            h_tag = str(hit.get("affect_tag") or "")
            h_conf = float(hit.get("affect_conf") or 0.0)
        except Exception:
            h_tag, h_conf = "", 0.0
        if h_tag and h_tag == ctx.q_affect_tag and h_conf >= ctx.affect_min_conf:
            r.affect_match_bonus = ctx.affect_match_bonus * float(min(ctx.q_affect_conf, h_conf))

        # --- Mood-drift bonus ---
        if ctx.affect_personal and str(hit.get("type")) == "mood_drift":
            r.mood_drift_bonus = ctx.mood_drift_bonus

        # --- Mood-spiral penalty ---
        if ctx.spiral_enable and ctx.spiral_neg_recent >= ctx.spiral_min_drifts:
            _neg = {"stressed", "sad", "angry"}
            try:
                _ht = str(hit.get("affect_tag") or "")
                _hs = int(hit.get("step", -1))
            except Exception:
                _ht, _hs = "", -1
            if _ht in _neg and _hs >= 0 and ctx.canonical_step >= 0:
                _age = max(0, ctx.canonical_step - _hs)
                if _age > ctx.spiral_older_than:
                    _age_fac = min(1.0, float(_age - ctx.spiral_older_than) / float(max(1, ctx.spiral_window)))
                    _trend_fac = min(1.0, 0.5 + 0.25 * float(ctx.spiral_neg_recent - ctx.spiral_min_drifts + 1))
                    r.mood_spiral_penalty = float(ctx.spiral_penalty_max) * _age_fac * _trend_fac

    return r
