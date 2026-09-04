"""Private/direct B5-A4R2 native public-ingest recovery executor.

This module is intentionally not imported by REST, Spine, MCP, startup, or a
backend selector.  It proves one owner-qualified execution/recovery envelope.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import logging
from typing import Any, Callable, Mapping

import numpy as np

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.fabric import TormentFabric, _detect_canon_conflict, _mark_embed_audit_dirty
from torment_service.ingest_orchestration import (
    FabricIngestStorageDisposition,
    FabricIngestStorageOutcome,
    PreparedFabricIngest,
)
from torment_service.post_write_runtime import FabricPostWriteContext, PostWriteStorageOutcome
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.public_mutation_identity import (
    canonical_public_request_fingerprint,
    derive_native_operation_key,
    normalize_public_mutation_key,
)

from .fabric_native_routing import (
    NativeFabricRouteRequest,
    NativeFabricRouteResult,
    NativePrimaryOutcomeWitness,
    NativePrecommitSymbolStateEffect,
)
from .native_post_write_runtime import (
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativePostWriteRouteWitness,
)
from .native_public_mutation_receipts import (
    NativePublicMutationReceiptStore,
    PublicMutationRecoveryRequired,
    PublicMutationRecoveryState,
)
from .payload_policy import MEMORY_STRUCTURAL_PAYLOAD_KEYS
from .production_native_owner import NativeProductionResourceOwner


class NativePublicIngestExecutionError(RuntimeError):
    """The direct native executor cannot safely continue this operation."""


class NativePublicIngestInterruption(RuntimeError):
    """Qualification-only deterministic crash-window interruption."""


@dataclass(frozen=True)
class NativePublicIngestRequest:
    """Direct-use public semantic inputs; this is not a transport request."""

    workspace_id: str
    agent_id: str
    text: str
    public_mutation_key: str
    step: int = 0
    domain_id: str | None = None
    tri_mod: Mapping[str, float] | None = None
    supplied_summary: str | None = None
    supplied_embedding: list[float] | None = None
    scope: str = "private"
    provenance: Mapping[str, Any] | None = None
    memory_class: str = "core"
    extra_payload: Mapping[str, Any] | None = None
    skip_packet_emission: bool = False
    suppress_canon: bool = False


class NativeFabricIngestStorageAdapter:
    """Route one frozen carrier through the existing active native router."""

    def __init__(self, owner: NativeProductionResourceOwner, fabric: TormentFabric) -> None:
        self._owner = owner
        self._fabric = fabric

    def store(
        self,
        prepared: PreparedFabricIngest,
        *,
        _test_stop_after: str | None = None,
    ) -> FabricIngestStorageOutcome:
        if prepared.native_operation_key is None:
            raise NativePublicIngestExecutionError("prepared native public operation key is required")
        if not prepared.allow_write:
            return FabricIngestStorageOutcome(
                workspace_id=prepared.workspace_id, agent_id=prepared.agent_id,
                scope=prepared.scope, domain_id=prepared.domain_id,
                disposition=FabricIngestStorageDisposition.NO_WRITE,
                stored=False, eid=None, motif_ids=(), created_motif=None,
                state_symbol=None, storage_witness=None,
                primary_outcome_witness=_ordinary_no_write_witness(prepared),
                # This deliberately is not inferred from ``stored``.  Legacy
                # ordinary NO_WRITE reaches its always-run post-write tail,
                # unlike a failed canonical flush.
                post_write_eligible=True,
            )
        runtime = self._owner._recover_active_runtime()
        lane = runtime.representation_lane
        request = NativeFabricRouteRequest(
            workspace_id=prepared.workspace_id,
            scope=prepared.scope,
            agent_id=prepared.agent_id,
            domain_id=prepared.domain_id,
            native_operation_key=_storage_key(prepared.native_operation_key),
            embedder_lane=lane,
            summary=prepared.summary,
            memory_type=prepared.memory_type,
            memory_class=prepared.memory_class,
            strength=prepared.strength,
            confidence=prepared.confidence,
            half_life_days=0.0 if prepared.half_life_days is None else prepared.half_life_days,
            logical_step=prepared.logical_step,
            created_ts=prepared.frozen_created_ts,
            last_active_ts=prepared.frozen_last_active_ts,
            last_reinforced_ts=prepared.frozen_last_reinforced_ts,
            incoming_embedding=prepared.embedding,
            provenance=ProvenanceV1.from_dict(dict(prepared.provenance)),
            governance=MemoryGovernanceFlags(),
            flexible_payload=_native_flexible_payload(prepared),
            raw_links=prepared.links,
            attach_threshold=prepared.attach_threshold,
            stability_delta=prepared.stability_delta,
            prior_symbol=prepared.prior_symbol,
            prior_symbol_trace=prepared.prior_symbol_trace,
            prior_motif_id=prepared.prior_motif_id,
            prior_tension=prepared.prior_tension,
            precommit_spawn_observer=lambda _eid: _mark_embed_audit_dirty(
                self._fabric.data_dir, prepared.workspace_id,
            ),
            precommit_symbol_state_owner=lambda effect: self._apply_symbol_precommit_owner(effect),
            # I4B-2's two-stage true-split proof is a private native-public
            # route only. Shared public ingest retains its established route
            # and post-write dispatch without this opt-in.
            precommit_parity_required=prepared.scope == "private",
            contradiction_guard=lambda incoming, existing, similarity: bool(
                _detect_canon_conflict(incoming, existing, similarity)[0]
            ),
        )
        with self._owner.open_write_context() as context:
            attempt = context.route(request, _test_stop_after=_test_stop_after)
        if not attempt.qualification.eligible or attempt.result is None:
            raise NativePublicIngestExecutionError(
                f"native public storage is not qualified: {attempt.qualification.reason_code}"
            )
        result = attempt.result
        primary_witness = result.primary_outcome
        canonical_failure = (
            not result.stored
            and primary_witness is not None
            and primary_witness.create_failure_disposition
            == "CANONICAL_FLUSH_FAILURE_STRUCTURED"
        )
        if not result.stored and not canonical_failure:
            raise NativePublicIngestExecutionError(
                "native public storage returned an unclassified non-stored outcome"
            )
        return FabricIngestStorageOutcome(
            workspace_id=prepared.workspace_id, agent_id=prepared.agent_id,
            scope=prepared.scope, domain_id=prepared.domain_id,
            disposition=(
                FabricIngestStorageDisposition.NO_WRITE
                if not result.stored else (
                    FabricIngestStorageDisposition.REINFORCED_EXISTING
                    if result.reinforced else FabricIngestStorageDisposition.CREATED_NEW
                )
            ),
            stored=result.stored, eid=result.eid, motif_ids=result.motifs,
            # This is route-owned semantic truth.  It must not be inferred
            # from affected motifs: I4B-2 attach-then-split affects parent and
            # child but did not create a normal public motif.
            created_motif=result.created_motif,
            state_symbol=None,
            # A failed canonical flush is never a stored route witness.  The
            # legacy source returns before the storage/post-write adapter, so
            # preserve its residue and public failure without entering the
            # downstream tail.
            storage_witness=(None if canonical_failure else (result, request.native_operation_key)),
            primary_outcome_witness=primary_witness,
            post_write_eligible=not canonical_failure,
            failure_code=("canonical_commit_failed" if canonical_failure else None),
        )

    def _apply_symbol_precommit_owner(
        self, effect: NativePrecommitSymbolStateEffect,
    ) -> Mapping[str, Any]:
        """Delegate native orchestration to Fabric's retained symbol owner."""
        return self._fabric._apply_native_precommit_symbol_state(
            effect.workspace_id,
            effect.agent_id,
            primary_motif_id=effect.runtime_motif_id,
            current_tension=effect.current_tension,
            enrichment=dict(effect.enrichment),
        )


