# definitions.py
# ============================================================
# Canonical, deterministic metric / observable definitions.
#
# RULES:
#   - No RNG usage here.
#   - No plotting here.
#   - No file I/O here.
#   - Must not mutate input histories.
#
# This module exists to prevent "metric drift" across:
#   UI plots, scans, diagnostics, and paper figures.
# ============================================================
import numpy as np

# ------------------------------------------------------------
# SECTION 0: TriOcta chirality (Jeff) canonical definitions
# ------------------------------------------------------------

EPS = 1e-12

def compute_jeff_from_omega(Omega: np.ndarray) -> float:
    """Canonical J_eff definition: Im(Ω1 Ω2* Ω3)."""
    Om = np.asarray(Omega)
    if Om.shape != (3,):
        Om = Om.reshape(3,)
    return float(np.imag(Om[0] * np.conj(Om[1]) * Om[2]))


def compute_jeff_series(hist: dict) -> np.ndarray:
    """Return Jeff(t) as a 1D float array.

    Preference order:
      1) hist['J_eff'] if present
      2) derived from hist['Omega'] via compute_jeff_from_omega
    """
    if hist is None:
        raise ValueError("hist is required")
    if "J_eff" in hist and hist["J_eff"] is not None and len(hist["J_eff"]) > 0:
        return np.asarray(hist["J_eff"], dtype=float)

    if "Omega" not in hist:
        raise KeyError("history must contain 'J_eff' or 'Omega'")
    Om = np.asarray(hist["Omega"])
    if Om.ndim != 2 or Om.shape[1] != 3:
        raise ValueError(f"hist['Omega'] must have shape (T,3); got {Om.shape}")
    return np.array([compute_jeff_from_omega(Om[t]) for t in range(Om.shape[0])], dtype=float)


def chirality_sign(j: float, deadband: float = 1e-9) -> int:
    """Map Jeff to sign (+1/-1) with a deadband around 0."""
    if not np.isfinite(j) or abs(j) <= deadband:
        return 0
    return 1 if j > 0 else -1


def count_sign_flips(j_series: np.ndarray, deadband: float = 1e-9) -> int:
    """Count sign flips in Jeff, ignoring near-zero values."""
    j = np.asarray(j_series, dtype=float)
    s = np.array([chirality_sign(x, deadband=deadband) for x in j], dtype=int)
    s = s[s != 0]
    if s.size < 2:
        return 0
    return int(np.sum(s[1:] != s[:-1]))


def estimate_chirality_commit_time(j_series: np.ndarray, frac: float = 0.90, deadband: float = 1e-9):
    """Estimate chirality commit time.

    Finds the first index t where |J(t)| reaches frac * max(|J|) and
    all subsequent nonzero Jeff signs remain the same.
    Returns (t_commit_index, sign) or (None, 0).
    """
    j = np.asarray(j_series, dtype=float)
    if j.size == 0:
        return None, 0
    a = np.abs(j)
    amax = float(np.max(a))
    if not np.isfinite(amax) or amax <= deadband:
        return None, 0

    thresh = frac * amax
    for t in range(j.size):
        if a[t] >= thresh:
            s0 = chirality_sign(j[t], deadband=deadband)
            if s0 == 0:
                continue
            rest = np.array([chirality_sign(x, deadband=deadband) for x in j[t:]], dtype=int)
            rest = rest[rest != 0]
            if rest.size == 0:
                return t, s0
            if np.all(rest == s0):
                return t, s0
    return None, 0


def jeff_radius_stats(j_series: np.ndarray):
    """Return (median(|J|), p05(|J|), p95(|J|))."""
    a = np.abs(np.asarray(j_series, dtype=float))
    if a.size == 0:
        return 0.0, 0.0, 0.0
    return float(np.median(a)), float(np.quantile(a, 0.05)), float(np.quantile(a, 0.95))


# ------------------------------------------------------------
# SECTION 0b: v_rec canonical baselines (entropy + geometry)
# ------------------------------------------------------------

