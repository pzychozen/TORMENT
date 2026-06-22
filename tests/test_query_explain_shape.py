"""Characterization lock for query().explain shape vs trace() decomposition.

This is a CHARACTERIZATION test (motion-keeper slice "D"), not a parity fix.
It pins the *current* shape of the per-hit ``explain`` dict returned by
``TormentFabric.query(..., explain=True)`` and documents — as an executable
invariant — that it is a STRICT SUBSET of the per-hit ``explain`` dict returned
by ``TormentFabric.trace(...)``.

Why this exists
---------------
``query()`` and ``trace()`` build their per-hit ``explain`` dict off the *same*
scoring contract (``score_hit``, identical static ``weights``), but ``trace()``
surfaces a far richer decomposition. Every field ``trace()`` exposes and
``query()`` omits is in fact already *computed* inside ``query()``'s scoring
loop (continuity bonuses, SRG multipliers, lane weight, post-score discounts) —
it is computed-then-discarded, not absent. A future "explain parity" slice would
surface those values; this test freezes today's asymmetry so that such a slice
becomes a *visible, intentional diff* against a pinned baseline rather than a
silent shape change.

This test locks SHAPE ONLY. It asserts nothing about scoring values, ranking,
or behavior, and it changes no production code. If a later authorized parity
slice adds fields to ``query().explain``, this test is expected to fail and be
updated *intentionally* as part of that slice.

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


# --- Pinned baseline: the CURRENT key set of query().explain ----------------
# Locked deliberately. A future parity slice that adds fields here must update
# this set as an explicit, reviewed change.
EXPECTED_QUERY_EXPLAIN_KEYS = frozenset({
    "sim",
    "strength",
    "recency_days",
    "motif_alignment",
    "contradiction_risk",
    "conflict_status",
    "conflict_penalty",
    "conflict_ids",
    "weights",
})

# --- Pinned baseline: the decomposition fields trace() surfaces that ---------
# query().explain omits (the documented one-directional gap). 16 fields here;
# ``provenance_type`` is the 17th gap element but is handled separately below
# because query() *does* compute it — it simply places it at the hit top level,
# not inside ``explain`` (a placement asymmetry, not an absence).
EXPECTED_TRACE_ONLY_DECOMPOSITION = frozenset({
    "collective_discount",
    "tool_result_discount",
    "self_thread_bonus",
    "self_anchor_bonus",
    "thread_window_bonus",
    "affect_match_bonus",
    "mood_drift_bonus",
    "mood_spiral_penalty",
    "continuity_total_adjustment",
    "srg_same_band_bonus",
    "srg_crystal_bonus",
    "srg_heartbeat_bonus",
    "srg_total_multiplier",
    "memory_plan_lane",
    "lane_weight",
    "lane_weight_applied",
})


class TestQueryExplainShape(unittest.TestCase):
    """Pin query().explain shape and its subset relationship to trace()."""

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

    # -- 1. lock current query().explain key set ------------------------------
    def test_query_explain_key_set_locked(self):
        """query().explain currently exposes exactly EXPECTED_QUERY_EXPLAIN_KEYS.

        This is the baseline lock. If it fails because keys were ADDED, a
        parity slice likely landed and this constant should be updated as a
        reviewed, intentional change.
        """
        q_explain = self._query_hit()["explain"]
        self.assertEqual(
            set(q_explain.keys()), set(EXPECTED_QUERY_EXPLAIN_KEYS),
            msg=(
                "query().explain key set drifted from the pinned baseline. "
                "If this is an intentional parity slice, update "
                "EXPECTED_QUERY_EXPLAIN_KEYS in the same change."
            ),
        )

    # -- 2. query().explain has nothing trace().explain lacks -----------------
    def test_query_explain_is_strict_subset_of_trace(self):
        """Every key in query().explain also appears in trace().explain, and
        trace() carries strictly more (proper subset)."""
        q_keys = set(self._query_hit()["explain"].keys())
        t_keys = set(self._trace_explain().keys())

        missing_from_trace = q_keys - t_keys
        self.assertEqual(
            missing_from_trace, set(),
            msg=f"query().explain has keys trace() lacks: {missing_from_trace}",
        )
        self.assertTrue(
            q_keys < t_keys,
            msg="query().explain should be a PROPER subset of trace().explain",
        )

    # -- 3. the trace-only decomposition gap is exactly the documented set ----
    def test_trace_only_decomposition_gap_is_exact(self):
        """The keys trace().explain adds over query().explain are exactly the
        16 documented decomposition fields plus provenance_type (placement
        asymmetry). Locks the gap so a future parity slice is a visible diff.
        """
        q_keys = set(self._query_hit()["explain"].keys())
        t_keys = set(self._trace_explain().keys())

        gap = t_keys - q_keys
        expected_gap = set(EXPECTED_TRACE_ONLY_DECOMPOSITION) | {"provenance_type"}
        self.assertEqual(
            gap, expected_gap,
            msg=(
                "trace-only decomposition gap drifted. Expected the 16 "
                "decomposition fields + provenance_type. Got: "
                f"{sorted(gap)}"
            ),
        )

    # -- 4. provenance_type placement asymmetry -------------------------------
    def test_provenance_type_placement_asymmetry(self):
        """provenance_type is computed on both surfaces, but query() places it
        at the hit top level while trace() places it inside explain. Documented
        as a placement asymmetry, not an absence."""
        hit = self._query_hit()
        q_explain = hit["explain"]
        t_explain = self._trace_explain()

        # trace: inside explain
        self.assertIn("provenance_type", t_explain)
        # query: NOT inside explain ...
        self.assertNotIn("provenance_type", q_explain)
        # ... but present at the hit top level
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
