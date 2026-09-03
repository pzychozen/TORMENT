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
from .native_derived_memory_runtime import (
    NativeDerivedMemoryRuntime,
    NativeDerivedMemoryRuntimeConfiguration,
)
from .native_primary_precommit import (
    NativePrecommitMemoryAbort,
    NativePrecommitMemoryCommit,
    NativePrecommitMemoryReservation,
    NativePrimaryPrecommitService,
)
from .provenance import NativeProvenanceRecord
from .native_world_runtime import (
    NativeWorldProcessState,
    NativeWorldRuntime,
    WorldDiagnosticSuccessorMaterialization,
)
from .motif_runtime_reader import NativeMotifRuntimeReader, NativeRuntimeMotif
from .motifs import NativeMotifService
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
_PRODUCTION_PREPARED = object()


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

    def retire_runtime_id(
        self,
        *,
        routing_scope: NativeFabricRoutingScope,
        domain_id: str,
        runtime_motif_id: str,
    ) -> None:
        """Reconcile one locally retired motif after its committed merge.

        A catalog that has not yet been initialized has no process-local
        ordering to repair.  Once initialized, only the owner that executed
        the native merge may remove the retired ID; the next attach therefore
        observes the same live set instead of treating the committed merge as
        an out-of-band catalog mutation.
        """
        key = (*routing_scope.key, domain_id, routing_scope.motif_alias_namespace_id)
        with self._lock:
            known = self._runtime_ids.get(key)
            if known is None or runtime_motif_id not in known:
                return
            self._runtime_ids[key] = tuple(item for item in known if item != runtime_motif_id)

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
class _NativeProductionRoutingBindingFacts:
    """Minimal active capability facts consumed by existing write adapters."""

    representation_lane: NativeRepresentationLane


@dataclass(frozen=True)
class NativeProductionRoutingCapability:
    """Owner-prepared ACTIVE_CORE capability for bounded production requests.

    This is intentionally not a variant of ``NativeFabricRoutingCapability``:
    the latter stays STAGING-only.  Only the B5 production resource owner
    constructs this private-marker capability after exact agreement recovery.
    It carries no SQLite connection.
    """

    core_database_path: Path
    core_id: UUID
    routing_scopes: tuple[NativeFabricRoutingScope, ...]
    representation_lane: NativeRepresentationLane
    process_order: NativeMotifProcessOrder = field(repr=False, compare=False)
    srg_process_state: NativeSRGProcessState = field(repr=False, compare=False)
    world_process_state: NativeWorldProcessState = field(repr=False, compare=False)
    _prepared_marker: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._prepared_marker is not _PRODUCTION_PREPARED:
            raise SubstrateConfigurationError(
                "production routing capability must be prepared by its resource owner"
            )
        if not isinstance(self.core_database_path, Path) or not isinstance(self.core_id, UUID):
            raise SubstrateConfigurationError("production routing capability core facts are invalid")
        if not isinstance(self.routing_scopes, tuple) or not self.routing_scopes:
            raise SubstrateConfigurationError("production routing capability requires claimed scopes")
        if any(not isinstance(scope, NativeFabricRoutingScope) for scope in self.routing_scopes):
            raise SubstrateConfigurationError("production routing capability scopes are invalid")
        _validate_lane(self.representation_lane)

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

    @property
    def binding(self) -> _NativeProductionRoutingBindingFacts:
        """Compatibility facts only; this is never a STAGING binding/token."""

        return _NativeProductionRoutingBindingFacts(self.representation_lane)


def _prepare_production_routing_capability(
    *,
    core_database_path: Path,
    core_id: UUID,
    routing_scopes: tuple[NativeFabricRoutingScope, ...],
    representation_lane: NativeRepresentationLane,
    process_order: NativeMotifProcessOrder,
    srg_process_state: NativeSRGProcessState,
    world_process_state: NativeWorldProcessState,
) -> NativeProductionRoutingCapability:
    """Construct the active capability for the private production owner only."""

    return NativeProductionRoutingCapability(
        core_database_path=core_database_path,
        core_id=core_id,
        routing_scopes=routing_scopes,
        representation_lane=representation_lane,
        process_order=process_order,
        srg_process_state=srg_process_state,
        world_process_state=world_process_state,
        _prepared_marker=_PRODUCTION_PREPARED,
    )


@dataclass(frozen=True)
class NativeFabricRouteQualification:
    """Stable, explicit admission outcome for one Fabric-facing route."""

    eligible: bool
    route_scope: NativeFabricRoutingScope | None
    reason_code: str
    production_activation_allowed: bool = False


