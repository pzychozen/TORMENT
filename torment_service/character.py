"""
character.py — TORMENT living character identity layer

Philosophy:
    Characters are not scripts. A character is a gravitational basin in
    memory space. A minimal seed establishes initial conditions — who they
    are at the core. Then every interaction adds mass to the field. The
    coherence geometry provides drift protection for free: the deeper the
    seed basin, the harder it is for accumulated memories to push the
    character off-center.

    Three memory tiers arise naturally from half-life:
      - Core identity   (decade half-life, barely changes)
      - Relational       (monthly half-life, builds with specific users)
      - Situational      (weekly half-life, resets or fades)

    The seed is not a rulebook the model performs. It is the deepest
    attractor in the epistemic landscape. Everything else orbits.

Design:
    Seed + Memory + Drift.
    No new physics — we reuse motif gravity, coherence field basins,
    and half-life decay. The module adds:
      1. Seed planting (canon memories → deepest basin)
      2. Drift measurement (distance from seed centroid + field health)
      3. Gentle gravity correction (additive anchors, never rewrites)
      4. Tier-aware context assembly for model queries
"""
from __future__ import annotations

import json
import logging
import math
import os
import random
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .motifs import cosine
from .pathing import approved_subdir, stable_filename

log = logging.getLogger("torment.character")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_ts() -> int:
    return int(time.time())


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return int(default)


def _env_bool(key: str, default: bool = True) -> bool:
    v = str(os.environ.get(key, "1" if default else "0")).strip().lower()
    return v in ("1", "true", "yes", "on")


def _split_seed_text(seed_text: str, max_concepts: int = 5) -> List[str]:
    """Split seed text into 3-5 concept sentences for individual embedding.

    Keeps each concept self-contained so it produces a distinct embedding.
    """
    # Split on sentence boundaries
    raw = re.split(r'(?<=[.!?])\s+', seed_text.strip())
    # Filter empties and very short fragments
    sentences = [s.strip() for s in raw if len(s.strip()) > 10]
    if not sentences:
        # Fallback: treat the whole seed as one concept
        return [seed_text.strip()]
    # If we have more than max, merge shorter adjacent sentences
    if len(sentences) > max_concepts:
        merged = []
        buf = sentences[0]
        for s in sentences[1:]:
            if len(merged) < max_concepts - 1:
                if len(buf) < 80:
                    buf = buf + " " + s
                else:
                    merged.append(buf)
                    buf = s
            else:
                buf = buf + " " + s
        merged.append(buf)
        return merged[:max_concepts]
    return sentences[:max_concepts]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CharacterSeed:
    """Minimal character definition — the non-negotiables."""

    seed_id: str                    # e.g. "aria_v1"
    character_name: str             # e.g. "Aria"
    seed_text: str                  # 10-15 lines of natural language

    # Set after planting — the gravitational basin
    seed_motif_id: str = ""
    seed_eids: List[int] = field(default_factory=list)

    # Drift parameters
    drift_window_steps: int = 500
    drift_correction_threshold: float = 0.35
    drift_gravity_strength: float = 0.12

    # Tier half-lives (days)
    core_half_life: float = 3650.0       # ~10 years
    relational_half_life: float = 30.0
    situational_half_life: float = 7.0

    # Tier weights for context assembly
    core_weight: float = 0.50
    derived_weight: float = 0.42           # auto-emitted identity anchors (D3)
    relational_weight: float = 0.35
    situational_weight: float = 0.15

    # Metadata
    version: str = "1.0.0"
    created_ts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CharacterSeed":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


