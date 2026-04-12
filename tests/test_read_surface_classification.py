"""
Tests for read-surface classification — provenance preservation.

Verifies that the /retrieve and cognition-aperture paths preserve
provenance classification so collective echoes remain visibly collective
all the way into reasoning context.

These are pure-Python tests that do not require a running TormentFabric.
"""
import unittest
from typing import Any, Dict, List, Optional


# ============================================================================
# PATCH 1 tests: /retrieve ContextBlock provenance preservation
# ============================================================================


class TestHitToBlockPreservesProvenanceType(unittest.TestCase):
    """TEST 1: _hit_to_block preserves provenance_type for collective echo."""

    def test_hit_to_block_preserves_provenance_type(self):
        from torment_service.retrieval_assembler import _hit_to_block

        hit: Dict[str, Any] = {
            "eid": 42,
            "score": 0.8,
            "summary": "A distant convergence of loss.",
            "type": "memory",
            "strength": 0.7,
            "confidence": 0.9,
            "half_life": 30,
            "provenance_type": "collective_echo",
            "provenance_tool_name": None,
            "provenance": {
                "source_type": "collective_echo",
                "write_path": "collective_reingest",
            },
        }

        block = _hit_to_block(hit, "situational")

        self.assertEqual(block.metadata.get("provenance_type"), "collective_echo")
        self.assertEqual(block.source, "core")


class TestHitToBlockPreservesNonCollectiveProvenanceType(unittest.TestCase):
    """TEST 2: _hit_to_block preserves non-collective provenance types."""

    def test_hit_to_block_preserves_non_collective_provenance_type(self):
        from torment_service.retrieval_assembler import _hit_to_block

        hit: Dict[str, Any] = {
            "eid": 10,
            "score": 0.9,
            "summary": "User said hello at the harbor.",
            "type": "memory",
            "strength": 0.8,
            "confidence": 0.95,
            "half_life": 60,
            "provenance_type": "user_input",
            "provenance_tool_name": None,
            "provenance": {
                "source_type": "user_input",
                "write_path": "direct_ingest",
            },
        }

        block = _hit_to_block(hit, "relational")

        self.assertEqual(block.metadata.get("provenance_type"), "user_input")

    def test_hit_to_block_preserves_tool_result_provenance(self):
        from torment_service.retrieval_assembler import _hit_to_block

        hit: Dict[str, Any] = {
            "eid": 20,
            "score": 0.6,
            "summary": "Tool returned weather data.",
            "type": "memory",
            "strength": 0.5,
            "confidence": 0.8,
            "half_life": 15,
            "provenance_type": "tool_result",
            "provenance_tool_name": "weather_api",
            "provenance": {
                "source_type": "tool_result",
                "tool_name": "weather_api",
                "write_path": "tool_ingest",
            },
        }

        block = _hit_to_block(hit, "situational")

        self.assertEqual(block.metadata.get("provenance_type"), "tool_result")
        self.assertEqual(block.metadata.get("provenance_tool_name"), "weather_api")

    def test_hit_to_block_derives_provenance_from_raw_dict(self):
        """When provenance_type is absent, derive from raw provenance dict."""
        from torment_service.retrieval_assembler import _hit_to_block

        hit: Dict[str, Any] = {
            "eid": 30,
            "score": 0.5,
            "summary": "Convergence echo.",
            "type": "memory",
            "strength": 0.4,
            "confidence": 0.7,
            "half_life": 20,
            # No provenance_type — only raw provenance dict
            "provenance": {
                "source_type": "collective_echo",
                "write_path": "collective_reingest",
            },
        }

        block = _hit_to_block(hit, "situational")

        self.assertEqual(block.metadata.get("provenance_type"), "collective_echo")

    def test_hit_to_block_derives_provenance_from_legacy_string(self):
        """When raw provenance is the legacy 'collective' string."""
        from torment_service.retrieval_assembler import _hit_to_block

        hit: Dict[str, Any] = {
            "eid": 31,
            "score": 0.4,
            "summary": "Legacy echo.",
            "type": "memory",
            "strength": 0.3,
            "confidence": 0.6,
            "half_life": 10,
            "provenance": "collective",
        }

        block = _hit_to_block(hit, "situational")

        self.assertEqual(block.metadata.get("provenance_type"), "collective_echo")

    def test_hit_to_block_no_provenance_yields_none(self):
        """When there is no provenance at all, provenance_type should be absent."""
        from torment_service.retrieval_assembler import _hit_to_block

        hit: Dict[str, Any] = {
            "eid": 50,
            "score": 0.7,
            "summary": "Ancient memory.",
            "type": "memory",
            "strength": 0.6,
            "confidence": 0.8,
            "half_life": 90,
        }

        block = _hit_to_block(hit, "identity")

        # No provenance → provenance_type should not be in metadata
        self.assertNotIn("provenance_type", block.metadata)


# ============================================================================
# PATCH 2 tests: cognition aperture provenance classification
# ============================================================================


