"""BV matched generative search v0.4d (offline research; form A; NON-LEARNING; NOT vision).

Runs EXACTLY the sealed v0.4c enumeration
(docs: TORMENT_BRAINVISION_MATCHED_GENERATIVE_SEARCH_ENUMERATION_v0.4c) over the v0.4b protocol
(docs: ..._PREREG_v0.4b). It searches a CLOSED, finite space of non-winder candidate generators for fixtures
that MATCH the frozen v0.3 target winders on the four MATCHED proxy groups within the frozen TOL, subject to the
SOLE non-structure feasibility constraint PSC < PSC_FLOOR. It reuses the frozen v0.3 / v0.8 / v1.9 / v2.0
descriptor, evaluator, GROUPS mapping, and generators BY IDENTITY; it invents no formula and no protocol
threshold, changes no gate/verdict logic, deletes/weakens no control, and adds NO classifier (form B) / neural
encoder (form C).

Search objective is ONLY proxy_match_residual under feasibility (PSC < PSC_FLOOR). It NEVER optimizes the fixed
rule decision score, PSC/AIC balanced accuracy, any classifier score, S_best_threshold, label accuracy, held-out
performance, any post-hoc shortcut metric, or the cheap-baseline BA. The frozen evaluator (structure iff
PSC >= PSC_FLOOR and AIC >= AIC_FLOOR) and the cheap-baseline audit are computed only AFTER the search, on the
single-shot held-out set, and are never fed back. Budget is finite (190 dev + 93 held-out = 283 evaluations,
full grid once per target, no restarts / retries / redraws). NaN / non-finite / extreme-quantized values are
defensively excluded and can never satisfy feasibility, matching, baseline closure, or any claim.

This makes NO vision / "Brainvision sees" / temporal-order / descriptor-validity / memory / runtime /
integration claim. Claim locks stay False and the frozen Brainvision verdict stays HOLD under EVERY outcome.

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

# ---- frozen protocol thresholds (referenced from frozen code / committed docs; NOT invented here) ----
PSC_FLOOR = cs.PSC_FLOOR                 # 0.30 (frozen)
AIC_FLOOR = cs.AIC_FLOOR                 # 0.30 (frozen)
CHANCE_BAND = v3.CHANCE_BAND             # 0.60 (frozen, reporting-only)
TOL = 0.0634                             # frozen v0.3 best-effort L-inf residual ceiling (v0.4b/v0.4c)

# ---- frozen descriptor / evaluator / group surfaces (reused BY IDENTITY) ----
GROUPS = v3.GROUPS                       # frozen v0.3 cheap-shortcut mapping
MATCHED_GROUPS = ("movement_channel_energy", "directional", "per_channel", "frame_diff")   # spectral audit-note-only
MATCHED_STATS = tuple(dict.fromkeys(s for g in MATCHED_GROUPS for s in GROUPS[g]))          # dedup union (spectral excluded)
_feat = v3._feat                         # frozen descriptor+stats feature dict (incl. PSC/AIC/S)
T = cs.T
A = cs.A
BASE_Y = cs.BASE_Y
THETA0 = v9.THETA0
FULL = v9.FULL

# ---- defensive sanitization (REQUIRED by v0.4d; a reporting/hygiene bound, NOT a descriptor threshold) ----
EXTREME_VALUE_CAP = 1.0e6                # |value| above this is treated as an extreme-quantized artifact -> excluded

# ---- sealed v0.4c enumeration ----
FAMILIES = ("full_circle_incoherent_traversal", "rosette_multilobe_traversal", "segment_paired_canceller",
            "phase_scrambled_full_coverage", "hybrid_coverage_preserving_canceller")
F1_SIGMAS = (0.3, 0.6, 1.0)
F2_LOBES = (2, 3, 5)
F2_RADII = (0.7, 1.0)
F3_G = (0.10, 0.20, 0.30, 0.50, 0.79)      # subset of frozen v0.3 outback increments
F3_PAIRS = (1, 2)
F4_SIGMAS = (0.5, 1.0, 1.5)
DEVELOPMENT_SEEDS = (20260709, 20260710, 20260711)
HELDOUT_SEEDS = (20260712, 20260713)
DEVELOPMENT_TARGETS = ("winder_sp0.5", "winder_sp1.0", "winder_sp2.0", "winder_ph0.00", "winder_ph1.57")
HELDOUT_TARGETS = ("winder_ph3.14", "winder_r0.7", "winder_r0.5")
SEALED_TOTAL_EVALUATIONS = 283             # 5 dev targets x 38 + 3 held-out targets x 31

MATCH_SELECTION_FIELDS = ("proxy_match_residual", "feasible")   # the ONLY fields selection may use


# ----------------------------- candidate family generators (non-winders; PSC expected < floor) -----------------------------
def _f1_full_circle_incoherent(sigma, seed):
    """Full-circle up/down sweep (reversing -> net winding cancels) + per-step Gaussian phase noise (sigma)."""
    rng = np.random.default_rng(int(seed))
    t = np.arange(T)
    base = 2 * np.pi * (1.0 - np.abs(2.0 * t / (T - 1) - 1.0))          # 0 -> 2pi -> 0 (full coverage, reversing)
    d = np.diff(base) + rng.normal(0.0, sigma, size=T - 1)
    theta = THETA0 + np.concatenate([[0.0], np.cumsum(d)])
    return v9._series_theta(theta)


def _f2_rosette_multilobe(lobes, radius_frac):
    """Rose curve r = frac*A*cos(lobes*phi); multi-lobe coverage, net winding does not persist."""
    t = np.arange(T)
    phi = 2 * np.pi * t / T
    r = radius_frac * A * np.cos(lobes * phi)
    return cs._series(np.full(T, BASE_Y), r * np.cos(phi), r * np.sin(phi))


def _f3_segment_paired_canceller(g, pairs):
    """`pairs` forward/back angular blocks of magnitude g; each block cancels -> net winding cancels."""
    n = T - 1
    d = np.zeros(n)
    base = n // pairs
    for p in range(pairs):
        lo = p * base
        hi = n if p == pairs - 1 else (p + 1) * base
        seg = hi - lo
        fwd = seg // 2
        d[lo:lo + fwd] = g
        d[lo + fwd:hi] = -g
    theta = THETA0 + np.concatenate([[0.0], np.cumsum(d)])
    return v9._series_theta(theta)


def _f4_phase_scrambled_full_coverage(sigma, seed):
    """Permute a full-winder's angle samples with a sigma-controlled noisy sort key: coverage multiset preserved,
    winding order scrambled -> net winding cancels."""
    rng = np.random.default_rng(int(seed))
    base_theta = THETA0 + FULL * np.arange(T)                          # a full coherent winder (order intact)
    key = np.arange(T) + rng.normal(0.0, sigma * T, size=T)
    order = np.argsort(key, kind="stable")
    return v9._series_theta(base_theta[order])


def _combine(gen_a, gen_b, mix):
    ra, ba = gen_a()[0], gen_a()[1]
    rb, bb = gen_b()[0], gen_b()[1]
    rg = mix * np.asarray(ra, float) + (1 - mix) * np.asarray(rb, float)
    by = mix * np.asarray(ba, float) + (1 - mix) * np.asarray(bb, float)
    return cs._series(np.full(T, BASE_Y), rg, by)


def _f5_hybrid_comboA():                                               # deterministic
    return _combine(lambda: _f2_rosette_multilobe(3, 1.0),
                    lambda: _f3_segment_paired_canceller(0.30, 1), 0.5)


def _f5_hybrid_comboB(seed):                                          # uses an F1 component (stochastic)
    return _combine(lambda: _f1_full_circle_incoherent(0.6, seed),
                    lambda: _f3_segment_paired_canceller(0.50, 2), 0.5)


def candidates(seed_pool):
    """Return the ordered, sealed candidate list for one phase's seed pool (deterministic order)."""
    out = []

    def add(family, params, seed, gen):
        cid = "%s|%s|seed=%s" % (family, ",".join("%s=%s" % (k, params[k]) for k in sorted(params)), seed)
        out.append({"family": family, "params": dict(params), "seed": seed, "cand_id": cid, "gen": gen})

    for sg in F1_SIGMAS:
        for sd in seed_pool:
            add("full_circle_incoherent_traversal", {"sigma": sg}, sd,
                (lambda sg=sg, sd=sd: _f1_full_circle_incoherent(sg, sd)))
    for lb in F2_LOBES:
        for rf in F2_RADII:
            add("rosette_multilobe_traversal", {"lobes": lb, "radius_frac": rf}, None,
                (lambda lb=lb, rf=rf: _f2_rosette_multilobe(lb, rf)))
    for g in F3_G:
        for pr in F3_PAIRS:
            add("segment_paired_canceller", {"increment_g": g, "pairs": pr}, None,
                (lambda g=g, pr=pr: _f3_segment_paired_canceller(g, pr)))
    for sg in F4_SIGMAS:
        for sd in seed_pool:
            add("phase_scrambled_full_coverage", {"sigma": sg}, sd,
                (lambda sg=sg, sd=sd: _f4_phase_scrambled_full_coverage(sg, sd)))
    add("hybrid_coverage_preserving_canceller", {"combo": "A"}, None, _f5_hybrid_comboA)
    for sd in seed_pool:
        add("hybrid_coverage_preserving_canceller", {"combo": "B"}, sd, (lambda sd=sd: _f5_hybrid_comboB(sd)))
    return out


