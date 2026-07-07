"""BV color G5 roughness/spectrum diagnostic v0.4 (offline research; NOT runtime/integration; NOT vision).

Implements the committed v0.4 plan (docs: TORMENT_BRAINVISION_COLOR_G5_ROUGHNESS_SPECTRUM_PLAN_v0.4) on top of
the v0.3 bridge (run_color_descriptor_bridge_v0_3). It adds the faithful G5 gate as two clearly-scoped sub-gates:

  * G5a -- cross-channel roughness immunity (achievable): rough luminance cannot create chroma; a
    roughness-matched color-vs-luminance pair does not cross-fire; color response does not track roughness.
  * G5b -- within-chroma spectrum diagnostic (predeclared LIKELY FAIL with per-channel temporal-std descriptors):
    an intended color fixture must beat a spectrum-matched null whose Y' is held to the intended Y' series and
    whose RG/BY are INDEPENDENTLY phase-randomized (amplitude spectrum preserved). Because per-channel std is set
    by the amplitude spectrum, RG/BY ratios are ~1 and G5b is expected to fail; RG/BY/CHROMA are reported
    SEPARATELY (never hidden behind a max color response).

Full G5 = G5a AND G5b. A G5a-only pass does NOT license descriptor-control validity; the honest verdict is HOLD.
This makes NO vision / "Brainvision sees" / temporal-order claim. Does NOT tune toward PASS, adds NO new
descriptor family, and does NOT touch RGB-space phase randomization (out of scope).

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no object/scene
understanding; no hue-continuity / edges / coarse-layout / colorxmotion; no temporal-order diagnostic; no clip
corpus.
"""
from __future__ import annotations

import numpy as np

import run_color_descriptor_bridge_v0_3 as cb

# ----- frozen G5 constants (predeclared BEFORE running; never tuned after) -----
NULL_BEAT_MARGIN = 0.20         # intended must exceed matched-null response by this factor (ratio >= 1.20)
LEAK_CEIL_RATIO = 0.10          # cross-channel leak ceiling as a fraction of a color-rich baseline
ROUGHNESS_CORR_CEIL = 0.30      # |Spearman(color response, delta_rms)| must stay below this
CORR_BANK_CONTENT = 0.10        # fixed chroma content for the roughness-correlation bank
CORR_BANK_FREQS = (1, 2, 3, 4, 6)     # sub-Nyquist temporal frequencies (roughness varies,
#                                       content fixed; f=T/2 excluded -- it aliases to a constant)

COLOR_CH = ("RG", "BY", "CHROMA")
G5B_FIXTURES = ("red_green_opponent_change", "blue_yellow_opponent_change", "hue_rotation_like",
                "color_only_equal_luminance")
# predeclared ACTIVE channels per G5b fixture (all channels are still REPORTED; only active ones gate)
G5B_ACTIVE = {
    "red_green_opponent_change": ("RG", "CHROMA"),
    "blue_yellow_opponent_change": ("BY", "CHROMA"),
    "hue_rotation_like": ("RG", "BY"),
    "color_only_equal_luminance": ("RG", "BY", "CHROMA"),
}


# ----------------------------- helpers -----------------------------
def _delta_rms(v):
    v = np.asarray(v, float)
    return float(np.sqrt(np.mean(np.diff(v) ** 2))) if v.size > 1 else 0.0


def _spectral_centroid(v):
    v = np.asarray(v, float) - np.mean(v)
    F = np.abs(np.fft.rfft(v)) ** 2
    freqs = np.fft.rfftfreq(len(v))
    s = float(F.sum())
    return float((freqs * F).sum() / s) if s > 0 else 0.0


