"""BV color descriptor bridge v0.3 (offline research; NOT runtime/integration; NOT vision).

First small implementation slice of the committed v0.2 manifest/plan
(docs: TORMENT_BRAINVISION_COLOR_DESCRIPTOR_MANIFEST_PLAN_v0.2). It builds the frozen first-pass opponent
transform, the synthetic fixtures, static color/channel controls, per-channel descriptor summaries, and a
G1-G6 gate report. It makes NO vision claim, NO "Brainvision sees" claim, and NO temporal-order claim.

IMPORTANT (Codex correction): the v0.2 G5 roughness/spectrum gate (spectrum-matched dissociation showing
roughness/spectrum does not explain color-descriptor movement) is **NOT faithfully implemented** in v0.3 -- only
a narrow sanity check (rough luminance must not create chroma) is run. Because full G5 is absent, this slice
CANNOT establish first-pass descriptor-control validity, so the honest verdict is **HOLD**, not PASS. A PASS
would require a faithful G5 and would still be only descriptor-CONTROL validity, never perception.

Frozen terminology (v0.2): Y' is a Rec.709-STYLE LUMA PROXY on gamma-encoded sRGB, NOT true luminance. RG/BY/
CHROMA are FIRST-PASS PROXIES, not perceptual color science. "Y' held" means within a frozen tolerance, not
assumed (and is now REQUIRED for any non-FAIL verdict). Synthetic fixtures assert no unintended gamut clipping
and report measured Y'/RG/BY/CHROMA drift. Calibration and stress entries cannot create a pass; validation
entries drive the gates. No first-pass descriptor-control validity claim unless G1-G5 (incl. a faithful G5)
pass. G6 is an invariant: no temporal-order claim.

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no object recognition;
no scene understanding; no hue-continuity / edges / coarse-layout / colorxmotion; no temporal-order diagnostic.
"""
from __future__ import annotations

import numpy as np

# ----- frozen first-pass transform (Rec.709 luma weights on gamma-encoded sRGB) -----
W_R, W_G, W_B = 0.2126, 0.7152, 0.0722
_RG_COEF = W_G + W_B / 2.0   # inverse coefficient for RG (= 0.7513)

# ----- frozen gate constants (predeclared BEFORE running; never tuned after) -----
COLLAPSE_RATIO = 0.10        # color families must fall to <= this fraction of color-rich baseline
SEPARATION_MARGIN = 5.0      # color response must exceed luminance response by this factor (and mirror)
NEUTRAL_FLOOR = 1e-3         # CHROMA level below this is neutral, not amplified
ROUGHNESS_CEIL = 0.30        # reserved for a faithful G5 (NOT implemented in v0.3)
Y_HOLD_TOL = 1e-3            # "Y' held" means Y' response within this tolerance (required for non-FAIL verdict)
GAMUT_TOL = 1e-6            # RGB must stay within [-tol, 1+tol] for synthetic fixtures

CHANNELS = ("Yp", "RG", "BY", "CHROMA")
T_DEFAULT, HW_DEFAULT = 32, 8
BASE_Y = 0.5
AMP = 0.12                   # opponent amplitude kept small so reconstructed sRGB stays in gamut

FIXTURES = ("luminance_only_change", "red_green_opponent_change", "blue_yellow_opponent_change",
            "saturation_collapse", "hue_rotation_like", "color_only_equal_luminance",
            "grayscale_control", "rough_color_change", "low_saturation_neutral")
ALLOWED_USE = {"luminance_only_change": "calibration", "low_saturation_neutral": "stress"}  # rest: validation
# fixtures that bear RG/BY/CHROMA structure and hold Y' -> used by the strengthened G2 collapse gate
G2_FIXTURES = ("red_green_opponent_change", "blue_yellow_opponent_change",
               "hue_rotation_like", "color_only_equal_luminance")
Y_HELD_FIXTURES = ("red_green_opponent_change", "blue_yellow_opponent_change", "saturation_collapse",
                   "hue_rotation_like", "color_only_equal_luminance")


def allowed_use(name):
    return ALLOWED_USE.get(name, "validation")


# ----------------------------- transform -----------------------------
def forward(rgb):
    """RGB (..,3) in [0,1] -> (Y', RG, BY, CHROMA). Y' is a luma PROXY, not true luminance."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    Yp = W_R * r + W_G * g + W_B * b
    RG = r - g
    BY = b - (r + g) / 2.0
    CH = np.sqrt(RG ** 2 + BY ** 2)
    return Yp, RG, BY, CH


def inverse(Yp, RG, BY):
    """Exact inverse of forward's (Y',RG,BY): R = Y' + (W_G+W_B/2)*RG - W_B*BY; G = R-RG; B = BY+R-RG/2."""
    R = Yp + _RG_COEF * RG - W_B * BY
    G = R - RG
    B = BY + R - RG / 2.0
    return np.stack([R, G, B], axis=-1)