# ----------------------------- defensive value handling -----------------------------
def _is_clean(x):
    """True iff x is finite AND not an extreme-quantized artifact. NaN / inf / |x|>cap -> NOT clean."""
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return False
    return bool(np.isfinite(xf)) and (abs(xf) <= EXTREME_VALUE_CAP)


def _safe_feat(gen):
    """Compute the frozen feature dict defensively. Returns (feat_or_None, feasible, invalid_reason).

    feasible requires: PSC clean AND PSC < PSC_FLOOR AND every MATCHED_STAT clean. Non-finite / extreme values
    can NEVER be feasible."""
    try:
        feat = _feat(gen)
    except Exception as exc:                                           # generator/descriptor blew up -> invalid
        return None, False, "exception:%s" % type(exc).__name__
    if not _is_clean(feat.get("PSC")):
        return feat, False, "nonfinite_or_extreme_PSC"
    for s in MATCHED_STATS:
        if not _is_clean(feat.get(s)):
            return feat, False, "nonfinite_or_extreme_stat:%s" % s
    feasible = bool(float(feat["PSC"]) < PSC_FLOOR)                    # SOLE non-structure feasibility constraint
    return feat, feasible, ("" if feasible else "not_non_structure_PSC>=PSC_FLOOR")


def _residual(cand_feat, target_feat):
    """L-inf max abs delta over MATCHED_STATS (v0.3 raw-delta convention, spectral excluded). Non-finite/extreme
    in either side -> +inf (cannot match)."""
    worst = 0.0
    for s in MATCHED_STATS:
        a = cand_feat.get(s)
        b = target_feat.get(s)
        if not (_is_clean(a) and _is_clean(b)):
            return float("inf")
        worst = max(worst, abs(float(a) - float(b)))
    return worst


