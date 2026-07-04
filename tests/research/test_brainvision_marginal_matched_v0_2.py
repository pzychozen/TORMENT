"""v0.2 tests: marginal-matched temporal fixtures.

Prove the amplitude shortcut is removed (classes share amplitude marginals, differ only in temporal
order) and that PsiBV's signal is temporal (degrades under time-shuffle). Offline only; no torment_service.

These tests verify the machinery and controls, not that PsiBV beats the temporal baselines. Whether PsiBV
beats plain_fft / frame_diff is the research question the runner reports; a negative result is a valid
closure.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import fixtures  # noqa: E402
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


def test_marginals_matched_across_classes():
    fams = fixtures.MM_CLASS_FAMILIES
    arrs = [fixtures.generate_mm(name, 0) for name in fams]
    ref = arrs[0]
    for other in arrs[1:]:
        for ch in range(fixtures.N_PRIMITIVE):
            # identical value multiset per channel -> matched histogram / mean / variance
            assert np.allclose(np.sort(ref[:, ch]), np.sort(other[:, ch])), ch
            assert abs(ref[:, ch].mean() - other[:, ch].mean()) < 1e-9
            assert abs(ref[:, ch].var() - other[:, ch].var()) < 1e-9


def test_temporal_order_differs():
    a = fixtures.generate_mm("mm_smooth", 0)
    b = fixtures.generate_mm("mm_snap", 0)
    c = fixtures.generate_mm("mm_oscillation", 0)
    assert not np.array_equal(a, b)
    assert not np.array_equal(a, c)
    assert not np.array_equal(b, c)


def test_descriptor_only_no_longer_trivial():
    r = run_falsifier.run(seeds=range(8), mode="marginal_matched")
    # In v0.1 coarse descriptor_only was 1.000; with matched marginals it must fall toward chance.
    assert r["descriptor_only"] < 0.6, r["descriptor_only"]
    assert r["descriptor_only"] <= r["chance"] + 0.15, (r["descriptor_only"], r["chance"])


def test_psi_is_temporal_and_degrades_under_shuffle():
    r = run_falsifier.run(seeds=range(8), mode="marginal_matched")
    psi = r["psi"]
    assert psi > r["chance"] + 0.1, (psi, r["chance"])
    assert psi > r["psi_time_shuffled"] + 0.05, (psi, r["psi_time_shuffled"])
    assert psi > r["descriptor_only"], (psi, r["descriptor_only"])  # beats the neutralized shortcut
