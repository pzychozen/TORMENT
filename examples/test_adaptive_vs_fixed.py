# -*- coding: utf-8 -*-
"""
Fixed vs Adaptive DISP_SCALE — Side-by-Side Simulation
=======================================================
Runs the SAME ingest sequence through two kernel configurations:
  A) Fixed DISP_SCALE = 1.5  (current production)
  B) Adaptive DISP_SCALE     (proposed, k=2.0)

Both use the same embedder (ST if available, else Hash).
Reports: disp, coherence, deltas, symbol assignments, packet eligibility,
write-gate outcomes, and overall statistics.

Usage:
    set TORMENT_EMBED_PROVIDER=st
    set TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
    set TORMENT_EMBED_DEVICE=cpu
    python examples/test_adaptive_vs_fixed.py
"""
import os
import sys
from collections import Counter
from dataclasses import dataclass
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from torment_service.memory_kernel import TriOctaMemoryKernel
from torment_service.kernel.model_core import ModelParams
from torment_service.symbols import assign_symbol_state


# ─────────────────────────────────────────────────────
# Adaptive DISP_SCALE implementation (self-contained)
# ─────────────────────────────────────────────────────
class AdaptiveKernel(TriOctaMemoryKernel):
    """TriOctaMemoryKernel with adaptive DISP_SCALE.

    Overrides _dispersion_coherence to track a rolling window of
    dispersion values and compute the scale from the distribution.
    """

    def __init__(self, *args, sensitivity: float = 2.0, window: int = 50,
                 warmup: int = 10, fallback: float = 1.50, **kwargs):
        super().__init__(*args, **kwargs)
        self._disp_buffer: List[float] = []
        self._sensitivity = sensitivity      # k multiplier
        self._window = window                # rolling window size
        self._warmup = warmup                # steps before full adaptive
        self._fallback = fallback            # fixed scale during warmup

    def _effective_disp_scale(self, disp: float) -> float:
        buf = self._disp_buffer
        buf.append(disp)
        if len(buf) > self._window:
            buf.pop(0)

        n = len(buf)
        if n < 2:
            self._last_effective_scale = self._fallback
            return self._fallback

        mu = float(np.mean(buf))
        sigma = float(np.std(buf))
        adaptive = self._sensitivity * (mu + sigma)

        # Smooth blend from fallback to adaptive
        alpha = min(1.0, n / self._warmup)
        effective = (1.0 - alpha) * self._fallback + alpha * adaptive

        effective = max(effective, 1e-6)
        # Clamp to sane range
        effective = min(effective, 10.0)
        self._last_effective_scale = effective
        return effective

    def _dispersion_coherence(self, Omega):
        ph = np.angle(Omega)
        d01 = float((float(ph[0] - ph[1]) + np.pi) % (2 * np.pi) - np.pi)
        d12 = float((float(ph[1] - ph[2]) + np.pi) % (2 * np.pi) - np.pi)
        d20 = float((float(ph[2] - ph[0]) + np.pi) % (2 * np.pi) - np.pi)
        disp = float(np.sqrt(np.mean(np.square([d01, d12, d20]))))

        scale = self._effective_disp_scale(disp)
        coh_phase = float(np.exp(-((disp / max(scale, 1e-12)) ** 2)))
        return disp, coh_phase


# ─────────────────────────────────────────────────────
# Test data — same texts as agents.py
# ─────────────────────────────────────────────────────
INGEST_TEXTS = [
    ("atlas",  "research",    "Atlas round1: Memory governance reliability depends on provenance retention, contamination resistance, drift stability, and decision consistency."),
    ("vanta",  "research",    "Vanta round1: Memory governance reliability can fail through provenance loss, contamination, drift instability, and false decision consistency."),
    ("raven",  "engineering", "Raven round1: Build evaluation for memory governance reliability with provenance logs, contamination checks, drift monitoring, and decision consistency scoring."),
    ("atlas",  "research",    "Atlas round2: Compare governed memory versus unguided memory using provenance retention, contamination resistance, drift stability, and decision consistency."),
    ("vanta",  "research",    "Vanta round2: Test whether governed memory versus unguided memory changes provenance retention, contamination resistance, drift stability, and decision consistency."),
    ("raven",  "engineering", "Raven round2: Implement baseline versus governed memory runs and log provenance retention, contamination resistance, drift stability, and decision consistency."),
    ("atlas",  "research",    "Atlas round3: Longitudinal evaluation should measure whether memory governance improves provenance retention, contamination resistance, drift stability, and decision consistency over time."),
    ("vanta",  "research",    "Vanta round3: Longitudinal evaluation must detect whether lower variance hides worse provenance retention, contamination resistance, drift stability, or decision consistency."),
    ("raven",  "engineering", "Raven round3: Produce dashboards for provenance retention, contamination resistance, drift stability, and decision consistency across governed and unguided memory runs."),
]

