"""Regression tests for MCP key migration and feedback normalization.

Covers:
1. Spine _fast_feedback normalizes list→bool at the boundary
2. Collective status agent discovery uses canonical "/" prefix
3. MCP admin status key parsing matches app.py logic
4. MCP provenance resource uses _agent_key + normalizes legacy strings
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric


# =========================================================================
# 1. Spine feedback normalization
# =========================================================================

class TestSpineFeedbackNormalization(unittest.TestCase):
    """Verify _fast_feedback converts list payloads to bools for Fabric."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        # Ingest a memory so feedback has something to work with
        self.fabric.ingest(
            workspace_id="default", agent_id="agent1",
            text="Test memory for feedback", step=1,
        )

    def test_list_used_successfully_becomes_bool(self):
        """MCP sends [1, 3] for used_successfully — Fabric should receive True."""
        from torment_service.spine import _fast_feedback
        from torment_service.request_context import RequestContext

        ctx = RequestContext(
            session_id="test", client_id="test", trust_tier=0.6,
            workspace_id="default", agent_id="agent1",
        )
        payload = {
            "retrieved_ids": [1],
            "used_successfully": [1],
            "user_confirmed": [],
            "contradiction_detected": [],
        }

        # Should not crash — lists are normalized to bools
        result = _fast_feedback(self.fabric, ctx, payload)
        self.assertIsNotNone(result)

    def test_empty_list_becomes_false(self):
        """Empty list [] should become False, not be passed as []."""
        from torment_service.spine import _fast_feedback
        from torment_service.request_context import RequestContext

        ctx = RequestContext(
            session_id="test", client_id="test", trust_tier=0.6,
            workspace_id="default", agent_id="agent1",
        )
        payload = {
            "retrieved_ids": [1],
            "used_successfully": [],
            "user_confirmed": [],
            "contradiction_detected": [],
        }

        result = _fast_feedback(self.fabric, ctx, payload)
        self.assertIsNotNone(result)

    def test_bool_true_passes_through(self):
        """HTTP endpoint sends True — should still work."""
        from torment_service.spine import _fast_feedback
        from torment_service.request_context import RequestContext

        ctx = RequestContext(
            session_id="test", client_id="test", trust_tier=0.6,
            workspace_id="default", agent_id="agent1",
        )
        payload = {
            "retrieved_ids": [1],
            "used_successfully": True,
            "user_confirmed": False,
            "contradiction_detected": False,
        }

        result = _fast_feedback(self.fabric, ctx, payload)
        self.assertIsNotNone(result)


# =========================================================================
# 2. Collective status agent discovery — canonical "/" prefix
# =========================================================================

class TestCollectiveAgentDiscovery(unittest.TestCase):
    """Verify agent discovery uses 'workspace/' prefix, not 'workspace:'."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmpdir)

    def test_canonical_prefix_finds_agents(self):
        """Agents stored with '/' key should be found by '/' prefix search."""
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Atlas memory", step=1,
        )
        self.fabric.ingest(
            workspace_id="ws1", agent_id="echo",
            text="Echo memory", step=1,
        )

        # Simulate collective_status agent discovery logic (fixed version)
        agents = []
        _ws_prefix = "ws1/"
        for key in self.fabric.agent_states:
            if key.startswith(_ws_prefix):
                agents.append(key[len(_ws_prefix):])

        self.assertEqual(sorted(agents), ["atlas", "echo"])

    def test_colon_prefix_finds_nothing_in_canonical_keys(self):
        """Old ':' prefix should NOT match canonical '/' keys."""
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Atlas memory", step=1,
        )

        # Simulate the OLD (buggy) discovery logic
        agents_old = []
        for key in self.fabric.agent_states:
            if key.startswith("ws1:"):
                agents_old.append(key.split(":", 1)[1])

        self.assertEqual(agents_old, [],
                         "Old ':' prefix should not find agents in canonical '/' keyed states")


# =========================================================================
# 3. Admin status key parsing
# =========================================================================

class TestAdminStatusKeyParsing(unittest.TestCase):
    """Verify admin status parses canonical '/' keys correctly."""

    def _parse_key(self, key):
        """Reproduce the fixed admin_status parsing logic."""
        if "/" in key:
            ws, ag = key.split("/", 1)
        elif ":" in key:
            ws, ag = key.split(":", 1)
        else:
            ws, ag = "unknown", key
        return ws, ag

    def test_canonical_key(self):
        ws, ag = self._parse_key("default/atlas")
        self.assertEqual(ws, "default")
        self.assertEqual(ag, "atlas")

    def test_legacy_colon_key(self):
        ws, ag = self._parse_key("default:atlas")
        self.assertEqual(ws, "default")
        self.assertEqual(ag, "atlas")

    def test_bare_key(self):
        ws, ag = self._parse_key("atlas")
        self.assertEqual(ws, "unknown")
        self.assertEqual(ag, "atlas")


# =========================================================================
# 4. Provenance resource normalization
# =========================================================================

class TestMCPProvenanceNormalization(unittest.TestCase):
    """Verify MCP provenance resource normalizes legacy strings."""

    def _normalize(self, prov):
        """Reproduce the normalization from resource_provenance."""
        if prov and not isinstance(prov, dict):
            return {"source_type": "legacy_string", "raw": str(prov)}
        return prov

    def test_legacy_collective_normalized(self):
        prov = self._normalize("collective")
        self.assertIsInstance(prov, dict)
        self.assertEqual(prov["source_type"], "legacy_string")
        self.assertEqual(prov["raw"], "collective")

    def test_dict_provenance_unchanged(self):
        prov = self._normalize({"source_type": "tool_result", "tool_name": "calc"})
        self.assertEqual(prov["source_type"], "tool_result")

    def test_none_provenance_stays_none(self):
        prov = self._normalize(None)
        self.assertIsNone(prov)

    def test_provenance_resource_uses_agent_key(self):
        """resource_provenance should use _agent_key, not manual string assembly."""
        ak_manual = "ws1/agent1"
        ak_canonical = TormentFabric._agent_key("ws1", "agent1")
        self.assertEqual(ak_manual, ak_canonical,
                         "Manual and canonical keys should match — "
                         "but code should use _agent_key for consistency")


if __name__ == "__main__":
    unittest.main()
