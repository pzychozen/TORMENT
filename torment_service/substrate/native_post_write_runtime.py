"""Explicit STAGING-only composition of the qualified native post-write core.

This is not a Fabric selector.  A caller must prepare a routing capability,
prepare an immutable qualification profile and external side-store bindings,
then explicitly supply the native route result that precedes ``run``.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import logging
import sqlite3
from typing import Any, Callable

from torment_service.post_write_runtime import (
    FabricPostWriteContext,
    FabricPostWriteOutcome,
    FabricPostWriteRuntimePort,
    LegacyFabricPostWriteAdapter,
    LegacyFabricPostWriteDependencies,
    PostWriteStorageOutcome,
    run_bridge_suggestions,
)
from torment_service.motif_geometry_port import NativeMotifGeometryAdapter, NativeScopedMotifGeometryAdapter
from torment_service.motif_maintenance import NativeMotifMaintenanceAdapter

from .connection import open_existing_native_core_connection
from .errors import SubstrateConfigurationError, SubstrateInvariantViolation
from .fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRouteResult,
    NativeFabricRoutingCapability,
    NativeFabricRoutingScope,
    _revalidate_capability_for_route,
)
from .ids import native_id_to_bytes
from .native_memory_runtime_access import NativePostWriteMemoryAccess
from .native_srg_runtime import NativeSRGTransientRuntime
from .native_world_runtime import NativeWorldRuntime
from .native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from .native_character_drift_runtime import (
    NativeCharacterDriftRuntime,
    NativeCharacterDriftRuntimeConfiguration,
)
from .native_character_gravity_runtime import (
    NativeCharacterGravityCorrectionRuntime,
    NativeCharacterGravityCorrectionRuntimeConfiguration,
)
from .motif_runtime_reader import NativeMotifRuntimeReader
from .native_motif_merge_runtime import NativeMotifMergeRuntime
from .runtime_binding import validate_fabric_embedder


class NativePostWriteBehavior(str, Enum):
    QUALIFIED = "QUALIFIED"
    REQUIRED_NOOP = "REQUIRED_NOOP"
    DISABLED_FOR_PROFILE = "DISABLED_FOR_PROFILE"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class NativePostWriteQualificationProfile:
    """Immutable statement of this adapter's supported core semantics."""

    conflict_consumer: NativePostWriteBehavior
    srg: NativePostWriteBehavior
    hivemind: NativePostWriteBehavior
    derived_memory: NativePostWriteBehavior
    world: NativePostWriteBehavior
    proposal: NativePostWriteBehavior
    motif_suggestion_maintenance: NativePostWriteBehavior
    motif_auto_merge: NativePostWriteBehavior
    character: NativePostWriteBehavior
    compression: NativePostWriteBehavior
    deep_memory: NativePostWriteBehavior
    checkpoint: NativePostWriteBehavior
    trajectory_evidence: NativePostWriteBehavior
    bridge_suggestions: NativePostWriteBehavior
    shared_bridge_suggestion: NativePostWriteBehavior
    shared_motif_suggestion_maintenance: NativePostWriteBehavior
    shared_trigger_identity_anchor: NativePostWriteBehavior
    shared_trigger_mood_drift: NativePostWriteBehavior
    shared_hivemind_packet_emission: NativePostWriteBehavior = NativePostWriteBehavior.UNSUPPORTED

    @classmethod
    def core_staging(cls) -> "NativePostWriteQualificationProfile":
        return cls(
            NativePostWriteBehavior.QUALIFIED, NativePostWriteBehavior.QUALIFIED,
            NativePostWriteBehavior.QUALIFIED, NativePostWriteBehavior.QUALIFIED,
            NativePostWriteBehavior.QUALIFIED, NativePostWriteBehavior.QUALIFIED,
            NativePostWriteBehavior.REQUIRED_NOOP, NativePostWriteBehavior.UNSUPPORTED,
            NativePostWriteBehavior.UNSUPPORTED, NativePostWriteBehavior.UNSUPPORTED,
            NativePostWriteBehavior.UNSUPPORTED, NativePostWriteBehavior.DISABLED_FOR_PROFILE,
            NativePostWriteBehavior.DISABLED_FOR_PROFILE, NativePostWriteBehavior.DISABLED_FOR_PROFILE,
            NativePostWriteBehavior.DISABLED_FOR_PROFILE,
            NativePostWriteBehavior.UNSUPPORTED, NativePostWriteBehavior.UNSUPPORTED,
            NativePostWriteBehavior.UNSUPPORTED,
        )

    @classmethod
    def core_staging_with_character(cls) -> "NativePostWriteQualificationProfile":
        """Explicit C1A/C1B staging profile; ``core_staging`` remains frozen."""
        return replace(cls.core_staging(), character=NativePostWriteBehavior.QUALIFIED)

    @classmethod
    def core_staging_with_motif_suggestion_maintenance(cls) -> "NativePostWriteQualificationProfile":
        """Explicit M1 profile; auto-merge remains an unsupported mutation."""
        return replace(
            cls.core_staging(),
            motif_suggestion_maintenance=NativePostWriteBehavior.QUALIFIED,
        )

    @classmethod
    def core_staging_with_motif_merge_maintenance(cls) -> "NativePostWriteQualificationProfile":
        """Explicit M2 staging profile; both qualified motif behaviors are opt-in."""
        return replace(
            cls.core_staging(),
            motif_suggestion_maintenance=NativePostWriteBehavior.QUALIFIED,
            motif_auto_merge=NativePostWriteBehavior.QUALIFIED,
        )

    @classmethod
    def core_staging_with_shared_bridge_suggestion(cls) -> "NativePostWriteQualificationProfile":
        """Explicit B1 profile; shared support remains bridge-only."""
        return replace(
            cls.core_staging(),
            shared_bridge_suggestion=NativePostWriteBehavior.QUALIFIED,
        )

    @classmethod
    def core_staging_with_shared_m1_mood_drift(cls) -> "NativePostWriteQualificationProfile":
        """D1 profile for shared M1 and private-target mood drift only."""
        return replace(
            cls.core_staging_with_motif_merge_maintenance(),
            shared_motif_suggestion_maintenance=NativePostWriteBehavior.QUALIFIED,
            shared_trigger_identity_anchor=NativePostWriteBehavior.REQUIRED_NOOP,
            shared_trigger_mood_drift=NativePostWriteBehavior.QUALIFIED,
        )

    @classmethod
    def core_staging_with_shared_hivemind_packet_emission(cls) -> "NativePostWriteQualificationProfile":
        """D2 profile for the shared-source Hivemind packet boundary only."""
        return replace(
            cls.core_staging(),
            shared_hivemind_packet_emission=NativePostWriteBehavior.QUALIFIED,
        )


