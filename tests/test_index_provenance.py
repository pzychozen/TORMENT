"""Tests for SQLite index provenance alignment patch.

Covers:
  - derive_provenance_type() canonical helper (scoring.py)
  - index_node() stores provenance_type in core_nodes
  - /recent and /motif/* surfaces return provenance_type
  - rebuild path repopulates provenance_type from canonical payloads
"""
import json
import os
import shutil
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.scoring import derive_provenance_type
from torment_service.sqlite_index import IndexManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp():
    return tempfile.mkdtemp(prefix="torment_idx_prov_test_")


# ---------------------------------------------------------------------------
# Test: derive_provenance_type canonical helper
# ---------------------------------------------------------------------------

class TestDeriveProvenanceType:
    """Unit tests for the canonical provenance derivation rule."""

    def test_structured_collective_echo(self):
        prov = {"source_type": "collective_echo", "agent_id": "other"}
        assert derive_provenance_type(prov) == "collective_echo"

    def test_structured_user_input(self):
        prov = {"source_type": "user_input"}
        assert derive_provenance_type(prov) == "user_input"

    def test_structured_tool_result(self):
        prov = {"source_type": "tool_result", "tool_name": "web_search"}
        assert derive_provenance_type(prov) == "tool_result"

    def test_legacy_collective_string(self):
        assert derive_provenance_type("collective") == "collective_echo"

    def test_legacy_user_input_string(self):
        assert derive_provenance_type("user_input") == "user_input"

    def test_none_provenance(self):
        assert derive_provenance_type(None) is None

    def test_missing_source_type_in_dict(self):
        prov = {"agent_id": "x"}  # no source_type
        assert derive_provenance_type(prov) is None


# ---------------------------------------------------------------------------
# Test: index_node stores provenance_type
# ---------------------------------------------------------------------------

class TestIndexNodeStoresProvenanceType:

    def test_index_node_stores_collective_provenance_type(self):
        """Collective echo provenance → provenance_type='collective_echo' in core_nodes."""
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            ok = idx.index_node(1, {
                "type": "episode",
                "summary": "Shared cultural memory",
                "provenance": {"source_type": "collective_echo", "agent_id": "other"},
                "strength": 0.5,
            })
            assert ok
            rows = idx.get_recent_memories(limit=10)
            assert len(rows) == 1
            assert rows[0]["provenance_type"] == "collective_echo"
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_index_node_stores_legacy_collective_provenance_type(self):
        """Legacy bare string 'collective' → normalised to 'collective_echo'."""
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            ok = idx.index_node(2, {
                "type": "episode",
                "summary": "Legacy collective memory",
                "provenance": "collective",
                "strength": 0.4,
            })
            assert ok
            rows = idx.get_recent_memories(limit=10)
            assert len(rows) == 1
            assert rows[0]["provenance_type"] == "collective_echo"
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_index_node_stores_non_collective_provenance_type(self):
        """user_input and tool_result provenance preserved as compact strings."""
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            idx.index_node(3, {
                "type": "episode",
                "summary": "User said hello",
                "provenance": {"source_type": "user_input"},
                "strength": 0.8,
            })
            idx.index_node(4, {
                "type": "episode",
                "summary": "Web search result",
                "provenance": {"source_type": "tool_result", "tool_name": "search"},
                "strength": 0.6,
            })
            rows = idx.get_recent_memories(limit=10)
            prov_types = {r["eid"]: r["provenance_type"] for r in rows}
            assert prov_types[3] == "user_input"
            assert prov_types[4] == "tool_result"
            idx.close()
        finally:
            shutil.rmtree(tmp)

    def test_index_node_stores_none_when_no_provenance(self):
        """Missing provenance → provenance_type is None."""
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            ok = idx.index_node(5, {
                "type": "episode",
                "summary": "No provenance field",
                "strength": 0.5,
            })
            assert ok
            rows = idx.get_recent_memories(limit=10)
            assert len(rows) == 1
            assert rows[0]["provenance_type"] is None
            idx.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: /recent endpoint returns provenance_type
# ---------------------------------------------------------------------------

