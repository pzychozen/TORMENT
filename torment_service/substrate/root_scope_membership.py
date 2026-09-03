"""Relationship-backed root-scope membership and non-materializing resolution.

This module owns only the root-qualified membership fact described by Phase
9D-R0: a semantic memory scope is an active member of an existing root-profile
generation.  Existing schema relationships own durability and lifecycle;
``NativeMemoryRuntimeScope`` continues to own the scope namespace bundle.

It deliberately has no Fabric, workspace, agent, graph, selector, provider, or
embedding dependency.  In particular, resolution cannot materialize a legacy
scope when membership is absent.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Final
from uuid import UUID

from .errors import SubstrateConfigurationError, SubstrateRevisionConflict
from .ids import native_id_to_bytes
from .objects import NativeObjectService
from .relationships import Endpoint, NativeRelationshipService, RelationshipState
from .runtime_binding import NativeMemoryRuntimeScope
from .schema import open_schema
from .migration.root_scope import RootScopeKey, RootScopeKind


ROOT_SCOPE_MEMBERSHIP_KIND: Final[str] = "ROOT_SCOPE_MEMBERSHIP"
ROOT_SCOPE_MEMBERSHIP_CONTRACT: Final[str] = "TMS-ROOT-SCOPE-MEMBERSHIP-1"
_ROOT_PROFILE_ENDPOINT_ROLE: Final[str] = "ROOT_PROFILE_GENERATION"
_ACTIVE: Final[str] = "ACTIVE"
_RETIRED: Final[str] = "RETIRED"
_PRIVATE: Final[str] = "PRIVATE_AGENT"
_SHARED: Final[str] = "SHARED_DOMAIN"


class RootScopeMembershipError(SubstrateConfigurationError):
    """Base refusal for root-qualified membership operations."""


class RootScopeMembershipAbsent(RootScopeMembershipError):
    """Raised when a complete requested scope has no active membership."""


class RootScopeMembershipRetired(RootScopeMembershipError):
    """Raised when the matching durable membership has been retired."""


class RootScopeMembershipConflict(RootScopeMembershipError):
    """Raised for duplicate or contradictory immutable membership facts."""


class _MembershipAlreadyRecorded(Exception):
    """Private transaction preflight signal; the durable record is re-read."""


@dataclass(frozen=True)
class RootScopeMembershipWitness:
    """Immutable reference to evidence supplied by an external admission step.

    This carrier intentionally verifies shape only.  It never mints, verifies,
    or replaces an external authority; production acceptance of that authority
    remains the Phase-0 pre-activation gate.
    """

    witness_id: str
    witness_digest: str

    def __post_init__(self) -> None:
        _text(self.witness_id, "witness_id")
        if (
            not isinstance(self.witness_digest, str)
            or len(self.witness_digest) != 64
            or any(character not in "0123456789abcdef" for character in self.witness_digest)
        ):
            raise RootScopeMembershipError("witness_digest must be a lowercase SHA-256 hex digest")

    def payload(self) -> dict[str, str]:
        return {"witness_id": self.witness_id, "witness_digest": self.witness_digest}


@dataclass(frozen=True)
class RootProfileGenerationRef:
    """Reference to an existing root-profile control-object revision.

    The control object, not this value object, owns the root/profile fact.  The
    reference is the canonical identity used by membership endpoints and
    process-local resolution caches.
    """

    core_id: UUID
    profile_generation: int
    profile_object_id: UUID
    profile_revision_id: UUID
    profile_revision_ordinal: int
    profile_semantic_scope_id: UUID

    def __post_init__(self) -> None:
        for value, label in (
            (self.core_id, "core_id"),
            (self.profile_object_id, "profile_object_id"),
            (self.profile_revision_id, "profile_revision_id"),
            (self.profile_semantic_scope_id, "profile_semantic_scope_id"),
        ):
            _native_uuid(value, label)
        if not isinstance(self.profile_generation, int) or isinstance(self.profile_generation, bool) or self.profile_generation < 1:
            raise RootScopeMembershipError("profile_generation must be a positive integer")
        if not isinstance(self.profile_revision_ordinal, int) or isinstance(self.profile_revision_ordinal, bool) or self.profile_revision_ordinal < 1:
            raise RootScopeMembershipError("profile_revision_ordinal must be a positive integer")

    def payload(self) -> dict[str, object]:
        return {
            "core_id": str(self.core_id),
            "profile_generation": self.profile_generation,
        }


@dataclass(frozen=True)
class RootQualifiedRuntimeKey:
    """Canonical process-cache identity for one profile generation and scope."""

    profile: RootProfileGenerationRef
    scope_key: RootScopeKey

    def __post_init__(self) -> None:
        if not isinstance(self.profile, RootProfileGenerationRef):
            raise RootScopeMembershipError("runtime key requires RootProfileGenerationRef")
        if not isinstance(self.scope_key, RootScopeKey):
            raise RootScopeMembershipError("runtime key requires RootScopeKey")

    @property
    def cache_key(self) -> tuple[str, int, str, int, str, str, str]:
        return (
            str(self.profile.core_id),
            self.profile.profile_generation,
            str(self.profile.profile_revision_id),
            self.profile.profile_revision_ordinal,
            self.scope_key.workspace_id,
            self.scope_key.scope_kind.value,
            self.scope_key.qualifier,
        )


@dataclass(frozen=True)
class RootQualifiedLegacyEidKey:
    """A legacy EID qualified by active root/profile, scope, namespace, revision."""

    runtime_key: RootQualifiedRuntimeKey
    legacy_source_namespace_id: UUID
    numeric_eid: int
    object_revision_id: UUID | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.runtime_key, RootQualifiedRuntimeKey):
            raise RootScopeMembershipError("EID key requires a root-qualified runtime key")
        _native_uuid(self.legacy_source_namespace_id, "legacy_source_namespace_id")
        if not isinstance(self.numeric_eid, int) or isinstance(self.numeric_eid, bool) or self.numeric_eid < 0:
            raise RootScopeMembershipError("numeric_eid must be a non-negative integer")
        if self.object_revision_id is not None:
            _native_uuid(self.object_revision_id, "object_revision_id")


@dataclass(frozen=True)
class RootScopeMembershipRecord:
    """Durably recovered membership relationship state; no scope bundle is copied."""

    runtime_key: RootQualifiedRuntimeKey
    relationship_id: UUID
    relationship_revision_id: UUID
    relationship_revision_ordinal: int
    membership_identity_namespace_id: UUID
    semantic_scope_id: UUID
    lifecycle_state: str
    witness: RootScopeMembershipWitness

    @property
    def active(self) -> bool:
        return self.lifecycle_state == _ACTIVE


@dataclass(frozen=True)
class RootQualifiedMemberScope:
    """Resolved runtime binding for one durably active membership.

    This is the surviving generalized runtime abstraction.  It uniquely owns
    only the binding of a recovered membership record to an existing native
    scope resource.  It does not duplicate namespace ownership or create state.
    """

    record: RootScopeMembershipRecord
    runtime_scope: NativeMemoryRuntimeScope

    def __post_init__(self) -> None:
        if not self.record.active:
            raise RootScopeMembershipError("resolved member scope must be active")
        if self.record.semantic_scope_id != self.runtime_scope.semantic_scope_id:
            raise RootScopeMembershipError("membership and runtime scope semantic identities differ")

    @property
    def runtime_key(self) -> RootQualifiedRuntimeKey:
        return self.record.runtime_key

    def legacy_eid_key(
        self,
        numeric_eid: int,
        *,
        object_revision_id: UUID | None = None,
    ) -> RootQualifiedLegacyEidKey:
        return RootQualifiedLegacyEidKey(
            runtime_key=self.runtime_key,
            legacy_source_namespace_id=self.runtime_scope.legacy_source_namespace_id,
            numeric_eid=numeric_eid,
            object_revision_id=object_revision_id,
        )


class RootScopeMembershipService:
    """Durable membership lifecycle over existing relationship revisions."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection)
        self._connection = connection
        self._relationships = NativeRelationshipService(connection)
        self._objects = NativeObjectService(connection)

    def admit(
        self,
        *,
        profile: RootProfileGenerationRef,
        runtime_scope: NativeMemoryRuntimeScope,
        witness: RootScopeMembershipWitness,
        membership_identity_namespace_id: UUID,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
    ) -> RootScopeMembershipRecord:
        """Persist one witnessed member only after all structural checks pass."""

        self._validate_profile(profile)
        scope_key = _scope_key(runtime_scope)
        _native_uuid(membership_identity_namespace_id, "membership_identity_namespace_id")
        _native_uuid(idempotency_namespace_id, "idempotency_namespace_id")
        _text(idempotency_key, "idempotency_key")
        if not isinstance(witness, RootScopeMembershipWitness):
            raise RootScopeMembershipError("membership requires an explicit witness")
        existing = self._records_for_profile(profile, scope_key)
        if existing:
            return self._matching_admission(
                existing,
                runtime_scope=runtime_scope,
                witness=witness,
                membership_identity_namespace_id=membership_identity_namespace_id,
            )

        state = self._relationship_state(
            profile=profile,
            runtime_scope=runtime_scope,
            witness=witness,
            membership_identity_namespace_id=membership_identity_namespace_id,
            lifecycle_state=_ACTIVE,
        )
        try:
            result = self._relationships.create_relationship(
                idempotency_namespace_id=idempotency_namespace_id,
                idempotency_key=idempotency_key,
                state=state,
                preflight=lambda _tx: self._require_admission_absent(profile, scope_key),
            )
        except _MembershipAlreadyRecorded:
            return self._matching_admission(
                self._records_for_profile(profile, scope_key),
                runtime_scope=runtime_scope,
                witness=witness,
                membership_identity_namespace_id=membership_identity_namespace_id,
            )
        record = self._record_by_id(profile, result.relationship_id)
        if record is None or not record.active:
            raise RootScopeMembershipError("committed membership was not durably published as active")
        return record

    def retire(
        self,
        *,
        profile: RootProfileGenerationRef,
        relationship_id: UUID,
        expected_relationship_revision_id: UUID,
        idempotency_namespace_id: UUID,
        idempotency_key: str,
    ) -> RootScopeMembershipRecord:
        """Durably retire one active membership before any runtime can resolve it."""

        self._validate_profile(profile)
        _native_uuid(relationship_id, "relationship_id")
        _native_uuid(expected_relationship_revision_id, "expected_relationship_revision_id")
        _native_uuid(idempotency_namespace_id, "idempotency_namespace_id")
        record = self._record_by_id(profile, relationship_id)
        if record is None:
            raise RootScopeMembershipAbsent("membership does not belong to this root profile generation")
        if not record.active:
            raise RootScopeMembershipRetired("membership is already retired")
        if record.relationship_revision_id != expected_relationship_revision_id:
            raise SubstrateRevisionConflict("expected membership revision is not current")
        state = self._relationship_state(
            profile=profile,
            runtime_scope=_scope_placeholder(record.runtime_key.scope_key, record.semantic_scope_id),
            witness=record.witness,
            membership_identity_namespace_id=record.membership_identity_namespace_id,
            lifecycle_state=_RETIRED,
        )
        result = self._relationships.transition_relationship(
            idempotency_namespace_id=idempotency_namespace_id,
            idempotency_key=idempotency_key,
            relationship_id=relationship_id,
            expected_revision_id=expected_relationship_revision_id,
            state=state,
        )
        retired = self._record_by_id(profile, result.relationship_id)
        if retired is None or retired.lifecycle_state != _RETIRED:
            raise RootScopeMembershipError("retired membership was not durably published")
        return retired

    def recover(self, profile: RootProfileGenerationRef) -> tuple[RootScopeMembershipRecord, ...]:
        """Recover all durable memberships for one exact root-profile revision."""

        self._validate_profile(profile)
        rows = self._connection.execute(
            "SELECT r.relationship_id,r.identity_namespace_id,rr.relationship_revision_id,"
            "rr.revision_ordinal,rr.effective_semantic_scope_id,rr.lifecycle_state,"
            "rr.lifecycle_authoritative,rr.payload_format,rr.payload_text "
            "FROM relationships r "
            "JOIN relationship_revisions rr ON rr.relationship_revision_id=r.current_revision_id "
            "JOIN relationship_revision_endpoints e ON e.relationship_revision_id=rr.relationship_revision_id "
            "WHERE r.relationship_kind=? AND e.endpoint_ordinal=0 "
            "AND e.endpoint_role=? AND e.binding_mode='EXACT_REVISION' "
            "AND e.endpoint_semantic_scope_id=? AND e.object_id=? "
            "AND e.bound_object_revision_id=? AND e.bound_object_revision_ordinal=?",
            (
                ROOT_SCOPE_MEMBERSHIP_KIND,
                _ROOT_PROFILE_ENDPOINT_ROLE,
                native_id_to_bytes(profile.profile_semantic_scope_id),
                native_id_to_bytes(profile.profile_object_id),
                native_id_to_bytes(profile.profile_revision_id),
                profile.profile_revision_ordinal,
            ),
        ).fetchall()
        records = tuple(self._record_from_row(profile, row) for row in rows)
        keys = [record.runtime_key for record in records]
        if len(keys) != len(set(keys)):
            raise RootScopeMembershipConflict("durable membership recovery found duplicate root-qualified scopes")
        return tuple(sorted(records, key=lambda record: record.runtime_key.cache_key))

    def _record_by_id(
        self,
        profile: RootProfileGenerationRef,
        relationship_id: UUID,
    ) -> RootScopeMembershipRecord | None:
        matches = [
            record
            for record in self.recover(profile)
            if record.relationship_id == relationship_id
        ]
        if len(matches) > 1:
            raise RootScopeMembershipConflict("relationship id recovered more than once")
        return matches[0] if matches else None

    def _records_for_profile(
        self,
        profile: RootProfileGenerationRef,
        scope_key: RootScopeKey,
    ) -> tuple[RootScopeMembershipRecord, ...]:
        return tuple(
            record for record in self.recover(profile) if record.runtime_key.scope_key == scope_key
        )

    def _require_admission_absent(
        self,
        profile: RootProfileGenerationRef,
        scope_key: RootScopeKey,
    ) -> None:
        if self._records_for_profile(profile, scope_key):
            raise _MembershipAlreadyRecorded

    @staticmethod
    def _matching_admission(
        records: tuple[RootScopeMembershipRecord, ...],
        *,
        runtime_scope: NativeMemoryRuntimeScope,
        witness: RootScopeMembershipWitness,
        membership_identity_namespace_id: UUID,
    ) -> RootScopeMembershipRecord:
        if len(records) != 1:
            raise RootScopeMembershipConflict("duplicate durable memberships share one root-qualified scope")
        record = records[0]
        if not record.active:
            raise RootScopeMembershipRetired("retired membership cannot be silently reactivated")
        if (
            record.semantic_scope_id != runtime_scope.semantic_scope_id
            or record.witness != witness
            or record.membership_identity_namespace_id != membership_identity_namespace_id
        ):
            raise RootScopeMembershipConflict("membership immutable facts conflict with the admitted relationship")
        return record

    def _validate_profile(self, profile: RootProfileGenerationRef) -> None:
        if not isinstance(profile, RootProfileGenerationRef):
            raise RootScopeMembershipError("membership requires RootProfileGenerationRef")
        current = self._objects.get_current_object(profile.profile_object_id)
        if (
            current.revision_id != profile.profile_revision_id
            or current.ordinal != profile.profile_revision_ordinal
            or current.scope_id != profile.profile_semantic_scope_id
        ):
            raise RootScopeMembershipError("root profile generation is absent, stale, or scope-mismatched")

    def _relationship_state(
        self,
        *,
        profile: RootProfileGenerationRef,
        runtime_scope: NativeMemoryRuntimeScope,
        witness: RootScopeMembershipWitness,
        membership_identity_namespace_id: UUID,
        lifecycle_state: str,
    ) -> RelationshipState:
        scope_key = _scope_key(runtime_scope)
        if lifecycle_state not in {_ACTIVE, _RETIRED}:
            raise RootScopeMembershipError("unsupported membership lifecycle state")
        return RelationshipState(
            identity_namespace_id=membership_identity_namespace_id,
            semantic_scope_id=runtime_scope.semantic_scope_id,
            relationship_kind=ROOT_SCOPE_MEMBERSHIP_KIND,
            existence_state="EXISTS",
            lifecycle_state=lifecycle_state,
            lifecycle_authoritative=True,
            governance_state="QUALIFIED" if lifecycle_state == _ACTIVE else "RETIRED",
            authority_category="EVIDENCE",
            endpoints=(
                Endpoint(
                    0,
                    _ROOT_PROFILE_ENDPOINT_ROLE,
                    profile.profile_semantic_scope_id,
                    profile.profile_object_id,
                    "EXACT_REVISION",
                    profile.profile_revision_id,
                    profile.profile_revision_ordinal,
                ),
            ),
            payload={
                "contract": ROOT_SCOPE_MEMBERSHIP_CONTRACT,
                "profile": profile.payload(),
                "scope_key": scope_key.identity_payload(),
                "external_witness": witness.payload(),
            },
            payload_format="JSON",
        )

    def _record_from_row(
        self,
        profile: RootProfileGenerationRef,
        row: tuple[object, ...],
    ) -> RootScopeMembershipRecord:
        (
            relationship_id,
            membership_identity_namespace_id,
            relationship_revision_id,
            ordinal,
            semantic_scope_id,
            lifecycle_state,
            lifecycle_authoritative,
            payload_format,
            payload_text,
        ) = row
        if lifecycle_authoritative != 1 or payload_format != "JSON" or not isinstance(payload_text, str):
            raise RootScopeMembershipError("membership relationship state is not authoritative JSON evidence")
        try:
            payload = json.loads(payload_text)
        except (TypeError, json.JSONDecodeError) as exc:
            raise RootScopeMembershipError("membership relationship payload is malformed") from exc
        if not isinstance(payload, dict) or payload.get("contract") != ROOT_SCOPE_MEMBERSHIP_CONTRACT:
            raise RootScopeMembershipError("relationship is not a root-scope membership contract")
        if payload.get("profile") != profile.payload():
            raise RootScopeMembershipConflict("membership profile facts conflict with its root endpoint")
        scope_key = _scope_key_from_payload(payload.get("scope_key"))
        witness = _witness_from_payload(payload.get("external_witness"))
        if lifecycle_state not in {_ACTIVE, _RETIRED}:
            raise RootScopeMembershipError("membership lifecycle is not active or retired")
        return RootScopeMembershipRecord(
            runtime_key=RootQualifiedRuntimeKey(profile, scope_key),
            relationship_id=_uuid_from_blob(relationship_id, "relationship_id"),
            relationship_revision_id=_uuid_from_blob(relationship_revision_id, "relationship_revision_id"),
            relationship_revision_ordinal=_positive_ordinal(ordinal),
            membership_identity_namespace_id=_uuid_from_blob(
                membership_identity_namespace_id, "membership_identity_namespace_id"
            ),
            semantic_scope_id=_uuid_from_blob(semantic_scope_id, "semantic_scope_id"),
            lifecycle_state=lifecycle_state,
            witness=witness,
        )


