"""Deterministic synthetic descriptor-sequence fixtures for the offline Brainvision falsifier.

OFFLINE RESEARCH ONLY. No torment_service imports. No camera/screen/sensor/stream input.
Each generator returns a primitive descriptor array of shape (T, 3): channels [luminance, contrast,
color]. Regime groups are the classification target.

v0.1 "coarse" families differ in amplitude AND temporal structure (amplitude marginals leak the class).
v0.2 "marginal_matched" families share, per channel, an identical target value multiset, so classes have
matched amplitude histograms/mean/variance and differ ONLY in temporal arrangement.

stdlib + numpy only.
"""
from __future__ import annotations

import zlib

import numpy as np

T = 64
N_PRIMITIVE = 3

FAMILY_GROUP = {
    "stable_field": "CONTINUITY",
    "smooth_drift": "CONTINUITY",
    "edge_emergence": "PULSE",
    "contrast_pulse": "PULSE",
    "color_light_shift": "PULSE",
    "occlusion_interruption": "DISRUPTION",
    "snap_reset": "DISRUPTION",
    "recurrence_after_gap": "RECURRENCE",
    "random_noise": "NOISE",
    "shuffled_temporal_order": "CONTROL",
}
CLASS_FAMILIES = [f for f, g in FAMILY_GROUP.items() if g != "CONTROL"]
FAMILIES = list(FAMILY_GROUP.keys())
_SIGMA = 0.02


def _seed_for(name: str, seed: int) -> int:
    return (zlib.crc32(name.encode("utf-8")) ^ ((seed * 2654435761) & 0xFFFFFFFF)) & 0xFFFFFFFF


def _noise(rng, sigma=_SIGMA):
    return rng.normal(0.0, sigma, T)


def _bump(center, width, height=1.0):
    t = np.arange(T, dtype=float)
    return height * np.exp(-((t - center) ** 2) / (2.0 * width ** 2))


def _sigmoid(center, width):
    t = np.arange(T, dtype=float)
    return 1.0 / (1.0 + np.exp(-(t - center) / width))


def generate(name, seed):
    if name not in FAMILY_GROUP:
        raise ValueError(f"unknown fixture family: {name!r}")
    rng = np.random.default_rng(_seed_for(name, int(seed)))
    lum = np.full(T, 0.5) + _noise(rng)
    con = np.full(T, 0.3) + _noise(rng)
    col = np.full(T, 0.5) + _noise(rng)
    if name == "stable_field":
        pass
    elif name == "smooth_drift":
        ramp = np.linspace(0.0, 0.35, T)
        lum = 0.4 + ramp + _noise(rng)
        col = 0.4 + 0.5 * ramp + _noise(rng)
    elif name == "edge_emergence":
        con = 0.1 + 0.6 * _sigmoid(T * 0.5, 3.0) + _noise(rng)
    elif name == "contrast_pulse":
        con = 0.2 + 0.7 * _bump(T * 0.5, 2.5) + _noise(rng)
    elif name == "color_light_shift":
        col = 0.3 + 0.5 * _sigmoid(T * 0.5, 1.5) + _noise(rng)
    elif name == "occlusion_interruption":
        lum = np.full(T, 0.55)
        a, b = int(T * 0.35), int(T * 0.5)
        lum[a:b] = 0.05
        lum[b:] = 0.4
        con = con - 0.15 * ((np.arange(T) >= a) & (np.arange(T) < b))
        lum = lum + _noise(rng)
    elif name == "snap_reset":
        mid = T // 2
        lum = np.full(T, 0.55)
        lum[mid] = 1.0
        lum[mid + 1:] = 0.2
        con = np.full(T, 0.35)
        con[mid + 1:] = 0.15
        lum = lum + _noise(rng)
        con = con + _noise(rng)
    elif name == "recurrence_after_gap":
        pattern = _bump(T * 0.25, 2.5, 0.6) + _bump(T * 0.75, 2.5, 0.6)
        lum = 0.4 + pattern + _noise(rng)
        con = 0.25 + 0.7 * pattern + _noise(rng)
    elif name == "random_noise":
        lum = rng.uniform(0.0, 1.0, T)
        con = rng.uniform(0.0, 1.0, T)
        col = rng.uniform(0.0, 1.0, T)
    elif name == "shuffled_temporal_order":
        base = generate("recurrence_after_gap", seed)
        return base[rng.permutation(T), :]
    return np.stack([lum, con, col], axis=1)


# --- v0.2 marginal-matched families -----------------------------------------
# All marginal-matched families share, per channel, an IDENTICAL target value multiset. Classes therefore
# have matched amplitude histograms / mean / variance / order-statistics by construction, and differ ONLY
# in temporal arrangement. This removes the amplitude shortcut that made v0.1 trivial for descriptor_only.
_MM_TARGETS = {
    0: np.linspace(0.20, 0.80, T),
    1: np.linspace(0.10, 0.60, T),
    2: np.linspace(0.30, 0.70, T),
}
MM_FAMILY_GROUP = {
    "mm_smooth": "CONTINUITY_MM",
    "mm_recurrence": "RECURRENCE_MM",
    "mm_snap": "SNAP_MM",
    "mm_oscillation": "OSC_MM",
}
MM_CLASS_FAMILIES = list(MM_FAMILY_GROUP.keys())


def _rank_match(base, target):
    """Return an array with EXACTLY target's values, ordered by base's rank order."""
    order = np.argsort(np.argsort(base))
    return np.asarray(target)[order]


def _mm_base(name, channel, rng):
    t = np.arange(T, dtype=float)
    jitter = rng.normal(0.0, 0.08, T)  # tiny rank-perturbing jitter for within-class variety
    if name == "mm_smooth":
        base = t / T
    elif name == "mm_recurrence":
        c1 = T * 0.25 + rng.uniform(-2, 2)
        c2 = T * 0.75 + rng.uniform(-2, 2)
        base = np.exp(-((t - c1) ** 2) / 8.0) + np.exp(-((t - c2) ** 2) / 8.0)
    elif name == "mm_snap":
        cut = int(T * 0.5 + rng.uniform(-3, 3))
        base = np.where(t < cut, 0.0, 1.0).astype(float)
    elif name == "mm_oscillation":
        freq = 0.42 + 0.03 * channel
        base = np.sin(2 * np.pi * freq * t)
    else:
        raise ValueError(f"unknown mm family: {name!r}")
    return base + jitter


def generate_mm(name, seed):
    if name not in MM_FAMILY_GROUP:
        raise ValueError(f"unknown mm family: {name!r}")
    rng = np.random.default_rng(_seed_for(name, int(seed)))
    chans = [_rank_match(_mm_base(name, c, rng), _MM_TARGETS[c]) for c in range(N_PRIMITIVE)]
    return np.stack(chans, axis=1)


def dataset(seeds, mode="coarse"):
    """Yield (name, group, seed, array). mode in {"coarse" (v0.1), "marginal_matched" (v0.2)}."""
    if mode == "coarse":
        for name in CLASS_FAMILIES:
            for s in seeds:
                yield name, FAMILY_GROUP[name], int(s), generate(name, int(s))
    elif mode == "marginal_matched":
        for name in MM_CLASS_FAMILIES:
            for s in seeds:
                yield name, MM_FAMILY_GROUP[name], int(s), generate_mm(name, int(s))
    else:
        raise ValueError(f"unknown mode: {mode!r}")