def _clip_from_series(Yp_t, RG_t, BY_t, hw=HW_DEFAULT):
    rgb = inverse(np.asarray(Yp_t, float), np.asarray(RG_t, float), np.asarray(BY_t, float))  # (T,3)
    return np.repeat(np.repeat(rgb[:, None, None, :], hw, axis=1), hw, axis=2)                 # (T,hw,hw,3)


# ----------------------------- synthetic fixtures (generated in opponent space, gamut-safe) -----------------------------
def fixture(name, seed=0, T=T_DEFAULT):
    rng = np.random.default_rng(seed)
    t = np.arange(T)
    s = np.sin(2 * np.pi * t / T)
    c = np.cos(2 * np.pi * t / T)
    Yp = np.full(T, BASE_Y)
    RG = np.zeros(T)
    BY = np.zeros(T)
    if name == "luminance_only_change":
        Yp = BASE_Y + 0.3 * s                                   # brightness varies, chroma 0
    elif name == "red_green_opponent_change":
        RG = AMP * s                                            # RG varies, Y' & (mostly) BY held
    elif name == "blue_yellow_opponent_change":
        BY = AMP * s
    elif name == "saturation_collapse":
        f = np.linspace(1.0, 0.0, T)
        RG = AMP * f
        BY = 0.6 * AMP * f                                      # chroma collapses to 0, Y' held
    elif name == "hue_rotation_like":
        ang = 2 * np.pi * t / T
        RG = AMP * np.cos(ang)
        BY = AMP * np.sin(ang)                                  # chroma const, angle rotates
    elif name == "color_only_equal_luminance":
        RG = AMP * s
        BY = 0.6 * AMP * s                                      # color moves, Y' held const (equal luminance)
    elif name == "grayscale_control":
        pass                                                    # Y' const, chroma 0 -> gray
    elif name == "rough_color_change":
        # NOTE: an UNMATCHED rough color change. The v0.2 `roughness_matched_color_change` fixture (matched to a
        # roughness/spectrum null) is DEFERRED to the faithful-G5 work; this does not claim matched behavior.
        RG = np.clip(0.06 * rng.standard_normal(T), -AMP, AMP)
        BY = np.clip(0.06 * rng.standard_normal(T), -AMP, AMP)
    elif name == "low_saturation_neutral":
        RG = 3e-4 * s
        BY = 3e-4 * c                                           # tiny chroma below the neutral floor
    else:
        raise ValueError(f"unknown fixture: {name!r}")
    return _clip_from_series(Yp, RG, BY)


# ----------------------------- static color / channel controls -----------------------------
def ctl_grayscale(frames):
    Yp, _, _, _ = forward(frames)
    return np.stack([Yp, Yp, Yp], axis=-1)


def ctl_saturation_collapse(frames, factor=0.0):
    Yp, _, _, _ = forward(frames)
    gray = np.stack([Yp, Yp, Yp], axis=-1)
    return gray + factor * (frames - gray)


def ctl_hue_rotation(frames, angle=np.pi / 2):
    Yp, RG, BY, _ = forward(frames)
    cs, sn = np.cos(angle), np.sin(angle)
    return inverse(Yp, cs * RG - sn * BY, sn * RG + cs * BY)


def ctl_channel_shuffle(frames, perm=(1, 2, 0)):
    return frames[..., list(perm)]


def ctl_luminance_only(frames):
    return ctl_grayscale(frames)      # keep the luma proxy, zero chroma (coincides with grayscale here)


def ctl_color_only_luminance_removed(frames):
    """Remove luminance DYNAMICS (equalize per-frame mean Y' to the clip mean) while preserving RG/BY."""
    Yp, _, _, _ = forward(frames)
    frame_mean = Yp.mean(axis=(1, 2))
    shift = (Yp.mean() - frame_mean)[:, None, None, None]
    return frames + shift


# ----------------------------- descriptors -----------------------------
def _spatial_means(frames):
    Yp, RG, BY, CH = forward(frames)
    return {"Yp": Yp.mean((1, 2)), "RG": RG.mean((1, 2)), "BY": BY.mean((1, 2)), "CHROMA": CH.mean((1, 2))}


def descriptor(frames):
    sm = _spatial_means(frames)
    out = {}
    for ch in CHANNELS:
        v = sm[ch]
        out[ch] = {"level": float(v.mean()), "response": float(v.std()),
                   "drift": float(v.max() - v.min()),
                   "delta_rms": float(np.sqrt(np.mean(np.diff(v) ** 2))) if v.size > 1 else 0.0}
    lo, hi = float(np.asarray(frames).min()), float(np.asarray(frames).max())
    out["_gamut"] = {"min": lo, "max": hi, "clipped": bool(lo < -GAMUT_TOL or hi > 1.0 + GAMUT_TOL)}
    return out


