# torment_service/memory_graph.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import os, json, time
import logging

import numpy as np

from .kernel.seed_trajectory_analysis import classify_trajectory
from .kernel.trajectory_logging import TrajectoryLogger
from .kernel.seed_entities import SeedWorld, SeedEntity, _as3
from .embeddings import Embedder, HashEmbedding
from .embedding_store import (
    EmbeddingShardWriter,
    EmbeddingShardReader,
    _child_path,
    load_embedding as _load_embedding_universal,
)
from .lifecycle import (
    LifecycleActor,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStatus,
    derive_protected_lifecycle_from_legacy_markers,
    validate_lifecycle_envelope,
)
from .candidate_types import CandidateShapedValue

log = logging.getLogger("torment.memory_graph")


def _now_ts() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# Half-life decay — applied at query time to effective retrieval strength
# ---------------------------------------------------------------------------
_DECAY_RANKING_FLOOR = 0.03   # minimum effective strength for ranking (avoids total disappearance)

def _half_life_decay_factor(payload: Dict[str, Any], now_ts: Optional[int] = None) -> float:
    """Compute exponential decay factor based on half_life_days.

    Uses ``last_reinforced`` (full clock reset on reinforcement) if available,
    otherwise falls back to ``created_ts``.

    Returns a multiplier in (0, 1].  Caller applies:
        effective_strength = stored_strength * factor
    """
    hl = float(payload.get("half_life", 0) or 0)
    if hl <= 0:
        return 1.0  # no decay configured

    anchor_ts = int(payload.get("last_reinforced_ts", 0) or 0)
    if anchor_ts <= 0:
        anchor_ts = int(payload.get("created_ts", 0) or 0)
    if anchor_ts <= 0:
        return 1.0  # no timestamp → can't decay

    if now_ts is None:
        now_ts = _now_ts()
    age_days = max(0.0, (now_ts - anchor_ts) / 86400.0)
    if age_days <= 0:
        return 1.0

    factor = float(2.0 ** (-age_days / hl))
    return max(_DECAY_RANKING_FLOOR, factor)


# ---------------------------------------------------------------------------
# Q2-H1c + Q2-D Slice 3: write-site lifecycle envelope emission
#
# Per docs/CLUSTER_5_PATH_C_Q2_LIFECYCLE_IMPLEMENTATION_FRAMING_v0.1.md, every
# new memory row created via :meth:`MemoryGraph.spawn_memory` is, on return,
# guaranteed to carry a ``lifecycle_status`` envelope on its payload.
#
# Q2-H1c (original): new rows with no caller-supplied envelope and no legacy
# protected markers receive the canonical row-authoritative UNSET envelope
# (``actor=SYSTEM``, ``via=INGEST_UNMARKED``, ``at=int(time.time())``).
# Caller-supplied envelopes are validated and preserved verbatim. Malformed
# supplied envelopes raise ``LifecycleStateError`` -- no silent downgrade.
#
# Q2-D Slice 3 extension: new rows with no caller-supplied envelope but WITH
# legacy protected markers (canon, kind, tier, srg.is_crystal,
# governance.protected) now stamp the derived PROTECTED envelope instead of
# UNSET. The write-side call uses ``actor=SYSTEM`` -- distinct from the
# read-side Slice 2 derivation which uses ``actor=MIGRATION``. The two
# actors record whether the PROTECTED interpretation was inferred at read
# (legacy origin) or asserted at write (Q2-era runtime).
#
# Still NOT in scope at this slice:
#   * lifecycle enforcement primitive (Q2-F) at production decision sites
#   * existing protected reader migration (``is_compression_protected``,
#     ``derive_retention_tier``) -- deferred to Q2-D Slice 5+
#   * disagreement detection between explicit envelope and legacy markers
#     (Q2-D Slice 4)
#   * review-queue join formalization (Q2-E)
#   * baton-lifecycle / Q2-envelope overlap resolution (R3)
#   * load/rehydrate path stamping (legacy on-disk rows continue to derive
#     PROTECTED-or-UNSET via the Slice 2 read-side shim)
# ---------------------------------------------------------------------------


