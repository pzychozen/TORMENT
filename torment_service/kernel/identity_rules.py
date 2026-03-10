# identity_rules.py
import numpy as np
from dataclasses import dataclass
from typing import List

@dataclass
class CycleConfig:
    """
    Configuration for the recursive cycle stages S0..S6.

    kappa_thresholds: array of monotonically increasing thresholds.
    Stage is 'how many thresholds kappa has crossed'.
    """
    kappa_thresholds: np.ndarray

# Optional: semantic labels for the 9 identity states (you can rename later)
IDENTITY_LABELS: List[str] = [
    "s0_void_low",
    "s1_low_posZ",
    "s2_low_negZ",
    "s3_mid_low",
    "s4_mid_posZ",
    "s5_mid_negZ",
    "s6_high_low",
    "s7_high_posZ",
    "s8_high_negZ",
]

def compute_cycle_stage(kappa: float, config: CycleConfig) -> int:
    """
    Given scalar kappa and cycle config, return stage index S = 0..6.

    Currently:
        S = number of thresholds that kappa exceeds.
    """
    return int(np.sum(kappa > config.kappa_thresholds))

def map_identity_state(stage: int, z: float, num_states: int = 9) -> int:
    """
    Map (cycle_stage, sign(z)) -> identity index s = 0..8.

    base = stage
    offset = 0 if z == 0, 1 if z>0, 2 if z<0
    s = (base * 3 + offset) mod num_states
    """
    base = stage
    if z > 0:
        offset = 1
    elif z < 0:
        offset = 2
    else:
        offset = 0
    return (base * 3 + offset) % num_states

def label_for_identity(s: int) -> str:
    """
    Return a human-readable label for identity index s.
    Safe for any integer s (wraps mod len).
    """
    idx = s % len(IDENTITY_LABELS)
    return IDENTITY_LABELS[idx]
