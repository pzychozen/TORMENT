"""A3D qualification-only native Fabric routing boundary.

This module intentionally has no startup hook, environment selector, or
production activation path.  A caller must explicitly prepare a STAGING-only
capability, explicitly claim a routing scope, and supply a stable operation
key before this boundary will open an existing native core.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import threading
from types import MappingProxyType
from typing import Any, Callable, Iterator, Mapping
from uuid import UUID

import numpy as np

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.provenance_v1 import ProvenanceV1

from .compat import NativeMemoryCompatibilityFacade
from .canonical_intent import canonical_intent_text
from .connection import open_existing_native_core_connection
from .errors import (
    SubstrateConfigurationError,
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
)
from .fabric_translation import (
    ABSENT,
    FabricStructuralTranslationRequest,
    QualifiedCompatibilityLinkTarget,
    translate_fabric_structural,
)
from .ids import native_id_from_bytes, native_id_to_bytes
from .memory_motif_composition import (
    NativeMemoryMotifCompositionRequest,
    NativeMemoryMotifCompositionService,
    StaleMotifCatalogError,
    UnsupportedNativeSplitError,
)
from .memory_reinforcement import (
    NativeMemoryReinforcementRequest,
    NativeMemoryReinforcementService,
)
from .native_srg_runtime import (
    NativeSRGProcessState,
    NativeSRGTransientRuntime,
    SRGSuccessorMaterialization,
)
from .native_world_runtime import (
    NativeWorldProcessState,
    NativeWorldRuntime,
    WorldDiagnosticSuccessorMaterialization,
)
from .motif_runtime_reader import NativeMotifRuntimeReader, NativeRuntimeMotif
from .representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from .runtime_binding import (
    NativeMemoryRuntimeBinding,
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
)
from .schema import CORE_ROLE_STAGING, require_current_schema


_LEGACY_ACTIVE_DEPLOYMENT = "LEGACY_ACTIVE"
_PRIVATE_AGENT_SCOPE = "PRIVATE_AGENT"
_SHARED_DOMAIN_SCOPE = "SHARED_DOMAIN"
_PREPARED = object()


class NativeMotifProcessOrderError(SubstrateInvariantViolation):
    """A live catalog cannot be placed honestly in a process-local order."""


@dataclass(frozen=True)
class NativeFabricRoutingScope:
    """Additional explicit namespaces required by an A3D routing scope."""

    runtime_scope: NativeMemoryRuntimeScope
    motif_alias_namespace_id: UUID
    motif_identity_namespace_id: UUID
    membership_identity_namespace_id: UUID
    idempotency_namespace_id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.runtime_scope, NativeMemoryRuntimeScope):
            raise ValueError("runtime_scope must be NativeMemoryRuntimeScope")
        for field_name in (
            "motif_alias_namespace_id",
            "motif_identity_namespace_id",
            "membership_identity_namespace_id",
            "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, field_name), UUID):
                raise ValueError(f"{field_name} must be a UUID")

    @property
    def key(self) -> tuple[str, str, str]:
        return _runtime_scope_key(self.runtime_scope)


class NativeMotifProcessOrder:
    """Per-capability process ordering for current native runtime motifs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._runtime_ids: dict[tuple[str, str, str, str, UUID], tuple[str, ...]] = {}

    @contextmanager
    def locked_catalog(
        self,
        *,
        reader: NativeMotifRuntimeReader,
        routing_scope: NativeFabricRoutingScope,
        domain_id: str,
    ) -> Iterator[tuple[NativeRuntimeMotif, ...]]:
        """Yield the current catalog in frozen process order under one lock."""
        if not isinstance(domain_id, str) or not domain_id:
            raise NativeMotifProcessOrderError("process motif order requires a domain_id")
        key = (*routing_scope.key, domain_id, routing_scope.motif_alias_namespace_id)
        with self._lock:
            live = reader.list_runtime_motifs(
                motif_alias_namespace_id=routing_scope.motif_alias_namespace_id,
                domain_id=domain_id,
                semantic_scope_id=routing_scope.runtime_scope.semantic_scope_id,
            )
            live_by_runtime_id = {item.read_model.runtime_motif_id: item for item in live}
            if len(live_by_runtime_id) != len(live):
                raise NativeMotifProcessOrderError("native motif catalog has duplicate runtime IDs")
            known = self._runtime_ids.get(key)
            if known is None:
                # A reader starts each process from the frozen lexicographic
                # baseline.  Later creation is appended below, never re-sorted.
                known = tuple(sorted(live_by_runtime_id))
                self._runtime_ids[key] = known
            elif set(known) != set(live_by_runtime_id):
                raise NativeMotifProcessOrderError(
                    "native motif catalog changed outside the process-order owner"
                )
            yield tuple(live_by_runtime_id[item] for item in known)

    def append_created(
        self,
        *,
        routing_scope: NativeFabricRoutingScope,
        domain_id: str,
        runtime_motif_id: str,
    ) -> None:
        """Append one locally-created motif without changing existing order."""
        key = (*routing_scope.key, domain_id, routing_scope.motif_alias_namespace_id)
        with self._lock:
            known = self._runtime_ids.get(key)
            if known is None:
                raise NativeMotifProcessOrderError("motif order was not initialized before creation")
            if runtime_motif_id in known:
                return
            self._runtime_ids[key] = (*known, runtime_motif_id)

    def runtime_ids_for_testing(
        self, *, routing_scope: NativeFabricRoutingScope, domain_id: str,
    ) -> tuple[str, ...] | None:
        """Return an immutable diagnostic snapshot; it has no routing authority."""
        key = (*routing_scope.key, domain_id, routing_scope.motif_alias_namespace_id)
        with self._lock:
            return self._runtime_ids.get(key)


