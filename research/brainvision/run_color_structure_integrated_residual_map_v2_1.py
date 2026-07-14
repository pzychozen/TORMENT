"""BV chroma-structure integrated residual map / deconfounded-bank diagnostic v2.1 (offline research; NOT vision).

Consolidates the strongest synthetic controls resolved across v1.9 (spectral/std blocker) and v2.0 (by_std
residual) into ONE bank, re-runs the frozen v0.7/v0.8 chroma-structure descriptor + the UNCHANGED §7 anti-proxy
surface over it, and MAPS which §7 failures remain after the known spectral/std and by_std confounds are
controlled or explained. It answers: "what still fails once spectral_centroid and by_std are controlled?"

It is REPORTING-ONLY. It reuses the frozen v0.7/v0.8 machinery by identity (structure_score / _stats /
_spearman / constants) and the v1.4/v1.9/v2.0 fixture generators; it changes NO formula, NO §7 anti-proxy
logic, NO §8 verdict logic, NO threshold, and NO control; it deletes/cherry-picks nothing; it PRESERVES the
hard controls (trajectory-order nulls, independent-phase nulls, structureless + continuity). It cannot make
the gate pass: the verdict comes from the frozen §8 logic over the consolidated bank and stays HOLD while any
§7 stat fails. Prior failures now under the ceiling are reported as `controlled_or_explained` (NOT deleted);
failures that remain are reported honestly.

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
import run_color_structure_by_std_residual_v2_0 as v20

# frozen surfaces reused verbatim (NOT redefined)
T = cs.T
BASE_Y = cs.BASE_Y
structure_score = cs.structure_score
stats = cs._stats
series = cs._series
spearman = cs.g5._spearman
CEIL = cs.MAGNITUDE_CORR_CEIL
ANTI_PROXY_STATS = cs.ANTI_PROXY_STATS
NULL_REL_STATS = cs.NULL_REL_STATS

# stats the arc previously flagged as spectral/std blockers (v1.8) or the v2.0-explained residual
CONTROLLED_EXPLAINED_STATS = ("spectral_centroid", "by_std")
EVIDENCE = {
    "spectral_centroid": "v1.8 matched-subset blocker; controlled on the consolidated bank (const-CHROMA family)",
    "by_std": "v2.0 pool-composition artifact; controlled on the consolidated bank (matched by_std ranges)",
    "rg_spread": "v1.9 neutralized per-pair (PR RG==BY, delta 0) but the pooled consolidated bank still fails",
    "nr_rg_spread": "v1.9 neutralized per-pair (PR RG==BY, delta 0) but the pooled consolidated bank still fails",
    "u_directional_delta_rms": "directional movement axis; pooled covariance driven by nulls/controls (v1.6/v1.8)",
    "angular_increment_mag": "directional movement axis; pooled covariance driven by nulls/controls (v1.6/v1.8)",
    "rg_centroid": "per-channel spectral geometry axis (v1.8 directional/per-channel residual)",
    "by_centroid": "per-channel spectral geometry axis (v1.8 directional/per-channel residual)",
    "by_spread": "per-channel spectral geometry axis (v1.8 directional/per-channel residual)",
}


def _sc(gen):
    rg, by, ch = gen()[:3]
    s = structure_score(rg, by, ch)
    return {"S": s["S"], "PSC": s["PSC"], "AIC": s["AIC"], "stats": stats(rg, by, ch), "rgby": (rg, by, ch)}


def _build_bank():
    """Consolidated deconfounded bank: v1.9 pairwise winder/non-winder families + v2.0 span groups (winder /
    out-and-back / collinear across amplitude fractions) + per-winder trajectory + independent-phase nulls +
    structureless + continuity controls. Hard controls preserved; nothing deleted."""
    families = []
    winders, nonwinders = [], []
    for pid, wgen, ngen, _strat in v9._PAIRS:
        winders.append((pid + "_winder", _sc(wgen))); nonwinders.append((pid + "_nonwinder", _sc(ngen)))
        families.append("pairwise:" + pid)
    for f in v20.FRACS:
        winders.append(("winder_span_%.1f" % f, _sc(lambda f=f: v20._winder(f))))
        nonwinders.append(("outback_span_%.1f" % f, _sc(lambda f=f: v20._outback(f))))
        nonwinders.append(("collinear_span_%.1f" % f, _sc(lambda f=f: v20._collinear(f))))
    families += ["winder_span", "outback_span", "collinear_span"]

    ct = series(*cs.continuity_control()); S_cont = structure_score(ct[0], ct[1], ct[2])["S"]
    st = series(*cs.structureless_control()); S_struct = structure_score(st[0], st[1], st[2])["S"]

    entries = []
    traj_by_name, n_traj, n_indep = {}, 0, 0
    for i, (nm, it) in enumerate(winders):
        entries.append({"name": nm, "group": "winder", "S": it["S"], "PSC": it["PSC"], "AIC": it["AIC"],
                        "stats": it["stats"]})
        rg, by, ch = it["rgby"]
        rgp, byp, chp, _r, invalid = fb.traj_null_guarded(rg, by)
        if not invalid:
            s_t = structure_score(rgp, byp, chp)
            traj_by_name[nm] = s_t["S"]; n_traj += 1
            entries.append({"name": nm + "_traj", "group": "traj_null", "S": s_t["S"], "stats": stats(rgp, byp, chp)})
            irg, iby, ich, _ic = series(np.full(T, BASE_Y), *cs.null_independent_phase(rg, by, 7000 + i))
            entries.append({"name": nm + "_indep", "group": "indep_null", "S": structure_score(irg, iby, ich)["S"],
                            "stats": stats(irg, iby, ich)}); n_indep += 1
    for nm, it in nonwinders:
        entries.append({"name": nm, "group": "nonwinder", "S": it["S"], "PSC": it["PSC"], "stats": it["stats"]})
    entries.append({"name": "continuity_control", "group": "continuity_control", "S": S_cont, "PSC": 0.0,
                    "stats": stats(ct[0], ct[1], ct[2])})
    entries.append({"name": "structureless_control", "group": "structureless_control", "S": S_struct, "PSC": 0.0,
                    "stats": stats(st[0], st[1], st[2])})
    return {"entries": entries, "winders": winders, "nonwinders": nonwinders, "families": families,
            "traj_by_name": traj_by_name, "n_traj": n_traj, "n_indep": n_indep, "S_cont": S_cont,
            "S_struct": S_struct}


def run():
    bank = _build_bank()
    entries = bank["entries"]
    traj_stats = [e for e in entries if e["group"] == "traj_null"]
    keys = list(ANTI_PROXY_STATS) + ["nr_" + s for s in NULL_REL_STATS]
    Sall = np.array([e["S"] for e in entries], float)

    # ---- frozen §7 anti-proxy over the consolidated bank (UNCHANGED rule) ----
    anti_proxy_failure_map = []
    remaining_failures, resolved_or_explained = [], []
    for k in keys:
        sn = k[3:] if k.startswith("nr_") else k
        base = (float(np.mean([e["stats"][sn] for e in traj_stats])) if traj_stats else 0.0) if k.startswith("nr_") else 0.0
        rho = float(spearman(Sall, np.array([e["stats"][sn] - base for e in entries], float)))
        fails = abs(rho) >= CEIL
        base_stat = sn
        if not fails:
            status = "controlled_or_explained" if base_stat in CONTROLLED_EXPLAINED_STATS else "pass"
        else:
            status = "remaining_failure"
        if status == "remaining_failure":
            remaining_failures.append(k)
        elif status == "controlled_or_explained":
            resolved_or_explained.append(k)
        anti_proxy_failure_map.append({
            "stat": k, "rho": round(rho, 3), "abs_rho": round(abs(rho), 3),
            "gate": "fail" if fails else "pass", "status": status,
            "evidence_note": EVIDENCE.get(base_stat, "")})
    anti_proxy_ok = (len(remaining_failures) == 0)

    # ---- frozen §8 verdict over the consolidated bank (UNCHANGED; traj-null beat + FAIL branch) ----
    inscope = [e for e in entries if e["group"] == "winder"]
    tb = bank["traj_by_name"]
    n_ok = sum(1 for e in inscope
               if e["name"] in tb
               and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * tb[e["name"]]
               and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * bank["S_cont"]
               and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * bank["S_struct"]
               and e["PSC"] >= cs.PSC_FLOOR and e["AIC"] >= cs.AIC_FLOOR)
    n_le_null = sum(1 for e in inscope if e["name"] in tb and e["S"] <= tb[e["name"]])
    if n_le_null > len(inscope) / 2:
        verdict = "FAIL"
    elif n_ok > len(inscope) / 2 and anti_proxy_ok:
        verdict = "PASS"
    else:
        verdict = "HOLD"

    # ---- section 3: deconfounded_bank_summary ----
    n_win = len(bank["winders"]); n_non = len(bank["nonwinders"])
    controls_present = (bank["n_traj"] > 0 and bank["n_indep"] > 0
                        and any(e["group"] == "continuity_control" for e in entries)
                        and any(e["group"] == "structureless_control" for e in entries)
                        and n_non > 0)
    deconfounded_bank_summary = {
        "bank_size": len(entries), "fixture_families": bank["families"], "winder_count": n_win,
        "non_winder_count": n_non, "traj_null_count": bank["n_traj"], "indep_null_count": bank["n_indep"],
        "control_count": 2, "all_required_controls_present": bool(controls_present)}

    # ---- section 4: separation_summary ----
    w_S = [e["S"] for e in entries if e["group"] == "winder"]
    w_P = [e["PSC"] for e in entries if e["group"] == "winder"]
    n_S = [e["S"] for e in entries if e["group"] == "nonwinder"]
    n_P = [e["PSC"] for e in entries if e["group"] == "nonwinder"]
    t_S = [e["S"] for e in entries if e["group"] == "traj_null"]
    separation_summary = {
        "coherent_winder_S_range": [round(min(w_S), 4), round(max(w_S), 4)],
        "coherent_winder_PSC_range": [round(min(w_P), 4), round(max(w_P), 4)],
        "non_winder_S_range": [round(min(n_S), 4), round(max(n_S), 4)],
        "non_winder_PSC_range": [round(min(n_P), 4), round(max(n_P), 4)],
        "trajectory_null_S_range": [round(min(t_S), 4), round(max(t_S), 4)] if t_S else None,
        "structureless_S": round(bank["S_struct"], 4), "continuity_S": round(bank["S_cont"], 4),
        "S_PSC_still_separates": bool(min(w_P) >= cs.PSC_FLOOR and max(n_P) < cs.PSC_FLOOR
                                      and min(w_S) - max(n_S) > 0.5)}

    # ---- section 5: residual_interpretation ----
    directional = {"u_directional_delta_rms", "angular_increment_mag", "nr_u_directional_delta_rms",
                   "nr_angular_increment_mag"}
    per_channel_spectral = {"rg_centroid", "by_centroid", "rg_spread", "by_spread",
                            "nr_rg_centroid", "nr_by_centroid", "nr_rg_spread", "nr_by_spread"}
    rem = set(remaining_failures)
    axes = []
    if rem & directional:
        axes.append("directional movement")
    if rem & per_channel_spectral:
        axes.append("per-channel spectral/std geometry")
    residual_interpretation = {
        "remaining_failures": remaining_failures,
        "controlled_or_explained_failures": resolved_or_explained,
        "remaining_axes": axes,
        "note": ("After the spectral_centroid and by_std confounds are controlled/explained, the surviving §7 "
                 "failures are the " + " + ".join(axes) + " axis -- the pooled covariance between winding (S) and "
                 "directional / per-channel-spectral geometry that v1.6/v1.8 localized to the nulls/controls "
                 "(the open validity-surface question). This is NOT a descriptor-validity, vision, or "
                 "temporal-order claim." if axes else
                 "No §7 failures remain on the consolidated bank; still NOT a validity/vision/temporal claim.")}

    if anti_proxy_ok:
        classification = "clean"
    elif remaining_failures:
        classification = "residual_failures_remain"
    else:
        classification = "unresolved"

    integrated_residual_summary = {
        "verdict": verdict, "anti_proxy_ok": anti_proxy_ok,
        "first_pass_structure_validity_claim_allowed": bool(verdict == "PASS"),
        "temporal_claim_allowed": False,
        "remaining_failures": remaining_failures, "resolved_or_explained_failures": resolved_or_explained,
        "classification": classification}

    return {"diagnostic": "v2.1 integrated residual map (reuses frozen v0.7/v0.8 + v1.4/v1.9/v2.0, reporting-only)",
            "integrated_residual_summary": integrated_residual_summary,
            "anti_proxy_failure_map": anti_proxy_failure_map,
            "deconfounded_bank_summary": deconfounded_bank_summary,
            "separation_summary": separation_summary,
            "residual_interpretation": residual_interpretation,
            "reporting_only": True,
            "first_pass_structure_validity_claim_allowed": bool(verdict == "PASS"),
            "temporal_claim_allowed": False}


if __name__ == "__main__":
    r = run()
    s = r["integrated_residual_summary"]
    print("verdict", s["verdict"], "| anti_proxy_ok", s["anti_proxy_ok"], "| classification", s["classification"])
    print("bank:", r["deconfounded_bank_summary"]["bank_size"], "winders",
          r["deconfounded_bank_summary"]["winder_count"], "nonwinders",
          r["deconfounded_bank_summary"]["non_winder_count"], "traj_nulls",
          r["deconfounded_bank_summary"]["traj_null_count"], "all_controls",
          r["deconfounded_bank_summary"]["all_required_controls_present"])
    print("\nanti_proxy_failure_map:")
    for d in r["anti_proxy_failure_map"]:
        print("  %-26s rho=%+.3f %-4s %-22s %s" % (d["stat"], d["rho"], d["gate"], d["status"], d["evidence_note"]))
    print("\nresolved_or_explained:", s["resolved_or_explained_failures"])
    print("remaining_failures:", s["remaining_failures"])
    print("\nseparation:", r["separation_summary"]["S_PSC_still_separates"],
          "winder S", r["separation_summary"]["coherent_winder_S_range"],
          "nonwinder S", r["separation_summary"]["non_winder_S_range"])
    print("\nresidual_interpretation:", r["residual_interpretation"]["note"])
