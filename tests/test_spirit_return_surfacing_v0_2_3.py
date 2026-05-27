"""
tests/test_spirit_return_surfacing_v0_2_3.py — Memory-to-Prompt v0.2.3.

Spirit-return / voice-cue surfacing verification at the `/retrieve` API
boundary.

v0.2.3 proves what v0.2.2's surfacing layer + the existing
retrieval_assembler voice-cue logic + the existing
character.spirit_return_summary production all do *together* at the
`/retrieve` API surface. No production code change. No assembled_text
mutation. No new endpoint. No real Ryuki dependency. Mock at
`fabric.query()` return shape (Option (i) per v0.2.3 trio
ratification); the real `assemble_context()` and the v0.2.2 surfacing
layer run for real.

Three tests, one per gap closed:
    A. `/retrieve` surfaces `character_context.spirit_return_summary`
       with the shipping `{total, by_mode, avg_warmth}` shape when
       `fabric.query` returns one. (v0.2.2 proved the absence case;
       v0.2.3 proves the presence case.)
    B. `/retrieve` preserves the existing `[Returning Memory]`,
       `[Voice:]`, `[Flavor:]` markers in `assembled_text` when
       spirit-return hits are in the mocked `fabric.query` results.
       Verification only — v0.2.2 did not change `assembled_text`
       production; this asserts that what was already produced
       reaches the API.
    C. `by_mode` breakdown keys are within the documented set
       `{resonance, surfacing, recollection}`.

Hard non-goals (carried from v0.2.3 ratification, see
`docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_2_CHARACTER_CONTEXT.md`
and the v0.2 lane doctrine at
`docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md`):
    - no production code change
    - no `assembled_text` format change
    - no `/agent/query` wiring (Option A surfacing remains
      `/retrieve`-only)
    - no archive-FILTER-A change
    - no real Ryuki/live workspace dependency
    - no new endpoint, env var, or tool family
    - no consistency check between
      `character_context.spirit_return_summary` and
      `assembly_audit.spirit_return_summary` (parked as Gap C from
      v0.2.3 audit — separately ratifiable)
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixture — isolated app instance with temp DATA_DIR
# ---------------------------------------------------------------------------

@pytest.fixture()
def appmod(tmp_path):
    """Reloaded `torment_service.app` module pointing at a temp data dir.

    Manual env save/restore + post-yield reload — not monkeypatch.
    Same Pattern A shape as `tests/test_character_context_surfacing.py`,
    `tests/test_smoke_api.py`, and `tests/test_assembly_audit_wiring.py`
    after the 2026-05-27 test-isolation gate. See those fixtures'
    docstrings for the full why-not-monkeypatch reasoning. Yielding
    `appmod` (rather than a `TestClient`) so tests can `patch.object`
    on `appmod.fabric.query` before constructing the `TestClient`.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    original_env = os.environ.get("TORMENT_DATA_DIR")
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)

    import torment_service.app as _appmod
    _appmod = importlib.reload(_appmod)
    try:
        yield _appmod
    finally:
        if original_env is None:
            os.environ.pop("TORMENT_DATA_DIR", None)
        else:
            os.environ["TORMENT_DATA_DIR"] = original_env
        importlib.reload(_appmod)


# ---------------------------------------------------------------------------
# Synthetic fixture builders
# ---------------------------------------------------------------------------

def _retrieve_payload(
    workspace: str = "ws_v0_2_3",
    agent: str = "ag_v0_2_3",
) -> Dict[str, Any]:
    return {
        "workspace_id": workspace,
        "agent_id": agent,
        "query": "What did we talk about?",
        "profile": "companion",
        "token_budget": 1500,
        "top_k": 5,
    }


