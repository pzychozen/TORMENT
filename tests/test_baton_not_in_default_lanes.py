# tests/test_baton_not_in_default_lanes.py
"""
T2 — AC-3 proof: default MemoryPlan retrieval lanes exclude baton entries.

Covers the acceptance criterion from BLOCK_A_DESIGN.md §4 AC-3:

    Default retrieval lanes exclude baton entries. A MemoryPlan query with
    any combination of retrieve_core/archive/deep/relational returns zero
    baton EIDs, even when content embeddings match. Baton-aware retrieval
    requires an explicit baton-inclusive query path.

Design intent per BLOCK_A_DESIGN.md §7 (rigidity sniff test):
    Exclusion is a lifecycle filter (`memory_class == "baton"`), NOT
    a score down-weighting. Baton entries must never surface via core
    retrieval, regardless of embedding similarity.

Explicit baton-aware path: fabric.list_active_batons (§6.2).

These tests FAIL against current code (pre-implementation). They pass
once:
    - fabric.ingest accepts memory_class="baton"
    - retrieval_assembler filters memory_class=="baton" out of every lane
    - fabric.list_active_batons exists and returns baton entries
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric
from torment_service.provenance_v1 import ProvenanceV1


def _baton_prov() -> dict:
    return ProvenanceV1.for_baton_ingest().to_dict()


def _lifecycle(owner: str = "user",
               expires: str = "after_review",
               resolves: str = "user confirms review done") -> dict:
    return {
        "owner": owner,
        "expires_when": expires,
        "resolution_condition": resolves,
    }


class TestDefaultLanesExcludeBaton(unittest.TestCase):
    """A MemoryPlan-shaped retrieval must never return baton EIDs even
    when embeddings match closely."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Two core memories + one baton, all about the same topic so
        # similarity is high. The baton's text deliberately overlaps
        # the core topic so a score-based approach would surface it.
        self.core_eids = []
        for text in [
            "The migration script runs nightly and verifies schema integrity.",
            "Schema integrity checks happen during the nightly migration run.",
        ]:
            r = self.fabric.ingest(
                workspace_id="ws1", agent_id="atlas",
                text=text, step=1, scope="private",
            )
            self.core_eids.append(int(r["eid"]))

        r = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Remember to check the migration script output tomorrow.",
            step=1, scope="private",
            provenance=_baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": _lifecycle()},
        )
        self.baton_eid = int(r["eid"])

    def _query_eids(self, query_text: str) -> list:
        """Call the fabric's normal query path and return eids found."""
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text=query_text, top_k=10,
        )
        return [int(h.get("eid", -1)) for h in result.get("results", [])]

    def test_baton_not_returned_by_default_query(self) -> None:
        eids = self._query_eids("migration script verification")
        self.assertNotIn(
            self.baton_eid, eids,
            f"Baton eid {self.baton_eid} must not appear in default query "
            f"results. Got eids: {eids}"
        )

    def test_core_memories_still_returned(self) -> None:
        """Sanity: core memories with matching embeddings should still
        be returned — baton exclusion is lifecycle-based, not a
        side-effect that breaks core retrieval."""
        eids = self._query_eids("migration schema integrity")
        # At least one core eid should still surface
        core_hits = [e for e in eids if e in self.core_eids]
        self.assertGreater(
            len(core_hits), 0,
            f"At least one core memory should be returned; got eids {eids}"
        )

    def test_baton_exclusion_is_filter_not_rank(self) -> None:
        """Rigidity sniff test: baton must be ABSENT from results, not
        merely ranked lower. If the implementation just down-weights
        baton, it could still appear in a top_k=10 query — this test
        pins hard exclusion."""
        # Query with a large top_k to catch any baton that's just
        # down-ranked rather than filtered.
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="migration",
            top_k=100,
        )
        eids = [int(h.get("eid", -1)) for h in result.get("results", [])]
        self.assertNotIn(
            self.baton_eid, eids,
            "Baton exclusion must be a hard filter, not a score penalty"
        )


class TestListActiveBatons(unittest.TestCase):
    """fabric.list_active_batons is the explicit baton-aware path."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Ingest two batons with different owners
        r1 = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Check the log rotation script.",
            step=1, scope="private",
            provenance=_baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": _lifecycle(owner="user")},
        )
        self.user_baton_eid = int(r1["eid"])

        r2 = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Next session: follow up on the auth change.",
            step=1, scope="private",
            provenance=_baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": _lifecycle(owner="next_ai")},
        )
        self.next_ai_baton_eid = int(r2["eid"])

        # Also ingest a core memory that should NOT appear in list_active_batons
        r3 = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Core memory about nothing baton-related.",
            step=1, scope="private",
        )
        self.core_eid = int(r3["eid"])

    def test_list_active_batons_method_exists(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "list_active_batons"),
            "fabric.list_active_batons must exist per §6.2"
        )

    def test_list_active_batons_returns_both(self) -> None:
        result = self.fabric.list_active_batons(
            workspace_id="ws1", agent_id="atlas",
        )
        batons = result.get("batons", [])
        eids = [b["eid"] for b in batons]
        self.assertIn(self.user_baton_eid, eids)
        self.assertIn(self.next_ai_baton_eid, eids)

    def test_list_active_batons_excludes_core(self) -> None:
        result = self.fabric.list_active_batons(
            workspace_id="ws1", agent_id="atlas",
        )
        batons = result.get("batons", [])
        eids = [b["eid"] for b in batons]
        self.assertNotIn(
            self.core_eid, eids,
            "list_active_batons must only return memory_class='baton' entries"
        )

    def test_list_active_batons_owner_filter(self) -> None:
        result = self.fabric.list_active_batons(
            workspace_id="ws1", agent_id="atlas", owner="user",
        )
        batons = result.get("batons", [])
        eids = [b["eid"] for b in batons]
        self.assertIn(self.user_baton_eid, eids)
        self.assertNotIn(self.next_ai_baton_eid, eids)

    def test_list_active_batons_envelope_shape(self) -> None:
        result = self.fabric.list_active_batons(
            workspace_id="ws1", agent_id="atlas",
        )
        self.assertIn("ok", result)
        self.assertIn("result_code", result)
        self.assertIn("batons", result)
        self.assertIn(result["result_code"], ("listed", "no_active"))


if __name__ == "__main__":
    unittest.main()
