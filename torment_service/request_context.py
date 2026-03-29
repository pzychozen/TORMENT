# request_context.py — Caller identity and trust for every TORMENT operation
#
# Every external request MUST carry a RequestContext. This is the bridge
# between MCP/HTTP authentication and TORMENT's internal governance.
#
# Trust tiers control what operations a caller may perform:
#   0.0  read-only (query, trace, inspect)
#   0.3  query + light reinforce (feedback)
#   0.6  ingest (memory writes)
#   0.9  collective actions (reingest, proposals)
#   1.0  operator-level (governance flags, compression, decisions)
#
# The Spine checks trust_tier before dispatching any operation.
# Fabric itself does NOT check trust — it is a pure execution layer.
# ---------------------------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time


# ---------------------------------------------------------------------------
# Trust tier constants
# ---------------------------------------------------------------------------

TRUST_READ_ONLY = 0.0
TRUST_QUERY_REINFORCE = 0.3
TRUST_INGEST = 0.6
TRUST_COLLECTIVE = 0.9
TRUST_OPERATOR = 1.0

# Operation -> minimum trust tier required
OPERATION_TRUST_REQUIREMENTS: Dict[str, float] = {
    # Read-only operations
    "query": TRUST_READ_ONLY,
    "trace": TRUST_READ_ONLY,
    "inspect": TRUST_READ_ONLY,
    "memory_chain": TRUST_READ_ONLY,
    "collective_status": TRUST_READ_ONLY,
    "agent_state": TRUST_READ_ONLY,
    "debug_metrics": TRUST_READ_ONLY,
    # Light write operations
    "feedback": TRUST_QUERY_REINFORCE,
    "reinforce": TRUST_QUERY_REINFORCE,
    # Memory writes
    "ingest": TRUST_INGEST,
    "archive_ingest": TRUST_INGEST,
    "promote": TRUST_INGEST,
    "propose_share": TRUST_INGEST,
    # Collective actions
    "collective_reingest": TRUST_COLLECTIVE,
    "process_proposals": TRUST_COLLECTIVE,
    # Operator-level
    "governance_set": TRUST_OPERATOR,
    "compress_trigger": TRUST_OPERATOR,
    "proposals_decide": TRUST_OPERATOR,
    "motif_merges_decide": TRUST_OPERATOR,
    "bridges_decide": TRUST_OPERATOR,
    "conflicts_decide": TRUST_OPERATOR,
    "workspace_create": TRUST_OPERATOR,
    "agent_create": TRUST_OPERATOR,
}


# ---------------------------------------------------------------------------
# RequestContext
# ---------------------------------------------------------------------------

@dataclass
class RequestContext:
    """Caller identity and authorization for a single TORMENT request.

    Created by the auth middleware from the incoming HTTP/MCP request.
    Passed through the Spine to Fabric. Every write operation must
    carry one.

    Attributes:
        client_id:      Authenticated caller identifier (from API key lookup).
        trust_tier:     Numeric trust level (0.0 - 1.0). Controls which
                        operations the caller may perform.
        workspace_id:   Target workspace for this request.
        agent_id:       Target agent for this request (may be None for
                        workspace-level operations).
        session_id:     Optional session identifier for request grouping
                        and audit correlation.
        timestamp:      When this context was created (epoch seconds).
        metadata:       Arbitrary caller-provided metadata for audit trail.
    """

    client_id: str
    trust_tier: float
    workspace_id: str
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        # Clamp trust tier to valid range
        self.trust_tier = max(0.0, min(1.0, self.trust_tier))

    def check_trust(self, operation: str) -> bool:
        """Return True if this context has sufficient trust for the operation."""
        required = OPERATION_TRUST_REQUIREMENTS.get(operation, TRUST_OPERATOR)
        return self.trust_tier >= required

    def require_trust(self, operation: str) -> None:
        """Raise if this context lacks trust for the operation.

        Call this at the top of any governed endpoint.
        """
        required = OPERATION_TRUST_REQUIREMENTS.get(operation, TRUST_OPERATOR)
        if self.trust_tier < required:
            raise InsufficientTrustError(
                client_id=self.client_id,
                operation=operation,
                required=required,
                actual=self.trust_tier,
            )

    def to_audit_dict(self) -> Dict[str, Any]:
        """Minimal dict for inclusion in audit trail entries."""
        d: Dict[str, Any] = {
            "client_id": self.client_id,
            "trust_tier": self.trust_tier,
            "workspace_id": self.workspace_id,
            "timestamp": self.timestamp,
        }
        if self.agent_id:
            d["agent_id"] = self.agent_id
        if self.session_id:
            d["session_id"] = self.session_id
        return d


# ---------------------------------------------------------------------------
# Internal / bypass context for system-initiated operations
# ---------------------------------------------------------------------------

def system_context(workspace_id: str, agent_id: Optional[str] = None) -> RequestContext:
    """Create a full-trust context for internal system operations.

    Used by compression, spirit return, auto-reingest, and other
    system-initiated operations that don't originate from an external caller.
    """
    return RequestContext(
        client_id="__system__",
        trust_tier=TRUST_OPERATOR,
        workspace_id=workspace_id,
        agent_id=agent_id,
        session_id=None,
        metadata={"origin": "system"},
    )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class InsufficientTrustError(Exception):
    """Raised when a caller's trust tier is too low for an operation."""

    def __init__(self, client_id: str, operation: str, required: float, actual: float):
        self.client_id = client_id
        self.operation = operation
        self.required = required
        self.actual = actual
        super().__init__(
            f"Client '{client_id}' has trust {actual:.1f}, "
            f"but operation '{operation}' requires {required:.1f}"
        )
