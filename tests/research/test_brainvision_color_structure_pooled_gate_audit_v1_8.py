"""v1.8 tests: pooled-gate AUDIT diagnostic (offline).

Lock the v1.8 slice: the audit DECOMPOSES the existing pooled §7 HOLD of the v1.4 movement-matched bank under
the UNCHANGED gate. It reuses the frozen v0.7/v0.8 machinery by identity (spearman / ceiling / stat sets) and
the v1.1 + v1.4 fixtures; it produces reporting-only decomposition tables (5 sections); it faithfully
reproduces mm.run()'s §7 result; it changes no formula / gate / verdict / threshold, deletes no control, and
cannot move the verdict (taken verbatim from mm and staying HOLD). Classification is reporting-only and
conservative. NO vision / temporal-order / memory-system claim. Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs              # noqa: E402
import run_color_structure_movement_matched_v1_4 as mm  # noqa: E402
import run_color_structure_pooled_gate_audit_v1_8 as aud  # noqa: E402

AUDIT_SRC = os.path.join(BV_DIR, "run_color_structure_pooled_gate_audit_v1_8.py")
ALLOWED_LABELS = {"likely legitimate descriptor blocker", "likely fixture / control-composition artifact",
                  "likely validity-surface framing mismatch", "unresolved / needs adversarial review"}


def test_audit_imports_only_quarantined_research_surfaces():
    with open(AUDIT_SRC, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods.append(node.module or "")
    for m in mods:
        assert not m.startswith("torment"), m
        assert "service" not in m, m
    # only the quarantined research modules + numpy/__future__
    assert set(mods) <= {"numpy", "__future__", "run_color_structure_v0_8",
                         "run_color_structure_fixture_bank_v1_1", "run_color_structure_movement_matched_v1_4"}


def test_audit_runs_and_is_reporting_only():
    r = aud.run()
    assert r["reporting_only"] is True
    for sec in ("failing_stats_ranked", "subset_spearman", "fixture_class_contribution",
                "control_family_contribution", "classification_reporting_only"):
        assert sec in r and isinstance(r[sec], list) and r[sec]


def test_reuses_frozen_gate_by_identity_and_unchanged_ceiling():
    assert aud.spearman is cs.g5._spearman
    assert aud.CEIL == cs.MAGNITUDE_CORR_CEIL == 0.30
    assert aud.ANTI_PROXY_STATS is cs.ANTI_PROXY_STATS and aud.NULL_REL_STATS is cs.NULL_REL_STATS
    # the audit defines NO descriptor of its own
    with open(AUDIT_SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "def structure_score" not in src and "def _spearman" not in src


def test_reports_under_unchanged_sec7_faithfully():
    r = aud.run()
    mm_res = mm.run()
    assert r["faithful_reconstruction"] is True
    assert r["bank_size"] == r["mm_bank_size"] == mm_res["bank_size"] == 21
    # every full-bank stat rho reproduces mm's reported §7 anti-proxy (audit changed nothing)
    full = {d["stat"]: d["spearman_rho"] for d in r["failing_stats_ranked"]}
    for k, v in mm_res["anti_proxy"].items():
        assert abs(full[k] - v["spearman"]) < 5e-3
        assert (full[k] and abs(full[k]) >= aud.CEIL) == (not v["ok"]) or abs(full[k]) < aud.CEIL


def test_verdict_taken_from_mm_and_cannot_be_moved():
    r = aud.run()
    mm_res = mm.run()
    assert r["verdict"] == mm_res["verdict"] == "HOLD"
    assert r["anti_proxy_ok"] is False and mm_res["anti_proxy_ok"] is False
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False


def test_required_subsets_present():
    r = aud.run()
    subs = {d["subset"] for d in r["subset_spearman"]}
    assert {"full_bank", "matched_pairs", "null_controls", "coherent_winders",
            "non_winder_cancellation"} <= subs
    for d in r["subset_spearman"]:
        assert set(d) >= {"subset", "n", "stat", "rho", "abs_rho", "s_std"}


def test_controls_not_removed_all_four_families_present():
    r = aud.run()
    fams = {d["control_family"] for d in r["control_family_contribution"]}
    assert {"traj_null", "indep_null", "continuity_control", "structureless_control"} == fams
    # leave-one-out is attribution only; the full bank retains every control (bank_size unchanged)
    assert r["bank_size"] == 21


def test_fixture_class_contribution_is_leave_one_out_attribution():
    r = aud.run()
    classes = {d["fixture_class"] for d in r["fixture_class_contribution"]}
    assert classes == {"A", "B", "C", "D"}
    for d in r["fixture_class_contribution"]:
        assert set(d) >= {"fixture_class", "stat", "rho_without_class", "delta_from_full"}


def test_classification_conservative_and_bounded():
    r = aud.run()
    for d in r["classification_reporting_only"]:
        assert d["classification"] in ALLOWED_LABELS
        # a "blocker" label is only allowed when the failing correlation survives on the primary subset
        if d["classification"] == "likely legitimate descriptor blocker":
            assert d["rho_primary_subset"] is not None and abs(d["rho_primary_subset"]) >= aud.CEIL
    # classification cannot flip the verdict
    assert r["verdict"] == "HOLD"


def test_hold_preserved_no_subset_pass_path():
    # every failing stat is failing under the FULL gate; no subset/leave-one-out is treated as a pass path
    r = aud.run()
    failing = [d for d in r["failing_stats_ranked"] if d["gate"] == "fail"]
    assert failing and all(d["abs_rho"] >= aud.CEIL for d in failing)
    assert r["verdict"] == "HOLD"


def test_no_vision_temporal_or_memory_claim_in_source():
    with open(AUDIT_SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "not proven vision" in src.lower()
    assert "no memory-system" in src.lower() or "memory-system integration" in src.lower()
    assert "temporal" in src.lower()  # explicitly disclaimed


def test_spectral_centroid_primary_blocker_is_reported():
    r = aud.run()
    by_stat = {d["stat"]: d for d in r["classification_reporting_only"]}
    d = by_stat["spectral_centroid"]
    assert d["classification"] == "likely legitimate descriptor blocker"
    assert abs(d["rho_primary_subset"]) >= aud.CEIL


def test_matched_subset_blockers_are_reported_consistently():
    r = aud.run()
    blockers = {
        d["stat"]: d for d in r["classification_reporting_only"]
        if d["classification"] == "likely legitimate descriptor blocker"
    }
    expected = {"by_std", "spectral_centroid", "rg_spread", "nr_rg_spread"}
    assert set(blockers) == expected
    assert blockers["spectral_centroid"]["pooled_gate"] == "fail"
    for stat in expected - {"spectral_centroid"}:
        assert blockers[stat]["pooled_gate"] == "pass"
    for stat in expected:
        assert abs(blockers[stat]["rho_primary_subset"]) >= aud.CEIL