@dataclass(frozen=True)
class NativePrecommitSymbolStateEffect:
    """Facts an existing external symbol owner needs after motif persistence."""

    workspace_id: str
    agent_id: str
    runtime_motif_id: str
    current_tension: float
    enrichment: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in ("workspace_id", "agent_id", "runtime_motif_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty text")
        if not isinstance(self.enrichment, Mapping):
            raise ValueError("enrichment must be a mapping")
        object.__setattr__(self, "enrichment", MappingProxyType(dict(self.enrichment)))


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
    precommit_spawn_observer: Callable[[int], None] | None = field(
        default=None, repr=False, compare=False
    )
    precommit_symbol_state_owner: Callable[[NativePrecommitSymbolStateEffect], Mapping[str, Any]] | None = field(
        default=None, repr=False, compare=False
    )
    precommit_parity_required: bool = False

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
        if self.precommit_spawn_observer is not None and not callable(self.precommit_spawn_observer):
            raise ValueError("precommit_spawn_observer must be callable when supplied")
        if self.precommit_symbol_state_owner is not None and not callable(self.precommit_symbol_state_owner):
            raise ValueError("precommit_symbol_state_owner must be callable when supplied")
        if type(self.precommit_parity_required) is not bool:
            raise ValueError("precommit_parity_required must be a boolean")


@dataclass(frozen=True)
class NativeFabricRouteResult:
    """Bounded native result; native identities stay internal to the adapter."""

    stored: bool
    reinforced: bool
    eid: int | None
    domain_id: str
    motifs: tuple[str, ...]
    memory_object_id: UUID | None
    memory_revision_id: UUID | None
    representation_id: UUID | None
    primary_outcome: "NativePrimaryOutcomeWitness | None" = None


@dataclass(frozen=True)
class NativePrimaryOutcomeWitness:
    """Recorded primary-write truth; it never selects cognition or storage."""

    scope: str
    attempt_origin: str
    reinforcement_disposition: str
    final_storage_outcome: str
    create_failure_disposition: str
    primary_canonical_state_committed: bool
    qualified_memory_eid: int | None
    qualified_memory_object_id: UUID | None
    qualified_memory_revision_id: UUID | None


class NativePrecommitAttachFailure(RuntimeError):
    """A legacy-equivalent raised attach/create failure with an outcome witness."""

    def __init__(self, witness: NativePrimaryOutcomeWitness) -> None:
        super().__init__("native precommit motif attach/create failed")
        self.witness = witness


class NativePrecommitTrueSplitRefused(RuntimeError):
    """I4B-1 must not silently apply the atomic true-split route."""


