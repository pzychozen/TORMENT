# spine.py — Dual-lane governed authority layer for TORMENT
#
# The Spine is the single governed entrypoint for all meaningful external
# actions. It sits between the MCP/HTTP boundary and the Fabric execution
# layer.
#
# Two internal paths:
#   FAST  — routine structured operations (ingest, query, feedback, etc.)
#           Does: trust check, routing, locking, invariant checks, dispatch,
#           audit envelope. No multi-role cognition.
#
#   FULL  — complex reasoning (identity rewrites, policy changes, reviews)
#           Routes through the existing 4-role cognition pipeline
#           (Interpreter → Engineer → Skeptic → Archivist).
#
# Public surface:
#   POST /spine/submit_task  →  SpineRequest  →  SpineResponse
#
# Internal dispatch:
#   spine.submit_task(request, fabric, request_context) → SpineResponse
#
# Design rule:
#   Fabric NEVER receives direct external calls for write operations.
#   Everything goes through: Spine → then Fabric.
# ---------------------------------------------------------------------------
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional

from .request_context import (
    RequestContext,
    InsufficientTrustError,
    system_context,
    TRUST_READ_ONLY,
    TRUST_QUERY_REINFORCE,
    TRUST_INGEST,
    TRUST_COLLECTIVE,
    TRUST_OPERATOR,
)
from .incident_log import log_spine_decision

logger = logging.getLogger("torment.spine")


# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

PATH_FAST = "fast"
PATH_FULL = "full"

MODE_FAST = "fast"
MODE_FULL = "full"
MODE_AUTO = "auto"
VALID_MODES = frozenset({MODE_FAST, MODE_FULL, MODE_AUTO})

# Operation classes — stable groupings for policy, logging, and MCP exposure
OP_CLASS_READ = "read"              # read-only queries, no state mutation
OP_CLASS_WRITE = "write"            # creates or modifies individual agent memory
OP_CLASS_COLLECTIVE = "collective"  # cross-agent / hive-mind operations
OP_CLASS_IDENTITY = "identity"      # modifies agent seed, character, or identity
OP_CLASS_COGNITIVE = "cognitive"    # full multi-role cognition pipeline
VALID_OP_CLASSES = frozenset({
    OP_CLASS_READ, OP_CLASS_WRITE, OP_CLASS_COLLECTIVE,
    OP_CLASS_IDENTITY, OP_CLASS_COGNITIVE,
})

# MCP exposure tiers — controls what the MCP transport layer can expose
EXPOSURE_OPEN = "open"          # Tier 1: exposed to any authenticated MCP client
EXPOSURE_GUARDED = "guarded"    # Tier 2: exposed only with elevated trust / explicit config
EXPOSURE_INTERNAL = "internal"  # Tier 3: never exposed through MCP in v1
VALID_EXPOSURE_TIERS = frozenset({EXPOSURE_OPEN, EXPOSURE_GUARDED, EXPOSURE_INTERNAL})


# ---------------------------------------------------------------------------
# Operation registry — which path, what trust, what it does
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OperationSpec:
    """Declares a governed operation and its routing policy."""
    name: str
    default_path: str           # "fast" or "full"
    min_trust: float            # minimum trust_tier to execute
    op_class: str = ""          # read | write | collective | identity | cognitive
    exposure_tier: str = EXPOSURE_INTERNAL  # open | guarded | internal
    can_escalate: bool = False  # can auto-escalate from fast → full
    description: str = ""


