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


# ---------------------------------------------------------------------------
# v0.2.4-A1: id_field parameterizes the identity key on excluded records
# so archive hits (chunk_id, not eid) can use the same canonical helper.
# Default "eid" must preserve all legacy contracts; existing test classes
# above implicitly cover that path because none pass id_field. Tests below
# add the new mode and the regression that the default really is "eid".
# ---------------------------------------------------------------------------

def _archive_hit(chunk_id: str, governance: dict = None) -> dict:
    """Build a minimal archive-hit-shaped dict for tests.

    Archive hits carry chunk_id and doc_id rather than eid (matches the
    shape returned by ArchiveStore.retrieve()).
    """
    h = {
        "chunk_id": chunk_id,
        "doc_id": f"doc_for_{chunk_id}",
        "score": 0.5,
        "text": f"archive chunk {chunk_id}",
    }
    if governance is not None:
        h["governance"] = governance
    return h


class TestFilterLLMFacing_IdFieldParam(unittest.TestCase):
    def test_default_id_field_is_eid(self):
        """Regression: default id_field must remain "eid" so core-memory
        call sites that already exist (e.g. fabric.query at
        fabric.py:4156) keep emitting eid-shaped excluded records.
        """
        h = _hit(7, {"non_shareable": True})
        out = filter_llm_facing([h], surface=SURFACE_LLM_CONTEXT)
        self.assertEqual(len(out["excluded"]), 1)
        self.assertIn("eid", out["excluded"][0])
        self.assertEqual(out["excluded"][0]["eid"], 7)
        self.assertNotIn("chunk_id", out["excluded"][0])

    def test_chunk_id_mode_emits_chunk_id_key(self):
        """With id_field="chunk_id", excluded records key on chunk_id."""
        h = _archive_hit("abc123_chunk_0000", {"non_shareable": True})
        out = filter_llm_facing(
            [h], surface=SURFACE_LLM_CONTEXT, id_field="chunk_id"
        )
        self.assertEqual(len(out["excluded"]), 1)
        self.assertIn("chunk_id", out["excluded"][0])
        self.assertEqual(out["excluded"][0]["chunk_id"], "abc123_chunk_0000")
        self.assertNotIn("eid", out["excluded"][0])
        self.assertEqual(
            out["excluded"][0]["excluded_reason"], "non_shareable"
        )

    def test_chunk_id_mode_with_collective_export_blocked(self):
        """Surface-conditional rule still fires under chunk_id mode."""
        h = _archive_hit(
            "ch_xyz", {"collective_export_blocked": True}
        )
        out = filter_llm_facing(
            [h],
            surface=SURFACE_COLLECTIVE_EXPORT,
            id_field="chunk_id",
        )
        self.assertEqual(out["results"], [])
        self.assertEqual(len(out["excluded"]), 1)
        self.assertEqual(out["excluded"][0]["chunk_id"], "ch_xyz")
        self.assertEqual(
            out["excluded"][0]["excluded_reason"],
            "collective_export_blocked",
        )

    def test_chunk_id_mode_passes_governance_less_chunk(self):
        """Default-pass behavior preserved under chunk_id mode: an
        archive hit with no governance field surfaces in results, not
        in excluded.
        """
        h = _archive_hit("ch_clean")
        out = filter_llm_facing(
            [h], surface=SURFACE_LLM_CONTEXT, id_field="chunk_id"
        )
        self.assertEqual(out["results"], [h])
        self.assertEqual(out["excluded"], [])

    def test_chunk_id_mode_mixed_batch_partitions_correctly(self):
        """Realistic archive-batch shape: some chunks have governance,
        some don't. Filter partitions by non_shareable cleanly.
        """
        hits = [
            _archive_hit("ch_1"),  # no governance → pass
            _archive_hit("ch_2", {"non_shareable": True}),  # excluded
            _archive_hit("ch_3", {"non_shareable": False}),  # pass
            _archive_hit("ch_4", {"non_shareable": True}),  # excluded
        ]
        out = filter_llm_facing(
            hits, surface=SURFACE_LLM_CONTEXT, id_field="chunk_id"
        )
        self.assertEqual(
            [h["chunk_id"] for h in out["results"]],
            ["ch_1", "ch_3"],
        )
        self.assertEqual(
            sorted(e["chunk_id"] for e in out["excluded"]),
            ["ch_2", "ch_4"],
        )

    def test_chunk_id_mode_missing_id_returns_none_value(self):
        """If the configured id_field is absent from the hit, the
        excluded record's identity slot is None — same shape contract
        as legacy missing-eid behavior (test_hit_without_eid above).
        """
        h = {
            "doc_id": "doc_x",  # no chunk_id, no eid
            "score": 0.5,
            "governance": {"non_shareable": True},
        }
        out = filter_llm_facing(
            [h], surface=SURFACE_LLM_CONTEXT, id_field="chunk_id"
        )
        self.assertEqual(len(out["excluded"]), 1)
        self.assertIsNone(out["excluded"][0]["chunk_id"])

    def test_arbitrary_id_field_works(self):
        """Smoke test: id_field is generic, not chunk_id-specific.
        Documents the contract — any string key on the hit dict can be
        used as the identity slot for excluded records.
        """
        h = {
            "custom_id": "anything-42",
            "score": 0.5,
            "governance": {"non_shareable": True},
        }
        out = filter_llm_facing(
            [h], surface=SURFACE_LLM_CONTEXT, id_field="custom_id"
        )
        self.assertEqual(len(out["excluded"]), 1)
        self.assertEqual(out["excluded"][0]["custom_id"], "anything-42")

    def test_id_field_does_not_alter_results_shape(self):
        """Load-bearing: id_field changes the EXCLUDED record key only.
        It MUST NOT alter the hits surfaced in results — results are
        the original hit dicts, unchanged.
        """
        h_pass = _archive_hit("ch_pass")
        h_excl = _archive_hit("ch_excl", {"non_shareable": True})
        out = filter_llm_facing(
            [h_pass, h_excl],
            surface=SURFACE_LLM_CONTEXT,
            id_field="chunk_id",
        )
        # results is the original hit dict, unchanged.
        self.assertEqual(out["results"], [h_pass])
        # excluded record uses chunk_id key.
        self.assertEqual(out["excluded"][0]["chunk_id"], "ch_excl")


if __name__ == "__main__":
    unittest.main()