def _ensure_lifecycle_envelope(payload: Dict[str, Any]) -> None:
    """Ensure the supplied new-row payload carries a lifecycle envelope.

    H1c (Q2-H1c) original behavior with Q2-D Slice 3 extension: stamps a
    canonical envelope on payloads that lack one (PROTECTED if legacy
    protected markers are present, UNSET otherwise), validates any
    caller-supplied envelope and leaves it untouched. Mutates ``payload``
    in place by adding a ``lifecycle_status`` key when one is absent or
    explicitly ``None``.

    Behavior -- three branches:

    1. ``payload["lifecycle_status"]`` absent OR explicitly ``None``:

       a. Q2-D Slice 3 -- first call
          :func:`derive_protected_lifecycle_from_legacy_markers` with
          ``actor=LifecycleActor.SYSTEM`` to see whether any legacy
          protected marker (canon, kind, tier, srg.is_crystal,
          governance.protected) is present. If so, stamp the derived
          PROTECTED envelope. This prevents new rows with legacy
          markers from being silently mis-stamped as UNSET (Hazard B
          from the Q2-D plan).

       b. Otherwise stamp the canonical H1c default UNSET envelope:
          ``state=UNSET``, ``is_authoritative_on_row=True``,
          ``set_by.actor=SYSTEM``, ``set_by.via=INGEST_UNMARKED``,
          ``set_by.at=int(time.time())``, ``requires_join=None``,
          ``history_ref=None``. ``UNSET_DEFAULT`` is structurally
          reserved for the H1a read-side lazy-derive path; H1c uses
          ``INGEST_UNMARKED`` so the two origins remain distinguishable
          at audit time.

    2. ``payload["lifecycle_status"]`` present and non-null -> validated
       via :func:`validate_lifecycle_envelope` and left intact. A
       malformed envelope raises ``LifecycleStateError`` (loud failure,
       no silent replacement, no fallback to protected derivation).
       **Explicit envelope wins**: legacy protected markers on the same
       payload are NOT consulted in this branch, even if they would
       derive a different state. Silent disagreement is acceptable for
       Slice 3; detection is deferred to Q2-D Slice 4.

    Actor distinction (audit-bearing):

      read-side legacy derivation (Slice 2)  -> actor=MIGRATION
      write-side stamping (this function)    -> actor=SYSTEM

    The two actors record whether the PROTECTED interpretation was
    inferred by the read shim at access time (legacy origin) or
    asserted by the runtime at row creation time (Q2-era write).

    Intended caller: :meth:`MemoryGraph.spawn_memory`, which builds a
    fresh payload dict and merges caller-supplied ``extra_payload`` into
    it before invoking this helper. The caller's original
    ``extra_payload`` dict is not mutated; only ``spawn_memory``'s local
    payload dict (and hence the entity that will carry it) is affected.
    """
    supplied = payload.get("lifecycle_status")
    if supplied is None:
        # Q2-D Slice 3: try legacy protected derivation first (write-time
        # actor=SYSTEM, distinct from Slice 2 read-side MIGRATION). If
        # any of the five legacy protected markers is present, stamp
        # the derived PROTECTED envelope so new rows with legacy
        # markers are no longer mis-stamped as plain UNSET. Hazard B
        # from the Q2-D plan.
        derived = derive_protected_lifecycle_from_legacy_markers(
            payload, actor=LifecycleActor.SYSTEM,
        )
        if derived is not None:
            payload["lifecycle_status"] = derived.to_dict()
            return
        # Otherwise stamp the canonical H1c default UNSET envelope.
        env = LifecycleStatus(
            state=LifecycleState.UNSET,
            is_authoritative_on_row=True,
            requires_join=None,
            set_by=LifecycleSetBy(
                actor=LifecycleActor.SYSTEM,
                via=LifecycleSetVia.INGEST_UNMARKED,
                at=int(time.time()),
            ),
            history_ref=None,
        )
        payload["lifecycle_status"] = env.to_dict()
        return
    # Present envelope: validate but do NOT replace. Malformed envelopes
    # propagate ``LifecycleStateError`` -- the wiring contract is "no
    # silent downgrade, ever". Explicit-wins is preserved; disagreement
    # between an explicit envelope and legacy markers is silent at this
    # slice (Q2-D Slice 4 will add detection).
    validate_lifecycle_envelope(supplied)


