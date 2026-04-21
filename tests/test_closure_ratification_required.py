# tests/test_closure_ratification_required.py
"""
T2 — AC-2: ratification is structural, not implied.

Covers acceptance criteria from BLOCK_C_DESIGN.md §4 AC-2:

    fabric.commit_closure(...) without a prior fabric.ratify_closure(...)
    ratification event in the ledger → rejected. State is derivable
    from event stream only; cannot be forged by setting a direct bool
    field.

Design intent per BLOCK_C_DESIGN.md §4, §5.4, §6.2, §6.3:

    Lifecycle stages — proposed / ratified / committed / revised —
    are stages of one ClosureEntry domain, derived from append-only
    ClosureLedger events. The entry has NO `state` field. State is
    derived by literal event-kind lookup in the ledger.

    Allowed pattern:
        - proposed event exists → state is proposed
        - ratified event after proposed → state is ratified
        - commit_closure rejects unless a ratified event exists
        - revise_closure creates a new version_id

    NOT allowed: inferring lifecycle from loose combinations of events,
    heuristic interpretation layers, ambiguous state reconstruction,
    "smart" lifecycle detection. (§12 handoff note 9.)

References:
    - BLOCK_C_DESIGN.md §4 AC-2
    - BLOCK_C_DESIGN.md §5.4 (event-derived lifecycle state)
    - BLOCK_C_DESIGN.md §6.2 (ratify_closure)
    - BLOCK_C_DESIGN.md §6.3 (commit_closure validates prior ratification)
    - BLOCK_C_DESIGN.md §12 handoff notes 3 + 9
    - PRE_BLOCK_C_PRECONDITIONS.md §4 (ratification-is-structural rule)
    - PRE_BLOCK_C_PRECONDITIONS.md R+7 (no automatic enactment)
    - PRE_BLOCK_C_PRECONDITIONS.md R+9 (no model-authored commits)
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
        "arc_name": "ratification-test-arc",
        "arc_kind": "feature",
        "scope": [1, 2, 3],
        "what_it_was": "An arc for testing ratification flow.",
        "what_worked": "Ratification was structural.",
        "what_surprised": "Nothing.",
        "what_to_carry_forward": "Keep ratification explicit.",
        "deferred_or_open_items": [],
    }


# ---------------------------------------------------------------------------
# AC-2 — commit requires prior ratification
# ---------------------------------------------------------------------------


class TestCommitRequiresPriorRatification(unittest.TestCase):
    """Per AC-2: a closure cannot be committed unless a ratified event
    exists for that closure_id in the ledger. The lifecycle rule is
    literal event-kind lookup — no fuzzy or smart inference."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        # Seed a proposal we'll attempt to commit without ratification.
        result = self.fabric.propose_closure(**_full_proposal_kwargs())
        self.assertTrue(result.get("ok"), "precondition: proposal succeeded")
        self.closure_id = result["closure_id"]

    def test_fabric_has_ratify_closure(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "ratify_closure"),
            "fabric.ratify_closure must exist per §6.2"
        )

    def test_fabric_has_commit_closure(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "commit_closure"),
            "fabric.commit_closure must exist per §6.3"
        )

    def test_commit_without_ratification_is_rejected(self) -> None:
        """The load-bearing AC-2 assertion."""
        result = self.fabric.commit_closure(
            workspace_id="ws1",
            closure_id=self.closure_id,
            ratifier="atlas",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "not_ratified")

    def test_ratify_then_commit_succeeds(self) -> None:
        """Sanity: the proposal → ratify → commit path works when followed
        in order."""
        ratify_result = self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=self.closure_id,
            ratifier="atlas",
        )
        self.assertTrue(ratify_result.get("ok"))
        self.assertEqual(ratify_result.get("result_code"), "ratified")

        commit_result = self.fabric.commit_closure(
            workspace_id="ws1",
            closure_id=self.closure_id,
            ratifier="atlas",
        )
        self.assertTrue(commit_result.get("ok"))
        self.assertEqual(commit_result.get("result_code"), "committed")

    def test_ratify_with_empty_ratifier_is_rejected(self) -> None:
        """R+9: model synthesis alone is not a valid authorship basis.
        An empty ratifier is structurally inadequate."""
        result = self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=self.closure_id,
            ratifier="",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "empty_ratifier")


