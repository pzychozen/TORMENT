# torment_service/deep_memory.py
"""
Deep memory store for TORMENT — long-path compressed memories.

Per-agent store for memories exported via event-gated compression.
These memories can "return like spirits" — recalled when core + archive
search returns insufficient results, or individually by EID for future
Kernel B consumption.

Storage layout:
    data/agents/{agent_id}/deep_memory/
        memories.jsonl       — compressed memory records (append-only)
        embeddings/          — shard storage (reuses EmbeddingShardWriter)
        manifest.json        — shard manifest
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# Reuse path hardening and shard infrastructure from embedding_store
from .embedding_store import (
    EmbeddingShardWriter,
    EmbeddingShardReader,
    DEFAULT_DIM,
    _child_path,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DeepMemory:
    """A compressed memory record in the deep store."""
    eid: int                            # original entity ID
    born_step: int                      # when originally created
    compressed_step: int                # when compressed
    summary: str                        # original or distilled summary
    compression_score: float = 0.0
    original_motif_id: Optional[str] = None
    memory_class: str = "core"
    embedding_ref: Optional[Dict[str, Any]] = None   # shard:row reference
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Ensure embedding_ref is serializable
        if d.get("embedding_ref") is not None:
            d["embedding_ref"] = dict(d["embedding_ref"])
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "DeepMemory":
        return cls(
            eid=int(d.get("eid", 0)),
            born_step=int(d.get("born_step", 0) or 0),
            compressed_step=int(d.get("compressed_step", 0) or 0),
            summary=str(d.get("summary", "") or ""),
            compression_score=float(d.get("compression_score", 0.0) or 0.0),
            original_motif_id=d.get("original_motif_id"),
            memory_class=str(d.get("memory_class", "core") or "core"),
            embedding_ref=d.get("embedding_ref"),
            metadata=dict(d.get("metadata", {}) or {}),
        )


# ---------------------------------------------------------------------------
# DeepMemoryStore
# ---------------------------------------------------------------------------

class DeepMemoryStore:
    """Per-agent deep memory store for long-path compressed memories.

    Provides:
      - export(): write compressed memory + embedding
      - query(): cosine similarity search over deep memories
      - recall(): retrieve specific memory by original EID
      - stats(): store statistics
    """

    def __init__(
        self,
        base_dir: Path,
        dim: int = DEFAULT_DIM,
        *,
        trusted_root: str = "",
    ) -> None:
        canonical_root = os.path.realpath(str(base_dir))

        # ---- sink-local containment guard --------------------------------
        # CodeQL requires an *inline* ``startswith(… + os.sep)`` before every
        # filesystem sink so the taint tracker can verify the path stays
        # inside a trusted directory.  When the caller supplies a
        # ``trusted_root`` (the canonical data-dir), we verify containment;
        # otherwise we fall back to an absolute-path assertion.
        if trusted_root:
            _trust = os.path.realpath(trusted_root)
            if canonical_root != _trust and not canonical_root.startswith(
                _trust + os.sep
            ):
                raise ValueError(
                    f"base_dir escapes trusted root: {canonical_root!r}"
                )
        if not canonical_root.startswith(os.sep) and not os.path.isabs(
            canonical_root
        ):
            raise ValueError(f"base_dir not absolute: {canonical_root!r}")
        # ------------------------------------------------------------------

        os.makedirs(canonical_root, exist_ok=True)
        self.base_dir = Path(canonical_root)

        self.memories_path = Path(_child_path(canonical_root, "memories.jsonl"))
        self.emb_dir = _child_path(canonical_root, "embeddings")
        self.dim = int(dim)

        # Initialize shard storage
        self._shard_writer: Optional[EmbeddingShardWriter] = None
        self._shard_reader: Optional[EmbeddingShardReader] = None
        self._init_shards()

        # In-memory index (loaded on first access)
        self._memories: Optional[List[DeepMemory]] = None
        self._eid_index: Optional[Dict[int, int]] = None  # eid → list index
        self._emb_mat: Optional[np.ndarray] = None
        self._emb_eid_list: Optional[List[int]] = None

    def _init_shards(self) -> None:
        """Initialize embedding shard writer and reader."""
        try:
            os.makedirs(self.emb_dir, exist_ok=True)
            self._shard_writer = EmbeddingShardWriter(self.emb_dir, dim=self.dim)
            self._shard_reader = EmbeddingShardReader(self.emb_dir)
        except Exception as exc:
            logger.warning("deep memory shard init failed: %s", exc)

    # -------------------------------------------------------------------
    # Load
    # -------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Load memories from disk if not already loaded."""
        if self._memories is not None:
            return

        self._memories = []
        self._eid_index = {}

        if self.memories_path.exists():
            try:
                with open(self.memories_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            mem = DeepMemory.from_dict(d)
                            self._memories.append(mem)
                            self._eid_index[mem.eid] = i
                        except Exception:
                            continue
            except Exception as exc:
                logger.warning("failed to load deep memories: %s", exc)

    def _invalidate_emb_cache(self) -> None:
        """Invalidate embedding matrix cache after export."""
        self._emb_mat = None
        self._emb_eid_list = None

    # -------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------

    def export(
        self,
        candidate,  # CompressionCandidate
        embedding: Optional[np.ndarray],
        original_payload: dict,
    ) -> DeepMemory:
        """Write compressed memory to deep store.

        Args:
            candidate: CompressionCandidate with scoring info
            embedding: optional embedding vector (384-dim float32)
            original_payload: original node payload dict (preserved fields)

        Returns:
            DeepMemory record
        """
        self._ensure_loaded()

        # Store embedding if available
        emb_ref = None
        if embedding is not None and self._shard_writer is not None:
            try:
                emb_vec = np.asarray(embedding, dtype=np.float32).reshape(-1)
                emb_ref = self._shard_writer.append(
                    emb_vec,
                    eid=candidate.eid,
                    memory_class=candidate.memory_class,
                    kind="deep_compressed",
                    step=candidate.born_step,
                )
            except Exception as exc:
                logger.warning("deep memory embedding write failed: %s", exc)

        # Build metadata from original payload (preserve useful fields)
        metadata_keys = [
            "type", "kind", "tier", "affect_tag", "state_symbol",
            "resonance_score", "transition_entropy", "in_corridor",
            "survival_steps", "tearing_risk", "user_id",
            "workspace_id", "domain_id", "agent_id",
            # Spirit return: preserve symbolic trace for birth-symbol matching
            "symbol_trace", "loop_type", "phase_shift",
            "dominant_transition", "affect_conf",
            "symbol_confidence", "symbol_reason", "half_life",
            # Phase-cycle duration for spirit return warmth boost
            "phase_duration_steps", "corridor_duration_steps",
            # Q3-D1-S4: preserve the source row's affect-VALUE lineage snapshot
            # (affect_attribution) verbatim, so a retrieval echo carries the
            # original producer envelope (inferred / derived) instead of
            # synthesizing a recovered/migration/legacy_read_fallback on read.
            # Copied unchanged; never re-synthesized, validated-rewritten, or
            # overwritten here. The echo's non-authoritative posture lives in
            # authority_status (authoritative=false / requires_rehydration=true /
            # role=retrieval_echo), an orthogonal axis — not in this field.
            "affect_attribution",
        ]
        metadata = {k: original_payload[k] for k in metadata_keys if k in original_payload}

        mem = DeepMemory(
            eid=candidate.eid,
            born_step=candidate.born_step,
            compressed_step=int(time.time()),  # approximate; caller can override
            summary=candidate.summary,
            compression_score=candidate.score,
            original_motif_id=candidate.motif_id,
            memory_class=candidate.memory_class,
            embedding_ref=emb_ref,
            metadata=metadata,
        )

        # Append to JSONL
        try:
            with open(self.memories_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(mem.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error("failed to write deep memory: %s", exc)
            raise

        # Update in-memory index
        assert self._memories is not None
        self._eid_index[mem.eid] = len(self._memories)  # type: ignore
        self._memories.append(mem)
        self._invalidate_emb_cache()

        return mem

    # -------------------------------------------------------------------
    # Query
    # -------------------------------------------------------------------

    def _build_emb_matrix(self) -> None:
        """Build cosine-search matrix from shard reader."""
        self._ensure_loaded()
        assert self._memories is not None

        vecs: List[np.ndarray] = []
        eids: List[int] = []

        for mem in self._memories:
            if mem.embedding_ref is None or self._shard_reader is None:
                continue
            try:
                vec = self._shard_reader.load_one(mem.embedding_ref)
                if vec is not None:
                    v = np.asarray(vec, dtype=np.float32).reshape(-1)
                    norm = float(np.linalg.norm(v) + 1e-12)
                    vecs.append(v / norm)
                    eids.append(mem.eid)
            except Exception:
                continue

        if vecs:
            self._emb_mat = np.stack(vecs, axis=0)
        else:
            self._emb_mat = np.zeros((0, self.dim), dtype=np.float32)
        self._emb_eid_list = eids

    def query(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
        min_similarity: float = 0.4,
    ) -> List[DeepMemory]:
        """Cosine similarity search over deep memory embeddings.

        Args:
            embedding: query embedding (384-dim)
            top_k: max results
            min_similarity: minimum cosine similarity threshold

        Returns:
            List of DeepMemory sorted by similarity (highest first)
        """
        if self._emb_mat is None:
            self._build_emb_matrix()

        assert self._emb_mat is not None
        assert self._emb_eid_list is not None

        if self._emb_mat.shape[0] == 0:
            return []

        # Normalize query
        qv = np.asarray(embedding, dtype=np.float32).reshape(-1)
        norm = float(np.linalg.norm(qv) + 1e-12)
        qv = qv / norm

        # Handle dim mismatch
        if qv.shape[0] != self._emb_mat.shape[1]:
            dim = self._emb_mat.shape[1]
            if qv.shape[0] < dim:
                qv = np.pad(qv, (0, dim - qv.shape[0]))
            else:
                qv = qv[:dim]

        # Cosine similarity
        scores = self._emb_mat @ qv
        k = min(int(top_k), len(scores))

        if k <= 0:
            return []

        if len(scores) <= k:
            order = np.argsort(-scores)
        else:
            idx = np.argpartition(-scores, k - 1)[:k]
            order = idx[np.argsort(-scores[idx])]

        self._ensure_loaded()
        assert self._memories is not None
        assert self._eid_index is not None

        results: List[DeepMemory] = []
        for i in order[:k]:
            sc = float(scores[int(i)])
            if sc < min_similarity:
                continue
            eid = self._emb_eid_list[int(i)]
            idx_in_list = self._eid_index.get(eid)
            if idx_in_list is not None and idx_in_list < len(self._memories):
                results.append(self._memories[idx_in_list])

        return results

    # -------------------------------------------------------------------
    # Recall
    # -------------------------------------------------------------------

    def recall(self, eid: int) -> Optional[DeepMemory]:
        """Retrieve a specific deep memory by original EID.

        For future "spirit return" — bringing memories back to core.
        """
        self._ensure_loaded()
        assert self._eid_index is not None
        assert self._memories is not None

        idx = self._eid_index.get(int(eid))
        if idx is not None and idx < len(self._memories):
            return self._memories[idx]
        return None

    # -------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Return store statistics."""
        self._ensure_loaded()
        assert self._memories is not None

        count = len(self._memories)
        if count == 0:
            return {
                "count": 0,
                "oldest_born_step": None,
                "newest_born_step": None,
                "has_embeddings": False,
            }

        born_steps = [m.born_step for m in self._memories]
        has_emb = any(m.embedding_ref is not None for m in self._memories)

        return {
            "count": count,
            "oldest_born_step": min(born_steps),
            "newest_born_step": max(born_steps),
            "has_embeddings": has_emb,
            "memory_classes": list(set(m.memory_class for m in self._memories)),
        }

    def close(self) -> None:
        """Release shard memmaps held by this store. Idempotent.

        Required on Windows before the backing directory can be
        removed (rmtree / TemporaryDirectory cleanup): numpy memmap
        objects hold the underlying file handles open until released.
        """
        if self._shard_writer is not None:
            self._shard_writer.close()
        if self._shard_reader is not None:
            self._shard_reader.close()

    def __enter__(self) -> "DeepMemoryStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
