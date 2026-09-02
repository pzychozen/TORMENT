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
from typing import Any, Mapping
from uuid import UUID

from .errors import DeploymentAuthorityError
from .ids import native_id_from_text
from .schema import SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR


_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


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
    "CoreDeploymentWitness",
    "DeploymentResolution",
    "DeploymentResolutionMode",
    "DeploymentState",
    "QualifiedDeploymentProfile",
    "SelectorState",
    "canonical_json",
    "digest_mapping",
    "require_digest",
    "require_relative_core_path",
    "require_uuid",
]
