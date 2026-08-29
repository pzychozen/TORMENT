"""Focused Phase 7F3F synthetic proposal/status admission tests."""

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
from torment_service.substrate.migration.proposal_admission import (
    LEGACY_PROPOSAL_ALIAS_KIND,
    LEGACY_SHARE_PROPOSAL_OBJECT_KIND,
    NativeLegacyProposalAdmissionService,
)
from torment_service.substrate.objects import NativeObjectService, SubstrateTx
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "legacy-proposal-admission.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity_namespace, scope, idempotency_namespace = _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity_namespace), "legacy-proposal-admission-objects"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), "legacy-proposal-admission-unknown-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "legacy-proposal-admission-idempotency"),
    )
    return qualified, identity_namespace, scope, idempotency_namespace


def _proposal(
    proposal_id: str,
    *,
    status: str = "pending",
    summary: str | None = None,
    agent_id: str = "agent-with-no-admitted-identity",
) -> dict[str, object]:
    return {
        "proposal_id": proposal_id,
        "workspace_id": "orchard",
        "domain_id": "personal",
        "agent_id": agent_id,
        "summary": summary or f"synthetic proposal {proposal_id}",
        "embedding": [0.25, -0.5, 0.75],
        "mtype": "episodic",
        "confidence": 0.9,
        "strength": 0.8,
        "created_ts": 100,
        "status": status,
        "half_life_days": 7.0,
        "note": "submitted",
    }


def _event(proposal_id: str, status: str, *, note: str | None = None, ts: int = 200) -> dict[str, object]:
    return {
        "proposal_id": proposal_id,
        "workspace_id": "orchard",
        "domain_id": "personal",
        "status": status,
        "note": note,
        "ts": ts,
    }


