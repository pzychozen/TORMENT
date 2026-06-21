"""tests/test_srg_social_resonance_chain.py — SRG live-chain integration.

Proves the *already-shipped* SRG->social_resonance capability (Slices A+B)
reaches the real Spine advisory surface end-to-end:

    SRG-on ingest  -> per-agent L_amplitude EMA            (fabric.ingest, Slice A)
      -> later Spine query turn harvests geometric context (spine._harvest_geometric_context)
        -> social_resonance blended toward the live signal (geometric_harvester, Slice B)
          -> advisory audit exposes the shifted geometric context
             (submit_task -> audit["advisory_thinking"]["geometric_context"]["social_resonance"])

This is a *test-only* proof. No production code is changed. It asserts on the
advisory geometric_context, NOT on stance flips (which depend on thresholds,
token counts and live-social wording and would be brittle).

Ordering note (load-bearing): ``submit_task`` harvests geometric context BEFORE
dispatch, while the SRG EMA is updated INSIDE ``fabric.ingest`` DURING dispatch.
So an ingest turn seeds the signal and the *next* turn observes it — which is
exactly the chain proven here.
"""
from __future__ import annotations

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.request_context import (
    RequestContext,
    TRUST_INGEST,
    TRUST_READ_ONLY,
)
from torment_service.spine import (
    SpineRequest,
    submit_task,
    _THINKING_ADVISORY_ENABLE,
)
from torment_service.fabric import TormentFabric

WS = "ws"
AGENT = "agent"

# Relational, distinct texts -> a non-trivial per-memory L_amplitude EMA.
_INGEST_TEXTS = [
    "a long letter to a friend across the sea",
    "the crowded warmth of a shared dinner table",
    "the quiet ache of an old, unkept promise",
    "laughter between two people on a winter street",
]
_QUERY_TEXT = "what do these shared moments mean to us"

# Skip cleanly if advisory thinking is off at import (module-level constant).
_ADVISORY = pytest.mark.skipif(
    not _THINKING_ADVISORY_ENABLE,
    reason="advisory thinking disabled at spine import time",
)


def _build_fabric(data_dir, monkeypatch, *, srg_on):
    # _srg_enable is captured in TormentFabric.__init__, so set env BEFORE construct.
    os.makedirs(data_dir, exist_ok=True)
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "1" if srg_on else "0")
    monkeypatch.setenv("TORMENT_THINKING_ADVISORY", "1")
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    fabric = TormentFabric(data_dir=str(data_dir))
    fabric.get_workspace(WS)
    fabric.create_agent(WS, AGENT)
    return fabric


def _ingest_all(fabric):
    ctx = RequestContext(client_id="t", trust_tier=TRUST_INGEST,
                         workspace_id=WS, agent_id=AGENT)
    for text in _INGEST_TEXTS:
        req = SpineRequest(workspace_id=WS, agent_id=AGENT,
                           operation="ingest", payload={"text": text})
        resp = submit_task(req, fabric, ctx)
        assert resp.ok, f"ingest failed: {resp.reason}"


def _query_social_resonance(fabric):
    """Run a read-only query turn and pull social_resonance off the advisory audit."""
    ctx = RequestContext(client_id="v", trust_tier=TRUST_READ_ONLY,
                         workspace_id=WS, agent_id=AGENT)
    req = SpineRequest(workspace_id=WS, agent_id=AGENT,
                       operation="query_memory",
                       payload={"query": _QUERY_TEXT, "top_k": 3})
    resp = submit_task(req, fabric, ctx)
    assert resp.ok, f"query failed: {resp.reason}"
    advisory = resp.audit.get("advisory_thinking")
    assert advisory is not None, "advisory_thinking missing from audit"
    geo = advisory.get("geometric_context")
    assert geo is not None, "geometric_context missing from advisory_thinking"
    sr = geo.get("social_resonance")
    assert isinstance(sr, (int, float)) and math.isfinite(sr), f"bad social_resonance: {sr!r}"
    assert 0.0 <= sr <= 1.0
    return float(sr)


@_ADVISORY
def test_srg_signal_shifts_advisory_social_resonance(tmp_path, monkeypatch):
    """The live SRG signal reaches advisory geometric_context.social_resonance.

    SRG-on vs SRG-off differ ONLY in the relational EMA (same texts, same hash
    embedder => identical kernel evolution / base social_resonance), so any
    difference in the advisory social_resonance isolates the SRG blend.
    """
    on = _build_fabric(tmp_path / "on", monkeypatch, srg_on=True)
    _ingest_all(on)
    signal = on.get_srg_relational_signal(WS, AGENT)
    assert isinstance(signal, float), "SRG-on must seed a relational signal after ingest"
    sr_on = _query_social_resonance(on)

    off = _build_fabric(tmp_path / "off", monkeypatch, srg_on=False)
    _ingest_all(off)
    assert off.get_srg_relational_signal(WS, AGENT) is None, "SRG-off must never seed a signal"
    sr_off = _query_social_resonance(off)

    # 1) The live signal moved social_resonance off its SRG-free baseline.
    assert sr_on != sr_off, (
        f"SRG signal did not reach the advisory surface: "
        f"sr_on={sr_on} sr_off={sr_off} signal={signal}"
    )

    # 2) The shift is *toward* the clamped signal and *informs, never dominates*
    #    (|shift| < |gap|). Formula-agnostic: does not hardcode the 0.15 weight.
    sig_c = max(0.0, min(1.0, signal))
    assert (sr_on - sr_off) * (sig_c - sr_off) > 0, (
        f"social_resonance shifted away from the SRG signal: "
        f"sr_on={sr_on} sr_off={sr_off} sig_c={sig_c}"
    )
    assert abs(sr_on - sr_off) < abs(sig_c - sr_off) + 1e-9, (
        f"SRG blend dominated instead of informed: "
        f"sr_on={sr_on} sr_off={sr_off} sig_c={sig_c}"
    )


@_ADVISORY
def test_ingest_seeds_then_query_observes_ordering(tmp_path, monkeypatch):
    """Ordering proof: no signal before ingest; signal present after ingest; the
    later query turn (which harvests *after* the ingest turns) surfaces a bounded
    social_resonance on the advisory audit."""
    fabric = _build_fabric(tmp_path / "order", monkeypatch, srg_on=True)
    assert fabric.get_srg_relational_signal(WS, AGENT) is None  # nothing ingested yet
    _ingest_all(fabric)
    assert isinstance(fabric.get_srg_relational_signal(WS, AGENT), float)  # seeded by ingest
    sr = _query_social_resonance(fabric)  # a later turn observes it
    assert 0.0 <= sr <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
