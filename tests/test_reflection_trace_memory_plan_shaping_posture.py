"""tests/test_reflection_trace_memory_plan_shaping_posture.py

ReflectionTrace MemoryPlan shaping posture (Layer-1 observability).

Locks a content-free, fixed-key boolean map on ReflectionTrace,
``memory_plan_shaping_posture``, that records which default-off MemoryPlan
shaping reflex ACTUALLY changed the effective plan this turn:

    {
        "relational_ambiguity_prominence": True | False,
        "ambiguity_context_diversity": True | False,
    }

True  -> the reflex actually changed the effective MemoryPlan.
False -> the reflex was disabled, ineligible, skipped, or a no-op.

The posture is populated from before/after MemoryPlan deltas around the two
existing shaping helpers (relational weight delta / top_k budget delta) — never
from raw text, prompt, private reasoning, provider data, or output decisions.

Obligations locked here:
  1.  ``memory_plan_shaping_posture`` appears in ``ReflectionTrace.to_dict()``.
  2.  Keys are exactly the two fixed keys.
  3.  Values are booleans only.
  4.  Both flags off -> both False.
  5.  Relational-ambiguity enabled + eligible -> only relational True.
  6.  Ambiguity-context-diversity enabled + eligible -> only ambiguity True.
  7.  Both enabled + eligible -> both True.
  8.  Enabled but ineligible / no-op -> remains False.
  9.  Governance/identity skip paths remain False.
  10. JSON trace does not contain raw user marker text.
  11. Existing ``lane_weight_shape`` behavior is unchanged.
  12. Existing ``lane_budget_shape`` behavior is unchanged.
"""
from __future__ import annotations

import json

import pytest

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.reflection_trace import (
    build_reflection_trace,
    _MEMORY_PLAN_SHAPING_POSTURE_KEYS,
)

_REL_FLAG = "_RELATIONAL_AMBIGUITY_PROMINENCE_V1_ENABLE"
_AMB_FLAG = "_AMBIGUITY_CONTEXT_DIVERSITY_V1_ENABLE"
_POSTURE_KEYS = {"relational_ambiguity_prominence", "ambiguity_context_diversity"}

# Crafted inputs (see _estimate_ambiguity + GOVERNANCE/IDENTITY hint words):
#   EL  : ambiguity 0.95 (maybe + stuff + "??" + <4 words) AND memory_need
#         ("remember" -> relational lane enabled); NOT governance/identity.
#   LOW : ambiguity 0.0 (>=4 words, no ambiguity markers) -> reflexes ineligible.
#   GOV : high ambiguity AND governance-sensitive ("delete").
#   IDN : high ambiguity AND identity-sensitive ("self").
_EL = "maybe remember stuff??"
_LOW = "please summarize the quarterly financial results document"
_GOV = "maybe delete stuff??"
_IDN = "maybe self stuff??"


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------

def _min_trace(**over):
    kw = dict(
        chosen_mode="reflective", action="answer", stance=None,
        review_status_flags={"approved": True},
        top_k_by_lane={"core": 6, "relational": 4, "deep": 0},
        weight_by_lane={"core": 1.0, "relational": 0.85, "deep": 0.0},
        geometric_context_present=False,
    )
    kw.update(over)
    return build_reflection_trace(**kw)


def _posture_via_think(monkeypatch, text, *, rel, amb):
    monkeypatch.setattr(tc, _REL_FLAG, rel)
    monkeypatch.setattr(tc, _AMB_FLAG, amb)
    r = ThinkingController().think("ws", "ag", text)
    return dict(r.reflection_trace.memory_plan_shaping_posture), r


# ---------------------------------------------------------------------------
# 1-3. shape of the field: present in to_dict, fixed keys, boolean values
# ---------------------------------------------------------------------------

def test_posture_appears_in_to_dict():
    d = _min_trace().to_dict()
    assert "memory_plan_shaping_posture" in d


def test_posture_keys_are_exactly_the_two_fixed_keys():
    p = _min_trace().to_dict()["memory_plan_shaping_posture"]
    assert set(p.keys()) == _POSTURE_KEYS
    # the module constant is the single source of truth for the keys
    assert set(_MEMORY_PLAN_SHAPING_POSTURE_KEYS) == _POSTURE_KEYS


def test_posture_values_are_booleans_only():
    p = _min_trace().to_dict()["memory_plan_shaping_posture"]
    assert all(isinstance(v, bool) for v in p.values())


def test_default_construction_has_both_keys_false():
    # fixed keys always present even with no posture supplied
    p = dict(_min_trace().memory_plan_shaping_posture)
    assert p == {"relational_ambiguity_prominence": False,
                 "ambiguity_context_diversity": False}


def test_build_normalizes_partial_and_dirty_posture():
    # partial map + stray/text keys + non-bool value -> exactly two bool keys
    t = _min_trace(memory_plan_shaping_posture={
        "relational_ambiguity_prominence": 1,     # truthy non-bool -> True
        "junk_text_key": "ZZQ_should_be_dropped",  # stray key dropped
    })
    p = dict(t.memory_plan_shaping_posture)
    assert set(p.keys()) == _POSTURE_KEYS
    assert p["relational_ambiguity_prominence"] is True
    assert p["ambiguity_context_diversity"] is False       # missing -> False
    assert all(isinstance(v, bool) for v in p.values())


def test_posture_map_is_read_only():
    t = _min_trace()
    with pytest.raises((TypeError, AttributeError)):
        t.memory_plan_shaping_posture["relational_ambiguity_prominence"] = True  # type: ignore[index]


# ---------------------------------------------------------------------------
# 4. both flags off -> both False
# ---------------------------------------------------------------------------

