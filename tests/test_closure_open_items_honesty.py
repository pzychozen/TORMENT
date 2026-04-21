# tests/test_closure_open_items_honesty.py
"""
T4 — AC-4: open-items honesty mismatch detection.

Covers acceptance criteria from BLOCK_C_DESIGN.md §4 AC-4:

    fabric.commit_closure(...) on a closure whose scope contains open
    ConflictRegistry conflicts or active batons, while
    deferred_or_open_items is empty → rejected with a specific
    mismatch result.

Design intent per BLOCK_C_DESIGN.md §8 + analysis §3.6 + R+11:

    The detector reads concrete v0.1 signals only:
        - ConflictRegistry.list(status="open") filtered to scope eids
        - fabric.list_active_batons(...) filtered to scope eids

    Mismatch fires when (open_conflicts + active_batons) is non-empty
    AND deferred_or_open_items is empty. A non-empty
    deferred_or_open_items satisfies (anti-false-finality, not
    full-truth-check; v0.1 anti-false-finality only).

    Task residue is a NAMED GAP per D.5 — NOT checked.

References:
    - BLOCK_C_DESIGN.md §4 AC-4
    - BLOCK_C_DESIGN.md §8 (open-items honesty mismatch detection)
    - BLOCK_C_IMPLEMENTATION_ANALYSIS.md §3.6 (concrete algorithm)
    - PRE_BLOCK_C_PRECONDITIONS.md §8.4 (open-items-honesty test)
    - PRE_BLOCK_C_PRECONDITIONS.md R+10 + R+11
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric
from torment_service.provenance_v1 import ProvenanceV1


def _full_proposal_kwargs(
    arc_name: str = "open-items-test-arc",
    scope: list = None,
    deferred: list = None,
) -> dict:
    return {
        "workspace_id": "ws1",
        "arc_name": arc_name,
        "arc_kind": "feature",
        "scope": scope if scope is not None else [],
        "what_it_was": "Arc for open-items honesty testing.",
        "what_worked": "Detection logic worked.",
        "what_surprised": "Nothing surprising.",
        "what_to_carry_forward": "Keep R+10 honest.",
        "deferred_or_open_items": deferred if deferred is not None else [],
    }


class TestDetectOpenItemsMismatchHelperExists(unittest.TestCase):
    """The shared helper from §8.1 must exist as a function (not method),
    pure over its inputs."""

    def test_helper_importable(self) -> None:
        try:
            from torment_service.closure_memory import (
                detect_open_items_mismatch,
            )  # noqa: F401
        except ImportError:
            self.fail(
                "torment_service.closure_memory.detect_open_items_mismatch "
                "must exist per §8.1"
            )


# ---------------------------------------------------------------------------
# AC-4 — open conflicts in scope + empty deferred → rejected
# ---------------------------------------------------------------------------


class TestCommitRejectedWhenScopeHasOpenConflicts(unittest.TestCase):
    """If ConflictRegistry has open conflicts whose eid_a or eid_b is
    in the closure's scope AND deferred_or_open_items is empty → the
    commit is rejected with open_items_mismatch."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Create two conflicting core ingests (Block A pattern) to
        # produce an open conflict in the registry.
        r1 = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The auth refactor is merged and deployed to prod yesterday.",
            step=1, scope="private",
        )
        self.eid_a = int(r1["eid"])

        r2 = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="The auth refactor is not merged and deployed to prod yesterday.",
            step=2, scope="private",
        )
        self.eid_b = int(r2["eid"])
        # That second ingest should have created an open conflict via
        # Block A's private-ingest contradiction surfacing.

    def test_setup_produced_an_open_conflict(self) -> None:
        """Sanity: the fixtures actually produced an open conflict in
        the registry, otherwise the AC-4 test is meaningless."""
        ws = self.fabric.get_workspace("ws1")
        any_open = False
        for domain_id, registry in ws.conflicts.items():
            opens = registry.list(status="open", limit=500)
            if opens:
                any_open = True
                break
        self.assertTrue(
            any_open,
            "precondition: setup must produce at least one open conflict"
        )

    def test_commit_rejected_when_scope_overlaps_open_conflict(self) -> None:
        """The AC-4 load-bearing assertion."""
        prop = self.fabric.propose_closure(**_full_proposal_kwargs(
            scope=[self.eid_a, self.eid_b],
            deferred=[],   # empty — and we have unresolved
        ))
        self.assertTrue(prop.get("ok"))
        self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=prop["closure_id"],
            ratifier="atlas",
        )
        result = self.fabric.commit_closure(
            workspace_id="ws1",
            closure_id=prop["closure_id"],
            ratifier="atlas",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "open_items_mismatch")
        # The unresolved signals should be reported back so the caller
        # can declare them.
        self.assertIn("unresolved", result)

    def test_commit_succeeds_when_deferred_acknowledges_open_items(self) -> None:
        """Non-empty deferred_or_open_items satisfies the check (v0.1
        is anti-false-finality, not full-truth-check)."""
        prop = self.fabric.propose_closure(**_full_proposal_kwargs(
            arc_name="acknowledged-open-items-arc",
            scope=[self.eid_a, self.eid_b],
            deferred=["auth-refactor-status: contradictory reports"],
        ))
        self.assertTrue(prop.get("ok"))
        self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=prop["closure_id"],
            ratifier="atlas",
        )
        result = self.fabric.commit_closure(
            workspace_id="ws1",
            closure_id=prop["closure_id"],
            ratifier="atlas",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "committed")