@dataclass(frozen=True)
class NativePostWriteExternalDependencies:
    """Existing non-memory owners deliberately retained by the core profile."""

    owner: Any
    workspace: Any
    identity: Any
    agent_key: str
    detect_canon_conflict: Callable[[str, str, float], tuple[bool, float, str]]
    proposal_allowed: Callable[..., bool]
    hivemind_log: logging.Logger
    character_store: Any | None = None
    character_embedder: Any | None = None
    shared_bridge_geometry: NativeMotifGeometryAdapter | None = None
    random_chance: Callable[[float], bool] | None = None


@dataclass(frozen=True)
class NativeSharedTriggerMoodDriftBinding:
    """Explicit private target for a shared-trigger mood-drift operation."""

    target_scope: NativeFabricRoutingScope
    runtime_template: NativeDerivedMemoryRuntimeConfiguration

    def __post_init__(self) -> None:
        if not isinstance(self.target_scope, NativeFabricRoutingScope):
            raise ValueError("target_scope must be NativeFabricRoutingScope")
        if not isinstance(self.runtime_template, NativeDerivedMemoryRuntimeConfiguration):
            raise ValueError("runtime_template must be NativeDerivedMemoryRuntimeConfiguration")


@dataclass(frozen=True)
class NativePostWriteQualificationConfiguration:
    """Explicit external posture; every excluded behavior must be declared."""

    routing_scope: NativeFabricRoutingScope
    profile: NativePostWriteQualificationProfile
    external: NativePostWriteExternalDependencies
    derived_runtime_template: NativeDerivedMemoryRuntimeConfiguration | None
    motif_suggestion_maintenance_required: bool
    persistent_trajectory_evidence_required: bool
    checkpoint_snapshots_required: bool
    bridge_suggestions_required: bool
    deep_memory_required: bool
    shared_bridge_suggestions_required: bool = False
    shared_motif_suggestion_maintenance_required: bool = False
    shared_mood_drift_binding: NativeSharedTriggerMoodDriftBinding | None = None
    shared_hivemind_packet_emission_required: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.routing_scope, NativeFabricRoutingScope):
            raise ValueError("routing_scope must be NativeFabricRoutingScope")
        if not isinstance(self.profile, NativePostWriteQualificationProfile):
            raise ValueError("profile must be NativePostWriteQualificationProfile")
        if not isinstance(self.external, NativePostWriteExternalDependencies):
            raise ValueError("external must be NativePostWriteExternalDependencies")
        if self.derived_runtime_template is not None and not isinstance(
            self.derived_runtime_template, NativeDerivedMemoryRuntimeConfiguration,
        ):
            raise ValueError("derived_runtime_template must be NativeDerivedMemoryRuntimeConfiguration or None")
        if self.shared_mood_drift_binding is not None and not isinstance(
            self.shared_mood_drift_binding, NativeSharedTriggerMoodDriftBinding,
        ):
            raise ValueError("shared_mood_drift_binding must be NativeSharedTriggerMoodDriftBinding or None")
        for name in (
            "motif_suggestion_maintenance_required", "persistent_trajectory_evidence_required",
            "checkpoint_snapshots_required", "bridge_suggestions_required", "deep_memory_required",
            "shared_bridge_suggestions_required", "shared_motif_suggestion_maintenance_required",
            "shared_hivemind_packet_emission_required",
        ):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a boolean")


