"""Offline Brainvision descriptor->psi falsifier runner.

Generates deterministic fixtures, extracts PsiBV and baseline features, scores regime separability with a
leave-one-out nearest-centroid balanced accuracy, prints a compact report, and (optionally) writes local
results under research/brainvision/results/.

OFFLINE ONLY. stdlib + numpy. No torment_service imports, no live state, no side effects outside the
results directory. A negative result ("does not beat baselines") is a valid closure.

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

_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
_DEFAULT_OUT = os.path.join(_MODULE_DIR, "results")


def build_dataset(seeds):
    prims, groups, seed_list = [], [], []
    for name, group, seed, arr in fixtures.dataset(seeds):
        prims.append(arr)
        groups.append(group)
        seed_list.append(seed)
    return prims, np.array(groups), seed_list


def _psi_features(prim):
    return psi_mapping.feature_vector(descriptors.prepare(prim))


def _feature_matrix(fn, prims):
    return np.array([fn(p) for p in prims], dtype=float)


def run(seeds=range(8)):
    seeds = list(seeds)
    prims, y, seed_list = build_dataset(seeds)

    methods = {
        "psi": _feature_matrix(_psi_features, prims),
        "psi_time_shuffled": np.array(
            [_psi_features(baselines.time_shuffle(p, s)) for p, s in zip(prims, seed_list)], dtype=float
        ),
        "frame_diff": _feature_matrix(baselines.frame_diff_features, prims),
        "descriptor_only": _feature_matrix(baselines.descriptor_only_features, prims),
        "plain_fft": _feature_matrix(baselines.plain_fft_features, prims),
        "random_mapping": _feature_matrix(baselines.random_mapping_features, prims),
    }

    accuracies = {
        name: metrics.loo_nearest_centroid_balanced_accuracy(X, y) for name, X in methods.items()
    }

    # shuffled-label control: PsiBV features but with permuted labels -> chance floor.
    rng = np.random.default_rng(2024)
    y_shuffled = y.copy()
    rng.shuffle(y_shuffled)
    accuracies["psi_shuffled_label"] = metrics.loo_nearest_centroid_balanced_accuracy(
        methods["psi"], y_shuffled
    )

    results = {
        "accuracies": {k: float(v) for k, v in accuracies.items()},
        "chance": float(metrics.chance_level(y)),
        "n_fixtures": int(len(prims)),
        "classes": sorted(set(y.tolist())),
        "seeds": seeds,
        "psi_feature_dim": int(methods["psi"].shape[1]),
    }
    results.update({k: float(v) for k, v in accuracies.items()})
    return results


def format_report(results) -> str:
    lines = []
    lines.append("Brainvision descriptor->psi falsifier — offline report")
    lines.append(f"  fixtures: {results['n_fixtures']}  classes: {results['classes']}  "
                 f"chance: {results['chance']:.3f}")
    lines.append(f"  psi feature dim: {results['psi_feature_dim']}")
    lines.append("  balanced accuracy (leave-one-out nearest centroid):")
    for name, acc in sorted(results["accuracies"].items(), key=lambda kv: -kv[1]):
        lines.append(f"    {name:<20s} {acc:.3f}")
    psi = results["accuracies"]["psi"]
    fd = results["accuracies"]["frame_diff"]
    fft = results["accuracies"]["plain_fft"]
    verdict = "psi ABOVE frame-diff & plain-fft" if (psi > fd and psi > fft) else \
              "psi does NOT beat both baselines (valid closure)"
    lines.append(f"  verdict: {verdict}")
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


def main(seeds=range(8), do_write=False, out_dir=None):
    results = run(seeds)
    print(format_report(results))
    if do_write:
        results["out_dir"] = write_results(results, out_dir)
        print(f"  wrote: {results['out_dir']}")
    return results


if __name__ == "__main__":
    main(seeds=range(8), do_write=True)
