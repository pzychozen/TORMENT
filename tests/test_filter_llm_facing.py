"""
tests/test_filter_llm_facing.py — FILTER-A helper unit tests.

Direct unit tests on torment_service.governance.filter_llm_facing per
docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md §10.2.

The helper is tested in isolation here (no fabric, no live service, no LLM).
End-to-end coverage lives in the substrate-time harness (Phase 0 re-run
after Commit γ wires this helper into the LLM-facing call sites).
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.governance import (
    filter_llm_facing,
    SURFACE_LLM_CONTEXT,
    SURFACE_COLLECTIVE_EXPORT,
    _RAW_HITS_MIN_TRUST,
)


def _hit(eid: int, governance: dict = None) -> dict:
    """Build a minimal memory-hit-shaped dict for tests."""
    h = {"eid": eid, "score": 0.5, "summary": f"memory {eid}"}
    if governance is not None:
        h["governance"] = governance
    return h


# ---------------------------------------------------------------------------
# Basics: empty input, no governance, response shape
# ---------------------------------------------------------------------------

class TestFilterLLMFacing_Basics(unittest.TestCase):
    def test_empty_hits(self):
        out = filter_llm_facing([], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(out, {"results": [], "excluded": []})

    def test_no_governance_field_included(self):
        h = _hit(1)
        out = filter_llm_facing([h], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(out["results"], [h])
        self.assertEqual(out["excluded"], [])

    def test_response_shape_no_raw_hits_key_by_default(self):
        out = filter_llm_facing([_hit(1)], surface=SURFACE_LLM_CONTEXT)
        self.assertNotIn("raw_hits", out)

    def test_response_keys_minimal(self):
        out = filter_llm_facing([_hit(1)], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(set(out.keys()), {"results", "excluded"})


# ---------------------------------------------------------------------------
# Required surface: no default; invalid surface raises
# ---------------------------------------------------------------------------

class TestFilterLLMFacing_RequiredSurface(unittest.TestCase):
    def test_missing_surface_raises_typeerror(self):
        # surface is keyword-only with no default → TypeError when omitted.
        with self.assertRaises(TypeError):
            filter_llm_facing([_hit(1)])  # type: ignore[call-arg]

    def test_invalid_surface_raises_valueerror(self):
        with self.assertRaises(ValueError):
            filter_llm_facing([_hit(1)], surface="unknown_surface")

    def test_none_surface_raises_valueerror(self):
        with self.assertRaises(ValueError):
            filter_llm_facing([_hit(1)], surface=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# non_shareable: universal LLM-facing exclusion (both surfaces)
# ---------------------------------------------------------------------------

class TestFilterLLMFacing_NonShareable(unittest.TestCase):
    def test_excluded_from_llm_context(self):
        h = _hit(4, {"non_shareable": True})
        out = filter_llm_facing([h], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(out["results"], [])
        self.assertEqual(len(out["excluded"]), 1)
        self.assertEqual(out["excluded"][0]["eid"], 4)
        self.assertEqual(out["excluded"][0]["excluded_reason"], "non_shareable")

    def test_excluded_from_collective_export(self):
        h = _hit(4, {"non_shareable": True})
        out = filter_llm_facing([h], surface=SURFACE_COLLECTIVE_EXPORT)
        self.assertEqual(out["results"], [])
        self.assertEqual(out["excluded"][0]["excluded_reason"], "non_shareable")

    def test_non_shareable_false_included(self):
        h = _hit(3, {"non_shareable": False})
        out = filter_llm_facing([h], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(out["results"], [h])
        self.assertEqual(out["excluded"], [])


# ---------------------------------------------------------------------------
# collective_export_blocked: surface-conditional (load-bearing)
# ---------------------------------------------------------------------------

class TestFilterLLMFacing_CollectiveExportBlocked(unittest.TestCase):
    def test_filters_on_collective_export_surface(self):
        h = _hit(7, {"collective_export_blocked": True})
        out = filter_llm_facing([h], surface=SURFACE_COLLECTIVE_EXPORT)
        self.assertEqual(out["results"], [])
        self.assertEqual(
            out["excluded"][0]["excluded_reason"],
            "collective_export_blocked",
        )

    def test_PASSES_on_llm_context_surface(self):
        """Load-bearing: a memory blocked from collective export is still
        shareable to its own agent's LLM context. Not over-filtered.

        Per FILTER-A §7: collective_export_blocked means 'do not emit across
        the agent boundary in collective surfaces.' It does NOT mean 'hide
        from this agent itself.' Filtering it from llm_context would treat
        the flag as if it meant non_shareable. It does not.
        """
        h = _hit(7, {"collective_export_blocked": True})
        out = filter_llm_facing([h], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(out["results"], [h])
        self.assertEqual(out["excluded"], [])


# ---------------------------------------------------------------------------
# Combined flags: precedence consistency
# ---------------------------------------------------------------------------

class TestFilterLLMFacing_CombinedFlags(unittest.TestCase):
    def test_both_flags_excluded_on_collective_export(self):
        h = _hit(11, {"non_shareable": True, "collective_export_blocked": True})
        out = filter_llm_facing([h], surface=SURFACE_COLLECTIVE_EXPORT)
        self.assertEqual(out["results"], [])
        # non_shareable check fires first; reason recorded reflects that.
        # If implementation order changes, update this assertion deliberately.
        self.assertEqual(out["excluded"][0]["excluded_reason"], "non_shareable")

    def test_both_flags_excluded_on_llm_context(self):
        h = _hit(11, {"non_shareable": True, "collective_export_blocked": True})
        out = filter_llm_facing([h], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(out["results"], [])
        self.assertEqual(out["excluded"][0]["excluded_reason"], "non_shareable")

    def test_mixed_batch_partitions_correctly(self):
        hits = [
            _hit(1),  # ordinary
            _hit(2, {"non_shareable": True}),  # excluded both surfaces
            _hit(3, {"collective_export_blocked": True}),  # surface-conditional
            _hit(4),  # ordinary
        ]

        out_llm = filter_llm_facing(hits, surface=SURFACE_LLM_CONTEXT)
        self.assertEqual([h["eid"] for h in out_llm["results"]], [1, 3, 4])
        self.assertEqual([e["eid"] for e in out_llm["excluded"]], [2])

        out_col = filter_llm_facing(hits, surface=SURFACE_COLLECTIVE_EXPORT)
        self.assertEqual([h["eid"] for h in out_col["results"]], [1, 4])
        self.assertEqual(
            sorted(e["eid"] for e in out_col["excluded"]),
            [2, 3],
        )


# ---------------------------------------------------------------------------
# Operator-only raw_hits: additive, never modifies results
# ---------------------------------------------------------------------------

class TestFilterLLMFacing_RawHitsAuthorization(unittest.TestCase):
    def test_authorized_includes_raw_key(self):
        hits = [_hit(3), _hit(4, {"non_shareable": True}), _hit(5)]
        out = filter_llm_facing(
            hits,
            surface=SURFACE_LLM_CONTEXT,
            include_raw_hits=True,
            actor="operator",
            trust_tier=_RAW_HITS_MIN_TRUST,
        )
        # results filtered (eid 4 excluded)
        self.assertEqual([h["eid"] for h in out["results"]], [3, 5])
        # raw_hits has the full unfiltered set
        self.assertIn("raw_hits", out)
        self.assertEqual([h["eid"] for h in out["raw_hits"]], [3, 4, 5])
        # excluded recorded
        self.assertEqual([e["eid"] for e in out["excluded"]], [4])

    def test_unauthorized_actor_omits_raw_key(self):
        hits = [_hit(3), _hit(4, {"non_shareable": True})]
        out = filter_llm_facing(
            hits,
            surface=SURFACE_LLM_CONTEXT,
            include_raw_hits=True,
            actor=None,
            trust_tier=_RAW_HITS_MIN_TRUST,
        )
        self.assertNotIn("raw_hits", out)
        self.assertEqual([h["eid"] for h in out["results"]], [3])

    def test_insufficient_trust_omits_raw_key(self):
        hits = [_hit(3), _hit(4, {"non_shareable": True})]
        out = filter_llm_facing(
            hits,
            surface=SURFACE_LLM_CONTEXT,
            include_raw_hits=True,
            actor="operator",
            trust_tier=_RAW_HITS_MIN_TRUST - 0.4,
        )
        self.assertNotIn("raw_hits", out)
        self.assertEqual([h["eid"] for h in out["results"]], [3])

    def test_missing_trust_tier_omits_raw_key(self):
        hits = [_hit(3), _hit(4, {"non_shareable": True})]
        out = filter_llm_facing(
            hits,
            surface=SURFACE_LLM_CONTEXT,
            include_raw_hits=True,
            actor="operator",
            trust_tier=None,
        )
        self.assertNotIn("raw_hits", out)
        self.assertEqual([h["eid"] for h in out["results"]], [3])

    def test_results_invariant_across_modes(self):
        """results MUST be identical whether include_raw_hits is True or False
        (with or without authorization). raw_hits is additive, never a
        replacement for results."""
        hits = [_hit(3), _hit(4, {"non_shareable": True}), _hit(5)]

        default = filter_llm_facing(hits, surface=SURFACE_LLM_CONTEXT)
        raw_authorized = filter_llm_facing(
            hits,
            surface=SURFACE_LLM_CONTEXT,
            include_raw_hits=True,
            actor="operator",
            trust_tier=_RAW_HITS_MIN_TRUST,
        )
        raw_unauthorized = filter_llm_facing(
            hits,
            surface=SURFACE_LLM_CONTEXT,
            include_raw_hits=True,
            actor=None,
            trust_tier=_RAW_HITS_MIN_TRUST,
        )

        self.assertEqual(default["results"], raw_authorized["results"])
        self.assertEqual(default["results"], raw_unauthorized["results"])
        self.assertEqual(default["excluded"], raw_authorized["excluded"])
        self.assertEqual(default["excluded"], raw_unauthorized["excluded"])


# ---------------------------------------------------------------------------
# Defensive inputs: malformed governance, non-dict hits, missing eid
# ---------------------------------------------------------------------------

class TestFilterLLMFacing_DefensiveInputs(unittest.TestCase):
    def test_governance_not_dict_does_not_crash(self):
        h = {"eid": 1, "score": 0.5, "governance": "broken"}
        out = filter_llm_facing([h], surface=SURFACE_LLM_CONTEXT)
        # broken governance → resolve_governance returns defaults → not flagged
        self.assertEqual(out["results"], [h])
        self.assertEqual(out["excluded"], [])

    def test_non_dict_hit_passthrough(self):
        out = filter_llm_facing(["not a dict"], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(out["results"], ["not a dict"])
        self.assertEqual(out["excluded"], [])

    def test_hit_without_eid(self):
        h = {"summary": "no eid", "governance": {"non_shareable": True}}
        out = filter_llm_facing([h], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(out["results"], [])
        self.assertEqual(len(out["excluded"]), 1)
        self.assertIsNone(out["excluded"][0]["eid"])

    def test_hits_list_unmodified(self):
        """The helper must not mutate its input list."""
        hits = [_hit(1), _hit(2, {"non_shareable": True})]
        original = list(hits)
        filter_llm_facing(hits, surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(hits, original)


if __name__ == "__main__":
    unittest.main()