def vrec_entropy(H_series: np.ndarray) -> np.ndarray:
    """Canonical entropy v_rec baseline: |ΔH|. Returns length T-1."""
    H = np.asarray(H_series, dtype=float)
    if H.size < 2:
        return np.array([], dtype=float)
    return np.abs(np.diff(H))


def vrec_geom_direction(hist: dict, z_key: str = "Z_total",
                        norm_floor: float = 1e-9) -> np.ndarray:
    """
    Direction-only geometric v_rec:
        θ_t = arccos( û(t) · û(t+1) )
    BUT: returns NaN where ||Z|| is too small, because direction is undefined.
    """
    key = z_key
    if key not in hist:
        key = "Z_vec" if "Z_vec" in hist else key

    Z = np.asarray(hist[key], dtype=float)
    if Z.ndim != 2 or Z.shape[0] < 2:
        return np.array([], dtype=float)

    n = np.linalg.norm(Z, axis=1)

    # Normalize only where safe
    U = np.full_like(Z, np.nan, dtype=float)
    good = n > norm_floor
    U[good] = Z[good] / n[good, None]

    # Direction angle between successive U, but only if both are good
    good_pairs = good[:-1] & good[1:]
    dots = np.full(Z.shape[0] - 1, np.nan, dtype=float)
    dots[good_pairs] = np.sum(U[1:][good_pairs] * U[:-1][good_pairs], axis=1)
    dots = np.clip(dots, -1.0, 1.0, out=dots)  # keeps NaNs as NaN

    return np.arccos(dots)


def estimate_chirality_timescale(t, J):
    """
    Roughly reproduce the 10%–90% chirality window:
    - J0 = initial value
    - Jp = late-time plateau (mean of last 20 steps)
    - find first t where J crosses 10% and 90% of the way from J0 to Jp
    Returns (t10, t90, dt) or (None, None, None) if it fails.
    """
    J0 = J[0]
    Jp = J[-20:].mean()
    dJ = Jp - J0

    if abs(dJ) < 1e-12:
        return None, None, None  # no real evolution

    J10 = J0 + 0.1 * dJ
    J90 = J0 + 0.9 * dJ

    t10 = None
    t90 = None

    for ti, Ji in zip(t, J):
        if t10 is None and ((dJ > 0 and Ji >= J10) or (dJ < 0 and Ji <= J10)):
            t10 = ti
        if t90 is None and ((dJ > 0 and Ji >= J90) or (dJ < 0 and Ji <= J90)):
            t90 = ti

    if t10 is None or t90 is None:
        return None, None, None

    return t10, t90, (t90 - t10)


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


# SECTION X: RSB (spectral) diagnostics
# ============================================================

def compute_spectral_energy_series(psi_hist: np.ndarray) -> np.ndarray:
    """
    Compute spectral energy per phase band over time.

    Args:
        psi_hist: array of shape (T, C, M, H)
                  (typically as returned by RSBModel.run)

    Returns:
        E_t_m: array of shape (T, M) with spectral energy per band over time.
    """
    arr = np.asarray(psi_hist)
    if arr.ndim != 4:
        raise ValueError(f"Expected psi_hist with 4 dims (T,C,M,H), got {arr.shape}")
    # sum over channels C and helicity H
    E_t_m = np.sum(np.abs(arr) ** 2, axis=(1, 3))  # (T, M)
    return E_t_m


def _wrap_angle_pi(x: np.ndarray) -> np.ndarray:
    """Wrap angles to [-pi, pi]."""
    return (x + np.pi) % (2 * np.pi) - np.pi

