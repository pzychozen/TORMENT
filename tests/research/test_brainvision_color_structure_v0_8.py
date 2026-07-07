"""v0.8 tests: chroma-structure formula diagnostic (offline).

Lock the frozen v0.7 machinery: offline-only, no service/runtime imports; a perfect rotation scores PSC≈AIC≈S≈1;
the PRIMARY trajectory-order-permuted null drops S far below the rotation (valid no-joint-structure null); the
independent phase-randomized null stays HIGH for narrowband rotations (which is exactly why it is reporting-only,
not the gate); zero-chroma controls return NEUTRAL; the smooth continuity control scores below the rotation
(rotation beats it); the anti-proxy bank follows v0.7 §7 (zero-chroma neutrals excluded); reporting-only nulls
cannot gate; and the honest deterministic verdict is HOLD (the anti-proxy roughness correlations are not cleanly
passed). NO temporal-order / vision / "Brainvision sees" claim. Offline; no torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs  # noqa: E402


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


def _series(name):
    frames = cs.cb._clip_from_series(*cs.rotation_series(name))
    sm = cs.cb._spatial_means(frames)
    return sm["RG"], sm["BY"], sm["CHROMA"]


def test_perfect_rotation_scores_one():
    for name in ("rot_full", "rot_multi2", "rot_reverse"):
        rg, by, ch = _series(name)
        s = cs.structure_score(rg, by, ch)
        assert not s["neutral"]
        assert s["PSC"] > 0.99 and s["AIC"] > 0.99 and s["S"] > 0.99


def test_trajectory_order_permuted_null_destroys_winding():
    rg, by, ch = _series("rot_full")
    s_int = cs.structure_score(rg, by, ch)
    rgp, byp = cs.null_trajectory_order_permuted(rg, by, cs.PERM_SEED)
    s_null = cs.structure_score(rgp, byp, np.sqrt(rgp ** 2 + byp ** 2))
    assert s_null["S"] < 0.5 * s_int["S"]                       # primary gate null: winding destroyed
    # multiset of unit directions / CHROMA preserved (same magnitudes, permuted order)
    assert np.allclose(np.sort(np.sqrt(rgp ** 2 + byp ** 2)), np.sort(ch))


def test_independent_phase_null_stays_high_for_narrowband():
    # Codex correction: for single-frequency rotation fixtures independent RG/BY phase randomization yields a
    # coherent ellipse -> S stays high -> it must be reporting-only, NOT the primary gate.
    rg, by, ch = _series("rot_full")
    irg, iby = cs.null_independent_phase(rg, by, 3000)
    s_indep = cs.structure_score(irg, iby, np.sqrt(irg ** 2 + iby ** 2))
    assert s_indep["S"] > 0.5


def test_zero_chroma_is_neutral():
    z = np.zeros(cs.T)
    s = cs.structure_score(z, z, z)
    assert s["neutral"] is True and s["S"] == 0.0


def test_continuity_below_rotation():
    yp, rg, by = cs.continuity_control()
    frames = cs.cb._clip_from_series(yp, rg, by)
    sm = cs.cb._spatial_means(frames)
    s_cont = cs.structure_score(sm["RG"], sm["BY"], sm["CHROMA"])["S"]
    s_rot = cs.structure_score(*_series("rot_full"))["S"]
    assert s_rot >= (1 + cs.STRUCTURE_BEAT_MARGIN) * s_cont      # rotation beats continuity by margin


def test_run_shape_and_reporting_only_discipline():
    res = cs.run()
    assert set(cs.IN_SCOPE) <= set(res["per_fixture"])
    for f in cs.IN_SCOPE:
        d = res["per_fixture"][f]
        assert d["in_scope"] and d["beat_null"]                 # beats the PRIMARY (trajectory) null
    # arcs are reporting-only (in_scope False)
    for f in cs.ARC_REPORT:
        assert res["per_fixture"][f]["in_scope"] is False
    assert set(res["anti_proxy"]) == set(cs.ANTI_PROXY_STATS) | {"nr_" + x for x in cs.NULL_REL_STATS}
    assert res["verdict"] in ("PASS", "HOLD", "FAIL")
    assert res["temporal_claim_allowed"] is False
    assert res["first_pass_structure_validity_claim_allowed"] == bool(res["verdict"] == "PASS")


def test_synthetic_verdict_is_hold_anti_proxy_blocks():
    # deterministic honest outcome: rotations detect winding and beat the primary null + continuity, but the
    # anti-proxy roughness correlations are NOT cleanly passed -> HOLD (no tuning to force PASS).
    res = cs.run()
    assert res["in_scope_ok"] == res["in_scope_n"]              # all in-scope fixtures beat null+continuity+floors
    assert res["neutral_ok"] is True
    assert res["anti_proxy_ok"] is False                        # directional/angular roughness correlations fail
    assert res["verdict"] == "HOLD"
    assert res["first_pass_structure_validity_claim_allowed"] is False


def test_shared_phase_null_preserves_relative_phase():
    # after the Codex fix, the shared-phase null adds a shared phase OFFSET (relative phase preserved) -> a
    # rotation stays rotation-like -> S high. It is REPORTING-ONLY and never gates.
    rg, by, ch = _series("rot_full")
    srg, sby = cs.null_shared_phase(rg, by, 5000)
    s_shared = cs.structure_score(srg, sby, np.sqrt(srg ** 2 + sby ** 2))
    assert s_shared["S"] > 0.5


def test_reported_out_of_scope_fixtures_do_not_gate():
    res = cs.run()
    assert set(res["reported_out_of_scope"]) == {
        "red_green_opponent_change", "blue_yellow_opponent_change", "color_only_equal_luminance"}
    # degenerate / collinear -> low structure, and they are NOT in the PASS-eligible in-scope set
    for name in res["reported_out_of_scope"]:
        assert name not in cs.IN_SCOPE


def test_report_completes():
    s = cs.format_report()
    assert "v0.8" in s and "VERDICT: HOLD" in s and "NOT vision" in s and "reporting-only" in s
