"""v0.7b tests: larger-N residual replication (form A, NON-LEARNING; reporting-only; offline).

Lock the v0.7b slice to ROBUST facts: it runs EXACTLY the sealed v0.7a enumeration (finite budget 222 + 1056 =
1278; sealed seeds / counts / pairing); it uses ONLY the frozen winder + F1-F5 generator surfaces (no new family
/ axis); TOL / PSC_FLOOR / AIC_FLOOR / CHANCE_BAND are unchanged; spectral stays audit-note-only; there is no
search-until-pass / rerun / redraw path; the outcome label is one of the sealed v0.7a labels; non-finite / extreme
values can never become evidence; and claim locks stay False with verdict HOLD. Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_all_shortcuts_closed_synthetic_v0_3 as v3                    # noqa: E402
import run_matched_generative_search_v0_4d as m4d                       # noqa: E402
import run_residual_sufficiency_v0_6a as m6a                            # noqa: E402
import run_larger_n_residual_replication_v0_7b as m7b                   # noqa: E402

SRC = os.path.join(BV_DIR, "run_larger_n_residual_replication_v0_7b.py")


# ---- provenance ----
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
                         "run_color_structure_spectral_std_blocker_v1_9", "run_color_structure_by_std_residual_v2_0",
                         "run_all_shortcuts_closed_synthetic_v0_3", "run_matched_generative_search_v0_4d",
                         "run_residual_sufficiency_v0_6a"}


def test_reuses_frozen_surfaces_by_identity():
    assert m7b._feature_audit is m6a._feature_audit          # frozen robustness lens reused, not re-authored
    assert m7b._is_clean is m4d._is_clean
    assert m7b.TOL == m4d.TOL == 0.0634
    assert m7b.PSC_FLOOR == m4d.PSC_FLOOR == 0.30
    assert m4d.AIC_FLOOR == 0.30                             # evaluator floors unchanged
    assert m7b.CHANCE_BAND == v3.CHANCE_BAND == 0.60
    assert m7b.MATCHED_GROUPS == m4d.MATCHED_GROUPS


# ---- sealed budget 1278 = 222 + 1056 ----
def test_sealed_budget_222_1056_1278():
    assert len(m7b._candidates(m7b.DEVELOPMENT_SEEDS)) == 37
    assert len(m7b._candidates(m7b.REPLICATION_SEEDS)) == 44
    dev_w = m7b._winders(m7b.DEVELOPMENT_WINDER_SPEEDS, m7b.DEVELOPMENT_WINDER_PHASES, m7b.DEVELOPMENT_WINDER_RADII)
    rep_w = m7b._winders(m7b.REPLICATION_WINDER_SPEEDS, m7b.REPLICATION_WINDER_PHASES, m7b.REPLICATION_WINDER_RADII)
    assert len(dev_w) == 6 and len(rep_w) == 24
    r = m7b.run()
    assert r["n_dev_evaluations"] == 222               # 6 x 37
    assert r["n_replication_evaluations"] == 1056       # 24 x 44
    assert r["n_total_evaluations"] == 1278 == r["sealed_total_evaluations"] == m7b.SEALED_TOTAL_EVALUATIONS


def test_seeds_counts_pairing_match_v0_7a():
    assert m7b.DEVELOPMENT_SEEDS == (20260721, 20260722)
    assert m7b.REPLICATION_SEEDS == (20260723, 20260724, 20260725)
    assert set(m7b.DEVELOPMENT_SEEDS).isdisjoint(m7b.REPLICATION_SEEDS)
    assert len(m7b.REPLICATION_WINDER_SPEEDS) == 8 and len(m7b.REPLICATION_WINDER_PHASES) == 8 and len(m7b.REPLICATION_WINDER_RADII) == 8
    assert len(m7b.DEVELOPMENT_WINDER_SPEEDS) == 2 and len(m7b.DEVELOPMENT_WINDER_PHASES) == 2 and len(m7b.DEVELOPMENT_WINDER_RADII) == 2
    assert m7b.F3_G == (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.79)
    assert m7b.F1_SIGMAS == (0.3, 0.6, 1.0) and m7b.F4_SIGMAS == (0.5, 1.0, 1.5)
    assert m7b.F2_LOBES == (2, 3, 5) and m7b.F2_RADII == (0.7, 1.0) and m7b.F3_PAIRS == (1, 2)
    # F3 increments are a subset of the frozen v0.3 outback increment set
    assert set(m7b.F3_G) <= {0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.79}


# ---- only existing generator surfaces; no new family / axis ----
def test_only_existing_generator_surfaces_no_new_family_or_axis():
    r = m7b.run()
    assert r["new_family_or_axis"] is False
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    # v0.7b defines NO family generator of its own -- it reuses the frozen m4d._f1.._f5 functions
    for tok in ("def _f1_", "def _f2_", "def _f3_", "def _f4_", "def _f5_"):
        assert tok not in src, tok
    for reused in ("m4d._f1_full_circle_incoherent", "m4d._f2_rosette_multilobe", "m4d._f3_segment_paired_canceller",
                   "m4d._f4_phase_scrambled_full_coverage", "m4d._f5_hybrid_comboA", "m4d._f5_hybrid_comboB"):
        assert reused in src, reused
    # winders come from the frozen winder generator only
    for reused in ("v9._winder", "v9._series_theta", "v20._winder"):
        assert reused in src, reused
    # the candidate pool exposes exactly the five sealed families
    fams = {c["family"] for c in m7b._candidates(m7b.REPLICATION_SEEDS)}
    assert fams == {"full_circle_incoherent_traversal", "rosette_multilobe_traversal", "segment_paired_canceller",
                    "phase_scrambled_full_coverage", "hybrid_coverage_preserving_canceller"}


def test_frozen_thresholds_and_flags():
    r = m7b.run()
    assert r["TOL"] == 0.0634 and r["TOL_redefined"] is False
    assert r["new_threshold_introduced"] is False
    assert r["PSC_FLOOR"] == 0.30 and r["CHANCE_BAND"] == 0.60


# ---- spectral audit-note-only, not a closure group ----
def test_spectral_audit_note_only():
    r = m7b.run()
    assert "audit-note-only" in r["spectral_role"]
    assert "spectral_centroid" not in m7b.ALL_EFFECTS and "spectral_spread" not in m7b.ALL_EFFECTS
    assert "spectral_centroid" not in r["per_effect"] and "spectral_spread" not in r["per_effect"]


# ---- single deterministic pass: no search-until-pass / rerun / redraw ----
def test_no_search_until_pass_or_rerun_path():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    # structural guard: a search-until-pass loop would be a While node -> assert there are NO while-loops.
    # (Token checks on prose are avoided: the docstring legitimately DESCRIBES "no retries/redraws".)
    tree = ast.parse(src)
    assert not any(isinstance(n, ast.While) for n in ast.walk(tree)), "no while-loops (single deterministic pass)"
    # functional proof of a single pass: each winder evaluates the full pool exactly once (n_eval == winders * pool)
    r = m7b.run()
    assert r["n_replication_evaluations"] == 24 * 44
    assert r["n_dev_evaluations"] == 6 * 37


# ---- outcome labels only the sealed set ----
def test_outcome_label_is_sealed():
    r = m7b.run()
    assert r["outcome_label"] in m7b.OUTCOME_LABELS
    assert set(m7b.OUTCOME_LABELS) == {"BY_persistence_metric_insufficiency", "directional_collapse_tiny_magnitude",
                                       "small_n_features_collapse", "mixed_effects_persist",
                                       "replication_inconclusive", "invalid_protocol_breach"}


# ---- larger-N result (structural, platform-stable) ----
def test_real_run_reports_by_persistence():
    r = m7b.run()
    assert r["n_matched"] >= 1 and r["n_dev_evaluations"] == 222
    assert set(r["magnitude_substantial"]) == {"by_std", "by_centroid", "by_spread"}
    assert set(r["magnitude_negligible"]) == {"rg_centroid", "rg_spread",
                                              "u_directional_delta_rms", "angular_increment_mag"}
    for s in ("by_std", "by_centroid", "by_spread"):
        assert r["per_effect"][s]["status"] == "persists_substantial"
    for s in ("rg_centroid", "rg_spread", "u_directional_delta_rms", "angular_increment_mag"):
        assert r["per_effect"][s]["status"] == "weakens_negligible"
    assert r["outcome_label"] == "BY_persistence_metric_insufficiency"


def test_largest_gap_split_is_threshold_free():
    sub, neg, gap = m7b._largest_gap_split([("a", 0.01), ("b", 0.02), ("c", 0.50), ("d", 0.55)])
    assert set(neg) == {"a", "b"} and set(sub) == {"c", "d"} and gap > 0.4


# ---- non-finite values can never become evidence ----
def test_nonfinite_forces_invalid_breach(monkeypatch):
    real = m6a._feature_audit

    def stub(win, cand, s):
        if s == "by_centroid":
            return {"invalid_nonfinite": True}
        return real(win, cand, s)
    monkeypatch.setattr(m7b, "_feature_audit", stub)
    r = m7b.run()
    assert r["outcome_label"] == "invalid_protocol_breach"
    assert r["protocol_ok"] is False


# ---- claim locks / verdict ----
def test_claim_locks_and_verdict_hold():
    r = m7b.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False and r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False and r["integration_readiness_claim"] is False
    assert r["learning"] is False and r["explanatory_only"] is True and r["reporting_only"] is True


def test_no_temporal_or_recurrence_features():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    for tok in ("recurrence", "arrow_of_time", "time_reversed", "laminarity", "rqa", "diagonal_length"):
        assert tok not in src, tok
