"""BV-ΨTRS v1.2a ordered-recurrence / continuity harness (offline research; NOT runtime/integration).

Implements EXACTLY the committed v1.2a plan (docs: TORMENT_BRAINVISION_ORDER_SENSITIVE_RECURRENCE_PLAN_v1.2a).
It builds a recurrence-quantification (RQA) diagnostic on the per-window normalized descriptor field and asks
whether ordered-continuity structure (diagonal determinism, DET) separates ordered/adjacent temporal conditions
from time-shuffle WITHOUT being a roughness/spectral-spread meter. It does NOT tune, does NOT force a PASS, and
makes NO temporal-order or vision claim unless the predeclared gates pass.

Frozen constants (fixed BEFORE running; do not change after outcomes):
  * embedding m = 1 (frame recurrence), tau = 1;               [EMBED_M / TAU]
  * off-diagonal only: line of identity (i==j) excluded from RR/DET/L/Lmax/ENTR/LAM/TT;
  * Theiler window w = 0 primary (excludes only the main diagonal); w in {1,2} secondary sensitivity only;
  * RR_target = 0.10 (eps is the per-window RR_target quantile of eligible off-diagonal distances);
  * diagonal minimum lmin = 3 primary; lmin = 2 sensitivity only; vertical vmin = 2 secondary;
  * primary statistic DET; secondary reported L, Lmax, ENTR, LAM, TT, RR;
  * near-flat windows neutral/excluded (v1.0 robust-scale FLOOR);
  * Tier-A beat margin M = 0.20; surrogate z-threshold Z = 2.0; roughness-invariance ceiling |rho| < 0.30.

stdlib + numpy only; no service imports; no runtime / camera / sensor / prompt / context / memory / action /
render-body / autonomy contact; no torment_service.
"""
from __future__ import annotations

import numpy as np

import run_real_video_sag_controls as ctrl   # transform_window (true/shuffled/reversed/circular)
import run_sag_anatomy as anat               # generate_field (synthetic bank)
import run_sag_candidate_v1_0 as cand        # robust_scale / normalize / FLOOR / SYNTH_FIELDS / CONTROLS
import run_sag_failure_analysis_v1_1 as fa    # _spearman / _median / cell_stats(delta_rms)

# ----- frozen constants (predeclared) -----
EMBED_M = 1
TAU = 1
THEILER_PRIMARY = 0
THEILER_SENS = (1, 2)
RR_TARGET = 0.10
LMIN_PRIMARY = 3
LMIN_SENS = 2
VMIN = 2
TIER_A_MARGIN = 0.20      # ordered-group DET must exceed shuffle DET by factor > 1 + M
SURR_Z = 2.0
ROUGH_CORR_CEIL = 0.30    # |Spearman(DET, delta_rms)| must be below this (roughness invariance)
N_SURR = 19               # shuffle surrogates per window for the DET z-score
N_DEFAULT = 6

DISSOCIATION = ("rough_ordered", "smooth_disordered")
FIELDS = tuple(cand.SYNTH_FIELDS) + DISSOCIATION
ORDERED_GROUP = ("true", "time_reversed", "circular_shift")
DET_KEYS = ("RR", "DET", "L", "Lmax", "ENTR", "LAM", "TT")


# ----------------------------- frozen dissociation-probe generators -----------------------------
def _rough_ordered(seed, T=anat.T_DEFAULT, C=anat.C_DEFAULT):
    """High-frequency deterministic periodic trajectory (integer period T//(T//4)=4): ROUGH but with a known,
    exact recurrence order (states repeat every 4 frames -> long period-offset diagonals)."""
    t = np.arange(T, dtype=float)
    f = T // 4
    ph = 0.1 * seed
    return np.stack([np.sin(2 * np.pi * f * t / T + 2 * np.pi * c / C + ph) for c in range(C)], axis=1)