@dataclass(frozen=True)
class NativeFabricRoutingCapability:
    """Prepared STAGING capability facts, distinct from the inert binding."""

    binding: NativeMemoryRuntimeBinding
    core_database_path: Path
    core_id: UUID
    routing_scopes: tuple[NativeFabricRoutingScope, ...]
    process_order: NativeMotifProcessOrder = field(repr=False, compare=False)
    srg_process_state: NativeSRGProcessState = field(repr=False, compare=False)
    world_process_state: NativeWorldProcessState = field(repr=False, compare=False)
    production_activation_allowed: bool = False
    qualification_only: bool = True
    _prepared_marker: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._prepared_marker is not _PREPARED:
            raise SubstrateConfigurationError(
                "native Fabric routing capability must be explicitly prepared"
            )
        if self.production_activation_allowed is not False or self.qualification_only is not True:
            raise SubstrateConfigurationError("A3D routing capability cannot grant production activation")

    def claimed_scope(
        self,
        *,
        workspace_id: str,
        scope: str,
        agent_id: str,
        domain_id: str,
    ) -> NativeFabricRoutingScope | None:
        target = _request_scope_key(workspace_id, scope, agent_id, domain_id)
        for routing_scope in self.routing_scopes:
            if routing_scope.key == target:
                return routing_scope
        return None


@dataclass(frozen=True)
class NativeFabricRouteQualification:
    """Stable, explicit admission outcome for one Fabric-facing route."""

    eligible: bool
    route_scope: NativeFabricRoutingScope | None
    reason_code: str
    production_activation_allowed: bool = False


