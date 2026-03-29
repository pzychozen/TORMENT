# test_mcp_server.py — Tests for TORMENT MCP v1 server
#
# Tests the MCP server components WITHOUT requiring an actual stdio transport.
# We test:
#   - MCPClientContext construction and RequestContext mapping
#   - Spine call helper (the authority path)
#   - Tool registration from exposure tier policy
#   - Resource handlers
#   - Exposure tier filtering (only exposed ops available via MCP)
# ---------------------------------------------------------------------------
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure the torment_fabric package root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("TORMENT_EMBED_PROVIDER", "hash")

from torment_service.mcp_server import (
    MCPClientContext,
    _spine_call,
    _get_fabric,
    _get_client_ctx,
    create_mcp_server,
)
from torment_service.spine import (
    get_exposed_operations,
    EXPOSURE_OPEN,
    EXPOSURE_GUARDED,
    OPERATION_REGISTRY,
)
from torment_service.request_context import RequestContext, TRUST_INGEST
from torment_service.fabric import TormentFabric

import torment_service.mcp_server as mcp_mod


class TestMCPClientContext(unittest.TestCase):
    """Test MCPClientContext dataclass and RequestContext mapping."""

    def test_default_context(self):
        ctx = MCPClientContext()
        self.assertEqual(ctx.client_id, "mcp_client")
        self.assertEqual(ctx.trust_tier, 0.6)
        self.assertEqual(ctx.transport, "stdio")
        self.assertTrue(ctx.session_id.startswith("mcp_"))

    def test_custom_context(self):
        ctx = MCPClientContext(
            client_id="test_client",
            trust_tier=0.9,
            default_workspace_id="ws1",
            default_agent_id="atlas",
            session_id="test_sess",
        )
        self.assertEqual(ctx.client_id, "test_client")
        self.assertEqual(ctx.trust_tier, 0.9)
        self.assertEqual(ctx.default_workspace_id, "ws1")
        self.assertEqual(ctx.default_agent_id, "atlas")
        self.assertEqual(ctx.session_id, "test_sess")

    def test_to_request_context_defaults(self):
        ctx = MCPClientContext(
            client_id="c1", trust_tier=0.6,
            default_workspace_id="ws1", default_agent_id="a1",
            session_id="s1",
        )
        rc = ctx.to_request_context()
        self.assertEqual(rc.client_id, "c1")
        self.assertEqual(rc.trust_tier, 0.6)
        self.assertEqual(rc.workspace_id, "ws1")
        self.assertEqual(rc.agent_id, "a1")
        self.assertEqual(rc.session_id, "s1")
        self.assertEqual(rc.metadata["transport"], "stdio")

    def test_to_request_context_overrides(self):
        ctx = MCPClientContext(
            client_id="c1", trust_tier=0.6,
            default_workspace_id="ws1", default_agent_id="a1",
        )
        rc = ctx.to_request_context(workspace_id="ws2", agent_id="a2")
        self.assertEqual(rc.workspace_id, "ws2")
        self.assertEqual(rc.agent_id, "a2")


