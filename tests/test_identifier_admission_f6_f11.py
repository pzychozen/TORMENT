"""Regression coverage for F6 portable admission and F11 dot rejection."""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from torment_service import app as app_module
from torment_service.checkpoint import _validate_path_component as checkpoint_component
from torment_service.compression import _validate_path_component as compression_component
from torment_service.fabric import TormentFabric, _validate_path_component as fabric_component
from torment_service.identity import IdentityStore
from torment_service.pathing import (
    safe_slug,
    validate_portable_new_identifier,
    validate_structural_path_component,
)
from torment_service.proposals import _validate_path_component as proposal_component


_ACCEPTED_NEW_IDS = (
    "normal",
    "wsE",
    "agE",
    "agentX",
    "ws_q2d_s4wA",
    "agent_q2d_s4wA",
)

_REJECTED_NEW_IDS = (
    "normal.",
    "normal ",
    " normal",
    "CON",
    "con",
    "CON.txt",
    "NUL",
    "COM1",
    "LPT9",
    "a:b",
    "a<b",
    "a>b",
    'a"b',
    "a|b",
    "a?b",
    "a*b",
    "line\nbreak",
    "nul\x00byte",
)


class TestIdentifierValidationLayers(unittest.TestCase):
    def test_structural_layer_preserves_legacy_ids_and_rejects_dot(self):
        for value in _ACCEPTED_NEW_IDS + ("legacy.", "legacy "):
            self.assertEqual(validate_structural_path_component(value), value)

        for value in ("", "..", "a/b", "a\\b", "."):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_structural_path_component(value)
                with self.assertRaises(ValueError):
                    safe_slug(value)

    def test_portable_new_id_admission_is_cross_platform_and_non_transforming(self):
        for value in _ACCEPTED_NEW_IDS:
            with self.subTest(value=value):
                self.assertEqual(validate_portable_new_identifier(value), value)

        for value in _REJECTED_NEW_IDS:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_portable_new_identifier(value)

    def test_representative_wrappers_keep_their_exception_contracts(self):
        for validator in (checkpoint_component, compression_component, proposal_component):
            with self.subTest(validator=validator.__module__):
                with self.assertRaises(ValueError):
                    validator(".", "identifier")

        for validator in (app_module._validate_path_component, fabric_component):
            with self.subTest(validator=validator.__module__):
                with self.assertRaises(HTTPException) as raised:
                    validator(".", "identifier")
                self.assertEqual(raised.exception.status_code, 400)


