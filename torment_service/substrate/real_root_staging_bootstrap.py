"""Source-free P1_BOOTSTRAP for one contained inert real-root staging core.

This module owns only native prerequisite construction and exact inert reuse.
It never reads legacy source surfaces, records a root envelope, creates a
selector, or changes deployment authority.  A stale inert core is retained
untouched and must be superseded by a distinct request/path/core identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sqlite3
from uuid import UUID

from .connection import (
    SubstrateConnectionError,
    open_existing_native_core_connection,
    open_new_native_core_connection,
)
from .deployment_core_maintenance import (
    CoreDeploymentInspection,
    inspect_contained_core_deployment,
)
from .deployment_types import DeploymentState
from .ids import native_id_from_bytes, native_id_to_bytes
from .migration.root_scope import RootScopeKey, RootScopeKind
from .objects import NativeObjectService, ObjectState
from .root_profile import (
    ROOT_NATIVE_PROFILE_GENERATION_KIND,
    RootProfileGenerationRef,
    current_root_profile_generation,
    root_profile_generation_payload,
)
from .root_scope_membership import (
    RootScopeMembershipReader,
    RootScopeMembershipRecord,
    RootScopeMembershipService,
    RootScopeMembershipWitness,
)
from .runtime_binding import NativeMemoryRuntimeScope
from .schema import create_schema


class P1StagingBootstrapError(RuntimeError):
    """A P1 request cannot create or exactly reuse an inert staging core."""


class P1StaleInertCore(P1StagingBootstrapError):
    """A retained inert core differs from the requested prerequisite bundle."""


class P1NonInertCore(P1StagingBootstrapError):
    """An existing core has asserted authority and can never be reused by P1."""


class P1ExistingCoreDisposition(str, Enum):
    CREATED = "CREATED"
    EXACT_INERT_MATCH = "EXACT_INERT_MATCH"
    STALE_INERT = "STALE_INERT"
    NON_INERT = "NON_INERT"


@dataclass(frozen=True)
class RootProfileBootstrap:
    """Typed native facts for one initial ROOT_NATIVE_PROFILE_GENERATION."""

    profile_object_id: UUID
    profile_generation: int
    identity_namespace_id: UUID
    identity_namespace_key: str
    semantic_scope_id: UUID
    semantic_scope_key: str
    idempotency_namespace_id: UUID
    idempotency_namespace_key: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _positive(self.profile_generation, "profile_generation")
        _uuid_fields(
            self.profile_object_id,
            self.identity_namespace_id,
            self.semantic_scope_id,
            self.idempotency_namespace_id,
        )
        _text_fields(
            self.identity_namespace_key,
            self.semantic_scope_key,
            self.idempotency_namespace_key,
            self.idempotency_key,
        )


@dataclass(frozen=True)
class RuntimeScopeBootstrap:
    """Typed native runtime/membership facts, with no legacy-source locator."""

    runtime_scope: NativeMemoryRuntimeScope
    identity_namespace_key: str
    semantic_scope_key: str
    legacy_source_namespace_key: str
    membership_identity_namespace_id: UUID
    membership_identity_namespace_key: str
    idempotency_namespace_id: UUID
    idempotency_namespace_key: str
    idempotency_key: str
    membership_witness: RootScopeMembershipWitness

    def __post_init__(self) -> None:
        if not isinstance(self.runtime_scope, NativeMemoryRuntimeScope):
            raise ValueError("runtime_scope must be typed")
        if self.runtime_scope.scope_kind not in {"PRIVATE_AGENT", "SHARED_DOMAIN"}:
            raise ValueError("runtime scope kind is unsupported")
        _uuid_fields(
            self.membership_identity_namespace_id,
            self.idempotency_namespace_id,
        )
        _text_fields(
            self.identity_namespace_key,
            self.semantic_scope_key,
            self.legacy_source_namespace_key,
            self.membership_identity_namespace_key,
            self.idempotency_namespace_key,
            self.idempotency_key,
        )
        if not isinstance(self.membership_witness, RootScopeMembershipWitness):
            raise ValueError("membership_witness must be typed")


@dataclass(frozen=True)
class P1StagingBootstrapRequest:
    """Only native prerequisite facts required for a contained inert core."""

    data_root: Path
    native_core_database_path: Path
    core_id: UUID
    root_profile: RootProfileBootstrap
    runtime_scopes: tuple[RuntimeScopeBootstrap, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.core_id, UUID):
            raise ValueError("core_id must be a UUID")
        if not isinstance(self.root_profile, RootProfileBootstrap):
            raise ValueError("root_profile must be typed")
        if not isinstance(self.runtime_scopes, tuple) or any(
            not isinstance(item, RuntimeScopeBootstrap) for item in self.runtime_scopes
        ):
            raise ValueError("runtime_scopes must be a tuple of typed prerequisites")
        keys = tuple(_scope_key(item.runtime_scope) for item in self.runtime_scopes)
        if len(set(keys)) != len(keys):
            raise ValueError("runtime scope prerequisites must not collide")


@dataclass(frozen=True)
class P1StagingBootstrapResult:
    """The only recoverable P1 facts; no authority capability is returned."""

    disposition: P1ExistingCoreDisposition
    core_path: Path
    core_id: UUID
    root_profile: RootProfileGenerationRef
    memberships: tuple[RootScopeMembershipRecord, ...]

    @property
    def reusable(self) -> bool:
        return self.disposition in {
            P1ExistingCoreDisposition.CREATED,
            P1ExistingCoreDisposition.EXACT_INERT_MATCH,
        }


class RealRootStagingBootstrap:
    """P1_BOOTSTRAP lifecycle authority for native-only inert prerequisites."""

    def classify_existing(self, request: P1StagingBootstrapRequest) -> P1ExistingCoreDisposition:
        """Classify an existing path without changing it.

        The caller can use STALE_INERT to retain that core and bootstrap a new,
        distinct request. NON_INERT is never a lawful P1 reuse/supersession
        target.
        """

        core_path = _contained_core_path(request, create_parent=False)
        if not core_path.exists():
            raise P1StagingBootstrapError("P1 existing-core classification requires an existing target")
        if core_path.is_symlink() or not core_path.is_file():
            raise P1StagingBootstrapError("P1 core target must be one real database file")
        try:
            inspection = inspect_contained_core_deployment(
                data_root=_root(request),
                core_relative_path=core_path.name,
            )
        except Exception as exc:
            raise P1StagingBootstrapError("P1 existing core is not a qualified contained core") from exc
        if not _inert_matches_identity(inspection, request.core_id):
            return (
                P1ExistingCoreDisposition.STALE_INERT
                if _is_inert(inspection)
                else P1ExistingCoreDisposition.NON_INERT
            )
        try:
            with open_existing_native_core_connection(core_path) as opened:
                profile, memberships = _verify_prerequisites(opened.connection, request)
        except Exception:
            return P1ExistingCoreDisposition.STALE_INERT
        if profile.core_id != request.core_id:
            return P1ExistingCoreDisposition.STALE_INERT
        return P1ExistingCoreDisposition.EXACT_INERT_MATCH

    def bootstrap(self, request: P1StagingBootstrapRequest) -> P1StagingBootstrapResult:
        """Create or exactly reuse a contained STAGING / LEGACY_ACTIVE core."""

        core_path = _contained_core_path(request, create_parent=True)
        if core_path.exists():
            disposition = self.classify_existing(request)
            if disposition is P1ExistingCoreDisposition.EXACT_INERT_MATCH:
                with open_existing_native_core_connection(core_path) as opened:
                    profile, memberships = _verify_prerequisites(opened.connection, request)
                return P1StagingBootstrapResult(
                    disposition=disposition,
                    core_path=core_path,
                    core_id=request.core_id,
                    root_profile=profile,
                    memberships=memberships,
                )
            if disposition is P1ExistingCoreDisposition.STALE_INERT:
                raise P1StaleInertCore(
                    "P1 target is retained stale inert state; bootstrap a new path and core identity"
                )
            raise P1NonInertCore("P1 refuses an existing pending, ever-active, or active core")

        try:
            with open_new_native_core_connection(core_path) as opened:
                metadata = create_schema(opened.connection, core_id=request.core_id)
                if native_id_from_bytes(metadata.core_id) != request.core_id:
                    raise P1StagingBootstrapError("P1 schema bootstrap returned another core identity")
                _persist_prerequisites(opened.connection, request)
                profile, memberships = _verify_prerequisites(opened.connection, request)
        except (P1StagingBootstrapError, P1StaleInertCore, P1NonInertCore):
            raise
        except Exception as exc:
            raise P1StagingBootstrapError("P1 native prerequisite bootstrap refused") from exc

        inspection = inspect_contained_core_deployment(
            data_root=_root(request),
            core_relative_path=core_path.name,
        )
        if not _inert_matches_identity(inspection, request.core_id):
            raise P1StagingBootstrapError("P1 bootstrap did not end in an exact inert state")
        return P1StagingBootstrapResult(
            disposition=P1ExistingCoreDisposition.CREATED,
            core_path=core_path,
            core_id=request.core_id,
            root_profile=profile,
            memberships=memberships,
        )


def bootstrap_real_root_staging(
    request: P1StagingBootstrapRequest,
) -> P1StagingBootstrapResult:
    """Convenience entrypoint for the typed P1_BOOTSTRAP workflow."""

    return RealRootStagingBootstrap().bootstrap(request)


def _persist_prerequisites(connection: sqlite3.Connection, request: P1StagingBootstrapRequest) -> None:
    profile_request = request.root_profile
    _ensure_namespace(
        connection, "identity_namespaces", "identity_namespace_id", "namespace_key",
        profile_request.identity_namespace_id, profile_request.identity_namespace_key,
    )
    _ensure_namespace(
        connection, "semantic_scopes", "semantic_scope_id", "scope_key",
        profile_request.semantic_scope_id, profile_request.semantic_scope_key,
    )
    _ensure_namespace(
        connection, "idempotency_namespaces", "idempotency_namespace_id", "namespace_key",
        profile_request.idempotency_namespace_id, profile_request.idempotency_namespace_key,
    )
    for item in request.runtime_scopes:
        scope = item.runtime_scope
        _ensure_namespace(
            connection, "identity_namespaces", "identity_namespace_id", "namespace_key",
            scope.identity_namespace_id, item.identity_namespace_key,
        )
        _ensure_namespace(
            connection, "semantic_scopes", "semantic_scope_id", "scope_key",
            scope.semantic_scope_id, item.semantic_scope_key,
        )
        _ensure_namespace(
            connection, "legacy_source_namespaces", "legacy_source_namespace_id", "source_key",
            scope.legacy_source_namespace_id, item.legacy_source_namespace_key,
        )
        _ensure_namespace(
            connection, "identity_namespaces", "identity_namespace_id", "namespace_key",
            item.membership_identity_namespace_id, item.membership_identity_namespace_key,
        )
        _ensure_namespace(
            connection, "idempotency_namespaces", "idempotency_namespace_id", "namespace_key",
            item.idempotency_namespace_id, item.idempotency_namespace_key,
        )

    result = NativeObjectService(connection).create_object(
        idempotency_namespace_id=profile_request.idempotency_namespace_id,
        idempotency_key=profile_request.idempotency_key,
        object_id=profile_request.profile_object_id,
        state=ObjectState(
            identity_namespace_id=profile_request.identity_namespace_id,
            semantic_scope_id=profile_request.semantic_scope_id,
            object_kind=ROOT_NATIVE_PROFILE_GENERATION_KIND,
            existence_state="EXISTS",
            lifecycle_state="ACTIVE",
            lifecycle_authoritative=True,
            governance_state="QUALIFIED",
            authority_category="EVIDENCE",
            payload=root_profile_generation_payload(profile_request.profile_generation),
            payload_format="JSON",
        ),
    )
    if result.object_id != profile_request.profile_object_id:
        raise P1StagingBootstrapError("P1 root profile object identity disagrees")

    profile = current_root_profile_generation(connection)
    service = RootScopeMembershipService(connection)
    for item in request.runtime_scopes:
        service.admit(
            profile=profile,
            runtime_scope=item.runtime_scope,
            witness=item.membership_witness,
            membership_identity_namespace_id=item.membership_identity_namespace_id,
            idempotency_namespace_id=item.idempotency_namespace_id,
            idempotency_key=item.idempotency_key,
        )


def _verify_prerequisites(
    connection: sqlite3.Connection,
    request: P1StagingBootstrapRequest,
) -> tuple[RootProfileGenerationRef, tuple[RootScopeMembershipRecord, ...]]:
    profile_request = request.root_profile
    _require_namespace(
        connection, "identity_namespaces", "identity_namespace_id", "namespace_key",
        profile_request.identity_namespace_id, profile_request.identity_namespace_key,
    )
    _require_namespace(
        connection, "semantic_scopes", "semantic_scope_id", "scope_key",
        profile_request.semantic_scope_id, profile_request.semantic_scope_key,
    )
    _require_namespace(
        connection, "idempotency_namespaces", "idempotency_namespace_id", "namespace_key",
        profile_request.idempotency_namespace_id, profile_request.idempotency_namespace_key,
    )
    for item in request.runtime_scopes:
        scope = item.runtime_scope
        _require_namespace(
            connection, "identity_namespaces", "identity_namespace_id", "namespace_key",
            scope.identity_namespace_id, item.identity_namespace_key,
        )
        _require_namespace(
            connection, "semantic_scopes", "semantic_scope_id", "scope_key",
            scope.semantic_scope_id, item.semantic_scope_key,
        )
        _require_namespace(
            connection, "legacy_source_namespaces", "legacy_source_namespace_id", "source_key",
            scope.legacy_source_namespace_id, item.legacy_source_namespace_key,
        )
        _require_namespace(
            connection, "identity_namespaces", "identity_namespace_id", "namespace_key",
            item.membership_identity_namespace_id, item.membership_identity_namespace_key,
        )
        _require_namespace(
            connection, "idempotency_namespaces", "idempotency_namespace_id", "namespace_key",
            item.idempotency_namespace_id, item.idempotency_namespace_key,
        )

    profile = current_root_profile_generation(connection)
    if (
        profile.core_id != request.core_id
        or profile.profile_object_id != profile_request.profile_object_id
        or profile.profile_generation != profile_request.profile_generation
        or profile.profile_semantic_scope_id != profile_request.semantic_scope_id
    ):
        raise P1StagingBootstrapError("P1 root profile prerequisite facts disagree")
    records = RootScopeMembershipReader(connection).recover(profile)
    if len(records) != len(request.runtime_scopes):
        raise P1StagingBootstrapError("P1 root membership count disagrees")
    by_key = {record.runtime_key.scope_key: record for record in records}
    for item in request.runtime_scopes:
        key = _scope_key(item.runtime_scope)
        record = by_key.get(key)
        if (
            record is None
            or not record.active
            or record.semantic_scope_id != item.runtime_scope.semantic_scope_id
            or record.membership_identity_namespace_id != item.membership_identity_namespace_id
            or record.witness != item.membership_witness
        ):
            raise P1StagingBootstrapError("P1 root membership prerequisite facts disagree")
    return profile, records


def _contained_core_path(request: P1StagingBootstrapRequest, *, create_parent: bool) -> Path:
    root = _root(request)
    substrate = root / "substrate"
    core_root = substrate / "cores"
    if substrate.exists() and substrate.is_symlink():
        raise P1StagingBootstrapError("P1 substrate directory must not be a symlink")
    if core_root.exists() and core_root.is_symlink():
        raise P1StagingBootstrapError("P1 cores directory must not be a symlink")
    if create_parent:
        core_root.mkdir(parents=True, exist_ok=True)
    if not core_root.is_dir():
        raise P1StagingBootstrapError("P1 contained core directory is unavailable")

    supplied = Path(request.native_core_database_path).expanduser()
    if not supplied.is_absolute():
        raise P1StagingBootstrapError("P1 native core path must be absolute")
    if supplied.is_symlink():
        raise P1StagingBootstrapError("P1 native core path must not be a symlink")
    target = supplied.resolve(strict=False)
    expected_parent = core_root.resolve(strict=True)
    if target.parent != expected_parent or target.suffix.lower() != ".db":
        raise P1StagingBootstrapError("P1 core must be one .db filename beneath data_root/substrate/cores")
    return target


def _root(request: P1StagingBootstrapRequest) -> Path:
    root = Path(request.data_root).expanduser().resolve()
    if not root.is_dir() or root.is_symlink():
        raise P1StagingBootstrapError("P1 data root must be an existing real directory")
    return root


def _ensure_namespace(
    connection: sqlite3.Connection,
    table: str,
    id_column: str,
    key_column: str,
    value: UUID,
    key: str,
) -> None:
    row = connection.execute(
        f"SELECT {id_column},{key_column} FROM {table} WHERE {id_column}=? OR {key_column}=?",
        (native_id_to_bytes(value), key),
    ).fetchone()
    if row is None:
        if table == "idempotency_namespaces":
            connection.execute(
                f"INSERT INTO {table} ({id_column},{key_column}) VALUES (?,?)",
                (native_id_to_bytes(value), key),
            )
        else:
            connection.execute(
                f"INSERT INTO {table} ({id_column},{key_column},created_at_ns) VALUES (?,?,0)",
                (native_id_to_bytes(value), key),
            )
        return
    if row != (native_id_to_bytes(value), key):
        raise P1StagingBootstrapError("P1 native namespace facts conflict")


def _require_namespace(
    connection: sqlite3.Connection,
    table: str,
    id_column: str,
    key_column: str,
    value: UUID,
    key: str,
) -> None:
    row = connection.execute(
        f"SELECT {id_column},{key_column} FROM {table} WHERE {id_column}=?",
        (native_id_to_bytes(value),),
    ).fetchone()
    if row != (native_id_to_bytes(value), key):
        raise P1StagingBootstrapError("P1 native namespace facts disagree")


def _inert_matches_identity(inspection: CoreDeploymentInspection, core_id: UUID) -> bool:
    return _is_inert(inspection) and inspection.core_id == core_id


def _is_inert(inspection: CoreDeploymentInspection) -> bool:
    return (
        inspection.core_role == "STAGING"
        and inspection.deployment_state is DeploymentState.LEGACY_ACTIVE
        and inspection.witness is None
        and not inspection.ever_active
    )


def _scope_key(scope: NativeMemoryRuntimeScope) -> RootScopeKey:
    if scope.scope_kind == "PRIVATE_AGENT":
        return RootScopeKey(scope.workspace_id, RootScopeKind.PRIVATE, agent_id=scope.agent_id)
    if scope.scope_kind == "SHARED_DOMAIN":
        return RootScopeKey(scope.workspace_id, RootScopeKind.SHARED, domain_id=scope.domain_id)
    raise P1StagingBootstrapError("P1 runtime scope kind is unsupported")


def _uuid_fields(*values: UUID) -> None:
    if any(not isinstance(value, UUID) for value in values):
        raise ValueError("P1 native identifiers must be UUIDs")


def _positive(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label} must be a positive integer")


def _text_fields(*values: str) -> None:
    if any(not isinstance(value, str) or not value or len(value) > 240 for value in values):
        raise ValueError("P1 native namespace and idempotency keys must be bounded non-empty text")


__all__ = [
    "P1ExistingCoreDisposition",
    "P1NonInertCore",
    "P1StagingBootstrapError",
    "P1StagingBootstrapRequest",
    "P1StagingBootstrapResult",
    "P1StaleInertCore",
    "RealRootStagingBootstrap",
    "RootProfileBootstrap",
    "RuntimeScopeBootstrap",
    "bootstrap_real_root_staging",
]
