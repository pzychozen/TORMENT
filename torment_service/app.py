# app.py
from __future__ import annotations
from typing import Dict, Any, Optional, List
import os, json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .fabric import TormentFabric
from .router import DEFAULT_DOMAINS
from .profiles import PROFILES, apply_profile_env
from .config_view import build_config_view

DATA_DIR = os.environ.get("TORMENT_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))

# Apply optional preset profile (defaults only; explicit env vars always win)
ACTIVE_PROFILE = os.environ.get("TORMENT_PROFILE", "").strip().lower() or None
PROFILE_APPLIED = apply_profile_env(ACTIVE_PROFILE)
PROFILE_KNOWN = bool(ACTIVE_PROFILE) and (ACTIVE_PROFILE in PROFILES)

app = FastAPI(title="Torment Memory Fabric (TriOcta)", version='2.0.0' )

fabric = TormentFabric(data_dir=DATA_DIR)


@app.get("/workspace/{workspace_id}/embed_audit")
def workspace_embed_audit(workspace_id: str) -> Dict[str, Any]:
    """Return persisted embedding health index for a workspace (fast; no scan)."""
    import os, json
    path = os.path.join(DATA_DIR, "workspaces", workspace_id, "embed_audit.json")
    if not os.path.exists(path):
        return {
            "ok": False,
            "workspace_id": workspace_id,
            "detail": "No audit found yet. Run /workspace/repair_embeddings with mode=scan or repair.",
        }
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    payload["ok"] = True
    return payload


@app.get("/workspaces/embed_audit_summary")
def workspaces_embed_audit_summary(limit: int = 200) -> Dict[str, Any]:
    """Return embedding audit summaries across workspaces (fast; no scan)."""
    import os, json
    wroot = os.path.join(DATA_DIR, "workspaces")
    out: List[Dict[str, Any]] = []
    if not os.path.isdir(wroot):
        return {"ok": True, "workspaces": out}
    for wsid in sorted(os.listdir(wroot)):
        if len(out) >= int(limit):
            break
        path = os.path.join(wroot, wsid, "embed_audit.json")
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            payload["ok"] = True
            out.append(payload)
        except Exception:
            continue
    return {"ok": True, "workspaces": out}

# -------------------- models --------------------
class WorkspaceCreateReq(BaseModel):
    workspace_id: str = Field(default="default")
    domains: Optional[List[str]] = None  # if provided, only these domains are created (default: all 5)



class WorkspaceCloneReq(BaseModel):
    source_workspace_id: str
    target_workspace_id: str
    include_private: bool = True
    include_shared: bool = True
    reembed: bool = True
    reembed_mode: str = "selective"  # selective|all


class WorkspaceRepairReq(BaseModel):
    workspace_id: str
    mode: str = "scan"  # scan|repair
    include_private: bool = True
    include_shared: bool = True
    limit: Optional[int] = None

class WorkspaceMaintenanceReq(BaseModel):
    workspace_id: str
    mode: str = "scan_embeddings"  # scan_embeddings|repair_embeddings|compact_indexes
    include_private: bool = True
    include_shared: bool = True
    limit: Optional[int] = None

class AgentCreateReq(BaseModel):
    workspace_id: str = Field(default="default")
    agent_id: str
    seed: Optional[Dict[str, Any]] = None

class IngestReq(BaseModel):
    workspace_id: str = Field(default="default")
    agent_id: str
    text: str
    step: int = Field(default=0)
    domain_id: Optional[str] = None
    scope: str = Field(default="private")  # private | shared (shared requires policy later)
    supplied_summary: Optional[str] = None
    supplied_embedding: Optional[List[float]] = None

class QueryReq(BaseModel):
    workspace_id: str = Field(default="default")
    agent_id: str
    query: str
    top_k: int = Field(default=8)
    domain_id: Optional[str] = None
    peek_bridges: bool = Field(default=False)
    explain: bool = Field(default=False)
    continuity_debug: bool = Field(default=False)

class FeedbackReq(BaseModel):
    workspace_id: str = Field(default="default")
    agent_id: str
    retrieved_ids: List[int] = Field(default_factory=list)
    used_successfully: bool = False
    user_confirmed: bool = False
    contradiction_detected: bool = False
    novel_motif_created: bool = False
    shared_memory_used: bool = False
    bridges_used: Optional[List[Dict[str, str]]] = None



class MotifMergeDecideReq(BaseModel):
    workspace_id: str = Field(default="default")
    domain_id: str
    suggestion_id: str
    decision: str  # approve | reject | reset
    note: str = Field(default="")


class ConflictDecideReq(BaseModel):
    workspace_id: str = Field(default="default")
    domain_id: str
    conflict_id: str
    decision: str  # keep_a | keep_b | fork | merge | demote_both | reject
    note: str = Field(default="")

class ProposeShareReq(BaseModel):
    workspace_id: str = Field(default="default")
    agent_id: str
    summary: str
    domain_id: Optional[str] = None
    mtype: str = Field(default="fact")
    confidence: float = Field(default=0.6)
    strength: float = Field(default=0.6)
    supplied_embedding: Optional[List[float]] = None

class ProcessProposalsReq(BaseModel):
    workspace_id: str = Field(default="default")
    domain_id: str
    max_to_process: int = Field(default=200)
    sim_threshold: float = Field(default=0.90)
    min_distinct_agents: int = Field(default=0)




class DecideBridgeReq(BaseModel):
    workspace_id: str = Field(default="default")
    from_domain: str
    from_motif: str
    to_domain: str
    to_motif: str
    decision: str  # approve|reject|reset

class ApproveDomainSuggestionReq(BaseModel):
    workspace_id: str = Field(default="default")
    domain_id: str


class TraceReq(BaseModel):
    workspace_id: str = Field(default="default")
    agent_id: str
    query: str
    eids: List[int] = Field(default_factory=list)
    domain_id: Optional[str] = None

class ChainReq(BaseModel):
    workspace_id: str = Field(default="default")
    eid: int
    scope: str = Field(default="shared")  # shared|private
    domain_id: Optional[str] = None       # for shared
    agent_id: Optional[str] = None        # for private

class TraceFullReq(BaseModel):
    workspace_id: str = Field(default="default")
    eid: int
    scope: str = Field(default="shared")  # shared|private
    domain_id: Optional[str] = None
    agent_id: Optional[str] = None
    depth: int = Field(default=2, ge=0, le=6)
    explain: bool = Field(default=False)
    export: str = Field(default="none")  # none|json|dot

class TraceBundleReq(BaseModel):
    workspace_id: str = Field(default="default")
    eid: int
    scope: str = Field(default="shared")  # shared|private
    domain_id: Optional[str] = None
    agent_id: Optional[str] = None
    depth: int = Field(default=2, ge=0, le=6)
    explain: bool = Field(default=False)
    export: str = Field(default="bundle")  # bundle|none


class TraceViewReq(BaseModel):
    workspace_id: str = Field(default="default")
    eid: int
    scope: str = Field(default="shared")  # shared|private
    domain_id: Optional[str] = None
    agent_id: Optional[str] = None
    depth: int = Field(default=2, ge=0, le=6)
    explain: bool = Field(default=False)

class DecideProposalReq(BaseModel):
    workspace_id: str = Field(default="default")
    domain_id: str
    proposal_id: str
    decision: str  # approve|reject
    note: Optional[str] = None

# -------------------- endpoints --------------------
@app.get("/health")
def health() -> Dict[str, Any]:
    embedder = getattr(getattr(fabric, "kernel", None), "embedder", None)
    info = {
        "provider": str(getattr(embedder, "provider", "")),
        "model": str(getattr(embedder, "model", "")),
        "dim": int(getattr(embedder, "dim", 0) or 0),
        "cache_size": int(getattr(embedder, "max_size", 0) or 0),
    }
    degraded = bool(getattr(fabric, "embedder_error", "")) and (str(getattr(fabric, "requested_embed_provider", "hash")).strip().lower() not in ("hash", "det", "deterministic"))

    ws_meta = []
    try:
        ws_meta = fabric.list_workspaces_meta()
    except Exception:
        ws_meta = []
    sample_n = int(os.environ.get("TORMENT_HEALTH_WORKSPACE_SAMPLE", "10") or 10)
    ws_sample = ws_meta[:max(0, sample_n)]

    # Optional: include persisted embedding audit summaries in /health (fast; no scan)
    include_audits = str(os.environ.get("TORMENT_HEALTH_INCLUDE_AUDITS", "")).strip().lower() in ("1","true","yes","on")
    audit_sample = []
    audit_count = 0
    audit_dirty_count = 0
    if include_audits:
        try:
            wroot = os.path.join(DATA_DIR, "workspaces")
            if os.path.isdir(wroot):
                sample_m = int(os.environ.get("TORMENT_HEALTH_AUDIT_SAMPLE", "10") or 10)
                for wsid in sorted(os.listdir(wroot)):
                    path = os.path.join(wroot, wsid, "embed_audit.json")
                    if not os.path.exists(path):
                        continue
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            payload = json.load(f)
                        audit_count += 1
                        if bool(payload.get("dirty", False)):
                            audit_dirty_count += 1
                        if len(audit_sample) < max(0, sample_m):
                            # keep payload light in /health
                            audit_sample.append({
                                "workspace_id": payload.get("workspace_id", wsid),
                                "updated_ts": payload.get("updated_ts", ""),
                                "dirty": bool(payload.get("dirty", False)),
                                "total_nodes": int(payload.get("total_nodes", 0) or 0),
                                "counts": payload.get("counts", {}),
                            })
                    except Exception:
                        continue
        except Exception:
            audit_sample = []
            audit_count = 0
            audit_dirty_count = 0


    return {
        "ok": True,
        "version": app.version,
        "profile": {
            "name": ACTIVE_PROFILE or "",
            "known": bool(PROFILE_KNOWN),
            "applied_count": int(len(PROFILE_APPLIED)),
            "applied_keys": list(PROFILE_APPLIED.keys())[:40],
        },
        "workspace_meta_count": int(len(ws_meta)),
        "workspace_meta_sample": ws_sample,
        "embed_audit_count": int(audit_count) if include_audits else None,
        "embed_audit_dirty_count": int(audit_dirty_count) if include_audits else None,
        "embed_audit_sample": audit_sample if include_audits else None,
        "embedder": info,
        "embedder_degraded": degraded,
        "embedder_error": str(getattr(fabric, "embedder_error", "")) if degraded else "",
        "requested_embedder": {
            "provider": str(getattr(fabric, "requested_embed_provider", "")),
            "model": str(getattr(fabric, "requested_embed_model", "")),
            "strict": str(os.environ.get("TORMENT_EMBED_STRICT") or "").strip() in ("1", "true", "yes", "on"),
        },
    }




@app.get("/profiles")
def profiles() -> Dict[str, Any]:
    """Return built-in profile definitions and the currently active profile (if any)."""
    return {
        "ok": True,
        "active": {
            "name": ACTIVE_PROFILE or "",
            "known": bool(PROFILE_KNOWN),
            "applied_count": int(len(PROFILE_APPLIED)),
            "applied": PROFILE_APPLIED,
        },
        "profiles": PROFILES,
    }


@app.get("/config")
def config() -> Dict[str, Any]:
    """Return a UI-friendly view of effective configuration.

    Read-only. Helps users/UI understand what settings are active, and where
    each value came from (default / profile_default / env_override).
    """
    return build_config_view(
        active_profile=ACTIVE_PROFILE,
        profile_applied=PROFILE_APPLIED,
        profile_known=PROFILE_KNOWN,
        data_dir=DATA_DIR,
    )

@app.get("/workspaces/meta")
def workspaces_meta() -> Dict[str, Any]:
    """List persisted workspace embedding locks/metadata."""
    meta = fabric.list_workspaces_meta()
    return {"ok": True, "count": int(len(meta)), "workspaces": meta}


def _embedder_actionable_hint(provider: str, err: str) -> str:
    p = (provider or "").strip().lower()
    e = (err or "").lower()
    if p == "st":
        if "sentence_transformers" in e or "sentence-transformers" in e or "no module named" in e:
            return "Install sentence-transformers: pip install sentence-transformers"
    if p == "ollama":
        if "connection refused" in e or "timed out" in e or "urlopen error" in e:
            return "Check Ollama is running and TORMENT_OLLAMA_URL is correct (default http://127.0.0.1:11434)."
        if "404" in e or "not found" in e:
            return "Ollama endpoint not found. Expected POST /api/embeddings on the Ollama server."
    return ""


@app.get("/embedder/check")
def embedder_check() -> Dict[str, Any]:
    """One-shot embedding diagnostic: embeds a probe string and reports dim + latency."""
    import time as _time

    embedder = getattr(getattr(fabric, "kernel", None), "embedder", None)
    provider = str(getattr(embedder, "provider", "")) if embedder else ""
    model = str(getattr(embedder, "model", "")) if embedder else ""
    t0 = _time.perf_counter()
    try:
        v = embedder.embed("dim_probe") if embedder else None
        dt_ms = (_time.perf_counter() - t0) * 1000.0
        dim = int(getattr(embedder, "dim", 0) or (len(v) if v is not None else 0))
        # Ensure vector-like
        ok = True
        return {
            "ok": ok,
            "provider": provider,
            "model": model,
            "dim": dim,
            "elapsed_ms": float(dt_ms),
            "degraded": bool(getattr(fabric, "embedder_error", "")),
            "error": "",
            "hint": "",
        }
    except Exception as e:
        dt_ms = (_time.perf_counter() - t0) * 1000.0
        err = f"{type(e).__name__}: {e}"
        hint = _embedder_actionable_hint(provider, err)
        return {
            "ok": False,
            "provider": provider,
            "model": model,
            "dim": int(getattr(embedder, "dim", 0) or 0) if embedder else 0,
            "elapsed_ms": float(dt_ms),
            "degraded": bool(getattr(fabric, "embedder_error", "")),
            "error": err,
            "hint": hint,
        }



@app.post("/workspace/create")
def workspace_create(req: WorkspaceCreateReq) -> Dict[str, Any]:
    ws = fabric.get_workspace(req.workspace_id, domains=req.domains)
    return {"workspace_id": ws.workspace_id, "domains": ws.domains}


@app.post("/workspace/clone")
def workspace_clone(req: WorkspaceCloneReq) -> Dict[str, Any]:
    return fabric.clone_workspace(
        source_workspace_id=req.source_workspace_id,
        target_workspace_id=req.target_workspace_id,
        include_private=req.include_private,
        include_shared=req.include_shared,
        reembed=req.reembed,
        reembed_mode=req.reembed_mode,
    )


@app.post("/workspace/repair_embeddings")
def workspace_repair_embeddings(req: WorkspaceRepairReq) -> Dict[str, Any]:
    """Scan or repair embeddings for a workspace without cloning."""
    return fabric.repair_embeddings(
        workspace_id=req.workspace_id,
        mode=req.mode,
        include_private=req.include_private,
        include_shared=req.include_shared,
        limit=req.limit,
    )

@app.post("/workspace/repair_embeddings/job")
def workspace_repair_embeddings_job(req: WorkspaceRepairReq) -> Dict[str, Any]:
    """Start an async scan/repair job and return a job_id."""
    return fabric.start_repair_embeddings_job(
        workspace_id=req.workspace_id,
        mode=req.mode,
        include_private=req.include_private,
        include_shared=req.include_shared,
        limit=req.limit,
    )

@app.get("/workspace/repair_embeddings/jobs")
def repair_jobs() -> Dict[str, Any]:
    return {"jobs": fabric.list_repair_jobs()}

@app.get("/workspace/repair_embeddings/job/{job_id}")
def repair_job(job_id: str) -> Dict[str, Any]:
    return fabric.get_repair_job(job_id)


@app.post("/workspace/repair_embeddings/job/{job_id}/cancel")
def cancel_repair_job(job_id: str) -> Dict[str, Any]:
    return fabric.cancel_repair_job(job_id)





@app.post("/workspace/maintenance")
def workspace_maintenance(req: WorkspaceMaintenanceReq) -> Dict[str, Any]:
    """Unified maintenance endpoint (simple UX wrapper)."""
    mode = (req.mode or "").strip().lower()
    if mode in ("scan_embeddings", "scan"):
        return fabric.repair_embeddings(
            workspace_id=req.workspace_id,
            mode="scan",
            include_private=req.include_private,
            include_shared=req.include_shared,
            limit=req.limit,
        )
    if mode in ("repair_embeddings", "repair"):
        return fabric.repair_embeddings(
            workspace_id=req.workspace_id,
            mode="repair",
            include_private=req.include_private,
            include_shared=req.include_shared,
            limit=req.limit,
        )
    if mode in ("compact_indexes", "compact"):
        # Placeholder: graph/index compaction can be added later without changing the UX surface.
        return {"ok": True, "workspace_id": req.workspace_id, "mode": "compact_indexes", "detail": "No-op (not implemented yet)."}
    raise HTTPException(status_code=400, detail=f"Unknown maintenance mode: {req.mode}")


@app.post("/workspace/maintenance/job")
def workspace_maintenance_job(req: WorkspaceMaintenanceReq) -> Dict[str, Any]:
    """Unified async maintenance job starter."""
    mode = (req.mode or "").strip().lower()
    if mode in ("scan_embeddings", "scan"):
        out = fabric.start_repair_embeddings_job(
            workspace_id=req.workspace_id,
            mode="scan",
            include_private=req.include_private,
            include_shared=req.include_shared,
            limit=req.limit,
        )
        out.update({"ok": True, "maintenance_mode": "scan_embeddings", "job_kind": "repair_embeddings"})
        return out
    if mode in ("repair_embeddings", "repair"):
        out = fabric.start_repair_embeddings_job(
            workspace_id=req.workspace_id,
            mode="repair",
            include_private=req.include_private,
            include_shared=req.include_shared,
            limit=req.limit,
        )
        out.update({"ok": True, "maintenance_mode": "repair_embeddings", "job_kind": "repair_embeddings"})
        return out
    if mode in ("compact_indexes", "compact"):
        raise HTTPException(status_code=400, detail="compact_indexes is not implemented yet (no async job).")
    raise HTTPException(status_code=400, detail=f"Unknown maintenance mode: {req.mode}")
@app.get("/workspace/clone/jobs")
def clone_jobs() -> Dict[str, Any]:
    return {"jobs": fabric.list_clone_jobs()}

@app.get("/workspace/clone/job/{job_id}")
def clone_job(job_id: str) -> Dict[str, Any]:
    return fabric.get_clone_job(job_id)

@app.get("/workspace/{workspace_id}/domains")
def list_domains(workspace_id: str) -> Dict[str, Any]:
    ws = fabric.get_workspace(workspace_id)
    return {"workspace_id": ws.workspace_id, "domains": ws.domains}

@app.post("/agent/create")
def agent_create(req: AgentCreateReq) -> Dict[str, Any]:
    ident = fabric.create_agent(req.workspace_id, req.agent_id, seed=req.seed)
    return {"workspace_id": ident.workspace_id, "agent_id": ident.agent_id, "seed": ident.seed, "overlay": ident.overlay}

@app.get("/agent/{agent_id}/identity")
def get_identity(agent_id: str, workspace_id: str = "default") -> Dict[str, Any]:
    ident = fabric.ident_store.load(workspace_id, agent_id)
    if ident is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")
    return {"workspace_id": ident.workspace_id, "agent_id": ident.agent_id, "seed": ident.seed, "overlay": ident.overlay, "updated_ts": ident.updated_ts}


@app.get("/agent/{agent_id}/roles")
def get_roles(agent_id: str, workspace_id: str = "default") -> Dict[str, Any]:
    """Return the soft role profile for character continuity (guidance signal)."""
    try:
        rp = fabric.role_store.load(workspace_id, agent_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Unknown agent_id")
    try:
        from .roles import dominant_role
        dom = dominant_role(rp)
    except Exception:
        dom = "explorer"
    return {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "dominant_role": dom,
        "scores": rp.scores,
        "samples": rp.samples,
        "created_ts": rp.created_ts,
        "updated_ts": rp.updated_ts,
    }

@app.post("/agent/ingest")
def ingest(req: IngestReq) -> Dict[str, Any]:
    return fabric.ingest(
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        text=req.text,
        step=req.step,
        domain_id=req.domain_id,
        supplied_summary=req.supplied_summary,
        supplied_embedding=req.supplied_embedding,
        scope=req.scope,
    )

@app.post("/agent/query")
def query(req: QueryReq) -> Dict[str, Any]:
    return fabric.query(
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        query_text=req.query,
        top_k=req.top_k,
        domain_id=req.domain_id,
        peek_bridges=req.peek_bridges,
        explain=req.explain,
        continuity_debug=req.continuity_debug,
    )


@app.post("/agent/trace")
def trace(req: TraceReq) -> Dict[str, Any]:
    return fabric.trace(
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        query_text=req.query,
        eids=req.eids,
        domain_id=req.domain_id,
    )


@app.post("/memory/chain")
def memory_chain(req: ChainReq) -> Dict[str, Any]:
    return fabric.memory_chain(
        workspace_id=req.workspace_id,
        eid=req.eid,
        scope=req.scope,
        domain_id=req.domain_id,
        agent_id=req.agent_id,
    )


@app.post("/memory/trace_full")
def memory_trace_full(req: TraceFullReq) -> Dict[str, Any]:
    return fabric.trace_full_graph(
        workspace_id=req.workspace_id,
        eid=req.eid,
        scope=req.scope,
        domain_id=req.domain_id,
        agent_id=req.agent_id,
        depth=req.depth,
        explain=req.explain,
        export=req.export,
    )

@app.post("/memory/trace_bundle")
def memory_trace_bundle(req: TraceBundleReq) -> Dict[str, Any]:
    return fabric.trace_bundle(
        workspace_id=req.workspace_id,
        eid=req.eid,
        scope=req.scope,
        domain_id=req.domain_id,
        agent_id=req.agent_id,
        depth=req.depth,
        explain=req.explain,
        export=req.export,
    )


@app.post("/memory/trace_view")
def memory_trace_view(req: TraceViewReq) -> Dict[str, Any]:
    return fabric.trace_view(
        workspace_id=req.workspace_id,
        eid=req.eid,
        scope=req.scope,
        domain_id=req.domain_id,
        agent_id=req.agent_id,
        depth=req.depth,
        explain=req.explain,
    )

@app.post("/agent/feedback")
def feedback(req: FeedbackReq) -> Dict[str, Any]:
    return fabric.feedback(
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        retrieved_ids=req.retrieved_ids,
        used_successfully=req.used_successfully,
        user_confirmed=req.user_confirmed,
        contradiction_detected=req.contradiction_detected,
        novel_motif_created=req.novel_motif_created,
        shared_memory_used=req.shared_memory_used,
        bridges_used=req.bridges_used,
    )

@app.get("/workspace/{workspace_id}/domain/{domain_id}/motifs/active")
def active_motifs(workspace_id: str, domain_id: str) -> Dict[str, Any]:
    ws = fabric.get_workspace(workspace_id)
    if domain_id not in ws.motif_regs:
        raise HTTPException(status_code=404, detail="Unknown domain_id")
    return {"workspace_id": workspace_id, "domain_id": domain_id, "active": ws.motif_regs[domain_id].active(top_k=12)}

@app.get("/workspace/{workspace_id}/bridges")
def list_bridges(workspace_id: str) -> Dict[str, Any]:
    return fabric.list_bridges(workspace_id=workspace_id, status="any", limit=500)



@app.get("/workspace/{workspace_id}/bridges/queue")
def bridges_queue(workspace_id: str, status: str = "suggested", limit: int = 200) -> Dict[str, Any]:
    # status: suggested|approved|rejected|any
    return fabric.list_bridges(workspace_id=workspace_id, status=status, limit=limit)

@app.post("/workspace/bridges/decide")
def decide_bridge(req: DecideBridgeReq) -> Dict[str, Any]:
    return fabric.decide_bridge(
        workspace_id=req.workspace_id,
        from_domain=req.from_domain,
        from_motif=req.from_motif,
        to_domain=req.to_domain,
        to_motif=req.to_motif,
        decision=req.decision,
    )

@app.post("/agent/propose_share")
def propose_share(req: ProposeShareReq) -> Dict[str, Any]:
    return fabric.propose_share(
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        summary=req.summary,
        embedding=req.supplied_embedding,
        domain_id=req.domain_id,
        mtype=req.mtype,
        confidence=req.confidence,
        strength=req.strength,
    )

@app.post("/workspace/process_proposals")
def process_proposals(req: ProcessProposalsReq) -> Dict[str, Any]:
    return fabric.process_proposals(
        workspace_id=req.workspace_id,
        domain_id=req.domain_id,
        max_to_process=req.max_to_process,
        sim_threshold=req.sim_threshold,
        min_distinct_agents=req.min_distinct_agents,
    )



@app.get("/workspace/{workspace_id}/domain/{domain_id}/proposals")
def list_proposals(workspace_id: str, domain_id: str, status: str = "pending", limit: int = 200) -> Dict[str, Any]:
    return fabric.list_proposals(workspace_id=workspace_id, domain_id=domain_id, status=status, limit=limit)

@app.post("/workspace/domain/proposals/decide")
def decide_proposal(req: DecideProposalReq) -> Dict[str, Any]:
    return fabric.decide_proposal(
        workspace_id=req.workspace_id,
        domain_id=req.domain_id,
        proposal_id=req.proposal_id,
        decision=req.decision,
        note=req.note,
    )


@app.post("/workspace/domain_suggestions/approve")
def approve_domain(req: ApproveDomainSuggestionReq) -> Dict[str, Any]:
    return fabric.approve_domain_suggestion(workspace_id=req.workspace_id, suggested_domain_id=req.domain_id)

@app.get("/workspace/{workspace_id}/domain_suggestions")
def domain_suggestions(workspace_id: str) -> Dict[str, Any]:
    ws = fabric.get_workspace(workspace_id)
    if not os.path.exists(ws.domain_suggestions_path):
        return {"workspace_id": workspace_id, "suggestions": []}
    with open(ws.domain_suggestions_path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return {"workspace_id": workspace_id, "suggestions": obj.get("suggestions", [])}

@app.get("/workspace/{workspace_id}/domain/{domain_id}/motif_entropy")
def motif_entropy(workspace_id: str, domain_id: str) -> Dict[str, Any]:
    try:
        return fabric.motif_entropy(workspace_id, domain_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/workspace/{workspace_id}/domain/{domain_id}/motif_merges")
def list_motif_merges(workspace_id: str, domain_id: str, status: str = "suggested", limit: int = 200) -> Dict[str, Any]:
    try:
        return fabric.list_motif_merges(workspace_id, domain_id, status=status, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/workspace/motif_merges/decide")
def decide_motif_merge(req: MotifMergeDecideReq) -> Dict[str, Any]:
    try:
        return fabric.decide_motif_merge(req.workspace_id, req.domain_id, req.suggestion_id, req.decision, note=req.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/workspace/{workspace_id}/domain/{domain_id}/conflicts")
def list_conflicts(workspace_id: str, domain_id: str, status: str = "open", limit: int = 200) -> Dict[str, Any]:
    try:
        return fabric.list_conflicts(workspace_id, domain_id, status=status, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/workspace/conflicts/decide")
def decide_conflict(req: ConflictDecideReq) -> Dict[str, Any]:
    try:
        return fabric.decide_conflict(req.workspace_id, req.domain_id, req.conflict_id, req.decision, note=req.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ====================================================================
# Archive Memory Endpoints (Phase 2 — separate from core identity)
# ====================================================================
from .archive_memory import ArchiveStore

# Lazy archive store cache (per workspace+agent)
_archive_stores: Dict[str, ArchiveStore] = {}

def _get_archive_store(workspace_id: str, agent_id: str) -> ArchiveStore:
    key = f"{workspace_id}/{agent_id}"
    if key not in _archive_stores:
        archive_dir = os.path.join(
            DATA_DIR, "workspaces", workspace_id, "agents", agent_id, "memory_archive"
        )
        sq_idx = fabric._get_sqlite_index(workspace_id, agent_id)
        _archive_stores[key] = ArchiveStore(
            archive_dir=archive_dir,
            embedder=fabric.kernel.embedder,
            sqlite_index=sq_idx,
        )
    return _archive_stores[key]


class IngestDocumentReq(BaseModel):
    workspace_id: str
    agent_id: str
    text: str
    title: str = "Untitled"
    source_type: str = "text"
    doc_id: Optional[str] = None
    target_tokens: int = 350
    max_tokens: int = 500
    overlap_tokens: int = 60


class ArchiveQueryReq(BaseModel):
    workspace_id: str
    agent_id: str
    query: str
    top_k: int = 5
    min_score: float = 0.0
    doc_id_filter: Optional[str] = None


@app.post("/archive/ingest_document")
def ingest_document(req: IngestDocumentReq) -> Dict[str, Any]:
    """Ingest a document into archive memory (NOT core identity).

    Chunks the text and stores embeddings in the archive lane.
    This never touches motifs, kernel, drift, or character state.
    """
    store = _get_archive_store(req.workspace_id, req.agent_id)
    return store.ingest_document(
        text=req.text,
        title=req.title,
        source_type=req.source_type,
        doc_id=req.doc_id,
        target_tokens=req.target_tokens,
        max_tokens=req.max_tokens,
        overlap_tokens=req.overlap_tokens,
    )


@app.post("/archive/query")
def archive_query(req: ArchiveQueryReq) -> Dict[str, Any]:
    """Query archive memory by cosine similarity (no physics, no identity)."""
    store = _get_archive_store(req.workspace_id, req.agent_id)
    results = store.retrieve(
        query=req.query,
        top_k=req.top_k,
        min_score=req.min_score,
        doc_id_filter=req.doc_id_filter,
    )
    return {"results": results, "count": len(results)}


@app.get("/archive/{workspace_id}/{agent_id}/documents")
def archive_list_documents(workspace_id: str, agent_id: str) -> Dict[str, Any]:
    """List all documents in an agent's archive memory."""
    store = _get_archive_store(workspace_id, agent_id)
    docs = store.list_documents()
    return {"documents": docs, "count": len(docs)}


@app.get("/archive/{workspace_id}/{agent_id}/document/{doc_id}")
def archive_get_document(workspace_id: str, agent_id: str, doc_id: str) -> Dict[str, Any]:
    """Get a specific document and its chunks."""
    store = _get_archive_store(workspace_id, agent_id)
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    chunks = store.get_chunks_for_document(doc_id)
    return {"document": doc, "chunks": chunks}


@app.delete("/archive/{workspace_id}/{agent_id}/document/{doc_id}")
def archive_delete_document(workspace_id: str, agent_id: str, doc_id: str) -> Dict[str, Any]:
    """Delete a document from archive memory. Safe — never affects core identity."""
    store = _get_archive_store(workspace_id, agent_id)
    ok = store.delete_document(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    return {"deleted": True, "doc_id": doc_id}


# ====================================================================
# Retrieval Assembler Endpoint (Phase 3 — unified context assembly)
# ====================================================================
from .retrieval_assembler import assemble_context, PROFILES as ASSEMBLER_PROFILES


class AssembleContextReq(BaseModel):
    workspace_id: str
    agent_id: str
    query: str
    profile: str = "companion"
    token_budget: int = 4000
    top_k: int = 8
    archive_top_k: int = 5
    archive_min_score: float = 0.0
    domain_id: Optional[str] = None
    custom_weights: Optional[Dict[str, float]] = None


@app.post("/retrieve")
def retrieve_assembled(req: AssembleContextReq) -> Dict[str, Any]:
    """Retrieve unified context combining core + archive memory.

    Uses the retrieval assembler (Phase 3) to produce a structured
    context object with hard precedence ordering:
      identity → relational → situational → archive

    Archive blocks NEVER outrank identity blocks.
    """
    # 1. Core retrieval (existing fabric.query)
    core_result = fabric.query(
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        query_text=req.query,
        top_k=req.top_k,
        domain_id=req.domain_id,
    )
    core_hits = core_result.get("results", [])

    # 2. Archive retrieval (if archive exists for this agent)
    archive_hits = []
    try:
        store = _get_archive_store(req.workspace_id, req.agent_id)
        if store.chunk_count > 0:
            archive_hits = store.retrieve(
                query=req.query,
                top_k=req.archive_top_k,
                min_score=req.archive_min_score,
            )
    except Exception:
        archive_hits = []

    # 2b. Track retrieval counts for promotion (Phase 5)
    if archive_hits:
        try:
            from .promotion import increment_retrieval_counts
            _arc_dir = os.path.join(
                DATA_DIR, "workspaces", req.workspace_id,
                "agents", req.agent_id, "memory_archive",
            )
            _ret_ids = [h.get("chunk_id") for h in archive_hits if h.get("chunk_id")]
            increment_retrieval_counts(_arc_dir, _ret_ids)
        except Exception:
            pass

    # 3. Load seed text and drift info for identity context
    seed_text = ""
    character_name = ""
    drift_info = None
    char_ctx = core_result.get("character_context")
    if char_ctx:
        seed_text = str(char_ctx.get("seed_preamble") or "")
        character_name = str(char_ctx.get("character_name") or "")
        drift_info = {
            "drift_score": float(char_ctx.get("drift_score", 0.0)),
            "drift_direction": str(char_ctx.get("drift_direction", "stable")),
            "explanation": str(char_ctx.get("drift_summary") or ""),
        }

    # 4. Assemble context with hard precedence
    assembled = assemble_context(
        core_hits=core_hits,
        archive_hits=archive_hits,
        profile=req.profile,
        token_budget=req.token_budget,
        seed_text=seed_text,
        character_name=character_name,
        drift_info=drift_info,
        custom_weights=req.custom_weights,
    )

    return assembled.to_dict()


@app.get("/retrieve/profiles")
def list_retrieval_profiles() -> Dict[str, Any]:
    """List available retrieval assembler profiles and their weights."""
    return {"profiles": ASSEMBLER_PROFILES}


# ====================================================================
# SQLite Sidecar Index Endpoints (Phase 4 — fast metadata lookup)
# ====================================================================

@app.get("/index/{workspace_id}/{agent_id}/recent")
def index_recent_memories(workspace_id: str, agent_id: str, limit: int = 20) -> Dict[str, Any]:
    """Fast recent memory lookup from the SQLite sidecar index."""
    idx = fabric._get_sqlite_index(workspace_id, agent_id)
    if not idx or not idx.available:
        return {"ok": False, "detail": "SQLite index not available", "results": []}
    results = idx.get_recent_memories(limit=limit)
    return {"ok": True, "results": results, "count": len(results)}


@app.get("/index/{workspace_id}/{agent_id}/motif/{motif_id}")
def index_memories_by_motif(workspace_id: str, agent_id: str, motif_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get memories belonging to a specific motif from the sidecar index."""
    idx = fabric._get_sqlite_index(workspace_id, agent_id)
    if not idx or not idx.available:
        return {"ok": False, "detail": "SQLite index not available", "results": []}
    results = idx.get_memories_by_motif(motif_id, limit=limit)
    return {"ok": True, "results": results, "count": len(results)}


@app.get("/index/{workspace_id}/{agent_id}/trajectory")
def index_trajectory_range(
    workspace_id: str, agent_id: str,
    step_from: int = 0, step_to: int = 999999, limit: int = 1000,
) -> Dict[str, Any]:
    """Get trajectory snapshots for a step range from the sidecar index."""
    idx = fabric._get_sqlite_index(workspace_id, agent_id)
    if not idx or not idx.available:
        return {"ok": False, "detail": "SQLite index not available", "results": []}
    results = idx.get_trajectory_range(step_from, step_to, limit=limit)
    return {"ok": True, "results": results, "count": len(results)}


@app.get("/index/{workspace_id}/{agent_id}/events")
def index_events_by_type(
    workspace_id: str, agent_id: str,
    event_type: str = "", limit: int = 100,
) -> Dict[str, Any]:
    """Get events by type from the sidecar index."""
    idx = fabric._get_sqlite_index(workspace_id, agent_id)
    if not idx or not idx.available:
        return {"ok": False, "detail": "SQLite index not available", "results": []}
    results = idx.get_events_by_type(event_type, limit=limit)
    return {"ok": True, "results": results, "count": len(results)}


@app.get("/index/{workspace_id}/{agent_id}/archive/search")
def index_archive_search(workspace_id: str, agent_id: str, q: str = "", limit: int = 20) -> Dict[str, Any]:
    """Search archive documents by title from the sidecar index."""
    idx = fabric._get_sqlite_index(workspace_id, agent_id)
    if not idx or not idx.available:
        return {"ok": False, "detail": "SQLite index not available", "results": []}
    results = idx.search_archive_metadata(q, limit=limit)
    return {"ok": True, "results": results, "count": len(results)}


@app.get("/index/{workspace_id}/{agent_id}/stats")
def index_stats(workspace_id: str, agent_id: str) -> Dict[str, Any]:
    """Get stats about the SQLite sidecar index."""
    idx = fabric._get_sqlite_index(workspace_id, agent_id)
    if not idx or not idx.available:
        return {"ok": False, "detail": "SQLite index not available"}
    return {"ok": True, **idx.get_index_stats()}


class RebuildIndexReq(BaseModel):
    workspace_id: str
    agent_id: str


@app.post("/index/rebuild")
def index_rebuild(req: RebuildIndexReq) -> Dict[str, Any]:
    """Rebuild the SQLite sidecar index from canonical JSONL sources.

    Safe to run at any time — the index is disposable and rebuildable.
    """
    idx = fabric._get_sqlite_index(req.workspace_id, req.agent_id)
    if not idx or not idx.available:
        return {"ok": False, "detail": "SQLite index not available"}

    # Locate canonical source files
    agent_dir = os.path.join(DATA_DIR, "workspaces", req.workspace_id, "agents", req.agent_id)
    private_dir = os.path.join(agent_dir, "private")
    archive_dir = os.path.join(agent_dir, "memory_archive")

    counts = idx.rebuild_from_jsonl(
        nodes_path=os.path.join(private_dir, "nodes.jsonl"),
        events_path=os.path.join(private_dir, "memory_events.jsonl"),
        trajectories_path=os.path.join(private_dir, "trajectories.jsonl"),
        archive_documents_path=os.path.join(archive_dir, "documents.jsonl"),
        archive_chunks_path=os.path.join(archive_dir, "chunks.jsonl"),
    )

    return {"ok": True, "rebuilt": counts}


# ====================================================================
# Phase 5 — Checkpoint + Promotion endpoints
# ====================================================================

# --- Checkpoints ---

class CheckpointSaveReq(BaseModel):
    workspace_id: str
    agent_id: str

@app.post("/checkpoint/save")
def checkpoint_save(req: CheckpointSaveReq) -> Dict[str, Any]:
    """Manually trigger a checkpoint save for an agent."""
    from .checkpoint import (
        save_checkpoint, get_checkpoint_dir,
        build_motif_summary, build_shard_snapshot,
    )
    from dataclasses import asdict

    state = fabric.agent_states.get(req.agent_id)
    if state is None:
        raise HTTPException(404, f"Agent '{req.agent_id}' has no active state")

    step = int(getattr(state, "step", 0))
    ckpt_dir = get_checkpoint_dir(DATA_DIR, req.workspace_id, req.agent_id)

    # Gather optional context
    motif_summary = None
    try:
        ws = fabric.get_workspace(req.workspace_id)
        for reg in ws.motif_regs.values():
            motif_summary = build_motif_summary(reg)
            break
    except Exception:
        pass

    shard_snap = None
    try:
        emb_dir = os.path.join(
            DATA_DIR, "workspaces", req.workspace_id,
            "agents", req.agent_id, "private", "embeddings",
        )
        shard_snap = build_shard_snapshot(emb_dir)
    except Exception:
        pass

    char_state_dict = None
    try:
        cstate = fabric.character_store.load_state(req.workspace_id, req.agent_id)
        if cstate:
            char_state_dict = asdict(cstate)
    except Exception:
        pass

    path = save_checkpoint(
        checkpoint_dir=ckpt_dir,
        step=step,
        model_state=state,
        corridor_monitor=fabric.kernel.mon,
        character_state_dict=char_state_dict,
        motif_summary=motif_summary,
        shard_snapshot=shard_snap,
    )
    return {"ok": path is not None, "step": step, "path": path}


@app.get("/checkpoint/{workspace_id}/{agent_id}/latest")
def checkpoint_latest(workspace_id: str, agent_id: str) -> Dict[str, Any]:
    """Load and return the latest checkpoint metadata."""
    from .checkpoint import load_latest_checkpoint, get_checkpoint_dir

    ckpt_dir = get_checkpoint_dir(DATA_DIR, workspace_id, agent_id)
    data = load_latest_checkpoint(ckpt_dir)
    if data is None:
        return {"ok": False, "detail": "No checkpoints found"}
    # Return metadata only — not the full state arrays
    return {
        "ok": True,
        "step": data.get("step"),
        "timestamp_iso": data.get("timestamp_iso"),
        "has_model_state": "model_state" in data,
        "has_corridor_monitor": "corridor_monitor" in data,
        "has_character_state": data.get("character_state") is not None,
        "motif_summary": data.get("motif_summary"),
        "shard_snapshot": data.get("shard_snapshot"),
    }


@app.get("/checkpoint/{workspace_id}/{agent_id}/list")
def checkpoint_list(workspace_id: str, agent_id: str) -> Dict[str, Any]:
    """List all available checkpoints for an agent."""
    from .checkpoint import get_checkpoint_dir, _extract_step_from_filename
    import glob as _glob

    ckpt_dir = get_checkpoint_dir(DATA_DIR, workspace_id, agent_id)
    if not os.path.isdir(ckpt_dir):
        return {"ok": True, "checkpoints": []}

    files = sorted(_glob.glob(os.path.join(ckpt_dir, "checkpoint_*.json")))
    items = []
    for f in files:
        step = _extract_step_from_filename(f)
        try:
            size = os.path.getsize(f)
        except Exception:
            size = 0
        items.append({"step": step, "file": os.path.basename(f), "size_bytes": size})
    return {"ok": True, "checkpoints": items}


# --- Promotion ---

class PromoteReq(BaseModel):
    workspace_id: str
    agent_id: str
    chunk_id: str
    force: bool = False   # skip evaluation, force promote
    step: int = 0

@app.post("/promote")
def promote_chunk_endpoint(req: PromoteReq) -> Dict[str, Any]:
    """Evaluate and optionally promote an archive chunk to core memory."""
    from .promotion import (
        evaluate_promotion, promote_chunk,
        load_retrieval_counts,
    )

    # Get archive store
    archive_dir = os.path.join(
        DATA_DIR, "workspaces", req.workspace_id,
        "agents", req.agent_id, "memory_archive",
    )
    store = _get_archive_store(req.workspace_id, req.agent_id)
    if store is None:
        raise HTTPException(404, "Archive store not found")

    # Find the chunk
    chunk = store._chunks.get(req.chunk_id)
    if chunk is None:
        raise HTTPException(404, f"Chunk '{req.chunk_id}' not found")

    chunk_text = chunk.text or ""
    doc_id = chunk.doc_id or ""

    # Gather evaluation inputs
    retrieval_counts = load_retrieval_counts(archive_dir)
    ret_count = retrieval_counts.get(req.chunk_id, 0)

    chunk_emb = store._chunk_embeddings.get(req.chunk_id)
    seed_emb = None
    try:
        ident = fabric.ident_store.load(req.workspace_id, req.agent_id)
        if ident:
            seed_id = str(ident.seed.get("seed_id", "") or "")
            if seed_id:
                cseed = fabric.character_store.load_seed(req.workspace_id, seed_id)
                if cseed and cseed.seed_eids:
                    graph = fabric.private_graphs.get(req.agent_id)
                    if graph:
                        embs = []
                        for seid in cseed.seed_eids[:5]:
                            ent = graph.entities.get(int(seid))
                            if ent and hasattr(ent, "embedding") and ent.embedding is not None:
                                embs.append(ent.embedding)
                        if embs:
                            import numpy as np
                            seed_emb = np.mean(embs, axis=0)
    except Exception:
        pass

    # Evaluate
    result = evaluate_promotion(
        chunk_text=chunk_text,
        chunk_id=req.chunk_id,
        is_canon=bool(req.force),
        retrieval_count=ret_count,
        chunk_embedding=chunk_emb,
        seed_embedding=seed_emb,
        user_approved=bool(req.force),
    )

    # Execute promotion if approved
    promoted_eid = None
    if result.promote or req.force:
        graph = fabric.private_graphs.get(req.agent_id)
        if graph is None:
            # Ensure agent is initialized
            fabric.create_agent(req.workspace_id, req.agent_id)
            graph = fabric.private_graphs.get(req.agent_id)

        if graph:
            promoted_eid = promote_chunk(
                chunk_id=req.chunk_id,
                chunk_text=chunk_text,
                doc_id=doc_id,
                memory_graph=graph,
                embedder=fabric.kernel.embedder,
                step=req.step,
            )

    return {
        "ok": True,
        "evaluation": result.to_dict(),
        "promoted_eid": promoted_eid,
    }


@app.get("/promote/suggestions/{workspace_id}/{agent_id}")
def promote_suggestions(
    workspace_id: str,
    agent_id: str,
    max_suggestions: int = 10,
) -> Dict[str, Any]:
    """Scan archive chunks and return top promotion candidates."""
    from .promotion import suggest_promotions, load_retrieval_counts

    archive_dir = os.path.join(
        DATA_DIR, "workspaces", workspace_id,
        "agents", agent_id, "memory_archive",
    )
    store = _get_archive_store(workspace_id, agent_id)
    if store is None:
        return {"ok": True, "suggestions": []}

    retrieval_counts = load_retrieval_counts(archive_dir)

    # Get seed embedding if available
    seed_emb = None
    try:
        ident = fabric.ident_store.load(workspace_id, agent_id)
        if ident:
            seed_id = str(ident.seed.get("seed_id", "") or "")
            if seed_id:
                cseed = fabric.character_store.load_seed(workspace_id, seed_id)
                if cseed and cseed.seed_eids:
                    graph = fabric.private_graphs.get(agent_id)
                    if graph:
                        import numpy as np
                        embs = []
                        for seid in cseed.seed_eids[:5]:
                            ent = graph.entities.get(int(seid))
                            if ent and hasattr(ent, "embedding") and ent.embedding is not None:
                                embs.append(ent.embedding)
                        if embs:
                            seed_emb = np.mean(embs, axis=0)
    except Exception:
        pass

    suggestions = suggest_promotions(
        archive_store=store,
        seed_embedding=seed_emb,
        retrieval_counts=retrieval_counts,
        max_suggestions=max_suggestions,
    )
    return {"ok": True, "suggestions": suggestions}


# ---------------------------------------------------------------------------
# Event-Gated Compression endpoints (Phase 6)
# ---------------------------------------------------------------------------

class CompressTriggerRequest(BaseModel):
    workspace_id: str
    agent_id: str
    step: int

@app.post("/workspace/{workspace_id}/compress/trigger")
async def trigger_compression(workspace_id: str, req: CompressTriggerRequest):
    """Manual compression trigger. Bypasses event detection, runs scorer+router+executor."""
    if not fabric._compress_enable:
        return {"ok": False, "error": "compression disabled (set TORMENT_COMPRESS_ENABLE=1)"}
    try:
        from .compression import (
            CompressionScorer, CompressionRouter, CompressionExecutor,
            _get_or_create_deep_store, _find_motifs_path, _log_compression_event,
        )
        from .coherence_field import compute_coherence_field as _ccf

        graph = fabric.private_graphs.get(req.agent_id)
        if graph is None:
            raise HTTPException(status_code=404, detail=f"No private graph for agent {req.agent_id}")

        deep_store = _get_or_create_deep_store(fabric, req.agent_id)

        # Load coherence field
        coherence_field = None
        try:
            mp = _find_motifs_path(fabric, req.agent_id)
            if mp and os.path.exists(mp):
                with open(mp, "r", encoding="utf-8") as f:
                    md = json.load(f)
                if isinstance(md, dict):
                    md = md.get("motifs", [])
                coherence_field = _ccf(md)
        except Exception:
            pass

        nodes = []
        for eid, ent in graph.entities.items():
            nodes.append({
                "eid": int(eid),
                "born_step": int(getattr(ent, "born_step", 0) or 0),
                "payload": dict(ent.payload or {}),
            })

        scorer = CompressionScorer()
        candidates = scorer.select_candidates(nodes, req.step, coherence_field)

        if not candidates:
            return {"ok": True, "message": "no compression candidates", "compressed": 0, "exported": 0}

        router = CompressionRouter()
        router.route_all(candidates, req.step)

        executor = CompressionExecutor(graph, deep_store)
        event = executor.execute(candidates, req.step, "manual")

        _log_compression_event(fabric, req.agent_id, event)
        fabric._compression_executors[req.agent_id] = executor

        return {
            "ok": True,
            "compressed": event.compressed,
            "exported_deep": event.exported_deep,
            "retained": event.retained,
            "candidates_evaluated": event.candidates_evaluated,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/workspace/{workspace_id}/compress/status")
async def compression_status(workspace_id: str, agent_id: str):
    """Returns compression history, deep memory stats, event detector state."""
    result: Dict[str, Any] = {
        "enabled": fabric._compress_enable,
        "min_step": fabric._compress_min_step,
    }

    # Event detector state
    detector = fabric._event_detectors.get(agent_id)
    if detector:
        result["detector"] = detector.state_dict()
    else:
        result["detector"] = None

    # Compression history
    executor = fabric._compression_executors.get(agent_id)
    if executor:
        result["history"] = executor.get_history()
    else:
        result["history"] = []

    # Deep memory stats
    deep_store = fabric._deep_stores.get(agent_id)
    if deep_store:
        result["deep_memory"] = deep_store.stats()
    else:
        result["deep_memory"] = None

    return result


class DeepMemoryQueryRequest(BaseModel):
    workspace_id: str
    agent_id: str
    text: str
    top_k: int = 5

@app.get("/workspace/{workspace_id}/spirit-return/status")
async def spirit_return_status(workspace_id: str, agent_id: str):
    """Warmup tracker stats + last return info for an agent."""
    from pathlib import Path
    result: Dict[str, Any] = {"agent_id": agent_id, "workspace_id": workspace_id}

    # Warmup tracker stats
    try:
        from .spirit_return import WarmupTracker
        warmup_dir = Path(DATA_DIR) / "workspaces" / workspace_id / "agents" / agent_id / "warmup"
        tracker = WarmupTracker(warmup_dir)
        result["warmup"] = tracker.stats()
    except Exception as exc:
        result["warmup"] = None
        result["warmup_error"] = str(exc)

    # Deep memory stats (for context)
    deep_store = fabric._deep_stores.get(agent_id)
    if deep_store is not None:
        try:
            result["deep_memory"] = deep_store.stats()
        except Exception:
            result["deep_memory"] = None
    else:
        result["deep_memory"] = None

    return result


@app.post("/workspace/{workspace_id}/deep-memory/query")
async def deep_memory_query(workspace_id: str, req: DeepMemoryQueryRequest):
    """Direct query against deep memory store. For debugging/research."""
    deep_store = fabric._deep_stores.get(req.agent_id)
    if deep_store is None:
        return {"ok": True, "results": [], "message": "no deep memory store for this agent"}

    try:
        q_emb = fabric.kernel.embedder.embed(req.text)
        q_vec = __import__("numpy").asarray(q_emb, dtype=__import__("numpy").float32).reshape(-1)
        hits = deep_store.query(q_vec, top_k=req.top_k)
        return {
            "ok": True,
            "results": [h.to_dict() for h in hits],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))