@dataclass(frozen=True)
class NativeFabricRouteRequest:
    """Already-known Fabric facts for one explicitly qualified memory route."""

    workspace_id: str
    scope: str
    agent_id: str
    domain_id: str
    native_operation_key: str | None
    embedder_lane: NativeRepresentationLane
    summary: str
    memory_type: str
    memory_class: str
    strength: float
    confidence: float
    half_life_days: float
    logical_step: int
    created_ts: int
    last_active_ts: int
    last_reinforced_ts: int
    incoming_embedding: Any
    provenance: ProvenanceV1
    governance: MemoryGovernanceFlags
    flexible_payload: Mapping[str, Any] = field(default_factory=dict)
    raw_links: tuple[str, ...] | list[str] = ()
    qualified_link_targets: tuple[QualifiedCompatibilityLinkTarget, ...] | list[QualifiedCompatibilityLinkTarget] = ()
    lifecycle_state: str = "ORDINARY"
    lifecycle_authoritative: bool = False
    governance_state: str = "DERIVED"
    attach_threshold: float = 0.76
    stability_delta: float = 0.0
    prior_symbol: str = ""
    prior_symbol_trace: tuple[str, ...] | list[str] = ()
    prior_motif_id: str = ""
    prior_tension: float = 0.0
    last_tool_refresh_ts: int | None = None
    contradiction_guard: Callable[[str, str, float], bool] | None = field(
        default=None, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        for field_name in (
            "workspace_id", "scope", "agent_id", "domain_id", "summary",
            "memory_type", "memory_class", "lifecycle_state", "governance_state",
        ):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name):
                raise ValueError(f"{field_name} must be non-empty text")
        if self.native_operation_key is not None and (
            not isinstance(self.native_operation_key, str) or not self.native_operation_key
        ):
            raise ValueError("native_operation_key must be non-empty text when supplied")
        if not isinstance(self.embedder_lane, NativeRepresentationLane):
            raise ValueError("embedder_lane must be NativeRepresentationLane")
        if not isinstance(self.provenance, ProvenanceV1):
            raise ValueError("provenance must be ProvenanceV1")
        if not isinstance(self.governance, MemoryGovernanceFlags):
            raise ValueError("governance must be MemoryGovernanceFlags")
        if not isinstance(self.flexible_payload, Mapping):
            raise ValueError("flexible_payload must be a mapping")
        object.__setattr__(self, "flexible_payload", MappingProxyType(dict(self.flexible_payload)))
        object.__setattr__(self, "raw_links", tuple(self.raw_links))
        object.__setattr__(self, "qualified_link_targets", tuple(self.qualified_link_targets))
        object.__setattr__(self, "prior_symbol_trace", tuple(str(item) for item in self.prior_symbol_trace))
        for field_name in ("logical_step", "created_ts", "last_active_ts", "last_reinforced_ts"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.last_tool_refresh_ts is not None and (
            not isinstance(self.last_tool_refresh_ts, int)
            or isinstance(self.last_tool_refresh_ts, bool)
            or self.last_tool_refresh_ts < 0
        ):
            raise ValueError("last_tool_refresh_ts must be a non-negative integer when supplied")


@dataclass(frozen=True)
class NativeFabricRouteResult:
    """Bounded native result; native identities stay internal to the adapter."""

    stored: bool
    reinforced: bool
    eid: int
    domain_id: str
    motifs: tuple[str, ...]
    memory_object_id: UUID
    memory_revision_id: UUID
    representation_id: UUID


@dataclass(frozen=True)
class NativeFabricRouteAttempt:
    qualification: NativeFabricRouteQualification
    result: NativeFabricRouteResult | None = None


def prepare_native_fabric_routing_capability(
    *,
    binding: NativeMemoryRuntimeBinding,
    connection: sqlite3.Connection,
    routing_scopes: tuple[NativeFabricRoutingScope, ...],
    expected_core_id: UUID,
) -> NativeFabricRoutingCapability:
    """Re-qualify an existing v1.1 STAGING core for explicit A3D tests only."""
    _validate_capability_inputs(binding, connection, routing_scopes, expected_core_id)
    path = _validated_connection_path(connection, binding.core_database_path)
    metadata = require_current_schema(connection)
    core_id = native_id_from_bytes(metadata.core_id)
    if core_id != expected_core_id or core_id != binding.core_id:
        raise SubstrateConfigurationError("routing capability core identity does not match the prepared binding")
    if metadata.core_role != CORE_ROLE_STAGING or binding.core_role != CORE_ROLE_STAGING:
        raise SubstrateConfigurationError("routing capability requires a STAGING core")
    deployment = connection.execute(
        "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
    ).fetchall()
    if deployment != [(_LEGACY_ACTIVE_DEPLOYMENT, None)]:
        raise SubstrateConfigurationError("routing capability requires LEGACY_ACTIVE deployment with no referenced core")
    _validate_lane(binding.representation_lane)
    _validate_routing_scopes(connection, binding, routing_scopes)
    return NativeFabricRoutingCapability(
        binding=binding,
        core_database_path=path,
        core_id=core_id,
        routing_scopes=routing_scopes,
        process_order=NativeMotifProcessOrder(),
        srg_process_state=NativeSRGProcessState(),
        world_process_state=NativeWorldProcessState(),
        _prepared_marker=_PREPARED,
    )


class NativeFabricMemoryRouter:
    """Per-operation A3D adapter; it never owns a long-lived SQLite handle."""

    def __init__(self, capability: NativeFabricRoutingCapability) -> None:
        if not isinstance(capability, NativeFabricRoutingCapability):
            raise ValueError("a prepared NativeFabricRoutingCapability is required")
        self._capability = capability

    def qualify(self, request: NativeFabricRouteRequest) -> NativeFabricRouteQualification:
        """Classify route selection before opening or mutating the native core."""
        scope = self._capability.claimed_scope(
            workspace_id=request.workspace_id,
            scope=request.scope,
            agent_id=request.agent_id,
            domain_id=request.domain_id,
        )
        if scope is None:
            return NativeFabricRouteQualification(False, None, "SCOPE_NOT_CLAIMED")
        if request.native_operation_key is None:
            return NativeFabricRouteQualification(False, scope, "MISSING_NATIVE_OPERATION_KEY")
        if request.embedder_lane != self._capability.binding.representation_lane:
            return NativeFabricRouteQualification(False, scope, "EMBEDDER_LANE_MISMATCH")
        try:
            _canonical_vector(request.incoming_embedding, request.embedder_lane.dimension)
        except ValueError:
            return NativeFabricRouteQualification(False, scope, "REPRESENTATION_NOT_QUALIFIED")
        return NativeFabricRouteQualification(True, scope, "QUALIFIED")

    def route(
        self,
        request: NativeFabricRouteRequest,
        *,
        _test_stop_after: str | None = None,
    ) -> NativeFabricRouteAttempt:
        """Execute one qualified native source route or return a refusal.

        A refusal occurs before a claimed native mutation.  Once A3C2 or A3C3
        has started, representation errors are deliberately propagated so the
        caller can retry this same native operation key; no legacy fallback is
        present in this adapter.
        """
        qualification = self.qualify(request)
        if not qualification.eligible:
            return NativeFabricRouteAttempt(qualification)
        assert qualification.route_scope is not None
        vector = _canonical_vector(request.incoming_embedding, request.embedder_lane.dimension)
        with open_existing_native_core_connection(self._capability.core_database_path) as opened:
            connection = opened.connection
            try:
                _revalidate_capability_for_route(self._capability, connection)
            except Exception:
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "CORE_NOT_CURRENT")
                )
            try:
                translation = _translate_route(request, qualification.route_scope)
            except (TypeError, ValueError):
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "PROVENANCE_NOT_QUALIFIED")
                )
            if translation.link_classification != ABSENT:
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "LINKS_DEFERRED")
                )
            try:
                world_runtime = NativeWorldRuntime(
                    connection,
                    legacy_source_namespace_id=(
                        qualification.route_scope.runtime_scope.legacy_source_namespace_id
                    ),
                    expected_dimension=request.embedder_lane.dimension,
                    process_state=self._capability.world_process_state,
                )
                result = self._route_qualified(
                    connection, request, qualification.route_scope, translation, vector, world_runtime,
                    _test_stop_after=_test_stop_after,
                )
            except NativeMotifProcessOrderError:
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "PROCESS_ORDER_INVALID")
                )
            except StaleMotifCatalogError:
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "PROCESS_ORDER_INVALID")
                )
            except UnsupportedNativeSplitError:
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "UNSUPPORTED_NATIVE_SPLIT")
                )
            except ValueError:
                # Structural translation and A3C2 planning both reject before
                # a source semantic transaction starts.  This remains an
                # explicit native qualification refusal, never a legacy retry.
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "STRUCTURAL_PAYLOAD_REFUSED")
                )
        return NativeFabricRouteAttempt(qualification, result)

    def _route_qualified(
        self,
        connection: sqlite3.Connection,
        request: NativeFabricRouteRequest,
        routing_scope: NativeFabricRoutingScope,
        translation: Any,
        vector: np.ndarray,
        world_runtime: NativeWorldRuntime,
        *,
        _test_stop_after: str | None,
    ) -> NativeFabricRouteResult:
        assert request.native_operation_key is not None
        recovered = _recover_reinforcement_request(
            connection, routing_scope.idempotency_namespace_id, request.native_operation_key
        )
        if recovered is not None:
            if recovered.routing_input_digest != _routing_input_digest(
                request, routing_scope, vector
            ):
                raise SubstrateIdempotencyConflict(
                    "native routing operation key was reused with different Fabric inputs"
                )
            srg_runtime = NativeSRGTransientRuntime(
                connection,
                legacy_source_namespace_id=routing_scope.runtime_scope.legacy_source_namespace_id,
                process_state=self._capability.srg_process_state,
            )
            # R2 is the first source operation in this branch, so capture the
            # pre-operation current world before recovering it.
            world_runtime.ensure_initialized()
            reinforced = NativeMemoryReinforcementService(connection).reinforce(
                recovered,
                _test_stop_after=_test_stop_after,
                on_source_committed=lambda source: _synchronize_world_successor(world_runtime, source),
            )
            if recovered.srg_materialization is not None:
                srg_runtime.acknowledge_materialized_successor(
                    recovered.srg_materialization,
                    eid=reinforced.source.eid,
                    successor_revision_id=reinforced.source.revision_id,
                )
            if recovered.world_diagnostic_materialization is not None:
                world_runtime.acknowledge_materialized_successor(
                    recovered.world_diagnostic_materialization,
                    eid=reinforced.source.eid,
                    successor_revision_id=reinforced.source.revision_id,
                )
            return NativeFabricRouteResult(
                True, True, reinforced.source.eid, request.domain_id, (),
                reinforced.source.memory_object_id, reinforced.source.revision_id,
                reinforced.e2_representation_id,
            )

        selected = self._select_private_duplicate(
            connection, request, routing_scope, vector,
        )
        if selected is not None:
            hit, source_channel = selected
            tool_refresh = request.last_tool_refresh_ts if source_channel == "tool_result" else None
            srg_runtime = NativeSRGTransientRuntime(
                connection,
                legacy_source_namespace_id=routing_scope.runtime_scope.legacy_source_namespace_id,
                process_state=self._capability.srg_process_state,
            )
            materialization = srg_runtime.prepare_successor_materialization(
                eid=hit.eid, expected_revision_id=hit.revision_id,
            )
            world_materialization = world_runtime.prepare_successor_materialization(
                eid=hit.eid, expected_revision_id=hit.revision_id,
            )
            reinforcement_request = NativeMemoryReinforcementRequest(
                legacy_source_namespace_id=routing_scope.runtime_scope.legacy_source_namespace_id,
                eid=hit.eid,
                expected_revision_id=hit.revision_id,
                expected_representation_id=hit.representation_id,
                idempotency_namespace_id=routing_scope.idempotency_namespace_id,
                idempotency_key=_reinforcement_base_key(request.native_operation_key),
                reinforcement_step=request.logical_step,
                last_reinforced_ts=request.last_reinforced_ts,
                expected_dimension=request.embedder_lane.dimension,
                last_tool_refresh_ts=tool_refresh,
                routing_input_digest=_routing_input_digest(request, routing_scope, vector),
                srg_materialization=materialization,
                world_diagnostic_materialization=world_materialization,
            )
            reinforced = NativeMemoryReinforcementService(connection).reinforce(
                reinforcement_request,
                _test_stop_after=_test_stop_after,
                on_source_committed=lambda source: _synchronize_world_successor(world_runtime, source),
            )
            if materialization is not None:
                srg_runtime.acknowledge_materialized_successor(
                    materialization,
                    eid=reinforced.source.eid,
                    successor_revision_id=reinforced.source.revision_id,
                )
            if world_materialization is not None:
                world_runtime.acknowledge_materialized_successor(
                    world_materialization,
                    eid=reinforced.source.eid,
                    successor_revision_id=reinforced.source.revision_id,
                )
            return NativeFabricRouteResult(
                True, True, reinforced.source.eid, request.domain_id, (),
                reinforced.source.memory_object_id, reinforced.source.revision_id,
                reinforced.e2_representation_id,
            )

        reader = NativeMotifRuntimeReader(connection)
        composition = NativeMemoryMotifCompositionService(connection)
        with self._capability.process_order.locked_catalog(
            reader=reader, routing_scope=routing_scope, domain_id=request.domain_id,
        ) as ordered_catalog:
            composition_request = NativeMemoryMotifCompositionRequest(
                legacy_source_namespace_id=routing_scope.runtime_scope.legacy_source_namespace_id,
                memory_identity_namespace_id=routing_scope.runtime_scope.identity_namespace_id,
                semantic_scope_id=routing_scope.runtime_scope.semantic_scope_id,
                summary=request.summary,
                memory_type=request.memory_type,
                memory_class=request.memory_class,
                strength=request.strength,
                confidence=request.confidence,
                half_life_days=request.half_life_days,
                user_id=request.agent_id,
                logical_step=request.logical_step,
                flexible_payload=request.flexible_payload,
                lifecycle_state=request.lifecycle_state,
                lifecycle_authoritative=request.lifecycle_authoritative,
                governance_state=request.governance_state,
                provenance=translation.provenance,
                governance=translation.governance,
                motif_alias_namespace_id=routing_scope.motif_alias_namespace_id,
                motif_identity_namespace_id=routing_scope.motif_identity_namespace_id,
                membership_identity_namespace_id=routing_scope.membership_identity_namespace_id,
                domain_id=request.domain_id,
                agent_id=request.agent_id,
                idempotency_namespace_id=routing_scope.idempotency_namespace_id,
                idempotency_key=_new_memory_source_key(request.native_operation_key),
                incoming_embedding=vector,
                attach_threshold=request.attach_threshold,
                created_ts=request.created_ts,
                last_active_ts=request.last_active_ts,
                expected_dimension=request.embedder_lane.dimension,
                stability_delta=request.stability_delta,
                prior_symbol=request.prior_symbol,
                prior_symbol_trace=request.prior_symbol_trace,
                prior_motif_id=request.prior_motif_id,
                prior_tension=request.prior_tension,
                qualified_link_intents=translation.qualified_link_intents,
                unresolved_link_references=translation.unresolved_link_references,
            )
            preview = composition.prepare_plan_from_ordered_catalog(
                composition_request, ordered_catalog
            )
            # A3C2 is the first source operation in this branch.  Planning is
            # read-only; initialization must happen immediately before commit
            # so a newly committed row receives fresh rather than reload state.
            world_runtime.ensure_initialized()
            composition_result = composition.commit(preview)
            if composition_result.runtime_motif_id not in {
                item.read_model.runtime_motif_id for item in ordered_catalog
            }:
                self._capability.process_order.append_created(
                    routing_scope=routing_scope,
                    domain_id=request.domain_id,
                    runtime_motif_id=composition_result.runtime_motif_id,
                )
            world_runtime.register_fresh_created(
                eid=composition_result.memory_eid,
                memory_object_id=composition_result.memory_object_id,
                memory_revision_id=composition_result.memory_revision_id,
                memory_revision_ordinal=composition_result.memory_revision_ordinal,
                born_step=request.logical_step,
                channel=0,
            )
        if _test_stop_after == "source":
            raise RuntimeError("forced interruption after committed native new-memory source")
        representation = _publish_new_memory_representation(
            connection, routing_scope, request, composition_result, vector
        )
        return NativeFabricRouteResult(
            True, False, composition_result.memory_eid, request.domain_id,
            (composition_result.runtime_motif_id,), composition_result.memory_object_id,
            composition_result.memory_revision_id, representation.representation_id,
        )

    def _select_private_duplicate(
        self,
        connection: sqlite3.Connection,
        request: NativeFabricRouteRequest,
        routing_scope: NativeFabricRoutingScope,
        vector: np.ndarray,
    ) -> tuple[Any, str | None] | None:
        if request.scope != "private" or not _has_positive_norm(vector):
            return None
        facade = NativeMemoryCompatibilityFacade(connection)
        hits = facade.search_by_embedding(
            legacy_source_namespace_id=routing_scope.runtime_scope.legacy_source_namespace_id,
            embedding=vector,
            dimension=request.embedder_lane.dimension,
            representation_class=request.embedder_lane.representation_class,
            generation=request.embedder_lane.generation,
            derivation_contract_version=request.embedder_lane.derivation_contract_version,
            encoding_id=request.embedder_lane.encoding_id,
            dtype=request.embedder_lane.dtype,
            top_k=3,
            user_id=request.agent_id,
        )
        threshold = float(os.getenv("TORMENT_REINFORCE_SIM_THRESHOLD", "0.92"))
        for hit in hits:
            if hit.raw_score < threshold:
                continue
            if str(hit.payload.get("memory_class", "core")) != request.memory_class:
                continue
            if request.memory_class == "core" and request.contradiction_guard is not None:
                if request.contradiction_guard(request.summary, hit.summary, hit.raw_score):
                    continue
            return hit, _source_channel_for_current_object(connection, hit.object_id)
        return None


