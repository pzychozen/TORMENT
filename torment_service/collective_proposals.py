# collective_proposals.py — Light proposal bridge for convergence events
#
# Phase D4: Automatically draft share proposals when convergence events
# are persistent and high-confidence. Proposals remain "pending" for
# operator review — this module never auto-approves.
#
# Design principles (from ChatGPT review):
#   - Proposals are auto-DRAFTED, never auto-ACCEPTED.
#   - Only fire for high-confidence, repeated/persistent convergence.
#   - Proposals require persistence: must see the same domain+motif
#     pattern across multiple events before drafting.
#   - One proposal per convergence pattern — no spam.
#   - Proposal metadata includes collective provenance for traceability.
#
# Flow:
#   1. After a convergence event is detected, call maybe_draft_proposal().
#   2. The bridge checks persistence (has this pattern fired before?),
#      confidence threshold, and dedup (already proposed?).
#   3. If all checks pass, a proposal is drafted and persisted.
#   4. Operator sees it in the normal proposal review queue.
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger("torment.collective_proposals")

import numpy as np

from .embedding_store import _canonical_storage_root, _child_path


def _validate_path_component(value: str, label: str) -> str:
    if not value or ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"Invalid {label}: must not contain path separators or '..'")
    return value


# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

# Minimum composite confidence for proposal consideration
PROPOSAL_CONFIDENCE_THRESHOLD = 0.70

# Minimum number of convergence events with similar pattern before proposing
PROPOSAL_PERSISTENCE_MIN = 2

# Time window for persistence counting (seconds)
PROPOSAL_PERSISTENCE_WINDOW = 7200  # 2 hours

# Cooldown between proposals for the same domain (seconds)
PROPOSAL_DOMAIN_COOLDOWN = 1800  # 30 minutes

# Maximum pending collective proposals per domain
PROPOSAL_MAX_PENDING_PER_DOMAIN = 5


# ---------------------------------------------------------------------------
# Convergence pattern key
# ---------------------------------------------------------------------------

def _pattern_key(domain_id: str, motifs: List[str]) -> str:
    """Create a deterministic key for a convergence pattern.

    A pattern is domain + sorted motif set. This lets us track
    whether similar convergence keeps happening.
    """
    sorted_motifs = tuple(sorted(set(motifs))) if motifs else ()
    return f"{domain_id}|{','.join(sorted_motifs)}"


# ---------------------------------------------------------------------------
# Persistence tracker
# ---------------------------------------------------------------------------

