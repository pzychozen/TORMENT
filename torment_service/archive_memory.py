# torment_service/archive_memory.py
"""
Archive memory lane for TORMENT.

This is the SECOND lane — separate from core identity memory.
Archive stores document chunks for retrieval, NOT for identity formation.

=== BOUNDARY RULE ===
Archive memory NEVER:
  - Enters the TriOcta kernel
  - Creates motifs in the core motif registry
  - Affects drift scores or character state
  - Gets treated as episodic or relational memory
  - Participates in coherence field calculations
  - Influences seed gravity or identity basins

Archive memory ONLY:
  - Stores document chunks with embeddings
  - Responds to cosine-similarity retrieval queries
  - Lives in its own folder (memory_archive/)
  - Uses its own embedding shards (separate from core)
  - Can be deleted without affecting identity

Promotion from archive → core is EXPLICIT and requires Phase 5.
=== END BOUNDARY RULE ===
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .chunking import chunk_text
from .embedding_store import EmbeddingShardWriter, EmbeddingShardReader
from .embeddings import Embedder, HashEmbedding


# Logger
log = logging.getLogger("torment.archive_memory")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ARCHIVE_MEMORY_CLASS = "archive"  # Never changes. Never "core".


def _now_ts() -> int:
    return int(time.time())


def _ensure_within_base(path: str, base_dir: str) -> str:
    """Resolve *path* and verify it lives inside *base_dir* (CWE-22 guard)."""
    base = os.path.realpath(base_dir)
    resolved = os.path.realpath(path)
    if resolved != base and not resolved.startswith(base + os.sep):
        raise ValueError("Path escapes base directory")
    return resolved


def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v) + 1e-12)
    return (v / n).astype(np.float32)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class ArchiveDocument:
    """Metadata for a source document."""
    doc_id: str
    title: str
    source_type: str          # "markdown", "text", "pdf", "html"
    chunk_count: int = 0
    token_count: int = 0
    created_ts: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchiveChunk:
    """A single chunk stored in the archive."""
    chunk_id: str
    doc_id: str
    chunk_index: int
    text: str
    token_count: int
    section_path: List[str]
    section_title: str
    embedding_ref: Optional[Dict[str, Any]] = None
    created_ts: int = 0
    # v0.2.4-A1: per-chunk governance metadata (FILTER-A defense-in-depth).
    # None for chunks ingested before v0.2.4 or without explicit governance;
    # the /retrieve archive filter wiring (separate slice) treats None as
    # default-pass per v0.2.4-A0 ratified default-policy. Per-document
    # governance at ingest is copied into every chunk; per-chunk override
    # is future scope.
    governance: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# ArchiveStore
# ---------------------------------------------------------------------------
class ArchiveStore:
    """Manages archive memory for one agent.

    Completely separate from core memory — own folder, own shards, own JSONL.
    """

    def __init__(
        self,
        archive_dir: str,
        embedder: Optional[Embedder] = None,
        sqlite_index=None,
    ) -> None:
        self.archive_dir = os.path.realpath(archive_dir)
        self.embedder = embedder or HashEmbedding()
        # Optional SQLite sidecar index (Phase 4).
        # Mirror writes go to SQLite after JSONL. Failure is non-fatal.
        self._sqlite_index = sqlite_index
        self._emb_dim = int(getattr(self.embedder, "dim", 0) or 0) or 384

        os.makedirs(self.archive_dir, exist_ok=True)

        # File paths
        self.documents_path = _ensure_within_base(
            os.path.join(self.archive_dir, "documents.jsonl"),
            self.archive_dir,
        )
        self.chunks_path = _ensure_within_base(
            os.path.join(self.archive_dir, "chunks.jsonl"),
            self.archive_dir,
        )
        self.events_path = _ensure_within_base(
            os.path.join(self.archive_dir, "events.jsonl"),
            self.archive_dir,
        )

        # Embedding storage — separate shard directory from core
        self._emb_dir = _ensure_within_base(
            os.path.join(self.archive_dir, "embeddings"),
            self.archive_dir,
        )
        self._shard_writer: Optional[EmbeddingShardWriter] = None
        self._shard_reader: Optional[EmbeddingShardReader] = None
        self._init_shard_storage()

        # In-memory indexes for fast retrieval
        self._documents: Dict[str, ArchiveDocument] = {}
        self._chunks: Dict[str, ArchiveChunk] = {}
        self._chunk_embeddings: Dict[str, np.ndarray] = {}  # chunk_id → unit vector

        self._load()

    def _init_shard_storage(self) -> None:
        try:
            self._shard_writer = EmbeddingShardWriter(self._emb_dir, dim=self._emb_dim)
            self._shard_reader = EmbeddingShardReader(self._emb_dir)
        except Exception:
            self._shard_writer = None
            self._shard_reader = None

    # ----------------------------
    # Persistence
    # ----------------------------

    def _append_jsonl(self, path: str, obj: Dict[str, Any]) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _load(self) -> None:
        """Load documents and chunks from JSONL."""
        # Documents
        if os.path.exists(self.documents_path):
            with open(self.documents_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        doc = ArchiveDocument(
                            doc_id=obj["doc_id"],
                            title=obj.get("title", ""),
                            source_type=obj.get("source_type", "text"),
                            chunk_count=int(obj.get("chunk_count", 0)),
                            token_count=int(obj.get("token_count", 0)),
                            created_ts=int(obj.get("created_ts", 0)),
                            metadata=obj.get("metadata", {}),
                        )
                        self._documents[doc.doc_id] = doc
                    except (json.JSONDecodeError, KeyError):
                        continue

        # Chunks
        if os.path.exists(self.chunks_path):
            with open(self.chunks_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        chunk = ArchiveChunk(
                            chunk_id=obj["chunk_id"],
                            doc_id=obj["doc_id"],
                            chunk_index=int(obj.get("chunk_index", 0)),
                            text=obj.get("text", ""),
                            token_count=int(obj.get("token_count", 0)),
                            section_path=obj.get("section_path", []),
                            section_title=obj.get("section_title", ""),
                            embedding_ref=obj.get("embedding_ref"),
                            created_ts=int(obj.get("created_ts", 0)),
                            # v0.2.4-A1: defensive .get() returns None for
                            # legacy chunks written before the field existed.
                            # Load-bearing for backward compat with on-disk
                            # chunks.jsonl files; no migration required.
                            governance=obj.get("governance"),
                        )
                        self._chunks[chunk.chunk_id] = chunk

                        # Load embedding into RAM for search
                        if chunk.embedding_ref and self._shard_reader:
                            vec = self._shard_reader.load_one(chunk.embedding_ref)
                            if vec is not None:
                                self._chunk_embeddings[chunk.chunk_id] = _unit(vec)
                    except (json.JSONDecodeError, KeyError):
                        continue

    # ----------------------------
    # Document ingestion
    # ----------------------------

    def ingest_document(
        self,
        text: str,
        title: str = "Untitled",
        source_type: str = "text",
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        target_tokens: int = 350,
        max_tokens: int = 500,
        overlap_tokens: int = 60,
        governance: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Ingest a document into archive memory.

        Chunks the text, embeds each chunk, stores in archive shards.
        NEVER touches core memory, motifs, or identity.

        Args:
            text: Full document text
            title: Document title
            source_type: "markdown", "text", "pdf", etc.
            doc_id: Optional explicit ID (auto-generated if None)
            metadata: Optional metadata dict
            governance: Optional per-document governance dict applied to
                every chunk produced from this document (v0.2.4-A1).
                Keys are FILTER-A governance flags such as
                ``non_shareable`` and ``collective_export_blocked``.
                A shallow copy is stored on each ArchiveChunk so caller
                mutations after ingest do not affect persisted chunks.
                Default ``None`` matches legacy behavior: chunks load
                with ``governance=None`` and the archive filter wiring
                (separate slice) treats them as default-pass per
                v0.2.4-A0.

        Returns:
            {"doc_id": str, "chunk_count": int, "token_count": int}
        """
        text = (text or "").strip()
        if not text:
            return {"doc_id": "", "chunk_count": 0, "token_count": 0}

        # Generate doc_id
        if not doc_id:
            safe_title = "".join(c if c.isalnum() else "_" for c in title[:30]).lower()
            doc_id = f"doc_{safe_title}_{_now_ts()}"

        # Chunk the text
        chunks = chunk_text(
            text,
            target_tokens=target_tokens,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        )

        if not chunks:
            return {"doc_id": doc_id, "chunk_count": 0, "token_count": 0}

        total_tokens = sum(c.token_count for c in chunks)

        # Write document record
        doc = ArchiveDocument(
            doc_id=doc_id,
            title=title,
            source_type=source_type,
            chunk_count=len(chunks),
            token_count=total_tokens,
            created_ts=_now_ts(),
            metadata=metadata or {},
        )
        self._documents[doc_id] = doc
        self._append_jsonl(self.documents_path, asdict(doc))
        # Mirror to SQLite sidecar (Phase 4) — failure is non-fatal
        if self._sqlite_index:
            try:
                self._sqlite_index.index_document(asdict(doc))
            except Exception as e:
                log.debug("SQLite index_document skipped: %s", e)

        # Process each chunk: embed + store
        for tc in chunks:
            chunk_id = f"{doc_id}_chunk_{tc.chunk_index:04d}"

            # Embed the chunk
            emb = np.asarray(self.embedder.embed(tc.text), dtype=np.float32)

            # Write to archive shard (NOT core shard)
            emb_ref = None
            if self._shard_writer:
                try:
                    emb_ref = self._shard_writer.append(
                        emb,
                        eid=tc.chunk_index,  # chunk index as eid for shard
                        memory_class=ARCHIVE_MEMORY_CLASS,  # Always "archive"
                        kind="document_chunk",
                        step=0,
                        extra_meta={"doc_id": doc_id, "chunk_id": chunk_id},
                    )
                except Exception as e:
                    log.debug("Shard write skipped: %s", e)
                    emb_ref = None

            chunk = ArchiveChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                chunk_index=tc.chunk_index,
                text=tc.text,
                token_count=tc.token_count,
                section_path=tc.section_path,
                section_title=tc.section_title,
                embedding_ref=emb_ref,
                created_ts=_now_ts(),
                # v0.2.4-A1: shallow-copy doc-wide governance into each
                # chunk so caller mutation after ingest does not affect
                # stored state. Governance flags are flat booleans;
                # shallow copy is sufficient.
                governance=dict(governance) if governance else None,
            )
            self._chunks[chunk_id] = chunk
            self._append_jsonl(self.chunks_path, asdict(chunk))
            # Mirror to SQLite sidecar (Phase 4) — failure is non-fatal
            if self._sqlite_index:
                try:
                    self._sqlite_index.index_chunk(asdict(chunk))
                except Exception as e:
                    log.debug("SQLite index_chunk skipped: %s", e)

            # Cache embedding for search
            self._chunk_embeddings[chunk_id] = _unit(emb)

        # Log event
        self._append_jsonl(self.events_path, {
            "type": "DOCUMENT_INGESTED",
            "ts": _now_ts(),
            "doc_id": doc_id,
            "title": title,
            "source_type": source_type,
            "chunk_count": len(chunks),
            "token_count": total_tokens,
        })

        return {
            "doc_id": doc_id,
            "chunk_count": len(chunks),
            "token_count": total_tokens,
        }

    # ----------------------------
    # Retrieval (pure cosine, NO physics)
    # ----------------------------

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        min_score: float = 0.0,
        doc_id_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve archive chunks by cosine similarity.

        This is PURE cosine retrieval — no motifs, no gravity, no drift,
        no kernel physics. Archive memory is a library, not a person.

        Args:
            query: Search query text
            top_k: Maximum results
            min_score: Minimum cosine similarity threshold
            doc_id_filter: Optional — only search within this document

        Returns:
            List of dicts with chunk info + similarity score.
        """
        query = (query or "").strip()
        if not query or not self._chunk_embeddings:
            return []

        q_emb = _unit(np.asarray(self.embedder.embed(query), dtype=np.float32))

        # Score all chunks
        scored: List[Tuple[str, float]] = []
        for chunk_id, emb in self._chunk_embeddings.items():
            if doc_id_filter:
                chunk = self._chunks.get(chunk_id)
                if chunk and chunk.doc_id != doc_id_filter:
                    continue
            sim = float(np.dot(q_emb, emb))
            if sim >= min_score:
                scored.append((chunk_id, sim))

        scored.sort(key=lambda t: t[1], reverse=True)
        scored = scored[:top_k]

        results: List[Dict[str, Any]] = []
        for chunk_id, sim in scored:
            chunk = self._chunks.get(chunk_id)
            if not chunk:
                continue
            doc = self._documents.get(chunk.doc_id)
            results.append({
                "chunk_id": chunk_id,
                "doc_id": chunk.doc_id,
                "doc_title": doc.title if doc else "",
                "text": chunk.text,
                "token_count": chunk.token_count,
                "section_path": chunk.section_path,
                "section_title": chunk.section_title,
                "score": float(sim),
                "memory_class": ARCHIVE_MEMORY_CLASS,  # Always. Never "core".
                # v0.2.4-A1: per-chunk governance surfaced at API boundary.
                # None on the dataclass materializes as {} here so callers
                # can use .get(...) safely without None-checking.
                "governance": dict(chunk.governance or {}),
            })

        return results

    def retrieve_by_embedding(
        self,
        query_embedding: np.ndarray,
        *,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Retrieve by pre-computed embedding vector."""
        if not self._chunk_embeddings:
            return []

        q = _unit(query_embedding)
        scored: List[Tuple[str, float]] = []
        for chunk_id, emb in self._chunk_embeddings.items():
            sim = float(np.dot(q, emb))
            if sim >= min_score:
                scored.append((chunk_id, sim))

        scored.sort(key=lambda t: t[1], reverse=True)
        scored = scored[:top_k]

        results: List[Dict[str, Any]] = []
        for chunk_id, sim in scored:
            chunk = self._chunks.get(chunk_id)
            if not chunk:
                continue
            doc = self._documents.get(chunk.doc_id)
            results.append({
                "chunk_id": chunk_id,
                "doc_id": chunk.doc_id,
                "doc_title": doc.title if doc else "",
                "text": chunk.text,
                "token_count": chunk.token_count,
                "section_path": chunk.section_path,
                "score": float(sim),
                "memory_class": ARCHIVE_MEMORY_CLASS,
                # v0.2.4-A1: per-chunk governance surfaced at API boundary.
                # Mirrors retrieve() shape so callers get the same dict
                # structure regardless of which retrieval entry point is
                # used. None on dataclass materializes as {} here.
                "governance": dict(chunk.governance or {}),
            })

        return results

    # ----------------------------
    # Info
    # ----------------------------

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all ingested documents."""
        return [asdict(d) for d in self._documents.values()]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID."""
        doc = self._documents.get(doc_id)
        return asdict(doc) if doc else None

    def get_chunks_for_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document, ordered by index."""
        chunks = [
            asdict(c) for c in self._chunks.values()
            if c.doc_id == doc_id
        ]
        chunks.sort(key=lambda c: c.get("chunk_index", 0))
        return chunks

    def delete_document(self, doc_id: str) -> bool:
        """Remove a document and its chunks from the archive.

        This is safe — archive deletion never affects core memory.
        Note: This removes from in-memory indexes. JSONL files retain
        the records (append-only), but they won't be loaded on restart
        once we add a deletion marker.
        """
        if doc_id not in self._documents:
            return False

        # Remove chunks
        chunk_ids = [
            cid for cid, c in self._chunks.items()
            if c.doc_id == doc_id
        ]
        for cid in chunk_ids:
            self._chunks.pop(cid, None)
            self._chunk_embeddings.pop(cid, None)

        # Remove document
        self._documents.pop(doc_id, None)

        # Log deletion event
        self._append_jsonl(self.events_path, {
            "type": "DOCUMENT_DELETED",
            "ts": _now_ts(),
            "doc_id": doc_id,
            "chunks_removed": len(chunk_ids),
        })

        # Mirror deletion to SQLite sidecar (Phase 4)
        if self._sqlite_index:
            try:
                self._sqlite_index.delete_document_index(doc_id)
            except Exception as e:
                log.debug("SQLite delete_document_index skipped: %s", e)

        return True

    @property
    def document_count(self) -> int:
        return len(self._documents)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def close(self) -> None:
        """Release shard memmaps held by this archive. Idempotent.

        Required on Windows before the data directory can be removed:
        numpy memmap objects in the embedding shard writer/reader hold
        OS file handles open until explicitly released.
        """
        if self._shard_writer is not None:
            self._shard_writer.close()
        if self._shard_reader is not None:
            self._shard_reader.close()

    def __enter__(self) -> "ArchiveStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
