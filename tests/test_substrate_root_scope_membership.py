from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest

from torment_service.substrate.connection import (
    QualifiedTemporaryConnection,
    open_existing_native_core_connection,
    open_temporary_test_connection,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.root_scope_membership import (
    RootProfileGenerationRef,
    RootScopeMembershipAbsent,
    RootScopeMembershipConflict,
    RootScopeMembershipRetired,
    RootScopeMembershipRuntime,
    RootScopeMembershipService,
    RootScopeMembershipWitness,
    synthetic_witness_digest,
)
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope
from torment_service.substrate.schema import create_schema, open_schema


def _u() -> UUID:
    return generate_native_id()


@dataclass
class Fixture:
    qualified: QualifiedTemporaryConnection
    profile: RootProfileGenerationRef
    membership_namespace_id: UUID
    idempotency_namespace_id: UUID
    scopes: dict[RootScopeKey, NativeMemoryRuntimeScope]

    @property
    def connection(self):
        return self.qualified.connection

    def runtime(self) -> RootScopeMembershipRuntime:
        return RootScopeMembershipRuntime(
            connection=self.connection,
            profile=self.profile,
            runtime_scopes=tuple(self.scopes.values()),
        )

    def admit(self, key: RootScopeKey, *, witness_value: str = "witness"):
        return RootScopeMembershipService(self.connection).admit(
            profile=self.profile,
            runtime_scope=self.scopes[key],
            witness=RootScopeMembershipWitness(
                witness_id=f"fixture:{key.workspace_id}:{key.scope_kind.value}:{key.qualifier}",
                witness_digest=synthetic_witness_digest(witness_value),
            ),
            membership_identity_namespace_id=self.membership_namespace_id,
            idempotency_namespace_id=self.idempotency_namespace_id,
            idempotency_key=f"admit:{key.workspace_id}:{key.scope_kind.value}:{key.qualifier}:{witness_value}",
        )


def _fixture(tmp_path: Path, *scope_keys: RootScopeKey) -> Fixture:
    qualified = open_temporary_test_connection(tmp_path / "membership.db")
    connection = qualified.connection
    metadata = create_schema(connection)
    profile_identity_namespace_id = _u()
    membership_namespace_id = _u()
    idempotency_namespace_id = _u()
    profile_semantic_scope_id = _u()
    for namespace_id, namespace_key in (
        (profile_identity_namespace_id, "profile-identity"),
        (membership_namespace_id, "membership-identity"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(namespace_id), namespace_key),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(profile_semantic_scope_id), "root-profile"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace_id), "membership-ops"),
    )
    profile_object = NativeObjectService(connection).create_object(
        idempotency_namespace_id=idempotency_namespace_id,
        idempotency_key="root-profile-generation",
        state=ObjectState(
            profile_identity_namespace_id,
            profile_semantic_scope_id,
            "ROOT_NATIVE_PROFILE_GENERATION",
            "EXISTS",
            "ACTIVE",
            True,
            "QUALIFIED",
            authority_category="EVIDENCE",
            payload={"fixture": "synthetic-qualified-profile"},
            payload_format="JSON",
        ),
    )
    profile = RootProfileGenerationRef(
        core_id=UUID(bytes=metadata.core_id),
        profile_generation=1,
        profile_object_id=profile_object.object_id,
        profile_revision_id=profile_object.revision_id,
        profile_revision_ordinal=NativeObjectService(connection).get_current_object(profile_object.object_id).ordinal,
        profile_semantic_scope_id=profile_semantic_scope_id,
    )
    scopes: dict[RootScopeKey, NativeMemoryRuntimeScope] = {}
    for index, key in enumerate(scope_keys):
        identity_namespace_id, semantic_scope_id, source_namespace_id = _u(), _u(), _u()
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(identity_namespace_id), f"scope-identity-{index}"),
        )
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(semantic_scope_id), f"scope-{index}"),
        )
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(source_namespace_id), f"source-{index}"),
        )
        scopes[key] = NativeMemoryRuntimeScope(
            workspace_id=key.workspace_id,
            scope_kind="PRIVATE_AGENT" if key.scope_kind is RootScopeKind.PRIVATE else "SHARED_DOMAIN",
            legacy_source_namespace_id=source_namespace_id,
            identity_namespace_id=identity_namespace_id,
            semantic_scope_id=semantic_scope_id,
            agent_id=key.agent_id,
            domain_id=key.domain_id,
        )
    return Fixture(qualified, profile, membership_namespace_id, idempotency_namespace_id, scopes)


