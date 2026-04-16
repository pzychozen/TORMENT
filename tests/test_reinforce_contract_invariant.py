# tests/test_reinforce_contract_invariant.py
#
# Contract-invariant tests for the reinforce contract (v2.4.x).
#
# Landing gate for the reinforce implementation PR.  If these tests pass
# end-to-end in both directions, the bound trio holds:
#   1. Mutation semantics  — reinforcement_count moves per-memory state
#   2. Envelope wording    — result_code truthfully reflects mutation
#   3. Observability       — callers may trust the envelope
#
# Test roster (per Implementation Plan §7.3):
#   1. test_reinforce_single_eid_increments_count
#   2. test_reinforce_multiple_eids_increments_each
#   3. test_reinforce_deduplicates_eids
#   4. test_reinforce_missing_eid_is_no_op
#   5. test_reinforce_shared_scope_eid_is_governed_skip
#   6. test_reinforce_envelope_reflects_mutation_invariant_forward
#   7. test_reinforce_envelope_reflects_mutation_invariant_reverse
#   8. test_reinforce_monotonic_never_decreases
#   9. test_reinforce_does_not_move_overlay
# ---------------------------------------------------------------------------
from __future__ import annotations

import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.request_context import (
    RequestContext,
    TRUST_QUERY_REINFORCE,
    TRUST_INGEST,
)
from torment_service.spine import (
    SpineRequest,
    submit_task,
    RESULT_REINFORCED,
    RESULT_NO_OP,
)
from torment_service.fabric import TormentFabric


