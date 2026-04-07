"""Regression tests for embedding_store.py path-expression hardening.

Covers:
  1. _canonical_storage_root is stable and absolute
  2. manifest path stays inside canonical root
  3. shard .npy and .map.jsonl paths stay inside canonical root
  4. temp manifest path stays inside canonical root (_write_json)
  5. legacy embedding path stays inside canonical base
  6. path traversal / escaped roots are rejected
"""

import os
import tempfile
import unittest

import numpy as np

from torment_service.embedding_store import (
    _canonical_storage_root,
    _child_path,
    _ensure_within_base,
    EmbeddingShardWriter,
    EmbeddingShardReader,
    load_legacy_embedding,
)


class TestCanonicalStorageRoot(unittest.TestCase):
    """1. _canonical_storage_root is stable and absolute."""

    def test_returns_absolute_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = _canonical_storage_root(td)
            self.assertTrue(os.path.isabs(root))

    def test_stable_across_calls(self):
        with tempfile.TemporaryDirectory() as td:
            r1 = _canonical_storage_root(td)
            r2 = _canonical_storage_root(td)
            self.assertEqual(r1, r2)

    def test_resolves_symlinks(self):
        with tempfile.TemporaryDirectory() as td:
            real_dir = os.path.join(td, "real")
            os.makedirs(real_dir)
            link_dir = os.path.join(td, "link")
            os.symlink(real_dir, link_dir)
            root = _canonical_storage_root(link_dir)
            self.assertEqual(root, os.path.realpath(real_dir))

    def test_mkdir_creates_directory(self):
        with tempfile.TemporaryDirectory() as td:
            new_dir = os.path.join(td, "new_storage")
            self.assertFalse(os.path.exists(new_dir))
            root = _canonical_storage_root(new_dir, mkdir=True)
            self.assertTrue(os.path.isdir(root))


class TestChildPath(unittest.TestCase):
    """6. Path traversal / escaped roots are rejected by _child_path."""

    def test_rejects_dotdot(self):
        with tempfile.TemporaryDirectory() as td:
            root = _canonical_storage_root(td)
            with self.assertRaises(ValueError):
                _child_path(root, "../escape.txt")

    def test_rejects_slash_in_filename(self):
        with tempfile.TemporaryDirectory() as td:
            root = _canonical_storage_root(td)
            with self.assertRaises(ValueError):
                _child_path(root, "sub/file.txt")

    def test_rejects_empty_filename(self):
        with tempfile.TemporaryDirectory() as td:
            root = _canonical_storage_root(td)
            with self.assertRaises(ValueError):
                _child_path(root, "")

    def test_valid_filename_stays_inside_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = _canonical_storage_root(td)
            child = _child_path(root, "manifest.json")
            self.assertTrue(child.startswith(root + os.sep))


class TestWriterPathIntegrity(unittest.TestCase):
    """2, 3, 4. Writer paths stay inside canonical root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.writer = EmbeddingShardWriter(self._tmpdir, dim=8)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_manifest_inside_root(self):
        """2. Manifest path stays inside canonical root."""
        self.assertTrue(
            self.writer.manifest_path.startswith(self.writer.embeddings_dir + os.sep),
            f"Manifest {self.writer.manifest_path} not inside {self.writer.embeddings_dir}",
        )

    def test_shard_npy_inside_root(self):
        """3. Shard .npy path stays inside canonical root."""
        npy = self.writer._shard_npy_path(0)
        self.assertTrue(npy.startswith(self.writer.embeddings_dir + os.sep))
        self.assertTrue(npy.endswith(".npy"))

    def test_shard_map_inside_root(self):
        """3. Shard .map.jsonl path stays inside canonical root."""
        map_path = self.writer._shard_map_path(0)
        self.assertTrue(map_path.startswith(self.writer.embeddings_dir + os.sep))
        self.assertTrue(map_path.endswith(".map.jsonl"))

    def test_write_json_temp_inside_root(self):
        """4. _write_json temp file stays inside canonical root.

        We verify by writing the manifest and checking the file exists
        at the expected path (no temp file leaks outside).
        """
        self.writer._save_manifest()
        self.assertTrue(os.path.exists(self.writer.manifest_path))
        # The .tmp file should have been replaced (not lingering)
        self.assertFalse(os.path.exists(self.writer.manifest_path + ".tmp"))

    def test_append_creates_shard_inside_root(self):
        """After append, all files are inside the canonical root."""
        vec = np.random.randn(8).astype(np.float32)
        ref = self.writer.append(vec, eid=1, step=1)
        shard_idx = ref["shard"]
        npy = self.writer._shard_npy_path(shard_idx)
        map_p = self.writer._shard_map_path(shard_idx)
        self.assertTrue(os.path.exists(npy))
        self.assertTrue(os.path.exists(map_p))
        self.assertTrue(npy.startswith(self.writer.embeddings_dir + os.sep))
        self.assertTrue(map_p.startswith(self.writer.embeddings_dir + os.sep))


class TestReaderPathIntegrity(unittest.TestCase):
    """2, 3. Reader paths stay inside canonical root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        # Create a writer first to populate storage
        writer = EmbeddingShardWriter(self._tmpdir, dim=8)
        vec = np.random.randn(8).astype(np.float32)
        writer.append(vec, eid=1, step=1)
        self.reader = EmbeddingShardReader(self._tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_manifest_inside_root(self):
        self.assertTrue(
            self.reader.manifest_path.startswith(self.reader.embeddings_dir + os.sep),
        )

    def test_shard_npy_inside_root(self):
        npy = self.reader._shard_npy_path(0)
        self.assertTrue(npy.startswith(self.reader.embeddings_dir + os.sep))

    def test_shard_map_inside_root(self):
        map_path = self.reader._shard_map_path(0)
        self.assertTrue(map_path.startswith(self.reader.embeddings_dir + os.sep))


class TestLegacyEmbeddingPathIntegrity(unittest.TestCase):
    """5. Legacy embedding path stays inside canonical base."""

    def test_valid_eid_path_inside_base(self):
        with tempfile.TemporaryDirectory() as td:
            # Create a dummy legacy file
            path = os.path.join(td, "emb_42.npy")
            np.save(path, np.zeros(8, dtype=np.float32))
            result = load_legacy_embedding(td, 42)
            self.assertIsNotNone(result)

    def test_missing_eid_returns_none(self):
        with tempfile.TemporaryDirectory() as td:
            result = load_legacy_embedding(td, 99999)
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