def _smooth_disordered(seed, T=anat.T_DEFAULT, C=anat.C_DEFAULT):
    """Heavily smoothed random trajectory: SMOOTH (low frame-to-frame delta) but with no periodic / ordered
    recurrence (a non-repeating random wander)."""
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((T, C))
    k = np.ones(7) / 7.0
    return np.stack([np.convolve(w[:, c], k, mode="same") for c in range(C)], axis=1)


def generate_field(kind, seed, T=anat.T_DEFAULT, C=anat.C_DEFAULT):
    if kind == "rough_ordered":
        return _rough_ordered(seed, T, C)
    if kind == "smooth_disordered":
        return _smooth_disordered(seed, T, C)
    return anat.generate_field(kind, seed, T, C)


def phase_randomize(w, rng):
    """Amplitude-spectrum-matched surrogate: preserve |FFT| per channel, randomize temporal phase (destroys
    higher-order/ordered structure while keeping the power spectrum, hence roughness)."""
    w = np.asarray(w, float)
    T, C = w.shape
    out = np.empty_like(w)
    for c in range(C):
        F = np.fft.rfft(w[:, c])
        mag = np.abs(F)
        phases = np.angle(F)
        rand = rng.uniform(-np.pi, np.pi, size=phases.shape)
        rand[0] = phases[0]
        if T % 2 == 0:
            rand[-1] = phases[-1]
        out[:, c] = np.fft.irfft(mag * np.exp(1j * rand), n=T)
    return out


# ----------------------------- RQA core (off-diagonal only) -----------------------------
def _runs(bmask):
    """Lengths of maximal runs of True in a 1-D boolean array."""
    b = np.asarray(bmask, bool).astype(np.int8)
    d = np.diff(np.concatenate(([0], b, [0])))
    return np.flatnonzero(d == -1) - np.flatnonzero(d == 1)


def rqa(wn, rr_target=RR_TARGET, theiler=THEILER_PRIMARY, lmin=LMIN_PRIMARY, vmin=VMIN):
    """Recurrence-quantification measures on frame states (m=1). Main diagonal + Theiler band excluded from
    every measure. eps is the rr_target quantile of eligible off-diagonal distances (RR matching by rule)."""
    wn = np.asarray(wn, float)
    T = wn.shape[0]
    diff = wn[:, None, :] - wn[None, :, :]
    D = np.sqrt(np.einsum("ijc,ijc->ij", diff, diff))
    iu, ju = np.triu_indices(T, k=theiler + 1)   # eligible off-diagonal upper pairs
    elig = D[iu, ju]
    if elig.size == 0:
        return {k: (0.0 if k != "Lmax" else 0) for k in DET_KEYS} | {"eps": 0.0, "RR_num": 0}
    eps = float(np.quantile(elig, rr_target))
    R = D <= eps
    rec_upper = R[iu, ju]
    RR = float(rec_upper.mean())
    RR_num = int(rec_upper.sum())
    # diagonal lines over upper offsets k = theiler+1 .. T-1
    diag = [_runs(np.diagonal(R, offset=k)) for k in range(theiler + 1, T)]
    diag = np.concatenate(diag) if diag else np.array([], int)
    long = diag[diag >= lmin]
    DET = float(long.sum() / RR_num) if RR_num > 0 else 0.0
    L = float(long.mean()) if long.size else 0.0
    Lmax = int(diag.max()) if diag.size else 0
    if long.size:
        _v, cts = np.unique(long, return_counts=True)
        p = cts / cts.sum()
        ENTR = float(-(p * np.log(p)).sum())
    else:
        ENTR = 0.0
    # vertical lines (LAM/TT) over full masked matrix columns
    vert = []
    for j in range(T):
        col = R[:, j].copy()
        col[max(0, j - theiler):j + theiler + 1] = False
        vert.append(_runs(col))
    vert = np.concatenate(vert) if vert else np.array([], int)
    full_mask = np.abs(np.subtract.outer(np.arange(T), np.arange(T))) > theiler
    rec_full = int((R & full_mask).sum())
    vlong = vert[vert >= vmin]
    LAM = float(vlong.sum() / rec_full) if rec_full > 0 else 0.0
    TT = float(vlong.mean()) if vlong.size else 0.0
    return {"RR": RR, "DET": DET, "L": L, "Lmax": Lmax, "ENTR": ENTR, "LAM": LAM, "TT": TT,
            "eps": eps, "RR_num": RR_num}