# Bonus: add some dissimilar texts to test how each handles topic shifts
BONUS_TEXTS = [
    ("atlas",  "research",    "Atlas bonus: The weather forecast suggests rain tomorrow with temperatures dropping to 5 degrees celsius."),
    ("vanta",  "research",    "Vanta bonus: Quantum computing leverages superposition and entanglement to solve problems intractable for classical machines."),
    ("raven",  "engineering", "Raven bonus: The ancient Egyptians built the pyramids using limestone blocks weighing up to 80 tonnes each."),
]

ALL_TEXTS = INGEST_TEXTS + BONUS_TEXTS

COH_THRESHOLD = 0.15
WRITE_THRESHOLD = 0.55


# ─────────────────────────────────────────────────────
# Simulation runner
# ─────────────────────────────────────────────────────
@dataclass
class StepResult:
    agent: str
    domain: str
    text_short: str
    disp: float
    coh_phase: float
    coh_raw: float
    coh_ema: float
    coh_delta: float
    strength: float
    stored: bool
    packet_eligible: bool
    symbol: str
    symbol_reason: str
    effective_scale: float


def _suppress_prints():
    """Context manager to suppress kernel debug prints during simulation."""
    import io, contextlib
    return contextlib.redirect_stdout(io.StringIO())


def run_simulation(kernel: TriOctaMemoryKernel, label: str) -> List[StepResult]:
    """Run all texts through a kernel, return per-step results."""
    with _suppress_prints():
        state = kernel.init_state("boot")
    results = []
    prev_coh = None

    for agent, domain, text in ALL_TEXTS:
        with _suppress_prints():
            state, signals, debug = kernel.process(state, text)

        coh = debug["coherence"]
        disp = debug["phase_disp"]
        coh_phase = debug["coh_phase"]
        coh_raw = debug["coh_raw"]
        delta = coh - prev_coh if prev_coh is not None else 0.0
        prev_coh = coh

        strength = float(np.clip(0.40 + 0.60 * coh, 0.0, 1.0))
        stored = strength >= WRITE_THRESHOLD
        packet_eligible = coh >= COH_THRESHOLD

        # Compute symbol (simplified — just coherence_delta driven)
        sym = assign_symbol_state(coherence_delta=delta)
        symbol = sym.get("state_symbol", "?")
        reason = sym.get("symbol_reason", "?")

        # Get effective scale (adaptive kernel exposes it)
        if hasattr(kernel, "_last_effective_scale"):
            eff_scale = kernel._last_effective_scale
        else:
            eff_scale = kernel.DISP_SCALE

        results.append(StepResult(
            agent=agent,
            domain=domain,
            text_short=text[:50],
            disp=disp,
            coh_phase=coh_phase,
            coh_raw=coh_raw,
            coh_ema=coh,
            coh_delta=delta,
            strength=strength,
            stored=stored,
            packet_eligible=packet_eligible,
            symbol=symbol,
            symbol_reason=reason,
            effective_scale=eff_scale,
        ))

    return results


def print_results(label: str, results: List[StepResult]):
    """Print per-step table and summary."""
    print(f"\n{'=' * 120}")
    print(f"  {label}")
    print(f"{'=' * 120}")

    print(f"{'#':>2} {'Agent':<6} {'Text':<50} {'disp':>6} {'scale':>6} {'coh':>6} {'delta':>7} {'str':>5} {'stor':>4} {'pkt':>3} {'sym':>2} {'reason':<20}")
    print("-" * 120)

    for i, r in enumerate(results):
        marker = ""
        if r.coh_delta > 0.10:
            marker = "**"
        elif abs(r.coh_delta) > 0.02:
            marker = "*"

        print(f"{i+1:2d} {r.agent:<6} {r.text_short:<50} "
              f"{r.disp:6.3f} {r.effective_scale:6.3f} {r.coh_ema:6.4f} {r.coh_delta:+7.4f}{marker:<2} "
              f"{r.strength:5.3f} {'Y' if r.stored else 'N':>4} {'Y' if r.packet_eligible else 'N':>3} "
              f"{r.symbol:>2} {r.symbol_reason:<20}")


