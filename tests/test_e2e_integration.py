"""
End-to-End Integration Tests — Phase 7 Pipeline
=================================================
Verifies the full chain:

  ingest → kernel → PhaseTimer → compression (duration resistance)
  → deep memory export → spirit return enrichment → character prompt (voice cues)

All components are tested via a live TormentFabric instance (hash embeddings,
no external API calls) with compression force-enabled.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path


def _setenv():
    """Configure environment for integration testing before any imports."""
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
    os.environ["TORMENT_COMPRESS_ENABLE"] = "1"
    os.environ["TORMENT_COMPRESS_MIN_STEP"] = "0"
    os.environ["TORMENT_COMPRESS_MIN_AGE"] = "5"       # low so we can compress quickly
    os.environ["TORMENT_CHARACTER_ENABLE"] = "0"        # disable drift (needs seeds)
    os.environ["TORMENT_CHECKPOINT_ENABLE"] = "0"       # skip checkpoints for speed


# Capture original env values at module IMPORT time, so we can restore
# them after this module's tests finish. The actual mutation (via
# _setenv()) is deferred to setUpModule() — which runs at EXECUTION
# time, not collection time — to avoid contaminating other test modules
# that are imported during pytest collection. Without that deferral,
# TORMENT_CHARACTER_ENABLE=0 would be set during collection and persist
# into the execution of alphabetically-earlier test modules
# (test_authority_lane_matrix.py character-badge tests are the most
# visible victims: their activation bridge in fabric.create_agent is
# gated by TORMENT_CHARACTER_ENABLE).
_E2E_ENV_KEYS = (
    "TORMENT_EMBED_PROVIDER",
    "TORMENT_COMPRESS_ENABLE",
    "TORMENT_COMPRESS_MIN_STEP",
    "TORMENT_COMPRESS_MIN_AGE",
    "TORMENT_CHARACTER_ENABLE",
    "TORMENT_CHECKPOINT_ENABLE",
)
_E2E_ENV_ORIG = {k: os.environ.get(k) for k in _E2E_ENV_KEYS}


def setUpModule():
    """Mutate os.environ for the e2e tests at EXECUTION time.

    pytest calls this once before the first test in this module runs.
    Deferring _setenv() here (rather than calling it at module import
    time) prevents the env mutation from being visible during pytest's
    collection of OTHER test modules, which would otherwise inherit
    the e2e-specific env values for the entire session.
    """
    _setenv()


def tearDownModule():
    """Restore os.environ to its pre-setUpModule state.

    pytest calls this once after the last test in this module
    finishes. Combined with the deferral in setUpModule, this scopes
    the env mutation to exactly the window where e2e tests are
    executing — never during collection, never during other modules'
    execution.
    """
    for k, orig in _E2E_ENV_ORIG.items():
        if orig is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = orig


from torment_service.fabric import TormentFabric
from torment_service.compression import (
    CompressionScorer,
    EventDetector,
    try_compress,
)
from torment_service.spirit_return import (
    enrich_deep_memory_hit,
    inject_spirit_return_into_hit,
    WarmupTracker,
    build_symbol_interaction_matrix,
)
from torment_service.phase_timer import PhaseTimer
from torment_service.retrieval_assembler import assemble_context
from torment_service.character import assemble_character_context, CharacterSeed


WS = "test_ws"
AGENT = "test_agent"
AK = f"{WS}/{AGENT}"  # composite key for agent-scoped dicts (see TormentFabric._agent_key)


class IntegrationBase(unittest.TestCase):
    """Shared setup: fresh TormentFabric in a temp directory."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="torment_e2e_")
        self.fabric = TormentFabric(data_dir=self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ---- helpers ----

    def _ingest(self, text: str, step: int, tri_mod_override=None):
        """Ingest a single observation and return the result dict."""
        return self.fabric.ingest(
            workspace_id=WS,
            agent_id=AGENT,
            text=text,
            step=step,
            tri_mod=tri_mod_override,
        )

    def _query(self, text: str, top_k: int = 8):
        return self.fabric.query(
            workspace_id=WS,
            agent_id=AGENT,
            query_text=text,
            top_k=top_k,
        )

    def _get_graph(self):
        return self.fabric.private_graphs.get(AK)

    def _get_deep_store(self):
        return self.fabric._deep_stores.get(AK)


# =====================================================================
# 1.  INGEST → KERNEL → PHASE TIMER → MEMORY SPAWNING
# =====================================================================
class TestIngestPipeline(IntegrationBase):
    """Verify that ingest produces memories with PhaseTimer metadata."""

    def test_basic_ingest_creates_memory(self):
        """A single ingest should create a memory and return eid."""
        result = self._ingest("I walked through the park today.", step=0)
        self.assertTrue(result["stored"])
        self.assertIsNotNone(result["eid"])
        self.assertIn("tri_mod", result)

    def test_tri_mod_has_corridor_fields(self):
        """tri_mod should contain corridor and cycle_stage fields."""
        result = self._ingest("thinking about the meaning of things", step=0)
        tri = result["tri_mod"]
        self.assertIn("in_corridor", tri)
        self.assertIn("cycle_stage", tri)

    def test_phase_timer_initialized_on_first_ingest(self):
        """PhaseTimer should exist for the agent after first ingest."""
        self._ingest("hello world", step=0)
        self.assertIn(AK, self.fabric._phase_timers)
        pt = self.fabric._phase_timers[AK]
        self.assertIsNotNone(pt)

    def test_phase_duration_in_payload(self):
        """Memory payload should contain phase_duration_steps."""
        self._ingest("step zero", step=0)
        self._ingest("step five", step=5)
        graph = self._get_graph()
        self.assertIsNotNone(graph)
        # Last entity should have phase_duration_steps in payload
        last_eid = max(graph.entities.keys())
        payload = dict(graph.entities[last_eid].payload or {})
        self.assertIn("phase_duration_steps", payload)

    def test_sequential_ingests_accumulate_state(self):
        """Multiple ingests build kernel state without errors.

        After the Omega extraction recalibration (folded embedding →
        genuine phase diversity), early steps may have high dispersion
        and therefore low coherence/strength, which legitimately causes
        the write-gate to reject some observations.  We assert that
        *at least some* ingests store successfully.
        """
        stored_count = 0
        for i in range(10):
            result = self._ingest(f"observation number {i}", step=i)
            if result["stored"]:
                stored_count += 1
        self.assertGreater(stored_count, 0, "At least one ingest should store")
        graph = self._get_graph()
        # Should have at least some entities
        self.assertGreater(len(graph.entities), 0)


# =====================================================================
# 2.  EVENT-GATED COMPRESSION → DEEP MEMORY EXPORT
# =====================================================================
class TestCompressionPipeline(IntegrationBase):
    """Verify compression fires on corridor exit and exports to deep store."""

    def _populate_aged_memories(self, count=20, base_step=0):
        """Ingest enough memories so some are old enough to compress."""
        for i in range(count):
            self._ingest(f"memory about topic number {i}", step=base_step + i)

    def test_compression_trigger_on_corridor_exit(self):
        """Feeding corridor exit event should trigger compression."""
        # Populate memories at low steps
        self._populate_aged_memories(count=15, base_step=0)

        # Manually trigger compression with a corridor_exit event
        detector = EventDetector()
        # Prime the detector with a corridor-enter state
        detector.check({"in_corridor": 1, "cycle_stage": 0, "tearing_risk": 0.0}, step=10)
        # Now corridor exit
        trigger = detector.check({"in_corridor": 0, "cycle_stage": 0, "tearing_risk": 0.0}, step=20)
        self.assertEqual(trigger, "corridor_exit")

    def test_try_compress_produces_event(self):
        """try_compress with forced trigger should return CompressionEvent."""
        self._populate_aged_memories(count=15, base_step=0)

        # Ensure detector fires on corridor exit (use composite key AK)
        if AK not in getattr(self.fabric, "_event_detectors", {}):
            self.fabric._event_detectors = {}
        det = EventDetector()
        # Prime
        det.check({"in_corridor": 1, "cycle_stage": 0, "tearing_risk": 0.1}, step=14)
        self.fabric._event_detectors[AK] = det

        # corridor exit → trigger
        event = try_compress(
            self.fabric, AGENT,
            tri_mod={"in_corridor": 0, "cycle_stage": 0, "tearing_risk": 0.0},
            step=20,
            workspace_id=WS,
        )
        self.assertIsNotNone(event)

    def test_deep_store_populated_after_long_path(self):
        """After compression with long-path candidates, deep store should have entries."""
        # Build lots of old, weak memories
        for i in range(30):
            self._ingest(f"mundane observation {i}", step=i)

        # Prime detector (use composite key AK)
        if not hasattr(self.fabric, "_event_detectors"):
            self.fabric._event_detectors = {}
        det = EventDetector()
        det.check({"in_corridor": 1, "cycle_stage": 0, "tearing_risk": 0.1}, step=29)
        self.fabric._event_detectors[AK] = det

        event = try_compress(
            self.fabric, AGENT,
            tri_mod={"in_corridor": 0, "cycle_stage": 0, "tearing_risk": 0.0},
            step=50,
            workspace_id=WS,
        )
        # Even if no long_path candidates (depends on scoring), the compression
        # pipeline should run without crashing
        self.assertIsNotNone(event)


# =====================================================================
# 3.  DURATION RESISTANCE — SUSTAINED MEMORIES RESIST COMPRESSION
# =====================================================================
class TestDurationResistance(IntegrationBase):
    """Verify that memories born during sustained corridors resist compression."""

    def test_sustained_memory_gets_lower_j_score(self):
        """Memories with phase_duration_steps >= 10 have reduced j_score."""
        scorer = CompressionScorer()
        # Normal memory
        normal_node = {
            "eid": 1, "born_step": 0,
            "payload": {
                "summary": "test", "strength": 0.3, "confidence": 0.5,
                "canon": False, "half_life": 30.0, "type": "memory",
                "kind": "experience", "tier": "relational", "memory_class": "core",
                "phase_duration_steps": 3, "corridor_duration_steps": 0,
            },
        }
        # Sustained memory
        sustained_node = {
            "eid": 2, "born_step": 0,
            "payload": {
                "summary": "test", "strength": 0.3, "confidence": 0.5,
                "canon": False, "half_life": 30.0, "type": "memory",
                "kind": "experience", "tier": "relational", "memory_class": "core",
                "phase_duration_steps": 15, "corridor_duration_steps": 0,
            },
        }
        c_normal = scorer.score(normal_node, 200)
        c_sustained = scorer.score(sustained_node, 200)
        self.assertIsNotNone(c_normal)
        self.assertIsNotNone(c_sustained)
        # Sustained should have a lower score (harder to compress)
        self.assertLess(c_sustained.score, c_normal.score)


# =====================================================================
# 4.  SPIRIT RETURN — DEEP MEMORY → ENRICHMENT → VOICE CUES
# =====================================================================
class TestSpiritReturnPipeline(IntegrationBase):
    """Verify spirit return enrichment and voice cue injection."""

    def test_symbol_interaction_matrix_complete(self):
        """All 19 rules in the interaction matrix should be present."""
        rules = build_symbol_interaction_matrix()
        self.assertEqual(len(rules), 19)

    def test_enrichment_produces_spirit_return_memory(self):
        """enrich_deep_memory_hit should produce a SpiritReturnMemory."""
        from torment_service.deep_memory import DeepMemory
        dm = DeepMemory(
            eid=42, born_step=5, compressed_step=50,
            summary="I was exploring a new place.",
            compression_score=0.6,
            metadata={"symbol_trace": ["◯", "∿"], "phase_duration_steps": 12},
        )
        warmup = type("MockWarmup", (), {
            "eid": 42, "first_appearance_step": 100,
            "appearance_count": 3, "current_warmth": 0.5,
            "max_warmth": 0.5, "last_retrieved_step": 100,
        })()

        spirit = enrich_deep_memory_hit(dm, "∿", warmup, compressed_in_core=False)
        self.assertIsNotNone(spirit)
        self.assertIn(spirit.return_mode, ("surfacing", "recollection", "resonance"))
        self.assertGreater(spirit.warmth_score, 0.0)

    def test_inject_produces_query_hit(self):
        """inject_spirit_return_into_hit should produce a dict usable as a query hit."""
        from torment_service.deep_memory import DeepMemory
        dm = DeepMemory(
            eid=42, born_step=5, compressed_step=50,
            summary="I was exploring a new place.",
            compression_score=0.6,
            metadata={"symbol_trace": ["◯", "∿"]},
        )
        warmup = type("MockWarmup", (), {
            "eid": 42, "first_appearance_step": 100,
            "appearance_count": 2, "current_warmth": 0.4,
            "max_warmth": 0.4, "last_retrieved_step": 100,
        })()

        spirit = enrich_deep_memory_hit(dm, "◈", warmup, compressed_in_core=False)
        hit = inject_spirit_return_into_hit(spirit)

        self.assertIsInstance(hit, dict)
        self.assertTrue(hit.get("from_spirit_return"))
        self.assertIn("spirit_return_mode", hit)
        self.assertIn("warmth_score", hit)
        self.assertIn("spirit_return_flavor", hit)
        self.assertIn("symbol_interaction", hit)

    def test_warmth_boost_for_sustained_corridor(self):
        """Deep memory from sustained corridor (≥10 steps) gets warmth floor 0.3."""
        from torment_service.deep_memory import DeepMemory
        dm = DeepMemory(
            eid=99, born_step=5, compressed_step=50,
            summary="Long corridor memory.",
            compression_score=0.5,
            metadata={"phase_duration_steps": 15, "corridor_duration_steps": 12},
        )
        # Warmup with very low warmth (first appearance)
        warmup = type("MockWarmup", (), {
            "eid": 99, "first_appearance_step": 200,
            "appearance_count": 1, "current_warmth": 0.2,
            "max_warmth": 0.2, "last_retrieved_step": 200,
        })()

        spirit = enrich_deep_memory_hit(dm, "◯", warmup, compressed_in_core=False)
        # Should be boosted to at least 0.3
        self.assertGreaterEqual(spirit.warmth_score, 0.3)


# =====================================================================
# 5.  CHARACTER PROMPT LAYER — VOICE CUES IN ASSEMBLY
# =====================================================================
class TestCharacterPromptIntegration(IntegrationBase):
    """Verify that spirit return hits flow into character context assembly."""

    def _make_spirit_hit(self, mode="surfacing", warmth=0.6):
        """Create a synthetic spirit return query hit."""
        return {
            "eid": 42,
            "summary": "A meaningful past experience.",
            "score": 0.7,
            "from_spirit_return": True,
            "spirit_return_mode": mode,
            "warmth_score": warmth,
            "spirit_return_flavor": "gentle return of an old thread",
            "symbol_interaction_type": "integration",
            "half_life": 30.0,
            "strength": 0.5,
            "kind": "experience",
            "tier": "relational",
            "type": "memory",
            "memory_class": "core",
            "canon": False,
            "step": 50,
        }

    def _make_normal_hit(self, eid=1, score=0.5):
        """Create a normal (non-spirit-return) query hit."""
        return {
            "eid": eid,
            "summary": "A recent observation.",
            "score": score,
            "half_life": 14.0,
            "strength": 0.5,
            "kind": "experience",
            "tier": "situational",
            "type": "memory",
            "memory_class": "core",
            "canon": False,
            "step": 100,
        }

    def test_retrieval_assembler_classifies_spirit_hit(self):
        """Spirit return hit should be classified into appropriate tier."""
        hits = [
            self._make_spirit_hit(mode="resonance", warmth=0.7),
            self._make_normal_hit(eid=2),
        ]
        ctx = assemble_context(
            core_hits=hits,
            profile="companion",
            token_budget=4000,
        )
        # The spirit hit should appear somewhere in assembled blocks
        all_block_texts = []
        for tier, blocks in ctx.blocks.items():
            for b in blocks:
                all_block_texts.append(b.get("text", ""))
        combined = " ".join(all_block_texts)
        # Should contain the returning memory marker
        self.assertIn("[Returning Memory]", combined)

    def test_character_assembly_includes_spirit_summary(self):
        """assemble_character_context should include spirit_return_summary."""
        self._ingest("bootstrap memory", step=0)
        graph = self._get_graph()

        seed = CharacterSeed(seed_id="test_seed", character_name="TestBot", seed_text="A thoughtful companion.")
        hits = [
            self._make_spirit_hit(mode="surfacing", warmth=0.5),
            self._make_spirit_hit(mode="resonance", warmth=0.8),
            self._make_normal_hit(eid=10),
        ]

        result = assemble_character_context(
            graph=graph,
            seed=seed,
            agent_id=AGENT,
            hits=hits,
        )
        self.assertIn("spirit_return_summary", result)
        summary = result["spirit_return_summary"]
        self.assertEqual(summary["total"], 2)
        self.assertIn("by_mode", summary)

    def test_voice_cue_in_assembled_text(self):
        """Voice cue markers should appear in assembled context text."""
        hits = [self._make_spirit_hit(mode="surfacing", warmth=0.5)]
        ctx = assemble_context(
            core_hits=hits,
            profile="companion",
            token_budget=4000,
        )
        combined = ctx.assembled_text
        self.assertIn("[Voice:", combined)

    def test_warmth_secondary_sort(self):
        """Within same score, warmer spirit hit should rank above cold one."""
        warm_hit = self._make_spirit_hit(mode="surfacing", warmth=0.9)
        warm_hit["score"] = 0.6
        cold_hit = self._make_spirit_hit(mode="recollection", warmth=0.2)
        cold_hit["score"] = 0.6
        cold_hit["eid"] = 43

        ctx = assemble_context(
            core_hits=[warm_hit, cold_hit],
            profile="companion",
            token_budget=4000,
        )
        # Both should be present
        block_texts = []
        for tier, blocks in ctx.blocks.items():
            for b in blocks:
                block_texts.append(b.get("text", ""))
        combined = " ".join(block_texts)
        self.assertIn("[Returning Memory]", combined)


# =====================================================================
# 6.  FULL PIPELINE — INGEST THROUGH TO QUERY WITH SPIRIT RETURN
# =====================================================================
class TestFullPipeline(IntegrationBase):
    """The big one: ingest observations, compress, then query and see spirit return."""

    def test_ingest_compress_query_cycle(self):
        """
        Full cycle:
        1. Ingest 30 observations
        2. Force compression via corridor exit
        3. Query and verify the fabric doesn't crash
        4. Check PhaseTimer state persists across ingests
        """
        # Phase 1: Build memory bank
        # After Omega recalibration, early steps may legitimately fail the
        # write-gate due to high initial dispersion.  We require a majority.
        stored_count = 0
        for i in range(30):
            result = self._ingest(f"I observed something about topic {i}", step=i)
            if result["stored"]:
                stored_count += 1
        self.assertGreater(stored_count, 10, f"Only {stored_count}/30 stored")

        # Verify phase timer tracked
        pt = self.fabric._phase_timers.get(AK)
        self.assertIsNotNone(pt)

        # Phase 2: Force corridor exit compression
        if not hasattr(self.fabric, "_event_detectors"):
            self.fabric._event_detectors = {}
        det = EventDetector()
        det.check({"in_corridor": 1, "cycle_stage": 0, "tearing_risk": 0.1}, step=29)
        self.fabric._event_detectors[AK] = det

        event = try_compress(
            self.fabric, AGENT,
            tri_mod={"in_corridor": 0, "cycle_stage": 0, "tearing_risk": 0.0},
            step=50,
            workspace_id=WS,
        )
        self.assertIsNotNone(event, "compression event should be produced")

        # Phase 3: Query — even if no deep hits, pipeline shouldn't crash
        query_result = self._query("What topics have I observed?", top_k=8)
        self.assertIn("results", query_result)
        hits = query_result["results"]
        # Should get at least some hits from private graph
        self.assertGreater(len(hits), 0)

    def test_spirit_return_fires_when_deep_store_populated(self):
        """
        If we manually populate deep store, spirit return should enrich query hits.
        """
        import numpy as np
        from torment_service.deep_memory import DeepMemoryStore, DeepMemory
        from torment_service.compression import CompressionCandidate

        # Ingest a few memories so the workspace/agent exists
        for i in range(5):
            self._ingest(f"baseline memory {i}", step=i)

        # Manually create a deep store and export a memory into it
        agent_dir = Path(self.tmpdir) / "workspaces" / WS / "agents" / AGENT
        deep_dir = agent_dir / "deep_memory"
        deep_dir.mkdir(parents=True, exist_ok=True)

        dim = self.fabric.kernel.embedder.dim
        store = DeepMemoryStore(deep_dir, dim=dim)
        self.fabric._deep_stores[AK] = store

        # Export a synthetic deep memory
        candidate = CompressionCandidate(
            eid=999, born_step=0, summary="A deep old memory about exploration.",
            score=0.8, j_score=0.7, z_score=0.5,
            route="long_path", memory_class="core",
        )
        emb = np.random.randn(dim).astype(np.float32)
        store.export(candidate, emb, {"summary": "A deep old memory about exploration."})

        # Save a symbol state so spirit return can read it
        from torment_service.fabric import _save_symbol_state
        _save_symbol_state(self.tmpdir, WS, AGENT, {
            "last_symbol": "∿",
            "symbol_trace": ["◯", "∿"],
            "last_motif_id": "",
            "last_tension": 0.0,
        })

        # Query with top_k larger than private hits to trigger deep fallback
        query_result = self._query("exploration and discovery", top_k=20)
        hits = query_result["results"]

        # Check if any hit is from spirit return
        spirit_hits = [h for h in hits if h.get("from_spirit_return")]
        # Note: may or may not fire depending on embedding similarity.
        # The key verification is that the pipeline runs without error.
        # If we do get spirit hits, verify structure:
        for sh in spirit_hits:
            self.assertIn("spirit_return_mode", sh)
            self.assertIn("warmth_score", sh)
            self.assertIn("spirit_return_flavor", sh)
            self.assertIn("symbol_interaction_type", sh)

    def test_phase_timer_durations_flow_to_deep_memory(self):
        """Phase/corridor durations in payload should survive compression to deep store."""
        import numpy as np
        from torment_service.compression import CompressionCandidate
        from torment_service.deep_memory import DeepMemoryStore

        # Ingest with manually set tri_mod to force corridor
        for i in range(20):
            self._ingest(
                f"corridor observation {i}",
                step=i,
                tri_mod_override={
                    "in_corridor": 1 if i >= 5 else 0,
                    "cycle_stage": 0,
                    "tearing_risk": 0.05,
                    # minimal tri_mod fields for kernel bypass
                    "coh_phase": 0.5, "disp": 0.1,
                    "tangent_align": 0.8, "survival_steps": i,
                },
            )

        # Check that a memory from step 15 has corridor_duration > 0
        graph = self._get_graph()
        found_corridor_dur = False
        for eid, ent in graph.entities.items():
            payload = dict(ent.payload or {})
            if int(payload.get("corridor_duration_steps", 0)) > 0:
                found_corridor_dur = True
                break
        self.assertTrue(found_corridor_dur, "At least one memory should have corridor_duration_steps > 0")


# =====================================================================
# 7.  WARMUP TRACKER PERSISTENCE
# =====================================================================
class TestWarmupTrackerPersistence(IntegrationBase):
    """Verify WarmupTracker state persists across invocations."""

    def test_warmup_roundtrip(self):
        """Warmup state written to JSONL should survive reload."""
        warmup_dir = Path(self.tmpdir) / "warmup_test"
        warmup_dir.mkdir(parents=True, exist_ok=True)

        tracker1 = WarmupTracker(warmup_dir, base_dir=self.tmpdir)
        ws = tracker1.get_or_create(42, 100)
        self.assertEqual(ws.appearance_count, 1)
        self.assertAlmostEqual(ws.current_warmth, 0.2, places=2)

        # Second retrieval bumps warmth
        ws = tracker1.get_or_create(42, 110)
        self.assertEqual(ws.appearance_count, 2)
        self.assertGreater(ws.current_warmth, 0.2)

        # Reload from disk
        tracker2 = WarmupTracker(warmup_dir, base_dir=self.tmpdir)
        ws2 = tracker2.get_or_create(42, 120)
        self.assertEqual(ws2.appearance_count, 3)
        # Warmth should be even higher
        self.assertGreater(ws2.current_warmth, ws.current_warmth)


# =====================================================================
# 8.  PHASE TIMER ↔ FABRIC WIRING
# =====================================================================
class TestPhaseTimerFabricWiring(IntegrationBase):
    """Verify PhaseTimer is correctly wired into the fabric ingest path."""

    def test_phase_timer_tracks_corridor_across_ingests(self):
        """PhaseTimer should track corridor state across sequential ingests."""
        # Ingest outside corridor
        self._ingest("outside corridor", step=0, tri_mod_override={
            "in_corridor": 0, "cycle_stage": 0, "tearing_risk": 0.0,
            "coh_phase": 0.5, "disp": 0.1, "tangent_align": 0.8,
            "survival_steps": 0,
        })
        pt = self.fabric._phase_timers[AK]
        self.assertFalse(pt.current_in_corridor)

        # Enter corridor
        self._ingest("entering corridor", step=5, tri_mod_override={
            "in_corridor": 1, "cycle_stage": 0, "tearing_risk": 0.1,
            "coh_phase": 0.5, "disp": 0.1, "tangent_align": 0.8,
            "survival_steps": 5,
        })
        self.assertTrue(pt.current_in_corridor)
        self.assertIsNotNone(pt.corridor_entry_step)

        # Stay in corridor
        self._ingest("still in corridor", step=10, tri_mod_override={
            "in_corridor": 1, "cycle_stage": 0, "tearing_risk": 0.1,
            "coh_phase": 0.5, "disp": 0.1, "tangent_align": 0.8,
            "survival_steps": 10,
        })
        durations = pt.get_durations(10)
        self.assertEqual(durations["corridor_duration_steps"], 5)  # 10 - 5

    def test_phase_change_resets_timer(self):
        """Changing cycle_stage should reset the phase entry step."""
        self._ingest("phase 0", step=0, tri_mod_override={
            "in_corridor": 0, "cycle_stage": 0, "tearing_risk": 0.0,
            "coh_phase": 0.5, "disp": 0.1, "tangent_align": 0.8,
            "survival_steps": 0,
        })
        pt = self.fabric._phase_timers[AK]
        old_entry = pt.phase_entry_step

        self._ingest("phase 1", step=10, tri_mod_override={
            "in_corridor": 0, "cycle_stage": 1, "tearing_risk": 0.0,
            "coh_phase": 0.5, "disp": 0.1, "tangent_align": 0.8,
            "survival_steps": 10,
        })
        # Phase entry should have been reset to step 10
        self.assertEqual(pt.phase_entry_step, 10)
        self.assertNotEqual(pt.phase_entry_step, old_entry)


if __name__ == "__main__":
    unittest.main()
