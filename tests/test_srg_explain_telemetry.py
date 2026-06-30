"""tests/test_srg_explain_telemetry.py — srg_active_modifiers explain field.

Focused coverage for the explain-only ``srg_active_modifiers`` diagnostic that
``query(..., explain=True)`` and ``trace()`` both surface. The field is derived
purely from the already-computed SRG multiplier values (``srg_same_band_bonus`` /
``srg_crystal_bonus`` / ``srg_heartbeat_bonus``); it reads no raw R and changes no
score / ranking / filter / write.

Note on surfaces: ``query()`` and ``trace()`` read the per-hit SRG payload from
different hit shapes in the EXISTING code (query reads ``hit['payload']['srg']``,
trace reads ``hit['srg']``). This slice does NOT change that — it only surfaces a
diagnostic derived from whatever multipliers each surface actually computed. So
the invariant tested per surface is: ``srg_active_modifiers`` equals the
stable-ordered subset of THAT surface's own non-neutral multipliers. Genuinely
active combined/single cases are demonstrated on ``trace()`` (which fires SRG for
the test's patched hits).

Asserts:
  * neutral case → ``[]`` (query and trace)
  * a single active modifier → matching single-element list (trace)
  * combined active modifiers → stable order
    ``["same_band", "crystal", "heartbeat_a"]`` (trace)
  * both surfaces expose the field, and each surface's list is exactly the
    stable-ordered subset of its OWN multiplier fields (derivation correctness)
  * no scoring drift: the SRG-on final_score equals the SRG-off final_score
    times the surfaced combined multiplier (the diagnostic list perturbs nothing)

Scope: tests-only. No production change. No service start. No endpoints.
No database/substrate. No provider. No memory writers.
"""
import os
import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric

_ORDER = ("same_band", "crystal", "heartbeat_a")
_BONUS_KEYS = {
    "same_band": "srg_same_band_bonus",
    "crystal": "srg_crystal_bonus",
    "heartbeat_a": "srg_heartbeat_bonus",
}


def _expected_from_multipliers(explain):
    """The stable-ordered subset implied by an explain dict's own multipliers."""
    return [name for name in _ORDER if explain.get(_BONUS_KEYS[name], 1.0) != 1.0]


class TestSRGExplainTelemetry(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_srg_explain_telemetry_")
        os.environ["TORMENT_SRG_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        os.environ.pop("TORMENT_SRG_ENABLE", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # -- helpers --------------------------------------------------------------
    def _ingest_with_srg(self, text, step, srg_payload):
        r = self.fabric.ingest(workspace_id="ws", agent_id="agent", text=text, step=step)
        eid = r["eid"]
        ak = self.fabric._agent_key("ws", "agent")
        pg = self.fabric.private_graphs.get(ak)
        if pg:
            ent = pg.entities.get(int(eid))
            if ent and ent.payload is not None:
                ent.payload["srg"] = srg_payload
        return eid

    def _query_explain(self, eid, query_text):
        q = self.fabric.query(
            workspace_id="ws", agent_id="agent",
            query_text=query_text, top_k=20, explain=True,
        )
        hit = next((h for h in q.get("results", []) if int(h.get("eid", -1)) == int(eid)), None)
        self.assertIsNotNone(hit, "query did not return the target hit")
        return hit["explain"], hit["final_score"]

    def _trace_explain(self, eid, query_text):
        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text=query_text, eids=[eid],
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)
        return items[0]["explain"], items[0]["final_score"]

    # -- neutral case → [] ----------------------------------------------------
    def test_neutral_modifiers_empty_query_and_trace(self):
        # SRG disabled at ingest (no SRG payload) and at read → no modifiers fire.
        self.fabric._srg_enable = False
        eid = self.fabric.ingest(workspace_id="ws", agent_id="agent",
                                 text="a plain memory about gardening tools", step=10)["eid"]
        q_explain, _ = self._query_explain(eid, "gardening tools")
        t_explain, _ = self._trace_explain(eid, "gardening tools")
        self.assertEqual(q_explain.get("srg_active_modifiers"), [])
        self.assertEqual(t_explain.get("srg_active_modifiers"), [])

    # -- single active modifier (trace fires SRG for patched hits) ------------
    def test_trace_single_crystal_modifier(self):
        eid = self._ingest_with_srg(
            "a crystal identity memory about who I am", step=10,
            srg_payload={"R_band": "X", "is_crystal": True, "heartbeat_class": "C"},
        )
        t_explain, _ = self._trace_explain(eid, "who I am")
        self.assertEqual(t_explain.get("srg_active_modifiers"), ["crystal"])

    # -- combined active modifiers → stable order (trace) ---------------------
    def test_trace_combined_modifiers_stable_order(self):
        eid = self._ingest_with_srg(
            "a special memory with every SRG property at once", step=10,
            srg_payload={"R_band": "A", "is_crystal": True, "heartbeat_class": "A"},
        )
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"
        t_explain, _ = self._trace_explain(eid, "special memory SRG")
        self.assertEqual(
            t_explain.get("srg_active_modifiers"),
            ["same_band", "crystal", "heartbeat_a"],
        )

    # -- both surfaces expose the field; each list matches its own multipliers -
    def test_both_surfaces_expose_and_derivation_consistent(self):
        eid = self._ingest_with_srg(
            "a memory with all SRG properties for derivation parity", step=10,
            srg_payload={"R_band": "A", "is_crystal": True, "heartbeat_class": "A"},
        )
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"

        q_explain, _ = self._query_explain(eid, "derivation parity SRG")
        t_explain, _ = self._trace_explain(eid, "derivation parity SRG")

        # both expose the field as a list
        self.assertIsInstance(q_explain.get("srg_active_modifiers"), list)
        self.assertIsInstance(t_explain.get("srg_active_modifiers"), list)
        # each surface's list is exactly the stable-ordered subset of ITS OWN
        # non-neutral multipliers (derivation correctness, surface-independent)
        self.assertEqual(
            q_explain["srg_active_modifiers"], _expected_from_multipliers(q_explain))
        self.assertEqual(
            t_explain["srg_active_modifiers"], _expected_from_multipliers(t_explain))
        # trace fires all three here → concrete stable-order check
        self.assertEqual(
            t_explain["srg_active_modifiers"], ["same_band", "crystal", "heartbeat_a"])

    # -- no scoring drift: diagnostic list does not perturb final_score -------
    def test_no_scoring_drift_from_modifiers(self):
        eid = self._ingest_with_srg(
            "a memory to prove the diagnostic does not change scoring", step=10,
            srg_payload={"R_band": "A", "is_crystal": True, "heartbeat_class": "A"},
        )
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"

        # SRG-off score first (no evolution side effects).
        self.fabric._srg_enable = False
        _, score_off = self._trace_explain(eid, "diagnostic scoring")

        # SRG-on score + the surfaced combined multiplier.
        self.fabric._srg_enable = True
        on_explain, score_on = self._trace_explain(eid, "diagnostic scoring")

        expected_mult = 1.08 * 1.05 * 1.03
        self.assertEqual(
            on_explain.get("srg_active_modifiers"),
            ["same_band", "crystal", "heartbeat_a"],
        )
        self.assertAlmostEqual(on_explain.get("srg_total_multiplier"), expected_mult, places=4)
        # final_score is exactly base × multiplier — the diagnostic list changed nothing
        self.assertAlmostEqual(score_on, score_off * expected_mult, delta=0.001)


if __name__ == "__main__":
    unittest.main()
