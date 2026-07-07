"""BV chroma-structure formula diagnostic v0.8 (offline research; NOT runtime/integration; NOT vision).

Implements EXACTLY the committed v0.7 formula-freeze plan
(docs: TORMENT_BRAINVISION_COLOR_STRUCTURE_CHROMA_FORMULA_FREEZE_v0.7). It computes the frozen chroma-plane
structure score S on rotation-like fixtures and gates it against the frozen primary null
(trajectory-order-permuted full chroma-plane samples), the smooth/spectrum continuity control, the high-chroma
structureless control, neutral controls, and the anti-proxy correlation gauntlet. It invents no formulas, tunes
no constants, changes no fixture scope, makes NO collinear phase-locked claim, and lets NO reporting-only null or
secondary companion create or rescue a PASS.

A PASS here is only a first-pass structure-sensitive descriptor-control validity statement on constructed
synthetic rotation fixtures -- NOT vision, NOT "Brainvision sees", NOT a temporal-order claim (the
trajectory-order permutation is a structure control only).

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no object/scene
understanding; no temporal-order diagnostic; no new descriptor family; no clip corpus.
"""
from __future__ import annotations

import numpy as np

import run_color_descriptor_bridge_v0_3 as cb
import run_color_g5_diagnostic_v0_4 as g5

# ----- frozen constants (v0.7 §3; predeclared, never tuned) -----
CHROMA_GATE_FLOOR = 1e-3
MIN_VALID_FRACTION = 0.5
MIN_VALID_PAIRS = 3
STRUCTURE_BEAT_MARGIN = 0.20
NEUTRAL_STRUCTURE_CEIL = 0.20
PSC_FLOOR = 0.30
AIC_FLOOR = 0.30
MAGNITUDE_CORR_CEIL = 0.30
EPS = 1e-9

T = cb.T_DEFAULT
A = cb.AMP
BASE_Y = cb.BASE_Y
PERM_SEED = 707        # predeclared trajectory-order permutation seed base

IN_SCOPE = ("rot_full", "rot_multi2", "rot_reverse")       # primary PASS fixtures (v0.7 §5)
ARC_REPORT = ("rot_half", "rot_quarter")                    # reporting-only arc-sensitivity fixtures
ANTI_PROXY_STATS = ("chroma_mag", "rg_std", "by_std", "delta_rms", "spectral_centroid", "spectral_spread",
                    "u_directional_delta_rms", "angular_increment_mag", "rg_centroid", "by_centroid",
                    "rg_spread", "by_spread")
# null-relative anti-proxy stats: each entry's stat minus the trajectory-order-permuted-null baseline (v0.7 §7)
NULL_REL_STATS = ("u_directional_delta_rms", "angular_increment_mag", "rg_centroid", "by_centroid",
                  "rg_spread", "by_spread")


# ----------------------------- fixtures / controls (opponent space -> gamut-safe frames) -----------------------------
def rotation_series(name, T=T):
    t = np.arange(T)
    if name == "rot_full":
        th = 2 * np.pi * t / T
    elif name == "rot_multi2":
        th = 4 * np.pi * t / T
    elif name == "rot_reverse":
        th = -2 * np.pi * t / T
    elif name == "rot_half":
        th = np.pi * t / (T - 1)
    elif name == "rot_quarter":
        th = (np.pi / 2) * t / (T - 1)
    else:
        raise ValueError(f"unknown rotation fixture: {name!r}")
    return np.full(T, BASE_Y), A * np.cos(th), A * np.sin(th)


def _series(Yp, RG, BY):
    """Round-trip through the v0.3 bridge (gamut-safe frames) and return spatial-mean RG/BY/CHROMA series."""
    frames = cb._clip_from_series(np.asarray(Yp, float), np.asarray(RG, float), np.asarray(BY, float))
    sm = cb._spatial_means(frames)
    clipped = bool(cb.descriptor(frames)["_gamut"]["clipped"])
    return sm["RG"], sm["BY"], sm["CHROMA"], clipped


