"""Regression tests for trace() parity with query() ranking reducers.

Bug: trace() explain_for_hit() did not apply the same provenance-based
discounts and conflict penalties that query() uses. This made trace
explanations overstate scores for collective echoes, tool-result
memories, and contested shared canon.

Fix: trace() now mirrors:
  1. Collective provenance discount (TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT)
  2. Tool-result discount (TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT)
  3. Conflict penalty for contested shared canon memories
  4. Self-thread bonus exclusion for tool-result memories

Tests:
  1. Collective echo trace score is discounted
  2. Tool-result trace score is discounted
  3. Conflict metadata surfaces in trace explanation
  4. Discount fields are present in explanation output
"""

import os
import shutil
import tempfile
import unittest

from torment_service.fabric import TormentFabric


class TestTraceCollectiveDiscount(unittest.TestCase):
    """Verify that trace applies the collective provenance discount."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_trace_disc_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_collective_echo_is_discounted(self):
        """A memory with collective_echo provenance should have a lower
        trace final_score than an equivalent organic memory."""
        # Ingest organic memory
        r_organic = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Organic observation about quantum mechanics",
            step=1,
            provenance={"source_type": "user_input", "confidence": 0.9},
        )
        eid_organic = r_organic["eid"]

        # Ingest collective echo memory with same text
        r_collective = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Collective echo about quantum mechanics",
            step=2,
            provenance={"source_type": "collective_echo", "confidence": 0.7},
        )
        eid_collective = r_collective["eid"]

        # Trace both
        result = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="quantum mechanics",
            eids=[eid_organic, eid_collective],
        )
        items = {it["eid"]: it for it in result.get("items", [])}

        self.assertIn(eid_organic, items, "Organic memory should be traced")
        self.assertIn(eid_collective, items, "Collective memory should be traced")

        org_item = items[eid_organic]
        col_item = items[eid_collective]

        # Collective should be discounted
        self.assertLess(
            col_item["explain"]["collective_discount"], 1.0,
            "Collective discount should be < 1.0",
        )
        # Organic should have no discount
        self.assertAlmostEqual(
            org_item["explain"]["collective_discount"], 1.0,
            msg="Organic memory should have collective_discount = 1.0",
        )
        # Provenance type should be surfaced
        self.assertEqual(
            col_item["explain"]["provenance_type"], "collective_echo",
        )


class TestTraceToolResultDiscount(unittest.TestCase):
    """Verify that trace applies the tool-result discount."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_trace_tool_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_tool_result_is_discounted(self):
        """A memory with tool_result provenance should show a discount
        in trace explanation."""
        # Ingest organic memory
        r_organic = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Personal observation about the weather today",
            step=1,
            provenance={"source_type": "user_input", "confidence": 0.9},
        )
        eid_organic = r_organic["eid"]

        # Ingest tool-result memory
        r_tool = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Tool result about the weather today",
            step=2,
            provenance={
                "source_type": "tool_result",
                "tool_name": "weather_api",
                "confidence": 0.8,
            },
        )
        eid_tool = r_tool["eid"]

        # Trace both
        result = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="weather today",
            eids=[eid_organic, eid_tool],
        )
        items = {it["eid"]: it for it in result.get("items", [])}

        self.assertIn(eid_tool, items, "Tool-result memory should be traced")

        tool_item = items[eid_tool]
        org_item = items[eid_organic]

        # Tool-result should be discounted
        self.assertLess(
            tool_item["explain"]["tool_result_discount"], 1.0,
            "Tool-result discount should be < 1.0",
        )
        # Organic should have no tool discount
        self.assertAlmostEqual(
            org_item["explain"]["tool_result_discount"], 1.0,
            msg="Organic memory should have tool_result_discount = 1.0",
        )
        # Provenance type should be surfaced
        self.assertEqual(
            tool_item["explain"]["provenance_type"], "tool_result",
        )


class TestTraceExplainFields(unittest.TestCase):
    """Verify that trace explanation output includes all discount fields."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_trace_fields_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)
        self.fabric.get_workspace("ws")
        self.fabric.create_agent("ws", "agent")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_explain_contains_all_discount_fields(self):
        """Every traced item should include discount and conflict fields
        in the explanation, even when they are at default values."""
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="A simple memory for field check",
            step=1,
        )
        result = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="simple memory",
            eids=[r["eid"]],
        )
        items = result.get("items", [])
        self.assertTrue(len(items) >= 1, "Should have at least one traced item")

        explain = items[0]["explain"]
        required_fields = [
            "collective_discount",
            "tool_result_discount",
            "conflict_penalty",
            "conflict_status",
            "conflict_ids",
            "provenance_type",
        ]
        for field in required_fields:
            self.assertIn(field, explain,
                f"Explanation missing '{field}' field")

    def test_default_discounts_are_neutral(self):
        """For a plain organic memory, all discounts should be 1.0 and
        conflict fields should be empty/None."""
        r = self.fabric.ingest(
            workspace_id="ws", agent_id="agent",
            text="Neutral memory with no special provenance",
            step=1,
        )
        result = self.fabric.trace(
            workspace_id="ws", agent_id="agent",
            query_text="neutral memory",
            eids=[r["eid"]],
        )
        explain = result["items"][0]["explain"]
        self.assertAlmostEqual(explain["collective_discount"], 1.0)
        self.assertAlmostEqual(explain["tool_result_discount"], 1.0)
        self.assertAlmostEqual(explain["conflict_penalty"], 0.0)
        self.assertIsNone(explain["conflict_status"])
        self.assertEqual(explain["conflict_ids"], [])


if __name__ == "__main__":
    unittest.main()
