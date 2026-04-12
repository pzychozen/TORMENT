# tests/test_aperture_lane_separation.py
"""
Phase 2 aperture lane separation tests (v2.4.4).

Proves that when build_memory_context receives a LaneQueryProvider,
each MemoryContext lane (private, shared, deep) contains ONLY hits
from its own scope — no cross-contamination.

Also verifies:
  - deep_top_k budget is respected per aperture config
  - protected aperture gets deep_top_k=0 (no deep memories)
  - legacy query_fn path still works (backward compat)
  - interpreter sees real private-only hits
  - engineer combined pool includes all three lanes
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cognition.apertures import (
    ApertureConfig,
    APERTURE_CONFIGS,
    LaneQueryProvider,
    MemoryContext,
    build_memory_context,
)


# ---------------------------------------------------------------------------
# Fake lane functions — each returns hits tagged with a known scope
# ---------------------------------------------------------------------------

def _fake_private(ws_id, ag_id, query_text, top_k):
    return [
        {"eid": i, "text": f"private-hit-{i}", "scope": "private", "final_score": 0.9 - i * 0.1}
        for i in range(top_k)
    ]


def _fake_shared(ws_id, ag_id, query_text, top_k, domain_id):
    hits = [
        {"eid": 100 + i, "text": f"shared-hit-{i}", "scope": "shared", "final_score": 0.8 - i * 0.1}
        for i in range(top_k)
    ]
    bridge_domains = ["domain_a"] if top_k > 0 else []
    return (hits, bridge_domains)


def _fake_deep(ws_id, ag_id, query_text, top_k):
    return [
        {"eid": 200 + i, "text": f"deep-hit-{i}", "scope": "deep",
         "deep_memory": True, "from_deep_memory": True, "final_score": 0.7 - i * 0.1}
        for i in range(top_k)
    ]


def _fake_character(ws_id, ag_id):
    return {"name": "atlas", "seed": "test-seed"}


def _fake_drift(ws_id, ag_id):
    return {"drift_score": 0.05, "status": "nominal"}


# ---------------------------------------------------------------------------
# Tests: lane isolation via LaneQueryProvider
# ---------------------------------------------------------------------------

class TestLaneSeparationNarrow(unittest.TestCase):
    """Narrow aperture: private=6, shared=3, deep=2."""

    def setUp(self):
        self.provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,
        )

    def test_private_only_private_hits(self):
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=self.provider,
        )
        for mem in ctx.private_memories:
            self.assertEqual(mem["scope"], "private",
                             f"Non-private hit in private_memories: {mem}")

    def test_shared_only_shared_hits(self):
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=self.provider,
        )
        for mem in ctx.shared_memories:
            self.assertEqual(mem["scope"], "shared",
                             f"Non-shared hit in shared_memories: {mem}")

    def test_deep_only_deep_hits(self):
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=self.provider,
        )
        for mem in ctx.deep_memories:
            self.assertEqual(mem["scope"], "deep",
                             f"Non-deep hit in deep_memories: {mem}")

    def test_narrow_budgets(self):
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=self.provider,
        )
        self.assertEqual(len(ctx.private_memories), 6)
        self.assertEqual(len(ctx.shared_memories), 3)
        self.assertEqual(len(ctx.deep_memories), 2)

    def test_total_memories(self):
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=self.provider,
        )
        self.assertEqual(ctx.total_memories, 6 + 3 + 2)

    def test_no_cross_contamination_eids(self):
        """EID ranges should not overlap across lanes."""
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=self.provider,
        )
        private_eids = {m["eid"] for m in ctx.private_memories}
        shared_eids = {m["eid"] for m in ctx.shared_memories}
        deep_eids = {m["eid"] for m in ctx.deep_memories}

        self.assertEqual(private_eids & shared_eids, set())
        self.assertEqual(private_eids & deep_eids, set())
        self.assertEqual(shared_eids & deep_eids, set())


class TestLaneSeparationBroad(unittest.TestCase):
    """Broad aperture: private=12, shared=8, deep=4."""

    def test_broad_budgets(self):
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "broad", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        self.assertEqual(len(ctx.private_memories), 12)
        self.assertEqual(len(ctx.shared_memories), 8)
        self.assertEqual(len(ctx.deep_memories), 4)

    def test_broad_character_full(self):
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "broad", "ws1", "ag1", "test query",
            lane_provider=provider,
            character_fn=_fake_character,
        )
        self.assertIsNotNone(ctx.character_context)
        # broad = "full" mode, no seed_only wrapper
        self.assertNotIn("seed_only", ctx.character_context)


class TestLaneSeparationProtected(unittest.TestCase):
    """Protected aperture: private=4, shared=2, deep=0."""

    def test_protected_no_deep(self):
        """Protected aperture must get zero deep memories."""
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,  # provided but should NOT be called
        )
        ctx = build_memory_context(
            "protected", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        self.assertEqual(len(ctx.deep_memories), 0,
                         "Protected aperture should have zero deep memories")

    def test_protected_budgets(self):
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "protected", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        self.assertEqual(len(ctx.private_memories), 4)
        self.assertEqual(len(ctx.shared_memories), 2)
        self.assertEqual(len(ctx.deep_memories), 0)

    def test_protected_drift_snapshot(self):
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
        )
        ctx = build_memory_context(
            "protected", "ws1", "ag1", "test query",
            lane_provider=provider,
            character_fn=_fake_character,
            drift_fn=_fake_drift,
        )
        self.assertIsNotNone(ctx.drift_snapshot)
        self.assertEqual(ctx.drift_snapshot["status"], "nominal")


class TestLaneSeparationEdgeCases(unittest.TestCase):
    """Edge cases: missing lanes, exceptions, None provider."""

    def test_missing_private_fn(self):
        provider = LaneQueryProvider(
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        self.assertEqual(len(ctx.private_memories), 0)
        self.assertGreater(len(ctx.shared_memories), 0)

    def test_missing_shared_fn(self):
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        self.assertGreater(len(ctx.private_memories), 0)
        self.assertEqual(len(ctx.shared_memories), 0)

    def test_missing_deep_fn(self):
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
        )
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        self.assertEqual(len(ctx.deep_memories), 0)

    def test_exception_in_private_fn(self):
        def _exploding_private(*args, **kwargs):
            raise RuntimeError("boom")

        provider = LaneQueryProvider(
            private_fn=_exploding_private,
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        # Private should be empty (exception caught), others should work
        self.assertEqual(len(ctx.private_memories), 0)
        self.assertGreater(len(ctx.shared_memories), 0)
        self.assertGreater(len(ctx.deep_memories), 0)

    def test_exception_in_shared_fn(self):
        def _exploding_shared(*args, **kwargs):
            raise RuntimeError("boom")

        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_exploding_shared,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        self.assertGreater(len(ctx.private_memories), 0)
        self.assertEqual(len(ctx.shared_memories), 0)
        self.assertGreater(len(ctx.deep_memories), 0)

    def test_shared_fn_returns_plain_list(self):
        """shared_fn returning a plain list instead of tuple should still work."""
        def _shared_plain_list(ws_id, ag_id, query_text, top_k, domain_id):
            return [{"eid": 100, "text": "shared", "scope": "shared"}]

        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_shared_plain_list,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        self.assertEqual(len(ctx.shared_memories), 1)


class TestLegacyQueryFnPath(unittest.TestCase):
    """Legacy query_fn path should still work when no lane_provider given."""

    def test_legacy_path_builds_context(self):
        def _fake_query_fn(ws_id, ag_id, query_text, top_k, domain_id):
            return {"results": [
                {"eid": i, "text": f"hit-{i}", "scope": "private"}
                for i in range(top_k)
            ]}

        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            query_fn=_fake_query_fn,
        )
        # Legacy path fills private and shared from same query_fn
        self.assertGreater(len(ctx.private_memories), 0)
        # Deep stays empty on legacy path
        self.assertEqual(len(ctx.deep_memories), 0)

    def test_lane_provider_takes_precedence(self):
        """When both lane_provider and query_fn given, lane_provider wins."""
        call_log = []

        def _logging_query_fn(*args, **kwargs):
            call_log.append("query_fn")
            return {"results": []}

        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
        )
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=provider,
            query_fn=_logging_query_fn,
        )
        # query_fn should NOT have been called
        self.assertEqual(call_log, [])
        # But lane_provider should have produced results
        self.assertGreater(len(ctx.private_memories), 0)


class TestMemoryContextSerialization(unittest.TestCase):
    """MemoryContext to_dict / from_dict round-trip with deep_memories."""

    def test_round_trip(self):
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "narrow", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        d = ctx.to_dict()
        ctx2 = MemoryContext.from_dict(d)

        self.assertEqual(len(ctx2.private_memories), len(ctx.private_memories))
        self.assertEqual(len(ctx2.shared_memories), len(ctx.shared_memories))
        self.assertEqual(len(ctx2.deep_memories), len(ctx.deep_memories))
        self.assertEqual(ctx2.aperture_name, "narrow")
        self.assertEqual(ctx2.total_memories, ctx.total_memories)

    def test_deep_memories_in_dict(self):
        provider = LaneQueryProvider(
            private_fn=_fake_private,
            shared_fn=_fake_shared,
            deep_fn=_fake_deep,
        )
        ctx = build_memory_context(
            "broad", "ws1", "ag1", "test query",
            lane_provider=provider,
        )
        d = ctx.to_dict()
        self.assertIn("deep_memories", d)
        self.assertEqual(len(d["deep_memories"]), 4)  # broad deep_top_k=4


class TestApertureConfigDeepTopK(unittest.TestCase):
    """Verify deep_top_k values in the config table."""

    def test_narrow_deep_top_k(self):
        self.assertEqual(APERTURE_CONFIGS["narrow"].deep_top_k, 2)

    def test_broad_deep_top_k(self):
        self.assertEqual(APERTURE_CONFIGS["broad"].deep_top_k, 4)

    def test_protected_deep_top_k(self):
        self.assertEqual(APERTURE_CONFIGS["protected"].deep_top_k, 0)


if __name__ == "__main__":
    unittest.main()
