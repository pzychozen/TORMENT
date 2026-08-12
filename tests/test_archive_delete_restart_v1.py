"""Mechanical proof for ARCHIVE_DELETE_RESTART_V1.

This test intentionally records the current persistence semantics.  It uses
only a TemporaryDirectory and the production ArchiveStore / IndexManager
paths; it never reads or writes a configured TORMENT data directory.
"""
from __future__ import annotations

import json
import os
import tempfile

from tools.compact_archive_memory import compact_documents
from torment_service.archive_memory import ArchiveStore
from torment_service.sqlite_index import IndexManager


DOC_ID = "archive_delete_restart_v1_document"
TITLE = "ARCHIVE_DELETE_RESTART_V1 uniquely identifiable document"
TEXT = "ARCHIVE_DELETE_RESTART_V1 uniquely identifiable document retrieval payload."
REINGESTED_TEXT = "ARCHIVE_DELETE_RESTART_V1 re-ingested replacement payload."


def _jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _state(store: ArchiveStore, index: IndexManager) -> dict:
    return {
        "store_document": store.get_document(DOC_ID) is not None,
        "store_chunks": len(store.get_chunks_for_document(DOC_ID)),
        "store_hits": len(store.retrieve(TEXT, top_k=5, doc_id_filter=DOC_ID)),
        "index_documents": len(index.search_archive_metadata(TITLE)),
        "index_chunks": len(index.get_chunks_for_document(DOC_ID)),
    }


def test_archive_delete_restart_v1() -> None:
    """Deleted Archive records stay absent after Store reload and SQLite rebuild."""
    with tempfile.TemporaryDirectory(prefix="archive_delete_restart_v1_") as tmp:
        archive_dir = os.path.join(tmp, "memory_archive")
        index = IndexManager(os.path.join(tmp, "index"))
        store = ArchiveStore(archive_dir=archive_dir, sqlite_index=index)
        reloaded = None
        try:
            ingested = store.ingest_document(text=TEXT, title=TITLE, doc_id=DOC_ID)
            assert ingested["chunk_count"] == 1

            before = _state(store, index)
            assert before == {
                "store_document": True,
                "store_chunks": 1,
                "store_hits": 1,
                "index_documents": 1,
                "index_chunks": 1,
            }

            assert store.delete_document(DOC_ID) is True
            deleted = _state(store, index)
            assert deleted == {
                "store_document": False,
                "store_chunks": 0,
                "store_hits": 0,
                "index_documents": 0,
                "index_chunks": 0,
            }

            documents = _jsonl(store.documents_path)
            chunks = _jsonl(store.chunks_path)
            events = _jsonl(store.events_path)
            assert [record["doc_id"] for record in documents] == [DOC_ID]
            assert [record["doc_id"] for record in chunks] == [DOC_ID]
            assert events == [
                {
                    "type": "DOCUMENT_INGESTED",
                    "ts": events[0]["ts"],
                    "doc_id": DOC_ID,
                    "title": TITLE,
                    "source_type": "text",
                    "chunk_count": 1,
                    "token_count": events[0]["token_count"],
                },
                {
                    "type": "DOCUMENT_DELETED",
                    "ts": events[1]["ts"],
                    "doc_id": DOC_ID,
                    "chunks_removed": 1,
                },
            ]
            assert "_deleted" not in documents[0]

            # The maintenance tool replays events.jsonl before deciding which
            # document records are active.
            compact_stats, active_doc_ids = compact_documents(
                store.documents_path, dry_run=True
            )
            assert compact_stats["deleted_docs"] == 1
            assert active_doc_ids == set()

            store.close()
            reloaded = ArchiveStore(archive_dir=archive_dir, sqlite_index=index)
            reloaded_state = _state(reloaded, index)
            assert reloaded_state == {
                "store_document": False,
                "store_chunks": 0,
                "store_hits": 0,
                "index_documents": 0,
                "index_chunks": 0,
            }

            rebuild = index.rebuild_from_jsonl(
                nodes_path="",
                archive_documents_path=reloaded.documents_path,
                archive_chunks_path=reloaded.chunks_path,
            )
            rebuilt = _state(reloaded, index)
            assert rebuild["documents"] == 0
            assert rebuild["chunks"] == 0
            assert rebuilt == {
                "store_document": False,
                "store_chunks": 0,
                "store_hits": 0,
                "index_documents": 0,
                "index_chunks": 0,
            }

            print(json.dumps({
                "before": before,
                "after_delete": deleted,
                "after_reload": reloaded_state,
                "after_rebuild": rebuilt,
                "rebuild_counts": rebuild,
                "documents_jsonl_records": len(documents),
                "chunks_jsonl_records": len(chunks),
                "events_jsonl_types": [event["type"] for event in events],
                "compactor_dry_run": compact_stats,
            }, sort_keys=True))
        finally:
            if reloaded is not None:
                reloaded.close()
            else:
                store.close()
            index.close()


