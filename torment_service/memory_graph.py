# torment_service/memory_graph.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import os, json, time

import numpy as np

from .kernel.seed_trajectory_analysis import classify_trajectory
from .kernel.trajectory_logging import TrajectoryLogger
from .kernel.seed_entities import SeedWorld, SeedEntity, _as3
from .embeddings import Embedder, HashEmbedding
from .embedding_store import (
    EmbeddingShardWriter,
    EmbeddingShardReader,
    load_embedding as _load_embedding_universal,
    load_legacy_embedding,
)


def _now_ts() -> int:
    return int(time.time())


class MemoryGraph:
    """
    A light persistent graph over SeedWorld entities.

    Storage:
      - JSONL for node payload metadata (append-only; last record per EID is canonical)
      - JSONL for edges
      - .npy for embeddings
    """

    def __init__(self, data_dir: str, embedder: Optional[Embedder] = None, sqlite_index=None) -> None:
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        # Optional SQLite sidecar index (Phase 4).
        # If provided, mirror writes go to SQLite after JSONL.
        # If None or if any mirror write fails, the engine continues normally.
        self._sqlite_index = sqlite_index

        self.embedder = embedder or HashEmbedding()
        # --- embedding index (fast similarity search) ---
        # Default: keep embeddings in RAM for fast dot-product search. Set env to 0 for low-RAM mode.
        self._emb_dim = int(getattr(self.embedder, "dim", 0) or 0) or 384
        self._cache_embeddings = str(os.getenv("TORMENT_GRAPH_EMB_CACHE", "1")).strip().lower() not in ("0", "false", "no")
        self._emb_by_eid: Dict[int, np.ndarray] = {}
        self._eid_list: List[int] = []
        self._emb_mat: Optional[np.ndarray] = None  # shape [N, D], float32, row-normalized
        self._index_dirty: bool = True

        # --- shard-based embedding storage ---
        self._emb_dir = os.path.join(self.data_dir, "embeddings")
        self._shard_writer: Optional[EmbeddingShardWriter] = None
        self._shard_reader: Optional[EmbeddingShardReader] = None
        self._init_shard_storage()

        self.world = SeedWorld()
        self.entities: Dict[int, SeedEntity] = {}

        self.traj = TrajectoryLogger(root_dir=self.data_dir)

        self.meta_path = os.path.join(self.data_dir, "nodes.jsonl")
        self.edges_path = os.path.join(self.data_dir, "edges.jsonl")
        self.events_path = os.path.join(self.data_dir, "memory_events.jsonl")

        self.edges: List[Dict[str, Any]] = []

        self._load()

    def _init_shard_storage(self) -> None:
        """Initialize shard writer and reader for embedding storage."""
        try:
            self._shard_writer = EmbeddingShardWriter(self._emb_dir, dim=self._emb_dim)
            self._shard_reader = EmbeddingShardReader(self._emb_dir)
        except Exception:
            # Graceful fallback — legacy per-file mode still works
            self._shard_writer = None
            self._shard_reader = None

    # ----------------------------
    # Persistence
    # ----------------------------

    def _append_jsonl(self, path: str, obj: Dict[str, Any]) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    def _emb_path(self, eid: int) -> str:
        return os.path.join(self.data_dir, f"emb_{int(eid)}.npy")

    def _normalize(self, v: np.ndarray) -> np.ndarray:
        v = np.asarray(v, dtype=np.float32).reshape(-1)
        if v.size == 0:
            return np.zeros(self._emb_dim, dtype=np.float32)
        if int(v.shape[0]) != int(self._emb_dim):
            if v.size < int(self._emb_dim):
                v = np.pad(v, (0, int(self._emb_dim) - int(v.size)))
            else:
                v = v[: int(self._emb_dim)]
        n = float(np.linalg.norm(v) + 1e-12)
        return (v / n).astype(np.float32)

    def _rebuild_matrix(self) -> None:
        self._eid_list = sorted(self._emb_by_eid.keys())
        if not self._eid_list:
            self._emb_mat = None
            self._index_dirty = False
            return
        self._emb_mat = np.stack([self._emb_by_eid[eid] for eid in self._eid_list], axis=0).astype(np.float32)
        self._index_dirty = False

    def _load_embeddings_into_ram(self) -> None:
        self._emb_by_eid.clear()
        for eid, ent in self.entities.items():
            payload = getattr(ent, "payload", {}) or {}
            vec = _load_embedding_universal(
                eid, payload, self._shard_reader, self.data_dir
            )
            if vec is None:
                continue
            try:
                self._emb_by_eid[int(eid)] = self._normalize(vec)
            except Exception:
                continue
        self._rebuild_matrix()

    def _ensure_index(self) -> None:
        if not self._cache_embeddings:
            return
        if self._index_dirty or self._emb_mat is None:
            self._load_embeddings_into_ram()

    def _register_embedding(self, eid: int, emb: np.ndarray) -> None:
        if not self._cache_embeddings:
            return
        self._emb_by_eid[int(eid)] = self._normalize(emb)
        self._index_dirty = True

    def search(
        self,
        query_text: str,
        *,
        top_k: int = 8,
        user_id: Optional[str] = None,
        min_score: Optional[float] = None,
        type_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Vector search over stored memories."""
        q = (query_text or "").strip()
        if not q:
            return []

        qv = np.asarray(self.embedder.embed(q), dtype=np.float32).reshape(-1)
        if int(qv.shape[0]) != int(self._emb_dim):
            qv = self._normalize(qv)

        hits_eids: List[Tuple[int, float]] = []
        if self._cache_embeddings:
            self._ensure_index()
            if self._emb_mat is None or not self._eid_list:
                return []
            qv = self._normalize(qv)
            scores = (self._emb_mat @ qv).astype(np.float32)
            k = int(max(1, top_k))
            n = int(scores.shape[0])
            if n <= k:
                order = np.argsort(-scores)
            else:
                idx = np.argpartition(-scores, k - 1)[:k]
                order = idx[np.argsort(-scores[idx])]
            hits_eids = [(int(self._eid_list[int(i)]), float(scores[int(i)])) for i in order[:k]]
        else:
            qv = self._normalize(qv)
            for eid, ent in self.entities.items():
                payload = getattr(ent, "payload", {}) or {}
                raw = _load_embedding_universal(
                    eid, payload, self._shard_reader, self.data_dir
                )
                if raw is None:
                    continue
                try:
                    v = self._normalize(raw)
                except Exception:
                    continue
                hits_eids.append((int(eid), float(np.dot(v, qv))))
            hits_eids.sort(key=lambda t: t[1], reverse=True)
            hits_eids = hits_eids[: int(max(1, top_k))]

        out: List[Dict[str, Any]] = []
        type_set = set(type_filter or [])
        for eid, sc in hits_eids:
            if min_score is not None and float(sc) < float(min_score):
                continue
            ent = self.entities.get(int(eid))
            if ent is None:
                continue
            payload = dict(ent.payload or {})
            mtype = str(payload.get("type") or payload.get("mtype") or "")
            if type_set and mtype and mtype not in type_set:
                continue
            out.append({
                "eid": int(eid),
                "score": float(sc),
                "summary": str(payload.get("summary") or payload.get("text") or ""),
                "type": mtype or "memory",
                "strength": float(payload.get("strength") or 0.0),
                "confidence": float(payload.get("confidence") or 0.0),
                "step": int(payload.get("step") or payload.get("born_step") or 0),
                "ts": int(payload.get("ts") or payload.get("created_ts") or 0),
                **payload,
            })
        return out



    def _log_event(self, evt: Dict[str, Any]) -> None:
        evt = dict(evt)
        evt.setdefault("ts", _now_ts())
        # Canonical write (JSONL first — always)
        self._append_jsonl(self.events_path, evt)
        # Mirror to SQLite sidecar (Phase 4) — failure is non-fatal
        if self._sqlite_index:
            try:
                self._sqlite_index.index_event(evt)
            except Exception:
                pass

    def _load(self) -> None:
        """
        Load nodes.jsonl as append-only log, taking the LAST record per EID as canonical.
        """
        max_eid = 0

        # Load nodes (canonical per EID)
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    eid = int(obj.get("eid"))
                    max_eid = max(max_eid, eid)

                    payload = obj.get("payload", {}) or {}
                    born_step = int(obj.get("born_step", 0) or 0)
                    channel = int(obj.get("channel", 0) or 0)

                    # canonical physics fields (persisted in payload)
                    pos = _as3(payload.get("pos", payload.get("seed_pos0", np.zeros(3))))
                    vel = _as3(payload.get("vel", payload.get("seed_v0", np.zeros(3))))
                    vel0 = _as3(payload.get("vel0", vel))

                    if eid in self.entities:
                        # update in-place (last record wins)
                        ent = self.entities[eid]
                        ent.born_step = born_step
                        ent.channel = channel
                        ent.pos = pos
                        ent.vel = vel
                        ent.vel0 = vel0
                        ent.alive = bool(payload.get("alive", True))
                        ent.payload = payload
                    else:
                        ent = SeedEntity(
                            eid=eid,
                            born_step=born_step,
                            channel=channel,
                            pos=pos,
                            vel=vel,
                            vel0=vel0,
                            payload=payload,
                            trail=[],
                            alive=bool(payload.get("alive", True)),
                        )
                        self.entities[eid] = ent
                        self.world.entities.append(ent)

        # Load edges
        if os.path.exists(self.edges_path):
            with open(self.edges_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    self.edges.append(json.loads(line))

        # Prevent EID collisions on future spawns
        try:
            self.world._next_id = int(max_eid) + 1  # SeedWorld uses _next_id internally
        except Exception:
            pass

    # ----------------------------
    # Node ops
    # ----------------------------

    def update_payload(self, eid: int, patch: Dict[str, Any]) -> None:
        """
        Update an existing entity's payload and append a new nodes.jsonl record.
        Loader will accept the last record as canonical.
        """
        eid = int(eid)
        if eid not in self.entities:
            raise KeyError(f"Unknown eid: {eid}")

        ent = self.entities[eid]
        try:
            ent.payload.update(dict(patch))
        except Exception:
            ent.payload = dict(patch)

        # keep canonical physics fields consistent if present
        if "pos" in ent.payload:
            try:
                ent.pos = _as3(ent.payload["pos"])
            except Exception:
                pass
        if "vel" in ent.payload:
            try:
                ent.vel = _as3(ent.payload["vel"])
            except Exception:
                pass
        if "vel0" in ent.payload:
            try:
                ent.vel0 = _as3(ent.payload["vel0"])
            except Exception:
                pass

        self._append_jsonl(
            self.meta_path,
            {
                "eid": int(ent.eid),
                "born_step": int(getattr(ent, "born_step", 0) or 0),
                "channel": int(getattr(ent, "channel", 0) or 0),
                "payload": ent.payload,
            },
        )
        # Mirror to SQLite sidecar (Phase 4) — failure is non-fatal
        if self._sqlite_index:
            try:
                self._sqlite_index.index_node(int(ent.eid), ent.payload or {})
            except Exception:
                pass

    @staticmethod
    def _vec3(x, default=(0.0, 0.0, 0.0)):
        if x is None:
            return np.asarray(default, dtype=float)
        a = np.asarray(x, dtype=float).reshape(-1)
        if a.size == 0:
            return np.asarray(default, dtype=float)
        if a.size == 1:
            return np.asarray([float(a[0]), 0.0, 0.0], dtype=float)
        if a.size == 2:
            return np.asarray([float(a[0]), float(a[1]), 0.0], dtype=float)
        return np.asarray([float(a[0]), float(a[1]), float(a[2])], dtype=float)

    def spawn_memory(
        self,
        summary: str,
        embedding: np.ndarray,
        mtype: str,
        strength: float,
        confidence: float,
        half_life_days: float,
        links: Optional[List[str]] = None,
        canon: bool = False,
        user_id: str = "default",
        step: int = 0,
        extra_payload: Optional[Dict[str, Any]] = None,
        memory_class: str = "core",
    ) -> int:
        """Create entity + save embedding, but do NOT write to nodes.jsonl yet.

        Call flush_node(eid) after enrichment (symbols, motifs, etc.) to write
        the complete record exactly once.

        Args:
            memory_class: "core" (identity/relational) or "archive" (document chunks).
                          Defaults to "core" to preserve existing behavior.
        """
        links = links or []
        payload: Dict[str, Any] = {
            "summary": summary,
            "type": mtype,
            "memory_class": str(memory_class),
            "strength": float(strength),
            "confidence": float(confidence),
            "canon": bool(canon),
            "created_at": int(step),
            "created_ts": _now_ts(),
            "last_reinforced": int(step),
            "half_life": float(half_life_days),
            "user_id": user_id,
        }
        if extra_payload:
            payload.update(extra_payload)

        pos0 = self._vec3(payload.get("seed_pos0", None))
        vel0 = self._vec3(payload.get("seed_v0", None))
        payload["pos"] = pos0.tolist()
        payload["vel"] = vel0.tolist()
        payload["vel0"] = vel0.tolist()

        ent = self.world.spawn(
            born_step=int(step),
            channel=0,
            pos=pos0,
            vel=vel0,
            payload=payload,
        )
        self.entities[int(ent.eid)] = ent

        # --- Write embedding: shard (preferred) or legacy per-file ---
        emb_vec = np.asarray(embedding, dtype=np.float32)
        if self._shard_writer:
            try:
                kind = str(mtype or "episode")
                emb_ref = self._shard_writer.append(
                    emb_vec,
                    eid=int(ent.eid),
                    memory_class=str(memory_class),
                    kind=kind,
                    step=int(step),
                )
                # Update ent.payload (spawn copies the dict, so update via entity)
                ent.payload["embedding_ref"] = emb_ref
            except Exception:
                # Fallback to legacy if shard write fails
                emb_path = os.path.join(self.data_dir, f"emb_{ent.eid}.npy")
                np.save(emb_path, emb_vec)
        else:
            # Legacy mode — per-file storage
            emb_path = os.path.join(self.data_dir, f"emb_{ent.eid}.npy")
            np.save(emb_path, emb_vec)

        self._register_embedding(int(ent.eid), embedding)

        self._log_event({
            "type": "MEMORY_CREATE",
            "eid": int(ent.eid),
            "memory_class": str(memory_class),
            "scope": payload.get("scope"),
            "workspace_id": payload.get("workspace_id"),
            "domain_id": payload.get("domain_id"),
            "agent_id": payload.get("agent_id"),
        })

        for tgt in links:
            e = {"src": int(ent.eid), "tgt": tgt, "kind": "link", "w": float(strength), "ts": _now_ts()}
            self.edges.append(e)
            self._append_jsonl(self.edges_path, e)

        return int(ent.eid)

    def flush_node(self, eid: int) -> None:
        """Write the current entity payload to nodes.jsonl (single canonical record).

        Call this after all enrichment (symbols, resonance, motif data) is done
        so the record is written exactly once with the complete payload.
        """
        eid = int(eid)
        ent = self.entities.get(eid)
        if ent is None:
            return
        # Canonical write (JSONL first — always)
        self._append_jsonl(self.meta_path, {
            "eid": int(ent.eid),
            "born_step": int(getattr(ent, "born_step", 0) or 0),
            "channel": int(getattr(ent, "channel", 0) or 0),
            "payload": ent.payload,
        })
        # Mirror to SQLite sidecar (Phase 4) — failure is non-fatal
        if self._sqlite_index:
            try:
                self._sqlite_index.index_node(int(ent.eid), ent.payload or {})
            except Exception:
                pass

    def add_memory(
        self,
        summary: str,
        embedding: np.ndarray,
        mtype: str,
        strength: float,
        confidence: float,
        half_life_days: float,
        links: Optional[List[str]] = None,
        canon: bool = False,
        user_id: str = "default",
        step: int = 0,
        extra_payload: Optional[Dict[str, Any]] = None,
        memory_class: str = "core",
    ) -> int:
        """Legacy interface: spawn + immediate flush (2 writes if update_payload follows).

        Prefer spawn_memory() + enrich + flush_node() for single-write path.
        """
        eid = self.spawn_memory(
            summary=summary,
            embedding=embedding,
            mtype=mtype,
            strength=strength,
            confidence=confidence,
            half_life_days=half_life_days,
            links=links,
            canon=canon,
            user_id=user_id,
            step=step,
            extra_payload=extra_payload,
            memory_class=memory_class,
        )
        self.flush_node(eid)
        return eid

    # ----------------------------
    # World ops
    # ----------------------------

    def step_world(self, step: int, classify_every: int = 50, log_every: int = 1) -> None:
        """
        Advance SeedWorld continuously (non-finite seeds), log kinematics, and
        periodically classify trajectories.

        classify_trajectory signature (your file):
            classify_trajectory(r_history, eps=..., min_samples=...) -> str
        """
        # 1) physics step
        self.world.step()

        # 2) log snapshots
        if log_every and (int(step) % int(log_every) == 0):
            for ent in list(self.world.entities):
                if ent is None or not getattr(ent, "alive", True):
                    continue
                try:
                    self.traj.log_entity(ent, step=int(step))
                except Exception:
                    pass

        # 3) classify occasionally (in-memory only — no nodes.jsonl write)
        #    Trajectory labels are diagnostic; they stay in the entity payload
        #    in RAM and are logged to memory_events.jsonl. They do NOT need to
        #    rewrite nodes.jsonl for every entity — that caused quadratic file
        #    growth (N entities × N/50 classify rounds).
        if classify_every and (int(step) % int(classify_every) == 0):
            for ent in list(self.world.entities):
                if ent is None or not getattr(ent, "alive", True):
                    continue
                try:
                    label = classify_trajectory(getattr(ent, "r_history", []))
                    ent.payload["traj_label"] = str(label)
                    ent.payload["traj_last_classify_step"] = int(step)

                    # log to events (lightweight, does not bloat nodes.jsonl)
                    try:
                        self._append_jsonl(self.events_path, {
                            "type": "TRAJ_CLASSIFY",
                            "ts": _now_ts(),
                            "step": int(step),
                            "eid": int(ent.eid),
                            "traj_label": ent.payload.get("traj_label"),
                        })
                    except Exception:
                        pass

                except Exception:
                    pass