# ----------------------------- search (objective = proxy_match_residual + feasibility ONLY) -----------------------------
def _target_feat(name):
    return _feat(v3._winders()[name])


def _search_phase(target_names, seed_pool):
    cands = candidates(seed_pool)
    per_target = {}
    n_eval = 0
    for tname in target_names:
        tfeat = _target_feat(tname)
        rows = []
        best = None                                                   # (key, cand, feat, residual)
        for c in cands:
            n_eval += 1
            feat, feasible, reason = _safe_feat(c["gen"])
            resid = _residual(feat, tfeat) if (feasible and feat is not None) else float("inf")
            clean_resid = bool(np.isfinite(resid))
            matched = bool(feasible and clean_resid and resid <= TOL)
            rows.append({"cand_id": c["cand_id"], "family": c["family"], "seed": c["seed"],
                         "feasible": feasible, "invalid_reason": reason,
                         "proxy_match_residual": (round(float(resid), 6) if clean_resid else None),
                         "matched": matched})
            # SELECTION uses ONLY (proxy_match_residual, feasible); tie-break lowest seed then cand_id.
            if feasible and clean_resid:
                key = (resid, (c["seed"] if c["seed"] is not None else -1), c["cand_id"])
                if best is None or key < best[0]:
                    best = (key, c, feat, resid)
        if best is None:
            per_target[tname] = {"n_candidates": len(cands), "matched": False, "best_residual": None,
                                 "best_cand_id": None, "best_feasible_found": False, "rows": rows}
        else:
            _, bc, bfeat, bresid = best
            per_target[tname] = {"n_candidates": len(cands), "matched": bool(bresid <= TOL),
                                 "best_residual": round(float(bresid), 6), "best_cand_id": bc["cand_id"],
                                 "best_feasible_found": True, "_best_feat": bfeat, "rows": rows}
    return per_target, n_eval