class TestSpineCallIntegration(unittest.TestCase):
    """Test the _spine_call helper with a real Fabric."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        self.client = MCPClientContext(
            client_id="test", trust_tier=TRUST_INGEST,
            default_workspace_id="ws1", default_agent_id="atlas",
            session_id="test_sess",
        )

        # Inject into module globals
        mcp_mod._fabric = self.fabric
        mcp_mod._client_ctx = self.client

    def tearDown(self):
        mcp_mod._fabric = None
        mcp_mod._client_ctx = None

    def test_ingest_through_spine_call(self):
        result = _spine_call("ingest", {"text": "Hello MCP world", "step": 1})
        self.assertTrue(result["ok"])
        self.assertEqual(result["operation"], "ingest")
        self.assertEqual(result["decision_code"], "fast_allowed")
        self.assertEqual(result["result_code"], "stored")
        self.assertEqual(result["path"], "fast")

    def test_query_state_through_spine_call(self):
        result = _spine_call("query_state", {})
        self.assertTrue(result["ok"])
        self.assertEqual(result["result_code"], "state_read")
        self.assertIn("workspace_id", result["result"])
        self.assertIn("agent_id", result["result"])

    def test_query_memory_through_spine_call(self):
        # Ingest first
        _spine_call("ingest", {"text": "The sky is blue", "step": 1})
        # Then query
        result = _spine_call("query_memory", {"query": "sky color"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["result_code"], "queried")

    def test_feedback_through_spine_call(self):
        result = _spine_call("feedback", {
            "retrieved_ids": [],
            "used_successfully": [],
            "user_confirmed": [],
            "contradiction_detected": [],
        })
        self.assertTrue(result["ok"])
        self.assertEqual(result["result_code"], "reinforced")

    def test_workspace_override(self):
        result = _spine_call("query_state", {}, workspace_id="ws1", agent_id="atlas")
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["workspace_id"], "ws1")

    def test_trust_rejection(self):
        """Low-trust client should be blocked from high-trust ops."""
        self.client.trust_tier = 0.0  # read-only
        mcp_mod._client_ctx = self.client
        result = _spine_call("ingest", {"text": "should fail"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["decision_code"], "blocked_insufficient_trust")

    def test_missing_context_rejection(self):
        """Empty defaults + no explicit args should return blocked_mcp_missing_context."""
        self.client.default_workspace_id = ""
        self.client.default_agent_id = ""
        mcp_mod._client_ctx = self.client
        result = _spine_call("ingest", {"text": "no context"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["decision_code"], "blocked_mcp_missing_context")
        self.assertIn("workspace_id", result["reason"])
        self.assertIn("agent_id", result["reason"])

    def test_partial_missing_context(self):
        """Missing only workspace should report only workspace."""
        self.client.default_workspace_id = ""
        self.client.default_agent_id = "atlas"
        mcp_mod._client_ctx = self.client
        result = _spine_call("ingest", {"text": "partial"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["decision_code"], "blocked_mcp_missing_context")
        self.assertIn("workspace_id", result["reason"])
        self.assertNotIn("agent_id", result["reason"])


class TestMCPServerCreation(unittest.TestCase):
    """Test that create_mcp_server builds the right tool/resource surface."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        os.environ["TORMENT_MCP_DATA_DIR"] = self.tmp
        os.environ["TORMENT_MCP_EXPOSURE_TIER"] = "open"

        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("default")
        self.fabric.create_agent("default", "default")
        mcp_mod._fabric = self.fabric
        mcp_mod._client_ctx = MCPClientContext()

    def tearDown(self):
        mcp_mod._fabric = None
        mcp_mod._client_ctx = None
        for key in ("TORMENT_MCP_DATA_DIR", "TORMENT_MCP_EXPOSURE_TIER"):
            os.environ.pop(key, None)

    def test_server_creates_successfully(self):
        mcp = create_mcp_server()
        self.assertIsNotNone(mcp)

    def test_canonical_tool_registered(self):
        mcp = create_mcp_server()
        # The FastMCP stores tools internally — check via _tool_manager
        tool_names = set()
        if hasattr(mcp, '_tool_manager'):
            tool_names = set(mcp._tool_manager._tools.keys())
        self.assertIn("torment_submit_task", tool_names,
                      f"Expected torment_submit_task in tools: {tool_names}")

    def test_convenience_tools_registered(self):
        mcp = create_mcp_server()
        tool_names = set()
        if hasattr(mcp, '_tool_manager'):
            tool_names = set(mcp._tool_manager._tools.keys())
        expected = {"torment_ingest", "torment_query_memory", "torment_query_state",
                    "torment_feedback", "torment_reinforce"}
        for name in expected:
            self.assertIn(name, tool_names,
                          f"Expected {name} in tools: {tool_names}")

    def test_resources_registered(self):
        mcp = create_mcp_server()
        # Check resource templates
        resource_templates = set()
        if hasattr(mcp, '_resource_manager'):
            for tmpl in mcp._resource_manager._templates.values():
                resource_templates.add(tmpl.uri_template)
        expected_uris = {
            "torment://workspace/{workspace_id}/agent/{agent_id}/state",
            "torment://workspace/{workspace_id}/agent/{agent_id}/memory-summary",
            "torment://workspace/{workspace_id}/collective/status",
        }
        for uri in expected_uris:
            self.assertIn(uri, resource_templates,
                          f"Expected resource {uri} in templates: {resource_templates}")

    def test_tool_count_matches_tier1(self):
        """Should have 1 canonical + 5 convenience tools = 6 total."""
        mcp = create_mcp_server()
        tool_names = set()
        if hasattr(mcp, '_tool_manager'):
            tool_names = set(mcp._tool_manager._tools.keys())
        self.assertEqual(len(tool_names), 6,
                         f"Expected 6 tools (1 canonical + 5 convenience), got {len(tool_names)}: {tool_names}")


class TestExposureTierFiltering(unittest.TestCase):
    """Test that MCP only exposes operations matching the configured tier."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")
        mcp_mod._fabric = self.fabric
        mcp_mod._client_ctx = MCPClientContext(
            client_id="test", trust_tier=TRUST_INGEST,
            default_workspace_id="ws1", default_agent_id="atlas",
        )

    def tearDown(self):
        mcp_mod._fabric = None
        mcp_mod._client_ctx = None

    def test_tier1_only_exposes_open_ops(self):
        open_ops = get_exposed_operations(EXPOSURE_OPEN)
        self.assertEqual(len(open_ops), 5)
        self.assertIn("ingest", open_ops)
        self.assertIn("query_memory", open_ops)
        self.assertNotIn("collective_reingest", open_ops)
        self.assertNotIn("identity_rewrite", open_ops)

    def test_tier2_exposes_guarded_ops(self):
        guarded_ops = get_exposed_operations(EXPOSURE_GUARDED)
        self.assertIn("collective_reingest", guarded_ops)
        self.assertIn("cognition_run", guarded_ops)
        self.assertNotIn("identity_rewrite", guarded_ops)


class TestMCPResourceHandlers(unittest.TestCase):
    """Test resource handlers return valid data."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")
        mcp_mod._fabric = self.fabric
        mcp_mod._client_ctx = MCPClientContext(
            client_id="test", trust_tier=TRUST_INGEST,
            default_workspace_id="ws1", default_agent_id="atlas",
        )

    def tearDown(self):
        mcp_mod._fabric = None
        mcp_mod._client_ctx = None

    def test_agent_state_resource(self):
        """Agent state resource should return valid JSON."""
        result = _spine_call("query_state", {},
                             workspace_id="ws1", agent_id="atlas")
        self.assertTrue(result["ok"])
        self.assertIn("workspace_id", result["result"])

    def test_ingest_then_query_resource(self):
        """Ingest, then verify query resource returns data."""
        _spine_call("ingest", {"text": "MCP resource test", "step": 1},
                    workspace_id="ws1", agent_id="atlas")
        result = _spine_call("query_memory", {"query": "resource test"},
                             workspace_id="ws1", agent_id="atlas")
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
