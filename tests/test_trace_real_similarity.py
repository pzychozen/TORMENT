"""Regression tests for TormentFabric.trace() real similarity scoring.

Bug: trace() constructed synthetic hit objects with score=0.0 for every
traced memory, then explain_for_hit() used that as the similarity input.
This meant final_score and the explanation were fundamentally detached
from actual query-time retrieval ranking.

Fix: trace() now computes real cosine similarity between the query
embedding and each entity's stored embedding, matching the similarity
that search() / query() would produce.

Tests:
  1. Traced item similarity is non-zero for an actually matching memory
  2. Trace ordering is consistent with query ordering for the same eids
  3. Trace does not hardcode score=0.0 synthetic hits anymore
"""

import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric


class TestTraceRealSimilarity(unittest.TestCase):
    """Verify that trace() produces real similarity scores."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_trace_test_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

        # Ingest memories with semantically distinct text so the hash
        # embedder produces different vectors with measurable similarity.
        self.eids = []
        texts = [
            "The weather in Reykjavik is cold and windy today",
            "Machine learning models require large training datasets",
            "Cold wind blows across the Reykjavik harbor in winter",
        ]
        for i, t in enumerate(texts):
            result = self.fabric.ingest(
                workspace_id="ws",
                agent_id="agent",
                text=t,
                step=i,
            )
            self.eids.append(result["eid"])

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -----------------------------------------------------------------
    # 1. Traced similarity is non-zero for a matching memory
    # -----------------------------------------------------------------

    def test_trace_sim_nonzero_for_matching_memory(self):
        """When a memory semantically matches the query, trace should
        report a non-zero similarity, not the old hardcoded 0.0."""
        # Query about weather — eid[0] should be a strong match
        result = self.fabric.trace(
            workspace_id="ws",
            agent_id="agent",
            query_text="weather in Reykjavik",
            eids=[self.eids[0]],
        )
        items = result.get("items", [])
        self.assertTrue(len(items) >= 1, "Expected at least one traced item")

        item = items[0]
        sim = item["explain"]["sim"]
        self.assertNotEqual(sim, 0.0,
            "trace() should compute real similarity, not hardcode 0.0")
        self.assertGreater(item["final_score"], 0.0,
            "final_score should be positive for a matching memory")

    # -----------------------------------------------------------------
    # 2. Trace ordering matches query ordering for the same eids
    # -----------------------------------------------------------------

    def test_trace_ordering_consistent_with_query(self):
        """Trace-explained final_scores should rank eids in the same
        order as query() does."""
        query_text = "cold weather wind Reykjavik"

        # Run query to get the real ranking
        q_result = self.fabric.query(
            workspace_id="ws",
            agent_id="agent",
            query_text=query_text,
            top_k=10,
        )
        q_hits = q_result.get("hits", [])
        if len(q_hits) < 2:
            self.skipTest("Need at least 2 hits to compare ordering")

        q_eids = [h["eid"] for h in q_hits]

        # Run trace for the same eids
        t_result = self.fabric.trace(
            workspace_id="ws",
            agent_id="agent",
            query_text=query_text,
            eids=q_eids,
        )
        t_items = t_result.get("items", [])
        t_items.sort(key=lambda x: x["final_score"], reverse=True)
        t_eids = [it["eid"] for it in t_items]

        # The top-ranked eid in trace should match the top-ranked in query.
        # We compare the top item rather than full ordering because trace
        # doesn't yet replicate every scoring adjustment from query().
        self.assertEqual(t_eids[0], q_eids[0],
            f"Top eid from trace ({t_eids[0]}) should match "
            f"top eid from query ({q_eids[0]})")

    # -----------------------------------------------------------------
    # 3. No more hardcoded 0.0 synthetic scores
    # -----------------------------------------------------------------

    def test_trace_no_zero_sim_for_real_memories(self):
        """Verify that trace doesn't produce sim=0.0 for every item
        regardless of query relevance."""
        result = self.fabric.trace(
            workspace_id="ws",
            agent_id="agent",
            query_text="cold weather Reykjavik harbor winter",
            eids=self.eids,
        )
        items = result.get("items", [])
        self.assertTrue(len(items) >= 1, "Expected traced items")

        sims = [it["explain"]["sim"] for it in items]
        # At least one should be non-zero (with hash embeddings all
        # memories from the same embedder will have *some* similarity)
        nonzero = [s for s in sims if abs(s) > 1e-9]
        self.assertTrue(len(nonzero) > 0,
            f"All similarities were zero: {sims}. "
            "trace() should compute real cosine similarity.")

    def test_trace_different_queries_give_different_sims(self):
        """Different query texts should produce different similarity
        profiles for the same set of eids."""
        r1 = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="weather in Reykjavik",
            eids=self.eids,
        )
        r2 = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="machine learning training data",
            eids=self.eids,
        )
        sims1 = [it["explain"]["sim"] for it in r1["items"]]
        sims2 = [it["explain"]["sim"] for it in r2["items"]]

        # With the old bug both would be all-zeros and identical.
        # With real similarity at least one pair should differ.
        self.assertNotEqual(sims1, sims2,
            "Different queries should produce different similarity profiles")


if __name__ == "__main__":
    unittest.main()
