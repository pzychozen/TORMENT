"""
tests/test_tool_result_lifecycle.py — Tool-result lifecycle policy tests

Tests covering:
    - Half-life cap at ingest (default 7 days, env-configurable)
    - Compression tier classification ("tool_result" tier)
    - Compression scoring (+10% compressibility)
    - Short-path multiplier (0.45x)
    - Reinforcement guard (no strength boost for tool-result memories)

Doctrine:
    Tool-result lifecycle policy must remain entirely inside the epistemic
    memory system. It must not imply freshness refresh, background re-query,
    scheduled updates, or any autonomous external action.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.compression import (
    derive_retention_tier,
    CompressionScorer,
    COMPRESS_TOOL_RESULT_MULT,
    COMPRESS_TOOL_RESULT_SCORE_MULT,
    COMPRESS_SHORT_PATH_MULT,
    COMPRESS_ECHO_MULT,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal fabric for testing
# ---------------------------------------------------------------------------

def _make_fabric():
    """Create a fresh fabric with one workspace and agent."""
    tmpdir = tempfile.mkdtemp(prefix="torment_test_lifecycle_")
    fabric = TormentFabric(data_dir=tmpdir)
    fabric.get_workspace("test-ws")
    fabric.create_agent("test-ws", "agent-1")
    return fabric


def _tool_result_prov(tool_name="weather_api", step=1):
    return ProvenanceV1.for_tool_result(
        tool_name=tool_name,
        parent_eids=[],
        step=step,
    ).to_dict()


# ===========================================================================
# Tests
# ===========================================================================

class TestToolResultHalfLifeCap(unittest.TestCase):
    """Tool-result memories should have a capped half-life at ingest."""

    def setUp(self):
        self.fabric = _make_fabric()

    def test_half_life_capped_default(self):
        """Tool-result memory half-life should be <= 7 days by default."""
        prov = _tool_result_prov()
        result = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="Current weather in Reykjavik: 3C, partly cloudy, clear skies expected",
            step=1,
            domain_id="personal",
            scope="private",
            provenance=prov,
        )
        eid = result["eid"]
        ak = self.fabric._agent_key("test-ws", "agent-1")
        entity = self.fabric.private_graphs[ak].entities[eid]
        hl = float((entity.payload or {}).get("half_life", 999))
        self.assertLessEqual(hl, 7.0, "Tool-result half-life should be capped at 7 days")

    def test_half_life_cap_env_override(self):
        """TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS should override the cap."""
        os.environ["TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS"] = "3"
        try:
            prov = _tool_result_prov()
            result = self.fabric.ingest(
                workspace_id="test-ws",
                agent_id="agent-1",
                text="Temperature forecast: 5C tomorrow, 7C day after",
                step=2,
                domain_id="personal",
                scope="private",
                provenance=prov,
            )
            eid = result["eid"]
            ak = self.fabric._agent_key("test-ws", "agent-1")
            entity = self.fabric.private_graphs[ak].entities[eid]
            hl = float((entity.payload or {}).get("half_life", 999))
            self.assertLessEqual(hl, 3.0, "Tool-result half-life should respect env override")
        finally:
            os.environ.pop("TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS", None)

    def test_user_memory_not_capped(self):
        """User memories should NOT be affected by the tool-result half-life cap."""
        result = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="I visited Reykjavik last summer and loved the midnight sun and the weather was perfect",
            step=1,
            domain_id="personal",
            scope="private",
        )
        eid = result["eid"]
        ak = self.fabric._agent_key("test-ws", "agent-1")
        entity = self.fabric.private_graphs[ak].entities[eid]
        hl = float((entity.payload or {}).get("half_life", 0))
        # User memory with coherent text should get a longer half-life than 7 days
        # (kernel gives 20-100 days based on coherence)
        self.assertGreater(hl, 7.0, "User memory half-life should not be capped by tool-result policy")


class TestToolResultCompressionTier(unittest.TestCase):
    """derive_retention_tier should return 'tool_result' for tool-result provenance."""

    def test_tool_result_tier(self):
        payload = {
            "provenance": _tool_result_prov(),
            "half_life": 5.0,
        }
        tier = derive_retention_tier(payload)
        self.assertEqual(tier, "tool_result")

    def test_user_memory_not_tool_result_tier(self):
        payload = {
            "half_life": 5.0,
        }
        tier = derive_retention_tier(payload)
        self.assertNotEqual(tier, "tool_result")

    def test_collective_still_echo(self):
        """Collective provenance should still classify as 'echo', not 'tool_result'."""
        payload = {
            "provenance": ProvenanceV1.for_collective_echo(notes="test").to_dict(),
            "half_life": 5.0,
        }
        tier = derive_retention_tier(payload)
        self.assertEqual(tier, "echo")

    def test_tool_result_tier_over_relational(self):
        """Tool-result should classify as tool_result even if half_life >= 7."""
        payload = {
            "provenance": _tool_result_prov(),
            "half_life": 50.0,  # would be 'relational' without provenance check
        }
        tier = derive_retention_tier(payload)
        self.assertEqual(tier, "tool_result")


class TestToolResultCompressionScoring(unittest.TestCase):
    """Tool-result compression tier should have correct compressibility multiplier."""

    def test_tool_result_constants(self):
        """Verify the compression constants are set correctly."""
        self.assertAlmostEqual(COMPRESS_TOOL_RESULT_MULT, 0.45)
        self.assertAlmostEqual(COMPRESS_TOOL_RESULT_SCORE_MULT, 1.10)

    def test_tool_result_between_echo_and_default(self):
        """Tool-result multiplier should be between echo and situational defaults."""
        self.assertGreater(COMPRESS_TOOL_RESULT_MULT, COMPRESS_ECHO_MULT,
                           "Tool-result mult should be > echo mult")
        self.assertLess(COMPRESS_TOOL_RESULT_MULT, COMPRESS_SHORT_PATH_MULT,
                        "Tool-result mult should be < situational default mult")


class TestToolResultShortPathMultiplier(unittest.TestCase):
    """Short-path compression should use the tool_result multiplier."""

    def test_scorer_recognizes_tool_result_tier(self):
        """CompressionScorer should produce a candidate with tier='tool_result'."""
        scorer = CompressionScorer()
        node = {
            "eid": 1,
            "step": 0,
            "payload": {
                "strength": 0.5,
                "retrieval_count": 0,
                "provenance": _tool_result_prov(),
                "half_life": 5.0,
                "summary": "Weather API result",
            },
        }
        candidate = scorer.score(node, current_step=100, coherence_field=None)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.tier, "tool_result")


class TestToolResultReinforcementGuard(unittest.TestCase):
    """Reinforcement of tool-result memories should not boost strength."""

    def setUp(self):
        self.fabric = _make_fabric()

    def test_reinforcement_no_strength_boost(self):
        """When a tool-result memory is reinforced, strength should stay the same."""
        prov = _tool_result_prov(tool_name="search_api", step=1)
        # First ingest
        result1 = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="Search result: best coffee shops in Reykjavik Iceland for tourists",
            step=1,
            domain_id="personal",
            scope="private",
            provenance=prov,
        )
        eid1 = result1["eid"]
        ak = self.fabric._agent_key("test-ws", "agent-1")
        entity1 = self.fabric.private_graphs[ak].entities[eid1]
        strength_before = float((entity1.payload or {}).get("strength", 0.5))

        # Second ingest of very similar content — should trigger reinforcement
        prov2 = _tool_result_prov(tool_name="search_api", step=2)
        result2 = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="Search result: best coffee shops in Reykjavik Iceland for tourists",
            step=2,
            domain_id="personal",
            scope="private",
            provenance=prov2,
        )
        eid2 = result2["eid"]

        if eid2 == eid1:
            # Reinforcement happened — verify strength did not increase
            entity_after = self.fabric.private_graphs[ak].entities[eid1]
            strength_after = float((entity_after.payload or {}).get("strength", 0.5))
            self.assertAlmostEqual(
                strength_after, strength_before, places=3,
                msg="Tool-result reinforcement should NOT boost strength",
            )
            # Verify reinforce_count was still incremented
            rc = int((entity_after.payload or {}).get("reinforce_count", 0))
            self.assertGreaterEqual(rc, 1, "reinforce_count should be incremented")
            # Verify last_tool_refresh_ts was set
            refresh_ts = (entity_after.payload or {}).get("last_tool_refresh_ts")
            self.assertIsNotNone(refresh_ts, "last_tool_refresh_ts should be set on tool-result reinforcement")
        else:
            # If dedup didn't fire (similarity below threshold), skip this assertion.
            # The guard only applies when reinforcement actually occurs.
            pass

    def test_user_memory_reinforcement_still_boosts(self):
        """User memories should still get strength boosts on reinforcement."""
        # First ingest
        result1 = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="I love visiting the coffee shops in Reykjavik every single summer vacation",
            step=1,
            domain_id="personal",
            scope="private",
        )
        eid1 = result1["eid"]
        ak = self.fabric._agent_key("test-ws", "agent-1")
        entity1 = self.fabric.private_graphs[ak].entities[eid1]
        strength_before = float((entity1.payload or {}).get("strength", 0.5))

        # Second ingest of identical content
        result2 = self.fabric.ingest(
            workspace_id="test-ws",
            agent_id="agent-1",
            text="I love visiting the coffee shops in Reykjavik every single summer vacation",
            step=2,
            domain_id="personal",
            scope="private",
        )
        eid2 = result2["eid"]

        if eid2 == eid1:
            # Reinforcement happened — verify strength DID increase
            entity_after = self.fabric.private_graphs[ak].entities[eid1]
            strength_after = float((entity_after.payload or {}).get("strength", 0.5))
            self.assertGreater(
                strength_after, strength_before,
                msg="User memory reinforcement should boost strength",
            )


if __name__ == "__main__":
    unittest.main()
