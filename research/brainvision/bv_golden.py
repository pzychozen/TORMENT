"""BV-ΨTRS-GP: Golden-Point Calibration (offline, exploratory).

Old raw-kernel golden points (v4.0/golden) are NOT universal constants and do NOT directly transfer to
Brainvision. They are used here only as old-kernel regime anchors / scan priors (stable_core, edge_band,
near_knee, expected_fail) to see whether their ordering aligns with the BV-ΨTRS-SAG recursive-time
amplification structure. A misalignment is a valid negative.

Mapping note: the SAG probe is pure-clock, so the recursive-time knob is kappa (mapped from k3_scale).
g is a geometry-feedback prior that is recorded but NOT exercised by this pure-clock probe. The alignment
is exploratory and fragile: mapping g -> warp-sharpness instead collapses the non-fail regimes to
coherent. Only the failure extreme (expected_fail) amplifies/fails robustly. stdlib + numpy; no service
imports.
"""
from __future__ import annotations

import json
import os

import numpy as np

import symmetry_gain as sg

# Bundled anchors extracted once from v4.0/golden/golden_points.json (one param set per regime).
_GOLDEN_BUNDLED = {
    "eps_star": 0.2447,
    "points": [
        {"label": "stable_core", "eps": 0.0005000605482966, "g": 0.4036285061499943,
         "k3_scale": 0.1084591949599039, "dt": 0.03, "has_nan": 0},
        {"label": "near_knee", "eps": 0.2442664965468864, "g": 0.1855441172896098,
         "k3_scale": 0.928375781050064, "dt": 0.03, "has_nan": 0},
        {"label": "edge_band", "eps": 0.1712112326839077, "g": 0.2558850953310614,
         "k3_scale": 7.032141146785419, "dt": 0.03, "has_nan": 0},
        {"label": "expected_fail", "eps": 0.3679188826793566, "g": 19.76339816581597,
         "k3_scale": 7.540247471119014, "dt": 0.03, "has_nan": 1},
    ],
}


def load_golden(path=None):
    """Return {eps_star, points:[...]}. Optionally read a local JSON path if present; else bundled table."""
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "points" in data:
            return {"eps_star": data.get("eps_star", _GOLDEN_BUNDLED["eps_star"]), "points": data["points"]}
        return {"eps_star": _GOLDEN_BUNDLED["eps_star"], "points": data}
    return _GOLDEN_BUNDLED


def golden_to_bv_priors(pt):
    """Cautious field mapping (exploratory, not a claim of transfer)."""
    return {
        "dt": float(pt["dt"]),           # dt -> Brainvision dt (common-mode in SAG)
        "eps": float(pt["eps"]),         # eps -> perturbation / coupling prior
        "g": float(pt["g"]),             # g -> Ψ geometry-feedback prior (recorded; not exercised by SAG)
        "kappa": float(pt["k3_scale"]),  # k3_scale -> recursive-time kappa prior
    }


def _classify(label, has_nan, G, G0):
    if label == "expected_fail" or has_nan or not np.isfinite(G):
        return "fail-control"
    if G < G0 + 0.1:
        return "coherent"
    if G < G0 + 1.0:
        return "near-transition"
    return "amplifying"


def calibrate(base_seed=0, steps=60, golden_path=None):
    golden = load_golden(golden_path)
    b = sg.base_field(base_seed)
    G0 = sg.symmetry_gain(b, 0.0, steps=steps)
    rows, seen = [], set()
    for pt in golden["points"]:
        if pt["label"] in seen:
            continue
        seen.add(pt["label"])
        pr = golden_to_bv_priors(pt)
        try:
            eps = float(np.clip(pr["eps"], 1e-4, 0.3))
            # kappa (=k3_scale) is the recursive-time knob; warp sharpness uses the harness default.
            # g (geometry feedback) is recorded but NOT exercised by the pure-clock SAG probe.
            G = sg.symmetry_gain(b, pr["kappa"], eps=eps, steps=steps)
            if not np.isfinite(G):
                G = float("nan")
        except Exception:
            G = float("nan")
        rows.append({"label": pt["label"], "eps": pr["eps"], "g": pr["g"], "k3_scale": pr["kappa"],
                     "kappa": pr["kappa"], "gain": float(G),
                     "class": _classify(pt["label"], pt.get("has_nan", 0), G, G0)})
    return {"G0": float(G0), "eps_star": golden["eps_star"], "rows": rows}


def report(golden_path=None):
    cal = calibrate(golden_path=golden_path)
    lines = ["BV-ΨTRS-GP — golden-point calibration (OLD-KERNEL anchors; exploratory, NOT universal constants)"]
    lines.append(f"  reference kappa=0 gain G0={cal['G0']:.3f}   eps_star={cal['eps_star']}")
    lines.append(f"  {'label':<14}{'eps':>9}{'g':>9}{'k3_scale':>10}  ->  {'kappa':>7}{'SAG_gain':>10}   interpretation")
    for r in cal["rows"]:
        gv = "nan" if not np.isfinite(r["gain"]) else f"{r['gain']:.3f}"
        lines.append(f"  {r['label']:<14}{r['eps']:>9.4f}{r['g']:>9.3f}{r['k3_scale']:>10.3f}  ->  "
                     f"{r['kappa']:>7.3f}{gv:>10}   {r['class']}")
    lines.append("  NOTE: exploratory + fragile (g->warp-sharpness mapping collapses non-fail regimes to")
    lines.append("        coherent). Old-kernel golden points do NOT directly transfer to Brainvision.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
