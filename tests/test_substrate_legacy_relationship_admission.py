"""Focused Phase 7F3A synthetic legacy relationship-admission tests."""

from __future__ import annotations

from pathlib import Path
import shutil
from uuid import UUID

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import (
    EDGES_CANDIDATE_SELECTION_RULE,
    NativeLegacyObjectAdmissionService,
    NativeLegacyRelationshipAdmissionService,
)
from torment_service.substrate.objects import NativeObjectService, ObjectState, SubstrateTx
from torment_service.substrate.relationships import NativeRelationshipService
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "legacy-relationship-admission.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    object_namespace, relationship_namespace, scope_one, scope_two, idempotency_namespace = (
        _id(),
        _id(),
        _id(),
        _id(),
        _id(),
    )
    for namespace, key in (
        (object_namespace, "legacy-relationship-object-namespace"),
        (relationship_namespace, "legacy-relationship-namespace"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(namespace), key),
        )
    for scope, key in ((scope_one, "legacy-scope-one"), (scope_two, "legacy-scope-two")):
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(scope), key),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "legacy-relationship-idempotency"),
    )
    return qualified, object_namespace, relationship_namespace, scope_one, scope_two, idempotency_namespace


def _snapshot(
    tmp_path: Path, source_key: str, node_rows: list[bytes], edge_rows: list[bytes]
):
    capture = tmp_path / source_key
    root = capture / "legacy-snapshot"
    root.mkdir(parents=True)
    (root / "nodes.jsonl").write_bytes(b"".join(node_rows))
    (root / "edges.jsonl").write_bytes(b"".join(edge_rows))
    (root / "memory_events.jsonl").write_bytes(b'{"event":"MEMORY_CREATE","eid":999}\n')
    (root / "embeddings").mkdir()
    (root / "embeddings" / "manifest.json").write_bytes(b'{"embedding":"evidence-only"}\n')
    manifest_path = capture / "snapshot-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=_id(),
        legacy_source_namespace_key=source_key,
        capture_label="synthetic 7F3A relationship fixture only",
    )
    return root, manifest_path, manifest


def _admit_nodes(service, root, manifest_path, idempotency_namespace, object_namespace, scope):
    return service.admit_nodes_current_state(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
        object_identity_namespace_id=object_namespace,
        unknown_semantic_scope_id=scope,
    )


def _admit_edges(service, root, manifest_path, idempotency_namespace, relationship_namespace, scope):
    return service.admit_edges_current_state(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
        relationship_identity_namespace_id=relationship_namespace,
        unknown_semantic_scope_id=scope,
    )


