"""tests/test_geometric_memory_plan_shaping.py — Geometric shaping v1.

First retrieval-facing consumer of the live kernel ``geometric_context``
(``stance_policy`` already consumes it for abstention): when present and the
default-off flag is on, it lightly shapes ``MemoryPlan.weight_by_lane``
for already-enabled core/deep lanes from coherence + stability. Guidance, not
control — bounded +/-15%, enabled lanes only, never touches top_k / retrieval
booleans / safety_constraints / budget, skipped on governance/identity turns.

Contract locked here:
  1. ``geometric_context is None`` (or flag off) ⇒ byte-identical MemoryPlan.
  2. High coherence/stability raises ONLY enabled lane weights.
  3. Low coherence/stability narrows ONLY enabled lane weights.
  4. Disabled lanes stay disabled (untouched).
  5. Governance-/identity-sensitive turns are skipped entirely.
  6. ``ThinkingController.think(..., geometric_context=geo)`` exposes the shaped
     plan in the ThinkingResult (and its ``to_dict()``).
  7. Live Spine advisory: ``resp.audit["advisory_thinking"]["memory_plan"]``
     reflects the geometric shaping deterministically from the live context.
"""
from __future__ import annotations

import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import (
    MemoryPlan,
    EphemeralCognitionState,
    GeometricStanceContext,
)

_FLAG = "_GEOMETRIC_MEMORY_SHAPING_V1_ENABLE"


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------

def _state(**over) -> EphemeralCognitionState:
    """A benign, non-governance, non-identity ephemeral state. Override as needed."""
    base = dict(
        chosen_mode="reflective",
        allowed_depth=2,
        requires_self_review=False,
        may_escalate=False,
        confidence_floor=0.0,
        urgency=0.2,
        ambiguity_score=0.2,
        confidence_need=0.3,
        action_need=False,
        memory_need=True,
        tool_need=False,
        governance_sensitive=False,
        identity_sensitive=False,
        live_social=False,
        archive_context_signal=False,
        collective_context_signal=False,
        character_state_context_eligible=True,
        deep_context_eligible=True,
    )
    base.update(over)
    return EphemeralCognitionState(**base)


def _plan(*, core=1.0, deep=0.60, relational=0.0,
          retrieve_deep=True, retrieve_relational=False) -> MemoryPlan:
    p = MemoryPlan()
    p.retrieve_core = True
    p.retrieve_deep = retrieve_deep
    p.retrieve_relational = retrieve_relational
    p.top_k_by_lane = {
        "core": 6,
        "deep": 3 if retrieve_deep else 0,
        "relational": 4 if retrieve_relational else 0,
    }
    p.weight_by_lane = {
        "core": core,
        "deep": deep if retrieve_deep else 0.0,
        "relational": relational if retrieve_relational else 0.0,
    }
    return p


def _geo(coherence, stability) -> GeometricStanceContext:
    return GeometricStanceContext(
        coherence=coherence,
        stability=stability,
        identity_lock=0.5,
        ambiguity_tolerance=0.5,
        social_resonance=0.5,
    )


def _expected_mult(coherence, stability) -> float:
    settled = max(0.0, min(1.0, 0.5 * (coherence + stability)))
    return max(0.85, min(1.15, 0.85 + 0.30 * settled))


# ---------------------------------------------------------------------------
# (1) None / flag-off ⇒ no-op
# ---------------------------------------------------------------------------