@dataclass(frozen=True)
class NativePostWriteRouteWitness:
    """The native route result and stable parent key preceding one tail run."""

    route_result: NativeFabricRouteResult | None
    native_operation_key: str | None

    def __post_init__(self) -> None:
        if self.route_result is not None and not isinstance(self.route_result, NativeFabricRouteResult):
            raise ValueError("route_result must be NativeFabricRouteResult or None")
        if self.native_operation_key is not None and (
            not isinstance(self.native_operation_key, str) or not self.native_operation_key
        ):
            raise ValueError("native_operation_key must be non-empty when supplied")


_PREPARED = object()


class NativeFabricPostWriteAdapter(FabricPostWriteRuntimePort):
    """A connection-scoped core post-write adapter with no activation authority."""

    def __init__(
        self,
        capability: NativeFabricRoutingCapability,
        configuration: NativePostWriteQualificationConfiguration,
        *,
        _prepared_marker: object | None = None,
    ) -> None:
        if _prepared_marker is not _PREPARED:
            raise SubstrateConfigurationError("native post-write adapter must be explicitly prepared")
        self._capability = capability
        self._configuration = configuration

    def run(
        self,
        context: FabricPostWriteContext,
        *,
        route_witness: NativePostWriteRouteWitness | None = None,
    ) -> FabricPostWriteOutcome:
        if not isinstance(context, FabricPostWriteContext):
            raise ValueError("context must be FabricPostWriteContext")
        witness = route_witness or NativePostWriteRouteWitness(None, None)
        if context.scope == "shared":
            if self._configuration.shared_hivemind_packet_emission_required:
                self._validate_shared_hivemind_pre_effect(context)
                with open_existing_native_core_connection(self._capability.core_database_path) as opened:
                    connection = opened.connection
                    _revalidate_capability_for_route(self._capability, connection)
                    self._validate_context_and_route(connection, context, witness)
                    if context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
                        consumers = LegacyFabricPostWriteAdapter(
                            self._bind_shared_hivemind_dependencies(connection)
                        )
                        consumers._run_hivemind(context)
                return FabricPostWriteOutcome()
            if self._configuration.shared_motif_suggestion_maintenance_required:
                self._validate_shared_m1_mood_pre_effect(context)
                with open_existing_native_core_connection(self._capability.core_database_path) as opened:
                    connection = opened.connection
                    _revalidate_capability_for_route(self._capability, connection)
                    self._validate_context_and_route(connection, context, witness)
                    if context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
                        consumers = LegacyFabricPostWriteAdapter(
                            self._bind_shared_m1_mood_dependencies(connection, context, witness)
                        )
                        consumers._run_motif_maintenance_and_anchors(context)
                return FabricPostWriteOutcome()
            self._validate_shared_bridge_pre_effect(context)
            with open_existing_native_core_connection(self._capability.core_database_path) as opened:
                connection = opened.connection
                _revalidate_capability_for_route(self._capability, connection)
                self._validate_context_and_route(connection, context, witness)
                run_bridge_suggestions(
                    context,
                    workspace=self._configuration.external.workspace,
                    random_chance=self._configuration.external.random_chance,
                    geometry=self._configuration.external.shared_bridge_geometry,
                )
            return FabricPostWriteOutcome()
        if context.scope != "private":
            raise SubstrateInvariantViolation("native post-write context has an unsupported scope")
        if self._configuration.routing_scope.runtime_scope.scope_kind != "PRIVATE_AGENT":
            raise SubstrateInvariantViolation("private post-write context does not match claimed native scope")
        self._validate_profile_pre_effect(context)
        with open_existing_native_core_connection(self._capability.core_database_path) as opened:
            connection = opened.connection
            _revalidate_capability_for_route(self._capability, connection)
            self._validate_context_and_route(connection, context, witness)
            deps = self._bind_dependencies(connection, context, witness)
            consumers = LegacyFabricPostWriteAdapter(deps)
            if context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
                consumers._run_contradiction_surface(context)
                consumers._run_srg_collision(context)
                consumers._run_hivemind(context)
                if self._configuration.motif_suggestion_maintenance_required:
                    consumers._run_motif_maintenance_and_anchors(context)
                else:
                    consumers._run_derived_memory(context)
            consumers._run_world_step(context)
            consumers._run_character_drift(context)
            proposal_id = consumers._run_proposal(context)
            return FabricPostWriteOutcome(proposal_id=proposal_id)

    def _bind_dependencies(
        self,
        connection: sqlite3.Connection,
        context: FabricPostWriteContext,
        witness: NativePostWriteRouteWitness,
    ) -> LegacyFabricPostWriteDependencies:
        scope = self._configuration.routing_scope
        runtime_scope = scope.runtime_scope
        memory = NativePostWriteMemoryAccess(
            connection, legacy_source_namespace_id=runtime_scope.legacy_source_namespace_id,
            expected_dimension=self._capability.binding.representation_lane.dimension,
        )
        world = NativeWorldRuntime(
            connection, legacy_source_namespace_id=runtime_scope.legacy_source_namespace_id,
            expected_dimension=self._capability.binding.representation_lane.dimension,
            process_state=self._capability.world_process_state,
        )
        srg = NativeSRGTransientRuntime(
            connection, legacy_source_namespace_id=runtime_scope.legacy_source_namespace_id,
            process_state=self._capability.srg_process_state,
        )
        template = self._configuration.derived_runtime_template
        if template is None:
            raise SubstrateInvariantViolation("private native post-write requires a derived runtime template")
        parent_key = witness.native_operation_key or "NATIVE_POST_WRITE_NO_WRITE"
        derived = NativeFabricMemoryRouter(self._capability).bind_derived_memory_runtime(
            connection,
            configuration=replace(template, parent_native_operation_key=parent_key),
        )
        external = self._configuration.external
        character_drift = None
        character_correction = None
        motif_runtime = None
        if self._configuration.motif_suggestion_maintenance_required:
            data_dir = getattr(external.workspace, "data_dir", None)
            if not isinstance(data_dir, str) or not data_dir:
                raise SubstrateConfigurationError(
                    "native motif suggestion maintenance requires workspace.data_dir"
                )
            motif_runtime = NativeMotifMaintenanceAdapter(
                NativeScopedMotifGeometryAdapter(
                    NativeMotifRuntimeReader(connection),
                    domain_id=context.chosen_domain,
                    motif_alias_namespace_id=scope.motif_alias_namespace_id,
                    semantic_scope_id=runtime_scope.semantic_scope_id,
                    expected_dimension=self._capability.binding.representation_lane.dimension,
                ),
                data_dir=data_dir,
                workspace_id=runtime_scope.workspace_id,
                domain_id=context.chosen_domain,
                merge_mutator=(
                    NativeMotifMergeRuntime(
                        connection,
                        routing_scope=scope,
                        domain_id=context.chosen_domain,
                        process_order=self._capability.process_order,
                    )
                    if self._configuration.profile.motif_auto_merge
                    is NativePostWriteBehavior.QUALIFIED else None
                ),
            )
        if self._configuration.profile.character is NativePostWriteBehavior.QUALIFIED:
            embedder = external.character_embedder
            if embedder is None:
                raise SubstrateConfigurationError("Character-qualified post-write requires the caller-owned embedder")
            validate_fabric_embedder(self._capability.binding, embedder)
            seed_id = str(external.identity.seed.get("seed_id", "") or "").strip()
            store = external.character_store
            if store is None:
                raise SubstrateConfigurationError("Character-qualified post-write requires CharacterStore")
            character_drift = NativeCharacterDriftRuntime(
                configuration=NativeCharacterDriftRuntimeConfiguration(
                    workspace_id=scope.runtime_scope.workspace_id,
                    agent_id=scope.runtime_scope.agent_id,
                    seed_id=seed_id,
                    domain_id=template.domain_id,
                    motif_alias_namespace_id=scope.motif_alias_namespace_id,
                    semantic_scope_id=scope.runtime_scope.semantic_scope_id,
                    expected_dimension=self._capability.binding.representation_lane.dimension,
                    character_enabled=bool(getattr(external.owner, "_character_enable", False)),
                    drift_every=int(getattr(external.owner, "_character_drift_every", 1)),
                    embedding_cache_enabled=True,
                ),
                store=store,
                memory_read=memory,
                memory_enumeration=memory,
                motif_reader=NativeMotifRuntimeReader(connection),
            )
            character_correction = NativeCharacterGravityCorrectionRuntime(
                connection,
                configuration=NativeCharacterGravityCorrectionRuntimeConfiguration(
                    workspace_id=scope.runtime_scope.workspace_id,
                    agent_id=scope.runtime_scope.agent_id,
                    domain_id=template.domain_id,
                    parent_native_operation_key=parent_key,
                    routing_scope=scope,
                    representation_lane=self._capability.binding.representation_lane,
                    embedder=embedder,
                ),
                world_process_state=self._capability.world_process_state,
                motif_process_order=self._capability.process_order,
            )
        return LegacyFabricPostWriteDependencies(
            owner=external.owner, workspace=external.workspace, graph=_ForbiddenNativeGraph(),
            world_runtime=world, derived_memory_runtime=derived, memory_access=memory,
            memory_enumeration=memory, srg_runtime=srg,
            embedding_dimension=self._capability.binding.representation_lane.dimension,
            identity=external.identity, motif_registry=None, motif_runtime=motif_runtime,
            model_state=None, kernel_context=None, agent_key=external.agent_key,
            detect_canon_conflict=external.detect_canon_conflict,
            proposal_allowed=external.proposal_allowed,
            random_chance=_forbidden_random_chance,
            save_checkpoint=_forbidden_checkpoint,
            build_motif_summary=_forbidden_checkpoint,
            build_shard_snapshot=_forbidden_checkpoint,
            hivemind_log=external.hivemind_log,
            character_drift_runtime=character_drift,
            character_gravity_runtime=character_correction,
        )

    def _bind_shared_m1_mood_dependencies(
        self,
        connection: sqlite3.Connection,
        context: FabricPostWriteContext,
        witness: NativePostWriteRouteWitness,
    ) -> LegacyFabricPostWriteDependencies:
        """Bind D1's shared M1 source and explicit private mood target only."""
        configuration = self._configuration
        scope = configuration.routing_scope
        binding = configuration.shared_mood_drift_binding
        if binding is None:
            raise SubstrateInvariantViolation("shared D1 post-write requires a private mood-drift binding")
        external = configuration.external
        data_dir = getattr(external.workspace, "data_dir", None)
        if not isinstance(data_dir, str) or not data_dir:
            raise SubstrateConfigurationError("shared motif suggestion maintenance requires workspace.data_dir")
        parent_key = witness.native_operation_key or "NATIVE_POST_WRITE_NO_WRITE"
        derived = NativeFabricMemoryRouter(self._capability).bind_derived_memory_runtime(
            connection,
            configuration=replace(
                binding.runtime_template,
                parent_native_operation_key=parent_key,
            ),
        )
        motif_runtime = NativeMotifMaintenanceAdapter(
            NativeScopedMotifGeometryAdapter(
                NativeMotifRuntimeReader(connection),
                domain_id=context.chosen_domain,
                motif_alias_namespace_id=scope.motif_alias_namespace_id,
                semantic_scope_id=scope.runtime_scope.semantic_scope_id,
                expected_dimension=self._capability.binding.representation_lane.dimension,
            ),
            data_dir=data_dir,
            workspace_id=scope.runtime_scope.workspace_id,
            domain_id=context.chosen_domain,
            merge_mutator=(
                NativeMotifMergeRuntime(
                    connection,
                    routing_scope=scope,
                    domain_id=context.chosen_domain,
                    process_order=self._capability.process_order,
                )
                if configuration.profile.motif_auto_merge is NativePostWriteBehavior.QUALIFIED
                else None
            ),
        )
        forbidden = _ForbiddenNativeGraph()
        return LegacyFabricPostWriteDependencies(
            owner=external.owner, workspace=external.workspace, graph=forbidden,
            world_runtime=forbidden, derived_memory_runtime=derived,
            memory_access=forbidden, memory_enumeration=forbidden, srg_runtime=forbidden,
            embedding_dimension=self._capability.binding.representation_lane.dimension,
            identity=external.identity, motif_registry=None, motif_runtime=motif_runtime,
            model_state=None, kernel_context=None, agent_key=external.agent_key,
            detect_canon_conflict=external.detect_canon_conflict,
            proposal_allowed=external.proposal_allowed,
            random_chance=_forbidden_random_chance,
            save_checkpoint=_forbidden_checkpoint,
            build_motif_summary=_forbidden_checkpoint,
            build_shard_snapshot=_forbidden_checkpoint,
            hivemind_log=external.hivemind_log,
        )

    def _bind_shared_hivemind_dependencies(
        self,
        connection: sqlite3.Connection,
    ) -> LegacyFabricPostWriteDependencies:
        """Bind D2's shared-source Hivemind reader and existing external owners only."""
        scope = self._configuration.routing_scope
        external = self._configuration.external
        forbidden = _ForbiddenNativeGraph()
        memory = NativePostWriteMemoryAccess(
            connection,
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=self._capability.binding.representation_lane.dimension,
        )
        return LegacyFabricPostWriteDependencies(
            owner=external.owner, workspace=external.workspace, graph=forbidden,
            world_runtime=forbidden, derived_memory_runtime=forbidden,
            memory_access=memory, memory_enumeration=forbidden, srg_runtime=forbidden,
            embedding_dimension=self._capability.binding.representation_lane.dimension,
            identity=external.identity, motif_registry=None, motif_runtime=None,
            model_state=None, kernel_context=None, agent_key=external.agent_key,
            detect_canon_conflict=external.detect_canon_conflict,
            proposal_allowed=external.proposal_allowed,
            random_chance=_forbidden_random_chance,
            save_checkpoint=_forbidden_checkpoint,
            build_motif_summary=_forbidden_checkpoint,
            build_shard_snapshot=_forbidden_checkpoint,
            hivemind_log=external.hivemind_log,
        )

    def _validate_context_and_route(
        self,
        connection: sqlite3.Connection,
        context: FabricPostWriteContext,
        witness: NativePostWriteRouteWitness,
    ) -> None:
        scope = self._configuration.routing_scope.runtime_scope
        if scope.scope_kind == "PRIVATE_AGENT":
            template = self._configuration.derived_runtime_template
            matches = (
                template is not None
                and context.workspace_id == scope.workspace_id
                and context.scope == "private"
                and context.agent_id == scope.agent_id
                and context.chosen_domain == template.domain_id
            )
        elif scope.scope_kind == "SHARED_DOMAIN":
            matches = (
                context.workspace_id == scope.workspace_id
                and context.scope == "shared"
                and context.chosen_domain == scope.domain_id
            )
        else:
            matches = False
        if not matches:
            raise SubstrateInvariantViolation("post-write context does not match claimed native scope")
        if context.storage_outcome is PostWriteStorageOutcome.NO_WRITE:
            if context.stored or context.eid is not None or witness.route_result is not None:
                raise SubstrateInvariantViolation("NO_WRITE context must not claim a native storage result")
            return
        result = witness.route_result
        if result is None or witness.native_operation_key is None:
            raise SubstrateInvariantViolation("stored native post-write requires route result and operation key")
        expected_outcome = (
            PostWriteStorageOutcome.REINFORCED_EXISTING if result.reinforced
            else PostWriteStorageOutcome.CREATED_NEW
        )
        if (
            not result.stored or not context.stored or context.storage_outcome is not expected_outcome
            or context.eid != result.eid or context.chosen_domain != result.domain_id
            or tuple(context.motif_ids) != tuple(result.motifs)
        ):
            raise SubstrateInvariantViolation("post-write context disagrees with native route result")
        current = connection.execute(
            """SELECT a.object_id,o.current_revision_id
                 FROM legacy_object_aliases a
                 JOIN objects o ON o.object_id=a.object_id
                WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?""",
            (native_id_to_bytes(scope.legacy_source_namespace_id), str(result.eid)),
        ).fetchall()
        if current != [
            (native_id_to_bytes(result.memory_object_id), native_id_to_bytes(result.memory_revision_id))
        ]:
            raise SubstrateInvariantViolation("native route result is not current native memory truth")
        source_key = (
            f"NATIVE_REINFORCEMENT:SOURCE:NATIVE_FABRIC_REINFORCEMENT:{witness.native_operation_key}"
            if result.reinforced
            else f"NATIVE_FABRIC_NEW_MEMORY:SOURCE:{witness.native_operation_key}"
        )
        source_rows = connection.execute(
            """SELECT o.operation_id
                 FROM operations o
                 JOIN operation_outputs out ON out.operation_id=o.operation_id
                WHERE o.idempotency_namespace_id=? AND o.idempotency_key=?
                  AND out.object_id=? AND out.object_revision_id=?""",
            (
                native_id_to_bytes(self._configuration.routing_scope.idempotency_namespace_id), source_key,
                native_id_to_bytes(result.memory_object_id), native_id_to_bytes(result.memory_revision_id),
            ),
        ).fetchall()
        if len(source_rows) != 1:
            raise SubstrateInvariantViolation("route witness operation key does not own the native result")
        view = NativePostWriteMemoryAccess(
            connection, legacy_source_namespace_id=scope.legacy_source_namespace_id,
            expected_dimension=self._capability.binding.representation_lane.dimension,
        ).get_current(result.eid)
        if view is None or view.memory_class != context.memory_class:
            raise SubstrateInvariantViolation("post-write context disagrees with current native memory")

    def _validate_profile_pre_effect(self, context: FabricPostWriteContext) -> None:
        profile = self._configuration.profile
        ext = self._configuration.external
        owner = ext.owner
        policy = ext.workspace.domain_policies.get(context.chosen_domain, {})
        _require_qualified(profile.conflict_consumer, "conflict consumer")
        _require_qualified(profile.srg, "SRG")
        _require_qualified(profile.hivemind, "Hivemind")
        _require_qualified(profile.derived_memory, "derived memory")
        _require_qualified(profile.world, "world")
        _require_qualified(profile.proposal, "proposal")
        if self._configuration.motif_suggestion_maintenance_required:
            if profile.motif_suggestion_maintenance is not NativePostWriteBehavior.QUALIFIED:
                _refuse(profile.motif_suggestion_maintenance, "motif suggestion maintenance")
        if bool(policy.get("auto_merge_motifs", False)):
            _refuse(profile.motif_auto_merge, "motif auto-merge")
        character_due = bool(getattr(owner, "_character_enable", False)) and context.stored and (
            int(context.step) > 0 and int(context.step) % int(getattr(owner, "_character_drift_every", 1)) == 0
        )
        if character_due and profile.character is not NativePostWriteBehavior.QUALIFIED:
            _refuse(profile.character, "Character drift")
        compression_due = bool(getattr(owner, "_compress_enable", False)) and int(context.step) >= int(getattr(owner, "_compress_min_step", 0))
        if compression_due:
            _refuse(profile.compression, "compression")
        checkpoint_due = bool(getattr(owner, "_checkpoint_enable", False)) and int(context.step) > 0 and (
            int(context.step) % int(getattr(owner, "_checkpoint_interval", 1)) == 0
        )
        if checkpoint_due or self._configuration.checkpoint_snapshots_required:
            _refuse(profile.checkpoint, "checkpoint")
        if self._configuration.persistent_trajectory_evidence_required:
            _refuse(profile.trajectory_evidence, "trajectory evidence")
        if self._configuration.bridge_suggestions_required:
            _refuse(profile.bridge_suggestions, "bridge suggestions")
        if self._configuration.deep_memory_required:
            _refuse(profile.deep_memory, "deep memory")

    def _validate_shared_bridge_pre_effect(self, context: FabricPostWriteContext) -> None:
        configuration = self._configuration
        external = configuration.external
        if configuration.routing_scope.runtime_scope.scope_kind != "SHARED_DOMAIN":
            raise SubstrateInvariantViolation("shared post-write requires a claimed shared native scope")
        if not configuration.shared_bridge_suggestions_required:
            raise SubstrateConfigurationError("shared bridge suggestion capability is not required by this profile")
        _require_qualified(configuration.profile.shared_bridge_suggestion, "shared bridge suggestion")
        if configuration.derived_runtime_template is not None:
            raise SubstrateConfigurationError("shared bridge profile must not bind a derived runtime")
        _require_shared_bridge_geometry(external.shared_bridge_geometry, self._capability)
        if not callable(external.random_chance):
            raise SubstrateConfigurationError("shared bridge profile requires an injected random_chance dependency")

    def _validate_shared_m1_mood_pre_effect(self, context: FabricPostWriteContext) -> None:
        configuration = self._configuration
        scope = configuration.routing_scope
        if scope.runtime_scope.scope_kind != "SHARED_DOMAIN":
            raise SubstrateInvariantViolation("shared post-write requires a claimed shared native scope")
        if configuration.shared_bridge_suggestions_required:
            raise SubstrateConfigurationError("shared D1 M1/mood profile cannot compose B1 bridge suggestions")
        if configuration.derived_runtime_template is not None:
            raise SubstrateConfigurationError("shared D1 M1/mood profile must not bind a source-scope derived runtime")
        _require_qualified(configuration.profile.shared_motif_suggestion_maintenance, "shared motif suggestion maintenance")
        _require_required_noop(configuration.profile.shared_trigger_identity_anchor, "shared trigger identity anchor")
        _require_qualified(configuration.profile.shared_trigger_mood_drift, "shared trigger mood drift")
        policy = configuration.external.workspace.domain_policies.get(context.chosen_domain, {})
        if bool(policy.get("auto_merge_motifs", False)):
            _require_qualified(configuration.profile.motif_auto_merge, "motif auto-merge")
        _validate_shared_mood_drift_binding(self._capability, configuration)

    def _validate_shared_hivemind_pre_effect(self, context: FabricPostWriteContext) -> None:
        configuration = self._configuration
        if configuration.routing_scope.runtime_scope.scope_kind != "SHARED_DOMAIN":
            raise SubstrateInvariantViolation("shared post-write requires a claimed shared native scope")
        if not configuration.shared_hivemind_packet_emission_required:
            raise SubstrateConfigurationError("shared Hivemind packet capability is not required by this profile")
        _require_qualified(configuration.profile.shared_hivemind_packet_emission, "shared Hivemind packet emission")
        if configuration.shared_bridge_suggestions_required:
            raise SubstrateConfigurationError("shared Hivemind and B1 bridge consumers must be prepared separately")
        if configuration.shared_motif_suggestion_maintenance_required or configuration.shared_mood_drift_binding is not None:
            raise SubstrateConfigurationError("shared Hivemind and D1 M1/mood consumers must be prepared separately")
        if configuration.derived_runtime_template is not None:
            raise SubstrateConfigurationError("shared Hivemind profile must not bind a source-scope derived runtime")


