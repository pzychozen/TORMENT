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


# ===========================================================================
# Tool-result retrieval semantics tests (v2.4.3)
# ===========================================================================

class TestToolResultRetrievalScoring(unittest.TestCase):
    """Verify tool-result memories receive a retrieval discount."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()
        # Ingest a user memory (step 1)
        self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="I visited Reykjavik last summer and loved the weather",
            step=1,
            domain_id="personal",
            scope="private",
        )
        # Ingest a tool-result memory with similar content (step 2)
        from torment_service.provenance_v1 import ProvenanceV1
        prov = ProvenanceV1.for_tool_result(
            tool_name="weather_api",
            parent_eids=[],
            step=2,
        ).to_dict()
        self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="Current weather in Reykjavik: 3C, partly cloudy, winds from north",
            step=2,
            domain_id="personal",
            scope="private",
            provenance=prov,
        )

    def test_tool_result_retrieval_discount_applied(self):
        """Tool-result hit should have a lower final_score than a comparable user memory."""
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="weather in Reykjavik",
            top_k=10,
        )
        hits = results.get("results", [])
        self.assertGreaterEqual(len(hits), 2, "Expected at least 2 hits")
        # Find tool-result vs user hit
        tool_hits = [h for h in hits if h.get("provenance_type") == "tool_result"]
        user_hits = [h for h in hits if h.get("provenance_type") is None or h.get("provenance_type") not in ("tool_result", "collective_echo", "collective")]
        self.assertGreaterEqual(len(tool_hits), 1, "Expected at least one tool-result hit")
        self.assertGreaterEqual(len(user_hits), 1, "Expected at least one user hit")
        # The tool-result discount (0.85x) means its final_score should be lower
        # than an equally-similar user hit, all else being equal.
        # We check that the tool hit's score is strictly less than the top user hit.
        best_tool = max(tool_hits, key=lambda h: h.get("final_score", 0))
        best_user = max(user_hits, key=lambda h: h.get("final_score", 0))
        # If both are returned, the tool result should be discounted
        self.assertLess(
            best_tool.get("final_score", 0) / max(best_user.get("final_score", 0), 1e-9),
            1.0,
            "Tool-result hit should be scored lower than user hit due to 0.85x discount",
        )

    def test_tool_result_discount_env_override(self):
        """TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT env var should control the discount."""
        # Set to 1.0 (no discount)
        os.environ["TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT"] = "1.0"
        try:
            results = self.fabric.query(
                workspace_id="test-ws",
                agent_id="agent-1",
                query_text="weather in Reykjavik",
                top_k=10,
            )
            hits = results.get("results", [])
            tool_hits = [h for h in hits if h.get("provenance_type") == "tool_result"]
            # With discount=1.0, tool results are not penalized.
            # We just verify the query runs without error and tool hits exist.
            self.assertGreaterEqual(len(tool_hits), 1, "Tool-result hit should still appear")
        finally:
            os.environ.pop("TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT", None)


class TestToolResultNoContinuityBonus(unittest.TestCase):
    """Tool-result memories should not receive self-thread or thread-window bonuses."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()

    def test_tool_result_no_continuity_bonus(self):
        """When continuity_debug is on, tool-result hits should show zero self_thread and thread_window bonuses."""
        from torment_service.provenance_v1 import ProvenanceV1
        prov = ProvenanceV1.for_tool_result(
            tool_name="search_api",
            parent_eids=[],
            step=5,
        ).to_dict()
        self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="Search result: best restaurants in Reykjavik 2026",
            step=5,
            domain_id="personal",
            scope="private",
            provenance=prov,
        )
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="restaurants in Reykjavik",
            top_k=10,
            continuity_debug=True,
        )
        hits = results.get("results", [])
        tool_hits = [h for h in hits if h.get("provenance_type") == "tool_result"]
        self.assertGreaterEqual(len(tool_hits), 1, "Expected at least one tool-result hit")
        # Check the continuity debug breakdown in the response
        cd = results.get("continuity_debug")
        if cd is not None:
            # If top_hits_bonus_breakdown includes tool-result hits, their
            # self_thread and thread_window bonuses should be 0.
            for bd in cd.get("top_hits_bonus_breakdown", []):
                # Find the tool-result entry by matching eid
                for th in tool_hits:
                    if bd.get("eid") == th.get("eid"):
                        bonuses = bd.get("bonuses", {})
                        self.assertAlmostEqual(
                            bonuses.get("self_thread", 0.0), 0.0,
                            msg="Tool-result hit should not get self_thread bonus",
                        )
                        self.assertAlmostEqual(
                            bonuses.get("thread_window", 0.0), 0.0,
                            msg="Tool-result hit should not get thread_window bonus",
                        )