def compute_recursive_velocity_geom(
    hist: dict,
    z_key: str = "Z_total",
    w_z: float = 1.0,
    w_phase: float = 1.0,
    w_corridor: float = 0.5,
    w_kappa: float = 0.0,
    return_components: bool = False,
):
    """
    Geometry-aware recursive velocity computed from *saved* histories (deterministic).

    Components:
      - dZ:      step length in chosen Z-space (macro/chiral/total)
      - dphi:    mean phase step inferred from Omega(t+1)*conj(Omega(t))
      - dcorr:   corridor jump indicator from phi_index changes
      - dkappa:  optional kappa step magnitude

    The combined metric is:
        v_geom = sqrt( (w_z*dZ)^2 + (w_phase*dphi)^2 + (w_corridor*dcorr)^2 + (w_kappa*dkappa)^2 )

    Returns:
      v_geom (T-1,)  or (v_geom, components_dict) if return_components=True
    """
    if hist is None:
        raise ValueError("hist is required")

    # --- Z step length ---
    if z_key not in hist:
        # fallback to legacy key if needed
        z_key_eff = "Z_vec" if "Z_vec" in hist else z_key
    else:
        z_key_eff = z_key

    Z = np.asarray(hist[z_key_eff], dtype=float)
    if Z.ndim != 2 or Z.shape[0] < 2:
        v = np.zeros(max(0, Z.shape[0]-1), dtype=float)
        return (v, {}) if return_components else v

    dZ_vec = Z[1:] - Z[:-1]
    dZ = np.linalg.norm(dZ_vec, axis=1)

    # --- mean phase step from Omega ---
    Omega = np.asarray(hist.get("Omega", []))
    if Omega is None or np.size(Omega) == 0 or Omega.shape[0] < 2:
        dphi = np.zeros_like(dZ)
    else:
        prod = np.mean(Omega[1:] * np.conj(Omega[:-1]), axis=1)
        dphi = np.abs(_wrap_angle_pi(np.angle(prod)))

    # --- corridor jump ---
    phi_idx = np.asarray(hist.get("phi_index", []))
    if phi_idx is None or phi_idx.size < 2:
        dcorr = np.zeros_like(dZ)
    else:
        dcorr = (phi_idx[1:] != phi_idx[:-1]).astype(float)

    # --- kappa step (optional) ---
    kappa = np.asarray(hist.get("kappa", []), dtype=float)
    if kappa is None or kappa.size < 2:
        dkappa = np.zeros_like(dZ)
    else:
        dkappa = np.abs(np.diff(kappa))

    v_geom = np.sqrt((w_z * dZ) ** 2 + (w_phase * dphi) ** 2 + (w_corridor * dcorr) ** 2 + (w_kappa * dkappa) ** 2)

    if return_components:
        comps = {
            "z_key": z_key_eff,
            "dZ": dZ,
            "dphi": dphi,
            "dcorr": dcorr,
            "dkappa": dkappa,
        }
        return v_geom, comps
    return v_geom

def compute_recursive_velocity(H_series: np.ndarray) -> np.ndarray:
    """
    Recursive velocity v_rec(n) ~ |ΔH(n)| between timesteps.

    For now we define it as the absolute difference of spectral entropy:
        v_rec[n] = | H[n+1] - H[n] |.

    This can be refined later to angular velocity in phase space, etc.
    """
    H = np.asarray(H_series, dtype=float)
    if H.size < 2:
        return np.zeros_like(H)
    return np.abs(np.diff(H))

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


def compute_dominant_band_series(E_t_m: np.ndarray) -> np.ndarray:
    """
    E_t_m: (T, M)
    Returns:
        m0_series: (T,) dominant band indices over time.
    """
    E_t_m = np.asarray(E_t_m)
    if E_t_m.ndim != 2:
        raise ValueError(f"Expected E_t_m shape (T,M), got {E_t_m.shape}")
    return np.argmax(E_t_m, axis=1)


