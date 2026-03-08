# diagnostics.py
# ============================================================
# Central place for all extended analysis / tests / scans
# ============================================================

import numpy as np
from .definitions import (
    estimate_chirality_timescale,
    compute_spectral_energy_series,
    compute_dominant_band_series,
    compute_spectral_entropy_series,
    compute_recursive_velocity,
    compute_recursive_velocity_geom,
    compute_rsb_observables,
    analyze_rsb_history,
    classify_run,
    summarize_rsb_seed,
    format_rsb_seed_summary,
)


# --- Core model imports ---
from .model_core import ModelParams, ModelState, TriOctaPhaseLockModel
from .constants_selector import default_k_triplet

# --- Flavor / physics observables ---
from .physics_sampler import sample_physics_observables
from .physics_sampler2 import (
    summarize_cp_conditioned_observables,
    plot_flavor_time_series,
    plot_Jeff_vs_time,
    detect_chirality_selection_window,
)

from .cp_windows import cp_mask_from_phi_indices, default_cp_config


# --- Corridor / Δ-cluster analysis ---
from .tangent_corridor_analysis import (
    detect_tangent_corridors,
    cluster_delta_kz,
    cp_split_big_delta_events,
)

# ============================================================
# SECTION 1: Basic run wrapper (run_once)
# ============================================================
def run_once(params: ModelParams):
    """
    Run the full pipeline for a single parameter set:
    - build model
    - integrate
    - collect history + observables
    - run key diagnostics (chirality window + Δ(κ,Z) clustering)
    Returns (hist, obs, big_steps_mask, mags) so a parameter scan
    can extract summary numbers.
    """

    # --- state init: mirror your __main__ block ---
    rng = np.random.default_rng(0)
    Omega0 = 0.1 * (rng.standard_normal(3) + 1j * rng.standard_normal(3))
    state = ModelState(Omega=Omega0)

    # --- build model + integrate ---
    model = TriOctaPhaseLockModel(params)
    hist = model.run(state, n_steps=200, dt=0.05)

    # --- physics-shaped observables ---
    obs = sample_physics_observables(hist)

    # (optional: comment these out if you don't want plots during scans)
    # summarize_observables(obs)
    # plot_phase_and_cp_distributions(obs)

    # CP-conditioned views + chirality window
    summarize_cp_conditioned_observables(hist, obs)
    plot_flavor_time_series(hist, obs)
    plot_Jeff_vs_time(hist, obs)
    detect_chirality_selection_window(hist, obs)

    # Tangent corridor alignment + Δ
    mask_tan, xy, jumpvec, dot = detect_tangent_corridors(hist)

    # (κ,Z) clustering view
    big_steps_mask, mags = cluster_delta_kz(hist, frac_of_max=0.5)

    return hist, obs, big_steps_mask, mags

# ============================================================
# SECTION 2: Chirality timescale estimator
# ============================================================
# NOTE: canonical implementation lives in definitions.py

