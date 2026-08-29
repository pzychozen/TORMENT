"""Focused Phase 7F3D synthetic motif and membership admission tests."""

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
from torment_service.substrate.migration.motif_admission import (
    LEGACY_DERIVED_MOTIF_OBJECT_KIND,
    LEGACY_MOTIF_ALIAS_KIND,
    MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,
    NativeLegacyMotifAdmissionService,
)
from torment_service.substrate.objects import NativeObjectService, ObjectState, SubstrateTx
from torment_service.substrate.relationships import NativeRelationshipService
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "legacy-motif-admission.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    object_namespace, relationship_namespace, scope, alternate_scope, idempotency_namespace = (
        _id(), _id(), _id(), _id(), _id()
    )
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(object_namespace), "legacy-motif-objects"),
    )
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(relationship_namespace), "legacy-motif-memberships"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), "legacy-motif-unknown-scope"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(alternate_scope), "legacy-motif-alternate-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "legacy-motif-idempotency"),
    )
    return qualified, object_namespace, relationship_namespace, scope, alternate_scope, idempotency_namespace


def _motif(*, motif_id: str = "motif_reflection_0001", members: list[int] | None = None, **overrides):
    state = {
        "motif_id": motif_id,
        "domain_id": "reflection",
        "label": "Synthetic reflection basin",
        "centroid": [0.25, -0.5, 0.75],
        "strength": 0.7,
        "members": [1, 2, 3] if members is None else members,
        "contributing_agents": ["aria", "nox"],
        "stability_score": 0.8,
        "created_ts": 101,
        "last_active_ts": 102,
        "derivation_metadata": {"algorithm": "captured-synthetic-only"},
    }
    state.update(overrides)
    return state


