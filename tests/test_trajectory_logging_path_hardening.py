"""Regression tests for trajectory_logging.py path-expression hardening.

Covers:
  1. Canonical root dir is stable and absolute
  2. self.path stays inside canonical root
  3. Invalid filenames with /, \\, or .. are rejected
  4. Default filename remains trajectories.jsonl
  5. Logging still appends valid JSONL after refactor
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

import numpy as np

from torment_service.kernel.trajectory_logging import TrajectoryLogger


class TestTrajectoryLoggerPathIntegrity(unittest.TestCase):
    """1, 2, 4. Root and path stay canonical and inside root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.logger = TrajectoryLogger(self._tmpdir)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_root_is_canonical(self):
        self.assertTrue(os.path.isabs(self.logger.root_dir))
        self.assertEqual(self.logger.root_dir, os.path.realpath(self.logger.root_dir))

    def test_path_inside_root(self):
        self.assertTrue(
            self.logger.path.startswith(self.logger.root_dir + os.sep),
            f"path {self.logger.path} not inside {self.logger.root_dir}",
        )

    def test_default_filename(self):
        self.assertTrue(self.logger.path.endswith("trajectories.jsonl"))

    def test_custom_filename(self):
        logger = TrajectoryLogger(self._tmpdir, filename="custom.jsonl")
        self.assertTrue(logger.path.endswith("custom.jsonl"))
        self.assertTrue(logger.path.startswith(logger.root_dir + os.sep))

    def test_root_dir_created(self):
        self.assertTrue(os.path.isdir(self.logger.root_dir))


class TestTrajectoryLoggerInvalidPaths(unittest.TestCase):
    """3. Invalid filenames are rejected."""

    def test_rejects_dotdot_filename(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                TrajectoryLogger(td, filename="../escape.jsonl")

    def test_rejects_slash_filename(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                TrajectoryLogger(td, filename="sub/file.jsonl")

    @unittest.skipUnless(os.sep == "\\", "backslash is only a separator on Windows")
    def test_rejects_backslash_filename(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                TrajectoryLogger(td, filename="sub\\file.jsonl")

    def test_rejects_empty_filename(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                TrajectoryLogger(td, filename="")


class TestTrajectoryLoggerBehavior(unittest.TestCase):
    """5. Logging still appends valid JSONL after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.logger = TrajectoryLogger(self._tmpdir)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_log_entity_creates_file(self):
        ent = MagicMock()
        ent.pos = np.array([1.0, 2.0, 3.0])
        ent.vel = np.array([0.1, 0.2, 0.3])
        ent.vel0 = np.array([0.1, 0.2, 0.3])
        ent.eid = 1
        ent.born_step = 0
        ent.channel = 0
        ent.alive = True
        ent.payload = {}

        self.logger.log_entity(ent, step=10)
        self.assertTrue(os.path.exists(self.logger.path))

    def test_log_entity_writes_valid_jsonl(self):
        ent = MagicMock()
        ent.pos = np.array([1.0, 2.0, 3.0])
        ent.vel = np.array([0.1, 0.2, 0.3])
        ent.vel0 = np.array([0.1, 0.2, 0.3])
        ent.eid = 42
        ent.born_step = 5
        ent.channel = 1
        ent.alive = True
        ent.payload = {"traj_label": "test"}

        self.logger.log_entity(ent, step=10)
        self.logger.log_entity(ent, step=11)

        with open(self.logger.path, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        self.assertEqual(len(lines), 2)
        rec = json.loads(lines[0])
        self.assertEqual(rec["eid"], 42)
        self.assertEqual(rec["step"], 10)
        self.assertEqual(rec["pos"], [1.0, 2.0, 3.0])

    def test_empty_logger_no_file(self):
        """If nothing is logged, no file is created."""
        self.assertFalse(os.path.exists(self.logger.path))


if __name__ == "__main__":
    unittest.main()
