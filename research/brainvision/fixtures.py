"""Deterministic synthetic descriptor-sequence fixtures for the offline Brainvision falsifier.

OFFLINE RESEARCH ONLY. No torment_service imports. No camera/screen/sensor/stream input.
Each generator returns a primitive descriptor array of shape (T, 3): channels [luminance, contrast,
color]. Higher-level descriptors are derived in descriptors.py. Regime groups are used as the
classification target in the falsifier.

stdlib + numpy only.
"""
from __future__ import annotations

import zlib

import numpy as np

T = 64  # fixture length (time steps)
N_PRIMITIVE = 3  # [luminance, contrast, color]

# family -> coarse regime group (classification target). The temporal-shuffle control family is not a
# class; it is excluded from the classification set.
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

_SIGMA = 0.02  # small deterministic observation noise


def _seed_for(name: str, seed: int) -> int:
    # Stable across processes (unlike builtin hash()).
    return (zlib.crc32(name.encode("utf-8")) ^ ((seed * 2654435761) & 0xFFFFFFFF)) & 0xFFFFFFFF


def _noise(rng: np.random.Generator, sigma: float = _SIGMA) -> np.ndarray:
    return rng.normal(0.0, sigma, T)


def _bump(center: float, width: float, height: float = 1.0) -> np.ndarray:
    t = np.arange(T, dtype=float)
    return height * np.exp(-((t - center) ** 2) / (2.0 * width ** 2))


def _sigmoid(center: float, width: float) -> np.ndarray:
    t = np.arange(T, dtype=float)
    return 1.0 / (1.0 + np.exp(-(t - center) / width))


def generate(name: str, seed: int) -> np.ndarray:
    """Return a deterministic (T, 3) primitive descriptor array for `name` seeded by `seed`."""
    if name not in FAMILY_GROUP:
        raise ValueError(f"unknown fixture family: {name!r}")
    rng = np.random.default_rng(_seed_for(name, int(seed)))
    lum = np.full(T, 0.5) + _noise(rng)
    con = np.full(T, 0.3) + _noise(rng)
    col = np.full(T, 0.5) + _noise(rng)

    if name == "stable_field":
        pass  # flat baselines only

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
        lum[mid] = 1.0  # one-sample spike
        lum[mid + 1:] = 0.2  # reinitialized baseline
        con = np.full(T, 0.35)
        con[mid + 1:] = 0.15
        lum = lum + _noise(rng)
        con = con + _noise(rng)

    elif name == "recurrence_after_gap":
        pattern = _bump(T * 0.25, 2.5, 0.6) + _bump(T * 0.75, 2.5, 0.6)  # same shape twice, gap between
        lum = 0.4 + pattern + _noise(rng)
        con = 0.25 + 0.7 * pattern + _noise(rng)

    elif name == "random_noise":
        lum = rng.uniform(0.0, 1.0, T)
        con = rng.uniform(0.0, 1.0, T)
        col = rng.uniform(0.0, 1.0, T)

    elif name == "shuffled_temporal_order":
        base = generate("recurrence_after_gap", seed)
        perm = rng.permutation(T)
        return base[perm, :]

    return np.stack([lum, con, col], axis=1)


def dataset(seeds, families=None):
    """Yield (name, group, seed, array) for each family x seed. Deterministic."""
    families = list(families) if families is not None else CLASS_FAMILIES
    for name in families:
        group = FAMILY_GROUP[name]
        for seed in seeds:
            yield name, group, int(seed), generate(name, int(seed))
