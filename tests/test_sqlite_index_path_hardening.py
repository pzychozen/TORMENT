"""Regression tests for sqlite_index.py path-expression hardening.

Covers:
  1. Canonical index dir is stable and absolute
  2. db_path stays inside canonical index root
  3. Default DB filename remains memory_index.sqlite
  4. Index initialization and stats still work after refactor
"""

import os
import shutil
import tempfile
import unittest

from torment_service.sqlite_index import IndexManager


class TestIndexManagerPathIntegrity(unittest.TestCase):
    """1, 2, 3. Paths are canonical and contained."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.idx = IndexManager(self._tmpdir)

    def tearDown(self):
        if self.idx._conn:
            self.idx._conn.close()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_index_dir_is_canonical(self):
        self.assertTrue(os.path.isabs(self.idx.index_dir))
        self.assertEqual(self.idx.index_dir, os.path.realpath(self.idx.index_dir))

    def test_db_path_inside_index_dir(self):
        self.assertTrue(
            self.idx.db_path.startswith(self.idx.index_dir + os.sep),
            f"db_path {self.idx.db_path} not inside {self.idx.index_dir}",
        )

    def test_db_path_correct_name(self):
        self.assertTrue(self.idx.db_path.endswith("memory_index.sqlite"))

    def test_index_dir_created(self):
        self.assertTrue(os.path.isdir(self.idx.index_dir))

    def test_db_file_created(self):
        self.assertTrue(os.path.exists(self.idx.db_path))


class TestIndexManagerBehavior(unittest.TestCase):
    """4. Init and stats still work after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.idx = IndexManager(self._tmpdir)

    def tearDown(self):
        if self.idx._conn:
            self.idx._conn.close()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_get_index_stats(self):
        stats = self.idx.get_index_stats()
        self.assertIn("core_nodes", stats)
        self.assertEqual(stats["core_nodes"], 0)

    def test_index_node_and_query(self):
        """Basic write + read round trip."""
        payload = {
            "kind": "episode",
            "tier": "situational",
            "memory_class": "core",
            "step": 10,
            "half_life_days": 7.0,
            "coherence": 0.5,
            "strength": 0.8,
            "confidence": 0.9,
            "summary": "test memory",
            "embedding_ref": {"shard": 0, "row": 0, "dim": 384},
        }
        self.idx.index_node(eid=1, payload=payload)
        stats = self.idx.get_index_stats()
        self.assertEqual(stats["core_nodes"], 1)

    def test_fresh_index_loads_cleanly(self):
        with tempfile.TemporaryDirectory() as td:
            idx = IndexManager(td)
            stats = idx.get_index_stats()
            self.assertEqual(stats["core_nodes"], 0)
            idx._conn.close()


if __name__ == "__main__":
    unittest.main()