def _edge(edge_id: str, endpoints: list[dict[str, object]], **attributes: object) -> bytes:
    import json

    return (
        json.dumps(
            {
                "edge_id": edge_id,
                "relationship_kind": "LEGACY_EDGE",
                "endpoints": endpoints,
                **attributes,
            },
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def test_successful_relationship_admission_is_idempotent_namespaced_and_non_authoritative(
    tmp_path: Path,
):
    qualified, object_namespace, relationship_namespace, scope_one, _scope_two, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(
            tmp_path,
            "source-a",
            [b'{"eid":1,"text":"one"}\n', b'{"eid":2,"text":"two"}\n'],
            [
                _edge(
                    "edge-1",
                    [{"role": "MEMBER", "eid": 1}, {"role": "MEMBER", "eid": 2}],
                    authority="ACTIVE_AUTHORIZATION",
                    label="flexible legacy content",
                )
            ],
        )
        objects = NativeLegacyObjectAdmissionService(connection)
        node_run = _admit_nodes(
            objects, root, manifest_path, idempotency_namespace, object_namespace, scope_one
        )
        relationships = NativeLegacyRelationshipAdmissionService(connection)
        first = _admit_edges(
            relationships, root, manifest_path, idempotency_namespace, relationship_namespace, scope_one
        )
        # This is the lost-response retry: all durable outputs reconstruct identically.
        retry = _admit_edges(
            relationships, root, manifest_path, idempotency_namespace, relationship_namespace, scope_one
        )
        admitted = first.results[0]
        assert retry == first
        assert first.candidate_selection_rule == EDGES_CANDIDATE_SELECTION_RULE
        assert admitted.admission_status == "ADMITTED"
        assert admitted.relationship_id and admitted.revision_id and admitted.transition_id
        assert relationships.resolve_legacy_relationship_alias(
            legacy_source_namespace_id=manifest.legacy_source_namespace_id,
            alias_kind="EDGE_ID",
            alias_value="edge-1",
        ) == admitted.relationship_id
        with pytest.raises(SubstrateObjectNotFound):
            relationships.resolve_legacy_relationship_alias(
                legacy_source_namespace_id=manifest.legacy_source_namespace_id,
                alias_kind="EDGE_ID",
                alias_value="missing",
            )
        view = NativeRelationshipService(connection).get_current_relationship(admitted.relationship_id)
        assert view.revision_id == admitted.revision_id and view.ordinal == 1
        assert [(endpoint.role, endpoint.binding_mode, endpoint.object_revision_id) for endpoint in view.endpoints] == [
            ("MEMBER", "IDENTITY", None),
            ("MEMBER", "IDENTITY", None),
        ]
        node_ids = {result.raw_eid: result.object_id for result in node_run.results}
        assert [endpoint.object_id for endpoint in view.endpoints] == [node_ids[1], node_ids[2]]
        assert connection.execute(
            """
            SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,
                   lifecycle_state,lifecycle_authoritative,governance_state,authority_category,payload_text
            FROM relationship_revisions WHERE relationship_revision_id=?
            """,
            (native_id_to_bytes(admitted.revision_id),),
        ).fetchone() == (
            "LEGACY_PREDECESSOR_UNKNOWN",
            None,
            None,
            "UNKNOWN",
            0,
            "UNKNOWN",
            "NOT_APPLICABLE",
            '{"legacy_attributes":{"authority":"ACTIVE_AUTHORIZATION","label":"flexible legacy content"}}',
        )
        assert connection.execute(
            "SELECT transition_kind,origin_kind FROM semantic_transitions WHERE transition_id=?",
            (native_id_to_bytes(admitted.transition_id),),
        ).fetchone() == ("LEGACY_RELATIONSHIP_ADMISSION", "LEGACY_ADMISSION")
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationship_revisions").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationship_revision_endpoints").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM legacy_relationship_aliases").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        with pytest.raises(Exception):
            connection.execute(
                "DELETE FROM relationship_revision_endpoints WHERE relationship_revision_id=?",
                (native_id_to_bytes(admitted.revision_id),),
            )
    finally:
        qualified.close()


def test_dangling_and_malformed_edge_rows_are_durable_without_native_relationships(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope_one, _scope_two, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest = _snapshot(
            tmp_path,
            "dangling-source",
            [b'{"eid":1,"text":"only endpoint"}\n'],
            [
                _edge(
                    "dangling-edge",
                    [{"role": "SOURCE", "eid": 1}, {"role": "TARGET", "eid": 999}],
                ),
                b'{"edge_id":"malformed-edge","relationship_kind":\n',
            ],
        )
        _admit_nodes(
            NativeLegacyObjectAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            object_namespace,
            scope_one,
        )
        run = _admit_edges(
            NativeLegacyRelationshipAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            relationship_namespace,
            scope_one,
        )
        assert [(result.raw_edge_id, result.admission_status) for result in run.results] == [
            ("dangling-edge", "QUARANTINED"),
            ("malformed-edge", "UNKNOWN"),
        ]
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM relationship_revisions").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM relationship_revision_endpoints").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_relationship_aliases").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_quarantine_records").fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM legacy_object_aliases WHERE alias_value='999'"
        ).fetchone()[0] == 0
    finally:
        qualified.close()


