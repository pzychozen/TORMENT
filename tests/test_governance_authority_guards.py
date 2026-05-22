"""tests/test_governance_authority_guards.py

H4a tests for the sibling governance authority guards.

After H4, ``should_emit_packet`` rejected NonAuthoritativeDeepHit at entry.
H4a extends the same guard to the three sibling governance gates:

    * ``is_compression_protected(payload)``
    * ``is_decay_accelerated(payload)``
    * ``allows_collective_reingest(payload)``

This file tests the rejection contract and verifies that normal
dict/None payload behavior is preserved verbatim for each function.

P0 -- rejection (6 tests, 2 per function):
  * each function rejects ``DeepRetrievalHit``
  * each function rejects ``OrphanedDeepHit``

P0 -- normal-shape behavior preserved (3 tests, 1 per function):
  * existing flag semantics unchanged under dict / None payloads
"""
from __future__ import annotations

import pytest

from torment_service.deep_hits import (
    DeepRetrievalHit,
    NonAuthoritativeMemoryError,
    OrphanedDeepHit,
)
from torment_service.governance import (
    allows_collective_reingest,
    is_compression_protected,
    is_decay_accelerated,
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


# ---------------------------------------------------------------------------
# P0: is_compression_protected
# ---------------------------------------------------------------------------


def test_is_compression_protected_rejects_deep_retrieval_hit():
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        is_compression_protected(_make_retrieval_hit())
    assert exc_info.value.role == "retrieval_echo"


def test_is_compression_protected_rejects_orphaned_deep_hit():
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        is_compression_protected(_make_orphan_hit())
    assert exc_info.value.role == "orphaned_echo"


def test_is_compression_protected_accepts_normal_dict_payloads():
    """Existing flag semantics: protected=True -> True; otherwise False."""
    assert is_compression_protected({"governance": {"protected": True}}) is True
    assert is_compression_protected({"governance": {"protected": False}}) is False
    assert is_compression_protected({}) is False
    assert is_compression_protected(None) is False


# ---------------------------------------------------------------------------
# P0: is_decay_accelerated
# ---------------------------------------------------------------------------


def test_is_decay_accelerated_rejects_deep_retrieval_hit():
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        is_decay_accelerated(_make_retrieval_hit())
    assert exc_info.value.role == "retrieval_echo"


def test_is_decay_accelerated_rejects_orphaned_deep_hit():
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        is_decay_accelerated(_make_orphan_hit())
    assert exc_info.value.role == "orphaned_echo"


def test_is_decay_accelerated_accepts_normal_dict_payloads():
    """Existing flag semantics:
      * decay_accelerated=True alone -> True
      * protected=True overrides decay_accelerated=True -> False
      * empty/None -> False
    """
    # decay_accelerated true alone -> True
    assert (
        is_decay_accelerated({"governance": {"decay_accelerated": True}})
        is True
    )
    # protected wins even when decay_accelerated is true
    assert (
        is_decay_accelerated(
            {"governance": {"protected": True, "decay_accelerated": True}}
        )
        is False
    )
    # No governance block -> False
    assert is_decay_accelerated({}) is False
    assert is_decay_accelerated(None) is False


# ---------------------------------------------------------------------------
# P0: allows_collective_reingest
# ---------------------------------------------------------------------------


def test_allows_collective_reingest_rejects_deep_retrieval_hit():
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        allows_collective_reingest(_make_retrieval_hit())
    assert exc_info.value.role == "retrieval_echo"


def test_allows_collective_reingest_rejects_orphaned_deep_hit():
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        allows_collective_reingest(_make_orphan_hit())
    assert exc_info.value.role == "orphaned_echo"


def test_allows_collective_reingest_accepts_normal_dict_payloads():
    """Existing flag semantics:
      * collective_reingest_blocked=False -> True (allowed)
      * collective_reingest_blocked=True -> False (blocked)
      * empty/None -> True (default permissive)
    """
    assert (
        allows_collective_reingest(
            {"governance": {"collective_reingest_blocked": False}}
        )
        is True
    )
    assert (
        allows_collective_reingest(
            {"governance": {"collective_reingest_blocked": True}}
        )
        is False
    )
    assert allows_collective_reingest({}) is True
    assert allows_collective_reingest(None) is True
