"""Production-facing regressions for Closure trusted-current reconciliation."""

from __future__ import annotations

from dataclasses import replace
import gc
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.closure_ledger import ClosureLedger
from torment_service.closure_memory import ClosureEntry
from torment_service.fabric import TormentFabric


def _dispose_fabric(fabric: TormentFabric) -> None:
    fabric.close()
    for name in (
        "private_graphs", "workspaces", "agent_states", "_kernel_contexts",
        "_sqlite_indexes", "closure_stores",
    ):
        value = getattr(fabric, name, None)
        if isinstance(value, dict):
            value.clear()
    gc.collect()


class _ClosureCurrentCase(unittest.TestCase):
    workspace_id = "reconciled_current_ws"

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.env = patch.dict(os.environ, {"TORMENT_EMBED_PROVIDER": "hash"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, self.fabric)
        self.fabric.get_workspace(self.workspace_id)
        self.fabric.create_agent(self.workspace_id, "seed")
        result = self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id="seed",
            text="Closure reconciliation scope seed.",
            step=1,
        )
        self.scope_eid = int(result["eid"])

    def proposal_kwargs(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "arc_name": "Reconciled current regression",
            "arc_kind": "test",
            "scope": [self.scope_eid],
            "what_it_was": "A closure reconciliation regression.",
            "what_worked": "Append-only evidence remains visible.",
            "what_surprised": "Nothing outside the test boundary.",
            "what_to_carry_forward": "Keep trusted current separate from raw.",
            "deferred_or_open_items": [],
        }

    def propose_ratify_commit(self) -> dict:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        self.assertTrue(proposed["ok"])
        self.assertTrue(
            self.fabric.ratify_closure(
                self.workspace_id, proposed["closure_id"], "operator"
            )["ok"]
        )
        self.assertTrue(
            self.fabric.commit_closure(
                self.workspace_id, proposed["closure_id"], "operator"
            )["ok"]
        )
        return proposed

    def restarted(self) -> TormentFabric:
        fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, fabric)
        return fabric

    def current(self, closure_id: str, fabric: TormentFabric | None = None) -> dict:
        value = (fabric or self.fabric).get_closure_current(
            self.workspace_id, closure_id
        )
        self.assertIsNotNone(value)
        return value

    def append_raw_child(
        self,
        closure_id: str,
        *,
        source_version_id: str,
        parent_version_id: str,
        marker: str,
    ) -> ClosureEntry:
        store = self.fabric._get_closure_store(self.workspace_id)
        parent = store.get_version(closure_id, source_version_id)
        self.assertIsNotNone(parent)
        child = replace(
            parent,
            version_id=store.new_version_id(),
            parent_version_id=parent_version_id,
            version_history=list(parent.version_history) + [{
                "version_id": marker,
                "parent_version_id": parent_version_id,
                "ratifier": "operator",
                "ts": 1,
            }],
        )
        store.add_version(child)
        return child


class TestClosureCurrentHealthyLifecycle(_ClosureCurrentCase):
    def test_healthy_v1_v2_v3_chain_remains_unchanged_and_restarts(self) -> None:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        closure_id = proposed["closure_id"]
        self.assertEqual(
            (self.current(closure_id)["current_state"], self.current(closure_id)["current_version_id"]),
            ("proposed", proposed["version_id"]),
        )

        self.assertTrue(
            self.fabric.ratify_closure(self.workspace_id, closure_id, "operator")["ok"]
        )
        self.assertEqual(self.current(closure_id)["current_state"], "ratified")
        self.assertTrue(
            self.fabric.commit_closure(self.workspace_id, closure_id, "operator")["ok"]
        )
        self.assertEqual(self.current(closure_id)["current_state"], "committed")

        v2 = self.fabric.revise_closure(
            self.workspace_id, closure_id, {"what_to_carry_forward": "V2"}, "operator"
        )
        self.assertTrue(v2["ok"])
        v3 = self.fabric.revise_closure(
            self.workspace_id, closure_id, {"what_to_carry_forward": "V3"}, "operator"
        )
        self.assertTrue(v3["ok"])
        current = self.current(closure_id)
        self.assertEqual(
            (current["current_state"], current["current_version_id"]),
            ("revised", v3["version_id"]),
        )
        self.assertTrue(current["healthy"])

        restarted = self.restarted()
        after = self.current(closure_id, restarted)
        self.assertEqual(
            (after["current_state"], after["current_version_id"], after["healthy"]),
            ("revised", v3["version_id"], True),
        )