def _heldout_baseline_audit(per_target):
    """AFTER-the-search, single-shot: on the matched held-out pairs, report cheap-baseline separability per
    matched group and whether the frozen evaluator still separates. Never fed back into the search."""
    matched_targets = [t for t in HELDOUT_TARGETS if per_target[t]["matched"]]
    if not matched_targets:
        return {"matched_targets": [], "group_separability_BA": {}, "all_matched_groups_closed": False,
                "evaluator_ba": None, "evaluator_separates": False}
    win_feats = [_target_feat(t) for t in matched_targets]
    cand_feats = [per_target[t]["_best_feat"] for t in matched_targets]
    feats = win_feats + cand_feats
    y = [1] * len(win_feats) + [0] * len(cand_feats)
    group_ba = {g: v3._group_sep_ba(feats, y, GROUPS[g]) for g in MATCHED_GROUPS}
    all_closed = bool(all(ba <= CHANCE_BAND for ba in group_ba.values()))
    ev_pred = v3._color_predict(feats)
    ev_ba = round(float(v3._ba(y, ev_pred)), 4)
    return {"matched_targets": matched_targets, "group_separability_BA": group_ba,
            "all_matched_groups_closed": all_closed, "evaluator_ba": ev_ba,
            "evaluator_separates": bool(ev_ba > 0.9)}