@dataclass(frozen=True)
class NativeFabricRouteAttempt:
    qualification: NativeFabricRouteQualification
    result: NativeFabricRouteResult | None = None
    primary_outcome: NativePrimaryOutcomeWitness | None = None


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

    def __init__(
        self,
        capability: NativeFabricRoutingCapability | NativeProductionRoutingCapability,
    ) -> None:
        if not isinstance(capability, (NativeFabricRoutingCapability, NativeProductionRoutingCapability)):
            raise ValueError("a prepared native routing capability is required")
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
        if request.embedder_lane != _capability_representation_lane(self._capability):
            return NativeFabricRouteQualification(False, scope, "EMBEDDER_LANE_MISMATCH")
        try:
            _canonical_vector(request.incoming_embedding, request.embedder_lane.dimension)
        except ValueError:
            return NativeFabricRouteQualification(False, scope, "REPRESENTATION_NOT_QUALIFIED")
        return NativeFabricRouteQualification(True, scope, "QUALIFIED")

    def bind_derived_memory_runtime(
        self,
        connection: sqlite3.Connection,
        *,
        configuration: NativeDerivedMemoryRuntimeConfiguration,
    ) -> NativeDerivedMemoryRuntime:
        """Bind one qualified connection to the closed A3D9 runtime port.

        This is deliberately not a post-write adapter and does not select or
        activate native storage.  It only proves that the already-prepared
        capability owns the native memory/motif read scope and the same
        process-local SRG/world owners needed by the derived boundary.
        """
        if not isinstance(configuration, NativeDerivedMemoryRuntimeConfiguration):
            raise SubstrateConfigurationError("derived runtime requires explicit A3D9 configuration")
        _revalidate_capability_for_route(self._capability, connection)
        scope = self._capability.claimed_scope(
            workspace_id=configuration.workspace_id,
            scope="private",
            agent_id=configuration.agent_id,
            domain_id=configuration.domain_id,
        )
        if scope is None:
            raise SubstrateConfigurationError("derived runtime scope is not claimed")
        if (
            configuration.legacy_source_namespace_id != scope.runtime_scope.legacy_source_namespace_id
            or configuration.memory_identity_namespace_id != scope.runtime_scope.identity_namespace_id
            or configuration.semantic_scope_id != scope.runtime_scope.semantic_scope_id
            or configuration.motif_alias_namespace_id != scope.motif_alias_namespace_id
            or configuration.idempotency_namespace_id != scope.idempotency_namespace_id
        ):
            raise SubstrateConfigurationError("derived runtime configuration does not match claimed native scope")
        return NativeDerivedMemoryRuntime(
            connection,
            configuration=configuration,
            world_process_state=self._capability.world_process_state,
            srg_process_state=self._capability.srg_process_state,
        )

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
            return NativeFabricRouteAttempt(
                qualification, primary_outcome=_refused_primary_outcome(request),
            )
        assert qualification.route_scope is not None
        vector = _canonical_vector(request.incoming_embedding, request.embedder_lane.dimension)
        with open_existing_native_core_connection(self._capability.core_database_path) as opened:
            connection = opened.connection
            try:
                _revalidate_capability_for_route(self._capability, connection)
            except Exception:
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "CORE_NOT_CURRENT"),
                    primary_outcome=_refused_primary_outcome(request),
                )
            try:
                translation = _translate_route(request, qualification.route_scope)
            except (TypeError, ValueError):
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "PROVENANCE_NOT_QUALIFIED"),
                    primary_outcome=_refused_primary_outcome(request),
                )
            if translation.link_classification != ABSENT:
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "LINKS_DEFERRED"),
                    primary_outcome=_refused_primary_outcome(request),
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
                    NativeFabricRouteQualification(False, qualification.route_scope, "PROCESS_ORDER_INVALID"),
                    primary_outcome=_refused_primary_outcome(request),
                )
            except StaleMotifCatalogError:
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "PROCESS_ORDER_INVALID"),
                    primary_outcome=_refused_primary_outcome(request),
                )
            except NativePrecommitTrueSplitRefused:
                # This is a reachable topology, but no source reservation or
                # motif mutation has started.  I4B-2 must qualify its durable
                # precommit failure topology before native activation can use it.
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(
                        False, qualification.route_scope, "TRUE_SPLIT_PENDING_I4B2",
                    ),
                    primary_outcome=_refused_primary_outcome(request),
                )
            except ValueError:
                # Structural translation and A3C2 planning both reject before
                # a source semantic transaction starts.  This remains an
                # explicit native qualification refusal, never a legacy retry.
                return NativeFabricRouteAttempt(
                    NativeFabricRouteQualification(False, qualification.route_scope, "STRUCTURAL_PAYLOAD_REFUSED"),
                    primary_outcome=_refused_primary_outcome(request),
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
                _primary_outcome(
                    request,
                    attempt_origin="INGEST_REINFORCEMENT_ATTEMPT",
                    reinforcement_disposition="REINFORCED",
                    final_storage_outcome="REINFORCED_EXISTING",
                    create_failure_disposition="NONE",
                    committed=True,
                    eid=reinforced.source.eid,
                    object_id=reinforced.source.memory_object_id,
                    revision_id=reinforced.source.revision_id,
                ),
            )

        composition_request = _new_memory_composition_request(
            request, routing_scope, translation, vector,
        )
        composition = NativeMemoryMotifCompositionService(connection)
        precommit = NativePrimaryPrecommitService(connection)
        recovered_primary = (
            precommit.recover_canonical(composition_request)
            if request.precommit_parity_required else None
        )
        if recovered_primary is not None:
            # A completed canonical source must win over a later duplicate
            # search, including after process-local owners are recreated.
            motif_ids = _runtime_motif_ids_for_member(connection, routing_scope, recovered_primary.memory_object_id)
            reader = NativeMotifRuntimeReader(connection)
            with self._capability.process_order.locked_catalog(
                reader=reader, routing_scope=routing_scope, domain_id=request.domain_id,
            ):
                world_runtime.ensure_initialized()
                world_runtime.register_fresh_created(
                    eid=recovered_primary.eid,
                    memory_object_id=recovered_primary.memory_object_id,
                    memory_revision_id=recovered_primary.memory_revision_id,
                    memory_revision_ordinal=recovered_primary.memory_revision_ordinal,
                    born_step=request.logical_step,
                    channel=0,
                )
            if _test_stop_after == "source":
                raise RuntimeError("forced interruption after committed native new-memory source")
            representation = _publish_new_memory_representation(
                connection, routing_scope, request, recovered_primary, vector,
            )
            return NativeFabricRouteResult(
                True, False, recovered_primary.eid, request.domain_id, motif_ids,
                recovered_primary.memory_object_id, recovered_primary.memory_revision_id,
                representation.representation_id,
                _primary_outcome(
                    request,
                    attempt_origin="DIRECT_CREATE_PATH",
                    reinforcement_disposition="NOT_APPLICABLE",
                    final_storage_outcome="CREATED_NEW",
                    create_failure_disposition="NONE",
                    committed=True,
                    eid=recovered_primary.eid,
                    object_id=recovered_primary.memory_object_id,
                    revision_id=recovered_primary.memory_revision_id,
                ),
            )

        recovered_abort = (
            precommit.recover_aborted(composition_request)
            if request.precommit_parity_required else None
        )
        if recovered_abort is not None:
            return _return_recovered_abort(
                connection=connection,
                request=request,
                routing_scope=routing_scope,
                aborted=recovered_abort,
            )

        if not request.precommit_parity_required:
            recovered_composition = composition.recover_committed(composition_request)
            if recovered_composition is not None:
                reader = NativeMotifRuntimeReader(connection)
                with self._capability.process_order.locked_catalog(
                    reader=reader, routing_scope=routing_scope, domain_id=request.domain_id,
                ):
                    world_runtime.ensure_initialized()
                    world_runtime.register_fresh_created(
                        eid=recovered_composition.memory_eid,
                        memory_object_id=recovered_composition.memory_object_id,
                        memory_revision_id=recovered_composition.memory_revision_id,
                        memory_revision_ordinal=recovered_composition.memory_revision_ordinal,
                        born_step=request.logical_step,
                        channel=0,
                    )
                if _test_stop_after == "source":
                    raise RuntimeError("forced interruption after committed native new-memory source")
                representation = _publish_new_memory_representation(
                    connection, routing_scope, request, recovered_composition, vector,
                )
                return NativeFabricRouteResult(
                    True, False, recovered_composition.memory_eid, request.domain_id,
                    recovered_composition.affected_runtime_motif_ids or (recovered_composition.runtime_motif_id,),
                    recovered_composition.memory_object_id, recovered_composition.memory_revision_id,
                    representation.representation_id,
                    _primary_outcome(
                        request,
                        attempt_origin="DIRECT_CREATE_PATH",
                        reinforcement_disposition="NOT_APPLICABLE",
                        final_storage_outcome="CREATED_NEW",
                        create_failure_disposition="NONE",
                        committed=True,
                        eid=recovered_composition.memory_eid,
                        object_id=recovered_composition.memory_object_id,
                        revision_id=recovered_composition.memory_revision_id,
                    ),
                )

        try:
            hit, source_channel, duplicate_disposition = self._select_private_duplicate(
                connection, request, routing_scope, vector,
            )
        except Exception:
            # Legacy duplicate implementation failures are deliberately not
            # refusals; ordinary CREATE owns the exception-fallthrough path.
            hit, source_channel, duplicate_disposition = None, None, "EXCEPTION_FALLTHROUGH_TO_CREATE"
        if hit is not None:
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
                direct_ingest_provenance_backfill=translation.provenance,
                routing_input_digest=_routing_input_digest(request, routing_scope, vector),
                srg_materialization=materialization,
                world_diagnostic_materialization=world_materialization,
            )
            try:
                reinforced = NativeMemoryReinforcementService(connection).reinforce(
                    reinforcement_request,
                    _test_stop_after=_test_stop_after,
                    on_source_committed=lambda source: _synchronize_world_successor(world_runtime, source),
                )
            except Exception:
                # A committed R2 must be recovered/retried, never converted
                # into a second CREATE.  Only a wholly uncommitted duplicate
                # implementation error follows legacy exception fallthrough.
                recovered_after_error = _recover_reinforcement_request(
                    connection, routing_scope.idempotency_namespace_id, request.native_operation_key,
                )
                if recovered_after_error is None:
                    hit, source_channel = None, None
                    duplicate_disposition = "EXCEPTION_FALLTHROUGH_TO_CREATE"
                else:
                    reinforced = NativeMemoryReinforcementService(connection).reinforce(
                        recovered_after_error,
                        _test_stop_after=_test_stop_after,
                        on_source_committed=lambda source: _synchronize_world_successor(world_runtime, source),
                    )
            if hit is not None:
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
                    _primary_outcome(
                        request,
                        attempt_origin="INGEST_REINFORCEMENT_ATTEMPT",
                        reinforcement_disposition="REINFORCED",
                        final_storage_outcome="REINFORCED_EXISTING",
                        create_failure_disposition="NONE",
                        committed=True,
                        eid=reinforced.source.eid,
                        object_id=reinforced.source.memory_object_id,
                        revision_id=reinforced.source.revision_id,
                    ),
                )

        if not request.precommit_parity_required:
            # This is the established I3 native route.  I4B-1 is explicitly
            # qualified by the public-ingest adapter below; keeping the
            # default path intact preserves its R1 -> R2 reinforcement lineage
            # and existing atomic composition contract.
            reader = NativeMotifRuntimeReader(connection)
            with self._capability.process_order.locked_catalog(
                reader=reader, routing_scope=routing_scope, domain_id=request.domain_id,
            ) as ordered_catalog:
                preview = composition.prepare_plan_from_ordered_catalog(
                    composition_request, ordered_catalog
                )
                world_runtime.ensure_initialized()
                composition_result = composition.commit(preview)
                if composition_result.split_child_runtime_motif_id is not None:
                    self._capability.process_order.append_created(
                        routing_scope=routing_scope,
                        domain_id=request.domain_id,
                        runtime_motif_id=composition_result.split_child_runtime_motif_id,
                    )
                elif composition_result.runtime_motif_id not in {
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
                composition_result.affected_runtime_motif_ids or (composition_result.runtime_motif_id,),
                composition_result.memory_object_id, composition_result.memory_revision_id,
                representation.representation_id,
                _primary_outcome(
                    request,
                    attempt_origin="DIRECT_CREATE_PATH",
                    reinforcement_disposition=duplicate_disposition,
                    final_storage_outcome="CREATED_NEW",
                    create_failure_disposition="NONE",
                    committed=True,
                    eid=composition_result.memory_eid,
                    object_id=composition_result.memory_object_id,
                    revision_id=composition_result.memory_revision_id,
                ),
            )

        reader = NativeMotifRuntimeReader(connection)
        with self._capability.process_order.locked_catalog(
            reader=reader, routing_scope=routing_scope, domain_id=request.domain_id,
        ) as ordered_catalog:
            preview = composition.prepare_plan_from_ordered_catalog(
                composition_request, ordered_catalog
            )
            if preview.split_plan is not None:
                # The I4B-1 precommit route reaches this topology.  Its
                # established atomic implementation cannot stand in for the
                # durable precommit residue contract, so refuse before an EID
                # reservation or motif write.  The non-precommit branch above
                # deliberately retains its established atomic split behavior.
                raise NativePrecommitTrueSplitRefused(
                    "true split requires I4B-2 precommit qualification"
                )
            reservation = precommit.reserve(composition_request)
            _observe_precommit_spawn(request, reservation.eid)
            try:
                motif_result = _commit_precommit_motif(
                    connection, composition_request, preview, reservation,
                )
            except Exception as exc:
                attempt_origin = _attempt_origin_for(duplicate_disposition)
                precommit.abort(
                    request=composition_request,
                    reservation=reservation,
                    disposition="PRECOMMIT_MOTIF_ATTACH_FAILURE",
                    attempt_origin=attempt_origin,
                    reinforcement_disposition=duplicate_disposition,
                )
                raise NativePrecommitAttachFailure(
                    _primary_outcome(
                        request,
                        attempt_origin=attempt_origin,
                        reinforcement_disposition=duplicate_disposition,
                        final_storage_outcome="NO_WRITE",
                        create_failure_disposition="PRECOMMIT_MOTIF_ATTACH_FAILURE_RAISED",
                        committed=False,
                        eid=reservation.eid,
                        object_id=reservation.memory_object_id,
                        revision_id=reservation.memory_revision_id,
                    )
                ) from exc
            runtime_motif_id = preview.prospective_motif_state.runtime_motif_id
            if runtime_motif_id not in {
                item.read_model.runtime_motif_id for item in ordered_catalog
            }:
                self._capability.process_order.append_created(
                    routing_scope=routing_scope,
                    domain_id=request.domain_id,
                    runtime_motif_id=runtime_motif_id,
                )
            enrichment_patch = dict(preview.enrichment_patch)
            if request.precommit_symbol_state_owner is not None:
                external_effect = NativePrecommitSymbolStateEffect(
                    workspace_id=request.workspace_id,
                    agent_id=request.agent_id,
                    runtime_motif_id=runtime_motif_id,
                    current_tension=float(preview.primary_field_row.get("tension", 0.0) or 0.0),
                    enrichment=enrichment_patch,
                )
                enrichment_patch = dict(request.precommit_symbol_state_owner(external_effect))
            # Keep the pre-existing world registration boundary unchanged:
            # initialization is immediately before canonical source commit,
            # while registration happens only if that commit returns.
            world_runtime.ensure_initialized()
            try:
                if _test_stop_after == "precommit_canonical_failure":
                    raise RuntimeError("forced canonical primary commit failure")
                committed = precommit.commit(
                    request=composition_request,
                    reservation=reservation,
                    enrichment_patch=enrichment_patch,
                )
            except Exception:
                attempt_origin = _attempt_origin_for(duplicate_disposition)
                precommit.abort(
                    request=composition_request,
                    reservation=reservation,
                    disposition="CANONICAL_FLUSH_FAILURE",
                    attempt_origin=attempt_origin,
                    reinforcement_disposition=duplicate_disposition,
                )
                return NativeFabricRouteResult(
                    False, False, None, request.domain_id, (runtime_motif_id,),
                    None, None, None,
                    _primary_outcome(
                        request,
                        attempt_origin=attempt_origin,
                        reinforcement_disposition=duplicate_disposition,
                        final_storage_outcome="NO_WRITE",
                        create_failure_disposition="CANONICAL_FLUSH_FAILURE_STRUCTURED",
                        committed=False,
                        eid=reservation.eid,
                        object_id=reservation.memory_object_id,
                        revision_id=reservation.memory_revision_id,
                    ),
                )
            world_runtime.register_fresh_created(
                eid=committed.eid,
                memory_object_id=committed.memory_object_id,
                memory_revision_id=committed.memory_revision_id,
                memory_revision_ordinal=committed.memory_revision_ordinal,
                born_step=request.logical_step,
                channel=0,
            )
        if _test_stop_after == "source":
            raise RuntimeError("forced interruption after committed native new-memory source")
        representation = _publish_new_memory_representation(
            connection, routing_scope, request, committed, vector
        )
        return NativeFabricRouteResult(
            True, False, committed.eid, request.domain_id, (runtime_motif_id,),
            committed.memory_object_id, committed.memory_revision_id, representation.representation_id,
            _primary_outcome(
                request,
                attempt_origin=_attempt_origin_for(duplicate_disposition),
                reinforcement_disposition=duplicate_disposition,
                final_storage_outcome="CREATED_NEW",
                create_failure_disposition="NONE",
                committed=True,
                eid=committed.eid,
                object_id=committed.memory_object_id,
                revision_id=committed.memory_revision_id,
            ),
        )

    def _select_private_duplicate(
        self,
        connection: sqlite3.Connection,
        request: NativeFabricRouteRequest,
        routing_scope: NativeFabricRoutingScope,
        vector: np.ndarray,
    ) -> tuple[Any | None, str | None, str]:
        if request.scope != "private" or not _has_positive_norm(vector):
            return None, None, "NOT_APPLICABLE"
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
        semantic_fallthrough = "NOT_APPLICABLE"
        for hit in hits:
            if hit.raw_score < threshold:
                continue
            if str(hit.payload.get("memory_class", "core")) != request.memory_class:
                semantic_fallthrough = "SEMANTIC_FALLTHROUGH_TO_CREATE"
                continue
            if request.memory_class == "core" and request.contradiction_guard is not None:
                if request.contradiction_guard(request.summary, hit.summary, hit.raw_score):
                    semantic_fallthrough = "SEMANTIC_FALLTHROUGH_TO_CREATE"
                    continue
            return hit, _source_channel_for_current_object(connection, hit.object_id), "REINFORCED"
        return None, None, semantic_fallthrough