def test_unknown_kind_and_duplicate_source_edge_ids_remain_evidence_not_history(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope_one, _scope_two, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest = _snapshot(
            tmp_path,
            "ambiguous-source",
            [b'{"eid":1}\n', b'{"eid":2}\n'],
            [
                b'{"relationship_kind":"LEGACY_EDGE","endpoints":[{"role":"A","eid":1},{"role":"B","eid":2}]}\n',
                b'{"edge_id":"unknown-kind","relationship_kind":"PAIR","endpoints":[{"role":"A","eid":1},{"role":"B","eid":2}]}\n',
                _edge("duplicate", [{"role": "A", "eid": 1}, {"role": "B", "eid": 2}]),
                _edge("duplicate", [{"role": "A", "eid": 2}, {"role": "B", "eid": 1}]),
            ],
        )
        _admit_nodes(
            NativeLegacyObjectAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            object_namespace,
            scope_one,
        )
        run = _admit_edges(
            NativeLegacyRelationshipAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            relationship_namespace,
            scope_one,
        )
        assert [result.admission_status for result in run.results] == [
            "NOT_ADMITTED",
            "NOT_ADMITTED",
            "NOT_ADMITTED",
            "NOT_ADMITTED",
        ]
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_relationship_aliases").fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM relationship_revisions WHERE lineage_kind='NATIVE_ORDINARY'"
        ).fetchone()[0] == 0
    finally:
        qualified.close()


