"""v0.4.1 tests: BV-ΨTRS-SAG symmetry amplification gain.

Test the recursive-time claim with the TIME papers' own diagnostic: a fixed clock (kappa=0) keeps a
mirror-perturbed pair coherent (symmetry preserved), while a state-dependent clock (kappa>0) can amplify
their separation above threshold (symmetry breaking). Offline only; no torment_service. A negative result
is a valid closure.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import symmetry_gain as sg  # noqa: E402


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


def test_paired_trajectories_deterministic_and_mirrored():
    b = sg.base_field(0)
    p1, m1 = sg.paired_trajectories(b, 1e-2, 0)
    p2, m2 = sg.paired_trajectories(b, 1e-2, 0)
    assert np.array_equal(p1, p2) and np.array_equal(m1, m2)   # deterministic
    assert np.allclose((p1 + m1) / 2.0, b)                     # mirror-symmetric about base


def test_kappa0_coherent_low_gain():
    b = sg.base_field(0)
    assert sg.symmetry_gain(b, 0.0, eps=1e-2, steps=60) < 1.05  # fixed clock preserves symmetry


def test_kappa_positive_amplifies_on_a_setting():
    b = sg.base_field(0)
    g0 = sg.symmetry_gain(b, 0.0, eps=1e-2, steps=60)
    gk = sg.symmetry_gain(b, 3.0, eps=1e-2, steps=60)
    assert gk > g0 + 0.5, (g0, gk)   # state-dependent clock amplifies above threshold
    assert gk > 1.5


def test_gain_scan_finite_bounded():
    b = sg.base_field(0)
    G = sg.gain_scan(b, [0.0, 1.0, 3.0], [0.5, 1.0, 2.0], eps=1e-2, steps=40)
    assert np.all(np.isfinite(G))
    assert G.max() < 1e6 and G.min() >= 0.0


def test_report_completes_offline():
    s = sg.report()
    assert "Symmetry Amplification Gain" in s and "verdict" in s


def test_runner_report_all_offline():
    import run_falsifier
    res = run_falsifier.report_all(seeds=range(4))
    assert "v0.4_psi_time_recursive" in res
