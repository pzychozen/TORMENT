# torment_service/embedding_store.py
"""
Embedding shard storage for TORMENT memory system.

Replaces per-memory emb_<eid>.npy files with consolidated shard matrices.
Each shard holds up to ROWS_PER_SHARD embeddings in a single .npy file,
with a companion .map.jsonl for metadata.

Canonical layout:
    embeddings/
        manifest.json
        shard_000000.npy          # shape (ROWS_PER_SHARD, dim), float32
        shard_000000.map.jsonl    # one JSON line per row
        shard_000001.npy
        shard_000001.map.jsonl
        ...

Design rule: The engine defines the memory objects. Storage mirrors them.
Databases do not define the ontology.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ROWS_PER_SHARD = 4096
MANIFEST_VERSION = 1
DEFAULT_DIM = 384
DEFAULT_DTYPE = "float32"


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
def _default_manifest(dim: int = DEFAULT_DIM) -> Dict[str, Any]:
    return {
        "version": MANIFEST_VERSION,
        "embedding_dim": int(dim),
        "dtype": DEFAULT_DTYPE,
        "rows_per_shard": ROWS_PER_SHARD,
        "active_shard": 0,
        "next_row": 0,
        "total_rows": 0,
    }


def _shard_name(idx: int) -> str:
    return f"shard_{idx:06d}"


# ---------------------------------------------------------------------------
# Backward-compatible wrappers around the centralised pathing module.
# Existing callers that import from embedding_store continue to work.
# New code should import from torment_service.pathing directly.
# ---------------------------------------------------------------------------
from .pathing import ensure_within_base as _ensure_within_base   # noqa: F401
from .pathing import stable_filename as _stable_filename


def _child_path(root: str, filename: str) -> str:
    """Derive a child file path from a canonical root, with traversal check.

    Thin wrapper around ``pathing.stable_filename`` that preserves the
    original ``_child_path(root, filename)`` call signature used by
    every module that imports from ``embedding_store``.

    ``filename`` must be a simple name (no separators, no '..').
    """
    return _stable_filename(root, filename)


def _canonical_storage_root(path: str) -> str:
    """Canonicalize a storage root path — thin wrapper kept for compat.

    New code should use ``pathing.safe_join`` or ``pathing.approved_subdir``
    instead, which combine canonicalization with base-containment in one call.
    """
    root = os.path.realpath(path)
    if ".." not in root.split(os.sep):
        return root
    raise ValueError(f"Canonical path contains traversal segment: {root!r}")


# ---------------------------------------------------------------------------
# EmbeddingShardWriter
# ---------------------------------------------------------------------------
class EmbeddingShardWriter:
    """Append embeddings to shard storage.

    Each call to ``append()`` writes one embedding vector and returns
    an ``embedding_ref`` dict that the caller stores in the node payload.
    """

    def _guard(self, path: str) -> str:
        """Inline containment check — keeps CodeQL taint-chain visible at every sink."""
        rp = os.path.realpath(path)
        base = os.path.realpath(self.embeddings_dir)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes storage root: {rp!r}")
        return rp

    def __init__(self, embeddings_dir: str, dim: int = DEFAULT_DIM) -> None:
        self.embeddings_dir = _canonical_storage_root(embeddings_dir)
        os.makedirs(self.embeddings_dir, exist_ok=True)
        self.dim = int(dim)

        self.manifest_path = _child_path(self.embeddings_dir, "manifest.json")
        self.manifest = self._load_or_create_manifest()

        # Ensure dim consistency
        if self.manifest["embedding_dim"] != self.dim:
            # First write sets the dim; subsequent must match
            if self.manifest["total_rows"] == 0:
                self.manifest["embedding_dim"] = self.dim
                self._save_manifest()
            else:
                raise ValueError(
                    f"Manifest dim={self.manifest['embedding_dim']} != requested dim={self.dim}"
                )

        # Pre-load or create the active shard memmap
        self._active_mmap: Optional[np.memmap] = None
        self._ensure_active_shard()

    # ---- manifest ----

    def _load_or_create_manifest(self) -> Dict[str, Any]:
        safe = self._guard(self.manifest_path)
        if os.path.exists(safe):
            with open(safe, "r", encoding="utf-8") as f:
                return json.load(f)
        m = _default_manifest(self.dim)
        self._write_json(self.manifest_path, m)
        return m

    def _save_manifest(self) -> None:
        self._write_json(self.manifest_path, self.manifest)

    def _write_json(self, path: str, obj: Dict[str, Any]) -> None:
        """Atomically write JSON, verifying both target and temp stay inside storage root."""
        safe_path = _ensure_within_base(path, self.embeddings_dir)
        tmp = safe_path + ".tmp"
        _ensure_within_base(tmp, self.embeddings_dir)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        os.replace(tmp, safe_path)

    # ---- shard management ----

    def _shard_npy_path(self, idx: int) -> str:
        return _child_path(self.embeddings_dir, _shard_name(idx) + ".npy")

    def _shard_map_path(self, idx: int) -> str:
        return _child_path(self.embeddings_dir, _shard_name(idx) + ".map.jsonl")

    def _ensure_active_shard(self) -> None:
        """Create or open the active shard memmap."""
        idx = self.manifest["active_shard"]
        npy_path = self._shard_npy_path(idx)
        rows = self.manifest["rows_per_shard"]
        dim = self.manifest["embedding_dim"]

        safe_npy = self._guard(npy_path)
        if not os.path.exists(safe_npy):
            # Create a zeroed shard file
            arr = np.zeros((rows, dim), dtype=np.float32)
            np.save(safe_npy, arr)

        # Open as memmap for efficient partial writes
        self._active_mmap = np.load(safe_npy, mmap_mode="r+")

    def _rotate_shard(self) -> None:
        """Move to the next shard when current is full."""
        self._active_mmap = None
        self.manifest["active_shard"] += 1
        self.manifest["next_row"] = 0
        self._save_manifest()
        self._ensure_active_shard()

    # ---- public API ----

    def append(
        self,
        embedding: np.ndarray,
        eid: int,
        memory_class: str = "core",
        kind: str = "episode",
        step: int = 0,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append one embedding to the active shard.

        Returns an ``embedding_ref`` dict:
            {"shard": int, "row": int, "dim": int}
        """
        vec = np.asarray(embedding, dtype=np.float32).reshape(-1)
        if vec.shape[0] != self.dim:
            # Pad or truncate to match expected dim
            if vec.shape[0] < self.dim:
                vec = np.pad(vec, (0, self.dim - vec.shape[0]))
            else:
                vec = vec[: self.dim]

        shard_idx = self.manifest["active_shard"]
        row = self.manifest["next_row"]

        # Check if we need to rotate
        if row >= self.manifest["rows_per_shard"]:
            self._rotate_shard()
            shard_idx = self.manifest["active_shard"]
            row = self.manifest["next_row"]

        # Write embedding to memmap
        self._active_mmap[row] = vec
        self._active_mmap.flush()

        # Write map entry
        map_entry = {
            "row": row,
            "eid": int(eid),
            "memory_class": str(memory_class),
            "kind": str(kind),
            "step": int(step),
            "ts": int(time.time()),
        }
        if extra_meta:
            map_entry.update(extra_meta)

        map_path = self._guard(self._shard_map_path(shard_idx))
        with open(map_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(map_entry, ensure_ascii=False) + "\n")

        # Update manifest
        self.manifest["next_row"] = row + 1
        self.manifest["total_rows"] += 1
        self._save_manifest()

        return {
            "shard": shard_idx,
            "row": row,
            "dim": self.dim,
        }

    @property
    def total_rows(self) -> int:
        return self.manifest.get("total_rows", 0)