# ---------------------------------------------------------------------------
# Lifecycle is event-derived (§12 handoff note 9)
# ---------------------------------------------------------------------------


class TestLifecycleIsEventDerived(unittest.TestCase):
    """The closure entry has no `state` field. Lifecycle state is
    derived by literal event-kind lookup in the ClosureLedger.

    Allowed: proposed event → state is proposed; ratified after proposed
    → state is ratified; etc.

    NOT allowed: heuristic inference, ambiguous reconstruction, fuzzy
    "smart" lifecycle detection."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

    def test_closure_ledger_module_exists(self) -> None:
        try:
            from torment_service.closure_ledger import (
                ClosureLedger, ClosureEvent,
            )  # noqa: F401
        except ImportError:
            self.fail(
                "torment_service.closure_ledger.{ClosureLedger, ClosureEvent} "
                "must exist per §6.6"
            )

    def test_ledger_records_proposed_event_on_propose(self) -> None:
        result = self.fabric.propose_closure(**_full_proposal_kwargs())
        self.assertTrue(result.get("ok"))
        from torment_service.closure_ledger import ClosureLedger
        ledger = ClosureLedger(data_dir=self.tmp, workspace_id="ws1")
        events = ledger.list_events(closure_id=result["closure_id"])
        proposed = [e for e in events if getattr(e, "kind", None) == "proposed"]
        self.assertEqual(
            len(proposed), 1,
            "exactly one 'proposed' event must exist after propose_closure"
        )

    def test_ledger_records_ratified_event_on_ratify(self) -> None:
        proposal = self.fabric.propose_closure(**_full_proposal_kwargs())
        self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=proposal["closure_id"],
            ratifier="atlas",
        )
        from torment_service.closure_ledger import ClosureLedger
        ledger = ClosureLedger(data_dir=self.tmp, workspace_id="ws1")
        events = ledger.list_events(
            closure_id=proposal["closure_id"], kind="ratified"
        )
        self.assertEqual(len(events), 1)

    def test_ledger_records_committed_event_on_commit(self) -> None:
        proposal = self.fabric.propose_closure(**_full_proposal_kwargs())
        self.fabric.ratify_closure(
            workspace_id="ws1",
            closure_id=proposal["closure_id"],
            ratifier="atlas",
        )
        self.fabric.commit_closure(
            workspace_id="ws1",
            closure_id=proposal["closure_id"],
            ratifier="atlas",
        )
        from torment_service.closure_ledger import ClosureLedger
        ledger = ClosureLedger(data_dir=self.tmp, workspace_id="ws1")
        events = ledger.list_events(
            closure_id=proposal["closure_id"], kind="committed"
        )
        self.assertEqual(len(events), 1)

    def test_ledger_get_latest_event_kind_is_deterministic(self) -> None:
        """The lifecycle-state derivation is literal event-kind lookup,
        not heuristic. After propose → ratify → commit, the latest
        event kind is exactly 'committed'."""
        proposal = self.fabric.propose_closure(**_full_proposal_kwargs())
        self.fabric.ratify_closure(
            workspace_id="ws1", closure_id=proposal["closure_id"],
            ratifier="atlas",
        )
        self.fabric.commit_closure(
            workspace_id="ws1", closure_id=proposal["closure_id"],
            ratifier="atlas",
        )
        from torment_service.closure_ledger import ClosureLedger
        ledger = ClosureLedger(data_dir=self.tmp, workspace_id="ws1")
        latest = ledger.get_latest_event_kind(proposal["closure_id"])
        self.assertEqual(latest, "committed")


# ---------------------------------------------------------------------------
# Negative-space: no shortcuts to bypass ratification
# ---------------------------------------------------------------------------


class TestNoBypassPaths(unittest.TestCase):
    """No alternate fabric methods that bypass ratification. The only
    way to reach 'committed' state is through ratify_closure +
    commit_closure."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)

    def test_no_force_commit_method(self) -> None:
        for forbidden in (
            "force_commit_closure",
            "commit_closure_unsafe",
            "commit_closure_no_ratification",
            "auto_commit_closure",
        ):
            self.assertFalse(
                hasattr(self.fabric, forbidden),
                f"fabric must not expose {forbidden!r}; ratification is "
                "structural per R+7."
            )


if __name__ == "__main__":
    unittest.main()
