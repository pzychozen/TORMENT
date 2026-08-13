"""Phase-2 execution harness for the current Core/MemoryGraph substrate.

This is deliberately tests-only.  Gate A compares only contractually durable
semantic state.  Gate B preserves observed seam behavior without changing any
production policy or storage format.
"""

import copy
import json
import os
import shutil
from pathlib import Path

import numpy as np
import pytest

from torment_service.embeddings import HashEmbedding
from torment_service.fabric import TormentFabric
from torment_service.memory_graph import MemoryGraph
from torment_service.sqlite_index import IndexManager


_DIM = 8
_ACTIVE_SRG = {"R_band": "A", "is_crystal": True, "heartbeat_class": "A"}


def _embed(slot: int) -> np.ndarray:
    value = np.zeros(_DIM, dtype=np.float32)
    value[int(slot) % _DIM] = 1.0
    return value


def _graph(path: Path, *, sqlite_index=None) -> MemoryGraph:
    return MemoryGraph(str(path), embedder=HashEmbedding(dim=_DIM), sqlite_index=sqlite_index)


def _add(
    graph: MemoryGraph,
    summary: str,
    slot: int,
    *,
    user_id: str = "agent",
    step: int = 1,
    extra_payload=None,
    links=None,
) -> int:
    return graph.add_memory(
        summary=summary,
        embedding=_embed(slot),
        mtype="episode",
        strength=0.7,
        confidence=0.8,
        half_life_days=30.0,
        user_id=user_id,
        step=step,
        extra_payload=extra_payload,
        links=links,
    )


def _rows(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _map_rows(graph: MemoryGraph):
    records = []
    for path in sorted(Path(graph.data_dir, "embeddings").glob("shard_*.map.jsonl")):
        records.extend(_rows(path))
    return records


def _portable(value):
    """Canonical JSON-compatible test snapshot; not a runtime-object snapshot."""
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str))


def _semantic_snapshot(graph: MemoryGraph, query: str, *, user_id: str):
    hits = graph.search(query, top_k=20, user_id=user_id)
    return {
        "nodes": [
            {
                "eid": int(eid),
                "born_step": int(ent.born_step),
                "channel": int(ent.channel),
                "alive": bool(ent.alive),
                "payload": _portable(ent.payload),
            }
            for eid, ent in sorted(graph.entities.items())
        ],
        "edges": _portable(graph.edges),
        "next_eid": int(graph.world._next_id),
        "search_eids": [int(hit["eid"]) for hit in hits],
    }


def _close_fabric_graphs(fabric: TormentFabric) -> None:
    """Idempotent cleanup for Fabric instances created by this test module."""
    for graph in list(getattr(fabric, "private_graphs", {}).values()):
        graph.close()
    for workspace in list(getattr(fabric, "workspaces", {}).values()):
        for graph in list(getattr(workspace, "shared_graphs", {}).values()):
            graph.close()
    fabric.close()


def _fabric_ingest(
    fabric: TormentFabric,
    text: str,
    *,
    step: int,
    scope: str = "private",
    nested_srg: bool = False,
) -> int:
    """Create a normal Fabric memory, optionally preserving the legacy gate shape."""
    extra_payload = {"payload": {"srg": dict(_ACTIVE_SRG)}} if nested_srg else None
    result = fabric.ingest(
        workspace_id="ws",
        agent_id="agent",
        text=text,
        step=step,
        domain_id="personal",
        scope=scope,
        tri_mod={"write_mult": 0.0},
        extra_payload=extra_payload,
        skip_packet_emission=True,
    )
    assert result["stored"] is True
    assert result["reinforced"] is False
    return int(result["eid"])


