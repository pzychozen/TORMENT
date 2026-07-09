"""BV residual sufficiency audit v0.6a (offline research; form A; NON-LEARNING; NOT vision).

EXPLANATORY, NOT corrective. It audits whether the v0.4d group-level residual / TOL closure metric (per-pair
L-inf over the ten matched statistics <= TOL) can COEXIST with feature-level class separability, and whether the
surviving baseline separability (v0.5a) is best explained by metric insufficiency, small-N optimism, both, or is
inconclusive. It reuses the frozen v0.3 and the v0.4d / v0.5a records BY IDENTITY (the exact sealed matched
held-out pairs and frozen best-threshold BA); it reruns nothing with new parameters, replaces no sealed
candidate, changes no v0.4d matched pair, adds no generator family, invents no threshold, REDEFINES NO TOL,
proposes no pass/fail rule change, and adds NO classifier (form B) / neural encoder (form C).

It is REPORTING-ONLY: it optimizes nothing (no decision score, no PSC/AIC balanced accuracy, no classifier
score, no S_best_threshold, no label accuracy, no held-out performance, no post-hoc shortcut metric) and never
tunes toward closing the baselines. Spectral stays audit-note-only and is not reopened. NaN / non-finite /
extreme-quantized values are defensively excluded and can never become evidence. Claim locks stay False and the
frozen Brainvision verdict stays HOLD under every outcome.

The distinction between metric insufficiency and small-N optimism uses a PARAMETER-FREE separability lens: the
between-class rank-separation gap versus the within-class spread (ratio to the natural boundary 1.0 = "gap
equals within-class variation"). This is a DESCRIPTIVE robustness reference derived from the data's own scale;
it is NOT an adopted pass/fail threshold and is applied to NO closure decision. No "tiny" signed-median-diff
cutoff and no BA-saturation cutoff are introduced: BA-saturated features are identified structurally (BA
saturates at its ceiling iff the winder-set is rank-separated from the candidate-set) and are reported ordered
by the continuous signed-median-difference-as-a-fraction-of-TOL.

stdlib + numpy only; reuses only quarantined research surfaces; no torment_service; no runtime / camera /
sensor / live-capture / screen-capture / streaming / prompt / context / memory / action / render-body /
autonomy contact; no real clips.
"""
from __future__ import annotations

import numpy as np

import run_all_shortcuts_closed_synthetic_v0_3 as v3
import run_matched_generative_search_v0_4d as m4d
import run_baseline_anatomy_v0_5a as m5a

# ---- frozen / reused-by-identity surfaces (nothing re-authored, nothing re-thresholded) ----
GROUPS = v3.GROUPS
MATCHED_GROUPS = m4d.MATCHED_GROUPS
TOL = m4d.TOL                                       # 0.0634 (frozen; NOT redefined here)
_best_threshold = v3._best_threshold               # frozen best-threshold BA (reused by identity)
_is_clean = m4d._is_clean                          # frozen defensive value check
EXTREME_VALUE_CAP = m4d.EXTREME_VALUE_CAP           # frozen extreme-artifact bound (reused, not new)
_matched_pairs = m5a._matched_pairs                # reuse v0.5a's reuse/verify of the sealed v0.4d pairs

OUTCOME_LABELS = ("residual_metric_insufficient", "small_n_baseline_optimism",
                  "mixed_metric_and_small_n", "audit_inconclusive")


