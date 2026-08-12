"""tests/test_archive_ingest_governance_endpoint.py — v0.2.4 item #2.

HTTP-layer coverage for the `/archive/ingest_document` governance pass-through.
v0.2.4-A1 added per-chunk archive governance + FILTER-A exclusion at /retrieve,
but the HTTP request model could not carry governance (tests bypassed HTTP via
ArchiveStore.ingest_document directly). This slice closes that gap: the request
model now accepts an optional `governance` dict and passes it straight through.

These tests prove, through the REAL HTTP endpoint:
  1. ingest WITHOUT governance still works and default-passes (backward compat);
  2. ingest WITH governance={"non_shareable": True} stores the chunk governance;
  3. a non-shareable archive doc ingested via HTTP is excluded from the
     retrieved/assembled prompt-visible output by the existing FILTER-A path
     (and is proven to have been a retrieval candidate, so the test is not
     vacuous);
  4. the response shape stays compatible for callers that omit governance.

Harness mirrors tests/test_assembly_audit_wiring.py (isolated app + TestClient).
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture()
def client(tmp_path):
    """Isolated app instance bound to a temp data dir.

    Manual env save/restore + reload-in-finally, mirroring
    test_assembly_audit_wiring.py exactly (TORMENT_DATA_DIR only) so archive
    retrieval/exclusion behaves identically to that proven harness —
    torment_service.app reads TORMENT_DATA_DIR at module-import time.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    original_env = os.environ.get("TORMENT_DATA_DIR")
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)

    import torment_service.app as appmod
    appmod = importlib.reload(appmod)
    try:
        yield TestClient(appmod.app)
    finally:
        if original_env is None:
            os.environ.pop("TORMENT_DATA_DIR", None)
        else:
            os.environ["TORMENT_DATA_DIR"] = original_env
        importlib.reload(appmod)


def _unit_vec(dim=384, seed=0):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(dim,)).astype(np.float32)
    v /= (np.linalg.norm(v) + 1e-12)
    return v.tolist()


def _bootstrap(client, *, workspace="ws_gov", agent="ag_gov"):
    r = client.post("/workspace/create", json={"workspace_id": workspace})
    assert r.status_code == 200, r.text
    r = client.post(
        "/agent/create",
        json={"workspace_id": workspace, "agent_id": agent,
              "seed": {"coupling_mode": "read_only", "coupling_strength": 0.2}},
    )
    assert r.status_code == 200, r.text
    for i, text in enumerate([
        "We chose summaries plus embeddings for storage.",
        "Character voice should preserve material meaning.",
        "Tool results are advisory and decay-bounded.",
    ]):
        r = client.post(
            "/agent/ingest",
            json={"workspace_id": workspace, "agent_id": agent, "text": text,
                  "step": i + 1, "supplied_summary": text,
                  "supplied_embedding": _unit_vec(seed=i + 1), "scope": "private"},
        )
        assert r.status_code == 200, r.text
    return workspace, agent