def print_summary(label: str, results: List[StepResult]):
    """Print aggregate statistics."""
    disps = [r.disp for r in results]
    cohs = [r.coh_ema for r in results]
    deltas = [r.coh_delta for r in results[1:]]  # skip first (no delta)
    scales = [r.effective_scale for r in results]
    symbols = Counter(r.symbol for r in results)
    reasons = Counter(r.symbol_reason for r in results)

    stored_count = sum(1 for r in results if r.stored)
    packet_count = sum(1 for r in results if r.packet_eligible)
    insight_count = sum(1 for d in deltas if d > 0.10)
    release_count = sum(1 for d in deltas if 0.02 < abs(d) <= 0.10)

    print(f"\n{'─' * 60}")
    print(f"  SUMMARY: {label}")
    print(f"{'─' * 60}")
    print(f"  Dispersion     min={min(disps):.4f}  max={max(disps):.4f}  mean={np.mean(disps):.4f}")
    print(f"  Eff. scale     min={min(scales):.4f}  max={max(scales):.4f}  mean={np.mean(scales):.4f}")
    print(f"  Coherence      min={min(cohs):.4f}  max={max(cohs):.4f}  mean={np.mean(cohs):.4f}")
    print(f"  Max |delta|    {max(abs(d) for d in deltas):.4f}")
    print(f"  Stored         {stored_count}/{len(results)}")
    print(f"  Packets        {packet_count}/{len(results)}")
    print(f"  Insight (d>0.10)  {insight_count}")
    print(f"  Release (d>0.02)  {release_count}")
    print(f"  Symbols: ", end="")
    for sym in ["◯", "∿", "◈", "⊗", "⋮", "◠", "✧", "⊘"]:
        if symbols[sym] > 0:
            print(f"{sym}={symbols[sym]}  ", end="")
    print()
    print(f"  Reasons: ", end="")
    for reason, count in reasons.most_common():
        print(f"{reason}={count}  ", end="")
    print()

    return {
        "label": label,
        "disp_min": min(disps), "disp_max": max(disps), "disp_mean": np.mean(disps),
        "coh_min": min(cohs), "coh_max": max(cohs), "coh_mean": np.mean(cohs),
        "max_delta": max(abs(d) for d in deltas),
        "stored": stored_count, "packets": packet_count,
        "insights": insight_count, "releases": release_count,
        "symbols": dict(symbols),
        "scale_min": min(scales), "scale_max": max(scales),
    }