# ============================================================
# SECTION 3: Initial-condition robustness scan
# ============================================================
def run_ic_scan(
    params: ModelParams,
    n_inits: int = 32,
    seed: int = 123,
    verbose: bool = True,
):
    """
    Initial-condition robustness test:
    - Fix params
    - Run n_inits random Omega0
    - Record J_plateau sign, chirality timescale, and strong Δ(κ,Z) stats.
    If verbose=True, prints a summary; always returns a list of per-run dicts.
    """
    rng = np.random.default_rng(seed)
    summaries = []

    for i in range(n_inits):
        # Random initial Omega0 (normalized)
        Omega0 = 0.1 * (rng.standard_normal(3) + 1j * rng.standard_normal(3))
        Omega0 /= np.linalg.norm(Omega0)

        state = ModelState(Omega=Omega0)
        model = TriOctaPhaseLockModel(params)
        hist = model.run(state, n_steps=200, dt=0.05)

        # Physics observables (includes J_eff etc.)
        from physics_sampler2 import sample_physics_observables
        obs = sample_physics_observables(hist)

        J = np.asarray(obs["J_eff"])
        t = np.asarray(hist["t"])

        J_plateau = J[-20:].mean()
        sign_J = int(np.sign(J_plateau))

        t10, t90, dtJ = estimate_chirality_timescale(t, J)

        # Δ(κ,Z) clustering (same diagnostic as before)
        big_mask, mags = cluster_delta_kz(hist, frac_of_max=0.5)
        num_strong_delta = int(big_mask.sum())
        max_delta = float(mags.max())

        summaries.append({
            "run": i,
            "J_plateau": float(J_plateau),
            "J_sign": sign_J,
            "t10": t10,
            "t90": t90,
            "dtJ": dtJ,
            "num_strong_delta": num_strong_delta,
            "max_delta": max_delta,
        })

    # --- Print ensemble summary (optional) ---
    if verbose:
        print("\n=== Initial-condition robustness scan ===")
        J_signs = [s["J_sign"] for s in summaries]
        num_pos = sum(1 for s in J_signs if s > 0)
        num_neg = sum(1 for s in J_signs if s < 0)
        num_zero = sum(1 for s in J_signs if s == 0)

        print(f"Total runs: {n_inits}")
        print(f"  J_sign > 0 : {num_pos}")
        print(f"  J_sign < 0 : {num_neg}")
        print(f"  J_sign = 0 : {num_zero}")

        dts = [s["dtJ"] for s in summaries if s["dtJ"] is not None]
        if dts:
            print(f"  Δt_J mean ≈ {np.mean(dts):.3f}, std ≈ {np.std(dts):.3f}")

        strong_counts = [s["num_strong_delta"] for s in summaries]
        print(
            f"  strong Δ(κ,Z) steps: mean ≈ {np.mean(strong_counts):.2f}, "
            f"std ≈ {np.std(strong_counts):.2f}"
        )
        print(
            f"  max |Δ(κ,Z)| across runs ≈ "
            f"{max(s['max_delta'] for s in summaries):.4e}"
        )

    return summaries

# ============================================================
# SECTION 4: Δ-sector histogram helper (Test 3)
# ============================================================
def strong_delta_sector_histogram(history, big_steps_mask, cp_cfg=None):
    """
    For a single run:
    - take big_steps_mask (strong Δ(κ,Z) events from cluster_delta_kz)
    - map them to arrival φ indices (phi_index[1:])
    - build 12-bin histograms:
        * overall strong events per sector
        * CP-tagged strong events per sector
        * non-CP-tagged strong events per sector
    Returns (all_counts, cp_counts, ncp_counts), each length-12 arrays.
    """
    phi_idx = np.asarray(history["phi_index"])
    N = len(phi_idx)

    L = len(big_steps_mask)
    if L + 1 > N:
        # safety trim if lengths ever differ
        L = N - 1
        big_steps_mask = big_steps_mask[:L]

    # arrival corridor index for each Δ-step (step t → t+1)
    arrival_phi = phi_idx[1:L+1]

    # strong steps
    strong = big_steps_mask[:L]
    if strong.sum() == 0:
        return (
            np.zeros(12, dtype=int),
            np.zeros(12, dtype=int),
            np.zeros(12, dtype=int),
        )

    if cp_cfg is None:
        cp_cfg = default_cp_config()

    cp_time_mask = cp_mask_from_phi_indices(phi_idx, cp_cfg)  # per time index
    cp_arrival = cp_time_mask[1:L+1]                          # per Δ-step

    # All strong steps
    strong_phi_all = arrival_phi[strong]
    sector_all = np.mod(np.round(strong_phi_all).astype(int), 12)
    all_counts = np.bincount(sector_all, minlength=12)

    # CP-tagged strong steps
    strong_cp = strong & cp_arrival
    strong_ncp = strong & (~cp_arrival)

    cp_counts = np.zeros(12, dtype=int)
    ncp_counts = np.zeros(12, dtype=int)

    if strong_cp.any():
        strong_phi_cp = arrival_phi[strong_cp]
        sector_cp = np.mod(np.round(strong_phi_cp).astype(int), 12)
        cp_counts = np.bincount(sector_cp, minlength=12)

    if strong_ncp.any():
        strong_phi_ncp = arrival_phi[strong_ncp]
        sector_ncp = np.mod(np.round(strong_phi_ncp).astype(int), 12)
        ncp_counts = np.bincount(sector_ncp, minlength=12)

    return all_counts, cp_counts, ncp_counts

