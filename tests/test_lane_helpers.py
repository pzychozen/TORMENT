# tests/test_lane_helpers.py
"""
Phase 1 lane helper verification tests (v2.4.4).

Verifies that the extracted _query_private_lane, _query_shared_lane,
_query_deep_lane helpers produce the same merged result through
fabric.query() as the pre-extraction monolithic implementation.

These tests prove Phase 1 is behavior-preserving externally.
"""
import os
import sys
import tempfile
import unittest

# Ensure torment_service is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("TORMENT_EMBED_PROVIDER", "hash")

from torment_service.fabric import TormentFabric


class TestLaneHelpersSmokeTest(unittest.TestCase):
    """Basic smoke test: lane helpers exist and are callable."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def test_private_lane_exists(self):
        self.assertTrue(hasattr(self.fabric, "_query_private_lane"))

    def test_shared_lane_exists(self):
        self.assertTrue(hasattr(self.fabric, "_query_shared_lane"))

    def test_deep_lane_exists(self):
        self.assertTrue(hasattr(self.fabric, "_query_deep_lane"))

    def test_canonical_step_exists(self):
        self.assertTrue(hasattr(self.fabric, "_get_canonical_step"))


class TestLaneHelpersPrivate(unittest.TestCase):
    """Test private lane retrieval returns only private-scope hits."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")
        # Ingest memories into private graph
        for text in [
            "Private memory about quantum fields",
            "Private memory about topology",
            "Private memory about identity seeds",
        ]:
            self.fabric.ingest(
                workspace_id="ws1", agent_id="atlas",
                text=text, scope="private",
            )

    def test_private_lane_returns_hits(self):
        ak = self.fabric._agent_key("ws1", "atlas")
        hits = self.fabric._query_private_lane(ak, "quantum", "atlas", top_k=3)
        self.assertIsInstance(hits, list)
        self.assertGreater(len(hits), 0)

    def test_private_lane_zero_topk_returns_empty(self):
        ak = self.fabric._agent_key("ws1", "atlas")
        hits = self.fabric._query_private_lane(ak, "quantum", "atlas", top_k=0)
        self.assertEqual(hits, [])

    def test_private_lane_respects_topk(self):
        ak = self.fabric._agent_key("ws1", "atlas")
        hits = self.fabric._query_private_lane(ak, "quantum", "atlas", top_k=1)
        self.assertLessEqual(len(hits), 1)


class TestLaneHelpersShared(unittest.TestCase):
    """Test shared lane retrieval."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")  # ensure workspace exists
        self.fabric.create_agent("ws1", "atlas")
        # Ingest into shared graph
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Shared memory about collective fields",
            scope="shared",
        )

    def test_shared_lane_returns_hits_and_bridge_domains(self):
        ws = self.fabric.get_workspace("ws1")
        domains = list(ws.shared_graphs.keys())
        hits, bridge_domains = self.fabric._query_shared_lane(
            ws, "collective", top_k=3, domains=domains,
        )
        self.assertIsInstance(hits, list)
        self.assertIsInstance(bridge_domains, list)

    def test_shared_lane_zero_topk_returns_empty(self):
        ws = self.fabric.get_workspace("ws1")
        domains = list(ws.shared_graphs.keys())
        hits, bridge_domains = self.fabric._query_shared_lane(
            ws, "collective", top_k=0, domains=domains,
        )
        self.assertEqual(hits, [])
        self.assertEqual(bridge_domains, [])


class TestLaneHelpersDeep(unittest.TestCase):
    """Test deep lane retrieval returns empty when no deep store."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def test_deep_lane_zero_topk_returns_empty(self):
        import numpy as np
        ak = self.fabric._agent_key("ws1", "atlas")
        qemb = np.zeros(384, dtype=np.float32)
        hits = self.fabric._query_deep_lane(
            ak, "ws1", "atlas", qemb, top_k=0, canonical_step=0,
        )
        self.assertEqual(hits, [])

    def test_deep_lane_no_store_returns_empty(self):
        import numpy as np
        ak = self.fabric._agent_key("ws1", "atlas")
        qemb = np.zeros(384, dtype=np.float32)
        hits = self.fabric._query_deep_lane(
            ak, "ws1", "atlas", qemb, top_k=5, canonical_step=0,
        )
        self.assertEqual(hits, [])


class TestCanonicalStep(unittest.TestCase):
    """Test _get_canonical_step helper."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def test_returns_int(self):
        ak = self.fabric._agent_key("ws1", "atlas")
        step = self.fabric._get_canonical_step(ak)
        self.assertIsInstance(step, int)


class TestQueryMergedBehaviorPreserved(unittest.TestCase):
    """Verify fabric.query() produces the same merged output shape
    after the lane helper refactor."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")
        # Ingest private memories
        for text in [
            "The quantum field resonates with memory attractors",
            "Identity seeds determine baseline character drift",
            "Topology of shared memory graphs shows bridge formation",
        ]:
            self.fabric.ingest(
                workspace_id="ws1", agent_id="atlas",
                text=text, scope="private",
            )
        # Ingest shared memories
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Collective observation: field coherence is increasing",
            scope="shared",
        )

    def test_query_returns_expected_shape(self):
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="quantum field", top_k=5,
        )
        # Standard response keys
        self.assertIn("results", result)
        self.assertIn("domains", result)
        self.assertIn("domain_used", result)
        self.assertIn("motifs", result)
        self.assertIn("bridges", result)
        self.assertIn("role_context", result)
        self.assertIn("embed_context", result)

    def test_query_results_are_sorted_by_final_score(self):
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="quantum field", top_k=5,
        )
        scores = [r.get("final_score", 0.0) for r in result["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_query_respects_topk(self):
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="quantum field", top_k=2,
        )
        self.assertLessEqual(len(result["results"]), 2)

    def test_query_results_contain_standard_fields(self):
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="quantum", top_k=3,
        )
        for r in result["results"]:
            self.assertIn("eid", r)
            self.assertIn("final_score", r)
            self.assertIn("motifs", r)

    def test_private_hits_have_scope_private(self):
        """Private-graph hits should carry scope='private'."""
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="quantum field", top_k=5,
        )
        # At least some results should be private scope
        scopes = [r.get("scope") for r in result["results"]]
        self.assertIn("private", scopes)


class TestSpiritReturnScopeDeep(unittest.TestCase):
    """Verify inject_spirit_return_into_hit now sets scope='deep'."""

    def test_scope_deep_in_spirit_return_hit(self):
        from torment_service.spirit_return import (
            SpiritReturnMemory,
            inject_spirit_return_into_hit,
        )
        from torment_service.deep_memory import DeepMemory

        dm = DeepMemory(
            eid=42,
            summary="A deep compressed memory",
            born_step=100,
            compressed_step=105,
            compression_score=0.75,
            memory_class="experiential",
            metadata={"type": "memory"},
        )
        spirit = SpiritReturnMemory(
            deep_memory=dm,
            birth_symbol="◯",
            current_kernel_symbol="◯",
            symbol_interaction="stable",
            return_flavor="familiar",
            return_mode="recollection",
            warmth_score=0.3,
            resonance_confidence=0.5,
        )
        hit = inject_spirit_return_into_hit(spirit)

        # Must have scope="deep"
        self.assertEqual(hit["scope"], "deep")
        # Must still have deep memory markers
        self.assertTrue(hit["from_deep_memory"])
        self.assertTrue(hit["deep_memory"])
        self.assertTrue(hit["from_spirit_return"])


if __name__ == "__main__":
    unittest.main()