def _commit_precommit_motif(
    connection: sqlite3.Connection,
    request: NativeMemoryMotifCompositionRequest,
    preview: Any,
    reservation: NativePrecommitMemoryReservation,
) -> Any:
    """Persist only the planned attach/create mutation before primary commit."""
    motifs = NativeMotifService(connection)
    if preview.decision.kind == "CREATE_NEW":
        return motifs.create_motif_with_member(
            idempotency_namespace_id=request.idempotency_namespace_id,
            idempotency_key=f"I4B1:PRECOMMIT_MOTIF:{request.idempotency_key}",
            motif_identity_namespace_id=request.motif_identity_namespace_id,
            membership_identity_namespace_id=request.membership_identity_namespace_id,
            motif_alias_namespace_id=request.motif_alias_namespace_id,
            state=preview.prospective_motif_state,
            member_object_id=reservation.memory_object_id,
        )
    if preview.selected_motif_object_id is None:
        raise SubstrateInvariantViolation("precommit attach has no selected motif")
    selected = next(
        item for item in preview.catalog_witness
        if item.motif_object_id == preview.selected_motif_object_id
    )
    return motifs.add_motif_member(
        idempotency_namespace_id=request.idempotency_namespace_id,
        idempotency_key=f"I4B1:PRECOMMIT_MOTIF:{request.idempotency_key}",
        motif_alias_namespace_id=request.motif_alias_namespace_id,
        membership_identity_namespace_id=request.membership_identity_namespace_id,
        motif_object_id=preview.selected_motif_object_id,
        expected_motif_revision_id=selected.motif_revision_id,
        state=preview.prospective_motif_state,
        member_object_id=reservation.memory_object_id,
    )


