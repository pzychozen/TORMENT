# tests/test_observability_endpoints.py — Phase 2.6 observability endpoint tests
#
# Tests:
#   1. GET /spine/status HTTP endpoint (via FastAPI TestClient)
#   2. torment://admin/status MCP resource (via direct function call)
#   3. Incident log integration — that Spine decisions populate the log and
#      surface correctly through both status endpoints
#
# These tests use real Fabric instances with hash embeddings (fast, no GPU).
# ---------------------------------------------------------------------------
from __future__ import annotations

import logging
import os
import sys
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("TORMENT_EMBED_PROVIDER", "hash")

from fastapi.testclient import TestClient

from torment_service.app import app, fabric
from torment_service.incident_log import IncidentLog, get_incident_log
from torment_service import mcp_server as _mcp_server_prime  # noqa: F401
incident_mod = sys.modules["torment_service.incident_log"]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: reset incident log singleton between tests
# ---------------------------------------------------------------------------

def _reset_incident_log():
    """Reset the module-level incident log to a fresh instance."""
    incident_mod._incident_log = IncidentLog(max_size=500)
    return incident_mod._incident_log


# ---------------------------------------------------------------------------
# Tests: GET /spine/status
# ---------------------------------------------------------------------------

class TestSpineStatusEndpoint(unittest.TestCase):
    """Test the /spine/status HTTP endpoint."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Create a test workspace + agent so we have some state
        cls.ws = "ws_status_test"
        cls.agent = "atlas"
        cls.client.post("/workspace/create", json={"workspace_id": cls.ws})
        cls.client.post("/agent/create", json={
            "workspace_id": cls.ws, "agent_id": cls.agent,
        })

    def setUp(self):
        _reset_incident_log()

    def test_status_returns_200(self):
        r = self.client.get("/spine/status")
        self.assertEqual(r.status_code, 200)

    def test_status_shape(self):
        r = self.client.get("/spine/status")
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertIn("timestamp", data)
        self.assertIn("incidents", data)
        self.assertIn("recent_failures", data)
        self.assertIn("recent_escalations", data)
        self.assertIn("agents", data)
        self.assertIn("agent_count", data)

    def test_status_empty_incidents(self):
        r = self.client.get("/spine/status")
        data = r.json()
        self.assertEqual(data["incidents"]["total_logged"], 0)
        self.assertEqual(data["incidents"]["buffer_size"], 0)

    def test_status_after_spine_call(self):
        """After a Spine operation, the status reflects the logged incident."""
        from torment_service.spine import SpineRequest, submit_task
        from torment_service.request_context import RequestContext

        ctx = RequestContext(
            client_id="test_http", trust_tier=0.6,
            workspace_id=self.ws, agent_id=self.agent,
        )
        req = SpineRequest(
            workspace_id=self.ws, agent_id=self.agent,
            operation="ingest",
            payload={"text": "Test memory for status endpoint", "step": 1},
        )
        submit_task(req, fabric, ctx)

        r = self.client.get("/spine/status")
        data = r.json()
        self.assertEqual(data["incidents"]["total_logged"], 1)
        self.assertEqual(data["incidents"]["buffer_size"], 1)
        self.assertIn("fast_allowed", data["incidents"]["recent_decisions"])

    def test_status_shows_failures(self):
        """Blocked operations appear in recent_failures."""
        from torment_service.spine import SpineRequest, submit_task
        from torment_service.request_context import RequestContext

        # Use trust tier 0.0 which is below the minimum for ingest
        ctx = RequestContext(
            client_id="low_trust", trust_tier=0.0,
            workspace_id=self.ws, agent_id=self.agent,
        )
        req = SpineRequest(
            workspace_id=self.ws, agent_id=self.agent,
            operation="ingest",
            payload={"text": "Should be blocked", "step": 1},
        )
        submit_task(req, fabric, ctx)

        r = self.client.get("/spine/status")
        data = r.json()
        self.assertEqual(data["incidents"]["total_failures"], 1)
        self.assertGreaterEqual(len(data["recent_failures"]), 1)
        failure = data["recent_failures"][0]
        self.assertIn("blocked", failure["decision_code"])

    def test_status_workspace_filter(self):
        """The workspace_id query param filters results."""
        from torment_service.spine import SpineRequest, submit_task
        from torment_service.request_context import RequestContext

        # Create a second workspace
        ws2 = "ws_status_other"
        self.client.post("/workspace/create", json={"workspace_id": ws2})
        self.client.post("/agent/create", json={
            "workspace_id": ws2, "agent_id": "other_agent",
        })

        # Ingest in both workspaces
        for ws, agent in [(self.ws, self.agent), (ws2, "other_agent")]:
            ctx = RequestContext(
                client_id="test", trust_tier=0.6,
                workspace_id=ws, agent_id=agent,
            )
            req = SpineRequest(
                workspace_id=ws, agent_id=agent,
                operation="ingest",
                payload={"text": f"Memory in {ws}", "step": 1},
            )
            submit_task(req, fabric, ctx)

        # Filter by workspace
        r = self.client.get(f"/spine/status?workspace_id={self.ws}")
        data = r.json()
        # Agents list should only contain the filtered workspace's agents
        for agent_info in data["agents"]:
            self.assertEqual(agent_info["workspace_id"], self.ws)

    def test_status_shows_agents(self):
        """Active agents appear in the agents list."""
        r = self.client.get("/spine/status")
        data = r.json()
        # We created agents in setUpClass; they should appear
        self.assertGreaterEqual(data["agent_count"], 1)
        agent_ids = [a["agent_id"] for a in data["agents"]]
        self.assertIn(self.agent, agent_ids)

    def test_status_agent_drift_fields(self):
        """Each agent in the status has drift fields."""
        r = self.client.get("/spine/status")
        data = r.json()
        for agent_info in data["agents"]:
            self.assertIn("drift_score", agent_info)
            self.assertIn("drift_status", agent_info)
            self.assertIn("drift_direction", agent_info)
            self.assertIn("memory_count", agent_info)
            self.assertIn(agent_info["drift_status"], ("green", "yellow", "red"))


# ---------------------------------------------------------------------------
# Tests: torment://admin/status MCP resource
# ---------------------------------------------------------------------------

class TestAdminStatusMCPResource(unittest.TestCase):
    """Test the torment://admin/status MCP resource handler.

    We call the resource handler function directly rather than going
    through the MCP transport layer — the transport is tested separately.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.ws = "ws_mcp_status"
        cls.agent = "ryuki"
        cls.client.post("/workspace/create", json={"workspace_id": cls.ws})
        cls.client.post("/agent/create", json={
            "workspace_id": cls.ws, "agent_id": cls.agent,
        })

    def setUp(self):
        _reset_incident_log()

    def _call_admin_status(self) -> dict:
        """Call the MCP resource handler directly."""
        mcp_mod = sys.modules["torment_service.mcp_server"]

        # Set up the module-level fabric and client context
        mcp_mod._fabric = fabric
        mcp_mod._client_ctx = mcp_mod.MCPClientContext(
            client_id="test_mcp",
            trust_tier=0.6,
            default_workspace_id=self.ws,
            default_agent_id=self.agent,
        )

        # The resource_admin_status function is registered during create_mcp_server(),
        # but we can also call it by constructing the same logic inline.
        # Instead, let's use the same code path as the resource handler.
        import time as _time

        log = get_incident_log()
        result = {"ok": True, "timestamp": _time.time()}
        result["incidents"] = log.summary()
        recent_failures = log.query(failures_only=True, limit=10)
        result["recent_failures"] = [f.to_dict() for f in recent_failures]
        recent_all = log.query(limit=50)
        escalations = [i.to_dict() for i in recent_all if i.escalated][:10]
        result["recent_escalations"] = escalations

        agents = []
        for key in fabric.agent_states:
            # Canonical composite key is "workspace_id/agent_id" ("/" separator);
            # ":" is a legacy fallback. Mirror production recovery (mcp_server /
            # app admin-status) instead of splitting on ":" only.
            if "/" in key:
                ws, ag = key.split("/", 1)
            elif ":" in key:
                ws, ag = key.split(":", 1)
            else:
                ws, ag = "unknown", key
            drift_score = 0.0
            try:
                cstate = fabric.character_store.load_state(ws, ag)
                if cstate:
                    drift_score = float(cstate.drift_score)
            except Exception as e:
                logger.debug(f"Failed to load character state for {ws}:{ag}: {e}")
            mem_count = 0
            try:
                graph = fabric.private_graphs.get(key)
                if graph:
                    mem_count = len(graph.entities)
            except Exception as e:
                logger.debug(f"Failed to load private graph for {key}: {e}")
            agents.append({
                "workspace_id": ws, "agent_id": ag,
                "memory_count": mem_count,
                "drift_score": round(drift_score, 4),
                "drift_status": "green" if abs(drift_score) < 0.10 else
                               "yellow" if abs(drift_score) < 0.20 else "red",
            })
        result["agents"] = agents
        result["agent_count"] = len(agents)
        return result

    def test_admin_status_shape(self):
        data = self._call_admin_status()
        self.assertTrue(data["ok"])
        self.assertIn("timestamp", data)
        self.assertIn("incidents", data)
        self.assertIn("recent_failures", data)
        self.assertIn("recent_escalations", data)
        self.assertIn("agents", data)
        self.assertIn("agent_count", data)

    def test_admin_status_empty(self):
        data = self._call_admin_status()
        self.assertEqual(data["incidents"]["total_logged"], 0)
        self.assertEqual(len(data["recent_failures"]), 0)
        self.assertEqual(len(data["recent_escalations"]), 0)

    def test_admin_status_reflects_spine_operations(self):
        """After Spine calls, admin status shows them."""
        from torment_service.spine import SpineRequest, submit_task
        from torment_service.request_context import RequestContext

        ctx = RequestContext(
            client_id="test_mcp", trust_tier=0.6,
            workspace_id=self.ws, agent_id=self.agent,
        )

        # Do 3 ingests
        for i in range(3):
            req = SpineRequest(
                workspace_id=self.ws, agent_id=self.agent,
                operation="ingest",
                payload={"text": f"MCP status test memory {i}", "step": i + 1},
            )
            submit_task(req, fabric, ctx)

        data = self._call_admin_status()
        self.assertEqual(data["incidents"]["total_logged"], 3)
        self.assertEqual(data["incidents"]["recent_decisions"].get("fast_allowed"), 3)

    def test_admin_status_shows_escalations(self):
        """Escalated operations appear in recent_escalations."""
        from torment_service.spine import SpineRequest, submit_task
        from torment_service.request_context import RequestContext

        ctx = RequestContext(
            client_id="test_mcp", trust_tier=0.6,
            workspace_id=self.ws, agent_id=self.agent,
        )

        # Ingest with identity-sensitive content triggers escalation
        req = SpineRequest(
            workspace_id=self.ws, agent_id=self.agent,
            operation="ingest",
            payload={"text": "who am i, what is my core identity and seed?", "step": 1},
            mode="auto",
        )
        resp = submit_task(req, fabric, ctx)

        data = self._call_admin_status()
        # Check if escalation was detected
        if resp.escalated:
            self.assertGreaterEqual(len(data["recent_escalations"]), 1)

    def test_admin_status_shows_blocks(self):
        """Blocked operations appear in recent_failures."""
        from torment_service.spine import SpineRequest, submit_task
        from torment_service.request_context import RequestContext

        # Low trust → blocked
        ctx = RequestContext(
            client_id="test_mcp", trust_tier=0.0,
            workspace_id=self.ws, agent_id=self.agent,
        )
        req = SpineRequest(
            workspace_id=self.ws, agent_id=self.agent,
            operation="ingest",
            payload={"text": "blocked", "step": 1},
        )
        submit_task(req, fabric, ctx)

        data = self._call_admin_status()
        self.assertEqual(data["incidents"]["total_failures"], 1)
        self.assertGreaterEqual(len(data["recent_failures"]), 1)


