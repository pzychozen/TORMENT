"""Response-boundary regression coverage for trajectory index rebuilds."""

from __future__ import annotations

import importlib
import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from torment_service.kernel.trajectory_v2 import TrajectoryV2Writer


def test_index_rebuild_redacts_unsealed_v2_integrity_details():
    """Authenticated callers receive a stable, non-diagnostic integrity report."""
    temp_root = Path(tempfile.mkdtemp(prefix="torment_s1_1423_"))
    env_overrides = {
        "TORMENT_DATA_DIR": str(temp_root / "data"),
        "TORMENT_AUTH_ENABLE": "1",
        "TORMENT_API_KEYS": "sk-index-rebuild-low:index-rebuild-low:0.0",
        "TORMENT_EMBED_PROVIDER": "hash",
        "TORMENT_SQLITE_INDEX_ENABLE": "1",
        "TORMENT_TRAJECTORY_FORMAT": "v2",
    }
    original_env = {key: os.environ.get(key) for key in env_overrides}
    original_api_keys_file = os.environ.get("TORMENT_API_KEYS_FILE")

    appmod = None
    authmod = None
    client = None
    index = None
    try:
        os.environ.update(env_overrides)
        os.environ.pop("TORMENT_API_KEYS_FILE", None)

        import torment_service.app as appmod  # noqa: PLC0415
        import torment_service.auth as authmod  # noqa: PLC0415

        authmod = importlib.reload(authmod)
        appmod = importlib.reload(appmod)

        workspace_id = "ws_index_rebuild_redaction"
        agent_id = "ag_index_rebuild_redaction"
        agent_dir = (
            temp_root
            / "data"
            / "workspaces"
            / workspace_id
            / "agents"
            / agent_id
        )
        agent_dir.mkdir(parents=True)

        # Match the existing SQLite rebuild fixture: a writer with an unsealed
        # V2 partial chunk is a legitimate interrupted trajectory state.
        writer = TrajectoryV2Writer(str(agent_dir))
        entity = type("Entity", (), {
            "eid": 7,
            "pos": np.asarray((1.0, 2.0, 3.0), dtype=np.float64),
            "vel": np.asarray((0.1, 0.2, 0.3), dtype=np.float64),
            "vel0": np.asarray((0.1, 0.2, 0.3), dtype=np.float64),
            "born_step": 0,
            "channel": 0,
            "alive": True,
            "payload": {},
        })()
        assert writer.write_step([entity], 1).ok
        writer._chunk_handle.close()
        writer._chunk_handle = None
        partial_chunk = next(agent_dir.rglob("*.partial"))

        index = appmod.fabric._get_sqlite_index(workspace_id, agent_id)
        assert index is not None and index.available
        assert index.index_node(777, {"type": "sidecar_sentinel", "summary": "sidecar baseline"})
        sentinel_before = index.get_recent_memories(limit=10)

        client = TestClient(appmod.app)
        response = client.post(
            "/index/rebuild",
            headers={"X-API-Key": "sk-index-rebuild-low"},
            json={"workspace_id": workspace_id, "agent_id": agent_id},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is False
        assert payload["detail"] == "Trajectory history was not indexed because integrity verification failed"
        assert isinstance(payload["integrity_report"], str)
        assert payload["integrity_report"] == "Trajectory integrity verification failed"

        serialized_response = json.dumps(payload, sort_keys=True)
        assert str(temp_root) not in serialized_response
        assert str(partial_chunk) not in serialized_response
        assert partial_chunk.name not in serialized_response
        assert ".partial" not in serialized_response
        assert "INCOMPLETE_FINAL_CHUNK" not in serialized_response
        assert index.get_recent_memories(limit=10) == sentinel_before
    finally:
        if client is not None:
            client.close()
        if index is not None:
            index.close()

        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if original_api_keys_file is None:
            os.environ.pop("TORMENT_API_KEYS_FILE", None)
        else:
            os.environ["TORMENT_API_KEYS_FILE"] = original_api_keys_file

        if authmod is not None:
            importlib.reload(authmod)
        if appmod is not None:
            importlib.reload(appmod)
        shutil.rmtree(temp_root)
