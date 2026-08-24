"""Fabric ownership tests for cached DeepMemoryStore lifecycle resources."""

import logging
import shutil
from pathlib import Path

import numpy as np

from torment_service.compression import CompressionCandidate, _get_or_create_deep_store
from torment_service.fabric import TormentFabric


def _configure_env(monkeypatch) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")


def _populate_owned_store(fabric: TormentFabric, *, agent_id: str, eid: int):
    store = _get_or_create_deep_store(fabric, agent_id, workspace_id="ws")
    vector = np.zeros(store.dim, dtype=np.float32)
    vector[0] = 1.0
    candidate = CompressionCandidate(
        eid=eid,
        born_step=1,
        summary=f"fabric deep-store lifecycle {eid}",
        score=0.9,
        memory_class="core",
        tier="relational",
        route="long_path",
    )
    store.export(
        candidate,
        vector,
        {"workspace_id": "ws", "agent_id": agent_id, "domain_id": "personal"},
        step=600,
    )
    assert store.query(vector, top_k=1)
    assert store._shard_writer is not None
    assert store._shard_writer._active_mmap is not None
    assert store._shard_reader is not None
    assert store._shard_reader._shard_cache
    return store


def _assert_store_released(store) -> None:
    assert store._shard_writer is not None
    assert store._shard_writer._active_mmap is None
    assert store._shard_reader is not None
    assert store._shard_reader._shard_cache == {}
    assert store._shard_reader._map_cache == {}


def test_fabric_close_releases_owned_deep_stores_and_backing_directory(tmp_path, monkeypatch):
    _configure_env(monkeypatch)
    root = tmp_path / "deep-store-fabric-close"
    fabric = TormentFabric(str(root))
    store = None
    try:
        store = _populate_owned_store(fabric, agent_id="agent", eid=1)

        fabric.close()

        assert fabric._deep_stores == {}
        _assert_store_released(store)

        fabric.close()
        assert fabric._deep_stores == {}

        shutil.rmtree(root)
        assert not root.exists()
    finally:
        if store is not None:
            store.close()
        fabric.close()
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)


def test_memory_fabric_close_removes_used_deep_store_backing_directory(monkeypatch):
    _configure_env(monkeypatch)
    fabric = TormentFabric(data_dir=":memory:")
    root = Path(fabric.data_dir)
    store = None
    try:
        store = _populate_owned_store(fabric, agent_id="agent", eid=2)
        assert root.exists()

        fabric.close()

        assert fabric._deep_stores == {}
        _assert_store_released(store)
        assert not root.exists()
    finally:
        if store is not None:
            store.close()
        fabric.close()
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)


def test_fabric_close_continues_after_owned_deep_store_failure(monkeypatch, tmp_path, caplog):
    _configure_env(monkeypatch)
    root = tmp_path / "deep-store-close-failure"
    fabric = TormentFabric(str(root))
    first = None
    second = None
    try:
        first = _populate_owned_store(fabric, agent_id="first", eid=3)
        second = _populate_owned_store(fabric, agent_id="second", eid=4)

        def fail_close():
            raise RuntimeError("controlled deep-store close failure")

        with monkeypatch.context() as close_patch:
            close_patch.setattr(first, "close", fail_close)
            with caplog.at_level(logging.DEBUG, logger="torment.clone"):
                fabric.close()

        assert fabric._deep_stores == {}
        _assert_store_released(second)
        assert any(
            record.name == "torment.clone"
            and "DeepMemoryStore close failed during fabric close" in record.getMessage()
            and "controlled deep-store close failure" in record.getMessage()
            for record in caplog.records
        )
    finally:
        if first is not None:
            first.close()
        if second is not None:
            second.close()
        fabric.close()
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)
