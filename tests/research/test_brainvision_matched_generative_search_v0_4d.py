"""v0.4d tests: matched generative search over the sealed v0.4c enumeration (form A, NON-LEARNING; offline).

Lock the v0.4d slice to ROBUST, platform-independent facts: it runs EXACTLY the sealed enumeration (families /
grid / seeds / dev-held-out split / finite 283-evaluation budget); the SOLE non-structure feasibility constraint
is PSC < PSC_FLOOR (AIC plays no role); selection uses ONLY proxy_match_residual + feasibility (no decision /
baseline / label / S_best_threshold objective); held-out is single-shot; NaN / non-finite / extreme values can
never satisfy feasibility, matching, or a pass; frozen surfaces are reused by identity; and claim locks stay
False with verdict HOLD under every outcome. Offline; no torment_service.
"""
import ast
import math
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs                                   # noqa: E402
import run_all_shortcuts_closed_synthetic_v0_3 as v3                    # noqa: E402
import run_matched_generative_search_v0_4d as m                         # noqa: E402

SRC = os.path.join(BV_DIR, "run_matched_generative_search_v0_4d.py")


def _clean_feat(psc, aic=0.99):
    d = {s: 0.01 for s in m.MATCHED_STATS}
    d["PSC"] = psc
    d["AIC"] = aic
    d["S"] = 0.0
    return d


