"""Regression tests for MemoryGraph.search() user_id filtering.

Bug: search() accepted a user_id parameter but never filtered on it,
while search_by_embedding() did apply the filter.  This made the API
contract inconsistent and could silently leak cross-user results in
any mixed-graph usage.

Fix: added the same user_id guard to search() that already existed in
search_by_embedding().

Tests:
  1. search() respects user_id — only matching memories returned
  2. search_by_embedding() and search() behave consistently
  3. search(user_id=None) preserves unrestricted behavior
"""

import os
import shutil
import tempfile

import numpy as np
import pytest

from torment_service.memory_graph import MemoryGraph


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp(prefix="torment_uid_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _populate_mixed_graph(graph: MemoryGraph) -> dict:
    """Spawn memories for two users with distinct text so search hits both."""
    dim = graph._emb_dim
    eids = {}

    # User alice — two memories
    for i, text in enumerate(["alpha observation one", "alpha observation two"]):
        vec = np.random.randn(dim).astype(np.float32)
        eid = graph.spawn_memory(
            summary=text,
            embedding=vec,
            mtype="memory",
            strength=0.8,
            confidence=0.8,
            half_life_days=30.0,
            user_id="alice",
            step=i,
        )
        graph.flush_node(eid)
        eids.setdefault("alice", []).append(eid)

    # User bob — two memories
    for i, text in enumerate(["beta observation one", "beta observation two"]):
        vec = np.random.randn(dim).astype(np.float32)
        eid = graph.spawn_memory(
            summary=text,
            embedding=vec,
            mtype="memory",
            strength=0.8,
            confidence=0.8,
            half_life_days=30.0,
            user_id="bob",
            step=i + 10,
        )
        graph.flush_node(eid)
        eids.setdefault("bob", []).append(eid)

    return eids


# -------------------------------------------------------------------
# 1. search() respects user_id
# -------------------------------------------------------------------


class TestSearchUserIdFilter:
    def test_search_filters_to_alice(self, tmp_dir):
        graph = MemoryGraph(data_dir=tmp_dir)
        _populate_mixed_graph(graph)

        hits = graph.search("observation", top_k=10, user_id="alice")
        user_ids = {h.get("user_id") for h in hits}
        assert user_ids <= {"alice"}, f"Expected only alice, got {user_ids}"
        assert len(hits) > 0, "Should return at least one hit for alice"

    def test_search_filters_to_bob(self, tmp_dir):
        graph = MemoryGraph(data_dir=tmp_dir)
        _populate_mixed_graph(graph)

        hits = graph.search("observation", top_k=10, user_id="bob")
        user_ids = {h.get("user_id") for h in hits}
        assert user_ids <= {"bob"}, f"Expected only bob, got {user_ids}"
        assert len(hits) > 0, "Should return at least one hit for bob"

    def test_search_nonexistent_user_returns_empty(self, tmp_dir):
        graph = MemoryGraph(data_dir=tmp_dir)
        _populate_mixed_graph(graph)

        hits = graph.search("observation", top_k=10, user_id="nobody")
        assert hits == [], f"Expected empty results for unknown user, got {len(hits)}"


# -------------------------------------------------------------------
# 2. search() and search_by_embedding() behave consistently
# -------------------------------------------------------------------


class TestSearchConsistency:
    def test_both_paths_agree_on_user_filter(self, tmp_dir):
        """search() and search_by_embedding() should return the same eids
        when given the same query vector and user_id."""
        graph = MemoryGraph(data_dir=tmp_dir)
        _populate_mixed_graph(graph)

        query_text = "observation"
        qv = np.asarray(
            graph.embedder.embed(query_text), dtype=np.float32
        ).reshape(-1)

        text_hits = graph.search(query_text, top_k=10, user_id="alice")
        emb_hits = graph.search_by_embedding(qv, top_k=10, user_id="alice")

        text_eids = {h["eid"] for h in text_hits}
        emb_eids = {h["eid"] for h in emb_hits}

        assert text_eids == emb_eids, (
            f"search() eids {text_eids} != search_by_embedding() eids {emb_eids}"
        )

    def test_both_paths_agree_no_filter(self, tmp_dir):
        """Without user_id both methods should return the same set."""
        graph = MemoryGraph(data_dir=tmp_dir)
        _populate_mixed_graph(graph)

        query_text = "observation"
        qv = np.asarray(
            graph.embedder.embed(query_text), dtype=np.float32
        ).reshape(-1)

        text_hits = graph.search(query_text, top_k=10, user_id=None)
        emb_hits = graph.search_by_embedding(qv, top_k=10, user_id=None)

        text_eids = {h["eid"] for h in text_hits}
        emb_eids = {h["eid"] for h in emb_hits}

        assert text_eids == emb_eids, (
            f"Unfiltered search() eids {text_eids} != "
            f"search_by_embedding() eids {emb_eids}"
        )


# -------------------------------------------------------------------
# 3. user_id=None preserves unrestricted behavior
# -------------------------------------------------------------------


class TestSearchNoFilter:
    def test_search_none_returns_all_users(self, tmp_dir):
        graph = MemoryGraph(data_dir=tmp_dir)
        eids = _populate_mixed_graph(graph)

        hits = graph.search("observation", top_k=10, user_id=None)
        user_ids = {h.get("user_id") for h in hits}

        assert "alice" in user_ids, "alice should appear when user_id=None"
        assert "bob" in user_ids, "bob should appear when user_id=None"
        expected_count = len(eids["alice"]) + len(eids["bob"])
        assert len(hits) == expected_count, (
            f"Expected {expected_count} hits, got {len(hits)}"
        )
