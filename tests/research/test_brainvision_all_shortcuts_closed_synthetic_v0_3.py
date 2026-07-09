"""v0.3 tests: all-shortcuts-closed synthetic falsifier (form A, NON-LEARNING; offline).

Lock the v0.3 slice: it applies the SAME fixed frozen color rule (PSC/AIC floors; no label fit) to a larger-N
synthetic family that attempts to close all cheap-proxy shortcut groups simultaneously, and it AUDITS closure
honestly. Tests assert ROBUST facts only: reuse-by-identity (no redefinition of frozen surfaces); non-learning
(no trained weights, no label-fitted color threshold, S_best_threshold labelled optimistic/diagnostic); the
shortcut audit covers all five groups and honestly reports open residual shortcuts / infeasibility; the frozen
verdict stays HOLD and claim locks stay False; recurrence/temporal features are excluded; a shuffled-label
control is near chance; and no vision/validity/temporal/memory/runtime/integration claim is emitted. Offline;
no torment_service. NOT platform-marginal numeric values.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs                              # noqa: E402
import run_all_shortcuts_closed_synthetic_v0_3 as m                # noqa: E402

SRC = os.path.join(BV_DIR, "run_all_shortcuts_closed_synthetic_v0_3.py")


def test_imports_only_quarantined_research_surfaces():
    with open(SRC, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods.append(node.module or "")
    for mod in mods:
        assert not mod.startswith("torment") and "service" not in mod, mod
    assert set(mods) <= {"numpy", "__future__", "run_color_structure_v0_8",
                         "run_color_structure_spectral_std_blocker_v1_9", "run_color_structure_by_std_residual_v2_0"}


def test_reuses_frozen_descriptors_by_identity_no_redefine():
    assert m.structure_score is cs.structure_score
    assert m.stats is cs._stats
    assert m.PSC_FLOOR == cs.PSC_FLOOR == 0.30
    assert m.AIC_FLOOR == cs.AIC_FLOOR == 0.30
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "def structure_score" not in src and "def _stats" not in src


def test_non_learning_fixed_rule_no_trained_weights():
    r = m.run()
    assert r["learning"] is False and r["model_form"] == "A_non_learning_scoring"
    assert r["fixed_rule"].startswith("structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR")
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    for banned in (".fit(", "sklearn", "torch", "tensorflow", "backward(", "optimizer", "train("):
        assert banned not in src, banned
    # S_best_threshold must be labelled optimistic/diagnostic, NOT the fixed model
    assert "S_best_threshold_ba_OPTIMISTIC_DIAGNOSTIC_ONLY" in r["ablations"]
    import json
    assert json.dumps(m.run(), sort_keys=True, default=str) == json.dumps(r, sort_keys=True, default=str)


def test_shortcut_audit_covers_all_groups_and_reports_open_residuals():
    r = m.run()
    for g in ("movement_channel_energy", "directional", "spectral", "per_channel", "frame_diff"):
        assert g in r["shortcut_audit"]
        d = r["shortcut_audit"][g]
        assert set(d) >= {"class_centroid_abs_delta", "cheap_baseline_separates_BA", "closed"}
    # open residuals reported honestly; consistent with the all_shortcuts_closed / feasibility flags
    assert isinstance(r["open_residual_shortcut_groups"], list)
    assert r["all_shortcuts_closed"] == (len(r["open_residual_shortcut_groups"]) == 0)
    assert r["all_shortcuts_closed_construction_feasible"] == r["all_shortcuts_closed"]


def test_outcome_is_one_of_predeclared_and_consistent():
    r = m.run()
    assert r["outcome"].startswith(("Outcome_1", "Outcome_2", "Outcome_3", "Outcome_4", "unresolved"))
    # if any residual shortcut is open, the outcome cannot be the "all closed / cheap fails" success
    if r["open_residual_shortcut_groups"]:
        assert not r["outcome"].startswith("Outcome_1")


def test_baselines_ablations_controls_present():
    r = m.run()
    for g in ("movement_channel_energy", "directional", "spectral", "per_channel", "frame_diff", "random"):
        assert g in r["baselines_separability_BA"]
    assert set(r["ablations"]) >= {"PSC_only_frozen_ba", "AIC_only_frozen_ba",
                                   "S_best_threshold_ba_OPTIMISTIC_DIAGNOSTIC_ONLY"}
    assert set(r["color_structure_confusion"]) == {"tp", "fn", "fp", "tn"}
    assert "shuffled_label_control_ba" in r


def test_shuffled_label_control_near_chance():
    r = m.run()
    assert 0.4 <= r["shuffled_label_control_ba"] <= 0.6


def test_recurrence_temporal_excluded():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    for banned in ("import run_sag", "recurrence_quant", "rqa(", "_det(", "_lam("):
        assert banned not in src, banned


def test_frozen_verdict_hold_and_claim_locks_false():
    r = m.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False
    assert r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False
    assert r["integration_readiness_claim"] is False


def test_positive_result_cannot_move_verdict_or_locks():
    r = m.run()
    assert r["reporting_only"] is True
    if r["color_structure_model_ba"] >= 0.9:
        assert r["frozen_brainvision_verdict"] == "HOLD"
        assert r["first_pass_structure_validity_claim_allowed"] is False
    sig = r["research_signal"].lower()
    assert "vision" not in sig or "no_vision" in sig


def test_no_vision_temporal_or_memory_claim_in_source():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    assert "not proven vision" in src
    assert "no memory-system" in src or "memory-system integration" in src
    assert "temporal" in src
