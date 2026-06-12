"""
tests/test_assembly_audit_wiring.py — S5 opt-in wiring integration tests.

Exercises the `build_assembly_audit` helper through the live
`POST /retrieve` endpoint and the additive `fabric.query()` return
shape, per Memory-to-Prompt v0.2 §4.3 and v0.2 §7.3 (Slice S5).

Uses FastAPI TestClient against an isolated app instance pointing at
a temp data dir (matches `tests/test_smoke_api.py` pattern). No
service start required. No LLM. No API keys. No disk persistence
beyond the temp workspace.

Test classes:
    - TestWiring_RequestModel: `AssembleContextReq.include_assembly_audit`
      field accepted, defaults False.
    - TestWiring_AuditOffByDefault: `/retrieve` without the flag returns
      no `assembly_audit` key; default-off path is byte-identical to
      pre-S5 shape on the common keys.
    - TestWiring_AuditOnReturnsAudit: `/retrieve` with the flag returns
      the `assembly_audit` key matching v0.2 §4.2 top-level shape.
    - TestWiring_ResultsByteIdentityABTest: same query with vs without
      audit; common-key contents byte-identical.
    - TestWiring_FabricQueryReturnShape: `fabric.query()` return dict
      now includes `filter_excluded`, `_core_hits_in_count`,
      `_authority_guard_rejected`.
    - TestWiring_MemoryBridgeKwarg: `MemoryBridge.retrieve(include_assembly_audit=
      True)` sends the flag in the POST payload.
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Dict
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixtures (mirror test_smoke_api.py pattern)
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path):
    """Create an isolated app instance pointing at a temp data dir.

    Manual env save/restore + post-yield reload — not monkeypatch.
    torment_service.app reads TORMENT_DATA_DIR at module-import time and
    binds both DATA_DIR and the module-level fabric to it. Reloading the
    module with TORMENT_DATA_DIR=tmp rebinds both to the tmp dir.
    monkeypatch.setenv would restore the env var at fixture teardown, but
    its restoration runs AFTER this fixture's post-yield code — so any
    reload-in-finally would re-bind to the still-tmp env. Saving the env
    manually and reloading inside finally AFTER the manual restore is the
    only shape that reverts appmod.DATA_DIR + appmod.fabric to their
    pre-fixture values. Without that revert, alphabetically-later tests
    that depend on the repo DATA_DIR (e.g. test_app_security_hardening.py)
    see a leaked tmp path.
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


def _bootstrap(client: TestClient, *, workspace="ws_s5", agent="ag_s5"):
    """Create a workspace + agent and ingest a small batch of memories
    so /retrieve has something to assemble. Returns (workspace, agent).
    """
    r = client.post("/workspace/create", json={"workspace_id": workspace})
    assert r.status_code == 200, r.text

    r = client.post(
        "/agent/create",
        json={
            "workspace_id": workspace,
            "agent_id": agent,
            "seed": {
                "coupling_mode": "read_only",
                "coupling_strength": 0.2,
            },
        },
    )
    assert r.status_code == 200, r.text

    # Ingest a few memories with stable embeddings so retrieval is
    # deterministic across the A/B test.
    for i, text in enumerate([
        "We chose summaries plus embeddings for storage.",
        "Character voice should preserve material meaning.",
        "Tool results are advisory and decay-bounded.",
    ]):
        r = client.post(
            "/agent/ingest",
            json={
                "workspace_id": workspace,
                "agent_id": agent,
                "text": text,
                "step": i + 1,
                "supplied_summary": text,
                "supplied_embedding": _unit_vec(seed=i + 1),
                "scope": "private",
            },
        )
        assert r.status_code == 200, r.text

    return workspace, agent


def _retrieve_payload(workspace: str, agent: str, *, include_audit: bool = False) -> Dict[str, Any]:
    return {
        "workspace_id": workspace,
        "agent_id": agent,
        "query": "What did we decide about storage?",
        "profile": "companion",
        "token_budget": 1500,
        "top_k": 5,
        "include_assembly_audit": include_audit,
    }


# ---------------------------------------------------------------------------
# 1. RequestModel — pydantic field accepted, defaults false
# ---------------------------------------------------------------------------

