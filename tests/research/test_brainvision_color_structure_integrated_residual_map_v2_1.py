"""v2.1 tests: integrated residual map / deconfounded-bank diagnostic (offline).

Lock the v2.1 slice: it consolidates the v1.9/v2.0 resolved controls into ONE bank, re-runs the frozen §7
anti-proxy over it, and maps which failures remain vs are controlled/explained. It reuses the frozen v0.7/v0.8
machinery by identity; produces the five reporting sections; preserves the hard controls (trajectory nulls +
independent-phase nulls + structureless + continuity); the frozen §8 verdict stays HOLD (no forced pass); it
changes no formula/gate/threshold and removes no control. Tests assert ROBUST facts only (by_std/spectral_centroid
controlled far below ceiling; the directional axis remains failing far above ceiling; S/PSC separates) -- NOT
platform-marginal correlations. NO vision / temporal-order / memory-system claim. Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs                       # noqa: E402
import run_color_structure_integrated_residual_map_v2_1 as v21  # noqa: E402

SRC = os.path.join(BV_DIR, "run_color_structure_integrated_residual_map_v2_1.py")


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
                         "run_color_structure_spectral_std_blocker_v1_9", "run_color_structure_by_std_residual_v2_0"}


def test_runs_and_all_sections_present_reporting_only():
    r = v21.run()
    assert r["reporting_only"] is True
    for sec in ("integrated_residual_summary", "anti_proxy_failure_map", "deconfounded_bank_summary",
                "separation_summary", "residual_interpretation"):
        assert sec in r


def test_reuses_frozen_logic_by_identity_no_redefine():
    assert v21.structure_score is cs.structure_score
    assert v21.stats is cs._stats
    assert v21.spearman is cs.g5._spearman
    assert v21.CEIL == cs.MAGNITUDE_CORR_CEIL == 0.30
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "def structure_score" not in src and "def _spearman" not in src


def test_allowed_flags_false_and_hold_bound():
    r = v21.run()
    s = r["integrated_residual_summary"]
    assert s["verdict"] == "HOLD" and s["verdict"] != "PASS"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False


def test_anti_proxy_map_complete_under_unchanged_sec7():
    r = v21.run()
    stats_seen = {d["stat"] for d in r["anti_proxy_failure_map"]}
    expected = set(cs.ANTI_PROXY_STATS) | {"nr_" + x for x in cs.NULL_REL_STATS}
    assert stats_seen == expected
    for d in r["anti_proxy_failure_map"]:
        assert set(d) >= {"stat", "rho", "abs_rho", "gate", "status", "evidence_note"}
        assert d["status"] in ("remaining_failure", "controlled_or_explained", "pass")


def test_hard_controls_preserved_present():
    r = v21.run()
    b = r["deconfounded_bank_summary"]
    assert b["traj_null_count"] > 0 and b["indep_null_count"] > 0
    assert b["all_required_controls_present"] is True
    names = {e for e in b["fixture_families"]}
    assert any("winder_span" == n or n.startswith("pairwise:") for n in names)


def test_by_std_and_spectral_centroid_controlled_or_explained():
    # v2.0/v1.8 confounds are controlled on the consolidated bank (far below the 0.30 ceiling -> robust)
    r = v21.run()
    resolved = set(r["integrated_residual_summary"]["resolved_or_explained_failures"])
    assert "by_std" in resolved and "spectral_centroid" in resolved
    by = {d["stat"]: d for d in r["anti_proxy_failure_map"]}
    assert by["by_std"]["gate"] == "pass" and by["spectral_centroid"]["gate"] == "pass"


def test_directional_axis_remains_failing_and_classification():
    # after controlling the spectral/std confounds, the directional / per-channel-spectral axis still fails
    r = v21.run()
    rem = set(r["integrated_residual_summary"]["remaining_failures"])
    assert {"u_directional_delta_rms", "angular_increment_mag"} <= rem
    assert r["integrated_residual_summary"]["classification"] == "residual_failures_remain"
    assert r["separation_summary"]["S_PSC_still_separates"] is True


def test_no_vision_temporal_or_memory_claim_in_source():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    assert "not proven vision" in src
    assert "no memory-system" in src or "memory-system integration" in src
    assert "temporal" in src
