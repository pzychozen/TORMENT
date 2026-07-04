"""Narrow offline tests for the Brainvision descriptor->psi falsifier.

These tests are self-contained and MUST NOT import torment_service. They confirm the harness is offline,
deterministic, correctly shaped, that temporal/label controls degrade the intended signal, and that the
runner writes only into the research folder.

Note: these tests verify the *machinery and controls*, not that PsiBV beats the baselines. Whether PsiBV
beats the baselines is the research question the runner reports; a negative result is a valid closure.
"""
import ast
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import baselines  # noqa: E402,F401
import descriptors  # noqa: E402
import fixtures  # noqa: E402
import psi_mapping  # noqa: E402
import run_falsifier  # noqa: E402


def test_no_forbidden_imports():
    """Parse each module's AST and assert no import of torment* / rsb_model / RSBModel."""
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
                assert not mod.startswith("torment"), f"{fn}: from {mod} import ..."
                assert "rsb_model" not in mod, f"{fn}: from {mod} import ..."
                for alias in node.names:
                    assert alias.name != "RSBModel", f"{fn}: imports RSBModel"


def test_fixtures_deterministic():
    a = fixtures.generate("recurrence_after_gap", 3)
    b = fixtures.generate("recurrence_after_gap", 3)
    assert np.array_equal(a, b)
    c = fixtures.generate("recurrence_after_gap", 4)
    assert not np.array_equal(a, c)
    assert a.shape == (fixtures.T, 3)


def test_psi_shape_and_scalars():
    prim = fixtures.generate("contrast_pulse", 1)
    desc = descriptors.prepare(prim)
    psi = psi_mapping.compute_psi(desc)
    assert psi.ndim == 4
    assert psi.shape[0] == fixtures.T
    assert psi.shape[1] == descriptors.N_DESCRIPTORS
    assert psi.shape[2] == psi_mapping.M_BANDS
    assert psi.shape[3] == 2  # rising / falling polarity split
    scal = psi_mapping.derive_scalars(psi)
    for key in ("H_bv", "m0_bv", "J_bv", "v_bv"):
        assert key in scal and scal[key].shape[0] == fixtures.T


def test_time_and_label_controls_degrade_signal():
    r = run_falsifier.run(seeds=range(6))
    psi = r["psi"]
    assert psi > r["chance"] + 0.1, f"psi not above chance: {psi} vs chance {r['chance']}"
    assert psi > r["psi_time_shuffled"] + 0.05, (psi, r["psi_time_shuffled"])
    assert psi > r["psi_shuffled_label"] + 0.05, (psi, r["psi_shuffled_label"])


def test_run_writes_only_into_research_folder():
    out = os.path.join(BV_DIR, "results", "_pytest_tmp")
    try:
        r = run_falsifier.main(seeds=range(4), do_write=True, out_dir=out)
        assert "out_dir" in r
        assert os.path.realpath(r["out_dir"]).startswith(BV_DIR), r["out_dir"]
        assert os.path.exists(os.path.join(r["out_dir"], "results.json"))
        assert os.path.exists(os.path.join(r["out_dir"], "results.csv"))
    finally:
        shutil.rmtree(out, ignore_errors=True)