def _snapshot(
    tmp_path: Path,
    source_key: str,
    *,
    motifs: dict[str, object] | None = None,
    node_eids: tuple[int, ...] = (1, 2, 3),
    include_events: bool = True,
):
    capture = tmp_path / source_key
    root = capture / "legacy-snapshot"
    root.mkdir(parents=True)
    if node_eids:
        (root / "nodes.jsonl").write_bytes(
            b"".join(
                json.dumps({"eid": eid, "text": f"synthetic node {eid}"}, separators=(",", ":")).encode("utf-8") + b"\n"
                for eid in node_eids
            )
        )
    motif_path = root / "workspaces" / "orchard" / "domains" / "reflection" / "motifs.json"
    motif_path.parent.mkdir(parents=True)
    motif_path.write_text(
        json.dumps(
            {"motifs": motifs if motifs is not None else {"motif_reflection_0001": _motif()}},
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if include_events:
        event_path = motif_path.with_name("motif_events.jsonl")
        event_path.write_bytes(
            b'{"event":"MOTIF_CREATED","motif_id":"event-only","members":[999]}\n'
        )
    manifest_path = capture / "snapshot-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=_id(),
        legacy_source_namespace_key=source_key,
        capture_label="synthetic 7F3D motif fixture only",
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


def _admit_motifs(
    service,
    root,
    manifest_path,
    idempotency_namespace,
    object_namespace,
    relationship_namespace,
    scope,
):
    return service.admit_motifs_current_state(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
        motif_identity_namespace_id=object_namespace,
        membership_identity_namespace_id=relationship_namespace,
        unknown_semantic_scope_id=scope,
    )


def test_valid_motif_admission_is_atomic_derived_and_leaves_events_as_evidence(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope, _alternate_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(tmp_path, "valid-motif-source")
        node_run = _admit_nodes(
            NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope
        )
        sources = {result.raw_eid: result for result in node_run.results}
        source_views = {
            eid: NativeObjectService(connection).get_current_object(result.object_id)
            for eid, result in sources.items()
        }
        source_revision_count = connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0]
        source_transition_count = connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0]
        service = NativeLegacyMotifAdmissionService(connection)
        first = _admit_motifs(
            service, root, manifest_path, idempotency_namespace, object_namespace, relationship_namespace, scope
        )
        retry = _admit_motifs(
            service, root, manifest_path, idempotency_namespace, object_namespace, relationship_namespace, scope
        )
        assert retry == first
        result = first.results[0]
        assert result.admission_status == "ADMITTED"
        assert result.motif_id == "motif_reflection_0001"
        assert result.motif_object_id and result.motif_revision_id and result.transition_id
        assert [membership.member_eid for membership in result.memberships] == [1, 2, 3]
        assert len({membership.relationship_id for membership in result.memberships}) == 3
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 4
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 3
        assert connection.execute("SELECT count(*) FROM relationship_revisions").fetchone()[0] == 3
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_relationship_aliases").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM operation_outputs WHERE operation_id=?", (native_id_to_bytes(result.operation_id),)).fetchone()[0] == 4
        assert connection.execute("SELECT count(*) FROM object_revision_effects WHERE transition_id=?", (native_id_to_bytes(result.transition_id),)).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationship_revision_effects WHERE transition_id=?", (native_id_to_bytes(result.transition_id),)).fetchone()[0] == 3
        assert connection.execute("SELECT count(*) FROM legacy_admission_effects WHERE transition_id=?", (native_id_to_bytes(result.transition_id),)).fetchone()[0] == 1
        motif = NativeObjectService(connection).get_current_object(result.motif_object_id)
        assert motif == NativeObjectService(connection).get_object_revision(result.motif_revision_id)
        assert json.loads(motif.payload) == {
            key: value for key, value in _motif().items() if key != "members"
        }
        assert "members" not in json.loads(motif.payload)
        assert json.loads(motif.payload)["centroid"] == [0.25, -0.5, 0.75]
        assert json.loads(motif.payload)["derivation_metadata"] == {"algorithm": "captured-synthetic-only"}
        assert service.resolve_legacy_motif_alias(
            legacy_source_namespace_id=manifest.legacy_source_namespace_id,
            motif_id="motif_reflection_0001",
        ) == result.motif_object_id
        relationship_service = NativeRelationshipService(connection)
        for membership in result.memberships:
            view = relationship_service.get_current_relationship(membership.relationship_id)
            assert view == relationship_service.get_relationship_revision(membership.revision_id)
            assert [(endpoint.ordinal, endpoint.role, endpoint.binding_mode, endpoint.object_revision_id) for endpoint in view.endpoints] == [
                (0, "MOTIF", "IDENTITY", None),
                (1, "MEMBER", "IDENTITY", None),
            ]
            assert view.endpoints[0].object_id == result.motif_object_id
            assert view.endpoints[1].object_id == sources[membership.member_eid].object_id
            assert view.endpoints[1].semantic_scope_id == scope
        assert {eid: NativeObjectService(connection).get_current_object(item.object_id) for eid, item in sources.items()} == source_views
        assert connection.execute("SELECT count(*) FROM object_revisions").fetchone()[0] == source_revision_count + 1
        assert connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == source_transition_count + 1
        assert connection.execute(
            "SELECT transition_kind FROM semantic_transitions WHERE transition_kind LIKE '%MOTIF_EVENT%'"
        ).fetchall() == []
        assert connection.execute(
            "SELECT count(*) FROM legacy_artifact_records ar JOIN legacy_artifacts a USING(legacy_artifact_id) WHERE a.observed_locator LIKE '%motif_events.jsonl'"
        ).fetchone()[0] == 0
        metadata = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?",
            (native_id_to_bytes(result.admission_record_id),),
        ).fetchone()[0])
        assert metadata["motif_reconstructability"] == "NOT_PROVEN"
        assert metadata["motif_event_completeness_for_replay"] == "NOT_PROVEN"
        assert metadata["native_representation_created"] is False
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE object_revisions SET payload_text='{}' WHERE object_revision_id=?", (native_id_to_bytes(result.motif_revision_id),))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE relationship_revisions SET lifecycle_state='ACTIVE' WHERE relationship_revision_id=?", (native_id_to_bytes(result.memberships[0].revision_id),))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM relationship_revision_endpoints WHERE relationship_revision_id=?", (native_id_to_bytes(result.memberships[0].revision_id),))
    finally:
        qualified.close()


