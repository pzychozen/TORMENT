"""Focused Phase 7F2 synthetic legacy object admission and H7 tests."""

from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import (
    NODES_CURRENT_SELECTION_RULE,
    NativeLegacyObjectAdmissionService,
)
from torment_service.substrate.objects import NativeObjectService, SubstrateTx
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "legacy-admission.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity_namespace, scope, idempotency_namespace = _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity_namespace), "legacy-admission-objects"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), "legacy-admission-unknown-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "legacy-admission-idempotency"),
    )
    return qualified, identity_namespace, scope, idempotency_namespace


def _snapshot(tmp_path: Path, source_key: str, node_rows: list[bytes]):
    capture = tmp_path / source_key
    root = capture / "legacy-snapshot"
    root.mkdir(parents=True)
    (root / "nodes.jsonl").write_bytes(b"".join(node_rows))
    (root / "edges.jsonl").write_bytes(b'{"source":1,"target":2}\n')
    (root / "memory_events.jsonl").write_bytes(b'{"event":"MEMORY_CREATE","eid":999}\n')
    (root / "embeddings").mkdir()
    (root / "embeddings" / "manifest.json").write_bytes(b'{"embedding":"evidence-only"}\n')
    manifest_path = capture / "snapshot-manifest.json"
    source_namespace_id = _id()
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=source_namespace_id,
        legacy_source_namespace_key=source_key,
        capture_label="synthetic 7F2 admission fixture only",
    )
    return root, manifest_path, manifest


def _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope):
    return service.admit_nodes_current_state(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
        object_identity_namespace_id=identity_namespace,
        unknown_semantic_scope_id=scope,
    )


def test_last_current_candidate_admission_is_typed_idempotent_and_non_authoritative(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(
            tmp_path,
            "source-a",
            [
                b'{"eid":1,"text":"first"}\n',
                b'{"eid":1,"text":"second","authority":"ACTIVE_AUTHORIZATION"}\n',
                b'{"eid":1,"text":"selected current","permission":"admin","authority":"ACTIVE_AUTHORIZATION"}\n',
                b'{"eid":2,"text":"only current"}\n',
            ],
        )
        service = NativeLegacyObjectAdmissionService(connection)
        first = _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope)
        # First response may be lost: the stable evidence key reconstructs all durable outputs.
        retry = _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope)
        admitted = [result for result in first.results if result.admission_status == "ADMITTED"]
        assert retry == first
        assert first.candidate_selection_rule == NODES_CURRENT_SELECTION_RULE
        assert [(result.raw_eid, result.line_ordinal) for result in admitted] == [(1, 3), (2, 4)]
        assert len({result.object_id for result in admitted}) == 2
        assert all(result.revision_id and result.transition_id for result in admitted)
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM legacy_admission_effects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert not hasattr(service, "get_object_by_eid")
        objects = NativeObjectService(connection)
        selected = admitted[0]
        current = objects.get_current_object(selected.object_id)
        exact = objects.get_object_revision(selected.revision_id)
        assert current == exact
        assert current.ordinal == 1
        assert connection.execute(
            """
            SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,
                   lifecycle_state,lifecycle_authoritative,governance_state,authority_category,payload_text
            FROM object_revisions WHERE object_revision_id=?
            """,
            (native_id_to_bytes(selected.revision_id),),
        ).fetchone() == (
            "LEGACY_PREDECESSOR_UNKNOWN",
            None,
            None,
            "UNKNOWN",
            0,
            "UNKNOWN",
            "NOT_APPLICABLE",
            '{"eid":1,"text":"selected current","permission":"admin","authority":"ACTIVE_AUTHORIZATION"}\n',
        )
        assert connection.execute(
            "SELECT transition_kind,origin_kind FROM semantic_transitions WHERE transition_id=?",
            (native_id_to_bytes(selected.transition_id),),
        ).fetchone() == ("LEGACY_OBJECT_ADMISSION", "LEGACY_ADMISSION")
        assert service.resolve_legacy_object_alias(
            legacy_source_namespace_id=manifest.legacy_source_namespace_id,
            alias_kind="EID",
            alias_value="1",
        ) == selected.object_id
        with pytest.raises(SubstrateObjectNotFound):
            service.resolve_legacy_object_alias(
                legacy_source_namespace_id=manifest.legacy_source_namespace_id,
                alias_kind="EID",
                alias_value="999",
            )
        # The MEMORY_CREATE evidence was present but never consulted to create EID 999.
        assert connection.execute(
            "SELECT count(*) FROM legacy_object_aliases WHERE alias_value='999'"
        ).fetchone()[0] == 0
    finally:
        qualified.close()