def _return_recovered_abort(
    *,
    connection: sqlite3.Connection,
    request: NativeFabricRouteRequest,
    routing_scope: NativeFabricRoutingScope,
    aborted: NativePrecommitMemoryAbort,
) -> NativeFabricRouteResult:
    """Return the original failed-primary truth without redoing precommit work."""
    reservation = aborted.reservation
    motifs = _runtime_motif_ids_for_member(
        connection, routing_scope, reservation.memory_object_id,
    )
    if aborted.disposition == "PRECOMMIT_MOTIF_ATTACH_FAILURE":
        raise NativePrecommitAttachFailure(
            _primary_outcome(
                request,
                attempt_origin=aborted.attempt_origin,
                reinforcement_disposition=aborted.reinforcement_disposition,
                final_storage_outcome="NO_WRITE",
                create_failure_disposition="PRECOMMIT_MOTIF_ATTACH_FAILURE_RAISED",
                committed=False,
                eid=reservation.eid,
                object_id=reservation.memory_object_id,
                revision_id=reservation.memory_revision_id,
            )
        )
    if aborted.disposition != "CANONICAL_FLUSH_FAILURE":
        raise SubstrateInvariantViolation("aborted precommit has an unknown disposition")
    return NativeFabricRouteResult(
        False, False, None, request.domain_id, motifs, None, None, None,
        _primary_outcome(
            request,
            attempt_origin=aborted.attempt_origin,
            reinforcement_disposition=aborted.reinforcement_disposition,
            final_storage_outcome="NO_WRITE",
            create_failure_disposition="CANONICAL_FLUSH_FAILURE_STRUCTURED",
            committed=False,
            eid=reservation.eid,
            object_id=reservation.memory_object_id,
            revision_id=reservation.memory_revision_id,
        ),
    )


