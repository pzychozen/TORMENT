"""BV-ΨTRS-RVD-CONTROLS: offline controls/fragility wrapper for real-video SAG (v0.4 controls pass).

Runs the EXISTING multi-window SAG (from run_real_video_descriptors) on each descriptor window and on
temporal/null controls of that window, to test whether kappa>0 amplification is specific to true temporal
order or survives shuffling/reversal/shifting. If shuffled/reversed windows amplify like true windows, the
recursive-time survival claim weakens. No new operators, no theory, no tuning. stdlib + numpy; no service
imports; no runtime/camera/sensor/prompt/context/memory/action/render-body/autonomy contact.
"""
from __future__ import annotations

import json
import os

import numpy as np

import real_video
import run_real_video_descriptors as rvd

_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
LOCAL_INPUTS = rvd.LOCAL_INPUTS

CONTROLS = ("true", "time_shuffled", "time_reversed", "circular_shift", "channel_shuffle", "descriptor_dropout")


def transform_window(window, control, rng):
    """Deterministic per-window transform. 'true' is identity; the rest are temporal/null controls."""
    w = np.asarray(window, float)
    T, C = w.shape
    if control == "true":
        return w
    if control == "time_shuffled":                    # destroys temporal order (keeps marginal)
        return w[rng.permutation(T)]
    if control == "time_reversed":                    # preserves |FFT| + marginal, flips direction
        return w[::-1].copy()
    if control == "circular_shift":                   # preserves |FFT| + marginal, shifts phase origin
        return np.roll(w, T // 3 + int(rng.integers(0, 5)), axis=0)
    if control == "channel_shuffle":                  # permutes descriptor channels
        return w[:, rng.permutation(C)]
    if control == "descriptor_dropout":               # nulls one descriptor channel
        w = w.copy()
        w[:, int(rng.integers(0, C))] = 0.0
        return w
    raise ValueError(f"unknown control: {control!r}")


def _pack(sag):
    return {"n_windows": sag["n_windows"], "G_k0": sag["G_k0_summary"], "G_kpos": sag["G_kpos_summary"],
            "n_amplifying": sag["n_amplifying"], "frac_amplifying": sag["frac_amplifying"],
            "kpos_median": sag["G_kpos_summary"]["median"]}


def run_controls_for_windows(windows, seed=0):
    out = {}
    for ci, control in enumerate(CONTROLS):
        rng = np.random.default_rng(seed * 100 + ci)
        transformed = [transform_window(w, control, rng) for w in windows]
        out[control] = _pack(rvd.evaluate_sag_real(transformed))
    t = out["true"]
    out["_comparison"] = {
        "true_median": t["kpos_median"],
        "shuffled_median": out["time_shuffled"]["kpos_median"],
        "reversed_median": out["time_reversed"]["kpos_median"],
        "true_amplifying": t["n_amplifying"],
        "shuffled_amplifying": out["time_shuffled"]["n_amplifying"],
        "reversed_amplifying": out["time_reversed"]["n_amplifying"],
        "true_gt_shuffled_median": bool(t["kpos_median"] > out["time_shuffled"]["kpos_median"]),
        "true_gt_reversed_median": bool(t["kpos_median"] > out["time_reversed"]["kpos_median"]),
    }
    return out


def run_controls_for_clip(frames, win=64, stride=32, seed=0):
    windows, _ = real_video.clip_descriptor_dataset(frames, win, stride)
    if not windows:
        return {"n_windows": 0}
    return run_controls_for_windows(windows, seed=seed)


def run_npz(path, win=64, stride=32, seed=0):
    return run_controls_for_clip(real_video.load_frame_stack_npz(path), win, stride, seed)


def run_manifest(manifest_path):
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    results = {}
    for clip in manifest:
        npz = clip.get("npz", "")
        cid = clip.get("clip_id", npz)
        results[cid] = ({"skipped": "npz not found (local media not committed)"}
                        if not npz or not os.path.exists(npz) else run_npz(npz))
    return results


def format_report(clip_id, res) -> str:
    lines = [f"BV-ΨTRS-RVD-CONTROLS — clip={clip_id}"]
    if "skipped" in res:
        lines.append(f"  skipped: {res['skipped']}")
        return "\n".join(lines)
    if res.get("n_windows") == 0:
        lines.append("  no windows (clip too short)")
        return "\n".join(lines)
    lines.append(f"  {'control':<18}{'G(k=0) med':>12}{'G(k>0) med':>12}{'G(k>0) mean':>12}{'amp':>8}")
    for control in CONTROLS:
        r = res[control]
        lines.append(f"  {control:<18}{r['G_k0']['median']:>12.3f}{r['G_kpos']['median']:>12.3f}"
                     f"{r['G_kpos']['mean']:>12.3f}{r['n_amplifying']:>5}/{r['n_windows']}")
    c = res["_comparison"]
    lines.append(f"  compare: true_med={c['true_median']:.3f}  shuffled_med={c['shuffled_median']:.3f}  "
                 f"reversed_med={c['reversed_median']:.3f}")
    lines.append(f"           amplifying true={c['true_amplifying']}  shuffled={c['shuffled_amplifying']}  "
                 f"reversed={c['reversed_amplifying']}")
    both = c["true_gt_shuffled_median"] and c["true_gt_reversed_median"]
    verdict = ("true amplifies MORE than shuffled & reversed (true exceeds shuffled & reversed under this control -> temporal-order specificity not falsified by these controls)"
               if both else
               "shuffled/reversed amplify like (or more than) true -> amplification NOT temporal-order-specific "
               "-> temporal-order interpretation WEAKENS; numeric SAG amplification remains")
    lines.append(f"  verdict: {verdict}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    man = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_MODULE_DIR, "real_video_manifest.json")
    if os.path.exists(man):
        for cid, res in run_manifest(man).items():
            print(format_report(cid, res))
            print()
    else:
        print(f"No manifest at {man}. Place local .npz under {LOCAL_INPUTS} (gitignored) and add a manifest.")
