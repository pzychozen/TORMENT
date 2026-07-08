"""BV chroma-structure spectral/std blocker diagnostic v1.9 (offline research; NOT runtime/integration; NOT vision).

Attacks the four v1.8 spectral/std blockers directly. The v1.8 pooled-gate audit (edge af39175) found that,
even at exactly matched directional movement, `S` still tracked per-channel spectral/std geometry on the
movement-matched subset:

    spectral_centroid : pooled fail, matched fail
    by_std            : pooled pass, matched fail
    rg_spread         : pooled pass, matched fail
    nr_rg_spread      : pooled pass, matched fail   (= rg_spread minus a constant null baseline)

This diagnostic asks: can `S`/`PSC` still separate coherent chroma winding from cancellation when those four
blocker axes are explicitly CONTROLLED (matched / neutralized) between a winder and its non-winder partner?
It is REPORTING-ONLY. It reuses the frozen v0.7/v0.8 machinery by identity (structure_score / _stats /
_spearman / constants) and the v1.1 + v1.4 fixture style; it changes NO formula, NO §7 anti-proxy logic, NO
§8 verdict logic, NO threshold, and NO control, defines no replacement acceptance criteria, cherry-picks
nothing into a pass, and cannot make the gate pass. The verdict is taken from the frozen §8 logic over the
v1.9 bank and stays HOLD.

If perfect blocker matching is impossible it reports the residual deltas honestly (does not fake a pass, does
not hide the blocker). Outcomes A (S survives blocker control -> blocker weakened), B (S collapses ->
descriptor limitation strengthened), and C (matching fails -> fixture-construction problem) are all acceptable.

`MATCH_REPORT_DELTA` below is a DESCRIPTIVE reporting cutoff for labeling a blocker "matched" in the tables;
it is NOT an acceptance criterion and does NOT feed the verdict (the verdict uses only the frozen §8 logic).

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no memory-system
integration; no object/scene understanding; no temporal-order diagnostic; no new descriptor; no new gate; no
real clips. Brainvision Path B is NOT proven vision and is NOT a functioning vision layer for TORMENT memory.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_color_structure_fixture_bank_v1_1 as fb
import run_color_structure_movement_matched_v1_4 as mm

# frozen surfaces reused verbatim (NOT redefined)
T = cs.T
A = cs.A
BASE_Y = cs.BASE_Y
structure_score = cs.structure_score
stats = cs._stats
series = cs._series
spearman = cs.g5._spearman
CEIL = cs.MAGNITUDE_CORR_CEIL

BLOCKERS = ("spectral_centroid", "by_std", "rg_spread", "nr_rg_spread")
THETA0 = 0.30
MATCH_REPORT_DELTA = 0.05      # descriptive "matched" label cutoff for the tables; NOT an acceptance criterion


def _series_theta(theta, amp=None):
    amp = A * np.ones(T) if amp is None else np.asarray(amp, float)
    theta = np.asarray(theta, float)
    return series(np.full(T, BASE_Y), amp * np.cos(theta), amp * np.sin(theta))


def _winder(g):
    return _series_theta(THETA0 + g * np.arange(T))                    # monotonic theta -> coherent winding


def _arc_osc(delta, k):
    t = np.arange(T)
    return _series_theta(THETA0 + delta * np.sin(2 * np.pi * k * t / T))   # oscillates on circle; cancels winding


def _collinear(f):
    t = np.arange(T)
    x = A * np.cos(2 * np.pi * f * t / T + THETA0)
    return series(np.full(T, BASE_Y), x, x.copy())                     # RG == BY -> collinear; cancels


def _outback(g):
    h = (T - 1) // 2
    d = np.concatenate([np.full(h, g), np.full(T - 1 - h, -g)])
    return _series_theta(np.concatenate([[THETA0], THETA0 + np.cumsum(d)]))   # forward/back -> cancels


# predeclared blocker-controlled pair families (winder vs non-winder; strategy = which blockers it targets)
FULL = 2 * np.pi / T
_PAIRS = (
    ("M_movement_matched", lambda: _winder(0.20), lambda: _outback(0.20),
     "movement-matched only (v1.4 baseline; spectral/std blockers uncontrolled)"),
    ("CC_const_chroma", lambda: _winder(FULL), lambda: _arc_osc(1.2, 2),
     "constant-CHROMA arc oscillator (targets spectral_centroid + by_std)"),
    ("PR_collinear", lambda: _winder(FULL), lambda: _collinear(1),
     "phase-relative collinear (targets by_std + rg_spread/nr_rg_spread)"),
    ("SS_lowamp_arc", lambda: _winder(FULL), lambda: _arc_osc(0.8, 3),
     "narrow arc oscillator (targets spectral_centroid + by_std + rg_spread jointly)"),
)


def _entry(name, gen, group, pair):
    rg, by, ch = gen()[:3]
    s = structure_score(rg, by, ch)
    return {"name": name, "group": group, "pair": pair, "stats": stats(rg, by, ch),
            "S": s["S"], "PSC": s["PSC"], "AIC": s["AIC"]}


def _build_bank():
    """v1.9 §7 bank (winders in-scope + traj/indep nulls + non-winders + continuity + structureless)."""
    ct = series(*cs.continuity_control())
    S_cont = structure_score(ct[0], ct[1], ct[2])["S"]
    st = series(*cs.structureless_control())
    S_struct = structure_score(st[0], st[1], st[2])["S"]
    entries = []
    for i, (pid, wgen, ngen, _strat) in enumerate(_PAIRS):
        entries.append(_entry(pid + "_winder", wgen, "winder", pid))
        entries.append(_entry(pid + "_nonwinder", ngen, "nonwinder", pid))
        wr, wg, wc = wgen()[:3]
        rgp, byp, chp, _r, invalid = fb.traj_null_guarded(wr, wg)
        if not invalid:
            s_traj = structure_score(rgp, byp, chp)
            entries.append({"name": pid + "_winder_traj_null", "group": "traj_null", "pair": pid,
                            "stats": stats(rgp, byp, chp), "S": s_traj["S"], "PSC": s_traj["PSC"],
                            "AIC": s_traj["AIC"]})
            irg, iby, ich, _ic = series(np.full(T, BASE_Y), *cs.null_independent_phase(wr, wg, 4000 + i))
            s_ind = structure_score(irg, iby, ich)
            entries.append({"name": pid + "_winder_indep_null", "group": "indep_null", "pair": pid,
                            "stats": stats(irg, iby, ich), "S": s_ind["S"], "PSC": s_ind["PSC"],
                            "AIC": s_ind["AIC"]})
    entries.append({"name": "continuity_control", "group": "continuity_control", "pair": None,
                    "stats": stats(ct[0], ct[1], ct[2]), "S": S_cont, "PSC": 0.0, "AIC": 0.0})
    entries.append({"name": "structureless_control", "group": "structureless_control", "pair": None,
                    "stats": stats(st[0], st[1], st[2]), "S": S_struct, "PSC": 0.0, "AIC": 0.0})
    return entries, S_cont, S_struct


def run():
    entries, S_cont, S_struct = _build_bank()
    traj_entries = [e for e in entries if e["group"] == "traj_null"]
    base = float(np.mean([e["stats"]["rg_spread"] for e in traj_entries])) if traj_entries else 0.0
    traj_by_pair = {e["pair"]: e for e in traj_entries}

    def _bval(stt, blk):
        return stt["rg_spread"] - base if blk == "nr_rg_spread" else stt[blk]

    win = {e["pair"]: e for e in entries if e["group"] == "winder"}
    non = {e["pair"]: e for e in entries if e["group"] == "nonwinder"}

    # section 1: blocker_match_table
    blocker_match_table = []
    for pid, _wg, _ng, strat in _PAIRS:
        w, n = win[pid], non[pid]
        row = {"pair_id": pid, "strategy": strat,
               "winder": {"S": round(w["S"], 4), "PSC": round(w["PSC"], 4), "AIC": round(w["AIC"], 4)},
               "nonwinder": {"S": round(n["S"], 4), "PSC": round(n["PSC"], 4), "AIC": round(n["AIC"], 4)},
               "blockers": {}, "blocker_abs_delta": {}}
        for blk in BLOCKERS:
            wv, nv = _bval(w["stats"], blk), _bval(n["stats"], blk)
            row["blockers"][blk] = {"winder": round(wv, 4), "nonwinder": round(nv, 4)}
            row["blocker_abs_delta"][blk] = round(abs(wv - nv), 4)
        row["mean_blocker_abs_delta"] = round(float(np.mean(list(row["blocker_abs_delta"].values()))), 4)
        row["all_blockers_matched"] = bool(all(d < MATCH_REPORT_DELTA for d in row["blocker_abs_delta"].values()))
        row["S_separation"] = round(w["S"] - n["S"], 4)
        row["PSC_separation"] = round(w["PSC"] - n["PSC"], 4)
        row["winder_traj_null_S"] = round(traj_by_pair[pid]["S"], 4) if pid in traj_by_pair else None
        blocker_match_table.append(row)

    # section 2: separation_under_blocker_control
    separation = []
    for row in blocker_match_table:
        w, n = win[row["pair_id"]], non[row["pair_id"]]
        winder_winds = w["PSC"] >= cs.PSC_FLOOR
        nonwinder_cancels = n["PSC"] < cs.PSC_FLOOR
        matched = [b for b, d in row["blocker_abs_delta"].items() if d < MATCH_REPORT_DELTA]
        separation.append({
            "pair_id": row["pair_id"], "winder_winds": bool(winder_winds),
            "nonwinder_cancels": bool(nonwinder_cancels),
            "S_still_separates": bool(winder_winds and nonwinder_cancels and row["S_separation"] > 0.5),
            "matched_blockers": matched, "all_blockers_matched": row["all_blockers_matched"],
            "mean_blocker_abs_delta": row["mean_blocker_abs_delta"]})

    # section 3: blocker_residuals (best achieved delta per blocker + whether it still explains S across the pool)
    pool = [e for e in entries if e["group"] in ("winder", "nonwinder")]
    Svec = np.array([e["S"] for e in pool], float)
    blocker_residuals = []
    for blk in BLOCKERS:
        deltas = {row["pair_id"]: row["blocker_abs_delta"][blk] for row in blocker_match_table}
        best = min(deltas, key=deltas.get)
        rho = float(spearman(Svec, np.array([_bval(e["stats"], blk) for e in pool], float)))
        blocker_residuals.append({"blocker": blk, "min_abs_delta": deltas[best], "best_pair": best,
                                  "still_explains_S_pool_spearman": round(rho, 3),
                                  "still_explains_S": bool(abs(rho) >= CEIL)})

    # section 4: verdict -- frozen §7 anti-proxy + §8 over the v1.9 bank (UNCHANGED logic); in-scope = winders
    keys = list(cs.ANTI_PROXY_STATS) + ["nr_" + s for s in cs.NULL_REL_STATS]
    Sall = np.array([e["S"] for e in entries], float)
    anti = {}
    for k in keys:
        st_name = k[3:] if k.startswith("nr_") else k
        b = (float(np.mean([e["stats"][st_name] for e in traj_entries])) if traj_entries else 0.0) \
            if k.startswith("nr_") else 0.0
        rho = spearman(Sall, np.array([e["stats"][st_name] - b for e in entries], float))
        anti[k] = {"spearman": round(rho, 3), "ok": bool(abs(rho) < CEIL)}
    anti_ok = all(v["ok"] for v in anti.values())
    inscope = [e for e in entries if e["group"] == "winder"]
    n_ok = sum(
        1 for e in inscope
        if e["pair"] in traj_by_pair
        and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * traj_by_pair[e["pair"]]["S"]
        and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * S_cont
        and e["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * S_struct
        and e["PSC"] >= cs.PSC_FLOOR
        and e["AIC"] >= cs.AIC_FLOOR
    )
    n_le_null = sum(
        1 for e in inscope
        if e["pair"] in traj_by_pair and e["S"] <= traj_by_pair[e["pair"]]["S"]
    )
    if n_le_null > len(inscope) / 2:
        verdict = "FAIL"
    elif n_ok > len(inscope) / 2 and anti_ok:
        verdict = "PASS"
    else:
        verdict = "HOLD"

    # honest interpretive outcome (reporting-only)
    tight = [s for s in separation if s["all_blockers_matched"]]
    tight_and_separate = [s for s in tight if s["S_still_separates"]]
    all_separate = all(s["S_still_separates"] for s in separation)
    residual_pool = [b["blocker"] for b in blocker_residuals if b["still_explains_S"]]
    if tight_and_separate and not residual_pool:
        outcome = ("A: with all four blocker deltas driven low (" + ",".join(s["pair_id"] for s in tight_and_separate)
                   + ") S/PSC still separates winding from cancellation and no blocker still explains S "
                   "-> spectral/std blocker weakened.")
    elif tight_and_separate and residual_pool:
        outcome = ("A_with_residual: in the tightly-matched families (" + ",".join(s["pair_id"] for s in tight_and_separate)
                   + ", all four blocker |delta| < %.2f) S/PSC still separates winding from cancellation, so S is "
                   "NOT explained by the spectral/std blockers at matched values; residual: " % MATCH_REPORT_DELTA
                   + ",".join(residual_pool) + " retain(s) a weaker cross-family pool correlation with S "
                   "(pool-composition residual, not a within-matched-pair failure).")
    elif all_separate and not tight:
        outcome = "C: S separates but no family drove all four blockers jointly low -> matching incomplete."
    elif not all_separate:
        outcome = "B: S/PSC collapses under spectral/std control -> descriptor limitation strengthened."
    else:
        outcome = "ambiguous / needs adversarial review."

    return {"diagnostic": "v1.9 spectral/std blocker (reuses frozen v0.7/v0.8 + v1.4 style, reporting-only)",
            "blocker_match_table": blocker_match_table, "separation_under_blocker_control": separation,
            "blocker_residuals": blocker_residuals, "anti_proxy": anti, "anti_proxy_ok": anti_ok,
            "bank_size": len(entries), "match_report_delta": MATCH_REPORT_DELTA, "verdict": verdict,
            "reporting_only": True, "interpretive_outcome": outcome,
            "first_pass_structure_validity_claim_allowed": bool(verdict == "PASS"),
            "temporal_claim_allowed": False}


if __name__ == "__main__":
    r = run()
    print("verdict", r["verdict"], "| anti_proxy_ok", r["anti_proxy_ok"], "| bank_size", r["bank_size"],
          "| reporting_only", r["reporting_only"])
    print("\n1. blocker_match_table (winder vs non-winder; |Δ| = abs blocker delta):")
    for row in r["blocker_match_table"]:
        print("  %-20s S %.3f/%.3f PSC %.2f/%.2f  mean|Δblk|=%.4f all_matched=%s Ssep=%.3f"
              % (row["pair_id"], row["winder"]["S"], row["nonwinder"]["S"], row["winder"]["PSC"],
                 row["nonwinder"]["PSC"], row["mean_blocker_abs_delta"], row["all_blockers_matched"],
                 row["S_separation"]))
        for blk in BLOCKERS:
            print("       %-18s w=%+.4f n=%+.4f |Δ|=%.4f"
                  % (blk, row["blockers"][blk]["winder"], row["blockers"][blk]["nonwinder"],
                     row["blocker_abs_delta"][blk]))
    print("\n2. separation_under_blocker_control:")
    for s in r["separation_under_blocker_control"]:
        print("  %-20s winds=%s cancels=%s S_separates=%s all_matched=%s matched=%s"
              % (s["pair_id"], s["winder_winds"], s["nonwinder_cancels"], s["S_still_separates"],
                 s["all_blockers_matched"], s["matched_blockers"]))
    print("\n3. blocker_residuals:")
    for b in r["blocker_residuals"]:
        print("  %-18s min|Δ|=%.4f (%s) pool_spearman(S)=%+.3f still_explains_S=%s"
              % (b["blocker"], b["min_abs_delta"], b["best_pair"], b["still_explains_S_pool_spearman"],
                 b["still_explains_S"]))
    print("\n4. interpretive_outcome:", r["interpretive_outcome"])
