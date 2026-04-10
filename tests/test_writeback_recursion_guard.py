# tests/test_writeback_recursion_guard.py
"""
Unit tests for cognition.recursion_guard and ProvenanceV1.normalize_parent.

These tests intentionally avoid importing cognition.pipeline (which drags in
fastapi and the full cognition stack). The guard is designed as a pure
function over a lookup_fn so it can be exercised in isolation — that is the
shape the tests depend on.

Covers step 5 of the v2.4.x tactical provenance pass. See
docs/RECURSION_SAFETY_POLICY_v2.4.x.md and
docs/RECURSION_GUARD_TUNING_v2.4.x.md for policy + tuning context.
"""
from __future__ import annotations

import unittest
from typing import Any, Dict, List, Optional

from cognition.recursion_guard import (
    recursion_guard_check,
    REASON_UNKNOWN_PARENT,
    REASON_ARCHIVIST_BLOCKED,
    REASON_COLLECTIVE_ECHO,
    REASON_DERIVED,
    REASON_UNSAFE_SOURCE_TYPE,
    REASON_DEPTH_EXCEEDED,
    REASON_MALFORMED_ROLE_OUT,
)
from torment_service.provenance_v1 import ProvenanceV1, SOURCE_MEMORY


# ── Test helpers ────────────────────────────────────────────────────

