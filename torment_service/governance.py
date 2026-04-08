# governance.py — Memory governance resolution, enforcement, and audit
#
# Central resolver for MemoryGovernanceFlags. All governance checks should
# go through this module to prevent scattered .get() calls and version-skew
# bugs when older memories lack governance fields.
#
# Conceptual split (per design review):
#
#   SOURCE PROTECTION FLAGS — govern whether private material can leave:
#     - protected:                 immune to automated compression/decay
#     - non_shareable:             exclude from collective packets entirely
#     - collective_export_blocked: don't emit to collective field
#
#   DERIVED/ECHO HANDLING FLAGS — govern synthetic collective material after arrival:
#     - collective_reingest_blocked: don't accept back from collective
#     - decay_accelerated:           faster forgetting (NOT applied if protected=True)
#
# Invariants (must remain true across all future patches):
#   1. Protected memories are never weakened automatically.
#   2. Non-shareable or export-blocked memories never emit packets.
#   3. Collective echoes are terminal by default.
#   4. Collective echoes are influences, not autobiography.
#   5. Collective provenance cannot outrank seed/canon identity by default.
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import os
import time
import threading
from dataclasses import asdict
from typing import Any, Dict, Optional

from .collective_models import MemoryGovernanceFlags
from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


# ---------------------------------------------------------------------------
# Resolver: normalize governance from any payload
# ---------------------------------------------------------------------------

def resolve_governance(payload: Optional[Dict[str, Any]] = None) -> MemoryGovernanceFlags:
    """Load governance flags from a memory payload, merging with defaults.

    Handles:
        - payload is None or empty → all defaults (permissive)
        - payload has no "governance" key → all defaults
        - payload["governance"] is partial → missing fields get defaults
        - payload["governance"] is complete → pass through

    This is the SINGLE entry point for reading governance. Do not use
    scattered payload.get("governance", {}) calls elsewhere.
    """
    if not payload:
        return MemoryGovernanceFlags()

    raw = payload.get("governance")
    if not raw or not isinstance(raw, dict):
        return MemoryGovernanceFlags()

    return MemoryGovernanceFlags.from_dict(raw)


# ---------------------------------------------------------------------------
# Enforcement checks: source protection
# ---------------------------------------------------------------------------

def should_emit_packet(payload: Optional[Dict[str, Any]] = None) -> bool:
    """Return True if this memory is allowed to emit a collective packet.

    Checks source protection flags:
        - non_shareable → block
        - collective_export_blocked → block

    Called at packet emission time in fabric.ingest(), BEFORE building
    the ResonancePacket. This is the earliest boundary.
    """
    gov = resolve_governance(payload)
    if gov.non_shareable:
        return False
    if gov.collective_export_blocked:
        return False
    return True


def is_compression_protected(payload: Optional[Dict[str, Any]] = None) -> bool:
    """Return True if this memory must not be automatically compressed/decayed.

    The 'protected' flag blocks ALL automated strength reduction:
        - compression short-path (strength *= mult)
        - compression long-path (export to deep + reduce to minimum)
        - decay_accelerated is IGNORED when protected=True

    Does NOT block manual operator actions (future: explicit override path).
    """
    gov = resolve_governance(payload)
    return gov.protected


def is_decay_accelerated(payload: Optional[Dict[str, Any]] = None) -> bool:
    """Return True if this memory should decay faster than normal.

    Protected memories NEVER get accelerated decay, even if the flag is set.
    This prevents contradictory state where someone marks a memory as both
    protected and decay-accelerated.
    """
    gov = resolve_governance(payload)
    if gov.protected:
        return False  # protected always wins
    return gov.decay_accelerated


# ---------------------------------------------------------------------------
# Enforcement checks: derived/echo handling
# ---------------------------------------------------------------------------

def allows_collective_reingest(payload: Optional[Dict[str, Any]] = None) -> bool:
    """Return True if this memory can accept collective echo re-ingestion.

    When False, convergence events involving this memory's content will not
    produce echoes back into this agent. Used by the policy engine in Phase D.
    """
    gov = resolve_governance(payload)
    return not gov.collective_reingest_blocked


# ---------------------------------------------------------------------------
# Mutation: partial update with audit trail
# ---------------------------------------------------------------------------

def update_governance(
    payload: Dict[str, Any],
    changes: Dict[str, bool],
    *,
    actor: str = "operator",
    source: str = "api",
) -> Dict[str, Any]:
    """Apply partial governance flag updates to a memory payload.

    Args:
        payload: The memory's payload dict (mutated in place).
        changes: Dict of flag_name → new_value. Only specified flags
                 are changed; unspecified flags keep their current value.
        actor: Who initiated the change (for audit).
        source: Where the change came from (for audit).

    Returns:
        The governance audit record that was appended.

    Raises:
        ValueError: If a change key is not a valid governance flag.
    """
    valid_flags = {f.name for f in MemoryGovernanceFlags.__dataclass_fields__.values()}
    bad_keys = set(changes.keys()) - valid_flags
    if bad_keys:
        raise ValueError(f"Unknown governance flags: {bad_keys}")

    # Resolve current state
    current = resolve_governance(payload)
    current_dict = asdict(current)

    # Apply partial changes
    changed_fields = {}
    for key, new_val in changes.items():
        old_val = current_dict.get(key)
        if old_val != new_val:
            current_dict[key] = bool(new_val)
            changed_fields[key] = {"old": old_val, "new": bool(new_val)}

    # Write back the full governance dict
    payload["governance"] = current_dict

    # Build audit record
    audit_record = {
        "ts": int(time.time()),
        "actor": actor,
        "source": source,
        "changed": changed_fields,
    }

    # Append to audit trail in payload
    if "governance_audit" not in payload:
        payload["governance_audit"] = []
    payload["governance_audit"].append(audit_record)

    return audit_record


# ---------------------------------------------------------------------------
# Audit persistence (workspace-level log for cross-memory queries)
# ---------------------------------------------------------------------------

class GovernanceAuditLog:
    """Append-only JSONL audit log for governance changes within a workspace.

    Each record tracks: timestamp, memory EID, changed flags, actor/source.
    Used for debugging "why didn't this emit?" or "why was this blocked?"
    """

    def __init__(self, data_dir: str, workspace_id: str) -> None:
        safe_workspace_id = safe_slug(workspace_id, "workspace_id")

        # Canonical trust chain: data_dir → workspaces/<id>/governance
        canonical_data = _canonical_storage_root(data_dir)
        governance_root = _canonical_storage_root(
            os.path.join(canonical_data, "workspaces", safe_workspace_id, "governance")
        )
        os.makedirs(governance_root, exist_ok=True)
        self._base = governance_root
        self._path = _child_path(governance_root, "audit.jsonl")
        self._lock = threading.Lock()

    def log(
        self,
        eid: int,
        agent_id: str,
        changes: Dict[str, Any],
        *,
        actor: str = "operator",
        source: str = "api",
    ) -> Dict[str, Any]:
        """Append a governance change record to the workspace audit log."""
        record = {
            "ts": int(time.time()),
            "eid": int(eid),
            "agent_id": agent_id,
            "changes": changes,
            "actor": actor,
            "source": source,
        }
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")
        return record

    def recent(self, limit: int = 50) -> list:
        """Return recent audit records."""
        if not os.path.exists(self._path):
            return []
        records = []
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records[-limit:]
