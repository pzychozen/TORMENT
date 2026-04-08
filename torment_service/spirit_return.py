# torment_service/spirit_return.py
"""
Spirit Return with Symbolic Resonance — TORMENT Phase 7

When compressed memories return from the deep store, they carry their
birth symbol — the emotional watermark stamped at the moment of creation.
The interaction between that birth symbol and the kernel's current symbol
determines *how* the character experiences the returning memory.

Three return modes:
    surfacing   — short-path compressed, still in core. Present-tense.
                  "wait, there's something about that..."
    recollection — long-path from deep store. Past-tense, distilled.
                  "I remember something from a while ago..."
    resonance   — kernel symbol matches birth symbol closely. Déjà vu.
                  Rare. The memory feels vivid and immediate.

Warmup mechanic:
    Deep memories don't return at full strength. First appearance is a
    glimpse (warmth=0.2). Repeated retrieval within a step window
    increases warmth (+0.15 per appearance), capping at 1.0. Higher
    warmth → higher re-entry strength in the query hit.

Symbol interaction matrix:
    Birth symbol × current symbol → interaction type + flavor.
    ~20 key rules mapping emotional trajectories. Unmapped pairs
    default to "echo" (same symbol) or "contrast" (different).
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .symbols import SYMBOL_MEANINGS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SymbolInteractionRule:
    """A rule mapping birth_symbol × current_symbol → interaction."""
    birth_symbol: str           # or "*" for wildcard
    current_symbol: str         # or "*" for wildcard
    interaction_type: str       # "echo", "resolution", "integration", etc.
    flavor_template: str        # human-readable description
    confidence_boost: float     # bonus to resonance_confidence [0, 0.3]

    def matches(self, birth: str, current: str) -> bool:
        b_ok = self.birth_symbol == "*" or self.birth_symbol == birth
        c_ok = self.current_symbol == "*" or self.current_symbol == current
        return b_ok and c_ok


@dataclass
class WarmupState:
    """Tracks warmth accumulation for a single deep memory EID."""
    eid: int
    first_appearance_step: int
    appearance_count: int
    current_warmth: float       # 0.2 to 1.0
    max_warmth: float           # historical peak
    last_retrieved_step: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "WarmupState":
        return cls(
            eid=int(d.get("eid", 0)),
            first_appearance_step=int(d.get("first_appearance_step", 0) or 0),
            appearance_count=int(d.get("appearance_count", 0) or 0),
            current_warmth=float(d.get("current_warmth", 0.2) or 0.2),
            max_warmth=float(d.get("max_warmth", 0.2) or 0.2),
            last_retrieved_step=int(d.get("last_retrieved_step", 0) or 0),
        )


@dataclass
class SpiritReturnMemory:
    """A deep memory enriched with spirit return metadata."""
    deep_memory: Any            # DeepMemory instance
    birth_symbol: str
    current_kernel_symbol: str
    symbol_interaction: str     # interaction type name
    return_flavor: str          # human-readable description
    return_mode: str            # "surfacing" | "recollection" | "resonance"
    warmth_score: float
    resonance_confidence: float


# ---------------------------------------------------------------------------
# Symbol Interaction Matrix
# ---------------------------------------------------------------------------

_DEFAULT_RULES: Optional[List[SymbolInteractionRule]] = None


def build_symbol_interaction_matrix() -> List[SymbolInteractionRule]:
    """Build the extensible matrix of symbol pair rules.

    Exact matches tried first, then wildcard, then default echo/contrast.
    Rules are ordered by specificity — exact pairs before wildcards.
    """
    rules = [
        # --- Exact pair rules (birth → current) ---

        # Contradiction resolving into release
        SymbolInteractionRule("⊗", "⊘", "resolution",
            "a difficult memory dissolves into clarity", 0.25),

        # Contradiction finding rest
        SymbolInteractionRule("⊗", "◠", "integration",
            "old tension finds a place to rest", 0.20),

        # Comfort receding under pressure
        SymbolInteractionRule("◠", "⊗", "nostalgia_under_stress",
            "a warm memory returns but the present is harsh", 0.10),

        # Insight deepening insight
        SymbolInteractionRule("✧", "✧", "deepening",
            "an old insight deepens into something richer", 0.25),

        # Potential fulfilled
        SymbolInteractionRule("◯", "◈", "fulfilled",
            "something that was once only potential has crystallized", 0.20),

        # Released tension resurfaces
        SymbolInteractionRule("⊘", "⊗", "resurgence",
            "something released returns with new friction", 0.05),

        # Comfort outgrown
        SymbolInteractionRule("◠", "∿", "outgrown",
            "a place of comfort has become too small", 0.10),

        # Insight becomes structure
        SymbolInteractionRule("✧", "◈", "crystallized",
            "an old flash of understanding has become solid ground", 0.20),

        # Exploration finds home
        SymbolInteractionRule("∿", "◠", "found_home",
            "wandering led somewhere that feels like belonging", 0.20),

        # Familiar ground yields surprise
        SymbolInteractionRule("⋮", "✧", "breakthrough",
            "something familiar suddenly reveals a new angle", 0.20),

        # Stability shattered
        SymbolInteractionRule("◈", "⊗", "disrupted",
            "something once stable has been shaken", 0.05),

        # Release leads to warmth
        SymbolInteractionRule("⊘", "◠", "peace",
            "what was let go has become a source of quiet warmth", 0.20),

        # Potential exploring
        SymbolInteractionRule("◯", "∿", "unfolding",
            "something new has begun to spread out and wander", 0.15),

        # Continuity in contradiction — stuck
        SymbolInteractionRule("⋮", "⊗", "grinding",
            "familiar ground has turned rough", 0.05),

        # Exploration into insight
        SymbolInteractionRule("∿", "✧", "discovery",
            "wandering has led to a moment of clarity", 0.20),

        # Stabilization into release
        SymbolInteractionRule("◈", "⊘", "letting_go",
            "something once held together has been gently released", 0.15),

        # Contradiction into potential — reset after friction
        SymbolInteractionRule("⊗", "◯", "reset",
            "tension has broken and something new begins", 0.15),

        # Held into insight
        SymbolInteractionRule("◠", "✧", "illumination",
            "deep comfort gives rise to understanding", 0.20),

        # Continuity into stabilization — deepening roots
        SymbolInteractionRule("⋮", "◈", "rooted",
            "familiar ground settles into something more solid", 0.15),
    ]
    return rules


def _get_default_rules() -> List[SymbolInteractionRule]:
    global _DEFAULT_RULES
    if _DEFAULT_RULES is None:
        _DEFAULT_RULES = build_symbol_interaction_matrix()
    return _DEFAULT_RULES


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def compute_symbol_interaction(
    birth_symbol: str,
    current_symbol: str,
    rules: Optional[List[SymbolInteractionRule]] = None,
) -> Dict[str, Any]:
    """Match a birth×current symbol pair against the interaction matrix.

    Returns:
        {
            "interaction_type": str,
            "flavor": str,
            "confidence_boost": float,
            "is_resonance_candidate": bool,
        }
    """
    if rules is None:
        rules = _get_default_rules()

    birth = str(birth_symbol or "◯")
    current = str(current_symbol or "◯")

    # Try exact match rules first
    for rule in rules:
        if rule.matches(birth, current):
            is_resonance = rule.confidence_boost >= 0.20
            return {
                "interaction_type": rule.interaction_type,
                "flavor": rule.flavor_template,
                "confidence_boost": rule.confidence_boost,
                "is_resonance_candidate": is_resonance,
            }

    # Same symbol → echo
    if birth == current:
        meaning = SYMBOL_MEANINGS.get(birth, "unknown")
        return {
            "interaction_type": "echo",
            "flavor": f"a memory born in {meaning} returns to {meaning} — pattern recognition",
            "confidence_boost": 0.15,
            "is_resonance_candidate": True,
        }

    # Different symbol, no rule → contrast
    birth_meaning = SYMBOL_MEANINGS.get(birth, "unknown")
    current_meaning = SYMBOL_MEANINGS.get(current, "unknown")
    return {
        "interaction_type": "contrast",
        "flavor": f"a memory of {birth_meaning} meets a moment of {current_meaning}",
        "confidence_boost": 0.0,
        "is_resonance_candidate": False,
    }


def select_return_mode(
    deep_memory: Any,
    compressed_in_core: bool,
    symbol_interaction: Dict[str, Any],
    warmth: float,
) -> str:
    """Determine how the character experiences this returning memory.

    Returns:
        "resonance"   — high confidence + resonance candidate. Rare, vivid.
        "surfacing"   — compressed in core + warm enough. Present-tense.
        "recollection" — default. Past-tense, distilled.
    """
    # Resonance requires: resonance candidate + high warmth + confidence boost
    if (symbol_interaction.get("is_resonance_candidate", False)
            and warmth >= 0.5
            and symbol_interaction.get("confidence_boost", 0) >= 0.20):
        return "resonance"

    # Surfacing: still exists in core (short-path compressed) and warm
    if compressed_in_core and warmth >= 0.3:
        return "surfacing"

    return "recollection"


# ---------------------------------------------------------------------------
# Warmth
# ---------------------------------------------------------------------------

# Warmth increases within this many steps of the first appearance
WARMTH_WINDOW_STEPS = 400
WARMTH_FLOOR = 0.2
WARMTH_INCREMENT = 0.15
WARMTH_CAP = 1.0


def compute_warmth(appearance_count: int, steps_since_first: int) -> float:
    """Compute current warmth based on retrieval history.

    Floor of 0.2 on first appearance. +0.15 per subsequent appearance
    within the warmth window. Caps at 1.0. No increase if too many
    steps have passed since first appearance.
    """
    if appearance_count <= 0:
        return WARMTH_FLOOR

    if appearance_count == 1:
        return WARMTH_FLOOR

    # Only accumulate warmth if appearances are within the window
    if steps_since_first > WARMTH_WINDOW_STEPS:
        # Reset — too far apart, warmth doesn't build
        return WARMTH_FLOOR

    additional = WARMTH_INCREMENT * (appearance_count - 1)
    return min(WARMTH_CAP, WARMTH_FLOOR + additional)


# ---------------------------------------------------------------------------
# Enrichment Pipeline
# ---------------------------------------------------------------------------

def enrich_deep_memory_hit(
    deep_memory: Any,
    current_kernel_symbol: str,
    warmup_state: "WarmupState",
    compressed_in_core: bool,
) -> SpiritReturnMemory:
    """Main enrichment entry point.

    Takes a DeepMemory, the current kernel symbol, warmup state, and
    whether the memory still exists in core. Returns a fully enriched
    SpiritReturnMemory with all spirit return fields.
    """
    # Extract birth symbol from deep memory metadata
    metadata = getattr(deep_memory, "metadata", {}) or {}
    birth_symbol = str(metadata.get("state_symbol", "◯") or "◯")

    # Default empty kernel symbol to ◯
    current_kernel_symbol = str(current_kernel_symbol or "◯") or "◯"

    # Compute symbol interaction
    interaction = compute_symbol_interaction(birth_symbol, current_kernel_symbol)

    # Compute warmth from warmup state
    # Phase-cycle duration boost: sustained memories return warmer
    warmth = warmup_state.current_warmth
    _phase_dur = int(metadata.get("phase_duration_steps", 0) or 0)
    _corridor_dur = int(metadata.get("corridor_duration_steps", 0) or 0)
    _sustained = max(_phase_dur, _corridor_dur)
    SUSTAINED_CORRIDOR_THRESHOLD = 10
    SUSTAINED_WARMTH_FLOOR = 0.3
    if _sustained >= SUSTAINED_CORRIDOR_THRESHOLD and warmth < SUSTAINED_WARMTH_FLOOR:
        warmth = SUSTAINED_WARMTH_FLOOR

    # SRG spirit return enrichment (reads metadata only, no import when absent)
    _srg_meta = metadata.get("srg")
    _srg_force_resonance = False
    if _srg_meta and isinstance(_srg_meta, dict):
        # Crystal memories always return in resonance mode (vivid)
        if _srg_meta.get("is_crystal", False):
            _srg_force_resonance = True
        # Class A heartbeat: +0.15 warmth floor (deep/slow memories return warmer)
        if _srg_meta.get("heartbeat_class") == "A":
            _srg_warmth_floor = warmth + 0.15
            if warmth < _srg_warmth_floor:
                warmth = min(1.0, _srg_warmth_floor)

    # Select return mode
    if _srg_force_resonance:
        mode = "resonance"
    else:
        mode = select_return_mode(deep_memory, compressed_in_core, interaction, warmth)

    # Compute resonance confidence
    # Base confidence from deep memory, boosted by symbol interaction
    base_conf = float(metadata.get("symbol_confidence", 0.5) or 0.5)
    boost = interaction.get("confidence_boost", 0.0)
    resonance_conf = min(1.0, base_conf + boost)

    return SpiritReturnMemory(
        deep_memory=deep_memory,
        birth_symbol=birth_symbol,
        current_kernel_symbol=current_kernel_symbol,
        symbol_interaction=interaction["interaction_type"],
        return_flavor=interaction["flavor"],
        return_mode=mode,
        warmth_score=warmth,
        resonance_confidence=resonance_conf,
    )


def inject_spirit_return_into_hit(spirit_mem: SpiritReturnMemory) -> Dict[str, Any]:
    """Convert a SpiritReturnMemory into a query hit dict.

    The output is compatible with the existing hit merge pipeline in
    fabric.py query(). All spirit return fields are added alongside
    the standard hit fields.
    """
    dm = spirit_mem.deep_memory
    metadata = getattr(dm, "metadata", {}) or {}

    # Strength varies by return mode
    warmth = spirit_mem.warmth_score
    mode = spirit_mem.return_mode
    if mode == "resonance":
        strength = 0.6 * warmth
    elif mode == "surfacing":
        strength = 0.4 * warmth
    else:  # recollection
        strength = 0.1 * warmth

    return {
        "eid": dm.eid,
        "score": dm.compression_score,
        "summary": dm.summary,
        "type": metadata.get("type", "memory"),
        "strength": strength,
        "confidence": spirit_mem.resonance_confidence,
        "step": dm.born_step,
        "memory_class": dm.memory_class,
        # Deep memory markers
        "from_deep_memory": True,
        # Spirit return markers
        "from_spirit_return": True,
        "spirit_return_mode": mode,
        "spirit_return_flavor": spirit_mem.return_flavor,
        "birth_symbol": spirit_mem.birth_symbol,
        "current_kernel_symbol": spirit_mem.current_kernel_symbol,
        "symbol_interaction": spirit_mem.symbol_interaction,
        "warmth_score": spirit_mem.warmth_score,
        "resonance_confidence": spirit_mem.resonance_confidence,
    }


# ---------------------------------------------------------------------------
# WarmupTracker
# ---------------------------------------------------------------------------

class WarmupTracker:
    """Persists warmup state per deep memory EID.

    Storage: warmup_state.jsonl (append-only, with periodic compaction).
    In-memory dict keyed by EID for fast lookup.

    *base_dir* is the trusted root directory.  The resolved storage path
    is verified to stay inside it before any file access.
    """

    def __init__(self, storage_path: Path, *, base_dir: str) -> None:
        base = os.path.realpath(base_dir)
        resolved = os.path.realpath(str(storage_path))
        if resolved != base and not resolved.startswith(base + os.sep):
            raise ValueError("WarmupTracker storage_path escapes base directory")
        self.storage_path = Path(resolved)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._file = self.storage_path / "warmup_state.jsonl"
        self._states: Optional[Dict[int, WarmupState]] = None

    def _ensure_loaded(self) -> None:
        if self._states is not None:
            return
        self._states = {}
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            ws = WarmupState.from_dict(d)
                            self._states[ws.eid] = ws
                        except Exception:
                            continue
            except Exception as exc:
                logger.warning("warmup state load failed: %s", exc)

        # Auto-compact on first load if the file has grown significantly
        try:
            self.compact()
        except Exception:
            pass  # compaction is never critical

    def _persist(self, ws: WarmupState) -> None:
        """Append a warmup state update to disk."""
        try:
            with open(self._file, "a", encoding="utf-8") as f:
                f.write(json.dumps(ws.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning("warmup state persist failed: %s", exc)

    def get_or_create(self, eid: int, current_step: int) -> WarmupState:
        """Get warmup state for an EID, creating if needed.

        Each call increments the appearance count and recomputes warmth.
        """
        self._ensure_loaded()
        assert self._states is not None

        eid = int(eid)
        existing = self._states.get(eid)

        if existing is None:
            # First appearance
            ws = WarmupState(
                eid=eid,
                first_appearance_step=current_step,
                appearance_count=1,
                current_warmth=WARMTH_FLOOR,
                max_warmth=WARMTH_FLOOR,
                last_retrieved_step=current_step,
            )
        else:
            # Subsequent appearance
            steps_since = max(0, current_step - existing.first_appearance_step)
            new_count = existing.appearance_count + 1
            new_warmth = compute_warmth(new_count, steps_since)
            ws = WarmupState(
                eid=eid,
                first_appearance_step=existing.first_appearance_step,
                appearance_count=new_count,
                current_warmth=new_warmth,
                max_warmth=max(existing.max_warmth, new_warmth),
                last_retrieved_step=current_step,
            )

        self._states[eid] = ws
        self._persist(ws)
        return ws

    def compact(self) -> Dict[str, Any]:
        """Compact the append-only JSONL file.

        Reads all entries, keeps only the latest state per EID (which
        _ensure_loaded already deduplicates into self._states), then
        rewrites the file atomically. Safe to call at any time.

        Returns a summary of what was compacted.
        """
        self._ensure_loaded()
        assert self._states is not None

        if not self._file.exists():
            return {"compacted": False, "reason": "no_file", "entries_before": 0, "entries_after": 0}

        # Count lines before compaction
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                lines_before = sum(1 for line in f if line.strip())
        except Exception:
            lines_before = 0

        entries_after = len(self._states)

        # Skip if compaction would save less than 20% or fewer than 10 lines
        if lines_before - entries_after < max(10, int(lines_before * 0.2)):
            return {
                "compacted": False,
                "reason": "not_needed",
                "entries_before": lines_before,
                "entries_after": entries_after,
            }

        # Write compacted file atomically: write to temp, then rename
        tmp_file = self._file.with_suffix(".jsonl.tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                for ws in self._states.values():
                    f.write(json.dumps(ws.to_dict(), ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace (on POSIX; on Windows this is close enough)
            tmp_file.replace(self._file)

            logger.info(
                "Warmup state compacted: %d → %d entries",
                lines_before, entries_after,
            )
            return {
                "compacted": True,
                "entries_before": lines_before,
                "entries_after": entries_after,
                "saved_entries": lines_before - entries_after,
            }
        except Exception as exc:
            logger.warning("Warmup compaction failed (file unchanged): %s", exc)
            # Clean up temp file if it exists
            try:
                tmp_file.unlink(missing_ok=True)
            except Exception as cleanup_exc:
                logger.debug("temp file cleanup failed during compaction rollback: %s", cleanup_exc)
            return {
                "compacted": False,
                "reason": str(exc),
                "entries_before": lines_before,
                "entries_after": entries_after,
            }

    def stats(self) -> Dict[str, Any]:
        """Return warmup tracker statistics."""
        self._ensure_loaded()
        assert self._states is not None

        if not self._states:
            return {
                "tracked_eids": 0,
                "total_appearances": 0,
                "avg_warmth": 0.0,
                "max_warmth": 0.0,
                "resonance_ready": 0,
            }

        total_app = sum(ws.appearance_count for ws in self._states.values())
        warmths = [ws.current_warmth for ws in self._states.values()]
        resonance_ready = sum(1 for ws in self._states.values() if ws.current_warmth >= 0.5)

        return {
            "tracked_eids": len(self._states),
            "total_appearances": total_app,
            "avg_warmth": float(sum(warmths) / len(warmths)) if warmths else 0.0,
            "max_warmth": float(max(warmths)) if warmths else 0.0,
            "resonance_ready": resonance_ready,
        }
