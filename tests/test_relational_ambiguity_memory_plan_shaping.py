"""tests/test_relational_ambiguity_memory_plan_shaping.py

Relational ambiguity-prominence shaping v1 (Layer-1 / MemoryPlan shaping).

Locks the approved rule (env flag ``TORMENT_RELATIONAL_AMBIGUITY_PROMINENCE_V1``):
when ambiguity is HIGH and the ``relational`` lane is already enabled, give it a
small, bounded advisory WEIGHT lift (prominence) driven purely by the content-free
``state.ambiguity_score`` -- no dynamic-kernel / geometric-context coupling.

Contract locked here:
  1. flag OFF is a byte-identical no-op;
  2. flag ON + high ambiguity + relational enabled -> ONLY weight_by_lane["relational"]
     changes;
  3. top_k_by_lane is unchanged;
  4. retrieval booleans / lane eligibility are unchanged;
  5. core / deep / archive / collective weights are unchanged;
  6. identity- or governance-sensitive turns are skipped;
  7. a disabled relational lane stays disabled and unshaped;
  8. ReflectionTrace.lane_weight_shape mirrors the shaped relational weight;
  9. lane_weight_shape carries no raw user marker text.
"""
from __future__ import annotations

import copy
import json

import pytest

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import MemoryPlan, EphemeralCognitionState
from torment_service.reflection_trace import build_reflection_trace

_FLAG = "_RELATIONAL_AMBIGUITY_PROMINENCE_V1_ENABLE"
_LANES = ("core", "relational", "archive", "deep", "collective")


# ---------------------------------------------------------------------------
# builders (mirror the geometric-shaping test doubles)
# ---------------------------------------------------------------------------

def _state(**over) -> EphemeralCognitionState:
    base = dict(
        chosen_mode="reflective", allowed_depth=2, requires_self_review=False,
        may_escalate=False, confidence_floor=0.0, urgency=0.2, ambiguity_score=0.9,
        confidence_need=0.3, action_need=False, memory_need=True, tool_need=False,
        governance_sensitive=False, identity_sensitive=False, live_social=False,
        archive_context_signal=False, collective_context_signal=False,
        character_state_context_eligible=True, deep_context_eligible=True,
    )
    base.update(over)
    return EphemeralCognitionState(**base)


def _plan(*, relational=0.85, retrieve_relational=True) -> MemoryPlan:
    p = MemoryPlan()
    p.retrieve_core = True
    p.retrieve_relational = retrieve_relational
    p.retrieve_deep = True
    p.retrieve_archive = True
    p.retrieve_collective = False
    p.top_k_by_lane = {"core": 6, "relational": 4 if retrieve_relational else 0,
                       "archive": 4, "deep": 3, "collective": 0}
    p.weight_by_lane = {"core": 1.0,
                        "relational": relational if retrieve_relational else 0.0,
                        "archive": 0.45, "deep": 0.60, "collective": 0.0}
    return p


def _shape(plan, state):
    ThinkingController()._apply_relational_ambiguity_prominence_v1(plan, state)
    return plan


# ---------------------------------------------------------------------------
# 1. flag off is a no-op
# ---------------------------------------------------------------------------

def test_flag_off_is_noop(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, False)
    p = _plan()
    before_w, before_tk = copy.deepcopy(p.weight_by_lane), copy.deepcopy(p.top_k_by_lane)
    _shape(p, _state(ambiguity_score=0.9))
    assert p.weight_by_lane == before_w
    assert p.top_k_by_lane == before_tk


# ---------------------------------------------------------------------------
# 2 + 5. flag on, high ambiguity, relational enabled -> only relational weight moves
# ---------------------------------------------------------------------------

