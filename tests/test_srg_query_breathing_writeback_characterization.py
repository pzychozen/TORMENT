"""tests/test_srg_query_breathing_writeback_characterization.py

Characterization lock for the SRG query() breathing/writeback BOUNDARY after
commit 80cbb07, which intentionally split SRG scoring/explain source
normalization from breathing/writeback authority:

  * scoring/explain reads _effective_srg_source(hit): prefer top-level
    hit["srg"] (MemoryGraph.search flattens entity payload into top-level
    fields), fall back to nested hit["payload"]["srg"].
  * breathing/writeback stays gated on the OLD nested hit["payload"]["srg"]
    source ONLY.

This pins the CURRENT behavior so a future change is a visible, intentional diff:
  1. ordinary flattened MemoryGraph.search() hits ACTIVATE SRG scoring/explain;
  2. those flattened hits do NOT activate breathing/writeback (the stored entity
     SRG state is left unchanged by the query read);
  3. a manually-shaped legacy nested hit["payload"]["srg"] STILL activates the
     existing breathing/writeback (and scoring independently follows the
     top-level source) -- proving the split is real;
  4. trace() is read-only for the same SRG state (never writes back);
  5. no provider call / endpoint / schema / model-output-to-memory path / new
     write authority is involved: the scoring selector is read-only and the only
     write is the pre-existing nested-gated SRG breathing writeback.

Scope: tests-only. No production change. No service start. No endpoints. No
provider. No database/substrate. No memory writers beyond the pre-existing SRG
breathing path characterized here. Test-local temp data, cleaned up in tearDown.
"""
import ast
import copy
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from torment_service.fabric import TormentFabric, _effective_srg_source

# All three SRG modifiers active when this is the scoring source + band matches.
_ACTIVE = {"R_band": "A", "is_crystal": True, "heartbeat_class": "A"}
# Neutral scoring source: wrong band, not crystal, not heartbeat-A -> no modifiers.
_NEUTRAL = {"R_band": "Z", "is_crystal": False, "heartbeat_class": "C"}

_ALLOWED_IMPORT_ROOTS = {
    "ast", "copy", "os", "shutil", "tempfile", "unittest", "pathlib",
    "torment_service",
}


class TestSRGQueryBreathingWritebackBoundary(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_srg_writeback_char_")
        os.environ["TORMENT_SRG_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")
        self.ak = self.fabric._agent_key("ws", "agent")

    def tearDown(self):
        os.environ.pop("TORMENT_SRG_ENABLE", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -- helpers --------------------------------------------------------------
    def _ingest(self, text, step=10):
        eid = self.fabric.ingest(workspace_id="ws", agent_id="agent", text=text, step=step)["eid"]
        ent = self.fabric.private_graphs.get(self.ak).entities.get(int(eid))
        return eid, ent

    def _query_hit(self, eid, query_text):
        q = self.fabric.query(workspace_id="ws", agent_id="agent",
                              query_text=query_text, top_k=20, explain=True)
        hit = next((h for h in q.get("results", []) if int(h.get("eid", -1)) == int(eid)), None)
        self.assertIsNotNone(hit, "query did not return the target hit")
        return hit

    # 1 + 2: flattened hit -> scoring/explain active, writeback inactive
    def test_flattened_hit_scores_but_does_not_writeback(self):
        eid, ent = self._ingest("an ordinary flattened SRG memory")
        ent.payload["srg"] = dict(_ACTIVE)                  # flattened top-level only
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"
        before = copy.deepcopy(ent.payload["srg"])

        hit = self._query_hit(eid, "ordinary flattened SRG memory")
        # flattened shape: top-level srg present, NO nested payload key
        self.assertIsInstance(hit.get("srg"), dict)
        self.assertIsNone(hit.get("payload"))
        # (1) scoring/explain ACTIVE from the top-level source
        self.assertEqual(hit["explain"]["srg_active_modifiers"],
                         ["same_band", "crystal", "heartbeat_a"])
        self.assertGreater(hit["explain"]["srg_total_multiplier"], 1.0)
        # (2) writeback INACTIVE: stored SRG state left unchanged by the query read
        self.assertEqual(ent.payload["srg"], before)

    # 3: manually-shaped legacy nested hit -> writeback STILL fires; scoring
    #    independently follows the top-level source (the split is real).
    def test_legacy_nested_hit_still_activates_writeback(self):
        eid, ent = self._ingest("a manually nested SRG memory")
        ent.payload["srg"] = dict(_NEUTRAL)                 # top-level scoring source (neutral)
        ent.payload["payload"] = {"srg": dict(_ACTIVE)}     # legacy nested writeback source (active)
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"
        before_top = copy.deepcopy(ent.payload["srg"])

        hit = self._query_hit(eid, "manually nested SRG memory")
        # the hit carries the manually-shaped nested payload
        self.assertIsInstance(hit.get("payload"), dict)
        self.assertEqual(hit["payload"].get("srg"), _ACTIVE)
        # scoring follows the TOP-LEVEL (neutral) source, NOT the nested one
        self.assertEqual(hit["explain"]["srg_active_modifiers"], [])
        # breathing/writeback fires from the NESTED source: stored SRG state changes
        self.assertNotEqual(ent.payload["srg"], before_top)

    # 4: trace() is read-only for the same SRG state (never writes back)
    def test_trace_is_read_only_for_srg_state(self):
        eid, ent = self._ingest("a memory traced read-only")
        ent.payload["srg"] = dict(_ACTIVE)
        ent.payload["payload"] = {"srg": dict(_ACTIVE)}     # even with a nested source present
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"
        before = copy.deepcopy(ent.payload["srg"])

        t = self.fabric.trace(workspace_id="ws", agent_id="agent",
                              query_text="traced read-only", eids=[eid])
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)
        # trace sees SRG (scoring/explain) from the top-level source ...
        self.assertEqual(items[0]["explain"]["srg_active_modifiers"],
                         ["same_band", "crystal", "heartbeat_a"])
        # ... but never writes back: stored SRG state unchanged
        self.assertEqual(ent.payload["srg"], before)

    # 5a: the scoring source selector is read-only (mutates nothing)
    def test_effective_srg_source_is_read_only(self):
        hit = {"srg": dict(_ACTIVE), "payload": {"srg": dict(_NEUTRAL)}}
        snapshot = copy.deepcopy(hit)
        src = _effective_srg_source(hit)
        self.assertIs(src, hit["srg"])          # top-level preferred
        self.assertEqual(hit, snapshot)         # selector mutated the hit not at all

    # 5b: this characterization touches no provider/endpoint/schema module
    def test_no_provider_or_endpoint_surface_imported(self):
        src = Path(__file__).read_text(encoding="utf-8")
        roots = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                for a in node.names:
                    roots.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertEqual(roots - _ALLOWED_IMPORT_ROOTS, set(),
                         "unexpected import roots in characterization test")


if __name__ == "__main__":
    unittest.main()
