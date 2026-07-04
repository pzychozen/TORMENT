"""PsiBV-RPSR: Return-Phase Spectral Recursion (offline, re-derived, no service imports).

RPSR[t, c, m, r] with return-relation classes r in {immediate, short_return, long_return,
inverted_return, reset}. Reads instantaneous band phase to score whether the current spectral state
returns (in phase), returns after a gap, returns inverted (anti-phase), or resets with no return --
information a plain FFT magnitude spectrum discards. stdlib + numpy only.
"""
from __future__ import annotations

import numpy as np

M_BANDS = 4
RETURN_CLASSES = ("immediate", "short_return", "long_return", "inverted_return", "reset")
R_DIM = len(RETURN_CLASSES)
_SHORT_LAG = 3
_LONG_LAG = 12
_EPS = 1e-8


def _analytic(x):
    N = len(x); X = np.fft.fft(x); h = np.zeros(N)
    if N % 2 == 0:
        h[0] = 1; h[N // 2] = 1; h[1:N // 2] = 2
    else:
        h[0] = 1; h[1:(N + 1) // 2] = 2
    return np.fft.ifft(X * h)


def _bandpass(x, m, M):
    F = np.fft.rfft(x); nb = len(F)
    edges = np.linspace(1, nb, M + 1).astype(int)
    mask = np.zeros_like(F); mask[edges[m]:edges[m + 1]] = 1.0
    return np.fft.irfft(F * mask, n=len(x))


def compute_rpsr(descriptors):
    """Return RPSR of shape (T, C, M_BANDS, R_DIM) from a (T, C) descriptor array."""
    d = np.asarray(descriptors, float); T, C = d.shape
    rp = np.zeros((T, C, M_BANDS, R_DIM))
    for c in range(C):
        for m in range(M_BANDS):
            a = _analytic(_bandpass(d[:, c], m, M_BANDS))
            amp = np.abs(a); ph = np.angle(a)
            for t in range(T):
                def sim(lag):
                    if t - lag < 0:
                        return 0.0
                    w = min(amp[t], amp[t - lag]) / (max(amp[t], amp[t - lag]) + _EPS)
                    return w * np.cos(ph[t] - ph[t - lag])
                s1, ss, sl = sim(1), sim(_SHORT_LAG), sim(_LONG_LAG)
                q = abs(amp[t] - amp[t - 1]) / (amp[t] + amp[t - 1] + _EPS) if t >= 1 else 0.0
                rp[t, c, m, 0] = max(s1, 0.0)             # immediate continuity
                rp[t, c, m, 1] = max(ss, 0.0)             # short-return
                rp[t, c, m, 2] = max(sl, 0.0)             # long-return
                rp[t, c, m, 3] = max(-ss, -sl, -s1, 0.0)  # phase-inverted return
                rp[t, c, m, 4] = q * (1.0 - max(s1, ss, sl, 0.0))  # reset / no-return
    return rp


def derive_scalars(rp):
    """Return {R_bv, Phi_bv, K_bv, Q_bv, J_bv, inv} time series from an RPSR tensor."""
    cont = rp[..., 0].mean(axis=(1, 2)); sh = rp[..., 1].mean(axis=(1, 2))
    lo = rp[..., 2].mean(axis=(1, 2)); inv = rp[..., 3].mean(axis=(1, 2))
    res = rp[..., 4].mean(axis=(1, 2))
    R_bv = np.maximum.reduce([cont, sh, lo])          # return strength
    Phi_bv = cont                                     # phase-return alignment (immediate coherence)
    K_bv = np.abs(np.gradient(np.gradient(R_bv)))     # recurrence curvature / return acceleration
    return dict(R_bv=R_bv, Phi_bv=Phi_bv, K_bv=K_bv, Q_bv=res, J_bv=sh - lo, inv=inv)


def feature_vector(descriptors):
    """Fixed-length, phase-sensitive PsiBV-RPSR feature vector for classification."""
    rp = compute_rpsr(descriptors); s = derive_scalars(rp)
    feats = []
    for key in ("R_bv", "Phi_bv", "K_bv", "Q_bv", "J_bv"):
        v = s[key]; feats += [v.mean(), v.std(), v.max(), v.min()]
    feats += list(rp.mean(axis=(0, 1, 2)))  # mean energy per return class
    return np.array(feats, float)
