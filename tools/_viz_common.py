"""
_viz_common.py — shared helpers for TORMENT visualization tools.

Used by motif_field_viz.py and visualize_attractors.py.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List

import numpy as np


def _unit(v: np.ndarray) -> np.ndarray:
    """L2-normalise a vector (with epsilon to avoid division by zero)."""
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v) + 1e-12)
    return (v / n).astype(np.float32)


def _pca_2d(X: np.ndarray) -> np.ndarray:
    """Simple PCA via SVD; returns Nx2."""
    if X.ndim != 2:
        raise ValueError("X must be 2D")
    if X.shape[0] == 0:
        return np.zeros((0, 2), dtype=np.float32)
    Xc = X - X.mean(axis=0, keepdims=True)
    if X.shape[0] == 1:
        return np.zeros((1, 2), dtype=np.float32)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    Z = Xc @ Vt[:2].T
    if Z.shape[1] == 1:
        Z = np.concatenate([Z, np.zeros((Z.shape[0], 1), dtype=Z.dtype)], axis=1)
    return Z[:, :2].astype(np.float32)


@dataclass
class MotifInfo:
    motif_id: str
    label: str
    strength: float
    stability_score: float
    members: List[int]
    centroid: np.ndarray

    @property
    def density(self) -> float:
        # Same saturation shape as the gravity-well patch.
        return float(min(1.0, np.log1p(max(0, len(self.members))) / np.log(33.0)))

    @property
    def gravity_bonus(self) -> float:
        return float(
            0.10 * np.clip(self.strength, 0.0, 1.0)
            + 0.07 * self.density
            + 0.05 * np.clip(self.stability_score, 0.0, 1.0)
        )


def make_color_cycle(n: int) -> List[str]:
    base = [
        "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple",
        "tab:brown", "tab:pink", "tab:gray", "tab:olive", "tab:cyan",
    ]
    return [base[i % len(base)] for i in range(n)]


def load_motifs(data_dir: str, workspace: str, domain: str) -> Dict[str, MotifInfo]:
    """Load motifs.json for a workspace/domain. Returns empty dict if not found."""
    path = os.path.join(data_dir, "workspaces", workspace, "domains", domain, "motifs.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    out: Dict[str, MotifInfo] = {}
    for mid, md in obj.get("motifs", {}).items():
        centroid_raw = md.get("centroid", [])
        if not centroid_raw:
            continue
        out[mid] = MotifInfo(
            motif_id=mid,
            label=str(md.get("label", mid)),
            strength=float(md.get("strength", 0.0)),
            stability_score=float(md.get("stability_score", 0.0)),
            members=[int(x) for x in md.get("members", [])],
            centroid=_unit(np.asarray(centroid_raw, dtype=np.float32)),
        )
    return out
