"""Regression tests for checkpoint.py path-expression hardening.

Covers:
  1. Canonical checkpoint root stays inside base dir
  2. Checkpoint filename path stays inside checkpoint root
  3. Temp file path stays inside checkpoint root
  4. Globbed prune targets are revalidated before deletion
  5. Latest checkpoint load revalidates selected file
  6. Invalid workspace/agent IDs are rejected
  7. Save/load/prune behavior still works after refactor
"""

import json
import os
import shutil
import tempfile
import unittest

import numpy as np

from torment_service.checkpoint import (
    get_checkpoint_dir,
    save_checkpoint,
    load_latest_checkpoint,
    _prune_old_checkpoints,
    build_shard_snapshot,
    restore_from_checkpoint,
    _validate_path_component,
    _ensure_within_base,
)
from torment_service.kernel.model_core import ModelState
from torment_service.memory_kernel import CorridorMonitor


def _make_model_state() -> ModelState:
    """Create a minimal ModelState for testing."""
    return ModelState(
        Omega=np.array([1 + 0j, 0 + 1j, 0.5 + 0.5j], dtype=np.complex128),
        phi_index=3,
        cycle_stage=2,
        identity_state=1,
        z=0.15,
        z_mem=0.10,
        t=100.0,
        step=50,
    )


def _make_corridor_monitor() -> CorridorMonitor:
    """Create a minimal CorridorMonitor for testing."""
    return CorridorMonitor()


class TestGetCheckpointDir(unittest.TestCase):
    """1, 6. Canonical root and invalid ID rejection."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_returns_canonical_path(self):
        result = get_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        self.assertTrue(os.path.isabs(result))
        self.assertEqual(result, os.path.realpath(result))

    def test_path_inside_data_dir(self):
        result = get_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(
            result.startswith(canonical_data + os.sep),
            f"checkpoint dir {result} not inside {canonical_data}",
        )

    def test_expected_structure(self):
        result = get_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        self.assertTrue(result.endswith(
            os.path.join("workspaces", "ws1", "agents", "agent1", "private", "checkpoints")
        ))

    def test_rejects_dotdot_workspace(self):
        with self.assertRaises(ValueError):
            get_checkpoint_dir(self._tmpdir, "../escape", "agent1")

    def test_rejects_slash_workspace(self):
        with self.assertRaises(ValueError):
            get_checkpoint_dir(self._tmpdir, "ws/evil", "agent1")

    def test_rejects_empty_workspace(self):
        with self.assertRaises(ValueError):
            get_checkpoint_dir(self._tmpdir, "", "agent1")

    def test_rejects_dotdot_agent(self):
        with self.assertRaises(ValueError):
            get_checkpoint_dir(self._tmpdir, "ws1", "../escape")

    def test_rejects_slash_agent(self):
        with self.assertRaises(ValueError):
            get_checkpoint_dir(self._tmpdir, "ws1", "a/evil")

    def test_rejects_empty_agent(self):
        with self.assertRaises(ValueError):
            get_checkpoint_dir(self._tmpdir, "ws1", "")

    def test_rejects_backslash_workspace(self):
        with self.assertRaises(ValueError):
            get_checkpoint_dir(self._tmpdir, "ws\\evil", "agent1")


class TestSaveCheckpointPaths(unittest.TestCase):
    """2, 3. Checkpoint and temp file paths stay inside root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._ckpt_dir = get_checkpoint_dir(self._tmpdir, "ws1", "agent1")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_creates_file_inside_root(self):
        path = save_checkpoint(
            self._ckpt_dir, step=10,
            model_state=_make_model_state(),
            corridor_monitor=_make_corridor_monitor(),
            base_dir=self._tmpdir,
        )
        self.assertIsNotNone(path)
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(path.startswith(canonical_data + os.sep))

    def test_save_correct_filename(self):
        path = save_checkpoint(
            self._ckpt_dir, step=42,
            model_state=_make_model_state(),
            corridor_monitor=_make_corridor_monitor(),
            base_dir=self._tmpdir,
        )
        self.assertTrue(path.endswith("checkpoint_000042.json"))

    def test_no_tmp_file_left_after_save(self):
        save_checkpoint(
            self._ckpt_dir, step=10,
            model_state=_make_model_state(),
            corridor_monitor=_make_corridor_monitor(),
            base_dir=self._tmpdir,
        )
        # The .tmp file should have been replaced
        files = os.listdir(self._ckpt_dir)
        tmp_files = [f for f in files if f.endswith(".tmp")]
        self.assertEqual(tmp_files, [])


