"""Immutable root-wide admission description for future generalized admission.

Phase 9A provides typed administrative evidence only.  It does not execute
admission, write SQLite, allocate namespaces, create a core, select a backend,
or become activation evidence by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
from typing import Final

from torment_service.pathing import validate_structural_path_component

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateConfigurationError
from ..runtime_binding import NativeRepresentationLane
from .explicit_source_evidence import (
    EvidenceAbsenceReason,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    RootEvidenceManifest,
    SourceOwnerClass,
)
from .root_scope import RootScopeKey, RootScopeKind


CENSUS_AND_MANIFEST_REQUIRE_WRITER_FREEZE: Final[bool] = True
SEMANTIC_ADAPTER_OWNERSHIP_DOES_NOT_EQUAL_DURABLE_STORE_OWNERSHIP: Final[bool] = True
PHASE_9A_TARGET_REPRESENTATION_PROVIDER: Final[str] = "st"
PHASE_9A_TARGET_REPRESENTATION_MODEL: Final[str] = "BAAI/bge-small-en-v1.5"
PHASE_9A_TARGET_REPRESENTATION_DIMENSION: Final[int] = 384


class RootRepresentationDisposition(StrEnum):
    TARGET_COMPATIBLE = "TARGET_COMPATIBLE"
    REEMBED_REQUIRED = "REEMBED_REQUIRED"
    UNKNOWN_IDENTITY = "UNKNOWN_IDENTITY"
    NO_VECTOR = "NO_VECTOR"
    UNUSABLE_VECTOR = "UNUSABLE_VECTOR"


class MaterializedScopePosture(StrEnum):
    MEMORY_GRAPH = "MEMORY_GRAPH"
    EMPTY_SHARED_WITH_MOTIF = "EMPTY_SHARED_WITH_MOTIF"
    EMPTY_PRIVATE = "EMPTY_PRIVATE"
    DECLARED_EMPTY_SHARED = "DECLARED_EMPTY_SHARED"


class GeometryDerivedExternalStateDisposition(StrEnum):
    UNRESOLVED_PRE_ACTIVATION_GATE = "UNRESOLVED_PRE_ACTIVATION_GATE"


class WriterFreezeEvidenceState(StrEnum):
    REQUIRED_NOT_WITNESSED = "REQUIRED_NOT_WITNESSED"


class ExternalOwnerObservationKind(StrEnum):
    IDENTITY = "IDENTITY"
    ROLE = "ROLE"
    CHARACTER = "CHARACTER"
    BRIDGE = "BRIDGE"
    CONFLICT = "CONFLICT"
    PROPOSAL_WORKFLOW = "PROPOSAL_WORKFLOW"
    CHECKPOINT = "CHECKPOINT"
    TRAJECTORY = "TRAJECTORY"
    WORLD_SRG = "WORLD_SRG"
    OTHER_QUALIFIED = "OTHER_QUALIFIED"


class RootAdmissionDescriptionError(SubstrateConfigurationError):
    """Raised when a generalized root admission input is inconsistent."""


@dataclass(frozen=True)
class RepresentationDispositionCount:
    disposition: RootRepresentationDisposition
    scope_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.disposition, RootRepresentationDisposition):
            raise RootAdmissionDescriptionError("disposition must be RootRepresentationDisposition")
        _nonnegative(self.scope_count, "scope_count")

    def identity_payload(self) -> dict[str, object]:
        return {"disposition": self.disposition.value, "scope_count": self.scope_count}


@dataclass(frozen=True)
class WorkspaceTopologyCounts:
    zero_private_workspaces: int
    one_private_workspace: int
    multiple_private_workspaces: int
    zero_shared_workspaces: int
    one_shared_workspace: int
    multiple_shared_workspaces: int

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            _nonnegative(getattr(self, field_name), field_name)

    def private_total(self) -> int:
        return self.zero_private_workspaces + self.one_private_workspace + self.multiple_private_workspaces

    def shared_total(self) -> int:
        return self.zero_shared_workspaces + self.one_shared_workspace + self.multiple_shared_workspaces

    def identity_payload(self) -> dict[str, int]:
        return {field_name: getattr(self, field_name) for field_name in self.__dataclass_fields__}


@dataclass(frozen=True)
class ExpectedRootCensus:
    workspace_count: int
    materialized_private_scope_count: int
    materialized_shared_scope_count: int
    total_materialized_scope_count: int
    representation_disposition_counts: tuple[RepresentationDispositionCount, ...]
    workspace_topology_counts: WorkspaceTopologyCounts
    declared_empty_shared_scope_count: int = 0
    empty_private_identity_scope_count: int = 0

    def __post_init__(self) -> None:
        for field_name in (
            "workspace_count",
            "materialized_private_scope_count",
            "materialized_shared_scope_count",
            "total_materialized_scope_count",
            "declared_empty_shared_scope_count",
            "empty_private_identity_scope_count",
        ):
            _nonnegative(getattr(self, field_name), field_name)
        if self.workspace_count < 1:
            raise RootAdmissionDescriptionError("workspace_count must be positive")
        if self.materialized_private_scope_count + self.materialized_shared_scope_count != self.total_materialized_scope_count:
            raise RootAdmissionDescriptionError("private plus shared scope counts must equal total materialized scopes")
        if not isinstance(self.representation_disposition_counts, tuple):
            raise RootAdmissionDescriptionError("representation_disposition_counts must be a tuple")
        if any(not isinstance(item, RepresentationDispositionCount) for item in self.representation_disposition_counts):
            raise RootAdmissionDescriptionError("representation_disposition_counts must be typed")
        dispositions = tuple(item.disposition for item in self.representation_disposition_counts)
        if set(dispositions) != set(RootRepresentationDisposition) or len(dispositions) != len(set(dispositions)):
            raise RootAdmissionDescriptionError("census must state every representation disposition exactly once")
        if sum(item.scope_count for item in self.representation_disposition_counts) != self.total_runtime_scope_count:
            raise RootAdmissionDescriptionError("representation disposition counts must equal total runtime scopes")
        if not isinstance(self.workspace_topology_counts, WorkspaceTopologyCounts):
            raise RootAdmissionDescriptionError("workspace_topology_counts must be typed")
        if self.workspace_topology_counts.private_total() != self.workspace_count:
            raise RootAdmissionDescriptionError("private workspace topology counts must equal workspace_count")
        if self.workspace_topology_counts.shared_total() != self.workspace_count:
            raise RootAdmissionDescriptionError("shared workspace topology counts must equal workspace_count")
        ordered = tuple(sorted(self.representation_disposition_counts, key=lambda item: item.disposition.value))
        object.__setattr__(self, "representation_disposition_counts", ordered)

    def identity_payload(self) -> dict[str, object]:
        return {
            "workspace_count": self.workspace_count,
            "materialized_private_scope_count": self.materialized_private_scope_count,
            "materialized_shared_scope_count": self.materialized_shared_scope_count,
            "total_materialized_scope_count": self.total_materialized_scope_count,
            "declared_empty_shared_scope_count": self.declared_empty_shared_scope_count,
            "empty_private_identity_scope_count": self.empty_private_identity_scope_count,
            "representation_disposition_counts": [item.identity_payload() for item in self.representation_disposition_counts],
            "workspace_topology_counts": self.workspace_topology_counts.identity_payload(),
        }

    @property
    def total_runtime_scope_count(self) -> int:
        """All admitted runtime scopes, including declared-empty shared domains."""

        return self.total_materialized_scope_count + self.declared_empty_shared_scope_count


@dataclass(frozen=True)
class MaterializedRootScopePlan:
    scope_key: RootScopeKey
    representation_disposition: RootRepresentationDisposition
    materialization_posture: MaterializedScopePosture = MaterializedScopePosture.MEMORY_GRAPH

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey):
            raise RootAdmissionDescriptionError("scope_key must be RootScopeKey")
        if not isinstance(self.representation_disposition, RootRepresentationDisposition):
            raise RootAdmissionDescriptionError("representation_disposition must be typed")
        if not isinstance(self.materialization_posture, MaterializedScopePosture):
            raise RootAdmissionDescriptionError("materialization_posture must be typed")
        if (
            self.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF
            and self.scope_key.scope_kind is not RootScopeKind.SHARED
        ):
            raise RootAdmissionDescriptionError("EMPTY_SHARED_WITH_MOTIF requires a SHARED scope")
        if (
            self.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE
            and self.scope_key.scope_kind is not RootScopeKind.PRIVATE
        ):
            raise RootAdmissionDescriptionError("EMPTY_PRIVATE requires a PRIVATE scope")
        if (
            self.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
            and self.scope_key.scope_kind is not RootScopeKind.SHARED
        ):
            raise RootAdmissionDescriptionError("DECLARED_EMPTY_SHARED requires a SHARED scope")
        if (
            self.materialization_posture in (
                MaterializedScopePosture.EMPTY_PRIVATE,
                MaterializedScopePosture.DECLARED_EMPTY_SHARED,
            )
            and self.representation_disposition is not RootRepresentationDisposition.NO_VECTOR
        ):
            raise RootAdmissionDescriptionError("declared-empty scope requires NO_VECTOR disposition")

    def identity_payload(self) -> dict[str, object]:
        return {
            "scope_key": self.scope_key.identity_payload(),
            "representation_disposition": self.representation_disposition.value,
            "materialization_posture": self.materialization_posture.value,
        }


@dataclass(frozen=True)
class IdentityOnlyAgentObservation:
    agent_id: str
    observation_key: str

    def __post_init__(self) -> None:
        _identifier(self.agent_id, "agent_id")
        _text(self.observation_key, "observation_key")

    def identity_payload(self) -> dict[str, str]:
        return {"agent_id": self.agent_id, "observation_key": self.observation_key}


@dataclass(frozen=True)
class DeclaredUnmaterializedDomain:
    domain_id: str
    declaration_key: str

    def __post_init__(self) -> None:
        _identifier(self.domain_id, "domain_id")
        _text(self.declaration_key, "declaration_key")

    def identity_payload(self) -> dict[str, str]:
        return {"domain_id": self.domain_id, "declaration_key": self.declaration_key}


@dataclass(frozen=True)
class WorkspaceRootAdmissionPlan:
    workspace_id: str
    private_materialized_scopes: tuple[MaterializedRootScopePlan, ...] = ()
    shared_materialized_scopes: tuple[MaterializedRootScopePlan, ...] = ()
    identity_only_agents: tuple[IdentityOnlyAgentObservation, ...] = ()
    declared_unmaterialized_domains: tuple[DeclaredUnmaterializedDomain, ...] = ()
    no_memory_scope: bool = False

    def __post_init__(self) -> None:
        _identifier(self.workspace_id, "workspace_id")
        _typed_tuple(self.private_materialized_scopes, MaterializedRootScopePlan, "private_materialized_scopes")
        _typed_tuple(self.shared_materialized_scopes, MaterializedRootScopePlan, "shared_materialized_scopes")
        _typed_tuple(self.identity_only_agents, IdentityOnlyAgentObservation, "identity_only_agents")
        _typed_tuple(self.declared_unmaterialized_domains, DeclaredUnmaterializedDomain, "declared_unmaterialized_domains")
        if not isinstance(self.no_memory_scope, bool):
            raise RootAdmissionDescriptionError("no_memory_scope must be boolean")
        _validate_scope_group(self.workspace_id, self.private_materialized_scopes, RootScopeKind.PRIVATE)
        _validate_scope_group(self.workspace_id, self.shared_materialized_scopes, RootScopeKind.SHARED)
        private = tuple(sorted(self.private_materialized_scopes, key=lambda item: item.scope_key.qualifier))
        shared = tuple(sorted(self.shared_materialized_scopes, key=lambda item: item.scope_key.qualifier))
        identities = tuple(sorted(self.identity_only_agents, key=lambda item: item.agent_id))
        domains = tuple(sorted(self.declared_unmaterialized_domains, key=lambda item: item.domain_id))
        _no_duplicates((item.scope_key.qualifier for item in private), "private materialized scope")
        _no_duplicates((item.scope_key.qualifier for item in shared), "shared materialized scope")
        _no_duplicates((item.agent_id for item in identities), "identity-only agent")
        _no_duplicates((item.domain_id for item in domains), "declared unmaterialized domain")
        empty_private_agents = {
            item.scope_key.agent_id
            for item in private
            if item.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE
        }
        material_private_agents = {
            item.scope_key.agent_id
            for item in private
            if item.materialization_posture is not MaterializedScopePosture.EMPTY_PRIVATE
        }
        if material_private_agents & {item.agent_id for item in identities}:
            raise RootAdmissionDescriptionError("identity-only agent cannot also have a materialized private scope")
        if not empty_private_agents <= {item.agent_id for item in identities}:
            raise RootAdmissionDescriptionError("EMPTY_PRIVATE scope requires an identity-only agent observation")
        declared_empty_domains = {
            item.scope_key.domain_id
            for item in shared
            if item.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
        }
        material_shared_domains = {
            item.scope_key.domain_id
            for item in shared
            if item.materialization_posture is not MaterializedScopePosture.DECLARED_EMPTY_SHARED
        }
        if material_shared_domains & {item.domain_id for item in domains}:
            raise RootAdmissionDescriptionError("unmaterialized domain cannot also have a materialized shared scope")
        if not declared_empty_domains <= {item.domain_id for item in domains}:
            raise RootAdmissionDescriptionError("DECLARED_EMPTY_SHARED scope requires a domain declaration")
        has_materialized = bool(self.materialized_scopes)
        if self.no_memory_scope == has_materialized:
            raise RootAdmissionDescriptionError("no_memory_scope must exactly describe the absence of materialized scopes")
        object.__setattr__(self, "private_materialized_scopes", private)
        object.__setattr__(self, "shared_materialized_scopes", shared)
        object.__setattr__(self, "identity_only_agents", identities)
        object.__setattr__(self, "declared_unmaterialized_domains", domains)

    @property
    def materialized_scopes(self) -> tuple[MaterializedRootScopePlan, ...]:
        """Physically discoverable source scopes only.

        A DECLARED_EMPTY_SHARED scope is a runtime membership obligation, not a
        directory that root discovery is allowed to invent or require.
        """

        return self.private_materialized_scopes + tuple(
            item
            for item in self.shared_materialized_scopes
            if item.materialization_posture is not MaterializedScopePosture.DECLARED_EMPTY_SHARED
        )

    @property
    def runtime_scopes(self) -> tuple[MaterializedRootScopePlan, ...]:
        """Every explicitly admitted runtime scope, including declared-empty shared."""

        return self.private_materialized_scopes + self.shared_materialized_scopes

    def identity_payload(self) -> dict[str, object]:
        return {
            "workspace_id": self.workspace_id,
            "private_materialized_scopes": [item.identity_payload() for item in self.private_materialized_scopes],
            "shared_materialized_scopes": [item.identity_payload() for item in self.shared_materialized_scopes],
            "identity_only_agents": [item.identity_payload() for item in self.identity_only_agents],
            "declared_unmaterialized_domains": [item.identity_payload() for item in self.declared_unmaterialized_domains],
            "no_memory_scope": self.no_memory_scope,
        }


@dataclass(frozen=True)
class ExternalOwnerObservation:
    workspace_id: str
    owner_kind: ExternalOwnerObservationKind
    observation_key: str
    observation_digest: str
    scope_key: RootScopeKey | None = None

    def __post_init__(self) -> None:
        _identifier(self.workspace_id, "workspace_id")
        if not isinstance(self.owner_kind, ExternalOwnerObservationKind):
            raise RootAdmissionDescriptionError("owner_kind must be ExternalOwnerObservationKind")
        _text(self.observation_key, "observation_key")
        _sha256(self.observation_digest)
        if self.scope_key is not None and not isinstance(self.scope_key, RootScopeKey):
            raise RootAdmissionDescriptionError("scope_key must be RootScopeKey when supplied")
        if self.scope_key is not None and self.scope_key.workspace_id != self.workspace_id:
            raise RootAdmissionDescriptionError("external owner observation crosses workspace identity")

    @property
    def canonical_key(self) -> tuple[str, str, str, tuple[str, str, str]]:
        return (
            self.workspace_id,
            self.owner_kind.value,
            self.observation_key,
            self.scope_key.canonical_key if self.scope_key is not None else ("", "", ""),
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "workspace_id": self.workspace_id,
            "owner_kind": self.owner_kind.value,
            "observation_key": self.observation_key,
            "observation_digest": self.observation_digest,
            "scope_key": self.scope_key.identity_payload() if self.scope_key is not None else None,
        }


@dataclass(frozen=True)
class RootFeaturePosture:
    profile_name: str
    compression_enabled: bool
    deep_memory_enabled: bool
    geometry_derived_external_state_disposition: GeometryDerivedExternalStateDisposition = (
        GeometryDerivedExternalStateDisposition.UNRESOLVED_PRE_ACTIVATION_GATE
    )

    def __post_init__(self) -> None:
        _text(self.profile_name, "profile_name")
        if not isinstance(self.compression_enabled, bool) or not isinstance(self.deep_memory_enabled, bool):
            raise RootAdmissionDescriptionError("feature posture booleans must be bool")
        if self.geometry_derived_external_state_disposition is not GeometryDerivedExternalStateDisposition.UNRESOLVED_PRE_ACTIVATION_GATE:
            raise RootAdmissionDescriptionError("geometry-derived external state must remain unresolved in Phase 9A")

    def identity_payload(self) -> dict[str, object]:
        return {
            "profile_name": self.profile_name,
            "compression_enabled": self.compression_enabled,
            "deep_memory_enabled": self.deep_memory_enabled,
            "geometry_derived_external_state_disposition": self.geometry_derived_external_state_disposition.value,
        }


@dataclass(frozen=True)
class RootNativeProductionAdmissionDescription:
    """Immutable administrative input for a later root-wide admission phase."""

    data_root_identity: str
    operator_identity: str
    workspace_plans: tuple[WorkspaceRootAdmissionPlan, ...]
    target_representation_lane: NativeRepresentationLane
    expected_census: ExpectedRootCensus
    explicit_source_manifest: RootEvidenceManifest
    external_owner_observations: tuple[ExternalOwnerObservation, ...]
    feature_posture: RootFeaturePosture
    writer_freeze_evidence_state: WriterFreezeEvidenceState = WriterFreezeEvidenceState.REQUIRED_NOT_WITNESSED

    def __post_init__(self) -> None:
        _text(self.data_root_identity, "data_root_identity")
        _text(self.operator_identity, "operator_identity")
        _typed_tuple(self.workspace_plans, WorkspaceRootAdmissionPlan, "workspace_plans")
        if not isinstance(self.target_representation_lane, NativeRepresentationLane):
            raise RootAdmissionDescriptionError("target_representation_lane must be NativeRepresentationLane")
        if not _is_phase_9a_target_lane(self.target_representation_lane):
            raise RootAdmissionDescriptionError(
                "target_representation_lane must be the frozen st / BAAI/bge-small-en-v1.5 / 384 lane"
            )
        if not isinstance(self.expected_census, ExpectedRootCensus):
            raise RootAdmissionDescriptionError("expected_census must be ExpectedRootCensus")
        if not isinstance(self.explicit_source_manifest, RootEvidenceManifest):
            raise RootAdmissionDescriptionError("explicit_source_manifest must be RootEvidenceManifest")
        _typed_tuple(self.external_owner_observations, ExternalOwnerObservation, "external_owner_observations")
        if not isinstance(self.feature_posture, RootFeaturePosture):
            raise RootAdmissionDescriptionError("feature_posture must be RootFeaturePosture")
        if self.writer_freeze_evidence_state is not WriterFreezeEvidenceState.REQUIRED_NOT_WITNESSED:
            raise RootAdmissionDescriptionError("Phase 9A cannot claim a writer-freeze witness")
        workspaces = tuple(sorted(self.workspace_plans, key=lambda item: item.workspace_id))
        _no_duplicates((item.workspace_id for item in workspaces), "workspace plan")
        observations = tuple(sorted(self.external_owner_observations, key=lambda item: item.canonical_key))
        _no_duplicates((item.canonical_key for item in observations), "external owner observation")
        workspace_ids = {item.workspace_id for item in workspaces}
        if any(item.workspace_id not in workspace_ids for item in observations):
            raise RootAdmissionDescriptionError("external owner observation names an undeclared workspace")
        if any(
            item.owner_boundary.workspace_id not in workspace_ids
            for item in self.explicit_source_manifest.entries
        ):
            raise RootAdmissionDescriptionError("manifest evidence names an undeclared workspace")
        object.__setattr__(self, "workspace_plans", workspaces)
        object.__setattr__(self, "external_owner_observations", observations)
        self._validate_census_against_plans()
        self._validate_manifest_against_plans()

    @property
    def external_owner_observation_digest(self) -> str:
        payload = [item.identity_payload() for item in self.external_owner_observations]
        return hashlib.sha256(canonical_intent_text(payload).encode("utf-8")).hexdigest()

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "data_root_identity": self.data_root_identity,
            "operator_identity": self.operator_identity,
            "workspace_plans": [item.identity_payload() for item in self.workspace_plans],
            "target_representation_lane": _lane_payload(self.target_representation_lane),
            "expected_census": self.expected_census.identity_payload(),
            "explicit_source_manifest_digest": self.explicit_source_manifest.digest,
            "external_owner_observation_digest": self.external_owner_observation_digest,
            "feature_posture": self.feature_posture.identity_payload(),
            "writer_freeze_evidence_state": self.writer_freeze_evidence_state.value,
        }

    @property
    def canonical_text(self) -> str:
        return canonical_intent_text(self.canonical_payload)

    @property
    def identity_digest(self) -> str:
        return hashlib.sha256(self.canonical_text.encode("utf-8")).hexdigest()

    @property
    def is_activation_evidence(self) -> bool:
        """Phase 9A descriptions never self-certify a future activation."""
        return False

    def _validate_census_against_plans(self) -> None:
        materialized = tuple(scope for workspace in self.workspace_plans for scope in workspace.materialized_scopes)
        plans = tuple(scope for workspace in self.workspace_plans for scope in workspace.runtime_scopes)
        private_count = sum(scope.scope_key.scope_kind is RootScopeKind.PRIVATE for scope in materialized)
        shared_count = sum(scope.scope_key.scope_kind is RootScopeKind.SHARED for scope in materialized)
        declared_empty_shared_count = sum(
            scope.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
            for scope in plans
        )
        empty_private_count = sum(
            scope.materialization_posture is MaterializedScopePosture.EMPTY_PRIVATE
            for scope in plans
        )
        census = self.expected_census
        if len(self.workspace_plans) != census.workspace_count:
            raise RootAdmissionDescriptionError("workspace plans do not match expected census")
        if private_count != census.materialized_private_scope_count or shared_count != census.materialized_shared_scope_count:
            raise RootAdmissionDescriptionError("materialized scope plans do not match expected census")
        if len(materialized) != census.total_materialized_scope_count:
            raise RootAdmissionDescriptionError("total materialized scope plans do not match expected census")
        if declared_empty_shared_count != census.declared_empty_shared_scope_count:
            raise RootAdmissionDescriptionError("declared empty shared scope plans do not match expected census")
        if empty_private_count != census.empty_private_identity_scope_count:
            raise RootAdmissionDescriptionError("empty private identity scope plans do not match expected census")
        actual_dispositions = {disposition: 0 for disposition in RootRepresentationDisposition}
        for plan in plans:
            actual_dispositions[plan.representation_disposition] += 1
        expected_dispositions = {item.disposition: item.scope_count for item in census.representation_disposition_counts}
        if actual_dispositions != expected_dispositions:
            raise RootAdmissionDescriptionError("scope representation dispositions do not match expected census")
        topology = WorkspaceTopologyCounts(
            zero_private_workspaces=sum(not item.private_materialized_scopes for item in self.workspace_plans),
            one_private_workspace=sum(len(item.private_materialized_scopes) == 1 for item in self.workspace_plans),
            multiple_private_workspaces=sum(len(item.private_materialized_scopes) > 1 for item in self.workspace_plans),
            zero_shared_workspaces=sum(not item.shared_materialized_scopes for item in self.workspace_plans),
            one_shared_workspace=sum(len(item.shared_materialized_scopes) == 1 for item in self.workspace_plans),
            multiple_shared_workspaces=sum(len(item.shared_materialized_scopes) > 1 for item in self.workspace_plans),
        )
        if topology != census.workspace_topology_counts:
            raise RootAdmissionDescriptionError("workspace topology plans do not match expected census")

    def _validate_manifest_against_plans(self) -> None:
        materialized = {
            scope.scope_key: scope
            for workspace in self.workspace_plans
            for scope in workspace.materialized_scopes
        }
        declared_unmaterialized = {
            RootScopeKey(workspace.workspace_id, RootScopeKind.SHARED, domain_id=domain.domain_id)
            for workspace in self.workspace_plans
            for domain in workspace.declared_unmaterialized_domains
        }
        declared_empty = {
            scope.scope_key: scope
            for workspace in self.workspace_plans
            for scope in workspace.runtime_scopes
            if scope.materialization_posture is MaterializedScopePosture.DECLARED_EMPTY_SHARED
        }
        for entry in self.explicit_source_manifest.entries:
            if entry.scope_key is not None and entry.scope_key not in materialized:
                is_declared_unmaterialized_absence = (
                    entry.scope_key in declared_unmaterialized
                    and entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT
                    and entry.absence_reason is EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION
                )
                if (
                    entry.owner_class is not SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION
                    and not is_declared_unmaterialized_absence
                    and entry.scope_key not in declared_empty
                ):
                    raise RootAdmissionDescriptionError("manifest evidence names an undeclared materialized scope")
        for scope_key, plan in materialized.items():
            entries = [entry for entry in self.explicit_source_manifest.entries if entry.scope_key == scope_key]
            nodes = [entry for entry in entries if entry.semantic_role is EvidenceSemanticRole.NODES]
            if plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
                if not any(entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT for entry in nodes):
                    raise RootAdmissionDescriptionError("materialized memory scope lacks required present nodes evidence")
            elif plan.materialization_posture is MaterializedScopePosture.EMPTY_SHARED_WITH_MOTIF:
                if not any(
                    entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT
                    and entry.absence_reason is EvidenceAbsenceReason.EMPTY_GRAPH
                    for entry in nodes
                ):
                    raise RootAdmissionDescriptionError("empty shared scope lacks EMPTY_GRAPH nodes absence evidence")
                if not any(
                    entry.semantic_role is EvidenceSemanticRole.MOTIFS
                    and entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT
                    for entry in entries
                ):
                    raise RootAdmissionDescriptionError("empty shared motif scope lacks present motif evidence")
            else:
                if not any(
                    entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT
                    and entry.absence_reason is EvidenceAbsenceReason.EMPTY_GRAPH
                    for entry in nodes
                ):
                    raise RootAdmissionDescriptionError("empty private scope lacks EMPTY_GRAPH nodes absence evidence")
                if any(
                    entry.semantic_role is EvidenceSemanticRole.MOTIFS
                    and entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT
                    for entry in entries
                ):
                    raise RootAdmissionDescriptionError("empty private scope cannot declare motif evidence")
        for scope_key, plan in declared_empty.items():
            entries = [entry for entry in self.explicit_source_manifest.entries if entry.scope_key == scope_key]
            nodes = [entry for entry in entries if entry.semantic_role is EvidenceSemanticRole.NODES]
            if not any(
                entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT
                and entry.absence_reason is EvidenceAbsenceReason.UNMATERIALIZED_DECLARATION
                for entry in nodes
            ):
                raise RootAdmissionDescriptionError("declared empty shared scope lacks UNMATERIALIZED_DECLARATION nodes evidence")
            if not any(
                entry.owner_boundary.workspace_id == scope_key.workspace_id
                and entry.semantic_role is EvidenceSemanticRole.DOMAINS
                and entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT
                for entry in self.explicit_source_manifest.entries
            ):
                raise RootAdmissionDescriptionError("declared empty shared scope lacks present domain declaration evidence")


def representation_identity_matches_target(
    *,
    provider: str | None,
    model: str | None,
    dimension: int | None,
    target_lane: NativeRepresentationLane,
) -> bool:
    """Return true only for exact provider/model/dimension target identity."""
    if not isinstance(target_lane, NativeRepresentationLane):
        raise RootAdmissionDescriptionError("target_lane must be NativeRepresentationLane")
    return (
        isinstance(provider, str)
        and isinstance(model, str)
        and isinstance(dimension, int)
        and not isinstance(dimension, bool)
        and provider == target_lane.provider
        and model == target_lane.model
        and dimension == target_lane.dimension
    )


def _is_phase_9a_target_lane(lane: NativeRepresentationLane) -> bool:
    return representation_identity_matches_target(
        provider=PHASE_9A_TARGET_REPRESENTATION_PROVIDER,
        model=PHASE_9A_TARGET_REPRESENTATION_MODEL,
        dimension=PHASE_9A_TARGET_REPRESENTATION_DIMENSION,
        target_lane=lane,
    )


def _validate_scope_group(
    workspace_id: str,
    scopes: tuple[MaterializedRootScopePlan, ...],
    expected_kind: RootScopeKind,
) -> None:
    for scope in scopes:
        if scope.scope_key.workspace_id != workspace_id or scope.scope_key.scope_kind is not expected_kind:
            raise RootAdmissionDescriptionError("materialized scope is in the wrong workspace or group")


def _typed_tuple(value: object, expected_type: type, label: str) -> None:
    if not isinstance(value, tuple) or any(not isinstance(item, expected_type) for item in value):
        raise RootAdmissionDescriptionError(f"{label} must be a tuple of {expected_type.__name__}")


def _no_duplicates(values: object, label: str) -> None:
    collected = tuple(values)  # type: ignore[arg-type]
    if len(collected) != len(set(collected)):
        raise RootAdmissionDescriptionError(f"duplicate {label} identity")


def _nonnegative(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RootAdmissionDescriptionError(f"{label} must be a non-negative integer")
    return value


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RootAdmissionDescriptionError(f"{label} must be non-empty text")
    try:
        return validate_structural_path_component(value, label)
    except ValueError as exc:
        raise RootAdmissionDescriptionError(str(exc)) from exc


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RootAdmissionDescriptionError(f"{label} must be non-empty text")
    return value


def _sha256(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise RootAdmissionDescriptionError("observation_digest must be lowercase SHA-256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise RootAdmissionDescriptionError("observation_digest must be lowercase SHA-256 hex") from exc
    return value


def _lane_payload(lane: NativeRepresentationLane) -> dict[str, object]:
    return {name: getattr(lane, name) for name in lane.__dataclass_fields__}


__all__ = [
    "CENSUS_AND_MANIFEST_REQUIRE_WRITER_FREEZE",
    "DeclaredUnmaterializedDomain",
    "ExpectedRootCensus",
    "ExternalOwnerObservation",
    "ExternalOwnerObservationKind",
    "GeometryDerivedExternalStateDisposition",
    "IdentityOnlyAgentObservation",
    "MaterializedRootScopePlan",
    "MaterializedScopePosture",
    "RepresentationDispositionCount",
    "RootAdmissionDescriptionError",
    "RootFeaturePosture",
    "RootNativeProductionAdmissionDescription",
    "RootRepresentationDisposition",
    "PHASE_9A_TARGET_REPRESENTATION_DIMENSION",
    "PHASE_9A_TARGET_REPRESENTATION_MODEL",
    "PHASE_9A_TARGET_REPRESENTATION_PROVIDER",
    "SEMANTIC_ADAPTER_OWNERSHIP_DOES_NOT_EQUAL_DURABLE_STORE_OWNERSHIP",
    "WorkspaceRootAdmissionPlan",
    "WorkspaceTopologyCounts",
    "WriterFreezeEvidenceState",
    "representation_identity_matches_target",
]
