"""Pure recovery of P3 source plans from an already-frozen P2 description.

This module intentionally has no filesystem inputs.  Envelope recovery
supplies a typed ``RootNativeProductionAdmissionDescription`` and its bound
``RootEvidenceManifest``; this module only projects those immutable facts to
the source-plan representation consumed by P3.
"""

from __future__ import annotations

from .explicit_source_evidence import (
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
)
from .root_admission_description import (
    MaterializedScopePosture,
    RootNativeProductionAdmissionDescription,
)
from .root_scope import RootScopeKind


class RootP2SourcePlanRecoveryRefused(ValueError):
    """Raised when frozen P2 facts cannot determine one source plan exactly."""


def _source_plan_types():
    """Avoid importing the compatibility packet during migration package init."""

    from ..corrective_freeze_packet import RootSourceScopePlan, SourceArtifactPresence

    return RootSourceScopePlan, SourceArtifactPresence


def recover_root_source_scope_plans(
    description: RootNativeProductionAdmissionDescription,
) -> tuple[RootSourceScopePlan, ...]:
    """Recover the exact generic P3 source-plan tuple from P2 facts.

    Private scopes deliberately retain ``motif_domain_id=None``.  Character
    witness-domain derivation is a separate P3 concern and is never folded
    into this generic source-plan projection.
    """

    if not isinstance(description, RootNativeProductionAdmissionDescription):
        raise RootP2SourcePlanRecoveryRefused(
            "P2 source-plan recovery requires a typed root description"
        )

    RootSourceScopePlan, SourceArtifactPresence = _source_plan_types()
    recovered: list[RootSourceScopePlan] = []
    for workspace in description.workspace_plans:
        # The adapter captures physical private scopes, then physical shared
        # scopes, then declared-only shared scopes.  All three groups are
        # preserved by the canonical description, so recover that exact tuple
        # order instead of inventing a new sort order.
        declared_scopes = (
            *workspace.private_materialized_scopes,
            *(item for item in workspace.shared_materialized_scopes
              if item.materialization_posture is not MaterializedScopePosture.DECLARED_EMPTY_SHARED),
            *(item for item in workspace.shared_materialized_scopes
              if item.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED),
        )
        for declared in declared_scopes:
            scope = declared.scope_key
            if scope.scope_kind is RootScopeKind.PRIVATE:
                motif_domain_id = None
                motif_presence = SourceArtifactPresence.ABSENT
            elif scope.scope_kind is RootScopeKind.SHARED:
                motif_domain_id = scope.domain_id
                if motif_domain_id is None:
                    raise RootP2SourcePlanRecoveryRefused(
                        "shared P2 runtime scope is missing its domain identity"
                    )
                motif_presence = _shared_motif_presence(
                    description=description,
                    scope_plan=declared,
                )
            else:  # pragma: no cover - RootScopeKey makes this unreachable.
                raise RootP2SourcePlanRecoveryRefused("P2 scope kind is unsupported")
            recovered.append(
                RootSourceScopePlan(
                    scope_key=scope,
                    materialization_posture=declared.materialization_posture,
                    representation_disposition=declared.representation_disposition,
                    motif_domain_id=motif_domain_id,
                    target_representation_lane=description.target_representation_lane,
                    motif_presence=motif_presence,
                )
            )
    return tuple(recovered)


def _shared_motif_presence(
    *,
    description: RootNativeProductionAdmissionDescription,
    scope_plan: object,
) -> SourceArtifactPresence:
    """Apply the bounded P2 motif-presence law for one shared runtime scope."""

    _RootSourceScopePlan, SourceArtifactPresence = _source_plan_types()
    posture = scope_plan.materialization_posture
    if posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF:
        return SourceArtifactPresence.PRESENT
    if posture in {
        MaterializedScopePosture.EMPTY_SHARED_WITHOUT_MOTIF,
        MaterializedScopePosture.DECLARED_EMPTY_SHARED,
    }:
        return SourceArtifactPresence.ABSENT
    if posture is not MaterializedScopePosture.MEMORY_GRAPH:
        raise RootP2SourcePlanRecoveryRefused("P2 materialization posture is unsupported")

    motif_entries = tuple(
        entry
        for entry in description.explicit_source_manifest.entries
        if entry.scope_key == scope_plan.scope_key
        and entry.semantic_role is EvidenceSemanticRole.MOTIFS
    )
    if len(motif_entries) > 1:
        raise RootP2SourcePlanRecoveryRefused(
            "P2 shared motif evidence is ambiguous or duplicated"
        )
    return (
        SourceArtifactPresence.PRESENT
        if motif_entries
        and motif_entries[0].presence_expectation
        is EvidencePresenceExpectation.EXPECTED_PRESENT
        else SourceArtifactPresence.ABSENT
    )


__all__ = [
    "RootP2SourcePlanRecoveryRefused",
    "recover_root_source_scope_plans",
]