class MemoryGraph:
    """
    A light persistent graph over SeedWorld entities.

    Storage:
      - JSONL for node payload metadata (append-only; last record per EID is canonical)
      - JSONL for edges
      - .npy for embeddings
    """

    def __init__(self, data_dir: str, embedder: Optional[Embedder] = None, sqlite_index=None) -> None:
        # Canonicalize via local variable so CodeQL sees the full
        # realpath ➜ startswith ➜ makedirs chain without attribute indirection.
        _safe_dir = os.path.realpath(data_dir)
        if not _safe_dir.startswith(os.sep) and not os.path.isabs(_safe_dir):
            raise ValueError(f"data_dir did not resolve to absolute path: {_safe_dir!r}")
        os.makedirs(_safe_dir, exist_ok=True)
        self.data_dir = _safe_dir

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
        # Local-variable chain for CodeQL taint visibility at makedirs sink.
        _emb = os.path.realpath(
            os.path.join(_safe_dir, "embeddings")
        )
        if not _emb.startswith(_safe_dir + os.sep):
            raise ValueError(f"Embeddings dir escapes data root: {_emb!r}")
        os.makedirs(_emb, exist_ok=True)
        self._emb_dir = _emb
        self._shard_writer: Optional[EmbeddingShardWriter] = None
        self._shard_reader: Optional[EmbeddingShardReader] = None
        self._init_shard_storage()

        self.world = SeedWorld()
        self.entities: Dict[int, SeedEntity] = {}

        self.traj = TrajectoryLogger(root_dir=self.data_dir)

        # Derive fixed child paths from the canonical root.
        self.meta_path = _child_path(self.data_dir, "nodes.jsonl")
        self.edges_path = _child_path(self.data_dir, "edges.jsonl")
        self.events_path = _child_path(self.data_dir, "memory_events.jsonl")

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

    def _guard(self, path: str) -> str:
        """Inline containment check — CodeQL needs visible realpath+startswith at sinks."""
        rp = os.path.realpath(path)
        base = os.path.realpath(self.data_dir)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes data root: {rp!r}")
        return rp

    def _append_jsonl(self, path: str, obj: Dict[str, Any]) -> None:
        safe = self._guard(path)
        with open(safe, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _emb_path(self, eid: int) -> str:
        return _child_path(self.data_dir, f"emb_{int(eid)}.npy")

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
        _now = _now_ts()
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
            # user filter (parity with search_by_embedding)
            if user_id is not None and str(payload.get("user_id", "")) != str(user_id):
                continue
            # Half-life decay: adjust effective score for ranking
            decay = _half_life_decay_factor(payload, _now)
            effective_score = float(sc) * decay
            out.append({
                "eid": int(eid),
                "score": effective_score,
                "raw_score": float(sc),
                "decay_factor": decay,
                "summary": str(payload.get("summary") or payload.get("text") or ""),
                "type": mtype or "memory",
                "strength": float(payload.get("strength") or 0.0),
                "confidence": float(payload.get("confidence") or 0.0),
                "step": int(payload.get("step") or payload.get("born_step") or 0),
                "ts": int(payload.get("ts") or payload.get("created_ts") or 0),
                **payload,
            })
        # Re-sort by decayed score (decay may reorder results)
        out.sort(key=lambda h: h["score"], reverse=True)
        return out

    def search_by_embedding(
        self,
        embedding: np.ndarray,
        *,
        top_k: int = 8,
        user_id: Optional[str] = None,
        min_score: Optional[float] = None,
        type_filter: Optional[List[str]] = None,
        canon_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Vector search using a pre-computed embedding vector.

        Same as search() but skips the embedding step — useful when the caller
        already has the vector (e.g. process_proposals in fabric.py).

        Args:
            embedding: Pre-computed embedding vector (any shape, will be normalized).
            top_k: Maximum results to return.
            user_id: If set, filter to memories owned by this user_id (or None for all).
            min_score: Minimum cosine similarity threshold.
            type_filter: If set, only return memories of these types.
            canon_only: If True, only return memories where payload["canon"] is True.
        """
        qv = np.asarray(embedding, dtype=np.float32).reshape(-1)
        if qv.size == 0:
            return []
        qv = self._normalize(qv)

        hits_eids: List[Tuple[int, float]] = []
        if self._cache_embeddings:
            self._ensure_index()
            if self._emb_mat is None or not self._eid_list:
                return []
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
        _now = _now_ts()
        for eid, sc in hits_eids:
            if min_score is not None and float(sc) < float(min_score):
                continue
            ent = self.entities.get(int(eid))
            if ent is None:
                continue
            payload = dict(ent.payload or {})
            # canon filter
            if canon_only and not payload.get("canon", False):
                continue
            # user filter
            if user_id is not None and str(payload.get("user_id", "")) != str(user_id):
                continue
            mtype = str(payload.get("type") or payload.get("mtype") or "")
            if type_set and mtype and mtype not in type_set:
                continue
            # Half-life decay: adjust effective score for ranking
            decay = _half_life_decay_factor(payload, _now)
            effective_score = float(sc) * decay
            out.append({
                "eid": int(eid),
                "score": effective_score,
                "raw_score": float(sc),
                "decay_factor": decay,
                "summary": str(payload.get("summary") or payload.get("text") or ""),
                "type": mtype or "memory",
                "strength": float(payload.get("strength") or 0.0),
                "confidence": float(payload.get("confidence") or 0.0),
                "step": int(payload.get("step") or payload.get("born_step") or 0),
                "ts": int(payload.get("ts") or payload.get("created_ts") or 0),
                **payload,
            })
        # Re-sort by decayed score
        out.sort(key=lambda h: h["score"], reverse=True)
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
            except Exception as e:
                log.debug("SQLite index_event skipped: %s", e)

    def _load(self) -> None:
        """
        Load nodes.jsonl as append-only log, taking the LAST record per EID as canonical.
        """
        max_eid = 0

        # Inline containment re-assertions: CodeQL traces instance
        # attributes back to the constructor's tainted data_dir param,
        # so it needs a local realpath+startswith guard before each
        # filesystem sink in this method.
        _root = os.path.realpath(self.data_dir)
        _meta = os.path.realpath(self.meta_path)
        _edges = os.path.realpath(self.edges_path)

        # Load nodes (canonical per EID)
        if _meta.startswith(_root + os.sep) and os.path.exists(_meta):
            with open(_meta, "r", encoding="utf-8") as f:
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
        if _edges.startswith(_root + os.sep) and os.path.exists(_edges):
            with open(_edges, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    self.edges.append(json.loads(line))

        # Prevent EID collisions on future spawns
        try:
            self.world._next_id = int(max_eid) + 1  # SeedWorld uses _next_id internally
        except Exception as e:
            log.debug("Could not set _next_id: %s", e)

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
            except Exception as e:
                log.debug("Could not parse pos from payload: %s", e)
        if "vel" in ent.payload:
            try:
                ent.vel = _as3(ent.payload["vel"])
            except Exception as e:
                log.debug("Could not parse vel from payload: %s", e)
        if "vel0" in ent.payload:
            try:
                ent.vel0 = _as3(ent.payload["vel0"])
            except Exception as e:
                log.debug("Could not parse vel0 from payload: %s", e)

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
            except Exception as e:
                log.debug("SQLite index_node skipped: %s", e)

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
        # === GATE A LAYER 4 — candidate refusal at node-creation primitive ===
        # First executable statement. Structural, content-blind, type-only refusal
        # of a candidate-shaped value passed as the ordinary-memory `summary`,
        # before any payload construction, world.spawn, embedding write, logging,
        # JSONL write, or self mutation. Covers every MemoryGraph creation caller
        # (ordinary ingest, identity anchors, shared writes, promotion-beneath,
        # character seeding) via this one choke. Inspects only the TYPE of
        # `summary` — never contents, metadata, tags, payload keys, provenance,
        # links, extra_payload, nested structures, or markers; the message never
        # interpolates the value.
        #
        # SCOPE (smallest brick): `summary` ONLY. UNRESOLVED / out of scope:
        # update_payload, extra_payload, links, ReferenceStore, EnvironmentStore,
        # ArchiveStore, the other direct-writer bypasses, and the parked writer
        # non-conformances. This is NOT wall completion.
        if isinstance(summary, CandidateShapedValue):
            raise TypeError("candidate-shaped value cannot be written as ordinary memory summary")
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

        # Q2-H1c: ensure every new memory row carries an explicit lifecycle
        # envelope. See module-level ``_ensure_lifecycle_envelope`` for the
        # full contract. Wiring-only slice: this does not introduce
        # lifecycle enforcement, protected collapse, review-queue joins,
        # or baton-lifecycle resolution.
        _ensure_lifecycle_envelope(payload)

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
                np.save(self._guard(self._emb_path(int(ent.eid))), emb_vec)
        else:
            # Legacy mode — per-file storage
            np.save(self._guard(self._emb_path(int(ent.eid))), emb_vec)

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
            except Exception as e:
                log.debug("SQLite index_node skipped: %s", e)

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
                except Exception as e:
                    log.debug("Trajectory log skipped: %s", e)

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
                    except Exception as e:
                        log.debug("Traj classify event write skipped: %s", e)

                except Exception as e:
                    log.debug("Trajectory classification skipped for eid=%s: %s", getattr(ent, "eid", "?"), e)

    def close(self) -> None:
        """Release shard memmaps held by this graph. Idempotent.

        Required on Windows before the data directory can be removed:
        numpy memmap objects in the embedding shard writer/reader hold
        OS file handles open until explicitly released.
        """
        if self._shard_writer is not None:
            self._shard_writer.close()
        if self._shard_reader is not None:
            self._shard_reader.close()

    def __enter__(self) -> "MemoryGraph":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
