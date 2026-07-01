"""tests/test_ambiguity_context_diversity_memory_plan_shaping.py

Ambiguity context-diversity shaping v1 (Layer-1 / MemoryPlan shaping).

Locks the approved rule (env flag ``TORMENT_AMBIGUITY_CONTEXT_DIVERSITY_V1``):
when ambiguity is HIGH, avoid over-collapsing retrieval into a single lane by giving
each already-enabled NON-CORE lane a tiny, bounded ``+1`` BUDGET lift on
``top_k_by_lane`` (capped per lane). Driven purely by the content-free
``state.ambiguity_score`` -- no dynamic-kernel / geometric-context coupling.

Contract locked here (13 obligations):
  1.  flag OFF is a byte-identical no-op;
  2.  flag ON + high ambiguity -> ONLY already-enabled non-core ``top_k_by_lane``
      entries change (each by +1);
  3.  each +1 respects the small per-lane caps (deep<=4, relational<=5, archive<=5,
      collective<=3);
  4.  disabled lanes stay at budget 0;
  5.  no lane is newly enabled (retrieval booleans + disabled-lane budgets unchanged);
  6.  ``core`` top_k is unchanged;
  7.  ``weight_by_lane`` is unchanged;
  8.  retrieval booleans are unchanged;
  9.  ``safety_constraints`` and ``max_token_budget`` are unchanged;
  10. identity-/governance-sensitive turns are skipped;
  11. ReflectionTrace.lane_budget_shape mirrors the shaped top_k plan;
  12. lane_budget_shape carries no raw user marker text;
  13. low ambiguity (``<= 0.5``) is a no-op even with the flag on.
"""
from __future__ import annotations

import copy
import json

import pytest

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import MemoryPlan, EphemeralCognitionState
from torment_service.reflection_trace import build_reflection_trace

_FLAG = "_AMBIGUITY_CONTEXT_DIVERSITY_V1_ENABLE"
_LANES = ("core", "relational", "archive", "deep", "collective")


# ---------------------------------------------------------------------------
# builders (mirror the ambiguity/geometric-shaping test doubles)
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


def _plan(*, retrieve_relational=True, retrieve_archive=True, retrieve_deep=True,
          retrieve_collective=False) -> MemoryPlan:
    """A representative post-build MemoryPlan (non-core lanes mostly enabled).

    Budgets mirror ``build_memory_plan`` bases: core 6, relational 4, archive 4,
    deep 3, collective 2 (each 0 when its lane is disabled).
    """
    p = MemoryPlan()
    p.retrieve_core = True
    p.retrieve_relational = retrieve_relational
    p.retrieve_deep = retrieve_deep
    p.retrieve_archive = retrieve_archive
    p.retrieve_collective = retrieve_collective
    p.top_k_by_lane = {
        "core": 6,
        "relational": 4 if retrieve_relational else 0,
        "archive": 4 if retrieve_archive else 0,
        "deep": 3 if retrieve_deep else 0,
        "collective": 2 if retrieve_collective else 0,
    }
    p.weight_by_lane = {
        "core": 1.0,
        "relational": 0.85 if retrieve_relational else 0.0,
        "archive": 0.45 if retrieve_archive else 0.0,
        "deep": 0.60 if retrieve_deep else 0.0,
        "collective": 0.30 if retrieve_collective else 0.0,
    }
    p.max_token_budget = 2000
    p.safety_constraints = ["no_raw_user_text"]
    return p


def _shape(plan, state):
    ThinkingController()._apply_ambiguity_context_diversity_v1(plan, state)
    return plan


# ---------------------------------------------------------------------------
# 1. flag off is a byte-identical no-op
# ---------------------------------------------------------------------------

def test_flag_off_is_noop(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, False)
    p = _plan(retrieve_collective=True)
    before_tk = copy.deepcopy(p.top_k_by_lane)
    before_w = copy.deepcopy(p.weight_by_lane)
    _shape(p, _state(ambiguity_score=0.9))
    assert p.top_k_by_lane == before_tk
    assert p.weight_by_lane == before_w


