# torment_service/retrieval_assembler.py
"""
Retrieval Assembler — Phase 3 of the TORMENT v2.1 migration.

Unifies core memory retrieval and archive retrieval into a single
structured context object with explicit priority ordering.

=== HARD PRECEDENCE RULE ===
Archive blocks NEVER outrank identity blocks, even if archive
similarity is higher. The fill order is absolute:

  1. seed / core canon         — always included first
  2. drift / identity state    — always included
  3. relational continuity     — included before archive if any exists
  4. situational context       — recent conversation memories
  5. archive context           — fills remaining budget only

Archive is a library. Identity is the person. A library card does
not overwrite who you are.
=== END HARD PRECEDENCE RULE ===
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Token estimation (simple whitespace-based; matches chunking.py)
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 words per token for English."""
    words = len(text.split())
    return max(1, int(math.ceil(words / 0.75)))


# ---------------------------------------------------------------------------
# Block types
# ---------------------------------------------------------------------------

BLOCK_IDENTITY = "identity_context"
BLOCK_RELATIONAL = "relational_context"
BLOCK_SITUATIONAL = "situational_context"
BLOCK_ARCHIVE = "archive_context"

# Fill order — this is the hard precedence. Archive is always last.
FILL_ORDER = [
    BLOCK_IDENTITY,
    BLOCK_RELATIONAL,
    BLOCK_SITUATIONAL,
    BLOCK_ARCHIVE,
]


@dataclass
class ContextBlock:
    """One selected memory/chunk for inclusion in the assembled context."""
    block_type: str           # one of BLOCK_* constants
    eid: Optional[int] = None          # memory entity ID (core) or None (archive)
    chunk_id: Optional[str] = None     # archive chunk ID or None (core)
    text: str = ""
    token_count: int = 0
    score: float = 0.0
    reason: str = ""          # human-readable selection reason
    source: str = ""          # "core" or "archive"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssembledContext:
    """The structured output of the retrieval assembler."""
    profile: str
    token_budget: int
    tokens_used: int = 0
    blocks: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    assembled_text: str = ""
    block_token_counts: Dict[str, int] = field(default_factory=dict)
    selection_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

# Each profile defines SOFT budget percentages per block type.
# These are targets, not guarantees. The hard precedence rule means:
#   - Identity always gets its full allocation (up to what's available)
#   - Relational always fills before archive
#   - Archive only gets what's left after higher-priority blocks
#
# The percentages guide how MUCH each block can take, but never
# override the fill ORDER.

PROFILES: Dict[str, Dict[str, float]] = {
    "companion": {
        BLOCK_IDENTITY:    0.35,
        BLOCK_RELATIONAL:  0.30,
        BLOCK_SITUATIONAL: 0.20,
        BLOCK_ARCHIVE:     0.15,
    },
    "research": {
        BLOCK_IDENTITY:    0.15,
        BLOCK_RELATIONAL:  0.10,
        BLOCK_SITUATIONAL: 0.25,
        BLOCK_ARCHIVE:     0.50,
    },
    "narrator": {
        BLOCK_IDENTITY:    0.40,
        BLOCK_RELATIONAL:  0.25,
        BLOCK_SITUATIONAL: 0.25,
        BLOCK_ARCHIVE:     0.10,
    },
    "balanced": {
        BLOCK_IDENTITY:    0.25,
        BLOCK_RELATIONAL:  0.25,
        BLOCK_SITUATIONAL: 0.25,
        BLOCK_ARCHIVE:     0.25,
    },
}

# Minimum tokens guaranteed to identity, regardless of profile.
# Seed text + drift state should always fit.
IDENTITY_MIN_TOKENS = 200


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def _classify_core_hit(hit: Dict[str, Any]) -> str:
    """Classify a core memory hit into a block type.

    Uses memory type, tier, and half-life to determine which
    block a memory belongs to. Spirit return hits are classified
    by return mode + warmth instead of half-life.
    """
    mtype = str(hit.get("type") or hit.get("mtype") or "")
    tier = str(hit.get("character_tier") or "")
    half_life = float(hit.get("half_life", 30.0))
    canon = bool(hit.get("canon", False))

    # Seed canon and identity anchors are always identity
    if mtype in ("seed_canon", "drift_correction", "identity_anchor"):
        return BLOCK_IDENTITY
    if canon:
        return BLOCK_IDENTITY

    # Spirit return: classify by return mode + warmth
    if hit.get("from_spirit_return"):
        mode = str(hit.get("spirit_return_mode", "recollection"))
        warmth = float(hit.get("warmth_score", 0.2))
        if mode == "resonance" and warmth >= 0.5:
            return BLOCK_IDENTITY
        if mode == "surfacing" and warmth >= 0.3:
            return BLOCK_RELATIONAL
        return BLOCK_SITUATIONAL

    # Tier-based (from character.py classify_tier logic)
    if tier == "core_identity" or half_life >= 365.0:
        return BLOCK_IDENTITY
    if tier == "relational" or half_life >= 7.0:
        return BLOCK_RELATIONAL

    # Everything else is situational
    return BLOCK_SITUATIONAL


