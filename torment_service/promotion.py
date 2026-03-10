"""
promotion.py — Archive → Core promotion bridge (Phase 5)

This module governs the selective promotion of archive chunks into core
memory.  Most archive content stays in the archive lane — only passages
that prove identity-defining get promoted.

=== PROMOTION RULES ===
Promote archive chunks into core ONLY when at least one is true:
  1. Explicitly marked canon
  2. Retrieved repeatedly over time (retrieval_count > threshold)
  3. Strongly motif-aligned with seed identity
  4. High emotional / relational salience
  5. Explicitly approved by user/developer

Promotion creates a DISTILLED core node — NOT a raw chunk copy.
Source reference is preserved: {doc_id, chunk_id}.
=== END RULES ===

Design:
  - evaluate_promotion() scores a chunk against criteria → promote yes/no + reason
  - promote_chunk() creates a distilled core node from a qualifying chunk
  - suggest_promotions() scans archive for top candidates
  - Retrieval counting is tracked via a lightweight JSON counter file
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .affect import classify_affect

log = logging.getLogger("torment.promotion")


# ---------------------------------------------------------------------------
# Promotion config (tunable)
# ---------------------------------------------------------------------------
RETRIEVAL_COUNT_THRESHOLD = 5       # chunk must be retrieved N+ times
MOTIF_ALIGNMENT_THRESHOLD = 0.55    # cosine similarity to seed embedding
EMOTIONAL_SALIENCE_TAGS = frozenset({
    "joy", "love", "grief", "anger", "fear", "trust",
    "pride", "devotion", "bond", "protective",
})
PROMOTION_SCORE_THRESHOLD = 0.60    # weighted sum cutoff for auto-suggest


# ---------------------------------------------------------------------------
# Scoring weights (sum to 1.0)
# ---------------------------------------------------------------------------
W_CANON = 0.30          # explicit canon marking
W_RETRIEVAL = 0.25      # retrieval frequency
W_MOTIF_ALIGN = 0.25    # alignment with seed motif centroid
W_EMOTIONAL = 0.10      # emotional salience
W_USER_APPROVED = 0.10  # explicit user/dev approval


# ---------------------------------------------------------------------------
# Retrieval counter — lightweight persistence
# ---------------------------------------------------------------------------

def _retrieval_counts_path(archive_dir: str) -> str:
    return os.path.join(archive_dir, "retrieval_counts.json")


def load_retrieval_counts(archive_dir: str) -> Dict[str, int]:
    """Load chunk_id → retrieval_count map."""
    path = _retrieval_counts_path(archive_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_retrieval_counts(archive_dir: str, counts: Dict[str, int]) -> None:
    """Persist retrieval counts."""
    path = _retrieval_counts_path(archive_dir)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(counts, f)
        os.replace(tmp, path)
    except Exception as exc:
        log.warning("Failed to save retrieval counts: %s", exc)


def increment_retrieval_counts(archive_dir: str, chunk_ids: List[str]) -> None:
    """Bump retrieval counts for a batch of chunks (called after each retrieval)."""
    if not chunk_ids:
        return
    counts = load_retrieval_counts(archive_dir)
    for cid in chunk_ids:
        counts[cid] = counts.get(cid, 0) + 1
    save_retrieval_counts(archive_dir, counts)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

@dataclass
class PromotionResult:
    """Outcome of evaluating a chunk for promotion."""
    promote: bool
    score: float
    reason: str
    criteria: Dict[str, float]   # per-criterion score

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float).reshape(-1)
    b = np.asarray(b, dtype=float).reshape(-1)
    na = float(np.linalg.norm(a) + 1e-12)
    nb = float(np.linalg.norm(b) + 1e-12)
    return float(np.dot(a, b) / (na * nb))


def evaluate_promotion(
    chunk_text: str,
    chunk_id: str,
    *,
    is_canon: bool = False,
    retrieval_count: int = 0,
    chunk_embedding: Optional[np.ndarray] = None,
    seed_embedding: Optional[np.ndarray] = None,
    user_approved: bool = False,
) -> PromotionResult:
    """Score a chunk against promotion criteria.

    Returns a PromotionResult with a boolean decision, aggregate score,
    human-readable reason, and per-criterion breakdown.
    """
    criteria: Dict[str, float] = {}

    # 1. Canon flag
    criteria["canon"] = 1.0 if is_canon else 0.0

    # 2. Retrieval frequency (sigmoid-like ramp)
    if retrieval_count >= RETRIEVAL_COUNT_THRESHOLD:
        # Saturates at ~1.0 around 2× threshold
        criteria["retrieval"] = min(1.0, retrieval_count / (2.0 * RETRIEVAL_COUNT_THRESHOLD))
    else:
        criteria["retrieval"] = retrieval_count / (RETRIEVAL_COUNT_THRESHOLD + 1.0)

    # 3. Motif alignment with seed
    if chunk_embedding is not None and seed_embedding is not None:
        sim = _cosine(chunk_embedding, seed_embedding)
        criteria["motif_alignment"] = max(0.0, (sim - 0.3) / 0.7)  # remap [0.3, 1.0] → [0, 1]
    else:
        criteria["motif_alignment"] = 0.0

    # 4. Emotional salience
    try:
        affect = classify_affect(chunk_text)
        tag = str(affect.tag).lower() if affect.tag else ""
        conf = float(affect.conf) if affect.conf else 0.0
        if tag in EMOTIONAL_SALIENCE_TAGS and conf > 0.3:
            criteria["emotional"] = min(1.0, conf * 1.5)
        else:
            criteria["emotional"] = 0.0
    except Exception:
        criteria["emotional"] = 0.0

    # 5. User approval
    criteria["user_approved"] = 1.0 if user_approved else 0.0

    # Weighted aggregate
    score = (
        W_CANON * criteria["canon"]
        + W_RETRIEVAL * criteria["retrieval"]
        + W_MOTIF_ALIGN * criteria["motif_alignment"]
        + W_EMOTIONAL * criteria["emotional"]
        + W_USER_APPROVED * criteria["user_approved"]
    )

    # Build reason
    reasons: List[str] = []
    if criteria["canon"] > 0:
        reasons.append("canon-marked")
    if criteria["retrieval"] >= 0.5:
        reasons.append(f"retrieved {retrieval_count}x")
    if criteria["motif_alignment"] >= 0.5:
        reasons.append("seed-aligned")
    if criteria["emotional"] >= 0.5:
        reasons.append("emotionally salient")
    if criteria["user_approved"] > 0:
        reasons.append("user-approved")

    # Decision: promote if canon, user-approved, or score exceeds threshold
    promote = False
    if is_canon:
        promote = True
        reason = "Canon-marked: auto-promote"
    elif user_approved:
        promote = True
        reason = "User-approved: force promote"
    elif score >= PROMOTION_SCORE_THRESHOLD:
        promote = True
        reason = "Score {:.2f} >= {:.2f}: {}".format(
            score, PROMOTION_SCORE_THRESHOLD, " + ".join(reasons) or "combined criteria",
        )
    else:
        reason = "Score {:.2f} < {:.2f}: {}".format(
            score, PROMOTION_SCORE_THRESHOLD, ", ".join(reasons) if reasons else "no strong signals",
        )

    return PromotionResult(
        promote=promote,
        score=round(score, 4),
        reason=reason,
        criteria={k: round(v, 4) for k, v in criteria.items()},
    )


# ---------------------------------------------------------------------------
# Promotion execution
# ---------------------------------------------------------------------------

def promote_chunk(
    chunk_id: str,
    chunk_text: str,
    doc_id: str,
    memory_graph,
    embedder,
    *,
    step: int = 0,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """Create a distilled core node from an archive chunk.

    The promoted node:
      - kind = "canon_promotion"
      - tier = "core_identity"
      - memory_class = "core"
      - Very long half_life (3650 days)
      - Preserves source_ref to original doc/chunk

    Returns the new eid, or None on failure.
    """
    try:
        # Distill: use the chunk text as-is for now (future: LLM summarization)
        # The text should already be reasonably concise from chunking.
        distilled = chunk_text.strip()
        if len(distilled) > 500:
            # Truncate with ellipsis if too long for a core identity node
            distilled = distilled[:497] + "..."

        emb = embedder.embed(distilled)

        payload = {
            "memory_class": "core",
            "kind": "canon_promotion",
            "tier": "core_identity",
            "source_ref": {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
            },
            "promoted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "canon": True,
        }
        if extra_payload:
            payload.update(extra_payload)

        eid = memory_graph.spawn_memory(
            summary=distilled,
            embedding=emb,
            mtype="identity",
            strength=0.90,
            confidence=0.85,
            half_life_days=3650.0,   # decade half-life
            links=[],
            canon=True,
            user_id="promotion_system",
            step=step,
            extra_payload=payload,
        )

        # Flush the node to JSONL
        memory_graph.flush_node(int(eid))

        log.info("Promoted chunk %s → core eid=%d", chunk_id, eid)
        return int(eid)

    except Exception as exc:
        log.warning("Promotion failed for chunk %s: %s", chunk_id, exc)
        return None


# ---------------------------------------------------------------------------
# Suggestions
# ---------------------------------------------------------------------------

def suggest_promotions(
    archive_store,
    *,
    seed_embedding: Optional[np.ndarray] = None,
    retrieval_counts: Optional[Dict[str, int]] = None,
    max_suggestions: int = 10,
) -> List[Dict[str, Any]]:
    """Scan archive chunks and return top promotion candidates.

    Returns a list of dicts with chunk_id, text, score, reason, criteria.
    """
    counts = retrieval_counts or {}
    candidates: List[Tuple[float, Dict[str, Any]]] = []

    chunks = getattr(archive_store, "_chunks", {})
    chunk_embeddings = getattr(archive_store, "_chunk_embeddings", {})

    for chunk_id, chunk in chunks.items():
        text = getattr(chunk, "text", "") or ""
        doc_id = getattr(chunk, "doc_id", "") or ""
        meta = {}

        # Check if chunk's document has canon marking
        docs = getattr(archive_store, "_documents", {})
        doc = docs.get(doc_id)
        is_canon = False
        if doc:
            doc_meta = getattr(doc, "metadata", {}) or {}
            is_canon = bool(doc_meta.get("canon", False))

        chunk_emb = chunk_embeddings.get(chunk_id)

        result = evaluate_promotion(
            chunk_text=text,
            chunk_id=chunk_id,
            is_canon=is_canon,
            retrieval_count=counts.get(chunk_id, 0),
            chunk_embedding=chunk_emb,
            seed_embedding=seed_embedding,
            user_approved=False,
        )

        if result.score > 0.1:  # Only include non-trivial candidates
            candidates.append((result.score, {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "text": text[:200],
                "score": result.score,
                "promote": result.promote,
                "reason": result.reason,
                "criteria": result.criteria,
            }))

    # Sort by score descending, return top N
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [c[1] for c in candidates[:max_suggestions]]
