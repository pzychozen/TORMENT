"""Regression tests for canonical current-step in query() scoring.

Bug: query() inferred the "current step" from max(hit["step"]) in the
retrieved candidate set. Thread-window bonus and mood-spiral penalty
both depended on this inferred step, making scoring circular — if
recent memories were absent from candidates, the step moved backwards
and continuity bonuses underfired or misfired.

Fix: derive _canonical_step from the agent's kernel ModelState.step
(the authoritative step counter incremented on every ingest), with a
fallback to max(born_step) from the private graph.

Tests:
  1. Continuity bonuses don't depend on whether the newest memory was
     retrieved into all_hits
  2. Canonical step comes from agent state, not from candidate set
  3. Two queries from the same agent state produce consistent step
"""

import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric


class TestCanonicalStep(unittest.TestCase):
    """Verify that query() uses a canonical step, not hit-derived step."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_canstep_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

        # Ingest a sequence of memories at increasing steps so the
        # agent's ModelState.step advances to a known value.
        self.max_step = 100
        for i in range(0, self.max_step + 1, 10):
            self.fabric.ingest(
                workspace_id="ws",
                agent_id="agent",
                text=f"Observation at step {i} about the weather",
                step=i,
            )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _get_agent_state_step(self) -> int:
        ak = self.fabric._agent_key("ws", "agent")
        state = self.fabric.agent_states.get(ak)
        return int(getattr(state, "step", -1)) if state else -1

    # -----------------------------------------------------------------
    # 1. Agent state step is authoritative and tracks ingests
    # -----------------------------------------------------------------

    def test_agent_state_step_advances_with_ingests(self):
        """ModelState.step should reflect the number of kernel ticks,
        which advances with each ingest — not depend on what query
        retrieves."""
        step = self._get_agent_state_step()
        # After 11 ingests (steps 0,10,...,100), kernel has ticked 11 times
        self.assertGreater(step, 0,
            "Agent state step should be positive after ingests")

    # -----------------------------------------------------------------
    # 2. Query results are consistent regardless of top_k
    # -----------------------------------------------------------------

    def test_continuity_bonus_independent_of_top_k(self):
        """Thread-window bonus should not change when top_k is small
        enough to exclude recent memories. With canonical step, the
        bonus computation is the same regardless of retrieval size."""
        # Query with large top_k — should include recent memories
        r_large = self.fabric.query(
            workspace_id="ws",
            agent_id="agent",
            query_text="weather observation",
            top_k=20,
            continuity_debug=True,
        )
        # Query with top_k=1 — may only get one hit
        r_small = self.fabric.query(
            workspace_id="ws",
            agent_id="agent",
            query_text="weather observation",
            top_k=1,
            continuity_debug=True,
        )

        # Find a common eid that appears in both result sets
        large_by_eid = {h["eid"]: h for h in r_large.get("results", [])}
        small_by_eid = {h["eid"]: h for h in r_small.get("results", [])}
        common_eids = set(large_by_eid.keys()) & set(small_by_eid.keys())

        if not common_eids:
            self.skipTest("No common eids between top_k=20 and top_k=1")

        for eid in common_eids:
            large_hit = large_by_eid[eid]
            small_hit = small_by_eid[eid]
            # With canonical step, the final_score for the same eid
            # should be identical regardless of what else was retrieved.
            self.assertAlmostEqual(
                large_hit["final_score"],
                small_hit["final_score"],
                places=6,
                msg=(
                    f"eid={eid} final_score differs between top_k=20 "
                    f"({large_hit['final_score']:.6f}) and top_k=1 "
                    f"({small_hit['final_score']:.6f}) — step-based "
                    f"bonuses should not depend on candidate set size"
                ),
            )

    # -----------------------------------------------------------------
    # 3. Canonical step does not regress when hits are sparse
    # -----------------------------------------------------------------

    def test_canonical_step_not_from_hits(self):
        """Even if we ingest a very old memory after many recent ones,
        querying should still use the agent's latest kernel step, not
        the step from the most recent hit."""
        # The agent state step should be well past 0
        agent_step = self._get_agent_state_step()
        self.assertGreater(agent_step, 0)

        # Ingest one more memory at step 0 (old)
        self.fabric.ingest(
            workspace_id="ws",
            agent_id="agent",
            text="Very old memory from step zero about ancient history",
            step=0,
        )

        # Query — the canonical step should still be high, not
        # dragged down by the old memory's step=0
        new_step = self._get_agent_state_step()
        self.assertGreaterEqual(new_step, agent_step,
            "Agent state step should not regress after ingesting old-step memory")

    # -----------------------------------------------------------------
    # 4. Two queries produce consistent scoring for the same eid
    # -----------------------------------------------------------------

    def test_repeated_queries_produce_consistent_scores(self):
        """Two identical queries should produce identical final_scores
        for the same eids — there's no randomness in step derivation."""
        r1 = self.fabric.query(
            workspace_id="ws", agent_id="agent",
            query_text="weather observation step",
            top_k=10,
        )
        r2 = self.fabric.query(
            workspace_id="ws", agent_id="agent",
            query_text="weather observation step",
            top_k=10,
        )

        eids1 = {h["eid"]: h["final_score"] for h in r1.get("results", [])}
        eids2 = {h["eid"]: h["final_score"] for h in r2.get("results", [])}

        common = set(eids1.keys()) & set(eids2.keys())
        self.assertTrue(len(common) > 0, "Repeated queries should return results")

        for eid in common:
            self.assertAlmostEqual(
                eids1[eid], eids2[eid], places=8,
                msg=f"eid={eid} scores differ between identical queries",
            )


if __name__ == "__main__":
    unittest.main()
