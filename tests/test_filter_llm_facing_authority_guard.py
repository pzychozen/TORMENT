"""tests/test_filter_llm_facing_authority_guard.py

H4d tests for the authority guard wired into
``governance.filter_llm_facing``.

``filter_llm_facing`` is the FILTER-A canonical helper that gates LLM-facing
context. It had a pre-H4d defensive non-dict pass-through that would have
let a ``NonAuthoritativeDeepHit`` wrapper leak straight through to LLM
context. H4d closes that leak with fail-loud per-item rejection: the first
wrapper encountered in the hits list raises ``NonAuthoritativeMemoryError``,
and the rest of the list is not processed.

P0 -- rejection (3 tests):
  * list containing a ``DeepRetrievalHit`` is rejected
  * list containing an ``OrphanedDeepHit`` is rejected
  * mixed list (dicts + one wrapper) is rejected (fail-loud, not silent drop)

P0 -- existing behavior preserved (2 tests):
  * pure dict list goes through filtering unchanged
  * non-dict, non-wrapper items still pass through defensively
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from torment_service.deep_hits import (
    DeepRetrievalHit,
    NonAuthoritativeMemoryError,
    OrphanedDeepHit,
)
from torment_service.governance import (
    SURFACE_COLLECTIVE_EXPORT,
    SURFACE_LLM_CONTEXT,
    filter_llm_facing,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_retrieval_hit() -> DeepRetrievalHit:
    return DeepRetrievalHit(
        source_eid=42,
        workspace_id="ws1",
        agent_id="ag1",
        compressed_step=100,
        similarity_score=0.5,
        embedding_ref=None,
        display_text=None,
        derivative_metadata={},
    )


def _make_orphan_hit() -> OrphanedDeepHit:
    return OrphanedDeepHit(
        source_eid=99,
        workspace_id="ws1",
        agent_id="ag1",
        compressed_step=50,
        orphan_reason="source_eid_not_found",
        detected_at=1716300000,
    )


def _dict_hit(eid: int, *, non_shareable: bool = False,
              collective_export_blocked: bool = False) -> Dict[str, Any]:
    """Build a minimal dict-shaped memory hit with optional governance."""
    gov: Dict[str, bool] = {}
    if non_shareable:
        gov["non_shareable"] = True
    if collective_export_blocked:
        gov["collective_export_blocked"] = True
    hit: Dict[str, Any] = {"eid": eid, "summary": f"hit_{eid}"}
    if gov:
        hit["governance"] = gov
    return hit


# ---------------------------------------------------------------------------
# P0: rejection of wrappers in the list
# ---------------------------------------------------------------------------


def test_filter_llm_facing_rejects_deep_retrieval_hit_in_list():
    """A list containing a DeepRetrievalHit raises NonAuthoritativeMemoryError
    before any LLM-facing context is built.
    """
    hits = [_make_retrieval_hit()]
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        filter_llm_facing(hits, surface=SURFACE_LLM_CONTEXT)
    err = exc_info.value
    assert err.received_type is DeepRetrievalHit
    assert err.role == "retrieval_echo"


def test_filter_llm_facing_rejects_orphaned_deep_hit_in_list():
    """A list containing an OrphanedDeepHit raises
    NonAuthoritativeMemoryError. Same rejection mechanism as the live
    subtype; the base-class isinstance check covers both.
    """
    hits = [_make_orphan_hit()]
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        filter_llm_facing(hits, surface=SURFACE_COLLECTIVE_EXPORT)
    err = exc_info.value
    assert err.received_type is OrphanedDeepHit
    assert err.role == "orphaned_echo"


def test_filter_llm_facing_rejects_mixed_list_with_wrapper():
    """Mixed list with normal dicts plus one wrapper must raise on the
    wrapper. Fail-loud: the whole call rejects rather than silently
    dropping the wrapper and returning the dicts.
    """
    hits = [
        _dict_hit(1),
        _dict_hit(2),
        _make_retrieval_hit(),  # wrapper at index 2
        _dict_hit(4),
    ]
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        filter_llm_facing(hits, surface=SURFACE_LLM_CONTEXT)
    err = exc_info.value
    # The exception identifies the offending wrapper
    assert err.received_type is DeepRetrievalHit
    assert err.source_eid == 42
    assert err.role == "retrieval_echo"


# ---------------------------------------------------------------------------
# P0: existing behavior preserved
# ---------------------------------------------------------------------------


def test_filter_llm_facing_normal_dict_list_unchanged():
    """Pure dict list goes through governance-flag filtering verbatim:
      * non_shareable=True is excluded
      * non_shareable=False (or absent) passes
      * results/excluded contract is intact
    """
    hits = [
        _dict_hit(1),  # default permissive
        _dict_hit(2, non_shareable=True),
        _dict_hit(3),
    ]
    out = filter_llm_facing(hits, surface=SURFACE_LLM_CONTEXT)

    assert "results" in out and "excluded" in out
    result_eids = {h["eid"] for h in out["results"]}
    excluded_eids = {e["eid"] for e in out["excluded"]}

    # eids 1 and 3 are admitted; eid 2 is excluded for non_shareable
    assert result_eids == {1, 3}
    assert excluded_eids == {2}
    assert out["excluded"][0]["excluded_reason"] == "non_shareable"


def test_filter_llm_facing_non_dict_non_wrapper_defensive_passthrough_unchanged():
    """Non-dict, non-wrapper items (None, int, str, list, etc.) still
    pass through defensively to results, preserving the function's
    existing behavior for unrecognised shapes.

    Note: this is the existing FILTER-A defensive contract. H4d
    deliberately preserves it; only NonAuthoritativeDeepHit subtypes
    are rejected.
    """
    hits = [
        _dict_hit(1),
        None,
        42,
        "not a hit",
        _dict_hit(5),
    ]
    out = filter_llm_facing(hits, surface=SURFACE_LLM_CONTEXT)

    # All 5 items pass through (no governance flag on the dicts, defensive
    # pass-through on the other three).
    assert len(out["results"]) == 5
    assert out["excluded"] == []

    # Verify the non-dict items kept their identity (defensive pass-through)
    assert None in out["results"]
    assert 42 in out["results"]
    assert "not a hit" in out["results"]