def det_z(wn, rng, n_surr=N_SURR, **kw):
    """DET z-score of wn against its own shuffle surrogates (order destroyed, marginal/roughness held)."""
    det0 = rqa(wn, **kw)["DET"]
    surr = np.array([rqa(wn[rng.permutation(wn.shape[0])], **kw)["DET"] for _ in range(n_surr)])
    return float((det0 - surr.mean()) / (surr.std() + 1e-9))


# ----------------------------- run -----------------------------
def run_recurrence(fields=FIELDS, n=N_DEFAULT, theiler=THEILER_PRIMARY, lmin=LMIN_PRIMARY):
    rows = []
    for fi, field in enumerate(fields):
        base = [generate_field(field, s) for s in range(n)]
        for ci, control in enumerate(cand.CONTROLS):
            rng_t = np.random.default_rng(1000 + ci)     # matches the arc's transform seeding
            for si, w in enumerate(base):
                tw = ctrl.transform_window(w, control, rng_t)
                neutral = bool(cand.robust_scale(tw) < cand.FLOOR)
                row = {"field": field, "control": control, "seed": si, "neutral": neutral}
                if neutral:
                    row.update({k: float("nan") for k in DET_KEYS})
                    row.update({"DET_z": float("nan"), "delta_rms": float("nan")})
                    rows.append(row)
                    continue
                wn = cand.normalize(tw)
                q = rqa(wn, theiler=theiler, lmin=lmin)
                surr_rng = np.random.default_rng(70000 + fi * 1000 + ci * 100 + si)
                row.update({k: q[k] for k in DET_KEYS})
                row["DET_z"] = det_z(wn, surr_rng, theiler=theiler, lmin=lmin)
                row["delta_rms"] = fa.cell_stats(tw)["delta_rms"]
                rows.append(row)
    return rows


def _spectrum_matched_det(fields=FIELDS, n=N_DEFAULT, theiler=THEILER_PRIMARY, lmin=LMIN_PRIMARY):
    """Pooled median DET on amplitude-spectrum-matched (phase-randomized) surrogates of the true windows."""
    dets = []
    for fi, field in enumerate(fields):
        for si in range(n):
            w = generate_field(field, si)
            if cand.robust_scale(w) < cand.FLOOR:
                continue
            rng = np.random.default_rng(80000 + fi * 1000 + si)
            wn = cand.normalize(phase_randomize(w, rng))
            dets.append(rqa(wn, theiler=theiler, lmin=lmin)["DET"])
    return fa._median(dets)


# ----------------------------- aggregation / tables -----------------------------
def _nn(rows):
    return [r for r in rows if not r["neutral"]]


def t1_per_control(rows):
    out = {}
    for c in cand.CONTROLS:
        sub = [r for r in _nn(rows) if r["control"] == c]
        out[c] = {k: fa._median([r[k] for r in sub]) for k in ("RR", "DET", "L", "LAM", "ENTR", "DET_z")}
    return out


def _field_ctrl_median(rows, field, control, key):
    return fa._median([r[key] for r in _nn(rows)
                       if r["field"] == field and r["control"] == control])