def _publish_new_memory_representation(
    connection: sqlite3.Connection,
    routing_scope: NativeFabricRoutingScope,
    request: NativeFabricRouteRequest,
    source: Any,
    vector: np.ndarray,
):
    assert request.native_operation_key is not None
    payload = vector.tobytes(order="C")
    representations = NativeRepresentationService(connection)
    pending = representations.create_representation_pending(
        idempotency_namespace_id=routing_scope.idempotency_namespace_id,
        idempotency_key=_new_memory_representation_key(request.native_operation_key, "PENDING"),
        request=RepresentationRequest(
            "OBJECT_REVISION", source.memory_object_id, source.memory_revision_id,
            None, None, request.embedder_lane.representation_class,
            request.embedder_lane.generation,
            request.embedder_lane.derivation_contract_version,
            request.embedder_lane.encoding_id, request.embedder_lane.dtype,
            request.embedder_lane.dimension, (), None, len(payload),
        ),
    )
    representations.establish_representation_integrity_expectation(
        idempotency_namespace_id=routing_scope.idempotency_namespace_id,
        idempotency_key=_new_memory_representation_key(request.native_operation_key, "EXPECTATION"),
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
            hashlib.sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    return representations.publish_representation_ready(
        idempotency_namespace_id=routing_scope.idempotency_namespace_id,
        idempotency_key=_new_memory_representation_key(request.native_operation_key, "READY"),
        request=RepresentationReadyRequest(
            pending.representation_id, request.embedder_lane.representation_class,
            request.embedder_lane.generation,
            request.embedder_lane.derivation_contract_version,
            request.embedder_lane.encoding_id, payload,
        ),
    )


def _translate_route(
    request: NativeFabricRouteRequest,
    routing_scope: NativeFabricRoutingScope,
):
    runtime_scope = routing_scope.runtime_scope
    return translate_fabric_structural(
        FabricStructuralTranslationRequest(
            workspace_id=request.workspace_id,
            scope=request.scope,
            legacy_source_namespace_id=runtime_scope.legacy_source_namespace_id,
            identity_namespace_id=runtime_scope.identity_namespace_id,
            semantic_scope_id=runtime_scope.semantic_scope_id,
            provenance=request.provenance,
            governance=request.governance,
            agent_id=request.agent_id if request.scope == "private" else None,
            domain_id=request.domain_id if request.scope == "shared" else None,
            raw_links=request.raw_links,
            qualified_link_targets=request.qualified_link_targets,
        )
    )


def _synchronize_world_successor(world_runtime: NativeWorldRuntime, source: Any) -> None:
    """Synchronize the process world once R2 is committed, even before E2."""
    world_runtime.synchronize_reinforcement_successor(
        eid=source.eid,
        memory_object_id=source.memory_object_id,
        predecessor_revision_id=source.predecessor_revision_id,
        predecessor_revision_ordinal=source.predecessor_revision_ordinal,
        successor_revision_id=source.revision_id,
        successor_revision_ordinal=source.revision_ordinal,
    )


def _recover_reinforcement_request(
    connection: sqlite3.Connection,
    idempotency_namespace_id: UUID,
    native_operation_key: str,
) -> NativeMemoryReinforcementRequest | None:
    """Recover A3C3's exact R1/E1 witness before doing a new duplicate search."""
    row = connection.execute(
        "SELECT canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
        (
            native_id_to_bytes(idempotency_namespace_id),
            f"NATIVE_REINFORCEMENT:SOURCE:{_reinforcement_base_key(native_operation_key)}",
        ),
    ).fetchone()
    if row is None:
        return None
    try:
        contract = json.loads(row[0])["retry_contract"]
        materialization_intent = contract.get("srg_materialization")
        world_materialization_intent = contract.get("world_diagnostic_materialization")
        return NativeMemoryReinforcementRequest(
            legacy_source_namespace_id=UUID(contract["legacy_source_namespace_id"]),
            eid=int(contract["eid"]),
            expected_revision_id=UUID(contract["expected_revision_id"]),
            expected_representation_id=UUID(contract["expected_representation_id"]),
            idempotency_namespace_id=idempotency_namespace_id,
            idempotency_key=_reinforcement_base_key(native_operation_key),
            reinforcement_step=int(contract["reinforcement_step"]),
            last_reinforced_ts=int(contract["last_reinforced_ts"]),
            expected_dimension=int(contract["expected_dimension"]),
            last_tool_refresh_ts=contract.get("last_tool_refresh_ts"),
            routing_input_digest=contract.get("routing_input_digest"),
            srg_materialization=(
                None if materialization_intent is None
                else SRGSuccessorMaterialization.from_intent(materialization_intent)
            ),
            world_diagnostic_materialization=(
                None if world_materialization_intent is None
                else WorldDiagnosticSuccessorMaterialization.from_intent(
                    world_materialization_intent
                )
            ),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SubstrateInvariantViolation("stored native reinforcement route is malformed") from exc


def _source_channel_for_current_object(connection: sqlite3.Connection, object_id: UUID) -> str | None:
    row = connection.execute(
        """
        SELECT p.source_channel
          FROM objects o
          JOIN object_revisions r
            ON r.object_id=o.object_id
           AND r.object_revision_id=o.current_revision_id
           AND r.revision_ordinal=o.current_revision_ordinal
          JOIN provenance_records p ON p.provenance_id=r.provenance_id
         WHERE o.object_id=?
        """,
        (native_id_to_bytes(object_id),),
    ).fetchone()
    if row is None:
        raise SubstrateInvariantViolation("native duplicate has no current structural provenance")
    return row[0]


def _validate_capability_inputs(
    binding: NativeMemoryRuntimeBinding,
    connection: sqlite3.Connection,
    routing_scopes: tuple[NativeFabricRoutingScope, ...],
    expected_core_id: UUID,
) -> None:
    if not isinstance(binding, NativeMemoryRuntimeBinding):
        raise SubstrateConfigurationError("routing capability requires a prepared native runtime binding")
    if not isinstance(connection, sqlite3.Connection):
        raise SubstrateConfigurationError("routing capability preparation requires a qualified sqlite connection")
    if not isinstance(expected_core_id, UUID):
        raise SubstrateConfigurationError("routing capability expected_core_id must be a UUID")
    if not isinstance(routing_scopes, tuple) or not routing_scopes:
        raise SubstrateConfigurationError("routing capability requires explicit routing scopes")
    if any(not isinstance(scope, NativeFabricRoutingScope) for scope in routing_scopes):
        raise SubstrateConfigurationError("routing scopes must be NativeFabricRoutingScope values")


def _revalidate_capability_for_route(
    capability: NativeFabricRoutingCapability,
    connection: sqlite3.Connection,
) -> None:
    path = _validated_connection_path(connection, capability.core_database_path)
    if path != capability.core_database_path:
        raise SubstrateConfigurationError("native route opened an unexpected core path")
    metadata = require_current_schema(connection)
    if native_id_from_bytes(metadata.core_id) != capability.core_id:
        raise SubstrateConfigurationError("native route core identity changed")
    if metadata.core_role != CORE_ROLE_STAGING:
        raise SubstrateConfigurationError("native route requires a STAGING core")
    deployment = connection.execute(
        "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
    ).fetchall()
    if deployment != [(_LEGACY_ACTIVE_DEPLOYMENT, None)]:
        raise SubstrateConfigurationError("native route deployment is no longer legacy-active")
    _validate_lane(capability.binding.representation_lane)
    _validate_routing_scopes(connection, capability.binding, capability.routing_scopes)


def _validate_routing_scopes(
    connection: sqlite3.Connection,
    binding: NativeMemoryRuntimeBinding,
    routing_scopes: tuple[NativeFabricRoutingScope, ...],
) -> None:
    keys: set[tuple[str, str, str]] = set()
    for scope in routing_scopes:
        if scope.runtime_scope not in binding.scope_bindings:
            raise SubstrateConfigurationError("routing scope is not a prepared binding scope")
        if scope.key in keys:
            raise SubstrateConfigurationError("routing scope collision")
        keys.add(scope.key)
        runtime = scope.runtime_scope
        if runtime.legacy_source_namespace_id == scope.motif_alias_namespace_id:
            raise SubstrateConfigurationError("memory and motif alias namespaces must remain distinct")
        _require_native_id_row(connection, "legacy_source_namespaces", "legacy_source_namespace_id", runtime.legacy_source_namespace_id)
        _require_native_id_row(connection, "identity_namespaces", "identity_namespace_id", runtime.identity_namespace_id)
        _require_native_id_row(connection, "semantic_scopes", "semantic_scope_id", runtime.semantic_scope_id)
        _require_native_id_row(connection, "legacy_source_namespaces", "legacy_source_namespace_id", scope.motif_alias_namespace_id)
        _require_native_id_row(connection, "identity_namespaces", "identity_namespace_id", scope.motif_identity_namespace_id)
        _require_native_id_row(connection, "identity_namespaces", "identity_namespace_id", scope.membership_identity_namespace_id)
        _require_native_id_row(connection, "idempotency_namespaces", "idempotency_namespace_id", scope.idempotency_namespace_id)


def _validated_connection_path(connection: sqlite3.Connection, expected_path: str | Path) -> Path:
    path = Path(expected_path).expanduser().resolve()
    if path.suffix.lower() != ".db" or not path.is_file():
        raise SubstrateConfigurationError("native routing requires an existing .db core")
    rows = connection.execute("PRAGMA database_list").fetchall()
    main_paths = [str(row[2]) for row in rows if row[1] == "main"]
    if len(main_paths) != 1 or not main_paths[0]:
        raise SubstrateConfigurationError("native routing requires a file-backed core connection")
    actual = Path(main_paths[0]).expanduser().resolve()
    if os.path.normcase(str(actual)) != os.path.normcase(str(path)):
        raise SubstrateConfigurationError("native routing connection path does not match the prepared core")
    return path


def _require_native_id_row(connection: sqlite3.Connection, table: str, column: str, value: UUID) -> None:
    row = connection.execute(
        f"SELECT 1 FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)
    ).fetchone()
    if row is None:
        raise SubstrateConfigurationError(f"routing scope references a missing {column}")


def _validate_lane(lane: NativeRepresentationLane) -> None:
    if not isinstance(lane, NativeRepresentationLane):
        raise SubstrateConfigurationError("routing capability requires an explicit representation lane")
    if (
        lane.representation_class,
        lane.generation,
        lane.derivation_contract_version,
        lane.encoding_id,
        lane.dtype,
    ) != ("COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32"):
        raise SubstrateConfigurationError("routing capability supports only the qualified compatibility embedding lane")
    if not isinstance(lane.dimension, int) or isinstance(lane.dimension, bool) or lane.dimension < 1:
        raise SubstrateConfigurationError("routing capability lane dimension must be positive")
    if not isinstance(lane.provider, str) or not lane.provider or not isinstance(lane.model, str) or not lane.model:
        raise SubstrateConfigurationError("routing capability lane provider and model must be non-empty")


def _canonical_vector(value: Any, dimension: int) -> np.ndarray:
    try:
        vector = np.asarray(value, dtype=np.float32).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise ValueError("native route embedding must be numeric float32 data") from exc
    if vector.size != dimension or not np.all(np.isfinite(vector)):
        raise ValueError("native route embedding must be finite and match the qualified dimension")
    return np.ascontiguousarray(vector, dtype=np.float32)


def _has_positive_norm(vector: np.ndarray) -> bool:
    return math.isfinite(float(np.linalg.norm(vector))) and float(np.linalg.norm(vector)) > 0.0


def _routing_input_digest(
    request: NativeFabricRouteRequest,
    routing_scope: NativeFabricRoutingScope,
    vector: np.ndarray,
) -> str:
    """Bind durable A3C3 recovery to the Fabric facts that selected R1/E1."""
    payload = {
        "workspace_id": request.workspace_id,
        "scope": request.scope,
        "agent_id": request.agent_id,
        "domain_id": request.domain_id,
        "routing_scope": {
            "legacy_source_namespace_id": str(routing_scope.runtime_scope.legacy_source_namespace_id),
            "semantic_scope_id": str(routing_scope.runtime_scope.semantic_scope_id),
            "idempotency_namespace_id": str(routing_scope.idempotency_namespace_id),
        },
        "lane": {
            "provider": request.embedder_lane.provider,
            "model": request.embedder_lane.model,
            "dimension": request.embedder_lane.dimension,
            "representation_class": request.embedder_lane.representation_class,
            "generation": request.embedder_lane.generation,
            "derivation_contract_version": request.embedder_lane.derivation_contract_version,
            "encoding_id": request.embedder_lane.encoding_id,
            "dtype": request.embedder_lane.dtype,
        },
        "summary": request.summary,
        "memory_type": request.memory_type,
        "memory_class": request.memory_class,
        "logical_step": request.logical_step,
        "last_reinforced_ts": request.last_reinforced_ts,
        "last_tool_refresh_ts": request.last_tool_refresh_ts,
        "embedding_sha256": hashlib.sha256(vector.tobytes(order="C")).hexdigest(),
        "provenance": request.provenance.to_dict(),
        "governance": request.governance.to_dict(),
        "flexible_payload": dict(request.flexible_payload),
        "raw_links": list(request.raw_links),
        "qualified_link_targets": [
            {
                "legacy_source_namespace_id": str(item.target_legacy_source_namespace_id),
                "eid": item.target_eid,
            }
            for item in request.qualified_link_targets
        ],
    }
    return hashlib.sha256(canonical_intent_text(payload).encode("utf-8")).hexdigest()


def _runtime_scope_key(scope: NativeMemoryRuntimeScope) -> tuple[str, str, str]:
    return (scope.workspace_id, scope.scope_kind, scope.qualifier)


def _request_scope_key(workspace_id: str, scope: str, agent_id: str, domain_id: str) -> tuple[str, str, str]:
    if scope == "private":
        return (workspace_id, _PRIVATE_AGENT_SCOPE, agent_id)
    if scope == "shared":
        return (workspace_id, _SHARED_DOMAIN_SCOPE, domain_id)
    return (workspace_id, "INVALID", "")


def _new_memory_source_key(operation_key: str) -> str:
    return f"NATIVE_FABRIC_NEW_MEMORY:SOURCE:{operation_key}"


def _new_memory_representation_key(operation_key: str, phase: str) -> str:
    return f"NATIVE_FABRIC_NEW_MEMORY:REP_{phase}:{operation_key}"


def _reinforcement_base_key(operation_key: str) -> str:
    return f"NATIVE_FABRIC_REINFORCEMENT:{operation_key}"


__all__ = [
    "NativeFabricMemoryRouter",
    "NativeFabricRouteAttempt",
    "NativeFabricRouteQualification",
    "NativeFabricRouteRequest",
    "NativeFabricRouteResult",
    "NativeFabricRoutingCapability",
    "NativeFabricRoutingScope",
    "NativeMotifProcessOrder",
    "NativeMotifProcessOrderError",
    "prepare_native_fabric_routing_capability",
]
