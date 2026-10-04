"""Diagnostic stabilization estimates for saved Z directions."""
import numpy as np


def estimate_z_stabilization_time(
    hist: dict,
    z_key: str = "Z_total",
    settle_deg: float = 15.0,
    min_norm: float = 1e-10,
    tail: int = 30,
):
    """Estimate a "Z stabilization" time t_Z for a chosen Z component.

    This is intentionally a *diagnostic* (not a definition of dynamics): it detects when
    the *direction* of Z stops wandering and becomes aligned with its late-time mean.

    Method:
      1) Let Z(t) be hist[z_key] (fallback to Z_vec if needed).
      2) Compute the late-time reference direction u* from the mean over the last `tail` steps.
      3) Compute the running mean direction u(t) = mean(Z[:t]) / ||mean(Z[:t])||.
      4) Return the first time where angle(u(t), u*) <= settle_deg AND ||mean(Z[:t])|| >= min_norm.

    Returns:
      t_Z (float) or None if it cannot be estimated.
    """
    if hist is None or "t" not in hist:
        return None

    key = z_key if z_key in hist else ("Z_vec" if "Z_vec" in hist else z_key)
    if key not in hist:
        return None

    Z = np.asarray(hist[key], dtype=float)
    t = np.asarray(hist["t"], dtype=float)
    if Z.ndim != 2 or Z.shape[0] < max(5, tail) or t.shape[0] != Z.shape[0]:
        return None

    Z_tail = np.mean(Z[-tail:], axis=0)
    n_tail = float(np.linalg.norm(Z_tail))
    if not np.isfinite(n_tail) or n_tail < min_norm:
        return None

    u_star = Z_tail / n_tail
    cos_thresh = float(np.cos(np.deg2rad(settle_deg)))

    # Running mean (prefix) to capture "meta-shell" settling
    Z_cum = np.cumsum(Z, axis=0)
    for i in range(4, Z.shape[0]):
        mu = Z_cum[i] / float(i + 1)
        n_mu = float(np.linalg.norm(mu))
        if not np.isfinite(n_mu) or n_mu < min_norm:
            continue
        u = mu / n_mu
        c = float(np.clip(np.dot(u, u_star), -1.0, 1.0))
        if c >= cos_thresh:
            return float(t[i])

    return None