def t2_tier_a(rows):
    out = {}
    for field in sorted({r["field"] for r in _nn(rows)}):
        grp = {c: _field_ctrl_median(rows, field, c, "DET") for c in ORDERED_GROUP}
        if any(not np.isfinite(v) for v in grp.values()):
            continue
        ordered_min = float(min(grp.values()))
        shuffle = _field_ctrl_median(rows, field, "time_shuffled", "DET")
        true_z = _field_ctrl_median(rows, field, "true", "DET_z")
        beats = bool(np.isfinite(shuffle) and ordered_min > shuffle * (1.0 + TIER_A_MARGIN))
        zc = bool(np.isfinite(true_z) and true_z >= SURR_Z)
        out[field] = {"DET_true": grp["true"], "DET_reversed": grp["time_reversed"],
                      "DET_circular": grp["circular_shift"], "ordered_group_min": ordered_min,
                      "DET_shuffled": shuffle, "true_z": true_z, "vote": bool(beats and zc)}
    return out


def t3_roughness_invariance(rows, spectrum_det):
    nn = _nn(rows)
    pooled_shuffle = fa._median([r["DET"] for r in nn if r["control"] == "time_shuffled"])
    pooled_ordered = fa._median([r["DET"] for r in nn if r["control"] in ORDERED_GROUP])
    rough_ordered = _field_ctrl_median(rows, "rough_ordered", "true", "DET")
    smooth_dis = _field_ctrl_median(rows, "smooth_disordered", "true", "DET")
    rho = fa._spearman(np.array([r["DET"] for r in nn], float),
                       np.array([r["delta_rms"] for r in nn], float))
    # predeclared dissociation checks (ALL required): shuffle low, rough-but-ordered high, smooth-but-disordered
    # low, spectrum-matched low, and DET not correlated with roughness. Each is exposed so a FAIL names its cause.
    ordered_beats_shuffle = (
        np.isfinite(pooled_shuffle)
        and np.isfinite(pooled_ordered)
        and pooled_shuffle < pooled_ordered
    )
    rough_high = (
        np.isfinite(rough_ordered)
        and np.isfinite(pooled_shuffle)
        and rough_ordered > pooled_shuffle * (1.0 + TIER_A_MARGIN)
    )
    smooth_low = (
        np.isfinite(smooth_dis)
        and np.isfinite(pooled_shuffle)
        and smooth_dis <= pooled_shuffle * (1.0 + TIER_A_MARGIN)
    )
    spectrum_low = (
        np.isfinite(spectrum_det)
        and np.isfinite(pooled_shuffle)
        and spectrum_det <= pooled_shuffle * (1.0 + TIER_A_MARGIN)
    )
    corr_ok = np.isfinite(rho) and abs(rho) < ROUGH_CORR_CEIL
    invariance_pass = bool(
        ordered_beats_shuffle and rough_high and smooth_low and spectrum_low and corr_ok
    )
    return {"pooled_shuffle_DET": pooled_shuffle, "pooled_ordered_DET": pooled_ordered,
            "rough_ordered_DET": rough_ordered, "smooth_disordered_DET": smooth_dis,
            "spectrum_matched_DET": spectrum_det, "spearman_DET_delta_rms": rho,
            "ordered_beats_shuffle": bool(ordered_beats_shuffle), "rough_high": bool(rough_high),
            "smooth_low": bool(smooth_low), "spectrum_low": bool(spectrum_low),
            "corr_ok": bool(corr_ok), "invariance_pass": invariance_pass}


def t4_tier_b(rows):
    """Symmetric DET is time-reversal invariant, so it is NOT used to claim Tier B. Reported for evidence only;
    verdict is NA unless a genuine directional variant is supplied (none is designed in v1.2a)."""
    out = {}
    for field in sorted({r["field"] for r in _nn(rows)}):
        dt = _field_ctrl_median(rows, field, "true", "DET")
        dr = _field_ctrl_median(rows, field, "time_reversed", "DET")
        out[field] = {"DET_true": dt, "DET_reversed": dr,
                      "symmetric_equal": bool(np.isfinite(dt) and np.isfinite(dr)
                                              and abs(dt - dr) <= 1e-6 * (1 + abs(dt)))}
    return {"per_field": out, "directional_variant": None, "verdict": "NA"}


