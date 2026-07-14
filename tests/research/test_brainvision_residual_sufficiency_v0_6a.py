"""v0.6a tests: residual sufficiency audit (form A, NON-LEARNING; EXPLANATORY-only; offline).

Lock the v0.6a slice to ROBUST facts: it reuses the v0.4d/v0.5a records by identity (no rerun with new params,
no replaced pair, no family/grid/seed change); TOL is unchanged and no new threshold is adopted (actively
guarded); spectral is not reopened; the parameter-free robustness lens (gap vs within-class spread) defensively
bounds extreme ratios and never lets non-finite values become evidence; BA-saturated features are reported
threshold-free (ordered by smd fraction); the outcome is one of the four planned labels; and claim locks stay
False with verdict HOLD. Offline; no torment_service.
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
import run_baseline_anatomy_v0_5a as m5a                                # noqa: E402
import run_residual_sufficiency_v0_6a as m6a                            # noqa: E402

SRC = os.path.join(BV_DIR, "run_residual_sufficiency_v0_6a.py")


def _feats(vals):
    return [{"x": v} for v in vals]


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
    assert set(mods) <= {"numpy", "__future__", "run_all_shortcuts_closed_synthetic_v0_3",
                         "run_matched_generative_search_v0_4d", "run_baseline_anatomy_v0_5a"}


def test_reuses_frozen_and_prior_records_by_identity():
    assert m6a._best_threshold is v3._best_threshold
    assert m6a._is_clean is m4d._is_clean
    assert m6a._matched_pairs is m5a._matched_pairs           # reuses v0.5a's reuse/verify of v0.4d pairs
    assert m6a.GROUPS is v3.GROUPS
    assert m6a.MATCHED_GROUPS == m4d.MATCHED_GROUPS


# ---- TOL unchanged; no new threshold adopted ----
def test_tol_unchanged_no_new_threshold():
    r = m6a.run()
    assert m6a.TOL == m4d.TOL == 0.0634
    assert r["TOL_redefined"] is False
    assert r["new_threshold_introduced"] is False
    # the robustness lens is a descriptive ratio to the NATURAL boundary 1.0 (no invented numeric threshold)
    assert "descriptive" in r["robustness_lens"].lower()
    # actively forbid any unregistered tiny-SMD / BA-saturation cutoff in the source
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    for bad in ("0.1 * TOL", "0.1*TOL", ">= 0.999", ">=0.999", "tiny_smd"):
        assert bad not in src, bad


# ---- only four matched groups; spectral not reopened ----
def test_spectral_not_reopened():
    r = m6a.run()
    assert r["inspected_groups"] == ["movement_channel_energy", "directional", "per_channel", "frame_diff"]
    assert "spectral" not in r["per_group"]
    seen = {f["feature"] for g in r["per_group"].values() for f in g if not f["invalid_nonfinite"]}
    assert "spectral_centroid" not in seen and "spectral_spread" not in seen


# ---- v0.4d candidates/pairs preserved; no generator/family/grid/seed change ----
def test_preserves_v0_4d_pairs_and_envelope():
    r = m6a.run()
    assert r["matched_targets"] == list(m4d.HELDOUT_TARGETS)
    assert r["per_pair_residual"] == {"winder_ph3.14": 0.045046, "winder_r0.7": 0.036, "winder_r0.5": 0.06}
    assert r["per_pair_all_within_tol"] is True and r["protocol_ok"] is True
    # sealed v0.4d enumeration untouched
    assert m4d.F3_G == (0.10, 0.20, 0.30, 0.50, 0.79) and m4d.HELDOUT_SEEDS == (20260712, 20260713)
    assert m4d.HELDOUT_TARGETS == ("winder_ph3.14", "winder_r0.7", "winder_r0.5")
    assert m4d.SEALED_TOTAL_EVALUATIONS == 283
    # v0.6a defines NO generator family of its own
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    for tok in ("def _f1_", "def _f2_", "def _f3_", "def _f4_", "def _f5_", "def candidates("):
        assert tok not in src, tok


# ---- required audit outputs computed ----
def test_required_audit_outputs_present():
    r = m6a.run()
    # per-target residual vs feature-level BA / smd juxtaposed
    assert set(r["per_pair_residual"].keys()) == set(m4d.HELDOUT_TARGETS)
    for g in m4d.MATCHED_GROUPS:
        for f in r["per_group"][g]:
            if f["invalid_nonfinite"]:
                continue
            for k in ("best_threshold_BA", "signed_median_diff", "pair_delta_max", "rank_separated",
                      "robustness", "smd_as_fraction_of_TOL"):
                assert k in f
    assert r["residual_closeness_coexists_with_separability"] is True
    assert isinstance(r["metric_insufficiency_features"], list)
    assert isinstance(r["small_n_optimism_features"], list)
    # threshold-free ordered reporting: rank-separated (BA-saturated) features by smd fraction, ascending
    sat = r["saturated_ba_features_by_smd_fraction"]
    assert isinstance(sat, list) and all(len(t) == 2 for t in sat)
    assert [t[1] for t in sat] == sorted(t[1] for t in sat)          # ascending by smd fraction, no cutoff


# ---- parameter-free robustness lens classification ----
def test_robustness_lens_classifies_gap_vs_spread():
    robust = m6a._feature_audit(_feats([2.0, 2.1, 2.2]), _feats([1.0, 1.1, 1.2]), "x")   # gap 0.8 >> spread 0.2
    assert robust["rank_separated"] and robust["robustness"] == "robust" and robust["metric_insufficiency_signature"]
    fragile = m6a._feature_audit(_feats([2.0, 2.5, 2.9]), _feats([1.0, 1.5, 1.9]), "x")   # gap 0.1 << spread 0.9
    assert fragile["rank_separated"] and fragile["robustness"] == "fragile" and fragile["small_n_optimism_signature"]
    overlap = m6a._feature_audit(_feats([1.0, 2.0, 3.0]), _feats([1.5, 2.5, 3.5]), "x")
    assert overlap["rank_separated"] is False and overlap["robustness"] == "not_rank_separated"
    # effectively-zero within-class spread -> robust_constant, ratio bounded (NOT a huge/inf number)
    const = m6a._feature_audit(_feats([1.0, 1.0, 1.0]), _feats([1.001, 1.001, 1.001]), "x")
    assert const["robustness"] == "robust_constant_within_class" and const["gap_over_within_spread"] is None


def test_real_run_reports_mixed_and_key_features():
    r = m6a.run()
    # by_centroid / by_spread are robustly separated (metric insufficiency); rg_centroid / rg_spread fragile (small-N)
    assert "by_centroid" in r["metric_insufficiency_features"] and "by_spread" in r["metric_insufficiency_features"]
    assert "rg_centroid" in r["small_n_optimism_features"] and "rg_spread" in r["small_n_optimism_features"]
    assert r["metric_insufficiency_features"] and r["small_n_optimism_features"]
    assert r["outcome_label"] == "mixed_metric_and_small_n"


def test_no_reported_value_is_nonfinite_or_extreme():
    r = m6a.run()
    for g in r["inspected_groups"]:
        for f in r["per_group"][g]:
            v = f.get("gap_over_within_spread")
            if v is not None:
                assert m6a._is_clean(v), (g, f["feature"], v)


# ---- non-finite values can never become evidence ----
def test_nonfinite_feature_excluded_and_forces_inconclusive(monkeypatch):
    single = m6a._feature_audit(_feats([1.0, float("nan"), 1.2]), _feats([2.0, 2.1, 2.2]), "x")
    assert single["invalid_nonfinite"] is True
    # inject inf into a real pair -> audit_inconclusive, no claim movement
    orig = m4d._target_feat

    def bad(t):
        d = dict(orig(t))
        d["by_centroid"] = float("inf")
        return d
    monkeypatch.setattr(m4d, "_target_feat", bad)
    r = m6a.run()
    assert r["outcome_label"] == "audit_inconclusive"
    assert r["protocol_ok"] is False


# ---- outcome label is one of four; claim locks / verdict ----
def test_outcome_label_is_one_of_four():
    r = m6a.run()
    assert r["outcome_label"] in m6a.OUTCOME_LABELS
    assert set(m6a.OUTCOME_LABELS) == {"residual_metric_insufficient", "small_n_baseline_optimism",
                                       "mixed_metric_and_small_n", "audit_inconclusive"}


def test_claim_locks_and_verdict_hold():
    r = m6a.run()
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
