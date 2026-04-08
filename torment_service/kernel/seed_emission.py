# seed_emission.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from typing import Dict, Any, Tuple

def wrap_pi(a: np.ndarray) -> np.ndarray:
    return (a + np.pi) % (2*np.pi) - np.pi

def triad_coherence_from_omega(Omega: np.ndarray) -> Tuple[float, float, complex]:
    Omega = np.asarray(Omega, dtype=np.complex128).reshape(3)
    phi = np.angle(Omega)
    S = np.mean(np.exp(1j * 3.0 * phi))
    return float(np.abs(S)), float(np.angle(S)), S

@dataclass
class GapGate:
    """
    Defines an angular gap window (center +/- width).
    We compute a per-channel angle theta_k and check if it's inside the window.
    """
    n_sectors: int = 24
    gap_center_deg: float = 0.0
    gap_width_deg: float = 5.0
    require_coherence: bool = False
    coherence_min: float = 0.65  # |S| threshold if require_coherence=True
    mode: str = "partial"        # "partial" or "coherent"

    def _gap_center_rad(self) -> float:
        return np.deg2rad(self.gap_center_deg)

    def _gap_width_rad(self) -> float:
        return np.deg2rad(self.gap_width_deg)

def channel_angles(Omega: np.ndarray, phi_index: int, n_sectors: int) -> np.ndarray:
    """
    Build per-channel angular coordinates theta_k for gating.

    Minimal, robust definition:
      theta_scaffold = 2π * phi_index / n_sectors
      theta_k = theta_scaffold + angle(Omega_k)

    This makes the gap predicate depend on BOTH scaffold location and channel phase.
    """
    Omega = np.asarray(Omega, dtype=np.complex128).reshape(3)
    theta_scaffold = 2*np.pi * (phi_index % n_sectors) / float(n_sectors)
    phi = np.angle(Omega)
    return wrap_pi(theta_scaffold + phi)

def in_gap(theta: np.ndarray, center: float, halfwidth: float) -> np.ndarray:
    return np.abs(wrap_pi(theta - center)) <= halfwidth

def check_emission(state, gate: GapGate) -> Dict[str, Any]:
    """
    Returns an emission decision structure:
      {
        "emit": bool,
        "channels": [k,...]   # which channels emitted
        "theta": np.ndarray(3),
        "S_mag": float,
        "Phi_coll": float,
      }
    """
    Omega = state.Omega
    phi_index = int(state.phi_index)

    theta = channel_angles(Omega, phi_index, gate.n_sectors)
    mask = in_gap(theta, gate._gap_center_rad(), gate._gap_width_rad())

    S_mag, Phi_coll, _ = triad_coherence_from_omega(Omega)

    if gate.require_coherence and (S_mag < gate.coherence_min):
        return {"emit": False, "channels": [], "theta": theta, "S_mag": S_mag, "Phi_coll": Phi_coll}

    if gate.mode == "coherent":
        emit = bool(np.all(mask))
        channels = [0, 1, 2] if emit else []
    else:
        # partial mode: any channel may emit
        channels = [int(k) for k in np.where(mask)[0].tolist()]
        emit = len(channels) > 0

    return {"emit": emit, "channels": channels, "theta": theta, "S_mag": S_mag, "Phi_coll": Phi_coll}

def make_payload(state, channel: int, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    Omega = np.asarray(state.Omega, dtype=np.complex128).reshape(3)
    phi = np.angle(Omega)
    r = np.abs(Omega)

    step_val = int(getattr(state, "step_i", getattr(state, "step", 0)))

    payload = {
        "phi_index": int(state.phi_index),
        "phi": phi.copy(),
        "r": r.copy(),
        "channel": int(channel),
        "Omega_channel": Omega[int(channel)],
        "step": step_val,
    }
    if extra:
        payload.update(extra)
    return payload

