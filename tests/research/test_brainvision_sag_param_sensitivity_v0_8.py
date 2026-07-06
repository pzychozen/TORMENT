"""v0.8 tests: SAG parameter-sensitivity harness (offline).

Verify the sweep is offline-only, imports no service/runtime paths, is deterministic, produces finite
output on normal cells, does not crash on constant/low-energy cases, computes flags, and formats a report.
Tests use a SMALL grid for speed. They do NOT assert any temporal-order claim (temporal_claim_allowed stays
False). Offline; no torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_sag_parameter_sensitivity as ps  # noqa: E402

SMALL = dict(n=2, fields=("constant", "white_noise", "tiny_noise"),
             scales=(0.1, 1.0), eps_values=(1e-4, 1e-3), kappas=(0.0, 3.0))


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


def test_sweep_deterministic():
    a = ps.sweep(**SMALL)
    b = ps.sweep(**SMALL)
    assert set(a) == set(b)
    for k in a:
        ga, gb = a[k]["gain_median"], b[k]["gain_median"]
        assert ga == gb or (np.isnan(ga) and np.isnan(gb))


def test_finite_on_normal_cell():
    g = ps.sweep(**SMALL)
    cell = g[("white_noise", 1.0, 1e-3, 3.0)]
    assert np.isfinite(cell["gain_median"]) and np.isfinite(cell["k0_median"])
    assert 0 <= cell["n_amp"] <= cell["n"]


def test_constant_and_low_energy_do_not_crash():
    g = ps.sweep(**SMALL)  # includes constant + tiny_noise (low energy)
    assert ("constant", 1.0, 1e-3, 0.0) in g
    assert np.isfinite(g[("constant", 1.0, 1e-3, 0.0)]["k0_median"])
    assert ("tiny_noise", 0.1, 1e-3, 0.0) in g  # low-energy case present, no crash


def test_flags_and_report_complete():
    g = ps.sweep(**SMALL)
    f = ps.flags(g)
    for key in ("k0_coherent_rate", "unstable_low_energy", "scale_sensitive", "spike_sensitive",
                "temporal_claim_allowed"):
        assert key in f
    assert f["temporal_claim_allowed"] is False
    s = ps.report(g)
    assert "parameter sensitivity" in s and "temporal_claim_allowed" in s and "READING" in s
