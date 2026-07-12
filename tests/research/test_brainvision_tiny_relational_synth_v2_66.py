"""v2.66 tests: repaired-control tiny synthetic target + CHEAP BASELINES ONLY (offline / quarantined).

NO Brainvision-style reading exists in the module under test, and none is exercised here.

These tests lock: generator determinism and balance; that the repaired control keeps the two elements
DISTINCT (v2.66 R1); that the relation is neither lockstep nor swap-invariant (R2); the two-sided
random-control chance band on BOTH variants; the preregistered decision-rule bands; that a failed
positive control forces UNINFORMATIVE even when a cheap baseline separates the target; and the
RECORDED RUN VERDICT (UNINFORMATIVE -- B5 misses the bar again, while the repaired B6 clears the
control and separates the target above the DEAD bar). Offline; no torment_service.
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import tiny_relational_synth_v2_66 as tsr                                   # noqa: E402


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


def test_repaired_control_keeps_the_two_elements_distinct():
    """v2.66 R1: the control may not collapse the two elements into one effective object."""
    rng = np.random.default_rng(tsr.SEED_DATA_EASY)
    for related in (True, False):
        for _ in range(tsr.EASY_MAX_TRIES):
            A, B = tsr._tracks(rng, related, tsr.EASY_SPEED_CLASS_TWO, tsr.PHI_RELATION)
            if tsr._min_sep(A, B) >= tsr.EASY_MIN_SEPARATION:
                break
        else:
            pytest.fail("rejection sampling could not keep the two elements distinct")


def test_relation_is_neither_lockstep_nor_swap_invariant():
    """v2.66 R2: a relation that reads the same after swapping the elements tests nothing."""
    assert tsr.PHI_RELATION not in (0.0, np.pi)


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


def test_failed_positive_control_forces_uninformative_even_with_a_solved_target():
    """The control gate precedes interpretation: no verdict may be read out of a broken harness."""
    assert tsr.decision(_scores(B6=0.99), control_ok=False)[0] == "UNINFORMATIVE"


@pytest.mark.parametrize("b4", [0.20, 0.80])
def test_target_random_control_off_chance_forces_uninformative(b4):
    verdict, reason = tsr.decision(_scores(B4=b4), control_ok=True)
    assert verdict == "UNINFORMATIVE"
    assert "HARNESS BROKEN" in reason


def test_positive_control_flags_broken_baseline_and_off_chance_random_control():
    good = {k: 0.95 for k in tsr.CHEAP_BASELINES}
    good["B4"] = 0.51
    assert tsr.positive_control_verdict(good)[0] is True
    assert tsr.positive_control_verdict(dict(good, B5=0.88))[0] is False
    for off_chance in (0.20, 0.80):
        ok, reason = tsr.positive_control_verdict(dict(good, B4=off_chance))
        assert ok is False and "HARNESS BROKEN" in reason


def test_random_control_sits_at_chance_on_both_variants():
    for variant in ("target", "easy"):
        assert tsr.b4_at_chance(tsr.evaluate(variant).scores) is True


def test_frozen_run_reproduces_the_recorded_verdict():
    """Recorded run: B5 misses the bar again; repaired B6 clears the control and separates the target."""
    easy = tsr.evaluate("easy").scores
    control_ok, _ = tsr.positive_control_verdict(easy)
    target = tsr.evaluate("target").scores
    verdict, _ = tsr.decision(target, control_ok)
    assert easy["B5"] < tsr.POSITIVE_CONTROL_AT
    assert easy["B6"] >= tsr.POSITIVE_CONTROL_AT
    assert target["B6"] >= tsr.DEAD_AT
    assert control_ok is False
    assert verdict == "UNINFORMATIVE"


def test_module_contains_no_brainvision_style_reading():
    with open(tsr.__file__, encoding="utf-8") as fh:
        src = fh.read().lower()
    for forbidden in ("psi_trs", "rpsr", "symmetry_gain", "chroma", "psi_mapping"):
        assert forbidden not in src
