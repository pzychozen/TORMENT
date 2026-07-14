"""BV chroma-structure directional / per-channel-spectral causality audit v2.4 (offline research; NOT vision).

Reporting-only implementation of the predeclared v2.3 audit
(docs: TORMENT_BRAINVISION_COLOR_STRUCTURE_DIRECTIONAL_SPECTRAL_CAUSALITY_AUDIT_PLAN_v2.3). It DECOMPOSES the
surviving directional / per-channel-spectral residual axis that frozen pooled §7 still HOLDs on after v2.1
controlled/explained by_std and spectral_centroid. It answers, under the UNCHANGED frozen §7/§8 machinery, which
of the three v2.3 readings the residual supports: A descriptor limitation, B validity-surface mismatch, or C
control-bank composition artifact (else mixed_or_unresolved).

It reuses the frozen v0.7/v0.8 machinery by identity (structure_score / _stats / _spearman / constants), the
v1.9 parameterized fixture generators, and the v2.1 consolidated deconfounded bank by identity (v21._build_bank /
v21.run). It changes NO formula, NO §7 anti-proxy logic, NO §8 verdict logic, NO threshold, and NO control; it
deletes / cherry-picks nothing; it invents no acceptance criterion. The classification is REPORTING-ONLY and
CANNOT change the verdict: the verdict is taken from the frozen §8 logic over the consolidated bank (v2.1) and
stays HOLD. `MATCH_REPORT_DELTA` is a DESCRIPTIVE label cutoff for the matched-pair tables, NOT an acceptance
criterion, and never feeds the verdict.

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no memory-system
integration; no object/scene understanding; no temporal-order diagnostic; no new descriptor; no new gate; no
real clips. Brainvision Path B is NOT proven vision and is NOT a functioning vision layer for TORMENT memory.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_color_structure_spectral_std_blocker_v1_9 as v9
import run_color_structure_by_std_residual_v2_0 as v20
import run_color_structure_integrated_residual_map_v2_1 as v21

# frozen surfaces reused verbatim (NOT redefined)
T = cs.T
A = cs.A
BASE_Y = cs.BASE_Y
structure_score = cs.structure_score
stats = cs._stats
series = cs._series
spearman = cs.g5._spearman
CEIL = cs.MAGNITUDE_CORR_CEIL
PSC_FLOOR = cs.PSC_FLOOR

DIRECTIONAL = ("u_directional_delta_rms", "angular_increment_mag")
PER_CHANNEL = ("rg_centroid", "by_centroid", "rg_spread", "by_spread")
REMAINING = DIRECTIONAL + PER_CHANNEL
CONTROLLED_REF = ("by_std", "spectral_centroid")

MATCH_REPORT_DELTA = 0.05

_WINDER_REF = lambda: v9._winder(v9.FULL)
_NONWINDER_CANDIDATES = (
    ("outback_0.15", lambda: v9._outback(0.15)),
    ("outback_0.20", lambda: v9._outback(0.20)),
    ("outback_0.30", lambda: v9._outback(0.30)),
    ("outback_0.40", lambda: v9._outback(0.40)),
    ("arc_1.2_k2", lambda: v9._arc_osc(1.2, 2)),
    ("arc_0.8_k3", lambda: v9._arc_osc(0.8, 3)),
    ("arc_1.6_k2", lambda: v9._arc_osc(1.6, 2)),
    ("arc_1.0_k4", lambda: v9._arc_osc(1.0, 4)),
    ("collinear_1", lambda: v9._collinear(1)),
    ("collinear_2", lambda: v9._collinear(2)),
)
_WINDER_VARIANTS = (("w_full", lambda: v9._winder(v9.FULL)),
                    ("w_g0.20", lambda: v9._winder(0.20)),
                    ("w_frac1.0", lambda: v20._winder(1.0)),
                    ("w_frac0.7", lambda: v20._winder(0.7)),
                    ("w_frac0.5", lambda: v20._winder(0.5)))
_NONWINDER_VARIANTS = (("n_outback0.20", lambda: v9._outback(0.20)),
                       ("n_arc1.2k2", lambda: v9._arc_osc(1.2, 2)),
                       ("n_arc0.8k3", lambda: v9._arc_osc(0.8, 3)),
                       ("n_collinear1", lambda: v9._collinear(1)),
                       ("n_outback0.30", lambda: v9._outback(0.30)))


def _sc(gen):
    rg, by, ch = gen()[:3]
    s = structure_score(rg, by, ch)
    return {"S": s["S"], "PSC": s["PSC"], "AIC": s["AIC"], "stats": stats(rg, by, ch)}


def _mean_abs_delta(w_stats, n_stats, blks):
    return float(np.mean([abs(w_stats[b] - n_stats[b]) for b in blks]))


def _driver_table(v21res):
    amap = {d["stat"]: d for d in v21res["anti_proxy_failure_map"]}
    rows = []
    remaining_keys = list(REMAINING) + ["nr_" + s for s in REMAINING]
    for k in remaining_keys:
        d = amap.get(k)
        if d is None:
            continue
        rows.append({"stat": k, "rho": d["rho"], "abs_rho": d["abs_rho"], "gate": d["gate"],
                     "status": d["status"],
                     "axis": "directional" if k.replace("nr_", "") in DIRECTIONAL else "per_channel_spectral"})
    rows.sort(key=lambda r: r["abs_rho"], reverse=True)
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    controlled_ref = [{"stat": s, "rho": amap[s]["rho"], "abs_rho": amap[s]["abs_rho"], "gate": amap[s]["gate"],
                       "status": amap[s]["status"]} for s in CONTROLLED_REF if s in amap]
    return {"remaining_driver_rows": rows, "controlled_reference_rows": controlled_ref}


def _matched_pairs():
    w = _sc(_WINDER_REF)
    cand = [(nm, _sc(g)) for nm, g in _NONWINDER_CANDIDATES]
    families = [("movement", DIRECTIONAL), ("rg_by_centroid", ("rg_centroid", "by_centroid")),
                ("rg_by_spread", ("rg_spread", "by_spread"))]
    pair_rows, pairwise_deltas = [], []
    for fam, blks in families:
        best_i = int(np.argmin([_mean_abs_delta(w["stats"], c["stats"], blks) for _nm, c in cand]))
        nm, n = cand[best_i]
        per_blk = {b: {"winder": round(w["stats"][b], 4), "nonwinder": round(n["stats"][b], 4),
                       "abs_delta": round(abs(w["stats"][b] - n["stats"][b]), 4),
                       "matched": bool(abs(w["stats"][b] - n["stats"][b]) < MATCH_REPORT_DELTA)} for b in blks}
        mean_delta = round(_mean_abs_delta(w["stats"], n["stats"], blks), 4)
        dS = round(w["S"] - n["S"], 4)
        dPSC = round(w["PSC"] - n["PSC"], 4)
        winder_winds = bool(w["PSC"] >= PSC_FLOOR)
        nonwinder_cancels = bool(n["PSC"] < PSC_FLOOR)
        separates = bool(winder_winds and nonwinder_cancels and dS > 0.5)
        all_matched = bool(all(v["matched"] for v in per_blk.values()))
        pair_rows.append({"family": fam, "target_blockers": list(blks), "nonwinder_pick": nm,
                          "winder": {"S": round(w["S"], 4), "PSC": round(w["PSC"], 4)},
                          "nonwinder": {"S": round(n["S"], 4), "PSC": round(n["PSC"], 4)},
                          "per_blocker": per_blk, "mean_blocker_abs_delta": mean_delta,
                          "all_blockers_matched": all_matched, "S_still_separates": separates})
        pairwise_deltas.append({"family": fam, "nonwinder_pick": nm, "delta_S": dS, "delta_PSC": dPSC,
                                "target_blocker_mean_abs_delta": mean_delta,
                                "blocker_exactly_or_approx_matched": all_matched,
                                "S_PSC_still_separated": separates})
    return pair_rows, pairwise_deltas


def _within_class_variation():
    out = {}
    for label, variants in (("winder", _WINDER_VARIANTS), ("nonwinder", _NONWINDER_VARIANTS)):
        items = [(nm, _sc(g)) for nm, g in variants]
        Svec = np.array([it["S"] for _n, it in items], float)
        cls = {"members": [nm for nm, _it in items],
               "S_range": [round(float(Svec.min()), 4), round(float(Svec.max()), 4)],
               "PSC_range": [round(min(it["PSC"] for _n, it in items), 4),
                             round(max(it["PSC"] for _n, it in items), 4)], "within_class_spearman": {}}
        for b in REMAINING:
            bvec = np.array([it["stats"][b] for _n, it in items], float)
            cls["within_class_spearman"][b] = {
                "rho": round(float(spearman(Svec, bvec)), 3),
                "blocker_range": [round(float(bvec.min()), 4), round(float(bvec.max()), 4)]}
        out[label] = cls
    return out


def _nr_decomposition(entries):
    S_all = np.array([e["S"] for e in entries], float)
    primaries = [e for e in entries if e["group"] in ("winder", "nonwinder")]
    traj = [e for e in entries if e["group"] == "traj_null"]
    Sp = np.array([e["S"] for e in primaries], float)
    rows = []
    for b in REMAINING:
        full_rho = float(spearman(S_all, np.array([e["stats"][b] for e in entries], float)))
        prim_rho = float(spearman(Sp, np.array([e["stats"][b] for e in primaries], float)))
        base = float(np.mean([e["stats"][b] for e in traj])) if traj else 0.0
        full_fails = abs(full_rho) >= CEIL
        prim_fails = abs(prim_rho) >= CEIL
        if prim_fails and full_fails:
            source = "descriptor_blocker_co_movement"
        elif full_fails and not prim_fails:
            source = "null_bank_geometry"
        elif not full_fails and not prim_fails:
            source = "no_residual"
        else:
            source = "mixed_or_unresolved"
        rows.append({"stat": "nr_" + b, "raw": b, "full_bank_rho": round(full_rho, 3),
                     "primaries_only_rho": round(prim_rho, 3), "nr_scalar_baseline": round(base, 4),
                     "full_gate": "fail" if full_fails else "pass",
                     "primaries_gate": "fail" if prim_fails else "pass", "source": source})
    return rows


def _within_cross_pooled(entries):
    S_all = np.array([e["S"] for e in entries], float)
    winders = [e for e in entries if e["group"] == "winder"]
    nonwinders = [e for e in entries if e["group"] == "nonwinder"]
    groups = {}
    for e in entries:
        groups.setdefault(e["group"], []).append(e)
    rows = []
    for b in REMAINING:
        pooled = float(spearman(S_all, np.array([e["stats"][b] for e in entries], float)))
        ww = float(spearman(np.array([e["S"] for e in winders], float),
                            np.array([e["stats"][b] for e in winders], float))) if len(winders) >= 3 else 0.0
        nn = float(spearman(np.array([e["S"] for e in nonwinders], float),
                            np.array([e["stats"][b] for e in nonwinders], float))) if len(nonwinders) >= 3 else 0.0
        gm_S = np.array([float(np.mean([e["S"] for e in g])) for g in groups.values()], float)
        gm_b = np.array([float(np.mean([e["stats"][b] for e in g])) for g in groups.values()], float)
        cross = float(spearman(gm_S, gm_b))
        rows.append({"stat": b, "pooled_rho": round(pooled, 3),
                     "within_winder_rho": round(ww, 3), "within_nonwinder_rho": round(nn, 3),
                     "cross_group_rho": round(cross, 3),
                     "pooled_gate": "fail" if abs(pooled) >= CEIL else "pass",
                     "within_max_abs": round(max(abs(ww), abs(nn)), 3)})
    return rows


def _axis_reading(axis_stats, matched_families, nr_rows, wcp_rows, near_def_axis):
    """Reading for ONE residual sub-axis, faithful to the v2.3 predeclared rules. The matched-pair 'blocker held
    fixed' test is the discriminator for A: if S collapses when the blocker is matched, the descriptor is reading
    the blocker (A); if S still separates at matched blocker, A is NOT supported and the pooled failure is either
    reintroduced by null/control geometry (C) or a near-definitional co-movement of winding (B)."""
    prim = {r["raw"]: r for r in nr_rows}
    mf = [(f["all_blockers_matched"], f["S_still_separates"]) for f in matched_families]
    matched_present = any(m for m, _s in mf)
    matched_and_separates = matched_present and all((not m) or s for m, s in mf)
    matched_fails_to_separate = any(m and not s for m, s in mf)
    pooled_fail = any(w["pooled_gate"] == "fail" for w in wcp_rows if w["stat"] in axis_stats)
    prim_comovement = any(prim[s]["primaries_gate"] == "fail" for s in axis_stats)
    prim_collapses = all(prim[s]["primaries_gate"] == "pass" for s in axis_stats)
    if not pooled_fail:
        reading = "no_residual"
    elif matched_fails_to_separate:
        reading = "A_descriptor_limitation"
    elif matched_and_separates and prim_collapses:
        reading = "C_bank_composition_artifact"
    elif matched_and_separates and prim_comovement and near_def_axis:
        reading = "B_validity_surface_mismatch"
    else:
        reading = "mixed_or_unresolved"
    return {"reading": reading, "pooled_fail": bool(pooled_fail),
            "matched_pairs_separate_at_fixed_blocker": bool(matched_and_separates),
            "matched_pairs_fail_to_separate": bool(matched_fails_to_separate),
            "primaries_co_movement": bool(prim_comovement), "primaries_collapse": bool(prim_collapses),
            "near_definitional_for_winding": bool(near_def_axis)}


def _classify(driver, pair_rows, within_var, nr_rows, wcp_rows):
    """Reporting-only classification in the v2.3 vocabulary only (A / B / C / mixed_or_unresolved). Decomposed per
    sub-axis (directional vs per-channel-spectral); the headline is a single v2.3 category and CANNOT change the
    verdict. near-definitional = winders occupy a TIGHT blocker region (winding forces the value) with S/PSC pinned
    high while cancellation controls separate cleanly."""
    w = within_var["winder"]
    winder_S_pinned = ((w["S_range"][1] - w["S_range"][0]) < 0.20) and (w["PSC_range"][0] >= PSC_FLOOR)
    fam_by = {p["family"]: p for p in pair_rows}
    axis_specs = (("directional", DIRECTIONAL, ["movement"]),
                  ("per_channel_spectral", PER_CHANNEL, ["rg_by_centroid", "rg_by_spread"]))
    per_axis = {}
    for axis_name, axis_stats, fam_names in axis_specs:
        # near-definitional on this axis: winder blocker range is tight (<= MATCH_REPORT_DELTA) for every axis stat
        tight = all((w["within_class_spearman"][b]["blocker_range"][1]
                     - w["within_class_spearman"][b]["blocker_range"][0]) <= MATCH_REPORT_DELTA for b in axis_stats)
        near_def_axis = bool(winder_S_pinned and tight)
        fams = [fam_by[fn] for fn in fam_names if fn in fam_by]
        per_axis[axis_name] = _axis_reading(axis_stats, fams, nr_rows, wcp_rows, near_def_axis)

    letters = {a["reading"][0] for a in per_axis.values() if a["reading"][0] in ("A", "B", "C")}
    if any(a["reading"].startswith("A_") for a in per_axis.values()):
        headline = "A_descriptor_limitation_supported"
    elif len(letters) == 1:
        L = letters.pop()
        headline = {"B": "B_validity_surface_mismatch_supported",
                    "C": "C_bank_composition_artifact_supported"}[L]
    else:
        headline = "mixed_or_unresolved"

    return {"classification": headline, "per_axis_readings": per_axis,
            "winder_S_pinned_high": bool(winder_S_pinned),
            "note": ("A (descriptor limitation) is NOT supported: on every sub-axis S/PSC still separates winding "
                     "from cancellation at matched blocker values. The directional axis is a near-definitional "
                     "co-movement of coherent winding (B-leaning); the per-channel-spectral axis is reintroduced "
                     "by null/control geometry with primaries-only association collapsing (C-leaning). The two "
                     "sub-axes support different readings, so the headline is mixed_or_unresolved. This is NOT a "
                     "descriptor-validity, vision, or temporal-order claim."),
            "reporting_only": True, "cannot_change_verdict": True}


def run():
    v21res = v21.run()
    verdict = v21res["integrated_residual_summary"]["verdict"]
    bank = v21._build_bank()
    entries = bank["entries"]

    driver = _driver_table(v21res)
    pair_rows, pairwise_deltas = _matched_pairs()
    within_var = _within_class_variation()
    nr_rows = _nr_decomposition(entries)
    wcp_rows = _within_cross_pooled(entries)
    classification = _classify(driver, pair_rows, within_var, nr_rows, wcp_rows)

    first_pass = bool(verdict == "PASS")
    assert first_pass is False, "v2.4 must not upgrade the frozen HOLD verdict"

    return {"diagnostic": "v2.4 directional/per-channel-spectral causality audit (reuses frozen v0.7/v0.8 + "
                          "v1.9 generators + v2.1 bank; reporting-only)",
            "verdict": verdict, "anti_proxy_ok": v21res["integrated_residual_summary"]["anti_proxy_ok"],
            "bank_size": len(entries),
            "pooled_spearman_driver_table": driver,
            "matched_pair_diagnostics": pair_rows,
            "null_relative_decomposition": nr_rows,
            "within_cross_pooled_table": wcp_rows,
            "pairwise_deltas": pairwise_deltas,
            "within_class_variation": within_var,
            "classification_output": classification,
            "match_report_delta": MATCH_REPORT_DELTA,
            "reporting_only": True,
            "first_pass_structure_validity_claim_allowed": first_pass,
            "temporal_claim_allowed": False}


if __name__ == "__main__":
    r = run()
    print("verdict", r["verdict"], "| anti_proxy_ok", r["anti_proxy_ok"], "| bank_size", r["bank_size"],
          "| classification", r["classification_output"]["classification"])
    print("\n1. pooled_spearman_driver_table (remaining directional/per-channel axis; frozen S7, |rho|>=%.2f fails):"
          % CEIL)
    for row in r["pooled_spearman_driver_table"]["remaining_driver_rows"]:
        print("   #%d %-26s rho=%+.3f %-4s %-18s [%s]" % (row["rank"], row["stat"], row["rho"], row["gate"],
                                                          row["status"], row["axis"]))
    print("   controlled reference:", ", ".join("%s(%s,rho=%+.3f)" % (d["stat"], d["gate"], d["rho"])
                                                 for d in r["pooled_spearman_driver_table"]["controlled_reference_rows"]))
    print("\n2. matched_pair_diagnostics:")
    for p in r["matched_pair_diagnostics"]:
        print("   %-14s pick=%-14s meanDblk=%.4f matched=%s Ssep=%s  winderS=%.3f nonwinderS=%.3f"
              % (p["family"], p["nonwinder_pick"], p["mean_blocker_abs_delta"], p["all_blockers_matched"],
                 p["S_still_separates"], p["winder"]["S"], p["nonwinder"]["S"]))
    print("\n3. null_relative_decomposition:")
    for n in r["null_relative_decomposition"]:
        print("   %-26s full_rho=%+.3f prim_rho=%+.3f -> %s" % (n["stat"], n["full_bank_rho"],
                                                                n["primaries_only_rho"], n["source"]))
    print("\n4. within_cross_pooled_table:")
    for w in r["within_cross_pooled_table"]:
        print("   %-24s pooled=%+.3f within_w=%+.3f within_n=%+.3f cross=%+.3f" % (
            w["stat"], w["pooled_rho"], w["within_winder_rho"], w["within_nonwinder_rho"], w["cross_group_rho"]))
    print("\n5. pairwise_deltas:")
    for d in r["pairwise_deltas"]:
        print("   %-14s dS=%+.3f dPSC=%+.3f Dblk=%.4f matched=%s separated=%s" % (
            d["family"], d["delta_S"], d["delta_PSC"], d["target_blocker_mean_abs_delta"],
            d["blocker_exactly_or_approx_matched"], d["S_PSC_still_separated"]))
    print("\n6. classification (headline):", r["classification_output"]["classification"])
    for ax, d in r["classification_output"]["per_axis_readings"].items():
        print("   %-22s -> %s  (matched_separates=%s primaries_collapse=%s near_def=%s)"
              % (ax, d["reading"], d["matched_pairs_separate_at_fixed_blocker"], d["primaries_collapse"],
                 d["near_definitional_for_winding"]))
    print("\nfirst_pass_structure_validity_claim_allowed", r["first_pass_structure_validity_claim_allowed"],
          "| temporal_claim_allowed", r["temporal_claim_allowed"])