def _feature_audit(win, cand, s):
    """Reporting-only per-feature audit relating per-pair residual closeness to class-level separability."""
    wv = [float(f[s]) for f in win]
    cv = [float(f[s]) for f in cand]
    if not (wv and cv and all(_is_clean(v) for v in wv + cv)):
        return {"feature": s, "invalid_nonfinite": True}
    wa = np.array(wv, float); ca = np.array(cv, float)
    y = [1] * len(wv) + [0] * len(cv)
    ba = round(float(_best_threshold(wv + cv, y)), 4)
    smd = float(np.median(wa) - np.median(ca))
    pair_delta = np.abs(wa - ca)                                    # per matched pair |winder - candidate| on s
    # class-level rank separation (winder-set fully above/below candidate-set)
    if wa.min() > ca.max():
        rank_sep, gap, direction = True, float(wa.min() - ca.max()), "winder_high"
    elif ca.min() > wa.max():
        rank_sep, gap, direction = True, float(ca.min() - wa.max()), "candidate_high"
    else:
        rank_sep, gap, direction = False, None, "overlap"
    within_spread = float(max(wa.max() - wa.min(), ca.max() - ca.min()))
    # PARAMETER-FREE robustness lens: gap vs within-class spread (boundary 1.0). An effectively-zero within-class
    # spread (numerical noise) makes the ratio extreme; per the defensive rule that is bounded and treated as
    # "robust_constant_within_class", NOT reported as a huge (near-infinite) ratio or as stronger evidence.
    if not rank_sep:
        robustness, gap_over_spread = "not_rank_separated", None
    else:
        ratio = (gap / within_spread) if within_spread > 0.0 else float("inf")
        if within_spread <= 0.0 or (not _is_clean(ratio)) or ratio > EXTREME_VALUE_CAP:
            robustness, gap_over_spread = "robust_constant_within_class", None
        elif ratio >= 1.0:
            robustness, gap_over_spread = "robust", round(ratio, 4)
        else:
            robustness, gap_over_spread = "fragile", round(ratio, 4)
    metric_insufficiency = bool(rank_sep and robustness in ("robust", "robust_constant_within_class"))
    small_n_optimism = bool(rank_sep and robustness == "fragile")
    return {"feature": s, "invalid_nonfinite": False, "best_threshold_BA": ba, "signed_median_diff": round(smd, 6),
            "pair_delta_max": round(float(pair_delta.max()), 6), "pair_delta_median": round(float(np.median(pair_delta)), 6),
            "pair_deltas_all_within_TOL": bool(np.all(pair_delta <= TOL)),
            "rank_separated": rank_sep, "separation_gap": (round(gap, 6) if gap is not None else None),
            "within_class_spread": round(within_spread, 6), "gap_over_within_spread": gap_over_spread,
            "direction": direction, "robustness": robustness,
            "metric_insufficiency_signature": metric_insufficiency, "small_n_optimism_signature": small_n_optimism,
            "smd_as_fraction_of_TOL": round(abs(smd) / TOL, 4)}