def test_source_namespace_resolution_never_uses_the_same_eid_from_another_source(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope_one, _scope_two, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root_a, manifest_a_path, manifest_a = _snapshot(
            tmp_path,
            "source-a",
            [b'{"eid":7,"text":"a"}\n'],
            [_edge("edge-a", [{"role": "MEMBER", "eid": 7}, {"role": "MEMBER", "eid": 7}])],
        )
        root_b, manifest_b_path, manifest_b = _snapshot(
            tmp_path,
            "source-b",
            [b'{"eid":7,"text":"b"}\n'],
            [_edge("edge-b", [{"role": "MEMBER", "eid": 7}, {"role": "MEMBER", "eid": 7}])],
        )
        object_service = NativeLegacyObjectAdmissionService(connection)
        nodes_a = _admit_nodes(object_service, root_a, manifest_a_path, idempotency_namespace, object_namespace, scope_one)
        nodes_b = _admit_nodes(object_service, root_b, manifest_b_path, idempotency_namespace, object_namespace, scope_one)
        relationships = NativeLegacyRelationshipAdmissionService(connection)
        result_a = _admit_edges(relationships, root_a, manifest_a_path, idempotency_namespace, relationship_namespace, scope_one).results[0]
        object_a, object_b = nodes_a.results[0].object_id, nodes_b.results[0].object_id
        assert object_a != object_b
        assert [endpoint.object_id for endpoint in NativeRelationshipService(connection).get_current_relationship(result_a.relationship_id).endpoints] == [object_a, object_a]
        assert relationships.resolve_legacy_relationship_alias(
            legacy_source_namespace_id=manifest_a.legacy_source_namespace_id,
            alias_kind="EDGE_ID",
            alias_value="edge-a",
        ) == result_a.relationship_id
        with pytest.raises(SubstrateObjectNotFound):
            relationships.resolve_legacy_relationship_alias(
                legacy_source_namespace_id=manifest_b.legacy_source_namespace_id,
                alias_kind="EDGE_ID",
                alias_value="edge-a",
            )
    finally:
        qualified.close()


def test_cross_scope_and_repeated_endpoint_roles_are_preserved_without_exact_revision_binding(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope_one, scope_two, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest = _snapshot(
            tmp_path,
            "cross-scope-source",
            [b'{"eid":1}\n', b'{"eid":2}\n'],
            [_edge("cross-scope", [{"role": "MEMBER", "eid": 1}, {"role": "MEMBER", "eid": 2}])],
        )
        node_run = _admit_nodes(
            NativeLegacyObjectAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            object_namespace,
            scope_one,
        )
        node_two = next(result for result in node_run.results if result.raw_eid == 2)
        NativeObjectService(connection).transition_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="synthetic-cross-scope-object-two",
            object_id=node_two.object_id,
            expected_revision_id=node_two.revision_id,
            state=ObjectState(
                object_namespace,
                scope_two,
                "LEGACY_CORE_NODE",
                "EXISTS",
                "UNKNOWN",
                False,
                "UNKNOWN",
            ),
        )
        result = _admit_edges(
            NativeLegacyRelationshipAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            relationship_namespace,
            scope_one,
        ).results[0]
        endpoints = NativeRelationshipService(connection).get_current_relationship(result.relationship_id).endpoints
        assert [endpoint.role for endpoint in endpoints] == ["MEMBER", "MEMBER"]
        assert [endpoint.semantic_scope_id for endpoint in endpoints] == [scope_one, scope_two]
        assert all(endpoint.binding_mode == "IDENTITY" and endpoint.object_revision_id is None for endpoint in endpoints)
    finally:
        qualified.close()


def test_moved_snapshot_retry_reuses_the_same_relationship_operation_and_outputs(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope_one, _scope_two, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest = _snapshot(
            tmp_path,
            "movable-source",
            [b'{"eid":1}\n', b'{"eid":2}\n'],
            [_edge("movable", [{"role": "A", "eid": 1}, {"role": "B", "eid": 2}])],
        )
        _admit_nodes(
            NativeLegacyObjectAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            object_namespace,
            scope_one,
        )
        relationships = NativeLegacyRelationshipAdmissionService(connection)
        first = _admit_edges(relationships, root, manifest_path, idempotency_namespace, relationship_namespace, scope_one)
        moved_capture = tmp_path / "moved-capture"
        shutil.copytree(root.parent, moved_capture)
        moved = _admit_edges(
            relationships,
            moved_capture / root.name,
            moved_capture / manifest_path.name,
            idempotency_namespace,
            relationship_namespace,
            scope_one,
        )
        assert moved == first
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 1
    finally:
        qualified.close()


def _manual_relationship_admission(
    connection,
    *,
    manifest,
    idempotency_namespace,
    relationship_namespace,
    endpoint_object_id,
    endpoint_scope,
    origin_kind: str = "LEGACY_ADMISSION",
    include_admission_effect: bool = True,
    include_output: bool = True,
    mismatched_output: tuple[UUID, UUID] | None = None,
):
    snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
    source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
    artifact_id = native_id_to_bytes(
        next(artifact.artifact_id for artifact in manifest.artifacts if artifact.observed_relative_locator == "edges.jsonl")
    )
    batch_id = connection.execute(
        """
        SELECT admission_batch_id FROM legacy_admission_batches
        WHERE legacy_snapshot_id=? AND batch_identity='TMS-LEGACY-RELATIONSHIP-ADMISSION-7F3A'
        """,
        (snapshot_id,),
    ).fetchone()[0]
    operation_id, transition_id, relationship_id, revision_id, admission_id, artifact_record_id = (
        _id(),
        _id(),
        _id(),
        _id(),
        _id(),
        _id(),
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
            (
                native_id_to_bytes(operation_id),
                native_id_to_bytes(idempotency_namespace),
                f"manual-relationship-{origin_kind}-{include_admission_effect}-{include_output}",
                "ADMIT_LEGACY_RELATIONSHIP_CURRENT",
                "TMS-INTENT-1",
                "{}",
            ),
        )
        connection.execute(
            "INSERT INTO legacy_artifact_records VALUES (?,?,?,?)",
            (native_id_to_bytes(artifact_record_id), artifact_id, f"manual-{relationship_id}", "edges.jsonl#line:manual"),
        )
        connection.execute(
            "INSERT INTO legacy_admission_records VALUES (?,?,?,'ADMITTED',NULL)",
            (native_id_to_bytes(admission_id), batch_id, native_id_to_bytes(artifact_record_id)),
        )
        connection.execute(
            "INSERT INTO relationships VALUES (?,?,?,?,?,?,?)",
            (
                native_id_to_bytes(relationship_id),
                native_id_to_bytes(relationship_namespace),
                "LEGACY_EDGE",
                native_id_to_bytes(transition_id),
                native_id_to_bytes(revision_id),
                1,
                0,
            ),
        )
        connection.execute(
            """
            INSERT INTO relationship_revisions(
                relationship_revision_id,relationship_id,revision_ordinal,lineage_kind,
                effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,
                governance_state,authority_category,payload_format,created_at_ns
            ) VALUES (?,?,1,'LEGACY_PREDECESSOR_UNKNOWN',?,'EXISTS','UNKNOWN',0,
                      'UNKNOWN','NOT_APPLICABLE','NONE',0)
            """,
            (native_id_to_bytes(revision_id), native_id_to_bytes(relationship_id), native_id_to_bytes(endpoint_scope)),
        )
        connection.execute(
            "INSERT INTO relationship_revision_endpoints VALUES (?,?,?,? ,?,'IDENTITY',NULL,NULL)",
            (native_id_to_bytes(revision_id), 0, "MEMBER", native_id_to_bytes(endpoint_scope), native_id_to_bytes(endpoint_object_id)),
        )
        connection.execute(
            "INSERT INTO legacy_relationship_aliases VALUES (?,'EDGE_ID','manual',?)",
            (source_namespace_id, native_id_to_bytes(relationship_id)),
        )
        connection.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "LEGACY_RELATIONSHIP_ADMISSION", origin_kind),
        )
        connection.execute(
            "INSERT INTO relationship_revision_effects VALUES (?,?,?,1)",
            (native_id_to_bytes(transition_id), native_id_to_bytes(relationship_id), native_id_to_bytes(revision_id)),
        )
        if include_admission_effect:
            connection.execute(
                "INSERT INTO legacy_admission_effects VALUES (?,?)",
                (native_id_to_bytes(transition_id), native_id_to_bytes(admission_id)),
            )
        if include_output:
            output_relationship_id, output_revision_id = (
                mismatched_output
                if mismatched_output is not None
                else (relationship_id, revision_id)
            )
            connection.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,relationship_id,relationship_revision_id,relationship_revision_ordinal) VALUES (?,?,?,'RELATIONSHIP',?,?,1)",
                (native_id_to_bytes(operation_id), 0, "LEGACY_RELATIONSHIP_ADMISSION", native_id_to_bytes(output_relationship_id), native_id_to_bytes(output_revision_id)),
            )
        tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
        tx.transitions.append(native_id_to_bytes(transition_id))
        tx.relationship_published.append((native_id_to_bytes(relationship_id), native_id_to_bytes(revision_id), 1))
        tx.legacy_relationship_admitted.append(
            (
                native_id_to_bytes(relationship_id),
                native_id_to_bytes(revision_id),
                1,
                native_id_to_bytes(admission_id),
                native_id_to_bytes(transition_id),
                snapshot_id,
                artifact_id,
                native_id_to_bytes(artifact_record_id),
                "EDGE_ID",
                "manual",
                ((0, "MEMBER", "1", native_id_to_bytes(endpoint_object_id), native_id_to_bytes(endpoint_scope)),),
            )
        )
        return tx
    except Exception:
        connection.execute("ROLLBACK")
        raise


