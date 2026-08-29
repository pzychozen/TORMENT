from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import (
    SubstrateIdempotencyConflict,
    SubstrateIntegrityMismatch,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
    SubstrateRevisionConflict,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.objects import NativeObjectService, ObjectState, SubstrateTx
from torment_service.substrate.relationships import Endpoint, NativeRelationshipService, RelationshipState
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationFailureRequest,
    RepresentationIntegrityExpectationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.schema import create_schema


def _uuid():
    return generate_native_id()


def _object_state(namespace, scope):
    return ObjectState(namespace, scope, "NOTE", "EXISTS", "LIVE", True, "GOVERNED")


def _seed(connection):
    namespace, scope, idempotency_namespace = _uuid(), _uuid(), _uuid()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(namespace), "native-test"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), "native-test"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "native-test"),
    )
    return namespace, scope, idempotency_namespace


def _object_pending(service, source, idempotency_namespace, key, *, payload: bytes, dependencies=()):
    return service.create_representation_pending(
        idempotency_namespace_id=idempotency_namespace,
        idempotency_key=key,
        request=RepresentationRequest(
            "OBJECT_REVISION",
            source.object_id,
            source.revision_id,
            None,
            None,
            "EMBEDDING",
            1,
            "v1",
            "raw",
            dependencies=dependencies,
            expected_payload_byte_length=len(payload),
        ),
    )


def _establish(service, representation_id, idempotency_namespace, key, payload: bytes):
    return service.establish_representation_integrity_expectation(
        idempotency_namespace_id=idempotency_namespace,
        idempotency_key=key,
        request=RepresentationIntegrityExpectationRequest(
            representation_id,
            INTEGRITY_ALGORITHM_SHA256,
            sha256(payload).digest(),
            INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )


def _ready_request(representation_id, payload: bytes):
    return RepresentationReadyRequest(representation_id, "EMBEDDING", 1, "v1", "raw", payload)


def test_pending_is_idempotent_and_binds_an_exact_object_revision(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "pending.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        source = NativeObjectService(connection).create_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="object",
            state=_object_state(namespace, scope),
        )
        service = NativeRepresentationService(connection)
        request = RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "SYNTHETIC", 1, "v1", "raw",
        )
        first = service.create_representation_pending(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="pending",
            request=request,
        )
        assert service.create_representation_pending(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="pending",
            request=request,
        ) == first
        assert first.readiness == "PENDING"
        with pytest.raises(SubstrateRevisionConflict, match="pre-established integrity expectation"):
            service.publish_representation_ready(
                idempotency_namespace_id=idempotency_namespace,
                idempotency_key="ready-without-expectation",
                request=RepresentationReadyRequest(first.representation_id, "SYNTHETIC", 1, "v1", "raw", b"x"),
            )
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
        with pytest.raises(SubstrateIdempotencyConflict):
            service.create_representation_pending(
                idempotency_namespace_id=idempotency_namespace,
                idempotency_key="pending",
                request=RepresentationRequest(
                    "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
                    "OTHER", 1, "v1", "raw",
                ),
            )
    finally:
        qualified.close()


def test_ready_preestablishes_immutable_integrity_and_supports_lost_response_retry(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "ready.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        objects = NativeObjectService(connection)
        source = objects.create_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="object",
            state=_object_state(namespace, scope),
        )
        source_before = objects.get_current_object(source.object_id)
        source_revision_count = connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0]
        service = NativeRepresentationService(connection)
        payload = b"object-derived-representation"
        pending = _object_pending(service, source, idempotency_namespace, "pending", payload=payload)

        expectation = _establish(service, pending.representation_id, idempotency_namespace, "expect", payload)
        assert _establish(service, pending.representation_id, idempotency_namespace, "expect", payload) == expectation
        assert service.get_representation_metadata(pending.representation_id).integrity_expectation_id == expectation.expectation_id
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE integrity_expectations SET expected_value=? WHERE expectation_id=?",
                (b"x" * 32, native_id_to_bytes(expectation.expectation_id)),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "DELETE FROM integrity_expectations WHERE expectation_id=?",
                (native_id_to_bytes(expectation.expectation_id),),
            )

        request = _ready_request(pending.representation_id, payload)
        service.publish_representation_ready(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="ready",
            request=request,
        )
        published = service.publish_representation_ready(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="ready",
            request=request,
        )
        assert published.readiness == "READY"
        assert published.disposition == "USABLE"
        assert published.selected_measurement_id is not None

        traced_sql: list[str] = []
        connection.set_trace_callback(traced_sql.append)
        assert service.get_representation_metadata(pending.representation_id) == published
        connection.set_trace_callback(None)
        assert not any("representation_payloads" in statement.lower() for statement in traced_sql)
        assert service.read_representation_payload(pending.representation_id) == payload

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE integrity_measurements SET result='MISMATCH' WHERE measurement_id=?",
                (native_id_to_bytes(published.selected_measurement_id),),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "DELETE FROM integrity_measurements WHERE measurement_id=?",
                (native_id_to_bytes(published.selected_measurement_id),),
            )
        assert connection.execute(
            """
            SELECT count(*) FROM semantic_transitions t
            JOIN representation_state_effects s USING(transition_id)
            JOIN integrity_measurement_effects m USING(transition_id)
            JOIN operation_outputs o ON o.operation_id=t.operation_id
            WHERE t.transition_kind='REPRESENTATION_READY'
              AND s.representation_id=? AND o.representation_id=s.representation_id
              AND o.output_role='REPRESENTATION_READY'
            """,
            (native_id_to_bytes(pending.representation_id),),
        ).fetchone()[0] == 1
        assert objects.get_current_object(source.object_id) == source_before
        assert connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0] == source_revision_count
    finally:
        qualified.close()