class NativePublicIngestExecutor:
    """One recovery envelope over an already-qualified active native owner."""

    def __init__(
        self,
        *,
        owner: NativeProductionResourceOwner,
        fabric: TormentFabric,
        post_write_configuration: Callable[[PreparedFabricIngest], NativePostWriteQualificationConfiguration],
        preparation_context: Callable[[NativePublicIngestRequest], Mapping[str, Any]] | None = None,
    ) -> None:
        if not isinstance(owner, NativeProductionResourceOwner):
            raise ValueError("native public executor requires a production owner")
        if not isinstance(fabric, TormentFabric) or not callable(post_write_configuration):
            raise ValueError("native public executor requires Fabric and post-write configuration")
        self._owner = owner
        self._fabric = fabric
        self._post_write_configuration = post_write_configuration
        self._preparation_context = preparation_context
        self._receipts = NativePublicMutationReceiptStore(owner)
        self._storage = NativeFabricIngestStorageAdapter(owner, fabric)

    def execute(
        self,
        request: NativePublicIngestRequest,
        *,
        _test_interrupt_after: str | None = None,
        _test_storage_stop_after: str | None = None,
    ) -> dict[str, Any]:
        key = normalize_public_mutation_key(request.public_mutation_key)
        if key is None:
            raise NativePublicIngestExecutionError("native public execution requires a caller mutation key")
        fingerprint = _fingerprint(request)
        native_key = derive_native_operation_key(
            operation="ingest", workspace_id=request.workspace_id,
            agent_id=request.agent_id, key=key,
        )
        reservation = self._receipts.reserve(
            workspace_id=request.workspace_id, agent_id=request.agent_id,
            operation="ingest", native_operation_key=native_key,
            public_request_fingerprint=fingerprint,
        )
        if _test_interrupt_after == "RESERVED":
            raise NativePublicIngestInterruption("interrupted after RESERVED")
        recovery = self._receipts.recover(reservation)
        if recovery.state is PublicMutationRecoveryState.COMMITTED_SAME_REQUEST:
            assert recovery.result is not None
            return dict(recovery.result)
        if recovery.state is PublicMutationRecoveryState.COGNITION_OUTCOME_UNCERTAIN:
            raise PublicMutationRecoveryRequired("COGNITION_OUTCOME_UNCERTAIN: RECOVERY_REQUIRED")
        if recovery.state is PublicMutationRecoveryState.NEW:
            # This durable fence precedes Fabric's first mutable preparation
            # effect (agent/kernel/phase/SRG/role/affect work).
            self._receipts.mark_cognition_started(reservation)
            if _test_interrupt_after == "COGNITION_STARTED":
                raise NativePublicIngestInterruption("interrupted after COGNITION_STARTED")
            prepared = self._prepare(request)
            prepared = self._receipts.write_prepared(reservation, prepared)
            if _test_interrupt_after == "PREPARED":
                raise NativePublicIngestInterruption("interrupted after PREPARED")
        else:
            assert recovery.prepared is not None
            prepared = recovery.prepared
        result = self._execute_prepared(prepared, _test_storage_stop_after)
        if _test_interrupt_after == "POST_WRITE":
            raise NativePublicIngestInterruption("interrupted after post-write")
        return self._receipts.complete(reservation, result)

    def _prepare(self, request: NativePublicIngestRequest) -> PreparedFabricIngest:
        context: dict[str, Any] = {}
        if self._preparation_context is not None:
            supplied = self._preparation_context(request)
            if not isinstance(supplied, Mapping):
                raise NativePublicIngestExecutionError("native preparation context must be a mapping")
            # This is a private executor seam, not public caller input.  The
            # runtime factory uses it only to pass an inert native workspace
            # view and an already-validated identity into Fabric cognition.
            context = dict(supplied)
        prepared = self._fabric.ingest(
            request.workspace_id, request.agent_id, request.text, step=request.step,
            domain_id=request.domain_id, tri_mod=(None if request.tri_mod is None else dict(request.tri_mod)),
            supplied_summary=request.supplied_summary, supplied_embedding=request.supplied_embedding,
            scope=request.scope, provenance=(None if request.provenance is None else dict(request.provenance)),
            memory_class=request.memory_class,
            extra_payload=(None if request.extra_payload is None else dict(request.extra_payload)),
            skip_packet_emission=request.skip_packet_emission, suppress_canon=request.suppress_canon,
            public_mutation_key=request.public_mutation_key, _prepare_only=True,
            **context,
        )
        if not isinstance(prepared, PreparedFabricIngest):
            raise NativePublicIngestExecutionError("Fabric preparation did not return PreparedFabricIngest")
        return prepared

    def _execute_prepared(
        self, prepared: PreparedFabricIngest, test_storage_stop_after: str | None,
    ) -> dict[str, Any]:
        outcome = self._storage.store(prepared, _test_stop_after=test_storage_stop_after)
        if not outcome.post_write_eligible:
            # This matches Fabric's canonical flush exception branch: it
            # leaves precommit residue but returns before the post-write
            # adapter, and it must not manufacture a route witness.
            if outcome.failure_code != "canonical_commit_failed":
                raise NativePublicIngestExecutionError(
                    "native public storage withheld post-write without a canonical failure"
                )
            return {
                "stored": False,
                "reinforced": False,
                "failure_code": outcome.failure_code,
                "eid": None,
                "domain_chosen": prepared.domain_id,
            }
        route_result, route_key = _route_witness(outcome)
        context = FabricPostWriteContext.make(
            workspace_id=prepared.workspace_id, agent_id=prepared.agent_id,
            scope=prepared.scope, chosen_domain=prepared.domain_id,
            step=prepared.logical_step,
            storage_outcome=PostWriteStorageOutcome(outcome.disposition.value),
            stored=outcome.stored, eid=outcome.eid, created_motif=outcome.created_motif,
            motif_ids=outcome.motif_ids, half_life_days=prepared.half_life_days,
            summary=prepared.summary, embedding=np.asarray(prepared.embedding, dtype=np.float32),
            memory_class=prepared.memory_class, memory_type=prepared.memory_type,
            strength=prepared.strength, confidence=prepared.confidence,
            promotion_score=prepared.promotion_score, stability_delta=prepared.stability_delta,
            tri_mod=prepared.tri_mod, debug=prepared.debug, srg_state=prepared.srg_state,
            phase_durations=prepared.phase_durations, state_symbol=outcome.state_symbol,
            affect_tag=prepared.affect_tag, affect_conf=prepared.affect_conf,
            skip_packet_emission=prepared.skip_packet_emission,
        )
        configuration = self._post_write_configuration(prepared)
        if (
            route_result is not None
            and route_result.precommit_true_split
            and prepared.scope == "private"
        ):
            # I4C composes conflict ahead of I4B-2's motif/anchor tail. I4D
            # retains mood and Character; I4E adds SRG, private trajectory/
            # world, and checkpoint around their frozen legacy positions.
            configuration = replace(
                configuration,
                profile=(
                    NativePostWriteQualificationProfile
                    .core_staging_with_i4e_private_tail()
                ),
                motif_suggestion_maintenance_required=True,
                # I4F's ordinary broad-private proposal/bridge continuation
                # is not part of I4B-2's frozen created-only true-split tail.
                bridge_suggestions_required=False,
            )
        with self._owner.open_post_write_context(configuration=configuration) as post_write:
            post = post_write.run(
                context,
                route_witness=NativePostWriteRouteWitness(route_result, route_key),
            )
        return {
            "stored": outcome.stored,
            "reinforced": outcome.reinforced,
            "proposal_id": post.proposal_id,
            "eid": outcome.eid,
            "domain_ranked": [dict(item) for item in prepared.domain_ranked],
            "domain_chosen": prepared.domain_id,
            "motifs": list(outcome.motif_ids),
            "tri_mod": dict(prepared.tri_mod),
            "created_motif": outcome.created_motif,
            "signals": {
                "write_intent": prepared.write_intent,
                "memory_type": prepared.memory_type,
                "strength": prepared.strength,
                "confidence": prepared.confidence,
                "half_life": prepared.signal_half_life_days,
                "promotion_score": prepared.promotion_score,
                "links": list(prepared.links),
                "stability_delta": prepared.stability_delta,
            },
            "debug": dict(prepared.debug),
        }