def _make_character_context_with_spirit_summary(
    *,
    total: int = 3,
    by_mode: Dict[str, int] = None,
    avg_warmth: float = 0.45,
) -> Dict[str, Any]:
    """Build a synthetic character_context with a spirit_return_summary
    sub-dict matching the shipping shape from
    `torment_service.character.assemble_character_context` (see
    character.py:932-961). The shipping shape is
    `{total, by_mode, avg_warmth}` — `recommendations` is a separate
    top-level field of character_context, NOT inside
    spirit_return_summary.
    """
    if by_mode is None:
        by_mode = {"resonance": 1, "surfacing": 1, "recollection": 1}
    return {
        "seed_preamble": "TestCharacter is calm and curious.",
        "seed_id": "test_v0_2_3",
        "character_name": "TestCharacter",
        "tier_breakdown": {
            "core_identity": 0,
            "derived_identity": 0,
            "relational": 0,
            "situational": 0,
        },
        "drift_score": 0.0,
        "drift_summary": "",
        "drift_direction": "stable",
        "seed_basin_role": "anchor",
        "relational_count": 0,
        "recommendations": [],
        "spirit_return_summary": {
            "total": total,
            "by_mode": dict(by_mode),
            "avg_warmth": avg_warmth,
        },
    }


def _make_spirit_hit(
    eid: int = 42,
    mode: str = "resonance",
    warmth: float = 0.7,
    summary: str = "we talked about the stars",
    flavor: str = "vivid déjà vu of an earlier conversation",
) -> Dict[str, Any]:
    """Build a synthetic spirit-return hit matching the shape that
    `torment_service.retrieval_assembler._classify_core_hit` /
    `_hit_to_block` read (see retrieval_assembler.py:167-280)."""
    return {
        "eid": eid,
        "score": 0.5,
        "final_score": 0.5,
        "summary": summary,
        "type": "memory",
        "strength": 0.3,
        "confidence": 0.7,
        "step": 100,
        "memory_class": "core",
        "from_deep_memory": True,
        "from_spirit_return": True,
        "spirit_return_mode": mode,
        "spirit_return_flavor": flavor,
        "birth_symbol": "✧",
        "current_kernel_symbol": "✧",
        "symbol_interaction": "echo",
        "warmth_score": warmth,
        "resonance_confidence": 0.8,
    }


def _make_core_result(
    *,
    results=None,
    character_context=None,
) -> Dict[str, Any]:
    """Build a synthetic `fabric.query()` return dict with the minimum
    keys the `/retrieve` handler reads. Other keys (filter_excluded,
    excluded, _core_hits_in_count, _authority_guard_rejected) are
    consumed by the v0.2 assembly_audit path when `include_assembly_audit`
    is True; default-False in v0.2.3 tests so they are not load-bearing
    but are included for shape-correctness.
    """
    return {
        "results": list(results or []),
        "character_context": character_context,
        "filter_excluded": [],
        "excluded": [],
        "_core_hits_in_count": len(results or []),
        "_authority_guard_rejected": 0,
    }


# ===========================================================================
# Test A — positive /retrieve surfacing of spirit_return_summary
# ===========================================================================

class TestRetrieveSpiritReturnSummary:
    """v0.2.3 §A — `/retrieve` surfaces
    `character_context.spirit_return_summary` with the shipping
    `{total, by_mode, avg_warmth}` shape and matching values when
    `fabric.query` produces one. Closes the v0.2.2 gap: only the
    absence case was proven at the API level.
    """

    def test_spirit_return_summary_surfaced_with_shipping_shape(self, appmod):
        char_ctx = _make_character_context_with_spirit_summary(
            total=3,
            by_mode={"resonance": 1, "surfacing": 1, "recollection": 1},
            avg_warmth=0.45,
        )
        core_result = _make_core_result(character_context=char_ctx)
        with patch.object(appmod.fabric, "query", return_value=core_result):
            tc = TestClient(appmod.app)
            r = tc.post("/retrieve", json=_retrieve_payload())
        assert r.status_code == 200, r.text
        body = r.json()
        # Surfacing path landed character_context.spirit_return_summary
        # on the response.
        assert "character_context" in body
        assert "spirit_return_summary" in body["character_context"]
        srs = body["character_context"]["spirit_return_summary"]
        # Shape is exactly the shipping {total, by_mode, avg_warmth} —
        # nothing else leaks through.
        assert set(srs.keys()) == {"total", "by_mode", "avg_warmth"}
        # Values match the mocked input verbatim.
        assert srs["total"] == 3
        assert srs["by_mode"] == {
            "resonance": 1, "surfacing": 1, "recollection": 1,
        }
        assert srs["avg_warmth"] == pytest.approx(0.45)


