"""BV baseline anatomy diagnostic v0.5a (offline research; form A; NON-LEARNING; NOT vision).

EXPLANATORY, NOT corrective. It explains why the v0.4d matched generative search
(docs: ..._FINDINGS_v0.4d / ..._SYNTHESIS_v0.4e) remained Partial by decomposing the surviving cheap-baseline
separability into PER-FEATURE anatomy, on the EXACT v0.4d matched held-out pairs. It reuses the frozen v0.3 /
v0.8 and the v0.4d search surfaces BY IDENTITY; it reruns nothing with new parameters, replaces no sealed
candidate, changes no v0.4d matched pair, adds no generator family, invents no threshold, and does NOT redefine
TOL. It is REPORTING-ONLY: it optimizes nothing (no decision score, no PSC/AIC balanced accuracy, no classifier
score, no S_best_threshold, no label accuracy, no held-out performance, no post-hoc shortcut metric) and never
tunes toward closing the baselines. It adds NO classifier (form B) / neural encoder (form C).

It inspects ONLY the four frozen MATCHED groups (movement_channel_energy, directional, per_channel, frame_diff);
spectral stays audit-note-only / ill-defined on constant chroma and is NOT reopened as a closure group. NaN /
non-finite / extreme-quantized feature values are defensively excluded and can never become evidence. Claim
locks stay False and the frozen Brainvision verdict stays HOLD under every outcome.

stdlib + numpy only; reuses only quarantined research surfaces; no torment_service; no runtime / camera /
sensor / live-capture / screen-capture / streaming / prompt / context / memory / action / render-body /
autonomy contact; no real clips.
"""
from __future__ import annotations

import numpy as np

import run_all_shortcuts_closed_synthetic_v0_3 as v3
import run_matched_generative_search_v0_4d as m4d

# ---- frozen / reused-by-identity surfaces (nothing re-authored, nothing re-thresholded) ----
GROUPS = v3.GROUPS
MATCHED_GROUPS = m4d.MATCHED_GROUPS                 # movement_channel_energy, directional, per_channel, frame_diff
TOL = m4d.TOL                                       # 0.0634 (frozen; NOT redefined here)
SEP_REFERENCE = m4d.CHANCE_BAND                     # 0.60 reused ONLY as a descriptive "still-separating" reference
_best_threshold = v3._best_threshold               # frozen best-threshold BA (reused by identity)
_is_clean = m4d._is_clean                          # frozen defensive value check (NaN / inf / |x|>cap -> not clean)

# v0.4d sealed matched held-out pairs (committed 77ed133): reused/preserved, verified below (NOT recomputed anew)
V0_4D_EXPECTED = {
    "winder_ph3.14": ("segment_paired_canceller|increment_g=0.2,pairs=1|seed=None", 0.045046),
    "winder_r0.7":   ("segment_paired_canceller|increment_g=0.2,pairs=1|seed=None", 0.036),
    "winder_r0.5":   ("segment_paired_canceller|increment_g=0.2,pairs=2|seed=None", 0.06),
}


def _matched_pairs():
    """Reuse the EXACT v0.4d sealed held-out search (deterministic; same seeds/targets/grid) and verify it
    reproduces the committed v0.4d matched pairs. Returns (winder_feats, candidate_feats, matched_targets,
    per_pair_residual, breaches)."""
    per, n_eval = m4d._search_phase(m4d.HELDOUT_TARGETS, m4d.HELDOUT_SEEDS)
    breaches = []
    if n_eval != 93:
        breaches.append("heldout_eval_count=%d!=93" % n_eval)
    matched_targets, win, cand, per_pair = [], [], [], {}
    for t in m4d.HELDOUT_TARGETS:
        d = per[t]
        exp_id, exp_res = V0_4D_EXPECTED[t]
        if not d["matched"]:
            breaches.append("target_not_matched:%s" % t)
            continue
        if d["best_cand_id"] != exp_id or abs(float(d["best_residual"]) - exp_res) > 1e-6:
            breaches.append("pair_mismatch:%s(%s,%s)" % (t, d["best_cand_id"], d["best_residual"]))
        matched_targets.append(t)
        win.append(m4d._target_feat(t))
        cand.append(d["_best_feat"])
        per_pair[t] = float(d["best_residual"])
    return win, cand, matched_targets, per_pair, breaches


