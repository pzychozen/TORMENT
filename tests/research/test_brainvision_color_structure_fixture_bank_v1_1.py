"""v1.1 tests: fixture-bank redesign (offline).

Lock the v1.1 slice: the predeclared A-H fixture classes are generated and labeled; the diagnostic reports
THROUGH the unchanged v0.7/v0.8 logic (frozen PSC/AIC/S, constants, anti-proxy names, null semantics,
pass/HOLD/FAIL) reused by identity from run_color_structure_v0_8; A<->D pair over chroma magnitude and B<->E
over spectral spread; E fixtures are structurally non-winding by the signed-turn c(t); the G null is a pure
trajectory-order permutation (multiset of (RG,BY) preserved, order destroyed) with a bounded predeclared guard
(no redraw-until-desired-S); H neutral fixtures stay NEUTRAL/below ceiling; reporting-only nulls are present but
never gate; and no formula/constant/gate is redefined. NO temporal-order / vision / "Brainvision sees" claim.
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

import run_color_structure_v0_8 as cs        # noqa: E402
import run_color_structure_fixture_bank_v1_1 as fb  # noqa: E402


def test_no_forbidden_imports_v1_1():
    with open(os.path.join(BV_DIR, "run_color_structure_fixture_bank_v1_1.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert not a.name.startswith("torment"), a.name
        elif isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("torment"), node.module


def test_reuses_frozen_logic_by_identity():
    # the v1.1 module must NOT redefine the descriptor / gate: it reuses them from cs by identity.
    assert fb.structure_score is cs.structure_score
    assert fb.stats is cs._stats
    assert fb.traj_perm is cs.null_trajectory_order_permuted
    assert fb.series is cs._series
    # frozen constants are the cs constants (unchanged values)
    assert (fb.cs.PSC_FLOOR, fb.cs.AIC_FLOOR, fb.cs.MAGNITUDE_CORR_CEIL, fb.cs.STRUCTURE_BEAT_MARGIN,
            fb.cs.NEUTRAL_STRUCTURE_CEIL) == (0.30, 0.30, 0.30, 0.20, 0.20)


def test_all_classes_generated_and_labeled():
    res = fb.run()
    pf = res["per_fixture"]
    assert set(pf) == set(fb.ALL_FIXTURES)
    for cl in "ABCDEF":
        assert any(d["class"] == cl for d in pf.values()), f"class {cl} missing"
    # class sizes balanced enough that no single class dominates the pooled bank
    sizes = {cl: res["classes"][cl]["n"] for cl in "ABCDEF"}
    assert max(sizes.values()) <= 3 * min(sizes.values())


def test_winding_families_are_winding_lowS_families_are_not():
    res = fb.run()
    pf = res["per_fixture"]
    for f in fb.WIND_IN_SCOPE:                      # A + B + F
        assert pf[f]["winding"] is True and pf[f]["PSC"] >= cs.PSC_FLOOR and pf[f]["S"] > 0.5
    for f in [s[0] for s in fb.C_SPECS] + [s[0] for s in fb.E_SPECS]:
        assert pf[f]["winding"] is False and pf[f]["S"] < 0.5


def test_A_D_magnitude_pairing_exists():
    res = fb.run(); pf = res["per_fixture"]
    A = [s[0] for s in fb.A_SPECS]
    D = [s[0] for s in fb.D_SPECS]
    a_cm = [fb.stats(*fb.fixture_series(f)[:3])["chroma_mag"] for f in A]
    d_cm = [fb.stats(*fb.fixture_series(f)[:3])["chroma_mag"] for f in D]
    # overlapping magnitude ranges, but A high-S and D low-S over that shared range
    assert min(a_cm) <= max(d_cm) and min(d_cm) <= max(a_cm)          # ranges overlap
    assert np.mean([pf[f]["S"] for f in A]) > 0.9
    assert np.mean([pf[f]["S"] for f in D]) < 0.5
    # magnitude proxy is decorrelated on the redesigned bank (the v0.8 chroma_mag failure is gone)
    assert res["anti_proxy"]["chroma_mag"]["ok"] is True


def test_B_E_spectral_spread_pairing_exists():
    res = fb.run(); pf = res["per_fixture"]
    B = [s[0] for s in fb.B_SPECS]
    E = [s[0] for s in fb.E_SPECS]
    b_sp = [fb.stats(*fb.fixture_series(f)[:3])["by_spread"] for f in B]
    e_sp = [fb.stats(*fb.fixture_series(f)[:3])["by_spread"] for f in E]
    assert np.mean(b_sp) > 0 and np.mean(e_sp) >= 0                    # both families present
    assert np.mean([pf[f]["S"] for f in B]) > 0.9                     # B coherent winders (high S)
    assert np.mean([pf[f]["S"] for f in E]) < 0.1                     # E narrowband, non-winding (low S)


def test_E_is_structurally_non_winding_by_c_of_t():
    for f in [s[0] for s in fb.E_SPECS]:
        rg, by, ch, _ = fb.fixture_series(f)
        s = cs.structure_score(rg, by, ch)
        # signed-turn path/scatter contrast collapses -> not coherent winding (verified by c(t), not by S alone)
        assert s["PSC"] < cs.PSC_FLOOR and s["PSC"] < 0.05
        winding, _s = fb.is_winding(rg, by, ch)
        assert winding is False
        st = fb.stats(rg, by, ch)
        assert st["rg_std"] > 1e-6 and st["by_std"] > 1e-6
        assert st["rg_spread"] < 0.03 and st["by_spread"] < 0.03


def test_D_structureless_family_is_non_winding_by_c_of_t():
    res = fb.run()
    for f in [s[0] for s in fb.D_SPECS]:
        rg, by, ch, _ = fb.fixture_series(f)
        s = cs.structure_score(rg, by, ch)
        assert res["per_fixture"][f]["winding"] is False
        assert s["PSC"] < cs.PSC_FLOOR
        assert res["per_fixture"][f]["S"] < 0.5


def test_G_null_is_pure_trajectory_order_permutation():
    rg, by, ch, _ = fb.fixture_series("A_mag_full")
    rgp, byp, chp, retries, invalid = fb.traj_null_guarded(rg, by)
    # multiset of (RG,BY) pairs preserved -> multiset of u(t) directions and CHROMA preserved; only order destroyed
    assert sorted(zip(np.round(rg, 12), np.round(by, 12))) == sorted(zip(np.round(rgp, 12), np.round(byp, 12)))
    assert np.allclose(np.sort(ch), np.sort(chp))
    # a coherent winder's trajectory-order null destroys winding, accepted within the fixed retry budget
    assert invalid is False and 0 <= retries <= fb.TRAJ_RETRY_LIMIT
    assert cs.structure_score(rgp, byp, chp)["PSC"] < cs.PSC_FLOOR


def test_G_guard_is_bounded_no_redraw_until_desired():
    # predeclared bounded guard: fixed retry limit and a fixed fallback-seed order (never chase an S).
    assert isinstance(fb.TRAJ_RETRY_LIMIT, int) and fb.TRAJ_RETRY_LIMIT <= 3
    assert len(fb.TRAJ_FALLBACK_OFFSETS) >= fb.TRAJ_RETRY_LIMIT + 1
    for f in fb.ALL_FIXTURES:
        rg, by, _ch, _ = fb.fixture_series(f)
        _r, _b, _c, retries, _inv = fb.traj_null_guarded(rg, by)
        assert retries <= fb.TRAJ_RETRY_LIMIT


def test_H_neutral_fixtures_stay_neutral_or_below_ceiling():
    res = fb.run()
    assert res["neutral_ok"] is True
    for k, v in res["neutral"].items():
        assert v["ok"] is True and (v["neutral"] or v["S"] <= cs.NEUTRAL_STRUCTURE_CEIL)


def test_reporting_only_nulls_present_but_non_gating():
    res = fb.run(); pf = res["per_fixture"]
    for f in fb.WIND_IN_SCOPE:
        d = pf[f]
        for key in ("S_indep_null", "S_permuted_by", "S_shared_phase"):
            assert key in d and isinstance(d[key], float)
        # fixture_ok depends ONLY on gating quantities, never on the reporting-only nulls
        recomputed = bool(d["in_scope"] and (not d["traj_null_invalid"]) and d["beat_null"]
                          and d["beat_continuity"] and d["beat_structureless"] and d["floors_ok"])
        assert d["fixture_ok"] == recomputed


def test_verdict_uses_unchanged_v0_8_logic_and_stays_hold():
    res = fb.run()
    assert set(res["anti_proxy"]) == set(cs.ANTI_PROXY_STATS) | {"nr_" + x for x in cs.NULL_REL_STATS}
    assert res["verdict"] in ("PASS", "HOLD", "FAIL")
    assert res["temporal_claim_allowed"] is False
    assert res["first_pass_structure_validity_claim_allowed"] == bool(res["verdict"] == "PASS")
    # honest deterministic outcome for this bank: winders beat their nulls, neutrals hold, but the anti-proxy
    # gate is not cleanly met (directional/per-channel-spectral axis) -> HOLD (no tuning to force PASS).
    assert res["in_scope_ok"] == res["in_scope_n"]
    assert res["neutral_ok"] is True
    assert res["anti_proxy_ok"] is False
    assert res["verdict"] == "HOLD"


def test_hard_cases_retained_in_bank():
    # anti-cherry-picking: the hard low-S families and controls must be present (not deleted to clean the gate).
    res = fb.run()
    for f in [s[0] for s in fb.D_SPECS] + [s[0] for s in fb.E_SPECS]:
        assert f in res["per_fixture"]
    assert res["continuity_S"] > 0 and res["structureless_S"] == 0.0
