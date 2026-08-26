from __future__ import annotations

import asyncio
import json
import shutil
import struct
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.kernel.trajectory_v2 import (
    CHUNK_HEADER,
    DYNAMIC_RECORD,
    STEP_HEADER,
    DynamicRecordV2,
    TrajectoryChunkReaderV2,
    TrajectoryPathsV2,
    TrajectoryV2Verifier,
    TrajectoryV2Writer,
    iter_v2_dynamic_records,
    sha256_file,
)
from torment_service.sqlite_index import IndexManager


def entity(eid: int, *, pos=(1.0, 2.0, 3.0), vel=(0.1, 0.2, 0.3)):
    return SimpleNamespace(
        eid=eid, pos=np.asarray(pos, dtype=np.float64), vel=np.asarray(vel, dtype=np.float64),
        vel0=np.asarray(vel, dtype=np.float64), born_step=0, channel=1, alive=True, payload={},
    )


class TestTrajectoryV2FrameIdentity:
    def setup_method(self):
        self.root = Path(tempfile.mkdtemp(prefix="torment_trajectory_v2_"))

    def teardown_method(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_dynamic_record_remains_exact_56_byte_float64_payload(self):
        record = DynamicRecordV2((1 << 64) - 1, (-0.0, float("inf"), 1.2345678901234567),
                                 (float("-inf"), 3.0, -4.5))
        packed = record.pack()
        assert DYNAMIC_RECORD.format == "<Q6d"
        assert DYNAMIC_RECORD.size == len(packed) == 56
        assert DynamicRecordV2.unpack(packed).pack() == packed
        assert packed == struct.pack("<Q6d", (1 << 64) - 1, -0.0, float("inf"),
                                     1.2345678901234567, float("-inf"), 3.0, -4.5)

    def test_repeated_step_and_eid_are_two_valid_frames(self):
        writer = TrajectoryV2Writer(str(self.root), chunk_steps=8)
        subject = entity(7)
        assert writer.write_step([subject], 25).frame_seq == 1
        subject.pos = np.asarray((9.0, 8.0, 7.0), dtype=np.float64)
        assert writer.write_step([subject], 25).frame_seq == 2
        assert writer.close().ok

        report = TrajectoryV2Verifier(str(self.root)).verify()
        assert report.valid, report.to_dict()
        rows = list(iter_v2_dynamic_records(str(self.root)))
        assert [(row["step"], row["frame_seq"], row["eid"]) for row in rows] == [(25, 1, 7), (25, 2, 7)]
        assert rows[-1]["pos"] == [9.0, 8.0, 7.0]

    def test_duplicate_eid_within_one_frame_is_invalid(self):
        writer = TrajectoryV2Writer(str(self.root))
        duplicate = entity(7)
        assert writer.write_step([duplicate, duplicate], 1).ok
        assert writer.close().ok
        report = TrajectoryV2Verifier(str(self.root)).verify()
        assert not report.valid
        assert any(issue["code"] == "DUPLICATE_EID_IN_FRAME" for issue in report.issues)

    def test_frame_sequence_must_be_exactly_monotonic(self):
        writer = TrajectoryV2Writer(str(self.root))
        assert writer.write_step([entity(7)], 1).ok
        assert writer.write_step([entity(7)], 1).ok
        assert writer.close().ok
        chunk = next(TrajectoryPathsV2(self.root).chunks.rglob("*.trj2"))
        raw = bytearray(chunk.read_bytes())
        second_header = CHUNK_HEADER.size + STEP_HEADER.size + DYNAMIC_RECORD.size
        values = list(STEP_HEADER.unpack(raw[second_header:second_header + STEP_HEADER.size]))
        values[1] = 99
        raw[second_header:second_header + STEP_HEADER.size] = STEP_HEADER.pack(*values)
        chunk.write_bytes(bytes(raw))
        manifest_path = TrajectoryPathsV2(self.root).manifest
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["chunk_sha256"] = sha256_file(chunk)
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        report = TrajectoryV2Verifier(str(self.root)).verify()
        assert not report.valid
        assert any(issue["code"] == "FRAME_SEQUENCE_INVALID" for issue in report.issues)

    def test_manifest_reports_frame_sequence_range_and_count(self):
        writer = TrajectoryV2Writer(str(self.root))
        assert writer.write_step([entity(7)], 25).ok
        assert writer.write_step([entity(7)], 25).ok
        assert writer.close().ok
        entry = json.loads(TrajectoryPathsV2(self.root).manifest.read_text(encoding="utf-8"))
        assert entry["schema_version"] == "trajectory-v2.2"
        assert {"frame_seq_from", "frame_seq_to", "frame_count", "step_from", "step_to"} <= set(entry)
        assert (entry["frame_seq_from"], entry["frame_seq_to"], entry["frame_count"]) == (1, 2, 2)

    def test_live_allows_one_current_open_tail_but_sealed_rejects_it_then_close_seals(self):
        writer = TrajectoryV2Writer(str(self.root))
        assert writer.write_step([entity(7)], 1).ok
        live = TrajectoryV2Verifier(str(self.root)).verify(mode="live")
        assert live.valid, live.to_dict()
        assert live.active_open_tails == 1
        assert any(note["code"] == "ACTIVE_OPEN_TAIL" for note in live.notices)
        sealed = TrajectoryV2Verifier(str(self.root)).verify(mode="sealed")
        assert not sealed.valid
        assert any(issue["code"] == "INCOMPLETE_FINAL_CHUNK" for issue in sealed.issues)
        assert writer.close().ok
        sealed_after_close = TrajectoryV2Verifier(str(self.root)).verify()
        assert sealed_after_close.valid, sealed_after_close.to_dict()
        assert not list(TrajectoryPathsV2(self.root).chunks.rglob("*.partial"))

    def test_restart_marks_old_partial_as_orphan_crash_condition(self):
        first = TrajectoryV2Writer(str(self.root))
        assert first.write_step([entity(7)], 1).ok
        # Simulate a crashed process without closing its active chunk.
        first._chunk_handle.close()
        first._chunk_handle = None
        second = TrajectoryV2Writer(str(self.root))
        assert second.write_step([entity(7)], 2).ok
        assert second.close().ok
        report = TrajectoryV2Verifier(str(self.root)).verify(mode="live")
        assert not report.valid
        assert any(issue["code"] == "ORPHANED_CRASH_PARTIAL" for issue in report.issues)
        diagnostics = TrajectoryPathsV2(self.root).diagnostics.read_text(encoding="utf-8")
        assert "ORPHANED_CRASH_PARTIAL" in diagnostics


class TestTrajectoryV2CacheAndSurfaces:
    def setup_method(self):
        self.root = Path(tempfile.mkdtemp(prefix="torment_trajectory_v2_cache_"))

    def teardown_method(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_sqlite_rebuild_retains_same_step_same_eid_across_frames(self):
        writer = TrajectoryV2Writer(str(self.root))
        subject = entity(7)
        assert writer.write_step([subject], 90).ok
        subject.pos = np.asarray((2.0, 2.0, 2.0), dtype=np.float64)
        assert writer.write_step([subject], 90).ok
        assert writer.close().ok
        idx = IndexManager(str(self.root / "index"))
        try:
            counts = idx.rebuild_from_jsonl(nodes_path="", trajectory_v2_root=str(self.root))
            assert counts["trajectory_index"] == 2
            assert idx.trajectory_cache_status() == {"status": "v2_ready", "schema": "trajectory-v2-cache.2"}
            entity_rows = idx.get_trajectory_range(90, 90, mode="entity", eid=7, limit=10)
            assert [(row["step"], row["frame_seq"], row["eid"]) for row in entity_rows] == [(90, 1, 7), (90, 2, 7)]
            assert idx.get_trajectory_range(90, 90, mode="all", row_limit=10)[-1]["pos_x"] == 2.0
        finally:
            idx.close()

    def test_legacy_jsonl_rebuild_reconstructs_second_same_step_frame(self):
        legacy = self.root / "legacy.jsonl"
        legacy.write_text("\n".join([
            json.dumps({"step": 25, "eid": 7, "pos": [1, 0, 0]}),
            json.dumps({"step": 25, "eid": 8, "pos": [2, 0, 0]}),
            json.dumps({"step": 25, "eid": 7, "pos": [3, 0, 0]}),
            json.dumps({"step": 25, "eid": 8, "pos": [4, 0, 0]}),
        ]) + "\n", encoding="utf-8")
        idx = IndexManager(str(self.root / "index"))
        try:
            counts = idx.rebuild_from_jsonl(nodes_path="", legacy_trajectories_path=str(legacy))
            assert counts["trajectory_index"] == 4
            rows = idx.get_trajectory_range(25, 25, mode="entity", eid=7, limit=10)
            assert [(row["frame_seq"], row["pos_x"]) for row in rows] == [(1, 1.0), (2, 3.0)]
        finally:
            idx.close()

    def test_endpoint_modes_report_frame_identity_and_deterministic_legacy_policy(self, monkeypatch):
        idx = IndexManager(str(self.root / "index"))
        try:
            assert idx.index_trajectory(25, 7, (1, 0, 0), epoch=1, frame_seq=1)
            assert idx.index_trajectory(25, 8, (2, 0, 0), epoch=1, frame_seq=1)
            assert idx.index_trajectory(25, 7, (3, 0, 0), epoch=1, frame_seq=2)
            assert idx.index_trajectory(25, 8, (4, 0, 0), epoch=1, frame_seq=2)
            from torment_service import app as appmod
            monkeypatch.setattr(appmod.fabric, "_get_sqlite_index", lambda *_args: idx)
            legacy = appmod.index_trajectory_range("ws", "agent", 25, 25, mode="legacy")
            entity_mode = appmod.index_trajectory_range("ws", "agent", 25, 25, mode="entity", eid=7, limit=10)
            all_mode = appmod.index_trajectory_range("ws", "agent", 25, 25, mode="all", row_limit=10)
            assert legacy["ok"] and legacy["results"][0]["frame_seq"] == 2 and legacy["results"][0]["eid"] == 8
            assert entity_mode["limit_unit"] == "frames"
            assert [row["frame_seq"] for row in entity_mode["results"]] == [1, 2]
            assert [row["frame_seq"] for row in all_mode["results"]] == [1, 1, 2, 2]
            assert legacy["representative_policy"] == "highest_eid_of_latest_frame_per_logical_step"
        finally:
            idx.close()

    def test_fastapi_shutdown_seals_fabric_owned_v2_graph(self, monkeypatch):
        from torment_service.fabric import TormentFabric
        from torment_service import app as appmod
        monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "v2")
        fabric = TormentFabric(data_dir=str(self.root / "fabric"))
        try:
            fabric.create_agent("ws", "agent")
            graph = fabric.private_graphs[fabric._agent_key("ws", "agent")]
            graph.add_memory("shutdown integration", np.ones(384), "episode", 0.5, 0.5, 30.0)
            graph.step_world(1, classify_every=0, log_every=1)
            monkeypatch.setattr(appmod, "fabric", fabric)
            asyncio.run(appmod._close_fabric_on_shutdown())
            report = TrajectoryV2Verifier(str(graph.data_dir)).verify(mode="sealed")
            assert report.valid, report.to_dict()
            assert not list(TrajectoryPathsV2(Path(graph.data_dir)).chunks.rglob("*.partial"))
        finally:
            fabric.close()


class TestMemoryGraphTrajectoryV2Integration:
    def test_v2_close_seals_graph_tail_and_reset_names_last_frame(self, monkeypatch):
        from torment_service.embeddings import HashEmbedding
        from torment_service.memory_graph import MemoryGraph

        root = Path(tempfile.mkdtemp(prefix="torment_graph_trajectory_v2_"))
        monkeypatch.setenv("TORMENT_TRAJECTORY_FORMAT", "v2")
        graph = MemoryGraph(str(root), embedder=HashEmbedding())
        try:
            eid = graph.add_memory("trajectory V2 integration", np.ones(384), "episode", 0.5, 0.5, 30.0)
            graph.step_world(1, classify_every=0, log_every=1)
            graph.update_payload(eid, {"pos": [8.0, 9.0, 10.0]})
        finally:
            graph.close()
        report = TrajectoryV2Verifier(str(root)).verify()
        assert report.valid, report.to_dict()
        boundaries = [json.loads(line) for line in TrajectoryPathsV2(root).boundaries.read_text(encoding="utf-8").splitlines()]
        reset = next(row for row in boundaries if row["type"] == "ENTITY_KINEMATIC_RESET")
        assert reset["last_observed_frame_seq"] == 1
        shutil.rmtree(root, ignore_errors=True)

    def test_default_format_stays_legacy(self, monkeypatch):
        from torment_service.embeddings import HashEmbedding
        from torment_service.memory_graph import MemoryGraph

        root = Path(tempfile.mkdtemp(prefix="torment_graph_trajectory_legacy_"))
        monkeypatch.delenv("TORMENT_TRAJECTORY_FORMAT", raising=False)
        graph = MemoryGraph(str(root), embedder=HashEmbedding())
        try:
            assert graph._trajectory_format == "legacy"
            assert not TrajectoryPathsV2(root).base.exists()
        finally:
            graph.close()
            shutil.rmtree(root, ignore_errors=True)
