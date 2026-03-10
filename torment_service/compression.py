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
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .coherence_field import compute_coherence_field

logger = logging.getLogger(__name__)

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
    trigger: str                # "corridor_exit" | "cycle_stage_change" | "emergency_tear" | "manual"
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

    Triggers on:
      - in_corridor True→False  (corridor exit — primary)
      - cycle_stage change       (kernel phase transition)
      - tearing_risk > threshold while in_corridor (emergency)

    Maintains previous state for edge detection.
    """

    def __init__(self) -> None:
        self.prev_in_corridor: Optional[bool] = None
        self.prev_cycle_stage: Optional[int] = None
        self.prev_identity_state: Optional[str] = None
        self.warning_active: bool = False
        self._prev_tear: float = 0.0
        self._prev_align: float = 1.0

    def check(self, tri_mod: dict, step: int) -> Optional[str]:
        """Return trigger type string if event boundary detected, else None.

        Args:
            tri_mod: modulation dict from TriOctaMemoryKernel.process()
            step: current conversation step

        Returns:
            "corridor_exit" | "cycle_stage_change" | "emergency_tear" | None
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
        }


# ---------------------------------------------------------------------------
# CompressionScorer — J→Z ordered scoring of memory nodes
# ---------------------------------------------------------------------------

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
        """Return True if this node must never be compressed."""
        if payload.get("canon") is True:
            return True
        kind = str(payload.get("kind", payload.get("type", "")) or "")
        if kind in self.PROTECTED_KINDS:
            return True
        tier = str(payload.get("tier", "") or "")
        if tier in self.PROTECTED_TIERS:
            return True
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

        # Protection check
        if self._is_protected(payload):
            return None

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

        # Composite: J-weighted 60%, Z-weighted 40% (per RGD ordering)
        composite = 0.60 * j_score + 0.40 * z_score

        summary = str(payload.get("summary", payload.get("text", "")) or "")
        memory_class = str(payload.get("memory_class", "core") or "core")
        tier = str(payload.get("tier", "") or "")

        return CompressionCandidate(
            eid=eid,
            born_step=born_step,
            summary=summary[:200],  # truncate for candidate record
            score=round(composite, 4),
            j_score=round(j_score, 4),
            z_score=round(z_score, 4),
            motif_id=str(motif_id) if motif_id else None,
            memory_class=memory_class,
            tier=tier,
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
        """Reduce strength, mark compressed in core memory."""
        ent = self.memory_graph.entities.get(candidate.eid)
        if ent is None:
            raise KeyError(f"Entity {candidate.eid} not found in memory graph")

        payload = ent.payload or {}
        old_strength = float(payload.get("strength", 0.5) or 0.5)
        new_strength = max(0.05, old_strength * COMPRESS_SHORT_PATH_MULT)

        patch = {
            "strength": round(new_strength, 4),
            "compressed": True,
            "compressed_step": step,
            "compression_route": "short_path",
            "compression_score": candidate.score,
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
        except Exception:
            pass

        # Export to deep store
        self.deep_store.export(candidate, embedding, payload)

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
    """
    # Lazy-init per-agent detector
    if not hasattr(fabric_instance, "_event_detectors"):
        fabric_instance._event_detectors = {}
    if agent_id not in fabric_instance._event_detectors:
        fabric_instance._event_detectors[agent_id] = EventDetector()

    detector = fabric_instance._event_detectors[agent_id]
    trigger = detector.check(tri_mod, step)

    if trigger is None:
        return None

    logger.info("compression trigger=%s at step=%d for agent=%s", trigger, step, agent_id)

    # Get memory graph for this agent
    graph = fabric_instance.private_graphs.get(agent_id)
    if graph is None:
        logger.warning("no private graph for agent=%s, skipping compression", agent_id)
        return None

    # Get or create deep store
    deep_store = _get_or_create_deep_store(fabric_instance, agent_id)

    # Load motifs for coherence field
    coherence_field = None
    try:
        motifs_path = _find_motifs_path(fabric_instance, agent_id)
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

    # Score
    scorer = CompressionScorer()
    candidates = scorer.select_candidates(nodes, step, coherence_field)

    if not candidates:
        logger.debug("no compression candidates at step=%d", step)
        return CompressionEvent(step=step, trigger=trigger)

    # Route
    router = CompressionRouter()
    router.route_all(candidates, step)

    # Execute
    executor = CompressionExecutor(graph, deep_store)
    event = executor.execute(candidates, step, trigger)

    # Persist executor in fabric for history access
    if not hasattr(fabric_instance, "_compression_executors"):
        fabric_instance._compression_executors = {}
    fabric_instance._compression_executors[agent_id] = executor

    # Log to compression_log.jsonl
    _log_compression_event(fabric_instance, agent_id, event)

    return event


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_deep_store(fabric_instance, agent_id: str):
    """Lazy-init deep memory store for an agent."""
    if not hasattr(fabric_instance, "_deep_stores"):
        fabric_instance._deep_stores = {}
    if agent_id not in fabric_instance._deep_stores:
        from .deep_memory import DeepMemoryStore
        base = Path(fabric_instance.data_dir) / "agents" / agent_id / "deep_memory"
        fabric_instance._deep_stores[agent_id] = DeepMemoryStore(base)
    return fabric_instance._deep_stores[agent_id]


def _find_motifs_path(fabric_instance, agent_id: str) -> Optional[str]:
    """Locate motifs.json for an agent."""
    data_dir = getattr(fabric_instance, "data_dir", "data")
    # Check agent private dir
    candidates = [
        os.path.join(data_dir, "agents", agent_id, "private", "motifs.json"),
        os.path.join(data_dir, "agents", agent_id, "motifs.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _log_compression_event(fabric_instance, agent_id: str, event: CompressionEvent) -> None:
    """Append compression event to agent's compression_log.jsonl."""
    try:
        data_dir = getattr(fabric_instance, "data_dir", "data")
        log_dir = os.path.join(data_dir, "agents", agent_id, "private")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "compression_log.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("failed to log compression event: %s", exc)
