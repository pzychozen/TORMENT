import importlib

import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create an isolated app instance pointing at a temp data dir."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TORMENT_DATA_DIR", str(data_dir))

    import torment_service.app as appmod

    # Reload to ensure DATA_DIR and fabric are initialized from env var.
    appmod = importlib.reload(appmod)
    return TestClient(appmod.app)


def _unit_vec(dim=384, seed=0):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(dim,)).astype(np.float32)
    v /= (np.linalg.norm(v) + 1e-12)
    return v.tolist()


def test_end_to_end_private_memory(client: TestClient):
    # Workspace + agent
    r = client.post("/workspace/create", json={"workspace_id": "ws"})
    assert r.status_code == 200

    r = client.post(
        "/agent/create",
        json={
            "workspace_id": "ws",
            "agent_id": "a1",
            "seed": {"coupling_mode": "read_only", "coupling_strength": 0.2},
        },
    )
    assert r.status_code == 200

    emb = _unit_vec(seed=1)
    r = client.post(
        "/agent/ingest",
        json={
            "workspace_id": "ws",
            "agent_id": "a1",
            "text": "We decided: summaries + embeddings only.",
            "step": 1,
            "supplied_summary": "Store summaries + embeddings (no raw text).",
            "supplied_embedding": emb,
            "scope": "private",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("stored") in (True, False)

    # Query should return a structured response
    r = client.post(
        "/agent/query",
        json={
            "workspace_id": "ws",
            "agent_id": "a1",
            "query": "What did we decide about storage?",
            "top_k": 5,
            "explain": True,
        },
    )
    assert r.status_code == 200
    q = r.json()
    assert "results" in q
    assert "motifs" in q
    assert "bridges" in q

    # If we have results, explainability fields should exist.
    if q["results"]:
        hit = q["results"][0]
        assert "score" in hit
        assert "explain" in hit


def test_shared_governance_proposals_and_trace_view(client: TestClient):
    client.post("/workspace/create", json={"workspace_id": "ws"})

    # Two agents to satisfy min_distinct_agents governance
    client.post("/agent/create", json={"workspace_id": "ws", "agent_id": "a1"})
    client.post("/agent/create", json={"workspace_id": "ws", "agent_id": "a2"})

    # Same embedding to force grouping
    emb = _unit_vec(seed=42)
    p1 = client.post(
        "/agent/propose_share",
        json={
            "workspace_id": "ws",
            "agent_id": "a1",
            "summary": "Shared canon: private-write, shared-read with proposals.",
            "domain_id": "meta",
            "mtype": "fact",
            "confidence": 0.9,
            "strength": 0.9,
            "supplied_embedding": emb,
        },
    )
    assert p1.status_code == 200

    p2 = client.post(
        "/agent/propose_share",
        json={
            "workspace_id": "ws",
            "agent_id": "a2",
            "summary": "Shared canon: private-write, shared-read with proposals.",
            "domain_id": "meta",
            "mtype": "fact",
            "confidence": 0.85,
            "strength": 0.88,
            "supplied_embedding": emb,
        },
    )
    assert p2.status_code == 200

    pr = client.post(
        "/workspace/process_proposals",
        json={
            "workspace_id": "ws",
            "domain_id": "meta",
            "max_to_process": 50,
            "sim_threshold": 0.95,
            "min_distinct_agents": 2,
        },
    )
    assert pr.status_code == 200
    out = pr.json()
    assert out.get("approved_groups", 0) >= 1
    created = out.get("created_shared_eids") or out.get("created_shared_eid")
    assert created is not None
    shared_eid = created[0] if isinstance(created, list) else created

    # Trace view should render narrative without requiring bundle export
    tv = client.post(
        "/memory/trace_view",
        json={
            "workspace_id": "ws",
            "eid": int(shared_eid),
            "scope": "shared",
            "domain_id": "meta",
            "depth": 1,
        },
    )
    assert tv.status_code == 200
    t = tv.json()
    assert "narrative" in t
    assert "graph_summary" in t
