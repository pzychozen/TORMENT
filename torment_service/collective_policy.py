# collective_policy.py — Collective re-ingestion policy engine
#
# Decides whether a convergence event may be re-ingested into a target agent.
# This is the gatekeeper between detection and action.
#
# 7-gate eligibility order (all must pass):
#   1. Event confidence >= threshold
#   2. Agent opt-in (collective_reingest_enabled)
#   3. Domain exact match
#   4. Deduplication (event_id + agent_id — same event never reingested twice)
#   5. Rate limiting (max N reingests per agent per window)
#   6. Identity compatibility / drift budget
#   7. Eligible
#
# Design principles:
#   - Collective re-ingestion is NOT memory transfer.
#     It is low-amplitude thematic reinforcement.
#   - Echoes are influences, not autobiography.
#   - The policy should be conservative, asymmetric, and slightly
#     annoying to trigger. That is a feature, not a flaw.
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger("torment.collective_policy")


# ---------------------------------------------------------------------------
# Configuration defaults (overridable via constructor)
# ---------------------------------------------------------------------------

DEFAULT_CONFIDENCE_THRESHOLD = 0.60     # higher than detection (0.45)
DEFAULT_RATE_LIMIT_MAX = 3              # max reingests per agent per window
DEFAULT_RATE_LIMIT_WINDOW = 3600        # window in seconds (1 hour)
DEFAULT_DRIFT_BUDGET = 0.30             # max drift_score delta before blocking
DEFAULT_ECHO_STRENGTH = 0.25            # default strength multiplier for echoes
DEFAULT_ECHO_STRENGTH_CAP = 0.40        # hard cap on echo strength


# ---------------------------------------------------------------------------
# Policy result
# ---------------------------------------------------------------------------

@dataclass
class PolicyResult:
    """Result of a policy eligibility check."""

    eligible: bool = False
    gate_failed: Optional[str] = None   # which gate rejected (None if eligible)
    reason: str = ""                     # human-readable explanation
    echo_strength: float = DEFAULT_ECHO_STRENGTH

    def to_dict(self) -> Dict[str, Any]:
        return {
            "eligible": self.eligible,
            "gate_failed": self.gate_failed,
            "reason": self.reason,
            "echo_strength": self.echo_strength,
        }


# ---------------------------------------------------------------------------
# Dedup + rate limit tracker (persistent)
# ---------------------------------------------------------------------------

class ReingestTracker:
    """Tracks which events have been reingested into which agents,
    and enforces rate limiting.

    Persistence: JSONL at data/workspaces/{ws}/collective/reingest_log.jsonl
    """

    def __init__(self, data_dir: str, workspace_id: str) -> None:
        self._base = os.path.join(data_dir, "workspaces", workspace_id, "collective")
        os.makedirs(self._base, exist_ok=True)
        self._log_path = os.path.join(self._base, "reingest_log.jsonl")
        self._lock = threading.Lock()

        # In-memory caches (loaded from disk on startup)
        self._reingested: Set[str] = set()       # "agent_id|event_id" pairs
        self._agent_timestamps: Dict[str, List[int]] = {}  # agent_id -> list of timestamps

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
                        agent_id = record.get("agent_id", "")
                        event_id = record.get("event_id", "")
                        ts = int(record.get("ts", 0))
                        if agent_id and event_id:
                            self._reingested.add(f"{agent_id}|{event_id}")
                            self._agent_timestamps.setdefault(agent_id, []).append(ts)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            log.debug("Could not load reingestion log: %s", e)

    def is_duplicate(self, agent_id: str, event_id: str) -> bool:
        """Check if this event has already been reingested into this agent."""
        return f"{agent_id}|{event_id}" in self._reingested

    def count_recent(self, agent_id: str, window_seconds: int) -> int:
        """Count reingests for this agent within the time window."""
        cutoff = int(time.time()) - window_seconds
        timestamps = self._agent_timestamps.get(agent_id, [])
        return sum(1 for ts in timestamps if ts >= cutoff)

    def record(self, agent_id: str, event_id: str) -> None:
        """Record a successful reingest."""
        now = int(time.time())
        record = {
            "agent_id": agent_id,
            "event_id": event_id,
            "ts": now,
        }
        with self._lock:
            self._reingested.add(f"{agent_id}|{event_id}")
            self._agent_timestamps.setdefault(agent_id, []).append(now)
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")

    def check_and_reserve(self, agent_id: str, event_id: str) -> bool:
        """Atomic check-and-reserve for deduplication.

        Returns True if the event was NOT already reingested and has been
        reserved (marked as reingested). Returns False if it's a duplicate.

        This eliminates the race window between is_duplicate() and record()
        where two threads could both pass the check before either records.

        Call this BEFORE performing the actual reingest. If the reingest
        fails, call unreserve() to roll back.
        """
        key = f"{agent_id}|{event_id}"
        with self._lock:
            if key in self._reingested:
                return False  # duplicate
            self._reingested.add(key)
            return True  # reserved

    def confirm_reservation(self, agent_id: str, event_id: str) -> None:
        """Persist a previously reserved reingest to disk.

        Call this AFTER the reingest succeeds. The in-memory reservation
        was already made by check_and_reserve().
        """
        now = int(time.time())
        record = {
            "agent_id": agent_id,
            "event_id": event_id,
            "ts": now,
        }
        with self._lock:
            self._agent_timestamps.setdefault(agent_id, []).append(now)
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")

    def unreserve(self, agent_id: str, event_id: str) -> None:
        """Roll back a reservation if the reingest failed.

        Removes the in-memory mark so the event can be retried later.
        """
        key = f"{agent_id}|{event_id}"
        with self._lock:
            self._reingested.discard(key)