class TestRecentEndpointReturnsProvenanceType:

    def test_recent_index_endpoint_returns_provenance_type(self):
        """get_recent_memories() includes provenance_type in returned dicts."""
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            idx.index_node(10, {
                "type": "episode",
                "summary": "Collective echo via recent",
                "provenance": {"source_type": "collective_echo"},
                "created_at": 100,
            })
            idx.index_node(11, {
                "type": "episode",
                "summary": "Organic private memory",
                "provenance": {"source_type": "user_input"},
                "created_at": 101,
            })
            results = idx.get_recent_memories(limit=10)
            assert len(results) == 2
            prov_map = {r["eid"]: r["provenance_type"] for r in results}
            assert prov_map[10] == "collective_echo"
            assert prov_map[11] == "user_input"
            idx.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: /motif/* endpoint returns provenance_type
# ---------------------------------------------------------------------------

class TestMotifEndpointReturnsProvenanceType:

    def test_motif_index_endpoint_returns_provenance_type(self):
        """get_memories_by_motif() includes provenance_type via JOIN."""
        tmp = _tmp()
        try:
            idx = IndexManager(tmp)
            idx.index_node(20, {
                "type": "episode",
                "summary": "Motif member — collective",
                "provenance": {"source_type": "collective_echo"},
            })
            idx.index_node(21, {
                "type": "episode",
                "summary": "Motif member — organic",
                "provenance": {"source_type": "user_input"},
            })
            idx.index_motif_membership(20, "motif_test_001", 0.9)
            idx.index_motif_membership(21, "motif_test_001", 0.7)

            results = idx.get_memories_by_motif("motif_test_001")
            assert len(results) == 2
            prov_map = {r["eid"]: r["provenance_type"] for r in results}
            assert prov_map[20] == "collective_echo"
            assert prov_map[21] == "user_input"
            idx.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: rebuild path repopulates provenance_type
# ---------------------------------------------------------------------------

class TestRebuildPopulatesProvenanceType:

    def test_index_rebuild_populates_provenance_type(self):
        """rebuild_from_jsonl extracts provenance_type from canonical payloads."""
        tmp = _tmp()
        try:
            # Create fake nodes.jsonl with provenance in payloads
            nodes_path = os.path.join(tmp, "nodes.jsonl")
            with open(nodes_path, "w") as f:
                json.dump({
                    "eid": 100,
                    "payload": {
                        "type": "episode",
                        "summary": "Collective from rebuild",
                        "provenance": {"source_type": "collective_echo"},
                        "strength": 0.5,
                    }
                }, f)
                f.write("\n")
                json.dump({
                    "eid": 101,
                    "payload": {
                        "type": "episode",
                        "summary": "Organic from rebuild",
                        "provenance": {"source_type": "user_input"},
                        "strength": 0.7,
                    }
                }, f)
                f.write("\n")
                json.dump({
                    "eid": 102,
                    "payload": {
                        "type": "episode",
                        "summary": "Legacy collective from rebuild",
                        "provenance": "collective",
                        "strength": 0.3,
                    }
                }, f)
                f.write("\n")
                json.dump({
                    "eid": 103,
                    "payload": {
                        "type": "episode",
                        "summary": "No provenance from rebuild",
                        "strength": 0.4,
                    }
                }, f)
                f.write("\n")

            idx_dir = os.path.join(tmp, "index")
            idx = IndexManager(idx_dir)
            counts = idx.rebuild_from_jsonl(nodes_path=nodes_path)
            assert counts["core_nodes"] == 4

            rows = idx.get_recent_memories(limit=10)
            prov_map = {r["eid"]: r["provenance_type"] for r in rows}
            assert prov_map[100] == "collective_echo"
            assert prov_map[101] == "user_input"
            assert prov_map[102] == "collective_echo"  # legacy normalised
            assert prov_map[103] is None               # absent provenance
            idx.close()
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_index_provenance_tests():
    """Run all index provenance alignment tests."""
    tests = [
        # derive_provenance_type
        ("DPT.1 Structured collective_echo", TestDeriveProvenanceType().test_structured_collective_echo),
        ("DPT.2 Structured user_input", TestDeriveProvenanceType().test_structured_user_input),
        ("DPT.3 Structured tool_result", TestDeriveProvenanceType().test_structured_tool_result),
        ("DPT.4 Legacy 'collective' string", TestDeriveProvenanceType().test_legacy_collective_string),
        ("DPT.5 Legacy 'user_input' string", TestDeriveProvenanceType().test_legacy_user_input_string),
        ("DPT.6 None provenance", TestDeriveProvenanceType().test_none_provenance),
        ("DPT.7 Dict missing source_type", TestDeriveProvenanceType().test_missing_source_type_in_dict),
        # index_node stores provenance_type
        ("IDX.1 Collective provenance stored", TestIndexNodeStoresProvenanceType().test_index_node_stores_collective_provenance_type),
        ("IDX.2 Legacy collective normalised", TestIndexNodeStoresProvenanceType().test_index_node_stores_legacy_collective_provenance_type),
        ("IDX.3 Non-collective preserved", TestIndexNodeStoresProvenanceType().test_index_node_stores_non_collective_provenance_type),
        ("IDX.4 None when missing", TestIndexNodeStoresProvenanceType().test_index_node_stores_none_when_no_provenance),
        # /recent returns provenance_type
        ("RCT.1 Recent returns provenance_type", TestRecentEndpointReturnsProvenanceType().test_recent_index_endpoint_returns_provenance_type),
        # /motif/* returns provenance_type
        ("MOT.1 Motif returns provenance_type", TestMotifEndpointReturnsProvenanceType().test_motif_index_endpoint_returns_provenance_type),
        # rebuild populates provenance_type
        ("RBD.1 Rebuild populates provenance_type", TestRebuildPopulatesProvenanceType().test_index_rebuild_populates_provenance_type),
    ]

    passed = 0
    failed = 0
    print("\n--- Index Provenance Alignment Tests ---")
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
    p, f = run_index_provenance_tests()
    print(f"\nIndex Provenance: {p} passed, {f} failed")
    if f > 0:
        sys.exit(1)
