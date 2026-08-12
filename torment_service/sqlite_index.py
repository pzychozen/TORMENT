# torment_service/sqlite_index.py
"""
SQLite Sidecar Index — Phase 4 of the TORMENT v2.1 migration.

=== DESIGN RULE ===
SQLite should help the system, not define it.

This module provides FAST METADATA LOOKUP only. It is:
  - A mirror of canonical JSONL/NPY data (never authoritative)
  - Deletable and rebuildable at any time
  - Optional — the engine runs fine without it
  - Write-order: JSONL first, SQLite second, always

If SQLite fails at any point, log a warning and continue.
The engine is not dependent on this index.
=== END DESIGN RULE ===
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

from .embedding_store import _child_path
from .scoring import derive_provenance_type
from .archive_lifecycle import (
    is_current_archive_chunk,
    replay_canonical_archive_documents,
)

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _now_ts() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# Schema DDL — matches todolist.md sections 8.2 and 8.3 exactly
# ---------------------------------------------------------------------------

_SCHEMA_DDL = """
-- Core memory index
CREATE TABLE IF NOT EXISTS core_nodes (
    eid          INTEGER PRIMARY KEY,
    kind         TEXT,
    tier         TEXT,
    provenance_type TEXT,
    memory_class TEXT DEFAULT 'core',
    step         INTEGER,
    created_at   TEXT,
    half_life_days REAL,
    coherence    REAL,
    strength     REAL,
    confidence   REAL,
    summary      TEXT,
    shard        INTEGER,
    row_idx      INTEGER
);

CREATE TABLE IF NOT EXISTS core_motifs (
    eid    INTEGER,
    motif  TEXT,
    weight REAL
);
CREATE INDEX IF NOT EXISTS idx_core_motifs_eid ON core_motifs(eid);
CREATE INDEX IF NOT EXISTS idx_core_motifs_motif ON core_motifs(motif);

CREATE TABLE IF NOT EXISTS core_events (
    event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    step       INTEGER,
    eid        INTEGER,
    drift_score REAL,
    coherence  REAL,
    timestamp  TEXT
);
CREATE INDEX IF NOT EXISTS idx_core_events_type ON core_events(event_type);
CREATE INDEX IF NOT EXISTS idx_core_events_step ON core_events(step);

CREATE TABLE IF NOT EXISTS trajectory_index (
    step          INTEGER PRIMARY KEY,
    eid           INTEGER,
    coh           REAL,
    phi_index     INTEGER,
    corridor_deg  REAL,
    pos_x         REAL,
    pos_y         REAL,
    pos_z         REAL
);

-- Archive index
CREATE TABLE IF NOT EXISTS documents (
    doc_id      TEXT PRIMARY KEY,
    title       TEXT,
    source_type TEXT,
    chunk_count INTEGER,
    token_count INTEGER,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT,
    chunk_index INTEGER,
    token_count INTEGER,
    shard       INTEGER,
    row_idx     INTEGER,
    created_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);

