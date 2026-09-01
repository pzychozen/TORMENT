"""Explicit 7G5E4C multi-scope existing-workspace admission.

This is an administrative coordinator over the qualified B1--B5 services.
It deliberately does not alter the single-private 7G5E1 request or provide a
Fabric selector.  Every source lane is frozen independently, then admitted to
one STAGING core under explicit, non-overlapping identities.
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

from ..character_seed_witness import (
    CharacterSeedWitness, CharacterSeedWitnessRefused, read_legacy_character_seed_witness,
)
from ..compat import NativeMemoryCompatibilityFacade
from ..compat_embedding_reader import NativeCompatEmbeddingReader
from ..connection import open_existing_native_core_connection, open_new_native_core_connection
from ..errors import SubstrateConfigurationError
from ..fabric_native_routing import (
    NativeFabricRoutingScope, prepare_native_fabric_routing_capability,
)
from ..ids import native_id_from_bytes, native_id_to_bytes
from ..motif_runtime_reader import NativeMotifRuntimeReader
from ..native_memory_runtime_access import NativePostWriteMemoryAccess
from ..native_memory_vector_runtime import (
    NativeMemoryVectorRuntime, NativeMemoryVectorRuntimeConfiguration,
    NativeVectorRuntimeEmbedder,
)
from ..native_post_write_runtime import (
    NativePostWriteQualificationConfiguration, prepare_native_fabric_post_write_adapter,
)
from ..runtime_binding import (
    NativeMemoryRuntimeScope, NativeRepresentationLane, prepare_native_memory_runtime_binding,
    validate_fabric_embedder,
)
from ..schema import create_schema, open_schema
from .character_seed_normalization import (
    MigrationCharacterSeedNormalizationRequest, NativeMigrationCharacterSeedNormalizationService,
)
from .rehearsal import MigrationRehearsalConfig, NativeLegacyMigrationRehearsal, _verify_whole_core
from .runtime_motif_projection import (
    MigrationRuntimeMotifProjectionRequest, NativeMigrationRuntimeMotifProjectionService,
)
from .runtime_normalization import (
    MigrationRuntimeNormalizationRequest, NativeMigrationRuntimeNormalizationService,
)
from .runtime_readiness import (
    MigrationRuntimeReadinessRequest, MigrationRuntimeScopePlan,
    NativeMigrationRuntimeReadinessPreflight, ObjectRuntimeReadiness,
)
from .runtime_representation_bootstrap import (
    MigrationRuntimeRepresentationBootstrapRequest,
    NativeMigrationRuntimeRepresentationBootstrapService,
)
from .snapshot import create_snapshot_manifest, load_snapshot_manifest, verify_snapshot
from .workspace_runtime_readiness import (
    NativeWorkspaceRuntimeReadiness, RetainedSideStoreEIDObservation,
    RetainedSideStoreEIDReference, WorkspaceNativeEmbedderIdentity,
    WorkspaceNativeFeaturePosture, WorkspaceNativeRuntimeReadinessRequest,
)


_PROFILE = "EXISTING_WORKSPACE_MULTI_SCOPE_CORE"
_SCHEMA = "TORMENT_EXISTING_WORKSPACE_NATIVE_MULTI_SCOPE_ADMISSION"
_VERSION = 1
_PRIVATE = "PRIVATE_AGENT"
_SHARED = "SHARED_DOMAIN"
_INCOMPLETE = "ADMISSION_INCOMPLETE_RESUMABLE"
_COMPLETE = "ADMISSION_COMPLETE"


class ExistingWorkspaceMultiScopeAdmissionRefused(SubstrateConfigurationError):
    """A typed, fail-closed refusal at the multi-scope administrative seam."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ExistingWorkspaceMultiScopeAdmissionState(StrEnum):
    ADMISSION_INCOMPLETE_RESUMABLE = _INCOMPLETE
    ADMISSION_COMPLETE = _COMPLETE
    RECOVERY_READY = "RECOVERY_READY"