# ---------------------------------------------------------------------------
# EmbeddingShardReader
# ---------------------------------------------------------------------------
class EmbeddingShardReader:
    """Read embeddings from shard storage by reference.

    Also supports loading all embeddings for bulk operations (e.g. search).
    """

    def _guard(self, path: str) -> str:
        """Inline containment check — keeps CodeQL taint-chain visible at every sink."""
        rp = os.path.realpath(path)
        base = os.path.realpath(self.embeddings_dir)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes storage root: {rp!r}")
        return rp

    def __init__(self, embeddings_dir: str) -> None:
        self.embeddings_dir = _canonical_storage_root(embeddings_dir)
        self._shard_cache: Dict[int, np.ndarray] = {}
        self._map_cache: Dict[int, List[Dict[str, Any]]] = {}

        self.manifest_path = _child_path(self.embeddings_dir, "manifest.json")
        self.manifest: Optional[Dict[str, Any]] = None
        safe_manifest = self._guard(self.manifest_path)
        if os.path.exists(safe_manifest):
            with open(safe_manifest, "r", encoding="utf-8") as f:
                self.manifest = json.load(f)

    @property
    def available(self) -> bool:
        """True if shard storage exists and has data."""
        return self.manifest is not None and self.manifest.get("total_rows", 0) > 0

    @property
    def dim(self) -> int:
        if self.manifest:
            return int(self.manifest.get("embedding_dim", DEFAULT_DIM))
        return DEFAULT_DIM

    # ---- shard loading ----

    def _shard_npy_path(self, idx: int) -> str:
        return _child_path(self.embeddings_dir, _shard_name(idx) + ".npy")

    def _shard_map_path(self, idx: int) -> str:
        return _child_path(self.embeddings_dir, _shard_name(idx) + ".map.jsonl")

    def _load_shard(self, idx: int) -> np.ndarray:
        """Load a shard into cache (read-only memmap)."""
        if idx not in self._shard_cache:
            npy_path = self._guard(self._shard_npy_path(idx))
            if not os.path.exists(npy_path):
                raise FileNotFoundError(f"Shard {idx} not found: {npy_path}")
            self._shard_cache[idx] = np.load(npy_path, mmap_mode="r")
        return self._shard_cache[idx]

    def _load_map(self, idx: int) -> List[Dict[str, Any]]:
        """Load the map file for a shard."""
        if idx not in self._map_cache:
            map_path = self._guard(self._shard_map_path(idx))
            entries: List[Dict[str, Any]] = []
            if os.path.exists(map_path):
                with open(map_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
            self._map_cache[idx] = entries
        return self._map_cache[idx]

    # ---- public API ----

    def load_one(self, embedding_ref: Dict[str, Any]) -> Optional[np.ndarray]:
        """Load a single embedding by its reference.

        Args:
            embedding_ref: {"shard": int, "row": int, "dim": int}

        Returns:
            numpy array of shape (dim,) or None if not found.
        """
        if not embedding_ref:
            return None
        shard_idx = int(embedding_ref.get("shard", 0))
        row = int(embedding_ref.get("row", 0))
        try:
            shard = self._load_shard(shard_idx)
            return np.asarray(shard[row], dtype=np.float32).copy()
        except (FileNotFoundError, IndexError):
            return None

    def load_batch(
        self, refs: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], Optional[np.ndarray]]]:
        """Load multiple embeddings. Returns list of (ref, embedding) pairs."""
        results = []
        for ref in refs:
            results.append((ref, self.load_one(ref)))
        return results

    def load_all_for_class(
        self, memory_class: str = "core"
    ) -> List[Tuple[int, np.ndarray]]:
        """Load all embeddings of a given memory class.

        Returns list of (eid, embedding) pairs, useful for building search matrices.
        """
        if not self.manifest:
            return []

        results: List[Tuple[int, np.ndarray]] = []
        active = self.manifest.get("active_shard", 0)

        for shard_idx in range(active + 1):
            try:
                shard = self._load_shard(shard_idx)
                map_entries = self._load_map(shard_idx)
            except FileNotFoundError:
                continue

            for entry in map_entries:
                if entry.get("memory_class") != memory_class:
                    continue
                row = int(entry.get("row", 0))
                eid = int(entry.get("eid", 0))
                try:
                    vec = np.asarray(shard[row], dtype=np.float32).copy()
                    results.append((eid, vec))
                except IndexError:
                    continue

        return results

    def get_eid_to_ref_map(self) -> Dict[int, Dict[str, Any]]:
        """Build a mapping from eid → embedding_ref for all stored embeddings.

        Useful during migration to update node payloads with refs.
        """
        if not self.manifest:
            return {}

        mapping: Dict[int, Dict[str, Any]] = {}
        active = self.manifest.get("active_shard", 0)
        dim = self.dim

        for shard_idx in range(active + 1):
            map_entries = self._load_map(shard_idx)
            for entry in map_entries:
                eid = int(entry.get("eid", 0))
                row = int(entry.get("row", 0))
                mapping[eid] = {"shard": shard_idx, "row": row, "dim": dim}

        return mapping

    def clear_cache(self) -> None:
        """Release cached memmaps and map data."""
        self._shard_cache.clear()
        self._map_cache.clear()