def _fingerprint(request: NativePublicIngestRequest) -> str:
    return canonical_public_request_fingerprint(
        operation="ingest", workspace_id=request.workspace_id, agent_id=request.agent_id,
        semantic_payload={
            "text": request.text, "step": int(request.step), "domain_id": request.domain_id,
            "scope": request.scope, "supplied_summary": request.supplied_summary,
            "supplied_embedding": request.supplied_embedding,
            "provenance": None if request.provenance is None else dict(request.provenance),
            "memory_class": request.memory_class,
            "extra_payload": None if request.extra_payload is None else dict(request.extra_payload),
            "skip_packet_emission": bool(request.skip_packet_emission),
            "suppress_canon": bool(request.suppress_canon),
        },
    )


def _storage_key(native_operation_key: str) -> str:
    return f"{native_operation_key}:STORAGE"


def _ordinary_no_write_witness(prepared: PreparedFabricIngest) -> NativePrimaryOutcomeWitness:
    """Observe a write-gate refusal without inventing a native source row."""
    return NativePrimaryOutcomeWitness(
        scope=prepared.scope,
        attempt_origin="WRITE_GATE",
        reinforcement_disposition="NOT_APPLICABLE",
        final_storage_outcome="NO_WRITE",
        create_failure_disposition="NONE",
        primary_canonical_state_committed=False,
        qualified_memory_eid=None,
        qualified_memory_object_id=None,
        qualified_memory_revision_id=None,
    )


