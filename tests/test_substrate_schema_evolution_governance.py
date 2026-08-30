"""Phase 7G5A3C1S schema-evolution and closed-child qualification tests."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from torment_service.substrate.closed_child_qualification import (
    NativeClosedChildQualificationService,
    NativeProvenanceRecord,
)
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.errors import (
    SubstrateIdempotencyConflict,
    SubstrateSchemaCompatibilityError,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.object_revision_governance import (
    NativeMemoryGovernanceFacts,
    NativeObjectRevisionGovernanceService,
)
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.relationships import NativeRelationshipService
from torment_service.substrate import schema as schema_module
from torment_service.substrate.schema import (
    CORE_ROLE_STAGING,
    SCHEMA_MAJOR,
    SCHEMA_MINOR,
    SCHEMA_V1_MAJOR,
    SCHEMA_V1_MINOR,
    SCHEMA_V1_1_MAJOR,
    SCHEMA_V1_1_MINOR,
    SCHEMA_V1_TO_V1_1_GOVERNANCE_MIGRATION_KEY,
    SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER_MIGRATION_KEY,
    create_schema,
    create_schema_v1,
    create_schema_v1_1,
    open_schema,
    upgrade_schema_v1_to_v1_1,
    upgrade_schema_v1_1_to_v1_2,
)


def _id():
    return generate_native_id()


def _database(tmp_path: Path, *, v1: bool = False, v1_1: bool = False):
    qualified = open_temporary_test_connection(tmp_path / "schema-evolution-governance.db")
    try:
        if v1:
            create_schema_v1(qualified.connection)
        elif v1_1:
            create_schema_v1_1(qualified.connection)
        else:
            create_schema(qualified.connection)
        return qualified
    except Exception:
        qualified.close()
        raise


def _foundation(connection: sqlite3.Connection):
    identity, scope, idem = _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity), f"identity-{identity}"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), f"scope-{scope}"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idem), f"idem-{idem}"),
    )
    return identity, scope, idem


def _state(identity, scope, *, lifecycle_state: str = "UNSET"):
    return ObjectState(
        identity,
        scope,
        "LEGACY_CORE_NODE",
        "EXISTS",
        lifecycle_state,
        True,
        "UNKNOWN",
        "NOT_APPLICABLE",
        {"summary": "qualification memory"},
        "JSON",
    )


def _provenance(*, notes: str = "fixture"):
    return NativeProvenanceRecord(
        "RUNTIME_PROVENANCE_V1",
        "user_input",
        None,
        "DIRECT",
        "UNKNOWN",
        capture_time_ns=123,
        descriptive_notes=notes,
    )


def _insert_governance(connection, result, facts: NativeMemoryGovernanceFacts):
    ordinal = connection.execute(
        "SELECT revision_ordinal FROM object_revisions WHERE object_revision_id=?",
        (native_id_to_bytes(result.revision_id),),
    ).fetchone()[0]
    connection.execute(
        """
        INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            native_id_to_bytes(result.object_id),
            native_id_to_bytes(result.revision_id),
            ordinal,
            *facts.as_storage_tuple(),
        ),
    )


def _historical_v1_object(connection: sqlite3.Connection):
    """Insert pre-existing v1 history without invoking current semantic APIs."""
    identity, scope, object_id, revision_id = _id(), _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity), f"historical-identity-{identity}"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), f"historical-scope-{scope}"),
    )
    connection.execute(
        "INSERT INTO objects(object_id,identity_namespace_id,object_kind,created_at_ns) "
        "VALUES (?,?,?,0)",
        (native_id_to_bytes(object_id), native_id_to_bytes(identity), "LEGACY_CORE_NODE"),
    )
    connection.execute(
        """
        INSERT INTO object_revisions(
            object_revision_id,object_id,revision_ordinal,lineage_kind,
            predecessor_revision_id,predecessor_revision_ordinal,
            effective_semantic_scope_id,existence_state,lifecycle_state,
            lifecycle_authoritative,governance_state,authority_category,
            payload_format,created_at_ns
        ) VALUES (?,?,1,'NATIVE_CREATION',NULL,NULL,?,'EXISTS','UNSET',1,
                  'UNKNOWN','NOT_APPLICABLE','NONE',0)
        """,
        (native_id_to_bytes(revision_id), native_id_to_bytes(object_id), native_id_to_bytes(scope)),
    )
    connection.execute(
        "UPDATE objects SET current_revision_id=?,current_revision_ordinal=1 WHERE object_id=?",
        (native_id_to_bytes(revision_id), native_id_to_bytes(object_id)),
    )
    connection.commit()
    return object_id