# ---------------------------------------------------------------------------
# Spirit return voice cues
# ---------------------------------------------------------------------------

_VOICE_CUES = {
    "resonance": "[Voice: present-tense, vivid, déjà vu — 'this feels familiar, like I already know this']",
    "surfacing": "[Voice: present-tense, gentle — 'there's something about that... it never really left']",
    "recollection": "[Voice: past-tense, distilled — 'I remember something from a while ago']",
}


def _get_voice_cue(mode: str) -> str:
    """Return the voice cue string for a spirit return mode."""
    return _VOICE_CUES.get(mode, _VOICE_CUES["recollection"])


def _hit_to_block(hit: Dict[str, Any], block_type: str) -> ContextBlock:
    """Convert a core memory hit dict to a ContextBlock.

    Spirit return hits get enriched with voice cues and flavor metadata.
    """
    text = str(hit.get("summary") or hit.get("text") or "")
    mtype = str(hit.get("type") or hit.get("mtype") or "memory")
    score = float(hit.get("final_score") or hit.get("score") or 0.0)

    # Build selection reason
    reasons = []
    if mtype == "seed_canon":
        reasons.append("seed canon memory")
    elif mtype == "drift_correction":
        reasons.append("drift correction anchor")
    elif mtype == "identity_anchor":
        reasons.append("identity anchor")
    elif bool(hit.get("canon", False)):
        reasons.append("canon memory")

    tier = str(hit.get("character_tier") or "")
    if tier:
        reasons.append(f"tier={tier}")

    if score > 0:
        reasons.append(f"score={score:.3f}")

    motifs = hit.get("motifs") or []
    if motifs:
        reasons.append(f"motif_aligned={','.join(str(m) for m in motifs[:2])}")

    # Base metadata
    meta: Dict[str, Any] = {
        "type": mtype,
        "half_life": float(hit.get("half_life", 0)),
        "strength": float(hit.get("strength", 0)),
        "confidence": float(hit.get("confidence", 0)),
    }

    # Spirit return enrichment
    is_spirit = bool(hit.get("from_spirit_return"))
    if is_spirit:
        mode = str(hit.get("spirit_return_mode", "recollection"))
        warmth = float(hit.get("warmth_score", 0.2))
        meta["from_spirit_return"] = True
        meta["spirit_return_mode"] = mode
        meta["spirit_return_flavor"] = str(hit.get("spirit_return_flavor", ""))
        meta["voice_cue"] = _get_voice_cue(mode)
        meta["warmth_score"] = warmth
        meta["symbol_interaction_type"] = str(hit.get("symbol_interaction", ""))
        reasons.append(f"spirit return ({mode}), warmth={warmth:.1f}")

        # Embed voice cue and flavor into the block text
        parts = [f"[Returning Memory]", meta["voice_cue"], text]
        flavor = meta["spirit_return_flavor"]
        if flavor:
            parts.append(f"[Flavor: {flavor}]")
        text = "\n".join(parts)

    return ContextBlock(
        block_type=block_type,
        eid=int(hit.get("eid", 0)) if hit.get("eid") is not None else None,
        chunk_id=None,
        text=text,
        token_count=_estimate_tokens(text),
        score=score,
        reason=" | ".join(reasons) if reasons else "core memory match",
        source="core",
        metadata=meta,
    )


