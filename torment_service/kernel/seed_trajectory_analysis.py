# seed_trajectory_analysis.py
from __future__ import annotations
import numpy as np

def classify_trajectory(r_history, eps: float = 1e-6, min_samples: int = 200) -> str:
    """
    Stable classification based on r(t)=sqrt(x^2+y^2).
    For very short histories (late emissions), return 'grazing' to avoid slope artifacts.
    """
    r = np.asarray(r_history, dtype=float)
    if r.size < min_samples:
        return "grazing"
    if r.size < 3:
        return "unknown"

    dr = np.diff(r)

    if np.all(dr > eps):
        return "escape"
    if np.any(dr < -eps):
        return "return"
    return "grazing"

