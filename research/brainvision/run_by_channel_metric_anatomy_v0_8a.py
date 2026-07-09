"""BV BY-channel metric anatomy v0.8a (offline research; form A; NON-LEARNING; NOT vision).

EXPLANATORY, NOT corrective. It explains WHY the BY-channel features (by_centroid, by_spread, by_std) persist as
substantial residual separability after the v0.7b larger-N replication -- it does NOT try to make Brainvision
pass or close BY. It reproduces the v0.7b sealed replication matching BY IDENTITY (same frozen winder + F1-F5
generators, same sealed seeds/counts/pairing, proxy_match_residual, PSC < PSC_FLOOR feasibility, TOL) and
verifies it reproduces the committed v0.7b matched/unmatched sets; it then reports a reporting-only anatomy of
the BY persistence. It reuses the frozen descriptor / GROUPS / best-threshold BA / robustness lens / rank
correlation BY IDENTITY. It adds NO new family, NO new axis, NO new closure metric, invents NO threshold,
REDEFINES NO TOL, changes no evaluator / control, reopens no spectral group, and adds NO classifier (form B) /
neural encoder (form C).

It optimizes NOTHING (no fixed-rule decision score, no PSC/AIC balanced accuracy, no classifier score, no
S_best_threshold, no label accuracy, no held-out performance, no cheap-baseline BA) and never tunes toward a
pass or toward closing BY. NaN / non-finite / extreme-quantized values are defensively excluded and can never
become evidence. Claim locks stay False and the frozen Brainvision verdict stays HOLD under every outcome.

stdlib + numpy only; reuses only quarantined research surfaces; no torment_service; no runtime / camera /
sensor / live-capture / screen-capture / streaming / prompt / context / memory / action / render-body /
autonomy contact; no real clips.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_matched_generative_search_v0_4d as m4d
import run_residual_sufficiency_v0_6a as m6a
import run_larger_n_residual_replication_v0_7b as m7b

# ---- frozen / reused-by-identity surfaces ----
TOL = m7b.TOL                                       # 0.0634 (frozen)
MATCHED_STATS = m4d.MATCHED_STATS
_feature_audit = m6a._feature_audit                # frozen robustness lens
_is_clean = m4d._is_clean
_spearman = cs.g5._spearman                        # frozen rank correlation (reused, not re-authored)

# ---- feature roles (v0.8 plan) ----
BY_FEATURES = ("by_centroid", "by_spread", "by_std")            # PRIMARY target
RG_FEATURES = ("rg_centroid", "rg_spread")                     # comparison
DIRECTIONAL_FEATURES = ("u_directional_delta_rms", "angular_increment_mag")   # comparison
AMPLITUDE_FEATURES = ("chroma_mag", "rg_std")                  # channel-energy / amplitude context for by_std

OUTCOME_LABELS = ("BY_axis_asymmetry", "BY_centroid_spread_coupling", "BY_amplitude_leakage",
                  "BY_family_artifact", "BY_metric_compression", "BY_anatomy_inconclusive",
                  "invalid_protocol_breach")

# v0.7b committed result to reproduce (protocol check; NOT recomputed anew)
V0_7B_MATCHED = 19
V0_7B_UNMATCHED = ("w_sp3.00", "w_sp3.50", "w_r0.4", "w_r0.3", "w_r0.2")


def _region(wn):
    return "speed" if wn.startswith("w_sp") else ("phase" if wn.startswith("w_ph") else "radius")


def _reproduce_replication_pairs():
    """Reproduce the v0.7b sealed replication matching (same enumeration, deterministic) and capture family +
    binding-stat metadata. Returns (pairs, unmatched, n_eval)."""
    winders = m7b._winders(m7b.REPLICATION_WINDER_SPEEDS, m7b.REPLICATION_WINDER_PHASES, m7b.REPLICATION_WINDER_RADII)
    pool = m7b._candidates(m7b.REPLICATION_SEEDS)
    n_eval = 0
    pairs, unmatched = [], []
    for wn, wg in winders.items():
        tfeat = m4d._feat(wg)
        best = None                                                     # (key, cand_feat, family, residual)
        for c in pool:
            n_eval += 1
            feat, feasible, _r = m4d._safe_feat(c["gen"])
            if feasible:
                resid = m4d._residual(feat, tfeat)
                if np.isfinite(resid):
                    key = (resid, (c["seed"] if c["seed"] is not None else -1), c["cand_id"])
                    if best is None or key < best[0]:
                        best = (key, feat, c["family"], resid)
        if best is not None and best[3] <= TOL:
            cf = best[1]
            deltas = {s: abs(float(tfeat[s]) - float(cf[s])) for s in MATCHED_STATS
                      if _is_clean(tfeat.get(s)) and _is_clean(cf.get(s))}
            binding = max(deltas, key=deltas.get) if deltas else None
            pairs.append({"winder": wn, "region": _region(wn), "win_feat": tfeat, "cand_feat": cf,
                          "family": best[2], "residual": best[3], "binding_stat": binding})
        else:
            unmatched.append(wn)
    return pairs, unmatched, n_eval


def _pair_diffs(pairs, s):
    return np.array([float(p["win_feat"][s]) - float(p["cand_feat"][s]) for p in pairs], float)


def run():
    pairs, unmatched, n_eval = _reproduce_replication_pairs()
    n_matched = len(pairs)

    breaches = []
    if n_eval != 1056:
        breaches.append("replication_eval=%d!=1056" % n_eval)
    if n_matched != V0_7B_MATCHED:
        breaches.append("n_matched=%d!=%d(v0.7b)" % (n_matched, V0_7B_MATCHED))
    if tuple(unmatched) != V0_7B_UNMATCHED:
        breaches.append("unmatched!=v0.7b")
    # non-finite guard on all inspected features (checked BEFORE any evidence is computed)
    any_nonfinite = False
    for p in pairs:
        for s in BY_FEATURES + RG_FEATURES + DIRECTIONAL_FEATURES + AMPLITUDE_FEATURES:
            if not (_is_clean(p["win_feat"].get(s)) and _is_clean(p["cand_feat"].get(s))):
                any_nonfinite = True

    clean = (len(breaches) == 0) and (not any_nonfinite)

    # defaults for the breach path -- NO evidence is computed on non-finite / breached data
    by_vs_rg, by_dominant = {}, False
    sign, mean_consistency, asymmetry_score = {}, 0.0, 0.0
    coupling, amp, amplitude_score = None, {}, 0.0
    fam_counts, n_matching_families = {}, 0
    region_by, unmatched_regions, binding_counts = {}, {}, {}
    by_binding_frac, compression_score = 0.0, 0.0
    scores = {}

    if clean:
        win = [p["win_feat"] for p in pairs]
        cand = [p["cand_feat"] for p in pairs]

        # (1) BY vs RG comparison
        def _eff(s):
            a = _feature_audit(win, cand, s)
            return {"BA": a["best_threshold_BA"], "signed_median_diff": a["signed_median_diff"],
                    "abs_effect_frac_TOL": round(a["smd_as_fraction_of_TOL"], 4)}
        by_vs_rg = {s: _eff(s) for s in BY_FEATURES + RG_FEATURES + DIRECTIONAL_FEATURES}
        by_eff = [by_vs_rg[s]["abs_effect_frac_TOL"] for s in BY_FEATURES]
        rg_eff = [by_vs_rg[s]["abs_effect_frac_TOL"] for s in RG_FEATURES]
        by_dominant = bool(min(by_eff) > max(rg_eff))

        # (2) BY signed-difference distributions
        for s in BY_FEATURES:
            d = _pair_diffs(pairs, s)
            pos = float(np.mean(d > 0)); neg = float(np.mean(d < 0))
            sign[s] = {"median_diff": round(float(np.median(d)), 6), "frac_positive": round(pos, 3),
                       "frac_negative": round(neg, 3), "sign_consistency": round(max(pos, neg), 3),
                       "dominant_sign": ("+" if pos >= neg else "-")}
        mean_consistency = float(np.mean([sign[s]["sign_consistency"] for s in BY_FEATURES]))
        asymmetry_score = round(max(0.0, 2.0 * mean_consistency - 1.0), 4)

        # (3) centroid/spread coupling
        coupling = round(abs(float(_spearman(_pair_diffs(pairs, "by_centroid"), _pair_diffs(pairs, "by_spread")))), 4)

        # (4) by_std amplitude leakage
        amp = {a: round(abs(float(_spearman(_pair_diffs(pairs, "by_std"), _pair_diffs(pairs, a)))), 4)
               for a in AMPLITUDE_FEATURES}
        amplitude_score = max(amp.values()) if amp else 0.0

        # (5) family anatomy
        for p in pairs:
            fam_counts[p["family"]] = fam_counts.get(p["family"], 0) + 1
        n_matching_families = len(fam_counts)

        # (6) target-region anatomy
        for reg in ("speed", "phase", "radius"):
            sub = [p for p in pairs if p["region"] == reg]
            if len(sub) >= 2:
                a = _feature_audit([p["win_feat"] for p in sub], [p["cand_feat"] for p in sub], "by_centroid")
                region_by[reg] = {"n": len(sub), "by_centroid_BA": a.get("best_threshold_BA"),
                                  "by_centroid_smd": a.get("signed_median_diff")}
        for wn in unmatched:
            unmatched_regions[_region(wn)] = unmatched_regions.get(_region(wn), 0) + 1

        # (7) residual aggregation
        for p in pairs:
            binding_counts[p["binding_stat"]] = binding_counts.get(p["binding_stat"], 0) + 1
        by_binding = sum(binding_counts.get(s, 0) for s in BY_FEATURES)
        by_binding_frac = round(by_binding / n_matched, 4) if n_matched else 0.0
        by_share = len([s for s in BY_FEATURES if s in MATCHED_STATS]) / len(MATCHED_STATS)
        compression_score = round(max(0.0, by_binding_frac - by_share), 4)

        scores = {"BY_axis_asymmetry": asymmetry_score, "BY_centroid_spread_coupling": coupling,
                  "BY_amplitude_leakage": round(float(amplitude_score), 4), "BY_metric_compression": compression_score}

    # outcome (research-only; leaves claim locks unchanged)
    if not clean:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches + (["nonfinite_feature_values"] if any_nonfinite else []))
    elif not by_dominant:
        outcome_label = "BY_anatomy_inconclusive"
        outcome = "BY_anatomy_inconclusive: BY effects do not dominate RG in these records"
    else:
        best = max(scores, key=scores.get)
        if scores[best] <= 0.0:
            outcome_label = "BY_anatomy_inconclusive"
            outcome = "BY_anatomy_inconclusive: no mechanism score dominates"
        else:
            outcome_label = best
            outcome = "%s: strongest BY-anatomy signal (scores=%s)" % (best, scores)

    protocol_ok = clean
    return {"diagnostic": "v0.8a BY-channel metric anatomy (form A, NON-LEARNING; EXPLANATORY-only; reproduces "
                          "v0.7b replication by identity; reporting-only)",
            "model_form": "A_non_learning_reporting", "learning": False, "explanatory_only": True,
            "core_question": "why do by_centroid / by_spread / by_std persist as substantial residual separability?",
            "TOL": TOL, "TOL_redefined": False, "new_threshold_introduced": False, "new_family_or_axis": False,
            "spectral_role": "audit-note-only (NOT reopened)",
            "n_replication_evaluations": n_eval, "n_matched": n_matched, "n_unmatched": len(unmatched),
            "unmatched_winders": unmatched,
            "reproduces_v0_7b": (n_matched == V0_7B_MATCHED and tuple(unmatched) == V0_7B_UNMATCHED),
            "by_vs_rg": by_vs_rg, "by_dominant_over_rg": by_dominant,
            "by_signed_difference": sign, "mean_by_sign_consistency": round(mean_consistency, 3),
            "centroid_spread_coupling_spearman": coupling,
            "by_std_amplitude_spearman": amp,
            "family_distribution": fam_counts, "n_matching_families": n_matching_families,
            "region_by_persistence": region_by, "unmatched_regions": unmatched_regions,
            "binding_stat_distribution": binding_counts, "by_binding_fraction": by_binding_frac,
            "mechanism_scores": scores, "protocol_ok": protocol_ok, "breaches": breaches,
            "outcome_label": outcome_label, "outcome": outcome, "reporting_only": True,
            "frozen_brainvision_verdict": "HOLD",
            "first_pass_structure_validity_claim_allowed": False, "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
            "integration_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| explanatory_only", r["explanatory_only"], "| TOL", r["TOL"], "(redefined=%s)" % r["TOL_redefined"])
    print("core question:", r["core_question"])
    print("replication evals:", r["n_replication_evaluations"], "| matched:", r["n_matched"], "| unmatched:", r["n_unmatched"],
          "| reproduces v0.7b:", r["reproduces_v0_7b"])
    print()
    print("(1) BY vs RG effect size (|smd|/TOL):  BY_dominant=%s" % r["by_dominant_over_rg"])
    for s in BY_FEATURES + RG_FEATURES + DIRECTIONAL_FEATURES:
        d = r["by_vs_rg"][s]
        print("     %-24s BA=%.3f  effect=%.0f%% TOL" % (s, d["BA"], 100 * d["abs_effect_frac_TOL"]))
    print("(2) BY signed-difference sign consistency (mean=%.3f):" % r["mean_by_sign_consistency"])
    for s in BY_FEATURES:
        d = r["by_signed_difference"][s]
        print("     %-12s dominant %s  consistency=%.2f  median_diff=%+.5f" % (s, d["dominant_sign"], d["sign_consistency"], d["median_diff"]))
    print("(3) centroid/spread coupling spearman:", r["centroid_spread_coupling_spearman"])
    print("(4) by_std ~ amplitude spearman:", r["by_std_amplitude_spearman"])
    print("(5) matched family distribution:", r["family_distribution"], "| n_families:", r["n_matching_families"])
    print("(6) region BY persistence:", r["region_by_persistence"], "| unmatched regions:", r["unmatched_regions"])
    print("(7) binding L-inf stat distribution:", r["binding_stat_distribution"], "| BY-binding frac:", r["by_binding_fraction"])
    print()
    print("mechanism scores:", r["mechanism_scores"])
    print("OUTCOME_LABEL:", r["outcome_label"])
    print("protocol_ok:", r["protocol_ok"], r["breaches"])
    print("verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"], r["descriptor_validity_claim_allowed"])
