"""
tests/test_tool_result_ingest.py — Tool-result ingest pipeline tests

Tests covering:
    - Successful ingest through Spine governance (happy path)
    - Provenance persistence and round-trip
    - Retrieval visibility (tool-result memories appear in queries)
    - /debug/provenance visibility
    - Malformed/missing payload handling
    - Default parent_eids=[]
    - No identity flags implicitly set
    - No execution semantics (memory only)

Doctrine:
    TORMENT may remember what tools returned.
    TORMENT does not decide what tools to run.
    This test file verifies the first half of that boundary.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric
from torment_service.spine import (
    SpineRequest,
    submit_task,
    OPERATION_REGISTRY,
    FAST_DISPATCH,
)
from torment_service.request_context import RequestContext
from torment_service.provenance_v1 import (
    ProvenanceV1,
    SOURCE_TOOL_RESULT,
    WRITE_TOOL_INGEST,
    VALID_SOURCE_TYPES,
    VALID_WRITE_PATHS,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal fabric + context for testing
# ---------------------------------------------------------------------------

def _make_fabric():
    """Create a fresh in-memory fabric with one workspace and agent."""
    tmpdir = tempfile.mkdtemp(prefix="torment_test_tool_")
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


def _make_tool_ingest_request(**overrides):
    defaults = {
        "tool_name": "weather_api",
        "content": "Current weather in Reykjavik: 3C, partly cloudy",
        "summary": "Weather: Reykjavik 3C cloudy",
        "step": 1,
        "domain_id": "personal",
        "session_id": "sess_001",
    }
    defaults.update(overrides)
    return SpineRequest(
        workspace_id="test-ws",
        agent_id="agent-1",
        operation="tool_result_ingest",
        payload=defaults,
    )


# ===========================================================================
# Tests
# ===========================================================================

class TestToolResultIngestRegistration(unittest.TestCase):
    """Verify operation and handler are properly registered."""

    def test_operation_registered(self):
        self.assertIn("tool_result_ingest", OPERATION_REGISTRY)

    def test_operation_spec(self):
        spec = OPERATION_REGISTRY["tool_result_ingest"]
        self.assertEqual(spec.default_path, "fast")
        self.assertEqual(spec.op_class, "write")
        self.assertEqual(spec.exposure_tier, "guarded")
        self.assertAlmostEqual(spec.min_trust, 0.6)

    def test_fast_dispatch_registered(self):
        self.assertIn("tool_result_ingest", FAST_DISPATCH)

    def test_provenance_constants_registered(self):
        self.assertIn(SOURCE_TOOL_RESULT, VALID_SOURCE_TYPES)
        self.assertIn(WRITE_TOOL_INGEST, VALID_WRITE_PATHS)


class TestToolResultIngestHappyPath(unittest.TestCase):
    """Successful ingest through Spine governance."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()

    def test_basic_ingest(self):
        req = _make_tool_ingest_request()
        resp = submit_task(req, self.fabric, self.ctx)
        self.assertTrue(resp.ok)
        self.assertTrue(resp.allowed)
        self.assertEqual(resp.path, "fast")
        self.assertIn("eid", resp.result)

    def test_ingest_returns_eid(self):
        req = _make_tool_ingest_request()
        resp = submit_task(req, self.fabric, self.ctx)
        eid = resp.result.get("eid")
        self.assertIsNotNone(eid)
        self.assertIsInstance(eid, int)

    def test_ingest_with_metadata(self):
        req = _make_tool_ingest_request(
            tool_metadata={"endpoint": "/v1/weather", "latency_ms": 230}
        )
        resp = submit_task(req, self.fabric, self.ctx)
        self.assertTrue(resp.ok)


