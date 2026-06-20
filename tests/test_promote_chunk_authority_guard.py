"""tests/test_promote_chunk_authority_guard.py

Deep-hit negative tripwire wiring for `promotion.promote_chunk` (the optional
Path C Q1 boundary). The six governance functions were already wired in a prior
slice; this file is the wiring + coverage for promote_chunk only.

Narrow claim: a live `NonAuthoritativeDeepHit` wrapper passed as `extra_payload`
is rejected (`NonAuthoritativeMemoryError`) BEFORE the canon-promotion write.
Ordinary dict / None payloads pass untouched. This asserts nothing about
source-sameness, dict shapes from `to_dict()`, raw deep-store records, or
stale EIDs.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.promotion import promote_chunk
from torment_service.deep_hits import (
    DeepRetrievalHit,
    OrphanedDeepHit,
    NonAuthoritativeMemoryError,
)


class _FakeMemoryGraph:
    """Minimal mock — records spawns so we can prove no write happened on reject."""

    def __init__(self):
        self.entities = {}
        self._spawned = []
        self._next_eid = 9000

    def spawn_memory(self, summary, embedding, mtype, strength, confidence,
                     half_life_days, links, canon, user_id, step, extra_payload=None):
        eid = self._next_eid
        self._next_eid += 1
        self._spawned.append({"eid": eid, "canon": canon, "extra_payload": extra_payload or {}})

        class _Ent:
            pass

        ent = _Ent()
        ent.eid = eid
        ent.payload = extra_payload or {}
        self.entities[eid] = ent
        return eid

    def flush_node(self, eid):
        pass


class _FakeEmbedder:
    def embed(self, text):
        h = hash(text) % (2**31)
        np.random.seed(h)
        return np.random.randn(384).astype(np.float32)


def _retrieval_hit():
    return DeepRetrievalHit(
        source_eid=1, workspace_id="ws", agent_id="ag",
        compressed_step=5, similarity_score=0.9,
    )


def _orphan_hit():
    return OrphanedDeepHit(
        source_eid=2, workspace_id="ws", agent_id="ag",
        compressed_step=5, orphan_reason="source row gone", detected_at=10,
    )


def _promote(graph, embedder, *, extra_payload):
    return promote_chunk(
        chunk_id="chunk_x",
        chunk_text="A reasonably concise distilled chunk of text.",
        doc_id="doc_x",
        memory_graph=graph,
        embedder=embedder,
        step=7,
        extra_payload=extra_payload,
    )


def test_promote_chunk_rejects_deep_retrieval_hit_before_write():
    graph, embedder = _FakeMemoryGraph(), _FakeEmbedder()
    with pytest.raises(NonAuthoritativeMemoryError):
        _promote(graph, embedder, extra_payload=_retrieval_hit())
    # No canon-promotion write happened — the guard fired first.
    assert graph._spawned == []


def test_promote_chunk_rejects_orphaned_deep_hit_before_write():
    graph, embedder = _FakeMemoryGraph(), _FakeEmbedder()
    with pytest.raises(NonAuthoritativeMemoryError):
        _promote(graph, embedder, extra_payload=_orphan_hit())
    assert graph._spawned == []


def test_promote_chunk_none_extra_payload_passes_guard():
    graph, embedder = _FakeMemoryGraph(), _FakeEmbedder()
    eid = _promote(graph, embedder, extra_payload=None)
    assert eid is not None
    assert len(graph._spawned) == 1
    assert graph._spawned[0]["canon"] is True


def test_promote_chunk_normal_dict_extra_payload_passes_guard():
    graph, embedder = _FakeMemoryGraph(), _FakeEmbedder()
    eid = _promote(graph, embedder, extra_payload={"promotion_reason": "test"})
    assert eid is not None
    assert len(graph._spawned) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
