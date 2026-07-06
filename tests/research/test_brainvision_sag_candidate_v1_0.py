"""v1.0 tests: normalized-control-gated SAG candidate (offline).

Lock the candidate machinery + gate logic: offline-only, deterministic normalization, near-flat/degenerate
fields report neutral, finite output, report completes, and temporal_claim_allowed is False unless ALL
predeclared gates pass. Includes hardening locks: exact-half majority must NOT pass (strict majority), and
the spike/lowpass probe must be present or the claim is blocked (no vacuous spike-robust pass). These do NOT
assert the synthetic run yields a temporal PASS. Offline; no torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_sag_anatomy as anat  # noqa: E402
import run_sag_candidate_v1_0 as cand  # noqa: E402


def _fake_res(true_g, ctrl_g, scale_med=None):
    data = {}
    for f in ("white_noise", "spike", "lowpass"):
        for c in cand.CONTROLS:
            g = true_g if c == "true" else ctrl_g
            data[(f, c)] = [{"neutral": False, "scale": 1.0, "g_k0": 1.0, "g_kpos": float(g)} for _ in range(3)]
    if scale_med is None:
        scale_med = {0.1: float(true_g), 1.0: float(true_g), 10.0: float(true_g)}
    return {"data": data, "scale_med": scale_med, "fields": ("white_noise", "spike", "lowpass"), "n": 3}


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


def test_normalization_deterministic():
    w = np.random.default_rng(0).standard_normal((64, 9))
    assert np.allclose(cand.normalize(w), cand.normalize(w))
    assert cand.robust_scale(w) == cand.robust_scale(w)


def test_near_flat_returns_neutral():
    flat = anat.generate_field("constant", 0)
    r = cand.candidate_window(flat)
    assert r["neutral"] is True and r["g_kpos"] == 1.0 and r["g_k0"] == 1.0


def test_candidate_output_finite():
    res = cand.run_candidate(fields=("constant", "white_noise", "spike", "lowpass"), n=2)
    a = cand.analyze(res)
    assert np.isfinite(a["k0_coherent_rate"])
    for k in ("true_median", "shuffled_median", "reversed_median", "circular_median"):
        assert np.isfinite(a[k])
    assert a["near_flat_neutral_count"] >= 1  # constant gated


def test_temporal_gate_both_directions():
    assert cand.analyze(_fake_res(10.0, 1.0))["temporal_claim_allowed"] is True
    assert cand.analyze(_fake_res(1.0, 10.0))["temporal_claim_allowed"] is False


def test_gate_blocks_claim_when_scale_sensitive():
    # true beats the control medians, but a scale-sensitive result must still block the temporal claim
    res = _fake_res(10.0, 1.0, scale_med={0.1: 1.0, 1.0: 10.0, 10.0: 100.0})
    a = cand.analyze(res)
    assert a["scale_sensitive"] is True
    assert a["temporal_claim_allowed"] is False
    assert "g4_scale_invariant" in a["reason"]


def test_spike_probe_absence_blocks_claim():
    # a custom field set without spike/lowpass: the spike/lowpass comparison is unavailable, so even
    # though true beats the controls the temporal claim must not pass (probe-vacuity guard).
    data = {}
    for f in ("white_noise", "smooth_ramp"):
        for c in cand.CONTROLS:
            g = 10.0 if c == "true" else 1.0
            data[(f, c)] = [{"neutral": False, "scale": 1.0, "g_k0": 1.0, "g_kpos": float(g)} for _ in range(3)]
    res = {"data": data, "scale_med": {0.1: 10.0, 1.0: 10.0, 10.0: 10.0},
           "fields": ("white_noise", "smooth_ramp"), "n": 3}
    a = cand.analyze(res)
    assert a["gates"]["g5_spike_probe_present"] is False
    assert a["temporal_claim_allowed"] is False
    assert "g5_spike_probe_present" in a["reason"]


def test_exact_half_majority_does_not_pass():
    # exactly half of non-neutral fields have true beating all controls -> "majority" must be strict
    data = {}
    for f, (tg, cg) in {"p": (10.0, 1.0), "q": (1.0, 10.0)}.items():  # p passes, q fails
        for c in cand.CONTROLS:
            g = tg if c == "true" else cg
            data[(f, c)] = [{"neutral": False, "scale": 1.0, "g_k0": 1.0, "g_kpos": float(g)} for _ in range(3)]
    res = {"data": data, "scale_med": {0.1: 1.0, 1.0: 1.0, 10.0: 1.0}, "fields": ("p", "q"), "n": 3}
    a = cand.analyze(res)
    assert a["field_majority_true_beats_controls"] == 0.5
    assert a["gates"]["g2_field_majority_true_beats_controls"] is False


def test_report_completes():
    res = cand.run_candidate(fields=("constant", "white_noise", "spike", "lowpass"), n=2)
    s = cand.report(res)
    assert "candidate v1.0" in s and "temporal_claim_allowed" in s and "none is hidden" in s


def test_synthetic_run_does_not_force_pass():
    # on the synthetic set the shuffled control amplifies more than true, so no temporal claim
    res = cand.run_candidate(n=3)
    a = cand.analyze(res)
    assert a["temporal_claim_allowed"] is False  # honest: candidate must not force a PASS here
