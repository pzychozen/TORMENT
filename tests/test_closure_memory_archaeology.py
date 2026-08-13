"""Test-only characterization of current Block C closure behavior.

These tests use isolated temporary data directories.  They document current
behavior, including fault-injected ledger/store divergence, without changing
any production behavior or treating malformed JSONL as a repair target.
"""
from __future__ import annotations

from dataclasses import asdict
import gc
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.closure_ledger import ClosureLedger
from torment_service.closure_memory import ClosureStore
from torment_service.fabric import TormentFabric
from torment_service.provenance_v1 import ProvenanceV1


def _dispose_fabric(fabric: TormentFabric) -> None:
    """Release Windows-held graph artifacts before temporary cleanup."""
    fabric.close()
    for name in (
        "private_graphs", "workspaces", "agent_states", "_kernel_contexts",
        "_sqlite_indexes", "closure_stores",
    ):
        value = getattr(fabric, name, None)
        if isinstance(value, dict):
            value.clear()
    gc.collect()


class _ClosureCase(unittest.TestCase):
    workspace_id = "closure_ws_a"

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.env = patch.dict(os.environ, {"TORMENT_EMBED_PROVIDER": "hash"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, self.fabric)
        self.fabric.get_workspace(self.workspace_id)
        self.fabric.create_agent(self.workspace_id, "scope_seed")
        scope_seed = self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id="scope_seed",
            text="Closure scope seed.",
            step=1,
        )
        self.scope_eid = int(scope_seed["eid"])

    def proposal_kwargs(self, *, scope=None, deferred=None) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "arc_name": "Closure archaeology arc",
            "arc_kind": "feature",
            "scope": [self.scope_eid] if scope is None else scope,
            "what_it_was": "A mechanical closure lifecycle characterization.",
            "what_worked": "Explicit lifecycle events were recorded.",
            "what_surprised": "Nothing beyond the test boundary.",
            "what_to_carry_forward": "Keep closure separate from retrieval.",
            "deferred_or_open_items": [] if deferred is None else deferred,
        }

    def propose_ratify_commit(self, *, scope=None, deferred=None) -> dict:
        proposed = self.fabric.propose_closure(
            **self.proposal_kwargs(scope=scope, deferred=deferred)
        )
        self.assertTrue(proposed["ok"])
        ratified = self.fabric.ratify_closure(
            self.workspace_id, proposed["closure_id"], ratifier="operator"
        )
        self.assertTrue(ratified["ok"])
        committed = self.fabric.commit_closure(
            self.workspace_id, proposed["closure_id"], ratifier="operator"
        )
        self.assertTrue(committed["ok"])
        return proposed

    def restarted(self) -> TormentFabric:
        fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, fabric)
        return fabric


class TestClosureLifecycleRestartArchaeology(_ClosureCase):
    def test_proposed_ratified_and_committed_states_replay_literally(self) -> None:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        self.assertTrue(proposed["ok"])
        closure_id = proposed["closure_id"]
        version_id = proposed["version_id"]

        store = self.fabric._get_closure_store(self.workspace_id)
        ledger = self.fabric._get_closure_ledger(self.workspace_id)
        self.assertEqual(store.get_latest_version(closure_id).version_id, version_id)
        self.assertEqual(ledger.get_latest_event_kind(closure_id), "proposed")

        restarted = self.restarted()
        self.assertEqual(
            restarted._get_closure_ledger(self.workspace_id).get_latest_event_kind(closure_id),
            "proposed",
        )

        self.assertTrue(
            restarted.ratify_closure(self.workspace_id, closure_id, ratifier="operator")["ok"]
        )
        self.assertEqual(
            restarted._get_closure_ledger(self.workspace_id).get_latest_event_kind(closure_id),
            "ratified",
        )

        restarted_again = self.restarted()
        committed = restarted_again.commit_closure(
            self.workspace_id, closure_id, ratifier="operator"
        )
        self.assertEqual(committed["result_code"], "committed")

        final = self.restarted()
        final_ledger = final._get_closure_ledger(self.workspace_id)
        self.assertEqual(final_ledger.get_latest_event_kind(closure_id), "committed")
        self.assertEqual(
            [event.kind for event in final_ledger.list_events(closure_id=closure_id)],
            ["proposed", "ratified", "committed"],
        )
        self.assertEqual(
            final.get_closure(self.workspace_id, closure_id)["version_id"], version_id
        )

    def test_wrong_workspace_and_unknown_closure_are_isolated(self) -> None:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        closure_id = proposed["closure_id"]

        self.assertEqual(
            self.fabric.ratify_closure("closure_ws_b", closure_id, ratifier="operator"),
            {"ok": False, "result_code": "not_found", "closure_id": closure_id},
        )
        self.assertIsNone(self.fabric.get_closure("closure_ws_b", closure_id))
        self.assertEqual(self.fabric.list_closures("closure_ws_b"), [])
        self.assertEqual(
            self.fabric.commit_closure(
                self.workspace_id, "closure_does_not_exist", ratifier="operator"
            )["result_code"],
            "not_found",
        )


