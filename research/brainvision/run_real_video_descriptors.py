"""BV-ΨTRS-RVD runner: evaluate Brainvision methods on real prerecorded descriptor sequences (offline).

Accepts local .npz paths or a manifest. Computes low-level descriptors, runs the existing methods and a
multi-window SAG probe, and prints a compact offline report. Writes only into research/brainvision/
(gitignored). No camera/screen/sensor capture; real media is converted to .npz outside this harness.
stdlib + numpy.

Manifest format (local, gitignored -- real_video_manifest.json):
[
  {"clip_id": "example_clip",
   "npz": "research/brainvision/local_inputs/example_clip.npz",
   "fps": 30,
   "segments": [{"label": "stable", "start": 0, "end": 60},
                {"label": "motion", "start": 60, "end": 120},
                {"label": "cut_or_reset", "start": 120, "end": 150}]}
]
Segment labels are optional; if absent, self-supervised temporal controls run only.
"""
from __future__ import annotations

import json
import os

import numpy as np

import baselines
import descriptors  # noqa: F401  (kept for parity / z-score reuse via real_video)
import metrics
import psi_mapping
import psi_trs
import real_video
import rpsr
import symmetry_gain

_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
LOCAL_INPUTS = os.path.join(_MODULE_DIR, "local_inputs")
_DEFAULT_OUT = os.path.join(_MODULE_DIR, "results", "real_video")


def _extractors():
    return {
        "descriptor_only": baselines.descriptor_only_features,
        "frame_diff": baselines.frame_diff_features,
        "plain_fft": baselines.plain_fft_features,
        "random_mapping": baselines.random_mapping_features,
        "psi": psi_mapping.feature_vector,
        "rpsr": rpsr.feature_vector,
        "psi_trs": lambda D: psi_trs.psi_trs_features(D, kappa=0.5),
        "psi_trs_k0": lambda D: psi_trs.psi_trs_features(D, kappa=0.0),
    }


def evaluate_true_vs_shuffled(windows, seed=0):
    """Self-supervised: can each method separate true temporal order from time-shuffled? chance=0.5."""
    rng = np.random.default_rng(seed)
    out = {}
    for name, fn in _extractors().items():
        Xr = [fn(w) for w in windows]
        Xs = [fn(w[rng.permutation(w.shape[0])]) for w in windows]
        X = np.array(Xr + Xs)
        y = np.array([1] * len(Xr) + [0] * len(Xs))
        out[name] = metrics.loo_nearest_centroid_balanced_accuracy(X, y)
    return out


def _summary(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"mean": float("nan"), "median": float("nan"), "min": float("nan"), "max": float("nan")}
    return {"mean": float(a.mean()), "median": float(np.median(a)),
            "min": float(a.min()), "max": float(a.max())}


def evaluate_sag_real(windows, steps=60, kappa=3.0, margin=0.2):
    """Multi-window SAG: paired-mirror gain over EVERY descriptor window (not just windows[0]).

    A single window can swing the verdict, so we report per-window G(k=0)/G(k>0), summaries, and how many
    windows genuinely amplify (k>0 exceeds a coherent k=0 baseline). Most-windows-amplify => stronger
    recursive-time evidence; one-window => fragility.
    """
    per = []
    for i, w in enumerate(windows):
        g0 = symmetry_gain.symmetry_gain(w, 0.0, steps=steps)
        gk = symmetry_gain.symmetry_gain(w, kappa, steps=steps)
        per.append({"window": i, "G_k0": float(g0), "G_kpos": float(gk),
                    "delta": float(gk - g0), "ratio": float(gk / (g0 + 1e-12))})
    n = len(per)
    n_amp = sum(1 for p in per if np.isfinite(p["G_kpos"]) and p["G_k0"] < 1.1 and p["G_kpos"] > p["G_k0"] + margin)
    g0s = _summary([p["G_k0"] for p in per])
    gks = _summary([p["G_kpos"] for p in per])
    return {
        "n_windows": n,
        "per_window": per,
        "n_amplifying": int(n_amp),
        "frac_amplifying": float(n_amp / n) if n else 0.0,
        "amplifies_any": bool(n_amp >= 1),
        "amplifies_most": bool(n_amp > n / 2.0),
        "G_k0_summary": g0s,
        "G_kpos_summary": gks,
        "G_k0": g0s["mean"],        # backward-compatible single values (means)
        "G_kpos": gks["mean"],
        "amplifies": bool(n_amp > n / 2.0),
    }


