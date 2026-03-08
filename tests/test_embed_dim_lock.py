from fastapi.testclient import TestClient

from torment_service.app import app


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