# ===========================================================================
# Test B — voice cues preserved through /retrieve under spirit-return
# ===========================================================================

class TestRetrieveAssembledTextVoiceCues:
    """v0.2.3 §B — `/retrieve`'s `assembled_text` preserves the
    existing `[Returning Memory]`, `[Voice:]`, `[Flavor:]` markers
    when `fabric.query` returns spirit-return hits. Verification only;
    v0.2.2 did not change `assembled_text` production and v0.2.3
    does not either. Existing unit tests in
    `tests/test_spirit_return_voice.py` prove the markers are produced
    by `retrieval_assembler` directly; this test proves they reach
    the API surface.
    """

    def test_voice_markers_in_assembled_text_under_spirit_return(self, appmod):
        hit = _make_spirit_hit(
            mode="surfacing",
            warmth=0.4,
            summary="we talked about the stars",
            flavor="gentle return of an old thread",
        )
        core_result = _make_core_result(results=[hit], character_context=None)
        with patch.object(appmod.fabric, "query", return_value=core_result):
            tc = TestClient(appmod.app)
            r = tc.post("/retrieve", json=_retrieve_payload())
        assert r.status_code == 200, r.text
        text = r.json().get("assembled_text", "")
        # All three markers, produced by retrieval_assembler._hit_to_block
        # (see retrieval_assembler.py:278-281), must reach the response.
        assert "[Returning Memory]" in text, (
            "[Returning Memory] marker missing from assembled_text — "
            "the v0.2.2 surfacing layer or retrieval_assembler may have "
            "regressed."
        )
        assert "[Voice:" in text, (
            "[Voice:] marker missing from assembled_text — voice-cue "
            "generation or block-text embedding may have regressed."
        )
        assert "[Flavor:" in text, (
            "[Flavor:] marker missing from assembled_text — "
            "spirit_return_flavor was non-empty but did not reach "
            "block text."
        )


# ===========================================================================
# Test C — by_mode breakdown documented modes
# ===========================================================================

class TestSpiritReturnSummaryByModeShape:
    """v0.2.3 §C — `by_mode` keys, when present in the surfaced
    `spirit_return_summary`, are within the documented set
    `{resonance, surfacing, recollection}`. Documents the contract;
    catches future drift if a new mode is added in
    `character.assemble_character_context` without doctrine update.
    """

    _DOCUMENTED_MODES = frozenset({"resonance", "surfacing", "recollection"})

    def test_by_mode_keys_within_documented_set(self, appmod):
        char_ctx = _make_character_context_with_spirit_summary(
            total=3,
            by_mode={"resonance": 2, "surfacing": 1, "recollection": 0},
        )
        core_result = _make_core_result(character_context=char_ctx)
        with patch.object(appmod.fabric, "query", return_value=core_result):
            tc = TestClient(appmod.app)
            r = tc.post("/retrieve", json=_retrieve_payload())
        assert r.status_code == 200, r.text
        srs = r.json()["character_context"]["spirit_return_summary"]
        keys = set(srs["by_mode"].keys())
        unexpected = keys - self._DOCUMENTED_MODES
        assert not unexpected, (
            f"by_mode contains undocumented mode keys: {unexpected!r}. "
            f"Documented set is {self._DOCUMENTED_MODES!r}. If a new "
            f"spirit-return mode is being added, update the v0.2 lane "
            f"doctrine and this assertion together."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