def test_dangling_member_quarantines_whole_motif_without_placeholder_or_partial_rows(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope, _alternate_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(
            tmp_path,
            "dangling-motif-source",
            motifs={"motif_reflection_0001": _motif(members=[1, 2, 999])},
            node_eids=(1, 2),
        )
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        result = _admit_motifs(
            NativeLegacyMotifAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, relationship_namespace, scope
        ).results[0]
        assert result.admission_status == "QUARANTINED"
        assert result.motif_object_id is None and result.memberships == ()
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases WHERE alias_value='999'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM semantic_transitions WHERE transition_kind='LEGACY_MOTIF_ADMISSION'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_quarantine_records").fetchone()[0] == 1
    finally:
        qualified.close()


@pytest.mark.parametrize(
    ("source_key", "motif_state", "status", "reason"),
    [
        ("duplicate-member-source", _motif(members=[1, 1]), "QUARANTINED", "duplicate member"),
        ("malformed-motif-source", _motif(centroid=[0.1, "not-a-number"]), "UNKNOWN", "centroid"),
    ],
)
def test_ambiguous_or_malformed_motif_is_not_coerced_to_semantics(tmp_path: Path, source_key, motif_state, status, reason):
    qualified, object_namespace, relationship_namespace, scope, _alternate_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, source_key, motifs={"motif_reflection_0001": motif_state}, node_eids=(1,))
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        result = _admit_motifs(
            NativeLegacyMotifAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, relationship_namespace, scope
        ).results[0]
        assert result.admission_status == status
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind=?", (LEGACY_DERIVED_MOTIF_OBJECT_KIND,)).fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        metadata = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?", (native_id_to_bytes(result.admission_record_id),)
        ).fetchone()[0])
        assert reason in metadata["reason"]
    finally:
        qualified.close()


def test_moved_snapshot_retry_returns_same_motif_and_memberships(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope, _alternate_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, "movable-motif-source")
        _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        service = NativeLegacyMotifAdmissionService(connection)
        first = _admit_motifs(service, root, manifest_path, idempotency_namespace, object_namespace, relationship_namespace, scope)
        moved_capture = tmp_path / "moved-capture"
        shutil.copytree(root.parent, moved_capture)
        moved = _admit_motifs(
            service,
            moved_capture / root.name,
            moved_capture / manifest_path.name,
            idempotency_namespace,
            object_namespace,
            relationship_namespace,
            scope,
        )
        assert moved == first
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind=?", (LEGACY_DERIVED_MOTIF_OBJECT_KIND,)).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationships WHERE relationship_kind=?", (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,)).fetchone()[0] == 3
    finally:
        qualified.close()


def test_cross_scope_member_endpoint_preserves_current_member_scope_without_mutating_source(tmp_path: Path):
    qualified, object_namespace, relationship_namespace, scope, alternate_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, "cross-scope-motif-source")
        nodes = _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        source_two = next(item for item in nodes.results if item.raw_eid == 2)
        successor = NativeObjectService(connection).transition_object(
            idempotency_namespace_id=idempotency_namespace,
            idempotency_key="synthetic-cross-scope-source-successor",
            object_id=source_two.object_id,
            expected_revision_id=source_two.revision_id,
            state=ObjectState(object_namespace, alternate_scope, "LEGACY_CORE_NODE", "EXISTS", "UNKNOWN", False, "UNKNOWN"),
        )
        before = NativeObjectService(connection).get_current_object(source_two.object_id)
        result = _admit_motifs(
            NativeLegacyMotifAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, relationship_namespace, scope
        ).results[0]
        second_membership = next(item for item in result.memberships if item.member_eid == 2)
        endpoints = NativeRelationshipService(connection).get_current_relationship(second_membership.relationship_id).endpoints
        assert endpoints[0].semantic_scope_id == scope
        assert endpoints[1].semantic_scope_id == alternate_scope
        assert endpoints[1].object_revision_id is None
        assert NativeObjectService(connection).get_current_object(source_two.object_id) == before
        assert NativeObjectService(connection).get_current_object(source_two.object_id).revision_id == successor.revision_id
    finally:
        qualified.close()


