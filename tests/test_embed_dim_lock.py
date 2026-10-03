from fastapi.testclient import TestClient

from conftest import assert_legacy_mode, ensure_legacy_run_root

ensure_legacy_run_root()  # I11: existing legacy owner on the run root before the import-time binding

from torment_service.app import app


def setup_module():
    import torment_service.app as appmod
    assert_legacy_mode(appmod)


def test_workspace_embedding_dim_lock_rejects_mismatch() -> None:
    client = TestClient(app)

    ws = "ws_dimlock"
    agent = "a1"

    # Create workspace/agent
    r = client.post("/workspace/create", json={"workspace_id": ws})
    assert r.status_code == 200
    r = client.post("/agent/create", json={"workspace_id": ws, "agent_id": agent})
    assert r.status_code == 200

    # First ingest with correct dim (default hash dim is 384)
    ok_emb = [0.0] * 384
    r = client.post(
        "/agent/ingest",
        json={"workspace_id": ws, "agent_id": agent, "text": "hello", "step": 1, "supplied_embedding": ok_emb},
    )
    assert r.status_code == 200

    # Now ingest with wrong dim -> 409
    bad_emb = [0.0] * 385
    r = client.post(
        "/agent/ingest",
        json={"workspace_id": ws, "agent_id": agent, "text": "hello2", "step": 2, "supplied_embedding": bad_emb},
    )
    assert r.status_code == 409
