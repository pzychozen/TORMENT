"""Lightweight, deterministic separability metrics for the offline Brainvision falsifier.

Only local numpy arrays. No service imports, no sklearn/scipy. The core metric is a leave-one-out
nearest-centroid balanced accuracy, which is deterministic and needs no training loop.
"""
from __future__ import annotations

import numpy as np

_EPS = 1e-8


def standardize(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    mu = X.mean(axis=0, keepdims=True)
    sd = X.std(axis=0, keepdims=True)
    return (X - mu) / (sd + _EPS)


def loo_nearest_centroid_balanced_accuracy(X: np.ndarray, y) -> float:
    """Leave-one-out nearest-centroid balanced accuracy. Deterministic."""
    X = standardize(np.asarray(X, dtype=float))
    y = np.asarray(y)
    classes = np.unique(y)
    n = len(y)
    preds = np.empty(n, dtype=object)
    for i in range(n):
        best_c, best_d = None, np.inf
        for c in classes:
            mask = (y == c)
            mask[i] = False
            if not mask.any():
                continue
            centroid = X[mask].mean(axis=0)
            d = float(np.linalg.norm(X[i] - centroid))
            if d < best_d:
                best_d, best_c = d, c
        preds[i] = best_c
    recalls = []
    for c in classes:
        idx = (y == c)
        if idx.sum() == 0:
            continue
        recalls.append(float((preds[idx] == c).mean()))
    return float(np.mean(recalls)) if recalls else 0.0


def chance_level(y) -> float:
    return 1.0 / max(len(np.unique(np.asarray(y))), 1)