def secondary_sensitivity(fields=FIELDS, n=N_DEFAULT):
    """NON-RESCUING secondary sensitivity (plan-allowed): report the roughness-invariance Spearman and the
    pooled ordered/shuffle DET gap for Theiler w in {1,2} and for lmin=2. Per the v1.2a plan these are
    REPORTING ONLY and CANNOT change or rescue the primary (w=0, lmin=3) verdict."""
    def _probe(theiler, lmin):
        det, drm, po, ps = [], [], [], []
        for field in fields:
            base = [generate_field(field, s) for s in range(n)]
            for ci, control in enumerate(cand.CONTROLS):
                rng_t = np.random.default_rng(1000 + ci)   # mirror the primary run's per-control seeding
                for w in base:
                    tw = ctrl.transform_window(w, control, rng_t)
                    if cand.robust_scale(tw) < cand.FLOOR:
                        continue
                    d = rqa(cand.normalize(tw), theiler=theiler, lmin=lmin)["DET"]
                    det.append(d); drm.append(fa.cell_stats(tw)["delta_rms"])
                    if control in ORDERED_GROUP:
                        po.append(d)
                    elif control == "time_shuffled":
                        ps.append(d)
        rho = fa._spearman(np.array(det, float), np.array(drm, float))
        return {"theiler": theiler, "lmin": lmin, "spearman_DET_delta_rms": rho,
                "pooled_ordered_DET": fa._median(po), "pooled_shuffle_DET": fa._median(ps),
                "invariance_would_pass": bool(np.isfinite(rho) and abs(rho) < ROUGH_CORR_CEIL)}
    return {"w1_lmin3": _probe(1, LMIN_PRIMARY), "w2_lmin3": _probe(2, LMIN_PRIMARY),
            "w0_lmin2": _probe(THEILER_PRIMARY, LMIN_SENS)}


def analyze(rows=None, n=N_DEFAULT):
    if rows is None:
        rows = run_recurrence(n=n)
    t1 = t1_per_control(rows)
    t2 = t2_tier_a(rows)
    t3 = t3_roughness_invariance(rows, _spectrum_matched_det(n=n))
    t4 = t4_tier_b(rows)
    votes = [v["vote"] for v in t2.values()]
    field_majority = (sum(votes) / len(votes)) if votes else 0.0
    pooled_ordered_beats = all(
        np.isfinite(t1[c]["DET"]) and np.isfinite(t1["time_shuffled"]["DET"])
        and t1[c]["DET"] > t1["time_shuffled"]["DET"] * (1.0 + TIER_A_MARGIN)
        for c in ORDERED_GROUP)
    tier_a_pass = bool(t3["invariance_pass"] and votes and field_majority > 0.5 and pooled_ordered_beats)
    neutral_count = int(sum(1 for r in rows if r["neutral"]))
    if not t3["invariance_pass"]:
        verdict = "FAIL"          # behaves as a roughness/continuity-inverse meter; no order claim
    elif tier_a_pass:
        verdict = "PASS"          # Tier-A undirected order, offline only
    else:
        verdict = "HOLD"          # invariance OK but ordered group does not beat shuffle on a strict majority
    gates = {
        "roughness_invariance_prereq": t3["invariance_pass"],
        "tier_A_undirected_order": tier_a_pass,
        "tier_B_arrow_of_time": t4["verdict"],           # NA (no directional variant)
        "field_majority": round(field_majority, 3),
        "pooled_ordered_beats_shuffle": pooled_ordered_beats,
        "near_flat_neutral_count": neutral_count,
    }
    return {"T1_per_control": t1, "T2_tier_a": t2, "T3_roughness_invariance": t3,
            "T4_tier_b": t4, "T5_gates": gates,
            "S_secondary_non_rescuing": secondary_sensitivity(n=n), "verdict": verdict,
            # historical directional temporal-order claim stays False; only undirected order can flip on PASS
            "undirected_order_claim_allowed": bool(t3["invariance_pass"] and tier_a_pass),
            "temporal_claim_allowed": False}


