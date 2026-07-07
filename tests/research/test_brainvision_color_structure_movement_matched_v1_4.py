"""v1.4 tests: movement-matched fixture diagnostic (offline).

Lock the v1.4 slice: predeclared movement-matched winder/non-winder families are generated and labeled; the
diagnostic reports THROUGH the unchanged v0.8/v1.1 logic (frozen PSC/AIC/S, constants, anti-proxy names, null
semantics, pass/HOLD/FAIL) reused by identity from run_color_structure_v0_8 and run_color_structure_fixture_bank_v1_1;
winders are winding-coherent and non-winders structurally non-winding by c(t)/PSC; matched pairs report
u_directional_delta_rms and angular_increment_mag and are (by construction) exactly matched while S separates;
match quality is present but REPORTING-ONLY (never gates); the trajectory-order-permuted null preserves the
multiset and destroys only order; reporting-only nulls never gate; neutral/floor fixtures stay neutral/below
ceiling; and no formula/constant/gate is redefined. NO temporal-order / vision / "Brainvision sees" claim.
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

import run_color_structure_v0_8 as cs              # noqa: E402
import run_color_structure_fixture_bank_v1_1 as fb  # noqa: E402
import run_color_structure_movement_matched_v1_4 as mm  # noqa: E402


def test_no_forbidden_imports_v1_4():
    with open(os.path.join(BV_DIR, "run_color_structure_movement_matched_v1_4.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert not a.name.startswith("torment"), a.name
        elif isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("torment"), node.module


def test_reuses_frozen_logic_by_identity():
    # must NOT redefine the descriptor / gate: reuse from cs (v0.8) and fb (v1.1) by identity.
    assert mm.structure_score is cs.structure_score
    assert mm.stats is cs._stats
    assert mm.traj_perm is cs.null_trajectory_order_permuted
    assert mm.series is cs._series
    assert mm.is_winding is fb.is_winding
    assert mm.traj_null_guarded is fb.traj_null_guarded
    assert (mm.cs.PSC_FLOOR, mm.cs.AIC_FLOOR, mm.cs.MAGNITUDE_CORR_CEIL, mm.cs.STRUCTURE_BEAT_MARGIN,
            mm.cs.NEUTRAL_STRUCTURE_CEIL) == (0.30, 0.30, 0.30, 0.20, 0.20)


def test_families_generated_and_labeled():
    res = mm.run(); pf = res["per_fixture"]
    assert set(pf) == set(mm.ALL_FIXTURES)
    for cl in "ABCD":
        assert any(d["class"] == cl for d in pf.values()), f"class {cl} missing"
    assert res["classes"]["A"]["roles"] == ["winder"] and res["classes"]["D"]["roles"] == ["winder"]
    assert res["classes"]["B"]["roles"] == ["nonwinder"] and res["classes"]["C"]["roles"] == ["nonwinder"]
    assert all(pf[f]["role_ok"] for f in mm.ALL_FIXTURES)


def test_winders_are_winding_coherent():
    res = mm.run(); pf = res["per_fixture"]
    for f in mm.WINDERS:
        rg, by, ch, _ = mm.fixture_series(f)
        s = cs.structure_score(rg, by, ch)
        assert pf[f]["winding"] is True and s["PSC"] >= cs.PSC_FLOOR and s["S"] > 0.5


def test_nonwinders_are_structurally_non_winding():
    res = mm.run(); pf = res["per_fixture"]
    for f in mm.NONWINDERS:
        rg, by, ch, _ = mm.fixture_series(f)
        s = cs.structure_score(rg, by, ch)
        # verified by signed-turn / PSC before use; B/C are not accidental coherent winders
        assert pf[f]["winding"] is False and s["PSC"] < cs.PSC_FLOOR and pf[f]["S"] < 0.5


def test_matched_pairs_report_movement_and_separate_on_S():
    res = mm.run()
    assert res["match_quality_reporting_only"] is True
    assert len(res["matched_pairs"]) == len(mm.MATCHED_PAIRS)
    for m in res["matched_pairs"]:
        # each pair reports both movement stats for winder and non-winder
        for k in ("u_ddr_winder", "u_ddr_nonwinder", "ang_winder", "ang_nonwinder",
                  "u_ddr_abs_diff", "ang_abs_diff"):
            assert k in m
        # by construction (same |Δθ| multiset) the movement stats match to numerical precision
        assert m["u_ddr_abs_diff"] < 1e-6 and m["ang_abs_diff"] < 1e-6
        # yet S / PSC separate winder from non-winder at matched movement
        assert m["S_winder"] > 0.5 and m["S_nonwinder"] < 0.5
        assert m["PSC_winder"] >= cs.PSC_FLOOR and m["PSC_nonwinder"] < cs.PSC_FLOOR


def test_match_quality_is_present_but_non_gating():
    res = mm.run(); pf = res["per_fixture"]
    assert res["match_quality_reporting_only"] is True
    # fixture_ok / verdict depend ONLY on frozen gating quantities, never on matched-pair movement diffs
    for f in mm.IN_SCOPE:
        d = pf[f]
        recomputed = bool(d["in_scope"] and (not d["traj_null_invalid"]) and d["beat_null"]
                          and d["floors_ok"] and (d["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * res["continuity_S"])
                          and (d["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * res["structureless_S"]))
        assert d["fixture_ok"] == recomputed


def test_trajectory_order_null_preserves_multiset_destroys_order():
    rg, by, ch, _ = mm.fixture_series("A_winder_m")
    rgp, byp, chp, retries, invalid = mm.traj_null_guarded(rg, by)
    assert sorted(zip(np.round(rg, 12), np.round(by, 12))) == sorted(zip(np.round(rgp, 12), np.round(byp, 12)))
    assert np.allclose(np.sort(ch), np.sort(chp))
    assert invalid is False and 0 <= retries <= fb.TRAJ_RETRY_LIMIT
    assert cs.structure_score(rgp, byp, chp)["PSC"] < cs.PSC_FLOOR   # winding destroyed by permutation


def test_reporting_only_nulls_present_but_non_gating():
    res = mm.run(); pf = res["per_fixture"]
    for f in mm.WINDERS:
        d = pf[f]
        for key in ("S_indep_null", "S_permuted_by", "S_shared_phase"):
            assert key in d and isinstance(d[key], float)


def test_neutral_floor_fixtures_stay_neutral_or_below_ceiling():
    res = mm.run()
    assert res["neutral_ok"] is True
    for k, v in res["neutral"].items():
        assert v["ok"] is True and (v["neutral"] or v["S"] <= cs.NEUTRAL_STRUCTURE_CEIL)


def test_verdict_uses_unchanged_v0_8_logic():
    res = mm.run()
    assert set(res["anti_proxy"]) == set(cs.ANTI_PROXY_STATS) | {"nr_" + x for x in cs.NULL_REL_STATS}
    assert res["verdict"] in ("PASS", "HOLD", "FAIL")
    assert res["temporal_claim_allowed"] is False
    assert res["first_pass_structure_validity_claim_allowed"] == bool(res["verdict"] == "PASS")
    # honest deterministic outcome for this diagnostic bank: winders beat their nulls, neutrals hold, but the
    # anti-proxy gate is not cleanly met -> HOLD (no tuning, no forced PASS, no validity claim).
    assert res["in_scope_ok"] == res["in_scope_n"]
    assert res["neutral_ok"] is True
    assert res["anti_proxy_ok"] is False
    assert res["verdict"] == "HOLD"
    assert res["first_pass_structure_validity_claim_allowed"] is False


def test_interpretive_outcome_reported():
    res = mm.run()
    assert isinstance(res["interpretive_outcome"], str) and res["interpretive_outcome"]