def run():
    win, cand, matched_targets, per_pair, breaches = _matched_pairs()
    if len(matched_targets) != 3:
        breaches.append("matched_target_count=%d!=3" % len(matched_targets))

    per_group = {}
    any_nonfinite = False
    for g in MATCHED_GROUPS:
        rows = [_feature_audit(win, cand, s) for s in GROUPS[g]]
        if any(r["invalid_nonfinite"] for r in rows):
            any_nonfinite = True
        per_group[g] = rows

    valid_feats = [r for g in MATCHED_GROUPS for r in per_group[g] if not r["invalid_nonfinite"]]
    metric_insuff = [(r["feature"]) for r in valid_feats if r["metric_insufficiency_signature"]]
    small_n = [(r["feature"]) for r in valid_feats if r["small_n_optimism_signature"]]
    rank_sep_feats = [r["feature"] for r in valid_feats if r["rank_separated"]]
    # BA saturates at its ceiling (1.0) IFF the feature is rank-separated (structural, threshold-free);
    # report those features ordered by signed-median-diff as a fraction of TOL (ascending). No cutoff.
    saturated_ba_features_by_smd_fraction = sorted(
        [(r["feature"], r["smd_as_fraction_of_TOL"]) for r in valid_feats if r["rank_separated"]],
        key=lambda kv: kv[1])

    per_pair_all_within_tol = bool(matched_targets) and all(per_pair[t] <= TOL for t in matched_targets)
    # answer to the core audit question:
    residual_closeness_coexists_with_separability = bool(per_pair_all_within_tol and len(rank_sep_feats) > 0)

    # outcome (research-only; leaves claim locks unchanged)
    if breaches or any_nonfinite:
        outcome = "audit_inconclusive: " + "; ".join(breaches + (["nonfinite_feature_values"] if any_nonfinite else []))
        outcome_label = "audit_inconclusive"
    elif metric_insuff and small_n:
        outcome_label = "mixed_metric_and_small_n"
        outcome = ("mixed_metric_and_small_n: robust class separation the per-pair L-inf<=TOL did not close "
                   "(metric insufficiency, features=%s) COEXISTS with fragile thin-margin separations "
                   "(small-N optimism, features=%s)" % (metric_insuff, small_n))
    elif metric_insuff:
        outcome_label = "residual_metric_insufficient"
        outcome = "residual_metric_insufficient: robust class separation survives per-pair L-inf<=TOL (features=%s)" % metric_insuff
    elif small_n:
        outcome_label = "small_n_baseline_optimism"
        outcome = "small_n_baseline_optimism: rank separations are fragile thin-margin (features=%s)" % small_n
    else:
        outcome_label = "audit_inconclusive"
        outcome = "audit_inconclusive: no rank-separated features to attribute"

    protocol_ok = (len(breaches) == 0 and not any_nonfinite)
    return {"diagnostic": "v0.6a residual sufficiency audit (form A, NON-LEARNING; EXPLANATORY-only; reuses "
                          "v0.4d/v0.5a records + frozen v0.3 by identity; reporting-only)",
            "model_form": "A_non_learning_reporting", "learning": False, "explanatory_only": True,
            "audit_question": "can group-level residual/TOL closure coexist with feature-level separability?",
            "inspected_groups": list(MATCHED_GROUPS), "spectral_role": "audit-note-only (NOT reopened)",
            "TOL": TOL, "TOL_redefined": False, "new_threshold_introduced": False,
            "robustness_lens": "between-class rank gap vs within-class spread (boundary 1.0); descriptive, NOT a pass/fail threshold",
            "matched_targets": matched_targets, "per_pair_residual": {t: round(per_pair[t], 6) for t in matched_targets},
            "per_pair_all_within_tol": per_pair_all_within_tol,
            "residual_closeness_coexists_with_separability": residual_closeness_coexists_with_separability,
            "per_group": per_group,
            "metric_insufficiency_features": metric_insuff, "small_n_optimism_features": small_n,
            "saturated_ba_features_by_smd_fraction": saturated_ba_features_by_smd_fraction,
            "rank_separated_features": rank_sep_feats,
            "small_n_caveat": "n=%d vs %d; best-threshold BA saturates on thin margins" % (len(win), len(cand)),
            "protocol_ok": protocol_ok, "breaches": breaches,
            "outcome_label": outcome_label, "outcome": outcome, "reporting_only": True,
            "frozen_brainvision_verdict": "HOLD",
            "first_pass_structure_validity_claim_allowed": False, "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
            "integration_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| explanatory_only", r["explanatory_only"], "| TOL", r["TOL"], "(redefined=%s)" % r["TOL_redefined"])
    print("audit question:", r["audit_question"])
    print("matched targets:", r["matched_targets"], "| per-pair residual:", r["per_pair_residual"], "| all<=TOL:", r["per_pair_all_within_tol"])
    print("residual closeness COEXISTS with feature-level separability:", r["residual_closeness_coexists_with_separability"])
    print()
    for g in r["inspected_groups"]:
        print("== %s" % g)
        for f in r["per_group"][g]:
            if f["invalid_nonfinite"]:
                print("     %-24s INVALID/non-finite (excluded)" % f["feature"]); continue
            print("     %-24s BA=%.3f smd=%+.5f (%.0f%% TOL) rank_sep=%s robustness=%-26s gap/spread=%s"
                  % (f["feature"], f["best_threshold_BA"], f["signed_median_diff"], 100 * f["smd_as_fraction_of_TOL"],
                     f["rank_separated"], f["robustness"], f["gap_over_within_spread"]))
    print()
    print("metric_insufficiency_features:", r["metric_insufficiency_features"])
    print("small_n_optimism_features    :", r["small_n_optimism_features"])
    print("saturated_ba_features_by_smd_fraction (ascending; smallest = small-N):", r["saturated_ba_features_by_smd_fraction"])
    print("small_n_caveat:", r["small_n_caveat"])
    print()
    print("OUTCOME_LABEL:", r["outcome_label"])
    print("OUTCOME:", r["outcome"])
    print("protocol_ok:", r["protocol_ok"], r["breaches"])
    print("verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"], r["descriptor_validity_claim_allowed"])