def test_only_relational_weight_changes(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan()
    before = copy.deepcopy(p.weight_by_lane)
    _shape(p, _state(ambiguity_score=0.9))
    assert p.weight_by_lane["relational"] > before["relational"]  # lifted
    for lane in ("core", "deep", "archive", "collective"):
        assert p.weight_by_lane[lane] == before[lane]


def test_low_ambiguity_is_noop_even_with_flag_on(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan()
    before = copy.deepcopy(p.weight_by_lane)
    _shape(p, _state(ambiguity_score=0.3))
    assert p.weight_by_lane == before


def test_lift_is_bounded_and_below_core(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan()
    _shape(p, _state(ambiguity_score=1.0))  # maximum ambiguity -> maximum lift
    r = p.weight_by_lane["relational"]
    self_core = p.weight_by_lane["core"]
    assert 0.85 < r <= 0.99            # lifted, capped under the peripheral ceiling
    assert r < self_core               # relational stays below core prominence


# ---------------------------------------------------------------------------
# 3. top_k_by_lane unchanged
# ---------------------------------------------------------------------------

def test_top_k_by_lane_unchanged(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan()
    before_tk = copy.deepcopy(p.top_k_by_lane)
    _shape(p, _state(ambiguity_score=0.9))
    assert p.top_k_by_lane == before_tk


# ---------------------------------------------------------------------------
# 4. retrieval booleans / lane eligibility unchanged
# ---------------------------------------------------------------------------

def test_retrieval_booleans_unchanged(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan()
    flags = {k: getattr(p, k) for k in
             ("retrieve_core", "retrieve_relational", "retrieve_deep",
              "retrieve_archive", "retrieve_collective")}
    _shape(p, _state(ambiguity_score=0.9))
    for k, v in flags.items():
        assert getattr(p, k) == v


# ---------------------------------------------------------------------------
# 6. identity-/governance-sensitive turns are skipped
# ---------------------------------------------------------------------------

def test_identity_and_governance_sensitive_are_skipped(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    for over in ({"identity_sensitive": True}, {"governance_sensitive": True}):
        p = _plan()
        before = copy.deepcopy(p.weight_by_lane)
        _shape(p, _state(ambiguity_score=0.9, **over))
        assert p.weight_by_lane == before


# ---------------------------------------------------------------------------
# 7. disabled relational lane stays disabled and unshaped
# ---------------------------------------------------------------------------

def test_disabled_relational_stays_disabled(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_relational=False)
    assert p.weight_by_lane["relational"] == 0.0
    before = copy.deepcopy(p.weight_by_lane)
    _shape(p, _state(ambiguity_score=0.9))
    assert p.weight_by_lane["relational"] == 0.0       # never enabled/lifted
    assert p.retrieve_relational is False
    assert p.weight_by_lane == before


# ---------------------------------------------------------------------------
# 8. ReflectionTrace.lane_weight_shape mirrors the shaped relational weight
# ---------------------------------------------------------------------------

def _trace_for(plan):
    return build_reflection_trace(
        chosen_mode="reflective", action="answer", stance=None,
        review_status_flags={"approved": True},
        top_k_by_lane=plan.top_k_by_lane, weight_by_lane=plan.weight_by_lane,
        geometric_context_present=False,
    )


def test_lane_weight_shape_mirrors_shaped_relational(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan()
    _shape(p, _state(ambiguity_score=0.9))
    shaped = p.weight_by_lane["relational"]
    trace = _trace_for(p)
    assert trace.lane_weight_shape["relational"] == pytest.approx(shaped)
    assert dict(trace.lane_weight_shape) == {k: float(v) for k, v in p.weight_by_lane.items()}


def test_think_end_to_end_lifts_relational_and_trace_mirrors(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    # crafted: high ambiguity (maybe + stuff + "??") + memory_need (remember) +
    # not governance/identity sensitive. (_estimate_ambiguity adds +0.20 per
    # distinct category, so several categories are needed to exceed 0.5.)
    r = ThinkingController().think("ws", "ag", "maybe remember stuff??")
    frame, plan, trace = r.task_frame, r.memory_plan, r.reflection_trace
    # preconditions the crafted input is chosen to satisfy
    assert frame.ambiguity_score > 0.5
    assert plan.retrieve_relational and plan.weight_by_lane["relational"] > 0.0
    assert not frame.governance_sensitive and not frame.identity_sensitive
    # the shaping fired end-to-end: relational lifted above base, below core, and
    # the trace mirrors the effective plan weights.
    assert plan.weight_by_lane["relational"] > 0.85
    assert plan.weight_by_lane["relational"] < plan.weight_by_lane["core"]
    assert trace.lane_weight_shape["relational"] == pytest.approx(
        plan.weight_by_lane["relational"])


# ---------------------------------------------------------------------------
# 9. lane_weight_shape carries no raw user marker text
# ---------------------------------------------------------------------------

def test_lane_weight_shape_has_no_raw_user_text(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    marker = "ZZQ_USER_MARKER_9X"
    r = ThinkingController().think("ws", "ag", f"maybe remember stuff?? {marker}")
    lw = r.reflection_trace.lane_weight_shape
    assert set(lw.keys()) <= set(_LANES)
    assert all(isinstance(k, str) for k in lw.keys())
    assert all(isinstance(v, float) for v in lw.values())
    assert marker not in json.dumps(dict(lw))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
