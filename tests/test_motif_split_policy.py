"""Frozen characterization of legacy ``MotifRegistry._maybe_split_motif``."""
from __future__ import annotations

import numpy as np
import pytest

from torment_service.motif_decision import _unit
from torment_service.motif_split_policy import MotifSplitPlan, NoMotifSplit, decide_motif_auto_split
from torment_service.motifs import Motif, MotifRegistry


def _decision(vectors, centroid):
    return decide_motif_auto_split(
        tuple((index, _unit(np.asarray(vector, dtype=np.float32))) for index, vector in enumerate(vectors)),
        np.asarray(centroid, dtype=np.float32),
    )


def test_below_radius_and_too_small_child_remain_no_split_at_the_legacy_minimum():
    below_radius = _decision([(1.0, 0.0, 0.0)] * 96, (1.0, 0.0, 0.0))
    assert isinstance(below_radius, NoMotifSplit) and below_radius.reason == "RADIUS"

    too_small = _decision(
        [(1.0, 0.0, 0.0)] * 81 + [(-1.0, 0.0, 0.0)] * 15,
        (1.0, 0.0, 0.0),
    )
    assert isinstance(too_small, NoMotifSplit) and too_small.reason == "CHILD_POPULATION"


def test_high_dimensional_radius_eligible_evidence_can_fail_the_improvement_gate():
    rng = np.random.default_rng(123)
    vectors = [_unit(row) for row in rng.normal(size=(96, 256)).astype(np.float32)]
    outcome = _decision(vectors, _unit(np.mean(vectors, axis=0)))
    assert isinstance(outcome, NoMotifSplit) and outcome.reason == "SSE_IMPROVEMENT"


def test_true_split_is_deterministic_tie_stable_and_uses_legacy_cluster_order():
    vectors = [(1.0, 0.0, 0.0)] * 48 + [(-1.0, 0.0, 0.0)] * 48
    first = _decision(vectors, (1.0, 0.0, 0.0))
    second = _decision(vectors, (1.0, 0.0, 0.0))
    assert isinstance(first, MotifSplitPlan) and second == first
    # The earliest farthest point is the first negative member.  It is seed A
    # and therefore legacy parent cluster 0; child preserves positive order.
    assert first.parent_members == tuple(range(48, 96))
    assert first.child_members == tuple(range(48))
    assert first.radius_before >= .22 and first.sse_improvement >= .08


def test_later_attach_after_the_minimum_uses_the_same_policy_again():
    vectors = [(1.0, 0.0, 0.0)] * 49 + [(-1.0, 0.0, 0.0)] * 49
    outcome = _decision(vectors, (1.0, 0.0, 0.0))
    assert isinstance(outcome, MotifSplitPlan)
    assert len(outcome.parent_members) == 49
    assert len(outcome.child_members) == 49


def test_legacy_registry_split_output_remains_the_frozen_contract(tmp_path, monkeypatch):
    """Exercise the real legacy mutation surface against the frozen fixture."""
    registry = MotifRegistry(str(tmp_path), "split-policy", "reflection")
    motif_id = "motif_reflection_0001"
    registry.motifs[motif_id] = Motif(
        motif_id, "reflection", "Legacy basin", [1.0, 0.0, 0.0], .70,
        list(range(96)), ["aria", "nox"], .80, 100, 101,
    )
    registry._next_id = 2  # recovered global counter after the pre-existing parent
    vectors = {
        index: _unit(np.asarray(vector, dtype=np.float32))
        for index, vector in enumerate(([(1.0, 0.0, 0.0)] * 48) + ([( -1.0, 0.0, 0.0)] * 48))
    }
    monkeypatch.setattr(registry, "_member_embedding", lambda eid: vectors[eid])

    event = registry._maybe_split_motif(motif_id)

    assert event is not None
    assert event["parent"] == motif_id
    assert event["child"] == "motif_reflection_0001_split_0002"
    assert event["parent_members"] == 48 and event["child_members"] == 48
    parent = registry.motifs[motif_id]
    child = registry.motifs[event["child"]]
    assert parent.members == list(range(48, 96))
    assert child.members == list(range(48))
    assert np.asarray(parent.centroid) == pytest.approx((-1.0, 0.0, 0.0), abs=1e-7)
    assert np.asarray(child.centroid) == pytest.approx((1.0, 0.0, 0.0), abs=1e-7)
    assert parent.strength == pytest.approx(.12 + .88 * (1.0 - np.exp(-48 / 24.0)))
    assert child.strength == pytest.approx(.12 + .88 * (1.0 - np.exp(-48 / 24.0)))
    assert child.stability_score == .80
    assert child.contributing_agents == ["aria", "nox"]
