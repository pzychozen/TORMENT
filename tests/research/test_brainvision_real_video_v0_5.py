"""v0.5 tests: BV-ΨTRS-RVD real prerecorded descriptor route.

Uses SYNTHETIC image-like frame stacks (never real media). Locks the machinery: npz loader, deterministic
low-level descriptors, stable shape, RGB+grayscale, offline runner, and outputs confined to the research
folder. Does NOT require ΨTRS to win -- whether the recursive-time channel survives real descriptor
messiness is the research question, and a negative is valid. Offline only; no torment_service.
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


def _synth(T=80, H=16, W=16, rgb=False, seed=0):
    rng = np.random.default_rng(seed)
    g = np.zeros((T, H, W))
    x = np.linspace(0, 1, W)[None, :] * np.ones((H, 1))
    for t in range(T):
        if t < T // 2:
            g[t] = 0.3 + 0.02 * rng.standard_normal((H, W))
        else:
            g[t] = np.roll(x, t % W, axis=1) + 0.02 * rng.standard_normal((H, W))
    if rgb:
        g = np.stack([g, g * 0.9, g * 1.1], axis=-1)
    return g


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


def test_npz_loader_uint8_and_float():
    frames = _synth()
    with tempfile.TemporaryDirectory() as d:
        p8 = os.path.join(d, "u8.npz")
        np.savez(p8, frames=(frames * 255).astype("uint8"))
        loaded = rvd.load_frame_stack_npz(p8)
        assert loaded.shape == frames.shape and loaded.max() <= 1.5   # rescaled to [0,1]
        pf = os.path.join(d, "f.npz")
        np.savez(pf, frames=frames)
        assert rvd.load_frame_stack_npz(pf).shape == frames.shape


def test_descriptors_deterministic_and_shape():
    frames = _synth()
    D1 = rvd.frames_to_low_level_descriptors(frames)
    D2 = rvd.frames_to_low_level_descriptors(frames)
    assert np.array_equal(D1, D2)
    assert D1.shape == (frames.shape[0], rvd.N_RV_DESCRIPTORS)


def test_rgb_and_grayscale_both_work():
    g = rvd.frames_to_low_level_descriptors(_synth(rgb=False))
    c = rvd.frames_to_low_level_descriptors(_synth(rgb=True))
    assert g.shape[1] == rvd.N_RV_DESCRIPTORS
    assert c.shape[1] == rvd.N_RV_DESCRIPTORS   # RGB adds color_drift; shape stable


def test_runner_processes_npz_offline():
    frames = _synth(T=96)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.npz")
        np.savez(p, frames=frames)
        res = rv.run_npz(p, win=32, stride=16)
    assert res["n_windows"] >= 1 and res["descriptor_dim"] == rvd.N_RV_DESCRIPTORS
    assert "sag" in res and np.isfinite(res["sag"]["G_k0"]) and np.isfinite(res["sag"]["G_kpos"])
    if "true_vs_shuffled" in res:
        assert all(np.isfinite(v) for v in res["true_vs_shuffled"].values())


def test_no_media_or_results_required():
    # runs on in-memory frames; needs no files under local_inputs/, writes nothing
    res = rv.run_clip(_synth(), win=32, stride=16)
    assert res["descriptor_dim"] == rvd.N_RV_DESCRIPTORS


def test_output_stays_in_research_folder():
    assert os.path.realpath(rv.LOCAL_INPUTS).startswith(os.path.realpath(rv._MODULE_DIR))
    assert os.path.realpath(rv._DEFAULT_OUT).startswith(os.path.realpath(rv._MODULE_DIR))
