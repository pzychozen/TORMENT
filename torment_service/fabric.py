# fabric.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import os, time, json, re, threading, uuid, logging, math
import numpy as np

from fastapi import HTTPException

from .memory_kernel import TriOctaMemoryKernel
from .memory_graph import MemoryGraph
from .identity import IdentityStore, AgentIdentity, DEFAULT_AGENT_SEED, DEFAULT_AGENT_OVERLAY
from .motifs import MotifRegistry, cosine as cos_sim
from .router import DomainRouter, DEFAULT_DOMAINS, SINGLE_AGENT_DOMAIN
from .domain_policies import DEFAULT_DOMAIN_POLICIES
from .bridges import BridgeRegistry
from .proposals import ProposalRegistry
from .conflicts import ConflictRegistry
from .scoring import score_hit
from .embeddings import build_embedder_from_env, Embedder, embedding_checksum
from .resonance import append_symbol, summarize_resonance
from .coherence_field import compute_coherence_field
from .symbols import assign_symbol_state, update_symbol_trace
from .affect import classify_affect, looks_personal
from .roles import RoleStore, dominant_role, role_multipliers
from .character import (
    CharacterSeed, CharacterState, CharacterStore,
    plant_seed, measure_drift, gravity_correction,
    assemble_character_context, derive_kernel_modulation,
)
from .agent_locks import AgentLockManager
from .checkpoint import (
    save_checkpoint, load_latest_checkpoint, restore_from_checkpoint,
    get_checkpoint_dir, serialize_model_state, serialize_corridor_monitor,
    build_motif_summary, build_shard_snapshot,
)

log = logging.getLogger("torment.fabric")

class _JobCancelled(Exception):
    pass



def _proposal_allowed(
    ident: "AgentIdentity",
    domain_policy: Dict[str, Any],
    created_motif: Optional[str],
    promotion_score: float,
    strength: float,
    confidence: float,
    tri_mod: Optional[Dict[str, float]] = None,
) -> bool:
    """Rate-limit + novelty filter for auto-proposals.

    This function is intentionally conservative: auto-proposals should be rare,
    high-signal, and not spammy. It combines:
      - per-agent rate limiting (window + min-gap),
      - optional novelty gating (created motif or novelty_bias),
      - minimum signal thresholds (promotion/strength/confidence),
      - optional TriOcta modulation (bounded multiplier).
    """
    now = _now_ts()
    overlay = ident.overlay

    # signal thresholds (per-domain knobs)
    min_p = float(domain_policy.get("auto_propose_min_promotion", 0.78))
    min_s = float(domain_policy.get("auto_propose_min_strength", 0.80))
    min_c = float(domain_policy.get("auto_propose_min_confidence", 0.70))

    # TriOcta modulation (bounded multiplier)
    tri_mod = tri_mod or {}
    proposal_mult = float(tri_mod.get("proposal_mult", 1.0))  # expected ~0.9..1.1
    proposal_mult = float(np.clip(proposal_mult, 0.90, 1.10))
    min_p *= proposal_mult
    min_s *= proposal_mult
    min_c *= proposal_mult

    # rate limit: max N proposals per window, min gap between proposals
    win = 600
    max_in_win = int(domain_policy.get(
        "auto_propose_max_per_window",
        overlay.get("auto_propose_max_per_window", 5),
    ))
    min_gap = int(domain_policy.get(
        "auto_propose_min_gap_s",
        overlay.get("auto_propose_min_gap_s", 15),
    ))
    wstart = int(overlay.get("auto_propose_window_start_ts", 0) or 0)
    wcount = int(overlay.get("auto_propose_window_count", 0) or 0)
    last_ts = int(overlay.get("auto_propose_last_ts", 0) or 0)

    if last_ts and (now - last_ts) < min_gap:
        return False
    if not wstart or (now - wstart) > win:
        wstart, wcount = now, 0
    if wcount >= max_in_win:
        return False

    # novelty filter: optional per-domain requirement
    novelty_bias = float(overlay.get("novelty_bias", 0.5))
    require_novel = bool(domain_policy.get("auto_propose_require_novelty", False))
    is_novel = (created_motif is not None) or (novelty_bias >= 0.55)

    if require_novel and not is_novel:
        return False
    # if not novel, demand higher promotion score
    if (not is_novel) and float(promotion_score) < 0.88:
        return False

    # signal gate
    if not ((float(promotion_score) >= min_p) or (float(strength) >= min_s and float(confidence) >= min_c)):
        return False

    # pass: record counters (caller should persist ident)
    overlay["auto_propose_window_start_ts"] = wstart
    overlay["auto_propose_window_count"] = wcount + 1
    overlay["auto_propose_last_ts"] = now
    return True



def _tokenize(s: str) -> List[str]:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    toks = [t for t in s.split() if len(t) >= 3]
    stop = {"this","that","with","from","have","were","been","then","than","into","over","under","your","their","about","because"}
    return [t for t in toks if t not in stop]


def _detect_canon_conflict(new_summary: str, old_summary: str, sim: float) -> Tuple[bool, float, str]:
    """Heuristic conflict detection without a language model.

    We only fire conflicts when similarity is high (same topic) but summaries appear
    to disagree via negation mismatch or explicit contrast markers.
    """
    if sim < 0.88:
        return (False, 0.0, "")
    ns = (new_summary or "").lower()
    os_ = (old_summary or "").lower()
    neg_words = ["not", "no", "never", "cannot", "can't", "won't", "doesn't", "isn't", "aren't", "wasn't", "weren't"]
    new_neg = any(w in ns for w in neg_words)
    old_neg = any(w in os_ for w in neg_words)
    neg_mismatch = (new_neg != old_neg)

    contrast = any(w in ns for w in ["however", "but", "except"]) or any(w in os_ for w in ["however", "but", "except"])

    a = set(_tokenize(new_summary))
    b = set(_tokenize(old_summary))
    if not a or not b:
        return (False, 0.0, "")
    j = len(a & b) / max(1, len(a | b))

    # conflict score: requires topic overlap, boosted by negation mismatch or contrast markers
    boost = 0.0
    reason = ""
    if neg_mismatch:
        boost += 0.7
        reason = "negation_mismatch"
    if contrast:
        boost += 0.2
        reason = reason or "contrast_marker"
    score = float(min(1.0, j * (0.3 + boost)))
    is_conflict = (j >= 0.18) and (boost >= 0.7)  # require negation mismatch
    return (is_conflict, score, reason)

def _now_ts() -> int:
    return int(time.time())


def _embed_audit_path(data_dir: str, workspace_id: str) -> str:
    _validate_path_component(workspace_id, "workspace_id")
    return os.path.normpath(os.path.join(data_dir, "workspaces", workspace_id, "embed_audit.json"))


