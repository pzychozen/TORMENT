"""BV-ΨTRS-RVD: real prerecorded visual descriptor route (offline, dependency-light).

Loads .npz frame stacks (key 'frames', shape (T,H,W) grayscale or (T,H,W,3) RGB, uint8 or float) and
reduces them to a low-level, label-free descriptor field (T, 9) suitable for the existing Brainvision
methods. NO camera / screen / sensor / stream capture -- real videos are converted to .npz OUTSIDE this
harness. stdlib + numpy only; no service imports; no OpenCV/PIL.
"""
from __future__ import annotations

import numpy as np

import descriptors

RV_DESCRIPTOR_NAMES = [
    "lum_mean", "lum_var", "contrast_energy", "framediff_mag", "edge_energy",
    "color_drift", "patch_variance", "recurrence_score", "continuity_score",
]
N_RV_DESCRIPTORS = len(RV_DESCRIPTOR_NAMES)


def load_frame_stack_npz(path):
    """Load a frame stack from .npz (key 'frames'). Returns float frames; uint8/0-255 rescaled to [0,1]."""
    with np.load(path) as d:
        if "frames" not in d:
            raise KeyError("npz must contain key 'frames'")
        frames = np.asarray(d["frames"], dtype=float)
    if frames.ndim not in (3, 4):
        raise ValueError(f"frames must be (T,H,W) or (T,H,W,3), got {frames.shape}")
    if frames.size and frames.max() > 1.5:
        frames = frames / 255.0
    return frames


def _luminance(frames):
    if frames.ndim == 4:
        w = np.array([0.299, 0.587, 0.114])
        return (frames[..., :3] * w).sum(axis=-1)
    return frames


def _patch_variance(g, grid=4):
    H, W = g.shape
    hs, ws = H // grid, W // grid
    if hs < 1 or ws < 1:
        return float(np.var(g))
    blocks = g[:hs * grid, :ws * grid].reshape(grid, hs, grid, ws).mean(axis=(1, 3))
    return float(np.var(blocks))


def frames_to_low_level_descriptors(frames):
    """Return a raw (T, 9) low-level, label-free descriptor field from a frame stack."""
    frames = np.asarray(frames, float)
    if frames.size and frames.max() > 1.5:
        frames = frames / 255.0
    is_rgb = frames.ndim == 4
    gray = _luminance(frames)
    T = gray.shape[0]
    flat = gray.reshape(T, -1)
    lum_mean = flat.mean(axis=1)
    lum_var = flat.var(axis=1)
    contrast = flat.std(axis=1)
    framediff = np.zeros(T)
    if T > 1:
        framediff[1:] = np.abs(gray[1:] - gray[:-1]).reshape(T - 1, -1).mean(axis=1)
    edge = np.array([(np.abs(np.gradient(g, axis=0)) + np.abs(np.gradient(g, axis=1))).mean() for g in gray])
    if is_rgb:
        caxis = frames[..., 0].reshape(T, -1).mean(1) - frames[..., 1].reshape(T, -1).mean(1)
        color_drift = np.zeros(T)
        if T > 1:
            color_drift[1:] = np.abs(np.diff(caxis))
    else:
        color_drift = np.zeros(T)
    patch = np.array([_patch_variance(g) for g in gray])
    recurrence = descriptors._recurrence_score(lum_mean)
    continuity = descriptors._continuity_score(lum_mean)
    return np.stack([lum_mean, lum_var, contrast, framediff, edge, color_drift, patch, recurrence, continuity], axis=1)


def window_descriptors(D, win=64, stride=32, min_len=16):
    """Split a (T,C) descriptor field into z-scored windows of length win (whole clip if shorter)."""
    D = np.asarray(D, float)
    T = D.shape[0]
    if T < win:
        return [descriptors._zscore(D)] if T >= min_len else []
    return [descriptors._zscore(D[i:i + win]) for i in range(0, T - win + 1, stride)]


def _segment_label(center, segments):
    if not segments:
        return None
    for seg in segments:
        if int(seg["start"]) <= center < int(seg["end"]):
            return seg.get("label")
    return None


def clip_descriptor_dataset(frames, win=64, stride=32, segments=None, min_len=16):
    """Return (windows, labels). labels is None if no segments; else a per-window segment label list."""
    D = frames_to_low_level_descriptors(frames)
    T = D.shape[0]
    windows, labels = [], []
    if T < win:
        if T >= min_len:
            windows.append(descriptors._zscore(D))
            labels.append(_segment_label(T // 2, segments))
    else:
        for i in range(0, T - win + 1, stride):
            windows.append(descriptors._zscore(D[i:i + win]))
            labels.append(_segment_label(i + win // 2, segments))
    return windows, (labels if segments else None)
