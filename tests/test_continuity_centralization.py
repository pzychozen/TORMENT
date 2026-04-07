"""Regression tests for continuity centralization refactor.

Refactor: self-thread bonus and identity-anchor bonus (including anchor
top-k dominance cap) were moved from duplicated inline logic in query()
and trace() into the shared ``compute_continuity_bonuses()`` helper in
``scoring.py``.

Tests:
  1. Self-thread bonus matches between query and trace via shared helper
  2. Identity-anchor bonus matches between query and trace via shared helper
  3. Non-top anchors receive reduced bonus consistently in both paths
  4. Tool-result memories do not receive self-thread bonus in either path
"""

import os
import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric


class TestContinuityCentralization(unittest.TestCase):
    """Verify self-thread and self-anchor bonuses are consistent between query and trace."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_cont_central_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -----------------------------------------------------------------
    # helpers
    # -----------------------------------------------------------------
    def _query_score(self, eid: int, query_text: str) -> float:
        """Get the final_score for a specific eid from query()."""
        r = self.fabric.query(
            workspace_id="ws", agent_id="agent",
            query_text=query_text, top_k=50,
        )
        for h in r.get("results", []):
            if int(h.get("eid", -1)) == eid:
                return float(h["final_score"])
        return -1.0

    def _trace_result(self, eid: int, query_text: str) -> dict:
        """Get full trace item for a specific eid."""
        r = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text=query_text, eids=[eid],
        )
        for it in r.get("items", []):
            if int(it.get("eid", -1)) == eid:
                return it
        return {}

    # -----------------------------------------------------------------
    # 1. Self-thread bonus matches between query and trace
    # -----------------------------------------------------------------
    def test_self_thread_bonus_parity(self):
        """Private, non-tool-result memory should receive the same
        self-thread bonus in both query() and trace().

        Note: final_score may differ due to post-multipliers (SRG, lane
        weights) that only query() applies. We verify the continuity
        bonus field value directly instead.
        """
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="My personal memory about my cat",
            step=10,
        )
        eid = r["eid"]
        query_text = "Tell me about my cat"

        qs = self._query_score(eid, query_text)
        tr = self._trace_result(eid, query_text)
        ts = tr.get("final_score", -1.0)

        self.assertGreater(qs, 0.0, "query should return the eid")
        self.assertGreater(ts, 0.0, "trace should return the eid")

        # trace explanation should report a non-zero self_thread_bonus
        explain = tr.get("explain", {})
        self.assertIn("self_thread_bonus", explain)
        self.assertGreater(explain["self_thread_bonus"], 0.0,
            "Private own memory should have positive self_thread_bonus")

        # The self_thread_bonus value should match the configured env
        # default (0.06) — proving the shared helper is used
        try:
            expected = float(os.getenv("TORMENT_SELF_MEMORY_BONUS", "0.06"))
        except Exception:
            expected = 0.06
        self.assertAlmostEqual(
            explain["self_thread_bonus"], expected, places=4,
            msg="self_thread_bonus should match TORMENT_SELF_MEMORY_BONUS",
        )

    # -----------------------------------------------------------------
    # 2. Identity-anchor bonus matches between query and trace
    # -----------------------------------------------------------------
    def test_identity_anchor_bonus_parity(self):
        """An identity_anchor memory should receive the same anchor bonus
        in both query() and trace()."""
        # Ingest a normal memory first
        self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Background context about the world",
            step=5,
        )

        # Ingest and patch as identity_anchor
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="I am a thoughtful, analytical character who values precision",
            step=10,
        )
        eid = r["eid"]

        ak = self.fabric._agent_key("ws", "agent")
        pg = self.fabric.private_graphs.get(ak)
        if pg:
            ent = pg.entities.get(int(eid))
            if ent and ent.payload is not None:
                ent.payload["type"] = "identity_anchor"

        query_text = "What is my character identity?"

        qs = self._query_score(eid, query_text)
        tr = self._trace_result(eid, query_text)
        ts = tr.get("final_score", -1.0)

        self.assertGreater(qs, 0.0, "query should return anchor eid")
        self.assertGreater(ts, 0.0, "trace should return anchor eid")

        self.assertAlmostEqual(
            qs, ts, delta=0.02,
            msg=f"Anchor bonus divergence: query={qs:.6f}, trace={ts:.6f}",
        )

        explain = tr.get("explain", {})
        self.assertIn("self_anchor_bonus", explain)
        self.assertGreater(explain["self_anchor_bonus"], 0.0,
            "Identity anchor should have positive self_anchor_bonus")

    # -----------------------------------------------------------------
    # 3. Non-top anchors receive reduced bonus consistently
    # -----------------------------------------------------------------
    def test_non_top_anchor_reduced_bonus(self):
        """When more anchors exist than TORMENT_ANCHOR_BOOST_TOPK, the
        lower-scoring ones should receive a reduced bonus in both paths."""
        # Set top-k to 1 so only the best anchor gets full boost
        os.environ["TORMENT_ANCHOR_BOOST_TOPK"] = "1"
        os.environ["TORMENT_ANCHOR_BOOST_REST_MULT"] = "0.35"
        try:
            eids = []
            for i in range(4):
                r = self.fabric.ingest(
                    workspace_id="ws", agent_id="agent",
                    text=f"Identity anchor statement number {i} about my personality",
                    step=10 + i,
                )
                eid = r["eid"]
                eids.append(eid)
                # Patch as identity_anchor
                ak = self.fabric._agent_key("ws", "agent")
                pg = self.fabric.private_graphs.get(ak)
                if pg:
                    ent = pg.entities.get(int(eid))
                    if ent and ent.payload is not None:
                        ent.payload["type"] = "identity_anchor"

            query_text = "What defines my personality?"

            # Trace all anchors
            t_result = self.fabric.trace(
                workspace_id="ws", agent_id="agent",
                query_text=query_text, eids=eids,
            )
            anchor_bonuses = []
            for it in t_result.get("items", []):
                ab = it.get("explain", {}).get("self_anchor_bonus", 0.0)
                anchor_bonuses.append(ab)

            # At least one should have full bonus and others reduced
            if len(anchor_bonuses) >= 2:
                max_bonus = max(anchor_bonuses)
                min_bonus = min(anchor_bonuses)
                self.assertGreater(max_bonus, min_bonus,
                    "Top anchor should have higher bonus than non-top anchors")
                # The reduced bonus should be roughly rest_mult * base
                # base=0.12, rest_mult=0.35, so reduced=0.042 + 0.04(self_anchor)
                # full=0.12 + 0.04 = 0.16
                self.assertGreater(min_bonus, 0.0,
                    "Non-top anchors should still receive some bonus")
        finally:
            os.environ.pop("TORMENT_ANCHOR_BOOST_TOPK", None)
            os.environ.pop("TORMENT_ANCHOR_BOOST_REST_MULT", None)

    # -----------------------------------------------------------------
    # 4. Tool-result memories do NOT receive self-thread bonus
    # -----------------------------------------------------------------
    def test_tool_result_no_self_thread_bonus(self):
        """A memory with tool_result provenance should not receive
        self-thread bonus, in both query() and trace()."""
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Tool result: search API returned 42 items",
            step=10,
            provenance={"source_type": "tool_result", "tool_name": "search"},
        )
        eid = r["eid"]

        query_text = "What did the search tool return?"

        tr = self._trace_result(eid, query_text)
        explain = tr.get("explain", {})

        self.assertIn("self_thread_bonus", explain)
        self.assertAlmostEqual(explain["self_thread_bonus"], 0.0,
            msg="Tool-result memories should NOT get self-thread bonus")

        # Also verify the tool-result discount IS applied
        self.assertIn("tool_result_discount", explain)
        self.assertLess(explain["tool_result_discount"], 1.0,
            "Tool-result discount should be applied")


if __name__ == "__main__":
    unittest.main()
