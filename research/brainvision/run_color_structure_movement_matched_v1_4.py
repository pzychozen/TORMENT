"""BV chroma-structure movement-matched diagnostic v1.4 (offline research; NOT runtime/integration; NOT vision).

Narrow offline slice for the v1.4 movement-matched fixture plan
(docs: TORMENT_BRAINVISION_COLOR_STRUCTURE_MOVEMENT_MATCHED_FIXTURE_PLAN_v1.4). It asks one question:

    can winding-coherent and non-winding fixtures be MATCHED on directional movement amount
    (`u_directional_delta_rms`, `angular_increment_mag`) while differing in winding coherence (`PSC`)?

It reports the answer THROUGH the unchanged v0.8/v1.1 diagnostic logic imported by identity from
run_color_structure_v0_8 (`cs`) and run_color_structure_fixture_bank_v1_1 (`fb`). It changes NO formula and NO
constant: `PSC`, `AIC`, `S`, the chroma gate, the anti-proxy statistic set/gauntlet, the null semantics, and the
§7/§8 pass/HOLD/FAIL verdict rule are all reused verbatim. The only new thing is the CONTENTS of the fixture
bank (predeclared movement-matched winder/non-winder families) and a REPORTING-ONLY movement-match readout.

Construction principle (predeclared, never tuned to an S): a coherent winder built from a constant same-sign
per-step angular increment `+g` and a non-winder built from the SAME per-step magnitude `|g|` with cancelling
signs share the identical multiset of `|Δθ|` increments, hence the identical `u_directional_delta_rms` and
`angular_increment_mag`, while `PSC` is ~1 for the winder and ~0 for the non-winder. Match quality (the movement
differences of a matched pair) is REPORTING-ONLY: it is never a pass/fail surface and invents no threshold.

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no object/scene
understanding; no temporal-order diagnostic; no new descriptor family; no clip corpus; no real clips.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_color_structure_fixture_bank_v1_1 as fb

# frozen surfaces reused verbatim (NOT redefined)
T = cs.T
A = cs.A
BASE_Y = cs.BASE_Y
EPS = cs.EPS
structure_score = cs.structure_score
stats = cs._stats
traj_perm = cs.null_trajectory_order_permuted
series = cs._series
is_winding = fb.is_winding
traj_null_guarded = fb.traj_null_guarded

THETA0 = 0.30                            # predeclared start hue-angle (fixed, never tuned)
# predeclared per-step angular-increment magnitudes (movement levels), fixed before any run
G_XS, G_S, G_M, G_L = 0.05, 0.10, 0.20, 0.42


def _from_increments(deltas, theta0=THETA0):
    """Opponent-space chroma path from a predeclared per-step signed angular-increment sequence."""
    deltas = np.asarray(deltas, float)
    theta = np.concatenate([[theta0], theta0 + np.cumsum(deltas)])
    return np.full(T, BASE_Y), A * np.cos(theta), A * np.sin(theta)


def _winder(g):
    return _from_increments(np.full(T - 1, g))                        # constant +g -> coherent winding


def _out_and_back(g):
    h = (T - 1) // 2
    d = np.concatenate([np.full(h, g), np.full(T - 1 - h, -g)])       # +g then -g: forward/backward, cancels
    return _from_increments(d)


def _alternating(g):
    d = g * ((-1.0) ** np.arange(T - 1))                             # +g,-g,+g,...: max motion, zero net winding
    return _from_increments(d)


def _figure_eight():
    phi = 2 * np.pi * np.arange(T) / T
    return np.full(T, BASE_Y), A * np.cos(phi), (A / 2.0) * np.sin(2 * phi)   # lemniscate: two lobes cancel


def _circle_out_and_back():
    t = np.arange(T)
    up = 2 * np.pi * t[: T // 2] / (T // 2)
    theta = np.concatenate([up, up[::-1]])[:T]                        # 0->2pi then 2pi->0: closed, net winding 0
    return np.full(T, BASE_Y), A * np.cos(theta + THETA0), A * np.sin(theta + THETA0)


# predeclared fixtures (name -> (generator, role, class))  -- parameters frozen before any run
_SPECS = (
    ("A_winder_m", lambda: _winder(G_M), "winder", "A"),
    ("A_winder_l", lambda: _winder(G_L), "winder", "A"),
    ("B_outback_m", lambda: _out_and_back(G_M), "nonwinder", "B"),
    ("B_outback_l", lambda: _out_and_back(G_L), "nonwinder", "B"),
    ("B_alternating_m", lambda: _alternating(G_M), "nonwinder", "B"),
    ("C_figure_eight", _figure_eight, "nonwinder", "C"),
    ("C_circle_outback", _circle_out_and_back, "nonwinder", "C"),
    ("D_winder_xs", lambda: _winder(G_XS), "winder", "D"),
    ("D_winder_s", lambda: _winder(G_S), "winder", "D"),
    ("B_outback_xs", lambda: _out_and_back(G_XS), "nonwinder", "B"),
    ("B_outback_s", lambda: _out_and_back(G_S), "nonwinder", "B"),
)
_GEN = {name: gen for (name, gen, role, cl) in _SPECS}
ROLE = {name: role for (name, gen, role, cl) in _SPECS}
CLASS = {name: cl for (name, gen, role, cl) in _SPECS}
ALL_FIXTURES = tuple(name for (name, gen, role, cl) in _SPECS)
WINDERS = tuple(n for n in ALL_FIXTURES if ROLE[n] == "winder")
NONWINDERS = tuple(n for n in ALL_FIXTURES if ROLE[n] == "nonwinder")
IN_SCOPE = WINDERS                        # winders are the structure-bearing in-scope set for the §8 verdict

# predeclared movement-matched pairs (winder <-> non-winder built from the same |Δθ| magnitude)
MATCHED_PAIRS = (("A_winder_m", "B_outback_m"), ("A_winder_l", "B_outback_l"),
                 ("D_winder_xs", "B_outback_xs"), ("D_winder_s", "B_outback_s"),
                 ("A_winder_m", "B_alternating_m"))


def fixture_series(name):
    yp, rg, by = _GEN[name]()
    return series(yp, rg, by)


def run():
    ct = series(*cs.continuity_control())
    S_cont = structure_score(ct[0], ct[1], ct[2])["S"]
    st = series(*cs.structureless_control())
    S_struct = structure_score(st[0], st[1], st[2])["S"]

    bank = []
    per_fixture = {}
    for i, name in enumerate(ALL_FIXTURES):
        rg, by, ch, clip = fixture_series(name)
        s_int = structure_score(rg, by, ch)
        winding, _ = is_winding(rg, by, ch)
        role = ROLE[name]
        # structural verification of the declared role (by signed turns / PSC), reused frozen PSC_FLOOR
        role_ok = bool((winding and role == "winder") or ((not winding) and role == "nonwinder"))
        st_stats = stats(rg, by, ch)
        rgp, byp, chp, retries, null_invalid = traj_null_guarded(rg, by)
        s_traj = structure_score(rgp, byp, chp)
        s_indep = structure_score(*series(np.full(T, BASE_Y), *cs.null_independent_phase(rg, by, 9000 + i))[:3])
        s_pby = structure_score(*series(np.full(T, BASE_Y), *cs.null_permuted_by(rg, by, 9100 + i))[:3])
        s_shared = structure_score(*series(np.full(T, BASE_Y), *cs.null_shared_phase(rg, by, 9200 + i))[:3])
        in_scope = name in IN_SCOPE
        beat_null = s_int["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * s_traj["S"]
        beat_cont = s_int["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * S_cont
        beat_struct = s_int["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * S_struct
        floors = (s_int["PSC"] >= cs.PSC_FLOOR) and (s_int["AIC"] >= cs.AIC_FLOOR)
        fixture_ok = bool(in_scope and (not s_int["neutral"]) and (not null_invalid)
                          and beat_null and beat_cont and beat_struct and floors)
        per_fixture[name] = {
            "class": CLASS[name], "role": role, "in_scope": in_scope, "winding": bool(winding),
            "role_ok": role_ok, "S": round(s_int["S"], 4), "PSC": round(s_int["PSC"], 4),
            "AIC": round(s_int["AIC"], 4), "u_directional_delta_rms": round(st_stats["u_directional_delta_rms"], 5),
            "angular_increment_mag": round(st_stats["angular_increment_mag"], 5),
            "rg_centroid": round(st_stats["rg_centroid"], 4), "by_centroid": round(st_stats["by_centroid"], 4),
            "rg_spread": round(st_stats["rg_spread"], 4), "by_spread": round(st_stats["by_spread"], 4),
            "S_traj_null": round(s_traj["S"], 4), "traj_null_retries": retries, "traj_null_invalid": null_invalid,
            "S_indep_null": round(s_indep["S"], 4), "S_permuted_by": round(s_pby["S"], 4),
            "S_shared_phase": round(s_shared["S"], 4), "gamut_clip": clip,
            "beat_null": beat_null, "floors_ok": floors, "fixture_ok": fixture_ok,
            "S_le_null": bool(s_int["S"] <= s_traj["S"])}
        bank.append((name, s_int["S"], st_stats, s_int["neutral"]))
        if in_scope and not null_invalid:
            bank.append((name + "_traj_null", s_traj["S"], stats(rgp, byp, chp), s_traj["neutral"]))
            irg, iby, ich, _ic = series(np.full(T, BASE_Y), *cs.null_independent_phase(rg, by, 9000 + i))
            bank.append((name + "_indep_null", structure_score(irg, iby, ich)["S"], stats(irg, iby, ich), False))

    # F: neutral / chroma-floor carry-forward (identical to v0.8; EXCLUDED from anti-proxy bank per §7)
    neutral = {}
    frames0 = cs.cb._clip_from_series(*cs.rotation_series("rot_full"))
    for cname, frames in (("grayscale", cs.cb.ctl_grayscale(frames0)),
                          ("saturation_collapse", cs.cb.ctl_saturation_collapse(frames0, 0.0)),
                          ("low_saturation_neutral", cs.cb.fixture("low_saturation_neutral")),
                          ("rough_luminance_only_null", cs.g5.rough_luminance_only_null(0))):
        sm = cs.cb._spatial_means(frames)
        s = structure_score(sm["RG"], sm["BY"], sm["CHROMA"])
        neutral[cname] = {"S": round(s["S"], 4), "neutral": s["neutral"],
                          "ok": bool(s["neutral"] or s["S"] <= cs.NEUTRAL_STRUCTURE_CEIL)}
    bank.append(("continuity_control", S_cont, stats(ct[0], ct[1], ct[2]), False))
    bank.append(("structureless_control", S_struct, stats(st[0], st[1], st[2]), False))

    # anti-proxy Spearman over the full bank (frozen §7 names + null-relative variants) -- UNCHANGED rule
    Svec = np.array([b[1] for b in bank], float)
    anti = {}
    for stat_name in cs.ANTI_PROXY_STATS:
        rho = cs.g5._spearman(Svec, np.array([b[2][stat_name] for b in bank], float))
        anti[stat_name] = {"spearman": round(rho, 3), "ok": bool(abs(rho) < cs.MAGNITUDE_CORR_CEIL)}
    traj_entries = [b for b in bank if b[0].endswith("_traj_null")]
    for stat_name in cs.NULL_REL_STATS:
        base = float(np.mean([b[2][stat_name] for b in traj_entries])) if traj_entries else 0.0
        rho = cs.g5._spearman(Svec, np.array([b[2][stat_name] - base for b in bank], float))
        anti["nr_" + stat_name] = {"spearman": round(rho, 3), "ok": bool(abs(rho) < cs.MAGNITUDE_CORR_CEIL)}
    anti_proxy_ok = all(v["ok"] for v in anti.values())

    # REPORTING-ONLY movement-match readout (never a pass/fail surface; invents no threshold)
    movement_match = []
    for w, n in MATCHED_PAIRS:
        du = abs(per_fixture[w]["u_directional_delta_rms"] - per_fixture[n]["u_directional_delta_rms"])
        da = abs(per_fixture[w]["angular_increment_mag"] - per_fixture[n]["angular_increment_mag"])
        movement_match.append({
            "winder": w, "nonwinder": n,
            "u_ddr_winder": per_fixture[w]["u_directional_delta_rms"],
            "u_ddr_nonwinder": per_fixture[n]["u_directional_delta_rms"], "u_ddr_abs_diff": round(du, 5),
            "ang_winder": per_fixture[w]["angular_increment_mag"],
            "ang_nonwinder": per_fixture[n]["angular_increment_mag"], "ang_abs_diff": round(da, 5),
            "S_winder": per_fixture[w]["S"], "S_nonwinder": per_fixture[n]["S"],
            "PSC_winder": per_fixture[w]["PSC"], "PSC_nonwinder": per_fixture[n]["PSC"]})

    # verdict (v0.7 §8) -- UNCHANGED logic, applied over the winder in-scope set
    n_scope = len(IN_SCOPE)
    n_ok = sum(per_fixture[f]["fixture_ok"] for f in IN_SCOPE)
    n_le_null = sum(per_fixture[f]["S_le_null"] for f in IN_SCOPE)
    neutral_ok = all(v["ok"] for v in neutral.values())
    if n_le_null > n_scope / 2:
        verdict = "FAIL"
    elif (n_ok > n_scope / 2) and neutral_ok and anti_proxy_ok:
        verdict = "PASS"
    else:
        verdict = "HOLD"

    classes = {}
    for cl in "ABCD":
        names = [f for f in ALL_FIXTURES if CLASS[f] == cl]
        classes[cl] = {"n": len(names), "roles": sorted(set(ROLE[f] for f in names)),
                       "S_mean": round(float(np.mean([per_fixture[f]["S"] for f in names])), 4),
                       "winding": sum(per_fixture[f]["winding"] for f in names),
                       "role_ok": all(per_fixture[f]["role_ok"] for f in names)}

    # honest interpretive-outcome hint (REPORTING-ONLY; classification, not a claim)
    matched_pairs_separate = all(
        (m["S_winder"] > 0.5 and m["S_nonwinder"] < 0.5) for m in movement_match)
    tight_match = all(m["u_ddr_abs_diff"] < 1e-6 and m["ang_abs_diff"] < 1e-6 for m in movement_match)
    move_stats_decorrelated = all(anti[s]["ok"] for s in ("u_directional_delta_rms", "angular_increment_mag"))
    if matched_pairs_separate and tight_match:
        outcome = ("Outcome1_movement_matched_S_separates: at matched movement, winders stay high-S and "
                   "non-winders low-S -> residual directional-axis failure is at least partly a fixture-bank "
                   "artifact (S is not merely movement amount)")
        if not move_stats_decorrelated:
            outcome += ("; NOTE the pooled-bank Spearman(S, movement) can still fail because nulls/controls "
                        "re-introduce movement<->S covariation across the whole bank")
    elif not tight_match:
        outcome = "Outcome3_matching_not_achieved: could not match movement without collapsing the distinction"
    else:
        outcome = "Outcome2_S_tracks_movement_even_after_matching (supports later Direction C question)"

    return {"per_fixture": per_fixture, "classes": classes, "matched_pairs": movement_match,
            "match_quality_reporting_only": True, "continuity_S": round(S_cont, 4),
            "structureless_S": round(S_struct, 4), "neutral": neutral, "anti_proxy": anti,
            "anti_proxy_ok": anti_proxy_ok, "in_scope_n": n_scope, "in_scope_ok": n_ok, "neutral_ok": neutral_ok,
            "bank_size": len(bank), "verdict": verdict,
            "first_pass_structure_validity_claim_allowed": bool(verdict == "PASS"),
            "temporal_claim_allowed": False, "interpretive_outcome": outcome}


if __name__ == "__main__":
    import json
    r = run()
    print("verdict", r["verdict"], "| anti_proxy_ok", r["anti_proxy_ok"], "| in_scope_ok",
          "%d/%d" % (r["in_scope_ok"], r["in_scope_n"]), "| neutral_ok", r["neutral_ok"],
          "| bank_size", r["bank_size"])
    print("match_quality_reporting_only:", r["match_quality_reporting_only"])
    print("\nper-fixture:")
    for n, d in r["per_fixture"].items():
        print("  %-18s cls=%s role=%-9s S=%.3f PSC=%.2f AIC=%.2f u_ddr=%.4f ang=%.4f wind=%s role_ok=%s"
              % (n, d["class"], d["role"], d["S"], d["PSC"], d["AIC"], d["u_directional_delta_rms"],
                 d["angular_increment_mag"], d["winding"], d["role_ok"]))
    print("\nmatched pairs (movement-match is REPORTING-ONLY):")
    for m in r["matched_pairs"]:
        print("  %-14s <-> %-16s u_ddr %.4f/%.4f d=%.1e  ang %.4f/%.4f d=%.1e  S %.3f/%.3f  PSC %.2f/%.2f"
              % (m["winder"], m["nonwinder"], m["u_ddr_winder"], m["u_ddr_nonwinder"], m["u_ddr_abs_diff"],
                 m["ang_winder"], m["ang_nonwinder"], m["ang_abs_diff"], m["S_winder"], m["S_nonwinder"],
                 m["PSC_winder"], m["PSC_nonwinder"]))
    print("\nanti-proxy (frozen §7 gate, UNCHANGED):")
    for k, v in r["anti_proxy"].items():
        print("  %-26s %+.3f %s" % (k, v["spearman"], "ok" if v["ok"] else "FAIL"))
    print("\ninterpretive_outcome:", r["interpretive_outcome"])
