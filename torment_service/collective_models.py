# collective_models.py — Data contracts for the TORMENT Hivemind layer
#
# This module defines the portable data structures for workspace-level
# resonance coupling between agents. It is NOT a replacement for the existing
# proposal/bridge governance systems — it sits above them.
#
# These contracts are used by collective_field.py, collective_policy.py,
# and the collective API endpoints in app.py.
# ---------------------------------------------------------------------------
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple


def _now_ts() -> int:
    return int(time.time())


def _new_id(prefix: str = "pkt") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# ResonancePacket — portable per-ingest collective representation
# ---------------------------------------------------------------------------

@dataclass
class ResonancePacket:
    """Lightweight snapshot of an ingest event for the collective field.

    Built from enriched signals AFTER motif/symbol/resonance processing in
    fabric.ingest(). Packets are the atoms of the collective — convergence
    events are detected by comparing packets across agents.
    """

    packet_id: str = ""
    workspace_id: str = ""
    agent_id: str = ""
    domain_id: str = ""
    source_eid: Optional[int] = None
    ts: int = 0

    # Content
    summary: str = ""
    embedding_hash: str = ""          # short hash ref (full embedding stays in graph)

    # Kernel state
    cycle_stage: str = ""             # S0..S6
    identity_state: str = ""          # s0..s8
    coherence: float = 0.0
    stability_delta: float = 0.0

    # Phase timing
    corridor_angle_deg: Optional[float] = None
    corridor_duration_steps: Optional[int] = None
    phase_duration_steps: Optional[int] = None

    # Motifs and symbols
    motifs: List[str] = field(default_factory=list)
    created_motif: Optional[str] = None

    state_symbol: Optional[str] = None
    resonance_score: Optional[float] = None
    loop_type: Optional[str] = None

    # Character drift
    drift_score: Optional[float] = None
    drift_direction: Optional[str] = None
    seed_id: Optional[str] = None

    # SRG (Crystal Attunement)
    srg_band: Optional[int] = None
    srg_heartbeat_class: Optional[str] = None
    srg_is_crystal: bool = False

    # Governance
    permissions: Dict[str, bool] = field(default_factory=lambda: {
        "shareable": True,
        "reingestable": True,
        "visible_to_workspace": True,
    })
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.packet_id:
            self.packet_id = _new_id("pkt")
        if not self.ts:
            self.ts = _now_ts()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResonancePacket":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


# ---------------------------------------------------------------------------
# ConvergenceEvent — cross-agent alignment record
# ---------------------------------------------------------------------------

@dataclass
class ConvergenceEvent:
    """Detected multi-agent resonance within a workspace/domain.

    Created when two or more agents produce semantically overlapping packets
    within a temporal window, with compatible phase/symbol state. These are
    the meaningful moments of collective alignment — not raw memory sharing.
    """

    event_id: str = ""
    workspace_id: str = ""
    domain_id: str = ""
    ts_start: int = 0
    ts_end: int = 0

    # Participants
    participating_agents: List[str] = field(default_factory=list)
    source_packets: List[str] = field(default_factory=list)
    source_eids: List[int] = field(default_factory=list)

    # Alignment metrics
    confidence: float = 0.0           # composite confidence (0-1)
    persistence: float = 0.0          # how long the overlap lasted
    semantic_overlap: float = 0.0     # cosine similarity of packet embeddings
    phase_alignment: float = 0.0      # how close agents' cycle stages are
    symbol_alignment: float = 0.0     # symbol/motif overlap score

    # Dominant collective state
    dominant_motifs: List[str] = field(default_factory=list)
    dominant_symbol: Optional[str] = None
    dominant_cycle_stage: Optional[str] = None
    dominant_identity_state: Optional[str] = None

    # Summary
    summary: str = ""

    # Policy
    policy_flags: Dict[str, bool] = field(default_factory=lambda: {
        "reingestable": True,
        "proposal_eligible": False,
    })

    def __post_init__(self) -> None:
        if not self.event_id:
            self.event_id = _new_id("cev")
        if not self.ts_start:
            self.ts_start = _now_ts()
        if not self.ts_end:
            self.ts_end = self.ts_start

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConvergenceEvent":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


# ---------------------------------------------------------------------------
# CharacterSelfState — clean API view for self-awareness
# ---------------------------------------------------------------------------

@dataclass
class CharacterSelfState:
    """Public-facing self-state for an agent's living character layer.

    Assembled from CharacterState + CharacterSeed + phase timer data.
    This is what the self-awareness endpoint returns — everything an agent
    (or operator) needs to understand identity health at a glance.
    """

    workspace_id: str = ""
    agent_id: str = ""
    seed_id: Optional[str] = None
    character_name: Optional[str] = None
    seed_motif_id: Optional[str] = None

    # Drift
    drift_score: float = 0.0
    drift_direction: str = "stable"
    distance_to_seed: float = 0.0

    # Seed basin geometry
    seed_basin_role: str = "plateau"
    seed_basin_phi: float = 0.0
    seed_basin_kappa: float = 0.0
    seed_basin_tension: float = 0.0

    # Memory tier counts
    core_count: int = 0
    relational_count: int = 0
    situational_count: int = 0

    # Phase timing
    phase_duration_steps: Optional[int] = None
    corridor_duration_steps: Optional[int] = None
    last_cycle_stage: Optional[str] = None
    last_identity_state: Optional[str] = None

    # SRG Crystal Attunement (if enabled)
    srg_enabled: bool = False
    srg_dominant_band: Optional[int] = None

    # Collective (populated after Phase B+)
    recent_collective_events: int = 0
    recent_compressions: int = 0

    updated_ts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CharacterSelfState":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


# ---------------------------------------------------------------------------
# MemoryGovernanceFlags — per-memory consent/sharing controls
# ---------------------------------------------------------------------------

@dataclass
class MemoryGovernanceFlags:
    """Control surface for selective sharing, decay, and consent.

    Stored in memory extra_payload["governance"]. Not all flags are wired
    in Phase A — the shape is defined here for forward compatibility.
    """

    protected: bool = False                    # immune to compression
    non_shareable: bool = False                # exclude from collective packets
    decay_accelerated: bool = False            # faster forgetting
    collective_export_blocked: bool = False     # don't emit to collective field
    collective_reingest_blocked: bool = False   # don't accept back from collective

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryGovernanceFlags":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)
