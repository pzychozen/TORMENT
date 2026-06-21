"""tests/test_participation_guidance_v1.py — participation guidance v1.

Visible advisory only. A pure mapper turns (TaskFrame, optional stance) into one
``participation_guidance`` candidate surfaced ONLY on ``ThinkingResult.to_dict()``
and the Spine ``audit["advisory_thinking"]`` when ``TORMENT_PARTICIPATION_GUIDANCE_V1``
is on. It is never on ``/agent/query``, never a response-control field, and never
suppresses / vetoes / empties a response or touches dispatch / review.blocked /
authority / memory. See docs/TORMENT_PARTICIPATION_GUIDANCE_FRAME_v0.1.md.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service import thinking_controller as tc
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import (
    TaskFrame,
    ResponseStance,
    ResponseStanceDecision,
    map_participation_guidance,
)

_FLAG = "_PARTICIPATION_GUIDANCE_V1_ENABLE"
_VALUES = {"none", "respond_briefly_candidate", "defer_candidate", "silent_observe_candidate"}


def _frame(**over) -> TaskFrame:
    base = dict(workspace_id="ws", agent_id="ag", raw_input="hello", normalized_input="hello")
    base.update(over)
    return TaskFrame(**base)


def _stance(s) -> ResponseStanceDecision:
    return ResponseStanceDecision(stance=s, reason="t")


# --- mapper whitelist / skip rules (3, 4, 5) --------------------------------

def test_mapper_whitelist():
    f = _frame()
    assert map_participation_guidance(f, _stance(ResponseStance.RESPOND_BRIEFLY)) == "respond_briefly_candidate"
    assert map_participation_guidance(f, _stance(ResponseStance.DEFER)) == "defer_candidate"
    assert map_participation_guidance(f, _stance(ResponseStance.SILENT_OBSERVE)) == "silent_observe_candidate"


def test_mapper_non_whitelisted_stance_is_none():
    f = _frame()
    for s in (ResponseStance.RESPOND_NOW, ResponseStance.ASK_CLARIFICATION, ResponseStance.ABSTAIN,
              ResponseStance.REQUEST_TURN, ResponseStance.GOVERNED_REDIRECT, ResponseStance.TOOL_REDIRECT):
        assert map_participation_guidance(f, _stance(s)) == "none"


def test_mapper_missing_stance_is_none():
    assert map_participation_guidance(_frame(), None) == "none"


def test_mapper_non_ordinary_turns_are_none():
    d = _stance(ResponseStance.DEFER)
    # any non-user_text source (operator / system / reflex-like)
    for st in ("reflex", "operator", "system", "tool_result", "not_user_text"):
        assert map_participation_guidance(_frame(source_type=st), d) == "none"
    # governance- / identity-sensitive turns
    assert map_participation_guidance(_frame(governance_sensitive=True), d) == "none"
    assert map_participation_guidance(_frame(identity_sensitive=True), d) == "none"


# --- flag gating on ThinkingResult.to_dict (1, 2) ---------------------------

def test_flag_off_omits_field(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, False)
    r = ThinkingController().think("ws", "ag", "tell me about the lake")
    assert "participation_guidance" not in r.to_dict()


def test_flag_on_includes_field(monkeypatch):
    monkeypatch.setattr(tc, _FLAG, True)
    r = ThinkingController().think("ws", "ag", "tell me about the lake")
    d = r.to_dict()
    assert "participation_guidance" in d
    assert d["participation_guidance"] in _VALUES
    # default capabilities → contextual_abstention off → stance None → "none".
    assert d["participation_guidance"] == "none"


# --- Spine advisory audit surface (6, 7, 9) ---------------------------------

def _fresh_fabric(data_dir, monkeypatch):
    monkeypatch.setenv("TORMENT_THINKING_ADVISORY", "1")
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    from torment_service.fabric import TormentFabric
    os.makedirs(str(data_dir), exist_ok=True)
    fab = TormentFabric(data_dir=str(data_dir))
    fab.get_workspace("ws")
    fab.create_agent("ws", "ag")
    return fab


def _spine_query(fabric):
    from torment_service.request_context import RequestContext, TRUST_READ_ONLY
    from torment_service.spine import SpineRequest, submit_task
    ctx = RequestContext(client_id="v", trust_tier=TRUST_READ_ONLY, workspace_id="ws", agent_id="ag")
    req = SpineRequest(workspace_id="ws", agent_id="ag", operation="query_memory",
                       payload={"query": "what do you recall about the lake", "top_k": 3})
    return submit_task(req, fabric, ctx)


def test_spine_field_only_in_advisory_audit_not_top_level(tmp_path, monkeypatch):
    from torment_service.spine import _THINKING_ADVISORY_ENABLE
    if not _THINKING_ADVISORY_ENABLE:
        pytest.skip("advisory thinking disabled at import")
    monkeypatch.setattr(tc, _FLAG, True)
    fab = _fresh_fabric(tmp_path, monkeypatch)
    resp = _spine_query(fab)
    assert resp.ok
    at = resp.audit.get("advisory_thinking")
    assert at is not None
    assert "participation_guidance" in at
    assert at["participation_guidance"] in _VALUES
    # NOT a top-level response-control field on the Spine envelope.
    assert "participation_guidance" not in resp.to_dict()
    # response not suppressed; envelope normal (9).
    assert resp.allowed and resp.result is not None


def test_spine_envelope_unchanged_by_flag(tmp_path, monkeypatch):
    from torment_service.spine import _THINKING_ADVISORY_ENABLE
    if not _THINKING_ADVISORY_ENABLE:
        pytest.skip("advisory thinking disabled at import")
    monkeypatch.setattr(tc, _FLAG, False)
    r_off = _spine_query(_fresh_fabric(tmp_path / "off", monkeypatch))
    monkeypatch.setattr(tc, _FLAG, True)
    r_on = _spine_query(_fresh_fabric(tmp_path / "on", monkeypatch))
    # ok / allowed / path / result_code unchanged (7).
    assert (r_off.ok, r_off.allowed, r_off.path, r_off.result_code) == \
           (r_on.ok, r_on.allowed, r_on.path, r_on.result_code)
    # field present only under the flag (1/2 at the spine surface).
    assert "participation_guidance" not in (r_off.audit.get("advisory_thinking") or {})
    assert "participation_guidance" in (r_on.audit.get("advisory_thinking") or {})


# --- structural guard: not wired into dispatch / suppression (8, 9, 10) -----

def test_field_not_wired_into_dispatch_or_query_or_loop():
    """participation_guidance must not be referenced by /agent/query, the Spine
    dispatch, or agent_loop — proving no output-control / suppression / memory
    wiring and no /agent/query exposure. It flows only through to_dict()."""
    import torment_service
    base = os.path.dirname(torment_service.__file__)
    for fname in ("agent_loop.py", "spine.py", "app.py"):
        with open(os.path.join(base, fname), encoding="utf-8") as fh:
            src = fh.read()
        assert "participation_guidance" not in src, (
            f"{fname} must not reference participation_guidance"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