class TestIdentifierAdmissionSeams(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_f6_f11_")
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
        self.env.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_existing_legacy_agent_is_provisioned_through_fabric_without_normalization(self):
        legacy = IdentityStore(self.tmpdir)
        legacy_workspace_id = "legacy-workspace"
        legacy_agent_id = "agent."
        legacy.create(legacy_workspace_id, legacy_agent_id, seed={"seed_id": ""})
        agents_dir = os.path.join(
            self.tmpdir, "workspaces", legacy_workspace_id, "agents"
        )
        before_entries = sorted(os.listdir(agents_dir))

        legacy_fabric = TormentFabric(data_dir=self.tmpdir)
        loaded = legacy_fabric.create_agent(legacy_workspace_id, legacy_agent_id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.workspace_id, legacy_workspace_id)
        self.assertEqual(loaded.agent_id, legacy_agent_id)
        self.assertEqual(sorted(os.listdir(agents_dir)), before_entries)
        self.assertIsNotNone(legacy.load(legacy_workspace_id, legacy_agent_id))

        with self.assertRaises(HTTPException) as new_agent_error:
            self.fabric.create_agent("new-agent-workspace", "agent.")
        self.assertEqual(new_agent_error.exception.status_code, 400)
        self.assertFalse(
            os.path.exists(
                os.path.join(self.tmpdir, "workspaces", "new-agent-workspace")
            )
        )

    def test_dot_workspace_and_agent_fail_before_container_artifacts(self):
        with self.assertRaises(HTTPException) as workspace_error:
            self.fabric.get_workspace(".")
        self.assertEqual(workspace_error.exception.status_code, 400)
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, "workspaces")))

        with self.assertRaises(HTTPException) as agent_error:
            self.fabric.create_agent("ordinary", ".")
        self.assertEqual(agent_error.exception.status_code, 400)
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, "workspaces")))

    def test_new_workspace_clone_target_domain_and_seed_use_portable_admission(self):
        for workspace_id in ("workspace.", " workspace"):
            with self.subTest(workspace_id=workspace_id):
                with self.assertRaises(HTTPException) as raised:
                    self.fabric.get_workspace(workspace_id)
                self.assertEqual(raised.exception.status_code, 400)

        with self.assertRaises(HTTPException) as clone_error:
            self.fabric.clone_workspace("source", "clone-target.")
        self.assertEqual(clone_error.exception.status_code, 400)

        workspace = self.fabric.get_workspace("ordinary")
        with self.assertRaises(HTTPException) as domain_error:
            workspace.add_domain("domain.")
        self.assertEqual(domain_error.exception.status_code, 400)
        self.assertNotIn("domain.", workspace.domains)

        self.env.stop()
        self.env = patch.dict(
            os.environ,
            {
                "TORMENT_EMBED_PROVIDER": "hash",
                "TORMENT_CHARACTER_ENABLE": "1",
                "TORMENT_CHECKPOINT_ENABLE": "0",
                "TORMENT_COMPRESS_ENABLE": "0",
                "TORMENT_SRG_ENABLE": "0",
            },
            clear=False,
        )
        self.env.start()
        character_fabric = TormentFabric(data_dir=self.tmpdir)
        with self.assertRaises(HTTPException) as seed_error:
            character_fabric.create_agent(
                "seed-workspace",
                "seed-agent",
                seed={"seed_id": "seed.", "seed_text": "A valid seed body."},
            )
        self.assertEqual(seed_error.exception.status_code, 400)
        self.assertIsNone(character_fabric.ident_store.load("seed-workspace", "seed-agent"))

    def test_existing_legacy_domain_remains_usable_and_new_domains_are_admitted(self):
        legacy_workspace_id = "legacy-domain-workspace"
        workspace_root = os.path.join(self.tmpdir, "workspaces", legacy_workspace_id)
        legacy_domain_id = "legacy."
        os.makedirs(
            os.path.join(workspace_root, "domains", legacy_domain_id, "shared"),
            exist_ok=True,
        )
        with open(os.path.join(workspace_root, "domains.json"), "w", encoding="utf-8") as f:
            json.dump({"domains": [legacy_domain_id]}, f)

        legacy_workspace = self.fabric.get_workspace(
            legacy_workspace_id, domains=[legacy_domain_id]
        )
        self.assertIn(legacy_domain_id, legacy_workspace.domains)
        self.fabric.get_workspace(legacy_workspace_id, domains=[legacy_domain_id])
        self.assertIn(legacy_domain_id, legacy_workspace.shared_graphs)

        normal_workspace = self.fabric.get_workspace("normal-domain-workspace")
        normal_workspace.add_domain("research")
        self.assertIn("research", normal_workspace.domains)
        self.fabric.get_workspace("normal-domain-workspace", domains=["research"])

        with self.assertRaises(HTTPException) as invalid_domain_error:
            self.fabric.get_workspace(
                "normal-domain-workspace", domains=["new-domain."]
            )
        self.assertEqual(invalid_domain_error.exception.status_code, 400)
        self.assertNotIn("new-domain.", normal_workspace.domains)

    def test_domain_admission_returns_400_and_unrelated_dimension_mismatch_stays_409(self):
        with self.assertRaises(HTTPException) as new_workspace_error:
            self.fabric.get_workspace("new-domain-workspace", domains=["new-domain."])
        self.assertEqual(new_workspace_error.exception.status_code, 400)

        existing_workspace = self.fabric.get_workspace("existing-domain-workspace")
        with self.assertRaises(HTTPException) as existing_workspace_error:
            self.fabric.get_workspace(
                existing_workspace.workspace_id, domains=["new-domain."]
            )
        self.assertEqual(existing_workspace_error.exception.status_code, 400)

        mismatch_root = os.path.join(self.tmpdir, "workspaces", "dimension-mismatch")
        os.makedirs(mismatch_root, exist_ok=True)
        with open(
            os.path.join(mismatch_root, "workspace_meta.json"), "w", encoding="utf-8"
        ) as f:
            json.dump({"workspace_id": "dimension-mismatch", "embed_dim": 999}, f)
        with self.assertRaises(HTTPException) as mismatch_error:
            self.fabric.get_workspace("dimension-mismatch")
        self.assertEqual(mismatch_error.exception.status_code, 409)

    def test_rest_workspace_create_applies_portable_admission_before_fabric(self):
        request = app_module.WorkspaceCreateReq(workspace_id="rest-workspace.")

        with self.assertRaises(HTTPException) as raised:
            app_module.workspace_create(request)

        self.assertEqual(raised.exception.status_code, 400)

    @unittest.skipUnless(os.name == "nt", "Windows alias characterization")
    def test_windows_new_agent_admission_blocks_trailing_dot_and_space_aliases(self):
        for suffix, alias in (("dot", "agent."), ("space", "agent ")):
            workspace_id = f"alias-{suffix}-workspace"
            with self.subTest(alias=alias):
                with self.assertRaises(HTTPException) as raised:
                    self.fabric.create_agent(workspace_id, alias)
                self.assertEqual(raised.exception.status_code, 400)
                self.assertFalse(
                    os.path.exists(os.path.join(self.tmpdir, "workspaces", workspace_id))
                )


if __name__ == "__main__":
    unittest.main()