def continuity_control(seed=1001):
    """Two INDEPENDENT smooth (length-7 moving-average) signals, normalized to unit peak, scaled to A."""
    rng = np.random.default_rng(seed)
    k = np.ones(7) / 7.0

    def _smooth():
        y = np.convolve(rng.standard_normal(T), k, mode="same")
        return y / (np.max(np.abs(y)) + EPS)
    return np.full(T, BASE_Y), A * _smooth(), A * _smooth()


def structureless_control(seed=2002):
    rng = np.random.default_rng(seed)
    return (np.full(T, BASE_Y), np.clip(A * rng.standard_normal(T), -A, A),
            np.clip(A * rng.standard_normal(T), -A, A))


# ----------------------------- nulls (all operate on RG/BY series) -----------------------------
def null_trajectory_order_permuted(RG, BY, seed):
    """PRIMARY GATE null: permute the temporal order of the full chroma-plane samples (RG,BY jointly), preserving
    the multiset of unit directions and CHROMA while destroying coherent winding."""
    perm = np.random.default_rng(seed).permutation(len(RG))
    return RG[perm], BY[perm]


def null_independent_phase(RG, BY, seed):                    # reporting-only
    return (g5.phase_randomize_1d(RG, np.random.default_rng(seed)),
            g5.phase_randomize_1d(BY, np.random.default_rng(seed + 1)))


def null_permuted_by(RG, BY, seed):                          # reporting-only (changes chroma-plane occupancy)
    return RG, BY[np.random.default_rng(seed).permutation(len(BY))]


def null_shared_phase(RG, BY, seed):                         # reporting-only
    n = len(RG)
    ph = np.random.default_rng(seed).uniform(-np.pi, np.pi, size=np.fft.rfftfreq(n).shape)

    def _apply(x):
        X = np.fft.rfft(x)
        Xs = np.abs(X) * np.exp(1j * (np.angle(X) + ph))   # shared phase OFFSET -> relative phase preserved
        Xs[0] = X[0]
        if n % 2 == 0:
            Xs[-1] = X[-1]
        return np.fft.irfft(Xs, n=n)
    return _apply(RG), _apply(BY)


# ----------------------------- frozen structure score (v0.7 §4) -----------------------------
def structure_score(RG, BY, CHROMA):
    RG = np.asarray(RG, float); BY = np.asarray(BY, float); CHROMA = np.asarray(CHROMA, float)
    n = CHROMA.size
    Ppair = n - 1
    valid = CHROMA >= CHROMA_GATE_FLOOR
    pair_valid = valid[:-1] & valid[1:]
    Np = int(pair_valid.sum())
    if Np < MIN_VALID_PAIRS or Ppair <= 0 or (Np / Ppair) < MIN_VALID_FRACTION:
        return {"neutral": True, "S": 0.0, "PSC": 0.0, "AIC": 0.0, "Np": Np}
    ux = RG / np.maximum(CHROMA, EPS)
    uy = BY / np.maximum(CHROMA, EPS)
    c = (ux[:-1] * uy[1:] - uy[:-1] * ux[1:])[pair_valid]           # signed turn on valid pairs
    PSC = float(abs(c.sum()) / (np.abs(c).sum() + EPS))
    th = np.arctan2(BY, RG)
    dth = np.arctan2(np.sin(th[1:] - th[:-1]), np.cos(th[1:] - th[:-1]))[pair_valid]
    R = float(abs(np.mean(np.exp(1j * dth))))
    AIC = float(np.sqrt(max(0.0, (Np * R ** 2 - 1.0) / (Np - 1)))) if Np >= 2 else 0.0
    S = float(np.sqrt(PSC * AIC))
    return {"neutral": False, "S": S, "PSC": PSC, "AIC": AIC, "Np": Np}


# ----------------------------- anti-proxy statistics -----------------------------
def _spectral_spread(v):
    v = np.asarray(v, float) - np.mean(v)
    F = np.abs(np.fft.rfft(v)) ** 2
    freqs = np.fft.rfftfreq(len(v))
    tot = float(F.sum())
    if tot <= 0:
        return 0.0
    mu = float((freqs * F).sum() / tot)
    return float(np.sqrt(((freqs - mu) ** 2 * F).sum() / tot))