def test_integrity_mismatch_refuses_ready_without_payload_or_transition_residue_then_explicit_failure(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "mismatch.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        objects = NativeObjectService(connection)
        source = objects.create_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="object",
            state=_object_state(namespace, scope),
        )
        source_before = objects.get_current_object(source.object_id)
        service = NativeRepresentationService(connection)
        pending = _object_pending(service, source, idempotency_namespace, "pending", payload=b"expected")
        _establish(service, pending.representation_id, idempotency_namespace, "expect", b"expected")

        with pytest.raises(SubstrateIntegrityMismatch):
            service.publish_representation_ready(
                idempotency_namespace_id=idempotency_namespace,
                idempotency_key="mismatched-ready",
                request=_ready_request(pending.representation_id, b"observed"),
            )
        assert service.get_representation_metadata(pending.representation_id).readiness == "PENDING"
        assert connection.execute(
            "SELECT count(*) FROM representation_payloads WHERE representation_id=?",
            (native_id_to_bytes(pending.representation_id),),
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM semantic_transitions WHERE transition_kind='REPRESENTATION_READY'"
        ).fetchone()[0] == 0

        failed_request = RepresentationFailureRequest(
            pending.representation_id, "DERIVATION_INTEGRITY_MISMATCH", "payload digest differed"
        )
        service.fail_representation(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="explicit-failure",
            request=failed_request,
        )
        failed = service.fail_representation(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="explicit-failure",
            request=failed_request,
        )
        assert (failed.readiness, failed.disposition, failed.selected_measurement_id) == ("FAILED", "WITHHELD", None)
        assert connection.execute(
            """
            SELECT count(*) FROM semantic_transitions t
            JOIN representation_state_effects s USING(transition_id)
            JOIN operation_outputs o ON o.operation_id=t.operation_id
            WHERE t.transition_kind='REPRESENTATION_FAILED'
              AND s.representation_id=? AND o.representation_id=s.representation_id
              AND o.output_role='REPRESENTATION_FAILED'
            """,
            (native_id_to_bytes(pending.representation_id),),
        ).fetchone()[0] == 1
        with pytest.raises(SubstrateObjectNotFound):
            service.read_representation_payload(pending.representation_id)
        assert objects.get_current_object(source.object_id) == source_before
    finally:
        qualified.close()


def test_ready_requires_ready_dependencies(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "dependencies.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        objects = NativeObjectService(connection)
        dependency_source = objects.create_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="dependency-source",
            state=_object_state(namespace, scope),
        )
        source = objects.create_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="source",
            state=_object_state(namespace, scope),
        )
        service = NativeRepresentationService(connection)
        dependency = _object_pending(
            service, dependency_source, idempotency_namespace, "dependency", payload=b"dependency"
        )
        blocked = _object_pending(
            service, source, idempotency_namespace, "blocked", payload=b"blocked",
            dependencies=(dependency.representation_id,),
        )
        _establish(service, dependency.representation_id, idempotency_namespace, "dependency-expect", b"dependency")
        _establish(service, blocked.representation_id, idempotency_namespace, "blocked-expect", b"blocked")
        with pytest.raises(SubstrateRevisionConflict):
            service.publish_representation_ready(
                idempotency_namespace_id=idempotency_namespace,
                idempotency_key="blocked-ready",
                request=_ready_request(blocked.representation_id, b"blocked"),
            )
        assert connection.execute(
            "SELECT count(*) FROM representation_payloads WHERE representation_id=?",
            (native_id_to_bytes(blocked.representation_id),),
        ).fetchone()[0] == 0
        service.publish_representation_ready(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="dependency-ready",
            request=_ready_request(dependency.representation_id, b"dependency"),
        )
        assert service.publish_representation_ready(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="blocked-ready",
            request=_ready_request(blocked.representation_id, b"blocked"),
        ).readiness == "READY"
    finally:
        qualified.close()