# ============================================================
# SECTION 5: Jeff coupling analysis
# ============================================================
def analyze_Jeff_coupling(history, obs, big_steps_mask):
    """
    Jeff–Δ(κ,Z) coupling test.

    Given:
      - history: dict-like with "t"
      - obs:     dict-like with "J_eff" (from sample_physics_observables)
      - big_steps_mask: boolean array of length ~ N-1 marking strong Δ(κ,Z) steps
                        (e.g. from cluster_delta_kz(..., frac_of_max=0.5))

    This computes |dJ_eff/dt| on each step and compares:
      - strong Δ steps      (big_steps_mask == True)
      - background steps    (big_steps_mask == False)

    It prints:
      - mean / std of |dJ/dt| in strong vs background
      - fraction of total |dJ|-activity captured by strong Δ steps
    """
    t = np.asarray(history["t"])
    J = np.asarray(obs["J_eff"])

    if len(t) != len(J):
        print("[WARN] t and J_eff length mismatch, attempting to trim.")
        L = min(len(t), len(J))
        t = t[:L]
        J = J[:L]

    if len(t) < 2:
        print("[WARN] Not enough points to compute dJ/dt.")
        return None

    # Finite-difference derivative of Jeff
    dt = np.diff(t)
    dJ = np.diff(J)
    dJ_dt = dJ / (dt + 1e-12)  # guard against degenerate dt
    abs_dJ_dt = np.abs(dJ_dt)

    L_steps = len(abs_dJ_dt)
    if len(big_steps_mask) != L_steps:
        # align to common length if something was changed upstream
        L_common = min(L_steps, len(big_steps_mask))
        abs_dJ_dt = abs_dJ_dt[:L_common]
        big_steps_mask = big_steps_mask[:L_common]

    strong_mask = big_steps_mask.astype(bool)
    background_mask = ~strong_mask

    if not strong_mask.any():
        print("\n[Jeff–Δ coupling] No strong Δ(κ,Z) steps found.")
        return None

    strong_vals = abs_dJ_dt[strong_mask]
    back_vals = abs_dJ_dt[background_mask]

    mean_strong = strong_vals.mean()
    std_strong = strong_vals.std()
    mean_back = back_vals.mean()
    std_back = back_vals.std()

    total_activity = abs_dJ_dt.sum()
    strong_activity = strong_vals.sum()
    frac_activity = strong_activity / (total_activity + 1e-18)

    ratio = mean_strong / (mean_back + 1e-18)

    print("\n=== Jeff–Δ(κ,Z) coupling diagnostics ===")
    print(f"Strong Δ steps      : {strong_mask.sum()} / {len(abs_dJ_dt)}")
    print(f"Background steps    : {background_mask.sum()} / {len(abs_dJ_dt)}")
    print(f"⟨|dJ/dt|⟩ strong     ≈ {mean_strong:.4e} (std ≈ {std_strong:.4e})")
    print(f"⟨|dJ/dt|⟩ background ≈ {mean_back:.4e} (std ≈ {std_back:.4e})")
    print(f"Ratio strong / background ≈ {ratio:.2f}×")
    print(f"Strong Δ steps carry ≈ {100.0 * frac_activity:.1f}% "
          f"of total |dJ| activity.")

    return {
        "mean_strong": mean_strong,
        "std_strong": std_strong,
        "mean_back": mean_back,
        "std_back": std_back,
        "ratio": ratio,
        "frac_activity": frac_activity,
        "n_strong": int(strong_mask.sum()),
        "n_background": int(background_mask.sum()),
    }

