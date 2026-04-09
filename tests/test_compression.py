"""
Tests for event-gated memory compression (Phase 6).

Covers:
  - EventDetector: corridor exit, cycle stage change, emergency, no-trigger
  - CompressionScorer: protection rules, age filter, J→Z weighting
  - CompressionRouter: deep vs short path routing
  - CompressionExecutor: short-path and long-path execution
  - DeepMemoryStore: export, query, recall, stats
  - Integration: try_compress full cycle, fabric hookup
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import MagicMock

import numpy as np

# Ensure project root is on sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from torment_service.compression import (
    EventDetector,
    CompressionScorer,
    CompressionRouter,
    CompressionExecutor,
    CompressionCandidate,
    CompressionEvent,
    try_compress,
)
from torment_service.deep_memory import DeepMemoryStore, DeepMemory


# ---------------------------------------------------------------------------
# Test helpers — mock objects
# ---------------------------------------------------------------------------

def _make_tri_mod(**overrides) -> dict:
    """Create a tri_mod dict with sensible defaults."""
    d = {
        "in_corridor": False,
        "cycle_stage": 1,
        "tearing_risk": 0.1,
        "tangent_align": 0.8,
        "align_ema": 0.7,
        "identity_state": "stable",
        "survival_steps": 10,
        "write_mult": 1.0,
        "proposal_mult": 1.0,
        "bridge_p": 0.5,
        "bridge_sim": 0.5,
        "disp": 0.001,
        "coh_phase": 0.5,
    }
    d.update(overrides)
    return d


def _make_node(eid: int, born_step: int = 0, **payload_overrides) -> dict:
    """Create a mock memory node."""
    payload = {
        "summary": f"Memory node {eid}",
        "type": "episode",
        "kind": "episode",
        "tier": "relational",
        "memory_class": "core",
        "strength": 0.5,
        "confidence": 0.6,
        "canon": False,
        "created_at": born_step,
        "half_life": 30.0,
        "retrieval_count": 0,
        "motif_id": None,
    }
    payload.update(payload_overrides)
    return {"eid": eid, "born_step": born_step, "payload": payload}


def _make_coherence_field() -> List[dict]:
    """Create a mock coherence field output."""
    return [
        {
            "motif_id": "motif_001",
            "label": "motif_001",
            "role": "basin",
            "phi": 0.8,
            "kappa": -0.02,
            "tension": 0.2,
            "density": 0.6,
            "strength": 0.7,
            "stability_score": 0.6,
            "members": 15,
        },
        {
            "motif_id": "motif_002",
            "label": "motif_002",
            "role": "plateau",
            "phi": 0.1,
            "kappa": 0.005,
            "tension": 0.1,
            "density": 0.2,
            "strength": 0.3,
            "stability_score": 0.2,
            "members": 3,
        },
    ]


class MockEntity:
    """Minimal entity mock for MemoryGraph."""
    def __init__(self, eid: int, born_step: int = 0, payload: Optional[dict] = None):
        self.eid = eid
        self.born_step = born_step
        self.payload = payload or {}


class MockMemoryGraph:
    """Minimal MemoryGraph mock."""
    def __init__(self, entities: Optional[Dict[int, MockEntity]] = None):
        self.entities = entities or {}
        self.data_dir = "/tmp/mock_graph"
        self._shard_reader = None
        self._updates: List[tuple] = []

    def update_payload(self, eid: int, patch: dict):
        ent = self.entities.get(eid)
        if ent is None:
            raise KeyError(f"Unknown eid: {eid}")
        ent.payload.update(patch)
        self._updates.append((eid, dict(patch)))


# ===========================================================================
# EventDetector tests
# ===========================================================================

class TestEventDetector(unittest.TestCase):
    def test_corridor_exit(self):
        """Corridor True→False should fire 'corridor_exit'."""
        d = EventDetector()
        # First call: set state to in_corridor=True
        d.check(_make_tri_mod(in_corridor=True), step=10)
        # Second call: corridor exit
        trigger = d.check(_make_tri_mod(in_corridor=False), step=11)
        self.assertEqual(trigger, "corridor_exit")

    def test_cycle_stage_change(self):
        """Cycle stage change should fire 'cycle_stage_change'."""
        d = EventDetector()
        d.check(_make_tri_mod(cycle_stage=1), step=10)
        trigger = d.check(_make_tri_mod(cycle_stage=2), step=11)
        self.assertEqual(trigger, "cycle_stage_change")

    def test_no_trigger_stable(self):
        """Stable state should return None."""
        d = EventDetector()
        d.check(_make_tri_mod(in_corridor=True, cycle_stage=1), step=10)
        trigger = d.check(_make_tri_mod(in_corridor=True, cycle_stage=1), step=11)
        self.assertIsNone(trigger)

    def test_emergency_tear(self):
        """High tearing_risk while in corridor should fire 'emergency_tear'."""
        d = EventDetector()
        trigger = d.check(_make_tri_mod(in_corridor=True, tearing_risk=0.85), step=10)
        self.assertEqual(trigger, "emergency_tear")

    def test_first_call_no_trigger(self):
        """First call should not trigger (no previous state)."""
        d = EventDetector()
        trigger = d.check(_make_tri_mod(in_corridor=False), step=1)
        self.assertIsNone(trigger)

    def test_warning_horizon(self):
        """Warning should activate when tearing rises."""
        d = EventDetector()
        d.check(_make_tri_mod(tearing_risk=0.1, align_ema=0.9), step=1)
        d.check(_make_tri_mod(tearing_risk=0.3, align_ema=0.8), step=2)
        self.assertTrue(d.is_warning())

    def test_state_dict(self):
        """state_dict should return serializable dict."""
        d = EventDetector()
        d.check(_make_tri_mod(in_corridor=True, cycle_stage=2), step=5)
        state = d.state_dict()
        self.assertTrue(state["prev_in_corridor"])
        self.assertEqual(state["prev_cycle_stage"], 2)
        # Ensure JSON-serializable
        json.dumps(state)


# ===========================================================================
# CompressionScorer tests
# ===========================================================================

class TestCompressionScorer(unittest.TestCase):
    def test_protected_canon(self):
        """Canon nodes should never be scored."""
        scorer = CompressionScorer(min_age_steps=0)
        node = _make_node(1, born_step=0, canon=True)
        result = scorer.score(node, current_step=100)
        self.assertIsNone(result)

    def test_protected_seed_kind(self):
        """Seed kind nodes should never be scored."""
        scorer = CompressionScorer(min_age_steps=0)
        node = _make_node(1, born_step=0, kind="seed")
        result = scorer.score(node, current_step=100)
        self.assertIsNone(result)

    def test_protected_identity_kind(self):
        """Identity kind should be protected."""
        scorer = CompressionScorer(min_age_steps=0)
        node = _make_node(1, born_step=0, kind="identity")
        result = scorer.score(node, current_step=100)
        self.assertIsNone(result)

    def test_protected_core_identity_tier(self):
        """core_identity tier should be protected."""
        scorer = CompressionScorer(min_age_steps=0)
        node = _make_node(1, born_step=0, tier="core_identity")
        result = scorer.score(node, current_step=100)
        self.assertIsNone(result)

    def test_age_filter(self):
        """Nodes younger than min_age should be excluded."""
        scorer = CompressionScorer(min_age_steps=50)
        node = _make_node(1, born_step=80)
        result = scorer.score(node, current_step=100)
        self.assertIsNone(result)

    def test_eligible_node_scores(self):
        """Eligible node should return a CompressionCandidate with valid score."""
        scorer = CompressionScorer(min_age_steps=10)
        node = _make_node(1, born_step=0, strength=0.3, retrieval_count=0)
        result = scorer.score(node, current_step=100)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, CompressionCandidate)
        self.assertGreater(result.score, 0.0)
        self.assertLessEqual(result.score, 1.0)

    def test_j_weighted_more_than_z(self):
        """J-score should have 60% weight, Z-score 40%."""
        scorer = CompressionScorer(min_age_steps=0)
        # High-strength node (low j_score = low compressibility)
        strong = _make_node(1, born_step=0, strength=0.9, retrieval_count=5)
        # Low-strength node (high j_score = high compressibility)
        weak = _make_node(2, born_step=0, strength=0.1, retrieval_count=0)

        c_strong = scorer.score(strong, current_step=100)
        c_weak = scorer.score(weak, current_step=100)
        self.assertIsNotNone(c_strong)
        self.assertIsNotNone(c_weak)
        # Weak should be more compressible
        self.assertGreater(c_weak.score, c_strong.score)

    def test_basin_member_resists(self):
        """Motif basin member should resist compression."""
        scorer = CompressionScorer(min_age_steps=0)
        cf = _make_coherence_field()

        # Basin member
        basin_node = _make_node(1, born_step=0, motif_id="motif_001", strength=0.3)
        # Non-motif node
        plain_node = _make_node(2, born_step=0, motif_id=None, strength=0.3)

        c_basin = scorer.score(basin_node, current_step=100, coherence_field=cf)
        c_plain = scorer.score(plain_node, current_step=100, coherence_field=cf)

        self.assertIsNotNone(c_basin)
        self.assertIsNotNone(c_plain)
        # Basin member should be LESS compressible (lower score)
        self.assertLess(c_basin.score, c_plain.score)

    def test_select_candidates_max(self):
        """select_candidates should respect max_candidates."""
        scorer = CompressionScorer(min_age_steps=0, max_candidates=3)
        nodes = [_make_node(i, born_step=0) for i in range(10)]
        candidates = scorer.select_candidates(nodes, current_step=100)
        self.assertLessEqual(len(candidates), 3)

    def test_select_candidates_sorted(self):
        """Candidates should be sorted by score descending."""
        scorer = CompressionScorer(min_age_steps=0, max_candidates=10)
        nodes = [
            _make_node(1, born_step=0, strength=0.1),
            _make_node(2, born_step=0, strength=0.9),
            _make_node(3, born_step=0, strength=0.5),
        ]
        candidates = scorer.select_candidates(nodes, current_step=100)
        self.assertGreaterEqual(len(candidates), 2)
        for i in range(len(candidates) - 1):
            self.assertGreaterEqual(candidates[i].score, candidates[i + 1].score)


# ===========================================================================
# CompressionRouter tests
# ===========================================================================

class TestCompressionRouter(unittest.TestCase):
    def test_short_path_default(self):
        """Low score should route to short_path."""
        router = CompressionRouter(deep_threshold=0.7, age_threshold_steps=500)
        c = CompressionCandidate(eid=1, born_step=400, summary="test", score=0.5)
        route = router.route(c, current_step=600)
        self.assertEqual(route, "short_path")

    def test_long_path_high_score_old(self):
        """High score + old → long_path."""
        router = CompressionRouter(deep_threshold=0.7, age_threshold_steps=500)
        c = CompressionCandidate(eid=1, born_step=0, summary="test", score=0.8)
        route = router.route(c, current_step=600)
        self.assertEqual(route, "long_path")

    def test_short_path_high_score_young(self):
        """High score but young → short_path."""
        router = CompressionRouter(deep_threshold=0.7, age_threshold_steps=500)
        c = CompressionCandidate(eid=1, born_step=500, summary="test", score=0.8)
        route = router.route(c, current_step=600)
        self.assertEqual(route, "short_path")

    def test_archive_always_deep(self):
        """Archive memory_class always goes deep."""
        router = CompressionRouter(deep_threshold=0.7, age_threshold_steps=500)
        c = CompressionCandidate(eid=1, born_step=500, summary="test", score=0.3,
                                  memory_class="archive")
        route = router.route(c, current_step=600)
        self.assertEqual(route, "long_path")

    def test_route_all(self):
        """route_all should update route field on all candidates."""
        router = CompressionRouter(deep_threshold=0.7, age_threshold_steps=100)
        candidates = [
            CompressionCandidate(eid=1, born_step=0, summary="a", score=0.8),
            CompressionCandidate(eid=2, born_step=400, summary="b", score=0.3),
        ]
        router.route_all(candidates, current_step=500)
        self.assertEqual(candidates[0].route, "long_path")
        self.assertEqual(candidates[1].route, "short_path")


# ===========================================================================
# CompressionExecutor tests
# ===========================================================================

class TestCompressionExecutor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.deep_store = DeepMemoryStore(Path(self.tmpdir) / "deep")
        self.entities = {
            1: MockEntity(1, born_step=0, payload={
                "summary": "Test memory 1", "strength": 0.6,
                "type": "episode", "memory_class": "core",
            }),
            2: MockEntity(2, born_step=0, payload={
                "summary": "Test memory 2", "strength": 0.8,
                "type": "episode", "memory_class": "core",
            }),
        }
        self.graph = MockMemoryGraph(self.entities)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_short_path_reduces_strength(self):
        """Short-path should reduce strength and mark compressed."""
        executor = CompressionExecutor(self.graph, self.deep_store)
        candidate = CompressionCandidate(
            eid=1, born_step=0, summary="test", score=0.5, route="short_path",
        )
        event = executor.execute([candidate], step=100, trigger="manual")

        self.assertEqual(event.compressed, 1)
        self.assertEqual(event.exported_deep, 0)
        payload = self.entities[1].payload
        self.assertTrue(payload.get("compressed"))
        self.assertLess(payload["strength"], 0.6)

    def test_long_path_exports(self):
        """Long-path should export to deep store and mark exported."""
        executor = CompressionExecutor(self.graph, self.deep_store)
        candidate = CompressionCandidate(
            eid=2, born_step=0, summary="test deep", score=0.8, route="long_path",
        )
        event = executor.execute([candidate], step=200, trigger="corridor_exit")

        self.assertEqual(event.compressed, 0)
        self.assertEqual(event.exported_deep, 1)
        payload = self.entities[2].payload
        self.assertTrue(payload.get("exported_deep"))

        # Verify deep store has the memory
        stats = self.deep_store.stats()
        self.assertEqual(stats["count"], 1)

    def test_missing_entity_retained(self):
        """Missing entity should be counted as retained (not crash)."""
        executor = CompressionExecutor(self.graph, self.deep_store)
        candidate = CompressionCandidate(
            eid=999, born_step=0, summary="ghost", score=0.5, route="short_path",
        )
        event = executor.execute([candidate], step=100, trigger="manual")
        self.assertEqual(event.retained, 1)

    def test_history_tracking(self):
        """Executor should track event history."""
        executor = CompressionExecutor(self.graph, self.deep_store)
        candidate = CompressionCandidate(
            eid=1, born_step=0, summary="test", score=0.5, route="short_path",
        )
        executor.execute([candidate], step=100, trigger="manual")
        executor.execute([candidate], step=200, trigger="corridor_exit")

        history = executor.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["trigger"], "manual")
        self.assertEqual(history[1]["trigger"], "corridor_exit")


# ===========================================================================
# DeepMemoryStore tests
# ===========================================================================

class TestDeepMemoryStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = DeepMemoryStore(Path(self.tmpdir) / "deep", dim=16)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_candidate(self, eid: int) -> CompressionCandidate:
        return CompressionCandidate(
            eid=eid, born_step=eid * 10, summary=f"Memory {eid}",
            score=0.5 + eid * 0.05, memory_class="core",
        )

    def test_export_and_recall(self):
        """Export a memory, then recall it by EID."""
        c = self._make_candidate(1)
        emb = np.random.randn(16).astype(np.float32)
        self.store.export(c, emb, {"type": "episode", "affect_tag": "joy"})

        recalled = self.store.recall(1)
        self.assertIsNotNone(recalled)
        self.assertEqual(recalled.eid, 1)
        self.assertEqual(recalled.summary, "Memory 1")
        self.assertEqual(recalled.metadata.get("affect_tag"), "joy")

    def test_export_and_query(self):
        """Export multiple memories, query should return similar ones."""
        np.random.seed(42)
        for i in range(5):
            c = self._make_candidate(i)
            # Create embeddings with some structure
            emb = np.zeros(16, dtype=np.float32)
            emb[i % 16] = 1.0
            emb += np.random.randn(16).astype(np.float32) * 0.1
            self.store.export(c, emb, {"type": "episode"})

        # Query with embedding similar to memory 0
        query_emb = np.zeros(16, dtype=np.float32)
        query_emb[0] = 1.0
        results = self.store.query(query_emb, top_k=3, min_similarity=0.0)

        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 3)
        # First result should be memory 0 (most similar)
        self.assertEqual(results[0].eid, 0)

    def test_query_empty_store(self):
        """Query on empty store should return empty list."""
        q = np.random.randn(16).astype(np.float32)
        results = self.store.query(q, top_k=5)
        self.assertEqual(len(results), 0)

    def test_recall_missing(self):
        """Recall of non-existent EID returns None."""
        result = self.store.recall(999)
        self.assertIsNone(result)

    def test_stats_empty(self):
        """Stats on empty store."""
        stats = self.store.stats()
        self.assertEqual(stats["count"], 0)
        self.assertIsNone(stats["oldest_born_step"])

    def test_stats_with_data(self):
        """Stats after exports."""
        for i in range(3):
            c = self._make_candidate(i)
            self.store.export(c, None, {"type": "episode"})

        stats = self.store.stats()
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["oldest_born_step"], 0)
        self.assertEqual(stats["newest_born_step"], 20)

    def test_export_no_embedding(self):
        """Export without embedding should work (no shard write)."""
        c = self._make_candidate(1)
        mem = self.store.export(c, None, {"type": "episode"})
        self.assertIsNotNone(mem)
        self.assertIsNone(mem.embedding_ref)

    def test_persistence(self):
        """Data should persist across store instances."""
        c = self._make_candidate(1)
        self.store.export(c, None, {"type": "episode"})

        # Create new store pointing to same dir
        store2 = DeepMemoryStore(Path(self.tmpdir) / "deep", dim=16)
        recalled = store2.recall(1)
        self.assertIsNotNone(recalled)
        self.assertEqual(recalled.summary, "Memory 1")


# ===========================================================================
# Integration tests
# ===========================================================================

class TestTryCompressIntegration(unittest.TestCase):
    """Test try_compress with mock fabric."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.fabric = MagicMock()
        self.fabric.data_dir = self.tmpdir
        self.fabric._event_detectors = {}
        self.fabric._compression_executors = {}
        self.fabric._deep_stores = {}

        # Set up a mock graph with entities
        entities = {}
        for i in range(10):
            entities[i] = MockEntity(i, born_step=0, payload={
                "summary": f"Memory {i}",
                "type": "episode",
                "kind": "episode",
                "tier": "relational",
                "memory_class": "core",
                "strength": 0.3 + (i * 0.05),
                "canon": False,
                "created_at": 0,
                "half_life": 30.0,
                "retrieval_count": i,
            })
        self.graph = MockMemoryGraph(entities)
        self.graph.data_dir = os.path.join(self.tmpdir, "graph")
        os.makedirs(self.graph.data_dir, exist_ok=True)
        self.fabric.private_graphs = {"default/test_agent": self.graph}

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_full_compression_cycle(self):
        """Corridor exit should trigger compression and produce event."""
        # First call: set corridor state
        tri_mod_in = _make_tri_mod(in_corridor=True, cycle_stage=1)
        result = try_compress(self.fabric, "test_agent", tri_mod_in, step=200, workspace_id="default")
        self.assertIsNone(result)  # No trigger yet

        # Second call: corridor exit
        tri_mod_out = _make_tri_mod(in_corridor=False, cycle_stage=1)
        result = try_compress(self.fabric, "test_agent", tri_mod_out, step=201, workspace_id="default")

        self.assertIsNotNone(result)
        self.assertIsInstance(result, CompressionEvent)
        self.assertEqual(result.trigger, "corridor_exit")
        self.assertGreater(result.candidates_evaluated, 0)

    def test_no_trigger_no_compression(self):
        """Stable state should not trigger compression."""
        tri_mod = _make_tri_mod(in_corridor=True, cycle_stage=1)
        result1 = try_compress(self.fabric, "test_agent", tri_mod, step=100, workspace_id="default")
        result2 = try_compress(self.fabric, "test_agent", tri_mod, step=101, workspace_id="default")
        self.assertIsNone(result1)
        self.assertIsNone(result2)

    def test_compression_disabled_no_graph(self):
        """Missing graph should return None gracefully."""
        tri_mod_in = _make_tri_mod(in_corridor=True)
        try_compress(self.fabric, "missing_agent", tri_mod_in, step=100, workspace_id="default")

        tri_mod_out = _make_tri_mod(in_corridor=False)
        result = try_compress(self.fabric, "missing_agent", tri_mod_out, step=101, workspace_id="default")
        self.assertIsNone(result)


