"""Explicit STAGING-only composition of the qualified native post-write core.

This is not a Fabric selector.  A caller must prepare a routing capability,
prepare an immutable qualification profile and external side-store bindings,
then explicitly supply the native route result that precedes ``run``.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import logging
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from typing import Any, Callable

from torment_service.checkpoint import build_motif_summary, build_shard_snapshot, save_checkpoint
from torment_service.post_write_runtime import (
    DerivedMemoryRuntimeContext,
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
    NativeProductionRoutingCapability,
    NativeFabricRoutingScope,
    _revalidate_capability_for_route,
)
from .ids import native_id_to_bytes
from .native_memory_runtime_access import NativePostWriteMemoryAccess
from .native_srg_runtime import NativeSRGTransientRuntime
from .native_world_runtime import NativeWorldRuntime
from .native_trajectory_evidence_runtime import (
    NativeTrajectoryEvidenceRuntime,
    resolve_trajectory_format,
)
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
    shared_trajectory_evidence: NativePostWriteBehavior = NativePostWriteBehavior.UNSUPPORTED
    shared_checkpoint_snapshot: NativePostWriteBehavior = NativePostWriteBehavior.UNSUPPORTED
    shared_compression_disabled_noop: NativePostWriteBehavior = NativePostWriteBehavior.UNSUPPORTED
    shared_trigger_character_noop: NativePostWriteBehavior = NativePostWriteBehavior.UNSUPPORTED
    shared_integrated_default: NativePostWriteBehavior = NativePostWriteBehavior.UNSUPPORTED

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
    def core_staging_with_character_and_motif_merge_maintenance(
        cls,
    ) -> "NativePostWriteQualificationProfile":
        """I4D's explicit private true-split composition profile only."""
        return replace(
            cls.core_staging_with_motif_merge_maintenance(),
            character=NativePostWriteBehavior.QUALIFIED,
        )

    @classmethod
    def core_staging_with_i4e_private_tail(cls) -> "NativePostWriteQualificationProfile":
        """I4E's private SRG/world/trajectory/checkpoint continuation."""
        return replace(
            cls.core_staging_with_character_and_motif_merge_maintenance(),
            checkpoint=NativePostWriteBehavior.QUALIFIED,
            trajectory_evidence=NativePostWriteBehavior.QUALIFIED,
        )

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

    @classmethod
    def core_staging_with_shared_trajectory_evidence(cls) -> "NativePostWriteQualificationProfile":
        """D3 profile for external shared trajectory evidence only."""
        return replace(
            cls.core_staging(),
            shared_trajectory_evidence=NativePostWriteBehavior.QUALIFIED,
        )

    @classmethod
    def core_staging_with_shared_checkpoint_snapshot(cls) -> "NativePostWriteQualificationProfile":
        """D4 profile for one external shared-trigger checkpoint snapshot."""
        return replace(
            cls.core_staging(),
            shared_checkpoint_snapshot=NativePostWriteBehavior.QUALIFIED,
        )

    @classmethod
    def core_staging_with_shared_compression_disabled_noop(cls) -> "NativePostWriteQualificationProfile":
        """D6 profile for a shared trigger while compression is explicitly off."""
        return replace(
            cls.core_staging(),
            shared_compression_disabled_noop=NativePostWriteBehavior.QUALIFIED,
        )

    @classmethod
    def core_staging_with_shared_integrated_default(cls) -> "NativePostWriteQualificationProfile":
        """E1's complete, default-disabled shared post-write composition.

        This intentionally does not widen any predecessor profile.  Callers
        must opt into the one named E1 capability and supply every retained
        external owner/binding it requires.
        """
        return replace(
            cls.core_staging_with_motif_merge_maintenance(),
            shared_bridge_suggestion=NativePostWriteBehavior.QUALIFIED,
            shared_motif_suggestion_maintenance=NativePostWriteBehavior.QUALIFIED,
            shared_trigger_identity_anchor=NativePostWriteBehavior.REQUIRED_NOOP,
            shared_trigger_mood_drift=NativePostWriteBehavior.QUALIFIED,
            shared_hivemind_packet_emission=NativePostWriteBehavior.QUALIFIED,
            shared_trajectory_evidence=NativePostWriteBehavior.QUALIFIED,
            shared_checkpoint_snapshot=NativePostWriteBehavior.QUALIFIED,
            shared_compression_disabled_noop=NativePostWriteBehavior.QUALIFIED,
            shared_trigger_character_noop=NativePostWriteBehavior.QUALIFIED,
            shared_integrated_default=NativePostWriteBehavior.QUALIFIED,
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
class NativeSharedTrajectoryEvidenceBinding:
    """Exact external artifact root and frozen legacy writer selection for D3."""

    artifact_root_dir: str
    trajectory_format: str

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_root_dir, str) or not self.artifact_root_dir:
            raise ValueError("artifact_root_dir must be non-empty text")
        if self.trajectory_format not in {"v2", "legacy"}:
            raise ValueError("trajectory_format must be v2 or legacy")


@dataclass(frozen=True)
class NativeSharedCheckpointSnapshotBinding:
    """Live process objects copied by the external checkpoint writer only."""

    model_state: Any | None
    kernel_runtime_context: Any | None


@dataclass(frozen=True)
class NativePrivateTrajectoryEvidenceBinding:
    """Exact external private artifact root and frozen legacy writer selection."""

    artifact_root_dir: str
    trajectory_format: str

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_root_dir, str) or not self.artifact_root_dir:
            raise ValueError("artifact_root_dir must be non-empty text")
        if self.trajectory_format not in {"v2", "legacy"}:
            raise ValueError("trajectory_format must be v2 or legacy")


@dataclass(frozen=True)
class NativePrivateCheckpointSnapshotBinding:
    """Private caller-owned live state for the existing external writer."""

    model_state: Any | None
    kernel_runtime_context: Any | None


