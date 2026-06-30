"""tests/test_reflection_trace_lane_weight_shape.py - lane_weight_shape observability.

ReflectionTrace.lane_weight_shape exposes the already-computed
MemoryPlan.weight_by_lane (content-free lane->weight numbers) so operators can
OBSERVE the existing deterministic lane-weight shaping (geometric / relational)
without any new shaping rule, write path, provider path, endpoint, or control
branch.

Proves:
  * default / no-shaping weights are observable and stable;
  * enabling the EXISTING geometric weight shaping becomes visible in
    lane_weight_shape as weights (matching memory_plan.weight_by_lane), not as a
    control signal;
  * the field is content-free (lane names -> floats only).

Scope: tests-only. No new shaping/scoring rule. No MemoryPlan behavior change.
No provider/endpoint/schema/database/write. test-local only.
"""
from __future__ import annotations

import json

import pytest

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import GeometricStanceContext

_FLAG = "_GEOMETRIC_MEMORY_SHAPING_V1_ENABLE"


def _geo(coherence, stability) -> GeometricStanceContext:
    return GeometricStanceContext(
        coherence=coherence, stability=stability,
        identity_lock=0.5, ambiguity_tolerance=0.5, social_resonance=0.5,
    )


def _plan_weights(result):
    return {
        str(k): float(v)
        for k, v in result.memory_plan.weight_by_lane.items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }


def _trace_weights(result):
    return dict(result.reflection_trace.lane_weight_shape)


def test_default_weights_observable_and_stable():
    # No geometric shaping: lane_weight_shape mirrors the base plan weights ...
    r = ThinkingController().think("ws", "ag", "what do I remember about coffee")
    assert _trace_weights(r) == _plan_weights(r)
    # ... and is deterministic / stable across identical calls.
    r2 = ThinkingController().think("ws", "ag", "what do I remember about coffee")
    assert _trace_weights(r) == _trace_weights(r2)


def test_geometric_shaping_observable_as_weights(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    text = "what do you recall about the calm water this afternoon"
    r_geo = ctl.think("ws", "ag", text, geometric_context=_geo(0.95, 0.95))
    r_none = ctl.think("ws", "ag", text, geometric_context=None)

    # guard: not a governance/identity turn (those skip shaping)
    assert not r_geo.task_frame.governance_sensitive
    assert not r_geo.task_frame.identity_sensitive

    # the trace surfaces EXACTLY the (shaped) effective plan weights ...
    assert _trace_weights(r_geo) == _plan_weights(r_geo)
    assert _trace_weights(r_none) == _plan_weights(r_none)
    # ... high coherence/stability shaping IS visible as a weight change vs the
    # unshaped baseline (observable, deterministic) -- not a control signal.
    assert _trace_weights(r_geo) != _trace_weights(r_none)
    assert r_geo.memory_plan.weight_by_lane["core"] > r_none.memory_plan.weight_by_lane["core"]
    assert _trace_weights(r_geo)["core"] == pytest.approx(
        r_geo.memory_plan.weight_by_lane["core"])


def test_lane_weight_shape_is_content_free(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    token = "ZZQ_LANEWEIGHT_MARKER_4B7E"
    r = ThinkingController().think(
        "ws", "ag", f"recall the calm water and remember {token}",
        geometric_context=_geo(0.9, 0.9),
    )
    lw = r.reflection_trace.lane_weight_shape
    assert all(isinstance(k, str) for k in lw.keys())
    assert all(isinstance(v, float) for v in lw.values())
    assert token not in json.dumps(dict(lw))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
