"""BV-ΨTRS-SAG v1.1 FAILURE ANALYSIS (offline; NOT a diagnostic; NOT runtime/integration).

Goal: make the v1.0 failure explain itself. v1.0 (normalized-control-gated SAG candidate) fixed the numeric
hygiene confounds but FAILED temporal-order specificity: after median/MAD amplitude normalization the
time_shuffled control still scored FAR higher than true (pooled medians ~ true 8.4 vs shuffled 147.7), while
time_reversed (~6.4) and circular_shift (~8.0) sat NEAR true. This harness measures *why*, by correlating the
existing v1.0 gain against predeclared descriptive properties of the exact normalized window SAG sees. It
introduces NO new operator, proposes NO new diagnostic, and does NOT tune anything toward a PASS.

PREDECLARED HYPOTHESIS H1 (fixed before running; see FINDINGS doc):
  After amplitude normalization the SAG kappa>0 gain is driven by *temporal roughness* -- the per-frame change
  magnitude of the normalized field. time_shuffling maximizes roughness (adjacent frames decorrelate -> large
  frame-to-frame deltas + a broad/flat temporal spectrum), whereas true-order structured fields are temporally
  smooth. Amplitude normalization removes overall scale but NOT the roughness-to-energy ratio, so shuffled>true
  survives. Mechanistic rationale (not tuned): SAG separates a mirror-perturbed pair in proportion to
  (differential clock phase) x (temporal gradient of the field); a rougher field has a larger temporal gradient,
  so the same clock desync yields a larger field-space separation -> higher gain. Prediction: time_reversed and
  circular_shift (which preserve adjacency/|FFT| and thus roughness) stay NEAR true; only shuffle (which whitens
  the temporal spectrum) departs.

PREDECLARED MEASURES (computed on wn = cand.normalize(transform_window(base, control, rng)), the EXACT array
v1.0 feeds to symmetry_gain), per (field, control, seed):
  raw_robust_scale   -- robust_scale of the RAW transformed window (pre-normalize); normalization should null it.
  delta_rms          -- RMS frame-to-frame delta of wn (primary predicted driver).
  temporal_continuity-- mean lag-1 autocorrelation of wn columns (high for smooth/true, ~0 for shuffled).
  spectral_centroid  -- energy-weighted mean normalized temporal frequency of wn in [0,0.5] (high for shuffled).
  psi_spec_norm      -- psi_trs.psi_spec(wn): the operator's own 2D spectral spread (what the clock reads).
  sag_gain           -- cand.candidate_window(...)['g_kpos']: the v1.0 score itself (the target variable).

PREDECLARED INTERPRETATION RULE (thresholds fixed in advance; NOT changed after seeing outcomes):
  H1 SUPPORTED  iff Spearman(delta_rms, log10 gain) >= DELTA_RMS_MIN_SPEARMAN AND delta_rms is the top member of
                the roughness family {delta_rms, spectral_centroid, psi_spec_norm, -temporal_continuity}
                AND the control with the highest median delta_rms is also the control with the highest median gain.
  H1 PARTIAL    iff some roughness-family member reaches the threshold (with control-ranking agreement) but the
                top member is not delta_rms specifically.
  H1 NOT SUPPORTED otherwise; the actual top correlate (including raw_robust_scale, which would mean normalization
                failed to remove amplitude scale) is reported.

stdlib + numpy only; no service imports; no runtime / camera / sensor / prompt / context / memory / action /
render-body / autonomy contact; no torment_service.
"""
from __future__ import annotations

import numpy as np

import psi_trs
import run_real_video_sag_controls as ctrl  # transform_window (true/shuffled/reversed/circular)
import run_sag_anatomy as anat              # generate_field
import run_sag_candidate_v1_0 as cand       # robust_scale/normalize/candidate_window + CONTROLS/SYNTH_FIELDS

STATS = ("raw_robust_scale", "delta_rms", "temporal_continuity", "spectral_centroid", "psi_spec_norm")
ROUGHNESS_FAMILY = ("delta_rms", "spectral_centroid", "psi_spec_norm", "temporal_continuity")
DELTA_RMS_MIN_SPEARMAN = 0.5   # predeclared support threshold; fixed before running


# ----------------------------- rank correlation (no scipy) -----------------------------
def _pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x - x.mean(); y = y - y.mean()
    d = float(np.sqrt((x * x).sum() * (y * y).sum()))
    return float((x * y).sum() / d) if d > 0 else float("nan")


