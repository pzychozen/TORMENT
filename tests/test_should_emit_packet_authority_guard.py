"""tests/test_should_emit_packet_authority_guard.py

H4 tests for the first load-bearing authority guard:
``governance.should_emit_packet`` now rejects ``NonAuthoritativeDeepHit``
subtypes at entry.

This is the first production wiring of ``assert_authoritative_memory``
(H3). It establishes the precedent for wiring the sibling governance
functions (``is_compression_protected``, ``is_decay_accelerated``,
``allows_collective_reingest``) in subsequent slices.

P0 -- rejection:
  * ``DeepRetrievalHit`` is rejected at entry.
  * ``OrphanedDeepHit`` is rejected at entry.

P0 -- normal-shape behavior preserved:
  * empty dict, None, and governance-flag dict shapes return the
    expected boolean.
  * ``non_shareable=True`` blocks emission.
  * ``collective_export_blocked=True`` blocks emission.
"""
from __future__ import annotations

import pytest

from torment_service.deep_hits import (
    DeepRetrievalHit,
    NonAuthoritativeMemoryError,
    OrphanedDeepHit,
)
from torment_service.governance import should_emit_packet


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
# P0: rejection
# ---------------------------------------------------------------------------


def test_should_emit_packet_rejects_deep_retrieval_hit():
    """A DeepRetrievalHit passed to should_emit_packet must raise
    NonAuthoritativeMemoryError. The wrapper announces non-authoritative
    status and cannot reach the sharing-decision boundary.
    """
    hit = _make_retrieval_hit()
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        should_emit_packet(hit)
    err = exc_info.value
    assert err.received_type is DeepRetrievalHit
    assert err.role == "retrieval_echo"


def test_should_emit_packet_rejects_orphaned_deep_hit():
    """An OrphanedDeepHit passed to should_emit_packet must raise
    NonAuthoritativeMemoryError. Same rejection mechanism as the live
    subtype; verifies the base-class isinstance check covers both.
    """
    hit = _make_orphan_hit()
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        should_emit_packet(hit)
    err = exc_info.value
    assert err.received_type is OrphanedDeepHit
    assert err.role == "orphaned_echo"


# ---------------------------------------------------------------------------
# P0: normal-shape behavior preserved
# ---------------------------------------------------------------------------


def test_should_emit_packet_accepts_normal_dict_payloads():
    """The guard is a tripwire only -- normal dict/None payloads must
    pass through unchanged. The existing governance flag semantics are
    preserved verbatim.
    """
    # Default permissive: empty payload, no governance block
    assert should_emit_packet({}) is True

    # Explicit non_shareable=False: emit allowed
    assert should_emit_packet({"governance": {"non_shareable": False}}) is True

    # non_shareable=True: emit blocked
    assert should_emit_packet({"governance": {"non_shareable": True}}) is False

    # collective_export_blocked=True: emit blocked
    assert (
        should_emit_packet(
            {"governance": {"collective_export_blocked": True}}
        )
        is False
    )

    # None payload: permissive default per existing contract
    assert should_emit_packet(None) is True

    # Payload with unrelated keys: still permissive
    assert should_emit_packet({"summary": "hello", "eid": 7}) is True