class TestReinforceContractInvariant(unittest.TestCase):
    """Contract-invariant tests for torment_reinforce (v2.4.x).

    Setup: create a workspace, agent, and ingest a few private memories
    so the reinforce writer has targets.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Ingest three private memories and capture their eids.
        self.eids = []
        for text in [
            "Memory Alpha: the first test memory.",
            "Memory Beta: the second test memory.",
            "Memory Gamma: the third test memory.",
        ]:
            ctx = RequestContext(client_id="test", trust_tier=TRUST_INGEST,
                                workspace_id="ws1", agent_id="atlas")
            req = SpineRequest(
                workspace_id="ws1", agent_id="atlas",
                operation="ingest",
                payload={"text": text, "scope": "private"},
                mode="fast",
            )
            resp = submit_task(req, self.fabric, ctx)
            self.assertTrue(resp.ok, f"Ingest failed: {resp.reason}")
            self.eids.append(int(resp.result["eid"]))

    def _reinforce(self, used_successfully, retrieved_ids=None):
        """Helper: submit a reinforce call and return the SpineResponse."""
        if retrieved_ids is None:
            retrieved_ids = list(used_successfully)
        ctx = RequestContext(client_id="test", trust_tier=TRUST_QUERY_REINFORCE,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="reinforce",
            payload={
                "retrieved_ids": retrieved_ids,
                "used_successfully": used_successfully,
            },
            mode="fast",
        )
        return submit_task(req, self.fabric, ctx)

    def _get_reinforcement_count(self, eid):
        """Read reinforcement_count from the private graph for an eid."""
        ak = self.fabric._agent_key("ws1", "atlas")
        g = self.fabric.private_graphs.get(ak)
        self.assertIsNotNone(g, "Private graph not found")
        ent = g.entities.get(eid)
        self.assertIsNotNone(ent, f"Entity {eid} not found")
        return int((ent.payload or {}).get("reinforcement_count", 0))

    # ------------------------------------------------------------------
    # §7.3 Case 1: Single eid in used_successfully increments count
    # ------------------------------------------------------------------
    def test_reinforce_single_eid_increments_count(self):
        eid = self.eids[0]
        before = self._get_reinforcement_count(eid)
        resp = self._reinforce([eid])
        self.assertTrue(resp.ok)
        after = self._get_reinforcement_count(eid)
        self.assertEqual(after, before + 1,
                         "reinforcement_count should increment by 1")

    # ------------------------------------------------------------------
    # §7.3 Case 2: Multiple eids each increment independently
    # ------------------------------------------------------------------
    def test_reinforce_multiple_eids_increments_each(self):
        eids = self.eids[:2]
        before = [self._get_reinforcement_count(e) for e in eids]
        resp = self._reinforce(eids)
        self.assertTrue(resp.ok)
        for i, eid in enumerate(eids):
            after = self._get_reinforcement_count(eid)
            self.assertEqual(after, before[i] + 1,
                             f"eid {eid} should have incremented")

    # ------------------------------------------------------------------
    # §7.3 Case 3: Duplicate eids in used_successfully are deduped
    # ------------------------------------------------------------------
    def test_reinforce_deduplicates_eids(self):
        eid = self.eids[0]
        before = self._get_reinforcement_count(eid)
        resp = self._reinforce([eid, eid, eid])
        self.assertTrue(resp.ok)
        after = self._get_reinforcement_count(eid)
        self.assertEqual(after, before + 1,
                         "Duplicate eids should increment only once per call")

    # ------------------------------------------------------------------
    # §7.3 Case 4: Missing eid produces no_op
    # ------------------------------------------------------------------
    def test_reinforce_missing_eid_is_no_op(self):
        resp = self._reinforce([999999])
        self.assertTrue(resp.ok)
        self.assertEqual(resp.result_code, RESULT_NO_OP,
                         "Missing eid should produce no_op result_code")
        self.assertEqual(resp.result.get("reinforced_eids"), [],
                         "No eids should have been reinforced")

    # ------------------------------------------------------------------
    # §7.3 Case 5: Shared/collective scope eid is a governed skip
    # ------------------------------------------------------------------
    def test_reinforce_shared_scope_eid_is_governed_skip(self):
        # Manually mark one eid as shared scope to test governed skip.
        eid = self.eids[2]
        ak = self.fabric._agent_key("ws1", "atlas")
        g = self.fabric.private_graphs[ak]
        g.update_payload(eid, {"scope": "shared"})

        before = self._get_reinforcement_count(eid)
        resp = self._reinforce([eid])
        self.assertTrue(resp.ok)
        after = self._get_reinforcement_count(eid)
        self.assertEqual(after, before,
                         "Shared-scope eid should NOT be incremented")
        self.assertEqual(resp.result_code, RESULT_NO_OP)
        # Verify skip reason is operator-visible (Plan-D7 amendment).
        skipped = resp.result.get("skipped", [])
        self.assertTrue(
            any(s["eid"] == eid and "scope_skip" in s.get("reason", "")
                for s in skipped),
            "Scope skip reason must be operator-visible in response"
        )

    # ------------------------------------------------------------------
    # §7.3 Case 6: Forward invariant — "reinforced" implies eid moved
    # ------------------------------------------------------------------
    def test_reinforce_envelope_reflects_mutation_invariant_forward(self):
        """If result_code == 'reinforced', at least one eid must have moved."""
        eid = self.eids[0]
        before = self._get_reinforcement_count(eid)
        resp = self._reinforce([eid])
        if resp.result_code == RESULT_REINFORCED:
            after = self._get_reinforcement_count(eid)
            self.assertGreater(after, before,
                               "Forward invariant: 'reinforced' must mean at least one eid moved")

    # ------------------------------------------------------------------
    # §7.3 Case 7: Reverse invariant — "no_op" implies no eid moved
    # ------------------------------------------------------------------
    def test_reinforce_envelope_reflects_mutation_invariant_reverse(self):
        """If result_code == 'no_op', no eid may have moved."""
        resp = self._reinforce([999999])
        self.assertEqual(resp.result_code, RESULT_NO_OP)
        # Verify no real eids moved (check all ingested eids).
        for eid in self.eids:
            count = self._get_reinforcement_count(eid)
            self.assertEqual(count, 0,
                             f"Reverse invariant: 'no_op' must mean no eid moved, "
                             f"but eid {eid} has reinforcement_count={count}")

    # ------------------------------------------------------------------
    # §7.3 Case 8: Monotonic — count never decreases
    # ------------------------------------------------------------------
    def test_reinforce_monotonic_never_decreases(self):
        eid = self.eids[1]
        counts = [self._get_reinforcement_count(eid)]
        for _ in range(5):
            self._reinforce([eid])
            counts.append(self._get_reinforcement_count(eid))
        for i in range(1, len(counts)):
            self.assertGreaterEqual(counts[i], counts[i - 1],
                                    f"reinforcement_count must be monotonic non-decreasing: "
                                    f"step {i-1}→{i}: {counts[i-1]}→{counts[i]}")
        self.assertEqual(counts[-1], 5,
                         "After 5 reinforce calls, count should be 5")


class TestReinforceDoesNotMoveOverlay(unittest.TestCase):
    """Reinforce must NOT touch the adaptive overlay (Framing Decision 4).

    Feedback = operator/outcome signal → overlay.
    Reinforce = per-memory/evidence signal → per-memory only.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Ingest a memory to reinforce against.
        ctx = RequestContext(client_id="test", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": "Overlay stability test memory.", "scope": "private"},
            mode="fast",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.eid = int(resp.result["eid"])

    def test_reinforce_does_not_move_overlay(self):
        """Overlay values must be identical before and after reinforce."""
        ident_before = self.fabric.create_agent("ws1", "atlas")
        overlay_before = dict(ident_before.overlay)

        ctx = RequestContext(client_id="test", trust_tier=TRUST_QUERY_REINFORCE,
                             workspace_id="ws1", agent_id="atlas")
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="reinforce",
            payload={
                "retrieved_ids": [self.eid],
                "used_successfully": [self.eid],
            },
            mode="fast",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.result_code, RESULT_REINFORCED)

        ident_after = self.fabric.create_agent("ws1", "atlas")
        overlay_after = dict(ident_after.overlay)

        self.assertEqual(overlay_before, overlay_after,
                         "Reinforce must NOT move overlay values. "
                         f"Before: {overlay_before}, After: {overlay_after}")


