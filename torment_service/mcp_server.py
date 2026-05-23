# mcp_server.py — MCP v1 stdio server for TORMENT
#
# This is the MCP protocol face of the TORMENT Spine. It exposes governed
# operations as MCP tools and read-only state as MCP resources.
#
# Architecture:
#   MCP SDK (stdio) → mcp_server.py → SpineRequest/RequestContext → Spine → Fabric
#
# The MCP server NEVER touches Fabric directly. All writes go through the Spine.
# All reads go through Spine-backed helpers or read-safe Fabric wrappers.
#
# Run:
#   python -m torment_service.mcp_server
#
# Configuration (environment variables):
#   TORMENT_MCP_DATA_DIR      — Fabric data directory (default: ./data)
#   TORMENT_MCP_CLIENT_ID     — MCP client identity (default: "mcp_client")
#   TORMENT_MCP_TRUST_TIER    — Trust tier for this session (default: 0.6)
#   TORMENT_MCP_WORKSPACE_ID  — Default workspace (default: "default")
#   TORMENT_MCP_AGENT_ID      — Default agent (default: "default")
#   TORMENT_MCP_EXPOSURE_TIER — Max exposure tier: open|guarded (default: "open")
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .request_context import RequestContext
from .spine import (
    SpineRequest,
    submit_task,
    get_exposed_operations,
    exposure_allows,
    EXPOSURE_OPEN,
    EXPOSURE_GUARDED,
)
from .fabric import TormentFabric
from .lifecycle import LifecycleStateError, read_lifecycle_envelope
from .scoring import derive_provenance_type as _derive_prov_type

logger = logging.getLogger("torment.mcp")


# ---------------------------------------------------------------------------
# Q2-H1b: lifecycle envelope read-side wiring helper.
#
# Per docs/CLUSTER_5_PATH_C_Q2_LIFECYCLE_IMPLEMENTATION_FRAMING_v0.1.md, the
# first production read-site for the Q2 lifecycle envelope is the guarded
# `resource_provenance` MCP resource. This helper is the per-row computation:
#
#   * Legacy rows (no ``lifecycle_status`` on the payload) lazily resolve to
#     the canonical row-authoritative UNSET envelope via the H1a shim
#     ``read_lifecycle_envelope`` -- ``LifecycleActor.MIGRATION`` /
#     ``LifecycleSetVia.UNSET_DEFAULT``.
#   * Valid envelopes round-trip through ``.to_dict()``.
#   * Malformed envelopes MUST NOT be silently downgraded to UNSET (that
#     would let a corrupt envelope masquerade as a legacy row and violate
#     the Q2 invariant). Instead, the validation failure is surfaced inline
#     as an error sentinel for that row only, so a single corrupt envelope
#     does not break the entire inspector view -- this is the appropriate
#     UX for an operator/debug observability surface.
#
# The shim never mutates the payload. The helper is read-only and is not
# wired into any decision-bearing path; lifecycle enforcement, protected
# dual-source collapse, and review-queue join formalization are deferred
# to later Q2 slices (Q2-F / Q2-D / Q2-E).
# ---------------------------------------------------------------------------


