# torment_service/spirit_reflection.py
"""
Spirit Reflection — post-response write-back for TORMENT Phase 7.

After a response is generated, any spirit return hits that *actually
influenced* the response are recorded as derived reflection events.
This is NOT a copy of the original deep memory — it records the *event*
of return and its influence on the conversation.

Design constraints (non-negotiable):
  - Do NOT mutate original deep memories.
  - Do NOT automatically re-ingest every returned memory.
  - Do NOT duplicate raw summaries back into memory.
  - Do NOT let reflections become top-tier spirit-return sources.
  - Do NOT break current retrieval precedence.
  - Reflections are eligible_for_spirit_return = False.

Anti-echo protections:
  - Cooldown by source_eid + return_mode + interaction_type
  - Duplicate suppression within a cooldown window
  - Generation depth capped at 1 (reflections cannot spawn reflections)
  - Minimum influence threshold before storing

Four core functions:
  extract_spirit_return_candidates  — pull spirit-return hits from blocks
  score_spirit_return_influence     — conservative lexical/concept scoring
  build_spirit_reflection_event     — create the derived reflection record
  should_store_reflection           — anti-echo guard
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_INFLUENCE_THRESHOLD = 0.30   # minimum score to store a reflection
DEFAULT_COOLDOWN_STEPS = 50          # steps before same source can reflect again
MAX_GENERATION_DEPTH = 1             # reflections cannot spawn reflections
MAX_RESPONSE_EXCERPT_LEN = 200       # truncate response excerpt


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SpiritReflectionEvent:
    """A derived reflection artifact from a spirit return event.

    This records the *event of return*, not the original memory.
    """
    eid: int                              # new unique ID for this reflection
    source_eid: int                       # original deep memory EID that returned
    derived_from_spirit_return: bool       # always True
    generation_depth: int                  # always 1 (original → reflection)
    created_step: int                      # step when this reflection was created
    created_at: float                      # timestamp
    query_text: str                        # user query that triggered the return
    response_excerpt: str                  # compressed trace of influence
    return_mode: str                       # "resonance" | "surfacing" | "recollection"
    warmth_score: float                    # warmth at time of return
    symbol_interaction: str                # interaction type from the matrix
    spirit_return_flavor: str              # human-readable flavor
    influence_score: float                 # how much the return shaped the response
    influence_reason_tags: List[str]       # why we believe it influenced
    summary: str                           # one-line description of the event
    cooldown_key: str                      # dedup key: "source_eid:mode:interaction"
    eligible_for_spirit_return: bool       # always False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SpiritReflectionEvent":
        return cls(
            eid=int(d.get("eid", 0)),
            source_eid=int(d.get("source_eid", 0)),
            derived_from_spirit_return=bool(d.get("derived_from_spirit_return", True)),
            generation_depth=int(d.get("generation_depth", 1)),
            created_step=int(d.get("created_step", 0)),
            created_at=float(d.get("created_at", 0.0)),
            query_text=str(d.get("query_text", "")),
            response_excerpt=str(d.get("response_excerpt", "")),
            return_mode=str(d.get("return_mode", "recollection")),
            warmth_score=float(d.get("warmth_score", 0.0)),
            symbol_interaction=str(d.get("symbol_interaction", "")),
            spirit_return_flavor=str(d.get("spirit_return_flavor", "")),
            influence_score=float(d.get("influence_score", 0.0)),
            influence_reason_tags=list(d.get("influence_reason_tags", [])),
            summary=str(d.get("summary", "")),
            cooldown_key=str(d.get("cooldown_key", "")),
            eligible_for_spirit_return=False,  # always False, regardless of input
        )


# ---------------------------------------------------------------------------
# Stage 1 — Extract spirit return candidates from assembled context
# ---------------------------------------------------------------------------

def extract_spirit_return_candidates(
    blocks: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract spirit-return hits from assembled context blocks.

    Looks for hits with `from_spirit_return: True` in the block list.
    Returns a list of candidate dicts, each containing the spirit return
    metadata fields needed for influence scoring and reflection building.

    Already-reflected hits (generation_depth >= MAX_GENERATION_DEPTH) are
    excluded — reflections cannot spawn reflections.
    """
    candidates = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if not block.get("from_spirit_return"):
            continue
        # Skip anything that is itself a reflection (guard against future
        # scenarios where reflections accidentally enter the hit pipeline)
        if block.get("derived_from_spirit_return") and block.get("generation_depth", 0) >= MAX_GENERATION_DEPTH:
            continue
        candidates.append(block)
    return candidates


