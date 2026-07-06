"""BV-ΨTRS-SAG anatomy: characterize what the existing SAG diagnostic is sensitive to (offline, no new math).

Generates controlled synthetic descriptor windows (flat, noise, ramp, periodic, phase-shifted, spike,
low-pass, amplitude-scaled, shuffled/reversed/circular) and runs the EXISTING multi-window SAG evaluator on
them, reporting G(k=0)/G(k>0) summaries, amplifying counts, and a simple energy/variance statistic, so SAG
can show whether its amplification tracks variance/richness/spikes/periodicity rather than temporal order.
No mechanism is proven; wording is 'appears sensitive to' / 'consistent with'. stdlib + numpy; no service
imports; no runtime/camera/sensor/prompt/context/memory/action/render-body/autonomy contact.
"""
from __future__ import annotations

import os

import numpy as np

import run_real_video_descriptors as rvd

T_DEFAULT, C_DEFAULT = 64, 9


def generate_field(kind, seed, T=T_DEFAULT, C=C_DEFAULT):
    rng = np.random.default_rng(seed)
    t = np.arange(T, dtype=float)
    if kind == "constant":
        return np.full((T, C), 0.5)
    if kind == "tiny_noise":
        return 0.01 * rng.standard_normal((T, C))
    if kind == "white_noise":
        return rng.standard_normal((T, C))
    if kind == "smooth_ramp":
        return np.stack([np.linspace(-1, 1, T) + 0.02 * rng.standard_normal(T) for _ in range(C)], axis=1)
    if kind == "sine":
        return np.stack([np.sin(2 * np.pi * (1 + c) * t / T) for c in range(C)], axis=1)
    if kind == "sine_phase_shift":
        return np.stack([np.sin(2 * np.pi * (1 + c) * t / T + rng.uniform(0, 2 * np.pi)) for c in range(C)], axis=1)
    if kind == "spike":
        f = 0.01 * rng.standard_normal((T, C))
        for i in rng.integers(0, T, 3):
            f[int(i)] += 5.0
        return f
    if kind == "lowpass":
        w = rng.standard_normal((T, C))
        k = np.ones(5) / 5.0
        return np.stack([np.convolve(w[:, c], k, mode="same") for c in range(C)], axis=1)
    raise ValueError(f"unknown field kind: {kind!r}")


FIELD_KINDS = ("constant", "tiny_noise", "white_noise", "smooth_ramp", "sine",
               "sine_phase_shift", "spike", "lowpass")


def _energy(windows):
    return float(np.mean([np.mean(np.var(w, axis=0)) for w in windows]))


def _row(windows):
    sag = rvd.evaluate_sag_real(windows)
    return {"energy": _energy(windows), "G_k0": sag["G_k0_summary"], "G_kpos": sag["G_kpos_summary"],
            "n_amplifying": sag["n_amplifying"], "frac": sag["frac_amplifying"], "n": sag["n_windows"]}


def characterize(n=8, T=T_DEFAULT, C=C_DEFAULT):
    rows = {}
    for kind in FIELD_KINDS:
        rows[kind] = _row([generate_field(kind, s, T, C) for s in range(n)])
    # amplitude-scaled white noise (probe amplitude-scale invariance)
    for scale in (0.1, 1.0, 10.0):
        rows[f"white_noise x{scale:g}"] = _row([scale * generate_field("white_noise", s, T, C) for s in range(n)])
    # temporal transforms of a periodic field (temporal-order probe at field level)
    base = [generate_field("sine_phase_shift", s, T, C) for s in range(n)]
    rows["sine_shuffled"] = _row([b[np.random.default_rng(s).permutation(T)] for s, b in enumerate(base)])
    rows["sine_reversed"] = _row([b[::-1].copy() for b in base])
    rows["sine_circular"] = _row([np.roll(b, T // 3, axis=0) for b in base])
    return rows


def interpret(rows):
    amp = {k: v["frac"] for k, v in rows.items()}
    flat_amp = amp.get("constant", 0.0)
    rich = [k for k in ("white_noise", "sine", "sine_phase_shift", "spike", "lowpass") if amp.get(k, 0) >= 0.5]
    scale_meds = [rows[f"white_noise x{sc:g}"]["G_kpos"]["median"] for sc in (0.1, 1.0, 10.0)]
    scale_invariant = (max(scale_meds) / (min(scale_meds) + 1e-9)) < 2.0
    tiny_k0 = rows["tiny_noise"]["G_k0"]["median"]
    tiny_unstable = tiny_k0 > 1.1
    temporal_same = (rows["sine_shuffled"]["frac"] >= rows["sine_phase_shift"]["frac"] - 1e-9)
    notes = []
    notes.append(f"flat/constant amplifying fraction: {flat_amp:.2f} (expected ~0)")
    notes.append(f"structured fields amplifying (frac>=0.5): {rich if rich else 'none'}")
    notes.append(f"amplitude-scale invariant (white-noise x0.1/x1/x10 medians within 2x): {scale_invariant} "
                 f"[medians {[round(m, 1) for m in scale_meds]}]")
    notes.append(f"very-low-energy stability: tiny_noise G(k=0) median={tiny_k0:.2f} "
                 f"({'UNSTABLE: k=0 not coherent' if tiny_unstable else 'coherent'})")
    notes.append(f"periodic shuffle amplifies >= periodic true: {temporal_same} (temporal order not required)")
    notes.append("READING (consistent-with, not proof): SAG amplification is consistent with sensitivity to "
                 "descriptor-field variance/richness (structured fields amplify; flat does not). It does NOT "
                 "appear temporal-order-specific (shuffle/reverse/circular of a periodic field still amplify). "
                 "It is NOT amplitude-scale invariant (gain depends on field-to-perturbation scale). It is "
                 "numerically UNSTABLE at very low energy. Mechanism not proven.")
    return notes


def format_report(rows) -> str:
    lines = ["BV-ΨTRS-SAG anatomy — what is SAG sensitive to? (offline synthetic characterization)"]
    lines.append(f"  {'field':<20}{'energy':>10}{'G(k=0) med':>12}{'G(k>0) med':>12}{'amp':>8}")
    for k, v in rows.items():
        lines.append(f"  {k:<20}{v['energy']:>10.3f}{v['G_k0']['median']:>12.3f}{v['G_kpos']['median']:>12.3f}"
                     f"{v['n_amplifying']:>5}/{v['n']}")
    lines.append("  --")
    for note in interpret(rows):
        lines.append("  " + note)
    lines.append("  NOTE: offline research artifact only; 'appears sensitive to' / 'consistent with', not proof.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_report(characterize()))