def _stats(RG, BY, CHROMA):
    RG = np.asarray(RG, float); BY = np.asarray(BY, float); CHROMA = np.asarray(CHROMA, float)
    valid = CHROMA >= CHROMA_GATE_FLOOR
    pair_valid = valid[:-1] & valid[1:]
    ux = RG / np.maximum(CHROMA, EPS); uy = BY / np.maximum(CHROMA, EPS)
    if pair_valid.sum() >= 1:
        du = np.sqrt((np.diff(ux) ** 2 + np.diff(uy) ** 2))[pair_valid]
        u_ddr = float(np.sqrt(np.mean(du ** 2)))
        th = np.arctan2(BY, RG)
        dth = np.arctan2(np.sin(th[1:] - th[:-1]), np.cos(th[1:] - th[:-1]))[pair_valid]
        ang_mag = float(np.mean(np.abs(dth)))
    else:
        u_ddr = 0.0
        ang_mag = 0.0
    return {"chroma_mag": float(np.median(CHROMA)), "rg_std": float(RG.std()), "by_std": float(BY.std()),
            "delta_rms": g5._delta_rms(CHROMA), "spectral_centroid": g5._spectral_centroid(CHROMA),
            "spectral_spread": _spectral_spread(CHROMA),
            "u_directional_delta_rms": u_ddr, "angular_increment_mag": ang_mag,
            "rg_centroid": g5._spectral_centroid(RG), "by_centroid": g5._spectral_centroid(BY),
            "rg_spread": _spectral_spread(RG), "by_spread": _spectral_spread(BY)}