def _jsonl(rows: list[dict[str, object] | bytes]) -> bytes:
    return b"".join(
        row + (b"" if row.endswith(b"\n") else b"\n")
        if isinstance(row, bytes)
        else (json.dumps(row, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def _snapshot(
    tmp_path: Path,
    source_key: str,
    *,
    proposals: list[dict[str, object] | bytes] | None = None,
    events: list[dict[str, object] | bytes] | None = None,
):
    capture = tmp_path / source_key
    root = capture / "legacy-snapshot"
    domain = root / "workspaces" / "orchard" / "domains" / "personal"
    domain.mkdir(parents=True)
    proposal_rows = proposals or [_proposal("P1"), _proposal("P2"), _proposal("P3"), _proposal("P4")]
    event_rows = events if events is not None else [
        _event("P2", "approved", note="approved", ts=201),
        _event("P3", "rejected", note="rejected", ts=202),
        _event("P4", "approved", note="first", ts=203),
        _event("P4", "rejected", note="last", ts=204),
    ]
    (domain / "proposals.jsonl").write_bytes(_jsonl(proposal_rows))
    (domain / "proposal_events.jsonl").write_bytes(_jsonl(event_rows))
    manifest_path = capture / "snapshot-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=_id(),
        legacy_source_namespace_key=source_key,
        capture_label="synthetic 7F3F proposal/status fixture only",
    )
    return root, manifest_path, manifest


def _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope):
    return service.admit_proposals_effective_state(
        snapshot_root=root,
        manifest_path=manifest_path,
        idempotency_namespace_id=idempotency_namespace,
        object_identity_namespace_id=identity_namespace,
        unknown_semantic_scope_id=scope,
    )


def _admitted_by_id(run):
    return {item.proposal_id: item for item in run.results if item.admission_status == "ADMITTED"}


def test_effective_proposal_status_is_frozen_intent_not_authorization_and_is_idempotent(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(tmp_path, "proposal-state-source")
        service = NativeLegacyProposalAdmissionService(connection)
        first = _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope)
        # A caller can lose the first response: immutable evidence returns the same result.
        assert _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope) == first
        admitted = _admitted_by_id(first)
        assert set(admitted) == {"P1", "P2", "P3", "P4"}
        assert all(item.object_id and item.revision_id and item.transition_id for item in admitted.values())
        views = {
            proposal_id: NativeObjectService(connection).get_current_object(item.object_id)
            for proposal_id, item in admitted.items()
        }
        payloads = {proposal_id: json.loads(view.payload) for proposal_id, view in views.items()}
        assert {proposal_id: payload["effective_status"] for proposal_id, payload in payloads.items()} == {
            "P1": "pending", "P2": "approved", "P3": "rejected", "P4": "rejected"
        }
        assert payloads["P4"]["legacy_proposal"]["note"] == "last"
        assert payloads["P4"]["legacy_proposal"]["processed_ts"] == 204
        assert [event["status"] for event in payloads["P4"]["legacy_event_evidence"]] == ["approved", "rejected"]
        assert all(view.authority_category == "INTENT_PROPOSAL" for view in views.values())
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE authority_category='ACTIVE_AUTHORIZATION'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind=?", (LEGACY_SHARE_PROPOSAL_OBJECT_KIND,)).fetchone()[0] == 4
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM relationships").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 4
        assert connection.execute("SELECT DISTINCT transition_kind FROM semantic_transitions").fetchall() == [("LEGACY_PROPOSAL_ADMISSION",)]
        assert connection.execute("SELECT count(*) FROM semantic_transitions WHERE transition_kind LIKE '%EVENT%'").fetchone()[0] == 0
        assert service.resolve_legacy_proposal_alias(
            legacy_source_namespace_id=manifest.legacy_source_namespace_id,
            workspace_id="orchard",
            domain_id="personal",
            proposal_id="P2",
        ) == admitted["P2"].object_id
        alias = connection.execute(
            "SELECT alias_value FROM legacy_object_aliases WHERE object_id=?",
            (native_id_to_bytes(admitted["P2"].object_id),),
        ).fetchone()[0]
        assert json.loads(alias) == {"domain_id": "personal", "proposal_id": "P2", "workspace_id": "orchard"}
        metadata = json.loads(connection.execute(
            "SELECT unknown_fields_json FROM legacy_admission_records WHERE admission_record_id=?",
            (native_id_to_bytes(admitted["P2"].admission_record_id),),
        ).fetchone()[0])
        assert metadata["authority_category"] == "INTENT_PROPOSAL"
        assert metadata["event_semantic_history"] == "NOT_IMPORTED"
        assert metadata["embedding_disposition"] == "CAPTURED_CONTENT_ONLY"
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind LIKE 'LEGACY_%IDENTITY%'").fetchone()[0] == 0
        classes = dict(connection.execute("SELECT observed_locator,artifact_kind FROM legacy_artifacts"))
        assert classes["workspaces/orchard/domains/personal/proposals.jsonl"] == "LEGACY_PROPOSAL_STATE_EVIDENCE"
        assert classes["workspaces/orchard/domains/personal/proposal_events.jsonl"] == "LEGACY_PROPOSAL_EVENT_EVIDENCE"
        with pytest.raises(sqlite3.IntegrityError, match="immutable object revision"):
            connection.execute(
                "UPDATE object_revisions SET payload_text='{}' WHERE object_revision_id=?",
                (native_id_to_bytes(admitted["P2"].revision_id),),
            )
    finally:
        qualified.close()


