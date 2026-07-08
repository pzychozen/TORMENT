"""BV offline prototype scoring probe v0.2 (offline research; NOT vision; NON-LEARNING).

First implementation slice of the accepted v0.1 offline-prototype-model plan
(docs: TORMENT_BRAINVISION_OFFLINE_PROTOTYPE_MODEL_PLAN_v0.1). Form A ONLY: a deterministic, NON-LEARNING
scoring model over synthetic fixtures. It does NOT train weights from labels; it uses a FIXED, explicit
decision rule built from the frozen v0.7/v0.8 descriptor floors, so failures and shortcuts stay visible. It
tests whether the Brainvision color-structure feature family separates synthetic visual-structure tasks better
than cheap baselines, and it is baseline-gated: beating cheap baselines is a research signal ONLY.

It reuses the frozen v0.7/v0.8 machinery by identity (structure_score / _stats / constants) and the v1.9 + v2.0
synthetic fixture generators. It changes NO formula, NO §7 anti-proxy logic, NO §8 verdict logic, NO threshold,
and NO control; it deletes / weakens nothing; it redesigns no descriptor; it invents no acceptance criterion.
The frozen Brainvision §8 verdict stays HOLD and is untouched; this probe has only a separate research-only
signal that moves no lock and no verdict.

NO learning (no label-fit weights). NO neural model. NO classical trained classifier (form B/C are NOT opened
here). NO recurrence / temporal summaries (DET/RR/LAM excluded to avoid temporal leakage). stdlib + numpy only;
no service imports; no runtime / camera / live-capture / screen-capture / streaming / prompt / context / memory
/ action / render-body / autonomy contact; no torment_service; no memory-system integration; no real clips.
Brainvision Path B is NOT proven vision and is NOT a functioning vision layer for TORMENT memory. Beating a
baseline is NOT proof of vision, descriptor validity, temporal order, memory readiness, or runtime readiness.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_color_structure_spectral_std_blocker_v1_9 as v9
import run_color_structure_by_std_residual_v2_0 as v20

# frozen surfaces reused verbatim (NOT redefined)
structure_score = cs.structure_score
stats = cs._stats
PSC_FLOOR = cs.PSC_FLOOR
AIC_FLOOR = cs.AIC_FLOOR
FULL = v9.FULL

RANDOM_SEED = 20260708         # fixed seed for the random baseline (determinism)

# feature families (frozen descriptor meanings only; recurrence/temporal DELIBERATELY excluded)
COLOR_STRUCTURE = ("PSC", "AIC", "S")
DIRECTIONAL = ("u_directional_delta_rms", "angular_increment_mag")
PER_CHANNEL = ("rg_centroid", "by_centroid", "rg_spread", "by_spread")
# cheap-baseline feature groups
BASELINE_GROUPS = {
    "movement_only": ("rg_std", "by_std", "chroma_mag"),
    "direction_only": ("u_directional_delta_rms", "angular_increment_mag"),
    "spectral_only": ("spectral_centroid", "spectral_spread"),
    "per_channel_only": ("rg_centroid", "by_centroid", "rg_spread", "by_spread"),
    "frame_diff_proxy": ("delta_rms",),
}


def _feat(gen):
    rg, by, ch = gen()[:3]
    s = structure_score(rg, by, ch)
    d = dict(stats(rg, by, ch))
    d["PSC"] = s["PSC"]; d["AIC"] = s["AIC"]; d["S"] = s["S"]
    return d


# --- PREDECLARED synthetic task families (label 1 = coherent-winding structure; 0 = cancellation) ---
# winders (label 1): all coherent winders -> PSC=1 by construction
_W = {
    "w_full": lambda: v9._winder(FULL), "w_2x": lambda: v9._winder(2 * FULL),
    "w_half": lambda: v9._winder(0.5 * FULL), "w_frac07": lambda: v20._winder(0.7),
    "w_frac05": lambda: v20._winder(0.5),
    "w_phase": lambda: v9._series_theta(np.pi + FULL * np.arange(cs.T)),
}
# cancellers (label 0): winding cancels -> PSC low
_C = {
    "arc_1.2_k2": lambda: v9._arc_osc(1.2, 2), "arc_0.8_k3": lambda: v9._arc_osc(0.8, 3),
    "arc_0.3_k1": lambda: v9._arc_osc(0.3, 1), "arc_0.4_k1": lambda: v9._arc_osc(0.4, 1),
    "arc_0.6_k1": lambda: v9._arc_osc(0.6, 1), "collinear_1": lambda: v9._collinear(1),
    "collinear_2": lambda: v9._collinear(2), "outback_0.10": lambda: v9._outback(0.10),
    "outback_0.20": lambda: v9._outback(0.20), "outback_0.40": lambda: v9._outback(0.40),
}
FAMILIES = {
    # F1: unmatched -> cheap features may separate (easy)
    "F1_unmatched": (["w_full", "w_2x", "w_half", "w_frac07"],
                     ["arc_1.2_k2", "arc_0.8_k3", "collinear_1", "outback_0.40"]),
    # F2: movement-matched -> movement/frame-diff features struggle
    "F2_movement_matched": (["w_full", "w_half", "w_frac07"],
                            ["outback_0.20", "outback_0.10", "outback_0.40"]),
    # F3: per-channel centroid/spread-matched (non-collinear) -> spectral/per-channel features struggle
    "F3_perchannel_matched": (["w_full", "w_frac05", "w_frac07"],
                              ["arc_0.3_k1", "arc_0.4_k1", "arc_0.6_k1"]),
    # F4: smoothness-without-winding -> movement AND spectral features struggle
    "F4_smoothness": (["w_full", "w_half"],
                      ["arc_0.3_k1", "arc_0.4_k1", "outback_0.10"]),
    # F5: channel-energy-matched (rg_std/by_std/chroma_mag matched) -> the movement/energy shortcut is CLOSED,
    # but NOT all cheap shortcuts: directional or spectral proxies may still separate this family.
    # Full-amplitude winders vs std-matched cancellers.
    "F5_std_matched": (["w_full", "w_2x", "w_phase"],
                       ["collinear_1", "collinear_2", "outback_0.40"]),
}


def _samples(fam):
    win, non = FAMILIES[fam]
    xs = [(_feat(_W[w]), 1) for w in win] + [(_feat(_C[c]), 0) for c in non]
    return xs


def _ba(y_true, y_pred):
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    P = (y_true == 1); N = (y_true == 0)
    tpr = float(np.mean(y_pred[P] == 1)) if P.any() else 0.0
    tnr = float(np.mean(y_pred[N] == 0)) if N.any() else 0.0
    return 0.5 * (tpr + tnr)


def _confusion(y_true, y_pred):
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    return {"tp": int(np.sum((y_true == 1) & (y_pred == 1))),
            "fn": int(np.sum((y_true == 1) & (y_pred == 0))),
            "fp": int(np.sum((y_true == 0) & (y_pred == 1))),
            "tn": int(np.sum((y_true == 0) & (y_pred == 0)))}


def _best_threshold(fvals, y):
    """Best balanced accuracy over all midpoint thresholds and both directions. This is an OPTIMISTIC upper
    bound (the threshold is chosen with knowledge of the eval labels) -- it is generous to the cheap baselines,
    so that a NON-LEARNING frozen rule beating it is a strong result. Returns (best_ba, threshold, direction)."""
    fvals = np.asarray(fvals, float); y = np.asarray(y)
    uniq = np.unique(fvals)
    if uniq.size < 2:
        return 0.5, None, "ge"
    cands = (uniq[:-1] + uniq[1:]) / 2.0
    best = (0.0, None, "ge")
    for t in cands:
        for direction in ("ge", "lt"):
            pred = (fvals >= t).astype(int) if direction == "ge" else (fvals < t).astype(int)
            b = _ba(y, pred)
            if b > best[0]:
                best = (b, float(t), direction)
    return best


def _apply_threshold(fvals, t, direction):
    fvals = np.asarray(fvals, float)
    if t is None:
        return np.zeros(fvals.size, int)
    return (fvals >= t).astype(int) if direction == "ge" else (fvals < t).astype(int)


# --- the NON-LEARNING color-structure model: FIXED frozen-floor rule (no label fit) ---
def _color_structure_predict(feats):
    """FIXED rule reusing the frozen PSC/AIC floors: predict 'structure' iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR.
    No weights, no thresholds tuned from labels -- fully interpretable and falsifiable."""
    return np.array([1 if (f["PSC"] >= PSC_FLOOR and f["AIC"] >= AIC_FLOOR) else 0 for f in feats], int)


def _group_best_ba(feats, y, group_feats):
    """Best-threshold BA over a feature group = max over its features (optimistic)."""
    best = (0.0, None, "ge", None)
    for name in group_feats:
        vals = [f[name] for f in feats]
        b, t, d = _best_threshold(vals, y)
        if b > best[0]:
            best = (b, t, d, name)
    return {"balanced_accuracy": round(best[0], 4), "best_feature": best[3],
            "threshold": (round(best[1], 4) if best[1] is not None else None), "direction": best[2]}


def run():
    rng = np.random.default_rng(RANDOM_SEED)
    fam_names = list(FAMILIES)
    per_family = {}
    pooled_feats, pooled_y = [], []
    for fam in fam_names:
        xs = _samples(fam)
        feats = [f for f, _y in xs]; y = [yy for _f, yy in xs]
        pooled_feats += feats; pooled_y += y

        # non-learning color-structure model (frozen rule)
        cs_pred = _color_structure_predict(feats)
        cs_ba = _ba(y, cs_pred); cs_conf = _confusion(y, cs_pred)

        # cheap baselines (optimistic best-threshold)
        baselines = {g: _group_best_ba(feats, y, gf) for g, gf in BASELINE_GROUPS.items()}
        rand_pred = rng.integers(0, 2, size=len(y))
        baselines["random"] = {"balanced_accuracy": round(_ba(y, rand_pred), 4), "best_feature": None,
                               "threshold": None, "direction": None}

        # ablations of the color-structure family (frozen-rule variants + best-threshold of S)
        psc_only = np.array([1 if f["PSC"] >= PSC_FLOOR else 0 for f in feats], int)
        aic_only = np.array([1 if f["AIC"] >= AIC_FLOOR else 0 for f in feats], int)
        s_bt = _best_threshold([f["S"] for f in feats], y)
        ablations = {"PSC_only_frozen_ba": round(_ba(y, psc_only), 4),
                     "AIC_only_frozen_ba": round(_ba(y, aic_only), 4),
                     "S_best_threshold_ba": round(s_bt[0], 4)}

        best_cheap = max(baselines.items(), key=lambda kv: kv[1]["balanced_accuracy"])
        per_family[fam] = {
            "n_structure": int(sum(y)), "n_nonstructure": int(len(y) - sum(y)),
            "color_structure_model_ba": round(cs_ba, 4), "color_structure_confusion": cs_conf,
            "baselines": baselines, "ablations": ablations,
            "best_cheap_baseline": {"name": best_cheap[0], "ba": best_cheap[1]["balanced_accuracy"]},
            "color_beats_best_cheap": bool(cs_ba > best_cheap[1]["balanced_accuracy"]),
            "shortcut_present": bool(best_cheap[1]["balanced_accuracy"] >= cs_ba - 1e-9
                                     and best_cheap[0] != "random")}

    # pooled
    cs_pred_p = _color_structure_predict(pooled_feats)
    pooled = {"n": len(pooled_y), "color_structure_model_ba": round(_ba(pooled_y, cs_pred_p), 4),
              "color_structure_confusion": _confusion(pooled_y, cs_pred_p),
              "baselines": {g: _group_best_ba(pooled_feats, pooled_y, gf) for g, gf in BASELINE_GROUPS.items()}}

    # cross-family generalization: choose each baseline group's best threshold on the REFERENCE family (F1),
    # then apply it UNCHANGED to the held-out families. The non-learning color rule needs no reference.
    ref = "F1_unmatched"
    ref_xs = _samples(ref); ref_feats = [f for f, _y in ref_xs]; ref_y = [yy for _f, yy in ref_xs]
    cross = {}
    for fam in fam_names:
        if fam == ref:
            continue
        xs = _samples(fam); feats = [f for f, _y in xs]; y = [yy for _f, yy in xs]
        row = {"color_structure_model_ba": round(_ba(y, _color_structure_predict(feats)), 4), "baselines": {}}
        for g, gf in BASELINE_GROUPS.items():
            # pick best single feature+threshold on ref, apply to held-out fam
            best = (0.0, None, "ge", None)
            for name in gf:
                b, t, d = _best_threshold([f[name] for f in ref_feats], ref_y)
                if b > best[0]:
                    best = (b, t, d, name)
            preds = _apply_threshold([f[best[3]] for f in feats], best[1], best[2]) if best[3] else np.zeros(len(y), int)
            row["baselines"][g] = {"held_out_ba": round(_ba(y, preds), 4), "ref_feature": best[3]}
        cross[fam] = row

    # shuffled-label control (sanity): the frozen rule should collapse to ~chance on shuffled labels.
    # Average balanced accuracy over many fixed-seed shuffles for a stable estimate (~0.5 expected).
    srng = np.random.default_rng(RANDOM_SEED + 1)
    shuf_bas = []
    for _ in range(500):
        sy = np.array(pooled_y); srng.shuffle(sy)
        shuf_bas.append(_ba(sy, cs_pred_p))
    shuffled_control_ba = round(float(np.mean(shuf_bas)), 4)

    # research-only signal (NON-authorizing): does the frozen color rule beat the best cheap baseline where it
    # matters (the matched families)? This is a RESEARCH signal only; it moves no lock and no verdict.
    # PRIMARY evidence = cross-family generalization (threshold learned on the reference family, applied
    # unchanged to held-out families). This is the RELIABLE test: the within-family best-threshold BA is an
    # optimistic upper bound that OVERFITS tiny N (it can perfectly separate ~1e-3 feature differences on 3-vs-3
    # samples), so it is reported but NOT used to decide shortcut vs advantage.
    held_out = [f for f in fam_names if f != ref]
    # per held-out family: does SOME cheap baseline (cross-family) match the color rule?
    each_family_separable_by_some_cheap = True
    for fam in held_out:
        best_cross = max(cross[fam]["baselines"].values(), key=lambda b: b["held_out_ba"])["held_out_ba"]
        if best_cross < cross[fam]["color_structure_model_ba"] - 1e-9:
            each_family_separable_by_some_cheap = False
    # does any SINGLE cheap baseline generalize (cross-family) across ALL held-out families?
    any_single_cheap_generalizes_all = False
    for g in BASELINE_GROUPS:
        worst = min(cross[fam]["baselines"][g]["held_out_ba"] for fam in held_out)
        if worst >= 1.0 - 1e-9:
            any_single_cheap_generalizes_all = True
    color_single_rule_generalizes_all = all(
        per_family[f]["color_structure_model_ba"] >= 1.0 - 1e-9 for f in fam_names)

    if color_single_rule_generalizes_all and not any_single_cheap_generalizes_all and each_family_separable_by_some_cheap:
        research_signal = ("color_structure_single_fixed_rule_generalizes_across_all_families; "
                           "no_single_cheap_baseline_does; but_each_family_also_separable_by_some_cheap_baseline; "
                           "research_signal_only_no_vision_or_validity_claim")
    elif color_single_rule_generalizes_all and not each_family_separable_by_some_cheap:
        research_signal = ("color_structure_separates_a_family_no_cheap_baseline_generalizes_to; "
                           "research_signal_only_no_vision_or_validity_claim")
    elif any_single_cheap_generalizes_all:
        research_signal = "cheap_baseline_generalizes_across_all_families_no_demonstrated_color_advantage"
    else:
        research_signal = "mixed_or_no_clear_advantage"

    cross_family_summary = {
        "reference_family": ref, "held_out_families": held_out,
        "each_family_separable_by_some_cheap_baseline": bool(each_family_separable_by_some_cheap),
        "any_single_cheap_baseline_generalizes_across_all_held_out": bool(any_single_cheap_generalizes_all),
        "color_single_fixed_rule_generalizes_across_all_families": bool(color_single_rule_generalizes_all),
        "small_sample_caveat": ("within-family best-threshold BA is an optimistic upper bound that overfits "
                                "tiny N; cross-family generalization is the reliable comparison")}

    return {"diagnostic": "v0.2 offline prototype scoring probe (form A, NON-LEARNING, reuses frozen v0.7/v0.8 + "
                          "v1.9/v2.0 generators; reporting-only)",
            "model_form": "A_non_learning_scoring", "learning": False,
            "fixed_rule": "structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR (frozen floors; no label fit)",
            "feature_families": {"color_structure": list(COLOR_STRUCTURE), "directional": list(DIRECTIONAL),
                                 "per_channel_spectral": list(PER_CHANNEL),
                                 "recurrence_temporal_excluded": True},
            "task_families": fam_names, "per_family": per_family, "pooled": pooled,
            "cross_family_generalization": cross, "cross_family_summary": cross_family_summary,
            "shuffled_label_control_ba": shuffled_control_ba,
            "random_seed": RANDOM_SEED, "research_signal": research_signal,
            "frozen_brainvision_verdict": "HOLD",
            "reporting_only": True,
            "first_pass_structure_validity_claim_allowed": False,
            "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| learning", r["learning"], "| research_signal", r["research_signal"])
    print("fixed_rule:", r["fixed_rule"])
    print("\nper-family (color-structure frozen rule vs best cheap baseline):")
    for fam, d in r["per_family"].items():
        print("  %-24s n=%d/%d  color_ba=%.3f  best_cheap=%s(%.3f)  color_beats=%s  shortcut=%s"
              % (fam, d["n_structure"], d["n_nonstructure"], d["color_structure_model_ba"],
                 d["best_cheap_baseline"]["name"], d["best_cheap_baseline"]["ba"],
                 d["color_beats_best_cheap"], d["shortcut_present"]))
    print("\n  per-family baseline detail (best-threshold BA, optimistic):")
    for fam, d in r["per_family"].items():
        print("   %-24s " % fam + " ".join("%s=%.3f" % (g, b["balanced_accuracy"]) for g, b in d["baselines"].items()))
    print("\n  ablations (color-structure family):")
    for fam, d in r["per_family"].items():
        print("   %-24s %s" % (fam, d["ablations"]))
    print("\npooled color_ba=%.3f conf=%s" % (r["pooled"]["color_structure_model_ba"], r["pooled"]["color_structure_confusion"]))
    print("pooled baselines:", {g: b["balanced_accuracy"] for g, b in r["pooled"]["baselines"].items()})
    print("\ncross-family generalization (baseline threshold chosen on F1, applied held-out):")
    for fam, d in r["cross_family_generalization"].items():
        print("   %-24s color_ba=%.3f  baselines_heldout=%s" % (fam, d["color_structure_model_ba"],
              {g: b["held_out_ba"] for g, b in d["baselines"].items()}))
    print("\ncross_family_summary:", r["cross_family_summary"])
    print("shuffled_label_control_ba (expect ~0.5):", r["shuffled_label_control_ba"])
    print("frozen_brainvision_verdict:", r["frozen_brainvision_verdict"],
          "| first_pass", r["first_pass_structure_validity_claim_allowed"],
          "| temporal", r["temporal_claim_allowed"], "| descriptor_validity", r["descriptor_validity_claim_allowed"])
