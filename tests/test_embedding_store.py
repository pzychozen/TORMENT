"""Tests for embedding shard storage system (Phase 1)."""
import json
import os
import shutil
import tempfile

import numpy as np
import pytest

from torment_service.embedding_store import (
    EmbeddingShardWriter,
    EmbeddingShardReader,
    load_embedding,
    ROWS_PER_SHARD,
)


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp(prefix="torment_emb_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# -------------------------------------------------------
# EmbeddingShardWriter
# -------------------------------------------------------

class TestShardWriter:
    def test_create_manifest(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=384)
        assert os.path.exists(os.path.join(emb_dir, "manifest.json"))
        assert writer.manifest["embedding_dim"] == 384
        assert writer.manifest["total_rows"] == 0

    def test_append_single(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=8)
        vec = np.random.randn(8).astype(np.float32)

        ref = writer.append(vec, eid=1, memory_class="core", kind="episode", step=0)

        assert ref["shard"] == 0
        assert ref["row"] == 0
        assert ref["dim"] == 8
        assert writer.total_rows == 1

    def test_append_multiple(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=8)

        refs = []
        for i in range(10):
            vec = np.random.randn(8).astype(np.float32)
            ref = writer.append(vec, eid=i, memory_class="core", step=i)
            refs.append(ref)

        assert writer.total_rows == 10
        assert refs[0]["row"] == 0
        assert refs[9]["row"] == 9

        # Verify map file
        map_path = os.path.join(emb_dir, "shard_000000.map.jsonl")
        assert os.path.exists(map_path)
        with open(map_path, "r") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert len(lines) == 10
        assert lines[0]["eid"] == 0
        assert lines[9]["eid"] == 9

    def test_dim_padding(self, tmp_dir):
        """Short vectors get zero-padded to match shard dim."""
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=8)
        short_vec = np.array([1.0, 2.0, 3.0], dtype=np.float32)

        ref = writer.append(short_vec, eid=1)
        assert ref["dim"] == 8

        # Read back and verify padding
        reader = EmbeddingShardReader(emb_dir)
        loaded = reader.load_one(ref)
        assert loaded is not None
        assert loaded.shape == (8,)
        np.testing.assert_almost_equal(loaded[:3], short_vec)
        np.testing.assert_almost_equal(loaded[3:], 0.0)

    def test_dim_truncation(self, tmp_dir):
        """Long vectors get truncated to match shard dim."""
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=4)
        long_vec = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float32)

        ref = writer.append(long_vec, eid=1)

        reader = EmbeddingShardReader(emb_dir)
        loaded = reader.load_one(ref)
        assert loaded is not None
        assert loaded.shape == (4,)
        np.testing.assert_almost_equal(loaded, long_vec[:4])


# -------------------------------------------------------
# EmbeddingShardReader
# -------------------------------------------------------

class TestShardReader:
    def test_load_one(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=8)
        vec = np.random.randn(8).astype(np.float32)
        ref = writer.append(vec, eid=42, memory_class="core")

        reader = EmbeddingShardReader(emb_dir)
        loaded = reader.load_one(ref)
        assert loaded is not None
        np.testing.assert_array_almost_equal(loaded, vec, decimal=5)

    def test_load_nonexistent(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=8)  # create manifest

        reader = EmbeddingShardReader(emb_dir)
        result = reader.load_one({"shard": 99, "row": 0, "dim": 8})
        assert result is None

    def test_load_all_for_class(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=4)

        # Write 3 core, 2 archive
        for i in range(3):
            writer.append(np.ones(4) * (i + 1), eid=i, memory_class="core")
        for i in range(2):
            writer.append(np.ones(4) * (i + 10), eid=100 + i, memory_class="archive")

        reader = EmbeddingShardReader(emb_dir)
        core_items = reader.load_all_for_class("core")
        archive_items = reader.load_all_for_class("archive")

        assert len(core_items) == 3
        assert len(archive_items) == 2
        assert core_items[0][0] == 0  # eid
        assert archive_items[0][0] == 100

    def test_eid_to_ref_map(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=4)

        writer.append(np.ones(4), eid=10)
        writer.append(np.ones(4), eid=20)
        writer.append(np.ones(4), eid=30)

        reader = EmbeddingShardReader(emb_dir)
        mapping = reader.get_eid_to_ref_map()
        assert 10 in mapping
        assert 20 in mapping
        assert 30 in mapping
        assert mapping[10]["row"] == 0
        assert mapping[20]["row"] == 1
        assert mapping[30]["row"] == 2

    def test_not_available_when_empty(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "nonexistent")
        reader = EmbeddingShardReader(emb_dir)
        assert not reader.available


# -------------------------------------------------------
# Shard rotation
# -------------------------------------------------------