def _feature_anatomy(win, cand, group):
    """Per-feature reporting-only anatomy for one group. Non-clean values are excluded and flagged (never
    evidence)."""
    y = [1] * len(win) + [0] * len(cand)
    rows = []
    for s in GROUPS[group]:
        wv = [float(f[s]) for f in win]
        cv = [float(f[s]) for f in cand]
        clean = bool(wv) and bool(cv) and all(_is_clean(v) for v in wv + cv)
        if not clean:
            rows.append({"feature": s, "invalid_nonfinite": True, "best_threshold_BA": None,
                         "signed_median_diff": None, "winder_median": None, "candidate_median": None,
                         "separates": False})
            continue
        ba = round(float(_best_threshold(wv + cv, y)), 4)
        wmed = float(np.median(wv))
        cmed = float(np.median(cv))
        rows.append({"feature": s, "invalid_nonfinite": False, "best_threshold_BA": ba,
                     "signed_median_diff": round(wmed - cmed, 6),
                     "winder_median": round(wmed, 6), "candidate_median": round(cmed, 6),
                     "separates": bool(ba > SEP_REFERENCE)})
    valid = [r for r in rows if not r["invalid_nonfinite"]]
    group_max = max((r["best_threshold_BA"] for r in valid), default=0.0)
    sep = [r["feature"] for r in valid if r["separates"]]
    carriers = [r["feature"] for r in valid if r["best_threshold_BA"] == group_max]
    ba_rank = [r["feature"] for r in sorted(valid, key=lambda r: -r["best_threshold_BA"])]
    eff_rank = [r["feature"] for r in sorted(valid, key=lambda r: -abs(r["signed_median_diff"]))]
    n_feat = len(GROUPS[group])
    # concentration: for a multi-feature group, is separability carried by ONE feature or MANY?
    if n_feat > 1:
        concentration = "concentrated" if len(sep) <= 1 else "distributed"
    else:
        concentration = "single_feature_group"
    return {"features": rows, "group_max_BA": round(float(group_max), 4), "n_features": n_feat,
            "separating_features": sep, "n_separating": len(sep), "carriers_of_group_max": carriers,
            "ba_ranking": ba_rank, "effect_size_ranking": eff_rank, "concentration": concentration,
            "any_nonfinite": any(r["invalid_nonfinite"] for r in rows)}


