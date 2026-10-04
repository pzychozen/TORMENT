"""Spectral observables for saved RSB histories; independent of the RSB engine."""
import numpy as np


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
