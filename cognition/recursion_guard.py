# cognition/recursion_guard.py
"""
Recursion-safety guard for archivist writeback — bounded DFS ancestry walk.

This module implements the TORMENT v2.4.x Recursion-Safety Policy (Rules A–F)
as a pure, unit-testable function that can be called from the writeback path
without dragging in the rest of the cognition pipeline. The guard is
deliberately kept storage-layer-adjacent so it can be reasoned about in
isolation.

Replaces the one-hop inline check that previously lived in
``cognition.pipeline._write_back_approved``. The prior check inspected only
direct parents; this guard walks the ancestor graph to a bounded depth,
closing the laundering gap documented in
``docs/RECURSION_SAFETY_POLICY_v2.4.x.md`` ("Collective Echo Exclusion" and
related corridor-tearing posture).

Design invariants
-----------------
1. **Fail-closed.** Any unknown, malformed, unnormalizable, or depth-exceeded
   ancestry → reject. See ``docs/DOCTRINE_v2.4.x.md`` rule #5
   ("Provenance is a hard boundary").

2. **Single source of truth for parent shape.** All raw provenance values
   pass through ``ProvenanceV1.normalize_parent`` before any inspection.
   The walk itself never branches on raw type.

3. **Bounded horizon.** The walk is capped at
   ``_RECURSION_GUARD_DEPTH_CAP`` hops. This is a tuning parameter — see
   ``docs/RECURSION_GUARD_TUNING_v2.4.x.md`` for the discipline around
   changing it.

4. **Visited set for cycles.** The graph is not guaranteed acyclic on an
   old corpus. The walk never revisits an EID.

5. **Archivist role is the decisive blocker.** At any depth, a parent whose
   ``source_role`` contains "archivist" → reject. This is independent of
   ``source_type`` and matches the production enforcement asymmetry
   resolved in step 5 (see ``docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md``).

6. **Safe source_types in the walked window:**
   ``user_input``, ``tool_result``, ``memory``, ``role_output`` (non-archivist).
   ``role_output`` is admitted inside the bounded window because rejecting
   it entirely would collapse the writeback lane more than is intended
   under the current model (the archivist role check remains the real
   blocker). ``collective_echo`` and ``derived`` are rejected at any depth
   — the former per the step-4 exclusion, the latter because
   ``SOURCE_DERIVED`` is deferred vocabulary and must not be pre-authorized
   through ancestry chaining.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional, Tuple

from torment_service.provenance_v1 import ProvenanceV1

_log = logging.getLogger(__name__)


# ── Tuning parameters ────────────────────────────────────────────────
#
# See docs/RECURSION_GUARD_TUNING_v2.4.x.md before adjusting any value here.
# These are bounded on purpose. Increasing them requires explicit analysis
# and doctrine review, not a casual tuning pass.

_RECURSION_GUARD_DEPTH_CAP = 3

_SAFE_SOURCE_TYPES_IN_WALK = frozenset({
    "user_input",
    "tool_result",
    "memory",
    "role_output",  # admitted only in walk; see module docstring & tuning doc
})

_REJECTED_SOURCE_TYPES_IN_WALK = frozenset({
    "collective_echo",  # step-4 exclusion
    "derived",          # deferred vocabulary — must not be chain-admitted
})

# Rejection reason vocabulary (stable strings for tests / logs / metrics)
REASON_UNKNOWN_PARENT       = "unknown_parent_provenance"
REASON_ARCHIVIST_BLOCKED    = "archivist_parent_blocked"
REASON_COLLECTIVE_ECHO      = "collective_echo_in_ancestry"
REASON_DERIVED              = "derived_in_ancestry"
REASON_UNSAFE_SOURCE_TYPE   = "unsafe_parent_source_type"
REASON_DEPTH_EXCEEDED       = "ancestry_depth_exceeded"
REASON_MALFORMED_ROLE_OUT   = "role_output_missing_source_role"


def recursion_guard_check(
    seed_eids: List[int],
    lookup_fn: Optional[Callable[[str, str, int], Any]],
    workspace_id: str,
    agent_id: str,
    depth_cap: int = _RECURSION_GUARD_DEPTH_CAP,
) -> Tuple[bool, Optional[str]]:
    """Run the bounded ancestry guard.

    Parameters
    ----------
    seed_eids
        The immediate parent EIDs for the write candidate (depth 1 of the walk).
    lookup_fn
        ``lookup_fn(workspace_id, agent_id, eid) -> payload dict | None``.
        Used to resolve every EID encountered during the walk. If ``None``
        and seed_eids is non-empty, the guard rejects conservatively.
    workspace_id, agent_id
        Context passed to ``lookup_fn`` on every call.
    depth_cap
        Maximum ancestor depth to walk. Defaults to
        ``_RECURSION_GUARD_DEPTH_CAP``. See tuning doc before changing.

    Returns
    -------
    (True, None)
        Every ancestor within the depth cap is admissible.
    (False, reason)
        A violation was detected. ``reason`` is one of the stable
        ``REASON_*`` strings.
    """
    # No parent EIDs → proposal derives from context, not specific memories.
    # Typical for first-generation proposals; matches prior behavior.
    if not seed_eids:
        return True, None

    if lookup_fn is None:
        # Conservative posture: parents exist but are unverifiable.
        return False, REASON_UNKNOWN_PARENT

    # DFS stack of (eid, depth). Depth 1 = immediate parent.
    stack: List[Tuple[int, int]] = [(int(eid), 1) for eid in seed_eids]
    visited: set = set()

    while stack:
        eid, depth = stack.pop()
        if eid in visited:
            continue
        visited.add(eid)

        try:
            payload = lookup_fn(workspace_id, agent_id, eid)
        except Exception as exc:
            _log.debug(
                "recursion_guard_check: lookup raised for eid=%s: %s",
                eid, exc,
            )
            return False, REASON_UNKNOWN_PARENT

        if not isinstance(payload, dict):
            return False, REASON_UNKNOWN_PARENT

        raw_prov = payload.get("provenance")
        prov = ProvenanceV1.normalize_parent(raw_prov)

        if prov is None:
            # None, malformed, undeclared, or unnormalizable.
            return False, REASON_UNKNOWN_PARENT

        source_type = prov.get("source_type")
        source_role = (prov.get("source_role") or "").lower()

        # Decisive blocker: archivist role at any depth.
        if "archivist" in source_role:
            return False, REASON_ARCHIVIST_BLOCKED

        # Explicit rejected source_types (collective_echo, derived).
        if source_type == "collective_echo":
            return False, REASON_COLLECTIVE_ECHO
        if source_type == "derived":
            return False, REASON_DERIVED

        # General safe-set check.
        if source_type not in _SAFE_SOURCE_TYPES_IN_WALK:
            return False, REASON_UNSAFE_SOURCE_TYPE

        # role_output admitted only with an explicit non-archivist source_role.
        # (archivist case already rejected above; this catches role_output
        # with missing/empty source_role, which is a malformed shape given
        # ProvenanceV1 requires source_role when source_type == role_output.)
        if source_type == "role_output" and not source_role:
            return False, REASON_MALFORMED_ROLE_OUT

        # Admit this node. Now consider its parents.
        parent_eids = prov.get("parent_eids") or []

        if not parent_eids:
            # Chain terminates cleanly at this node.
            continue

        if depth >= depth_cap:
            # This node has unverified ancestry beyond the depth cap.
            # Fail-closed: we cannot guarantee the corridor is clean.
            return False, REASON_DEPTH_EXCEEDED

        for pe in parent_eids:
            try:
                pe_int = int(pe)
            except (TypeError, ValueError):
                return False, REASON_UNKNOWN_PARENT
            if pe_int not in visited:
                stack.append((pe_int, depth + 1))

    return True, None
