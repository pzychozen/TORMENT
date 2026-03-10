import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.vq import kmeans2

from .cp_windows import cp_mask_from_phi_indices, default_cp_config

# --------------------------------------------------------
# 1. Corridor detection in torus tangent plane
# --------------------------------------------------------

def detect_tangent_corridors(history, R=2.0):
    """
    Take torus mapping (R + r cos chi)(cos phi, sin phi) as XY,
    compute its tangent direction, then find Δ jumps that move ALONG that tangent.

    Engine: history["uxy_coords"] lives in R^3 (x,y,z).
    Analysis: tangent_corridor operates in the torus XY plane,
    so we project the jumps to XY before taking the dot product.
    """
    phi_index = np.asarray(history["phi_index"])
    kappa = np.asarray(history["kappa"])

    # Compute φ angle
    phi = 2 * np.pi * phi_index / 12.0
    # minor radius scaled by κ
    rho = kappa / (1.0 + kappa)
    r = rho  # tube thickness normalized to 1

    # XY coords on torus (tangent-plane world)
    X = (R + r * np.cos(phi)) * np.cos(phi)
    Y = (R + r * np.cos(phi)) * np.sin(phi)
    path_xy = np.column_stack([X, Y])

    # Tangent vectors in XY plane via finite differences
    diffs = np.diff(path_xy, axis=0)
    tangents = diffs / (np.linalg.norm(diffs, axis=1, keepdims=True) + 1e-12)

    # Full 3D SRG trajectory from the engine
    uxy = np.asarray(history["uxy_coords"])      # shape (N, 3)
    jump_vecs = np.diff(uxy, axis=0)            # shape (N-1, 3)

    # Project jumps into same 2D plane as tangents
    jump_vecs_xy = jump_vecs[:, :2]             # keep (x, y), drop z for tangent-plane test
    jump_dirs = jump_vecs_xy / (
        np.linalg.norm(jump_vecs_xy, axis=1, keepdims=True) + 1e-12
    )

    # Dot product between jump direction (XY) and tangent (XY)
    dot = np.sum(jump_dirs * tangents, axis=1)

    # Steps where the trajectory moves along the tangent corridor
    tangent_corridor_mask = np.abs(dot) > 0.8  # strong motion along tangent

    print(
        f"Tangent corridor steps detected: {int(tangent_corridor_mask.sum())} / {len(dot)} "
        f"({tangent_corridor_mask.sum()/len(dot):.2%})"
    )

    # Plot tangent alignment over time
    t = np.asarray(history["t"])
    t_mid = 0.5 * (t[1:] + t[:-1])

    plt.figure()
    plt.plot(t_mid, dot)
    plt.scatter(t_mid[tangent_corridor_mask], dot[tangent_corridor_mask], marker="x", s=40)
    plt.xlabel("time")
    plt.ylabel("⟨jump, tangent⟩")
    plt.title("Torus tangent alignment of SRG jumps")
    plt.grid(True)
    plt.show()

    # Return:
    #   - mask (bool, length N-1)
    #   - XY path (aligned with jumps)
    #   - full 3D jump vectors (engine space, untouched)
    #   - dot alignment scalar
    return tangent_corridor_mask, path_xy[1:], jump_vecs, dot


# --------------------------------------------------------
# 2. Δ(κ, Z) clustering diagnostics
# --------------------------------------------------------

