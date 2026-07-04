"""Baseline and control feature extractors for the offline Brainvision falsifier.

Every method returns a fixed-length feature vector for a single fixture, so the same classifier/metric can
score PsiBV against each baseline. stdlib + numpy only. No service imports.

Baselines:
  frame_diff          - magnitude-of-change baseline (the one that beat visual_bus_v0)
  descriptor_only     - raw marginal statistics (order-invariant ablation)
  plain_fft           - temporal magnitude spectrum, no polarity/return split (ablation of the h axis)
  random_mapping      - fixed random projection (sanity floor)

Controls:
  time_shuffle(primitive, seed) - permute the time axis (destroys temporal structure)
  (shuffled-label control is applied in run_falsifier by permuting the label vector)
"""
from __future__ import annotations

import numpy as np

_EPS = 1e-8
_N_FFT_BANDS = 6


def frame_diff_features(primitive: np.ndarray) -> np.ndarray:
    x = np.asarray(primitive, dtype=float)
    fd = ((x[1:] - x[:-1]) ** 2).mean(axis=1)  # per-step frame-diff magnitude
    if fd.size == 0:
        fd = np.zeros(1)
    return np.array([fd.mean(), fd.std(), fd.max(), np.abs(fd).sum() / len(fd)], dtype=float)


def descriptor_only_features(primitive: np.ndarray) -> np.ndarray:
    """Order-invariant marginal statistics of the raw primitive channels."""
    x = np.asarray(primitive, dtype=float)
    return np.concatenate([
        x.mean(axis=0), x.std(axis=0), x.min(axis=0), x.max(axis=0),
    ]).astype(float)


def plain_fft_features(primitive: np.ndarray) -> np.ndarray:
    """Temporal magnitude spectrum band energies per channel (no polarity/return split)."""
    x = np.asarray(primitive, dtype=float)
    feats = []
    for c in range(x.shape[1]):
        mag = np.abs(np.fft.rfft(x[:, c] - x[:, c].mean()))
        bands = np.array_split(mag, _N_FFT_BANDS)
        feats.extend([float(b.sum()) for b in bands])
    return np.array(feats, dtype=float)


def random_mapping_features(primitive: np.ndarray, dim: int = 12, seed: int = 12345) -> np.ndarray:
    x = np.asarray(primitive, dtype=float).reshape(-1)
    rng = np.random.default_rng(seed)
    proj = rng.normal(0.0, 1.0, (dim, x.size))
    return proj @ x


def time_shuffle(primitive: np.ndarray, seed: int) -> np.ndarray:
    """Permute the time axis; destroys temporal/return structure while preserving marginals."""
    x = np.asarray(primitive, dtype=float)
    rng = np.random.default_rng((seed * 40503) & 0xFFFFFFFF)
    perm = rng.permutation(x.shape[0])
    return x[perm, :]
