"""Block B reference foregrounding: caller-controlled /retrieve scope tests."""
from __future__ import annotations

import gc
import os
import tempfile
import unittest
from unittest.mock import patch


from torment_service.fabric import TormentFabric


def _dispose_fabric(fabric: TormentFabric) -> None:
    fabric.close()
    for name in (
        "private_graphs", "workspaces", "agent_states", "_kernel_contexts",
        "_sqlite_indexes", "reference_stores", "reference_active_loads",
        "environment_stores", "_deep_stores",
    ):
        value = getattr(fabric, name, None)
        if isinstance(value, dict):
            value.clear()
    gc.collect()


class TestBlockBReferenceRetrieveIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, self.fabric)

        import torment_service.app as appmod

        self.appmod = appmod
        original_fabric = appmod.fabric
        appmod.fabric = self.fabric
        self.addCleanup(setattr, appmod, "fabric", original_fabric)

    def _prepare_agent(self, workspace_id: str = "ws_a", agent_id: str = "atlas") -> None:
        self.fabric.get_workspace(workspace_id)
        self.fabric.create_agent(workspace_id, agent_id)

    def _ingest_reference(
        self,
        body: str,
        *,
        workspace_id: str = "ws_a",
        title: str = "Reference",
        source_link: str = "internal/reference",
        source_kind: str = "internal_doc",
    ) -> str:
        result = self.fabric.ingest_reference(
            workspace_id=workspace_id,
            title=title,
            body=body,
            source_link=source_link,
            source_kind=source_kind,
        )
        self.assertTrue(result["ok"])
        return result["ref_id"]

    def _retrieve(
        self,
        *,
        workspace_id: str = "ws_a",
        agent_id: str = "atlas",
        scope_tag: object = ...,
        token_budget: int = 1000,
    ) -> dict:
        request = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "query": "reference foregrounding",
            "profile": "research",
            "token_budget": token_budget,
        }
        if scope_tag is not ...:
            request["scope_tag"] = scope_tag
        return self.appmod.retrieve_assembled(self.appmod.AssembleContextReq(**request))

    @staticmethod
    def _reference_blocks(result: dict) -> list[dict]:
        return result["blocks"]["reference_context"]

    def test_matching_scope_foregrounds_whole_reference_body(self) -> None:
        self._prepare_agent()
        ref_id = self._ingest_reference("MATCHING_SCOPE_REFERENCE")
        loaded = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")

        result = self._retrieve(scope_tag="research")

        blocks = self._reference_blocks(result)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["text"], "MATCHING_SCOPE_REFERENCE")
        self.assertEqual(blocks[0]["source"], "reference")
        self.assertEqual(blocks[0]["metadata"]["ref_id"], ref_id)
        self.assertEqual(blocks[0]["metadata"]["load_id"], loaded["load_id"])
        self.assertIn("MATCHING_SCOPE_REFERENCE", result["assembled_text"])

    def test_missing_null_and_empty_scope_never_foreground_references(self) -> None:
        self._prepare_agent()
        ref_id = self._ingest_reference("NO_IMPLICIT_ALL_SCOPES")
        self.fabric.load_reference("ws_a", "atlas", ref_id, "research")

        for scope_tag in (..., None, ""):
            with self.subTest(scope_tag=scope_tag):
                result = self._retrieve(scope_tag=scope_tag)
                self.assertEqual(self._reference_blocks(result), [])
                self.assertNotIn("NO_IMPLICIT_ALL_SCOPES", result["assembled_text"])

    def test_only_exact_workspace_agent_and_scope_match_is_selected(self) -> None:
        self._prepare_agent("ws_a", "atlas")
        self._prepare_agent("ws_a", "beacon")
        self._prepare_agent("ws_b", "atlas")

        visible = self._ingest_reference("VISIBLE_REFERENCE")
        wrong_scope = self._ingest_reference("WRONG_SCOPE_REFERENCE")
        wrong_agent = self._ingest_reference("WRONG_AGENT_REFERENCE")
        other_workspace = self._ingest_reference(
            "OTHER_WORKSPACE_REFERENCE", workspace_id="ws_b"
        )
        self.fabric.load_reference("ws_a", "atlas", visible, "research")
        self.fabric.load_reference("ws_a", "atlas", wrong_scope, "editorial")
        self.fabric.load_reference("ws_a", "beacon", wrong_agent, "research")
        self.fabric.load_reference("ws_b", "atlas", other_workspace, "research")

        result = self._retrieve(scope_tag="research")

        blocks = self._reference_blocks(result)
        self.assertEqual([block["text"] for block in blocks], ["VISIBLE_REFERENCE"])
        self.assertIn("VISIBLE_REFERENCE", result["assembled_text"])
        for sentinel in (
            "WRONG_SCOPE_REFERENCE",
            "WRONG_AGENT_REFERENCE",
            "OTHER_WORKSPACE_REFERENCE",
        ):
            self.assertNotIn(sentinel, result["assembled_text"])

    def test_same_scope_loads_remain_oldest_first_and_duplicate_loads_remain_distinct(self) -> None:
        self._prepare_agent()
        first_ref = self._ingest_reference("OLDEST_REFERENCE")
        second_ref = self._ingest_reference("SECOND_REFERENCE")

        with patch("torment_service.fabric.time.time", side_effect=range(100, 112)):
            first = self.fabric.load_reference("ws_a", "atlas", first_ref, "research")
            second = self.fabric.load_reference("ws_a", "atlas", second_ref, "research")
            duplicate = self.fabric.load_reference("ws_a", "atlas", first_ref, "research")

        result = self._retrieve(scope_tag="research")

        blocks = self._reference_blocks(result)
        self.assertEqual(
            [block["text"] for block in blocks],
            ["OLDEST_REFERENCE", "SECOND_REFERENCE", "OLDEST_REFERENCE"],
        )
        self.assertEqual(
            [block["metadata"]["load_id"] for block in blocks],
            [first["load_id"], second["load_id"], duplicate["load_id"]],
        )
        self.assertEqual(
            [block["metadata"]["ref_id"] for block in blocks].count(first_ref), 2,
        )

    def test_stale_at_load_is_preserved_in_reference_block_metadata(self) -> None:
        self._prepare_agent()
        source_path = os.path.join(self.tempdir.name, "mutable_source.txt")
        with open(source_path, "w", encoding="utf-8") as handle:
            handle.write("source version one")
        ref_id = self._ingest_reference(
            "STALE_REFERENCE_BODY",
            source_link=source_path,
            source_kind="repo_file",
        )
        with open(source_path, "w", encoding="utf-8") as handle:
            handle.write("source version two")
        loaded = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        self.assertTrue(loaded["stale"])

        result = self._retrieve(scope_tag="research")

        block = self._reference_blocks(result)[0]
        self.assertTrue(block["metadata"]["stale_at_load"])
        self.assertNotIn("stale", block["metadata"])

    def test_deleted_reference_under_active_load_is_safely_omitted(self) -> None:
        self._prepare_agent()
        ref_id = self._ingest_reference("DELETED_REFERENCE_BODY")
        self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        self.assertTrue(self.fabric._get_reference_store("ws_a").delete(ref_id))

        result = self._retrieve(scope_tag="research")

        self.assertEqual(self._reference_blocks(result), [])
        self.assertNotIn("DELETED_REFERENCE_BODY", result["assembled_text"])

    def test_retrieve_foregrounding_does_not_mutate_other_memory_boundaries(self) -> None:
        self._prepare_agent()
        agent_key = self.fabric._agent_key("ws_a", "atlas")
        graph = self.fabric.private_graphs[agent_key]
        workspace = self.fabric.get_workspace("ws_a")
        kernel_context = self.fabric.get_kernel_runtime_context("ws_a", "atlas")
        entity_count = len(graph.entities)
        motif_counts = {
            domain_id: len(registry.motifs)
            for domain_id, registry in workspace.motif_regs.items()
        }
        deep_store_keys = set(self.fabric._deep_stores)
        relational_state = dict(self.fabric._srg_relational_ema)
        self.assertFalse(hasattr(self.fabric, "environment_stores"))

        ref_id = self._ingest_reference("BOUNDARY_REFERENCE_BODY")
        loaded = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        active = self.fabric.reference_active_loads[agent_key][loaded["load_id"]]
        active_before = (
            active.ref_id,
            active.scope_tag,
            active.loaded_at_ts,
            active.stale_at_load,
            active.status,
            active.unloaded_at_ts,
        )
        with patch.object(
            self.appmod._thinking_controller_module,
            "_ARCHIVE_RECALL_ENABLE",
            False,
        ), patch.object(self.appmod, "_get_archive_store") as archive_store:
            result = self._retrieve(scope_tag="research")

        self.assertEqual(len(graph.entities), entity_count)
        self.assertIs(
            self.fabric.get_kernel_runtime_context("ws_a", "atlas"), kernel_context
        )
        self.assertEqual(
            {
                domain_id: len(registry.motifs)
                for domain_id, registry in workspace.motif_regs.items()
            },
            motif_counts,
        )
        self.assertEqual(set(self.fabric._deep_stores), deep_store_keys)
        self.assertEqual(self.fabric._srg_relational_ema, relational_state)
        self.assertFalse(hasattr(self.fabric, "environment_stores"))
        self.assertEqual(
            (
                active.ref_id,
                active.scope_tag,
                active.loaded_at_ts,
                active.stale_at_load,
                active.status,
                active.unloaded_at_ts,
            ),
            active_before,
        )
        archive_store.assert_not_called()
        self.assertIn("BOUNDARY_REFERENCE_BODY", result["assembled_text"])


if __name__ == "__main__":
    unittest.main()
