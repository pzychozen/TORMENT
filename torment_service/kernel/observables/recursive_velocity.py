"""Distinct entropy and geometry velocity metrics for saved histories."""
import numpy as np


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
    Omega_value = hist.get("Omega")
    Omega = None if Omega_value is None else np.asarray(Omega_value)
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