# ---------------------------------------------------------------------------
# 2 + 6. flag on, high ambiguity -> ONLY enabled non-core top_k change (+1); core same
# ---------------------------------------------------------------------------

def test_only_enabled_non_core_top_k_change_by_plus_one(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan()  # deep 3, relational 4, archive 4 enabled; collective disabled (0)
    before_tk = copy.deepcopy(p.top_k_by_lane)
    before_w = copy.deepcopy(p.weight_by_lane)
    _shape(p, _state(ambiguity_score=0.9))
    # each already-enabled non-core lane lifted by exactly +1
    assert p.top_k_by_lane["deep"] == before_tk["deep"] + 1        # 3 -> 4
    assert p.top_k_by_lane["relational"] == before_tk["relational"] + 1  # 4 -> 5
    assert p.top_k_by_lane["archive"] == before_tk["archive"] + 1  # 4 -> 5
    # core untouched; disabled collective untouched
    assert p.top_k_by_lane["core"] == 6
    assert p.top_k_by_lane["collective"] == 0
    # weights never move
    assert p.weight_by_lane == before_w


def test_core_top_k_unchanged(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_collective=True)
    _shape(p, _state(ambiguity_score=1.0))
    assert p.top_k_by_lane["core"] == 6


# ---------------------------------------------------------------------------
# 3. each +1 respects the small per-lane caps
# ---------------------------------------------------------------------------

def test_each_plus_one_respects_per_lane_caps(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_collective=True)
    # push every enabled non-core lane to (or past) its cap; the lift must NOT exceed it
    p.top_k_by_lane.update({"deep": 4, "relational": 5, "archive": 5, "collective": 3})
    _shape(p, _state(ambiguity_score=1.0))
    assert p.top_k_by_lane["deep"] == 4          # cap 4
    assert p.top_k_by_lane["relational"] == 5    # cap 5
    assert p.top_k_by_lane["archive"] == 5       # cap 5
    assert p.top_k_by_lane["collective"] == 3    # cap 3
    assert p.top_k_by_lane["core"] == 6


def test_collective_lifts_toward_its_cap(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_collective=True)  # collective base budget 2
    _shape(p, _state(ambiguity_score=0.9))
    assert p.top_k_by_lane["collective"] == 3    # 2 -> 3, at cap


# ---------------------------------------------------------------------------
# 4 + 5. disabled lanes stay at 0; no lane is newly enabled
# ---------------------------------------------------------------------------

def test_disabled_lanes_stay_zero_and_not_enabled(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_relational=False, retrieve_collective=False)
    assert p.top_k_by_lane["relational"] == 0 and p.top_k_by_lane["collective"] == 0
    _shape(p, _state(ambiguity_score=0.9))
    # disabled lanes remain at budget 0 (never lifted to 1)
    assert p.top_k_by_lane["relational"] == 0
    assert p.top_k_by_lane["collective"] == 0
    # and were not turned on
    assert p.retrieve_relational is False
    assert p.retrieve_collective is False


def test_retrieval_booleans_unchanged(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_collective=True)
    flags = {k: getattr(p, k) for k in
             ("retrieve_core", "retrieve_relational", "retrieve_deep",
              "retrieve_archive", "retrieve_collective")}
    _shape(p, _state(ambiguity_score=0.9))
    for k, v in flags.items():
        assert getattr(p, k) == v


# ---------------------------------------------------------------------------
# 7. weight_by_lane is unchanged
# ---------------------------------------------------------------------------

def test_weight_by_lane_unchanged(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_collective=True)
    before_w = copy.deepcopy(p.weight_by_lane)
    _shape(p, _state(ambiguity_score=0.9))
    assert p.weight_by_lane == before_w


# ---------------------------------------------------------------------------
# 9. safety_constraints + max_token_budget are unchanged
# ---------------------------------------------------------------------------

def test_safety_and_token_budget_unchanged(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_collective=True)
    before_safety = copy.deepcopy(p.safety_constraints)
    before_budget = p.max_token_budget
    _shape(p, _state(ambiguity_score=0.9))
    assert p.safety_constraints == before_safety
    assert p.max_token_budget == before_budget


# ---------------------------------------------------------------------------
# 10. identity-/governance-sensitive turns are skipped
# ---------------------------------------------------------------------------

def test_identity_and_governance_sensitive_are_skipped(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    for over in ({"identity_sensitive": True}, {"governance_sensitive": True}):
        p = _plan(retrieve_collective=True)
        before = copy.deepcopy(p.top_k_by_lane)
        _shape(p, _state(ambiguity_score=0.9, **over))
        assert p.top_k_by_lane == before


# ---------------------------------------------------------------------------
# 13. low ambiguity (<= 0.5) is a no-op even with the flag on
# ---------------------------------------------------------------------------

def test_low_ambiguity_is_noop_even_with_flag_on(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    for amb in (0.3, 0.5):  # 0.5 is the boundary: strictly > 0.5 is required
        p = _plan(retrieve_collective=True)
        before = copy.deepcopy(p.top_k_by_lane)
        _shape(p, _state(ambiguity_score=amb))
        assert p.top_k_by_lane == before


# ---------------------------------------------------------------------------
# 11. ReflectionTrace.lane_budget_shape mirrors the shaped top_k plan
# ---------------------------------------------------------------------------

def _trace_for(plan):
    return build_reflection_trace(
        chosen_mode="reflective", action="answer", stance=None,
        review_status_flags={"approved": True},
        top_k_by_lane=plan.top_k_by_lane, weight_by_lane=plan.weight_by_lane,
        geometric_context_present=False,
    )


def test_lane_budget_shape_mirrors_shaped_plan(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    p = _plan(retrieve_collective=True)
    _shape(p, _state(ambiguity_score=0.9))
    trace = _trace_for(p)
    assert dict(trace.lane_budget_shape) == {
        k: int(v) for k, v in p.top_k_by_lane.items()}


def test_think_end_to_end_broadens_enabled_non_core_budgets(monkeypatch):
    text = "maybe remember stuff??"  # high ambiguity (maybe + stuff + "??") + memory_need
    monkeypatch.setattr(tc, _FLAG, False)
    off = ThinkingController().think("ws", "ag", text).memory_plan
    monkeypatch.setattr(tc, _FLAG, True)
    r = ThinkingController().think("ws", "ag", text)
    on = r.memory_plan
    assert r.task_frame.ambiguity_score > 0.5
    assert not r.task_frame.governance_sensitive and not r.task_frame.identity_sensitive
    # core budget identical with flag off vs on
    assert on.top_k_by_lane["core"] == off.top_k_by_lane["core"]
    lifted = []
    for lane in ("deep", "relational", "archive", "collective"):
        b_off = off.top_k_by_lane.get(lane, 0)
        b_on = on.top_k_by_lane.get(lane, 0)
        if getattr(off, f"retrieve_{lane}", False) and b_off > 0:
            assert b_on >= b_off            # enabled non-core lane never shrinks
        else:
            assert b_on == b_off            # disabled lane not enabled/broadened
        if b_on > b_off:
            lifted.append(lane)
    assert lifted, "expected at least one already-enabled non-core lane to broaden"
    # trace mirrors the effective (shaped) budgets end-to-end
    assert dict(r.reflection_trace.lane_budget_shape) == {
        k: int(v) for k, v in on.top_k_by_lane.items()}


# ---------------------------------------------------------------------------
# 12. lane_budget_shape carries no raw user marker text
# ---------------------------------------------------------------------------

def test_lane_budget_shape_has_no_raw_user_text(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    marker = "ZZQ_USER_MARKER_9X"
    r = ThinkingController().think("ws", "ag", f"maybe remember stuff?? {marker}")
    lb = r.reflection_trace.lane_budget_shape
    assert set(lb.keys()) <= set(_LANES)
    assert all(isinstance(k, str) for k in lb.keys())
    assert all(isinstance(v, int) for v in lb.values())
    assert marker not in json.dumps(dict(lb))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