def _lifecycle_field_for_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compute the ``lifecycle_status`` field for one memory row in the
    Q2-H1b provenance inspector wiring.

    Returns either the canonical lifecycle envelope dict (5 keys: ``state``,
    ``is_authoritative_on_row``, ``requires_join``, ``set_by``,
    ``history_ref``) or an inline error sentinel of shape
    ``{"error": "<field>: <reason>"}`` if the row carries a malformed
    envelope.
    """
    try:
        return read_lifecycle_envelope(payload).to_dict()
    except LifecycleStateError as exc:
        return {"error": f"{exc.field}: {exc.reason}"}


# ---------------------------------------------------------------------------
# MCP client context — maps MCP session identity into RequestContext
# ---------------------------------------------------------------------------

@dataclass
class MCPClientContext:
    """Represents the identity of an MCP client session.

    Configured from environment variables at server startup.
    Every tool invocation builds a proper RequestContext from this.
    """
    client_id: str = "mcp_client"
    trust_tier: float = 0.6
    default_workspace_id: str = "default"
    default_agent_id: str = "default"
    session_id: str = ""
    transport: str = "stdio"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.session_id:
            import uuid
            self.session_id = f"mcp_{uuid.uuid4().hex[:8]}"

    def to_request_context(
        self,
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> RequestContext:
        """Build a RequestContext for a single tool invocation."""
        return RequestContext(
            client_id=self.client_id,
            trust_tier=self.trust_tier,
            workspace_id=workspace_id or self.default_workspace_id,
            agent_id=agent_id or self.default_agent_id,
            session_id=self.session_id,
            metadata={"transport": self.transport, **self.metadata},
        )


def _load_client_context() -> MCPClientContext:
    """Load MCPClientContext from environment variables.

    If TORMENT_MCP_WORKSPACE_ID or TORMENT_MCP_AGENT_ID are not set,
    defaults are empty strings. This makes the missing-context check in
    torment_submit_task actually trigger, rather than silently falling
    back to a "default" workspace that may not exist.
    """
    ctx = MCPClientContext(
        client_id=os.environ.get("TORMENT_MCP_CLIENT_ID", "mcp_client"),
        trust_tier=float(os.environ.get("TORMENT_MCP_TRUST_TIER", "0.6")),
        default_workspace_id=os.environ.get("TORMENT_MCP_WORKSPACE_ID", ""),
        default_agent_id=os.environ.get("TORMENT_MCP_AGENT_ID", ""),
        transport="stdio",
    )
    if not ctx.default_workspace_id:
        logger.warning("TORMENT_MCP_WORKSPACE_ID not set — tools will require explicit workspace_id")
    if not ctx.default_agent_id:
        logger.warning("TORMENT_MCP_AGENT_ID not set — tools will require explicit agent_id")
    return ctx


# ---------------------------------------------------------------------------
# Fabric singleton — initialized once at server startup
# ---------------------------------------------------------------------------

_fabric: Optional[TormentFabric] = None
_client_ctx: Optional[MCPClientContext] = None


def _get_fabric() -> TormentFabric:
    global _fabric
    if _fabric is None:
        data_dir = os.environ.get("TORMENT_MCP_DATA_DIR", "./data")
        _fabric = TormentFabric(data_dir=data_dir)
        logger.info("TORMENT Fabric initialized (data_dir=%s)", data_dir)
    return _fabric


def _get_client_ctx() -> MCPClientContext:
    global _client_ctx
    if _client_ctx is None:
        _client_ctx = _load_client_context()
        logger.info(
            "MCP client context: client_id=%s trust=%.1f ws=%s agent=%s session=%s",
            _client_ctx.client_id,
            _client_ctx.trust_tier,
            _client_ctx.default_workspace_id,
            _client_ctx.default_agent_id,
            _client_ctx.session_id,
        )
    return _client_ctx


# ---------------------------------------------------------------------------
# Helper: execute a Spine operation and return formatted result
# ---------------------------------------------------------------------------

def _spine_call(
    operation: str,
    payload: Dict[str, Any],
    workspace_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    mode: str = "auto",
) -> Dict[str, Any]:
    """Execute a governed Spine operation and return the full envelope.

    This is the single authority path for all MCP tool invocations.
    Returns a blocked_mcp_missing_context response if workspace/agent
    cannot be resolved from args or defaults.
    """
    fabric = _get_fabric()
    client = _get_client_ctx()

    # Resolve workspace/agent — fail early if unresolvable
    resolved_ws = workspace_id or client.default_workspace_id
    resolved_agent = agent_id or client.default_agent_id
    if not resolved_ws or not resolved_agent:
        missing = []
        if not resolved_ws:
            missing.append("workspace_id")
        if not resolved_agent:
            missing.append("agent_id")
        return {
            "ok": False,
            "reason": f"Missing required context: {', '.join(missing)}. "
                      "Provide them as arguments or set TORMENT_MCP_WORKSPACE_ID / "
                      "TORMENT_MCP_AGENT_ID environment variables.",
            "decision_code": "blocked_mcp_missing_context",
            "result_code": "none",
        }

    ctx = client.to_request_context(
        workspace_id=workspace_id,
        agent_id=agent_id,
    )

    req = SpineRequest(
        workspace_id=ctx.workspace_id,
        agent_id=ctx.agent_id,
        operation=operation,
        payload=payload,
        mode=mode,
    )

    logger.info(
        "MCP tool call: op=%s ws=%s agent=%s mode=%s",
        operation, ctx.workspace_id, ctx.agent_id, mode,
    )

    resp = submit_task(req, fabric, ctx)

    # Log decision/result for observability
    logger.info(
        "MCP result: op=%s decision=%s result=%s ok=%s elapsed=%.1fms",
        resp.operation, resp.decision_code, resp.result_code,
        resp.ok, resp.elapsed_ms,
    )

    return resp.to_dict()


# ---------------------------------------------------------------------------
# Build the MCP server
# ---------------------------------------------------------------------------

def create_mcp_server() -> FastMCP:
    """Create and configure the TORMENT MCP server.

    Tools and resources are registered based on the exposure tier policy
    in the Spine operation registry. The MCP surface is a projection of
    Spine policy, not a separate policy system.
    """
    mcp = FastMCP(
        name="torment-memory",
        instructions=(
            "TORMENT Memory Fabric — a geometric memory system for AI agents. "
            "Use torment_submit_task for full control, or use convenience tools "
            "like torment_ingest, torment_query_memory, etc. for common operations. "
            "All writes are governed by the Agent Spine with trust enforcement, "
            "drift monitoring, and auto-escalation."
        ),
    )

    # Determine exposure ceiling from config
    max_tier = os.environ.get("TORMENT_MCP_EXPOSURE_TIER", "open")
    exposed_ops = get_exposed_operations(max_tier)

    _guarded_ok = exposure_allows(EXPOSURE_GUARDED, max_tier)
    logger.info(
        "MCP server exposing %d operations (tier ceiling=%s): %s",
        len(exposed_ops), max_tier, sorted(exposed_ops.keys()),
    )
    logger.info(
        "MCP resource gating: guarded resources %s (tier ceiling=%s)",
        "enabled" if _guarded_ok else "hidden", max_tier,
    )

    # -----------------------------------------------------------------------
    # Canonical tool: torment_submit_task
    # -----------------------------------------------------------------------

    @mcp.tool(
        name="torment_submit_task",
        description=(
            "Submit a governed task to the TORMENT Agent Spine. "
            "This is the canonical write interface for all memory operations. "
            "The Spine enforces trust tiers, per-agent serialization, "
            "drift monitoring, and auto-escalation. "
            f"Available operations: {', '.join(sorted(exposed_ops.keys()))}. "
            "Returns a governed response envelope with decision_code, result_code, "
            "drift_status, and audit metadata."
        ),
    )
    def torment_submit_task(
        operation: str,
        workspace_id: str = "",
        agent_id: str = "",
        payload: str = "{}",
        mode: str = "auto",
    ) -> str:
        """Submit a governed task to the TORMENT Spine.

        Args:
            operation: Operation name (e.g. "ingest", "query_memory")
            workspace_id: Target workspace (uses default if empty)
            agent_id: Target agent (uses default if empty)
            payload: JSON string with operation-specific parameters
            mode: Routing mode — "auto" (recommended), "fast", or "full"

        Returns:
            JSON string with the governed response envelope.
        """
        # Validate operation is exposed
        if operation not in exposed_ops:
            available = sorted(exposed_ops.keys())
            return json.dumps({
                "ok": False,
                "reason": f"Operation '{operation}' is not available via MCP. "
                          f"Available: {available}",
                "decision_code": "blocked_mcp_not_exposed",
                "result_code": "none",
            })

        try:
            parsed_payload = json.loads(payload) if isinstance(payload, str) else payload
        except json.JSONDecodeError as e:
            return json.dumps({
                "ok": False,
                "reason": f"Invalid payload JSON: {e}",
                "decision_code": "blocked_mcp_invalid_payload",
                "result_code": "none",
            })

        # Check that we can resolve workspace/agent context
        client = _get_client_ctx()
        resolved_ws = workspace_id or client.default_workspace_id
        resolved_agent = agent_id or client.default_agent_id
        if not resolved_ws or not resolved_agent:
            missing = []
            if not resolved_ws:
                missing.append("workspace_id")
            if not resolved_agent:
                missing.append("agent_id")
            return json.dumps({
                "ok": False,
                "reason": f"Missing required context: {', '.join(missing)}. "
                          "Provide them as arguments or set TORMENT_MCP_WORKSPACE_ID / "
                          "TORMENT_MCP_AGENT_ID environment variables.",
                "decision_code": "blocked_mcp_missing_context",
                "result_code": "none",
            })

        result = _spine_call(
            operation=operation,
            payload=parsed_payload,
            workspace_id=workspace_id or None,
            agent_id=agent_id or None,
            mode=mode,
        )
        return json.dumps(result, default=str)

    # -----------------------------------------------------------------------
    # Convenience tools — generated from Tier 1 exposed operations
    # -----------------------------------------------------------------------

    # Only generate convenience tools for "open" tier operations
    open_ops = get_exposed_operations(EXPOSURE_OPEN)

    # --- torment_ingest ---
    if "ingest" in open_ops:
        @mcp.tool(
            name="torment_ingest",
            description=(
                "Ingest text as new memory for an agent. "
                "The text is processed through the geometric memory kernel, "
                "assigned an embedding, and stored in the agent's private graph. "
                "Governed by the Spine with trust enforcement and drift monitoring."
            ),
        )
        def torment_ingest(
            text: str,
            workspace_id: str = "",
            agent_id: str = "",
            domain_id: str = "",
            step: int = 0,
            scope: str = "private",
        ) -> str:
            """Ingest text as new memory.

            Args:
                text: The text content to memorize
                workspace_id: Target workspace (uses default if empty)
                agent_id: Target agent (uses default if empty)
                domain_id: Optional domain classification
                step: Simulation step number (0 for external input)
                scope: "private" or "shared"
            """
            payload: Dict[str, Any] = {"text": text, "step": step, "scope": scope}
            if domain_id:
                payload["domain_id"] = domain_id
            result = _spine_call("ingest", payload,
                                 workspace_id=workspace_id or None,
                                 agent_id=agent_id or None)
            return json.dumps(result, default=str)

    # --- torment_query_memory ---
    if "query_memory" in open_ops:
        @mcp.tool(
            name="torment_query_memory",
            description=(
                "Search an agent's memory using semantic similarity. "
                "Returns the most relevant memories ranked by the geometric "
                "kernel. Read-only operation with auto-escalation for "
                "identity-sensitive queries."
            ),
        )
        def torment_query_memory(
            query: str,
            workspace_id: str = "",
            agent_id: str = "",
            top_k: int = 8,
            domain_id: str = "",
            explain: bool = False,
        ) -> str:
            """Search agent memory.

            Args:
                query: Natural language search query
                workspace_id: Target workspace (uses default if empty)
                agent_id: Target agent (uses default if empty)
                top_k: Maximum results to return (default 8)
                domain_id: Optional domain filter
                explain: Include retrieval explanations
            """
            payload: Dict[str, Any] = {"query": query, "top_k": top_k, "explain": explain}
            if domain_id:
                payload["domain_id"] = domain_id
            result = _spine_call("query_memory", payload,
                                 workspace_id=workspace_id or None,
                                 agent_id=agent_id or None)
            return json.dumps(result, default=str)

    # --- torment_query_state ---
    if "query_state" in open_ops:
        @mcp.tool(
            name="torment_query_state",
            description=(
                "Read an agent's current state snapshot. Returns identity, "
                "character drift score, memory count, and compression status. "
                "Read-only, no trust requirement."
            ),
        )
        def torment_query_state(
            workspace_id: str = "",
            agent_id: str = "",
        ) -> str:
            """Read agent state snapshot.

            Args:
                workspace_id: Target workspace (uses default if empty)
                agent_id: Target agent (uses default if empty)
            """
            result = _spine_call("query_state", {},
                                 workspace_id=workspace_id or None,
                                 agent_id=agent_id or None)
            return json.dumps(result, default=str)

    # --- torment_feedback ---
    if "feedback" in open_ops:
        @mcp.tool(
            name="torment_feedback",
            description=(
                "Provide reinforcement feedback on previously retrieved memories. "
                "Pass the memory IDs and indicate whether they were useful and/or "
                "confirmed correct. This shapes future retrieval ranking."
            ),
        )
        def torment_feedback(
            memory_ids: str = "[]",
            useful: bool = True,
            confirmed: bool = False,
            contradicted: bool = False,
            workspace_id: str = "",
            agent_id: str = "",
        ) -> str:
            """Provide reinforcement feedback.

            Args:
                memory_ids: JSON array of memory IDs (ints) from retrieval results
                useful: Were these memories useful in the response?
                confirmed: Did the user confirm these memories are correct?
                contradicted: Were any of these memories contradicted?
                workspace_id: Target workspace (uses default if empty)
                agent_id: Target agent (uses default if empty)
            """
            try:
                ids = json.loads(memory_ids)
            except json.JSONDecodeError as e:
                return json.dumps({"ok": False, "reason": f"Invalid JSON in memory_ids: {e}"})

            # Map simplified interface to canonical Spine payload
            payload = {
                "retrieved_ids": ids,
                "used_successfully": ids if useful else [],
                "user_confirmed": ids if confirmed else [],
                "contradiction_detected": ids if contradicted else [],
            }

            result = _spine_call("feedback", payload,
                                 workspace_id=workspace_id or None,
                                 agent_id=agent_id or None)
            return json.dumps(result, default=str)

    # --- torment_reinforce ---
    if "reinforce" in open_ops:
        @mcp.tool(
            name="torment_reinforce",
            description=(
                "Directly reinforce specific memories. "
                "Similar to feedback but for direct reinforcement signals."
            ),
        )
        def torment_reinforce(
            retrieved_ids: str = "[]",
            used_successfully: str = "[]",
            workspace_id: str = "",
            agent_id: str = "",
        ) -> str:
            """Directly reinforce memories.

            Args:
                retrieved_ids: JSON array of memory IDs to reinforce
                used_successfully: JSON array of successfully used memory IDs
                workspace_id: Target workspace (uses default if empty)
                agent_id: Target agent (uses default if empty)
            """
            try:
                payload = {
                    "retrieved_ids": json.loads(retrieved_ids),
                    "used_successfully": json.loads(used_successfully),
                }
            except json.JSONDecodeError as e:
                return json.dumps({"ok": False, "reason": f"Invalid JSON: {e}"})

            result = _spine_call("reinforce", payload,
                                 workspace_id=workspace_id or None,
                                 agent_id=agent_id or None)
            return json.dumps(result, default=str)

    # --- torment_tool_result_ingest (guarded tier) ---
    if "tool_result_ingest" in exposed_ops:
        @mcp.tool(
            name="torment_tool_result_ingest",
            description=(
                "Store externally obtained tool output as governed memory. "
                "This is memory storage, not tool execution — TORMENT remembers "
                "what tools returned, it does not call tools. "
                "Provenance-tagged with source_type='tool_result'. "
                "Governed by the Spine with trust enforcement."
            ),
        )
        def torment_tool_result_ingest(
            tool_name: str,
            content: str,
            workspace_id: str = "",
            agent_id: str = "",
            summary: str = "",
            step: int = 0,
            domain_id: str = "",
            session_id: str = "",
            scope: str = "private",
        ) -> str:
            """Ingest tool output as governed memory.

            Args:
                tool_name: Identity of the tool that produced this output
                content: Raw tool output to store as memory
                workspace_id: Target workspace (uses default if empty)
                agent_id: Target agent (uses default if empty)
                summary: Optional short summary (auto-generated if empty)
                step: Simulation step number (0 for external input)
                domain_id: Optional domain classification
                session_id: Optional session identifier for provenance
                scope: "private" (default) or "shared"
            """
            payload: Dict[str, Any] = {
                "tool_name": tool_name,
                "content": content,
                "step": step,
                "scope": scope,
            }
            if summary:
                payload["summary"] = summary
            if domain_id:
                payload["domain_id"] = domain_id
            if session_id:
                payload["session_id"] = session_id
            result = _spine_call("tool_result_ingest", payload,
                                 workspace_id=workspace_id or None,
                                 agent_id=agent_id or None)
            return json.dumps(result, default=str)

    # -----------------------------------------------------------------------
    # Resources — read-only views, gated by exposure tier
    #
    # Policy:
    #   open    — basic telemetry (agent state, collective status, memory summary)
    #   guarded — sensitive debug/admin (provenance inspection, cross-agent admin)
    #
    # Uses the same exposure_allows() helper that governs tool registration.
    # -----------------------------------------------------------------------

    @mcp.resource(
        uri="torment://workspace/{workspace_id}/agent/{agent_id}/state",
        name="Agent State",
        description=(
            "Read-only snapshot of an agent's current state: identity, "
            "character drift, memory count, compression status."
        ),
        mime_type="application/json",
    )
    def resource_agent_state(workspace_id: str, agent_id: str) -> str:
        """Read agent state through the Spine's governed read path."""
        result = _spine_call(
            "query_state", {},
            workspace_id=workspace_id,
            agent_id=agent_id,
        )
        # Return just the result payload, not the full envelope
        if result.get("ok"):
            return json.dumps(result.get("result", {}), indent=2, default=str)
        return json.dumps({"error": result.get("reason", "Unknown error")})

    @mcp.resource(
        uri="torment://workspace/{workspace_id}/agent/{agent_id}/memory-summary",
        name="Memory Summary",
        description=(
            "Summary of an agent's memory: recent ingestions, memory count, "
            "active motifs, and drift status."
        ),
        mime_type="application/json",
    )
    def resource_memory_summary(workspace_id: str, agent_id: str) -> str:
        """Read a summary of agent memory through Spine-backed helpers."""
        fabric = _get_fabric()

        summary: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
        }

        # Memory count from query_state
        state_result = _spine_call("query_state", {},
                                   workspace_id=workspace_id,
                                   agent_id=agent_id)
        if state_result.get("ok"):
            state_data = state_result.get("result", {})
            summary["memory_count"] = state_data.get("memory_count", 0)
            summary["character"] = state_data.get("character")
            summary["compression"] = state_data.get("compression")

        # Drift status from envelope
        summary["drift_status"] = state_result.get("drift_status", "unknown")

        # Active motifs (read-safe, no Spine write involved)
        try:
            ws = fabric.get_workspace(workspace_id)
            if ws and ws.motif_regs:
                motif_summary = {}
                for domain_id, reg in ws.motif_regs.items():
                    active = reg.active(top_k=5)
                    if active:
                        motif_summary[domain_id] = active
                if motif_summary:
                    summary["active_motifs"] = motif_summary
        except Exception as e:
            logger.debug("Motif summary skipped: %s", e)

        return json.dumps(summary, indent=2, default=str)

    # --- Guarded resource: admin/status (cross-agent aggregate, internal observability) ---
    if exposure_allows(EXPOSURE_GUARDED, max_tier):
        @mcp.resource(
            uri="torment://admin/status",
            name="Spine Admin Status",
            description=(
                "[Guarded] Cross-agent administrative view: active agents, "
                "recent Spine decisions, blocks, escalations, and drift summary. "
                "Exposes internal operational state — requires guarded exposure tier."
            ),
            mime_type="application/json",
        )
        def resource_admin_status() -> str:
            """Cross-agent admin status — guarded exposure tier required."""
            from .incident_log import get_incident_log

            fabric = _get_fabric()
            log = get_incident_log()
            result: Dict[str, Any] = {"ok": True, "timestamp": time.time()}

            # Incident summary
            result["incidents"] = log.summary()

            # Recent failures
            recent_failures = log.query(failures_only=True, limit=10)
            result["recent_failures"] = [f.to_dict() for f in recent_failures]

            # Recent escalations
            recent_all = log.query(limit=50)
            escalations = [i.to_dict() for i in recent_all if i.escalated][:10]
            result["recent_escalations"] = escalations

            # Active agents
            agents = []
            for key in fabric.agent_states:
                # Canonical format is "workspace/agent"; legacy ":" is fallback.
                if "/" in key:
                    ws, ag = key.split("/", 1)
                elif ":" in key:
                    ws, ag = key.split(":", 1)
                else:
                    ws, ag = "unknown", key
                drift_score = 0.0
                try:
                    cstate = fabric.character_store.load_state(ws, ag)
                    if cstate:
                        drift_score = float(cstate.drift_score)
                except Exception as e:
                    logger.debug("Character state load skipped: %s", e)
                mem_count = 0
                try:
                    graph = fabric.private_graphs.get(key)
                    if graph:
                        mem_count = len(graph.entities)
                except Exception as e:
                    logger.debug("Graph entity count skipped: %s", e)
                agents.append({
                    "workspace_id": ws, "agent_id": ag,
                    "memory_count": mem_count,
                    "drift_score": round(drift_score, 4),
                    "drift_status": "green" if abs(drift_score) < 0.10 else
                                   "yellow" if abs(drift_score) < 0.20 else "red",
                })
            result["agents"] = agents
            result["agent_count"] = len(agents)

            return json.dumps(result, indent=2, default=str)

    @mcp.resource(
        uri="torment://workspace/{workspace_id}/collective/status",
        name="Collective Status",
        description=(
            "Read-only view of the hive-mind collective state for a workspace: "
            "convergence events, proposal status, and shared graph summary."
        ),
        mime_type="application/json",
    )
    def resource_collective_status(workspace_id: str) -> str:
        """Read collective status through read-safe Fabric wrappers."""
        fabric = _get_fabric()

        status: Dict[str, Any] = {"workspace_id": workspace_id}

        try:
            ws = fabric.get_workspace(workspace_id)

            # Shared graphs
            status["shared_domains"] = list(ws.shared_graphs.keys())

            # Agents in workspace (canonical "ws/agent" key format)
            agents = []
            _ws_prefix = f"{workspace_id}/"
            for key in fabric.agent_states:
                if key.startswith(_ws_prefix):
                    agents.append(key[len(_ws_prefix):])
            status["agents"] = agents
            status["agent_count"] = len(agents)

            # Bridges
            try:
                bridge_info = fabric.list_bridges(
                    workspace_id=workspace_id, status="any", limit=50)
                status["bridges"] = {
                    "total": bridge_info.get("count", 0),
                    "by_status": bridge_info.get("by_status", {}),
                }
            except Exception:
                status["bridges"] = {"total": 0}

            # Collective field (if it exists)
            cf = fabric._collective_fields.get(workspace_id)
            if cf is not None:
                status["collective_field"] = {
                    "convergence_events": getattr(cf, "event_count", 0),
                    "last_convergence_step": getattr(cf, "last_step", 0),
                }

            # Hivemind enabled flag
            status["hivemind_enabled"] = os.environ.get(
                "TORMENT_HIVEMIND_ENABLE", "0") == "1"

        except Exception as e:
            status["error"] = str(e)

        return json.dumps(status, indent=2, default=str)

    # --- Guarded resource: provenance (exposes memory text, debug/verification) ---
    if exposure_allows(EXPOSURE_GUARDED, max_tier):
        @mcp.resource(
            uri="torment://workspace/{workspace_id}/agent/{agent_id}/provenance",
            name="Provenance Inspector",
            description=(
                "[Guarded] Debug/verification view of recent memory provenance. "
                "Exposes source_type, write_path, source_role, and truncated "
                "memory text for each memory. Use to verify that tool-result "
                "ingest, user ingest, and collective operations are tagged "
                "correctly. Requires guarded exposure tier."
            ),
            mime_type="application/json",
        )
        def resource_provenance(workspace_id: str, agent_id: str) -> str:
            """Read-only provenance inspection — guarded exposure tier required."""
            fabric = _get_fabric()
            limit = 50

            memories: List[Dict[str, Any]] = []
            ak = fabric._agent_key(workspace_id, agent_id)
            graph = fabric.private_graphs.get(ak)

            if graph is not None and hasattr(graph, "entities"):
                for eid, entity in graph.entities.items():
                    payload = entity.payload or {}
                    prov = payload.get("provenance")
                    # Derive compact classification BEFORE legacy normalization
                    _prov_type = _derive_prov_type(prov)
                    # Normalize legacy string provenance for safe .get() access.
                    # Legacy bare string (e.g. "collective") is a pre-ProvenanceV1 artifact —
                    # normalize to SOURCE_MEMORY with the raw value preserved in `notes` so
                    # the read-path vocabulary stays inside VALID_SOURCE_TYPES
                    # (provenance_v1.py). Display-only; no writeback uses this dict.
                    if prov and not isinstance(prov, dict):
                        _legacy_raw = str(prov)
                        prov = {
                            "source_type": "memory",  # SOURCE_MEMORY
                            "notes": f"legacy_bare_string={_legacy_raw!r}",
                        }
                    # Q2-H1b: per-row lifecycle envelope. See module-level
                    # ``_lifecycle_field_for_payload`` for the contract.
                    # Surfaced as an additional read-only field; does not
                    # affect any existing key, sort order, limit, or the
                    # exposure tier gate.
                    memories.append({
                        "eid": eid,
                        "agent_id": agent_id,
                        "scope": "private",
                        "provenance_type": _prov_type,
                        "summary": (
                            (payload.get("summary") or str(payload.get("text", ""))[:120])
                            if payload else ""
                        ),
                        "provenance": prov,
                        "has_provenance": prov is not None,
                        "created_step": payload.get("step"),
                        "lifecycle_status": _lifecycle_field_for_payload(payload),
                    })

            # Most recent first
            memories.sort(key=lambda m: m["eid"], reverse=True)
            memories = memories[:limit]

            # Summary stats
            total = len(memories)
            with_prov = sum(1 for m in memories if m["has_provenance"])
            by_source_type: Dict[str, int] = {}
            by_write_path: Dict[str, int] = {}
            for m in memories:
                p = m.get("provenance")
                if p and isinstance(p, dict):
                    st = p.get("source_type", "unknown")
                    wp = p.get("write_path", "unknown")
                    by_source_type[st] = by_source_type.get(st, 0) + 1
                    by_write_path[wp] = by_write_path.get(wp, 0) + 1

            result: Dict[str, Any] = {
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "stats": {
                    "total_inspected": total,
                    "with_provenance": with_prov,
                    "without_provenance": total - with_prov,
                    "by_source_type": by_source_type,
                    "by_write_path": by_write_path,
                },
                "memories": memories,
            }
            return json.dumps(result, indent=2, default=str)

    return mcp


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main():
    """Run the TORMENT MCP server over stdio."""
    import sys
    # CRITICAL: all logging must go to stderr, NOT stdout.
    # MCP uses stdout exclusively for JSON-RPC protocol messages.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        stream=sys.stderr,
    )

    # Pre-initialize fabric and context so errors surface early
    _get_fabric()
    client = _get_client_ctx()

    logger.info("Starting TORMENT MCP server (stdio)")
    logger.info("Session: %s | Trust: %.1f | Workspace: %s | Agent: %s",
                client.session_id, client.trust_tier,
                client.default_workspace_id, client.default_agent_id)

    mcp = create_mcp_server()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
