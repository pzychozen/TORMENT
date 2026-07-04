"""Low-level, label-free descriptor preparation for the offline Brainvision falsifier.

Takes a primitive (T, 3) array [luminance, contrast, color] and derives a normalized (T, C) descriptor
feature array. No object labels, no semantics, no service imports. stdlib + numpy only.
"""
from __future__ import annotations

import numpy as np

_EPS = 1e-8

# Descriptor channel names (order matters; keep low-level and label-free).
DESCRIPTOR_NAMES = [
    "luminance_mean",
    "luminance_rolling_var",
    "contrast_energy",
    "framediff_magnitude",
    "edge_energy",
    "color_value",
    "color_drift",
    "patch_variance",
    "recurrence_score",
    "continuity_score",
]
N_DESCRIPTORS = len(DESCRIPTOR_NAMES)


def _rolling_var(x: np.ndarray, w: int = 5) -> np.ndarray:
    pad = w // 2
    xp = np.pad(x, pad, mode="edge")
    out = np.empty_like(x)
    for i in range(len(x)):
        out[i] = np.var(xp[i:i + w])
    return out


def _first_diff_mag(x: np.ndarray) -> np.ndarray:
    d = np.abs(np.diff(x, prepend=x[:1]))
    return d


def _recurrence_score(x: np.ndarray, w: int = 8) -> np.ndarray:
    """Short-lag self-similarity within a trailing window (0..1)."""
    out = np.zeros_like(x)
    for i in range(len(x)):
        lo = max(0, i - w)
        seg = x[lo:i + 1]
        if len(seg) < 3:
            continue
        a = seg[:-1] - seg[:-1].mean()
        b = seg[1:] - seg[1:].mean()
        denom = np.sqrt((a * a).sum() * (b * b).sum()) + _EPS
        out[i] = float(np.clip((a * b).sum() / denom, -1.0, 1.0))
    return out


def _continuity_score(x: np.ndarray) -> np.ndarray:
    """Smoothness: 1 - normalized |second difference|. Low on ruptures."""
    d2 = np.abs(np.diff(x, n=2, prepend=x[:1], append=x[-1:]))
    d2 = d2[:len(x)]
    scale = np.max(d2) + _EPS
    return 1.0 - d2 / scale


def _zscore(a: np.ndarray) -> np.ndarray:
    mu = a.mean(axis=0, keepdims=True)
    sd = a.std(axis=0, keepdims=True)
    return (a - mu) / (sd + _EPS)


def prepare(primitive: np.ndarray) -> np.ndarray:
    """Return a normalized (T, C) descriptor feature array. C == N_DESCRIPTORS."""
    primitive = np.asarray(primitive, dtype=float)
    if primitive.ndim != 2 or primitive.shape[1] != 3:
        raise ValueError(f"expected primitive shape (T, 3), got {primitive.shape}")
    lum, con, col = primitive[:, 0], primitive[:, 1], primitive[:, 2]
    channels = np.stack([
        lum,
        _rolling_var(lum),
        con,
        _first_diff_mag(lum),
        _first_diff_mag(con),
        col,
        _first_diff_mag(col),
        _rolling_var(col),
        _recurrence_score(lum),
        _continuity_score(lum),
    ], axis=1)
    return _zscore(channels)
