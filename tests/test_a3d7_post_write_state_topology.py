"""A3D7 characterization locks for the remaining legacy post-write tail.

These tests deliberately record current behaviour.  They do not introduce a
native adapter, route selection, or any new storage capability.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from torment_service.bridges import BridgeRegistry
from torment_service.character import CharacterSeed, measure_drift
from torment_service.checkpoint import load_latest_checkpoint
from torment_service.compression import (
    CompressionCandidate,
    CompressionExecutor,
)
from torment_service.embeddings import HashEmbedding
from torment_service.memory_graph import MemoryGraph
from torment_service.motifs import Motif, MotifRegistry


def _motif(motif_id: str, *, centroid: list[float]) -> Motif:
    return Motif(
        motif_id=motif_id,
        domain_id="personal",
        label=motif_id,
        centroid=centroid,
        strength=0.5,
        members=[],
        contributing_agents=[],
        stability_score=0.5,
        created_ts=1,
        last_active_ts=1,
    )


def test_world_step_is_live_kinematics_with_diagnostic_durability_not_node_durability(
    tmp_path,
    monkeypatch,
) -> None:
    """A restart recovers the original node payload, not the stepped overlay."""
    monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "v2")
    root = tmp_path / "world"
    graph = MemoryGraph(str(root), embedder=HashEmbedding())
    try:
        eid = graph.add_memory(
            "world overlay characterization",
            np.ones(384, dtype=np.float32),
            "episodic",
            0.5,
            0.8,
            30.0,
            step=1,
            extra_payload={"seed_v0": [1.0, 0.0, 0.0]},
        )
        node_bytes_before_step = Path(graph.meta_path).read_bytes()
        assert graph.entities[eid].payload["pos"] == [0.0, 0.0, 0.0]

        graph.step_world(step=50, classify_every=50, log_every=1)

        assert graph.entities[eid].pos.tolist() != [0.0, 0.0, 0.0]
        assert graph.entities[eid].payload["pos"] == [0.0, 0.0, 0.0]
        assert graph.entities[eid].payload["traj_last_classify_step"] == 50
        assert Path(graph.meta_path).read_bytes() == node_bytes_before_step
        assert "TRAJ_CLASSIFY" in Path(graph.events_path).read_text(encoding="utf-8")
    finally:
        graph.close()

    restarted = MemoryGraph(str(root), embedder=HashEmbedding())
    try:
        assert restarted.entities[eid].pos.tolist() == [0.0, 0.0, 0.0]
        assert "traj_last_classify_step" not in restarted.entities[eid].payload
    finally:
        restarted.close()


def test_entropy_suggestion_is_side_state_but_auto_merge_rewrites_motif_truth(tmp_path) -> None:
    registry = MotifRegistry(str(tmp_path), "ws", "personal")
    registry.motifs = {
        "motif_personal_0001": _motif("motif_personal_0001", centroid=[1.0, 0.0]),
        "motif_personal_0002": _motif("motif_personal_0002", centroid=[1.0, 0.0]),
    }
    registry.save()
    motif_bytes_before = Path(registry.path).read_bytes()

    report = registry.update_entropy_and_suggest(
        target_n=1,
        entropy_high=0.1,
        sim_threshold=0.9,
        max_suggestions=5,
        auto_merge=False,
        auto_merge_trigger=0.1,
    )

    assert report["entropy_score"] >= 0.1
    assert Path(registry.path).read_bytes() == motif_bytes_before
    assert len(registry.list_merge_suggestions()) == 1
    assert Path(registry.merges_path).is_file()

    registry.update_entropy_and_suggest(
        target_n=1,
        entropy_high=0.1,
        sim_threshold=0.9,
        max_suggestions=5,
        auto_merge=True,
        auto_merge_trigger=0.1,
    )

    assert len(registry.motifs) == 1
    assert Path(registry.path).read_bytes() != motif_bytes_before
    assert registry.list_merge_suggestions(status="approved")


def test_compression_long_path_exports_before_core_patch_without_compensation(
    tmp_path,
    monkeypatch,
) -> None:
    import torment_service.embedding_store as embedding_store

    candidate = CompressionCandidate(eid=7, born_step=1, summary="candidate", route="long_path")
    monkeypatch.setattr(
        embedding_store,
        "load_embedding",
        lambda *_args, **_kwargs: np.asarray([0.25, 0.75], dtype=np.float32),
    )

    class _Store:
        def __init__(self, order: list[str], *, fail: bool = False) -> None:
            self.order = order
            self.fail = fail
            self.exports: list[tuple[object, object, object, int]] = []

        def export(self, candidate, embedding, payload, *, step: int) -> None:
            self.order.append("export")
            self.exports.append((candidate, embedding, payload, step))
            if self.fail:
                raise RuntimeError("deep store unavailable")

    class _Graph:
        def __init__(self, order: list[str], *, fail_update: bool = False) -> None:
            self.order = order
            self.fail_update = fail_update
            self._shard_reader = None
            self.data_dir = str(tmp_path)
            self.entities = {7: SimpleNamespace(payload={"strength": 0.8})}
            self.patches: list[dict[str, object]] = []

        def update_payload(self, eid: int, patch: dict[str, object]) -> None:
            assert eid == 7
            self.order.append("core_patch")
            self.patches.append(patch)
            if self.fail_update:
                raise RuntimeError("core update unavailable")

    success_order: list[str] = []
    success_graph = _Graph(success_order)
    success_store = _Store(success_order)
    success_event = CompressionExecutor(success_graph, success_store).execute(
        [candidate], step=20, trigger="periodic",
    )
    assert success_order == ["export", "core_patch"]
    assert success_event.exported_deep == 1
    assert success_event.retained == 0
    assert success_graph.patches[0]["exported_deep"] is True
    assert np.array_equal(success_store.exports[0][1], np.asarray([0.25, 0.75], dtype=np.float32))

    failed_core_order: list[str] = []
    failed_core_graph = _Graph(failed_core_order, fail_update=True)
    failed_core_store = _Store(failed_core_order)
    failed_core_event = CompressionExecutor(failed_core_graph, failed_core_store).execute(
        [candidate], step=21, trigger="periodic",
    )
    assert failed_core_order == ["export", "core_patch"]
    assert failed_core_event.exported_deep == 0
    assert failed_core_event.retained == 1
    assert len(failed_core_store.exports) == 1

    failed_export_order: list[str] = []
    failed_export_graph = _Graph(failed_export_order)
    failed_export_store = _Store(failed_export_order, fail=True)
    failed_export_event = CompressionExecutor(failed_export_graph, failed_export_store).execute(
        [candidate], step=22, trigger="periodic",
    )
    assert failed_export_order == ["export"]
    assert failed_export_event.exported_deep == 0
    assert failed_export_event.retained == 1
    assert failed_export_graph.patches == []


def test_character_drift_uses_cached_embedding_and_payload_born_step_semantics() -> None:
    seed = CharacterSeed(
        seed_id="seed",
        character_name="Character",
        seed_text="A stable characterization seed.",
        seed_motif_id="seed-motif",
        drift_window_steps=5,
    )
    graph = SimpleNamespace(
        entities={
            1: SimpleNamespace(payload={
                "user_id": "agent",
                "type": "episodic",
                "half_life": 30.0,
                "created_at": 10,
            }),
            2: SimpleNamespace(payload={
                "user_id": "agent",
                "type": "episodic",
                "half_life": 30.0,
                "born_step": 9,
            }),
        },
        _emb_by_eid={
            1: np.asarray([1.0, 0.0], dtype=np.float32),
            2: np.asarray([0.0, 1.0], dtype=np.float32),
        },
    )
    motif_registry = SimpleNamespace(
        motifs={"seed-motif": SimpleNamespace(centroid_np=lambda: np.asarray([0.0, 1.0], dtype=np.float32))},
    )

    report = measure_drift(
        graph=graph,
        motif_registry=motif_registry,
        coherence_field=None,
        seed=seed,
        agent_id="agent",
        current_step=10,
    )

    # ``created_at`` is counted for tiers but not used for the window; only
    # the payload's ``born_step`` makes the second cached vector recent.
    assert report["relational_count"] == 2
    assert report["total_recent"] == 1
    assert report["distance_to_seed"] == 0.0
    assert report["drift_score"] == 1.0


def test_corrupt_checkpoint_is_ignored_without_mutating_authoritative_memory(tmp_path) -> None:
    checkpoint_dir = tmp_path / "workspaces" / "ws" / "agents" / "agent" / "private" / "checkpoints"
    checkpoint_dir.mkdir(parents=True)
    corrupt = checkpoint_dir / "checkpoint_000010.json"
    corrupt.write_text('{"truncated":', encoding="utf-8")

    assert load_latest_checkpoint(str(tmp_path), "ws", "agent") is None
    assert corrupt.read_text(encoding="utf-8") == '{"truncated":'


def test_bridge_suggestions_are_persisted_side_store_without_motif_mutation(tmp_path) -> None:
    left = MotifRegistry(str(tmp_path), "ws", "left")
    right = MotifRegistry(str(tmp_path), "ws", "right")
    left.motifs = {"left-1": _motif("left-1", centroid=[1.0, 0.0])}
    right.motifs = {"right-1": _motif("right-1", centroid=[1.0, 0.0])}
    left.save()
    right.save()
    left_before = Path(left.path).read_bytes()
    right_before = Path(right.path).read_bytes()

    bridges = BridgeRegistry(str(tmp_path), "ws")
    suggested = bridges.suggest({"left": left, "right": right}, sim_threshold=0.9, max_new=5)

    assert len(suggested) == 1
    assert Path(bridges.path).is_file()
    assert Path(left.path).read_bytes() == left_before
    assert Path(right.path).read_bytes() == right_before
    restarted = BridgeRegistry(str(tmp_path), "ws")
    assert [(item.from_motif, item.to_motif, item.status) for item in restarted.bridges] == [
        ("left-1", "right-1", "suggested"),
    ]