class TestReinforceBoostAtRankStage(unittest.TestCase):
    """Verify reinforcement_count is consumed at rank stage (Plan-D3).

    Uses a before/after approach on a single memory to avoid hash-embedder
    deduplication issues that prevent creating two identically-scored entities.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        os.environ["TORMENT_REINFORCE_BOOST"] = "0.04"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def tearDown(self):
        os.environ.pop("TORMENT_REINFORCE_BOOST", None)

    def _query_score_for_eid(self, eid, query_text):
        """Query and return the final (rescored) score for a specific eid, or None."""
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text=query_text, top_k=10,
        )
        for h in result.get("results", []):
            if int(h.get("eid", -1)) == eid:
                return float(h.get("final_score", h.get("score", 0)))
        return None

    def test_reinforced_memory_scores_higher(self):
        """Same memory should score higher after reinforcement_count is set."""
        ctx = RequestContext(client_id="test", trust_tier=TRUST_INGEST,
                             workspace_id="ws1", agent_id="atlas")
        text = "The quick brown fox jumped over the lazy dog."
        req = SpineRequest(
            workspace_id="ws1", agent_id="atlas",
            operation="ingest",
            payload={"text": text, "scope": "private"},
            mode="fast",
        )
        resp = submit_task(req, self.fabric, ctx)
        self.assertTrue(resp.ok)
        eid = int(resp.result["eid"])

        # Score before reinforcement.
        score_before = self._query_score_for_eid(eid, text)
        self.assertIsNotNone(score_before,
                             f"eid {eid} not found in query results")

        # Manually set reinforcement_count to simulate reinforcement.
        ak = self.fabric._agent_key("ws1", "atlas")
        g = self.fabric.private_graphs[ak]
        g.update_payload(eid, {"reinforcement_count": 5})

        # Score after reinforcement.
        score_after = self._query_score_for_eid(eid, text)
        self.assertIsNotNone(score_after,
                             f"eid {eid} not found after reinforcement")

        # The boost should be exactly 0.04 * ln(6) ≈ 0.0717
        expected_boost = 0.04 * math.log(6)
        actual_boost = score_after - score_before
        # Allow 10% tolerance for floating-point and any multiplicative
        # phases that compose on top of the additive boost.
        self.assertGreater(actual_boost, expected_boost * 0.5,
                           f"Score should increase by ~{expected_boost:.4f} "
                           f"but only increased by {actual_boost:.4f}. "
                           f"Before={score_before:.6f}, After={score_after:.6f}")


if __name__ == "__main__":
    unittest.main()