# ----------------------------- run -----------------------------
def run(T=T):
    # shared controls (computed once)
    ct = _series(*continuity_control())
    S_cont = structure_score(ct[0], ct[1], ct[2])["S"]
    st = _series(*structureless_control())
    S_struct = structure_score(st[0], st[1], st[2])["S"]

    bank = []          # (name, S, stats, neutral) for anti-proxy + reporting
    per_fixture = {}
    for i, name in enumerate(IN_SCOPE + ARC_REPORT):
        rg, by, ch, clip = _series(*rotation_series(name))
        s_int = structure_score(rg, by, ch)
        # primary gate null: trajectory-order-permuted
        rgp, byp = null_trajectory_order_permuted(rg, by, PERM_SEED + i)
        chp = np.sqrt(rgp ** 2 + byp ** 2)
        s_traj = structure_score(rgp, byp, chp)
        # reporting-only nulls
        s_indep = structure_score(*_series(np.full(T, BASE_Y), *null_independent_phase(rg, by, 3000 + i))[:3])
        s_pby = structure_score(*_series(np.full(T, BASE_Y), *null_permuted_by(rg, by, 4000 + i))[:3])
        s_shared = structure_score(*_series(np.full(T, BASE_Y), *null_shared_phase(rg, by, 5000 + i))[:3])
        in_scope = name in IN_SCOPE
        beat_null = s_int["S"] >= (1 + STRUCTURE_BEAT_MARGIN) * s_traj["S"]
        beat_cont = s_int["S"] >= (1 + STRUCTURE_BEAT_MARGIN) * S_cont
        beat_struct = s_int["S"] >= (1 + STRUCTURE_BEAT_MARGIN) * S_struct
        floors = (s_int["PSC"] >= PSC_FLOOR) and (s_int["AIC"] >= AIC_FLOOR)
        fixture_ok = bool(in_scope and (not s_int["neutral"]) and beat_null and beat_cont and beat_struct and floors)
        per_fixture[name] = {"in_scope": in_scope, "S": round(s_int["S"], 4), "PSC": round(s_int["PSC"], 4),
                             "AIC": round(s_int["AIC"], 4), "S_traj_null": round(s_traj["S"], 4),
                             "S_indep_null": round(s_indep["S"], 4), "S_permuted_by": round(s_pby["S"], 4),
                             "S_shared_phase": round(s_shared["S"], 4), "gamut_clip": clip,
                             "beat_null": beat_null, "beat_continuity": beat_cont,
                             "beat_structureless": beat_struct, "floors_ok": floors, "fixture_ok": fixture_ok,
                             "S_le_null": bool(s_int["S"] <= s_traj["S"])}
        bank.append((name, s_int["S"], _stats(rg, by, ch), s_int["neutral"]))
        if in_scope:                                          # per v0.7 §7: traj + independent nulls of in-scope
            bank.append((name + "_traj_null", s_traj["S"], _stats(rgp, byp, chp), s_traj["neutral"]))
            irg, iby, ich, _ic = _series(np.full(T, BASE_Y), *null_independent_phase(rg, by, 3000 + i))
            bank.append((name + "_indep_null", structure_score(irg, iby, ich)["S"], _stats(irg, iby, ich),
                         False))

    # neutral / reported controls
    neutral = {}
    rot0 = rotation_series("rot_full")
    frames0 = cb._clip_from_series(*rot0)
    for cname, frames in (("grayscale", cb.ctl_grayscale(frames0)),
                          ("saturation_collapse", cb.ctl_saturation_collapse(frames0, 0.0)),
                          ("low_saturation_neutral", cb.fixture("low_saturation_neutral")),
                          ("rough_luminance_only_null", g5.rough_luminance_only_null(0))):
        sm = cb._spatial_means(frames)
        s = structure_score(sm["RG"], sm["BY"], sm["CHROMA"])
        neutral[cname] = {"S": round(s["S"], 4), "neutral": s["neutral"],
                          "ok": bool(s["neutral"] or s["S"] <= NEUTRAL_STRUCTURE_CEIL)}
        # zero-chroma neutrals are gated by the neutral ceiling (below), NOT part of the anti-proxy bank (v0.7 §7)
    color_m, _lum_m = g5.roughness_matched_color_vs_luminance_pair(0)
    smc = cb._spatial_means(color_m)
    s_rm = structure_score(smc["RG"], smc["BY"], smc["CHROMA"])
    neutral["roughness_matched_color(report)"] = {"S": round(s_rm["S"], 4), "neutral": s_rm["neutral"],
                                                  "ok": bool(s_rm["neutral"] or s_rm["S"] <= NEUTRAL_STRUCTURE_CEIL)}
    bank.append(("roughness_matched_color", s_rm["S"], _stats(smc["RG"], smc["BY"], smc["CHROMA"]), s_rm["neutral"]))
    # out-of-scope REPORTING-ONLY fixtures (v0.7 §5): degenerate / collinear -> cannot contribute to PASS
    reported_oos = {}
    for oos in ("red_green_opponent_change", "blue_yellow_opponent_change", "color_only_equal_luminance"):
        smo = cb._spatial_means(cb.fixture(oos))
        so = structure_score(smo["RG"], smo["BY"], smo["CHROMA"])
        reported_oos[oos] = {"S": round(so["S"], 4), "neutral": so["neutral"]}
        bank.append((oos, so["S"], _stats(smo["RG"], smo["BY"], smo["CHROMA"]), so["neutral"]))
    # continuity + structureless into bank
    bank.append(("continuity_control", S_cont, _stats(ct[0], ct[1], ct[2]), False))
    bank.append(("structureless_control", S_struct, _stats(st[0], st[1], st[2]), False))

    # anti-proxy Spearman over the full bank
    Svec = np.array([b[1] for b in bank], float)
    anti = {}
    for stat in ANTI_PROXY_STATS:
        rho = g5._spearman(Svec, np.array([b[2][stat] for b in bank], float))
        anti[stat] = {"spearman": round(rho, 3), "ok": bool(abs(rho) < MAGNITUDE_CORR_CEIL)}
    traj_entries = [b for b in bank if b[0].endswith("_traj_null")]
    for stat in NULL_REL_STATS:
        base = float(np.mean([b[2][stat] for b in traj_entries])) if traj_entries else 0.0
        rho = g5._spearman(Svec, np.array([b[2][stat] - base for b in bank], float))
        anti["nr_" + stat] = {"spearman": round(rho, 3), "ok": bool(abs(rho) < MAGNITUDE_CORR_CEIL)}
    anti_proxy_ok = all(v["ok"] for v in anti.values())

    # verdict (v0.7 §8)
    n_scope = len(IN_SCOPE)
    n_ok = sum(per_fixture[f]["fixture_ok"] for f in IN_SCOPE)
    n_le_null = sum(per_fixture[f]["S_le_null"] for f in IN_SCOPE)
    neutral_ok = all(v["ok"] for v in neutral.values())
    if n_le_null > n_scope / 2:
        verdict = "FAIL"                      # S does not beat the primary gate null on a majority
    elif (n_ok > n_scope / 2) and neutral_ok and anti_proxy_ok:
        verdict = "PASS"
    else:
        verdict = "HOLD"
    first_pass = bool(verdict == "PASS")
    return {"per_fixture": per_fixture, "continuity_S": round(S_cont, 4), "structureless_S": round(S_struct, 4),
            "neutral": neutral, "reported_out_of_scope": reported_oos, "anti_proxy": anti,
            "anti_proxy_ok": anti_proxy_ok,
            "in_scope_ok": n_ok, "in_scope_n": n_scope, "neutral_ok": neutral_ok, "verdict": verdict,
            "first_pass_structure_validity_claim_allowed": first_pass, "temporal_claim_allowed": False}