@dataclass(frozen=True)
class ExistingWorkspaceNativeLanePlan:
    """One caller-owned, immutable source-to-native lane binding.

    In particular, source paths and all native namespaces are data, not
    derived from a human EID, a directory name, or another lane.
    """

    workspace_id: str
    scope_kind: str
    legacy_graph_source_path: str | Path
    legacy_source_namespace_id: UUID
    legacy_source_namespace_key: str
    target_identity_namespace_id: UUID
    target_semantic_scope_id: UUID
    motif_alias_namespace_id: UUID
    motif_identity_namespace_id: UUID
    membership_identity_namespace_id: UUID
    idempotency_namespace_id: UUID
    motif_domain_id: str
    representation_lane: NativeRepresentationLane | None = None
    agent_id: str | None = None
    domain_id: str | None = None
    character_seed_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.workspace_id, str) or not self.workspace_id:
            raise ValueError("workspace_id must be non-empty text")
        if not isinstance(self.legacy_graph_source_path, (str, Path)) or not str(self.legacy_graph_source_path):
            raise ValueError("legacy_graph_source_path must be explicit")
        if not isinstance(self.legacy_source_namespace_key, str) or not self.legacy_source_namespace_key:
            raise ValueError("legacy_source_namespace_key must be non-empty text")
        if not isinstance(self.motif_domain_id, str) or not self.motif_domain_id:
            raise ValueError("motif_domain_id must be non-empty text")
        if not isinstance(self.representation_lane, NativeRepresentationLane):
            raise ValueError("representation_lane must be typed")
        for name in (
            "legacy_source_namespace_id", "target_identity_namespace_id",
            "target_semantic_scope_id", "motif_alias_namespace_id",
            "motif_identity_namespace_id", "membership_identity_namespace_id",
            "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, name), UUID):
                raise ValueError(f"{name} must be a UUID")
        if self.scope_kind == _PRIVATE:
            if not isinstance(self.agent_id, str) or not self.agent_id or self.domain_id is not None:
                raise ValueError("PRIVATE_AGENT requires agent_id and forbids domain_id")
        elif self.scope_kind == _SHARED:
            if not isinstance(self.domain_id, str) or not self.domain_id or self.agent_id is not None:
                raise ValueError("SHARED_DOMAIN requires domain_id and forbids agent_id")
            if self.motif_domain_id != self.domain_id:
                raise ValueError("SHARED_DOMAIN motif_domain_id must equal domain_id")
            if self.character_seed_id is not None:
                raise ValueError("SHARED_DOMAIN cannot claim Character seed semantics")
        else:
            raise ValueError("scope_kind must be PRIVATE_AGENT or SHARED_DOMAIN")
        if self.character_seed_id is not None and (
            not isinstance(self.character_seed_id, str) or not self.character_seed_id
        ):
            raise ValueError("character_seed_id must be non-empty text when supplied")

    @property
    def qualifier(self) -> str:
        return self.agent_id if self.scope_kind == _PRIVATE else self.domain_id or ""

    @property
    def scope_plan(self) -> MigrationRuntimeScopePlan:
        return MigrationRuntimeScopePlan(
            legacy_source_namespace_id=self.legacy_source_namespace_id,
            workspace_id=self.workspace_id,
            scope_kind=self.scope_kind,
            agent_id=self.agent_id,
            domain_id=self.domain_id,
            target_identity_namespace_id=self.target_identity_namespace_id,
            target_semantic_scope_id=self.target_semantic_scope_id,
            motif_alias_namespace_id=self.motif_alias_namespace_id,
            motif_identity_namespace_id=self.motif_identity_namespace_id,
            membership_identity_namespace_id=self.membership_identity_namespace_id,
            idempotency_namespace_id=self.idempotency_namespace_id,
            motif_domain_id=self.motif_domain_id,
        )

    def payload(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id, "scope_kind": self.scope_kind,
            "qualifier": self.qualifier,
            "legacy_graph_source_path": str(Path(self.legacy_graph_source_path).expanduser().resolve()),
            "legacy_source_namespace_id": str(self.legacy_source_namespace_id),
            "legacy_source_namespace_key": self.legacy_source_namespace_key,
            "target_identity_namespace_id": str(self.target_identity_namespace_id),
            "target_semantic_scope_id": str(self.target_semantic_scope_id),
            "motif_alias_namespace_id": str(self.motif_alias_namespace_id),
            "motif_identity_namespace_id": str(self.motif_identity_namespace_id),
            "membership_identity_namespace_id": str(self.membership_identity_namespace_id),
            "idempotency_namespace_id": str(self.idempotency_namespace_id),
            "motif_domain_id": self.motif_domain_id,
            "representation_lane": _lane_payload(self.representation_lane),
            "agent_id": self.agent_id, "domain_id": self.domain_id,
            "character_seed_id": self.character_seed_id,
        }


@dataclass(frozen=True)
class ExistingWorkspaceNativeMultiScopeAdmissionRequest:
    """Complete, explicit input to the first multi-scope profile."""

    legacy_workspace_root: str | Path
    workspace_id: str
    native_core_database_path: str | Path
    admission_descriptor_path: str | Path
    snapshot_root: str | Path
    admission_key: str
    lane_plans: tuple[ExistingWorkspaceNativeLanePlan, ...]
    unknown_semantic_scope_id: UUID
    qualified_representation_lane: NativeRepresentationLane
    staging_feature_posture: WorkspaceNativeFeaturePosture
    production_feature_posture: WorkspaceNativeFeaturePosture
    qualification_embedder_identity: WorkspaceNativeEmbedderIdentity
    private_post_write_configuration: NativePostWriteQualificationConfiguration
    retained_side_store_eid_references: tuple[RetainedSideStoreEIDReference, ...] = ()
    retained_side_store_eid_observations: tuple[RetainedSideStoreEIDObservation, ...] = ()

    def __post_init__(self) -> None:
        for name in ("workspace_id", "admission_key"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty text")
        for name in ("legacy_workspace_root", "native_core_database_path", "admission_descriptor_path", "snapshot_root"):
            if not isinstance(getattr(self, name), (str, Path)) or not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be an explicit path")
        if not isinstance(self.lane_plans, tuple) or any(not isinstance(item, ExistingWorkspaceNativeLanePlan) for item in self.lane_plans):
            raise ValueError("lane_plans must contain typed lane plans")
        if not isinstance(self.unknown_semantic_scope_id, UUID):
            raise ValueError("unknown_semantic_scope_id must be UUID")
        if not isinstance(self.qualified_representation_lane, NativeRepresentationLane):
            raise ValueError("qualified_representation_lane must be typed")
        if not isinstance(self.staging_feature_posture, WorkspaceNativeFeaturePosture) or not isinstance(self.production_feature_posture, WorkspaceNativeFeaturePosture):
            raise ValueError("feature postures must be typed")
        if not isinstance(self.qualification_embedder_identity, WorkspaceNativeEmbedderIdentity):
            raise ValueError("qualification_embedder_identity must be typed")
        if not isinstance(self.private_post_write_configuration, NativePostWriteQualificationConfiguration):
            raise ValueError("private_post_write_configuration must be typed")
        if any(plan.workspace_id != self.workspace_id for plan in self.lane_plans):
            raise ValueError("all lane plans must name the requested workspace")
        private = [plan for plan in self.lane_plans if plan.scope_kind == _PRIVATE]
        shared = [plan for plan in self.lane_plans if plan.scope_kind == _SHARED]
        if len(private) != 1 or not shared:
            raise ValueError("the first profile requires exactly one private lane and at least one shared lane")
        if self.ordered_lane_plans != self.lane_plans:
            raise ValueError("lane_plans must be supplied in canonical private-then-shared order")
        if any(plan.representation_lane != self.qualified_representation_lane for plan in self.lane_plans):
            raise ValueError("every lane representation_lane must match the qualified workspace lane")
        _require_distinct_lane_identities(self.lane_plans)

    @property
    def ordered_lane_plans(self) -> tuple[ExistingWorkspaceNativeLanePlan, ...]:
        return tuple(sorted(self.lane_plans, key=lambda plan: (0 if plan.scope_kind == _PRIVATE else 1, plan.qualifier)))


@dataclass(frozen=True)
class ExistingWorkspaceNativeMultiScopeDescriptor:
    payload: dict[str, Any]
    digest: str

    @property
    def state(self) -> ExistingWorkspaceMultiScopeAdmissionState:
        return ExistingWorkspaceMultiScopeAdmissionState(self.payload["admission_state"])

    @property
    def native_core_id(self) -> UUID:
        value = self.payload.get("native_core_id")
        if not isinstance(value, str):
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_CORE_ID_MISSING")
        return UUID(value)

    @property
    def representation_lane(self) -> NativeRepresentationLane:
        return _lane_from_payload(self.payload["representation_lane"])


@dataclass(frozen=True)
class ExistingWorkspaceNativeMultiScopeLaneResult:
    scope_kind: str
    qualifier: str
    memory_count: int
    representation_count: int
    motif_count: int
    membership_count: int
    snapshot_digest: str
    readiness_report_digest: str


@dataclass(frozen=True)
class ExistingWorkspaceNativeMultiScopeAdmissionResult:
    descriptor: ExistingWorkspaceNativeMultiScopeDescriptor
    lane_results: tuple[ExistingWorkspaceNativeMultiScopeLaneResult, ...]
    multi_scope_b5: bool
    resumed: bool


@dataclass
class RecoveredExistingWorkspaceNativeMultiScopeReaders:
    _qualified_connection: Any
    memory: NativeMemoryCompatibilityFacade
    embeddings: NativeCompatEmbeddingReader
    motifs: NativeMotifRuntimeReader
    memory_enumeration: NativePostWriteMemoryAccess

    def close(self) -> None:
        self._qualified_connection.close()

    def __enter__(self) -> "RecoveredExistingWorkspaceNativeMultiScopeReaders":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


@dataclass(frozen=True)
class RecoveredExistingWorkspaceNativeMultiScopeScope:
    """One immutable recovered lane.  It has no writer or legacy fallback."""

    core_database_path: Path
    native_core_id: UUID
    representation_lane: NativeRepresentationLane
    memory_runtime_scope: NativeMemoryRuntimeScope
    fabric_routing_scope: NativeFabricRoutingScope
    character_seed_witness: CharacterSeedWitness | None = None

    def open_readers(self) -> RecoveredExistingWorkspaceNativeMultiScopeReaders:
        qualified = open_existing_native_core_connection(self.core_database_path)
        try:
            metadata = open_schema(qualified.connection, writable=False)
            if native_id_from_bytes(metadata.core_id) != self.native_core_id:
                raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_RECOVERY_WRONG_CORE")
            return RecoveredExistingWorkspaceNativeMultiScopeReaders(
                qualified, NativeMemoryCompatibilityFacade(qualified.connection),
                NativeCompatEmbeddingReader(qualified.connection), NativeMotifRuntimeReader(qualified.connection),
                NativePostWriteMemoryAccess(
                    qualified.connection,
                    legacy_source_namespace_id=self.memory_runtime_scope.legacy_source_namespace_id,
                    expected_dimension=self.representation_lane.dimension,
                ),
            )
        except Exception:
            qualified.close()
            raise

    def new_vector_runtime(self, *, embedder: NativeVectorRuntimeEmbedder) -> NativeMemoryVectorRuntime:
        return NativeMemoryVectorRuntime(
            NativeMemoryVectorRuntimeConfiguration(
                self.core_database_path, self.native_core_id, self.memory_runtime_scope,
                self.representation_lane,
            ),
            embedder=embedder,
        )

    def require_external_character_seed(self, character_store: Any) -> Any:
        witness = self.character_seed_witness
        if witness is None:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_CHARACTER_PROFILE_NOT_ADMITTED")
        if character_store is None or not hasattr(character_store, "load_seed"):
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_CHARACTER_STORE_REQUIRED")
        seed = character_store.load_seed(self.memory_runtime_scope.workspace_id, witness.seed_id)
        if seed is None or not hasattr(seed, "to_dict") or seed.to_dict() != dict(witness.seed_definition):
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_CHARACTER_STORE_SEED_MISMATCH")
        return seed


@dataclass(frozen=True)
class RecoveredExistingWorkspaceNativeMultiScopeRuntime:
    native_core_database_path: Path
    descriptor: ExistingWorkspaceNativeMultiScopeDescriptor
    representation_lane: NativeRepresentationLane
    scopes: tuple[RecoveredExistingWorkspaceNativeMultiScopeScope, ...]
    state: ExistingWorkspaceMultiScopeAdmissionState = ExistingWorkspaceMultiScopeAdmissionState.RECOVERY_READY

    @property
    def workspace_id(self) -> str:
        return self.descriptor.payload["workspace_id"]

    @property
    def native_core_id(self) -> UUID:
        return self.descriptor.native_core_id

    def lookup_private(self, agent_id: str) -> RecoveredExistingWorkspaceNativeMultiScopeScope:
        return self._lookup(_PRIVATE, agent_id)

    def lookup_shared(self, domain_id: str) -> RecoveredExistingWorkspaceNativeMultiScopeScope:
        return self._lookup(_SHARED, domain_id)

    def _lookup(self, kind: str, qualifier: str) -> RecoveredExistingWorkspaceNativeMultiScopeScope:
        matches = [scope for scope in self.scopes if scope.memory_runtime_scope.scope_kind == kind and scope.memory_runtime_scope.qualifier == qualifier]
        if len(matches) != 1:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_RECOVERY_SCOPE_NOT_FOUND")
        return matches[0]


class ExistingWorkspaceNativeMultiScopeAdmissionService:
    """Coordinate frozen private and shared lanes into one qualified core."""

    def admit(
        self, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, *,
        _test_interrupt_after: str | None = None,
        _test_lose_response_after: str | None = None,
    ) -> ExistingWorkspaceNativeMultiScopeAdmissionResult:
        if not isinstance(request, ExistingWorkspaceNativeMultiScopeAdmissionRequest):
            raise ValueError("request must be ExistingWorkspaceNativeMultiScopeAdmissionRequest")
        if _test_interrupt_after not in {None, "PRIVATE_B2", "BETWEEN_PRIVATE_AND_SHARED", "SHARED_B3A", "SHARED_B4A", "BEFORE_B5", "B5"}:
            raise ValueError("unknown multi-scope interruption point")
        if _test_lose_response_after not in {None, "B2", "B3A", "B4A", "B5"}:
            raise ValueError("unknown multi-scope response-loss point")
        paths = _paths(request)
        _validate_profile_and_topology(request, paths.workspace_root)
        descriptor = _load_or_create_descriptor(request, paths)
        resumed = descriptor is not None
        source_fingerprint = _tree_fingerprint(paths.workspace_root)
        if descriptor is None:
            descriptor = _new_descriptor(request, paths.workspace_root, source_fingerprint)
            _write_descriptor(paths.descriptor_path, descriptor.payload)
        else:
            _verify_descriptor_matches_request(descriptor, request)
            if descriptor.payload.get("source_workspace_fingerprint") != source_fingerprint:
                raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_SOURCE_EVIDENCE_MISMATCH")

        _verify_lane_snapshots(descriptor, request)
        qualified, core_id = _open_or_create_core(paths, descriptor)
        try:
            connection = qualified.connection
            _ensure_namespaces(connection, request)
            for index, plan in enumerate(request.ordered_lane_plans):
                lane = _lane_descriptor(descriptor.payload, plan)
                manifest = load_snapshot_manifest(Path(lane["snapshot_manifest_path"]))
                verify_snapshot(snapshot_root=lane["snapshot_root"], manifest=manifest)
                NativeLegacyMigrationRehearsal(connection).run(
                    snapshot_root=lane["snapshot_root"], manifest_path=lane["snapshot_manifest_path"],
                    config=MigrationRehearsalConfig(
                        core_id, plan.idempotency_namespace_id, plan.target_identity_namespace_id,
                        plan.membership_identity_namespace_id, request.unknown_semantic_scope_id,
                    ),
                )
                witness = _character_witness_from_lane(lane, plan)
                _ensure_lane_witnesses(connection, lane, plan, request.qualified_representation_lane, manifest, core_id, witness)
                _write_descriptor(paths.descriptor_path, descriptor.payload)

                _run_b2(connection, lane, plan, request, manifest, core_id, witness,
                        lose_response=_test_lose_response_after == "B2")
                _complete_lane_stage(lane, "B2")
                _write_descriptor(paths.descriptor_path, descriptor.payload)
                if index == 0 and _test_interrupt_after == "PRIVATE_B2":
                    raise RuntimeError("forced interruption after private B2")

                _run_b3a(connection, lane, plan, request, manifest, core_id,
                         lose_response=_test_lose_response_after == "B3A")
                _complete_lane_stage(lane, "B3A")
                _write_descriptor(paths.descriptor_path, descriptor.payload)
                if plan.scope_kind == _SHARED and _test_interrupt_after == "SHARED_B3A":
                    raise RuntimeError("forced interruption during shared B3A")

                _run_b4a(connection, lane, plan, request, manifest, core_id,
                         lose_response=_test_lose_response_after == "B4A")
                _complete_lane_stage(lane, "B4A")
                _write_descriptor(paths.descriptor_path, descriptor.payload)
                if plan.scope_kind == _SHARED and _test_interrupt_after == "SHARED_B4A":
                    raise RuntimeError("forced interruption during shared B4A")
                if index == 0 and _test_interrupt_after == "BETWEEN_PRIVATE_AND_SHARED":
                    raise RuntimeError("forced interruption between private and shared lanes")

            if _test_interrupt_after == "BEFORE_B5":
                raise RuntimeError("forced interruption before whole-workspace B5")
            reports = _run_whole_workspace_b5(connection, descriptor, request, core_id, paths.workspace_root)
            _record_b5(descriptor.payload, request, reports, connection)
            _write_descriptor(paths.descriptor_path, descriptor.payload)
            completed = load_existing_workspace_multi_scope_admission_descriptor(paths.descriptor_path)
            if _test_interrupt_after == "B5" or _test_lose_response_after == "B5":
                raise RuntimeError("forced response loss after committed multi-scope B5")
            if _tree_fingerprint(paths.workspace_root) != source_fingerprint:
                raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_SOURCE_EVIDENCE_MISMATCH")
            return ExistingWorkspaceNativeMultiScopeAdmissionResult(
                completed, _lane_results(completed), True, resumed,
            )
        finally:
            qualified.close()


@dataclass(frozen=True)
class _Paths:
    workspace_root: Path
    core_path: Path
    descriptor_path: Path
    snapshot_root: Path


def _paths(request: ExistingWorkspaceNativeMultiScopeAdmissionRequest) -> _Paths:
    source = Path(request.legacy_workspace_root).expanduser().resolve()
    workspace = source if (source / "workspace_meta.json").is_file() else source / "workspaces" / request.workspace_id
    if not workspace.is_dir() or not (workspace / "workspace_meta.json").is_file():
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_SOURCE_WORKSPACE_NOT_FOUND")
    core = Path(request.native_core_database_path).expanduser().resolve()
    descriptor = Path(request.admission_descriptor_path).expanduser().resolve()
    snapshot = Path(request.snapshot_root).expanduser().resolve()
    if core.suffix.lower() != ".db" or not core.parent.is_dir() or not descriptor.parent.is_dir() or not snapshot.parent.is_dir():
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_EXTERNAL_DESTINATION_PARENT_REQUIRED")
    for value, code in ((core, "MULTI_SCOPE_DESTINATION_INSIDE_SOURCE"), (descriptor, "MULTI_SCOPE_DESCRIPTOR_INSIDE_SOURCE"), (snapshot, "MULTI_SCOPE_SNAPSHOT_INSIDE_SOURCE")):
        if _is_within(value, workspace):
            raise ExistingWorkspaceMultiScopeAdmissionRefused(code)
    return _Paths(workspace, core, descriptor, snapshot)


def _validate_profile_and_topology(request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, workspace: Path) -> None:
    lane = request.qualified_representation_lane
    if (lane.representation_class, lane.generation, lane.derivation_contract_version, lane.encoding_id, lane.dtype) != (
        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
    ):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_UNQUALIFIED_REPRESENTATION_LANE")
    try:
        metadata = json.loads((workspace / "workspace_meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_EMBEDDING_LOCK_UNREADABLE") from exc
    if not isinstance(metadata, dict) or (metadata.get("embed_provider"), metadata.get("embed_model"), metadata.get("embed_dim")) != (lane.provider, lane.model, lane.dimension):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_EMBEDDING_LANE_MISMATCH")
    for plan in request.ordered_lane_plans:
        expected = workspace / "agents" / (plan.agent_id or "") / "private" if plan.scope_kind == _PRIVATE else workspace / "domains" / (plan.domain_id or "") / "shared"
        supplied = Path(plan.legacy_graph_source_path).expanduser().resolve()
        if supplied != expected.resolve():
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_LANE_PATH_MISMATCH")
        if not expected.is_dir() or not (expected / "nodes.jsonl").is_file() or not (expected / "embeddings" / "manifest.json").is_file():
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_LANE_CORE_EVIDENCE_INCOMPLETE")
        motif = workspace / "domains" / plan.motif_domain_id / "motifs.json"
        if not motif.is_file():
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_MOTIF_EVIDENCE_INCOMPLETE")


def _require_distinct_lane_identities(plans: tuple[ExistingWorkspaceNativeLanePlan, ...]) -> None:
    for name in (
        "legacy_source_namespace_id", "target_identity_namespace_id", "target_semantic_scope_id",
        "motif_alias_namespace_id", "motif_identity_namespace_id", "membership_identity_namespace_id",
        "idempotency_namespace_id",
    ):
        values = [getattr(plan, name) for plan in plans]
        if len(set(values)) != len(values):
            raise ValueError(f"every lane requires a distinct {name}")
    qualifiers = [(plan.scope_kind, plan.qualifier) for plan in plans]
    if len(set(qualifiers)) != len(qualifiers):
        raise ValueError("duplicate scope qualifier")


def _load_or_create_descriptor(request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, paths: _Paths) -> ExistingWorkspaceNativeMultiScopeDescriptor | None:
    if paths.descriptor_path.exists():
        return load_existing_workspace_multi_scope_admission_descriptor(paths.descriptor_path)
    if paths.core_path.exists():
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_FIRST_DESTINATION_MUST_BE_NEW")
    if paths.snapshot_root.exists():
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_FIRST_SNAPSHOT_DESTINATION_MUST_BE_NEW")
    return None


def _new_descriptor(request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, workspace: Path, source_fingerprint: str) -> ExistingWorkspaceNativeMultiScopeDescriptor:
    request_snapshot_root = Path(request.snapshot_root).expanduser().resolve()
    request_snapshot_root.mkdir()
    lanes: list[dict[str, Any]] = []
    for index, plan in enumerate(request.ordered_lane_plans):
        token = f"{index:02d}-{plan.scope_kind.lower()}-{plan.qualifier}"
        snapshot_root = request_snapshot_root / "lanes" / token
        manifest_path = request_snapshot_root / "manifests" / f"{token}.json"
        _create_lane_snapshot(workspace, plan, snapshot_root)
        manifest = create_snapshot_manifest(
            snapshot_root=snapshot_root, manifest_path=manifest_path,
            legacy_source_namespace_id=plan.legacy_source_namespace_id,
            legacy_source_namespace_key=plan.legacy_source_namespace_key,
            capture_label=f"7G5E4C {plan.scope_kind} {plan.qualifier}",
        )
        lane = {
            "plan": plan.payload(), "snapshot_root": str(snapshot_root),
            "snapshot_manifest_path": str(manifest_path),
            "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
            "snapshot_digest": _file_digest(manifest_path),
            "source_fingerprint": _lane_source_fingerprint(workspace, plan),
            "stages_complete": [], "memory_witnesses": [], "motif_witnesses": [],
            "readiness_report_digest": None, "readiness_counts": None,
        }
        if plan.character_seed_id is not None:
            lane["character_seed"] = _read_character_witness(workspace, plan).descriptor_payload()
        lanes.append(lane)
    payload: dict[str, Any] = {
        "descriptor_schema": _SCHEMA, "descriptor_version": _VERSION, "profile": _PROFILE,
        "admission_state": _INCOMPLETE, "admission_key": request.admission_key,
        "workspace_id": request.workspace_id, "source_workspace_fingerprint": source_fingerprint,
        "native_core_id": None, "schema_version": [1, 2],
        "unknown_semantic_scope_id": str(request.unknown_semantic_scope_id),
        "representation_lane": _lane_payload(request.qualified_representation_lane),
        "lane_plan_digest": _digest([plan.payload() for plan in request.ordered_lane_plans]),
        "declared_lane_count": len(lanes), "lanes": lanes,
        "retained_side_store_digest": _retained_side_store_digest(workspace, request),
        "bridge_compatibility_observation": None, "bridge_compatibility_observation_digest": None,
        "multi_scope_b5": None,
    }
    return ExistingWorkspaceNativeMultiScopeDescriptor(payload, _digest(payload))


def _create_lane_snapshot(workspace: Path, plan: ExistingWorkspaceNativeLanePlan, destination: Path) -> None:
    source = Path(plan.legacy_graph_source_path).expanduser().resolve()
    destination.mkdir(parents=True)
    _copy_current_nodes(source / "nodes.jsonl", destination / "nodes.jsonl")
    edges = source / "edges.jsonl"
    if edges.is_file():
        shutil.copy2(edges, destination / "edges.jsonl")
    shutil.copytree(source / "embeddings", destination / "embeddings")
    snapshot_workspace = destination / "workspaces" / plan.workspace_id
    snapshot_workspace.mkdir(parents=True)
    shutil.copy2(workspace / "workspace_meta.json", snapshot_workspace / "workspace_meta.json")
    motif_target = snapshot_workspace / "domains" / plan.motif_domain_id
    motif_target.mkdir(parents=True)
    shutil.copy2(workspace / "domains" / plan.motif_domain_id / "motifs.json", motif_target / "motifs.json")


def _copy_current_nodes(source: Path, destination: Path) -> None:
    try:
        raw_lines = source.read_bytes().splitlines()
    except OSError as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_NODES_UNREADABLE") from exc
    first: list[int] = []
    current: dict[int, bytes] = {}
    for raw in raw_lines:
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
            eid = value["eid"] if isinstance(value, dict) else None
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_NODES_MALFORMED") from exc
        if not isinstance(eid, int) or isinstance(eid, bool) or eid < 0:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_NODES_MALFORMED")
        if eid not in current:
            first.append(eid)
        current[eid] = raw
    if not first:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_NODES_EMPTY")
    destination.write_bytes(b"\n".join(current[eid] for eid in first) + b"\n")


def _open_or_create_core(paths: _Paths, descriptor: ExistingWorkspaceNativeMultiScopeDescriptor) -> tuple[Any, UUID]:
    if paths.core_path.exists():
        qualified = open_existing_native_core_connection(paths.core_path)
        actual = native_id_from_bytes(open_schema(qualified.connection, writable=False).core_id)
        expected = descriptor.payload.get("native_core_id")
        if expected is not None and expected != str(actual):
            qualified.close()
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_NATIVE_CORE_ID_MISMATCH")
        if expected is None:
            descriptor.payload["native_core_id"] = str(actual)
            _write_descriptor(paths.descriptor_path, descriptor.payload)
        return qualified, actual
    if descriptor.payload.get("native_core_id") is not None:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_NATIVE_CORE_MISSING")
    qualified = open_new_native_core_connection(paths.core_path)
    try:
        actual = native_id_from_bytes(create_schema(qualified.connection).core_id)
        descriptor.payload["native_core_id"] = str(actual)
        _write_descriptor(paths.descriptor_path, descriptor.payload)
        return qualified, actual
    except Exception:
        qualified.close()
        raise


def _ensure_namespaces(connection: Any, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest) -> None:
    for lane_number, plan in enumerate(request.ordered_lane_plans):
        for ordinal, value in enumerate((plan.target_identity_namespace_id, plan.motif_identity_namespace_id, plan.membership_identity_namespace_id)):
            _ensure_namespace(connection, "identity_namespaces", "identity_namespace_id", value, f"7G5E4C:{request.admission_key}:{lane_number}:identity:{ordinal}", reserved=True)
        _ensure_namespace(connection, "semantic_scopes", "semantic_scope_id", plan.target_semantic_scope_id, f"7G5E4C:{request.admission_key}:{lane_number}:scope", reserved=True)
        _ensure_namespace(connection, "idempotency_namespaces", "idempotency_namespace_id", plan.idempotency_namespace_id, f"7G5E4C:{request.admission_key}:{lane_number}:idempotency", reserved=False)
        _ensure_namespace(connection, "legacy_source_namespaces", "legacy_source_namespace_id", plan.motif_alias_namespace_id, f"7G5E4C:{request.admission_key}:{lane_number}:motif-alias", reserved=True)
    _ensure_namespace(connection, "semantic_scopes", "semantic_scope_id", request.unknown_semantic_scope_id, f"7G5E4C:{request.admission_key}:unknown", reserved=True)


def _ensure_namespace(connection: Any, table: str, column: str, value: UUID, key: str, *, reserved: bool) -> None:
    row = connection.execute(f"SELECT * FROM {table} WHERE {column}=?", (native_id_to_bytes(value),)).fetchone()
    expected = (native_id_to_bytes(value), key, 0) if reserved else (native_id_to_bytes(value), key)
    if row is None:
        connection.execute(f"INSERT INTO {table} VALUES ({'?,?,0' if reserved else '?,?'})", expected[:-1] if reserved else expected)
    elif tuple(row) != expected:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_NAMESPACE_IDENTITY_MISMATCH")


def _ensure_lane_witnesses(connection: Any, lane: dict[str, Any], plan: ExistingWorkspaceNativeLanePlan, target: NativeRepresentationLane, manifest: Any, core_id: UUID, character_witness: CharacterSeedWitness | None) -> None:
    if lane["memory_witnesses"]:
        return
    report = NativeMigrationRuntimeReadinessPreflight(connection).run(
        MigrationRuntimeReadinessRequest(manifest.legacy_snapshot_id, core_id, (plan.scope_plan,), target)
    )
    if report.reembed_required_count:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_REEMBED_REQUIRED")
    if report.quarantine_or_unsupported_count:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_MEMORY_PROFILE_NOT_ADMISSIBLE")
    seed_eids = set(character_witness.seed_eids) if character_witness else set()
    memories: list[dict[str, Any]] = []
    for item in report.object_items:
        if item.eid is None:
            continue
        allowed = {ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED, ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED}
        if item.eid in seed_eids:
            allowed.add(ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED)
        if item.readiness not in allowed:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_MEMORY_PROFILE_NOT_ADMISSIBLE")
        memories.append({"eid": item.eid, "r1_revision_id": str(item.current_revision_id), "normalization_kind": "CHARACTER_SEED" if item.eid in seed_eids else "ORDINARY"})
    motifs = []
    for item in report.motif_items:
        if item.runtime_motif_id is None:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_MOTIF_PROFILE_NOT_ADMISSIBLE")
        motifs.append({"runtime_motif_id": item.runtime_motif_id, "source_object_id": str(item.motif_object_id), "r1_revision_id": str(item.current_revision_id)})
    if not memories or not motifs:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_LANE_EVIDENCE_INCOMPLETE")
    lane["memory_witnesses"] = sorted(memories, key=lambda value: value["eid"])
    lane["motif_witnesses"] = sorted(motifs, key=lambda value: value["runtime_motif_id"])


def _run_b2(connection: Any, lane: dict[str, Any], plan: ExistingWorkspaceNativeLanePlan, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, manifest: Any, core_id: UUID, character_witness: CharacterSeedWitness | None, *, lose_response: bool) -> None:
    ordinary = NativeMigrationRuntimeNormalizationService(connection)
    character = NativeMigrationCharacterSeedNormalizationService(connection) if character_witness else None
    for index, witness in enumerate(lane["memory_witnesses"]):
        base = MigrationRuntimeNormalizationRequest(
            lane["snapshot_root"], lane["snapshot_manifest_path"], manifest.legacy_snapshot_id,
            plan.legacy_source_namespace_id, core_id, witness["eid"], UUID(witness["r1_revision_id"]),
            (plan.scope_plan,), plan.idempotency_namespace_id, _stage_key(request, plan, "B2", witness["eid"]),
        )
        if witness["normalization_kind"] == "CHARACTER_SEED":
            if character is None or character_witness is None:
                raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_CHARACTER_WITNESS_REQUIRED")
            result = character.normalize_character_seed(MigrationCharacterSeedNormalizationRequest(base, character_witness), _test_lose_response_after_commit=lose_response and index == 0)
        else:
            result = ordinary.normalize_legacy_core_memory(base, _test_lose_response_after_commit=lose_response and index == 0)
        witness["r2_revision_id"] = str(result.revision_id)


def _run_b3a(connection: Any, lane: dict[str, Any], plan: ExistingWorkspaceNativeLanePlan, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, manifest: Any, core_id: UUID, *, lose_response: bool) -> None:
    service = NativeMigrationRuntimeRepresentationBootstrapService(connection)
    for index, witness in enumerate(lane["memory_witnesses"]):
        result = service.bootstrap_from_legacy_capture(MigrationRuntimeRepresentationBootstrapRequest(
            lane["snapshot_root"], lane["snapshot_manifest_path"], manifest.legacy_snapshot_id,
            plan.legacy_source_namespace_id, core_id, witness["eid"], UUID(witness["r1_revision_id"]),
            UUID(witness["r2_revision_id"]), request.qualified_representation_lane,
            plan.idempotency_namespace_id, _stage_key(request, plan, "B3A", witness["eid"]),
        ), _test_lose_response_after_ready=lose_response and index == 0)
        witness["representation_id"] = str(result.representation_id)


def _run_b4a(connection: Any, lane: dict[str, Any], plan: ExistingWorkspaceNativeLanePlan, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, manifest: Any, core_id: UUID, *, lose_response: bool) -> None:
    service = NativeMigrationRuntimeMotifProjectionService(connection)
    for index, witness in enumerate(lane["motif_witnesses"]):
        result = service.project_lane_preserving_legacy_motif(MigrationRuntimeMotifProjectionRequest(
            lane["snapshot_root"], lane["snapshot_manifest_path"], manifest.legacy_snapshot_id,
            plan.legacy_source_namespace_id, core_id, witness["runtime_motif_id"],
            UUID(witness["source_object_id"]), UUID(witness["r1_revision_id"]), (plan.scope_plan,),
            request.qualified_representation_lane, plan.idempotency_namespace_id,
            _stage_key(request, plan, "B4A", witness["runtime_motif_id"]),
        ), _test_lose_response_after_commit=lose_response and index == 0)
        witness["target_object_id"] = str(result.motif_object_id)


def _run_whole_workspace_b5(connection: Any, descriptor: ExistingWorkspaceNativeMultiScopeDescriptor, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, core_id: UUID, workspace: Path) -> tuple[Any, ...]:
    """Run B5 per frozen source, then jointly construct all scope bindings.

    B5's original snapshot evidence model is intentionally one source
    namespace per report.  The joint binding/capability below is the actual
    multi-scope closure: all plans must construct together after every
    individual B5 closure has succeeded.
    """
    reports: list[Any] = []
    for plan in request.ordered_lane_plans:
        lane = _lane_descriptor(descriptor.payload, plan)
        manifest = load_snapshot_manifest(lane["snapshot_manifest_path"])
        if plan.scope_kind == _PRIVATE:
            report = NativeWorkspaceRuntimeReadiness(connection).run(WorkspaceNativeRuntimeReadinessRequest(
                legacy_snapshot_id=manifest.legacy_snapshot_id, expected_native_core_id=core_id,
                native_core_database_path=request.native_core_database_path, scope_plans=(plan.scope_plan,),
                target_lane=request.qualified_representation_lane, expected_workspace_ids=(request.workspace_id,),
                staging_feature_posture=request.staging_feature_posture,
                production_feature_posture=request.production_feature_posture,
                qualification_embedder_identity=request.qualification_embedder_identity,
                post_write_configuration=request.private_post_write_configuration,
                retained_side_store_eid_references=request.retained_side_store_eid_references,
                retained_side_store_eid_observations=request.retained_side_store_eid_observations,
                observed_file_roots=(workspace,),
            ))
            if not report.core_staging_runtime_ready:
                raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_B5_LANE_CLOSURE_INCOMPLETE")
        else:
            report = _shared_b5_read_only_closure(connection, plan, manifest, core_id, request.qualified_representation_lane)
        reports.append(report)
    scopes = tuple(_runtime_scope(plan) for plan in request.ordered_lane_plans)
    try:
        binding = prepare_native_memory_runtime_binding(
            connection=connection, core_database_path=request.native_core_database_path,
            expected_core_id=core_id, scope_bindings=scopes,
            representation_lane=request.qualified_representation_lane,
        )
        validate_fabric_embedder(binding, request.qualification_embedder_identity)
        capability = prepare_native_fabric_routing_capability(
            binding=binding, connection=connection,
            routing_scopes=tuple(_routing_scope(plan) for plan in request.ordered_lane_plans),
            expected_core_id=core_id,
        )
        # A3D's post-write adapter is intentionally private-only.  It is
        # prepared once for the admitted private lane; shared writes remain
        # outside this phase while their read/motif closure is qualified above.
        prepare_native_fabric_post_write_adapter(
            capability=capability, configuration=request.private_post_write_configuration,
        )
    except (SubstrateConfigurationError, ValueError) as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_B5_JOINT_BINDING_REFUSED") from exc
    return tuple(reports)


def _record_b5(payload: dict[str, Any], request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, reports: tuple[Any, ...], connection: Any) -> None:
    for plan, report in zip(request.ordered_lane_plans, reports, strict=True):
        lane = _lane_descriptor(payload, plan)
        lane["readiness_report_digest"] = _report_digest(report)
        lane["readiness_counts"] = {
            "memory": _report_memory_count(report), "representation": _report_representation_count(report),
            "motif": _report_motif_count(report), "membership": _report_membership_count(report),
        }
        _complete_lane_stage(lane, "B5")
    payload["bridge_compatibility_observation"] = _observe_bridges(connection, payload)
    payload["bridge_compatibility_observation_digest"] = _digest(payload["bridge_compatibility_observation"])
    payload["multi_scope_b5"] = {
        "scope_plan_digest": _digest([plan.scope_plan.intent() for plan in request.ordered_lane_plans]),
        "lane_report_digests": [_report_digest(report) for report in reports], "joint_binding_constructible": True,
    }
    payload["admission_state"] = _COMPLETE


def _shared_b5_read_only_closure(
    connection: Any, plan: ExistingWorkspaceNativeLanePlan, manifest: Any, core_id: UUID,
    target_lane: NativeRepresentationLane,
) -> dict[str, Any]:
    """B5-equivalent read closure for a shared lane with no write adapter.

    The established A3D post-write configuration intentionally rejects shared
    writes.  Requiring that private-only adapter here would falsely claim a
    new shared-write route.  This invokes the same B1 and B5 memory/motif
    postconditions, followed by the whole-core invariant, but creates nothing.
    """
    before_changes = connection.total_changes
    before_core = _core_count_fingerprint(connection)
    b1 = NativeMigrationRuntimeReadinessPreflight(connection).run(
        MigrationRuntimeReadinessRequest(manifest.legacy_snapshot_id, core_id, (plan.scope_plan,), target_lane)
    )
    observer = NativeWorkspaceRuntimeReadiness(connection)
    observation_request = type("_SharedB5Observation", (), {"target_lane": target_lane, "scope_plans": (plan.scope_plan,)})()
    blockers: list[Any] = []
    memory_items = observer._memory_items(b1, observation_request, blockers)
    motif_items, member_closure = observer._motif_items(b1, observation_request, memory_items, blockers)
    _verify_whole_core(connection)
    memory_ready = bool(memory_items) and all(
        item.readiness is ObjectRuntimeReadiness.RUNTIME_READY_AS_IS and not item.reason_codes
        for item in memory_items
    )
    motif_ready = bool(motif_items) and all(item.readiness.value == "RUNTIME_READY_AS_IS" for item in motif_items)
    if not (b1.deploy_gate_ready and memory_ready and motif_ready and member_closure):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_B5_SHARED_LANE_CLOSURE_INCOMPLETE")
    if before_changes != connection.total_changes or before_core != _core_count_fingerprint(connection):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_B5_SHARED_NOT_READ_ONLY")
    values = {
        "kind": "SHARED_DOMAIN_READ_ONLY_B5", "snapshot_id": str(manifest.legacy_snapshot_id),
        "scope_plan": plan.scope_plan.intent(),
        "memory": [(str(item.object_id), item.eid, item.lineage.value) for item in memory_items],
        "motif": [(str(item.source_motif_object_id), item.runtime_motif_id, item.member_count) for item in motif_items],
    }
    values["report_digest"] = _digest(values)
    return values


def _core_count_fingerprint(connection: Any) -> tuple[tuple[str, int], ...]:
    tables = (
        "objects", "object_revisions", "relationships", "relationship_revisions", "representations",
        "representation_current_state", "integrity_expectations", "integrity_measurements",
        "operations", "semantic_transitions", "legacy_admission_records",
    )
    return tuple((table, connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]) for table in tables)


def _report_digest(report: Any) -> str:
    return report.report_digest if hasattr(report, "report_digest") else report["report_digest"]


def _report_memory_count(report: Any) -> int:
    return len(report.memory_items) if hasattr(report, "memory_items") else len(report["memory"])


def _report_representation_count(report: Any) -> int:
    if hasattr(report, "b3a_ready_memory_count"):
        return report.b3a_ready_memory_count
    return len(report["memory"])


def _report_motif_count(report: Any) -> int:
    return len(report.motif_items) if hasattr(report, "motif_items") else len(report["motif"])


def _report_membership_count(report: Any) -> int:
    return sum(item.member_count for item in report.motif_items) if hasattr(report, "motif_items") else sum(item[2] for item in report["motif"])


def _observe_bridges(connection: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Resolve only admitted endpoints under their exact domain alias scope."""
    workspace = Path(payload["lanes"][0]["plan"]["legacy_graph_source_path"]).resolve()
    # source graph -> workspace/agents|domains/...; recover workspace without inference from IDs
    while workspace.name not in {"agents", "domains"}:
        workspace = workspace.parent
    workspace = workspace.parent
    bridge_path = workspace / "bridges.json"
    try:
        value = json.loads(bridge_path.read_text(encoding="utf-8")) if bridge_path.is_file() else {"bridges": []}
    except (OSError, json.JSONDecodeError) as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_BRIDGE_EVIDENCE_UNREADABLE") from exc
    bridges = value.get("bridges", []) if isinstance(value, dict) else None
    if not isinstance(bridges, list):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_BRIDGE_EVIDENCE_MALFORMED")
    domains = {lane["plan"]["domain_id"]: lane for lane in payload["lanes"] if lane["plan"]["scope_kind"] == _SHARED}
    reader = NativeMotifRuntimeReader(connection)
    observations = []
    for bridge in bridges:
        if not isinstance(bridge, dict):
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_BRIDGE_EVIDENCE_MALFORMED")
        endpoints = []
        for domain_key, motif_key in (("from_domain", "from_motif"), ("to_domain", "to_motif")):
            domain, motif_id = bridge.get(domain_key), bridge.get(motif_key)
            lane = domains.get(domain)
            if lane is None:
                endpoints.append({"domain_id": domain, "motif_id": motif_id, "status": "UNADMITTED_DOMAIN"})
                continue
            plan = lane["plan"]
            matches = [motif for motif in reader.list_runtime_motifs(
                motif_alias_namespace_id=UUID(plan["motif_alias_namespace_id"]), domain_id=domain,
                semantic_scope_id=UUID(plan["target_semantic_scope_id"]),
            ) if motif.read_model.runtime_motif_id == motif_id]
            endpoints.append({"domain_id": domain, "motif_id": motif_id, "status": "RESOLVED" if len(matches) == 1 else "REFUSED", "object_id": str(matches[0].motif_object_id) if len(matches) == 1 else None})
        observations.append({"from_domain": bridge.get("from_domain"), "from_motif": bridge.get("from_motif"), "to_domain": bridge.get("to_domain"), "to_motif": bridge.get("to_motif"), "endpoints": endpoints})
    return {"owner": "EXTERNAL_BRIDGE_REGISTRY", "bridge_path_digest": _file_digest(bridge_path) if bridge_path.is_file() else None, "bridges": observations}


def _verify_lane_snapshots(descriptor: ExistingWorkspaceNativeMultiScopeDescriptor, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest) -> None:
    for plan in request.ordered_lane_plans:
        lane = _lane_descriptor(descriptor.payload, plan)
        manifest_path = Path(lane["snapshot_manifest_path"])
        manifest = load_snapshot_manifest(manifest_path)
        if str(manifest.legacy_snapshot_id) != lane["legacy_snapshot_id"] or _file_digest(manifest_path) != lane["snapshot_digest"]:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_SNAPSHOT_DESCRIPTOR_MISMATCH")
        if manifest.legacy_source_namespace_id != plan.legacy_source_namespace_id:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_SNAPSHOT_NAMESPACE_MISMATCH")
        verify_snapshot(snapshot_root=lane["snapshot_root"], manifest=manifest)


def _verify_descriptor_matches_request(descriptor: ExistingWorkspaceNativeMultiScopeDescriptor, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest) -> None:
    payload = descriptor.payload
    expected = {
        "profile": _PROFILE, "admission_key": request.admission_key, "workspace_id": request.workspace_id,
        "unknown_semantic_scope_id": str(request.unknown_semantic_scope_id),
        "representation_lane": _lane_payload(request.qualified_representation_lane),
        "lane_plan_digest": _digest([plan.payload() for plan in request.ordered_lane_plans]),
        "declared_lane_count": len(request.lane_plans),
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_REQUEST_MISMATCH")
    if len(payload.get("lanes", [])) != len(request.lane_plans):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_LANE_SET_MISMATCH")
    for plan in request.ordered_lane_plans:
        _lane_descriptor(payload, plan)


def _lane_descriptor(payload: dict[str, Any], plan: ExistingWorkspaceNativeLanePlan) -> dict[str, Any]:
    matches = [lane for lane in payload.get("lanes", []) if isinstance(lane, dict) and lane.get("plan") == plan.payload()]
    if len(matches) != 1:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_LANE_SET_MISMATCH")
    return matches[0]


def _complete_lane_stage(lane: dict[str, Any], stage: str) -> None:
    if stage not in lane["stages_complete"]:
        lane["stages_complete"].append(stage)


def _character_witness_from_lane(lane: dict[str, Any], plan: ExistingWorkspaceNativeLanePlan) -> CharacterSeedWitness | None:
    value = lane.get("character_seed")
    return None if value is None else CharacterSeedWitness.from_descriptor_payload(
        workspace_id=plan.workspace_id, agent_id=plan.agent_id or "", domain_id=plan.motif_domain_id, value=value,
    )


def _read_character_witness(workspace: Path, plan: ExistingWorkspaceNativeLanePlan) -> CharacterSeedWitness:
    try:
        return read_legacy_character_seed_witness(
            workspace_root=workspace, workspace_id=plan.workspace_id, agent_id=plan.agent_id or "",
            domain_id=plan.motif_domain_id, requested_seed_id=plan.character_seed_id or "",
        )
    except CharacterSeedWitnessRefused as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused(exc.code) from exc


def _runtime_scope(plan: ExistingWorkspaceNativeLanePlan) -> NativeMemoryRuntimeScope:
    return NativeMemoryRuntimeScope(plan.workspace_id, plan.scope_kind, plan.legacy_source_namespace_id, plan.target_identity_namespace_id, plan.target_semantic_scope_id, plan.agent_id, plan.domain_id)


def _routing_scope(plan: ExistingWorkspaceNativeLanePlan) -> NativeFabricRoutingScope:
    return NativeFabricRoutingScope(_runtime_scope(plan), plan.motif_alias_namespace_id, plan.motif_identity_namespace_id, plan.membership_identity_namespace_id, plan.idempotency_namespace_id)


def _stage_key(request: ExistingWorkspaceNativeMultiScopeAdmissionRequest, plan: ExistingWorkspaceNativeLanePlan, stage: str, value: int | str) -> str:
    return f"7G5E4C:{request.admission_key}:{plan.legacy_source_namespace_id}:{stage}:{value}"


def _lane_results(descriptor: ExistingWorkspaceNativeMultiScopeDescriptor) -> tuple[ExistingWorkspaceNativeMultiScopeLaneResult, ...]:
    values = []
    for lane in descriptor.payload["lanes"]:
        counts = lane["readiness_counts"]
        values.append(ExistingWorkspaceNativeMultiScopeLaneResult(
            lane["plan"]["scope_kind"], lane["plan"]["qualifier"], counts["memory"],
            counts["representation"], counts["motif"], counts["membership"],
            lane["snapshot_digest"], lane["readiness_report_digest"],
        ))
    return tuple(values)


def load_existing_workspace_multi_scope_admission_descriptor(path: str | Path) -> ExistingWorkspaceNativeMultiScopeDescriptor:
    descriptor_path = Path(path).expanduser().resolve()
    try:
        wrapped = json.loads(descriptor_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_UNREADABLE") from exc
    if not isinstance(wrapped, dict) or set(wrapped) != {"descriptor_digest", "payload"} or not isinstance(wrapped["payload"], dict):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_TAMPERED")
    payload = wrapped["payload"]
    digest = _digest(payload)
    if wrapped["descriptor_digest"] != digest:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_TAMPERED")
    if payload.get("descriptor_schema") != _SCHEMA or payload.get("descriptor_version") != _VERSION:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_VERSION_UNSUPPORTED")
    try:
        ExistingWorkspaceMultiScopeAdmissionState(payload["admission_state"])
    except (KeyError, ValueError) as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_TAMPERED") from exc
    _validate_descriptor_lane_set(payload)
    return ExistingWorkspaceNativeMultiScopeDescriptor(payload, digest)


def _validate_descriptor_lane_set(payload: dict[str, Any]) -> None:
    """Fail closed before cold recovery can trust a serialized lane set."""
    values = payload.get("lanes")
    if not isinstance(values, list) or payload.get("declared_lane_count") != len(values):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_LANE_SET_MISMATCH")
    try:
        plans = tuple(_plan_from_payload(entry["plan"]) for entry in values if isinstance(entry, dict))
        descriptor_lane = _lane_from_payload(payload["representation_lane"])
        if len(plans) != len(values) or tuple(sorted(plans, key=lambda plan: (0 if plan.scope_kind == _PRIVATE else 1, plan.qualifier))) != plans:
            raise ValueError("non-canonical plans")
        if len([plan for plan in plans if plan.scope_kind == _PRIVATE]) != 1 or not any(plan.scope_kind == _SHARED for plan in plans):
            raise ValueError("profile lane mix")
        _require_distinct_lane_identities(plans)
        if any(plan.representation_lane != descriptor_lane for plan in plans):
            raise ValueError("lane representation mismatch")
        if payload.get("lane_plan_digest") != _digest([plan.payload() for plan in plans]):
            raise ValueError("lane plan digest mismatch")
        for entry, plan in zip(values, plans, strict=True):
            if entry.get("plan") != plan.payload():
                raise ValueError("noncanonical plan payload")
    except (KeyError, TypeError, ValueError, ExistingWorkspaceMultiScopeAdmissionRefused) as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_LANE_SET_MISMATCH") from exc


def recover_existing_workspace_native_multi_scope_runtime(*, native_core_database_path: str | Path, admission_descriptor_path: str | Path, expected_representation_lane: NativeRepresentationLane | None = None, character_store: Any | None = None) -> RecoveredExistingWorkspaceNativeMultiScopeRuntime:
    descriptor = load_existing_workspace_multi_scope_admission_descriptor(admission_descriptor_path)
    if descriptor.state is not ExistingWorkspaceMultiScopeAdmissionState.ADMISSION_COMPLETE:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_RECOVERY_NOT_COMPLETE")
    lane = descriptor.representation_lane
    if expected_representation_lane is not None and expected_representation_lane != lane:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_RECOVERY_WRONG_LANE")
    core_path = Path(native_core_database_path).expanduser().resolve()
    scopes: list[RecoveredExistingWorkspaceNativeMultiScopeScope] = []
    for entry in descriptor.payload["lanes"]:
        plan = _plan_from_payload(entry["plan"])
        witness = _character_witness_from_lane(entry, plan)
        scopes.append(RecoveredExistingWorkspaceNativeMultiScopeScope(core_path, descriptor.native_core_id, lane, _runtime_scope(plan), _routing_scope(plan), witness))
    with open_existing_native_core_connection(core_path) as qualified:
        metadata = open_schema(qualified.connection, writable=False)
        if native_id_from_bytes(metadata.core_id) != descriptor.native_core_id:
            raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_RECOVERY_WRONG_CORE")
        prepare_native_memory_runtime_binding(
            connection=qualified.connection, core_database_path=core_path, expected_core_id=descriptor.native_core_id,
            scope_bindings=tuple(scope.memory_runtime_scope for scope in scopes), representation_lane=lane,
        )
    runtime = RecoveredExistingWorkspaceNativeMultiScopeRuntime(core_path, descriptor, lane, tuple(scopes))
    for scope in scopes:
        if scope.character_seed_witness is not None:
            scope.require_external_character_seed(character_store)
    return runtime


def _plan_from_payload(value: Any) -> ExistingWorkspaceNativeLanePlan:
    if not isinstance(value, dict):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_TAMPERED")
    try:
        return ExistingWorkspaceNativeLanePlan(
            workspace_id=value["workspace_id"], scope_kind=value["scope_kind"],
            legacy_graph_source_path=value["legacy_graph_source_path"],
            legacy_source_namespace_id=UUID(value["legacy_source_namespace_id"]),
            legacy_source_namespace_key=value["legacy_source_namespace_key"],
            target_identity_namespace_id=UUID(value["target_identity_namespace_id"]),
            target_semantic_scope_id=UUID(value["target_semantic_scope_id"]),
            motif_alias_namespace_id=UUID(value["motif_alias_namespace_id"]),
            motif_identity_namespace_id=UUID(value["motif_identity_namespace_id"]),
            membership_identity_namespace_id=UUID(value["membership_identity_namespace_id"]),
            idempotency_namespace_id=UUID(value["idempotency_namespace_id"]),
            motif_domain_id=value["motif_domain_id"],
            representation_lane=_lane_from_payload(value["representation_lane"]),
            agent_id=value.get("agent_id"),
            domain_id=value.get("domain_id"), character_seed_id=value.get("character_seed_id"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_TAMPERED") from exc


def _lane_payload(lane: NativeRepresentationLane) -> dict[str, Any]:
    return {name: getattr(lane, name) for name in lane.__dataclass_fields__}


def _lane_from_payload(value: Any) -> NativeRepresentationLane:
    if not isinstance(value, dict):
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_TAMPERED")
    try:
        return NativeRepresentationLane(**value)
    except (TypeError, ValueError) as exc:
        raise ExistingWorkspaceMultiScopeAdmissionRefused("MULTI_SCOPE_DESCRIPTOR_TAMPERED") from exc


def _write_descriptor(path: Path, payload: dict[str, Any]) -> None:
    wrapped = {"descriptor_digest": _digest(payload), "payload": payload}
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(_canonical(wrapped) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def _retained_side_store_digest(workspace: Path, request: ExistingWorkspaceNativeMultiScopeAdmissionRequest) -> str:
    paths = [workspace / "bridges.json", workspace / "bridge_events.jsonl"]
    for plan in request.ordered_lane_plans:
        if plan.scope_kind == _PRIVATE:
            agent = workspace / "agents" / (plan.agent_id or "")
            paths.extend((agent / "character_state.json", agent / "private" / "checkpoints", agent / "private" / "trajectories.jsonl"))
    values = []
    for path in paths:
        if path.is_file():
            values.append((str(path.relative_to(workspace)), _file_digest(path)))
        elif path.is_dir():
            values.append((str(path.relative_to(workspace)), _tree_fingerprint(path)))
        else:
            values.append((str(path.relative_to(workspace)), None))
    return _digest({"observations": [str(item) for item in request.retained_side_store_eid_observations], "paths": values})


def _lane_source_fingerprint(workspace: Path, plan: ExistingWorkspaceNativeLanePlan) -> str:
    source = Path(plan.legacy_graph_source_path).expanduser().resolve()
    paths = [source, workspace / "workspace_meta.json", workspace / "domains" / plan.motif_domain_id / "motifs.json"]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(workspace)).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        if path.is_dir():
            digest.update(_tree_fingerprint(path).encode("ascii"))
        else:
            digest.update(_file_digest(path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _tree_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8")); digest.update(b"\0")
        digest.update(path.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


__all__ = [
    "ExistingWorkspaceMultiScopeAdmissionRefused", "ExistingWorkspaceMultiScopeAdmissionState",
    "ExistingWorkspaceNativeLanePlan", "ExistingWorkspaceNativeMultiScopeAdmissionRequest",
    "ExistingWorkspaceNativeMultiScopeDescriptor", "ExistingWorkspaceNativeMultiScopeLaneResult",
    "ExistingWorkspaceNativeMultiScopeAdmissionResult", "ExistingWorkspaceNativeMultiScopeAdmissionService",
    "RecoveredExistingWorkspaceNativeMultiScopeReaders", "RecoveredExistingWorkspaceNativeMultiScopeScope",
    "RecoveredExistingWorkspaceNativeMultiScopeRuntime",
    "load_existing_workspace_multi_scope_admission_descriptor",
    "recover_existing_workspace_native_multi_scope_runtime",
]