# ---------------------------------------------------------------------------
# Legacy support
# ---------------------------------------------------------------------------
def load_legacy_embedding(data_dir: str, eid: int) -> Optional[np.ndarray]:
    """Load an embedding from the old per-file format: emb_<eid>.npy

    Returns None if the file doesn't exist.
    """
    safe_data_dir = _canonical_storage_root(data_dir)
    path = _child_path(safe_data_dir, f"emb_{int(eid)}.npy")
    # Inline containment guard — CodeQL needs to see realpath+startswith at the sink
    rp = os.path.realpath(path)
    base = os.path.realpath(safe_data_dir)
    if not rp.startswith(base + os.sep):
        raise ValueError(f"Path escapes storage root: {rp!r}")
    if not os.path.exists(rp):
        return None
    try:
        return np.load(rp).astype(np.float32)
    except Exception:
        return None


def load_embedding(
    eid: int,
    payload: Dict[str, Any],
    shard_reader: Optional[EmbeddingShardReader],
    data_dir: str,
) -> Optional[np.ndarray]:
    """Universal embedding loader with fallback chain.

    1. If payload has embedding_ref → load from shard
    2. Else if legacy emb_<eid>.npy exists → load from file
    3. Else → return None
    """
    # Try shard first
    ref = payload.get("embedding_ref")
    if ref and shard_reader:
        vec = shard_reader.load_one(ref)
        if vec is not None:
            return vec

    # Fallback to legacy
    return load_legacy_embedding(data_dir, eid)
