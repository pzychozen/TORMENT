"""Test-only archaeology for ClosureStore / ClosureLedger reconciliation.

This module deliberately contains a pure candidate projection rather than a
production helper.  It records the smallest fail-closed interpretation that
the existing append order and identifiers can support; it does not change the
raw store, ledger, or Fabric API.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import gc
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.closure_ledger import ClosureEvent, ClosureLedger
from torment_service.closure_memory import ClosureEntry, ClosureStore
from torment_service.fabric import TormentFabric


_EVENT_KINDS = {"proposed", "ratified", "committed", "revised"}


@dataclass(frozen=True)
class ReconciledClosure:
    """Result of the test-only, non-mutating candidate projection."""

    valid_version_ids: tuple[str, ...]
    orphan_version_ids: tuple[str, ...]
    valid_event_ids: tuple[str, ...]
    orphan_event_ids: tuple[str, ...]
    current_state: str | None
    current_version_id: str | None
    diagnostics: tuple[str, ...]


def reconcile_closure_history(
    entries: list[ClosureEntry],
    events: list[ClosureEvent],
    *,
    workspace_id: str,
    closure_id: str,
) -> ReconciledClosure:
    """Derive a fail-closed current view using only persisted fields/order.

    Store and ledger rows are preserved as forensic evidence.  A payload joins
    the trusted chain only through a valid birth event: ``proposed`` for V1 or
    ``revised`` for a child of the trusted current version.  A malformed,
    unpaired, duplicate, foreign, or out-of-order event is diagnostic only and
    cannot displace an earlier trusted state.

    Ratification is intentionally closure-bound: it must have no version_id
    and does not create a new payload pairing.
    """
    diagnostics: list[str] = []
    target_entries = [
        entry
        for entry in entries
        if entry.workspace_id == workspace_id and entry.closure_id == closure_id
    ]
    version_counts = Counter(entry.version_id for entry in target_entries)
    entries_by_id = {
        entry.version_id: entry
        for entry in target_entries
        if version_counts[entry.version_id] == 1
    }
    duplicate_versions = {
        version_id for version_id, count in version_counts.items() if count != 1
    }
    for version_id in sorted(duplicate_versions):
        diagnostics.append(f"duplicate_version:{version_id}")

    valid_versions: list[str] = []
    valid_events: list[str] = []
    orphan_events: list[str] = []
    paired_versions: set[str] = set()
    seen_event_ids: set[str] = set()
    current_state: str | None = None
    current_version_id: str | None = None
    has_ratification = False
    has_committed = False

    def reject(event: ClosureEvent, reason: str) -> None:
        orphan_events.append(event.event_id)
        diagnostics.append(f"event:{event.event_id}:{reason}")

    for event in events:
        if event.closure_id != closure_id:
            continue
        if event.workspace_id != workspace_id:
            reject(event, "foreign_workspace")
            continue
        if event.event_id in seen_event_ids:
            reject(event, "duplicate_event_id")
            continue
        seen_event_ids.add(event.event_id)
        if event.kind not in _EVENT_KINDS:
            reject(event, "unknown_kind")
            continue

        if event.kind == "proposed":
            entry = entries_by_id.get(event.version_id or "")
            if event.version_id in duplicate_versions:
                reject(event, "ambiguous_version")
            elif entry is None:
                reject(event, "missing_version")
            elif entry.parent_version_id is not None:
                reject(event, "proposal_has_parent")
            elif current_state is not None or event.version_id in paired_versions:
                reject(event, "invalid_proposal_transition")
            else:
                paired_versions.add(event.version_id)
                valid_versions.append(event.version_id)
                valid_events.append(event.event_id)
                current_state = "proposed"
                current_version_id = event.version_id
            continue

        if event.kind == "ratified":
            if event.version_id is not None:
                reject(event, "ratification_must_be_versionless")
            elif current_state not in {"proposed", "ratified", "revised"}:
                reject(event, "invalid_ratification_transition")
            else:
                valid_events.append(event.event_id)
                has_ratification = True
                current_state = "ratified"
            continue

        entry = entries_by_id.get(event.version_id or "")
        if event.version_id in duplicate_versions:
            reject(event, "ambiguous_version")
            continue
        if entry is None:
            reject(event, "missing_version")
            continue

        if event.kind == "committed":
            if not has_ratification:
                reject(event, "not_ratified")
            elif current_state not in {"ratified", "revised"}:
                reject(event, "invalid_commit_transition")
            elif event.version_id != current_version_id:
                reject(event, "commit_not_current_version")
            else:
                valid_events.append(event.event_id)
                current_state = "committed"
                has_committed = True
            continue

        # revised: it births a new payload version and must extend the
        # existing trusted chain.  Closure's historical ratification remains
        # closure-bound, so a revised current state can later be committed.
        if not has_committed:
            reject(event, "not_committed")
        elif current_state not in {"committed", "ratified", "revised"}:
            reject(event, "invalid_revision_transition")
        elif entry.parent_version_id != current_version_id:
            reject(event, "revision_parent_not_current")
        elif event.version_id in paired_versions:
            reject(event, "duplicate_revision_version")
        else:
            paired_versions.add(event.version_id)
            valid_versions.append(event.version_id)
            valid_events.append(event.event_id)
            current_state = "revised"
            current_version_id = event.version_id

    orphan_versions = [
        entry.version_id
        for entry in target_entries
        if entry.version_id not in paired_versions
    ]
    return ReconciledClosure(
        valid_version_ids=tuple(valid_versions),
        orphan_version_ids=tuple(orphan_versions),
        valid_event_ids=tuple(valid_events),
        orphan_event_ids=tuple(orphan_events),
        current_state=current_state,
        current_version_id=current_version_id,
        diagnostics=tuple(diagnostics),
    )


class _HistoryFactory:
    workspace_id = "reconciliation_ws"
    closure_id = "closure_a"

    def entry(
        self,
        version_id: str,
        parent_version_id: str | None = None,
        *,
        closure_id: str | None = None,
        workspace_id: str | None = None,
    ) -> ClosureEntry:
        return ClosureEntry(
            closure_id=closure_id or self.closure_id,
            version_id=version_id,
            workspace_id=workspace_id or self.workspace_id,
            arc_name="Reconciliation archaeology",
            arc_kind="test",
            scope=[1],
            what_it_was="test",
            what_worked="test",
            what_surprised="test",
            what_to_carry_forward="test",
            deferred_or_open_items=[],
            authorship_provenance={},
            version_history=[],
            created_ts=1,
            parent_version_id=parent_version_id,
            metadata={},
        )

    def event(
        self,
        event_id: str,
        kind: str,
        version_id: str | None = None,
        *,
        closure_id: str | None = None,
        workspace_id: str | None = None,
    ) -> ClosureEvent:
        return ClosureEvent(
            event_id=event_id,
            workspace_id=workspace_id or self.workspace_id,
            closure_id=closure_id or self.closure_id,
            version_id=version_id,
            kind=kind,
            ts=1,
            ratifier="operator" if kind != "proposed" else None,
            provenance={},
            notes=None,
        )

    def project(
        self, entries: list[ClosureEntry], events: list[ClosureEvent]
    ) -> ReconciledClosure:
        return reconcile_closure_history(
            entries,
            events,
            workspace_id=self.workspace_id,
            closure_id=self.closure_id,
        )

    def healthy(self) -> tuple[list[ClosureEntry], list[ClosureEvent]]:
        entries = [self.entry("v1"), self.entry("v2", "v1"), self.entry("v3", "v2")]
        events = [
            self.event("e1", "proposed", "v1"),
            self.event("e2", "ratified"),
            self.event("e3", "committed", "v1"),
            self.event("e4", "revised", "v2"),
            self.event("e5", "revised", "v3"),
        ]
        return entries, events


class TestPureReconciliationArchaeology(unittest.TestCase):
    def setUp(self) -> None:
        self.history = _HistoryFactory()

    def test_healthy_lifecycle_pairs_v1_then_revisions_and_keeps_ratification_versionless(self) -> None:
        entries, events = self.history.healthy()
        result = self.history.project(entries, events)

        self.assertEqual(result.valid_version_ids, ("v1", "v2", "v3"))
        self.assertEqual(result.orphan_version_ids, ())
        self.assertEqual(result.valid_event_ids, ("e1", "e2", "e3", "e4", "e5"))
        self.assertEqual(result.orphan_event_ids, ())
        self.assertEqual((result.current_state, result.current_version_id), ("revised", "v3"))

    def test_healthy_intermediate_states_are_deterministic(self) -> None:
        entries, events = self.history.healthy()
        expected = [
            ("proposed", "v1"),
            ("ratified", "v1"),
            ("committed", "v1"),
            ("revised", "v2"),
            ("revised", "v3"),
        ]
        for count, state in enumerate(expected, start=1):
            with self.subTest(event_count=count):
                result = self.history.project(entries[: 1 if count < 4 else count - 2], events[:count])
                self.assertEqual((result.current_state, result.current_version_id), state)

    def test_store_only_initial_is_not_a_trusted_closure(self) -> None:
        result = self.history.project([self.history.entry("v1")], [])

        self.assertEqual((result.current_state, result.current_version_id), (None, None))
        self.assertEqual(result.orphan_version_ids, ("v1",))

    def test_orphan_revision_does_not_displace_prior_committed_version(self) -> None:
        v1 = self.history.entry("v1")
        v2 = self.history.entry("v2", "v1")
        events = [
            self.history.event("e1", "proposed", "v1"),
            self.history.event("e2", "ratified"),
            self.history.event("e3", "committed", "v1"),
        ]
        result = self.history.project([v1, v2], events)

        self.assertEqual((result.current_state, result.current_version_id), ("committed", "v1"))
        self.assertEqual(result.orphan_version_ids, ("v2",))

    def test_later_revision_can_bypass_an_orphan_only_when_it_parents_the_trusted_version(self) -> None:
        v1 = self.history.entry("v1")
        orphan_v2 = self.history.entry("v2", "v1")
        v3 = self.history.entry("v3", "v1")
        events = [
            self.history.event("e1", "proposed", "v1"),
            self.history.event("e2", "ratified"),
            self.history.event("e3", "committed", "v1"),
            self.history.event("e4", "revised", "v3"),
        ]
        result = self.history.project([v1, orphan_v2, v3], events)

        self.assertEqual((result.current_state, result.current_version_id), ("revised", "v3"))
        self.assertEqual(result.valid_version_ids, ("v1", "v3"))
        self.assertEqual(result.orphan_version_ids, ("v2",))

    def test_revision_chained_from_orphan_is_not_trusted(self) -> None:
        v1 = self.history.entry("v1")
        orphan_v2 = self.history.entry("v2", "v1")
        v3 = self.history.entry("v3", "v2")
        events = [
            self.history.event("e1", "proposed", "v1"),
            self.history.event("e2", "ratified"),
            self.history.event("e3", "committed", "v1"),
            self.history.event("e4", "revised", "v3"),
        ]
        result = self.history.project([v1, orphan_v2, v3], events)

        self.assertEqual((result.current_state, result.current_version_id), ("committed", "v1"))
        self.assertEqual(result.orphan_version_ids, ("v2", "v3"))
        self.assertEqual(result.orphan_event_ids, ("e4",))
        self.assertIn("revision_parent_not_current", result.diagnostics[-1])

    def test_revision_before_a_valid_commit_is_out_of_order(self) -> None:
        v1 = self.history.entry("v1")
        v2 = self.history.entry("v2", "v1")
        events = [
            self.history.event("e1", "proposed", "v1"),
            self.history.event("e2", "ratified"),
            self.history.event("e3", "revised", "v2"),
        ]
        result = self.history.project([v1, v2], events)

        self.assertEqual((result.current_state, result.current_version_id), ("ratified", "v1"))
        self.assertEqual(result.orphan_version_ids, ("v2",))
        self.assertEqual(result.orphan_event_ids, ("e3",))
        self.assertIn("not_committed", result.diagnostics[-1])

    def test_event_only_and_unknown_version_events_do_not_claim_lifecycle(self) -> None:
        events = [
            self.history.event("e1", "proposed", "missing-v1"),
            self.history.event("e2", "committed", "missing-v2"),
            self.history.event("e3", "revised", "missing-v3"),
        ]
        result = self.history.project([], events)

        self.assertEqual((result.current_state, result.current_version_id), (None, None))
        self.assertEqual(result.orphan_event_ids, ("e1", "e2", "e3"))

    def test_invalid_latest_commit_falls_back_to_last_valid_committed_version(self) -> None:
        v1 = self.history.entry("v1")
        events = [
            self.history.event("e1", "proposed", "v1"),
            self.history.event("e2", "ratified"),
            self.history.event("e3", "committed", "v1"),
            self.history.event("e4", "committed", "v999"),
        ]
        result = self.history.project([v1], events)

        self.assertEqual((result.current_state, result.current_version_id), ("committed", "v1"))
        self.assertEqual(result.orphan_event_ids, ("e4",))

    def test_foreign_workspace_duplicate_and_out_of_order_events_are_diagnostic_only(self) -> None:
        v1 = self.history.entry("v1")
        events = [
            self.history.event("e0", "committed", "v1"),
            self.history.event("e1", "proposed", "v1"),
            self.history.event("e2", "proposed", "v1"),
            self.history.event("e3", "ratified", workspace_id="other_ws"),
            self.history.event("e4", "ratified"),
            self.history.event("e5", "committed", "v1"),
            self.history.event("e5", "committed", "v1"),
        ]
        result = self.history.project([v1], events)

        self.assertEqual((result.current_state, result.current_version_id), ("committed", "v1"))
        self.assertEqual(result.orphan_event_ids, ("e0", "e2", "e3", "e5"))

    def test_replay_of_the_same_rows_is_deterministic(self) -> None:
        entries, events = self.history.healthy()
        entries.append(self.history.entry("orphan", "v3"))
        events.append(self.history.event("bad", "committed", "missing"))
        before = self.history.project(entries, events)
        reloaded_entries = [ClosureEntry(**asdict(entry)) for entry in entries]
        reloaded_events = [ClosureEvent(**asdict(event)) for event in events]
        after = self.history.project(reloaded_entries, reloaded_events)

        self.assertEqual(after, before)


def _dispose_fabric(fabric: TormentFabric) -> None:
    fabric.close()
    for name in ("private_graphs", "workspaces", "agent_states", "_kernel_contexts", "_sqlite_indexes", "closure_stores"):
        value = getattr(fabric, name, None)
        if isinstance(value, dict):
            value.clear()
    gc.collect()


class TestExistingWriteBoundaryArchaeology(unittest.TestCase):
    """Mechanical current behavior; the pure model above changes none of it."""

    workspace_id = "reconciliation_fault_ws"

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
        seed = self.fabric.ingest(
            workspace_id=self.workspace_id,
            agent_id="seed",
            text="reconciliation fault scope seed",
            step=1,
        )
        self.scope_eid = int(seed["eid"])

    def proposal_kwargs(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "arc_name": "Store/ledger reconciliation",
            "arc_kind": "test",
            "scope": [self.scope_eid],
            "what_it_was": "test",
            "what_worked": "test",
            "what_surprised": "test",
            "what_to_carry_forward": "test",
            "deferred_or_open_items": [],
        }

    def restart(self) -> TormentFabric:
        fabric = TormentFabric(data_dir=self.tempdir.name)
        self.addCleanup(_dispose_fabric, fabric)
        return fabric

    def committed(self) -> dict:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        self.assertTrue(proposed["ok"])
        self.assertTrue(self.fabric.ratify_closure(self.workspace_id, proposed["closure_id"], "operator")["ok"])
        self.assertTrue(self.fabric.commit_closure(self.workspace_id, proposed["closure_id"], "operator")["ok"])
        return proposed

    def test_store_payload_append_failure_creates_an_in_memory_only_ghost(self) -> None:
        store = ClosureStore(self.tempdir.name, "direct_store_failure")
        entry = _HistoryFactory().entry("v1", workspace_id="direct_store_failure")
        with patch.object(store, "_append_jsonl", side_effect=OSError("payload unavailable")):
            with self.assertRaisesRegex(OSError, "payload unavailable"):
                store.add_version(entry)

        self.assertEqual(store.get_latest_version(entry.closure_id).version_id, "v1")
        reloaded = ClosureStore(self.tempdir.name, "direct_store_failure")
        self.assertIsNone(reloaded.get_latest_version(entry.closure_id))

    def test_store_internal_event_failure_leaves_store_only_initial_payload(self) -> None:
        original_append = ClosureStore._append_jsonl

        def fail_internal_event(store: ClosureStore, path: str, obj: dict) -> None:
            if path == store.events_path:
                raise OSError("store internal event unavailable")
            original_append(store, path, obj)

        with patch.object(ClosureStore, "_append_jsonl", new=fail_internal_event):
            with self.assertRaisesRegex(OSError, "store internal event unavailable"):
                self.fabric.propose_closure(**self.proposal_kwargs())

        restarted = self.restart()
        closure_id = restarted.list_closures(self.workspace_id)[0]
        self.assertIsNotNone(restarted.get_closure(self.workspace_id, closure_id))
        self.assertEqual(
            restarted._get_closure_ledger(self.workspace_id).list_events(closure_id=closure_id),
            [],
        )

    def test_failed_proposed_event_leaves_store_only_v1_that_cannot_enter_trusted_chain(self) -> None:
        with patch.object(ClosureLedger, "add_event", side_effect=OSError("ledger unavailable")):
            with self.assertRaisesRegex(OSError, "ledger unavailable"):
                self.fabric.propose_closure(**self.proposal_kwargs())

        restarted = self.restart()
        closure_id = restarted.list_closures(self.workspace_id)[0]
        self.assertEqual(
            restarted.ratify_closure(self.workspace_id, closure_id, "operator")["result_code"],
            "not_found",
        )
        self.assertEqual(
            restarted.commit_closure(self.workspace_id, closure_id, "operator")["result_code"],
            "not_found",
        )

    def test_failed_ratification_or_commit_event_has_no_payload_partial_and_can_retry(self) -> None:
        proposed = self.fabric.propose_closure(**self.proposal_kwargs())
        closure_id = proposed["closure_id"]
        with patch.object(ClosureLedger, "add_event", side_effect=OSError("ratify unavailable")):
            with self.assertRaisesRegex(OSError, "ratify unavailable"):
                self.fabric.ratify_closure(self.workspace_id, closure_id, "operator")

        restarted = self.restart()
        self.assertEqual(restarted._get_closure_ledger(self.workspace_id).get_latest_event_kind(closure_id), "proposed")
        self.assertTrue(restarted.ratify_closure(self.workspace_id, closure_id, "operator")["ok"])
        with patch.object(ClosureLedger, "add_event", side_effect=OSError("commit unavailable")):
            with self.assertRaisesRegex(OSError, "commit unavailable"):
                restarted.commit_closure(self.workspace_id, closure_id, "operator")

        after_commit_failure = self.restart()
        self.assertEqual(
            after_commit_failure._get_closure_ledger(self.workspace_id).get_latest_event_kind(closure_id),
            "ratified",
        )
        self.assertTrue(after_commit_failure.commit_closure(self.workspace_id, closure_id, "operator")["ok"])

    def test_failed_revised_event_keeps_future_revision_on_trusted_parent(self) -> None:
        proposed = self.committed()
        closure_id = proposed["closure_id"]
        with patch.object(ClosureLedger, "add_event", side_effect=OSError("revision unavailable")):
            with self.assertRaisesRegex(OSError, "revision unavailable"):
                self.fabric.revise_closure(
                    self.workspace_id,
                    closure_id,
                    {"what_to_carry_forward": "orphan v2"},
                    "operator",
                )

        restarted = self.restart()
        raw_v2 = restarted.get_closure(self.workspace_id, closure_id)
        self.assertNotEqual(raw_v2["version_id"], proposed["version_id"])
        self.assertEqual(
            restarted._get_closure_ledger(self.workspace_id).get_latest_event_kind(closure_id),
            "committed",
        )
        v3 = restarted.revise_closure(
            self.workspace_id,
            closure_id,
            {"what_to_carry_forward": "raw chain from orphan"},
            "operator",
        )
        self.assertTrue(v3["ok"])
        self.assertEqual(v3["parent_version_id"], proposed["version_id"])
        self.assertNotEqual(v3["parent_version_id"], raw_v2["version_id"])
        committed = restarted.commit_closure(self.workspace_id, closure_id, "operator")
        self.assertTrue(committed["ok"])
        self.assertEqual(committed["version_id"], v3["version_id"])


if __name__ == "__main__":
    unittest.main()