# ---------------------------------------------------------------------------
# Drift budget checker
# ---------------------------------------------------------------------------

def check_drift_budget(
    current_drift_score: float,
    drift_direction: str,
    event_domain_id: str,
    agent_domain_id: str,
    event_motifs: List[str],
    agent_seed_motif_id: Optional[str],
    drift_budget: float = DEFAULT_DRIFT_BUDGET,
) -> Tuple[bool, str]:
    """Check whether the target agent can absorb an echo without exceeding drift budget.

    This is gate 6 — the identity compatibility check.

    Checks:
        1. If agent is already drifting hard (away_seed and |drift_score| near budget),
           don't push further.
        2. If event motifs have zero overlap with seed motif, the echo is
           thematically alien — reject.
        3. Domain must match exactly (enforced at gate 3, but double-checked here).

    Returns:
        (passed, reason) tuple.
    """
    # Domain match (defensive — should be caught at gate 3)
    if event_domain_id != agent_domain_id:
        return False, f"Domain mismatch: event={event_domain_id}, agent={agent_domain_id}"

    # Drift score check: if agent is far from seed and still moving away,
    # adding more external influence is risky
    if drift_direction == "away_seed" and current_drift_score < -drift_budget:
        return False, (
            f"Agent already drifting away (score={current_drift_score:.3f}, "
            f"budget={-drift_budget:.3f}). Echo would risk identity erosion."
        )

    # If drift score is very negative (far from seed), be cautious
    # even if direction is stable
    if current_drift_score < -(drift_budget + 0.15):
        return False, (
            f"Agent drift too far from seed (score={current_drift_score:.3f}). "
            f"Refusing echo until drift stabilizes."
        )

    # Motif compatibility: if agent has a seed motif, check for ANY thematic
    # connection with the event. If zero overlap, the echo is alien.
    if agent_seed_motif_id and event_motifs:
        # Simple check: does the seed motif appear in the event's dominant motifs?
        # This is crude but effective for Phase D. Can be refined later.
        if agent_seed_motif_id not in event_motifs:
            # Not a hard reject — the echo might still be relevant if the agent
            # has grown beyond their seed motif. Only reject if drift is negative.
            if current_drift_score < 0:
                return False, (
                    f"Event motifs {event_motifs} don't include seed motif "
                    f"'{agent_seed_motif_id}', and agent is already drifting "
                    f"(score={current_drift_score:.3f}). Echo rejected as thematically alien."
                )
            # If drift is positive (near seed), allow it — agent is stable enough
            # to absorb diverse influences

    return True, "Drift budget check passed"


# ---------------------------------------------------------------------------
# Main policy engine
# ---------------------------------------------------------------------------

