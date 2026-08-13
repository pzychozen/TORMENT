"""Read-only/test-only characterization of Block A Baton Memory."""

from __future__ import annotations

import gc
import os
import sys
import tempfile
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.baton_ledger import BatonLedger
from torment_service.fabric import TormentFabric
from torment_service.provenance_v1 import ProvenanceV1


def _dispose_fabric(fabric: TormentFabric) -> None:
    fabric.close()
    for workspace in getattr(fabric, "workspaces", {}).values():
        for graph in getattr(workspace, "shared_graphs", {}).values():
            try:
                graph.close()
            except Exception:
                pass
    for name in (
        "private_graphs", "workspaces", "agent_states", "_kernel_contexts",
        "_sqlite_indexes",
    ):
        value = getattr(fabric, name, None)
        if isinstance(value, dict):
            value.clear()
    gc.collect()


class _BatonCase(unittest.TestCase):
    workspace_id = "baton_archaeology_ws"
    agent_id = "atlas"

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.old_embed = os.environ.get("TORMENT_EMBED_PROVIDER")
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.addCleanup(self._restore_embed)
        self.fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, self.fabric)

    def _restore_embed(self) -> None:
        if self.old_embed is None:
            os.environ.pop("TORMENT_EMBED_PROVIDER", None)
        else:
            os.environ["TORMENT_EMBED_PROVIDER"] = self.old_embed

    def lifecycle(
        self,
        *,
        owner: str = "user",
        status: str | None = None,
        expires_when: str = "explicit resolution",
        resolution_condition: str = "operator acknowledgment",
    ) -> dict:
        lifecycle = {
            "owner": owner,
            "expires_when": expires_when,
            "resolution_condition": resolution_condition,
        }
        if status is not None:
            lifecycle["status"] = status
        return lifecycle

    def ingest_baton(
        self,
        text: str = "Verify the migration before release.",
        *,
        workspace_id: str | None = None,
        agent_id: str | None = None,
        lifecycle: dict | None = None,
        provenance: dict | None = None,
        step: int = 1,
        scope: str = "private",
    ) -> dict:
        return self.fabric.ingest(
            workspace_id=workspace_id or self.workspace_id,
            agent_id=agent_id or self.agent_id,
            text=text,
            step=step,
            scope=scope,
            provenance=(provenance or ProvenanceV1.for_baton_ingest(step=step).to_dict()),
            memory_class="baton",
            extra_payload={"baton_lifecycle": lifecycle or self.lifecycle()},
        )

    def graph(self, workspace_id: str | None = None, agent_id: str | None = None):
        return self.fabric.private_graphs[
            self.fabric._agent_key(workspace_id or self.workspace_id, agent_id or self.agent_id)
        ]

    def restarted(self) -> TormentFabric:
        fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, fabric)
        return fabric