def _manual_motif_admission(
    connection: sqlite3.Connection,
    *,
    manifest,
    baseline,
    sources,
    idempotency_namespace,
    object_namespace,
    relationship_namespace,
    scope,
    origin_kind: str = "LEGACY_ADMISSION",
    omit_membership_effect: bool = False,
    mismatch_output: bool = False,
):
    snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
    source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
    artifact_id = native_id_to_bytes(next(item.artifact_id for item in manifest.artifacts if item.observed_relative_locator.endswith("/motifs.json")))
    batch_id = connection.execute(
        "SELECT admission_batch_id FROM legacy_admission_batches WHERE legacy_snapshot_id=? AND batch_identity='TMS-LEGACY-MOTIF-ADMISSION-7F3D'",
        (snapshot_id,),
    ).fetchone()[0]
    operation_id, transition_id, motif_id, motif_revision_id, admission_id, artifact_record_id = (_id(), _id(), _id(), _id(), _id(), _id())
    memberships = [(_id(), _id(), eid) for eid in (1, 2)]
    alias_value = "manual-motif"
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("INSERT INTO operations VALUES (?,?,?,?,?,?,0)", (native_id_to_bytes(operation_id), native_id_to_bytes(idempotency_namespace), f"manual-motif-{origin_kind}-{omit_membership_effect}-{mismatch_output}", "ADMIT_LEGACY_MOTIF_CURRENT", "TMS-INTENT-1", "{}"))
        connection.execute("INSERT INTO legacy_artifact_records VALUES (?,?,?,?)", (native_id_to_bytes(artifact_record_id), artifact_id, f"manual-{motif_id}", "motifs.json#manual"))
        connection.execute("INSERT INTO legacy_admission_records VALUES (?,?,?,'ADMITTED',NULL)", (native_id_to_bytes(admission_id), batch_id, native_id_to_bytes(artifact_record_id)))
        connection.execute("INSERT INTO objects VALUES (?,?,?,?,?,?,?)", (native_id_to_bytes(motif_id), native_id_to_bytes(object_namespace), LEGACY_DERIVED_MOTIF_OBJECT_KIND, native_id_to_bytes(transition_id), native_id_to_bytes(motif_revision_id), 1, 0))
        connection.execute("""INSERT INTO object_revisions(object_revision_id,object_id,revision_ordinal,lineage_kind,effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,governance_state,authority_category,payload_format,payload_text,created_at_ns) VALUES (?,?,1,'LEGACY_PREDECESSOR_UNKNOWN',?,'EXISTS','UNKNOWN',0,'UNKNOWN','NOT_APPLICABLE','JSON','{}',0)""", (native_id_to_bytes(motif_revision_id), native_id_to_bytes(motif_id), native_id_to_bytes(scope)))
        connection.execute("INSERT INTO legacy_object_aliases VALUES (?,?,?,?)", (source_namespace_id, LEGACY_MOTIF_ALIAS_KIND, alias_value, native_id_to_bytes(motif_id)))
        for relationship_id, revision_id, eid in memberships:
            source = sources[eid]
            connection.execute("INSERT INTO relationships VALUES (?,?,?,?,?,?,?)", (native_id_to_bytes(relationship_id), native_id_to_bytes(relationship_namespace), MOTIF_MEMBERSHIP_RELATIONSHIP_KIND, native_id_to_bytes(transition_id), native_id_to_bytes(revision_id), 1, 0))
            connection.execute("""INSERT INTO relationship_revisions(relationship_revision_id,relationship_id,revision_ordinal,lineage_kind,effective_semantic_scope_id,existence_state,lifecycle_state,lifecycle_authoritative,governance_state,authority_category,payload_format,created_at_ns) VALUES (?,?,1,'LEGACY_PREDECESSOR_UNKNOWN',?,'EXISTS','UNKNOWN',0,'UNKNOWN','NOT_APPLICABLE','NONE',0)""", (native_id_to_bytes(revision_id), native_id_to_bytes(relationship_id), native_id_to_bytes(scope)))
            connection.execute("INSERT INTO relationship_revision_endpoints VALUES (?,?,?,? ,?,'IDENTITY',NULL,NULL)", (native_id_to_bytes(revision_id), 0, "MOTIF", native_id_to_bytes(scope), native_id_to_bytes(motif_id)))
            connection.execute("INSERT INTO relationship_revision_endpoints VALUES (?,?,?,? ,?,'IDENTITY',NULL,NULL)", (native_id_to_bytes(revision_id), 1, "MEMBER", native_id_to_bytes(scope), native_id_to_bytes(source.object_id)))
        connection.execute("INSERT INTO semantic_transitions VALUES (?,?,?,?,0)", (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "LEGACY_MOTIF_ADMISSION", origin_kind))
        connection.execute("INSERT INTO object_revision_effects VALUES (?,?,?,1)", (native_id_to_bytes(transition_id), native_id_to_bytes(motif_id), native_id_to_bytes(motif_revision_id)))
        for index, (relationship_id, revision_id, _eid) in enumerate(memberships):
            if not (omit_membership_effect and index == 1):
                connection.execute("INSERT INTO relationship_revision_effects VALUES (?,?,?,1)", (native_id_to_bytes(transition_id), native_id_to_bytes(relationship_id), native_id_to_bytes(revision_id)))
        connection.execute("INSERT INTO legacy_admission_effects VALUES (?,?)", (native_id_to_bytes(transition_id), native_id_to_bytes(admission_id)))
        output_motif_id = baseline.motif_object_id if mismatch_output else motif_id
        connection.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,'OBJECT',?,?,1)", (native_id_to_bytes(operation_id), 0, "LEGACY_MOTIF_ADMISSION", native_id_to_bytes(output_motif_id), native_id_to_bytes(motif_revision_id)))
        for index, (relationship_id, revision_id, _eid) in enumerate(memberships, start=1):
            connection.execute("INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,relationship_id,relationship_revision_id,relationship_revision_ordinal) VALUES (?,?,?,'RELATIONSHIP',?,?,1)", (native_id_to_bytes(operation_id), index, "LEGACY_MOTIF_MEMBERSHIP_ADMISSION", native_id_to_bytes(relationship_id), native_id_to_bytes(revision_id)))
        tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
        tx.transitions.append(native_id_to_bytes(transition_id))
        tx.published.append((native_id_to_bytes(motif_id), native_id_to_bytes(motif_revision_id), 1))
        tx.relationship_published.extend((native_id_to_bytes(relationship_id), native_id_to_bytes(revision_id), 1) for relationship_id, revision_id, _ in memberships)
        tx.legacy_motif_admitted.append((native_id_to_bytes(motif_id), native_id_to_bytes(motif_revision_id), 1, native_id_to_bytes(admission_id), native_id_to_bytes(transition_id), snapshot_id, artifact_id, native_id_to_bytes(artifact_record_id), alias_value, native_id_to_bytes(scope), tuple((native_id_to_bytes(relationship_id), native_id_to_bytes(revision_id), 1, native_id_to_bytes(sources[eid].object_id), native_id_to_bytes(scope), str(eid)) for relationship_id, revision_id, eid in memberships)))
        return tx
    except Exception:
        connection.execute("ROLLBACK")
        raise


