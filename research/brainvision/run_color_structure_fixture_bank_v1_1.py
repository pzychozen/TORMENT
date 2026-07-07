"""BV chroma-structure fixture-bank v1.1 (offline research; NOT runtime/integration; NOT vision).

First narrow implementation slice for the v1.1 fixture-bank requirements
(docs: TORMENT_BRAINVISION_COLOR_STRUCTURE_FIXTURE_BANK_IMPLEMENTATION_SPEC_v1.1). It instantiates the
predeclared A-H synthetic fixture classes and reports them THROUGH the unchanged v0.7/v0.8 diagnostic logic
imported from run_color_structure_v0_8 (`cs`). It changes NO formula and NO constant: PSC, AIC, S, the chroma
gate, the anti-proxy statistic set, the null semantics, and the pass/HOLD/FAIL logic are all reused verbatim
from `cs`. The only new thing here is the CONTENTS of the fixture bank (the predeclared decorrelated families);
the §7 rule ("Spearman(S, stat) over the full bank < ceil") and the §8 verdict rule are applied unchanged.

Intent (v0.9/v1.0/v1.1): a bank that intentionally separates winding coherence from directional smoothness,
chroma magnitude, and per-channel spectral spread/centroid, so the frozen anti-proxy gate becomes a real test
of the descriptor rather than a measurement of a built-in entanglement. This module PREDECLARES all fixture
parameters below (never selected after seeing S), keeps hard cases (D high-chroma structureless, E narrowband
non-winding, continuity, structureless), spans proxy ranges rather than shrinking them, and pairs high-S with
low-S families over shared proxy ranges (A<->D over magnitude, B<->E over spectral spread). It invents no
threshold and weakens no gate; the honest verdict is whatever the unchanged §8 logic returns.

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no object/scene
understanding; no temporal-order diagnostic; no new descriptor family; no clip corpus; no real clips.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs

# frozen surfaces reused verbatim (NOT redefined)
T = cs.T
A = cs.A
BASE_Y = cs.BASE_Y
EPS = cs.EPS
structure_score = cs.structure_score
stats = cs._stats
traj_perm = cs.null_trajectory_order_permuted
series = cs._series

# ----- predeclared fixture parameters (frozen BEFORE any run; never selected after seeing S) -----
# A: coherent one-turn winding, varied chroma magnitude envelope (winding held fixed, magnitude varies).
A_SPECS = (("A_mag_full", "const", 1.00), ("A_mag_mid", "const", 0.65), ("A_mag_low", "const", 0.30),
           ("A_mag_ramp", "ramp", None), ("A_mag_ammod", "ammod", None))
# B: coherent winding, varied per-channel spectral spread (monotonic non-uniform winding rate -> broadband).
B_SPECS = (("B_spread_chirp", "chirp"), ("B_spread_multi", "multi"), ("B_spread_jitter", "jitter"))
# C: smooth NON-winding chroma trajectories (low directional roughness, zero net winding -> low S).
C_SPECS = (("C_backforth_a", 0.80), ("C_backforth_b", 1.20), ("C_smooth_noise", None))
# D: high-chroma structureless trajectories, magnitude family OVERLAPPING A (low-S counterpart to A).
D_SPECS = (("D_struct_full", 1.00, 22201), ("D_struct_mid", 0.65, 22204), ("D_struct_low", 0.30, 22203))
# E: spectrally narrow NON-winding (collinear along a fixed chroma axis; verified non-winding by c(t)).
E_SPECS = (("E_narrow_axis_a", np.pi / 4.0), ("E_narrow_axis_b", np.pi / 3.0))
# F: coherent winding held fixed while per-channel spectral centroid/spread are perturbed.
F_SPECS = (("F_pert_a", 2, 3, 0.22), ("F_pert_b", 4, 2, 0.18))

WIND_IN_SCOPE = tuple(s[0] for s in A_SPECS) + tuple(s[0] for s in B_SPECS) + tuple(s[0] for s in F_SPECS)
LOW_S_FAMILY = tuple(s[0] for s in C_SPECS) + tuple(s[0] for s in D_SPECS) + tuple(s[0] for s in E_SPECS)

TRAJ_PERM_SEED = 1101                    # predeclared base seed for G trajectory-order-permuted nulls
TRAJ_FALLBACK_OFFSETS = (0, 131, 262, 393)   # predeclared fallback seed sequence (fixed retry order)
TRAJ_RETRY_LIMIT = 3                     # fixed retry limit; then mark invalid (never redraw-until-desired-S)


def _theta_winding(k=1):
    return 2 * np.pi * k * np.arange(T) / T


# ----------------------------- fixture generators (opponent space -> cs._series bridge) -----------------------------
def gen_A(spec):
    _name, mode, frac = spec
    th = _theta_winding(1)
    t = np.arange(T)
    if mode == "const":
        env = frac * A * np.ones(T)
    elif mode == "ramp":
        env = np.linspace(0.30, 1.00, T) * A
    elif mode == "ammod":
        env = A * (0.60 + 0.40 * np.cos(2 * np.pi * 3 * t / T))
    else:
        raise ValueError(mode)
    return np.full(T, BASE_Y), env * np.cos(th), env * np.sin(th)


def gen_B(spec):
    _name, mode = spec
    t = np.arange(T)
    if mode == "chirp":
        rate = 1.0 + 1.5 * (t / (T - 1))                       # strictly positive, accelerating
    elif mode == "multi":
        rate = 1.0 + 0.6 * np.cos(2 * np.pi * 3 * t / T)       # in [0.4, 1.6] -> positive
    elif mode == "jitter":
        r = np.convolve(np.random.default_rng(909).standard_normal(T), np.ones(5) / 5.0, mode="same")
        rate = 1.0 + 0.5 * (r / (np.max(np.abs(r)) + EPS))     # in [0.5, 1.5] -> positive
    else:
        raise ValueError(mode)
    rate = np.clip(rate, 1e-3, None)
    th = 2 * np.pi * np.cumsum(rate) / np.sum(rate)            # one full monotonic turn -> coherent winding
    return np.full(T, BASE_Y), A * np.cos(th), A * np.sin(th)


def gen_C(spec):
    _name, osc = spec
    t = np.arange(T)
    if osc is None:
        return cs.continuity_control(seed=33301)               # smooth, jointly structureless (non-winding)
    th = (np.pi / 2.0) + osc * np.sin(2 * np.pi * 2 * t / T)   # smooth back-and-forth arc, zero net winding
    return np.full(T, BASE_Y), A * np.cos(th), A * np.sin(th)


def gen_D(spec):
    _name, frac, seed = spec
    rng = np.random.default_rng(seed)
    return (np.full(T, BASE_Y), np.clip(frac * A * rng.standard_normal(T), -A, A),
            np.clip(frac * A * rng.standard_normal(T), -A, A))


def gen_E(spec):
    _name, phi = spec
    t = np.arange(T)
    s = 0.60 + 0.40 * np.cos(2 * np.pi * 1 * t / T)            # narrowband, strictly positive -> fixed direction
    return np.full(T, BASE_Y), A * np.cos(phi) * s, A * np.sin(phi) * s


def gen_F(spec):
    _name, p_rg, p_by, m = spec
    t = np.arange(T)
    th = _theta_winding(1)
    env_rg = 1.0 + m * np.cos(2 * np.pi * p_rg * t / T)
    env_by = 1.0 + m * np.cos(2 * np.pi * p_by * t / T)
    return np.full(T, BASE_Y), A * env_rg * np.cos(th), A * env_by * np.sin(th)


_GEN = {}
for _s in A_SPECS:
    _GEN[_s[0]] = (gen_A, _s)
for _s in B_SPECS:
    _GEN[_s[0]] = (gen_B, _s)
for _s in C_SPECS:
    _GEN[_s[0]] = (gen_C, _s)
for _s in D_SPECS:
    _GEN[_s[0]] = (gen_D, _s)
for _s in E_SPECS:
    _GEN[_s[0]] = (gen_E, _s)
for _s in F_SPECS:
    _GEN[_s[0]] = (gen_F, _s)

ALL_FIXTURES = (tuple(s[0] for s in A_SPECS) + tuple(s[0] for s in B_SPECS) + tuple(s[0] for s in C_SPECS)
                + tuple(s[0] for s in D_SPECS) + tuple(s[0] for s in E_SPECS) + tuple(s[0] for s in F_SPECS))


def fixture_series(name):
    gen, spec = _GEN[name]
    yp, rg, by = gen(spec)
    r, b, ch, clip = series(yp, rg, by)
    return r, b, ch, clip


def is_winding(rg, by, ch):
    """Predeclared signed-turn (c(t)) winding check reusing the frozen PSC component (PSC_FLOOR)."""
    s = structure_score(rg, by, ch)
    return (not s["neutral"]) and (s["PSC"] >= cs.PSC_FLOOR), s


# ----------------------------- G: trajectory-order-permuted null with predeclared guard -----------------------------
def traj_null_guarded(rg, by):
    """Pure trajectory-order permutation (preserves multiset of (RG,BY) pairs -> u(t) and CHROMA; destroys order).

    If a draw ACCIDENTALLY reconstructs coherent winding (null PSC >= frozen PSC_FLOOR), advance the predeclared
    fallback seed sequence up to a fixed retry limit and REPORT the retry count; if still coherent after the
    limit, mark the null draw INVALID. Never redraw until a desired S is obtained.
    """
    rgp = byp = chp = None
    for i in range(TRAJ_RETRY_LIMIT + 1):
        seed = TRAJ_PERM_SEED + TRAJ_FALLBACK_OFFSETS[min(i, len(TRAJ_FALLBACK_OFFSETS) - 1)]
        rgp, byp = traj_perm(rg, by, seed)
        chp = np.sqrt(rgp ** 2 + byp ** 2)
        if structure_score(rgp, byp, chp)["PSC"] < cs.PSC_FLOOR:
            return rgp, byp, chp, i, False                     # not coherent -> accept, report retries=i
    return rgp, byp, chp, TRAJ_RETRY_LIMIT, True               # exhausted -> invalid (do NOT chase an S)


# ----------------------------- run: report through unchanged v0.8 logic -----------------------------
def run():
    # shared controls (identical construction to v0.8)
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
        rgp, byp, chp, retries, null_invalid = traj_null_guarded(rg, by)
        s_traj = structure_score(rgp, byp, chp)
        # reporting-only nulls (never gate)
        s_indep = structure_score(*series(np.full(T, BASE_Y), *cs.null_independent_phase(rg, by, 6000 + i))[:3])
        s_pby = structure_score(*series(np.full(T, BASE_Y), *cs.null_permuted_by(rg, by, 7000 + i))[:3])
        s_shared = structure_score(*series(np.full(T, BASE_Y), *cs.null_shared_phase(rg, by, 8000 + i))[:3])
        in_scope = name in WIND_IN_SCOPE
        beat_null = s_int["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * s_traj["S"]
        beat_cont = s_int["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * S_cont
        beat_struct = s_int["S"] >= (1 + cs.STRUCTURE_BEAT_MARGIN) * S_struct
        floors = (s_int["PSC"] >= cs.PSC_FLOOR) and (s_int["AIC"] >= cs.AIC_FLOOR)
        fixture_ok = bool(in_scope and (not s_int["neutral"]) and (not null_invalid)
                          and beat_null and beat_cont and beat_struct and floors)
        per_fixture[name] = {
            "class": name[0], "in_scope": in_scope, "winding": bool(winding),
            "S": round(s_int["S"], 4), "PSC": round(s_int["PSC"], 4), "AIC": round(s_int["AIC"], 4),
            "S_traj_null": round(s_traj["S"], 4), "traj_null_retries": retries, "traj_null_invalid": null_invalid,
            "S_indep_null": round(s_indep["S"], 4), "S_permuted_by": round(s_pby["S"], 4),
            "S_shared_phase": round(s_shared["S"], 4), "gamut_clip": clip,
            "beat_null": beat_null, "beat_continuity": beat_cont, "beat_structureless": beat_struct,
            "floors_ok": floors, "fixture_ok": fixture_ok, "S_le_null": bool(s_int["S"] <= s_traj["S"])}
        # anti-proxy bank: every primary fixture + (for winders) its traj-null and independent-null (v0.7 §7 form)
        bank.append((name, s_int["S"], stats(rg, by, ch), s_int["neutral"]))
        if in_scope and not null_invalid:
            bank.append((name + "_traj_null", s_traj["S"], stats(rgp, byp, chp), s_traj["neutral"]))
            irg, iby, ich, _ic = series(np.full(T, BASE_Y), *cs.null_independent_phase(rg, by, 6000 + i))
            bank.append((name + "_indep_null", structure_score(irg, iby, ich)["S"], stats(irg, iby, ich), False))

    # H neutral / chroma-floor controls (identical construction to v0.8; excluded from anti-proxy bank per §7)
    neutral = {}
    rot0 = cs.rotation_series("rot_full")
    frames0 = cs.cb._clip_from_series(*rot0)
    for cname, frames in (("grayscale", cs.cb.ctl_grayscale(frames0)),
                          ("saturation_collapse", cs.cb.ctl_saturation_collapse(frames0, 0.0)),
                          ("low_saturation_neutral", cs.cb.fixture("low_saturation_neutral")),
                          ("rough_luminance_only_null", cs.g5.rough_luminance_only_null(0))):
        sm = cs.cb._spatial_means(frames)
        s = structure_score(sm["RG"], sm["BY"], sm["CHROMA"])
        neutral[cname] = {"S": round(s["S"], 4), "neutral": s["neutral"],
                          "ok": bool(s["neutral"] or s["S"] <= cs.NEUTRAL_STRUCTURE_CEIL)}
    color_m, _lum_m = cs.g5.roughness_matched_color_vs_luminance_pair(0)
    smc = cs.cb._spatial_means(color_m)
    s_rm = structure_score(smc["RG"], smc["BY"], smc["CHROMA"])
    neutral["roughness_matched_color(report)"] = {
        "S": round(s_rm["S"], 4), "neutral": s_rm["neutral"],
        "ok": bool(s_rm["neutral"] or s_rm["S"] <= cs.NEUTRAL_STRUCTURE_CEIL)}
    bank.append(("roughness_matched_color", s_rm["S"], stats(smc["RG"], smc["BY"], smc["CHROMA"]), s_rm["neutral"]))
    # continuity + structureless controls into bank (retained hard cases)
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

    # verdict (v0.7 §8) -- UNCHANGED logic, applied over the v1.1 in-scope winding families
    in_scope = [f for f in ALL_FIXTURES if f in WIND_IN_SCOPE]
    n_scope = len(in_scope)
    n_ok = sum(per_fixture[f]["fixture_ok"] for f in in_scope)
    n_le_null = sum(per_fixture[f]["S_le_null"] for f in in_scope)
    neutral_ok = all(v["ok"] for v in neutral.values())
    if n_le_null > n_scope / 2:
        verdict = "FAIL"
    elif (n_ok > n_scope / 2) and neutral_ok and anti_proxy_ok:
        verdict = "PASS"
    else:
        verdict = "HOLD"
    # class-level summary
    classes = {}
    for cl in "ABCDEF":
        names = [f for f in ALL_FIXTURES if per_fixture[f]["class"] == cl]
        classes[cl] = {"n": len(names), "S_mean": round(float(np.mean([per_fixture[f]["S"] for f in names])), 4),
                       "S_min": round(float(min(per_fixture[f]["S"] for f in names)), 4),
                       "S_max": round(float(max(per_fixture[f]["S"] for f in names)), 4),
                       "winding": sum(per_fixture[f]["winding"] for f in names)}
    return {"per_fixture": per_fixture, "classes": classes, "continuity_S": round(S_cont, 4),
            "structureless_S": round(S_struct, 4), "neutral": neutral, "anti_proxy": anti,
            "anti_proxy_ok": anti_proxy_ok, "in_scope_n": n_scope, "in_scope_ok": n_ok, "neutral_ok": neutral_ok,
            "bank_size": len(bank), "verdict": verdict,
            "first_pass_structure_validity_claim_allowed": bool(verdict == "PASS"), "temporal_claim_allowed": False}


if __name__ == "__main__":
    import json
    r = run()
    print(json.dumps({k: v for k, v in r.items() if k != "per_fixture"}, indent=1, default=str))
    print("\nper-fixture:")
    for n, d in r["per_fixture"].items():
        print(f"  {n:<16} cls={d['class']} S={d['S']:.3f} PSC={d['PSC']:.2f} AIC={d['AIC']:.2f} "
              f"traj={d['S_traj_null']:.3f} wind={d['winding']} inscope={d['in_scope']} ok={d['fixture_ok']}")