# ---------------------------------------------------------------------------
# AC-4 — active batons in scope + empty deferred → rejected
# ---------------------------------------------------------------------------


class TestCommitRejectedWhenScopeHasActiveBatons(unittest.TestCase):
    """If active batons (status=active) have eids in the closure scope
    AND deferred_or_open_items is empty → commit rejected."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Ingest an active baton (Block A pattern)
        baton_prov = ProvenanceV1.for_baton_ingest().to_dict()
        r = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Verify the migration before release.",
            step=1, scope="private",
            provenance=baton_prov,
            memory_class="baton",
            extra_payload={"baton_lifecycle": {
                "owner": "user",
                "expires_when": "user confirms done",
                "resolution_condition": "explicit acknowledgment",
            }},
        )
        self.baton_eid = int(r["eid"])

    def test_commit_rejected_with_active_baton_in_scope(self) -> None:
        prop = self.fabric.propose_closure(**_full_proposal_kwargs(
            arc_name="baton-in-scope-arc",
            scope=[self.baton_eid],
            deferred=[],
        ))
        self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=prop["closure_id"],
            ratifier="atlas",
        )
        result = self.fabric.commit_closure(
            workspace_id="ws1",
            closure_id=prop["closure_id"],
            ratifier="atlas",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "open_items_mismatch")


# ---------------------------------------------------------------------------
# Anti-false-positive: clean scope + empty deferred passes
# ---------------------------------------------------------------------------


class TestNoFalsePositive(unittest.TestCase):
    """If scope has NO open conflicts and NO active batons, then an
    empty deferred_or_open_items is fine."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # One peaceful core memory; no contradictions; no batons.
        r = self.fabric.ingest(
            workspace_id="ws1", agent_id="atlas",
            text="Documentation is up to date.",
            step=1, scope="private",
        )
        self.eid = int(r["eid"])

    def test_clean_scope_empty_deferred_commit_passes(self) -> None:
        prop = self.fabric.propose_closure(**_full_proposal_kwargs(
            arc_name="clean-scope-arc",
            scope=[self.eid],
            deferred=[],
        ))
        self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=prop["closure_id"],
            ratifier="atlas",
        )
        result = self.fabric.commit_closure(
            workspace_id="ws1",
            closure_id=prop["closure_id"],
            ratifier="atlas",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "committed")


if __name__ == "__main__":
    unittest.main()
