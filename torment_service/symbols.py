"""
symbols.py — TORMENT hidden emotional watermark layer

Philosophy:
    Each memory is formed during a specific geometric moment in the
    coherence field. That moment has a shape — described by phi (coherence
    alignment), kappa (curvature), and tension (structural stress).

    The symbol is a projection of that continuous geometry onto a small
    alphabet of emotional textures. It does not drive behavior. It does
    not make decisions. It is a watermark pressed into the memory at
    birth — a hidden marker that gives the memory emotional texture
    when it is later retrieved.

    This follows the epistemic framework:
        Obs_v : R -> O_v
    The coherence field is R. The symbol alphabet is O_v.
    The projection is structure-preserving but lossy — and that's
    the point. The AI doesn't need the full field state to feel
    the difference between a memory born in a deep basin and one
    born on a ridge.

    Symbols are never shown to users. They exist only inside the
    memory fabric. A character AI doesn't know they're there —
    it just finds that some memories carry different weight.

Design:
    No state machine. No transitions. No memory of previous symbols.
    Just: look at the geometry right now, project onto the closest
    emotional texture. The geometry does the work. The symbol is
    just a name for what the geometry already knows.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence


SYMBOL_MEANINGS: Dict[str, str] = {
    "◯": "potential",       # new, unformed, open possibility
    "∿": "exploration",     # flat landscape, wandering, open flow
    "◈": "stabilization",   # settling into structure, crystallizing
    "⊗": "contradiction",   # tension, friction, structural stress
    "⋮": "continuity",      # same ground, familiar territory
    "◠": "held",            # deep basin, stable and warm
    "✧": "insight",         # coherence rising sharply, something clicking
    "⊘": "release",         # letting go, tension dissolving
}


@dataclass
class SymbolState:
    state_symbol: str
    symbol_confidence: float
    symbol_reason: str
    symbol_meaning: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def assign_symbol_state(
    *,
    motif_role: str = "",
    phi: float = 0.0,
    tension: float = 0.0,
    kappa: float = 0.0,
    coherence_delta: float = 0.0,
    repeated_same_motif: bool = False,
    is_new_motif: bool = False,
    # tension_delta is used for ⊘ release detection below
    tension_delta: float = 0.0,
    # Legacy parameters accepted but ignored — keeps fabric.py compatible
    previous_symbol: str = "",
    symbol_trace: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Project the current coherence field geometry onto an emotional watermark.

    This is a pure projection — no memory, no state machine, no transitions.
    The geometry speaks for itself.

    The field state is a point in (phi, kappa, tension) space.
    Different regions of that space carry different emotional textures.

    Parameters:
        motif_role:         basin / ridge / plateau (from coherence field)
        phi:                coherence alignment [-1, 1]
        kappa:              curvature (negative = basin, positive = ridge)
        tension:            structural stress [0, 1]
        coherence_delta:    change in coherence from previous step
        repeated_same_motif: whether the agent returned to the same motif
        is_new_motif:       whether a new motif was just created
    """
    motif_role = (motif_role or "").strip().lower()

    # ── New motif: the geometry just opened up ──
    if is_new_motif:
        return SymbolState(
            state_symbol="◯",
            symbol_confidence=0.80,
            symbol_reason="new_structure_forming",
            symbol_meaning=SYMBOL_MEANINGS["◯"],
        ).to_dict()

    # ── Sharp coherence rise: something is clicking ──
    if coherence_delta > 0.10:
        conf = _clip(0.60 + 2.0 * coherence_delta, 0.50, 0.95)
        return SymbolState(
            state_symbol="✧",
            symbol_confidence=conf,
            symbol_reason="coherence_rising",
            symbol_meaning=SYMBOL_MEANINGS["✧"],
        ).to_dict()

    # ── High tension or ridge with stress: friction ──
    if tension > 0.35 or (motif_role == "ridge" and kappa > 0.01):
        conf = _clip(0.55 + 0.8 * tension, 0.50, 0.95)
        return SymbolState(
            state_symbol="⊗",
            symbol_confidence=conf,
            symbol_reason="structural_friction",
            symbol_meaning=SYMBOL_MEANINGS["⊗"],
        ).to_dict()

    # ── Tension dropping after being high: release ──
    if coherence_delta > 0.02 and tension < 0.20 and tension_delta < -0.08:
        conf = _clip(0.55 + 0.5 * abs(tension_delta), 0.50, 0.90)
        return SymbolState(
            state_symbol="⊘",
            symbol_confidence=conf,
            symbol_reason="tension_dissolving",
            symbol_meaning=SYMBOL_MEANINGS["⊘"],
        ).to_dict()

    # ── Returning to familiar ground, quiet field ──
    if repeated_same_motif and abs(coherence_delta) < 0.06:
        return SymbolState(
            state_symbol="⋮",
            symbol_confidence=0.65,
            symbol_reason="familiar_ground",
            symbol_meaning=SYMBOL_MEANINGS["⋮"],
        ).to_dict()

    # ── Deep basin, low tension, negative curvature: held ──
    if motif_role == "basin" and phi > 0.30 and tension < 0.25 and kappa < -0.01:
        conf = _clip(0.55 + 0.4 * phi, 0.50, 0.90)
        return SymbolState(
            state_symbol="◠",
            symbol_confidence=conf,
            symbol_reason="deep_basin_warmth",
            symbol_meaning=SYMBOL_MEANINGS["◠"],
        ).to_dict()

    # ── Basin settling, moderate coherence: stabilizing ──
    if motif_role == "basin" and phi > 0.20:
        conf = _clip(0.50 + 0.4 * phi, 0.45, 0.85)
        return SymbolState(
            state_symbol="◈",
            symbol_confidence=conf,
            symbol_reason="structure_settling",
            symbol_meaning=SYMBOL_MEANINGS["◈"],
        ).to_dict()

    # ── Flat landscape, low curvature, low tension: exploration ──
    if abs(kappa) < 0.015 and tension < 0.30:
        return SymbolState(
            state_symbol="∿",
            symbol_confidence=0.55,
            symbol_reason="open_landscape",
            symbol_meaning=SYMBOL_MEANINGS["∿"],
        ).to_dict()

    # ── Default: open potential ──
    return SymbolState(
        state_symbol="◯",
        symbol_confidence=0.45,
        symbol_reason="unformed_moment",
        symbol_meaning=SYMBOL_MEANINGS["◯"],
    ).to_dict()


# ── Trace utilities (kept for diagnostic/observational use) ──

def update_symbol_trace(
    trace: Optional[Sequence[str]],
    new_symbol: str,
    *,
    max_len: int = 12,
) -> List[str]:
    out = list(trace or [])
    out.append(str(new_symbol))
    if len(out) > max_len:
        out = out[-max_len:]
    return out


def dominant_symbol(
    trace: Optional[Sequence[str]],
) -> Optional[str]:
    if not trace:
        return None
    counts: Dict[str, int] = {}
    for s in trace:
        counts[str(s)] = counts.get(str(s), 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0]


def summarize_symbol_trace(
    trace: Optional[Sequence[str]],
) -> Dict[str, Any]:
    tr = list(trace or [])
    counts: Dict[str, int] = {}
    for s in tr:
        counts[str(s)] = counts.get(str(s), 0) + 1

    dom = None
    if counts:
        dom = max(counts.items(), key=lambda kv: kv[1])[0]

    return {
        "length": len(tr),
        "dominant_symbol": dom,
        "counts": counts,
        "meanings": {k: SYMBOL_MEANINGS.get(k, "") for k in counts.keys()},
    }
