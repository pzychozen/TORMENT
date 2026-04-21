# tests/test_closure_shape_boundary.py
"""
T1 — AC-1: closure shape validation.

Covers acceptance criteria from BLOCK_C_DESIGN.md §4 AC-1:

    fabric.propose_closure(...) succeeds only when every §5-required
    field is supplied. deferred_or_open_items specifically must exist
    (empty allowed; absent rejected). Missing any other required field
    → rejected with a named result_code.

Design references:
    - BLOCK_C_DESIGN.md §4 AC-1
    - BLOCK_C_DESIGN.md §5.2 (ClosureEntry shape)
    - BLOCK_C_DESIGN.md §6.1 (propose_closure)
    - BLOCK_C_DESIGN.md §12 handoff note 3 (lifecycle stages NOT separate ontologies)
    - PRE_BLOCK_C_PRECONDITIONS.md §5 (closure object minimum shape)
    - PRE_BLOCK_C_PRECONDITIONS.md R+10 (deferred_or_open_items required)

These tests FAIL against current code (pre-implementation). They pass once:
    - torment_service.closure_memory.ClosureEntry exists (single class)
    - torment_service.closure_memory.ClosureStore exists
    - fabric.propose_closure exists with the specified envelope
    - The required-field validation lands per §6.1
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric


# ---------------------------------------------------------------------------
# Negative-space: lifecycle stages are not separate object ontologies
# (Watch-item from analysis ratification + design §12 handoff note 3.)
# ---------------------------------------------------------------------------


class TestSingleClosureEntryClass(unittest.TestCase):
    """No ClosureProposal / RatifiedClosure / CommittedClosure /
    RevisedClosure sibling classes. The lifecycle is a property of the
    ledger, not separate object families."""

    def test_closure_memory_module_exposes_single_entry_class(self) -> None:
        try:
            from torment_service.closure_memory import ClosureEntry  # noqa: F401
        except ImportError:
            self.fail(
                "torment_service.closure_memory.ClosureEntry must exist"
            )

    def test_no_sibling_proposal_class(self) -> None:
        """Lifecycle-stage class families are forbidden per §12 handoff
        note 3. The state is derived from ClosureLedger events."""
        from torment_service import closure_memory as cm
        for forbidden in (
            "ClosureProposal",
            "RatifiedClosure",
            "CommittedClosure",
            "RevisedClosure",
            "ClosureCommit",
            "ClosureRatification",
            "ClosureRevision",
        ):
            self.assertFalse(
                hasattr(cm, forbidden),
                f"closure_memory must not declare {forbidden!r}; "
                "lifecycle stages live in ClosureLedger events, not in "
                "separate object classes (§12 handoff note 3)."
            )

    def test_closure_entry_has_no_state_field(self) -> None:
        """Per §5.4: no `state` field on the entry. Lifecycle state
        is derived from ledger events for that closure_id."""
        from torment_service.closure_memory import ClosureEntry
        # Use dataclass introspection if it's a dataclass; otherwise
        # check for attribute on instance with all required args.
        forbidden_fields = ("state", "lifecycle_state", "is_committed",
                            "is_ratified", "ratified")
        if hasattr(ClosureEntry, "__dataclass_fields__"):
            fields = set(ClosureEntry.__dataclass_fields__.keys())
            for f in forbidden_fields:
                self.assertNotIn(
                    f, fields,
                    f"ClosureEntry must not have field {f!r}; lifecycle "
                    "state is event-derived, not stored on the entry."
                )


# ---------------------------------------------------------------------------
# AC-1: required fields — fabric.propose_closure
# ---------------------------------------------------------------------------


def _full_proposal_kwargs() -> dict:
    """Helper: returns a complete-and-valid set of kwargs for propose_closure."""
    return {
        "workspace_id": "ws1",
        "arc_name": "block-c-test-arc",
        "arc_kind": "feature",                # free-form per D.4
        "scope": [1, 2, 3],                   # explicit eid list per D.3
        "what_it_was": "A small test arc for proposing a closure.",
        "what_worked": "The proposal validation worked.",
        "what_surprised": "Nothing surprising in this test.",
        "what_to_carry_forward": "Keep validation strict.",
        "deferred_or_open_items": [],         # empty IS valid
    }


class TestProposeClosureRequiresAllFields(unittest.TestCase):
    """Each §5-required field, when missing, is rejected with a
    named result_code. deferred_or_open_items absent is REJECTED;
    deferred_or_open_items present-but-empty is OK."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

    def test_fabric_has_propose_closure(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "propose_closure"),
            "fabric.propose_closure must exist per §6.1"
        )

    def test_complete_proposal_succeeds(self) -> None:
        result = self.fabric.propose_closure(**_full_proposal_kwargs())
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "proposed")
        self.assertTrue(result.get("closure_id"))
        self.assertTrue(result.get("version_id"))

    def test_empty_deferred_or_open_items_is_OK(self) -> None:
        """deferred_or_open_items=[] is valid. R+10 says it must be
        PRESENT, not non-empty."""
        kwargs = _full_proposal_kwargs()
        kwargs["deferred_or_open_items"] = []
        result = self.fabric.propose_closure(**kwargs)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "proposed")

    def test_missing_arc_name_is_rejected(self) -> None:
        kwargs = _full_proposal_kwargs()
        kwargs["arc_name"] = ""
        result = self.fabric.propose_closure(**kwargs)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_required_field")

    def test_missing_arc_kind_is_rejected(self) -> None:
        kwargs = _full_proposal_kwargs()
        kwargs["arc_kind"] = ""
        result = self.fabric.propose_closure(**kwargs)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_required_field")

    def test_missing_scope_is_rejected(self) -> None:
        kwargs = _full_proposal_kwargs()
        kwargs["scope"] = []
        result = self.fabric.propose_closure(**kwargs)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_required_field")

    def test_missing_what_it_was_is_rejected(self) -> None:
        kwargs = _full_proposal_kwargs()
        kwargs["what_it_was"] = ""
        result = self.fabric.propose_closure(**kwargs)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_required_field")

    def test_missing_what_worked_is_rejected(self) -> None:
        kwargs = _full_proposal_kwargs()
        kwargs["what_worked"] = ""
        result = self.fabric.propose_closure(**kwargs)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_required_field")

    def test_missing_what_surprised_is_rejected(self) -> None:
        kwargs = _full_proposal_kwargs()
        kwargs["what_surprised"] = ""
        result = self.fabric.propose_closure(**kwargs)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_required_field")

    def test_missing_what_to_carry_forward_is_rejected(self) -> None:
        kwargs = _full_proposal_kwargs()
        kwargs["what_to_carry_forward"] = ""
        result = self.fabric.propose_closure(**kwargs)
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_required_field")

    def test_absent_deferred_or_open_items_is_rejected(self) -> None:
        """R+10 specifically: deferred_or_open_items must EXIST. Absent
        (None) is NOT the same as empty list ([])."""
        kwargs = _full_proposal_kwargs()
        kwargs["deferred_or_open_items"] = None
        result = self.fabric.propose_closure(**kwargs)
        self.assertFalse(result.get("ok"))
        # R+10 may produce missing_required_field or a deferred-specific
        # code; both are acceptable mismatch results per the design.
        self.assertIn(
            result.get("result_code"),
            ("missing_required_field", "missing_deferred_or_open_items"),
        )


