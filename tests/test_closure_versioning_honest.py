# tests/test_closure_versioning_honest.py
"""
T3 — AC-3: revision creates new version, never silently overwrites.

Covers acceptance criteria from BLOCK_C_DESIGN.md §4 AC-3:

    fabric.revise_closure(...) produces a new version (new version_id),
    stored alongside the original. Original closure reads unchanged.
    version_history grows on each revision. No code path silently
    overwrites a prior version.

Design intent per BLOCK_C_DESIGN.md §6.4, R+8 from preconditions:

    Revising a closure means storing a new version alongside the prior
    one — never silent overwrite. The original stays readable. Version
    history is inspectable. The system must be able to see both what
    it believed at closure time and how that understanding evolved
    later.

References:
    - BLOCK_C_DESIGN.md §4 AC-3
    - BLOCK_C_DESIGN.md §6.4 (revise_closure)
    - PRE_BLOCK_C_PRECONDITIONS.md R+8 (no retrospective editing without versioning)
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric


def _full_proposal_kwargs() -> dict:
    return {
        "workspace_id": "ws1",
        "arc_name": "versioning-test-arc",
        "arc_kind": "feature",
        "scope": [10, 11, 12],
        "what_it_was": "An arc for testing revision versioning.",
        "what_worked": "The first commit was complete.",
        "what_surprised": "Nothing in the first version.",
        "what_to_carry_forward": "Original wisdom version 1.",
        "deferred_or_open_items": [],
    }


class TestRevisionCreatesNewVersion(unittest.TestCase):
    """Each revise_closure call produces a new version_id. Originals
    remain readable; nothing is silently overwritten."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        # propose → ratify → commit, so we have something to revise
        prop = self.fabric.propose_closure(**_full_proposal_kwargs())
        self.assertTrue(prop.get("ok"))
        self.closure_id = prop["closure_id"]
        self.original_version_id = prop["version_id"]
        self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=self.closure_id,
            ratifier="atlas",
        )
        commit = self.fabric.commit_closure(
            workspace_id="ws1",
            closure_id=self.closure_id,
            ratifier="atlas",
        )
        self.assertTrue(commit.get("ok"),
                        "precondition: commit succeeded before revision tests")

    def test_fabric_has_revise_closure(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "revise_closure"),
            "fabric.revise_closure must exist per §6.4"
        )

    def test_revise_creates_new_version_id(self) -> None:
        """The fundamental AC-3 assertion."""
        result = self.fabric.revise_closure(
            workspace_id="ws1",
            closure_id=self.closure_id,
            revised_fields={
                "what_to_carry_forward": "Updated wisdom version 2.",
            },
            ratifier="atlas",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "revised")
        new_version_id = result.get("version_id")
        self.assertTrue(new_version_id)
        self.assertNotEqual(
            new_version_id, self.original_version_id,
            "revise_closure must produce a NEW version_id, not the original"
        )
        # parent_version_id should link back to original
        self.assertEqual(result.get("parent_version_id"),
                         self.original_version_id)

    def test_original_version_remains_readable_after_revision(self) -> None:
        """R+8: revision is new version alongside original; original
        stays readable."""
        self.fabric.revise_closure(
            workspace_id="ws1",
            closure_id=self.closure_id,
            revised_fields={
                "what_to_carry_forward": "Updated wisdom version 2.",
            },
            ratifier="atlas",
        )
        # Read the original via the closure store
        from torment_service.closure_memory import ClosureStore
        store = ClosureStore(data_dir=self.tmp, workspace_id="ws1")
        original = store.get_version(self.closure_id, self.original_version_id)
        self.assertIsNotNone(
            original,
            "original version must be readable after revision"
        )
        self.assertEqual(
            original.what_to_carry_forward,
            "Original wisdom version 1.",
            "original content must be unchanged"
        )

    def test_two_revisions_produce_two_new_versions(self) -> None:
        r1 = self.fabric.revise_closure(
            workspace_id="ws1", closure_id=self.closure_id,
            revised_fields={"what_to_carry_forward": "v2"},
            ratifier="atlas",
        )
        r2 = self.fabric.revise_closure(
            workspace_id="ws1", closure_id=self.closure_id,
            revised_fields={"what_to_carry_forward": "v3"},
            ratifier="atlas",
        )
        self.assertNotEqual(r1["version_id"], r2["version_id"])
        self.assertNotEqual(r1["version_id"], self.original_version_id)
        self.assertNotEqual(r2["version_id"], self.original_version_id)

    def test_version_history_grows_on_each_revision(self) -> None:
        """Each revision appends to version_history per §5.2."""
        self.fabric.revise_closure(
            workspace_id="ws1", closure_id=self.closure_id,
            revised_fields={"what_to_carry_forward": "v2"},
            ratifier="atlas",
        )
        from torment_service.closure_memory import ClosureStore
        store = ClosureStore(data_dir=self.tmp, workspace_id="ws1")
        latest = store.get_latest_version(self.closure_id)
        self.assertIsNotNone(latest)
        self.assertGreater(
            len(latest.version_history), 0,
            "version_history must grow when a revision is made"
        )

    def test_list_versions_returns_all(self) -> None:
        """ClosureStore.list_versions returns every version of a closure."""
        self.fabric.revise_closure(
            workspace_id="ws1", closure_id=self.closure_id,
            revised_fields={"what_to_carry_forward": "v2"},
            ratifier="atlas",
        )
        self.fabric.revise_closure(
            workspace_id="ws1", closure_id=self.closure_id,
            revised_fields={"what_to_carry_forward": "v3"},
            ratifier="atlas",
        )
        from torment_service.closure_memory import ClosureStore
        store = ClosureStore(data_dir=self.tmp, workspace_id="ws1")
        versions = store.list_versions(self.closure_id)
        # original + 2 revisions = 3 versions
        self.assertEqual(len(versions), 3)

    def test_revise_unratified_proposal_is_rejected(self) -> None:
        """Per §6.4: only committed closures can be revised. You don't
        revise a proposal — you create a new proposal."""
        # Create a fresh proposal that is NOT ratified or committed
        kwargs = _full_proposal_kwargs()
        kwargs["arc_name"] = "fresh-unratified-arc"
        proposal = self.fabric.propose_closure(**kwargs)
        self.assertTrue(proposal.get("ok"))

        result = self.fabric.revise_closure(
            workspace_id="ws1",
            closure_id=proposal["closure_id"],
            revised_fields={"what_to_carry_forward": "early revision"},
            ratifier="atlas",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "not_committed")

    def test_revise_nonexistent_closure_returns_not_found(self) -> None:
        result = self.fabric.revise_closure(
            workspace_id="ws1",
            closure_id="closure_does_not_exist",
            revised_fields={"what_to_carry_forward": "x"},
            ratifier="atlas",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "not_found")


# ---------------------------------------------------------------------------
# Negative-space: no silent overwrite path
# ---------------------------------------------------------------------------


class TestNoSilentOverwritePath(unittest.TestCase):
    """Verify there's no fabric method that updates a closure version
    in place. The only mutation path for committed closures is
    revise_closure, which produces a new version."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)

    def test_no_in_place_update_method(self) -> None:
        for forbidden in (
            "update_closure",
            "modify_closure",
            "edit_closure",
            "overwrite_closure",
            "patch_closure",
        ):
            self.assertFalse(
                hasattr(self.fabric, forbidden),
                f"fabric must not expose {forbidden!r}; revisions go "
                "through revise_closure (R+8 — no silent overwrite)."
            )


if __name__ == "__main__":
    unittest.main()