def test_private_collision_isolation_and_runtime_cache_scope_keys(tmp_path: Path) -> None:
    left = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    right = RootScopeKey("workspace-b", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, left, right)
    try:
        fixture.admit(left)
        fixture.admit(right)
        runtime = fixture.runtime()
        left_member = runtime.resolve_private("workspace-a", "agent-7")
        right_member = runtime.resolve_private("workspace-b", "agent-7")
        assert left_member.runtime_key != right_member.runtime_key
        assert left_member.runtime_scope.semantic_scope_id != right_member.runtime_scope.semantic_scope_id
        assert len(runtime.cache_keys) == 2
    finally:
        fixture.qualified.close()


def test_shared_domain_collision_isolation(tmp_path: Path) -> None:
    left = RootScopeKey("workspace-a", RootScopeKind.SHARED, domain_id="research")
    right = RootScopeKey("workspace-b", RootScopeKind.SHARED, domain_id="research")
    fixture = _fixture(tmp_path, left, right)
    try:
        fixture.admit(left)
        fixture.admit(right)
        runtime = fixture.runtime()
        assert runtime.resolve_shared("workspace-a", "research").runtime_key != runtime.resolve_shared(
            "workspace-b", "research"
        ).runtime_key
    finally:
        fixture.qualified.close()


def test_numeric_eid_isolation_uses_scope_and_source_namespace(tmp_path: Path) -> None:
    left = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    right = RootScopeKey("workspace-b", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, left, right)
    try:
        fixture.admit(left)
        fixture.admit(right)
        runtime = fixture.runtime()
        assert runtime.resolve(left).legacy_eid_key(42) != runtime.resolve(right).legacy_eid_key(42)
    finally:
        fixture.qualified.close()


