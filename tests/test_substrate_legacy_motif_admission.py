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
    event_record: dict[str, object] | None = None,
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
            json.dumps(
                event_record or {"event": "MOTIF_CREATED", "motif_id": "event-only", "members": [999]},
                separators=(",", ":"),
            ).encode("utf-8") + b"\n"
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
    eligible_member_source_namespace_ids=None,
):
    return service.admit_motifs_current_state(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
        motif_identity_namespace_id=object_namespace,
        membership_identity_namespace_id=relationship_namespace,
        unknown_semantic_scope_id=scope,
        eligible_member_source_namespace_ids=eligible_member_source_namespace_ids,
    )


def _additional_scope(connection, label: str):
    value = _id()
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(value), label),
    )
    return value


def _admitted_node_source(
    connection,
    tmp_path: Path,
    source_key: str,
    node_eids: tuple[int, ...],
    idempotency_namespace,
    object_namespace,
    scope,
):
    root, manifest_path, manifest = _snapshot(
        tmp_path, source_key, motifs={}, node_eids=node_eids
    )
    run = _admit_nodes(
        NativeLegacyObjectAdmissionService(connection),
        root,
        manifest_path,
        idempotency_namespace,
        object_namespace,
        scope,
    )
    return root, manifest_path, manifest, {item.raw_eid: item for item in run.results}


def _motif_result(
    connection,
    tmp_path: Path,
    source_key: str,
    motif_state: dict[str, object],
    idempotency_namespace,
    object_namespace,
    relationship_namespace,
    scope,
    eligible_member_source_namespace_ids,
    event_record: dict[str, object] | None = None,
):
    root, manifest_path, manifest = _snapshot(
        tmp_path,
        source_key,
        motifs={str(motif_state["motif_id"]): motif_state},
        node_eids=(),
        event_record=event_record,
    )
    result = _admit_motifs(
        NativeLegacyMotifAdmissionService(connection),
        root,
        manifest_path,
        idempotency_namespace,
        object_namespace,
        relationship_namespace,
        scope,
        eligible_member_source_namespace_ids,
    ).results[0]
    return manifest, result


def _membership_endpoint_rows(connection, result):
    return {
        membership.member_eid: connection.execute(
            """
            SELECT object_id,endpoint_semantic_scope_id
            FROM relationship_revision_endpoints
            WHERE relationship_revision_id=? AND endpoint_ordinal=1 AND endpoint_role='MEMBER'
            """,
            (native_id_to_bytes(membership.revision_id),),
        ).fetchone()
        for membership in result.memberships
    }


def _quarantine_condition(connection, result) -> str:
    return connection.execute(
        """
        SELECT condition_code FROM legacy_quarantine_records
        WHERE admission_record_id=?
        """,
        (native_id_to_bytes(result.admission_record_id),),
    ).fetchone()[0]


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


def test_q1_local_namespace_remains_admitted_under_an_explicit_singleton_boundary(tmp_path: Path):
    qualified, object_ns, relationship_ns, scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(
            tmp_path,
            "q1-local",
            motifs={"q1": _motif(motif_id="q1", members=[1, 2, 3])},
            node_eids=(1, 2, 3),
        )
        run = _admit_nodes(
            NativeLegacyObjectAdmissionService(connection), root, manifest_path,
            idempotency, object_ns, scope,
        )
        source = {item.raw_eid: item for item in run.results}
        result = _admit_motifs(
            NativeLegacyMotifAdmissionService(connection), root, manifest_path,
            idempotency, object_ns, relationship_ns, scope,
            (manifest.legacy_source_namespace_id,),
        ).results[0]
        assert result.admission_status == "ADMITTED"
        endpoints = _membership_endpoint_rows(connection, result)
        assert {eid: row[0] for eid, row in endpoints.items()} == {
            eid: native_id_to_bytes(item.object_id) for eid, item in source.items()
        }
    finally:
        qualified.close()


