"""
resonance.py — TORMENT symbolic resonance loops v2

v2 changes:
    - Richer loop classification with more granular categories
    - Cycle detection: find actual repeating subsequences (not just set membership)
    - Transition entropy: measure diversity of transitions (low = habitual, high = chaotic)
    - Attractor detection: when a 2-3 symbol cycle repeats, flag it as an attractor candidate
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple
import math


VALID_SYMBOLS = {"◯", "∿", "◈", "⊗", "⋮", "◠", "✧", "⊘"}


def normalize_trace(trace: Optional[Sequence[str]], max_len: int = 12) -> List[str]:
    out: List[str] = []
    for s in list(trace or []):
        s = str(s)
        if s in VALID_SYMBOLS:
            out.append(s)
    if len(out) > max_len:
        out = out[-max_len:]
    return out


def append_symbol(trace: Optional[Sequence[str]], symbol: str, max_len: int = 12) -> List[str]:
    out = normalize_trace(trace, max_len=max_len)
    s = str(symbol)
    if s in VALID_SYMBOLS:
        out.append(s)
    if len(out) > max_len:
        out = out[-max_len:]
    return out


def transition_counts(trace: Optional[Sequence[str]]) -> Dict[str, int]:
    tr = normalize_trace(trace)
    counts: Dict[str, int] = {}
    for a, b in zip(tr[:-1], tr[1:]):
        k = f"{a}->{b}"
        counts[k] = counts.get(k, 0) + 1
    return counts


def resonance_score(trace: Optional[Sequence[str]]) -> float:
    """Concentration of transitions — high = few dominant transitions (habitual),
    low = many different transitions (chaotic/exploratory)."""
    counts = transition_counts(trace)
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    sq = sum(v * v for v in counts.values())
    return float(sq / float(total * total))


def transition_entropy(trace: Optional[Sequence[str]]) -> float:
    """Shannon entropy of transition distribution, normalized to [0,1].

    0.0 = perfectly habitual (one transition dominates)
    1.0 = maximally diverse (all transitions equally likely)
    """
    counts = transition_counts(trace)
    total = sum(counts.values())
    if total <= 1:
        return 0.0
    probs = [v / total for v in counts.values()]
    H = -sum(p * math.log(p) for p in probs if p > 0)
    # Normalize by log of number of unique transitions
    n_unique = len(counts)
    if n_unique <= 1:
        return 0.0
    return float(H / math.log(n_unique))


def dominant_transition(trace: Optional[Sequence[str]]) -> Optional[Tuple[str, str]]:
    counts = transition_counts(trace)
    if not counts:
        return None
    k = max(counts.items(), key=lambda kv: kv[1])[0]
    a, b = k.split("->", 1)
    return (a, b)


def find_cycles(trace: Optional[Sequence[str]], min_len: int = 2, max_len: int = 4) -> List[Dict[str, Any]]:
    """Detect repeating subsequences in the trace.

    Returns a list of found cycles, each with:
        pattern: list of symbols forming the cycle
        count: how many times it repeats consecutively
        start: index where the cycle begins
    """
    tr = normalize_trace(trace)
    if len(tr) < min_len * 2:
        return []

    found: List[Dict[str, Any]] = []

    for cycle_len in range(min_len, max_len + 1):
        for start in range(len(tr) - cycle_len):
            pattern = tr[start:start + cycle_len]
            repeats = 1
            pos = start + cycle_len
            while pos + cycle_len <= len(tr):
                if tr[pos:pos + cycle_len] == pattern:
                    repeats += 1
                    pos += cycle_len
                else:
                    break
            if repeats >= 2:
                already = False
                for f in found:
                    if f["start"] <= start and f["start"] + len(f["pattern"]) * f["count"] >= start + cycle_len * repeats:
                        already = True
                        break
                if not already:
                    found.append({
                        "pattern": pattern,
                        "count": repeats,
                        "start": start,
                    })

    found.sort(key=lambda c: c["count"] * len(c["pattern"]), reverse=True)
    return found


def loop_type(trace: Optional[Sequence[str]]) -> str:
    """Classify the overall resonance pattern of the trace.

    Categories:
        constructive: insight appears alongside stabilization/continuity/held
        recovery: tension -> release -> potential/exploration pattern
        tension: persistent contradiction without resolution
        exploratory: mostly potential/exploration symbols
        habitual: a short cycle repeats 3+ times (attractor candidate)
        deepening: progression toward held/stabilized states
        mixed: no clear pattern
    """
    tr = normalize_trace(trace)
    if len(tr) < 2:
        return "mixed"

    has = set(tr)

    # Check for habitual cycles (attractor candidates)
    cycles = find_cycles(tr, min_len=2, max_len=3)
    for c in cycles:
        if c["count"] >= 3:
            return "habitual"

    # Constructive: insight + structure
    if "✧" in has and (("◈" in has) or ("⋮" in has) or ("◠" in has)):
        return "constructive"

    # Recovery: ⊗ -> ⊘ -> (◯ or ∿)
    for i in range(len(tr) - 2):
        if tr[i] == "⊗" and tr[i + 1] == "⊘" and tr[i + 2] in ("◯", "∿"):
            return "recovery"

    # Tension: persistent contradiction
    if tr.count("⊗") >= 2 and "◈" not in has and "✧" not in has:
        return "tension"

    # Deepening: progression toward stability
    stable_symbols = {"◈", "◠", "⋮"}
    if len(tr) >= 4:
        head = tr[: len(tr) // 2]
        tail = tr[len(tr) // 2:]
        head_stable = sum(1 for s in head if s in stable_symbols)
        tail_stable = sum(1 for s in tail if s in stable_symbols)
        if tail_stable > head_stable and tail_stable >= 2:
            return "deepening"

    # Exploratory: mostly open symbols
    exploratory_n = sum(1 for s in tr if s in ("◯", "∿"))
    if exploratory_n >= max(2, len(tr) // 2):
        return "exploratory"

    return "mixed"


def phase_shift(prev_trace: Optional[Sequence[str]], new_trace: Optional[Sequence[str]]) -> bool:
    lt0 = loop_type(prev_trace)
    lt1 = loop_type(new_trace)
    if lt0 == "mixed" and lt1 == "mixed":
        return False
    return lt0 != lt1


def summarize_resonance(
    trace: Optional[Sequence[str]],
    prev_trace: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    tr = normalize_trace(trace)
    dom = dominant_transition(tr)
    cycles = find_cycles(tr)

    return {
        "symbol_trace": tr,
        "resonance_score": resonance_score(tr),
        "transition_entropy": transition_entropy(tr),
        "loop_type": loop_type(tr),
        "phase_shift": bool(phase_shift(prev_trace, tr)),
        "dominant_transition": list(dom) if dom is not None else None,
        "transition_counts": transition_counts(tr),
        "cycles": cycles[:3] if cycles else [],
    }
