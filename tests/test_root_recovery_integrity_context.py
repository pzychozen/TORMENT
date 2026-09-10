"""R6 amplification and adversarial qualification on disposable cores only."""
from dataclasses import replace

import pytest

from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.root_blocker5_binding import root_membership_closure_digest
from torment_service.substrate.root_scope_membership import RootScopeMembershipService
from torment_service.substrate.root_scope_membership import RootScopeMembershipRuntime
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.schema import RootRecoveryIntegrityContext, open_schema
from torment_service.substrate.errors import SubstrateError
from test_substrate_root_scope_membership import _advance_profile, _fixture


def _key(workspace="workspace-a", agent="agent-7"):
    return RootScopeKey(workspace, RootScopeKind.PRIVATE, agent_id=agent)


def _closure(fixture, *, profile=None, scopes=None, keys=None):
    return root_membership_closure_digest(
        connection=fixture.connection,
        profile=profile or fixture.profile,
        runtime_scopes=tuple(fixture.scopes.values()) if scopes is None else scopes,
        declared_scope_keys=tuple(fixture.scopes) if keys is None else keys,
    )


def _retire(fixture, record, connection=None):
    return RootScopeMembershipService(connection or fixture.connection).retire(
        profile=fixture.profile,
        relationship_id=record.relationship_id,
        expected_relationship_revision_id=record.relationship_revision_id,
        idempotency_namespace_id=fixture.idempotency_namespace_id,
        idempotency_key="r6-retire",
    )


def _corrupt_foreign_key(connection):
    connection.execute("PRAGMA foreign_keys=OFF")
    connection.execute(
        "INSERT INTO objects(object_id,identity_namespace_id,object_kind,created_at_ns) VALUES (?,?,?,0)",
        (native_id_to_bytes(generate_native_id()), native_id_to_bytes(generate_native_id()), "R6_ORPHAN"),
    )
    connection.execute("PRAGMA foreign_keys=ON")
    assert connection.execute("PRAGMA foreign_key_check").fetchone() is not None


def _corrupt_check_constraint(connection):
    connection.execute("PRAGMA ignore_check_constraints=ON")
    connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (b"bad", "r6-invalid-id"))
    connection.execute("PRAGMA ignore_check_constraints=OFF")
    assert connection.execute("PRAGMA integrity_check").fetchone() != ("ok",)


@pytest.mark.parametrize("scope_count", (1, 3))
def test_one_root_closure_does_not_scan_database_per_membership(tmp_path, scope_count):
    from test_diagnostic_query_timing import collecting

    fixture = _fixture(tmp_path, *(_key(agent=f"agent-{i}") for i in range(scope_count)))
    try:
        for key in fixture.scopes:
            fixture.admit(key)
        statements = []
        fixture.connection.set_trace_callback(statements.append)
        with collecting() as timing:
            first = _closure(fixture)
        assert timing.stages["root.profile_verification"]["calls"] == scope_count + 2
        assert timing.stages["schema.validation"]["calls"] == 2 * (scope_count + 2) + 1
        assert timing.stages["schema.integrity_check"]["calls"] == 1
        assert timing.stages["schema.foreign_key_check"]["calls"] == 1
        assert len(first) == 64
        assert statements.count("PRAGMA integrity_check") == 1
        assert statements.count("PRAGMA foreign_key_check") == 1
        statements.clear()
        assert _closure(fixture) == first
        assert statements.count("PRAGMA integrity_check") == 1
        assert statements.count("PRAGMA foreign_key_check") == 1
    finally:
        fixture.qualified.close()