def _semantic_counts(connection: sqlite3.Connection) -> tuple[int, ...]:
    return tuple(
        connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in ("objects", "relationships", "operations", "semantic_transitions")
    )


def test_current_bootstrap_is_v1_2_with_exact_governance_and_runtime_order_shape(tmp_path: Path):
    qualified = _database(tmp_path)
    try:
        connection = qualified.connection
        metadata = open_schema(connection)
        assert (metadata.schema_major, metadata.schema_minor) == (SCHEMA_MAJOR, SCHEMA_MINOR) == (1, 2)
        assert open_schema(connection, writable=False) == metadata
        assert connection.execute(
            "SELECT count(*) FROM object_revision_governance"
        ).fetchone()[0] == 0
        columns = connection.execute("PRAGMA table_info(object_revision_governance)").fetchall()
        assert [row[1] for row in columns] == [
            "object_id", "object_revision_id", "object_revision_ordinal", "protected",
            "non_shareable", "collective_export_blocked", "collective_reingest_blocked",
            "decay_accelerated",
        ]
        assert [row[2] for row in columns] == ["BLOB", "BLOB", "INTEGER"] + ["INTEGER"] * 5
        assert [
            (row[2], row[3], row[4])
            for row in sorted(
                connection.execute(
                    "PRAGMA foreign_key_list(object_revision_governance)"
                ).fetchall(),
                key=lambda row: (row[0], row[1]),
            )
        ] == [
            ("object_revisions", "object_id", "object_id"),
            ("object_revisions", "object_revision_id", "object_revision_id"),
            ("object_revisions", "object_revision_ordinal", "revision_ordinal"),
        ]
        assert [
            (row[2], row[3], row[4])
            for row in connection.execute(
                "PRAGMA index_list(object_revision_governance)"
            )
        ] == [(1, "pk", 0)]
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name='immutable_object_revision_governance_update'"
        ).fetchone() == (1,)
        assert connection.execute(
            "PRAGMA table_info(memory_runtime_enumeration_orders)"
        ).fetchall()[0][1:3] == ("legacy_source_namespace_id", "BLOB")
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='trigger' "
            "AND name='immutable_memory_runtime_enumeration_order_update'"
        ).fetchone() == (1,)
    finally:
        qualified.close()


def test_explicit_v1_upgrade_is_additive_idempotent_and_preserves_deployment(tmp_path: Path):
    qualified = _database(tmp_path, v1=True)
    try:
        connection = qualified.connection
        before = open_schema(connection, writable=False)
        assert (before.schema_major, before.schema_minor) == (SCHEMA_V1_MAJOR, SCHEMA_V1_MINOR)
        with pytest.raises(SubstrateSchemaCompatibilityError, match="explicit versioned schema upgrade"):
            create_schema(connection)
        with pytest.raises(SubstrateSchemaCompatibilityError):
            NativeObjectRevisionGovernanceService(connection)
        historical = _historical_v1_object(connection)
        deployment = connection.execute(
            "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
        ).fetchone()

        upgraded_v1_1 = upgrade_schema_v1_to_v1_1(connection)
        assert (upgraded_v1_1.schema_major, upgraded_v1_1.schema_minor) == (SCHEMA_V1_1_MAJOR, SCHEMA_V1_1_MINOR)
        assert upgraded_v1_1.core_id == before.core_id and upgraded_v1_1.core_role == CORE_ROLE_STAGING
        assert connection.execute(
            "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
        ).fetchone() == deployment == ("LEGACY_ACTIVE", None)
        ledger_v1_1 = connection.execute(
            "SELECT migration_key,from_major,from_minor,to_major,to_minor FROM schema_migration_ledger"
        ).fetchall()
        assert ledger_v1_1 == [
            (
                SCHEMA_V1_TO_V1_1_GOVERNANCE_MIGRATION_KEY,
                SCHEMA_V1_MAJOR,
                SCHEMA_V1_MINOR,
                SCHEMA_V1_1_MAJOR,
                SCHEMA_V1_1_MINOR,
            )
        ]
        assert connection.execute(
            "SELECT maintenance_kind,completed_at_ns IS NOT NULL FROM maintenance_events"
        ).fetchall() == [("SCHEMA_UPGRADE", 1)]
        with pytest.raises(SubstrateSchemaCompatibilityError, match="read-only"):
            NativeObjectRevisionGovernanceService(connection)
        upgraded = upgrade_schema_v1_1_to_v1_2(connection)
        assert (upgraded.schema_major, upgraded.schema_minor) == (SCHEMA_MAJOR, SCHEMA_MINOR)
        assert NativeObjectRevisionGovernanceService(connection).get_current_object_governance(
            object_id=historical
        ) is None
        assert isinstance(NativeObjectService(connection), NativeObjectService)

        assert upgrade_schema_v1_to_v1_1(connection) == upgraded
        assert upgrade_schema_v1_1_to_v1_2(connection) == upgraded
        assert connection.execute("SELECT count(*) FROM schema_migration_ledger").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM maintenance_events").fetchone()[0] == 2
        assert connection.execute(
            "SELECT migration_key FROM schema_migration_ledger WHERE migration_key=?",
            (SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER_MIGRATION_KEY,),
        ).fetchone() == (SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER_MIGRATION_KEY,)
    finally:
        qualified.close()


