"""tests/test_update_governance_authority_guard.py

H4b tests for the authority guard wired into ``governance.update_governance``.

``update_governance`` is the *mutation surface* for ``MemoryGovernanceFlags``
on a memory payload. Unlike the read-only governance gates guarded in H4
and H4a, this function modifies state in place: it writes back
``payload["governance"]`` and appends to ``payload["governance_audit"]``.
The authority guard runs BEFORE any mutation attempt so a rejection
produces a clean ``NonAuthoritativeMemoryError`` instead of a confusing
mid-function failure (e.g., a frozen-dataclass assignment error).

P0 -- rejection:
  * ``DeepRetrievalHit`` is rejected at entry.
  * ``OrphanedDeepHit`` is rejected at entry.

P0 -- normal-shape behavior preserved:
  * partial flag update works
  * payload mutates in place
  * audit record is appended
  * unknown flag still raises ``ValueError``
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from torment_service.deep_hits import (
    DeepRetrievalHit,
    NonAuthoritativeMemoryError,
    OrphanedDeepHit,
)
from torment_service.governance import update_governance


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


def test_update_governance_rejects_deep_retrieval_hit():
    """Passing a live retrieval wrapper to update_governance must raise
    NonAuthoritativeMemoryError BEFORE any payload mutation is attempted.
    """
    hit = _make_retrieval_hit()
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        update_governance(hit, {"protected": True})

    err = exc_info.value
    assert err.received_type is DeepRetrievalHit
    assert err.role == "retrieval_echo"


def test_update_governance_rejects_orphaned_deep_hit():
    """Passing an orphan wrapper must raise NonAuthoritativeMemoryError
    BEFORE any payload mutation is attempted. Same rejection mechanism
    as the live subtype.
    """
    orphan = _make_orphan_hit()
    with pytest.raises(NonAuthoritativeMemoryError) as exc_info:
        update_governance(orphan, {"protected": True})

    err = exc_info.value
    assert err.received_type is OrphanedDeepHit
    assert err.role == "orphaned_echo"


# ---------------------------------------------------------------------------
# P0: normal-shape behavior preserved
# ---------------------------------------------------------------------------


def test_update_governance_accepts_normal_dict_payloads():
    """The guard is a tripwire only -- normal dict payload behavior is
    unchanged:

      * partial flag update works
      * payload mutates in place
      * audit record is appended
      * unknown flag still raises ValueError
    """
    # --- partial update on empty payload ---
    payload: Dict[str, Any] = {}
    audit = update_governance(payload, {"protected": True})

    # In-place mutation: governance dict written into payload
    assert "governance" in payload
    assert payload["governance"]["protected"] is True
    # Other flags default to False (since they were unspecified)
    assert payload["governance"]["non_shareable"] is False

    # Audit trail appended
    assert "governance_audit" in payload
    assert isinstance(payload["governance_audit"], list)
    assert len(payload["governance_audit"]) == 1
    assert payload["governance_audit"][0]["changed"]["protected"]["new"] is True
    assert payload["governance_audit"][0]["changed"]["protected"]["old"] is False

    # Returned audit record matches the appended entry
    assert audit["changed"]["protected"]["new"] is True
    assert audit["actor"] == "operator"  # default
    assert audit["source"] == "api"  # default

    # --- second update: appends to audit (does not replace) ---
    audit2 = update_governance(
        payload, {"non_shareable": True}, actor="admin", source="cli"
    )
    assert payload["governance"]["non_shareable"] is True
    assert payload["governance"]["protected"] is True  # unchanged
    assert len(payload["governance_audit"]) == 2
    assert audit2["actor"] == "admin"
    assert audit2["source"] == "cli"

    # --- unknown flag still raises ValueError ---
    with pytest.raises(ValueError) as exc_info:
        update_governance({}, {"nonexistent_flag": True})
    assert "nonexistent_flag" in str(exc_info.value)
