# phase_triad_sync.py
from __future__ import annotations
import numpy as np

def apply_phase_triad_sync(Omega_next: np.ndarray, lambda_phase: float) -> np.ndarray:
    """
    Phase-only triadic synchronization operator.

    Implements:
      phi_k <- phi_k + lambda * sum_{j!=k} sin(3*(phi_j - phi_k))
    while preserving amplitudes |Omega_k|.
    """
    if lambda_phase == 0.0:
        return Omega_next

    # Ensure shape (3,)
    Omega_next = np.asarray(Omega_next, dtype=np.complex128).reshape(3)

    r = np.abs(Omega_next)
    phi = np.angle(Omega_next)

    # Pairwise differences phi_j - phi_k
    d = phi[None, :] - phi[:, None]  # rows=k, cols=j => d[k,j] = phi_j - phi_k
    # Exclude diagonal automatically since sin(0)=0
    delta_phi = lambda_phase * np.sum(np.sin(3.0 * d), axis=1)

    phi_new = phi + delta_phi
    return r * np.exp(1j * phi_new)

def triad_coherence(Omega: np.ndarray) -> tuple[float, float, complex]:
    """
    Triadic coherence:
      S = (1/3) * sum_k exp(i*3*phi_k)
      S_mag = |S|
      Phi_coll = arg(S)
    """
    Omega = np.asarray(Omega, dtype=np.complex128).reshape(3)
    phi = np.angle(Omega)
    S = np.mean(np.exp(1j * 3.0 * phi))
    return float(np.abs(S)), float(np.angle(S)), S