class TestGateACoreInvariants:
    def test_a1_durable_live_and_cold_semantics_match(self, tmp_path):
        graph = _graph(tmp_path / "golden")
        reopened = None
        try:
            first = graph.spawn_memory(
                summary="golden durable first",
                embedding=_embed(0),
                mtype="episode",
                strength=0.7,
                confidence=0.8,
                half_life_days=30.0,
                user_id="agent",
                step=11,
                links=["fixture-link"],
                extra_payload={"fixture": "v1", "scope": "private"},
            )
            graph.entities[first].payload["enriched"] = "before-flush"
            graph.flush_node(first)
            graph.update_payload(first, {"fixture": "v2", "updated": True})
            second = _add(
                graph,
                "golden durable second",
                1,
                step=12,
                extra_payload={"fixture": "second", "scope": "private"},
            )

            live = _semantic_snapshot(graph, "golden durable", user_id="agent")
            assert live["search_eids"] == [first, second]
            assert live["nodes"][0]["payload"]["embedding_ref"]
            assert live["edges"] and live["edges"][0]["src"] == first

            graph.close()
            reopened = _graph(tmp_path / "golden")
            cold = _semantic_snapshot(reopened, "golden durable", user_id="agent")

            # MUST_MATCH: canonical nodes, physical node fields, embedding refs,
            # stored edges, next EID, and deterministic semantic search ordering.
            assert cold == live
        finally:
            graph.close()
            if reopened is not None:
                reopened.close()

    def test_a2_ephemeral_changes_do_not_become_canonical(self, tmp_path):
        graph = _graph(tmp_path / "ephemeral")
        reopened = None
        try:
            durable = _add(
                graph,
                "durable before physics",
                2,
                extra_payload={
                    "seed_pos0": [1.0, 0.0, 0.0],
                    "seed_v0": [1.0, 0.0, 0.0],
                },
            )
            stored_pos = list(graph.entities[durable].payload["pos"])
            graph.step_world(step=1, classify_every=1, log_every=1)
            unflushed = graph.spawn_memory(
                summary="unflushed ephemeral candidate",
                embedding=_embed(3),
                mtype="episode",
                strength=0.7,
                confidence=0.8,
                half_life_days=30.0,
                user_id="agent",
                step=2,
            )
            graph.search("durable before physics", top_k=5, user_id="agent")

            # EXPECTED_TO_DIFFER: live physics/history/classification and derived
            # cache exist in RAM; the unflushed entity is live but noncanonical.
            assert not np.allclose(graph.entities[durable].pos, stored_pos)
            assert graph.entities[durable].payload["traj_last_classify_step"] == 1
            assert graph._emb_mat is not None
            assert unflushed in graph.entities

            graph.close()
            reopened = _graph(tmp_path / "ephemeral")

            # MUST_MATCH: the flushed node and its pre-step canonical payload.
            assert set(reopened.entities) == {durable}
            assert reopened.entities[durable].payload["summary"] == "durable before physics"
            assert reopened.entities[durable].payload["pos"] == stored_pos
            # EXPECTED_TO_DIFFER: RAM-only state and unflushed node do not reload.
            assert "traj_label" not in reopened.entities[durable].payload
            assert "traj_last_classify_step" not in reopened.entities[durable].payload
            assert reopened._emb_mat is None
            assert unflushed not in reopened.entities
            # Diagnostic/residue artifacts are intentionally independent of node
            # authority and remain observable after the restart.
            assert list(Path(graph.data_dir, "logs", "trajectories", "daily").glob("*.jsonl"))
            assert any(int(row["eid"]) == unflushed for row in _map_rows(reopened))
        finally:
            graph.close()
            if reopened is not None:
                reopened.close()

    def test_a3_spawn_without_flush_leaves_residue_but_no_cold_node(self, tmp_path):
        index = IndexManager(str(tmp_path / "index"))
        graph = _graph(tmp_path / "unflushed", sqlite_index=index)
        reopened = None
        try:
            eid = graph.spawn_memory(
                summary="unflushed only",
                embedding=_embed(4),
                mtype="episode",
                strength=0.7,
                confidence=0.8,
                half_life_days=30.0,
                user_id="agent",
                step=20,
                links=["residue-link"],
            )
            assert eid in graph.entities
            assert _rows(Path(graph.meta_path)) == []
            assert _map_rows(graph) and _map_rows(graph)[0]["eid"] == eid
            assert json.loads(Path(graph.data_dir, "embeddings", "manifest.json").read_text())["total_rows"] == 1
            assert [row["type"] for row in _rows(Path(graph.events_path))] == ["MEMORY_CREATE"]
            assert graph.edges and graph.edges[0]["src"] == eid
            assert index.get_recent_memories() == []
            assert len(index.get_events_by_type("MEMORY_CREATE")) == 1

            graph.close()
            reopened = _graph(tmp_path / "unflushed")
            assert reopened.entities == {}
            assert reopened.edges and reopened.edges[0]["src"] == eid
            # The allocator only recovers canonical node EIDs, so the trailing
            # unflushed EID is allocated again on the fresh graph.
            next_eid = reopened.spawn_memory(
                summary="next after unflushed",
                embedding=_embed(5),
                mtype="episode",
                strength=0.7,
                confidence=0.8,
                half_life_days=30.0,
                user_id="agent",
                step=21,
            )
            assert next_eid == eid
            assert [row["eid"] for row in _map_rows(reopened)] == [eid, eid]
        finally:
            graph.close()
            if reopened is not None:
                reopened.close()
            index.close()

    def test_a4_spawn_flush_and_add_memory_are_equivalent_creation_paths(self, tmp_path):
        graph = _graph(tmp_path / "creation-paths")
        reopened = None
        try:
            spawned = graph.spawn_memory(
                summary="same creation contract",
                embedding=_embed(6),
                mtype="episode",
                strength=0.7,
                confidence=0.8,
                half_life_days=30.0,
                user_id="agent",
                step=30,
                extra_payload={"contract": "equivalent"},
            )
            graph.flush_node(spawned)
            added = _add(
                graph,
                "same creation contract",
                7,
                step=30,
                extra_payload={"contract": "equivalent"},
            )
            assert len(_rows(Path(graph.meta_path))) == 2

            graph.close()
            reopened = _graph(tmp_path / "creation-paths")
            left = dict(reopened.entities[spawned].payload)
            right = dict(reopened.entities[added].payload)
            # NOT_COMPARABLE: allocation-specific embedding row and wall-clock
            # creation timestamp.  All creation semantics must match.
            for payload in (left, right):
                payload.pop("embedding_ref", None)
                payload.pop("created_ts", None)
            assert left == right
            assert reopened.search("same creation contract", top_k=5, user_id="agent")
        finally:
            graph.close()
            if reopened is not None:
                reopened.close()

    def test_a5_same_eid_update_recovers_last_row(self, tmp_path):
        graph = _graph(tmp_path / "updates")
        reopened = None
        try:
            eid = _add(graph, "update v1", 0, step=40, extra_payload={"version": "v1"})
            emb_ref = copy.deepcopy(graph.entities[eid].payload["embedding_ref"])
            graph.update_payload(eid, {"version": "v2"})
            graph.update_payload(eid, {"version": "v3", "v3_only": True})
            assert set(graph.entities) == {eid}
            assert len([row for row in _rows(Path(graph.meta_path)) if row["eid"] == eid]) == 3
            assert graph.entities[eid].payload["embedding_ref"] == emb_ref

            graph.close()
            reopened = _graph(tmp_path / "updates")
            assert set(reopened.entities) == {eid}
            assert reopened.entities[eid].payload["version"] == "v3"
            assert reopened.entities[eid].payload["v3_only"] is True
            assert reopened.entities[eid].payload["embedding_ref"] == emb_ref
            assert _add(reopened, "next update node", 1, step=41) == eid + 1
        finally:
            graph.close()
            if reopened is not None:
                reopened.close()

    def test_a6_eids_are_graph_local_and_physical_graphs_are_isolated(self, tmp_path):
        root = tmp_path / "workspaces" / "ws"
        paths = {
            "a": root / "agents" / "agent-a" / "private",
            "b": root / "agents" / "agent-b" / "private",
            "shared": root / "domains" / "personal" / "shared",
        }
        graphs = {name: _graph(path) for name, path in paths.items()}
        reopened = {}
        try:
            eids = {
                "a": _add(graphs["a"], "private-a", 0, user_id="agent-a", extra_payload={"graph": "a", "scope": "private"}),
                "b": _add(graphs["b"], "private-b", 1, user_id="agent-b", extra_payload={"graph": "b", "scope": "private"}),
                "shared": _add(graphs["shared"], "shared-c", 2, user_id="collective", extra_payload={"graph": "shared", "scope": "shared", "domain_id": "personal"}),
            }
            assert eids == {"a": 1, "b": 1, "shared": 1}
            graphs["a"].update_payload(1, {"changed_in": "a"})
            assert "changed_in" not in graphs["b"].entities[1].payload
            assert "changed_in" not in graphs["shared"].entities[1].payload
            assert graphs["a"].search("private-a", user_id="agent-a")[0]["eid"] == 1
            assert graphs["b"].search("private-b", user_id="agent-b")[0]["eid"] == 1
            assert graphs["shared"].search("shared-c")[0]["eid"] == 1

            for graph in graphs.values():
                graph.close()
            reopened = {name: _graph(path) for name, path in paths.items()}
            assert reopened["a"].entities[1].payload["changed_in"] == "a"
            assert reopened["b"].entities[1].payload["graph"] == "b"
            assert reopened["shared"].entities[1].payload["graph"] == "shared"
        finally:
            for graph in graphs.values():
                graph.close()
            for graph in reopened.values():
                graph.close()

    def test_a7_restart_allocation_uses_max_canonical_eid(self, tmp_path):
        durable = _graph(tmp_path / "allocation-durable")
        residue = _graph(tmp_path / "allocation-residue")
        durable_reopened = None
        residue_reopened = None
        try:
            assert _add(durable, "one", 0) == 1
            assert _add(durable, "two", 1) == 2
            durable.close()
            durable_reopened = _graph(tmp_path / "allocation-durable")
            assert _add(durable_reopened, "three", 2) == 3

            assert _add(residue, "one", 0) == 1
            assert _add(residue, "two", 1) == 2
            unflushed = residue.spawn_memory(
                summary="three unflushed",
                embedding=_embed(2),
                mtype="episode",
                strength=0.7,
                confidence=0.8,
                half_life_days=30.0,
                user_id="agent",
                step=3,
            )
            assert unflushed == 3
            residue.close()
            residue_reopened = _graph(tmp_path / "allocation-residue")
            assert _add(residue_reopened, "replacement three", 3) == 3
        finally:
            durable.close()
            residue.close()
            if durable_reopened is not None:
                durable_reopened.close()
            if residue_reopened is not None:
                residue_reopened.close()

    def test_a8_sqlite_sidecar_can_be_deleted_and_rebuilt_from_canonical_nodes(self, tmp_path):
        root = tmp_path / "sqlite-independent"
        fabric = TormentFabric(str(root))
        reopened = None
        try:
            fabric.create_agent("ws", "agent")
            key = fabric._agent_key("ws", "agent")
            graph = fabric.private_graphs[key]
            first = _add(graph, "sqlite canonical one", 0, step=51)
            second = _add(graph, "sqlite canonical two", 1, step=52)
            index = fabric._get_sqlite_index("ws", "agent")
            assert {row["eid"] for row in index.get_recent_memories()} == {first, second}
            assert {hit["eid"] for hit in fabric.query("ws", "agent", "sqlite canonical", top_k=10)["results"]} >= {first, second}

            db_path = Path(index.db_path)
            graph.close()
            fabric.close()
            for path in (db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")):
                if path.exists():
                    path.unlink()
            assert not db_path.exists()

            reopened = TormentFabric(str(root))
            reopened.create_agent("ws", "agent")
            reopened_key = reopened._agent_key("ws", "agent")
            reopened_graph = reopened.private_graphs[reopened_key]
            assert set(reopened_graph.entities) == {first, second}
            assert {hit["eid"] for hit in reopened.query("ws", "agent", "sqlite canonical", top_k=10)["results"]} >= {first, second}

            rebuilt_index = reopened._get_sqlite_index("ws", "agent")
            counts = rebuilt_index.rebuild_from_jsonl(
                nodes_path=reopened_graph.meta_path,
                events_path=reopened_graph.events_path,
            )
            assert counts["core_nodes"] == 2
            assert {row["eid"] for row in rebuilt_index.get_recent_memories()} == {first, second}
        finally:
            _close_fabric_graphs(fabric)
            if reopened is not None:
                _close_fabric_graphs(reopened)


class TestGateBSuspiciousSeams:
    def test_b1_shared_origin_writeback_uses_its_production_ingest_graph(self, tmp_path, monkeypatch):
        """A shared Fabric-ingest hit with a colliding EID evolves only in shared."""
        monkeypatch.setenv("TORMENT_SRG_ENABLE", "1")
        monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "0")
        monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
        fabric = TormentFabric(str(tmp_path / "srg-collision"))
        try:
            workspace = fabric.get_workspace("ws")
            fabric.create_agent("ws", "agent")
            private = fabric.private_graphs[fabric._agent_key("ws", "agent")]
            shared = workspace.shared_graphs["personal"]
            private_eid = _fabric_ingest(
                fabric, "private raw-eid collision", step=101
            )
            shared_eid = _fabric_ingest(
                fabric, "shared raw-eid collision", step=102,
                scope="shared", nested_srg=True,
            )
            assert private_eid == shared_eid == 1
            before_private = copy.deepcopy(private.entities[private_eid].payload)
            before_shared = copy.deepcopy(shared.entities[shared_eid].payload)

            response = fabric.query("ws", "agent", "raw-eid collision", top_k=10, domain_id="personal", explain=True)
            hit = next(
                item for item in response["results"]
                if item.get("scope") == "shared" and int(item["eid"]) == shared_eid
            )
            assert hit["domain_id"] == "personal"
            assert hit["payload"]["srg"] == _ACTIVE_SRG

            assert private.entities[private_eid].payload == before_private
            assert shared.entities[shared_eid].payload != before_shared
        finally:
            _close_fabric_graphs(fabric)

    def test_b1_private_origin_writeback_uses_its_production_ingest_graph(self, tmp_path, monkeypatch):
        """A private Fabric-ingest hit with a colliding EID evolves only in private."""
        monkeypatch.setenv("TORMENT_SRG_ENABLE", "1")
        monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "0")
        monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
        fabric = TormentFabric(str(tmp_path / "srg-private-collision"))
        try:
            workspace = fabric.get_workspace("ws")
            fabric.create_agent("ws", "agent")
            private = fabric.private_graphs[fabric._agent_key("ws", "agent")]
            shared = workspace.shared_graphs["personal"]
            private_eid = _fabric_ingest(
                fabric, "private origin collision", step=111, nested_srg=True
            )
            shared_eid = _fabric_ingest(
                fabric, "shared unrelated collision", step=112, scope="shared"
            )
            assert private_eid == shared_eid == 1
            before_private = copy.deepcopy(private.entities[private_eid].payload)
            before_shared = copy.deepcopy(shared.entities[shared_eid].payload)

            response = fabric.query("ws", "agent", "private origin collision", top_k=10, domain_id="personal", explain=True)
            hit = next(
                item for item in response["results"]
                if item.get("scope") == "private" and int(item["eid"]) == private_eid
            )
            assert hit["payload"]["srg"] == _ACTIVE_SRG
            assert private.entities[private_eid].payload != before_private
            assert shared.entities[shared_eid].payload == before_shared
        finally:
            _close_fabric_graphs(fabric)

    def test_b1_unresolved_and_deep_origins_fail_closed(self, tmp_path, monkeypatch):
        """No origin metadata means no raw-EID fallback, including deep scope."""
        monkeypatch.setenv("TORMENT_SRG_ENABLE", "1")
        monkeypatch.setenv("TORMENT_REINFORCE_SIM_THRESHOLD", "0")
        monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
        fabric = TormentFabric(str(tmp_path / "srg-unresolved"))
        try:
            workspace = fabric.get_workspace("ws")
            fabric.create_agent("ws", "agent")
            private = fabric.private_graphs[fabric._agent_key("ws", "agent")]
            shared = workspace.shared_graphs["personal"]
            private_eid = _fabric_ingest(fabric, "private unresolved collision", step=121)
            shared_eid = _fabric_ingest(
                fabric, "shared unresolved collision", step=122,
                scope="shared", nested_srg=True,
            )
            assert private_eid == shared_eid == 1
            before_private = copy.deepcopy(private.entities[private_eid].payload)
            before_shared = copy.deepcopy(shared.entities[shared_eid].payload)

            shared_hit = shared.search("shared unresolved collision", top_k=1)[0]
            unresolved_hit = dict(shared_hit)
            unresolved_hit["domain_id"] = "missing-domain"
            monkeypatch.setattr(fabric, "_query_private_lane", lambda *args, **kwargs: [])
            monkeypatch.setattr(fabric, "_query_shared_lane", lambda *args, **kwargs: ([unresolved_hit], []))
            monkeypatch.setattr(fabric, "_query_deep_lane", lambda *args, **kwargs: [])
            fabric.query("ws", "agent", "shared unresolved collision", top_k=10, domain_id="personal")
            assert private.entities[private_eid].payload == before_private
            assert shared.entities[shared_eid].payload == before_shared

            deep_hit = {
                "eid": private_eid,
                "score": 1.0,
                "summary": "synthetic deep origin",
                "strength": 0.5,
                "confidence": 0.5,
                "memory_class": "core",
                "scope": "deep",
                "workspace_id": "ws",
                "agent_id": "agent",
                "deep_memory": True,
                "payload": {"srg": dict(_ACTIVE_SRG)},
            }
            monkeypatch.setattr(fabric, "_query_shared_lane", lambda *args, **kwargs: ([], []))
            monkeypatch.setattr(fabric, "_query_deep_lane", lambda *args, **kwargs: [deep_hit])
            fabric.query("ws", "agent", "synthetic deep origin", top_k=10, domain_id="personal")
            assert private.entities[private_eid].payload == before_private
            assert shared.entities[shared_eid].payload == before_shared
        finally:
            _close_fabric_graphs(fabric)

    def test_b2_fabric_close_releases_all_shard_handles_before_workspace_cleanup(self, tmp_path):
        root = tmp_path / "fabric-close-probe"
        fabric = TormentFabric(str(root))
        try:
            workspace = fabric.get_workspace("ws")
            fabric.create_agent("ws", "agent")
            private = fabric.private_graphs[fabric._agent_key("ws", "agent")]
            shared = workspace.shared_graphs["personal"]
            _add(private, "private close probe", 0)
            _add(shared, "shared close probe", 1, user_id="collective", extra_payload={"scope": "shared", "domain_id": "personal"})
            private.search("private close probe", user_id="agent")
            shared.search("shared close probe")

            fabric.close()  # The supported Fabric-owned close path under test.
            fabric.close()  # Repeated close is safe and leaves resources closed.
            assert private._shard_writer._active_mmap is None
            assert shared._shard_writer._active_mmap is None
            assert private._shard_reader._shard_cache == {}
            assert shared._shard_reader._shard_cache == {}
            shutil.rmtree(root)
            assert not root.exists()
        finally:
            fabric.close()
            if root.exists():
                shutil.rmtree(root)

    def test_b3_admin_rebuild_includes_current_daily_and_legacy_trajectory_records(self, tmp_path):
        """Mirror app.index_rebuild's daily and legacy source paths exactly."""
        root = tmp_path / "trajectory-rebuild"
        fabric = TormentFabric(str(root))
        try:
            fabric.create_agent("ws", "agent")
            key = fabric._agent_key("ws", "agent")
            graph = fabric.private_graphs[key]
            eid = _add(graph, "trajectory rebuild core node", 0, step=71)
            graph.step_world(step=71, classify_every=0, log_every=1)
            private_dir = Path(graph.data_dir)
            daily_paths = list((private_dir / "logs" / "trajectories" / "daily").glob("*.jsonl"))
            assert daily_paths and any(int(row["eid"]) == eid for row in _rows(daily_paths[0]))
            second_daily = daily_paths[0].with_name("2026-08-12.jsonl")
            second_daily.write_text(
                json.dumps({"step": 72, "eid": eid, "pos": [2.0, 0.0, 0.0]}) + "\n",
                encoding="utf-8",
            )
            legacy_path = private_dir / "trajectories.jsonl"
            legacy_path.write_text(
                json.dumps({"step": 73, "eid": eid, "pos": [3.0, 0.0, 0.0]}) + "\n",
                encoding="utf-8",
            )

            index = fabric._get_sqlite_index("ws", "agent")
            # These are the current production/admin endpoint parameters.
            counts = index.rebuild_from_jsonl(
                nodes_path=str(private_dir / "nodes.jsonl"),
                events_path=str(private_dir / "memory_events.jsonl"),
                trajectories_path=str(private_dir / "logs" / "trajectories" / "daily"),
                legacy_trajectories_path=str(legacy_path),
            )
            assert counts["core_nodes"] == 1
            assert counts["core_events"] == 1
            assert counts["trajectory_index"] == 3
            assert [row["step"] for row in index.get_trajectory_range(71, 73)] == [71, 72, 73]
            assert any(int(hit["eid"]) == eid for hit in fabric.query("ws", "agent", "trajectory rebuild", top_k=10)["results"])

            missing_index = IndexManager(str(tmp_path / "missing-daily-index"))
            try:
                missing_counts = missing_index.rebuild_from_jsonl(
                    nodes_path=str(private_dir / "nodes.jsonl"),
                    events_path=str(private_dir / "memory_events.jsonl"),
                    trajectories_path=str(private_dir / "logs" / "trajectories" / "absent"),
                )
                assert missing_counts["core_nodes"] == counts["core_nodes"]
                assert missing_counts["core_events"] == counts["core_events"]
                assert missing_counts["trajectory_index"] == 0
            finally:
                missing_index.close()
        finally:
            _close_fabric_graphs(fabric)