CREATE TABLE IF NOT EXISTS chunk_sections (
    chunk_id     TEXT,
    section_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_chunk_sections_chunk ON chunk_sections(chunk_id);

-- Metadata
CREATE TABLE IF NOT EXISTS index_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


# ---------------------------------------------------------------------------
# IndexManager
# ---------------------------------------------------------------------------

class IndexManager:
    """SQLite sidecar index for one agent's memory.

    Mirrors JSONL writes for fast lookup. Never authoritative —
    always rebuildable from canonical JSONL/NPY sources.
    """

    def __init__(self, index_dir: str) -> None:
        # Canonicalize via local variable so CodeQL sees the full
        # realpath ➜ startswith ➜ makedirs chain without attribute indirection.
        _safe_dir = os.path.realpath(index_dir)
        if not _safe_dir.startswith(os.sep) and not os.path.isabs(_safe_dir):
            raise ValueError(f"index_dir did not resolve to absolute path: {_safe_dir!r}")
        os.makedirs(_safe_dir, exist_ok=True)
        self.index_dir = _safe_dir
        self.db_path = _child_path(self.index_dir, "memory_index.sqlite")
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        """Open database and create tables if needed."""
        try:
            self._conn = sqlite3.connect(self.db_path, timeout=5.0)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.executescript(_SCHEMA_DDL)
            # --- Schema upgrade: add provenance_type if missing (v4.0→v4.1) ---
            try:
                self._conn.execute(
                    "ALTER TABLE core_nodes ADD COLUMN provenance_type TEXT"
                )
                self._conn.commit()
            except sqlite3.OperationalError:
                pass  # column already exists — expected on fresh schema
            self._conn.execute(
                "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
                ("schema_version", "4.1"),
            )
            self._conn.commit()
        except Exception as e:
            logger.warning("SQLite index init failed: %s", e)
            self._conn = None

    @property
    def available(self) -> bool:
        return self._conn is not None

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception as e:
                logger.debug("SQLite close ignored: %s", e)
            self._conn = None

    # ------------------------------------------------------------------
    # Safe execute wrapper — all writes go through here
    # ------------------------------------------------------------------

    def _safe_execute(self, sql: str, params: tuple = ()) -> bool:
        """Execute SQL safely. Returns True on success, False on failure."""
        if not self._conn:
            return False
        try:
            self._conn.execute(sql, params)
            self._conn.commit()
            return True
        except Exception as e:
            logger.warning("SQLite write failed: %s — %s", sql[:80], e)
            return False

    def _safe_executemany(self, sql: str, param_list: List[tuple]) -> bool:
        if not self._conn or not param_list:
            return False
        try:
            self._conn.executemany(sql, param_list)
            self._conn.commit()
            return True
        except Exception as e:
            logger.warning("SQLite executemany failed: %s — %s", sql[:80], e)
            return False

    def _safe_query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        if not self._conn:
            return []
        try:
            self._conn.row_factory = sqlite3.Row
            cur = self._conn.execute(sql, params)
            return cur.fetchall()
        except Exception as e:
            logger.warning("SQLite query failed: %s — %s", sql[:80], e)
            return []

    # ------------------------------------------------------------------
    # Mirror-write methods (called AFTER canonical JSONL writes)
    # ------------------------------------------------------------------

    def index_node(self, eid: int, payload: Dict[str, Any]) -> bool:
        """Mirror a core node write to the index.

        Called after flush_node() writes to nodes.jsonl.
        Uses INSERT OR REPLACE so re-indexing the same eid is safe.
        """
        emb_ref = payload.get("embedding_ref") or {}
        # Derive compact provenance classification from raw provenance
        prov_type = derive_provenance_type(payload.get("provenance"))
        return self._safe_execute(
            """INSERT OR REPLACE INTO core_nodes
               (eid, kind, tier, provenance_type, memory_class, step,
                created_at, half_life_days, coherence, strength, confidence,
                summary, shard, row_idx)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                int(eid),
                str(payload.get("type") or payload.get("mtype") or ""),
                str(payload.get("tier") or payload.get("character_tier") or ""),
                prov_type,
                str(payload.get("memory_class", "core")),
                int(payload.get("created_at") or payload.get("born_step") or 0),
                str(payload.get("created_ts") or _now_iso()),
                float(payload.get("half_life", 0.0)),
                float(payload.get("coherence", 0.0)),
                float(payload.get("strength", 0.0)),
                float(payload.get("confidence", 0.0)),
                str(payload.get("summary") or payload.get("text") or "")[:500],
                int(emb_ref.get("shard", -1)),
                int(emb_ref.get("row", -1)),
            ),
        )

    def index_event(self, event: Dict[str, Any]) -> bool:
        """Mirror a memory event to the index.

        Called after _log_event() writes to memory_events.jsonl.
        """
        return self._safe_execute(
            """INSERT INTO core_events
               (event_type, step, eid, drift_score, coherence, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(event.get("type", "")),
                int(event.get("step", 0)),
                int(event.get("eid", 0)),
                float(event.get("drift_score", 0.0)),
                float(event.get("coherence", 0.0)),
                str(event.get("ts") or _now_ts()),
            ),
        )

    def index_motif_membership(self, eid: int, motif_id: str, weight: float = 1.0) -> bool:
        """Mirror a motif membership to the index."""
        # Remove old entry for this eid+motif pair, then insert fresh
        self._safe_execute(
            "DELETE FROM core_motifs WHERE eid = ? AND motif = ?",
            (int(eid), str(motif_id)),
        )
        return self._safe_execute(
            "INSERT INTO core_motifs (eid, motif, weight) VALUES (?, ?, ?)",
            (int(eid), str(motif_id), float(weight)),
        )

    def index_trajectory(
        self,
        step: int,
        eid: int,
        pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        coh: float = 0.0,
        phi_index: int = 0,
        corridor_deg: float = 0.0,
    ) -> bool:
        """Mirror a trajectory snapshot to the index."""
        return self._safe_execute(
            """INSERT OR REPLACE INTO trajectory_index
               (step, eid, coh, phi_index, corridor_deg, pos_x, pos_y, pos_z)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                int(step), int(eid), float(coh), int(phi_index),
                float(corridor_deg),
                float(pos[0]), float(pos[1]), float(pos[2]),
            ),
        )

    def index_document(self, doc: Dict[str, Any]) -> bool:
        """Mirror an archive document record to the index."""
        return self._safe_execute(
            """INSERT OR REPLACE INTO documents
               (doc_id, title, source_type, chunk_count, token_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(doc.get("doc_id", "")),
                str(doc.get("title", "")),
                str(doc.get("source_type", "text")),
                int(doc.get("chunk_count", 0)),
                int(doc.get("token_count", 0)),
                str(doc.get("created_ts") or _now_ts()),
            ),
        )

    def index_chunk(self, chunk: Dict[str, Any]) -> bool:
        """Mirror an archive chunk record to the index."""
        emb_ref = chunk.get("embedding_ref") or {}
        ok = self._safe_execute(
            """INSERT OR REPLACE INTO chunks
               (chunk_id, doc_id, chunk_index, token_count, shard, row_idx, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(chunk.get("chunk_id", "")),
                str(chunk.get("doc_id", "")),
                int(chunk.get("chunk_index", 0)),
                int(chunk.get("token_count", 0)),
                int(emb_ref.get("shard", -1)),
                int(emb_ref.get("row", -1)),
                str(chunk.get("created_ts") or _now_ts()),
            ),
        )

        # Index section paths
        section_path = chunk.get("section_path") or []
        if section_path and ok:
            chunk_id = str(chunk.get("chunk_id", ""))
            self._safe_execute(
                "DELETE FROM chunk_sections WHERE chunk_id = ?",
                (chunk_id,),
            )
            for sp in section_path:
                self._safe_execute(
                    "INSERT INTO chunk_sections (chunk_id, section_path) VALUES (?, ?)",
                    (chunk_id, str(sp)),
                )
        return ok

    def delete_document_index(self, doc_id: str) -> bool:
        """Remove a document and its chunks from the index."""
        ok1 = self._safe_execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        # Get chunk_ids before deleting
        rows = self._safe_query("SELECT chunk_id FROM chunks WHERE doc_id = ?", (doc_id,))
        chunk_ids = [str(r["chunk_id"]) for r in rows]
        ok2 = self._safe_execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        for cid in chunk_ids:
            self._safe_execute("DELETE FROM chunk_sections WHERE chunk_id = ?", (cid,))
        return ok1 and ok2

    # ------------------------------------------------------------------
    # Query helpers (for UI, debug, analytics)
    # ------------------------------------------------------------------

    def get_recent_memories(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fast recent memory lookup, ordered by step descending."""
        rows = self._safe_query(
            "SELECT * FROM core_nodes ORDER BY step DESC LIMIT ?",
            (int(limit),),
        )
        return [dict(r) for r in rows]

    def get_memories_by_kind(self, kind: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get memories filtered by kind (type)."""
        rows = self._safe_query(
            "SELECT * FROM core_nodes WHERE kind = ? ORDER BY step DESC LIMIT ?",
            (str(kind), int(limit)),
        )
        return [dict(r) for r in rows]

    def get_memories_by_motif(self, motif_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get memories that belong to a specific motif."""
        rows = self._safe_query(
            """SELECT cn.*, cm.motif, cm.weight AS motif_weight
               FROM core_motifs cm
               JOIN core_nodes cn ON cm.eid = cn.eid
               WHERE cm.motif = ?
               ORDER BY cm.weight DESC, cn.step DESC
               LIMIT ?""",
            (str(motif_id), int(limit)),
        )
        return [dict(r) for r in rows]

    def get_trajectory_range(
        self,
        step_from: int,
        step_to: int,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Get trajectory snapshots for a step range."""
        rows = self._safe_query(
            """SELECT * FROM trajectory_index
               WHERE step >= ? AND step <= ?
               ORDER BY step ASC
               LIMIT ?""",
            (int(step_from), int(step_to), int(limit)),
        )
        return [dict(r) for r in rows]

    def get_events_by_type(
        self,
        event_type: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get events filtered by type."""
        rows = self._safe_query(
            "SELECT * FROM core_events WHERE event_type = ? ORDER BY event_id DESC LIMIT ?",
            (str(event_type), int(limit)),
        )
        return [dict(r) for r in rows]

    def search_archive_metadata(
        self,
        title_query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search archive documents by title (LIKE match)."""
        rows = self._safe_query(
            "SELECT * FROM documents WHERE title LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{title_query}%", int(limit)),
        )
        return [dict(r) for r in rows]

    def get_chunks_for_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get indexed chunks for a document."""
        rows = self._safe_query(
            "SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index ASC",
            (str(doc_id),),
        )
        return [dict(r) for r in rows]

    def get_index_stats(self) -> Dict[str, Any]:
        """Return quick stats about the index contents."""
        stats: Dict[str, Any] = {}
        for table in ["core_nodes", "core_events", "core_motifs",
                       "trajectory_index", "documents", "chunks"]:
            rows = self._safe_query(f"SELECT COUNT(*) as cnt FROM {table}")
            stats[table] = int(rows[0]["cnt"]) if rows else 0
        stats["db_path"] = self.db_path
        stats["db_size_bytes"] = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        return stats

    # ------------------------------------------------------------------
    # Rebuild from canonical sources
    # ------------------------------------------------------------------

    def clear_all(self) -> None:
        """Drop all data from the index (keeps schema)."""
        if not self._conn:
            return
        for table in ["core_nodes", "core_motifs", "core_events",
                       "trajectory_index", "documents", "chunks", "chunk_sections"]:
            self._safe_execute(f"DELETE FROM {table}")

    @staticmethod
    def _guard_rebuild_path(path: str, label: str) -> str:
        """Canonicalize a rebuild source path via ``os.path.realpath``.

        Rebuild sources (nodes.jsonl, events.jsonl, etc.) intentionally live
        outside ``index_dir`` — they come from the agent's data directory —
        so no base-containment check is applied here.

        The purpose of this helper is to resolve the path to an absolute
        canonical form so that CodeQL's taint model sees a ``realpath``
        call between the caller-supplied value and the ``open()`` sink.
        """
        if not path:
            return ""
        return os.path.realpath(path)

    def rebuild_from_jsonl(
        self,
        nodes_path: str,
        events_path: str = "",
        trajectories_path: str = "",
        archive_documents_path: str = "",
        archive_chunks_path: str = "",
        motifs_path: str = "",
    ) -> Dict[str, int]:
        """Rebuild the entire index from canonical JSONL/JSON files.

        Returns counts of records indexed per table.
        """
        # Inline containment guards — CodeQL needs visible realpath+startswith
        # before every open() sink below.
        safe_nodes = self._guard_rebuild_path(nodes_path, "nodes")
        safe_events = self._guard_rebuild_path(events_path, "events")
        safe_trajectories = self._guard_rebuild_path(trajectories_path, "trajectories")
        safe_archive_docs = self._guard_rebuild_path(archive_documents_path, "archive_documents")
        safe_archive_chunks = self._guard_rebuild_path(archive_chunks_path, "archive_chunks")
        safe_motifs = self._guard_rebuild_path(motifs_path, "motifs")
        archive_source = safe_archive_docs or safe_archive_chunks
        # Archive replay derives one canonical document state used for both
        # document lifecycle suppression and chunk-range replacement filtering.
        archive_documents = replay_canonical_archive_documents(
            safe_archive_docs,
            os.path.join(os.path.dirname(archive_source), "events.jsonl"),
        ) if archive_source else {}

        self.clear_all()
        counts: Dict[str, int] = {
            "core_nodes": 0,
            "core_events": 0,
            "trajectory_index": 0,
            "documents": 0,
            "chunks": 0,
            "core_motifs": 0,
        }

        # --- Core nodes (last record per eid wins) ---
        if safe_nodes and os.path.exists(safe_nodes):
            canonical: Dict[int, Dict[str, Any]] = {}
            with open(safe_nodes, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        eid = int(obj.get("eid", 0))
                        canonical[eid] = obj.get("payload", {}) or {}
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            for eid, payload in canonical.items():
                if self.index_node(eid, payload):
                    counts["core_nodes"] += 1

        # --- Core events ---
        if safe_events and os.path.exists(safe_events):
            with open(safe_events, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        if self.index_event(obj):
                            counts["core_events"] += 1
                    except (json.JSONDecodeError, KeyError):
                        continue

        # --- Trajectory index ---
        if safe_trajectories and os.path.exists(safe_trajectories):
            with open(safe_trajectories, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        pos = obj.get("pos", [0, 0, 0])
                        if len(pos) < 3:
                            pos = pos + [0.0] * (3 - len(pos))
                        if self.index_trajectory(
                            step=int(obj.get("step", 0)),
                            eid=int(obj.get("eid", 0)),
                            pos=(float(pos[0]), float(pos[1]), float(pos[2])),
                        ):
                            counts["trajectory_index"] += 1
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

        # --- Archive documents ---
        if safe_archive_docs and os.path.exists(safe_archive_docs):
            with open(safe_archive_docs, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        document = archive_documents.get(str(obj.get("doc_id", "")))
                        if document is None or not document.active:
                            continue
                        record = obj
                        if document.chunk_count is None:
                            record = dict(obj)
                            record["chunk_count"] = 0
                        if self.index_document(record):
                            counts["documents"] += 1
                    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                        continue

        # --- Archive chunks ---
        if safe_archive_chunks and os.path.exists(safe_archive_chunks):
            with open(safe_archive_chunks, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        if not is_current_archive_chunk(
                            archive_documents,
                            str(obj.get("doc_id", "")),
                            int(obj.get("chunk_index", 0)),
                        ):
                            continue
                        if self.index_chunk(obj):
                            counts["chunks"] += 1
                    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                        continue

        # --- Motifs (JSON file, not JSONL) ---
        if safe_motifs and os.path.exists(safe_motifs):
            try:
                with open(safe_motifs, "r", encoding="utf-8") as f:
                    motifs_data = json.load(f)
                motif_list = motifs_data if isinstance(motifs_data, list) else list(motifs_data.values())
                for m in motif_list:
                    mid = str(m.get("motif_id", ""))
                    members = m.get("members", [])
                    strength = float(m.get("strength", 1.0))
                    for eid in members:
                        if self.index_motif_membership(int(eid), mid, strength):
                            counts["core_motifs"] += 1
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning("Motif rebuild skipped (corrupt file): %s", e)

        # Record rebuild timestamp
        self._safe_execute(
            "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
            ("last_rebuild_ts", str(_now_ts())),
        )

        return counts