def make_payload(
    source_type: str,
    parent_eids: Optional[List[int]] = None,
    source_role: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a minimal stored payload with a normalized provenance dict."""
    prov: Dict[str, Any] = {"source_type": source_type}
    if parent_eids is not None:
        prov["parent_eids"] = parent_eids
    if source_role is not None:
        prov["source_role"] = source_role
    if notes is not None:
        prov["notes"] = notes
    return {"eid": 0, "provenance": prov}


def make_lookup(corpus: Dict[int, Any]):
    """Return a lookup_fn closed over a fixed eid→payload dict."""
    def _lookup(ws_id: str, ag_id: str, eid: int):
        return corpus.get(eid)
    return _lookup


# ── normalize_parent unit tests ─────────────────────────────────────

class TestNormalizeParent(unittest.TestCase):
    """ProvenanceV1.normalize_parent: four-shape contract + fail-closed."""

    def test_none_returns_none(self):
        self.assertIsNone(ProvenanceV1.normalize_parent(None))

    def test_legacy_bare_string_normalizes_to_memory(self):
        out = ProvenanceV1.normalize_parent("collective")
        self.assertIsNotNone(out)
        self.assertEqual(out["source_type"], SOURCE_MEMORY)
        self.assertIn("legacy_bare_string", out["notes"])
        self.assertIn("collective", out["notes"])

    def test_valid_dict_passes_through(self):
        d = {"source_type": "memory", "parent_eids": [1, 2]}
        out = ProvenanceV1.normalize_parent(d)
        self.assertEqual(out, d)

    def test_dict_missing_source_type_returns_none(self):
        # Critical fail-closed case: malformed shape must not crash.
        self.assertIsNone(ProvenanceV1.normalize_parent({}))
        self.assertIsNone(ProvenanceV1.normalize_parent({"notes": "orphan"}))

    def test_dict_with_invalid_source_type_returns_none(self):
        # Undeclared vocabulary is rejected, including the eliminated
        # legacy_string pseudo-type from step 2.
        self.assertIsNone(
            ProvenanceV1.normalize_parent({"source_type": "legacy_string"})
        )
        self.assertIsNone(
            ProvenanceV1.normalize_parent({"source_type": "unknown_new_type"})
        )

    def test_provenancev1_instance_is_serialized(self):
        p = ProvenanceV1.for_user_ingest()
        out = ProvenanceV1.normalize_parent(p)
        self.assertIsInstance(out, dict)
        self.assertEqual(out["source_type"], "user_input")

    def test_non_provenance_values_return_none(self):
        for val in (42, 3.14, [1, 2], ("a",), object()):
            self.assertIsNone(ProvenanceV1.normalize_parent(val))


# ── recursion_guard_check tests ─────────────────────────────────────

class TestRecursionGuardBasics(unittest.TestCase):
    """Trivial cases: empty seeds, no lookup, unknown parent."""

    def test_no_parent_eids_admits(self):
        ok, reason = recursion_guard_check(
            seed_eids=[],
            lookup_fn=None,
            workspace_id="ws",
            agent_id="ag",
        )
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_no_lookup_fn_with_parents_rejects(self):
        ok, reason = recursion_guard_check(
            seed_eids=[1],
            lookup_fn=None,
            workspace_id="ws",
            agent_id="ag",
        )
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_UNKNOWN_PARENT)

    def test_lookup_returns_none_rejects(self):
        lookup = make_lookup({})  # eid 1 not present
        ok, reason = recursion_guard_check([1], lookup, "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_UNKNOWN_PARENT)

    def test_lookup_raises_rejects(self):
        def bad_lookup(ws, ag, eid):
            raise RuntimeError("db down")
        ok, reason = recursion_guard_check([1], bad_lookup, "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_UNKNOWN_PARENT)


class TestRecursionGuardCleanChains(unittest.TestCase):
    """Chains that MUST be admitted."""

    def test_single_user_input_parent_admits(self):
        corpus = {1: make_payload("user_input")}
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertTrue(ok, msg=f"rejected: {reason}")

    def test_single_tool_result_parent_admits(self):
        corpus = {1: make_payload("tool_result")}
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertTrue(ok, msg=f"rejected: {reason}")

    def test_three_hop_memory_chain_admits(self):
        # depth=1 memory → depth=2 memory → depth=3 memory (terminal, no parents)
        corpus = {
            1: make_payload("memory", parent_eids=[2]),
            2: make_payload("memory", parent_eids=[3]),
            3: make_payload("memory", parent_eids=[]),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertTrue(ok, msg=f"rejected: {reason}")

    def test_non_archivist_role_output_admitted_in_walk(self):
        # Step 5 policy: non-archivist role_output is admissible inside
        # the walked window. Preserves the writeback lane under the
        # current model; archivist remains the real blocker.
        corpus = {
            1: make_payload(
                "role_output",
                source_role="skeptic",
                parent_eids=[2],
            ),
            2: make_payload("user_input"),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertTrue(ok, msg=f"rejected: {reason}")


class TestRecursionGuardRejections(unittest.TestCase):
    """Chains that MUST be rejected."""

    def test_archivist_direct_parent_rejects(self):
        corpus = {
            1: make_payload(
                "role_output",
                source_role="archivist_writeback",
            ),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_ARCHIVIST_BLOCKED)

    def test_archivist_two_hops_back_rejects(self):
        corpus = {
            1: make_payload("memory", parent_eids=[2]),
            2: make_payload(
                "role_output",
                source_role="archivist_writeback",
                parent_eids=[],
            ),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_ARCHIVIST_BLOCKED)

    def test_collective_echo_direct_parent_rejects(self):
        corpus = {1: make_payload("collective_echo")}
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_COLLECTIVE_ECHO)

    def test_collective_echo_two_hops_back_rejects(self):
        # The laundering case the step-4 RSP exclusion documents:
        # a clean direct parent cannot launder a collective ancestor.
        corpus = {
            1: make_payload("memory", parent_eids=[2]),
            2: make_payload("collective_echo", parent_eids=[]),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_COLLECTIVE_ECHO)

    def test_derived_anywhere_rejects(self):
        # SOURCE_DERIVED is deferred vocabulary — never ancestry-admissible.
        corpus = {
            1: make_payload("memory", parent_eids=[2]),
            2: make_payload("derived", parent_eids=[]),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_DERIVED)

    def test_malformed_dict_missing_source_type_rejects_cleanly(self):
        # Must not raise AttributeError or similar.
        corpus = {1: {"eid": 1, "provenance": {"notes": "orphan"}}}
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_UNKNOWN_PARENT)

    def test_legacy_bare_string_parent_does_not_crash(self):
        # The step-5 regression: previously `parent_prov.get("source_role")`
        # on a raw str raised AttributeError. After normalization, the bare
        # string becomes {"source_type": "memory", ...} and is ADMITTED,
        # because "memory" is a safe source_type.
        corpus = {1: {"eid": 1, "provenance": "collective"}}
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertTrue(ok, msg=f"rejected: {reason}")

    def test_role_output_missing_source_role_rejects(self):
        # Malformed role_output (no source_role) — ProvenanceV1 normally
        # rejects this at construction, but an old corpus entry could
        # still reach the guard. Must fail closed, not crash.
        corpus = {1: make_payload("role_output", source_role=None)}
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_MALFORMED_ROLE_OUT)


class TestRecursionGuardDepthCap(unittest.TestCase):
    """Depth-cap = 3 boundary conditions."""

    def test_four_hop_chain_rejects(self):
        # 1 → 2 → 3 → 4 → 5, depth 4 exceeds the cap.
        # At the node at depth 3 (eid=3), parent_eids=[4] is present
        # but cannot be verified within the window → reject.
        corpus = {
            1: make_payload("memory", parent_eids=[2]),
            2: make_payload("memory", parent_eids=[3]),
            3: make_payload("memory", parent_eids=[4]),
            4: make_payload("memory", parent_eids=[5]),
            5: make_payload("memory", parent_eids=[]),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_DEPTH_EXCEEDED)

    def test_three_hop_chain_terminating_admits(self):
        # Exactly at the cap: depth-3 node has no parents, corridor clean.
        corpus = {
            1: make_payload("memory", parent_eids=[2]),
            2: make_payload("memory", parent_eids=[3]),
            3: make_payload("memory", parent_eids=[]),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        self.assertTrue(ok, msg=f"rejected: {reason}")

    def test_cycle_does_not_loop(self):
        # A → B → A cycle. Visited set must prevent infinite recursion.
        corpus = {
            1: make_payload("memory", parent_eids=[2]),
            2: make_payload("memory", parent_eids=[1]),
        }
        ok, reason = recursion_guard_check([1], make_lookup(corpus), "ws", "ag")
        # Both nodes are memory → admitted; the walk terminates because
        # each eid is only visited once.
        self.assertTrue(ok, msg=f"rejected: {reason}")


if __name__ == "__main__":
    unittest.main()