def format_report(res=None):
    if res is None:
        res = run()
    L = ["BV chroma-structure diagnostic v0.8 (offline; rotation-scope; NOT vision; no order claim; no forced PASS)"]
    L.append("  per-fixture (in-scope rotations gate PASS; arcs reporting-only):")
    L.append(f"    {'fixture':<14}{'scope':>8}{'S':>8}{'PSC':>7}{'AIC':>7}{'S_traj':>8}{'S_indep':>8}{'S_shar':>8}  ok")
    for n, d in res["per_fixture"].items():
        L.append(f"    {n:<14}{('PASS' if d['in_scope'] else 'report'):>8}{d['S']:>8.3f}{d['PSC']:>7.2f}"
                 f"{d['AIC']:>7.2f}{d['S_traj_null']:>8.3f}{d['S_indep_null']:>8.3f}{d['S_shared_phase']:>8.3f}"
                 f"  {d['fixture_ok'] if d['in_scope'] else '-'}")
    L.append(f"  continuity_control S={res['continuity_S']}  structureless_control S={res['structureless_S']}  "
             f"(margin x{1 + STRUCTURE_BEAT_MARGIN})")
    L.append(f"  neutral controls: " + ", ".join(f"{k}={v['S']}({'ok' if v['ok'] else 'FAIL'})"
                                                  for k, v in res["neutral"].items()))
    L.append("  anti-proxy Spearman(S, stat)  (|rho| < %.2f required):" % MAGNITUDE_CORR_CEIL)
    for k, v in res["anti_proxy"].items():
        L.append(f"    {k:<26}{v['spearman']:>7.3f}  {'ok' if v['ok'] else 'FAIL'}")
    L.append(f"  in_scope_ok={res['in_scope_ok']}/{res['in_scope_n']}  neutral_ok={res['neutral_ok']}  "
             f"anti_proxy_ok={res['anti_proxy_ok']}")
    L.append(f"  VERDICT: {res['verdict']}   "
             f"first_pass_structure_validity_claim_allowed={res['first_pass_structure_validity_claim_allowed']}   "
             f"temporal_claim_allowed={res['temporal_claim_allowed']}")
    L.append("  NOTE: offline; rotation-scope only; NO collinear claim; reporting-only nulls (independent/permuted-BY/")
    L.append("  shared-phase) cannot create or rescue PASS; trajectory-order permutation is a structure control, NOT a")
    L.append("  temporal-order claim; NOT vision; NOT 'Brainvision sees'.")
    return "\n".join(L)


if __name__ == "__main__":
    print(format_report())
