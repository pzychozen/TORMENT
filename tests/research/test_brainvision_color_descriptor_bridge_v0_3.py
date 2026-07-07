"""v0.3 tests: color descriptor bridge (offline).

Lock the MACHINERY and the v0.2 discipline: offline-only, no service/runtime imports, the Y'/RG/BY/CHROMA
transform round-trips, gray has zero chroma, synthetic fixtures do NOT clip gamut, "Y' held" fixtures hold Y'
within tolerance, color/channel controls behave (grayscale collapses color across the RG/BY/CHROMA-bearing
fixtures; luminance cannot fake color), neutral handling works, the faithful roughness/spectrum G5 is NOT
implemented in v0.3 so the verdict is HOLD (not PASS), and the harness makes NO temporal-order claim (G6
invariant). These tests assert no vision/"Brainvision sees"/temporal-order claim. Offline; no torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

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


def test_transform_round_trip_and_gray_zero_chroma():
    rng = np.random.default_rng(0)
    rgb = rng.uniform(0, 1, size=(5, 4, 4, 3))
    Yp, RG, BY, _ = cb.forward(rgb)
    assert np.allclose(cb.inverse(Yp, RG, BY), rgb, atol=1e-10)   # exact inverse
    gray = np.full((3, 2, 2, 3), 0.37)
    _, g_rg, g_by, g_ch = cb.forward(gray)
    assert np.allclose(g_rg, 0) and np.allclose(g_by, 0) and np.allclose(g_ch, 0)  # gray -> zero chroma


def test_fixtures_do_not_clip_gamut():
    for name in cb.FIXTURES:
        d = cb.descriptor(cb.fixture(name))
        assert not d["_gamut"]["clipped"], f"{name} clipped: {d['_gamut']}"


def test_luminance_only_and_red_green_channels():
    d_lum = cb.descriptor(cb.fixture("luminance_only_change"))
    assert d_lum["Yp"]["response"] > 0.1                               # luma proxy moves
    assert d_lum["CHROMA"]["response"] < 1e-9                          # color collapsed
    d_rg = cb.descriptor(cb.fixture("red_green_opponent_change"))
    assert d_rg["RG"]["response"] > 0.01                              # RG moves
    assert d_rg["Yp"]["response"] <= cb.Y_HOLD_TOL                    # Y' held within tolerance


def test_grayscale_collapses_color_and_luminance_cannot_fake_color():
    base = cb.fixture("red_green_opponent_change")
    base_c = cb._color_response(cb.descriptor(base))
    gray_c = cb._color_response(cb.descriptor(cb.ctl_grayscale(base)))
    assert gray_c <= cb.COLLAPSE_RATIO * base_c                       # grayscale collapses color
    d_co = cb.descriptor(cb.fixture("color_only_equal_luminance"))
    assert cb._color_response(d_co) >= cb.SEPARATION_MARGIN * max(cb._lum_response(d_co), 1e-12)


def test_g2_strengthened_collapse_across_fixtures():
    # G2 must test collapse across ALL RG/BY/CHROMA-bearing validation fixtures, not just red_green
    res = cb.run_gates()
    assert set(res["g2_detail"]) == set(cb.G2_FIXTURES)
    assert all(v["ok"] for v in res["g2_detail"].values())
    assert res["gates"]["G2_color_collapses"] is True


def test_neutral_low_saturation():
    d = cb.descriptor(cb.fixture("low_saturation_neutral"))
    assert d["CHROMA"]["level"] <= cb.NEUTRAL_FLOOR


def test_allowed_use_discipline():
    assert cb.allowed_use("luminance_only_change") == "calibration"
    assert cb.allowed_use("low_saturation_neutral") == "stress"
    assert cb.allowed_use("color_only_equal_luminance") == "validation"


def test_gates_report_and_no_temporal_order_claim():
    res = cb.run_gates()
    for gk in ("G1_luminance_cannot_fake_color", "G2_color_collapses", "G3_luminance_not_color_only",
               "G4_low_sat_neutral", "G5_roughness_spectrum_faithful", "G6_no_temporal_order_claim"):
        assert gk in res["gates"]
    assert res["verdict"] in ("PASS", "FAIL", "HOLD")
    assert res["temporal_claim_allowed"] is False                    # G6 invariant
    assert res["gates"]["G6_no_temporal_order_claim"] is True
    # the validity claim is allowed ONLY if the verdict is PASS
    assert res["first_pass_descriptor_control_validity_claim_allowed"] == bool(res["verdict"] == "PASS")


def test_verdict_is_hold_pending_faithful_g5():
    # v0.3 does NOT implement the faithful roughness/spectrum G5, so full descriptor-control validity is not
    # established: core gates pass but the honest verdict is HOLD (machinery sanity-check only, NOT vision).
    res = cb.run_gates()
    assert res["fixture_gamut_clip"] is False and res["y_held_all"] is True
    g = res["gates"]
    assert g["G1_luminance_cannot_fake_color"] and g["G2_color_collapses"] and g["G3_luminance_not_color_only"] \
        and g["G4_low_sat_neutral"]
    assert g["G5_roughness_spectrum_faithful"] is False              # faithful G5 deferred
    assert res["verdict"] == "HOLD"
    assert res["first_pass_descriptor_control_validity_claim_allowed"] is False


def test_report_completes():
    s = cb.format_report()
    assert "v0.3" in s and "VERDICT: HOLD" in s and "NOT vision" in s and "reporting-only" in s


def test_rough_color_change_not_named_matched():
    # the v0.2 roughness_matched fixture is deferred; the implemented rough fixture must NOT claim matched behavior
    assert "rough_color_change" in cb.FIXTURES
    assert "roughness_matched_color_change" not in cb.FIXTURES
