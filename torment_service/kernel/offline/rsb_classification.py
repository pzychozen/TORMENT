"""Regime classification for saved RSB observable series."""
import numpy as np


def classify_run(
    d,
    sigma_spec,
    h,
    eps_d: float = 0.03,
    delta_d: float = 1e-3,
    delta_spec: float = 1e-3,
    delta_h: float = 1e-3,
    sigma_min: float = 0.1,
    sigma_max: float = 0.9,
    sigma_coll: float = 0.1,
    h_small: float = 0.1,
    h_edge: float = 0.1,
) -> str:
    """
    Classify an RSB run into:
      - "Class I_spec"   (oscillatory / reversible)
      - "Class II_spec"  (spectral attractor)
      - "Class III_spec" (collapse)
      - or "Transitional / ambiguous"

    d, sigma_spec, h are 1D arrays over time.

    NOTE: This version prioritizes the spectral spread (sigma_spec) as the
    primary indicator:
      - very small mean sigma_spec → collapse (Class III_spec)
      - intermediate, low-variance sigma_spec → attractor (Class II_spec)
      - high variability in d / sigma_spec / h → oscillatory (Class I_spec)
    """

    d = np.asarray(d, dtype=float)
    s = np.asarray(sigma_spec, dtype=float)
    h = np.asarray(h, dtype=float)

    N = len(d)
    if N == 0:
        return "Transitional / ambiguous"

    # Tail window: last W steps, where W is at most N and at least min(50, N//4)
    W = min(N, max(N // 4, 50))
    start = N - W
    tail = slice(start, N)

    d_tail = d[tail]
    s_tail = s[tail]
    h_tail = h[tail]

    # Drop non-finite values in h_tail for stats
    finite_mask = np.isfinite(h_tail)
    if not np.any(finite_mask):
        # If helicity is completely undefined, treat it as 0 with zero variance.
        h_tail_valid = np.zeros(1, dtype=float)
    else:
        h_tail_valid = h_tail[finite_mask]

    mean_d = d_tail.mean()
    var_d = ((d_tail - mean_d) ** 2).mean()
    cv_d = (var_d ** 0.5) / max(abs(mean_d), 1e-6)

    mean_s = s_tail.mean()
    var_s = ((s_tail - mean_s) ** 2).mean()
    cv_s = (var_s ** 0.5) / max(mean_s, 1e-6)

    mean_h = h_tail_valid.mean()
    var_h = ((h_tail_valid - mean_h) ** 2).mean()

    # ------------------------------------------------------------------
    # Class III: spectral collapse
    #   - mean sigma_spec very small
    #   - low variability in sigma_spec
    #   - optionally: distance reasonably "locked" and helicity saturated
    # ------------------------------------------------------------------
    if (
        mean_s < sigma_coll              # very narrow spectrum (collapsed)
        and cv_s < delta_spec            # stable narrowness
    ):
        # Use d and h only as soft refinements, not hard gates
        return "Class III_spec"

    # ------------------------------------------------------------------
    # Class II: structured attractor
    #   - sigma_spec in an intermediate range
    #   - low variability in d and sigma_spec
    #   - helicity non-saturated but stable
    # ------------------------------------------------------------------
    if (
        sigma_min < mean_s < sigma_max   # neither collapsed nor fully spread
        and cv_s < delta_spec            # stable spectral spread
        and cv_d < delta_d               # stable distance metric
        and var_h < delta_h              # helicity not fluctuating wildly
        and abs(mean_h) < 1 - h_edge     # not fully saturated helicity
    ):
        return "Class II_spec"

    # ------------------------------------------------------------------
    # Class I: oscillatory / reversible
    #   - high variability in d or sigma_spec
    #   - and/or helicity fluctuates significantly around small mean
    # ------------------------------------------------------------------
    if (
        cv_d > delta_d
        or cv_s > delta_spec
        or (abs(mean_h) < h_small and var_h > delta_h)
    ):
        return "Class I_spec"

    # Fallback / ambiguous cases
    return "Transitional / ambiguous"