def _runtime_motif_ids_for_member(
    connection: sqlite3.Connection,
    routing_scope: NativeFabricRoutingScope,
    member_object_id: UUID,
) -> tuple[str, ...]:
    """Recover only current motif aliases that still contain this source."""
    rows = connection.execute(
        """
        SELECT alias.alias_value
          FROM relationships membership
          JOIN relationship_revisions revision
            ON revision.relationship_id=membership.relationship_id
           AND revision.relationship_revision_id=membership.current_revision_id
           AND revision.revision_ordinal=membership.current_revision_ordinal
          JOIN relationship_revision_endpoints motif_endpoint
            ON motif_endpoint.relationship_revision_id=revision.relationship_revision_id
           AND motif_endpoint.endpoint_ordinal=0 AND motif_endpoint.endpoint_role='MOTIF'
           AND motif_endpoint.binding_mode='IDENTITY'
          JOIN relationship_revision_endpoints member_endpoint
            ON member_endpoint.relationship_revision_id=revision.relationship_revision_id
           AND member_endpoint.endpoint_ordinal=1 AND member_endpoint.endpoint_role='MEMBER'
           AND member_endpoint.binding_mode='IDENTITY'
          JOIN legacy_object_aliases alias
            ON alias.object_id=motif_endpoint.object_id
         WHERE membership.relationship_kind='MOTIF_MEMBERSHIP'
           AND revision.existence_state='EXISTS'
           AND member_endpoint.object_id=?
           AND alias.legacy_source_namespace_id=? AND alias.alias_kind='MOTIF_ID'
         ORDER BY alias.alias_value
        """,
        (
            native_id_to_bytes(member_object_id),
            native_id_to_bytes(routing_scope.motif_alias_namespace_id),
        ),
    ).fetchall()
    return tuple(str(row[0]) for row in rows)