def compute_spectral_entropy_series(E_t_m: np.ndarray) -> np.ndarray:
    """
    E_t_m: (T, M)
    Returns:
        H_series: (T,) normalized spectral entropy in [0, 1].
    """
    E_t_m = np.asarray(E_t_m)
    if E_t_m.ndim != 2:
        raise ValueError(f"Expected E_t_m shape (T,M), got {E_t_m.shape}")

    T, M = E_t_m.shape
    H_series = np.zeros(T, dtype=float)

    for t in range(T):
        E_m = E_t_m[t]
        total = E_m.sum()
        if total <= 0.0:
            H_series[t] = 0.0
            continue
        p_m = E_m / total
        S = -np.sum(p_m * np.log(p_m + 1e-12))
        H_series[t] = S / np.log(M + 1e-12)

    return H_series


def compute_rsb_observables(
    psi_hist: np.ndarray,
    chan_axis: int = 1,
    phase_axis: int = 2,
    hel_axis: int = 3,
    dark_channels: tuple = (1, 2),
):
    """
    Compute RSB observables (d, sigma_spec, h) from psi_hist.

    Args:
        psi_hist: complex array with 4 axes: time, channels, phases, helicity.
                  By default we assume (T, C, M, H), but chan/phase/hel axes
                  can be overridden via chan_axis, phase_axis, hel_axis.
        chan_axis: index of the channel axis in psi_hist.
        phase_axis: index of the phase (band) axis in psi_hist.
        hel_axis: index of the helicity axis in psi_hist.
        dark_channels: tuple of channel indices to treat as "dark".

    Returns:
        dict with 1D arrays:
          - "d"          : distance between visible and mean dark channel
          - "sigma_spec" : spectral variance of band index
          - "h"          : helicity asymmetry for visible channel
    """
    arr = np.asarray(psi_hist)
    if arr.ndim != 4:
        raise ValueError(f"Expected psi_hist with 4 dims, got {arr.shape}")

    # Determine time axis as "the one that is not chan/phase/hel"
    all_axes = set(range(arr.ndim))
    other_axes = {chan_axis, phase_axis, hel_axis}
    time_axes = list(all_axes - other_axes)
    if len(time_axes) != 1:
        raise ValueError(
            f"Could not infer time axis from chan={chan_axis}, "
            f"phase={phase_axis}, hel={hel_axis} in shape {arr.shape}"
        )
    time_axis = time_axes[0]

    # Reorder to (T, C, M, H)
    psi_t = np.moveaxis(
        arr,
        (time_axis, chan_axis, phase_axis, hel_axis),
        (0, 1, 2, 3),
    )  # shape (T, C, M, H)

    T = psi_t.shape[0]
    d_list = []
    s_list = []
    h_list = []

    for t in range(T):
        psi = psi_t[t]  # shape (C, M, H)

        # --- dark / visible split ---
        # assume channel 0 is visible, dark_channels are dark
        vis = psi[0]
        dark = psi[list(dark_channels)]

        dark_mean = np.mean(dark, axis=0)
        d_val = np.linalg.norm(vis - dark_mean)
        d_list.append(d_val)

        # --- spectral variance (sigma_spec^2) ---
        # energy per phase index
        E_m = np.sum(np.abs(psi) ** 2, axis=(0, 2))  # shape (M,)
        E_tot = E_m.sum() + 1e-14
        p_m = E_m / E_tot

        m_indices = np.arange(E_m.shape[0])
        mean_m = np.sum(m_indices * p_m)
        var_m = np.sum((m_indices - mean_m) ** 2 * p_m)
        s_list.append(var_m)

        # --- helicity asymmetry ---
        H = psi.shape[2]
        if H >= 2:
            # compare helicity 0 vs 1 for visible
            h0 = np.sum(np.abs(vis[:, 0]) ** 2)
            h1 = np.sum(np.abs(vis[:, 1]) ** 2)
            denom = h0 + h1 + 1e-14
            h_val = (h0 - h1) / denom
        else:
            h_val = 0.0
        h_list.append(h_val)

    return {
        "d": np.array(d_list, dtype=float),
        "sigma_spec": np.array(s_list, dtype=float),
        "h": np.array(h_list, dtype=float),
    }


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
