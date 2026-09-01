# fabric.py
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple
import os, time, json, re, atexit, tempfile, threading, uuid, logging, math
from pathlib import Path
import numpy as np

from fastapi import HTTPException

from .memory_kernel import KernelRuntimeContext, TriOctaMemoryKernel
from .memory_graph import MemoryGraph
from .identity import (
    IdentityStore,
    AgentIdentity,
    PersistentIdentityCollisionError,
    PersistentIdentityMissingError,
    DEFAULT_AGENT_SEED,
    DEFAULT_AGENT_OVERLAY,
)
from .motifs import MotifRegistry, cosine as cos_sim
from .motif_geometry_port import LegacyMotifGeometryAdapter, MotifGeometryPort
from .query_read_model import (
    LegacyQualifiedQueryReadModel,
    NativeQualifiedQueryReadModel,
    QualifiedQueryHit,
    QualifiedQueryReadModel,
)
from .motif_runtime import LegacyMotifRuntimeAdapter
from .router import DomainRouter, DomainScore, SINGLE_AGENT_DOMAIN
from .domain_policies import DEFAULT_DOMAIN_POLICIES
from .bridges import BridgeRegistry
from .proposals import ProposalRegistry, ShareProposal
from .conflicts import ConflictRegistry
from .proposal_shared_storage import (
    AuthorizedSharedProposalStorage,
    LegacyAuthorizedSharedProposalStorage,
    NativeAuthorizedSharedProposalStorage,
    native_operator_operation_key,
    native_quorum_operation_key,
)
from .substrate.authorized_proposal_receipts import (
    AuthorizedProposalReceipt,
    AuthorizedProposalReceiptError,
    verify_receipt_sources,
)
from .substrate.shared_proposal_materialization import (
    AuthorizedSharedProposalOperator,
    AuthorizedSharedProposalQuorum,
)
from .scoring import (
    score_hit,
    ContinuityContext,
    QueryMemoryIdentity,
    compute_continuity_bonuses,
    qualified_query_memory_identity,
)
from .embeddings import build_embedder_from_env, Embedder, embedding_checksum
from .resonance import append_symbol, summarize_resonance
from .coherence_field import compute_coherence_field
from .symbols import assign_symbol_state
from .affect import classify_affect, looks_personal
from .affect_attribution import (
    build_ingest_classifier_attribution,
    build_mood_drift_attribution,
)
from .roles import RoleStore, dominant_role, role_multipliers
from .character import (
    CharacterSeed, CharacterState, CharacterStore,
    plant_seed, measure_drift, gravity_correction,
    assemble_character_context, derive_kernel_modulation,
)
from .agent_locks import AgentLockManager
from brainvision.lifecycle import BrainvisionLifecycleManager
from .checkpoint import (
    save_checkpoint,
    build_motif_summary, build_shard_snapshot,
)
from .governance import filter_llm_facing, SURFACE_LLM_CONTEXT
from .memory_runtime_access import LegacyPostWriteMemoryAccess
from .srg_runtime_state import LegacySRGTransientRuntime
from .candidate_types import CandidateShapedValue
from .derived_memory_runtime import LegacyDerivedMemoryRuntime
from .pathing import validate_portable_new_identifier, validate_structural_path_component
from .post_write_runtime import (
    FabricPostWriteContext,
    LegacyFabricPostWriteAdapter,
    LegacyFabricPostWriteDependencies,
    PostWriteStorageOutcome,
)
from .world_runtime import LegacyWorldRuntime

if TYPE_CHECKING:
    from .substrate.runtime_binding import (
        NativeMemoryBindingReadiness,
        NativeMemoryRuntimeBinding,
    )

log = logging.getLogger("torment.fabric")
hivemind_log = logging.getLogger("torment.hivemind")

_FILESYSTEM_CONTAINMENT_EVENT = "filesystem_containment_substitution"


class PersistedJobContainmentError(RuntimeError):
    """Bounded persisted-job root continuity detection failed."""


@dataclass(frozen=True)
class _FilesystemDirectoryIdentity:
    """Canonical directory identity used for bounded continuity detection."""

    canonical_path: str
    st_dev: int
    st_ino: int


@dataclass(frozen=True)
class _PersistedJobRootIdentity:
    """Captured root and parent identities for persisted-job deletion.

    A matching value is evidence of continuity, not proof that a later remove
    operation is race-free.
    """

    data_root: _FilesystemDirectoryIdentity
    jobs_root: _FilesystemDirectoryIdentity
    clone_root: _FilesystemDirectoryIdentity
    repair_root: _FilesystemDirectoryIdentity


@dataclass(frozen=True)
class _QueryMotifIdentity:
    """Internal domain-qualified identity for legacy motif geometry lookup."""

    workspace_id: str
    domain_id: str
    motif_id: str


def _qualified_query_motif_identity(
    hit: Dict[str, Any],
    *,
    workspace_id: str,
    motif_id: Any,
) -> Optional[_QueryMotifIdentity]:
    """Resolve a stored hit motif only in its authoritative source domain.

    ``bridge_domain`` is routing metadata, not the memory's namespace.  A hit
    without a validated private/shared origin is intentionally unresolved.
    """
    if not isinstance(motif_id, str) or not motif_id:
        return None
    if str(hit.get("workspace_id") or "") != str(workspace_id):
        return None
    if str(hit.get("scope") or "") not in {"private", "shared"}:
        return None
    domain_id = str(hit.get("domain_id") or "")
    if not domain_id:
        return None
    return _QueryMotifIdentity(
        workspace_id=str(workspace_id),
        domain_id=domain_id,
        motif_id=motif_id,
    )

class _JobCancelled(Exception):
    pass


def _safe_log_value(value: Any) -> str:
    """Return a single-line representation for user-derived log fields."""
    return str(value).replace("\r", "\\r").replace("\n", "\\n")


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


def _conflict_record_keys(conflict: Any, workspace_id: str) -> List[Tuple[str, str, int]]:
    """Return qualified lookup keys for a current-origin conflict row."""
    if str(getattr(conflict, "workspace_id", "")) != str(workspace_id):
        return []
    origin_scope = getattr(conflict, "origin_scope", None)
    if origin_scope == "private":
        qualifier = str(getattr(conflict, "origin_agent_id", "") or "").strip()
    elif origin_scope == "shared":
        qualifier = str(getattr(conflict, "origin_domain_id", "") or "").strip()
    else:
        return []
    if not qualifier:
        return []
    return [
        (str(origin_scope), qualifier, int(conflict.eid_a)),
        (str(origin_scope), qualifier, int(conflict.eid_b)),
    ]


def _conflict_hit_key(hit: Dict[str, Any]) -> Optional[Tuple[str, str, int]]:
    """Return a qualified conflict key from existing flattened hit origin."""
    origin_scope = str(hit.get("scope", "") or "")
    if origin_scope == "private":
        qualifier = str(hit.get("agent_id", "") or "").strip()
    elif origin_scope == "shared":
        qualifier = str(hit.get("domain_id", "") or "").strip()
    else:
        return None
    if not qualifier:
        return None
    try:
        return (origin_scope, qualifier, int(hit.get("eid")))
    except (TypeError, ValueError):
        return None


def _build_conflict_map(ws: Any, workspace_id: str, domains: List[str]) -> Dict[Tuple[str, str, int], Dict[str, Any]]:
    """Build a qualified open-conflict map for query and trace scoring."""
    conflict_map: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
    for domain_id in domains:
        try:
            conflicts = ws.conflicts[domain_id].list(status="open", limit=500)
        except Exception as exc:
            log.warning(
                "Conflict registry unreadable for query/trace workspace=%s domain=%s: %s",
                _safe_log_value(workspace_id),
                _safe_log_value(domain_id),
                _safe_log_value(exc),
            )
            continue
        for conflict in conflicts:
            for key in _conflict_record_keys(conflict, workspace_id):
                entry = conflict_map.get(key)
                if entry is None:
                    conflict_map[key] = {
                        "max_score": float(conflict.conflict_score),
                        "conflict_ids": [conflict.conflict_id],
                    }
                else:
                    entry["max_score"] = max(
                        float(entry.get("max_score", 0.0)),
                        float(conflict.conflict_score),
                    )
                    conflict_ids = entry.get("conflict_ids") or []
                    if conflict.conflict_id not in conflict_ids:
                        conflict_ids.append(conflict.conflict_id)
                    entry["conflict_ids"] = conflict_ids
    return conflict_map


def _now_ts() -> int:
    return int(time.time())


