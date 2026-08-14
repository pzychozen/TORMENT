# incident_log.py — Structured Spine incident log for TORMENT
#
# Records every Spine decision in a ring buffer for observability.
# Not a persistent database — this is a lightweight in-memory log
# with an optional file-append mode for post-mortem analysis.
#
# Design:
#   - Ring buffer (default 500 entries) so memory stays bounded
#   - Each entry captures the full decision context
#   - Queryable by operation, decision_code, time range, agent
#   - Thread-safe (uses the same locking model as Spine)
#   - Optional file append to {data_dir}/spine_incidents.jsonl
#
# Usage:
#   from .incident_log import incident_log, log_spine_decision
#   log_spine_decision(response, request, context)
#   recent = incident_log.query(decision_code="blocked_insufficient_trust", limit=10)
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections.abc import Mapping
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger("torment.incidents")

# ---------------------------------------------------------------------------
# Incident record
# ---------------------------------------------------------------------------

@dataclass
class SpineIncident:
    """A single Spine decision record for observability."""
    timestamp: float
    operation: str
    decision_code: str
    result_code: str
    ok: bool
    workspace_id: str
    agent_id: str
    trust_tier: float
    drift_status: str
    path: str                           # "fast" | "full" | "none"
    elapsed_ms: float
    escalated: bool = False
    escalation_reasons: List[str] = field(default_factory=list)
    reason: str = ""                    # non-empty for blocks/errors
    client_id: str = ""
    session_id: str = ""
    task_id: str = ""
    operation_ok: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_failure(self) -> bool:
        """True if Spine blocked/errored or its handler explicitly failed."""
        return not self.ok or not self.operation_ok or \
               self.decision_code.startswith("blocked_") or \
               self.decision_code.startswith("error_")


# ---------------------------------------------------------------------------
# Incident log — ring buffer with query support
# ---------------------------------------------------------------------------

class IncidentLog:
    """Thread-safe ring buffer of Spine incidents.

    Args:
        max_size: Maximum number of incidents to retain (default 500).
        file_path: Optional path to append incidents as JSONL for persistence.
    """

    def __init__(self, max_size: int = 500, file_path: Optional[str] = None):
        self._buffer: Deque[SpineIncident] = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._file_path = file_path
        self._total_logged: int = 0
        self._total_failures: int = 0

    def record(self, incident: SpineIncident) -> None:
        """Record a new incident."""
        with self._lock:
            self._buffer.append(incident)
            self._total_logged += 1
            if incident.is_failure():
                self._total_failures += 1

        # File append (best-effort, never blocks)
        if self._file_path:
            try:
                with open(self._file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(incident.to_dict(), default=str) + "\n")
            except Exception:
                pass  # observability must never crash the system

    def query(
        self,
        *,
        limit: int = 20,
        operation: Optional[str] = None,
        decision_code: Optional[str] = None,
        ok: Optional[bool] = None,
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        since: Optional[float] = None,
        failures_only: bool = False,
    ) -> List[SpineIncident]:
        """Query the incident log with optional filters.

        Returns most recent matching incidents first.
        """
        with self._lock:
            candidates = list(self._buffer)

        # Most recent first
        candidates.reverse()

        results: List[SpineIncident] = []
        for inc in candidates:
            if len(results) >= limit:
                break
            if operation and inc.operation != operation:
                continue
            if decision_code and inc.decision_code != decision_code:
                continue
            if ok is not None and inc.ok != ok:
                continue
            if workspace_id and inc.workspace_id != workspace_id:
                continue
            if agent_id and inc.agent_id != agent_id:
                continue
            if since and inc.timestamp < since:
                continue
            if failures_only and not inc.is_failure():
                continue
            results.append(inc)

        return results

    def summary(self) -> Dict[str, Any]:
        """Return aggregate stats for the status surface."""
        with self._lock:
            items = list(self._buffer)

        if not items:
            return {
                "total_logged": self._total_logged,
                "total_failures": self._total_failures,
                "buffer_size": 0,
                "recent_decisions": {},
                "recent_blocks": [],
            }

        # Count decision codes
        decision_counts: Dict[str, int] = {}
        block_list: List[Dict[str, Any]] = []
        for inc in reversed(items):
            decision_counts[inc.decision_code] = decision_counts.get(inc.decision_code, 0) + 1
            if inc.is_failure() and len(block_list) < 10:
                block_list.append({
                    "timestamp": inc.timestamp,
                    "operation": inc.operation,
                    "decision_code": inc.decision_code,
                    "reason": inc.reason,
                    "workspace_id": inc.workspace_id,
                    "agent_id": inc.agent_id,
                    "trust_tier": inc.trust_tier,
                })

        return {
            "total_logged": self._total_logged,
            "total_failures": self._total_failures,
            "buffer_size": len(items),
            "oldest_timestamp": items[0].timestamp,
            "newest_timestamp": items[-1].timestamp,
            "recent_decisions": decision_counts,
            "recent_blocks": block_list,
        }

    def clear(self) -> None:
        """Clear the buffer (for testing)."""
        with self._lock:
            self._buffer.clear()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

# Initialized lazily; call init_incident_log() to set file path
_incident_log: Optional[IncidentLog] = None
_log_lock = threading.Lock()


def get_incident_log(file_path: Optional[str] = None) -> IncidentLog:
    """Get or create the module-level incident log singleton.

    File persistence is enabled by either:
      - Passing file_path explicitly on first call
      - Setting the TORMENT_MCP_INCIDENT_LOG environment variable

    The env var is checked only during singleton creation (first call).
    """
    global _incident_log
    if _incident_log is None:
        with _log_lock:
            if _incident_log is None:
                resolved_path = file_path or os.environ.get("TORMENT_MCP_INCIDENT_LOG")
                if resolved_path:
                    logger.info("Incident log persistence enabled: %s", resolved_path)
                _incident_log = IncidentLog(file_path=resolved_path)
    return _incident_log


def log_spine_decision(
    resp,   # SpineResponse (duck-typed to avoid circular import)
    req,    # SpineRequest
    ctx,    # RequestContext
) -> None:
    """Record a Spine decision in the incident log.

    Call this at the end of submit_task() to capture every decision.
    """
    log = get_incident_log()
    result = getattr(resp, "result", None)
    operation_ok = not (
        isinstance(result, Mapping)
        and result.get("ok") is False
    )
    incident = SpineIncident(
        timestamp=time.time(),
        operation=resp.operation,
        decision_code=resp.decision_code,
        result_code=resp.result_code,
        ok=resp.ok,
        workspace_id=resp.workspace_id,
        agent_id=resp.agent_id,
        trust_tier=resp.trust_tier,
        drift_status=resp.drift_status,
        path=resp.path,
        elapsed_ms=resp.elapsed_ms,
        escalated=resp.escalated,
        escalation_reasons=list(resp.escalation_reasons),
        reason=resp.reason,
        client_id=getattr(ctx, "client_id", ""),
        session_id=getattr(ctx, "session_id", ""),
        task_id=resp.task_id,
        operation_ok=operation_ok,
    )
    log.record(incident)

    # Log failures at WARNING level for stderr visibility
    if incident.is_failure():
        logger.warning(
            "INCIDENT | %s | %s | %s | ws=%s agent=%s trust=%.1f | %s",
            incident.decision_code, incident.operation, incident.result_code,
            incident.workspace_id, incident.agent_id, incident.trust_tier,
            incident.reason,
        )
