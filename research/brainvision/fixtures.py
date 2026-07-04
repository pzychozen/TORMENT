"""Deterministic synthetic descriptor-sequence fixtures for the offline Brainvision falsifier.

OFFLINE RESEARCH ONLY. No torment_service imports. No camera/screen/sensor/stream input.
Each generator returns a primitive descriptor array of shape (T, 3): channels [luminance, contrast,
color]. Regime groups are the classification target.

Modes:
  coarse (v0.1)            : classes differ in amplitude AND temporal structure (amplitude marginal leaks).
  marginal_matched (v0.2)  : classes share an identical per-channel amplitude multiset; differ only in
                             temporal order (removes the amplitude-marginal shortcut).
  spectrum_matched (v0.3)  : classes are IAAFT surrogates forced to one fixed target power spectrum
                             (|FFT| identical across classes -> plain-FFT magnitude cannot separate),
                             differing only in phase / return geometry, which PsiBV-RPSR reads.
  psi_time_recursive (v0.4): alias of spectrum_matched fixtures, used with BV-ΨTRS.

stdlib + numpy only.
"""
from __future__ import annotations

import zlib

import numpy as np

T = 64
N_PRIMITIVE = 3
_SIGMA = 0.02

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


# --- v0.1 coarse ------------------------------------------------------------
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


# --- v0.2 marginal-matched --------------------------------------------------
_MM_TARGETS = {0: np.linspace(0.20, 0.80, T), 1: np.linspace(0.10, 0.60, T), 2: np.linspace(0.30, 0.70, T)}
MM_FAMILY_GROUP = {
    "mm_smooth": "CONTINUITY_MM",
    "mm_recurrence": "RECURRENCE_MM",
    "mm_snap": "SNAP_MM",
    "mm_oscillation": "OSC_MM",
}
MM_CLASS_FAMILIES = list(MM_FAMILY_GROUP.keys())


def _rank_match(base, target):
    return np.asarray(target)[np.argsort(np.argsort(base))]


def _mm_base(name, channel, rng):
    t = np.arange(T, dtype=float)
    jitter = rng.normal(0.0, 0.08, T)
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
        base = np.sin(2 * np.pi * (0.42 + 0.03 * channel) * t)
    else:
        raise ValueError(name)
    return base + jitter


def generate_mm(name, seed):
    if name not in MM_FAMILY_GROUP:
        raise ValueError(name)
    rng = np.random.default_rng(_seed_for(name, int(seed)))
    return np.stack([_rank_match(_mm_base(name, c, rng), _MM_TARGETS[c]) for c in range(N_PRIMITIVE)], axis=1)


# --- v0.3 spectrum-matched (RPSR) -------------------------------------------
SM_FAMILY_GROUP = {
    "sm_continuity": "CONT_SM",
    "sm_short_return": "SHORT_SM",
    "sm_long_return": "LONG_SM",
    "sm_inverted_return": "INV_SM",
    "sm_reset": "RESET_SM",
}
SM_CLASS_FAMILIES = list(SM_FAMILY_GROUP.keys())
_SM_TARGET_SORTED = np.sort(np.random.default_rng(12345).normal(0.0, 1.0, T))


def _sm_target_amp():
    nb = T // 2 + 1
    amp = 1.0 / (1.0 + np.arange(nb, dtype=float))
    amp[0] = 0.0
    return amp


def _sm_base(name, rng):
    t = np.arange(T, dtype=float)

    def motif(c, w=2.5, h=1.0):
        return h * np.exp(-((t - c) ** 2) / (2.0 * w ** 2))

    j = rng.uniform(-2.0, 2.0)
    # Homogeneous two-event bases (unit height, no level shifts) so amplitude extremes match too; classes
    # differ only in the RETURN RELATION between the two events (carried by phase after spectrum matching).
    if name == "sm_continuity":
        c = T * 0.5 + j
        base = motif(c - 1) + motif(c + 1)
    elif name == "sm_short_return":
        c = T * 0.35 + j
        base = motif(c) + motif(c + 5)
    elif name == "sm_long_return":
        c = T * 0.20 + j
        base = motif(c) + motif(c + 24)
    elif name == "sm_inverted_return":
        c = T * 0.30 + j
        base = motif(c) - motif(c + 10)
    elif name == "sm_reset":
        c = T * 0.30 + j
        base = motif(c) + motif(c + 15)
        base[int(c + 18):] *= -1.0
    else:
        raise ValueError(name)
    return base


def _iaaft(base, target_amp, target_sorted, n_iter=25):
    """IAAFT surrogate: alternately impose target power spectrum and target marginal, seeded by base's
    phase. Ends on the SPECTRUM step so |FFT| == target exactly (plain-FFT magnitude -> chance). Marginal
    is matched in mean/variance (Parseval) and closely in higher moments; a residual remains because
    matching BOTH marginal and spectrum exactly is only possible for the shift/reversal group."""
    ph = np.angle(np.fft.rfft(base))
    x = np.fft.irfft(target_amp * np.exp(1j * ph), n=T)
    for _ in range(n_iter):
        x = target_sorted[np.argsort(np.argsort(x))]
        ph = np.angle(np.fft.rfft(x))
        x = np.fft.irfft(target_amp * np.exp(1j * ph), n=T)
    return x


def generate_sm(name, seed):
    if name not in SM_FAMILY_GROUP:
        raise ValueError(name)
    rng = np.random.default_rng(_seed_for(name, int(seed)))
    target_amp = _sm_target_amp()
    chans = [_iaaft(_sm_base(name, rng) + rng.normal(0.0, 0.01, T), target_amp, _SM_TARGET_SORTED)
             for _c in range(N_PRIMITIVE)]
    return np.stack(chans, axis=1)


def dataset(seeds, mode="coarse"):
    """Yield (name, group, seed, array). mode in {coarse, marginal_matched, spectrum_matched,
    psi_time_recursive}. psi_time_recursive reuses the spectrum-matched fixtures (v0.4 ΨTRS)."""
    if mode == "coarse":
        gen, fam, grp = generate, CLASS_FAMILIES, FAMILY_GROUP
    elif mode == "marginal_matched":
        gen, fam, grp = generate_mm, MM_CLASS_FAMILIES, MM_FAMILY_GROUP
    elif mode in ("spectrum_matched", "psi_time_recursive"):
        gen, fam, grp = generate_sm, SM_CLASS_FAMILIES, SM_FAMILY_GROUP
    else:
        raise ValueError(f"unknown mode: {mode!r}")
    for name in fam:
        for s in seeds:
            yield name, grp[name], int(s), gen(name, int(s))
