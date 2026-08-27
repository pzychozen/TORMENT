# torment_service/compression.py
"""
Event-gated memory compression for TORMENT.

Physics basis:
  - Tri-Octa imposes geometric order only at corridor transitions (event boundaries),
    NOT continuously. Between events, inter-event chaos dominates.
  - Compression executes AT event boundaries: corridor exit, cycle-stage change, or
    emergency tearing.
  - J-channel (relational/coherence) settles before Z-channel (geometry). Scoring
    evaluates relational importance first (60% weight), geometric second (40%).
  - Two return channels: short-path (re-file in core, reduced strength) and long-path
    (export to deep memory store for future recall).

Architecture:
  Dynamics (kernel) → Observables (tri_mod signals) → Trigger (EventDetector)
  → Scorer → Router → Executor → Diagnostics (compression_log.jsonl)

  Reverse influence is forbidden per Trigger Registry rules.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from .coherence_field import compute_coherence_field
from .pathing import validate_structural_path_component

logger = logging.getLogger(__name__)


def _validate_path_component(value: str, label: str) -> str:
    try:
        return validate_structural_path_component(value, label)
    except ValueError as exc:
        if value == ".":
            raise ValueError(f"Invalid {label}: must not be '.'") from exc
        raise ValueError(f"Invalid {label}: must not contain path separators or '..'")


# ---------------------------------------------------------------------------
# Configuration (env-based, sensible defaults)
# ---------------------------------------------------------------------------
_env = os.environ.get


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(_env(key, str(default)))
    except (ValueError, TypeError):
        return default


COMPRESS_MIN_AGE = _env_int("TORMENT_COMPRESS_MIN_AGE", 50)
COMPRESS_MAX_CANDIDATES = _env_int("TORMENT_COMPRESS_MAX_CANDIDATES", 20)
COMPRESS_DEEP_THRESHOLD = _env_float("TORMENT_COMPRESS_DEEP_THRESHOLD", 0.7)
COMPRESS_AGE_THRESHOLD = _env_int("TORMENT_COMPRESS_AGE_THRESHOLD", 500)
COMPRESS_TEAR_EMERGENCY = _env_float("TORMENT_COMPRESS_TEAR_EMERGENCY", 0.7)
COMPRESS_SHORT_PATH_MULT = _env_float("TORMENT_COMPRESS_SHORT_STRENGTH_MULT", 0.5)
COMPRESS_LONG_PATH_STRENGTH = _env_float("TORMENT_COMPRESS_LONG_STRENGTH", 0.1)

# Tier-specific short-path multipliers (Proposal D — Phase 2.2)
COMPRESS_RELATIONAL_MULT = _env_float("TORMENT_COMPRESS_RELATIONAL_MULT", 0.7)
COMPRESS_ECHO_MULT = _env_float("TORMENT_COMPRESS_ECHO_MULT", 0.4)
COMPRESS_TOOL_RESULT_MULT = _env_float("TORMENT_COMPRESS_TOOL_RESULT_MULT", 0.45)
COMPRESS_TOOL_RESULT_SCORE_MULT = 1.10  # +10% compressibility for tool-result tier
COMPRESS_ECHO_DEEP_AGE = _env_int("TORMENT_COMPRESS_ECHO_DEEP_AGE", 150)

# Fallback trigger thresholds (Proposal A — Phase 2.2)
COMPRESS_COUNT_THRESHOLD = _env_int("TORMENT_COMPRESS_COUNT_THRESHOLD", 400)
COMPRESS_STEP_INTERVAL = _env_int("TORMENT_COMPRESS_STEP_INTERVAL", 200)
COMPRESS_FALLBACK_COOLDOWN = _env_int("TORMENT_COMPRESS_FALLBACK_COOLDOWN", 50)
COMPRESS_PERIODIC_FLOOR = _env_float("TORMENT_COMPRESS_PERIODIC_FLOOR", 0.4)

# Hard memory cap — last-resort safety net (not primary mechanism)
COMPRESS_HARD_CAP = _env_int("TORMENT_MAX_PRIVATE_MEMORIES", 10000)
COMPRESS_HARD_CAP_TARGET = _env_float("TORMENT_HARD_CAP_TARGET_RATIO", 0.80)  # compress down to 80%

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CompressionCandidate:
    eid: int
    born_step: int
    summary: str
    score: float = 0.0          # composite compression score (higher = more compressible)
    j_score: float = 0.0        # relational importance (inverted: higher = LESS important)
    z_score: float = 0.0        # geometric organization (higher = more compressible)
    route: str = "short_path"   # "short_path" or "long_path"
    motif_id: Optional[str] = None
    memory_class: str = "core"
    tier: str = ""


@dataclass
class CompressionEvent:
    step: int
    trigger: str                # "corridor_exit" | "cycle_stage_change" | "emergency_tear" | "count_overflow" | "periodic" | "manual"
    candidates_evaluated: int = 0
    compressed: int = 0
    exported_deep: int = 0
    retained: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# EventDetector — detects corridor transition events from tri_mod signals
# ---------------------------------------------------------------------------

class EventDetector:
    """Detects discrete event boundaries from kernel tri_mod signals.

    Triggers (in priority order):
      1. emergency_tear    — tearing_risk > threshold while in_corridor
      2. corridor_exit     — in_corridor True→False
      3. cycle_stage_change — kernel phase transition
      4. count_overflow    — memory count exceeds threshold (fallback)
      5. periodic          — N steps since last compression (fallback)

    Geometric triggers (1-3) always take priority over fallback triggers (4-5).
    Fallback triggers respect a cooldown period after ANY compression event.
    """

    def __init__(self) -> None:
        self.prev_in_corridor: Optional[bool] = None
        self.prev_cycle_stage: Optional[int] = None
        self.prev_identity_state: Optional[str] = None
        self.warning_active: bool = False
        self._prev_tear: float = 0.0
        self._prev_align: float = 1.0
        # Fallback trigger state (Proposal A)
        self.last_compression_step: int = 0
        self.compression_events_total: int = 0

    def record_compression(self, step: int) -> None:
        """Called after a compression event to update cooldown tracking."""
        self.last_compression_step = step
        self.compression_events_total += 1

    def check(
        self,
        tri_mod: dict,
        step: int,
        memory_count: int = 0,
    ) -> Optional[str]:
        """Return trigger type string if event boundary detected, else None.

        Args:
            tri_mod: modulation dict from TriOctaMemoryKernel.process()
            step: current conversation step
            memory_count: current private memory count for this agent (for fallback triggers)

        Returns:
            "corridor_exit" | "cycle_stage_change" | "emergency_tear"
            | "count_overflow" | "periodic" | None
        """
        in_corridor = bool(tri_mod.get("in_corridor", False))
        cycle_stage = tri_mod.get("cycle_stage")
        tearing_risk = float(tri_mod.get("tearing_risk", 0.0) or 0.0)

        trigger: Optional[str] = None

        # Priority 1: emergency tearing while inside corridor
        if in_corridor and tearing_risk > COMPRESS_TEAR_EMERGENCY:
            trigger = "emergency_tear"

        # Priority 2: corridor exit (True→False)
        elif self.prev_in_corridor is True and not in_corridor:
            trigger = "corridor_exit"

        # Priority 3: cycle stage change
        elif (self.prev_cycle_stage is not None
              and cycle_stage is not None
              and cycle_stage != self.prev_cycle_stage):
            trigger = "cycle_stage_change"

        # Priority 4-5: fallback triggers (only if geometric triggers didn't fire)
        elif self._fallback_cooldown_ok(step):
            # Priority 4: count overflow — hard safety rail
            if memory_count > COMPRESS_COUNT_THRESHOLD:
                trigger = "count_overflow"
            # Priority 5: periodic maintenance
            elif (step - self.last_compression_step) > COMPRESS_STEP_INTERVAL:
                trigger = "periodic"

        # Update state for next call
        self.prev_in_corridor = in_corridor
        if cycle_stage is not None:
            self.prev_cycle_stage = cycle_stage
        identity_state = tri_mod.get("identity_state")
        if identity_state is not None:
            self.prev_identity_state = str(identity_state)

        # Update warning horizon signals
        self._update_warning(tri_mod)

        return trigger

    def _fallback_cooldown_ok(self, step: int) -> bool:
        """Return True if enough steps have passed since last compression for fallback."""
        return (step - self.last_compression_step) >= COMPRESS_FALLBACK_COOLDOWN

    def _update_warning(self, tri_mod: dict) -> None:
        """Track warning horizon: tearing rising + alignment falling."""
        tear = float(tri_mod.get("tearing_risk", 0.0) or 0.0)
        align = float(tri_mod.get("align_ema", 1.0) or 1.0)

        tear_rising = tear > self._prev_tear + 0.05
        align_falling = align < self._prev_align - 0.05

        self.warning_active = tear_rising or align_falling

        self._prev_tear = tear
        self._prev_align = align

    def is_warning(self) -> bool:
        """True if warning horizon is active (pre-computation recommended)."""
        return self.warning_active

    def state_dict(self) -> Dict[str, Any]:
        """Serializable state for status endpoint."""
        return {
            "prev_in_corridor": self.prev_in_corridor,
            "prev_cycle_stage": self.prev_cycle_stage,
            "prev_identity_state": self.prev_identity_state,
            "warning_active": self.warning_active,
            "last_compression_step": self.last_compression_step,
            "compression_events_total": self.compression_events_total,
        }


# ---------------------------------------------------------------------------
# CompressionScorer — J→Z ordered scoring of memory nodes
# ---------------------------------------------------------------------------

def _protected_via_lifecycle(payload: dict, *, site: str):
    """Q2-D shared protected check for compression.py readers
    (``derive_retention_tier`` from Slice 5-b and
    ``CompressionScorer._is_protected`` from Slice 5-c). Mirrors
    ``governance._is_protected_via_lifecycle`` with a caller-supplied
    site name in the disagreement log; deliberately duplicated from
    governance rather than imported to avoid cross-module coupling
    on a transitional helper.

    Parameters
    ----------
    payload : dict
        The memory row dict to consult.
    site : str
        Caller name to include in disagreement warning logs (e.g.,
        ``"derive_retention_tier"`` or
        ``"CompressionScorer._is_protected"``). Lets a single shared
        helper produce accurate per-site audit messages.

    Returns:
        ``True``  -- lifecycle envelope decisively says state=PROTECTED
                     and the envelope is safe to decide from (row-
                     authoritative, no disagreement with legacy
                     markers).
        ``False`` -- lifecycle envelope is decisively in a non-PROTECTED
                     row-authoritative state with no disagreement.
        ``None``  -- the lifecycle path cannot safely decide; the
                     caller should fall back to the legacy
                     protected-marker branch (canon/kind/tier/
                     srg.is_crystal).

    Returns ``None`` (fall back to legacy) when:

    * ``read_lifecycle_envelope(payload)`` raises ``LifecycleStateError``
      (payload is not a dict, or carries a malformed
      ``lifecycle_status``).
    * ``assert_lifecycle_row_authoritative(env)`` raises
      ``NonAuthoritativeLifecycleError`` (the envelope announces a
      side-channel join is required; the row alone cannot decide).
    * ``detect_lifecycle_legacy_marker_disagreement(payload)`` reports
      a ``STATE_MISMATCH`` or ``AUTHORITY_MISMATCH``. The detector
      itself raising ``LifecycleStateError`` (malformed) is also a
      fall-back trigger -- belt and braces.

    On disagreement, emits a ``WARNING`` log line so operators can
    observe real-world incidence of explicit/legacy conflicts during
    the soft-migration period. Future Q2-D Slice 6 will remove the
    legacy fallback once disagreement incidence is acceptable.

    Second production consumer of the Q2-F enforcement primitive
    (``assert_lifecycle_row_authoritative``). The Q2-F guard's raise
    is caught here and converted to "decline to decide" -- not
    propagated. Soft-migration shape, mirroring Slice 5.
    """
    # Inline imports match the existing compression.py style (see
    # ``CompressionScorer._is_protected``'s late import of
    # ``governance.is_compression_protected``). Keeps the diff narrow.
    from .lifecycle import (
        LifecycleState,
        LifecycleStateError,
        NonAuthoritativeLifecycleError,
        assert_lifecycle_row_authoritative,
        detect_lifecycle_legacy_marker_disagreement,
        read_lifecycle_envelope,
    )
    try:
        env = read_lifecycle_envelope(payload)
    except LifecycleStateError:
        return None
    try:
        assert_lifecycle_row_authoritative(env)
    except NonAuthoritativeLifecycleError:
        return None
    try:
        disagreement = detect_lifecycle_legacy_marker_disagreement(payload)
    except LifecycleStateError:
        return None
    if disagreement is not None:
        logger.warning(
            "Q2-D lifecycle/legacy-marker disagreement at %s: kind=%s "
            "explicit_state=%s explicit_via=%s derived_via=%s; falling "
            "back to legacy protected-marker branch",
            site,
            disagreement.kind.value,
            disagreement.explicit_state.value,
            disagreement.explicit_via.value,
            disagreement.derived_via.value,
        )
        return None
    return env.state is LifecycleState.PROTECTED


def derive_retention_tier(payload: dict) -> str:
    """Derive retention tier from payload fields at scoring time (Proposal D).

    No migration needed — tier is computed from existing payload fields.

    Returns one of: "protected", "identity", "relational", "situational", "echo"

    Q2-D Slice 5-b (soft migration): the protected branch is now
    lifecycle-first. The Q2-D Slice 1 derivation helper (via the
    Slice 2 read shim) provides a single canonical answer for "is
    this row protected?" that uses the same five legacy markers
    (canon, kind, tier, srg.is_crystal, governance.protected) as a
    fallback when no explicit envelope is present.

    Protected-branch behavior:

    * lifecycle path decisively says PROTECTED -> return "protected"
    * lifecycle path decisively says non-PROTECTED -> SKIP the legacy
      protected-marker checks and fall through to identity/echo/
      tool_result/relational/situational logic
    * lifecycle path declines to decide (malformed envelope, join-
      required envelope, or explicit-vs-legacy disagreement) ->
      fall back to the legacy protected-marker checks (canon, kind,
      tier, srg.is_crystal) verbatim, then continue to non-protected
      tier logic if no legacy protected marker matched

    The non-protected tier logic (identity, echo, tool_result,
    relational, situational) is untouched by Slice 5-b. Branches 2-6
    of this function remain byte-identical to pre-Slice-5-b behavior.

    Future Slice 6 will remove the legacy fallback inside the
    protected branch.
    """
    # Q2-D Slice 5-b: lifecycle-first protected check.
    lifecycle_protected = _protected_via_lifecycle(
        payload, site="derive_retention_tier",
    )
    if lifecycle_protected is True:
        return "protected"
    if lifecycle_protected is None:
        # Legacy protected-marker fallback. Preserved verbatim from
        # pre-Slice-5-b behavior; the 4 checks below run only when
        # the lifecycle path cannot safely decide.
        if payload.get("canon") is True:
            return "protected"
        kind = str(payload.get("kind", payload.get("type", "")) or "")
        if kind in ("seed", "identity", "core_identity"):
            return "protected"
        tier_field = str(payload.get("tier", "") or "")
        if tier_field == "core_identity":
            return "protected"
        srg = payload.get("srg")
        if isinstance(srg, dict) and srg.get("is_crystal", False):
            return "protected"
    # When lifecycle_protected is False, we skip the legacy protected
    # branch and fall through directly to the non-protected tier logic
    # below. The lifecycle envelope decisively said this row is NOT
    # protected; respect that even if no legacy marker disagreed.

    # Identity: half_life >= 365 days
    hl = float(payload.get("half_life", payload.get("half_life_days", 0)) or 0)
    if hl >= 365:
        return "identity"

    # Echo: collective provenance (dict or legacy bare string)
    _prov = payload.get("provenance")
    _is_collective = (
        _prov == "collective"  # legacy bare string
        or (isinstance(_prov, dict) and _prov.get("source_type") == "collective_echo")
    )
    if _is_collective:
        return "echo"

    # Tool result: external observation, decays faster than experiential memory
    if isinstance(_prov, dict) and _prov.get("source_type") == "tool_result":
        return "tool_result"

    # Relational: half_life >= 7 days
    if hl >= 7:
        return "relational"

    # Default: situational
    return "situational"


class CompressionScorer:
    """Score memory nodes for compression eligibility.

    J-score (relational, 60% weight) — evaluated first per RGD temporal ordering:
      - retrieval_count: more retrieved = more important (resist compression)
      - strength: stronger = resist
      - canon: True → PROTECTED, never compress
      - motif membership in active basin → resist

    Z-score (geometric, 40% weight) — evaluated second:
      - coherence field role: basin members resist, plateau members compress
      - phi proximity to zero: ambiguous reinforcement = compress candidate
      - tension: high tension = unresolved = resist (keep for resolution)
    """

    PROTECTED_KINDS = frozenset({"seed", "identity", "core_identity"})
    PROTECTED_TIERS = frozenset({"core_identity"})

    def __init__(
        self,
        min_age_steps: int = COMPRESS_MIN_AGE,
        max_candidates: int = COMPRESS_MAX_CANDIDATES,
    ) -> None:
        self.min_age_steps = int(min_age_steps)
        self.max_candidates = int(max_candidates)

    def _is_protected(self, payload: dict) -> bool:
        """Return True if this node must never be compressed.

        Legacy fallback checks (in order):
            1. Canon flag (existing)
            2. Protected kinds — seed, anchor, identity_anchor (existing)
            3. Protected tiers — core_identity (existing)
            4. Governance 'protected' flag (Phase D addition, via
               ``governance.is_compression_protected``)

        Q2-D Slice 5-c (soft migration): the scorer's protected check
        is now lifecycle-first via :func:`_protected_via_lifecycle`,
        the same helper used by Slice 5-b's
        ``derive_retention_tier``. If the lifecycle path decisively
        says protected/non-protected, that answer wins. If the
        lifecycle path declines (malformed envelope, join-required
        envelope, or explicit/legacy disagreement), the legacy
        fallback above runs verbatim. A warning is logged on
        disagreement so operators can observe explicit/legacy
        conflicts during the soft-migration period; future Slice 6
        will remove the fallback.

        Behavior unification: after Slice 5-c, a payload with
        ``srg.is_crystal=True`` and no other markers returns True
        (was False pre-Slice-5-c). The other two protected readers
        already treat ``srg.is_crystal`` as protected via the
        lifecycle path; Slice 5-c brings the scorer into alignment.

        Invariant: protected memories are never weakened automatically.
        """
        # Q2-D Slice 5-c: lifecycle-first protected check.
        lifecycle_protected = _protected_via_lifecycle(
            payload, site="CompressionScorer._is_protected",
        )
        if lifecycle_protected is True:
            return True
        if lifecycle_protected is False:
            # Lifecycle decisively says non-PROTECTED. Skip legacy
            # fallback and return False directly.
            return False
        # lifecycle_protected is None -> legacy fallback (existing
        # inline + governance-delegation logic, preserved verbatim).
        if payload.get("canon") is True:
            return True
        kind = str(payload.get("kind", payload.get("type", "")) or "")
        if kind in self.PROTECTED_KINDS:
            return True
        tier = str(payload.get("tier", "") or "")
        if tier in self.PROTECTED_TIERS:
            return True
        # Phase D: governance flag check
        try:
            from .governance import is_compression_protected
            if is_compression_protected(payload):
                return True
        except ImportError as e:
            logger.debug("Governance check unavailable: %s", e)
        return False

    def score(
        self,
        node: dict,
        current_step: int,
        coherence_field: Optional[List[dict]] = None,
    ) -> Optional[CompressionCandidate]:
        """Score a single memory node for compressibility.

        Args:
            node: dict with at least {eid, born_step, payload} or flat payload fields
            current_step: current conversation step
            coherence_field: list of MotifFieldState dicts from compute_coherence_field()

        Returns:
            CompressionCandidate if eligible, None if protected/too young
        """
        payload = node.get("payload", node)  # support both wrapped and flat
        eid = int(node.get("eid", payload.get("eid", 0)))
        born_step = int(
            node.get("born_step", payload.get("created_at", payload.get("born_step", 0))) or 0
        )

        # Derive retention tier (Proposal D)
        retention_tier = derive_retention_tier(payload)

        # Protection check — both legacy and tier-based
        if retention_tier == "protected" or self._is_protected(payload):
            return None

        # Identity tier: only long-path deep export, never short-path weakened
        # (handled in router, but we still score them)

        # Age check
        age = current_step - born_step
        if age < self.min_age_steps:
            return None

        # --- J-score (relational importance, inverted for compressibility) ---
        strength = float(payload.get("strength", 0.5) or 0.5)
        retrieval_count = int(payload.get("retrieval_count", 0) or 0)
        motif_id = payload.get("motif_id") or None

        # Normalize retrieval resistance: log scale, capped at ~10 retrievals
        retrieval_resist = min(1.0, np.log1p(retrieval_count) / np.log(11.0))

        # Motif basin membership resistance
        basin_resist = 0.0
        if motif_id and coherence_field:
            for mf in coherence_field:
                if str(mf.get("motif_id", "")) == str(motif_id):
                    role = str(mf.get("role", ""))
                    if role == "basin":
                        basin_resist = 0.6   # strong resistance
                    elif role == "ridge":
                        basin_resist = 0.3   # moderate
                    # plateau = 0.0 (no resistance)
                    break

        # J-score: higher = LESS compressible (we invert for composite)
        j_importance = (
            0.35 * strength
            + 0.35 * retrieval_resist
            + 0.30 * basin_resist
        )
        # Invert: j_score = 1 - importance → higher = more compressible
        j_score = 1.0 - j_importance

        # --- Z-score (geometric compressibility) ---
        phi_compressible = 0.5  # default: neutral
        tension_resist = 0.0
        role_compress = 0.5     # default: neutral

        if coherence_field and motif_id:
            for mf in coherence_field:
                if str(mf.get("motif_id", "")) == str(motif_id):
                    phi = float(mf.get("phi", 0.0) or 0.0)
                    tension = float(mf.get("tension", 0.0) or 0.0)
                    role = str(mf.get("role", ""))

                    # Near-zero phi = ambiguous reinforcement = compress
                    phi_compressible = 1.0 - min(1.0, abs(phi))

                    # High tension = unresolved = keep
                    tension_resist = min(1.0, tension)

                    # Role: plateau → compress, basin → resist
                    if role == "plateau":
                        role_compress = 0.8
                    elif role == "ridge":
                        role_compress = 0.5
                    elif role == "basin":
                        role_compress = 0.2
                    break

        z_score = (
            0.40 * phi_compressible
            + 0.30 * (1.0 - tension_resist)  # invert: low tension → compressible
            + 0.30 * role_compress
        )

        # Phase-cycle duration resistance: sustained memories resist compression
        _phase_dur = int(payload.get("phase_duration_steps", 0) or 0)
        _corridor_dur = int(payload.get("corridor_duration_steps", 0) or 0)
        _sustained = max(_phase_dur, _corridor_dur)
        if _sustained >= 10:  # PHASE_DURATION_RESIST_THRESHOLD
            j_score = max(0.0, j_score - 0.15)  # PHASE_DURATION_RESIST_BONUS

        # SRG compression resistance (opt-in, reads payload only)
        _srg_pay = payload.get("srg")
        if _srg_pay and isinstance(_srg_pay, dict):
            # Crystal memories are NEVER compressed
            if _srg_pay.get("is_crystal", False):
                return None
            # Class A heartbeat = deep memory = 15% harder to compress
            if _srg_pay.get("heartbeat_class") == "A":
                j_score *= 0.85
            # High R (near fixed-point lock) = resists compression
            _srg_R = float(_srg_pay.get("R", 0.0) or 0.0)
            if _srg_R > 0.15:
                j_score *= (1.0 - 0.1 * min(1.0, _srg_R / 0.176))

        # Composite: J-weighted 60%, Z-weighted 40% (per RGD ordering)
        composite = 0.60 * j_score + 0.40 * z_score

        # Tier-based score adjustment (Proposal D)
        # Echo memories are slightly more compressible; relational slightly less
        if retention_tier == "echo":
            composite = min(1.0, composite * 1.15)   # +15% compressibility
        elif retention_tier == "tool_result":
            composite = min(1.0, composite * COMPRESS_TOOL_RESULT_SCORE_MULT)  # +10% compressibility
        elif retention_tier == "relational":
            composite = max(0.0, composite * 0.85)   # -15% compressibility (more resistant)
        elif retention_tier == "identity":
            composite = max(0.0, composite * 0.70)   # -30% compressibility (strong resistance)

        summary = str(payload.get("summary", payload.get("text", "")) or "")
        memory_class = str(payload.get("memory_class", "core") or "core")

        return CompressionCandidate(
            eid=eid,
            born_step=born_step,
            summary=summary[:200],  # truncate for candidate record
            score=round(composite, 4),
            j_score=round(j_score, 4),
            z_score=round(z_score, 4),
            motif_id=str(motif_id) if motif_id else None,
            memory_class=memory_class,
            tier=retention_tier,
        )

    def select_candidates(
        self,
        nodes: Sequence[dict],
        current_step: int,
        coherence_field: Optional[List[dict]] = None,
    ) -> List[CompressionCandidate]:
        """Score all eligible nodes, return top candidates sorted by score (highest first)."""
        candidates: List[CompressionCandidate] = []
        for node in nodes:
            c = self.score(node, current_step, coherence_field)
            if c is not None:
                candidates.append(c)

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[: self.max_candidates]


# ---------------------------------------------------------------------------
# CompressionRouter — decides short-path vs long-path
# ---------------------------------------------------------------------------

class CompressionRouter:
    """Route compression candidates to short-path or long-path.

    Long-path (deep memory export):
      - compression score > deep_threshold AND age > age_threshold
      - OR memory_class == "archive" (document chunks always go deep)

    Short-path (re-file in core, reduced strength):
      - everything else
    """

    def __init__(
        self,
        deep_threshold: float = COMPRESS_DEEP_THRESHOLD,
        age_threshold_steps: int = COMPRESS_AGE_THRESHOLD,
    ) -> None:
        self.deep_threshold = float(deep_threshold)
        self.age_threshold_steps = int(age_threshold_steps)

    def route(self, candidate: CompressionCandidate, current_step: int) -> str:
        """Determine compression route for a candidate.

        Returns "short_path" or "long_path".
        """
        age = current_step - candidate.born_step

        # Tier-specific routing (Proposal D)
        # Identity tier: ONLY long-path deep export, never short-path weakened
        if candidate.tier == "identity":
            return "long_path"

        # Echo tier: deep export after fewer steps (COMPRESS_ECHO_DEEP_AGE)
        if candidate.tier == "echo" and age >= COMPRESS_ECHO_DEEP_AGE:
            return "long_path"

        # Archive memories always go deep
        if candidate.memory_class == "archive":
            return "long_path"

        # High score + old enough → deep export
        if candidate.score >= self.deep_threshold and age >= self.age_threshold_steps:
            return "long_path"

        return "short_path"

    def route_all(
        self,
        candidates: List[CompressionCandidate],
        current_step: int,
    ) -> List[CompressionCandidate]:
        """Route all candidates, updating their route field in place."""
        for c in candidates:
            c.route = self.route(c, current_step)
        return candidates


# ---------------------------------------------------------------------------
# CompressionExecutor — executes compression decisions
# ---------------------------------------------------------------------------

class CompressionExecutor:
    """Execute compression: short-path modifies core, long-path exports to deep store."""

    def __init__(
        self,
        memory_graph,      # MemoryGraph instance (PrivateMemoryGraph)
        deep_store,        # DeepMemoryStore instance
        coherence_field_fn=None,  # callable() -> List[dict]
    ) -> None:
        self.memory_graph = memory_graph
        self.deep_store = deep_store
        self.coherence_field_fn = coherence_field_fn
        self.history: List[CompressionEvent] = []

    def execute(
        self,
        candidates: List[CompressionCandidate],
        step: int,
        trigger: str,
    ) -> CompressionEvent:
        """Execute compression on routed candidates.

        Short-path: reduce strength, mark compressed=True
        Long-path: export to deep store, mark exported=True, reduce strength to minimum
        """
        event = CompressionEvent(
            step=step,
            trigger=trigger,
            candidates_evaluated=len(candidates),
        )

        for c in candidates:
            try:
                if c.route == "long_path":
                    self._execute_long_path(c, step)
                    event.exported_deep += 1
                else:
                    self._execute_short_path(c, step)
                    event.compressed += 1
            except Exception as exc:
                logger.warning("compression failed for eid=%d: %s", c.eid, exc)
                event.retained += 1

        self.history.append(event)
        return event

    def _execute_short_path(self, candidate: CompressionCandidate, step: int) -> None:
        """Reduce strength, mark compressed in core memory.

        Tier-specific multipliers (Proposal D):
          - relational: 0.7x (gentler)
          - echo: 0.4x (slightly aggressive, per ChatGPT review)
          - situational/default: 0.5x
        """
        ent = self.memory_graph.entities.get(candidate.eid)
        if ent is None:
            raise KeyError(f"Entity {candidate.eid} not found in memory graph")

        # Select tier-specific multiplier
        if candidate.tier == "relational":
            mult = COMPRESS_RELATIONAL_MULT
        elif candidate.tier == "echo":
            mult = COMPRESS_ECHO_MULT
        elif candidate.tier == "tool_result":
            mult = COMPRESS_TOOL_RESULT_MULT
        else:
            mult = COMPRESS_SHORT_PATH_MULT

        payload = ent.payload or {}
        old_strength = float(payload.get("strength", 0.5) or 0.5)
        new_strength = max(0.05, old_strength * mult)

        patch = {
            "strength": round(new_strength, 4),
            "compressed": True,
            "compressed_step": step,
            "compression_route": "short_path",
            "compression_score": candidate.score,
            "compression_tier": candidate.tier,
        }
        self.memory_graph.update_payload(candidate.eid, patch)

    def _execute_long_path(self, candidate: CompressionCandidate, step: int) -> None:
        """Export to deep memory store, mark exported in core."""
        ent = self.memory_graph.entities.get(candidate.eid)
        if ent is None:
            raise KeyError(f"Entity {candidate.eid} not found in memory graph")

        payload = ent.payload or {}

        # Try to load embedding for deep store
        embedding = None
        try:
            from .embedding_store import load_embedding as _load_emb
            embedding = _load_emb(
                candidate.eid, payload,
                self.memory_graph._shard_reader,
                self.memory_graph.data_dir,
            )
        except Exception as e:
            logger.debug("Could not load embedding for deep store: %s", e)

        # Export to deep store
        self.deep_store.export(candidate, embedding, payload, step=step)

        # Mark exported in core with minimal strength
        patch = {
            "strength": COMPRESS_LONG_PATH_STRENGTH,
            "exported_deep": True,
            "exported_step": step,
            "compression_route": "long_path",
            "compression_score": candidate.score,
        }
        self.memory_graph.update_payload(candidate.eid, patch)

    def get_history(self) -> List[Dict[str, Any]]:
        """Return compression event history as serializable dicts."""
        return [e.to_dict() for e in self.history]


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------

def try_compress(
    fabric_instance,
    agent_id: str,
    tri_mod: dict,
    step: int,
    workspace_id: str = "default",
) -> Optional[CompressionEvent]:
    """Called from fabric.ingest() after checkpoint phase.

    1. EventDetector.check(tri_mod, step) → trigger or None
    2. On trigger: load nodes → score → route → execute → log
    3. Returns CompressionEvent or None if no trigger

    Args:
        fabric_instance: TormentFabric instance (for graph/store access)
        agent_id: agent whose memories to compress
        tri_mod: modulation dict from kernel
        step: current conversation step
        workspace_id: workspace scope for composite key isolation
    """
    # Composite key for workspace-scoped dict access
    from .fabric import TormentFabric
    ak = TormentFabric._agent_key(workspace_id, agent_id)

    # Lazy-init per-agent detector
    if not hasattr(fabric_instance, "_event_detectors"):
        fabric_instance._event_detectors = {}
    if ak not in fabric_instance._event_detectors:
        fabric_instance._event_detectors[ak] = EventDetector()

    detector = fabric_instance._event_detectors[ak]

    # Get memory graph for this agent (keyed by composite key)
    graph = fabric_instance.private_graphs.get(ak)
    if graph is None:
        logger.warning("no private graph for agent=%s ws=%s, skipping compression", agent_id, workspace_id)
        return None

    # Pass memory count to detector for fallback triggers (Proposal A)
    memory_count = len(graph.entities) if hasattr(graph, "entities") else 0
    trigger = detector.check(tri_mod, step, memory_count=memory_count)

    if trigger is None:
        return None

    logger.info("compression trigger=%s at step=%d for agent=%s ws=%s (mem_count=%d)",
                trigger, step, agent_id, workspace_id, memory_count)

    # Get or create deep store
    deep_store = _get_or_create_deep_store(fabric_instance, agent_id, workspace_id)

    # Load motifs for coherence field
    coherence_field = None
    try:
        motifs_path = _find_motifs_path(fabric_instance, agent_id, workspace_id)
        if motifs_path and os.path.exists(motifs_path):
            with open(motifs_path, "r", encoding="utf-8") as f:
                motifs_data = json.load(f)
            if isinstance(motifs_data, dict):
                motifs_data = motifs_data.get("motifs", [])
            coherence_field = compute_coherence_field(motifs_data)
    except Exception as exc:
        logger.debug("coherence field unavailable: %s", exc)

    # Build node list from graph entities
    nodes = []
    for eid, ent in graph.entities.items():
        payload = dict(ent.payload or {})
        nodes.append({
            "eid": int(eid),
            "born_step": int(getattr(ent, "born_step", 0) or 0),
            "payload": payload,
        })

    # Score — max_candidates varies by trigger type
    scorer = CompressionScorer()
    candidates = scorer.select_candidates(nodes, step, coherence_field)

    # Trigger-specific candidate filtering (Proposal A)
    if trigger == "periodic":
        # Periodic: only compress candidates scoring above the floor
        candidates = [c for c in candidates if c.score >= COMPRESS_PERIODIC_FLOOR]
    elif trigger == "count_overflow":
        # Count overflow: compress enough to drop below 80% of threshold
        target_count = int(COMPRESS_COUNT_THRESHOLD * 0.80)
        excess = memory_count - target_count
        if excess > 0:
            # Take at most `excess` candidates (already sorted by score desc)
            candidates = candidates[:excess]

    if not candidates:
        logger.debug("no compression candidates at step=%d (trigger=%s)", step, trigger)
        return CompressionEvent(step=step, trigger=trigger)

    # Route
    router = CompressionRouter()
    router.route_all(candidates, step)

    # Execute
    executor = CompressionExecutor(graph, deep_store)
    event = executor.execute(candidates, step, trigger)

    # Record compression in detector for cooldown tracking (Proposal A)
    detector.record_compression(step)

    # Persist executor in fabric for history access (composite key)
    if not hasattr(fabric_instance, "_compression_executors"):
        fabric_instance._compression_executors = {}
    fabric_instance._compression_executors[ak] = executor

    # Log to compression_log.jsonl
    _log_compression_event(fabric_instance, agent_id, event, workspace_id)

    return event


def check_hard_cap(
    fabric_instance,
    agent_id: str,
    step: int,
    workspace_id: str = "default",
) -> Optional[CompressionEvent]:
    """Last-resort safety net: if memory count exceeds HARD_CAP, force-compress.

    This runs AFTER try_compress and is independent of EventDetector triggers.
    It's the absolute ceiling — should rarely fire if fallback triggers are healthy.
    """
    from .fabric import TormentFabric
    ak = TormentFabric._agent_key(workspace_id, agent_id)

    graph = fabric_instance.private_graphs.get(ak)
    if graph is None:
        return None

    memory_count = len(graph.entities) if hasattr(graph, "entities") else 0
    if memory_count <= COMPRESS_HARD_CAP:
        return None

    target = int(COMPRESS_HARD_CAP * COMPRESS_HARD_CAP_TARGET)
    excess = memory_count - target
    logger.warning(
        "HARD CAP triggered: agent=%s ws=%s count=%d > cap=%d, compressing %d",
        agent_id, workspace_id, memory_count, COMPRESS_HARD_CAP, excess,
    )

    deep_store = _get_or_create_deep_store(fabric_instance, agent_id, workspace_id)

    # Score all nodes
    nodes = []
    for eid, ent in graph.entities.items():
        payload = dict(ent.payload or {})
        nodes.append({
            "eid": int(eid),
            "born_step": int(getattr(ent, "born_step", 0) or 0),
            "payload": payload,
        })

    scorer = CompressionScorer(min_age_steps=0)  # override min_age for emergency
    candidates = scorer.select_candidates(nodes, step)
    candidates = candidates[:excess]

    if not candidates:
        return None

    router = CompressionRouter()
    router.route_all(candidates, step)

    executor = CompressionExecutor(graph, deep_store)
    event = executor.execute(candidates, step, "hard_cap")

    _log_compression_event(fabric_instance, agent_id, event, workspace_id)
    return event


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deep_store_location(fabric_instance, agent_id: str, workspace_id: str = "default"):
    """Return the validated deep-store cache key, data root, and base path."""
    from .fabric import TormentFabric
    ak = TormentFabric._agent_key(workspace_id, agent_id)
    if not hasattr(fabric_instance, "_deep_stores"):
        fabric_instance._deep_stores = {}
    from .pathing import safe_slug

    # Validate dynamic components before embedding in a path.
    safe_slug(workspace_id, "workspace_id")
    safe_slug(agent_id, "agent_id")

    # Build path under the canonical data root and verify containment
    # (inline startswith is CodeQL's recognised sanitiser).
    _data_root = os.path.realpath(str(fabric_instance.data_dir))
    _base = os.path.realpath(os.path.join(
        _data_root, "workspaces", workspace_id,
        "agents", agent_id, "deep_memory",
    ))
    if not _base.startswith(_data_root + os.sep):
        raise ValueError(
            f"Deep memory path escapes data root: {_base!r}"
        )
    return ak, _data_root, Path(_base)


def _get_or_create_deep_store(fabric_instance, agent_id: str, workspace_id: str = "default"):
    """Lazy-init deep memory store for an agent (workspace-scoped)."""
    ak, _data_root, _base = _deep_store_location(
        fabric_instance, agent_id, workspace_id
    )
    if ak not in fabric_instance._deep_stores:
        from .deep_memory import DeepMemoryStore

        fabric_instance._deep_stores[ak] = DeepMemoryStore(
            _base, trusted_root=_data_root,
        )
    return fabric_instance._deep_stores[ak]


def _attach_persisted_deep_store(
    fabric_instance,
    agent_id: str,
    workspace_id: str = "default",
):
    """Attach an existing persisted deep store without creating one.

    Retrieval uses this after the compression feature guard. The only
    existence gate is the validated ``deep_memory/memories.jsonl`` file:
    absent stores return None without constructing DeepMemoryStore, so a
    no-deep-memory query cannot create deep-memory directories or files.
    """
    from .fabric import TormentFabric

    ak = TormentFabric._agent_key(workspace_id, agent_id)
    if not hasattr(fabric_instance, "_deep_stores"):
        fabric_instance._deep_stores = {}
    cached = fabric_instance._deep_stores.get(ak)
    if cached is not None:
        return cached

    ak, _data_root, _base = _deep_store_location(
        fabric_instance, agent_id, workspace_id
    )

    _memories = os.path.realpath(os.path.join(str(_base), "memories.jsonl"))
    if not _memories.startswith(_data_root + os.sep):
        raise ValueError(
            f"Deep memory file path escapes data root: {_memories!r}"
        )
    if not os.path.isfile(_memories):
        return None

    with fabric_instance.locks.agent_lock(workspace_id, agent_id):
        cached = fabric_instance._deep_stores.get(ak)
        if cached is not None:
            return cached
        if not os.path.isfile(_memories):
            return None

        from .deep_memory import DeepMemoryStore

        store = DeepMemoryStore(_base, trusted_root=_data_root)
        fabric_instance._deep_stores[ak] = store
        return store


def _find_motifs_path(fabric_instance, agent_id: str, workspace_id: str = "default") -> Optional[str]:
    """Locate motifs.json for an agent (workspace-scoped).

    All candidate paths are resolved via ``os.path.realpath`` and verified
    to stay inside the canonical data root before any filesystem access.
    """
    raw_data_dir = getattr(fabric_instance, "data_dir", "data")
    safe_ws = _validate_path_component(workspace_id, "workspace_id")
    safe_agent = _validate_path_component(agent_id, "agent_id")

    # Canonicalize the data root once.
    base = os.path.realpath(raw_data_dir)

    # Check workspace-scoped paths first, then legacy flat paths as fallback
    candidates = [
        os.path.join(base, "workspaces", safe_ws, "agents", safe_agent, "private", "motifs.json"),
        os.path.join(base, "workspaces", safe_ws, "agents", safe_agent, "motifs.json"),
        # Legacy flat paths (for backward compatibility with pre-workspace layouts)
        os.path.join(base, "agents", safe_agent, "private", "motifs.json"),
        os.path.join(base, "agents", safe_agent, "motifs.json"),
    ]
    for p in candidates:
        resolved = os.path.realpath(p)
        if not resolved.startswith(base + os.sep):
            continue
        if os.path.exists(resolved):
            return resolved
    return None


def _log_compression_event(fabric_instance, agent_id: str, event: CompressionEvent, workspace_id: str = "default") -> None:
    """Append compression event to agent's compression_log.jsonl (workspace-scoped).

    Path sanitisation is fully inlined (``os.path.realpath`` →
    ``startswith`` guard → sinks) so CodeQL sees the trust chain
    without crossing function boundaries.
    """
    try:
        base = os.path.realpath(getattr(fabric_instance, "data_dir", "data"))
        safe_workspace_id = _validate_path_component(workspace_id, "workspace_id")
        safe_agent_id = _validate_path_component(agent_id, "agent_id")

        log_dir = os.path.realpath(
            os.path.join(
                base,
                "workspaces",
                safe_workspace_id,
                "agents",
                safe_agent_id,
                "private",
            )
        )
        if not log_dir.startswith(base + os.sep):
            return
        os.makedirs(log_dir, exist_ok=True)

        log_path = os.path.realpath(os.path.join(log_dir, "compression_log.jsonl"))
        if not log_path.startswith(log_dir + os.sep):
            return
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("failed to log compression event: %s", exc)