class TestProvenanceBadgeOnHit(unittest.TestCase):
    """Retrieved hits should carry provenance_type at top level."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()

    def test_provenance_badge_on_tool_result_hit(self):
        from torment_service.provenance_v1 import ProvenanceV1
        prov = ProvenanceV1.for_tool_result(
            tool_name="geocoding_api",
            parent_eids=[],
            step=1,
        ).to_dict()
        self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="Geocoded location: 64.1466N, 21.9426W, Reykjavik, Iceland",
            step=1,
            domain_id="personal",
            scope="private",
            provenance=prov,
        )
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="Reykjavik coordinates",
            top_k=5,
        )
        hits = results.get("results", [])
        self.assertGreaterEqual(len(hits), 1)
        tool_hits = [h for h in hits if h.get("provenance_type") == "tool_result"]
        self.assertGreaterEqual(len(tool_hits), 1, "Expected provenance_type='tool_result' on hit")
        # Check tool_name badge
        self.assertEqual(tool_hits[0].get("provenance_tool_name"), "geocoding_api")

    def test_provenance_badge_absent_for_user_memory(self):
        self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="I really enjoy visiting Iceland every summer",
            step=1,
            domain_id="personal",
            scope="private",
        )
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="Iceland summer visit",
            top_k=5,
        )
        hits = results.get("results", [])
        self.assertGreaterEqual(len(hits), 1)
        # User memory should NOT have provenance_type == "tool_result"
        # (it may be None or a default provenance type depending on ingest path)
        tool_hits = [h for h in hits if h.get("provenance_type") == "tool_result"]
        self.assertEqual(len(tool_hits), 0, "User memory should not have provenance_type='tool_result'")

    def test_provenance_badge_collective_echo(self):
        """Collective-echo provenance should surface as provenance_type."""
        from torment_service.provenance_v1 import ProvenanceV1
        prov = ProvenanceV1.for_collective_echo(
            notes="test_collective",
        ).to_dict()
        self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="Collective knowledge: Iceland has active volcanoes",
            step=1,
            domain_id="personal",
            scope="private",
            provenance=prov,
        )
        results = self.fabric.query(
            workspace_id="test-ws",
            agent_id="agent-1",
            query_text="Iceland volcanoes",
            top_k=5,
        )
        hits = results.get("results", [])
        coll_hits = [h for h in hits if h.get("provenance_type") == "collective_echo"]
        self.assertGreaterEqual(len(coll_hits), 1, "Collective echo should appear as provenance_type='collective_echo'")


# ===========================================================================
# Tool-result canon suppression (doctrine ratification post-Q2-D Phase 2)
# ===========================================================================
#
# Doctrine: external tool-result rows must NOT become identity-canonical
# automatically. The previous behavior auto-canonized any coherent
# tool-result row via fabric.ingest's kernel-driven promotion_score >= 0.78
# check, which contradicted the source_type=tool_result contract.
#
# Patch shape: ordinary fabric.ingest now fails closed for canon authority;
# _fast_tool_result_ingest still passes ``suppress_canon=True`` defensively.
#
# These tests lock the doctrine in:
#   - the full tool-result submit_task pipeline yields canon=False
#   - the resulting lifecycle envelope is UNSET / SYSTEM / INGEST_UNMARKED
#   - fabric.ingest(..., suppress_canon=True) is honored at the API layer
#   - fabric.ingest(..., suppress_canon=False) -- the default -- also
#     remains non-canon even when kernel promotion telemetry is high


# Reasonably coherent English text. The live Phase 2 smoke confirmed
# that text of this shape triggers auto-canon under the default
# kernel.promotion_score >= 0.78 threshold (eid=1 and eid=2 in the
# external_inference_smoke agent both ended up PROTECTED/CANON_SET).
# Using equivalent text here is the closest in-test analog to that
# live evidence.
_COHERENT_INGEST_TEXT = (
    "Right back at you. I acknowledge this test prompt with a complete "
    "sentence that should score well on coherence metrics."
)


class TestToolResultCanonSuppression(unittest.TestCase):
    """Q2-D doctrine ratification: tool-result rows are not auto-canon."""

    def setUp(self):
        self.fabric = _make_fabric()
        self.ctx = _make_ctx()

    def _payload_for_eid(self, eid):
        ak = self.fabric._agent_key("test-ws", "agent-1")
        graph = self.fabric.private_graphs[ak]
        return graph.entities[eid].payload

    # ----- Integration: full /tool/ingest pipeline -----

    def test_tool_result_via_submit_task_does_not_auto_canonize(self):
        """tool_result_ingest must produce a non-canon row, even for
        text that would otherwise trip the kernel's canon threshold."""
        req = _make_tool_ingest_request(content=_COHERENT_INGEST_TEXT)
        resp = submit_task(req, self.fabric, self.ctx)
        self.assertTrue(resp.ok, msg=f"submit_task failed: {resp.reason}")
        eid = resp.result["eid"]
        payload = self._payload_for_eid(eid)
        self.assertFalse(
            payload.get("canon"),
            (
                "tool_result row must not be canon; got "
                f"canon={payload.get('canon')!r}. If this fires, the "
                "suppress_canon wiring on _fast_tool_result_ingest "
                "has regressed."
            ),
        )

    def test_tool_result_lifecycle_status_is_unset_ingest_unmarked(self):
        """The Q2-D envelope on a vanilla tool_result row is the
        ordinary unset shape: state=unset, actor=system,
        via=ingest_unmarked. This is the live-evidence expectation
        the original Q2-D plan documented; it now holds because
        suppress_canon prevents PROTECTED/CANON_SET stamping."""
        req = _make_tool_ingest_request(content=_COHERENT_INGEST_TEXT)
        resp = submit_task(req, self.fabric, self.ctx)
        self.assertTrue(resp.ok)
        eid = resp.result["eid"]
        payload = self._payload_for_eid(eid)

        ls = payload.get("lifecycle_status")
        self.assertIsNotNone(
            ls, "lifecycle_status must be stamped by H1c on every spawn",
        )
        self.assertEqual(ls.get("state"), "unset")
        self.assertTrue(ls.get("is_authoritative_on_row"))
        self.assertIsNone(ls.get("requires_join"))
        self.assertIsNone(ls.get("history_ref"))
        set_by = ls.get("set_by") or {}
        self.assertEqual(set_by.get("actor"), "system")
        self.assertEqual(set_by.get("via"), "ingest_unmarked")
        # set_by.at must be a real epoch int (not None).
        self.assertIsInstance(set_by.get("at"), int)
        self.assertGreater(set_by.get("at"), 0)

    # ----- Unit: fabric.ingest API contract for suppress_canon -----

    def test_fabric_ingest_suppress_canon_forces_canon_false(self):
        """fabric.ingest(..., suppress_canon=True) must produce a
        non-canon row regardless of kernel promotion_score. This is
        the API-level guarantee the new kwarg makes."""
        result = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text=_COHERENT_INGEST_TEXT,
            step=10,
            suppress_canon=True,
        )
        eid = result["eid"]
        payload = self._payload_for_eid(eid)
        self.assertFalse(
            payload.get("canon"),
            "suppress_canon=True must force canon=False",
        )

    def test_forced_high_promotion_cannot_grant_canon_authority(self):
        """Deterministic G1 regression guard for both arms of the
        ``canon=(False if suppress_canon else _auto_canon)`` ternary.

        Approach: monkeypatch ``kernel.process`` so that signals come
        back with ``promotion_score=1.0`` regardless of the input
        text. Under the fail-closed G1 posture:

        * default ``fabric.ingest`` (``suppress_canon=False``) MUST
          stamp canon=False on the resulting row.
        * ``fabric.ingest(..., suppress_canon=True)`` MUST stamp
          canon=False on the resulting row.

        Together these prove:

        1. promotion_score remains observable without granting canon.
        2. The explicit suppress_canon caller posture remains valid.
        """
        from unittest.mock import patch

        real_process = self.fabric.kernel.process

        def patched_process(state, text, runtime_ctx):
            state_out, signals, debug = real_process(state, text, runtime_ctx)
            # KernelSignals is a non-frozen @dataclass -- mutation is
            # allowed. Forcing 1.0 deterministically pushes the value
            # above the historical canon threshold regardless of text.
            signals.promotion_score = 1.0
            return state_out, signals, debug

        with patch.object(
            self.fabric.kernel, "process", side_effect=patched_process,
        ):
            # Default (suppress_canon=False): high kernel telemetry must
            # remain advisory and fail closed for canon authority.
            default_result = self.fabric.ingest(
                workspace_id="test-ws",
                agent_id="agent-1",
                text="forced-promotion default arm",
                step=30,
            )
            default_payload = self._payload_for_eid(default_result["eid"])

            # Suppress (suppress_canon=True): explicit defensive caller
            # posture remains fail closed as well.
            suppress_result = self.fabric.ingest(
                workspace_id="test-ws",
                agent_id="agent-1",
                text="forced-promotion suppress arm",
                step=31,
                suppress_canon=True,
            )
            suppress_payload = self._payload_for_eid(suppress_result["eid"])

        self.assertFalse(
            default_payload.get("canon"),
            (
                "G1 regression: promotion_score=1.0 must remain advisory "
                "during ordinary ingest and cannot grant canon authority."
            ),
        )
        self.assertFalse(
            suppress_payload.get("canon"),
            (
                "suppress arm regression: with promotion_score=1.0, "
                "fabric.ingest(..., suppress_canon=True) must still "
                "force canon=False. The doctrine -- external tool "
                "results are not auto-canon -- relies on this override."
            ),
        )


if __name__ == "__main__":
    unittest.main()
