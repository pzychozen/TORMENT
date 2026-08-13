"""Test-only characterization of Block B reference and environment memory.

This file records present behavior; it is deliberately not a redesign or a
normative expansion of Block B.  All storage writes are made below a temporary
data directory and no production module is modified.
"""
from __future__ import annotations

from dataclasses import asdict
import gc
import inspect
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.environment_memory import EnvironmentStore
from torment_service.fabric import TormentFabric
from torment_service.reference_load_ledger import ReferenceLoadLedger
from torment_service.reference_memory import ReferenceStore


def _dispose_fabric(fabric: TormentFabric) -> None:
    """Release Windows-held graph artifacts before TemporaryDirectory cleanup."""
    fabric.close()
    for name in (
        "private_graphs", "workspaces", "agent_states", "_kernel_contexts",
        "_sqlite_indexes", "reference_stores", "reference_active_loads",
        "environment_stores",
    ):
        value = getattr(fabric, name, None)
        if isinstance(value, dict):
            value.clear()
    gc.collect()


class _FabricCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, self.fabric)

    def ingest_reference(self, workspace_id: str = "ws_a") -> str:
        result = self.fabric.ingest_reference(
            workspace_id=workspace_id,
            title="Reference title",
            body="REFERENCE_ARCHAEOLOGY_SENTINEL body",
            source_link="internal/reference/archaeology",
            source_kind="internal_doc",
        )
        self.assertTrue(result["ok"])
        return result["ref_id"]

    def write_observation(
        self, workspace_id: str = "ws_a", scope_tag: str = "shell"
    ) -> str:
        result = self.fabric.write_environment(
            workspace_id=workspace_id,
            target_runtime="test_runtime",
            scope_tag=scope_tag,
            key="network_available",
            value="ENVIRONMENT_ARCHAEOLOGY_SENTINEL",
            evidence_class="observed",
            ownership="system",
            observation_source="archaeology_probe",
        )
        self.assertTrue(result["ok"])
        return result["env_id"]


