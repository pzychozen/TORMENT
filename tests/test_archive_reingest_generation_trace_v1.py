"""Regression coverage for Archive same-document replacement durability."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from tools.compact_archive_memory import compact_chunks, compact_documents
from torment_service.archive_memory import ArchiveStore
from torment_service.sqlite_index import IndexManager


DOC_ID = "archive_reingest_generation_trace_v1_document"
TITLE = "ARCHIVE_REINGEST_GENERATION_TRACE_V1 document"
OLD_PREFIX = "ARCHIVE_REINGEST_GENERATION_TRACE_V1_OLD"
NEW_PREFIX = "ARCHIVE_REINGEST_GENERATION_TRACE_V1_NEW"


def _jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _chunked_text(prefix: str, count: int) -> str:
    """Make one short, distinct archive chunk per markdown section."""
    return "\n\n".join(
        f"## {prefix} section {index}\n" + " ".join([f"{prefix}_{index}"] * 12)
        for index in range(count)
    )


def _ingest(store: ArchiveStore, prefix: str, count: int, **kwargs) -> dict:
    result = store.ingest_document(
        text=_chunked_text(prefix, count),
        title=TITLE,
        doc_id=DOC_ID,
        target_tokens=40,
        max_tokens=100,
        overlap_tokens=0,
        **kwargs,
    )
    assert result["chunk_count"] == count
    return result


def _assert_current(store: ArchiveStore, prefix: str, count: int) -> None:
    chunks = store.get_chunks_for_document(DOC_ID)
    assert len(chunks) == count
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(count))
    assert all(prefix in chunk["text"] for chunk in chunks)
    assert all(OLD_PREFIX not in chunk["text"] for chunk in chunks if prefix != OLD_PREFIX)
    assert len(store._chunk_embeddings) == count
    if prefix != OLD_PREFIX:
        old_hits = store.retrieve(f"{OLD_PREFIX}_11", top_k=20, doc_id_filter=DOC_ID)
        assert all(OLD_PREFIX not in hit["text"] for hit in old_hits)


def _rebuild(index: IndexManager, store: ArchiveStore) -> None:
    counts = index.rebuild_from_jsonl(
        nodes_path="",
        archive_documents_path=store.documents_path,
        archive_chunks_path=store.chunks_path,
    )
    # Rebuild counters retain their historic input-record accounting.  The
    # sidecar rows themselves must represent only the canonical incarnation.
    assert counts["documents"] >= 1
    assert counts["chunks"] >= store.get_document(DOC_ID)["chunk_count"]
    assert len(index.search_archive_metadata(TITLE)) == 1
    chunks = index.get_chunks_for_document(DOC_ID)
    assert len(chunks) == store.get_document(DOC_ID)["chunk_count"]
    assert not any(chunk["chunk_id"].endswith("_0011") for chunk in chunks)


def _compact_and_assert_one(store: ArchiveStore) -> None:
    _, active_doc_ids = compact_documents(store.documents_path, dry_run=False)
    compact_chunks(store.chunks_path, active_doc_ids, dry_run=False)
    chunks = _jsonl(store.chunks_path)
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert NEW_PREFIX in chunks[0]["text"]


def test_delete_then_reingest_replaces_across_restart_rebuild_and_compaction() -> None:
    with tempfile.TemporaryDirectory(prefix="archive_reingest_generation_v1_") as tmp:
        index = IndexManager(os.path.join(tmp, "index"))
        store = ArchiveStore(os.path.join(tmp, "memory_archive"), sqlite_index=index)
        reloaded = None
        try:
            _ingest(store, OLD_PREFIX, 12)
            assert store.delete_document(DOC_ID) is True
            _ingest(store, NEW_PREFIX, 1)
            _assert_current(store, NEW_PREFIX, 1)
            assert len(index.get_chunks_for_document(DOC_ID)) == 1

            assert [record["chunk_count"] for record in _jsonl(store.documents_path)] == [12, 1]
            assert [record["type"] for record in _jsonl(store.events_path)] == [
                "DOCUMENT_INGESTED", "DOCUMENT_DELETED", "DOCUMENT_INGESTED",
            ]

            store.close()
            reloaded = ArchiveStore(store.archive_dir, sqlite_index=index)
            _assert_current(reloaded, NEW_PREFIX, 1)
            _rebuild(index, reloaded)
            _compact_and_assert_one(reloaded)
        finally:
            (reloaded or store).close()
            index.close()


def test_direct_reingest_replaces_live_restart_sqlite_and_compactor() -> None:
    with tempfile.TemporaryDirectory(prefix="archive_reingest_generation_v1_") as tmp:
        index = IndexManager(os.path.join(tmp, "index"))
        store = ArchiveStore(os.path.join(tmp, "memory_archive"), sqlite_index=index)
        reloaded = None
        try:
            _ingest(store, OLD_PREFIX, 12)
            _ingest(store, NEW_PREFIX, 1)
            _assert_current(store, NEW_PREFIX, 1)
            assert len(index.get_chunks_for_document(DOC_ID)) == 1
            assert [record["type"] for record in _jsonl(store.events_path)] == [
                "DOCUMENT_INGESTED", "DOCUMENT_INGESTED",
            ]

            store.close()
            reloaded = ArchiveStore(store.archive_dir, sqlite_index=index)
            _assert_current(reloaded, NEW_PREFIX, 1)
            _rebuild(index, reloaded)
            _compact_and_assert_one(reloaded)
        finally:
            (reloaded or store).close()
            index.close()


def test_document_append_failure_preserves_old_live_chunks_before_supersession(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with tempfile.TemporaryDirectory(prefix="archive_reingest_generation_v1_") as tmp:
        index = IndexManager(os.path.join(tmp, "index"))
        store = ArchiveStore(os.path.join(tmp, "memory_archive"), sqlite_index=index)
        try:
            _ingest(store, OLD_PREFIX, 12)
            append_jsonl = store._append_jsonl

            def fail_document_append(path: str, record: dict) -> None:
                if path == store.documents_path:
                    raise OSError("simulated document append failure")
                append_jsonl(path, record)

            monkeypatch.setattr(store, "_append_jsonl", fail_document_append)
            with pytest.raises(OSError, match="simulated document append failure"):
                _ingest(store, NEW_PREFIX, 1)

            old_chunks = store.get_chunks_for_document(DOC_ID)
            assert len(old_chunks) == 12
            assert all(OLD_PREFIX in chunk["text"] for chunk in old_chunks)
            assert len(index.get_chunks_for_document(DOC_ID)) == 12
        finally:
            store.close()
            index.close()


def test_same_count_and_larger_replacements_keep_exact_current_range() -> None:
    with tempfile.TemporaryDirectory(prefix="archive_reingest_generation_v1_") as tmp:
        store = ArchiveStore(os.path.join(tmp, "memory_archive"))
        reloaded = None
        try:
            _ingest(store, OLD_PREFIX, 12)
            _ingest(store, NEW_PREFIX, 12)
            _assert_current(store, NEW_PREFIX, 12)
            _ingest(store, NEW_PREFIX, 1)
            _ingest(store, OLD_PREFIX, 12)
            _assert_current(store, OLD_PREFIX, 12)

            store.close()
            reloaded = ArchiveStore(store.archive_dir)
            _assert_current(reloaded, OLD_PREFIX, 12)
        finally:
            (reloaded or store).close()


def test_multiple_reactivations_and_final_delete_obey_final_lifecycle_state() -> None:
    with tempfile.TemporaryDirectory(prefix="archive_reingest_generation_v1_") as tmp:
        index = IndexManager(os.path.join(tmp, "index"))
        store = ArchiveStore(os.path.join(tmp, "memory_archive"), sqlite_index=index)
        reloaded = None
        try:
            _ingest(store, OLD_PREFIX, 12)
            assert store.delete_document(DOC_ID)
            _ingest(store, NEW_PREFIX, 4)
            assert store.delete_document(DOC_ID)
            _ingest(store, NEW_PREFIX, 1)
            _assert_current(store, NEW_PREFIX, 1)
            assert store.delete_document(DOC_ID)

            store.close()
            reloaded = ArchiveStore(store.archive_dir, sqlite_index=index)
            assert reloaded.get_document(DOC_ID) is None
            assert reloaded.get_chunks_for_document(DOC_ID) == []
            assert reloaded._chunk_embeddings == {}
            counts = index.rebuild_from_jsonl(
                nodes_path="",
                archive_documents_path=reloaded.documents_path,
                archive_chunks_path=reloaded.chunks_path,
            )
            assert counts["documents"] == counts["chunks"] == 0
            _, active_doc_ids = compact_documents(reloaded.documents_path, dry_run=False)
            compact_chunks(reloaded.chunks_path, active_doc_ids, dry_run=False)
            assert _jsonl(reloaded.documents_path) == []
            assert _jsonl(reloaded.chunks_path) == []
        finally:
            (reloaded or store).close()
            index.close()


def test_legacy_records_without_chunk_count_remain_unbounded_and_active() -> None:
    with tempfile.TemporaryDirectory(prefix="archive_reingest_generation_v1_") as tmp:
        archive_dir = os.path.join(tmp, "memory_archive")
        os.makedirs(archive_dir)
        with open(os.path.join(archive_dir, "documents.jsonl"), "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"doc_id": DOC_ID, "title": TITLE}) + "\n")
        with open(os.path.join(archive_dir, "chunks.jsonl"), "w", encoding="utf-8") as handle:
            for index in range(2):
                handle.write(json.dumps({
                    "chunk_id": f"{DOC_ID}_chunk_{index:04d}", "doc_id": DOC_ID,
                    "chunk_index": index, "text": f"legacy {index}",
                    "token_count": 1, "section_path": [], "section_title": "",
                }) + "\n")

        store = ArchiveStore(archive_dir)
        try:
            assert store.get_document(DOC_ID) is not None
            assert len(store.get_chunks_for_document(DOC_ID)) == 2
        finally:
            store.close()


def test_malformed_chunk_count_retains_legacy_unbounded_chunk_loading() -> None:
    with tempfile.TemporaryDirectory(prefix="archive_reingest_generation_v1_") as tmp:
        archive_dir = os.path.join(tmp, "memory_archive")
        os.makedirs(archive_dir)
        with open(os.path.join(archive_dir, "documents.jsonl"), "w", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "doc_id": DOC_ID, "title": TITLE, "chunk_count": "not-an-int",
            }) + "\n")
        with open(os.path.join(archive_dir, "chunks.jsonl"), "w", encoding="utf-8") as handle:
            for index in range(2):
                handle.write(json.dumps({
                    "chunk_id": f"{DOC_ID}_chunk_{index:04d}", "doc_id": DOC_ID,
                    "chunk_index": index, "text": f"legacy malformed {index}",
                    "token_count": 1, "section_path": [], "section_title": "",
                }) + "\n")

        store = ArchiveStore(archive_dir)
        try:
            assert store.get_document(DOC_ID) is not None
            assert len(store.get_chunks_for_document(DOC_ID)) == 2
        finally:
            store.close()


def test_replacement_preserves_current_chunk_governance() -> None:
    with tempfile.TemporaryDirectory(prefix="archive_reingest_generation_v1_") as tmp:
        store = ArchiveStore(os.path.join(tmp, "memory_archive"))
        try:
            _ingest(store, OLD_PREFIX, 12, governance={"non_shareable": True})
            _ingest(store, NEW_PREFIX, 1, governance={"non_shareable": False})
            chunks = store.get_chunks_for_document(DOC_ID)
            assert len(chunks) == 1
            assert chunks[0]["governance"] == {"non_shareable": False}
        finally:
            store.close()
