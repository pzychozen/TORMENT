"""A3D8 legacy world lifecycle characterization.

The tests freeze process-local physics and its deliberately surprising
interaction with later whole-payload serialization.  They do not alter the
legacy memory kernel.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from torment_service.embeddings import HashEmbedding
from torment_service.kernel.seed_entities import SeedWorld
from torment_service.kernel.trajectory_v2 import TrajectoryPathsV2
from torment_service.memory_graph import MemoryGraph


def _graph(tmp_path, monkeypatch: pytest.MonkeyPatch) -> MemoryGraph:
    monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "v2")
    return MemoryGraph(str(tmp_path / "graph"), embedder=HashEmbedding())


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (None, [0.0, 0.0, 0.0]),
        (2.5, [2.5, 0.0, 0.0]),
        ([2.5, -3.0], [2.5, -3.0, 0.0]),
        ([2.5, -3.0, 4.0], [2.5, -3.0, 4.0]),
    ),
)
def test_fresh_memory_uses_exact_vec3_genesis_defaults_and_fresh_histories(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    raw,
    expected,
) -> None:
    graph = _graph(tmp_path, monkeypatch)
    try:
        extra = {} if raw is None else {"seed_pos0": raw, "seed_v0": raw}
        eid = graph.add_memory(
            "world genesis",
            np.ones(384, dtype=np.float32),
            "episodic",
            0.5,
            0.8,
            30.0,
            user_id="agent",
            step=17,
            extra_payload=extra,
        )
        entity = graph.entities[eid]
        assert entity.born_step == 17
        assert entity.channel == 0
        assert entity.alive is True
        assert entity.pos.tolist() == expected
        assert entity.vel.tolist() == expected
        assert entity.vel0.tolist() == expected
        assert entity.payload["pos"] == expected
        assert entity.payload["vel"] == expected
        assert entity.payload["vel0"] == expected
        assert entity.r_history == [float(np.hypot(expected[0], expected[1]))]
        assert entity.z_history == [expected[2]]
        assert entity.x_history == [expected[0]]
        assert entity.y_history == [expected[1]]
        assert len(entity.trail) == 1
        assert entity.trail[0].tolist() == expected
        assert graph.world.dt == 1.0
        assert graph.world.drag == 0.02
        assert graph.world.drift.tolist() == [0.0, 0.0, 0.0]
        assert graph.world.trail_len == 200
    finally:
        graph.close()


def test_reload_has_empty_world_histories_and_restarts_from_durable_payload(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _graph(tmp_path, monkeypatch)
    try:
        eid = graph.add_memory(
            "reload world",
            np.ones(384, dtype=np.float32),
            "episodic",
            0.5,
            0.8,
            30.0,
            step=9,
            extra_payload={"seed_pos0": [2.0, 3.0], "seed_v0": [1.0, -1.0, 0.5]},
        )
        graph.step_world(1, classify_every=0, log_every=0)
        assert graph.entities[eid].pos.tolist() != graph.entities[eid].payload["pos"]
    finally:
        graph.close()

    reloaded = MemoryGraph(str(tmp_path / "graph"), embedder=HashEmbedding())
    try:
        entity = reloaded.entities[eid]
        assert entity.born_step == 9
        assert entity.channel == 0
        assert entity.alive is True
        assert entity.pos.tolist() == [2.0, 3.0, 0.0]
        assert entity.vel.tolist() == [1.0, -1.0, 0.5]
        assert entity.vel0.tolist() == [1.0, -1.0, 0.5]
        assert entity.trail == []
        assert entity.r_history == []
        assert entity.z_history == []
        assert entity.x_history == []
        assert entity.y_history == []
        reloaded.step_world(2, classify_every=0, log_every=0)
        assert entity.vel.tolist() == pytest.approx([0.98, -0.98, 0.49])
        assert entity.pos.tolist() == pytest.approx([2.98, 2.02, 0.49])
        assert len(entity.trail) == len(entity.r_history) == 1
    finally:
        reloaded.close()


def test_nonkinematic_successor_resets_live_kinematics_but_retains_histories_and_labels(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _graph(tmp_path, monkeypatch)
    try:
        eid = graph.add_memory(
            "reset world",
            np.ones(384, dtype=np.float32),
            "episodic",
            0.5,
            0.8,
            30.0,
            step=1,
            extra_payload={"seed_v0": [1.0, 0.0, 0.0]},
        )
        graph.step_world(50, classify_every=50, log_every=0)
        entity = graph.entities[eid]
        moved_pos = entity.pos.copy()
        trail_count = len(entity.trail)
        history_count = len(entity.r_history)
        assert entity.payload["traj_last_classify_step"] == 50

        graph.update_payload(eid, {"ordinary_patch": "yes"})

        assert entity.pos.tolist() == [0.0, 0.0, 0.0]
        assert entity.vel.tolist() == [1.0, 0.0, 0.0]
        assert entity.vel0.tolist() == [1.0, 0.0, 0.0]
        assert entity.pos.tolist() != moved_pos.tolist()
        assert len(entity.trail) == trail_count
        assert len(entity.r_history) == history_count
        assert entity.payload["traj_last_classify_step"] == 50
        current_node = json.loads(Path(graph.meta_path).read_text(encoding="utf-8").splitlines()[-1])
        assert current_node["payload"]["ordinary_patch"] == "yes"
        assert current_node["payload"]["traj_last_classify_step"] == 50

        graph.step_world(51, classify_every=0, log_every=0)
        assert entity.vel.tolist() == pytest.approx([0.98, 0.0, 0.0])
        assert entity.pos.tolist() == pytest.approx([0.98, 0.0, 0.0])
        assert len(entity.trail) == trail_count + 1
        assert len(entity.r_history) == history_count + 1
    finally:
        graph.close()


def test_explicit_kinematic_patch_resets_runtime_and_records_v2_reset_boundary(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _graph(tmp_path, monkeypatch)
    try:
        eid = graph.add_memory(
            "explicit reset",
            np.ones(384, dtype=np.float32),
            "episodic",
            0.5,
            0.8,
            30.0,
        )
        graph.step_world(1, classify_every=0, log_every=1)
        graph.update_payload(eid, {"pos": [8.0, 9.0, 10.0], "vel": [2.0, 3.0, 4.0], "vel0": [5.0, 6.0, 7.0]})
        entity = graph.entities[eid]
        assert entity.pos.tolist() == [8.0, 9.0, 10.0]
        assert entity.vel.tolist() == [2.0, 3.0, 4.0]
        assert entity.vel0.tolist() == [5.0, 6.0, 7.0]
        boundaries = [
            json.loads(line)
            for line in TrajectoryPathsV2(Path(graph.data_dir)).boundaries.read_text(encoding="utf-8").splitlines()
        ]
        reset = next(item for item in boundaries if item["type"] == "ENTITY_KINEMATIC_RESET")
        assert reset["eid"] == eid
        assert reset["last_observed_step"] == 1
        assert reset["last_observed_frame_seq"] == 1
    finally:
        graph.close()


def test_abort_removes_live_world_entity_without_rewinding_allocator(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _graph(tmp_path, monkeypatch)
    try:
        aborted = graph.spawn_memory(
            "abort me",
            np.ones(384, dtype=np.float32),
            "episodic",
            0.5,
            0.8,
            30.0,
        )
        assert aborted in graph.entities
        assert any(entity.eid == aborted for entity in graph.world.entities)
        graph.abort_unflushed_node(aborted)
        assert aborted not in graph.entities
        assert all(entity.eid != aborted for entity in graph.world.entities)
        next_eid = graph.spawn_memory(
            "allocator remains monotonic",
            np.ones(384, dtype=np.float32),
            "episodic",
            0.5,
            0.8,
            30.0,
        )
        assert next_eid == aborted + 1
    finally:
        graph.close()


def test_dead_world_entity_is_skipped_and_fresh_alive_payload_is_not_authoritative(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _graph(tmp_path, monkeypatch)
    try:
        eid = graph.add_memory(
            "alive quirk",
            np.ones(384, dtype=np.float32),
            "episodic",
            0.5,
            0.8,
            30.0,
            extra_payload={"alive": False, "seed_v0": [1.0, 0.0, 0.0]},
        )
        entity = graph.entities[eid]
        # Fresh spawn does not read the payload's alive key, whereas reload does.
        assert entity.alive is True
        entity.alive = False
        graph.step_world(1, classify_every=0, log_every=0)
        assert entity.pos.tolist() == [0.0, 0.0, 0.0]
    finally:
        graph.close()


def test_seed_world_default_truncates_trail_without_truncating_histories() -> None:
    world = SeedWorld(trail_len=2)
    entity = world.spawn(0, 0, np.zeros(3), np.ones(3), {})
    for _ in range(3):
        world.step()
    assert len(entity.trail) == 2
    assert len(entity.r_history) == len(entity.z_history) == len(entity.x_history) == len(entity.y_history) == 4