class RootScopeMembershipRuntime:
    """Restart-safe resolver over durable membership and supplied native scopes.

    The cache uses ``RootQualifiedRuntimeKey`` exclusively and is refreshed
    from durable relationship state on every resolution.  This conservative
    discipline prevents cold-cache disappearance and stale active visibility
    after retirement without introducing a second durable registry.
    """

    def __init__(
        self,
        *,
        connection: sqlite3.Connection,
        profile: RootProfileGenerationRef,
        runtime_scopes: tuple[NativeMemoryRuntimeScope, ...],
    ) -> None:
        open_schema(connection, writable=False)
        self._service = RootScopeMembershipService(connection)
        self._profile = profile
        self._bindings = _binding_map(runtime_scopes)
        self._active: dict[RootQualifiedRuntimeKey, RootQualifiedMemberScope] = {}
        self._retired: set[RootQualifiedRuntimeKey] = set()
        self.recover()

    def recover(self) -> None:
        """Rebuild publication only from committed relationship revisions."""

        active: dict[RootQualifiedRuntimeKey, RootQualifiedMemberScope] = {}
        retired: set[RootQualifiedRuntimeKey] = set()
        for record in self._service.recover(self._profile):
            binding = self._bindings.get(record.runtime_key.scope_key)
            if binding is None:
                raise RootScopeMembershipError("durable membership has no supplied native runtime scope")
            if binding.semantic_scope_id != record.semantic_scope_id:
                raise RootScopeMembershipConflict("durable membership semantic scope conflicts with supplied runtime scope")
            if record.active:
                active[record.runtime_key] = RootQualifiedMemberScope(record, binding)
            else:
                retired.add(record.runtime_key)
        self._active = active
        self._retired = retired

    def resolve(self, scope_key: RootScopeKey) -> RootQualifiedMemberScope:
        if not isinstance(scope_key, RootScopeKey):
            raise RootScopeMembershipError("resolution requires a complete RootScopeKey")
        self.recover()
        key = RootQualifiedRuntimeKey(self._profile, scope_key)
        member = self._active.get(key)
        if member is not None:
            return member
        if key in self._retired:
            raise RootScopeMembershipRetired("requested root scope membership is retired")
        raise RootScopeMembershipAbsent("requested root scope is not admitted")

    def resolve_private(self, workspace_id: str, agent_id: str) -> RootQualifiedMemberScope:
        return self.resolve(RootScopeKey(workspace_id, RootScopeKind.PRIVATE, agent_id=agent_id))

    def resolve_shared(self, workspace_id: str, domain_id: str) -> RootQualifiedMemberScope:
        return self.resolve(RootScopeKey(workspace_id, RootScopeKind.SHARED, domain_id=domain_id))

    def list_workspace_members(self, workspace_id: str) -> tuple[RootQualifiedMemberScope, ...]:
        _text(workspace_id, "workspace_id")
        self.recover()
        return tuple(
            member
            for key, member in sorted(self._active.items(), key=lambda item: item[0].cache_key)
            if key.scope_key.workspace_id == workspace_id
        )

    @property
    def cache_keys(self) -> tuple[RootQualifiedRuntimeKey, ...]:
        self.recover()
        return tuple(sorted(self._active, key=lambda key: key.cache_key))


