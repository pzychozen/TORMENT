"""v0.4 tests: color G5 roughness/spectrum diagnostic (offline).

Lock the MACHINERY and the v0.4 discipline: offline-only, no service/runtime imports; phase-randomization
preserves each channel's amplitude spectrum (hence std) and DC; the spectrum-matched null holds Y' to the
intended fixture's Y' series and independently phase-randomizes RG/BY; the roughness-matched pair is matched in
delta_rms; G5a (cross-channel roughness immunity) passes; G5b (within-chroma spectrum immunity) FAILS as
predeclared because per-channel-std RG/BY ratios are ~1 (RG/BY/CHROMA reported separately, never behind a max);
full G5 = G5a AND G5b so the verdict is HOLD; and NO temporal-order / vision / "Brainvision sees" claim is made.
Offline; no torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_g5_diagnostic_v0_4 as g5  # noqa: E402
import run_color_descriptor_bridge_v0_3 as cb  # noqa: E402


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


def test_phase_randomize_preserves_spectrum_and_dc():
    rng = np.random.default_rng(0)
    x = np.sin(np.linspace(0, 6, 32)) + 0.3 * rng.standard_normal(32)
    y = g5.phase_randomize_1d(x, np.random.default_rng(1))
    assert abs(np.std(y) - np.std(x)) < 1e-9              # variance/std preserved exactly
    assert abs(np.mean(y) - np.mean(x)) < 1e-9            # DC preserved
    assert np.allclose(np.sort(np.abs(np.fft.rfft(y))), np.sort(np.abs(np.fft.rfft(x))))  # amplitude spectrum


def test_spectrum_matched_null_holds_yp_and_preserves_rg_std():
    name = "red_green_opponent_change"
    intended = cb.fixture(name)
    null = g5.spectrum_matched_color_null(name, 0)
    sm_i, sm_n = cb._spatial_means(intended), cb._spatial_means(null)
    assert np.allclose(sm_i["Yp"], sm_n["Yp"], atol=1e-9)         # Y' held to intended series
    assert abs(sm_i["RG"].std() - sm_n["RG"].std()) < 1e-9        # RG std preserved -> ratio ~1


def test_rough_luminance_only_null_has_zero_chroma():
    d = cb.descriptor(g5.rough_luminance_only_null(0))
    assert d["CHROMA"]["response"] < 1e-9 and d["RG"]["response"] < 1e-9 and d["BY"]["response"] < 1e-9


def test_roughness_matched_pair_is_delta_rms_matched():
    color, lum = g5.roughness_matched_color_vs_luminance_pair(0)
    rg_drms = g5._delta_rms(cb._spatial_means(color)["RG"])
    yp_drms = g5._delta_rms(cb._spatial_means(lum)["Yp"])
    assert abs(rg_drms - yp_drms) < 1e-9                          # matched roughness across the pair


def test_g5a_passes():
    a = g5.run_g5a()
    assert a["checks"]["a1_rough_lum_no_color"] and a["checks"]["a2_no_cross_fire"] \
        and a["checks"]["a3_roughness_corr"] and a["pair_valid"]
    assert a["G5a"] is True


def test_g5b_reports_channels_separately_and_fails_as_predeclared():
    b = g5.run_g5b()
    for name, d in b["per_fixture"].items():
        assert set(d["ratios"]) == {"RG", "BY", "CHROMA"}         # RG/BY/CHROMA ALWAYS reported (never behind max)
        assert set(d["channel_ok"]) == {"RG", "BY", "CHROMA"}
        assert abs(d["ratios"]["RG"] - 1.0) < 1e-6                # per-channel std preserved -> ratio ~1
        # fixture_ok gates only on the predeclared ACTIVE channels, but still reports all channels
        assert d["fixture_ok"] == all(d["channel_ok"][ch] for ch in g5.G5B_ACTIVE[name])
    assert b["G5b"] is False                                      # predeclared: not achievable with std descriptors


def test_g5b_active_channel_map_covers_all_fixtures():
    assert set(g5.G5B_ACTIVE) == set(g5.G5B_FIXTURES)
    for name, active in g5.G5B_ACTIVE.items():
        assert set(active) <= {"RG", "BY", "CHROMA"} and len(active) >= 1


def test_null_gamut_clip_is_visible_and_blocks_when_set():
    b = g5.run_g5b()
    assert "any_null_gamut_clip" in b
    assert all("null_gamut_clip" in d for d in b["per_fixture"].values())
    res = g5.run_g5()
    assert "any_null_gamut_clip" in res
    assert res["any_null_gamut_clip"] is False                    # nulls stay in gamut for these fixtures


def test_full_verdict_is_hold_no_forced_pass():
    res = g5.run_g5()
    assert res["g5a"]["G5a"] is True and res["g5b"]["G5b"] is False
    assert res["full_G5"] is False
    assert res["verdict"] == "HOLD"                               # G5a-only pass does NOT license validity
    assert res["first_pass_descriptor_control_validity_claim_allowed"] is False
    assert res["temporal_claim_allowed"] is False


def test_no_single_fixture_pass():
    # G5b must require a majority; a single favorable fixture cannot flip it
    b = g5.run_g5b()
    assert b["G5b"] == bool(b["majority"] > 0.5)


def test_report_completes():
    s = g5.format_report()
    assert "G5" in s and "VERDICT=HOLD" in s and "NOT vision" in s and "predeclared" in s.lower()
    assert "any_null_gamut_clip" in s
