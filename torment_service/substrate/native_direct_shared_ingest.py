"""Explicit E1-only direct shared ingest over already-determined Fabric facts.

This module is deliberately not imported by ``TormentFabric``.  It has no
selector, fallback, dual-write/read, or production activation authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from torment_service.post_write_runtime import FabricPostWriteContext, PostWriteStorageOutcome

from .errors import SubstrateConfigurationError, SubstrateInvariantViolation
from .fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteAttempt,
    NativeFabricRouteQualification,
    NativeFabricRouteRequest,
    NativeFabricRouteResult,
    NativeFabricRoutingCapability,
    NativeFabricRoutingScope,
)
from .native_memory_vector_runtime import NativeMemoryVectorRuntime
from .native_post_write_runtime import (
    NativeFabricPostWriteAdapter,
    NativePostWriteRouteWitness,
    NativeSharedIntegratedPostWriteOutcome,
)


@dataclass(frozen=True)
class NativeDirectSharedPostWriteFacts:
    """The post-write facts Fabric already computed before storage selection."""

    promotion_score: float
    stability_delta: float
    tri_mod: Mapping[str, Any]
    debug: Mapping[str, Any]
    srg_state: Mapping[str, Any] | None
    phase_durations: Mapping[str, Any]
    state_symbol: str | None
    affect_tag: str | None
    affect_conf: float | None
    skip_packet_emission: bool

    def __post_init__(self) -> None:
        for name in ("tri_mod", "debug", "phase_durations"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise ValueError(f"{name} must be a mapping")
            object.__setattr__(self, name, MappingProxyType(dict(value)))
        if self.srg_state is not None:
            if not isinstance(self.srg_state, Mapping):
                raise ValueError("srg_state must be a mapping or None")
            object.__setattr__(self, "srg_state", MappingProxyType(dict(self.srg_state)))
        if type(self.skip_packet_emission) is not bool:
            raise ValueError("skip_packet_emission must be a boolean")


@dataclass(frozen=True)
class NativeDirectSharedIngestResult:
    """One E1 qualification attempt, including the exact vector-lane ledger."""

    route_attempt: NativeFabricRouteAttempt
    post_write: NativeSharedIntegratedPostWriteOutcome | None
    invalidated_lane_keys: tuple[tuple[object, ...], ...]


class NativeDirectSharedIngestAdapter:
    """One explicit, qualification-only shared source + integrated-tail seam."""

    def __init__(
        self,
        *,
        capability: NativeFabricRoutingCapability,
        post_write_adapter: NativeFabricPostWriteAdapter,
        warm_vector_runtimes: tuple[NativeMemoryVectorRuntime, ...],
    ) -> None:
        if not isinstance(capability, NativeFabricRoutingCapability):
            raise ValueError("capability must be a prepared NativeFabricRoutingCapability")
        if not isinstance(post_write_adapter, NativeFabricPostWriteAdapter):
            raise ValueError("post_write_adapter must be NativeFabricPostWriteAdapter")
        if not isinstance(warm_vector_runtimes, tuple) or not warm_vector_runtimes:
            raise ValueError("warm_vector_runtimes must be a non-empty tuple")
        if any(not isinstance(item, NativeMemoryVectorRuntime) for item in warm_vector_runtimes):
            raise ValueError("warm_vector_runtimes must contain NativeMemoryVectorRuntime values")
        self._capability = capability
        self._post_write = post_write_adapter
        self._router = NativeFabricMemoryRouter(capability)
        self._vector_by_scope: dict[object, NativeMemoryVectorRuntime] = {}
        for runtime in warm_vector_runtimes:
            configuration = runtime.configuration
            if (
                configuration.expected_core_id != capability.core_id
                or configuration.core_database_path != capability.core_database_path
                or configuration.representation_lane != capability.binding.representation_lane
            ):
                raise SubstrateConfigurationError("E1 vector runtime does not match the prepared native capability")
            key = configuration.scope
            if key in self._vector_by_scope:
                raise SubstrateConfigurationError("E1 vector runtime bindings have duplicate lane scopes")
            self._vector_by_scope[key] = runtime

    def execute(
        self,
        request: NativeFabricRouteRequest,
        facts: NativeDirectSharedPostWriteFacts,
        *,
        _test_stop_after: str | None = None,
    ) -> NativeDirectSharedIngestResult:
        """Route one shared source with no legacy fallback or input recomputation."""
        if not isinstance(request, NativeFabricRouteRequest):
            raise ValueError("request must be NativeFabricRouteRequest")
        if not isinstance(facts, NativeDirectSharedPostWriteFacts):
            raise ValueError("facts must be NativeDirectSharedPostWriteFacts")
        if request.scope != "shared":
            raise SubstrateInvariantViolation("E1 direct ingest accepts shared routes only")

        # This is intentionally before ``router.route``: D6's deployment
        # premise must fail before any shared source, motif, or representation
        # can be committed.
        self._post_write.preflight_shared_integrated_default()
        target_scope, _mood_scope = self._post_write.shared_integrated_ready_scopes()
        qualification = self._router.qualify(request)
        if not qualification.eligible:
            return NativeDirectSharedIngestResult(
                NativeFabricRouteAttempt(qualification), None, (),
            )
        if qualification.route_scope != target_scope:
            return NativeDirectSharedIngestResult(
                NativeFabricRouteAttempt(NativeFabricRouteQualification(
                    False, qualification.route_scope, "POST_WRITE_SCOPE_NOT_CLAIMED",
                )),
                None,
                (),
            )
        self._require_warm_lanes(target_scope)
        before_eids = {
            scope: frozenset(row.eid for row in runtime.snapshot.rows)
            for scope, runtime in self._vector_by_scope.items()
            if runtime.snapshot is not None
        }
        attempt = self._router.route(request, _test_stop_after=_test_stop_after)
        if attempt.result is None:
            return NativeDirectSharedIngestResult(attempt, None, ())
        result = attempt.result
        if result.reinforced:
            raise SubstrateInvariantViolation("E1 shared direct ingest must never use native reinforcement")
        context = _post_write_context(request, result, facts)
        observed_ready: list[tuple[NativeFabricRoutingScope, int]] = []
        try:
            post_write = self._post_write.run_shared_integrated_default(
                context,
                route_witness=NativePostWriteRouteWitness(result, request.native_operation_key),
                on_ready_memory=lambda scope, eid: observed_ready.append((scope, eid)),
            )
        except Exception:
            self._invalidate_new_ready_lanes(observed_ready, before_eids)
            raise
        invalidated = self._invalidate_new_ready_lanes(observed_ready, before_eids)
        return NativeDirectSharedIngestResult(attempt, post_write, invalidated)

    def _require_warm_lanes(self, source_scope: NativeFabricRoutingScope) -> None:
        _source, mood_scope = self._post_write.shared_integrated_ready_scopes()
        for scope in (source_scope.runtime_scope, mood_scope.runtime_scope):
            runtime = self._vector_by_scope.get(scope)
            if runtime is None:
                raise SubstrateConfigurationError("E1 requires an injected vector runtime for every READY target lane")
            if runtime.snapshot is None:
                raise SubstrateConfigurationError("E1 requires warm vector runtimes before direct ingest")

    def _invalidate_new_ready_lanes(
        self,
        ready: list[tuple[NativeFabricRoutingScope, int]],
        before_eids: Mapping[object, frozenset[int]],
    ) -> tuple[tuple[object, ...], ...]:
        invalidated: list[tuple[object, ...]] = []
        seen: set[tuple[object, ...]] = set()
        for scope, eid in ready:
            runtime = self._vector_by_scope.get(scope.runtime_scope)
            if runtime is None:
                raise SubstrateConfigurationError("E1 READY lane lacks an injected vector runtime")
            if eid in before_eids.get(scope.runtime_scope, frozenset()):
                continue
            lane_key = runtime.configuration.lane_key
            if lane_key in seen:
                continue
            runtime.invalidate("E1 READY representation changed")
            seen.add(lane_key)
            invalidated.append(lane_key)
        return tuple(invalidated)


def _post_write_context(
    request: NativeFabricRouteRequest,
    result: NativeFabricRouteResult,
    facts: NativeDirectSharedPostWriteFacts,
) -> FabricPostWriteContext:
    """Project stored result plus unchanged Fabric facts into the fixed tail context."""
    if result.reinforced:
        raise SubstrateInvariantViolation("E1 shared direct ingest must not project reinforcement")
    return FabricPostWriteContext.make(
        workspace_id=request.workspace_id,
        agent_id=request.agent_id,
        scope="shared",
        chosen_domain=request.domain_id,
        step=request.logical_step,
        storage_outcome=PostWriteStorageOutcome.CREATED_NEW,
        stored=result.stored,
        eid=result.eid,
        created_motif=result.motifs[0] if result.motifs else None,
        motif_ids=result.motifs,
        half_life_days=request.half_life_days,
        summary=request.summary,
        embedding=request.incoming_embedding,
        memory_class=request.memory_class,
        memory_type=request.memory_type,
        strength=request.strength,
        confidence=request.confidence,
        promotion_score=facts.promotion_score,
        stability_delta=facts.stability_delta,
        tri_mod=facts.tri_mod,
        debug=facts.debug,
        srg_state=facts.srg_state,
        phase_durations=facts.phase_durations,
        state_symbol=facts.state_symbol,
        affect_tag=facts.affect_tag,
        affect_conf=facts.affect_conf,
        skip_packet_emission=facts.skip_packet_emission,
    )


__all__ = [
    "NativeDirectSharedIngestAdapter",
    "NativeDirectSharedIngestResult",
    "NativeDirectSharedPostWriteFacts",
]