def _archive_hit_to_block(hit: Dict[str, Any]) -> ContextBlock:
    """Convert an archive retrieval result to a ContextBlock."""
    text = str(hit.get("text") or "")
    score = float(hit.get("score", 0.0))

    reason_parts = [f"archive semantic match (score={score:.3f})"]
    doc_title = str(hit.get("doc_title") or "")
    if doc_title:
        reason_parts.append(f"doc={doc_title}")
    section = str(hit.get("section_title") or "")
    if section:
        reason_parts.append(f"section={section}")

    return ContextBlock(
        block_type=BLOCK_ARCHIVE,
        eid=None,
        chunk_id=str(hit.get("chunk_id") or ""),
        text=text,
        token_count=int(hit.get("token_count", 0)) or _estimate_tokens(text),
        score=score,
        reason=" | ".join(reason_parts),
        source="archive",
        metadata={
            "doc_id": str(hit.get("doc_id") or ""),
            "doc_title": doc_title,
            "section_path": hit.get("section_path", []),
            "memory_class": "archive",
        },
    )


# ---------------------------------------------------------------------------
# Seed / drift context builder
# ---------------------------------------------------------------------------

def _build_seed_block(
    seed_text: str,
    character_name: str,
    drift_info: Optional[Dict[str, Any]] = None,
) -> ContextBlock:
    """Build the always-included seed identity block."""
    parts = []
    if character_name:
        parts.append(f"[Character: {character_name}]")
    parts.append(seed_text.strip())

    if drift_info:
        ds = float(drift_info.get("drift_score", 0.0))
        direction = str(drift_info.get("drift_direction", "stable"))
        explanation = str(drift_info.get("explanation") or "")
        parts.append(f"[Drift: score={ds:.3f}, direction={direction}]")
        if explanation:
            parts.append(f"[{explanation}]")

    text = "\n".join(parts)
    return ContextBlock(
        block_type=BLOCK_IDENTITY,
        eid=None,
        chunk_id=None,
        text=text,
        token_count=_estimate_tokens(text),
        score=1.0,  # Always maximum priority
        reason="seed/core canon — always included first",
        source="core",
        metadata={"is_seed": True},
    )


# ---------------------------------------------------------------------------
# Main assembler
# ---------------------------------------------------------------------------

