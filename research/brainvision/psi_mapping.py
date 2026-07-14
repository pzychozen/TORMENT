"""Offline PsiBV[t, c, m, h] mapping for the Brainvision falsifier.

Independently re-derived. Does NOT import or reuse RSBModel, definitions.py, TriOctaMemoryKernel, or any
torment_service surface. stdlib + numpy only.

Axes:
  t = time step
  c = descriptor channel
  m = temporal band (multi-scale band-pass of the channel time series)
  h = polarity/return split, predeclared here as {rising, falling} (h=0 rising, h=1 falling)

Derived scalars (re-derived offline analogues, not imports):
  H_bv  = normalized band entropy over m
  m0_bv = dominant band argmax_m
  J_bv  = rising-minus-falling (polarity/return) imbalance
  v_bv  = |dH_bv/dt| recursive velocity
"""
from __future__ import annotations

import numpy as np

SCALES = (1, 2, 4, 8)  # M temporal bands
M_BANDS = len(SCALES)
H_POLARITY = 2  # rising / falling
_EPS = 1e-8


def _moving_average(x: np.ndarray, w: int) -> np.ndarray:
    if w <= 1:
        return x.astype(float).copy()
    pad = w // 2
    xp = np.pad(x.astype(float), pad, mode="edge")
    kernel = np.ones(w) / w
    return np.convolve(xp, kernel, mode="same")[pad:pad + len(x)]


def compute_psi(descriptors: np.ndarray) -> np.ndarray:
    """Return PsiBV of shape (T, C, M_BANDS, 2) from a (T, C) descriptor array."""
    d = np.asarray(descriptors, dtype=float)
    if d.ndim != 2:
        raise ValueError(f"expected (T, C) descriptors, got {d.shape}")
    T, C = d.shape
    psi = np.zeros((T, C, M_BANDS, H_POLARITY), dtype=float)
    for c in range(C):
        x = d[:, c]
        slope = np.gradient(x)
        rising = (slope >= 0.0).astype(float)
        falling = 1.0 - rising
        for mi, s in enumerate(SCALES):
            band = _moving_average(x, 2 * s + 1) - _moving_average(x, 4 * s + 1)
            energy = np.abs(band)
            psi[:, c, mi, 0] = energy * rising
            psi[:, c, mi, 1] = energy * falling
    return psi


def derive_scalars(psi: np.ndarray) -> dict:
    """Return {H_bv, m0_bv, J_bv, v_bv} time series from a PsiBV tensor."""
    band_energy = (psi ** 2).sum(axis=(1, 3))  # (T, M)
    row = band_energy.sum(axis=1, keepdims=True) + _EPS
    p = band_energy / row
    H_bv = -(p * np.log(p + _EPS)).sum(axis=1) / np.log(psi.shape[2])
    m0_bv = np.argmax(band_energy, axis=1).astype(int)
    J_bv = (psi[:, :, :, 0] - psi[:, :, :, 1]).sum(axis=(1, 2))  # rising - falling
    v_bv = np.abs(np.diff(H_bv, prepend=H_bv[:1]))
    return {"H_bv": H_bv, "m0_bv": m0_bv, "J_bv": J_bv, "v_bv": v_bv}


def feature_vector(descriptors: np.ndarray) -> np.ndarray:
    """Fixed-length, order-dependent PsiBV feature vector for classification."""
    psi = compute_psi(descriptors)
    s = derive_scalars(psi)
    v, J, H, m0 = s["v_bv"], s["J_bv"], s["H_bv"], s["m0_bv"]
    M = psi.shape[2]
    band_energy = (psi ** 2).sum(axis=(0, 1, 3))  # (M,)
    band_frac = band_energy / (band_energy.sum() + _EPS)
    m0_hist = np.bincount(m0, minlength=M)[:M] / max(len(m0), 1)
    head = np.array([
        v.mean(), v.std(), v.max(),
        np.abs(J).mean(), J.std(), np.abs(J).max(),
        H.mean(), H.std(),
    ], dtype=float)
    return np.concatenate([head, band_frac, m0_hist])
