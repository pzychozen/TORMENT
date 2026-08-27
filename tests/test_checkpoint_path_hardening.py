"""Regression tests for checkpoint.py path-expression hardening.

Covers:
  1. Canonical checkpoint root stays inside base dir
  2. Checkpoint filename path stays inside checkpoint root
  3. Temp file path stays inside checkpoint root
  4. Prune targets are revalidated before deletion
  5. Latest checkpoint load revalidates selected file
  6. Invalid workspace/agent IDs are rejected
  7. Save/load/prune behavior still works after refactor
  8. _build_checkpoint_dir inline validation
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
    _build_checkpoint_dir,
    _get_checkpoint_root_guard,
    build_shard_snapshot,
    restore_from_checkpoint,
    _validate_path_component,
    _ensure_within_base,
    _validated_checkpoint_root,
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


class TestBuildCheckpointDir(unittest.TestCase):
    """8. _build_checkpoint_dir inline validation (used by save/load)."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_returns_canonical_path(self):
        result = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        self.assertTrue(os.path.isabs(result))
        self.assertEqual(result, os.path.realpath(result))

    def test_path_inside_data_dir(self):
        result = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(result.startswith(canonical_data + os.sep))

    def test_rejects_dotdot_workspace(self):
        with self.assertRaises(ValueError):
            _build_checkpoint_dir(self._tmpdir, "../escape", "agent1")

    def test_rejects_slash_agent(self):
        with self.assertRaises(ValueError):
            _build_checkpoint_dir(self._tmpdir, "ws1", "a/evil")

    def test_rejects_empty_workspace(self):
        with self.assertRaises(ValueError):
            _build_checkpoint_dir(self._tmpdir, "", "agent1")

    def test_rejects_empty_agent(self):
        with self.assertRaises(ValueError):
            _build_checkpoint_dir(self._tmpdir, "ws1", "")

    def test_rejects_backslash_workspace(self):
        with self.assertRaises(ValueError):
            _build_checkpoint_dir(self._tmpdir, "ws\\evil", "agent1")

    def test_rejects_backslash_agent(self):
        with self.assertRaises(ValueError):
            _build_checkpoint_dir(self._tmpdir, "ws1", "agent\\evil")


class TestSaveCheckpointPaths(unittest.TestCase):
    """2, 3. Checkpoint and temp file paths stay inside root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_creates_file_inside_root(self):
        path = save_checkpoint(
            data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
            step=10,
            model_state=_make_model_state(),
            corridor_monitor=_make_corridor_monitor(),
        )
        self.assertIsNotNone(path)
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(path.startswith(canonical_data + os.sep))

    def test_save_correct_filename(self):
        path = save_checkpoint(
            data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
            step=42,
            model_state=_make_model_state(),
            corridor_monitor=_make_corridor_monitor(),
        )
        self.assertTrue(path.endswith("checkpoint_000042.json"))

    def test_no_tmp_file_left_after_save(self):
        save_checkpoint(
            data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
            step=10,
            model_state=_make_model_state(),
            corridor_monitor=_make_corridor_monitor(),
        )
        ckpt_dir = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        files = os.listdir(ckpt_dir)
        tmp_files = [f for f in files if f.endswith(".tmp")]
        self.assertEqual(tmp_files, [])

    def test_save_rejects_invalid_workspace(self):
        """save_checkpoint with traversal workspace returns None (non-fatal)."""
        path = save_checkpoint(
            data_dir=self._tmpdir, workspace_id="../escape", agent_id="agent1",
            step=10,
            model_state=_make_model_state(),
            corridor_monitor=_make_corridor_monitor(),
        )
        self.assertIsNone(path)

    def test_save_rejects_invalid_agent(self):
        """save_checkpoint with traversal agent returns None (non-fatal)."""
        path = save_checkpoint(
            data_dir=self._tmpdir, workspace_id="ws1", agent_id="a/evil",
            step=10,
            model_state=_make_model_state(),
            corridor_monitor=_make_corridor_monitor(),
        )
        self.assertIsNone(path)


class TestPruneCheckpoints(unittest.TestCase):
    """4. Prune revalidates and works correctly."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_prune_keeps_max(self):
        for step in range(5):
            save_checkpoint(
                data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
                step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                max_checkpoints=3,
            )
        ckpt_dir = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        files = sorted(os.listdir(ckpt_dir))
        json_files = [f for f in files if f.endswith(".json")]
        self.assertLessEqual(len(json_files), 3)

    def test_prune_keeps_newest(self):
        for step in range(5):
            save_checkpoint(
                data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
                step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                max_checkpoints=2,
            )
        ckpt_dir = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        files = sorted(os.listdir(ckpt_dir))
        json_files = [f for f in files if f.endswith(".json")]
        self.assertIn("checkpoint_000004.json", json_files)
        self.assertIn("checkpoint_000003.json", json_files)
        self.assertNotIn("checkpoint_000000.json", json_files)

    def test_prune_ignores_unexpected_filenames(self):
        """Files that don't match checkpoint_NNNNNN.json are left alone."""
        for step in range(3):
            save_checkpoint(
                data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
                step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                max_checkpoints=1,
            )
        ckpt_dir = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        rogue = os.path.join(ckpt_dir, "notes.txt")
        with open(rogue, "w") as f:
            f.write("keep me")
        stale_tmp = os.path.join(ckpt_dir, "checkpoint_000999.json.tmp")
        with open(stale_tmp, "w") as f:
            f.write("incomplete")
        root_guard = _get_checkpoint_root_guard(self._tmpdir, "ws1", "agent1")
        _prune_old_checkpoints(root_guard, 1)
        self.assertTrue(os.path.exists(rogue), "non-checkpoint file was deleted")
        self.assertTrue(os.path.exists(stale_tmp), "tmp checkpoint was pruned")

    def test_prune_uses_child_path_not_raw_glob(self):
        """Prune reconstructs paths from basenames — a symlink-escaped
        name won't match the pattern and is therefore ignored."""
        for step in range(3):
            save_checkpoint(
                data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
                step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
                max_checkpoints=10,
            )
        ckpt_dir = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        root_guard = _get_checkpoint_root_guard(self._tmpdir, "ws1", "agent1")
        _prune_old_checkpoints(root_guard, 1)
        remaining = [f for f in os.listdir(ckpt_dir) if f.endswith(".json")]
        self.assertEqual(len(remaining), 1, "should keep exactly 1 valid checkpoint")


