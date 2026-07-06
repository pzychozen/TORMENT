"""Normalized-control-gated SAG candidate v1.0 (offline research candidate; NOT runtime/integration).

A minimal wrapper around the existing SAG that tries to address the v0.4-v0.8 failure modes:
  * amplitude-scale sensitivity  -> per-window robust (median/MAD) normalization to unit scale;
  * low-energy kappa=0 instability -> a predeclared floor: near-flat windows report NEUTRAL/non-amplifying;
  * spike-heavy gains            -> robust (MAD) scale + median score, not mean/max;
  * shuffle/reverse/circular controls -> first-class temporal-control gate: temporal_claim_allowed stays
    False unless ALL predeclared gates pass (see analyze()).

This does NOT claim Brainvision works and does NOT force a PASS. If any gate fails, it reports failure and
names the failed gate(s). stdlib + numpy; no service imports; no runtime / camera / sensor / prompt /
context / memory / action / render-body / autonomy contact.
"""
from __future__ import annotations

import numpy as np

import run_real_video_sag_controls as ctrl  # transform_window (true/shuffled/reversed/circular)
import run_sag_anatomy as anat              # generate_field
import symmetry_gain as sg

FLOOR = 1e-3        # predeclared robust-scale floor: below this a window is NEUTRAL
REL_EPS = 1e-2      # relative perturbation (field is unit-scale after normalization)
KAPPA = 3.0
STEPS = 40
CONTROLS = ("true", "time_shuffled", "time_reversed", "circular_shift")
SYNTH_FIELDS = ("constant", "tiny_noise", "white_noise", "smooth_ramp", "sine",
                "sine_phase_shift", "spike", "lowpass")
_COHERENT = 1.1
_MARGIN = 0.05          # true must exceed a control median by > this factor to count as beating it
# predeclared temporal-claim gate thresholds (fixed in advance; NOT tuned after seeing outcomes)
K0_COHERENT_MIN = 0.95     # gate 3: minimum kappa=0 coherence rate required for any temporal claim
FIELD_MAJORITY_MIN = 0.5   # gate 2: non-neutral-field fraction where true beats all controls must STRICTLY exceed this


def robust_scale(w):
    """Spike-robust global scale = 1.4826 * MAD of the median-centered window."""
    c = np.asarray(w, float) - np.median(w, axis=0, keepdims=True)
    return float(1.4826 * np.median(np.abs(c)))


def normalize(w):
    c = np.asarray(w, float) - np.median(w, axis=0, keepdims=True)
    return c / (robust_scale(w) + 1e-12)


def candidate_window(w, kappa=KAPPA, eps=REL_EPS, steps=STEPS):
    s = robust_scale(w)
    if s < FLOOR:  # near-flat / degenerate -> neutral, non-amplifying (predeclared rule)
        return {"neutral": True, "scale": s, "g_k0": 1.0, "g_kpos": 1.0}
    wn = normalize(w)
    return {"neutral": False, "scale": s,
            "g_k0": float(sg.symmetry_gain(wn, 0.0, eps=eps, steps=steps)),
            "g_kpos": float(sg.symmetry_gain(wn, kappa, eps=eps, steps=steps))}


def _median(vals):
    a = np.asarray(vals, float)
    a = a[np.isfinite(a)]
    return float(np.median(a)) if a.size else float("nan")


def run_candidate(fields=SYNTH_FIELDS, n=6, kappa=KAPPA, steps=STEPS, scale_field="white_noise"):
    data = {}
    for field in fields:
        base = [anat.generate_field(field, s) for s in range(n)]
        for ci, control in enumerate(CONTROLS):
            rng = np.random.default_rng(1000 + ci)
            data[(field, control)] = [candidate_window(ctrl.transform_window(w, control, rng), kappa, REL_EPS, steps)
                                      for w in base]
    # amplitude-scale probe (candidate should be ~scale invariant after normalization)
    scale_med = {}
    for mult in (0.1, 1.0, 10.0):
        rows = [candidate_window(mult * anat.generate_field(scale_field, s), kappa) for s in range(n)]
        scale_med[mult] = _median([r["g_kpos"] for r in rows if not r["neutral"]])
    return {"data": data, "scale_med": scale_med, "fields": fields, "n": n}


def _field_median(data, field, control):
    return _median([r["g_kpos"] for r in data[(field, control)] if not r["neutral"]])


