"""Chirality observables for saved triad histories; deterministic and NumPy-only."""
import numpy as np

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