def test_moved_snapshot_retry_reuses_exact_proposal_outputs(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        root, manifest_path, _ = _snapshot(tmp_path, "movable-proposal-source")
        service = NativeLegacyProposalAdmissionService(qualified.connection)
        first = _admit(service, root, manifest_path, idempotency_namespace, identity_namespace, scope)
        moved_capture = tmp_path / "moved-capture"
        shutil.copytree(root.parent, moved_capture)
        moved = _admit(
            service, moved_capture / root.name, moved_capture / manifest_path.name,
            idempotency_namespace, identity_namespace, scope,
        )
        assert moved == first
        assert qualified.connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 4
        assert qualified.connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 4
    finally:
        qualified.close()


def test_malformed_orphan_and_conflicting_proposal_evidence_is_not_guessed(tmp_path: Path):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        proposals = [
            _proposal("P1"),
            _proposal("P2"),
            b'{"proposal_id":"broken",',
            _proposal("Pdup", summary="first submission"),
            _proposal("Pdup", summary="conflicting second submission"),
        ]
        events = [
            _event("P2", "not-a-supported-status", ts=201),
            _event("orphan", "approved", ts=202),
            b'{"proposal_id":"P1","status":',
        ]
        root, manifest_path, _ = _snapshot(
            tmp_path, "ambiguous-proposal-source", proposals=proposals, events=events
        )
        run = _admit(
            NativeLegacyProposalAdmissionService(qualified.connection), root, manifest_path,
            idempotency_namespace, identity_namespace, scope,
        )
        admitted = _admitted_by_id(run)
        # The malformed JSON row cannot safely be attributed to P1, so it is
        # retained as evidence and does not overwrite P1's prior state.
        assert set(admitted) == {"P1"}
        assert qualified.connection.execute("SELECT count(*) FROM objects").fetchone()[0] == 1
        statuses = [(item.proposal_id, item.admission_status) for item in run.results]
        assert ("P1", "ADMITTED") in statuses
        assert ("P2", "QUARANTINED") in statuses
        assert ("Pdup", "QUARANTINED") in statuses
        assert ("orphan", "UNKNOWN") in statuses
        assert any(status == "UNKNOWN" and proposal_id is None for proposal_id, status in statuses)
        assert qualified.connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 1
        assert qualified.connection.execute("SELECT count(*) FROM legacy_admission_records WHERE admission_status='QUARANTINED'").fetchone()[0] >= 3
    finally:
        qualified.close()


def _manual_proposal_admission(
    connection: sqlite3.Connection,
    *,
    manifest,
    baseline,
    idempotency_namespace,
    identity_namespace,
    scope,
    origin_kind: str = "LEGACY_ADMISSION",
    authority_category: str = "INTENT_PROPOSAL",
    include_object_effect: bool = True,
    include_admission_effect: bool = True,
    include_output: bool = True,
    mismatch_output: bool = False,
):
    snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
    source_namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
    artifact_id = native_id_to_bytes(next(
        artifact.artifact_id for artifact in manifest.artifacts if artifact.observed_relative_locator.endswith("/proposals.jsonl")
    ))
    batch_id = connection.execute(
        "SELECT admission_batch_id FROM legacy_admission_batches WHERE legacy_snapshot_id=? AND batch_identity='TMS-LEGACY-PROPOSAL-ADMISSION-7F3F'",
        (snapshot_id,),
    ).fetchone()[0]
    operation_id, transition_id, object_id, revision_id, admission_id, artifact_record_id = (_id(), _id(), _id(), _id(), _id(), _id())
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
            (
                native_id_to_bytes(operation_id), native_id_to_bytes(idempotency_namespace),
                f"manual-proposal-{origin_kind}-{authority_category}-{include_object_effect}-{include_admission_effect}-{include_output}-{mismatch_output}",
                "ADMIT_LEGACY_PROPOSAL_EFFECTIVE_STATE", "TMS-INTENT-1", "{}",
            ),
        )
        connection.execute(
            "INSERT INTO legacy_artifact_records VALUES (?,?,?,?)",
            (native_id_to_bytes(artifact_record_id), artifact_id, f"manual-{object_id}", "proposals.jsonl#manual"),
        )
        connection.execute(
            "INSERT INTO legacy_admission_records VALUES (?,?,?,'ADMITTED',NULL)",
            (native_id_to_bytes(admission_id), batch_id, native_id_to_bytes(artifact_record_id)),
        )
        connection.execute(
            "INSERT INTO objects VALUES (?,?,?,?,?,?,?)",
            (native_id_to_bytes(object_id), native_id_to_bytes(identity_namespace), LEGACY_SHARE_PROPOSAL_OBJECT_KIND,
             native_id_to_bytes(transition_id), native_id_to_bytes(revision_id), 1, 0),
        )
        connection.execute(
            """
            INSERT INTO object_revisions(
                object_revision_id,object_id,revision_ordinal,lineage_kind,effective_semantic_scope_id,
                existence_state,lifecycle_state,lifecycle_authoritative,governance_state,authority_category,
                payload_format,payload_text,created_at_ns
            ) VALUES (?,?,1,'LEGACY_PREDECESSOR_UNKNOWN',?,'EXISTS','UNKNOWN',0,'UNKNOWN',?,'JSON',?,0)
            """,
            (native_id_to_bytes(revision_id), native_id_to_bytes(object_id), native_id_to_bytes(scope), authority_category,
             '{"effective_status":"approved","legacy_event_evidence":[],"legacy_proposal":{"status":"approved"}}'),
        )
        alias_value = json.dumps({"domain_id": "manual", "proposal_id": "manual", "workspace_id": "manual"}, separators=(",", ":"), sort_keys=True)
        connection.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (source_namespace_id, LEGACY_PROPOSAL_ALIAS_KIND, alias_value, native_id_to_bytes(object_id)),
        )
        connection.execute(
            "INSERT INTO semantic_transitions VALUES (?,?,?,?,0)",
            (native_id_to_bytes(transition_id), native_id_to_bytes(operation_id), "LEGACY_PROPOSAL_ADMISSION", origin_kind),
        )
        if include_object_effect:
            connection.execute("INSERT INTO object_revision_effects VALUES (?,?,?,1)", (native_id_to_bytes(transition_id), native_id_to_bytes(object_id), native_id_to_bytes(revision_id)))
        if include_admission_effect:
            connection.execute("INSERT INTO legacy_admission_effects VALUES (?,?)", (native_id_to_bytes(transition_id), native_id_to_bytes(admission_id)))
        if include_output:
            output_object_id = baseline.object_id if mismatch_output else object_id
            connection.execute(
                "INSERT INTO operation_outputs(operation_id,output_ordinal,output_role,output_kind,object_id,object_revision_id,object_revision_ordinal) VALUES (?,?,?,'OBJECT',?,?,1)",
                (native_id_to_bytes(operation_id), 0, "LEGACY_PROPOSAL_ADMISSION", native_id_to_bytes(output_object_id), native_id_to_bytes(revision_id)),
            )
        tx = SubstrateTx(connection, native_id_to_bytes(operation_id))
        tx.transitions.append(native_id_to_bytes(transition_id))
        if include_object_effect:
            tx.published.append((native_id_to_bytes(object_id), native_id_to_bytes(revision_id), 1))
        tx.legacy_proposal_admitted.append(
            (native_id_to_bytes(object_id), native_id_to_bytes(revision_id), 1, native_id_to_bytes(admission_id),
             native_id_to_bytes(transition_id), snapshot_id, artifact_id, native_id_to_bytes(artifact_record_id), alias_value, "approved")
        )
        return tx
    except Exception:
        connection.execute("ROLLBACK")
        raise


