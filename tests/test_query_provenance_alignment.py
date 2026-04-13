"""Tests for query doctrinal provenance alignment.

Covers:
  - Truth-table parity: derive_query_provenance_type matches expected
    VALID_SOURCE_TYPES-enforced output for every raw provenance shape.
  - Query uses doctrinal helper (structural import test).
  - Trace matches query derivation (structural import test).
  - Legacy collective mapping: bare "collective" → "collective_echo"
    (not "memory"), confirming the canonical helper fires before the
    vocabulary clamp.
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.scoring import (
    derive_provenance_type,
    derive_query_provenance_type,
)
from torment_service.provenance_v1 import (
    VALID_SOURCE_TYPES,
    SOURCE_MEMORY,
    SOURCE_COLLECTIVE_ECHO,
)


# ---------------------------------------------------------------------------
# Test 1: truth-table parity
# ---------------------------------------------------------------------------

class TestQueryProvenanceTruthTable:
    """Verify derive_query_provenance_type produces the expected value for
    every raw provenance shape in the truth table."""

    CASES = [
        # (raw_provenance, expected_canonical, expected_query)
        # None → None in both
        (None, None, None),
        # Structured dicts — both agree
        ({"source_type": "collective_echo"}, "collective_echo", "collective_echo"),
        ({"source_type": "user_input"}, "user_input", "user_input"),
        ({"source_type": "tool_result", "tool_name": "search"}, "tool_result", "tool_result"),
        ({"source_type": "memory"}, "memory", "memory"),
        ({"source_type": "role_output"}, "role_output", "role_output"),
        ({"source_type": "derived"}, "derived", "derived"),
        ({"source_type": "gate1_unrecoverable"}, "gate1_unrecoverable", "gate1_unrecoverable"),
        # Legacy bare string "collective" → canonical maps to collective_echo,
        # which IS in VALID_SOURCE_TYPES, so query adapter keeps it.
        ("collective", "collective_echo", "collective_echo"),
        # Legacy bare strings that ARE in VALID_SOURCE_TYPES pass through.
        ("user_input", "user_input", "user_input"),
        ("tool_result", "tool_result", "tool_result"),
        ("memory", "memory", "memory"),
        # Legacy bare strings NOT in VALID_SOURCE_TYPES → canonical passes
        # through, but query adapter clamps to SOURCE_MEMORY.
        ("some_unknown_legacy", "some_unknown_legacy", "memory"),
        ("old_format", "old_format", "memory"),
    ]

    def test_truth_table_canonical(self):
        """Canonical derive_provenance_type matches expected for all cases."""
        for raw, expected_canonical, _ in self.CASES:
            result = derive_provenance_type(raw)
            assert result == expected_canonical, (
                f"derive_provenance_type({raw!r}): "
                f"expected {expected_canonical!r}, got {result!r}"
            )

    def test_truth_table_query(self):
        """derive_query_provenance_type matches expected for all cases."""
        for raw, _, expected_query in self.CASES:
            result = derive_query_provenance_type(raw)
            assert result == expected_query, (
                f"derive_query_provenance_type({raw!r}): "
                f"expected {expected_query!r}, got {result!r}"
            )

    def test_query_output_always_in_valid_source_types_or_none(self):
        """Every non-None output of derive_query_provenance_type is in
        VALID_SOURCE_TYPES."""
        for raw, _, _ in self.CASES:
            result = derive_query_provenance_type(raw)
            if result is not None:
                assert result in VALID_SOURCE_TYPES, (
                    f"derive_query_provenance_type({raw!r}) = {result!r} "
                    f"not in VALID_SOURCE_TYPES"
                )


# ---------------------------------------------------------------------------
# Test 2: query uses doctrinal helper (structural)
# ---------------------------------------------------------------------------

class TestQueryUsesDoctrinalHelper:

    def test_query_imports_derive_query_provenance_type(self):
        """fabric.py query path should import derive_query_provenance_type
        from scoring (structural grep-level check)."""
        import inspect
        from torment_service import fabric as fab_mod
        source = inspect.getsource(fab_mod)
        assert "derive_query_provenance_type" in source, (
            "fabric.py should import derive_query_provenance_type from scoring"
        )


# ---------------------------------------------------------------------------
# Test 3: trace matches query derivation (structural)
# ---------------------------------------------------------------------------

class TestTraceMatchesQueryDerivation:

    def test_trace_imports_derive_query_provenance_type(self):
        """fabric.py trace path should also import
        derive_query_provenance_type from scoring."""
        import inspect
        from torment_service import fabric as fab_mod
        source = inspect.getsource(fab_mod)
        # Both query and trace should import the adapter
        count = source.count("derive_query_provenance_type")
        assert count >= 2, (
            f"Expected derive_query_provenance_type imported at least twice "
            f"(query + trace), found {count} occurrences"
        )


# ---------------------------------------------------------------------------
# Test 4: legacy collective mapping
# ---------------------------------------------------------------------------

class TestLegacyCollectiveMapping:

    def test_legacy_collective_maps_to_collective_echo_not_memory(self):
        """The bare string 'collective' must map to 'collective_echo' in
        query context, NOT to 'memory'. This confirms the canonical helper
        normalizes before the vocabulary clamp fires."""
        result = derive_query_provenance_type("collective")
        assert result == SOURCE_COLLECTIVE_ECHO, (
            f"'collective' should map to '{SOURCE_COLLECTIVE_ECHO}', "
            f"got {result!r}"
        )
        # And it should NOT be SOURCE_MEMORY
        assert result != SOURCE_MEMORY, (
            f"'collective' must not be clamped to '{SOURCE_MEMORY}'"
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_query_provenance_alignment_tests():
    """Run all query provenance alignment tests."""
    tests = [
        ("TT.1 Truth table — canonical",
         TestQueryProvenanceTruthTable().test_truth_table_canonical),
        ("TT.2 Truth table — query adapter",
         TestQueryProvenanceTruthTable().test_truth_table_query),
        ("TT.3 Query output always in VALID_SOURCE_TYPES or None",
         TestQueryProvenanceTruthTable().test_query_output_always_in_valid_source_types_or_none),
        ("QRY.1 Query imports doctrinal helper",
         TestQueryUsesDoctrinalHelper().test_query_imports_derive_query_provenance_type),
        ("TRC.1 Trace imports doctrinal helper",
         TestTraceMatchesQueryDerivation().test_trace_imports_derive_query_provenance_type),
        ("COL.1 Legacy collective → collective_echo (not memory)",
         TestLegacyCollectiveMapping().test_legacy_collective_maps_to_collective_echo_not_memory),
    ]

    passed = 0
    failed = 0
    print("\n--- Query Provenance Alignment Tests ---")
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
            passed += 1
        except Exception:
            print(f"  FAIL: {name}")
            traceback.print_exc()
            failed += 1

    return passed, failed


if __name__ == "__main__":
    p, f = run_query_provenance_alignment_tests()
    print(f"\nQuery Provenance Alignment: {p} passed, {f} failed")
    if f > 0:
        exit(1)