# ============================================================
# SECTION 6: Corridor spectroscopy scan (Test 5)
# ============================================================
def run_corridor_spectroscopy_scan(params: ModelParams,
                                   n_inits: int = 32,
                                   seed: int = 321,
                                   frac_of_max: float = 0.5):
    """
    Test 5: corridor spectroscopy across many initial conditions.

    For each IC:
      - draw random Ω0
      - run model
      - detect strong Δ(κ,Z) events via cluster_delta_kz
      - build 12-bin histograms of strong events vs φ sector
        (all, CP-tagged, non-CP-tagged)

    At the end:
      - print total counts per sector
      - print normalized fractions per sector
      - print CP vs non-CP band widths (# of sectors with any events)
    """
    rng = np.random.default_rng(seed)

    total_all = np.zeros(12, dtype=int)
    total_cp = np.zeros(12, dtype=int)
    total_ncp = np.zeros(12, dtype=int)

    all_strong_counts = []

    for i in range(n_inits):
        # random normalized Ω0
        Omega0 = 0.1 * (rng.standard_normal(3) + 1j * rng.standard_normal(3))
        Omega0 /= np.linalg.norm(Omega0)

        state = ModelState(Omega=Omega0)
        model = TriOctaPhaseLockModel(params)
        hist = model.run(state, n_steps=200, dt=0.05)

        # strong Δ(κ,Z) events for this run
        big_steps_mask, mags = cluster_delta_kz(hist, frac_of_max=frac_of_max)
        all_strong_counts.append(int(big_steps_mask.sum()))

        all_c, cp_c, ncp_c = strong_delta_sector_histogram(hist, big_steps_mask)
        total_all += all_c
        total_cp += cp_c
        total_ncp += ncp_c

    # --- summary ---
    print("\n=== Corridor spectroscopy scan (many ICs) ===")
    print(f"Parameters: eps={params.eps}, g={params.g}, k_vals={params.k_vals}")
    print(f"Number of IC runs: {n_inits}")
    print(f"Mean strong Δ(κ,Z) steps per run: "
          f"{np.mean(all_strong_counts):.2f} ± {np.std(all_strong_counts):.2f}")

    total_strong = total_all.sum()
    total_cp_strong = total_cp.sum()
    total_ncp_strong = total_ncp.sum()

    print(f"\nTotal strong Δ events across all runs: {total_strong}")
    print(f"  of which CP-tagged   : {total_cp_strong}")
    print(f"           non-CP-tagged: {total_ncp_strong}")

    def print_sector_summary(label, counts):
        s = counts.sum()
        nonzero = np.count_nonzero(counts)
        print(f"\n{label}:")
        print(f"  total events = {s}, support sectors (nonzero bins) = {nonzero}")
        if s > 0:
            frac = counts / s
            for k in range(12):
                if counts[k] > 0:
                    print(f"    sector {k:2d}: count={counts[k]:3d}, "
                          f"frac={frac[k]:.3f}")

    print_sector_summary("All strong Δ events", total_all)
    print_sector_summary("CP-tagged strong Δ", total_cp)
    print_sector_summary("non-CP strong Δ", total_ncp)

    return {
        "total_all": total_all,
        "total_cp": total_cp,
        "total_ncp": total_ncp,
        "all_strong_counts": all_strong_counts,
    }

