"""Offline Brainvision falsifier runner.

Modes: v0.1 coarse, v0.2 marginal-matched, v0.3 spectrum-matched (RPSR), v0.4 psi_time_recursive (ΨTRS).
Generates deterministic fixtures, extracts PsiBV / PsiBV-RPSR / BV-ΨTRS and baseline features, scores
regime separability with a leave-one-out nearest-centroid balanced accuracy, prints a compact report, and
optionally writes local results. OFFLINE ONLY. stdlib + numpy. No torment_service imports. A negative
result ("does not beat baselines") is a valid closure.

Run:  python research/brainvision/run_falsifier.py
"""
from __future__ import annotations

import csv
import json
import os

import numpy as np

import baselines
import descriptors
import fixtures
import metrics
import psi_mapping
import psi_trs
import rpsr

_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
_DEFAULT_OUT = os.path.join(_MODULE_DIR, "results")

MODES = (
    ("coarse", "v0.1_coarse"),
    ("marginal_matched", "v0.2_marginal_matched"),
    ("spectrum_matched", "v0.3_spectrum_matched"),
    ("psi_time_recursive", "v0.4_psi_time_recursive"),
)


def build_dataset(seeds, mode="coarse"):
    prims, groups, seed_list = [], [], []
    for name, group, seed, arr in fixtures.dataset(seeds, mode=mode):
        prims.append(arr)
        groups.append(group)
        seed_list.append(seed)
    return prims, np.array(groups), seed_list


def _psi(prim):
    return psi_mapping.feature_vector(descriptors.prepare(prim))


def _rpsr(prim):
    return rpsr.feature_vector(descriptors.prepare(prim))


def _trs(prim, kappa):
    return psi_trs.psi_trs_features(descriptors.prepare(prim), kappa=kappa)


def _matrix(fn, prims):
    return np.array([fn(p) for p in prims], dtype=float)


def run(seeds=range(8), mode="coarse"):
    seeds = list(seeds)
    prims, y, seed_list = build_dataset(seeds, mode=mode)
    methods = {
        "psi": _matrix(_psi, prims),
        "psi_time_shuffled": np.array([_psi(baselines.time_shuffle(p, s)) for p, s in zip(prims, seed_list)]),
        "rpsr": _matrix(_rpsr, prims),
        "rpsr_time_shuffled": np.array([_rpsr(baselines.time_shuffle(p, s)) for p, s in zip(prims, seed_list)]),
        "frame_diff": _matrix(baselines.frame_diff_features, prims),
        "descriptor_only": _matrix(baselines.descriptor_only_features, prims),
        "plain_fft": _matrix(baselines.plain_fft_features, prims),
        "random_mapping": _matrix(baselines.random_mapping_features, prims),
    }
    if mode == "psi_time_recursive":
        methods["psi_trs"] = _matrix(lambda p: _trs(p, 0.5), prims)         # state-dependent internal time
        methods["psi_trs_k0"] = _matrix(lambda p: _trs(p, 0.0), prims)      # ablation: no recursive time
        methods["psi_trs_time_shuffled"] = np.array(
            [psi_trs.psi_trs_features(descriptors.prepare(baselines.time_shuffle(p, s)), kappa=0.5)
             for p, s in zip(prims, seed_list)])

    accuracies = {name: metrics.loo_nearest_centroid_balanced_accuracy(X, y) for name, X in methods.items()}
    rng = np.random.default_rng(2024)
    y_shuffled = y.copy()
    rng.shuffle(y_shuffled)
    accuracies["psi_shuffled_label"] = metrics.loo_nearest_centroid_balanced_accuracy(methods["psi"], y_shuffled)

    results = {
        "mode": mode,
        "accuracies": {k: float(v) for k, v in accuracies.items()},
        "chance": float(metrics.chance_level(y)),
        "n_fixtures": int(len(prims)),
        "classes": sorted(set(y.tolist())),
        "seeds": seeds,
    }
    results.update({k: float(v) for k, v in accuracies.items()})
    return results


def format_report(results) -> str:
    a = results["accuracies"]
    lines = [f"Brainvision falsifier — mode={results['mode']}"]
    lines.append(f"  fixtures: {results['n_fixtures']}  classes: {results['classes']}  chance: {results['chance']:.3f}")
    lines.append("  balanced accuracy (leave-one-out nearest centroid):")
    for name, acc in sorted(a.items(), key=lambda kv: -kv[1]):
        lines.append(f"    {name:<22s} {acc:.3f}")
    lines.append(f"  amplitude-shortcut(descriptor_only)={a['descriptor_only']:.3f}  "
                 f"power-spectrum-shortcut(plain_fft)={a['plain_fft']:.3f}")
    if "psi_trs" in a:
        gain = "ADDS signal" if a["psi_trs"] > a["psi_trs_k0"] else "no gain"
        lines.append(f"  RECURSIVE-TIME CHANNEL: psi_trs(k>0)={a['psi_trs']:.3f} vs "
                     f"psi_trs_k0(ablation)={a['psi_trs_k0']:.3f}  ({gain})")
    lines.append("  NOTE: offline research artifact only; authorizes no runtime/memory/action contact.")
    return "\n".join(lines)


def write_results(results, out_dir=None) -> str:
    out_dir = os.path.realpath(out_dir or _DEFAULT_OUT)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, sort_keys=True)
    with open(os.path.join(out_dir, "results.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["method", "balanced_accuracy"])
        for name, acc in sorted(results["accuracies"].items()):
            w.writerow([name, f"{acc:.6f}"])
    return out_dir


def main(seeds=range(8), do_write=False, out_dir=None, mode="coarse"):
    results = run(seeds, mode=mode)
    print(format_report(results))
    if do_write:
        results["out_dir"] = write_results(results, out_dir)
        print(f"  wrote: {results['out_dir']}")
    return results


def report_all(seeds=range(8), do_write=False, out_dir=None):
    all_results = {}
    for mode, label in MODES:
        res = run(seeds, mode=mode)
        print(format_report(res))
        print()
        if do_write:
            res["out_dir"] = write_results(res, os.path.join(out_dir or _DEFAULT_OUT, label))
        all_results[label] = res
    return all_results


if __name__ == "__main__":
    report_all(seeds=range(8), do_write=True)