class TestLoadLatestCheckpoint(unittest.TestCase):
    """5, 7. Load revalidates and works correctly."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_load_returns_latest(self):
        for step in [10, 20, 30]:
            save_checkpoint(
                data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
                step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
            )
        ckpt_dir = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        with open(os.path.join(ckpt_dir, "checkpoint_000999.json.tmp"), "w") as f:
            f.write('{"step": 999')
        data = load_latest_checkpoint(self._tmpdir, "ws1", "agent1")
        self.assertIsNotNone(data)
        self.assertEqual(data["step"], 30)

    def test_load_empty_dir_returns_none(self):
        ckpt_dir = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        os.makedirs(ckpt_dir, exist_ok=True)
        data = load_latest_checkpoint(self._tmpdir, "ws1", "agent1")
        self.assertIsNone(data)

    def test_load_nonexistent_returns_none(self):
        data = load_latest_checkpoint(self._tmpdir, "ws_none", "agent_none")
        self.assertIsNone(data)

    def test_load_invalid_workspace_returns_none(self):
        data = load_latest_checkpoint(self._tmpdir, "../escape", "agent1")
        self.assertIsNone(data)

    def test_load_invalid_agent_returns_none(self):
        data = load_latest_checkpoint(self._tmpdir, "ws1", "a/evil")
        self.assertIsNone(data)

    def test_load_ignores_non_matching_files(self):
        """Only checkpoint_NNNNNN.json files are candidates for loading."""
        ckpt_dir = _build_checkpoint_dir(self._tmpdir, "ws1", "agent1")
        os.makedirs(ckpt_dir, exist_ok=True)
        rogue = os.path.join(ckpt_dir, "checkpoint_evil.json")
        with open(rogue, "w") as f:
            json.dump({"step": 999}, f)
        stale_tmp = os.path.join(ckpt_dir, "checkpoint_000999.json.tmp")
        with open(stale_tmp, "w") as f:
            f.write('{"step": 999')
        data = load_latest_checkpoint(self._tmpdir, "ws1", "agent1")
        self.assertIsNone(data, "should ignore non-matching filenames")

    def test_load_selects_latest_valid_basename(self):
        """Load reconstructs path from validated basename, picks highest step."""
        for step in [5, 15, 10]:
            save_checkpoint(
                data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
                step=step,
                model_state=_make_model_state(),
                corridor_monitor=_make_corridor_monitor(),
            )
        data = load_latest_checkpoint(self._tmpdir, "ws1", "agent1")
        self.assertIsNotNone(data)
        self.assertEqual(data["step"], 15)

    def test_round_trip_save_load_restore(self):
        """Full save -> load -> restore round trip."""
        ms = _make_model_state()
        cm = _make_corridor_monitor()
        save_checkpoint(
            data_dir=self._tmpdir, workspace_id="ws1", agent_id="agent1",
            step=50,
            model_state=ms,
            corridor_monitor=cm,
            character_state_dict={"drift_score": 0.05},
        )
        data = load_latest_checkpoint(self._tmpdir, "ws1", "agent1")
        self.assertIsNotNone(data)
        restored = restore_from_checkpoint(data)
        self.assertEqual(restored["step"], 50)
        self.assertEqual(data["model_state"]["z_semantics"], "kernel_canonical_v4_0")
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


class TestValidatedCheckpointRoot(unittest.TestCase):
    """Inline sanitiser returns canonical path inside base, rejects escapes."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_returns_realpath_inside_base(self):
        sub = os.path.join(self._tmpdir, "ckpts")
        os.makedirs(sub)
        result = _validated_checkpoint_root(sub, self._tmpdir)
        self.assertEqual(result, os.path.realpath(sub))

    def test_mkdir_creates_directory(self):
        sub = os.path.join(self._tmpdir, "new_ckpts")
        result = _validated_checkpoint_root(sub, self._tmpdir, mkdir=True)
        self.assertTrue(os.path.isdir(result))

    def test_rejects_escape_via_dotdot(self):
        outside = os.path.join(self._tmpdir, "..", "escape")
        with self.assertRaises(ValueError):
            _validated_checkpoint_root(outside, self._tmpdir)

    def test_rejects_unrelated_directory(self):
        with self.assertRaises(ValueError):
            _validated_checkpoint_root("/tmp/unrelated", self._tmpdir)

    def test_accepts_base_dir_itself(self):
        result = _validated_checkpoint_root(self._tmpdir, self._tmpdir)
        self.assertEqual(result, os.path.realpath(self._tmpdir))

    def test_normalises_trailing_separators(self):
        sub = os.path.join(self._tmpdir, "ckpts")
        os.makedirs(sub)
        result = _validated_checkpoint_root(sub + os.sep + os.sep, self._tmpdir)
        self.assertEqual(result, os.path.realpath(sub))


if __name__ == "__main__":
    unittest.main()