def test_explicit_v1_1_upgrade_adds_only_runtime_order_and_records_its_own_ledger(tmp_path: Path):
    qualified = _database(tmp_path, v1_1=True)
    try:
        connection = qualified.connection
        assert open_schema(connection, writable=False).schema_minor == SCHEMA_V1_1_MINOR
        with pytest.raises(SubstrateSchemaCompatibilityError, match="read-only"):
            open_schema(connection)
        with pytest.raises(SubstrateSchemaCompatibilityError, match="explicit versioned schema upgrade"):
            create_schema(connection)
        upgraded = upgrade_schema_v1_1_to_v1_2(connection)
        assert upgraded.schema_minor == SCHEMA_MINOR
        assert connection.execute(
            "SELECT count(*) FROM memory_runtime_enumeration_orders"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT migration_key,from_major,from_minor,to_major,to_minor "
            "FROM schema_migration_ledger"
        ).fetchall() == [
            (
                SCHEMA_V1_1_TO_V1_2_RUNTIME_ORDER_MIGRATION_KEY,
                SCHEMA_V1_1_MAJOR,
                SCHEMA_V1_1_MINOR,
                SCHEMA_MAJOR,
                SCHEMA_MINOR,
            )
        ]
        assert upgrade_schema_v1_1_to_v1_2(connection) == upgraded
    finally:
        qualified.close()


@pytest.mark.parametrize("mutation", ("hybrid", "newer", "wrong-schema-id"))
def test_upgrade_refuses_invalid_or_non_v1_source(tmp_path: Path, mutation: str):
    qualified = _database(tmp_path, v1=True)
    try:
        connection = qualified.connection
        if mutation == "hybrid":
            connection.execute("CREATE TABLE unapproved_hybrid (value INTEGER) STRICT")
        elif mutation == "newer":
            connection.execute("UPDATE core_metadata SET schema_minor=2")
        else:
            connection.execute("PRAGMA ignore_check_constraints=ON")
            connection.execute("UPDATE core_metadata SET schema_id='other.schema'")
            connection.execute("PRAGMA ignore_check_constraints=OFF")
        with pytest.raises(SubstrateSchemaCompatibilityError):
            upgrade_schema_v1_to_v1_1(connection)
    finally:
        qualified.close()


def test_upgrade_rolls_back_all_evolution_state_on_forced_failure(tmp_path: Path, monkeypatch):
    qualified = _database(tmp_path, v1=True)
    try:
        connection = qualified.connection

        def fail(_connection):
            raise RuntimeError("forced upgrade rollback")

        monkeypatch.setattr(schema_module, "_before_upgrade_metadata_write", fail)
        with pytest.raises(RuntimeError, match="forced upgrade rollback"):
            upgrade_schema_v1_to_v1_1(connection)
        assert (
            open_schema(connection, writable=False).schema_major,
            open_schema(connection, writable=False).schema_minor,
        ) == (1, 0)
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='object_revision_governance'"
        ).fetchone() is None
        assert connection.execute("SELECT count(*) FROM schema_migration_ledger").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM maintenance_events").fetchone()[0] == 0
    finally:
        qualified.close()


