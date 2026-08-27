"""F7 Layer-C persistent identity self-verification regressions."""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from torment_service import app as app_module
from torment_service.fabric import (
    TormentFabric,
    _WORKSPACE_IDENTITY_LEGACY_UNVERIFIED,
    _WORKSPACE_IDENTITY_VERIFIED_EXISTING,
    _verify_workspace_identity_before_initialization,
)
from torment_service.identity import IdentityStore, PersistentIdentityCollisionError


class TestPersistentAgentIdentityCollisionF7(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_identity_collision_f7_")
        self.env = patch.dict(
            os.environ,
            {
                "TORMENT_EMBED_PROVIDER": "hash",
                "TORMENT_CHARACTER_ENABLE": "0",
                "TORMENT_CHECKPOINT_ENABLE": "0",
                "TORMENT_COMPRESS_ENABLE": "0",
                "TORMENT_SRG_ENABLE": "0",
            },
            clear=False,
        )
        self.env.start()
        self.store = IdentityStore(self.tmpdir)
        self.fabric = TormentFabric(data_dir=self.tmpdir)

    def tearDown(self):
        self.fabric.close()
        self.env.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _identity_path(self, workspace_id, agent_id):
        return os.path.join(
            self.tmpdir,
            "workspaces",
            workspace_id,
            "agents",
            agent_id,
            "identity.json",
        )

    def _write_declared_identity(self, workspace_id, agent_id, *, declared_workspace_id, declared_agent_id):
        self.store.create(workspace_id, agent_id, seed={"seed_id": ""})
        path = self._identity_path(workspace_id, agent_id)
        with open(path, "r", encoding="utf-8") as f:
            body = json.load(f)
        body["workspace_id"] = declared_workspace_id
        body["agent_id"] = declared_agent_id
        with open(path, "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2, sort_keys=True)
        return path

    def test_exact_persisted_identity_match_succeeds_and_existing_identity_is_readable(self):
        self.store.create("workspace", "alice", seed={"seed_id": ""})

        loaded = self.store.load("workspace", "alice")

        self.assertEqual((loaded.workspace_id, loaded.agent_id), ("workspace", "alice"))
        self.assertEqual(
            self.fabric.create_agent("workspace", "alice").agent_id,
            "alice",
        )

    def test_persisted_agent_mismatch_fails_closed_without_identity_write_and_maps_to_409(self):
        path = self._write_declared_identity(
            "workspace", "alice",
            declared_workspace_id="workspace",
            declared_agent_id="Alice",
        )
        before = open(path, "rb").read()

        with self.assertRaises(PersistentIdentityCollisionError):
            self.store.load("workspace", "alice")
        with self.assertRaises(HTTPException) as fabric_error:
            self.fabric.create_agent("workspace", "alice")
        self.assertEqual(fabric_error.exception.status_code, 409)
        with patch.object(app_module, "fabric", self.fabric):
            with self.assertRaises(HTTPException) as api_error:
                app_module.get_identity("alice", workspace_id="workspace")
        self.assertEqual(api_error.exception.status_code, 409)

        self.assertEqual(open(path, "rb").read(), before)
        self.assertNotIn(self.fabric._agent_key("workspace", "alice"), self.fabric.private_graphs)

    def test_persisted_workspace_mismatch_fails_closed(self):
        self._write_declared_identity(
            "workspace", "alice",
            declared_workspace_id="Workspace",
            declared_agent_id="alice",
        )

        with self.assertRaises(PersistentIdentityCollisionError):
            self.store.load("workspace", "alice")
        with self.assertRaises(HTTPException) as raised:
            self.fabric.create_agent("workspace", "alice")
        self.assertEqual(raised.exception.status_code, 409)

    def test_new_identity_creation_remains_unchanged(self):
        created = self.fabric.create_agent("new-workspace", "new-agent")

        self.assertEqual((created.workspace_id, created.agent_id), ("new-workspace", "new-agent"))
        self.assertIsNotNone(self.store.load("new-workspace", "new-agent"))

    def test_exact_comparison_does_not_trim_casefold_or_unicode_normalize(self):
        pairs = (
            ("agent", "Agent"),
            ("agent", "agent "),
            ("\u00e9", "e\u0301"),
        )
        for request_agent_id, persisted_agent_id in pairs:
            with self.subTest(request_agent_id=request_agent_id, persisted_agent_id=persisted_agent_id):
                workspace_id = f"workspace-{len(request_agent_id)}-{len(persisted_agent_id)}"
                self._write_declared_identity(
                    workspace_id,
                    request_agent_id,
                    declared_workspace_id=workspace_id,
                    declared_agent_id=persisted_agent_id,
                )
                with self.assertRaises(PersistentIdentityCollisionError):
                    self.store.load(workspace_id, request_agent_id)

    def test_case_alias_cannot_observe_or_initialize_original_identity_when_host_aliases_it(self):
        workspace_id = "case-alias-workspace"
        original = self.fabric.create_agent(workspace_id, "Alice")
        original_path = self._identity_path(workspace_id, "Alice")
        alias_path = self._identity_path(workspace_id, "alice")
        if not os.path.exists(alias_path):
            self.skipTest("host filesystem permits distinct Alice/alice agent directories")
        try:
            aliases = os.path.samefile(original_path, alias_path)
        except OSError as exc:
            self.skipTest(f"host cannot demonstrate case aliasing: {exc}")
        if not aliases:
            self.skipTest("host filesystem permits distinct Alice/alice agent directories")

        before = open(original_path, "rb").read()
        with self.assertRaises(HTTPException) as raised:
            self.fabric.create_agent(workspace_id, "alice")
        self.assertEqual(raised.exception.status_code, 409)
        with self.assertRaises(PersistentIdentityCollisionError):
            self.store.load(workspace_id, "alice")

        self.assertEqual(original.agent_id, "Alice")
        self.assertEqual(open(original_path, "rb").read(), before)
        self.assertNotIn(self.fabric._agent_key(workspace_id, "alice"), self.fabric.private_graphs)

    def test_case_sensitive_host_allows_distinct_exact_identities(self):
        workspace_id = "case-sensitive-workspace"
        first = self.fabric.create_agent(workspace_id, "Alice")
        lower_path = self._identity_path(workspace_id, "alice")
        if os.path.exists(lower_path):
            try:
                if os.path.samefile(self._identity_path(workspace_id, "Alice"), lower_path):
                    self.skipTest("host filesystem aliases Alice and alice")
            except OSError as exc:
                self.skipTest(f"host cannot demonstrate distinct case paths: {exc}")

        second = self.fabric.create_agent(workspace_id, "alice")

        self.assertEqual((first.agent_id, second.agent_id), ("Alice", "alice"))
        self.assertEqual(self.store.load(workspace_id, "Alice").agent_id, "Alice")
        self.assertEqual(self.store.load(workspace_id, "alice").agent_id, "alice")


class TestWorkspaceIdentityCollisionF7(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_workspace_collision_f7_")
        self.env = patch.dict(
            os.environ,
            {
                "TORMENT_EMBED_PROVIDER": "hash",
                "TORMENT_CHARACTER_ENABLE": "0",
                "TORMENT_CHECKPOINT_ENABLE": "0",
                "TORMENT_COMPRESS_ENABLE": "0",
                "TORMENT_SRG_ENABLE": "0",
            },
            clear=False,
        )
        self.env.start()
        self.fabric = TormentFabric(data_dir=self.tmpdir)

    def tearDown(self):
        self.fabric.close()
        self.env.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _workspace_root(self, workspace_id):
        return os.path.join(self.tmpdir, "workspaces", workspace_id)

    def _write_workspace_meta(self, workspace_id, declared_workspace_id):
        root = self._workspace_root(workspace_id)
        os.makedirs(root, exist_ok=True)
        with open(os.path.join(root, "workspace_meta.json"), "w", encoding="utf-8") as f:
            json.dump({"workspace_id": declared_workspace_id}, f)

    def test_metadata_backed_exact_workspace_identity_succeeds(self):
        self._write_workspace_meta("workspace", "workspace")

        self.assertEqual(
            _verify_workspace_identity_before_initialization(self.tmpdir, "workspace"),
            _WORKSPACE_IDENTITY_VERIFIED_EXISTING,
        )
        self.assertEqual(self.fabric.get_workspace("workspace").workspace_id, "workspace")

    def test_metadata_backed_workspace_alias_mismatch_fails_closed(self):
        self._write_workspace_meta("workspace", "Workspace")

        with self.assertRaises(HTTPException) as raised:
            self.fabric.get_workspace("workspace")
        self.assertEqual(raised.exception.status_code, 409)

    def test_legacy_exact_directory_entry_is_unverified_until_normal_initialization(self):
        root = self._workspace_root("legacy")
        meta_path = os.path.join(root, "workspace_meta.json")
        os.makedirs(root, exist_ok=True)

        state = _verify_workspace_identity_before_initialization(self.tmpdir, "legacy")

        self.assertEqual(state, _WORKSPACE_IDENTITY_LEGACY_UNVERIFIED)
        self.assertFalse(os.path.exists(meta_path))
        self.assertEqual(self.fabric.get_workspace("legacy").workspace_id, "legacy")
        self.assertTrue(os.path.exists(meta_path))

    def test_legacy_alias_to_same_directory_fails_closed_when_host_aliases_it(self):
        self._workspace_root("Legacy")
        os.makedirs(self._workspace_root("Legacy"), exist_ok=True)
        alias_root = self._workspace_root("legacy")
        if not os.path.exists(alias_root):
            self.skipTest("host filesystem permits distinct Legacy/legacy workspace directories")
        try:
            aliases = os.path.samefile(self._workspace_root("Legacy"), alias_root)
        except OSError as exc:
            self.skipTest(f"host cannot demonstrate workspace aliasing: {exc}")
        if not aliases:
            self.skipTest("host filesystem permits distinct Legacy/legacy workspace directories")

        with self.assertRaises(HTTPException) as raised:
            self.fabric.get_workspace("legacy")
        self.assertEqual(raised.exception.status_code, 409)

    def test_workspace_comparison_does_not_trim_casefold_or_unicode_normalize(self):
        pairs = (
            ("workspace", "Workspace"),
            ("workspace", "workspace "),
            ("\u00e9", "e\u0301"),
        )
        for requested_workspace_id, persisted_workspace_id in pairs:
            with self.subTest(
                requested_workspace_id=requested_workspace_id,
                persisted_workspace_id=persisted_workspace_id,
            ):
                self._write_workspace_meta(requested_workspace_id, persisted_workspace_id)
                with self.assertRaises(HTTPException) as raised:
                    self.fabric.get_workspace(requested_workspace_id)
                self.assertEqual(raised.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