class TestClosureVersionHistoryArchaeology(_ClosureCase):
    def test_three_versions_remain_readable_and_replay_in_append_order(self) -> None:
        proposed = self.propose_ratify_commit()
        closure_id = proposed["closure_id"]
        v1 = proposed["version_id"]
        v2 = self.fabric.revise_closure(
            self.workspace_id,
            closure_id,
            {"what_to_carry_forward": "Carry forward version two."},
            ratifier="operator",
        )
        v3 = self.fabric.revise_closure(
            self.workspace_id,
            closure_id,
            {"what_to_carry_forward": "Carry forward version three."},
            ratifier="operator",
        )
        self.assertTrue(v2["ok"])
        self.assertTrue(v3["ok"])
        self.assertEqual(v2["parent_version_id"], v1)
        self.assertEqual(v3["parent_version_id"], v2["version_id"])

        restarted = self.restarted()
        store = restarted._get_closure_store(self.workspace_id)
        versions = store.list_versions(closure_id)
        self.assertEqual([version.version_id for version in versions], [v1, v2["version_id"], v3["version_id"]])
        self.assertEqual(
            restarted.get_closure(self.workspace_id, closure_id, v1)["what_to_carry_forward"],
            "Keep closure separate from retrieval.",
        )
        self.assertEqual(
            restarted.get_closure(self.workspace_id, closure_id, v2["version_id"])["what_to_carry_forward"],
            "Carry forward version two.",
        )
        latest = restarted.get_closure(self.workspace_id, closure_id)
        self.assertEqual(latest["version_id"], v3["version_id"])
        self.assertEqual(latest["what_to_carry_forward"], "Carry forward version three.")
        self.assertEqual(
            [item["version_id"] for item in latest["version_history"]],
            [v2["version_id"], v3["version_id"]],
        )

    def test_manual_duplicate_version_row_is_not_rejected_during_replay(self) -> None:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        store = self.fabric._get_closure_store(self.workspace_id)
        original = store.get_latest_version(proposed["closure_id"])
        duplicate = asdict(original)
        duplicate["what_it_was"] = "MANUAL_DUPLICATE_VERSION_ROW"
        store._append_jsonl(store.closures_path, duplicate)

        reloaded = ClosureStore(self.tempdir.name, self.workspace_id)
        versions = reloaded.list_versions(proposed["closure_id"])
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version_id, versions[1].version_id)
        self.assertEqual(
            reloaded.get_version(proposed["closure_id"], proposed["version_id"]).what_it_was,
            "A mechanical closure lifecycle characterization.",
        )
        self.assertEqual(reloaded.get_latest_version(proposed["closure_id"]).what_it_was, "MANUAL_DUPLICATE_VERSION_ROW")


