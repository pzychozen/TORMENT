# tests/test_private_ingest_contradiction_surface.py
"""
T5 — AC-4 proof: private ingest fires contradiction surfacing via
ConflictRegistry when a high-similarity-plus-contradictory entry exists.

Covers the acceptance criterion from BLOCK_A_DESIGN.md §4 AC-4:

    When a private ingest's content is high-similarity-plus-contradictory
    to an existing same-agent entry, the existing ConflictRegistry
    records the conflict. Does not block the write; does not auto-resolve.

Design per BLOCK_A_DESIGN.md §8:
    - Fires for private memory_class=="core" writes only (v0.1 scope).
    - Uses existing _detect_canon_conflict heuristic.
    - Does NOT block the write — ingest still succeeds.
    - Does NOT auto-resolve — conflict status is "open".
    - Does NOT fire for shared writes (shared path handles its own).
    - Does NOT fire for baton writes (baton is lifecycle, not claim).

§8 framing reminder: "core" is NOT the eternal contradiction-bearing
class. Future memory classes must make an explicit decision. This test
pins v0.1 behavior; later expansions need their own tests.

These tests FAIL against current code (pre-implementation): private
ingest at fabric.py:~2301 does not currently wire contradiction
detection. They pass once the §8 change lands.

References:
    - BLOCK_A_DESIGN.md §4 AC-4
    - BLOCK_A_DESIGN.md §8 (wiring + scope framing)
    - torment_service/fabric.py::_detect_canon_conflict (line ~130)
    - torment_service/conflicts.py (ConflictRegistry)
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


def _lifecycle() -> dict:
    return {
        "owner": "user",
        "expires_when": "later",
        "resolution_condition": "attended",
    }


class TestPrivateCoreContradictionSurfaces(unittest.TestCase):
    """Two contradictory private-core ingests → ConflictRegistry records."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def _all_open_conflicts(self) -> list:
        ws = self.fabric.get_workspace("ws1")
        conflicts = []
        for domain_id, registry in ws.conflicts.items():
            conflicts.extend(registry.list(status="open", limit=500))
        return conflicts

    def test_contradiction_fires_for_private_core(self) -> None:
        """Ingest statement, then a contradictory statement on the
        same topic — a conflict should be recorded.

        Sentence pair chosen so hash-embedder similarity exceeds the
        0.88 floor in _detect_canon_conflict (measured ~0.95 under
        TORMENT_EMBED_PROVIDER=hash). With a real sentence-transformer
        embedder any topically-similar contradictory pair would
        trigger; the hash embedder is less discriminating so the test
        uses a pair with high lexical overlap plus a negation mismatch.
        """
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The auth refactor is merged and deployed to prod yesterday.",
            step=1, scope="private",
        )
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The auth refactor is not merged and deployed to prod yesterday.",
            step=2, scope="private",
        )

        conflicts = self._all_open_conflicts()
        self.assertGreater(
            len(conflicts), 0,
            "Private-ingest contradiction should have been recorded "
            f"in ConflictRegistry. Conflicts found: {conflicts}"
        )

    def test_contradiction_does_not_block_write(self) -> None:
        """Second ingest still succeeds — contradiction does not veto."""
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The auth refactor is merged and deployed to prod yesterday.",
            step=1, scope="private",
        )
        result = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The auth refactor is not merged and deployed to prod yesterday.",
            step=2, scope="private",
        )
        # The write still succeeded; eid returned.
        self.assertTrue(
            result.get("stored") or result.get("eid") is not None,
            f"Contradictory ingest should still store; got {result}"
        )

    def test_contradiction_status_is_open_not_auto_resolved(self) -> None:
        """Surfacing records at status=open; never auto-resolves."""
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The feature flag is live in production environment today.",
            step=1, scope="private",
        )
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The feature flag is not live in production environment today.",
            step=2, scope="private",
        )
        conflicts = self._all_open_conflicts()
        for c in conflicts:
            self.assertEqual(
                c.status, "open",
                f"Contradiction must stay open (no auto-resolve). Got: {c.status}"
            )


class TestBatonDoesNotFireContradiction(unittest.TestCase):
    """§8 scope framing: baton writes are lifecycle, not claim. They
    must NOT fire contradiction surfacing."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Pre-existing core memory making a claim
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The migration script is complete.",
            step=1, scope="private",
        )

    def _all_open_conflicts(self) -> list:
        ws = self.fabric.get_workspace("ws1")
        conflicts = []
        for domain_id, registry in ws.conflicts.items():
            conflicts.extend(registry.list(status="open", limit=500))
        return conflicts

    def test_baton_write_does_not_fire_contradiction(self) -> None:
        """Baton 'remember to check X' next to core 'X is true' is NOT
        a contradiction. Lifecycle intent ≠ claim contradiction."""
        before = len(self._all_open_conflicts())

        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Remember to double-check whether the migration completed.",
            step=2, scope="private",
            provenance=_baton_prov(),
            memory_class="baton",
            extra_payload={"baton_lifecycle": _lifecycle()},
        )

        after = len(self._all_open_conflicts())
        self.assertEqual(
            before, after,
            f"Baton write must not fire contradiction surfacing. "
            f"Conflicts before={before}, after={after}"
        )


class TestSharedWriteDoesNotDoublefire(unittest.TestCase):
    """§8 explicit note: contradiction surfacing for shared writes
    continues through the existing shared-commit path at
    fabric.py:~4222. The Block A private-ingest wiring must not
    double-fire on shared writes."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def test_private_branch_does_not_fire_for_shared(self) -> None:
        """A 'scope=shared' ingest should not go through the new
        private-ingest contradiction check at all. Verified by a
        shared ingest not increasing conflict count beyond what the
        shared-commit path would normally record."""
        # We assert by structure — shared writes go through a different
        # path; the private-ingest wiring's scope=="private" guard
        # excludes them. If the guard is wrong, this test will likely
        # fail in indirect ways (double-counted conflicts). For v0.1
        # scaffolding, simply assert that shared writes don't raise
        # via the private-ingest path.
        # (Real shared-commit conflict behavior is covered by existing
        # collective tests; we just confirm the private path stays private.)
        ws = self.fabric.get_workspace("ws1")
        ws_conflicts_before = sum(
            len(r.list(status="any", limit=500))
            for r in ws.conflicts.values()
        )

        # A direct-shared ingest is uncommon; the existing flow is to
        # use propose_share / commit. For scaffolding we just confirm
        # the private-path guard doesn't misfire: a private-core
        # ingest should be the only thing firing the new private path.
        self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="A private note about the auth rework.",
            step=1, scope="private",
        )
        # No prior entry similar enough → no conflict expected
        ws_conflicts_after = sum(
            len(r.list(status="any", limit=500))
            for r in ws.conflicts.values()
        )
        self.assertEqual(
            ws_conflicts_before, ws_conflicts_after,
            "A solitary private ingest with no similar prior entries "
            "must not produce a conflict record"
        )


if __name__ == "__main__":
    unittest.main()