class TestWiring_RequestModel:
    def test_field_defaults_false(self):
        """AssembleContextReq.include_assembly_audit defaults to False."""
        # Re-import to ensure model reflects the S5-added field.
        import torment_service.app as appmod
        importlib.reload(appmod)
        req = appmod.AssembleContextReq(
            workspace_id="ws", agent_id="ag", query="q",
        )
        assert req.include_assembly_audit is False

    def test_field_accepts_true(self):
        import torment_service.app as appmod
        importlib.reload(appmod)
        req = appmod.AssembleContextReq(
            workspace_id="ws", agent_id="ag", query="q",
            include_assembly_audit=True,
        )
        assert req.include_assembly_audit is True


# ---------------------------------------------------------------------------
# 2. AuditOffByDefault — no audit key when flag omitted or false
# ---------------------------------------------------------------------------

class TestWiring_AuditOffByDefault:
    def test_omitted_flag_no_audit_key(self, client):
        ws, ag = _bootstrap(client)
        # Send payload WITHOUT the include_assembly_audit field — pydantic
        # default takes over.
        payload = _retrieve_payload(ws, ag)
        payload.pop("include_assembly_audit")
        r = client.post("/retrieve", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "assembly_audit" not in body

    def test_explicit_false_no_audit_key(self, client):
        ws, ag = _bootstrap(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag, include_audit=False))
        assert r.status_code == 200, r.text
        body = r.json()
        assert "assembly_audit" not in body


# ---------------------------------------------------------------------------
# 3. AuditOnReturnsAudit — response carries the v0.2 §4.2 top-level shape
# ---------------------------------------------------------------------------

_EXPECTED_AUDIT_TOP_LEVEL_KEYS = frozenset({
    "lane_version",
    "timestamp",
    "request",
    "embedder",
    "filter_a",
    "assembly",
    "character",
    "spirit_return_summary",
    "tool_result_summary",
})


class TestWiring_AuditOnReturnsAudit:
    def test_audit_key_present(self, client):
        ws, ag = _bootstrap(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag, include_audit=True))
        assert r.status_code == 200, r.text
        body = r.json()
        assert "assembly_audit" in body

    def test_audit_top_level_keys_match_v0_2_4_2_schema(self, client):
        ws, ag = _bootstrap(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag, include_audit=True))
        body = r.json()
        audit = body["assembly_audit"]
        assert set(audit.keys()) == _EXPECTED_AUDIT_TOP_LEVEL_KEYS

    def test_audit_lane_version_is_v0_2(self, client):
        ws, ag = _bootstrap(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag, include_audit=True))
        body = r.json()
        assert (
            body["assembly_audit"]["lane_version"]
            == "memory_to_prompt_observability_v0.2"
        )

    def test_audit_request_block_reflects_request(self, client):
        ws, ag = _bootstrap(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag, include_audit=True))
        body = r.json()
        req_block = body["assembly_audit"]["request"]
        assert req_block["workspace_id"] == ws
        assert req_block["agent_id"] == ag
        assert req_block["profile"] == "companion"
        assert req_block["surface"] == "llm_context"

    def test_audit_filter_a_archive_filter_applied_true_in_production(self, client):
        """v0.2.4-A1: production audits now report
        ``archive_filter_applied=True``. Replaces the v0.2 first-revision
        contract that honestly reported ``False`` while the gap was
        deferred (per S3 Decision 5). The /retrieve handler runs the
        archive filter unconditionally between ArchiveStore.retrieve()
        and assemble_context() (app.py §3b), so the audit field is
        always True in production after Commit 4 — including when
        archive_hits is empty (filter posture is active even when there
        is nothing to filter).
        """
        ws, ag = _bootstrap(client)
        r = client.post("/retrieve", json=_retrieve_payload(ws, ag, include_audit=True))
        body = r.json()
        assert body["assembly_audit"]["filter_a"]["archive_filter_applied"] is True


# ---------------------------------------------------------------------------
# 4. ResultsByteIdentityABTest — audit on vs off must not change blocks/text
# ---------------------------------------------------------------------------

