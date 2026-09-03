from __future__ import annotations

import ast
from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import threading
from uuid import UUID

import pytest

import torment_service.substrate.root_scope_membership as root_scope_membership_module

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
    RootScopeMembershipError,
    RootScopeMembershipRetired,
    RootScopeMembershipRuntime,
    RootScopeMembershipService,
    RootScopeMembershipWitness,
)
from torment_service.substrate.root_profile import (
    ROOT_NATIVE_PROFILE_GENERATION_KIND,
    RootProfileGenerationError,
    current_root_profile_generation,
    root_profile_generation_payload,
)
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope
from torment_service.substrate.schema import create_schema, open_schema


def _u() -> UUID:
    return generate_native_id()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _witness(key: RootScopeKey, value: str = "witness") -> RootScopeMembershipWitness:
    return RootScopeMembershipWitness(
        witness_id=f"fixture:{key.workspace_id}:{key.scope_kind.value}:{key.qualifier}",
        witness_digest=_digest(value),
        issuer_reference="qualification-fixture",
        provenance_kind="QUALIFICATION_TEST",
    )


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
            witness=_witness(key, witness_value),
            membership_identity_namespace_id=self.membership_namespace_id,
            idempotency_namespace_id=self.idempotency_namespace_id,
            idempotency_key=(
                f"admit:{self.profile.profile_generation}:{key.workspace_id}:"
                f"{key.scope_kind.value}:{key.qualifier}:{witness_value}"
            ),
        )


def _fixture(tmp_path: Path, *scope_keys: RootScopeKey) -> Fixture:
    qualified = open_temporary_test_connection(tmp_path / "membership.db")
    connection = qualified.connection
    create_schema(connection)
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
            ROOT_NATIVE_PROFILE_GENERATION_KIND,
            "EXISTS",
            "ACTIVE",
            True,
            "QUALIFIED",
            authority_category="EVIDENCE",
            payload=root_profile_generation_payload(1),
            payload_format="JSON",
        ),
    )
    profile = current_root_profile_generation(connection)
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


def _advance_profile(
    fixture: Fixture,
    *,
    generation: int,
    existence_state: str = "EXISTS",
    lifecycle_state: str = "ACTIVE",
    governance_state: str = "QUALIFIED",
) -> RootProfileGenerationRef:
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
        idempotency_key=f"root-profile-generation-{generation}-{lifecycle_state}",
        object_id=current.object_id,
        expected_revision_id=current.revision_id,
        state=ObjectState(
            profile_namespace_id,
            fixture.profile.profile_semantic_scope_id,
            ROOT_NATIVE_PROFILE_GENERATION_KIND,
            existence_state,
            lifecycle_state,
            True,
            governance_state,
            authority_category="EVIDENCE",
            payload=root_profile_generation_payload(generation),
            payload_format="JSON",
        ),
    )
    if (
        existence_state,
        lifecycle_state,
        governance_state,
    ) == ("EXISTS", "ACTIVE", "QUALIFIED"):
        return current_root_profile_generation(fixture.connection)
    return RootProfileGenerationRef(
        core_id=fixture.profile.core_id,
        profile_generation=generation,
        profile_object_id=successor.object_id,
        profile_revision_id=successor.revision_id,
        profile_revision_ordinal=service.get_current_object(successor.object_id).ordinal,
        profile_semantic_scope_id=fixture.profile.profile_semantic_scope_id,
    )


def test_private_collision_isolation_and_runtime_cache_scope_keys(tmp_path: Path) -> None:
    left = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    right = RootScopeKey("workspace-b", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, left, right)
    try:
        fixture.admit(left)
        fixture.admit(right)
        assert {
            record.runtime_key.scope_key
            for record in RootScopeMembershipService(fixture.connection).recover(fixture.profile)
        } == set(fixture.scopes)
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
            witness=_witness(key),
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
                ROOT_NATIVE_PROFILE_GENERATION_KIND,
                "EXISTS",
                "ACTIVE",
                True,
                "QUALIFIED",
                authority_category="EVIDENCE",
                payload=root_profile_generation_payload(2),
                payload_format="JSON",
            ),
        )
        fixture.profile = current_root_profile_generation(fixture.connection)
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