# ---------------------------------------------------------------------------
# Negative-space: ClosureStore exists with the expected shape
# ---------------------------------------------------------------------------


class TestClosureStorePresence(unittest.TestCase):
    """Block C produces a ClosureStore parallel to ReferenceStore /
    EnvironmentStore, per D.1."""

    def test_closure_store_class_exists(self) -> None:
        try:
            from torment_service.closure_memory import ClosureStore  # noqa: F401
        except ImportError:
            self.fail(
                "torment_service.closure_memory.ClosureStore must exist "
                "per BLOCK_C_DESIGN §6.5"
            )

    def test_no_closure_in_memory_graph(self) -> None:
        """memory_graph.spawn_memory must not be a closure write path
        (R+3 / R+11 / preconditions §11)."""
        from torment_service import memory_graph as mg
        # Verify spawn_memory signature does not have closure-specific args
        import inspect
        sig = inspect.signature(mg.MemoryGraph.spawn_memory)
        param_names = set(sig.parameters.keys())
        for forbidden in ("closure_id", "arc_name", "is_closure"):
            self.assertNotIn(
                forbidden, param_names,
                f"memory_graph.spawn_memory must not accept {forbidden!r}; "
                "closure has its own ClosureStore."
            )


if __name__ == "__main__":
    unittest.main()