def prepare_native_fabric_post_write_adapter(
    *,
    capability: NativeFabricRoutingCapability,
    configuration: NativePostWriteQualificationConfiguration,
) -> NativeFabricPostWriteAdapter:
    """Prepare a staging-only adapter without opening a durable connection."""
    if not isinstance(capability, NativeFabricRoutingCapability):
        raise SubstrateConfigurationError("post-write adapter requires prepared routing capability")
    if not isinstance(configuration, NativePostWriteQualificationConfiguration):
        raise SubstrateConfigurationError("post-write adapter requires explicit qualification configuration")
    if configuration.routing_scope not in capability.routing_scopes:
        raise SubstrateConfigurationError("post-write configuration scope is not prepared by capability")
    scope = configuration.routing_scope
    template = configuration.derived_runtime_template
    if scope.runtime_scope.scope_kind == "PRIVATE_AGENT":
        if template is None:
            raise SubstrateConfigurationError("private post-write configuration requires a derived runtime template")
        if (
            template.workspace_id != scope.runtime_scope.workspace_id
            or template.agent_id != scope.runtime_scope.agent_id
            or template.legacy_source_namespace_id != scope.runtime_scope.legacy_source_namespace_id
            or template.motif_alias_namespace_id != scope.motif_alias_namespace_id
            or template.memory_identity_namespace_id != scope.runtime_scope.identity_namespace_id
            or template.semantic_scope_id != scope.runtime_scope.semantic_scope_id
            or template.idempotency_namespace_id != scope.idempotency_namespace_id
        ):
            raise SubstrateConfigurationError("derived runtime template does not match prepared scope")
    elif scope.runtime_scope.scope_kind == "SHARED_DOMAIN":
        shared_d1 = configuration.shared_motif_suggestion_maintenance_required
        shared_hivemind = configuration.shared_hivemind_packet_emission_required
        shared_consumers = sum((
            bool(configuration.shared_bridge_suggestions_required),
            bool(shared_d1),
            bool(shared_hivemind),
        ))
        if shared_consumers > 1:
            raise SubstrateConfigurationError("shared post-write consumers must be prepared separately")
        if shared_consumers == 0:
            raise SubstrateConfigurationError("shared post-write configuration has no qualified consumer")
        if template is not None:
            raise SubstrateConfigurationError("shared post-write configuration must not bind a source-scope derived runtime")
        if configuration.shared_bridge_suggestions_required:
            _require_qualified(configuration.profile.shared_bridge_suggestion, "shared bridge suggestion")
            _require_shared_bridge_geometry(configuration.external.shared_bridge_geometry, capability)
            if not callable(configuration.external.random_chance):
                raise SubstrateConfigurationError("shared bridge configuration requires an injected random_chance dependency")
        elif shared_d1:
            _require_qualified(configuration.profile.shared_motif_suggestion_maintenance, "shared motif suggestion maintenance")
            _require_required_noop(configuration.profile.shared_trigger_identity_anchor, "shared trigger identity anchor")
            _require_qualified(configuration.profile.shared_trigger_mood_drift, "shared trigger mood drift")
            _validate_shared_mood_drift_binding(capability, configuration)
        else:
            _require_qualified(configuration.profile.shared_hivemind_packet_emission, "shared Hivemind packet emission")
            if configuration.shared_mood_drift_binding is not None:
                raise SubstrateConfigurationError("shared Hivemind configuration must not bind a private mood-drift target")
    else:
        raise SubstrateConfigurationError("post-write configuration has an unsupported runtime scope")
    return NativeFabricPostWriteAdapter(capability, configuration, _prepared_marker=_PREPARED)


