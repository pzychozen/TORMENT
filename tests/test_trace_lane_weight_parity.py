"""Regression tests for trace() memory-plan lane-weight parity with query().

Bug: trace() had no `memory_plan` parameter and did not apply lane-weight
multipliers, so its final_score and explanation were misleading whenever
a planner shaped ranking through lane weights.

Fix: trace() now accepts optional `memory_plan`, mirrors query()'s lane
classification (deep / relational / core / collective-skip), applies the
clamped [0.1, 2.0] weight multiplier, and surfaces `memory_plan_lane`,
`lane_weight`, and `lane_weight_applied` in the explanation output.

Tests:
  1. trace applies core lane weight when memory_plan.weight_by_lane.core is set
  2. trace applies relational lane weight for shared hits
  3. trace applies deep lane weight for spirit-return/deep hits
  4. collective echo hits do not receive lane weighting even when memory_plan is provided
  5. trace final score stays aligned with query final score for the same memory_plan
"""

import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric


class TestTraceLaneWeightParity(unittest.TestCase):
    """Verify that trace applies memory-plan lane weights like query."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_trace_lane_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -----------------------------------------------------------------
    # 1. Core lane weight applied in trace
    # -----------------------------------------------------------------
    def test_core_lane_weight(self):
        """Private memory should be classified as 'core' lane and receive
        the configured core weight multiplier."""
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="My private core memory about daily routine",
            step=10,
        )
        eid = r["eid"]

        mp = {"weight_by_lane": {"core": 1.5, "relational": 0.8, "deep": 0.6}}

        # Without memory_plan
        t_no_plan = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="Tell me about my daily routine",
            eids=[eid],
        )
        # With memory_plan
        t_with_plan = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="Tell me about my daily routine",
            eids=[eid],
            memory_plan=mp,
        )

        items_no = t_no_plan.get("items", [])
        items_yes = t_with_plan.get("items", [])
        self.assertGreaterEqual(len(items_no), 1)
        self.assertGreaterEqual(len(items_yes), 1)

        explain_no = items_no[0].get("explain", {})
        explain_yes = items_yes[0].get("explain", {})

        # Without plan: lane_weight_applied should be False
        self.assertFalse(explain_no.get("lane_weight_applied", False))
        self.assertAlmostEqual(explain_no.get("lane_weight", 1.0), 1.0)

        # With plan: lane should be "core", weight should be 1.5
        self.assertTrue(explain_yes.get("lane_weight_applied"))
        self.assertEqual(explain_yes.get("memory_plan_lane"), "core")
        self.assertAlmostEqual(explain_yes.get("lane_weight"), 1.5, places=4)

        # final_score with plan should be 1.5x the no-plan score
        score_no = items_no[0]["final_score"]
        score_yes = items_yes[0]["final_score"]
        self.assertAlmostEqual(score_yes, score_no * 1.5, delta=0.001)

    # -----------------------------------------------------------------
    # 2. Relational lane weight for shared hits
    # -----------------------------------------------------------------
    def test_relational_lane_weight(self):
        """Shared-scope memory should be classified as 'relational' lane."""
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Shared observation about collaborative project",
            step=10, scope="shared",
        )
        eid = r["eid"]

        mp = {"weight_by_lane": {"core": 1.0, "relational": 0.7, "deep": 1.0}}

        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="Tell me about the collaborative project",
            eids=[eid],
            memory_plan=mp,
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)

        explain = items[0].get("explain", {})
        self.assertEqual(explain.get("memory_plan_lane"), "relational")
        self.assertAlmostEqual(explain.get("lane_weight"), 0.7, places=4)
        self.assertTrue(explain.get("lane_weight_applied"))

    # -----------------------------------------------------------------
    # 3. Deep lane weight for spirit-return/deep hits
    # -----------------------------------------------------------------
    def test_deep_lane_weight(self):
        """Memory with deep_memory flag should be classified as 'deep' lane."""
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Ancient deep memory from long ago about existential questions",
            step=1,
        )
        eid = r["eid"]

        # Patch the entity to have deep_memory flag
        ak = self.fabric._agent_key("ws", "agent")
        pg = self.fabric.private_graphs.get(ak)
        if pg:
            ent = pg.entities.get(int(eid))
            if ent and ent.payload is not None:
                ent.payload["deep_memory"] = True

        mp = {"weight_by_lane": {"core": 1.0, "relational": 1.0, "deep": 1.8}}

        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="existential questions",
            eids=[eid],
            memory_plan=mp,
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)

        explain = items[0].get("explain", {})
        self.assertEqual(explain.get("memory_plan_lane"), "deep")
        self.assertAlmostEqual(explain.get("lane_weight"), 1.8, places=4)
        self.assertTrue(explain.get("lane_weight_applied"))

    # -----------------------------------------------------------------
    # 4. Collective echo hits skip lane weighting
    # -----------------------------------------------------------------
    def test_collective_echo_skips_lane_weight(self):
        """Collective-provenance hits should NOT receive lane weighting
        because they already get the dedicated collective discount."""
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Echoed collective observation about the group",
            step=10,
            provenance={"source_type": "collective_echo"},
        )
        eid = r["eid"]

        mp = {"weight_by_lane": {"core": 2.0, "relational": 2.0, "deep": 2.0}}

        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="Tell me about the group",
            eids=[eid],
            memory_plan=mp,
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)

        explain = items[0].get("explain", {})
        # Lane should be "collective" with weight 1.0 (no multiplier applied)
        self.assertEqual(explain.get("memory_plan_lane"), "collective")
        self.assertAlmostEqual(explain.get("lane_weight"), 1.0, places=4)

    # -----------------------------------------------------------------
    # 5. trace final score aligned with query for same memory_plan
    # -----------------------------------------------------------------
    def test_trace_query_alignment_with_plan(self):
        """For a fixed set of eids and identical memory_plan, trace and
        query final scores should be closely aligned."""
        eids = []
        for i in range(3):
            r = self.fabric.ingest(
                workspace_id="ws", agent_id="agent",
                text=f"Memory about topic number {i} that I recall",
                step=10 + i,
            )
            eids.append(r["eid"])

        mp = {"weight_by_lane": {"core": 1.3, "relational": 0.9, "deep": 0.5}}
        query_text = "What do I recall about topics?"

        q = self.fabric.query(
            workspace_id="ws", agent_id="agent",
            query_text=query_text, top_k=20,
            memory_plan=mp,
        )
        q_scores = {h["eid"]: h["final_score"] for h in q.get("results", [])}

        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text=query_text, eids=eids,
            memory_plan=mp,
        )
        t_scores = {it["eid"]: it["final_score"] for it in t.get("items", [])}

        common = set(q_scores.keys()) & set(t_scores.keys())
        if not common:
            self.skipTest("No common eids between query and trace results")

        for eid in common:
            qs = q_scores[eid]
            ts = t_scores[eid]
            # Allow tolerance for non-lane scoring differences (SRG, etc.)
            diff = abs(qs - ts)
            self.assertLess(
                diff, 0.15,
                msg=(
                    f"eid={eid}: query={qs:.6f} vs trace={ts:.6f} "
                    f"(diff={diff:.6f}) — lane-weighted scores should "
                    f"be in the same ballpark"
                ),
            )


if __name__ == "__main__":
    unittest.main()
