# physics_sampler.py
import numpy as np
import matplotlib.pyplot as plt

from .definitions import compute_jeff_from_omega


def compute_flavor_probabilities(Omega_history: np.ndarray):
    """
    Omega_history: shape (T, 3) complex, from history["Omega"].

    Returns:
      P: shape (T, 3) real, each row sums to 1 (up to numerical noise).
    """
    mags2 = np.abs(Omega_history)**2  # (T,3)
    norms = mags2.sum(axis=1, keepdims=True) + 1e-12
    P = mags2 / norms
    return P


def compute_relative_phases(Omega_history: np.ndarray):
    """
    Compute pairwise relative phases:

      θ12 = arg(Ω1 Ω2*)
      θ23 = arg(Ω2 Ω3*)
      θ31 = arg(Ω3 Ω1*)

    Returns:
      phases: dict with keys "theta12", "theta23", "theta31" (each length T).
    """
    Ω1 = Omega_history[:, 0]
    Ω2 = Omega_history[:, 1]
    Ω3 = Omega_history[:, 2]

    theta12 = np.angle(Ω1 * np.conjugate(Ω2))
    theta23 = np.angle(Ω2 * np.conjugate(Ω3))
    theta31 = np.angle(Ω3 * np.conjugate(Ω1))

    return {
        "theta12": theta12,
        "theta23": theta23,
        "theta31": theta31,
    }


def compute_cp_like_invariant(Omega_history: np.ndarray):
    """
    Canonical chirality observable:
      J_eff(t) = Im(Ω1 Ω2* Ω3)

    Implemented via the centralized definition in definitions.py
    (compute_jeff_from_omega) to prevent drift across modules.
    """
    Omega_history = np.asarray(Omega_history)
    if Omega_history.ndim != 2 or Omega_history.shape[1] != 3:
        raise ValueError("Omega_history must have shape (T,3) complex")
    return np.array([compute_jeff_from_omega(Omega_history[t]) for t in range(len(Omega_history))], dtype=float)



def sample_physics_observables(history):
    """
    High-level helper: given history dict, compute and return observables.

    Returns:
      obs: dict with keys:
        "P"         -> (T,3) flavor probabilities
        "theta12"   -> (T,)
        "theta23"   -> (T,)
        "theta31"   -> (T,)
        "J_eff"     -> (T,)
    """
    Omega_hist = history["Omega"]   # (T,3) complex

    P = compute_flavor_probabilities(Omega_hist)
    phases = compute_relative_phases(Omega_hist)
    J_eff = compute_cp_like_invariant(Omega_hist)

    obs = {
        "P": P,
        "theta12": phases["theta12"],
        "theta23": phases["theta23"],
        "theta31": phases["theta31"],
        "J_eff": J_eff,
    }
    return obs


def summarize_observables(obs):
    """
    Print some basics: flavor averages, phase spreads, J_eff stats.
    """
    P = obs["P"]
    J_eff = obs["J_eff"]

    P_mean = P.mean(axis=0)
    print("Flavor probability means (⟨P1⟩,⟨P2⟩,⟨P3⟩):",
          f"{P_mean[0]:.3f}, {P_mean[1]:.3f}, {P_mean[2]:.3f}")

    for key in ["theta12", "theta23", "theta31"]:
        ph = obs[key]
        print(f"{key}: mean={ph.mean():.3f}, std={ph.std():.3f}")

    print(f"J_eff: mean={J_eff.mean():.4e}, "
          f"std={J_eff.std():.4e}, "
          f"min={J_eff.min():.4e}, max={J_eff.max():.4e}")


def plot_phase_and_cp_distributions(obs):
    """
    Plot histograms of relative phases and J_eff.
    """
    theta12 = obs["theta12"]
    theta23 = obs["theta23"]
    theta31 = obs["theta31"]
    J_eff = obs["J_eff"]

    # relative phase histograms
    plt.figure()
    plt.hist(theta12, bins=30, alpha=0.5)
    plt.hist(theta23, bins=30, alpha=0.5)
    plt.hist(theta31, bins=30, alpha=0.5)
    plt.xlabel("relative phase (radians)")
    plt.ylabel("count")
    plt.title("Distributions of relative phases θ12, θ23, θ31")
    plt.grid(True)

    # J_eff histogram
    plt.figure()
    plt.hist(J_eff, bins=30)
    plt.xlabel("J_eff")
    plt.ylabel("count")
    plt.title("Distribution of CP-like invariant J_eff")
    plt.grid(True)

    plt.show()
