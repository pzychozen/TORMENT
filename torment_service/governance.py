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

    Path C Q1 enforcement: rejects any NonAuthoritativeDeepHit subtype
    (DeepRetrievalHit, OrphanedDeepHit) passed where a memory payload
    is expected. The guard is a structural tripwire matching the
    Shape B wrapper-type contract; see
    docs/CLUSTER_5_PATH_C_Q1_IMPLEMENTATION_FRAMING_v0.1.md Step 4.
    """
    # Path C Q1 enforcement: see docstring. Inline import keeps the
    # diff narrow; future cleanup may move to module-level imports.
    from .deep_hits import assert_authoritative_memory
    assert_authoritative_memory(payload)

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
# Surface-aware exclusion: gate memories at the LLM-facing context boundary
#
# FILTER-A — see docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md
#
# Phase 0 substrate audit (2026-05-04) confirmed CODE_FOLLOWUP_REGISTRY entry 01:
# `non_shareable` is stored correctly but is not yet acting as a retrieval /
# context-eligibility filter on the `/agent/query` path. This helper applies
# the existing governance flags as exclusion at the LLM-facing boundary.
#
# Invariants:
#   - "results" is ALWAYS the filtered LLM-facing list, regardless of mode.
#   - Operator/debug raw access is ADDITIVE via "raw_hits"; never overloads
#     "results".
#   - non_shareable applies to BOTH surfaces (universal LLM-facing exclusion).
#   - collective_export_blocked applies ONLY to collective_export surface.
# ---------------------------------------------------------------------------

# Surface constants. The `surface` parameter to filter_llm_facing is REQUIRED
# (no default) so call sites cannot accidentally conflate private LLM context
# with collective-export surfaces.
SURFACE_LLM_CONTEXT = "llm_context"
SURFACE_COLLECTIVE_EXPORT = "collective_export"
_VALID_SURFACES = frozenset({SURFACE_LLM_CONTEXT, SURFACE_COLLECTIVE_EXPORT})

# Trust threshold for include_raw_hits=True. Matches operator-tier ops in
# SPINE_CONTRACT.md §3 (seed_change, memory_governance_set both require 1.0).
_RAW_HITS_MIN_TRUST = 1.0


def filter_llm_facing(
    hits: list,
    *,
    surface: str,
    include_raw_hits: bool = False,
    actor: Optional[str] = None,
    trust_tier: Optional[float] = None,
) -> Dict[str, Any]:
    """Apply governance-flag exclusion to a list of memory hits.

    Single canonical helper for FILTER-A. Every LLM-facing retrieval /
    context-assembly path should call this after raw scoring and before
    building the final result/context blocks. See
    docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md for the full design.

    Args:
        hits: List of memory hit dicts (each may carry a 'governance' key).
        surface: REQUIRED. One of:
            - SURFACE_LLM_CONTEXT ("llm_context"): agent's own LLM-facing
              context (private query results, character_context, aperture
              lanes feeding the agent's prompt). Filter: non_shareable.
            - SURFACE_COLLECTIVE_EXPORT ("collective_export"): outbound
              surface (collective packets, echoes, cross-agent emission).
              Filter: non_shareable AND collective_export_blocked.
        include_raw_hits: When True (with valid operator authorization),
            adds a "raw_hits" key to the response containing the unfiltered
            candidate list. The "results" key is ALWAYS the filtered list,
            regardless of this flag. Default False.
        actor: Caller identity. Required for include_raw_hits=True.
        trust_tier: Caller trust tier in [0.0, 1.0]. Must be >=
            _RAW_HITS_MIN_TRUST (1.0) for include_raw_hits=True.

    Returns:
        Dict with shape:
            {
                "results":  [...],   # ALWAYS filtered per surface
                "excluded": [{"eid": <int|None>, "excluded_reason": <str>}, ...],
                "raw_hits": [...],   # ONLY present when include_raw_hits=True
                                     # AND authorization passes
            }

        Per FILTER-A §5 invariant: "results" never contains a memory the
        surface excludes. Operator/debug raw access is exposed exclusively
        via "raw_hits"; "results" never changes shape under raw mode.

    Raises:
        ValueError: if surface is missing or not in _VALID_SURFACES.

    Notes:
        - Authorization for include_raw_hits=True is the helper's last line
          of defense; the spine should already have authorized the caller
          before reaching this helper. If authorization here fails, the
          helper silently omits "raw_hits" rather than raising — "results"
          remains filtered, which preserves the privacy invariant. The
          helper does not authenticate; it only enforces the surface shape.
        - Non-dict items in `hits` pass through to "results" untouched
          (defensive; the helper does not endorse non-dict hits but also
          will not crash on them).
    """
    if surface not in _VALID_SURFACES:
        raise ValueError(
            f"filter_llm_facing requires surface in "
            f"{sorted(_VALID_SURFACES)}; got {surface!r}"
        )

    results: list = []
    excluded: list = []

    for hit in hits:
        if not isinstance(hit, dict):
            results.append(hit)
            continue

        gov = resolve_governance(hit)
        eid = hit.get("eid")

        # non_shareable is the universal LLM-facing exclusion; applies to
        # both surfaces (per FILTER-A §7 + HIVEMIND_GUIDE Invariant 2).
        if gov.non_shareable:
            excluded.append({"eid": eid, "excluded_reason": "non_shareable"})
            continue

        # collective_export_blocked is surface-conditional. It excludes from
        # collective/export surfaces only; on private llm_context the flag
        # does NOT apply (the memory IS shareable to its own agent).
        if surface == SURFACE_COLLECTIVE_EXPORT and gov.collective_export_blocked:
            excluded.append(
                {"eid": eid, "excluded_reason": "collective_export_blocked"}
            )
            continue

        results.append(hit)

    response: Dict[str, Any] = {"results": results, "excluded": excluded}

    # Operator/debug additive raw_hits, gated by explicit authorization.
    # Unauthorized requests silently omit raw_hits rather than raising;
    # results invariance is what matters here.
    if include_raw_hits:
        authorized = (
            actor is not None
            and trust_tier is not None
            and trust_tier >= _RAW_HITS_MIN_TRUST
        )
        if authorized:
            response["raw_hits"] = list(hits)

    return response


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
        governance_root = os.path.realpath(os.path.join(canonical_data, "workspaces", safe_workspace_id, "governance"))
        if not governance_root.startswith(canonical_data + os.sep):
            raise ValueError(f"Governance path escapes base: {governance_root!r}")
        os.makedirs(governance_root, exist_ok=True)
        self._base = governance_root
        self._path = _child_path(governance_root, "audit.jsonl")
        self._lock = threading.Lock()

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes governance root: {rp!r}")
        return rp

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
            with open(self._guard(self._path), "a", encoding="utf-8") as f:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")
        return record

    def recent(self, limit: int = 50) -> list:
        """Return recent audit records."""
        if not os.path.exists(self._path):
            return []
        records = []
        with open(self._guard(self._path), "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records[-limit:]
