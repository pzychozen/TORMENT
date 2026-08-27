"""P1 regressions for canonical commit truth and identity rebinding."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from torment_service.archive_memory import ArchiveStore
from torment_service.fabric import TormentFabric
from torment_service.identity import PersistentIdentityMissingError


WORKSPACE_ID = "p1-workspace"
AGENT_ID = "p1-agent"


def _configure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")


def _new_fabric(root: Path, monkeypatch: pytest.MonkeyPatch) -> TormentFabric:
    _configure_env(monkeypatch)
    return TormentFabric(str(root))


def _identity_path(root: Path) -> Path:
    return root / "workspaces" / WORKSPACE_ID / "agents" / AGENT_ID / "identity.json"


def _private_path(root: Path, name: str) -> Path:
    return root / "workspaces" / WORKSPACE_ID / "agents" / AGENT_ID / "private" / name


def _force_writes(fabric: TormentFabric) -> None:
    identity = fabric.create_agent(WORKSPACE_ID, AGENT_ID)
    identity.overlay["write_threshold"] = 0.0
    fabric.ident_store.save(identity)


def test_new_empty_agent_creates_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric = _new_fabric(tmp_path, monkeypatch)
    try:
        created = fabric.create_agent(WORKSPACE_ID, AGENT_ID)

        assert (created.workspace_id, created.agent_id) == (WORKSPACE_ID, AGENT_ID)
        assert _identity_path(tmp_path).exists()
        assert fabric.private_graphs[fabric._agent_key(WORKSPACE_ID, AGENT_ID)].entities == {}
    finally:
        fabric.close()


def test_flush_failure_never_reports_or_leaves_a_live_canonical_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric = _new_fabric(tmp_path, monkeypatch)
    reopened = None
    try:
        _force_writes(fabric)
        graph = fabric.private_graphs[fabric._agent_key(WORKSPACE_ID, AGENT_ID)]

        original_search = graph.search_by_embedding
        search_calls = []

        def observed_search(*args, **kwargs):
            search_calls.append((args, kwargs))
            return original_search(*args, **kwargs)

        def fail_flush(_eid: int) -> None:
            raise OSError("injected canonical commit failure")

        monkeypatch.setattr(graph, "search_by_embedding", observed_search)
        monkeypatch.setattr(graph, "flush_node", fail_flush)
        fabric._hivemind_enable = True
        monkeypatch.setattr(
            fabric,
            "_get_collective_field",
            lambda *_args, **_kwargs: pytest.fail("failed commit reached Hivemind emission"),
        )
        monkeypatch.setattr(
            fabric,
            "_maybe_emit_identity_anchor",
            lambda *_args, **_kwargs: pytest.fail("failed commit reached identity-anchor emission"),
        )

        result = fabric.ingest(
            WORKSPACE_ID,
            AGENT_ID,
            "P1 unique flush failure proof",
            step=1,
            domain_id="personal",
        )

        assert result == {
            "stored": False,
            "reinforced": False,
            "failure_code": "canonical_commit_failed",
            "eid": None,
            "domain_chosen": "personal",
        }
        assert search_calls and len(search_calls) == 1
        assert graph.entities == {}
        assert graph.world.entities == []
        assert graph.edges == []
        assert graph._emb_by_eid == {}
        assert not graph.search("P1 unique flush failure proof", top_k=5, user_id=AGENT_ID)

        assert not Path(graph.meta_path).exists()
        events = [json.loads(line) for line in Path(graph.events_path).read_text().splitlines()]
        assert [event["type"] for event in events] == ["MEMORY_CREATE"]
        assert (Path(graph.data_dir) / "embeddings" / "manifest.json").exists()

        fabric.close()
        reopened = _new_fabric(tmp_path, monkeypatch)
        reopened.create_agent(WORKSPACE_ID, AGENT_ID)
        reopened_graph = reopened.private_graphs[
            reopened._agent_key(WORKSPACE_ID, AGENT_ID)
        ]
        assert reopened_graph.entities == {}
    finally:
        if reopened is not None:
            reopened.close()
        else:
            fabric.close()


def test_missing_identity_over_private_canonical_memory_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric = _new_fabric(tmp_path, monkeypatch)
    rebound = None
    try:
        _force_writes(fabric)
        stored = fabric.ingest(
            WORKSPACE_ID,
            AGENT_ID,
            "P1 canonical private memory",
            step=1,
            domain_id="personal",
        )
        assert stored["stored"] is True
        nodes_path = _private_path(tmp_path, "nodes.jsonl")
        before_nodes = nodes_path.read_bytes()
        identity_path = _identity_path(tmp_path)
        identity_path.unlink()
        fabric.close()

        rebound = _new_fabric(tmp_path, monkeypatch)
        with pytest.raises(HTTPException) as raised:
            rebound.create_agent(WORKSPACE_ID, AGENT_ID)

        assert raised.value.status_code == 409
        assert raised.value.detail == (
            "Persistent identity is missing for existing canonical agent memory; "
            "recovery is required"
        )
        assert isinstance(raised.value.__cause__, PersistentIdentityMissingError)
        assert not identity_path.exists()
        assert nodes_path.read_bytes() == before_nodes
        assert rebound._agent_key(WORKSPACE_ID, AGENT_ID) not in rebound.private_graphs
    finally:
        if rebound is not None:
            rebound.close()
        else:
            fabric.close()


def test_missing_identity_over_agent_archive_memory_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive_dir = (
        tmp_path / "workspaces" / WORKSPACE_ID / "agents" / AGENT_ID / "memory_archive"
    )
    store = ArchiveStore(str(archive_dir))
    try:
        store.ingest_document(
            text="P1 archive canonical ownership proof",
            title="P1 archive",
            doc_id="p1-archive-document",
        )
    finally:
        store.close()

    documents_path = archive_dir / "documents.jsonl"
    before_documents = documents_path.read_bytes()
    fabric = _new_fabric(tmp_path, monkeypatch)
    try:
        with pytest.raises(HTTPException) as raised:
            fabric.create_agent(WORKSPACE_ID, AGENT_ID)

        assert raised.value.status_code == 409
        assert not _identity_path(tmp_path).exists()
        assert documents_path.read_bytes() == before_documents
    finally:
        fabric.close()


def test_missing_identity_with_derived_residue_allows_new_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embedding_manifest = _private_path(tmp_path, "embeddings/manifest.json")
    embedding_manifest.parent.mkdir(parents=True)
    embedding_manifest.write_text('{"total_rows": 1}')
    _private_path(tmp_path, "memory_events.jsonl").write_text(
        '{"type": "MEMORY_CREATE", "eid": 1}\n'
    )
    index_path = (
        tmp_path / "workspaces" / WORKSPACE_ID / "agents" / AGENT_ID / "index" / "index.sqlite"
    )
    index_path.parent.mkdir(parents=True)
    index_path.write_bytes(b"derived-only")

    fabric = _new_fabric(tmp_path, monkeypatch)
    try:
        created = fabric.create_agent(WORKSPACE_ID, AGENT_ID)

        assert (created.workspace_id, created.agent_id) == (WORKSPACE_ID, AGENT_ID)
        assert _identity_path(tmp_path).exists()
        assert fabric.private_graphs[fabric._agent_key(WORKSPACE_ID, AGENT_ID)].entities == {}
    finally:
        fabric.close()


def test_malformed_identity_remains_fail_closed_without_rewrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity_path = _identity_path(tmp_path)
    identity_path.parent.mkdir(parents=True)
    identity_path.write_text("{ malformed identity")
    before = identity_path.read_bytes()

    fabric = _new_fabric(tmp_path, monkeypatch)
    try:
        with pytest.raises(json.JSONDecodeError):
            fabric.create_agent(WORKSPACE_ID, AGENT_ID)

        assert identity_path.read_bytes() == before
    finally:
        fabric.close()


def test_valid_identity_with_existing_memory_loads_normally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fabric = _new_fabric(tmp_path, monkeypatch)
    reopened = None
    try:
        _force_writes(fabric)
        result = fabric.ingest(
            WORKSPACE_ID,
            AGENT_ID,
            "P1 valid identity reload proof",
            step=1,
            domain_id="personal",
        )
        assert result["stored"] is True
        fabric.close()

        reopened = _new_fabric(tmp_path, monkeypatch)
        identity = reopened.create_agent(WORKSPACE_ID, AGENT_ID)
        graph = reopened.private_graphs[reopened._agent_key(WORKSPACE_ID, AGENT_ID)]

        assert (identity.workspace_id, identity.agent_id) == (WORKSPACE_ID, AGENT_ID)
        assert len(graph.entities) == 1
    finally:
        if reopened is not None:
            reopened.close()
        else:
            fabric.close()
