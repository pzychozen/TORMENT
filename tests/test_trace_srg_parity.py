"""Regression tests for trace() SRG score-modifier parity with query().

Bug: query() applies three SRG post-score multipliers (same-band resonance
×1.08, crystal identity ×1.05, heartbeat class A ×1.03) but trace() did
not reflect any of them, causing trace explanations to understate scores
for SRG-enabled runs.

Fix: trace() now mirrors query()'s SRG multipliers (without breathing
evolution side effects) and surfaces srg_same_band_bonus, srg_crystal_bonus,
srg_heartbeat_bonus, and srg_total_multiplier in the explanation output.

Tests:
  1. Traced same-band SRG memory gets ×1.08 multiplier
  2. Traced crystal SRG memory gets ×1.05 multiplier
  3. Traced heartbeat class A SRG memory gets ×1.03 multiplier
  4. Combined SRG modifiers compose multiplicatively
  5. When SRG is disabled or no SRG payload, all SRG fields stay neutral
"""

import os
import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric


class TestTraceSRGParity(unittest.TestCase):
    """Verify that trace applies the same SRG score multipliers as query."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_trace_srg_")
        # Enable SRG for these tests
        os.environ["TORMENT_SRG_ENABLE"] = "1"
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        os.environ.pop("TORMENT_SRG_ENABLE", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _ingest_with_srg(self, text, step, srg_payload):
        """Ingest a memory and patch its entity with an SRG payload."""
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text=text, step=step,
        )
        eid = r["eid"]
        ak = self.fabric._agent_key("ws", "agent")
        pg = self.fabric.private_graphs.get(ak)
        if pg:
            ent = pg.entities.get(int(eid))
            if ent and ent.payload is not None:
                ent.payload["srg"] = srg_payload
        return eid

    # -----------------------------------------------------------------
    # 1. Same-band resonance: ×1.08
    # -----------------------------------------------------------------
    def test_same_band_bonus(self):
        """SRG memory with R_band matching _srg_last_ingest_band should
        receive ×1.08 multiplier in trace."""
        eid = self._ingest_with_srg(
            "Memory about resonance patterns",
            step=10,
            srg_payload={"R_band": "B", "is_crystal": False, "heartbeat_class": "C"},
        )
        # Set last ingest band AFTER ingest (ingest overwrites this attribute)
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "B"

        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="resonance patterns",
            eids=[eid],
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)

        explain = items[0].get("explain", {})
        self.assertAlmostEqual(explain.get("srg_same_band_bonus"), 1.08, places=4)
        self.assertAlmostEqual(explain.get("srg_crystal_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_heartbeat_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_total_multiplier"), 1.08, places=4)
        self.assertEqual(explain.get("srg_active_modifiers"), ["same_band"])

    # -----------------------------------------------------------------
    # 2. Crystal identity: ×1.05
    # -----------------------------------------------------------------
    def test_crystal_bonus(self):
        """SRG memory with is_crystal=True should receive ×1.05 in trace."""
        eid = self._ingest_with_srg(
            "Crystal identity memory about self-concept",
            step=10,
            srg_payload={"R_band": "X", "is_crystal": True, "heartbeat_class": "C"},
        )

        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="self-concept",
            eids=[eid],
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)

        explain = items[0].get("explain", {})
        self.assertAlmostEqual(explain.get("srg_same_band_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_crystal_bonus"), 1.05, places=4)
        self.assertAlmostEqual(explain.get("srg_heartbeat_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_total_multiplier"), 1.05, places=4)
        self.assertEqual(explain.get("srg_active_modifiers"), ["crystal"])

    # -----------------------------------------------------------------
    # 3. Heartbeat class A: ×1.03
    # -----------------------------------------------------------------
    def test_heartbeat_class_a_bonus(self):
        """SRG memory with heartbeat_class='A' should receive ×1.03."""
        eid = self._ingest_with_srg(
            "Deep slow heartbeat memory about stability",
            step=10,
            srg_payload={"R_band": "X", "is_crystal": False, "heartbeat_class": "A"},
        )

        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="stability",
            eids=[eid],
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)

        explain = items[0].get("explain", {})
        self.assertAlmostEqual(explain.get("srg_same_band_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_crystal_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_heartbeat_bonus"), 1.03, places=4)
        self.assertAlmostEqual(explain.get("srg_total_multiplier"), 1.03, places=4)
        self.assertEqual(explain.get("srg_active_modifiers"), ["heartbeat_a"])

    # -----------------------------------------------------------------
    # 4. Combined SRG modifiers compose multiplicatively
    # -----------------------------------------------------------------
    def test_combined_srg_modifiers(self):
        """All three SRG bonuses should compose: 1.08 × 1.05 × 1.03."""
        eid = self._ingest_with_srg(
            "Special memory with all SRG properties",
            step=10,
            srg_payload={"R_band": "A", "is_crystal": True, "heartbeat_class": "A"},
        )
        # Set last ingest band AFTER ingest
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"

        # Get score without SRG (disable temporarily)
        self.fabric._srg_enable = False
        t_no_srg = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="special memory",
            eids=[eid],
        )
        self.fabric._srg_enable = True

        # Get score with SRG
        t_srg = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="special memory",
            eids=[eid],
        )

        items_no = t_no_srg.get("items", [])
        items_yes = t_srg.get("items", [])
        self.assertGreaterEqual(len(items_no), 1)
        self.assertGreaterEqual(len(items_yes), 1)

        score_no = items_no[0]["final_score"]
        score_yes = items_yes[0]["final_score"]

        expected_mult = 1.08 * 1.05 * 1.03
        explain = items_yes[0].get("explain", {})
        self.assertAlmostEqual(
            explain.get("srg_total_multiplier"), expected_mult, places=4,
            msg=f"Combined SRG multiplier should be {expected_mult:.6f}",
        )
        # combined active modifiers must surface in stable order
        self.assertEqual(
            explain.get("srg_active_modifiers"),
            ["same_band", "crystal", "heartbeat_a"],
            msg="combined active SRG modifiers must use stable order",
        )

        # final_score should reflect the combined multiplier
        self.assertAlmostEqual(
            score_yes, score_no * expected_mult, delta=0.001,
            msg="SRG-enabled score should be base × combined multiplier",
        )

    # -----------------------------------------------------------------
    # 5. SRG disabled or no payload → neutral fields
    # -----------------------------------------------------------------
    def test_no_srg_neutral_fields(self):
        """When SRG is disabled or no SRG payload exists, all SRG
        explanation fields should be 1.0 (neutral)."""
        # Ingest with SRG disabled so no SRG payload is auto-created
        self.fabric._srg_enable = False
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Normal memory without SRG data",
            step=10,
        )
        eid = r["eid"]

        # Re-enable SRG for the trace call, but the memory has no srg payload
        self.fabric._srg_enable = True
        t = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="normal memory",
            eids=[eid],
        )
        items = t.get("items", [])
        self.assertGreaterEqual(len(items), 1)

        explain = items[0].get("explain", {})
        self.assertAlmostEqual(explain.get("srg_same_band_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_crystal_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_heartbeat_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain.get("srg_total_multiplier"), 1.0, places=4)
        self.assertEqual(explain.get("srg_active_modifiers"), [])

        # Also test with SRG explicitly disabled at trace time
        self.fabric._srg_enable = False
        eid2 = self._ingest_with_srg(
            "Memory with SRG payload but SRG disabled at trace",
            step=20,
            srg_payload={"R_band": "A", "is_crystal": True, "heartbeat_class": "A"},
        )
        self.fabric._srg_last_ingest_band_by_agent[("ws", "agent")] = "A"

        t2 = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="SRG disabled memory",
            eids=[eid2],
        )
        items2 = t2.get("items", [])
        self.assertGreaterEqual(len(items2), 1)

        explain2 = items2[0].get("explain", {})
        self.assertAlmostEqual(explain2.get("srg_same_band_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain2.get("srg_crystal_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain2.get("srg_heartbeat_bonus"), 1.0, places=4)
        self.assertAlmostEqual(explain2.get("srg_total_multiplier"), 1.0, places=4)
        self.assertEqual(explain2.get("srg_active_modifiers"), [])


if __name__ == "__main__":
    unittest.main()