def run():
    win, cand, matched_targets, per_pair, breaches = _matched_pairs()
    if len(matched_targets) != 3:
        breaches.append("matched_target_count=%d!=3" % len(matched_targets))

    anatomy = {g: _feature_anatomy(win, cand, g) for g in MATCHED_GROUPS}

    # cross-group effect-size ranking (which features carry the largest class-level difference)
    all_feat = []
    for g in MATCHED_GROUPS:
        for r in anatomy[g]["features"]:
            if not r["invalid_nonfinite"]:
                all_feat.append((g, r["feature"], r["best_threshold_BA"], abs(r["signed_median_diff"])))
    top_by_effect = [(g, s) for g, s, _ba, _e in sorted(all_feat, key=lambda x: -x[3])[:5]]
    top_by_ba = [(g, s) for g, s, ba, _e in sorted(all_feat, key=lambda x: -x[2])[:5]]

    # protocol-metric-mismatch flag: per-pair L-inf <= TOL held for ALL matched pairs, yet a group still
    # separates at class level (best-threshold BA > reference). Reporting flag only; not a threshold.
    per_pair_all_within_tol = bool(matched_targets) and all(per_pair[t] <= TOL for t in matched_targets)
    any_group_separates = any(anatomy[g]["group_max_BA"] > SEP_REFERENCE for g in MATCHED_GROUPS)
    protocol_metric_mismatch_flag = bool(per_pair_all_within_tol and any_group_separates)

    # concentration verdict across MULTI-feature groups that separate
    multi = [g for g in MATCHED_GROUPS if anatomy[g]["n_features"] > 1 and anatomy[g]["group_max_BA"] > SEP_REFERENCE]
    n_distributed = sum(anatomy[g]["concentration"] == "distributed" for g in multi)
    n_concentrated = sum(anatomy[g]["concentration"] == "concentrated" for g in multi)

    any_nonfinite = any(anatomy[g]["any_nonfinite"] for g in MATCHED_GROUPS)
    if breaches or any_nonfinite:
        outcome = "invalid_diagnostic_breach: " + "; ".join(breaches + (["nonfinite_feature_values"] if any_nonfinite else []))
    elif not multi:
        outcome = "protocol_metric_mismatch"                       # nothing multi-feature separates -> mismatch only
    elif n_distributed > n_concentrated:
        outcome = "distributed_residual_geometry"
    elif n_concentrated > n_distributed:
        outcome = "concentrated_residual_feature"
    else:
        outcome = "protocol_metric_mismatch"

    protocol_ok = (len(breaches) == 0 and not any_nonfinite)
    return {"diagnostic": "v0.5a baseline anatomy (form A, NON-LEARNING; EXPLANATORY-only; reuses v0.4d matched "
                          "held-out pairs + frozen v0.3/v0.8 by identity; reporting-only)",
            "model_form": "A_non_learning_reporting", "learning": False, "explanatory_only": True,
            "inspected_groups": list(MATCHED_GROUPS), "spectral_role": "audit-note-only (NOT a closure group)",
            "TOL": TOL, "separation_reference_CHANCE_BAND": SEP_REFERENCE,
            "matched_targets": matched_targets, "n_winders": len(win), "n_candidates": len(cand),
            "per_pair_residual": {t: round(per_pair[t], 6) for t in matched_targets},
            "per_pair_all_within_tol": per_pair_all_within_tol,
            "anatomy": anatomy,
            "top_features_by_effect_size": top_by_effect, "top_features_by_BA": top_by_ba,
            "protocol_metric_mismatch_flag": protocol_metric_mismatch_flag,
            "small_n_caveat": ("best-threshold BA saturates easily at n=%d vs %d; BA near 1.0 with tiny "
                               "signed_median_diff indicates small-N optimism, not a large class-level gap"
                               % (len(win), len(cand))),
            "n_distributed_multi_groups": n_distributed, "n_concentrated_multi_groups": n_concentrated,
            "protocol_ok": protocol_ok, "breaches": breaches, "outcome": outcome, "reporting_only": True,
            "frozen_brainvision_verdict": "HOLD",
            "first_pass_structure_validity_claim_allowed": False, "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
            "integration_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| explanatory_only", r["explanatory_only"], "| learning", r["learning"])
    print("inspected groups:", r["inspected_groups"], "| spectral:", r["spectral_role"])
    print("matched targets:", r["matched_targets"], "| classes: winders=%d cand=%d" % (r["n_winders"], r["n_candidates"]))
    print("per-pair residual (all <= TOL=%.4f): %s -> %s" % (r["TOL"], r["per_pair_residual"], r["per_pair_all_within_tol"]))
    print()
    for g in r["inspected_groups"]:
        a = r["anatomy"][g]
        print("== %-24s group_max_BA=%.4f  concentration=%s  separating=%s" %
              (g, a["group_max_BA"], a["concentration"], a["separating_features"]))
        for f in a["features"]:
            if f["invalid_nonfinite"]:
                print("     %-24s INVALID/non-finite (excluded, not evidence)" % f["feature"])
            else:
                print("     %-24s BA=%.4f  signed_med_diff=%+.5f  separates=%s" %
                      (f["feature"], f["best_threshold_BA"], f["signed_median_diff"], f["separates"]))
    print()
    print("top features by EFFECT SIZE :", r["top_features_by_effect_size"])
    print("top features by BA          :", r["top_features_by_BA"])
    print("protocol_metric_mismatch_flag:", r["protocol_metric_mismatch_flag"])
    print("small_n_caveat:", r["small_n_caveat"])
    print("multi-group concentration: distributed=%d concentrated=%d" %
          (r["n_distributed_multi_groups"], r["n_concentrated_multi_groups"]))
    print()
    print("OUTCOME:", r["outcome"], "| protocol_ok:", r["protocol_ok"], r["breaches"])
    print("verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"],
          r["descriptor_validity_claim_allowed"])
