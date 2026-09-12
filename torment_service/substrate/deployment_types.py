"""Typed, canonical deployment facts and origin-specific completion evidence.

These values describe authority bindings or completion evidence. They do not
grant a memory writer, select a Fabric backend, or expose public routing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from enum import Enum
import hashlib
import json
import re
from typing import Any, ClassVar, Mapping, TypeAlias
from uuid import UUID

from .errors import DeploymentAuthorityError
from .ids import native_id_from_text
from .schema import SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR
from .genesis_contracts import (
    GenesisAcceptedStart, GenesisExternalOwnerProjection, GenesisIntent,
    GenesisExternalOwnerProjectionV2, GenesisAgentSeedCompletion,
    GenesisMembershipReference, GenesisRepresentationLane,
    GenesisRootProfileReference, GenesisRuntimePlan, GenesisSeedCompletion,
    exact_object, initial_membership_closure_digest, ordered_runtime_plans,
    payload_digest, require as require_genesis, runtime_plan_digest,
)


_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

FROZEN_ROOT_GEOMETRY_DISPOSITIONS: tuple[tuple[str, str], ...] = (
    ("bridge_registry", "RETAIN_DECISION_STATUS_CONFIDENCE_HISTORICAL"),
    ("character_active_baseline", "RECOMPUTE_TARGET_GEOMETRY_BASELINE"),
    ("character_drift_history", "RETAIN_AS_HISTORICAL_GEOMETRY_EPOCH_STATE"),
    ("character_seed", "RETAIN"),
    ("checkpoint_kernel_calibration", "REINITIALIZE_CALIBRATION_ONLY"),
    ("conflict_role_affect_identity", "NO_GEOMETRY_DISPOSITION_REQUIRED"),
    ("deep_archive_vector_state", "RETAIN_UNTOUCHED_DISABLED"),
    ("hivemind_historical_geometry_scores", "RETAIN_HISTORICALLY"),
    ("proposal_registry", "RETAIN_UNMODIFIED_WITH_FUTURE_CONSUMER_GUARD"),
    ("srg_payload_markers", "RETAIN_EXACTLY"),
    ("world_trajectory", "RETAIN"),
)


class DeploymentState(str, Enum):
    """The existing in-core/external deployment-state vocabulary."""

    LEGACY_ACTIVE = "LEGACY_ACTIVE"
    CUTOVER_PENDING = "CUTOVER_PENDING"
    NATIVE_ACTIVE = "NATIVE_ACTIVE"


class DeploymentResolutionMode(str, Enum):
    """Read-only resolver dispositions; none itself routes a public request."""

    LEGACY_PUBLIC = "LEGACY_PUBLIC"
    MAINTENANCE_ONLY = "MAINTENANCE_ONLY"
    NATIVE_AGREEMENT = "NATIVE_AGREEMENT"
    REFUSED = "REFUSED"


@dataclass(frozen=True)
class QualifiedDeploymentProfile:
    """Canonical effective profile facts required by the B5-A2 agreement test."""

    compression_enabled: bool
    deep_memory_enabled: bool
    representation_provider: str
    representation_model: str
    representation_dimension: int
    admitted_scope_plan_digest: str
    external_owner_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.compression_enabled, bool) or not isinstance(self.deep_memory_enabled, bool):
            raise DeploymentAuthorityError("deployment profile flags must be boolean")
        for name in ("representation_provider", "representation_model"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise DeploymentAuthorityError(f"deployment profile {name} must be non-empty text")
        if (
            not isinstance(self.representation_dimension, int)
            or isinstance(self.representation_dimension, bool)
            or self.representation_dimension < 1
        ):
            raise DeploymentAuthorityError("deployment profile representation_dimension must be positive")
        _require_digest(self.admitted_scope_plan_digest, "admitted_scope_plan_digest")
        _require_digest(self.external_owner_digest, "external_owner_digest")

    @property
    def digest(self) -> str:
        return digest_mapping(asdict(self))

    @property
    def is_qualified(self) -> bool:
        return not self.compression_enabled and not self.deep_memory_enabled


@dataclass(frozen=True)
class CoreDeploymentWitness:
    """Canonical core-side authority facts and their descriptor/profile binding."""

    core_id: UUID
    schema_id: str
    schema_major: int
    schema_minor: int
    core_role: str
    deployment_state: DeploymentState
    descriptor_digest: str
    profile_digest: str

    def __post_init__(self) -> None:
        _require_uuid(self.core_id, "core_id")
        if (
            self.schema_id != SCHEMA_ID
            or (self.schema_major, self.schema_minor) != (SCHEMA_MAJOR, SCHEMA_MINOR)
        ):
            raise DeploymentAuthorityError("core witness must use the current native schema")
        if self.core_role not in {"STAGING", "ACTIVE_CORE"}:
            raise DeploymentAuthorityError("core witness role is not deployment-eligible")
        _require_digest(self.descriptor_digest, "descriptor_digest")
        _require_digest(self.profile_digest, "profile_digest")
        valid = {
            ("STAGING", DeploymentState.LEGACY_ACTIVE),
            ("STAGING", DeploymentState.CUTOVER_PENDING),
            ("ACTIVE_CORE", DeploymentState.NATIVE_ACTIVE),
        }
        if (self.core_role, self.deployment_state) not in valid:
            raise DeploymentAuthorityError("core role and deployment state are incompatible")

    @property
    def digest(self) -> str:
        return digest_mapping(
            {
                "core_id": str(self.core_id),
                "schema_id": self.schema_id,
                "schema_major": self.schema_major,
                "schema_minor": self.schema_minor,
                "core_role": self.core_role,
                "deployment_state": self.deployment_state.value,
                "descriptor_digest": self.descriptor_digest,
                "profile_digest": self.profile_digest,
            }
        )


@dataclass(frozen=True)
class AdmissionCompletionWitness:
    """Immutable activation evidence for one completed mutable admission.

    ``admission_identity_digest`` is the selector/core binding.  The two
    descriptor digests retain the distinct mutable-progress proof needed at
    activation: the ordinary full descriptor hash and the non-self-referential
    completed-progress hash recorded inside that descriptor.
    """

    admission_identity_digest: str
    completed_descriptor_digest: str
    completed_progress_digest: str
    native_core_id: UUID
    workspace_id: str
    whole_workspace_closure_digest: str
    profile_digest: str | None

    def __post_init__(self) -> None:
        for name in (
            "admission_identity_digest",
            "completed_descriptor_digest",
            "completed_progress_digest",
            "whole_workspace_closure_digest",
        ):
            _require_digest(getattr(self, name), name)
        _require_uuid(self.native_core_id, "native_core_id")
        if not isinstance(self.workspace_id, str) or not self.workspace_id:
            raise DeploymentAuthorityError("completion witness workspace_id must be non-empty text")
        if self.profile_digest is not None:
            _require_digest(self.profile_digest, "completion witness profile_digest")

    def payload(self) -> dict[str, str | None]:
        """Return the historical v1 payload exactly as it was persisted.

        The v1 shape deliberately remains discriminator-free because it is
        already embedded in durable Blocker-5 maintenance records.  The v2
        root form below is explicitly discriminated and versioned; decoding
        therefore never needs a fake workspace sentinel to distinguish them.
        """
        return {
            "admission_identity_digest": self.admission_identity_digest,
            "completed_descriptor_digest": self.completed_descriptor_digest,
            "completed_progress_digest": self.completed_progress_digest,
            "native_core_id": str(self.native_core_id),
            "profile_digest": self.profile_digest,
            "whole_workspace_closure_digest": self.whole_workspace_closure_digest,
            "workspace_id": self.workspace_id,
        }


@dataclass(frozen=True)
class RootAdmissionCompletionWitness:
    """Versioned root-wide completion evidence for the existing P6 slot.

    This is evidence, not an authority.  Its ``admission_identity_digest``
    and ``profile_digest`` properties allow the existing selector/core
    agreement machinery to retain its one completion-evidence slot without a
    root-specific controller or ledger.
    """

    data_root_identity: str
    root_admission_envelope_digest: str
    declared_census_digest: str
    discovered_census_digest: str
    manifest_digest: str
    external_owner_observation_digest: str
    geometry_disposition_table_digest: str
    target_representation_identity: str
    root_writer_freeze_witness_digest: str
    native_staging_core_id: UUID
    qualified_deployment_profile_digest: str
    root_profile_object_id: UUID
    root_profile_revision_id: UUID
    root_profile_ordinal: int
    root_membership_closure_digest: str
    normalization_closure_digest: str

    CONTRACT = "TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS"
    VERSION = 2

    def __post_init__(self) -> None:
        if not isinstance(self.data_root_identity, str) or not self.data_root_identity:
            raise DeploymentAuthorityError("root completion data_root_identity must be non-empty text")
        if not isinstance(self.target_representation_identity, str) or not self.target_representation_identity:
            raise DeploymentAuthorityError("root completion target_representation_identity must be non-empty text")
        for name in (
            "root_admission_envelope_digest",
            "declared_census_digest",
            "discovered_census_digest",
            "manifest_digest",
            "external_owner_observation_digest",
            "geometry_disposition_table_digest",
            "root_writer_freeze_witness_digest",
            "qualified_deployment_profile_digest",
            "root_membership_closure_digest",
            "normalization_closure_digest",
        ):
            _require_digest(getattr(self, name), name)
        for name in (
            "native_staging_core_id",
            "root_profile_object_id",
            "root_profile_revision_id",
        ):
            _require_uuid(getattr(self, name), name)
        if (
            not isinstance(self.root_profile_ordinal, int)
            or isinstance(self.root_profile_ordinal, bool)
            or self.root_profile_ordinal < 1
        ):
            raise DeploymentAuthorityError("root completion root_profile_ordinal must be positive")

    @property
    def admission_identity_digest(self) -> str:
        return self.root_admission_envelope_digest

    @property
    def native_core_id(self) -> UUID:
        return self.native_staging_core_id

    @property
    def profile_digest(self) -> str:
        return self.qualified_deployment_profile_digest

    def payload(self) -> dict[str, object]:
        return {
            "contract": self.CONTRACT,
            "version": self.VERSION,
            "data_root_identity": self.data_root_identity,
            "root_admission_envelope_digest": self.root_admission_envelope_digest,
            "declared_census_digest": self.declared_census_digest,
            "discovered_census_digest": self.discovered_census_digest,
            "manifest_digest": self.manifest_digest,
            "external_owner_observation_digest": self.external_owner_observation_digest,
            "geometry_disposition_table_digest": self.geometry_disposition_table_digest,
            "target_representation_identity": self.target_representation_identity,
            "root_writer_freeze_witness_digest": self.root_writer_freeze_witness_digest,
            "native_staging_core_id": str(self.native_staging_core_id),
            "qualified_deployment_profile_digest": self.qualified_deployment_profile_digest,
            "root_profile_object_id": str(self.root_profile_object_id),
            "root_profile_revision_id": str(self.root_profile_revision_id),
            "root_profile_ordinal": self.root_profile_ordinal,
            "root_membership_closure_digest": self.root_membership_closure_digest,
            "normalization_closure_digest": self.normalization_closure_digest,
        }


@dataclass(frozen=True)
class NativeGenesisCompletionWitness:
    """Self-contained fresh-origin evidence, not an activation capability.

    All initial declarations are retained without consulting external defaults.
    preparation_result_digest hashes preparation_payload(), excluding only that
    digest itself. digest hashes the complete payload. These are different,
    non-circular bindings. The immutable initial overlay lives only in intent;
    mutable owner overlays/process observations are not completion evidence.
    """

    data_root_identity: str
    operation_key: str
    intent_digest: str
    expanded_intent: GenesisIntent
    accepted_start_observation: GenesisAcceptedStart
    native_core_id: UUID
    core_relative_path: str
    schema_id: str
    schema_major: int
    schema_minor: int
    qualified_deployment_profile: QualifiedDeploymentProfile
    qualified_deployment_profile_digest: str
    representation_lane: GenesisRepresentationLane
    root_profile: GenesisRootProfileReference
    runtime_scope_plans: tuple[GenesisRuntimePlan, ...]
    runtime_plan_digest: str
    external_owner_projection: GenesisExternalOwnerProjection
    external_owner_closure_digest: str
    character_seed_completion: GenesisSeedCompletion
    initial_memberships: tuple[GenesisMembershipReference, ...]
    initial_membership_closure_digest: str
    quiescence_evidence_digest: str
    preparation_result_digest: str

    CONTRACT = "TORMENT_NATIVE_GENESIS_COMPLETION_WITNESS"
    VERSION = 1
    ORIGIN = "NATIVE_GENESIS"

    def __post_init__(self) -> None:
        for name, cls in (
            ("expanded_intent", GenesisIntent), ("accepted_start_observation", GenesisAcceptedStart),
            ("qualified_deployment_profile", QualifiedDeploymentProfile),
            ("representation_lane", GenesisRepresentationLane), ("root_profile", GenesisRootProfileReference),
            ("external_owner_projection", GenesisExternalOwnerProjection if self.VERSION == 1 else GenesisExternalOwnerProjectionV2),
        ):
            require_genesis(isinstance(getattr(self, name), cls), f"{name} must be typed")
        intent = self.expanded_intent.payload()
        require_genesis(intent["version"] == self.VERSION, "fresh completion and intent versions differ")
        if self.VERSION == 1:
            require_genesis(isinstance(self.character_seed_completion, GenesisSeedCompletion), "character_seed_completion must be typed")
        else:
            require_genesis(type(self.character_seed_completions) is tuple and
                all(isinstance(entry, GenesisAgentSeedCompletion) for entry in self.character_seed_completions),
                "character_seed_completions must be a typed tuple")
            agents = self.expanded_intent.initial_agents()
            require_genesis([entry.payload()["agent_id"] for entry in self.character_seed_completions] ==
                [agent["agent_id"] for agent in agents], "agent seed completions differ from canonical roster")
            for agent, entry in zip(agents, self.character_seed_completions, strict=True):
                expected = agent["character"].get("definition", {}).get("seed_id")
                require_genesis(entry.payload()["seed_id"] == expected, "agent seed identity differs from intent")
        require_genesis(self.data_root_identity == self.expanded_intent.data_root_identity and
                        self.operation_key == self.expanded_intent.operation_key and
                        self.intent_digest == self.expanded_intent.digest, "fresh completion intent binding mismatch")
        self.accepted_start_observation.require_intent(self.expanded_intent)
        require_uuid(self.native_core_id, "native_core_id")
        allocations = intent["allocations"]
        require_genesis(str(self.native_core_id) == allocations["core_id"] and
                        self.core_relative_path == allocations["core_relative_path"], "fresh core allocation mismatch")
        require_genesis(self.schema_id == SCHEMA_ID and type(self.schema_major) is int and
                        type(self.schema_minor) is int and
                        (self.schema_major, self.schema_minor) == (SCHEMA_MAJOR, SCHEMA_MINOR), "fresh completion requires current schema")
        require_genesis(self.qualified_deployment_profile.is_qualified, "fresh profile must be qualified")
        profile = self.qualified_profile_payload()
        require_genesis(all(profile[k] == v and type(profile[k]) is type(v) for k, v in intent["profile_choice"].items()), "fresh profile differs from immutable choice")
        require_genesis(self.representation_lane.payload() == intent["representation_lane"], "fresh representation lane mismatch")
        require_genesis(type(self.runtime_scope_plans) is tuple and
                        all(isinstance(p, GenesisRuntimePlan) for p in self.runtime_scope_plans), "fresh plans must be a typed tuple")
        require_genesis(self.runtime_scope_plans == self.expanded_intent.runtime_plans, "fresh plans differ from allocated routing bundle")
        require_genesis(self.runtime_plan_digest == runtime_plan_digest(self.runtime_scope_plans) ==
                        profile["admitted_scope_plan_digest"], "fresh runtime plan digest mismatch")
        require_genesis(self.external_owner_projection.digest == payload_digest(self.expanded_intent.external_owner_projection()),
                        "fresh external owner projection mismatch")
        require_genesis(self.external_owner_closure_digest == self.external_owner_projection.digest ==
                        profile["external_owner_digest"], "fresh external owner digest mismatch")
        require_genesis(self.qualified_deployment_profile_digest == self.qualified_deployment_profile.digest,
                        "fresh qualified profile digest mismatch")
        ref = self.root_profile.payload()
        for ref_key, allocation_key in (("core_id", "core_id"), ("profile_generation", "root_profile_generation"),
                                        ("profile_object_id", "root_profile_object_id"),
                                        ("profile_semantic_scope_id", "root_profile_semantic_scope_id")):
            require_genesis(ref[ref_key] == allocations[allocation_key], "fresh root profile allocation mismatch")
        require_genesis(type(self.initial_memberships) is tuple and
                        all(isinstance(m, GenesisMembershipReference) for m in self.initial_memberships),
                        "initial memberships must be a typed tuple")
        require_genesis(self.initial_memberships == tuple(sorted(self.initial_memberships, key=lambda m: m.canonical_key)),
                        "initial memberships must use canonical scope ordering")
        for key in ("relationship_id", "relationship_revision_id"):
            require_genesis(len({m.payload()[key] for m in self.initial_memberships}) == len(self.initial_memberships),
                            "initial membership references collide")
        require_genesis(self.initial_membership_closure_digest == initial_membership_closure_digest(
            self.root_profile, self.runtime_scope_plans, self.initial_memberships), "fresh membership closure digest mismatch")
        for agent in self.expanded_intent.initial_agents():
            seed = self.seed_completion_for(agent["agent_id"]).payload()
            require_genesis(seed["mode"] == agent["character"]["mode"], "fresh seed mode differs from intent")
            if seed["mode"] == "ENABLED":
                require_genesis(seed["definition_digest"] == payload_digest(agent["character"]["definition"]),
                                "fresh seed definition digest mismatch")
        require_digest(self.quiescence_evidence_digest, "quiescence_evidence_digest")
        require_genesis(self.preparation_result_digest == payload_digest(self.preparation_payload()),
                        "fresh preparation result digest mismatch")

    def seed_completion_for(self, agent_id):
        self.expanded_intent.initial_agent(agent_id)
        if self.VERSION == 1:
            return self.character_seed_completion
        return GenesisSeedCompletion.from_payload(next(entry.payload()["completion"]
            for entry in self.character_seed_completions if entry.payload()["agent_id"] == agent_id))

    @property
    def admission_identity_digest(self) -> str:
        return self.intent_digest

    @property
    def profile_digest(self) -> str:
        return self.qualified_deployment_profile_digest

    @property
    def digest(self) -> str:
        return payload_digest(self.payload())

    def qualified_profile_payload(self) -> dict[str, object]:
        """Exact seven-field convenience export, never an authority lookup."""
        return asdict(self.qualified_deployment_profile)

    def preparation_payload(self) -> dict[str, object]:
        result: dict[str, object] = {"contract": self.CONTRACT, "version": self.VERSION, "origin": self.ORIGIN}
        for field in fields(self):
            if field.name == "preparation_result_digest":
                continue
            value = getattr(self, field.name)
            if field.name == "qualified_deployment_profile":
                value = self.qualified_profile_payload()
            elif isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, tuple):
                value = [v.payload() for v in value]
            elif hasattr(value, "payload"):
                value = value.payload()
            result[field.name] = value
        return result

    def payload(self) -> dict[str, object]:
        return {**self.preparation_payload(), "preparation_result_digest": self.preparation_result_digest}

    @classmethod
    def from_payload(cls, value: object) -> NativeGenesisCompletionWitness:
        # Explicit dispatch; a v1-shaped document tagged v2 still refuses.
        if cls is NativeGenesisCompletionWitness and isinstance(value, Mapping) and type(value.get("version")) is int and value["version"] == 2:
            return NativeGenesisCompletionWitnessV2.from_payload(value)
        # Validate finite JSON before comparisons (True must never alias 1).
        payload_digest(value)
        value = exact_object(value, "contract version origin " + " ".join(f.name for f in fields(cls)), "fresh completion")
        require_genesis(value["contract"] == cls.CONTRACT and type(value["version"]) is int and
                        value["version"] == cls.VERSION and value["origin"] == cls.ORIGIN,
                        "unsupported fresh completion discriminator")
        profile = exact_object(value["qualified_deployment_profile"], " ".join(f.name for f in fields(QualifiedDeploymentProfile)), "qualified profile")
        require_genesis(isinstance(value["initial_memberships"], list), "initial memberships must be an array")
        from .genesis_contracts import uuid_text
        uuid_text(value["native_core_id"], "native_core_id")
        typed = dict(value)
        for name, contract in (("expanded_intent", GenesisIntent), ("accepted_start_observation", GenesisAcceptedStart),
                               ("representation_lane", GenesisRepresentationLane), ("root_profile", GenesisRootProfileReference),
                               ("external_owner_projection", GenesisExternalOwnerProjection if cls.VERSION == 1 else GenesisExternalOwnerProjectionV2)):
            typed[name] = contract.from_payload(value[name])
        if cls.VERSION == 1:
            typed["character_seed_completion"] = GenesisSeedCompletion.from_payload(value["character_seed_completion"])
        else:
            require_genesis(isinstance(value["character_seed_completions"], list), "agent seed completions must be an array")
            typed["character_seed_completions"] = tuple(GenesisAgentSeedCompletion.from_payload(entry)
                for entry in value["character_seed_completions"])
        typed["native_core_id"] = UUID(value["native_core_id"])
        typed["qualified_deployment_profile"] = QualifiedDeploymentProfile(**profile)
        typed["runtime_scope_plans"] = ordered_runtime_plans(value["runtime_scope_plans"])
        typed["initial_memberships"] = tuple(GenesisMembershipReference.from_payload(m) for m in value["initial_memberships"])
        for key in ("contract", "version", "origin"):
            del typed[key]
        return cls(**typed)


@dataclass(frozen=True)
class NativeGenesisCompletionWitnessV2(NativeGenesisCompletionWitness):
    """Fresh roster evidence; no singular seed field is serialized or decoded."""
    VERSION = 2
    character_seed_completion: ClassVar[None] = None
    character_seed_completions: tuple[GenesisAgentSeedCompletion, ...]


CompletionWitness: TypeAlias = AdmissionCompletionWitness | RootAdmissionCompletionWitness | NativeGenesisCompletionWitness


@dataclass(frozen=True)
class RootDispositionOwnerResult:
    """One immutable synthetic owner result under the frozen geometry plan."""

    owner_identity: str
    source_observation_digest: str
    disposition: str
    outcome: str
    geometry_transition_identity: str

    def __post_init__(self) -> None:
        for name in ("owner_identity", "disposition", "outcome", "geometry_transition_identity"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise DeploymentAuthorityError(f"root disposition {name} must be non-empty text")
        _require_digest(self.source_observation_digest, "root disposition source_observation_digest")

    def payload(self) -> dict[str, str]:
        return {
            "owner_identity": self.owner_identity,
            "source_observation_digest": self.source_observation_digest,
            "disposition": self.disposition,
            "outcome": self.outcome,
            "geometry_transition_identity": self.geometry_transition_identity,
        }


@dataclass(frozen=True)
class RootDispositionExecutionReceipt:
    """Immutable post-P6 evidence; it cannot activate a selector by itself."""

    root_admission_envelope_digest: str
    native_staging_core_id: UUID
    geometry_disposition_table_digest: str
    geometry_transition_identity: str
    owner_results: tuple[RootDispositionOwnerResult, ...]

    CONTRACT = "TORMENT_ROOT_DISPOSITION_EXECUTION_RECEIPT"
    VERSION = 1

    def __post_init__(self) -> None:
        for name in ("root_admission_envelope_digest", "geometry_disposition_table_digest"):
            _require_digest(getattr(self, name), name)
        _require_uuid(self.native_staging_core_id, "native_staging_core_id")
        if not isinstance(self.geometry_transition_identity, str) or not self.geometry_transition_identity:
            raise DeploymentAuthorityError("geometry_transition_identity must be non-empty text")
        if not isinstance(self.owner_results, tuple) or not self.owner_results:
            raise DeploymentAuthorityError("root disposition receipt requires owner results")
        if any(not isinstance(item, RootDispositionOwnerResult) for item in self.owner_results):
            raise DeploymentAuthorityError("root disposition receipt owner results must be typed")
        ordered = tuple(sorted(self.owner_results, key=lambda item: item.owner_identity))
        if len({item.owner_identity for item in ordered}) != len(ordered):
            raise DeploymentAuthorityError("root disposition receipt owner identities must be unique")
        expected_dispositions = dict(FROZEN_ROOT_GEOMETRY_DISPOSITIONS)
        if {item.owner_identity for item in ordered} != set(expected_dispositions):
            raise DeploymentAuthorityError("root disposition receipt must cover the frozen owner table")
        if any(expected_dispositions[item.owner_identity] != item.disposition for item in ordered):
            raise DeploymentAuthorityError("root disposition receipt conflicts with the frozen owner disposition")
        if any(item.geometry_transition_identity != self.geometry_transition_identity for item in ordered):
            raise DeploymentAuthorityError("root disposition receipt owner transition identities disagree")
        object.__setattr__(self, "owner_results", ordered)

    @property
    def digest(self) -> str:
        return digest_mapping(self.payload())

    def payload(self) -> dict[str, object]:
        return {
            "contract": self.CONTRACT,
            "version": self.VERSION,
            "root_admission_envelope_digest": self.root_admission_envelope_digest,
            "native_staging_core_id": str(self.native_staging_core_id),
            "geometry_disposition_table_digest": self.geometry_disposition_table_digest,
            "geometry_transition_identity": self.geometry_transition_identity,
            "owner_results": [item.payload() for item in self.owner_results],
        }


@dataclass(frozen=True)
class SelectorState:
    """One validated external-selector singleton snapshot."""

    generation: int
    deployment_state: DeploymentState
    core_id: UUID | None
    core_relative_path: str | None
    descriptor_digest: str | None
    profile_digest: str | None
    core_witness_digest: str | None
    updated_at_ns: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.generation, int)
            or isinstance(self.generation, bool)
            or self.generation < 0
        ):
            raise DeploymentAuthorityError("selector generation must be non-negative")
        if (
            not isinstance(self.updated_at_ns, int)
            or isinstance(self.updated_at_ns, bool)
            or self.updated_at_ns < 0
        ):
            raise DeploymentAuthorityError("selector updated_at_ns must be non-negative")
        if self.deployment_state is DeploymentState.LEGACY_ACTIVE:
            if any(
                value is not None
                for value in (
                    self.core_id,
                    self.core_relative_path,
                    self.descriptor_digest,
                    self.profile_digest,
                    self.core_witness_digest,
                )
            ):
                raise DeploymentAuthorityError("LEGACY_ACTIVE selector state must not name a core")
            return
        _require_uuid(self.core_id, "selector core_id")
        _require_relative_core_path(self.core_relative_path)
        _require_digest(self.descriptor_digest, "selector descriptor_digest")
        _require_digest(self.profile_digest, "selector profile_digest")
        _require_digest(self.core_witness_digest, "selector core_witness_digest")


@dataclass(frozen=True)
class DeploymentResolution:
    """Pure deployment resolver output with a concise, stable refusal reason."""

    mode: DeploymentResolutionMode
    reason: str
    selector_state: SelectorState | None = None
    core_witness: CoreDeploymentWitness | None = None


def canonical_json(value: Mapping[str, Any]) -> str:
    """Return the one JSON encoding used for digests and immutable intent evidence."""

    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=True)


def digest_mapping(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def require_digest(value: object, label: str) -> str:
    return _require_digest(value, label)


def require_relative_core_path(value: object) -> str:
    return _require_relative_core_path(value)


def require_uuid(value: object, label: str) -> UUID:
    return _require_uuid(value, label)


def completion_witness_from_payload(value: object) -> CompletionWitness:
    """Explicit dispatch for historical v1, migration root-v2, and fresh Genesis.

    V1 remains untagged with its historical optional profile digest. Unknown
    tags (including explicit null tags) cannot fall through to that branch.
    """

    if not isinstance(value, Mapping):
        raise DeploymentAuthorityError("completion witness payload must be an object")
    contract = value.get("contract")
    version = value.get("version")
    try:
        if contract == NativeGenesisCompletionWitness.CONTRACT:
            return NativeGenesisCompletionWitness.from_payload(value)
        if contract == RootAdmissionCompletionWitness.CONTRACT and version == RootAdmissionCompletionWitness.VERSION:
            return RootAdmissionCompletionWitness(
                data_root_identity=value["data_root_identity"],
                root_admission_envelope_digest=value["root_admission_envelope_digest"],
                declared_census_digest=value["declared_census_digest"],
                discovered_census_digest=value["discovered_census_digest"],
                manifest_digest=value["manifest_digest"],
                external_owner_observation_digest=value["external_owner_observation_digest"],
                geometry_disposition_table_digest=value["geometry_disposition_table_digest"],
                target_representation_identity=value["target_representation_identity"],
                root_writer_freeze_witness_digest=value["root_writer_freeze_witness_digest"],
                native_staging_core_id=UUID(value["native_staging_core_id"]),
                qualified_deployment_profile_digest=value["qualified_deployment_profile_digest"],
                root_profile_object_id=UUID(value["root_profile_object_id"]),
                root_profile_revision_id=UUID(value["root_profile_revision_id"]),
                root_profile_ordinal=value["root_profile_ordinal"],
                root_membership_closure_digest=value["root_membership_closure_digest"],
                normalization_closure_digest=value["normalization_closure_digest"],
            )
        historical_keys = {
            "admission_identity_digest", "completed_descriptor_digest", "completed_progress_digest",
            "native_core_id", "workspace_id", "whole_workspace_closure_digest",
        }
        if "contract" in value or "version" in value or not historical_keys <= value.keys():
            raise DeploymentAuthorityError("completion witness contract/version is unsupported")
        return AdmissionCompletionWitness(
            admission_identity_digest=value["admission_identity_digest"],
            completed_descriptor_digest=value["completed_descriptor_digest"],
            completed_progress_digest=value["completed_progress_digest"],
            native_core_id=UUID(value["native_core_id"]),
            workspace_id=value["workspace_id"],
            whole_workspace_closure_digest=value["whole_workspace_closure_digest"],
            profile_digest=value.get("profile_digest"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DeploymentAuthorityError("completion witness payload is malformed") from exc


def root_disposition_receipt_from_payload(value: object) -> RootDispositionExecutionReceipt:
    """Decode the one immutable receipt representation recorded after P6."""

    if not isinstance(value, Mapping):
        raise DeploymentAuthorityError("root disposition receipt payload must be an object")
    if (
        value.get("contract") != RootDispositionExecutionReceipt.CONTRACT
        or value.get("version") != RootDispositionExecutionReceipt.VERSION
    ):
        raise DeploymentAuthorityError("root disposition receipt contract/version is unsupported")
    raw_results = value.get("owner_results")
    if not isinstance(raw_results, list):
        raise DeploymentAuthorityError("root disposition receipt owner results are malformed")
    if any(not isinstance(item, Mapping) for item in raw_results):
        raise DeploymentAuthorityError("root disposition receipt owner results are malformed")
    try:
        return RootDispositionExecutionReceipt(
            root_admission_envelope_digest=value["root_admission_envelope_digest"],
            native_staging_core_id=UUID(value["native_staging_core_id"]),
            geometry_disposition_table_digest=value["geometry_disposition_table_digest"],
            geometry_transition_identity=value["geometry_transition_identity"],
            owner_results=tuple(
                RootDispositionOwnerResult(
                    owner_identity=item["owner_identity"],
                    source_observation_digest=item["source_observation_digest"],
                    disposition=item["disposition"],
                    outcome=item["outcome"],
                    geometry_transition_identity=item["geometry_transition_identity"],
                )
                for item in raw_results
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DeploymentAuthorityError("root disposition receipt payload is malformed") from exc


def _require_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise DeploymentAuthorityError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_relative_core_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise DeploymentAuthorityError("selector core_relative_path must be non-empty text")
    if "/" in value or "\\" in value or value in {".", ".."} or ".." in value:
        raise DeploymentAuthorityError("selector core_relative_path must be a contained core filename")
    if not value.endswith(".db"):
        raise DeploymentAuthorityError("selector core_relative_path must name a .db core")
    return value


def _require_uuid(value: object, label: str) -> UUID:
    if not isinstance(value, UUID):
        raise DeploymentAuthorityError(f"{label} must be a UUID")
    try:
        return native_id_from_text(str(value))
    except Exception as exc:
        raise DeploymentAuthorityError(f"{label} must be a canonical UUIDv4") from exc


__all__ = [
    "AdmissionCompletionWitness",
    "CompletionWitness",
    "CoreDeploymentWitness",
    "DeploymentResolution",
    "DeploymentResolutionMode",
    "DeploymentState",
    "FROZEN_ROOT_GEOMETRY_DISPOSITIONS",
    "QualifiedDeploymentProfile",
    "NativeGenesisCompletionWitness",
    "RootAdmissionCompletionWitness",
    "RootDispositionExecutionReceipt",
    "RootDispositionOwnerResult",
    "SelectorState",
    "canonical_json",
    "completion_witness_from_payload",
    "digest_mapping",
    "require_digest",
    "require_relative_core_path",
    "require_uuid",
    "root_disposition_receipt_from_payload",
]