def test_v1_is_read_only_for_current_semantic_services_until_explicit_upgrade(tmp_path: Path):
    qualified = _database(tmp_path, v1=True)
    try:
        connection = qualified.connection
        assert open_schema(connection, writable=False) == schema_module.validate_schema(connection)
        before = _semantic_counts(connection)
        with pytest.raises(SubstrateSchemaCompatibilityError, match="read-only"):
            open_schema(connection)
        with pytest.raises(SubstrateSchemaCompatibilityError, match="read-only"):
            NativeObjectService(connection)
        with pytest.raises(SubstrateSchemaCompatibilityError, match="read-only"):
            NativeRelationshipService(connection)
        with pytest.raises(SubstrateSchemaCompatibilityError, match="read-only"):
            NativeMemoryCompatibilityFacade(connection)
        assert _semantic_counts(connection) == before

        reader = NativeMotifRuntimeReader(connection)
        assert reader.list_runtime_motifs(
            motif_alias_namespace_id=_id(),
            domain_id="read-only-domain",
            semantic_scope_id=_id(),
        ) == ()

        assert upgrade_schema_v1_to_v1_1(connection).schema_minor == SCHEMA_V1_1_MINOR
        assert upgrade_schema_v1_1_to_v1_2(connection).schema_minor == SCHEMA_MINOR
        assert open_schema(connection).schema_minor == SCHEMA_MINOR
        assert isinstance(NativeObjectService(connection), NativeObjectService)
        assert isinstance(NativeRelationshipService(connection), NativeRelationshipService)
        assert isinstance(NativeMemoryCompatibilityFacade(connection), NativeMemoryCompatibilityFacade)
    finally:
        qualified.close()


def test_governance_exact_revision_constraints_and_immutability(tmp_path: Path):
    qualified = _database(tmp_path)
    try:
        connection = qualified.connection
        identity, scope, idem = _foundation(connection)
        service = NativeObjectService(connection)
        first = service.create_object(
            idempotency_namespace_id=idem,
            idempotency_key="first",
            state=_state(identity, scope),
        )
        for index, value in enumerate((-1, 2, None, "not-a-boolean")):
            invalid = service.create_object(
                idempotency_namespace_id=idem,
                idempotency_key=f"invalid-governance-{index}",
                state=_state(identity, scope),
            )
            invalid_ordinal = connection.execute(
                "SELECT revision_ordinal FROM object_revisions WHERE object_revision_id=?",
                (native_id_to_bytes(invalid.revision_id),),
            ).fetchone()[0]
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)",
                    (
                        native_id_to_bytes(invalid.object_id),
                        native_id_to_bytes(invalid.revision_id),
                        invalid_ordinal,
                        value,
                        0,
                        0,
                        0,
                        0,
                    ),
                )

        _insert_governance(connection, first, NativeMemoryGovernanceFacts())
        base = (
            native_id_to_bytes(first.object_id),
            native_id_to_bytes(first.revision_id),
            connection.execute(
                "SELECT revision_ordinal FROM object_revisions WHERE object_revision_id=?",
                (native_id_to_bytes(first.revision_id),),
            ).fetchone()[0],
        )
        assert NativeObjectRevisionGovernanceService(connection).get_object_revision_governance(
            object_id=first.object_id,
            object_revision_id=first.revision_id,
            object_revision_ordinal=base[2],
        ).facts == NativeMemoryGovernanceFacts()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)",
                (*base, 0, 0, 0, 0, 0),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)",
                (
                    native_id_to_bytes(_id()),
                    native_id_to_bytes(first.revision_id),
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                ),
            )
        other = service.create_object(
            idempotency_namespace_id=idem,
            idempotency_key="other-revision",
            state=_state(identity, scope),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)",
                (
                    native_id_to_bytes(first.object_id),
                    native_id_to_bytes(other.revision_id),
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)",
                (native_id_to_bytes(first.object_id), native_id_to_bytes(_id()), 1, 0, 0, 0, 0, 0),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)",
                (native_id_to_bytes(first.object_id), native_id_to_bytes(first.revision_id), 2, 0, 0, 0, 0, 0),
            )
        with pytest.raises(sqlite3.IntegrityError, match="immutable object revision governance"):
            connection.execute("UPDATE object_revision_governance SET protected=1")
        with pytest.raises(sqlite3.IntegrityError, match="immutable object revision governance"):
            connection.execute("DELETE FROM object_revision_governance")
    finally:
        qualified.close()