def test_member_results_and_logical_sql_are_identical_to_unscoped_resolution(tmp_path):
    fixture = _fixture(tmp_path, _key(), _key(workspace="workspace-b"))
    try:
        for key in fixture.scopes:
            fixture.admit(key)
        traces = []
        outputs = []
        for bounded in (False, True):
            statements = []
            fixture.connection.set_trace_callback(statements.append)

            def resolve(context=None):
                runtime = RootScopeMembershipRuntime(
                    connection=fixture.connection, profile=fixture.profile,
                    runtime_scopes=tuple(fixture.scopes.values()), _integrity_context=context,
                )
                return tuple(runtime.resolve(k.scope_key) for k in runtime.cache_keys)

            if bounded:
                with RootRecoveryIntegrityContext(fixture.connection) as context:
                    outputs.append(resolve(context))
            else:
                outputs.append(resolve())
            traces.append(statements)
        assert outputs[0] == outputs[1]
        assert len({member.runtime_key.scope_key.workspace_id for member in outputs[1]}) == 2
        physical = {"PRAGMA integrity_check", "PRAGMA foreign_key_check",
                    "PRAGMA main.data_version", "PRAGMA main.schema_version"}
        assert [sql for sql in traces[0] if sql not in physical] == [
            sql for sql in traces[1] if sql not in physical]
        assert traces[0].count("PRAGMA integrity_check") == 9
        assert traces[1].count("PRAGMA integrity_check") == 1
        profile_reads = "SELECT object_kind FROM objects WHERE object_id="
        assert sum(sql.startswith(profile_reads) for sql in traces[1]) == 4
    finally:
        fixture.qualified.close()


@pytest.mark.parametrize("change", ("retirement", "profile", "core"))
@pytest.mark.parametrize("external", (False, True))
def test_next_resolution_observes_committed_change_inside_context(tmp_path, change, external):
    key = _key()
    fixture = _fixture(tmp_path, key)
    other = None
    try:
        admitted = fixture.admit(key)
        if external:
            other = open_existing_native_core_connection(fixture.qualified.database_path)
        writer = other.connection if other else fixture.connection
        with RootRecoveryIntegrityContext(fixture.connection) as context:
            runtime = RootScopeMembershipRuntime(
                connection=fixture.connection, profile=fixture.profile,
                runtime_scopes=tuple(fixture.scopes.values()), _integrity_context=context,
            )
            assert runtime.resolve(key).record == admitted
            if change == "retirement":
                _retire(fixture, admitted, writer)
            elif change == "profile":
                writer_fixture = replace(fixture, qualified=other) if other else fixture
                _advance_profile(writer_fixture, generation=2)
            else:
                writer.execute("UPDATE core_metadata SET core_id=?", (native_id_to_bytes(generate_native_id()),))
            assert not writer.in_transaction
            with pytest.raises(SubstrateError):
                runtime.resolve(key)
        # Context expiry cannot carry an active result into a later recovery.
        with pytest.raises(SubstrateError):
            _closure(fixture)
    finally:
        if other:
            other.close()
        fixture.qualified.close()


@pytest.mark.parametrize("corrupt", (_corrupt_foreign_key, _corrupt_check_constraint))
@pytest.mark.parametrize("external", (False, True))
def test_integrity_is_rechecked_after_a_committed_change(tmp_path, corrupt, external):
    fixture = _fixture(tmp_path, _key())
    other = None
    try:
        fixture.admit(_key())
        if external:
            other = open_existing_native_core_connection(fixture.qualified.database_path)
        with RootRecoveryIntegrityContext(fixture.connection) as context:
            open_schema(fixture.connection, _integrity_context=context)
            corrupt(other.connection if other else fixture.connection)
            with pytest.raises(SubstrateError):
                open_schema(fixture.connection, _integrity_context=context)
            # A failed validation cannot make a later attempt reuse success.
            with pytest.raises(SubstrateError):
                open_schema(fixture.connection, _integrity_context=context)
        with pytest.raises(SubstrateError):
            _closure(fixture)
    finally:
        if other:
            other.close()
        fixture.qualified.close()


