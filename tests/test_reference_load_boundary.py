# tests/test_reference_load_boundary.py
"""
T1 — AC-1.1 through AC-1.4: reference memory load boundary tests.

Covers acceptance criteria from BLOCK_B_DESIGN.md §4.1:

    AC-1.1 — Reference ingest requires source linkage.
    AC-1.2 — Load returns a whole object with staleness marked.
    AC-1.3 — Loaded references never silently become durable substrate.
    AC-1.4 — Default retrieval lanes exclude reference entries.

Design intent per BLOCK_B_DESIGN.md §5.2–5.3, §6 and the carry-forward
caution from ratification:

    Storage identity and activation/loading must stay separate.
    ReferenceEntry has durable identity; ActiveLoad is a thin
    lifecycle event on top. A reference's provenance is set once at
    ingest and never touched again; every load is a separate event
    captured in ReferenceLoadLedger.

These tests FAIL against current code (pre-implementation). They pass
once:
    - torment_service.reference_memory.ReferenceStore exists
    - fabric.ingest_reference / load_reference / unload_reference
      / list_active_loads exist with the specified envelopes
    - The default-lane filter at fabric.query excludes memory_class="reference"
    - ProvenanceV1.for_reference_ingest factory lands
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric


# ---------------------------------------------------------------------------
# AC-1.1 — ingest requires source linkage
# ---------------------------------------------------------------------------


class TestReferenceIngestRequiresSourceLinkage(unittest.TestCase):
    """Block B §4.1 AC-1.1: source_link AND source_kind required."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

    def test_fabric_has_ingest_reference_method(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "ingest_reference"),
            "fabric.ingest_reference must exist per BLOCK_B_DESIGN §6.2"
        )

    def test_complete_reference_ingest_succeeds(self) -> None:
        result = self.fabric.ingest_reference(
            workspace_id="ws1",
            title="Block A Design",
            body="The canonical Block A design document body...",
            source_link="docs/BLOCK_A_DESIGN.md",
            source_kind="repo_file",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "ingested")
        self.assertTrue(result.get("ref_id"))

    def test_missing_source_link_is_rejected(self) -> None:
        result = self.fabric.ingest_reference(
            workspace_id="ws1",
            title="No source link",
            body="content",
            source_link="",  # empty
            source_kind="repo_file",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_source_linkage")
        self.assertNotIn("ref_id", result) if "ref_id" not in result else None
        # Either the field is absent, or it's empty — both acceptable
        self.assertFalse(result.get("ref_id"))

    def test_missing_source_kind_is_rejected(self) -> None:
        result = self.fabric.ingest_reference(
            workspace_id="ws1",
            title="No source kind",
            body="content",
            source_link="docs/SOMEWHERE.md",
            source_kind="",  # empty
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_source_linkage")


# ---------------------------------------------------------------------------
# AC-1.2 — load returns whole object with staleness
# ---------------------------------------------------------------------------


class TestReferenceLoadReturnsWholeObject(unittest.TestCase):
    """Load returns the whole body (not chunks) with a stale flag."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        self.body = (
            "This is a long coherent reference body. "
            "It has multiple sentences. "
            "Its whole matters beyond any distilled fact extracted from it."
        )
        r = self.fabric.ingest_reference(
            workspace_id="ws1",
            title="Ref 1",
            body=self.body,
            source_link="internal/doc/1",
            source_kind="internal_doc",
        )
        self.ref_id = r["ref_id"]

    def test_fabric_has_load_reference_method(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "load_reference"),
            "fabric.load_reference must exist per BLOCK_B_DESIGN §6.3"
        )

    def test_load_returns_whole_body(self) -> None:
        result = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=self.ref_id, scope_tag="scope_a",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "loaded")
        # Whole body, not chunked
        self.assertEqual(result.get("body"), self.body)

    def test_load_envelope_carries_stale_flag(self) -> None:
        result = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=self.ref_id, scope_tag="scope_a",
        )
        self.assertIn("stale", result,
                      "load envelope must carry stale flag per AC-1.2")
        # First load — source unchanged — should be fresh
        self.assertFalse(result["stale"])

    def test_load_returns_load_id_not_ref_id_duplicate(self) -> None:
        """Per carry-forward caution: ActiveLoad identity ≠ ReferenceEntry
        identity. load_id is a new identifier for the lifecycle event,
        not an echo of ref_id."""
        result = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=self.ref_id, scope_tag="scope_a",
        )
        self.assertIn("load_id", result)
        self.assertIn("ref_id", result)
        self.assertEqual(result["ref_id"], self.ref_id)
        # load_id is distinct from ref_id — loads and references have
        # separate identity
        self.assertNotEqual(result["load_id"], self.ref_id)

    def test_two_loads_produce_two_distinct_load_ids(self) -> None:
        """Same ref, two loads → two different load_ids. Each load is
        its own lifecycle event (addresses storage-vs-loading caution)."""
        r1 = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=self.ref_id, scope_tag="scope_a",
        )
        r2 = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=self.ref_id, scope_tag="scope_b",
        )
        self.assertNotEqual(r1["load_id"], r2["load_id"])
        # Both refer to same underlying reference
        self.assertEqual(r1["ref_id"], r2["ref_id"])

    def test_load_nonexistent_ref_returns_not_found(self) -> None:
        result = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id="ref_does_not_exist", scope_tag="scope_a",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "not_found")


# ---------------------------------------------------------------------------
# AC-1.3 — loaded refs never silently become durable
# ---------------------------------------------------------------------------


class TestLoadedReferencesNeverDurable(unittest.TestCase):
    """A load does NOT create a core or baton substrate entry."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def _entity_count(self) -> int:
        ak = self.fabric._agent_key("ws1", "atlas")
        g = self.fabric.private_graphs.get(ak)
        return len(g.entities) if g is not None else 0

    def test_ingest_reference_does_not_create_substrate_entity(self) -> None:
        before = self._entity_count()
        self.fabric.ingest_reference(
            workspace_id="ws1",
            title="Ref",
            body="A long reference body",
            source_link="/docs/ref.md",
            source_kind="repo_file",
        )
        after = self._entity_count()
        self.assertEqual(
            before, after,
            "ingest_reference must NOT create a substrate entity"
        )

    def test_load_does_not_create_substrate_entity(self) -> None:
        r = self.fabric.ingest_reference(
            workspace_id="ws1",
            title="Ref",
            body="body",
            source_link="/docs/ref.md",
            source_kind="repo_file",
        )
        before = self._entity_count()
        self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=r["ref_id"], scope_tag="scope_a",
        )
        after = self._entity_count()
        self.assertEqual(
            before, after,
            "load_reference must NOT create a substrate entity (R+3)"
        )


# ---------------------------------------------------------------------------
# AC-1.4 — default retrieval lanes exclude reference entries
# ---------------------------------------------------------------------------


class TestDefaultLanesExcludeReference(unittest.TestCase):
    """fabric.query returns zero reference entries regardless of lane
    selection or embedding similarity."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # A core memory we expect TO surface
        r1 = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The migration script runs nightly.",
            step=1, scope="private",
        )
        self.core_eid = int(r1["eid"])

        # A reference entry we expect NEVER to surface via fabric.query
        self.fabric.ingest_reference(
            workspace_id="ws1",
            title="Migration Script Reference",
            body="Documentation about the migration script that runs nightly and verifies schema integrity.",
            source_link="docs/migration_script.md",
            source_kind="repo_file",
        )

    def test_reference_entry_not_in_core_query(self) -> None:
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="migration script", top_k=10,
        )
        for h in result.get("results", []):
            self.assertNotEqual(
                h.get("memory_class"), "reference",
                f"Reference entry leaked into fabric.query results: {h}"
            )

    def test_reference_entry_not_surfaced_via_high_top_k(self) -> None:
        """Hard filter: even with huge top_k, reference never appears."""
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="migration", top_k=100,
        )
        for h in result.get("results", []):
            self.assertNotEqual(h.get("memory_class"), "reference")

    def test_core_still_retrievable(self) -> None:
        """Sanity: filtering reference doesn't break core retrieval."""
        result = self.fabric.query(
            workspace_id="ws1", agent_id="atlas",
            query_text="migration script", top_k=10,
        )
        eids = [int(h.get("eid", -1)) for h in result.get("results", [])]
        self.assertIn(self.core_eid, eids)


if __name__ == "__main__":
    unittest.main()
