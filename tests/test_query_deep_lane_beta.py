"""tests/test_query_deep_lane_beta.py

H1 tests for beta runtime filtering at ``fabric._query_deep_lane``.

Validates the Shape B safety contract: orphaned deep hits do not leave
``_query_deep_lane`` on the normal consumer path, and every returned dict
carries the canonical ``authority_status`` marker per the Path C field-marker
contract (Phase 7 Step C).

P0 -- safety-bearing:
  * orphan deep hit filtered from _query_deep_lane
  * live deep hit returned with authority_status.role == "retrieval_echo"
  * mixed live+orphan returns only live
  * raw DeepMemory objects do not leak through _query_deep_lane
  * every returned hit has authority_status.authoritative == False

P1 -- legacy-compat:
  * legacy from_deep_memory / deep_memory markers do not contradict
    authority_status
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from torment_service.deep_memory import DeepMemory
from torment_service.fabric import TormentFabric


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _FakeEntity:
    """Minimal stand-in for a MemoryGraph entity. Only ``.payload`` is
    accessed by _query_deep_lane.
    """

    def __init__(self, payload: Dict[str, Any]) -> None:
        self.payload = payload


class _FakeMemoryGraph:
    """Minimal stand-in for MemoryGraph. Only ``.entities`` is accessed by
    _query_deep_lane.
    """

    def __init__(self, entities_by_eid: Dict[int, _FakeEntity]) -> None:
        self.entities = entities_by_eid


class _FakeDeepStore:
    """Minimal stand-in for DeepMemoryStore. Only ``.query(qv, top_k)`` is
    called by _query_deep_lane.
    """

    def __init__(self, hits: List[DeepMemory]) -> None:
        self._hits = hits

    def query(self, qv: Any, top_k: int) -> List[DeepMemory]:
        return list(self._hits[: max(1, int(top_k))])


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


def _make_fake_fabric(tmpdir, deep_store, private_graph):
    """Construct a minimal fabric-like object exposing the attributes that
    _query_deep_lane needs. The function is invoked via the unbound method
    descriptor, so this stand-in does not need to inherit from TormentFabric.
    """
    ws_id = "ws1"
    ag_id = "ag1"
    ak = TormentFabric._agent_key(ws_id, ag_id)

    class _FakeFabric:
        pass

    f = _FakeFabric()
    f._compress_enable = True
    f.data_dir = str(tmpdir)
    f._deep_stores = {ak: deep_store}
    f.private_graphs = {ak: private_graph}
    return f, ws_id, ag_id, ak


def _call_query_deep_lane(fake_fabric, ak, ws_id, ag_id, top_k=5, step=100):
    """Invoke TormentFabric._query_deep_lane as an unbound function against
    the fake fabric instance. This avoids constructing a full TormentFabric.
    """
    qemb = np.zeros(384, dtype=np.float32)
    return TormentFabric._query_deep_lane(
        fake_fabric, ak, ws_id, ag_id, qemb,
        top_k=top_k, canonical_step=step,
    )


# ---------------------------------------------------------------------------
# P0: beta filter behavior
# ---------------------------------------------------------------------------


def test_orphan_deep_hit_filtered_from_query_deep_lane(tmp_path):
    """A deep hit whose source EID is absent from MemoryGraph.entities must
    NOT appear in the returned list.
    """
    # Empty graph -- the deep hit's source row does not exist.
    graph = _FakeMemoryGraph(entities_by_eid={})
    store = _FakeDeepStore(hits=[_make_dm(eid=42)])
    fake, ws_id, ag_id, ak = _make_fake_fabric(tmp_path, store, graph)

    result = _call_query_deep_lane(fake, ak, ws_id, ag_id)

    assert result == [], (
        "Orphan deep hit must be filtered out by beta at _query_deep_lane"
    )


def test_live_deep_hit_returned_with_authority_status_marker(tmp_path):
    """A deep hit whose source EID is present in MemoryGraph.entities is
    returned with the canonical authority_status marker
    (role == 'retrieval_echo').
    """
    graph = _FakeMemoryGraph(
        entities_by_eid={42: _FakeEntity(payload={"compressed": False})}
    )
    store = _FakeDeepStore(hits=[_make_dm(eid=42)])
    fake, ws_id, ag_id, ak = _make_fake_fabric(tmp_path, store, graph)

    result = _call_query_deep_lane(fake, ak, ws_id, ag_id)

    assert len(result) == 1, (
        f"Expected exactly 1 live hit, got {len(result)}: {result}"
    )
    hit = result[0]
    assert "authority_status" in hit, (
        "Every returned hit must carry authority_status"
    )
    status = hit["authority_status"]
    assert status["authoritative"] is False
    assert status["requires_rehydration"] is True
    assert status["role"] == "retrieval_echo"


def test_mixed_live_and_orphan_returns_only_live(tmp_path):
    """Two hits, one with a live source row and one orphan, must produce a
    single returned dict for the live one only.
    """
    # eid 42 is live in MemoryGraph; eid 99 is orphan
    graph = _FakeMemoryGraph(
        entities_by_eid={42: _FakeEntity(payload={"compressed": False})}
    )
    store = _FakeDeepStore(hits=[_make_dm(eid=42), _make_dm(eid=99)])
    fake, ws_id, ag_id, ak = _make_fake_fabric(tmp_path, store, graph)

    result = _call_query_deep_lane(fake, ak, ws_id, ag_id)

    assert len(result) == 1, (
        f"Expected exactly 1 hit (live), got {len(result)}: {result}"
    )
    # Marker must be present on the surviving live hit.
    assert "authority_status" in result[0]
    assert result[0]["authority_status"]["role"] == "retrieval_echo"


def test_raw_deepmemory_does_not_leak_through_query_deep_lane(tmp_path):
    """No element of the returned list may be a raw DeepMemory instance.

    The function is contractually a dict-emitter; raw storage types must not
    leak across the consumer boundary.
    """
    graph = _FakeMemoryGraph(
        entities_by_eid={42: _FakeEntity(payload={"compressed": False})}
    )
    store = _FakeDeepStore(hits=[_make_dm(eid=42)])
    fake, ws_id, ag_id, ak = _make_fake_fabric(tmp_path, store, graph)

    result = _call_query_deep_lane(fake, ak, ws_id, ag_id)

    for item in result:
        assert not isinstance(item, DeepMemory), (
            f"Raw DeepMemory must not leak through _query_deep_lane; "
            f"got: {type(item).__name__}"
        )


# ---------------------------------------------------------------------------
# P0: authority_status presence on every returned hit
# ---------------------------------------------------------------------------


def test_query_deep_lane_emits_authority_status_on_every_returned_hit(tmp_path):
    """Every returned hit dict must carry an ``authority_status`` block with
    ``authoritative: False`` and ``role: "retrieval_echo"``.
    """
    graph = _FakeMemoryGraph(
        entities_by_eid={
            1: _FakeEntity(payload={"compressed": False}),
            2: _FakeEntity(payload={"compressed": True}),
            3: _FakeEntity(payload={"compressed": False}),
        }
    )
    store = _FakeDeepStore(
        hits=[_make_dm(eid=1), _make_dm(eid=2), _make_dm(eid=3)]
    )
    fake, ws_id, ag_id, ak = _make_fake_fabric(tmp_path, store, graph)

    result = _call_query_deep_lane(fake, ak, ws_id, ag_id)

    assert len(result) >= 1, "Expected at least one live hit to be returned"
    for hit in result:
        assert "authority_status" in hit, (
            f"Returned hit missing authority_status marker: {hit}"
        )
        status = hit["authority_status"]
        assert status["authoritative"] is False
        assert status["role"] == "retrieval_echo"


# ---------------------------------------------------------------------------
# P1: legacy marker compatibility
# ---------------------------------------------------------------------------


def test_legacy_from_deep_memory_marker_does_not_contradict_authority_status(
    tmp_path,
):
    """If the legacy ``from_deep_memory: True`` marker is present in the
    returned hit dict, it must not contradict
    ``authority_status.authoritative == False``.

    Per Phase 7 Step C: legacy markers may persist temporarily during the
    transition window, but must not disagree with the canonical marker.
    """
    graph = _FakeMemoryGraph(
        entities_by_eid={42: _FakeEntity(payload={"compressed": False})}
    )
    store = _FakeDeepStore(hits=[_make_dm(eid=42)])
    fake, ws_id, ag_id, ak = _make_fake_fabric(tmp_path, store, graph)

    result = _call_query_deep_lane(fake, ak, ws_id, ag_id)

    assert len(result) == 1
    hit = result[0]
    # Legacy markers MAY be present; if present, they must not contradict
    # the canonical authority_status marker.
    legacy_present = (
        hit.get("from_deep_memory") is True or hit.get("deep_memory") is True
    )
    if legacy_present:
        assert hit["authority_status"]["authoritative"] is False, (
            "Legacy from_deep_memory / deep_memory markers must not "
            "contradict authority_status.authoritative == False"
        )
