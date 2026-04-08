"""Regression tests for governance.py path-expression hardening.

Covers:
  1. Governance root stays inside canonical data root
  2. audit.jsonl stays inside governance root
  3. Invalid workspace IDs are rejected
  4. log/recent behavior still works after refactor
  5. Reload from disk still works
"""

import os
import shutil
import tempfile
import unittest

from torment_service.governance import GovernanceAuditLog
from torment_service.pathing import safe_slug


class TestGovernanceAuditLogPathIntegrity(unittest.TestCase):
    """1, 2. All paths stay inside their respective roots."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.audit = GovernanceAuditLog(self._tmpdir, "test_ws")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_base_is_canonical(self):
        self.assertTrue(os.path.isabs(self.audit._base))
        self.assertEqual(self.audit._base, os.path.realpath(self.audit._base))

    def test_base_inside_data_dir(self):
        canonical_data = os.path.realpath(self._tmpdir)
        self.assertTrue(
            self.audit._base.startswith(canonical_data + os.sep),
            f"governance root {self.audit._base} not inside {canonical_data}",
        )

    def test_audit_path_inside_base(self):
        self.assertTrue(
            self.audit._path.startswith(self.audit._base + os.sep),
            f"audit path {self.audit._path} not inside {self.audit._base}",
        )

    def test_audit_path_correct_name(self):
        self.assertTrue(self.audit._path.endswith("audit.jsonl"))

    def test_governance_dir_created(self):
        self.assertTrue(os.path.isdir(self.audit._base))

    def test_expected_directory_structure(self):
        self.assertTrue(self.audit._base.endswith(
            os.path.join("workspaces", "test_ws", "governance")
        ))


class TestGovernanceAuditLogInvalidPaths(unittest.TestCase):
    """3. Invalid workspace IDs are rejected."""

    def test_rejects_dotdot_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                GovernanceAuditLog(td, "../escape")

    def test_rejects_slash_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                GovernanceAuditLog(td, "ws/evil")

    def test_rejects_backslash_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                GovernanceAuditLog(td, "ws\\evil")

    def test_rejects_empty_workspace_id(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                GovernanceAuditLog(td, "")

    def test_validate_path_component_rejects_dotdot(self):
        with self.assertRaises(ValueError):
            safe_slug("..")


class TestGovernanceAuditLogBehavior(unittest.TestCase):
    """4. log/recent behavior still works after refactor."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.audit = GovernanceAuditLog(self._tmpdir, "test_ws")

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_log_creates_file(self):
        self.audit.log(eid=1, agent_id="a1", changes={"protected": True})
        self.assertTrue(os.path.exists(self.audit._path))

    def test_log_returns_record(self):
        record = self.audit.log(eid=1, agent_id="a1", changes={"protected": True})
        self.assertEqual(record["eid"], 1)
        self.assertEqual(record["agent_id"], "a1")
        self.assertEqual(record["actor"], "operator")
        self.assertEqual(record["source"], "api")

    def test_log_custom_actor_source(self):
        record = self.audit.log(
            eid=2, agent_id="a2",
            changes={"non_shareable": True},
            actor="system", source="auto",
        )
        self.assertEqual(record["actor"], "system")
        self.assertEqual(record["source"], "auto")

    def test_recent_returns_logged_records(self):
        self.audit.log(eid=1, agent_id="a1", changes={"protected": True})
        self.audit.log(eid=2, agent_id="a1", changes={"decay_accelerated": True})
        records = self.audit.recent(limit=10)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["eid"], 1)
        self.assertEqual(records[1]["eid"], 2)

    def test_recent_respects_limit(self):
        for i in range(5):
            self.audit.log(eid=i, agent_id="a1", changes={"protected": True})
        records = self.audit.recent(limit=3)
        self.assertEqual(len(records), 3)
        # Should be the last 3
        self.assertEqual(records[0]["eid"], 2)

    def test_recent_empty_log(self):
        records = self.audit.recent()
        self.assertEqual(records, [])

    def test_empty_audit_loads_cleanly(self):
        audit = GovernanceAuditLog(self._tmpdir, "fresh_ws")
        self.assertEqual(audit.recent(), [])


class TestGovernanceAuditLogReload(unittest.TestCase):
    """5. Reload from disk still works."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_reload_from_disk(self):
        audit1 = GovernanceAuditLog(self._tmpdir, "test_ws")
        audit1.log(eid=1, agent_id="a1", changes={"protected": True})
        audit1.log(eid=2, agent_id="a2", changes={"non_shareable": True})

        # New instance reads from the same JSONL
        audit2 = GovernanceAuditLog(self._tmpdir, "test_ws")
        records = audit2.recent(limit=10)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["eid"], 1)
        self.assertEqual(records[1]["eid"], 2)


if __name__ == "__main__":
    unittest.main()