def format_report(res=None, n=N_DEFAULT):
    if res is None:
        res = analyze(n=n)
    t1, t2, t3, g = res["T1_per_control"], res["T2_tier_a"], res["T3_roughness_invariance"], res["T5_gates"]
    L = ["BV-ΨTRS v1.2a ordered-recurrence / continuity harness (offline; RQA DET; does not force a PASS)"]
    L.append("  T1 per-control pooled medians (non-neutral):")
    L.append(f"    {'control':<15}{'RR':>8}{'DET':>9}{'L':>8}{'LAM':>8}{'ENTR':>8}{'DET_z':>9}")
    for c in cand.CONTROLS:
        d = t1[c]
        L.append(f"    {c:<15}{d['RR']:>8.3f}{d['DET']:>9.3f}{d['L']:>8.2f}{d['LAM']:>8.3f}"
                 f"{d['ENTR']:>8.3f}{d['DET_z']:>9.2f}")
    L.append("  T2 per-field Tier-A (median DET; ordered group {true,reversed,circular} vs shuffle):")
    L.append(f"    {'field':<18}{'true':>8}{'rev':>8}{'circ':>8}{'ord_min':>9}{'shuffle':>9}{'true_z':>8}{'vote':>6}")
    for f, d in t2.items():
        L.append(f"    {f:<18}{d['DET_true']:>8.3f}{d['DET_reversed']:>8.3f}{d['DET_circular']:>8.3f}"
                 f"{d['ordered_group_min']:>9.3f}{d['DET_shuffled']:>9.3f}{d['true_z']:>8.2f}"
                 f"{('Y' if d['vote'] else 'n'):>6}")
    L.append("  T3 roughness invariance / dissociation:")
    L.append(f"    pooled_ordered_DET={t3['pooled_ordered_DET']:.3f}  pooled_shuffle_DET={t3['pooled_shuffle_DET']:.3f}")
    L.append(f"    rough_ordered_DET={t3['rough_ordered_DET']:.3f}  smooth_disordered_DET={t3['smooth_disordered_DET']:.3f}"
             f"  spectrum_matched_DET={t3['spectrum_matched_DET']:.3f}")
    L.append(f"    Spearman(DET, delta_rms)={t3['spearman_DET_delta_rms']:.3f}  (|rho|<{ROUGH_CORR_CEIL} required)"
             f"  -> invariance_pass={t3['invariance_pass']}")
    L.append(f"    invariance subchecks: ordered_beats_shuffle={t3['ordered_beats_shuffle']} "
             f"rough_high={t3['rough_high']} smooth_low={t3['smooth_low']} spectrum_low={t3['spectrum_low']} "
             f"corr_ok={t3['corr_ok']}")
    L.append(f"  T4 Tier-B arrow-of-time: verdict={res['T4_tier_b']['verdict']} "
             f"(symmetric DET is time-reversal invariant; not used for a Tier-B claim)")
    L.append(f"  T5 gates: {g}")
    ss = res.get("S_secondary_non_rescuing", {})
    if ss:
        L.append("  SECONDARY sensitivity (NON-RESCUING; cannot change the primary w=0/lmin=3 verdict):")
        for k, d in ss.items():
            L.append(f"    {k:<10} rho(DET,delta_rms)={d['spearman_DET_delta_rms']:+.3f}"
                     f"  ordered_DET={d['pooled_ordered_DET']:.3f}  shuffle_DET={d['pooled_shuffle_DET']:.3f}"
                     f"  would_pass_invariance={d['invariance_would_pass']}")
    L.append(f"  VERDICT: {res['verdict']}   undirected_order_claim_allowed={res['undirected_order_claim_allowed']}"
             f"   temporal_claim_allowed(directional)={res['temporal_claim_allowed']}")
    L.append("  NOTE: offline research artifact; no runtime/memory/action contact; no vision claim; a Tier-A PASS")
    L.append("  supports only an offline UNDIRECTED order/continuity statement, never an arrow-of-time claim.")
    return "\n".join(L)


if __name__ == "__main__":
    print(format_report())