# Always-fast operations
_ALWAYS_FAST = [
    OperationSpec("ingest",               PATH_FAST, TRUST_INGEST,
                  op_class=OP_CLASS_WRITE, exposure_tier=EXPOSURE_OPEN,
                  can_escalate=True,
                  description="Ingest text as new memory"),
    OperationSpec("feedback",             PATH_FAST, TRUST_QUERY_REINFORCE,
                  op_class=OP_CLASS_WRITE, exposure_tier=EXPOSURE_OPEN,
                  description="Provide reinforcement feedback on query results"),
    OperationSpec("reinforce",            PATH_FAST, TRUST_QUERY_REINFORCE,
                  op_class=OP_CLASS_WRITE, exposure_tier=EXPOSURE_OPEN,
                  description="Directly reinforce a memory"),
    OperationSpec("collective_reingest",  PATH_FAST, TRUST_COLLECTIVE,
                  op_class=OP_CLASS_COLLECTIVE, exposure_tier=EXPOSURE_GUARDED,
                  can_escalate=True,
                  description="Re-ingest convergence event as echo"),
    OperationSpec("memory_governance_set", PATH_FAST, TRUST_OPERATOR,
                  op_class=OP_CLASS_WRITE, exposure_tier=EXPOSURE_GUARDED,
                  description="Update governance flags on a memory"),
    OperationSpec("query_state",          PATH_FAST, TRUST_READ_ONLY,
                  op_class=OP_CLASS_READ, exposure_tier=EXPOSURE_OPEN,
                  description="Read agent state / identity / character"),
    OperationSpec("query_memory",         PATH_FAST, TRUST_READ_ONLY,
                  op_class=OP_CLASS_READ, exposure_tier=EXPOSURE_OPEN,
                  can_escalate=True,
                  description="Search agent memory"),
    OperationSpec("compression_run",      PATH_FAST, TRUST_OPERATOR,
                  op_class=OP_CLASS_WRITE, exposure_tier=EXPOSURE_GUARDED,
                  description="Trigger compression cycle"),
]

# Always-full operations
_ALWAYS_FULL = [
    OperationSpec("cognition_run",            PATH_FULL, TRUST_INGEST,
                  op_class=OP_CLASS_COGNITIVE, exposure_tier=EXPOSURE_GUARDED,
                  description="Run full 4-role cognition pipeline"),
    OperationSpec("identity_rewrite",         PATH_FULL, TRUST_OPERATOR,
                  op_class=OP_CLASS_IDENTITY, exposure_tier=EXPOSURE_INTERNAL,
                  description="Rewrite agent seed or identity"),
    OperationSpec("seed_change",              PATH_FULL, TRUST_OPERATOR,
                  op_class=OP_CLASS_IDENTITY, exposure_tier=EXPOSURE_INTERNAL,
                  description="Change agent character seed"),
    OperationSpec("collective_policy_change", PATH_FULL, TRUST_OPERATOR,
                  op_class=OP_CLASS_COLLECTIVE, exposure_tier=EXPOSURE_INTERNAL,
                  description="Modify collective policy parameters"),
    OperationSpec("proposal_review",          PATH_FULL, TRUST_COLLECTIVE,
                  op_class=OP_CLASS_COLLECTIVE, exposure_tier=EXPOSURE_INTERNAL,
                  description="Review and decide on proposals"),
    OperationSpec("role_conflict_resolution", PATH_FULL, TRUST_OPERATOR,
                  op_class=OP_CLASS_COGNITIVE, exposure_tier=EXPOSURE_INTERNAL,
                  description="Resolve inter-role conflicts"),
    OperationSpec("architecture_review",      PATH_FULL, TRUST_OPERATOR,
                  op_class=OP_CLASS_COGNITIVE, exposure_tier=EXPOSURE_INTERNAL,
                  description="Full pipeline review of architectural change"),
]

# Build lookup
OPERATION_REGISTRY: Dict[str, OperationSpec] = {}
for _spec in _ALWAYS_FAST + _ALWAYS_FULL:
    OPERATION_REGISTRY[_spec.name] = _spec


def get_exposed_operations(max_tier: str = EXPOSURE_OPEN) -> Dict[str, OperationSpec]:
    """Return operations eligible for MCP exposure at the given tier ceiling.

    Args:
        max_tier: Maximum exposure tier to include.
            "open"     → only Tier 1 operations
            "guarded"  → Tier 1 + Tier 2 operations
            "internal" → all operations (not recommended for MCP)

    Returns:
        Dict of operation name → OperationSpec for operations at or below the tier.
    """
    tier_order = {EXPOSURE_OPEN: 1, EXPOSURE_GUARDED: 2, EXPOSURE_INTERNAL: 3}
    ceiling = tier_order.get(max_tier, 1)
    return {
        name: spec
        for name, spec in OPERATION_REGISTRY.items()
        if tier_order.get(spec.exposure_tier, 3) <= ceiling
    }