class TestClosureCurrentDivergence(_ClosureCurrentCase):
    def test_store_only_v1_stays_raw_and_cannot_be_ratified_or_committed(self) -> None:
        with patch.object(ClosureLedger, "add_event", side_effect=OSError("ledger unavailable")):
            with self.assertRaisesRegex(OSError, "ledger unavailable"):
                self.fabric.propose_closure(**self.proposal_kwargs())

        closure_id = self.fabric.list_closures(self.workspace_id)[0]
        raw = self.fabric.get_closure(self.workspace_id, closure_id)
        current = self.current(closure_id)
        self.assertIsNotNone(raw)
        self.assertIsNone(current["closure"])
        self.assertEqual((current["current_state"], current["current_version_id"]), (None, None))
        self.assertTrue(current["reconciled_with_orphans"])
        self.assertIn("store_only_version", {d["kind"] for d in current["diagnostics"]})

        restarted = self.restarted()
        after = self.current(closure_id, restarted)
        self.assertEqual(
            (after["current_state"], after["current_version_id"], after["diagnostics"]),
            (current["current_state"], current["current_version_id"], current["diagnostics"]),
        )
        self.assertEqual(
            restarted.ratify_closure(self.workspace_id, closure_id, "operator")["result_code"],
            "not_found",
        )
        self.assertEqual(
            restarted.commit_closure(self.workspace_id, closure_id, "operator")["result_code"],
            "not_found",
        )

    def test_orphan_v2_remains_raw_while_next_revision_parents_trusted_v1(self) -> None:
        proposed = self.propose_ratify_commit()
        closure_id = proposed["closure_id"]
        with patch.object(ClosureLedger, "add_event", side_effect=OSError("ledger unavailable")):
            with self.assertRaisesRegex(OSError, "ledger unavailable"):
                self.fabric.revise_closure(
                    self.workspace_id,
                    closure_id,
                    {"what_to_carry_forward": "orphan V2"},
                    "operator",
                )

        raw_v2 = self.fabric.get_closure(self.workspace_id, closure_id)
        current = self.current(closure_id)
        self.assertNotEqual(raw_v2["version_id"], proposed["version_id"])
        self.assertEqual(
            (current["current_state"], current["current_version_id"]),
            ("committed", proposed["version_id"]),
        )
        self.assertIn(raw_v2["version_id"], current["orphan_version_ids"])

        restarted = self.restarted()
        after = self.current(closure_id, restarted)
        self.assertEqual(
            (after["current_state"], after["current_version_id"]),
            ("committed", proposed["version_id"]),
        )
        self.assertEqual(
            restarted.ratify_closure(self.workspace_id, closure_id, "operator")["result_code"],
            "already_committed",
        )
        self.assertEqual(
            restarted.commit_closure(self.workspace_id, closure_id, "operator")["result_code"],
            "already_committed",
        )
        v3 = restarted.revise_closure(
            self.workspace_id,
            closure_id,
            {"what_to_carry_forward": "trusted V3"},
            "operator",
        )
        self.assertTrue(v3["ok"])
        self.assertEqual(v3["parent_version_id"], proposed["version_id"])
        self.assertNotEqual(v3["parent_version_id"], raw_v2["version_id"])
        self.assertEqual(
            restarted.get_closure(self.workspace_id, closure_id, raw_v2["version_id"])["version_id"],
            raw_v2["version_id"],
        )
        self.assertEqual(
            self.current(closure_id, restarted)["current_version_id"], v3["version_id"]
        )

    def test_invalid_commit_to_missing_v999_cannot_displace_trusted_commit(self) -> None:
        proposed = self.propose_ratify_commit()
        closure_id = proposed["closure_id"]
        ledger = self.fabric._get_closure_ledger(self.workspace_id)
        ledger.add_event(ledger.build_committed_event(
            closure_id,
            "V999",
            ratifier="operator",
            provenance={"source_type": "closure"},
        ))

        current = self.current(closure_id)
        self.assertEqual(
            (current["current_state"], current["current_version_id"]),
            ("committed", proposed["version_id"]),
        )
        self.assertIn("missing_version_reference", {d["kind"] for d in current["diagnostics"]})
        self.assertEqual(
            self.fabric.commit_closure(self.workspace_id, closure_id, "operator")["result_code"],
            "already_committed",
        )
        restarted = self.restarted()
        self.assertEqual(
            self.current(closure_id, restarted)["current_version_id"], proposed["version_id"]
        )

    def test_event_only_proposal_and_revision_remain_diagnostic_without_current_entry(self) -> None:
        ledger = self.fabric._get_closure_ledger(self.workspace_id)
        ledger.add_event(ledger.build_proposed_event(
            "event_only_proposal", "missing-v1", provenance={"source_type": "closure"}
        ))
        ledger.add_event(ledger.build_revised_event(
            "event_only_revision",
            "missing-v2",
            ratifier="operator",
            provenance={"source_type": "closure"},
        ))

        for closure_id in ("event_only_proposal", "event_only_revision"):
            with self.subTest(closure_id=closure_id):
                current = self.current(closure_id)
                self.assertIsNone(self.fabric.get_closure(self.workspace_id, closure_id))
                self.assertIsNone(current["closure"])
                self.assertEqual((current["current_state"], current["current_version_id"]), (None, None))
                self.assertIn(
                    "missing_version_reference", {d["kind"] for d in current["diagnostics"]}
                )
                self.assertEqual(
                    self.current(closure_id, self.restarted())["diagnostics"], current["diagnostics"]
                )

    def test_wrong_parent_revision_is_diagnostic_and_does_not_advance_current(self) -> None:
        proposed = self.propose_ratify_commit()
        closure_id = proposed["closure_id"]
        wrong_parent = self.append_raw_child(
            closure_id,
            source_version_id=proposed["version_id"],
            parent_version_id="not-the-trusted-parent",
            marker="wrong-parent",
        )
        ledger = self.fabric._get_closure_ledger(self.workspace_id)
        ledger.add_event(ledger.build_revised_event(
            closure_id,
            wrong_parent.version_id,
            ratifier="operator",
            provenance={"source_type": "closure"},
        ))

        current = self.current(closure_id)
        self.assertEqual(current["current_version_id"], proposed["version_id"])
        self.assertEqual(
            self.fabric.get_closure(self.workspace_id, closure_id)["version_id"], wrong_parent.version_id
        )
        self.assertIn("revision_parent_not_current", {d["kind"] for d in current["diagnostics"]})
        self.assertEqual(
            self.current(closure_id, self.restarted())["current_version_id"], proposed["version_id"]
        )

    def test_foreign_version_and_workspace_events_are_diagnostic_only(self) -> None:
        proposed = self.propose_ratify_commit()
        other = self.propose_ratify_commit()
        closure_id = proposed["closure_id"]
        ledger = self.fabric._get_closure_ledger(self.workspace_id)
        ledger.add_event(ledger.build_committed_event(
            closure_id,
            other["version_id"],
            ratifier="operator",
            provenance={"source_type": "closure"},
        ))
        foreign_workspace_event = replace(
            ledger.build_committed_event(
                closure_id,
                proposed["version_id"],
                ratifier="operator",
                provenance={"source_type": "closure"},
            ),
            workspace_id="foreign_workspace",
        )
        ledger.add_event(foreign_workspace_event)

        current = self.current(closure_id)
        self.assertEqual(current["current_version_id"], proposed["version_id"])
        kinds = {d["kind"] for d in current["diagnostics"]}
        self.assertIn("foreign_version_reference", kinds)
        self.assertIn("foreign_workspace_event", kinds)
        self.assertEqual(
            self.current(closure_id, self.restarted())["current_version_id"], proposed["version_id"]
        )

    def test_out_of_order_and_duplicate_events_remain_diagnostic(self) -> None:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        closure_id = proposed["closure_id"]
        self.assertTrue(
            self.fabric.ratify_closure(self.workspace_id, closure_id, "operator")["ok"]
        )
        v2 = self.append_raw_child(
            closure_id,
            source_version_id=proposed["version_id"],
            parent_version_id=proposed["version_id"],
            marker="out-of-order-v2",
        )
        ledger = self.fabric._get_closure_ledger(self.workspace_id)
        ledger.add_event(ledger.build_revised_event(
            closure_id, v2.version_id, ratifier="operator", provenance={"source_type": "closure"}
        ))
        self.assertTrue(
            self.fabric.commit_closure(self.workspace_id, closure_id, "operator")["ok"]
        )
        ledger.add_event(ledger.build_proposed_event(
            closure_id, proposed["version_id"], provenance={"source_type": "closure"}
        ))
        ledger.add_event(ledger.build_committed_event(
            closure_id,
            proposed["version_id"],
            ratifier="operator",
            provenance={"source_type": "closure"},
        ))

        current = self.current(closure_id)
        self.assertEqual(
            (current["current_state"], current["current_version_id"]),
            ("committed", proposed["version_id"]),
        )
        kinds = {d["kind"] for d in current["diagnostics"]}
        self.assertIn("missing_valid_commit", kinds)
        self.assertIn("invalid_lifecycle_transition", kinds)
        self.assertEqual(
            self.current(closure_id, self.restarted())["current_version_id"], proposed["version_id"]
        )


if __name__ == "__main__":
    unittest.main()
