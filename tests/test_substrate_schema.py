"""Focused Phase 7B structural schema tests; no semantic repository is present."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.schema import (
    CORE_ROLE_STAGING,
    EXPECTED_INDEXES,
    EXPECTED_TABLES,
    EXPECTED_TRIGGERS,
    HELPER_OWNED_INVARIANTS,
    SCHEMA_ID,
    SCHEMA_MAJOR,
    SCHEMA_MINOR,
    create_schema,
    open_schema,
)
from torment_service.substrate.errors import SubstrateSchemaCompatibilityError


def _id() -> bytes:
    return native_id_to_bytes(generate_native_id())


@pytest.fixture
def database(tmp_path: Path) -> sqlite3.Connection:
    qualified = open_temporary_test_connection(tmp_path / "phase-7b-schema.db")
    try:
        create_schema(qualified.connection)
        yield qualified.connection
    finally:
        qualified.close()


def _base(conn: sqlite3.Connection) -> tuple[bytes, bytes]:
    namespace, scope = _id(), _id()
    conn.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (namespace, "identity" + namespace.hex()))
    conn.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (scope, "scope" + scope.hex()))
    return namespace, scope


def _object(conn: sqlite3.Connection, namespace: bytes) -> bytes:
    object_id = _id()
    conn.execute("INSERT INTO objects(object_id,identity_namespace_id,object_kind,created_at_ns) VALUES (?,?,?,0)", (object_id, namespace, "TEST"))
    return object_id


def _object_revision(conn: sqlite3.Connection, object_id: bytes, scope: bytes, ordinal: int = 1, predecessor: tuple[bytes, int] | None = None, authority: str = "NOT_APPLICABLE") -> bytes:
    revision_id = _id()
    if predecessor is None:
        lineage, predecessor_id, predecessor_ordinal = "NATIVE_CREATION", None, None
    else:
        lineage, predecessor_id, predecessor_ordinal = "NATIVE_ORDINARY", predecessor[0], predecessor[1]
    conn.execute(
        "INSERT INTO object_revisions(object_revision_id,object_id,revision_ordinal,lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,governance_state,authority_category,payload_format,created_at_ns) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
        (revision_id, object_id, ordinal, lineage, predecessor_id, predecessor_ordinal, scope, "EXISTS", "LIVE", 1, "GOVERNED", authority, "NONE"),
    )
    return revision_id


def _relationship(conn: sqlite3.Connection, namespace: bytes) -> bytes:
    relationship_id = _id()
    conn.execute("INSERT INTO relationships(relationship_id,identity_namespace_id,relationship_kind,created_at_ns) VALUES (?,?,?,0)", (relationship_id, namespace, "TEST"))
    return relationship_id


def _relationship_revision(conn: sqlite3.Connection, relationship_id: bytes, scope: bytes, ordinal: int = 1, predecessor: tuple[bytes, int] | None = None) -> bytes:
    revision_id = _id()
    if predecessor is None:
        lineage, predecessor_id, predecessor_ordinal = "NATIVE_CREATION", None, None
    else:
        lineage, predecessor_id, predecessor_ordinal = "NATIVE_ORDINARY", predecessor[0], predecessor[1]
    conn.execute(
        "INSERT INTO relationship_revisions(relationship_revision_id,relationship_id,revision_ordinal,lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,governance_state,authority_category,payload_format,created_at_ns) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
        (revision_id, relationship_id, ordinal, lineage, predecessor_id, predecessor_ordinal, scope, "EXISTS", "LIVE", 1, "GOVERNED", "NOT_APPLICABLE", "NONE"),
    )
    return revision_id


def _operation(conn: sqlite3.Connection) -> bytes:
    namespace = _id()
    conn.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (namespace, "idem" + namespace.hex()))
    operation = _id()
    conn.execute("INSERT INTO operations VALUES (?,?,?,?,?,?,0)", (operation, namespace, "retry-key", "TEST", "TMS-INTENT-1", "{}"))
    return operation


def test_bootstrap_is_transactional_strict_and_idempotent(database: sqlite3.Connection) -> None:
    metadata = open_schema(database)
    second = create_schema(database)
    assert metadata == second
    assert metadata.core_id == database.execute("SELECT core_id FROM core_metadata").fetchone()[0]
    assert len(metadata.core_id) == 16
    assert metadata.core_role == CORE_ROLE_STAGING
    assert (metadata.schema_id, metadata.schema_major, metadata.schema_minor) == (SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR)
    assert {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table'") if not row[0].startswith("sqlite_")} == EXPECTED_TABLES
    assert EXPECTED_INDEXES.issubset({row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='index'")})
    assert EXPECTED_TRIGGERS.issubset({row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='trigger'")})
    assert all(row[5] == 1 for row in database.execute("PRAGMA table_list") if row[1] in EXPECTED_TABLES)
    assert database.execute("PRAGMA foreign_key_check").fetchall() == []
    assert database.execute("SELECT deployment_state FROM deployment_metadata").fetchone()[0] == "LEGACY_ACTIVE"


def test_namespace_scope_and_current_pointer_limit_are_explicit(database: sqlite3.Connection) -> None:
    namespace, scope = _base(database)
    assert namespace != scope
    object_id = _object(database, namespace)
    # H1 is deliberately helper-owned: raw SQLite can commit a carrier with NULL current pointer.
    assert database.execute("SELECT current_revision_id FROM objects WHERE object_id=?", (object_id,)).fetchone()[0] is None
    revision = _object_revision(database, object_id, scope)
    database.execute("UPDATE objects SET current_revision_id=?,current_revision_ordinal=1 WHERE object_id=?", (revision, object_id))


def test_same_carrier_object_and_relationship_constraints(database: sqlite3.Connection) -> None:
    namespace, scope = _base(database)
    left, right = _object(database, namespace), _object(database, namespace)
    left_revision, right_revision = _object_revision(database, left, scope), _object_revision(database, right, scope)
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("UPDATE objects SET current_revision_id=?,current_revision_ordinal=1 WHERE object_id=?", (right_revision, left))
    with pytest.raises(sqlite3.IntegrityError):
        _object_revision(database, left, scope, 2, (right_revision, 1))
    _object_revision(database, left, scope, 2, (left_revision, 1))
    with pytest.raises(sqlite3.IntegrityError):
        _object_revision(database, left, scope, 2, (left_revision, 1))
    relationship = _relationship(database, namespace)
    relationship_revision = _relationship_revision(database, relationship, scope)
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("UPDATE relationships SET current_revision_id=?,current_revision_ordinal=1 WHERE relationship_id=?", (right_revision, relationship))
    database.execute("UPDATE relationships SET current_revision_id=?,current_revision_ordinal=1 WHERE relationship_id=?", (relationship_revision, relationship))
    with pytest.raises(sqlite3.IntegrityError):
        _relationship_revision(database, relationship, scope, 2, (right_revision, 1))


def test_endpoint_exact_revision_requires_target_object_ownership(database: sqlite3.Connection) -> None:
    namespace, scope = _base(database)
    first, second = _object(database, namespace), _object(database, namespace)
    first_revision, second_revision = _object_revision(database, first, scope), _object_revision(database, second, scope)
    relationship = _relationship(database, namespace)
    relationship_revision = _relationship_revision(database, relationship, scope)
    database.execute("INSERT INTO relationship_revision_endpoints VALUES (?,?,?,?,?,?,?,?)", (relationship_revision, 0, "same-role", scope, first, "IDENTITY", None, None))
    database.execute("INSERT INTO relationship_revision_endpoints VALUES (?,?,?,?,?,?,?,?)", (relationship_revision, 1, "same-role", scope, second, "EXACT_REVISION", second_revision, 1))
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO relationship_revision_endpoints VALUES (?,?,?,?,?,?,?,?)", (relationship_revision, 2, "same-role", scope, first, "EXACT_REVISION", second_revision, 1))
    assert first_revision != second_revision


@pytest.mark.parametrize("authority", ["NOT_APPLICABLE", "UNKNOWN"])
def test_authority_categories_accept_explicit_non_authority_values(database: sqlite3.Connection, authority: str) -> None:
    namespace, scope = _base(database)
    _object_revision(database, _object(database, namespace), scope, authority=authority)
    with pytest.raises(sqlite3.IntegrityError):
        _object_revision(database, _object(database, namespace), scope, authority="MADE_UP")


def test_operation_idempotency_json_and_repeated_roles(database: sqlite3.Connection) -> None:
    operation = _operation(database)
    identity_namespace, _ = _base(database)
    object_id = _object(database, identity_namespace)
    namespace = database.execute("SELECT idempotency_namespace_id FROM operations WHERE operation_id=?", (operation,)).fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO operations VALUES (?,?,?,?,?,?,0)", (_id(), namespace, "retry-key", "TEST", "TMS-INTENT-1", "{}"))
    database.execute("INSERT INTO operations VALUES (?,?,?,?,?,?,0)", (_id(), namespace, "another-key", "TEST", "TMS-INTENT-1", "[]"))
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO operations VALUES (?,?,?,?,?,?,0)", (_id(), namespace, "bad-json", "TEST", "TMS-INTENT-1", "{"))
    database.execute("INSERT INTO operation_targets(operation_id,target_ordinal,target_role,target_kind,object_id) VALUES (?,?,?,?,?)", (operation, 0, "repeat", "OBJECT", object_id))
    database.execute("INSERT INTO operation_targets(operation_id,target_ordinal,target_role,target_kind,object_id) VALUES (?,?,?,?,?)", (operation, 1, "repeat", "OBJECT", object_id))
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO operation_targets(operation_id,target_ordinal,target_role,target_kind,object_id) VALUES (?,?,?,?,?)", (operation, 1, "repeat", "OBJECT", object_id))


def test_transition_effect_fks_and_h2_limit(database: sqlite3.Connection) -> None:
    operation = _operation(database)
    transition = _id()
    database.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)", (transition, operation, "TEST", "NATIVE"))
    # H2 is deliberate: the DDL permits an effectless transition until 7C's outer helper.
    assert database.execute("SELECT count(*) FROM object_revision_effects WHERE transition_id=?", (transition,)).fetchone()[0] == 0
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO object_revision_effects VALUES (?,?,?,?)", (transition, _id(), _id(), 1))


def test_h3_rejection_xor_transition_remains_helper_owned(database: sqlite3.Connection) -> None:
    operation = _operation(database)
    database.execute("INSERT INTO operation_rejections VALUES (?,?,?,0)", (operation, "REJECTED", None))
    # H3 is intentionally not encoded as cross-table trigger business logic in 7B.
    database.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)", (_id(), operation, "TEST", "NATIVE"))


def test_representation_source_payload_and_immutability(database: sqlite3.Connection) -> None:
    namespace, scope = _base(database)
    object_id = _object(database, namespace)
    revision = _object_revision(database, object_id, scope)
    representation = _id()
    database.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (representation, "OBJECT_REVISION", object_id, revision, 1, None, None, None, "vector", 1, "v1", "raw", None, None, None, 0))
    database.execute("INSERT INTO representation_payloads VALUES (?,?,?,0)", (representation, b"payload", 7))
    assert database.execute("SELECT representation_class FROM representations WHERE representation_id=?", (representation,)).fetchone()[0] == "vector"
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("UPDATE representations SET generation=2 WHERE representation_id=?", (representation,))
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO representations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (_id(), "OBJECT_REVISION", object_id, revision, 1, None, _id(), 1, "vector", 2, "v1", "raw", None, None, None, 0))


def test_integrity_and_reconciliation_structures(database: sqlite3.Connection) -> None:
    namespace, scope = _base(database)
    object_id, revision = _object(database, namespace), None
    revision = _object_revision(database, object_id, scope)
    expectation = _id()
    database.execute("INSERT INTO integrity_expectations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (expectation, "OBJECT_REVISION", object_id, revision, 1, None, None, None, None, "sha256", b"x", "raw", 0))
    database.execute("INSERT INTO integrity_measurements VALUES (?,?,?,?,?,0)", (_id(), expectation, "MATCH", b"x", None))
    database.execute("INSERT INTO integrity_measurements VALUES (?,?,?,?,?,0)", (_id(), expectation, "MISMATCH", b"y", None))
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("UPDATE integrity_expectations SET algorithm_id='other' WHERE expectation_id=?", (expectation,))
    case = _id()
    database.execute("INSERT INTO reconciliation_cases(reconciliation_case_id,condition_code,reason_text,subject_kind,opened_at_ns) VALUES (?,?,?,'CORE',0)", (case, "TEST", "test"))
    first = _id()
    database.execute("INSERT INTO reconciliation_case_states VALUES (?,?,?,?,?,?,?,?,?,0)", (first, case, 1, "NATIVE_CREATION", None, None, "WITHHELD", None, None))
    database.execute("UPDATE reconciliation_cases SET current_state_id=?,current_state_ordinal=1 WHERE reconciliation_case_id=?", (first, case))
    second = _id()
    database.execute("INSERT INTO reconciliation_case_states VALUES (?,?,?,?,?,?,?,?,?,0)", (second, case, 2, "NATIVE_ORDINARY", first, 1, "USABLE", None, None))
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO reconciliation_case_states VALUES (?,?,?,?,?,?,?,?,?,0)", (_id(), case, 2, "NATIVE_ORDINARY", first, 1, "USABLE", None, None))


def test_legacy_aliases_are_namespaced_and_delete_is_non_cascading(database: sqlite3.Connection) -> None:
    namespace, scope = _base(database)
    object_id = _object(database, namespace)
    _object_revision(database, object_id, scope)
    source_one, source_two = _id(), _id()
    database.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (source_one, "legacy-one"))
    database.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (source_two, "legacy-two"))
    database.execute("INSERT INTO legacy_object_aliases VALUES (?,?,?,?)", (source_one, "EID", "same", object_id))
    database.execute("INSERT INTO legacy_object_aliases VALUES (?,?,?,?)", (source_two, "EID", "same", object_id))
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("DELETE FROM objects WHERE object_id=?", (object_id,))


def test_schema_refuses_missing_trigger_and_version_mismatch(database: sqlite3.Connection) -> None:
    database.execute("DROP TRIGGER immutable_object_revision_update")
    with pytest.raises(SubstrateSchemaCompatibilityError):
        open_schema(database)


def test_schema_refuses_unsupported_metadata_version(database: sqlite3.Connection) -> None:
    database.execute("UPDATE core_metadata SET schema_minor=?", (SCHEMA_MINOR + 1,))
    with pytest.raises(SubstrateSchemaCompatibilityError):
        open_schema(database)


def test_helper_owned_registry_is_closed_for_v1() -> None:
    assert set(HELPER_OWNED_INVARIANTS) == {
        "H1_CURRENT_POINTER_COMPLETE", "H2_TRANSITION_EFFECT_COMPLETE", "H3_REJECTION_XOR_TRANSITION", "H4_REPRESENTATION_READY_COMPLETE", "H5_IMMUTABLE_AGGREGATE_CLOSED", "H6_RECONCILIATION_CURRENT_COMPLETE", "H7_LEGACY_ADMISSION_TYPED", "H8_ALLOCATED_OUTPUT_PUBLICATION_MATCH",
    }