def run():
    dev_per_target, n_dev = _search_phase(DEVELOPMENT_TARGETS, DEVELOPMENT_SEEDS)      # construction/reporting only
    held_per_target, n_held = _search_phase(HELDOUT_TARGETS, HELDOUT_SEEDS)            # single-shot evaluation
    n_total = n_dev + n_held

    audit = _heldout_baseline_audit(held_per_target)
    n_matched_targets = sum(1 for t in HELDOUT_TARGETS if held_per_target[t]["matched"])
    strict_majority = bool(n_matched_targets >= 2)                                     # >=2 of 3 (reporting aggregation)

    # protocol self-checks (any breach -> Invalid, no evidential weight)
    breaches = []
    if n_dev != 190:
        breaches.append("dev_eval_count=%d!=190" % n_dev)
    if n_held != 93:
        breaches.append("heldout_eval_count=%d!=93" % n_held)
    if n_total != SEALED_TOTAL_EVALUATIONS:
        breaches.append("total_eval=%d!=283" % n_total)
    # a matched pair must have clean MATCHED_STATS (non-finite can never back a match)
    for t in HELDOUT_TARGETS:
        if held_per_target[t]["matched"]:
            bf = held_per_target[t]["_best_feat"]
            if not all(_is_clean(bf.get(s)) for s in MATCHED_STATS):
                breaches.append("nonfinite_in_matched_pair:%s" % t)
    protocol_ok = (len(breaches) == 0)

    if not protocol_ok:
        outcome = "Invalid_protocol_breach: " + "; ".join(breaches)
    elif strict_majority and audit["all_matched_groups_closed"] and audit["evaluator_separates"]:
        outcome = ("Match_feasible: matched non-winders for a strict majority of held-out targets close all four "
                   "matched cheap-baseline groups while the frozen evaluator still separates "
                   "(RESEARCH SIGNAL ONLY; NOT vision/validity)")
    elif n_matched_targets == 0:
        outcome = ("Match_infeasible: no admissible candidate reached residual <= TOL for any held-out target "
                   "across the sealed enumeration (Outcome-4-style; proxy wall stands for this family)")
    else:
        outcome = ("Partial: some held-out targets matched and/or some but not all matched groups closed; "
                   "reported per-target / per-group, not rounded up")

    def _pt(pt):
        return {t: {k: v for k, v in d.items() if k not in ("_best_feat", "rows")} for t, d in pt.items()}

    return {"diagnostic": "v0.4d matched generative search (form A, NON-LEARNING; sealed v0.4c enumeration; "
                          "reuses frozen v0.3/v0.8/v1.9/v2.0 by identity; reporting-only)",
            "model_form": "A_non_learning_search", "learning": False,
            "search_objective": "proxy_match_residual + feasibility(PSC < PSC_FLOOR)",
            "sole_feasibility_constraint": "PSC < PSC_FLOOR",
            "frozen_evaluator": "structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR",
            "matched_groups": list(MATCHED_GROUPS), "matched_stats": list(MATCHED_STATS),
            "spectral_role": "audit-note-only (excluded from match target)",
            "TOL": TOL, "PSC_FLOOR": PSC_FLOOR, "AIC_FLOOR": AIC_FLOOR, "CHANCE_BAND": CHANCE_BAND,
            "extreme_value_cap": EXTREME_VALUE_CAP,
            "families": list(FAMILIES),
            "development_targets": list(DEVELOPMENT_TARGETS), "heldout_targets": list(HELDOUT_TARGETS),
            "development_seeds": list(DEVELOPMENT_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
            "n_dev_evaluations": n_dev, "n_heldout_evaluations": n_held, "n_total_evaluations": n_total,
            "sealed_total_evaluations": SEALED_TOTAL_EVALUATIONS,
            "development_per_target": _pt(dev_per_target), "heldout_per_target": _pt(held_per_target),
            "heldout_baseline_audit": audit, "n_matched_heldout_targets": n_matched_targets,
            "strict_majority_heldout": strict_majority, "protocol_ok": protocol_ok, "protocol_breaches": breaches,
            "outcome": outcome, "reporting_only": True,
            "frozen_brainvision_verdict": "HOLD",
            "first_pass_structure_validity_claim_allowed": False, "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
            "integration_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| learning", r["learning"])
    print("objective:", r["search_objective"], "| feasibility:", r["sole_feasibility_constraint"])
    print("evaluations dev/held/total:", r["n_dev_evaluations"], r["n_heldout_evaluations"], r["n_total_evaluations"],
          "(sealed", r["sealed_total_evaluations"], ")")
    print("\nheld-out per target (best feasible residual; matched iff <= TOL=%.4f):" % r["TOL"])
    for t, d in r["heldout_per_target"].items():
        print("  %-14s best_residual=%s matched=%s feasible_found=%s"
              % (t, d["best_residual"], d["matched"], d["best_feasible_found"]))
    a = r["heldout_baseline_audit"]
    print("\nheld-out baseline audit (matched targets=%s):" % a["matched_targets"])
    print("  group separability BA:", a["group_separability_BA"], "| all_closed:", a["all_matched_groups_closed"])
    print("  evaluator_ba:", a["evaluator_ba"], "| separates:", a["evaluator_separates"])
    print("\nn_matched_heldout_targets:", r["n_matched_heldout_targets"], "| strict_majority:", r["strict_majority_heldout"])
    print("protocol_ok:", r["protocol_ok"], r["protocol_breaches"])
    print("\nOUTCOME:", r["outcome"])
    print("verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"],
          r["descriptor_validity_claim_allowed"])