def _color_response(d):
    return max(d["RG"]["response"], d["BY"]["response"], d["CHROMA"]["response"])


def _lum_response(d):
    return d["Yp"]["response"]


# ----------------------------- gates -----------------------------
def run_gates(T=T_DEFAULT):
    F = {n: fixture(n, T=T) for n in FIXTURES}
    D = {n: descriptor(F[n]) for n in FIXTURES}

    fixture_clip = any(D[n]["_gamut"]["clipped"] for n in FIXTURES)
    y_held_ok = {n: bool(D[n]["Yp"]["response"] <= Y_HOLD_TOL) for n in Y_HELD_FIXTURES}
    y_held_all = bool(all(y_held_ok.values()))

    # G1 (validation: color_only_equal_luminance): color response >> luminance response
    d_co = D["color_only_equal_luminance"]
    g1 = bool(_color_response(d_co) >= SEPARATION_MARGIN * max(_lum_response(d_co), 1e-12))
    # G2 (strengthened): grayscale AND saturation-collapse collapse color across ALL RG/BY/CHROMA-bearing
    # validation fixtures (not just red_green)
    g2_detail = {}
    g2 = True
    for n in G2_FIXTURES:
        base_c = _color_response(D[n])
        gray_c = _color_response(descriptor(ctl_grayscale(F[n])))
        sat_c = _color_response(descriptor(ctl_saturation_collapse(F[n], 0.0)))
        ok = bool(gray_c <= COLLAPSE_RATIO * max(base_c, 1e-12)
                  and sat_c <= COLLAPSE_RATIO * max(base_c, 1e-12))
        g2_detail[n] = {"base": round(base_c, 5), "grayscale": round(gray_c, 5),
                        "saturation_collapse": round(sat_c, 5), "ok": ok}
        g2 = g2 and ok
    g2 = bool(g2)
    # G3 (validation, mirror of G1): luminance descriptor does not reproduce color-only effects
    g3 = bool(_lum_response(d_co) <= _color_response(d_co) / SEPARATION_MARGIN)
    # G4 (stress: low_saturation_neutral): CHROMA level below the neutral floor (handled neutral)
    g4 = bool(D["low_saturation_neutral"]["CHROMA"]["level"] <= NEUTRAL_FLOOR)
    # G5 (roughness/spectrum): NOT faithfully implemented in v0.3. The v0.2 G5 requires a spectrum-matched
    # dissociation showing roughness/spectrum does not explain color-descriptor movement; that is deferred.
    # Only a narrow sanity check (S1) is run: a rough grayscale must not create a color response.
    g5_faithful = False
    base_rg = _color_response(D["red_green_opponent_change"])
    rng = np.random.default_rng(12345)
    rough_gray = _clip_from_series(np.clip(BASE_Y + 0.3 * rng.standard_normal(T), 0.0, 1.0),
                                   np.zeros(T), np.zeros(T))
    s1_rough_lum_no_chroma = bool(_color_response(descriptor(rough_gray)) <= COLLAPSE_RATIO * max(base_rg, 1e-12))
    # G6 invariant: temporal controls are reporting-only; NO temporal-order claim
    g6_invariant = True

    core = bool(g1 and g2 and g3 and g4)
    if not y_held_all:
        verdict = "FAIL"          # Y'-held precondition violated (machinery not behaving as designed)
    elif fixture_clip:
        verdict = "HOLD"          # untrustworthy machinery (a synthetic fixture clipped)
    elif not core:
        verdict = "FAIL"          # a core color/channel gate (G1-G4) failed
    elif not g5_faithful:
        verdict = "HOLD"          # core gates pass but the faithful roughness/spectrum G5 is not implemented
    else:
        verdict = "PASS"          # would require a faithful G5; first-pass descriptor-CONTROL validity only

    first_pass_descriptor_control_validity_claim_allowed = bool(verdict == "PASS")
    control_matrix = _control_matrix(F["red_green_opponent_change"])
    return {
        "fixtures": D,
        "gates": {"G1_luminance_cannot_fake_color": g1, "G2_color_collapses": g2,
                  "G3_luminance_not_color_only": g3, "G4_low_sat_neutral": g4,
                  "G5_roughness_spectrum_faithful": g5_faithful,
                  "G6_no_temporal_order_claim": g6_invariant},
        "g2_detail": g2_detail,
        "sanity_checks": {"S1_rough_luminance_no_chroma": s1_rough_lum_no_chroma},
        "y_held_ok": y_held_ok, "y_held_all": y_held_all, "fixture_gamut_clip": fixture_clip,
        "control_matrix": control_matrix,
        "separability": {"color_response": _color_response(d_co), "luminance_response": _lum_response(d_co),
                         "separation": _color_response(d_co) / max(_lum_response(d_co), 1e-12)},
        "verdict": verdict,
        "first_pass_descriptor_control_validity_claim_allowed": first_pass_descriptor_control_validity_claim_allowed,
        "temporal_claim_allowed": False,   # G6 invariant
        "constants": {"COLLAPSE_RATIO": COLLAPSE_RATIO, "SEPARATION_MARGIN": SEPARATION_MARGIN,
                      "NEUTRAL_FLOOR": NEUTRAL_FLOOR, "Y_HOLD_TOL": Y_HOLD_TOL},
    }