# ============================================================
# SECTION 7: Long-time stability test (Test 4)
# ============================================================
def run_long_time_stability_test(params: ModelParams,
                                 n_steps: int = 2000,
                                 dt: float = 0.05,
                                 seed: int = 999,
                                 frac_of_max: float = 0.5):
    """
    Long-time stability test for the toy engine.

    - Run a single long trajectory with random normalized Omega0.
    - Check:
        * chirality sign over early vs late windows
        * Δ(κ,Z) clustering structure at early vs late
        * corridor histograms of strong Δ events at early vs late

    Prints a compact diagnostic summary.
    """
    rng = np.random.default_rng(seed)
    Omega0 = rng.standard_normal(3) + 1j * rng.standard_normal(3)
    Omega0 /= np.linalg.norm(Omega0) + 1e-12

    state0 = ModelState(Omega0)
    model = TriOctaPhaseLockModel(params)
    hist = model.run(state0, n_steps=n_steps, dt=dt)

    # Observables
    obs = sample_physics_observables(hist)
    t = np.asarray(hist["t"])
    J = np.asarray(obs["J_eff"])

    # Define early / late windows (e.g. first 25% vs last 25%)
    n = len(t)
    if n < 20:
        print("[WARN] Not enough steps for long-time test.")
        return None

    i_q1 = n // 4
    i_q3 = 3 * n // 4

    J_early = J[i_q1 // 2 : i_q1]       # a chunk in early-mid region
    J_late  = J[i_q3 : n]               # last quarter

    sign_early = np.sign(np.mean(J_early))
    sign_late  = np.sign(np.mean(J_late))

    print("\n===== Long-time stability test =====")
    print(f"Total steps = {n_steps}, dt = {dt}")
    print(f"Mean J_eff early window  ≈ {np.mean(J_early):.4e}, sign = {int(sign_early)}")
    print(f"Mean J_eff late window   ≈ {np.mean(J_late):.4e}, sign = {int(sign_late)}")

    # Δ(κ,Z) cluster structure over full run
    big_mask_full, mags_full = cluster_delta_kz(hist, frac_of_max=frac_of_max)

    # Restrict history to early and late segments for local Δ analysis
    # We slice κ, Z, phi_index, uxy_coords, etc. consistently.
    # Build two sub-histories:
    def slice_history(hist, start_idx, end_idx):
        h_sub = {}
        for key, val in hist.items():
            arr = np.asarray(val)
            # If it's per-step, slice [start_idx:end_idx]
            if arr.shape[0] == n:
                h_sub[key] = arr[start_idx:end_idx]
            else:
                # Otherwise keep as-is (e.g. constants), or trim if off by 1 is needed upstream
                h_sub[key] = arr
        return h_sub

    early_hist = slice_history(hist, 0, i_q1)
    late_hist  = slice_history(hist, i_q3, n)

    print("\n-- Early-segment Δ(κ,Z) structure --")
    early_big, early_mags = cluster_delta_kz(early_hist, frac_of_max=frac_of_max)

    print("\n-- Late-segment Δ(κ,Z) structure --")
    late_big, late_mags = cluster_delta_kz(late_hist, frac_of_max=frac_of_max)

    # Corridor histograms for strong Δ in early vs late
    print("\n-- Early-segment corridor histogram --")
    early_all, early_cp, early_ncp = strong_delta_sector_histogram(early_hist, early_big)
    print(f"  total strong early = {early_all.sum()}, support sectors = {np.count_nonzero(early_all)}")

    print("\n-- Late-segment corridor histogram --")
    late_all, late_cp, late_ncp = strong_delta_sector_histogram(late_hist, late_big)
    print(f"  total strong late = {late_all.sum()}, support sectors = {np.count_nonzero(late_all)}")

    return {
        "J_early_mean": float(np.mean(J_early)),
        "J_late_mean": float(np.mean(J_late)),
        "sign_early": int(sign_early),
        "sign_late": int(sign_late),
        "early_all": early_all,
        "late_all": late_all,
        "early_cp": early_cp,
        "late_cp": late_cp,
        "early_ncp": early_ncp,
        "late_ncp": late_ncp,
    }

# ============================================================
# SECTION 8: Noise robustness test (final test)
# ============================================================
def run_noise_robustness_test(params,
                              n_steps: int = 200,
                              dt: float = 0.05,
                              noise_sigma_k: float = 0.01,
                              noise_sigma_z: float = 0.01,
                              noise_sigma_J: float = 0.01,
                              frac_of_max: float = 0.5,
                              seed: int = 1234):
    """
    Noise robustness test (measurement noise, not dynamical noise).

    Steps:
      1. Run a clean trajectory with given params.
      2. Compute baseline strong-Δ(κ,Z) mask via cluster_delta_kz.
      3. Add Gaussian noise to the recorded κ(t), Z(t), and J_eff(t).
      4. Recompute clustering on the noisy κ,Z.
      5. Compare:
         - # strong steps (baseline vs noisy)
         - fraction of time steps where strong-mask agrees
         - correlation between baseline and noisy Δ magnitudes.

    Returns a small dict of summary stats.
    """
    from model_core import ModelState, TriOctaPhaseLockModel

    rng = np.random.default_rng(seed)

    # --- 1. Run clean trajectory ---
    Omega0 = rng.standard_normal(3) + 1j * rng.standard_normal(3)
    Omega0 /= np.linalg.norm(Omega0) + 1e-12

    state0 = ModelState(Omega0)
    model = TriOctaPhaseLockModel(params)
    hist = model.run(state0, n_steps=n_steps, dt=dt)

    obs = sample_physics_observables(hist)

    # --- 2. Baseline clustering ---
    base_big_mask, base_mags = cluster_delta_kz(hist, frac_of_max=frac_of_max)
    base_n_strong = int(base_big_mask.sum())

    # --- 3. Add noise to κ,Z,J_eff (measurement-level) ---
    kappa = np.asarray(hist["kappa"])
    z     = np.asarray(hist["z"])
    J     = np.asarray(obs["J_eff"])

    noisy_hist = dict(hist)
    noisy_hist["kappa"] = kappa + noise_sigma_k * rng.standard_normal(kappa.shape)
    noisy_hist["z"]     = z     + noise_sigma_z * rng.standard_normal(z.shape)

    noisy_obs = dict(obs)
    noisy_obs["J_eff"] = J + noise_sigma_J * rng.standard_normal(J.shape)

    # --- 4. Clustering on noisy κ,Z ---
    noisy_big_mask, noisy_mags = cluster_delta_kz(noisy_hist, frac_of_max=frac_of_max)
    noisy_n_strong = int(noisy_big_mask.sum())

    # --- 5. Compare masks and magnitudes ---
    L = min(len(base_big_mask), len(noisy_big_mask))
    base_mask = base_big_mask[:L]
    noisy_mask = noisy_big_mask[:L]

    agree_mask = (base_mask == noisy_mask)
    frac_agree = agree_mask.mean()

    # Pearson-style correlation for Δ magnitudes (over matched slice)
    base_m = np.asarray(base_mags[:L])
    noisy_m = np.asarray(noisy_mags[:L])
    if base_m.std() > 0 and noisy_m.std() > 0:
        corr = np.corrcoef(base_m, noisy_m)[0, 1]
    else:
        corr = np.nan

    print("\n===== Noise robustness test (measurement noise) =====")
    print(f"Parameters: eps={params.eps}, g={params.g}, k_vals={params.k_vals}")
    print(f"Noise levels: σ_k={noise_sigma_k}, σ_Z={noise_sigma_z}, σ_J={noise_sigma_J}")
    print(f"Baseline strong steps : {base_n_strong} / {L}")
    print(f"Noisy strong steps    : {noisy_n_strong} / {L}")
    print(f"Mask agreement        : {100.0 * frac_agree:.1f}% of steps")
    print(f"Δ-magnitude correlation (clean vs noisy): {corr:.3f}")

    return {
        "base_n_strong": base_n_strong,
        "noisy_n_strong": noisy_n_strong,
        "frac_agree": float(frac_agree),
        "corr_mags": float(corr),
    }

# ============================================================
# SECTION X: RSB (spectral) diagnostics
# ============================================================
# NOTE: canonical implementations live in definitions.py