def _rank(a):
    a = np.asarray(a, float)
    order = np.argsort(a, kind="mergesort")
    r = np.empty(len(a), float)
    r[order] = np.arange(1, len(a) + 1, dtype=float)
    sa = a[order]
    i, n = 0, len(a)
    while i < n:
        j = i
        while j + 1 < n and sa[j + 1] == sa[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def _spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if x.size < 3 or np.std(x) < 1e-12 or np.std(y) < 1e-12:
        return 0.0
    rx, ry = _rank(x) - _rank(x).mean(), _rank(y) - _rank(y).mean()
    d = float(np.sqrt((rx * rx).sum() * (ry * ry).sum()))
    return float((rx * ry).sum() / d) if d > 0 else 0.0


def phase_randomize_1d(x, rng):
    """Phase-randomize a real 1-D series while PRESERVING its amplitude spectrum (and DC + Nyquist exactly).
    Variance/std is preserved exactly (Parseval); only intermediate phases are randomized."""
    x = np.asarray(x, float)
    n = x.size
    X = np.fft.rfft(x)
    Xs = np.abs(X) * np.exp(1j * rng.uniform(-np.pi, np.pi, size=X.shape))
    Xs[0] = X[0]                       # preserve DC (mean) exactly
    if n % 2 == 0:
        Xs[-1] = X[-1]                 # preserve Nyquist exactly
    return np.fft.irfft(Xs, n=n)


# ----------------------------- predeclared null / control fixtures -----------------------------
def rough_luminance_only_null(seed=0, T=cb.T_DEFAULT):
    rng = np.random.default_rng(100 + seed)
    Yp = np.clip(cb.BASE_Y + 0.25 * rng.standard_normal(T), 0.05, 0.95)   # rough achromatic, chroma 0
    return cb._clip_from_series(Yp, np.zeros(T), np.zeros(T))


def rough_chroma_null(seed=0, T=cb.T_DEFAULT):
    # REPORTING-ONLY in this slice (the v0.4 "no-structure but rough" reference); it is NOT a G5 gate here.
    rng = np.random.default_rng(200 + seed)
    RG = np.clip(0.06 * rng.standard_normal(T), -cb.AMP, cb.AMP)          # rough chroma, no coherent structure
    BY = np.clip(0.06 * rng.standard_normal(T), -cb.AMP, cb.AMP)
    return cb._clip_from_series(np.full(T, cb.BASE_Y), RG, BY)


def roughness_matched_color_vs_luminance_pair(seed=0, T=cb.T_DEFAULT):
    """A color change and a luminance change that share a rough profile -> matched delta_rms / spectrum."""
    rng = np.random.default_rng(300 + seed)
    p = np.clip(rng.standard_normal(T), -2.0, 2.0)
    p = p - p.mean()
    a = 0.05
    color = cb._clip_from_series(np.full(T, cb.BASE_Y), a * p, np.zeros(T))    # RG carries profile, Y' held
    lum = cb._clip_from_series(cb.BASE_Y + a * p, np.zeros(T), np.zeros(T))    # Y' carries same profile, chroma 0
    return color, lum


def spectrum_matched_color_null(intended_name, seed=0, T=cb.T_DEFAULT):
    """Generated in Y'/RG/BY descriptor space: Y' held to the intended fixture's Y' series; RG and BY are
    INDEPENDENTLY phase-randomized (each channel's amplitude spectrum preserved). RGB-space phase randomization
    is out of scope."""
    sm = cb._spatial_means(cb.fixture(intended_name, T=T))
    rng = np.random.default_rng(400 + seed)
    RG_s = phase_randomize_1d(sm["RG"], rng)
    BY_s = phase_randomize_1d(sm["BY"], rng)              # independent phase randomization
    return cb._clip_from_series(sm["Yp"], RG_s, BY_s)     # Y' held to the intended series


def spectrum_matched_color_null_shared_phase(intended_name, seed=0, T=cb.T_DEFAULT):
    """Reporting-only shared-phase variant: RG and BY share one random phase set (not independent)."""
    sm = cb._spatial_means(cb.fixture(intended_name, T=T))
    rng = np.random.default_rng(500 + seed)
    n = T
    ph = rng.uniform(-np.pi, np.pi, size=np.fft.rfftfreq(n).shape)

    def _apply(x):
        X = np.fft.rfft(x)
        Xs = np.abs(X) * np.exp(1j * ph)
        Xs[0] = X[0]
        if n % 2 == 0:
            Xs[-1] = X[-1]
        return np.fft.irfft(Xs, n=n)
    return cb._clip_from_series(sm["Yp"], _apply(sm["RG"]), _apply(sm["BY"]))


# ----------------------------- G5a: cross-channel roughness immunity -----------------------------
def run_g5a(T=cb.T_DEFAULT):
    base_color = cb._color_response(cb.descriptor(cb.fixture("red_green_opponent_change", T=T)))
    leak_ceil = LEAK_CEIL_RATIO * base_color

    d_rlon = cb.descriptor(rough_luminance_only_null(0, T))
    rough_lum_color = cb._color_response(d_rlon)
    a1 = bool(rough_lum_color <= leak_ceil)

    color_m, lum_m = roughness_matched_color_vs_luminance_pair(0, T)
    d_color, d_lum = cb.descriptor(color_m), cb.descriptor(lum_m)
    cross_color_to_Yp = d_color["Yp"]["response"]        # rough color change must not move Y'
    cross_lum_to_color = cb._color_response(d_lum)        # rough luminance must not move color
    a2 = bool(cross_color_to_Yp <= leak_ceil and cross_lum_to_color <= leak_ceil)
    pair_valid = bool(cb._color_response(d_color) > leak_ceil and d_lum["Yp"]["response"] > leak_ceil)

    resp, drm = [], []
    for f in CORR_BANK_FREQS:
        t = np.arange(T)
        fr = cb._clip_from_series(np.full(T, cb.BASE_Y), CORR_BANK_CONTENT * np.sin(2 * np.pi * f * t / T),
                                  np.zeros(T))
        resp.append(cb._color_response(cb.descriptor(fr)))
        drm.append(_delta_rms(cb._spatial_means(fr)["RG"]))
    corr = _spearman(resp, drm)
    a3 = bool(abs(corr) < ROUGHNESS_CORR_CEIL)

    g5a = bool(a1 and a2 and a3 and pair_valid)
    return {"leak_ceil": leak_ceil, "rough_lum_color_response": rough_lum_color,
            "cross_color_to_Yp": cross_color_to_Yp, "cross_lum_to_color": cross_lum_to_color,
            "pair_valid": pair_valid, "roughness_corr": corr,
            "checks": {"a1_rough_lum_no_color": a1, "a2_no_cross_fire": a2, "a3_roughness_corr": a3},
            "G5a": g5a}


# ----------------------------- G5b: within-chroma spectrum diagnostic -----------------------------
def run_g5b(T=cb.T_DEFAULT):
    per_fixture = {}
    ok = 0
    for name in G5B_FIXTURES:
        d_int = cb.descriptor(cb.fixture(name, T=T))
        d_null = cb.descriptor(spectrum_matched_color_null(name, 0, T))
        ratios, ch_ok = {}, {}
        for ch in COLOR_CH:                              # RG / BY / CHROMA reported SEPARATELY
            ri, rn = d_int[ch]["response"], d_null[ch]["response"]
            ratio = (ri / rn) if rn > 1e-12 else (float("inf") if ri > 1e-12 else 1.0)
            ratios[ch] = ratio
            ch_ok[ch] = bool(np.isfinite(ratio) and ratio >= 1.0 + NULL_BEAT_MARGIN)
        fixture_ok = bool(all(ch_ok[ch] for ch in G5B_ACTIVE[name]))   # gate on ACTIVE channels only
        per_fixture[name] = {"ratios": {k: (round(v, 4) if np.isfinite(v) else v) for k, v in ratios.items()},
                             "channel_ok": ch_ok, "fixture_ok": fixture_ok,
                             "null_gamut_clip": bool(d_null["_gamut"]["clipped"])}
        ok += int(fixture_ok)
    majority = ok / len(G5B_FIXTURES)
    any_null_clip = bool(any(per_fixture[n]["null_gamut_clip"] for n in G5B_FIXTURES))
    return {"per_fixture": per_fixture, "fixtures_ok": ok, "n_fixtures": len(G5B_FIXTURES),
            "majority": majority, "any_null_gamut_clip": any_null_clip,
            "G5b": bool(majority > 0.5)}   # no pass from one favorable fixture


def _stats_table(T=cb.T_DEFAULT):
    names = list(G5B_FIXTURES) + ["rough_luminance_only_null", "rough_chroma_null"]
    frames = {n: cb.fixture(n, T=T) for n in G5B_FIXTURES}
    frames["rough_luminance_only_null"] = rough_luminance_only_null(0, T)
    frames["rough_chroma_null"] = rough_chroma_null(0, T)
    out = {}
    for n in names:
        sm = cb._spatial_means(frames[n])
        out[n] = {ch: {"delta_rms": round(_delta_rms(sm[ch]), 5),
                       "spectral_centroid": round(_spectral_centroid(sm[ch]), 5),
                       "response": round(float(sm[ch].std()), 5)} for ch in cb.CHANNELS}
    return out


def run_g5(T=cb.T_DEFAULT):
    g5a = run_g5a(T)
    g5b = run_g5b(T)
    any_null_clip = bool(g5b.get("any_null_gamut_clip", False))
    full_g5 = bool(g5a["G5a"] and g5b["G5b"] and not any_null_clip)
    if any_null_clip:
        verdict = "HOLD"                 # a spectrum-matched null clipped gamut -> G5b untrustworthy
        reason = "spectrum-matched null clipped gamut; G5b untrustworthy -> validity not established"
    elif full_g5:
        verdict = "PASS"                 # first-pass descriptor-CONTROL validity (would still not be vision)
        reason = "full G5 (G5a AND G5b) met"
    elif g5a["G5a"]:
        verdict = "HOLD"                 # G5a passes but G5b unmet -> validity NOT established (expected)
        reason = ("G5a passed; G5b unmet: within-chroma spectrum immunity not achievable with per-channel-std "
                  "descriptors (active RG/BY ratios ~1)")
    else:
        verdict = "FAIL"                 # cross-channel roughness immunity failed
        reason = "G5a failed: cross-channel roughness immunity not established"
    return {"g5a": g5a, "g5b": g5b, "full_G5": full_g5, "verdict": verdict, "reason": reason,
            "any_null_gamut_clip": any_null_clip,
            "first_pass_descriptor_control_validity_claim_allowed": full_g5,
            "temporal_claim_allowed": False,
            "constants": {"NULL_BEAT_MARGIN": NULL_BEAT_MARGIN, "LEAK_CEIL_RATIO": LEAK_CEIL_RATIO,
                          "ROUGHNESS_CORR_CEIL": ROUGHNESS_CORR_CEIL}}


# ----------------------------- report -----------------------------
def format_report(res=None, T=cb.T_DEFAULT):
    if res is None:
        res = run_g5(T=T)
    a, b = res["g5a"], res["g5b"]
    stats = _stats_table(T)
    L = ["BV color G5 roughness/spectrum diagnostic v0.4 (offline; NOT vision; no order claim; does not force PASS)"]
    L.append("  T1 per-fixture intended-vs-null response ratios (per channel; RG/BY/CHROMA separate):")
    L.append(f"    {'fixture':<28}{'RG':>10}{'BY':>10}{'CHROMA':>10}  fixture_ok")
    for n, d in b["per_fixture"].items():
        r = d["ratios"]
        L.append(f"    {n:<28}{str(r['RG']):>10}{str(r['BY']):>10}{str(r['CHROMA']):>10}  {d['fixture_ok']}")
    L.append("  T2 roughness/spectrum statistics (delta_rms | spectral_centroid | response):")
    for n, chd in stats.items():
        parts = "  ".join(f"{ch}:{chd[ch]['delta_rms']}/{chd[ch]['spectral_centroid']}/{chd[ch]['response']}"
                          for ch in ("RG", "BY", "CHROMA"))
        L.append(f"    {n:<28}{parts}")
    L.append("  T3 G5 gate summary:")
    L.append(f"    G5a checks: {a['checks']}  leak_ceil={a['leak_ceil']:.4f}  roughness_corr={a['roughness_corr']:.3f}"
             f"  -> G5a={a['G5a']}")
    L.append(f"      rough_lum_color_response={a['rough_lum_color_response']:.4f}  "
             f"cross_color->Yp={a['cross_color_to_Yp']:.4f}  cross_lum->color={a['cross_lum_to_color']:.4f}  "
             f"pair_valid={a['pair_valid']}")
    L.append(f"    G5b: fixtures_ok={b['fixtures_ok']}/{b['n_fixtures']}  majority={b['majority']:.2f}  -> G5b={b['G5b']}")
    L.append(f"    full_G5={res['full_G5']}  any_null_gamut_clip={res.get('any_null_gamut_clip', False)}")
    L.append("    (rough_chroma_null is REPORTING-ONLY in this slice; not a gate)")
    L.append("  T4 HOLD/FAIL reason:")
    L.append(f"    VERDICT={res['verdict']}  reason: {res['reason']}")
    L.append(f"    first_pass_descriptor_control_validity_claim_allowed="
             f"{res['first_pass_descriptor_control_validity_claim_allowed']}  "
             f"temporal_claim_allowed={res['temporal_claim_allowed']}")
    L.append("  NOTE: G5b is PREDECLARED likely-FAIL: per-channel temporal-std responses are set by the amplitude")
    L.append("  spectrum, so a spectrum-matched null (RG/BY independently phase-randomized) has ~equal RG/BY response")
    L.append("  (ratio ~1). This is the honest limitation, not a tuning target. Offline; NOT vision; no order claim.")
    return "\n".join(L)


if __name__ == "__main__":
    print(format_report())