class TestBatonWriteAndPersistenceArchaeology(_BatonCase):
    def test_valid_baton_persists_lifecycle_provenance_and_default_status(self) -> None:
        result = self.ingest_baton()
        self.assertTrue(result["stored"])
        eid = int(result["eid"])
        payload = self.graph().entities[eid].payload
        self.assertEqual(payload["memory_class"], "baton")
        self.assertEqual(payload["baton_lifecycle"]["status"], "active")
        self.assertEqual(payload["provenance"]["source_type"], "baton_intent")

        restarted = self.restarted()
        restarted.create_agent(self.workspace_id, self.agent_id)
        payload_after = restarted.private_graphs[
            restarted._agent_key(self.workspace_id, self.agent_id)
        ].entities[eid].payload
        self.assertEqual(payload_after["baton_lifecycle"], payload["baton_lifecycle"])
        self.assertEqual(payload_after["provenance"], payload["provenance"])

    def test_all_declared_owners_are_accepted(self) -> None:
        for owner in ("user", "next_ai", "system"):
            with self.subTest(owner=owner):
                result = self.ingest_baton(
                    text=f"owned by {owner}", lifecycle=self.lifecycle(owner=owner)
                )
                self.assertTrue(result["stored"])

    def test_shared_scope_baton_is_rejected_by_the_private_only_contract(self) -> None:
        with self.assertRaisesRegex(ValueError, "scope='private'"):
            self.ingest_baton("shared baton", scope="shared")

    def test_invalid_lifecycle_rejects_node_but_initializes_agent_before_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required field 'owner'"):
            self.ingest_baton(lifecycle={
                "expires_when": "later",
                "resolution_condition": "acknowledged",
            })

        agent_key = self.fabric._agent_key(self.workspace_id, self.agent_id)
        self.assertIn(agent_key, self.fabric.private_graphs)
        self.assertIsNotNone(
            self.fabric.ident_store.load(self.workspace_id, self.agent_id),
            "validation happens after create_agent persists identity state",
        )
        self.assertEqual(self.graph().entities, {})
        self.assertEqual(
            self.fabric.list_active_batons(self.workspace_id, self.agent_id)["result_code"],
            "no_active",
        )

    def test_non_dict_missing_and_invalid_owner_are_rejected_without_nodes(self) -> None:
        cases = [
            ({"baton_lifecycle": []}, "requires extra_payload"),
            ({"baton_lifecycle": {"owner": "collective", "expires_when": "x", "resolution_condition": "y"}}, "owner must be one of"),
            ({"baton_lifecycle": {"owner": "user", "expires_when": "", "resolution_condition": "y"}}, "missing required field 'expires_when'"),
        ]
        for index, (extra, error) in enumerate(cases):
            workspace_id = f"invalid_{index}"
            with self.subTest(workspace_id=workspace_id):
                with self.assertRaisesRegex(ValueError, error):
                    self.fabric.ingest(
                        workspace_id=workspace_id,
                        agent_id=self.agent_id,
                        text="invalid baton",
                        scope="private",
                        memory_class="baton",
                        extra_payload=extra,
                    )
                graph = self.graph(workspace_id)
                self.assertEqual(graph.entities, {})

    def test_baton_source_type_is_not_required_by_baton_boundary(self) -> None:
        result = self.ingest_baton(
            provenance=ProvenanceV1.for_user_ingest().to_dict(),
        )
        self.assertTrue(result["stored"])
        payload = self.graph().entities[int(result["eid"])].payload
        self.assertEqual(payload["provenance"]["source_type"], "user_input")


