"""Focused Phase 7F3E synthetic deep-memory derivation admission tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.migration.deep_memory_admission import (
    LEGACY_DEEP_MEMORY_ENCODING,
    LEGACY_DEEP_MEMORY_REPRESENTATION_CLASS,
    NativeLegacyDeepMemoryAdmissionService,
)
from torment_service.substrate.objects import NativeObjectService, ObjectState, SubstrateTx
from torment_service.substrate.representations import NativeRepresentationService
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "legacy-deep-memory-admission.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    object_namespace, scope, successor_scope, idempotency_namespace = _id(), _id(), _id(), _id()
    connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(object_namespace), "legacy-deep-objects"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope), "legacy-deep-unknown-scope"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(successor_scope), "legacy-deep-successor-scope"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency_namespace), "legacy-deep-idempotency"))
    return qualified, object_namespace, scope, successor_scope, idempotency_namespace


def _node(eid: int = 1, *, exported: bool = True, exported_step: int = 50):
    payload = {"eid": eid, "text": f"synthetic source {eid}", "compression_score": 0.5}
    if exported:
        payload.update({"exported_deep": True, "exported_step": exported_step, "compression_route": "long_path"})
    return payload


def _deep_record(eid: int = 1, *, compressed_step: int = 50, **overrides):
    record = {
        "eid": eid,
        "born_step": 11,
        "compressed_step": compressed_step,
        "summary": "Captured deep summary.",
        "compression_score": 0.5000001,
        "original_motif_id": "unadmitted-motif",
        "memory_class": "core",
        "embedding_ref": {"shard": 9, "row": 4, "dim": 3},
        "metadata": {"workspace_id": "orchard", "derivation_note": "captured only"},
    }
    record.update(overrides)
    return record


def _line(record: dict) -> bytes:
    return json.dumps(record, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def _snapshot(
    tmp_path: Path,
    source_key: str,
    *,
    node_rows: list[dict] | None = None,
    deep_rows: list[bytes] | None = None,
):
    capture = tmp_path / source_key
    root = capture / "legacy-snapshot"
    root.mkdir(parents=True)
    nodes = node_rows if node_rows is not None else [_node()]
    (root / "nodes.jsonl").write_bytes(b"".join(_line(row) for row in nodes))
    deep_path = root / "workspaces" / "orchard" / "agents" / "aria" / "deep_memory" / "memories.jsonl"
    deep_path.parent.mkdir(parents=True)
    deep_path.write_bytes(b"".join(deep_rows if deep_rows is not None else [_line(_deep_record())]))
    manifest_path = capture / "snapshot-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=_id(),
        legacy_source_namespace_key=source_key,
        capture_label="synthetic 7F3E deep-memory fixture only",
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


def _admit_deep(service, root, manifest_path, idempotency_namespace):
    return service.admit_deep_memory_current_state(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
    )


def test_corroborated_deep_capture_is_exact_nonready_and_does_not_change_source_truth(tmp_path: Path):
    qualified, object_namespace, scope, successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        raw_record = _line(_deep_record())
        root, manifest_path, _ = _snapshot(tmp_path, "valid-deep-source", deep_rows=[raw_record])
        source = _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope).results[0]
        source_before = NativeObjectService(connection).get_current_object(source.object_id)
        source_revision_count = connection.execute("SELECT count(*) FROM object_revisions WHERE object_id=?", (native_id_to_bytes(source.object_id),)).fetchone()[0]
        source_transition_count = connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0]
        service = NativeLegacyDeepMemoryAdmissionService(connection)
        first = _admit_deep(service, root, manifest_path, idempotency_namespace)
        retry = _admit_deep(service, root, manifest_path, idempotency_namespace)
        assert retry == first
        result = first.results[0]
        assert result.admission_status == "ADMITTED"
        assert result.representation_id and result.transition_id
        assert result.source_object_id == source.object_id
        assert result.source_revision_id == source.revision_id
        metadata = service.get_admitted_deep_memory_metadata(result.representation_id)
        assert (metadata.representation_class, metadata.generation, metadata.readiness, metadata.disposition) == (
            LEGACY_DEEP_MEMORY_REPRESENTATION_CLASS, 1, "UNKNOWN", "RECONCILIATION_REQUIRED"
        )
        traced: list[str] = []
        connection.set_trace_callback(traced.append)
        assert service.get_admitted_deep_memory_metadata(result.representation_id) == metadata
        connection.set_trace_callback(None)
        assert not any("representation_payloads" in statement.lower() for statement in traced)
        assert service.read_admitted_deep_memory_payload(result.representation_id) == raw_record
        with pytest.raises(SubstrateObjectNotFound):
            NativeRepresentationService(connection).read_representation_payload(result.representation_id)
        assert connection.execute("SELECT count(*) FROM integrity_expectations WHERE representation_id=?", (native_id_to_bytes(result.representation_id),)).fetchone()[0] == 0
        admission_metadata = json.loads(connection.execute("SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?", (native_id_to_bytes(result.admission_record_id),)).fetchone()[0])
        assert admission_metadata["deep_record"]["summary"] == "Captured deep summary."
        assert admission_metadata["deep_record"]["metadata"] == {"derivation_note": "captured only", "workspace_id": "orchard"}
        assert admission_metadata["optional_deep_embedding"] == "REFERENCE_PRESERVED_ADMISSION_DEFERRED"
        assert admission_metadata["original_motif_linkage"] == {"original_motif_id": "unadmitted-motif", "status": "UNRESOLVED_PRESERVED"}
        assert admission_metadata["semantic_integrity_expectation"] == "NOT_ESTABLISHED_FROM_CAPTURED_BYTES"
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 1
        assert NativeObjectService(connection).get_current_object(source.object_id) == source_before
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE object_id=?", (native_id_to_bytes(source.object_id),)).fetchone()[0] == source_revision_count
        assert connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == source_transition_count + 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE representations SET generation=2 WHERE representation_id=?", (native_id_to_bytes(result.representation_id),))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE representation_payloads SET payload_bytes=? WHERE representation_id=?", (b"rewrite", native_id_to_bytes(result.representation_id)))
        successor = NativeObjectService(connection).transition_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="synthetic-deep-source-successor",
            object_id=source.object_id,
            expected_revision_id=source.revision_id,
            state=ObjectState(object_namespace, successor_scope, "LEGACY_CORE_NODE", "EXISTS", "UNKNOWN", False, "UNKNOWN"),
        )
        assert successor.revision_id != source.revision_id
        assert connection.execute("SELECT source_object_id,source_object_revision_id FROM representations WHERE representation_id=?", (native_id_to_bytes(result.representation_id),)).fetchone() == (native_id_to_bytes(source.object_id), native_id_to_bytes(source.revision_id))
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("source_key", "node_rows", "deep_rows", "reason"),
    [
        ("uncorroborated-deep-source", [_node(exported=False)], [_line(_deep_record())], "does not corroborate"),
        ("step-mismatch-deep-source", [_node(exported_step=51)], [_line(_deep_record(compressed_step=50))], "does not corroborate"),
        ("unresolved-deep-source", [_node(eid=1)], [_line(_deep_record(eid=999))], "does not resolve"),
    ],
)
def test_uncorroborated_mismatched_or_unresolved_deep_residue_is_quarantined(tmp_path: Path, source_key, node_rows, deep_rows, reason):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, source_key, node_rows=node_rows, deep_rows=deep_rows)
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        result = _admit_deep(NativeLegacyDeepMemoryAdmissionService(connection), root, manifest_path, idempotency_namespace).results[0]
        assert result.admission_status == "QUARANTINED"
        assert result.representation_id is None
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == len(node_rows)
        assert reason in json.loads(connection.execute("SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?", (native_id_to_bytes(result.admission_record_id),)).fetchone()[0])["reason"]
    finally:
        qualified.close()


def test_latest_loader_valid_row_is_selected_while_earlier_and_malformed_rows_remain_evidence(tmp_path: Path):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        earlier = _line(_deep_record(compressed_step=40, summary="Earlier deep summary."))
        latest = _line(_deep_record(compressed_step=50, summary="Latest deep summary."))
        malformed = b'{"eid":1,"compressed_step":\n'
        root, manifest_path, _ = _snapshot(tmp_path, "latest-deep-source", deep_rows=[earlier, latest, malformed])
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        run = _admit_deep(NativeLegacyDeepMemoryAdmissionService(connection), root, manifest_path, idempotency_namespace)
        admitted = next(item for item in run.results if item.admission_status == "ADMITTED")
        malformed_result = next(item for item in run.results if item.admission_status == "UNKNOWN")
        assert admitted.line_ordinal == 2
        assert malformed_result.line_ordinal == 3
        assert NativeLegacyDeepMemoryAdmissionService(connection).read_admitted_deep_memory_payload(admitted.representation_id) == latest
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM legacy_artifact_records ar JOIN legacy_artifacts a USING(legacy_artifact_id) WHERE a.observed_locator LIKE '%deep_memory/memories.jsonl'"
        ).fetchone()[0] == 2
    finally:
        qualified.close()


def test_moved_snapshot_retry_reuses_same_deep_representation(tmp_path: Path):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, "movable-deep-source")
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        service = NativeLegacyDeepMemoryAdmissionService(connection)
        first = _admit_deep(service, root, manifest_path, idempotency_namespace)
        moved_capture = tmp_path / "moved-capture"
        shutil.copytree(root.parent, moved_capture)
        moved = _admit_deep(service, moved_capture / root.name, moved_capture / manifest_path.name, idempotency_namespace)
        assert moved == first
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 1
    finally:
        qualified.close()


def _manual_deep_admission(
    connection: sqlite3.Connection,
    *,
    manifest,
    source,
    baseline,
    idempotency_namespace,
    origin_kind: str = "LEGACY_ADMISSION",
    include_state_effect: bool = True,
    include_admission_effect: bool = True,
    mismatch_output: bool = False,
):
    snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
    artifact_id = native_id_to_bytes(next(item.artifact_id for item in manifest.artifacts if item.observed_relative_locator.endswith("/memories.jsonl")))
    batch_id = connection.execute("SELECT admission_batch_id FROM legacy_admission_batches WHERE legacy_snapshot_id=? AND batch_identity='TMS-LEGACY-DEEP-MEMORY-ADMISSION-7F3E'", (snapshot_id,)).fetchone()[0]
    operation_id, transition_id, representation_id, admission_id, artifact_record_id = _id(), _id(), _id(), _id(), _id()
    source_ordinal = connection.execute("SELECT revision_ordinal FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(source.revision_id),)).fetchone()[0]
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("INSERT INTO operations VALUES (?,?,?,?,?,?,0)", (native_id_to_bytes(operation_id), native_id_to_bytes(idempotency_namespace), f"manual-deep-{origin_kind}-{include_state_effect}-{include_admission_effect}-{mismatch_output}", "ADMIT_LEGACY_DEEP_MEMORY_CURRENT", "TMS-INTENT-1", "{}"))
        connection.execute("INSERT INTO legacy_artifact_records VALUES (?,?,?,?)", (native_id_to_bytes(artifact_record_id), artifact_id, f"manual-{representation_id}", "deep_memory/memories.jsonl#line:manual"))
        connection.execute("INSERT INTO legacy_admission_records VALUES (?,?,?,'ADMITTED',NULL)", (native_id_to_bytes(admission_id), batch_id, native_id_to_bytes(artifact_record_id)))
        connection.execute("""INSERT INTO representations(representation_id,source_kind,source_object_id,source_object_revision_id,source_object_revision_ordinal,representation_class,generation,derivation_contract_version,encoding_id,dtype,dimension,expected_payload_byte_length,created_at_ns) VALUES (?,'OBJECT_REVISION',?,?,?,?,?,?,?,?,?,?,?)""", (native_id_to_bytes(representation_id), native_id_to_bytes(source.object_id), native_id_to_bytes(source.revision_id), source_ordinal, LEGACY_DEEP_MEMORY_REPRESENTATION_CLASS, 1, "LEGACY_UNSPECIFIED", LEGACY_DEEP_MEMORY_ENCODING, None, None, 6, 0))
        connection.execute("INSERT INTO representation_current_state VALUES (?,'UNKNOWN','RECONCILIATION_REQUIRED',NULL)", (native_id_to_bytes(representation_id),))
        connection.execute("INSERT INTO representation_payloads VALUES (?,?,6,0)", (native_id_to_bytes(representation_id), b"manual"))
        connection.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)", (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "LEGACY_DEEP_MEMORY_ADMISSION", origin_kind))
        if include_state_effect:
            connection.execute("INSERT INTO representation_state_effects VALUES (?,?,?, ?,NULL)", (native_id_to_bytes(transition_id), native_id_to_bytes(representation_id), "UNKNOWN", "RECONCILIATION_REQUIRED"))
        if include_admission_effect:
            connection.execute("INSERT INTO legacy_admission_effects VALUES (?,?)", (native_id_to_bytes(transition_id), native_id_to_bytes(admission_id)))
        output_representation = baseline.representation_id if mismatch_output else representation_id
        connection.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,representation_id) VALUES (?,?,?,'REPRESENTATION',?)", (native_id_to_bytes(operation_id), 0, "LEGACY_DEEP_MEMORY_ADMISSION", native_id_to_bytes(output_representation)))
        tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
        tx.transitions.append(native_id_to_bytes(transition_id))
        tx.legacy_deep_memory_admitted.append((native_id_to_bytes(representation_id), native_id_to_bytes(admission_id), native_id_to_bytes(transition_id), snapshot_id, artifact_id, native_id_to_bytes(artifact_record_id), native_id_to_bytes(source.object_id), native_id_to_bytes(source.revision_id), source_ordinal, "1", 50, 6))
        return tx
    except Exception:
        connection.execute("ROLLBACK")
        raise


@pytest.mark.parametrize(
    ("origin_kind", "include_state_effect", "include_admission_effect", "mismatch_output", "match"),
    [
        ("NATIVE", True, True, False, "H7"),
        ("LEGACY_ADMISSION", False, True, False, "H2 legacy deep representation state effect"),
        ("LEGACY_ADMISSION", True, False, False, "H2 legacy deep admission effect"),
        ("LEGACY_ADMISSION", True, True, True, "H8"),
    ],
)
def test_h7_h2_and_h8_refuse_incomplete_or_masquerading_deep_admission(tmp_path: Path, origin_kind, include_state_effect, include_admission_effect, mismatch_output, match):
    qualified, object_namespace, scope, _successor_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(
            tmp_path,
            "deep-invariant-source",
            node_rows=[_node(1), _node(2)],
            deep_rows=[_line(_deep_record(eid=2))],
        )
        sources = _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope).results
        source = next(item for item in sources if item.raw_eid == 1)
        baseline = _admit_deep(NativeLegacyDeepMemoryAdmissionService(connection), root, manifest_path, idempotency_namespace).results[0]
        representation_count = connection.execute("SELECT count(*) FROM representations").fetchone()[0]
        tx = _manual_deep_admission(connection, manifest=manifest, source=source, baseline=baseline, idempotency_namespace=idempotency_namespace, origin_kind=origin_kind, include_state_effect=include_state_effect, include_admission_effect=include_admission_effect, mismatch_output=mismatch_output)
        try:
            with pytest.raises(SubstrateInvariantViolation, match=match):
                tx.validate()
        finally:
            connection.execute("ROLLBACK")
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == representation_count
    finally:
        qualified.close()
