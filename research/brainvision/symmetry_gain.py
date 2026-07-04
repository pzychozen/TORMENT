"""BV-ΨTRS-SAG: Symmetry Amplification Gain (offline, no service imports).

Tests the recursive-time claim with the TIME papers' own diagnostic instead of classification: evolve two
mirror-perturbed descriptor fields under the ΨTRS internal clock and measure whether a state-dependent
clock (kappa>0) amplifies their separation (symmetry breaking) while a fixed clock (kappa=0) keeps them
coherent (symmetry preserved). The base clock map is non-expanding, so any amplification is attributable
to state-dependent temporality. stdlib + numpy only.

G = max_t ||Theta+(t) - Theta-(t)|| / ||Theta+(0) - Theta-(0)||.
"""
from __future__ import annotations

import numpy as np

import psi_trs

_EPS = 1e-12


def base_field(seed=0, T=64, C=6):
    rng = np.random.default_rng(seed)
    t = np.arange(T, dtype=float)
    cols = []
    for c in range(C):
        cols.append(np.sin(2 * np.pi * (1 + c) * t / T + rng.uniform(0, 1))
                    + 0.4 * np.sin(2 * np.pi * (2 + c) * t / T))
    return np.stack(cols, axis=1)


def paired_trajectories(base, eps=1e-3, seed=0):
    """Return (Theta+, Theta-) = base +/- eps * unit mirror perturbation. Deterministic."""
    rng = np.random.default_rng(seed + 777)
    delta = rng.normal(size=np.asarray(base).shape)
    delta = delta / (np.linalg.norm(delta) + _EPS)
    return base + eps * delta, base - eps * delta


def _step(th, kappa, omega, dt, alpha, x0, L):
    """One ΨTRS clock step: advance the field by the state-dependent internal clock (a bounded
    translation) and renormalize. This base map is NON-expanding, so with a fixed clock (kappa=0) a
    mirror-perturbed pair stays coherent; only a state-dependent clock (kappa>0) can desynchronize it."""
    T = th.shape[0]
    rho = psi_trs.psi_spec(th)                                            # translation/scale invariant
    dphi = omega * dt + kappa * psi_trs.bounded_warp(rho, alpha, x0)      # state-dependent clock increment
    k = np.fft.rfftfreq(T) * T
    F = np.fft.rfft(th, axis=0) * np.exp(-2j * np.pi * k[:, None] * dphi / T)
    th = np.fft.irfft(F, n=T, axis=0)
    return psi_trs.spectral_renormalize(th, L=L)


def evolve(theta0, kappa, omega=1.0, dt=1.0, steps=40, alpha=3.0, x0=None, L=0.7):
    th = np.asarray(theta0, float).copy()
    if x0 is None:
        x0 = psi_trs.psi_spec(th)
    traj = [th.copy()]
    for _ in range(steps):
        th = _step(th, kappa, omega, dt, alpha, x0, L)
        traj.append(th.copy())
    return np.array(traj)


def symmetry_gain(base, kappa, omega=1.0, eps=1e-3, steps=40, seed=0, x0=None, **kw):
    if x0 is None:
        x0 = psi_trs.psi_spec(np.asarray(base, float))
    tp, tm = paired_trajectories(base, eps, seed)
    Tp = evolve(tp, kappa, omega=omega, steps=steps, x0=x0, **kw)
    Tm = evolve(tm, kappa, omega=omega, steps=steps, x0=x0, **kw)
    d = np.linalg.norm((Tp - Tm).reshape(len(Tp), -1), axis=1)
    return float(d.max() / (d[0] + _EPS))


def gain_scan(base, kappas, omegas, **kw):
    x0 = psi_trs.psi_spec(np.asarray(base, float))
    G = np.zeros((len(kappas), len(omegas)))
    for i, kap in enumerate(kappas):
        for j, w in enumerate(omegas):
            G[i, j] = symmetry_gain(base, kap, omega=w, x0=x0, **kw)
    return G


def report(seed=0, steps=60, eps=1e-2):
    b = base_field(seed)
    ks = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0]
    G = [symmetry_gain(b, k, eps=eps, steps=steps) for k in ks]
    G0 = G[0]
    amplifies = any(g > G0 + 0.2 for g in G[1:])
    lines = ["BV-ΨTRS-SAG — Symmetry Amplification Gain (paired mirror-perturbed ΨTRS trajectories)"]
    lines.append("  G = max_t ||Theta+(t)-Theta-(t)|| / ||Theta+(0)-Theta-(0)||   (kappa=0 => fixed clock)")
    for k, g in zip(ks, G):
        lines.append(f"    kappa={k:4.1f}  G={g:.3f}")
    verdict = ("state-dependent clock AMPLIFIES above threshold; fixed clock stays coherent"
               if (amplifies and G0 < 1.1) else "no clean amplification (valid negative)")
    lines.append(f"  verdict: {verdict}  (kappa=0 gain G0={G0:.3f})")
    lines.append("  NOTE: offline research artifact only; authorizes no runtime/memory/action contact.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