# ---------------------------------------------------------------------------
# Stage 2 — Influence scoring
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Simple whitespace + lowercase tokenizer for overlap scoring."""
    return re.findall(r"[a-z0-9]+", text.lower())


MIN_CANDIDATE_TOKENS_FOR_LEXICAL = 5  # below this, lexical overlap is unreliable


def _lexical_overlap(candidate_summary: str, response_text: str) -> float:
    """Jaccard-ish overlap between candidate summary and response.

    Returns a value in [0, 1]. Weighted toward candidate tokens appearing
    in the response (recall-oriented), since a long response will have
    many tokens not from the candidate.

    Ultra-short candidates (< 5 unique tokens) are heavily dampened because
    a single common word matching inflates recall to near 1.0, producing
    false positives.
    """
    c_tokens = set(_tokenize(candidate_summary))
    r_tokens = set(_tokenize(response_text))
    if not c_tokens:
        return 0.0
    overlap = c_tokens & r_tokens
    raw_recall = len(overlap) / len(c_tokens)

    # Dampen ultra-short candidates: scale down proportionally to how
    # far below the minimum they are.  At 1 token the dampener is 0.2,
    # at 4 tokens it's 0.8, at 5+ tokens it's 1.0 (no change).
    if len(c_tokens) < MIN_CANDIDATE_TOKENS_FOR_LEXICAL:
        dampener = len(c_tokens) / MIN_CANDIDATE_TOKENS_FOR_LEXICAL
        return raw_recall * dampener

    return raw_recall


def _concept_alignment(candidate: Dict[str, Any], response_text: str) -> float:
    """Simple concept alignment heuristic.

    Checks whether key spirit return concepts (symbol interaction flavor,
    return mode semantics) have traces in the response text.
    """
    score = 0.0
    checks = 0

    # Check if the spirit return flavor words appear in the response
    flavor = str(candidate.get("spirit_return_flavor", ""))
    if flavor:
        flavor_words = set(_tokenize(flavor))
        resp_words = set(_tokenize(response_text))
        if flavor_words and (flavor_words & resp_words):
            score += 0.5
        checks += 1

    # Check for mode-related language
    mode = candidate.get("spirit_return_mode", "")
    mode_signals = {
        "resonance": {"vivid", "familiar", "recognize", "deja", "echo", "resonance"},
        "surfacing": {"something", "wait", "notice", "surface", "emerging"},
        "recollection": {"remember", "recall", "before", "past", "earlier", "ago"},
    }
    signals = mode_signals.get(mode, set())
    if signals:
        resp_words = set(_tokenize(response_text))
        if signals & resp_words:
            score += 0.5
        checks += 1

    return (score / checks) if checks > 0 else 0.0


def score_spirit_return_influence(
    candidate: Dict[str, Any],
    response_text: str,
) -> Dict[str, Any]:
    """Score how much a spirit return candidate influenced the response.

    Returns:
        {
            "influence_score": float (0–1),
            "influence_reason_tags": list[str],
        }

    This is intentionally conservative — false negatives are better than
    false positives for the anti-echo design.
    """
    tags: List[str] = []
    scores: List[float] = []

    # Lexical overlap between candidate summary and response
    summary = str(candidate.get("summary", ""))
    lex = _lexical_overlap(summary, response_text)
    if lex > 0.15:
        tags.append("lexical_overlap")
    scores.append(lex)

    # Concept alignment
    concept = _concept_alignment(candidate, response_text)
    if concept > 0.2:
        tags.append("concept_alignment")
    scores.append(concept)

    # Warmth bonus: warmer memories are more likely to have influenced
    warmth = float(candidate.get("warmth_score", 0.0))
    warmth_factor = warmth * 0.2  # max 0.2 contribution
    if warmth >= 0.5:
        tags.append("high_warmth")
    scores.append(warmth_factor)

    # Resonance mode bonus: resonance returns are vivid and more
    # likely to shape responses
    mode = candidate.get("spirit_return_mode", "")
    if mode == "resonance":
        scores.append(0.15)
        tags.append("resonance_mode")
    else:
        scores.append(0.0)

    # Weighted average — lexical and concept are primary signals
    weights = [0.40, 0.30, 0.15, 0.15]
    influence = sum(s * w for s, w in zip(scores, weights))
    influence = min(1.0, max(0.0, influence))

    return {
        "influence_score": round(influence, 4),
        "influence_reason_tags": tags,
    }


# ---------------------------------------------------------------------------
# Stage 3 — Build the reflection event
# ---------------------------------------------------------------------------

def _make_cooldown_key(source_eid: int, return_mode: str, interaction: str) -> str:
    """Build a deduplication key for anti-echo cooldown."""
    return f"{source_eid}:{return_mode}:{interaction}"


def _make_reflection_eid(source_eid: int, created_step: int) -> int:
    """Generate a unique-ish EID for the reflection event.

    Uses a hash of source + step to avoid collisions while staying
    deterministic for testing.
    """
    raw = f"sr:{source_eid}:{created_step}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return int(digest, 16) % (2**31)  # keep within 32-bit signed range


def build_spirit_reflection_event(
    candidate: Dict[str, Any],
    response_text: str,
    current_step: int,
    query_text: str,
    influence_result: Optional[Dict[str, Any]] = None,
) -> SpiritReflectionEvent:
    """Create a derived reflection artifact from a spirit return candidate.

    This records the *event of return and its influence*, not the
    original memory content. The summary is a new sentence describing
    what happened, not a copy of the original summary.
    """
    source_eid = int(candidate.get("eid", 0))
    return_mode = str(candidate.get("spirit_return_mode", "recollection"))
    interaction = str(candidate.get("symbol_interaction", ""))
    flavor = str(candidate.get("spirit_return_flavor", ""))
    warmth = float(candidate.get("warmth_score", 0.0))

    if influence_result is None:
        influence_result = score_spirit_return_influence(candidate, response_text)

    influence_score = influence_result["influence_score"]
    influence_tags = influence_result["influence_reason_tags"]

    # Build a derived summary — NOT a copy of the original
    summary = (
        f"A prior deep memory (eid={source_eid}) resurfaced in {return_mode} mode "
        f"via {interaction} interaction and materially shaped the present reply."
    )

    # Truncate response excerpt
    excerpt = response_text[:MAX_RESPONSE_EXCERPT_LEN].strip()
    if len(response_text) > MAX_RESPONSE_EXCERPT_LEN:
        excerpt += "..."

    return SpiritReflectionEvent(
        eid=_make_reflection_eid(source_eid, current_step),
        source_eid=source_eid,
        derived_from_spirit_return=True,
        generation_depth=1,
        created_step=current_step,
        created_at=time.time(),
        query_text=query_text,
        response_excerpt=excerpt,
        return_mode=return_mode,
        warmth_score=warmth,
        symbol_interaction=interaction,
        spirit_return_flavor=flavor,
        influence_score=influence_score,
        influence_reason_tags=influence_tags,
        summary=summary,
        cooldown_key=_make_cooldown_key(source_eid, return_mode, interaction),
        eligible_for_spirit_return=False,
    )


# ---------------------------------------------------------------------------
# Stage 4 — Anti-echo guard
# ---------------------------------------------------------------------------

def should_store_reflection(
    event: SpiritReflectionEvent,
    recent_events: Sequence[SpiritReflectionEvent],
    *,
    influence_threshold: float = DEFAULT_INFLUENCE_THRESHOLD,
    cooldown_steps: int = DEFAULT_COOLDOWN_STEPS,
) -> Dict[str, Any]:
    """Determine whether a reflection event should be stored.

    Returns:
        {
            "store": bool,
            "reason": str,
        }

    Anti-echo rules (checked in order):
      1. Generation depth must be exactly 1.
      2. Influence score must meet threshold.
      3. Cooldown: same cooldown_key must not appear within cooldown_steps.
      4. Duplicate suppression: same source_eid + same step = duplicate.
    """
    # Rule 1: depth guard
    if event.generation_depth > MAX_GENERATION_DEPTH:
        return {"store": False, "reason": "generation_depth_exceeded"}

    # Rule 2: influence threshold
    if event.influence_score < influence_threshold:
        return {"store": False, "reason": "below_influence_threshold"}

    # Rule 3: cooldown by key
    for recent in recent_events:
        if recent.cooldown_key == event.cooldown_key:
            step_gap = event.created_step - recent.created_step
            if step_gap < cooldown_steps:
                return {
                    "store": False,
                    "reason": f"cooldown_active (gap={step_gap}, need={cooldown_steps})",
                }

    # Rule 4: duplicate suppression (same source + same step)
    for recent in recent_events:
        if recent.source_eid == event.source_eid and recent.created_step == event.created_step:
            return {"store": False, "reason": "duplicate_same_step"}

    return {"store": True, "reason": "passed_all_guards"}


# ---------------------------------------------------------------------------
# Storage — spirit_reflections.jsonl (separate from deep memory)
# ---------------------------------------------------------------------------

def _ensure_within_base(path: str, base_dir: str) -> Path:
    """Resolve *path* and verify it stays inside *base_dir*.

    Returns a resolved ``Path`` object that is safe to use for I/O.
    Raises ``ValueError`` on any escape attempt (traversal, symlink, etc.).
    """
    base = os.path.realpath(base_dir)
    resolved = os.path.realpath(str(path))
    if resolved != base and not resolved.startswith(base + os.sep):
        raise ValueError("Path escapes base directory")
    return Path(resolved)


def _safe_log_value(value: Any) -> str:
    """Neutralize newlines / carriage returns to prevent log injection."""
    return str(value).replace("\r", "\\r").replace("\n", "\\n")


class SpiritReflectionStore:
    """Persists spirit reflection events to a separate JSONL file.

    Storage is intentionally separate from deep_memory/ to preserve the
    clean separation between original compressed memories and derived
    reflection artifacts.

    Layout:
        data/agents/{agent_id}/spirit_reflections/
            reflections.jsonl   — append-only reflection log
    """

    def __init__(self, storage_path: Path, *, base_dir: str) -> None:
        self._dir = _ensure_within_base(str(storage_path), base_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = _ensure_within_base(
            str(self._dir / "reflections.jsonl"), base_dir,
        )
        self._cache: Optional[List[SpiritReflectionEvent]] = None

    def _ensure_loaded(self) -> None:
        if self._cache is not None:
            return
        self._cache = []
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            self._cache.append(SpiritReflectionEvent.from_dict(d))
                        except Exception:
                            continue
            except Exception as exc:
                logger.warning("spirit reflection store load failed: %s", exc)

    def store(self, event: SpiritReflectionEvent) -> bool:
        """Append a reflection event. Returns True on success."""
        self._ensure_loaded()
        assert self._cache is not None
        try:
            with open(self._file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
            self._cache.append(event)
            return True
        except Exception as exc:
            logger.warning("spirit reflection store write failed: %s", exc)
            return False

    def recent(self, n: int = 50) -> List[SpiritReflectionEvent]:
        """Return the N most recent reflection events."""
        self._ensure_loaded()
        assert self._cache is not None
        return list(self._cache[-n:])

    def all_events(self) -> List[SpiritReflectionEvent]:
        """Return all stored reflection events."""
        self._ensure_loaded()
        assert self._cache is not None
        return list(self._cache)

    def stats(self) -> Dict[str, Any]:
        """Return reflection store statistics."""
        self._ensure_loaded()
        assert self._cache is not None
        if not self._cache:
            return {
                "total_reflections": 0,
                "unique_sources": 0,
                "avg_influence": 0.0,
                "mode_counts": {},
            }
        sources = set(e.source_eid for e in self._cache)
        influences = [e.influence_score for e in self._cache]
        modes: Dict[str, int] = {}
        for e in self._cache:
            modes[e.return_mode] = modes.get(e.return_mode, 0) + 1
        return {
            "total_reflections": len(self._cache),
            "unique_sources": len(sources),
            "avg_influence": round(sum(influences) / len(influences), 4),
            "mode_counts": modes,
        }


# ---------------------------------------------------------------------------
# Convenience — full post-response reflection pass
# ---------------------------------------------------------------------------

def process_spirit_reflections(
    blocks: Sequence[Dict[str, Any]],
    response_text: str,
    query_text: str,
    current_step: int,
    store: SpiritReflectionStore,
    *,
    influence_threshold: float = DEFAULT_INFLUENCE_THRESHOLD,
    cooldown_steps: int = DEFAULT_COOLDOWN_STEPS,
) -> List[SpiritReflectionEvent]:
    """Run the full post-response reflection pipeline.

    1. Extract spirit return candidates from assembled blocks
    2. Score influence of each candidate against the response
    3. Build reflection events for candidates above threshold
    4. Guard against anti-echo violations
    5. Store surviving reflections

    Returns the list of reflections that were actually stored.
    """
    candidates = extract_spirit_return_candidates(blocks)
    if not candidates:
        return []

    recent = store.recent(n=100)
    stored: List[SpiritReflectionEvent] = []

    for candidate in candidates:
        # Score influence
        influence = score_spirit_return_influence(candidate, response_text)

        # Build the event (even if it might not pass the guard — we need
        # the full event to check cooldown keys)
        event = build_spirit_reflection_event(
            candidate, response_text, current_step, query_text,
            influence_result=influence,
        )

        # Anti-echo guard
        guard = should_store_reflection(
            event, recent + stored,
            influence_threshold=influence_threshold,
            cooldown_steps=cooldown_steps,
        )

        if guard["store"]:
            if store.store(event):
                stored.append(event)
                logger.debug(
                    "spirit reflection stored: source_eid=%d mode=%s influence=%.3f",
                    event.source_eid,
                    _safe_log_value(event.return_mode),
                    event.influence_score,
                )
        else:
            logger.debug(
                "spirit reflection rejected: source_eid=%s reason=%s",
                _safe_log_value(candidate.get("eid", "?")),
                _safe_log_value(guard["reason"]),
            )

    return stored