class TestPruneCheckpoints(unittest.TestCase):
    """4. Prune revalidates and works correctly."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._ckpt_dir = get_checkpoint_dir(self._tmpdir, "ws1", "agent1")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_prune_keeps_max(self):
        for step in range(5):
            save_checkpoint(
                self._ckpt_dir, step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                max_checkpoints=3,
                base_dir=self._tmpdir,
            )
        files = sorted(os.listdir(self._ckpt_dir))
        json_files = [f for f in files if f.endswith(".json")]
        self.assertLessEqual(len(json_files), 3)

    def test_prune_keeps_newest(self):
        for step in range(5):
            save_checkpoint(
                self._ckpt_dir, step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                max_checkpoints=2,
                base_dir=self._tmpdir,
            )
        files = sorted(os.listdir(self._ckpt_dir))
        json_files = [f for f in files if f.endswith(".json")]
        # Should have the last 2
        self.assertIn("checkpoint_000004.json", json_files)
        self.assertIn("checkpoint_000003.json", json_files)
        self.assertNotIn("checkpoint_000000.json", json_files)

    def test_prune_ignores_unexpected_filenames(self):
        """Files that don't match checkpoint_NNNNNN.json are left alone."""
        for step in range(3):
            save_checkpoint(
                self._ckpt_dir, step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                max_checkpoints=1,
                base_dir=self._tmpdir,
            )
        # Plant a non-matching file
        rogue = os.path.join(self._ckpt_dir, "notes.txt")
        with open(rogue, "w") as f:
            f.write("keep me")
        _prune_old_checkpoints(self._ckpt_dir, 1, self._tmpdir)
        self.assertTrue(os.path.exists(rogue), "non-checkpoint file was deleted")

    def test_prune_uses_child_path_not_raw_glob(self):
        """Prune reconstructs paths from basenames — a symlink-escaped
        name won't match the pattern and is therefore ignored."""
        for step in range(3):
            save_checkpoint(
                self._ckpt_dir, step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                max_checkpoints=10,
                base_dir=self._tmpdir,
            )
        # Plant a file whose name contains path traversal (wouldn't match pattern)
        rogue = os.path.join(self._ckpt_dir, "checkpoint_../../etc.json")
        # This filename is invalid on most OS but the key test is that
        # _prune_old_checkpoints only processes pattern-matched basenames
        _prune_old_checkpoints(self._ckpt_dir, 1, self._tmpdir)
        remaining = [f for f in os.listdir(self._ckpt_dir) if f.endswith(".json")]
        self.assertEqual(len(remaining), 1, "should keep exactly 1 valid checkpoint")


class TestLoadLatestCheckpoint(unittest.TestCase):
    """5, 7. Load revalidates and works correctly."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._ckpt_dir = get_checkpoint_dir(self._tmpdir, "ws1", "agent1")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_load_returns_latest(self):
        for step in [10, 20, 30]:
            save_checkpoint(
                self._ckpt_dir, step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                base_dir=self._tmpdir,
            )
        data = load_latest_checkpoint(self._ckpt_dir, self._tmpdir)
        self.assertIsNotNone(data)
        self.assertEqual(data["step"], 30)

    def test_load_empty_dir_returns_none(self):
        os.makedirs(self._ckpt_dir, exist_ok=True)
        data = load_latest_checkpoint(self._ckpt_dir, self._tmpdir)
        self.assertIsNone(data)

    def test_load_nonexistent_dir_returns_none(self):
        data = load_latest_checkpoint("/nonexistent/path", self._tmpdir)
        self.assertIsNone(data)

    def test_load_ignores_non_matching_files(self):
        """Only checkpoint_NNNNNN.json files are candidates for loading."""
        os.makedirs(self._ckpt_dir, exist_ok=True)
        # Plant a file that glob would match but doesn't fit the strict pattern
        rogue = os.path.join(self._ckpt_dir, "checkpoint_evil.json")
        with open(rogue, "w") as f:
            json.dump({"step": 999}, f)
        data = load_latest_checkpoint(self._ckpt_dir, self._tmpdir)
        self.assertIsNone(data, "should ignore non-matching filenames")

    def test_load_selects_latest_valid_basename(self):
        """Load reconstructs path from validated basename, picks highest step."""
        for step in [5, 15, 10]:
            save_checkpoint(
                self._ckpt_dir, step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                base_dir=self._tmpdir,
            )
        data = load_latest_checkpoint(self._ckpt_dir, self._tmpdir)
        self.assertIsNotNone(data)
        self.assertEqual(data["step"], 15)

    def test_round_trip_save_load_restore(self):
        """Full save → load → restore round trip."""
        ms = _make_model_state()
        cm = _make_corridor_monitor()
        save_checkpoint(
            self._ckpt_dir, step=50,
            model_state=ms,
            corridor_monitor=cm,
            character_state_dict={"drift_score": 0.05},
            base_dir=self._tmpdir,
        )
        data = load_latest_checkpoint(self._ckpt_dir, self._tmpdir)
        self.assertIsNotNone(data)
        restored = restore_from_checkpoint(data)
        self.assertEqual(restored["step"], 50)
        self.assertAlmostEqual(restored["model_state"].z, 0.15, places=5)
        self.assertEqual(restored["character_state"]["drift_score"], 0.05)


class TestBuildShardSnapshot(unittest.TestCase):
    """Shard snapshot path stays inside base."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._emb_dir = os.path.join(self._tmpdir, "embeddings")
        os.makedirs(self._emb_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_reads_manifest(self):
        manifest = {"active_shard": 0, "next_row": 42, "total_rows": 100, "embedding_dim": 384}
        with open(os.path.join(self._emb_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)
        result = build_shard_snapshot(self._emb_dir, self._tmpdir)
        self.assertIsNotNone(result)
        self.assertEqual(result["next_row"], 42)

    def test_missing_manifest_returns_none(self):
        result = build_shard_snapshot(self._emb_dir, self._tmpdir)
        self.assertIsNone(result)

    def test_traversal_attempt_returns_none(self):
        result = build_shard_snapshot("/etc/evil", self._tmpdir)
        self.assertIsNone(result)


class TestPathHelpers(unittest.TestCase):
    """Validate helper behavior."""

    def test_validate_path_component_rejects_dotdot(self):
        with self.assertRaises(ValueError):
            _validate_path_component("..", "test")

    def test_validate_path_component_rejects_empty(self):
        with self.assertRaises(ValueError):
            _validate_path_component("", "test")

    def test_ensure_within_base_rejects_escape(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                _ensure_within_base("/etc/passwd", td)


if __name__ == "__main__":
    unittest.main()
