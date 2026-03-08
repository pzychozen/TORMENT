import numpy as np
import copy


def clone_state(state):
    """Deep clone of ModelState for diagnostic stepping."""
    return copy.deepcopy(state)


def compute_option_volume(
    model,
    state,
    *,
    dt=0.1,
    delta=1e-4,
    K=5,
    N=16,
    eps_corridor=0.05,
    eps_norm=1.0,
    rng_seed_base=1337,
):
    """
    Estimate option geometry inside the corridor using micro-perturbed clones.

    Returns dict with:
      V_opt: covariance-volume proxy (scale-sensitive; may underflow)
      R_opt: median radius around median endpoint (scale-robust)
      survival_frac: fraction of clones that stayed within corridor for K steps

    IMPORTANT:
      - Uses deterministic RNG per (state.step) so results are reproducible.
      - Computes corridor deviation on each actual transition:
            d = ||Z_vec(t+1) - Z_vec(t)|| / eps_norm
      - If too few survivors (<3), returns NaN for V_opt/R_opt to avoid fake "collapse to zero".
    """
    step_i = int(getattr(state, "step", 0))
    rng = np.random.default_rng(rng_seed_base + step_i)

    endpoints = []
    survivors = 0

    N = int(N)
    K = int(K)
    eps_norm = float(eps_norm)
    eps_corridor = float(eps_corridor)
    delta = float(delta)

    for _ in range(N):
        s = clone_state(state)

        # Micro-perturb Omega only (safest invariant)
        noise = delta * (rng.standard_normal(3) + 1j * rng.standard_normal(3))
        s.Omega = np.asarray(s.Omega, dtype=np.complex128) + noise

        # Recompute Z fields so Z_vec is consistent with perturbed Omega
        # (model_core provides update_z as a method)
        model.update_z(s)

        valid = True
        for _k in range(K):
            # corridor deviation on the actual transition
            Z0 = np.asarray(s.Z_vec, dtype=float).copy()
            model.step(s, dt=dt)
            Z1 = np.asarray(s.Z_vec, dtype=float)

            d = float(np.linalg.norm(Z1 - Z0) / eps_norm)
            if (not np.isfinite(d)) or (d > eps_corridor):
                valid = False
                break

        if valid:
            endpoints.append(np.asarray(s.Z_vec, dtype=float).copy())
            survivors += 1

    survival_frac = float(survivors) / float(N) if N > 0 else 0.0

    # If probe dies, do NOT report 0.0 (that creates fake foreclosure).
    if survivors < 3:
        return {
            "V_opt": float("nan"),
            "R_opt": float("nan"),
            "survival_frac": survival_frac,
        }

    X = np.asarray(endpoints, dtype=float)  # shape (survivors, 3)

    # Scale-robust spread metric
    center = np.median(X, axis=0)
    R_opt = float(np.median(np.linalg.norm(X - center, axis=1)))

    # Covariance-volume proxy (may underflow when spread is extremely small)
    cov = np.cov(X.T)
    V_opt = float("nan")
    if np.all(np.isfinite(cov)):
        det = float(np.linalg.det(cov))
        if det > 0.0 and np.isfinite(det):
            V_opt = float(np.sqrt(det))

    return {
        "V_opt": V_opt,
        "R_opt": R_opt,
        "survival_frac": survival_frac,
    }