class TestReferenceLifecycleArchaeology(_FabricCase):
    def test_entry_and_load_ledger_survive_restart_but_active_load_does_not(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        ref_id = self.ingest_reference()
        loaded = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        self.assertEqual(loaded["result_code"], "loaded")

        restarted = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, restarted)
        self.assertEqual(
            restarted._get_reference_store("ws_a").get(ref_id).body,
            "REFERENCE_ARCHAEOLOGY_SENTINEL body",
        )
        self.assertEqual(
            restarted.list_active_loads("ws_a", "atlas")["result_code"],
            "no_active",
        )
        events = ReferenceLoadLedger(
            self.tempdir.name, "ws_a", "atlas"
        ).list_events(ref_id=ref_id)
        self.assertEqual([event.kind for event in events], ["loaded"])

    def test_load_state_is_per_agent_and_reference_storage_is_per_workspace(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        self.fabric.create_agent("ws_a", "beacon")
        ref_id = self.ingest_reference()

        atlas_load = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        self.assertEqual(atlas_load["result_code"], "loaded")
        self.assertEqual(
            self.fabric.list_active_loads("ws_a", "beacon")["result_code"],
            "no_active",
        )
        beacon_load = self.fabric.load_reference("ws_a", "beacon", ref_id, "research")
        self.assertNotEqual(atlas_load["load_id"], beacon_load["load_id"])

        self.fabric.get_workspace("ws_b")
        self.assertIsNone(self.fabric._get_reference_store("ws_b").get(ref_id))
        self.assertEqual(
            self.fabric.load_reference("ws_b", "atlas", ref_id, "research")["result_code"],
            "not_found",
        )

    def test_stale_source_is_still_loadable_without_replacing_entry_identity(self) -> None:
        source_path = os.path.join(self.tempdir.name, "source.txt")
        with open(source_path, "w", encoding="utf-8") as handle:
            handle.write("source version one")
        created = self.fabric.ingest_reference(
            workspace_id="ws_a",
            title="Mutable source",
            body="stored whole object",
            source_link=source_path,
            source_kind="repo_file",
        )
        ref_id = created["ref_id"]
        entry_before = self.fabric._get_reference_store("ws_a").get(ref_id)

        with open(source_path, "w", encoding="utf-8") as handle:
            handle.write("source version two")
        loaded = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        entry_after = self.fabric._get_reference_store("ws_a").get(ref_id)

        self.assertTrue(loaded["stale"])
        self.assertEqual(loaded["ref_id"], ref_id)
        self.assertEqual(entry_after.ref_id, entry_before.ref_id)
        self.assertEqual(entry_after.source_hash, entry_before.source_hash)
        self.assertEqual(entry_after.body, "stored whole object")

    def test_unload_then_reload_reuses_entry_but_creates_a_new_lifecycle_event(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        ref_id = self.ingest_reference()
        first = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        self.assertEqual(
            self.fabric.unload_reference("ws_a", "atlas", first["load_id"])["result_code"],
            "unloaded",
        )
        self.assertEqual(
            self.fabric.list_active_loads("ws_a", "atlas")["result_code"], "no_active"
        )
        second = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        self.assertNotEqual(first["load_id"], second["load_id"])
        self.assertEqual(second["ref_id"], ref_id)
        events = ReferenceLoadLedger(self.tempdir.name, "ws_a", "atlas").list_events(
            ref_id=ref_id
        )
        self.assertEqual([event.kind for event in events], ["loaded", "unloaded", "loaded"])

    def test_duplicate_ref_id_uses_last_jsonl_record_and_malformed_lines_are_skipped(self) -> None:
        store = ReferenceStore(self.tempdir.name, "ws_a")
        entry = store.ingest(
            title="first", body="first body", source_link="internal/one",
            source_kind="internal_doc", provenance={},
        )
        replacement = asdict(entry)
        replacement["title"] = "last"
        replacement["body"] = "last body"
        with open(store.references_path, "a", encoding="utf-8") as handle:
            handle.write("{malformed json}\n")
            handle.write(json.dumps(replacement) + "\n")
            handle.write(json.dumps({"ref_id": "incomplete"}) + "\n")
            handle.write(json.dumps({"ref_id": "legacy", "workspace_id": "ws_a"}) + "\n")

        reloaded = ReferenceStore(self.tempdir.name, "ws_a")
        self.assertEqual(reloaded.reference_count, 2)
        self.assertEqual(reloaded.get(entry.ref_id).title, "last")
        self.assertIsNone(reloaded.get("incomplete"))
        self.assertEqual(reloaded.get("legacy").body, "")

    def test_reference_delete_remains_absent_after_restart(self) -> None:
        store = ReferenceStore(self.tempdir.name, "ws_a")
        entry = store.ingest(
            title="deleted", body="will reappear after restart",
            source_link="internal/deleted", source_kind="internal_doc", provenance={},
        )
        self.assertTrue(store.delete(entry.ref_id))
        self.assertIsNone(store.get(entry.ref_id))
        reloaded = ReferenceStore(self.tempdir.name, "ws_a")
        self.assertIsNone(reloaded.get(entry.ref_id))

    def test_reingest_same_ref_id_after_delete_is_live_after_restart(self) -> None:
        store = ReferenceStore(self.tempdir.name, "ws_a")
        first = store.ingest(
            title="first", body="first body", source_link="internal/first",
            source_kind="internal_doc", provenance={},
        )
        self.assertTrue(store.delete(first.ref_id))
        with patch("torment_service.reference_memory.uuid.uuid4") as new_uuid:
            new_uuid.return_value.hex = first.ref_id.removeprefix("ref_")
            second = store.ingest(
                title="second", body="second body", source_link="internal/second",
                source_kind="internal_doc", provenance={},
            )
        self.assertEqual(second.ref_id, first.ref_id)

        reloaded = ReferenceStore(self.tempdir.name, "ws_a")
        self.assertEqual(reloaded.get(first.ref_id).title, "second")
        self.assertEqual(reloaded.get(first.ref_id).body, "second body")

    def test_same_ref_id_replacement_uses_latest_live_entry_after_restart(self) -> None:
        store = ReferenceStore(self.tempdir.name, "ws_a")
        first = store.ingest(
            title="first", body="first body", source_link="internal/first",
            source_kind="internal_doc", provenance={},
        )
        with patch("torment_service.reference_memory.uuid.uuid4") as new_uuid:
            new_uuid.return_value.hex = first.ref_id.removeprefix("ref_")
            store.ingest(
                title="latest", body="latest body", source_link="internal/latest",
                source_kind="internal_doc", provenance={},
            )

        reloaded = ReferenceStore(self.tempdir.name, "ws_a")
        self.assertEqual(reloaded.reference_count, 1)
        self.assertEqual(reloaded.get(first.ref_id).title, "latest")

    def test_deleted_reference_does_not_affect_unrelated_references_after_restart(self) -> None:
        store = ReferenceStore(self.tempdir.name, "ws_a")
        deleted = store.ingest(
            title="deleted", body="deleted body", source_link="internal/deleted",
            source_kind="internal_doc", provenance={},
        )
        retained = store.ingest(
            title="retained", body="retained body", source_link="internal/retained",
            source_kind="internal_doc", provenance={},
        )
        self.assertTrue(store.delete(deleted.ref_id))

        reloaded = ReferenceStore(self.tempdir.name, "ws_a")
        self.assertIsNone(reloaded.get(deleted.ref_id))
        self.assertEqual(reloaded.get(retained.ref_id).body, "retained body")

    def test_unsupported_source_kind_is_rejected_at_fabric_and_store_boundaries(self) -> None:
        result = self.fabric.ingest_reference(
            workspace_id="ws_a", title="unknown source kind", body="body",
            source_link="opaque://source", source_kind="unregistered_kind",
        )
        self.assertEqual(result, {
            "ok": False, "result_code": "unsupported_source_kind", "ref_id": "",
        })
        store = ReferenceStore(self.tempdir.name, "ws_a")
        with self.assertRaises(ValueError):
            store.ingest(
                title="unknown", body="body", source_link="opaque://source",
                source_kind="unregistered_kind", provenance={},
            )
        self.assertEqual(store.reference_count, 0)
        self.assertFalse(os.path.exists(store.references_path))

    def test_all_declared_source_kinds_remain_accepted(self) -> None:
        store = ReferenceStore(self.tempdir.name, "ws_a")
        for source_kind in ("repo_file", "url", "internal_doc", "generated"):
            with self.subTest(source_kind=source_kind):
                entry = store.ingest(
                    title=source_kind, body="body", source_link="internal/source",
                    source_kind=source_kind, provenance={},
                )
                self.assertEqual(entry.source_kind, source_kind)

    def test_legacy_persisted_source_kind_remains_loadable(self) -> None:
        store = ReferenceStore(self.tempdir.name, "ws_a")
        entry = store.ingest(
            title="legacy", body="legacy body", source_link="legacy/source",
            source_kind="internal_doc", provenance={},
        )
        legacy = asdict(entry)
        legacy["source_kind"] = "legacy_source_kind"
        with open(store.references_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(legacy) + "\n")

        reloaded = ReferenceStore(self.tempdir.name, "ws_a")
        self.assertEqual(reloaded.get(entry.ref_id).source_kind, "legacy_source_kind")

    def test_reference_operations_leave_existing_core_and_kernel_state_untouched(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        agent_key = self.fabric._agent_key("ws_a", "atlas")
        graph = self.fabric.private_graphs[agent_key]
        state = self.fabric.agent_states[agent_key]
        runtime_context = self.fabric.get_kernel_runtime_context("ws_a", "atlas")
        before_entities = len(graph.entities)

        ref_id = self.ingest_reference()
        loaded = self.fabric.load_reference("ws_a", "atlas", ref_id, "research")
        self.fabric.unload_reference("ws_a", "atlas", loaded["load_id"])

        self.assertEqual(len(graph.entities), before_entities)
        self.assertIs(self.fabric.agent_states[agent_key], state)
        self.assertIs(
            self.fabric.get_kernel_runtime_context("ws_a", "atlas"), runtime_context
        )

    def test_loaded_reference_is_absent_from_actual_retrieve_assembly(self) -> None:
        """Characterizes the currently unwired BLOCK_REFERENCE path."""
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        ref_id = self.ingest_reference()
        self.fabric.load_reference("ws_a", "atlas", ref_id, "research")

        import torment_service.app as appmod

        original_fabric = appmod.fabric
        appmod.fabric = self.fabric
        self.addCleanup(setattr, appmod, "fabric", original_fabric)
        result = appmod.retrieve_assembled(appmod.AssembleContextReq(
            workspace_id="ws_a", agent_id="atlas", query="archaeology",
        ))

        self.assertNotIn("REFERENCE_ARCHAEOLOGY_SENTINEL", result["assembled_text"])
        self.assertEqual(result["blocks"]["reference_context"], [])


class TestReferenceScopeContractArchaeology(_FabricCase):
    """Characterize scope filtering without proposing retrieval wiring."""

    def test_scope_filter_is_exact_all_scopes_are_visible_and_loads_are_not_deduped(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        first_ref = self.ingest_reference()
        second_ref = self.fabric.ingest_reference(
            workspace_id="ws_a",
            title="Second reference",
            body="SECOND_REFERENCE_SCOPE_SENTINEL",
            source_link="internal/reference/second",
            source_kind="internal_doc",
        )["ref_id"]

        # Load one reference twice into different scopes and a second reference
        # into the first scope.  Monotonic timestamps make the documented
        # oldest-first order mechanically observable.
        with patch("torment_service.fabric.time.time", side_effect=range(100, 112)):
            first_research = self.fabric.load_reference(
                "ws_a", "atlas", first_ref, "research"
            )
            second_research = self.fabric.load_reference(
                "ws_a", "atlas", second_ref, "research"
            )
            first_editorial = self.fabric.load_reference(
                "ws_a", "atlas", first_ref, "editorial"
            )

        research = self.fabric.list_active_loads("ws_a", "atlas", "research")["loads"]
        editorial = self.fabric.list_active_loads("ws_a", "atlas", "editorial")["loads"]
        all_scopes = self.fabric.list_active_loads("ws_a", "atlas")["loads"]

        self.assertEqual(
            [load["load_id"] for load in research],
            [first_research["load_id"], second_research["load_id"]],
        )
        self.assertEqual(
            [load["load_id"] for load in editorial],
            [first_editorial["load_id"]],
        )
        self.assertEqual(
            [load["load_id"] for load in all_scopes],
            [
                first_research["load_id"],
                second_research["load_id"],
                first_editorial["load_id"],
            ],
        )
        self.assertEqual(
            [load["ref_id"] for load in all_scopes].count(first_ref), 2,
            "list_active_loads returns distinct active load events, not one ref_id-deduped entry",
        )

    def test_scope_names_are_agent_and_workspace_isolated_and_unload_targets_one_load(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        self.fabric.create_agent("ws_a", "beacon")
        shared_workspace_ref = self.ingest_reference()

        atlas_shared = self.fabric.load_reference(
            "ws_a", "atlas", shared_workspace_ref, "shared"
        )
        atlas_private = self.fabric.load_reference(
            "ws_a", "atlas", shared_workspace_ref, "private"
        )
        beacon_shared = self.fabric.load_reference(
            "ws_a", "beacon", shared_workspace_ref, "shared"
        )

        self.assertEqual(
            [load["load_id"] for load in self.fabric.list_active_loads("ws_a", "atlas", "shared")["loads"]],
            [atlas_shared["load_id"]],
        )
        self.assertEqual(
            [load["load_id"] for load in self.fabric.list_active_loads("ws_a", "beacon", "shared")["loads"]],
            [beacon_shared["load_id"]],
        )

        self.fabric.get_workspace("ws_b")
        self.fabric.create_agent("ws_b", "atlas")
        workspace_b_ref = self.ingest_reference("ws_b")
        workspace_b_load = self.fabric.load_reference(
            "ws_b", "atlas", workspace_b_ref, "shared"
        )
        self.assertEqual(
            [load["load_id"] for load in self.fabric.list_active_loads("ws_b", "atlas", "shared")["loads"]],
            [workspace_b_load["load_id"]],
        )

        self.assertEqual(
            self.fabric.unload_reference("ws_a", "atlas", atlas_shared["load_id"])["result_code"],
            "unloaded",
        )
        self.assertEqual(
            [load["load_id"] for load in self.fabric.list_active_loads("ws_a", "atlas")["loads"]],
            [atlas_private["load_id"]],
        )
        self.assertEqual(
            [load["load_id"] for load in self.fabric.list_active_loads("ws_a", "beacon")["loads"]],
            [beacon_shared["load_id"]],
        )

    def test_public_active_load_api_has_scope_filter_but_no_ref_or_session_selector(self) -> None:
        list_params = inspect.signature(self.fabric.list_active_loads).parameters
        load_params = inspect.signature(self.fabric.load_reference).parameters
        unload_params = inspect.signature(self.fabric.unload_reference).parameters

        self.assertEqual(tuple(list_params), ("workspace_id", "agent_id", "scope_tag"))
        self.assertEqual(list_params["scope_tag"].default, None)
        self.assertNotIn("ref_id", list_params)
        self.assertNotIn("session_id", list_params)
        self.assertNotIn("session_id", load_params)
        self.assertEqual(tuple(unload_params), ("workspace_id", "agent_id", "load_id"))

    def test_none_scope_is_accepted_on_load_but_is_not_an_exact_list_filter(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        ref_id = self.ingest_reference()

        loaded = self.fabric.load_reference("ws_a", "atlas", ref_id, None)
        self.assertEqual(loaded["result_code"], "loaded")
        self.assertEqual(
            self.fabric.list_active_loads("ws_a", "atlas", "research")["result_code"],
            "no_active",
        )
        all_scopes = self.fabric.list_active_loads("ws_a", "atlas", None)["loads"]
        self.assertEqual(len(all_scopes), 1)
        self.assertIsNone(all_scopes[0]["scope_tag"])

    def test_retrieve_request_has_optional_scope_but_no_session_field(self) -> None:
        import torment_service.app as appmod

        fields = getattr(appmod.AssembleContextReq, "model_fields", None)
        if fields is None:
            fields = appmod.AssembleContextReq.__fields__
        self.assertIn("scope_tag", fields)
        self.assertIsNone(fields["scope_tag"].default)
        self.assertNotIn("session_id", fields)


class TestEnvironmentLifecycleArchaeology(_FabricCase):
    def test_evidence_classes_and_empty_inference_rule_set(self) -> None:
        user_asserted = self.fabric.write_environment(
            workspace_id="ws_a", target_runtime="runtime", scope_tag="shell",
            key="user_setting", value=True, evidence_class="user_asserted",
            ownership="user", asserted_by="operator",
        )
        observed = self.write_observation()
        inferred = self.fabric.write_environment(
            workspace_id="ws_a", target_runtime="runtime", scope_tag="shell",
            key="guessed", value="model-looking text", evidence_class="inferred",
            ownership="system", inference_rule="unratified_rule",
        )
        self.assertTrue(user_asserted["ok"])
        self.assertTrue(observed)
        self.assertEqual(inferred, {
            "ok": False, "result_code": "unknown_inference_rule", "env_id": "",
        })

    def test_environment_restart_scope_filter_and_consult_redaction(self) -> None:
        self.write_observation(scope_tag="shell")
        self.write_observation(scope_tag="container")
        restarted = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, restarted)
        result = restarted.consult_environment(
            "ws_a", "run_command", "shell", relevance_fields=["network_available"]
        )

        self.assertEqual(result["result_code"], "consulted")
        self.assertEqual(len(result["facts"]), 1)
        fact = result["facts"][0]
        self.assertEqual(fact["key"], "network_available")
        for redacted in (
            "env_id", "workspace_id", "target_runtime", "scope_tag", "ownership",
            "provenance", "created_ts", "metadata",
        ):
            self.assertNotIn(redacted, fact)

    def test_environment_is_workspace_shared_but_scope_tag_is_strict(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        self.fabric.create_agent("ws_a", "beacon")
        env_id = self.write_observation(scope_tag="shell")

        # consult has no agent parameter: the fact is workspace scoped.
        self.assertIsNotNone(self.fabric._get_environment_store("ws_a").get(env_id))
        self.assertEqual(
            self.fabric.consult_environment("ws_a", "run", "other")["facts"], []
        )
        self.assertEqual(
            self.fabric.consult_environment("ws_b", "run", "shell")["facts"], []
        )

    def test_duplicate_logical_key_appends_distinct_entries_instead_of_overwriting(self) -> None:
        first = self.write_observation()
        second = self.fabric.write_environment(
            workspace_id="ws_a", target_runtime="test_runtime", scope_tag="shell",
            key="network_available", value="second observation",
            evidence_class="observed", ownership="system",
            observation_source="archaeology_probe_second",
        )
        self.assertTrue(second["ok"])
        self.assertNotEqual(first, second["env_id"])
        result = self.fabric.consult_environment("ws_a", "run", "shell")
        self.assertEqual(len(result["facts"]), 2)
        self.assertEqual(
            {fact["value"] for fact in result["facts"]},
            {"ENVIRONMENT_ARCHAEOLOGY_SENTINEL", "second observation"},
        )

    def test_target_runtime_is_stored_metadata_not_a_consult_filter(self) -> None:
        first = self.write_observation(scope_tag="shell")
        second = self.fabric.write_environment(
            workspace_id="ws_a", target_runtime="other_runtime", scope_tag="shell",
            key="other_runtime_key", value="other runtime value",
            evidence_class="observed", ownership="system",
            observation_source="other_runtime_probe",
        )
        self.assertTrue(second["ok"])
        store = self.fabric._get_environment_store("ws_a")
        self.assertEqual(store.get(first).target_runtime, "test_runtime")
        self.assertEqual(store.get(second["env_id"]).target_runtime, "other_runtime")
        result = self.fabric.consult_environment("ws_a", "run", "shell")
        self.assertEqual(
            {fact["key"] for fact in result["facts"]},
            {"network_available", "other_runtime_key"},
        )

    def test_environment_load_accepts_schema_incomplete_legacy_record(self) -> None:
        store = EnvironmentStore(self.tempdir.name, "ws_a")
        legacy = {
            "env_id": "env_legacy", "workspace_id": "ws_a",
            "scope_tag": "shell", "key": "legacy_key",
        }
        with open(store.entries_path, "a", encoding="utf-8") as handle:
            handle.write("{malformed json}\n")
            handle.write(json.dumps(legacy) + "\n")

        reloaded = EnvironmentStore(self.tempdir.name, "ws_a")
        entry = reloaded.get("env_legacy")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.evidence_class, "")
        self.assertEqual(reloaded.consult("run", "shell").facts[0].key, "legacy_key")

    def test_environment_never_enters_query_or_retrieve_output(self) -> None:
        self.fabric.get_workspace("ws_a")
        self.fabric.create_agent("ws_a", "atlas")
        self.write_observation()

        query_result = self.fabric.query("ws_a", "atlas", "ENVIRONMENT_ARCHAEOLOGY_SENTINEL", top_k=100)
        self.assertNotIn("ENVIRONMENT_ARCHAEOLOGY_SENTINEL", json.dumps(query_result))

        import torment_service.app as appmod

        original_fabric = appmod.fabric
        appmod.fabric = self.fabric
        self.addCleanup(setattr, appmod, "fabric", original_fabric)
        assembled = appmod.retrieve_assembled(appmod.AssembleContextReq(
            workspace_id="ws_a", agent_id="atlas", query="ENVIRONMENT_ARCHAEOLOGY_SENTINEL",
        ))
        self.assertNotIn("ENVIRONMENT_ARCHAEOLOGY_SENTINEL", assembled["assembled_text"])


if __name__ == "__main__":
    unittest.main()
