"""tests/test_srg_relational_signal.py — SRG Slice A: agent-level relational EMA.

Slice A creates a per-agent, in-memory, advisory EMA of each ingested memory's
SRG ``L_amplitude`` (the breathing amplitude of the L / "who the memory is to"
field). Default-off (``TORMENT_SRG_ENABLE``). No persistence, no authority, no
API exposure, and no consumer wired yet — these tests lock the primitive only.
"""
from __future__ import annotations

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.srg_engine import SRGMemoryState, relational_amplitude
from torment_service.fabric import TormentFabric


def _fabric(tmp_path, monkeypatch, *, srg_on):
    # _srg_enable is read in TormentFabric.__init__, so set env BEFORE construct.
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "1" if srg_on else "0")
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    fabric = TormentFabric(data_dir=str(tmp_path))
    fabric.get_workspace("ws")
    fabric.create_agent("ws", "agent")
    return fabric


# ---------------------------------------------------------------------------
# helper unit
# ---------------------------------------------------------------------------

def test_relational_amplitude_returns_l_amplitude():
    assert relational_amplitude(SRGMemoryState(L_amplitude=0.42)) == pytest.approx(0.42)
    assert relational_amplitude(SRGMemoryState()) == 0.0  # default L_amplitude


# ---------------------------------------------------------------------------
# getter / cache behavior
# ---------------------------------------------------------------------------

def test_getter_none_when_srg_disabled(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, srg_on=False)
    fabric.ingest(workspace_id="ws", agent_id="agent", text="a quiet memory", step=1)
    assert fabric.get_srg_relational_signal("ws", "agent") is None


def test_getter_none_before_any_ingest(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, srg_on=True)
    assert fabric.get_srg_relational_signal("ws", "agent") is None


def test_getter_returns_finite_float_after_ingest(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, srg_on=True)
    fabric.ingest(workspace_id="ws", agent_id="agent", text="a memory about the sea", step=1)
    sig = fabric.get_srg_relational_signal("ws", "agent")
    assert isinstance(sig, float)
    assert math.isfinite(sig)


def test_ema_moves_across_distinct_ingests(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, srg_on=True)
    seen = []
    for i, text in enumerate([
        "a memory about the sea and the waves",
        "thoughts on a crowded city street at night",
        "the quiet weight of an old, unkept promise",
        "laughter shared across a long wooden table",
    ]):
        fabric.ingest(workspace_id="ws", agent_id="agent", text=text, step=i + 1)
        seen.append(fabric.get_srg_relational_signal("ws", "agent"))
    assert all(isinstance(s, float) for s in seen)
    # Distinct per-memory amplitudes blend through the EMA, so it must move.
    assert len(set(seen)) > 1


def test_per_agent_isolation(tmp_path, monkeypatch):
    fabric = _fabric(tmp_path, monkeypatch, srg_on=True)
    fabric.create_agent("ws", "other")

    fabric.ingest(workspace_id="ws", agent_id="agent", text="agent remembers a storm", step=1)
    # Only 'agent' ingested; 'other' must stay None (no key bleed).
    assert isinstance(fabric.get_srg_relational_signal("ws", "agent"), float)
    assert fabric.get_srg_relational_signal("ws", "other") is None

    agent_before = fabric.get_srg_relational_signal("ws", "agent")
    fabric.ingest(workspace_id="ws", agent_id="other", text="other recalls a melody", step=1)
    assert isinstance(fabric.get_srg_relational_signal("ws", "other"), float)
    # 'agent' value is independent of the 'other' ingest.
    assert fabric.get_srg_relational_signal("ws", "agent") == agent_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
