# tests/test_resolve_baton_soft_consume.py
"""
T4 — AC-2 proof: resolve_baton is explicit soft-consume with audit trail.

Covers the acceptance criterion from BLOCK_A_DESIGN.md §4 AC-2:

    fabric.resolve_baton(workspace_id, agent_id, eid, outcome) marks the
    entry's baton_lifecycle.status = "consumed" and appends a lifecycle
    event to an append-only ledger. The underlying content is preserved;
    the entry remains inspectable via baton-aware queries. Resolution
    never creates a new core entry in a single call.

Design per BLOCK_A_DESIGN.md §6.3–6.4:
    - Idempotent: re-resolving a consumed baton is a no-op.
    - Envelope: {ok, result_code, eid, outcome}.
    - result_code ∈ {"resolved", "already_consumed", "not_found", "not_a_baton"}.
    - Payload is current-state source of truth; BatonLedger is the audit trail.
    - Resolution NEVER creates a new core entry (separate explicit ingest
      would be required for that, with parent_eids pointing back).

These tests FAIL against current code (pre-implementation). They pass
once:
    - fabric.resolve_baton exists with the specified envelope contract
    - BatonLedger (torment_service/baton_ledger.py) exists and is
      updated on resolve
    - The payload's baton_lifecycle.status mutates on resolve

References:
    - BLOCK_A_DESIGN.md §4 AC-2
    - BLOCK_A_DESIGN.md §6.3 (resolve_baton semantics)
    - BLOCK_A_DESIGN.md §6.4 (BatonLedger — payload is state source of truth)
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric
from torment_service.provenance_v1 import ProvenanceV1


def _baton_prov() -> dict:
    return ProvenanceV1.for_baton_ingest().to_dict()


def _lifecycle() -> dict:
    return {
        "owner": "user",
        "expires_when": "user confirms done",
        "resolution_condition": "explicit acknowledgment",
    }


class TestResolveBatonHappyPath(unittest.TestCase):
    """Normal soft-consume flow: ingest baton, resolve it, verify state."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        r = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Verify the migration before release.",
            step=1, scope="private",
            provenance=_baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": _lifecycle()},
        )
        self.baton_eid = int(r["eid"])

    def _payload(self, eid: int) -> dict:
        ak = self.fabric._agent_key("ws1", "atlas")
        g = self.fabric.private_graphs[ak]
        return dict(g.entities[eid].payload or {})

    def test_resolve_baton_method_exists(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "resolve_baton"),
            "fabric.resolve_baton must exist per §6.3"
        )

    def test_resolve_baton_envelope_shape(self) -> None:
        result = self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.baton_eid, outcome="acknowledged",
        )
        self.assertIn("ok", result)
        self.assertIn("result_code", result)
        self.assertIn("eid", result)
        self.assertIn("outcome", result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["result_code"], "resolved")
        self.assertEqual(result["eid"], self.baton_eid)

    def test_resolve_updates_status_to_consumed(self) -> None:
        self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.baton_eid, outcome="acknowledged",
        )
        payload = self._payload(self.baton_eid)
        lifecycle = payload.get("baton_lifecycle", {})
        self.assertEqual(lifecycle.get("status"), "consumed")

    def test_resolve_records_consumed_timestamp_and_outcome(self) -> None:
        before_ts = int(time.time())
        self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.baton_eid, outcome="acknowledged",
            resolver="atlas",
        )
        payload = self._payload(self.baton_eid)
        lifecycle = payload.get("baton_lifecycle", {})
        self.assertIn("consumed_at", lifecycle)
        self.assertIn("consumed_by", lifecycle)
        self.assertIn("consumed_outcome", lifecycle)
        self.assertEqual(lifecycle["consumed_outcome"], "acknowledged")
        self.assertEqual(lifecycle["consumed_by"], "atlas")
        self.assertGreaterEqual(int(lifecycle["consumed_at"]), before_ts)

    def test_content_preserved_after_resolution(self) -> None:
        """Underlying text and provenance are preserved after resolve —
        soft-consume does not delete content."""
        before_payload = self._payload(self.baton_eid)
        before_summary = before_payload.get("summary", "")

        self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.baton_eid, outcome="discarded",
        )

        after_payload = self._payload(self.baton_eid)
        # Core content fields unchanged
        self.assertEqual(after_payload.get("summary", ""), before_summary)
        self.assertEqual(
            after_payload.get("memory_class"), "baton",
            "memory_class must not change — resolution is lifecycle, "
            "not re-classification"
        )
        # Provenance preserved
        self.assertEqual(
            after_payload.get("provenance"),
            before_payload.get("provenance"),
        )

    def test_resolve_never_creates_new_core_entry(self) -> None:
        """Per §6.3: resolution NEVER creates a new core entry in a
        single call. Count entries before and after; baton stays, no
        new core appears."""
        ak = self.fabric._agent_key("ws1", "atlas")
        g = self.fabric.private_graphs[ak]
        entities_before = set(g.entities.keys())

        self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.baton_eid, outcome="promoted",
        )

        entities_after = set(g.entities.keys())
        self.assertEqual(
            entities_before, entities_after,
            "resolve_baton must not create new entities. "
            f"Before: {entities_before}, After: {entities_after}"
        )


