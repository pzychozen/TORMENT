"""Regression tests for deep_memory.py path-expression hardening.

Covers:
  1. Canonical deep-memory root is stable and absolute
  2. memories.jsonl path stays inside root
  3. embeddings/ path stays inside root
  4. Traversal / escaped roots are rejected
  5. Export/query still work after refactor
"""

import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

from torment_service.deep_memory import DeepMemoryStore


class TestDeepMemoryRootCanonicalization(unittest.TestCase):
    """1. Canonical deep-memory root is stable and absolute."""

    def test_root_is_absolute(self):
        with tempfile.TemporaryDirectory() as td:
            with DeepMemoryStore(Path(td), dim=8) as store:
                self.assertTrue(os.path.isabs(str(store.base_dir)))

    def test_root_is_stable(self):
        with tempfile.TemporaryDirectory() as td:
            with DeepMemoryStore(Path(td), dim=8) as s1, \
                    DeepMemoryStore(Path(td), dim=8) as s2:
                self.assertEqual(str(s1.base_dir), str(s2.base_dir))

    def test_root_resolves_symlinks(self):
        with tempfile.TemporaryDirectory() as td:
            real_dir = os.path.join(td, "real")
            os.makedirs(real_dir)
            link_dir = os.path.join(td, "link")
            os.symlink(real_dir, link_dir)
            with DeepMemoryStore(Path(link_dir), dim=8) as store:
                self.assertEqual(str(store.base_dir), os.path.realpath(real_dir))


class TestDeepMemoryChildPaths(unittest.TestCase):
    """2, 3. Child paths stay inside root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.store = DeepMemoryStore(Path(self._tmpdir), dim=8)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_memories_path_inside_root(self):
        """2. memories.jsonl path stays inside root."""
        root = str(self.store.base_dir)
        mem_path = str(self.store.memories_path)
        self.assertTrue(
            mem_path.startswith(root + os.sep),
            f"memories_path {mem_path} not inside root {root}",
        )

    def test_emb_dir_inside_root(self):
        """3. embeddings/ path stays inside root."""
        root = str(self.store.base_dir)
        self.assertTrue(
            self.store.emb_dir.startswith(root + os.sep),
            f"emb_dir {self.store.emb_dir} not inside root {root}",
        )

    def test_memories_filename_correct(self):
        self.assertTrue(str(self.store.memories_path).endswith("memories.jsonl"))

    def test_emb_dir_name_correct(self):
        self.assertTrue(self.store.emb_dir.endswith("embeddings"))


class TestDeepMemoryExportQuery(unittest.TestCase):
    """5. Export/query still work after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.store = DeepMemoryStore(Path(self._tmpdir), dim=8)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_export_and_recall(self):
        """Export a memory, then recall it by EID."""
        from unittest.mock import MagicMock
        candidate = MagicMock()
        candidate.eid = 42
        candidate.born_step = 10
        candidate.summary = "test deep memory"
        candidate.score = 0.75
        candidate.motif_id = None
        candidate.memory_class = "core"

        vec = np.random.randn(8).astype(np.float32)
        mem = self.store.export(candidate, vec, {"type": "episode"}, step=101)

        self.assertEqual(mem.eid, 42)
        self.assertEqual(mem.summary, "test deep memory")

        recalled = self.store.recall(42)
        self.assertIsNotNone(recalled)
        self.assertEqual(recalled.eid, 42)

    def test_query_returns_results(self):
        """Export a memory with embedding, then query for it."""
        from unittest.mock import MagicMock
        candidate = MagicMock()
        candidate.eid = 1
        candidate.born_step = 1
        candidate.summary = "searchable memory"
        candidate.score = 0.5
        candidate.motif_id = None
        candidate.memory_class = "core"

        vec = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32)
        self.store.export(candidate, vec, {}, step=102)

        results = self.store.query(vec, top_k=5, min_similarity=0.1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].eid, 1)

    def test_stats_after_export(self):
        """Stats reflect exported memory."""
        from unittest.mock import MagicMock
        candidate = MagicMock()
        candidate.eid = 99
        candidate.born_step = 5
        candidate.summary = "stats test"
        candidate.score = 0.3
        candidate.motif_id = None
        candidate.memory_class = "core"

        self.store.export(candidate, np.zeros(8, dtype=np.float32), {}, step=103)
        s = self.store.stats()
        self.assertEqual(s["count"], 1)
        self.assertTrue(s["has_embeddings"])


class TestDeepMemoryTrustedRoot(unittest.TestCase):
    """4b. trusted_root containment prevents path traversal."""

    def test_valid_child_of_trusted_root(self):
        """Normal path under trusted root works."""
        with tempfile.TemporaryDirectory() as td:
            child = os.path.join(td, "agents", "a1", "deep_memory")
            os.makedirs(child)
            with DeepMemoryStore(Path(child), dim=8, trusted_root=td) as store:
                self.assertTrue(str(store.base_dir).startswith(os.path.realpath(td)))

    def test_traversal_escapes_trusted_root(self):
        """'../escape' under trusted root raises ValueError."""
        with tempfile.TemporaryDirectory() as td:
            inner = os.path.join(td, "inner")
            os.makedirs(inner)
            # Attempt to escape inner via ../
            bad = os.path.join(inner, "..", "escape")
            with self.assertRaises(ValueError):
                DeepMemoryStore(Path(bad), dim=8, trusted_root=inner)

    def test_sibling_dir_rejected(self):
        """A path outside the trusted root is rejected even if absolute."""
        with tempfile.TemporaryDirectory() as td:
            trusted = os.path.join(td, "trusted")
            sibling = os.path.join(td, "sibling")
            os.makedirs(trusted)
            os.makedirs(sibling)
            with self.assertRaises(ValueError):
                DeepMemoryStore(Path(sibling), dim=8, trusted_root=trusted)

    def test_trusted_root_equal_to_base_dir(self):
        """trusted_root == base_dir is allowed (root itself)."""
        with tempfile.TemporaryDirectory() as td:
            with DeepMemoryStore(Path(td), dim=8, trusted_root=td) as store:
                self.assertEqual(
                    str(store.base_dir), os.path.realpath(td),
                )

    def test_nested_slash_in_component_rejected(self):
        """Paths with embedded slashes that resolve outside root are rejected."""
        with tempfile.TemporaryDirectory() as td:
            # realpath resolves ".." so the result is outside td/inner
            inner = os.path.join(td, "inner")
            os.makedirs(inner)
            bad = os.path.join(inner, "..", "..", "tmp", "pwned")
            with self.assertRaises(ValueError):
                DeepMemoryStore(Path(bad), dim=8, trusted_root=inner)


if __name__ == "__main__":
    unittest.main()