class TestShardRotation:
    def test_rotate_when_full(self, tmp_dir):
        """Shard rotates to next file when rows_per_shard is reached."""
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=4)
        # Override rows_per_shard to small value for testing
        writer.manifest["rows_per_shard"] = 3
        writer._save_manifest()

        refs = []
        for i in range(5):
            ref = writer.append(np.ones(4) * i, eid=i)
            refs.append(ref)

        # First 3 in shard 0, next 2 in shard 1
        assert refs[0]["shard"] == 0
        assert refs[2]["shard"] == 0
        assert refs[3]["shard"] == 1
        assert refs[3]["row"] == 0
        assert refs[4]["shard"] == 1
        assert refs[4]["row"] == 1

        # Verify both shards readable
        reader = EmbeddingShardReader(emb_dir)
        for i, ref in enumerate(refs):
            vec = reader.load_one(ref)
            assert vec is not None
            np.testing.assert_almost_equal(vec[0], float(i))


# -------------------------------------------------------
# Universal loader (shard + legacy fallback)
# -------------------------------------------------------

class TestUniversalLoader:
    def test_load_from_shard(self, tmp_dir):
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=4)
        vec = np.array([1, 2, 3, 4], dtype=np.float32)
        ref = writer.append(vec, eid=1)

        reader = EmbeddingShardReader(emb_dir)
        payload = {"embedding_ref": ref}
        loaded = load_embedding(1, payload, reader, tmp_dir)
        assert loaded is not None
        np.testing.assert_array_almost_equal(loaded, vec)

    def test_fallback_to_legacy(self, tmp_dir):
        # Create legacy file
        vec = np.array([5, 6, 7, 8], dtype=np.float32)
        np.save(os.path.join(tmp_dir, "emb_42.npy"), vec)

        # No shard reader, no embedding_ref
        loaded = load_embedding(42, {}, None, tmp_dir)
        assert loaded is not None
        np.testing.assert_array_almost_equal(loaded, vec)

    def test_shard_preferred_over_legacy(self, tmp_dir):
        """When both exist, shard takes precedence."""
        # Create legacy file with different values
        legacy_vec = np.array([1, 1, 1, 1], dtype=np.float32)
        np.save(os.path.join(tmp_dir, "emb_1.npy"), legacy_vec)

        # Create shard with different values
        emb_dir = os.path.join(tmp_dir, "embeddings")
        writer = EmbeddingShardWriter(emb_dir, dim=4)
        shard_vec = np.array([9, 9, 9, 9], dtype=np.float32)
        ref = writer.append(shard_vec, eid=1)

        reader = EmbeddingShardReader(emb_dir)
        payload = {"embedding_ref": ref}
        loaded = load_embedding(1, payload, reader, tmp_dir)
        # Should get shard version
        np.testing.assert_array_almost_equal(loaded, shard_vec)

    def test_missing_returns_none(self, tmp_dir):
        loaded = load_embedding(999, {}, None, tmp_dir)
        assert loaded is None


# -------------------------------------------------------
# memory_class field
# -------------------------------------------------------

class TestMemoryClass:
    def test_memory_class_in_node_payload(self, tmp_dir):
        """Verify spawn_memory adds memory_class to payload."""
        from torment_service.memory_graph import MemoryGraph

        graph = MemoryGraph(data_dir=tmp_dir)
        vec = np.random.randn(graph._emb_dim).astype(np.float32)

        eid = graph.spawn_memory(
            summary="test memory",
            embedding=vec,
            mtype="memory",
            strength=0.5,
            confidence=0.5,
            half_life_days=7.0,
            memory_class="core",
        )
        graph.flush_node(eid)

        ent = graph.entities[eid]
        assert ent.payload.get("memory_class") == "core"

    def test_memory_class_defaults_to_core(self, tmp_dir):
        """Without explicit memory_class, defaults to core."""
        from torment_service.memory_graph import MemoryGraph

        graph = MemoryGraph(data_dir=tmp_dir)
        vec = np.random.randn(graph._emb_dim).astype(np.float32)

        eid = graph.spawn_memory(
            summary="default class test",
            embedding=vec,
            mtype="memory",
            strength=0.5,
            confidence=0.5,
            half_life_days=7.0,
        )

        ent = graph.entities[eid]
        assert ent.payload.get("memory_class") == "core"

    def test_archive_class_stored(self, tmp_dir):
        """Archive memory_class is stored correctly."""
        from torment_service.memory_graph import MemoryGraph

        graph = MemoryGraph(data_dir=tmp_dir)
        vec = np.random.randn(graph._emb_dim).astype(np.float32)

        eid = graph.spawn_memory(
            summary="document chunk",
            embedding=vec,
            mtype="archive_chunk",
            strength=0.3,
            confidence=0.8,
            half_life_days=30.0,
            memory_class="archive",
        )

        ent = graph.entities[eid]
        assert ent.payload.get("memory_class") == "archive"


# -------------------------------------------------------
# Integration: MemoryGraph with shard storage
# -------------------------------------------------------