def test_relationship_revision_source_ready_leaves_relationship_commit_truth_unchanged(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "relationship_ready.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        objects = NativeObjectService(connection)
        left = objects.create_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="left",
            state=_object_state(namespace, scope),
        )
        right = objects.create_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="right",
            state=_object_state(namespace, scope),
        )
        relationships = NativeRelationshipService(connection)
        source = relationships.create_relationship(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="relationship",
            state=RelationshipState(
                namespace, scope, "PAIR", "EXISTS", "LIVE", True, "GOVERNED",
                endpoints=(Endpoint(0, "LEFT", scope, left.object_id), Endpoint(1, "RIGHT", scope, right.object_id)),
            ),
        )
        source_before = relationships.get_current_relationship(source.relationship_id)
        service = NativeRepresentationService(connection)
        payload = b"relationship-derived-representation"
        pending = service.create_representation_pending(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="pending",
            request=RepresentationRequest(
                "RELATIONSHIP_REVISION", None, None, source.relationship_id, source.revision_id,
                "EMBEDDING", 1, "v1", "raw", expected_payload_byte_length=len(payload),
            ),
        )
        _establish(service, pending.representation_id, idempotency_namespace, "expect", payload)
        assert service.publish_representation_ready(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="ready",
            request=_ready_request(pending.representation_id, payload),
        ).readiness == "READY"
        assert relationships.get_current_relationship(source.relationship_id) == source_before
    finally:
        qualified.close()


def test_transaction_helper_refuses_missing_ready_state_measurement_or_output_effects(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "incomplete_ready.db")
    try:
        connection = qualified.connection
        create_schema(connection)
        namespace, scope, idempotency_namespace = _seed(connection)
        source = NativeObjectService(connection).create_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="object",
            state=_object_state(namespace, scope),
        )
        service = NativeRepresentationService(connection)
        payload = b"complete-payload"
        pending = _object_pending(service, source, idempotency_namespace, "pending", payload=payload)
        expectation = _establish(service, pending.representation_id, idempotency_namespace, "expect", payload)

        def assert_incomplete(*, include_state: bool, include_measurement: bool, include_output: bool, match: str):
            operation_id, transition_id, measurement_id = _uuid(), _uuid(), _uuid()
            representation_id = native_id_to_bytes(pending.representation_id)
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
                    (
                        native_id_to_bytes(operation_id),
                        native_id_to_bytes(idempotency_namespace),
                        f"incomplete-{include_state}-{include_measurement}-{include_output}",
                        "PUBLISH_REPRESENTATION_READY",
                        "TMS-INTENT-1",
                        "{}",
                    ),
                )
                connection.execute(
                    "INSERT INTO representation_payloads VALUES (?,?,?,0)",
                    (representation_id, payload, len(payload)),
                )
                connection.execute(
                    "INSERT INTO integrity_measurements VALUES (?,?,?,?,?,0)",
                    (
                        native_id_to_bytes(measurement_id),
                        native_id_to_bytes(expectation.expectation_id),
                        "MATCH",
                        sha256(payload).digest(),
                        None,
                    ),
                )
                connection.execute(
                    "UPDATE representation_current_state SET readiness='READY',operational_disposition='USABLE',selected_integrity_measurement_id=? WHERE representation_id=?",
                    (native_id_to_bytes(measurement_id), representation_id),
                )
                connection.execute(
                    "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
                    (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "REPRESENTATION_READY", "NATIVE"),
                )
                if include_state:
                    connection.execute(
                        "INSERT INTO representation_state_effects VALUES (?,?,?,?,?)",
                        (native_id_to_bytes(transition_id), representation_id, "READY", "USABLE", native_id_to_bytes(measurement_id)),
                    )
                if include_measurement:
                    connection.execute(
                        "INSERT INTO integrity_measurement_effects VALUES (?,?)",
                        (native_id_to_bytes(transition_id), native_id_to_bytes(measurement_id)),
                    )
                if include_output:
                    connection.execute(
                        "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,representation_id) VALUES (?,?,?,?,?)",
                        (native_id_to_bytes(operation_id), 0, "REPRESENTATION_READY", "REPRESENTATION", representation_id),
                    )
                tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
                tx.transitions.append(native_id_to_bytes(transition_id))
                tx.representation_ready.append(
                    (representation_id, native_id_to_bytes(expectation.expectation_id), native_id_to_bytes(measurement_id))
                )
                with pytest.raises(SubstrateInvariantViolation, match=match):
                    tx.validate()
            finally:
                connection.execute("ROLLBACK")

        assert_incomplete(include_state=False, include_measurement=True, include_output=True, match="H2")
        assert_incomplete(include_state=True, include_measurement=False, include_output=True, match="integrity measurement effect")
        assert_incomplete(include_state=True, include_measurement=True, include_output=False, match="H8")
    finally:
        qualified.close()


def test_phase_7e2_does_not_expose_h6_reconciliation_or_h7_legacy_admission():
    service_methods = set(dir(NativeRepresentationService))
    assert not {"reconcile_representation", "resolve_reconciliation_case", "admit_legacy_representation"} & service_methods
