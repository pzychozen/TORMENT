"""Pure-ish current motif attach/create decision and aggregate-state math.

This module deliberately has no registry, file, SQLite, UUID, or backend
knowledge.  It preserves the existing MotifRegistry equations so a decided
mutation can be applied by the legacy registry or a staging native adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


MotifDecisionKind = Literal["ATTACH_EXISTING", "CREATE_NEW"]


@dataclass(frozen=True)
class MotifDecisionPolicy:
    gravity_strength_weight: float = 0.10
    gravity_density_weight: float = 0.07
    gravity_stability_weight: float = 0.05


CURRENT_MOTIF_DECISION_POLICY = MotifDecisionPolicy()


@dataclass(frozen=True)
class MotifReadModel:
    """Backend-neutral current aggregate state in its observable iteration order."""

    runtime_motif_id: str
    domain_id: str
    label: str
    centroid: tuple[float, ...]
    strength: float
    member_count: int
    contributing_agents: tuple[str, ...]
    stability_score: float
    created_ts: int
    last_active_ts: int

    def centroid_np(self) -> np.ndarray:
        return np.asarray(self.centroid, dtype=np.float32)


@dataclass(frozen=True)
class MotifDecision:
    """The selected branch and the diagnostics used by legacy event output."""

    kind: MotifDecisionKind
    candidate_embedding: tuple[float, ...]
    selected: MotifReadModel | None
    raw_similarity: float | None
    attach_score: float | None
    effective_threshold: float
    pre_mutation_density: float | None


@dataclass(frozen=True)
class MotifAggregateState:
    """A realized motif aggregate successor; membership remains adapter-owned."""

    runtime_motif_id: str
    domain_id: str
    label: str
    centroid: tuple[float, ...]
    strength: float
    stability_score: float
    contributing_agents: tuple[str, ...]
    created_ts: int
    last_active_ts: int


def _unit(v: np.ndarray) -> np.ndarray:
    """The current motif float32 unit-vector behavior, preserved verbatim."""
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v) + 1e-12)
    return (v / n).astype(np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """The current motif cosine behavior, including its epsilon treatment."""
    na = float(np.linalg.norm(a) + 1e-12)
    nb = float(np.linalg.norm(b) + 1e-12)
    return float(np.dot(a, b) / (na * nb))


def motif_density(member_count: int) -> float:
    return float(min(1.0, np.log1p(max(0, member_count)) / np.log(129.0)))


def motif_gravity_bonus(state: MotifReadModel, policy: MotifDecisionPolicy) -> float:
    strength = float(np.clip(state.strength, 0.0, 1.0))
    density = motif_density(state.member_count)
    stability = float(np.clip(state.stability_score, 0.0, 1.0))
    return float(
        policy.gravity_strength_weight * strength
        + policy.gravity_density_weight * density
        + policy.gravity_stability_weight * stability
    )


def decide_attach_or_create(
    ordered_motifs: tuple[MotifReadModel, ...],
    embedding: np.ndarray,
    attach_threshold: float,
    policy: MotifDecisionPolicy = CURRENT_MOTIF_DECISION_POLICY,
) -> MotifDecision:
    """Choose the current attach/create branch without allocating or persisting."""
    candidate = _unit(embedding)
    dim = int(candidate.size)
    best: MotifReadModel | None = None
    best_raw_similarity = -1.0
    best_attach_score = -1.0
    best_effective_threshold = attach_threshold
    best_density: float | None = None

    for motif in ordered_motifs:
        centroid = motif.centroid_np()
        if centroid.size != dim:
            continue
        raw_similarity = cosine(candidate, centroid)
        density = motif_density(motif.member_count)
        attach_score = float(raw_similarity + motif_gravity_bonus(motif, policy))
        effective_threshold = float(
            max(
                0.62,
                attach_threshold - (0.04 * density + 0.03 * float(np.clip(motif.strength, 0.0, 1.0))),
            )
        )
        # Strict replacement retains current first-in-iteration tie behavior.
        if attach_score > best_attach_score:
            best = motif
            best_raw_similarity = raw_similarity
            best_attach_score = attach_score
            best_effective_threshold = effective_threshold
            best_density = density

    if best is not None and best_attach_score >= best_effective_threshold:
        return MotifDecision(
            "ATTACH_EXISTING",
            tuple(float(value) for value in candidate),
            best,
            float(best_raw_similarity),
            float(best_attach_score),
            float(best_effective_threshold),
            best_density,
        )
    return MotifDecision(
        "CREATE_NEW",
        tuple(float(value) for value in candidate),
        None,
        None,
        None,
        float(best_effective_threshold),
        None,
    )


def realize_attach_next_state(
    decision: MotifDecision,
    *,
    agent_id: str,
    last_active_ts: int,
) -> MotifAggregateState:
    """Realize the current attach aggregate math without mutating its read model."""
    if decision.kind != "ATTACH_EXISTING" or decision.selected is None:
        raise ValueError("an ATTACH_EXISTING decision is required")
    motif = decision.selected
    candidate = np.asarray(decision.candidate_embedding, dtype=np.float32)
    centroid = _unit(motif.centroid_np())
    member_n = max(1, motif.member_count)
    learning_rate = float(np.clip(0.12 / np.sqrt(1.0 + member_n / 8.0), 0.025, 0.08))
    new_centroid = _unit((1.0 - learning_rate) * centroid + learning_rate * candidate)
    agents = list(motif.contributing_agents)
    if agent_id not in agents:
        agents.append(agent_id)
    target_strength = float(0.12 + 0.88 * (1.0 - np.exp(-(motif.member_count + 1) / 24.0)))
    return MotifAggregateState(
        motif.runtime_motif_id,
        motif.domain_id,
        motif.label,
        tuple(float(value) for value in new_centroid),
        float(max(motif.strength, min(1.0, target_strength))),
        float(np.clip(0.90 * motif.stability_score + 0.10 * max(0.0, decision.raw_similarity), 0.0, 1.0)),
        tuple(agents),
        motif.created_ts,
        last_active_ts,
    )


def motif_label_from_summary(domain_id: str, summary: str) -> str:
    summary = (summary or "").strip()
    tokens = [token.strip(".,:;!?()[]{}\\\"\\'").lower() for token in summary.split()]
    tokens = [token for token in tokens if token and len(token) > 2][:5]
    if not tokens:
        return f"{domain_id} motif"
    return " ".join(tokens)


def realize_create_next_state(
    decision: MotifDecision,
    *,
    runtime_motif_id: str,
    domain_id: str,
    summary: str,
    agent_id: str,
    created_ts: int,
    last_active_ts: int,
) -> MotifAggregateState:
    """Realize a CREATE_NEW decision after an adapter supplies its runtime ID."""
    if decision.kind != "CREATE_NEW":
        raise ValueError("a CREATE_NEW decision is required")
    return MotifAggregateState(
        runtime_motif_id,
        domain_id,
        motif_label_from_summary(domain_id, summary),
        decision.candidate_embedding,
        0.10,
        0.5,
        (agent_id,),
        created_ts,
        last_active_ts,
    )