def test_q2_shared_registry_binds_unique_private_members_without_duplicate_objects_or_aliases(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        private_scope = _additional_scope(connection, "q2-private")
        _root, _path, private_manifest, private = _admitted_node_source(
            connection, tmp_path, "q2-private", (1, 2, 3, 4), idempotency, object_ns, private_scope
        )
        before_objects = connection.execute("SELECT count(*) FROM objects").fetchone()[0]
        before_aliases = connection.execute("SELECT count(*) FROM legacy_object_aliases").fetchone()[0]
        shared_manifest, result = _motif_result(
            connection, tmp_path, "q2-shared", _motif(motif_id="q2", members=[1, 2, 3, 4]),
            idempotency, object_ns, relationship_ns, shared_scope,
            (private_manifest.legacy_source_namespace_id,),
        )
        assert result.admission_status == "ADMITTED"
        assert len(result.memberships) == 4
        endpoints = _membership_endpoint_rows(connection, result)
        assert {eid: row[0] for eid, row in endpoints.items()} == {
            eid: native_id_to_bytes(item.object_id) for eid, item in private.items()
        }
        assert {row[1] for row in endpoints.values()} == {native_id_to_bytes(private_scope)}
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == before_objects + 1
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases").fetchone()[0] == before_aliases + 1
        assert shared_manifest.legacy_source_namespace_id != private_manifest.legacy_source_namespace_id
    finally:
        qualified.close()


def test_q3_one_motif_resolves_each_member_against_its_own_unique_scope(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        private_a_scope = _additional_scope(connection, "q3-private-a")
        private_b_scope = _additional_scope(connection, "q3-private-b")
        _root, _path, private_a_manifest, private_a = _admitted_node_source(
            connection, tmp_path, "q3-private-a", (1,), idempotency, object_ns, private_a_scope
        )
        _root, _path, private_b_manifest, private_b = _admitted_node_source(
            connection, tmp_path, "q3-private-b", (3,), idempotency, object_ns, private_b_scope
        )
        _root, _path, shared_manifest, shared = _admitted_node_source(
            connection, tmp_path, "q3-shared", (2,), idempotency, object_ns, shared_scope
        )
        # The source manifest has already frozen the registry, so use a separate
        # motif registry source while retaining the shared namespace as candidate.
        motif_manifest, result = _motif_result(
            connection, tmp_path, "q3-registry", _motif(motif_id="q3", members=[1, 2, 3]),
            idempotency, object_ns, relationship_ns, shared_scope,
            (
                private_a_manifest.legacy_source_namespace_id,
                shared_manifest.legacy_source_namespace_id,
                private_b_manifest.legacy_source_namespace_id,
            ),
        )
        endpoints = _membership_endpoint_rows(connection, result)
        assert result.admission_status == "ADMITTED"
        assert endpoints[1] == (native_id_to_bytes(private_a[1].object_id), native_id_to_bytes(private_a_scope))
        assert endpoints[2] == (native_id_to_bytes(shared[2].object_id), native_id_to_bytes(shared_scope))
        assert endpoints[3] == (native_id_to_bytes(private_b[3].object_id), native_id_to_bytes(private_b_scope))
        assert motif_manifest.legacy_source_namespace_id not in {
            private_a_manifest.legacy_source_namespace_id,
            shared_manifest.legacy_source_namespace_id,
            private_b_manifest.legacy_source_namespace_id,
        }
    finally:
        qualified.close()


def test_q4_private_shared_numeric_collision_is_ambiguous_and_has_no_partial_motif(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        private_scope = _additional_scope(connection, "q4-private")
        _root, _path, private_manifest, _private = _admitted_node_source(
            connection, tmp_path, "q4-private", (1,), idempotency, object_ns, private_scope
        )
        _root, _path, shared_manifest, _shared = _admitted_node_source(
            connection, tmp_path, "q4-shared-memory", (1,), idempotency, object_ns, shared_scope
        )
        _motif_manifest, result = _motif_result(
            connection, tmp_path, "q4-registry", _motif(motif_id="q4", members=[1]),
            idempotency, object_ns, relationship_ns, shared_scope,
            (private_manifest.legacy_source_namespace_id, shared_manifest.legacy_source_namespace_id),
        )
        assert result.admission_status == "QUARANTINED"
        assert result.motif_object_id is None and result.memberships == ()
        assert _quarantine_condition(connection, result) == "AMBIGUOUS_LEGACY_MOTIF_MEMBER_ALIAS"
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        metadata = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?",
            (native_id_to_bytes(result.admission_record_id),),
        ).fetchone()[0])
        assert metadata["member_resolution_failure"] == "AMBIGUOUS_LEGACY_MOTIF_MEMBER_ALIAS"
    finally:
        qualified.close()


def test_q5_two_private_numeric_collision_does_not_use_contributing_agents_as_tie_break(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        scope_a = _additional_scope(connection, "q5-private-a")
        scope_b = _additional_scope(connection, "q5-private-b")
        _root, _path, manifest_a, _items_a = _admitted_node_source(
            connection, tmp_path, "q5-private-a", (1,), idempotency, object_ns, scope_a
        )
        _root, _path, manifest_b, _items_b = _admitted_node_source(
            connection, tmp_path, "q5-private-b", (1,), idempotency, object_ns, scope_b
        )
        _motif_manifest, result = _motif_result(
            connection, tmp_path, "q5-registry",
            _motif(motif_id="q5", members=[1], contributing_agents=["private-a"]),
            idempotency, object_ns, relationship_ns, shared_scope,
            (manifest_a.legacy_source_namespace_id, manifest_b.legacy_source_namespace_id),
        )
        assert result.admission_status == "QUARANTINED"
        assert _quarantine_condition(connection, result) == "AMBIGUOUS_LEGACY_MOTIF_MEMBER_ALIAS"
    finally:
        qualified.close()


def test_q6_no_bounded_candidate_is_unresolved_without_a_placeholder(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        _manifest, result = _motif_result(
            connection, tmp_path, "q6-registry", _motif(motif_id="q6", members=[404]),
            idempotency, object_ns, relationship_ns, shared_scope, (_id(),),
        )
        assert result.admission_status == "QUARANTINED"
        assert result.motif_object_id is None and result.memberships == ()
        assert _quarantine_condition(connection, result) == "UNRESOLVED_LEGACY_MOTIF_MEMBER_ALIAS"
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 0
    finally:
        qualified.close()


def test_q7_unrelated_workspace_alias_is_never_a_candidate_without_topology_membership(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        foreign_scope = _additional_scope(connection, "workspace-b-private")
        _root, _path, _foreign_manifest, _foreign = _admitted_node_source(
            connection, tmp_path, "workspace-b-private", (7,), idempotency, object_ns, foreign_scope
        )
        local_namespace = _id()
        _manifest, result = _motif_result(
            connection, tmp_path, "workspace-a-registry", _motif(motif_id="q7", members=[7]),
            idempotency, object_ns, relationship_ns, shared_scope, (local_namespace,),
        )
        assert result.admission_status == "QUARANTINED"
        assert _quarantine_condition(connection, result) == "UNRESOLVED_LEGACY_MOTIF_MEMBER_ALIAS"
    finally:
        qualified.close()


def test_q8_motif_events_are_diagnostic_only_and_cannot_resolve_an_ambiguous_member(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        scope_a = _additional_scope(connection, "q8-private-a")
        scope_b = _additional_scope(connection, "q8-private-b")
        _root, _path, manifest_a, _items_a = _admitted_node_source(
            connection, tmp_path, "q8-private-a", (1,), idempotency, object_ns, scope_a
        )
        _root, _path, manifest_b, _items_b = _admitted_node_source(
            connection, tmp_path, "q8-private-b", (1,), idempotency, object_ns, scope_b
        )
        _manifest, result = _motif_result(
            connection, tmp_path, "q8-registry",
            _motif(motif_id="q8", members=[1], contributing_agents=["private-a"]),
            idempotency, object_ns, relationship_ns, shared_scope,
            (manifest_a.legacy_source_namespace_id, manifest_b.legacy_source_namespace_id),
            {"event": "MOTIF_MEMBER_ADDED", "motif_id": "q8", "member_eid": 1, "agent_id": "private-a"},
        )
        assert result.admission_status == "QUARANTINED"
        assert _quarantine_condition(connection, result) == "AMBIGUOUS_LEGACY_MOTIF_MEMBER_ALIAS"
        assert connection.execute(
            "SELECT count(*) FROM semantic_transitions WHERE transition_kind LIKE '%MOTIF_EVENT%'"
        ).fetchone()[0] == 0
    finally:
        qualified.close()


def test_q9_contributing_agents_remain_motif_aggregate_evidence_not_member_identity(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        scope_a = _additional_scope(connection, "q9-private-a")
        scope_b = _additional_scope(connection, "q9-private-b")
        _root, _path, manifest_a, _items_a = _admitted_node_source(
            connection, tmp_path, "q9-private-a", (9,), idempotency, object_ns, scope_a
        )
        _root, _path, manifest_b, _items_b = _admitted_node_source(
            connection, tmp_path, "q9-private-b", (9,), idempotency, object_ns, scope_b
        )
        _manifest, result = _motif_result(
            connection, tmp_path, "q9-registry",
            _motif(motif_id="q9", members=[9], contributing_agents=["q9-private-a"]),
            idempotency, object_ns, relationship_ns, shared_scope,
            (manifest_a.legacy_source_namespace_id, manifest_b.legacy_source_namespace_id),
        )
        assert result.admission_status == "QUARANTINED"
        assert _quarantine_condition(connection, result) == "AMBIGUOUS_LEGACY_MOTIF_MEMBER_ALIAS"
    finally:
        qualified.close()


def test_q10_unique_cross_scope_retry_reuses_one_motif_and_membership_set(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        private_scope = _additional_scope(connection, "q10-private")
        _root, _path, private_manifest, _private = _admitted_node_source(
            connection, tmp_path, "q10-private", (1, 2), idempotency, object_ns, private_scope
        )
        root, manifest_path, _manifest = _snapshot(
            tmp_path, "q10-registry", motifs={"q10": _motif(motif_id="q10", members=[1, 2])}, node_eids=()
        )
        service = NativeLegacyMotifAdmissionService(connection)
        kwargs = (
            service, root, manifest_path, idempotency, object_ns, relationship_ns,
            shared_scope, (private_manifest.legacy_source_namespace_id,),
        )
        first = _admit_motifs(*kwargs)
        second = _admit_motifs(*kwargs)
        assert first == second
        assert first.results[0].admission_status == "ADMITTED"
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind=?", (LEGACY_DERIVED_MOTIF_OBJECT_KIND,)).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationships WHERE relationship_kind=?", (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,)).fetchone()[0] == 2
    finally:
        qualified.close()


def test_local_only_quarantine_is_preserved_before_bounded_requalification(tmp_path: Path):
    qualified, object_ns, relationship_ns, shared_scope, _alternate, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        private_scope = _additional_scope(connection, "requalification-private")
        _root, _path, private_manifest, _private = _admitted_node_source(
            connection, tmp_path, "requalification-private", (1, 2), idempotency, object_ns, private_scope
        )
        root, manifest_path, registry_manifest = _snapshot(
            tmp_path,
            "requalification-registry",
            motifs={"requalification": _motif(motif_id="requalification", members=[1, 2])},
            node_eids=(),
        )
        service = NativeLegacyMotifAdmissionService(connection)
        local_only = _admit_motifs(
            service, root, manifest_path, idempotency, object_ns, relationship_ns, shared_scope,
            (registry_manifest.legacy_source_namespace_id,),
        ).results[0]
        recovered = _admit_motifs(
            service, root, manifest_path, idempotency, object_ns, relationship_ns, shared_scope,
            (private_manifest.legacy_source_namespace_id, registry_manifest.legacy_source_namespace_id),
        ).results[0]
        retry = _admit_motifs(
            service, root, manifest_path, idempotency, object_ns, relationship_ns, shared_scope,
            (private_manifest.legacy_source_namespace_id, registry_manifest.legacy_source_namespace_id),
        ).results[0]
        assert local_only.admission_status == "QUARANTINED"
        assert _quarantine_condition(connection, local_only) == "UNRESOLVED_LEGACY_MOTIF_MEMBER_ALIAS"
        assert recovered.admission_status == "ADMITTED"
        assert retry == recovered
        assert local_only.admission_record_id != recovered.admission_record_id
        assert connection.execute(
            "SELECT count(*) FROM legacy_admission_records WHERE admission_status='QUARANTINED'"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM objects WHERE object_kind=?", (LEGACY_DERIVED_MOTIF_OBJECT_KIND,)
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM relationships WHERE relationship_kind=?", (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,)
        ).fetchone()[0] == 2
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
        tx.legacy_motif_admitted.append((native_id_to_bytes(motif_id), native_id_to_bytes(motif_revision_id), 1, native_id_to_bytes(admission_id), native_id_to_bytes(transition_id), snapshot_id, artifact_id, native_id_to_bytes(artifact_record_id), alias_value, native_id_to_bytes(scope), tuple((native_id_to_bytes(relationship_id), native_id_to_bytes(revision_id), 1, native_id_to_bytes(sources[eid].object_id), native_id_to_bytes(scope), str(eid), source_namespace_id) for relationship_id, revision_id, eid in memberships)))
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
