"""v2.65 tests: tiny synthetic relational target + CHEAP BASELINES ONLY (offline / quarantined).

These tests exercise the preregistered cheap-baseline harness. NO Brainvision-style reading exists
in the module under test, and none is exercised here. They lock: generator determinism and balance;
the fixed split; the preregistered decision-rule bands; the easy-control positive check (including
its ability to flag a broken baseline and an OFF-CHANCE random control, above OR below chance); the
random control sitting at chance on BOTH variants; a target-task random control off chance forcing
UNINFORMATIVE; and the RECORDED RUN VERDICT (UNINFORMATIVE -- B5 misses the easy-control bar), so
that the frozen result cannot drift without a test failing. Offline; no torment_service.
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import tiny_relational_synth_v2_65 as tsr                                   # noqa: E402


def _scores(**override):
    scores = {k: 0.52 for k in tsr.CHEAP_BASELINES}
    scores["B4"] = 0.51
    scores.update(override)
    return scores


def test_generator_is_deterministic_and_balanced():
    c1, y1 = tsr.generate("target")
    c2, y2 = tsr.generate("target")
    assert np.array_equal(c1, c2) and np.array_equal(y1, y2)
    assert c1.shape == (2 * tsr.N_PER_CLASS, tsr.T_FRAMES, tsr.FRAME_H, tsr.FRAME_W)
    assert int((y1 == 1).sum()) == int((y1 == 0).sum()) == tsr.N_PER_CLASS


def test_split_is_fixed_and_disjoint():
    tr, te = tsr.split_indices(2 * tsr.N_PER_CLASS)
    tr2, te2 = tsr.split_indices(2 * tsr.N_PER_CLASS)
    assert np.array_equal(tr, tr2) and np.array_equal(te, te2)
    assert not set(tr.tolist()) & set(te.tolist())
    assert len(tr) + len(te) == 2 * tsr.N_PER_CLASS


def test_balanced_accuracy_edges():
    y = np.array([1, 1, 0, 0])
    assert tsr.balanced_accuracy(y, y) == 1.0
    assert tsr.balanced_accuracy(y, 1 - y) == 0.0
    assert tsr.balanced_accuracy(y, np.array([1, 1, 1, 1])) == 0.5


@pytest.mark.parametrize(
    "override,expected",
    [
        ({"B6": 0.99}, "DEAD"),
        ({"B2": 0.62}, "NO CONCLUSION"),
        ({}, "ELIGIBLE"),
    ],
)
def test_decision_rule_bands(override, expected):
    assert tsr.decision(_scores(**override), control_ok=True)[0] == expected


def test_decision_rule_is_uninformative_without_positive_control():
    assert tsr.decision(_scores(), control_ok=False)[0] == "UNINFORMATIVE"


@pytest.mark.parametrize("b4", [0.80, 0.20])
def test_target_random_control_off_chance_forces_uninformative(b4):
    """B4 must sit AT CHANCE on the target too: below chance is harness-broken exactly as above is."""
    verdict, reason = tsr.decision(_scores(B4=b4), control_ok=True)
    assert verdict == "UNINFORMATIVE"
    assert "HARNESS BROKEN" in reason


def test_positive_control_flags_broken_baseline_and_off_chance_random_control():
    good = {k: 0.95 for k in tsr.CHEAP_BASELINES}
    good["B4"] = 0.51
    assert tsr.positive_control_verdict(good)[0] is True

    weak = dict(good, B5=0.88)
    assert tsr.positive_control_verdict(weak)[0] is False

    for off_chance_b4 in (0.80, 0.20):
        ok, reason = tsr.positive_control_verdict(dict(good, B4=off_chance_b4))
        assert ok is False and "HARNESS BROKEN" in reason


def test_b4_at_chance_band_is_two_sided():
    assert tsr.b4_at_chance({"B4": 0.50}) is True
    assert tsr.b4_at_chance({"B4": tsr.B4_CHANCE_LOW}) is True
    assert tsr.b4_at_chance({"B4": tsr.B4_CHANCE_HIGH}) is True
    assert tsr.b4_at_chance({"B4": tsr.B4_CHANCE_LOW - 0.01}) is False
    assert tsr.b4_at_chance({"B4": tsr.B4_CHANCE_HIGH + 0.01}) is False


def test_random_control_sits_at_chance_on_both_variants():
    for variant in ("target", "easy"):
        scores = tsr.evaluate(variant).scores
        assert tsr.B4_CHANCE_LOW <= scores["B4"] <= tsr.B4_CHANCE_HIGH
        assert tsr.b4_at_chance(scores) is True


def test_frozen_run_reproduces_the_recorded_verdict():
    """Regression lock: B5 misses the easy-control bar, so the recorded run is UNINFORMATIVE."""
    easy = tsr.evaluate("easy").scores
    control_ok, _ = tsr.positive_control_verdict(easy)
    target = tsr.evaluate("target").scores
    verdict, _ = tsr.decision(target, control_ok)
    assert easy["B5"] < tsr.POSITIVE_CONTROL_AT
    assert control_ok is False
    assert verdict == "UNINFORMATIVE"


def test_module_contains_no_brainvision_style_reading():
    with open(tsr.__file__, encoding="utf-8") as fh:
        src = fh.read().lower()
    for forbidden in ("psi_trs", "rpsr", "symmetry_gain", "chroma", "descriptors", "psi_mapping"):
        assert forbidden not in src
