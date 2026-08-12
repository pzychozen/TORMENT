"""tests/test_deep_hits.py

Slice 0 tests for the non-authoritative deep-hit wrapper types.

Validates the Shape B wrapper-type and field-marker contracts from
Phase 7 Steps B and C:

P0 — safety-bearing:
  * serialization always carries ``authority_status`` with the correct role
  * orphan subtype lacks retrieval-useful fields
  * identity fields are immutable (frozen dataclass)
  * orphan subtype has no rehydrate method
  * both subtypes pass ``isinstance(x, NonAuthoritativeDeepHit)``

P1 — contract-completion:
  * live ``rehydrate()`` returns the entity when the source row is present
  * live ``rehydrate()`` raises ``OrphanedAtRehydrateError`` when the source
    row is absent

Slice 0 does NOT test:
  * β filtering at ``_query_deep_lane`` (not yet wired)
  * α endpoints (not yet implemented)
  * γ sweep (not yet implemented)
  * any cross-module integration
"""
from __future__ import annotations

import dataclasses

import pytest

from torment_service.deep_hits import (
    DeepRetrievalHit,
    NonAuthoritativeDeepHit,
    OrphanedAtRehydrateError,
    OrphanedDeepHit,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _FakeMemoryGraph:
    """Minimal ``MemoryGraph``-shaped stand-in for rehydrate tests.

    Only the ``.entities`` mapping interface is required by
    ``DeepRetrievalHit.rehydrate()``. Keeping the fake local to this test
    module avoids coupling Slice 0 to the real ``MemoryGraph`` class.
    """

    def __init__(self, entities: dict):
        self.entities = entities


def _make_retrieval_hit(**overrides) -> DeepRetrievalHit:
    defaults = dict(
        source_eid=42,
        workspace_id="ws1",
        agent_id="ag1",
        compressed_step=100,
        similarity_score=0.87,
        embedding_ref={"shard": 0, "row": 5},
        display_text="echo of something",
        derivative_metadata={"tier": "relational", "kind": ""},
    )
    defaults.update(overrides)
    return DeepRetrievalHit(**defaults)


def _make_orphaned_hit(**overrides) -> OrphanedDeepHit:
    defaults = dict(
        source_eid=99,
        workspace_id="ws1",
        agent_id="ag1",
        compressed_step=50,
        orphan_reason="source_eid_not_found",
        detected_at=1716300000,
    )
    defaults.update(overrides)
    return OrphanedDeepHit(**defaults)


# ---------------------------------------------------------------------------
# P0: serialization carries authority_status
# ---------------------------------------------------------------------------


def test_deep_retrieval_hit_serializes_with_authority_status():
    """Live hit's ``to_dict()`` emits authority_status with retrieval_echo role."""
    hit = _make_retrieval_hit()
    d = hit.to_dict()

    assert "authority_status" in d, (
        "DeepRetrievalHit.to_dict() must include 'authority_status'"
    )
    status = d["authority_status"]
    assert status["authoritative"] is False
    assert status["requires_rehydration"] is True
    assert status["role"] == "retrieval_echo"


def test_deep_retrieval_hit_identity_serialization_has_four_fixed_fields():
    """Patch D preserves the deep-hit identity shape unchanged."""
    d = _make_retrieval_hit().to_dict()
    identity_fields = {"source_eid", "workspace_id", "agent_id", "compressed_step"}
    assert set(d).intersection(identity_fields) == identity_fields
    assert len(set(d).intersection(identity_fields)) == 4


def test_orphaned_deep_hit_serializes_with_authority_status():
    """Orphan hit's ``to_dict()`` emits authority_status with orphaned_echo role
    and mirrors ``orphan_reason`` into ``rehydration_blocked``.
    """
    hit = _make_orphaned_hit(orphan_reason="source_eid_not_found")
    d = hit.to_dict()

    assert "authority_status" in d, (
        "OrphanedDeepHit.to_dict() must include 'authority_status'"
    )
    status = d["authority_status"]
    assert status["authoritative"] is False
    assert status["requires_rehydration"] is False
    assert status["role"] == "orphaned_echo"
    assert status["rehydration_blocked"] == "source_eid_not_found"


# ---------------------------------------------------------------------------
# P0: orphan lacks retrieval-useful fields
# ---------------------------------------------------------------------------


def test_orphaned_deep_hit_lacks_retrieval_fields():
    """OrphanedDeepHit must not expose retrieval-shaped fields, either on
    the dataclass or in serialized form.
    """
    hit = _make_orphaned_hit()
    retrieval_fields = (
        "similarity_score",
        "embedding_ref",
        "display_text",
        "derivative_metadata",
    )
    for absent_field in retrieval_fields:
        assert not hasattr(hit, absent_field), (
            f"OrphanedDeepHit must not expose retrieval-shaped field "
            f"{absent_field!r}"
        )

    d = hit.to_dict()
    for absent_field in retrieval_fields:
        assert absent_field not in d, (
            f"OrphanedDeepHit.to_dict() must not include "
            f"retrieval-shaped field {absent_field!r}"
        )


# ---------------------------------------------------------------------------
# P0: identity fields are immutable
# ---------------------------------------------------------------------------


def test_wrapper_identity_fields_immutable():
    """Frozen dataclasses must reject field assignment on identity fields."""
    live = _make_retrieval_hit()
    orphan = _make_orphaned_hit()
    identity_fields = ("source_eid", "workspace_id", "agent_id", "compressed_step")

    for hit in (live, orphan):
        for fld in identity_fields:
            with pytest.raises(dataclasses.FrozenInstanceError):
                setattr(hit, fld, "x")


# ---------------------------------------------------------------------------
# P0: orphan has no rehydrate method
# ---------------------------------------------------------------------------


def test_orphaned_deep_hit_has_no_rehydrate_method():
    """OrphanedDeepHit must not expose a rehydrate() method.

    Enforced by class definition; getattr should return False (no method).
    """
    hit = _make_orphaned_hit()
    assert not hasattr(hit, "rehydrate"), (
        "OrphanedDeepHit must not expose a rehydrate() method"
    )


# ---------------------------------------------------------------------------
# P0: both subtypes are NonAuthoritativeDeepHit (rejection-check target)
# ---------------------------------------------------------------------------


def test_subtypes_are_nonauthoritative_for_isinstance_check():
    """Both concrete subtypes must pass isinstance(x, NonAuthoritativeDeepHit).

    Authority-bearing APIs use this single check to reject any non-authoritative
    deep hit at API entry.
    """
    assert isinstance(_make_retrieval_hit(), NonAuthoritativeDeepHit)
    assert isinstance(_make_orphaned_hit(), NonAuthoritativeDeepHit)


# ---------------------------------------------------------------------------
# P1: rehydrate semantics
# ---------------------------------------------------------------------------


def test_deep_retrieval_hit_rehydrate_returns_entity_when_present():
    """rehydrate() returns the entity from memory_graph.entities[source_eid]."""
    sentinel_entity = object()
    graph = _FakeMemoryGraph({42: sentinel_entity})
    hit = _make_retrieval_hit(source_eid=42)

    assert hit.rehydrate(graph) is sentinel_entity


def test_deep_retrieval_hit_rehydrate_raises_when_source_absent():
    """rehydrate() raises OrphanedAtRehydrateError when source row is absent.

    The exception carries the identity of the missing source row.
    """
    graph = _FakeMemoryGraph({})  # empty — source row missing
    hit = _make_retrieval_hit(source_eid=42)

    with pytest.raises(OrphanedAtRehydrateError) as exc_info:
        hit.rehydrate(graph)

    err = exc_info.value
    assert err.source_eid == 42
    assert err.workspace_id == "ws1"
    assert err.agent_id == "ag1"
