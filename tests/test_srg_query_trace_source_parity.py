"""tests/test_srg_query_trace_source_parity.py - query/trace SRG source parity.

Fix: query() previously read per-hit SRG from hit["payload"]["srg"], but
MemoryGraph.search() flattens entity payload into top-level hit fields, so stored
payload["srg"] surfaces as hit["srg"]. Ordinary private/shared hits therefore
missed SRG modifiers in query() while trace() (which reads hit["srg"]) saw them.

This slice normalizes both surfaces onto _effective_srg_source(hit) - prefer
top-level hit["srg"], fall back to nested hit["payload"]["srg"] - for SCORING and
explain ONLY. query()'s SRG breathing/writeback stays bound to the original nested
source so this fix does not newly activate any write.

Proves: source-selector precedence + nested fallback (unit); query(explain=True)
now sees SRG modifiers from an ordinary flattened hit; trace() unchanged and in
agreement with query on the same source; srg_active_modifiers parity; no scoring
drift beyond the intended SRG activation; and no new breathing writeback.

Scope: tests-only. No service start. No endpoints. No database/substrate.
No provider. No memory writers.
"""
import copy
import os
import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric, _effective_srg_source


class TestEffectiveSRGSourceUnit(unittest.TestCase):
    def test_prefers_top_level(self):
        top = {"R_band": "A", "is_crystal": True}
        hit = {"srg": top, "payload": {"srg": {"R_band": "Z"}}}
        self.assertIs(_effective_srg_source(hit), top)

    def test_falls_back_to_nested(self):
        nested = {"R_band": "B", "is_crystal": False}
        self.assertIs(_effective_srg_source({"payload": {"srg": nested}}), nested)

    def test_none_when_absent(self):
        self.assertIsNone(_effective_srg_source({}))
        self.assertIsNone(_effective_srg_source({"payload": {}}))

    def test_none_or_fallback_when_top_level_not_dict(self):
        self.assertIsNone(_effective_srg_source({"srg": "not-a-dict"}))
        nested = {"R_band": "C"}
        self.assertIs(
            _effective_srg_source({"srg": None, "payload": {"srg": nested}}), nested)


class TestQueryTraceSourceParity(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_srg_source_parity_")
        os.environ["TORMENT_SRG_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        os.environ.pop("TORMENT_SRG_ENABLE", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _ingest_with_srg(self, text, step, srg_payload):
        eid = self.fabric.ingest(workspace_id="ws", agent_id="agent", text=text, step=step)["eid"]
        ak = self.fabric._agent_key("ws", "agent")
        ent = self.fabric.private_graphs.get(ak).entities.get(int(eid))
        ent.payload["srg"] = srg_payload
        return eid, ent

    def _query_hit(self, eid, query_text):
        q = self.fabric.query(workspace_id="ws", agent_id="agent",
                              query_text=query_text, top_k=20, explain=True)
        hit = next((h for h in q.get("results", []) if int(h.get("eid", -1)) == int(eid)), None)
        self.assertIsNotNone(hit, "query did not return the target hit")
        return hit

    def _trace_item(self, eid, query_text):
        t = self.fabric.trace(workspace_id="ws", agent_id="agent",
                              query_text=query_text, eids=[eid])
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)
        return items[0]

    # core fix: an ordinary flattened hit (top-level srg, no nested payload) is now
    # seen by query() -- failing before, passing after.
    def test_query_sees_srg_from_flattened_top_level(self):
        eid, _ = self._ingest_with_srg(
            "an ordinary memory carrying crystal SRG state", step=10,
            srg_payload={"R_band": "X", "is_crystal": True, "heartbeat_class": "C"})
        hit = self._query_hit(eid, "crystal SRG state")
        # the retrieved hit carries SRG at the FLATTENED top level, not nested:
        # the old hit["payload"]["srg"] read would have found nothing here.
        self.assertIsInstance(hit.get("srg"), dict)
        self.assertIsNone(hit.get("payload"))
        explain = hit["explain"]
        self.assertAlmostEqual(explain["srg_crystal_bonus"], 1.05, places=4)
        self.assertEqual(explain["srg_active_modifiers"], ["crystal"])

    # query and trace agree on the same effective source (combined modifiers)
    def test_query_trace_modifier_parity_combined(self):
        eid, _ = self._ingest_with_srg(
            "a memory with all SRG properties for source parity", step=10,
            srg_payload={"R_band": "A", "is_crystal": True, "heartbeat_class": "A"})
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"
        q_explain = self._query_hit(eid, "all SRG properties source parity")["explain"]
        t_explain = self._trace_item(eid, "all SRG properties source parity")["explain"]
        expected = ["same_band", "crystal", "heartbeat_a"]
        self.assertEqual(q_explain["srg_active_modifiers"], expected)
        self.assertEqual(t_explain["srg_active_modifiers"], expected)
        for k in ("srg_same_band_bonus", "srg_crystal_bonus",
                  "srg_heartbeat_bonus", "srg_total_multiplier"):
            self.assertAlmostEqual(q_explain[k], t_explain[k], places=4)

    # trace behavior unchanged: top-level read still drives it
    def test_trace_behavior_unchanged(self):
        eid, _ = self._ingest_with_srg(
            "a memory used to confirm trace still reads top level", step=10,
            srg_payload={"R_band": "X", "is_crystal": True, "heartbeat_class": "C"})
        t_explain = self._trace_item(eid, "trace top level")["explain"]
        self.assertAlmostEqual(t_explain["srg_crystal_bonus"], 1.05, places=4)
        self.assertEqual(t_explain["srg_active_modifiers"], ["crystal"])

    # no scoring drift beyond the intended SRG activation
    def test_no_scoring_drift_beyond_intended_activation(self):
        eid, _ = self._ingest_with_srg(
            "a memory to bound query SRG scoring drift", step=10,
            srg_payload={"R_band": "A", "is_crystal": True, "heartbeat_class": "A"})
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"
        on_hit = self._query_hit(eid, "bound scoring drift")
        score_on = on_hit["final_score"]
        mult = on_hit["explain"]["srg_total_multiplier"]
        self.fabric._srg_enable = False
        score_off = self._query_hit(eid, "bound scoring drift")["final_score"]
        self.fabric._srg_enable = True
        self.assertAlmostEqual(mult, 1.08 * 1.05 * 1.03, places=4)
        self.assertAlmostEqual(score_on, score_off * mult, delta=0.001)

    # writeback HOLD: a flattened top-level-only hit triggers no breathing write
    def test_no_breathing_writeback_on_flattened_hit(self):
        eid, ent = self._ingest_with_srg(
            "a memory that must not be evolved by a query read", step=10,
            srg_payload={"R_band": "A", "is_crystal": True, "heartbeat_class": "A"})
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"
        before = copy.deepcopy(ent.payload["srg"])
        hit = self._query_hit(eid, "must not be evolved")
        # scoring DID fire (we read the source) ...
        self.assertEqual(hit["explain"]["srg_active_modifiers"],
                         ["same_band", "crystal", "heartbeat_a"])
        # ... but the stored SRG state is UNCHANGED (no breathing writeback).
        self.assertEqual(ent.payload["srg"], before)


if __name__ == "__main__":
    unittest.main()