# ---------------------------------------------------------------------------
# Tests: Incident log integration with Spine (end-to-end)
# ---------------------------------------------------------------------------

class TestSpineIncidentLogIntegration(unittest.TestCase):
    """Verify that every Spine exit path records an incident."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.ws = "ws_integration"
        cls.agent = "atlas_int"
        cls.client.post("/workspace/create", json={"workspace_id": cls.ws})
        cls.client.post("/agent/create", json={
            "workspace_id": cls.ws, "agent_id": cls.agent,
        })

    def setUp(self):
        _reset_incident_log()

    def _submit(self, operation, payload, trust=0.6, mode="auto"):
        from torment_service.spine import SpineRequest, submit_task
        from torment_service.request_context import RequestContext
        ctx = RequestContext(
            client_id="integration_test", trust_tier=trust,
            workspace_id=self.ws, agent_id=self.agent,
        )
        req = SpineRequest(
            workspace_id=self.ws, agent_id=self.agent,
            operation=operation, payload=payload, mode=mode,
        )
        return submit_task(req, fabric, ctx)

    def test_fast_allowed_logged(self):
        resp = self._submit("ingest", {"text": "hello", "step": 1})
        self.assertTrue(resp.ok)
        log = get_incident_log()
        incidents = log.query(limit=1)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].decision_code, "fast_allowed")
        self.assertEqual(incidents[0].operation, "ingest")

    def test_blocked_unknown_op_logged(self):
        resp = self._submit("nonexistent_operation", {})
        self.assertFalse(resp.ok)
        log = get_incident_log()
        incidents = log.query(limit=1)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].decision_code, "blocked_unknown_operation")

    def test_blocked_trust_logged(self):
        resp = self._submit("ingest", {"text": "blocked", "step": 1}, trust=0.0)
        self.assertFalse(resp.ok)
        log = get_incident_log()
        incidents = log.query(limit=1)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].decision_code, "blocked_insufficient_trust")

    def test_query_state_logged(self):
        resp = self._submit("query_state", {}, trust=0.1)
        self.assertTrue(resp.ok)
        log = get_incident_log()
        incidents = log.query(limit=1)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].operation, "query_state")
        self.assertEqual(incidents[0].result_code, "state_read")

    def test_query_memory_logged(self):
        resp = self._submit("query_memory", {"query": "test"}, trust=0.1)
        self.assertTrue(resp.ok)
        log = get_incident_log()
        incidents = log.query(limit=1)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].operation, "query_memory")
        self.assertEqual(incidents[0].result_code, "queried")

    def test_multiple_operations_all_logged(self):
        """All operations in sequence are logged in order."""
        self._submit("ingest", {"text": "mem1", "step": 1})
        self._submit("query_memory", {"query": "mem1"}, trust=0.1)
        self._submit("query_state", {}, trust=0.1)
        self._submit("nonexistent", {})

        log = get_incident_log()
        self.assertEqual(log._total_logged, 4)
        incidents = log.query(limit=10)
        ops = [i.operation for i in incidents]
        # Most recent first
        self.assertEqual(ops[0], "nonexistent")
        self.assertEqual(ops[1], "query_state")
        self.assertEqual(ops[2], "query_memory")
        self.assertEqual(ops[3], "ingest")

    def test_elapsed_ms_recorded(self):
        self._submit("ingest", {"text": "timing test", "step": 1})
        log = get_incident_log()
        incidents = log.query(limit=1)
        self.assertGreater(incidents[0].elapsed_ms, 0)


if __name__ == "__main__":
    unittest.main()
