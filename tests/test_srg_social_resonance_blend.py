"""tests/test_srg_social_resonance_blend.py — SRG Slice B.

Slice B lets ``geometric_harvester.harvest_geometric_context`` blend the
agent-level SRG relational signal into ``social_resonance`` when present.
Contract:
  * ``srg_relational is None`` ⇒ exact prior behavior (blend skipped).
  * ``srg_relational`` present ⇒ social_resonance shifts *toward* the signal,
    by a small weight (informs, never dominates), output bounded 0.0–1.0.
  * ``spine._harvest_geometric_context`` fetches the signal via the existing
    fabric getter and passes it through (defensive: any error ⇒ None ⇒ unchanged).
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.geometric_harvester import harvest_geometric_context
from torment_service.spine import _harvest_geometric_context

# A tri_mod that drives the social_resonance composite (kernel present).
_TRI = {"coh_phase": 0.85, "tearing_risk": 0.35, "survival_steps": 1.0}


def _sr(srg):
    ctx = harvest_geometric_context(tri_mod=dict(_TRI), srg_relational=srg)
    assert ctx is not None
    return ctx.social_resonance


# ---------------------------------------------------------------------------
# harvester blend
# ---------------------------------------------------------------------------

def test_none_signal_reproduces_prior_behavior():
    base = _sr(None)
    # Omitting the param entirely == passing None (default), i.e. blend skipped.
    omitted = harvest_geometric_context(tri_mod=dict(_TRI))
    assert omitted.social_resonance == base
    assert 0.0 <= base <= 1.0


def test_high_signal_raises_social_resonance_bounded():
    base = _sr(None)
    high = _sr(0.9)
    assert high > base                 # moved toward the (higher) signal
    assert 0.0 <= high <= 1.0


def test_low_signal_lowers_social_resonance_bounded():
    base = _sr(None)
    low = _sr(0.0)
    assert low < base                  # moved toward the (lower) signal
    assert 0.0 <= low <= 1.0


def test_out_of_range_signal_is_clamped_and_bounded():
    assert 0.0 <= _sr(5.0) <= 1.0      # input clamped to 1.0
    assert 0.0 <= _sr(-3.0) <= 1.0     # input clamped to 0.0


def test_blend_informs_not_dominates():
    base = _sr(None)
    high = _sr(1.0)
    # 15% blend: the shift toward a maxed signal is small vs the available gap.
    gap = 1.0 - base
    shift = high - base
    assert 0.0 < shift < 0.5 * gap


# ---------------------------------------------------------------------------
# spine seam
# ---------------------------------------------------------------------------

class _Mon:
    coh_ema = 0.85
    tear_score_ema = 0.35
    surv_ema = 1.0


class _Ctx:
    mon = _Mon()


class _FakeFabric:
    def __init__(self, srg):
        self._srg = srg

    def get_kernel_runtime_context(self, ws, ag):
        return _Ctx()

    def get_srg_relational_signal(self, ws, ag):
        return self._srg
    # No character_store attribute -> char_state stays None; tri_mod drives harvest.


def _direct_none():
    return harvest_geometric_context(
        tri_mod={"coh_phase": 0.85, "tearing_risk": 0.35, "survival_steps": 1.0},
        srg_relational=None,
    ).social_resonance


def test_spine_passes_srg_signal_through():
    with_sig = _harvest_geometric_context(_FakeFabric(0.95), "ws", "ag")
    without = _harvest_geometric_context(_FakeFabric(None), "ws", "ag")
    assert with_sig is not None and without is not None
    assert with_sig.social_resonance != without.social_resonance
    assert with_sig.social_resonance > without.social_resonance  # 0.95 > base
    assert 0.0 <= with_sig.social_resonance <= 1.0


def test_spine_none_signal_matches_no_signal_path():
    ctx = _harvest_geometric_context(_FakeFabric(None), "ws", "ag")
    assert ctx is not None
    assert ctx.social_resonance == _direct_none()


def test_spine_getter_exception_falls_back_to_none():
    class _BadFabric(_FakeFabric):
        def get_srg_relational_signal(self, ws, ag):
            raise RuntimeError("boom")

    ctx = _harvest_geometric_context(_BadFabric(None), "ws", "ag")
    assert ctx is not None
    assert ctx.social_resonance == _direct_none()  # defensive fallback, no crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
