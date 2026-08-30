"""Backend-neutral motif radius mathematics.

Resolution of member vectors is deliberately outside this module. Callers pass
the vectors they can currently resolve; unavailable and dimension-mismatched
members contribute no radius sample.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

from .motif_decision import cosine


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
