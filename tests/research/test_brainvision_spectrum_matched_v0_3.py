"""v0.3 tests: spectrum-matched fixtures + PsiBV-RPSR (Return-Phase Spectral Recursion).

Prove the power-spectrum shortcut is removed (identical |FFT| across classes -> plain_fft at chance) and
that RPSR reads phase/return structure the magnitude spectrum cannot, so plain FFT cannot win the contest.
Offline only; no torment_service. These tests verify machinery + controls, not that RPSR is the strongest
method overall (a negative result there is a valid closure).
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
import rpsr  # noqa: E402
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


def test_rpsr_tensor_shape_and_scalars():
    prim = fixtures.generate_sm("sm_short_return", 0)
    rp = rpsr.compute_rpsr(descriptors.prepare(prim))
    assert rp.ndim == 4
    assert rp.shape[0] == fixtures.T
    assert rp.shape[2] == rpsr.M_BANDS
    assert rp.shape[3] == rpsr.R_DIM == 5  # immediate/short/long/inverted/reset
    s = rpsr.derive_scalars(rp)
    for key in ("R_bv", "Phi_bv", "K_bv", "Q_bv", "J_bv"):
        assert key in s and s[key].shape[0] == fixtures.T


def test_power_spectrum_matched_across_classes():
    arrs = [fixtures.generate_sm(n, 0) for n in fixtures.SM_CLASS_FAMILIES]
    ref = arrs[0]
    for other in arrs[1:]:
        for ch in range(fixtures.N_PRIMITIVE):
            assert np.allclose(np.abs(np.fft.rfft(ref[:, ch])), np.abs(np.fft.rfft(other[:, ch])), atol=1e-6)


def test_plain_fft_cannot_win_spectrum_matched():
    r = run_falsifier.run(seeds=range(8), mode="spectrum_matched")
    # identical magnitude spectrum -> plain_fft cannot separate the classes
    assert r["plain_fft"] <= r["chance"] + 0.05, (r["plain_fft"], r["chance"])
    # the intended contest: RPSR beats plain FFT magnitude by reading phase/return structure
    assert r["rpsr"] > r["plain_fft"] + 0.1, (r["rpsr"], r["plain_fft"])


def test_rpsr_is_temporal_and_degrades_under_shuffle():
    r = run_falsifier.run(seeds=range(8), mode="spectrum_matched")
    assert r["rpsr"] > r["chance"] + 0.1, (r["rpsr"], r["chance"])
    assert r["rpsr"] > r["rpsr_time_shuffled"] + 0.05, (r["rpsr"], r["rpsr_time_shuffled"])