def _effective_srg_source(hit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the per-hit SRG state used for SCORING / explain decomposition.

    ``MemoryGraph.search()`` flattens an entity's stored ``payload`` into the
    top-level hit fields, so a stored ``payload["srg"]`` surfaces as
    ``hit["srg"]``. Prefer that flattened top-level value; fall back defensively
    to a nested ``hit["payload"]["srg"]`` for legacy / manual-shaped hits. Returns
    ``None`` when neither is present or the value is not a dict.

    READ-ONLY source selector for scoring/explain ONLY. It is NOT a gate for SRG
    breathing/writeback — that path stays bound to its original nested source so
    this normalization does not newly activate any write.
    """
    src = hit.get("srg")
    if not isinstance(src, dict):
        src = (hit.get("payload") or {}).get("srg")
    return src if isinstance(src, dict) else None


def random_chance(p: float) -> bool:
    """Return True with probability *p*, clamped to [0, 1]."""
    import random as _rng
    return _rng.random() < max(0.0, min(1.0, float(p)))


def dominant_thread(active_motifs: Dict[str, list]) -> Optional[Dict[str, Any]]:
    """Return the single highest-scored active motif across all domains, or None."""
    best: Optional[Dict[str, Any]] = None
    best_score = -1.0
    for _domain, motifs in active_motifs.items():
        for m in motifs:
            s = float(m.get("score", m.get("strength", 0.0)) if isinstance(m, dict) else 0.0)
            if s > best_score:
                best_score = s
                best = m
    return best


def _embed_audit_path(data_dir: str, workspace_id: str) -> str:
    return _safe_child(_ws_root(data_dir, workspace_id), "embed_audit.json")


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
    # Sink-local guard for CodeQL: realpath + startswith at makedirs site.
    _dir = os.path.realpath(os.path.dirname(path))
    if not _dir.startswith(os.sep) and not os.path.isabs(_dir):
        raise ValueError(f"Audit dir not absolute: {_dir!r}")
    os.makedirs(_dir, exist_ok=True)
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


def _affect_state_path(data_dir: str, workspace_id: str, agent_id: str) -> str:
    _ag = _agent_dir(data_dir, workspace_id, agent_id)
    # Sink-local guard for CodeQL at makedirs site.
    _rp = os.path.realpath(_ag)
    if not _rp.startswith(os.sep) and not os.path.isabs(_rp):
        raise ValueError(f"Agent dir not absolute: {_rp!r}")
    os.makedirs(_rp, exist_ok=True)
    return _safe_child(_ag, "affect_state.json")


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


def _anchor_state_path(data_dir: str, workspace_id: str, agent_id: str) -> str:
    return _safe_child(_agent_dir(data_dir, workspace_id, agent_id), "anchors.json")


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
    _dir = os.path.realpath(os.path.dirname(p))
    if not _dir.startswith(os.sep) and not os.path.isabs(_dir):
        raise ValueError(f"Anchor dir not absolute: {_dir!r}")
    os.makedirs(_dir, exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, p)


def _symbol_state_path(data_dir: str, workspace_id: str, agent_id: str) -> str:
    return _safe_child(_agent_dir(data_dir, workspace_id, agent_id), "symbol_state.json")


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
    _dir = os.path.realpath(os.path.dirname(p))
    if not _dir.startswith(os.sep) and not os.path.isabs(_dir):
        raise ValueError(f"Symbol dir not absolute: {_dir!r}")
    os.makedirs(_dir, exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, p)

class Workspace:
    def __init__(self, data_dir: str, workspace_id: str, kernel: TriOctaMemoryKernel,
                 requested_domains: Optional[List[str]] = None) -> None:
        self.data_dir = _canonical_data_root(data_dir)
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
            dom_dir = _domain_shared_dir(self.data_dir, workspace_id, d)
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
        _ws = _ws_root(self.data_dir, workspace_id)
        self.domain_suggestions_path = _safe_child(_ws, "domain_suggestions.json")
        # Sink-local guard for CodeQL
        _ws_dir = os.path.realpath(_ws)
        if not _ws_dir.startswith(os.sep) and not os.path.isabs(_ws_dir):
            raise ValueError(f"Workspace dir not absolute: {_ws_dir!r}")
        os.makedirs(_ws_dir, exist_ok=True)

        # per-domain policy knobs (throttles, governance, peeks)
        self.domain_policies_path = _safe_child(_ws, "domain_policies.json")
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
        return _safe_child(_ws_root(self.data_dir, self.workspace_id), "workspace_meta.json")

    def _load_or_init_meta(self) -> Dict[str, Any]:
        p = self._meta_path()
        _dir = os.path.realpath(os.path.dirname(p))
        if not _dir.startswith(os.sep) and not os.path.isabs(_dir):
            raise ValueError(f"Meta dir not absolute: {_dir!r}")
        os.makedirs(_dir, exist_ok=True)
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
        return _safe_child(_ws_root(self.data_dir, self.workspace_id), "domains.json")

    def _load_or_init_domains(self, requested_domains: Optional[List[str]] = None) -> List[str]:
        p = self._domains_path()
        _dir = os.path.realpath(os.path.dirname(p))
        if not _dir.startswith(os.sep) and not os.path.isabs(_dir):
            raise ValueError(f"Domains dir not absolute: {_dir!r}")
        os.makedirs(_dir, exist_ok=True)
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
                        _validate_new_path_component(d, "domain_id")
                        existing.append(d)
                        added = True
                if added:
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump({"domains": existing}, f, indent=2)
            return existing
        # New workspace — use requested domains or single-agent default.
        # For multi-agent hive-mind, pass domains explicitly (e.g. DEFAULT_DOMAINS).
        domains = list(requested_domains) if requested_domains else [SINGLE_AGENT_DOMAIN]
        for d in domains:
            _validate_new_path_component(d, "domain_id")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"domains": domains}, f, indent=2)
        return domains

    def _load_or_init_domain_policies(self) -> Dict[str, Any]:
        p = self.domain_policies_path
        _dir = os.path.realpath(os.path.dirname(p))
        if not _dir.startswith(os.sep) and not os.path.isabs(_dir):
            raise ValueError(f"Policies dir not absolute: {_dir!r}")
        os.makedirs(_dir, exist_ok=True)
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
        if domain_id in self.domains:
            return
        _validate_new_path_component(domain_id, "domain_id")
        self.domains.append(domain_id)
        # persist domains
        with open(self._domains_path(), "w", encoding="utf-8") as f:
            json.dump({"domains": self.domains}, f, indent=2)
        # instantiate registries and stores (shared graph first so shard reader is available)
        dom_dir = _domain_shared_dir(self.data_dir, self.workspace_id, domain_id)
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
    """Reject empty values and path traversal characters in user-provided identifiers.

    Raises HTTPException(400) if the value is empty or contains '/', '\\', or '..'.
    Returns the value unchanged for valid inputs.
    """
    try:
        return validate_structural_path_component(value, label)
    except ValueError as exc:
        if value == ".":
            raise HTTPException(status_code=400, detail=f"Invalid {label}: must not be '.'") from exc
        raise HTTPException(status_code=400, detail=f"Invalid {label}: must not contain path separators or '..'")


def _validate_new_path_component(value: str, label: str = "identifier") -> str:
    """Apply portable admission rules at a new filesystem-identity seam."""
    try:
        return validate_portable_new_identifier(value, label)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Internal path helpers — canonicalization + containment guards.
#
# Every helper uses os.path.realpath() for symlink resolution, then a
# startswith() containment check.  Keep these simple so CodeQL can
# follow the taint through to sink sites.
# ---------------------------------------------------------------------------

def _canonical_data_root(data_dir: str) -> str:
    """Canonicalize *data_dir* to an absolute real path."""
    _r = os.path.realpath(data_dir)
    if not _r.startswith(os.sep) and not os.path.isabs(_r):
        raise ValueError(f"data_dir did not resolve to absolute path: {_r!r}")
    return _r


def _ws_root(data_dir: str, workspace_id: str) -> str:
    """Return canonical workspace root, guarded under *data_dir*."""
    _validate_path_component(workspace_id, "workspace_id")
    _base = os.path.realpath(data_dir)
    _r = os.path.realpath(os.path.join(_base, "workspaces", workspace_id))
    if not _r.startswith(_base + os.sep):
        raise ValueError(f"Workspace path escapes data root: {_r!r}")
    return _r


def _agent_dir(data_dir: str, workspace_id: str, agent_id: str) -> str:
    """Return canonical agent directory, guarded under workspace root."""
    _ws = _ws_root(data_dir, workspace_id)
    _validate_path_component(agent_id, "agent_id")
    _r = os.path.realpath(os.path.join(_ws, "agents", agent_id))
    if not _r.startswith(_ws + os.sep):
        raise ValueError(f"Agent path escapes workspace root: {_r!r}")
    return _r


def _domain_shared_dir(data_dir: str, workspace_id: str, domain_id: str) -> str:
    """Return canonical domain shared directory, guarded under workspace root."""
    _ws = _ws_root(data_dir, workspace_id)
    _validate_path_component(domain_id, "domain_id")
    _r = os.path.realpath(os.path.join(_ws, "domains", domain_id, "shared"))
    if not _r.startswith(_ws + os.sep):
        raise ValueError(f"Domain path escapes workspace root: {_r!r}")
    return _r


def _safe_child(base: str, *parts: str) -> str:
    """Join *parts* under *base* and verify the result stays contained."""
    _b = os.path.realpath(base)
    _r = os.path.realpath(os.path.join(_b, *parts))
    if _r != _b and not _r.startswith(_b + os.sep):
        raise ValueError(f"Path escapes base directory: {_r!r}")
    return _r


def _agent_canonical_ownership_evidence(
    data_dir: str,
    workspace_id: str,
    agent_id: str,
) -> Tuple[str, ...]:
    """Return non-empty agent-bound canonical files without creating paths.

    The identity file binds the private core graph and per-agent archive lane.
    Embeddings, SQLite indexes, checkpoints, and memory-event logs are
    derived or audit-only residue and therefore cannot by themselves block a
    genuinely new identity. Reference, environment, and closure stores are
    workspace-scoped rather than agent-bound, so they are outside this check.
    """
    agent_dir = _agent_dir(data_dir, workspace_id, agent_id)
    candidates = (
        ("private_nodes", ("private", "nodes.jsonl")),
        ("private_edges", ("private", "edges.jsonl")),
        ("archive_documents", ("memory_archive", "documents.jsonl")),
        ("archive_chunks", ("memory_archive", "chunks.jsonl")),
        ("archive_lifecycle", ("memory_archive", "events.jsonl")),
    )
    evidence: List[str] = []
    for label, parts in candidates:
        path = _safe_child(agent_dir, *parts)
        try:
            if os.path.getsize(path) > 0:
                evidence.append(label)
        except OSError:
            # An unreadable or substituted canonical filename is still
            # ownership evidence. Fail closed rather than create an identity
            # over state that cannot be classified safely.
            if os.path.lexists(path):
                evidence.append(label)
    return tuple(evidence)


def _raise_if_agent_identity_is_missing_over_canonical_memory(
    data_dir: str,
    workspace_id: str,
    agent_id: str,
) -> None:
    if _agent_canonical_ownership_evidence(data_dir, workspace_id, agent_id):
        raise PersistentIdentityMissingError(
            "Persistent identity is missing for existing canonical agent memory"
        )


_WORKSPACE_IDENTITY_NEW = "NEW"
_WORKSPACE_IDENTITY_VERIFIED_EXISTING = "VERIFIED_EXISTING"
_WORKSPACE_IDENTITY_LEGACY_UNVERIFIED = "LEGACY_UNVERIFIED"


def _verify_workspace_identity_before_initialization(data_dir: str, workspace_id: str) -> str:
    """Read-only Layer-C verification before Workspace can create metadata.

    Metadata-backed workspaces self-verify their persisted ID.  For legacy
    metadata-less roots, an exact immediate directory-entry spelling is only a
    collision-containment witness; it is not persistent identity evidence.
    """
    workspace_root = _ws_root(data_dir, workspace_id)
    if not os.path.exists(workspace_root):
        return _WORKSPACE_IDENTITY_NEW

    meta_path = _safe_child(workspace_root, "workspace_meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            persisted_workspace_id = meta.get("workspace_id") if isinstance(meta, dict) else None
        except (OSError, ValueError, TypeError) as exc:
            raise PersistentIdentityCollisionError(
                "Persistent workspace identity cannot be verified from metadata: "
                f"requested workspace_id={workspace_id!r}"
            ) from exc
        if not isinstance(persisted_workspace_id, str) or persisted_workspace_id != workspace_id:
            raise PersistentIdentityCollisionError(
                "Persistent workspace identity collision: requested "
                f"workspace_id={workspace_id!r}; stored declaration does not exactly match"
            )
        return _WORKSPACE_IDENTITY_VERIFIED_EXISTING

    workspaces_root = _safe_child(_canonical_data_root(data_dir), "workspaces")
    try:
        entries = tuple(os.scandir(workspaces_root))
    except OSError as exc:
        raise PersistentIdentityCollisionError(
            "Persistent legacy workspace identity cannot be verified: "
            f"requested workspace_id={workspace_id!r}"
        ) from exc

    has_exact_entry = False
    samefile_errors = []
    for entry in entries:
        try:
            if not entry.is_dir():
                continue
        except OSError:
            continue
        if entry.name == workspace_id:
            has_exact_entry = True
            continue
        try:
            if os.path.samefile(entry.path, workspace_root):
                raise PersistentIdentityCollisionError(
                    "Persistent legacy workspace identity collision: requested "
                    f"workspace_id={workspace_id!r}; existing directory entry "
                    f"{entry.name!r} resolves to the same object"
                )
        except PersistentIdentityCollisionError:
            raise
        except (AttributeError, NotImplementedError, OSError) as exc:
            samefile_errors.append(exc)

    if has_exact_entry:
        return _WORKSPACE_IDENTITY_LEGACY_UNVERIFIED
    if samefile_errors:
        raise PersistentIdentityCollisionError(
            "Persistent legacy workspace identity cannot be verified without "
            f"filesystem object equivalence: requested workspace_id={workspace_id!r}"
        ) from samefile_errors[0]
    raise PersistentIdentityCollisionError(
        "Persistent legacy workspace identity has no exact directory-entry witness: "
        f"requested workspace_id={workspace_id!r}"
    )


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

    def __init__(
        self,
        data_dir: str,
        *,
        native_memory_binding: Optional["NativeMemoryRuntimeBinding"] = None,
    ) -> None:
        # Block C1 (Windows): map data_dir=":memory:" to a real
        # TemporaryDirectory so every sub-store's os.makedirs call
        # works cross-platform. ':' is an illegal filename character
        # on Windows. The TemporaryDirectory is held on self for this
        # fabric's lifetime and released by close() / __exit__() / GC.
        self._memory_tmpdir = None
        if data_dir == ":memory:":
            self._memory_tmpdir = tempfile.TemporaryDirectory(
                prefix="torment_memory_"
            )
            self.data_dir = self._memory_tmpdir.name
            # Register cleanup at interpreter exit so SQLite + tmpdir
            # handles are released even when callers (e.g., module-global
            # test fabrics) never explicitly call close(). Only for
            # :memory: fabrics -- real-disk fabrics persist intentionally.
            atexit.register(self.close)
        else:
            _safe = _canonical_data_root(data_dir)
            # Sink-local guard for CodeQL at makedirs site.
            if not _safe.startswith(os.sep) and not os.path.isabs(_safe):
                raise ValueError(f"data_dir not absolute: {_safe!r}")
            os.makedirs(_safe, exist_ok=True)
            self.data_dir = _safe
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
        # Phase 7G4 retains a prevalidated native STAGING binding only as inert
        # configuration.  The conditional import keeps ordinary Fabric startup
        # free of any substrate runtime dependency.  No existing runtime path
        # reads from or writes to this value.
        self._native_memory_binding: Optional["NativeMemoryRuntimeBinding"] = None
        self._native_memory_binding_readiness: Optional["NativeMemoryBindingReadiness"] = None
        if native_memory_binding is not None:
            from .substrate.runtime_binding import validate_fabric_embedder

            self._native_memory_binding_readiness = validate_fabric_embedder(
                native_memory_binding, self.embedder,
            )
            self._native_memory_binding = native_memory_binding
        self.kernel = TriOctaMemoryKernel(embedder=self.embedder)  # base kernel template
        self.ident_store = IdentityStore(data_dir=self.data_dir)
        self.role_store = RoleStore(data_dir=self.data_dir)
        self.character_store = CharacterStore(data_dir=self.data_dir)
        self._character_enable = str(os.environ.get("TORMENT_CHARACTER_ENABLE", "1")).strip().lower() in ("1", "true", "yes", "on")
        self._character_drift_every = int(os.environ.get("TORMENT_CHARACTER_DRIFT_CHECK_EVERY", "25"))

        # v0.1.0a: optional callback for automatic reflex triggering on
        # drift transitioning from below-threshold to above-threshold.
        # External consumers (typically an AgentRunner owner) set this
        # attribute after construction. Signature:
        #   (workspace_id: str, agent_id: str, drift_info: Dict) -> None
        # The fabric fires the callback only on a below→above transition
        # (tracked per-agent in `_last_drift_was_high`) to prevent
        # recursive re-triggering when the reflex turn itself ingests
        # and re-runs the drift check. If None, no reflex dispatch.
        # See docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md v0.1.0a.
        self.drift_reflex_callback: Optional[Callable[[str, str, Dict[str, Any]], None]] = None
        self._last_drift_was_high: Dict[Tuple[str, str], bool] = {}

        self.workspaces: Dict[str, Workspace] = {}
        self.agent_states: Dict[str, Any] = {}  # _agent_key(ws, agent) -> TriOcta ModelState
        self._kernel_contexts: Dict[str, KernelRuntimeContext] = {}

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
        # SRG relational signal (Slice A, advisory, in-memory): per-agent EMA of
        # each ingested memory's L_amplitude. Populated only while SRG is
        # enabled; stays empty otherwise. Not persisted, not authoritative, not
        # exposed via API/debug. Consumed by nothing yet (primitive only).
        self._srg_relational_ema: Dict[Tuple[str, str], float] = {}
        # Per-agent last-ingested SRG R band, keyed by (workspace_id, agent_id)
        # — same key discipline as the relational EMA above. Replaces a former
        # fabric-wide scalar that let one agent's last-ingest band influence
        # another agent's same-band query/trace scoring inside a shared fabric
        # instance. In-memory only; not persisted, not authoritative, not exposed.
        self._srg_last_ingest_band_by_agent: Dict[Tuple[str, str], int] = {}

        # Hivemind collective resonance (opt-in) — disabled by default
        self._hivemind_enable = str(os.environ.get("TORMENT_HIVEMIND_ENABLE", "0")).strip().lower() in ("1", "true", "yes", "on")
        self._hivemind_telemetry_enable = str(os.environ.get("TORMENT_HIVEMIND_TELEMETRY", "0")).strip().lower() in ("1", "true", "yes", "on")
        self._hivemind_telemetry_sequence = 0
        self._collective_fields: Dict[str, Any] = {}  # workspace_id -> CollectiveField (lazy init)
        self._proposal_bridges: Dict[str, Any] = {}  # workspace_id -> CollectiveProposalBridge (lazy init)

        # private memory stores per agent
        self.private_graphs: Dict[str, MemoryGraph] = {}  # _agent_key(ws, agent) -> graph

        # Per-agent and per-workspace serialization (Phase 0 — MCP prep)
        self.locks = AgentLockManager()
        self.brainvision_lifecycle = BrainvisionLifecycleManager(
            data_dir=self.data_dir,
            identity_store=self.ident_store,
            lock_manager=self.locks,
        )

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
        self._jobs_root: str = _safe_child(self.data_dir, 'jobs')
        self._persisted_job_root_identity: Optional[_PersistedJobRootIdentity] = None
        self._last_persisted_job_security_incident: Optional[Dict[str, str]] = None
        if self._job_persist:
            _clone_dir = os.path.realpath(os.path.join(self._jobs_root, 'clone'))
            if not _clone_dir.startswith(os.sep) and not os.path.isabs(_clone_dir):
                raise ValueError(f"Clone job dir not absolute: {_clone_dir!r}")
            os.makedirs(_clone_dir, exist_ok=True)
            _repair_dir = os.path.realpath(os.path.join(self._jobs_root, 'repair'))
            if not _repair_dir.startswith(os.sep) and not os.path.isabs(_repair_dir):
                raise ValueError(f"Repair job dir not absolute: {_repair_dir!r}")
            os.makedirs(_repair_dir, exist_ok=True)
            self._persisted_job_root_identity = self._capture_persisted_job_root_identity()
            self._load_jobs('clone')
            self._load_jobs('repair')



    def get_kernel_runtime_context(
        self, workspace_id: str, agent_id: str,
    ) -> Optional[KernelRuntimeContext]:
        """Return an existing per-agent kernel context without creating it."""
        return self._kernel_contexts.get(self._agent_key(workspace_id, agent_id))

    def get_srg_relational_signal(
        self, workspace_id: str, agent_id: str,
    ) -> Optional[float]:
        """Return the per-agent SRG relational EMA, or ``None``.

        ``None`` means SRG is disabled or no memory has been ingested for this
        agent yet. Advisory, in-memory, non-authoritative; not persisted and
        not exposed through any API/debug/result surface. Slice A primitive —
        no consumer wired yet.
        """
        return self._srg_relational_ema.get((workspace_id, agent_id))

    def _create_kernel_state_and_context(
        self,
        ak: str,
        *,
        seed_text: str,
        character_modulation: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Create or retrieve structurally paired per-agent kernel state."""
        has_state = ak in self.agent_states
        has_context = ak in self._kernel_contexts
        if has_state != has_context:
            raise RuntimeError(
                f"Kernel state/context lifecycle invariant violated for {ak!r}"
            )
        if not has_state:
            state = self.kernel.init_state(
                seed_text=seed_text,
                character_modulation=character_modulation,
            )
            runtime_ctx = self.kernel.new_runtime_context()
            self.agent_states[ak] = state
            self._kernel_contexts[ak] = runtime_ctx
        return self.agent_states[ak]


    def _get_sqlite_index(self, workspace_id: str, agent_id: str):
        """Get or create a SQLite IndexManager for an agent (Phase 4).

        Returns None if SQLite indexing is disabled or init fails.
        Failure is always non-fatal.
        """
        if not self._sqlite_enable:
            return None
        key = self._agent_key(workspace_id, agent_id)
        if key not in self._sqlite_indexes:
            try:
                from .sqlite_index import IndexManager
                index_dir = _safe_child(
                    _agent_dir(self.data_dir, workspace_id, agent_id),
                    "index",
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
                identity_state = _verify_workspace_identity_before_initialization(
                    self.data_dir, workspace_id,
                )
            except PersistentIdentityCollisionError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            # A missing root is a first-creation seam and must be admitted
            # portably before Workspace can write workspace-level artefacts.
            if identity_state == _WORKSPACE_IDENTITY_NEW:
                _validate_new_path_component(workspace_id, "workspace_id")
            try:
                ws = Workspace(data_dir=self.data_dir, workspace_id=workspace_id,
                               kernel=self.kernel, requested_domains=domains)
            except ValueError as e:
                # Dim mismatch safety.
                raise HTTPException(status_code=409, detail=str(e))
            self.workspaces[workspace_id] = ws
        elif domains:
            # Workspace exists in memory — ensure requested domains are present
            for d in domains:
                ws.add_domain(d)
        return ws

    @property
    def native_memory_binding(self) -> Optional["NativeMemoryRuntimeBinding"]:
        """Return the inert 7G4 binding, if explicitly injected by a caller."""
        return self._native_memory_binding

    @property
    def native_memory_binding_readiness(self) -> Optional["NativeMemoryBindingReadiness"]:
        """Return operational binding readiness, never semantic authority."""
        return self._native_memory_binding_readiness

    def list_workspaces_meta(self) -> List[Dict[str, Any]]:
        """Return persisted workspace embedding locks and basic metadata.

        Reads from data/workspaces/<workspace_id>/workspace_meta.json.
        Safe for large numbers of workspaces; returns empty list if none exist.
        """
        ws_root = _safe_child(self.data_dir, "workspaces")
        if not os.path.exists(ws_root):
            return []
        out: List[Dict[str, Any]] = []
        for name in sorted(os.listdir(ws_root)):
            _validate_path_component(name, "workspace_id")
            p = _safe_child(ws_root, name, "workspace_meta.json")
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
    @staticmethod
    def _filesystem_directory_identity(path: str) -> _FilesystemDirectoryIdentity:
        """Capture a directory identity token without retaining a handle."""
        canonical_path = os.path.normcase(os.path.realpath(path))
        st = os.stat(canonical_path)
        if not os.path.isdir(canonical_path):
            raise OSError("expected persisted-job directory is not a directory")
        return _FilesystemDirectoryIdentity(
            canonical_path=canonical_path,
            st_dev=int(st.st_dev),
            st_ino=int(st.st_ino),
        )

    @staticmethod
    def _is_link_or_reparse(path: str) -> bool:
        """Return whether a deletion candidate is a link/reparse point."""
        if os.path.islink(path):
            return True
        isjunction = getattr(os.path, "isjunction", None)
        if callable(isjunction) and isjunction(path):
            return True
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
        return bool(attributes & 0x0400)  # FILE_ATTRIBUTE_REPARSE_POINT

    def _capture_persisted_job_root_identity(self) -> _PersistedJobRootIdentity:
        """Capture the trusted job-root identities after normal setup.

        These are Level-2 identity-continuity tokens.  They are deliberately
        not represented as pinned directory handles and do not close a later
        same-user TOCTOU window.
        """
        data_root = self._filesystem_directory_identity(self.data_dir)
        jobs_root = self._filesystem_directory_identity(
            _safe_child(data_root.canonical_path, 'jobs'),
        )
        clone_root = self._filesystem_directory_identity(
            _safe_child(jobs_root.canonical_path, 'clone'),
        )
        repair_root = self._filesystem_directory_identity(
            _safe_child(jobs_root.canonical_path, 'repair'),
        )
        return _PersistedJobRootIdentity(
            data_root=data_root,
            jobs_root=jobs_root,
            clone_root=clone_root,
            repair_root=repair_root,
        )

    def _record_persisted_job_containment_incident(self, operation: str) -> None:
        """Keep a stable, process-local security record without new I/O."""
        self._last_persisted_job_security_incident = {
            "event": _FILESYSTEM_CONTAINMENT_EVENT,
            "subsystem": "persisted_job",
            "operation": operation,
            "failure_class": "identity_continuity",
        }
        self._log.error(
            "security_incident=%s subsystem=persisted_job operation=%s "
            "failure_class=identity_continuity",
            _FILESYSTEM_CONTAINMENT_EVENT,
            operation,
        )

    def _persisted_job_containment_failure(
        self, operation: str,
    ) -> PersistedJobContainmentError:
        # A later ordinary operation may rederive a fresh identity after the
        # caller has restored/reopened the expected root; do not poison Fabric.
        self._persisted_job_root_identity = None
        self._record_persisted_job_containment_incident(operation)
        return PersistedJobContainmentError(
            "persisted-job filesystem containment or identity continuity validation failed"
        )

    def _revalidate_persisted_job_root(self, kind: str, operation: str) -> str:
        """Return a current job-kind root or fail closed on substitution.

        The revalidation is intentionally bounded detection.  It compares the
        original canonical root plus device/inode tokens before destructive
        work, but does not claim a handle-pinned, race-free deletion.
        """
        _validate_path_component(kind, "job_kind")
        try:
            identity = self._persisted_job_root_identity
            if identity is None:
                identity = self._capture_persisted_job_root_identity()
                self._persisted_job_root_identity = identity
                self._jobs_root = identity.jobs_root.canonical_path

            current_data = self._filesystem_directory_identity(self.data_dir)
            if current_data != identity.data_root:
                raise OSError("persisted-job data root identity changed")
            current_jobs = self._filesystem_directory_identity(
                _safe_child(current_data.canonical_path, 'jobs'),
            )
            if current_jobs != identity.jobs_root:
                raise OSError("persisted-job root identity changed")

            expected_kind_root = (
                identity.clone_root if kind == 'clone' else identity.repair_root
            )
            current_kind = self._filesystem_directory_identity(
                _safe_child(current_jobs.canonical_path, kind),
            )
            if current_kind != expected_kind_root:
                raise OSError("persisted-job parent identity changed")
            return current_kind.canonical_path
        except Exception as exc:
            if isinstance(exc, PersistedJobContainmentError):
                raise
            raise self._persisted_job_containment_failure(operation) from None

    def _validated_persisted_job_delete_path(self, kind: str, job_id: str) -> str:
        """Revalidate one destructive persisted-job deletion target."""
        _validate_path_component(job_id, "job_id")
        kind_root = self._revalidate_persisted_job_root(kind, "sweep")
        filename = f"{job_id}.json"
        raw_candidate = os.path.join(kind_root, filename)
        try:
            candidate = _safe_child(kind_root, filename)
            if self._is_link_or_reparse(raw_candidate):
                raise self._persisted_job_containment_failure("sweep")
            return candidate
        except FileNotFoundError:
            # Preserve ordinary cleanup semantics for a file already absent.
            return raw_candidate
        except PersistedJobContainmentError:
            raise
        except Exception:
            raise self._persisted_job_containment_failure("sweep") from None

    def _job_path(self, kind: str, job_id: str) -> str:
        _validate_path_component(kind, "job_kind")
        _validate_path_component(job_id, "job_id")
        return _safe_child(self._jobs_root, kind, f"{job_id}.json")

    def _load_jobs(self, kind: str) -> None:
        """Load persisted jobs from disk into in-memory stores.

        Any job that was 'running' at shutdown is marked 'abandoned'.
        """
        if not self._job_persist:
            return
        store = self._clone_jobs if kind == 'clone' else self._repair_jobs
        _validate_path_component(kind, "job_kind")
        root = _safe_child(self._jobs_root, kind)
        if not os.path.isdir(root):
            return
        for fn in sorted(os.listdir(root)):
            if not fn.endswith('.json'):
                continue
            p = _safe_child(root, fn)
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
            _dir = os.path.realpath(os.path.dirname(p))
            if not _dir.startswith(os.sep) and not os.path.isabs(_dir):
                raise ValueError(f"Job dir not absolute: {_dir!r}")
            os.makedirs(_dir, exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(st, f, indent=2, sort_keys=True)
        except Exception as e:
            self._log.debug("Job persist failed: %s", e)

    def _prune_jobs(self, kind: str) -> bool:
        """Keep only the most recent N jobs (by started_ts) in memory and on disk.

        A root-identity substitution aborts the sweep before the affected job
        is removed from memory or disk and returns ``False``.  Normal lifecycle
        behaviour remains best-effort and returns ``True``.
        """
        n = int(self._job_max or 0)
        if n <= 0:
            return True
        store = self._clone_jobs if kind == 'clone' else self._repair_jobs
        items = sorted(store.items(), key=lambda kv: float(kv[1].get('started_ts', 0) or 0), reverse=True)
        drop = [jid for jid,_ in items[n:]]

        if self._job_persist:
            try:
                self._revalidate_persisted_job_root(kind, "sweep")
            except PersistedJobContainmentError:
                return False

        for jid in drop:
            if self._job_persist:
                try:
                    os.remove(self._validated_persisted_job_delete_path(kind, jid))
                except PersistedJobContainmentError:
                    return False
                except Exception as e:
                    self._log.debug("Job file removal failed: %s", e)
            store.pop(jid, None)
        return True




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
            except Exception as e:
                self._log.debug("Mutex release failed: %s", e)

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

        ws_root = _ws_root(self.data_dir, workspace_id)
        if not os.path.isdir(ws_root):
            raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")

        def _iter_graph_dirs() -> List[str]:
            gdirs: List[str] = []
            agents_root = _safe_child(ws_root, "agents")
            if include_private and os.path.isdir(agents_root):
                for aid in sorted(os.listdir(agents_root)):
                    _validate_path_component(aid, "agent_id")
                    gdir = _safe_child(agents_root, aid, "private")
                    if os.path.isdir(gdir):
                        gdirs.append(gdir)
            domains_root = _safe_child(ws_root, "domains")
            if include_shared and os.path.isdir(domains_root):
                for dom in sorted(os.listdir(domains_root)):
                    _validate_path_component(dom, "domain_id")
                    gdir = _safe_child(domains_root, dom, "shared")
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

        self._repair_log.info(
            "repair_embeddings start workspace=%s mode=%s graphs=%d",
            _safe_log_value(workspace_id),
            _safe_log_value(mode),
            total_graphs,
        )
        _push_progress("", 0)

        for gi, gdir in enumerate(graph_dirs, start=1):
            nodes_path = _safe_child(gdir, "nodes.jsonl")
            if not os.path.exists(nodes_path):
                continue
            counts["graphs"] += 1
            gstat = {"graph": gdir, "nodes": 0, "stale": 0, "repaired": 0}
            objs: List[Dict[str, Any]] = []
            modified = False

            self._repair_log.info(
                "repair_embeddings graph %d/%d %s",
                gi,
                total_graphs,
                _safe_log_value(gdir),
            )
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
                    emb_path = _safe_child(gdir, f"emb_{eid}.npy")

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

        self._repair_log.info(
            "repair_embeddings done workspace=%s mode=%s processed=%d",
            _safe_log_value(workspace_id),
            _safe_log_value(mode),
            processed,
        )
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

            # §2A D2: compute seed overlap for provenance tagging.
            # Can be cached later if emission volume becomes measurable (P4).
            _seed_eids: set = set()
            try:
                _cstate = self.character_store.load_state(ws.workspace_id, agent_id)
                if _cstate and _cstate.seed_id:
                    _cseed = self.character_store.load_seed(ws.workspace_id, _cstate.seed_id)
                    if _cseed:
                        _seed_eids = set(int(e) for e in (_cseed.seed_eids or []))
            except Exception:
                # §2A D2: seed-overlap tag is best-effort provenance —
                # falls through with _seed_overlap=0 / seed_aligned=False.
                log.debug(
                    "seed-overlap lookup failed for agent %s; emitting with seed_aligned=False",
                    agent_id,
                    exc_info=True,
                )
            _seed_overlap = len(_seed_eids & set(int(e) for e in agent_member_eids))

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
                    # §2A D2: provenance metadata for derived identity anchors
                    "anchor_origin": "derived",
                    "anchor_source": "motif_cluster",
                    "seed_overlap_count": int(_seed_overlap),
                    "seed_aligned": bool(_seed_overlap > 0),
                    "source_member_eids": [int(e) for e in agent_member_eids],
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
                    # D1-S3: affect-VALUE lineage for the mood_drift row. A
                    # mood_drift row is an affect-bearing derived transition signal
                    # (prior tag + current classifier result + qualified transition),
                    # so its ratified posture is system/derived/unconfirmed/
                    # via=mood_drift_transition — distinct from the ordinary-ingest
                    # classifier producer. Internally constructed (no caller surface
                    # on this add_memory path), always value_state=set because this
                    # producer emits no row when affect is absent/neutral/below-conf/
                    # unchanged/in-gap. Row lineage stays in mtype/mood_from/mood_to.
                    "affect_attribution": build_mood_drift_attribution(
                        affect_tag=str(affect_tag),
                    ),
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
        _validate_new_path_component(target_workspace_id, "target_workspace_id")
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
    
        self._log.info(
            "clone start job_id=%s src=%s tgt=%s include_private=%s include_shared=%s reembed=%s reembed_mode=%s",
            _safe_log_value(job_id),
            _safe_log_value(source_workspace_id),
            _safe_log_value(target_workspace_id),
            _safe_log_value(include_private),
            _safe_log_value(include_shared),
            _safe_log_value(reembed),
            _safe_log_value(reembed_mode),
        )
    
        try:
            src_root = _ws_root(self.data_dir, source_workspace_id)
            if not os.path.isdir(src_root):
                raise HTTPException(status_code=404, detail=f"Source workspace '{source_workspace_id}' not found")
            tgt_root = _ws_root(self.data_dir, target_workspace_id)
            if os.path.exists(tgt_root):
                raise HTTPException(status_code=409, detail=f"Target workspace '{target_workspace_id}' already exists")
    
            import shutil
    
            _job_update(phase="copy")
            def _copytree_filtered(src: str, dst: str) -> None:
                # Guard the destination root before walking.
                _dst = os.path.realpath(dst)
                if not _dst.startswith(os.sep) and not os.path.isabs(_dst):
                    raise ValueError(f"Clone dst not absolute: {_dst!r}")
                os.makedirs(_dst, exist_ok=True)
                for root, dirs, files in os.walk(src):
                    rel = os.path.relpath(root, src)
                    out_root = _safe_child(_dst, rel) if rel != "." else _dst

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
                        srcp = _safe_child(root, fn)
                        dstp = _safe_child(out_root, fn)
                        os.makedirs(os.path.dirname(dstp), exist_ok=True)
                        shutil.copy2(srcp, dstp, follow_symlinks=False)
    
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
            mp = _safe_child(tgt_root, "workspace_meta.json")
            with open(mp, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
    
            regenerated = {"graphs": 0, "embeddings": 0}
            if reembed:
                _job_update(phase="reembed")
    
                def _iter_graph_dirs() -> List[str]:
                    gdirs: List[str] = []
                    agents_root = _safe_child(tgt_root, "agents")
                    if include_private and os.path.isdir(agents_root):
                        for aid in sorted(os.listdir(agents_root)):
                            _validate_path_component(aid, "agent_id")
                            gdir = _safe_child(agents_root, aid, "private")
                            if os.path.isdir(gdir):
                                gdirs.append(gdir)
                    domains_root = _safe_child(tgt_root, "domains")
                    if include_shared and os.path.isdir(domains_root):
                        for dom in sorted(os.listdir(domains_root)):
                            _validate_path_component(dom, "domain_id")
                            gdir = _safe_child(domains_root, dom, "shared")
                            if os.path.isdir(gdir):
                                gdirs.append(gdir)
                    return gdirs
    
                graph_dirs = _iter_graph_dirs()
                _prog(graphs_total=len(graph_dirs), graphs_done=0, embeddings_done=0, current_graph="")
    
                def _regen_graph(graph_dir: str) -> None:
                    nodes_path = _safe_child(graph_dir, "nodes.jsonl")
                    if not os.path.exists(nodes_path):
                        return
                    regenerated["graphs"] += 1
                    local_count = 0
                    self._log.info(
                        "clone job_id=%s reembed graph=%s",
                        _safe_log_value(job_id),
                        _safe_log_value(graph_dir),
                    )
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
                            emb_path = _safe_child(graph_dir, f"emb_{eid}.npy")
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
                                    self._log.info(
                                        "clone job_id=%s progress graph=%s embeddings=%d",
                                        _safe_log_value(job_id),
                                        _safe_log_value(graph_dir),
                                        regenerated["embeddings"],
                                    )
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
                self._log.debug(
                    "Failed to write embedding audit for workspace_id=%s: %s",
                    _safe_log_value(target_workspace_id),
                    _safe_log_value(e),
                )

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
            raise HTTPException(status_code=500, detail="Clone operation failed")
        finally:
            try:
                self._clone_mutex.release()
            except Exception as e:
                self._log.debug("Mutex release failed: %s", e)


    def create_agent(self, workspace_id: str, agent_id: str, seed: Optional[Dict[str, Any]] = None) -> AgentIdentity:
        _validate_path_component(agent_id, "agent_id")
        # IdentityStore.load derives a validated path with mkdir=False, so this
        # existence probe cannot create an agent directory.  Preserve access to
        # legacy identities through Layer A while applying Layer B before any
        # new identity can be written.
        try:
            existing_identity = self.ident_store.load(workspace_id, agent_id)
        except PersistentIdentityCollisionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if existing_identity is None:
            _validate_new_path_component(agent_id, "agent_id")
        ak = self._agent_key(workspace_id, agent_id)
        # Serialize creation by workspace before the per-agent initializer so a
        # CharacterSeed ownership check and first save are one atomic sequence.
        with self.locks.workspace_lock(workspace_id), self.locks.agent_lock(workspace_id, agent_id):
            try:
                ident = self.ident_store.load(workspace_id, agent_id)
            except PersistentIdentityCollisionError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            if ident is None:
                try:
                    _raise_if_agent_identity_is_missing_over_canonical_memory(
                        self.data_dir, workspace_id, agent_id,
                    )
                except PersistentIdentityMissingError as exc:
                    self._log.warning(
                        "persistent_identity_missing_over_canonical_memory "
                        "workspace_id=%s agent_id=%s",
                        _safe_log_value(workspace_id),
                        _safe_log_value(agent_id),
                    )
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Persistent identity is missing for existing canonical "
                            "agent memory; recovery is required"
                        ),
                    ) from exc

            # Do not initialize the workspace before the missing-identity
            # check above: an agent-bound canonical artifact must fail closed
            # without creating replacement state around it.
            ws = self.get_workspace(workspace_id)
            if ident is None:
                effective_seed = seed or DEFAULT_AGENT_SEED
                effective_seed_id = str(effective_seed.get("seed_id", "") or "")
                if self._character_enable and effective_seed_id:
                    existing_character_seed = self.character_store.load_seed(
                        workspace_id, effective_seed_id
                    )
                    if existing_character_seed is None:
                        _validate_new_path_component(effective_seed_id, "seed_id")
                    if existing_character_seed is not None:
                        owner_agent_id = str(existing_character_seed.owner_agent_id or "").strip()
                        if not owner_agent_id or owner_agent_id != agent_id:
                            detail = (
                                "Character seed ownership conflict: "
                                f"workspace_id={workspace_id!r}, "
                                f"seed_id={effective_seed_id!r}, "
                                f"requesting_agent_id={agent_id!r}"
                            )
                            if owner_agent_id:
                                detail += f", owner_agent_id={owner_agent_id!r}"
                            raise HTTPException(status_code=409, detail=detail)
                ident = self.ident_store.create(workspace_id, agent_id, seed=effective_seed)
            # init role profile (character continuity guidance)
            try:
                _ = self.role_store.load(workspace_id, agent_id)
            except Exception as e:
                self._log.debug(
                    "Failed to load role_store for workspace_id=%s agent_id=%s: %s",
                    _safe_log_value(workspace_id),
                    _safe_log_value(agent_id),
                    _safe_log_value(e),
                )
            # init kernel state if needed — route character seed through oscillator physics
            if ak not in self.agent_states:
                char_mod = None
                if self._character_enable:
                    seed_text_val = str(ident.seed.get("seed_text", "") or "").strip()
                    if seed_text_val:
                        try:
                            _raw_name = str(
                                ident.seed.get("character_name", "")
                                or ident.seed.get("seed_id", "")
                                or ""
                            )
                            _cseed = CharacterSeed(
                                seed_id=str(ident.seed.get("seed_id", "") or ""),
                                character_name=_raw_name,
                                seed_text=seed_text_val,
                            )
                            char_mod = derive_kernel_modulation(_cseed, self.kernel.embedder)
                        except Exception:
                            char_mod = None
                if char_mod:
                    self._create_kernel_state_and_context(
                        ak,
                        seed_text=seed_text_val,
                        character_modulation=char_mod,
                    )
                else:
                    self._create_kernel_state_and_context(
                        ak, seed_text=f"agent:{agent_id}",
                    )
            else:
                self._create_kernel_state_and_context(
                    ak, seed_text=f"agent:{agent_id}",
                )
            # init private store
            if ak not in self.private_graphs:
                pdir = _safe_child(_agent_dir(self.data_dir, workspace_id, agent_id), "private")
                sq_idx = self._get_sqlite_index(workspace_id, agent_id)
                self.private_graphs[ak] = MemoryGraph(
                    data_dir=pdir, embedder=self.kernel.embedder, sqlite_index=sq_idx,
                )

            # --- Character seed planting (optional, non-blocking) ---
            if self._character_enable:
                seed_text = str(ident.seed.get("seed_text", "") or "").strip()
                seed_id = str(ident.seed.get("seed_id", "") or "")
                if seed_text and seed_id:
                    try:
                        char_seed = self.character_store.load_seed(workspace_id, seed_id)
                        if char_seed is None:
                            _char_name = str(
                                ident.seed.get("character_name", "")
                                or seed_id
                            )
                            char_seed = CharacterSeed(
                                seed_id=seed_id,
                                character_name=_char_name,
                                seed_text=seed_text,
                                owner_agent_id=agent_id,
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
                                # Activation bridge: write a minimal
                                # CharacterState anchor so Path 3 character
                                # provenance badges fire from the first
                                # ingest, not only after the periodic drift
                                # cycle. This is not canon, not identity,
                                # and not drift measurement — only an
                                # active-state anchor. The drift block at
                                # fabric.py:3120+ remains the source of
                                # drift evolution and will load-and-merge
                                # over this anchor on its first tick.
                                self.character_store.save_state(
                                    workspace_id,
                                    CharacterState(
                                        workspace_id=workspace_id,
                                        agent_id=agent_id,
                                        seed_id=seed_id,
                                    ),
                                )
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

    def _emit_hivemind_packet_telemetry(
        self,
        *,
        workspace_id: str,
        agent_id: str,
        domain_id: Optional[str],
        source_eid: Optional[int],
        packet_emitted: bool,
        gate_outcome: str,
        skip_reason: Optional[str],
        coherence: Optional[float],
        provenance_class: Optional[str] = None,
        convergence_event: Optional[Any] = None,
    ) -> None:
        """Emit one optional structured packet-decision record for experiment capture."""
        if not self._hivemind_telemetry_enable:
            return

        self._hivemind_telemetry_sequence += 1
        partner_agent_id = None
        if convergence_event is not None:
            for participant in getattr(convergence_event, "participating_agents", []):
                if participant != agent_id:
                    partner_agent_id = participant
                    break
        record = {
            "event_kind": "hivemind_packet_decision",
            "timestamp": time.time(),
            "sequence": self._hivemind_telemetry_sequence,
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "domain_id": domain_id,
            "source_eid": source_eid,
            "packet_emitted": packet_emitted,
            "gate_outcome": gate_outcome,
            "skip_reason": skip_reason,
            "coherence": coherence,
            "provenance_class": provenance_class,
            "convergence_occurred": convergence_event is not None,
            "convergence_event_id": getattr(convergence_event, "event_id", None),
            "convergence_partner_agent_id": partner_agent_id,
            "semantic_similarity": getattr(convergence_event, "semantic_overlap", None),
        }
        hivemind_log.info(
            "HIVEMIND_PACKET_DECISION",
            extra={"hivemind_telemetry": record},
        )

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
            - Provenance-marked (ProvenanceV1 source_type='collective_echo', source_event_id, source_agents)
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

        # Pre-stamp collective provenance so the echo is born with correct
        # lineage. This is belt-and-suspenders — skip_packet_emission is the
        # primary guard, but pre-stamping ensures the stored payload is correct
        # from the moment of creation.
        from .provenance_v1 import ProvenanceV1
        _echo_prov = ProvenanceV1.for_collective_echo(
            notes=f"event_id={event_id}",
        ).to_dict()

        # Ingest the echo as a low-amplitude memory.
        # skip_packet_emission=True is the PRIMARY guard against the echo-
        # packet-leak invariant violation: echoes must never emit packets.
        ingest_result = self.ingest(
            workspace_id=workspace_id,
            agent_id=target_agent_id,
            text=echo_summary,
            step=0,  # echoes don't participate in step-counting
            domain_id=target_domain,
            supplied_summary=echo_summary,
            scope="private",
            provenance=_echo_prov,
            skip_packet_emission=True,
        )

        echo_eid = ingest_result.get("eid")

        if echo_eid is not None:
            # Patch the stored memory with remaining collective metadata +
            # terminal governance flags. Entity lookup failure here means
            # the echo exists but is ungoverned — treat as a hard failure.
            _patch_ok = False
            _patch_error = None
            try:
                graph = self.private_graphs.get(self._agent_key(workspace_id, target_agent_id))
                if graph:
                    ent = graph.entities.get(int(echo_eid))
                    if ent is not None:
                        # Collective metadata
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
                        graph.flush_node(int(echo_eid))
                        _patch_ok = True
                    else:
                        _patch_error = f"Entity eid={echo_eid} not found after ingest"
                else:
                    _patch_error = f"Graph not found for agent {target_agent_id}"
            except Exception as e:
                _patch_error = f"Exception during echo governance patch: {e}"

            if not _patch_ok:
                self._log.warning(
                    "reingest_convergence: echo eid=%s created but governance patch FAILED: %s. "
                    "Echo may exist without terminal governance flags.",
                    echo_eid, _patch_error,
                )
                return {
                    "eligible": False,
                    "reason": f"Echo created (eid={echo_eid}) but governance patch failed: {_patch_error}",
                    "echo_eid": echo_eid,
                    "partial_failure": True,
                }

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
        provenance: Optional[Dict[str, Any]] = None,
        memory_class: str = "core",
        extra_payload: Optional[Dict[str, Any]] = None,
        *,
        skip_packet_emission: bool = False,
        suppress_canon: bool = False,
    ) -> Dict[str, Any]:
        # === GATE A LAYER 4 — ordinary-ingest candidate refusal (first brick) ===
        # FIRST executable statement. Structural, content-blind type refusal:
        # ordinary ingest must not accept a candidate-shaped value as ordinary
        # memory input. This precedes _agent_key, create_agent, provenance, kernel
        # processing, and ALL fan-out / mutation, so a refused call has zero side
        # effects. It inspects ONLY the type of `text` — never its contents,
        # metadata, tags, payload keys, provenance, marker fields, or container
        # structure; the error message never interpolates the value or its repr.
        #
        # SCOPE (smallest brick): `text` parameter ONLY. The non-text parameters
        # (supplied_summary, extra_payload, supplied_embedding, provenance, ...)
        # and the known direct-writer bypasses remain UNRESOLVED and out of scope.
        # This is NOT wall completion.
        if isinstance(text, CandidateShapedValue):
            raise TypeError(
                "TormentFabric.ingest does not accept candidate-shaped values as "
                "ordinary memory input (Gate A Layer 4 text-boundary refusal)."
            )
        # === BOUNDARY GUARD ===
        # Core ingest ALWAYS creates "core" memory. Archive documents use
        # ArchiveStore.ingest_document() via /archive/ingest_document endpoint.
        # This prevents archive content from entering the identity pipeline.
        # =====================
        ak = self._agent_key(workspace_id, agent_id)
        ident = self.create_agent(workspace_id, agent_id)
        ws = self.get_workspace(workspace_id)

        # --- Provenance (v2.4.x first-pass) ---
        # Rule 1: every ingested memory must have provenance.
        # Rule 2: default for plain user ingest if caller did not supply one.
        # Rule 4: non-direct writes must supply explicit provenance.
        from .provenance_v1 import ProvenanceV1, CHARACTER_SCOPE_ACTIVE
        if provenance is not None:
            # Validate by round-tripping through the dataclass
            _prov = ProvenanceV1.from_dict(provenance)
            _prov_dict = _prov.to_dict()
        else:
            _prov = ProvenanceV1.for_user_ingest(step=step)
            _prov_dict = _prov.to_dict()

        # --- Path 3 (§10.5) character context badge ---
        # If the agent has an active CharacterState pointing at a known
        # CharacterSeed, stamp the resulting memory with descriptive
        # character metadata. This is provenance, not canon: it records
        # the context the memory was formed in without altering retrieval,
        # governance, or collective emission. Caller-supplied character_id
        # is honored — only stamps when the field is empty. Fail-closed:
        # any error skips the badge and ingest continues normally.
        if not _prov.character_id:
            try:
                _cstate = self.character_store.load_state(workspace_id, agent_id)
                if _cstate and _cstate.seed_id:
                    _cseed = self.character_store.load_seed(workspace_id, _cstate.seed_id)
                    if _cseed and _cseed.seed_id:
                        _prov.character_id = _cseed.seed_id
                        _prov.character_name = _cseed.character_name
                        _prov.character_scope = CHARACTER_SCOPE_ACTIVE
                        _prov_dict = _prov.to_dict()
            except Exception as _e:
                log.debug("Path 3 character badge skipped: %s", _e)

        # --- Baton lifecycle validation (Block A, docs/BLOCK_A_DESIGN.md §6.1) ---
        # When memory_class == "baton", the caller-supplied extra_payload
        # MUST carry a baton_lifecycle dict with owner, expires_when, and
        # resolution_condition. Missing any required field → reject with a
        # specific error, no state mutation, no node written.
        # Baton lifecycle fields live on extra_payload (mutable state over
        # the baton's life), not on ProvenanceV1 (origin/lineage only).
        if memory_class == "baton":
            if scope != "private":
                raise ValueError(
                    "memory_class='baton' requires scope='private'"
                )
            _bl = (extra_payload or {}).get("baton_lifecycle")
            if not isinstance(_bl, dict):
                raise ValueError(
                    "memory_class='baton' requires extra_payload['baton_lifecycle'] dict "
                    "with owner, expires_when, and resolution_condition"
                )
            for _req in ("owner", "expires_when", "resolution_condition"):
                if not _bl.get(_req):
                    raise ValueError(
                        f"baton_lifecycle missing required field '{_req}'"
                    )
            _valid_owners = {"user", "next_ai", "system"}
            if _bl.get("owner") not in _valid_owners:
                raise ValueError(
                    f"baton_lifecycle.owner must be one of "
                    f"{sorted(_valid_owners)}, got {_bl.get('owner')!r}"
                )
            _bl.setdefault("status", "active")

        state = self.agent_states[ak]
        runtime_ctx = self._kernel_contexts.get(ak)
        if runtime_ctx is None:
            raise RuntimeError(
                f"KernelRuntimeContext missing for active agent {ak!r}"
            )
        # process kernel (text only used for gating signals)
        state, signals, debug = self.kernel.process(state, text, runtime_ctx)
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
            from .srg_engine import build_memory_srg, detect_character_mode, relational_amplitude
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
            # Track last-ingested band PER AGENT for same-band scoring in the
            # query/trace path, keyed by (workspace_id, agent_id) so one agent's
            # ingest cannot influence another agent's same-band scoring.
            self._srg_last_ingest_band_by_agent[(workspace_id, agent_id)] = _srg_state.R_band

            # SRG relational signal (Slice A, advisory): update the per-agent EMA
            # of this memory's L_amplitude. First ingest seeds it; later ingests
            # blend with alpha=0.2. In-memory only; no persistence, no authority.
            _srg_rel_amp = relational_amplitude(_srg_state)
            _srg_rel_key = (workspace_id, agent_id)
            _srg_rel_prev = self._srg_relational_ema.get(_srg_rel_key)
            if _srg_rel_prev is None:
                self._srg_relational_ema[_srg_rel_key] = _srg_rel_amp
            else:
                self._srg_relational_ema[_srg_rel_key] = (
                    0.8 * _srg_rel_prev + 0.2 * _srg_rel_amp
                )

        # Character continuity (v1.11): soft role inference (guidance signal).
        # Updates slowly and is used only to tune memory behavior (anchors/recency), never persona writing.
        try:
            _rp = self.role_store.load(workspace_id, agent_id)
            _rp = self.role_store.update_from_text(_rp, summary)
            self.role_store.save(_rp)
        except Exception as _role_exc:
            log.debug("Role inference update failed: %s", _role_exc)

        # Character continuity (v1.11): lightweight affect tagging.
        # This is a guidance signal only; it must not dominate or rewrite persona.
        affect_tag = None
        affect_conf = None
        # D1-S2: the ingest affect-attribution stamp is emitted iff classification
        # COMPLETED SUCCESSFULLY. "enabled" != "ran": classify_affect is fail-soft,
        # so a raise must NOT be recorded as an evaluated `unset`. This boolean is
        # set True only after the classifier returns without raising; it stays
        # False when affect is disabled or when classification raises.
        # unset != not evaluated.
        affect_classification_completed = False
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
                affect_classification_completed = True
            except Exception:
                affect_tag, affect_conf = None, None
                # classification did not complete -> not evaluated -> no stamp
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

        # Preflight: domain must exist in the workspace's motif registries
        # before any state mutation. Failing here is cheap and clean;
        # failing later at ws.motif_regs[chosen_domain] leaves orphan
        # state — a MEMORY_CREATE event in memory_events.jsonl and an
        # embedding shard row — without a matching nodes.jsonl row,
        # because flush_node() is downstream of the motif lookup and is
        # never reached. Ingest semantics are all-or-nothing.
        if chosen_domain not in ws.motif_regs:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown domain_id={chosen_domain!r} for "
                    f"workspace={workspace_id!r}. Valid domains: "
                    f"{sorted(ws.motif_regs.keys())}"
                ),
            )

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
        legacy_registry: Optional[MotifRegistry] = None
        motif_runtime: Optional[LegacyMotifRuntimeAdapter] = None
        state_symbol: Optional[str] = None

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

            # Tool-result lifecycle: cap half-life for informational memories.
            # Tool outputs are observations, not experiences — their value decays
            # faster than experiential or identity memory.
            if (isinstance(_prov_dict, dict)
                    and _prov_dict.get("source_type") == "tool_result"):
                try:
                    _tool_hl_cap = float(os.getenv(
                        "TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS", "7"))
                except Exception:
                    _tool_hl_cap = 7.0
                half_life_days = min(half_life_days, _tool_hl_cap)

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
                                # Block A cross-class guard (docs/BLOCK_A_DESIGN.md §6.1):
                                # reinforce-in-place applies only when incoming and existing
                                # memory_class match. A baton must not reinforce a core entry
                                # and vice versa — they have different lifecycle semantics.
                                _existing_class = str(
                                    (_existing_ent.payload or {}).get("memory_class", "core")
                                )
                                if _existing_class != memory_class:
                                    continue
                                # Block A contradiction guard (docs/BLOCK_A_DESIGN.md §8):
                                # if incoming content is similar-AND-contradictory to this
                                # existing entry, do NOT reinforce. Fall through to the spawn
                                # path so the contradiction is recorded in ConflictRegistry.
                                # Applies to core writes only; baton is lifecycle, not claim.
                                if memory_class == "core":
                                    _old_sum_guard = str(
                                        (_existing_ent.payload or {}).get("summary", "")
                                    )
                                    _sim_guard = float(
                                        _rh.get("raw_score", _rh.get("score", 0))
                                    )
                                    _is_c, _cs, _r = _detect_canon_conflict(
                                        summary, _old_sum_guard, _sim_guard
                                    )
                                    if _is_c:
                                        continue
                                _old_str = float((_existing_ent.payload or {}).get("strength", 0.5))
                                # Check if the EXISTING entity is a tool-result memory.
                                # Tool-result reinforcement: do NOT boost strength.
                                # Repeated tool output is a staleness signal, not importance.
                                _existing_prov_for_guard = (_existing_ent.payload or {}).get("provenance")
                                _existing_is_tool_result = (
                                    isinstance(_existing_prov_for_guard, dict)
                                    and _existing_prov_for_guard.get("source_type") == "tool_result"
                                )
                                if _existing_is_tool_result:
                                    _new_str = _old_str  # no strength boost
                                else:
                                    # Asymptotic reinforcement: diminishing returns, cap at 0.98
                                    _new_str = min(0.98, _old_str + (1.0 - _old_str) * 0.3)
                                # On reinforcement:
                                # - NEVER overwrite existing provenance (Rule F: no laundering)
                                # - Only backfill if missing AND the new provenance is
                                #   user-origin (direct_ingest). Do not stamp archivist/
                                #   derived provenance onto old user memories.
                                _reinforce_updates: Dict[str, Any] = {
                                    "strength": round(_new_str, 4),
                                    "last_reinforced": int(step),
                                    "last_reinforced_ts": _now_ts(),
                                    "reinforcement_count": int((_existing_ent.payload or {}).get("reinforcement_count", 0)) + 1,
                                }
                                if _existing_is_tool_result:
                                    _reinforce_updates["last_tool_refresh_ts"] = _now_ts()
                                _existing_prov = (_existing_ent.payload or {}).get("provenance")
                                if (not _existing_prov
                                        and _prov.write_path == "direct_ingest"):
                                    _reinforce_updates["provenance"] = _prov_dict
                                graph.update_payload(_existing_eid, _reinforce_updates)
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

                # Block A: merge caller-supplied extra_payload with internal
                # fields. Internal keys win over caller keys to keep identity
                # invariants (workspace_id, scope, provenance, etc.) trustworthy;
                # caller's extras (e.g. baton_lifecycle) are preserved as long as
                # they don't collide.
                _internal_ep: Dict[str, Any] = {
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
                    # D1-S2: affect-value production lineage. Sibling of affect_tag/
                    # affect_conf, deliberately OUTSIDE ProvenanceV1 (which records
                    # row lineage, not affect lineage). Emitted iff the ingest affect
                    # classification completed successfully; the not-evaluated states
                    # (disabled / raised) are left unstamped. The internal-wins merge
                    # below (_merged_ep.update(_internal_ep)) also guarantees a caller
                    # cannot smuggle a forged envelope via extra_payload.
                    **(
                        {"affect_attribution": build_ingest_classifier_attribution(affect_tag=affect_tag)}
                        if affect_classification_completed else {}
                    ),

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

                    # Provenance (v2.4.x first-pass)
                    "provenance": _prov_dict,
                }
                # Q3-D1-H1: affect_attribution is an internal authority-bearing
                # field (affect-VALUE lineage). Ordinary callers must never set it
                # through the generic extra_payload carrier. Strip it from a COPY of
                # the caller payload before the merge; the internal writer above adds
                # a truthful envelope back iff classification completed. This makes
                # anti-forgery GLOBAL rather than stamped-row-only: when classification
                # is disabled or raised, _internal_ep carries no affect_attribution, so
                # without this strip a forged caller envelope would survive the merge.
                # The caller's original dict is never mutated (we copy first).
                # Scope is deliberately narrow: only this one reserved key is stripped;
                # the not-evaluated fallback vocabulary and all other producers stay
                # untouched. unset != not evaluated.
                _caller_ep: Dict[str, Any] = dict(extra_payload or {})
                _caller_ep.pop("affect_attribution", None)
                _merged_ep: Dict[str, Any] = _caller_ep
                _merged_ep.update(_internal_ep)  # internal wins on collision

                # Ordinary ingest fails closed for canon authority.
                # Kernel promotion_score remains advisory telemetry for
                # memory mechanics, but canon promotion must come from an
                # explicit governed path.
                _auto_canon = False
                eid = graph.spawn_memory(
                summary=summary,
                embedding=emb,
                mtype=signals.memory_type,
                strength=signals.strength,
                confidence=signals.confidence,
                half_life_days=half_life_days,
                links=signals.links,
                canon=(False if suppress_canon else _auto_canon),
                user_id=agent_id,
                step=step,
                memory_class=memory_class,
                extra_payload=_merged_ep,
                )

                _mark_embed_audit_dirty(self.data_dir, workspace_id)

                legacy_registry = ws.motif_regs[chosen_domain]
                motif_runtime = LegacyMotifRuntimeAdapter(legacy_registry)
                motif_mutation = motif_runtime.attach_or_create(
                    emb,
                    memory_eid=int(eid),
                    agent_id=agent_id,
                    summary=summary,
                    attach_threshold=float(0.62 + 0.2 * ident.overlay.get("motif_sensitivity", 0.7)),
                )
                motif_ids = list(motif_mutation.affected_runtime_ids)
                created_motif = motif_mutation.created_runtime_id

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
                    field_rows = compute_coherence_field(
                        motif_runtime.project_coherence_field_rows()
                    )
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
                except Exception:
                    # The nodes.jsonl append is the canonical commit boundary.
                    # Pre-commit embedding/event/edge residue is intentionally
                    # retained for later reconciliation, but the live entity
                    # must not remain queryable as stored memory.
                    graph.abort_unflushed_node(int(eid))
                    self._log.warning(
                        "canonical_memory_commit_failed workspace_id=%s agent_id=%s",
                        _safe_log_value(workspace_id),
                        _safe_log_value(agent_id),
                    )
                    return {
                        "stored": False,
                        "reinforced": False,
                        "failure_code": "canonical_commit_failed",
                        "eid": None,
                        "domain_chosen": chosen_domain,
                    }
                stored = True
                state_symbol = sym.get("state_symbol")

        if not stored:
            storage_outcome = PostWriteStorageOutcome.NO_WRITE
        elif _reinforced_eid is not None:
            storage_outcome = PostWriteStorageOutcome.REINFORCED_EXISTING
        else:
            storage_outcome = PostWriteStorageOutcome.CREATED_NEW

        post_write_context = FabricPostWriteContext.make(
            workspace_id=workspace_id,
            agent_id=agent_id,
            scope=scope,
            chosen_domain=chosen_domain,
            step=int(step),
            storage_outcome=storage_outcome,
            stored=stored,
            eid=int(eid) if eid is not None else None,
            created_motif=created_motif,
            motif_ids=motif_ids,
            half_life_days=half_life_days,
            summary=summary,
            embedding=emb,
            memory_class=memory_class,
            memory_type=signals.memory_type,
            strength=float(signals.strength),
            confidence=float(signals.confidence),
            promotion_score=float(signals.promotion_score),
            stability_delta=float(signals.stability_delta),
            tri_mod=tri_mod,
            debug=debug,
            srg_state=_srg_dict,
            phase_durations=_pt_durations,
            state_symbol=state_symbol,
            affect_tag=affect_tag,
            affect_conf=affect_conf,
            skip_packet_emission=skip_packet_emission,
        )
        memory_access = LegacyPostWriteMemoryAccess(
            graph, expected_dimension=int(ws.embed_dim),
        )
        post_write_dependencies = LegacyFabricPostWriteDependencies(
            owner=self,
            workspace=ws,
            graph=graph,
            world_runtime=LegacyWorldRuntime(graph),
            derived_memory_runtime=LegacyDerivedMemoryRuntime(owner=self, workspace=ws),
            memory_access=memory_access,
            memory_enumeration=memory_access,
            srg_runtime=LegacySRGTransientRuntime(graph),
            embedding_dimension=int(ws.embed_dim),
            identity=ident,
            motif_registry=legacy_registry,
            motif_runtime=motif_runtime,
            model_state=state,
            kernel_context=runtime_ctx,
            agent_key=ak,
            detect_canon_conflict=_detect_canon_conflict,
            proposal_allowed=_proposal_allowed,
            random_chance=random_chance,
            save_checkpoint=save_checkpoint,
            build_motif_summary=build_motif_summary,
            build_shard_snapshot=build_shard_snapshot,
            hivemind_log=hivemind_log,
        )
        proposal_id = LegacyFabricPostWriteAdapter(post_write_dependencies).run(
            post_write_context
        ).proposal_id

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

    # -----------------------------------------------------------------------
    # Lane-specific retrieval helpers (Phase 1, v2.4.4)
    #
    # These extract the three retrieval lanes that fabric.query() uses
    # internally.  In Phase 1 they are only called by query() itself;
    # Phase 2 will let the aperture builder call them directly so that
    # cognition roles receive truly scope-separated memory context.
    # -----------------------------------------------------------------------

    def _resolve_srg_writeback_target(
        self,
        ws: Workspace,
        workspace_id: str,
        agent_id: str,
        hit: Dict[str, Any],
    ) -> Optional[Any]:
        """Resolve an SRG writeback target from a hit's graph origin.

        EIDs are graph-local, so target selection must be fully determined by
        the flattened origin metadata carried by the retrieved hit.  Anything
        incomplete or inconsistent fails closed rather than probing graphs by
        raw EID.
        """
        try:
            eid = int(hit.get("eid"))
        except (TypeError, ValueError):
            return None

        if str(hit.get("workspace_id") or "") != str(workspace_id):
            return None

        scope = str(hit.get("scope") or "")
        graph: Optional[MemoryGraph]
        if scope == "private":
            if str(hit.get("agent_id") or "") != str(agent_id):
                return None
            graph = self.private_graphs.get(self._agent_key(workspace_id, agent_id))
        elif scope == "shared":
            domain_id = str(hit.get("domain_id") or "")
            if not domain_id:
                return None
            graph = ws.shared_graphs.get(domain_id)
        else:
            # Deep and unknown-origin hits do not carry a graph identity that
            # is sufficient for this RAM-only SRG writeback.
            return None

        if graph is None:
            return None
        entity = graph.entities.get(eid)
        if entity is None:
            return None

        payload = getattr(entity, "payload", {}) or {}
        if str(payload.get("workspace_id") or "") != str(workspace_id):
            return None
        if str(payload.get("scope") or "") != scope:
            return None
        if scope == "private":
            if str(payload.get("agent_id") or "") != str(agent_id):
                return None
        elif str(payload.get("domain_id") or "") != str(hit.get("domain_id") or ""):
            return None
        return entity

    @staticmethod
    def _query_read_hit_key() -> str:
        """Private carrier for one A2 hit during qualification orchestration."""
        return "_a3_qualified_query_hit"

    def _legacy_query_read_model(
        self,
        ws: Workspace,
        *,
        workspace_id: str,
        agent_id: str,
        preferred_private_domain: str | None,
    ) -> LegacyQualifiedQueryReadModel:
        """Adapt the live legacy readers without changing their public owner.

        A3 always routes public ``query()`` through this adapter too, so the
        orchestration has one storage seam.  The legacy compatibility hit is
        preserved verbatim; only native qualification uses A2's current motif
        membership projection to reconstruct an otherwise absent native field.
        """
        ak = self._agent_key(workspace_id, agent_id)
        graph = self.private_graphs.get(ak)
        if graph is None:
            raise KeyError(f"private query lane is unavailable for agent {agent_id!r}")
        private_domain = self._legacy_private_motif_domain(
            graph,
            registries=ws.motif_regs,
            preferred_domain=preferred_private_domain,
        )
        return LegacyQualifiedQueryReadModel(
            workspace_id,
            private_graphs={agent_id: graph},
            shared_graphs=ws.shared_graphs,
            motif_registries=ws.motif_regs,
            private_motif_domains={agent_id: private_domain},
            shared_domain_order=tuple(ws.shared_graphs),
        )

    @staticmethod
    def _legacy_private_motif_domain(
        graph: MemoryGraph,
        *,
        registries: Dict[str, MotifRegistry],
        preferred_domain: str | None,
    ) -> str:
        """Recover the already-stored private motif-domain fact, never infer one.

        The A2 legacy adapter needs one registry to expose its internal
        membership projection.  Public legacy result payloads remain untouched
        below, so an old multi-domain private graph cannot change public query
        behavior at this qualification seam.
        """
        for entity in graph.entities.values():
            payload = getattr(entity, "payload", {}) or {}
            domain_id = payload.get("domain_id")
            if isinstance(domain_id, str) and domain_id in registries:
                return domain_id
        if preferred_domain in registries:
            return str(preferred_domain)
        try:
            return next(iter(registries))
        except StopIteration as exc:
            raise KeyError("workspace has no motif registry for private query") from exc

    def _query_read_hits_to_compatibility(
        self,
        hits: tuple[QualifiedQueryHit, ...],
        *,
        read_model: QualifiedQueryReadModel,
    ) -> List[Dict[str, Any]]:
        """Expose the existing hit shape while retaining A2 identity privately."""
        native = isinstance(read_model, NativeQualifiedQueryReadModel)
        values: List[Dict[str, Any]] = []
        for hit in hits:
            value = hit.as_legacy_hit()
            if native:
                # A2 membership is current native relationship truth.  Legacy
                # graph payloads already carry the compatibility list, so do
                # not rewrite them and thereby perturb public legacy behavior.
                value["motifs"] = list(hit.motif_ids)
            value[self._query_read_hit_key()] = hit
            values.append(value)
        return values

    @staticmethod
    def _rank_domains_from_read_model(
        query_embedding: Any,
        *,
        read_model: QualifiedQueryReadModel,
        domain_order: tuple[str, ...],
        expected_dimension: int,
        top_k: int,
    ) -> List[DomainScore]:
        """Run the existing DomainRouter cosine/stable-sort law over A2 geometry."""
        scores: List[DomainScore] = []
        for domain_id in domain_order:
            geometry = read_model.domain_geometry(domain_id)
            centroid = np.asarray(geometry.centroid, dtype=np.float32).reshape(-1)
            if centroid.size != expected_dimension:
                raise ValueError("qualified query geometry dimension mismatch")
            if np.allclose(centroid, 0):
                score = 0.0
            else:
                score = float(cos_sim(query_embedding, centroid))
            scores.append(DomainScore(domain_id=domain_id, score=score))
        scores.sort(key=lambda item: item.score, reverse=True)
        return scores[:top_k]

    def _query_with_read_model(
        self,
        workspace_id: str,
        agent_id: str,
        query_text: str,
        *,
        read_model: QualifiedQueryReadModel,
        top_k: int = 8,
        domain_id: Optional[str] = None,
        peek_bridges: bool = False,
        explain: bool = False,
        continuity_debug: bool = False,
        memory_plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Private A3 qualification entrypoint; it is not an API selector."""
        return self.query(
            workspace_id, agent_id, query_text,
            top_k=top_k, domain_id=domain_id, peek_bridges=peek_bridges,
            explain=explain, continuity_debug=continuity_debug,
            memory_plan=memory_plan,
            _qualification_read_model=read_model,
        )

    def _query_private_lane(
        self,
        ak: str,
        workspace_id: str,
        query_text: str,
        agent_id: str,
        top_k: int,
        read_model: QualifiedQueryReadModel,
    ) -> List[Dict[str, Any]]:
        """Return hits from the agent's private graph only.

        Parameters
        ----------
        ak : str
            Agent key (workspace_id/agent_id).
        query_text : str
            The search query.
        agent_id : str
            Used for user_id filtering inside graph.search().
        top_k : int
            Maximum number of private hits to return.

        Returns
        -------
        list[dict]
            Raw scored hits from private_graphs[ak].search().
        """
        if top_k <= 0:
            return []
        hits = read_model.private_lane(workspace_id, agent_id).search(
            query_text, top_k=top_k, user_id=agent_id,
        )
        return self._query_read_hits_to_compatibility(
            hits, read_model=read_model,
        )

    def _query_shared_lane(
        self,
        ws: Any,
        workspace_id: str,
        query_text: str,
        top_k: int,
        domains: List[str],
        read_model: QualifiedQueryReadModel,
        *,
        peek_bridges: bool = False,
        peek_top_k: int = 4,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Return hits from shared graphs (+ optional bridge peek).

        Parameters
        ----------
        ws : Workspace
            The workspace object (carries shared_graphs, bridges,
            domain_policies).
        query_text : str
            The search query.
        top_k : int
            Maximum hits *per domain* from the primary domains.
        domains : list[str]
            Ranked domain IDs (usually top 2 from the domain router).
        peek_bridges : bool
            Whether to fan out into bridged domains.
        peek_top_k : int
            Per-domain hit cap for bridge-peek domains.

        Returns
        -------
        (hits, bridge_peek_domains)
            hits: list of scored hit dicts from shared graphs.
            bridge_peek_domains: list of domain IDs reached via bridge.
        """
        shared_hits: List[Dict[str, Any]] = []
        if top_k > 0:
            for d in domains:
                shared_hits.extend(
                    self._query_read_hits_to_compatibility(
                        read_model.shared_lane(workspace_id, d).search(
                            query_text, top_k=top_k, user_id=None,
                        ),
                        read_model=read_model,
                    )
                )

        bridge_peek_domains: List[str] = []
        if peek_bridges:
            rel_br = ws.bridges.relevant_to_domains(domains, top_k=12)
            strict = any(
                bool(ws.domain_policies.get(d, {}).get("bridge_peek_requires_approval", False))
                for d in domains
            )
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
            for pd in bridge_peek_domains:
                if pd in ws.shared_graphs:
                    hits_pd = self._query_read_hits_to_compatibility(
                        read_model.shared_lane(workspace_id, pd).search(
                            query_text, top_k=peek_top_k, user_id=None,
                        ),
                        read_model=read_model,
                    )
                    for h in hits_pd:
                        hh = dict(h)
                        hh["via_bridge"] = True
                        hh["bridge_domain"] = pd
                        shared_hits.append(hh)

        return shared_hits, bridge_peek_domains

    def _query_deep_lane(
        self,
        ak: str,
        workspace_id: str,
        agent_id: str,
        qemb: Any,
        top_k: int,
        canonical_step: int,
    ) -> List[Dict[str, Any]]:
        """Return deep/spirit-return hits with explicit scope='deep'.

        Parameters
        ----------
        ak : str
            Agent key.
        workspace_id, agent_id : str
            For symbol state and warmup tracker paths.
        qemb : array-like
            Pre-computed query embedding.
        top_k : int
            Maximum deep hits to return.
        canonical_step : int
            Current kernel step for warmup tracking.

        Returns
        -------
        list[dict]
            Deep memory hits enriched with spirit-return metadata.
            Each hit carries ``scope="deep"`` and
            ``from_deep_memory=True``.
        """
        if not self._compress_enable or top_k <= 0:
            return []
        try:
            from .compression import _attach_persisted_deep_store
            from .spirit_return import enrich_deep_memory_hit, WarmupTracker, inject_spirit_return_into_hit

            _deep_store = self._deep_stores.get(ak)
            if not _deep_store:
                _deep_store = _attach_persisted_deep_store(
                    self, agent_id, workspace_id=workspace_id
                )
            if not _deep_store:
                return []

            _deep_qv = np.asarray(qemb, dtype=np.float32).reshape(-1)
            _deep_hits = _deep_store.query(
                _deep_qv,
                top_k=max(1, top_k),
            )

            # Current kernel symbol from persisted state
            _sym_state = _load_symbol_state(self.data_dir, workspace_id, agent_id)
            _current_sym = str(_sym_state.get("last_symbol", "◯") or "◯")

            # Warmup tracker (lazy init per agent). Build the directory through
            # the guarded _agent_dir() helper so workspace_id / agent_id are
            # validated and contained (matches every other per-agent path in
            # fabric); the raw join here previously relied solely on
            # WarmupTracker's constructor guard.
            _warmup_dir = Path(_agent_dir(self.data_dir, workspace_id, agent_id)) / "warmup"
            _warmup = WarmupTracker(_warmup_dir, base_dir=self.data_dir)

            # Source-row presence predicate for beta filtering and the
            # short-path compressed-eid set. Per Cluster 5 Path C Q1
            # implementation framing
            # (docs/CLUSTER_5_PATH_C_Q1_IMPLEMENTATION_FRAMING_v0.1.md):
            # orphaned deep hits -- those whose source row is absent from
            # MemoryGraph.entities -- must NOT leave _query_deep_lane on
            # the normal consumer path. If no private graph exists for
            # this agent, every deep hit is orphaned by definition.
            _pg = self.private_graphs.get(ak)
            if _pg is None:
                return []
            _pg_entities = _pg.entities

            # Identify short-path compressed eids for spirit-return
            # enrichment.
            _core_compressed: set = set()
            for _eid_key, _ent in _pg_entities.items():
                if (_ent.payload or {}).get("compressed"):
                    _core_compressed.add(int(_eid_key))

            # Wrapper used internally to emit the canonical
            # authority_status marker per Step C. The wrapper does not
            # flow downstream in H1; only its marker block is injected
            # into the returned dict.
            from .deep_hits import DeepRetrievalHit

            results: List[Dict[str, Any]] = []
            for _dm in _deep_hits:
                # Beta filter: source row must be present in
                # MemoryGraph.entities at access time. Defensive: tolerate
                # both int and string keys in case any writer path leaves
                # a JSON-roundtripped string key behind.
                _eid = int(_dm.eid)
                if _eid not in _pg_entities and str(_eid) not in _pg_entities:
                    continue

                _ws = _warmup.get_or_create(_dm.eid, canonical_step)
                _spirit = enrich_deep_memory_hit(
                    _dm, _current_sym, _ws, _eid in _core_compressed
                )
                _hit_dict = inject_spirit_return_into_hit(_spirit)

                # Inject canonical authority_status marker (Path C 4.1).
                # The wrapper is constructed for the marker block only;
                # it does not flow downstream in H1.
                _wrapper = DeepRetrievalHit(
                    source_eid=_eid,
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    compressed_step=int(getattr(_dm, "compressed_step", 0) or 0),
                    similarity_score=float(
                        getattr(_dm, "compression_score", 0.0) or 0.0
                    ),
                    embedding_ref=(
                        dict(_dm.embedding_ref)
                        if isinstance(getattr(_dm, "embedding_ref", None), dict)
                        else None
                    ),
                    display_text=(
                        str(_dm.summary)
                        if getattr(_dm, "summary", None)
                        else None
                    ),
                    derivative_metadata=dict(getattr(_dm, "metadata", {}) or {}),
                )
                _hit_dict["authority_status"] = (
                    _wrapper.to_dict()["authority_status"]
                )

                # Q3-D1-S4b: surface the preserved source affect-attribution
                # snapshot onto the runtime echo — the same object that carries
                # the Q1 authority markers — so a reader sees the original
                # producer envelope (inferred / derived) instead of synthesizing
                # recovered/migration/legacy_read_fallback. Copied verbatim from
                # the durable DeepMemory.metadata (D1-S4a) only when a snapshot
                # exists; absent -> legacy source stays legacy (parked vocabulary).
                # affect_tag MUST be copied beside the envelope: read_affect_
                # attribution validates a `set` envelope against affect_tag and
                # fails loud if it is missing. affect_conf is deliberately NOT
                # surfaced here (not needed for validation; held for D1-S5). This
                # is affect-VALUE lineage and stays orthogonal to authority_status
                # (the echo's authority posture), which is unchanged.
                _dm_metadata = getattr(_dm, "metadata", {}) or {}
                if "affect_attribution" in _dm_metadata:
                    _hit_dict["affect_tag"] = _dm_metadata.get("affect_tag")
                    _hit_dict["affect_attribution"] = dict(
                        _dm_metadata["affect_attribution"]
                    )

                results.append(_hit_dict)

            return results
        except Exception:
            return []  # Spirit return is non-fatal

    # -----------------------------------------------------------------------
    # Alpha diagnostic helper (Path C Step E)
    # -----------------------------------------------------------------------

    def list_orphaned_deep_hits(
        self,
        workspace_id: str,
        agent_id: str,
    ) -> List["OrphanedDeepHit"]:
        """Return all orphaned deep records for an agent's deep store.

        An orphaned deep record is one whose source EID is absent from
        MemoryGraph.entities at access time. Per Cluster 5 Path C Q1
        framing: orphan records must never reach normal cognition,
        autonomy, character, sharing, lifecycle, affect-attribution,
        or governance paths.

        This method is the alpha diagnostic building block. Callers
        must be operator/admin/diagnostic surfaces only. It is NOT
        called by _query_deep_lane or any cognition consumer.

        Parameters
        ----------
        workspace_id, agent_id : str
            Identifies the agent whose deep store is enumerated.

        Returns
        -------
        list of OrphanedDeepHit
            Empty list if no deep store exists for the agent.
            All deep records become orphans if no private graph
            exists for the agent.
        """
        from .deep_hits import OrphanedDeepHit

        ak = self._agent_key(workspace_id, agent_id)

        deep_store = self._deep_stores.get(ak)
        if deep_store is None:
            return []

        # Intentional internal access to the deep store's record list.
        # The alpha diagnostic surface is the one legitimate caller for
        # this enumeration; normal cognition consumers go through
        # _query_deep_lane, not through enumeration. A future hardening
        # may extract a public iter_all() method on DeepMemoryStore.
        try:
            deep_store._ensure_loaded()
        except Exception as exc:
            log.warning(
                "orphan diagnostic enumeration: deep store load failed "
                "for workspace_id=%s agent_id=%s: %s",
                workspace_id,
                agent_id,
                exc,
            )
        all_records = list(getattr(deep_store, "_memories", None) or [])

        pg = self.private_graphs.get(ak)
        pg_entities = pg.entities if pg is not None else {}

        now_ts = int(time.time())
        orphans: List["OrphanedDeepHit"] = []
        for record in all_records:
            eid = int(record.eid)
            # Defensive: tolerate both int and string keys, matching the
            # beta-filter robustness applied at _query_deep_lane.
            if eid in pg_entities or str(eid) in pg_entities:
                continue
            orphans.append(
                OrphanedDeepHit(
                    source_eid=eid,
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    compressed_step=int(
                        getattr(record, "compressed_step", 0) or 0
                    ),
                    orphan_reason="source_eid_not_found",
                    detected_at=now_ts,
                )
            )
        return orphans

    # -----------------------------------------------------------------------
    # Canonical step helper
    # -----------------------------------------------------------------------

    def _get_canonical_step(self, ak: str) -> int:
        """Return the authoritative 'now' step for an agent.

        Uses the agent's kernel ModelState.step. Falls back to
        max(born_step) from the private graph.
        """
        _canonical_step: int = -1
        try:
            _agent_state = self.agent_states.get(ak)
            if _agent_state is not None:
                _canonical_step = int(getattr(_agent_state, "step", -1))
        except Exception as _step_exc:
            log.debug("Failed to read canonical step from agent state: %s", _step_exc)
        if _canonical_step < 0:
            _pg_fallback = self.private_graphs.get(ak)
            if _pg_fallback:
                for _ent_fb in _pg_fallback.entities.values():
                    _canonical_step = max(_canonical_step, int(getattr(_ent_fb, "born_step", 0) or 0))
        return _canonical_step

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
        memory_plan: Optional[Dict[str, Any]] = None,
        _qualification_read_model: QualifiedQueryReadModel | None = None,
    ) -> Dict[str, Any]:
        ws = self.get_workspace(workspace_id)
        ak = self._agent_key(workspace_id, agent_id)
        ident = self.create_agent(workspace_id, agent_id)

        read_model = _qualification_read_model or self._legacy_query_read_model(
            ws,
            workspace_id=workspace_id,
            agent_id=agent_id,
            preferred_private_domain=domain_id,
        )
        native_qualification = isinstance(read_model, NativeQualifiedQueryReadModel)
        if native_qualification and self._compress_enable:
            # A3 deliberately has no native deep lane.  Refuse the profile
            # rather than silently mixing native core candidates with legacy
            # deep-memory retrieval.
            raise ValueError("qualified native query does not support enabled deep retrieval")

        qemb = self.kernel.embedder.embed(query_text)
        if int(np.asarray(qemb).reshape(-1).shape[0]) != int(ws.embed_dim):
            raise HTTPException(
                status_code=409,
                detail=f"Embedding dimension mismatch; workspace '{workspace_id}' locked to {ws.embed_dim} but query embedder returned {int(np.asarray(qemb).reshape(-1).shape[0])}.",
            )
        dom_scores = self._rank_domains_from_read_model(
            qemb,
            read_model=read_model,
            domain_order=tuple(ws.shared_graphs),
            expected_dimension=int(ws.embed_dim),
            top_k=2,
        )
        domains = [d.domain_id for d in dom_scores]
        if domain_id:
            domains = [domain_id] + [d for d in domains if d != domain_id]
            domains = domains[:2]

        # --- Memory-plan-aware retrieval (v2.4.2) ---
        # When a MemoryPlan is provided (from the thinking controller),
        # use lane-specific top_k instead of flat top_k for everything.
        # Clamped to sane bounds: each lane top_k in [0, top_k*2].
        _mp = memory_plan or {}
        _mp_topk = _mp.get("top_k_by_lane", {})
        _mp_weights = _mp.get("weight_by_lane", {})
        _topk_cap = top_k * 2  # safety cap per lane

        _core_k = min(max(0, int(_mp_topk.get("core", top_k))), _topk_cap)
        _relational_k = min(max(0, int(_mp_topk.get("relational", top_k))), _topk_cap)
        _deep_key_present = "deep" in _mp_topk
        _deep_k = min(max(0, int(_mp_topk.get("deep", 0))), _topk_cap)

        # --- Lane retrieval (v2.4.4) ---
        # Each lane is a separate helper; query() merges and rescores.
        private_hits = self._query_private_lane(
            ak, workspace_id, query_text, agent_id, top_k=_core_k,
            read_model=read_model,
        )

        shared_hits, bridge_peek_domains = self._query_shared_lane(
            ws, workspace_id, query_text, top_k=_relational_k, domains=domains,
            read_model=read_model,
            peek_bridges=peek_bridges, peek_top_k=max(2, top_k // 2),
        )

        # --- Canonical current step (v2.4.x) ---
        _canonical_step = self._get_canonical_step(ak)

        # --- Deep memory fallback with spirit return (Phase 6) ---
        # Deep is a headroom-bounded gap filler. An absent plan key preserves
        # baseline gap-fill; an explicit value caps it, and zero declines it.
        _remaining = max(0, top_k - len(private_hits) - len(shared_hits))
        _deep_budget = min(_deep_k, _remaining) if _deep_key_present else _remaining

        deep_hits = self._query_deep_lane(
            ak, workspace_id, agent_id, qemb,
            top_k=_deep_budget, canonical_step=_canonical_step,
        )

        # merge and rescore with motif alignment if available
        # NOTE (v2.4.4): deep_hits are now a separate lane instead of
        # being appended to shared_hits.  The merged pool is identical
        # to the previous behavior — deep hits participate in the same
        # unified rescore pass.
        all_hits = private_hits + shared_hits + deep_hits

        # Block A + B (docs/BLOCK_A_DESIGN.md §7.1, docs/BLOCK_B_DESIGN.md
        # §6.5): default lanes exclude non-substrate memory classes.
        # HARD lifecycle filter, not score de-weighting. Each class has
        # its own explicit retrieval primitive:
        #   - baton:       fabric.list_active_batons
        #   - reference:   fabric.load_reference / fabric.list_active_loads
        #   - environment: fabric.consult_environment
        # Reference and environment never enter memory_graph in the first
        # place (they live in their own per-workspace stores), so this
        # filter is defensive — but the explicit exclusion is
        # architectural signal against future drift where a new code path
        # might accidentally surface them here.
        #
        # Block C extension (2026-04-21): "closure" joins the exclusion
        # set. Closure objects live in ClosureStore (torment_service/
        # closure_memory.py) and do not enter memory_graph either — the
        # filter is again defensive and signals that default retrieval
        # lanes must not surface closure synthesis objects. This is a
        # HARD FILTER (exclusion set), not a de-weighting, not a profile
        # tweak. Per BLOCK_C_DESIGN.md §10 the query SIGNATURE is
        # unchanged — only this internal frozenset is extended.
        _NON_DEFAULT_CLASSES = frozenset({
            "baton", "reference", "environment", "closure",
        })
        all_hits = [h for h in all_hits
                    if h.get("memory_class") not in _NON_DEFAULT_CLASSES]
        rescored = []
        # FILTER-A (Commit γ): defensive init so the return dict never references
        # an unbound variable if future branch edits skip the filter call.
        # Populated by filter_llm_facing() after top-k selection below.
        _filter_excluded: List[Dict[str, Any]] = []
        active_motifs = {}
        for d in domains:
            active_motifs[d] = read_model.active_motifs(d, top_k=6)

        # Preserve domain ownership of motif geometry.  Runtime motif IDs are
        # compatibility identifiers within a domain, not global identifiers.
        motif_centroids: Dict[_QueryMotifIdentity, np.ndarray] = {}
        for d in domains:
            for qualified_motif in read_model.domain_geometry(d).motifs:
                m = qualified_motif.geometry
                motif_centroids[_QueryMotifIdentity(
                    workspace_id=str(workspace_id),
                    domain_id=str(d),
                    motif_id=str(m.runtime_motif_id),
                )] = m.centroid_np()

        
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
        # Conflict map keyed by flattened graph origin plus graph-local EID.
        conflict_map = _build_conflict_map(ws, workspace_id, domains)

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
        # Character continuity: cap identity anchor dominance so anchors guide rather than dominate.
        try:
            _anchor_topk = int(os.getenv("TORMENT_ANCHOR_BOOST_TOPK", "3"))
        except Exception:
            _anchor_topk = 3
        _anchor_full_boost: set[QueryMemoryIdentity] = set()
        if _anchor_topk > 0:
            try:
                _acand: List[Tuple[QueryMemoryIdentity, float]] = []
                for _hh in all_hits:
                    try:
                        _htype = str(_hh.get("type") or "")
                        # §2A P7: only seed-canon and drift-correction anchors
                        # qualify for the full continuity boost.  Derived
                        # (non-canon) identity_anchors are excluded so they
                        # cannot bypass the tier-weight separation.
                        if _htype == "identity_anchor":
                            if not bool(_hh.get("canon")):
                                continue
                        elif _htype not in ("seed_canon", "drift_correction"):
                            continue
                        if bool(_hh.get("anchor_retired")):
                            continue
                        _memory_identity = qualified_query_memory_identity(
                            _hh,
                            expected_workspace_id=str(workspace_id),
                        )
                        if _memory_identity is None:
                            continue
                        _acand.append((_memory_identity, float(_hh.get("score", 0.0))))
                    except Exception:
                        continue
                _acand.sort(key=lambda x: x[1], reverse=True)
                _anchor_full_boost = {identity for (identity, _score) in _acand[:_anchor_topk]}
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

        _spiral_neg_recent = 0
        if _spiral_enable and ak in self.private_graphs:
            try:
                _st = _load_affect_state(self.data_dir, ws.workspace_id, str(agent_id))
                _dh = _st.get("drift_hist") or []
                if not isinstance(_dh, list):
                    _dh = []
                if _canonical_step >= 0:
                    _neg = {"stressed", "sad", "angry"}
                    for _e in _dh[-20:]:
                        try:
                            if int(_e.get("step", -10**9)) < _canonical_step - _spiral_window:
                                continue
                            if str(_e.get("to")) in _neg:
                                _spiral_neg_recent += 1
                        except Exception:
                            continue
            except Exception:
                _spiral_neg_recent = 0

        # Build shared continuity context (used by per-hit scoring below)
        _cont_ctx = ContinuityContext.from_env(
            agent_id=str(agent_id),
            canonical_step=_canonical_step,
            affect_personal=_affect_personal,
            q_affect_tag=_q_affect_tag,
            q_affect_conf=_q_affect_conf,
            spiral_neg_recent=_spiral_neg_recent,
            workspace_id=str(workspace_id),
            anchor_full_boost_memory_ids=frozenset(_anchor_full_boost),
        )

        now_ts = _now_ts()
        for h in all_hits:
            _qualified_hit = h.get(self._query_read_hit_key())
            # Extract provenance early so all scoring phases can use it.
            _h_prov_raw = (h.get("payload") or h).get("provenance") or h.get("provenance")
            _h_is_tool_result = (
                isinstance(_h_prov_raw, dict)
                and _h_prov_raw.get("source_type") == "tool_result"
            )

            sim = float(h.get("score", 0.0))
            strength = float(h.get("strength", 0.5))
            ts = int(h.get("created_ts", now_ts))
            recency_days = max(0.0, (now_ts - ts) / 86400.0)
            motifs = h.get("motifs") or []
            motif_identities: List[_QueryMotifIdentity] = []
            if not motifs and motif_centroids:
                # infer best motif by similarity
                best_identity = None
                best_ms = -1.0
                for motif_identity, c in motif_centroids.items():
                    s2 = float(np.dot(qemb, c) / ((np.linalg.norm(qemb)+1e-12)*(np.linalg.norm(c)+1e-12)))
                    if s2 > best_ms:
                        best_ms = s2
                        best_identity = motif_identity
                if best_identity is not None and best_ms >= 0.55:
                    motifs = [best_identity.motif_id]
                    motif_identities = [best_identity]
            elif motifs:
                for mid in motifs:
                    identity = _qualified_query_motif_identity(
                        h,
                        workspace_id=str(workspace_id),
                        motif_id=mid,
                    )
                    if identity is not None:
                        motif_identities.append(identity)

            motif_alignment = 0.0
            for motif_identity in motif_identities:
                c = motif_centroids.get(motif_identity)
                if c is None:
                    continue
                motif_alignment = max(motif_alignment, float(np.dot(qemb, c) / ((np.linalg.norm(qemb)+1e-12)*(np.linalg.norm(c)+1e-12))))
            contradiction_risk = float(h.get("contradiction_risk", 0.0))
            conflict_key = _conflict_hit_key(h)
            conflict_info = conflict_map.get(conflict_key) if conflict_key is not None else None
            conflict_penalty = 0.0
            conflict_ids: List[str] = []
            conflict_status = None
            if conflict_info is not None and str(h.get("scope", "")) == "shared" and bool(h.get("canon", False)):
                conflict_status = "open"
                conflict_ids = list(conflict_info.get("conflict_ids") or [])
                conflict_penalty = float(conflict_info.get("max_score", 0.0))
                if not wants_contested:
                    contradiction_risk = max(contradiction_risk, 0.5 * conflict_penalty)
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

            # All continuity bonuses via shared helper (self-thread, self-anchor,
            # thread-window, affect, mood-drift, mood-spiral)
            _cont = compute_continuity_bonuses(h, _cont_ctx, is_tool_result=_h_is_tool_result)
            type_bonus += _cont.total
            if _bon is not None:
                _bon["self_thread"] += _cont.self_thread_bonus
                _bon["self_anchor"] += _cont.self_anchor_bonus
                _bon["thread_window"] += _cont.thread_window_bonus
                _bon["affect_match"] += _cont.affect_match_bonus
                _bon["mood_drift"] += _cont.mood_drift_bonus
                _bon["mood_spiral_penalty"] += _cont.mood_spiral_penalty

            base_score = score_hit(sim=sim, strength=strength, recency_days=recency_days, motif_alignment=motif_alignment, contradiction_risk=contradiction_risk, type_bonus=0.0)
            final = score_hit(sim=sim, strength=strength, recency_days=recency_days, motif_alignment=motif_alignment, contradiction_risk=contradiction_risk, type_bonus=type_bonus)

            # Reinforcement boost (reinforce contract v2.4.x, Plan-D3):
            # Additive bounded boost at rank stage after lane-separated recall.
            # Formula: final += TORMENT_REINFORCE_BOOST * ln(1 + reinforcement_count)
            # Default 0.04 chosen via sanity-check against observed score distribution
            # (single reinforcement ≈ 3-5% of typical semantic score).
            _rc = int((h.get("payload") or h).get("reinforcement_count", 0))
            if _rc > 0:
                try:
                    _reinforce_boost = float(os.getenv("TORMENT_REINFORCE_BOOST", "0.04"))
                except Exception:
                    _reinforce_boost = 0.04
                final += _reinforce_boost * math.log(1 + _rc)

            # SRG scoring bonuses + breathing evolution (Phase 3)
            # Observability: track the per-hit SRG multipliers (default 1.0) so
            # query(explain=True) can mirror trace()'s SRG decomposition. The
            # `final *=` math is unchanged — the same literal multipliers are
            # applied under the same conditions.
            _srg_same_band = 1.0
            _srg_crystal = 1.0
            _srg_heartbeat = 1.0
            _native_effective_srg: Dict[str, Any] | None = None
            if self._srg_enable:
                # Normalized SRG SCORING/explain source: prefer flattened top-level
                # hit["srg"] (MemoryGraph.search flattens payload), fall back to
                # nested hit["payload"]["srg"] for legacy/manual-shaped hits — the
                # same effective source trace() uses. Read-only; not a writeback gate.
                _srg_score_src = _effective_srg_source(h)
                if native_qualification and isinstance(_qualified_hit, QualifiedQueryHit):
                    try:
                        _native_effective_srg = read_model.effective_srg_state(_qualified_hit)  # type: ignore[attr-defined]
                        if _native_effective_srg is not None:
                            _srg_score_src = _native_effective_srg
                            # Preserve the existing compatibility payload
                            # surface when a qualified process-local overlay
                            # supersedes the durable native baseline.  This is
                            # query-time state only: no SQLite successor is
                            # published and legacy rows are untouched.
                            if isinstance(h.get("payload"), dict):
                                h["payload"] = dict(h["payload"])
                                h["payload"]["srg"] = dict(_native_effective_srg)
                    except Exception as e:
                        self._log.debug("failed to read native transient SRG state: %s", e)
                if _srg_score_src:
                    # Same-band resonance: 8% boost — compare against THIS agent's
                    # last-ingested band only (keyed by (workspace_id, agent_id)).
                    _srg_last_band = self._srg_last_ingest_band_by_agent.get((workspace_id, agent_id))
                    if _srg_last_band is not None and _srg_score_src.get("R_band") == _srg_last_band:
                        _srg_same_band = 1.08
                        final *= _srg_same_band
                    # Crystal identity anchor: 5% boost
                    if _srg_score_src.get("is_crystal", False):
                        _srg_crystal = 1.05
                        final *= _srg_crystal
                    # Class A (deep/slow heartbeat): 3% stability bonus
                    if _srg_score_src.get("heartbeat_class") == "A":
                        _srg_heartbeat = 1.03
                        final *= _srg_heartbeat

                # Breathing evolution / writeback stays gated on the ORIGINAL
                # nested payload source ONLY. This slice fixes scoring/explain
                # source parity but does NOT newly activate breathing/writeback
                # for flattened top-level hits — writeback remains HOLD.
                _srg_writeback_src = (h.get("payload") or {}).get("srg")
                if _srg_writeback_src:
                    # Breathing evolution: retrieved memories are "active" → evolve
                    try:
                        from .srg_engine import SRGMemoryState as _SMS, evolve_breathing as _evolve
                        _srg_evolution_src = _srg_writeback_src
                        if native_qualification and _native_effective_srg is not None:
                            _srg_evolution_src = _native_effective_srg
                        _srg_live = _SMS.from_dict(_srg_evolution_src)
                        _evolve(_srg_live)
                        # Write back evolved state only to the graph that
                        # produced this hit.  Raw EIDs are graph-local.
                        _hit_eid = h.get("eid")
                        if native_qualification and isinstance(_qualified_hit, QualifiedQueryHit):
                            read_model.replace_srg_state(_qualified_hit, _srg_live.to_dict())  # type: ignore[attr-defined]
                        else:
                            _hit_ent = self._resolve_srg_writeback_target(
                                ws, workspace_id, agent_id, h
                            )
                            if _hit_ent is not None:
                                _hit_ent.payload["srg"] = _srg_live.to_dict()
                    except Exception as e:
                        self._log.debug("failed to write srg payload to entity eid=%s: %s", _hit_eid, e)

            # Phase D3: collective-provenance retrieval discount
            # Uses shared helper from scoring.py (centralised contract).
            from .scoring import apply_collective_discount as _apply_coll_disc, is_collective_provenance as _is_coll_prov, derive_query_provenance_type as _derive_q_prov
            _h_is_collective = _is_coll_prov(_h_prov_raw)
            try:
                _coll_discount = float(os.getenv("TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT", "0.50"))
            except Exception:
                _coll_discount = 0.50
            final = _apply_coll_disc(final, _h_prov_raw, discount=_coll_discount)

            # Phase D3b: tool-result retrieval discount
            # Tool results are external observations, not self-knowledge —
            # discount so they don't outrank organic experiential memories.
            # Observability: track the effective discount (1.0 when not applied)
            # for query(explain=True) parity with trace(). `final` math unchanged.
            _tool_result_discount = 1.0
            if _h_is_tool_result:
                try:
                    _tool_discount = float(os.getenv("TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT", "0.85"))
                except Exception:
                    _tool_discount = 0.85
                _tool_result_discount = _tool_discount
                final *= _tool_discount

            # Memory-plan lane weights (v2.4.2):
            # Apply weight multiplier based on hit source/provenance.
            # Private hits → "core" lane, shared → "relational",
            # deep/spirit-return → "deep".
            # NOTE: collective provenance is EXCLUDED — Phase D3 already
            # applies a dedicated discount. Stacking would over-penalize.
            # Observability: track lane name / weight / applied-flag (defaults
            # core / 1.0 / False) so query(explain=True) mirrors trace()'s lane
            # decomposition. The `final *= _lane_w` math is unchanged.
            _lane = "core"
            _lane_w = 1.0
            _lane_applied = False
            if _mp_weights:
                _hit_scope = str(h.get("scope", "private"))
                _is_deep = bool(h.get("spirit_return_mode") or h.get("deep_memory"))
                if _is_deep:
                    _lane = "deep"
                    _lane_w = float(_mp_weights.get("deep", 1.0))
                elif _h_is_collective:
                    # Skip — Phase D3 collective discount already applied above.
                    _lane = "collective"
                    _lane_w = 1.0
                elif _hit_scope == "shared":
                    _lane = "relational"
                    _lane_w = float(_mp_weights.get("relational", 1.0))
                else:
                    _lane = "core"
                    _lane_w = float(_mp_weights.get("core", 1.0))
                # Clamp weight to [0.1, 2.0] to prevent extreme distortion
                _lane_w = max(0.1, min(2.0, _lane_w))
                final *= _lane_w
                _lane_applied = True

            hh = dict(h)
            # A2 structural identity is strictly an orchestration carrier.
            # Never let it cross the existing public query-result boundary.
            hh.pop(self._query_read_hit_key(), None)
            hh["motifs"] = motifs
            hh["final_score"] = final
            # Provenance badge: surface source_type for downstream consumers.
            # Uses derive_query_provenance_type() — the canonical derivation
            # rule (derive_provenance_type) plus VALID_SOURCE_TYPES
            # enforcement.  Legacy bare-string provenance maps to
            # SOURCE_MEMORY when the raw value isn't in the vocabulary.
            # The neighboring semantic `"collective"` check above is
            # preserved untouched because it drives the collective retrieval
            # discount and depends on matching the historical raw value.
            # See docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md §7.2.
            hh["provenance_type"] = _derive_q_prov(_h_prov_raw)
            if isinstance(_h_prov_raw, dict):
                hh["provenance_tool_name"] = _h_prov_raw.get("tool_name")
            if _cd_enable:
                hh["_base_score"] = float(base_score)
                hh["_bonus_components"] = _bon
            hh["motif_alignment"] = motif_alignment
            if conflict_status is not None:
                    hh["conflict_status"] = conflict_status
                    hh["conflict_ids"] = conflict_ids
                    hh["conflict_penalty"] = conflict_penalty

            if explain:
                # Observability parity with trace().explain_for_hit (diagnostic
                # only — no effect on final_score, ranking, filtering, returned
                # hits, MemoryPlan, SRG scoring, or any write path). Every field
                # below is read from a value query() already computed above; this
                # mirrors the same decomposition trace() surfaces.
                hh["explain"] = {
                    "sim": sim,
                    "strength": strength,
                    "recency_days": recency_days,
                    "motif_alignment": motif_alignment,
                    "contradiction_risk": contradiction_risk,
                    "weights": {"alpha": 0.35, "beta": 0.10, "gamma": 0.20, "delta": 0.30},
                    "collective_discount": (_coll_discount if _h_is_collective else 1.0),
                    "tool_result_discount": _tool_result_discount,
                    "conflict_penalty": conflict_penalty,
                    "conflict_status": conflict_status,
                    "conflict_ids": conflict_ids,
                    "provenance_type": _derive_q_prov(_h_prov_raw),
                    "self_thread_bonus": _cont.self_thread_bonus,
                    "self_anchor_bonus": _cont.self_anchor_bonus,
                    "thread_window_bonus": _cont.thread_window_bonus,
                    "affect_match_bonus": _cont.affect_match_bonus,
                    "mood_drift_bonus": _cont.mood_drift_bonus,
                    "mood_spiral_penalty": _cont.mood_spiral_penalty,
                    "continuity_total_adjustment": _cont.total,
                    "srg_same_band_bonus": _srg_same_band,
                    "srg_crystal_bonus": _srg_crystal,
                    "srg_heartbeat_bonus": _srg_heartbeat,
                    "srg_total_multiplier": _srg_same_band * _srg_crystal * _srg_heartbeat,
                    # Diagnostic-only: names of the SRG multipliers that fired
                    # (non-neutral), in stable order. Derived purely from the
                    # already-computed multiplier values above; reads no raw R
                    # and affects no score / ranking / filter / write.
                    "srg_active_modifiers": [
                        _name for _name, _mult in (
                            ("same_band", _srg_same_band),
                            ("crystal", _srg_crystal),
                            ("heartbeat_a", _srg_heartbeat),
                        ) if _mult != 1.0
                    ],
                    "memory_plan_lane": _lane,
                    "lane_weight": _lane_w,
                    "lane_weight_applied": _lane_applied,
                }
            rescored.append(hh)

        rescored.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        rescored = rescored[:top_k]

        # FILTER-A (Commit γ): apply non_shareable exclusion at the single
        # chokepoint before any LLM-facing surface uses rescored. Surfaces
        # consuming this list below: continuity_debug summary, collective
        # discount loop, assemble_character_context(hits=rescored, ...),
        # and the returned "results" key. One filter, four protected surfaces.
        # See docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md and
        # torment_service/governance.py:filter_llm_facing.
        _filtered = filter_llm_facing(rescored, surface=SURFACE_LLM_CONTEXT)
        rescored = _filtered["results"]
        _filter_excluded = _filtered["excluded"]

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
            "excluded": _filter_excluded,  # FILTER-A: governance exclusions
            # S5 additive observability surface (Memory-to-Prompt v0.2 §4.2).
            # `filter_excluded` is the doctrinally-named alias the
            # `build_assembly_audit` helper reads; `excluded` (above) is the
            # historical name preserved for backward-compat. Both carry the
            # same list. Future v0.2.x cleanup may pick one canonical name.
            # `_core_hits_in_count` and `_authority_guard_rejected` are
            # underscore-prefixed per the internal-observability convention:
            # consumers should not rely on them for behavior. The latter is
            # always 0 in normal operation because the H4d authority guard
            # at governance.py is fail-loud (any wrapper rejection raises
            # before reaching this return path); the key is present so a
            # future revision can propagate a non-fail-loud count if needed.
            "filter_excluded": _filter_excluded,
            "_core_hits_in_count": len(rescored) + len(_filter_excluded),
            "_authority_guard_rejected": 0,
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
        fb_path = _safe_child(_agent_dir(self.data_dir, workspace_id, agent_id), "feedback_events.jsonl")
        _fb_dir = os.path.realpath(os.path.dirname(fb_path))
        if not _fb_dir.startswith(os.sep) and not os.path.isabs(_fb_dir):
            raise ValueError(f"Feedback dir not absolute: {_fb_dir!r}")
        os.makedirs(_fb_dir, exist_ok=True)
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


    def reinforce(
        self,
        workspace_id: str,
        agent_id: str,
        retrieved_ids: List[int],
        used_successfully: List[int],
    ) -> Dict[str, Any]:
        """Per-memory reinforcement writer (reinforce contract v2.4.x).

        Increments ``reinforcement_count`` on each eid in *used_successfully*
        that exists as a **private-scope** memory for this agent.  Each eid is
        processed at most once per call (deduped).  Shared/collective eids are
        governed skips with reason codes visible in the return envelope.

        Returns a dict with:
          - ``ok``: True
          - ``_reinforce_result_code``: ``"reinforced"`` if at least one eid
            moved, ``"no_op"`` otherwise.  Consumed by the Spine envelope.
          - ``reinforced_eids``: list of eids that were actually incremented
          - ``skipped``: list of ``{"eid": int, "reason": str}`` for eids that
            were not incremented (missing, out-of-scope, shared, etc.)
        """
        ak = self._agent_key(workspace_id, agent_id)
        g = self.private_graphs.get(ak)

        reinforced_eids: List[int] = []
        skipped: List[Dict[str, Any]] = []

        # Dedupe: process each eid at most once per call (Plan-D2).
        seen: set = set()
        for eid in used_successfully:
            eid = int(eid)
            if eid in seen:
                continue
            seen.add(eid)

            # Must exist in private graph
            if g is None or eid not in g.entities:
                skipped.append({"eid": eid, "reason": "not_found_in_private_graph"})
                continue

            ent = g.entities[eid]
            payload = ent.payload or {}

            # Plan-D7: private-scope only; shared/collective are governed skips.
            scope = str(payload.get("scope", "private"))
            if scope != "private":
                skipped.append({"eid": eid, "reason": f"scope_skip:{scope}"})
                continue

            # Increment reinforcement_count (monotonic, Plan-D1 + D4).
            old_count = int(payload.get("reinforcement_count", 0))
            g.update_payload(eid, {
                "reinforcement_count": old_count + 1,
            })
            reinforced_eids.append(eid)

        # Plan-D5: "reinforced" if at least one eid moved; "no_op" otherwise.
        result_code = "reinforced" if reinforced_eids else "no_op"

        return {
            "ok": True,
            "_reinforce_result_code": result_code,
            "reinforced_eids": reinforced_eids,
            "skipped": skipped,
        }


    # -----------------------------------------------------------------
    # Block A — baton lifecycle API
    # (docs/BLOCK_A_DESIGN.md §6.2 / §6.3)
    # -----------------------------------------------------------------

    def _baton_private_graph_view(
        self,
        workspace_id: str,
        agent_id: str,
    ) -> Tuple[Optional[MemoryGraph], bool]:
        """Return the cached private graph or a transient persisted view.

        Baton lifecycle operations are explicit and agent-private.  A cold
        Fabric process must therefore be able to inspect an existing private
        graph without hydrating the agent runtime or retaining a graph cache
        entry.  The boolean reports whether the caller must close the view.
        """
        ak = self._agent_key(workspace_id, agent_id)
        graph = self.private_graphs.get(ak)
        if graph is not None:
            return graph, False

        private_dir = _safe_child(
            _agent_dir(self.data_dir, workspace_id, agent_id), "private"
        )
        if not os.path.isdir(private_dir):
            return None, False

        try:
            return MemoryGraph(
                data_dir=private_dir,
                embedder=self.kernel.embedder,
            ), True
        except Exception as e:
            self._log.debug(
                "Baton private-graph read skipped for workspace_id=%s "
                "agent_id=%s: %s",
                _safe_log_value(workspace_id),
                _safe_log_value(agent_id),
                _safe_log_value(e),
            )
            return None, False

    def list_active_batons(
        self,
        workspace_id: str,
        agent_id: str,
        owner: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List active baton entries for an agent.

        Block A (docs/BLOCK_A_DESIGN.md §6.2). The explicit baton-aware
        retrieval path — baton is NOT a MemoryPlan lane. This method is
        the honest interface for lifecycle-aware baton lookup.

        Filter semantics:
            - agent-scoped (private only — baton is never shared)
            - active only (baton_lifecycle.status == "active")
            - optional owner filter ("user" | "next_ai" | "system")
            - sorted by created_ts ascending (oldest first — aging bias)
            - limit capped at 200 server-side

        Returns:
            {
                "ok": True,
                "result_code": "listed" | "no_active",
                "batons": [
                    {"eid": int, "summary": str, "baton_lifecycle": {...},
                     "created_ts": int, "provenance": {...}},
                    ...
                ],
            }
        """
        # Cap the server-side limit to prevent runaway large responses.
        limit = max(1, min(int(limit), 200))

        batons: List[Dict[str, Any]] = []
        g, transient = self._baton_private_graph_view(workspace_id, agent_id)
        try:
            if g is not None:
                for eid, ent in g.entities.items():
                    payload = ent.payload or {}
                    if not isinstance(payload, dict):
                        continue
                    if payload.get("memory_class") != "baton":
                        continue
                    lifecycle = payload.get("baton_lifecycle")
                    if not isinstance(lifecycle, dict):
                        continue
                    if lifecycle.get("status") != "active":
                        continue
                    if owner is not None and lifecycle.get("owner") != owner:
                        continue
                    batons.append({
                        "eid": int(eid),
                        "summary": payload.get("summary", ""),
                        "baton_lifecycle": dict(lifecycle),
                        "created_ts": int(payload.get("created_ts", 0) or 0),
                        "provenance": payload.get("provenance"),
                    })
        finally:
            if transient and g is not None:
                g.close()

        # Sort oldest first (aging bias — oldest batons surface first).
        batons.sort(key=lambda b: b.get("created_ts", 0))
        if len(batons) > limit:
            batons = batons[:limit]

        return {
            "ok": True,
            "result_code": "listed" if batons else "no_active",
            "batons": batons,
        }

    def resolve_baton(
        self,
        workspace_id: str,
        agent_id: str,
        eid: int,
        outcome: str,
        resolver: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark a baton as consumed. Does NOT delete or auto-promote.

        Block A (docs/BLOCK_A_DESIGN.md §6.3). Soft-consume semantics:
            - payload["baton_lifecycle"]["status"] = "consumed"
            - payload["baton_lifecycle"]["consumed_at"] = unix_ts
            - payload["baton_lifecycle"]["consumed_by"] = resolver or agent_id
            - payload["baton_lifecycle"]["consumed_outcome"] = outcome
            - A BatonEvent(kind="consumed") is appended to the ledger
              (audit trail; payload remains the source of truth).

        The memory entry is NEVER deleted. Original content + provenance
        preserved. Resolution NEVER creates a new core entry in a single
        call — promoting baton content to durable is a separate, explicit
        ingest with parent_eids pointing back to the baton.

        Idempotent: resolving an already-consumed baton is a no-op
        (result_code="already_consumed", no state change, no duplicate
        ledger entry).

        Returns:
            {
                "ok": True,
                "result_code": "resolved" | "already_consumed"
                              | "not_found" | "not_a_baton"
                              | "invalid_lifecycle",
                "eid": int,
                "outcome": str,
            }
        """
        eid = int(eid)
        g, transient = self._baton_private_graph_view(workspace_id, agent_id)
        try:
            # Not-found: no private graph or eid absent.
            if g is None or eid not in g.entities:
                return {"ok": True, "result_code": "not_found",
                        "eid": eid, "outcome": outcome}

            ent = g.entities[eid]
            payload = ent.payload or {}

            # Not-a-baton: present but wrong memory_class.
            if not isinstance(payload, dict) or payload.get("memory_class") != "baton":
                return {"ok": True, "result_code": "not_a_baton",
                        "eid": eid, "outcome": outcome}

            lifecycle = payload.get("baton_lifecycle")
            if not isinstance(lifecycle, dict):
                return {"ok": True, "result_code": "invalid_lifecycle",
                        "eid": eid, "outcome": outcome}
            # Already-consumed: no-op (idempotent). No ledger re-entry.
            if lifecycle.get("status") == "consumed":
                return {"ok": True, "result_code": "already_consumed",
                        "eid": eid, "outcome": outcome}

            # Soft-consume: update lifecycle fields in place. memory_class
            # does NOT change (resolution is lifecycle, not reclassification).
            lifecycle = dict(lifecycle)
            now_ts = int(time.time())
            consumed_by = resolver or agent_id
            owner_at_consume = lifecycle.get("owner")
            lifecycle["status"] = "consumed"
            lifecycle["consumed_at"] = now_ts
            lifecycle["consumed_by"] = consumed_by
            lifecycle["consumed_outcome"] = outcome
            g.update_payload(eid, {"baton_lifecycle": lifecycle})

            # Append to the audit ledger. Payload is source of truth;
            # ledger is audit trail. Errors here are swallowed — a ledger
            # write failure must not roll back the payload state change,
            # because the ledger is derivable from payload events but the
            # payload is not derivable from the ledger alone.
            try:
                from .baton_ledger import BatonLedger
                ledger = BatonLedger(
                    data_dir=self.data_dir,
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                )
                event = ledger.build_consumed_event(
                    eid=eid,
                    outcome=outcome,
                    resolver=consumed_by,
                    owner=owner_at_consume,
                )
                ledger.add_event(event)
            except Exception as e:
                self._log.debug(
                    "baton ledger write failed for eid=%s: %s", eid, e
                )

            return {"ok": True, "result_code": "resolved",
                    "eid": eid, "outcome": outcome}
        finally:
            if transient and g is not None:
                g.close()

    # -----------------------------------------------------------------
    # Block B — reference memory API
    # (docs/BLOCK_B_DESIGN.md §6.2, §6.3)
    # -----------------------------------------------------------------
    #
    # Reference memory is per-workspace whole-object storage, separate
    # from ArchiveStore (which chunks) and from core/baton substrate
    # (which is kernel-governed). Loading is intentional, sustained,
    # reasoning-oriented — NOT cosine retrieval.
    #
    # Two state surfaces managed here:
    #   - self.reference_stores[workspace_id]: ReferenceStore per workspace
    #   - self.reference_active_loads[agent_key]: {load_id: ActiveLoad}
    #     in-memory per-agent state for active loads
    #
    # Carry-forward caution (ratified): ReferenceEntry identity is
    # durable; ActiveLoad is lifecycle state on top. Load/unload events
    # go to the ReferenceLoadLedger (audit); ActiveLoad is the current-
    # state source of truth.

    def _get_reference_store(self, workspace_id: str):
        """Lazily create the per-workspace ReferenceStore."""
        if not hasattr(self, "reference_stores"):
            self.reference_stores = {}
        if workspace_id not in self.reference_stores:
            from .reference_memory import ReferenceStore
            self.reference_stores[workspace_id] = ReferenceStore(
                data_dir=self.data_dir,
                workspace_id=workspace_id,
            )
        return self.reference_stores[workspace_id]

    def _get_active_loads_map(self, workspace_id: str, agent_id: str):
        """Lazily create the per-agent active-loads in-memory dict."""
        if not hasattr(self, "reference_active_loads"):
            self.reference_active_loads = {}
        ak = self._agent_key(workspace_id, agent_id)
        if ak not in self.reference_active_loads:
            self.reference_active_loads[ak] = {}
        return self.reference_active_loads[ak]

    def _get_reference_load_ledger(self, workspace_id: str, agent_id: str):
        from .reference_load_ledger import ReferenceLoadLedger
        return ReferenceLoadLedger(
            data_dir=self.data_dir,
            workspace_id=workspace_id,
            agent_id=agent_id,
        )

    def ingest_reference(
        self,
        workspace_id: str,
        title: str,
        body: str,
        source_link: str,
        source_kind: str,
        metadata: Optional[Dict[str, Any]] = None,
        step: int = 0,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingest a reference object (Block B §6.2).

        Source linkage is REQUIRED (AC-1.1). Both fields must be
        truthy; either missing → rejected without writing.

        Returns:
            {"ok": True, "result_code": "ingested", "ref_id": str}
            or on missing source linkage:
            {"ok": False, "result_code": "missing_source_linkage",
             "ref_id": ""}
        """
        # AC-1.1 — source_link + source_kind both required
        if not source_link or not source_kind:
            return {
                "ok": False,
                "result_code": "missing_source_linkage",
                "ref_id": "",
            }

        from .reference_memory import VALID_SOURCE_KINDS
        # Leave candidate-shaped values to ReferenceStore's pre-side-effect
        # type guard, which is the established refusal boundary for them.
        if (not isinstance(source_kind, CandidateShapedValue)
                and source_kind not in VALID_SOURCE_KINDS):
            return {
                "ok": False,
                "result_code": "unsupported_source_kind",
                "ref_id": "",
            }

        # Make sure the workspace exists (for consistency with other methods)
        self.get_workspace(workspace_id)

        from .provenance_v1 import ProvenanceV1
        prov = ProvenanceV1.for_reference_ingest(
            step=step, session_id=session_id,
        ).to_dict()

        store = self._get_reference_store(workspace_id)
        entry = store.ingest(
            title=title,
            body=body,
            source_link=source_link,
            source_kind=source_kind,
            provenance=prov,
            metadata=metadata,
        )
        return {
            "ok": True,
            "result_code": "ingested",
            "ref_id": entry.ref_id,
        }

    def load_reference(
        self,
        workspace_id: str,
        agent_id: str,
        ref_id: str,
        scope_tag: str,
    ) -> Dict[str, Any]:
        """Load a reference object into the agent's active context
        (Block B §6.3).

        Returns the whole body (AC-1.2) and computes staleness on load.
        Idempotent at the call level in the sense of "repeated load
        calls each produce a new load_id" (design decision — each
        load is its own lifecycle event).

        Envelope:
            {"ok": True,
             "result_code": "loaded" | "not_found" | "not_a_reference",
             "load_id": str,
             "ref_id": str,
             "title": str,
             "body": str,
             "stale": bool,
             "loaded_at_ts": int}
        """
        # Workspace existence is assumed; fetch store (lazy-creates if
        # the workspace has no prior reference-memory state)
        self.get_workspace(workspace_id)
        store = self._get_reference_store(workspace_id)

        entry = store.get(ref_id)
        if entry is None:
            return {
                "ok": True,
                "result_code": "not_found",
                "ref_id": ref_id,
            }

        # Staleness = source hash at load time vs stored source_hash.
        # For v0.1, the ReferenceStore's compute_source_hash uses a
        # per-kind handler defaulting to the body-hash fallback
        # (conservative stale=False when the source can't be re-read).
        current_hash = store.compute_source_hash(
            source_link=entry.source_link,
            source_kind=entry.source_kind,
            body=entry.body,
        )
        stale = (current_hash != entry.source_hash)

        # Create a new ActiveLoad — note that load_id is a fresh uuid,
        # structurally separate from ref_id. Loadedness is not identity.
        load_id = f"load_{uuid.uuid4().hex[:16]}"
        loaded_ts = int(time.time())
        from .reference_memory import ActiveLoad
        active = ActiveLoad(
            load_id=load_id,
            ref_id=ref_id,
            workspace_id=workspace_id,
            agent_id=agent_id,
            scope_tag=scope_tag,
            loaded_at_ts=loaded_ts,
            stale_at_load=stale,
            status="active",
        )
        loads_map = self._get_active_loads_map(workspace_id, agent_id)
        loads_map[load_id] = active

        # Record the event in the ledger (audit only — ActiveLoad
        # remains the state source of truth).
        try:
            ledger = self._get_reference_load_ledger(workspace_id, agent_id)
            ledger.add_event(ledger.build_loaded_event(
                ref_id=ref_id,
                load_id=load_id,
                scope_tag=scope_tag,
                stale_at_load=stale,
            ))
        except Exception as e:
            self._log.debug(
                "reference load ledger write failed for load_id=%s: %s",
                load_id, e,
            )

        return {
            "ok": True,
            "result_code": "loaded",
            "load_id": load_id,
            "ref_id": ref_id,
            "title": entry.title,
            "body": entry.body,
            "stale": stale,
            "loaded_at_ts": loaded_ts,
        }

    def unload_reference(
        self,
        workspace_id: str,
        agent_id: str,
        load_id: str,
    ) -> Dict[str, Any]:
        """Mark an active load as unloaded. Soft-operation; idempotent
        on already-unloaded loads.

        Envelope:
            {"ok": True,
             "result_code": "unloaded" | "not_found" | "already_unloaded",
             "load_id": str}
        """
        loads_map = self._get_active_loads_map(workspace_id, agent_id)
        active = loads_map.get(load_id)
        if active is None:
            return {
                "ok": True,
                "result_code": "not_found",
                "load_id": load_id,
            }
        if active.status != "active":
            return {
                "ok": True,
                "result_code": "already_unloaded",
                "load_id": load_id,
            }

        now_ts = int(time.time())
        active.status = "unloaded"
        active.unloaded_at_ts = now_ts

        try:
            ledger = self._get_reference_load_ledger(workspace_id, agent_id)
            ledger.add_event(ledger.build_unloaded_event(
                ref_id=active.ref_id,
                load_id=load_id,
                scope_tag=active.scope_tag,
            ))
        except Exception as e:
            self._log.debug(
                "reference unload ledger write failed for load_id=%s: %s",
                load_id, e,
            )

        return {
            "ok": True,
            "result_code": "unloaded",
            "load_id": load_id,
        }

    def list_active_loads(
        self,
        workspace_id: str,
        agent_id: str,
        scope_tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List this agent's currently-active reference loads.

        Optional scope_tag filter. Sorted by loaded_at_ts ascending
        (oldest first).

        Envelope:
            {"ok": True,
             "result_code": "listed" | "no_active",
             "loads": [
                 {"load_id": str, "ref_id": str, "scope_tag": str,
                  "loaded_at_ts": int, "stale_at_load": bool,
                  "body": str, "title": str},
                 ...
             ]}

        Note: includes body + title so callers (e.g., a future
        retrieval_assembler integration per §8.2) can use the loaded
        state directly without a second fetch against ReferenceStore.
        """
        loads_map = self._get_active_loads_map(workspace_id, agent_id)
        store = self._get_reference_store(workspace_id)

        loads: List[Dict[str, Any]] = []
        for load_id, active in loads_map.items():
            if active.status != "active":
                continue
            if scope_tag is not None and active.scope_tag != scope_tag:
                continue
            entry = store.get(active.ref_id)
            # If the entry was deleted under the load (edge case),
            # skip this load rather than returning None-shaped data.
            if entry is None:
                continue
            loads.append({
                "load_id": active.load_id,
                "ref_id": active.ref_id,
                "scope_tag": active.scope_tag,
                "loaded_at_ts": active.loaded_at_ts,
                "stale_at_load": active.stale_at_load,
                "title": entry.title,
                "body": entry.body,
            })

        loads.sort(key=lambda l: l.get("loaded_at_ts", 0))

        return {
            "ok": True,
            "result_code": "listed" if loads else "no_active",
            "loads": loads,
        }


    # -----------------------------------------------------------------
    # Block B — environment memory API
    # (docs/BLOCK_B_DESIGN.md §7)
    # -----------------------------------------------------------------
    #
    # Environment memory is per-workspace operational-facts storage
    # with STRICT evidence-class discipline (R+5). Never flows through
    # retrieval_assembler (R+4). Consult is return-only (D.3).
    #
    # v0.1 ships with VALID_INFERENCE_RULES empty — any inferred write
    # is rejected at the fabric gate. Adding a rule requires explicit
    # future ratification per docs/BLOCK_B_DESIGN.md §11 Q2.

    def _get_environment_store(self, workspace_id: str):
        """Lazily create the per-workspace EnvironmentStore."""
        if not hasattr(self, "environment_stores"):
            self.environment_stores = {}
        if workspace_id not in self.environment_stores:
            from .environment_memory import EnvironmentStore
            self.environment_stores[workspace_id] = EnvironmentStore(
                data_dir=self.data_dir,
                workspace_id=workspace_id,
            )
        return self.environment_stores[workspace_id]

    def _get_environment_event_ledger(self, workspace_id: str):
        from .environment_event_ledger import EnvironmentEventLedger
        return EnvironmentEventLedger(
            data_dir=self.data_dir,
            workspace_id=workspace_id,
        )

    def write_environment(
        self,
        workspace_id: str,
        target_runtime: str,
        scope_tag: str,
        key: str,
        value: Any,
        evidence_class: str,
        ownership: str,
        observation_source: Optional[str] = None,
        inference_rule: Optional[str] = None,
        asserted_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        step: int = 0,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Write an environment fact (Block B §7.2).

        Validates evidence class first (R+5 gate) before building
        provenance. Missing or invalid evidence class → rejected with
        a specific result_code and no entry created.

        Envelope:
            {"ok": True, "result_code": "written", "env_id": str}
            or on reject:
            {"ok": False,
             "result_code": "missing_evidence_class"
                           | "missing_evidence_field"
                           | "inferred_requires_rule"
                           | "unknown_inference_rule",
             "env_id": ""}
        """
        # Evidence-class validation FIRST. EnvironmentStore.validate_evidence
        # is the single gate; rejecting here avoids constructing provenance
        # for writes we'll refuse.
        from .environment_memory import EnvironmentStore
        ok, code = EnvironmentStore.validate_evidence(
            evidence_class=evidence_class,
            ownership=ownership,
            observation_source=observation_source,
            inference_rule=inference_rule,
            asserted_by=asserted_by,
        )
        if not ok:
            return {"ok": False, "result_code": code, "env_id": ""}

        # Build provenance via the evidence-class-matched factory.
        # Each factory populates exactly the field that corresponds to
        # its class; no cross-class field pollution.
        from .provenance_v1 import ProvenanceV1
        if evidence_class == "user_asserted":
            prov = ProvenanceV1.for_environment_user_asserted(
                asserted_by=asserted_by,
                step=step, session_id=session_id,
            ).to_dict()
        elif evidence_class == "observed":
            prov = ProvenanceV1.for_environment_observed(
                observation_source=observation_source,
                step=step, session_id=session_id,
            ).to_dict()
        else:  # inferred — already validated that rule is in VALID_INFERENCE_RULES
            prov = ProvenanceV1.for_environment_inferred(
                inference_rule=inference_rule,
                step=step, session_id=session_id,
            ).to_dict()

        # Make sure workspace exists, then delegate to store
        self.get_workspace(workspace_id)
        store = self._get_environment_store(workspace_id)
        result = store.write(
            target_runtime=target_runtime,
            scope_tag=scope_tag,
            key=key,
            value=value,
            evidence_class=evidence_class,
            ownership=ownership,
            provenance=prov,
            observation_source=observation_source,
            inference_rule=inference_rule,
            asserted_by=asserted_by,
            metadata=metadata,
        )

        # Record ledger event on success (audit only; store is source of truth)
        if result.get("ok") and result.get("env_id"):
            try:
                ledger = self._get_environment_event_ledger(workspace_id)
                ledger.add_event(ledger.build_written_event(
                    env_id=result["env_id"],
                    evidence_class=evidence_class,
                ))
            except Exception as e:
                self._log.debug(
                    "environment event ledger write failed "
                    "for env_id=%s: %s",
                    result.get("env_id"), e,
                )
        return result

    def consult_environment(
        self,
        workspace_id: str,
        operation: str,
        scope: str,
        *,
        relevance_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Consult environment memory (Block B §7.3).

        RETURN-ONLY per D.3. This method does NOT call any policy
        gate, does NOT inject into prompt context, does NOT modify
        state. Callers decide what to do with the facts.

        Returns a serialized EnvironmentConsultResult:
            {"ok": True,
             "result_code": "consulted" | "no_relevant_facts",
             "operation": str,
             "scope": str,
             "facts": [
                 {"key": str, "value": Any, "evidence_class": str,
                  "last_observed": int, "inferred": bool},
                 ...
             ]}

        The `facts` list contains EnvironmentFactView dicts — a VIEW
        over relevant entries, structurally distinct from the stored
        EnvironmentEntry (no env_id, no workspace_id, no full
        provenance dict). Carry-forward caution: entry identity is
        separate from consult result shape.
        """
        self.get_workspace(workspace_id)
        store = self._get_environment_store(workspace_id)
        result = store.consult(
            operation=operation,
            scope=scope,
            relevance_fields=relevance_fields,
        )

        # Log the consult for audit (no state change)
        try:
            ledger = self._get_environment_event_ledger(workspace_id)
            ledger.add_event(ledger.build_consulted_event(
                operation=operation,
                scope=scope,
            ))
        except Exception as e:
            self._log.debug(
                "environment consult ledger write failed: %s", e,
            )
        return result.to_dict()

    def probe_environment_on_fail(
        self,
        workspace_id: str,
        target_runtime: str,
        scope_tag: str,
        key: str,
        value: Any,
        observation_source: str,
        *,
        ownership: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
        step: int = 0,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """System-initiated probe write after an action failure
        (Block B §7.4).

        ALWAYS writes with evidence_class="observed" — never accepts
        "inferred" from this path (AC-2.5). The observation_source
        is REQUIRED and names the probe that produced the observation.
        This wrapper cannot be used to smuggle inferred content into
        observed provenance.

        Per D.3, this method is callable but not wired: no automatic
        trigger from action_policy or the runner in v0.1. External
        code (tests, HTTP endpoints, later runtime-doctrine
        increments) invokes it explicitly.
        """
        if not observation_source:
            return {
                "ok": False,
                "result_code": "missing_evidence_field",
                "env_id": "",
            }
        # Delegate to write_environment with forced evidence_class.
        # The write path records a "written" ledger event; the probe-
        # specific "probed" event kind exists for callers that want to
        # log separately, not for this wrapper's default path.
        return self.write_environment(
            workspace_id=workspace_id,
            target_runtime=target_runtime,
            scope_tag=scope_tag,
            key=key,
            value=value,
            evidence_class="observed",
            ownership=ownership,
            observation_source=observation_source,
            metadata=metadata,
            step=step,
            session_id=session_id,
        )


    # ==================================================================
    # Block C — Closure lifecycle (docs/BLOCK_C_DESIGN.md §6)
    # ==================================================================
    #
    # Four public methods + two administrative reads + two private
    # helpers for the per-workspace ClosureStore and ClosureLedger.
    #
    # STRUCTURAL SEPARATION from writeback (§7 + handoff note 4):
    #   - These methods NEVER call self.ingest or fabric.ingest.
    #   - They NEVER use ProvenanceV1.for_cognition_writeback.
    #   - They NEVER write to the archivist log or reuse any writeback
    #     audit path.
    #   - Closure storage uses ClosureStore (closures.jsonl) +
    #     ClosureLedger (closure_events.jsonl); both live under
    #     <ws>/closure_memory/ with no overlap on any other store's files.
    #   - Closure commit/revision use WRITE_CLOSURE_COMMIT; ratification
    #     uses WRITE_DIRECT_INGEST (lifecycle event only, not content).
    #
    # RAW lifecycle evidence is literal Ledger append history. Trusted
    # operational lifecycle is a named, non-mutating reconciliation of that
    # evidence with ClosureStore payload versions.

    def _get_closure_store(self, workspace_id: str):
        """Lazily create the per-workspace ClosureStore."""
        if not hasattr(self, "closure_stores"):
            self.closure_stores = {}
        if workspace_id not in self.closure_stores:
            from .closure_memory import ClosureStore
            self.closure_stores[workspace_id] = ClosureStore(
                data_dir=self.data_dir,
                workspace_id=workspace_id,
            )
        return self.closure_stores[workspace_id]

    def _get_closure_ledger(self, workspace_id: str):
        """Build a per-workspace ClosureLedger.

        Not cached — the ledger reads the JSONL on every call, so a new
        instance carries no state (matching BatonLedger / ReferenceLoadLedger
        patterns where each call gets a fresh reader).
        """
        from .closure_ledger import ClosureLedger
        return ClosureLedger(
            data_dir=self.data_dir,
            workspace_id=workspace_id,
        )

    def _reconcile_closure_current(self, workspace_id: str, closure_id: str):
        """Return the non-mutating trusted-current Closure projection.

        Store and ledger APIs intentionally retain their raw forensic meaning.
        Lifecycle mutation gates use this helper so unmatched rows cannot enter
        a trusted ancestry chain or advance a lifecycle claim.
        """
        from .closure_reconciliation import reconcile_closure_history

        store = self._get_closure_store(workspace_id)
        entries = []
        for known_closure_id in store.list_closures():
            entries.extend(store.list_versions(known_closure_id))
        events = self._get_closure_ledger(workspace_id).list_events(
            closure_id=closure_id,
            limit=None,
        )
        return reconcile_closure_history(
            entries,
            events,
            workspace_id=workspace_id,
            closure_id=closure_id,
        )

    # ---- Closure scope / honesty read helpers ----

    def _closure_private_graph_views(
        self,
        workspace_id: str,
    ) -> Tuple[List[Tuple[str, MemoryGraph]], List[MemoryGraph]]:
        """Read persisted private graphs without hydrating agent runtime state."""
        agent_ids: set = set()
        prefix = f"{workspace_id}/"
        for agent_key in self.private_graphs:
            if agent_key.startswith(prefix):
                agent_id = agent_key[len(prefix):]
                if agent_id:
                    agent_ids.add(agent_id)

        agents_root = _safe_child(_ws_root(self.data_dir, workspace_id), "agents")
        if os.path.isdir(agents_root):
            for agent_id in os.listdir(agents_root):
                try:
                    _validate_path_component(agent_id, "agent_id")
                except HTTPException:
                    continue
                private_dir = _safe_child(
                    _agent_dir(self.data_dir, workspace_id, agent_id), "private"
                )
                if os.path.isdir(private_dir):
                    agent_ids.add(agent_id)

        views: List[Tuple[str, MemoryGraph]] = []
        transient: List[MemoryGraph] = []
        for agent_id in sorted(agent_ids):
            graph = self.private_graphs.get(self._agent_key(workspace_id, agent_id))
            if graph is None:
                private_dir = _safe_child(
                    _agent_dir(self.data_dir, workspace_id, agent_id), "private"
                )
                try:
                    graph = MemoryGraph(
                        data_dir=private_dir,
                        embedder=self.kernel.embedder,
                    )
                except Exception as e:
                    self._log.debug(
                        "Closure private-graph read skipped for workspace_id=%s "
                        "agent_id=%s: %s",
                        _safe_log_value(workspace_id),
                        _safe_log_value(agent_id),
                        _safe_log_value(e),
                    )
                    continue
                transient.append(graph)
            views.append((agent_id, graph))
        return views, transient

    def _closure_workspace_eids(self, workspace_id: str) -> set:
        """Return workspace-local EID candidates for closure scope validation.

        EIDs are local to individual graphs.  The established v0.1 closure
        schema stores only ``List[int]``, so this write-boundary guard proves
        local existence without inventing an agent/domain qualifier.
        """
        known_eids: set = set()
        workspace = self.get_workspace(workspace_id)
        for graph in workspace.shared_graphs.values():
            known_eids.update(int(eid) for eid in graph.entities)

        views, transient = self._closure_private_graph_views(workspace_id)
        try:
            for _agent_id, graph in views:
                known_eids.update(int(eid) for eid in graph.entities)
        finally:
            for graph in transient:
                graph.close()
        return known_eids

    def _normalize_and_validate_closure_scope(
        self,
        workspace_id: str,
        scope: List[int],
    ) -> Tuple[List[int], List[Any]]:
        """Normalize scope EIDs in first-seen order and report invalid values."""
        normalized: List[int] = []
        invalid: List[Any] = []
        seen: set = set()
        for raw_eid in scope:
            try:
                eid = int(raw_eid)
            except (TypeError, ValueError):
                invalid.append(raw_eid)
                continue
            if eid not in seen:
                seen.add(eid)
                normalized.append(eid)
        if invalid:
            return normalized, invalid

        known_eids = self._closure_workspace_eids(workspace_id)
        return normalized, [eid for eid in normalized if eid not in known_eids]

    def _closure_active_batons(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Read active persisted batons for Closure honesty without cache reliance."""
        active: List[Dict[str, Any]] = []
        views, transient = self._closure_private_graph_views(workspace_id)
        try:
            for agent_id, graph in views:
                try:
                    for eid, entry in graph.entities.items():
                        payload = entry.payload or {}
                        if not isinstance(payload, dict):
                            continue
                        if payload.get("memory_class") != "baton":
                            continue
                        lifecycle = payload.get("baton_lifecycle") or {}
                        if not isinstance(lifecycle, dict):
                            continue
                        if lifecycle.get("status") != "active":
                            continue
                        active.append({
                            "eid": int(eid),
                            "summary": str(payload.get("summary", "")),
                            "agent_id": agent_id,
                        })
                except Exception as e:
                    self._log.debug(
                        "Closure baton scan skipped damaged graph for workspace_id=%s "
                        "agent_id=%s: %s",
                        _safe_log_value(workspace_id),
                        _safe_log_value(agent_id),
                        _safe_log_value(e),
                    )
        finally:
            for graph in transient:
                graph.close()
        active.sort(key=lambda baton: (baton["agent_id"], baton["eid"]))
        return active

    # ---- Required-field validation helper ----

    @staticmethod
    def _closure_missing_required(
        arc_name: str,
        arc_kind: str,
        scope: Any,
        what_it_was: str,
        what_worked: str,
        what_surprised: str,
        what_to_carry_forward: str,
        deferred_or_open_items: Any,
    ) -> Optional[str]:
        """Return the first missing required field name, or None if all
        present. Matches the validation list in §6.1:

            - arc_name / arc_kind / what_it_was / what_worked /
              what_surprised / what_to_carry_forward — non-empty strings
            - scope — non-empty list
            - deferred_or_open_items — must be a list (empty OK; None
              or absent rejected per R+10)
        """
        # String fields
        for field_name, value in (
            ("arc_name", arc_name),
            ("arc_kind", arc_kind),
            ("what_it_was", what_it_was),
            ("what_worked", what_worked),
            ("what_surprised", what_surprised),
            ("what_to_carry_forward", what_to_carry_forward),
        ):
            if not isinstance(value, str) or not value.strip():
                return field_name
        # Scope: must be non-empty list of ints
        if not isinstance(scope, list) or len(scope) == 0:
            return "scope"
        # deferred_or_open_items: REQUIRED (R+10) — empty list OK,
        # None / missing rejected. Check list-ness explicitly.
        if not isinstance(deferred_or_open_items, list):
            return "deferred_or_open_items"
        return None

    # ---- 6.1 — propose_closure ----

    def propose_closure(
        self,
        workspace_id: str,
        arc_name: str,
        arc_kind: str,
        scope: List[int],
        what_it_was: str,
        what_worked: str,
        what_surprised: str,
        what_to_carry_forward: str,
        deferred_or_open_items: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        step: int = 0,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a closure proposal (§6.1).

        Validates the §5.2 required fields. Writes a ClosureEntry at
        version 1. Appends a "proposed" event to the ledger. No
        ratification, no commit — those are explicit follow-on calls
        (R+7: no automatic enactment).
        """
        missing = self._closure_missing_required(
            arc_name, arc_kind, scope,
            what_it_was, what_worked, what_surprised, what_to_carry_forward,
            deferred_or_open_items,
        )
        if missing is not None:
            # Distinct code for absent-None deferred vs. other missing
            # fields per AC-1 test contract (both acceptable).
            code = (
                "missing_deferred_or_open_items"
                if missing == "deferred_or_open_items"
                   and deferred_or_open_items is None
                else "missing_required_field"
            )
            return {
                "ok": False,
                "result_code": code,
                "missing_field": missing,
                "closure_id": "",
                "version_id": "",
            }

        normalized_scope, invalid_eids = self._normalize_and_validate_closure_scope(
            workspace_id, scope,
        )
        if invalid_eids:
            return {
                "ok": False,
                "result_code": "invalid_scope",
                "invalid_eids": invalid_eids,
                "closure_id": "",
                "version_id": "",
            }

        store = self._get_closure_store(workspace_id)
        ledger = self._get_closure_ledger(workspace_id)

        # Build the entry. Authorship provenance for the initial
        # proposal uses for_closure_commit as the authorship record on
        # the entry — the entry carries its commit-style authorship
        # provenance from day one (ratifier is filled in at ratify/
        # commit time; this field records "who drafted this version").
        #
        # Note: a proposal is NOT yet committed; we still use
        # for_closure_commit for authorship record because ClosureEntry
        # is the SAME class across the lifecycle (one-class watch-item).
        # The lifecycle-STATE distinction is carried by the ledger.
        from .provenance_v1 import ProvenanceV1
        closure_id = store.new_closure_id()
        version_id = store.new_version_id()

        authorship_provenance = ProvenanceV1.for_closure_commit(
            arc_name=arc_name,
            ratifier="(proposer-draft)",   # filled only once ratified/committed
            step=step,
            session_id=session_id,
            notes="initial proposal draft",
        ).to_dict()

        from .closure_memory import ClosureEntry
        entry = ClosureEntry(
            closure_id=closure_id,
            version_id=version_id,
            workspace_id=workspace_id,
            arc_name=arc_name,
            arc_kind=arc_kind,
            scope=normalized_scope,
            what_it_was=what_it_was,
            what_worked=what_worked,
            what_surprised=what_surprised,
            what_to_carry_forward=what_to_carry_forward,
            deferred_or_open_items=list(deferred_or_open_items),
            authorship_provenance=authorship_provenance,
            version_history=[],
            created_ts=int(time.time()),
            parent_version_id=None,
            metadata=dict(metadata or {}),
        )
        store.add_version(entry)

        # Ledger event — the proposed event's provenance is an
        # authorship record too, not a lifecycle flag. Lifecycle
        # stage is derived from the kind field, not this provenance.
        proposed_prov = ProvenanceV1.for_closure_commit(
            arc_name=arc_name,
            ratifier="(proposer-draft)",
            step=step,
            session_id=session_id,
        ).to_dict()
        ledger.add_event(ledger.build_proposed_event(
            closure_id=closure_id,
            version_id=version_id,
            provenance=proposed_prov,
        ))

        return {
            "ok": True,
            "result_code": "proposed",
            "closure_id": closure_id,
            "version_id": version_id,
        }

    # ---- 6.2 — ratify_closure ----

    def ratify_closure(
        self,
        workspace_id: str,
        closure_id: str,
        ratifier: str,
        notes: Optional[str] = None,
        step: int = 0,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record ratification of a closure proposal (§6.2).

        Appends a "ratified" event to the ledger. Does NOT commit —
        commit_closure is the separate explicit step (R+7 / AC-2).

        R+9: empty ratifier is rejected. Model assistance in drafting
        is legitimate; model-authored ratifications (ratifier = "" or
        unset) are not.
        """
        if not isinstance(ratifier, str) or not ratifier.strip():
            return {
                "ok": False,
                "result_code": "empty_ratifier",
                "closure_id": closure_id or "",
            }

        ledger = self._get_closure_ledger(workspace_id)
        reconciled = self._reconcile_closure_current(workspace_id, closure_id)
        entry = reconciled.current_entry
        if entry is None:
            return {
                "ok": False,
                "result_code": "not_found",
                "closure_id": closure_id,
            }

        # If already committed, ratifying again is a no-op error — the
        # lifecycle state "committed" is terminal for the ratification
        # gate. Revisions flow through revise_closure instead.
        if reconciled.current_state == "committed":
            return {
                "ok": False,
                "result_code": "already_committed",
                "closure_id": closure_id,
            }

        from .provenance_v1 import ProvenanceV1
        prov = ProvenanceV1.for_closure_ratification(
            arc_name=entry.arc_name,
            ratifier=ratifier,
            step=step,
            session_id=session_id,
            notes=notes,
        ).to_dict()
        ledger.add_event(ledger.build_ratified_event(
            closure_id=closure_id,
            ratifier=ratifier,
            provenance=prov,
            notes=notes,
        ))

        return {
            "ok": True,
            "result_code": "ratified",
            "closure_id": closure_id,
        }

    # ---- 6.3 — commit_closure ----
    #
    # Phase 3: ratification-gate + already-committed guard. The
    # open-items honesty check lands in Phase 4 per BLOCK_C_DESIGN §8
    # (detect_open_items_mismatch + commit-time integration).

    def commit_closure(
        self,
        workspace_id: str,
        closure_id: str,
        ratifier: str,
        step: int = 0,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Commit a ratified closure — the transition to durable (§6.3).

        Requires a prior "ratified" event per AC-2 (ratification is
        structural). R+9: empty ratifier rejected.

        Phase 3 wires the ratification-gate. The open-items honesty
        check (AC-4) lands in Phase 4 with the
        `detect_open_items_mismatch` helper — until then,
        `open_items_mismatch` is a documented result code but is not
        emitted by this method.
        """
        if not isinstance(ratifier, str) or not ratifier.strip():
            return {
                "ok": False,
                "result_code": "empty_ratifier",
                "closure_id": closure_id or "",
            }

        ledger = self._get_closure_ledger(workspace_id)
        reconciled = self._reconcile_closure_current(workspace_id, closure_id)
        entry = reconciled.current_entry
        if entry is None:
            return {
                "ok": False,
                "result_code": "not_found",
                "closure_id": closure_id,
            }

        if reconciled.current_state == "committed":
            return {
                "ok": False,
                "result_code": "already_committed",
                "closure_id": closure_id,
            }

        # AC-2: the closure-bound ratification must be part of the trusted
        # chain, and commit may only advance a trusted ratified/revised state.
        if (
            not reconciled.has_ratification
            or reconciled.current_state not in {"ratified", "revised"}
        ):
            return {
                "ok": False,
                "result_code": "not_ratified",
                "closure_id": closure_id,
            }

        # AC-4: open-items honesty mismatch detection (Phase 4, §8.1-§8.2).
        # Pure helper over the current entry's scope + deferred_or_open_items
        # against v0.1 signals (open conflicts + active batons filtered to
        # scope). Fires only when known-unresolved is non-empty AND
        # declared_open_items is empty — anti-false-finality, not
        # full-truth-check (§8.4).
        from .closure_memory import detect_open_items_mismatch
        check = detect_open_items_mismatch(
            fabric=self,
            workspace_id=workspace_id,
            scope=entry.scope,
            declared_open_items=entry.deferred_or_open_items,
        )
        if check.get("unreadable_conflict_domains"):
            return {
                "ok": False,
                "result_code": "conflict_state_unreadable",
                "closure_id": closure_id,
                "unreadable": {
                    "unreadable_conflict_domains": check["unreadable_conflict_domains"],
                    "unresolved_conflicts": check["unresolved_conflicts"],
                    "unresolved_batons": check["unresolved_batons"],
                },
            }
        if check.get("mismatch"):
            return {
                "ok": False,
                "result_code": "open_items_mismatch",
                "closure_id": closure_id,
                "unresolved": {
                    "unresolved_conflicts": check["unresolved_conflicts"],
                    "unresolved_batons": check["unresolved_batons"],
                    "reason": check["reason"],
                },
            }

        from .provenance_v1 import ProvenanceV1
        prov = ProvenanceV1.for_closure_commit(
            arc_name=entry.arc_name,
            ratifier=ratifier,
            step=step,
            session_id=session_id,
        ).to_dict()
        ledger.add_event(ledger.build_committed_event(
            closure_id=closure_id,
            version_id=entry.version_id,
            ratifier=ratifier,
            provenance=prov,
        ))

        return {
            "ok": True,
            "result_code": "committed",
            "closure_id": closure_id,
            "version_id": entry.version_id,
        }

    # ---- 6.4 — revise_closure ----

    def revise_closure(
        self,
        workspace_id: str,
        closure_id: str,
        revised_fields: Dict[str, Any],
        ratifier: str,
        step: int = 0,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Produce a new version of a committed closure (§6.4).

        R+8: creates a new version_id alongside the prior. The original
        stays readable. version_history grows — never replaced.

        Only committed closures can be revised (you revise an
        unratified proposal by creating a new proposal, not by
        revising).

        Phase 3 wires the machinery. The open-items honesty check on
        revisions that would reset `deferred_or_open_items` to []
        lands in Phase 4.
        """
        if not isinstance(ratifier, str) or not ratifier.strip():
            return {
                "ok": False,
                "result_code": "missing_ratifier",
                "closure_id": closure_id or "",
            }
        if not isinstance(revised_fields, dict):
            return {
                "ok": False,
                "result_code": "invalid_revised_fields",
                "closure_id": closure_id or "",
            }

        store = self._get_closure_store(workspace_id)
        ledger = self._get_closure_ledger(workspace_id)

        reconciled = self._reconcile_closure_current(workspace_id, closure_id)
        latest = reconciled.current_entry
        if latest is None:
            return {
                "ok": False,
                "result_code": "not_found",
                "closure_id": closure_id,
            }

        # The trusted chain must have been committed at least once.  A
        # revision remains revisable after valid revised events, while a raw
        # orphan payload cannot become the parent of a new trusted version.
        if not reconciled.has_committed:
            return {
                "ok": False,
                "result_code": "not_committed",
                "closure_id": closure_id,
            }

        # Build the new version. Start from the latest entry, apply
        # revised_fields to a mutable copy, assign new version_id,
        # record parent_version_id linking to the prior version's id,
        # and append a version_history entry.
        from .provenance_v1 import ProvenanceV1
        from .closure_memory import ClosureEntry

        new_version_id = store.new_version_id()
        parent_version_id = latest.version_id

        # Fields that ARE revisable. Structural fields (closure_id,
        # workspace_id, version_id, created_ts, parent_version_id,
        # authorship_provenance, version_history) are NOT revisable
        # via this path — they are either immutable or computed here.
        REVISABLE_FIELDS = {
            "arc_name", "arc_kind", "scope",
            "what_it_was", "what_worked", "what_surprised",
            "what_to_carry_forward", "deferred_or_open_items",
            "metadata",
        }

        def _field(name: str) -> Any:
            return (
                revised_fields[name]
                if name in revised_fields and name in REVISABLE_FIELDS
                else getattr(latest, name)
            )

        # Emit a fresh authorship_provenance for this revision.
        revision_authorship = ProvenanceV1.for_closure_revision(
            arc_name=_field("arc_name"),
            ratifier=ratifier,
            parent_closure_id=closure_id,
            step=step,
            session_id=session_id,
        ).to_dict()

        # Preserve prior version_history and append this revision's
        # linkage record. R+8: history grows, never replaces.
        new_history = list(latest.version_history)
        new_history.append({
            "version_id": new_version_id,
            "parent_version_id": parent_version_id,
            "ratifier": ratifier,
            "ts": int(time.time()),
        })

        # AC-4 (revision edition, per §8.2): run the open-items honesty
        # mismatch check against the REVISED scope + deferred. A revision
        # that would reset deferred_or_open_items to [] while the scope
        # still has open conflicts / active batons is rejected with the
        # same code commit_closure uses.
        from .closure_memory import detect_open_items_mismatch
        if "scope" in revised_fields and "scope" in REVISABLE_FIELDS:
            if not isinstance(_field("scope"), list) or not _field("scope"):
                return {
                    "ok": False,
                    "result_code": "missing_required_field",
                    "missing_field": "scope",
                    "closure_id": closure_id,
                }
            prospective_scope, invalid_eids = self._normalize_and_validate_closure_scope(
                workspace_id, _field("scope"),
            )
            if invalid_eids:
                return {
                    "ok": False,
                    "result_code": "invalid_scope",
                    "invalid_eids": invalid_eids,
                    "closure_id": closure_id,
                }
        else:
            prospective_scope = list(int(e) for e in _field("scope"))
        prospective_deferred = list(_field("deferred_or_open_items"))
        check = detect_open_items_mismatch(
            fabric=self,
            workspace_id=workspace_id,
            scope=prospective_scope,
            declared_open_items=prospective_deferred,
        )
        if check.get("unreadable_conflict_domains"):
            return {
                "ok": False,
                "result_code": "conflict_state_unreadable",
                "closure_id": closure_id,
                "unreadable": {
                    "unreadable_conflict_domains": check["unreadable_conflict_domains"],
                    "unresolved_conflicts": check["unresolved_conflicts"],
                    "unresolved_batons": check["unresolved_batons"],
                },
            }
        if check.get("mismatch"):
            return {
                "ok": False,
                "result_code": "open_items_mismatch",
                "closure_id": closure_id,
                "unresolved": {
                    "unresolved_conflicts": check["unresolved_conflicts"],
                    "unresolved_batons": check["unresolved_batons"],
                    "reason": check["reason"],
                },
            }

        new_entry = ClosureEntry(
            closure_id=closure_id,
            version_id=new_version_id,
            workspace_id=workspace_id,
            arc_name=_field("arc_name"),
            arc_kind=_field("arc_kind"),
            scope=prospective_scope,
            what_it_was=_field("what_it_was"),
            what_worked=_field("what_worked"),
            what_surprised=_field("what_surprised"),
            what_to_carry_forward=_field("what_to_carry_forward"),
            deferred_or_open_items=prospective_deferred,
            authorship_provenance=revision_authorship,
            version_history=new_history,
            created_ts=int(time.time()),
            parent_version_id=parent_version_id,
            metadata=dict(_field("metadata")),
        )
        store.add_version(new_entry)

        # Append revised event to the ledger. Its provenance is the
        # same revision authorship dict — origin/authorship, not
        # lifecycle state.
        ledger.add_event(ledger.build_revised_event(
            closure_id=closure_id,
            version_id=new_version_id,
            ratifier=ratifier,
            provenance=revision_authorship,
        ))

        return {
            "ok": True,
            "result_code": "revised",
            "closure_id": closure_id,
            "version_id": new_version_id,
            "parent_version_id": parent_version_id,
        }

    # ---- Administrative reads (§6.5 tail) ----

    def get_closure(
        self,
        workspace_id: str,
        closure_id: str,
        version_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return one closure version as a dict (or None if missing).

        This is the RAW / FORENSIC admin surface. If `version_id` is None,
        it returns the physically latest Store version even when that version
        is unmatched by lifecycle evidence. Use ``get_closure_current`` for
        trusted operational state. Neither surface is wired into retrieval.
        """
        store = self._get_closure_store(workspace_id)
        from dataclasses import asdict
        if version_id is None:
            entry = store.get_latest_version(closure_id)
        else:
            entry = store.get_version(closure_id, version_id)
        if entry is None:
            return None
        return asdict(entry)

    def get_closure_current(
        self,
        workspace_id: str,
        closure_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the TRUSTED / OPERATIONAL current Closure projection.

        Unlike :meth:`get_closure`, this validates the raw Store and Ledger
        relationship without modifying either. ``diagnostics`` makes an
        otherwise healthy chain distinguishable from one reconciled around
        orphan evidence.
        """
        reconciled = self._reconcile_closure_current(workspace_id, closure_id)
        if not (
            reconciled.valid_versions
            or reconciled.orphan_versions
            or reconciled.valid_events
            or reconciled.orphan_events
        ):
            return None
        current = reconciled.as_current_dict()
        # A Store-only or event-only history has no trusted entry, but the
        # named current-read still identifies the raw closure being examined.
        current["closure_id"] = closure_id
        current["workspace_id"] = workspace_id
        return current

    def list_closures(self, workspace_id: str) -> List[str]:
        """Return the list of closure_ids in the workspace's store."""
        return list(self._get_closure_store(workspace_id).list_closures())

    # ==================================================================

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

        if chosen_domain not in ws.proposals:
            available = sorted(ws.proposals.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Domain '{chosen_domain}' not found in workspace '{workspace_id}'. "
                       f"Available domains: {available}",
            )

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
            from non-collective-derived proposals
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
        # Production proposal orchestration remains unconditionally legacy.
        # The native implementation is available only through the explicit
        # private qualification seam below.
        return self._process_proposals_impl(
            workspace_id=workspace_id,
            domain_id=domain_id,
            max_to_process=max_to_process,
            sim_threshold=sim_threshold,
            min_distinct_agents=min_distinct_agents,
            step=step,
            storage=LegacyAuthorizedSharedProposalStorage(
                shared_graph=ws.shared_graphs[domain_id],
                motif_registry=ws.motif_regs[domain_id],
                geometry=LegacyMotifGeometryAdapter(ws.motif_regs),
            ),
        )

    def _process_proposals_with_qualified_native_storage(
        self,
        workspace_id: str,
        domain_id: str,
        *,
        storage: NativeAuthorizedSharedProposalStorage,
        max_to_process: int = 200,
        sim_threshold: float = 0.90,
        min_distinct_agents: int = 0,
        step: Optional[int] = None,
        _side_effect_trace: Optional[List[str]] = None,
        _test_fail_after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Qualification-only native counterpart of :meth:`process_proposals`.

        Callers must construct and pass a fully-qualified native storage port;
        this method neither discovers a native core nor selects a backend.
        """
        if not isinstance(storage, NativeAuthorizedSharedProposalStorage):
            raise ValueError("native proposal qualification requires explicit native storage")
        return self._process_proposals_with_receipt_recovery(
            workspace_id=workspace_id,
            domain_id=domain_id,
            max_to_process=max_to_process,
            sim_threshold=sim_threshold,
            min_distinct_agents=min_distinct_agents,
            step=step,
            storage=storage,
            _side_effect_trace=_side_effect_trace,
            _test_fail_after=_test_fail_after,
        )

    def _process_proposals_with_receipt_recovery(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        max_to_process: int,
        sim_threshold: float,
        min_distinct_agents: int,
        step: Optional[int],
        storage: NativeAuthorizedSharedProposalStorage,
        _side_effect_trace: Optional[List[str]] = None,
        _test_fail_after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Resume frozen qualified proposals before considering fresh pending work.

        This private method is intentionally separate from the legacy public
        workflow.  It never re-runs TORMENT authority for a receipt: it merely
        verifies immutable source facts and reconciles the already-authorized
        effects in their recorded order.
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
            min_distinct_agents = int(
                ws.domain_policies.get(domain_id, {}).get("shared_min_distinct_agents", 2)
            )
        process_call = {
            "max_to_process": int(max_to_process),
            "sim_threshold": float(sim_threshold),
            "min_distinct_agents": int(min_distinct_agents),
            "step": None if step is None else int(step),
        }

        recovered: list[dict[str, Any]] = []
        for receipt in storage.receipts.list_incomplete_quorum(
            workspace_id=workspace_id, domain_id=domain_id,
        ):
            recovered.append(
                self._recover_native_quorum_receipt(
                    ws=ws,
                    registry=reg,
                    storage=storage,
                    receipt=receipt,
                    _side_effect_trace=_side_effect_trace,
                    _test_fail_after=_test_fail_after,
                )
            )

        pending = reg.list_pending(limit=max_to_process)
        if not pending:
            if recovered:
                result = self._combine_native_quorum_results(recovered)
                self._proposal_trace(_side_effect_trace, "RETURN")
                return result
            # A fully completed qualified call is safely replayable by its
            # frozen process knobs.  No ordinary/public path uses this lookup.
            completed = storage.receipts.completed_quorum_for_call(
                workspace_id=workspace_id, domain_id=domain_id, process_call=process_call,
            )
            if completed:
                for receipt, _result in completed:
                    verify_receipt_sources(receipt, reg)
                result = self._combine_native_quorum_results([item[1] for item in completed])
                self._proposal_trace(_side_effect_trace, "RETURN")
                return result
            return {"ok": True, "processed": 0, "approved_groups": 0, "approved": 0}

        P = pending
        E = [np.asarray(p.embedding, dtype=np.float32) for p in P]
        used: set[str] = set()
        fresh: list[dict[str, Any]] = []
        for i, pi in enumerate(P):
            if pi.proposal_id in used:
                continue
            group = [i]
            used.add(pi.proposal_id)
            agents = {pi.agent_id} if pi.mtype != "collective_echo" else set()
            for j in range(i + 1, len(P)):
                pj = P[j]
                if pj.proposal_id in used:
                    continue
                if cos_sim(E[i], E[j]) >= sim_threshold:
                    group.append(j)
                    used.add(pj.proposal_id)
                    if pj.mtype != "collective_echo":
                        agents.add(pj.agent_id)
            if len(agents) < min_distinct_agents:
                continue

            authority_candidates = [k for k in group if P[k].mtype != "collective_echo"]
            if not authority_candidates:
                raise RuntimeError("quorum-qualified proposal group has no authority contributor")
            rep_idx = max(authority_candidates, key=lambda k: (P[k].strength, P[k].confidence))
            representative = P[rep_idx]
            participating = tuple(P[k] for k in group)
            support_agents = tuple(sorted(agents))
            embedding_provider = str(getattr(self.kernel.embedder, "provider", ""))
            embedding_model = str(getattr(self.kernel.embedder, "model", ""))
            self._proposal_trace(_side_effect_trace, "AUTHORITY_DECIDED")
            witness = storage.pre_conflict_read(E[rep_idx])
            self._proposal_trace(_side_effect_trace, "PRE_CONFLICT_READ")
            policy = self._receipt_motif_policy(ws.domain_policies.get(domain_id, {}))
            receipt = storage.receipts.prepare_quorum(
                authorization=AuthorizedSharedProposalQuorum(
                    workspace_id=workspace_id,
                    domain_id=domain_id,
                    representative=representative,
                    participating_proposals=participating,
                    support_agents=support_agents,
                    embedding_provider=embedding_provider,
                    embedding_model=embedding_model,
                ),
                authority_proposal_ids=tuple(P[k].proposal_id for k in authority_candidates),
                sim_threshold=sim_threshold,
                min_distinct_agents=min_distinct_agents,
                step=step,
                native_storage_key=native_quorum_operation_key(workspace_id, domain_id, participating),
                pre_conflict_witness=witness,
                policy=policy,
                process_call=process_call,
            )
            fresh.append(
                self._run_native_quorum_receipt(
                    ws=ws,
                    registry=reg,
                    storage=storage,
                    receipt=receipt,
                    proposals=participating,
                    representative=representative,
                    _side_effect_trace=_side_effect_trace,
                    _test_fail_after=_test_fail_after,
                )
            )

        result = self._combine_native_quorum_results(recovered + fresh)
        # Preserve the public result-envelope meaning for a fresh scan: it
        # counts every considered pending proposal, even those left pending.
        if fresh:
            result["processed"] = len(P)
        self._proposal_trace(_side_effect_trace, "RETURN")
        return result

    def _recover_native_quorum_receipt(
        self,
        *,
        ws: Workspace,
        registry: ProposalRegistry,
        storage: NativeAuthorizedSharedProposalStorage,
        receipt: AuthorizedProposalReceipt,
        _side_effect_trace: Optional[List[str]],
        _test_fail_after: Optional[str],
    ) -> dict[str, Any]:
        if receipt.kind != "QUORUM":
            raise AuthorizedProposalReceiptError("non-quorum receipt reached quorum recovery")
        proposals = verify_receipt_sources(receipt, registry)
        by_id = {proposal.proposal_id: proposal for proposal in proposals}
        representative = by_id.get(receipt.representative_id)
        if representative is None:
            raise AuthorizedProposalReceiptError("receipt representative is missing")
        if not set(receipt.payload["authority_proposal_ids"]).issubset(by_id):
            raise AuthorizedProposalReceiptError("receipt authority source facts differ")
        return self._run_native_quorum_receipt(
            ws=ws,
            registry=registry,
            storage=storage,
            receipt=receipt,
            proposals=proposals,
            representative=representative,
            _side_effect_trace=_side_effect_trace,
            _test_fail_after=_test_fail_after,
        )

    def _run_native_quorum_receipt(
        self,
        *,
        ws: Workspace,
        registry: ProposalRegistry,
        storage: NativeAuthorizedSharedProposalStorage,
        receipt: AuthorizedProposalReceipt,
        proposals: tuple[ShareProposal, ...],
        representative: ShareProposal,
        _side_effect_trace: Optional[List[str]],
        _test_fail_after: Optional[str],
    ) -> dict[str, Any]:
        completed = storage.receipts.completion(receipt)
        if completed is not None:
            return completed
        materialized = storage.materialize_quorum(
            workspace_id=receipt.workspace_id,
            domain_id=receipt.domain_id,
            representative=representative,
            participating_proposals=proposals,
            support_agents=receipt.authority_agents,
            embedding_provider=receipt.embedding_provider,
            embedding_model=receipt.embedding_model,
            step=receipt.payload.get("step"),
            receipt=receipt,
        )
        eid = int(materialized.eid)
        self._proposal_trace(_side_effect_trace, "STORAGE_COMMITTED")
        self._proposal_fault(_test_fail_after, "storage_commit")

        self._reconcile_native_receipt_conflict(
            ws=ws, receipt=receipt, representative=representative, eid=eid,
        )
        storage.receipts.mark_stage(receipt, "CONFLICT")
        self._proposal_trace(_side_effect_trace, "CONFLICT_SIDE_EFFECT")
        self._proposal_fault(_test_fail_after, "conflict")

        storage.ensure_motif_current(
            embedding=np.asarray(representative.embedding, dtype=np.float32), eid=eid, summary=representative.summary,
        )
        if not storage.receipts.has_stage(receipt, "MOTIF_MAINTENANCE"):
            try:
                if materialized.created_new:
                    storage.update_motif_maintenance(receipt.policy)
            except Exception as exc:
                self._log.debug(
                    "group proposal motif entropy update failed for domain=%s: %s",
                    _safe_log_value(receipt.domain_id), _safe_log_value(exc),
                )
            storage.receipts.mark_stage(receipt, "MOTIF_MAINTENANCE")
        self._proposal_trace(_side_effect_trace, "MOTIF_MAINTENANCE")
        if bool(receipt.policy.get("auto_merge_motifs", False)):
            self._proposal_trace(_side_effect_trace, "AUTO_MERGE_IF_ANY")
        self._proposal_fault(_test_fail_after, "motif_maintenance")

        self._reconcile_native_receipt_marks(
            registry=registry,
            receipt=receipt,
            note=f"approved via group (agents={len(receipt.authority_agents)})",
            first_mark_fault="proposal_mark_after_first",
            _test_fail_after=_test_fail_after,
        )
        storage.receipts.mark_stage(receipt, "PROPOSAL_MARK")
        self._proposal_trace(_side_effect_trace, "PROPOSAL_MARK")
        self._proposal_fault(_test_fail_after, "proposal_mark")

        if not storage.receipts.has_stage(receipt, "BRIDGE_SUGGEST"):
            ws.bridges.suggest(storage.geometry, sim_threshold=0.86, max_new=10)
            storage.receipts.mark_stage(receipt, "BRIDGE_SUGGEST")
        self._proposal_trace(_side_effect_trace, "BRIDGE_SUGGEST")
        self._proposal_fault(_test_fail_after, "bridge")
        if not storage.receipts.has_stage(receipt, "DOMAIN_SUGGEST"):
            self._maybe_suggest_domain(ws, domain_id=receipt.domain_id, geometry=storage.geometry)
            storage.receipts.mark_stage(receipt, "DOMAIN_SUGGEST")
        self._proposal_trace(_side_effect_trace, "DOMAIN_SUGGEST")
        result = {
            "ok": True,
            "processed": len(proposals),
            "approved_groups": 1,
            "approved": len(proposals),
            "created_shared_eids": [eid],
        }
        result = storage.receipts.complete(receipt, result)
        # The fault boundary is deliberately after completion.  A lost reply
        # therefore has immutable evidence for the exact outward result.
        self._proposal_fault(_test_fail_after, "domain_suggestion")
        return result

    @staticmethod
    def _receipt_motif_policy(policy: Dict[str, Any]) -> dict[str, Any]:
        return {
            "motif_entropy_target_n": int(policy.get("motif_entropy_target_n", 24)),
            "motif_entropy_high": float(policy.get("motif_entropy_high", 0.72)),
            "motif_merge_similarity": float(policy.get("motif_merge_similarity", 0.93)),
            "motif_merge_max_suggestions": int(policy.get("motif_merge_max_suggestions", 20)),
            "auto_merge_motifs": bool(policy.get("auto_merge_motifs", False)),
            "auto_merge_entropy_trigger": float(policy.get("auto_merge_entropy_trigger", 0.80)),
        }

    @staticmethod
    def _combine_native_quorum_results(results: list[dict[str, Any]]) -> dict[str, Any]:
        if not results:
            return {"ok": True, "processed": 0, "approved_groups": 0, "approved": 0, "created_shared_eids": []}
        if len(results) == 1:
            return dict(results[0])
        return {
            "ok": True,
            "processed": sum(int(item["processed"]) for item in results),
            "approved_groups": sum(int(item["approved_groups"]) for item in results),
            "approved": sum(int(item["approved"]) for item in results),
            "created_shared_eids": [eid for item in results for eid in item["created_shared_eids"]],
        }

    def _reconcile_native_receipt_conflict(
        self,
        *,
        ws: Workspace,
        receipt: AuthorizedProposalReceipt,
        representative: ShareProposal,
        eid: int,
    ) -> None:
        expected: tuple[int, float, float, str] | None = None
        for witness in receipt.witness:
            old_eid = int(witness.get("eid", 0))
            if old_eid <= 0:
                continue
            sim = float(witness.get("score", 0.0))
            is_conflict, score, reason = _detect_canon_conflict(
                representative.summary, str(witness.get("summary", "")), sim,
            )
            if is_conflict:
                expected = (old_eid, sim, float(score), str(reason or "heuristic"))
                break
        if expected is None:
            return
        old_eid, sim, score, reason = expected
        matches = [
            conflict for conflict in ws.conflicts[receipt.domain_id].apply_events().values()
            if conflict.eid_a == old_eid and conflict.eid_b == eid
            and conflict.sim == sim and conflict.conflict_score == score
            and conflict.reason == reason and conflict.origin_scope == "shared"
            and conflict.origin_domain_id == receipt.domain_id and conflict.origin_agent_id is None
        ]
        if len(matches) > 1:
            raise AuthorizedProposalReceiptError("receipt conflict reconciliation is ambiguous")
        if not matches:
            ws.conflicts[receipt.domain_id].add(
                eid_a=old_eid, eid_b=eid, sim=sim, conflict_score=score, reason=reason,
                origin_scope="shared", origin_agent_id=None, origin_domain_id=receipt.domain_id,
            )

    def _reconcile_native_receipt_marks(
        self,
        *,
        registry: ProposalRegistry,
        receipt: AuthorizedProposalReceipt,
        note: str,
        first_mark_fault: str | None,
        _test_fail_after: Optional[str],
    ) -> None:
        latest = registry.apply_events()
        marked = 0
        for proposal_id in receipt.source_proposal_ids:
            proposal = latest.get(proposal_id)
            if proposal is None:
                raise AuthorizedProposalReceiptError("receipt proposal is missing during mark reconciliation")
            if proposal.status == "pending":
                registry.mark(proposal_id, status="approved", note=note)
                marked += 1
                if marked == 1 and first_mark_fault is not None:
                    self._proposal_fault(_test_fail_after, first_mark_fault)
            elif proposal.status == "approved":
                continue
            elif proposal.status == "rejected":
                raise AuthorizedProposalReceiptError("receipt proposal was rejected before recovery")
            else:
                raise AuthorizedProposalReceiptError("receipt proposal has an unknown effective status")

    def _process_proposals_impl(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        max_to_process: int,
        sim_threshold: float,
        min_distinct_agents: int,
        step: Optional[int],
        storage: AuthorizedSharedProposalStorage,
        _side_effect_trace: Optional[List[str]] = None,
        _test_fail_after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run unchanged TORMENT authority over one authorized storage port."""
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
            # Collective-derived proposals remain in the group but are not
            # independent agent evidence for quorum.
            agents = {pi.agent_id} if pi.mtype != "collective_echo" else set()
            for j in range(i+1, len(P)):
                pj = P[j]
                if pj.proposal_id in used:
                    continue
                s = cos_sim(E[i], E[j])
                if s >= sim_threshold:
                    group.append(j)
                    used.add(pj.proposal_id)
                    if pj.mtype != "collective_echo":
                        agents.add(pj.agent_id)

            if len(agents) >= min_distinct_agents:
                approved_groups += 1
                # Canonical content must come from a proposal that contributed
                # independent-agent authority to this quorum-qualified group.
                authority_candidates = [
                    k for k in group if P[k].mtype != "collective_echo"
                ]
                if not authority_candidates:
                    raise RuntimeError(
                        "quorum-qualified proposal group has no authority contributor"
                    )
                # Choose the strongest authority-contributing representative.
                rep_idx = max(
                    authority_candidates,
                    key=lambda k: (P[k].strength, P[k].confidence),
                )
                rep = P[rep_idx]
                emb = E[rep_idx]

                emb_provider = str(getattr(self.kernel.embedder, "provider", ""))
                emb_model = str(getattr(self.kernel.embedder, "model", ""))
                support_agents = tuple(sorted(agents))
                participating = tuple(P[k] for k in group)
                self._proposal_trace(_side_effect_trace, "AUTHORITY_DECIDED")

                # Pre-scan uses the storage lane's exact vector read law.  On
                # legacy this is MemoryGraph; native qualification supplies
                # NativeMemoryVectorRuntime with the same top_k/canon filter.
                existing = storage.pre_conflict_read(emb)
                self._proposal_trace(_side_effect_trace, "PRE_CONFLICT_READ")

                materialized = storage.materialize_quorum(
                    workspace_id=workspace_id,
                    domain_id=domain_id,
                    representative=rep,
                    participating_proposals=participating,
                    support_agents=support_agents,
                    embedding_provider=emb_provider,
                    embedding_model=emb_model,
                    step=step,
                )
                eid = int(materialized.eid)
                created_shared_eids.append(eid)
                self._proposal_trace(_side_effect_trace, "STORAGE_COMMITTED")
                self._proposal_fault(_test_fail_after, "storage_commit")

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
                            origin_scope="shared",
                            origin_agent_id=None,
                            origin_domain_id=domain_id,
                        )
                        # one conflict per new node is enough for now
                        break
                self._proposal_trace(_side_effect_trace, "CONFLICT_SIDE_EFFECT")
                self._proposal_fault(_test_fail_after, "conflict")

                # Legacy attachment remains in this exact place.  Qualified
                # native storage has already made current motif truth and is
                # deliberately a no-op to avoid a second native attachment.
                storage.ensure_motif_current(embedding=emb, eid=eid, summary=rep.summary)

                # motif entropy + merge suggestions (domain)
                pol = ws.domain_policies.get(domain_id, {})
                try:
                    if materialized.created_new:
                        storage.update_motif_maintenance(pol)
                except Exception as e:
                    self._log.debug(
                        "group proposal motif entropy update failed for domain=%s: %s",
                        _safe_log_value(domain_id),
                        _safe_log_value(e),
                    )
                self._proposal_trace(_side_effect_trace, "MOTIF_MAINTENANCE")
                if bool(pol.get("auto_merge_motifs", False)):
                    self._proposal_trace(_side_effect_trace, "AUTO_MERGE_IF_ANY")
                self._proposal_fault(_test_fail_after, "motif_maintenance")

                # mark all proposals in group approved
                for k in group:
                    reg.mark(P[k].proposal_id, status="approved", note=f"approved via group (agents={len(agents)})")
                    approved += 1
                    if approved == 1:
                        self._proposal_fault(_test_fail_after, "proposal_mark_after_first")
                self._proposal_trace(_side_effect_trace, "PROPOSAL_MARK")
                self._proposal_fault(_test_fail_after, "proposal_mark")
            else:
                # Not enough agreement; leave pending (no event)
                pass

        # Refresh bridge suggestions after new shared nodes
        if created_shared_eids:
            ws.bridges.suggest(storage.geometry, sim_threshold=0.86, max_new=10)
            self._proposal_trace(_side_effect_trace, "BRIDGE_SUGGEST")
            self._proposal_fault(_test_fail_after, "bridge")

        # Domain suggestion heuristic: if we keep seeing strong motifs poorly aligned with any domain centroid.
        self._maybe_suggest_domain(ws, domain_id=domain_id, geometry=storage.geometry)
        self._proposal_trace(_side_effect_trace, "DOMAIN_SUGGEST")
        self._proposal_fault(_test_fail_after, "domain_suggestion")

        result = {
            "ok": True,
            "processed": len(P),
            "approved_groups": approved_groups,
            "approved": approved,
            "created_shared_eids": created_shared_eids,
        }
        self._proposal_trace(_side_effect_trace, "RETURN")
        return result

    

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
        _validate_path_component(workspace_id, "workspace_id")
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
        # Production operator decisions remain unconditionally legacy.
        return self._decide_proposal_impl(
            workspace_id=workspace_id,
            domain_id=domain_id,
            proposal_id=proposal_id,
            decision=decision,
            note=note,
            storage=LegacyAuthorizedSharedProposalStorage(
                shared_graph=ws.shared_graphs[domain_id],
                motif_registry=ws.motif_regs[domain_id],
                geometry=LegacyMotifGeometryAdapter(ws.motif_regs),
            ),
        )

    def _decide_proposal_with_qualified_native_storage(
        self,
        workspace_id: str,
        domain_id: str,
        proposal_id: str,
        decision: str,
        note: Optional[str] = None,
        *,
        storage: NativeAuthorizedSharedProposalStorage,
        _side_effect_trace: Optional[List[str]] = None,
        _test_fail_after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Qualification-only native counterpart of :meth:`decide_proposal`."""
        if not isinstance(storage, NativeAuthorizedSharedProposalStorage):
            raise ValueError("native proposal qualification requires explicit native storage")
        return self._decide_proposal_with_receipt_recovery(
            workspace_id=workspace_id,
            domain_id=domain_id,
            proposal_id=proposal_id,
            decision=decision,
            note=note,
            storage=storage,
            _side_effect_trace=_side_effect_trace,
            _test_fail_after=_test_fail_after,
        )

    def _decide_proposal_with_receipt_recovery(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        proposal_id: str,
        decision: str,
        note: Optional[str],
        storage: NativeAuthorizedSharedProposalStorage,
        _side_effect_trace: Optional[List[str]] = None,
        _test_fail_after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Private operator path with receipt recovery for approved decisions only."""
        ws = self.get_workspace(workspace_id)
        if domain_id not in ws.domains:
            raise ValueError("Unknown domain_id")
        registry = ws.proposals[domain_id]
        latest = registry.apply_events()
        proposal = latest.get(proposal_id)
        if proposal is None:
            raise ValueError("Unknown proposal_id")
        if decision not in ("approve", "reject"):
            raise ValueError("decision must be approve|reject")
        # Rejections deliberately retain the ordinary Fabric-only behavior;
        # an authorization recovery receipt never represents a rejection.
        if decision == "reject":
            registry.mark(proposal_id, status="rejected", note=note or "rejected manually")
            return {"ok": True, "decision": "rejected", "proposal_id": proposal_id}
        if proposal.mtype == "collective_echo":
            raise ValueError(
                "collective-derived proposals require the grouped "
                "independent-authority path"
            )

        native_key = native_operator_operation_key(workspace_id, domain_id, proposal)
        receipt = storage.receipts.get(
            workspace_id=workspace_id, domain_id=domain_id, native_storage_key=native_key,
        )
        if receipt is not None:
            if receipt.kind != "OPERATOR_APPROVE":
                raise AuthorizedProposalReceiptError("operator receipt kind differs")
            return self._recover_native_operator_receipt(
                ws=ws,
                registry=registry,
                storage=storage,
                receipt=receipt,
                note=note,
                _side_effect_trace=_side_effect_trace,
                _test_fail_after=_test_fail_after,
            )
        if proposal.status != "pending":
            raise AuthorizedProposalReceiptError(
                "approved operator proposal has no qualified recovery receipt"
            )

        embedding_provider = str(getattr(self.kernel.embedder, "provider", ""))
        embedding_model = str(getattr(self.kernel.embedder, "model", ""))
        self._proposal_trace(_side_effect_trace, "AUTHORITY_DECIDED")
        receipt = storage.receipts.prepare_operator(
            authorization=AuthorizedSharedProposalOperator(
                workspace_id=workspace_id,
                domain_id=domain_id,
                proposal=proposal,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
            ),
            native_storage_key=native_key,
            policy=self._receipt_motif_policy(ws.domain_policies.get(domain_id, {})),
        )
        return self._recover_native_operator_receipt(
            ws=ws,
            registry=registry,
            storage=storage,
            receipt=receipt,
            note=note,
            _side_effect_trace=_side_effect_trace,
            _test_fail_after=_test_fail_after,
        )

    def _recover_native_operator_receipt(
        self,
        *,
        ws: Workspace,
        registry: ProposalRegistry,
        storage: NativeAuthorizedSharedProposalStorage,
        receipt: AuthorizedProposalReceipt,
        note: Optional[str],
        _side_effect_trace: Optional[List[str]],
        _test_fail_after: Optional[str],
    ) -> Dict[str, Any]:
        if receipt.kind != "OPERATOR_APPROVE":
            raise AuthorizedProposalReceiptError("non-operator receipt reached operator recovery")
        proposals = verify_receipt_sources(receipt, registry)
        if len(proposals) != 1 or proposals[0].proposal_id != receipt.representative_id:
            raise AuthorizedProposalReceiptError("operator receipt source facts differ")
        completed = storage.receipts.completion(receipt)
        if completed is not None:
            self._proposal_trace(_side_effect_trace, "RETURN")
            return completed
        proposal = proposals[0]
        materialized = storage.materialize_operator(
            workspace_id=receipt.workspace_id,
            domain_id=receipt.domain_id,
            proposal=proposal,
            embedding_provider=receipt.embedding_provider,
            embedding_model=receipt.embedding_model,
            receipt=receipt,
        )
        eid = int(materialized.eid)
        self._proposal_trace(_side_effect_trace, "STORAGE_COMMITTED")
        self._proposal_fault(_test_fail_after, "operator_storage_commit")
        storage.ensure_motif_current(
            embedding=np.asarray(proposal.embedding, dtype=np.float32), eid=eid, summary=proposal.summary,
        )
        self._reconcile_native_receipt_marks(
            registry=registry,
            receipt=receipt,
            note=note or "approved manually",
            first_mark_fault=None,
            _test_fail_after=_test_fail_after,
        )
        storage.receipts.mark_stage(receipt, "PROPOSAL_MARK")
        self._proposal_trace(_side_effect_trace, "PROPOSAL_MARK")
        self._proposal_fault(_test_fail_after, "operator_proposal_mark")
        if not storage.receipts.has_stage(receipt, "BRIDGE_SUGGEST"):
            ws.bridges.suggest(storage.geometry, sim_threshold=0.86, max_new=5)
            storage.receipts.mark_stage(receipt, "BRIDGE_SUGGEST")
        self._proposal_trace(_side_effect_trace, "BRIDGE_SUGGEST")
        self._proposal_fault(_test_fail_after, "operator_bridge")
        if not storage.receipts.has_stage(receipt, "DOMAIN_SUGGEST"):
            self._maybe_suggest_domain(ws, domain_id=receipt.domain_id, geometry=storage.geometry)
            storage.receipts.mark_stage(receipt, "DOMAIN_SUGGEST")
        self._proposal_trace(_side_effect_trace, "DOMAIN_SUGGEST")
        result = storage.receipts.complete(
            receipt,
            {
                "ok": True,
                "decision": "approved",
                "proposal_id": proposal.proposal_id,
                "created_shared_eid": eid,
            },
        )
        self._proposal_fault(_test_fail_after, "operator_domain_suggestion")
        self._proposal_trace(_side_effect_trace, "RETURN")
        return result

    def _decide_proposal_impl(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        proposal_id: str,
        decision: str,
        note: Optional[str],
        storage: AuthorizedSharedProposalStorage,
        _side_effect_trace: Optional[List[str]] = None,
        _test_fail_after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run unchanged operator authority over one authorized storage port."""
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

        if p.mtype == "collective_echo":
            raise ValueError(
                "collective-derived proposals require the grouped "
                "independent-authority path"
            )

        emb = np.asarray(p.embedding, dtype=np.float32)
        emb_provider = str(getattr(self.kernel.embedder, "provider", ""))
        emb_model = str(getattr(self.kernel.embedder, "model", ""))
        self._proposal_trace(_side_effect_trace, "AUTHORITY_DECIDED")
        materialized = storage.materialize_operator(
            workspace_id=workspace_id,
            domain_id=domain_id,
            proposal=p,
            embedding_provider=emb_provider,
            embedding_model=emb_model,
        )
        eid = int(materialized.eid)
        self._proposal_trace(_side_effect_trace, "STORAGE_COMMITTED")
        self._proposal_fault(_test_fail_after, "operator_storage_commit")
        storage.ensure_motif_current(embedding=emb, eid=eid, summary=p.summary)
        reg.mark(proposal_id, status="approved", note=note or "approved manually")
        self._proposal_trace(_side_effect_trace, "PROPOSAL_MARK")
        self._proposal_fault(_test_fail_after, "operator_proposal_mark")
        ws.bridges.suggest(storage.geometry, sim_threshold=0.86, max_new=5)
        self._proposal_trace(_side_effect_trace, "BRIDGE_SUGGEST")
        self._proposal_fault(_test_fail_after, "operator_bridge")
        self._maybe_suggest_domain(ws, domain_id=domain_id, geometry=storage.geometry)
        self._proposal_trace(_side_effect_trace, "DOMAIN_SUGGEST")
        self._proposal_fault(_test_fail_after, "operator_domain_suggestion")
        result = {"ok": True, "decision": "approved", "proposal_id": proposal_id, "created_shared_eid": eid}
        self._proposal_trace(_side_effect_trace, "RETURN")
        return result


    @staticmethod
    def _proposal_trace(trace: Optional[List[str]], event: str) -> None:
        """Append a qualification-only observable side-effect boundary."""
        if trace is not None:
            trace.append(event)

    @staticmethod
    def _proposal_fault(requested_boundary: Optional[str], boundary: str) -> None:
        """Private fault seam used only to characterize cross-store retries."""
        if requested_boundary == boundary:
            raise RuntimeError(f"forced proposal orchestration failure after {boundary}")


    def _maybe_suggest_domain(
        self,
        ws: Workspace,
        domain_id: str,
        *,
        geometry: MotifGeometryPort | None = None,
    ) -> None:
        """Suggest new domains based on strong motifs that are poorly aligned with their current domain centroid."""
        _validate_path_component(domain_id, "domain_id")
        # The suggestion workflow remains Fabric-owned external JSON state.
        # Geometry is deliberately injected so a qualified native caller never
        # reads stale legacy motif JSON after a native motif mutation.
        geometry = geometry or LegacyMotifGeometryAdapter(ws.motif_regs)
        # Build domain centroid from motif centroids
        dom_centroids: Dict[str, np.ndarray] = {}
        for d in geometry.domain_ids():
            cs = [
                motif.centroid_np()
                for motif in geometry.list_motifs(d)
                if motif.centroid_np().size > 0
            ]
            if not cs:
                continue
            dom_centroids[d] = np.mean(np.stack(cs, axis=0), axis=0)

        dc = dom_centroids.get(domain_id)
        if dc is None:
            return

        suggestions = []
        for motif in geometry.list_motifs(domain_id):
            if float(motif.strength) < 0.75:
                continue
            c = motif.centroid_np()
            if c.size == 0:
                continue
            s = float(np.dot(c, dc) / ((np.linalg.norm(c)+1e-12)*(np.linalg.norm(dc)+1e-12)))
            if s < 0.35:
                label = motif.label or 'emergent'
                name = re.sub(r"[^a-z0-9_]+", "_", label.lower()).strip("_")
                if not name:
                    name = 'emergent'
                name = f"suggested_{name}"[:32]
                suggestions.append({
                    "domain_id": name,
                    "from_domain": domain_id,
                    "motif_id": motif.runtime_motif_id,
                    "motif_label": label,
                    "strength": float(motif.strength),
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


    def trace(self, workspace_id: str, agent_id: str, query_text: str, eids: List[int], domain_id: Optional[str] = None, memory_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Explain why specific memories scored the way they did for a query."""
        _validate_path_component(workspace_id, "workspace_id")
        _validate_path_component(agent_id, "agent_id")
        if domain_id:
            _validate_path_component(domain_id, "domain_id")
        ws = self.get_workspace(workspace_id)
        ak = self._agent_key(workspace_id, agent_id)
        self.create_agent(workspace_id, agent_id)
        qemb = self.kernel.embedder.embed(query_text)
        dom_scores = ws.router.rank_domains(qemb, top_k=2)
        domains = [d.domain_id for d in dom_scores]
        if domain_id:
            domains = [domain_id] + [d for d in domains if d != domain_id]
            domains = domains[:2]

        motif_centroids: Dict[_QueryMotifIdentity, np.ndarray] = {}
        for d in domains:
            for m in ws.motif_regs.get(d, MotifRegistry(self.data_dir, workspace_id, d)).motifs.values():
                motif_centroids[_QueryMotifIdentity(
                    workspace_id=str(workspace_id),
                    domain_id=str(d),
                    motif_id=str(m.motif_id),
                )] = m.centroid_np()

        # Build qualified conflict map for traced domains (parity with query()).
        _trace_conflict_map = _build_conflict_map(ws, workspace_id, domains)

        # --- Memory-plan lane weights (parity with query()) ---
        _trace_mp = memory_plan or {}
        _trace_mp_weights = _trace_mp.get("weight_by_lane", {})

        # --- Continuity context (parity with query()) ---
        # 1. Canonical step from agent kernel state
        _trace_canonical_step: int = -1
        try:
            _trace_agent_state = self.agent_states.get(ak)
            if _trace_agent_state is not None:
                _trace_canonical_step = int(getattr(_trace_agent_state, "step", -1))
        except Exception as _trace_step_exc:
            log.debug("Failed to read canonical step for trace: %s", _trace_step_exc)
        if _trace_canonical_step < 0:
            _pg_fb = self.private_graphs.get(ak)
            if _pg_fb:
                for _ent_fb in _pg_fb.entities.values():
                    _trace_canonical_step = max(_trace_canonical_step, int(getattr(_ent_fb, "born_step", 0) or 0))

        # 2. Affect classification of the query
        try:
            _trace_affect_enable = str(os.getenv("TORMENT_AFFECT_ENABLE", "1")).strip().lower() not in ("0", "false", "no")
        except Exception:
            _trace_affect_enable = True
        _trace_affect_personal = bool(_trace_affect_enable and looks_personal(query_text))
        _trace_q_affect_tag = "neutral"
        _trace_q_affect_conf = 0.0
        if _trace_affect_personal:
            try:
                _trace_qa = classify_affect(query_text)
                _trace_q_affect_tag = str(_trace_qa.tag)
                _trace_q_affect_conf = float(_trace_qa.conf)
            except Exception:
                _trace_q_affect_tag, _trace_q_affect_conf = "neutral", 0.0

        # 3. Mood-spiral: count recent negative drifts
        _trace_spiral_neg_recent = 0
        try:
            _trace_spiral_enable = str(os.getenv("TORMENT_MOOD_SPIRAL_ENABLE", "1")).strip().lower() not in ("0", "false", "no")
        except Exception:
            _trace_spiral_enable = True
        if _trace_spiral_enable and ak in self.private_graphs:
            try:
                _tst = _load_affect_state(self.data_dir, ws.workspace_id, str(agent_id))
                _tdh = _tst.get("drift_hist") or []
                if not isinstance(_tdh, list):
                    _tdh = []
                if _trace_canonical_step >= 0:
                    try:
                        _t_spiral_window = int(os.getenv("TORMENT_MOOD_SPIRAL_WINDOW_STEPS", "800"))
                    except Exception:
                        _t_spiral_window = 800
                    _neg = {"stressed", "sad", "angry"}
                    for _te in _tdh[-20:]:
                        try:
                            if int(_te.get("step", -10**9)) < _trace_canonical_step - _t_spiral_window:
                                continue
                            if str(_te.get("to")) in _neg:
                                _trace_spiral_neg_recent += 1
                        except Exception:
                            continue
            except Exception:
                _trace_spiral_neg_recent = 0

        # 4. Build shared ContinuityContext (qualified anchors are gathered below)
        _trace_anchor_full_boost: frozenset[QueryMemoryIdentity] = frozenset()

        def explain_for_hit(hit: Dict[str, Any]) -> Dict[str, Any]:
            now_ts = _now_ts()
            sim = float(hit.get('score', 0.0))
            strength = float(hit.get('strength', 0.5))
            ts = int(hit.get('created_ts', now_ts) or now_ts)
            recency_days = max(0.0, (now_ts - ts) / 86400.0)
            motifs = hit.get('motifs') or []
            motif_alignment = 0.0
            for mid in motifs:
                motif_identity = _qualified_query_motif_identity(
                    hit,
                    workspace_id=str(workspace_id),
                    motif_id=mid,
                )
                if motif_identity is None:
                    continue
                c = motif_centroids.get(motif_identity)
                if c is None or c.size == 0:
                    continue
                motif_alignment = max(motif_alignment, float(np.dot(qemb, c) / ((np.linalg.norm(qemb)+1e-12)*(np.linalg.norm(c)+1e-12))))
            contradiction_risk = float(hit.get('contradiction_risk', 0.0))
            type_bonus = 0.0

            # --- Provenance extraction (parity with query()) ---
            # Uses shared helper from scoring.py (centralised contract).
            from .scoring import is_collective_provenance as _is_coll_prov_t, apply_collective_discount as _apply_coll_disc_t, derive_query_provenance_type as _derive_q_prov_t
            _prov_raw = hit.get("provenance")
            _is_tool_result = (
                isinstance(_prov_raw, dict)
                and _prov_raw.get("source_type") == "tool_result"
            )
            _is_collective = _is_coll_prov_t(_prov_raw)

            # --- Conflict penalty (parity with query()) ---
            _hit_eid = int(hit.get("eid", -1))
            _hit_conflict_key = _conflict_hit_key(hit)
            conflict_info = (
                _trace_conflict_map.get(_hit_conflict_key)
                if _hit_conflict_key is not None
                else None
            )
            conflict_penalty = 0.0
            conflict_ids: List[str] = []
            conflict_status = None
            if conflict_info is not None and str(hit.get("scope", "")) == "shared" and bool(hit.get("canon", False)):
                conflict_status = "open"
                conflict_ids = list(conflict_info.get("conflict_ids") or [])
                conflict_penalty = float(conflict_info.get("max_score", 0.0))
                # Mirror query(): escalate contradiction_risk for contested canon
                contradiction_risk = max(contradiction_risk, 0.5 * conflict_penalty)

            # All continuity bonuses via shared helper (self-thread, self-anchor,
            # thread-window, affect, mood-drift, mood-spiral)
            _cont = compute_continuity_bonuses(hit, _trace_cont_ctx, is_tool_result=_is_tool_result)
            type_bonus += _cont.total

            final = score_hit(sim=sim, strength=strength, recency_days=recency_days, motif_alignment=motif_alignment, contradiction_risk=contradiction_risk, type_bonus=type_bonus)

            # --- SRG scoring bonuses (parity with query(), Phase 3) ---
            # NOTE: breathing evolution side effects are intentionally NOT
            # mirrored here — trace is read-only. Only score multipliers.
            _srg_same_band = 1.0
            _srg_crystal = 1.0
            _srg_heartbeat = 1.0
            if self._srg_enable:
                # Normalized SRG source (parity with query()): prefer top-level
                # hit["srg"], fall back to nested hit["payload"]["srg"]. Trace stays
                # read-only — no breathing/writeback here.
                _srg_hit = _effective_srg_source(hit)
                if _srg_hit:
                    # Same-band resonance: 8% boost — compare against THIS agent's
                    # last-ingested band only (keyed by (workspace_id, agent_id)).
                    _srg_last_band = self._srg_last_ingest_band_by_agent.get((workspace_id, agent_id))
                    if _srg_last_band is not None and _srg_hit.get("R_band") == _srg_last_band:
                        _srg_same_band = 1.08
                        final *= _srg_same_band
                    # Crystal identity anchor: 5% boost
                    if _srg_hit.get("is_crystal", False):
                        _srg_crystal = 1.05
                        final *= _srg_crystal
                    # Class A (deep/slow heartbeat): 3% stability bonus
                    if _srg_hit.get("heartbeat_class") == "A":
                        _srg_heartbeat = 1.03
                        final *= _srg_heartbeat

            # --- Post-score discounts (parity with query()) ---
            try:
                collective_discount = float(os.getenv("TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT", "0.50"))
            except Exception:
                collective_discount = 0.50
            _pre_coll = final
            final = _apply_coll_disc_t(final, _prov_raw, discount=collective_discount)
            # Record effective discount for explain surface
            if final != _pre_coll:
                pass  # collective_discount already set
            else:
                collective_discount = 1.0
            tool_result_discount = 1.0

            if _is_tool_result:
                try:
                    tool_result_discount = float(os.getenv("TORMENT_TOOL_RESULT_RETRIEVAL_DISCOUNT", "0.85"))
                except Exception:
                    tool_result_discount = 0.85
                final *= tool_result_discount

            # --- Memory-plan lane weights (parity with query()) ---
            _lane = "core"
            _lane_w = 1.0
            _lane_applied = False
            if _trace_mp_weights:
                _hit_scope = str(hit.get("scope", "private"))
                _is_deep = bool(hit.get("spirit_return_mode") or hit.get("deep_memory"))
                if _is_deep:
                    _lane = "deep"
                    _lane_w = float(_trace_mp_weights.get("deep", 1.0))
                elif _is_collective:
                    # Skip — Phase D3 collective discount already applied above.
                    _lane = "collective"
                    _lane_w = 1.0
                elif _hit_scope == "shared":
                    _lane = "relational"
                    _lane_w = float(_trace_mp_weights.get("relational", 1.0))
                else:
                    _lane = "core"
                    _lane_w = float(_trace_mp_weights.get("core", 1.0))
                # Clamp weight to [0.1, 2.0] to prevent extreme distortion
                _lane_w = max(0.1, min(2.0, _lane_w))
                final *= _lane_w
                _lane_applied = True

            return {
                "eid": _hit_eid,
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
                    "collective_discount": collective_discount,
                    "tool_result_discount": tool_result_discount,
                    "conflict_penalty": conflict_penalty,
                    "conflict_status": conflict_status,
                    "conflict_ids": conflict_ids,
                    # Provenance badge via doctrinal adapter — canonical
                    # derivation + VALID_SOURCE_TYPES enforcement.
                    # See docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md §7.2.
                    "provenance_type": _derive_q_prov_t(_prov_raw),
                    "self_thread_bonus": _cont.self_thread_bonus,
                    "self_anchor_bonus": _cont.self_anchor_bonus,
                    "thread_window_bonus": _cont.thread_window_bonus,
                    "affect_match_bonus": _cont.affect_match_bonus,
                    "mood_drift_bonus": _cont.mood_drift_bonus,
                    "mood_spiral_penalty": _cont.mood_spiral_penalty,
                    "continuity_total_adjustment": _cont.total,
                    "srg_same_band_bonus": _srg_same_band,
                    "srg_crystal_bonus": _srg_crystal,
                    "srg_heartbeat_bonus": _srg_heartbeat,
                    "srg_total_multiplier": _srg_same_band * _srg_crystal * _srg_heartbeat,
                    # Diagnostic-only: names of the SRG multipliers that fired
                    # (non-neutral), in stable order. Derived purely from the
                    # already-computed multiplier values above; reads no raw R
                    # and affects no score / ranking / filter / write.
                    "srg_active_modifiers": [
                        _name for _name, _mult in (
                            ("same_band", _srg_same_band),
                            ("crystal", _srg_crystal),
                            ("heartbeat_a", _srg_heartbeat),
                        ) if _mult != 1.0
                    ],
                    "memory_plan_lane": _lane,
                    "lane_weight": _lane_w,
                    "lane_weight_applied": _lane_applied,
                },
            }

        # Compute real cosine similarity for a graph entity against the
        # query embedding so trace scores reflect actual retrieval ranking
        # instead of the previous hardcoded 0.0.
        from .embedding_store import load_embedding as _load_emb_trace
        _qv_norm = np.asarray(qemb, dtype=np.float32).reshape(-1)
        _qv_n = np.linalg.norm(_qv_norm)
        if _qv_n > 1e-12:
            _qv_norm = _qv_norm / _qv_n

        def _real_sim(graph, eid: int, payload: dict) -> float:
            """Return cosine similarity between qemb and stored embedding."""
            try:
                raw = _load_emb_trace(
                    eid, payload,
                    graph._shard_reader, graph.data_dir,
                )
                if raw is None:
                    return 0.0
                v = np.asarray(raw, dtype=np.float32).reshape(-1)
                n = np.linalg.norm(v)
                if n < 1e-12:
                    return 0.0
                return float(np.dot(_qv_norm, v / n))
            except Exception:
                return 0.0

        def _build_trace_hit(graph, eid: int, ent, default_scope: str) -> dict:
            """Build a hit dict with real similarity and full payload fields."""
            payload = dict(ent.payload or {})
            return {
                "eid": int(eid),
                "score": _real_sim(graph, int(eid), payload),
                "strength": float(payload.get('strength', 0.0)),
                "created_ts": int(payload.get('created_ts', 0) or 0),
                "workspace_id": payload.get('workspace_id'),
                "domain_id": payload.get('domain_id'),
                "scope": payload.get('scope', default_scope),
                "motifs": payload.get('motifs', []),
                "type": str(payload.get('type') or ''),
                "agent_id": payload.get('agent_id', ''),
                "affect_tag": payload.get('affect_tag', ''),
                "affect_conf": float(payload.get('affect_conf', 0.0) or 0.0),
                "canon": bool(payload.get('canon', False)),
                "provenance": payload.get('provenance'),
                "step": int(getattr(ent, 'born_step', 0) or payload.get('step', 0) or 0),
                "spirit_return_mode": payload.get('spirit_return_mode'),
                "deep_memory": bool(payload.get('deep_memory', False)),
                "srg": payload.get('srg'),
            }

        # gather raw hits first (needed for anchor top-k before explain)
        _raw_hits: List[Dict[str, Any]] = []
        priv = self.private_graphs.get(ak)
        if priv:
            for eid in eids:
                ent = priv.entities.get(int(eid))
                if ent:
                    _raw_hits.append(_build_trace_hit(priv, eid, ent, 'private'))
        for d in domains:
            sg = ws.shared_graphs.get(d)
            if not sg:
                continue
            for eid in eids:
                ent = sg.entities.get(int(eid))
                if not ent:
                    continue
                _raw_hits.append(_build_trace_hit(sg, eid, ent, 'shared'))

        # Compute anchor top-k from gathered hits (parity with query())
        try:
            _t_anchor_topk = int(os.getenv("TORMENT_ANCHOR_BOOST_TOPK", "3"))
        except Exception:
            _t_anchor_topk = 3
        if _t_anchor_topk > 0:
            try:
                _t_acand = []
                for _rh in _raw_hits:
                    # §2A P7: parity with query() — only seed-canon and
                    # drift-correction anchors qualify for full boost.
                    _rh_type = str(_rh.get("type") or "")
                    if _rh_type == "identity_anchor":
                        if not bool(_rh.get("canon")):
                            continue
                    elif _rh_type not in ("seed_canon", "drift_correction"):
                        continue
                    if bool(_rh.get("anchor_retired")):
                        continue
                    _memory_identity = qualified_query_memory_identity(
                        _rh,
                        expected_workspace_id=str(workspace_id),
                    )
                    if _memory_identity is None:
                        continue
                    _t_acand.append((_memory_identity, float(_rh.get("score", 0.0))))
                _t_acand.sort(key=lambda x: x[1], reverse=True)
                _trace_anchor_full_boost = frozenset(
                    identity for (identity, _score) in _t_acand[:_t_anchor_topk]
                )
            except Exception:
                _trace_anchor_full_boost = frozenset()

        # Build ContinuityContext now that qualified anchor identities are known
        _trace_cont_ctx = ContinuityContext.from_env(
            agent_id=str(agent_id),
            canonical_step=_trace_canonical_step,
            affect_personal=_trace_affect_personal,
            q_affect_tag=_trace_q_affect_tag,
            q_affect_conf=_trace_q_affect_conf,
            spiral_neg_recent=_trace_spiral_neg_recent,
            workspace_id=str(workspace_id),
            anchor_full_boost_memory_ids=_trace_anchor_full_boost,
        )

        # Explain each raw hit
        out = [explain_for_hit(rh) for rh in _raw_hits]

        return {"workspace_id": workspace_id, "agent_id": agent_id, "query": query_text, "domains": domains, "items": out, "embed_context": self._embed_context(ws)}


    def memory_chain(self, workspace_id: str, eid: int, scope: str = "shared", domain_id: Optional[str] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Return append-only event chain for a memory (from its graph event log)."""
        _validate_path_component(workspace_id, "workspace_id")
        if domain_id:
            _validate_path_component(domain_id, "domain_id")
        if agent_id:
            _validate_path_component(agent_id, "agent_id")
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
        _validate_path_component(workspace_id, "workspace_id")
        if domain_id:
            _validate_path_component(domain_id, "domain_id")
        if agent_id:
            _validate_path_component(agent_id, "agent_id")
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
        out_dir = _safe_child(_ws_root(self.data_dir, workspace_id), 'exports')
        _od = os.path.realpath(out_dir)
        if not _od.startswith(os.sep) and not os.path.isabs(_od):
            raise ValueError(f"Export dir not absolute: {_od!r}")
        os.makedirs(_od, exist_ok=True)
        if export in ('json','bundle'):
            jp = _safe_child(out_dir, f"trace_{eid}_{dom}.json")
            with open(jp,'w',encoding='utf-8') as f:
                json.dump(graph, f, indent=2, ensure_ascii=False)
            export_files['json'] = jp
        if export in ('dot','bundle'):
            dp = _safe_child(out_dir, f"trace_{eid}_{dom}.dot")
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
        _validate_path_component(workspace_id, "workspace_id")
        if domain_id:
            _validate_path_component(domain_id, "domain_id")
        if agent_id:
            _validate_path_component(agent_id, "agent_id")
        dom = domain_id or 'research'
        graph = self.trace_full_graph(workspace_id, eid, scope=scope, domain_id=dom, agent_id=agent_id, depth=depth, explain=explain, export='bundle')
        out_dir = _safe_child(_ws_root(self.data_dir, workspace_id), 'exports', f"bundle_{eid}_{dom}")
        _od = os.path.realpath(out_dir)
        if not _od.startswith(os.sep) and not os.path.isabs(_od):
            raise ValueError(f"Bundle dir not absolute: {_od!r}")
        os.makedirs(_od, exist_ok=True)
        # write graph.json/dot already created in exports; copy into bundle
        import shutil
        jp = graph.get('export_files', {}).get('json')
        dp = graph.get('export_files', {}).get('dot')
        bjp = _safe_child(out_dir, 'graph.json')
        bdp = _safe_child(out_dir, 'graph.dot')
        # Containment guard: validate source paths stay within workspace
        _bundle_ws = os.path.realpath(_ws_root(self.data_dir, workspace_id))
        if jp:
            _jp_safe = os.path.realpath(jp)
            if not _jp_safe.startswith(_bundle_ws + os.sep):
                raise ValueError(f"Export JSON path escapes workspace: {_jp_safe!r}")
            if os.path.exists(_jp_safe):
                shutil.copy(_jp_safe, bjp)
        if dp:
            _dp_safe = os.path.realpath(dp)
            if not _dp_safe.startswith(_bundle_ws + os.sep):
                raise ValueError(f"Export DOT path escapes workspace: {_dp_safe!r}")
            if os.path.exists(_dp_safe):
                shutil.copy(_dp_safe, bdp)
        # narrative
        narrative = self._trace_narrative(workspace_id, eid=eid, scope=scope, domain_id=dom, agent_id=agent_id)
        npath = _safe_child(out_dir, 'narrative.md')
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
            },
        }
        mpath = _safe_child(out_dir, 'manifest.json')
        import json as _json_mod
        with open(mpath, 'w', encoding='utf-8') as f:
            _json_mod.dump(manifest, f, indent=2, default=str)
        manifest['manifest_path'] = mpath
        return manifest
            

    def _trace_narrative(
        self,
        workspace_id: str,
        eid: int,
        scope: str = "shared",
        domain_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        """Build a markdown narrative summarizing a memory's trace history.

        Walks memory_chain events for the given eid and renders them as a
        readable markdown block. Used by both trace_view (return-only HTTP
        endpoint) and trace_bundle (writes the same string to narrative.md).
        Pure function over memory_chain output -- no filesystem effects.
        """
        chain = self.memory_chain(
            workspace_id, eid=eid, scope=scope,
            domain_id=domain_id, agent_id=agent_id,
        )
        events = chain.get("events", []) or []
        lines = []
        lines.append(f"# Trace narrative for eid={int(eid)}")
        lines.append("")
        lines.append(f"- workspace: `{workspace_id}`")
        lines.append(f"- scope: `{scope}`")
        if domain_id:
            lines.append(f"- domain: `{domain_id}`")
        if agent_id:
            lines.append(f"- agent: `{agent_id}`")
        lines.append(f"- events: {len(events)}")
        lines.append("")
        if not events:
            lines.append("_(no recorded events for this memory)_")
        else:
            lines.append("## Events")
            for i, evt in enumerate(events):
                etype = evt.get("type", "EVENT")
                ts = evt.get("ts", "")
                step = evt.get("step", "")
                who = evt.get("agent_id", "")
                lines.append(
                    f"{i+1}. **{etype}** -- step={step} ts={ts} agent={who}"
                )
        return "\n".join(lines)

    def trace_view(
        self,
        workspace_id: str,
        eid: int,
        scope: str = "shared",
        domain_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        depth: int = 2,
        explain: bool = False,
    ) -> Dict[str, Any]:
        """Return a trace narrative + graph summary without writing files.

        Lightweight return-only counterpart to trace_bundle: the same source
        data (memory_chain + trace graph) rendered into an in-memory response
        for the /memory/trace_view HTTP endpoint. trace_bundle remains the
        path that materializes the bundle on disk.
        """
        graph = self.trace_full_graph(
            workspace_id, eid,
            scope=scope, domain_id=domain_id, agent_id=agent_id,
            depth=depth, explain=explain, export="none",
        )
        narrative = self._trace_narrative(
            workspace_id, eid=eid, scope=scope,
            domain_id=domain_id, agent_id=agent_id,
        )
        nodes = graph.get("nodes", []) or []
        edges = graph.get("edges", []) or []
        node_types: Dict[str, int] = {}
        for n in nodes:
            t = str(n.get("type", "unknown"))
            node_types[t] = node_types.get(t, 0) + 1
        graph_summary = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": node_types,
            "meta": graph.get("meta", {}),
        }
        return {
            "workspace_id": workspace_id,
            "eid": int(eid),
            "scope": scope,
            "domain_id": domain_id,
            "narrative": narrative,
            "graph_summary": graph_summary,
        }

    # ------------------------------------------------------------------
    # Lifecycle (Block C1 -- :memory: handling)
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release fabric-owned transient resources.

        Closes Fabric-owned graphs and per-agent SQLite indexes, then, if this
        fabric was constructed with data_dir=":memory:", the backing
        TemporaryDirectory. Idempotent -- safe to call multiple times. After
        close(), persistent state held only in the temp directory is gone.
        """
        manager = getattr(self, "brainvision_lifecycle", None)
        if manager is not None:
            try:
                manager.shutdown()
            except Exception as e:
                log.debug("Brainvision lifecycle shutdown failed during fabric close: %s", e)

        # Close per-agent SQLite indexes BEFORE tmpdir cleanup so
        # Windows can unlink memory_index.sqlite. IndexManager.close()
        # is itself idempotent (handles already-closed connections).
        sqlite_indexes = getattr(self, "_sqlite_indexes", None)
        if sqlite_indexes:
            for idx in list(sqlite_indexes.values()):
                if idx is not None:
                    try:
                        idx.close()
                    except Exception as e:
                        self._log.debug("SQLite index close failed during fabric close: %s", e)
            sqlite_indexes.clear()

        # Cached private and shared graphs are Fabric-owned.  Their shard
        # reader/writer memmaps must be closed before Windows can clean up a
        # Fabric temporary directory.  Deduplicate by object identity in case
        # a graph is ever reachable from more than one owned cache.
        closed_graph_ids = set()

        def _close_owned_graph(graph: Optional[MemoryGraph]) -> None:
            if graph is None or id(graph) in closed_graph_ids:
                return
            closed_graph_ids.add(id(graph))
            try:
                graph.close()
            except Exception as e:
                self._log.debug("MemoryGraph close failed during fabric close: %s", e)

        for graph in list(getattr(self, "private_graphs", {}).values()):
            _close_owned_graph(graph)
        for workspace in list(getattr(self, "workspaces", {}).values()):
            for graph in list(getattr(workspace, "shared_graphs", {}).values()):
                _close_owned_graph(graph)

        # Deep stores are constructed and retained by this Fabric.  Their shard
        # memmaps must be released before a :memory: backing directory is removed.
        deep_stores = getattr(self, "_deep_stores", None)
        if deep_stores:
            for store in list(deep_stores.values()):
                if store is not None:
                    try:
                        store.close()
                    except Exception as e:
                        self._log.debug(
                            "DeepMemoryStore close failed during fabric close: %s", e
                        )
            deep_stores.clear()

        kernel_contexts = getattr(self, "_kernel_contexts", None)
        if kernel_contexts is not None:
            kernel_contexts.clear()
        agent_states = getattr(self, "agent_states", None)
        if agent_states is not None:
            agent_states.clear()

        tmpdir = getattr(self, "_memory_tmpdir", None)
        if tmpdir is not None:
            try:
                tmpdir.cleanup()
            except Exception:
                # Windows may hold open handles (numpy memmap, sqlite);
                # cleanup is best-effort here. tempfile's own finalizer
                # will retry at garbage collection.
                pass
            self._memory_tmpdir = None

    def __enter__(self) -> "TormentFabric":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
