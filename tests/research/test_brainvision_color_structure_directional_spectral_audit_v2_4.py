"""v2.4 tests: directional / per-channel-spectral causality audit (offline).

Lock the v2.4 slice: it DECOMPOSES the surviving directional / per-channel-spectral residual axis under the
UNCHANGED frozen §7/§8 machinery, reusing the v0.7/v0.8 formulas + gate and the v2.1 consolidated bank by
identity. Tests assert: reuse-by-identity (no redefinition of the frozen surfaces); all six reporting sections
present; the frozen verdict stays HOLD and the reporting-only classification can NEVER upgrade it; the flags stay
False; the classification vocabulary is exactly the v2.3 predeclared set; the driver table ranks the remaining
axis; matched-pair separation at fixed blocker is reported; imports stay inside the quarantined research surface.
Tests assert ROBUST facts only (verdict HOLD, flags False, sections present, reuse-by-identity, regression lock) --
NOT platform-marginal correlation values. NO vision / temporal-order / memory-system claim. Offline; no
torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs                                     # noqa: E402
import run_color_structure_integrated_residual_map_v2_1 as v21           # noqa: E402
import run_color_structure_directional_spectral_audit_v2_4 as v24        # noqa: E402

SRC = os.path.join(BV_DIR, "run_color_structure_directional_spectral_audit_v2_4.py")

_ALLOWED_CLASS = {"A_descriptor_limitation_supported", "B_validity_surface_mismatch_supported",
                  "C_bank_composition_artifact_supported", "mixed_or_unresolved"}


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
                         "run_color_structure_integrated_residual_map_v2_1"}


def test_reuses_frozen_logic_by_identity_no_redefine():
    assert v24.structure_score is cs.structure_score
    assert v24.stats is cs._stats
    assert v24.spearman is cs.g5._spearman
    assert v24.CEIL == cs.MAGNITUDE_CORR_CEIL == 0.30
    assert v24.PSC_FLOOR == cs.PSC_FLOOR == 0.30
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "def structure_score" not in src and "def _spearman" not in src
    assert "def _stats" not in src


def test_runs_and_all_six_sections_present_reporting_only():
    r = v24.run()
    assert r["reporting_only"] is True
    for sec in ("pooled_spearman_driver_table", "matched_pair_diagnostics", "null_relative_decomposition",
                "within_cross_pooled_table", "pairwise_deltas", "classification_output"):
        assert sec in r


def test_verdict_hold_and_flags_false():
    r = v24.run()
    assert r["verdict"] == "HOLD" and r["verdict"] != "PASS"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False


def test_verdict_taken_from_frozen_v21_by_identity():
    # the verdict is the frozen §8 verdict over the v2.1 consolidated bank -- v2.4 does not recompute or move it
    r = v24.run()
    assert r["verdict"] == v21.run()["integrated_residual_summary"]["verdict"] == "HOLD"


def test_classification_cannot_upgrade_verdict_regression_lock():
    r = v24.run()
    c = r["classification_output"]
    # classification is reporting-only and structurally cannot change the verdict
    assert c["reporting_only"] is True
    assert c["cannot_change_verdict"] is True
    assert c["classification"] in _ALLOWED_CLASS
    # even if the classification vocabulary were maximally favorable, the verdict/flags are unmoved
    assert r["verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    # no reporting-only PASS token may leak into the verdict-bearing fields
    assert "PASS" not in str(r["verdict"])
    assert c["classification"] != "PASS"


def test_driver_table_ranks_remaining_axis_under_unchanged_gate():
    r = v24.run()
    rows = r["pooled_spearman_driver_table"]["remaining_driver_rows"]
    assert len(rows) >= 6
    # ranked by descending |rho|
    ranks = [row["rank"] for row in rows]
    assert ranks == sorted(ranks)
    absr = [row["abs_rho"] for row in rows]
    assert absr == sorted(absr, reverse=True)
    # every remaining-axis row is a §7 fail under the unchanged gate (that is the surviving wall)
    assert all(row["gate"] == "fail" for row in rows)
    # by_std / spectral_centroid appear only as CONTROLLED reference (they are NOT remaining failures)
    ref = {d["stat"]: d for d in r["pooled_spearman_driver_table"]["controlled_reference_rows"]}
    assert ref["by_std"]["gate"] == "pass" and ref["spectral_centroid"]["gate"] == "pass"


def test_matched_pairs_report_separation_at_fixed_blocker():
    r = v24.run()
    fams = {p["family"] for p in r["matched_pair_diagnostics"]}
    assert {"movement", "rg_by_centroid", "rg_by_spread"} <= fams
    for p in r["matched_pair_diagnostics"]:
        assert set(p) >= {"family", "target_blockers", "nonwinder_pick", "mean_blocker_abs_delta",
                          "all_blockers_matched", "S_still_separates"}
    for d in r["pairwise_deltas"]:
        assert set(d) >= {"family", "delta_S", "delta_PSC", "target_blocker_mean_abs_delta",
                          "blocker_exactly_or_approx_matched", "S_PSC_still_separated"}


def test_per_axis_readings_use_predeclared_vocabulary():
    r = v24.run()
    per_axis = r["classification_output"]["per_axis_readings"]
    assert {"directional", "per_channel_spectral"} <= set(per_axis)
    for ax, d in per_axis.items():
        assert d["reading"].split("_")[0] in ("A", "B", "C", "no", "mixed")


def test_no_vision_temporal_or_memory_claim_in_source():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    assert "not proven vision" in src
    assert "no memory-system" in src or "memory-system integration" in src
    assert "temporal" in src