class TestMemoryGraphShardIntegration:
    def test_spawn_creates_shard(self, tmp_dir):
        """spawn_memory writes to shard, not legacy file."""
        from torment_service.memory_graph import MemoryGraph

        graph = MemoryGraph(data_dir=tmp_dir)
        vec = np.random.randn(graph._emb_dim).astype(np.float32)

        eid = graph.spawn_memory(
            summary="shard test",
            embedding=vec,
            mtype="memory",
            strength=0.5,
            confidence=0.5,
            half_life_days=7.0,
        )

        # Should have embedding_ref in payload
        ref = graph.entities[eid].payload.get("embedding_ref")
        assert ref is not None
        assert "shard" in ref
        assert "row" in ref

        # Shard file should exist
        shard_path = os.path.join(tmp_dir, "embeddings", "shard_000000.npy")
        assert os.path.exists(shard_path)

        # Legacy file should NOT exist
        legacy_path = os.path.join(tmp_dir, f"emb_{eid}.npy")
        assert not os.path.exists(legacy_path)

    def test_search_works_with_shards(self, tmp_dir):
        """Vector search still works after shard migration."""
        from torment_service.memory_graph import MemoryGraph

        graph = MemoryGraph(data_dir=tmp_dir)

        # Add several memories
        for i in range(5):
            vec = np.random.randn(graph._emb_dim).astype(np.float32)
            graph.spawn_memory(
                summary=f"memory {i}",
                embedding=vec,
                mtype="memory",
                strength=0.5,
                confidence=0.5,
                half_life_days=7.0,
            )
            graph.flush_node(i + 1)

        results = graph.search("test query", top_k=3)
        assert len(results) > 0  # Should find something

    def test_reload_with_shards(self, tmp_dir):
        """Graph can be reloaded and embeddings are still accessible."""
        from torment_service.memory_graph import MemoryGraph

        # Create graph and add memories
        graph1 = MemoryGraph(data_dir=tmp_dir)
        vec = np.random.randn(graph1._emb_dim).astype(np.float32)
        eid = graph1.spawn_memory(
            summary="persistence test",
            embedding=vec,
            mtype="memory",
            strength=0.5,
            confidence=0.5,
            half_life_days=7.0,
        )
        graph1.flush_node(eid)

        # Reload from disk
        graph2 = MemoryGraph(data_dir=tmp_dir)
        assert eid in graph2.entities
        ref = graph2.entities[eid].payload.get("embedding_ref")
        assert ref is not None

        # Search should still work
        results = graph2.search("persistence test", top_k=1)
        assert len(results) > 0


# -------------------------------------------------------
# Migration script
# -------------------------------------------------------

class TestMigrationScript:
    def test_migrate_legacy_to_shards(self, tmp_dir):
        """Migration script converts emb_*.npy to shard storage."""
        from tools.migrate_embeddings_to_shards import migrate_graph

        # Create a fake graph directory with legacy embeddings
        graph_dir = os.path.join(tmp_dir, "test_graph")
        os.makedirs(graph_dir, exist_ok=True)

        # Write legacy embeddings
        dim = 8
        for eid in range(5):
            vec = np.random.randn(dim).astype(np.float32)
            np.save(os.path.join(graph_dir, f"emb_{eid}.npy"), vec)

        # Write nodes.jsonl
        nodes_path = os.path.join(graph_dir, "nodes.jsonl")
        with open(nodes_path, "w") as f:
            for eid in range(5):
                node = {
                    "eid": eid,
                    "born_step": 0,
                    "channel": 0,
                    "payload": {"summary": f"memory {eid}", "type": "memory"},
                }
                f.write(json.dumps(node) + "\n")

        # Run migration
        report = migrate_graph(graph_dir)
        assert report["migrated"] == 5
        assert report["errors"] == 0

        # Legacy files should be moved
        for eid in range(5):
            assert not os.path.exists(os.path.join(graph_dir, f"emb_{eid}.npy"))
            assert os.path.exists(
                os.path.join(graph_dir, "legacy_embeddings", f"emb_{eid}.npy")
            )

        # Shard storage should exist
        assert os.path.exists(os.path.join(graph_dir, "embeddings", "manifest.json"))
        assert os.path.exists(os.path.join(graph_dir, "embeddings", "shard_000000.npy"))

        # Nodes should have embedding_ref and memory_class
        with open(nodes_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                node = json.loads(line)
                payload = node.get("payload", {})
                assert "embedding_ref" in payload
                assert payload.get("memory_class") == "core"

    def test_migration_idempotent(self, tmp_dir):
        """Running migration twice doesn't duplicate or break anything."""
        from tools.migrate_embeddings_to_shards import migrate_graph

        graph_dir = os.path.join(tmp_dir, "test_graph")
        os.makedirs(graph_dir, exist_ok=True)

        dim = 4
        for eid in range(3):
            np.save(os.path.join(graph_dir, f"emb_{eid}.npy"),
                     np.random.randn(dim).astype(np.float32))

        nodes_path = os.path.join(graph_dir, "nodes.jsonl")
        with open(nodes_path, "w") as f:
            for eid in range(3):
                f.write(json.dumps({
                    "eid": eid, "born_step": 0, "channel": 0,
                    "payload": {"summary": f"mem {eid}", "type": "memory"},
                }) + "\n")

        # First run
        r1 = migrate_graph(graph_dir)
        assert r1["migrated"] == 3

        # Second run — legacy files moved, nothing left to find or migrate
        r2 = migrate_graph(graph_dir)
        assert r2["migrated"] == 0
        assert r2["legacy_found"] == 0  # files already moved to legacy_embeddings/
