"""Regression tests for compression.py path-expression hardening.

Covers:
  1. _find_motifs_path validates components and stays inside data root
  2. _log_compression_event stays inside data root
  3. Invalid workspace/agent IDs are rejected
  4. Compression logging still works for valid inputs
"""

from contextlib import contextmanager
import json
import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace

from torment_service.compression import (
    _find_motifs_path,
    _log_compression_event,
    _attach_persisted_deep_store,
    _validate_path_component,
    CompressionEvent,
)


class _Locks:
    @contextmanager
    def agent_lock(self, workspace_id: str, agent_id: str):
        yield


class _CountingLocks:
    def __init__(self):
        self.count = 0

    @contextmanager
    def agent_lock(self, workspace_id: str, agent_id: str):
        self.count += 1
        yield


def _make_fabric(data_dir: str) -> SimpleNamespace:
    """Create a minimal fabric-like object."""
    return SimpleNamespace(data_dir=data_dir, _deep_stores={}, locks=_Locks())


def _make_event() -> CompressionEvent:
    """Create a minimal CompressionEvent."""
    return CompressionEvent(
        step=1,
        trigger="corridor_exit",
    )


class TestFindMotifsPath(unittest.TestCase):
    """_find_motifs_path validates and stays inside data root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_returns_none_when_no_motifs_exist(self):
        fab = _make_fabric(self._tmpdir)
        result = _find_motifs_path(fab, "agent1", "ws1")
        self.assertIsNone(result)

    def test_finds_workspace_scoped_motifs(self):
        motifs_dir = os.path.join(
            self._tmpdir, "workspaces", "ws1", "agents", "agent1", "private"
        )
        os.makedirs(motifs_dir)
        motifs_file = os.path.join(motifs_dir, "motifs.json")
        with open(motifs_file, "w") as f:
            json.dump([], f)

        fab = _make_fabric(self._tmpdir)
        result = _find_motifs_path(fab, "agent1", "ws1")
        self.assertIsNotNone(result)
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(
            result.startswith(canonical_data + os.sep),
            f"motifs path {result} not inside {canonical_data}",
        )

    def test_rejects_dotdot_workspace(self):
        fab = _make_fabric(self._tmpdir)
        with self.assertRaises(ValueError):
            _find_motifs_path(fab, "agent1", "../escape")

    def test_rejects_slash_agent(self):
        fab = _make_fabric(self._tmpdir)
        with self.assertRaises(ValueError):
            _find_motifs_path(fab, "a/evil", "ws1")

    def test_rejects_empty_workspace(self):
        fab = _make_fabric(self._tmpdir)
        with self.assertRaises(ValueError):
            _find_motifs_path(fab, "agent1", "")

    def test_returned_path_is_canonical(self):
        motifs_dir = os.path.join(
            self._tmpdir, "workspaces", "ws1", "agents", "agent1"
        )
        os.makedirs(motifs_dir)
        motifs_file = os.path.join(motifs_dir, "motifs.json")
        with open(motifs_file, "w") as f:
            json.dump([], f)

        fab = _make_fabric(self._tmpdir)
        result = _find_motifs_path(fab, "agent1", "ws1")
        self.assertIsNotNone(result)
        self.assertEqual(result, os.path.realpath(result))


class TestLogCompressionEvent(unittest.TestCase):
    """_log_compression_event stays inside data root and works."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_creates_log_inside_data_root(self):
        fab = _make_fabric(self._tmpdir)
        event = _make_event()
        _log_compression_event(fab, "agent1", event, "ws1")

        log_path = os.path.join(
            self._tmpdir, "workspaces", "ws1", "agents", "agent1",
            "private", "compression_log.jsonl",
        )
        self.assertTrue(os.path.exists(log_path))
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(
            os.path.realpath(log_path).startswith(canonical_data + os.sep),
        )

    def test_log_content_is_valid_jsonl(self):
        fab = _make_fabric(self._tmpdir)
        event = _make_event()
        _log_compression_event(fab, "agent1", event, "ws1")

        log_path = os.path.join(
            self._tmpdir, "workspaces", "ws1", "agents", "agent1",
            "private", "compression_log.jsonl",
        )
        with open(log_path, "r") as f:
            line = f.readline()
        data = json.loads(line)
        self.assertEqual(data["trigger"], "corridor_exit")

    def test_rejects_dotdot_workspace(self):
        fab = _make_fabric(self._tmpdir)
        event = _make_event()
        # Should not raise — non-fatal — but should not create files outside root
        _log_compression_event(fab, "agent1", event, "../escape")
        # Verify nothing was created outside data root
        parent = os.path.dirname(self._tmpdir)
        escape_dir = os.path.join(parent, "escape")
        self.assertFalse(os.path.exists(escape_dir))

    def test_rejects_slash_agent(self):
        fab = _make_fabric(self._tmpdir)
        event = _make_event()
        # _validate_path_component raises but outer try/except catches it
        _log_compression_event(fab, "a/evil", event, "ws1")

    def test_appends_multiple_events(self):
        fab = _make_fabric(self._tmpdir)
        for i in range(3):
            event = _make_event()
            _log_compression_event(fab, "agent1", event, "ws1")

        log_path = os.path.join(
            self._tmpdir, "workspaces", "ws1", "agents", "agent1",
            "private", "compression_log.jsonl",
        )
        with open(log_path, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 3)


