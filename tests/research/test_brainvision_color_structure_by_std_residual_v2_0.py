"""v2.0 tests: by_std residual diagnostic (offline).

Lock the v2.0 slice: it decomposes the v1.9 by_std cross-family pool residual into within-class vs
between-class components and classifies it (pool-composition artifact / descriptor limitation / unresolved).
It reuses the frozen v0.7/v0.8 machinery by identity; produces the five reporting sections; separates pooled
vs within-family analysis; reports by_std pairwise deltas explicitly; the frozen §8 verdict over the v2.0 bank
stays HOLD (no validity claim, no forced pass); changes no formula/gate/threshold and removes no control.
Tests assert ROBUST facts only (PR pair by_std delta exactly 0 with S separation; the pooled mismatched vs
matched-range rhos are far from the 0.30 ceiling) -- NOT platform-marginal correlations. NO vision /
temporal-order / memory-system claim. Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs              # noqa: E402
import run_color_structure_by_std_residual_v2_0 as v2  # noqa: E402

SRC = os.path.join(BV_DIR, "run_color_structure_by_std_residual_v2_0.py")


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
                         "run_color_structure_spectral_std_blocker_v1_9"}


def test_runs_and_all_sections_present_reporting_only():
    r = v2.run()
    assert r["reporting_only"] is True
    for sec in ("by_std_residual_summary", "pairwise_by_std_control", "family_level_residuals",
                "pooled_vs_within_family_comparison"):
        assert sec in r


def test_reuses_frozen_logic_by_identity_no_redefine():
    assert v2.structure_score is cs.structure_score
    assert v2.stats is cs._stats
    assert v2.spearman is cs.g5._spearman
    assert v2.CEIL == cs.MAGNITUDE_CORR_CEIL == 0.30
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "def structure_score" not in src and "def _spearman" not in src


def test_allowed_flags_false_and_hold_bound():
    r = v2.run()
    assert r["verdict"] == "HOLD" and r["verdict"] != "PASS"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False


def test_by_std_pairwise_deltas_reported_explicitly():
    r = v2.run()
    assert r["pairwise_by_std_control"]
    for pc in r["pairwise_by_std_control"]:
        for key in ("pair_id", "winder_by_std", "nonwinder_by_std", "abs_by_std_delta", "S_separation",
                    "winder_S", "nonwinder_S", "winder_PSC", "nonwinder_PSC"):
            assert key in pc


def test_phase_relative_pair_matches_by_std_yet_S_separates():
    # PR_collinear: RG==BY makes by_std analytically identical (delta 0) between winder and non-winder,
    # yet S separates -> within-pair by_std does NOT explain S (artifact evidence).
    r = v2.run()
    pr = next(pc for pc in r["pairwise_by_std_control"] if pc["pair_id"] == "PR_collinear")
    assert pr["abs_by_std_delta"] == 0.0
    assert pr["S_separation"] > 0.5


def test_pooled_vs_within_family_separated_and_correlation_disappears_when_matched():
    r = v2.run()
    c = r["pooled_vs_within_family_comparison"]
    # pooled (mismatched by_std ranges) is well above the ceiling; matched-range pooled is well below it
    assert abs(c["pooled_mismatched_by_std_rho"]) >= cs.MAGNITUDE_CORR_CEIL
    assert abs(c["pooled_matched_range_by_std_rho"]) < cs.MAGNITUDE_CORR_CEIL
    assert c["pooled_correlation_disappears_when_ranges_matched"] is True
    assert c["pooled_correlation_persists_within_families"] is False


def test_single_winding_class_families_flagged_degenerate():
    r = v2.run()
    fams = {f["family"]: f for f in r["family_level_residuals"]}
    for g in ("winder_span", "outback_span", "collinear_span"):
        assert fams[g]["degenerate_or_underpowered"] is True   # S ~constant within a winding class


def test_classification_is_pool_composition_artifact():
    r = v2.run()
    assert r["by_std_residual_summary"]["classification"] == "pool-composition artifact"
    assert set(r["by_std_residual_summary"]["matched_pairs_that_still_separate"]) >= {"PR_collinear"}


def test_no_vision_temporal_or_memory_claim_in_source():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    assert "not proven vision" in src
    assert "no memory-system" in src or "memory-system integration" in src
    assert "temporal" in src
