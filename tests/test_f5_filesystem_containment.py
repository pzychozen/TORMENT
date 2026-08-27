"""F5 regression coverage for physical filesystem containment on Windows."""
from __future__ import annotations

import importlib
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from torment_service.kernel.trajectory_v2 import (
    CHUNK_HEADER,
    FORMAT_VERSION,
    MAGIC,
    TrajectoryIntegrityError,
    TrajectoryV2Verifier,
    TrajectoryV2Writer,
)
from torment_service.proposals import ProposalRegistry


def _make_directory_junction(link: Path, target: Path) -> None:
    if os.name != "nt":
        pytest.skip("directory junctions are a Windows-specific regression surface")
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip("directory junction creation is unavailable on this host")


@pytest.fixture()
def authenticated_client(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    env_keys = (
        "TORMENT_DATA_DIR",
        "TORMENT_AUTH_ENABLE",
        "TORMENT_API_KEYS",
        "TORMENT_API_KEYS_FILE",
        "TORMENT_EMBED_PROVIDER",
        "TORMENT_HIVEMIND_ENABLE",
        "TORMENT_SQLITE_INDEX_ENABLE",
    )
    original_env = {key: os.environ.get(key) for key in env_keys}
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)
    os.environ["TORMENT_AUTH_ENABLE"] = "1"
    os.environ["TORMENT_API_KEYS"] = "f5-admin:admin:1.0,f5-archive:archive:0.6"
    os.environ.pop("TORMENT_API_KEYS_FILE", None)
    os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
    os.environ["TORMENT_HIVEMIND_ENABLE"] = "0"
    os.environ["TORMENT_SQLITE_INDEX_ENABLE"] = "0"

    import torment_service.auth as authmod
    import torment_service.app as appmod

    authmod = importlib.reload(authmod)
    appmod = importlib.reload(appmod)
    client = TestClient(appmod.app)
    try:
        yield client, appmod, data_dir
    finally:
        client.close()
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        importlib.reload(authmod)
        importlib.reload(appmod)


def _headers(key: str) -> dict[str, str]:
    return {"X-API-Key": key}


def _bootstrap_archive_agent(client: TestClient, *, workspace: str, agent: str) -> None:
    response = client.post(
        "/workspace/create",
        json={"workspace_id": workspace},
        headers=_headers("f5-admin"),
    )
    assert response.status_code == 200, response.text
    response = client.post(
        "/agent/create",
        json={"workspace_id": workspace, "agent_id": agent},
        headers=_headers("f5-admin"),
    )
    assert response.status_code == 200, response.text


def test_authenticated_archive_ingest_rejects_junction_before_any_outside_write(
    authenticated_client,
    tmp_path,
):
    client, _appmod, data_dir = authenticated_client
    workspace, agent = "ws_f5_archive", "ag_f5_archive"
    _bootstrap_archive_agent(client, workspace=workspace, agent=agent)
    outside = tmp_path / "outside"
    outside.mkdir()
    archive_dir = data_dir / "workspaces" / workspace / "agents" / agent / "memory_archive"
    _make_directory_junction(archive_dir, outside)

    response = client.post(
        "/archive/ingest_document",
        json={"workspace_id": workspace, "agent_id": agent, "text": "must not escape", "title": "f5"},
        headers=_headers("f5-archive"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Archive path escapes data directory"
    assert not (outside / "documents.jsonl").exists()
    assert not (outside / "chunks.jsonl").exists()
    assert not (outside / "embeddings").exists()


def test_authenticated_archive_ingest_keeps_contained_archive_behavior(authenticated_client):
    client, _appmod, data_dir = authenticated_client
    workspace, agent = "ws_f5_archive_ok", "ag_f5_archive_ok"
    _bootstrap_archive_agent(client, workspace=workspace, agent=agent)

    response = client.post(
        "/archive/ingest_document",
        json={"workspace_id": workspace, "agent_id": agent, "text": "ordinary contained archive", "title": "f5"},
        headers=_headers("f5-archive"),
    )

    assert response.status_code == 200, response.text
    archive_dir = data_dir / "workspaces" / workspace / "agents" / agent / "memory_archive"
    assert (archive_dir / "documents.jsonl").is_file()
    assert (archive_dir / "chunks.jsonl").is_file()
    assert (archive_dir / "embeddings").is_dir()


def test_proposal_registry_revalidates_cached_paths_after_domain_junction_replacement(tmp_path):
    data_dir = tmp_path / "data"
    registry = ProposalRegistry(str(data_dir), "ws_f5_proposals", "domain_f5")
    ordinary = registry.submit(
        "agent_f5",
        "contained proposal",
        np.ones(4, dtype=np.float32),
        "fact",
        0.8,
        0.7,
    )
    assert ordinary.proposal_id
    assert len(registry.list_pending()) == 1

    domain_dir = data_dir / "workspaces" / "ws_f5_proposals" / "domains" / "domain_f5"
    parked_dir = domain_dir.with_name("domain_f5_parked")
    domain_dir.rename(parked_dir)
    outside = tmp_path / "outside"
    outside.mkdir()
    _make_directory_junction(domain_dir, outside)

    with pytest.raises(ValueError):
        registry.submit(
            "agent_f5",
            "redirected proposal",
            np.ones(4, dtype=np.float32),
            "fact",
            0.8,
            0.7,
        )
    with pytest.raises(ValueError):
        registry.mark(ordinary.proposal_id, "approved")
    assert not (outside / "proposals.jsonl").exists()
    assert not (outside / "proposal_events.jsonl").exists()


def _write_chunk_header(path: Path, *, seq: int, epoch: int) -> bytes:
    raw = CHUNK_HEADER.pack(MAGIC, FORMAT_VERSION, 0, seq, epoch)
    path.write_bytes(raw)
    return raw


def test_trajectory_discovery_rejects_junctioned_outside_chunk(tmp_path):
    root = tmp_path / "trajectory_root"
    chunks = root / "trajectories" / "v2" / "chunks"
    chunks.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_chunk = outside / "chunk-00000000000000004242.trj2"
    original_bytes = _write_chunk_header(outside_chunk, seq=4242, epoch=9)
    _make_directory_junction(chunks / "alias", outside)

    with pytest.raises(TrajectoryIntegrityError, match="discovered chunk path escapes"):
        TrajectoryV2Writer(str(root))

    report = TrajectoryV2Verifier(str(root)).verify()
    assert not report.valid
    assert any(issue["code"] == "DISCOVERED_CHUNK_PATH_INVALID" for issue in report.issues)
    assert outside_chunk.read_bytes() == original_bytes


def test_trajectory_discovery_retains_contained_recursive_chunk_behavior(tmp_path):
    root = tmp_path / "trajectory_root"
    nested = root / "trajectories" / "v2" / "chunks" / "nested"
    nested.mkdir(parents=True)
    contained_chunk = nested / "chunk-00000000000000000042.trj2"
    original_bytes = _write_chunk_header(contained_chunk, seq=42, epoch=9)

    writer = TrajectoryV2Writer(str(root))

    assert writer._next_seq == 43
    assert writer.epoch == 10
    assert contained_chunk.read_bytes() == original_bytes
