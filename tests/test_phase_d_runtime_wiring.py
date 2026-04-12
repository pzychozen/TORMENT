# tests/test_phase_d_runtime_wiring.py
"""
Phase D runtime wiring tests — validates that live runtime paths enforce
the same governance invariants tested at module level in
test_phase_d_integration.py.

These tests exercise REAL runtime paths, not isolated module contracts.

Test groups:
  A. Scoring helper (pure-Python, no Fabric dependency)
  B. Runtime integration (requires TormentFabric, runs locally)

See: docs/AUDIT_phase_d_runtime_wiring.md
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ===========================================================================
# A. SCORING HELPER TESTS (pure-Python)
# ===========================================================================

from torment_service.scoring import (
    apply_collective_discount,
    is_collective_provenance,
    DEFAULT_COLLECTIVE_RETRIEVAL_DISCOUNT,
)


class TestIsCollectiveProvenance(unittest.TestCase):
    """Verify is_collective_provenance detects both provenance formats."""

    def test_legacy_collective_string(self):
        self.assertTrue(is_collective_provenance("collective"))

    def test_structured_collective_echo(self):
        prov = {"source_type": "collective_echo", "write_path": "collective_reingest"}
        self.assertTrue(is_collective_provenance(prov))

    def test_non_collective_string(self):
        self.assertFalse(is_collective_provenance("user_input"))

    def test_non_collective_dict(self):
        prov = {"source_type": "tool_result", "tool_name": "web_search"}
        self.assertFalse(is_collective_provenance(prov))

    def test_none_provenance(self):
        self.assertFalse(is_collective_provenance(None))

    def test_empty_dict(self):
        self.assertFalse(is_collective_provenance({}))

    def test_empty_string(self):
        self.assertFalse(is_collective_provenance(""))

    def test_memory_string(self):
        self.assertFalse(is_collective_provenance("memory"))


class TestApplyCollectiveDiscount(unittest.TestCase):
    """Verify apply_collective_discount applies correctly."""

    def test_legacy_collective_string_discounted(self):
        result = apply_collective_discount(0.80, "collective")
        self.assertAlmostEqual(result, 0.40)

    def test_structured_collective_echo_discounted(self):
        prov = {"source_type": "collective_echo"}
        result = apply_collective_discount(0.80, prov)
        self.assertAlmostEqual(result, 0.40)

    def test_non_collective_unchanged(self):
        result = apply_collective_discount(0.80, "user_input")
        self.assertAlmostEqual(result, 0.80)

    def test_non_collective_dict_unchanged(self):
        prov = {"source_type": "tool_result"}
        result = apply_collective_discount(0.80, prov)
        self.assertAlmostEqual(result, 0.80)

    def test_none_provenance_unchanged(self):
        result = apply_collective_discount(0.80, None)
        self.assertAlmostEqual(result, 0.80)

    def test_custom_discount(self):
        result = apply_collective_discount(1.00, "collective", discount=0.30)
        self.assertAlmostEqual(result, 0.30)

    def test_default_discount_is_050(self):
        self.assertAlmostEqual(DEFAULT_COLLECTIVE_RETRIEVAL_DISCOUNT, 0.50)

    def test_organic_always_above_collective_at_parity(self):
        """Same base score: organic ranks above collective after discount."""
        base = 0.75
        organic = apply_collective_discount(base, None)
        collective = apply_collective_discount(base, "collective")
        self.assertGreater(organic, collective)

    def test_high_collective_still_below_moderate_organic(self):
        """Even a high-scoring collective echo should not outrank a moderate organic."""
        echo_score = apply_collective_discount(0.90, "collective")
        organic_score = apply_collective_discount(0.50, None)
        self.assertLessEqual(echo_score, organic_score)


# ===========================================================================
# B. RUNTIME INTEGRATION TESTS (require TormentFabric)
# ===========================================================================

try:
    from torment_service.fabric import TormentFabric
    _HAS_FABRIC = True
except (ImportError, SyntaxError):
    _HAS_FABRIC = False


@unittest.skipUnless(_HAS_FABRIC, "TormentFabric not importable (FUSE truncation?)")
class TestReingestConvergenceEchoDoesNotEmitPacket(unittest.TestCase):
    """TEST 1: Runtime — echo created by reingest_convergence must not emit a packet."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_HIVEMIND_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmp)

    def tearDown(self):
        os.environ.pop("TORMENT_HIVEMIND_ENABLE", None)

    def test_reingest_convergence_echo_does_not_emit_packet(self):
        import numpy as np
        from torment_service.collective_models import ResonancePacket, ConvergenceEvent
        ws = "ws_rt_test"
        self.fabric.create_agent(ws, "agent_a")
        self.fabric.create_agent(ws, "agent_b")

        # Ingest content from two agents to build kernel state
        # Use "personal" — the default domain that always exists on a bare workspace
        self.fabric.ingest(ws, "agent_a", "Loss and memory at the harbor", step=1, domain_id="personal")
        self.fabric.ingest(ws, "agent_b", "Loss and memory at the harbor", step=1, domain_id="personal")

        # Manually create a convergence event (faster than relying on detection)
        field = self.fabric._get_collective_field(ws)
        event = ConvergenceEvent(
            workspace_id=ws,
            domain_id="personal",
            confidence=0.80,
            participating_agents=["agent_a", "agent_b"],
            dominant_motifs=["motif_loss"],
        )
        field.append_event(event)

        # Count packets before reingest
        packets_before = len(field.recent_packets(limit=1000))

        # Perform reingest
        result = self.fabric.reingest_convergence(ws, "agent_b", event.event_id)
        self.assertTrue(result.get("eligible"), f"Reingest should succeed: {result}")
        echo_eid = result.get("echo_eid")
        self.assertIsNotNone(echo_eid)

        # Count packets after reingest
        all_packets = field.recent_packets(limit=1000)
        echo_packets = [p for p in all_packets if p.get("source_eid") == echo_eid]

        self.assertEqual(
            len(echo_packets), 0,
            f"Echo EID {echo_eid} emitted {len(echo_packets)} packet(s) — "
            f"invariant violation: echoes must never emit packets"
        )