class TestToolResultProvenance(unittest.TestCase):
    """Provenance persistence and correctness."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()
        req = _make_tool_ingest_request(
            tool_name="calendar_api",
            tool_metadata={"method": "GET"},
        )
        resp = submit_task(req, self.fabric, self.ctx)
        self.eid = resp.result["eid"]
        ak = self.fabric._agent_key("test-ws", "agent-1")
        graph = self.fabric.private_graphs[ak]
        self.entity = graph.entities[self.eid]
        self.prov = self.entity.payload.get("provenance", {})

    def test_source_type(self):
        self.assertEqual(self.prov["source_type"], "tool_result")

    def test_write_path(self):
        self.assertEqual(self.prov["write_path"], "tool_ingest")

    def test_tool_name_preserved(self):
        self.assertEqual(self.prov["tool_name"], "calendar_api")

    def test_parent_eids_empty_by_default(self):
        self.assertEqual(self.prov["parent_eids"], [])

    def test_schema_version(self):
        self.assertEqual(self.prov["schema_version"], "1.0")

    def test_session_id_preserved(self):
        self.assertEqual(self.prov.get("session_id"), "sess_001")

    def test_step_preserved(self):
        self.assertEqual(self.prov.get("created_at_step"), 1)

    def test_timestamp_present(self):
        self.assertIn("created_at_ts", self.prov)
        self.assertIsNotNone(self.prov["created_at_ts"])

    def test_metadata_in_notes(self):
        notes = self.prov.get("notes", "")
        self.assertIn("tool_metadata", notes)

    def test_provenance_round_trip(self):
        """Verify provenance survives from_dict() → to_dict() round-trip."""
        p = ProvenanceV1.from_dict(self.prov)
        d = p.to_dict()
        self.assertEqual(d["source_type"], "tool_result")
        self.assertEqual(d["write_path"], "tool_ingest")
        self.assertEqual(d["tool_name"], "calendar_api")
        self.assertEqual(d["parent_eids"], [])


class TestToolResultRetrieval(unittest.TestCase):
    """Tool-result memories are visible in normal retrieval."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()
        req = _make_tool_ingest_request(
            content="The server response time was 150ms with status 200 OK",
            summary="Server health check: 150ms, 200 OK",
        )
        resp = submit_task(req, self.fabric, self.ctx)
        self.eid = resp.result["eid"]

    def test_retrieval_returns_tool_result(self):
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="server response time",
            top_k=5,
        )
        hits = results.get("results", [])
        self.assertGreater(len(hits), 0)

    def test_retrieval_preserves_provenance(self):
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="server response",
            top_k=5,
        )
        hits = results.get("results", [])
        self.assertGreater(len(hits), 0)
        top = hits[0]
        prov = (top.get("payload") or top).get("provenance", {})
        self.assertEqual(prov.get("source_type"), "tool_result")


class TestToolResultSemanticPolicy(unittest.TestCase):
    """Tool results are external-origin, not identity-canonical."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()
        req = _make_tool_ingest_request()
        resp = submit_task(req, self.fabric, self.ctx)
        self.eid = resp.result["eid"]
        ak = self.fabric._agent_key("test-ws", "agent-1")
        graph = self.fabric.private_graphs[ak]
        self.payload = graph.entities[self.eid].payload

    def test_not_identity_canonical(self):
        """Tool results should not carry identity flags."""
        prov = self.payload.get("provenance", {})
        # source_type must be tool_result, not user_input or role_output
        self.assertEqual(prov["source_type"], "tool_result")
        self.assertNotEqual(prov["source_type"], "user_input")
        self.assertNotEqual(prov["source_type"], "role_output")

    def test_no_seed_contamination(self):
        """Tool results must not have character seed markers."""
        self.assertNotIn("seed_id", self.payload)
        self.assertNotIn("is_seed", self.payload)

    def test_stored_as_private_scope(self):
        """Default scope is private."""
        # The entity exists in the private graph (setUp found it there)
        self.assertIsNotNone(self.payload)


class TestToolResultParentEids(unittest.TestCase):
    """parent_eids behavior for tool-result ingest."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()

    def test_default_empty_parents(self):
        req = _make_tool_ingest_request()
        resp = submit_task(req, self.fabric, self.ctx)
        ak = self.fabric._agent_key("test-ws", "agent-1")
        graph = self.fabric.private_graphs[ak]
        prov = graph.entities[resp.result["eid"]].payload["provenance"]
        self.assertEqual(prov["parent_eids"], [])

    def test_explicit_parent_eids_preserved(self):
        """If caller explicitly supplies parent_eids, they should persist."""
        req = _make_tool_ingest_request(parent_eids=[100, 200])
        resp = submit_task(req, self.fabric, self.ctx)
        ak = self.fabric._agent_key("test-ws", "agent-1")
        graph = self.fabric.private_graphs[ak]
        prov = graph.entities[resp.result["eid"]].payload["provenance"]
        self.assertEqual(prov["parent_eids"], [100, 200])