def _scope_key(runtime_scope: NativeMemoryRuntimeScope) -> RootScopeKey:
    if not isinstance(runtime_scope, NativeMemoryRuntimeScope):
        raise RootScopeMembershipError("membership requires NativeMemoryRuntimeScope")
    for value, label in (
        (runtime_scope.legacy_source_namespace_id, "legacy_source_namespace_id"),
        (runtime_scope.identity_namespace_id, "identity_namespace_id"),
        (runtime_scope.semantic_scope_id, "semantic_scope_id"),
    ):
        _native_uuid(value, label)
    if runtime_scope.scope_kind == _PRIVATE:
        return RootScopeKey(runtime_scope.workspace_id, RootScopeKind.PRIVATE, agent_id=runtime_scope.agent_id)
    if runtime_scope.scope_kind == _SHARED:
        return RootScopeKey(runtime_scope.workspace_id, RootScopeKind.SHARED, domain_id=runtime_scope.domain_id)
    raise RootScopeMembershipError("runtime scope kind is not private or shared")


def _scope_placeholder(scope_key: RootScopeKey, semantic_scope_id: UUID) -> NativeMemoryRuntimeScope:
    """Use only retained membership facts during lifecycle transition.

    Namespace fields are deliberately placeholders here: relationship retirement
    must not copy or take ownership of the separately owned namespace bundle.
    They are never persisted by the membership relationship.
    """

    placeholder = UUID("00000000-0000-4000-8000-000000000000")
    return NativeMemoryRuntimeScope(
        workspace_id=scope_key.workspace_id,
        scope_kind=_PRIVATE if scope_key.scope_kind is RootScopeKind.PRIVATE else _SHARED,
        legacy_source_namespace_id=placeholder,
        identity_namespace_id=placeholder,
        semantic_scope_id=semantic_scope_id,
        agent_id=scope_key.agent_id,
        domain_id=scope_key.domain_id,
    )


