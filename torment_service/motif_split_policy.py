"""Frozen, side-effect-free legacy motif auto-split policy.

This module deliberately owns only the numerical decision made by
``MotifRegistry._maybe_split_motif``.  Callers provide members in their
current logical order and vectors through their existing compatibility loader;
the helper neither reads storage nor allocates identities or timestamps.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from .motif_decision import _unit


AUTO_SPLIT_ENABLE = True
AUTO_SPLIT_MIN_MEMBERS = 96
AUTO_SPLIT_RADIUS_THRESHOLD = 0.22
AUTO_SPLIT_IMPROVEMENT_MIN = 0.08


@dataclass(frozen=True)
class NoMotifSplit:
    """The exact legacy gate which prevented an automatic split."""

    reason: str


@dataclass(frozen=True)
class MotifSplitPlan:
    """One immutable two-means partition over already ordered evidence."""

    parent_members: tuple[Any, ...]
    child_members: tuple[Any, ...]
    parent_centroid: tuple[float, ...]
    child_centroid: tuple[float, ...]
    radius_before: float
    sse_improvement: float


def decide_motif_auto_split(
    member_evidence: Iterable[tuple[Any, np.ndarray | None]],
    parent_centroid: np.ndarray | tuple[float, ...] | list[float],
    *,
    enabled: bool = AUTO_SPLIT_ENABLE,
    min_members: int = AUTO_SPLIT_MIN_MEMBERS,
    radius_threshold: float = AUTO_SPLIT_RADIUS_THRESHOLD,
    improvement_min: float = AUTO_SPLIT_IMPROVEMENT_MIN,
) -> NoMotifSplit | MotifSplitPlan:
    """Return legacy's exact split decision without performing a mutation.

    Vectors must already have passed the legacy member-loader's ``_unit``
    transformation.  ``None`` preserves the old unavailable-vector behavior:
    it is omitted from split evidence.
    """
    if not enabled:
        return NoMotifSplit("DISABLED")

    evidence = tuple(member_evidence)
    if len(evidence) < min_members:
        return NoMotifSplit("MEMBER_COUNT")

    members: list[Any] = []
    vectors: list[np.ndarray] = []
    for member, vector in evidence:
        if vector is None:
            continue
        members.append(member)
        vectors.append(np.asarray(vector, dtype=np.float32))
    if len(vectors) < min_members:
        return NoMotifSplit("USABLE_VECTOR_COUNT")
    try:
        X = np.stack(vectors, axis=0).astype(np.float32)
    except ValueError:
        return NoMotifSplit("VECTOR_SHAPE")
    if X.ndim != 2 or not np.all(np.isfinite(X)):
        return NoMotifSplit("VECTOR_SHAPE")

    c = _unit(np.asarray(parent_centroid, dtype=np.float32))
    if c.ndim != 1 or c.size != X.shape[1] or not np.all(np.isfinite(c)):
        return NoMotifSplit("CENTROID_SHAPE")
    d = np.sum((X - c[None, :]) ** 2, axis=1)
    radius = float(np.mean(1.0 - np.clip(X @ c, -1.0, 1.0)))
    if radius < radius_threshold:
        return NoMotifSplit("RADIUS")

    seed_a = int(np.argmax(d))
    d2 = np.sum((X - X[seed_a][None, :]) ** 2, axis=1)
    seed_b = int(np.argmax(d2))
    if seed_a == seed_b:
        return NoMotifSplit("SEEDS")

    ca = X[seed_a].copy()
    cb = X[seed_b].copy()
    assign = np.zeros((X.shape[0],), dtype=np.int32)
    for _ in range(12):
        da = np.sum((X - ca[None, :]) ** 2, axis=1)
        db = np.sum((X - cb[None, :]) ** 2, axis=1)
        # ``db < da`` intentionally retains ties in legacy parent/cluster 0.
        assign = (db < da).astype(np.int32)
        if np.all(assign == 0) or np.all(assign == 1):
            break
        ca = _unit(X[assign == 0].mean(axis=0))
        cb = _unit(X[assign == 1].mean(axis=0))
    n0 = int(np.sum(assign == 0))
    n1 = int(np.sum(assign == 1))
    if n0 < 16 or n1 < 16:
        return NoMotifSplit("CHILD_POPULATION")

    base_sse = float(np.sum((X - c[None, :]) ** 2))
    sse0 = float(np.sum((X[assign == 0] - ca[None, :]) ** 2))
    sse1 = float(np.sum((X[assign == 1] - cb[None, :]) ** 2))
    improved = 1.0 - ((sse0 + sse1) / (base_sse + 1e-12))
    if improved < improvement_min:
        return NoMotifSplit("SSE_IMPROVEMENT")

    return MotifSplitPlan(
        tuple(member for index, member in enumerate(members) if assign[index] == 0),
        tuple(member for index, member in enumerate(members) if assign[index] == 1),
        tuple(float(value) for value in _unit(ca)),
        tuple(float(value) for value in _unit(cb)),
        radius,
        float(improved),
    )


__all__ = [
    "AUTO_SPLIT_ENABLE",
    "AUTO_SPLIT_IMPROVEMENT_MIN",
    "AUTO_SPLIT_MIN_MEMBERS",
    "AUTO_SPLIT_RADIUS_THRESHOLD",
    "MotifSplitPlan",
    "NoMotifSplit",
    "decide_motif_auto_split",
]
