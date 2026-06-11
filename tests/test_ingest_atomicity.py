"""
tests/test_ingest_atomicity.py — Invalid-domain ingest atomicity tests

Verifies that `fabric.ingest()` does NOT leave orphan state when the
caller-supplied `domain_id` does not exist in the workspace's motif
registries.

Bug context (pre-fix):
    In fabric.ingest(), `chosen_domain = domain_id or routed[0] or "research"`
    was consumed downstream of graph.spawn_memory(), which had already
    mutated graph.entities (RAM), appended an embedding row to the shard,
    registered the embedding in the in-memory cache, and written
    MEMORY_CREATE to memory_events.jsonl. The motif-registry lookup
    `ws.motif_regs[chosen_domain]` then raised KeyError, and flush_node()
    was never reached. Result: orphan MEMORY_CREATE event + orphan
    embedding shard row + transient RAM ghost, with NO matching node row
    in nodes.jsonl.

Fix (Phase B):
    A preflight check in fabric.ingest() rejects unknown domain_id
    BEFORE any state mutation, raising HTTPException(400).

These tests pin that behavior so a future regression is loud.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric
from torment_service.spine import SpineRequest, submit_task
from torment_service.request_context import RequestContext


# An invalid domain string chosen to be obviously not a default.
INVALID_DOMAIN = "definitely_not_a_real_domain_xyz_12345"


# ---------------------------------------------------------------------------
# Test helpers (mirror tests/test_tool_result_ingest.py)
# ---------------------------------------------------------------------------

def _make_fabric():
    """Create a fresh in-memory fabric with one workspace and agent."""
    tmpdir = tempfile.mkdtemp(prefix="torment_test_atomicity_")
    fabric = TormentFabric(data_dir=tmpdir)
    fabric.get_workspace("test-ws")
    fabric.create_agent("test-ws", "agent-1")
    return fabric


def _make_ctx(trust=0.6):
    return RequestContext(
        client_id="test_client",
        workspace_id="test-ws",
        agent_id="agent-1",
        trust_tier=trust,
    )


def _count_lines(path):
    """Return number of lines in a file, or 0 if the file does not exist."""
    if not path or not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def _snapshot_state(fabric):
    """Capture pre-ingest persistence + RAM state for atomicity comparison.

    Returns a dict of counts that should all be identical after a failed
    ingest. Any non-zero delta means the failure left orphan state.
    """
    ak = fabric._agent_key("test-ws", "agent-1")
    graph = fabric.private_graphs[ak]
    return {
        "entities": len(graph.entities),
        "nodes_lines": _count_lines(getattr(graph, "meta_path", None)),
        "events_lines": _count_lines(getattr(graph, "events_path", None)),
    }


# ===========================================================================
# Tests
# ===========================================================================

class TestInvalidDomainToolResultIngestAtomicity(unittest.TestCase):
    """Invalid domain on tool_result_ingest must leave no side effects."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()
        # Sanity: the invalid domain really isn't there
        ws = self.fabric.get_workspace("test-ws")
        self.assertNotIn(INVALID_DOMAIN, ws.motif_regs)

    def test_failed_ingest_returns_envelope_not_ok(self):
        """A failed envelope is the visible signal to the caller."""
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={
                "tool_name": "atomicity_probe",
                "content": "Atomicity test content: token-ALPHA-BETA-7777",
                "summary": "Atomicity test ALPHA-BETA-7777",
                "step": 1,
                "domain_id": INVALID_DOMAIN,
                "session_id": "atomicity_test",
            },
        )
        resp = submit_task(req, self.fabric, self.ctx)
        self.assertFalse(resp.ok)

    def test_failed_ingest_does_not_grow_entities(self):
        before = _snapshot_state(self.fabric)
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={
                "tool_name": "atomicity_probe",
                "content": "Atomicity test content: token-ALPHA-BETA-7777",
                "summary": "Atomicity test ALPHA-BETA-7777",
                "step": 1,
                "domain_id": INVALID_DOMAIN,
                "session_id": "atomicity_test",
            },
        )
        _ = submit_task(req, self.fabric, self.ctx)
        after = _snapshot_state(self.fabric)
        self.assertEqual(
            after["entities"], before["entities"],
            "graph.entities grew after a failed invalid-domain ingest "
            "(RAM ghost would have been left behind)",
        )

    def test_failed_ingest_does_not_append_memory_events(self):
        before = _snapshot_state(self.fabric)
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={
                "tool_name": "atomicity_probe",
                "content": "Atomicity test content: token-ALPHA-BETA-7777",
                "summary": "Atomicity test ALPHA-BETA-7777",
                "step": 1,
                "domain_id": INVALID_DOMAIN,
                "session_id": "atomicity_test",
            },
        )
        _ = submit_task(req, self.fabric, self.ctx)
        after = _snapshot_state(self.fabric)
        self.assertEqual(
            after["events_lines"], before["events_lines"],
            "memory_events.jsonl grew after a failed invalid-domain ingest "
            "(orphan MEMORY_CREATE row would have been left behind)",
        )

    def test_failed_ingest_does_not_append_nodes(self):
        before = _snapshot_state(self.fabric)
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={
                "tool_name": "atomicity_probe",
                "content": "Atomicity test content: token-ALPHA-BETA-7777",
                "summary": "Atomicity test ALPHA-BETA-7777",
                "step": 1,
                "domain_id": INVALID_DOMAIN,
                "session_id": "atomicity_test",
            },
        )
        _ = submit_task(req, self.fabric, self.ctx)
        after = _snapshot_state(self.fabric)
        self.assertEqual(
            after["nodes_lines"], before["nodes_lines"],
            "nodes.jsonl unexpectedly changed after a failed invalid-domain "
            "ingest (canonical write should be all-or-nothing)",
        )

    def test_failed_ingest_not_retrievable(self):
        """Retrieval must not surface the would-be entity even from RAM."""
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={
                "tool_name": "atomicity_probe",
                "content": "Atomicity test content: token-ALPHA-BETA-7777",
                "summary": "Atomicity test ALPHA-BETA-7777",
                "step": 1,
                "domain_id": INVALID_DOMAIN,
                "session_id": "atomicity_test",
            },
        )
        _ = submit_task(req, self.fabric, self.ctx)
        # Query for the unique token; no hit must contain it
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="ALPHA-BETA-7777",
            top_k=5,
        )
        hits = results.get("results", []) or results.get("hits", [])
        for h in hits:
            self.assertNotIn(
                "ALPHA-BETA-7777", str(h.get("summary", "")),
                f"Found a retrievable phantom: {h}",
            )