class _ForbiddenNativeGraph:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"native post-write adapter accessed forbidden MemoryGraph attribute {name}")


def _forbidden_random_chance(*_args: Any, **_kwargs: Any) -> bool:
    raise AssertionError("native post-write adapter attempted excluded bridge suggestions")


def _forbidden_checkpoint(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("native post-write adapter attempted excluded checkpoint work")


def _require_qualified(value: NativePostWriteBehavior, name: str) -> None:
    if value is not NativePostWriteBehavior.QUALIFIED:
        raise SubstrateConfigurationError(f"native post-write profile does not qualify {name}")


def _refuse(value: NativePostWriteBehavior, name: str) -> None:
    raise SubstrateConfigurationError(
        f"native post-write profile refuses {name} ({value.value}) before effects"
    )


def _require_required_noop(value: NativePostWriteBehavior, name: str) -> None:
    if value is not NativePostWriteBehavior.REQUIRED_NOOP:
        raise SubstrateConfigurationError(f"native post-write profile does not qualify required no-op {name}")


def _validate_shared_mood_drift_binding(
    capability: NativeFabricRoutingCapability,
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    source_scope = configuration.routing_scope
    binding = configuration.shared_mood_drift_binding
    if binding is None:
        raise SubstrateConfigurationError("shared D1 M1/mood configuration requires a private mood-drift binding")
    target = binding.target_scope
    template = binding.runtime_template
    if target not in capability.routing_scopes or target.runtime_scope.scope_kind != "PRIVATE_AGENT":
        raise SubstrateConfigurationError("shared mood-drift target must be an admitted private native scope")
    if (
        template.workspace_id != target.runtime_scope.workspace_id
        or template.agent_id != target.runtime_scope.agent_id
        or template.domain_id != source_scope.runtime_scope.domain_id
        or template.legacy_source_namespace_id != target.runtime_scope.legacy_source_namespace_id
        or template.motif_alias_namespace_id != target.motif_alias_namespace_id
        or template.memory_identity_namespace_id != target.runtime_scope.identity_namespace_id
        or template.semantic_scope_id != target.runtime_scope.semantic_scope_id
        or template.idempotency_namespace_id != target.idempotency_namespace_id
    ):
        raise SubstrateConfigurationError("shared mood-drift binding does not match its private target and shared trigger domain")


def _require_shared_bridge_geometry(
    geometry: NativeMotifGeometryAdapter | None,
    capability: NativeFabricRoutingCapability,
) -> None:
    if not isinstance(geometry, NativeMotifGeometryAdapter):
        raise SubstrateConfigurationError("shared bridge profile requires qualified native multi-scope motif geometry")
    admitted_domains = {
        scope.runtime_scope.domain_id
        for scope in capability.routing_scopes
        if scope.runtime_scope.scope_kind == "SHARED_DOMAIN"
    }
    if set(geometry.domain_ids()) != admitted_domains:
        raise SubstrateConfigurationError("shared bridge geometry does not cover exactly the admitted shared domains")


__all__ = [
    "NativeFabricPostWriteAdapter",
    "NativePostWriteBehavior",
    "NativePostWriteExternalDependencies",
    "NativePostWriteQualificationConfiguration",
    "NativePostWriteQualificationProfile",
    "NativePostWriteRouteWitness",
    "NativeSharedTriggerMoodDriftBinding",
    "prepare_native_fabric_post_write_adapter",
]
