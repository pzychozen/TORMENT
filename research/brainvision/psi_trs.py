"""BV-ΨTRS: Brainvision Psi-Time Recursive Spectral Operator (offline, re-derived, no service imports).

Implements the TORMENT spectral-recursion + recursive-time math on a 2D descriptor-time field:

  * psi_spec(theta): dimensionless Ψ-spectral spread = energy-weighted mean spectral radius (amplitude
    -scale invariant), per spectral_recursion.pdf §1.2.
  * bounded_warp(rho): smooth bounded warp W(rho) = tanh(alpha*(rho - x0)). (The Continuous_time /
    Time_induced_symmetry papers use an UNBOUNDED tan; we use a bounded tanh so the offline harness stays
    numerically safe, matching the spectral paper's sigma_L(u)=tanh(u/L).)
  * internal_clock: state-dependent time  phi[t+1] = phi[t] + omega*dt + kappa*W(rho[t]).
  * warp_by_internal_clock: resample descriptor field onto a uniform internal-time grid.
  * spectral_renormalize / geometry_operator / spectral_recursion: bounded self-referential spectral
    update whose operator depends on the field's own Ψspec (spectral_recursion.pdf §1.3-1.5).
  * psi_trs_features: features from the recursive-clock-warped descriptor field.

The recursive-time channel exists only for kappa>0 (state-dependent temporality). kappa=0 collapses the
internal clock to a fixed external clock (warp = identity): the built-in ablation.

stdlib + numpy only.
"""
from __future__ import annotations

import numpy as np

_EPS = 1e-8


def _spectral_radius(nr, nc, a=1.0, b=1.0):
    kr = np.fft.fftfreq(nr) * nr
    kc = np.fft.fftfreq(nc) * nc
    KR, KC = np.meshgrid(kr, kc, indexing="ij")
    return np.sqrt((KR / a) ** 2 + (KC / b) ** 2)


def psi_spec(theta, a=1.0, b=1.0, eps=_EPS):
    """Dimensionless Ψ-spectral spread: energy-weighted mean spectral radius. Amplitude-scale invariant."""
    th = np.asarray(theta, float)
    if th.ndim == 1:
        th = th[:, None]
    P = np.abs(np.fft.fft2(th)) ** 2
    rho = _spectral_radius(*th.shape, a=a, b=b)
    return float((rho * P).sum() / (eps + P.sum()))


spectral_spread = psi_spec  # alias


def bounded_warp(rho, alpha=1.0, x0=0.0):
    """Smooth bounded warp W(rho) = tanh(alpha*(rho - x0)) in (-1, 1)."""
    return np.tanh(alpha * (np.asarray(rho, float) - x0))


def internal_clock(rho_series, omega=1.0, kappa=0.0, dt=1.0, alpha=1.0, x0=None, epsilon=0.0):
    """State-dependent internal clock. Returns (phi, alpha_bv).

    phi[0] = 0 ;  phi[t] = phi[t-1] + omega*dt + kappa*W(rho[t-1]).
    kappa=0 -> phi[t] = omega*dt*t (fixed external clock).
    """
    rho = np.asarray(rho_series, float)
    if x0 is None:
        x0 = float(np.median(rho))
    W = bounded_warp(rho, alpha, x0)
    dphi = omega * dt + kappa * W
    phi = np.concatenate([[0.0], np.cumsum(dphi[:-1])])
    alpha_bv = 1.0 + epsilon * W
    return phi, alpha_bv


def warp_by_internal_clock(D, phi):
    """Resample descriptor field D (T,C) onto a uniform internal-time grid defined by phi. kappa=0 -> id."""
    D = np.asarray(D, float)
    T, C = D.shape
    phi = np.asarray(phi, float)
    grid = np.linspace(phi[0], phi[-1], T)
    out = np.empty((T, C))
    for c in range(C):
        out[:, c] = np.interp(grid, phi, D[:, c])
    return out


def spectral_renormalize(theta, L=0.7, eps=_EPS):
    """Ĉ_Ψ: scale all Fourier amplitudes to bounded global energy, preserving relative shell structure."""
    F = np.fft.fft2(np.asarray(theta, float))
    F2 = np.mean(np.abs(F) ** 2)
    F = F * np.exp(L) / np.sqrt(eps ** 2 + F2)
    return np.real(np.fft.ifft2(F))


def geometry_operator(theta, a=1.0, b=1.0, beta=1.0, L=1.0):
    """Ĝ_Ψ: state-dependent geometry, attenuation g(rho,Ψ)=rho^2*(1+beta*tanh(Ψ/L))."""
    th = np.asarray(theta, float)
    F = np.fft.fft2(th)
    rho = _spectral_radius(*th.shape, a=a, b=b)
    g = rho ** 2 * (1.0 + beta * np.tanh(psi_spec(th, a, b) / L))
    return np.real(np.fft.ifft2(-g * F))


def spectral_recursion(theta, steps=3, dt=0.03, beta=1.0, L=0.7, kappa_inj=0.1, eps=_EPS):
    """Self-referential bounded spectral update; returns (final_field, Ψspec trajectory)."""
    th = np.asarray(theta, float).copy()
    traj = []
    for _ in range(steps):
        Dmap = psi_spec(th) * th
        upd = th + dt * geometry_operator(th, beta=beta, L=L) + kappa_inj * np.tanh(Dmap)
        th = spectral_renormalize(upd, L=L, eps=eps)
        traj.append(psi_spec(th))
    return th, np.array(traj)


def _local_rho(D, window=8):
    T = D.shape[0]
    return np.array([psi_spec(D[max(0, t - window + 1):t + 1, :]) for t in range(T)])


def psi_trs_features(D, kappa=0.5, omega=1.0, dt=1.0, window=8, alpha=1.0, epsilon=0.3):
    """Features from the recursive-clock-warped descriptor field. The clock-desync block is identically
    zero when kappa=0 (no recursive-time channel)."""
    D = np.asarray(D, float)
    T, C = D.shape
    rho = _local_rho(D, window)
    x0 = float(np.median(rho))
    phi, _alpha_bv = internal_clock(rho, omega, kappa, dt, alpha, x0, epsilon)
    Dw = warp_by_internal_clock(D, phi)
    _th, psi_traj = spectral_recursion(Dw)
    desync = kappa * bounded_warp(rho, alpha, x0)  # clock divergence channel (== 0 iff kappa==0)
    feats = [rho.mean(), rho.std(), rho.max() - rho.min(),
             desync.mean(), desync.std(), np.abs(desync).max(),
             psi_traj.mean(), psi_traj.std(), float(psi_traj[-1])]
    for c in range(C):
        Fc = np.abs(np.fft.rfft(Dw[:, c] - Dw[:, c].mean()))
        feats += [Fc.mean(), Fc.std()]
    return np.array(feats, float)