class CollectivePolicy:
    """7-gate eligibility engine for collective echo re-ingestion.

    Conservative by design. Each gate must pass in order.
    """

    def __init__(
        self,
        data_dir: str,
        workspace_id: str,
        *,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        rate_limit_max: int = DEFAULT_RATE_LIMIT_MAX,
        rate_limit_window: int = DEFAULT_RATE_LIMIT_WINDOW,
        drift_budget: float = DEFAULT_DRIFT_BUDGET,
        echo_strength: float = DEFAULT_ECHO_STRENGTH,
        echo_strength_cap: float = DEFAULT_ECHO_STRENGTH_CAP,
    ) -> None:
        self.workspace_id = workspace_id
        self.confidence_threshold = confidence_threshold
        self.rate_limit_max = rate_limit_max
        self.rate_limit_window = rate_limit_window
        self.drift_budget = drift_budget
        self.echo_strength = min(echo_strength, echo_strength_cap)
        self.echo_strength_cap = echo_strength_cap

        # Agent-level opt-in/out registry (in-memory, settable via API)
        # Default: all agents opted in
        self._agent_opt_out: Set[str] = set()

        # Persistent dedup + rate tracker
        self.tracker = ReingestTracker(data_dir, workspace_id)

        # Track active reservation from evaluate() for cleanup on failure
        self._reserved_event_id: Optional[str] = None
        self._reserved_agent_id: Optional[str] = None

    def _unreserve_if_needed(self) -> None:
        """Roll back any active reservation from a failed gate evaluation."""
        if self._reserved_event_id and self._reserved_agent_id:
            self.tracker.unreserve(self._reserved_agent_id, self._reserved_event_id)
            self._reserved_event_id = None
            self._reserved_agent_id = None

    def set_agent_opt_out(self, agent_id: str, opt_out: bool = True) -> None:
        """Set whether an agent refuses collective echoes."""
        if opt_out:
            self._agent_opt_out.add(agent_id)
        else:
            self._agent_opt_out.discard(agent_id)

    def is_agent_opted_in(self, agent_id: str) -> bool:
        """Check if an agent accepts collective echoes."""
        return agent_id not in self._agent_opt_out

    def evaluate(
        self,
        event: Dict[str, Any],
        target_agent_id: str,
        target_domain_id: str,
        *,
        current_drift_score: float = 0.0,
        drift_direction: str = "stable",
        agent_seed_motif_id: Optional[str] = None,
    ) -> PolicyResult:
        """Run all 7 gates and return eligibility result.

        Args:
            event: ConvergenceEvent as dict (from collective_field).
            target_agent_id: Agent that would receive the echo.
            target_domain_id: Domain the agent is operating in.
            current_drift_score: Agent's current drift score (-1 to +1).
            drift_direction: "toward_seed", "away_seed", or "stable".
            agent_seed_motif_id: Agent's seed motif ID (if seeded).

        Returns:
            PolicyResult with eligibility decision and explanation.
        """

        # ── Gate 1: Event confidence ──────────────────────────────────
        confidence = float(event.get("confidence", 0.0))
        if confidence < self.confidence_threshold:
            return PolicyResult(
                eligible=False,
                gate_failed="confidence",
                reason=(
                    f"Event confidence {confidence:.3f} below threshold "
                    f"{self.confidence_threshold:.3f}"
                ),
            )

        # ── Gate 2: Agent opt-in ──────────────────────────────────────
        if not self.is_agent_opted_in(target_agent_id):
            return PolicyResult(
                eligible=False,
                gate_failed="agent_opt_in",
                reason=f"Agent '{target_agent_id}' has opted out of collective echoes",
            )

        # ── Gate 3: Domain exact match ────────────────────────────────
        event_domain = event.get("domain_id", "")
        if event_domain != target_domain_id:
            return PolicyResult(
                eligible=False,
                gate_failed="domain_match",
                reason=(
                    f"Domain mismatch: event domain='{event_domain}', "
                    f"target domain='{target_domain_id}'"
                ),
            )

        # ── Gate 4: Deduplication (atomic check-and-reserve) ─────────
        event_id = event.get("event_id", "")
        if not self.tracker.check_and_reserve(target_agent_id, event_id):
            return PolicyResult(
                eligible=False,
                gate_failed="dedup",
                reason=(
                    f"Event '{event_id}' already reingested into "
                    f"agent '{target_agent_id}'"
                ),
            )
        # NOTE: event is now reserved in-memory. If any later gate fails,
        # we must unreserve. The _reserved_event_id flag tracks this.
        self._reserved_event_id = event_id
        self._reserved_agent_id = target_agent_id

        # ── Gate 5: Rate limiting ─────────────────────────────────────
        recent_count = self.tracker.count_recent(
            target_agent_id, self.rate_limit_window,
        )
        if recent_count >= self.rate_limit_max:
            self._unreserve_if_needed()
            return PolicyResult(
                eligible=False,
                gate_failed="rate_limit",
                reason=(
                    f"Agent '{target_agent_id}' has reached rate limit "
                    f"({recent_count}/{self.rate_limit_max} in "
                    f"{self.rate_limit_window}s window)"
                ),
            )

        # ── Gate 6: Identity compatibility / drift budget ─────────────
        event_motifs = event.get("dominant_motifs", [])
        drift_ok, drift_reason = check_drift_budget(
            current_drift_score=current_drift_score,
            drift_direction=drift_direction,
            event_domain_id=event_domain,
            agent_domain_id=target_domain_id,
            event_motifs=event_motifs,
            agent_seed_motif_id=agent_seed_motif_id,
            drift_budget=self.drift_budget,
        )
        if not drift_ok:
            self._unreserve_if_needed()
            return PolicyResult(
                eligible=False,
                gate_failed="drift_budget",
                reason=drift_reason,
            )

        # ── Gate 7: Eligible ──────────────────────────────────────────
        return PolicyResult(
            eligible=True,
            gate_failed=None,
            reason=(
                f"All gates passed. Confidence={confidence:.3f}, "
                f"drift={current_drift_score:.3f}, "
                f"rate={recent_count}/{self.rate_limit_max}"
            ),
            echo_strength=self.echo_strength,
        )

    def record_reingest(self, agent_id: str, event_id: str) -> None:
        """Confirm and persist a successful reingest (call AFTER re-ingestion succeeds).

        If called after evaluate() reserved the event (normal flow), this
        persists the reservation to disk. If called standalone (legacy/tests),
        this does a full record (both in-memory add and disk persist).
        """
        if (self._reserved_event_id == event_id
                and self._reserved_agent_id == agent_id):
            # Normal flow: evaluate() already reserved in-memory via check_and_reserve
            self.tracker.confirm_reservation(agent_id, event_id)
            self._reserved_event_id = None
            self._reserved_agent_id = None
        else:
            # Legacy/standalone path: do full record (in-memory + disk)
            self.tracker.record(agent_id, event_id)
