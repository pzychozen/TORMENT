"""v0.2 tests: offline prototype scoring probe (form A, NON-LEARNING; offline).

Lock the v0.2 slice: a deterministic NON-LEARNING scoring probe (form A) over synthetic fixtures, reusing the
frozen v0.7/v0.8 descriptors by identity and the v1.9/v2.0 generators. Tests assert ROBUST facts only: the model
does not learn from labels (fixed frozen-floor rule; source contains no fit/train call); it is deterministic;
recurrence/temporal features are excluded; cheap baselines + ablations + cross-family generalization + a
shuffled-label control are present; the frozen Brainvision verdict stays HOLD and is untouched; the claim locks
stay False; and no vision / descriptor-validity / temporal / memory / runtime claim is emitted. Offline; no
torment_service. NOT platform-marginal numeric values.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs                          # noqa: E402
import run_offline_prototype_model_v0_2 as m                   # noqa: E402

SRC = os.path.join(BV_DIR, "run_offline_prototype_model_v0_2.py")


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


def test_model_is_non_learning_and_deterministic():
    r = m.run()
    assert r["learning"] is False
    assert r["model_form"] == "A_non_learning_scoring"
    # no label-fitting / training constructs in the source
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    for banned in (".fit(", "sklearn", "torch", "tensorflow", "backward(", "optimizer", "train("):
        assert banned not in src, banned
    # deterministic
    import json
    assert json.dumps(m.run(), sort_keys=True, default=str) == json.dumps(r, sort_keys=True, default=str)


def test_recurrence_temporal_features_excluded():
    r = m.run()
    # exclusion is declared, and recurrence/temporal features do not appear among the declared feature families
    assert r["feature_families"]["recurrence_temporal_excluded"] is True
    declared = (r["feature_families"]["color_structure"] + r["feature_families"]["directional"]
                + r["feature_families"]["per_channel_spectral"])
    for tok in ("DET", "RR", "LAM", "recurrence"):
        assert not any(tok.lower() in f.lower() for f in declared), tok
    # and no recurrence/RQA module is imported or called (the import whitelist test already bounds imports)
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    for banned in ("import run_sag", "recurrence_quant", "rqa(", "_det(", "_lam("):
        assert banned not in src, banned


def test_baselines_ablations_and_controls_present():
    r = m.run()
    for fam, d in r["per_family"].items():
        for g in ("movement_only", "direction_only", "spectral_only", "per_channel_only", "frame_diff_proxy",
                  "random"):
            assert g in d["baselines"]
        assert set(d["ablations"]) >= {"PSC_only_frozen_ba", "AIC_only_frozen_ba", "S_best_threshold_ba"}
        assert set(d["color_structure_confusion"]) == {"tp", "fn", "fp", "tn"}
    assert "cross_family_generalization" in r and "cross_family_summary" in r
    assert "shuffled_label_control_ba" in r


def test_shuffled_label_control_is_near_chance():
    # sanity: the fixed rule has no signal on shuffled labels (averaged over many shuffles ~ 0.5)
    r = m.run()
    assert 0.4 <= r["shuffled_label_control_ba"] <= 0.6


def test_frozen_verdict_hold_and_claim_locks_false():
    r = m.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False
    assert r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False


def test_positive_result_is_framed_research_only_not_validity():
    # a strong balanced accuracy must NOT flip any claim lock or the verdict
    r = m.run()
    assert r["pooled"]["color_structure_model_ba"] >= 0.9   # robust: the frozen rule separates these fixtures
    assert r["reporting_only"] is True
    # research_signal is a research token, never a vision/validity/verdict token
    sig = r["research_signal"].lower()
    assert "hold" not in sig or "verdict" not in sig
    assert "vision" not in sig or "no_vision" in sig
    assert r["frozen_brainvision_verdict"] == "HOLD"


def test_baseline_doctrine_reported_no_single_cheap_generalizes_but_families_separable():
    # the honest cross-family picture is exposed (not hidden): color's single rule generalizes; each family is
    # still separable by SOME cheap baseline -> no over-claim of unique visual-structure advantage
    r = m.run()
    cfs = r["cross_family_summary"]
    assert cfs["color_single_fixed_rule_generalizes_across_all_families"] is True
    assert "each_family_separable_by_some_cheap_baseline" in cfs
    assert "small_sample_caveat" in cfs


def test_no_vision_temporal_or_memory_claim_in_source():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    assert "not proven vision" in src
    assert "no memory-system" in src or "memory-system integration" in src
    assert "temporal" in src