def _write_embed_audit(
    data_dir: str,
    workspace_id: str,
    counts: Dict[str, Any],
    graphs_scanned: int,
    total_nodes: int,
    *,
    dirty: bool,
    lock: Optional[Dict[str, Any]] = None,
    embedder: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist last-known embedding health for a workspace.

    This is a fast index for UIs and operators; it avoids requiring a full scan to show
    basic health state. Counts are authoritative only when dirty==False.
    """
    path = _embed_audit_path(data_dir, workspace_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload: Dict[str, Any] = {
        "workspace_id": workspace_id,
        "updated_ts": _now_ts(),
        "dirty": bool(dirty),
        "graphs_scanned": int(graphs_scanned),
        "total_nodes": int(total_nodes),
        "counts": counts,
    }
    if lock is not None:
        payload["lock"] = lock
    if embedder is not None:
        payload["embedder"] = embedder
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _mark_embed_audit_dirty(data_dir: str, workspace_id: str) -> None:
    """Mark workspace audit as dirty (stale) after ingest changes.

    Best-effort: we do not attempt incremental counter updates (too easy to get wrong).
    """
    path = _embed_audit_path(data_dir, workspace_id)
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        payload["dirty"] = True
        payload["updated_ts"] = _now_ts()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        return


def _anchor_state_path(data_dir: str, workspace_id: str, agent_id: str) -> str:
    return os.path.join(data_dir, "workspaces", workspace_id, "agents", agent_id, "anchors.json")


def _load_anchor_state(data_dir: str, workspace_id: str, agent_id: str) -> Dict[str, Any]:
    """Load per-agent auto-anchor bookkeeping.

    Structure (best-effort):
      {"motifs": {motif_id: {"last_step": int, "count_at_create": int, "last_eid": int}}}
    """
    p = _anchor_state_path(data_dir, workspace_id, agent_id)
    if not os.path.exists(p):
        return {"motifs": {}}
    try:
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            return {"motifs": {}}
        obj.setdefault("motifs", {})
        if not isinstance(obj.get("motifs"), dict):
            obj["motifs"] = {}
        return obj
    except Exception:
        return {"motifs": {}}


def _save_anchor_state(data_dir: str, workspace_id: str, agent_id: str, state: Dict[str, Any]) -> None:
    p = _anchor_state_path(data_dir, workspace_id, agent_id)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, p)


def _symbol_state_path(data_dir: str, workspace_id: str, agent_id: str) -> str:
    _validate_path_component(workspace_id, "workspace_id")
    _validate_path_component(agent_id, "agent_id")
    return os.path.normpath(os.path.join(data_dir, "workspaces", workspace_id, "agents", agent_id, "symbol_state.json"))


def _load_symbol_state(data_dir: str, workspace_id: str, agent_id: str) -> Dict[str, Any]:
    p = _symbol_state_path(data_dir, workspace_id, agent_id)
    defaults = {"last_symbol": "", "symbol_trace": [], "last_motif_id": "", "last_tension": 0.0}
    if not os.path.exists(p):
        return dict(defaults)
    try:
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            return dict(defaults)
        return {
            "last_symbol": str(obj.get("last_symbol", "") or ""),
            "symbol_trace": list(obj.get("symbol_trace", []) or []),
            "last_motif_id": str(obj.get("last_motif_id", "") or ""),
            "last_tension": float(obj.get("last_tension", 0.0) or 0.0),
        }
    except Exception:
        return dict(defaults)


def _save_symbol_state(data_dir: str, workspace_id: str, agent_id: str, state: Dict[str, Any]) -> None:
    p = _symbol_state_path(data_dir, workspace_id, agent_id)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, p)

class Workspace:
    def __init__(self, data_dir: str, workspace_id: str, kernel: TriOctaMemoryKernel,
                 requested_domains: Optional[List[str]] = None) -> None:
        self.data_dir = os.path.normpath(data_dir)
        self.workspace_id = workspace_id
        self.kernel = kernel
        self.meta = self._load_or_init_meta()
        self.embed_dim = int(self.meta.get("embed_dim") or int(getattr(kernel.embedder, "dim", 0) or 0))
        # Hard safety: dimension mismatch is not allowed.
        if int(getattr(kernel.embedder, "dim", 0) or 0) and int(self.embed_dim) != int(kernel.embedder.dim):
            raise ValueError(
                f"Workspace '{workspace_id}' is locked to embed_dim={self.embed_dim}, "
                f"but current embedder provides dim={kernel.embedder.dim}."
            )
        self.domains = self._load_or_init_domains(requested_domains=requested_domains)

        # shared stores per domain (created before motif_regs so shard readers are available)
        self.shared_graphs: Dict[str, MemoryGraph] = {}
        for d in self.domains:
            dom_dir = os.path.join(data_dir, "workspaces", workspace_id, "domains", d, "shared")
            self.shared_graphs[d] = MemoryGraph(data_dir=dom_dir, embedder=kernel.embedder)

        self.motif_regs: Dict[str, MotifRegistry] = {
            d: MotifRegistry(
                data_dir=data_dir, workspace_id=workspace_id, domain_id=d,
                shard_reader=self.shared_graphs[d]._shard_reader if d in self.shared_graphs else None,
                entity_payload_fn=lambda eid, _d=d: self._entity_payload_for_motif(eid, _d),
            ) for d in self.domains
        }
        self.router = DomainRouter(self.motif_regs, embed_dim=int(self.embed_dim))
        self.bridges = BridgeRegistry(data_dir=data_dir, workspace_id=workspace_id)


        # share proposals per domain (private-write, shared-read default; shared-write via proposals)
        self.proposals: Dict[str, ProposalRegistry] = {
            d: ProposalRegistry(data_dir=data_dir, workspace_id=workspace_id, domain_id=d) for d in self.domains
        }

        # canon conflicts per domain
        self.conflicts: Dict[str, ConflictRegistry] = {
            d: ConflictRegistry(data_dir=data_dir, workspace_id=workspace_id, domain_id=d) for d in self.domains
        }

        # domain suggestions (emergent suggestions require admin approval later)
        self.domain_suggestions_path = os.path.normpath(os.path.join(data_dir, "workspaces", workspace_id, "domain_suggestions.json"))
        os.makedirs(os.path.dirname(self.domain_suggestions_path), exist_ok=True)

        # per-domain policy knobs (throttles, governance, peeks)
        self.domain_policies_path = os.path.normpath(os.path.join(data_dir, "workspaces", workspace_id, "domain_policies.json"))
        self.domain_policies = self._load_or_init_domain_policies()

        # collective kernel placeholder (domain kernels would live here later)
        self.collective_state: Dict[str, Any] = {}

    def _entity_payload_for_motif(self, eid: int, domain_id: str) -> Optional[Dict[str, Any]]:
        """Lookup entity payload by eid for motif embedding resolution."""
        # Check shared graph for this domain first
        sg = self.shared_graphs.get(domain_id)
        if sg:
            ent = sg.entities.get(int(eid))
            if ent:
                return getattr(ent, "payload", {}) or {}
        return {}

    def _meta_path(self) -> str:
        return os.path.normpath(os.path.join(self.data_dir, "workspaces", self.workspace_id, "workspace_meta.json"))

    def _load_or_init_meta(self) -> Dict[str, Any]:
        p = self._meta_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f) or {}
            except Exception:
                return {}
        meta = {
            "workspace_id": self.workspace_id,
            "created_ts": _now_ts(),
            "embed_dim": int(getattr(self.kernel.embedder, "dim", 0) or 0),
            "embed_provider": str(getattr(self.kernel.embedder, "provider", "")),
            "embed_model": str(getattr(self.kernel.embedder, "model", "")),
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, sort_keys=True)
        return meta

    def _domains_path(self) -> str:
        return os.path.normpath(os.path.join(self.data_dir, "workspaces", self.workspace_id, "domains.json"))

    def _load_or_init_domains(self, requested_domains: Optional[List[str]] = None) -> List[str]:
        p = self._domains_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            # Workspace already exists — load existing domains
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
            existing = list(obj.get("domains", [SINGLE_AGENT_DOMAIN]))
            # If new domains requested, add any missing ones (never remove)
            if requested_domains:
                added = False
                for d in requested_domains:
                    if d not in existing:
                        existing.append(d)
                        added = True
                if added:
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump({"domains": existing}, f, indent=2)
            return existing
        # New workspace — use requested domains or single-agent default.
        # For multi-agent hive-mind, pass domains explicitly (e.g. DEFAULT_DOMAINS).
        domains = list(requested_domains) if requested_domains else [SINGLE_AGENT_DOMAIN]
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"domains": domains}, f, indent=2)
        return domains

    def _load_or_init_domain_policies(self) -> Dict[str, Any]:
        p = self.domain_policies_path
        os.makedirs(os.path.dirname(p), exist_ok=True)
        pol = {}
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                pol = obj.get("policies", {}) or {}
            except Exception:
                pol = {}
        outpol: Dict[str, Any] = {}
        for d in self.domains:
            outpol[d] = dict(pol.get(d) or DEFAULT_DOMAIN_POLICIES.get(d) or DEFAULT_DOMAIN_POLICIES["research"])
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"policies": outpol}, f, indent=2, sort_keys=True)
        return outpol

    def add_domain(self, domain_id: str) -> None:
        domain_id = domain_id.strip()
        if not domain_id:
            return
        if domain_id in self.domains:
            return
        self.domains.append(domain_id)
        # persist domains
        with open(self._domains_path(), "w", encoding="utf-8") as f:
            json.dump({"domains": self.domains}, f, indent=2)
        # instantiate registries and stores (shared graph first so shard reader is available)
        dom_dir = os.path.normpath(os.path.join(self.data_dir, "workspaces", self.workspace_id, "domains", domain_id, "shared"))
        self.shared_graphs[domain_id] = MemoryGraph(data_dir=dom_dir, embedder=self.kernel.embedder)
        self.motif_regs[domain_id] = MotifRegistry(
            data_dir=self.data_dir, workspace_id=self.workspace_id, domain_id=domain_id,
            shard_reader=self.shared_graphs[domain_id]._shard_reader,
            entity_payload_fn=lambda eid, _d=domain_id: self._entity_payload_for_motif(eid, _d),
        )
        self.proposals[domain_id] = ProposalRegistry(data_dir=self.data_dir, workspace_id=self.workspace_id, domain_id=domain_id)
        self.conflicts[domain_id] = ConflictRegistry(data_dir=self.data_dir, workspace_id=self.workspace_id, domain_id=domain_id)
        # ensure a policy exists
        if hasattr(self, "domain_policies"):
            self.domain_policies[domain_id] = dict(DEFAULT_DOMAIN_POLICIES.get(domain_id, DEFAULT_DOMAIN_POLICIES["research"]))
            with open(self.domain_policies_path, "w", encoding="utf-8") as f:
                json.dump({"policies": self.domain_policies}, f, indent=2, sort_keys=True)
        # update router
        self.router = DomainRouter(self.motif_regs, embed_dim=int(self.embed_dim))

def _validate_path_component(value: str, label: str = "identifier") -> str:
    """Reject path traversal characters in user-provided identifiers.

    Raises HTTPException(400) if the value contains '/', '\\', or '..'.
    Returns the value unchanged for valid inputs.
    """
    if ".." in value or "/" in value or "\\" in value:
        raise HTTPException(status_code=400, detail=f"Invalid {label}: must not contain path separators or '..'")
    return value


class TormentFabric:

    @staticmethod
    def _agent_key(workspace_id: str, agent_id: str) -> str:
        """Composite key for all per-agent in-memory dicts.

        Ensures agent "atlas" in workspace "Entity" and agent "atlas" in
        workspace "Entity3" never collide.  Every dict keyed by agent scope
        (private_graphs, agent_states, _phase_timers, _deep_stores, etc.)
        MUST use this helper — never bare ``agent_id``.
        """
        return f"{workspace_id}/{agent_id}"

    def __init__(self, data_dir: str) -> None:
        self.data_dir = os.path.normpath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        # v1.10: embedder is configured via env and attached to the kernel.
        self.embedder_error: str = ""
        self.requested_embed_provider: str = str(os.environ.get("TORMENT_EMBED_PROVIDER") or "hash")
        self.requested_embed_model: str = str(os.environ.get("TORMENT_EMBED_MODEL") or "")
        strict = str(os.environ.get("TORMENT_EMBED_STRICT") or "").strip() in ("1", "true", "yes", "on")
        try:
            self.embedder: Embedder = build_embedder_from_env()
        except Exception as e:
            self.embedder_error = f"{type(e).__name__}: {e}"
            if strict:
                raise
            # Degraded mode: fall back to deterministic hash so the service can still start.
            from .embeddings import HashEmbedding
            self.embedder = HashEmbedding()
        self.kernel = TriOctaMemoryKernel(embedder=self.embedder)  # base kernel template
        self.ident_store = IdentityStore(data_dir=self.data_dir)
        self.role_store = RoleStore(data_dir=self.data_dir)
        self.character_store = CharacterStore(data_dir=self.data_dir)
        self._character_enable = str(os.environ.get("TORMENT_CHARACTER_ENABLE", "1")).strip().lower() in ("1", "true", "yes", "on")
        self._character_drift_every = int(os.environ.get("TORMENT_CHARACTER_DRIFT_CHECK_EVERY", "25"))

        self.workspaces: Dict[str, Workspace] = {}
        self.agent_states: Dict[str, Any] = {}  # _agent_key(ws, agent) -> TriOcta ModelState

        # SQLite sidecar index (Phase 4) — optional, non-blocking
        self._sqlite_enable = str(os.environ.get("TORMENT_SQLITE_INDEX_ENABLE", "1")).strip().lower() in ("1", "true", "yes", "on")
        self._sqlite_indexes: Dict[str, Any] = {}  # "workspace/agent" -> IndexManager

        # Checkpoint system (Phase 5) — periodic state snapshots
        self._checkpoint_enable = str(os.environ.get("TORMENT_CHECKPOINT_ENABLE", "1")).strip().lower() in ("1", "true", "yes", "on")
        self._checkpoint_interval = int(os.environ.get("TORMENT_CHECKPOINT_INTERVAL", "500"))
        self._checkpoint_max_keep = int(os.environ.get("TORMENT_CHECKPOINT_MAX_KEEP", "10"))

        # Event-gated compression (Phase 6) — disabled by default
        self._compress_enable = str(os.environ.get("TORMENT_COMPRESS_ENABLE", "0")).strip().lower() in ("1", "true", "yes", "on")
        self._compress_min_step = int(os.environ.get("TORMENT_COMPRESS_MIN_STEP", "100"))
        self._event_detectors: Dict[str, Any] = {}       # _agent_key -> detector
        self._compression_executors: Dict[str, Any] = {}  # _agent_key -> executor
        self._deep_stores: Dict[str, Any] = {}            # _agent_key -> store
        self._phase_timers: Dict[str, Any] = {}            # _agent_key -> PhaseTimer

        # SRG living memory (opt-in) — disabled by default
        self._srg_enable = str(os.environ.get("TORMENT_SRG_ENABLE", "0")).strip().lower() in ("1", "true", "yes", "on")

        # Hivemind collective resonance (opt-in) — disabled by default
        self._hivemind_enable = str(os.environ.get("TORMENT_HIVEMIND_ENABLE", "0")).strip().lower() in ("1", "true", "yes", "on")
        self._collective_fields: Dict[str, Any] = {}  # workspace_id -> CollectiveField (lazy init)
        self._proposal_bridges: Dict[str, Any] = {}  # workspace_id -> CollectiveProposalBridge (lazy init)

        # private memory stores per agent
        self.private_graphs: Dict[str, MemoryGraph] = {}  # _agent_key(ws, agent) -> graph

        # Per-agent and per-workspace serialization (Phase 0 — MCP prep)
        self.locks = AgentLockManager()

        # workspace clone controls (v1.10.4)
        self._clone_mutex = threading.Lock()
        self._clone_jobs: Dict[str, Dict[str, Any]] = {}
        self._last_clone_ts: float = 0.0
        self._clone_min_gap_s: float = float(os.environ.get("TORMENT_CLONE_MIN_GAP_S") or 0)
        self._clone_log_every: int = int(os.environ.get("TORMENT_CLONE_LOG_EVERY") or 250)
        self._log = logging.getLogger("torment.clone")
        # workspace repair controls (v1.10.8)
        self._repair_jobs: Dict[str, Dict[str, Any]] = {}
        self._repair_log = logging.getLogger("torment.repair")

        # job retention + persistence (v1.10.10)
        self._job_max: int = int(os.environ.get('TORMENT_JOB_MAX') or 50)
        self._job_persist: bool = str(os.environ.get('TORMENT_JOB_PERSIST') or '').strip().lower() in ('1','true','yes','on')
        self._jobs_root: str = os.path.join(self.data_dir, 'jobs')
        if self._job_persist:
            os.makedirs(os.path.join(self._jobs_root, 'clone'), exist_ok=True)
            os.makedirs(os.path.join(self._jobs_root, 'repair'), exist_ok=True)
            self._load_jobs('clone')
            self._load_jobs('repair')



    def _get_sqlite_index(self, workspace_id: str, agent_id: str):
        """Get or create a SQLite IndexManager for an agent (Phase 4).

        Returns None if SQLite indexing is disabled or init fails.
        Failure is always non-fatal.
        """
        if not self._sqlite_enable:
            return None
        key = f"{workspace_id}/{agent_id}"
        if key not in self._sqlite_indexes:
            try:
                from .sqlite_index import IndexManager
                index_dir = os.path.join(
                    self.data_dir, "workspaces", workspace_id,
                    "agents", agent_id, "index",
                )
                self._sqlite_indexes[key] = IndexManager(index_dir)
            except Exception:
                self._sqlite_indexes[key] = None
        return self._sqlite_indexes[key]

    def get_workspace(self, workspace_id: str, domains: Optional[List[str]] = None) -> Workspace:
        _validate_path_component(workspace_id, "workspace_id")
        ws = self.workspaces.get(workspace_id)
        if ws is None:
            try:
                ws = Workspace(data_dir=self.data_dir, workspace_id=workspace_id,
                               kernel=self.kernel, requested_domains=domains)
            except ValueError as e:
                # Dim mismatch safety.
                raise HTTPException(status_code=409, detail=str(e))
            self.workspaces[workspace_id] = ws
        elif domains:
            # Workspace exists in memory — ensure requested domains are present
            added = False
            for d in domains:
                if d not in ws.domains:
                    # Add domain infrastructure
                    dom_dir = os.path.join(self.data_dir, "workspaces", workspace_id, "domains", d, "shared")
                    ws.shared_graphs[d] = MemoryGraph(data_dir=dom_dir, embedder=self.kernel.embedder)
                    ws.motif_regs[d] = MotifRegistry(
                        data_dir=self.data_dir, workspace_id=workspace_id, domain_id=d,
                        shard_reader=ws.shared_graphs[d]._shard_reader,
                        entity_payload_fn=lambda eid, _d=d: ws._entity_payload_for_motif(eid, _d),
                    )
                    ws.proposals[d] = ProposalRegistry(
                        data_dir=self.data_dir, workspace_id=workspace_id, domain_id=d)
                    ws.conflicts[d] = ConflictRegistry(
                        data_dir=self.data_dir, workspace_id=workspace_id, domain_id=d)
                    ws.domains.append(d)
                    added = True
            if added:
                # Persist updated domain list
                p = ws._domains_path()
                with open(p, "w", encoding="utf-8") as f:
                    json.dump({"domains": ws.domains}, f, indent=2)
                # Rebuild router with new motif registries
                ws.router = DomainRouter(ws.motif_regs, embed_dim=int(ws.embed_dim))
        return ws

    def list_workspaces_meta(self) -> List[Dict[str, Any]]:
        """Return persisted workspace embedding locks and basic metadata.

        Reads from data/workspaces/<workspace_id>/workspace_meta.json.
        Safe for large numbers of workspaces; returns empty list if none exist.
        """
        ws_root = os.path.join(self.data_dir, "workspaces")
        if not os.path.exists(ws_root):
            return []
        out: List[Dict[str, Any]] = []
        for name in sorted(os.listdir(ws_root)):
            p = os.path.join(ws_root, name, "workspace_meta.json")
            if not os.path.exists(p):
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    meta = json.load(f) or {}
            except Exception:
                meta = {}
            out.append({
                "workspace_id": str(meta.get("workspace_id") or name),
                "created_ts": int(meta.get("created_ts") or 0),
                "embed_dim": int(meta.get("embed_dim") or 0),
                "embed_provider": str(meta.get("embed_provider") or ""),
                "embed_model": str(meta.get("embed_model") or ""),
            })
        return out

    # ---- job persistence helpers (v1.10.10) ----
    def _job_path(self, kind: str, job_id: str) -> str:
        return os.path.normpath(os.path.join(self._jobs_root, kind, f"{job_id}.json"))

    def _load_jobs(self, kind: str) -> None:
        """Load persisted jobs from disk into in-memory stores.

        Any job that was 'running' at shutdown is marked 'abandoned'.
        """
        if not self._job_persist:
            return
        store = self._clone_jobs if kind == 'clone' else self._repair_jobs
        root = os.path.join(self._jobs_root, kind)
        if not os.path.isdir(root):
            return
        for fn in sorted(os.listdir(root)):
            if not fn.endswith('.json'):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    st = json.load(f) or {}
            except Exception:
                continue
            job_id = str(st.get('job_id') or fn[:-5])
            st['job_id'] = job_id
            if st.get('status') == 'running':
                st['status'] = 'abandoned'
                st['phase'] = 'abandoned'
                st['error'] = st.get('error') or 'abandoned (server restarted)'
                st['updated_ts'] = time.time()
                try:
                    with open(p, 'w', encoding='utf-8') as f:
                        json.dump(st, f, indent=2, sort_keys=True)
                except Exception as e:
                    self._log.debug("Job state write failed: %s", e)
            store[job_id] = st
        self._prune_jobs(kind)

    def _persist_job(self, kind: str, job_id: str) -> None:
        if not self._job_persist:
            return
        store = self._clone_jobs if kind == 'clone' else self._repair_jobs
        st = store.get(job_id)
        if not st:
            return
        p = self._job_path(kind, job_id)
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(st, f, indent=2, sort_keys=True)
        except Exception as e:
            self._log.debug("Job persist failed: %s", e)

    def _prune_jobs(self, kind: str) -> None:
        """Keep only the most recent N jobs (by started_ts) in memory and on disk."""
        n = int(self._job_max or 0)
        if n <= 0:
            return
        store = self._clone_jobs if kind == 'clone' else self._repair_jobs
        items = sorted(store.items(), key=lambda kv: float(kv[1].get('started_ts', 0) or 0), reverse=True)
        keep = dict(items[:n])
        drop = [jid for jid,_ in items[n:]]
        for jid in drop:
            store.pop(jid, None)
            if self._job_persist:
                try:
                    os.remove(self._job_path(kind, jid))
                except Exception as e:
                    self._log.debug("Job file removal failed: %s", e)




    # ---- clone job inspection (v1.10.4) ----
    def list_clone_jobs(self) -> List[Dict[str, Any]]:
        """List recent clone jobs (in-memory)."""
        out: List[Dict[str, Any]] = []
        for jid, st in sorted(self._clone_jobs.items(), key=lambda kv: float(kv[1].get("started_ts", 0)), reverse=True):
            out.append({
                "job_id": jid,
                "status": st.get("status", ""),
                "phase": st.get("phase", ""),
                "source_workspace_id": st.get("source_workspace_id", ""),
                "target_workspace_id": st.get("target_workspace_id", ""),
                "started_ts": st.get("started_ts", 0),
                "updated_ts": st.get("updated_ts", 0),
                "progress": st.get("progress", {}),
                "error": st.get("error", ""),
                "cancel_requested": bool(st.get("cancel_requested")),
            })
        return out

    def get_clone_job(self, job_id: str) -> Dict[str, Any]:
        st = self._clone_jobs.get(job_id)
        if st is None:
            raise HTTPException(status_code=404, detail=f"Unknown clone job_id '{job_id}'")
        return st


    # ---- repair job inspection (v1.10.8) ----
    def list_repair_jobs(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for jid, st in sorted(self._repair_jobs.items(), key=lambda kv: float(kv[1].get("started_ts", 0)), reverse=True):
            out.append({
                "job_id": jid,
                "status": st.get("status", ""),
                "phase": st.get("phase", ""),
                "workspace_id": st.get("workspace_id", ""),
                "mode": st.get("mode", ""),
                "started_ts": st.get("started_ts", 0),
                "updated_ts": st.get("updated_ts", 0),
                "progress": st.get("progress", {}),
                "error": st.get("error", ""),
                "cancel_requested": bool(st.get("cancel_requested")),
            })
        return out

    def get_repair_job(self, job_id: str) -> Dict[str, Any]:
        st = self._repair_jobs.get(job_id)
        if st is None:
            raise HTTPException(status_code=404, detail=f"Unknown repair job_id '{job_id}'")
        return st


    def cancel_repair_job(self, job_id: str) -> Dict[str, Any]:
        st = self._repair_jobs.get(job_id)
        if st is None:
            raise HTTPException(status_code=404, detail=f"Unknown repair job_id '{job_id}'")
        if st.get('status') not in ('running',):
            return {"ok": True, "job_id": job_id, "status": st.get('status'), "message": "not running"}
        st['cancel_requested'] = True
        st['updated_ts'] = time.time()
        self._persist_job('repair', job_id)
        return {"ok": True, "job_id": job_id, "status": "cancelling"}

    def start_repair_embeddings_job(
        self,
        workspace_id: str,
        mode: str = "scan",
        include_private: bool = True,
        include_shared: bool = True,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Start an async scan/repair job and return job_id.

        Uses the same heavy-op mutex as clone to prevent concurrent I/O storms.
        """
        # Prevent concurrent heavy operations.
        if not self._clone_mutex.acquire(blocking=False):
            raise HTTPException(status_code=429, detail="Another heavy workspace operation is already in progress")

        job_id = uuid.uuid4().hex[:12]
        st: Dict[str, Any] = {
            "job_id": job_id,
            "status": "running",
            "phase": "starting",
            "workspace_id": workspace_id,
            "mode": mode,
            "started_ts": time.time(),
            "updated_ts": time.time(),
            "progress": {},
            "error": "",
            "result": None,
            "cancel_requested": False,
            "cancelled_ts": 0,
        }
        self._repair_jobs[job_id] = st
        self._persist_job('repair', job_id)
        self._prune_jobs('repair')

        def _run() -> None:
            try:
                st["phase"] = "running"
                st["updated_ts"] = time.time()

                def _progress_cb(p: Dict[str, Any]) -> None:
                    st["progress"] = p
                    st["updated_ts"] = time.time()
                    self._persist_job('repair', job_id)
                    self._persist_job('repair', job_id)

                res = self._repair_embeddings_impl(
                    workspace_id=workspace_id,
                    mode=mode,
                    include_private=include_private,
                    include_shared=include_shared,
                    limit=limit,
                    progress_cb=_progress_cb,
                    cancel_check=lambda: bool(st.get("cancel_requested")),
                )
                st["status"] = "done"
                st["phase"] = "done"
                st["result"] = res
                st["updated_ts"] = time.time()

            except _JobCancelled as e:
                st["status"] = "cancelled"
                st["phase"] = "cancelled"
                st["error"] = str(e) or "cancelled"
                st["cancelled_ts"] = time.time()
                st["updated_ts"] = time.time()
            except Exception as e:
                st["status"] = "error"
                st["phase"] = "error"
                st["error"] = f"{type(e).__name__}: {e}"
                st["updated_ts"] = time.time()
            finally:
                self._persist_job('repair', job_id)
                self._prune_jobs('repair')
                try:
                    self._clone_mutex.release()
                except Exception as e:
                    self._log.debug("Mutex release failed: %s", e)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return {"ok": True, "job_id": job_id, "status": "running"}







    def repair_embeddings(
        self,
        workspace_id: str,
        mode: str = "scan",
        include_private: bool = True,
        include_shared: bool = True,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Synchronous scan/repair embeddings (legacy endpoint).

        For large workspaces, prefer the async job endpoint which calls the same implementation.
        """
        _validate_path_component(workspace_id, "workspace_id")
        # Prevent concurrent heavy operations.
        if not self._clone_mutex.acquire(blocking=False):
            raise HTTPException(status_code=429, detail="Another heavy workspace operation is already in progress")
        try:
            return self._repair_embeddings_impl(
                workspace_id=workspace_id,
                mode=mode,
                include_private=include_private,
                include_shared=include_shared,
                limit=limit,
                progress_cb=None,
            )
        finally:
            try:
                self._clone_mutex.release()
            except Exception:
                pass

    def _repair_embeddings_impl(
        self,
        workspace_id: str,
        mode: str = "scan",
        include_private: bool = True,
        include_shared: bool = True,
        limit: Optional[int] = None,
        progress_cb: Optional[Any] = None,
        cancel_check: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Implementation for scan/repair embeddings.

        Does NOT acquire/release the heavy-op mutex; callers must handle that.
        """
        ws = self.get_workspace(workspace_id)
        mode = (mode or "scan").strip().lower()
        if mode not in ("scan", "repair"):
            raise HTTPException(status_code=400, detail="mode must be scan|repair")

        # Enforce lock match.
        emb = getattr(self.kernel, "embedder", None)
        cur_provider = str(getattr(emb, "provider", ""))
        cur_model = str(getattr(emb, "model", ""))
        cur_dim = int(getattr(emb, "dim", 0) or 0)

        lock_provider = str(ws.meta.get("embed_provider", ""))
        lock_model = str(ws.meta.get("embed_model", ""))
        lock_dim = int(getattr(ws, "embed_dim", 0) or 0)

        if lock_dim and cur_dim and lock_dim != cur_dim:
            raise HTTPException(status_code=409, detail=f"Active embedder dim {cur_dim} does not match workspace lock {lock_dim}. Use /workspace/clone to migrate.")
        if lock_provider and cur_provider and lock_provider != cur_provider:
            raise HTTPException(status_code=409, detail=f"Active embedder provider '{cur_provider}' does not match workspace lock '{lock_provider}'. Use /workspace/clone to migrate.")
        if lock_model and cur_model and lock_model != cur_model:
            raise HTTPException(status_code=409, detail=f"Active embedder model '{cur_model}' does not match workspace lock '{lock_model}'. Use /workspace/clone to migrate.")

        ws_root = os.path.normpath(os.path.join(self.data_dir, "workspaces", workspace_id))
        if not os.path.isdir(ws_root):
            raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")

        def _iter_graph_dirs() -> List[str]:
            gdirs: List[str] = []
            agents_root = os.path.join(ws_root, "agents")
            if include_private and os.path.isdir(agents_root):
                for aid in sorted(os.listdir(agents_root)):
                    gdir = os.path.join(agents_root, aid, "private")
                    if os.path.isdir(gdir):
                        gdirs.append(gdir)
            domains_root = os.path.join(ws_root, "domains")
            if include_shared and os.path.isdir(domains_root):
                for dom in sorted(os.listdir(domains_root)):
                    gdir = os.path.join(domains_root, dom, "shared")
                    if os.path.isdir(gdir):
                        gdirs.append(gdir)
            return gdirs

        counts = {
            "graphs": 0,
            "nodes": 0,
            "stale_total": 0,
            "missing": 0,
            "unreadable": 0,
            "wrong_dim": 0,
            "no_checksum": 0,
            "checksum_mismatch": 0,
            "repaired": 0,
            "skipped": 0,
        }
        per_graph: List[Dict[str, Any]] = []
        max_nodes = int(limit) if limit is not None else None
        processed = 0

        graph_dirs = _iter_graph_dirs()
        total_graphs = len(graph_dirs)

        def _push_progress(current_graph: str = "", idx_graph: int = 0) -> None:
            if progress_cb is None:
                return
            progress_cb({
                "mode": mode,
                "graph_index": idx_graph,
                "graph_total": total_graphs,
                "current_graph": current_graph,
                "processed_nodes": processed,
                "counts": dict(counts),
            })

        self._repair_log.info("repair_embeddings start workspace=%s mode=%s graphs=%d", workspace_id, mode, total_graphs)
        _push_progress("", 0)

        for gi, gdir in enumerate(graph_dirs, start=1):
            nodes_path = os.path.join(gdir, "nodes.jsonl")
            if not os.path.exists(nodes_path):
                continue
            counts["graphs"] += 1
            gstat = {"graph": gdir, "nodes": 0, "stale": 0, "repaired": 0}
            objs: List[Dict[str, Any]] = []
            modified = False

            self._repair_log.info("repair_embeddings graph %d/%d %s", gi, total_graphs, gdir)
            _push_progress(gdir, gi)

            with open(nodes_path, "r", encoding="utf-8") as nf:
                for line in nf:
                    if cancel_check is not None and cancel_check():
                        raise _JobCancelled("cancel requested")
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    eid = int(obj.get("eid"))
                    payload = obj.get("payload", {}) or {}
                    summary = str(payload.get("summary") or payload.get("text") or "").strip()
                    if not summary:
                        summary = "(empty)"

                    expected_ck = embedding_checksum(summary, cur_provider, cur_model)
                    stored_ck = str(payload.get("embedding_checksum") or "").strip()
                    emb_path = os.path.join(gdir, f"emb_{eid}.npy")

                    stale_reason = ""
                    if not os.path.exists(emb_path):
                        stale_reason = "missing"
                    else:
                        try:
                            old = np.load(emb_path)
                            old = np.asarray(old).reshape(-1)
                            if lock_dim and int(old.shape[0]) != int(lock_dim):
                                stale_reason = "wrong_dim"
                            elif not stored_ck:
                                stale_reason = "no_checksum"
                            elif stored_ck != expected_ck:
                                stale_reason = "checksum_mismatch"
                        except Exception:
                            stale_reason = "unreadable"

                    is_stale = bool(stale_reason)
                    if is_stale:
                        counts[stale_reason] += 1
                        counts["stale_total"] += 1
                        gstat["stale"] += 1

                    if mode == "repair" and is_stale:
                        v = np.asarray(self.kernel.embedder.embed(summary), dtype=np.float32).reshape(-1)
                        if lock_dim and int(v.shape[0]) != int(lock_dim):
                            raise HTTPException(status_code=500, detail=f"Embedder returned dim {int(v.shape[0])} but workspace lock is {int(lock_dim)}")
                        np.save(emb_path, v)
                        counts["repaired"] += 1
                        gstat["repaired"] += 1

                        payload["embedding_provider"] = cur_provider
                        payload["embedding_model"] = cur_model
                        payload["embedding_dim"] = int(lock_dim or int(v.shape[0]))
                        payload["embedding_checksum"] = expected_ck
                        obj["payload"] = payload
                        modified = True
                    else:
                        counts["skipped"] += 1

                    objs.append(obj)
                    gstat["nodes"] += 1
                    counts["nodes"] += 1
                    processed += 1

                    if processed % max(1, int(self._clone_log_every)) == 0:
                        _push_progress(gdir, gi)

                    if max_nodes is not None and processed >= max_nodes:
                        break

            if modified:
                tmp = nodes_path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as wf:
                    for o in objs:
                        wf.write(json.dumps(o, ensure_ascii=False) + "\n")
                os.replace(tmp, nodes_path)

            per_graph.append(gstat)
            _push_progress(gdir, gi)

            if max_nodes is not None and processed >= max_nodes:
                break

        self._repair_log.info("repair_embeddings done workspace=%s mode=%s processed=%d", workspace_id, mode, processed)
        _push_progress("", total_graphs)

        # Persist fast workspace-level embedding health index.
        try:
            _write_embed_audit(
                self.data_dir,
                workspace_id,
                counts=counts,
                graphs_scanned=len(per_graph),
                total_nodes=processed,
                dirty=False,
                lock={"provider": lock_provider, "model": lock_model, "dim": lock_dim},
                embedder={"provider": cur_provider, "model": cur_model, "dim": cur_dim},
            )
        except Exception as e:
            self._log.debug("Embed audit write failed: %s", e)

        return {
            "ok": True,
            "workspace_id": workspace_id,
            "mode": mode,
            "lock": {"provider": lock_provider, "model": lock_model, "dim": lock_dim},
            "embedder": {"provider": cur_provider, "model": cur_model, "dim": cur_dim},
            "counts": counts,
            "graphs": per_graph,
        }


    
    def _role_context(self, ws: "Workspace", agent_id: str) -> Dict[str, Any]:
        """Return soft role context (guidance signal) for character continuity."""
        try:
            rp = self.role_store.load(ws.workspace_id, agent_id)
            r = dominant_role(rp)
            # return small payload to avoid noise
            top = sorted(((k, float(v)) for k, v in (rp.scores or {}).items()), key=lambda kv: kv[1], reverse=True)[:3]
            return {"dominant_role": r, "top_roles": [{"role": k, "score": v} for k, v in top], "samples": int(rp.samples)}
        except Exception:
            return {"dominant_role": "explorer", "top_roles": [], "samples": 0}

    def _embed_context(self, ws: "Workspace") -> Dict[str, Any]:
        """Return embedder runtime info + workspace lock info for UI/trace."""
        emb = getattr(self.kernel, "embedder", None)
        return {
            "embedder": {
                "provider": str(getattr(emb, "provider", "")),
                "model": str(getattr(emb, "model", "")),
                "dim": int(getattr(emb, "dim", 0) or 0),
            },
            "workspace_lock": {
                "workspace_id": ws.workspace_id,
                "embed_dim": int(getattr(ws, "embed_dim", 0) or 0),
                "embed_provider": str(ws.meta.get("embed_provider", "")),
                "embed_model": str(ws.meta.get("embed_model", "")),
            },
        }


    def _maybe_emit_identity_anchor(
        self,
        ws: "Workspace",
        agent_id: str,
        domain_id: str,
        step: int,
        motif_ids: List[str],
    ) -> Optional[int]:
        """Auto-detect and emit an identity anchor memory (B-mode).

        If the agent repeatedly contributes to the same motif, create a stable
        "identity_anchor" memory summarizing the recurring thread.

        We avoid in-place mutation of existing nodes (graphs are append-only).
        """
        try:
            min_count = int(os.getenv("TORMENT_ID_ANCHOR_MIN_COUNT", "3"))
            min_gap = int(os.getenv("TORMENT_ID_ANCHOR_MIN_GAP_STEPS", "50"))
            max_examples = int(os.getenv("TORMENT_ID_ANCHOR_MAX_EXAMPLES", "2"))
        except Exception:
            min_count, min_gap, max_examples = 3, 50, 2

        # Soft role inference: gently tune anchor emission aggressiveness.
        try:
            rp = self.role_store.load(ws.workspace_id, agent_id)
            r = dominant_role(rp)
            mult = role_multipliers(r)
            min_count = int(max(2, round(float(min_count) * float(mult.get("anchor_count_mult", 1.0)))))
            min_gap = int(max(10, round(float(min_gap) * float(mult.get("anchor_gap_mult", 1.0)))))
        except Exception as e:
            self._log.debug("Role store load skipped: %s", e)

        if not motif_ids:
            return None
        ak = self._agent_key(ws.workspace_id, agent_id)
        if ak not in self.private_graphs:
            return None
        g = self.private_graphs[ak]
        reg = ws.motif_regs.get(domain_id)
        if reg is None:
            return None

        state = _load_anchor_state(self.data_dir, ws.workspace_id, agent_id)
        seen = state.get("motifs", {}) or {}

        created_eid: Optional[int] = None
        for mid in motif_ids:
            m = reg.motifs.get(mid)
            if m is None:
                continue

            

            agent_member_eids = [int(eid) for eid in (m.members or []) if int(eid) in g.entities]
            agent_count = len(agent_member_eids)

            # Emotional stability: motifs that are primarily affect-toned are "affect-sensitive"
            # and should require stronger evidence before becoming identity anchors.
            affect_sensitive = False
            try:
                non_neutral = 0
                checked = 0
                for _eid in agent_member_eids[-12:]:
                    try:
                        t = str(g.entities[int(_eid)].payload.get("affect_tag") or "")
                    except Exception:
                        t = ""
                    if t:
                        checked += 1
                        if t != "neutral":
                            non_neutral += 1
                if checked >= 4 and (float(non_neutral) / float(max(1, checked))) >= 0.60:
                    affect_sensitive = True
            except Exception:
                affect_sensitive = False

            _min_count = min_count
            _min_gap = min_gap
            if affect_sensitive:
                try:
                    _min_count = int(max(2, math.ceil(float(min_count) * float(os.getenv("TORMENT_ID_ANCHOR_AFFECT_COUNT_MULT", "1.6")))))
                except Exception:
                    _min_count = int(max(2, math.ceil(float(min_count) * 1.6)))
                try:
                    _min_gap = int(max(10, math.ceil(float(min_gap) * float(os.getenv("TORMENT_ID_ANCHOR_AFFECT_GAP_MULT", "1.5")))))
                except Exception:
                    _min_gap = int(max(10, math.ceil(float(min_gap) * 1.5)))

            if agent_count < _min_count:
                continue
            prev = seen.get(mid) or {}
            last_step = int(prev.get("last_step", -10**9))
            count_at_create = int(prev.get("count_at_create", 0))
            if step - last_step < _min_gap:
                continue
            if agent_count <= max(count_at_create, min_count - 1):
                continue

            label = str(getattr(m, "label", "") or mid)
            examples: List[str] = []
            for eid in agent_member_eids[-max_examples:]:
                try:
                    examples.append(str(g.entities[int(eid)].payload.get("summary", "")).strip())
                except Exception:
                    continue
            examples = [e for e in examples if e]
            ex_txt = "" if not examples else (" Examples: " + " | ".join(examples[:max_examples]))
            anchor_summary = f"Identity anchor: recurring theme '{label}'." + ex_txt

            emb = np.asarray(self.kernel.embedder.embed(anchor_summary), dtype=np.float32)
            emb_dim = int(emb.reshape(-1).shape[0])
            if emb_dim != int(ws.embed_dim):
                continue
            emb_provider = str(getattr(self.kernel.embedder, "provider", ""))
            emb_model = str(getattr(self.kernel.embedder, "model", ""))
            emb_ck = embedding_checksum(anchor_summary, emb_provider, emb_model)

            strength = float(min(1.0, 0.55 + 0.08 * float(agent_count)))
            eid = g.add_memory(
                summary=anchor_summary,
                embedding=emb,
                mtype="identity_anchor",
                strength=strength,
                confidence=0.85,
                half_life_days=3650.0,
                links=[],
                canon=False,
                user_id=agent_id,
                step=step,
                extra_payload={
                    "workspace_id": ws.workspace_id,
                    "domain_id": domain_id,
                    "scope": "private",
                    "agent_id": agent_id,
                    "anchor_for_motif": mid,
                    "anchor_member_count": int(agent_count),
                    "anchor_label": label,
                    "anchor_affect_sensitive": bool(affect_sensitive),
                    "embedding_provider": emb_provider,
                    "embedding_model": emb_model,
                    "embedding_dim": int(emb_dim),
                    "embedding_checksum": emb_ck,
                },
            )
            created_eid = int(eid)
            _mark_embed_audit_dirty(self.data_dir, ws.workspace_id)

            # Anchor refinement: retire the previously emitted anchor for this motif (if any).
            try:
                _prev_eid = int(prev.get("last_eid", 0) or 0)
                if _prev_eid and _prev_eid != int(eid) and _prev_eid in g.entities:
                    g.update_payload(_prev_eid, {
                        "anchor_retired": True,
                        "anchor_retired_reason": "superseded",
                        "anchor_superseded_by": int(eid),
                        "last_reinforced": int(step),
                    })
            except Exception as e:
                self._log.debug("Anchor retire failed: %s", e)

            seen[mid] = {"last_step": int(step), "count_at_create": int(agent_count), "last_eid": int(eid)}
            state["motifs"] = seen
            _save_anchor_state(self.data_dir, ws.workspace_id, agent_id, state)
            break

        return created_eid

    
    def _maybe_emit_mood_drift(
        self,
        ws: "Workspace",
        agent_id: str,
        domain_id: str,
        step: int,
        affect_tag: Optional[str],
        affect_conf: Optional[float],
    ) -> Optional[int]:
        """Emotional continuity v2: emit a lightweight mood drift memory.

        This is guidance-only. It helps the agent remember changes in the user's
        recent emotional tone without dominating retrieval or defining persona.
        """
        if not affect_tag or affect_tag == "neutral":
            return None
        try:
            enable = str(os.getenv("TORMENT_MOOD_DRIFT_ENABLE", "1")).strip().lower() not in ("0", "false", "no")
        except Exception:
            enable = True
        if not enable:
            return None
        try:
            min_conf = float(os.getenv("TORMENT_MOOD_DRIFT_MIN_CONF", "0.55"))
        except Exception:
            min_conf = 0.55
        try:
            min_gap = int(os.getenv("TORMENT_MOOD_DRIFT_MIN_GAP_STEPS", "120"))
        except Exception:
            min_gap = 120

        conf = float(affect_conf or 0.0)
        if conf < min_conf:
            return None

        ak = self._agent_key(ws.workspace_id, agent_id)
        if ak not in self.private_graphs:
            return None
        g = self.private_graphs[ak]

        st = _load_affect_state(self.data_dir, ws.workspace_id, agent_id)
        last_tag = st.get("last_tag")
        last_step = int(st.get("last_step", -10**9))
        last_conf = float(st.get("last_conf", 0.0))

        # Update state regardless (best-effort) to track the latest tag.
        st["last_tag"] = str(affect_tag)
        st["last_conf"] = float(conf)
        st["last_step"] = int(step)
        _save_affect_state(self.data_dir, ws.workspace_id, agent_id, st)

        if not last_tag or last_tag == "neutral":
            return None
        if str(last_tag) == str(affect_tag):
            return None
        if int(step) - int(last_step) < int(min_gap):
            return None

        drift_summary = f"Mood drift: from {last_tag} to {affect_tag}."
        try:
            emb = np.asarray(self.kernel.embedder.embed(drift_summary), dtype=np.float32)
            emb_dim = int(emb.reshape(-1).shape[0])
            if emb_dim != int(ws.embed_dim):
                return None
            emb_provider = str(getattr(self.kernel.embedder, "provider", ""))
            emb_model = str(getattr(self.kernel.embedder, "model", ""))
            emb_ck = embedding_checksum(drift_summary, emb_provider, emb_model)
        except Exception:
            return None

        strength = float(min(1.0, 0.50 + 0.20 * conf))
        try:
            eid = g.add_memory(
                summary=drift_summary,
                embedding=emb,
                mtype="mood_drift",
                strength=strength,
                confidence=float(min(0.95, 0.6 + 0.35 * conf)),
                half_life_days=float(os.getenv("TORMENT_MOOD_DRIFT_HALF_LIFE_DAYS", "60")),
                links=[],
                canon=False,
                user_id=agent_id,
                step=int(step),
                extra_payload={
                    "workspace_id": ws.workspace_id,
                    "domain_id": domain_id,
                    "scope": "private",
                    "agent_id": agent_id,
                    "affect_tag": str(affect_tag),
                    "affect_conf": float(conf),
                    "mood_from": str(last_tag),
                    "mood_to": str(affect_tag),
                    "embedding_provider": emb_provider,
                    "embedding_model": emb_model,
                    "embedding_dim": int(emb_dim),
                    "embedding_checksum": emb_ck,
                },
            )
            


            _mark_embed_audit_dirty(self.data_dir, ws.workspace_id)
            # Record drift history for lightweight "mood spiral" hygiene.
            try:
                st2 = _load_affect_state(self.data_dir, ws.workspace_id, agent_id)
                dh = st2.get("drift_hist") or []
                if not isinstance(dh, list):
                    dh = []
                dh.append({"from": str(last_tag), "to": str(affect_tag), "step": int(step), "conf": float(conf)})
                st2["drift_hist"] = dh[-50:]
                _save_affect_state(self.data_dir, ws.workspace_id, agent_id, st2)
            except Exception as e:
                self._log.debug("Affect state save failed: %s", e)
            return int(eid)

        except Exception as e:
            self._log.debug("Mood drift emit failed: %s", e)
            return None

    def _refine_identity_anchors(self, ws: "Workspace", agent_id: str, domain_id: str, motif_ids: List[str]) -> None:
        """Anchor quality refinement.

        - Keep only the strongest anchors per motif (soft-retire the rest).
        - Optionally soft-retire weak/old anchors.
        This is strictly a memory hygiene pass; it does not enforce persona.
        """
        ak = self._agent_key(ws.workspace_id, agent_id)
        if ak not in self.private_graphs:
            return
        g = self.private_graphs[ak]
        try:
            keep_k = int(os.getenv("TORMENT_ANCHOR_KEEP_PER_MOTIF", "1"))
        except Exception:
            keep_k = 1
        try:
            weak_max = int(os.getenv("TORMENT_ANCHOR_WEAK_MEMBER_MAX", "3"))
        except Exception:
            weak_max = 3
        try:
            weak_min_age = int(os.getenv("TORMENT_ANCHOR_WEAK_MIN_AGE_STEPS", "800"))
        except Exception:
            weak_min_age = 800
        try:
            now_step = max(int(ent.payload.get("created_at", 0)) for ent in g.entities.values())
        except Exception:
            now_step = 0

        for mid in motif_ids or []:
            anchors = []
            for eid, ent in g.entities.items():
                p = ent.payload or {}
                if str(p.get("type")) != "identity_anchor":
                    continue
                if str(p.get("anchor_for_motif", "")) != str(mid):
                    continue
                if bool(p.get("anchor_retired", False)):
                    continue
                member_n = int(p.get("anchor_member_count", 0) or 0)
                step0 = int(p.get("created_at", 0) or 0)
                anchors.append((eid, member_n, step0, p))
            if not anchors:
                continue
            anchors.sort(key=lambda x: (x[1], x[2]), reverse=True)
            keep = anchors[:max(1, keep_k)]
            keep_eids = {int(x[0]) for x in keep}
            best_eid = int(keep[0][0])

            # Retire duplicates beyond keep_k.
            for (eid, member_n, step0, p) in anchors:
                if int(eid) in keep_eids:
                    continue
                try:
                    g.update_payload(int(eid), {
                        "anchor_retired": True,
                        "anchor_retired_reason": "superseded",
                        "anchor_superseded_by": int(best_eid),
                        "anchor_merged_into": int(best_eid),
                        "last_reinforced": int(now_step),
                    })
                except Exception as e:
                    self._log.debug("Anchor supersede update failed: %s", e)

            # Soft-retire weak anchors that are old (even if within keep set, except best).
            for (eid, member_n, step0, p) in keep:
                if int(eid) == best_eid:
                    continue
                if int(member_n) <= int(weak_max) and (int(now_step) - int(step0)) >= int(weak_min_age):
                    try:
                        g.update_payload(int(eid), {
                            "anchor_retired": True,
                            "anchor_retired_reason": "weak_old",
                            "anchor_superseded_by": int(best_eid),
                            "last_reinforced": int(now_step),
                        })
                    except Exception as e:
                        self._log.debug("Weak anchor retire failed: %s", e)


    def clone_workspace(self, source_workspace_id: str, target_workspace_id: str, include_private: bool = True, include_shared: bool = True, reembed: bool = True, reembed_mode: str = "selective") -> Dict[str, Any]:
        """Clone a workspace into a new workspace ID, optionally re-embedding all memories.
    
        Intended for safe migration when changing embedding provider/model/dim.
        Operational model:
          - Start server with desired embedder (st/ollama/etc).
          - Call this endpoint to clone + re-embed.
          - Target workspace becomes locked to the new embedder dim/provider/model.
    
        v1.10.4 additions:
          - Single-flight + optional rate limiting (prevents concurrent heavy clones).
          - Progress logging to server logs.
          - In-memory job status you can poll via /workspace/clone/job/{job_id}.
    
        Notes:
          - Copies nodes/edges/events verbatim and regenerates emb_*.npy from stored summaries.
          - Keeps EIDs stable within each graph by overwriting emb_{eid}.npy in-place.
        """
        _validate_path_component(source_workspace_id, "source_workspace_id")
        _validate_path_component(target_workspace_id, "target_workspace_id")
        now = time.time()
        if self._clone_min_gap_s and (now - float(self._last_clone_ts or 0.0)) < float(self._clone_min_gap_s):
            wait_s = int(max(1.0, float(self._clone_min_gap_s) - (now - float(self._last_clone_ts or 0.0))))
            raise HTTPException(status_code=429, detail=f"Clone rate-limited; try again in {wait_s}s")
        if not self._clone_mutex.acquire(blocking=False):
            raise HTTPException(status_code=429, detail="Another workspace clone is already in progress")
        self._last_clone_ts = now
    
        job_id = str(uuid.uuid4())
        self._clone_jobs[job_id] = {
            "job_id": job_id,
            "status": "running",
            "phase": "init",
            "source_workspace_id": source_workspace_id,
            "target_workspace_id": target_workspace_id,
            "started_ts": int(now),
            "updated_ts": int(now),
            "progress": {"graphs_total": 0, "graphs_done": 0, "embeddings_done": 0, "current_graph": ""},
            "error": "",
        }
        self._persist_job('clone', job_id)
        self._prune_jobs('clone')
    
        def _job_update(**kwargs: Any) -> None:
            st = self._clone_jobs.get(job_id)
            if not st:
                return
            st.update(kwargs)
            st["updated_ts"] = int(time.time())
            self._persist_job('clone', job_id)
    
        def _prog(**kwargs: Any) -> None:
            st = self._clone_jobs.get(job_id)
            if not st:
                return
            pr = st.get("progress") or {}
            pr.update(kwargs)
            st["progress"] = pr
            st["updated_ts"] = int(time.time())
            self._persist_job('clone', job_id)
    
        self._log.info("clone start job_id=%s src=%s tgt=%s include_private=%s include_shared=%s reembed=%s reembed_mode=%s",
                       job_id, source_workspace_id, target_workspace_id, include_private, include_shared, reembed, reembed_mode)
    
        try:
            src_root = os.path.normpath(os.path.join(self.data_dir, "workspaces", source_workspace_id))
            if not os.path.isdir(src_root):
                raise HTTPException(status_code=404, detail=f"Source workspace '{source_workspace_id}' not found")
            tgt_root = os.path.normpath(os.path.join(self.data_dir, "workspaces", target_workspace_id))
            if os.path.exists(tgt_root):
                raise HTTPException(status_code=409, detail=f"Target workspace '{target_workspace_id}' already exists")
    
            import shutil
    
            _job_update(phase="copy")
            def _copytree_filtered(src: str, dst: str) -> None:
                os.makedirs(dst, exist_ok=True)
                for root, dirs, files in os.walk(src):
                    rel = os.path.relpath(root, src)
                    out_root = os.path.join(dst, rel) if rel != "." else dst
    
                    parts = rel.split(os.sep) if rel != "." else []
                    if (not include_private) and ("agents" in parts) and ("private" in parts):
                        dirs[:] = []
                        continue
                    if (not include_shared) and ("domains" in parts) and ("shared" in parts):
                        dirs[:] = []
                        continue
    
                    os.makedirs(out_root, exist_ok=True)
                    for fn in files:
                        if fn.startswith("emb_") and fn.endswith(".npy"):
                            continue
                        srcp = os.path.join(root, fn)
                        dstp = os.path.join(out_root, fn)
                        os.makedirs(os.path.dirname(dstp), exist_ok=True)
                        shutil.copy2(srcp, dstp)
    
            _copytree_filtered(src_root, tgt_root)
    
            emb = getattr(self.kernel, "embedder", None)
            meta = {
                "workspace_id": target_workspace_id,
                "created_ts": int(time.time()),
                "embed_dim": int(getattr(emb, "dim", 0) or 0),
                "embed_provider": str(getattr(emb, "provider", "")),
                "embed_model": str(getattr(emb, "model", "")),
                "source_workspace_id": source_workspace_id,
            }
            mp = os.path.join(tgt_root, "workspace_meta.json")
            with open(mp, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
    
            regenerated = {"graphs": 0, "embeddings": 0}
            if reembed:
                _job_update(phase="reembed")
    
                def _iter_graph_dirs() -> List[str]:
                    gdirs: List[str] = []
                    agents_root = os.path.join(tgt_root, "agents")
                    if include_private and os.path.isdir(agents_root):
                        for aid in sorted(os.listdir(agents_root)):
                            gdir = os.path.join(agents_root, aid, "private")
                            if os.path.isdir(gdir):
                                gdirs.append(gdir)
                    domains_root = os.path.join(tgt_root, "domains")
                    if include_shared and os.path.isdir(domains_root):
                        for dom in sorted(os.listdir(domains_root)):
                            gdir = os.path.join(domains_root, dom, "shared")
                            if os.path.isdir(gdir):
                                gdirs.append(gdir)
                    return gdirs
    
                graph_dirs = _iter_graph_dirs()
                _prog(graphs_total=len(graph_dirs), graphs_done=0, embeddings_done=0, current_graph="")
    
                def _regen_graph(graph_dir: str) -> None:
                    nodes_path = os.path.join(graph_dir, "nodes.jsonl")
                    if not os.path.exists(nodes_path):
                        return
                    regenerated["graphs"] += 1
                    local_count = 0
                    self._log.info("clone job_id=%s reembed graph=%s", job_id, graph_dir)
                    objs: List[Dict[str, Any]] = []
                    modified_nodes = False
                    with open(nodes_path, "r", encoding="utf-8") as nf:
                        for line in nf:
                            if not line.strip():
                                continue
                            obj = json.loads(line)
                            eid = int(obj.get("eid"))
                            payload = obj.get("payload", {}) or {}
                            summary = str(payload.get("summary") or payload.get("text") or "").strip()
                            if not summary:
                                summary = "(empty)"
                            emb_path = os.path.join(graph_dir, f"emb_{eid}.npy")
                            mode = (reembed_mode or "selective").lower().strip()
                            if mode not in ("all", "selective", "missing"):
                                mode = "selective"

                            expected_ck = embedding_checksum(summary, meta["embed_provider"], meta["embed_model"])
                            stored_ck = str(payload.get("embedding_checksum") or "").strip()

                            needs_reembed = (mode == "all")
                            if not needs_reembed:
                                if not os.path.exists(emb_path):
                                    needs_reembed = True
                                else:
                                    try:
                                        old = np.load(emb_path)
                                        old = np.asarray(old).reshape(-1)
                                        if int(meta["embed_dim"]) and int(old.shape[0]) != int(meta["embed_dim"]):
                                            needs_reembed = True
                                        elif (not stored_ck) or (stored_ck != expected_ck):
                                            # No checksum or checksum mismatch => stale/unknown embedding.
                                            needs_reembed = True
                                    except Exception:
                                        needs_reembed = True

                            if needs_reembed:
                                v = np.asarray(self.kernel.embedder.embed(summary), dtype=np.float32).reshape(-1)
                                if int(meta["embed_dim"]) and int(v.shape[0]) != int(meta["embed_dim"]):
                                    raise HTTPException(status_code=500, detail=f"Embedder returned dim {int(v.shape[0])} but target lock is {int(meta['embed_dim'])}")
                                np.save(emb_path, v)
                                regenerated["embeddings"] += 1
                                local_count += 1
                                if local_count % int(max(1, self._clone_log_every)) == 0:
                                    _prog(embeddings_done=regenerated["embeddings"])
                                    self._log.info("clone job_id=%s progress graph=%s embeddings=%d", job_id, graph_dir, regenerated["embeddings"])
                            else:
                                regenerated.setdefault("skipped", 0)
                                regenerated["skipped"] += 1

                            # Always align node metadata to the target workspace lock.
                            if payload.get("embedding_provider") != meta["embed_provider"]:
                                payload["embedding_provider"] = meta["embed_provider"]
                                modified_nodes = True
                            if payload.get("embedding_model") != meta["embed_model"]:
                                payload["embedding_model"] = meta["embed_model"]
                                modified_nodes = True
                            if int(payload.get("embedding_dim") or 0) != int(meta["embed_dim"] or 0):
                                payload["embedding_dim"] = int(meta["embed_dim"] or 0)
                                modified_nodes = True
                            if payload.get("embedding_checksum") != expected_ck:
                                payload["embedding_checksum"] = expected_ck
                                modified_nodes = True

                            obj["payload"] = payload
                            objs.append(obj)

                    if modified_nodes:
                        tmp = nodes_path + ".tmp"
                        with open(tmp, "w", encoding="utf-8") as wf:
                            for o in objs:
                                wf.write(json.dumps(o, ensure_ascii=False) + "\n")
                        os.replace(tmp, nodes_path)

                    _prog(embeddings_done=regenerated["embeddings"])
    
                for i, gdir in enumerate(graph_dirs):
                    _prog(current_graph=gdir)
                    _regen_graph(gdir)
                    _prog(graphs_done=i + 1)
    
            _job_update(status="done", phase="done")
            self._log.info("clone done job_id=%s graphs=%d embeddings=%d", job_id, regenerated["graphs"], regenerated["embeddings"])

            # Persist a fast workspace-level embedding audit index for the target.
            # We mark it dirty because clone does not compute full stale taxonomy.
            try:
                total_nodes = int(regenerated.get("embeddings", 0) + regenerated.get("skipped", 0))
                _write_embed_audit(
                    self.data_dir,
                    target_workspace_id,
                    counts={
                        "regenerated": int(regenerated.get("embeddings", 0)),
                        "skipped": int(regenerated.get("skipped", 0)),
                        "note": "clone_completed_run_repair_scan_for_authoritative_counts",
                    },
                    graphs_scanned=int(regenerated.get("graphs", 0)),
                    total_nodes=total_nodes,
                    dirty=True,
                    lock={"provider": meta.get("embed_provider", ""), "model": meta.get("embed_model", ""), "dim": meta.get("embed_dim", 0)},
                    embedder={"provider": meta.get("embed_provider", ""), "model": meta.get("embed_model", ""), "dim": meta.get("embed_dim", 0)},
                )
            except Exception as e:
                self._log.debug("Failed to write embedding audit for workspace_id=%s: %s", target_workspace_id, e)

            return {
                "ok": True,
                "job_id": job_id,
                "source_workspace_id": source_workspace_id,
                "target_workspace_id": target_workspace_id,
                "embedder": {"provider": meta["embed_provider"], "model": meta["embed_model"], "dim": meta["embed_dim"]},
                "include_private": bool(include_private),
                "include_shared": bool(include_shared),
                "reembed": bool(reembed),
                "reembed_mode": str(reembed_mode),
                "regenerated": regenerated,
            }
    
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            _job_update(status="error", phase="error", error=err)
            self._log.exception("clone error job_id=%s err=%s", job_id, err)
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail=err)
        finally:
            try:
                self._clone_mutex.release()
            except Exception:
                pass
    
    
    def create_agent(self, workspace_id: str, agent_id: str, seed: Optional[Dict[str, Any]] = None) -> AgentIdentity:
        _validate_path_component(agent_id, "agent_id")
        ws = self.get_workspace(workspace_id)
        ak = self._agent_key(workspace_id, agent_id)
        # Serialize entire agent creation to prevent duplicate init under concurrency
        with self.locks.agent_lock(workspace_id, agent_id):
            ident = self.ident_store.load(workspace_id, agent_id)
            if ident is None:
                ident = self.ident_store.create(workspace_id, agent_id, seed=seed or DEFAULT_AGENT_SEED)
            # init role profile (character continuity guidance)
            try:
                _ = self.role_store.load(workspace_id, agent_id)
            except Exception as e:
                self._log.debug("Failed to load role_store for workspace_id=%s agent_id=%s: %s", workspace_id, agent_id, e)
            # init kernel state if needed — route character seed through oscillator physics
            if ak not in self.agent_states:
                char_mod = None
                if self._character_enable:
                    seed_text_val = str(ident.seed.get("seed_text", "") or "").strip()
                    if seed_text_val:
                        try:
                            _cseed = CharacterSeed(
                                seed_id=str(ident.seed.get("seed_id", "") or ""),
                                character_name=str(ident.seed.get("seed_id", "") or ""),
                                seed_text=seed_text_val,
                            )
                            char_mod = derive_kernel_modulation(_cseed, self.kernel.embedder)
                        except Exception:
                            char_mod = None
                if char_mod:
                    self.agent_states[ak] = self.kernel.init_state(
                        seed_text=seed_text_val, character_modulation=char_mod)
                else:
                    self.agent_states[ak] = self.kernel.init_state(seed_text=f"agent:{agent_id}")
            # init private store
            if ak not in self.private_graphs:
                pdir = os.path.join(self.data_dir, "workspaces", workspace_id, "agents", agent_id, "private")
                sq_idx = self._get_sqlite_index(workspace_id, agent_id)
                self.private_graphs[ak] = MemoryGraph(
                    data_dir=pdir, embedder=self.kernel.embedder, sqlite_index=sq_idx,
                )

            # --- Character seed planting (optional, non-blocking) ---
            if self._character_enable:
                seed_text = str(ident.seed.get("seed_text", "") or "").strip()
                seed_id = str(ident.seed.get("seed_id", "") or "").strip()
                if seed_text and seed_id:
                    try:
                        char_seed = self.character_store.load_seed(workspace_id, seed_id)
                        if char_seed is None:
                            char_seed = CharacterSeed(
                                seed_id=seed_id,
                                character_name=seed_id,
                                seed_text=seed_text,
                            )
                        if not char_seed.seed_motif_id:
                            # Determine domain (first available or "default")
                            dom = list(ws.shared_graphs.keys())[0] if ws.shared_graphs else "default"
                            mreg = ws.motif_regs.get(dom)
                            if mreg is not None:
                                char_seed = plant_seed(
                                    graph=self.private_graphs[ak],
                                    motif_registry=mreg,
                                    coherence_field=None,
                                    embedder=self.kernel.embedder,
                                    seed=char_seed,
                                    agent_id=agent_id,
                                    step=0,
                                )
                                self.character_store.save_seed(workspace_id, char_seed)
                    except Exception:
                        pass  # Character is optional — never blocks agent creation

            return ident

    def _get_collective_field(self, workspace_id: str):
        """Lazy-init and return the CollectiveField for a workspace.

        Uses double-checked locking to prevent duplicate initialization
        when multiple threads access the same workspace concurrently.
        """
        if workspace_id in self._collective_fields:
            return self._collective_fields[workspace_id]
        with self.locks.init_lock:
            if workspace_id not in self._collective_fields:
                from .collective_field import CollectiveField
                self._collective_fields[workspace_id] = CollectiveField(
                    workspace_id=workspace_id, data_dir=self.data_dir,
                )
        return self._collective_fields[workspace_id]

    def _get_proposal_bridge(self, workspace_id: str):
        """Lazy-init and return the CollectiveProposalBridge for a workspace.

        Uses double-checked locking for thread safety.
        """
        if workspace_id in self._proposal_bridges:
            return self._proposal_bridges[workspace_id]
        with self.locks.init_lock:
            if workspace_id not in self._proposal_bridges:
                from .collective_proposals import CollectiveProposalBridge
                self._proposal_bridges[workspace_id] = CollectiveProposalBridge(
                    data_dir=self.data_dir, workspace_id=workspace_id,
                )
        return self._proposal_bridges[workspace_id]

    def _collective_query_context(self, workspace_id: str, domains: List[str]) -> Dict[str, Any]:
        """Build optional collective_context for query response.

        Returns recent convergence events relevant to the queried domains.
        Does NOT influence scoring — informational only.
        """
        try:
            field = self._get_collective_field(workspace_id)
            relevant_events = []
            for d in domains:
                relevant_events.extend(field.events_by_domain(d, limit=5))
            # Deduplicate by event_id
            seen = set()
            unique = []
            for ev in relevant_events:
                eid = ev.get("event_id", "")
                if eid not in seen:
                    seen.add(eid)
                    unique.append(ev)
            if not unique:
                return {}
            return {
                "collective_context": {
                    "recent_events": unique[:10],
                    "event_count": len(unique),
                }
            }
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Phase D3: Collective echo re-ingestion
    # ------------------------------------------------------------------

    def reingest_convergence(
        self,
        workspace_id: str,
        target_agent_id: str,
        event_id: str,
        *,
        echo_strength_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Re-ingest a convergence event as a low-amplitude echo into a target agent.

        This is the core D3 method — the bridge between detection and influence.
        It loads the event, runs it through the 7-gate policy engine, then calls
        ingest() with reduced strength and collective governance flags.

        Echoes are:
            - Low-amplitude (0.25x default, 0.40x hard cap)
            - Terminal (collective_reingest_blocked + collective_export_blocked)
            - Provenance-marked (provenance='collective', source_event_id, source_agents)
            - Retrieval-discounted (0.5x weight at query time)
            - Excluded from seed-basin correction

        Args:
            workspace_id: Target workspace.
            target_agent_id: Agent that will receive the echo.
            event_id: Convergence event to reingest.
            echo_strength_override: Optional strength override (capped at echo_strength_cap).

        Returns:
            Dict with reingest result (eligible, gate_failed, echo details or rejection reason).
        """
        if not self._hivemind_enable:
            return {"eligible": False, "reason": "Hivemind is disabled (TORMENT_HIVEMIND_ENABLE=0)"}

        # Load the convergence event
        field = self._get_collective_field(workspace_id)
        event_dict = field.get_event(event_id)
        if event_dict is None:
            return {"eligible": False, "reason": f"Event '{event_id}' not found"}

        # Ensure target agent exists
        try:
            self.create_agent(workspace_id, target_agent_id)
        except Exception as e:
            return {"eligible": False, "reason": f"Cannot initialize agent: {e}"}

        # Build policy engine
        from .collective_policy import CollectivePolicy

        policy = CollectivePolicy(
            data_dir=self.data_dir,
            workspace_id=workspace_id,
        )

        # Load agent's character state for drift info
        current_drift_score = 0.0
        drift_direction = "stable"
        agent_seed_motif_id = None
        try:
            cstate = self.character_store.load_state(workspace_id, target_agent_id)
            if cstate:
                current_drift_score = float(cstate.drift_score)
                drift_direction = str(cstate.drift_direction or "stable")
                # Load seed for motif ID
                seed_id = str(cstate.seed_id or "")
                if seed_id:
                    cseed = self.character_store.load_seed(workspace_id, seed_id)
                    if cseed:
                        agent_seed_motif_id = cseed.seed_motif_id
        except Exception as e:
            self._log.debug("Failed to load character seed for agent_id=%s: %s", target_agent_id, e)

        # Determine target domain
        target_domain = event_dict.get("domain_id", "")

        # Run 7-gate policy evaluation
        result = policy.evaluate(
            event=event_dict,
            target_agent_id=target_agent_id,
            target_domain_id=target_domain,
            current_drift_score=current_drift_score,
            drift_direction=drift_direction,
            agent_seed_motif_id=agent_seed_motif_id,
        )

        if not result.eligible:
            return {
                "eligible": False,
                "gate_failed": result.gate_failed,
                "reason": result.reason,
            }

        # Determine echo strength (policy default, overridable with cap)
        from .collective_policy import DEFAULT_ECHO_STRENGTH_CAP
        echo_strength = result.echo_strength
        if echo_strength_override is not None:
            echo_strength = min(float(echo_strength_override), DEFAULT_ECHO_STRENGTH_CAP)

        # Synthesize summary from event data
        participating = event_dict.get("participating_agents", [])
        source_agents = [a for a in participating if a != target_agent_id]
        dominant_motifs = event_dict.get("dominant_motifs", [])
        event_summary = event_dict.get("summary", "")

        echo_summary = (
            f"[collective echo] {event_summary}"
            if event_summary
            else f"[collective echo] Convergence across {', '.join(source_agents)} "
                 f"in domain '{target_domain}'"
        )
        if dominant_motifs:
            echo_summary += f" (motifs: {', '.join(dominant_motifs[:3])})"

        # Ingest the echo as a low-amplitude memory
        # We call ingest() directly but then immediately patch the stored memory
        # with collective governance flags and provenance markers.
        ingest_result = self.ingest(
            workspace_id=workspace_id,
            agent_id=target_agent_id,
            text=echo_summary,
            step=0,  # echoes don't participate in step-counting
            domain_id=target_domain,
            supplied_summary=echo_summary,
            scope="private",
        )

        echo_eid = ingest_result.get("eid")

        if echo_eid is not None:
            # Patch the stored memory with collective provenance + governance
            try:
                graph = self.private_graphs.get(self._agent_key(workspace_id, target_agent_id))
                if graph:
                    ent = graph.entities.get(int(echo_eid))
                    if ent is not None:
                        # Mark provenance
                        ent.payload["provenance"] = "collective"
                        ent.payload["source_event_id"] = event_id
                        ent.payload["source_agents"] = source_agents

                        # Reduce strength to echo level
                        ent.payload["strength"] = float(echo_strength)

                        # Apply terminal governance: double-block
                        from .governance import update_governance
                        update_governance(ent.payload, {
                            "collective_reingest_blocked": True,
                            "collective_export_blocked": True,
                        }, actor="collective_policy", source="reingest")

                        # Flush the patched entity to disk
                        try:
                            graph.flush_node(int(echo_eid))
                        except Exception as e:
                            self._log.debug("Failed to flush node eid=%s: %s", echo_eid, e)
            except Exception as e:
                self._log.debug("Failed to process reingest for agent_id=%s event_id=%s: %s", target_agent_id, event_id, e)

        # Record the reingest in the tracker (for dedup + rate limiting)
        policy.record_reingest(target_agent_id, event_id)

        return {
            "eligible": True,
            "echo_eid": echo_eid,
            "echo_strength": echo_strength,
            "event_id": event_id,
            "target_agent_id": target_agent_id,
            "source_agents": source_agents,
            "reason": result.reason,
        }

    def ingest(
        self,
        workspace_id: str,
        agent_id: str,
        text: str,
        step: int = 0,
        domain_id: Optional[str] = None,
        tri_mod: Optional[Dict[str, float]] = None,
        supplied_summary: Optional[str] = None,
        supplied_embedding: Optional[List[float]] = None,
        scope: str = "private",
    ) -> Dict[str, Any]:
        # === BOUNDARY GUARD ===
        # Core ingest ALWAYS creates "core" memory. Archive documents use
        # ArchiveStore.ingest_document() via /archive/ingest_document endpoint.
        # This prevents archive content from entering the identity pipeline.
        # =====================
        ws = self.get_workspace(workspace_id)
        ak = self._agent_key(workspace_id, agent_id)
        ident = self.create_agent(workspace_id, agent_id)
        ws = self.get_workspace(workspace_id)

        state = self.agent_states[ak]
        # process kernel (text only used for gating signals)
        state, signals, debug = self.kernel.process(state, text)
        self.agent_states[ak] = state

        summary = supplied_summary or debug.get("summary") or (text.strip()[:240] + ("…" if len(text.strip()) > 240 else ""))

        kernel_tri = debug.get("tri_mod", {}) or {}
        tri_mod = {**kernel_tri, **(tri_mod or {})}

        # Phase-cycle time tracking (per-agent)
        from .phase_timer import PhaseTimer as _PhaseTimer
        _pt = self._phase_timers.get(ak)
        if _pt is None:
            _pt = _PhaseTimer()
            self._phase_timers[ak] = _pt
        _pt_in_corr = bool(tri_mod.get("in_corridor", 0))
        _pt_stage = tri_mod.get("cycle_stage")
        if _pt_stage is not None:
            _pt_stage = int(_pt_stage)
        _pt.update(int(step), _pt_in_corr, _pt_stage)
        _pt_durations = _pt.get_durations(int(step))

        # SRG living memory — build dual-field state if enabled (Phase 1+2)
        _srg_dict = None
        if self._srg_enable:
            from .srg_engine import build_memory_srg, detect_character_mode
            _srg_char_mode = detect_character_mode(text)
            _srg_state = build_memory_srg(
                strength=float(signals.strength),
                coherence=float(debug.get("coherence", 0.5)),
                phase_duration=int(_pt_durations.get("phase_duration_steps", 0)),
                content_hash=hash(summary) & 0xFFFFFFFF,
                character_mode=_srg_char_mode,
                is_seed=False,
            )
            _srg_dict = _srg_state.to_dict()
            # Track last-ingested band for same-band scoring in query path
            self._srg_last_ingest_band = _srg_state.R_band

        # Character continuity (v1.11): soft role inference (guidance signal).
        # Updates slowly and is used only to tune memory behavior (anchors/recency), never persona writing.
        try:
            _rp = self.role_store.load(workspace_id, agent_id)
            _rp = self.role_store.update_from_text(_rp, summary)
            self.role_store.save(_rp)
        except Exception:
            _rp = None

        # Character continuity (v1.11): lightweight affect tagging.

        # Character continuity (v1.11): lightweight affect tagging.
        # This is a guidance signal only; it must not dominate or rewrite persona.
        affect_tag = None
        affect_conf = None
        try:
            affect_enable = str(os.getenv("TORMENT_AFFECT_ENABLE", "1")).strip().lower() not in ("0", "false", "no")
        except Exception:
            affect_enable = True
        if affect_enable:
            try:
                a = classify_affect(summary)
                if a.tag and a.tag != "neutral" and float(a.conf) > 0.0:
                    affect_tag = str(a.tag)
                    affect_conf = float(a.conf)
            except Exception:
                affect_tag, affect_conf = None, None
        if supplied_embedding is not None:
            emb = np.asarray(supplied_embedding, dtype=np.float32)
        else:
            emb = self.kernel.embedder.embed(summary)

        # Tie stored embeddings to the summary + embedder identity to prevent silent drift.
        emb_provider = str(getattr(self.kernel.embedder, "provider", ""))
        emb_model = str(getattr(self.kernel.embedder, "model", ""))
        emb_dim = int(np.asarray(emb).reshape(-1).shape[0])
        emb_ck = embedding_checksum(summary, emb_provider, emb_model)

        if emb_dim != int(ws.embed_dim):
            raise HTTPException(
                status_code=409,
                detail=f"Embedding dimension mismatch; workspace '{workspace_id}' locked to {ws.embed_dim} but got {emb_dim}.",
            )

        # route domain if relevant (for shared proposals and for motif tracking)
        dom_scores = ws.router.rank_domains(emb, top_k=2)
        routed = [d.domain_id for d in dom_scores]
        chosen_domain = domain_id or (routed[0] if routed else "research")

        stored = False
        eid = None
        motif_ids: List[str] = []
        created_motif: Optional[str] = None
        proposal_id: Optional[str] = None

        # gating via overlay threshold
        wt = float(ident.overlay.get("write_threshold", 0.55))
        wt *= float(tri_mod.get("write_mult", 1.0))
        # hard gate + soft band (prevents cliff behavior)
        allow_write = False
        if signals.write_intent:
            s = float(signals.strength)

            if s >= wt:
                allow_write = True
            else:
                # within a narrow band below threshold, allow probabilistically
                band = float(ident.overlay.get("write_band", 0.08))  # default 0.08
                if band > 0 and s >= (wt - band):
                    # map [wt-band, wt] -> [0, 1] with tri_mod influence already in wt
                    p = (s - (wt - band)) / band

                    # optional: corridor survival slightly increases p, tearing reduces p
                    survival = float(tri_mod.get("survival_steps", 0.0))
                    tear = float(tri_mod.get("tearing_risk", 0.0))
                    p *= (1.0 + 0.20 * np.tanh(survival / 80.0))     # up to +20%
                    p *= (1.0 - 0.30 * tear)                         # up to -30%
                    p = float(np.clip(p, 0.0, 1.0))

                    allow_write = random_chance(p)
        half_life_days: Optional[float] = None
        motif_ids: list = []
        created_motif: Optional[str] = None
        _reinforced_eid: Optional[int] = None

        # choose graph early so world can evolve even when we don't store
        if scope == "shared":
            graph = ws.shared_graphs[chosen_domain]
        else:
            graph = self.private_graphs[ak]

        if allow_write:
            # --- metastability -> half-life (A-only: memory mechanics) ---
            decay_scale = float(ident.overlay.get("decay_scale", 1.0))

            survival = float(tri_mod.get("survival_steps", 0.0))
            in_corr = bool(float(tri_mod.get("in_corridor", 0.0)) >= 0.5)  # telemetry only
            tear = float(tri_mod.get("tearing_risk", 0.0))

            survival_boost = 1.0 + (0.20 * np.tanh(survival / 200.0))    # max ~ +20%
            tear_penalty = 1.0 - 0.15 * tear                              # max ~ -15%
            hl_mult = float(np.clip(survival_boost * tear_penalty, 0.85, 1.25))

            half_life_days = max(1.0, float(signals.half_life) * decay_scale * hl_mult)

            # --- Duplicate suppression: reinforce existing instead of creating new ---
            # Same-agent only, strict threshold, recent-window search.
            _reinforce_sim_threshold = float(os.getenv("TORMENT_REINFORCE_SIM_THRESHOLD", "0.92"))
            _reinforced_eid: Optional[int] = None
            if scope == "private" and _reinforce_sim_threshold > 0:
                try:
                    _recent_hits = graph.search_by_embedding(
                        np.asarray(emb, dtype=np.float32),
                        top_k=3,
                        user_id=agent_id,
                    )
                    for _rh in _recent_hits:
                        if float(_rh.get("raw_score", _rh.get("score", 0))) >= _reinforce_sim_threshold:
                            _existing_eid = int(_rh["eid"])
                            _existing_ent = graph.entities.get(_existing_eid)
                            if _existing_ent is not None:
                                _old_str = float((_existing_ent.payload or {}).get("strength", 0.5))
                                # Asymptotic reinforcement: diminishing returns, cap at 0.98
                                _new_str = min(0.98, _old_str + (1.0 - _old_str) * 0.3)
                                graph.update_payload(_existing_eid, {
                                    "strength": round(_new_str, 4),
                                    "last_reinforced": int(step),
                                    "last_reinforced_ts": _now_ts(),
                                    "reinforce_count": int((_existing_ent.payload or {}).get("reinforce_count", 0)) + 1,
                                })
                                _reinforced_eid = _existing_eid
                                break
                except Exception:
                    pass  # on any error, fall through to normal creation

            if _reinforced_eid is not None:
                stored = True
                eid = _reinforced_eid
                # Skip spawn — we reinforced an existing memory
            else:
                # --- Single-write path: spawn → enrich → flush ---
                # spawn_memory creates entity + embedding in RAM but does NOT
                # write to nodes.jsonl yet.  We enrich the payload with motif,
                # symbol, and resonance data, then flush_node writes one
                # complete record.  This replaces the old add_memory +
                # update_payload pattern that wrote 2 (or 3) records per memory.

                eid = graph.spawn_memory(
                summary=summary,
                embedding=emb,
                mtype=signals.memory_type,
                strength=signals.strength,
                confidence=signals.confidence,
                half_life_days=half_life_days,
                links=signals.links,
                canon=(signals.promotion_score >= 0.78),
                user_id=agent_id,
                step=step,
                extra_payload={
                    "workspace_id": workspace_id,
                    "domain_id": chosen_domain,
                    "scope": scope,
                    "agent_id": agent_id,
                    "embedding_provider": emb_provider,
                    "embedding_model": emb_model,
                    "embedding_dim": emb_dim,
                    "embedding_checksum": emb_ck,
                    "affect_tag": affect_tag,
                    "affect_conf": affect_conf,

                    # metastability telemetry
                    "in_corridor": in_corr,
                    "survival_steps": survival,
                    "tearing_risk": tear,
                    "hl_mult": hl_mult,

                    # TriOcta -> seed motion
                    "seed_v0": tri_mod.get("seed_v0") or [0.0, 0.0, 0.0],
                    "seed_pos0": tri_mod.get("seed_pos0") or [0.0, 0.0, 0.0],

                    # Phase-cycle duration tracking
                    "phase_duration_steps": _pt_durations.get("phase_duration_steps", 0),
                    "corridor_duration_steps": _pt_durations.get("corridor_duration_steps", 0),

                    # SRG dual-field state (None when flag is off — filtered below)
                    "srg": _srg_dict,
                },
                )
                stored = True

                _mark_embed_audit_dirty(self.data_dir, workspace_id)

                reg = ws.motif_regs[chosen_domain]
                motif_ids, created_motif = reg.attach_or_create(
                    emb,
                    memory_eid=int(eid),
                    agent_id=agent_id,
                    summary=summary,
                    attach_threshold=float(0.62 + 0.2 * ident.overlay.get("motif_sensitivity", 0.7)),
                )

                sym_state = _load_symbol_state(self.data_dir, workspace_id, agent_id)
                prev_symbol = str(sym_state.get("last_symbol", "") or "")
                prev_trace = list(sym_state.get("symbol_trace", []) or [])
                primary_prev_motif_id = str(sym_state.get("last_motif_id", "") or "")
                prev_tension = float(sym_state.get("last_tension", 0.0) or 0.0)

                # hidden symbolic watermark — geometric projection from coherence field
                sym = {
                    "state_symbol": None,
                    "symbol_confidence": None,
                    "symbol_reason": None,
                }
                current_tension = 0.0

                try:
                    # Build motif rows for the whole chosen domain
                    motif_rows = []
                    for mid, mm in reg.motifs.items():
                        motif_rows.append({
                            "motif_id": mid,
                            "label": getattr(mm, "label", mid),
                            "centroid": list(getattr(mm, "centroid", []) or []),
                            "strength": float(getattr(mm, "strength", 0.0) or 0.0),
                            "stability_score": float(getattr(mm, "stability_score", 0.0) or 0.0),
                            "members": list(getattr(mm, "members", []) or []),
                            "radius": float(reg._motif_radius(mm)) if hasattr(reg, "_motif_radius") else 0.0,
                        })

                    field_rows = compute_coherence_field(motif_rows)
                    field_by_id = {row["motif_id"]: row for row in field_rows}

                    primary_motif_id = created_motif or (motif_ids[0] if motif_ids else None)
                    field_state = field_by_id.get(primary_motif_id or "", {})

                    current_tension = float(field_state.get("tension", 0.0) or 0.0)
                    tension_delta = current_tension - prev_tension

                    sym = assign_symbol_state(
                        motif_role=str(field_state.get("role", "") or ""),
                        phi=float(field_state.get("phi", 0.0) or 0.0),
                        tension=current_tension,
                        kappa=float(field_state.get("kappa", 0.0) or 0.0),
                        coherence_delta=float(signals.stability_delta),
                        tension_delta=tension_delta,
                        previous_symbol=prev_symbol,
                        repeated_same_motif=bool(primary_motif_id and str(primary_motif_id) == primary_prev_motif_id),
                        is_new_motif=bool(created_motif is not None),
                        symbol_trace=prev_trace,
                    )
                except Exception as e:
                    self._log.debug("Failed to record symbol motif trace for eid=%s: %s", eid, e)

                # Enrich the entity payload with symbol + resonance data IN-MEMORY
                # (no nodes.jsonl write yet — flush_node below handles that)
                try:
                    if eid is not None:
                        new_symbol = sym.get("state_symbol")
                        new_trace = append_symbol(prev_trace, new_symbol) if new_symbol else prev_trace
                        res = summarize_resonance(new_trace, prev_trace=prev_trace)

                        sym_state["last_symbol"] = str(new_symbol or "")
                        sym_state["last_motif_id"] = str(primary_motif_id or "")
                        sym_state["last_tension"] = float(current_tension)
                        sym_state["symbol_trace"] = list(new_trace[-12:])
                        _save_symbol_state(self.data_dir, workspace_id, agent_id, sym_state)

                        # Enrich payload in-memory (entity is already in graph.entities)
                        ent = graph.entities.get(int(eid))
                        if ent is not None:
                            ent.payload.update({
                                "state_symbol": sym.get("state_symbol"),
                                "symbol_confidence": sym.get("symbol_confidence"),
                                "symbol_reason": sym.get("symbol_reason"),
                                "symbol_trace": list(res.get("symbol_trace", []) or []),
                                "resonance_score": float(res.get("resonance_score", 0.0) or 0.0),
                                "transition_entropy": float(res.get("transition_entropy", 0.0) or 0.0),
                                "loop_type": str(res.get("loop_type", "mixed") or "mixed"),
                                "phase_shift": bool(res.get("phase_shift", False)),
                                "dominant_transition": res.get("dominant_transition"),
                                "cycles": res.get("cycles", []),
                            })
                except Exception as e:
                    self._log.debug("Failed to enrich resonance data for eid=%s: %s", eid, e)

                # --- Single flush: write the complete, enriched record once ---
                try:
                    graph.flush_node(int(eid))
                except Exception as e:
                    self._log.debug("Failed to flush node eid=%s: %s", eid, e)

                # --- SRG collision detection (Phase 3) ---
                if self._srg_enable and _srg_dict and eid is not None:
                    try:
                        from .srg_engine import SRGMemoryState, collision as srg_collision, evolve_breathing
                        from .embedding_store import load_embedding as _load_emb_srg
                        # Find closest existing memory by embedding similarity
                        _new_emb_norm = emb / (np.linalg.norm(emb) + 1e-12)
                        _best_sim = 0.0
                        _best_eid = None
                        for _oid, _oent in graph.entities.items():
                            if int(_oid) == int(eid):
                                continue
                            _opay = getattr(_oent, "payload", {}) or {}
                            if not _opay.get("srg"):
                                continue
                            _raw = _load_emb_srg(
                                _oid, _opay, graph._shard_reader, graph.data_dir
                            )
                            if _raw is None:
                                continue
                            _ov = np.asarray(_raw, dtype=np.float32).reshape(-1)
                            _on = float(np.linalg.norm(_ov))
                            if _on < 1e-12:
                                continue
                            _sim = float(np.dot(_new_emb_norm, _ov / _on))
                            if _sim > _best_sim:
                                _best_sim = _sim
                                _best_eid = int(_oid)

                        if _best_eid is not None and _best_sim >= 0.75:
                            _exist_ent = graph.entities.get(_best_eid)
                            if _exist_ent is not None:
                                _exist_srg = SRGMemoryState.from_dict(
                                    (_exist_ent.payload or {}).get("srg", {})
                                )
                                _new_srg = SRGMemoryState.from_dict(_srg_dict)
                                _col_report = srg_collision(
                                    _exist_srg, _new_srg, _best_sim, int(step)
                                )
                                if _col_report.get("collision"):
                                    # Write back updated states
                                    _exist_ent.payload["srg"] = _exist_srg.to_dict()
                                    _my_ent = graph.entities.get(int(eid))
                                    if _my_ent is not None:
                                        _my_ent.payload["srg"] = _new_srg.to_dict()
                                        _my_ent.payload["srg_collision"] = _col_report
                    except Exception as e:
                        self._log.debug("Failed to process SRG collision for eid=%s: %s", eid, e)

                # --- Hivemind: emit ResonancePacket into collective field ---
                # === TEMPORARY PACKET DEBUG (print to stdout — remove after diagnosis) ===
                import sys as _hm_sys
                print(f"\n[PACKET-GATE] hivemind_enable={self._hivemind_enable}, stored={stored}, eid={eid}, agent={agent_id}, ws={workspace_id}", file=_hm_sys.stderr, flush=True)
                _hm_sys.stderr.flush()
                if self._hivemind_enable and stored and eid is not None:
                    try:
                        from .collective_models import ResonancePacket
                        from .governance import should_emit_packet as _gov_should_emit

                        # Gate 1: governance — non_shareable / export_blocked memories never emit
                        # Check at emission time (earliest boundary), not at convergence time.
                        _hm_emit_ok = True
                        _hm_skip_reason = None
                        try:
                            _hm_ent_gov = graph.entities.get(int(eid))
                            if _hm_ent_gov is not None:
                                _hm_emit_ok = _gov_should_emit(_hm_ent_gov.payload)
                                if not _hm_emit_ok:
                                    _hm_skip_reason = "governance: non_shareable or export_blocked"
                                # Gate 1b: collective-provenance memories never emit packets
                                # (terminal echo invariant — echoes don't echo)
                                if str((_hm_ent_gov.payload or {}).get("provenance", "")) == "collective":
                                    _hm_emit_ok = False
                                    _hm_skip_reason = "governance: collective provenance (echo invariant)"
                        except Exception as _gov_exc:
                            print(f"[PACKET-GATE] governance check exception: {_gov_exc}", file=_hm_sys.stderr, flush=True)

                        # Gate 2: coherence minimum threshold
                        # Restored to 0.15 after DISP_SCALE recalibration (7e-4 → 0.10)
                        # and distributed Omega extraction fix.
                        _HM_COH_THRESHOLD = 0.15
                        _hm_coherence = float(debug.get("coherence", 0.0) or 0.0)

                        print(f"[PACKET-GATE] gate1_ok={_hm_emit_ok}, coherence={_hm_coherence:.4f} (threshold={_HM_COH_THRESHOLD}), skip_reason={_hm_skip_reason}", file=_hm_sys.stderr, flush=True)

                        if _hm_emit_ok and _hm_coherence >= _HM_COH_THRESHOLD:
                            _hm_emb_hash = ""
                            try:
                                import hashlib
                                _hm_emb_hash = hashlib.md5(emb.tobytes()).hexdigest()[:12]
                            except Exception as e:
                                self._log.debug("Failed to compute embedding hash: %s", e)

                            # Safely extract resonance data (may not exist if sym enrichment failed)
                            _hm_res_score = None
                            _hm_loop_type = None
                            try:
                                _hm_ent = graph.entities.get(int(eid))
                                if _hm_ent and _hm_ent.payload:
                                    _hm_res_score = _hm_ent.payload.get("resonance_score")
                                    _hm_loop_type = _hm_ent.payload.get("loop_type")
                            except Exception as e:
                                self._log.debug("Failed to extract resonance data for packet: %s", e)

                            # Drift info (may not exist yet)
                            _hm_drift = None
                            _hm_drift_dir = None
                            _hm_seed_id = None
                            try:
                                _hm_cstate = self.character_store.load_state(workspace_id, agent_id)
                                if _hm_cstate:
                                    _hm_drift = _hm_cstate.drift_score
                                    _hm_drift_dir = _hm_cstate.drift_direction
                                    _hm_seed_id = _hm_cstate.seed_id
                            except Exception as e:
                                self._log.debug("Failed to load character state for packet: %s", e)

                            # SRG fields
                            _hm_srg_band = None
                            _hm_srg_hb = None
                            _hm_srg_crystal = False
                            if _srg_dict and isinstance(_srg_dict, dict):
                                _hm_srg_band = _srg_dict.get("R_band")
                                _hm_srg_hb = _srg_dict.get("heartbeat_class")
                                _hm_srg_crystal = bool(_srg_dict.get("is_crystal", False))

                            _hm_packet = ResonancePacket(
                                workspace_id=workspace_id,
                                agent_id=agent_id,
                                domain_id=chosen_domain,
                                source_eid=int(eid),
                                summary=str(summary),
                                embedding_hash=_hm_emb_hash,
                                cycle_stage=str(tri_mod.get("cycle_stage", "")),
                                identity_state=str(tri_mod.get("identity_state", "")),
                                coherence=_hm_coherence,
                                stability_delta=float(signals.stability_delta),
                                corridor_angle_deg=_pt_durations.get("corridor_angle_deg") if _pt_durations else None,
                                corridor_duration_steps=int(_pt_durations.get("corridor_duration_steps", 0)) if _pt_durations else None,
                                phase_duration_steps=int(_pt_durations.get("phase_duration_steps", 0)) if _pt_durations else None,
                                motifs=list(motif_ids),
                                created_motif=created_motif,
                                state_symbol=sym.get("state_symbol"),
                                resonance_score=float(_hm_res_score) if _hm_res_score is not None else None,
                                loop_type=str(_hm_loop_type) if _hm_loop_type else None,
                                drift_score=float(_hm_drift) if _hm_drift is not None else None,
                                drift_direction=str(_hm_drift_dir) if _hm_drift_dir else None,
                                seed_id=str(_hm_seed_id) if _hm_seed_id else None,
                                srg_band=_hm_srg_band,
                                srg_heartbeat_class=_hm_srg_hb,
                                srg_is_crystal=_hm_srg_crystal,
                            )
                            _hm_field = self._get_collective_field(workspace_id)
                            _hm_conv_event = _hm_field.append_packet(_hm_packet, embedding=emb)

                            print(
                                f"[PACKET-EMIT] packet BUILT and appended: agent={agent_id}, domain={chosen_domain}, "
                                f"coherence={_hm_coherence:.3f}, eid={eid}, convergence_event={_hm_conv_event is not None}",
                                flush=True,
                            )

                            # Phase D4: Light proposal bridge
                            # If convergence was detected, feed it to the proposal bridge.
                            # Proposals are auto-drafted (pending), never auto-approved.
                            if _hm_conv_event is not None:
                                print(f"[PACKET-CONVERGE] convergence event detected! {_hm_conv_event}", flush=True)
                                try:
                                    _hm_prop_bridge = self._get_proposal_bridge(workspace_id)
                                    _hm_prop_reg = ws.proposals.get(chosen_domain)
                                    _hm_prop_bridge.maybe_draft_proposal(
                                        event=_hm_conv_event.to_dict(),
                                        proposal_registry=_hm_prop_reg,
                                        embedding=emb,
                                    )
                                except Exception:
                                    pass  # Proposal bridge is optional
                        else:
                            print(
                                f"[PACKET-SKIP] packet NOT built: emit_ok={_hm_emit_ok}, coherence={_hm_coherence:.4f}, "
                                f"reason={_hm_skip_reason if not _hm_emit_ok else 'coherence_below_0.15'}",
                                flush=True,
                            )
                    except Exception as _hm_exc:
                        import traceback
                        print(f"[PACKET-ERROR] exception in packet emission: {_hm_exc}", flush=True)
                        traceback.print_exc()
                else:
                    # Outer gate failed — print which condition was False
                    _hm_reasons = []
                    if not self._hivemind_enable:
                        _hm_reasons.append("hivemind_enable=False (set TORMENT_HIVEMIND_ENABLE=1)")
                    if not stored:
                        _hm_reasons.append("stored=False")
                    if eid is None:
                        _hm_reasons.append("eid=None")
                    print(f"[PACKET-BLOCKED] outer gate failed: {', '.join(_hm_reasons)}", file=_hm_sys.stderr, flush=True)

                pol = ws.domain_policies.get(chosen_domain, {})
                try:
                    reg.update_entropy_and_suggest(
                        target_n=int(pol.get("motif_entropy_target_n", 24)),
                        entropy_high=float(pol.get("motif_entropy_high", 0.72)),
                        sim_threshold=float(pol.get("motif_merge_similarity", 0.93)),
                        max_suggestions=int(pol.get("motif_merge_max_suggestions", 20)),
                        auto_merge=bool(pol.get("auto_merge_motifs", False)),
                        auto_merge_trigger=float(pol.get("auto_merge_entropy_trigger", 0.80)),
                    )
                except Exception as e:
                    self._log.debug("motif entropy update failed for domain=%s: %s", chosen_domain, e)

                # optional B-layers (safe to keep wrapped)
                try:
                    _ = self._maybe_emit_identity_anchor(ws, agent_id=agent_id, domain_id=chosen_domain, step=int(step), motif_ids=list(motif_ids))
                except Exception as e:
                    self._log.debug("identity anchor emission failed: %s", e)
                try:
                    self._refine_identity_anchors(ws, agent_id=agent_id, domain_id=chosen_domain, motif_ids=list(motif_ids))
                except Exception as e:
                    self._log.debug("identity anchor refinement failed: %s", e)
                try:
                    self._maybe_emit_mood_drift(ws, agent_id=agent_id, domain_id=chosen_domain, step=int(step), affect_tag=affect_tag, affect_conf=affect_conf)
                except Exception as e:
                    self._log.debug("mood drift emission failed: %s", e)

        # world evolves continuously (non-finite seeds), even if no memory stored this tick
        try:
            graph.step_world(step=int(step), classify_every=50, log_every=1)
        except Exception:
            pass

        # --- Character drift check (periodic, non-blocking) ---
        if self._character_enable and stored and int(step) > 0 and int(step) % self._character_drift_every == 0:
            try:
                _seed_id = str(ident.seed.get("seed_id", "") or "").strip()
                if _seed_id:
                    _cseed = self.character_store.load_seed(workspace_id, _seed_id)
                    if _cseed and _cseed.seed_motif_id:
                        _cstate = self.character_store.load_state(workspace_id, agent_id)
                        _drift = measure_drift(
                            graph=graph,
                            motif_registry=reg,
                            coherence_field=None,
                            seed=_cseed,
                            agent_id=agent_id,
                            current_step=int(step),
                            previous_state=_cstate,
                        )
                        # Update state
                        if _cstate is None:
                            _cstate = CharacterState(
                                workspace_id=workspace_id,
                                agent_id=agent_id,
                                seed_id=_seed_id,
                            )
                        _cstate.drift_score = float(_drift["drift_score"])
                        _cstate.drift_direction = str(_drift["drift_direction"])
                        _cstate.distance_to_seed = float(_drift["distance_to_seed"])
                        _cstate.seed_basin_phi = float(_drift.get("seed_basin_phi", 0.0))
                        _cstate.seed_basin_kappa = float(_drift.get("seed_basin_kappa", 0.0))
                        _cstate.seed_basin_tension = float(_drift.get("seed_basin_tension", 0.0))
                        _cstate.seed_basin_role = str(_drift.get("seed_basin_role", "plateau"))
                        _cstate.core_count = int(_drift.get("core_count", 0))
                        _cstate.relational_count = int(_drift.get("relational_count", 0))
                        _cstate.situational_count = int(_drift.get("situational_count", 0))
                        _cstate.drift_history.append((int(step), float(_drift["drift_score"])))
                        _cstate.drift_history = _cstate.drift_history[-50:]  # cap history
                        self.character_store.save_state(workspace_id, _cstate)

                        # Gravity correction if needed
                        if float(_drift["drift_score"]) < -_cseed.drift_correction_threshold:
                            if str(_drift["drift_direction"]) == "away_seed":
                                gravity_correction(
                                    graph=graph,
                                    motif_registry=reg,
                                    embedder=self.kernel.embedder,
                                    seed=_cseed,
                                    agent_id=agent_id,
                                    step=int(step),
                                    drift_info=_drift,
                                )
            except Exception:
                pass  # Character drift is optional — never blocks ingest

        # --- Periodic checkpoint (Phase 5) — non-blocking ---
        if self._checkpoint_enable and int(step) > 0 and int(step) % self._checkpoint_interval == 0:
            try:
                _ckpt_dir = get_checkpoint_dir(self.data_dir, workspace_id, agent_id)
                _motif_summary = None
                try:
                    _ckpt_reg = ws.motif_regs.get(chosen_domain)
                    if _ckpt_reg:
                        _motif_summary = build_motif_summary(_ckpt_reg)
                except Exception as e:
                    self._log.debug("checkpoint motif summary build failed: %s", e)
                _shard_snap = None
                try:
                    _priv_dir = os.path.join(
                        self.data_dir, "workspaces", workspace_id,
                        "agents", agent_id, "private", "embeddings",
                    )
                    _shard_snap = build_shard_snapshot(_priv_dir)
                except Exception as e:
                    self._log.debug("checkpoint shard snapshot build failed for path=%s: %s", _priv_dir, e)
                _char_state_dict = None
                try:
                    _ckpt_cstate = self.character_store.load_state(workspace_id, agent_id)
                    if _ckpt_cstate:
                        from dataclasses import asdict as _da
                        _char_state_dict = _da(_ckpt_cstate)
                except Exception as e:
                    self._log.debug("checkpoint character state load failed: %s", e)
                save_checkpoint(
                    checkpoint_dir=_ckpt_dir,
                    step=int(step),
                    model_state=state,
                    corridor_monitor=self.kernel.mon,
                    character_state_dict=_char_state_dict,
                    motif_summary=_motif_summary,
                    shard_snapshot=_shard_snap,
                    max_checkpoints=self._checkpoint_max_keep,
                )
            except Exception as e:
                self._log.debug("checkpoint save failed for step=%s: %s", step, e)

        # --- Event-gated compression (Phase 6) — non-blocking ---
        if self._compress_enable and int(step) >= self._compress_min_step:
            try:
                from .compression import try_compress, check_hard_cap
                _comp_event = try_compress(self, agent_id, tri_mod, int(step), workspace_id=workspace_id)
                if _comp_event and (_comp_event.compressed + _comp_event.exported_deep) > 0:
                    logging.getLogger("torment.compression").info(
                        "compression at step %s: %d compressed, %d exported deep (trigger=%s)",
                        step, _comp_event.compressed, _comp_event.exported_deep,
                        _comp_event.trigger,
                    )
                # Hard cap safety net — fires independently of event triggers
                _hc_event = check_hard_cap(self, agent_id, int(step), workspace_id=workspace_id)
                if _hc_event and (_hc_event.compressed + _hc_event.exported_deep) > 0:
                    logging.getLogger("torment.compression").warning(
                        "HARD CAP compression at step %s: %d compressed, %d exported deep",
                        step, _hc_event.compressed, _hc_event.exported_deep,
                    )
            except Exception:
                pass  # Compression failure is always non-fatal

        # auto share-proposal emission (optional coupling)
        coupling_mode = str(ident.seed.get("coupling_mode", "read_only"))
        if stored and scope == "private" and coupling_mode in ("propose", "sync") and (half_life_days is not None):
            # auto-propose with throttling + novelty filter
            if _proposal_allowed(
                ident,
                ws.domain_policies.get(chosen_domain, {}),
                created_motif,
                float(signals.promotion_score),
                float(signals.strength),
                float(signals.confidence),
                tri_mod=tri_mod,
            ):
                regp = ws.proposals.get(chosen_domain)
                if regp is not None:
                    p = regp.submit(
                        agent_id=agent_id,
                        summary=summary,
                        embedding=emb,
                        mtype=signals.memory_type,
                        confidence=signals.confidence,
                        strength=signals.strength,
                        half_life_days=float(half_life_days),
                    )
                    proposal_id = p.proposal_id
                    # persist overlay counters
                    self.ident_store.save(ident)

        # periodically suggest bridges
        tear = float(tri_mod.get("tearing_risk", 0.0))

        p_bridge = float(tri_mod.get("bridge_p", 0.08)) * (1.0 - 0.40 * tear)
        sim_thr  = float(tri_mod.get("bridge_sim", 0.86)) + (0.03 * tear)

        p_bridge = float(np.clip(p_bridge, 0.02, 0.12))
        sim_thr  = float(np.clip(sim_thr, 0.84, 0.92))

        if stored and random_chance(p_bridge):
            ws.bridges.suggest(ws.motif_regs, sim_threshold=sim_thr, max_new=5)

        return {
            "stored": stored,
            "reinforced": bool(_reinforced_eid is not None),
            "proposal_id": proposal_id,
            "eid": eid,
            "domain_ranked": [{"id": d.domain_id, "score": d.score} for d in dom_scores],
            "domain_chosen": chosen_domain,
            "motifs": motif_ids,
            "tri_mod": tri_mod,
            "created_motif": created_motif,
            "signals": {
                "write_intent": bool(signals.write_intent),
                "memory_type": signals.memory_type,
                "strength": float(signals.strength),
                "confidence": float(signals.confidence),
                "half_life": float(signals.half_life),
                "promotion_score": float(signals.promotion_score),
                "links": list(signals.links),
                "stability_delta": float(signals.stability_delta),
            },
            "debug": debug,
        }

    def query(
        self,
        workspace_id: str,
        agent_id: str,
        query_text: str,
        top_k: int = 8,
        domain_id: Optional[str] = None,
        peek_bridges: bool = False,
        explain: bool = False,
        continuity_debug: bool = False,
    ) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        ak = self._agent_key(workspace_id, agent_id)
        ident = self.create_agent(workspace_id, agent_id)

        qemb = self.kernel.embedder.embed(query_text)
        if int(np.asarray(qemb).reshape(-1).shape[0]) != int(ws.embed_dim):
            raise HTTPException(
                status_code=409,
                detail=f"Embedding dimension mismatch; workspace '{workspace_id}' locked to {ws.embed_dim} but query embedder returned {int(np.asarray(qemb).reshape(-1).shape[0])}.",
            )
        dom_scores = ws.router.rank_domains(qemb, top_k=2)
        domains = [d.domain_id for d in dom_scores]
        if domain_id:
            domains = [domain_id] + [d for d in domains if d != domain_id]
            domains = domains[:2]

        # candidate hits from private store + each domain shared
        private_hits = self.private_graphs[ak].search(query_text, top_k=top_k, user_id=agent_id)
        shared_hits: List[Dict[str, Any]] = []
        for d in domains:
            shared_hits.extend(ws.shared_graphs[d].search(query_text, top_k=top_k, user_id=None))


        # optional bridge peek: bounded fan-out into bridged domains (approved by confidence threshold)
        bridge_peek_domains: List[str] = []
        if peek_bridges:
            rel_br = ws.bridges.relevant_to_domains(domains, top_k=12)
            # domain-aware governance: ops/meta require manual approval for peeks
            strict = any(bool(ws.domain_policies.get(d, {}).get("bridge_peek_requires_approval", False)) for d in domains)
            # approved if manually approved, else confidence heuristic (unless strict); rejected bridges ignored
            for b in rel_br:
                if str(b.get("status", "suggested")) == "rejected":
                    continue
                if strict:
                    if str(b.get("status", "suggested")) != "approved":
                        continue
                else:
                    if str(b.get("status", "suggested")) != "approved" and float(b.get("confidence", 0.0)) < 0.65:
                        continue
                od = b["to_domain"] if b["from_domain"] in domains else b["from_domain"]
                if od not in domains and od not in bridge_peek_domains:
                    bridge_peek_domains.append(od)
                if len(bridge_peek_domains) >= 2:
                    break
            peek_k = max(2, top_k // 2)
            for pd in bridge_peek_domains:
                if pd in ws.shared_graphs:
                    hits_pd = ws.shared_graphs[pd].search(query_text, top_k=peek_k, user_id=None)
                    for h in hits_pd:
                        hh = dict(h)
                        hh["via_bridge"] = True
                        hh["bridge_domain"] = pd
                        shared_hits.append(hh)


        # --- Deep memory fallback with spirit return (Phase 6) ---
        if self._compress_enable and len(private_hits) + len(shared_hits) < top_k:
            try:
                from .spirit_return import enrich_deep_memory_hit, WarmupTracker, inject_spirit_return_into_hit

                _deep_store = self._deep_stores.get(ak)
                if _deep_store:
                    _deep_qv = np.asarray(qemb, dtype=np.float32).reshape(-1)
                    _deep_hits = _deep_store.query(
                        _deep_qv,
                        top_k=max(1, top_k - len(private_hits) - len(shared_hits)),
                    )

                    # Current kernel symbol from persisted state
                    _sym_state = _load_symbol_state(self.data_dir, workspace_id, agent_id)
                    _current_sym = str(_sym_state.get("last_symbol", "◯") or "◯")

                    # Warmup tracker (lazy init per agent)
                    _warmup_dir = Path(self.data_dir) / "workspaces" / workspace_id / "agents" / agent_id / "warmup"
                    _warmup = WarmupTracker(_warmup_dir)

                    # Check which deep EIDs also exist in core (short-path compressed)
                    _core_compressed: set = set()
                    _pg = self.private_graphs.get(ak)
                    if _pg:
                        for _eid_key, _ent in _pg.entities.items():
                            if (_ent.payload or {}).get("compressed"):
                                _core_compressed.add(int(_eid_key))

                    # Current step (best-effort from existing hits)
                    _cur_step = max(
                        (int(h.get("step", 0)) for h in private_hits + shared_hits),
                        default=0,
                    )

                    for _dm in _deep_hits:
                        _ws = _warmup.get_or_create(_dm.eid, _cur_step)
                        _spirit = enrich_deep_memory_hit(
                            _dm, _current_sym, _ws, int(_dm.eid) in _core_compressed
                        )
                        shared_hits.append(inject_spirit_return_into_hit(_spirit))
            except Exception:
                pass  # Spirit return is non-fatal; deep fallback already ran or skipped

        # merge and rescore with motif alignment if available
        all_hits = private_hits + shared_hits
        rescored = []
        active_motifs = {}
        for d in domains:
            active_motifs[d] = ws.motif_regs[d].active(top_k=6)

        # build quick motif centroid lookup
        motif_centroids: Dict[str, np.ndarray] = {}
        for d in domains:
            for m in ws.motif_regs[d].motifs.values():
                motif_centroids[m.motif_id] = m.centroid_np()

        
        wants_contested = any(k in query_text.lower() for k in ["contested", "disputed", "conflict", "contradict", "both sides", "arguments"])

        # Character continuity (v1.11): affect-guided tie-breaking.
        # Only used when the query looks personal; never intended to dominate retrieval.
        try:
            _affect_enable = str(os.getenv("TORMENT_AFFECT_ENABLE", "1")).strip().lower() not in ("0", "false", "no")
        except Exception:
            _affect_enable = True
        _affect_personal = bool(_affect_enable and looks_personal(query_text))
        _q_affect_tag = "neutral"
        _q_affect_conf = 0.0
        if _affect_personal:
            try:
                _qa = classify_affect(query_text)
                _q_affect_tag = str(_qa.tag)
                _q_affect_conf = float(_qa.conf)
            except Exception:
                _q_affect_tag, _q_affect_conf = "neutral", 0.0
        try:
            _affect_match_bonus = float(os.getenv("TORMENT_AFFECT_MATCH_BONUS", "0.05"))
        except Exception:
            _affect_match_bonus = 0.05
        try:
            _affect_min_conf = float(os.getenv("TORMENT_AFFECT_MIN_CONF", "0.40"))
        except Exception:
            _affect_min_conf = 0.40
        # conflict map: map eid->max conflict score and ids for open conflicts in the queried domains
        conflict_map: Dict[int, Dict[str, Any]] = {}

        # Continuity debug (v1.11.6): compact, opt-in explanation of which continuity bonuses fired.
        try:
            _cd_top = int(os.getenv("TORMENT_CONTINUITY_DEBUG_TOP", "5"))
        except Exception:
            _cd_top = 5
        try:
            _cd_max_hits = int(os.getenv("TORMENT_CONTINUITY_DEBUG_MAX_HITS", "50"))
        except Exception:
            _cd_max_hits = 50
        _cd_enable = bool(continuity_debug)
        for d in domains:
            try:
                clist = ws.conflicts[d].list(status="open", limit=500)
            except Exception:
                clist = []
            for c in clist:
                for eid in (int(c.eid_a), int(c.eid_b)):
                    ent = conflict_map.get(eid)
                    if ent is None:
                        conflict_map[eid] = {"max_score": float(c.conflict_score), "conflict_ids": [c.conflict_id]}
                    else:
                        ent["max_score"] = max(float(ent.get("max_score", 0.0)), float(c.conflict_score))
                        ids = ent.get("conflict_ids") or []
                        if c.conflict_id not in ids:
                            ids.append(c.conflict_id)
                        ent["conflict_ids"] = ids
        
        # Character continuity: cap identity anchor dominance so anchors guide rather than dominate.
        try:
            _anchor_topk = int(os.getenv("TORMENT_ANCHOR_BOOST_TOPK", "3"))
        except Exception:
            _anchor_topk = 3
        try:
            _anchor_rest_mult = float(os.getenv("TORMENT_ANCHOR_BOOST_REST_MULT", "0.35"))
        except Exception:
            _anchor_rest_mult = 0.35
        _anchor_full_boost: set = set()
        if _anchor_topk > 0:
            try:
                _acand: List[Tuple[int, float]] = []
                for _hh in all_hits:
                    try:
                        if str(_hh.get("type")) != "identity_anchor":
                            continue
                        if bool(_hh.get("anchor_retired")):
                            continue
                        _acand.append((int(_hh.get("eid", -1)), float(_hh.get("score", 0.0))))
                    except Exception:
                        continue
                _acand.sort(key=lambda x: x[1], reverse=True)
                _anchor_full_boost = set([e for (e, _s) in _acand[:_anchor_topk] if e >= 0])
            except Exception:
                _anchor_full_boost = set()

        # Emotional stability: mood spiral dampening.
        # If recent drift history shows multiple negative shifts, reduce the weight of older negative-tone memories.
        try:
            _spiral_enable = str(os.getenv("TORMENT_MOOD_SPIRAL_ENABLE", "1")).strip().lower() not in ("0", "false", "no")
        except Exception:
            _spiral_enable = True
        try:
            _spiral_window = int(os.getenv("TORMENT_MOOD_SPIRAL_WINDOW_STEPS", "800"))
        except Exception:
            _spiral_window = 800
        try:
            _spiral_min_drifts = int(os.getenv("TORMENT_MOOD_SPIRAL_MIN_NEG_DRIFTS", "2"))
        except Exception:
            _spiral_min_drifts = 2
        try:
            _spiral_older_than = int(os.getenv("TORMENT_MOOD_SPIRAL_OLDER_THAN_STEPS", "250"))
        except Exception:
            _spiral_older_than = 250
        try:
            _spiral_penalty_max = float(os.getenv("TORMENT_MOOD_SPIRAL_PENALTY_MAX", "0.08"))
        except Exception:
            _spiral_penalty_max = 0.08

        _spiral_neg_recent = 0
        if _spiral_enable and str(agent_id) in self.private_graphs:
            try:
                _st = _load_affect_state(self.data_dir, ws.workspace_id, str(agent_id))
                _dh = _st.get("drift_hist") or []
                if not isinstance(_dh, list):
                    _dh = []
                # Determine current step from hits (best-effort)
                _torment_cur_step = -1
                for _hh in all_hits:
                    try:
                        _torment_cur_step = max(_torment_cur_step, int(_hh.get("step", -1)))
                    except Exception as e:
                        self._log.debug("failed to extract step from hit: %s", e)
                if _torment_cur_step >= 0:
                    _neg = {"stressed", "sad", "angry"}
                    for _e in _dh[-20:]:
                        try:
                            if int(_e.get("step", -10**9)) < _torment_cur_step - _spiral_window:
                                continue
                            if str(_e.get("to")) in _neg:
                                _spiral_neg_recent += 1
                        except Exception:
                            continue
            except Exception:
                _spiral_neg_recent = 0
        now_ts = _now_ts()
        for h in all_hits:
            sim = float(h.get("score", 0.0))
            strength = float(h.get("strength", 0.5))
            ts = int(h.get("created_ts", now_ts))
            recency_days = max(0.0, (now_ts - ts) / 86400.0)
            motifs = h.get("motifs") or []
            if not motifs and motif_centroids:
                # infer best motif by similarity
                best_mid = None
                best_ms = -1.0
                for mid, c in motif_centroids.items():
                    s2 = float(np.dot(qemb, c) / ((np.linalg.norm(qemb)+1e-12)*(np.linalg.norm(c)+1e-12)))
                    if s2 > best_ms:
                        best_ms = s2
                        best_mid = mid
                if best_mid is not None and best_ms >= 0.55:
                    motifs = [best_mid]

            motif_alignment = 0.0
            for mid in motifs:
                c = motif_centroids.get(mid)
                if c is None:
                    continue
                motif_alignment = max(motif_alignment, float(np.dot(qemb, c) / ((np.linalg.norm(qemb)+1e-12)*(np.linalg.norm(c)+1e-12))))
            contradiction_risk = float(h.get("contradiction_risk", 0.0))
            conflict_info = conflict_map.get(int(h.get("eid", -1)))
            conflict_penalty = 0.0
            conflict_ids: List[str] = []
            conflict_status = None
            if conflict_info is not None and str(h.get("scope", "")) == "shared" and bool(h.get("canon", False)):
                conflict_status = "open"
                conflict_ids = list(conflict_info.get("conflict_ids") or [])
                conflict_penalty = float(conflict_info.get("max_score", 0.0))
                if not wants_contested:
                    contradiction_risk = max(contradiction_risk, 0.5 * conflict_penalty)
            mtype = str(h.get("type") or "")
            type_bonus = 0.0

            # Continuity debug collects a compact breakdown (no behavioral change when disabled).
            _bon = None
            if _cd_enable:
                _bon = {
                    "self_thread": 0.0,
                    "self_anchor": 0.0,
                    "thread_window": 0.0,
                    "affect_match": 0.0,
                    "mood_drift": 0.0,
                    "mood_spiral_penalty": 0.0,
                }

            # Character continuity: prefer the agent's own private thread.
            try:
                self_bonus = float(os.getenv("TORMENT_SELF_MEMORY_BONUS", "0.06"))
            except Exception:
                self_bonus = 0.06
            if str(h.get("scope", "")) == "private" and str(h.get("agent_id", "")) == str(agent_id):
                type_bonus += self_bonus
                if _bon is not None:
                    _bon["self_thread"] += float(self_bonus)

            # Character continuity: recent thread coherence window.
            # Boost memories from the same agent's private thread that are very recent in step-time.
            # This makes the agent feel like it stays "in the conversation" without adding governance.
            try:
                thread_window_steps = int(os.getenv("TORMENT_THREAD_WINDOW_STEPS", "50"))
            except Exception:
                thread_window_steps = 50
            try:
                thread_window_bonus = float(os.getenv("TORMENT_THREAD_WINDOW_BONUS", "0.08"))
            except Exception:
                thread_window_bonus = 0.08
            if thread_window_steps > 0 and thread_window_bonus > 0.0 and str(h.get("scope", "")) == "private" and str(h.get("agent_id", "")) == str(agent_id):
                # Determine the current step from available hits (best-effort).
                if "_torment_q_step" not in locals():
                    _torment_q_step = -1
                    for _hh in all_hits:
                        try:
                            s = int(_hh.get("step", -1))
                        except Exception:
                            s = -1
                        if s > _torment_q_step:
                            _torment_q_step = s
                try:
                    hit_step = int(h.get("step", -1))
                except Exception:
                    hit_step = -1
                if _torment_q_step >= 0 and hit_step >= 0:
                    delta = max(0, _torment_q_step - hit_step)
                    if delta <= thread_window_steps:
                        # Linear taper: newest gets full bonus.
                        _tw = thread_window_bonus * (1.0 - (float(delta) / float(max(1, thread_window_steps))))
                        type_bonus += _tw
                        if _bon is not None:
                            _bon["thread_window"] += float(_tw)
            if mtype == "identity_anchor":
                # Character continuity: identity anchors get a consistent lift, but cap dominance.
                _ab = 0.12
                try:
                    _eid = int(h.get("eid", -1))
                except Exception:
                    _eid = -1
                if _anchor_full_boost and _eid not in _anchor_full_boost:
                    _ab = float(_ab) * float(_anchor_rest_mult)
                type_bonus += float(_ab)
                if _bon is not None:
                    # This is the anchor lift (capped by top-k logic elsewhere).
                    _bon["self_anchor"] += float(_ab)
                # Additional lift when the anchor belongs to the querying agent's private thread.
                if str(h.get("scope", "")) == "private" and str(h.get("agent_id", "")) == str(agent_id):
                    try:
                        _sab = float(os.getenv("TORMENT_SELF_ANCHOR_BONUS", "0.04"))
                    except Exception:
                        _sab = 0.04
                    type_bonus += float(_sab)
                    if _bon is not None:
                        _bon["self_anchor"] += float(_sab)

            # Emotional continuity: if the query looks personal and has a confident affect tag,
            # lightly prefer memories with matching affect.
            if _affect_personal and _q_affect_tag and _q_affect_tag != "neutral" and _q_affect_conf >= _affect_min_conf:
                try:
                    h_tag = str(h.get("affect_tag") or "")
                    h_conf = float(h.get("affect_conf") or 0.0)
                except Exception:
                    h_tag, h_conf = "", 0.0
                if h_tag and h_tag == _q_affect_tag and h_conf >= _affect_min_conf:
                    _am = _affect_match_bonus * float(min(_q_affect_conf, h_conf))
                    type_bonus += _am
                    if _bon is not None:
                        _bon["affect_match"] += float(_am)
                # Emotional continuity v2: mood drift memories are useful for personal queries.
                try:
                    _md_bonus = float(os.getenv("TORMENT_MOOD_DRIFT_QUERY_BONUS", "0.04"))
                except Exception:
                    _md_bonus = 0.04
                if _affect_personal and str(h.get("type")) == "mood_drift":
                    type_bonus += float(_md_bonus)
                    if _bon is not None:
                        _bon["mood_drift"] += float(_md_bonus)

                # Emotional stability: dampen older negative-tone memories if recent mood drift trends negative.
                if _spiral_enable and _spiral_neg_recent >= _spiral_min_drifts:
                    try:
                        _neg = {"stressed", "sad", "angry"}
                        _ht = str(h.get("affect_tag") or "")
                        _hs = int(h.get("step", -1))
                    except Exception:
                        _ht, _hs = "", -1
                    if _ht in _neg and _hs >= 0:
                        try:
                            _cur = int(_torment_cur_step if "_torment_cur_step" in locals() else -1)
                        except Exception:
                            _cur = -1
                        if _cur >= 0:
                            _age = max(0, _cur - _hs)
                            if _age > _spiral_older_than:
                                _age_fac = min(1.0, float(_age - _spiral_older_than) / float(max(1, _spiral_window)))
                                _trend_fac = min(1.0, 0.5 + 0.25 * float(_spiral_neg_recent - _spiral_min_drifts + 1))
                                _sp = float(_spiral_penalty_max) * float(_age_fac) * float(_trend_fac)
                                type_bonus -= _sp
                                if _bon is not None:
                                    _bon["mood_spiral_penalty"] += float(_sp)

            base_score = score_hit(sim=sim, strength=strength, recency_days=recency_days, motif_alignment=motif_alignment, contradiction_risk=contradiction_risk, type_bonus=0.0)
            final = score_hit(sim=sim, strength=strength, recency_days=recency_days, motif_alignment=motif_alignment, contradiction_risk=contradiction_risk, type_bonus=type_bonus)

            # SRG scoring bonuses + breathing evolution (Phase 3)
            if self._srg_enable:
                _srg_hit = (h.get("payload") or {}).get("srg")
                if _srg_hit:
                    # Same-band resonance: 8% boost
                    if hasattr(self, "_srg_last_ingest_band") and _srg_hit.get("R_band") == self._srg_last_ingest_band:
                        final *= 1.08
                    # Crystal identity anchor: 5% boost
                    if _srg_hit.get("is_crystal", False):
                        final *= 1.05
                    # Class A (deep/slow heartbeat): 3% stability bonus
                    if _srg_hit.get("heartbeat_class") == "A":
                        final *= 1.03

                    # Breathing evolution: retrieved memories are "active" → evolve
                    try:
                        from .srg_engine import SRGMemoryState as _SMS, evolve_breathing as _evolve
                        _srg_live = _SMS.from_dict(_srg_hit)
                        _evolve(_srg_live)
                        # Write back evolved state to the in-memory entity
                        _hit_eid = h.get("eid")
                        if _hit_eid is not None:
                            # Try private graph first, then each domain's shared graph
                            _hit_ent = None
                            _pg = self.private_graphs.get(ak)
                            if _pg is not None:
                                _hit_ent = _pg.entities.get(int(_hit_eid))
                            if _hit_ent is None:
                                for _sg in ws.shared_graphs.values():
                                    _hit_ent = _sg.entities.get(int(_hit_eid))
                                    if _hit_ent is not None:
                                        break
                            if _hit_ent is not None:
                                _hit_ent.payload["srg"] = _srg_live.to_dict()
                    except Exception as e:
                        self._log.debug("failed to write srg payload to entity eid=%s: %s", _hit_eid, e)

            # Phase D3: collective-provenance retrieval discount
            # Echoes are influences, not autobiography — discount so they don't
            # outrank organic private memories in retrieval.
            _h_provenance = str((h.get("payload") or h).get("provenance", "") or h.get("provenance", "") or "")
            if _h_provenance == "collective":
                try:
                    _coll_discount = float(os.getenv("TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT", "0.50"))
                except Exception:
                    _coll_discount = 0.50
                final *= _coll_discount

            hh = dict(h)
            hh["motifs"] = motifs
            hh["final_score"] = final
            if _cd_enable:
                hh["_base_score"] = float(base_score)
                hh["_bonus_components"] = _bon
            hh["motif_alignment"] = motif_alignment
            if conflict_status is not None:
                    hh["conflict_status"] = conflict_status
                    hh["conflict_ids"] = conflict_ids
                    hh["conflict_penalty"] = conflict_penalty

            if explain:
                hh["explain"] = {
                    "sim": sim,
                    "strength": strength,
                    "recency_days": recency_days,
                    "motif_alignment": motif_alignment,
                    "contradiction_risk": contradiction_risk,
                    "conflict_status": conflict_status,
                    "conflict_penalty": conflict_penalty,
                    "conflict_ids": conflict_ids,
                    "weights": {"alpha": 0.35, "beta": 0.10, "gamma": 0.20, "delta": 0.30},
                }
            rescored.append(hh)

        rescored.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        rescored = rescored[:top_k]

        continuity_dbg: Optional[Dict[str, Any]] = None
        if _cd_enable:
            # Compact summary of which continuity mechanisms fired.
            enabled = {
                "self_thread": True,
                "thread_window": True,
                "identity_anchors": True,
                "affect_match": bool(_affect_enable),
                "mood_drift": bool(str(os.getenv("TORMENT_MOOD_DRIFT_ENABLE", "1")).strip().lower() not in ("0", "false", "no")),
                "mood_spiral": bool(str(os.getenv("TORMENT_MOOD_SPIRAL_ENABLE", "1")).strip().lower() not in ("0", "false", "no")),
            }
            qsig = {
                "personal_query": bool(_affect_personal),
                "query_affect_tag": _q_affect_tag,
                "query_affect_conf": float(_q_affect_conf),
            }
            try:
                rc = self._role_context(ws, agent_id)
                qsig["dominant_role"] = rc.get("dominant_role")
            except Exception:
                qsig["dominant_role"] = None

            # Aggregate how many results were affected by each bonus type.
            summary_counts = {"self_thread": 0, "self_anchor": 0, "thread_window": 0, "affect_match": 0, "mood_drift": 0, "mood_spiral_penalty": 0}
            for hh in rescored[: min(len(rescored), max(0, _cd_max_hits))]:
                bc = hh.get("_bonus_components") or {}
                for k in summary_counts.keys():
                    try:
                        if float(bc.get(k, 0.0)) != 0.0:
                            summary_counts[k] += 1
                    except Exception:
                        continue

            top_breakdown = []
            for hh in rescored[: min(len(rescored), max(0, _cd_top))]:
                bc = hh.get("_bonus_components") or {}
                top_breakdown.append(
                    {
                        "eid": hh.get("eid"),
                        "base_score": float(hh.get("_base_score", hh.get("final_score", 0.0))),
                        "final_score": float(hh.get("final_score", 0.0)),
                        "bonuses": {
                            "self_thread": float(bc.get("self_thread", 0.0)),
                            "self_anchor": float(bc.get("self_anchor", 0.0)),
                            "thread_window": float(bc.get("thread_window", 0.0)),
                            "affect_match": float(bc.get("affect_match", 0.0)),
                            "mood_drift": float(bc.get("mood_drift", 0.0)),
                        },
                    }
                )

            continuity_dbg = {
                "mode": "character_continuity",
                "bonuses_enabled": enabled,
                "query_signals": qsig,
                "applied_bonuses_summary": summary_counts,
                "top_hits_bonus_breakdown": top_breakdown,
            }

            # Strip internal debug keys from normal results.
            for hh in rescored:
                if "_base_score" in hh:
                    hh.pop("_base_score", None)
                if "_bonus_components" in hh:
                    hh.pop("_bonus_components", None)

        bridges = ws.bridges.relevant_to_domains(domains + bridge_peek_domains, top_k=8)

        dominant = dominant_thread(active_motifs)

        # --- Character context assembly (optional, non-blocking) ---
        _char_ctx: Optional[Dict[str, Any]] = None
        if self._character_enable:
            try:
                _seed_id = str(ident.seed.get("seed_id", "") or "").strip()
                if _seed_id:
                    _cseed = self.character_store.load_seed(workspace_id, _seed_id)
                    if _cseed and _cseed.seed_motif_id:
                        _cstate = self.character_store.load_state(workspace_id, agent_id)
                        _drift_info = None
                        if _cstate:
                            _drift_info = {
                                "drift_score": _cstate.drift_score,
                                "drift_direction": _cstate.drift_direction,
                                "explanation": "",
                                "seed_basin_role": _cstate.seed_basin_role,
                                "relational_count": _cstate.relational_count,
                            }
                        _char_ctx = assemble_character_context(
                            graph=self.private_graphs.get(ak),
                            seed=_cseed,
                            agent_id=agent_id,
                            hits=rescored,
                            drift_info=_drift_info,
                        )
            except Exception:
                pass  # Character context is optional

        return {
            "domains": [{"id": d.domain_id, "score": d.score} for d in dom_scores],
            "domain_used": domains,
            "bridge_peek_domains": bridge_peek_domains,
            "results": rescored,
            "motifs": {
                "active": [m for d in domains for m in active_motifs.get(d, [])],
                "dominant_thread": dominant,
            },
            "bridges": bridges,
            "role_context": self._role_context(ws, agent_id),
            "embed_context": self._embed_context(ws),
            **({"continuity_debug": continuity_dbg} if continuity_dbg is not None else {}),
            **({"character_context": _char_ctx} if _char_ctx is not None else {}),
            **(self._collective_query_context(workspace_id, domains) if self._hivemind_enable else {}),
        }

    def feedback(
        self,
        workspace_id: str,
        agent_id: str,
        retrieved_ids: List[int],
        used_successfully: bool,
        user_confirmed: bool = False,
        contradiction_detected: bool = False,
        novel_motif_created: bool = False,
        shared_memory_used: bool = False,
        bridges_used: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        ident = self.create_agent(workspace_id, agent_id)
        ws = self.get_workspace(workspace_id)
        # very conservative overlay evolution
        eta = 0.002
        overlay = ident.overlay

        # compute simple signals
        E_success = 1.0 if used_successfully and user_confirmed else 0.0
        E_noise = 1.0 if (not used_successfully) and retrieved_ids else 0.0
        E_contra = 1.0 if contradiction_detected else 0.0
        E_collect = 1.0 if (shared_memory_used and used_successfully) else 0.0
        E_novel = 1.0 if (novel_motif_created and used_successfully) else 0.0

        # update overlay within a trust region around defaults (±0.25)
        def upd(k: str, delta: float):
            base = DEFAULT_AGENT_OVERLAY.get(k, overlay.get(k, 0.5))
            lo = max(0.0, base - 0.25)
            hi = min(1.0, base + 0.25)
            overlay[k] = float(min(hi, max(lo, overlay.get(k, base) + delta)))

        upd("write_threshold", -eta * E_success + eta * E_noise + 2*eta*E_contra)
        upd("decay_scale", -eta * E_success + eta * E_noise + eta*E_contra)
        upd("promotion_bias", eta * E_success - eta * E_contra)
        upd("novelty_bias", eta * E_novel - eta * E_noise)
        upd("motif_sensitivity", eta * E_success + eta * E_novel - eta * E_noise)
        upd("contradiction_sensitivity", eta * E_contra)
        upd("reinforcement_gain", eta * E_success)
        upd("coupling_strength", eta * E_collect - eta * E_noise)
        upd("shared_trust", eta * E_collect - eta * E_contra)
        # stability_guard: increase when turbulence
        upd("stability_guard", eta * E_contra)

        # bridge confidence learning (optional)
        if bridges_used:
            # Each item: {"from_domain":..., "from_motif":..., "to_domain":..., "to_motif":...}
            delta = 0.01 if (used_successfully and user_confirmed) else (-0.01 if (not used_successfully) else 0.0)
            for b in bridges_used:
                ws.bridges.update_confidence(
                    from_domain=b.get("from_domain",""),
                    from_motif=b.get("from_motif",""),
                    to_domain=b.get("to_domain",""),
                    to_motif=b.get("to_motif",""),
                    delta=delta,
                )

        self.ident_store.save(ident)
        # log feedback event (append-only) for causal tracing
        fb_path = os.path.join(self.data_dir, "workspaces", workspace_id, "agents", agent_id, "feedback_events.jsonl")
        os.makedirs(os.path.dirname(fb_path), exist_ok=True)
        with open(fb_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "FEEDBACK",
                "ts": _now_ts(),
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "retrieved_ids": retrieved_ids,
                "used_successfully": bool(used_successfully),
                "user_confirmed": bool(user_confirmed),
                "contradiction_detected": bool(contradiction_detected),
                "novel_motif_created": bool(novel_motif_created),
                "shared_memory_used": bool(shared_memory_used),
                "bridges_used": bridges_used or [],
                "overlay": dict(ident.overlay),
            }, ensure_ascii=False) + "\n")
        return {"ok": True, "overlay": ident.overlay}



    
    def decide_bridge(self, workspace_id: str, from_domain: str, from_motif: str, to_domain: str, to_motif: str, decision: str) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        ok = ws.bridges.decide(from_domain, from_motif, to_domain, to_motif, decision)
        return {"ok": bool(ok), "workspace_id": workspace_id, "decision": decision, "from_domain": from_domain, "to_domain": to_domain}


    def propose_share(
        self,
        workspace_id: str,
        agent_id: str,
        summary: str,
        embedding: Optional[List[float]] = None,
        domain_id: Optional[str] = None,
        mtype: str = "fact",
        confidence: float = 0.6,
        strength: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Submit a proposal to promote a memory into the shared domain space.

        Default policy is private-write/shared-read; shared-write is mediated through proposals.
        """
        ws = self.get_workspace(workspace_id)
        self.create_agent(workspace_id, agent_id)

        if embedding is None:
            emb = self.kernel.embedder.embed(summary)
        else:
            emb = np.asarray(embedding, dtype=np.float32)

        dom_scores = ws.router.rank_domains(emb, top_k=2)
        chosen_domain = domain_id or (dom_scores[0].domain_id if dom_scores else "research")

        prop = ws.proposals[chosen_domain].submit(
            agent_id=agent_id,
            summary=summary,
            embedding=emb,
            mtype=mtype,
            confidence=confidence,
            strength=strength,
        )
        return {
            "ok": True,
            "proposal": {
                "proposal_id": prop.proposal_id,
                "workspace_id": prop.workspace_id,
                "domain_id": prop.domain_id,
                "agent_id": prop.agent_id,
                "created_ts": prop.created_ts,
                "status": prop.status,
            },
            "domain_ranked": [{"id": d.domain_id, "score": d.score} for d in dom_scores],
        }

    def process_proposals(
        self,
        workspace_id: str,
        domain_id: str,
        max_to_process: int = 200,
        sim_threshold: float = 0.90,
        min_distinct_agents: int = 0,
        step: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Process pending share proposals for a domain.

        Simple governance v1:
          - group pending proposals by embedding similarity
          - approve a group if it has >= min_distinct_agents unique agent_id
          - store one shared memory node (summary from the highest-strength proposal)
          - mark all proposals in the approved group as approved; rest remain pending
        """
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.domains:
            raise ValueError(
                f"Unknown domain_id '{domain_id}' in workspace '{workspace_id}'. "
                f"Registered domains: {ws.domains}. "
                f"Domains are structural — register them at workspace creation or via add_domain()."
            )

        reg = ws.proposals[domain_id]
        if min_distinct_agents <= 0:
            min_distinct_agents = int(ws.domain_policies.get(domain_id, {}).get("shared_min_distinct_agents", 2))
        pending = reg.list_pending(limit=max_to_process)
        if not pending:
            return {"ok": True, "processed": 0, "approved_groups": 0, "approved": 0}

        # Prepare embeddings
        P = pending
        E = [np.asarray(p.embedding, dtype=np.float32) for p in P]

        used = set()
        approved = 0
        approved_groups = 0
        created_shared_eids: List[int] = []

        for i, pi in enumerate(P):
            if pi.proposal_id in used:
                continue
            # build group around i
            group = [i]
            used.add(pi.proposal_id)
            agents = {pi.agent_id}
            for j in range(i+1, len(P)):
                pj = P[j]
                if pj.proposal_id in used:
                    continue
                s = cos_sim(E[i], E[j])
                if s >= sim_threshold:
                    group.append(j)
                    used.add(pj.proposal_id)
                    agents.add(pj.agent_id)

            if len(agents) >= min_distinct_agents:
                approved_groups += 1
                # choose representative proposal: highest strength then confidence
                rep_idx = max(group, key=lambda k: (P[k].strength, P[k].confidence))
                rep = P[rep_idx]
                emb = E[rep_idx]

                emb_provider = str(getattr(self.kernel.embedder, "provider", ""))
                emb_model = str(getattr(self.kernel.embedder, "model", ""))
                emb_dim = int(np.asarray(emb).reshape(-1).shape[0])
                emb_ck = embedding_checksum(rep.summary, emb_provider, emb_model)

                # pre-scan for potential canon conflicts against existing shared canon
                sg = ws.shared_graphs[domain_id]
                existing = sg.search_by_embedding(emb, top_k=6, user_id=None, canon_only=True)

                # store into shared graph
                eid = sg.add_memory(
                    summary=rep.summary,
                    embedding=emb,
                    mtype=rep.mtype,
                    strength=max(0.7, float(rep.strength)),
                    confidence=max(0.7, float(rep.confidence)),
                    half_life_days=30.0,  # shared defaults to slow decay
                    links=[],
                    canon=True,
                    user_id="collective",
                    step=step if step is not None else int(time.time()),
                    extra_payload={
                        "workspace_id": workspace_id,
                        "domain_id": domain_id,
                        "scope": "shared",
                        "agent_id": "collective",
                        "source": "proposal_group",
                        "embedding_provider": emb_provider,
                        "embedding_model": emb_model,
                        "embedding_dim": emb_dim,
                        "embedding_checksum": emb_ck,
                        "support_agents": sorted(list(agents)),
                        "source_proposal_ids": [P[k].proposal_id for k in group],
                    },
                )
                created_shared_eids.append(int(eid))

                # conflict detection (heuristic) against nearest existing canon
                for h in existing:
                    old_eid = int(h.get("eid"))
                    if old_eid <= 0:
                        continue
                    sim = float(h.get("score", 0.0))
                    old_sum = str(h.get("summary", ""))
                    is_conflict, cscore, reason = _detect_canon_conflict(rep.summary, old_sum, sim)
                    if is_conflict:
                        ws.conflicts[domain_id].add(
                            eid_a=int(old_eid),
                            eid_b=int(eid),
                            sim=float(sim),
                            conflict_score=float(cscore),
                            reason=str(reason or "heuristic"),
                        )
                        # one conflict per new node is enough for now
                        break

                # attach to motifs
                ws.motif_regs[domain_id].attach_or_create(emb, memory_eid=int(eid), agent_id="collective", summary=rep.summary, attach_threshold=0.62)

                # motif entropy + merge suggestions (domain)
                pol = ws.domain_policies.get(domain_id, {})
                try:
                    ws.motif_regs[domain_id].update_entropy_and_suggest(
                        target_n=int(pol.get("motif_entropy_target_n", 24)),
                        entropy_high=float(pol.get("motif_entropy_high", 0.72)),
                        sim_threshold=float(pol.get("motif_merge_similarity", 0.93)),
                        max_suggestions=int(pol.get("motif_merge_max_suggestions", 20)),
                        auto_merge=bool(pol.get("auto_merge_motifs", False)),
                        auto_merge_trigger=float(pol.get("auto_merge_entropy_trigger", 0.80)),
                    )
                except Exception as e:
                    self._log.debug("group proposal motif entropy update failed for domain=%s: %s", domain_id, e)

                # mark all proposals in group approved
                for k in group:
                    reg.mark(P[k].proposal_id, status="approved", note=f"approved via group (agents={len(agents)})")
                    approved += 1
            else:
                # Not enough agreement; leave pending (no event)
                pass

        # Refresh bridge suggestions after new shared nodes
        if created_shared_eids:
            ws.bridges.suggest(ws.motif_regs, sim_threshold=0.86, max_new=10)

        # Domain suggestion heuristic: if we keep seeing strong motifs poorly aligned with any domain centroid.
        self._maybe_suggest_domain(ws, domain_id=domain_id)

        return {
            "ok": True,
            "processed": len(P),
            "approved_groups": approved_groups,
            "approved": approved,
            "created_shared_eids": created_shared_eids,
        }

    

    def motif_entropy(self, workspace_id: str, domain_id: str) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.motif_regs:
            raise ValueError("Unknown domain_id")
        pol = ws.domain_policies.get(domain_id, {})
        rep = ws.motif_regs[domain_id].entropy_report(target_n=int(pol.get("motif_entropy_target_n", 24)))
        rep["domain_id"] = domain_id
        rep["workspace_id"] = workspace_id
        return rep

    def list_motif_merges(self, workspace_id: str, domain_id: str, status: str = "suggested", limit: int = 200) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.motif_regs:
            raise ValueError("Unknown domain_id")
        items = ws.motif_regs[domain_id].list_merge_suggestions(status=status, limit=limit)
        return {"workspace_id": workspace_id, "domain_id": domain_id, "count": len(items), "items": items}

    def decide_motif_merge(self, workspace_id: str, domain_id: str, suggestion_id: str, decision: str, note: str = "") -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.motif_regs:
            raise ValueError("Unknown domain_id")
        res = ws.motif_regs[domain_id].decide_merge(suggestion_id, decision=decision, note=note)
        return {"workspace_id": workspace_id, "domain_id": domain_id, "result": res}

    def list_conflicts(self, workspace_id: str, domain_id: str, status: str = "open", limit: int = 200) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.conflicts:
            raise ValueError("Unknown domain_id")
        items = ws.conflicts[domain_id].list(status=status, limit=limit)
        return {
            "workspace_id": workspace_id,
            "domain_id": domain_id,
            "count": len(items),
            "items": [asdict(x) for x in items],
        }

    def decide_conflict(self, workspace_id: str, domain_id: str, conflict_id: str, decision: str, note: str = "") -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.conflicts:
            raise ValueError("Unknown domain_id")
        ws.conflicts[domain_id].decide(conflict_id=conflict_id, decision=decision, note=note)
        return {"workspace_id": workspace_id, "domain_id": domain_id, "conflict_id": conflict_id, "decision": decision}

    def approve_domain_suggestion(self, workspace_id: str, suggested_domain_id: str) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        dom = re.sub(r"[^a-zA-Z0-9_\-]", "_", suggested_domain_id.strip().lower())
        if not dom:
            raise ValueError("invalid domain_id")
        ws.add_domain(dom)
        # mark suggestion as approved in file (best-effort)
        obj = {"suggestions": []}
        if os.path.exists(ws.domain_suggestions_path):
            with open(ws.domain_suggestions_path, "r", encoding="utf-8") as f:
                try:
                    obj = json.load(f)
                except Exception:
                    obj = {"suggestions": []}
        for s in obj.get("suggestions", []):
            if str(s.get("domain_id","")).strip().lower() == suggested_domain_id.strip().lower():
                s["approved"] = True
                s["approved_ts"] = _now_ts()
        with open(ws.domain_suggestions_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
        return {"workspace_id": workspace_id, "domain_id": dom, "domains": ws.domains}


    def list_proposals(
        self,
        workspace_id: str,
        domain_id: str,
        status: str = "pending",
        limit: int = 200,
    ) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.domains:
            raise ValueError("Unknown domain_id")
        reg = ws.proposals[domain_id]
        latest = reg.apply_events()
        items = [p for p in latest.values() if (status == "any" or p.status == status)]
        items.sort(key=lambda p: p.created_ts, reverse=True)
        items = items[:limit]
        return {
            "workspace_id": workspace_id,
            "domain_id": domain_id,
            "status": status,
            "count": len(items),
            "proposals": [p.__dict__ for p in items],
        }

    def decide_proposal(
        self,
        workspace_id: str,
        domain_id: str,
        proposal_id: str,
        decision: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Manual moderation override: approve or reject a single proposal.

        If approved, it is immediately materialized as a shared canon memory node (single-source),
        marked approved in events, attached to motifs, and bridges/domain suggestions refreshed.
        """
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.domains:
            raise ValueError("Unknown domain_id")
        reg = ws.proposals[domain_id]
        latest = reg.apply_events()
        p = latest.get(proposal_id)
        if p is None:
            raise ValueError("Unknown proposal_id")
        if decision not in ("approve", "reject"):
            raise ValueError("decision must be approve|reject")

        if decision == "reject":
            reg.mark(proposal_id, status="rejected", note=note or "rejected manually")
            return {"ok": True, "decision": "rejected", "proposal_id": proposal_id}

        emb = np.asarray(p.embedding, dtype=np.float32)
        emb_provider = str(getattr(self.kernel.embedder, "provider", ""))
        emb_model = str(getattr(self.kernel.embedder, "model", ""))
        emb_dim = int(np.asarray(emb).reshape(-1).shape[0])
        emb_ck = embedding_checksum(p.summary, emb_provider, emb_model)
        sg = ws.shared_graphs[domain_id]
        eid = sg.add_memory(
            summary=p.summary,
            embedding=emb,
            mtype=p.mtype,
            strength=max(0.7, float(p.strength)),
            confidence=max(0.7, float(p.confidence)),
            half_life_days=30.0,
            links=[],
            canon=True,
            user_id="collective",
            step=int(time.time()),
            extra_payload={
                "workspace_id": workspace_id,
                "domain_id": domain_id,
                "scope": "shared",
                "agent_id": "collective",
                "source": "proposal_manual",
                "embedding_provider": emb_provider,
                "embedding_model": emb_model,
                "embedding_dim": emb_dim,
                "embedding_checksum": emb_ck,
                "support_agents": [p.agent_id],
            },
        )
        ws.motif_regs[domain_id].attach_or_create(emb, memory_eid=int(eid), agent_id="collective", summary=p.summary, attach_threshold=0.62)
        reg.mark(proposal_id, status="approved", note=note or "approved manually")
        ws.bridges.suggest(ws.motif_regs, sim_threshold=0.86, max_new=5)
        self._maybe_suggest_domain(ws, domain_id=domain_id)
        return {"ok": True, "decision": "approved", "proposal_id": proposal_id, "created_shared_eid": int(eid)}


    def _maybe_suggest_domain(self, ws: Workspace, domain_id: str) -> None:
        """Suggest new domains based on strong motifs that are poorly aligned with their current domain centroid."""
        # Build domain centroid from motif centroids
        dom_centroids: Dict[str, np.ndarray] = {}
        for d, r in ws.motif_regs.items():
            cs = [m.centroid_np() for m in r.motifs.values() if m.centroid_np().size > 0]
            if not cs:
                continue
            dom_centroids[d] = np.mean(np.stack(cs, axis=0), axis=0)

        dc = dom_centroids.get(domain_id)
        if dc is None:
            return

        suggestions = []
        for m in ws.motif_regs[domain_id].motifs.values():
            if float(getattr(m, 'strength', 0.0)) < 0.75:
                continue
            c = m.centroid_np()
            if c.size == 0:
                continue
            s = float(np.dot(c, dc) / ((np.linalg.norm(c)+1e-12)*(np.linalg.norm(dc)+1e-12)))
            if s < 0.35:
                label = getattr(m, 'label', '') or 'emergent'
                name = re.sub(r"[^a-z0-9_]+", "_", label.lower()).strip("_")
                if not name:
                    name = 'emergent'
                name = f"suggested_{name}"[:32]
                suggestions.append({
                    "domain_id": name,
                    "from_domain": domain_id,
                    "motif_id": m.motif_id,
                    "motif_label": label,
                    "strength": float(getattr(m, 'strength', 0.0)),
                    "score": s,
                    "ts": _now_ts(),
                    "approved": False,
                })

        if not suggestions:
            return

        existing = []
        if os.path.exists(ws.domain_suggestions_path):
            try:
                with open(ws.domain_suggestions_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f).get('suggestions', [])
            except Exception:
                existing = []
        seen = {(e.get('domain_id'), e.get('motif_id')) for e in existing}
        for s in suggestions:
            key = (s['domain_id'], s['motif_id'])
            if key in seen:
                continue
            existing.append(s)
            seen.add(key)
        with open(ws.domain_suggestions_path, 'w', encoding='utf-8') as f:
            json.dump({"suggestions": existing[-500:]}, f, indent=2, ensure_ascii=False)


    def list_bridges(self, workspace_id: str, status: str = "any", limit: int = 200) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        status = (status or "any").lower().strip()
        bridges = ws.bridges.bridges
        if status != "any":
            bridges = [b for b in bridges if (b.status or "suggested") == status]
        bridges = sorted(bridges, key=lambda b: (b.status != "suggested", -float(b.confidence), -int(b.updated_ts)))
        if limit:
            bridges = bridges[: int(limit)]
        return {"workspace_id": workspace_id, "bridges": [b.__dict__ for b in bridges]}


    def trace(self, workspace_id: str, agent_id: str, query_text: str, eids: List[int], domain_id: Optional[str] = None) -> Dict[str, Any]:
        """Explain why specific memories scored the way they did for a query."""
        ws = self.get_workspace(workspace_id)
        ak = self._agent_key(workspace_id, agent_id)
        self.create_agent(workspace_id, agent_id)
        qemb = self.kernel.embedder.embed(query_text)
        dom_scores = ws.router.rank_domains(qemb, top_k=2)
        domains = [d.domain_id for d in dom_scores]
        if domain_id:
            domains = [domain_id] + [d for d in domains if d != domain_id]
            domains = domains[:2]

        motif_centroids: Dict[str, np.ndarray] = {}
        for d in domains:
            for m in ws.motif_regs.get(d, MotifRegistry(self.data_dir, workspace_id, d)).motifs.values():
                motif_centroids[m.motif_id] = m.centroid_np()

        def explain_for_hit(hit: Dict[str, Any]) -> Dict[str, Any]:
            now_ts = _now_ts()
            sim = float(hit.get('score', 0.0))
            strength = float(hit.get('strength', 0.5))
            ts = int(hit.get('created_ts', now_ts) or now_ts)
            recency_days = max(0.0, (now_ts - ts) / 86400.0)
            motifs = hit.get('motifs') or []
            motif_alignment = 0.0
            for mid in motifs:
                c = motif_centroids.get(mid)
                if c is None or c.size == 0:
                    continue
                motif_alignment = max(motif_alignment, float(np.dot(qemb, c) / ((np.linalg.norm(qemb)+1e-12)*(np.linalg.norm(c)+1e-12))))
            contradiction_risk = float(hit.get('contradiction_risk', 0.0))
            mtype = str(hit.get("type") or "")
            type_bonus = 0.0

            # Character continuity: prefer the agent's own private thread.
            try:
                self_bonus = float(os.getenv("TORMENT_SELF_MEMORY_BONUS", "0.06"))
            except Exception:
                self_bonus = 0.06
            if str(hit.get("scope", "")) == "private" and str(hit.get("agent_id", "")) == str(agent_id):
                type_bonus += self_bonus

            if mtype == "identity_anchor":
                # Character continuity: identity anchors get a consistent lift.
                type_bonus += 0.12
                # Additional lift when the anchor belongs to the querying agent's private thread.
                if str(hit.get("scope", "")) == "private" and str(hit.get("agent_id", "")) == str(agent_id):
                    try:
                        type_bonus += float(os.getenv("TORMENT_SELF_ANCHOR_BONUS", "0.04"))
                    except Exception:
                        type_bonus += 0.04
            final = score_hit(sim=sim, strength=strength, recency_days=recency_days, motif_alignment=motif_alignment, contradiction_risk=contradiction_risk, type_bonus=type_bonus)
            return {
                "eid": int(hit.get('eid')),
                "scope": hit.get('scope'),
                "domain_id": hit.get('domain_id'),
                "final_score": final,
                "explain": {
                    "sim": sim,
                    "strength": strength,
                    "recency_days": recency_days,
                    "motif_alignment": motif_alignment,
                    "contradiction_risk": contradiction_risk,
                    "weights": {"alpha": 0.35, "beta": 0.10, "gamma": 0.20, "delta": 0.30},
                },
            }

        # gather hits by looking up in graphs
        out = []
        # private
        priv = self.private_graphs.get(ak)
        if priv:
            for eid in eids:
                ent = priv.entities.get(int(eid))
                if ent:
                    out.append(explain_for_hit({
                        "eid": int(eid),
                        "score": 0.0,
                        "strength": float(ent.payload.get('strength', 0.0)),
                        "created_ts": int(ent.payload.get('created_ts', 0) or 0),
                        "domain_id": ent.payload.get('domain_id'),
                        "scope": ent.payload.get('scope','private'),
                        "motifs": ent.payload.get('motifs', []),
                    }))
        # shared domain graphs
        for d in domains:
            sg = ws.shared_graphs.get(d)
            if not sg:
                continue
            for eid in eids:
                ent = sg.entities.get(int(eid))
                if not ent:
                    continue
                out.append(explain_for_hit({
                    "eid": int(eid),
                    "score": 0.0,
                    "strength": float(ent.payload.get('strength', 0.0)),
                    "created_ts": int(ent.payload.get('created_ts', 0) or 0),
                    "domain_id": ent.payload.get('domain_id'),
                    "scope": ent.payload.get('scope','shared'),
                    "motifs": ent.payload.get('motifs', []),
                }))

        return {"workspace_id": workspace_id, "agent_id": agent_id, "query": query_text, "domains": domains, "items": out, "embed_context": self._embed_context(ws)}


    def memory_chain(self, workspace_id: str, eid: int, scope: str = "shared", domain_id: Optional[str] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Return append-only event chain for a memory (from its graph event log)."""
        ws = self.get_workspace(workspace_id)
        events = []
        if scope == 'private':
            if not agent_id:
                raise ValueError('agent_id required for private scope')
            ak = self._agent_key(workspace_id, agent_id)
            g = self.private_graphs.get(ak)
            if g is None:
                return {"workspace_id": workspace_id, "eid": int(eid), "events": []}
            path = g.events_path
        else:
            dom = domain_id or 'research'
            g = ws.shared_graphs.get(dom)
            if g is None:
                return {"workspace_id": workspace_id, "eid": int(eid), "events": []}
            path = g.events_path

        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    if int(obj.get('eid', -1)) == int(eid):
                        events.append(obj)
        return {"workspace_id": workspace_id, "eid": int(eid), "scope": scope, "domain_id": domain_id, "events": events}


    def trace_full_graph(self, workspace_id: str, eid: int, scope: str = "shared", domain_id: Optional[str] = None, agent_id: Optional[str] = None, depth: int = 2, explain: bool = False, export: str = "none") -> Dict[str, Any]:
        """Build a causal trace graph for a memory. Simplified but complete enough for tooling."""
        ws = self.get_workspace(workspace_id)
        # base node
        nodes = []
        edges = []
        # include domain + workspace
        dom = domain_id or 'research'

        nodes.append({"id": f"domain:{dom}", "type": "domain", "domain_id": dom})
        nodes.append({"id": f"workspace:{workspace_id}", "type": "workspace", "workspace_id": workspace_id})
        edges.append({"src": f"domain:{dom}", "tgt": f"workspace:{workspace_id}", "type": "in_workspace"})

        mem_id = f"memory:{eid}:{scope}:{dom}"
        nodes.append({"id": mem_id, "type": "memory", "eid": int(eid), "scope": scope, "domain_id": dom})
        edges.append({"src": mem_id, "tgt": f"domain:{dom}", "type": "in_domain"})

        # add memory events
        chain = self.memory_chain(workspace_id, eid=eid, scope=scope, domain_id=dom, agent_id=agent_id)
        for i,evt in enumerate(chain.get('events', [])):
            ev_id = f"event:{eid}:{i}"
            nodes.append({"id": ev_id, "type": "event", **evt})
            edges.append({"src": ev_id, "tgt": mem_id, "type": "affects"})
            if evt.get('agent_id'):
                a = evt['agent_id']
                aid = f"agent:{a}"
                if not any(n['id']==aid for n in nodes):
                    nodes.append({"id": aid, "type": "agent", "agent_id": a})
                edges.append({"src": aid, "tgt": ev_id, "type": "authored"})

        # motifs containing this eid (best-effort by scanning motif registries)
        for d, reg in ws.motif_regs.items():
            for m in reg.motifs.values():
                if int(eid) in set(getattr(m,'member_eids', []) or []):
                    mid = f"motif:{d}:{m.motif_id}"
                    nodes.append({"id": mid, "type": "motif", "motif_id": m.motif_id, "label": m.label, "domain_id": d, "strength": float(m.strength)})
                    edges.append({"src": mem_id, "tgt": mid, "type": "in_motif"})

        # bridges touching involved domains
        brs = ws.bridges.relevant_to_domains([dom], top_k=20)
        for b in brs:
            bid = f"bridge:{b.get('from_domain')}:{b.get('from_motif')}->{b.get('to_domain')}:{b.get('to_motif')}"
            nodes.append({"id": bid, "type": "bridge", **b})
            edges.append({"src": bid, "tgt": f"domain:{b.get('from_domain')}", "type": "touches"})
            edges.append({"src": bid, "tgt": f"domain:{b.get('to_domain')}", "type": "touches"})

        graph = {"nodes": nodes, "edges": edges, "meta": {"workspace_id": workspace_id, "eid": int(eid), "scope": scope, "domain_id": dom, "depth": int(depth)}}
        graph["embed_context"] = self._embed_context(ws)

        export_files = {}
        out_dir = os.path.normpath(os.path.join(self.data_dir, 'workspaces', workspace_id, 'exports'))
        os.makedirs(out_dir, exist_ok=True)
        if export in ('json','bundle'):
            jp = os.path.join(out_dir, f"trace_{eid}_{dom}.json")
            with open(jp,'w',encoding='utf-8') as f:
                json.dump(graph, f, indent=2, ensure_ascii=False)
            export_files['json'] = jp
        if export in ('dot','bundle'):
            dp = os.path.join(out_dir, f"trace_{eid}_{dom}.dot")
            with open(dp,'w',encoding='utf-8') as f:
                f.write('digraph G {\n')
                for n in nodes:
                    f.write(f"  \"{n['id']}\" [label=\"{n.get('type')}\"];\n")
                for e in edges:
                    f.write(f"  \"{e['src']}\" -> \"{e['tgt']}\" [label=\"{e['type']}\"];\n")
                f.write('}\n')
            export_files['dot'] = dp

        graph['export_files'] = export_files
        return graph


    def trace_bundle(self, workspace_id: str, eid: int, scope: str = "shared", domain_id: Optional[str] = None, agent_id: Optional[str] = None, depth: int = 2, explain: bool = False, export: str = "bundle") -> Dict[str, Any]:
        """Create a trace bundle folder: graph.json, graph.dot, narrative.md, manifest.json."""
        dom = domain_id or 'research'
        graph = self.trace_full_graph(workspace_id, eid, scope=scope, domain_id=dom, agent_id=agent_id, depth=depth, explain=explain, export='bundle')
        out_dir = os.path.normpath(os.path.join(self.data_dir, 'workspaces', workspace_id, 'exports', f"bundle_{eid}_{dom}"))
        os.makedirs(out_dir, exist_ok=True)
        # write graph.json/dot already created in exports; copy into bundle
        import shutil
        jp = graph.get('export_files', {}).get('json')
        dp = graph.get('export_files', {}).get('dot')
        bjp = os.path.join(out_dir, 'graph.json')
        bdp = os.path.join(out_dir, 'graph.dot')
        if jp and os.path.exists(jp):
            shutil.copy(jp, bjp)
        if dp and os.path.exists(dp):
            shutil.copy(dp, bdp)
        # narrative
        narrative = self._trace_narrative(workspace_id, eid=eid, scope=scope, domain_id=dom, agent_id=agent_id)
        npath = os.path.join(out_dir, 'narrative.md')
        with open(npath,'w',encoding='utf-8') as f:
            f.write(narrative)
        manifest = {
            'workspace_id': workspace_id,
            'eid': int(eid),
            'scope': scope,
            'domain_id': dom,
            'bundle_dir': out_dir,
            'embed_context': graph.get('embed_context', {}),
            'files': {
                'graph_json': bjp,
                'graph_dot': bdp,
                'narrative_md': npath,
            }
        }
        mpath = os.path.join(out_dir, 'manifest.json')
        with open(mpath,'w',encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        return {"bundle_dir": out_dir, "manifest": manifest}


    def trace_view(self, workspace_id: str, eid: int, scope: str = "shared", domain_id: Optional[str] = None, agent_id: Optional[str] = None, depth: int = 2, explain: bool = False) -> Dict[str, Any]:
        """Inline reader-mode trace: narrative + compact summaries."""
        dom = domain_id or 'research'
        graph = self.trace_full_graph(workspace_id, eid, scope=scope, domain_id=dom, agent_id=agent_id, depth=depth, explain=explain, export='none')
        narrative = self._trace_narrative(workspace_id, eid=eid, scope=scope, domain_id=dom, agent_id=agent_id)
        # summarize graph
        type_counts = {}
        for n in graph.get('nodes', []):
            t = n.get('type','unknown')
            type_counts[t] = type_counts.get(t,0)+1
        return {
            'workspace_id': workspace_id,
            'eid': int(eid),
            'scope': scope,
            'domain_id': dom,
            'narrative': narrative,
            'graph_summary': {
                'nodes': len(graph.get('nodes', [])),
                'edges': len(graph.get('edges', [])),
                'counts_by_type': type_counts,
                'depth': int(depth),
            },
        }


    def _trace_narrative(self, workspace_id: str, eid: int, scope: str, domain_id: str, agent_id: Optional[str] = None) -> str:
        chain = self.memory_chain(workspace_id, eid=eid, scope=scope, domain_id=domain_id, agent_id=agent_id)
        evs = chain.get('events', [])
        lines = []
        lines.append(f"# Trace Narrative\n\n")
        lines.append(f"- Workspace: **{workspace_id}**\n")
        lines.append(f"- Domain: **{domain_id}**\n")
        lines.append(f"- Scope: **{scope}**\n")
        lines.append(f"- EID: **{int(eid)}**\n\n")
        if not evs:
            lines.append("No events found for this memory.\n")
            return ''.join(lines)
        lines.append("## Event Timeline\n")
        for evt in evs[-25:]:
            ts = evt.get('ts')
            et = evt.get('type')
            aid = evt.get('agent_id')
            lines.append(f"- {ts}: `{et}`" + (f" (agent `{aid}`)" if aid else "") + "\n")
        return ''.join(lines)



def dominant_thread(active: Dict[str, List[Dict[str, Any]]]) -> str:
    labels = []
    for dom, ms in active.items():
        for m in ms[:2]:
            labels.append(m.get("label", ""))
    labels = [l for l in labels if l]
    if not labels:
        return ""
    return " | ".join(labels[:4])


def random_chance(p: float) -> bool:
    import random
    return random.random() < float(p)

def _affect_state_path(data_dir: str, workspace_id: str, agent_id: str) -> str:
    _validate_path_component(workspace_id, "workspace_id")
    _validate_path_component(agent_id, "agent_id")
    base = os.path.normpath(os.path.join(data_dir, "workspaces", workspace_id, "agents", agent_id))
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "affect_state.json")

def _load_affect_state(data_dir: str, workspace_id: str, agent_id: str) -> Dict[str, Any]:
    p = _affect_state_path(data_dir, workspace_id, agent_id)
    base = {"last_tag": None, "last_conf": 0.0, "last_step": -10**9, "drift_hist": []}
    if not os.path.exists(p):
        return dict(base)
    try:
        with open(p, "r", encoding="utf-8") as f:
            st = json.load(f) or {}
    except Exception:
        st = {}
    # Backward-compatible fill
    if not isinstance(st, dict):
        st = {}
    for k, v in base.items():
        if k not in st:
            st[k] = v
    if not isinstance(st.get("drift_hist"), list):
        st["drift_hist"] = []
    # Trim history defensively
    try:
        st["drift_hist"] = list(st["drift_hist"])[-20:]
    except Exception:
        st["drift_hist"] = []
    return st

def _save_affect_state(data_dir: str, workspace_id: str, agent_id: str, state: Dict[str, Any]) -> None:
    p = _affect_state_path(data_dir, workspace_id, agent_id)
    try:
        # Keep payload small
        if isinstance(state, dict) and isinstance(state.get("drift_hist"), list):
            state["drift_hist"] = list(state["drift_hist"])[-50:]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(state or {}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.debug("failed to save affect state for agent=%s: %s", agent_id, e)
