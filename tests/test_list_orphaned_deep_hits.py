"""tests/test_list_orphaned_deep_hits.py

H2 tests for ``fabric.list_orphaned_deep_hits`` -- the alpha diagnostic
building block.

Validates the Shape B alpha contract: orphaned deep records are
identifiable by source-row absence, returned as ``OrphanedDeepHit``
wrapper instances, carrying the canonical ``authority_status`` marker
with ``role: "orphaned_echo"``.

P0 -- helper behavior:
  * returns only orphans (records with no source row)
  * returns empty when all source rows present
  * returns all records as orphans when private graph is missing
  * returns empty when no deep store exists

P0 -- wrapper-shape correctness at the helper boundary:
  * returned records serialize with authority_status.role == "orphaned_echo"
  * returned records are OrphanedDeepHit; lack retrieval-useful fields
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from torment_service.deep_hits import DeepRetrievalHit, OrphanedDeepHit
from torment_service.deep_memory import DeepMemory
from torment_service.fabric import TormentFabric


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _FakeEntity:
    """Minimal stand-in for a MemoryGraph entity. Only ``.payload`` is
    accessed by the helper / by adjacent code.
    """

    def __init__(self, payload: Dict[str, Any]) -> None:
        self.payload = payload


class _FakeMemoryGraph:
    """Minimal stand-in for MemoryGraph. Only ``.entities`` is accessed."""

    def __init__(self, entities_by_eid: Dict[int, _FakeEntity]) -> None:
        self.entities = entities_by_eid


class _FakeDeepStore:
    """Minimal DeepMemoryStore stand-in.

    Exposes the two attributes the helper reads:
      * ``._ensure_loaded`` -- no-op for tests
      * ``._memories``      -- list of DeepMemory records
    """

    def __init__(self, hits: List[DeepMemory]) -> None:
        self._memories = list(hits)

    def _ensure_loaded(self) -> None:
        return None


def _make_dm(eid: int, summary: str = "") -> DeepMemory:
    """Construct a minimal DeepMemory for testing."""
    return DeepMemory(
        eid=int(eid),
        born_step=0,
        compressed_step=100,
        summary=summary or f"deep_summary_{eid}",
        compression_score=0.5,
        original_motif_id=None,
        memory_class="core",
        embedding_ref=None,
        metadata={"tier": "relational"},
    )


def _make_fake_fabric(deep_store=None, private_graph=None):
    """Construct a minimal fabric-like object exposing the attributes
    that ``list_orphaned_deep_hits`` accesses.

    The helper is invoked via the unbound method descriptor, so this
    stand-in does not need to inherit from TormentFabric.
    """
    ws_id = "ws1"
    ag_id = "ag1"
    ak = TormentFabric._agent_key(ws_id, ag_id)

    class _FakeFabric:
        pass

    f = _FakeFabric()
    f._deep_stores = {ak: deep_store} if deep_store is not None else {}
    f.private_graphs = (
        {ak: private_graph} if private_graph is not None else {}
    )
    # The helper calls self._agent_key(...). Bind it from the real class.
    f._agent_key = TormentFabric._agent_key
    return f, ws_id, ag_id


def _call(fake_fabric, ws_id, ag_id):
    """Invoke the helper as an unbound method against the fake fabric."""
    return TormentFabric.list_orphaned_deep_hits(fake_fabric, ws_id, ag_id)


# ---------------------------------------------------------------------------
# P0: helper behavior
# ---------------------------------------------------------------------------


def test_list_orphaned_returns_only_orphans():
    """Deep store has EIDs 1, 2, 3. MemoryGraph has source rows for 1 and 3
    only. EID 2 must be classified as orphan and returned; live records must
    not appear.
    """
    deep_store = _FakeDeepStore(
        hits=[_make_dm(1), _make_dm(2), _make_dm(3)]
    )
    pg = _FakeMemoryGraph(
        entities_by_eid={
            1: _FakeEntity(payload={}),
            3: _FakeEntity(payload={}),
        }
    )
    fake, ws_id, ag_id = _make_fake_fabric(
        deep_store=deep_store, private_graph=pg
    )

    result = _call(fake, ws_id, ag_id)

    assert len(result) == 1, (
        f"Expected exactly 1 orphan (EID 2), got {len(result)}: {result}"
    )
    assert result[0].source_eid == 2
    assert isinstance(result[0], OrphanedDeepHit)


def test_list_orphaned_returns_empty_when_all_present():
    """Deep store has 3 records; MemoryGraph has all 3 as source rows.
    Helper returns empty list.
    """
    deep_store = _FakeDeepStore(
        hits=[_make_dm(1), _make_dm(2), _make_dm(3)]
    )
    pg = _FakeMemoryGraph(
        entities_by_eid={
            1: _FakeEntity(payload={}),
            2: _FakeEntity(payload={}),
            3: _FakeEntity(payload={}),
        }
    )
    fake, ws_id, ag_id = _make_fake_fabric(
        deep_store=deep_store, private_graph=pg
    )

    assert _call(fake, ws_id, ag_id) == []


def test_list_orphaned_returns_all_when_private_graph_missing():
    """Deep store has 3 records but no private graph exists for the agent.
    Every deep record is orphaned by definition.
    """
    deep_store = _FakeDeepStore(
        hits=[_make_dm(1), _make_dm(2), _make_dm(3)]
    )
    fake, ws_id, ag_id = _make_fake_fabric(
        deep_store=deep_store, private_graph=None
    )

    result = _call(fake, ws_id, ag_id)
    assert len(result) == 3, (
        f"Expected 3 orphans (all records), got {len(result)}: {result}"
    )
    for record in result:
        assert isinstance(record, OrphanedDeepHit)


def test_list_orphaned_returns_empty_when_deep_store_missing():
    """No deep store exists for the agent. Helper returns empty list
    without error.
    """
    fake, ws_id, ag_id = _make_fake_fabric(
        deep_store=None, private_graph=None
    )

    assert _call(fake, ws_id, ag_id) == []


# ---------------------------------------------------------------------------
# P0: wrapper-shape correctness at the helper boundary
# ---------------------------------------------------------------------------


def test_orphaned_results_carry_authority_status_orphaned_echo():
    """Every returned orphan serializes with the canonical
    ``authority_status`` marker carrying ``role: "orphaned_echo"``.
    """
    deep_store = _FakeDeepStore(hits=[_make_dm(42)])
    pg = _FakeMemoryGraph(entities_by_eid={})  # source row missing
    fake, ws_id, ag_id = _make_fake_fabric(
        deep_store=deep_store, private_graph=pg
    )

    result = _call(fake, ws_id, ag_id)

    assert len(result) == 1
    serialized = result[0].to_dict()
    assert "authority_status" in serialized
    status = serialized["authority_status"]
    assert status["authoritative"] is False
    assert status["requires_rehydration"] is False
    assert status["role"] == "orphaned_echo"
    assert status["rehydration_blocked"] == "source_eid_not_found"


def test_orphaned_results_are_orphaned_deep_hit_and_lack_retrieval_fields():
    """Returned records must be ``OrphanedDeepHit`` (not raw ``DeepMemory``
    and not ``DeepRetrievalHit``), and must structurally lack
    retrieval-shaped fields.
    """
    deep_store = _FakeDeepStore(hits=[_make_dm(42)])
    pg = _FakeMemoryGraph(entities_by_eid={})  # source row missing
    fake, ws_id, ag_id = _make_fake_fabric(
        deep_store=deep_store, private_graph=pg
    )

    result = _call(fake, ws_id, ag_id)

    assert len(result) == 1
    record = result[0]

    # Concrete type assertions
    assert isinstance(record, OrphanedDeepHit)
    assert not isinstance(record, DeepRetrievalHit)
    assert not isinstance(record, DeepMemory)

    # Retrieval-shaped fields are structurally absent
    for absent_field in (
        "similarity_score",
        "embedding_ref",
        "display_text",
        "derivative_metadata",
    ):
        assert not hasattr(record, absent_field), (
            f"OrphanedDeepHit must not carry retrieval-shaped field "
            f"{absent_field!r}"
        )

    # Diagnostic-bearing fields ARE present
    assert record.source_eid == 42
    assert record.orphan_reason == "source_eid_not_found"
    assert record.detected_at > 0


# ---------------------------------------------------------------------------
# P0: fail-soft diagnostic honesty when the deep store fails to load
# ---------------------------------------------------------------------------


def test_list_orphaned_fail_soft_warns_when_ensure_loaded_raises(caplog):
    """If ``deep_store._ensure_loaded()`` raises, the orphan diagnostic
    enumeration must stay fail-soft: still return a list (the existing
    empty-list shape for a store exposing no records), while emitting a
    WARNING breadcrumb that identifies the load failure and carries the
    synthetic exception context. The return contract is unchanged.
    """

    class _RaisingDeepStore:
        # ``_ensure_loaded`` raises; ``_memories`` stays empty so the
        # post-failure continuation yields the existing empty-list shape.
        _memories: List[DeepMemory] = []

        def _ensure_loaded(self) -> None:
            raise RuntimeError("synthetic ensure_loaded failure XYZZY")

    fake, ws_id, ag_id = _make_fake_fabric(deep_store=_RaisingDeepStore())

    with caplog.at_level(logging.WARNING, logger="torment.fabric"):
        result = _call(fake, ws_id, ag_id)

    # 1 + 2: fail-soft -- returns a list, in the existing empty-list shape
    assert isinstance(result, list)
    assert result == []

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]

    # 3 + 4: a WARNING breadcrumb identifying orphan diagnostic load failure
    assert any(
        "orphan diagnostic enumeration" in r.getMessage()
        and "load failed" in r.getMessage()
        for r in warnings
    ), (
        "expected an orphan-diagnostic load-failure WARNING; got: "
        f"{[r.getMessage() for r in warnings]}"
    )

    # 5: the synthetic exception context is visible in the captured log
    assert any(
        "synthetic ensure_loaded failure XYZZY" in r.getMessage()
        for r in warnings
    )