def test_membership_admission_is_idempotent_and_contradiction_fails_closed(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        first = fixture.admit(key, witness_value="same")
        second = fixture.admit(key, witness_value="same")
        assert second.relationship_id == first.relationship_id
        with pytest.raises(RootScopeMembershipConflict):
            fixture.admit(key, witness_value="different")
    finally:
        fixture.qualified.close()


def test_admission_rechecks_membership_inside_the_write_transaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        service = RootScopeMembershipService(fixture.connection)
        original_create = service._relationships.create_relationship
        injected = False

        def create_after_interleaved_admission(*args, **kwargs):
            nonlocal injected
            if not injected:
                injected = True
                fixture.admit(key)
            return original_create(*args, **kwargs)

        monkeypatch.setattr(service._relationships, "create_relationship", create_after_interleaved_admission)
        recovered = service.admit(
            profile=fixture.profile,
            runtime_scope=fixture.scopes[key],
            witness=RootScopeMembershipWitness(
                witness_id="fixture:workspace-a:PRIVATE:agent-7",
                witness_digest=synthetic_witness_digest("witness"),
            ),
            membership_identity_namespace_id=fixture.membership_namespace_id,
            idempotency_namespace_id=fixture.idempotency_namespace_id,
            idempotency_key="admit:interleaved",
        )
        assert recovered.active
        assert injected
        assert fixture.connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 1
    finally:
        fixture.qualified.close()


def test_membership_pins_an_exact_noninitial_root_profile_revision(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        service = NativeObjectService(fixture.connection)
        current = service.get_current_object(fixture.profile.profile_object_id)
        profile_namespace_id = UUID(
            bytes=fixture.connection.execute(
                "SELECT identity_namespace_id FROM objects WHERE object_id=?",
                (native_id_to_bytes(fixture.profile.profile_object_id),),
            ).fetchone()[0]
        )
        successor = service.transition_object(
            idempotency_namespace_id=fixture.idempotency_namespace_id,
            idempotency_key="root-profile-generation-2",
            object_id=current.object_id,
            expected_revision_id=current.revision_id,
            state=ObjectState(
                profile_namespace_id,
                fixture.profile.profile_semantic_scope_id,
                "ROOT_NATIVE_PROFILE_GENERATION",
                "EXISTS",
                "ACTIVE",
                True,
                "QUALIFIED",
                authority_category="EVIDENCE",
                payload={"fixture": "synthetic-qualified-profile-generation-2"},
                payload_format="JSON",
            ),
        )
        fixture.profile = RootProfileGenerationRef(
            core_id=fixture.profile.core_id,
            profile_generation=2,
            profile_object_id=successor.object_id,
            profile_revision_id=successor.revision_id,
            profile_revision_ordinal=service.get_current_object(successor.object_id).ordinal,
            profile_semantic_scope_id=fixture.profile.profile_semantic_scope_id,
        )
        fixture.admit(key)
        assert fixture.connection.execute(
            "SELECT bound_object_revision_ordinal FROM relationship_revision_endpoints"
        ).fetchone()[0] == 2
        assert fixture.runtime().resolve(key).runtime_key.profile.profile_generation == 2
    finally:
        fixture.qualified.close()


def test_absent_scope_refuses_without_materialization(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        object_count = fixture.connection.execute("SELECT count(*) FROM objects").fetchone()[0]
        relationship_count = fixture.connection.execute("SELECT count(*) FROM relationships").fetchone()[0]
        with pytest.raises(RootScopeMembershipAbsent):
            fixture.runtime().resolve_private("workspace-a", "agent-7")
        assert fixture.connection.execute("SELECT count(*) FROM objects").fetchone()[0] == object_count
        assert fixture.connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == relationship_count
    finally:
        fixture.qualified.close()


def test_retired_membership_is_not_runtime_visible_even_with_warm_cache(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        admitted = fixture.admit(key)
        runtime = fixture.runtime()
        assert runtime.resolve(key).record.relationship_id == admitted.relationship_id
        retired = RootScopeMembershipService(fixture.connection).retire(
            profile=fixture.profile,
            relationship_id=admitted.relationship_id,
            expected_relationship_revision_id=admitted.relationship_revision_id,
            idempotency_namespace_id=fixture.idempotency_namespace_id,
            idempotency_key="retire:agent-7",
        )
        assert retired.lifecycle_state == "RETIRED"
        with pytest.raises(RootScopeMembershipRetired):
            runtime.resolve(key)
    finally:
        fixture.qualified.close()


def test_restart_recovers_active_and_retired_memberships_without_identity_origination(tmp_path: Path) -> None:
    active = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    retired = RootScopeKey("workspace-b", RootScopeKind.SHARED, domain_id="research")
    fixture = _fixture(tmp_path, active, retired)
    fixture_closed = False
    try:
        fixture.admit(active)
        retired_record = fixture.admit(retired)
        RootScopeMembershipService(fixture.connection).retire(
            profile=fixture.profile,
            relationship_id=retired_record.relationship_id,
            expected_relationship_revision_id=retired_record.relationship_revision_id,
            idempotency_namespace_id=fixture.idempotency_namespace_id,
            idempotency_key="retire:research",
        )
        db_path = fixture.qualified.database_path
        profile, scopes = fixture.profile, fixture.scopes
        fixture.qualified.close()
        fixture_closed = True
        reopened = open_existing_native_core_connection(db_path)
        try:
            runtime = RootScopeMembershipRuntime(
                connection=reopened.connection,
                profile=profile,
                runtime_scopes=tuple(scopes.values()),
            )
            assert runtime.resolve(active).runtime_scope == scopes[active]
            with pytest.raises(RootScopeMembershipRetired):
                runtime.resolve(retired)
            assert reopened.connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 1
        finally:
            reopened.close()
    finally:
        if not fixture_closed:
            fixture.qualified.close()


def test_membership_is_not_visible_until_the_admission_operation_returns(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        runtime = fixture.runtime()
        with pytest.raises(RootScopeMembershipAbsent):
            runtime.resolve(key)
        admitted = fixture.admit(key)
        assert admitted.active
        assert runtime.resolve(key).record.relationship_revision_id == admitted.relationship_revision_id
    finally:
        fixture.qualified.close()


def test_runtime_rejects_durable_membership_without_supplied_scope_resources(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        fixture.admit(key)
        with pytest.raises(Exception, match="no supplied native runtime scope"):
            RootScopeMembershipRuntime(
                connection=fixture.connection,
                profile=fixture.profile,
                runtime_scopes=(
                    NativeMemoryRuntimeScope(
                        workspace_id="workspace-b",
                        scope_kind="PRIVATE_AGENT",
                        legacy_source_namespace_id=_u(),
                        identity_namespace_id=_u(),
                        semantic_scope_id=_u(),
                        agent_id="agent-7",
                    ),
                ),
            )
    finally:
        fixture.qualified.close()
