# constants_selector.py
import math
import numpy as np
from dataclasses import dataclass
from typing import Dict

# --- core math constants we care about ---

@dataclass(frozen=True)
class CoreConstants:
    pi: float
    phi: float
    e: float
    sqrt3: float
    euler_gamma: float
    apery_zeta3: float

def get_core_constants() -> CoreConstants:
    """Return a bundle of core constants used in the model."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    # Apery's constant ζ(3) ~ 1.2020569
    zeta3 = 1.202056903159594
    return CoreConstants(
        pi=math.pi,
        phi=phi,
        e=math.e,
        sqrt3=math.sqrt(3.0),
        euler_gamma=0.5772156649015329,
        apery_zeta3=zeta3,
    )

# --- θ-ladder helper (your reciprocal asymmetry) ---

def theta_value(Ci: float, Cj: float) -> float:
    """
    θ(Ci, Cj) = |Ci/Cj - Cj/Ci| / sqrt(Ci * Cj)
    (scale-invariant reciprocal asymmetry)
    """
    return abs(Ci / Cj - Cj / Ci) / math.sqrt(Ci * Cj)

def theta_soft_triplet(alpha: float = 1.0) -> np.ndarray:
    """
    Softer mapping of θ-pairs into k-values.

    - keep ordering from θ
    - compress extremes via sqrt
    - alpha is a global scale factor

    Result: k_i = alpha * sqrt(θ_i / θ_base).
    """
    c = get_core_constants()
    th1 = theta_value(c.sqrt3, c.phi)
    th2 = theta_value(c.pi, c.e)
    th3 = theta_value(c.phi, c.e)

    base = th1 if th1 != 0.0 else 1.0
    ratios = np.array([th1, th2, th3], dtype=float) / base
    k_soft = alpha * np.sqrt(ratios)
    return k_soft

def theta_triplet_scaled() -> np.ndarray:
    """
    Build a triplet of k-values from three θ-pairs, scaled so that
    θ(sqrt3, phi) maps to 1.0. The others are relative to that.

    This ties directly into your θ-ladder paper.
    """
    c = get_core_constants()
    # three special θ-pairs you like
    th1 = theta_value(c.sqrt3, c.phi)
    th2 = theta_value(c.pi, c.e)
    th3 = theta_value(c.phi, c.e)

    base = th1 if th1 != 0.0 else 1.0
    k1 = th1 / base
    k2 = th2 / base
    k3 = th3 / base

    return np.array([k1, k2, k3], dtype=float)

def simple_hand_tuned_triplet() -> np.ndarray:
    """
    Original stable hand-tuned values that gave nice κ(t):
    just kept here as a 'safe' mode.
    """
    return np.array([0.7, 1.0, 1.3], dtype=float)

def default_k_triplet(mode: str = "theta_scaled", alpha: float = 1.0) -> np.ndarray:
    """
    Main entry point:

    mode = "theta_scaled"   -> raw θ-ladder triplet (can be aggressive)
    mode = "theta_soft"     -> softened θ triplet (sqrt + scale)
    mode = "simple"         -> original [0.7, 1.0, 1.3]
    """
    if mode == "simple":
        return simple_hand_tuned_triplet()
    if mode == "theta_soft":
        return theta_soft_triplet(alpha=alpha)
    # default
    return theta_triplet_scaled()

def constants_dict() -> Dict[str, float]:
    """
    Convenience: get constants as a plain dict, if you ever want
    to inspect/print them in analysis.
    """
    c = get_core_constants()
    return {
        "pi": c.pi,
        "phi": c.phi,
        "e": c.e,
        "sqrt3": c.sqrt3,
        "euler_gamma": c.euler_gamma,
        "apery_zeta3": c.apery_zeta3,
    }