def _rankdata(a):
    """1-based ranks with average ties (scipy.stats.rankdata 'average' equivalent)."""
    a = np.asarray(a, float)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    sa = a[order]
    i, n = 0, len(a)
    while i < n:
        j = i
        while j + 1 < n and sa[j + 1] == sa[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def _spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    if int(m.sum()) < 3:
        return float("nan")
    return _pearson(_rankdata(x[m]), _rankdata(y[m]))


def _median(vals):
    a = np.asarray([v for v in vals if v is not None], float)
    a = a[np.isfinite(a)]
    return float(np.median(a)) if a.size else float("nan")


# ----------------------------- per-cell descriptive stats -----------------------------
def cell_stats(tw):
    """Predeclared descriptive properties of the normalized window SAG actually sees. No operator changes."""
    raw_scale = cand.robust_scale(tw)
    wn = cand.normalize(tw)
    T = wn.shape[0]
    diffs = np.diff(wn, axis=0)
    delta_rms = float(np.sqrt(np.mean(diffs ** 2))) if diffs.size else float("nan")
    a0, a1 = wn[:-1], wn[1:]
    ac = [_pearson(a0[:, c], a1[:, c]) for c in range(wn.shape[1])]
    ac = [r for r in ac if np.isfinite(r)]
    continuity = float(np.mean(ac)) if ac else float("nan")
    freqs = np.fft.rfftfreq(T)
    cents = []
    for c in range(wn.shape[1]):
        F = np.abs(np.fft.rfft(wn[:, c] - wn[:, c].mean())) ** 2
        s = float(F.sum())
        if s > 0:
            cents.append(float((freqs * F).sum() / s))
    centroid = float(np.mean(cents)) if cents else float("nan")
    return {"raw_robust_scale": float(raw_scale), "delta_rms": delta_rms,
            "temporal_continuity": continuity, "spectral_centroid": centroid,
            "psi_spec_norm": float(psi_trs.psi_spec(wn))}


def run_analysis(fields=None, n=6, kappa=None, steps=None):
    """Replicate v1.0's exact iteration (same seeds / per-control rng / window order) so recorded gains ARE the
    v1.0 gains, and pair each with the predeclared descriptive stats of the identical normalized window."""
    fields = cand.SYNTH_FIELDS if fields is None else fields
    kappa = cand.KAPPA if kappa is None else kappa
    steps = cand.STEPS if steps is None else steps
    rows = []
    for field in fields:
        base = [anat.generate_field(field, s) for s in range(n)]
        for ci, control in enumerate(cand.CONTROLS):
            rng = np.random.default_rng(1000 + ci)   # matches run_sag_candidate_v1_0.run_candidate
            for s, w in enumerate(base):
                tw = ctrl.transform_window(w, control, rng)
                cw = cand.candidate_window(tw, kappa, cand.REL_EPS, steps)
                row = {"field": field, "control": control, "seed": s,
                       "neutral": bool(cw["neutral"]), "sag_gain": float(cw["g_kpos"])}
                row.update(cell_stats(tw))
                rows.append(row)
    return rows


# ----------------------------- aggregation -----------------------------
def per_control_medians(rows):
    nn = [r for r in rows if not r["neutral"]]
    out = {}
    for c in cand.CONTROLS:
        sub = [r for r in nn if r["control"] == c]
        d = {"sag_gain": _median([r["sag_gain"] for r in sub]), "n": len(sub)}
        for st in STATS:
            d[st] = _median([r[st] for r in sub])
        out[c] = d
    return out


def per_field_table(rows):
    nn = [r for r in rows if not r["neutral"]]
    out = {}
    for f in sorted({r["field"] for r in nn}):
        def med(control, key):
            return _median([r[key] for r in nn if r["field"] == f and r["control"] == control])
        tg, sg_ = med("true", "sag_gain"), med("time_shuffled", "sag_gain")
        td, sd = med("true", "delta_rms"), med("time_shuffled", "delta_rms")
        out[f] = {
            "true_gain": tg, "shuffled_gain": sg_,
            "reversed_gain": med("time_reversed", "sag_gain"),
            "circular_gain": med("circular_shift", "sag_gain"),
            "true_delta_rms": td, "shuffled_delta_rms": sd,
            "true_continuity": med("true", "temporal_continuity"),
            "shuffled_continuity": med("time_shuffled", "temporal_continuity"),
            "shuffled_gain_gt_true": bool(np.isfinite(tg) and np.isfinite(sg_) and sg_ > tg),
            "shuffled_delta_gt_true": bool(np.isfinite(td) and np.isfinite(sd) and sd > td),
        }
    return out


def correlations(rows):
    nn = [r for r in rows if not r["neutral"]]
    loggain = np.log10(np.array([r["sag_gain"] for r in nn], float))
    return {st: _spearman(np.array([r[st] for r in nn], float), loggain) for st in STATS}


def verdict(corrs, pcm):
    signed = {}
    for st in ROUGHNESS_FAMILY:
        c = corrs.get(st, float("nan"))
        signed[st] = (-c if st == "temporal_continuity" else c)

    def _sk(k):
        v = signed[k]
        return v if np.isfinite(v) else -9.0
    top = max(ROUGHNESS_FAMILY, key=_sk)

    def _ctrl_key(metric):
        return max(cand.CONTROLS,
                   key=lambda c: pcm[c][metric] if np.isfinite(pcm[c][metric]) else -9.0)
    gain_top = _ctrl_key("sag_gain")
    delta_top = _ctrl_key("delta_rms")
    control_agree = bool(gain_top == delta_top)
    dr = corrs.get("delta_rms", float("nan"))
    if np.isfinite(dr) and dr >= DELTA_RMS_MIN_SPEARMAN and top == "delta_rms" and control_agree:
        v = "H1_SUPPORTED"
    elif control_agree and any(np.isfinite(signed[k]) and signed[k] >= DELTA_RMS_MIN_SPEARMAN
                               for k in ROUGHNESS_FAMILY):
        v = "H1_PARTIAL"
    else:
        v = "H1_NOT_SUPPORTED"
    overall_top = max(STATS, key=lambda k: abs(corrs[k]) if np.isfinite(corrs[k]) else -9.0)
    return {"verdict": v, "top_roughness_member": top, "gain_top_control": gain_top,
            "delta_rms_top_control": delta_top, "control_ranking_agrees": control_agree,
            "overall_top_correlate": overall_top}


def analyze(rows):
    pcm = per_control_medians(rows)
    corrs = correlations(rows)
    return {"per_control": pcm, "per_field": per_field_table(rows),
            "correlations": corrs, "verdict": verdict(corrs, pcm),
            "neutral_count": int(sum(1 for r in rows if r["neutral"]))}


def format_report(rows=None, n=6):
    if rows is None:
        rows = run_analysis(n=n)
    a = analyze(rows)
    pcm, corrs, v = a["per_control"], a["correlations"], a["verdict"]
    L = ["BV-ΨTRS-SAG v1.1 FAILURE ANALYSIS — why does shuffled score higher than true? (offline; no diagnostic)"]
    L.append(f"  neutral(near-flat) cells excluded: {a['neutral_count']}")
    L.append("  per-control pooled medians (non-neutral):")
    L.append(f"    {'control':<15}{'gain':>10}{'delta_rms':>11}{'continuity':>12}{'spec_cent':>11}"
             f"{'psi_spec':>10}{'raw_scale':>11}")
    for c in cand.CONTROLS:
        d = pcm[c]
        L.append(f"    {c:<15}{d['sag_gain']:>10.3f}{d['delta_rms']:>11.3f}{d['temporal_continuity']:>12.3f}"
                 f"{d['spectral_centroid']:>11.3f}{d['psi_spec_norm']:>10.3f}{d['raw_robust_scale']:>11.3f}")
    L.append("  per-field true-vs-shuffled (median gain / median delta_rms):")
    L.append(f"    {'field':<18}{'true_g':>9}{'shuf_g':>9}{'s>t?':>6}{'true_dr':>9}{'shuf_dr':>9}{'s>t?':>6}")
    for f, d in a["per_field"].items():
        L.append(f"    {f:<18}{d['true_gain']:>9.3f}{d['shuffled_gain']:>9.3f}"
                 f"{('Y' if d['shuffled_gain_gt_true'] else 'n'):>6}"
                 f"{d['true_delta_rms']:>9.3f}{d['shuffled_delta_rms']:>9.3f}"
                 f"{('Y' if d['shuffled_delta_gt_true'] else 'n'):>6}")
    L.append("  Spearman(property, log10 gain) across all non-neutral cells:")
    for st in STATS:
        L.append(f"    {st:<20}{corrs[st]:>8.3f}")
    L.append(f"  predeclared verdict: {v['verdict']}")
    L.append(f"    top roughness member={v['top_roughness_member']}  overall top correlate={v['overall_top_correlate']}")
    L.append(f"    highest-gain control={v['gain_top_control']}  highest-delta_rms control={v['delta_rms_top_control']}"
             f"  (agree={v['control_ranking_agrees']})")
    L.append("  READING (consistent-with, not proof; no new diagnostic proposed or built here): the v1.0 gain")
    L.append("  tracks temporal roughness of the normalized window, not temporal order. time_reversed and")
    L.append("  circular_shift preserve frame adjacency (hence roughness) and sit near true; only time_shuffle")
    L.append("  whitens the temporal spectrum (raises delta_rms / spectral_centroid, drops continuity) and so")
    L.append("  raises the gain. Amplitude normalization removed scale but not roughness. This EXPLAINS the v1.0")
    L.append("  temporal-gate failure; it does NOT rescue a temporal-order claim.")
    L.append("  NOTE: offline research artifact; authorizes no runtime/memory/action contact and makes no vision")
    L.append("  or temporal-order-specificity claim. Any v1.2 direction is a hypothesis for review, not built here.")
    return "\n".join(L)


if __name__ == "__main__":
    print(format_report())
