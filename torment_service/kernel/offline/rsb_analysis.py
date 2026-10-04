"""RSB history analysis, seed summaries and formatting."""
import numpy as np

from .rsb_classification import classify_run
from .rsb_observables import (
    compute_rsb_observables,
    compute_spectral_energy_series,
    compute_dominant_band_series,
    compute_spectral_entropy_series,
)


def analyze_rsb_history(
    psi_hist: np.ndarray,
    chan_axis: int = 1,
    phase_axis: int = 2,
    hel_axis: int = 3,
    dark_channels: tuple = (1, 2),
    verbose: bool = True,
    seed = None,
    **classify_kwargs,
):
    """
    Convenience wrapper:
      1) compute RSB observables (d, sigma_spec, h),
      2) classify regime via classify_run,
      3) optionally print a one-line summary,
      4) attach spectral diagnostics (E_t_m, dom band, entropy).

    Returns dict with:
      - label
      - d_series, sigma_spec_series, h_series
      - E_t_m                   (T, M)
      - dom_band_series         (T,)
      - spectral_entropy_series (T,)
    """

    # 1) Compute time series from psi_hist
    obs = compute_rsb_observables(
        psi_hist,
        chan_axis=chan_axis,
        phase_axis=phase_axis,
        hel_axis=hel_axis,
        dark_channels=dark_channels,
    )

    d = np.asarray(obs["d"], dtype=float)
    s = np.asarray(obs["sigma_spec"], dtype=float)
    h = np.asarray(obs["h"], dtype=float)

    # If somehow we got no data, just return ambiguous.
    N = len(d)
    if N == 0:
        label = "Transitional / ambiguous"
        if verbose:
            print("[RSB] regime=Transitional / ambiguous (no steps)")
        return {
            "label": label,
            "d_series": d,
            "sigma_spec_series": s,
            "h_series": h,
            "E_t_m": None,
            "dom_band_series": None,
            "spectral_entropy_series": None,
        }

    # 2) Classify using classify_run
    label = classify_run(d, s, h, **classify_kwargs)

    # 3) Tail statistics for summary line (safe)
    if verbose:
        # Tail window: at most N, at least min(50, N//4)
        W = min(N, max(N // 4, 50))
        start = N - W
        tail = slice(start, N)

        d_tail = d[tail]
        s_tail = s[tail]
        h_tail = h[tail]

        mean_d = float(d_tail.mean()) if d_tail.size > 0 else float("nan")
        mean_s = float(s_tail.mean()) if s_tail.size > 0 else float("nan")

        # For h, ignore non-finite values
        if h_tail.size > 0:
            finite_mask = np.isfinite(h_tail)
            if np.any(finite_mask):
                mean_h = float(h_tail[finite_mask].mean())
            else:
                mean_h = 0.0
        else:
            mean_h = 0.0

        print(
            f"[RSB] regime={label}, "
            f"<d>≈{mean_d:.3f}, <sigma_spec^2>≈{mean_s:.3f}, <h>≈{mean_h:.3f}"
        )

    # 4) Spectral diagnostics
    E_t_m = compute_spectral_energy_series(psi_hist)          # shape (T, M)
    dom_band_series = compute_dominant_band_series(E_t_m)     # shape (T,)
    spectral_entropy_series = compute_spectral_entropy_series(E_t_m)

    stats = {
        "label": label,
        "d_series": d,
        "sigma_spec_series": s,
        "h_series": h,
        "E_t_m": E_t_m,
        "dom_band_series": dom_band_series,
        "spectral_entropy_series": spectral_entropy_series,
    }

    # Time axis for H(t) etc.  If you don't have a physical dt,
    # using index-based t = 0..T-1 is fine.
    T = len(spectral_entropy_series)
    t_axis = np.arange(T, dtype=float)

    seed_summary = summarize_rsb_seed(
        stats,
        t=t_axis,
        frac=0.10,     # 10% collapse threshold (same as before)
        seed=None,
    )
    stats["seed_summary"] = seed_summary

    # ---------------------------------------------
    # NEW: entropy-based meta class using seed_summary
    # ---------------------------------------------
    H0 = seed_summary.get("H0", None)
    HT = seed_summary.get("HT", None)
    collapsed_10 = seed_summary.get("collapsed_10pct", False)
    t_coll = seed_summary.get("t_collapse_10pct", None)

    # Default: keep raw classifier label as fallback
    meta_label = label

    if H0 is not None and HT is not None and H0 > 1e-8:
        frac = HT / H0  # final entropy as fraction of initial

        # 1) No collapse / reversible:
        #    entropy stays high, never crosses 10% threshold.
        if (not collapsed_10) and frac > 0.7:
            meta_label = "Class I_spec"   # oscillatory / reversible

        # 2) Intermediate / attractor-like:
        #    entropy settles in middle band.
        elif 0.2 < frac <= 0.7:
            meta_label = "Class II_spec"  # structured attractor / plateau

        # 3) Strong collapse:
        #    entropy drops to small fraction,
        #    does cross 10% threshold.
        elif collapsed_10 and frac <= 0.2:
            if t_coll is not None and T > 1:
                frac_coll = t_coll / float(T - 1)
                if frac_coll <= 0.20:
                    meta_label = "Class III_fast"
                else:
                    meta_label = "Class III_slow"
            else:
                meta_label = "Class III_spec"

        # 4) Weird / edge cases:
        else:
            meta_label = "Transitional / ambiguous"

    stats["meta_label"] = meta_label
    return stats


def summarize_rsb_seed(
    rsb_stats,
    t=None,
    frac=0.10,
    seed=None,
):
    """
    Build a compact, numeric summary of a single RSB trajectory
    (i.e. one seed under one parameter set).

    Parameters
    ----------
    rsb_stats : dict
        Output of `analyze_rsb_history(...)`. Expected keys:
          - "spectral_entropy_series" : array-like, H(t)
          - "dom_band_series"         : array-like, m0(t)
          - "label"                   : regime label (e.g. "Class III_collapse")
    t : array-like or None, optional
        Time axis corresponding to H(t). If None, uses np.arange(len(H)).
    frac : float, optional
        Fraction threshold for "collapse time". Default 0.10:
        t_collapse_10pct is the first time t where H(t) <= frac * H(0).
    seed : int or None, optional
        Optional seed identifier to store in the summary.

    Returns
    -------
    summary : dict
        {
          "regime": str or None,
          "seed": int or None,
          "H0": float or None,
          "HT": float or None,
          "delta_H": float or None,
          "t_collapse_10pct": float or None,
          "collapsed_10pct": bool,
          "m0_final": int or None,
          "visited_bands": list[int],
          "n_band_switches": int,
        }
    """
    # --- Pull main series out with safe defaults ---
    H_series = np.asarray(rsb_stats.get("spectral_entropy_series", []), dtype=float)
    m_series = np.asarray(rsb_stats.get("dom_band_series", []), dtype=float)

    # Time axis
    if t is None:
        t_axis = np.arange(H_series.size, dtype=float)
    else:
        t_axis = np.asarray(t, dtype=float)

    # --- Entropy summary ---
    if H_series.size > 0:
        H0 = float(H_series[0])
        HT = float(H_series[-1])
        delta_H = H0 - HT

        # Collapse time: first time H(t) <= frac * H0
        thresh = frac * H0
        idx = np.where(H_series <= thresh)[0]
        if idx.size > 0:
            t_collapse = float(t_axis[idx[0]])
            collapsed_10pct = True
        else:
            t_collapse = None
            collapsed_10pct = False
    else:
        H0 = HT = delta_H = None
        t_collapse = None
        collapsed_10pct = False

    # --- Dominant band summary ---
    if m_series.size > 0:
        # integer band index at final time
        m0_final = int(m_series[-1])

        # unique bands visited
        visited = sorted({int(x) for x in m_series})

        # count band switches
        if m_series.size > 1:
            n_switches = int(np.count_nonzero(m_series[1:] != m_series[:-1]))
        else:
            n_switches = 0
    else:
        m0_final = None
        visited = []
        n_switches = 0

    regime = rsb_stats.get("label", None)

    summary = {
        "regime": regime,
        "seed": seed,
        "H0": H0,
        "HT": HT,
        "delta_H": delta_H,
        "t_collapse_10pct": t_collapse,
        "collapsed_10pct": collapsed_10pct,
        "m0_final": m0_final,
        "visited_bands": visited,
        "n_band_switches": n_switches,
    }
    return summary


def format_rsb_seed_summary(summary):
    """
    Pretty-print an RSB seed summary dict.
    """
    lines = []

    regime = summary.get("regime", "?")
    seed = summary.get("seed", None)

    header = f"RSB seed summary"
    if seed is not None:
        header += f" (seed={seed})"
    lines.append(header)
    lines.append(f"  regime: {regime}")

    H0 = summary.get("H0", None)
    HT = summary.get("HT", None)
    dH = summary.get("delta_H", None)

    if H0 is not None and HT is not None:
        lines.append(f"  H(0)    = {H0:.3f}")
        lines.append(f"  H(T)    = {HT:.3f}")
        lines.append(f"  ΔH      = {dH:.3f}")
    else:
        lines.append("  H(0), H(T), ΔH: N/A")

    t_col = summary.get("t_collapse_10pct", None)
    if t_col is not None:
        lines.append(f"  t_collapse_10pct ≈ {t_col:.3f}")
    else:
        lines.append("  t_collapse_10pct: none (no 10% collapse)")

    m0 = summary.get("m0_final", None)
    visited = summary.get("visited_bands", [])
    n_sw = summary.get("n_band_switches", 0)

    lines.append(f"  m₀(T)   = {m0}")
    lines.append(f"  visited bands = {visited}")
    lines.append(f"  # band switches = {n_sw}")

    return "\n".join(lines)
