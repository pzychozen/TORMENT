"""Tests for the SQLite Sidecar Index (Phase 4).

Covers:
  - Table creation and schema
  - Mirror-write methods (index_node, index_event, index_motif, etc.)
  - Query helpers (recent, by motif, trajectory, archive search)
  - Rebuild from JSONL
  - Graceful degradation (engine works without SQLite)
  - Integration with MemoryGraph and ArchiveStore
"""
import json
import os
import shutil
import sys
import tempfile
import traceback

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.sqlite_index import IndexManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp():
    return tempfile.mkdtemp(prefix="torment_sqlite_test_")


# ---------------------------------------------------------------------------
# Test: Basic IndexManager
# ---------------------------------------------------------------------------

class TestIndexManagerBasic:
    def test_creates_database(self):
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            assert idx.available
            assert os.path.exists(idx.db_path)
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_index_node_and_query(self):
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            ok = idx.index_node(1, {
                "type": "episode",
                "memory_class": "core",
                "half_life": 30.0,
                "strength": 0.7,
                "confidence": 0.8,
                "summary": "Test memory about cats",
                "created_at": 10,
                "embedding_ref": {"shard": 0, "row": 5},
            })
            assert ok

            recent = idx.get_recent_memories(limit=10)
            assert len(recent) == 1
            assert recent[0]["eid"] == 1
            assert recent[0]["kind"] == "episode"
            assert recent[0]["summary"] == "Test memory about cats"
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_index_event(self):
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            ok = idx.index_event({
                "type": "MEMORY_CREATE",
                "step": 42,
                "eid": 7,
                "drift_score": -0.15,
            })
            assert ok

            events = idx.get_events_by_type("MEMORY_CREATE", limit=10)
            assert len(events) == 1
            assert events[0]["eid"] == 7
            assert events[0]["step"] == 42
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_index_motif_membership(self):
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            # Index a node first
            idx.index_node(10, {"type": "episode", "summary": "Motif member"})
            idx.index_node(11, {"type": "episode", "summary": "Another member"})

            # Add motif memberships
            idx.index_motif_membership(10, "motif_creative_0001", 0.85)
            idx.index_motif_membership(11, "motif_creative_0001", 0.72)

            results = idx.get_memories_by_motif("motif_creative_0001")
            assert len(results) == 2
            eids = {r["eid"] for r in results}
            assert eids == {10, 11}
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_index_trajectory(self):
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            idx.index_trajectory(step=100, eid=5, pos=(0.1, 0.2, 0.3), coh=0.85)
            idx.index_trajectory(step=101, eid=5, pos=(0.15, 0.25, 0.35), coh=0.82)
            idx.index_trajectory(step=200, eid=5, pos=(0.5, 0.5, 0.5), coh=0.70)

            results = idx.get_trajectory_range(100, 150)
            assert len(results) == 2
            assert results[0]["step"] == 100
            assert abs(results[0]["pos_x"] - 0.1) < 0.01
            idx.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: Archive Index
# ---------------------------------------------------------------------------

class TestArchiveIndex:
    def test_index_document_and_chunks(self):
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            idx.index_document({
                "doc_id": "doc_test_001",
                "title": "Machine Learning Basics",
                "source_type": "markdown",
                "chunk_count": 3,
                "token_count": 900,
            })
            idx.index_chunk({
                "chunk_id": "doc_test_001_chunk_0000",
                "doc_id": "doc_test_001",
                "chunk_index": 0,
                "token_count": 300,
                "section_path": ["Introduction", "Overview"],
                "embedding_ref": {"shard": 0, "row": 0},
            })
            idx.index_chunk({
                "chunk_id": "doc_test_001_chunk_0001",
                "doc_id": "doc_test_001",
                "chunk_index": 1,
                "token_count": 300,
                "section_path": ["Methods"],
            })

            results = idx.search_archive_metadata("Machine Learning")
            assert len(results) == 1
            assert results[0]["doc_id"] == "doc_test_001"

            chunks = idx.get_chunks_for_document("doc_test_001")
            assert len(chunks) == 2
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_delete_document_index(self):
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            idx.index_document({"doc_id": "doc_del", "title": "To Delete"})
            idx.index_chunk({"chunk_id": "doc_del_c0", "doc_id": "doc_del", "chunk_index": 0, "token_count": 100})
            idx.index_chunk({"chunk_id": "doc_del_c1", "doc_id": "doc_del", "chunk_index": 1, "token_count": 100})

            # Verify exists
            assert len(idx.search_archive_metadata("Delete")) == 1
            assert len(idx.get_chunks_for_document("doc_del")) == 2

            # Delete
            ok = idx.delete_document_index("doc_del")
            assert ok

            # Verify gone
            assert len(idx.search_archive_metadata("Delete")) == 0
            assert len(idx.get_chunks_for_document("doc_del")) == 0
            idx.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: Rebuild from JSONL
