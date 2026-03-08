# cp_windows.py
import numpy as np
from dataclasses import dataclass
from typing import Sequence

@dataclass
class CPWindowConfig:
    """
    CP ridge windows in D24 sector space.

    center_indices: sector centers (0..n_sectors-1)
    half_width: integer radius in sectors around each center.
                Example: half_width=1 means center-1, center, center+1.
    n_sectors: total number of angular sectors (12 for D24).
    """
    center_indices: Sequence[int]
    half_width: int = 1
    n_sectors: int = 12

def cp_mask_from_phi_indices(phi_indices: np.ndarray, cfg: CPWindowConfig) -> np.ndarray:
    """
    Given phi_indices (0..n_sectors-1), return boolean mask of points that lie
    inside any CP window defined by cfg.
    """
    phi_indices = np.asarray(phi_indices)
    mask = np.zeros_like(phi_indices, dtype=bool)

    for c in cfg.center_indices:
        # distance in cyclic sector space
        dist = np.minimum(
            (phi_indices - c) % cfg.n_sectors,
            (c - phi_indices) % cfg.n_sectors,
        )
        mask |= dist <= cfg.half_width

    return mask

def default_cp_config() -> CPWindowConfig:
    """
    Default CP ridge config: windows around ±π/2 in D24.

    In 12-sector indexing, φ = π/2 corresponds to sector 3,
    φ = 3π/2 corresponds to sector 9.

    half_width=1 → sectors {2,3,4} and {8,9,10}.
    """
    return CPWindowConfig(center_indices=[3, 9], half_width=1, n_sectors=12)