def test_moved_snapshot_retry_and_same_eid_in_different_namespaces_do_not_collide(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root_a, manifest_a_path, manifest_a = _snapshot(
            tmp_path, "source-a", [b'{"eid":7,"text":"source a"}\n']
        )
        service = NativeLegacyObjectAdmissionService(connection)
        first = _admit(service, root_a, manifest_a_path, idempotency_namespace, identity_namespace, scope)
        moved_capture = tmp_path / "moved-source-a"
        shutil.copytree(root_a.parent, moved_capture)
        moved = _admit(
            service,
            moved_capture / root_a.name,
            moved_capture / manifest_a_path.name,
            idempotency_namespace,
            identity_namespace,
            scope,
        )
        root_b, manifest_b_path, manifest_b = _snapshot(
            tmp_path, "source-b", [b'{"eid":7,"text":"source b"}\n']
        )
        second_source = _admit(
            service, root_b, manifest_b_path, idempotency_namespace, identity_namespace, scope
        )
        first_result = first.results[0]
        assert moved == first
        assert first_result.object_id != second_source.results[0].object_id
        assert service.resolve_legacy_object_alias(
            legacy_source_namespace_id=manifest_a.legacy_source_namespace_id,
            alias_kind="EID",
            alias_value="7",
        ) == first_result.object_id
        assert service.resolve_legacy_object_alias(
            legacy_source_namespace_id=manifest_b.legacy_source_namespace_id,
            alias_kind="EID",
            alias_value="7",
        ) == second_source.results[0].object_id
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases").fetchone()[0] == 2
    finally:
        qualified.close()


def test_malformed_final_eid_row_records_unknown_without_falling_back_or_creating_semantics(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(
            tmp_path,
            "malformed-source",
            [b'{"eid":5,"text":"earlier valid"}\n', b'{"eid":5,"text":\n'],
        )
        run = _admit(
            NativeLegacyObjectAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            identity_namespace,
            scope,
        )
        assert [(result.admission_status, result.raw_eid, result.line_ordinal) for result in run.results] == [
            ("UNKNOWN", 5, 2)
        ]
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases").fetchone()[0] == 0
        assert connection.execute(
            "SELECT admission_status FROM legacy_admission_records"
        ).fetchone() == ("UNKNOWN",)
    finally:
        qualified.close()


def _manual_legacy_admission(
    connection: sqlite3.Connection,
    *,
    manifest,
    idempotency_namespace,
    identity_namespace,
    scope,
    origin_kind: str = "LEGACY_ADMISSION",
    include_admission_effect: bool = True,
    include_output: bool = True,
):
    snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
    source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
    artifact_id = native_id_to_bytes(
        next(artifact.artifact_id for artifact in manifest.artifacts if artifact.observed_relative_locator == "nodes.jsonl")
    )
    batch_id = connection.execute(
        "SELECT admission_batch_id FROM legacy_admission_batches WHERE legacy_snapshot_id=?",
        (snapshot_id,),
    ).fetchone()[0]
    operation_id, transition_id, object_id, revision_id, admission_id, artifact_record_id = (
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
                f"manual-{origin_kind}-{include_admission_effect}-{include_output}",
                "ADMIT_LEGACY_NODE_CURRENT",
                "TMS-INTENT-1",
                "{}",
            ),
        )
        connection.execute(
            "INSERT INTO legacy_artifact_records VALUES (?,?,?,?)",
            (native_id_to_bytes(artifact_record_id), artifact_id, f"manual-{object_id}", "nodes.jsonl#line:manual"),
        )
        connection.execute(
            "INSERT INTO legacy_admission_records VALUES (?,?,?,'ADMITTED',NULL)",
            (native_id_to_bytes(admission_id), batch_id, native_id_to_bytes(artifact_record_id)),
        )
        connection.execute(
            "INSERT INTO objects VALUES (?,?,?,?,?,?,?)",
            (native_id_to_bytes(object_id), native_id_to_bytes(identity_namespace), "LEGACY_CORE_NODE", native_id_to_bytes(transition_id), native_id_to_bytes(revision_id), 1, 0),
        )
        connection.execute(
            """
            INSERT INTO object_revisions(
                object_revision_id,object_id,revision_ordinal,lineage_kind,
                effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,
                governance_state,authority_category,payload_format,created_at_ns
            ) VALUES (?,?,1,'LEGACY_PREDECESSOR_UNKNOWN',?,'EXISTS','UNKNOWN',0,
                      'UNKNOWN','NOT_APPLICABLE','NONE',0)
            """,
            (native_id_to_bytes(revision_id), native_id_to_bytes(object_id), native_id_to_bytes(scope)),
        )
        connection.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,'EID','manual',?)",
            (source_namespace_id, native_id_to_bytes(object_id)),
        )
        connection.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "LEGACY_OBJECT_ADMISSION", origin_kind),
        )
        connection.execute(
            "INSERT INTO object_revision_effects VALUES (?,?,?,1)",
            (native_id_to_bytes(transition_id), native_id_to_bytes(object_id), native_id_to_bytes(revision_id)),
        )
        if include_admission_effect:
            connection.execute(
                "INSERT INTO legacy_admission_effects VALUES (?,?)",
                (native_id_to_bytes(transition_id), native_id_to_bytes(admission_id)),
            )
        if include_output:
            connection.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,'OBJECT',?,?,1)",
                (native_id_to_bytes(operation_id), 0, "LEGACY_OBJECT_ADMISSION", native_id_to_bytes(object_id), native_id_to_bytes(revision_id)),
            )
        tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
        tx.transitions.append(native_id_to_bytes(transition_id))
        tx.published.append((native_id_to_bytes(object_id), native_id_to_bytes(revision_id), 1))
        tx.legacy_admitted.append(
            (
                native_id_to_bytes(object_id),
                native_id_to_bytes(revision_id),
                1,
                native_id_to_bytes(admission_id),
                native_id_to_bytes(transition_id),
                snapshot_id,
                artifact_id,
                native_id_to_bytes(artifact_record_id),
                "manual",
            )
        )
        return tx
    except Exception:
        connection.execute("ROLLBACK")
        raise


@pytest.mark.parametrize(
    ("origin_kind", "include_admission_effect", "include_output", "match"),
    [
        ("NATIVE", True, True, "H7"),
        ("LEGACY_ADMISSION", False, True, "H2 legacy admission effect"),
        ("LEGACY_ADMISSION", True, False, "H8"),
    ],
)
def test_h7_h2_and_h8_refuse_incomplete_or_masquerading_admission(
    tmp_path: Path, origin_kind: str, include_admission_effect: bool, include_output: bool, match: str
):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(
            tmp_path, "invariant-source", [b'{"eid":1,"text":"baseline"}\n']
        )
        _admit(
            NativeLegacyObjectAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            identity_namespace,
            scope,
        )
        tx = _manual_legacy_admission(
            connection,
            manifest=manifest,
            idempotency_namespace=idempotency_namespace,
            identity_namespace=identity_namespace,
            scope=scope,
            origin_kind=origin_kind,
            include_admission_effect=include_admission_effect,
            include_output=include_output,
        )
        try:
            with pytest.raises(SubstrateInvariantViolation, match=match):
                tx.validate()
        finally:
            connection.execute("ROLLBACK")
    finally:
        qualified.close()
