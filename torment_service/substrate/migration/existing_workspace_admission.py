"""Bounded existing-workspace private-core admission and cold native recovery.

This is deliberately an orchestration layer over the qualified B-series
services.  It has no selector, Fabric runtime import, legacy fallback, or
write-capable recovery surface.  The first supported profile is intentionally
small: one already-existing private agent workspace, ordinary core memories,
one locked captured embedding lane, and lane-preserving motifs below the
auto-split boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any
from uuid import UUID

from ..compat import NativeMemoryCompatibilityFacade
from ..compat_embedding_reader import NativeCompatEmbeddingReader
from ..character_seed_witness import (
    CharacterSeedWitness, CharacterSeedWitnessRefused, read_legacy_character_seed_witness,
)
from ..connection import open_existing_native_core_connection, open_new_native_core_connection
from ..errors import SubstrateConfigurationError
from ..fabric_native_routing import NativeFabricRoutingScope
from ..ids import native_id_from_bytes, native_id_to_bytes
from ..motif_runtime_reader import NativeMotifRuntimeReader
from ..native_memory_runtime_access import NativePostWriteMemoryAccess
from ..runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from ..schema import create_schema, open_schema
from .rehearsal import MigrationRehearsalConfig, NativeLegacyMigrationRehearsal
from .runtime_motif_projection import (
    MigrationRuntimeMotifProjectionRequest,
    NativeMigrationRuntimeMotifProjectionService,
)
from .runtime_normalization import (
    MigrationRuntimeNormalizationRequest,
    NativeMigrationRuntimeNormalizationService,
)
from .character_seed_normalization import (
    MigrationCharacterSeedNormalizationRequest,
    NativeMigrationCharacterSeedNormalizationService,
)
from .runtime_readiness import (
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeScopePlan,
    NativeMigrationRuntimeReadinessPreflight,
    ObjectRuntimeReadiness,
)
from .runtime_representation_bootstrap import (
    MigrationRuntimeRepresentationBootstrapRequest,
    NativeMigrationRuntimeRepresentationBootstrapService,
)
from .snapshot import create_snapshot_manifest, load_snapshot_manifest, verify_snapshot
from .workspace_runtime_readiness import (
    NativeWorkspaceRuntimeReadiness,
    RetainedSideStoreEIDObservation,
    RetainedSideStoreEIDReference,
    WorkspaceNativeEmbedderIdentity,
    WorkspaceNativeFeaturePosture,
    WorkspaceNativeRuntimeReadinessReport,
    WorkspaceNativeRuntimeReadinessRequest,
)


_PROFILE = "EXISTING_WORKSPACE/PRIVATE_AGENT/ORDINARY_CORE_MEMORY/CHARACTER_FREE/SINGLE_EMBEDDING_LANE"
_CHARACTER_PROFILE = "EXISTING_WORKSPACE_PRIVATE_CHARACTER"
_PRIVATE_AGENT = "PRIVATE_AGENT"
_DESCRIPTOR_SCHEMA = "TORMENT_EXISTING_WORKSPACE_NATIVE_ADMISSION"
_DESCRIPTOR_VERSION = 1
_COMPLETE = "ADMISSION_COMPLETE"
_INCOMPLETE = "ADMISSION_INCOMPLETE_RESUMABLE"
_MAX_SUPPORTED_MOTIF_MEMBERS = 95
_EID_OBSERVATION_STORES = (
    "conflicts", "anchors", "affect_history", "character_store",
    "hivemind_collective", "bridges", "trajectory_evidence", "deep_memory",
)


class ExistingWorkspaceAdmissionRefused(SubstrateConfigurationError):
    """A typed fail-closed profile or durable-evidence refusal."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ExistingWorkspaceAdmissionState(StrEnum):
    ADMISSION_NOT_STARTED = "ADMISSION_NOT_STARTED"
    ADMISSION_INCOMPLETE_RESUMABLE = _INCOMPLETE
    ADMISSION_COMPLETE = _COMPLETE
    RECOVERY_REFUSED = "RECOVERY_REFUSED"
    RECOVERY_READY = "RECOVERY_READY"


