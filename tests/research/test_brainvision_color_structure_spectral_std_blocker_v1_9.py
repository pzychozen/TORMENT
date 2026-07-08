"""v1.9 tests: spectral/std blocker diagnostic (offline).

Lock the v1.9 slice: it attacks the four v1.8 spectral/std blockers (spectral_centroid, by_std, rg_spread,
nr_rg_spread) by comparing coherent winders vs cancelling non-winders while those axes are controlled. It
reuses the frozen v0.7/v0.8 machinery by identity; it produces the four reporting sections; it reports blocker
deltas explicitly; the frozen §8 verdict over the v1.9 bank stays HOLD (no validity claim, no forced pass); it
changes no formula/gate/threshold and removes no control. Tests assert ROBUST structural facts only (e.g. the
phase-relative family's by_std/rg_spread deltas are analytically 0 while S still separates) -- NOT the
noise-dominated spectral_centroid values nor any platform-marginal pool correlation. NO vision / temporal-order
/ memory-system claim. Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs              # noqa: E402
import run_color_structure_spectral_std_blocker_v1_9 as v9  # noqa: E402

SRC = os.path.join(BV_DIR, "run_color_structure_spectral_std_blocker_v1_9.py")


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
                         "run_color_structure_fixture_bank_v1_1", "run_color_structure_movement_matched_v1_4"}


def test_runs_and_all_sections_present_reporting_only():
    r = v9.run()
    assert r["reporting_only"] is True
    for sec in ("blocker_match_table", "separation_under_blocker_control", "blocker_residuals"):
        assert sec in r and isinstance(r[sec], list) and r[sec]
    assert isinstance(r["anti_proxy"], dict) and r["anti_proxy"]


def test_reuses_frozen_logic_by_identity_no_redefine():
    assert v9.structure_score is cs.structure_score
    assert v9.stats is cs._stats
    assert v9.spearman is cs.g5._spearman
    assert v9.CEIL == cs.MAGNITUDE_CORR_CEIL == 0.30
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "def structure_score" not in src and "def _spearman" not in src


def test_allowed_flags_false_and_hold_bound():
    r = v9.run()
    assert r["verdict"] == "HOLD"                       # frozen §8 over the v1.9 bank; no forced pass
    assert r["verdict"] != "PASS"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False


def test_all_four_blocker_deltas_reported_per_pair():
    r = v9.run()
    blks = {"spectral_centroid", "by_std", "rg_spread", "nr_rg_spread"}
    for row in r["blocker_match_table"]:
        assert set(row["blocker_abs_delta"]) == blks
        for b in blks:
            assert isinstance(row["blocker_abs_delta"][b], float)
        assert "S_separation" in row and "PSC_separation" in row


def test_phase_relative_family_neutralizes_by_std_and_rg_spread_but_S_still_separates():
    # PR_collinear: RG==BY makes by_std / rg_spread / nr_rg_spread ANALYTICALLY identical to the quadrature
    # winder's (delta exactly 0), yet the collinear path cancels winding -> S/PSC still separates.
    r = v9.run()
    pr = next(row for row in r["blocker_match_table"] if row["pair_id"] == "PR_collinear")
    assert pr["blocker_abs_delta"]["by_std"] == 0.0
    assert pr["blocker_abs_delta"]["rg_spread"] == 0.0
    assert pr["blocker_abs_delta"]["nr_rg_spread"] == 0.0
    assert pr["winder"]["PSC"] >= cs.PSC_FLOOR and pr["nonwinder"]["PSC"] < cs.PSC_FLOOR
    assert pr["S_separation"] > 0.5


def test_every_family_separates_winding_from_cancellation():
    r = v9.run()
    assert len(r["separation_under_blocker_control"]) == len(v9._PAIRS)
    for s in r["separation_under_blocker_control"]:
        assert s["winder_winds"] is True and s["nonwinder_cancels"] is True
        assert s["S_still_separates"] is True
    # at least one family drives ALL four blocker deltas below the descriptive match cutoff
    assert any(s["all_blockers_matched"] for s in r["separation_under_blocker_control"])


def test_controls_present_not_removed():
    r = v9.run()
    # the v1.9 bank retains the continuity + structureless controls (not deleted)
    assert r["bank_size"] >= len(v9._PAIRS) * 2 + 2
    residual_blockers = {b["blocker"] for b in r["blocker_residuals"]}
    assert residual_blockers == {"spectral_centroid", "by_std", "rg_spread", "nr_rg_spread"}


def test_no_vision_temporal_or_memory_claim_in_source():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    assert "not proven vision" in src
    assert "no memory-system" in src or "memory-system integration" in src
    assert "temporal" in src


def test_in_scope_winders_beat_trajectory_nulls_under_frozen_margin():
    # governance: the §8 verdict must retain the primary trajectory-null beat (not simplified away).
    r = v9.run()
    rows = r["blocker_match_table"]
    assert rows
    for row in rows:
        assert row["winder_traj_null_S"] is not None
        assert row["winder"]["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * row["winder_traj_null_S"]
    # and the verdict block source retains the trajectory-null lookup AND the FAIL branch
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "traj_by_pair" in src and "n_le_null" in src and 'verdict = "FAIL"' in src
    assert r["verdict"] == "HOLD"