def test_archive_ingest_restart_stays_present() -> None:
    """An ordinary ingested document remains present after a Store restart."""
    with tempfile.TemporaryDirectory(prefix="archive_delete_restart_v1_") as tmp:
        archive_dir = os.path.join(tmp, "memory_archive")
        store = ArchiveStore(archive_dir=archive_dir)
        reloaded = None
        try:
            store.ingest_document(text=TEXT, title=TITLE, doc_id=DOC_ID)
            store.close()
            reloaded = ArchiveStore(archive_dir=archive_dir)

            assert reloaded.get_document(DOC_ID) is not None
            assert len(reloaded.get_chunks_for_document(DOC_ID)) == 1
            assert len(reloaded.retrieve(TEXT, top_k=5, doc_id_filter=DOC_ID)) == 1
        finally:
            if reloaded is not None:
                reloaded.close()
            else:
                store.close()


def test_archive_reingest_same_document_id_reactivates_on_restart() -> None:
    """The final DOCUMENT_INGESTED event reactivates a previously deleted ID."""
    with tempfile.TemporaryDirectory(prefix="archive_delete_restart_v1_") as tmp:
        archive_dir = os.path.join(tmp, "memory_archive")
        store = ArchiveStore(archive_dir=archive_dir)
        reloaded = None
        try:
            store.ingest_document(text=TEXT, title=TITLE, doc_id=DOC_ID)
            assert store.delete_document(DOC_ID) is True
            store.ingest_document(
                text=REINGESTED_TEXT,
                title=TITLE,
                doc_id=DOC_ID,
            )
            store.close()
            reloaded = ArchiveStore(archive_dir=archive_dir)

            assert reloaded.get_document(DOC_ID) is not None
            chunks = reloaded.get_chunks_for_document(DOC_ID)
            assert len(chunks) == 1
            assert chunks[0]["text"] == REINGESTED_TEXT
            assert len(
                reloaded.retrieve(REINGESTED_TEXT, top_k=5, doc_id_filter=DOC_ID)
            ) == 1
        finally:
            if reloaded is not None:
                reloaded.close()
            else:
                store.close()


def test_legacy_archive_records_without_lifecycle_events_remain_present() -> None:
    """Pre-lifecycle JSONL without an event file keeps its legacy active meaning."""
    with tempfile.TemporaryDirectory(prefix="archive_delete_restart_v1_") as tmp:
        archive_dir = os.path.join(tmp, "memory_archive")
        store = ArchiveStore(archive_dir=archive_dir)
        reloaded = None
        try:
            store.close()
            with open(os.path.join(archive_dir, "documents.jsonl"), "w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "doc_id": DOC_ID,
                    "title": TITLE,
                    "source_type": "text",
                    "chunk_count": 1,
                    "token_count": 1,
                    "created_ts": 1,
                    "metadata": {},
                }) + "\n")
            with open(os.path.join(archive_dir, "chunks.jsonl"), "w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "chunk_id": f"{DOC_ID}_chunk_0000",
                    "doc_id": DOC_ID,
                    "chunk_index": 0,
                    "text": TEXT,
                    "token_count": 1,
                    "section_path": [],
                    "section_title": "",
                    "embedding_ref": None,
                    "created_ts": 1,
                }) + "\n")

            reloaded = ArchiveStore(archive_dir=archive_dir)
            assert reloaded.get_document(DOC_ID) is not None
            assert len(reloaded.get_chunks_for_document(DOC_ID)) == 1
        finally:
            if reloaded is not None:
                reloaded.close()
            else:
                store.close()


def test_compactor_preserves_legacy_deleted_marker_support() -> None:
    """A pre-event ``_deleted`` tombstone remains a compactor fallback."""
    with tempfile.TemporaryDirectory(prefix="archive_delete_restart_v1_") as tmp:
        docs_path = os.path.join(tmp, "documents.jsonl")
        with open(docs_path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"doc_id": DOC_ID, "_deleted": True}) + "\n")

        compact_stats, active_doc_ids = compact_documents(docs_path, dry_run=True)
        assert compact_stats["deleted_docs"] == 1
        assert active_doc_ids == set()
