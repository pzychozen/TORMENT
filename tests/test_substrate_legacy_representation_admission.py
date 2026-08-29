"""Focused Phase 7F3B synthetic legacy embedding-admission tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3

import numpy as np
import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import (
    SubstrateEvidenceIntegrityMismatch,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.migration.representation_admission import (
    LEGACY_EMBEDDING_REPRESENTATION_CLASS,
    LEGACY_UNSPECIFIED_DERIVATION_CONTRACT,
    NativeLegacyRepresentationAdmissionService,
)
from torment_service.substrate.objects import NativeObjectService, ObjectState, SubstrateTx
from torment_service.substrate.representations import NativeRepresentationService
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "legacy-representation-admission.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    object_namespace, scope, successor_scope, idempotency_namespace = _id(), _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(object_namespace), "legacy-representation-objects"),
    )
    for value, key in ((scope, "legacy-representation-scope"), (successor_scope, "legacy-representation-successor-scope")):
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key)
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "legacy-representation-idempotency"),
    )
    return qualified, object_namespace, scope, successor_scope, idempotency_namespace


def _reference(eid: int, *, row: int = 0, dimension: int = 3, dtype: str = "float32") -> dict[str, object]:
    return {
        "eid": eid,
        "embedding_ref": {
            "map": "embeddings/shard_000000.map.jsonl",
            "shard": "embeddings/shard_000000.npy",
            "row": row,
            "dimension": dimension,
            "dtype": dtype,
        },
    }


def _json_line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode("utf-8") + b"\n"


def _snapshot(
    tmp_path: Path,
    source_key: str,
    *,
    nodes: list[dict[str, object]] | None = None,
    map_rows: list[dict[str, object]] | None = None,
    vectors: np.ndarray | None = None,
    include_map: bool = True,
    manifest_overrides: dict[str, object] | None = None,
):
    capture = tmp_path / source_key
    root = capture / "legacy-snapshot"
    embeddings = root / "embeddings"
    embeddings.mkdir(parents=True)
    nodes = nodes or [_reference(1), {"eid": 2, "text": "no vector reference"}]
    (root / "nodes.jsonl").write_bytes(b"".join(_json_line(node) for node in nodes))
    (root / "edges.jsonl").write_bytes(b'{"source":1,"target":2}\n')
    (root / "memory_events.jsonl").write_bytes(b'{"event":"MEMORY_CREATE","eid":999}\n')
    vectors = vectors if vectors is not None else np.array([[1.25, -2.0, 3.5], [4.0, 5.0, 6.0]], dtype=np.float32)
    np.save(embeddings / "shard_000000.npy", vectors)
    if include_map:
        map_rows = map_rows if map_rows is not None else [
            {"eid": 1, "shard": "embeddings/shard_000000.npy", "row": 0, "dimension": 3}
        ]
        (embeddings / "shard_000000.map.jsonl").write_bytes(
            b"".join(_json_line(row) for row in map_rows)
        )
    manifest = {
        "encoding_id": "NUMPY_NPY",
        "dtype": "float32",
        "dimension": 3,
        "derivation_contract_version": "legacy-embed-v1",
        "provider": "synthetic-provider",
        "model": "synthetic-model",
        "shards": [
            {"path": "embeddings/shard_000000.npy", "map": "embeddings/shard_000000.map.jsonl"}
        ],
    }
    if manifest_overrides:
        manifest.update(manifest_overrides)
    (embeddings / "manifest.json").write_bytes(_json_line(manifest))
    manifest_path = capture / "snapshot-manifest.json"
    frozen = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=_id(),
        legacy_source_namespace_key=source_key,
        capture_label="synthetic 7F3B representation fixture only",
    )
    return root, manifest_path, frozen, vectors


def _admit_nodes(service, root, manifest_path, idempotency_namespace, object_namespace, scope):
    return service.admit_nodes_current_state(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
        object_identity_namespace_id=object_namespace,
        unknown_semantic_scope_id=scope,
    )


def _admit_vectors(service, root, manifest_path, idempotency_namespace):
    return service.admit_embedding_evidence(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
    )


def test_valid_vector_admission_preserves_exact_bytes_and_stays_unverified(tmp_path: Path):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest, vectors = _snapshot(tmp_path, "valid-source")
        nodes = _admit_nodes(
            NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope
        )
        source = next(result for result in nodes.results if result.raw_eid == 1)
        source_before = NativeObjectService(connection).get_current_object(source.object_id)
        source_revision_count = connection.execute("SELECT count(*) FROM object_revisions WHERE object_id=?", (native_id_to_bytes(source.object_id),)).fetchone()[0]
        service = NativeLegacyRepresentationAdmissionService(connection)
        first = _admit_vectors(service, root, manifest_path, idempotency_namespace)
        retry = _admit_vectors(service, root, manifest_path, idempotency_namespace)
        result = first.results[0]
        assert retry == first
        assert result.admission_status == "ADMITTED"
        assert (result.source_object_id, result.source_revision_id) == (source.object_id, source.revision_id)
        metadata = service.get_admitted_representation_metadata(result.representation_id)
        assert (metadata.representation_class, metadata.generation, metadata.readiness, metadata.disposition) == (
            LEGACY_EMBEDDING_REPRESENTATION_CLASS,
            1,
            "UNKNOWN",
            "RECONCILIATION_REQUIRED",
        )
        traced: list[str] = []
        connection.set_trace_callback(traced.append)
        assert service.get_admitted_representation_metadata(result.representation_id) == metadata
        connection.set_trace_callback(None)
        assert not any("representation_payloads" in statement.lower() for statement in traced)
        expected = bytes(vectors[0].tobytes(order="C"))
        assert service.read_admitted_representation_payload(result.representation_id) == expected
        with pytest.raises(SubstrateObjectNotFound):
            NativeRepresentationService(connection).read_representation_payload(result.representation_id)
        assert connection.execute(
            "SELECT count(*) FROM integrity_expectations WHERE representation_id=?",
            (native_id_to_bytes(result.representation_id),),
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT transition_kind,origin_kind FROM semantic_transitions WHERE transition_id=?",
            (native_id_to_bytes(result.transition_id),),
        ).fetchone() == ("LEGACY_REPRESENTATION_ADMISSION", "LEGACY_ADMISSION")
        metadata_json = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?",
            (native_id_to_bytes(result.admission_record_id),),
        ).fetchone()[0])
        assert metadata_json["legacy_derivation_metadata"] == {"model": "synthetic-model", "provider": "synthetic-provider"}
        assert metadata_json["semantic_integrity_expectation"] == "NOT_ESTABLISHED_FROM_CAPTURED_BYTES"
        assert NativeObjectService(connection).get_current_object(source.object_id) == source_before
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE object_id=?", (native_id_to_bytes(source.object_id),)).fetchone()[0] == source_revision_count
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM representation_dependencies").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM relationship_revisions").fetchone()[0] == 0
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE representations SET generation=2 WHERE representation_id=?", (native_id_to_bytes(result.representation_id),))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE representation_payloads SET payload_bytes=? WHERE representation_id=?", (b"rewrite", native_id_to_bytes(result.representation_id)))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE legacy_admission_records SET admission_status='UNKNOWN' WHERE admission_record_id=?", (native_id_to_bytes(result.admission_record_id),))
    finally:
        qualified.close()


def test_unknown_derivation_metadata_is_not_fabricated_and_source_binding_survives_successor(tmp_path: Path):
    qualified, object_namespace, scope, successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest, _vectors = _snapshot(
            tmp_path,
            "unknown-metadata-source",
            manifest_overrides={
                "derivation_contract_version": LEGACY_UNSPECIFIED_DERIVATION_CONTRACT,
                "provider": None,
                "model": None,
            },
        )
        node_run = _admit_nodes(
            NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope
        )
        source = next(result for result in node_run.results if result.raw_eid == 1)
        result = _admit_vectors(NativeLegacyRepresentationAdmissionService(connection), root, manifest_path, idempotency_namespace).results[0]
        metadata_json = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?", (native_id_to_bytes(result.admission_record_id),)
        ).fetchone()[0])
        assert metadata_json["derivation_contract_version"] == LEGACY_UNSPECIFIED_DERIVATION_CONTRACT
        assert metadata_json["legacy_derivation_metadata"] == {}
        successor = NativeObjectService(connection).transition_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="synthetic-source-successor",
            object_id=source.object_id,
            expected_revision_id=source.revision_id,
            state=ObjectState(object_namespace, successor_scope, "LEGACY_CORE_NODE", "EXISTS", "UNKNOWN", False, "UNKNOWN"),
        )
        assert successor.revision_id != source.revision_id
        assert connection.execute(
            "SELECT source_object_id,source_object_revision_id FROM representations WHERE representation_id=?",
            (native_id_to_bytes(result.representation_id),),
        ).fetchone() == (native_id_to_bytes(source.object_id), native_id_to_bytes(source.revision_id))
    finally:
        qualified.close()


def test_moved_snapshot_retry_reuses_the_same_representation_operation_and_payload(tmp_path: Path):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest, _vectors = _snapshot(tmp_path, "movable-vector-source")
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        service = NativeLegacyRepresentationAdmissionService(connection)
        first = _admit_vectors(service, root, manifest_path, idempotency_namespace)
        moved_capture = tmp_path / "moved-capture"
        shutil.copytree(root.parent, moved_capture)
        moved = _admit_vectors(service, moved_capture / root.name, moved_capture / manifest_path.name, idempotency_namespace)
        assert moved == first
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 1
    finally:
        qualified.close()


def test_missing_map_is_quarantined_without_placeholder_representation(tmp_path: Path):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest, _vectors = _snapshot(tmp_path, "missing-map-source", include_map=False)
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        result = _admit_vectors(NativeLegacyRepresentationAdmissionService(connection), root, manifest_path, idempotency_namespace).results[0]
        assert result.admission_status == "QUARANTINED"
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_quarantine_records").fetchone()[0] == 1
    finally:
        qualified.close()


def test_unadmitted_source_eid_is_quarantined_without_creating_an_object_from_vector_evidence(tmp_path: Path):
    qualified, _object_namespace, _scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest, _vectors = _snapshot(tmp_path, "unadmitted-source-eid")
        result = _admit_vectors(
            NativeLegacyRepresentationAdmissionService(connection), root, manifest_path, idempotency_namespace
        ).results[0]
        assert result.admission_status == "QUARANTINED"
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("source_key", "nodes", "map_rows", "vectors", "expected_reason"),
    [
        (
            "eid-mismatch-source",
            [_reference(1)],
            [{"eid": 9, "shard": "embeddings/shard_000000.npy", "row": 0, "dimension": 3}],
            np.array([[1.0, 2.0, 3.0]], dtype=np.float32),
            "map",
        ),
        (
            "row-out-of-range-source",
            [_reference(1, row=5)],
            [{"eid": 1, "shard": "embeddings/shard_000000.npy", "row": 5, "dimension": 3}],
            np.array([[1.0, 2.0, 3.0]], dtype=np.float32),
            "outside",
        ),
        (
            "dimension-mismatch-source",
            [_reference(1, dimension=3)],
            [{"eid": 1, "shard": "embeddings/shard_000000.npy", "row": 0, "dimension": 3}],
            np.array([[1.0, 2.0]], dtype=np.float32),
            "dimension",
        ),
    ],
)
def test_eid_row_and_dimension_mismatches_are_quarantined_without_rewriting(
    tmp_path: Path, source_key, nodes, map_rows, vectors, expected_reason
):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest, _vectors = _snapshot(
            tmp_path, source_key, nodes=nodes, map_rows=map_rows, vectors=vectors
        )
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        result = _admit_vectors(NativeLegacyRepresentationAdmissionService(connection), root, manifest_path, idempotency_namespace).results[0]
        assert result.admission_status == "QUARANTINED"
        reason = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?", (native_id_to_bytes(result.admission_record_id),)
        ).fetchone()[0])["reason"]
        assert expected_reason in reason
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
    finally:
        qualified.close()


def test_conflicting_map_is_not_selected_by_append_order(tmp_path: Path):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest, _vectors = _snapshot(
            tmp_path,
            "conflicting-map-source",
            map_rows=[
                {"eid": 1, "shard": "embeddings/shard_000000.npy", "row": 0, "dimension": 3},
                {"eid": 1, "shard": "embeddings/shard_000000.npy", "row": 1, "dimension": 3},
            ],
        )
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        result = _admit_vectors(NativeLegacyRepresentationAdmissionService(connection), root, manifest_path, idempotency_namespace).results[0]
        assert result.admission_status == "QUARANTINED"
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
    finally:
        qualified.close()


def test_artifact_digest_mutation_blocks_admission_before_semantic_publication(tmp_path: Path):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _manifest, _vectors = _snapshot(tmp_path, "digest-failure-source")
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        (root / "embeddings" / "shard_000000.map.jsonl").write_bytes(b'{"tampered":true}\n')
        with pytest.raises(SubstrateEvidenceIntegrityMismatch):
            _admit_vectors(NativeLegacyRepresentationAdmissionService(connection), root, manifest_path, idempotency_namespace)
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
    finally:
        qualified.close()


def _manual_representation_admission(
    connection,
    *,
    manifest,
    idempotency_namespace,
    source_result,
    baseline_result,
    origin_kind: str = "LEGACY_ADMISSION",
    include_state_effect: bool = True,
    include_admission_effect: bool = True,
    include_output: bool = True,
    mismatch_output: bool = False,
):
    snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
    source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
    artifacts = {artifact.observed_relative_locator: artifact for artifact in manifest.artifacts}
    node_artifact, map_artifact, shard_artifact = (
        artifacts["nodes.jsonl"],
        artifacts["embeddings/shard_000000.map.jsonl"],
        artifacts["embeddings/shard_000000.npy"],
    )
    batch_id = connection.execute(
        "SELECT admission_batch_id FROM legacy_admission_batches WHERE legacy_snapshot_id=? AND batch_identity='TMS-LEGACY-REPRESENTATION-ADMISSION-7F3B'",
        (snapshot_id,),
    ).fetchone()[0]
    operation_id, transition_id, representation_id, admission_id, artifact_record_id = _id(), _id(), _id(), _id(), _id()
    source_ordinal = connection.execute("SELECT revision_ordinal FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(source_result.revision_id),)).fetchone()[0]
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
                (native_id_to_bytes(operation_id), native_id_to_bytes(idempotency_namespace), f"manual-representation-{origin_kind}-{include_state_effect}-{include_admission_effect}-{include_output}-{mismatch_output}", "ADMIT_LEGACY_EMBEDDING_EVIDENCE", "TMS-INTENT-1", "{}"),
        )
        connection.execute("INSERT INTO legacy_artifact_records VALUES (?,?,?,?)", (native_id_to_bytes(artifact_record_id), native_id_to_bytes(map_artifact.artifact_id), f"manual-{representation_id}", "embedding.map.jsonl#line:manual"))
        connection.execute("INSERT INTO legacy_admission_records VALUES (?,?,?,'ADMITTED',NULL)", (native_id_to_bytes(admission_id), batch_id, native_id_to_bytes(artifact_record_id)))
        connection.execute(
            """
            INSERT INTO representations(
                representation_id,source_kind,source_object_id,source_object_revision_id,source_object_revision_ordinal,
                representation_class,generation,derivation_contract_version,encoding_id,dtype,dimension,expected_payload_byte_length,created_at_ns
            ) VALUES (?,'OBJECT_REVISION',?,?,?,?,?,?,?,?,?,?,?)
            """,
            (native_id_to_bytes(representation_id), native_id_to_bytes(source_result.object_id), native_id_to_bytes(source_result.revision_id), source_ordinal, LEGACY_EMBEDDING_REPRESENTATION_CLASS, 1, LEGACY_UNSPECIFIED_DERIVATION_CONTRACT, "NUMPY_NPY", "float32", 3, 6, 0),
        )
        connection.execute("INSERT INTO representation_current_state VALUES (?,'UNKNOWN','RECONCILIATION_REQUIRED',NULL)", (native_id_to_bytes(representation_id),))
        connection.execute("INSERT INTO representation_payloads VALUES (?,?,6,0)", (native_id_to_bytes(representation_id), b"manual"))
        connection.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)", (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "LEGACY_REPRESENTATION_ADMISSION", origin_kind))
        if include_state_effect:
            connection.execute("INSERT INTO representation_state_effects VALUES (?,?,?, ?,NULL)", (native_id_to_bytes(transition_id), native_id_to_bytes(representation_id), "UNKNOWN", "RECONCILIATION_REQUIRED"))
        if include_admission_effect:
            connection.execute("INSERT INTO legacy_admission_effects VALUES (?,?)", (native_id_to_bytes(transition_id), native_id_to_bytes(admission_id)))
        if include_output:
            output_representation_id = baseline_result.representation_id if mismatch_output else representation_id
            connection.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,representation_id) VALUES (?,?,?,'REPRESENTATION',?)", (native_id_to_bytes(operation_id), 0, "LEGACY_REPRESENTATION_ADMISSION", native_id_to_bytes(output_representation_id)))
        tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
        tx.transitions.append(native_id_to_bytes(transition_id))
        if include_state_effect:
            tx.representation_published.append(native_id_to_bytes(representation_id))
        tx.legacy_representation_admitted.append(
            (
                native_id_to_bytes(representation_id), native_id_to_bytes(admission_id), native_id_to_bytes(transition_id), snapshot_id,
                native_id_to_bytes(node_artifact.artifact_id), native_id_to_bytes(map_artifact.artifact_id), native_id_to_bytes(shard_artifact.artifact_id), native_id_to_bytes(artifact_record_id),
                native_id_to_bytes(source_result.object_id), native_id_to_bytes(source_result.revision_id), source_ordinal, "2", 6,
            )
        )
        return tx
    except Exception:
        connection.execute("ROLLBACK")
        raise


@pytest.mark.parametrize(
    ("origin_kind", "include_state_effect", "include_admission_effect", "include_output", "mismatch_output", "match"),
    [
        ("NATIVE", True, True, True, False, "H7"),
        ("LEGACY_ADMISSION", False, True, True, False, "H2 legacy representation state effect"),
        ("LEGACY_ADMISSION", True, False, True, False, "H2 legacy representation admission effect"),
        ("LEGACY_ADMISSION", True, True, False, False, "H8 representation output"),
        ("LEGACY_ADMISSION", True, True, True, True, "H8 representation output"),
    ],
)
def test_h7_h2_and_h8_refuse_incomplete_or_masquerading_representation_admission(
    tmp_path: Path, origin_kind: str, include_state_effect: bool, include_admission_effect: bool, include_output: bool, mismatch_output: bool, match: str
):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest, _vectors = _snapshot(tmp_path, "invariant-vector-source")
        node_run = _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        source = next(result for result in node_run.results if result.raw_eid == 2)
        baseline = _admit_vectors(NativeLegacyRepresentationAdmissionService(connection), root, manifest_path, idempotency_namespace).results[0]
        tx = _manual_representation_admission(
            connection,
            manifest=manifest,
            idempotency_namespace=idempotency_namespace,
            source_result=source,
            baseline_result=baseline,
            origin_kind=origin_kind,
            include_state_effect=include_state_effect,
            include_admission_effect=include_admission_effect,
            include_output=include_output,
            mismatch_output=mismatch_output,
        )
        try:
            with pytest.raises(SubstrateInvariantViolation, match=match):
                tx.validate()
        finally:
            connection.execute("ROLLBACK")
    finally:
        qualified.close()
