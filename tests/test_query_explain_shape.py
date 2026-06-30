"""Parity lock for query().explain shape vs trace() decomposition.

This is a PARITY test. It pins the shape of the per-hit ``explain`` dict
returned by ``TormentFabric.query(..., explain=True)`` and asserts — as an
executable invariant — that it now exposes the SAME diagnostic decomposition
key set as the per-hit ``explain`` dict returned by ``TormentFabric.trace(...)``.

History
-------
``query()`` and ``trace()`` build their per-hit ``explain`` dict off the *same*
scoring contract (``score_hit``, identical static ``weights``). ``query()``
previously surfaced only a strict subset of trace()'s richer decomposition;
every omitted field was already *computed* inside query()'s scoring loop
(continuity bonuses, SRG multipliers, lane weight, post-score discounts) —
computed-then-discarded, not absent. The explain-parity slice surfaced those
already-computed values on ``query().explain`` as **diagnostic fields only**
(no change to ``final_score``, ranking, returned hits, filtering, MemoryPlan
behavior, SRG scoring, or any write path). This test pins that intentional
parity so any future drift in either direction is a *visible, reviewed* diff.

Source anchors (informational, at time of writing):
  * query().explain   — torment_service/fabric.py, ``if explain:`` block.
  * trace() explain    — torment_service/fabric.py, ``explain_for_hit`` return.

Scope: tests-only. No production change. No service start. No endpoints.
No database/substrate. No R-field. No participation-guidance. No Layer-1.
"""

import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric


# --- Pinned baseline: the parity key set of query().explain -----------------
# query().explain now mirrors trace().explain exactly. This is the intentional
# parity baseline; any added/removed field must update this set as an explicit,
# reviewed change.
EXPECTED_QUERY_EXPLAIN_KEYS = frozenset({
    # shared base decomposition
    "sim",
    "strength",
    "recency_days",
    "motif_alignment",
    "contradiction_risk",
    "weights",
    # conflict surface
    "conflict_status",
    "conflict_penalty",
    "conflict_ids",
    # post-score discounts
    "collective_discount",
    "tool_result_discount",
    # provenance placement (now inside explain, mirroring trace)
    "provenance_type",
    # continuity bonus decomposition
    "self_thread_bonus",
    "self_anchor_bonus",
    "thread_window_bonus",
    "affect_match_bonus",
    "mood_drift_bonus",
    "mood_spiral_penalty",
    "continuity_total_adjustment",
    # SRG multiplier decomposition
    "srg_same_band_bonus",
    "srg_crystal_bonus",
    "srg_heartbeat_bonus",
    "srg_total_multiplier",
    # memory-plan lane decomposition
    "memory_plan_lane",
    "lane_weight",
    "lane_weight_applied",
})


class TestQueryExplainShape(unittest.TestCase):
    """Pin query().explain shape and its parity with trace()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_query_explain_shape_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

        # One plain, shareable private memory is enough to exercise both
        # explain surfaces; the explain dict's KEY SET is data-independent
        # (both functions build a literal dict with all keys always present).
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="A private memory about my morning routine and coffee",
            step=10,
        )
        self.eid = r["eid"]
        self.query_text = "Tell me about my morning routine"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -- helpers --------------------------------------------------------------
    def _query_hit(self):
        q = self.fabric.query(
            workspace_id="ws", agent_id="agent",
            query_text=self.query_text, top_k=20,
            explain=True,
        )
        results = q.get("results", [])
        self.assertGreaterEqual(len(results), 1, "query returned no results")
        hit = next((h for h in results if int(h.get("eid", -1)) == int(self.eid)),
                   results[0])
        self.assertIn("explain", hit, "query hit is missing 'explain' surface")
        return hit

    def _trace_explain(self):
        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text=self.query_text, eids=[self.eid],
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1, "trace returned no items")
        item = items[0]
        self.assertIn("explain", item, "trace item is missing 'explain' surface")
        return item["explain"]

    # -- 1. lock the parity query().explain key set ---------------------------
    def test_query_explain_key_set_locked(self):
        """query().explain exposes exactly EXPECTED_QUERY_EXPLAIN_KEYS (the
        parity set). If this fails because keys changed, update the constant as
        a reviewed, intentional change in the same slice."""
        q_explain = self._query_hit()["explain"]
        self.assertEqual(
            set(q_explain.keys()), set(EXPECTED_QUERY_EXPLAIN_KEYS),
            msg=(
                "query().explain key set drifted from the pinned parity "
                "baseline. Update EXPECTED_QUERY_EXPLAIN_KEYS in the same change."
            ),
        )

    # -- 2. query().explain is at parity with trace().explain -----------------
    def test_query_explain_is_parity_with_trace(self):
        """query().explain and trace().explain now expose the SAME key set."""
        q_keys = set(self._query_hit()["explain"].keys())
        t_keys = set(self._trace_explain().keys())

        missing_from_query = t_keys - q_keys
        extra_in_query = q_keys - t_keys
        self.assertEqual(
            missing_from_query, set(),
            msg=f"query().explain is missing trace() fields: {sorted(missing_from_query)}",
        )
        self.assertEqual(
            extra_in_query, set(),
            msg=f"query().explain has fields trace() lacks: {sorted(extra_in_query)}",
        )
        self.assertEqual(q_keys, t_keys, msg="query()/trace() explain keys must be at parity")

    # -- 3. no trace-only decomposition gap remains ---------------------------
    def test_no_trace_only_decomposition_gap(self):
        """The previously-documented trace-only decomposition gap (the 16
        decomposition fields + provenance_type) is now closed: trace() exposes
        no explain key that query() omits."""
        q_keys = set(self._query_hit()["explain"].keys())
        t_keys = set(self._trace_explain().keys())

        gap = t_keys - q_keys
        self.assertEqual(
            gap, set(),
            msg=f"unexpected trace-only explain gap re-opened: {sorted(gap)}",
        )

    # -- 4. provenance_type now surfaced on both explain dicts ----------------
    def test_provenance_type_parity_and_top_level(self):
        """provenance_type is now inside BOTH query().explain and
        trace().explain (placement parity), and query() still also surfaces it
        at the hit top level (back-compat)."""
        hit = self._query_hit()
        q_explain = hit["explain"]
        t_explain = self._trace_explain()

        # parity: present inside both explain dicts
        self.assertIn("provenance_type", t_explain)
        self.assertIn("provenance_type", q_explain)
        # back-compat: query still surfaces it at the hit top level too
        self.assertIn(
            "provenance_type", hit,
            msg="query() should still surface provenance_type at hit top level",
        )

    # -- 5. shared scoring contract: identical static weights -----------------
    def test_shared_static_weights_parity(self):
        """Both surfaces expose the same static scoring weights dict — evidence
        they decompose the same underlying score_hit contract."""
        q_weights = self._query_hit()["explain"].get("weights")
        t_weights = self._trace_explain().get("weights")
        self.assertEqual(q_weights, t_weights)


if __name__ == "__main__":
    unittest.main()