def _observe_precommit_spawn(request: NativeFabricRouteRequest, eid: int) -> None:
    """Run the retained embed-audit observer as best-effort precommit state."""
    observer = request.precommit_spawn_observer
    if observer is None:
        return
    try:
        observer(eid)
    except Exception:
        # The legacy dirty marker is observability-facing best effort.  Its
        # failure neither changes primary truth nor blocks motif persistence.
        return


def _attempt_origin_for(reinforcement_disposition: str) -> str:
    return (
        "INGEST_REINFORCEMENT_ATTEMPT"
        if reinforcement_disposition != "NOT_APPLICABLE" else "DIRECT_CREATE_PATH"
    )


def _primary_outcome(
    request: NativeFabricRouteRequest,
    *,
    attempt_origin: str,
    reinforcement_disposition: str,
    final_storage_outcome: str,
    create_failure_disposition: str,
    committed: bool,
    eid: int | None,
    object_id: UUID | None,
    revision_id: UUID | None,
) -> NativePrimaryOutcomeWitness:
    return NativePrimaryOutcomeWitness(
        scope=request.scope,
        attempt_origin=attempt_origin,
        reinforcement_disposition=reinforcement_disposition,
        final_storage_outcome=final_storage_outcome,
        create_failure_disposition=create_failure_disposition,
        primary_canonical_state_committed=committed,
        qualified_memory_eid=eid,
        qualified_memory_object_id=object_id,
        qualified_memory_revision_id=revision_id,
    )