@pytest.mark.parametrize(
    ("origin_kind", "authority_category", "include_object_effect", "include_admission_effect", "include_output", "mismatch_output", "match"),
    [
        ("NATIVE", "INTENT_PROPOSAL", True, True, True, False, "H7"),
        ("LEGACY_ADMISSION", "ACTIVE_AUTHORIZATION", True, True, True, False, "H7"),
        ("LEGACY_ADMISSION", "INTENT_PROPOSAL", False, True, True, False, "H2"),
        ("LEGACY_ADMISSION", "INTENT_PROPOSAL", True, False, True, False, "H2 legacy proposal admission effect"),
        ("LEGACY_ADMISSION", "INTENT_PROPOSAL", True, True, False, False, "H8"),
        ("LEGACY_ADMISSION", "INTENT_PROPOSAL", True, True, True, True, "H8"),
    ],
)
def test_h7_h2_and_h8_refuse_wrong_proposal_admission_publication(
    tmp_path: Path,
    origin_kind: str,
    authority_category: str,
    include_object_effect: bool,
    include_admission_effect: bool,
    include_output: bool,
    mismatch_output: bool,
    match: str,
):
    qualified, identity_namespace, scope, idempotency_namespace = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(tmp_path, "proposal-invariant-source")
        baseline = _admit(
            NativeLegacyProposalAdmissionService(connection), root, manifest_path,
            idempotency_namespace, identity_namespace, scope,
        ).results[0]
        object_count = connection.execute("SELECT count(*) FROM objects").fetchone()[0]
        tx = _manual_proposal_admission(
            connection, manifest=manifest, baseline=baseline, idempotency_namespace=idempotency_namespace,
            identity_namespace=identity_namespace, scope=scope, origin_kind=origin_kind,
            authority_category=authority_category, include_object_effect=include_object_effect,
            include_admission_effect=include_admission_effect, include_output=include_output,
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