def _native_flexible_payload(prepared: PreparedFabricIngest) -> dict[str, Any]:
    """Project only ordinary payload facts into the native flexible carrier.

    Route identity, provenance, lifecycle, and governance are already carried
    by typed ``NativeFabricRouteRequest`` fields.  They must never be copied
    here: the qualified composition service correctly refuses flexible
    structural shadows before its first source transaction.
    """
    caller = {
        key: value
        for key, value in dict(prepared.flexible_payload).items()
        if key.casefold() not in MEMORY_STRUCTURAL_PAYLOAD_KEYS
    }
    caller.pop("affect_attribution", None)
    caller.update({
        "workspace_id": prepared.workspace_id,
        "domain_id": prepared.domain_id,
        "agent_id": prepared.agent_id,
        "embedding_provider": prepared.embedding_provider,
        "embedding_model": prepared.embedding_model,
        "embedding_dim": prepared.embedding_dimension,
        "embedding_checksum": prepared.embedding_checksum,
        "affect_tag": prepared.affect_tag, "affect_conf": prepared.affect_conf,
        "in_corridor": prepared.in_corridor,
        "survival_steps": prepared.survival_steps,
        "tearing_risk": prepared.tearing_risk,
        "hl_mult": prepared.half_life_multiplier,
        "seed_v0": prepared.tri_mod.get("seed_v0") or [0.0, 0.0, 0.0],
        "seed_pos0": prepared.tri_mod.get("seed_pos0") or [0.0, 0.0, 0.0],
        "phase_duration_steps": prepared.phase_durations.get("phase_duration_steps", 0),
        "corridor_duration_steps": prepared.phase_durations.get("corridor_duration_steps", 0),
        "srg": None if prepared.srg_state is None else dict(prepared.srg_state),
    })
    if prepared.affect_classification_completed:
        # Keep the native payload on the existing marker vocabulary without
        # allowing caller-provided affect lineage to survive the merge.
        caller["affect_attribution"] = {"affect_tag": prepared.affect_tag}
    return caller


def _route_witness(
    outcome: FabricIngestStorageOutcome,
) -> tuple[NativeFabricRouteResult | None, str | None]:
    witness = outcome.storage_witness
    if witness is None:
        return None, None
    route, key = witness
    if not isinstance(route, NativeFabricRouteResult) or not isinstance(key, str):
        raise NativePublicIngestExecutionError("native storage witness is malformed")
    return route, key


__all__ = [
    "NativeFabricIngestStorageAdapter",
    "NativePublicIngestExecutionError",
    "NativePublicIngestExecutor",
    "NativePublicIngestInterruption",
    "NativePublicIngestRequest",
]
