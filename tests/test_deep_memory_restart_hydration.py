from __future__ import annotations

from pathlib import Path

import numpy as np

from torment_service.compression import (
    CompressionCandidate,
    CompressionExecutor,
    _get_or_create_deep_store,
)
from torment_service.fabric import TormentFabric


WORKSPACE_ID = "restart_ws"
AGENT_ID = "restart_agent"
DOMAIN_ID = "personal"
SOURCE_TEXT = "Restart hydration marker cobalt notebook thunderstorm memory."


def _configure_env(monkeypatch, *, compress_enabled: bool) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "1" if compress_enabled else "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")


def _close_fabric_io(fabric: TormentFabric) -> None:
    # TormentFabric.close() owns private/shared graph shutdown.
    for store in list(getattr(fabric, "_deep_stores", {}).values()):
        try:
            store.close()
        except Exception:
            pass
    fabric.close()


def _deep_dir(data_dir: Path, workspace_id: str = WORKSPACE_ID, agent_id: str = AGENT_ID) -> Path:
    return data_dir / "workspaces" / workspace_id / "agents" / agent_id / "deep_memory"


def _deep_hits(result: dict) -> list[dict]:
    return [
        hit for hit in result.get("results", [])
        if hit.get("from_spirit_return") is True
    ]


def _create_source_and_export_deep(
    fabric: TormentFabric,
    *,
    workspace_id: str = WORKSPACE_ID,
    agent_id: str = AGENT_ID,
    text: str = SOURCE_TEXT,
) -> int:
    fabric.get_workspace(workspace_id, domains=[DOMAIN_ID])
    fabric.create_agent(workspace_id, agent_id)
    ak = fabric._agent_key(workspace_id, agent_id)
    graph = fabric.private_graphs[ak]

    embedding = np.asarray(fabric.kernel.embedder.embed(text), dtype=np.float32)
    eid = graph.add_memory(
        summary=text,
        embedding=embedding,
        mtype="episode",
        strength=0.25,
        confidence=0.9,
        half_life_days=30.0,
        canon=False,
        user_id=agent_id,
        step=1,
        memory_class="core",
        extra_payload={
            "workspace_id": workspace_id,
            "domain_id": DOMAIN_ID,
            "scope": "private",
            "agent_id": agent_id,
            "state_symbol": "circle",
            "symbol_trace": ["circle"],
            "in_corridor": False,
            "survival_steps": 0.0,
            "tearing_risk": 0.0,
        },
    )

    candidate = CompressionCandidate(
        eid=int(eid),
        born_step=1,
        summary=text,
        score=0.9,
        memory_class="core",
        tier="relational",
        route="long_path",
    )
    deep_store = _get_or_create_deep_store(
        fabric, agent_id, workspace_id=workspace_id
    )
    event = CompressionExecutor(graph, deep_store).execute(
        [candidate], step=600, trigger="test"
    )
    assert event.exported_deep == 1
    assert (_deep_dir(Path(fabric.data_dir), workspace_id, agent_id) / "memories.jsonl").exists()
    return int(eid)


def test_restart_hydrates_persisted_deep_store_without_manual_cache_assignment(
    tmp_path, monkeypatch,
):
    _configure_env(monkeypatch, compress_enabled=True)
    first = TormentFabric(data_dir=str(tmp_path))
    eid = _create_source_and_export_deep(first)
    _close_fabric_io(first)

    fresh = TormentFabric(data_dir=str(tmp_path))
    try:
        ak = fresh._agent_key(WORKSPACE_ID, AGENT_ID)
        assert fresh._deep_stores == {}

        result = fresh.query(
            WORKSPACE_ID,
            AGENT_ID,
            SOURCE_TEXT,
            top_k=5,
            domain_id=DOMAIN_ID,
        )

        hits = _deep_hits(result)
        assert any(int(hit.get("eid", -1)) == eid for hit in hits)
        assert ak in fresh._deep_stores
    finally:
        _close_fabric_io(fresh)


def test_absent_deep_store_query_does_not_create_deep_memory_directory(
    tmp_path, monkeypatch,
):
    _configure_env(monkeypatch, compress_enabled=True)
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        deep_dir = _deep_dir(tmp_path)
        assert not deep_dir.exists()
        assert not (deep_dir / "embeddings").exists()
        assert not (deep_dir / "memories.jsonl").exists()

        result = fabric.query(
            WORKSPACE_ID,
            AGENT_ID,
            "nothing deep exists yet",
            top_k=5,
            domain_id=DOMAIN_ID,
        )

        assert _deep_hits(result) == []
        assert fabric._deep_stores == {}
        assert not deep_dir.exists()
        assert not (deep_dir / "embeddings").exists()
        assert not (deep_dir / "memories.jsonl").exists()
    finally:
        _close_fabric_io(fabric)


def test_no_restart_deep_retrieval_parity(tmp_path, monkeypatch):
    _configure_env(monkeypatch, compress_enabled=True)
    fabric = TormentFabric(data_dir=str(tmp_path))
    try:
        eid = _create_source_and_export_deep(fabric)
        result = fabric.query(
            WORKSPACE_ID,
            AGENT_ID,
            SOURCE_TEXT,
            top_k=5,
            domain_id=DOMAIN_ID,
        )
        assert any(int(hit.get("eid", -1)) == eid for hit in _deep_hits(result))
    finally:
        _close_fabric_io(fabric)


def test_persisted_deep_store_is_workspace_and_agent_isolated(tmp_path, monkeypatch):
    _configure_env(monkeypatch, compress_enabled=True)
    first = TormentFabric(data_dir=str(tmp_path))
    _create_source_and_export_deep(first)
    _close_fabric_io(first)

    fresh = TormentFabric(data_dir=str(tmp_path))
    try:
        own = fresh.query(
            WORKSPACE_ID,
            AGENT_ID,
            SOURCE_TEXT,
            top_k=5,
            domain_id=DOMAIN_ID,
        )
        other_workspace = fresh.query(
            "other_ws",
            AGENT_ID,
            SOURCE_TEXT,
            top_k=5,
            domain_id=DOMAIN_ID,
        )
        other_agent = fresh.query(
            WORKSPACE_ID,
            "other_agent",
            SOURCE_TEXT,
            top_k=5,
            domain_id=DOMAIN_ID,
        )

        assert _deep_hits(own)
        assert _deep_hits(other_workspace) == []
        assert _deep_hits(other_agent) == []
        assert not _deep_dir(tmp_path, "other_ws", AGENT_ID).exists()
        assert not _deep_dir(tmp_path, WORKSPACE_ID, "other_agent").exists()
    finally:
        _close_fabric_io(fresh)


def test_feature_off_does_not_hydrate_persisted_deep_memory(
    tmp_path, monkeypatch,
):
    _configure_env(monkeypatch, compress_enabled=True)
    first = TormentFabric(data_dir=str(tmp_path))
    _create_source_and_export_deep(first)
    _close_fabric_io(first)

    _configure_env(monkeypatch, compress_enabled=False)
    fresh = TormentFabric(data_dir=str(tmp_path))
    try:
        result = fresh.query(
            WORKSPACE_ID,
            AGENT_ID,
            SOURCE_TEXT,
            top_k=5,
            domain_id=DOMAIN_ID,
        )
        assert _deep_hits(result) == []
        assert fresh._deep_stores == {}
    finally:
        _close_fabric_io(fresh)
