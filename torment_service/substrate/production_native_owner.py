"""B5-A3 private lifecycle owner for an already-qualified active native core.

This module is intentionally not imported by the public application, Fabric,
REST, or MCP.  Its owner can be created only by presenting an exact B5-A2
``NATIVE_AGREEMENT`` and retains no SQLite connection.  SQLite resources live
only within explicit, same-thread query or write contexts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Any
from uuid import UUID

from torment_service.query_read_model import (
    NativeQualifiedQueryReadModel,
    QualifiedDomainGeometry,
    QualifiedQueryHit,
    QualifiedQueryLane,
)
from torment_service.post_write_runtime import FabricPostWriteContext, FabricPostWriteOutcome

from .deployment_core_maintenance import (
    contained_core_path,
    inspect_contained_core_deployment,
    read_root_admission_envelope_record,
    read_root_disposition_execution_receipt,
)
from .connection import open_existing_native_core_connection
from .deployment_selector import (
    read_selector_native_activation_intent,
    resolve_deployment_agreement,
)
from .deployment_types import (
    CoreDeploymentWitness,
    DeploymentResolution,
    DeploymentResolutionMode,
    QualifiedDeploymentProfile,
    RootAdmissionCompletionWitness,
    SelectorState,
)
from .errors import DeploymentAuthorityError
from .fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteAttempt,
    NativeFabricRouteRequest,
    NativeMotifProcessOrder,
    NativeFabricRoutingScope,
    _validate_production_routing_scopes,
    _prepare_production_routing_capability,
)
from .migration.existing_workspace_multi_scope_admission import (
    ExistingWorkspaceMultiScopeAdmissionRefused,
    RecoveredActiveExistingWorkspaceNativeMultiScopeScope,
    RecoveredExistingWorkspaceNativeMultiScopeScope,
    load_existing_workspace_multi_scope_admission_descriptor,
    recover_active_existing_workspace_native_multi_scope_runtime,
)
from .migration.root_scope import RootScopeKey, RootScopeKind
from .root_blocker5_binding import (
    RootAdmissionEnvelopeRecord,
    root_membership_closure_digest,
    root_profile_ref_from_record_payload,
    root_runtime_scope_plan_digest,
)
from .root_profile import verify_root_profile_generation
from .native_srg_runtime import NativeSRGProcessState
from .native_trajectory_evidence_runtime import NativePrivateTrajectoryEvidenceProcessState
from .native_post_write_runtime import (
    NativeFabricPostWriteAdapter,
    NativePostWriteQualificationConfiguration,
    NativePostWriteRouteWitness,
    prepare_native_fabric_post_write_adapter,
)
from .native_world_runtime import NativeWorldProcessState
from .runtime_qualification import (
    QUALIFIED_SQLITE_RUNTIME,
    RuntimeQualificationResult,
    qualify_runtime,
)
from .runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane


_OWNER_PREPARED = object()


class NativeProductionResourceOwnerError(DeploymentAuthorityError):
    """Production-owner authority/lifecycle refusal with no fallback route."""


@dataclass(frozen=True)
class NativeProductionAuthorityFacts:
    """Immutable selector/core/runtime facts retained by one owner lifetime."""

    data_root: Path
    selector_generation: int
    core_id: UUID
    core_database_path: Path
    admission_identity_digest: str
    profile_digest: str
    core_witness: CoreDeploymentWitness
    sqlite_runtime_witness: RuntimeQualificationResult


@dataclass(frozen=True)
class _RootV2WorkspaceDescriptor:
    """Descriptor-shaped, record-derived view for the existing query adapter."""

    admission_identity_digest: str
    payload: dict[str, object]

    @property
    def digest(self) -> str:
        return self.admission_identity_digest


@dataclass(frozen=True)
class _RootV2WorkspaceRuntime:
    """One workspace projection of validated root-v2 recovery evidence."""

    native_core_database_path: Path
    native_core_id: UUID
    workspace_id: str
    representation_lane: NativeRepresentationLane
    descriptor: _RootV2WorkspaceDescriptor
    scopes: tuple[RecoveredActiveExistingWorkspaceNativeMultiScopeScope, ...]

    def lookup_private(self, agent_id: str) -> RecoveredActiveExistingWorkspaceNativeMultiScopeScope:
        return self._lookup("PRIVATE_AGENT", agent_id)

    def lookup_shared(self, domain_id: str) -> RecoveredActiveExistingWorkspaceNativeMultiScopeScope:
        return self._lookup("SHARED_DOMAIN", domain_id)

    def _lookup(
        self, scope_kind: str, qualifier: str,
    ) -> RecoveredActiveExistingWorkspaceNativeMultiScopeScope:
        matches = tuple(
            scope for scope in self.scopes
            if scope.memory_runtime_scope.scope_kind == scope_kind
            and scope.memory_runtime_scope.qualifier == qualifier
        )
        if len(matches) != 1:
            raise NativeProductionResourceOwnerError("root-v2 workspace scope is absent or ambiguous")
        return matches[0]


class NativeProductionResourceOwner:
    """Service-lifetime process owner for one exact active native agreement.

    The owner intentionally holds only frozen facts and process-local state:
    SRG state, world state, and motif ordering.  It never retains a raw
    SQLite connection.  Contexts are registered solely so owner shutdown can
    release their request-owned vector readers deterministically.
    """

    def __init__(
        self,
        *,
        authority_facts: NativeProductionAuthorityFacts,
        effective_profile: QualifiedDeploymentProfile,
        admission_descriptor_path: Path | None,
        character_store: Any | None,
        root_v2_completion: RootAdmissionCompletionWitness | None,
        _prepared_marker: object,
    ) -> None:
        if _prepared_marker is not _OWNER_PREPARED:
            raise NativeProductionResourceOwnerError(
                "production native owner requires an exact native agreement"
            )
        self._authority_facts = authority_facts
        self._effective_profile = effective_profile
        self._admission_descriptor_path = admission_descriptor_path
        self._character_store = character_store
        self._root_v2_completion = root_v2_completion
        self._root_workspace_views: dict[str, _RootV2WorkspaceRuntime] = {}
        self._srg_process_state = NativeSRGProcessState()
        self._world_process_state = NativeWorldProcessState()
        self._private_trajectory_evidence_process_state = NativePrivateTrajectoryEvidenceProcessState()
        self._motif_process_order = NativeMotifProcessOrder()
        self._contexts: set[_NativeProductionContext] = set()
        self._closed = False

    @classmethod
    def from_native_agreement(
        cls,
        *,
        data_root: str | Path,
        effective_profile: QualifiedDeploymentProfile,
        agreement: DeploymentResolution,
        admission_descriptor_path: str | Path | None = None,
        character_store: Any | None = None,
    ) -> "NativeProductionResourceOwner":
        """Create an owner only from a fresh exact B5-A2 agreement receipt."""

        if not isinstance(effective_profile, QualifiedDeploymentProfile):
            raise NativeProductionResourceOwnerError("production owner requires QualifiedDeploymentProfile")
        if not effective_profile.is_qualified:
            raise NativeProductionResourceOwnerError("production owner refuses compression or deep-memory profile")
        if not isinstance(agreement, DeploymentResolution):
            raise NativeProductionResourceOwnerError("production owner requires a resolver agreement")
        root = Path(data_root).expanduser().resolve()
        current = _resolve_exact_agreement(root, effective_profile)
        _require_same_agreement(agreement, current)
        state, witness = _native_agreement_parts(current)
        runtime_witness = _qualified_runtime_witness()
        core_path = contained_core_path(
            data_root=root,
            core_relative_path=state.core_relative_path or "",
            require_exists=True,
        )
        inspection = inspect_contained_core_deployment(
            data_root=root,
            core_relative_path=state.core_relative_path or "",
        )
        root_v2_completion = inspection.activation_completion_witness
        descriptor_path: Path | None = None
        if isinstance(root_v2_completion, RootAdmissionCompletionWitness):
            _recover_root_v2_workspace_runtime(
                data_root=root,
                core_path=core_path,
                effective_profile=effective_profile,
                state=state,
                witness=witness,
                completion=root_v2_completion,
                workspace_id=None,
            )
        else:
            if admission_descriptor_path is None:
                raise NativeProductionResourceOwnerError(
                    "v1 production owner requires an admission descriptor"
                )
            descriptor_path = Path(admission_descriptor_path).expanduser().resolve()
            if descriptor_path.is_symlink() or not descriptor_path.is_file():
                raise NativeProductionResourceOwnerError("production owner admission descriptor must be a real file")
            descriptor = load_existing_workspace_multi_scope_admission_descriptor(descriptor_path)
            identity_digest = descriptor.admission_identity_digest
            binding_digest = descriptor.digest if identity_digest is None else identity_digest
            if binding_digest != state.descriptor_digest or descriptor.native_core_id != witness.core_id:
                raise NativeProductionResourceOwnerError("production owner descriptor does not match selected core")
            if identity_digest is not None:
                try:
                    descriptor.completed_admission_witness()
                    recover_active_existing_workspace_native_multi_scope_runtime(
                        data_root=root,
                        agreement=current,
                        admission_descriptor_path=descriptor_path,
                        character_store=character_store,
                    )
                except ExistingWorkspaceMultiScopeAdmissionRefused as exc:
                    raise NativeProductionResourceOwnerError(
                        "production owner completed admission descriptor is refused"
                    ) from exc
            _require_profile_lane(descriptor.representation_lane, effective_profile)
            _require_profile_scope_plan(descriptor, effective_profile)
        facts = NativeProductionAuthorityFacts(
            data_root=root,
            selector_generation=state.generation,
            core_id=witness.core_id,
            core_database_path=core_path,
            admission_identity_digest=state.descriptor_digest or "",
            profile_digest=state.profile_digest or "",
            core_witness=witness,
            sqlite_runtime_witness=runtime_witness,
        )
        return cls(
            authority_facts=facts,
            effective_profile=effective_profile,
            admission_descriptor_path=descriptor_path,
            character_store=character_store,
            root_v2_completion=(
                root_v2_completion
                if isinstance(root_v2_completion, RootAdmissionCompletionWitness)
                else None
            ),
            _prepared_marker=_OWNER_PREPARED,
        )

    @property
    def authority_facts(self) -> NativeProductionAuthorityFacts:
        """Return immutable selected-core facts, never a connection/capability."""

        return self._authority_facts

    @property
    def closed(self) -> bool:
        return self._closed

    def open_query_context(
        self, *, embedder: Any, workspace_id: str | None = None,
    ) -> "NativeProductionQueryContext":
        self._require_open()
        runtime = self._recover_active_runtime(workspace_id=workspace_id)
        model = NativeQualifiedQueryReadModel(
            runtime,
            embedder=embedder,
            srg_process_state=self._srg_process_state,
        )
        context = NativeProductionQueryContext(self, model)
        self._contexts.add(context)
        return context

    def open_write_context(self, *, workspace_id: str | None = None) -> "NativeProductionWriteContext":
        self._require_open()
        runtime = self._recover_active_runtime(workspace_id=workspace_id)
        capability = self._new_routing_capability(runtime)
        context = NativeProductionWriteContext(self, runtime, NativeFabricMemoryRouter(capability))
        self._contexts.add(context)
        return context

    def open_post_write_context(
        self,
        *,
        configuration: NativePostWriteQualificationConfiguration,
    ) -> "NativeProductionPostWriteContext":
        """Open one active-only post-write tail without taking external ownership."""

        self._require_open()
        workspace_id = configuration.routing_scope.runtime_scope.workspace_id
        runtime = self._recover_active_runtime(workspace_id=workspace_id)
        adapter = prepare_native_fabric_post_write_adapter(
            capability=self._new_routing_capability(runtime),
            configuration=configuration,
        )
        context = NativeProductionPostWriteContext(self, runtime, adapter)
        self._contexts.add(context)
        return context

    def close(self) -> None:
        """Close active request resources and discard only in-memory owners."""

        if self._closed:
            return
        self._closed = True
        for context in tuple(self._contexts):
            context.close()
        self._contexts.clear()
        self._root_workspace_views.clear()
        self._private_trajectory_evidence_process_state.close()
        # No SQLite handle exists here.  Dropping these process-only owners is
        # the established restart behavior; durable core truth remains intact.
        self._srg_process_state = None  # type: ignore[assignment]
        self._world_process_state = None  # type: ignore[assignment]
        self._private_trajectory_evidence_process_state = None  # type: ignore[assignment]
        self._motif_process_order = None  # type: ignore[assignment]

    def _discard_context(self, context: "_NativeProductionContext") -> None:
        self._contexts.discard(context)

    def _new_routing_capability(self, runtime: Any) -> Any:
        return _prepare_production_routing_capability(
            core_database_path=runtime.native_core_database_path,
            core_id=runtime.native_core_id,
            routing_scopes=tuple(scope.fabric_routing_scope for scope in runtime.scopes),
            representation_lane=runtime.representation_lane,
            process_order=self._motif_process_order,
            srg_process_state=self._srg_process_state,
            world_process_state=self._world_process_state,
            private_trajectory_evidence_process_state=self._private_trajectory_evidence_process_state,
        )

    def _recover_active_runtime(self, *, workspace_id: str | None = None) -> Any:
        self._require_open()
        agreement = self._revalidate_authority()
        if self._root_v2_completion is not None:
            if not isinstance(workspace_id, str) or not workspace_id:
                raise NativeProductionResourceOwnerError("root-v2 recovery requires an exact workspace identity")
            state, witness = _native_agreement_parts(agreement)
            runtime = _recover_root_v2_workspace_runtime(
                data_root=self._authority_facts.data_root,
                core_path=self._authority_facts.core_database_path,
                effective_profile=self._effective_profile,
                state=state,
                witness=witness,
                completion=self._root_v2_completion,
                workspace_id=workspace_id,
            )
            cached = self._root_workspace_views.get(workspace_id)
            if cached is not None and _same_runtime_shape(cached, runtime):
                return cached
            self._root_workspace_views[workspace_id] = runtime
            return runtime
        try:
            runtime = recover_active_existing_workspace_native_multi_scope_runtime(
                data_root=self._authority_facts.data_root,
                agreement=agreement,
                admission_descriptor_path=self._admission_descriptor_path,  # type: ignore[arg-type]
                character_store=self._character_store,
            )
        except ExistingWorkspaceMultiScopeAdmissionRefused as exc:
            raise NativeProductionResourceOwnerError(
                "production active-core recovery refused"
            ) from exc
        if (
            runtime.native_core_id != self._authority_facts.core_id
            or runtime.native_core_database_path != self._authority_facts.core_database_path
            or (runtime.descriptor.admission_identity_digest or runtime.descriptor.digest)
            != self._authority_facts.admission_identity_digest
        ):
            raise NativeProductionResourceOwnerError("production active recovery changed selected facts")
        _require_profile_lane(runtime.representation_lane, self._effective_profile)
        _require_profile_scope_plan(runtime.descriptor, self._effective_profile)
        return runtime

    def _revalidate_authority(self) -> DeploymentResolution:
        self._require_open()
        current = _resolve_exact_agreement(
            self._authority_facts.data_root,
            self._effective_profile,
        )
        state, witness = _native_agreement_parts(current)
        if (
            state.generation != self._authority_facts.selector_generation
            or state.core_id != self._authority_facts.core_id
            or state.descriptor_digest != self._authority_facts.admission_identity_digest
            or state.profile_digest != self._authority_facts.profile_digest
            or witness != self._authority_facts.core_witness
        ):
            raise NativeProductionResourceOwnerError("stale production owner authority is refused")
        if _qualified_runtime_witness() != self._authority_facts.sqlite_runtime_witness:
            raise NativeProductionResourceOwnerError("production SQLite runtime witness changed")
        return current

    def _require_open(self) -> None:
        if self._closed:
            raise NativeProductionResourceOwnerError("production native owner is closed")


class _NativeProductionContext:
    """Common same-thread and close discipline for request-owned resources."""

    def __init__(self, owner: NativeProductionResourceOwner) -> None:
        self._owner = owner
        self._thread_id = threading.get_ident()
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._close_resources()
        self._closed = True
        self._owner._discard_context(self)

    def __enter__(self):
        self._require_open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _require_open(self) -> None:
        if self._closed:
            raise NativeProductionResourceOwnerError("production native context is closed")
        if threading.get_ident() != self._thread_id:
            raise NativeProductionResourceOwnerError("production native context cannot cross threads")
        self._owner._require_open()

    def _close_resources(self) -> None:
        raise NotImplementedError


class NativeProductionQueryContext(_NativeProductionContext):
    """One request-scoped native query model and its lazily created readers."""

    # This wrapper owns the concrete model's lifetime while retaining its
    # qualified-native, non-materializing read disposition.
    native_read_disposition = True

    def __init__(self, owner: NativeProductionResourceOwner, model: NativeQualifiedQueryReadModel) -> None:
        super().__init__(owner)
        self._model = model

    def private_lane(self, workspace_id: str, agent_id: str) -> QualifiedQueryLane:
        self._require_open()
        return self._model.private_lane(workspace_id, agent_id)

    def shared_lane(self, workspace_id: str, domain_id: str) -> QualifiedQueryLane:
        self._require_open()
        return self._model.shared_lane(workspace_id, domain_id)

    def domain_geometry(self, domain_id: str) -> QualifiedDomainGeometry:
        self._require_open()
        return self._model.domain_geometry(domain_id)

    def active_motifs(self, domain_id: str, top_k: int = 8) -> list[dict[str, Any]]:
        self._require_open()
        return self._model.active_motifs(domain_id, top_k=top_k)

    def domain_ids(self) -> tuple[str, ...]:
        self._require_open()
        return self._model.domain_ids()

    def effective_srg_state(self, hit: QualifiedQueryHit) -> dict[str, Any] | None:
        self._require_open()
        return self._model.effective_srg_state(hit)

    def replace_srg_state(self, hit: QualifiedQueryHit, state: dict[str, Any]) -> None:
        self._require_open()
        self._model.replace_srg_state(hit, state)

    def _close_resources(self) -> None:
        self._model.close()


class NativeProductionWriteContext(_NativeProductionContext):
    """One request-scoped active writer using the established router algorithm."""

    def __init__(self, owner: NativeProductionResourceOwner, runtime: Any, router: NativeFabricMemoryRouter) -> None:
        super().__init__(owner)
        self._runtime = runtime
        self._router = router

    def route(
        self,
        request: NativeFabricRouteRequest,
        *,
        _test_stop_after: str | None = None,
    ) -> NativeFabricRouteAttempt:
        self._require_open()
        # Re-resolve immediately before routing.  Recovery also reloads the
        # descriptor and scope witnesses, so a stale owner cannot mutate using
        # a request-opened capability after an administrative change.
        current = self._owner._recover_active_runtime(workspace_id=self._runtime.workspace_id)
        if not _same_runtime_shape(current, self._runtime):
            raise NativeProductionResourceOwnerError("production write context scope facts became stale")
        return self._router.route(request, _test_stop_after=_test_stop_after)

    def _close_resources(self) -> None:
        # NativeFabricMemoryRouter owns no connection; every route closed its
        # own qualified connection before returning.
        return None


class NativeProductionPostWriteContext(_NativeProductionContext):
    """Request-scoped active tail over caller-owned external dependencies."""

    def __init__(
        self,
        owner: NativeProductionResourceOwner,
        runtime: Any,
        adapter: NativeFabricPostWriteAdapter,
    ) -> None:
        super().__init__(owner)
        self._runtime = runtime
        self._adapter = adapter

    def run(
        self,
        context: FabricPostWriteContext,
        *,
        route_witness: NativePostWriteRouteWitness | None = None,
    ) -> FabricPostWriteOutcome:
        self._require_open()
        current = self._owner._recover_active_runtime(workspace_id=self._runtime.workspace_id)
        if not _same_runtime_shape(current, self._runtime):
            raise NativeProductionResourceOwnerError("production post-write context scope facts became stale")
        return self._adapter.run(context, route_witness=route_witness)

    def _close_resources(self) -> None:
        self._adapter.close()


def _recover_root_v2_workspace_runtime(
    *,
    data_root: Path,
    core_path: Path,
    effective_profile: QualifiedDeploymentProfile,
    state: SelectorState,
    witness: CoreDeploymentWitness,
    completion: RootAdmissionCompletionWitness,
    workspace_id: str | None,
) -> _RootV2WorkspaceRuntime | None:
    """Recover root-v2 solely from native authority evidence, never legacy layout.

    This is intentionally a record-to-runtime adapter, not a second owner or
    completion path.  It opens only the selector-selected native core and
    reconstructs the existing scope wrappers from the P2-frozen plan tuple.
    """

    if (
        completion.native_staging_core_id != witness.core_id
        or completion.root_admission_envelope_digest != state.descriptor_digest
        or completion.qualified_deployment_profile_digest != state.profile_digest
        or witness.descriptor_digest != state.descriptor_digest
        or witness.profile_digest != state.profile_digest
        or state.core_id != witness.core_id
        or state.core_relative_path is None
    ):
        raise NativeProductionResourceOwnerError("root-v2 completion disagrees with selected native authority")
    try:
        record = read_root_admission_envelope_record(
            data_root=data_root,
            core_relative_path=state.core_relative_path,
            root_admission_envelope_digest=completion.root_admission_envelope_digest,
        )
    except DeploymentAuthorityError as exc:
        raise NativeProductionResourceOwnerError("root-v2 envelope evidence is unavailable") from exc
    if not isinstance(record, RootAdmissionEnvelopeRecord):
        raise NativeProductionResourceOwnerError("root-v2 envelope evidence is missing")
    _require_root_v2_record_agreement(
        record=record,
        effective_profile=effective_profile,
        state=state,
        witness=witness,
        completion=completion,
    )
    runtime_scopes = tuple(_runtime_scope_from_root_plan(plan) for plan in record.runtime_scope_plans)
    routing_scopes = tuple(
        NativeFabricRoutingScope(
            runtime_scope=runtime,
            motif_alias_namespace_id=plan.motif_alias_namespace_id,
            motif_identity_namespace_id=plan.motif_identity_namespace_id,
            membership_identity_namespace_id=plan.membership_identity_namespace_id,
            idempotency_namespace_id=plan.idempotency_namespace_id,
        )
        for plan, runtime in zip(record.runtime_scope_plans, runtime_scopes, strict=True)
    )
    root_profile = root_profile_ref_from_record_payload(record.root_profile_payload)
    _require_root_v2_topology(record.runtime_scope_plans)
    try:
        with open_existing_native_core_connection(core_path) as opened:
            current_profile = verify_root_profile_generation(opened.connection, root_profile)
            if current_profile != root_profile:
                raise NativeProductionResourceOwnerError("root-v2 root profile changed during recovery")
            from .runtime_binding import _validate_representation_lane, _validate_scope_bindings

            _validate_representation_lane(record.target_representation_lane)
            _validate_scope_bindings(opened.connection, runtime_scopes)
            _validate_production_routing_scopes(opened.connection, routing_scopes)
            closure = root_membership_closure_digest(
                connection=opened.connection,
                profile=root_profile,
                runtime_scopes=runtime_scopes,
                declared_scope_keys=tuple(_root_scope_key_from_plan(plan) for plan in record.runtime_scope_plans),
            )
    except NativeProductionResourceOwnerError:
        raise
    except Exception as exc:
        raise NativeProductionResourceOwnerError("root-v2 runtime namespace or membership recovery is refused") from exc
    if (
        closure != completion.root_membership_closure_digest
        or closure != record.root_membership_closure_digest
    ):
        raise NativeProductionResourceOwnerError("root-v2 membership closure disagrees with completion evidence")
    try:
        receipt = read_root_disposition_execution_receipt(
            data_root=data_root,
            core_relative_path=state.core_relative_path,
            completion_witness=completion,
        )
        p7_intent = read_selector_native_activation_intent(data_root=data_root)
    except DeploymentAuthorityError as exc:
        raise NativeProductionResourceOwnerError("root-v2 disposition activation evidence is unavailable") from exc
    if (
        receipt is None
        or receipt.root_admission_envelope_digest != completion.root_admission_envelope_digest
        or receipt.native_staging_core_id != completion.native_staging_core_id
        or receipt.geometry_disposition_table_digest != completion.geometry_disposition_table_digest
        or p7_intent.get("disposition_execution_receipt_digest") != receipt.digest
    ):
        raise NativeProductionResourceOwnerError("root-v2 disposition receipt disagrees with P7 activation")
    if workspace_id is None:
        return None
    if not isinstance(workspace_id, str) or not workspace_id:
        raise NativeProductionResourceOwnerError("root-v2 workspace identity is invalid")
    selected = tuple(
        (plan, runtime, routing)
        for plan, runtime, routing in zip(
            record.runtime_scope_plans, runtime_scopes, routing_scopes, strict=True,
        )
        if plan.workspace_id == workspace_id
    )
    if not selected:
        raise NativeProductionResourceOwnerError("root-v2 workspace is not admitted")
    active_scopes = tuple(
        RecoveredActiveExistingWorkspaceNativeMultiScopeScope(
            RecoveredExistingWorkspaceNativeMultiScopeScope(
                core_path,
                witness.core_id,
                record.target_representation_lane,
                runtime,
                routing,
            ),
        )
        for _plan, runtime, routing in selected
    )
    descriptor = _RootV2WorkspaceDescriptor(
        admission_identity_digest=record.envelope_digest,
        payload={
            "lanes": [
                {"plan": {
                    **plan.intent(),
                    "agent_id": plan.agent_id,
                    "domain_id": plan.domain_id,
                }}
                for plan, _runtime, _routing in selected
            ],
        },
    )
    return _RootV2WorkspaceRuntime(
        native_core_database_path=core_path,
        native_core_id=witness.core_id,
        workspace_id=workspace_id,
        representation_lane=record.target_representation_lane,
        descriptor=descriptor,
        scopes=active_scopes,
    )


def _require_root_v2_record_agreement(
    *,
    record: RootAdmissionEnvelopeRecord,
    effective_profile: QualifiedDeploymentProfile,
    state: SelectorState,
    witness: CoreDeploymentWitness,
    completion: RootAdmissionCompletionWitness,
) -> None:
    try:
        stored_profile = QualifiedDeploymentProfile(**record.effective_profile_payload)
    except (TypeError, ValueError, DeploymentAuthorityError) as exc:
        raise NativeProductionResourceOwnerError("root-v2 stored profile is invalid") from exc
    scope_digest = root_runtime_scope_plan_digest(
        record.runtime_scope_plans, record.target_representation_lane,
    )
    envelope = record.envelope_payload
    target_identity = _representation_identity(record.target_representation_lane)
    if (
        stored_profile != effective_profile
        or stored_profile.digest != completion.qualified_deployment_profile_digest
        or stored_profile.admitted_scope_plan_digest != scope_digest
        or envelope.get("root_runtime_scope_plan_digest") != scope_digest
        or envelope.get("qualified_deployment_profile_digest") != stored_profile.digest
        or record.envelope_digest != completion.root_admission_envelope_digest
        or record.envelope_digest != state.descriptor_digest
        or record.envelope_digest != witness.descriptor_digest
        or completion.target_representation_identity != target_identity
        or envelope.get("target_representation_identity") != target_identity
        or completion.data_root_identity != record.root_description_payload.get("data_root_identity")
        or completion.declared_census_digest != envelope.get("declared_census_digest")
        or completion.discovered_census_digest != envelope.get("discovered_census_digest")
        or completion.manifest_digest != envelope.get("manifest_digest")
        or completion.external_owner_observation_digest != envelope.get("external_owner_observation_digest")
        or completion.geometry_disposition_table_digest != envelope.get("geometry_disposition_table_digest")
        or completion.native_staging_core_id != witness.core_id
        or completion.root_writer_freeze_witness_digest
        != _writer_freeze_digest(record.writer_freeze_payload)
    ):
        raise NativeProductionResourceOwnerError("root-v2 envelope record disagrees with completion evidence")
    root_profile = root_profile_ref_from_record_payload(record.root_profile_payload)
    if (
        root_profile.core_id != witness.core_id
        or root_profile.profile_object_id != completion.root_profile_object_id
        or root_profile.profile_revision_id != completion.root_profile_revision_id
        or root_profile.profile_revision_ordinal != completion.root_profile_ordinal
    ):
        raise NativeProductionResourceOwnerError("root-v2 completion root profile disagrees with record")
    _require_profile_lane(record.target_representation_lane, effective_profile)


def _runtime_scope_from_root_plan(plan: Any) -> NativeMemoryRuntimeScope:
    return NativeMemoryRuntimeScope(
        workspace_id=plan.workspace_id,
        scope_kind=plan.scope_kind,
        legacy_source_namespace_id=plan.legacy_source_namespace_id,
        identity_namespace_id=plan.target_identity_namespace_id,
        semantic_scope_id=plan.target_semantic_scope_id,
        agent_id=plan.agent_id,
        domain_id=plan.domain_id,
    )


def _root_scope_key_from_plan(plan: Any) -> RootScopeKey:
    if plan.scope_kind == "PRIVATE_AGENT":
        return RootScopeKey(plan.workspace_id, RootScopeKind.PRIVATE, agent_id=plan.agent_id)
    if plan.scope_kind == "SHARED_DOMAIN":
        return RootScopeKey(plan.workspace_id, RootScopeKind.SHARED, domain_id=plan.domain_id)
    raise NativeProductionResourceOwnerError("root-v2 runtime plan kind is unsupported")


def _require_root_v2_topology(plans: tuple[Any, ...]) -> None:
    by_workspace: dict[str, list[Any]] = {}
    scope_keys: set[tuple[str, str, str]] = set()
    for plan in plans:
        if plan.scope_kind not in {"PRIVATE_AGENT", "SHARED_DOMAIN"}:
            raise NativeProductionResourceOwnerError("root-v2 runtime scope kind is unsupported")
        qualifier = plan.agent_id if plan.scope_kind == "PRIVATE_AGENT" else plan.domain_id
        if not isinstance(qualifier, str) or not qualifier:
            raise NativeProductionResourceOwnerError("root-v2 runtime scope qualifier is invalid")
        key = (plan.workspace_id, plan.scope_kind, qualifier)
        if key in scope_keys:
            raise NativeProductionResourceOwnerError("root-v2 runtime scopes contain duplicate scope identities")
        scope_keys.add(key)
        by_workspace.setdefault(plan.workspace_id, []).append(plan)
    if not by_workspace:
        raise NativeProductionResourceOwnerError("root-v2 admission has no runtime workspaces")
    for workspace_id, workspace_plans in by_workspace.items():
        private_count = sum(plan.scope_kind == "PRIVATE_AGENT" for plan in workspace_plans)
        shared_count = sum(plan.scope_kind == "SHARED_DOMAIN" for plan in workspace_plans)
        # A root-v2 workspace must expose at least one explicitly admitted
        # shared lane.  It may have zero, one, or many private lanes; public
        # agent access remains an exact lookup and never creates one.
        if shared_count < 1:
            raise NativeProductionResourceOwnerError(
                f"root-v2 workspace topology is unsupported for {workspace_id!r}"
            )


def _representation_identity(lane: NativeRepresentationLane) -> str:
    return (
        f"{lane.provider}:{lane.model}:{lane.dimension}:"
        f"{lane.representation_class}"
    )


def _writer_freeze_digest(payload: object) -> str:
    if not isinstance(payload, dict):
        raise NativeProductionResourceOwnerError("root-v2 writer-freeze evidence is malformed")
    from .deployment_types import digest_mapping

    return digest_mapping(payload)


def _resolve_exact_agreement(
    data_root: Path,
    profile: QualifiedDeploymentProfile,
) -> DeploymentResolution:
    try:
        result = resolve_deployment_agreement(
            data_root=data_root,
            effective_profile=profile,
        )
    except DeploymentAuthorityError as exc:
        raise NativeProductionResourceOwnerError("production agreement resolution refused") from exc
    if result.mode is not DeploymentResolutionMode.NATIVE_AGREEMENT:
        raise NativeProductionResourceOwnerError("production owner requires exact NATIVE_AGREEMENT")
    _native_agreement_parts(result)
    return result


def _native_agreement_parts(
    agreement: DeploymentResolution,
) -> tuple[SelectorState, CoreDeploymentWitness]:
    state = agreement.selector_state
    witness = agreement.core_witness
    if (
        state is None
        or witness is None
        or state.core_id is None
        or state.core_relative_path is None
        or state.descriptor_digest is None
        or state.profile_digest is None
        or state.core_witness_digest is None
        or state.core_id != witness.core_id
        or state.descriptor_digest != witness.descriptor_digest
        or state.profile_digest != witness.profile_digest
        or state.core_witness_digest != witness.digest
    ):
        raise NativeProductionResourceOwnerError("native agreement lacks exact selected-core witnesses")
    return state, witness


def _require_same_agreement(expected: DeploymentResolution, actual: DeploymentResolution) -> None:
    if (
        expected.mode is not DeploymentResolutionMode.NATIVE_AGREEMENT
        or expected.selector_state != actual.selector_state
        or expected.core_witness != actual.core_witness
    ):
        raise NativeProductionResourceOwnerError("presented native agreement is stale or non-exact")


def _qualified_runtime_witness() -> RuntimeQualificationResult:
    try:
        witness = qualify_runtime()
    except Exception as exc:
        raise NativeProductionResourceOwnerError("production SQLite runtime is not qualified") from exc
    if (
        not isinstance(witness, RuntimeQualificationResult)
        or not witness.runtime_admissible
        or witness.sqlite_runtime_version != QUALIFIED_SQLITE_RUNTIME
    ):
        raise NativeProductionResourceOwnerError("production SQLite runtime witness is not exact")
    return witness


def _require_profile_lane(
    lane: NativeRepresentationLane,
    profile: QualifiedDeploymentProfile,
) -> None:
    if not isinstance(lane, NativeRepresentationLane) or (
        lane.provider != profile.representation_provider
        or lane.model != profile.representation_model
        or lane.dimension != profile.representation_dimension
    ):
        raise NativeProductionResourceOwnerError("active admission lane disagrees with deployment profile")


def _require_profile_scope_plan(descriptor: Any, profile: QualifiedDeploymentProfile) -> None:
    payload = getattr(descriptor, "payload", None)
    if not isinstance(payload, dict) or payload.get("lane_plan_digest") != profile.admitted_scope_plan_digest:
        raise NativeProductionResourceOwnerError("active admission scopes disagree with deployment profile")


def _same_runtime_shape(left: Any, right: Any) -> bool:
    if (
        left.native_core_id != right.native_core_id
        or left.native_core_database_path != right.native_core_database_path
        or left.descriptor.digest != right.descriptor.digest
        or left.representation_lane != right.representation_lane
    ):
        return False
    return tuple(
        scope.fabric_routing_scope for scope in left.scopes
    ) == tuple(scope.fabric_routing_scope for scope in right.scopes)


__all__ = [
    "NativeProductionAuthorityFacts",
    "NativeProductionQueryContext",
    "NativeProductionPostWriteContext",
    "NativeProductionResourceOwner",
    "NativeProductionResourceOwnerError",
    "NativeProductionWriteContext",
]