@pytest.mark.parametrize(
    ("origin_kind", "omit_membership_effect", "mismatch_output", "match"),
    [
        ("NATIVE", False, False, "H7"),
        ("LEGACY_ADMISSION", True, False, "H2 relationship effect"),
        ("LEGACY_ADMISSION", False, True, "H8"),
    ],
)
def test_h7_h2_and_h8_refuse_incomplete_or_masquerading_motif_admission(tmp_path: Path, origin_kind, omit_membership_effect, mismatch_output, match):
    qualified, object_namespace, relationship_namespace, scope, _alternate_scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(tmp_path, "motif-invariant-source")
        nodes = _admit_nodes(NativeLegacyObjectAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, scope)
        sources = {item.raw_eid: item for item in nodes.results}
        baseline = _admit_motifs(NativeLegacyMotifAdmissionService(connection), root, manifest_path, idempotency_namespace, object_namespace, relationship_namespace, scope).results[0]
        object_count = connection.execute("SELECT count(*) FROM objects").fetchone()[0]
        relationship_count = connection.execute("SELECT count(*) FROM relationships").fetchone()[0]
        tx = _manual_motif_admission(connection, manifest=manifest, baseline=baseline, sources=sources, idempotency_namespace=idempotency_namespace, object_namespace=object_namespace, relationship_namespace=relationship_namespace, scope=scope, origin_kind=origin_kind, omit_membership_effect=omit_membership_effect, mismatch_output=mismatch_output)
        try:
            with pytest.raises(SubstrateInvariantViolation, match=match):
                tx.validate()
        finally:
            connection.execute("ROLLBACK")
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == object_count
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == relationship_count
    finally:
        qualified.close()