@unittest.skipUnless(_HAS_FABRIC, "TormentFabric not importable (FUSE truncation?)")
class TestReingestConvergenceEchoIsTerminal(unittest.TestCase):
    """TEST 2: Runtime — echo payload is terminal immediately after creation."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_HIVEMIND_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmp)

    def tearDown(self):
        os.environ.pop("TORMENT_HIVEMIND_ENABLE", None)

    def test_reingest_convergence_echo_is_marked_collective_and_terminal(self):
        from torment_service.collective_models import ConvergenceEvent
        from torment_service.governance import resolve_governance, should_emit_packet, allows_collective_reingest
        from torment_service.scoring import is_collective_provenance

        ws = "ws_rt_term"
        self.fabric.create_agent(ws, "agent_a")
        self.fabric.create_agent(ws, "agent_b")
        self.fabric.ingest(ws, "agent_a", "Shared insight about renewal", step=1, domain_id="personal")
        self.fabric.ingest(ws, "agent_b", "Shared insight about renewal", step=1, domain_id="personal")

        field = self.fabric._get_collective_field(ws)
        event = ConvergenceEvent(
            workspace_id=ws, domain_id="personal", confidence=0.80,
            participating_agents=["agent_a", "agent_b"],
        )
        field.append_event(event)

        result = self.fabric.reingest_convergence(ws, "agent_b", event.event_id)
        self.assertTrue(result.get("eligible"), f"Reingest failed: {result}")
        echo_eid = result["echo_eid"]

        # Fetch the stored entity
        ak = self.fabric._agent_key(ws, "agent_b")
        graph = self.fabric.private_graphs.get(ak)
        self.assertIsNotNone(graph)
        ent = graph.entities.get(int(echo_eid))
        self.assertIsNotNone(ent, f"Echo entity {echo_eid} not found")

        payload = ent.payload

        # Collective provenance
        self.assertTrue(
            is_collective_provenance(payload.get("provenance")),
            f"Echo provenance should be collective, got: {payload.get('provenance')}"
        )

        # Terminal governance flags
        gov = resolve_governance(payload)
        self.assertTrue(gov.collective_export_blocked,
                        "Echo must have collective_export_blocked=True")
        self.assertTrue(gov.collective_reingest_blocked,
                        "Echo must have collective_reingest_blocked=True")

        # Governance helpers agree
        self.assertFalse(should_emit_packet(payload),
                         "should_emit_packet must return False for echo")
        self.assertFalse(allows_collective_reingest(payload),
                         "allows_collective_reingest must return False for echo")

        # Source metadata
        self.assertEqual(payload.get("source_event_id"), event.event_id)
        self.assertIn("agent_a", payload.get("source_agents", []))


@unittest.skipUnless(_HAS_FABRIC, "TormentFabric not importable (FUSE truncation?)")
class TestReingestConvergenceFailsCleanlyIfEchoEntityMissing(unittest.TestCase):
    """TEST 5: Runtime — missing entity after echo ingest does not report false success."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_HIVEMIND_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmp)

    def tearDown(self):
        os.environ.pop("TORMENT_HIVEMIND_ENABLE", None)

    def test_reingest_convergence_fails_cleanly_if_echo_entity_missing(self):
        from torment_service.collective_models import ConvergenceEvent

        ws = "ws_rt_fail"
        self.fabric.create_agent(ws, "agent_a")
        self.fabric.create_agent(ws, "agent_b")
        self.fabric.ingest(ws, "agent_a", "Test content", step=1, domain_id="personal")
        self.fabric.ingest(ws, "agent_b", "Test content", step=1, domain_id="personal")

        field = self.fabric._get_collective_field(ws)
        event = ConvergenceEvent(
            workspace_id=ws, domain_id="personal", confidence=0.80,
            participating_agents=["agent_a", "agent_b"],
        )
        field.append_event(event)

        # Sabotage: replace the graph's entities dict with a subclass whose
        # .get() returns None for the echo EID.  We intercept the post-ingest
        # governance patch (graph.entities.get(echo_eid)) while letting the
        # ingest itself succeed normally.
        ak = self.fabric._agent_key(ws, "agent_b")
        original_graph = self.fabric.private_graphs.get(ak)
        self.assertIsNotNone(original_graph, "Graph should exist after ingest")

        class _SabotageDict(dict):
            """Dict subclass that hides newly added keys to simulate lookup failure."""
            def __init__(self, base, snapshot_keys):
                super().__init__(base)
                # Keys that existed before reingest — allow lookups for those
                self._known = set(snapshot_keys)

            def get(self, key, *args):
                if key not in self._known:
                    # This is a post-ingest echo EID — hide it
                    return args[0] if args else None
                return super().get(key, *args)

        original_graph.entities = _SabotageDict(
            original_graph.entities,
            snapshot_keys=set(original_graph.entities.keys()),
        )

        result = self.fabric.reingest_convergence(ws, "agent_b", event.event_id)

        # Should NOT report eligible=True — should indicate partial failure
        self.assertTrue(result.get("partial_failure"),
                        f"Expected partial_failure in result: {result}")
        self.assertFalse(result.get("eligible", True),
                         "Partial failure should not claim eligible=True")
        self.assertIn("governance patch failed", result.get("reason", ""))


if __name__ == "__main__":
    unittest.main()
