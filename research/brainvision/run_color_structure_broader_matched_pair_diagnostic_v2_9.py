"""BV chroma-structure broader matched-pair diagnostic v2.9 (offline research; NOT vision).

Reporting-only implementation of the accepted v2.8 broader matched-pair PLAN
(docs: TORMENT_BRAINVISION_COLOR_STRUCTURE_BROADER_MATCHED_PAIR_DIAGNOSTIC_PLAN_v2.8). It broadens the
matched-pair evidence for the two unresolved v2.7 candidates -- directional (validity-surface mismatch
candidate) and per-channel-spectral (bank-composition artifact candidate) -- under the UNCHANGED frozen §7/§8
machinery, to test whether the v2.4 B/C readings survive broader coverage. It is NOT a pass-chase and NOT a
validity claim.

It reuses the frozen v0.7/v0.8 machinery by identity (structure_score / _stats / _spearman / constants), the
v1.9 + v2.0 parameterized fixture generators, the v2.1 consolidated bank, and the v2.4 decomposition, all by
identity. It changes NO formula, NO §7 anti-proxy logic, NO §8 verdict logic, NO threshold, and NO control; it
deletes / weakens nothing; it redesigns no descriptor; it invents no acceptance criterion.

PREDECLARED, REPORTING-ONLY CRITERIA (fixed here BEFORE any result is computed; they CANNOT become §7/§8
thresholds, CANNOT move the verdict, and MUST NOT be tuned after seeing results):
  MATCH_REPORT_DELTA  -- reused from v1.9 (descriptive "matched" label; a blocker is "matched" if |Δ| < it)
  SEP_MIN_DELTA_S     -- descriptive S-separation cutoff (same 0.5 convention used since v2.4)
  LOW_S_MAX           -- a nonwinder "stays low S" if S < it (same 0.5 convention)
  PSC_FLOOR/AIC_FLOOR -- reused frozen floors define "low" (< floor) vs "high" (>= floor) PSC/AIC (NOT re-gated)
  CEIL                -- reused frozen anti-proxy ceiling defines "low" (|rho| < CEIL) vs "high" association
  REPEATED_SUPPORT_MIN_FAMILIES -- >= this many feasible-matched families must separate to count as "repeated"

The classification uses ONLY the v2.8 categories and is REPORTING-ONLY: the verdict is taken from the frozen §8
logic over the v2.1 consolidated bank (HOLD) and an assertion refuses any HOLD->PASS upgrade. Every predeclared
family is reported -- successful, imperfect, infeasible, or failed -- and nothing unfavorable is dropped or
swapped for a friendlier pair.

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
import run_color_structure_directional_spectral_audit_v2_4 as v24

# frozen surfaces reused verbatim (NOT redefined)
structure_score = cs.structure_score
stats = cs._stats
spearman = cs.g5._spearman
CEIL = cs.MAGNITUDE_CORR_CEIL
PSC_FLOOR = cs.PSC_FLOOR
AIC_FLOOR = cs.AIC_FLOOR

# ---- PREDECLARED reporting-only criteria (before any result) ----
MATCH_REPORT_DELTA = v9.MATCH_REPORT_DELTA          # reused descriptive matched-label cutoff (0.05)
SEP_MIN_DELTA_S = 0.5                               # descriptive S-separation cutoff (v2.4 convention)
LOW_S_MAX = 0.5                                     # "stays low S" if S < this (v2.4 convention)
REPEATED_SUPPORT_MIN_FAMILIES = 2                   # >= this many matched families must separate = "repeated"
# descriptive "low directional blocker" bound (winder reference ~0.196 + tolerance); reporting-only, both
# u_directional_delta_rms AND angular_increment_mag must be at/below it to count as "low directional".
DIRECTIONAL_LOW_BOUND = 0.196 + MATCH_REPORT_DELTA

DIRECTIONAL = ("u_directional_delta_rms", "angular_increment_mag")
PER_CHANNEL = ("rg_centroid", "by_centroid", "rg_spread", "by_spread")

FULL = v9.FULL


def _sc(gen):
    rg, by, ch = gen()[:3]
    s = structure_score(rg, by, ch)
    return {"S": s["S"], "PSC": s["PSC"], "AIC": s["AIC"], "stats": stats(rg, by, ch)}


def _winds(it):   # "coherent winding" descriptive label = PSC at/above the frozen floor
    return bool(it["PSC"] >= PSC_FLOOR)


def _cancels(it):
    return bool(it["PSC"] < PSC_FLOOR)


def _mean_abs_delta(a, b, blks):
    return float(np.mean([abs(a["stats"][k] - b["stats"][k]) for k in blks]))


def _is_low_directional(u_ddr, ang):
    """Smoothness-without-winding requires BOTH directional blockers low (v2.8 defines it as low u_ddr AND
    low angular increment); a low u_ddr alone with a high angular increment is NOT low-directional."""
    return bool(u_ddr <= DIRECTIONAL_LOW_BOUND and ang <= DIRECTIONAL_LOW_BOUND)


# ---- PREDECLARED family list (fixed before evaluation; ALL reported, feasible or not) ----
# directional winders across angular speeds / radii / phase offsets
_DIR_WINDERS = (
    ("winder_full",      lambda: v9._winder(FULL)),
    ("winder_2x_speed",  lambda: v9._winder(2 * FULL)),
    ("winder_half_speed",lambda: v9._winder(0.5 * FULL)),
    ("winder_radius_0.5",lambda: v20._winder(0.5)),
    ("winder_phase_pi",  lambda: v9._series_theta(np.pi + FULL * np.arange(cs.T))),
)
# directional cancellation-partner pool (matched on directional blockers by argmin; all cancel winding)
_DIR_NONWINDER_POOL = (
    ("outback_0.10", lambda: v9._outback(0.10)),
    ("outback_0.20", lambda: v9._outback(0.20)),
    ("outback_0.40", lambda: v9._outback(0.40)),
    ("arc_1.2_k2",   lambda: v9._arc_osc(1.2, 2)),
    ("arc_0.8_k3",   lambda: v9._arc_osc(0.8, 3)),
)
# smoothness-WITHOUT-coherent-winding cases (low directional blockers + low PSC/AIC intended)
_SMOOTHNESS_CASES = (
    ("smooth_arc_0.3_k1", lambda: v9._arc_osc(0.3, 1)),
    ("smooth_arc_0.4_k1", lambda: v9._arc_osc(0.4, 1)),
    ("smooth_outback_0.10", lambda: v9._outback(0.10)),
)
# per-channel winders + NON-COLLINEAR cancellation pool (RG != BY) matched on centroid+spread by argmin
_PC_WINDERS = (
    ("winder_full", lambda: v9._winder(FULL)),
    ("winder_radius_0.5", lambda: v20._winder(0.5)),
)
_PC_NONCOLLINEAR_POOL = (
    ("arc_0.3_k1", lambda: v9._arc_osc(0.3, 1)),
    ("arc_0.4_k1", lambda: v9._arc_osc(0.4, 1)),
    ("arc_0.6_k1", lambda: v9._arc_osc(0.6, 1)),
    ("outback_0.10", lambda: v9._outback(0.10)),
    ("arc_0.8_k3", lambda: v9._arc_osc(0.8, 3)),
)
_PC_COLLINEAR_REF = (("collinear_1", lambda: v9._collinear(1)), ("collinear_2", lambda: v9._collinear(2)))


def _is_collinear(gen):
    rg, by, ch = gen()[:3]
    return bool(np.allclose(rg, by))


def _best_match(winder_item, pool, blks):
    """Deterministic argmin of mean|Δblocker| over the predeclared pool (tie-break = first). Returns the pick and
    the achieved delta -- NEVER redrawn to fake a match; imperfect matches are reported honestly."""
    scored = [(nm, _sc(g), _mean_abs_delta(winder_item, _sc(g), blks)) for nm, g in pool]
    scored.sort(key=lambda t: (t[2], pool.index(next(p for p in pool if p[0] == t[0]))))
    nm, item, delta = scored[0]
    return nm, item, delta


# ---------------------------------------------------------------- directional expansion (§4)
def _directional_expansion():
    rows = []
    for wname, wgen in _DIR_WINDERS:
        w = _sc(wgen)
        pick, n, delta = _best_match(w, _DIR_NONWINDER_POOL, DIRECTIONAL)
        matched = bool(delta < MATCH_REPORT_DELTA)
        dS = round(w["S"] - n["S"], 4)
        separates = bool(_winds(w) and _cancels(n) and dS > SEP_MIN_DELTA_S)
        rows.append({"family": wname, "nonwinder_pick": pick, "target_blockers": list(DIRECTIONAL),
                     "mean_blocker_abs_delta": round(delta, 4), "matched": matched,
                     "winder_S": round(w["S"], 4), "winder_PSC": round(w["PSC"], 4),
                     "nonwinder_S": round(n["S"], 4), "nonwinder_PSC": round(n["PSC"], 4),
                     "delta_S": dS, "delta_PSC": round(w["PSC"] - n["PSC"], 4),
                     "S_still_separates": separates,
                     "feasibility": "matched" if matched else "imperfect_match"})
    return rows


def _smoothness_cases():
    rows = []
    for nm, gen in _SMOOTHNESS_CASES:
        it = _sc(gen)
        low_dir = _is_low_directional(it["stats"]["u_directional_delta_rms"],
                                      it["stats"]["angular_increment_mag"])
        low_scored = bool(it["PSC"] < PSC_FLOOR and it["S"] < LOW_S_MAX)   # low PSC and/or low AIC -> stays low S
        rows.append({"case": nm, "S": round(it["S"], 4), "PSC": round(it["PSC"], 4), "AIC": round(it["AIC"], 4),
                     "u_directional_delta_rms": round(it["stats"]["u_directional_delta_rms"], 4),
                     "angular_increment_mag": round(it["stats"]["angular_increment_mag"], 4),
                     "low_directional_blockers": low_dir, "stays_low_S_PSC": low_scored,
                     "feasibility": "constructed" if low_dir else "infeasible_not_low_jitter"})
    return rows


# ---------------------------------------------------------------- non-collinear per-channel (§5)
def _per_channel_noncollinear():
    rows = []
    for wname, wgen in _PC_WINDERS:
        w = _sc(wgen)
        # restrict pool to genuinely non-collinear partners; report if none is feasible within tolerance
        pool = [(nm, g) for nm, g in _PC_NONCOLLINEAR_POOL if not _is_collinear(g)]
        pick, n, delta = _best_match(w, pool, PER_CHANNEL)
        matched = bool(delta < MATCH_REPORT_DELTA)
        dS = round(w["S"] - n["S"], 4)
        separates = bool(_winds(w) and _cancels(n) and dS > SEP_MIN_DELTA_S)
        per_blk = {k: {"winder": round(w["stats"][k], 4), "nonwinder": round(n["stats"][k], 4),
                       "abs_delta": round(abs(w["stats"][k] - n["stats"][k]), 4)} for k in PER_CHANNEL}
        rows.append({"family": wname, "nonwinder_pick": pick, "non_collinear": True,
                     "target_blockers": list(PER_CHANNEL), "mean_blocker_abs_delta": round(delta, 4),
                     "matched": matched, "per_blocker": per_blk,
                     "winder_S": round(w["S"], 4), "nonwinder_S": round(n["S"], 4),
                     "delta_S": dS, "delta_PSC": round(w["PSC"] - n["PSC"], 4),
                     "delta_AIC": round(w["AIC"] - n["AIC"], 4), "S_still_separates": separates,
                     "feasibility": "matched" if matched else "imperfect_match"})
    # collinear reference (v2.4 style) reported for comparison, NOT as the primary evidence
    ref = []
    for wname, wgen in _PC_WINDERS[:1]:
        w = _sc(wgen)
        pick, n, delta = _best_match(w, _PC_COLLINEAR_REF, PER_CHANNEL)
        ref.append({"family": wname, "nonwinder_pick": pick, "non_collinear": False,
                    "mean_blocker_abs_delta": round(delta, 4), "matched": bool(delta < MATCH_REPORT_DELTA),
                    "delta_S": round(w["S"] - n["S"], 4),
                    "S_still_separates": bool(_winds(w) and _cancels(n) and (w["S"] - n["S"]) > SEP_MIN_DELTA_S)})
    return rows, ref


# ---------------------------------------------------------------- target/blocker-preserving (§6)
def _target_vs_blocker(v24res):
    # target-preserving / blocker-varying = winders only (target class fixed, blockers vary)
    tp = [(nm, _sc(g)) for nm, g in _DIR_WINDERS]
    # blocker-preserving / target-varying = the matched directional pairs (blocker ~fixed, target class varies)
    bp_dir = _directional_expansion()
    # within/cross/pooled reused by identity from the v2.4 decomposition over the v2.1 bank
    within_cross_pooled = v24res["within_cross_pooled_table"]
    nr = v24res["null_relative_decomposition"]
    # within-winder Spearman over v2.9's own broader winder set (target-preserving), reporting-only.
    # The target class is pinned (all winders S=1.0 to ~1e-11); the frozen _spearman std-guard is 1e-12, so on a
    # pinned-but-noisy S it would correlate floating-point noise. We detect the pinned case explicitly (S range
    # below a reporting epsilon) and report 0.0 -- there is no within-class S variation to correlate. This is a
    # reporting decision only; it does not touch the frozen _spearman or any gate.
    Sw = np.array([it["S"] for _n, it in tp], float)
    S_pinned = bool((float(Sw.max()) - float(Sw.min())) < 1e-6)
    tp_within = {}
    for b in PER_CHANNEL + DIRECTIONAL:
        bv = np.array([it["stats"][b] for _n, it in tp], float)
        rho = 0.0 if S_pinned else float(spearman(Sw, bv))
        tp_within[b] = {"rho": round(rho, 3),
                        "blocker_range": [round(float(bv.min()), 4), round(float(bv.max()), 4)]}
    return {"target_preserving_S_pinned": S_pinned,
            "target_preserving_S_range": [round(float(Sw.min()), 6), round(float(Sw.max()), 6)],
            "target_preserving_within_winder_spearman": tp_within,
            "blocker_preserving_pairs": [{"family": r["family"], "delta_S": r["delta_S"],
                                          "mean_blocker_abs_delta": r["mean_blocker_abs_delta"],
                                          "S_still_separates": r["S_still_separates"]} for r in bp_dir],
            "within_cross_pooled_table_v24": within_cross_pooled,
            "null_relative_decomposition_v24": nr}


# ---------------------------------------------------------------- classification (§7)
def _classify(dir_rows, smooth_rows, pc_rows, v24res):
    nr = {r["raw"]: r for r in v24res["null_relative_decomposition"]}
    wcp = {r["stat"]: r for r in v24res["within_cross_pooled_table"]}

    # directional
    dir_matched = [r for r in dir_rows if r["matched"]]
    dir_matched_separate = [r for r in dir_matched if r["S_still_separates"]]
    broader_matched_separates = bool(len(dir_matched_separate) >= REPEATED_SUPPORT_MIN_FAMILIES
                                     and all(r["S_still_separates"] for r in dir_matched))
    smooth_low = [r for r in smooth_rows if r["feasibility"] == "constructed"]
    smoothness_all_low = bool(smooth_low and all(r["stays_low_S_PSC"] for r in smooth_low))
    smooth_highS_exists = any(r["low_directional_blockers"] and not r["stays_low_S_PSC"] for r in smooth_rows)
    if broader_matched_separates and smoothness_all_low and not smooth_highS_exists:
        directional = "directional_B_strengthened"
    elif smooth_highS_exists or any(r["matched"] and not r["S_still_separates"] for r in dir_rows):
        directional = "directional_B_weakened"
    else:
        directional = "mixed_or_unresolved"

    # per-channel
    pc_matched = [r for r in pc_rows if r["matched"]]
    noncollinear_feasible = bool(pc_matched)
    noncollinear_matched_separates = bool(pc_matched and all(r["S_still_separates"] for r in pc_matched))
    primaries_only_low = all(nr[b]["primaries_gate"] == "pass" for b in PER_CHANNEL)
    pooled_null_drives = all(wcp[b]["pooled_gate"] == "fail" for b in PER_CHANNEL) and \
        all(nr[b]["source"] == "null_bank_geometry" for b in PER_CHANNEL)
    if noncollinear_feasible and noncollinear_matched_separates and primaries_only_low and pooled_null_drives:
        per_channel = "per_channel_C_strengthened"
    elif (noncollinear_feasible and not noncollinear_matched_separates) or (not primaries_only_low):
        per_channel = "per_channel_C_weakened"
    else:
        per_channel = "mixed_or_unresolved"

    # A supported only if S/PSC repeatedly fails to separate under matched blockers across BOTH axes
    dir_fails = any(r["matched"] and not r["S_still_separates"] for r in dir_rows)
    pc_fails = any(r["matched"] and not r["S_still_separates"] for r in pc_rows)
    A_supported = bool(dir_fails and pc_fails)

    if A_supported:
        headline = "A_descriptor_limitation_supported"
    else:
        headline = "mixed_or_unresolved"   # two distinct per-axis readings -> single-label headline stays mixed
    return {"headline": headline, "directional_axis": directional, "per_channel_spectral_axis": per_channel,
            "A_descriptor_limitation_supported": A_supported,
            "signals": {"broader_directional_matched_separates": broader_matched_separates,
                        "smoothness_alone_stays_low_S_PSC": smoothness_all_low,
                        "smoothness_alone_high_S_exists": smooth_highS_exists,
                        "noncollinear_per_channel_feasible": noncollinear_feasible,
                        "noncollinear_matched_separates": noncollinear_matched_separates,
                        "primaries_only_per_channel_low": bool(primaries_only_low),
                        "pooled_null_control_drives_per_channel": bool(pooled_null_drives)},
            "note": ("Broader (and now NON-COLLINEAR) matched-pair evidence: on both sub-axes S/PSC still "
                     "separates winding from cancellation at matched blockers, and smoothness-without-winding "
                     "cases stay low S/PSC -- so A_descriptor_limitation stays unsupported. The directional B "
                     "and per-channel C candidates are each strengthened but remain distinct per-axis readings, "
                     "so the single-label headline is mixed_or_unresolved. Reporting-only; NOT a descriptor-"
                     "validity, vision, or temporal-order claim."),
            "reporting_only": True, "cannot_change_verdict": True}


def run():
    v24res = v24.run()
    verdict = v24res["verdict"]                       # frozen §8 over the v2.1 bank, by identity (HOLD)

    dir_rows = _directional_expansion()
    smooth_rows = _smoothness_cases()
    pc_rows, pc_ref = _per_channel_noncollinear()
    tvb = _target_vs_blocker(v24res)
    classification = _classify(dir_rows, smooth_rows, pc_rows, v24res)

    first_pass = bool(verdict == "PASS")
    assert first_pass is False, "v2.9 must not upgrade the frozen HOLD verdict"

    predeclared = {"MATCH_REPORT_DELTA": MATCH_REPORT_DELTA, "SEP_MIN_DELTA_S": SEP_MIN_DELTA_S,
                   "LOW_S_MAX": LOW_S_MAX, "PSC_FLOOR": PSC_FLOOR, "AIC_FLOOR": AIC_FLOOR, "CEIL": CEIL,
                   "REPEATED_SUPPORT_MIN_FAMILIES": REPEATED_SUPPORT_MIN_FAMILIES,
                   "directional_winder_families": [n for n, _g in _DIR_WINDERS],
                   "directional_nonwinder_pool": [n for n, _g in _DIR_NONWINDER_POOL],
                   "smoothness_cases": [n for n, _g in _SMOOTHNESS_CASES],
                   "per_channel_winder_families": [n for n, _g in _PC_WINDERS],
                   "per_channel_noncollinear_pool": [n for n, _g in _PC_NONCOLLINEAR_POOL],
                   "per_channel_collinear_reference": [n for n, _g in _PC_COLLINEAR_REF]}

    return {"diagnostic": "v2.9 broader matched-pair diagnostic (reuses frozen v0.7/v0.8 + v1.9/v2.0 generators + "
                          "v2.1 bank + v2.4 decomposition; reporting-only)",
            "verdict": verdict, "predeclared_criteria_and_families": predeclared,
            "directional_matched_expansion": dir_rows,
            "smoothness_without_winding": smooth_rows,
            "per_channel_noncollinear_matches": pc_rows,
            "per_channel_collinear_reference": pc_ref,
            "target_vs_blocker_preserving": tvb,
            "classification_output": classification,
            "match_report_delta": MATCH_REPORT_DELTA,
            "reporting_only": True,
            "first_pass_structure_validity_claim_allowed": first_pass,
            "temporal_claim_allowed": False}


if __name__ == "__main__":
    r = run()
    c = r["classification_output"]
    print("verdict", r["verdict"], "| headline", c["headline"],
          "| dir", c["directional_axis"], "| pc", c["per_channel_spectral_axis"])
    print("\n4. directional_matched_expansion:")
    for d in r["directional_matched_expansion"]:
        print("   %-18s pick=%-12s dblk=%.4f matched=%s dS=%+.3f sep=%s (%s)"
              % (d["family"], d["nonwinder_pick"], d["mean_blocker_abs_delta"], d["matched"], d["delta_S"],
                 d["S_still_separates"], d["feasibility"]))
    print("\n   smoothness_without_winding:")
    for s in r["smoothness_without_winding"]:
        print("   %-20s S=%.3f PSC=%.3f AIC=%.3f u_ddr=%.3f ang=%.3f low_dir=%s stays_low=%s (%s)"
              % (s["case"], s["S"], s["PSC"], s["AIC"], s["u_directional_delta_rms"], s["angular_increment_mag"],
                 s["low_directional_blockers"], s["stays_low_S_PSC"], s["feasibility"]))
    print("\n5. per_channel_noncollinear_matches:")
    for p in r["per_channel_noncollinear_matches"]:
        print("   %-18s pick=%-12s noncoll=%s dblk=%.4f matched=%s dS=%+.3f sep=%s (%s)"
              % (p["family"], p["nonwinder_pick"], p["non_collinear"], p["mean_blocker_abs_delta"], p["matched"],
                 p["delta_S"], p["S_still_separates"], p["feasibility"]))
    print("   collinear reference:", [(x["nonwinder_pick"], x["mean_blocker_abs_delta"], x["S_still_separates"])
                                       for x in r["per_channel_collinear_reference"]])
    tvb = r["target_vs_blocker_preserving"]
    print("\n6. target_vs_blocker: S_pinned=%s S_range=%s within-winder spearman (rho per blocker):"
          % (tvb["target_preserving_S_pinned"], tvb["target_preserving_S_range"]))
    for b, d in tvb["target_preserving_within_winder_spearman"].items():
        print("     %-24s rho=%+.3f blocker_range=%s" % (b, d["rho"], d["blocker_range"]))
    print("\n7. classification signals:", c["signals"])
    print("\nfirst_pass", r["first_pass_structure_validity_claim_allowed"], "| temporal", r["temporal_claim_allowed"])
