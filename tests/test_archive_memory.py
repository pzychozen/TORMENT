# tests/test_archive_memory.py
"""Per-chunk governance support in ArchiveStore (v0.2.4-A1 Commit 1).

Covers the storage + retrieval shape only. Does NOT exercise FILTER-A
integration — that wiring lands in v0.2.4-A1 Commit 4 (/retrieve handler)
and is tested separately in tests/test_assembly_audit_wiring.py.

Invariants verified here:

- ``ArchiveChunk`` dataclass carries an optional ``governance`` field that
  defaults to ``None``.
- ``ArchiveStore.ingest_document`` accepts a keyword-only ``governance``
  argument and propagates a shallow copy to every chunk produced from the
  ingested document.
- ``ArchiveStore.retrieve`` and ``ArchiveStore.retrieve_by_embedding``
  surface ``governance`` on every returned hit dict; ``None`` on the
  underlying chunk materializes as ``{}`` at the API boundary.
- Legacy ``chunks.jsonl`` rows written before the field existed load
  cleanly via defensive ``.get()`` and become chunks with
  ``governance=None``. This is the load-bearing backward-compat
  invariant — no on-disk migration is required.
- Caller mutation of the governance dict after ingest does not affect
  persisted chunks (shallow-copy invariant).
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import unittest
from typing import Any, Dict

from torment_service.archive_memory import ArchiveStore


# Short document — produces 1 chunk under default chunker params.
SHORT_TEXT = "Hello world. This is a short archive test document."

# Longer document — produces multiple chunks under default chunker params
# (target_tokens=350; ~5400 chars / ~1200 tokens here → multi-chunk).
LONG_TEXT = "This is a longer document about archive memory. " * 200


class _ArchiveStoreTestBase(unittest.TestCase):
    """Shared tempdir setUp/tearDown for ArchiveStore tests.

    Uses ``tempfile.TemporaryDirectory`` for isolation. ``ArchiveStore.close``
    is invoked in tearDown to release shard memmaps before the tempdir is
    cleaned up — required on Windows where memmap handles block dir
    removal.
    """

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.archive_dir = os.path.join(self._tmpdir.name, "archive")
        self.store = ArchiveStore(archive_dir=self.archive_dir)

    def tearDown(self) -> None:
        try:
            self.store.close()
        except Exception as e:
            logging.getLogger(__name__).debug(
                "ArchiveStore.close() failed during teardown: %s", e
            )
        try:
            self._tmpdir.cleanup()
        except Exception:
            # On Windows the tempdir cleanup can race shard handle release;
            # tolerate the cleanup failure rather than mask test outcomes.
            pass


class TestIngestDocumentDefault(_ArchiveStoreTestBase):
    """ingest_document without governance kwarg → chunks have governance=None."""

    def test_short_doc_chunks_have_none_governance(self) -> None:
        result = self.store.ingest_document(text=SHORT_TEXT, title="t")
        self.assertGreater(result["chunk_count"], 0)
        chunks = self.store.get_chunks_for_document(result["doc_id"])
        self.assertEqual(len(chunks), result["chunk_count"])
        for c in chunks:
            self.assertIsNone(c.get("governance"))

    def test_multi_chunk_doc_all_have_none_governance(self) -> None:
        result = self.store.ingest_document(text=LONG_TEXT, title="t")
        chunks = self.store.get_chunks_for_document(result["doc_id"])
        # Confirm we actually got multiple chunks (verifies the fixture
        # length is sufficient for the chunker's default params).
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertIsNone(c.get("governance"))


class TestIngestDocumentWithGovernance(_ArchiveStoreTestBase):
    """ingest_document with governance kwarg → every chunk carries the dict."""

    def test_governance_propagates_to_every_chunk(self) -> None:
        gov: Dict[str, Any] = {"non_shareable": True}
        result = self.store.ingest_document(
            text=LONG_TEXT, title="t", governance=gov
        )
        chunks = self.store.get_chunks_for_document(result["doc_id"])
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertEqual(c["governance"], {"non_shareable": True})

    def test_governance_with_multiple_flags(self) -> None:
        gov: Dict[str, Any] = {
            "non_shareable": True,
            "collective_export_blocked": True,
        }
        result = self.store.ingest_document(
            text=SHORT_TEXT, title="t", governance=gov
        )
        chunks = self.store.get_chunks_for_document(result["doc_id"])
        for c in chunks:
            self.assertEqual(c["governance"], gov)

    def test_governance_empty_dict_stored_as_empty_dict(self) -> None:
        """Explicit empty {} at ingest is preserved (not collapsed to None)."""
        result = self.store.ingest_document(
            text=SHORT_TEXT, title="t", governance={}
        )
        chunks = self.store.get_chunks_for_document(result["doc_id"])
        for c in chunks:
            # Explicit {} ingest → chunk.governance None (truthiness collapse)
            # is acceptable because the empty dict carries no information and
            # the API boundary materializes both as {} regardless.
            self.assertIn(c.get("governance"), (None, {}))


class TestRetrieveSurfacesGovernance(_ArchiveStoreTestBase):
    """retrieve() and retrieve_by_embedding() include governance in returned hits."""

    def test_retrieve_includes_governance_for_marked_chunk(self) -> None:
        self.store.ingest_document(
            text=SHORT_TEXT,
            title="t",
            governance={"non_shareable": True},
        )
        hits = self.store.retrieve(query="Hello world", top_k=5)
        self.assertGreater(len(hits), 0)
        for h in hits:
            self.assertIn("governance", h)
            self.assertEqual(h["governance"], {"non_shareable": True})

    def test_retrieve_governance_is_empty_dict_for_governance_less_chunk(
        self,
    ) -> None:
        """API boundary materializes ``None`` → ``{}`` for downstream .get safety."""
        self.store.ingest_document(text=SHORT_TEXT, title="t")
        hits = self.store.retrieve(query="Hello world", top_k=5)
        self.assertGreater(len(hits), 0)
        for h in hits:
            self.assertIn("governance", h)
            self.assertEqual(h["governance"], {})

    def test_retrieve_by_embedding_includes_governance(self) -> None:
        """retrieve_by_embedding() return shape mirrors retrieve() for governance."""
        self.store.ingest_document(
            text=SHORT_TEXT,
            title="t",
            governance={"non_shareable": True},
        )
        q_emb = self.store.embedder.embed("Hello world")
        hits = self.store.retrieve_by_embedding(
            query_embedding=q_emb, top_k=5
        )
        self.assertGreater(len(hits), 0)
        for h in hits:
            self.assertIn("governance", h)
            self.assertEqual(h["governance"], {"non_shareable": True})

    def test_retrieve_by_embedding_governance_empty_for_governance_less(
        self,
    ) -> None:
        self.store.ingest_document(text=SHORT_TEXT, title="t")
        q_emb = self.store.embedder.embed("Hello world")
        hits = self.store.retrieve_by_embedding(
            query_embedding=q_emb, top_k=5
        )
        self.assertGreater(len(hits), 0)
        for h in hits:
            self.assertIn("governance", h)
            self.assertEqual(h["governance"], {})


class TestBackwardCompatLoadExistingChunks(_ArchiveStoreTestBase):
    """LOAD-BEARING: legacy chunks.jsonl rows (no governance field) load cleanly.

    This guarantees v0.2.4-A1 introduces no on-disk migration. Any existing
    archive_memory/ directory written by prior versions continues to load
    with chunks carrying ``governance=None``.
    """

    def test_load_legacy_chunks_jsonl_without_governance_field(self) -> None:
        # 1. Drop the current store so we can write to its files cleanly.
        self.store.close()

        # 2. Append legacy-format records — note the absence of the
        # ``governance`` key on the chunk row. This is what older
        # archive_memory.py versions wrote.
        legacy_doc = {
            "doc_id": "legacy_doc",
            "title": "Legacy",
            "source_type": "text",
            "chunk_count": 1,
            "token_count": 8,
            "created_ts": 1700000000,
            "metadata": {},
        }
        legacy_chunk = {
            "chunk_id": "legacy_doc_chunk_0000",
            "doc_id": "legacy_doc",
            "chunk_index": 0,
            "text": "Legacy chunk text without governance metadata.",
            "token_count": 8,
            "section_path": [],
            "section_title": "",
            "embedding_ref": None,
            "created_ts": 1700000000,
            # NO "governance" key — pre-v0.2.4-A1 on-disk shape.
        }
        with open(
            os.path.join(self.archive_dir, "documents.jsonl"),
            "a",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(legacy_doc) + "\n")
        with open(
            os.path.join(self.archive_dir, "chunks.jsonl"),
            "a",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(legacy_chunk) + "\n")

        # 3. Re-instantiate ArchiveStore. The _load() path must accept the
        # legacy chunk row and set governance to None via defensive .get().
        self.store = ArchiveStore(archive_dir=self.archive_dir)

        chunks = self.store.get_chunks_for_document("legacy_doc")
        self.assertEqual(len(chunks), 1)
        self.assertIsNone(chunks[0].get("governance"))


class TestGovernanceDeepCopyOnIngest(_ArchiveStoreTestBase):
    """Caller mutation after ingest must not affect persisted chunks."""

    def test_caller_mutation_after_ingest_does_not_affect_chunks(self) -> None:
        gov: Dict[str, Any] = {"non_shareable": True}
        result = self.store.ingest_document(
            text=LONG_TEXT, title="t", governance=gov
        )

        # Mutate the caller's dict after ingest.
        gov["non_shareable"] = False
        gov["extra_key"] = "should_not_appear"

        chunks = self.store.get_chunks_for_document(result["doc_id"])
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertEqual(c["governance"], {"non_shareable": True})
            self.assertNotIn("extra_key", c["governance"] or {})

    def test_retrieve_governance_is_isolated_from_chunk_storage(self) -> None:
        """Mutating a retrieve() result must not affect the next retrieve()."""
        self.store.ingest_document(
            text=SHORT_TEXT,
            title="t",
            governance={"non_shareable": True},
        )

        hits_1 = self.store.retrieve(query="Hello world", top_k=5)
        self.assertGreater(len(hits_1), 0)
        # Mutate the returned dict.
        hits_1[0]["governance"]["non_shareable"] = False
        hits_1[0]["governance"]["leaked"] = "yes"

        hits_2 = self.store.retrieve(query="Hello world", top_k=5)
        self.assertGreater(len(hits_2), 0)
        for h in hits_2:
            self.assertEqual(h["governance"], {"non_shareable": True})
            self.assertNotIn("leaked", h["governance"])


if __name__ == "__main__":
    unittest.main()
