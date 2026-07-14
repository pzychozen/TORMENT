"""BV chroma-structure by_std residual diagnostic v2.0 (offline research; NOT runtime/integration; NOT vision).

v1.9 (edge a749d6e) showed S/PSC survives tight spectral/std blocker control (Outcome A_with_residual) but left
one residual: `by_std` retains a weaker CROSS-FAMILY pool correlation with S. This diagnostic decomposes that
residual to decide whether it is:

    A. a pool-composition artifact  -> by_std<->S appears in the pooled/cross-family view but disappears
                                       within matched pairs and within a winding class (S constant per class);
    B. a true descriptor limitation -> by_std<->S persists WITHIN matched pairs / within a winding class even
                                       when movement and the other blockers are controlled;
    C. unresolved                   -> family sizes / degeneracy / residual matching make it unclear.

It is REPORTING-ONLY. It reuses the frozen v0.7/v0.8 machinery by identity (structure_score / _stats /
_spearman / constants) and the v1.4/v1.9 fixture generators; it changes NO formula, NO §7 anti-proxy logic, NO
§8 verdict logic, NO threshold, and NO control, defines no replacement acceptance criteria, cherry-picks
nothing into a pass, and cannot make the gate pass. The verdict is taken from the frozen §8 logic over the
v2.0 bank and stays HOLD. Matching by_std RANGES across winding classes is a within-diagnostic decomposition,
NOT a change to the frozen §7 gate.

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no memory-system
integration; no object/scene understanding; no temporal-order diagnostic; no new descriptor; no new gate; no
real clips. Brainvision Path B is NOT proven vision and is NOT a functioning vision layer for TORMENT memory.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_color_structure_fixture_bank_v1_1 as fb
import run_color_structure_spectral_std_blocker_v1_9 as v9

# frozen surfaces reused verbatim (NOT redefined)
T = cs.T
A = cs.A
BASE_Y = cs.BASE_Y
structure_score = cs.structure_score
stats = cs._stats
series = cs._series
spearman = cs.g5._spearman
CEIL = cs.MAGNITUDE_CORR_CEIL
THETA0 = v9.THETA0
FULL = v9.FULL

FRACS = (1.0, 0.7, 0.5, 0.3)      # predeclared amplitude fractions -> span by_std within a winding class


def _winder(frac):
    return v9._series_theta(THETA0 + FULL * np.arange(T), frac * A * np.ones(T))    # coherent winding, S=1


def _outback(frac):
    h = (T - 1) // 2
    d = np.concatenate([np.full(h, 0.20), np.full(T - 1 - h, -0.20)])
    return v9._series_theta(np.concatenate([[THETA0], THETA0 + np.cumsum(d)]), frac * A * np.ones(T))  # low by_std


def _collinear(frac):
    t = np.arange(T)
    x = frac * A * np.cos(2 * np.pi * t / T + THETA0)
    return series(np.full(T, BASE_Y), x, x.copy())      # RG==BY -> cancels; by_std MATCHES the winder's


def _score(gen):
    rg, by, ch = gen()[:3]
    s = structure_score(rg, by, ch)
    return {"S": s["S"], "PSC": s["PSC"], "AIC": s["AIC"], "stats": stats(rg, by, ch), "rgbych": (rg, by, ch)}


def _rho_S_bystd(items):
    if len(items) < 3:
        return None
    Sv = np.array([it["S"] for it in items], float)
    bv = np.array([it["stats"]["by_std"] for it in items], float)
    return float(spearman(Sv, bv))


def run():
    # ---- span groups (vary by_std within a fixed winding class) ----
    winder_span = [{"name": "winder_%.1f" % f, "frac": f, "cls": "winder", **_score(lambda f=f: _winder(f))}
                   for f in FRACS]
    outback_span = [{"name": "outback_%.1f" % f, "frac": f, "cls": "nonwinder", **_score(lambda f=f: _outback(f))}
                    for f in FRACS]                                # by_std MISMATCHED (lower) vs winders
    collinear_span = [{"name": "collinear_%.1f" % f, "frac": f, "cls": "nonwinder",
                       **_score(lambda f=f: _collinear(f))} for f in FRACS]   # by_std MATCHED to winders

    # ---- pairwise families reused from v1.9 (winder vs non-winder) ----
    pairwise = []
    for pid, wgen, ngen, strat in v9._PAIRS:
        w, n = _score(wgen), _score(ngen)
        pairwise.append({"pair_id": pid, "strategy": strat, "w": w, "n": n})

    def _by(it):
        return it["stats"]["by_std"]

    # ================= section 2: pairwise_by_std_control =================
    pairwise_by_std_control = []
    for p in pairwise:
        w, n = p["w"], p["n"]
        pairwise_by_std_control.append({
            "pair_id": p["pair_id"], "family": p["strategy"],
            "winder_S": round(w["S"], 4), "nonwinder_S": round(n["S"], 4),
            "winder_PSC": round(w["PSC"], 4), "nonwinder_PSC": round(n["PSC"], 4),
            "winder_by_std": round(_by(w), 5), "nonwinder_by_std": round(_by(n), 5),
            "abs_by_std_delta": round(abs(_by(w) - _by(n)), 5),
            "S_separation": round(w["S"] - n["S"], 4)})

    # ================= section 3: family_level_residuals =================
    groups = {"winder_span": winder_span, "outback_span": outback_span, "collinear_span": collinear_span}
    for p in pairwise:                                            # each pairwise family as a 2-point group
        groups["pair_" + p["pair_id"]] = [p["w"], p["n"]]
    family_level_residuals = []
    for gname, items in groups.items():
        Sr = [it["S"] for it in items]
        br = [_by(it) for it in items]
        pscs = [it["PSC"] for it in items]
        rho = _rho_S_bystd(items)
        single_class = all(p >= cs.PSC_FLOOR for p in pscs) or all(p < cs.PSC_FLOOR for p in pscs)
        degenerate = (len(items) < 3) or single_class or (float(np.std(br)) < 1e-9)
        family_level_residuals.append({
            "family": gname, "n": len(items),
            "by_std_rho_with_S": (None if rho is None else round(rho, 3)),
            "by_std_range": [round(min(br), 5), round(max(br), 5)],
            "S_range": [round(min(Sr), 4), round(max(Sr), 4)],
            "degenerate_or_underpowered": bool(degenerate),
            "note": ("n<3 underpowered" if len(items) < 3 else
                     ("single winding class -> S ~constant within family; within-class by_std<->S rho is not "
                      "meaningful (S is a winding-class function)" if single_class else ""))})

    # ================= section 4: pooled_vs_within_family_comparison =================
    pool_mismatched = winder_span + outback_span        # winder by_std HIGH, non-winder by_std LOW (v1.9-style)
    pool_matched = winder_span + collinear_span          # winder & collinear by_std MATCHED across the range
    pooled_mismatched_rho = _rho_S_bystd(pool_mismatched)
    pooled_matched_rho = _rho_S_bystd(pool_matched)
    within_family_rhos = {g: f["by_std_rho_with_S"] for g, f in
                          zip(groups, family_level_residuals)}
    pooled_persists_within = any(
        (f["by_std_rho_with_S"] is not None and abs(f["by_std_rho_with_S"]) >= CEIL
         and not f["degenerate_or_underpowered"]) for f in family_level_residuals)
    pooled_vs_within_family_comparison = {
        "pooled_mismatched_by_std_rho": (None if pooled_mismatched_rho is None else round(pooled_mismatched_rho, 3)),
        "pooled_matched_range_by_std_rho": (None if pooled_matched_rho is None else round(pooled_matched_rho, 3)),
        "within_family_rhos": within_family_rhos,
        "pooled_correlation_disappears_when_ranges_matched": bool(
            pooled_mismatched_rho is not None and pooled_matched_rho is not None
            and abs(pooled_mismatched_rho) >= CEIL and abs(pooled_matched_rho) < CEIL),
        "pooled_correlation_persists_within_families": bool(pooled_persists_within)}

    # ================= section 1: by_std_residual_summary + classification =================
    within_pair_delta = {pc["pair_id"]: pc["abs_by_std_delta"] for pc in pairwise_by_std_control}
    matched_pairs_that_separate = [pc["pair_id"] for pc in pairwise_by_std_control
                                   if pc["abs_by_std_delta"] < 0.01 and pc["S_separation"] > 0.5]
    cmp = pooled_vs_within_family_comparison
    pm = cmp["pooled_matched_range_by_std_rho"]
    pmis = cmp["pooled_mismatched_by_std_rho"]
    survives_matched = (pm is not None) and (abs(pm) >= CEIL)          # correlation survives matched by_std ranges
    disappears_matched = (pm is not None and pmis is not None and abs(pmis) >= CEIL and abs(pm) < CEIL)
    if survives_matched or cmp["pooled_correlation_persists_within_families"]:
        classification = "descriptor limitation"
    elif disappears_matched and matched_pairs_that_separate:
        classification = "pool-composition artifact"
    else:
        classification = "unresolved"
    by_std_residual_summary = {
        "pooled_rho_S_by_std": cmp["pooled_mismatched_by_std_rho"],
        "within_pair_delta_profile": within_pair_delta,
        "within_family_rho_profile": within_family_rhos,
        "cross_family_matched_range_rho": cmp["pooled_matched_range_by_std_rho"],
        "matched_pairs_that_still_separate": matched_pairs_that_separate,
        "classification": classification}

    # ================= section 5: verdict -- frozen §7 anti-proxy + §8 over the v2.0 bank (UNCHANGED) =========
    ct = series(*cs.continuity_control()); S_cont = structure_score(ct[0], ct[1], ct[2])["S"]
    st = series(*cs.structureless_control()); S_struct = structure_score(st[0], st[1], st[2])["S"]
    entries, inscope, traj_by_pair = [], [], {}
    all_winders = [(it["name"], it) for it in winder_span] + [("pair_" + p["pair_id"] + "_w", p["w"]) for p in pairwise]
    all_nonwind = [(it["name"], it) for it in outback_span + collinear_span] \
        + [("pair_" + p["pair_id"] + "_n", p["n"]) for p in pairwise]
    for i, (nm, it) in enumerate(all_winders):
        e = {"name": nm, "S": it["S"], "PSC": it["PSC"], "AIC": it["AIC"], "stats": it["stats"], "pair": nm}
        entries.append(e); inscope.append(e)
        rg, by, ch = it["rgbych"]
        rgp, byp, chp, _r, invalid = fb.traj_null_guarded(rg, by)
        if not invalid:
            s_t = structure_score(rgp, byp, chp)
            traj_by_pair[nm] = {"S": s_t["S"]}
            entries.append({"name": nm + "_traj", "S": s_t["S"], "stats": stats(rgp, byp, chp), "pair": nm})
            irg, iby, ich, _ic = series(np.full(T, BASE_Y), *cs.null_independent_phase(rg, by, 5000 + i))
            entries.append({"name": nm + "_indep", "S": structure_score(irg, iby, ich)["S"],
                            "stats": stats(irg, iby, ich), "pair": nm})
    for nm, it in all_nonwind:
        entries.append({"name": nm, "S": it["S"], "stats": it["stats"], "pair": nm})
    entries.append({"name": "continuity_control", "S": S_cont, "stats": stats(ct[0], ct[1], ct[2]), "pair": None})
    entries.append({"name": "structureless_control", "S": S_struct, "stats": stats(st[0], st[1], st[2]), "pair": None})
    keys = list(cs.ANTI_PROXY_STATS) + ["nr_" + s for s in cs.NULL_REL_STATS]
    traj_stats = [entries[j] for j in range(len(entries)) if entries[j]["name"].endswith("_traj")]
    Sall = np.array([e["S"] for e in entries], float)
    anti_ok = True
    for k in keys:
        st_name = k[3:] if k.startswith("nr_") else k
        b = (float(np.mean([e["stats"][st_name] for e in traj_stats])) if traj_stats else 0.0) if k.startswith("nr_") else 0.0
        if abs(spearman(Sall, np.array([e["stats"][st_name] - b for e in entries], float))) >= CEIL:
            anti_ok = False
    n_ok = sum(1 for e in inscope
               if e["name"] in traj_by_pair
               and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * traj_by_pair[e["name"]]["S"]
               and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * S_cont
               and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * S_struct
               and e["PSC"] >= cs.PSC_FLOOR and e["AIC"] >= cs.AIC_FLOOR)
    n_le_null = sum(1 for e in inscope if e["name"] in traj_by_pair and e["S"] <= traj_by_pair[e["name"]]["S"])
    if n_le_null > len(inscope) / 2:
        verdict = "FAIL"
    elif n_ok > len(inscope) / 2 and anti_ok:
        verdict = "PASS"
    else:
        verdict = "HOLD"

    return {"diagnostic": "v2.0 by_std residual (reuses frozen v0.7/v0.8 + v1.4/v1.9 fixtures, reporting-only)",
            "by_std_residual_summary": by_std_residual_summary,
            "pairwise_by_std_control": pairwise_by_std_control,
            "family_level_residuals": family_level_residuals,
            "pooled_vs_within_family_comparison": pooled_vs_within_family_comparison,
            "bank_size": len(entries), "verdict": verdict, "reporting_only": True,
            "first_pass_structure_validity_claim_allowed": bool(verdict == "PASS"),
            "temporal_claim_allowed": False}


if __name__ == "__main__":
    r = run()
    print("verdict", r["verdict"], "| bank_size", r["bank_size"], "| reporting_only", r["reporting_only"])
    print("\n1. by_std_residual_summary:")
    print("   pooled_rho(S,by_std) [mismatched] =", r["by_std_residual_summary"]["pooled_rho_S_by_std"])
    print("   cross_family_matched_range_rho    =", r["by_std_residual_summary"]["cross_family_matched_range_rho"])
    print("   matched_pairs_that_still_separate =", r["by_std_residual_summary"]["matched_pairs_that_still_separate"])
    print("   CLASSIFICATION                    =", r["by_std_residual_summary"]["classification"])
    print("\n2. pairwise_by_std_control:")
    for pc in r["pairwise_by_std_control"]:
        print("   %-20s S %.3f/%.3f PSC %.2f/%.2f by_std %.4f/%.4f |Δ|=%.4f Ssep=%.3f"
              % (pc["pair_id"], pc["winder_S"], pc["nonwinder_S"], pc["winder_PSC"], pc["nonwinder_PSC"],
                 pc["winder_by_std"], pc["nonwinder_by_std"], pc["abs_by_std_delta"], pc["S_separation"]))
    print("\n3. family_level_residuals:")
    for f in r["family_level_residuals"]:
        print("   %-18s n=%d rho(S,by_std)=%s by_std=%s S=%s degen=%s %s"
              % (f["family"], f["n"], f["by_std_rho_with_S"], f["by_std_range"], f["S_range"],
                 f["degenerate_or_underpowered"], f["note"]))
    print("\n4. pooled_vs_within_family_comparison:")
    c = r["pooled_vs_within_family_comparison"]
    print("   pooled_mismatched_rho =", c["pooled_mismatched_by_std_rho"],
          "| pooled_matched_range_rho =", c["pooled_matched_range_by_std_rho"])
    print("   disappears_when_ranges_matched =", c["pooled_correlation_disappears_when_ranges_matched"],
          "| persists_within_families =", c["pooled_correlation_persists_within_families"])