class TestEmptyGraphNoCrash(unittest.TestCase):
    """Compression on empty memory graph should not crash."""

    def test_empty_graph(self):
        tmpdir = tempfile.mkdtemp()
        try:
            fabric = MagicMock()
            fabric.data_dir = tmpdir
            fabric._event_detectors = {}
            fabric._compression_executors = {}
            fabric._deep_stores = {}
            fabric.private_graphs = {"default/agent": MockMemoryGraph({})}

            tri_mod_in = _make_tri_mod(in_corridor=True)
            try_compress(fabric, "agent", tri_mod_in, step=100, workspace_id="default")

            tri_mod_out = _make_tri_mod(in_corridor=False)
            result = try_compress(fabric, "agent", tri_mod_out, step=101, workspace_id="default")
            # Should return event with 0 candidates
            self.assertIsNotNone(result)
            self.assertEqual(result.candidates_evaluated, 0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestAllProtectedNothingCompressed(unittest.TestCase):
    """All canon nodes → 0 compressed."""

    def test_all_protected(self):
        tmpdir = tempfile.mkdtemp()
        try:
            fabric = MagicMock()
            fabric.data_dir = tmpdir
            fabric._event_detectors = {}
            fabric._compression_executors = {}
            fabric._deep_stores = {}

            entities = {
                1: MockEntity(1, born_step=0, payload={
                    "summary": "Seed memory", "type": "seed", "kind": "seed",
                    "canon": True, "strength": 0.9, "created_at": 0,
                }),
                2: MockEntity(2, born_step=0, payload={
                    "summary": "Identity", "type": "identity", "kind": "identity",
                    "canon": True, "strength": 0.9, "created_at": 0,
                }),
            }
            graph = MockMemoryGraph(entities)
            graph.data_dir = os.path.join(tmpdir, "g")
            os.makedirs(graph.data_dir, exist_ok=True)
            fabric.private_graphs = {"default/agent": graph}

            tri_mod_in = _make_tri_mod(in_corridor=True)
            try_compress(fabric, "agent", tri_mod_in, step=200, workspace_id="default")
            tri_mod_out = _make_tri_mod(in_corridor=False)
            result = try_compress(fabric, "agent", tri_mod_out, step=201, workspace_id="default")

            self.assertIsNotNone(result)
            self.assertEqual(result.compressed, 0)
            self.assertEqual(result.exported_deep, 0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestConcurrentAgentsIsolated(unittest.TestCase):
    """Two agents should compress independently."""

    def test_isolated_agents(self):
        tmpdir = tempfile.mkdtemp()
        try:
            fabric = MagicMock()
            fabric.data_dir = tmpdir
            fabric._event_detectors = {}
            fabric._compression_executors = {}
            fabric._deep_stores = {}

            ws = "default"
            for agent in ("alice", "bob"):
                entities = {
                    i: MockEntity(i, born_step=0, payload={
                        "summary": f"{agent} memory {i}", "type": "episode",
                        "kind": "episode", "memory_class": "core", "strength": 0.3,
                        "canon": False, "created_at": 0, "half_life": 30.0,
                    })
                    for i in range(5)
                }
                graph = MockMemoryGraph(entities)
                graph.data_dir = os.path.join(tmpdir, agent)
                os.makedirs(graph.data_dir, exist_ok=True)
                fabric.private_graphs[f"{ws}/{agent}"] = graph

            # Alice corridor exit
            try_compress(fabric, "alice", _make_tri_mod(in_corridor=True), step=100, workspace_id=ws)
            result_a = try_compress(fabric, "alice", _make_tri_mod(in_corridor=False), step=101, workspace_id=ws)

            # Bob should have separate detector (composite keys)
            self.assertIn(f"{ws}/alice", fabric._event_detectors)
            bob_det = fabric._event_detectors.get(f"{ws}/bob")
            # Bob hasn't had any calls yet, so should not have a detector
            self.assertIsNone(bob_det)

            # Bob corridor exit
            try_compress(fabric, "bob", _make_tri_mod(in_corridor=True), step=100, workspace_id=ws)
            result_b = try_compress(fabric, "bob", _make_tri_mod(in_corridor=False), step=101, workspace_id=ws)

            self.assertIsNotNone(result_a)
            self.assertIsNotNone(result_b)
            # Both should have independent detectors (composite keys)
            self.assertIn(f"{ws}/alice", fabric._event_detectors)
            self.assertIn(f"{ws}/bob", fabric._event_detectors)
            self.assertIsNot(
                fabric._event_detectors[f"{ws}/alice"],
                fabric._event_detectors[f"{ws}/bob"],
            )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ===========================================================================
# CompressionEvent serialization
# ===========================================================================

class TestCompressionEventSerialization(unittest.TestCase):
    def test_to_dict(self):
        """CompressionEvent should serialize to JSON-safe dict."""
        event = CompressionEvent(
            step=100, trigger="corridor_exit",
            candidates_evaluated=5, compressed=3, exported_deep=1, retained=1,
        )
        d = event.to_dict()
        self.assertEqual(d["step"], 100)
        self.assertEqual(d["trigger"], "corridor_exit")
        # Ensure JSON-serializable
        json.dumps(d)


# ===========================================================================
# DeepMemory serialization
# ===========================================================================

class TestDeepMemorySerialization(unittest.TestCase):
    def test_roundtrip(self):
        """DeepMemory should survive to_dict → from_dict roundtrip."""
        mem = DeepMemory(
            eid=42, born_step=10, compressed_step=100,
            summary="Hello world", compression_score=0.75,
            original_motif_id="motif_001", memory_class="core",
            embedding_ref={"shard": 0, "row": 5, "dim": 384},
            metadata={"affect_tag": "joy", "type": "episode"},
        )
        d = mem.to_dict()
        json_str = json.dumps(d)
        restored = DeepMemory.from_dict(json.loads(json_str))

        self.assertEqual(restored.eid, 42)
        self.assertEqual(restored.summary, "Hello world")
        self.assertEqual(restored.compression_score, 0.75)
        self.assertEqual(restored.embedding_ref, {"shard": 0, "row": 5, "dim": 384})


if __name__ == "__main__":
    unittest.main()