# ---------------------------------------------------------------------------
# Escalation policy — when auto mode should escalate fast → full
# ---------------------------------------------------------------------------

def should_escalate(
    operation: str,
    payload: Dict[str, Any],
    ctx: RequestContext,
    drift_score: float = 0.0,
    drift_direction: str = "stable",
) -> bool:
    """Determine if an auto-mode request should escalate from fast to full.

    Returns True if any escalation trigger fires.
    Use escalation_reasons() for structured reason codes.
    """
    return len(escalation_reasons(operation, payload, ctx, drift_score, drift_direction)) > 0


# Structured escalation reason codes
ESCALATION_IDENTITY_SENSITIVE = "identity_sensitive"
ESCALATION_HIGH_DRIFT = "high_drift"
ESCALATION_PROTECTED_MEMORY = "protected_memory"
ESCALATION_BORDERLINE_TRUST = "borderline_trust"
ESCALATION_OPEN_ENDED_REQUEST = "open_ended_request"


def escalation_reasons(
    operation: str,
    payload: Dict[str, Any],
    ctx: RequestContext,
    drift_score: float = 0.0,
    drift_direction: str = "stable",
) -> List[str]:
    """Return a list of structured escalation reason codes.

    Each code explains WHY an auto-mode request should escalate fast → full.
    Returns an empty list if no escalation is needed.

    Possible codes:
      - identity_sensitive:   payload touches seed/canon/identity keywords
      - high_drift:           drift score exceeds 0.20 threshold
      - protected_memory:     protected or canon memory flag in payload
      - borderline_trust:     trust is within 0.1 of the required minimum
      - open_ended_request:   payload looks like open-ended reasoning (long text + question marks)
    """
    spec = OPERATION_REGISTRY.get(operation)
    if spec is None or not spec.can_escalate:
        return []

    reasons: List[str] = []

    # Seed/canon/identity content in payload
    text = str(payload.get("text", "") or payload.get("query", "")).lower()
    if any(kw in text for kw in ("seed", "canon", "identity", "core identity",
                                  "who am i", "character", "rewrite")):
        logger.info("Escalating %s: identity-sensitive content detected", operation)
        reasons.append(ESCALATION_IDENTITY_SENSITIVE)

    # Drift above threshold
    if abs(drift_score) > 0.20:
        logger.info("Escalating %s: drift_score=%.3f exceeds threshold", operation, drift_score)
        reasons.append(ESCALATION_HIGH_DRIFT)

    # Protected memory in payload
    if payload.get("protected") or payload.get("canon"):
        logger.info("Escalating %s: protected/canon memory involved", operation)
        reasons.append(ESCALATION_PROTECTED_MEMORY)

    # Borderline trust (within 0.1 of required, but not exact match)
    trust_margin = ctx.trust_tier - spec.min_trust
    if spec.min_trust > 0 and 0 < trust_margin < 0.1:
        logger.info("Escalating %s: borderline trust (%.1f vs required %.1f)",
                     operation, ctx.trust_tier, spec.min_trust)
        reasons.append(ESCALATION_BORDERLINE_TRUST)

    # Long open-ended text (looks like reasoning, not structured input)
    if len(text) > 500 and text.count("?") >= 2:
        logger.info("Escalating %s: payload looks like open-ended reasoning", operation)
        reasons.append(ESCALATION_OPEN_ENDED_REQUEST)

    return reasons


# ---------------------------------------------------------------------------
# SpineRequest / SpineResponse
# ---------------------------------------------------------------------------