@dataclass(frozen=True)
class ExistingWorkspaceNativeAdmissionRequest:
    """All profile identities and B5 facts are caller-owned and explicit."""

    legacy_workspace_root: str | Path
    workspace_id: str
    agent_id: str
    native_core_database_path: str | Path
    admission_descriptor_path: str | Path
    snapshot_root: str | Path
    snapshot_manifest_path: str | Path
    admission_key: str
    legacy_source_namespace_id: UUID
    legacy_source_namespace_key: str
    target_identity_namespace_id: UUID
    target_semantic_scope_id: UUID
    unknown_semantic_scope_id: UUID
    motif_alias_namespace_id: UUID
    motif_identity_namespace_id: UUID
    membership_identity_namespace_id: UUID
    idempotency_namespace_id: UUID
    qualified_representation_lane: NativeRepresentationLane
    motif_domain_id: str
    staging_feature_posture: WorkspaceNativeFeaturePosture
    production_feature_posture: WorkspaceNativeFeaturePosture
    qualification_embedder_identity: WorkspaceNativeEmbedderIdentity
    post_write_configuration: Any
    retained_side_store_eid_references: tuple[RetainedSideStoreEIDReference, ...] = ()
    retained_side_store_eid_observations: tuple[RetainedSideStoreEIDObservation, ...] = ()
    scope_kind: str = _PRIVATE_AGENT
    shared_domain_claimed: bool = False
    character_seed_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "workspace_id", "agent_id", "admission_key", "legacy_source_namespace_key", "motif_domain_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty text")
        for name in (
            "legacy_workspace_root", "native_core_database_path", "admission_descriptor_path",
            "snapshot_root", "snapshot_manifest_path",
        ):
            if not isinstance(getattr(self, name), (str, Path)) or not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be an explicit path")
        for name in (
            "legacy_source_namespace_id", "target_identity_namespace_id", "target_semantic_scope_id",
            "unknown_semantic_scope_id", "motif_alias_namespace_id", "motif_identity_namespace_id",
            "membership_identity_namespace_id", "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, name), UUID):
                raise ValueError(f"{name} must be a UUID")
        if not isinstance(self.qualified_representation_lane, NativeRepresentationLane):
            raise ValueError("qualified_representation_lane must be NativeRepresentationLane")
        if not isinstance(self.staging_feature_posture, WorkspaceNativeFeaturePosture):
            raise ValueError("staging_feature_posture must be typed")
        if not isinstance(self.production_feature_posture, WorkspaceNativeFeaturePosture):
            raise ValueError("production_feature_posture must be typed")
        if not isinstance(self.qualification_embedder_identity, WorkspaceNativeEmbedderIdentity):
            raise ValueError("qualification_embedder_identity must be typed")
        if type(self.shared_domain_claimed) is not bool:
            raise ValueError("shared_domain_claimed must be boolean")
        if self.character_seed_id is not None and (
            not isinstance(self.character_seed_id, str) or not self.character_seed_id
        ):
            raise ValueError("character_seed_id must be non-empty text when supplied")

    @property
    def scope_plan(self) -> MigrationRuntimeScopePlan:
        return MigrationRuntimeScopePlan(
            legacy_source_namespace_id=self.legacy_source_namespace_id,
            workspace_id=self.workspace_id,
            scope_kind=_PRIVATE_AGENT,
            agent_id=self.agent_id,
            target_identity_namespace_id=self.target_identity_namespace_id,
            target_semantic_scope_id=self.target_semantic_scope_id,
            motif_alias_namespace_id=self.motif_alias_namespace_id,
            motif_identity_namespace_id=self.motif_identity_namespace_id,
            membership_identity_namespace_id=self.membership_identity_namespace_id,
            idempotency_namespace_id=self.idempotency_namespace_id,
            motif_domain_id=self.motif_domain_id,
        )


@dataclass(frozen=True)
class ExistingWorkspaceAdmissionDescriptor:
    """Canonical durable facts sufficient for native-only read recovery."""

    payload: dict[str, Any]
    digest: str

    @property
    def state(self) -> ExistingWorkspaceAdmissionState:
        return ExistingWorkspaceAdmissionState(self.payload["admission_state"])

    @property
    def native_core_id(self) -> UUID:
        value = self.payload.get("native_core_id")
        if not isinstance(value, str):
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_CORE_ID_MISSING")
        return UUID(value)

    @property
    def representation_lane(self) -> NativeRepresentationLane:
        return _lane_from_payload(self.payload["representation_lane"])

    @property
    def scope_plan(self) -> MigrationRuntimeScopePlan:
        value = self.payload["scope_plan"]
        return MigrationRuntimeScopePlan(
            legacy_source_namespace_id=UUID(value["legacy_source_namespace_id"]),
            workspace_id=value["workspace_id"], scope_kind=value["scope_kind"],
            agent_id=value["agent_id"],
            target_identity_namespace_id=UUID(value["target_identity_namespace_id"]),
            target_semantic_scope_id=UUID(value["target_semantic_scope_id"]),
            motif_alias_namespace_id=UUID(value["motif_alias_namespace_id"]),
            motif_identity_namespace_id=UUID(value["motif_identity_namespace_id"]),
            membership_identity_namespace_id=UUID(value["membership_identity_namespace_id"]),
            idempotency_namespace_id=UUID(value["idempotency_namespace_id"]),
            motif_domain_id=value["motif_domain_id"],
        )

    @property
    def character_seed_witness(self) -> CharacterSeedWitness | None:
        value = self.payload.get("character_seed")
        if value is None:
            return None
        plan = self.scope_plan
        return CharacterSeedWitness.from_descriptor_payload(
            workspace_id=plan.workspace_id, agent_id=plan.agent_id,
            domain_id=plan.motif_domain_id, value=value,
        )


@dataclass(frozen=True)
class ExistingWorkspaceNativeAdmissionResult:
    descriptor: ExistingWorkspaceAdmissionDescriptor
    readiness_report: WorkspaceNativeRuntimeReadinessReport
    rehearsal_execution_order: tuple[str, ...]
    memory_count: int
    motif_count: int
    resumed: bool


@dataclass
class RecoveredExistingWorkspaceNativeReaders:
    """Caller-owned, closeable read-only native reader bundle."""

    _qualified_connection: Any
    memory: NativeMemoryCompatibilityFacade
    embeddings: NativeCompatEmbeddingReader
    motifs: NativeMotifRuntimeReader
    memory_enumeration: NativePostWriteMemoryAccess

    def close(self) -> None:
        self._qualified_connection.close()

    def __enter__(self) -> "RecoveredExistingWorkspaceNativeReaders":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


@dataclass(frozen=True)
class RecoveredExistingWorkspaceNativeRuntime:
    """Immutable read-only reconstruction; it owns no legacy fallback or writer."""

    native_core_database_path: Path
    descriptor: ExistingWorkspaceAdmissionDescriptor
    memory_runtime_scope: NativeMemoryRuntimeScope
    fabric_routing_scope: NativeFabricRoutingScope
    representation_lane: NativeRepresentationLane
    character_seed_witness: CharacterSeedWitness | None = None
    state: ExistingWorkspaceAdmissionState = ExistingWorkspaceAdmissionState.RECOVERY_READY

    def open_readers(self) -> RecoveredExistingWorkspaceNativeReaders:
        qualified = open_existing_native_core_connection(self.native_core_database_path)
        try:
            metadata = open_schema(qualified.connection, writable=False)
            if native_id_from_bytes(metadata.core_id) != self.descriptor.native_core_id:
                raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_RECOVERY_WRONG_CORE")
            return RecoveredExistingWorkspaceNativeReaders(
                qualified,
                NativeMemoryCompatibilityFacade(qualified.connection),
                NativeCompatEmbeddingReader(qualified.connection),
                NativeMotifRuntimeReader(qualified.connection),
                NativePostWriteMemoryAccess(
                    qualified.connection,
                    legacy_source_namespace_id=self.memory_runtime_scope.legacy_source_namespace_id,
                    expected_dimension=self.representation_lane.dimension,
                ),
            )
        except Exception:
            qualified.close()
            raise

    def require_external_character_seed(self, character_store: Any) -> Any:
        """Read one retained external seed and bind it to descriptor evidence."""
        witness = self.character_seed_witness
        if witness is None:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_PROFILE_NOT_ADMITTED")
        if character_store is None or not hasattr(character_store, "load_seed"):
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_STORE_REQUIRED")
        seed = character_store.load_seed(self.memory_runtime_scope.workspace_id, witness.seed_id)
        if seed is None or not hasattr(seed, "to_dict") or seed.to_dict() != dict(witness.seed_definition):
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_STORE_SEED_MISMATCH")
        return seed


class ExistingWorkspaceNativeAdmissionService:
    """Coordinate one explicit B1--B5 private-core admission without cutover."""

    def admit(
        self,
        request: ExistingWorkspaceNativeAdmissionRequest,
        *,
        _test_interrupt_after_stage: str | None = None,
        _test_lose_response_after_stage: str | None = None,
    ) -> ExistingWorkspaceNativeAdmissionResult:
        if not isinstance(request, ExistingWorkspaceNativeAdmissionRequest):
            raise ValueError("request must be ExistingWorkspaceNativeAdmissionRequest")
        if _test_interrupt_after_stage not in {None, "B2", "B3A", "B4A", "B5"}:
            raise ValueError("_test_interrupt_after_stage must name a B-series stage")
        if _test_lose_response_after_stage not in {None, "B2", "B3A", "B4A"}:
            raise ValueError("_test_lose_response_after_stage must name a committed stage")
        self._validate_profile(request)
        paths = _AdmissionPaths.from_request(request)
        descriptor = _load_or_create_descriptor(request, paths)
        resumed = descriptor is not None
        source_fingerprint = _tree_fingerprint(paths.source_workspace_root)
        character_witness: CharacterSeedWitness | None
        if descriptor is None:
            if request.character_seed_id is None:
                _verify_character_free(request, paths.source_workspace_root)
                character_witness = None
            else:
                character_witness = _read_character_witness(request, paths.source_workspace_root)
            _verify_workspace_lane(request, paths.source_workspace_root)
            _verify_motif_profile(request, paths.source_workspace_root)
            _create_profile_snapshot(request, paths)
            manifest = create_snapshot_manifest(
                snapshot_root=paths.snapshot_root,
                manifest_path=paths.snapshot_manifest_path,
                legacy_source_namespace_id=request.legacy_source_namespace_id,
                legacy_source_namespace_key=request.legacy_source_namespace_key,
                capture_label="7G5E1 existing private workspace admission",
            )
            descriptor = _new_descriptor(request, source_fingerprint, manifest, character_witness)
            _write_descriptor(paths.descriptor_path, descriptor.payload)
        else:
            _verify_descriptor_matches_request(descriptor, request)
            if descriptor.payload["source_fingerprint"] != source_fingerprint:
                raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_SOURCE_EVIDENCE_MISMATCH")
            manifest = load_snapshot_manifest(paths.snapshot_manifest_path)
            _verify_descriptor_snapshot(descriptor, manifest, paths.snapshot_manifest_path)
            character_witness = descriptor.character_seed_witness

        verify_snapshot(snapshot_root=paths.snapshot_root, manifest=manifest)
        qualified, core_id = self._open_or_create_core(request, paths, descriptor)
        try:
            connection = qualified.connection
            _ensure_explicit_namespaces(connection, request)
            config = MigrationRehearsalConfig(
                native_core_id=core_id,
                idempotency_namespace_id=request.idempotency_namespace_id,
                object_identity_namespace_id=request.target_identity_namespace_id,
                relationship_identity_namespace_id=request.membership_identity_namespace_id,
                unknown_semantic_scope_id=request.unknown_semantic_scope_id,
            )
            rehearsal = NativeLegacyMigrationRehearsal(connection).run(
                snapshot_root=paths.snapshot_root, manifest_path=paths.snapshot_manifest_path, config=config,
            )
            descriptor = _ensure_stage_witnesses(
                descriptor, connection, request, manifest, core_id, character_witness,
            )
            _write_descriptor(paths.descriptor_path, descriptor.payload)
            if descriptor.state is ExistingWorkspaceAdmissionState.ADMISSION_COMPLETE:
                report = _readiness_report(connection, request, manifest, core_id, paths)
                return ExistingWorkspaceNativeAdmissionResult(descriptor, report, rehearsal.execution_order, len(report.memory_items), len(report.motif_items), resumed)

            self._run_b2(
                connection, request, manifest, core_id, descriptor, paths, character_witness,
                _test_lose_response_after_stage == "B2",
            )
            descriptor = _stage_complete(descriptor, "B2")
            _write_descriptor(paths.descriptor_path, descriptor.payload)
            _raise_if_interrupted(_test_interrupt_after_stage, "B2")

            self._run_b3a(connection, request, manifest, core_id, descriptor, paths, _test_lose_response_after_stage == "B3A")
            descriptor = _stage_complete(descriptor, "B3A")
            _write_descriptor(paths.descriptor_path, descriptor.payload)
            _raise_if_interrupted(_test_interrupt_after_stage, "B3A")

            self._run_b4a(connection, request, manifest, core_id, descriptor, paths, _test_lose_response_after_stage == "B4A")
            descriptor = _stage_complete(descriptor, "B4A")
            _write_descriptor(paths.descriptor_path, descriptor.payload)
            _raise_if_interrupted(_test_interrupt_after_stage, "B4A")

            report = _readiness_report(connection, request, manifest, core_id, paths)
            if not report.core_staging_runtime_ready:
                raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_B5_RUNTIME_READINESS_REFUSED")
            descriptor = _complete_descriptor(descriptor, report)
            _write_descriptor(paths.descriptor_path, descriptor.payload)
            descriptor = load_existing_workspace_admission_descriptor(paths.descriptor_path)
            _raise_if_interrupted(_test_interrupt_after_stage, "B5")
            if descriptor.payload["source_fingerprint"] != _tree_fingerprint(paths.source_workspace_root):
                raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_SOURCE_EVIDENCE_MISMATCH")
            return ExistingWorkspaceNativeAdmissionResult(descriptor, report, rehearsal.execution_order, len(report.memory_items), len(report.motif_items), resumed)
        finally:
            qualified.close()

    def _open_or_create_core(
        self, request: ExistingWorkspaceNativeAdmissionRequest, paths: "_AdmissionPaths",
        descriptor: ExistingWorkspaceAdmissionDescriptor,
    ) -> tuple[Any, UUID]:
        if paths.core_path.exists():
            qualified = open_existing_native_core_connection(paths.core_path)
            metadata = open_schema(qualified.connection, writable=False)
            actual = native_id_from_bytes(metadata.core_id)
            expected = descriptor.payload.get("native_core_id")
            if expected is not None and expected != str(actual):
                qualified.close()
                raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_NATIVE_CORE_ID_MISMATCH")
            if expected is None:
                descriptor.payload["native_core_id"] = str(actual)
                _write_descriptor(paths.descriptor_path, descriptor.payload)
            return qualified, actual
        if descriptor.payload.get("native_core_id") is not None:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_NATIVE_CORE_MISSING")
        qualified = open_new_native_core_connection(paths.core_path)
        try:
            metadata = create_schema(qualified.connection)
            actual = native_id_from_bytes(metadata.core_id)
            descriptor.payload["native_core_id"] = str(actual)
            _write_descriptor(paths.descriptor_path, descriptor.payload)
            return qualified, actual
        except Exception:
            qualified.close()
            raise

    def _run_b2(self, connection: Any, request: ExistingWorkspaceNativeAdmissionRequest, manifest: Any,
                core_id: UUID, descriptor: ExistingWorkspaceAdmissionDescriptor, paths: "_AdmissionPaths",
                character_witness: CharacterSeedWitness | None, lose_response: bool) -> None:
        service = NativeMigrationRuntimeNormalizationService(connection)
        character_service = NativeMigrationCharacterSeedNormalizationService(connection) if character_witness else None
        for witness in descriptor.payload["memory_witnesses"]:
            ordinary_request = MigrationRuntimeNormalizationRequest(
                paths.snapshot_root, paths.snapshot_manifest_path, manifest.legacy_snapshot_id,
                request.legacy_source_namespace_id, core_id, witness["eid"], UUID(witness["r1_revision_id"]),
                (request.scope_plan,), request.idempotency_namespace_id,
                _stage_key(request, "B2", witness["eid"]),
            )
            if witness.get("normalization_kind") == "CHARACTER_SEED":
                if character_service is None or character_witness is None:
                    raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_WITNESS_REQUIRED")
                result = character_service.normalize_character_seed(
                    MigrationCharacterSeedNormalizationRequest(ordinary_request, character_witness),
                    _test_lose_response_after_commit=lose_response and witness is descriptor.payload["memory_witnesses"][0],
                )
            else:
                result = service.normalize_legacy_core_memory(
                    ordinary_request,
                    _test_lose_response_after_commit=lose_response and witness is descriptor.payload["memory_witnesses"][0],
                )
            witness["r2_revision_id"] = str(result.revision_id)

    def _run_b3a(self, connection: Any, request: ExistingWorkspaceNativeAdmissionRequest, manifest: Any,
                 core_id: UUID, descriptor: ExistingWorkspaceAdmissionDescriptor, paths: "_AdmissionPaths", lose_response: bool) -> None:
        service = NativeMigrationRuntimeRepresentationBootstrapService(connection)
        for witness in descriptor.payload["memory_witnesses"]:
            result = service.bootstrap_from_legacy_capture(MigrationRuntimeRepresentationBootstrapRequest(
                paths.snapshot_root, paths.snapshot_manifest_path, manifest.legacy_snapshot_id,
                request.legacy_source_namespace_id, core_id, witness["eid"], UUID(witness["r1_revision_id"]),
                UUID(witness["r2_revision_id"]), request.qualified_representation_lane,
                request.idempotency_namespace_id, _stage_key(request, "B3A", witness["eid"]),
            ), _test_lose_response_after_ready=lose_response and witness is descriptor.payload["memory_witnesses"][0])
            witness["representation_id"] = str(result.representation_id)

    def _run_b4a(self, connection: Any, request: ExistingWorkspaceNativeAdmissionRequest, manifest: Any,
                 core_id: UUID, descriptor: ExistingWorkspaceAdmissionDescriptor, paths: "_AdmissionPaths", lose_response: bool) -> None:
        service = NativeMigrationRuntimeMotifProjectionService(connection)
        for witness in descriptor.payload["motif_witnesses"]:
            result = service.project_lane_preserving_legacy_motif(MigrationRuntimeMotifProjectionRequest(
                paths.snapshot_root, paths.snapshot_manifest_path, manifest.legacy_snapshot_id,
                request.legacy_source_namespace_id, core_id, witness["runtime_motif_id"],
                UUID(witness["source_object_id"]), UUID(witness["r1_revision_id"]),
                (request.scope_plan,), request.qualified_representation_lane,
                request.idempotency_namespace_id, _stage_key(request, "B4A", witness["runtime_motif_id"]),
            ), _test_lose_response_after_commit=lose_response and witness is descriptor.payload["motif_witnesses"][0])
            witness["target_object_id"] = str(result.motif_object_id)

    @staticmethod
    def _validate_profile(request: ExistingWorkspaceNativeAdmissionRequest) -> None:
        if request.shared_domain_claimed or request.scope_kind != _PRIVATE_AGENT:
            raise ExistingWorkspaceAdmissionRefused("SHARED_DOMAIN_ADMISSION_NOT_IN_7G5E1_PROFILE")
        lane = request.qualified_representation_lane
        if (lane.representation_class, lane.generation, lane.derivation_contract_version, lane.encoding_id, lane.dtype) != (
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
        ):
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_UNQUALIFIED_REPRESENTATION_LANE")


@dataclass(frozen=True)
class _AdmissionPaths:
    source_workspace_root: Path
    core_path: Path
    descriptor_path: Path
    snapshot_root: Path
    snapshot_manifest_path: Path

    @classmethod
    def from_request(cls, request: ExistingWorkspaceNativeAdmissionRequest) -> "_AdmissionPaths":
        source = Path(request.legacy_workspace_root).expanduser().resolve()
        if not source.is_dir():
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_SOURCE_ROOT_REQUIRED")
        workspace = source if (source / "workspace_meta.json").is_file() else source / "workspaces" / request.workspace_id
        if not workspace.is_dir() or not (workspace / "workspace_meta.json").is_file():
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_SOURCE_WORKSPACE_NOT_FOUND")
        core = Path(request.native_core_database_path).expanduser().resolve()
        descriptor = Path(request.admission_descriptor_path).expanduser().resolve()
        snapshot = Path(request.snapshot_root).expanduser().resolve()
        manifest = Path(request.snapshot_manifest_path).expanduser().resolve()
        if core.suffix.lower() != ".db" or not core.parent.is_dir():
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_NATIVE_DESTINATION_INVALID")
        for value, code in ((core, "EXISTING_WORKSPACE_DESTINATION_INSIDE_SOURCE"), (descriptor, "EXISTING_WORKSPACE_DESCRIPTOR_INSIDE_SOURCE"), (snapshot, "EXISTING_WORKSPACE_SNAPSHOT_INSIDE_SOURCE"), (manifest, "EXISTING_WORKSPACE_MANIFEST_INSIDE_SOURCE")):
            if _is_within(value, workspace):
                raise ExistingWorkspaceAdmissionRefused(code)
        if _is_within(core, source):
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESTINATION_INSIDE_SOURCE")
        return cls(workspace, core, descriptor, snapshot, manifest)


def recover_existing_workspace_native_runtime(
    *, native_core_database_path: str | Path, admission_descriptor_path: str | Path,
    expected_representation_lane: NativeRepresentationLane | None = None,
    character_store: Any | None = None,
) -> RecoveredExistingWorkspaceNativeRuntime:
    """Recover native read facts using only a complete descriptor and core path."""
    descriptor = load_existing_workspace_admission_descriptor(admission_descriptor_path)
    if descriptor.state is not ExistingWorkspaceAdmissionState.ADMISSION_COMPLETE:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_RECOVERY_NOT_COMPLETE")
    lane = descriptor.representation_lane
    if expected_representation_lane is not None and expected_representation_lane != lane:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_RECOVERY_WRONG_LANE")
    plan = descriptor.scope_plan
    core_path = Path(native_core_database_path).expanduser().resolve()
    with open_existing_native_core_connection(core_path) as qualified:
        metadata = open_schema(qualified.connection, writable=False)
        if native_id_from_bytes(metadata.core_id) != descriptor.native_core_id:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_RECOVERY_WRONG_CORE")
        scope = NativeMemoryRuntimeScope(
            workspace_id=plan.workspace_id, scope_kind=plan.scope_kind,
            legacy_source_namespace_id=plan.legacy_source_namespace_id,
            identity_namespace_id=plan.target_identity_namespace_id,
            semantic_scope_id=plan.target_semantic_scope_id, agent_id=plan.agent_id,
        )
        # The existing constructor is a read-only verification of the retained
        # STAGING/LEGACY_ACTIVE deployment facts; its result is intentionally not
        # a routing capability or writer.
        prepare_native_memory_runtime_binding(
            connection=qualified.connection, core_database_path=core_path,
            expected_core_id=descriptor.native_core_id, scope_bindings=(scope,), representation_lane=lane,
        )
    routing = NativeFabricRoutingScope(
        runtime_scope=scope, motif_alias_namespace_id=plan.motif_alias_namespace_id,
        motif_identity_namespace_id=plan.motif_identity_namespace_id,
        membership_identity_namespace_id=plan.membership_identity_namespace_id,
        idempotency_namespace_id=plan.idempotency_namespace_id,
    )
    runtime = RecoveredExistingWorkspaceNativeRuntime(
        core_path, descriptor, scope, routing, lane, descriptor.character_seed_witness,
    )
    if runtime.character_seed_witness is not None:
        runtime.require_external_character_seed(character_store)
    return runtime


def load_existing_workspace_admission_descriptor(path: str | Path) -> ExistingWorkspaceAdmissionDescriptor:
    descriptor_path = Path(path).expanduser().resolve()
    try:
        value = json.loads(descriptor_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_UNREADABLE") from exc
    if not isinstance(value, dict) or set(value) != {"descriptor_digest", "payload"} or not isinstance(value["payload"], dict):
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_TAMPERED")
    payload = value["payload"]
    canonical = _canonical(payload)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if value["descriptor_digest"] != digest:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_TAMPERED")
    if payload.get("descriptor_schema") != _DESCRIPTOR_SCHEMA or payload.get("descriptor_version") != _DESCRIPTOR_VERSION:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_VERSION_UNSUPPORTED")
    try:
        ExistingWorkspaceAdmissionState(payload["admission_state"])
    except (KeyError, ValueError) as exc:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_TAMPERED") from exc
    return ExistingWorkspaceAdmissionDescriptor(payload, digest)


def _load_or_create_descriptor(request: ExistingWorkspaceNativeAdmissionRequest, paths: _AdmissionPaths) -> ExistingWorkspaceAdmissionDescriptor | None:
    if paths.descriptor_path.exists():
        return load_existing_workspace_admission_descriptor(paths.descriptor_path)
    if paths.core_path.exists():
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_FIRST_DESTINATION_MUST_BE_NEW")
    if paths.snapshot_root.exists() or paths.snapshot_manifest_path.exists():
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_FIRST_SNAPSHOT_DESTINATION_MUST_BE_NEW")
    if not paths.descriptor_path.parent.is_dir() or not paths.snapshot_root.parent.is_dir() or not paths.snapshot_manifest_path.parent.is_dir():
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_EXTERNAL_DESTINATION_PARENT_REQUIRED")
    return None


def _new_descriptor(
    request: ExistingWorkspaceNativeAdmissionRequest, source_fingerprint: str, manifest: Any,
    character_witness: CharacterSeedWitness | None = None,
) -> ExistingWorkspaceAdmissionDescriptor:
    payload: dict[str, Any] = {
        "descriptor_schema": _DESCRIPTOR_SCHEMA,
        "descriptor_version": _DESCRIPTOR_VERSION,
        "profile": _CHARACTER_PROFILE if character_witness is not None else _PROFILE,
        "admission_state": _INCOMPLETE,
        "admission_key": request.admission_key,
        "source_fingerprint": source_fingerprint,
        "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
        "legacy_snapshot_manifest_digest": _file_digest(Path(request.snapshot_manifest_path)),
        "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
        "legacy_source_namespace_key": request.legacy_source_namespace_key,
        "workspace_id": request.workspace_id,
        "agent_id": request.agent_id,
        "native_core_id": None,
        "schema_version": [1, 2],
        "scope_plan": _scope_payload(request.scope_plan),
        "scope_plan_digest": _digest(_scope_payload(request.scope_plan)),
        "representation_lane": _lane_payload(request.qualified_representation_lane),
        "unknown_semantic_scope_id": str(request.unknown_semantic_scope_id),
        "shared_domain_admission": False,
        "stages_complete": [],
        "memory_witnesses": [],
        "motif_witnesses": [],
        "readiness_report_digest": None,
    }
    if character_witness is not None:
        payload["character_seed"] = character_witness.descriptor_payload()
    return ExistingWorkspaceAdmissionDescriptor(payload, _digest(payload))


def _ensure_stage_witnesses(descriptor: ExistingWorkspaceAdmissionDescriptor, connection: Any,
                            request: ExistingWorkspaceNativeAdmissionRequest, manifest: Any, core_id: UUID,
                            character_witness: CharacterSeedWitness | None) -> ExistingWorkspaceAdmissionDescriptor:
    if descriptor.payload["memory_witnesses"]:
        return descriptor
    report = NativeMigrationRuntimeReadinessPreflight(connection).run(
        MigrationRuntimeReadinessRequest(manifest.legacy_snapshot_id, core_id, (request.scope_plan,), request.qualified_representation_lane)
    )
    if report.reembed_required_count:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_REEMBED_REQUIRED_OUTSIDE_7G5E1_PROFILE")
    if report.quarantine_or_unsupported_count:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_MEMORY_PROFILE_NOT_ADMISSIBLE")
    witnesses = []
    seed_eids = set(character_witness.seed_eids) if character_witness is not None else set()
    for item in report.object_items:
        # B1 intentionally reports admitted evidence-only motif objects too;
        # they are not memory candidates and are handled by B4A below.
        if item.eid is None:
            continue
        allowed = {
            ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED,
            ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED,
        }
        # A source seed from the frozen real writer has no ProvenanceV1.  It
        # is the one and only admissible semantic-facts exception: the exact
        # external witness is revalidated by the Character-only R1 -> R2
        # normalizer before any native successor is published.  All ordinary
        # rows retain B2's previous refusal boundary.
        if item.eid in seed_eids:
            allowed.add(ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED)
        if item.readiness not in allowed:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_MEMORY_PROFILE_NOT_ADMISSIBLE")
        witnesses.append({
            "eid": item.eid, "r1_revision_id": str(item.current_revision_id),
            "normalization_kind": "CHARACTER_SEED" if item.eid in seed_eids else "ORDINARY",
        })
    if seed_eids and {value["eid"] for value in witnesses if value["normalization_kind"] == "CHARACTER_SEED"} != seed_eids:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_SEED_EVIDENCE_INCOMPLETE")
    if not witnesses or not report.motif_items:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_PRIVATE_CORE_EVIDENCE_INCOMPLETE")
    motifs = []
    for item in report.motif_items:
        if item.runtime_motif_id is None:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_MOTIF_PROFILE_NOT_ADMISSIBLE")
        motifs.append({"runtime_motif_id": item.runtime_motif_id, "source_object_id": str(item.motif_object_id), "r1_revision_id": str(item.current_revision_id)})
    descriptor.payload["memory_witnesses"] = sorted(witnesses, key=lambda value: value["eid"])
    descriptor.payload["motif_witnesses"] = sorted(motifs, key=lambda value: value["runtime_motif_id"])
    return descriptor


def _readiness_report(connection: Any, request: ExistingWorkspaceNativeAdmissionRequest, manifest: Any,
                      core_id: UUID, paths: _AdmissionPaths) -> WorkspaceNativeRuntimeReadinessReport:
    return NativeWorkspaceRuntimeReadiness(connection).run(WorkspaceNativeRuntimeReadinessRequest(
        legacy_snapshot_id=manifest.legacy_snapshot_id, expected_native_core_id=core_id,
        native_core_database_path=paths.core_path, scope_plans=(request.scope_plan,),
        target_lane=request.qualified_representation_lane, expected_workspace_ids=(request.workspace_id,),
        staging_feature_posture=request.staging_feature_posture,
        production_feature_posture=request.production_feature_posture,
        qualification_embedder_identity=request.qualification_embedder_identity,
        post_write_configuration=request.post_write_configuration,
        retained_side_store_eid_references=request.retained_side_store_eid_references,
        retained_side_store_eid_observations=request.retained_side_store_eid_observations,
        observed_file_roots=(paths.snapshot_root,),
    ))


def _stage_complete(descriptor: ExistingWorkspaceAdmissionDescriptor, stage: str) -> ExistingWorkspaceAdmissionDescriptor:
    values = descriptor.payload["stages_complete"]
    if stage not in values:
        values.append(stage)
    return descriptor


def _complete_descriptor(descriptor: ExistingWorkspaceAdmissionDescriptor, report: WorkspaceNativeRuntimeReadinessReport) -> ExistingWorkspaceAdmissionDescriptor:
    descriptor.payload["admission_state"] = _COMPLETE
    descriptor.payload["readiness_report_digest"] = report.report_digest
    descriptor.payload["readiness_counts"] = {
        "memory": len(report.memory_items), "motif": len(report.motif_items),
        "b3a_memory": report.b3a_ready_memory_count, "b4a_motif": report.b4a_ready_motif_count,
    }
    _stage_complete(descriptor, "B5")
    return descriptor


def _write_descriptor(path: Path, payload: dict[str, Any]) -> None:
    canonical = _canonical(payload)
    wrapped = _canonical({"descriptor_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(), "payload": payload}) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(wrapped, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _verify_descriptor_matches_request(descriptor: ExistingWorkspaceAdmissionDescriptor, request: ExistingWorkspaceNativeAdmissionRequest) -> None:
    expected = {
        "profile": _CHARACTER_PROFILE if request.character_seed_id is not None else _PROFILE,
        "admission_key": request.admission_key,
        "legacy_source_namespace_id": str(request.legacy_source_namespace_id),
        "legacy_source_namespace_key": request.legacy_source_namespace_key,
        "workspace_id": request.workspace_id,
        "agent_id": request.agent_id,
        "scope_plan": _scope_payload(request.scope_plan),
        "scope_plan_digest": _digest(_scope_payload(request.scope_plan)),
        "representation_lane": _lane_payload(request.qualified_representation_lane),
        "unknown_semantic_scope_id": str(request.unknown_semantic_scope_id),
        "shared_domain_admission": False,
    }
    for key, value in expected.items():
        if descriptor.payload.get(key) != value:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_REQUEST_MISMATCH")
    character = descriptor.character_seed_witness
    if request.character_seed_id is None:
        if character is not None:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_REQUEST_MISMATCH")
    elif character is None or character.seed_id != request.character_seed_id:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_REQUEST_MISMATCH")


def _verify_descriptor_snapshot(descriptor: ExistingWorkspaceAdmissionDescriptor, manifest: Any, path: Path) -> None:
    if descriptor.payload.get("legacy_snapshot_id") != str(manifest.legacy_snapshot_id) or descriptor.payload.get("legacy_snapshot_manifest_digest") != _file_digest(path):
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_SNAPSHOT_DESCRIPTOR_MISMATCH")


def _ensure_explicit_namespaces(connection: Any, request: ExistingWorkspaceNativeAdmissionRequest) -> None:
    identities = (request.target_identity_namespace_id, request.motif_identity_namespace_id, request.membership_identity_namespace_id)
    for ordinal, value in enumerate(dict.fromkeys(identities)):
        _ensure_namespace_row(connection, "identity_namespaces", "identity_namespace_id", value, f"7G5E1:{request.admission_key}:identity:{ordinal}", with_reserved=True)
    scopes = (request.target_semantic_scope_id, request.unknown_semantic_scope_id)
    for ordinal, value in enumerate(dict.fromkeys(scopes)):
        _ensure_namespace_row(connection, "semantic_scopes", "semantic_scope_id", value, f"7G5E1:{request.admission_key}:scope:{ordinal}", with_reserved=True)
    _ensure_namespace_row(connection, "idempotency_namespaces", "idempotency_namespace_id", request.idempotency_namespace_id, f"7G5E1:{request.admission_key}:idempotency", with_reserved=False)
    _ensure_namespace_row(connection, "legacy_source_namespaces", "legacy_source_namespace_id", request.motif_alias_namespace_id, f"7G5E1:{request.admission_key}:motif-alias", with_reserved=True)


def _ensure_namespace_row(connection: Any, table: str, column: str, value: UUID, key: str, *, with_reserved: bool) -> None:
    row = connection.execute(f"SELECT * FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)).fetchone()
    expected = (native_id_to_bytes(value), key, 0) if with_reserved else (native_id_to_bytes(value), key)
    if row is None:
        placeholders = "?,?,0" if with_reserved else "?,?"
        connection.execute(f"INSERT INTO {table} VALUES ({placeholders})", expected[:-1] if with_reserved else expected)
    elif tuple(row) != expected:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_NAMESPACE_IDENTITY_MISMATCH")


def _create_profile_snapshot(request: ExistingWorkspaceNativeAdmissionRequest, paths: _AdmissionPaths) -> None:
    private = paths.source_workspace_root / "agents" / request.agent_id / "private"
    nodes = private / "nodes.jsonl"
    embeddings = private / "embeddings"
    metadata = paths.source_workspace_root / "workspace_meta.json"
    motifs = paths.source_workspace_root / "domains" / request.motif_domain_id / "motifs.json"
    if not nodes.is_file() or not embeddings.is_dir() or not (embeddings / "manifest.json").is_file() or not motifs.is_file():
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_PRIVATE_CORE_EVIDENCE_INCOMPLETE")
    paths.snapshot_root.mkdir()
    _copy_current_private_nodes(nodes, paths.snapshot_root / "nodes.jsonl")
    edges = private / "edges.jsonl"
    if edges.is_file():
        shutil.copy2(edges, paths.snapshot_root / "edges.jsonl")
    shutil.copytree(embeddings, paths.snapshot_root / "embeddings")
    workspace = paths.snapshot_root / "workspaces" / request.workspace_id
    workspace.mkdir(parents=True)
    shutil.copy2(metadata, workspace / "workspace_meta.json")
    motif_target = workspace / "domains" / request.motif_domain_id
    motif_target.mkdir(parents=True)
    shutil.copy2(motifs, motif_target / "motifs.json")


def _copy_current_private_nodes(source: Path, destination: Path) -> None:
    """Freeze the legacy append log at its own last-record-per-EID semantics.

    ``MemoryGraph`` defines a private node's current state as the final line
    for its EID, while runtime order is first surviving appearance.  A retained
    reinforcement therefore has one embedding-map row but two node-log lines.
    Copying both lines would make the older representation-evidence admission
    try to admit that one map row twice.  This snapshot projection preserves
    the legacy current-state and first-surviving-order rules without touching
    the source, inventing a revision, or selecting a different embedding.
    """
    try:
        raw_lines = source.read_bytes().splitlines()
    except OSError as exc:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_PRIVATE_NODES_UNREADABLE") from exc
    first_order: list[int] = []
    current: dict[int, bytes] = {}
    for raw in raw_lines:
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
            eid = value["eid"] if isinstance(value, dict) else None
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_PRIVATE_NODES_MALFORMED") from exc
        if not isinstance(eid, int) or isinstance(eid, bool) or eid < 0:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_PRIVATE_NODES_MALFORMED")
        if eid not in current:
            first_order.append(eid)
        current[eid] = raw
    if not first_order:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_PRIVATE_NODES_EMPTY")
    destination.write_bytes(b"\n".join(current[eid] for eid in first_order) + b"\n")


def _verify_workspace_lane(request: ExistingWorkspaceNativeAdmissionRequest, root: Path) -> None:
    try:
        metadata = json.loads((root / "workspace_meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_EMBEDDING_LOCK_UNREADABLE") from exc
    lane = request.qualified_representation_lane
    if not isinstance(metadata, dict) or (metadata.get("embed_provider"), metadata.get("embed_model"), metadata.get("embed_dim")) != (lane.provider, lane.model, lane.dimension):
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_EMBEDDING_LANE_MISMATCH")


def _read_character_witness(
    request: ExistingWorkspaceNativeAdmissionRequest, root: Path,
) -> CharacterSeedWitness:
    if request.character_seed_id is None:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_SEED_ID_REQUIRED")
    try:
        return read_legacy_character_seed_witness(
            workspace_root=root, workspace_id=request.workspace_id, agent_id=request.agent_id,
            domain_id=request.motif_domain_id, requested_seed_id=request.character_seed_id,
        )
    except CharacterSeedWitnessRefused as exc:
        raise ExistingWorkspaceAdmissionRefused(exc.code) from exc


def _verify_character_free(request: ExistingWorkspaceNativeAdmissionRequest, root: Path) -> None:
    agent = root / "agents" / request.agent_id
    if (agent / "character_state.json").exists():
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_PROVENANCE_BLOCKED")
    identity = agent / "identity.json"
    if not identity.is_file():
        return
    try:
        value = json.loads(identity.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_PROVENANCE_BLOCKED") from exc
    seed = value.get("seed", {}) if isinstance(value, dict) else {}
    if not isinstance(seed, dict) or any(bool(seed.get(key)) for key in ("seed_id", "seed_text", "character_name")):
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_CHARACTER_PROVENANCE_BLOCKED")


def _verify_motif_profile(request: ExistingWorkspaceNativeAdmissionRequest, root: Path) -> None:
    path = root / "domains" / request.motif_domain_id / "motifs.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        motifs = raw.get("motifs", {}) if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_MOTIF_PROFILE_NOT_ADMISSIBLE") from exc
    if not isinstance(motifs, dict) or not motifs:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_MOTIF_PROFILE_NOT_ADMISSIBLE")
    for motif in motifs.values():
        if not isinstance(motif, dict) or not isinstance(motif.get("members"), list) or len(motif["members"]) > _MAX_SUPPORTED_MOTIF_MEMBERS:
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_MOTIF_RETIREMENT_UNSUPPORTED")


def _raise_if_interrupted(selected: str | None, stage: str) -> None:
    if selected == stage:
        raise RuntimeError(f"forced interruption after committed {stage}")


def _stage_key(request: ExistingWorkspaceNativeAdmissionRequest, stage: str, value: int | str) -> str:
    return f"7G5E1:{request.admission_key}:{stage}:{value}"


def _lane_payload(lane: NativeRepresentationLane) -> dict[str, Any]:
    return {name: getattr(lane, name) for name in lane.__dataclass_fields__}


def _lane_from_payload(value: Any) -> NativeRepresentationLane:
    if not isinstance(value, dict):
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_TAMPERED")
    try:
        return NativeRepresentationLane(**value)
    except (TypeError, ValueError) as exc:
        raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_DESCRIPTOR_TAMPERED") from exc


def _scope_payload(plan: MigrationRuntimeScopePlan) -> dict[str, Any]:
    return {
        "legacy_source_namespace_id": str(plan.legacy_source_namespace_id), "workspace_id": plan.workspace_id,
        "scope_kind": plan.scope_kind, "agent_id": plan.agent_id,
        "target_identity_namespace_id": str(plan.target_identity_namespace_id),
        "target_semantic_scope_id": str(plan.target_semantic_scope_id),
        "motif_alias_namespace_id": str(plan.motif_alias_namespace_id),
        "motif_identity_namespace_id": str(plan.motif_identity_namespace_id),
        "membership_identity_namespace_id": str(plan.membership_identity_namespace_id),
        "idempotency_namespace_id": str(plan.idempotency_namespace_id), "motif_domain_id": plan.motif_domain_id,
    }


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_fingerprint(root: Path) -> str:
    values: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ExistingWorkspaceAdmissionRefused("EXISTING_WORKSPACE_SOURCE_SYMLINK_REFUSED")
        if path.is_file():
            values.append((path.relative_to(root).as_posix(), path.stat().st_size, _file_digest(path)))
    return _digest(values)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
