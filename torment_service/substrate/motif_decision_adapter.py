"""Staging adapter that commits a motif decision through NativeMotifService.

The adapter has no runtime activation hook.  Its caller supplies ordered native
motif identities and, for a create, the compatibility runtime motif ID.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID

import numpy as np

from ..motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    MotifDecision,
    MotifDecisionPolicy,
    MotifReadModel,
    decide_attach_or_create,
    realize_attach_next_state,
    realize_create_next_state,
)
from .motifs import MotifState, NativeMotifMutationResult, NativeMotifService, NativeMotifSplitResult, NativeMotifView
from .motif_runtime_reader import NativeMotifRuntimeReader, NativeRuntimeMotif
from .native_motif_split import prepare_qualified_native_motif_split


@dataclass(frozen=True)
class NativeMotifDecisionPlan:
    """One backend-neutral decision paired with its selected native carrier."""

    decision: MotifDecision
    selected_motif: NativeMotifView | None
    catalog: tuple[NativeMotifView, ...]


class NativeMotifDecisionAdapter:
    """Apply 7G5A2 decisions with the existing 7G5A1 semantic service."""

    def __init__(self, service: NativeMotifService) -> None:
        self._service = service

    def decide(
        self,
        *,
        ordered_motif_object_ids: tuple[UUID, ...],
        embedding: np.ndarray,
        attach_threshold: float,
        policy: MotifDecisionPolicy = CURRENT_MOTIF_DECISION_POLICY,
    ) -> NativeMotifDecisionPlan:
        """Read native relationship cardinalities in caller-provided order only."""
        entries: list[tuple[NativeMotifView, MotifReadModel]] = []
        for motif_object_id in ordered_motif_object_ids:
            view = self._service.get_current_motif(motif_object_id)
            state = view.state
            entries.append(
                (
                    view,
                    MotifReadModel(
                        state.runtime_motif_id,
                        state.domain_id,
                        state.label,
                        state.centroid,
                        state.strength,
                        len(self._service.list_current_motif_members(motif_object_id)),
                        state.contributing_agents,
                        state.stability_score,
                        state.created_ts,
                        state.last_active_ts,
                    ),
                )
            )
        decision = decide_attach_or_create(
            tuple(model for _view, model in entries), embedding, attach_threshold, policy
        )
        selected = next(
            (view for view, model in entries if model is decision.selected), None
        )
        return NativeMotifDecisionPlan(decision, selected, tuple(view for view, _model in entries))

    def apply(
        self,
        plan: NativeMotifDecisionPlan,
        *,
        member_object_id: UUID,
        agent_id: str,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
        motif_alias_namespace_id: UUID,
        membership_identity_namespace_id: UUID,
        last_active_ts: int,
        motif_identity_namespace_id: UUID | None = None,
        runtime_motif_id: str | None = None,
        domain_id: str | None = None,
        semantic_scope_id: UUID | None = None,
        summary: str = "",
        created_ts: int | None = None,
        derivation_metadata: Mapping[str, Any] | None = None,
        extra_payload: Mapping[str, Any] | None = None,
    ) -> NativeMotifMutationResult | NativeMotifSplitResult:
        """Commit the already-decided branch without retry/staleness bypasses."""
        if plan.decision.kind == "ATTACH_EXISTING":
            if plan.selected_motif is None:
                raise ValueError("attach plan has no selected native motif")
            source = plan.selected_motif.state
            aggregate = realize_attach_next_state(
                plan.decision, agent_id=agent_id, last_active_ts=last_active_ts
            )
            state = _native_state(
                aggregate,
                source.semantic_scope_id,
                source.derivation_metadata,
                source.extra_payload,
            )
            selected = NativeRuntimeMotif(
                plan.selected_motif.motif_object_id, plan.selected_motif.motif_revision_id,
                plan.selected_motif.revision_ordinal, source.semantic_scope_id,
                plan.decision.selected,
            )
            split_plan = prepare_qualified_native_motif_split(
                reader=NativeMotifRuntimeReader(self._service._connection), selected=selected,
                source_state=source, aggregate_state=state, decision=plan.decision,
                candidate_member_object_id=member_object_id,
                expected_dimension=len(plan.decision.candidate_embedding),
                catalog_runtime_ids=tuple(item.state.runtime_motif_id for item in plan.catalog),
                child_created_ts=last_active_ts,
            )
            if split_plan is not None:
                return self._service.split_motif_with_member(
                    idempotency_namespace_id=idempotency_namespace_id,
                    idempotency_key=idempotency_key,
                    motif_identity_namespace_id=plan.selected_motif.identity_namespace_id,
                    membership_identity_namespace_id=membership_identity_namespace_id,
                    motif_alias_namespace_id=motif_alias_namespace_id,
                    plan=split_plan,
                )
            return self._service.add_motif_member(
                idempotency_namespace_id=idempotency_namespace_id,
                idempotency_key=idempotency_key,
                motif_alias_namespace_id=motif_alias_namespace_id,
                membership_identity_namespace_id=membership_identity_namespace_id,
                motif_object_id=plan.selected_motif.motif_object_id,
                expected_motif_revision_id=plan.selected_motif.motif_revision_id,
                state=state,
                member_object_id=member_object_id,
            )

        if (
            motif_identity_namespace_id is None
            or runtime_motif_id is None
            or domain_id is None
            or semantic_scope_id is None
            or created_ts is None
        ):
            raise ValueError("create plan requires explicit native identity, runtime motif ID, domain, scope, and created timestamp")
        aggregate = realize_create_next_state(
            plan.decision,
            runtime_motif_id=runtime_motif_id,
            domain_id=domain_id,
            summary=summary,
            agent_id=agent_id,
            created_ts=created_ts,
            last_active_ts=last_active_ts,
        )
        state = _native_state(aggregate, semantic_scope_id, derivation_metadata, extra_payload)
        return self._service.create_motif_with_member(
            idempotency_namespace_id=idempotency_namespace_id,
            idempotency_key=idempotency_key,
            motif_identity_namespace_id=motif_identity_namespace_id,
            membership_identity_namespace_id=membership_identity_namespace_id,
            motif_alias_namespace_id=motif_alias_namespace_id,
            state=state,
            member_object_id=member_object_id,
        )


def _native_state(
    aggregate: Any,
    semantic_scope_id: UUID,
    derivation_metadata: Mapping[str, Any] | None,
    extra_payload: Mapping[str, Any] | None,
) -> MotifState:
    return MotifState(
        semantic_scope_id,
        aggregate.runtime_motif_id,
        aggregate.domain_id,
        aggregate.label,
        aggregate.centroid,
        aggregate.strength,
        aggregate.stability_score,
        aggregate.contributing_agents,
        aggregate.created_ts,
        aggregate.last_active_ts,
        derivation_metadata,
        extra_payload,
    )