class TestBatonListAndResolveArchaeology(_BatonCase):
    def test_list_filters_active_owner_status_and_sorts_oldest_first(self) -> None:
        active_user_old = self.ingest_baton("old user", step=1)
        active_next = self.ingest_baton(
            "next ai", lifecycle=self.lifecycle(owner="next_ai"), step=2
        )
        self.ingest_baton("already expired", lifecycle=self.lifecycle(status="expired"), step=3)
        unknown = self.ingest_baton("unknown state", lifecycle=self.lifecycle(status="snoozed"), step=4)
        all_active = self.fabric.list_active_batons(self.workspace_id, self.agent_id)
        self.assertEqual(all_active["result_code"], "listed")
        self.assertEqual(
            [row["summary"] for row in all_active["batons"]], ["old user", "next ai"]
        )
        next_only = self.fabric.list_active_batons(
            self.workspace_id, self.agent_id, owner="next_ai"
        )
        self.assertEqual([row["eid"] for row in next_only["batons"]], [int(active_next["eid"])])
        self.assertTrue(
            self.fabric.resolve_baton(
                self.workspace_id, self.agent_id, int(active_user_old["eid"]), "done"
            )["ok"]
        )
        self.assertEqual(
            self.fabric.list_active_batons(self.workspace_id, self.agent_id, owner="user")["result_code"],
            "no_active",
        )
        self.assertEqual(
            self.graph().entities[int(unknown["eid"])].payload["baton_lifecycle"]["status"],
            "snoozed",
        )

    def test_expiry_and_resolution_condition_are_descriptive_not_enforced(self) -> None:
        result = self.ingest_baton(
            "past due", lifecycle=self.lifecycle(
                expires_when="before this ingest", resolution_condition="owner only"
            )
        )
        eid = int(result["eid"])
        self.assertEqual(
            self.fabric.list_active_batons(self.workspace_id, self.agent_id)["batons"][0]["eid"],
            eid,
        )
        resolved = self.fabric.resolve_baton(
            self.workspace_id, self.agent_id, eid, "any outcome", resolver="other_agent"
        )
        self.assertEqual(resolved["result_code"], "resolved")
        lifecycle = self.graph().entities[eid].payload["baton_lifecycle"]
        self.assertEqual(lifecycle["consumed_by"], "other_agent")
        self.assertEqual(lifecycle["status"], "consumed")

    def test_resolution_is_payload_authoritative_persistent_and_audited(self) -> None:
        result = self.ingest_baton()
        eid = int(result["eid"])
        self.assertEqual(
            self.fabric.resolve_baton(self.workspace_id, self.agent_id, eid, "acknowledged")["result_code"],
            "resolved",
        )
        self.assertEqual(
            self.fabric.resolve_baton(self.workspace_id, self.agent_id, eid, "again")["result_code"],
            "already_consumed",
        )
        ledger = BatonLedger(self.tempdir.name, self.workspace_id, self.agent_id)
        events = ledger.list_events(eid=eid)
        self.assertEqual([event.kind for event in events], ["consumed"])

        restarted = self.restarted()
        restarted.create_agent(self.workspace_id, self.agent_id)
        self.assertEqual(
            restarted.list_active_batons(self.workspace_id, self.agent_id)["result_code"],
            "no_active",
        )
        payload = restarted.private_graphs[
            restarted._agent_key(self.workspace_id, self.agent_id)
        ].entities[eid].payload
        self.assertEqual(payload["baton_lifecycle"]["status"], "consumed")

    def test_active_list_and_resolve_recover_persisted_graph_without_hydration(self) -> None:
        result = self.ingest_baton()
        eid = int(result["eid"])
        restarted = self.restarted()
        self.assertEqual(restarted.private_graphs, {})
        listed = restarted.list_active_batons(self.workspace_id, self.agent_id)
        self.assertEqual(listed["result_code"], "listed")
        self.assertEqual([row["eid"] for row in listed["batons"]], [eid])
        self.assertEqual(
            restarted.private_graphs, {}, "cold list must not hydrate the runtime cache"
        )
        self.assertEqual(
            restarted.resolve_baton(self.workspace_id, self.agent_id, eid, "done")["result_code"],
            "resolved",
        )
        self.assertEqual(
            restarted.private_graphs, {}, "cold resolve must not retain a graph cache entry"
        )

        second_restart = self.restarted()
        self.assertEqual(
            second_restart.list_active_batons(self.workspace_id, self.agent_id)["result_code"],
            "no_active",
        )
        self.assertEqual(second_restart.private_graphs, {})
        second_restart.create_agent(self.workspace_id, self.agent_id)
        self.assertEqual(
            second_restart.private_graphs[
                second_restart._agent_key(self.workspace_id, self.agent_id)
            ].entities[eid].payload["baton_lifecycle"]["status"],
            "consumed",
        )

    def test_workspace_and_agent_boundaries_hold_for_active_listing(self) -> None:
        own = self.ingest_baton("own")
        other_agent = self.ingest_baton("other agent", agent_id="beacon")
        other_workspace = self.ingest_baton("other workspace", workspace_id="other_ws")

        own_rows = self.fabric.list_active_batons(self.workspace_id, self.agent_id)["batons"]
        self.assertEqual([row["eid"] for row in own_rows], [int(own["eid"])])
        beacon_rows = self.fabric.list_active_batons(self.workspace_id, "beacon")["batons"]
        self.assertEqual([row["eid"] for row in beacon_rows], [int(other_agent["eid"])])
        other_rows = self.fabric.list_active_batons("other_ws", self.agent_id)["batons"]
        self.assertEqual([row["eid"] for row in other_rows], [int(other_workspace["eid"])])

    def test_malformed_lifecycle_is_skipped_and_refused_without_mutation(self) -> None:
        valid = self.ingest_baton("valid")
        malformed = self.ingest_baton("malformed")
        self.graph().update_payload(int(malformed["eid"]), {"baton_lifecycle": [1]})

        listed = self.fabric.list_active_batons(self.workspace_id, self.agent_id)
        self.assertEqual([row["eid"] for row in listed["batons"]], [int(valid["eid"])])
        refused = self.fabric.resolve_baton(
            self.workspace_id, self.agent_id, int(malformed["eid"]), "attempt"
        )
        self.assertEqual(refused["result_code"], "invalid_lifecycle")
        self.assertEqual(self.graph().entities[int(malformed["eid"])].payload["baton_lifecycle"], [1])
        self.assertEqual(self.graph().entities[int(valid["eid"])].payload["baton_lifecycle"]["status"], "active")

    def test_truthy_malformed_lifecycle_variants_do_not_hide_later_valid_baton(self) -> None:
        for index, malformed_lifecycle in enumerate(([1], "bad", 1)):
            agent_id = f"malformed_{index}"
            with self.subTest(malformed_lifecycle=repr(malformed_lifecycle)):
                malformed = self.ingest_baton(
                    "malformed first", agent_id=agent_id
                )
                valid = self.ingest_baton("valid after malformed", agent_id=agent_id)
                graph = self.graph(agent_id=agent_id)
                graph.update_payload(
                    int(malformed["eid"]), {"baton_lifecycle": malformed_lifecycle}
                )
                listed = self.fabric.list_active_batons(self.workspace_id, agent_id)
                self.assertEqual([row["eid"] for row in listed["batons"]], [int(valid["eid"])])
                self.assertEqual(
                    self.fabric.resolve_baton(
                        self.workspace_id, agent_id, int(malformed["eid"]), "attempt"
                    )["result_code"],
                    "invalid_lifecycle",
                )
                self.assertEqual(
                    graph.entities[int(malformed["eid"])].payload["baton_lifecycle"],
                    malformed_lifecycle,
                )
                self.assertEqual(
                    graph.entities[int(valid["eid"])].payload["baton_lifecycle"]["status"],
                    "active",
                )

    def test_null_lifecycle_is_skipped_by_list_and_refused_without_mutation(self) -> None:
        malformed = self.ingest_baton("null lifecycle")
        valid = self.ingest_baton("valid neighbor")
        self.graph().update_payload(int(malformed["eid"]), {"baton_lifecycle": None})

        listed = self.fabric.list_active_batons(self.workspace_id, self.agent_id)
        self.assertEqual([row["eid"] for row in listed["batons"]], [int(valid["eid"])])
        self.assertEqual(
            self.fabric.resolve_baton(
                self.workspace_id, self.agent_id, int(malformed["eid"]), "attempt"
            )["result_code"],
            "invalid_lifecycle",
        )
        self.assertEqual(
            self.graph().entities[int(malformed["eid"])].payload["baton_lifecycle"],
            None,
        )

    def test_malformed_agent_does_not_affect_another_agents_explicit_list(self) -> None:
        malformed = self.ingest_baton("malformed", agent_id="agent_a")
        valid = self.ingest_baton("valid", agent_id="agent_b")
        self.graph(agent_id="agent_a").update_payload(
            int(malformed["eid"]), {"baton_lifecycle": [1]}
        )

        self.assertEqual(
            self.fabric.list_active_batons(self.workspace_id, "agent_a")["result_code"],
            "no_active",
        )
        listed_b = self.fabric.list_active_batons(self.workspace_id, "agent_b")
        self.assertEqual([row["eid"] for row in listed_b["batons"]], [int(valid["eid"])])

    def test_resolve_scope_and_non_baton_envelopes_are_agent_workspace_scoped(self) -> None:
        baton = self.ingest_baton("target")
        core = self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id=self.agent_id,
            text="ordinary memory",
            scope="private",
            step=2,
        )
        eid = int(baton["eid"])
        self.assertEqual(
            self.fabric.resolve_baton(self.workspace_id, "other_agent", eid, "attempt")["result_code"],
            "not_found",
        )
        self.assertEqual(
            self.fabric.resolve_baton("other_workspace", self.agent_id, eid, "attempt")["result_code"],
            "not_found",
        )
        self.assertEqual(
            self.fabric.resolve_baton(self.workspace_id, self.agent_id, 999_999, "attempt")["result_code"],
            "not_found",
        )
        self.assertEqual(
            self.fabric.resolve_baton(
                self.workspace_id, self.agent_id, int(core["eid"]), "attempt"
            )["result_code"],
            "not_a_baton",
        )
        self.assertEqual(
            self.graph().entities[eid].payload["baton_lifecycle"]["status"], "active"
        )

    def test_resolve_preserves_content_class_and_evidence(self) -> None:
        baton = self.ingest_baton("preserve this wording")
        eid = int(baton["eid"])
        before = dict(self.graph().entities[eid].payload)
        resolved = self.fabric.resolve_baton(
            self.workspace_id, self.agent_id, eid, "acknowledged"
        )
        self.assertEqual(resolved["result_code"], "resolved")
        after = self.graph().entities[eid].payload
        self.assertIn(eid, self.graph().entities)
        self.assertEqual(after["summary"], before["summary"])
        self.assertEqual(after["memory_class"], "baton")
        self.assertEqual(after["provenance"], before["provenance"])


if __name__ == "__main__":
    unittest.main()