def cluster_delta_kz(history, frac_of_max=0.5, n_clusters=3):
    """
    Real clustering of Δ(κ, Z) using k-means (via kmeans2).

    - Uses history["kappa"], history["z"], history["t"] from the engine.
    - Builds Δκ, ΔZ vectors and clusters them into n_clusters modes.
    - Picks the dominant cluster (largest mean |Δ|).
    - Inside that cluster, selects strongest events using frac_of_max.
    - Returns:
        big_steps_mask : bool array over Δ steps (length L)
        mags           : array of |Δ(κ, Z)| for each step
    """

    # ----- Extract core time series from history -----
    kappa = np.asarray(history["kappa"])
    z = np.asarray(history["z"])
    t = np.asarray(history["t"])

    # Finite differences
    dk = np.diff(kappa)
    dz = np.diff(z)

    # Align lengths safely with time (t has length ~ N, diffs have N-1)
    L = min(len(dk), len(dz), len(t) - 1)
    dk = dk[:L]
    dz = dz[:L]

    # Midpoint time stamps for Δ events
    t_mid = 0.5 * (t[:L] + t[1:L+1])

    # Δ vectors in (κ, Z) plane: REAL data
    delta_vecs = np.column_stack([dk, dz])  # shape (L, 2)

    # ----- k-means clustering on Δ(κ,Z) -----
    # kmeans2 returns (centroids, labels)
    centroids, labels = kmeans2(delta_vecs, n_clusters, minit="points")

    # Magnitude of each Δ vector
    mags = np.linalg.norm(delta_vecs, axis=1)

    print("\n=== Δ(κ, Z) k-means cluster diagnostics ===")
    cluster_means = []
    for c in range(n_clusters):
        mask_c = (labels == c)
        if not np.any(mask_c):
            print(f"Cluster {c}: empty")
            cluster_means.append(-np.inf)
            continue

        m_mean = mags[mask_c].mean()
        m_std  = mags[mask_c].std()
        m_min  = mags[mask_c].min()
        m_max  = mags[mask_c].max()
        cluster_means.append(m_mean)

        print(
            f"Cluster {c}: steps={mask_c.sum():4d}, "
            f"mean|Δ|={m_mean:.4e}, std={m_std:.4e}, "
            f"min={m_min:.4e}, max={m_max:.4e}"
        )

    # ----- Pick dominant cluster (largest mean magnitude) -----
    dominant_cluster = int(np.argmax(cluster_means))
    mask_dom = (labels == dominant_cluster)

    # Within that cluster, apply relative threshold to pick
    # the strongest chirality/transition events.
    if np.any(mask_dom):
        local_max = mags[mask_dom].max()
        thr = frac_of_max * local_max
        big_steps_mask = mask_dom & (mags >= thr)
    else:
        thr = 0.0
        big_steps_mask = np.zeros_like(mags, dtype=bool)

    print(
        f"\nDominant cluster: {dominant_cluster}, "
        f"threshold within cluster = {frac_of_max:.2f} × local max = {thr:.4e}"
    )
    print(
        f"Strong Δ(κ, Z) steps (dominant cluster + threshold): "
        f"{big_steps_mask.sum()} / {len(big_steps_mask)} "
        f"({big_steps_mask.sum()/len(big_steps_mask):.1%})"
    )

    # ----- Chirality / transition timescale (real window) -----
    if np.any(big_steps_mask):
        t_sel = t_mid[big_steps_mask]
        t_start = t_sel.min()
        t_end   = t_sel.max()
        print(
            f"\nChirality/transition selection window: "
            f"t ≈ {t_start:.3f} → {t_end:.3f} "
            f"(Δt ≈ {t_end - t_start:.3f})"
        )
    else:
        t_start, t_end = None, None
        print("\nNo strong Δ(κ, Z) steps detected under current settings.")

    # ----- Plots for intuition / paper -----
    # 1) Δκ vs ΔZ scatter colored by cluster
    plt.figure()
    plt.scatter(dk, dz, c=labels)
    plt.xlabel(r"$\Delta \kappa$")
    plt.ylabel(r"$\Delta Z$")
    plt.title(r"$k$-means clusters in $\Delta(\kappa, Z)$ space")
    plt.grid(True)

    # 2) Strong events (dominant cluster + threshold) in (κ, Z) plane
    plt.figure()
    plt.scatter(kappa[:L][~big_steps_mask], z[:L][~big_steps_mask], s=8)
    plt.scatter(kappa[:L][big_steps_mask],  z[:L][big_steps_mask], marker="x", s=40)
    plt.xlabel(r"$\kappa$")
    plt.ylabel(r"$Z$")
    plt.title("Strong Δ(κ, Z) events in (κ, Z) plane")
    plt.grid(True)

    plt.show()

    return big_steps_mask, mags

# --------------------------------------------------------
# 3. CP vs non-CP inside strong Δ(κ, Z) events
# --------------------------------------------------------

def cp_split_big_delta_events(history, big_steps_mask, mags, cp_cfg=None):
    """
    Take the already-selected strong Δ(κ, Z) events (big_steps_mask)
    and split them into CP / non-CP using the same CP window logic
    as the rest of the code.

    This is exactly Test 3 from our list:
      - CP vs non-CP inside Δ-clusters
      - Check if CP mostly changes variance/cleanness, not the attractor itself.
    """
    # History arrays
    phi_idx = np.asarray(history["phi_index"])

    # Build CP mask per *time step* using the same config as elsewhere
    if cp_cfg is None:
        cp_cfg = default_cp_config()
    cp_mask_time = cp_mask_from_phi_indices(phi_idx, cp_cfg)  # shape (N,)

    # Δ(κ,Z) steps live between time steps.
    # big_steps_mask has length L = number of Δ steps.
    # We'll classify each Δ step by the CP state of its *arrival* time index.
    L = len(big_steps_mask)
    if L + 1 > len(cp_mask_time):
        # Safety guard: trim if someone changes history lengths
        L = len(cp_mask_time) - 1
        big_steps_mask = big_steps_mask[:L]
        mags = mags[:L]

    cp_step_mask = cp_mask_time[1:L+1]   # arrival CP state for each Δ-step

    # Strong events split by CP / non-CP
    strong_cp    = big_steps_mask & cp_step_mask
    strong_ncp   = big_steps_mask & (~cp_step_mask)

    n_strong     = int(big_steps_mask.sum())
    n_cp         = int(strong_cp.sum())
    n_ncp        = int(strong_ncp.sum())

    print("\n=== CP vs non-CP decomposition inside strong Δ(κ, Z) events ===")
    print(f"Total strong Δ steps: {n_strong} / {L} ({100.0 * n_strong / L:.1f}%)")
    print(f"  CP-tagged strong steps    : {n_cp} ({0 if n_strong == 0 else 100.0 * n_cp / n_strong:.1f}%)")
    print(f"  non-CP-tagged strong steps: {n_ncp} ({0 if n_strong == 0 else 100.0 * n_ncp / n_strong:.1f}%)")

    if n_cp > 0:
        cp_mean = mags[strong_cp].mean()
        cp_std  = mags[strong_cp].std()
        print(f"\n  CP strong Δ:   mean|Δ|={cp_mean:.4e}, std|Δ|={cp_std:.4e}")
    else:
        print("\n  CP strong Δ:   none")

    if n_ncp > 0:
        ncp_mean = mags[strong_ncp].mean()
        ncp_std  = mags[strong_ncp].std()
        print(f"  non-CP strong Δ: mean|Δ|={ncp_mean:.4e}, std|Δ|={ncp_std:.4e}")
    else:
        print("  non-CP strong Δ: none")

    # Optional: return the masks in case we want to hook into J_eff or (κ,Z) plots later
    return {
        "strong_cp_mask": strong_cp,
        "strong_ncp_mask": strong_ncp,
        "cp_step_mask": cp_step_mask[:L],
        "big_steps_mask": big_steps_mask,
        "mags": mags[:L],
    }