class ConvergencePersistenceTracker:
    """Tracks convergence event patterns over time to detect persistence.

    Persistence = the same domain+motif pattern firing across multiple
    events within a time window. Only persistent patterns get proposals.

    Persisted as JSONL for crash safety.
    """

    def __init__(self, data_dir: str, workspace_id: str) -> None:
        safe_workspace_id = _validate_path_component(workspace_id, "workspace_id")

        # Canonical trust chain: data_dir → workspaces/<id>/collective
        canonical_data = _canonical_storage_root(data_dir)
        collective_root = _canonical_storage_root(
            os.path.join(canonical_data, "workspaces", safe_workspace_id, "collective"),
            mkdir=True,
        )
        self._base = collective_root
        self._log_path = _child_path(collective_root, "convergence_patterns.jsonl")
        self._lock = threading.Lock()

        # pattern_key -> list of (event_id, timestamp)
        self._patterns: Dict[str, List[Tuple[str, int]]] = {}

        # event_ids that already generated proposals (dedup)
        self._proposed_events: Set[str] = set()

        # domain -> last proposal timestamp
        self._domain_last_proposed: Dict[str, int] = {}

        self._load()

    def _load(self) -> None:
        """Warm caches from disk."""
        if not os.path.exists(self._log_path):
            return
        try:
            with open(self._log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        rtype = record.get("type", "pattern")
                        if rtype == "pattern":
                            key = record.get("pattern_key", "")
                            eid = record.get("event_id", "")
                            ts = int(record.get("ts", 0))
                            if key and eid:
                                self._patterns.setdefault(key, []).append((eid, ts))
                        elif rtype == "proposed":
                            eid = record.get("event_id", "")
                            domain = record.get("domain_id", "")
                            ts = int(record.get("ts", 0))
                            if eid:
                                self._proposed_events.add(eid)
                            if domain:
                                self._domain_last_proposed[domain] = max(
                                    self._domain_last_proposed.get(domain, 0), ts,
                                )
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            log.debug("Could not load proposals file: %s", e)

    def record_event(self, event: Dict[str, Any]) -> None:
        """Record a convergence event for persistence tracking."""
        domain = event.get("domain_id", "")
        motifs = event.get("dominant_motifs", [])
        event_id = event.get("event_id", "")
        ts = int(event.get("ts_end", 0)) or int(time.time())

        key = _pattern_key(domain, motifs)
        record = {
            "type": "pattern",
            "pattern_key": key,
            "event_id": event_id,
            "domain_id": domain,
            "motifs": motifs,
            "ts": ts,
        }
        with self._lock:
            self._patterns.setdefault(key, []).append((event_id, ts))
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")

    def count_recent(
        self, domain_id: str, motifs: List[str], window: int,
    ) -> int:
        """Count recent events matching this pattern within the window."""
        key = _pattern_key(domain_id, motifs)
        cutoff = int(time.time()) - window
        entries = self._patterns.get(key, [])
        return sum(1 for _, ts in entries if ts >= cutoff)

    def is_event_proposed(self, event_id: str) -> bool:
        """Check if this specific event already generated a proposal."""
        return event_id in self._proposed_events

    def is_domain_on_cooldown(self, domain_id: str, cooldown: int) -> bool:
        """Check if the domain has had a recent collective proposal."""
        last_ts = self._domain_last_proposed.get(domain_id, 0)
        return (int(time.time()) - last_ts) < cooldown

    def record_proposed(self, event_id: str, domain_id: str) -> None:
        """Mark that a proposal was drafted from this event."""
        ts = int(time.time())
        record = {
            "type": "proposed",
            "event_id": event_id,
            "domain_id": domain_id,
            "ts": ts,
        }
        with self._lock:
            self._proposed_events.add(event_id)
            self._domain_last_proposed[domain_id] = ts
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# Proposal draft result
# ---------------------------------------------------------------------------

@dataclass
class ProposalDraftResult:
    """Result of attempting to draft a collective proposal."""

    drafted: bool = False
    reason: str = ""
    proposal_id: Optional[str] = None
    event_id: Optional[str] = None
    domain_id: Optional[str] = None
    pattern_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Main bridge
# ---------------------------------------------------------------------------

class CollectiveProposalBridge:
    """Bridges convergence events into the proposal system.

    Call maybe_draft_proposal() after convergence detection.
    If the event is persistent and high-confidence, a share proposal
    is drafted (status="pending") for operator review.
    """

    def __init__(
        self,
        data_dir: str,
        workspace_id: str,
        *,
        confidence_threshold: float = PROPOSAL_CONFIDENCE_THRESHOLD,
        persistence_min: int = PROPOSAL_PERSISTENCE_MIN,
        persistence_window: int = PROPOSAL_PERSISTENCE_WINDOW,
        domain_cooldown: int = PROPOSAL_DOMAIN_COOLDOWN,
        max_pending_per_domain: int = PROPOSAL_MAX_PENDING_PER_DOMAIN,
    ) -> None:
        self.workspace_id = workspace_id
        self.confidence_threshold = confidence_threshold
        self.persistence_min = persistence_min
        self.persistence_window = persistence_window
        self.domain_cooldown = domain_cooldown
        self.max_pending_per_domain = max_pending_per_domain

        self.tracker = ConvergencePersistenceTracker(data_dir, workspace_id)

    def maybe_draft_proposal(
        self,
        event: Dict[str, Any],
        proposal_registry: Optional[Any] = None,
        embedding: Optional[np.ndarray] = None,
    ) -> ProposalDraftResult:
        """Check if a convergence event warrants a share proposal.

        Always records the event for persistence tracking. Only drafts
        a proposal if ALL conditions are met:
            1. Event confidence >= threshold
            2. Pattern persistence >= minimum count in window
            3. This specific event hasn't already generated a proposal
            4. Domain is not on cooldown
            5. Domain doesn't have too many pending collective proposals

        Args:
            event: ConvergenceEvent as dict.
            proposal_registry: ProposalRegistry for the event's domain (optional).
                               If None, proposal is tracked but not submitted.
            embedding: Optional embedding for the proposal summary.

        Returns:
            ProposalDraftResult with outcome details.
        """
        event_id = event.get("event_id", "")
        domain_id = event.get("domain_id", "")
        confidence = float(event.get("confidence", 0.0))
        motifs = event.get("dominant_motifs", [])
        agents = event.get("participating_agents", [])

        # Always record the event for persistence tracking
        self.tracker.record_event(event)

        # ── Check 1: Confidence threshold ─────────────────────────────
        if confidence < self.confidence_threshold:
            return ProposalDraftResult(
                drafted=False,
                reason=f"Confidence {confidence:.3f} below proposal threshold {self.confidence_threshold:.3f}",
                event_id=event_id,
                domain_id=domain_id,
            )

        # ── Check 2: Persistence ──────────────────────────────────────
        pattern_count = self.tracker.count_recent(
            domain_id, motifs, self.persistence_window,
        )
        if pattern_count < self.persistence_min:
            return ProposalDraftResult(
                drafted=False,
                reason=(
                    f"Pattern not persistent enough: {pattern_count}/{self.persistence_min} "
                    f"events in {self.persistence_window}s window"
                ),
                event_id=event_id,
                domain_id=domain_id,
                pattern_count=pattern_count,
            )

        # ── Check 3: Event dedup ──────────────────────────────────────
        if self.tracker.is_event_proposed(event_id):
            return ProposalDraftResult(
                drafted=False,
                reason=f"Event '{event_id}' already generated a proposal",
                event_id=event_id,
                domain_id=domain_id,
                pattern_count=pattern_count,
            )

        # ── Check 4: Domain cooldown ─────────────────────────────────
        if self.tracker.is_domain_on_cooldown(domain_id, self.domain_cooldown):
            return ProposalDraftResult(
                drafted=False,
                reason=f"Domain '{domain_id}' is on proposal cooldown",
                event_id=event_id,
                domain_id=domain_id,
                pattern_count=pattern_count,
            )

        # ── Check 5: Max pending per domain ──────────────────────────
        if proposal_registry is not None:
            try:
                pending = proposal_registry.list_pending(limit=self.max_pending_per_domain + 1)
                # Count only collectively-sourced proposals
                collective_pending = [
                    p for p in pending
                    if hasattr(p, 'note') and p.note
                    and "collective_source" in str(p.note)
                ]
                if len(collective_pending) >= self.max_pending_per_domain:
                    return ProposalDraftResult(
                        drafted=False,
                        reason=(
                            f"Domain '{domain_id}' already has "
                            f"{len(collective_pending)} pending collective proposals "
                            f"(max={self.max_pending_per_domain})"
                        ),
                        event_id=event_id,
                        domain_id=domain_id,
                        pattern_count=pattern_count,
                    )
            except Exception:
                pass  # If registry check fails, don't block — fail open for drafting

        # ── All checks passed: draft the proposal ────────────────────
        summary = self._build_proposal_summary(event)
        proposal_id = None

        if proposal_registry is not None and embedding is not None:
            try:
                agent_id = agents[0] if agents else "collective"
                p = proposal_registry.submit(
                    agent_id=agent_id,
                    summary=summary,
                    embedding=embedding,
                    mtype="collective_echo",
                    confidence=confidence,
                    strength=float(event.get("semantic_overlap", 0.5)),
                )
                proposal_id = p.proposal_id
            except Exception:
                pass  # Proposal submission failure is non-fatal

        # Record that this event generated a proposal
        self.tracker.record_proposed(event_id, domain_id)

        return ProposalDraftResult(
            drafted=True,
            reason=(
                f"Proposal drafted: {pattern_count} convergence events "
                f"in {self.persistence_window}s window, confidence={confidence:.3f}"
            ),
            proposal_id=proposal_id,
            event_id=event_id,
            domain_id=domain_id,
            pattern_count=pattern_count,
        )

    @staticmethod
    def _build_proposal_summary(event: Dict[str, Any]) -> str:
        """Build a proposal summary from a convergence event."""
        agents = event.get("participating_agents", [])
        domain = event.get("domain_id", "unknown")
        motifs = event.get("dominant_motifs", [])
        confidence = float(event.get("confidence", 0.0))
        event_id = event.get("event_id", "")

        parts = [f"[collective proposal] Multi-agent convergence in '{domain}'"]
        if agents:
            parts.append(f"between {', '.join(agents)}")
        if motifs:
            parts.append(f"(motifs: {', '.join(motifs[:4])})")
        parts.append(f"confidence={confidence:.2f}")
        parts.append(f"[collective_source:{event_id}]")

        return " ".join(parts)