def evaluate_segments(windows, labels):
    """Optional segment classification (only if labels present and >=2 classes, >=4 labeled windows)."""
    lab = [(w, l) for w, l in zip(windows, labels or []) if l is not None]
    if len(lab) < 4 or len({l for _, l in lab}) < 2:
        return None
    W = [w for w, _ in lab]
    y = np.array([l for _, l in lab])
    return {name: metrics.loo_nearest_centroid_balanced_accuracy(np.array([fn(w) for w in W]), y)
            for name, fn in _extractors().items()}


def run_clip(frames, win=64, stride=32, segments=None):
    windows, labels = real_video.clip_descriptor_dataset(frames, win, stride, segments)
    out = {"n_windows": len(windows), "descriptor_dim": int(windows[0].shape[1]) if windows else 0}
    if len(windows) >= 4:
        out["true_vs_shuffled"] = evaluate_true_vs_shuffled(windows)
    if windows:
        out["sag"] = evaluate_sag_real(windows)
    seg = evaluate_segments(windows, labels)
    if seg is not None:
        out["segments"] = seg
    return out


def run_npz(path, win=64, stride=32, segments=None):
    frames = real_video.load_frame_stack_npz(path)
    return run_clip(frames, win, stride, segments)


def run_manifest(manifest_path):
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    results = {}
    for clip in manifest:
        npz = clip.get("npz", "")
        cid = clip.get("clip_id", npz)
        if not npz or not os.path.exists(npz):
            results[cid] = {"skipped": "npz not found (local media not committed)"}
            continue
        results[cid] = run_npz(npz, segments=clip.get("segments"))
    return results


def format_report(clip_id, res) -> str:
    lines = [f"BV-ΨTRS-RVD — real prerecorded descriptor test  clip={clip_id}"]
    if "skipped" in res:
        lines.append(f"  skipped: {res['skipped']}")
        return "\n".join(lines)
    lines.append(f"  windows={res['n_windows']}  descriptor_dim={res['descriptor_dim']}")
    if "true_vs_shuffled" in res:
        lines.append("  self-supervised true-order vs time-shuffled (balanced acc, chance 0.5):")
        for n, a in sorted(res["true_vs_shuffled"].items(), key=lambda kv: -kv[1]):
            lines.append(f"    {n:<18s} {a:.3f}")
    if "sag" in res:
        s = res["sag"]
        g0, gk = s["G_k0_summary"], s["G_kpos_summary"]
        lines.append(f"  SAG on real descriptor field ({s['n_windows']} windows, per-window paired-mirror gain):")
        lines.append(f"    G(k=0):  mean={g0['mean']:.3f} median={g0['median']:.3f} min={g0['min']:.3f} max={g0['max']:.3f}")
        lines.append(f"    G(k>0):  mean={gk['mean']:.3f} median={gk['median']:.3f} min={gk['min']:.3f} max={gk['max']:.3f}")
        lines.append(f"    windows amplifying (k>0 > k0+0.2, k0 coherent): {s['n_amplifying']}/{s['n_windows']} "
                     f"(frac {s['frac_amplifying']:.2f})")
        verdict = ("recursive-time SURVIVES (most windows amplify)" if s["amplifies_most"]
                   else "FRAGILE (only some/one window amplifies)" if s["amplifies_any"]
                   else "no amplification on real descriptors")
        lines.append(f"    verdict: {verdict}")
    if "segments" in res:
        lines.append("  segment classification (balanced acc; secondary, do not overclaim):")
        for n, a in sorted(res["segments"].items(), key=lambda kv: -kv[1]):
            lines.append(f"    {n:<18s} {a:.3f}")
    lines.append("  NOTE: offline research artifact only; classification is secondary. Main question:")
    lines.append("        does the recursive-time channel survive real descriptor messiness?")
    return "\n".join(lines)


if __name__ == "__main__":
    man = os.path.join(_MODULE_DIR, "real_video_manifest.json")
    if os.path.exists(man):
        for cid, res in run_manifest(man).items():
            print(format_report(cid, res))
            print()
    else:
        print("No local real_video_manifest.json found. Convert a video to .npz (key 'frames') and add a")
        print(f"manifest; place media under {LOCAL_INPUTS} (gitignored). Nothing to run offline by default.")
