"""Regression tests for CachedEmbedder copy-on-hit safety."""

from __future__ import annotations

import numpy as np

from torment_service.embeddings import CachedEmbedder, HashEmbedding


def test_cached_embedding_hits_return_safe_copies() -> None:
    text = "track-j cached embedding alias probe"
    inner = HashEmbedding()
    embedder = CachedEmbedder(inner)

    first = embedder.embed(text)
    expected = inner.embed(text)
    hit = embedder.embed(text)
    stored = embedder._cache[text]

    np.testing.assert_array_equal(first, expected)
    np.testing.assert_array_equal(hit, expected)
    assert hit is not stored
    assert not np.shares_memory(hit, stored)

    hit[0] = np.float32(123.0)
    next_hit = embedder.embed(text)

    np.testing.assert_array_equal(next_hit, expected)
    assert next_hit is not stored
    assert not np.shares_memory(next_hit, stored)