def _ingest_archive_http(client, ws, ag, *, text, title, governance=None):
    payload = {"workspace_id": ws, "agent_id": ag, "text": text, "title": title}
    if governance is not None:
        payload["governance"] = governance
    r = client.post("/archive/ingest_document", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _archive_query(client, ws, ag, query, *, top_k=5):
    r = client.post(
        "/archive/query",
        json={"workspace_id": ws, "agent_id": ag, "query": query, "top_k": top_k},
    )
    assert r.status_code == 200, r.text
    return r.json()["results"]


def _retrieve_payload(ws, ag, *, include_audit=False):
    return {
        "workspace_id": ws, "agent_id": ag,
        "query": "What did we decide about storage?",
        "profile": "companion", "token_budget": 1500, "top_k": 5,
        "include_assembly_audit": include_audit,
    }


# ---------------------------------------------------------------------------
# 1. Backward compatibility — request without governance still works.
# ---------------------------------------------------------------------------

def test_ingest_without_governance_still_works(client):
    ws, ag = _bootstrap(client)
    res = _ingest_archive_http(
        client, ws, ag,
        text="Public notes about storage decisions and tradeoffs.",
        title="public_doc",
    )
    assert "doc_id" in res
    assert res["chunk_count"] >= 1
    # default-pass: chunks ingested without governance surface governance == {}
    hits = _archive_query(client, ws, ag, "storage decisions")
    assert hits, "expected at least one archive hit"
    assert all(h.get("governance", {}) == {} for h in hits)


# ---------------------------------------------------------------------------
# 2. Governance passes through and is stored on the chunk.
# ---------------------------------------------------------------------------

def test_ingest_with_governance_stores_chunk_governance(client):
    ws, ag = _bootstrap(client)
    _ingest_archive_http(
        client, ws, ag,
        text="Private storage policy memo. Restricted distribution.",
        title="private_doc",
        governance={"non_shareable": True},
    )
    hits = _archive_query(client, ws, ag, "storage policy")
    assert hits, "expected at least one archive hit"
    assert any(h.get("governance", {}).get("non_shareable") is True for h in hits), (
        "governance did not pass through the HTTP endpoint to the stored chunk"
    )


# ---------------------------------------------------------------------------
# 3. End-to-end: non-shareable archive ingested via HTTP is excluded from the
#    retrieved/assembled prompt-visible output (and was actually a candidate).
# ---------------------------------------------------------------------------

def test_non_shareable_http_ingest_excluded_from_retrieve(client, monkeypatch):
    # This is the one test in this module that deliberately exercises
    # automatic Archive inclusion in /retrieve. It must opt in now that
    # Archive recall is default-off.
    import torment_service.thinking_controller as tc
    monkeypatch.setenv("TORMENT_ARCHIVE_RECALL", "1")
    monkeypatch.setattr(tc, "_ARCHIVE_RECALL_ENABLE", True)
    ws, ag = _bootstrap(client)
    secret = "TOKEN_HTTP_PRIVATE_MARKER_77_NOT_SHAREABLE"
    res = _ingest_archive_http(
        client, ws, ag,
        text=(
            f"Private memo about storage policy decisions. {secret}. "
            "Internal only — restricted distribution."
        ),
        title="private_http_doc",
        governance={"non_shareable": True},
    )
    doc_id = res["doc_id"]

    # Non-vacuity: prove the chunk WAS retrieved AND excluded by FILTER-A.
    audit_body = client.post(
        "/retrieve", json=_retrieve_payload(ws, ag, include_audit=True)
    ).json()
    archive_excluded = (
        audit_body.get("assembly_audit", {}).get("filter_a", {}).get("archive_excluded", [])
    )
    assert any(
        e.get("doc_id") == doc_id and e.get("excluded_reason") == "non_shareable"
        for e in archive_excluded
    ), "non-shareable HTTP-ingested chunk was not retrieved+excluded (test would be vacuous)"

    # Privacy invariant: the chunk's text marker and doc_id must not reach
    # prompt-visible output (independent of the audit flag).
    body = client.post("/retrieve", json=_retrieve_payload(ws, ag)).json()
    assert secret not in body.get("assembled_text", ""), (
        "non-shareable archive marker leaked into assembled_text via HTTP ingest"
    )
    for block in body.get("blocks", {}).get("archive_context", []):
        meta = block.get("metadata", {}) or {}
        assert meta.get("doc_id") != doc_id, (
            f"non-shareable HTTP-ingested chunk leaked into BLOCK_ARCHIVE: {meta!r}"
        )


# ---------------------------------------------------------------------------
# 4. Response shape stays compatible for callers that omit governance.
# ---------------------------------------------------------------------------

def test_response_shape_compatible_without_governance(client):
    ws, ag = _bootstrap(client)
    res = _ingest_archive_http(
        client, ws, ag,
        text="Some ordinary storage notes for shape check.",
        title="shape_doc",
    )
    assert set(res.keys()) == {"doc_id", "chunk_count", "token_count"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
