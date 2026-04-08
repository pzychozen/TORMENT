"""Tests for torment_service.pathing — centralised path-safety helpers."""

import datetime
import os
import shutil
import tempfile
import unittest

from torment_service.pathing import (
    safe_slug,
    ensure_within_base,
    safe_join,
    shard_for_key,
    sharded_entity_path,
    dated_log_path,
    approved_subdir,
    stable_filename,
)


class TestSafeSlug(unittest.TestCase):
    """safe_slug rejects traversal and separator characters."""

    def test_accepts_plain_identifier(self):
        self.assertEqual(safe_slug("workspace_1", "ws"), "workspace_1")

    def test_accepts_alphanumeric_with_dashes(self):
        self.assertEqual(safe_slug("my-agent-42", "agent"), "my-agent-42")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            safe_slug("", "id")

    def test_rejects_dotdot(self):
        with self.assertRaises(ValueError):
            safe_slug("../escape", "id")

    def test_rejects_dotdot_embedded(self):
        with self.assertRaises(ValueError):
            safe_slug("a..b", "id")

    def test_rejects_forward_slash(self):
        with self.assertRaises(ValueError):
            safe_slug("a/b", "id")

    def test_rejects_backslash(self):
        with self.assertRaises(ValueError):
            safe_slug("a\\b", "id")


class TestEnsureWithinBase(unittest.TestCase):
    """ensure_within_base validates resolved paths against a trusted root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_accepts_child(self):
        child = os.path.join(self._tmpdir, "sub")
        os.makedirs(child)
        result = ensure_within_base(child, self._tmpdir)
        self.assertEqual(result, os.path.realpath(child))

    def test_accepts_base_itself(self):
        result = ensure_within_base(self._tmpdir, self._tmpdir)
        self.assertEqual(result, os.path.realpath(self._tmpdir))

    def test_rejects_escape(self):
        with self.assertRaises(ValueError):
            ensure_within_base("/etc/passwd", self._tmpdir)

    def test_rejects_dotdot_escape(self):
        outside = os.path.join(self._tmpdir, "..", "escape")
        with self.assertRaises(ValueError):
            ensure_within_base(outside, self._tmpdir)


class TestSafeJoin(unittest.TestCase):
    """safe_join builds sub-paths and validates containment."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_joins_parts(self):
        result = safe_join(self._tmpdir, "a", "b", "c")
        expected = os.path.realpath(os.path.join(self._tmpdir, "a", "b", "c"))
        self.assertEqual(result, expected)

    def test_returns_base_for_no_parts(self):
        result = safe_join(self._tmpdir)
        self.assertEqual(result, os.path.realpath(self._tmpdir))

    def test_rejects_dotdot_traversal(self):
        with self.assertRaises(ValueError):
            safe_join(self._tmpdir, "..", "escape")

    def test_result_is_canonical(self):
        result = safe_join(self._tmpdir, "a")
        self.assertEqual(result, os.path.realpath(result))


class TestShardForKey(unittest.TestCase):
    """shard_for_key returns deterministic hex buckets."""

    def test_returns_two_char_hex(self):
        result = shard_for_key("some_key")
        self.assertRegex(result, r"^[0-9a-f]{2}$")

    def test_deterministic(self):
        a = shard_for_key("test_key")
        b = shard_for_key("test_key")
        self.assertEqual(a, b)

    def test_different_keys_can_differ(self):
        # Not guaranteed for any two keys, but statistically almost certain
        results = {shard_for_key(f"key_{i}") for i in range(100)}
        self.assertGreater(len(results), 1)

    def test_custom_bucket_count(self):
        result = shard_for_key("x", n=16)
        bucket = int(result, 16)
        self.assertLess(bucket, 16)


