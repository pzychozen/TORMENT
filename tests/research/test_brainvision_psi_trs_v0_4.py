"""v0.4 tests: BV-ΨTRS (state-dependent internal time + spectral recursion).

Verify the ΨTRS math invariants and, crucially, the recursive-time claim: the state-dependent internal
clock (kappa>0) adds signal that its own kappa=0 ablation (fixed external clock) does not. Offline only;
no torment_service. A negative result is a valid closure; these tests lock the machinery + the ablation.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import descriptors  # noqa: E402
import fixtures  # noqa: E402
import psi_trs  # noqa: E402
import run_falsifier  # noqa: E402


def test_no_forbidden_imports():
    for fn in os.listdir(BV_DIR):
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(BV_DIR, fn), encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=fn)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("torment"), f"{fn}: import {alias.name}"
                    assert "rsb_model" not in alias.name, f"{fn}: import {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("torment"), f"{fn}: from {mod}"
                assert "rsb_model" not in mod, f"{fn}: from {mod}"
                for alias in node.names:
                    assert alias.name != "RSBModel", f"{fn}: imports RSBModel"


def test_psi_spec_amplitude_scale_invariant():
    D = descriptors.prepare(fixtures.generate_sm("sm_short_return", 0))
    base = psi_trs.psi_spec(D)
    for c in (0.01, 37.5, 1000.0):
        assert abs(psi_trs.psi_spec(c * D) - base) < 1e-8, c


def test_spectral_renorm_bounds_energy():
    D = descriptors.prepare(fixtures.generate_sm("sm_reset", 1))
    e_small = float((psi_trs.spectral_renormalize(D) ** 2).sum())
    e_large = float((psi_trs.spectral_renormalize(1000.0 * D) ** 2).sum())
    assert abs(e_small - e_large) < 1e-6                      # energy scale-invariant (bounded)
    assert e_large < (np.exp(0.7) ** 2) * D.size + 1.0        # bounded by tau^2 * n_modes


def test_kappa0_equals_fixed_clock():
    D = descriptors.prepare(fixtures.generate_sm("sm_long_return", 2))
    rho = psi_trs._local_rho(D)
    phi0, _ = psi_trs.internal_clock(rho, omega=1.0, kappa=0.0, dt=1.0)
    assert np.allclose(phi0, np.arange(len(rho)) * 1.0)              # fixed external clock
    assert np.allclose(psi_trs.warp_by_internal_clock(D, phi0), D)   # warp is identity


def test_kappa_positive_is_state_dependent():
    T = fixtures.T
    rho_a = np.linspace(0.0, 1.0, T)
    rho_b = np.linspace(1.0, 0.0, T)
    # kappa=0: clock independent of state
    assert np.allclose(psi_trs.internal_clock(rho_a, kappa=0.0)[0], psi_trs.internal_clock(rho_b, kappa=0.0)[0])
    # kappa>0: clock diverges based on state
    phi_a = psi_trs.internal_clock(rho_a, kappa=0.5)[0]
    phi_b = psi_trs.internal_clock(rho_b, kappa=0.5)[0]
    assert not np.allclose(phi_a, phi_b)
    assert not np.allclose(phi_a, np.arange(T) * 1.0)


def test_recursive_time_channel_adds_signal():
    r = run_falsifier.run(seeds=range(8), mode="psi_time_recursive")
    # the state-dependent internal clock (kappa>0) beats its own kappa=0 ablation...
    assert r["psi_trs"] > r["psi_trs_k0"] + 0.1, (r["psi_trs"], r["psi_trs_k0"])
    # ...and is a real temporal signal that collapses under time-shuffle...
    assert r["psi_trs"] > r["psi_trs_time_shuffled"] + 0.1, (r["psi_trs"], r["psi_trs_time_shuffled"])
    # ...and above chance.
    assert r["psi_trs"] > r["chance"] + 0.1, (r["psi_trs"], r["chance"])