class TestClosureBoundaryGapsArchaeology(_ClosureCase):
    def test_scope_rejects_foreign_and_nonexistent_eids(self) -> None:
        self.fabric.ingest(
            workspace_id="closure_ws_b", agent_id="beacon", text="Foreign scope filler.", step=1
        )
        foreign = self.fabric.ingest(
            workspace_id="closure_ws_b", agent_id="beacon", text="Foreign scope sentinel.", step=1
        )
        foreign_eid = int(foreign["eid"])
        foreign_result = self.fabric.propose_closure(
            **self.proposal_kwargs(scope=[foreign_eid])
        )
        self.assertFalse(foreign_result["ok"])
        self.assertEqual(foreign_result["result_code"], "invalid_scope")
        self.assertEqual(foreign_result["invalid_eids"], [foreign_eid])

        nonexistent_result = self.fabric.propose_closure(
            **self.proposal_kwargs(scope=[987654321])
        )
        self.assertFalse(nonexistent_result["ok"])
        self.assertEqual(nonexistent_result["result_code"], "invalid_scope")
        self.assertEqual(nonexistent_result["invalid_eids"], [987654321])

    def test_scope_duplicates_are_normalized_in_first_seen_order(self) -> None:
        self.fabric.create_agent(self.workspace_id, "atlas")
        first = self.fabric.ingest(
            workspace_id=self.workspace_id, agent_id="atlas", text="First scope sentinel.", step=1
        )
        second = self.fabric.ingest(
            workspace_id=self.workspace_id, agent_id="atlas", text="Second scope sentinel.", step=2
        )
        proposed = self.fabric.propose_closure(
            **self.proposal_kwargs(
                scope=[int(first["eid"]), int(second["eid"]), int(first["eid"])]
            )
        )
        self.assertTrue(proposed["ok"])
        stored = self.fabric.get_closure(self.workspace_id, proposed["closure_id"])
        self.assertEqual(stored["scope"], [int(first["eid"]), int(second["eid"])])

    def test_revision_rejects_scope_with_no_workspace_candidate(self) -> None:
        self.fabric.create_agent(self.workspace_id, "atlas")
        memory = self.fabric.ingest(
            workspace_id=self.workspace_id, agent_id="atlas", text="Revision scope sentinel.", step=1
        )
        proposed = self.propose_ratify_commit(scope=[int(memory["eid"])])
        result = self.fabric.revise_closure(
            self.workspace_id,
            proposed["closure_id"],
            {"scope": [987654321]},
            ratifier="operator",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["result_code"], "invalid_scope")
        self.assertEqual(result["invalid_eids"], [987654321])

    def test_revision_normalizes_scope_duplicates_in_first_seen_order(self) -> None:
        self.fabric.create_agent(self.workspace_id, "atlas")
        self.fabric.ingest(
            workspace_id=self.workspace_id, agent_id="atlas", text="Revision duplicate filler.", step=1
        )
        second = self.fabric.ingest(
            workspace_id=self.workspace_id, agent_id="atlas", text="Revision duplicate sentinel.", step=2
        )
        proposed = self.propose_ratify_commit()
        result = self.fabric.revise_closure(
            self.workspace_id,
            proposed["closure_id"],
            {"scope": [self.scope_eid, int(second["eid"]), self.scope_eid]},
            ratifier="operator",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            self.fabric.get_closure(self.workspace_id, proposed["closure_id"])["scope"],
            [self.scope_eid, int(second["eid"])],
        )

    def test_revision_rejects_an_empty_scope(self) -> None:
        proposed = self.propose_ratify_commit()
        revised = self.fabric.revise_closure(
            self.workspace_id, proposed["closure_id"], {"scope": []}, ratifier="operator"
        )
        self.assertFalse(revised["ok"])
        self.assertEqual(revised["result_code"], "missing_required_field")
        self.assertEqual(revised["missing_field"], "scope")

    def test_model_looking_ratifier_is_accepted_as_free_text(self) -> None:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        closure_id = proposed["closure_id"]
        self.assertTrue(
            self.fabric.ratify_closure(
                self.workspace_id, closure_id, ratifier="llm:model-only"
            )["ok"]
        )
        committed = self.fabric.commit_closure(
            self.workspace_id, closure_id, ratifier="llm:model-only"
        )
        self.assertTrue(committed["ok"])
        event = self.fabric._get_closure_ledger(self.workspace_id).list_events(
            closure_id=closure_id, kind="committed"
        )[0]
        self.assertEqual(event.ratifier, "llm:model-only")

    def test_historical_closure_ratification_can_commit_a_revised_version(self) -> None:
        proposed = self.propose_ratify_commit()
        closure_id = proposed["closure_id"]
        revised = self.fabric.revise_closure(
            self.workspace_id,
            closure_id,
            {"what_worked": "A revised field."},
            ratifier="operator",
        )
        self.assertTrue(revised["ok"])
        recommitted = self.fabric.commit_closure(
            self.workspace_id, closure_id, ratifier="operator"
        )
        self.assertTrue(recommitted["ok"])
        self.assertEqual(recommitted["version_id"], revised["version_id"])
        self.assertEqual(
            [event.kind for event in self.fabric._get_closure_ledger(self.workspace_id).list_events(closure_id=closure_id)],
            ["proposed", "ratified", "committed", "revised", "committed"],
        )


