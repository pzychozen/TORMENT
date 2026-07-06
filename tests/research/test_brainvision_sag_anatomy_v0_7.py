"""v0.7 tests: SAG anatomy/characterization harness (offline).

Verify the anatomy harness is offline-only, imports no service/runtime paths, generates deterministic
synthetic fields, produces finite output, does not crash on flat/constant fields, and formats a report.
These tests lock the MACHINERY; the scientific reading ('SAG appears sensitive to variance/richness, not
temporal order') is reported by the harness, not asserted here. Offline; no torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_sag_anatomy as sa  # noqa: E402


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


def test_field_generation_deterministic_and_shape():
    for kind in sa.FIELD_KINDS:
        a = sa.generate_field(kind, 0)
        b = sa.generate_field(kind, 0)
        assert np.array_equal(a, b)
        assert a.shape == (sa.T_DEFAULT, sa.C_DEFAULT)


def test_constant_field_does_not_crash():
    c = sa.generate_field("constant", 0)
    row = sa._row([c, c, c, c])
    assert np.isfinite(row["G_k0"]["median"]) and np.isfinite(row["G_kpos"]["median"])


def test_characterize_finite_output():
    rows = sa.characterize(n=4)
    for v in rows.values():
        for summ in (v["G_k0"], v["G_kpos"]):
            assert all(np.isfinite(x) for x in summ.values())
        assert 0 <= v["n_amplifying"] <= v["n"]


def test_report_formatting_completes():
    s = sa.format_report(sa.characterize(n=4))
    assert "SAG anatomy" in s and "READING" in s