def analyze(res):
    data = res["data"]
    non_neutral = [r for rows in data.values() for r in rows if not r["neutral"]]
    neutral_count = sum(1 for rows in data.values() for r in rows if r["neutral"])
    k0_coherent_rate = (float(np.mean([1.0 if r["g_k0"] < _COHERENT else 0.0 for r in non_neutral]))
                        if non_neutral else float("nan"))
    # pooled control medians (kpos over all non-neutral windows for each control)
    ctrl_med = {c: _median([r["g_kpos"] for (f, cc), rows in data.items() if cc == c for r in rows if not r["neutral"]])
                for c in CONTROLS}
    # scale sensitivity: white_noise gain median across amplitude multipliers
    sm = [v for v in res["scale_med"].values() if np.isfinite(v)]
    scale_sensitive = bool(sm and (max(sm) / (min(sm) + 1e-9) > 2.0))
    # spike sensitivity: spike vs lowpass median (true control); the probe must actually be present,
    # otherwise the robustness gate cannot pass vacuously on a custom field set that omits them
    spike_probe_present = ("spike", "true") in data and ("lowpass", "true") in data
    sp = _field_median(data, "spike", "true") if spike_probe_present else float("nan")
    lp = _field_median(data, "lowpass", "true") if spike_probe_present else float("nan")
    spike_probe_present = bool(spike_probe_present and np.isfinite(sp) and np.isfinite(lp))
    spike_sensitive = bool(spike_probe_present and sp > 1.5 * lp)

    # ---- predeclared temporal gates: ALL must pass before temporal_claim_allowed can be True ----
    # gate 1: pooled true median beats every control median by margin
    pooled_beats = {c: (np.isfinite(ctrl_med["true"]) and np.isfinite(ctrl_med[c])
                        and ctrl_med["true"] > ctrl_med[c] * (1.0 + _MARGIN))
                    for c in CONTROLS if c != "true"}
    gate1_pooled = bool(pooled_beats) and all(pooled_beats.values())
    # gate 2: per-field, true beats ALL controls on a predeclared majority of non-neutral fields
    field_votes = {}
    for f in res["fields"]:
        tmed = _field_median(data, f, "true")
        if not np.isfinite(tmed):
            continue  # all-neutral field (e.g. constant): excluded from the vote
        field_votes[f] = all(
            np.isfinite(_field_median(data, f, c)) and tmed > _field_median(data, f, c) * (1.0 + _MARGIN)
            for c in CONTROLS if c != "true")
    field_majority = (sum(field_votes.values()) / len(field_votes)) if field_votes else 0.0
    gate2_field_majority = bool(field_votes) and field_majority > FIELD_MAJORITY_MIN  # strict: exact half fails
    # gate 3: kappa=0 coherence rate meets predeclared threshold
    gate3_k0 = bool(np.isfinite(k0_coherent_rate) and k0_coherent_rate >= K0_COHERENT_MIN)
    # gates 4-6: numerical-hygiene gates must be clean, and the spike/lowpass probe must be available
    gate4_scale = (scale_sensitive is False)
    gate5_probe = spike_probe_present
    gate6_spike = (spike_sensitive is False)

    gates = {"g1_pooled_true_beats_controls": gate1_pooled,
             "g2_field_majority_true_beats_controls": gate2_field_majority,
             "g3_k0_coherent_rate": gate3_k0,
             "g4_scale_invariant": gate4_scale,
             "g5_spike_probe_present": gate5_probe,
             "g6_spike_robust": gate6_spike}
    temporal_claim_allowed = all(gates.values())
    failed = [g for g, ok in gates.items() if not ok]
    reason = "all predeclared temporal gates pass" if temporal_claim_allowed else f"failed gates: {failed}"
    return {
        "k0_coherent_rate": round(k0_coherent_rate, 3) if np.isfinite(k0_coherent_rate) else float("nan"),
        "near_flat_neutral_count": int(neutral_count),
        "scale_sensitive": scale_sensitive,
        "spike_sensitive": spike_sensitive,
        "true_median": round(ctrl_med["true"], 3) if np.isfinite(ctrl_med["true"]) else float("nan"),
        "shuffled_median": round(ctrl_med["time_shuffled"], 3),
        "reversed_median": round(ctrl_med["time_reversed"], 3),
        "circular_median": round(ctrl_med["circular_shift"], 3),
        "field_majority_true_beats_controls": round(field_majority, 3),
        "scale_medians": {k: round(v, 3) for k, v in res["scale_med"].items()},
        "gates": gates,
        "temporal_claim_allowed": temporal_claim_allowed,
        "reason": reason,
    }


def report(res=None):
    if res is None:
        res = run_candidate()
    a = analyze(res)
    lines = ["Normalized-control-gated SAG candidate v1.0 (offline; no integration; does not force a PASS)"]
    lines.append(f"  k0_coherent_rate={a['k0_coherent_rate']}  near_flat_neutral_count={a['near_flat_neutral_count']}")
    lines.append(f"  scale_sensitive={a['scale_sensitive']}  spike_sensitive={a['spike_sensitive']}")
    lines.append(f"  scale medians (white_noise x0.1/x1/x10): {a['scale_medians']}")
    lines.append(f"  temporal medians  true={a['true_median']}  shuffled={a['shuffled_median']}  "
                 f"reversed={a['reversed_median']}  circular={a['circular_median']}")
    lines.append(f"  field_majority(true beats all controls)={a['field_majority_true_beats_controls']}")
    lines.append(f"  temporal gates (ALL required): {a['gates']}")
    lines.append(f"  temporal_claim_allowed={a['temporal_claim_allowed']}  ({a['reason']})")
    lines.append("  raw candidate gains/medians are reported above; no bounded/log score is used and none is hidden.")
    lines.append("  NOTE: offline research candidate; no mechanism/vision/temporal-order claim beyond what controls establish.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