@dataclass
class CharacterState:
    """Runtime drift tracking — point-in-time snapshot."""

    workspace_id: str
    agent_id: str
    seed_id: str

    # Drift
    drift_score: float = 0.0            # -1.0 (far away) to +1.0 (converged)
    drift_direction: str = "stable"     # toward_seed | away_seed | stable
    distance_to_seed: float = 0.0       # raw cosine distance

    # Coherence field at seed basin
    seed_basin_phi: float = 0.0
    seed_basin_kappa: float = 0.0
    seed_basin_tension: float = 0.0
    seed_basin_role: str = "plateau"

    # Tier counts
    core_count: int = 0
    relational_count: int = 0
    situational_count: int = 0

    # History (recent entries only — capped at 50)
    drift_history: List[Tuple[int, float]] = field(default_factory=list)

    updated_ts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CharacterState":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        # drift_history comes back as list of lists from JSON
        dh = filtered.get("drift_history", [])
        filtered["drift_history"] = [(int(t), float(s)) for t, s in dh]
        return cls(**filtered)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

class CharacterStore:
    """Persists character seeds and runtime state as JSON."""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = os.path.realpath(data_dir)

    # -- Seed paths --

    def _seed_path(self, workspace_id: str, seed_id: str) -> str:
        # Defense-in-depth: validate components + contain beneath data_dir.
        seed_dir = approved_subdir(
            self.data_dir,
            "workspaces",
            workspace_id,
            "seeds",
            seed_id,
            mkdir=False,
        )
        p = stable_filename(seed_dir, "seed.json")
        base = os.path.realpath(self.data_dir)
        resolved = os.path.realpath(p)
        if resolved != base and not resolved.startswith(base + os.sep):
            raise ValueError(f"Character seed path escapes data directory: {resolved!r}")
        return resolved

    def load_seed(self, workspace_id: str, seed_id: str) -> Optional[CharacterSeed]:
        p = self._seed_path(workspace_id, seed_id)
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return CharacterSeed.from_dict(json.load(f))

    def save_seed(self, workspace_id: str, seed: CharacterSeed) -> None:
        p = self._seed_path(workspace_id, seed.seed_id)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(seed.to_dict(), f, indent=2, sort_keys=True)

    # -- State paths --

    def _state_path(self, workspace_id: str, agent_id: str) -> str:
        # Defense-in-depth: validate components + contain beneath data_dir.
        agent_dir = approved_subdir(
            self.data_dir,
            "workspaces",
            workspace_id,
            "agents",
            agent_id,
            mkdir=False,
        )
        p = stable_filename(agent_dir, "character_state.json")
        base = os.path.realpath(self.data_dir)
        resolved = os.path.realpath(p)
        if resolved != base and not resolved.startswith(base + os.sep):
            raise ValueError(f"Character state path escapes data directory: {resolved!r}")
        return resolved

    def load_state(self, workspace_id: str, agent_id: str) -> Optional[CharacterState]:
        p = self._state_path(workspace_id, agent_id)
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return CharacterState.from_dict(json.load(f))

    def save_state(self, workspace_id: str, state: CharacterState) -> None:
        p = self._state_path(workspace_id, state.agent_id)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        state.updated_ts = _now_ts()
        with open(p, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------

CORE_HALF_LIFE_MIN = 365.0      # anything with half_life >= 365 days is core
RELATIONAL_HALF_LIFE_MIN = 7.0  # 7-364 days is relational
                                 # < 7 days is situational


def classify_tier(half_life_days: float, *, mtype: str = "", canon: bool = False) -> str:
    """Classify a memory into its tier based on half-life.

    Auto-emitted identity anchors (mtype="identity_anchor", canon=False) are
    classified as "derived_identity" rather than "core_identity" so they do not
    compete at the same tier weight as seed canon memories.  See §2A anchor-
    hygiene ratification (D1).
    """
    if half_life_days >= CORE_HALF_LIFE_MIN:
        # Auto-emitted (non-canon) identity anchors get their own tier
        if mtype == "identity_anchor" and not canon:
            return "derived_identity"
        return "core_identity"
    elif half_life_days >= RELATIONAL_HALF_LIFE_MIN:
        return "relational"
    return "situational"


def tier_weight(tier: str, seed: CharacterSeed) -> float:
    """Return the context-assembly weight for a given tier."""
    return {
        "core_identity": seed.core_weight,
        "derived_identity": seed.derived_weight,
        "relational": seed.relational_weight,
        "situational": seed.situational_weight,
    }.get(tier, seed.situational_weight)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def plant_seed(
    *,
    graph,            # MemoryGraph (private graph for this agent)
    motif_registry,   # MotifRegistry for the agent's primary domain
    coherence_field,  # CoherenceField instance
    embedder,         # Embedder with .embed(text) -> np.ndarray
    seed: CharacterSeed,
    agent_id: str,
    step: int = 0,
) -> CharacterSeed:
    """Plant seed memories to establish the character's deepest basin.

    Idempotent: if seed.seed_motif_id already points to a populated motif,
    this is a no-op and returns the seed unchanged.

    Returns the seed with seed_motif_id and seed_eids populated.
    """
    # Idempotent check
    if seed.seed_motif_id and seed.seed_eids:
        existing = motif_registry.motifs.get(seed.seed_motif_id)
        if existing and len(existing.members) > 0:
            return seed

    # Split seed text into embeddable concepts
    concepts = _split_seed_text(seed.seed_text)

    # Embed and spawn each concept as a canon memory
    eids: List[int] = []
    embeddings: List[np.ndarray] = []

    for i, concept in enumerate(concepts):
        emb = embedder.embed(concept)
        embeddings.append(np.asarray(emb, dtype=np.float32).reshape(-1))

        eid = graph.spawn_memory(
            summary=concept,
            embedding=emb,
            mtype="seed_canon",
            strength=0.95,
            confidence=0.95,
            half_life_days=seed.core_half_life,
            canon=True,
            user_id=agent_id,
            step=step,
            extra_payload={
                "seed_id": seed.seed_id,
                "character_name": seed.character_name,
                "tier": "core_identity",
                "seed_concept_index": i,
            },
        )
        eids.append(int(eid))

    # Attach all seed memories to motifs — they should cluster together
    # into one motif (the seed basin) since they share thematic coherence
    motif_ids_seen = set()
    for i, (eid_val, emb) in enumerate(zip(eids, embeddings)):
        affected_ids, created_id = motif_registry.attach_or_create(
            embedding=emb,
            memory_eid=eid_val,
            agent_id=agent_id,
            summary=concepts[i],
            attach_threshold=0.50,  # lower threshold so seed concepts cluster together
        )
        motif_ids_seen.update(affected_ids)
        if created_id:
            motif_ids_seen.add(created_id)

    # The seed motif is whichever motif got the most seed members
    best_motif_id = ""
    best_count = 0
    for mid in motif_ids_seen:
        m = motif_registry.motifs.get(mid)
        if m:
            count = sum(1 for e in eids if e in m.members)
            if count > best_count:
                best_count = count
                best_motif_id = mid

    # Boost the seed motif's strength and stability to deepen the basin
    if best_motif_id:
        m = motif_registry.motifs.get(best_motif_id)
        if m:
            m.strength = min(1.0, max(m.strength, 0.85))
            m.stability_score = min(1.0, max(m.stability_score, 0.90))

    # Flush all seed memories to disk
    for eid_val in eids:
        graph.flush_node(eid_val)

    # Save motif state
    motif_registry.save()

    # Update seed with planted references
    seed.seed_motif_id = best_motif_id
    seed.seed_eids = eids
    if seed.created_ts == 0:
        seed.created_ts = _now_ts()

    return seed


def measure_drift(
    *,
    graph,            # MemoryGraph (private graph for this agent)
    motif_registry,   # MotifRegistry
    coherence_field,  # CoherenceField instance (optional — can be None)
    seed: CharacterSeed,
    agent_id: str,
    current_step: int,
    previous_state: Optional[CharacterState] = None,
) -> Dict[str, Any]:
    """Measure how far the character has drifted from the seed basin.

    Returns a drift report dict (also suitable for updating CharacterState).
    """
    window = seed.drift_window_steps

    # --- Collect recent non-seed memories ---
    recent_embs: List[Tuple[float, np.ndarray]] = []  # (weight, embedding)
    tier_counts = {"core_identity": 0, "derived_identity": 0, "relational": 0, "situational": 0}

    for eid, ent in graph.entities.items():
        payload = ent.payload or {}

        # Skip seed canon memories (don't measure seed against itself)
        if payload.get("mtype") == "seed_canon" or payload.get("type") == "seed_canon":
            continue

        # Only count this agent's memories
        if payload.get("user_id") != agent_id:
            continue

        # Tier classification — pass mtype/canon so derived anchors don't
        # inflate core_count (§2A anchor-hygiene amendment P7)
        half_life = float(payload.get("half_life", 30.0))
        _mtype = str(payload.get("mtype") or payload.get("type", ""))
        _canon = bool(payload.get("canon", False))
        tier = classify_tier(half_life, mtype=_mtype, canon=_canon)
        if tier in tier_counts:
            tier_counts[tier] += 1
        else:
            tier_counts[tier] = 1

        # Recency filter for drift measurement
        born = int(payload.get("born_step", 0) or 0)
        age = max(0, current_step - born)
        if age > window:
            continue

        # Load embedding
        emb = graph._emb_by_eid.get(int(eid))
        if emb is None:
            continue

        # Recency weight: exponential decay within window
        decay = math.exp(-age / max(1, window * 0.5))
        recent_embs.append((decay, np.asarray(emb, dtype=np.float32).reshape(-1)))

    # --- Compute weighted centroid of recent memories ---
    if not recent_embs:
        # No recent memories — drift is zero (nothing to drift toward)
        return {
            "drift_score": 0.0,
            "drift_direction": "stable",
            "distance_to_seed": 0.0,
            "seed_basin_phi": 0.0,
            "seed_basin_kappa": 0.0,
            "seed_basin_tension": 0.0,
            "seed_basin_role": "plateau",
            "core_count": tier_counts["core_identity"],
            "derived_count": tier_counts.get("derived_identity", 0),
            "relational_count": tier_counts["relational"],
            "situational_count": tier_counts["situational"],
            "total_recent": 0,
            "explanation": "No recent memories to measure drift against.",
        }

    total_weight = sum(w for w, _ in recent_embs)
    if total_weight < 1e-12:
        total_weight = 1.0
    avg_emb = sum(w * e for w, e in recent_embs) / total_weight

    # --- Distance from seed motif centroid ---
    seed_motif = motif_registry.motifs.get(seed.seed_motif_id)
    if seed_motif is None:
        # Seed motif was lost (merge/prune?) — use seed memory embeddings
        seed_embs = []
        for seid in seed.seed_eids:
            se = graph._emb_by_eid.get(seid)
            if se is not None:
                seed_embs.append(np.asarray(se, dtype=np.float32).reshape(-1))
        if seed_embs:
            seed_centroid = np.mean(seed_embs, axis=0)
        else:
            seed_centroid = avg_emb  # no seed data — can't measure
    else:
        seed_centroid = seed_motif.centroid_np()

    raw_sim = float(cosine(avg_emb, seed_centroid))
    distance = 1.0 - raw_sim  # 0.0 = same, 1.0 = orthogonal

    # --- Coherence field health at seed basin ---
    basin_phi = 0.0
    basin_kappa = 0.0
    basin_tension = 0.0
    basin_role = "plateau"

    if coherence_field is not None and seed.seed_motif_id:
        try:
            field_data = coherence_field.last_result or {}
            motif_fields = field_data.get("motifs", {})
            sf = motif_fields.get(seed.seed_motif_id, {})
            basin_phi = float(sf.get("phi", 0.0))
            basin_kappa = float(sf.get("kappa", 0.0))
            basin_tension = float(sf.get("tension", 0.0))
            basin_role = str(sf.get("role", "plateau"))
        except Exception as e:
            log.debug("Coherence field read skipped: %s", e)

    # --- Drift direction (compare to previous) ---
    direction = "stable"
    if previous_state is not None:
        prev_dist = previous_state.distance_to_seed
        delta = distance - prev_dist
        if delta > 0.03:
            direction = "away_seed"
        elif delta < -0.03:
            direction = "toward_seed"

    # --- Map to drift score ---
    # Positive = healthy (close to seed), negative = drifting away
    # Range approximately -1.0 to +1.0
    drift_score = float(1.0 - 2.0 * min(1.0, distance / 0.5))
    drift_score = max(-1.0, min(1.0, drift_score))

    # --- Explanation ---
    if drift_score > 0.3:
        explanation = f"Character is well-centered near seed basin (distance {distance:.3f})."
    elif drift_score > -0.1:
        explanation = f"Character is moderately centered (distance {distance:.3f}). Some drift from seed."
    elif drift_score > -0.35:
        explanation = f"Character is drifting from seed (distance {distance:.3f}). Monitor closely."
    else:
        explanation = f"Significant drift detected (distance {distance:.3f}). Gravity correction recommended."

    if basin_role == "basin":
        explanation += " Seed basin is stable."
    elif basin_role == "ridge":
        explanation += " Warning: seed position is on a ridge — structurally unstable."

    return {
        "drift_score": drift_score,
        "drift_direction": direction,
        "distance_to_seed": distance,
        "seed_basin_phi": basin_phi,
        "seed_basin_kappa": basin_kappa,
        "seed_basin_tension": basin_tension,
        "seed_basin_role": basin_role,
        "core_count": tier_counts["core_identity"],
        "derived_count": tier_counts.get("derived_identity", 0),
        "relational_count": tier_counts["relational"],
        "situational_count": tier_counts["situational"],
        "total_recent": len(recent_embs),
        "explanation": explanation,
    }


def gravity_correction(
    *,
    graph,            # MemoryGraph (private graph)
    motif_registry,   # MotifRegistry
    embedder,         # Embedder
    seed: CharacterSeed,
    agent_id: str,
    step: int,
    drift_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply gentle gravity correction by emitting a seed-reinforcing memory.

    This is purely additive — it never rewrites or deletes existing memories.
    The new anchor memory strengthens the seed basin, pulling future drift
    back toward center through the coherence field's natural mechanics.

    Only fires when drift exceeds threshold AND direction is "away_seed".
    """
    drift_score = float(drift_info.get("drift_score", 0.0))
    direction = str(drift_info.get("drift_direction", "stable"))

    # Gate: only correct when drifting away past threshold
    if drift_score > -seed.drift_correction_threshold:
        return {"correction_applied": False, "reason": "drift within tolerance"}
    if direction != "away_seed":
        return {"correction_applied": False, "reason": "not drifting away"}

    # Pick a random seed concept to reinforce
    concepts = _split_seed_text(seed.seed_text)
    concept = random.choice(concepts) if concepts else seed.seed_text

    correction_text = f"[identity reinforcement] {concept}"
    emb = embedder.embed(correction_text)

    # Spawn as a core-tier canon memory
    eid = graph.spawn_memory(
        summary=correction_text,
        embedding=emb,
        mtype="drift_correction",
        strength=seed.drift_gravity_strength,
        confidence=0.85,
        half_life_days=seed.core_half_life,
        canon=True,
        user_id=agent_id,
        step=step,
        extra_payload={
            "seed_id": seed.seed_id,
            "tier": "core_identity",
            "corrects_drift_score": drift_score,
            "corrects_at_step": step,
        },
    )

    # Attach to seed motif to deepen the basin
    if seed.seed_motif_id:
        try:
            motif_registry.attach_or_create(
                embedding=np.asarray(emb, dtype=np.float32).reshape(-1),
                memory_eid=int(eid),
                agent_id=agent_id,
                summary=correction_text,
                attach_threshold=0.50,
            )
        except Exception as e:
            log.debug("Motif attach skipped: %s", e)

    graph.flush_node(int(eid))

    return {
        "correction_applied": True,
        "correction_eid": int(eid),
        "correction_strength": seed.drift_gravity_strength,
        "drift_score_at_correction": drift_score,
        "concept_reinforced": concept,
    }


# ---------------------------------------------------------------------------
# Kernel modulation — unifies character seed with tri-octagon physics
# ---------------------------------------------------------------------------

# Keyword sets for emotional signal extraction (matches affect.py / roles.py style)
_WARMTH_WORDS = frozenset([
    "warm", "bond", "love", "companion", "care", "empathy", "playful",
    "affection", "gentle", "kind", "trust", "heart", "nurture", "friend",
    "connect", "compassion", "tender", "intimate", "devoted", "loyal",
    "enthusiasm", "mischievous", "spark", "joy", "delight",
])
_STRUCTURE_WORDS = frozenset([
    "analytical", "precise", "logical", "systematic", "careful", "methodical",
    "rigorous", "formal", "structured", "disciplined", "calculated", "exact",
    "rational", "strategic", "ordered", "measured", "deliberate", "focused",
    "meticulous", "objective", "detached", "stoic", "reserved",
])


def derive_kernel_modulation(
    seed: CharacterSeed,
    embedder,
    *,
    g_default: float = 0.2,
    theta_lock_default: float = 0.244,
) -> Dict[str, Any]:
    """Derive kernel parameter modulations from a character seed.

    Routes the character's natural-language identity description through
    the kernel's embedding → Omega pipeline so that the oscillator physics
    inherently reflects who the character is.

    Returns:
        dict with keys:
            omega_init   — np.ndarray (3 complex) for init_state()
            g_mod        — float, modulated coupling strength
            theta_lock_mod — float, modulated preferred Z angle
            warmth       — float 0-1, detected warmth score
            structure    — float 0-1, detected structure score
    """
    # --- Embed full seed text → Omega ---
    full_emb = embedder.embed(seed.seed_text)
    full_emb = np.asarray(full_emb, dtype=float).reshape(-1)

    # Build Omega exactly as _omega_from_embedding does
    e = full_emb
    if e.size < 6:
        e = np.pad(e, (0, 6 - e.size))
    w = np.abs(e[:3]) + 1e-6
    w = w / np.sum(w)
    phases = e[3:6] * np.pi
    omega_init = np.sqrt(w) * (np.cos(phases) + 1j * np.sin(phases))
    omega_init = omega_init.astype(np.complex128)

    # --- Extract emotional signals from seed text ---
    words = set(re.findall(r'[a-z]+', seed.seed_text.lower()))

    warmth_hits = len(words & _WARMTH_WORDS)
    structure_hits = len(words & _STRUCTURE_WORDS)

    # Normalize to 0-1 with soft saturation (tanh)
    warmth = float(np.tanh(warmth_hits / 3.0))       # 3 warmth words → ~0.76
    structure = float(np.tanh(structure_hits / 3.0))   # 3 structure words → ~0.76

    # --- Compute modulations ---
    # Coupling g: warm characters couple tighter (±15%)
    g_mod = g_default * (1.0 + 0.15 * (warmth - 0.5))

    # theta_lock: structured characters shift preferred Z angle (±0.1 rad)
    theta_lock_mod = theta_lock_default + 0.1 * (structure - 0.5)

    # Bounds safety
    g_mod = float(np.clip(g_mod, g_default * 0.85, g_default * 1.15))
    theta_lock_mod = float(np.clip(theta_lock_mod, 0.0, 0.5))

    return {
        "omega_init": omega_init,
        "g_mod": g_mod,
        "theta_lock_mod": theta_lock_mod,
        "warmth": warmth,
        "structure": structure,
    }


def derive_srg_character_bands(seed: CharacterSeed) -> Dict[str, Any]:
    """Map a character seed's identity modes to golden tower bands.

    This is a read-only helper — it doesn't modify the seed or any state.
    Returns a dict of detected modes and their band assignments, or an
    empty dict if SRG is not enabled.

    Integration point for fabric.py to pass SRG character mode into
    build_memory_srg() at ingest time.
    """
    try:
        from .srg_engine import (
            srg_enabled, detect_character_mode, assign_band,
            golden_tower_frequency, CHARACTER_MODE_KEYWORDS,
        )
    except ImportError:
        return {}

    if not srg_enabled():
        return {}

    text = str(getattr(seed, "seed_text", "") or "")
    if not text:
        return {}

    # Detect dominant mode from seed text
    words = set(re.findall(r"[a-z]+", text.lower()))
    mode_scores = {
        mode: len(words & kws) for mode, kws in CHARACTER_MODE_KEYWORDS.items()
    }

    # Build band map for all modes with hits
    band_map = {}
    for mode, score in mode_scores.items():
        if score >= 1:
            band = assign_band(character_mode=mode)
            band_map[mode] = {
                "band": band,
                "frequency": golden_tower_frequency(band),
                "keyword_hits": score,
            }

    dominant = max(mode_scores, key=mode_scores.get)
    dominant_score = mode_scores[dominant]

    return {
        "dominant_mode": dominant if dominant_score >= 2 else "",
        "band_map": band_map,
    }


def build_self_state(
    workspace_id: str,
    agent_id: str,
    character_store: "CharacterStore",
    *,
    seed_id: Optional[str] = None,
    phase_timers: Optional[Dict[str, Any]] = None,
    srg_enable: bool = False,
) -> Dict[str, Any]:
    """Assemble a CharacterSelfState dict from persisted data.

    The caller (app.py) is expected to extract seed_id from the agent's
    identity. If seed_id is None, returns minimal state.

    This is a read-only helper — no side effects on any store.
    """
    from .collective_models import CharacterSelfState

    if not seed_id:
        # No character seed — return minimal state
        return CharacterSelfState(
            workspace_id=workspace_id,
            agent_id=agent_id,
            updated_ts=_now_ts(),
        ).to_dict()

    seed = character_store.load_seed(workspace_id, seed_id)
    state = character_store.load_state(workspace_id, agent_id)

    ss = CharacterSelfState(
        workspace_id=workspace_id,
        agent_id=agent_id,
        seed_id=seed_id,
        character_name=seed.character_name if seed else None,
        seed_motif_id=seed.seed_motif_id if seed else None,
        updated_ts=_now_ts(),
    )

    # Drift + basin from CharacterState
    if state:
        ss.drift_score = state.drift_score
        ss.drift_direction = state.drift_direction
        ss.distance_to_seed = state.distance_to_seed
        ss.seed_basin_role = state.seed_basin_role
        ss.seed_basin_phi = state.seed_basin_phi
        ss.seed_basin_kappa = state.seed_basin_kappa
        ss.seed_basin_tension = state.seed_basin_tension
        ss.core_count = state.core_count
        ss.relational_count = state.relational_count
        ss.situational_count = state.situational_count

    # Phase timing from fabric's phase_timers
    if phase_timers:
        pt = phase_timers.get(agent_id)
        if pt:
            ss.phase_duration_steps = pt.get("phase_duration_steps")
            ss.corridor_duration_steps = pt.get("corridor_duration_steps")
            ss.last_cycle_stage = pt.get("cycle_stage") or pt.get("last_cycle_stage")
            ss.last_identity_state = pt.get("identity_state") or pt.get("last_identity_state")

    # SRG
    ss.srg_enabled = srg_enable

    return ss.to_dict()


def assemble_character_context(
    *,
    graph,            # MemoryGraph (private graph)
    seed: CharacterSeed,
    agent_id: str,
    hits: List[Dict[str, Any]],
    drift_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Enrich query hits with tier-aware weighting and seed context.

    Takes the already-retrieved hits from fabric.query() and:
      1. Classifies each hit into a tier
      2. Applies tier weight multipliers to final_score
      3. Returns seed context preamble + drift-aware recommendations

    Does NOT re-rank or remove hits — just adds tier metadata and
    a character_context block for the downstream consumer.
    """
    tier_hits: Dict[str, List[Dict[str, Any]]] = {
        "core_identity": [],
        "derived_identity": [],
        "relational": [],
        "situational": [],
    }

    for h in hits:
        half_life = float(h.get("half_life", 30.0))
        _payload = h.get("payload") or {}
        # Try payload if top-level half_life not available
        if _payload:
            half_life = float(_payload.get("half_life", half_life))
        # Extract mtype and canon for tier discrimination (§2A D1)
        _mtype = str(h.get("type") or h.get("mtype") or _payload.get("type", ""))
        _canon = bool(h.get("canon") or _payload.get("canon", False))
        tier = classify_tier(half_life, mtype=_mtype, canon=_canon)
        h["character_tier"] = tier

        # Apply tier weight as a multiplier on final_score
        tw = tier_weight(tier, seed)
        # Scale: core gets a 1.2x boost, relational 1.0x, situational 0.8x
        # (relative to a normalized base of relational = 1.0)
        tier_mult = tw / max(0.01, seed.relational_weight)
        h["character_tier_weight"] = float(tier_mult)
        h["character_weighted_score"] = float(h.get("final_score", 0.0)) * tier_mult

        tier_hits[tier].append(h)

    # Recommendations based on drift
    recommendations: List[str] = []
    if drift_info:
        ds = float(drift_info.get("drift_score", 0.0))
        if ds < -0.3:
            recommendations.append(
                "Character is drifting from seed identity. "
                "Reinforce core values and speech patterns."
            )
        if ds > 0.3:
            recommendations.append(
                "Character is well-centered. Safe to explore new directions."
            )
        if drift_info.get("seed_basin_role") == "ridge":
            recommendations.append(
                "Seed basin is structurally unstable — consider adding "
                "reinforcing interactions."
            )
        if (
            drift_info.get("relational_count", 0) == 0
            and not tier_hits["relational"]
        ):
            recommendations.append(
                "No relational memories yet. Character is running on "
                "seed identity alone — early interactions will shape personality."
            )

    # Spirit return voice guidance
    spirit_hits = [h for h in hits if h.get("from_spirit_return")]
    spirit_summary: Optional[Dict[str, Any]] = None
    if spirit_hits:
        by_mode: Dict[str, List[Dict[str, Any]]] = {
            "resonance": [], "surfacing": [], "recollection": [],
        }
        for sh in spirit_hits:
            m = str(sh.get("spirit_return_mode", "recollection"))
            by_mode.setdefault(m, []).append(sh)

        if by_mode["resonance"]:
            recommendations.append(
                f"Character has {len(by_mode['resonance'])} vivid returning "
                f"memories (resonance). Speak with déjà vu immediacy."
            )
        if by_mode["surfacing"]:
            recommendations.append(
                f"Character has {len(by_mode['surfacing'])} warm memories "
                f"surfacing. Acknowledge them gently."
            )
        if by_mode["recollection"]:
            recommendations.append(
                f"Character has {len(by_mode['recollection'])} distilled "
                f"recollections. Speak from distance."
            )

        warmth_vals = [float(sh.get("warmth_score", 0.2)) for sh in spirit_hits]
        spirit_summary = {
            "total": len(spirit_hits),
            "by_mode": {k: len(v) for k, v in by_mode.items()},
            "avg_warmth": sum(warmth_vals) / len(warmth_vals) if warmth_vals else 0.0,
        }

    result: Dict[str, Any] = {
        "seed_preamble": seed.seed_text,
        "seed_id": seed.seed_id,
        "character_name": seed.character_name,
        "tier_breakdown": {
            tier: len(hits_list)
            for tier, hits_list in tier_hits.items()
        },
        "drift_score": float(drift_info.get("drift_score", 0.0)) if drift_info else 0.0,
        "drift_summary": str(drift_info.get("explanation", "")) if drift_info else "",
        "recommendations": recommendations,
        # v0.2.2 Candidate A: pass-through additional drift_info fields so
        # /retrieve can surface them under the stable character_context
        # subset. These were previously consumed only by the recommendations
        # logic above; v0.2.2 makes them observable to callers without
        # changing prompt-text behavior. See
        # docs/MEMORY_TO_PROMPT_AUTOMATION_v0.2.md §7.5 (v0.2.x extensions).
        "drift_direction": str(drift_info.get("drift_direction", "stable")) if drift_info else "stable",
        "seed_basin_role": str(drift_info.get("seed_basin_role", "")) if drift_info else "",
        "relational_count": int(drift_info.get("relational_count", 0)) if drift_info else 0,
    }
    if spirit_summary is not None:
        result["spirit_return_summary"] = spirit_summary
    return result