# ---------------------------------------------------------------------------

class TestRebuild:
    def test_rebuild_from_jsonl(self):
        tmp = _tmp()
        try:
            # Create fake JSONL files
            nodes_path = os.path.join(tmp, "nodes.jsonl")
            events_path = os.path.join(tmp, "events.jsonl")
            docs_path = os.path.join(tmp, "documents.jsonl")
            chunks_path = os.path.join(tmp, "chunks.jsonl")

            with open(nodes_path, "w") as f:
                for i in range(5):
                    json.dump({
                        "eid": i,
                        "born_step": i * 10,
                        "payload": {
                            "type": "episode",
                            "summary": f"Memory {i}",
                            "half_life": 30.0,
                            "strength": 0.5 + i * 0.1,
                            "memory_class": "core",
                        }
                    }, f)
                    f.write("\n")

            with open(events_path, "w") as f:
                json.dump({"type": "MEMORY_CREATE", "step": 0, "eid": 0, "ts": 1000}, f)
                f.write("\n")
                json.dump({"type": "MEMORY_CREATE", "step": 10, "eid": 1, "ts": 1001}, f)
                f.write("\n")

            with open(docs_path, "w") as f:
                json.dump({"doc_id": "doc_1", "title": "Test Doc", "source_type": "text", "chunk_count": 1, "token_count": 100}, f)
                f.write("\n")

            with open(chunks_path, "w") as f:
                json.dump({"chunk_id": "doc_1_c0", "doc_id": "doc_1", "chunk_index": 0, "token_count": 100}, f)
                f.write("\n")

            # Rebuild
            idx_dir = os.path.join(tmp, "index")
            idx = IndexManager(idx_dir)
            counts = idx.rebuild_from_jsonl(
                nodes_path=nodes_path,
                events_path=events_path,
                archive_documents_path=docs_path,
                archive_chunks_path=chunks_path,
            )

            assert counts["core_nodes"] == 5
            assert counts["core_events"] == 2
            assert counts["documents"] == 1
            assert counts["chunks"] == 1

            # Verify query works
            recent = idx.get_recent_memories(limit=10)
            assert len(recent) == 5
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_rebuild_survives_deletion(self):
        """Index can be deleted and rebuilt."""
        tmp = _tmp()
        try:
            idx_dir = os.path.join(tmp, "index")
            idx = IndexManager(idx_dir)
            idx.index_node(1, {"type": "test", "summary": "Before delete"})
            assert len(idx.get_recent_memories()) == 1
            db_path = idx.db_path
            idx.close()

            # Delete the database
            os.remove(db_path)
            assert not os.path.exists(db_path)

            # Recreate — should start fresh
            idx2 = IndexManager(idx_dir)
            assert idx2.available
            assert len(idx2.get_recent_memories()) == 0
            idx2.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: Graceful Degradation
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    def test_memory_graph_works_without_sqlite(self):
        """MemoryGraph works fine when sqlite_index=None."""
        from torment_service.memory_graph import MemoryGraph
        from torment_service.embeddings import HashEmbedding

        tmp = _tmp()
        try:
            g = MemoryGraph(os.path.join(tmp, "graph"), embedder=HashEmbedding(), sqlite_index=None)
            emb = np.random.randn(384).astype(np.float32)
            eid = g.add_memory("test no sqlite", emb, "episode", 0.5, 0.5, 30.0)
            assert eid > 0
            ent = g.entities[eid]
            assert ent.payload["summary"] == "test no sqlite"
        finally:
            shutil.rmtree(tmp)

    def test_archive_works_without_sqlite(self):
        """ArchiveStore works fine when sqlite_index=None."""
        from torment_service.archive_memory import ArchiveStore
        from torment_service.embeddings import HashEmbedding

        tmp = _tmp()
        try:
            store = ArchiveStore(os.path.join(tmp, "archive"), embedder=HashEmbedding(), sqlite_index=None)
            result = store.ingest_document("Test content " * 20, title="Test")
            assert result["chunk_count"] > 0
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: Integration (MemoryGraph + SQLite mirror)
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_memory_graph_mirrors_to_sqlite(self):
        """When sqlite_index is provided, writes are mirrored."""
        from torment_service.memory_graph import MemoryGraph
        from torment_service.embeddings import HashEmbedding

        tmp = _tmp()
        try:
            idx_dir = os.path.join(tmp, "index")
            idx = IndexManager(idx_dir)

            g = MemoryGraph(
                os.path.join(tmp, "graph"),
                embedder=HashEmbedding(),
                sqlite_index=idx,
            )
            emb = np.random.randn(384).astype(np.float32)
            eid = g.add_memory("mirrored memory", emb, "episode", 0.7, 0.8, 30.0)

            # Check mirror
            recent = idx.get_recent_memories(limit=10)
            assert len(recent) >= 1
            found = any(r["eid"] == eid for r in recent)
            assert found, f"eid {eid} not found in SQLite index"

            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_archive_mirrors_to_sqlite(self):
        """When sqlite_index is provided, archive writes are mirrored."""
        from torment_service.archive_memory import ArchiveStore
        from torment_service.embeddings import HashEmbedding

        tmp = _tmp()
        try:
            idx_dir = os.path.join(tmp, "index")
            idx = IndexManager(idx_dir)

            store = ArchiveStore(
                os.path.join(tmp, "archive"),
                embedder=HashEmbedding(),
                sqlite_index=idx,
            )
            result = store.ingest_document(
                "Integration test content. " * 30,
                title="Integration Doc",
                doc_id="doc_int_001",
            )
            assert result["chunk_count"] > 0

            # Check document mirror
            docs = idx.search_archive_metadata("Integration")
            assert len(docs) == 1
            assert docs[0]["doc_id"] == "doc_int_001"

            # Check chunk mirror
            chunks = idx.get_chunks_for_document("doc_int_001")
            assert len(chunks) == result["chunk_count"]

            # Test delete mirror
            store.delete_document("doc_int_001")
            assert len(idx.search_archive_metadata("Integration")) == 0
            assert len(idx.get_chunks_for_document("doc_int_001")) == 0

            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_index_stats(self):
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            idx.index_node(1, {"type": "test", "summary": "Stats test"})
            idx.index_event({"type": "TEST_EVENT", "step": 0, "eid": 1})

            stats = idx.get_index_stats()
            assert stats["core_nodes"] == 1
            assert stats["core_events"] == 1
            assert stats["db_size_bytes"] > 0
            idx.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_phase4_tests():
    """Run all Phase 4 tests and report results."""
    tests = [
        ("P4.1 Create database", TestIndexManagerBasic().test_creates_database),
        ("P4.2 Index node + query", TestIndexManagerBasic().test_index_node_and_query),
        ("P4.3 Index event", TestIndexManagerBasic().test_index_event),
        ("P4.4 Index motif membership", TestIndexManagerBasic().test_index_motif_membership),
        ("P4.5 Index trajectory", TestIndexManagerBasic().test_index_trajectory),
        ("P4.6 Archive doc + chunks", TestArchiveIndex().test_index_document_and_chunks),
        ("P4.7 Archive delete", TestArchiveIndex().test_delete_document_index),
        ("P4.8 Rebuild from JSONL", TestRebuild().test_rebuild_from_jsonl),
        ("P4.9 Rebuild survives deletion", TestRebuild().test_rebuild_survives_deletion),
        ("P4.10 MemoryGraph without SQLite", TestGracefulDegradation().test_memory_graph_works_without_sqlite),
        ("P4.11 Archive without SQLite", TestGracefulDegradation().test_archive_works_without_sqlite),
        ("P4.12 MemoryGraph mirrors to SQLite", TestIntegration().test_memory_graph_mirrors_to_sqlite),
        ("P4.13 Archive mirrors to SQLite", TestIntegration().test_archive_mirrors_to_sqlite),
        ("P4.14 Index stats", TestIntegration().test_index_stats),
    ]

    passed = 0
    failed = 0
    print("\n--- Phase 4 (SQLite Sidecar Index) ---")
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
            passed += 1
        except Exception:
            print(f"  FAIL: {name}")
            traceback.print_exc()
            failed += 1

    return passed, failed


if __name__ == "__main__":
    p, f = run_phase4_tests()
    print(f"\nPhase 4: {p} passed, {f} failed")
    if f > 0:
        exit(1)