class TestResolveBatonIdempotent(unittest.TestCase):
    """Re-resolving an already-consumed baton is a no-op."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        r = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Idempotency test baton.",
            step=1, scope="private",
            provenance=_baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": _lifecycle()},
        )
        self.baton_eid = int(r["eid"])
        # First resolve
        self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.baton_eid, outcome="acknowledged",
        )

    def test_second_resolve_returns_already_consumed(self) -> None:
        result = self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.baton_eid, outcome="anything",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["result_code"], "already_consumed")

    def test_second_resolve_does_not_overwrite_outcome(self) -> None:
        ak = self.fabric._agent_key("ws1", "atlas")
        g = self.fabric.private_graphs[ak]
        first_lifecycle = dict(
            (g.entities[self.baton_eid].payload or {}).get("baton_lifecycle", {})
        )

        self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.baton_eid, outcome="different_outcome",
        )

        second_lifecycle = dict(
            (g.entities[self.baton_eid].payload or {}).get("baton_lifecycle", {})
        )
        self.assertEqual(
            first_lifecycle.get("consumed_outcome"),
            second_lifecycle.get("consumed_outcome"),
            "Second resolve must not overwrite the first outcome"
        )


class TestResolveBatonErrorCases(unittest.TestCase):
    """Non-happy-path envelopes: not_found, not_a_baton."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Non-baton core memory
        r = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="A regular core memory.",
            step=1, scope="private",
        )
        self.core_eid = int(r["eid"])

    def test_not_found_eid_returns_not_found(self) -> None:
        result = self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=999_999, outcome="anything",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["result_code"], "not_found")

    def test_non_baton_eid_returns_not_a_baton(self) -> None:
        result = self.fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=self.core_eid, outcome="anything",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["result_code"], "not_a_baton")


class TestBatonLedgerPresence(unittest.TestCase):
    """BatonLedger class exists and records consume events.

    Per §6.4: payload is current-state source of truth; ledger is
    historical audit trail. The ledger must receive an event on
    resolve so the audit trail exists.
    """

    def test_baton_ledger_module_exists(self) -> None:
        try:
            from torment_service import baton_ledger as bl
        except ImportError:
            self.fail("torment_service.baton_ledger module must exist per §6.4")
        self.assertTrue(hasattr(bl, "BatonLedger"))
        self.assertTrue(hasattr(bl, "BatonEvent"))

    def test_resolve_appends_ledger_event(self) -> None:
        """After resolve_baton, the agent's ledger must contain a
        corresponding 'consumed' event."""
        tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        fabric = TormentFabric(data_dir=tmp)
        fabric.get_workspace("ws1")
        fabric.create_agent("ws1", "atlas")

        r = fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Ledger test.", step=1, scope="private",
            provenance=_baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": _lifecycle()},
        )
        eid = int(r["eid"])

        fabric.resolve_baton(
            workspace_id="ws1", agent_id="atlas",
            eid=eid, outcome="acknowledged",
        )

        # Ledger should have at least one event for this eid
        from torment_service.baton_ledger import BatonLedger
        ledger = BatonLedger(data_dir=tmp, workspace_id="ws1", agent_id="atlas")
        events = ledger.list_events(eid=eid)
        consumed_events = [e for e in events if getattr(e, "kind", None) == "consumed"]
        self.assertGreater(
            len(consumed_events), 0,
            "resolve_baton must append a 'consumed' event to the ledger"
        )


if __name__ == "__main__":
    unittest.main()