def _control_matrix(base_frames):
    """Response of each channel under each static control on the base fixture."""
    controls = {"grayscale": ctl_grayscale, "saturation_collapse": lambda f: ctl_saturation_collapse(f, 0.0),
                "hue_rotation": ctl_hue_rotation, "channel_shuffle": ctl_channel_shuffle,
                "luminance_only": ctl_luminance_only, "color_only": ctl_color_only_luminance_removed}
    base_d = descriptor(base_frames)
    out = {"_base": {ch: round(base_d[ch]["response"], 5) for ch in CHANNELS}}
    for cname, fn in controls.items():
        d = descriptor(fn(base_frames))
        out[cname] = {ch: round(d[ch]["response"], 5) for ch in CHANNELS}
    return out


# ----------------------------- report -----------------------------
def format_report(res=None, T=T_DEFAULT):
    if res is None:
        res = run_gates(T=T)
    D, g = res["fixtures"], res["gates"]
    L = ["BV color descriptor bridge v0.3 (offline; first-pass Y'/RG/BY/CHROMA proxies; NOT vision; no order claim)"]
    L.append("  T1 manifest summary: 9 synthetic fixtures "
             f"(calibration=1, validation=7, stress=1); fixture_gamut_clip={res['fixture_gamut_clip']}  "
             f"y_held_all={res['y_held_all']}")
    L.append("  T2 per-fixture descriptor response (temporal std of spatial mean) [use]:")
    L.append(f"    {'fixture':<30}{'Yp':>9}{'RG':>9}{'BY':>9}{'CHROMA':>9}  use")
    for n in FIXTURES:
        d = D[n]
        L.append(f"    {n:<30}{d['Yp']['response']:>9.4f}{d['RG']['response']:>9.4f}"
                 f"{d['BY']['response']:>9.4f}{d['CHROMA']['response']:>9.4f}  {allowed_use(n)}")
    L.append("  T3 control response matrix (channel response under each static control on the red_green base):")
    cm = res["control_matrix"]
    L.append(f"    {'control':<20}{'Yp':>9}{'RG':>9}{'BY':>9}{'CHROMA':>9}")
    for cname in ("_base", "grayscale", "saturation_collapse", "hue_rotation", "channel_shuffle",
                  "luminance_only", "color_only"):
        row = cm[cname]
        L.append(f"    {cname:<20}{row['Yp']:>9.4f}{row['RG']:>9.4f}{row['BY']:>9.4f}{row['CHROMA']:>9.4f}")
    sp = res["separability"]
    L.append(f"  T4 separability (color_only_equal_luminance): color_response={sp['color_response']:.4f}  "
             f"luminance_response={sp['luminance_response']:.2e}  separation={sp['separation']:.1f}x")
    ls = D["low_saturation_neutral"]["CHROMA"]["level"]
    L.append(f"  T5 neutral/stress: low_saturation_neutral CHROMA level={ls:.2e}  (NEUTRAL_FLOOR={NEUTRAL_FLOOR})")
    L.append(f"  G2 collapse detail (strengthened across {len(res['g2_detail'])} fixtures): "
             f"all_ok={all(v['ok'] for v in res['g2_detail'].values())}")
    L.append(f"  sanity: {res['sanity_checks']}  (S1 is NOT the faithful v0.2 G5)")
    L.append(f"  T6 gates: {g}")
    L.append(f"  VERDICT: {res['verdict']}   "
             f"first_pass_descriptor_control_validity_claim_allowed={res['first_pass_descriptor_control_validity_claim_allowed']}"
             f"   temporal_claim_allowed={res['temporal_claim_allowed']}")
    L.append("  NOTE: G5 (roughness/spectrum) is NOT faithfully implemented in v0.3, so full descriptor-control")
    L.append("  validity is NOT established -> verdict HOLD. This is offline sanity-checking of constructed fixtures;")
    L.append("  NOT vision, NOT 'Brainvision sees', NOT a temporal-order claim (G6 invariant). Temporal reporting-only.")
    return "\n".join(L)


if __name__ == "__main__":
    print(format_report())