def assemble_context(
    *,
    core_hits: List[Dict[str, Any]],
    archive_hits: Optional[List[Dict[str, Any]]] = None,
    profile: str = "companion",
    token_budget: int = 4000,
    seed_text: str = "",
    character_name: str = "",
    drift_info: Optional[Dict[str, Any]] = None,
    custom_weights: Optional[Dict[str, float]] = None,
) -> AssembledContext:
    """Assemble a unified context from core + archive retrieval.

    This is the main entry point for Phase 3.

    Args:
        core_hits: Results from fabric.query() — already rescored.
        archive_hits: Results from ArchiveStore.retrieve() (optional).
        profile: Profile name ("companion", "research", "narrator", "balanced").
        token_budget: Total token budget for assembled context.
        seed_text: Character seed text (always included first).
        character_name: Character name for the preamble.
        drift_info: Current drift measurement (optional).
        custom_weights: Override profile weights with custom values.

    Returns:
        AssembledContext with structured blocks and assembled text.
    """
    archive_hits = archive_hits or []

    # Resolve profile weights
    weights = dict(PROFILES.get(profile, PROFILES["companion"]))
    if custom_weights:
        for k, v in custom_weights.items():
            if k in weights:
                weights[k] = float(v)
        # Normalize to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

    # Initialize block buckets
    block_candidates: Dict[str, List[ContextBlock]] = {
        BLOCK_IDENTITY: [],
        BLOCK_RELATIONAL: [],
        BLOCK_SITUATIONAL: [],
        BLOCK_ARCHIVE: [],
    }

    # --- Step 1: Always include seed/drift as the first identity block ---
    if seed_text:
        seed_block = _build_seed_block(seed_text, character_name, drift_info)
        block_candidates[BLOCK_IDENTITY].append(seed_block)

    # --- Step 2: Classify and bucket core hits ---
    for hit in core_hits:
        block_type = _classify_core_hit(hit)
        block = _hit_to_block(hit, block_type)
        block_candidates[block_type].append(block)

    # --- Step 3: Convert archive hits to archive blocks ---
    for ahit in archive_hits:
        block = _archive_hit_to_block(ahit)
        block_candidates[BLOCK_ARCHIVE].append(block)

    # --- Step 4: Sort each bucket by score (descending) ---
    # Identity: seed block always first (score=1.0), then by score.
    # Warmth acts as secondary sort key for spirit return memories.
    for bt in FILL_ORDER:
        block_candidates[bt].sort(
            key=lambda b: (b.score, b.metadata.get("warmth_score", 0.0)),
            reverse=True,
        )

    # --- Step 5: Fill in HARD PRECEDENCE ORDER ---
    # Budget allocation per block type (soft targets)
    budget_per_block: Dict[str, int] = {}
    for bt in FILL_ORDER:
        budget_per_block[bt] = max(1, int(token_budget * weights.get(bt, 0.0)))

    # Ensure identity gets at least IDENTITY_MIN_TOKENS
    budget_per_block[BLOCK_IDENTITY] = max(
        budget_per_block[BLOCK_IDENTITY],
        IDENTITY_MIN_TOKENS,
    )

    selected_blocks: Dict[str, List[ContextBlock]] = {
        bt: [] for bt in FILL_ORDER
    }
    tokens_used_per_block: Dict[str, int] = {bt: 0 for bt in FILL_ORDER}
    total_tokens_used = 0
    selection_log: List[Dict[str, Any]] = []

    for bt in FILL_ORDER:
        candidates = block_candidates[bt]
        block_budget = budget_per_block[bt]

        for candidate in candidates:
            # Global budget check
            if total_tokens_used + candidate.token_count > token_budget:
                # Can we fit a partial? No — we keep blocks whole.
                # But check if we can fit it anyway (small block)
                if candidate.token_count <= 50 and total_tokens_used + candidate.token_count <= token_budget + 50:
                    pass  # Allow small overflow for tiny blocks
                else:
                    selection_log.append({
                        "block_type": bt,
                        "eid": candidate.eid,
                        "chunk_id": candidate.chunk_id,
                        "action": "skipped_budget_exhausted",
                        "reason": f"would exceed total budget ({total_tokens_used}+{candidate.token_count} > {token_budget})",
                    })
                    continue

            # Per-block soft budget check (non-archive blocks can overflow into
            # unused space from later blocks; archive CANNOT overflow)
            if bt == BLOCK_ARCHIVE:
                # Archive: strict — only fills remaining budget
                remaining = token_budget - total_tokens_used
                if candidate.token_count > remaining:
                    selection_log.append({
                        "block_type": bt,
                        "eid": candidate.eid,
                        "chunk_id": candidate.chunk_id,
                        "action": "skipped_archive_budget",
                        "reason": f"archive cannot exceed remaining budget ({candidate.token_count} > {remaining})",
                    })
                    continue
            else:
                # Non-archive: soft budget — can overflow if higher priority
                if tokens_used_per_block[bt] + candidate.token_count > block_budget * 2:
                    # Even non-archive gets a 2x hard cap to prevent one block
                    # from eating everything
                    selection_log.append({
                        "block_type": bt,
                        "eid": candidate.eid,
                        "chunk_id": candidate.chunk_id,
                        "action": "skipped_block_cap",
                        "reason": f"block {bt} reached 2x soft cap",
                    })
                    continue

            # Accept this block
            selected_blocks[bt].append(candidate)
            tokens_used_per_block[bt] += candidate.token_count
            total_tokens_used += candidate.token_count

            selection_log.append({
                "block_type": bt,
                "eid": candidate.eid,
                "chunk_id": candidate.chunk_id,
                "score": candidate.score,
                "token_count": candidate.token_count,
                "action": "selected",
                "reason": candidate.reason,
            })

    # --- Step 6: Assemble text in precedence order ---
    text_parts: List[str] = []
    for bt in FILL_ORDER:
        blocks = selected_blocks[bt]
        if not blocks:
            continue
        # Section header
        header = {
            BLOCK_IDENTITY: "[Identity Context]",
            BLOCK_RELATIONAL: "[Relational Context]",
            BLOCK_SITUATIONAL: "[Situational Context]",
            BLOCK_ARCHIVE: "[Archive Context]",
        }.get(bt, f"[{bt}]")
        text_parts.append(header)
        for b in blocks:
            text_parts.append(b.text)
        text_parts.append("")  # blank line between sections

    assembled_text = "\n".join(text_parts).strip()

    # --- Step 7: Build result ---
    result = AssembledContext(
        profile=profile,
        token_budget=token_budget,
        tokens_used=total_tokens_used,
        blocks={
            bt: [asdict(b) for b in blocks]
            for bt, blocks in selected_blocks.items()
        },
        assembled_text=assembled_text,
        block_token_counts=dict(tokens_used_per_block),
        selection_log=selection_log,
    )

    return result
