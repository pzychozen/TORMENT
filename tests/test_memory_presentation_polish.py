"""Tests for memory presentation polish — visible classification consistency.

Covers:
  - /debug/provenance output includes provenance_type
  - MCP provenance resource includes provenance_type
  - Index recent/motif retain provenance_type (regression guard)
  - Retrieve context blocks retain provenance_type (regression guard)
  - All surfaces use the canonical derive_provenance_type helper
"""
import os
import shutil
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.scoring import derive_provenance_type


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp():
    return tempfile.mkdtemp(prefix="torment_presentation_test_")


# ---------------------------------------------------------------------------
# Test 1: debug provenance output includes visible classification
# ---------------------------------------------------------------------------

class TestDebugProvenanceOutput:

    def test_debug_provenance_output_includes_provenance_type(self):
        """Verify /debug/provenance memory entries carry provenance_type.

        We test the entry-building logic rather than the full HTTP route
        to avoid requiring a running server.  The pattern is identical to
        what the route builds per-entity.
        """
        # Simulate what /debug/provenance does for each entity
        test_cases = [
            # (raw_provenance, expected_provenance_type)
            ({"source_type": "collective_echo", "agent_id": "other"}, "collective_echo"),
            ({"source_type": "user_input"}, "user_input"),
            ({"source_type": "tool_result", "tool_name": "search"}, "tool_result"),
            ("collective", "collective_echo"),
            (None, None),
        ]

        for raw_prov, expected_type in test_cases:
            # Derive classification BEFORE legacy normalization (matches app.py logic)
            prov_type = derive_provenance_type(raw_prov)

            # Legacy normalization (display dict)
            prov = raw_prov
            if prov and not isinstance(prov, dict):
                prov = {"source_type": "memory", "notes": f"legacy={prov!r}"}

            entry = {
                "eid": 1,
                "provenance_type": prov_type,
                "provenance": prov,
            }

            assert entry["provenance_type"] == expected_type, (
                f"For raw provenance {raw_prov!r}: "
                f"expected provenance_type={expected_type!r}, "
                f"got {entry['provenance_type']!r}"
            )


# ---------------------------------------------------------------------------
# Test 2: MCP provenance resource includes visible classification
# ---------------------------------------------------------------------------

class TestMCPProvenancePresentation:

    def test_mcp_provenance_resource_includes_provenance_type(self):
        """Verify MCP provenance resource entries carry provenance_type.

        Same derivation pattern as /debug/provenance — both use
        derive_provenance_type before legacy normalization.
        """
        # Simulate the MCP resource entry-building for a collective echo
        raw_prov = {"source_type": "collective_echo", "agent_id": "other"}
        prov_type = derive_provenance_type(raw_prov)

        entry = {
            "eid": 42,
            "provenance_type": prov_type,
            "provenance": raw_prov,
        }
        assert entry["provenance_type"] == "collective_echo"

        # And for a legacy string
        raw_prov_legacy = "collective"
        prov_type_legacy = derive_provenance_type(raw_prov_legacy)

        entry_legacy = {
            "eid": 43,
            "provenance_type": prov_type_legacy,
            "provenance": {"source_type": "memory", "notes": "legacy"},
        }
        assert entry_legacy["provenance_type"] == "collective_echo"


# ---------------------------------------------------------------------------
# Test 3: index recent output retains provenance_type (regression guard)
# ---------------------------------------------------------------------------

class TestIndexRecentRetainsProvenanceType:

    def test_index_recent_output_retains_provenance_type(self):
        """Regression: get_recent_memories still returns provenance_type."""
        from torment_service.sqlite_index import IndexManager

        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            idx.index_node(1, {
                "type": "episode",
                "summary": "Collective echo test",
                "provenance": {"source_type": "collective_echo"},
            })
            idx.index_node(2, {
                "type": "episode",
                "summary": "User input test",
                "provenance": {"source_type": "user_input"},
            })
            results = idx.get_recent_memories(limit=10)
            for r in results:
                assert "provenance_type" in r, (
                    f"Missing provenance_type in recent result: {r}"
                )
            prov_map = {r["eid"]: r["provenance_type"] for r in results}
            assert prov_map[1] == "collective_echo"
            assert prov_map[2] == "user_input"
            idx.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test 4: retrieve context block retains provenance_type (regression guard)
# ---------------------------------------------------------------------------

class TestRetrieveContextBlockRetainsProvenanceType:

    def test_retrieve_context_block_retains_provenance_type(self):
        """Regression: _hit_to_block preserves provenance_type in metadata."""
        from torment_service.retrieval_assembler import _hit_to_block

        hit = {
            "text": "Some memory text",
            "score": 0.85,
            "provenance_type": "collective_echo",
            "provenance": {"source_type": "collective_echo"},
        }
        block = _hit_to_block(hit, "memory")
        meta = block.metadata or {}
        assert meta.get("provenance_type") == "collective_echo", (
            f"ContextBlock metadata missing/wrong provenance_type: {meta}"
        )


# ---------------------------------------------------------------------------
# Test 5: visible classification uses canonical derivation helper
# ---------------------------------------------------------------------------

class TestCanonicalDerivationConsistency:

    def test_memory_presentation_uses_canonical_provenance_derivation(self):
        """All surfaces should use derive_provenance_type for consistency.

        Structural test: verify derive_provenance_type is the same function
        imported by both app.py and mcp_server.py.
        """
        from torment_service.scoring import derive_provenance_type as scoring_fn
        from torment_service.app import _derive_prov_type as app_fn
        from torment_service.mcp_server import _derive_prov_type as mcp_fn

        assert scoring_fn is app_fn, (
            "app.py._derive_prov_type should be scoring.derive_provenance_type"
        )
        assert scoring_fn is mcp_fn, (
            "mcp_server._derive_prov_type should be scoring.derive_provenance_type"
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_presentation_polish_tests():
    """Run all memory presentation polish tests."""
    tests = [
        ("DBG.1 Debug provenance includes provenance_type",
         TestDebugProvenanceOutput().test_debug_provenance_output_includes_provenance_type),
        ("MCP.1 MCP provenance includes provenance_type",
         TestMCPProvenancePresentation().test_mcp_provenance_resource_includes_provenance_type),
        ("IDX.1 Index recent retains provenance_type",
         TestIndexRecentRetainsProvenanceType().test_index_recent_output_retains_provenance_type),
        ("RTV.1 Retrieve context block retains provenance_type",
         TestRetrieveContextBlockRetainsProvenanceType().test_retrieve_context_block_retains_provenance_type),
        ("CAN.1 Canonical derivation consistency",
         TestCanonicalDerivationConsistency().test_memory_presentation_uses_canonical_provenance_derivation),
    ]

    passed = 0
    failed = 0
    print("\n--- Memory Presentation Polish Tests ---")
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
    p, f = run_presentation_polish_tests()
    print(f"\nPresentation Polish: {p} passed, {f} failed")
    if f > 0:
        exit(1)
