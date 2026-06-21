"""tests/test_srg_same_band_per_agent.py — SRG same-band scoring is per-agent.

Correctness fix: the SRG "same-band resonance" +8% bonus compares a retrieved
memory's ``R_band`` against the *last-ingested band of the querying agent*, keyed
by ``(workspace_id, agent_id)`` (same key discipline as the relational EMA).
Previously the last-ingest band was a single fabric-wide scalar, so one agent's
ingest could grant or deny another agent's same-band bonus inside a shared
``TormentFabric`` instance. The SRG enable flag, the 1.08 multiplier, and the
scoring formula are unchanged — only the key discipline.

Observability: ``trace()`` surfaces ``srg_same_band_bonus`` in its explain dict
(``query()`` applies the same multiplier to ``final_score`` but does not expose
the field), so these tests assert on trace and cross-check query/trace parity.
"""
import os
import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric


def _patch_band(fabric, ws, agent, eid, r_band):
    """Force a known SRG R_band onto an already-ingested private memory."""
    ak = fabric._agent_key(ws, agent)
    pg = fabric.private_graphs.get(ak)
    ent = pg.entities.get(int(eid)) if pg else None
    if ent and ent.payload is not None:
        ent.payload["srg"] = {"R_band": r_band, "is_crystal": False, "heartbeat_class": "C"}


def _same_band_bonus(trace_result):
    items = trace_result.get("items", [])
    assert items, "no trace items"
    return items[0].get("explain", {}).get("srg_same_band_bonus")


class TestSRGSameBandPerAgent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="torment_srg_per_agent_")
        os.environ["TORMENT_SRG_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "alice")
        self.fabric.create_agent("ws", "bob")

    def tearDown(self):
        os.environ.pop("TORMENT_SRG_ENABLE", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ingest(self, agent, text, step):
        return self.fabric.ingest(workspace_id="ws", agent_id=agent, text=text, step=step)["eid"]

    # 1. cross-agent isolation: another agent's ingest must not change my band.
    def test_other_agent_ingest_does_not_steal_my_same_band(self):
        eid_a = self._ingest("alice", "alice memory about resonance patterns", 10)
        _patch_band(self.fabric, "ws", "alice", eid_a, 5)
        self.fabric._srg_last_ingest_band_by_agent[("ws", "alice")] = 5

        t1 = self.fabric.trace(workspace_id="ws", agent_id="alice",
                               query_text="resonance patterns", eids=[eid_a])
        self.assertAlmostEqual(_same_band_bonus(t1), 1.08, places=4)

        # bob ingests with a DIFFERENT band — under the old fabric-wide scalar this
        # would overwrite the band alice's scoring reads; per-agent keying must not.
        self._ingest("bob", "bob memory about entirely other things", 11)
        self.fabric._srg_last_ingest_band_by_agent[("ws", "bob")] = 9

        t2 = self.fabric.trace(workspace_id="ws", agent_id="alice",
                               query_text="resonance patterns", eids=[eid_a])
        self.assertAlmostEqual(_same_band_bonus(t2), 1.08, places=4)
        # alice's band is untouched by bob's ingest.
        self.assertEqual(self.fabric._srg_last_ingest_band_by_agent[("ws", "alice")], 5)

    # 2. an agent with no prior ingest band gets no same-band bonus.
    def test_agent_without_band_gets_no_same_band_bonus(self):
        eid_a = self._ingest("alice", "alice memory about resonance patterns", 10)
        _patch_band(self.fabric, "ws", "alice", eid_a, 5)
        # Model "no prior ingest" for alice by clearing her key (a never-ingested
        # agent has no key at all → .get() returns None → no same-band bonus).
        self.fabric._srg_last_ingest_band_by_agent.pop(("ws", "alice"), None)
        self.assertIsNone(self.fabric._srg_last_ingest_band_by_agent.get(("ws", "alice")))

        t = self.fabric.trace(workspace_id="ws", agent_id="alice",
                              query_text="resonance patterns", eids=[eid_a])
        self.assertAlmostEqual(_same_band_bonus(t), 1.0, places=4)

    # 3. same agent still receives the existing same-band multiplier.
    def test_same_agent_gets_same_band_multiplier(self):
        eid_a = self._ingest("alice", "alice memory about resonance patterns", 10)
        _patch_band(self.fabric, "ws", "alice", eid_a, 5)
        self.fabric._srg_last_ingest_band_by_agent[("ws", "alice")] = 5
        t = self.fabric.trace(workspace_id="ws", agent_id="alice",
                              query_text="resonance patterns", eids=[eid_a])
        self.assertAlmostEqual(_same_band_bonus(t), 1.08, places=4)

    # 4. trace/query parity under per-agent keying.
    def test_trace_query_parity_same_band(self):
        eid_a = self._ingest("alice", "alice memory about resonance water survey", 10)
        _patch_band(self.fabric, "ws", "alice", eid_a, 5)
        self.fabric._srg_last_ingest_band_by_agent[("ws", "alice")] = 5

        q = self.fabric.query(workspace_id="ws", agent_id="alice",
                              query_text="resonance water survey", top_k=20)
        q_scores = {h["eid"]: h["final_score"] for h in q.get("results", [])}
        t = self.fabric.trace(workspace_id="ws", agent_id="alice",
                              query_text="resonance water survey", eids=[eid_a])
        t_scores = {it["eid"]: it["final_score"] for it in t.get("items", [])}
        self.assertIn(eid_a, q_scores)
        self.assertIn(eid_a, t_scores)
        # both apply the same per-agent same-band bonus → aligned final scores.
        self.assertAlmostEqual(q_scores[eid_a], t_scores[eid_a], delta=0.15)
        self.assertAlmostEqual(_same_band_bonus(t), 1.08, places=4)

    # 5. SRG-off: no per-agent band recorded, no bonus.
    def test_srg_off_is_neutral_and_tracks_no_band(self):
        os.environ["TORMENT_SRG_ENABLE"] = "0"
        tmp = tempfile.mkdtemp(prefix="torment_srg_off_")
        try:
            fab = TormentFabric(data_dir=tmp)
            fab.get_workspace("ws")
            fab.create_agent("ws", "alice")
            eid = fab.ingest(workspace_id="ws", agent_id="alice",
                             text="a plain memory without srg", step=10)["eid"]
            # SRG off → no per-agent band recorded at all.
            self.assertEqual(fab._srg_last_ingest_band_by_agent, {})
            t = fab.trace(workspace_id="ws", agent_id="alice",
                          query_text="plain memory", eids=[eid])
            items = t.get("items", [])
            self.assertGreaterEqual(len(items), 1)
            self.assertAlmostEqual(
                items[0].get("explain", {}).get("srg_same_band_bonus", 1.0), 1.0, places=4)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