class TestClosureDurabilityFaultInjectionArchaeology(_ClosureCase):
    def test_active_baton_honesty_check_survives_restart_without_agent_load(self) -> None:
        self.fabric.create_agent(self.workspace_id, "atlas")
        baton = self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id="atlas",
            text="BATON_RESTART_HONESTY_SENTINEL",
            step=1,
            scope="private",
            provenance=ProvenanceV1.for_baton_ingest().to_dict(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": {
                "owner": "user",
                "expires_when": "explicit completion",
                "resolution_condition": "user confirmation",
            }},
        )
        baton_eid = int(baton["eid"])
        proposed = self.fabric.propose_closure(**self.proposal_kwargs(scope=[baton_eid]))
        self.assertTrue(
            self.fabric.ratify_closure(
                self.workspace_id, proposed["closure_id"], ratifier="operator"
            )["ok"]
        )

        restarted = self.restarted()
        self.assertEqual(restarted.private_graphs, {})
        committed = restarted.commit_closure(
            self.workspace_id, proposed["closure_id"], ratifier="operator"
        )
        self.assertFalse(committed["ok"])
        self.assertEqual(committed["result_code"], "open_items_mismatch")
        self.assertEqual(
            [item["eid"] for item in committed["unresolved"]["unresolved_batons"]],
            [baton_eid],
        )
        self.assertEqual(restarted.private_graphs, {})

    def test_resolved_expired_and_inactive_batons_do_not_block_after_restart(self) -> None:
        self.fabric.create_agent(self.workspace_id, "atlas")
        resolved = self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id="atlas",
            text="BATON_NONACTIVE_RESOLVED",
            step=1,
            scope="private",
            provenance=ProvenanceV1.for_baton_ingest().to_dict(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": {
                "owner": "user",
                "expires_when": "explicit completion",
                "resolution_condition": "user confirmation",
            }},
        )
        self.assertEqual(
            self.fabric.resolve_baton(
                self.workspace_id, "atlas", int(resolved["eid"]), outcome="complete"
            )["result_code"],
            "resolved",
        )
        closures = []
        resolved_proposal = self.fabric.propose_closure(
            **self.proposal_kwargs(scope=[int(resolved["eid"])])
        )
        closures.append(resolved_proposal["closure_id"])
        self.assertTrue(
            self.fabric.ratify_closure(
                self.workspace_id, resolved_proposal["closure_id"], ratifier="operator"
            )["ok"]
        )

        for step, status in enumerate(("expired", "inactive"), start=2):
            baton = self.fabric.ingest(
                workspace_id=self.workspace_id,
                agent_id="atlas",
                text=f"BATON_NONACTIVE_{status}",
                step=step,
                scope="private",
                provenance=ProvenanceV1.for_baton_ingest().to_dict(),
                memory_class="baton",
                extra_payload={"baton_lifecycle": {
                    "owner": "user",
                    "expires_when": "explicit completion",
                    "resolution_condition": "user confirmation",
                    "status": status,
                }},
            )
            proposed = self.fabric.propose_closure(
                **self.proposal_kwargs(scope=[int(baton["eid"])])
            )
            closures.append(proposed["closure_id"])
            self.assertTrue(
                self.fabric.ratify_closure(
                    self.workspace_id, proposed["closure_id"], ratifier="operator"
                )["ok"]
            )

        restarted = self.restarted()
        for closure_id in closures:
            committed = restarted.commit_closure(
                self.workspace_id, closure_id, ratifier="operator"
            )
            self.assertTrue(committed["ok"])

    def test_out_of_scope_active_baton_does_not_block_after_restart(self) -> None:
        self.fabric.create_agent(self.workspace_id, "atlas")
        self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id="atlas",
            text="BATON_OUT_OF_SCOPE_SENTINEL",
            step=1,
            scope="private",
            provenance=ProvenanceV1.for_baton_ingest().to_dict(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": {
                "owner": "user",
                "expires_when": "explicit completion",
                "resolution_condition": "user confirmation",
            }},
        )
        core = self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id="atlas",
            text="CORE_SCOPE_SENTINEL",
            step=2,
            scope="private",
        )
        proposed = self.fabric.propose_closure(
            **self.proposal_kwargs(scope=[int(core["eid"])])
        )
        self.assertTrue(
            self.fabric.ratify_closure(
                self.workspace_id, proposed["closure_id"], ratifier="operator"
            )["ok"]
        )

        restarted = self.restarted()
        committed = restarted.commit_closure(
            self.workspace_id, proposed["closure_id"], ratifier="operator"
        )
        self.assertTrue(committed["ok"])

    def test_proposal_store_write_can_survive_a_failed_proposed_ledger_event(self) -> None:
        with patch.object(ClosureLedger, "add_event", side_effect=OSError("ledger unavailable")):
            with self.assertRaisesRegex(OSError, "ledger unavailable"):
                self.fabric.propose_closure(**self.proposal_kwargs())

        reloaded_store = ClosureStore(self.tempdir.name, self.workspace_id)
        closure_ids = reloaded_store.list_closures()
        self.assertEqual(len(closure_ids), 1)
        self.assertEqual(len(reloaded_store.list_versions(closure_ids[0])), 1)
        self.assertEqual(
            ClosureLedger(self.tempdir.name, self.workspace_id).list_events(closure_id=closure_ids[0]),
            [],
        )

    def test_revision_store_write_can_survive_a_failed_revised_ledger_event(self) -> None:
        proposed = self.propose_ratify_commit()
        closure_id = proposed["closure_id"]
        with patch.object(ClosureLedger, "add_event", side_effect=OSError("ledger unavailable")):
            with self.assertRaisesRegex(OSError, "ledger unavailable"):
                self.fabric.revise_closure(
                    self.workspace_id,
                    closure_id,
                    {"what_surprised": "This revision has no ledger event."},
                    ratifier="operator",
                )

        restarted = self.restarted()
        store = restarted._get_closure_store(self.workspace_id)
        versions = store.list_versions(closure_id)
        events = restarted._get_closure_ledger(self.workspace_id).list_events(closure_id=closure_id)
        self.assertEqual(len(versions), 2)
        self.assertEqual(events[-1].kind, "committed")
        self.assertEqual(events[-1].version_id, proposed["version_id"])
        self.assertNotEqual(store.get_latest_version(closure_id).version_id, events[-1].version_id)


