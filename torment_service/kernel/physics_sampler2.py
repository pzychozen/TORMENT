# physics_sampler2.py
import numpy as np
import matplotlib.pyplot as plt

from .definitions import estimate_chirality_commit_time

from .cp_windows import cp_mask_from_phi_indices, default_cp_config


def cp_conditioned_masks(history):
    """
    Return boolean masks for CP-window vs non-CP steps.
    """
    phi_idx = history["phi_index"]
    cfg = default_cp_config()
    mask_cp = cp_mask_from_phi_indices(phi_idx, cfg)
    mask_non = ~mask_cp
    return mask_cp, mask_non


def summarize_cp_conditioned_observables(history, obs):
    """
    Print CP vs non-CP statistics for:
      - flavor probabilities
      - phases
      - J_eff
    """
    mask_cp, mask_non = cp_conditioned_masks(history)

    P = obs["P"]
    J = obs["J_eff"]
    th12 = obs["theta12"]
    th23 = obs["theta23"]
    th31 = obs["theta31"]

    def mean_std(x, mask):
        vals = x[mask]
        return vals.mean(), vals.std()

    print("=== CP-conditioned flavor means (⟨P1⟩,⟨P2⟩,⟨P3⟩) ===")
    for label, m in [("CP", mask_cp), ("non-CP", mask_non)]:
        P_mean = P[m].mean(axis=0)
        print(f"{label}: {P_mean[0]:.3f}, {P_mean[1]:.3f}, {P_mean[2]:.3f}")

    print("\n=== CP-conditioned phase stats (mean, std) ===")
    for label, m in [("CP", mask_cp), ("non-CP", mask_non)]:
        m12, s12 = mean_std(th12, m)
        m23, s23 = mean_std(th23, m)
        m31, s31 = mean_std(th31, m)
        print(f"{label}:")
        print(f"  theta12: mean={m12:.3f}, std={s12:.3f}")
        print(f"  theta23: mean={m23:.3f}, std={s23:.3f}")
        print(f"  theta31: mean={m31:.3f}, std={s31:.3f}")

    print("\n=== CP-conditioned J_eff stats (mean, std, min, max) ===")
    for label, m in [("CP", mask_cp), ("non-CP", mask_non)]:
        vals = J[m]
        print(f"{label}: mean={vals.mean():.4e}, std={vals.std():.4e}, "
              f"min={vals.min():.4e}, max={vals.max():.4e}")

def detect_chirality_selection_window(history, obs, frac_start=0.1, frac_end=0.2):
    """
    Detect a 'chirality selection window' for J_eff(t) in a sign-agnostic way.

    Old versions assumed monotone 0 -> negative plateau. Patch 3.7+ treats chirality
    as spontaneous with possible early flips, so we use |J_eff| for windowing and
    additionally report a canonical commit time based on stable sign locking.

    Returns:
      dict with keys:
        t_10, t_90, dt, t_commit, sign_commit
      or None if no meaningful change is detected.
    """
    t = history["t"]
    J = np.asarray(obs["J_eff"], dtype=float)

    T = len(J)
    if T < 3:
        print("Chirality selection: insufficient samples.")
        return None

    n_start = max(1, int(frac_start * T))
    n_end = max(1, int(frac_end * T))

    # initial and plateau estimates on magnitude
    A0 = np.abs(J[:n_start]).mean()
    Ap = np.abs(J[-n_end:]).mean()
    delta = Ap - A0

    if abs(delta) < 1e-12 and np.max(np.abs(J)) < 1e-9:
        print("Chirality selection: no significant chirality signal detected.")
        return None

    # thresholds on magnitude, 10% and 90% between A0 and Ap
    A_10 = A0 + 0.1 * delta
    A_90 = A0 + 0.9 * delta

    A = np.abs(J)

    # Determine crossing direction based on delta sign
    if delta >= 0:
        cond_10 = A >= A_10
        cond_90 = A >= A_90
    else:
        cond_10 = A <= A_10
        cond_90 = A <= A_90

    idx_10 = int(np.argmax(cond_10)) if cond_10.any() else None
    idx_90 = int(np.argmax(cond_90)) if cond_90.any() else None

    if idx_10 is None or idx_90 is None:
        print("Chirality selection: thresholds not crossed in data.")
        return None

    t_10 = float(t[idx_10])
    t_90 = float(t[idx_90])
    dt = float(t_90 - t_10)

    # Canonical commit time (stable sign after |J| reaches high fraction)
    t_commit_idx, sign_commit = estimate_chirality_commit_time(J, frac=0.90)
    t_commit = float(t[t_commit_idx]) if t_commit_idx is not None else None

    print("=== Chirality selection window (J_eff) ===")
    print(f"Initial |J| ≈ {A0:.4e}, plateau |J| ≈ {Ap:.4e}")
    print(f"t_10% ≈ {t_10:.3f}, t_90% ≈ {t_90:.3f}, Δt ≈ {dt:.3f}")
    if t_commit is not None:
        sgn = "+" if sign_commit > 0 else "-"
        print(f"Commit time t_commit ≈ {t_commit:.3f} (sign {sgn})")
    else:
        print("Commit time: not detected (sign may be flipping or plateau not reached).")

    return {
        "t_10": t_10,
        "t_90": t_90,
        "dt": dt,
        "t_commit": t_commit,
        "sign_commit": int(sign_commit),
    }

def plot_flavor_time_series(history, obs):
    """
    Plot P1,P2,P3 as a function of time, with CP-window hits indicated
    along the top as markers.
    """
    t = history["t"]
    P = obs["P"]          # (T,3)
    mask_cp, _ = cp_conditioned_masks(history)

    plt.figure()
    plt.plot(t, P[:, 0])
    plt.plot(t, P[:, 1])
    plt.plot(t, P[:, 2])
    plt.xlabel("time")
    plt.ylabel("P_i(t)")
    plt.title("Flavor probabilities over time")
    plt.grid(True)

    # CP-hit markers along top axis
    y_top = P.max() + 0.02
    t_cp = t[mask_cp]
    y_cp = np.full_like(t_cp, y_top)
    plt.scatter(t_cp, y_cp, marker="x")

    plt.show()


def plot_Jeff_vs_time(history, obs):
    """
    Plot J_eff(t) over time, with CP-window hits highlighted as markers.
    """
    t = history["t"]
    J = obs["J_eff"]
    mask_cp, _ = cp_conditioned_masks(history)

    plt.figure()
    plt.plot(t, J)
    plt.xlabel("time")
    plt.ylabel("J_eff(t)")
    plt.title("CP-like invariant J_eff over time")
    plt.grid(True)

    # CP-hit markers
    t_cp = t[mask_cp]
    J_cp = J[mask_cp]
    plt.scatter(t_cp, J_cp, marker="x")

    plt.show()
