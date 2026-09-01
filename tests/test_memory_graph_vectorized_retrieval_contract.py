"""7G5E4A characterization of the live MemoryGraph vector-cache contract.

These tests deliberately do not activate native retrieval.  They freeze the
float32 matrix calculation that a later rebuildable native runtime must copy
from qualified durable vector bytes.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from torment_service.memory_graph import MemoryGraph
from torment_service.substrate.compat import (
    CompatibilityEmbeddingPublicationRequest,
    NativeMemoryCompatibilityFacade,
)
from torment_service.substrate.compat_embedding_reader import NativeCompatEmbeddingReader
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.schema import create_schema


class _ThreeDimensionalEmbedder:
    dim = 3
    provider = "7g5e4a-test"
    model = "frozen"

    def embed(self, _text: str) -> np.ndarray:
        return np.asarray((1.0, 0.0, 0.0), dtype=np.float32)


def _native_context(tmp_path: Path):
    opened = open_temporary_test_connection(tmp_path / "native-vector-contract.db")
    create_schema(opened.connection)
    values = {
        "connection": opened.connection,
        "opened": opened,
        "identity": generate_native_id(),
        "scope": generate_native_id(),
        "source": generate_native_id(),
        "idempotency": generate_native_id(),
    }
    opened.connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(values["identity"]), "7g5e4a-memory-identity"),
    )
    opened.connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(values["scope"]), "7g5e4a-memory-scope"),
    )
    opened.connection.execute(
        "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(values["source"]), "7g5e4a-source"),
    )
    opened.connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(values["idempotency"]), "7g5e4a-idempotency"),
    )
    return values


def _native_memory(values, *, key: str, vector: np.ndarray):
    raw = np.asarray(vector, dtype=np.float32).reshape(-1)
    facade = NativeMemoryCompatibilityFacade(values["connection"])
    draft = facade.begin_memory_draft(
        legacy_source_namespace_id=values["source"],
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=key,
        identity_namespace_id=values["identity"],
        semantic_scope_id=values["scope"],
        summary=key,
        memory_type="episodic",
        strength=.5,
        confidence=.8,
        half_life_days=0.0,
        user_id="agent",
        logical_step=1,
        embedding_request=CompatibilityEmbeddingPublicationRequest(
            raw.tobytes(), "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
            dtype="float32", dimension=3,
        ),
    )
    return facade.finalize_memory_draft(draft).source


def _memory_graph_candidate_indices(scores: np.ndarray, top_k: int) -> np.ndarray:
    """The exact current fast-recall candidate and extraction law."""
    if scores.shape[0] <= top_k:
        return np.argsort(-scores)
    candidate_indices = np.argpartition(-scores, top_k - 1)[:top_k]
    return candidate_indices[np.argsort(-scores[candidate_indices])]


def test_native_durable_bytes_reconstruct_the_memory_graph_float32_matrix_and_scores(tmp_path: Path):
    vectors = (
        np.asarray((2.0, 0.6, 0.0), dtype=np.float32),
        np.asarray((1e-12, 3e-13, 0.0), dtype=np.float32),
        np.asarray((0.6, 0.8, 0.0), dtype=np.float32),
        np.asarray((-0.4, 0.9, 0.0), dtype=np.float32),
    )
    query = np.asarray((0.7, 0.4, 0.0), dtype=np.float32)
    graph = MemoryGraph(str(tmp_path / "legacy"), embedder=_ThreeDimensionalEmbedder())
    for index, vector in enumerate(vectors):
        graph.add_memory(
            summary=f"legacy-{index}", embedding=vector, mtype="episodic",
            strength=.5, confidence=.8, half_life_days=0.0, user_id="agent", step=index,
        )
    graph._ensure_index()
    assert graph._emb_mat is not None
    assert graph._emb_mat.dtype == np.float32
    assert graph._eid_list == sorted(graph._eid_list)

    values = _native_context(tmp_path)
    try:
        sources = tuple(
            _native_memory(values, key=f"native-{index}", vector=vector)
            for index, vector in enumerate(vectors)
        )
        reader = NativeCompatEmbeddingReader(values["connection"])
        native_rows = []
        for source in sources:
            qualified = reader.read_current(source.object_id, expected_dimension=3)
            assert qualified is not None
            # A future native runtime must retain these source witnesses beside
            # the row; the matrix itself deliberately holds no authority.
            native_rows.append((
                source.eid, source.object_id, source.revision_id,
                graph._normalize(qualified.float32_vector()),
            ))
        native_rows.sort(key=lambda row: row[0])
        reconstructed = np.stack([row[3] for row in native_rows], axis=0).astype(np.float32)

        assert np.array_equal(reconstructed, graph._emb_mat)
        normalized_query = graph._normalize(query)
        native_scores = (reconstructed @ normalized_query).astype(np.float32)
        legacy_scores = (graph._emb_mat @ normalized_query).astype(np.float32)
        assert np.array_equal(native_scores, legacy_scores)

        expected_indices = _memory_graph_candidate_indices(legacy_scores, top_k=2)
        legacy_hits = graph.search_by_embedding(query, top_k=2)
        assert [hit["eid"] for hit in legacy_hits] == [
            graph._eid_list[int(index)] for index in expected_indices
        ]

        # The existing durable compatibility search intentionally uses float64
        # normalisation without MemoryGraph's epsilon.  It is a correctness
        # reader, not a drop-in replacement for live vectorised recall.
        facade_hits = NativeMemoryCompatibilityFacade(values["connection"]).search_by_embedding(
            legacy_source_namespace_id=values["source"], embedding=query, dimension=3, top_k=4,
        )
        small_row = next(index for index, row in enumerate(native_rows) if row[0] == sources[1].eid)
        native_small_score = float(native_scores[small_row])
        facade_small_score = next(hit.raw_score for hit in facade_hits if hit.eid == sources[1].eid)
        assert abs(native_small_score - facade_small_score) > 1e-3
    finally:
        values["opened"].close()


def test_memory_graph_fast_recall_keeps_numpy_argpartition_tie_behavior(tmp_path: Path):
    graph = MemoryGraph(str(tmp_path / "ties"), embedder=_ThreeDimensionalEmbedder())
    for index in range(5):
        graph.add_memory(
            summary=f"tie-{index}",
            embedding=np.asarray((1.0, 0.0, 0.0) if index < 4 else (-1.0, 0.0, 0.0), dtype=np.float32),
            mtype="episodic", strength=.5, confidence=.8, half_life_days=0.0, user_id="agent", step=index,
        )
    graph._ensure_index()
    assert graph._emb_mat is not None
    query = graph._normalize(np.asarray((1.0, 0.0, 0.0), dtype=np.float32))
    scores = (graph._emb_mat @ query).astype(np.float32)
    expected_indices = _memory_graph_candidate_indices(scores, top_k=2)

    hits = graph.search_by_embedding(query, top_k=2)
    assert [hit["eid"] for hit in hits] == [
        graph._eid_list[int(index)] for index in expected_indices
    ]
