"""Private/direct B5-A4R2 native public-ingest recovery executor.

This module is intentionally not imported by REST, Spine, MCP, startup, or a
backend selector.  It proves one owner-qualified execution/recovery envelope.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Callable, Mapping

import numpy as np

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.fabric import TormentFabric, _detect_canon_conflict
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

from .fabric_native_routing import NativeFabricRouteRequest, NativeFabricRouteResult
from .native_post_write_runtime import (
    NativePostWriteQualificationConfiguration,
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
        return FabricIngestStorageOutcome(
            workspace_id=prepared.workspace_id, agent_id=prepared.agent_id,
            scope=prepared.scope, domain_id=prepared.domain_id,
            disposition=(
                FabricIngestStorageDisposition.REINFORCED_EXISTING
                if result.reinforced else FabricIngestStorageDisposition.CREATED_NEW
            ),
            stored=result.stored, eid=result.eid, motif_ids=result.motifs,
            # Native route results expose affected public runtime motif IDs;
            # for a new source the first one is the normal compatibility
            # creation surface, without exposing native structural UUIDs.
            created_motif=(None if result.reinforced or not result.motifs else result.motifs[0]),
            state_symbol=None,
            storage_witness=(result, request.native_operation_key),
        )


class NativePublicIngestExecutor:
    """One recovery envelope over an already-qualified active native owner."""

    def __init__(
        self,
        *,
        owner: NativeProductionResourceOwner,
        fabric: TormentFabric,
        post_write_configuration: Callable[[PreparedFabricIngest], NativePostWriteQualificationConfiguration],
    ) -> None:
        if not isinstance(owner, NativeProductionResourceOwner):
            raise ValueError("native public executor requires a production owner")
        if not isinstance(fabric, TormentFabric) or not callable(post_write_configuration):
            raise ValueError("native public executor requires Fabric and post-write configuration")
        self._owner = owner
        self._fabric = fabric
        self._post_write_configuration = post_write_configuration
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
        prepared = self._fabric.ingest(
            request.workspace_id, request.agent_id, request.text, step=request.step,
            domain_id=request.domain_id, tri_mod=(None if request.tri_mod is None else dict(request.tri_mod)),
            supplied_summary=request.supplied_summary, supplied_embedding=request.supplied_embedding,
            scope=request.scope, provenance=(None if request.provenance is None else dict(request.provenance)),
            memory_class=request.memory_class,
            extra_payload=(None if request.extra_payload is None else dict(request.extra_payload)),
            skip_packet_emission=request.skip_packet_emission, suppress_canon=request.suppress_canon,
            public_mutation_key=request.public_mutation_key, _prepare_only=True,
        )
        if not isinstance(prepared, PreparedFabricIngest):
            raise NativePublicIngestExecutionError("Fabric preparation did not return PreparedFabricIngest")
        return prepared

    def _execute_prepared(
        self, prepared: PreparedFabricIngest, test_storage_stop_after: str | None,
    ) -> dict[str, Any]:
        outcome = self._storage.store(prepared, _test_stop_after=test_storage_stop_after)
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