@pytest.mark.parametrize(
    ("origin_kind", "include_admission_effect", "include_output", "mismatch_output", "match"),
    [
        ("NATIVE", True, True, False, "H7"),
        ("LEGACY_ADMISSION", False, True, False, "H2 legacy relationship admission effect"),
        ("LEGACY_ADMISSION", True, False, False, "H8 relationship output"),
        ("LEGACY_ADMISSION", True, True, True, "H8 relationship output"),
    ],
)
def test_h7_h2_and_h8_refuse_incomplete_or_masquerading_relationship_admission(
    tmp_path: Path, origin_kind: str, include_admission_effect: bool, include_output: bool, mismatch_output: bool, match: str
):
    qualified, object_namespace, relationship_namespace, scope_one, _scope_two, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(
            tmp_path,
            "invariant-source",
            [b'{"eid":1}\n', b'{"eid":2}\n'],
            [_edge("baseline", [{"role": "A", "eid": 1}, {"role": "B", "eid": 2}])],
        )
        node_run = _admit_nodes(
            NativeLegacyObjectAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            object_namespace,
            scope_one,
        )
        baseline = _admit_edges(
            NativeLegacyRelationshipAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            relationship_namespace,
            scope_one,
        )
        tx = _manual_relationship_admission(
            connection,
            manifest=manifest,
            idempotency_namespace=idempotency_namespace,
            relationship_namespace=relationship_namespace,
            endpoint_object_id=node_run.results[0].object_id,
            endpoint_scope=scope_one,
            origin_kind=origin_kind,
            include_admission_effect=include_admission_effect,
            include_output=include_output,
            mismatched_output=(baseline.results[0].relationship_id, baseline.results[0].revision_id)
            if mismatch_output
            else None,
        )
        try:
            with pytest.raises(SubstrateInvariantViolation, match=match):
                tx.validate()
        finally:
            connection.execute("ROLLBACK")
    finally:
        qualified.close()