def test_geo_none_is_noop_even_with_flag_on(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    p = _plan()
    before = copy.deepcopy(p)
    ctl._apply_geometric_memory_shaping_v1(p, _state(), None)
    assert p.to_dict() == before.to_dict()


def test_flag_off_is_noop_even_with_geo(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, False)
    ctl = ThinkingController()
    p = _plan()
    before = copy.deepcopy(p)
    ctl._apply_geometric_memory_shaping_v1(p, _state(), _geo(0.95, 0.95))
    assert p.to_dict() == before.to_dict()


def test_build_memory_plan_geo_none_byte_identical(monkeypatch):
    """Even with the flag ON, geo=None must reproduce the base plan exactly."""
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    frame = ctl.frame_task("ws", "ag", "what do you recall about the calm water")
    mode = ctl.choose_mode(frame)
    base = ctl.build_memory_plan(frame, mode)
    geo_none = ctl.build_memory_plan(frame, mode, geometric_context=None)
    assert geo_none.to_dict() == base.to_dict()


# ---------------------------------------------------------------------------
# (2)/(3) directional weight shaping, weights-only
# ---------------------------------------------------------------------------

def _assert_only_weights_changed(before: MemoryPlan, after: MemoryPlan):
    assert after.top_k_by_lane == before.top_k_by_lane
    assert after.retrieve_core == before.retrieve_core
    assert after.retrieve_deep == before.retrieve_deep
    assert after.retrieve_relational == before.retrieve_relational
    assert after.safety_constraints == before.safety_constraints
    assert after.max_token_budget == before.max_token_budget


def test_high_settled_raises_enabled_lane_weights(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    p = _plan(core=1.0, deep=0.60, retrieve_deep=True)
    before = copy.deepcopy(p)
    ctl._apply_geometric_memory_shaping_v1(p, _state(), _geo(0.95, 0.95))
    mult = _expected_mult(0.95, 0.95)  # 1.135
    assert p.weight_by_lane["core"] == pytest.approx(before.weight_by_lane["core"] * mult)
    assert p.weight_by_lane["deep"] == pytest.approx(before.weight_by_lane["deep"] * mult)
    assert p.weight_by_lane["core"] > before.weight_by_lane["core"]
    assert p.weight_by_lane["core"] <= 1.15 + 1e-9  # bounded
    _assert_only_weights_changed(before, p)
    # untouched lane weight stays put
    assert p.weight_by_lane["relational"] == before.weight_by_lane["relational"]


def test_low_settled_narrows_enabled_lane_weights(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    p = _plan(core=1.0, deep=0.60, retrieve_deep=True)
    before = copy.deepcopy(p)
    ctl._apply_geometric_memory_shaping_v1(p, _state(), _geo(0.05, 0.05))
    mult = _expected_mult(0.05, 0.05)  # 0.865
    assert p.weight_by_lane["core"] == pytest.approx(before.weight_by_lane["core"] * mult)
    assert p.weight_by_lane["deep"] == pytest.approx(before.weight_by_lane["deep"] * mult)
    assert p.weight_by_lane["core"] < before.weight_by_lane["core"]
    assert p.weight_by_lane["core"] >= 0.85 - 1e-9  # bounded
    _assert_only_weights_changed(before, p)


def test_neutral_settled_is_identity(monkeypatch):
    """settled == 0.5 → multiplier exactly 1.0 → weights unchanged."""
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    p = _plan(core=1.0, deep=0.60)
    before = copy.deepcopy(p)
    ctl._apply_geometric_memory_shaping_v1(p, _state(), _geo(0.5, 0.5))
    assert p.weight_by_lane["core"] == pytest.approx(before.weight_by_lane["core"])
    assert p.weight_by_lane["deep"] == pytest.approx(before.weight_by_lane["deep"])


# ---------------------------------------------------------------------------
# (4) disabled lanes stay disabled
# ---------------------------------------------------------------------------

def test_disabled_deep_lane_stays_disabled(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    p = _plan(retrieve_deep=False)  # deep weight 0.0, retrieve_deep False
    before = copy.deepcopy(p)
    ctl._apply_geometric_memory_shaping_v1(
        p, _state(deep_context_eligible=False), _geo(0.95, 0.95)
    )
    assert p.weight_by_lane["deep"] == 0.0   # never enabled
    assert p.retrieve_deep is False
    # the enabled core lane still shaped
    assert p.weight_by_lane["core"] > before.weight_by_lane["core"]


# ---------------------------------------------------------------------------
# (5) governance / identity turns are skipped entirely
# ---------------------------------------------------------------------------

def test_governance_sensitive_skips_shaping(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    p = _plan(core=1.0, deep=0.60)
    before = copy.deepcopy(p)
    ctl._apply_geometric_memory_shaping_v1(
        p, _state(governance_sensitive=True), _geo(0.95, 0.95)
    )
    assert p.to_dict() == before.to_dict()


def test_identity_sensitive_skips_shaping(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    p = _plan(core=1.0, deep=0.60)
    before = copy.deepcopy(p)
    ctl._apply_geometric_memory_shaping_v1(
        p, _state(identity_sensitive=True), _geo(0.95, 0.95)
    )
    assert p.to_dict() == before.to_dict()


# ---------------------------------------------------------------------------
# (6) think() exposes the shaped plan in the ThinkingResult
# ---------------------------------------------------------------------------

def test_think_exposes_shaped_memory_plan(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    ctl = ThinkingController()
    text = "what do you recall about the calm water this afternoon"
    r_geo = ctl.think("ws", "ag", text, geometric_context=_geo(0.95, 0.95))
    r_none = ctl.think("ws", "ag", text, geometric_context=None)
    # guard: the chosen input must not be a governance/identity turn (would skip)
    assert not r_geo.task_frame.governance_sensitive
    assert not r_geo.task_frame.identity_sensitive
    cw_geo = r_geo.memory_plan.weight_by_lane["core"]
    cw_none = r_none.memory_plan.weight_by_lane["core"]
    assert cw_geo != cw_none
    assert cw_geo == pytest.approx(cw_none * _expected_mult(0.95, 0.95))
    # serialized into the result dict that becomes the advisory audit payload
    assert r_geo.to_dict()["memory_plan"]["weight_by_lane"]["core"] == pytest.approx(cw_geo)


# ---------------------------------------------------------------------------
# (7) live Spine advisory proof — the plan the agent actually used is a
#     deterministic function of the live kernel geometric_context.
# ---------------------------------------------------------------------------

def test_spine_advisory_memory_plan_is_geometrically_shaped(tmp_path, monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    monkeypatch.setenv("TORMENT_THINKING_ADVISORY", "1")
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")

    from torment_service.request_context import (
        RequestContext, TRUST_INGEST, TRUST_READ_ONLY,
    )
    from torment_service.spine import SpineRequest, submit_task, _THINKING_ADVISORY_ENABLE
    from torment_service.fabric import TormentFabric

    if not _THINKING_ADVISORY_ENABLE:
        pytest.skip("advisory thinking disabled at spine import time")

    fabric = TormentFabric(data_dir=str(tmp_path))
    fabric.get_workspace("ws")
    fabric.create_agent("ws", "ag")

    ictx = RequestContext(client_id="t", trust_tier=TRUST_INGEST,
                          workspace_id="ws", agent_id="ag")
    submit_task(SpineRequest(workspace_id="ws", agent_id="ag", operation="ingest",
                             payload={"text": "a calm afternoon by the water"}),
                fabric, ictx)

    qctx = RequestContext(client_id="v", trust_tier=TRUST_READ_ONLY,
                          workspace_id="ws", agent_id="ag")
    resp = submit_task(SpineRequest(workspace_id="ws", agent_id="ag",
                                    operation="query_memory",
                                    payload={"query": "what do you recall about the water",
                                             "top_k": 3}),
                       fabric, qctx)
    assert resp.ok, resp.reason

    advisory = resp.audit.get("advisory_thinking")
    assert advisory is not None, "advisory_thinking missing from audit"

    # This is a *proof of shaping* — it must NOT pass on a fallback. Require a
    # real live geometric_context on a non-governance, non-identity turn.
    geo = advisory.get("geometric_context")
    assert geo is not None, "live geometric_context was None — cannot prove shaping"
    tf = advisory.get("task_frame", {})
    assert not tf.get("governance_sensitive"), "query unexpectedly governance-sensitive (would skip shaping)"
    assert not tf.get("identity_sensitive"), "query unexpectedly identity-sensitive (would skip shaping)"

    mp = advisory.get("memory_plan")
    assert mp is not None and "weight_by_lane" in mp
    core_w = mp["weight_by_lane"]["core"]

    coherence = float(geo["coherence"])
    stability = float(geo["stability"])
    settled = max(0.0, min(1.0, 0.5 * (coherence + stability)))
    mult = _expected_mult(coherence, stability)
    expected = max(0.1, min(2.0, 1.0 * mult))  # base core weight is 1.0

    # Base/unshaped (== 1.0) is NOT an acceptable pass for the live proof.
    assert core_w != pytest.approx(1.0), (
        f"core weight not shaped by live geometry "
        f"(settled={settled}, coherence={coherence}, stability={stability})"
    )
    # Shaped value matches the deterministic function of the live geometry...
    assert core_w == pytest.approx(expected)
    # ...and moved in the multiplier's direction.
    if settled > 0.5:
        assert core_w > 1.0
    else:
        assert core_w < 1.0


# ---------------------------------------------------------------------------
# (8) capstone — the shaped plan actually moves fabric.query ranking pressure,
#     not just the advisory audit. geo → shaped weight_by_lane["core"] →
#     memory_plan into fabric.query → core hit final_score is multiplied while
#     the (untouched) relational lane is unchanged → core-vs-relational ranking
#     pressure shifts. Deterministic via score *ratios* (no order-flip, no
#     dependence on absolute embedding similarity).
# ---------------------------------------------------------------------------

def test_geometric_shaping_changes_query_ranking_pressure(tmp_path, monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")

    from torment_service.fabric import TormentFabric

    # One fabric, core(private) + relational(shared) memory. "remember"/"we"
    # set memory_need (-> relational lane enabled); no identity/governance words,
    # so geometric shaping is NOT skipped on this turn. query() is a pure read
    # for this path (SRG off), so querying the same fabric twice is fine.
    fabric = TormentFabric(data_dir=str(tmp_path))
    fabric.get_workspace("ws")
    fabric.create_agent("ws", "ag")
    fabric.ingest(workspace_id="ws", agent_id="ag",
                  text="my private routine notes about the water survey", step=10)
    fabric.ingest(workspace_id="ws", agent_id="ag",
                  text="our shared project notes about the water survey", step=11, scope="shared")

    query_text = "what do we remember about the water survey notes"
    ctl = ThinkingController()
    frame = ctl.frame_task("ws", "ag", query_text)
    mode = ctl.choose_mode(frame)
    assert not frame.governance_sensitive and not frame.identity_sensitive

    plan_base = ctl.build_memory_plan(frame, mode)  # geo None -> core weight 1.0
    plan_shaped = ctl.build_memory_plan(frame, mode, geometric_context=_geo(0.95, 0.95))

    # geometric origin: shaping raised core weight, left relational untouched.
    base_core_w = plan_base.weight_by_lane["core"]
    shaped_core_w = plan_shaped.weight_by_lane["core"]
    assert shaped_core_w > base_core_w
    assert plan_shaped.weight_by_lane.get("relational") == plan_base.weight_by_lane.get("relational")
    # relational lane must actually be enabled, or the proof has no control hit.
    assert plan_base.retrieve_relational, "relational lane disabled - query won't return the shared hit"

    def _mp(plan):
        return {"top_k_by_lane": plan.top_k_by_lane, "weight_by_lane": plan.weight_by_lane}

    def _scores_by_scope(query_result):
        # COLLISION-SAFE keying. The private and shared stores have INDEPENDENT
        # eid spaces, so the private/core hit and the shared/relational hit both
        # come back as eid=1. Keying results by bare eid silently overwrites the
        # private score with the shared one (which made shaping look like a
        # no-op in an earlier draft of this test). Key by scope/lane instead.
        scores = {}
        for h in query_result.get("results", []):
            scores[h.get("scope")] = h["final_score"]
        return scores

    base = _scores_by_scope(fabric.query(
        workspace_id="ws", agent_id="ag", query_text=query_text,
        top_k=20, memory_plan=_mp(plan_base)))
    shaped = _scores_by_scope(fabric.query(
        workspace_id="ws", agent_id="ag", query_text=query_text,
        top_k=20, memory_plan=_mp(plan_shaped)))

    assert "private" in base and "private" in shaped, "private/core hit missing from query results"
    assert "shared" in base and "shared" in shaped, "shared/relational hit missing from query results"

    ratio = shaped_core_w / base_core_w  # the geometric multiplier (~1.135)

    # core (private) hit: final_score scaled by exactly the geometric core-weight
    # ratio. relational (shared) lane is untouched, so its score is the built-in
    # determinism guard for the two same-fabric reads.
    assert shaped["private"] == pytest.approx(base["private"] * ratio, rel=1e-3)
    assert shaped["private"] != pytest.approx(base["private"], rel=1e-3)
    assert shaped["shared"] == pytest.approx(base["shared"], rel=1e-3)

    # ranking pressure: core-vs-relational gap shifted toward core under shaping.
    assert (shaped["private"] / shaped["shared"]) > (base["private"] / base["shared"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
