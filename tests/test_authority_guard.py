"""tests/test_authority_guard.py

H3 tests for ``assert_authoritative_memory`` and
``NonAuthoritativeMemoryError`` -- the Shape B wrapper-type rejection
enforcement primitive.

The authority guard is the structural enforcement mechanism for the
Shape B wrapper-type contract: authority-bearing APIs call
``assert_authoritative_memory(value)`` at entry to reject any
``NonAuthoritativeDeepHit`` subtype.

P0 -- rejection behavior:
  * ``DeepRetrievalHit`` is rejected.
  * ``OrphanedDeepHit`` is rejected.
  * normal/fake authoritative shapes are accepted (negative guard, not
    a positive credential).
  * exception carries diagnostic info: ``received_type``, ``source_eid``,
    ``role``.
  * a future subtype of ``NonAuthoritativeDeepHit`` is also rejected
    through the base-class isinstance check.

This slice introduces the helper in isolation; no production
authority-bearing API call sites are wired yet.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pytest

from torment_service.deep_hits import (
    DeepRetrievalHit,
    NonAuthoritativeDeepHit,
    NonAuthoritativeMemoryError,
    OrphanedDeepHit,
    assert_authoritative_memory,
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
# P0: rejection of non-authoritative wrappers
# ---------------------------------------------------------------------------


def test_assert_authoritative_memory_rejects_deep_retrieval_hit():
    """A live ``DeepRetrievalHit`` is non-authoritative and must be
    rejected at the guard.
    """
    hit = _make_retrieval_hit()
    with pytest.raises(NonAuthoritativeMemoryError):
        assert_authoritative_memory(hit)


def test_assert_authoritative_memory_rejects_orphaned_deep_hit():
    """An ``OrphanedDeepHit`` is non-authoritative and must be rejected
    at the guard.
    """
    hit = _make_orphan_hit()
    with pytest.raises(NonAuthoritativeMemoryError):
        assert_authoritative_memory(hit)


# ---------------------------------------------------------------------------
# P0: acceptance of non-wrapper shapes
# ---------------------------------------------------------------------------


def test_assert_authoritative_memory_accepts_authoritative_shapes():
    """Negative-guard contract: anything that is not a
    ``NonAuthoritativeDeepHit`` subtype passes through without raising.

    The helper does NOT certify these shapes are authenticated
    authoritative memory; it only confirms they do not announce
    non-authoritative status. Authority verification is the source
    row's responsibility (``MemoryGraph``), not this helper's.
    """
    # A plain dict (e.g., a serialized source row)
    assert_authoritative_memory({"eid": 42, "summary": "x"})

    # A fake SeedEntity-shaped object (duck-typed authoritative shape)
    class _FakeSeedEntity:
        eid = 42
        payload = {"summary": "x"}

    assert_authoritative_memory(_FakeSeedEntity())

    # A bare None (null-check is the caller's responsibility, not the
    # guard's)
    assert_authoritative_memory(None)

    # Primitives pass through silently
    assert_authoritative_memory(42)
    assert_authoritative_memory("not a wrapper")
    assert_authoritative_memory([1, 2, 3])


# ---------------------------------------------------------------------------
# P0: exception carries diagnostic info
# ---------------------------------------------------------------------------


def test_exception_carries_diagnostic_info():
    """``NonAuthoritativeMemoryError`` carries ``received_type``,
    ``source_eid``, and ``role`` for tracing.
    """
    # Live-hit rejection: role = "retrieval_echo"
    hit = _make_retrieval_hit()
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        assert_authoritative_memory(hit)
    err = exc_info.value
    assert err.received_type is DeepRetrievalHit
    assert err.source_eid == 42
    assert err.role == "retrieval_echo"
    # The string message should also surface the diagnostic info.
    msg = str(err)
    assert "DeepRetrievalHit" in msg
    assert "retrieval_echo" in msg
    assert "42" in msg

    # Orphan-hit rejection: role = "orphaned_echo"
    orphan = _make_orphan_hit()
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info_o:
        assert_authoritative_memory(orphan)
    err_o = exc_info_o.value
    assert err_o.received_type is OrphanedDeepHit
    assert err_o.source_eid == 99
    assert err_o.role == "orphaned_echo"
    msg_o = str(err_o)
    assert "OrphanedDeepHit" in msg_o
    assert "orphaned_echo" in msg_o


# ---------------------------------------------------------------------------
# P0: base-class isinstance check (future subtype rejection)
# ---------------------------------------------------------------------------


def test_rejection_uses_base_class_isinstance_check():
    """A locally-defined future subtype of ``NonAuthoritativeDeepHit``
    must also be rejected by ``assert_authoritative_memory``.

    The guard's contract is that it uses ``isinstance`` against the
    abstract base, not a hard-coded list of concrete subtypes. This
    locks the property that any future non-authoritative subtype
    (e.g., a hypothetical ``StaleDeepHit``) is automatically covered
    by the guard without code changes.
    """

    @dataclass(frozen=True, kw_only=True)
    class _FutureSubtype(NonAuthoritativeDeepHit):
        """Locally-defined future subtype, used here for
        contract-locking purposes only.
        """

        extra_field: str = "future"

        def to_dict(self) -> Dict[str, Any]:
            base = super().to_dict()
            base.update(
                {
                    "extra_field": self.extra_field,
                    "authority_status": {
                        "authoritative": False,
                        "requires_rehydration": False,
                        "role": "future_echo",
                    },
                }
            )
            return base

    future = _FutureSubtype(
        source_eid=1,
        workspace_id="ws1",
        agent_id="ag1",
        compressed_step=0,
    )

    # Sanity: the locally-defined class IS a NonAuthoritativeDeepHit.
    assert isinstance(future, NonAuthoritativeDeepHit)

    # The guard must reject it via the base-class isinstance check.
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        assert_authoritative_memory(future)

    # And the exception must surface the subtype's role (extracted via
    # to_dict()).
    err = exc_info.value
    assert err.received_type is _FutureSubtype
    assert err.role == "future_echo"
    assert "future_echo" in str(err)