class TestClosureMalformedBatonContainmentArchaeology(_ClosureCase):
    def _ingest_baton(self, agent_id: str, text: str, step: int) -> int:
        self.fabric.create_agent(self.workspace_id, agent_id)
        result = self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id=agent_id,
            text=text,
            step=step,
            scope="private",
            provenance=ProvenanceV1.for_baton_ingest().to_dict(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": {
                "owner": "user",
                "expires_when": "explicit completion",
                "resolution_condition": "user confirmation",
            }},
        )
        return int(result["eid"])

    def _malform_baton_lifecycle(self, agent_id: str, eid: int) -> None:
        graph = self.fabric.private_graphs[
            self.fabric._agent_key(self.workspace_id, agent_id)
        ]
        graph.update_payload(eid, {"baton_lifecycle": [1]})

    def _ratified_closure(self, scope: list[int]) -> str:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs(scope=scope))
        self.assertTrue(proposed["ok"])
        self.assertTrue(
            self.fabric.ratify_closure(
                self.workspace_id, proposed["closure_id"], ratifier="operator"
            )["ok"]
        )
        return proposed["closure_id"]

    def test_malformed_lifecycle_only_does_not_crash_closure(self) -> None:
        eid = self._ingest_baton("agent_a", "MALFORMED_ONLY", 1)
        self._malform_baton_lifecycle("agent_a", eid)
        closure_id = self._ratified_closure([eid])

        restarted = self.restarted()
        result = restarted.commit_closure(
            self.workspace_id, closure_id, ratifier="operator"
        )
        self.assertTrue(result["ok"])

    def test_valid_active_baton_after_malformed_row_is_discovered(self) -> None:
        malformed_eid = self._ingest_baton("agent_a", "MALFORMED_FIRST", 1)
        self._malform_baton_lifecycle("agent_a", malformed_eid)
        active_eid = self._ingest_baton("agent_a", "ACTIVE_AFTER_MALFORMED", 2)
        closure_id = self._ratified_closure([active_eid])

        restarted = self.restarted()
        result = restarted.commit_closure(
            self.workspace_id, closure_id, ratifier="operator"
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["result_code"], "open_items_mismatch")
        self.assertEqual(
            result["unresolved"]["unresolved_batons"],
            [{"eid": active_eid, "summary": "ACTIVE_AFTER_MALFORMED", "agent_id": "agent_a"}],
        )

    def test_valid_active_baton_before_malformed_row_is_discovered(self) -> None:
        active_eid = self._ingest_baton("agent_a", "ACTIVE_BEFORE_MALFORMED", 1)
        malformed_eid = self._ingest_baton("agent_a", "MALFORMED_AFTER", 2)
        self._malform_baton_lifecycle("agent_a", malformed_eid)
        closure_id = self._ratified_closure([active_eid])

        restarted = self.restarted()
        result = restarted.commit_closure(
            self.workspace_id, closure_id, ratifier="operator"
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["result_code"], "open_items_mismatch")
        self.assertEqual(
            result["unresolved"]["unresolved_batons"],
            [{"eid": active_eid, "summary": "ACTIVE_BEFORE_MALFORMED", "agent_id": "agent_a"}],
        )

    def test_malformed_agent_does_not_hide_valid_baton_in_another_agent(self) -> None:
        malformed_eid = self._ingest_baton("agent_a", "MALFORMED_AGENT_A", 1)
        self._malform_baton_lifecycle("agent_a", malformed_eid)
        active_eid = self._ingest_baton("agent_b", "ACTIVE_AGENT_B", 2)
        self.assertEqual(malformed_eid, active_eid)
        closure_id = self._ratified_closure([active_eid])

        restarted = self.restarted()
        result = restarted.commit_closure(
            self.workspace_id, closure_id, ratifier="operator"
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["result_code"], "open_items_mismatch")
        self.assertEqual(
            result["unresolved"]["unresolved_batons"],
            [{"eid": active_eid, "summary": "ACTIVE_AGENT_B", "agent_id": "agent_b"}],
        )