@dataclass(frozen=True)
class _NativeCheckpointMotifProjection:
    """Read-only shape consumed by the existing checkpoint summary builder."""

    motif_id: str
    label: str
    strength: float
    members: range


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
    shared_trajectory_evidence_binding: NativeSharedTrajectoryEvidenceBinding | None = None
    shared_trajectory_evidence_required: bool = False
    shared_checkpoint_snapshot_binding: NativeSharedCheckpointSnapshotBinding | None = None
    shared_checkpoint_snapshot_required: bool = False
    shared_compression_disabled_noop_required: bool = False
    shared_integrated_default_required: bool = False
    private_trajectory_evidence_binding: NativePrivateTrajectoryEvidenceBinding | None = None
    private_checkpoint_snapshot_binding: NativePrivateCheckpointSnapshotBinding | None = None

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
        if self.shared_trajectory_evidence_binding is not None and not isinstance(
            self.shared_trajectory_evidence_binding, NativeSharedTrajectoryEvidenceBinding,
        ):
            raise ValueError(
                "shared_trajectory_evidence_binding must be NativeSharedTrajectoryEvidenceBinding or None"
            )
        if self.shared_checkpoint_snapshot_binding is not None and not isinstance(
            self.shared_checkpoint_snapshot_binding, NativeSharedCheckpointSnapshotBinding,
        ):
            raise ValueError(
                "shared_checkpoint_snapshot_binding must be NativeSharedCheckpointSnapshotBinding or None"
            )
        if self.private_trajectory_evidence_binding is not None and not isinstance(
            self.private_trajectory_evidence_binding, NativePrivateTrajectoryEvidenceBinding,
        ):
            raise ValueError(
                "private_trajectory_evidence_binding must be NativePrivateTrajectoryEvidenceBinding or None"
            )
        if self.private_checkpoint_snapshot_binding is not None and not isinstance(
            self.private_checkpoint_snapshot_binding, NativePrivateCheckpointSnapshotBinding,
        ):
            raise ValueError(
                "private_checkpoint_snapshot_binding must be NativePrivateCheckpointSnapshotBinding or None"
            )
        for name in (
            "motif_suggestion_maintenance_required", "persistent_trajectory_evidence_required",
            "checkpoint_snapshots_required", "bridge_suggestions_required", "deep_memory_required",
            "shared_bridge_suggestions_required", "shared_motif_suggestion_maintenance_required",
            "shared_hivemind_packet_emission_required", "shared_trajectory_evidence_required",
            "shared_checkpoint_snapshot_required", "shared_compression_disabled_noop_required",
            "shared_integrated_default_required",
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


@dataclass(frozen=True)
class NativeSharedIntegratedPostWriteOutcome:
    """E1's post-write result plus the exact READY lanes it reached."""

    outcome: FabricPostWriteOutcome
    ready_routing_scopes: tuple[NativeFabricRoutingScope, ...]
    ready_memory_eids: tuple[tuple[NativeFabricRoutingScope, int], ...]


_PREPARED = object()


class NativeFabricPostWriteAdapter(FabricPostWriteRuntimePort):
    """A connection-scoped core post-write adapter with no activation authority."""

    def __init__(
        self,
        capability: NativeFabricRoutingCapability | NativeProductionRoutingCapability,
        configuration: NativePostWriteQualificationConfiguration,
        *,
        _prepared_marker: object | None = None,
    ) -> None:
        if _prepared_marker is not _PREPARED:
            raise SubstrateConfigurationError("native post-write adapter must be explicitly prepared")
        self._capability = capability
        self._configuration = configuration
        self._shared_trajectory_evidence: NativeTrajectoryEvidenceRuntime | None = None

    def close(self) -> None:
        """Release only request-owned shared evidence without storage authority."""
        runtime = self._shared_trajectory_evidence
        if runtime is not None:
            runtime.close()

    def preflight_shared_integrated_default(self) -> None:
        """Refuse E1 before a direct router can mutate native memory."""
        _validate_shared_integrated_configuration(self._capability, self._configuration)

    def shared_integrated_ready_scopes(
        self,
    ) -> tuple[NativeFabricRoutingScope, NativeFabricRoutingScope]:
        """Return E1's explicit source and derived READY-lane authorities.

        The direct qualification seam uses this narrow declaration to bind its
        process-local vector caches.  It deliberately exposes neither the
        general post-write configuration nor any additional storage authority.
        """
        self.preflight_shared_integrated_default()
        binding = self._configuration.shared_mood_drift_binding
        assert binding is not None  # validated by the E1 preflight above.
        return self._configuration.routing_scope, binding.target_scope

    def run(
        self,
        context: FabricPostWriteContext,
        *,
        route_witness: NativePostWriteRouteWitness | None = None,
    ) -> FabricPostWriteOutcome:
        if not isinstance(context, FabricPostWriteContext):
            raise ValueError("context must be FabricPostWriteContext")
        witness = route_witness or NativePostWriteRouteWitness(None, None)
        if (
            context.scope == "private"
            and witness.route_result is not None
            and witness.route_result.precommit_true_split
        ):
            return self._run_i4b2_true_split_tail(context, witness)
        if context.scope == "shared":
            if self._configuration.shared_integrated_default_required:
                return self.run_shared_integrated_default(context, route_witness=witness).outcome
            if self._configuration.shared_compression_disabled_noop_required:
                self._validate_shared_compression_disabled_pre_effect()
                return FabricPostWriteOutcome()
            if self._configuration.shared_checkpoint_snapshot_required:
                self._validate_shared_checkpoint_pre_effect(context)
                with open_existing_native_core_connection(self._capability.core_database_path) as opened:
                    connection = opened.connection
                    _revalidate_capability_for_route(self._capability, connection)
                    self._validate_context_and_route(connection, context, witness)
                    self._run_shared_checkpoint_snapshot(connection, context)
                return FabricPostWriteOutcome()
            if self._configuration.shared_trajectory_evidence_required:
                self._validate_shared_trajectory_pre_effect(context)
                with open_existing_native_core_connection(self._capability.core_database_path) as opened:
                    connection = opened.connection
                    _revalidate_capability_for_route(self._capability, connection)
                    self._validate_context_and_route(connection, context, witness)
                    if context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
                        self._run_shared_trajectory_evidence(connection, context)
                return FabricPostWriteOutcome()
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
            if self._private_trajectory_evidence_enabled:
                self._run_private_world_and_trajectory(consumers, context)
            else:
                consumers._run_world_step(context)
            consumers._run_character_drift(context)
            if self._private_checkpoint_snapshot_enabled:
                self._run_private_checkpoint_snapshot(connection, context)
            proposal_id = consumers._run_proposal(context)
            return FabricPostWriteOutcome(proposal_id=proposal_id)

    def _run_i4b2_true_split_tail(
        self,
        context: FabricPostWriteContext,
        witness: NativePostWriteRouteWitness,
    ) -> FabricPostWriteOutcome:
        """Run I4C/I4D and opt-in I4E's bounded private true-split tail.

        A true split's child is a structural consequence of an attach route,
        not a public ``created_motif``.  The eligibility gate is therefore
        the primary ``CREATED_NEW`` outcome. I4C restores only the first
        legacy created-memory consumer: the existing external, fail-soft
        contradiction surface. I4D composes mood drift after I4B-2's preserved
        M1/anchor slot. The I4E profile inserts SRG before that slot, then
        world/trajectory before Character and checkpoint after Character.
        Hivemind remains excluded. Reinforcement and ordinary no-write perform
        neither conflict persistence nor true-split created-only work.
        """
        if context.storage_outcome is not PostWriteStorageOutcome.CREATED_NEW:
            return FabricPostWriteOutcome()
        if context.scope != "private":
            raise SubstrateInvariantViolation("I4B-2 true split has an unsupported scope")
        self._validate_i4b2_true_split_tail_pre_effect(context)
        with open_existing_native_core_connection(self._capability.core_database_path) as opened:
            connection = opened.connection
            _revalidate_capability_for_route(self._capability, connection)
            self._validate_context_and_route(connection, context, witness)
            consumers = LegacyFabricPostWriteAdapter(self._bind_dependencies(connection, context, witness))
            consumers._run_contradiction_surface(context)
            if self._private_i4e_enabled:
                consumers._run_srg_collision(context)
            self._run_i4b2_motif_maintenance_and_anchors(consumers, context, emit_anchors=True)
            self._run_i4d_mood_drift(consumers, context)
            if self._private_i4e_enabled:
                self._run_private_world_and_trajectory(consumers, context)
            consumers._run_character_drift(context)
            if self._private_i4e_enabled:
                self._run_private_checkpoint_snapshot(connection, context)
        return FabricPostWriteOutcome()

    @staticmethod
    def _run_i4d_mood_drift(
        consumers: LegacyFabricPostWriteAdapter,
        context: FabricPostWriteContext,
    ) -> None:
        """Retain only the fail-soft mood slot after I4B-2's anchor prefix."""
        deps = consumers._deps
        # The legacy derived slot is reached only through motif maintenance;
        # preserve that predecessor gate instead of granting mood its own
        # independent route when I4B-2 supplied no runtime.
        if deps.motif_runtime is None:
            return
        derived_context = DerivedMemoryRuntimeContext(
            workspace_id=context.workspace_id,
            agent_id=context.agent_id,
            domain_id=context.chosen_domain,
            trigger_scope=context.scope,
            step=int(context.step),
            motif_ids=tuple(context.motif_ids),
            affect_tag=context.affect_tag,
            affect_conf=context.affect_conf,
        )
        try:
            deps.derived_memory_runtime.maybe_emit_mood_drift(derived_context)
        except Exception as exc:
            deps.owner._log.debug("mood drift emission failed: %s", exc)

    @staticmethod
    def _run_i4b2_motif_maintenance_and_anchors(
        consumers: LegacyFabricPostWriteAdapter,
        context: FabricPostWriteContext,
        *,
        emit_anchors: bool,
    ) -> None:
        """Preserve only M1 plus the qualified anchor sub-slots, fail-soft."""
        deps = consumers._deps
        if deps.motif_runtime is None:
            return
        policy = deps.workspace.domain_policies.get(context.chosen_domain, {})
        try:
            deps.motif_runtime.update_entropy_and_suggest(
                target_n=int(policy.get("motif_entropy_target_n", 24)),
                entropy_high=float(policy.get("motif_entropy_high", 0.72)),
                sim_threshold=float(policy.get("motif_merge_similarity", 0.93)),
                max_suggestions=int(policy.get("motif_merge_max_suggestions", 20)),
                auto_merge=bool(policy.get("auto_merge_motifs", False)),
                auto_merge_trigger=float(policy.get("auto_merge_entropy_trigger", 0.80)),
            )
        except Exception as exc:
            deps.owner._log.debug("motif entropy update failed for domain=%s: %s", context.chosen_domain, exc)
        if not emit_anchors:
            return
        derived_context = DerivedMemoryRuntimeContext(
            workspace_id=context.workspace_id,
            agent_id=context.agent_id,
            domain_id=context.chosen_domain,
            trigger_scope=context.scope,
            step=int(context.step),
            motif_ids=tuple(context.motif_ids),
            affect_tag=context.affect_tag,
            affect_conf=context.affect_conf,
        )
        try:
            deps.derived_memory_runtime.maybe_emit_identity_anchor(derived_context)
        except Exception as exc:
            deps.owner._log.debug("identity anchor emission failed: %s", exc)
        try:
            deps.derived_memory_runtime.refine_identity_anchors(derived_context)
        except Exception as exc:
            deps.owner._log.debug("identity anchor refinement failed: %s", exc)

    def _validate_i4b2_true_split_tail_pre_effect(
        self, context: FabricPostWriteContext,
    ) -> None:
        profile = self._configuration.profile
        policy = self._configuration.external.workspace.domain_policies.get(context.chosen_domain, {})
        _require_qualified(profile.conflict_consumer, "conflict consumer")
        _require_qualified(profile.derived_memory, "derived memory")
        _require_qualified(profile.motif_suggestion_maintenance, "motif suggestion maintenance")
        owner = self._configuration.external.owner
        character_due = bool(getattr(owner, "_character_enable", False)) and context.stored and (
            int(context.step) > 0
            and int(context.step) % int(getattr(owner, "_character_drift_every", 1)) == 0
        )
        if character_due and profile.character is not NativePostWriteBehavior.QUALIFIED:
            _refuse(profile.character, "Character drift")
        if bool(policy.get("auto_merge_motifs", False)):
            _require_qualified(profile.motif_auto_merge, "motif auto-merge")
        if self._private_i4e_enabled:
            _require_qualified(profile.srg, "SRG")
            _require_qualified(profile.world, "world")
            _require_qualified(profile.trajectory_evidence, "trajectory evidence")
            _require_qualified(profile.checkpoint, "checkpoint")

    @property
    def _private_i4e_enabled(self) -> bool:
        return self._private_trajectory_evidence_enabled or self._private_checkpoint_snapshot_enabled

    @property
    def _private_trajectory_evidence_enabled(self) -> bool:
        return self._configuration.profile.trajectory_evidence is NativePostWriteBehavior.QUALIFIED

    @property
    def _private_checkpoint_snapshot_enabled(self) -> bool:
        return self._configuration.profile.checkpoint is NativePostWriteBehavior.QUALIFIED

    def _run_private_world_and_trajectory(
        self,
        consumers: LegacyFabricPostWriteAdapter,
        context: FabricPostWriteContext,
    ) -> None:
        """Advance native physics once even when external evidence fails."""
        world = consumers._deps.world_runtime
        if not isinstance(world, NativeWorldRuntime):
            raise SubstrateInvariantViolation("private I4E world binding is not native")
        evidence: NativeTrajectoryEvidenceRuntime | None = None
        try:
            evidence = self._private_trajectory_runtime()
        except Exception as exc:
            self._configuration.external.owner._log.debug(
                "trajectory evidence initialization failed at step=%s for workspace_id=%s agent_id=%s: %s",
                context.step, context.workspace_id, context.agent_id, exc,
            )
        if evidence is not None and context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW and context.eid is not None:
            try:
                world.write_trajectory_genesis_for_post_write(eid=int(context.eid), evidence=evidence)
            except Exception as exc:
                self._configuration.external.owner._log.debug(
                    "trajectory genesis failed at step=%s for eid=%s: %s",
                    context.step, context.eid, exc,
                )
        try:
            if evidence is None:
                world.advance_for_post_write(step=int(context.step))
            else:
                world.advance_for_post_write_with_trajectory_evidence(step=int(context.step), evidence=evidence)
        except Exception as exc:
            self._configuration.external.owner._log.debug(
                "step_world failed at step=%s for workspace_id=%s agent_id=%s: %s",
                context.step, context.workspace_id, context.agent_id, exc,
            )

    def _private_trajectory_runtime(self) -> NativeTrajectoryEvidenceRuntime:
        binding = self._configuration.private_trajectory_evidence_binding
        if binding is None:
            raise SubstrateConfigurationError("private I4E trajectory profile requires an evidence binding")
        scope = self._configuration.routing_scope.runtime_scope
        return self._capability.private_trajectory_evidence_process_state.acquire(
            core_id=self._capability.core_id,
            legacy_source_namespace_id=scope.legacy_source_namespace_id,
            root_dir=binding.artifact_root_dir,
            trajectory_format=binding.trajectory_format,
        )

    def _run_private_checkpoint_snapshot(
        self,
        connection: sqlite3.Connection,
        context: FabricPostWriteContext,
    ) -> None:
        """Run the retained private checkpoint writer after Character, fail-soft."""
        owner = self._configuration.external.owner
        if not (
            owner._checkpoint_enable
            and int(context.step) > 0
            and int(context.step) % owner._checkpoint_interval == 0
        ):
            return
        binding = self._configuration.private_checkpoint_snapshot_binding
        assert binding is not None  # private I4E preflight proves the binding.
        try:
            motif_summary = None
            try:
                motif_summary = self._build_native_checkpoint_motif_summary(connection, context)
            except Exception as exc:
                owner._log.debug("checkpoint motif summary build failed: %s", exc)
            shard_snapshot = None
            try:
                embeddings_dir = (
                    Path(owner.data_dir)
                    / "workspaces" / context.workspace_id / "agents" / context.agent_id
                    / "private" / "embeddings"
                )
                shard_snapshot = build_shard_snapshot(
                    str(embeddings_dir), base_dir=owner.data_dir,
                )
            except Exception as exc:
                owner._log.debug("checkpoint shard manifest build failed: %s", exc)
            character_state = None
            try:
                from dataclasses import asdict

                character_store = self._configuration.external.character_store
                if character_store is not None:
                    state = character_store.load_state(context.workspace_id, context.agent_id)
                    if state:
                        character_state = asdict(state)
            except Exception as exc:
                owner._log.debug("checkpoint character state load failed: %s", exc)
            if binding.kernel_runtime_context is None:
                owner._log.debug("checkpoint skipped: KernelRuntimeContext missing for %s", self._configuration.external.agent_key)
            else:
                save_checkpoint(
                    data_dir=owner.data_dir, workspace_id=context.workspace_id,
                    agent_id=context.agent_id, step=int(context.step),
                    model_state=binding.model_state,
                    corridor_monitor=binding.kernel_runtime_context.mon,
                    kernel_runtime_context=binding.kernel_runtime_context,
                    character_state_dict=character_state, motif_summary=motif_summary,
                    shard_snapshot=shard_snapshot, max_checkpoints=owner._checkpoint_max_keep,
                )
        except Exception as exc:
            owner._log.debug("checkpoint save failed for step=%s: %s", context.step, exc)

    def run_shared_integrated_default(
        self,
        context: FabricPostWriteContext,
        *,
        route_witness: NativePostWriteRouteWitness | None = None,
        on_ready_memory: Callable[[NativeFabricRoutingScope, int], None] | None = None,
    ) -> NativeSharedIntegratedPostWriteOutcome:
        """Execute E1's frozen shared sequence over one explicit route witness."""
        if not isinstance(context, FabricPostWriteContext):
            raise ValueError("context must be FabricPostWriteContext")
        if context.scope != "shared":
            raise SubstrateInvariantViolation("E1 integrated post-write requires a shared context")
        self.preflight_shared_integrated_default()
        witness = route_witness or NativePostWriteRouteWitness(None, None)
        with open_existing_native_core_connection(self._capability.core_database_path) as opened:
            connection = opened.connection
            _revalidate_capability_for_route(self._capability, connection)
            self._validate_context_and_route(connection, context, witness)
            consumers = self._bind_shared_integrated_dependencies(connection, context, witness)
            mood_scope: NativeFabricRoutingScope | None = None
            ready_memory_eids: list[tuple[NativeFabricRoutingScope, int]] = []
            if context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
                assert context.eid is not None
                ready_memory_eids.append((self._configuration.routing_scope, int(context.eid)))
                if on_ready_memory is not None:
                    try:
                        on_ready_memory(self._configuration.routing_scope, int(context.eid))
                    except Exception as exc:
                        self._configuration.external.owner._log.debug(
                            "E1 READY-lane observer failed for eid=%s: %s", context.eid, exc,
                        )
            if context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
                # This is the corrected legacy created-memory order.  The
                # first slot has an explicit shared predicate and is a no-op.
                consumers._run_contradiction_surface(context)
                consumers._run_srg_collision(context)
                consumers._run_hivemind(context)
                mood_eid = self._run_shared_integrated_m1_and_derived(consumers, context)
                if mood_eid is not None:
                    binding = self._configuration.shared_mood_drift_binding
                    assert binding is not None
                    mood_scope = binding.target_scope
                    ready_memory_eids.append((mood_scope, mood_eid))
                    if on_ready_memory is not None:
                        try:
                            on_ready_memory(mood_scope, mood_eid)
                        except Exception as exc:
                            self._configuration.external.owner._log.debug(
                                "E1 READY-lane observer failed for eid=%s: %s", mood_eid, exc,
                            )

            if context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
                self._run_shared_trajectory_evidence(connection, context)
            else:
                consumers._run_world_step(context)
            consumers._run_character_drift(context)
            self._run_shared_checkpoint_snapshot(connection, context)
            # D6 was preflighted above.  Compression is intentionally a real
            # no-op here, before the ordinary shared proposal gate and B1.
            self._run_shared_compression_disabled_noop()
            proposal_id = consumers._run_proposal(context)
            run_bridge_suggestions(
                context,
                workspace=self._configuration.external.workspace,
                random_chance=self._configuration.external.random_chance,
                geometry=self._configuration.external.shared_bridge_geometry,
            )
        scopes = [self._configuration.routing_scope]
        if mood_scope is not None:
            scopes.append(mood_scope)
        return NativeSharedIntegratedPostWriteOutcome(
            FabricPostWriteOutcome(proposal_id=proposal_id), tuple(scopes), tuple(ready_memory_eids),
        )

    def _run_shared_compression_disabled_noop(self) -> None:
        """D6's qualified semantic no-op in E1's exact legacy slot."""
        return None

    def _run_shared_trajectory_evidence(
        self,
        connection: sqlite3.Connection,
        context: FabricPostWriteContext,
    ) -> None:
        """Mirror the legacy V2 birth/step/event boundary for one fresh source.

        This profile deliberately limits itself to ``CREATED_NEW``.  Only that
        route has a fresh source-bound birth step/channel in the process world;
        D3 never invents those facts while rehydrating an older native row.
        """
        try:
            world = NativeWorldRuntime(
                connection,
                legacy_source_namespace_id=(
                    self._configuration.routing_scope.runtime_scope.legacy_source_namespace_id
                ),
                expected_dimension=self._capability.binding.representation_lane.dimension,
                process_state=self._capability.world_process_state,
            )
            evidence = self._shared_trajectory_runtime()
            assert context.eid is not None
            world.write_trajectory_genesis_for_post_write(eid=int(context.eid), evidence=evidence)
            world.advance_for_post_write_with_trajectory_evidence(
                step=int(context.step), evidence=evidence,
            )
        except Exception as exc:
            self._configuration.external.owner._log.debug(
                "step_world failed at step=%s for workspace_id=%s agent_id=%s: %s",
                context.step, context.workspace_id, context.agent_id, exc,
            )

    def _shared_trajectory_runtime(self) -> NativeTrajectoryEvidenceRuntime:
        runtime = self._shared_trajectory_evidence
        if runtime is not None:
            return runtime
        binding = self._configuration.shared_trajectory_evidence_binding
        if binding is None:
            raise SubstrateConfigurationError("shared trajectory profile requires an evidence binding")
        runtime = NativeTrajectoryEvidenceRuntime(
            root_dir=binding.artifact_root_dir,
            trajectory_format=binding.trajectory_format,
        )
        self._shared_trajectory_evidence = runtime
        return runtime

    def _run_shared_checkpoint_snapshot(
        self,
        connection: sqlite3.Connection,
        context: FabricPostWriteContext,
    ) -> None:
        """Run the existing non-authoritative checkpoint write with native reads.

        This deliberately mirrors ``LegacyFabricPostWriteAdapter._run_checkpoint``:
        component reads degrade independently, while the whole checkpoint slot
        remains fail-soft at the post-write boundary.  It never loads a
        checkpoint and therefore grants it no native recovery authority.
        """
        owner = self._configuration.external.owner
        if not (
            owner._checkpoint_enable
            and int(context.step) > 0
            and int(context.step) % owner._checkpoint_interval == 0
        ):
            return
        binding = self._configuration.shared_checkpoint_snapshot_binding
        assert binding is not None  # preparation proves the explicit binding.
        try:
            motif_summary = None
            try:
                motif_summary = self._build_native_checkpoint_motif_summary(connection, context)
            except Exception as exc:
                owner._log.debug("checkpoint motif summary build failed: %s", exc)

            # Native representations have no legacy embedding-shard manifest.
            # The existing checkpoint schema permits this truthful absence.
            shard_snapshot = None

            character_state = None
            try:
                from dataclasses import asdict

                character_store = self._configuration.external.character_store
                if character_store is not None:
                    state = character_store.load_state(context.workspace_id, context.agent_id)
                    if state:
                        character_state = asdict(state)
            except Exception as exc:
                owner._log.debug("checkpoint character state load failed: %s", exc)

            if binding.kernel_runtime_context is None:
                owner._log.debug("checkpoint skipped: KernelRuntimeContext missing for %s", self._configuration.external.agent_key)
            else:
                save_checkpoint(
                    data_dir=owner.data_dir, workspace_id=context.workspace_id,
                    agent_id=context.agent_id, step=int(context.step),
                    model_state=binding.model_state,
                    corridor_monitor=binding.kernel_runtime_context.mon,
                    kernel_runtime_context=binding.kernel_runtime_context,
                    character_state_dict=character_state, motif_summary=motif_summary,
                    shard_snapshot=shard_snapshot, max_checkpoints=owner._checkpoint_max_keep,
                )
        except Exception as exc:
            owner._log.debug("checkpoint save failed for step=%s: %s", context.step, exc)

    def _build_native_checkpoint_motif_summary(
        self,
        connection: sqlite3.Connection,
        context: FabricPostWriteContext,
    ) -> dict[str, Any]:
        """Project only current native motif geometry into the legacy schema."""
        scope = self._configuration.routing_scope
        reader = NativeMotifRuntimeReader(connection)
        motifs = reader.list_runtime_motifs(
            motif_alias_namespace_id=scope.motif_alias_namespace_id,
            domain_id=context.chosen_domain,
            semantic_scope_id=scope.runtime_scope.semantic_scope_id,
        )
        projection = SimpleNamespace(motifs={
            item.read_model.runtime_motif_id: _NativeCheckpointMotifProjection(
                motif_id=item.read_model.runtime_motif_id,
                label=str(item.read_model.label),
                strength=float(item.read_model.strength),
                members=range(int(item.read_model.member_count)),
            )
            for item in motifs
        })
        return build_motif_summary(projection)

    def _bind_shared_integrated_dependencies(
        self,
        connection: sqlite3.Connection,
        context: FabricPostWriteContext,
        witness: NativePostWriteRouteWitness,
    ) -> LegacyFabricPostWriteAdapter:
        """Bind E1's already-qualified owners without granting new authority."""
        m1 = self._bind_shared_m1_mood_dependencies(connection, context, witness)
        scope = self._configuration.routing_scope
        external = self._configuration.external
        memory = NativePostWriteMemoryAccess(
            connection,
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=self._capability.binding.representation_lane.dimension,
        )
        world = NativeWorldRuntime(
            connection,
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            expected_dimension=self._capability.binding.representation_lane.dimension,
            process_state=self._capability.world_process_state,
        )
        srg = NativeSRGTransientRuntime(
            connection,
            legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
            process_state=self._capability.srg_process_state,
        )
        character = NativeCharacterDriftRuntime(
            configuration=NativeCharacterDriftRuntimeConfiguration(
                workspace_id=scope.runtime_scope.workspace_id,
                agent_id=context.agent_id,
                seed_id=str(external.identity.seed.get("seed_id", "") or ""),
                domain_id=context.chosen_domain,
                motif_alias_namespace_id=scope.motif_alias_namespace_id,
                semantic_scope_id=scope.runtime_scope.semantic_scope_id,
                expected_dimension=self._capability.binding.representation_lane.dimension,
                character_enabled=bool(getattr(external.owner, "_character_enable", False)),
                drift_every=int(getattr(external.owner, "_character_drift_every", 1)),
            ),
            store=external.character_store,
            memory_read=memory,
            memory_enumeration=memory,
            motif_reader=NativeMotifRuntimeReader(connection),
        )
        dependencies = LegacyFabricPostWriteDependencies(
            owner=external.owner,
            workspace=external.workspace,
            graph=_ForbiddenNativeGraph(),
            world_runtime=world,
            derived_memory_runtime=m1.derived_memory_runtime,
            memory_access=memory,
            memory_enumeration=memory,
            srg_runtime=srg,
            embedding_dimension=self._capability.binding.representation_lane.dimension,
            identity=external.identity,
            motif_registry=None,
            motif_runtime=m1.motif_runtime,
            model_state=None,
            kernel_context=None,
            agent_key=external.agent_key,
            detect_canon_conflict=external.detect_canon_conflict,
            proposal_allowed=external.proposal_allowed,
            random_chance=_forbidden_random_chance,
            save_checkpoint=_forbidden_checkpoint,
            build_motif_summary=_forbidden_checkpoint,
            build_shard_snapshot=_forbidden_checkpoint,
            hivemind_log=external.hivemind_log,
            character_drift_runtime=character,
        )
        return LegacyFabricPostWriteAdapter(dependencies)

    def _run_shared_integrated_m1_and_derived(
        self,
        consumers: LegacyFabricPostWriteAdapter,
        context: FabricPostWriteContext,
    ) -> int | None:
        """Keep M1/D0/D1's independent fail-soft boundaries in legacy order."""
        deps = consumers._deps
        policy = deps.workspace.domain_policies.get(context.chosen_domain, {})
        try:
            assert deps.motif_runtime is not None
            deps.motif_runtime.update_entropy_and_suggest(
                target_n=int(policy.get("motif_entropy_target_n", 24)),
                entropy_high=float(policy.get("motif_entropy_high", 0.72)),
                sim_threshold=float(policy.get("motif_merge_similarity", 0.93)),
                max_suggestions=int(policy.get("motif_merge_max_suggestions", 20)),
                auto_merge=bool(policy.get("auto_merge_motifs", False)),
                auto_merge_trigger=float(policy.get("auto_merge_entropy_trigger", 0.80)),
            )
        except Exception as exc:
            deps.owner._log.debug("motif entropy update failed for domain=%s: %s", context.chosen_domain, exc)
        derived_context = DerivedMemoryRuntimeContext(
            workspace_id=context.workspace_id,
            agent_id=context.agent_id,
            domain_id=context.chosen_domain,
            trigger_scope=context.scope,
            step=int(context.step),
            motif_ids=tuple(context.motif_ids),
            affect_tag=context.affect_tag,
            affect_conf=context.affect_conf,
        )
        try:
            deps.derived_memory_runtime.maybe_emit_identity_anchor(derived_context)
        except Exception as exc:
            deps.owner._log.debug("identity anchor emission failed: %s", exc)
        try:
            deps.derived_memory_runtime.refine_identity_anchors(derived_context)
        except Exception as exc:
            deps.owner._log.debug("identity anchor refinement failed: %s", exc)
        try:
            return deps.derived_memory_runtime.maybe_emit_mood_drift(derived_context)
        except Exception as exc:
            deps.owner._log.debug("mood drift emission failed: %s", exc)
            return None

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
            _validate_capability_embedder(self._capability, embedder)
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
        if checkpoint_due or self._private_checkpoint_snapshot_enabled:
            if profile.checkpoint is not NativePostWriteBehavior.QUALIFIED:
                _refuse(profile.checkpoint, "checkpoint")
            _validate_private_checkpoint_snapshot_binding(self._configuration)
        if self._private_trajectory_evidence_enabled:
            if profile.trajectory_evidence is not NativePostWriteBehavior.QUALIFIED:
                _refuse(profile.trajectory_evidence, "trajectory evidence")
            _validate_private_trajectory_evidence_binding(self._configuration)
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

    def _validate_shared_trajectory_pre_effect(self, context: FabricPostWriteContext) -> None:
        configuration = self._configuration
        if configuration.routing_scope.runtime_scope.scope_kind != "SHARED_DOMAIN":
            raise SubstrateInvariantViolation("shared post-write requires a claimed shared native scope")
        if not configuration.shared_trajectory_evidence_required:
            raise SubstrateConfigurationError("shared trajectory evidence capability is not required by this profile")
        _require_qualified(configuration.profile.shared_trajectory_evidence, "shared trajectory evidence")
        _validate_shared_trajectory_evidence_binding(configuration)
        if configuration.shared_bridge_suggestions_required:
            raise SubstrateConfigurationError("shared trajectory evidence and B1 bridge consumers must be prepared separately")
        if configuration.shared_motif_suggestion_maintenance_required or configuration.shared_mood_drift_binding is not None:
            raise SubstrateConfigurationError("shared trajectory evidence and D1 M1/mood consumers must be prepared separately")
        if configuration.shared_hivemind_packet_emission_required:
            raise SubstrateConfigurationError("shared trajectory evidence and D2 Hivemind consumers must be prepared separately")
        if configuration.derived_runtime_template is not None:
            raise SubstrateConfigurationError("shared trajectory evidence profile must not bind a source-scope derived runtime")
        if configuration.persistent_trajectory_evidence_required:
            raise SubstrateConfigurationError("shared D3 trajectory profile must not claim the private trajectory capability")

    def _validate_shared_checkpoint_pre_effect(self, context: FabricPostWriteContext) -> None:
        configuration = self._configuration
        if configuration.routing_scope.runtime_scope.scope_kind != "SHARED_DOMAIN":
            raise SubstrateInvariantViolation("shared post-write requires a claimed shared native scope")
        if not configuration.shared_checkpoint_snapshot_required:
            raise SubstrateConfigurationError("shared checkpoint capability is not required by this profile")
        _require_qualified(configuration.profile.shared_checkpoint_snapshot, "shared checkpoint snapshot")
        _validate_shared_checkpoint_snapshot_binding(configuration)
        if configuration.shared_bridge_suggestions_required:
            raise SubstrateConfigurationError("shared checkpoint and B1 bridge consumers must be prepared separately")
        if configuration.shared_motif_suggestion_maintenance_required or configuration.shared_mood_drift_binding is not None:
            raise SubstrateConfigurationError("shared checkpoint and D1 M1/mood consumers must be prepared separately")
        if configuration.shared_hivemind_packet_emission_required:
            raise SubstrateConfigurationError("shared checkpoint and D2 Hivemind consumers must be prepared separately")
        if configuration.shared_trajectory_evidence_required:
            raise SubstrateConfigurationError("shared checkpoint and D3 trajectory consumers must be prepared separately")
        if configuration.derived_runtime_template is not None:
            raise SubstrateConfigurationError("shared checkpoint profile must not bind a source-scope derived runtime")
        if configuration.checkpoint_snapshots_required:
            raise SubstrateConfigurationError("shared D4 checkpoint profile must not claim the private checkpoint capability")

    def _validate_shared_compression_disabled_pre_effect(self) -> None:
        """Prove D6's disabled shared route cannot reach a compression owner."""
        _validate_shared_compression_disabled_configuration(self._configuration)


def prepare_native_fabric_post_write_adapter(
    *,
    capability: NativeFabricRoutingCapability | NativeProductionRoutingCapability,
    configuration: NativePostWriteQualificationConfiguration,
) -> NativeFabricPostWriteAdapter:
    """Prepare a staging or owner-prepared active adapter without opening SQLite."""
    if not isinstance(capability, (NativeFabricRoutingCapability, NativeProductionRoutingCapability)):
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
        _validate_private_i4e_configuration(configuration)
    elif scope.runtime_scope.scope_kind == "SHARED_DOMAIN":
        shared_d1 = configuration.shared_motif_suggestion_maintenance_required
        shared_hivemind = configuration.shared_hivemind_packet_emission_required
        shared_trajectory = configuration.shared_trajectory_evidence_required
        shared_checkpoint = configuration.shared_checkpoint_snapshot_required
        shared_compression_disabled = configuration.shared_compression_disabled_noop_required
        shared_integrated = configuration.shared_integrated_default_required
        shared_consumers = sum((
            bool(configuration.shared_bridge_suggestions_required),
            bool(shared_d1),
            bool(shared_hivemind),
            bool(shared_trajectory),
            bool(shared_checkpoint),
            bool(shared_compression_disabled),
            bool(shared_integrated),
        ))
        if shared_consumers > 1:
            raise SubstrateConfigurationError("shared post-write consumers must be prepared separately")
        if shared_consumers == 0:
            raise SubstrateConfigurationError("shared post-write configuration has no qualified consumer")
        if template is not None:
            raise SubstrateConfigurationError("shared post-write configuration must not bind a source-scope derived runtime")
        if shared_integrated:
            _validate_shared_integrated_configuration(capability, configuration)
        elif configuration.shared_bridge_suggestions_required:
            _require_qualified(configuration.profile.shared_bridge_suggestion, "shared bridge suggestion")
            _require_shared_bridge_geometry(configuration.external.shared_bridge_geometry, capability)
            if not callable(configuration.external.random_chance):
                raise SubstrateConfigurationError("shared bridge configuration requires an injected random_chance dependency")
        elif shared_d1:
            _require_qualified(configuration.profile.shared_motif_suggestion_maintenance, "shared motif suggestion maintenance")
            _require_required_noop(configuration.profile.shared_trigger_identity_anchor, "shared trigger identity anchor")
            _require_qualified(configuration.profile.shared_trigger_mood_drift, "shared trigger mood drift")
            _validate_shared_mood_drift_binding(capability, configuration)
        elif shared_trajectory:
            _require_qualified(configuration.profile.shared_trajectory_evidence, "shared trajectory evidence")
            _validate_shared_trajectory_evidence_binding(configuration)
            if configuration.shared_mood_drift_binding is not None:
                raise SubstrateConfigurationError("shared trajectory configuration must not bind a private mood-drift target")
            if configuration.persistent_trajectory_evidence_required:
                raise SubstrateConfigurationError("shared D3 trajectory profile must not claim the private trajectory capability")
        elif shared_checkpoint:
            _require_qualified(configuration.profile.shared_checkpoint_snapshot, "shared checkpoint snapshot")
            _validate_shared_checkpoint_snapshot_binding(configuration)
            if configuration.shared_mood_drift_binding is not None:
                raise SubstrateConfigurationError("shared checkpoint configuration must not bind a private mood-drift target")
            if configuration.checkpoint_snapshots_required:
                raise SubstrateConfigurationError("shared D4 checkpoint profile must not claim the private checkpoint capability")
        elif shared_compression_disabled:
            _validate_shared_compression_disabled_configuration(configuration)
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


def _validate_capability_embedder(
    capability: NativeFabricRoutingCapability | NativeProductionRoutingCapability,
    embedder: Any,
) -> None:
    """Preserve lane validation without fabricating a STAGING binding."""
    if isinstance(capability, NativeFabricRoutingCapability):
        validate_fabric_embedder(capability.binding, embedder)
        return
    lane = capability.representation_lane
    if (
        getattr(embedder, "provider", None) != lane.provider
        or getattr(embedder, "model", None) != lane.model
        or getattr(embedder, "dim", None) != lane.dimension
    ):
        raise SubstrateConfigurationError("production post-write embedder does not match the native lane")


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


def _validate_shared_compression_disabled_configuration(
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    """Validate D6's narrow, explicitly disabled shared compression posture.

    This intentionally validates no source or candidate.  Returning from the
    D6 adapter must not enumerate native memory, open a deep store, touch a
    vector lane, or mutate a core successor.
    """
    if configuration.routing_scope.runtime_scope.scope_kind != "SHARED_DOMAIN":
        raise SubstrateInvariantViolation("shared post-write requires a claimed shared native scope")
    if not configuration.shared_compression_disabled_noop_required:
        raise SubstrateConfigurationError("shared compression disabled capability is not required by this profile")
    _require_qualified(
        configuration.profile.shared_compression_disabled_noop,
        "shared compression disabled no-op",
    )
    if configuration.profile.compression is not NativePostWriteBehavior.UNSUPPORTED:
        raise SubstrateConfigurationError("D6 disabled profile must not claim enabled compression")
    if configuration.profile.deep_memory is not NativePostWriteBehavior.UNSUPPORTED:
        raise SubstrateConfigurationError("D6 disabled profile must not claim deep-memory export")
    if configuration.derived_runtime_template is not None:
        raise SubstrateConfigurationError("shared D6 profile must not bind a source-scope derived runtime")
    if configuration.deep_memory_required:
        raise SubstrateConfigurationError("shared D6 profile must not claim the private deep-memory capability")
    owner = configuration.external.owner
    enabled = getattr(owner, "_compress_enable", None)
    if type(enabled) is not bool:
        raise SubstrateConfigurationError("shared D6 profile requires a boolean owner._compress_enable")
    if enabled:
        raise SubstrateConfigurationError(
            "shared D6 profile requires TORMENT_COMPRESS_ENABLE=false before effects"
        )


def _validate_shared_integrated_configuration(
    capability: NativeFabricRoutingCapability,
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    """Validate the complete E1 composition before its source operation."""
    scope = configuration.routing_scope
    if scope.runtime_scope.scope_kind != "SHARED_DOMAIN":
        raise SubstrateInvariantViolation("E1 integrated post-write requires a claimed shared native scope")
    if not configuration.shared_integrated_default_required:
        raise SubstrateConfigurationError("E1 integrated shared capability is not required by this profile")
    profile = configuration.profile
    _require_qualified(profile.shared_integrated_default, "shared integrated default")
    _require_qualified(profile.shared_bridge_suggestion, "shared bridge suggestion")
    _require_qualified(profile.shared_motif_suggestion_maintenance, "shared motif suggestion maintenance")
    _require_required_noop(profile.shared_trigger_identity_anchor, "shared trigger identity anchor")
    _require_qualified(profile.shared_trigger_mood_drift, "shared trigger mood drift")
    _require_qualified(profile.shared_hivemind_packet_emission, "shared Hivemind packet emission")
    _require_qualified(profile.shared_trajectory_evidence, "shared trajectory evidence")
    _require_qualified(profile.shared_checkpoint_snapshot, "shared checkpoint snapshot")
    _require_qualified(profile.shared_compression_disabled_noop, "shared compression disabled no-op")
    _require_qualified(profile.shared_trigger_character_noop, "shared Character no-op")
    _require_qualified(profile.motif_auto_merge, "motif auto-merge")
    if profile.compression is not NativePostWriteBehavior.UNSUPPORTED:
        raise SubstrateConfigurationError("E1 integrated profile must not claim enabled compression")
    if profile.deep_memory is not NativePostWriteBehavior.UNSUPPORTED:
        raise SubstrateConfigurationError("E1 integrated profile must not claim deep-memory export")
    if configuration.derived_runtime_template is not None:
        raise SubstrateConfigurationError("E1 integrated shared profile must not bind a source-scope derived runtime")
    if any((
        configuration.motif_suggestion_maintenance_required,
        configuration.persistent_trajectory_evidence_required,
        configuration.checkpoint_snapshots_required,
        configuration.bridge_suggestions_required,
    )):
        raise SubstrateConfigurationError(
            "E1 integrated shared profile cannot claim private-only post-write capabilities"
        )
    if configuration.deep_memory_required:
        raise SubstrateConfigurationError("E1 integrated shared profile must not claim private deep memory")
    if any((
        configuration.shared_bridge_suggestions_required,
        configuration.shared_motif_suggestion_maintenance_required,
        configuration.shared_hivemind_packet_emission_required,
        configuration.shared_trajectory_evidence_required,
        configuration.shared_checkpoint_snapshot_required,
        configuration.shared_compression_disabled_noop_required,
    )):
        raise SubstrateConfigurationError("E1 integrated profile cannot compose standalone shared consumer flags")
    _validate_shared_mood_drift_binding(capability, configuration)
    _validate_shared_trajectory_evidence_binding(configuration)
    _validate_shared_checkpoint_snapshot_binding(configuration)
    _require_shared_bridge_geometry(configuration.external.shared_bridge_geometry, capability)
    if not callable(configuration.external.random_chance):
        raise SubstrateConfigurationError("E1 integrated profile requires an injected random_chance dependency")
    owner = configuration.external.owner
    enabled = getattr(owner, "_compress_enable", None)
    if type(enabled) is not bool:
        raise SubstrateConfigurationError("E1 integrated profile requires a boolean owner._compress_enable")
    if enabled:
        raise SubstrateConfigurationError(
            "E1 integrated profile requires TORMENT_COMPRESS_ENABLE=false before effects"
        )


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


def _validate_shared_trajectory_evidence_binding(
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    binding = configuration.shared_trajectory_evidence_binding
    if binding is None:
        raise SubstrateConfigurationError("shared trajectory profile requires an evidence binding")
    data_dir = getattr(configuration.external.workspace, "data_dir", None)
    if not isinstance(data_dir, str) or not data_dir:
        raise SubstrateConfigurationError("shared trajectory profile requires workspace.data_dir")
    scope = configuration.routing_scope.runtime_scope
    expected_root = (
        Path(data_dir).resolve()
        / "workspaces" / scope.workspace_id / "domains" / str(scope.domain_id) / "shared"
    )
    if Path(binding.artifact_root_dir).resolve() != expected_root:
        raise SubstrateConfigurationError("shared trajectory evidence root does not match the claimed shared domain")
    if binding.trajectory_format != resolve_trajectory_format():
        raise SubstrateConfigurationError("shared trajectory evidence format does not match current legacy selection")


def _validate_private_i4e_configuration(
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    """Keep I4E's separately owned private tail complete but non-transactional."""
    trajectory = configuration.persistent_trajectory_evidence_required
    checkpoint = configuration.checkpoint_snapshots_required
    profile_trajectory = (
        configuration.profile.trajectory_evidence is NativePostWriteBehavior.QUALIFIED
    )
    profile_checkpoint = (
        configuration.profile.checkpoint is NativePostWriteBehavior.QUALIFIED
    )
    if trajectory != profile_trajectory or checkpoint != profile_checkpoint:
        raise SubstrateConfigurationError(
            "private I4E profile/configuration disagreement refuses effects"
        )
    if profile_trajectory != profile_checkpoint:
        raise SubstrateConfigurationError(
            "private I4E profile refuses a partial trajectory/checkpoint selection before effects"
        )
    if profile_trajectory:
        _require_qualified(configuration.profile.srg, "SRG")
        _require_qualified(configuration.profile.world, "world")
        _require_qualified(configuration.profile.trajectory_evidence, "trajectory evidence")
        _require_qualified(configuration.profile.checkpoint, "checkpoint")
        _validate_private_trajectory_evidence_binding(configuration)
        _validate_private_checkpoint_snapshot_binding(configuration)
    elif (
        configuration.private_trajectory_evidence_binding is not None
        or configuration.private_checkpoint_snapshot_binding is not None
    ):
        raise SubstrateConfigurationError("private I4E bindings require both private I4E consumers")


def _validate_private_trajectory_evidence_binding(
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    binding = configuration.private_trajectory_evidence_binding
    if binding is None:
        raise SubstrateConfigurationError("private I4E trajectory profile requires an evidence binding")
    data_dir = getattr(configuration.external.workspace, "data_dir", None)
    if not isinstance(data_dir, str) or not data_dir:
        raise SubstrateConfigurationError("private I4E trajectory profile requires workspace.data_dir")
    scope = configuration.routing_scope.runtime_scope
    expected_root = (
        Path(data_dir).resolve()
        / "workspaces" / scope.workspace_id / "agents" / str(scope.agent_id) / "private"
    )
    if Path(binding.artifact_root_dir).resolve() != expected_root:
        raise SubstrateConfigurationError("private trajectory evidence root does not match the claimed private agent")
    if binding.trajectory_format != resolve_trajectory_format():
        raise SubstrateConfigurationError("private trajectory evidence format does not match current legacy selection")


def _validate_private_checkpoint_snapshot_binding(
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    binding = configuration.private_checkpoint_snapshot_binding
    if binding is None:
        raise SubstrateConfigurationError("private I4E checkpoint profile requires an explicit live-state binding")
    owner = configuration.external.owner
    for name in ("_checkpoint_enable", "_checkpoint_interval", "_checkpoint_max_keep", "data_dir", "_log"):
        if not hasattr(owner, name):
            raise SubstrateConfigurationError(f"private I4E checkpoint profile requires owner.{name}")
    if not isinstance(owner.data_dir, str) or not owner.data_dir:
        raise SubstrateConfigurationError("private I4E checkpoint profile requires a non-empty owner.data_dir")
    if not isinstance(owner._checkpoint_interval, int) or isinstance(owner._checkpoint_interval, bool) or owner._checkpoint_interval < 1:
        raise SubstrateConfigurationError("private I4E checkpoint profile requires a positive owner._checkpoint_interval")
    if not isinstance(owner._checkpoint_max_keep, int) or isinstance(owner._checkpoint_max_keep, bool) or owner._checkpoint_max_keep < 0:
        raise SubstrateConfigurationError("private I4E checkpoint profile requires a non-negative owner._checkpoint_max_keep")
    # The legacy checkpoint writer captures Character state as an independent,
    # fail-soft component read.  A missing or failing CharacterStore therefore
    # omits only that optional snapshot field; it is not a pre-effect refusal.


def _validate_shared_checkpoint_snapshot_binding(
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    binding = configuration.shared_checkpoint_snapshot_binding
    if binding is None:
        raise SubstrateConfigurationError("shared checkpoint profile requires an explicit live-state binding")
    owner = configuration.external.owner
    for name in ("_checkpoint_enable", "_checkpoint_interval", "_checkpoint_max_keep", "data_dir", "_log"):
        if not hasattr(owner, name):
            raise SubstrateConfigurationError(f"shared checkpoint profile requires owner.{name}")
    if not isinstance(owner.data_dir, str) or not owner.data_dir:
        raise SubstrateConfigurationError("shared checkpoint profile requires a non-empty owner.data_dir")
    if not isinstance(owner._checkpoint_interval, int) or isinstance(owner._checkpoint_interval, bool) or owner._checkpoint_interval < 1:
        raise SubstrateConfigurationError("shared checkpoint profile requires a positive owner._checkpoint_interval")
    if not isinstance(owner._checkpoint_max_keep, int) or isinstance(owner._checkpoint_max_keep, bool) or owner._checkpoint_max_keep < 0:
        raise SubstrateConfigurationError("shared checkpoint profile requires a non-negative owner._checkpoint_max_keep")
    character_store = configuration.external.character_store
    if character_store is None or not callable(getattr(character_store, "load_state", None)):
        raise SubstrateConfigurationError("shared checkpoint profile requires the existing CharacterStore load_state interface")


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
    "NativePrivateCheckpointSnapshotBinding",
    "NativePrivateTrajectoryEvidenceBinding",
    "NativePostWriteQualificationConfiguration",
    "NativePostWriteQualificationProfile",
    "NativePostWriteRouteWitness",
    "NativeSharedIntegratedPostWriteOutcome",
    "NativeSharedCheckpointSnapshotBinding",
    "NativeSharedTrajectoryEvidenceBinding",
    "NativeSharedTriggerMoodDriftBinding",
    "prepare_native_fabric_post_write_adapter",
]
