"""Regression tests for agent key consistency and provenance hardening.

Covers:
1. Same agent_id in two workspaces — no cross-contamination
2. Legacy string provenance does not crash /debug/provenance logic
3. spine_status key parsing handles /, :, and bare keys
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric


# =========================================================================
# 1. Agent key format — canonical _agent_key
# =========================================================================

class TestAgentKeyCanonical(unittest.TestCase):
    """Verify _agent_key produces workspace-scoped composite keys."""

    def test_agent_key_format(self):
        ak = TormentFabric._agent_key("ws1", "atlas")
        self.assertEqual(ak, "ws1/atlas")

    def test_same_agent_different_workspaces(self):
        """Same agent_id in two workspaces must produce different keys."""
        ak1 = TormentFabric._agent_key("workspace_a", "agent1")
        ak2 = TormentFabric._agent_key("workspace_b", "agent1")
        self.assertNotEqual(ak1, ak2)

    def test_key_contains_separator(self):
        """Key must use / separator, not : or ::."""
        ak = TormentFabric._agent_key("default", "test")
        self.assertIn("/", ak)
        self.assertNotIn("::", ak)


# =========================================================================
# 2. Cross-workspace isolation via Fabric
# =========================================================================

class TestCrossWorkspaceIsolation(unittest.TestCase):
    """Verify that two workspaces sharing an agent_id have isolated graphs."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmpdir)

    def test_ingest_isolation(self):
        """Ingest into ws_a/agent1 must not appear in ws_b/agent1."""
        # Ingest into workspace A
        self.fabric.ingest(
            workspace_id="ws_a", agent_id="agent1",
            text="Memory for workspace A", step=1,
        )
        # Ingest into workspace B
        self.fabric.ingest(
            workspace_id="ws_b", agent_id="agent1",
            text="Memory for workspace B", step=1,
        )

        # Verify isolation
        ak_a = TormentFabric._agent_key("ws_a", "agent1")
        ak_b = TormentFabric._agent_key("ws_b", "agent1")

        graph_a = self.fabric.private_graphs.get(ak_a)
        graph_b = self.fabric.private_graphs.get(ak_b)

        self.assertIsNotNone(graph_a, "Workspace A graph should exist")
        self.assertIsNotNone(graph_b, "Workspace B graph should exist")

        # Each should have exactly 1 memory
        self.assertEqual(len(graph_a.entities), 1)
        self.assertEqual(len(graph_b.entities), 1)

        # Content should differ (ingest stores text as "summary")
        text_a = list(graph_a.entities.values())[0].payload.get("summary", "")
        text_b = list(graph_b.entities.values())[0].payload.get("summary", "")
        self.assertIn("workspace A", text_a)
        self.assertIn("workspace B", text_b)

    def test_raw_agent_id_finds_nothing(self):
        """Looking up with bare agent_id (no workspace) should find nothing."""
        self.fabric.ingest(
            workspace_id="ws_a", agent_id="agent1",
            text="Memory for workspace A", step=1,
        )
        # Raw agent_id should NOT match the canonical key
        graph = self.fabric.private_graphs.get("agent1")
        self.assertIsNone(graph,
                          "Bare agent_id lookup should return None — "
                          "only workspace-qualified keys should match")


# =========================================================================
# 3. Legacy provenance string safety
# =========================================================================

class TestLegacyProvenanceSafety(unittest.TestCase):
    """Verify that legacy string provenance doesn't crash field access.

    As of the v2.4.x tactical provenance pass, legacy bare strings are no
    longer normalized to a synthetic 'legacy_string' source_type. They are
    normalized to SOURCE_MEMORY with the raw value preserved in `notes`, so
    the read-path vocabulary stays inside VALID_SOURCE_TYPES.
    """

    def _normalize(self, prov):
        """Reproduce the normalization logic from /debug/provenance."""
        if prov and not isinstance(prov, dict):
            _legacy_raw = str(prov)
            return {
                "source_type": "memory",  # SOURCE_MEMORY
                "notes": f"legacy_bare_string={_legacy_raw!r}",
            }
        return prov

    def test_legacy_string_provenance_normalization(self):
        """Legacy 'collective' string should be safe to call .get() on after normalization."""
        prov = self._normalize("collective")
        # Source type is now SOURCE_MEMORY — inside VALID_SOURCE_TYPES.
        self.assertEqual(prov.get("source_type"), "memory")
        # Raw value is preserved in notes for debugging.
        self.assertIn("collective", prov.get("notes", ""))
        self.assertIn("legacy_bare_string", prov.get("notes", ""))
        # Legacy pseudo-type is no longer emitted at read time.
        self.assertNotEqual(prov.get("source_type"), "legacy_string")
        self.assertNotIn("raw", prov)
        # Optional fields remain absent.
        self.assertIsNone(prov.get("source_role"))
        self.assertIsNone(prov.get("write_path"))

    def test_dict_provenance_unchanged(self):
        """Dict provenance should pass through without wrapping."""
        prov = self._normalize({"source_type": "tool_result", "write_path": "tool_ingest"})
        self.assertEqual(prov["source_type"], "tool_result")

    def test_none_provenance_safe(self):
        """None provenance should skip filters safely."""
        prov = self._normalize(None)
        self.assertIsNone(prov)


# =========================================================================
# 4. Spine status key parsing
# =========================================================================

class TestSpineStatusKeyParsing(unittest.TestCase):
    """Verify key parsing handles /, :, and bare keys."""

    def _parse_key(self, key):
        """Simulate the spine_status parsing logic."""
        if "/" in key:
            ws, ag = key.split("/", 1)
        elif ":" in key:
            ws, ag = key.split(":", 1)
        else:
            ws, ag = "unknown", key
        return ws, ag

    def test_canonical_slash_key(self):
        ws, ag = self._parse_key("default/atlas")
        self.assertEqual(ws, "default")
        self.assertEqual(ag, "atlas")

    def test_legacy_colon_key(self):
        ws, ag = self._parse_key("default:atlas")
        self.assertEqual(ws, "default")
        self.assertEqual(ag, "atlas")

    def test_bare_agent_id(self):
        ws, ag = self._parse_key("atlas")
        self.assertEqual(ws, "unknown")
        self.assertEqual(ag, "atlas")

    def test_agent_id_with_colon(self):
        """Agent ID containing colons after first split should stay intact."""
        ws, ag = self._parse_key("default:agent:with:colons")
        self.assertEqual(ws, "default")
        self.assertEqual(ag, "agent:with:colons")

    def test_workspace_with_slash_in_agent(self):
        """Only first / is split on — rest stays in agent_id."""
        ws, ag = self._parse_key("default/agent/subpath")
        self.assertEqual(ws, "default")
        self.assertEqual(ag, "agent/subpath")


if __name__ == "__main__":
    unittest.main()
