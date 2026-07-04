"""v0.4.2 tests: BV-ΨTRS-GP golden-point calibration.

Old raw-kernel golden points are exploratory regime anchors, NOT universal constants and NOT a claim of
transfer. These tests lock the loader, labels, and the two behavioral anchors we can require: a sane
mapping keeps stable_core coherent, and expected_fail is a fail-control (never success evidence).
Offline only; no torment_service.
"""
import ast
import json
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import bv_golden as gp  # noqa: E402


def test_no_forbidden_imports():
    for fn in os.listdir(BV_DIR):
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(BV_DIR, fn), encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=fn)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("torment"), f"{fn}: import {alias.name}"
                    assert "rsb_model" not in alias.name, f"{fn}: import {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("torment"), f"{fn}: from {mod}"
                assert "rsb_model" not in mod, f"{fn}: from {mod}"
                for alias in node.names:
                    assert alias.name != "RSBModel", f"{fn}: imports RSBModel"


def test_golden_table_loads_deterministically():
    a = gp.load_golden()
    b = gp.load_golden()
    assert a == b
    assert a["points"]
    assert all(all(k in p for k in ("label", "eps", "g", "k3_scale", "dt")) for p in a["points"])


def test_labels_present():
    labels = {p["label"] for p in gp.load_golden()["points"]}
    assert {"stable_core", "near_knee", "edge_band", "expected_fail"} <= labels


def test_optional_local_json_loader():
    pt = {"eps_star": 0.3, "points": [{"label": "stable_core", "eps": 1e-3, "g": 0.4, "k3_scale": 0.1, "dt": 0.03}]}
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "g.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(pt, fh)
        loaded = gp.load_golden(path)
        assert loaded["eps_star"] == 0.3 and loaded["points"][0]["label"] == "stable_core"


def test_stable_core_coherent():
    cal = gp.calibrate()
    row = next(r for r in cal["rows"] if r["label"] == "stable_core")
    assert np.isfinite(row["gain"])
    assert row["gain"] < cal["G0"] + 0.1
    assert row["class"] == "coherent"


def test_expected_fail_is_fail_control():
    cal = gp.calibrate()
    row = next(r for r in cal["rows"] if r["label"] == "expected_fail")
    assert row["class"] == "fail-control"  # never counted as success evidence


def test_report_completes_offline():
    s = gp.report()
    assert "golden-point calibration" in s and "expected_fail" in s