def test_context_connection_lifetime_and_schema_guards(tmp_path):
    fixture = _fixture(tmp_path, _key())
    other = open_existing_native_core_connection(fixture.qualified.database_path)
    try:
        context = RootRecoveryIntegrityContext(fixture.connection)
        with pytest.raises(SubstrateError, match="expired"):
            open_schema(fixture.connection, _integrity_context=context)
        with context:
            open_schema(fixture.connection, _integrity_context=context)
            with pytest.raises(SubstrateError, match="another connection"):
                open_schema(other.connection, _integrity_context=context)
            fixture.connection.execute("PRAGMA foreign_keys=OFF")
            with pytest.raises(SubstrateError, match="foreign keys must be enabled"):
                open_schema(fixture.connection, _integrity_context=context)
            fixture.connection.execute("PRAGMA foreign_keys=ON")
            fixture.connection.execute("UPDATE core_metadata SET schema_minor=999")
            with pytest.raises(SubstrateError, match="schema version"):
                open_schema(fixture.connection, _integrity_context=context)
        with pytest.raises(SubstrateError, match="expired"):
            open_schema(fixture.connection, _integrity_context=context)
        with pytest.raises(SubstrateError, match="cannot be reused"):
            with context:
                pass
    finally:
        other.close()
        fixture.qualified.close()


def test_commit_during_integrity_validation_does_not_publish_reusable_evidence(tmp_path, monkeypatch):
    import torment_service.substrate.schema as schema_module

    fixture = _fixture(tmp_path, _key())
    other = open_existing_native_core_connection(fixture.qualified.database_path)
    original = schema_module._require_foreign_key_integrity
    calls = 0

    def check(connection):
        nonlocal calls
        calls += 1
        original(connection)
        if calls == 1:
            other.connection.execute("UPDATE core_metadata SET created_at_ns=created_at_ns+1")

    monkeypatch.setattr(schema_module, "_require_foreign_key_integrity", check)
    try:
        with RootRecoveryIntegrityContext(fixture.connection) as context:
            open_schema(fixture.connection, _integrity_context=context)
            open_schema(fixture.connection, _integrity_context=context)
            open_schema(fixture.connection, _integrity_context=context)
        assert calls == 2
    finally:
        other.close()
        fixture.qualified.close()


@pytest.mark.parametrize("defect,match", (
    ("wrong_core", "root profile"),
    ("wrong_generation", "root profile"),
    ("missing", "CLOSURE_MISMATCH"),
    ("retired", "CLOSURE_MISMATCH"),
    ("invalid_binding", "semantic scope conflicts"),
    ("cross_workspace", "CLOSURE_MISMATCH"),
    ("schema", "schema version"),
    ("foreign_key", "foreign-key structural health"),
    ("integrity", "SQLite integrity check failed"),
))
def test_root_closure_refuses_durable_faults(tmp_path, defect, match):
    key = _key()
    fixture = _fixture(tmp_path, key)
    try:
        record = None if defect == "missing" else fixture.admit(key)
        kwargs = {}
        if defect == "wrong_core":
            kwargs["profile"] = replace(fixture.profile, core_id=generate_native_id())
        elif defect == "wrong_generation":
            kwargs["profile"] = replace(fixture.profile, profile_generation=2)
        elif defect == "retired":
            _retire(fixture, record)
        elif defect == "invalid_binding":
            kwargs["scopes"] = (replace(fixture.scopes[key], semantic_scope_id=generate_native_id()),)
        elif defect == "cross_workspace":
            kwargs["keys"] = (_key(workspace="workspace-b"),)
        elif defect == "schema":
            fixture.connection.execute("UPDATE core_metadata SET schema_minor=999")
        elif defect == "foreign_key":
            _corrupt_foreign_key(fixture.connection)
        elif defect == "integrity":
            _corrupt_check_constraint(fixture.connection)
        with pytest.raises(SubstrateError, match=match):
            _closure(fixture, **kwargs)
    finally:
        fixture.qualified.close()