class TestWiring_ResultsByteIdentityABTest:
    def test_common_keys_byte_identical_with_vs_without_audit(self, client):
        """Audit is observability only. Same query with vs without
        the flag must produce byte-identical `blocks`, `assembled_text`,
        `tokens_used`, `profile`, `block_token_counts` keys.
        """
        ws, ag = _bootstrap(client)

        r_off = client.post("/retrieve", json=_retrieve_payload(ws, ag, include_audit=False))
        r_on = client.post("/retrieve", json=_retrieve_payload(ws, ag, include_audit=True))

        body_off = r_off.json()
        body_on = r_on.json()

        # The audit-on response carries one extra top-level key
        # `assembly_audit`. Everything else common must be identical.
        for shared_key in ("blocks", "assembled_text", "tokens_used",
                           "profile", "block_token_counts",
                           "token_budget", "selection_log"):
            assert body_off.get(shared_key) == body_on.get(shared_key), (
                f"common key {shared_key!r} diverges between audit-off "
                f"and audit-on responses"
            )

        # The audit-on response has exactly one extra top-level key.
        extra = set(body_on.keys()) - set(body_off.keys())
        assert extra == {"assembly_audit"}, (
            f"audit-on response added unexpected keys: {extra!r}"
        )


# ---------------------------------------------------------------------------
# 5. FabricQueryReturnShape — S5 additive keys on fabric.query() return
# ---------------------------------------------------------------------------