def test_governance_reads_are_exact_revision_bound_and_missing_is_not_default(tmp_path: Path):
    qualified = _database(tmp_path)
    try:
        connection = qualified.connection
        identity, scope, idem = _foundation(connection)
        objects = NativeObjectService(connection)
        first = objects.create_object(
            idempotency_namespace_id=idem,
            idempotency_key="r1",
            state=_state(identity, scope, lifecycle_state="PROTECTED"),
        )
        r1_facts = NativeMemoryGovernanceFacts(protected=False, decay_accelerated=True)
        _insert_governance(connection, first, r1_facts)
        second = objects.transition_object(
            idempotency_namespace_id=idem,
            idempotency_key="r2",
            object_id=first.object_id,
            expected_revision_id=first.revision_id,
            state=_state(identity, scope, lifecycle_state="UNSET"),
        )
        r2_facts = NativeMemoryGovernanceFacts(protected=True, non_shareable=True)
        _insert_governance(connection, second, r2_facts)
        missing = objects.create_object(
            idempotency_namespace_id=idem,
            idempotency_key="missing",
            state=_state(identity, scope),
        )

        reader = NativeObjectRevisionGovernanceService(connection)
        assert reader.get_object_revision_governance(
            object_id=first.object_id,
            object_revision_id=first.revision_id,
            object_revision_ordinal=1,
        ).facts == r1_facts
        assert reader.get_current_object_governance(object_id=first.object_id).facts == r2_facts
        assert reader.get_current_object_governance(object_id=missing.object_id) is None
        assert objects.get_object_revision(first.revision_id).lifecycle_state == "PROTECTED"
        assert objects.get_current_object(first.object_id).lifecycle_state == "UNSET"
        assert r1_facts.protected is False and r2_facts.protected is True
    finally:
        qualified.close()


def test_closed_child_provenance_is_recoverable_from_memory_result(tmp_path: Path):
    qualified = _database(tmp_path)
    try:
        connection = qualified.connection
        identity, scope, idem = _foundation(connection)
        service = NativeClosedChildQualificationService(connection)
        facts = NativeMemoryGovernanceFacts(
            protected=True,
            collective_export_blocked=True,
        )
        result = service.create_memory_with_closed_children(
            idempotency_namespace_id=idem,
            idempotency_key="closed-child",
            state=_state(identity, scope),
            provenance=_provenance(),
            governance=facts,
        )
        assert connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM operation_outputs").fetchone()[0] == 1
        assert connection.execute(
            "SELECT transition_kind,origin_kind FROM semantic_transitions"
        ).fetchall() == [("OBJECT_REVISION", "NATIVE")]
        assert connection.execute(
            "SELECT output_kind,output_role FROM operation_outputs"
        ).fetchall() == [("OBJECT", "OBJECT")]
        assert connection.execute("SELECT count(*) FROM provenance_records").fetchone()[0] == 1
        assert connection.execute(
            "SELECT provenance_id FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(result.revision_id),),
        ).fetchone()[0] == native_id_to_bytes(result.provenance_id)
        assert NativeObjectRevisionGovernanceService(connection).get_current_object_governance(
            object_id=result.object_id
        ).facts == facts
        assert service.create_memory_with_closed_children(
            idempotency_namespace_id=idem,
            idempotency_key="closed-child",
            state=_state(identity, scope),
            provenance=_provenance(),
            governance=facts,
        ) == result
        with pytest.raises(SubstrateIdempotencyConflict):
            service.create_memory_with_closed_children(
                idempotency_namespace_id=idem,
                idempotency_key="closed-child",
                state=_state(identity, scope),
                provenance=_provenance(notes="changed intent"),
                governance=facts,
            )
        assert connection.execute("SELECT count(*) FROM provenance_records").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError, match="immutable provenance"):
            connection.execute("UPDATE provenance_records SET origin_kind='changed'")
        with pytest.raises(sqlite3.IntegrityError, match="immutable provenance"):
            connection.execute("DELETE FROM provenance_records")
    finally:
        qualified.close()


def test_closed_child_failure_rolls_back_provenance_and_memory_operation(tmp_path: Path):
    qualified = _database(tmp_path)
    try:
        connection = qualified.connection
        identity, scope, idem = _foundation(connection)
        service = NativeClosedChildQualificationService(connection)
        before = tuple(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "provenance_records", "objects", "object_revisions", "object_revision_governance",
                "semantic_transitions", "operations",
            )
        )
        with pytest.raises(RuntimeError, match="forced closed-child qualification rollback"):
            service.create_memory_with_closed_children(
                idempotency_namespace_id=idem,
                idempotency_key="rollback",
                state=_state(identity, scope),
                provenance=_provenance(),
                governance=NativeMemoryGovernanceFacts(),
                _test_fail_after_provenance=True,
            )
        after = tuple(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "provenance_records", "objects", "object_revisions", "object_revision_governance",
                "semantic_transitions", "operations",
            )
        )
        assert after == before
    finally:
        qualified.close()
