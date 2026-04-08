"""Tests for Checkpoint and Promotion systems (Phase 5).

Covers:
  - Checkpoint serialization / deserialization round-trip
  - ModelState complex field preservation
  - CorridorMonitor EMA field preservation
  - Checkpoint save / load / prune
  - Promotion evaluation criteria scoring
  - Promotion forced vs threshold decisions
  - Promote_chunk creates correct distilled node
  - Retrieval counting persistence
  - Promotion suggestion scanning
  - Maintenance tool functions
"""
import json
import os
import shutil
import sys
import tempfile
import traceback

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.checkpoint import (
    serialize_model_state, deserialize_model_state,
    serialize_corridor_monitor, deserialize_corridor_monitor,
    save_checkpoint, load_latest_checkpoint, restore_from_checkpoint,
    get_checkpoint_dir, build_motif_summary,
)
from torment_service.promotion import (
    evaluate_promotion, promote_chunk, suggest_promotions,
    load_retrieval_counts, save_retrieval_counts, increment_retrieval_counts,
    RETRIEVAL_COUNT_THRESHOLD, PROMOTION_SCORE_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp():
    return tempfile.mkdtemp(prefix="torment_p5_test_")

# Trusted root for checkpoint path-containment checks in tests.
_BASE_DIR = tempfile.gettempdir()


def _make_model_state():
    """Create a ModelState with realistic values."""
    from torment_service.kernel.model_core import ModelState
    Omega = np.array([0.5 + 0.3j, -0.2 + 0.8j, 0.4 - 0.6j], dtype=np.complex128)
    state = ModelState(Omega=Omega)
    state.phi_index = 7
    state.cycle_stage = 3
    state.identity_state = 5
    state.z = 0.42
    state.z_mem = 0.031
    state.Z_macro[:] = [0.1, 0.2, 0.42]
    state.Z_chiral[:] = [-0.05, 0.08, 0.02]
    state.Z_vec[:] = [0.12, 0.3, 0.44]
    state.t = 125.5
    state.step = 2510
    state._char_mod = {"g_mod": 0.22, "theta_lock_mod": 0.25}
    return state


def _make_corridor_monitor():
    """Create a CorridorMonitor with accumulated EMA state."""
    from torment_service.memory_kernel import CorridorMonitor
    mon = CorridorMonitor()
    mon.prev_xy = np.array([1.5, -0.3], dtype=float)
    mon.prev_uxy = np.array([0.1, 0.2, 0.8], dtype=float)
    mon.tear_score_ema = 0.12
    mon.align_ema = 0.85
    mon.prox_ema = 0.45
    mon.surv_ema = 1.7
    mon.coh_ema = 0.62
    return mon


class _FakeMemoryGraph:
    """Minimal mock for testing promote_chunk."""
    def __init__(self):
        self.entities = {}
        self._spawned = []
        self._flushed = []
        self._next_eid = 9000

    def spawn_memory(self, summary, embedding, mtype, strength, confidence,
                     half_life_days, links, canon, user_id, step, extra_payload=None):
        eid = self._next_eid
        self._next_eid += 1
        self._spawned.append({
            "eid": eid, "summary": summary, "mtype": mtype,
            "strength": strength, "half_life_days": half_life_days,
            "canon": canon, "extra_payload": extra_payload or {},
        })
        # Create a minimal entity object
        class _Ent:
            pass
        ent = _Ent()
        ent.eid = eid
        ent.payload = extra_payload or {}
        self.entities[eid] = ent
        return eid

    def flush_node(self, eid):
        self._flushed.append(eid)


class _FakeEmbedder:
    def embed(self, text):
        # Deterministic hash embedding
        h = hash(text) % (2**31)
        np.random.seed(h)
        return np.random.randn(384).astype(np.float32)


# ---------------------------------------------------------------------------
# Test: Checkpoint Serialization
# ---------------------------------------------------------------------------

class TestCheckpointSerialization:
    def test_model_state_round_trip(self):
        state = _make_model_state()
        data = serialize_model_state(state)
        restored = deserialize_model_state(data)

        # Omega must survive complex serialization
        assert np.allclose(state.Omega, restored.Omega, atol=1e-10)
        assert restored.phi_index == 7
        assert restored.cycle_stage == 3
        assert restored.identity_state == 5
        assert abs(restored.z - 0.42) < 1e-10
        assert abs(restored.z_mem - 0.031) < 1e-10
        assert abs(restored.t - 125.5) < 1e-10
        assert restored.step == 2510
        assert np.allclose(state.Z_macro, restored.Z_macro, atol=1e-10)
        assert np.allclose(state.Z_chiral, restored.Z_chiral, atol=1e-10)
        assert np.allclose(state.Z_vec, restored.Z_vec, atol=1e-10)
        assert restored._char_mod == {"g_mod": 0.22, "theta_lock_mod": 0.25}

    def test_corridor_monitor_round_trip(self):
        mon = _make_corridor_monitor()
        data = serialize_corridor_monitor(mon)
        restored = deserialize_corridor_monitor(data)

        assert np.allclose(mon.prev_xy, restored.prev_xy, atol=1e-10)
        assert np.allclose(mon.prev_uxy, restored.prev_uxy, atol=1e-10)
        assert abs(restored.tear_score_ema - 0.12) < 1e-10
        assert abs(restored.align_ema - 0.85) < 1e-10
        assert abs(restored.prox_ema - 0.45) < 1e-10
        assert abs(restored.surv_ema - 1.7) < 1e-10
        assert abs(restored.coh_ema - 0.62) < 1e-10

    def test_corridor_monitor_none_prevs(self):
        """CorridorMonitor with None prev_xy/prev_uxy should round-trip."""
        from torment_service.memory_kernel import CorridorMonitor
        mon = CorridorMonitor()  # prev_xy and prev_uxy are None by default
        data = serialize_corridor_monitor(mon)
        restored = deserialize_corridor_monitor(data)
        assert restored.prev_xy is None
        assert restored.prev_uxy is None

    def test_serialization_is_json_safe(self):
        state = _make_model_state()
        mon = _make_corridor_monitor()
        data = {
            "model_state": serialize_model_state(state),
            "corridor_monitor": serialize_corridor_monitor(mon),
        }
        # Must serialize without error
        s = json.dumps(data)
        # Must parse back
        parsed = json.loads(s)
        assert "model_state" in parsed


# ---------------------------------------------------------------------------
# Test: Checkpoint Save / Load
# ---------------------------------------------------------------------------

class TestCheckpointSaveLoad:
    # New API: save_checkpoint(data_dir, workspace_id, agent_id, step, ...)
    #          load_latest_checkpoint(data_dir, workspace_id, agent_id)
    _WS = "test_ws"
    _AG = "test_agent"

    def test_save_and_load_round_trip(self):
        tmp = _tmp()
        try:
            state = _make_model_state()
            mon = _make_corridor_monitor()

            path = save_checkpoint(
                data_dir=tmp,
                workspace_id=self._WS,
                agent_id=self._AG,
                step=500,
                model_state=state,
                corridor_monitor=mon,
                character_state_dict={"drift_score": 0.12, "seed_id": "test_v1"},
                motif_summary={"total_count": 5, "top_motifs": []},
                shard_snapshot={"active_shard": 0, "next_row": 42},
            )
            assert path is not None
            assert os.path.exists(path)

            loaded = load_latest_checkpoint(tmp, self._WS, self._AG)
            assert loaded is not None
            assert loaded["step"] == 500
            assert loaded["character_state"]["drift_score"] == 0.12
            assert loaded["shard_snapshot"]["next_row"] == 42
        finally:
            shutil.rmtree(tmp)

    def test_restore_from_checkpoint(self):
        tmp = _tmp()
        try:
            state = _make_model_state()
            mon = _make_corridor_monitor()

            save_checkpoint(
                data_dir=tmp, workspace_id=self._WS, agent_id=self._AG,
                step=1000, model_state=state, corridor_monitor=mon,
            )
            loaded = load_latest_checkpoint(tmp, self._WS, self._AG)
            restored = restore_from_checkpoint(loaded)

            assert restored["step"] == 1000
            assert np.allclose(state.Omega, restored["model_state"].Omega, atol=1e-10)
            assert abs(restored["corridor_monitor"].surv_ema - 1.7) < 1e-10
        finally:
            shutil.rmtree(tmp)

    def test_prune_old_checkpoints(self):
        tmp = _tmp()
        try:
            state = _make_model_state()
            mon = _make_corridor_monitor()

            # Save 15 checkpoints, keep max 5
            for i in range(15):
                save_checkpoint(
                    data_dir=tmp, workspace_id=self._WS, agent_id=self._AG,
                    step=(i + 1) * 100, model_state=state, corridor_monitor=mon,
                    max_checkpoints=5,
                )

            from torment_service.checkpoint import _build_checkpoint_dir
            ckpt_dir = _build_checkpoint_dir(tmp, self._WS, self._AG)
            files = [f for f in os.listdir(ckpt_dir) if f.endswith(".json")]
            assert len(files) == 5
            # Highest steps should survive
            steps = sorted([int(f.split("_")[1].split(".")[0]) for f in files])
            assert steps == [1100, 1200, 1300, 1400, 1500]
        finally:
            shutil.rmtree(tmp)

    def test_load_empty_directory(self):
        tmp = _tmp()
        try:
            loaded = load_latest_checkpoint(tmp, self._WS, self._AG)
            assert loaded is None
        finally:
            shutil.rmtree(tmp)

    def test_loads_latest_of_multiple(self):
        tmp = _tmp()
        try:
            state = _make_model_state()
            mon = _make_corridor_monitor()
            save_checkpoint(data_dir=tmp, workspace_id=self._WS, agent_id=self._AG, step=100, model_state=state, corridor_monitor=mon)
            save_checkpoint(data_dir=tmp, workspace_id=self._WS, agent_id=self._AG, step=500, model_state=state, corridor_monitor=mon)
            save_checkpoint(data_dir=tmp, workspace_id=self._WS, agent_id=self._AG, step=300, model_state=state, corridor_monitor=mon)

            loaded = load_latest_checkpoint(tmp, self._WS, self._AG)
            assert loaded["step"] == 500  # highest step number
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: Promotion Evaluation
# ---------------------------------------------------------------------------

class TestPromotionEvaluation:
    def test_canon_auto_promotes(self):
        result = evaluate_promotion(
            chunk_text="Ryuki's care is expressed through pressure.",
            chunk_id="test_001",
            is_canon=True,
        )
        assert result.promote is True
        assert result.criteria["canon"] == 1.0
        assert "canon" in result.reason.lower()

    def test_user_approved_promotes(self):
        result = evaluate_promotion(
            chunk_text="Any text here.",
            chunk_id="test_002",
            user_approved=True,
        )
        assert result.promote is True
        assert "user-approved" in result.reason.lower()

    def test_low_score_rejects(self):
        result = evaluate_promotion(
            chunk_text="The weather was nice today.",
            chunk_id="test_003",
            retrieval_count=0,
        )
        assert result.promote is False
        assert result.score < PROMOTION_SCORE_THRESHOLD

    def test_high_retrieval_contributes(self):
        result = evaluate_promotion(
            chunk_text="Important passage about identity.",
            chunk_id="test_004",
            retrieval_count=RETRIEVAL_COUNT_THRESHOLD + 5,
        )
        assert result.criteria["retrieval"] > 0.5

    def test_motif_alignment_with_seed(self):
        seed_emb = np.random.randn(384).astype(np.float32)
        # Chunk embedding very similar to seed
        chunk_emb = seed_emb + 0.01 * np.random.randn(384).astype(np.float32)

        result = evaluate_promotion(
            chunk_text="Deeply aligned passage.",
            chunk_id="test_005",
            chunk_embedding=chunk_emb,
            seed_embedding=seed_emb,
        )
        assert result.criteria["motif_alignment"] > 0.5

    def test_result_is_serializable(self):
        result = evaluate_promotion(
            chunk_text="Test text.",
            chunk_id="test_006",
        )
        d = result.to_dict()
        s = json.dumps(d)
        parsed = json.loads(s)
        assert "promote" in parsed
        assert "score" in parsed
        assert "criteria" in parsed


# ---------------------------------------------------------------------------
# Test: Promotion Execution
# ---------------------------------------------------------------------------

class TestPromotionExecution:
    def test_promote_chunk_creates_distilled_node(self):
        graph = _FakeMemoryGraph()
        embedder = _FakeEmbedder()

        eid = promote_chunk(
            chunk_id="chunk_001",
            chunk_text="Ryuki expresses care through pressure, not comfort.",
            doc_id="doc_ryuki_setup",
            memory_graph=graph,
            embedder=embedder,
            step=42,
        )
        assert eid is not None
        assert eid >= 9000

        # Verify the spawned memory
        assert len(graph._spawned) == 1
        spawned = graph._spawned[0]
        assert spawned["mtype"] == "identity"
        assert spawned["half_life_days"] == 3650.0
        assert spawned["canon"] is True
        assert spawned["extra_payload"]["kind"] == "canon_promotion"
        assert spawned["extra_payload"]["tier"] == "core_identity"
        assert spawned["extra_payload"]["memory_class"] == "core"
        assert spawned["extra_payload"]["source_ref"]["doc_id"] == "doc_ryuki_setup"
        assert spawned["extra_payload"]["source_ref"]["chunk_id"] == "chunk_001"

        # Verify flush was called
        assert eid in graph._flushed

    def test_promote_truncates_long_text(self):
        graph = _FakeMemoryGraph()
        embedder = _FakeEmbedder()
        long_text = "A" * 600

        eid = promote_chunk(
            chunk_id="chunk_long",
            chunk_text=long_text,
            doc_id="doc_test",
            memory_graph=graph,
            embedder=embedder,
        )
        assert eid is not None
        assert len(graph._spawned[0]["summary"]) <= 500


# ---------------------------------------------------------------------------
# Test: Retrieval Counting
# ---------------------------------------------------------------------------

class TestRetrievalCounting:
    def test_save_and_load(self):
        tmp = _tmp()
        try:
            counts = {"chunk_a": 3, "chunk_b": 7}
            save_retrieval_counts(tmp, counts)
            loaded = load_retrieval_counts(tmp)
            assert loaded == counts
        finally:
            shutil.rmtree(tmp)

    def test_increment(self):
        tmp = _tmp()
        try:
            increment_retrieval_counts(tmp, ["chunk_x", "chunk_y", "chunk_x"])
            counts = load_retrieval_counts(tmp)
            assert counts["chunk_x"] == 2
            assert counts["chunk_y"] == 1

            # Increment again
            increment_retrieval_counts(tmp, ["chunk_x"])
            counts = load_retrieval_counts(tmp)
            assert counts["chunk_x"] == 3
        finally:
            shutil.rmtree(tmp)

    def test_empty_dir_returns_empty(self):
        tmp = _tmp()
        try:
            counts = load_retrieval_counts(tmp)
            assert counts == {}
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Test: Promotion Suggestions
# ---------------------------------------------------------------------------

class TestPromotionSuggestions:
    def test_suggest_with_mock_archive(self):
        """Test suggestion scanning against a mock archive store."""
        class _MockArchive:
            def __init__(self):
                self._chunks = {}
                self._documents = {}
                self._chunk_embeddings = {}

        class _MockChunk:
            def __init__(self, chunk_id, doc_id, text):
                self.chunk_id = chunk_id
                self.doc_id = doc_id
                self.text = text

        class _MockDoc:
            def __init__(self, doc_id, metadata=None):
                self.doc_id = doc_id
                self.metadata = metadata or {}

        store = _MockArchive()
        store._documents["doc1"] = _MockDoc("doc1", {"canon": True})
        store._chunks["c1"] = _MockChunk("c1", "doc1", "Canon text about Ryuki")
        store._chunks["c2"] = _MockChunk("c2", "doc1", "Normal text about weather")

        suggestions = suggest_promotions(
            archive_store=store,
            retrieval_counts={"c1": 10, "c2": 0},
            max_suggestions=5,
        )
        assert len(suggestions) > 0
        # Canon chunk with high retrieval should score higher
        assert suggestions[0]["chunk_id"] == "c1"
        assert suggestions[0]["score"] > suggestions[-1]["score"] if len(suggestions) > 1 else True


# ---------------------------------------------------------------------------
# Test: Checkpoint dir helper
# ---------------------------------------------------------------------------

class TestCheckpointHelpers:
    def test_get_checkpoint_dir(self):
        path = get_checkpoint_dir("/data", "ws1", "agent1")
        assert "ws1" in path
        assert "agent1" in path
        assert "checkpoints" in path

    def test_build_motif_summary_empty(self):
        class _Reg:
            motifs = {}
        summary = build_motif_summary(_Reg())
        assert summary["total_count"] == 0
        assert summary["top_motifs"] == []


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_phase5_tests():
    tests = [
        # Checkpoint serialization
        ("P5.1 ModelState round-trip", TestCheckpointSerialization().test_model_state_round_trip),
        ("P5.2 CorridorMonitor round-trip", TestCheckpointSerialization().test_corridor_monitor_round_trip),
        ("P5.3 CorridorMonitor None prevs", TestCheckpointSerialization().test_corridor_monitor_none_prevs),
        ("P5.4 Serialization JSON-safe", TestCheckpointSerialization().test_serialization_is_json_safe),
        # Checkpoint save/load
        ("P5.5 Save+Load round-trip", TestCheckpointSaveLoad().test_save_and_load_round_trip),
        ("P5.6 Restore from checkpoint", TestCheckpointSaveLoad().test_restore_from_checkpoint),
        ("P5.7 Prune old checkpoints", TestCheckpointSaveLoad().test_prune_old_checkpoints),
        ("P5.8 Load empty dir", TestCheckpointSaveLoad().test_load_empty_directory),
        ("P5.9 Loads latest of multiple", TestCheckpointSaveLoad().test_loads_latest_of_multiple),
        # Promotion evaluation
        ("P5.10 Canon auto-promotes", TestPromotionEvaluation().test_canon_auto_promotes),
        ("P5.11 User-approved promotes", TestPromotionEvaluation().test_user_approved_promotes),
        ("P5.12 Low score rejects", TestPromotionEvaluation().test_low_score_rejects),
        ("P5.13 High retrieval contributes", TestPromotionEvaluation().test_high_retrieval_contributes),
        ("P5.14 Motif alignment with seed", TestPromotionEvaluation().test_motif_alignment_with_seed),
        ("P5.15 Result serializable", TestPromotionEvaluation().test_result_is_serializable),
        # Promotion execution
        ("P5.16 Distilled node creation", TestPromotionExecution().test_promote_chunk_creates_distilled_node),
        ("P5.17 Truncates long text", TestPromotionExecution().test_promote_truncates_long_text),
        # Retrieval counting
        ("P5.18 Count save+load", TestRetrievalCounting().test_save_and_load),
        ("P5.19 Count increment", TestRetrievalCounting().test_increment),
        ("P5.20 Empty dir returns empty", TestRetrievalCounting().test_empty_dir_returns_empty),
        # Suggestions
        ("P5.21 Suggest with mock archive", TestPromotionSuggestions().test_suggest_with_mock_archive),
        # Helpers
        ("P5.22 Checkpoint dir path", TestCheckpointHelpers().test_get_checkpoint_dir),
        ("P5.23 Motif summary empty", TestCheckpointHelpers().test_build_motif_summary_empty),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}")
            traceback.print_exc()
            failed += 1

    return passed, failed


if __name__ == "__main__":
    p, f = run_phase5_tests()
    print(f"\nPhase 5: {p} passed, {f} failed")
    if f > 0:
        exit(1)