def _refused_primary_outcome(request: NativeFabricRouteRequest) -> NativePrimaryOutcomeWitness:
    """Record a pre-source refusal without inventing a native memory identity."""
    return _primary_outcome(
        request,
        attempt_origin="DIRECT_CREATE_PATH",
        reinforcement_disposition="NOT_APPLICABLE",
        final_storage_outcome="REFUSED",
        create_failure_disposition="NONE",
        committed=False,
        eid=None,
        object_id=None,
        revision_id=None,
    )


def _new_memory_composition_request(
    request: NativeFabricRouteRequest,
    routing_scope: NativeFabricRoutingScope,
    translation: Any,
    vector: np.ndarray,
) -> NativeMemoryMotifCompositionRequest:
    """Build the one immutable A3C2 input for fresh and recovered routes."""
    assert request.native_operation_key is not None
    return NativeMemoryMotifCompositionRequest(
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
            direct_ingest_provenance_backfill=_provenance_from_intent(
                contract.get("direct_ingest_provenance_backfill")
            ),
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


def _provenance_from_intent(value: Any) -> NativeProvenanceRecord | None:
    """Recover only the typed direct-ingest backfill input from source intent."""
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("stored direct-ingest provenance backfill is malformed")
    return NativeProvenanceRecord(
        origin_kind=value["origin_kind"],
        source_channel=value["source_channel"],
        source_role=value["source_role"],
        derivation_status=value["derivation_status"],
        uncertainty_state=value["uncertainty_state"],
        source_time_ns=value.get("source_time_ns"),
        capture_time_ns=value.get("capture_time_ns"),
        memory_role=value.get("memory_role"),
        descriptive_notes=value.get("descriptive_notes"),
    )


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
    capability: NativeFabricRoutingCapability | NativeProductionRoutingCapability,
    connection: sqlite3.Connection,
) -> None:
    if isinstance(capability, NativeProductionRoutingCapability):
        _revalidate_production_capability_for_route(capability, connection)
        return
    if not isinstance(capability, NativeFabricRoutingCapability):
        raise SubstrateConfigurationError("native route requires a prepared capability")
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


def _revalidate_production_capability_for_route(
    capability: NativeProductionRoutingCapability,
    connection: sqlite3.Connection,
) -> None:
    """Revalidate only ACTIVE_CORE/NATIVE_ACTIVE resource facts.

    Agreement resolution remains the production owner's responsibility; this
    lower-level route guard independently prevents an active capability from
    being used after the core itself leaves its exact durable active state.
    """

    path = _validated_connection_path(connection, capability.core_database_path)
    if path != capability.core_database_path:
        raise SubstrateConfigurationError("production route opened an unexpected core path")
    metadata = require_current_schema(connection)
    if native_id_from_bytes(metadata.core_id) != capability.core_id:
        raise SubstrateConfigurationError("production route core identity changed")
    if metadata.core_role != "ACTIVE_CORE":
        raise SubstrateConfigurationError("production route requires an ACTIVE_CORE")
    deployment = connection.execute(
        "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
    ).fetchall()
    if deployment != [("NATIVE_ACTIVE", native_id_to_bytes(capability.core_id))]:
        raise SubstrateConfigurationError("production route requires NATIVE_ACTIVE deployment")
    _validate_lane(capability.representation_lane)
    _validate_production_routing_scopes(connection, capability.routing_scopes)


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


def _validate_production_routing_scopes(
    connection: sqlite3.Connection,
    routing_scopes: tuple[NativeFabricRoutingScope, ...],
) -> None:
    """Validate recovered active scope facts without constructing a binding."""

    keys: set[tuple[str, str, str]] = set()
    for scope in routing_scopes:
        if scope.key in keys:
            raise SubstrateConfigurationError("production routing scope collision")
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


def _capability_representation_lane(
    capability: NativeFabricRoutingCapability | NativeProductionRoutingCapability,
) -> NativeRepresentationLane:
    if isinstance(capability, NativeFabricRoutingCapability):
        return capability.binding.representation_lane
    return capability.representation_lane


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
    "NativePrecommitAttachFailure",
    "NativePrimaryOutcomeWitness",
    "NativeFabricRoutingCapability",
    "NativeFabricRoutingScope",
    "NativeMotifProcessOrder",
    "NativeMotifProcessOrderError",
    "prepare_native_fabric_routing_capability",
]