@dataclass
class SpineRequest:
    """Incoming request to the governed Spine layer.

    This is the primary interface for external callers. MCP tools,
    HTTP clients, and future protocol adapters all construct this.
    """
    workspace_id: str
    agent_id: str
    operation: str              # registered operation name
    payload: Dict[str, Any] = field(default_factory=dict)
    mode: str = MODE_AUTO       # "fast" | "full" | "auto"
    task_id: str = ""           # auto-generated if empty
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"spine_{uuid.uuid4().hex[:12]}"
        if self.mode not in VALID_MODES:
            raise ValueError(f"Invalid mode '{self.mode}'. Must be one of: {sorted(VALID_MODES)}")
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class SpineResponse:
    """Governed response envelope from the Spine.

    Every Spine response wraps the Fabric result with governance
    metadata: what path was taken, whether it was allowed, trust
    info, drift status, and audit trail.

    decision_code: structured code describing what the Spine decided to do
        - fast_allowed:              routed to fast path, executed normally
        - full_allowed:              routed to full cognition, executed normally
        - escalated_full:            auto-escalated from fast → full
        - blocked_unknown_operation: operation not in registry
        - blocked_insufficient_trust: caller trust below minimum
        - blocked_no_handler:        no handler in dispatch table
        - error_dispatch:            handler raised an unexpected exception
        - error_trust:               trust error during dispatch

    result_code: structured code describing the outcome of the operation
        - stored:      new memory created (ingest)
        - reinforced:  feedback/reinforcement applied
        - reingested:  collective reingest completed
        - queried:     read-only query returned results
        - governed:    governance flags updated
        - compressed:  compression cycle ran
        - cognition:   full cognition pipeline completed
        - state_read:  agent state snapshot returned
        - none:        no result (blocked or errored)
    """
    ok: bool
    path: str                               # "fast" or "full"
    operation: str
    allowed: bool
    workspace_id: str
    agent_id: str
    trust_tier: float = 0.0
    drift_status: str = "unknown"           # "green" | "yellow" | "red" | "unknown"
    decision_code: str = ""                 # structured governance decision
    result_code: str = ""                   # structured operation outcome
    result: Dict[str, Any] = field(default_factory=dict)
    audit: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""                        # explanation if not allowed or error
    task_id: str = ""
    escalated: bool = False                 # True if auto escalated fast→full
    escalation_reasons: List[str] = field(default_factory=list)  # structured reason codes
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Fast governance path
# ---------------------------------------------------------------------------

def _classify_drift(drift_score: float) -> str:
    """Map numeric drift score to status label."""
    abs_d = abs(drift_score)
    if abs_d < 0.10:
        return "green"
    elif abs_d < 0.20:
        return "yellow"
    else:
        return "red"