def _binding_map(
    runtime_scopes: tuple[NativeMemoryRuntimeScope, ...],
) -> dict[RootScopeKey, NativeMemoryRuntimeScope]:
    if not isinstance(runtime_scopes, tuple) or not runtime_scopes:
        raise RootScopeMembershipError("runtime resolution requires explicit typed scope bindings")
    result: dict[RootScopeKey, NativeMemoryRuntimeScope] = {}
    source_namespaces: set[UUID] = set()
    semantic_scopes: set[UUID] = set()
    for runtime_scope in runtime_scopes:
        scope_key = _scope_key(runtime_scope)
        if scope_key in result:
            raise RootScopeMembershipConflict("runtime scope bindings collide under root-qualified identity")
        if runtime_scope.legacy_source_namespace_id in source_namespaces:
            raise RootScopeMembershipConflict("runtime scope bindings share a legacy source namespace")
        if runtime_scope.semantic_scope_id in semantic_scopes:
            raise RootScopeMembershipConflict("runtime scope bindings share a semantic scope")
        result[scope_key] = runtime_scope
        source_namespaces.add(runtime_scope.legacy_source_namespace_id)
        semantic_scopes.add(runtime_scope.semantic_scope_id)
    return result


def _scope_key_from_payload(value: object) -> RootScopeKey:
    if not isinstance(value, dict):
        raise RootScopeMembershipError("membership scope key evidence is malformed")
    try:
        kind = RootScopeKind(value.get("scope_kind"))
        return RootScopeKey(
            value.get("workspace_id"),
            kind,
            agent_id=value.get("agent_id"),
            domain_id=value.get("domain_id"),
        )
    except (TypeError, ValueError, RootScopeMembershipError) as exc:
        raise RootScopeMembershipError("membership scope key evidence is invalid") from exc


