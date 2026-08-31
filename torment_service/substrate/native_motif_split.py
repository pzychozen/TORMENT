"""Qualified native preparation around the frozen motif split policy.

The policy itself lives in :mod:`torment_service.motif_split_policy`; this
thin read-only adapter turns its ordered partition into native final-state
evidence usable by every qualified motif writer.
"""
from __future__ import annotations

import math
from typing import Any
from uuid import UUID

import numpy as np

from torment_service.motif_decision import MotifDecision, _unit
from torment_service.motif_split_policy import MotifSplitPlan, decide_motif_auto_split

from .errors import SubstrateInvariantViolation
from .motif_runtime_reader import NativeMotifRuntimeReader, NativeRuntimeMotif
from .motifs import MotifState, NativeMotifSplitPlan


AUTO_SPLIT_MIN_MEMBERS = 96
_CANDIDATE_MARKER = "__NATIVE_SPLIT_CANDIDATE__"


def prepare_qualified_native_motif_split(
    *,
    reader: NativeMotifRuntimeReader,
    selected: NativeRuntimeMotif,
    source_state: MotifState,
    aggregate_state: MotifState,
    decision: MotifDecision,
    candidate_member_object_id: UUID | None,
    expected_dimension: int,
    catalog_runtime_ids: tuple[str, ...],
    child_created_ts: int,
) -> NativeMotifSplitPlan | None:
    """Return final native topology or ``None`` for a genuine no-split.

    Incomplete qualified historical vectors cannot be translated to the
    legacy JSON omission behavior without silently losing first-class
    memberships.  They therefore leave the ordinary attach intact.
    """
    try:
        members = reader.list_ordered_current_motif_members(selected.motif_object_id)
    except AttributeError:
        # A catalog-only staging reader cannot establish split geometry.
        return None
    if len(members) + 1 < AUTO_SPLIT_MIN_MEMBERS:
        return None
    evidence: list[tuple[object, np.ndarray | None]] = []
    for member in members:
        raw = reader.read_current_compat_embedding(
            member.member_object_id, expected_dimension=expected_dimension,
        )
        if raw is None:
            return None
        evidence.append((member.member_object_id, _unit(raw)))
    evidence.append((_CANDIDATE_MARKER, np.asarray(decision.candidate_embedding, dtype=np.float32)))
    outcome = decide_motif_auto_split(evidence, source_state.centroid)
    if not isinstance(outcome, MotifSplitPlan):
        return None
    all_members = set(outcome.parent_members) | set(outcome.child_members)
    if all_members != {item[0] for item in evidence}:
        raise SubstrateInvariantViolation("native split policy did not partition current evidence")
    child_runtime_id = next_split_runtime_motif_id(source_state.runtime_motif_id, catalog_runtime_ids)
    parent_state = MotifState(
        source_state.semantic_scope_id, aggregate_state.runtime_motif_id,
        aggregate_state.domain_id, aggregate_state.label, outcome.parent_centroid,
        split_strength(len(outcome.parent_members), floor=.18), aggregate_state.stability_score,
        aggregate_state.contributing_agents, aggregate_state.created_ts,
        aggregate_state.last_active_ts, source_state.derivation_metadata,
        source_state.extra_payload,
    )
    child_state = MotifState(
        source_state.semantic_scope_id, child_runtime_id, source_state.domain_id,
        f"{source_state.label} sub-basin", outcome.child_centroid,
        split_strength(len(outcome.child_members), floor=.15), aggregate_state.stability_score,
        aggregate_state.contributing_agents, child_created_ts, child_created_ts,
        source_state.derivation_metadata, source_state.extra_payload,
    )
    moved = tuple(
        member.member_object_id for member in members if member.member_object_id in outcome.child_members
    )
    if not moved:
        return None
    return NativeMotifSplitPlan(
        selected.motif_object_id, selected.motif_revision_id, parent_state, child_state,
        moved, candidate_member_object_id or UUID(int=0), _CANDIDATE_MARKER in outcome.child_members,
    )


def split_strength(member_count: int, *, floor: float) -> float:
    return float(max(floor, min(1.0, .12 + .88 * (1.0 - math.exp(-member_count / 24.0)))))


def next_split_runtime_motif_id(parent_runtime_id: str, runtime_ids: tuple[str, ...]) -> str:
    import re
    maximum = max((max((int(value) for value in re.findall(r"(\d+)", item)), default=0) for item in runtime_ids), default=0)
    return f"{parent_runtime_id}_split_{maximum + 1:04d}"


__all__ = [
    "AUTO_SPLIT_MIN_MEMBERS", "next_split_runtime_motif_id",
    "prepare_qualified_native_motif_split", "split_strength",
]