class TestClosureReplayToleranceArchaeology(_ClosureCase):
    def test_legacy_minimal_store_row_replays_while_malformed_rows_are_skipped(self) -> None:
        store = ClosureStore(self.tempdir.name, self.workspace_id)
        store._append_jsonl(
            store.closures_path,
            {
                "closure_id": "legacy_closure",
                "version_id": "legacy_version",
                "workspace_id": self.workspace_id,
                "arc_name": "Legacy closure",
                "arc_kind": "legacy",
            },
        )
        with open(store._guard(store.closures_path), "a", encoding="utf-8") as handle:
            handle.write("{not valid json}\n")

        reloaded = ClosureStore(self.tempdir.name, self.workspace_id)
        legacy = reloaded.get_latest_version("legacy_closure")
        self.assertIsNotNone(legacy)
        self.assertEqual(legacy.scope, [])
        self.assertEqual(legacy.deferred_or_open_items, [])
        self.assertEqual(legacy.what_it_was, "")

    def test_orphan_ledger_event_and_malformed_event_row_replay_literally(self) -> None:
        ledger = ClosureLedger(self.tempdir.name, self.workspace_id)
        with open(ledger._guard(ledger.path), "a", encoding="utf-8") as handle:
            handle.write("{not valid json}\n")
        event = ledger.build_committed_event(
            "orphan_closure",
            "orphan_version",
            ratifier="operator",
            provenance={"source_type": "closure"},
        )
        ledger.add_event(event)

        reloaded = ClosureLedger(self.tempdir.name, self.workspace_id)
        self.assertEqual(reloaded.get_latest_event_kind("orphan_closure"), "committed")
        self.assertIsNone(self.fabric.get_closure(self.workspace_id, "orphan_closure"))


if __name__ == "__main__":
    unittest.main()