def _witness_from_payload(value: object) -> RootScopeMembershipWitness:
    if not isinstance(value, dict):
        raise RootScopeMembershipError("membership witness evidence is malformed")
    return RootScopeMembershipWitness(value.get("witness_id"), value.get("witness_digest"))


def _native_uuid(value: object, label: str) -> UUID:
    try:
        native_id_to_bytes(value)  # type: ignore[arg-type]
    except Exception as exc:
        raise RootScopeMembershipError(f"{label} must be a native UUID") from exc
    return value  # type: ignore[return-value]


def _uuid_from_blob(value: object, label: str) -> UUID:
    if not isinstance(value, bytes) or len(value) != 16:
        raise RootScopeMembershipError(f"{label} must be a 16-byte native id")
    try:
        candidate = UUID(bytes=value)
        return _native_uuid(candidate, label)
    except ValueError as exc:
        raise RootScopeMembershipError(f"{label} is malformed") from exc


def _positive_ordinal(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RootScopeMembershipError("membership relationship revision ordinal is invalid")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RootScopeMembershipError(f"{label} must be non-empty text")
    return value


def synthetic_witness_digest(value: str) -> str:
    """Deterministic helper for isolated qualification fixtures only."""

    _text(value, "synthetic witness value")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


__all__ = [
    "ROOT_SCOPE_MEMBERSHIP_CONTRACT",
    "ROOT_SCOPE_MEMBERSHIP_KIND",
    "RootProfileGenerationRef",
    "RootQualifiedLegacyEidKey",
    "RootQualifiedMemberScope",
    "RootQualifiedRuntimeKey",
    "RootScopeMembershipAbsent",
    "RootScopeMembershipConflict",
    "RootScopeMembershipError",
    "RootScopeMembershipRecord",
    "RootScopeMembershipRetired",
    "RootScopeMembershipRuntime",
    "RootScopeMembershipService",
    "RootScopeMembershipWitness",
    "synthetic_witness_digest",
]