class TestStampProvenanceType(unittest.TestCase):
    """Tests for _stamp_provenance_type helper in apertures."""

    def test_stamps_collective_echo_from_dict(self):
        from cognition.apertures import _stamp_provenance_type

        hits = [
            {
                "eid": 1,
                "score": 0.8,
                "provenance": {"source_type": "collective_echo"},
            },
        ]

        result = _stamp_provenance_type(hits)

        self.assertEqual(result[0]["provenance_type"], "collective_echo")

    def test_stamps_user_input_from_dict(self):
        from cognition.apertures import _stamp_provenance_type

        hits = [
            {
                "eid": 2,
                "score": 0.9,
                "provenance": {"source_type": "user_input"},
            },
        ]

        result = _stamp_provenance_type(hits)

        self.assertEqual(result[0]["provenance_type"], "user_input")

    def test_stamps_legacy_collective_string(self):
        from cognition.apertures import _stamp_provenance_type

        hits = [{"eid": 3, "score": 0.5, "provenance": "collective"}]

        result = _stamp_provenance_type(hits)

        self.assertEqual(result[0]["provenance_type"], "collective_echo")

    def test_preserves_existing_provenance_type(self):
        from cognition.apertures import _stamp_provenance_type

        hits = [
            {
                "eid": 4,
                "score": 0.7,
                "provenance_type": "already_set",
                "provenance": {"source_type": "ignored"},
            },
        ]

        result = _stamp_provenance_type(hits)

        self.assertEqual(result[0]["provenance_type"], "already_set")

    def test_no_provenance_yields_none(self):
        from cognition.apertures import _stamp_provenance_type

        hits = [{"eid": 5, "score": 0.6}]

        result = _stamp_provenance_type(hits)

        self.assertIsNone(result[0]["provenance_type"])

    def test_empty_list(self):
        from cognition.apertures import _stamp_provenance_type

        result = _stamp_provenance_type([])

        self.assertEqual(result, [])


class TestBuildMemoryContextPreservesClassification(unittest.TestCase):
    """TEST 3: build_memory_context preserves collective classification."""

    def test_build_memory_context_preserves_collective_classification(self):
        from cognition.apertures import (
            build_memory_context,
            LaneQueryProvider,
        )

        organic_hit = {
            "eid": 1,
            "score": 0.9,
            "summary": "I remember the harbor.",
            "type": "memory",
            "provenance": {"source_type": "user_input", "write_path": "direct_ingest"},
        }
        collective_hit = {
            "eid": 2,
            "score": 0.5,
            "summary": "Convergence echo about loss.",
            "type": "memory",
            "provenance": {
                "source_type": "collective_echo",
                "write_path": "collective_reingest",
            },
        }

        def mock_private(ws, ag, qt, tk):
            return [organic_hit]

        def mock_shared(ws, ag, qt, tk, dom):
            return ([collective_hit], [])

        def mock_deep(ws, ag, qt, tk):
            return []

        provider = LaneQueryProvider(
            private_fn=mock_private,
            shared_fn=mock_shared,
            deep_fn=mock_deep,
        )

        ctx = build_memory_context(
            aperture_name="broad",
            workspace_id="ws_test",
            agent_id="agent_a",
            query_text="loss and memory",
            lane_provider=provider,
        )

        # Private lane should have organic classification
        self.assertEqual(len(ctx.private_memories), 1)
        self.assertEqual(ctx.private_memories[0]["provenance_type"], "user_input")

        # Shared lane should have collective classification
        self.assertEqual(len(ctx.shared_memories), 1)
        self.assertEqual(ctx.shared_memories[0]["provenance_type"], "collective_echo")


class TestBuildMemoryContextKeepsCollectiveAndOrganicDistinguishable(unittest.TestCase):
    """TEST 4: organic and collective remain distinguishable in context."""

    def test_build_memory_context_keeps_collective_and_organic_distinguishable(self):
        from cognition.apertures import (
            build_memory_context,
            LaneQueryProvider,
        )
        from torment_service.scoring import is_collective_provenance

        organic = {
            "eid": 10,
            "score": 0.85,
            "summary": "The harbor at dawn.",
            "provenance": {"source_type": "user_input"},
        }
        collective = {
            "eid": 20,
            "score": 0.45,
            "summary": "Echo of shared grief.",
            "provenance": {"source_type": "collective_echo"},
        }

        def mock_private(ws, ag, qt, tk):
            return [organic, collective]

        provider = LaneQueryProvider(
            private_fn=mock_private,
            shared_fn=None,
            deep_fn=None,
        )

        ctx = build_memory_context(
            aperture_name="narrow",
            workspace_id="ws_test",
            agent_id="agent_a",
            query_text="test",
            lane_provider=provider,
        )

        organic_hits = [
            m for m in ctx.private_memories
            if not is_collective_provenance(m.get("provenance"))
        ]
        collective_hits = [
            m for m in ctx.private_memories
            if is_collective_provenance(m.get("provenance"))
        ]

        self.assertTrue(len(organic_hits) > 0, "Should have organic hits")
        self.assertTrue(len(collective_hits) > 0, "Should have collective hits")

        # They should be distinguishable by provenance_type
        self.assertEqual(organic_hits[0]["provenance_type"], "user_input")
        self.assertEqual(collective_hits[0]["provenance_type"], "collective_echo")


if __name__ == "__main__":
    unittest.main()