def _fast_ingest(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-path ingest: trust-checked, locked, dispatched to Fabric."""
    with fabric.locks.agent_lock(ctx.workspace_id, ctx.agent_id):
        return fabric.ingest(
            workspace_id=ctx.workspace_id,
            agent_id=ctx.agent_id,
            text=payload.get("text", ""),
            step=int(payload.get("step", 0)),
            domain_id=payload.get("domain_id"),
            supplied_summary=payload.get("supplied_summary"),
            supplied_embedding=payload.get("supplied_embedding"),
            scope=payload.get("scope", "private"),
        )


def _fast_feedback(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-path feedback: trust-checked, locked, dispatched to Fabric."""
    with fabric.locks.agent_lock(ctx.workspace_id, ctx.agent_id):
        return fabric.feedback(
            workspace_id=ctx.workspace_id,
            agent_id=ctx.agent_id,
            retrieved_ids=payload.get("retrieved_ids", []),
            used_successfully=payload.get("used_successfully", []),
            user_confirmed=payload.get("user_confirmed", []),
            contradiction_detected=payload.get("contradiction_detected", []),
            novel_motif_created=payload.get("novel_motif_created", False),
            shared_memory_used=payload.get("shared_memory_used", []),
            bridges_used=payload.get("bridges_used", []),
        )


def _fast_collective_reingest(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-path collective reingest: trust-checked, locked, dispatched to Fabric."""
    with fabric.locks.agent_lock(ctx.workspace_id, ctx.agent_id):
        return fabric.reingest_convergence(
            workspace_id=ctx.workspace_id,
            target_agent_id=ctx.agent_id,
            event_id=payload.get("event_id", ""),
            echo_strength_override=payload.get("echo_strength_override"),
        )


def _fast_query_state(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-path query state: read-only agent state snapshot."""
    ws_id = ctx.workspace_id
    agent_id = ctx.agent_id

    result: Dict[str, Any] = {
        "workspace_id": ws_id,
        "agent_id": agent_id,
    }

    # Identity
    try:
        ident = fabric.ident_store.load(ws_id, agent_id)
        if ident:
            result["identity"] = {
                "seed": ident.seed,
                "overlay": ident.overlay,
                "created_ts": ident.created_ts,
                "updated_ts": ident.updated_ts,
            }
    except Exception:
        result["identity"] = None

    # Character state
    try:
        cstate = fabric.character_store.load_state(ws_id, agent_id)
        if cstate:
            result["character"] = {
                "drift_score": float(cstate.drift_score),
                "drift_direction": str(cstate.drift_direction or "stable"),
                "basin": str(getattr(cstate, "basin", "")),
                "seed_id": str(cstate.seed_id or ""),
            }
        else:
            result["character"] = None
    except Exception:
        result["character"] = None

    # Memory count
    try:
        ak = fabric._agent_key(ws_id, agent_id)
        graph = fabric.private_graphs.get(ak)
        if graph:
            result["memory_count"] = len(graph.entities)
        else:
            result["memory_count"] = 0
    except Exception:
        result["memory_count"] = 0

    # Compression status
    try:
        ak = fabric._agent_key(ws_id, agent_id)
        detector = fabric._event_detectors.get(ak)
        if detector:
            result["compression"] = {
                "total_events": getattr(detector, "compression_events_total", 0),
                "last_step": getattr(detector, "last_compression_step", 0),
            }
    except Exception:
        pass

    return result


def _fast_query_memory(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-path query memory: search agent memory, read-only."""
    return fabric.query(
        workspace_id=ctx.workspace_id,
        agent_id=ctx.agent_id,
        query_text=payload.get("query", payload.get("text", "")),
        top_k=int(payload.get("top_k", 8)),
        domain_id=payload.get("domain_id"),
        peek_bridges=bool(payload.get("peek_bridges", False)),
        explain=bool(payload.get("explain", False)),
    )


def _fast_governance_set(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-path governance set: update memory governance flags."""
    from .governance import update_governance, GovernanceAuditLog

    eid = int(payload.get("eid", 0))
    flags = payload.get("flags", {})
    actor = payload.get("actor", ctx.client_id)
    source = payload.get("source", "spine")

    ak = fabric._agent_key(ctx.workspace_id, ctx.agent_id)
    graph = fabric.private_graphs.get(ak)
    if graph is None:
        return {"ok": False, "reason": "Agent graph not found"}

    ent = graph.entities.get(eid)
    if ent is None:
        return {"ok": False, "reason": f"Memory eid={eid} not found"}

    p = ent.payload or {}
    audit_record = update_governance(p, flags, actor=actor, source=source)
    graph.update_payload(eid, p)

    # Workspace audit log (best-effort)
    try:
        import os
        data_dir = fabric.data_dir
        audit_log = GovernanceAuditLog(data_dir=data_dir, workspace_id=ctx.workspace_id)
        audit_log.log(eid=eid, agent_id=ctx.agent_id, changes=audit_record.get("changed", {}),
                      actor=actor, source=source)
    except Exception:
        pass

    return {"ok": True, "eid": eid, "audit": audit_record}


def _fast_compression_run(fabric, ctx: RequestContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-path compression trigger."""
    from .compression import try_compress, check_hard_cap

    step = int(payload.get("step", 0))
    ak = fabric._agent_key(ctx.workspace_id, ctx.agent_id)

    # Get TriOcta modulation for compression
    state = fabric.agent_states.get(ak)
    tri_mod = None
    if state is not None:
        tri_mod = getattr(state, "tri_mod", None)

    result: Dict[str, Any] = {"ok": True}

    with fabric.locks.agent_lock(ctx.workspace_id, ctx.agent_id):
        comp_event = try_compress(fabric, ctx.agent_id, tri_mod, step,
                                  workspace_id=ctx.workspace_id)
        if comp_event and (comp_event.compressed + comp_event.exported_deep) > 0:
            result["compression"] = {
                "compressed": comp_event.compressed,
                "exported_deep": comp_event.exported_deep,
                "trigger": comp_event.trigger,
            }

        hc_event = check_hard_cap(fabric, ctx.agent_id, step,
                                  workspace_id=ctx.workspace_id)
        if hc_event:
            result["hard_cap"] = {
                "compressed": hc_event.compressed,
                "exported_deep": hc_event.exported_deep,
            }

    return result


# Fast dispatch table
FAST_DISPATCH: Dict[str, Callable] = {
    "ingest": _fast_ingest,
    "feedback": _fast_feedback,
    "reinforce": _fast_feedback,           # same handler (feedback = reinforce)
    "collective_reingest": _fast_collective_reingest,
    "memory_governance_set": _fast_governance_set,
    "query_state": _fast_query_state,
    "query_memory": _fast_query_memory,
    "compression_run": _fast_compression_run,
}


# ---------------------------------------------------------------------------
# Full cognition path (delegates to existing pipeline)
# ---------------------------------------------------------------------------

def _full_cognition(fabric, ctx: RequestContext, req: SpineRequest) -> Dict[str, Any]:
    """Full cognition path: delegates to the existing 4-role pipeline."""
    from cognition.task_models import TaskPacket
    from cognition.pipeline import run_cognition_pipeline

    # Build TaskPacket from SpineRequest
    task = TaskPacket(
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        user_input=req.payload.get("text", req.payload.get("query", req.payload.get("user_input", ""))),
        mode=req.payload.get("cognition_mode", "auto"),
        priority=req.payload.get("priority", "normal"),
    )

    # Build query function (wraps fabric.query with aperture)
    def query_fn(ws_id, ag_id, query_text, top_k=8, domain_id=None, **kw):
        return fabric.query(
            workspace_id=ws_id, agent_id=ag_id,
            query_text=query_text, top_k=top_k,
            domain_id=domain_id, **kw,
        )

    # Build character function
    def character_fn(ws_id, ag_id):
        try:
            cstate = fabric.character_store.load_state(ws_id, ag_id)
            if cstate:
                return {
                    "drift_score": float(cstate.drift_score),
                    "drift_direction": str(cstate.drift_direction or "stable"),
                    "seed_id": str(cstate.seed_id or ""),
                }
        except Exception:
            pass
        return {}

    # Run pipeline
    ws = fabric.get_workspace(req.workspace_id)
    primary_domains = list(ws.shared_graphs.keys()) if ws else None

    result = run_cognition_pipeline(
        task=task,
        query_fn=query_fn,
        character_fn=character_fn,
        primary_domains=primary_domains,
    )

    return result


# ---------------------------------------------------------------------------
# Decision and result code constants
# ---------------------------------------------------------------------------

# Decision codes — what the Spine decided to do
DECISION_FAST_ALLOWED = "fast_allowed"
DECISION_FULL_ALLOWED = "full_allowed"
DECISION_ESCALATED_FULL = "escalated_full"
DECISION_BLOCKED_UNKNOWN_OP = "blocked_unknown_operation"
DECISION_BLOCKED_TRUST = "blocked_insufficient_trust"
DECISION_BLOCKED_NO_HANDLER = "blocked_no_handler"
DECISION_ERROR_DISPATCH = "error_dispatch"
DECISION_ERROR_TRUST = "error_trust"

# Result codes — what happened to the data
RESULT_STORED = "stored"
RESULT_REINFORCED = "reinforced"
RESULT_REINGESTED = "reingested"
RESULT_QUERIED = "queried"
RESULT_GOVERNED = "governed"
RESULT_COMPRESSED = "compressed"
RESULT_COGNITION = "cognition"
RESULT_STATE_READ = "state_read"
RESULT_NONE = "none"

# Operation → result code mapping (for successful fast-path dispatch)
_OPERATION_RESULT_CODES: Dict[str, str] = {
    "ingest": RESULT_STORED,
    "feedback": RESULT_REINFORCED,
    "reinforce": RESULT_REINFORCED,
    "collective_reingest": RESULT_REINGESTED,
    "memory_governance_set": RESULT_GOVERNED,
    "query_state": RESULT_STATE_READ,
    "query_memory": RESULT_QUERIED,
    "compression_run": RESULT_COMPRESSED,
}


# ---------------------------------------------------------------------------
# Blocked-action audit logging
# ---------------------------------------------------------------------------

def _audit_blocked(
    req: SpineRequest,
    ctx: RequestContext,
    block_reason: str,
    block_code: str,
) -> None:
    """Log a structured audit event when the Spine blocks an action.

    This provides observability for MCP and external monitoring.
    Block codes:
      - unknown_operation:    operation not in registry
      - insufficient_trust:   caller trust tier below minimum
      - no_fast_handler:      fast dispatch table has no handler
      - dispatch_error:       handler raised an unexpected exception
    """
    logger.warning(
        "SPINE_BLOCKED | code=%s op=%s ws=%s agent=%s client=%s trust=%.2f reason=%s",
        block_code,
        req.operation,
        req.workspace_id,
        req.agent_id,
        ctx.client_id if ctx else "unknown",
        ctx.trust_tier if ctx else 0.0,
        block_reason,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def submit_task(
    req: SpineRequest,
    fabric,
    ctx: RequestContext,
) -> SpineResponse:
    """Primary governed entry point for all meaningful external operations.

    This is the function that POST /spine/submit_task calls.
    MCP tools and future protocol adapters also call this.

    Flow:
      1. Validate operation exists
      2. Check trust tier
      3. Determine path (fast/full/auto)
      4. If auto: check escalation triggers
      5. Acquire locks
      6. Load drift state for audit envelope
      7. Dispatch to fast handler or full cognition
      8. Build governed response envelope
    """
    t0 = time.time()

    # --- 1. Validate operation ---
    spec = OPERATION_REGISTRY.get(req.operation)
    if spec is None:
        reason = f"Unknown operation: {req.operation}"
        _audit_blocked(req, ctx, reason, "unknown_operation")
        resp = SpineResponse(
            ok=False, path="none", operation=req.operation,
            allowed=False, workspace_id=req.workspace_id,
            agent_id=req.agent_id, reason=reason,
            decision_code=DECISION_BLOCKED_UNKNOWN_OP,
            result_code=RESULT_NONE,
            task_id=req.task_id,
        )
        log_spine_decision(resp, req, ctx)
        return resp

    # --- 2. Trust check ---
    if ctx.trust_tier < spec.min_trust:
        reason = f"Insufficient trust: {ctx.trust_tier:.1f} < required {spec.min_trust:.1f}"
        _audit_blocked(req, ctx, reason, "insufficient_trust")
        resp = SpineResponse(
            ok=False, path=spec.default_path, operation=req.operation,
            allowed=False, workspace_id=req.workspace_id,
            agent_id=req.agent_id, trust_tier=ctx.trust_tier,
            reason=reason,
            decision_code=DECISION_BLOCKED_TRUST,
            result_code=RESULT_NONE,
            task_id=req.task_id,
            audit=ctx.to_audit_dict(),
        )
        log_spine_decision(resp, req, ctx)
        return resp

    # --- 3. Determine path ---
    if req.mode == MODE_FAST:
        chosen_path = PATH_FAST
    elif req.mode == MODE_FULL:
        chosen_path = PATH_FULL
    else:
        # Auto: start with operation's default path
        chosen_path = spec.default_path

    # --- 4. Auto-escalation check ---
    escalated = False
    esc_reasons: List[str] = []
    if req.mode == MODE_AUTO and chosen_path == PATH_FAST and spec.can_escalate:
        # Load drift state for escalation decision
        drift_score = 0.0
        drift_direction = "stable"
        try:
            cstate = fabric.character_store.load_state(req.workspace_id, req.agent_id)
            if cstate:
                drift_score = float(cstate.drift_score)
                drift_direction = str(cstate.drift_direction or "stable")
        except Exception:
            pass

        esc_reasons = escalation_reasons(req.operation, req.payload, ctx, drift_score, drift_direction)
        if esc_reasons:
            chosen_path = PATH_FULL
            escalated = True
            logger.info("Auto-escalated %s from fast→full for %s/%s (reasons: %s)",
                        req.operation, req.workspace_id, req.agent_id, ", ".join(esc_reasons))

    # --- 5-6. Load drift for envelope ---
    drift_score = 0.0
    try:
        cstate = fabric.character_store.load_state(req.workspace_id, req.agent_id)
        if cstate:
            drift_score = float(cstate.drift_score)
    except Exception:
        pass
    drift_status = _classify_drift(drift_score)

    # --- 7. Dispatch ---
    try:
        if chosen_path == PATH_FAST:
            handler = FAST_DISPATCH.get(req.operation)
            if handler is None:
                reason = f"No fast handler for operation: {req.operation}"
                _audit_blocked(req, ctx, reason, "no_fast_handler")
                resp = SpineResponse(
                    ok=False, path=PATH_FAST, operation=req.operation,
                    allowed=True, workspace_id=req.workspace_id,
                    agent_id=req.agent_id, trust_tier=ctx.trust_tier,
                    drift_status=drift_status,
                    reason=reason,
                    decision_code=DECISION_BLOCKED_NO_HANDLER,
                    result_code=RESULT_NONE,
                    task_id=req.task_id,
                    audit=ctx.to_audit_dict(),
                )
                log_spine_decision(resp, req, ctx)
                return resp
            result = handler(fabric, ctx, req.payload)
        else:
            # Full cognition path
            result = _full_cognition(fabric, ctx, req)

    except InsufficientTrustError as e:
        _audit_blocked(req, ctx, str(e), "insufficient_trust")
        resp = SpineResponse(
            ok=False, path=chosen_path, operation=req.operation,
            allowed=False, workspace_id=req.workspace_id,
            agent_id=req.agent_id, trust_tier=ctx.trust_tier,
            drift_status=drift_status,
            decision_code=DECISION_ERROR_TRUST,
            result_code=RESULT_NONE,
            reason=str(e), task_id=req.task_id,
            audit=ctx.to_audit_dict(),
        )
        log_spine_decision(resp, req, ctx)
        return resp
    except Exception as e:
        reason = f"{type(e).__name__}: {e}"
        _audit_blocked(req, ctx, reason, "dispatch_error")
        logger.exception("Spine dispatch error for %s", req.operation)
        resp = SpineResponse(
            ok=False, path=chosen_path, operation=req.operation,
            allowed=True, workspace_id=req.workspace_id,
            agent_id=req.agent_id, trust_tier=ctx.trust_tier,
            drift_status=drift_status,
            decision_code=DECISION_ERROR_DISPATCH,
            result_code=RESULT_NONE,
            reason=reason,
            task_id=req.task_id,
            audit=ctx.to_audit_dict(),
        )
        log_spine_decision(resp, req, ctx)
        return resp

    # --- 8. Build response envelope ---
    elapsed = (time.time() - t0) * 1000

    # Determine decision and result codes
    if escalated:
        d_code = DECISION_ESCALATED_FULL
    elif chosen_path == PATH_FAST:
        d_code = DECISION_FAST_ALLOWED
    else:
        d_code = DECISION_FULL_ALLOWED

    if chosen_path == PATH_FULL:
        r_code = RESULT_COGNITION
    else:
        r_code = _OPERATION_RESULT_CODES.get(req.operation, RESULT_NONE)

    resp = SpineResponse(
        ok=True,
        path=chosen_path,
        operation=req.operation,
        allowed=True,
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        trust_tier=ctx.trust_tier,
        drift_status=drift_status,
        decision_code=d_code,
        result_code=r_code,
        result=result,
        audit=ctx.to_audit_dict(),
        task_id=req.task_id,
        escalated=escalated,
        escalation_reasons=esc_reasons,
        elapsed_ms=round(elapsed, 2),
    )
    log_spine_decision(resp, req, ctx)
    return resp
