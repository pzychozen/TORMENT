"""Backend-neutral motif radius mathematics.

Resolution of member vectors is deliberately outside this module. Callers pass
the vectors they can currently resolve; unavailable and dimension-mismatched
members contribute no radius sample.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

from .motif_decision import _unit, cosine


ORDERED_CURRENT_MEMBER_REGEOMETRY_V1 = "ORDERED_CURRENT_MEMBER_REGEOMETRY_V1"


def ordered_current_member_regeometry_v1(
    member_vectors: Iterable[np.ndarray | Sequence[float]],
) -> tuple[tuple[float, ...], float]:
    """Derive one target-lane motif baseline from ordered qualified vectors.

    This is calculation only: callers publish one motif R1 and its membership
    set separately.  The arithmetic intentionally reuses the existing motif
    float32 normalization and cosine semantics used by the legacy attach path.
    """
    centroid: np.ndarray | None = None
    stability = 0.5
    member_count = 0
    for value in member_vectors:
        candidate = _unit(np.asarray(value, dtype=np.float32))
        if not np.all(np.isfinite(candidate)) or candidate.size == 0:
            raise ValueError("member vectors must be non-empty finite vectors")
        if centroid is None:
            centroid = candidate
            member_count = 1
            continue
        if candidate.size != centroid.size:
            raise ValueError("member vectors must share one dimension")
        raw_similarity = cosine(candidate, centroid)
        learning_rate = float(np.clip(0.12 / np.sqrt(1.0 + member_count / 8.0), 0.025, 0.08))
        centroid = _unit((1.0 - learning_rate) * centroid + learning_rate * candidate)
        stability = float(np.clip(0.90 * stability + 0.10 * max(0.0, raw_similarity), 0.0, 1.0))
        member_count += 1
    if centroid is None:
        raise ValueError("at least one member vector is required")
    return tuple(float(item) for item in centroid), stability


def motif_radius_from_member_vectors(
    centroid: Sequence[float],
    member_vectors: Iterable[np.ndarray | Sequence[float] | None],
) -> float:
    """Preserve the current legacy motif-radius calculation exactly."""
    center = np.asarray(centroid, dtype=np.float32).reshape(-1)
    if center.size == 0:
        return 0.0
    distances: list[float] = []
    for member_vector in member_vectors:
        if member_vector is None:
            continue
        vector = np.asarray(member_vector, dtype=np.float32).reshape(-1)
        if vector.size != center.size:
            continue
        distances.append(1.0 - cosine(center, vector))
    if not distances:
        return 0.0
    return float(np.mean(distances))
