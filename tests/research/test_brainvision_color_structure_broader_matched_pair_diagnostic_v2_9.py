"""v2.9 tests: broader matched-pair diagnostic (offline).

Lock the v2.9 slice: it broadens the matched-pair evidence for the directional (B) and per-channel (C)
candidates under the UNCHANGED frozen §7/§8 machinery, reusing the v0.7/v0.8 formulas + gate, the v1.9/v2.0
generators, the v2.1 bank, and the v2.4 decomposition by identity. Tests assert ROBUST facts only:
reuse-by-identity (no redefinition of frozen surfaces); predeclared criteria exist as code constants; every
predeclared family is reported (feasible or not); the frozen verdict stays HOLD and the reporting-only
classification can NEVER upgrade it; flags stay False; the classification vocabulary is exactly the v2.8 set;
non-collinear per-channel matches are reported as non-collinear; smoothness-without-winding cases carry the
operational fields. NOT platform-marginal correlation values. NO vision / temporal-order / memory-system claim.
Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs                                        # noqa: E402
import run_color_structure_directional_spectral_audit_v2_4 as v24            # noqa: E402
import run_color_structure_broader_matched_pair_diagnostic_v2_9 as v29       # noqa: E402

SRC = os.path.join(BV_DIR, "run_color_structure_broader_matched_pair_diagnostic_v2_9.py")

_ALLOWED = {"directional_B_strengthened", "directional_B_weakened", "per_channel_C_strengthened",
            "per_channel_C_weakened", "A_descriptor_limitation_supported", "mixed_or_unresolved"}


def test_imports_only_quarantined_research_surfaces():
    with open(SRC, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods.append(node.module or "")
    for m in mods:
        assert not m.startswith("torment") and "service" not in m, m
    assert set(mods) <= {"numpy", "__future__", "run_color_structure_v0_8",
                         "run_color_structure_fixture_bank_v1_1", "run_color_structure_movement_matched_v1_4",
                         "run_color_structure_spectral_std_blocker_v1_9", "run_color_structure_by_std_residual_v2_0",
                         "run_color_structure_integrated_residual_map_v2_1",
                         "run_color_structure_directional_spectral_audit_v2_4"}


def test_reuses_frozen_logic_by_identity_no_redefine():
    assert v29.structure_score is cs.structure_score
    assert v29.stats is cs._stats
    assert v29.spearman is cs.g5._spearman
    assert v29.CEIL == cs.MAGNITUDE_CORR_CEIL == 0.30
    assert v29.PSC_FLOOR == cs.PSC_FLOOR == 0.30
    assert v29.MATCH_REPORT_DELTA == 0.05   # reused descriptive cutoff, not a new threshold
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "def structure_score" not in src and "def _spearman" not in src and "def _stats" not in src


def test_predeclared_criteria_and_family_list_present():
    r = v29.run()
    p = r["predeclared_criteria_and_families"]
    for k in ("MATCH_REPORT_DELTA", "SEP_MIN_DELTA_S", "LOW_S_MAX", "PSC_FLOOR", "AIC_FLOOR", "CEIL",
              "REPEATED_SUPPORT_MIN_FAMILIES", "directional_winder_families", "directional_nonwinder_pool",
              "smoothness_cases", "per_channel_winder_families", "per_channel_noncollinear_pool",
              "per_channel_collinear_reference"):
        assert k in p


def test_all_predeclared_families_reported_none_dropped():
    r = v29.run()
    p = r["predeclared_criteria_and_families"]
    reported_dir = {row["family"] for row in r["directional_matched_expansion"]}
    assert reported_dir == set(p["directional_winder_families"])
    reported_smooth = {row["case"] for row in r["smoothness_without_winding"]}
    assert reported_smooth == set(p["smoothness_cases"])
    reported_pc = {row["family"] for row in r["per_channel_noncollinear_matches"]}
    assert reported_pc == set(p["per_channel_winder_families"])
    # every reported family carries an explicit feasibility label
    for row in r["directional_matched_expansion"] + r["per_channel_noncollinear_matches"]:
        assert row["feasibility"] in ("matched", "imperfect_match")
    for row in r["smoothness_without_winding"]:
        assert row["feasibility"] in ("constructed", "infeasible_not_low_jitter")


def test_verdict_hold_and_flags_false():
    r = v29.run()
    assert r["verdict"] == "HOLD" and r["verdict"] != "PASS"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False


def test_verdict_taken_from_frozen_v24_v21_by_identity():
    r = v29.run()
    assert r["verdict"] == v24.run()["verdict"] == "HOLD"


def test_classification_cannot_upgrade_verdict_regression_lock():
    r = v29.run()
    c = r["classification_output"]
    assert c["reporting_only"] is True
    assert c["cannot_change_verdict"] is True
    assert c["headline"] in _ALLOWED
    assert c["directional_axis"] in _ALLOWED
    assert c["per_channel_spectral_axis"] in _ALLOWED
    assert r["verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert "PASS" not in str(r["verdict"]) and c["headline"] != "PASS"


def test_non_collinear_per_channel_matches_are_non_collinear():
    r = v29.run()
    pc = r["per_channel_noncollinear_matches"]
    assert pc, "expected non-collinear per-channel families"
    for row in pc:
        assert row["non_collinear"] is True
        assert set(row) >= {"family", "nonwinder_pick", "mean_blocker_abs_delta", "matched", "delta_S",
                            "S_still_separates", "per_blocker"}


def test_smoothness_low_directional_requires_both_blockers():
    # v2.8 defines smoothness-without-winding as LOW u_ddr AND LOW angular increment; a low u_ddr with a high
    # angular increment must NOT count as low_directional (regression for the v2.9 criteria gap).
    assert v29._is_low_directional(0.04, 0.04) is True
    assert v29._is_low_directional(0.04, 5.0) is False
    assert v29._is_low_directional(5.0, 0.04) is False
    # and every constructed smoothness row in the live run has BOTH blockers at/below the bound
    r = v29.run()
    for row in r["smoothness_without_winding"]:
        if row["low_directional_blockers"]:
            assert row["u_directional_delta_rms"] <= v29.DIRECTIONAL_LOW_BOUND
            assert row["angular_increment_mag"] <= v29.DIRECTIONAL_LOW_BOUND


def test_smoothness_cases_carry_operational_fields():
    r = v29.run()
    for row in r["smoothness_without_winding"]:
        assert set(row) >= {"case", "S", "PSC", "AIC", "u_directional_delta_rms", "angular_increment_mag",
                            "low_directional_blockers", "stays_low_S_PSC", "feasibility"}


def test_target_preserving_pinned_reported_without_noise_correlation():
    # when the winder S is pinned, within-winder association is reported as 0.0 (no S variation to correlate)
    r = v29.run()
    tvb = r["target_vs_blocker_preserving"]
    if tvb["target_preserving_S_pinned"]:
        for b, d in tvb["target_preserving_within_winder_spearman"].items():
            assert d["rho"] == 0.0


def test_no_vision_temporal_or_memory_claim_in_source():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    assert "not proven vision" in src
    assert "no memory-system" in src or "memory-system integration" in src
    assert "temporal" in src