class TestToolResultTrustEnforcement(unittest.TestCase):
    """Spine trust enforcement for tool_result_ingest."""

    def setUp(self):
        self.fabric = _make_fabric()

    def test_insufficient_trust_rejected(self):
        """Trust below TRUST_INGEST (0.6) should be rejected."""
        ctx = _make_ctx(trust=0.3)  # below 0.6 threshold
        req = _make_tool_ingest_request()
        resp = submit_task(req, self.fabric, ctx)
        self.assertFalse(resp.allowed)

    def test_sufficient_trust_allowed(self):
        ctx = _make_ctx(trust=0.6)
        req = _make_tool_ingest_request()
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.allowed)
        self.assertTrue(resp.ok)


class TestToolResultMalformedPayload(unittest.TestCase):
    """Handling of missing or malformed payload fields."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()

    def test_missing_content_uses_empty(self):
        """Missing content should not crash — uses empty string."""
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={"tool_name": "test_tool"},
        )
        resp = submit_task(req, self.fabric, self.ctx)
        # Should still succeed (empty content is valid, if not useful)
        self.assertTrue(resp.ok)

    def test_missing_tool_name_defaults(self):
        """Missing tool_name should default to 'unknown_tool'."""
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={"content": "some result data"},
        )
        resp = submit_task(req, self.fabric, self.ctx)
        self.assertTrue(resp.ok)
        ak = self.fabric._agent_key("test-ws", "agent-1")
        graph = self.fabric.private_graphs[ak]
        prov = graph.entities[resp.result["eid"]].payload["provenance"]
        self.assertEqual(prov["tool_name"], "unknown_tool")

    def test_empty_payload_still_ingests(self):
        """Completely empty payload should still route through without crash."""
        req = SpineRequest(
            workspace_id="test-ws",
            agent_id="agent-1",
            operation="tool_result_ingest",
            payload={},
        )
        resp = submit_task(req, self.fabric, self.ctx)
        self.assertTrue(resp.ok)


class TestToolResultProvenanceFactory(unittest.TestCase):
    """Direct tests on ProvenanceV1.for_tool_result() factory."""

    def test_factory_creates_correct_type(self):
        p = ProvenanceV1.for_tool_result(tool_name="test")
        self.assertEqual(p.source_type, SOURCE_TOOL_RESULT)
        self.assertEqual(p.write_path, WRITE_TOOL_INGEST)

    def test_factory_stores_tool_name(self):
        p = ProvenanceV1.for_tool_result(tool_name="weather_api")
        self.assertEqual(p.tool_name, "weather_api")

    def test_factory_empty_parents_by_default(self):
        p = ProvenanceV1.for_tool_result(tool_name="t")
        self.assertEqual(p.parent_eids, [])

    def test_factory_accepts_parent_eids(self):
        p = ProvenanceV1.for_tool_result(tool_name="t", parent_eids=[1, 2, 3])
        self.assertEqual(p.parent_eids, [1, 2, 3])

    def test_factory_deduplicates_parents(self):
        p = ProvenanceV1.for_tool_result(tool_name="t", parent_eids=[1, 2, 1, 3])
        self.assertEqual(p.parent_eids, [1, 2, 3])

    def test_to_dict_includes_all_fields(self):
        p = ProvenanceV1.for_tool_result(
            tool_name="api", step=5, session_id="s1"
        )
        d = p.to_dict()
        self.assertIn("source_type", d)
        self.assertIn("write_path", d)
        self.assertIn("tool_name", d)
        self.assertIn("parent_eids", d)
        self.assertIn("schema_version", d)
        self.assertIn("created_at_ts", d)


if __name__ == "__main__":
    unittest.main()