class TestShardedEntityPath(unittest.TestCase):
    """sharded_entity_path builds state/<category>/<shard>/<key>.<ext>."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_structure(self):
        result = sharded_entity_path(self._tmpdir, "agents", "agent_42")
        self.assertIn(os.sep + "state" + os.sep, result)
        self.assertIn(os.sep + "agents" + os.sep, result)
        self.assertTrue(result.endswith("agent_42.json"))

    def test_inside_base(self):
        result = sharded_entity_path(self._tmpdir, "agents", "a1")
        canonical = os.path.realpath(self._tmpdir)
        self.assertTrue(result.startswith(canonical + os.sep))

    def test_custom_extension(self):
        result = sharded_entity_path(self._tmpdir, "nodes", "n1", ext=".jsonl")
        self.assertTrue(result.endswith("n1.jsonl"))

    def test_rejects_traversal_in_category(self):
        with self.assertRaises(ValueError):
            sharded_entity_path(self._tmpdir, "../escape", "key")

    def test_rejects_traversal_in_key(self):
        with self.assertRaises(ValueError):
            sharded_entity_path(self._tmpdir, "cat", "../escape")


class TestDatedLogPath(unittest.TestCase):
    """dated_log_path builds logs/<category>/daily/YYYY-MM-DD.jsonl."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_structure(self):
        d = datetime.date(2026, 4, 8)
        result = dated_log_path(self._tmpdir, "trajectories", date=d)
        self.assertIn(os.sep + "logs" + os.sep, result)
        self.assertIn(os.sep + "trajectories" + os.sep, result)
        self.assertIn(os.sep + "daily" + os.sep, result)
        self.assertTrue(result.endswith("2026-04-08.jsonl"))

    def test_inside_base(self):
        result = dated_log_path(self._tmpdir, "events")
        canonical = os.path.realpath(self._tmpdir)
        self.assertTrue(result.startswith(canonical + os.sep))

    def test_uses_today_by_default(self):
        result = dated_log_path(self._tmpdir, "test")
        today = datetime.datetime.utcnow().date().isoformat()
        self.assertTrue(result.endswith(today + ".jsonl"))

    def test_rejects_traversal_category(self):
        with self.assertRaises(ValueError):
            dated_log_path(self._tmpdir, "../escape")


class TestApprovedSubdir(unittest.TestCase):
    """approved_subdir creates validated nested directories."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_creates_directory(self):
        result = approved_subdir(self._tmpdir, "workspaces", "ws1", "agents")
        self.assertTrue(os.path.isdir(result))

    def test_inside_base(self):
        result = approved_subdir(self._tmpdir, "sub", "dir")
        canonical = os.path.realpath(self._tmpdir)
        self.assertTrue(result.startswith(canonical + os.sep))

    def test_no_mkdir(self):
        result = approved_subdir(self._tmpdir, "nonexistent", mkdir=False)
        self.assertFalse(os.path.exists(result))

    def test_rejects_traversal(self):
        with self.assertRaises(ValueError):
            approved_subdir(self._tmpdir, "ok", "../escape")

    def test_rejects_slash_in_part(self):
        with self.assertRaises(ValueError):
            approved_subdir(self._tmpdir, "a/b")

    def test_rejects_empty_part(self):
        with self.assertRaises(ValueError):
            approved_subdir(self._tmpdir, "ok", "")


class TestStableFilename(unittest.TestCase):
    """stable_filename derives safe child paths from a root."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_returns_path_inside_root(self):
        result = stable_filename(self._tmpdir, "test.json")
        self.assertTrue(result.startswith(os.path.realpath(self._tmpdir) + os.sep))

    def test_returns_canonical_path(self):
        result = stable_filename(self._tmpdir, "test.json")
        self.assertEqual(result, os.path.realpath(result))

    def test_rejects_dotdot(self):
        with self.assertRaises(ValueError):
            stable_filename(self._tmpdir, "../escape.json")

    def test_rejects_slash(self):
        with self.assertRaises(ValueError):
            stable_filename(self._tmpdir, "sub/file.json")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            stable_filename(self._tmpdir, "")

    def test_rejects_backslash(self):
        with self.assertRaises(ValueError):
            stable_filename(self._tmpdir, "a\\b.json")


if __name__ == "__main__":
    unittest.main()
