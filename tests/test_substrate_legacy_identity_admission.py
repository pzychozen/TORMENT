"""Focused Phase 7F3C synthetic identity/character-definition admission tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.migration.identity_admission import (
    LEGACY_AGENT_IDENTITY_OBJECT_KIND,
    LEGACY_CHARACTER_DEFINITION_OBJECT_KIND,
    LEGACY_CHARACTER_SEED_ALIAS_KIND,
    LEGACY_IDENTITY_ALIAS_KIND,
    NativeLegacyIdentityAdmissionService,
)
from torment_service.substrate.objects import NativeObjectService, SubstrateTx
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "legacy-identity-admission.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity_namespace, scope, idempotency_namespace = _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity_namespace), "legacy-identity-admission-objects"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), "legacy-identity-admission-unknown-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "legacy-identity-admission-idempotency"),
    )
    return qualified, identity_namespace, scope, idempotency_namespace


def _identity_payload(*, workspace_id: str = "orchard", agent_id: str = "aria") -> dict[str, object]:
    return {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "seed": {"core_traits": ["analytical"], "seed_id": "aria-v1"},
        "overlay": {"write_threshold": 0.45},
        "created_ts": 101,
        "updated_ts": 102,
    }


def _seed_payload(*, seed_id: str = "aria-v1") -> dict[str, object]:
    return {
        "seed_id": seed_id,
        "character_name": "Aria",
        "seed_text": "A concise synthetic character definition.",
        "seed_eids": [999],
        "owner_agent_id": "aria",
        "version": "1.0.0",
        "created_ts": 103,
    }


def _snapshot(
    tmp_path: Path,
    source_key: str,
    *,
    identity_bytes: bytes | None = None,
    seed_bytes: bytes | None = None,
    include_state: bool = True,
    include_nodes: bool = False,
):
    capture = tmp_path / source_key
    root = capture / "legacy-snapshot"
    identity_path = root / "workspaces" / "orchard" / "agents" / "aria" / "identity.json"
    identity_path.parent.mkdir(parents=True)
    identity_path.write_bytes(
        identity_bytes
        if identity_bytes is not None
        else (json.dumps(_identity_payload(), sort_keys=True) + "\n").encode("utf-8")
    )
    seed_path = root / "workspaces" / "orchard" / "seeds" / "aria-v1" / "seed.json"
    seed_path.parent.mkdir(parents=True)
    seed_path.write_bytes(
        seed_bytes
        if seed_bytes is not None
        else (json.dumps(_seed_payload(), sort_keys=True) + "\n").encode("utf-8")
    )
    if include_state:
        state_path = root / "workspaces" / "orchard" / "agents" / "aria" / "character_state.json"
        state_path.write_text(
            json.dumps(
                {
                    "workspace_id": "orchard",
                    "agent_id": "aria",
                    "seed_id": "aria-v1",
                    "drift_score": 0.4,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    if include_nodes:
        (root / "nodes.jsonl").write_bytes(b'{"eid":7,"text":"unrelated synthetic memory evidence"}\n')
    manifest_path = capture / "snapshot-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=_id(),
        legacy_source_namespace_key=source_key,
        capture_label="synthetic 7F3C identity definition fixture only",
    )
    return root, manifest_path, manifest


def _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope):
    return service.admit_identity_definitions(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
        object_identity_namespace_id=identity_namespace,
        unknown_semantic_scope_id=scope,
    )


def test_identity_only_snapshot_is_memory_optional_typed_and_idempotent(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(tmp_path, "identity-only-source")
        service = NativeLegacyIdentityAdmissionService(connection)
        first = _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope)
        # A caller can lose the first response: immutable evidence returns the same durable result.
        retry = _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope)
        assert retry == first
        assert [(item.definition_kind, item.admission_status) for item in first.results] == [
            ("IDENTITY", "ADMITTED"),
            ("CHARACTER_DEFINITION", "ADMITTED"),
        ]
        identity, seed = first.results
        assert identity.object_id and identity.revision_id and identity.transition_id
        assert seed.object_id and seed.revision_id and seed.transition_id
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM relationship_revisions").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases WHERE alias_kind='EID'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases WHERE alias_value='999'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_admission_records").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM legacy_admission_effects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM operation_outputs").fetchone()[0] == 2
        assert connection.execute(
            "SELECT count(*) FROM objects WHERE object_kind='LEGACY_CHARACTER_STATE'"
        ).fetchone()[0] == 0
        identity_view = NativeObjectService(connection).get_current_object(identity.object_id)
        seed_view = NativeObjectService(connection).get_current_object(seed.object_id)
        assert identity_view == NativeObjectService(connection).get_object_revision(identity.revision_id)
        assert seed_view == NativeObjectService(connection).get_object_revision(seed.revision_id)
        assert json.loads(identity_view.payload) == _identity_payload()
        assert json.loads(seed_view.payload) == _seed_payload()
        assert connection.execute(
            """
            SELECT object_kind,lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,
                   authority_category,provenance_id,payload_format
            FROM objects JOIN object_revisions USING(object_id)
            WHERE object_revision_id=?
            """,
            (native_id_to_bytes(identity.revision_id),),
        ).fetchone() == (
            LEGACY_AGENT_IDENTITY_OBJECT_KIND,
            "LEGACY_PREDECESSOR_UNKNOWN",
            None,
            None,
            "NOT_APPLICABLE",
            None,
            "JSON",
        )
        identity_alias = json.dumps({"agent_id": "aria", "workspace_id": "orchard"}, separators=(",", ":"), sort_keys=True)
        assert service.resolve_legacy_identity_alias(
            legacy_source_namespace_id=manifest.legacy_source_namespace_id,
            alias_kind=LEGACY_IDENTITY_ALIAS_KIND,
            alias_value=identity_alias,
        ) == identity.object_id
        assert service.resolve_legacy_identity_alias(
            legacy_source_namespace_id=manifest.legacy_source_namespace_id,
            alias_kind=LEGACY_CHARACTER_SEED_ALIAS_KIND,
            alias_value="aria-v1",
        ) == seed.object_id
        metadata = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?",
            (native_id_to_bytes(identity.admission_record_id),),
        ).fetchone()[0])
        assert metadata == {
            "authority_category": "NOT_APPLICABLE",
            "definition_kind": "IDENTITY",
            "memory_dependency": "NONE",
            "original_provenance": "UNKNOWN",
            "payload_role": "FLEXIBLE_CHARACTER_DEFINITION_CONTENT",
        }
        assert connection.execute(
            "SELECT transition_kind,origin_kind FROM semantic_transitions WHERE transition_id=?",
            (native_id_to_bytes(seed.transition_id),),
        ).fetchone() == ("LEGACY_IDENTITY_ADMISSION", "LEGACY_ADMISSION")
        classes = dict(connection.execute("SELECT observed_locator,artifact_kind FROM legacy_artifacts"))
        assert classes["workspaces/orchard/agents/aria/character_state.json"] == "LEGACY_IDENTITY_CHARACTER_EVIDENCE"
        assert connection.execute(
            "SELECT count(*) FROM legacy_admission_records r JOIN legacy_artifact_records ar USING(legacy_artifact_record_id) WHERE ar.observed_locator LIKE '%character_state.json'"
        ).fetchone()[0] == 0
    finally:
        qualified.close()


def test_moved_identity_snapshot_retry_reuses_all_admitted_definition_outputs(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, "movable-identity-source")
        service = NativeLegacyIdentityAdmissionService(connection)
        first = _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope)
        moved_capture = tmp_path / "moved-capture"
        shutil.copytree(root.parent, moved_capture)
        moved = _admit(
            service,
            moved_capture / root.name,
            moved_capture / manifest_path.name,
            idempotency_namespace,
            identity_namespace,
            scope,
        )
        assert moved == first
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 2
    finally:
        qualified.close()


def test_malformed_identity_definition_stays_unknown_evidence_without_fabricated_object(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(
            tmp_path,
            "malformed-identity-source",
            identity_bytes=b'{"workspace_id":"orchard","agent_id":\n',
        )
        run = _admit(
            NativeLegacyIdentityAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            identity_namespace,
            scope,
        )
        assert [(item.definition_kind, item.admission_status) for item in run.results] == [
            ("IDENTITY", "UNKNOWN"),
            ("CHARACTER_DEFINITION", "ADMITTED"),
        ]
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind=?", (LEGACY_AGENT_IDENTITY_OBJECT_KIND,)).fetchone()[0] == 0
        unknown = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_status='UNKNOWN'"
        ).fetchone()[0])
        assert unknown["original_provenance"] == "UNKNOWN"
        assert "not valid UTF-8 JSON" in unknown["reason"]
    finally:
        qualified.close()


def test_identity_admission_remains_independent_of_unrelated_admitted_memory(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, "identity-with-memory-source", include_nodes=True)
        memory = NativeLegacyObjectAdmissionService(connection).admit_nodes_current_state(
            snapshot_root=root,
            manifest_path=manifest_path,
            idempotency_namespace_id=idempotency_namespace,
            object_identity_namespace_id=identity_namespace,
            unknown_semantic_scope_id=scope,
        ).results[0]
        identity_run = _admit(
            NativeLegacyIdentityAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            identity_namespace,
            scope,
        )
        assert memory.object_id is not None
        assert all(item.admission_status == "ADMITTED" for item in identity_run.results)
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 3
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
    finally:
        qualified.close()


def _manual_identity_admission(
    connection: sqlite3.Connection,
    *,
    manifest,
    baseline,
    idempotency_namespace,
    identity_namespace,
    scope,
    origin_kind: str = "LEGACY_ADMISSION",
    include_admission_effect: bool = True,
    include_output: bool = True,
    mismatch_output: bool = False,
):
    snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
    source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
    artifact_id = native_id_to_bytes(next(
        artifact.artifact_id
        for artifact in manifest.artifacts
        if artifact.observed_relative_locator.endswith("/identity.json")
    ))
    batch_id = connection.execute(
        "SELECT admission_batch_id FROM legacy_admission_batches WHERE legacy_snapshot_id=? AND batch_identity='TMS-LEGACY-IDENTITY-ADMISSION-7F3C'",
        (snapshot_id,),
    ).fetchone()[0]
    operation_id, transition_id, object_id, revision_id, admission_id, artifact_record_id = (
        _id(), _id(), _id(), _id(), _id(), _id()
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
            (
                native_id_to_bytes(operation_id),
                native_id_to_bytes(idempotency_namespace),
                f"manual-identity-{origin_kind}-{include_admission_effect}-{include_output}-{mismatch_output}",
                "ADMIT_LEGACY_IDENTITY_DEFINITION",
                "TMS-INTENT-1",
                "{}",
            ),
        )
        connection.execute(
            "INSERT INTO legacy_artifact_records VALUES (?,?,?,?)",
            (native_id_to_bytes(artifact_record_id), artifact_id, f"manual-{object_id}", "identity.json#manual"),
        )
        connection.execute(
            "INSERT INTO legacy_admission_records VALUES (?,?,?,'ADMITTED',NULL)",
            (native_id_to_bytes(admission_id), batch_id, native_id_to_bytes(artifact_record_id)),
        )
        connection.execute(
            "INSERT INTO objects VALUES (?,?,?,?,?,?,?)",
            (
                native_id_to_bytes(object_id),
                native_id_to_bytes(identity_namespace),
                LEGACY_AGENT_IDENTITY_OBJECT_KIND,
                native_id_to_bytes(transition_id),
                native_id_to_bytes(revision_id),
                1,
                0,
            ),
        )
        connection.execute(
            """
            INSERT INTO object_revisions(
                object_revision_id,object_id,revision_ordinal,lineage_kind,
                effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,
                governance_state,authority_category,payload_format,payload_text,created_at_ns
            ) VALUES (?,?,1,'LEGACY_PREDECESSOR_UNKNOWN',?,'EXISTS','UNKNOWN',0,
                      'UNKNOWN','NOT_APPLICABLE','JSON','{}',0)
            """,
            (native_id_to_bytes(revision_id), native_id_to_bytes(object_id), native_id_to_bytes(scope)),
        )
        alias_value = json.dumps({"agent_id": "manual", "workspace_id": "manual"}, separators=(",", ":"), sort_keys=True)
        connection.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (source_namespace_id, LEGACY_IDENTITY_ALIAS_KIND, alias_value, native_id_to_bytes(object_id)),
        )
        connection.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "LEGACY_IDENTITY_ADMISSION", origin_kind),
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
            output_object_id = baseline.object_id if mismatch_output else object_id
            connection.execute(
                """
                INSERT INTO operation_outputs(
                    operation_id,output_ordinal,output_role,output_kind,object_id,
                    object_revision_id,object_revision_ordinal
                ) VALUES (?,?,?,'OBJECT',?,?,1)
                """,
                (
                    native_id_to_bytes(operation_id),
                    0,
                    "LEGACY_IDENTITY_ADMISSION",
                    native_id_to_bytes(output_object_id),
                    native_id_to_bytes(revision_id),
                ),
            )
        tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
        tx.transitions.append(native_id_to_bytes(transition_id))
        tx.published.append((native_id_to_bytes(object_id), native_id_to_bytes(revision_id), 1))
        tx.legacy_identity_admitted.append(
            (
                native_id_to_bytes(object_id),
                native_id_to_bytes(revision_id),
                1,
                native_id_to_bytes(admission_id),
                native_id_to_bytes(transition_id),
                snapshot_id,
                artifact_id,
                native_id_to_bytes(artifact_record_id),
                LEGACY_AGENT_IDENTITY_OBJECT_KIND,
                LEGACY_IDENTITY_ALIAS_KIND,
                alias_value,
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
        ("LEGACY_ADMISSION", False, True, False, "H2 legacy identity admission effect"),
        ("LEGACY_ADMISSION", True, False, False, "H8"),
        ("LEGACY_ADMISSION", True, True, True, "H8"),
    ],
)
def test_h7_h2_and_h8_refuse_masquerading_or_incomplete_identity_admission(
    tmp_path: Path,
    origin_kind: str,
    include_admission_effect: bool,
    include_output: bool,
    mismatch_output: bool,
    match: str,
):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(tmp_path, "identity-invariant-source")
        baseline = _admit(
            NativeLegacyIdentityAdmissionService(connection),
            root,
            manifest_path,
            idempotency_namespace,
            identity_namespace,
            scope,
        ).results[0]
        object_count = connection.execute("SELECT count(*) FROM objects").fetchone()[0]
        tx = _manual_identity_admission(
            connection,
            manifest=manifest,
            baseline=baseline,
            idempotency_namespace=idempotency_namespace,
            identity_namespace=identity_namespace,
            scope=scope,
            origin_kind=origin_kind,
            include_admission_effect=include_admission_effect,
            include_output=include_output,
            mismatch_output=mismatch_output,
        )
        try:
            with pytest.raises(SubstrateInvariantViolation, match=match):
                tx.validate()
        finally:
            connection.execute("ROLLBACK")
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == object_count
    finally:
        qualified.close()