# ---- provenance / no forbidden imports ----
def test_imports_only_quarantined_research_surfaces():
    with open(SRC, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods.append(node.module or "")
    for mod in mods:
        assert not mod.startswith("torment") and "service" not in mod, mod
    assert set(mods) <= {"numpy", "__future__", "run_color_structure_v0_8",
                         "run_color_structure_spectral_std_blocker_v1_9",
                         "run_color_structure_by_std_residual_v2_0",
                         "run_all_shortcuts_closed_synthetic_v0_3"}


def test_reuses_frozen_surfaces_by_identity():
    assert m._feat is v3._feat
    assert m.GROUPS is v3.GROUPS
    assert m.PSC_FLOOR == cs.PSC_FLOOR and m.AIC_FLOOR == cs.AIC_FLOOR
    assert m.CHANCE_BAND == v3.CHANCE_BAND
    # matched stats = dedup union of the four matched groups, spectral EXCLUDED
    expect = tuple(dict.fromkeys(s for g in m.MATCHED_GROUPS for s in v3.GROUPS[g]))
    assert m.MATCHED_STATS == expect
    assert "spectral_centroid" not in m.MATCHED_STATS and "spectral_spread" not in m.MATCHED_STATS
    assert set(m.MATCHED_GROUPS) == {"movement_channel_energy", "directional", "per_channel", "frame_diff"}


# ---- frozen protocol thresholds referenced, not re-invented ----
def test_frozen_protocol_thresholds():
    assert m.TOL == 0.0634
    assert m.PSC_FLOOR == 0.30 and m.AIC_FLOOR == 0.30
    assert m.CHANCE_BAND == 0.60
    assert m.run()["frozen_evaluator"] == "structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR"


# ---- sealed enumeration: families / grid / seeds / split ----
def test_families_grid_seeds_split_match_v0_4c():
    assert m.FAMILIES == ("full_circle_incoherent_traversal", "rosette_multilobe_traversal",
                          "segment_paired_canceller", "phase_scrambled_full_coverage",
                          "hybrid_coverage_preserving_canceller")
    assert m.F1_SIGMAS == (0.3, 0.6, 1.0)
    assert m.F2_LOBES == (2, 3, 5) and m.F2_RADII == (0.7, 1.0)
    assert m.F3_G == (0.10, 0.20, 0.30, 0.50, 0.79) and m.F3_PAIRS == (1, 2)
    assert m.F4_SIGMAS == (0.5, 1.0, 1.5)
    assert m.DEVELOPMENT_SEEDS == (20260709, 20260710, 20260711)
    assert m.HELDOUT_SEEDS == (20260712, 20260713)
    assert set(m.DEVELOPMENT_SEEDS).isdisjoint(m.HELDOUT_SEEDS)
    assert m.DEVELOPMENT_TARGETS == ("winder_sp0.5", "winder_sp1.0", "winder_sp2.0", "winder_ph0.00", "winder_ph1.57")
    assert m.HELDOUT_TARGETS == ("winder_ph3.14", "winder_r0.7", "winder_r0.5")
    assert set(m.DEVELOPMENT_TARGETS).isdisjoint(m.HELDOUT_TARGETS)
    # F3 increments are a subset of the frozen v0.3 outback increment set
    frozen_outback = {0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.79}
    assert set(m.F3_G) <= frozen_outback
    # targets are frozen v0.3 winders
    wk = set(v3._winders().keys())
    assert set(m.DEVELOPMENT_TARGETS) | set(m.HELDOUT_TARGETS) <= wk


def test_sealed_evaluation_count_is_283():
    assert len(m.candidates(m.DEVELOPMENT_SEEDS)) == 38
    assert len(m.candidates(m.HELDOUT_SEEDS)) == 31
    r = m.run()
    assert r["n_dev_evaluations"] == 190          # 5 x 38
    assert r["n_heldout_evaluations"] == 93        # 3 x 31
    assert r["n_total_evaluations"] == 283 == r["sealed_total_evaluations"]
    # only the five sealed families appear
    assert {c["family"] for c in m.candidates(m.DEVELOPMENT_SEEDS)} == set(m.FAMILIES)


# ---- PSC < PSC_FLOOR is the SOLE non-structure feasibility constraint ----
def test_psc_below_floor_is_sole_feasibility(monkeypatch):
    # AIC must not matter: PSC below floor is feasible regardless of AIC; PSC >= floor is infeasible regardless of AIC
    monkeypatch.setattr(m, "_feat", lambda gen: _clean_feat(0.29, aic=0.00))
    feat, feasible, _ = m._safe_feat(lambda: None)
    assert feasible is True
    monkeypatch.setattr(m, "_feat", lambda gen: _clean_feat(0.29, aic=0.99))
    _, feasible, _ = m._safe_feat(lambda: None)
    assert feasible is True
    monkeypatch.setattr(m, "_feat", lambda gen: _clean_feat(0.31, aic=0.99))
    _, feasible, reason = m._safe_feat(lambda: None)
    assert feasible is False and "PSC>=PSC_FLOOR" in reason


# ---- selection objective = proxy_match_residual + feasibility ONLY ----
def test_selection_is_min_residual_over_feasible_only():
    assert m.MATCH_SELECTION_FIELDS == ("proxy_match_residual", "feasible")
    per, _ = m._search_phase(m.HELDOUT_TARGETS, m.HELDOUT_SEEDS)
    for t in m.HELDOUT_TARGETS:
        rows = per[t]["rows"]
        feas = [row["proxy_match_residual"] for row in rows
                if row["feasible"] and row["proxy_match_residual"] is not None]
        if feas:
            assert per[t]["best_residual"] == min(feas)   # exactly argmin residual among feasible; no other objective


def test_no_decision_or_baseline_objective_in_search_selection():
    # the search-phase selection must not consult evaluator/baseline/label/S_best_threshold scores
    src = open(SRC, encoding="utf-8").read()
    search_fn = src.split("def _search_phase", 1)[1].split("\ndef ", 1)[0]
    for forbidden in ("color_ba", "S_best_threshold", "balanced_accuracy", "_group_sep_ba",
                      "_color_predict", "label_accuracy", "evaluator_ba"):
        assert forbidden not in search_fn, forbidden


# ---- single-shot held-out ----
def test_heldout_single_shot():
    r1 = m.run()
    r2 = m.run()
    assert r1["n_heldout_evaluations"] == 93 and r2["n_heldout_evaluations"] == 93   # deterministic, evaluated once
    assert r1["heldout_baseline_audit"]["matched_targets"] == r2["heldout_baseline_audit"]["matched_targets"]
    # held-out audit uses only held-out targets
    assert set(r1["heldout_baseline_audit"]["matched_targets"]) <= set(m.HELDOUT_TARGETS)
    # each held-out target evaluated exactly the sealed grid once
    per, n = m._search_phase(m.HELDOUT_TARGETS, m.HELDOUT_SEEDS)
    assert n == 93
    for t in m.HELDOUT_TARGETS:
        assert per[t]["n_candidates"] == 31


# ---- NaN / non-finite / extreme values can never pass ----
def test_is_clean_rejects_nonfinite_and_extreme():
    assert m._is_clean(0.05) is True
    assert m._is_clean(float("nan")) is False
    assert m._is_clean(float("inf")) is False
    assert m._is_clean(-float("inf")) is False
    assert m._is_clean(m.EXTREME_VALUE_CAP * 10) is False     # extreme-quantized artifact excluded


def test_nonfinite_cannot_be_feasible_or_match(monkeypatch):
    # non-finite PSC -> infeasible
    monkeypatch.setattr(m, "_feat", lambda gen: _clean_feat(float("nan")))
    _, feasible, reason = m._safe_feat(lambda: None)
    assert feasible is False and "nonfinite_or_extreme_PSC" in reason
    # non-finite matched stat -> infeasible
    bad = _clean_feat(0.10)
    bad["by_std"] = float("inf")
    monkeypatch.setattr(m, "_feat", lambda gen: bad)
    _, feasible, reason = m._safe_feat(lambda: None)
    assert feasible is False and "nonfinite_or_extreme_stat" in reason
    # non-finite in residual -> +inf (cannot match)
    tgt = _clean_feat(1.0)
    cand = _clean_feat(0.10)
    cand["rg_std"] = float("nan")
    assert math.isinf(m._residual(cand, tgt))


def test_generator_exception_is_invalid_not_pass(monkeypatch):
    def boom(gen):
        raise ValueError("synthetic")
    monkeypatch.setattr(m, "_feat", boom)
    feat, feasible, reason = m._safe_feat(lambda: None)
    assert feat is None and feasible is False and reason.startswith("exception:")


# ---- claim locks / verdict / outcome ----
def test_claim_locks_and_verdict_hold():
    r = m.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False and r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False and r["integration_readiness_claim"] is False
    assert r["learning"] is False and r["reporting_only"] is True


def test_outcome_is_one_of_four():
    r = m.run()
    head = r["outcome"].split(":", 1)[0]
    assert head in {"Match_feasible", "Match_infeasible", "Partial", "Invalid_protocol_breach"}


def test_no_recurrence_or_temporal_features():
    src = open(SRC, encoding="utf-8").read().lower()
    for tok in ("recurrence", "arrow_of_time", "time_reversed", "laminarity", "rqa", "diagonal_length"):
        assert tok not in src, tok