class TestInvalidDomainRegularIngestAtomicity(unittest.TestCase):
    """The fix must apply to plain `ingest` too, not just tool_result_ingest.

    This guards the claim that the bug was in shared `fabric.ingest()` code,
    not in any one Spine operation handler.
    """

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()
        ws = self.fabric.get_workspace("test-ws")
        self.assertNotIn(INVALID_DOMAIN, ws.motif_regs)

    def test_failed_regular_ingest_no_orphan_state(self):
        before = _snapshot_state(self.fabric)
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="ingest",
            payload={
                "text": "Regular ingest atomicity check: token-GAMMA-DELTA-9999",
                "step": 1,
                "domain_id": INVALID_DOMAIN,
            },
        )
        resp = submit_task(req, self.fabric, self.ctx)
        after = _snapshot_state(self.fabric)

        self.assertFalse(resp.ok)
        self.assertEqual(after["entities"], before["entities"])
        self.assertEqual(after["events_lines"], before["events_lines"])
        self.assertEqual(after["nodes_lines"], before["nodes_lines"])


class TestValidDomainStillWorks(unittest.TestCase):
    """Sanity: the preflight check must not break the happy path."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()

    def test_valid_tool_result_ingest_still_stores(self):
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={
                "tool_name": "weather_api",
                "content": "Current weather in Reykjavik: 3C, partly cloudy",
                "summary": "Weather: Reykjavik 3C cloudy",
                "step": 1,
                "domain_id": "personal",
                "session_id": "sess_atomic_happy",
            },
        )
        resp = submit_task(req, self.fabric, self.ctx)
        self.assertTrue(resp.ok)
        self.assertIn("eid", resp.result)
        eid = resp.result["eid"]
        self.assertIsInstance(eid, int)

        # Provenance round-trip
        ak = self.fabric._agent_key("test-ws", "agent-1")
        graph = self.fabric.private_graphs[ak]
        ent = graph.entities[eid]
        prov = ent.payload.get("provenance") or {}
        self.assertEqual(prov.get("source_type"), "tool_result")
        self.assertEqual(prov.get("write_path"), "tool_ingest")
        self.assertEqual(prov.get("tool_name"), "weather_api")


if __name__ == "__main__":
    unittest.main()