def main():
    # ── Embedder setup ──
    embedder = None
    embedder_name = "HashEmbedding"
    try:
        if os.environ.get("TORMENT_EMBED_PROVIDER", "hash") == "st":
            from torment_service.embeddings import STEmbedding
            model = os.environ.get("TORMENT_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
            device = os.environ.get("TORMENT_EMBED_DEVICE", "cpu")
            embedder = STEmbedding(model=model, device=device)
            embedder_name = f"STEmbedding ({model})"
            print(f"[INFO] Using {embedder_name}")
        else:
            print("[INFO] Using HashEmbedding (set TORMENT_EMBED_PROVIDER=st for production)")
    except Exception as e:
        print(f"[INFO] ST load failed ({e}), using HashEmbedding")

    print(f"[INFO] {len(ALL_TEXTS)} texts ({len(INGEST_TEXTS)} core + {len(BONUS_TEXTS)} bonus/diverse)")
    print(f"[INFO] COH_THRESHOLD={COH_THRESHOLD}, WRITE_THRESHOLD={WRITE_THRESHOLD}")

    # Suppress kernel init/debug prints during kernel creation
    with _suppress_prints():
        # ── Run A: Fixed DISP_SCALE = 1.5 ──
        kernel_fixed = TriOctaMemoryKernel(params=ModelParams(), embedder=embedder)
        kernel_fixed.DISP_SCALE = 1.50
        kernel_fixed.COH_SMOOTH = 0.70

    results_fixed = run_simulation(kernel_fixed, "FIXED (DISP_SCALE=1.5)")
    print_results("A) FIXED  DISP_SCALE = 1.5", results_fixed)
    summary_fixed = print_summary("A) FIXED  DISP_SCALE = 1.5", results_fixed)

    with _suppress_prints():
        # ── Run B: Adaptive DISP_SCALE (k=2.0) ──
        kernel_adaptive = AdaptiveKernel(
            params=ModelParams(), embedder=embedder,
            sensitivity=2.0, window=50, warmup=10, fallback=1.50,
        )
        kernel_adaptive.COH_SMOOTH = 0.70

    results_adaptive = run_simulation(kernel_adaptive, "ADAPTIVE (k=2.0)")
    print_results("B) ADAPTIVE  k=2.0", results_adaptive)
    summary_adaptive = print_summary("B) ADAPTIVE  k=2.0", results_adaptive)

    # ── Side-by-side comparison ──
    print(f"\n\n{'=' * 80}")
    print("  SIDE-BY-SIDE COMPARISON")
    print(f"{'=' * 80}")
    print(f"  Embedder: {embedder_name}")
    print()

    metrics = [
        ("Dispersion range",  f"[{summary_fixed['disp_min']:.3f}, {summary_fixed['disp_max']:.3f}]",
                               f"[{summary_adaptive['disp_min']:.3f}, {summary_adaptive['disp_max']:.3f}]"),
        ("Dispersion mean",   f"{summary_fixed['disp_mean']:.4f}",
                               f"{summary_adaptive['disp_mean']:.4f}"),
        ("Eff. scale range",  f"[{summary_fixed['scale_min']:.3f}, {summary_fixed['scale_max']:.3f}]",
                               f"[{summary_adaptive['scale_min']:.3f}, {summary_adaptive['scale_max']:.3f}]"),
        ("Coherence range",   f"[{summary_fixed['coh_min']:.3f}, {summary_fixed['coh_max']:.3f}]",
                               f"[{summary_adaptive['coh_min']:.3f}, {summary_adaptive['coh_max']:.3f}]"),
        ("Coherence mean",    f"{summary_fixed['coh_mean']:.4f}",
                               f"{summary_adaptive['coh_mean']:.4f}"),
        ("Max |coh delta|",   f"{summary_fixed['max_delta']:.4f}",
                               f"{summary_adaptive['max_delta']:.4f}"),
        ("Stored / Total",    f"{summary_fixed['stored']}/{len(results_fixed)}",
                               f"{summary_adaptive['stored']}/{len(results_adaptive)}"),
        ("Packets / Total",   f"{summary_fixed['packets']}/{len(results_fixed)}",
                               f"{summary_adaptive['packets']}/{len(results_adaptive)}"),
        ("Insight events",    f"{summary_fixed['insights']}",
                               f"{summary_adaptive['insights']}"),
        ("Release events",    f"{summary_fixed['releases']}",
                               f"{summary_adaptive['releases']}"),
    ]

    print(f"  {'Metric':<22} {'FIXED (1.5)':>20} {'ADAPTIVE (k=2.0)':>20} {'Verdict':>12}")
    print(f"  {'-'*76}")
    for name, fixed_val, adaptive_val in metrics:
        # Simple verdict
        verdict = ""
        if fixed_val == adaptive_val:
            verdict = "same"
        print(f"  {name:<22} {fixed_val:>20} {adaptive_val:>20} {verdict:>12}")

    # Symbol comparison
    all_syms = set(summary_fixed["symbols"].keys()) | set(summary_adaptive["symbols"].keys())
    print(f"\n  {'Symbol':<10} {'FIXED':>10} {'ADAPTIVE':>10}")
    print(f"  {'-'*32}")
    for sym in ["◯", "∿", "◈", "⊗", "⋮", "◠", "✧", "⊘"]:
        if sym in all_syms:
            f_count = summary_fixed["symbols"].get(sym, 0)
            a_count = summary_adaptive["symbols"].get(sym, 0)
            print(f"  {sym:<10} {f_count:>10} {a_count:>10}")

    # Final assessment
    print(f"\n{'─' * 80}")
    print("  ASSESSMENT")
    print(f"{'─' * 80}")

    coh_range_fixed = summary_fixed["coh_max"] - summary_fixed["coh_min"]
    coh_range_adaptive = summary_adaptive["coh_max"] - summary_adaptive["coh_min"]

    print(f"  Coherence range:   fixed={coh_range_fixed:.4f}  adaptive={coh_range_adaptive:.4f}")

    if coh_range_adaptive > coh_range_fixed * 1.1:
        print("  -> Adaptive produces WIDER coherence range (better signal diversity)")
    elif coh_range_adaptive < coh_range_fixed * 0.9:
        print("  -> Adaptive produces NARROWER coherence range (less variation)")
    else:
        print("  -> Similar coherence range")

    if summary_adaptive["insights"] > summary_fixed["insights"]:
        print("  -> Adaptive produces MORE insight events (symbol system more active)")
    elif summary_adaptive["insights"] < summary_fixed["insights"]:
        print("  -> Adaptive produces FEWER insight events")
    else:
        print("  -> Same insight event count")

    if (summary_adaptive["packets"] < len(results_adaptive) and
            summary_fixed["packets"] == len(results_fixed)):
        print("  -> Adaptive is MORE SELECTIVE (some packets blocked)")
    elif (summary_adaptive["packets"] == summary_fixed["packets"]):
        print("  -> Same packet selectivity")

    # Portability note
    print(f"\n  KEY ADVANTAGE: With adaptive, switching embedders requires NO recalibration.")
    print(f"  The k=2.0 multiplier is dimensionless and embedder-independent.")


if __name__ == "__main__":
    main()
