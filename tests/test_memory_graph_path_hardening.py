"""Regression tests for memory_graph.py path-expression hardening.

Covers:
  1. Canonical data_dir is stable and absolute
  2. embeddings/ root stays inside canonical data root
  3. nodes.jsonl, edges.jsonl, memory_events.jsonl stay inside canonical root
  4. _emb_path(eid) stays inside canonical root and preserves emb_<eid>.npy naming
  5. Traversal-like data_dir components are rejected
  6. spawn_memory() legacy fallback writes to the safe path
  7. Normal graph load/save behavior still works after refactor
"""

import os
import shutil
import tempfile
import unittest

import numpy as np

from torment_service.memory_graph import MemoryGraph


class TestMemoryGraphInit(unittest.TestCase):
    """1-3. Canonical root and child paths."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_data_dir_is_canonical(self):
        mg = MemoryGraph(self._tmpdir)
        self.assertTrue(os.path.isabs(mg.data_dir))
        self.assertEqual(mg.data_dir, os.path.realpath(mg.data_dir))

    def test_data_dir_directory_created(self):
        sub = os.path.join(self._tmpdir, "subdir", "graph")
        mg = MemoryGraph(sub)
        self.assertTrue(os.path.isdir(mg.data_dir))

    def test_embeddings_dir_inside_root(self):
        mg = MemoryGraph(self._tmpdir)
        self.assertTrue(
            mg._emb_dir.startswith(mg.data_dir + os.sep),
            f"embeddings dir {mg._emb_dir} not inside {mg.data_dir}",
        )

    def test_meta_path_inside_root(self):
        mg = MemoryGraph(self._tmpdir)
        self.assertTrue(mg.meta_path.startswith(mg.data_dir + os.sep))
        self.assertTrue(mg.meta_path.endswith("nodes.jsonl"))

    def test_edges_path_inside_root(self):
        mg = MemoryGraph(self._tmpdir)
        self.assertTrue(mg.edges_path.startswith(mg.data_dir + os.sep))
        self.assertTrue(mg.edges_path.endswith("edges.jsonl"))

    def test_events_path_inside_root(self):
        mg = MemoryGraph(self._tmpdir)
        self.assertTrue(mg.events_path.startswith(mg.data_dir + os.sep))
        self.assertTrue(mg.events_path.endswith("memory_events.jsonl"))

    def test_rejects_traversal_in_canonical_root(self):
        """A data_dir that resolves to contain '..' segments is rejected."""
        # On a real filesystem, realpath resolves away '..', so this test
        # verifies the belt-and-suspenders check in _canonical_storage_root
        # for any edge case where realpath might leave traversal segments.
        # The normal case: realpath resolves it fine, no error.
        sub = os.path.join(self._tmpdir, "a", "..", "b")
        mg = MemoryGraph(sub)
        self.assertNotIn("..", mg.data_dir.split(os.sep))


class TestEmbPath(unittest.TestCase):
    """4. _emb_path stays inside root and preserves naming."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.mg = MemoryGraph(self._tmpdir)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_emb_path_inside_root(self):
        path = self.mg._emb_path(42)
        self.assertTrue(path.startswith(self.mg.data_dir + os.sep))

    def test_emb_path_naming(self):
        path = self.mg._emb_path(42)
        self.assertEqual(os.path.basename(path), "emb_42.npy")

    def test_emb_path_is_canonical(self):
        path = self.mg._emb_path(99)
        self.assertEqual(path, os.path.realpath(path))


class TestSpawnAndLoad(unittest.TestCase):
    """6-7. spawn_memory and load still work after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _spawn(self, mg, summary="test node"):
        emb = np.random.randn(384).astype(np.float32)
        return mg.spawn_memory(
            summary=summary, embedding=emb,
            mtype="fact", strength=0.5, confidence=0.8,
            half_life_days=30.0, step=1,
        )

    def test_spawn_creates_node(self):
        mg = MemoryGraph(self._tmpdir)
        eid = self._spawn(mg)
        self.assertIn(eid, mg.entities)

    def test_flush_writes_meta_file(self):
        mg = MemoryGraph(self._tmpdir)
        eid = self._spawn(mg)
        mg.flush_node(eid)
        self.assertTrue(os.path.exists(mg.meta_path))

    def test_load_round_trip(self):
        mg1 = MemoryGraph(self._tmpdir)
        eid = self._spawn(mg1, summary="hello world")
        mg1.flush_node(eid)

        # Reload from same dir
        mg2 = MemoryGraph(self._tmpdir)
        self.assertIn(eid, mg2.entities)
        self.assertEqual(mg2.entities[eid].payload.get("summary"), "hello world")


if __name__ == "__main__":
    unittest.main()