def test_both_flags_off_both_false(monkeypatch):
    p, _ = _posture_via_think(monkeypatch, _EL, rel=False, amb=False)
    assert p == {"relational_ambiguity_prominence": False,
                 "ambiguity_context_diversity": False}


# ---------------------------------------------------------------------------
# 5. relational-ambiguity enabled + eligible -> only relational True
# ---------------------------------------------------------------------------

def test_relational_only_true(monkeypatch):
    p, r = _posture_via_think(monkeypatch, _EL, rel=True, amb=False)
    # precondition the crafted input is chosen to satisfy
    assert r.task_frame.ambiguity_score > 0.5
    assert r.memory_plan.retrieve_relational
    assert not r.task_frame.governance_sensitive and not r.task_frame.identity_sensitive
    assert p == {"relational_ambiguity_prominence": True,
                 "ambiguity_context_diversity": False}


# ---------------------------------------------------------------------------
# 6. ambiguity-context-diversity enabled + eligible -> only ambiguity True
# ---------------------------------------------------------------------------

def test_ambiguity_only_true(monkeypatch):
    p, r = _posture_via_think(monkeypatch, _EL, rel=False, amb=True)
    assert r.task_frame.ambiguity_score > 0.5
    assert r.memory_plan.retrieve_relational                    # a non-core lane is enabled
    assert p == {"relational_ambiguity_prominence": False,
                 "ambiguity_context_diversity": True}


# ---------------------------------------------------------------------------
# 7. both enabled + eligible -> both True
# ---------------------------------------------------------------------------

def test_both_enabled_both_true(monkeypatch):
    p, _ = _posture_via_think(monkeypatch, _EL, rel=True, amb=True)
    assert p == {"relational_ambiguity_prominence": True,
                 "ambiguity_context_diversity": True}


# ---------------------------------------------------------------------------
# 8. enabled but ineligible / no-op -> remains False
# ---------------------------------------------------------------------------

def test_enabled_but_low_ambiguity_is_false(monkeypatch):
    p, r = _posture_via_think(monkeypatch, _LOW, rel=True, amb=True)
    assert r.task_frame.ambiguity_score <= 0.5                  # ineligible: low ambiguity
    assert p == {"relational_ambiguity_prominence": False,
                 "ambiguity_context_diversity": False}


# ---------------------------------------------------------------------------
# 9. governance/identity skip paths remain False
# ---------------------------------------------------------------------------

def test_governance_sensitive_skip_is_false(monkeypatch):
    p, r = _posture_via_think(monkeypatch, _GOV, rel=True, amb=True)
    assert r.task_frame.governance_sensitive
    assert p == {"relational_ambiguity_prominence": False,
                 "ambiguity_context_diversity": False}


def test_identity_sensitive_skip_is_false(monkeypatch):
    p, r = _posture_via_think(monkeypatch, _IDN, rel=True, amb=True)
    assert r.task_frame.identity_sensitive
    assert p == {"relational_ambiguity_prominence": False,
                 "ambiguity_context_diversity": False}


# ---------------------------------------------------------------------------
# 10. JSON trace does not contain raw user marker text
# ---------------------------------------------------------------------------

def test_json_trace_has_no_raw_user_marker_text(monkeypatch):
    monkeypatch.setattr(tc, _REL_FLAG, True)
    monkeypatch.setattr(tc, _AMB_FLAG, True)
    marker = "ZZQ_POSTURE_MARKER_7Q"
    r = ThinkingController().think("ws", "ag", f"maybe remember stuff?? {marker}")
    blob = json.dumps(r.reflection_trace.to_dict())
    assert marker not in blob
    posture = r.reflection_trace.to_dict()["memory_plan_shaping_posture"]
    assert set(posture.keys()) == _POSTURE_KEYS
    assert all(isinstance(v, bool) for v in posture.values())


# ---------------------------------------------------------------------------
# 11 + 12. existing lane_weight_shape / lane_budget_shape behavior unchanged
# ---------------------------------------------------------------------------

def test_lane_weight_shape_behavior_unchanged():
    t = build_reflection_trace(
        chosen_mode="reflective", action="answer", stance=None,
        review_status_flags={"approved": True},
        top_k_by_lane={"core": 6, "relational": 4, "deep": 0},
        weight_by_lane={"core": 1.0, "relational": 0.85, "deep": 0.0},
        geometric_context_present=False,
    )
    assert dict(t.lane_weight_shape) == {"core": 1.0, "relational": 0.85, "deep": 0.0}
    assert all(isinstance(v, float) for v in t.lane_weight_shape.values())


def test_lane_budget_shape_behavior_unchanged():
    t = build_reflection_trace(
        chosen_mode="reflective", action="answer", stance=None,
        review_status_flags={"approved": True},
        top_k_by_lane={"core": 6, "relational": 4, "deep": 0},
        weight_by_lane={"core": 1.0, "relational": 0.85, "deep": 0.0},
        geometric_context_present=False,
    )
    assert dict(t.lane_budget_shape) == {"core": 6, "relational": 4, "deep": 0}
    assert all(isinstance(v, int) for v in t.lane_budget_shape.values())


def test_think_lane_shapes_still_mirror_effective_plan(monkeypatch):
    # end-to-end: adding the posture field does not disturb the existing lane
    # shape mirrors of the effective MemoryPlan.
    monkeypatch.setattr(tc, _REL_FLAG, True)
    monkeypatch.setattr(tc, _AMB_FLAG, True)
    r = ThinkingController().think("ws", "ag", _EL)
    rt, mp = r.reflection_trace, r.memory_plan
    assert dict(rt.lane_weight_shape) == {k: float(v) for k, v in mp.weight_by_lane.items()}
    assert dict(rt.lane_budget_shape) == {k: int(v) for k, v in mp.top_k_by_lane.items()}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
