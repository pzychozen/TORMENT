"""Typed, canonical facts shared by B5-A2 deployment administration.

These values describe deployment authority only.  They do not grant a memory
writer, select a Fabric backend, or expose a public routing capability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any, Mapping, TypeAlias
from uuid import UUID

from .errors import DeploymentAuthorityError
from .ids import native_id_from_text
from .schema import SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR


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


CompletionWitness: TypeAlias = AdmissionCompletionWitness | RootAdmissionCompletionWitness


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
    """Decode durable v1 or explicitly discriminated root-v2 evidence."""

    if not isinstance(value, Mapping):
        raise DeploymentAuthorityError("completion witness payload must be an object")
    contract = value.get("contract")
    version = value.get("version")
    try:
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
        if contract is not None or version is not None:
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
