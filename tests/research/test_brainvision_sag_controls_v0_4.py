"""v0.4 controls tests: offline SAG controls/fragility wrapper.

Verify the controls wrapper is offline-only, imports no service/runtime paths, produces the expected
control fields deterministically, and runs on synthetic image-like stacks. These tests lock the MACHINERY;
they do NOT assert that true windows amplify more than the temporal controls -- whether the amplification
is temporal-order-specific is the research question the wrapper exists to answer. Offline; no torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_real_video_sag_controls as ct  # noqa: E402


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


def test_transform_shapes_and_determinism():
    w = np.random.default_rng(0).standard_normal((64, 9))
    for control in ct.CONTROLS:
        a = ct.transform_window(w, control, np.random.default_rng(3))
        b = ct.transform_window(w, control, np.random.default_rng(3))
        assert a.shape == w.shape
        assert np.array_equal(a, b)                      # deterministic given the rng seed


def test_time_reversed_preserves_marginal():
    w = np.random.default_rng(1).standard_normal((64, 9))
    rev = ct.transform_window(w, "time_reversed", np.random.default_rng(0))
    for c in range(w.shape[1]):
        assert np.allclose(np.sort(w[:, c]), np.sort(rev[:, c]))   # pure temporal op


def test_controls_run_offline_all_fields():
    res = ct.run_controls_for_clip(_synth(), win=64, stride=32)
    for control in ct.CONTROLS:
        assert control in res
        r = res[control]
        assert r["n_windows"] >= 2
        for summ in (r["G_k0"], r["G_kpos"]):
            assert all(np.isfinite(v) for v in summ.values())
        assert 0 <= r["n_amplifying"] <= r["n_windows"]
    comp = res["_comparison"]
    for k in ("true_median", "shuffled_median", "reversed_median",
              "true_amplifying", "shuffled_amplifying", "reversed_amplifying"):
        assert k in comp


def test_report_completes_offline():
    res = ct.run_controls_for_clip(_synth(), win=64, stride=32)
    s = ct.format_report("synthetic", res)
    assert "BV-ΨTRS-RVD-CONTROLS" in s and "verdict" in s
