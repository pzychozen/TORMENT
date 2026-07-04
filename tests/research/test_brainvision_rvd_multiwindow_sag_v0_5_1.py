"""v0.5.1 tests: real-video multi-window SAG robustness.

SAG is now evaluated over EVERY descriptor window, not just windows[0]. These tests lock the machinery on
synthetic image-like stacks: multi-window gains are finite, the k=0 baseline stays coherent across
windows, and the summary counts are correct. They do NOT assert amplification (whether k>0 amplifies on
real descriptors is the research question; a negative is valid). Offline only; no torment_service.
"""
import ast
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import real_video as rvd  # noqa: E402
import run_real_video_descriptors as rv  # noqa: E402


def _synth(T=160, H=32, W=32, seed=0):
    rng = np.random.default_rng(seed)
    g = np.zeros((T, H, W))
    x = np.linspace(0, 1, W)[None, :] * np.ones((H, 1))
    for t in range(T):
        if t < T // 3:
            g[t] = 0.3 + 0.05 * rng.standard_normal((H, W))
        elif t < 2 * T // 3:
            g[t] = np.roll(x, t % W, axis=1) + 0.05 * rng.standard_normal((H, W))
        else:
            g[t] = (0.8 if (t // 7) % 2 == 0 else 0.2) + 0.05 * rng.standard_normal((H, W))
    return np.stack([g, g * 0.9, g * 1.1], axis=-1)


def _windows():
    frames = _synth()
    windows, _ = rvd.clip_descriptor_dataset(frames, win=64, stride=32)
    return windows


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


def test_multiwindow_sag_finite():
    windows = _windows()
    sag = rv.evaluate_sag_real(windows)
    assert sag["n_windows"] == len(windows) >= 2
    for p in sag["per_window"]:
        assert np.isfinite(p["G_k0"]) and np.isfinite(p["G_kpos"])
    for summ in (sag["G_k0_summary"], sag["G_kpos_summary"]):
        assert all(np.isfinite(v) for v in summ.values())


def test_kappa0_baseline_coherent_across_windows():
    sag = rv.evaluate_sag_real(_windows())
    assert all(p["G_k0"] < 1.1 for p in sag["per_window"])   # fixed clock preserves coherence everywhere
    assert sag["G_k0_summary"]["max"] < 1.1


def test_summary_counts_windows_correctly():
    windows = _windows()
    sag = rv.evaluate_sag_real(windows, margin=0.2)
    assert sag["n_windows"] == len(sag["per_window"]) == len(windows)
    manual = sum(1 for p in sag["per_window"]
                 if np.isfinite(p["G_kpos"]) and p["G_k0"] < 1.1 and p["G_kpos"] > p["G_k0"] + 0.2)
    assert sag["n_amplifying"] == manual
    assert 0.0 <= sag["frac_amplifying"] <= 1.0
    assert sag["amplifies_most"] == (sag["n_amplifying"] > len(windows) / 2.0)


def test_runner_offline_with_multiwindow_sag():
    frames = _synth()
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.npz")
        np.savez(p, frames=frames)
        res = rv.run_npz(p, win=64, stride=32)
    assert "sag" in res and res["sag"]["n_windows"] >= 2
    assert np.isfinite(res["sag"]["G_k0"]) and np.isfinite(res["sag"]["G_kpos"])