class TestWiring_FabricQueryReturnShape:
    def test_filter_excluded_key_present(self, client):
        """fabric.query() return now includes `filter_excluded`
        (alias of the existing `excluded` key) for build_assembly_audit
        compatibility.
        """
        ws, ag = _bootstrap(client)
        r = client.post("/agent/query", json={
            "workspace_id": ws,
            "agent_id": ag,
            "query": "What did we decide?",
            "top_k": 5,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert "filter_excluded" in body
        # And the historical key remains for backward-compat.
        assert "excluded" in body
        # Both carry the same list (alias).
        assert body["filter_excluded"] == body["excluded"]

    def test_core_hits_in_count_key_present(self, client):
        ws, ag = _bootstrap(client)
        r = client.post("/agent/query", json={
            "workspace_id": ws,
            "agent_id": ag,
            "query": "What did we decide?",
            "top_k": 5,
        })
        body = r.json()
        assert "_core_hits_in_count" in body
        # Sanity: in_count == out_count + excluded_count (FILTER-A is
        # the only reduction step between rescored and the return).
        assert (
            body["_core_hits_in_count"]
            == len(body["results"]) + len(body["filter_excluded"])
        )

    def test_authority_guard_rejected_zero(self, client):
        """H4d guard is fail-loud: any rejection raises before reaching
        the return path. In normal operation the count is always 0;
        the key is present so future v0.2.x can propagate a real count.
        """
        ws, ag = _bootstrap(client)
        r = client.post("/agent/query", json={
            "workspace_id": ws,
            "agent_id": ag,
            "query": "What did we decide?",
            "top_k": 5,
        })
        body = r.json()
        assert body["_authority_guard_rejected"] == 0


# ---------------------------------------------------------------------------
# 6. MemoryBridgeKwarg — kwarg sent in POST payload
# ---------------------------------------------------------------------------

class TestWiring_MemoryBridgeKwarg:
    def test_kwarg_omitted_default_false_in_payload(self):
        """MemoryBridge.retrieve() without the kwarg sends
        include_assembly_audit=False in the POST payload.
        """
        from live_agent.memory_bridge import MemoryBridge

        bridge = MemoryBridge(
            base_url="http://127.0.0.1:9999",
            workspace_id="ws",
            agent_id="ag",
        )
        # Mock requests.post to capture the payload without making a
        # real HTTP call.
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "blocks": [], "character_context": {}
        }
        with patch("live_agent.memory_bridge.requests.post",
                   return_value=mock_response) as mock_post:
            bridge.retrieve("hello")
        # Inspect the captured payload.
        kwargs = mock_post.call_args.kwargs
        payload = kwargs.get("json") or {}
        assert payload.get("include_assembly_audit") is False

    def test_kwarg_true_passed_in_payload(self):
        from live_agent.memory_bridge import MemoryBridge

        bridge = MemoryBridge(
            base_url="http://127.0.0.1:9999",
            workspace_id="ws",
            agent_id="ag",
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "blocks": [], "character_context": {}, "assembly_audit": {}
        }
        with patch("live_agent.memory_bridge.requests.post",
                   return_value=mock_response) as mock_post:
            result = bridge.retrieve("hello", include_assembly_audit=True)
        kwargs = mock_post.call_args.kwargs
        payload = kwargs.get("json") or {}
        assert payload.get("include_assembly_audit") is True
        # And the bridge passes the response through (so audit reaches
        # the caller).
        assert "assembly_audit" in result


# ---------------------------------------------------------------------------
# 7. ArchiveFilterA — v0.2.4-A1 archive FILTER-A wiring (defense-in-depth)
# ---------------------------------------------------------------------------

def _ingest_archive_with_governance(workspace, agent, *, text, title, governance):
    """Ingest an archive document with explicit governance metadata.

    The /archive/ingest_document endpoint's request model does NOT
    accept governance in v0.2.4-A1 (extending that API surface would
    be a separate ratifiable slice). For tests we bypass the HTTP
    layer and call ArchiveStore.ingest_document directly through
    appmod._get_archive_store, which exercises the real storage +
    retrieve path (Commit 1 — per-chunk governance) end-to-end.
    """
    import torment_service.app as appmod
    store = appmod._get_archive_store(workspace, agent)
    return store.ingest_document(
        text=text, title=title, governance=governance,
    )


class TestWiring_ArchiveFilterA:
    """v0.2.4-A1 — archive FILTER-A in production /retrieve.

    Filter runs UNCONDITIONALLY between ArchiveStore.retrieve() and
    assemble_context(). The ``include_assembly_audit`` flag controls
    only whether the audit PAYLOAD is returned; it never controls
    whether archive content is filtered. Non-shareable archive chunks
    must be absent from ``blocks[BLOCK_ARCHIVE]`` and from
    ``assembled_text`` regardless of audit flag state.
    """

    def test_archive_excluded_empty_list_when_no_archive_ingested(self, client):
        """No archive chunks ingested → no exclusions → archive_excluded
        is an empty list. Presence of the empty list (not absent key)
        is the structural signal that the filter ran. v0.2.4-A1
        production posture: filter always runs at /retrieve.
        """
        ws, ag = _bootstrap(client)
        r = client.post(
            "/retrieve",
            json=_retrieve_payload(ws, ag, include_audit=True),
        )
        body = r.json()
        assert "archive_excluded" in body["assembly_audit"]["filter_a"]
        assert body["assembly_audit"]["filter_a"]["archive_excluded"] == []

    def test_archive_excluded_records_non_shareable_chunk(self, client):
        """LOAD-BEARING: a non-shareable archive chunk surfaces in
        ``filter_a.archive_excluded`` with the full v0.2.4-A0 shape:
        ``{chunk_id, doc_id, excluded_reason}``.
        """
        ws, ag = _bootstrap(client)
        result = _ingest_archive_with_governance(
            ws, ag,
            text=(
                "Private memo about storage policy decisions. "
                "Do not share this externally."
            ),
            title="private_storage_memo",
            governance={"non_shareable": True},
        )
        doc_id = result["doc_id"]

        r = client.post(
            "/retrieve",
            json=_retrieve_payload(ws, ag, include_audit=True),
        )
        body = r.json()
        archive_excluded = body["assembly_audit"]["filter_a"]["archive_excluded"]
        # The hash embedder reliably matches our chunk against the
        # storage-themed bootstrap query; assert at least one chunk
        # from OUR doc was excluded with the expected shape.
        ours = [e for e in archive_excluded if e["doc_id"] == doc_id]
        assert len(ours) >= 1, (
            f"expected at least one exclusion entry with doc_id={doc_id}; "
            f"got archive_excluded={archive_excluded!r}"
        )
        for e in ours:
            assert e["excluded_reason"] == "non_shareable"
            assert e["chunk_id"].startswith(doc_id), (
                f"chunk_id={e['chunk_id']!r} does not start with "
                f"doc_id={doc_id!r}"
            )

    def test_non_shareable_archive_chunk_absent_from_blocks(self, client):
        """LOAD-BEARING — the actual privacy invariant: non-shareable
        archive chunks must NOT appear in ``blocks[BLOCK_ARCHIVE]``.
        This is the reason the filter exists; the audit signal is
        secondary observability.
        """
        ws, ag = _bootstrap(client)
        result = _ingest_archive_with_governance(
            ws, ag,
            text=(
                "Private memo about storage policy decisions. "
                "Internal only — restricted distribution."
            ),
            title="private_blocks_check",
            governance={"non_shareable": True},
        )
        doc_id = result["doc_id"]

        r = client.post(
            "/retrieve",
            json=_retrieve_payload(ws, ag, include_audit=False),
        )
        body = r.json()
        archive_blocks = body.get("blocks", {}).get("archive_context", [])
        for block in archive_blocks:
            meta = block.get("metadata", {}) or {}
            assert meta.get("doc_id") != doc_id, (
                f"non-shareable chunk leaked into BLOCK_ARCHIVE: "
                f"doc_id={doc_id} present in block metadata={meta!r}"
            )

    def test_non_shareable_archive_chunk_absent_from_assembled_text(
        self, client
    ):
        """LOAD-BEARING companion: the non-shareable chunk's text
        marker must not appear in ``assembled_text`` either. Tests
        the text-level privacy invariant directly (not just metadata).
        """
        ws, ag = _bootstrap(client)
        secret_phrase = "TOKEN_PRIVATE_STORAGE_MARKER_42_NOT_SHAREABLE"
        _ingest_archive_with_governance(
            ws, ag,
            text=(
                f"Private memo about storage. {secret_phrase}. "
                "Restricted distribution."
            ),
            title="private_text_check",
            governance={"non_shareable": True},
        )

        r = client.post(
            "/retrieve",
            json=_retrieve_payload(ws, ag, include_audit=False),
        )
        body = r.json()
        assert secret_phrase not in body.get("assembled_text", ""), (
            f"non-shareable archive marker {secret_phrase!r} leaked "
            f"into assembled_text"
        )

    def test_filter_runs_when_audit_off(self, client):
        """CRITICAL: filter must be unconditional. ``include_assembly_audit``
        controls audit PAYLOAD return only; it MUST NOT control whether
        content is filtered. A non-shareable chunk must be absent from
        blocks/text regardless of the audit flag.

        This test is the single most load-bearing assertion in this
        file: it proves that the privacy invariant (no non-shareable
        archive content in LLM-facing surfaces) holds regardless of
        observability surface state.
        """
        ws, ag = _bootstrap(client)
        secret_marker = "TOKEN_UNCONDITIONAL_FILTER_INVARIANT_99"
        _ingest_archive_with_governance(
            ws, ag,
            text=(
                f"Private storage details. {secret_marker}. "
                "Restricted distribution memo."
            ),
            title="unconditional_filter_check",
            governance={"non_shareable": True},
        )

        # Audit-OFF call: the chunk MUST still be filtered.
        r_off = client.post(
            "/retrieve",
            json=_retrieve_payload(ws, ag, include_audit=False),
        )
        body_off = r_off.json()
        assert "assembly_audit" not in body_off  # audit-off path confirmed
        assert secret_marker not in body_off.get("assembled_text", ""), (
            "audit-off response leaked non-shareable archive marker "
            "into assembled_text — filter must run unconditionally"
        )
        for b in body_off.get("blocks", {}).get("archive_context", []):
            assert secret_marker not in b.get("text", ""), (
                f"audit-off response leaked non-shareable marker into "
                f"archive_context block: {b!r}"
            )

        # Audit-ON call: same fixture, same filtering — chunk still
        # excluded from blocks/text, and now ALSO surfaces in
        # archive_excluded.
        r_on = client.post(
            "/retrieve",
            json=_retrieve_payload(ws, ag, include_audit=True),
        )
        body_on = r_on.json()
        assert secret_marker not in body_on.get("assembled_text", "")
        for b in body_on.get("blocks", {}).get("archive_context", []):
            assert secret_marker not in b.get("text", "")
        # The exclusion is honestly reported in the audit.
        archive_excluded = body_on["assembly_audit"]["filter_a"][
            "archive_excluded"
        ]
        assert len(archive_excluded) >= 1, (
            "audit-on response missing expected archive_excluded entry "
            "for the non-shareable chunk"
        )

    def test_audit_off_response_has_no_audit_only_keys(self, client):
        """No audit-only keys leak into the audit-off response. The
        archive filter runs in both paths, but only the audit-on path
        materializes audit observability into the response shape.
        """
        ws, ag = _bootstrap(client)
        _ingest_archive_with_governance(
            ws, ag,
            text="Private storage policy memo for internal use.",
            title="leak_check",
            governance={"non_shareable": True},
        )
        r_off = client.post(
            "/retrieve",
            json=_retrieve_payload(ws, ag, include_audit=False),
        )
        body_off = r_off.json()
        # No top-level audit key.
        assert "assembly_audit" not in body_off
        # No archive-filter observability bleeds into the audit-off
        # top-level shape.
        assert "archive_excluded" not in body_off
        assert "archive_filter_applied" not in body_off
        assert "archive_filter_excluded" not in body_off


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
