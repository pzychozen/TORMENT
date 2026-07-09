"""BV all-shortcuts-closed synthetic falsifier v0.3 (offline research; NOT vision; NON-LEARNING).

Next falsifier after v0.2 (docs: TORMENT_BRAINVISION_OFFLINE_PROTOTYPE_MODEL_SYNTHESIS_v0.2). Form A ONLY: the
SAME fixed frozen color rule (structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR; no label fit, no trained
weights). It asks whether that rule still separates synthetic structure when the cheap-proxy shortcut groups
-- movement/channel-energy, directional, spectral, per-channel, frame-diff -- are matched or neutralized
BETWEEN the two labels SIMULTANEOUSLY, at larger N, with cross-family discipline.

It builds a larger-N synthetic family bank (structure = coherent winders; non-structure = cancellation
trajectories), matches each structure example to the cancellation partner that MINIMIZES the total cheap-proxy
residual, then AUDITS per shortcut group whether the two labels are actually matched (residual + whether a
cheap baseline can still separate the classes). If a group cannot be closed it is reported as an OPEN residual
shortcut and the construction is reported as (fully) INFEASIBLE -- never worked around by weakening a control,
deleting a baseline, inventing a threshold, or changing frozen descriptor logic.

It reuses the frozen v0.7/v0.8 machinery by identity (structure_score / _stats / constants) and the v1.9/v2.0
generators. It changes NO formula, NO §7 anti-proxy logic, NO §8 verdict logic, NO threshold, NO control. The
frozen Brainvision §8 verdict stays HOLD and is untouched. NO learning, NO classifier (form B), NO neural
encoder (form C), NO trained weights, NO label-fitted color threshold, NO recurrence/temporal features
(DET/RR/LAM excluded). `S_best_threshold` (if reported) is OPTIMISTIC / label-fit / DIAGNOSTIC ONLY and is NOT
the fixed model. stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture /
streaming / prompt / context / memory / action / render-body / autonomy contact; no torment_service; no
memory-system integration; no real clips. Brainvision Path B is NOT proven vision and is NOT a functioning
vision layer for TORMENT memory. Beating a baseline is NOT proof of vision, descriptor validity, temporal
order, memory readiness, runtime readiness, or integration readiness.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_color_structure_spectral_std_blocker_v1_9 as v9
import run_color_structure_by_std_residual_v2_0 as v20

structure_score = cs.structure_score
stats = cs._stats
PSC_FLOOR = cs.PSC_FLOOR
AIC_FLOOR = cs.AIC_FLOOR
FULL = v9.FULL
T = cs.T

RANDOM_SEED = 20260708
# Reporting-only shortcut-audit band for describing whether a cheap baseline still separates this synthetic
# family. This is not a §7/§8 threshold, not an acceptance criterion, and cannot move the frozen verdict.
CHANCE_BAND = 0.60                              # a cheap group "cannot separate" if its best-threshold BA <= this

# shortcut groups (cheap proxies) to be matched/neutralized SIMULTANEOUSLY
GROUPS = {
    "movement_channel_energy": ("rg_std", "by_std", "chroma_mag", "delta_rms"),
    "directional": ("u_directional_delta_rms", "angular_increment_mag"),
    "spectral": ("spectral_centroid", "spectral_spread"),
    "per_channel": ("rg_centroid", "by_centroid", "rg_spread", "by_spread"),
    "frame_diff": ("delta_rms",),
}
ALL_PROXIES = tuple(dict.fromkeys(s for g in GROUPS.values() for s in g))


def _feat(gen):
    rg, by, ch = gen()[:3]
    s = structure_score(rg, by, ch)
    d = dict(stats(rg, by, ch))
    d["PSC"] = s["PSC"]; d["AIC"] = s["AIC"]; d["S"] = s["S"]
    d["_chroma_constant"] = bool(np.std(ch) < 1e-6)   # spectral_centroid/spread of a constant chroma = FP noise
    return d


# structure examples: coherent winders (PSC=1) across angular speeds / phases / radii (larger N)
def _winders():
    out = {}
    for sp in (0.5, 1.0, 2.0):
        out["winder_sp%.1f" % sp] = (lambda sp=sp: v9._winder(sp * FULL))
    for ph in (0.0, np.pi / 2, np.pi):
        out["winder_ph%.2f" % ph] = (lambda ph=ph: v9._series_theta(ph + FULL * np.arange(T)))
    for fr in (0.7, 0.5):
        out["winder_r%.1f" % fr] = (lambda fr=fr: v20._winder(fr))
    return out


# cancellation pool (PSC low): out-and-back arcs at many increments (directional match) + full-sweep +
# arc oscillators + collinear. The matcher picks, per winder, the partner minimizing total proxy residual.
def _cancellers():
    out = {}
    for g in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.79):
        out["outback_%.2f" % g] = (lambda g=g: v9._outback(g))
    for delta, k in ((0.3, 1), (0.6, 1), (1.2, 2), (0.8, 3), (1.6, 2)):
        out["arc_%.1f_k%d" % (delta, k)] = (lambda delta=delta, k=k: v9._arc_osc(delta, k))
    for f in (1, 2):
        out["collinear_%d" % f] = (lambda f=f: v9._collinear(f))
    return out


def _linf_residual(a, b):
    return max(abs(a[s] - b[s]) for s in ALL_PROXIES)


def _ba(y, p):
    y = np.asarray(y); p = np.asarray(p)
    P = y == 1; N = y == 0
    tpr = float(np.mean(p[P] == 1)) if P.any() else 0.0
    tnr = float(np.mean(p[N] == 0)) if N.any() else 0.0
    return 0.5 * (tpr + tnr)


def _confusion(y, p):
    y = np.asarray(y); p = np.asarray(p)
    return {"tp": int(np.sum((y == 1) & (p == 1))), "fn": int(np.sum((y == 1) & (p == 0))),
            "fp": int(np.sum((y == 0) & (p == 1))), "tn": int(np.sum((y == 0) & (p == 0)))}


def _best_threshold(vals, y):
    vals = np.asarray(vals, float); y = np.asarray(y)
    uniq = np.unique(vals)
    if uniq.size < 2:
        return 0.5
    best = 0.0
    for t in (uniq[:-1] + uniq[1:]) / 2.0:
        for pred in ((vals >= t).astype(int), (vals < t).astype(int)):
            best = max(best, _ba(y, pred))
    return best


def _group_sep_ba(feats, y, group):
    """Best-threshold BA achievable by the single best feature in the group (optimistic separability)."""
    return round(max(_best_threshold([f[s] for f in feats], y) for s in group), 4)


def _color_predict(feats):
    return np.array([1 if (f["PSC"] >= PSC_FLOOR and f["AIC"] >= AIC_FLOOR) else 0 for f in feats], int)


def run():
    rng = np.random.default_rng(RANDOM_SEED)
    winders = {n: _feat(g) for n, g in _winders().items()}
    cancellers = {n: _feat(g) for n, g in _cancellers().items()}

    # match each winder (structure) to the canceller minimizing the L-inf proxy residual (best-effort closure)
    matched_pairs = []
    for wn, w in winders.items():
        cn, resid = min(((cn, _linf_residual(w, c)) for cn, c in cancellers.items()), key=lambda t: t[1])
        matched_pairs.append({"winder": wn, "canceller": cn, "linf_proxy_residual": round(resid, 4),
                              "per_stat_abs_delta": {s: round(abs(w[s] - cancellers[cn][s]), 4) for s in ALL_PROXIES}})

    used_cancellers = sorted({p["canceller"] for p in matched_pairs})
    feats = [winders[p["winder"]] for p in matched_pairs] + [cancellers[c] for c in used_cancellers]
    y = [1] * len(matched_pairs) + [0] * len(used_cancellers)

    # fixed frozen color rule
    color_pred = _color_predict(feats)
    color_ba = round(_ba(y, color_pred), 4)
    color_conf = _confusion(y, color_pred)

    # shortcut audit: per group, class-centroid residual + whether a cheap baseline still separates the classes
    win_feats = [f for f, yy in zip(feats, y) if yy == 1]
    non_feats = [f for f, yy in zip(feats, y) if yy == 0]
    any_chroma_constant = all(f["_chroma_constant"] for f in feats)
    shortcut_audit = {}
    open_groups = []
    for gname, gstats in GROUPS.items():
        centroid_resid = {s: round(abs(float(np.mean([f[s] for f in win_feats]))
                                       - float(np.mean([f[s] for f in non_feats]))), 4) for s in gstats}
        sep_ba = _group_sep_ba(feats, y, gstats)
        spectral_illdef = bool(gname == "spectral" and any_chroma_constant)
        closed = bool(sep_ba <= CHANCE_BAND) or spectral_illdef
        shortcut_audit[gname] = {"class_centroid_abs_delta": centroid_resid,
                                 "cheap_baseline_separates_BA": sep_ba, "closed": closed,
                                 "note": ("spectral_centroid/spread are FFT-of-constant-chroma numerical noise "
                                          "here -> not meaningfully matchable; treated as not-a-usable-shortcut"
                                          if spectral_illdef else "")}
        if not closed:
            open_groups.append(gname)

    all_shortcuts_closed = (len(open_groups) == 0)

    # cheap baselines over the pooled family (optimistic best-threshold; separability per group)
    baselines = {g: _group_sep_ba(feats, y, gstats) for g, gstats in GROUPS.items()}
    rand_ba = round(_ba(y, rng.integers(0, 2, size=len(y))), 4)
    baselines["random"] = rand_ba
    best_cheap = max(((g, b) for g, b in baselines.items() if g != "random"), key=lambda kv: kv[1])

    # ablations
    psc_only = np.array([1 if f["PSC"] >= PSC_FLOOR else 0 for f in feats], int)
    aic_only = np.array([1 if f["AIC"] >= AIC_FLOOR else 0 for f in feats], int)
    ablations = {"PSC_only_frozen_ba": round(_ba(y, psc_only), 4),
                 "AIC_only_frozen_ba": round(_ba(y, aic_only), 4),
                 "S_best_threshold_ba_OPTIMISTIC_DIAGNOSTIC_ONLY": round(_best_threshold([f["S"] for f in feats], y), 4)}

    # shuffled-label control (avg over many fixed-seed shuffles ~ chance)
    srng = np.random.default_rng(RANDOM_SEED + 1)
    shuf = []
    for _ in range(500):
        sy = np.array(y); srng.shuffle(sy); shuf.append(_ba(sy, color_pred))
    shuffled_control_ba = round(float(np.mean(shuf)), 4)

    # outcome classification (predeclared v0.3 outcomes)
    color_separates = bool(color_ba > 0.9)
    cheap_still_separates = bool(best_cheap[1] > CHANCE_BAND)
    if all_shortcuts_closed and color_separates and not cheap_still_separates:
        outcome = "Outcome_1_all_closed_color_separates_cheap_fails_STRONGER_RESEARCH_SIGNAL_ONLY"
    elif all_shortcuts_closed and cheap_still_separates:
        outcome = "Outcome_2_construction_succeeds_cheap_baselines_still_separate_PROXY_WALL_REMAINS"
    elif (not all_shortcuts_closed):
        outcome = ("Outcome_4_all_shortcuts_closed_construction_INFEASIBLE_residual_shortcut_remains; "
                   "best_effort_family_leaves_open_groups=" + ",".join(open_groups))
    elif not color_separates:
        outcome = "Outcome_3_construction_succeeds_but_fixed_color_rule_FAILS_v0_2_signal_fixture_dependent"
    else:
        outcome = "unresolved"

    research_signal = "unresolved_proxy_wall_remains" if cheap_still_separates or not all_shortcuts_closed \
        else "strengthened_research_signal_only_no_vision_or_validity_claim"

    return {"diagnostic": "v0.3 all-shortcuts-closed synthetic falsifier (form A, NON-LEARNING, reuses frozen "
                          "v0.7/v0.8 + v1.9/v2.0 generators; reporting-only)",
            "model_form": "A_non_learning_scoring", "learning": False,
            "fixed_rule": "structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR (frozen floors; no label fit)",
            "n_structure": len(matched_pairs), "n_nonstructure": len(used_cancellers),
            "matched_pairs": matched_pairs, "used_cancellers": used_cancellers,
            "color_structure_model_ba": color_ba, "color_structure_confusion": color_conf,
            "shortcut_audit": shortcut_audit, "open_residual_shortcut_groups": open_groups,
            "all_shortcuts_closed": all_shortcuts_closed,
            "all_shortcuts_closed_construction_feasible": all_shortcuts_closed,
            "baselines_separability_BA": baselines, "best_cheap_baseline": {"group": best_cheap[0], "ba": best_cheap[1]},
            "cheap_baseline_still_separates": cheap_still_separates,
            "ablations": ablations, "shuffled_label_control_ba": shuffled_control_ba,
            "chroma_constant_family": any_chroma_constant,
            "outcome": outcome, "research_signal": research_signal,
            "frozen_brainvision_verdict": "HOLD", "reporting_only": True,
            "first_pass_structure_validity_claim_allowed": False, "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
            "integration_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| learning", r["learning"])
    print("n_structure", r["n_structure"], "n_nonstructure", r["n_nonstructure"],
          "| color_ba", r["color_structure_model_ba"], "conf", r["color_structure_confusion"])
    print("\nshortcut_audit (closed if cheap baseline BA <= %.2f):" % CHANCE_BAND)
    for g, d in r["shortcut_audit"].items():
        print("  %-24s cheap_sep_BA=%.3f closed=%s %s" % (g, d["cheap_baseline_separates_BA"], d["closed"],
                                                          ("<- " + d["note"]) if d["note"] else ""))
    print("open_residual_shortcut_groups:", r["open_residual_shortcut_groups"])
    print("all_shortcuts_closed:", r["all_shortcuts_closed"])
    print("\nmatched pairs (winder -> best canceller, L-inf proxy residual):")
    for p in r["matched_pairs"]:
        print("  %-14s -> %-14s Linf=%.4f" % (p["winder"], p["canceller"], p["linf_proxy_residual"]))
    print("\nbaselines separability BA:", r["baselines_separability_BA"])
    print("best_cheap_baseline:", r["best_cheap_baseline"], "| cheap_still_separates:", r["cheap_baseline_still_separates"])
    print("ablations:", r["ablations"])
    print("shuffled_label_control_ba (~0.5):", r["shuffled_label_control_ba"], "| chroma_constant_family:", r["chroma_constant_family"])
    print("\nOUTCOME:", r["outcome"])
    print("research_signal:", r["research_signal"])
    print("frozen_brainvision_verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"], r["descriptor_validity_claim_allowed"])