def test_two_connection_admission_fence_never_duplicates_membership(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    barrier = threading.Barrier(2)
    local = threading.local()
    original_records = RootScopeMembershipService._records_for_profile
    outcomes: list[UUID] = []
    failures: list[BaseException] = []
    result_lock = threading.Lock()

    def synchronized_initial_read(service, profile, scope_key):
        calls = getattr(local, "calls", 0)
        local.calls = calls + 1
        result = original_records(service, profile, scope_key)
        if calls == 0:
            barrier.wait(timeout=5)
        return result

    def worker(label: str) -> None:
        opened = open_existing_native_core_connection(fixture.qualified.database_path, busy_timeout_ms=5_000)
        try:
            record = RootScopeMembershipService(opened.connection).admit(
                profile=fixture.profile,
                runtime_scope=fixture.scopes[key],
                witness=_witness(key),
                membership_identity_namespace_id=fixture.membership_namespace_id,
                idempotency_namespace_id=fixture.idempotency_namespace_id,
                idempotency_key=f"two-connection:{label}",
            )
            with result_lock:
                outcomes.append(record.relationship_id)
        except BaseException as exc:  # Thread results are asserted in the parent.
            with result_lock:
                failures.append(exc)
        finally:
            opened.close()

    try:
        monkeypatch.setattr(RootScopeMembershipService, "_records_for_profile", synchronized_initial_read)
        threads = [threading.Thread(target=worker, args=(label,)) for label in ("left", "right")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            assert not thread.is_alive()
        assert failures == []
        assert len(outcomes) == 2
        assert outcomes[0] == outcomes[1]
        assert fixture.connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 1
    finally:
        fixture.qualified.close()


def test_retired_membership_requires_no_live_runtime_binding(tmp_path: Path) -> None:
    active = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    retired = RootScopeKey("workspace-b", RootScopeKind.SHARED, domain_id="research")
    fixture = _fixture(tmp_path, active, retired)
    try:
        fixture.admit(active)
        retired_record = fixture.admit(retired)
        RootScopeMembershipService(fixture.connection).retire(
            profile=fixture.profile,
            relationship_id=retired_record.relationship_id,
            expected_relationship_revision_id=retired_record.relationship_revision_id,
            idempotency_namespace_id=fixture.idempotency_namespace_id,
            idempotency_key="retire:withdraw-binding",
        )
        runtime = RootScopeMembershipRuntime(
            connection=fixture.connection,
            profile=fixture.profile,
            runtime_scopes=(fixture.scopes[active],),
        )
        assert runtime.resolve(active).runtime_scope == fixture.scopes[active]
        with pytest.raises(RootScopeMembershipRetired):
            runtime.resolve(retired)
    finally:
        fixture.qualified.close()


def test_retired_membership_readmission_requires_a_new_profile_generation(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        admitted = fixture.admit(key)
        RootScopeMembershipService(fixture.connection).retire(
            profile=fixture.profile,
            relationship_id=admitted.relationship_id,
            expected_relationship_revision_id=admitted.relationship_revision_id,
            idempotency_namespace_id=fixture.idempotency_namespace_id,
            idempotency_key="retire:terminal",
        )
        with pytest.raises(RootScopeMembershipRetired):
            fixture.admit(key)
        fixture.profile = _advance_profile(fixture, generation=2)
        replacement = fixture.admit(key)
        assert replacement.relationship_id != admitted.relationship_id
    finally:
        fixture.qualified.close()


def test_profile_revision_advance_refuses_old_memberships_and_does_not_carry_them(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        fixture.admit(key)
        old_profile = fixture.profile
        successor_profile = _advance_profile(fixture, generation=2)
        with pytest.raises(RootScopeMembershipError):
            RootScopeMembershipRuntime(
                connection=fixture.connection,
                profile=old_profile,
                runtime_scopes=(fixture.scopes[key],),
            )
        successor_runtime = RootScopeMembershipRuntime(
            connection=fixture.connection,
            profile=successor_profile,
            runtime_scopes=(fixture.scopes[key],),
        )
        with pytest.raises(RootScopeMembershipAbsent):
            successor_runtime.resolve(key)
    finally:
        fixture.qualified.close()


def test_profile_claim_rejects_wrong_core_generation_and_object_kind(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        service = RootScopeMembershipService(fixture.connection)
        for invalid in (
            replace(fixture.profile, core_id=_u()),
            replace(fixture.profile, profile_generation=fixture.profile.profile_generation + 1),
        ):
            with pytest.raises(RootScopeMembershipError):
                service.admit(
                    profile=invalid,
                    runtime_scope=fixture.scopes[key],
                    witness=_witness(key),
                    membership_identity_namespace_id=fixture.membership_namespace_id,
                    idempotency_namespace_id=fixture.idempotency_namespace_id,
                    idempotency_key=f"invalid-profile:{invalid.profile_generation}",
                )
        profile_namespace_id = UUID(
            bytes=fixture.connection.execute(
                "SELECT identity_namespace_id FROM objects WHERE object_id=?",
                (native_id_to_bytes(fixture.profile.profile_object_id),),
            ).fetchone()[0]
        )
        wrong_object = NativeObjectService(fixture.connection).create_object(
            idempotency_namespace_id=fixture.idempotency_namespace_id,
            idempotency_key="wrong-profile-kind",
            state=ObjectState(
                profile_namespace_id,
                fixture.profile.profile_semantic_scope_id,
                "NOT_A_ROOT_PROFILE",
                "EXISTS",
                "ACTIVE",
                True,
                "QUALIFIED",
                authority_category="EVIDENCE",
                payload={"fixture": "wrong-profile-kind"},
                payload_format="JSON",
            ),
        )
        wrong_kind = replace(
            fixture.profile,
            profile_object_id=wrong_object.object_id,
            profile_revision_id=wrong_object.revision_id,
            profile_revision_ordinal=1,
        )
        with pytest.raises(RootScopeMembershipError):
            service.admit(
                profile=wrong_kind,
                runtime_scope=fixture.scopes[key],
                witness=_witness(key),
                membership_identity_namespace_id=fixture.membership_namespace_id,
                idempotency_namespace_id=fixture.idempotency_namespace_id,
                idempotency_key="invalid-profile:wrong-kind",
            )
    finally:
        fixture.qualified.close()


def test_nonadmissible_root_profile_refuses_admission_and_resolution(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        retired_profile = _advance_profile(
            fixture,
            generation=2,
            lifecycle_state="RETIRED",
            governance_state="RETIRED",
        )
        with pytest.raises(RootScopeMembershipError):
            fixture.admit(key)
        with pytest.raises(RootScopeMembershipError):
            RootScopeMembershipRuntime(
                connection=fixture.connection,
                profile=retired_profile,
                runtime_scopes=(fixture.scopes[key],),
            )
    finally:
        fixture.qualified.close()


def test_scope_identity_remains_exact_for_case_and_unicode_variants(tmp_path: Path) -> None:
    left = RootScopeKey("Workspace-A", RootScopeKind.PRIVATE, agent_id="caf\u00e9")
    right = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="cafe\u0301")
    fixture = _fixture(tmp_path, left, right)
    try:
        fixture.admit(left)
        fixture.admit(right)
        assert {
            record.runtime_key.scope_key
            for record in RootScopeMembershipService(fixture.connection).recover(fixture.profile)
        } == set(fixture.scopes)
        runtime = fixture.runtime()
        assert left != right
        assert runtime.resolve(left).runtime_key != runtime.resolve(right).runtime_key
    finally:
        fixture.qualified.close()


def test_current_root_profile_discovery_rejects_multiple_active_profiles_and_recovers_after_restart(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    try:
        assert current_root_profile_generation(fixture.connection) == fixture.profile
        profile_namespace_id = UUID(
            bytes=fixture.connection.execute(
                "SELECT identity_namespace_id FROM objects WHERE object_id=?",
                (native_id_to_bytes(fixture.profile.profile_object_id),),
            ).fetchone()[0]
        )
        NativeObjectService(fixture.connection).create_object(
            idempotency_namespace_id=fixture.idempotency_namespace_id,
            idempotency_key="second-active-root-profile",
            state=ObjectState(
                profile_namespace_id,
                fixture.profile.profile_semantic_scope_id,
                ROOT_NATIVE_PROFILE_GENERATION_KIND,
                "EXISTS",
                "ACTIVE",
                True,
                "QUALIFIED",
                authority_category="EVIDENCE",
                payload=root_profile_generation_payload(2),
                payload_format="JSON",
            ),
        )
        with pytest.raises(RootProfileGenerationError):
            current_root_profile_generation(fixture.connection)
    finally:
        fixture.qualified.close()


def test_current_root_profile_discovery_recovers_after_restart(tmp_path: Path) -> None:
    key = RootScopeKey("workspace-a", RootScopeKind.PRIVATE, agent_id="agent-7")
    fixture = _fixture(tmp_path, key)
    profile = fixture.profile
    path = fixture.qualified.database_path
    fixture.qualified.close()
    reopened = open_existing_native_core_connection(path)
    try:
        assert current_root_profile_generation(reopened.connection) == profile
    finally:
        reopened.close()


def test_membership_import_boundary_has_no_legacy_scope_materialization_calls() -> None:
    source = Path(root_scope_membership_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not any("fabric" in imported.lower() or "memory_graph" in imported.lower() for imported in imports)
    assert {"get_workspace", "create_agent"}.isdisjoint(calls)