class TestValidatePathComponent(unittest.TestCase):
    """Path component validation."""

    def test_rejects_dotdot(self):
        with self.assertRaises(ValueError):
            _validate_path_component("..", "test")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            _validate_path_component("", "test")

    def test_rejects_slash(self):
        with self.assertRaises(ValueError):
            _validate_path_component("a/b", "test")

    def test_accepts_valid(self):
        result = _validate_path_component("valid_name", "test")
        self.assertEqual(result, "valid_name")


class TestAttachPersistedDeepStore(unittest.TestCase):
    """_attach_persisted_deep_store validates paths without creating absent stores."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _deep_dir(self, workspace_id: str = "ws1", agent_id: str = "agent1") -> str:
        return os.path.join(
            self._tmpdir,
            "workspaces",
            workspace_id,
            "agents",
            agent_id,
            "deep_memory",
        )

    def test_absent_memories_returns_none_without_creating_directory(self):
        fab = _make_fabric(self._tmpdir)

        result = _attach_persisted_deep_store(fab, "agent1", "ws1")

        self.assertIsNone(result)
        self.assertEqual(fab._deep_stores, {})
        self.assertFalse(os.path.exists(self._deep_dir()))

    def test_attaches_existing_memories_jsonl_under_agent_lock(self):
        deep_dir = self._deep_dir()
        os.makedirs(deep_dir)
        with open(os.path.join(deep_dir, "memories.jsonl"), "w") as f:
            f.write("")

        fab = _make_fabric(self._tmpdir)
        locks = _CountingLocks()
        fab.locks = locks

        result = _attach_persisted_deep_store(fab, "agent1", "ws1")

        self.assertIsNotNone(result)
        self.assertEqual(locks.count, 1)
        self.assertIn("ws1/agent1", fab._deep_stores)

    def test_cached_store_returns_without_relocking(self):
        deep_dir = self._deep_dir()
        os.makedirs(deep_dir)
        with open(os.path.join(deep_dir, "memories.jsonl"), "w") as f:
            f.write("")

        fab = _make_fabric(self._tmpdir)
        locks = _CountingLocks()
        fab.locks = locks

        first = _attach_persisted_deep_store(fab, "agent1", "ws1")
        second = _attach_persisted_deep_store(fab, "agent1", "ws1")

        self.assertIs(first, second)
        self.assertEqual(locks.count, 1)

    def test_rejects_dotdot_workspace_before_probe(self):
        fab = _make_fabric(self._tmpdir)

        with self.assertRaises(ValueError):
            _attach_persisted_deep_store(fab, "agent1", "../escape")

        parent = os.path.dirname(self._tmpdir)
        self.assertFalse(os.path.exists(os.path.join(parent, "escape")))

    def test_rejects_slash_agent_before_probe(self):
        fab = _make_fabric(self._tmpdir)

        with self.assertRaises(ValueError):
            _attach_persisted_deep_store(fab, "a/evil", "ws1")

        self.assertFalse(os.path.exists(self._deep_dir("ws1", "a")))


if __name__ == "__main__":
    unittest.main()
