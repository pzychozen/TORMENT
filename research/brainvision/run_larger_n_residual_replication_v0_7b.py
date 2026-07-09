"""BV larger-N residual replication v0.7b (offline research; form A; NON-LEARNING; NOT vision).

EXPLANATORY / reporting-only. It runs EXACTLY the sealed v0.7a enumeration
(docs: ..._LARGER_N_RESIDUAL_REPLICATION_ENUMERATION_v0.7a) to test which v0.6a separability effects survive at
larger sample support. It reuses the frozen v0.3 / v0.8 / v1.9 / v2.0 and the v0.4d / v0.5a / v0.6a surfaces BY
IDENTITY (winder + F1-F5 generators, proxy_match_residual, PSC < PSC_FLOOR feasibility, TOL, descriptor / GROUPS
/ best-threshold BA, robustness lens). It adds NO new family, NO new axis, NO new closure metric, invents NO
threshold, REDEFINES NO TOL, changes no evaluator / control, reopens no spectral group, and adds NO classifier
(form B) / neural encoder (form C).

It optimizes NOTHING (no fixed-rule decision score, no PSC/AIC balanced accuracy, no classifier score, no
S_best_threshold, no label accuracy, no held-out performance, no cheap-baseline BA) and never tunes toward a
pass. It runs the fixed sealed enumeration ONCE (222 development + 1056 replication = 1278 evaluations; no
restarts / retries / redraws / replacements; no search-until-pass). NaN / non-finite / extreme-quantized values
are defensively excluded and can never become evidence. Claim locks stay False and the frozen Brainvision
verdict stays HOLD under every outcome.

stdlib + numpy only; reuses only quarantined research surfaces; no torment_service; no runtime / camera /
sensor / live-capture / screen-capture / streaming / prompt / context / memory / action / render-body /
autonomy contact; no real clips.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_color_structure_spectral_std_blocker_v1_9 as v9
import run_color_structure_by_std_residual_v2_0 as v20
import run_all_shortcuts_closed_synthetic_v0_3 as v3
import run_matched_generative_search_v0_4d as m4d
import run_residual_sufficiency_v0_6a as m6a

# ---- frozen / reused-by-identity surfaces ----
T = cs.T
FULL = v9.FULL
TOL = m4d.TOL                                       # 0.0634 (frozen)
PSC_FLOOR = m4d.PSC_FLOOR                           # 0.30 (frozen)
CHANCE_BAND = v3.CHANCE_BAND                        # 0.60 (frozen; used only as a descriptive separability floor)
MATCHED_GROUPS = m4d.MATCHED_GROUPS
_feature_audit = m6a._feature_audit                # frozen robustness lens (rank gap vs within-class spread)
_is_clean = m4d._is_clean

# ---- sealed v0.7a enumeration (numbers from the committed enumeration doc; not re-derived) ----
REPLICATION_WINDER_SPEEDS = (0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5)
REPLICATION_WINDER_PHASES = tuple(k * np.pi / 4 for k in range(8))          # 0, pi/4, ... 7pi/4
REPLICATION_WINDER_RADII = (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2)
DEVELOPMENT_WINDER_SPEEDS = (0.6, 1.25)
DEVELOPMENT_WINDER_PHASES = (np.pi / 8, 9 * np.pi / 8)
DEVELOPMENT_WINDER_RADII = (0.85, 0.35)
F1_SIGMAS = (0.3, 0.6, 1.0)
F2_LOBES = (2, 3, 5)
F2_RADII = (0.7, 1.0)
F3_G = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.79)     # all eight FROZEN v0.3 outback increments (within-axis)
F3_PAIRS = (1, 2)
F4_SIGMAS = (0.5, 1.0, 1.5)
DEVELOPMENT_SEEDS = (20260721, 20260722)
REPLICATION_SEEDS = (20260723, 20260724, 20260725)
SEALED_TOTAL_EVALUATIONS = 1278                    # 6*37 + 24*44 = 222 + 1056

EFFECTS_A_BY = ("by_centroid", "by_spread")
EFFECTS_B_DIRECTIONAL = ("u_directional_delta_rms", "angular_increment_mag")
EFFECTS_C_SMALL_N = ("by_std", "rg_centroid", "rg_spread")
ALL_EFFECTS = EFFECTS_A_BY + EFFECTS_B_DIRECTIONAL + EFFECTS_C_SMALL_N

OUTCOME_LABELS = ("BY_persistence_metric_insufficiency", "directional_collapse_tiny_magnitude",
                  "small_n_features_collapse", "mixed_effects_persist", "replication_inconclusive",
                  "invalid_protocol_breach")


def _winders(speeds, phases, radii):
    """More instances of the FROZEN winder generator (same generator, more parameter points). No new family."""
    out = {}
    for sp in speeds:
        out["w_sp%.2f" % sp] = (lambda sp=sp: v9._winder(sp * FULL))
    for i, ph in enumerate(phases):
        out["w_ph%d" % i] = (lambda ph=ph: v9._series_theta(ph + FULL * np.arange(T)))
    for fr in radii:
        out["w_r%.1f" % fr] = (lambda fr=fr: v20._winder(fr))
    return out


def _candidates(seed_pool):
    """Existing F1-F5 families at v0.7a within-axis instances (reuses m4d generator functions by identity)."""
    out = []

    def add(fam, params, seed, gen):
        cid = "%s|%s|seed=%s" % (fam, ",".join("%s=%s" % (k, params[k]) for k in sorted(params)), seed)
        out.append({"family": fam, "seed": seed, "cand_id": cid, "gen": gen})

    for sg in F1_SIGMAS:
        for sd in seed_pool:
            add("full_circle_incoherent_traversal", {"sigma": sg}, sd,
                (lambda sg=sg, sd=sd: m4d._f1_full_circle_incoherent(sg, sd)))
    for lb in F2_LOBES:
        for rf in F2_RADII:
            add("rosette_multilobe_traversal", {"lobes": lb, "radius_frac": rf}, None,
                (lambda lb=lb, rf=rf: m4d._f2_rosette_multilobe(lb, rf)))
    for g in F3_G:
        for pr in F3_PAIRS:
            add("segment_paired_canceller", {"increment_g": g, "pairs": pr}, None,
                (lambda g=g, pr=pr: m4d._f3_segment_paired_canceller(g, pr)))
    for sg in F4_SIGMAS:
        for sd in seed_pool:
            add("phase_scrambled_full_coverage", {"sigma": sg}, sd,
                (lambda sg=sg, sd=sd: m4d._f4_phase_scrambled_full_coverage(sg, sd)))
    add("hybrid_coverage_preserving_canceller", {"combo": "A"}, None, m4d._f5_hybrid_comboA)
    for sd in seed_pool:
        add("hybrid_coverage_preserving_canceller", {"combo": "B"}, sd, (lambda sd=sd: m4d._f5_hybrid_comboB(sd)))
    return out


def _match_phase(winder_dict, cand_pool):
    """Single deterministic pass: each winder -> min proxy_match_residual FEASIBLE candidate; matched iff <= TOL.
    No search-until-pass, no restarts/retries/redraws/replacements."""
    n_eval = 0
    win_feats, cand_feats, matched, unmatched = [], [], [], []
    for wn, wg in winder_dict.items():
        tfeat = m4d._feat(wg)
        best = None                                                     # (key, cand_feat, residual)
        for c in cand_pool:
            n_eval += 1
            feat, feasible, _reason = m4d._safe_feat(c["gen"])
            if feasible:
                resid = m4d._residual(feat, tfeat)
                if np.isfinite(resid):
                    key = (resid, (c["seed"] if c["seed"] is not None else -1), c["cand_id"])
                    if best is None or key < best[0]:
                        best = (key, feat, resid)
        if best is not None and best[2] <= TOL:
            matched.append(wn); win_feats.append(tfeat); cand_feats.append(best[1])
        else:
            unmatched.append(wn)
    return {"win_feats": win_feats, "cand_feats": cand_feats, "matched": matched, "unmatched": unmatched,
            "n_eval": n_eval}


def _largest_gap_split(pairs):
    """Threshold-free 1-D magnitude clustering: split the effect-size-ordered list at its single LARGEST gap.
    Returns (substantial_features, negligible_features, gap). Descriptive; NOT a fixed cutoff."""
    if len(pairs) < 2:
        return [p[0] for p in pairs], [], 0.0
    ordered = sorted(pairs, key=lambda p: p[1])                          # ascending by |smd|/TOL
    gaps = [(ordered[i + 1][1] - ordered[i][1], i) for i in range(len(ordered) - 1)]
    gap, idx = max(gaps, key=lambda g: g[0])
    negligible = [ordered[i][0] for i in range(idx + 1)]
    substantial = [ordered[i][0] for i in range(idx + 1, len(ordered))]
    return substantial, negligible, round(float(gap), 4)


def run():
    dev = _match_phase(_winders(DEVELOPMENT_WINDER_SPEEDS, DEVELOPMENT_WINDER_PHASES, DEVELOPMENT_WINDER_RADII),
                       _candidates(DEVELOPMENT_SEEDS))
    rep = _match_phase(_winders(REPLICATION_WINDER_SPEEDS, REPLICATION_WINDER_PHASES, REPLICATION_WINDER_RADII),
                       _candidates(REPLICATION_SEEDS))
    n_total = dev["n_eval"] + rep["n_eval"]

    # audit runs on REPLICATION matched pairs (single-shot); development is construction-only
    win, cand = rep["win_feats"], rep["cand_feats"]
    n_matched = len(rep["matched"])

    breaches = []
    if dev["n_eval"] != 222:
        breaches.append("dev_eval=%d!=222" % dev["n_eval"])
    if rep["n_eval"] != 1056:
        breaches.append("replication_eval=%d!=1056" % rep["n_eval"])
    if n_total != SEALED_TOTAL_EVALUATIONS:
        breaches.append("total_eval=%d!=1278" % n_total)

    # per-effect larger-N anatomy via the frozen robustness lens (reused by identity)
    per_effect = {}
    any_nonfinite = False
    for s in ALL_EFFECTS:
        a = _feature_audit(win, cand, s) if win and cand else {"invalid_nonfinite": True}
        if a.get("invalid_nonfinite"):
            any_nonfinite = True
            per_effect[s] = {"invalid_nonfinite": True}
            continue
        per_effect[s] = {"best_threshold_BA": a["best_threshold_BA"], "signed_median_diff": a["signed_median_diff"],
                         "smd_as_fraction_of_TOL": a["smd_as_fraction_of_TOL"], "rank_separated": a["rank_separated"],
                         "robustness": a["robustness"]}

    # threshold-free magnitude clustering over the valid effects (largest-gap split on |smd|/TOL)
    valid = [(s, per_effect[s]["smd_as_fraction_of_TOL"]) for s in ALL_EFFECTS if not per_effect[s].get("invalid_nonfinite")]
    substantial, negligible, split_gap = _largest_gap_split(valid)

    # per-effect persistence status vs v0.6a (which had rank_sep=True, BA=1.0 for all effects at n=3 vs 3)
    for s in ALL_EFFECTS:
        d = per_effect[s]
        if d.get("invalid_nonfinite"):
            d["status"] = "ambiguous"
        elif d["best_threshold_BA"] <= CHANCE_BAND:
            d["status"] = "collapses"                                   # separation gone (BA at/below chance floor)
        elif d["rank_separated"]:
            d["status"] = "persists_robust"                             # perfect rank separation survived larger n
        elif s in substantial:
            d["status"] = "persists_substantial"                        # BA saturation weakened, real class diff persists
        else:
            d["status"] = "weakens_negligible"                          # BA saturation weakened, magnitude negligible

    # outcome (research-only; leaves claim locks unchanged)
    def _persist(s):
        return per_effect[s].get("status") in ("persists_robust", "persists_substantial")
    a_persist = all(_persist(s) for s in EFFECTS_A_BY)
    rg_negligible = all(per_effect[s].get("status") == "weakens_negligible" for s in ("rg_centroid", "rg_spread"))
    directional_negligible = all(per_effect[s].get("status") in ("weakens_negligible", "collapses")
                                 for s in EFFECTS_B_DIRECTIONAL)

    if breaches or any_nonfinite:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches + (["nonfinite"] if any_nonfinite else []))
    elif a_persist and rg_negligible:
        outcome_label = "BY_persistence_metric_insufficiency"
        outcome = ("BY_persistence_metric_insufficiency: BY-channel effects persist with substantial magnitude at "
                   "larger n while the fragile rg / directional effects weaken to negligible magnitude")
    elif a_persist and not rg_negligible:
        outcome_label = "mixed_effects_persist"
        outcome = "mixed_effects_persist: BY-channel persists AND some small-N effects also persist"
    elif (not a_persist) and rg_negligible:
        outcome_label = "small_n_features_collapse"
        outcome = "small_n_features_collapse: fragile small-N effects weaken/collapse; BY-channel did not persist"
    elif directional_negligible and not a_persist:
        outcome_label = "directional_collapse_tiny_magnitude"
        outcome = "directional_collapse_tiny_magnitude: directional effects negligible/collapsed"
    else:
        outcome_label = "replication_inconclusive"
        outcome = "replication_inconclusive: larger-N pattern does not cleanly resolve the effects"

    protocol_ok = (len(breaches) == 0 and not any_nonfinite)
    residual_closeness_coexists = bool(n_matched > 0 and any(
        not per_effect[s].get("invalid_nonfinite") and per_effect[s]["best_threshold_BA"] > CHANCE_BAND
        for s in ALL_EFFECTS))
    return {"diagnostic": "v0.7b larger-N residual replication (form A, NON-LEARNING; reporting-only; sealed v0.7a "
                          "enumeration; reuses frozen v0.3/v0.4d/v0.5a/v0.6a by identity)",
            "model_form": "A_non_learning_reporting", "learning": False, "explanatory_only": True,
            "replication_question": "which v0.6a separability effects survive when sample support is larger?",
            "TOL": TOL, "PSC_FLOOR": PSC_FLOOR, "CHANCE_BAND": CHANCE_BAND, "TOL_redefined": False,
            "new_threshold_introduced": False, "new_family_or_axis": False, "spectral_role": "audit-note-only (NOT reopened)",
            "n_dev_evaluations": dev["n_eval"], "n_replication_evaluations": rep["n_eval"],
            "n_total_evaluations": n_total, "sealed_total_evaluations": SEALED_TOTAL_EVALUATIONS,
            "n_replication_winders": len(REPLICATION_WINDER_SPEEDS) + len(REPLICATION_WINDER_PHASES) + len(REPLICATION_WINDER_RADII),
            "n_matched": n_matched, "n_unmatched": len(rep["unmatched"]), "unmatched_winders": rep["unmatched"],
            "audit_n_per_class": n_matched,
            "per_effect": per_effect, "magnitude_substantial": substantial, "magnitude_negligible": negligible,
            "magnitude_split_gap": split_gap,
            "residual_closeness_coexists_with_separability": residual_closeness_coexists,
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
    print("evaluations dev/replication/total:", r["n_dev_evaluations"], r["n_replication_evaluations"],
          r["n_total_evaluations"], "(sealed", r["sealed_total_evaluations"], ")")
    print("replication winders:", r["n_replication_winders"], "| matched:", r["n_matched"], "| unmatched:", r["n_unmatched"], r["unmatched_winders"])
    print("residual closeness coexists with separability:", r["residual_closeness_coexists_with_separability"])
    print()
    print("per-effect at larger n (vs v0.6a where all were rank_sep=True, BA=1.0):")
    for s in ALL_EFFECTS:
        d = r["per_effect"][s]
        if d.get("invalid_nonfinite"):
            print("  %-24s INVALID/non-finite" % s); continue
        print("  %-24s BA=%.3f smd=%+.5f (%.0f%%TOL) rank_sep=%s -> %s"
              % (s, d["best_threshold_BA"], d["signed_median_diff"], 100 * d["smd_as_fraction_of_TOL"],
                 d["rank_separated"], d["status"]))
    print()
    print("magnitude SUBSTANTIAL:", r["magnitude_substantial"])
    print("magnitude NEGLIGIBLE :", r["magnitude_negligible"], "(largest-gap split=%.4f)" % r["magnitude_split_gap"])
    print()
    print("OUTCOME_LABEL:", r["outcome_label"])
    print("OUTCOME:", r["outcome"])
    print("protocol_ok:", r["protocol_ok"], r["breaches"])
    print("verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"], r["descriptor_validity_claim_allowed"])
