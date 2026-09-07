"""Focused B1F/B4P authority tests for preserved partial legacy motifs."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.migration.partial_motif_authority import (
    MotifSemanticDisposition,
    NativePartialMotifAuthorityRetentionService,
    PartialMotifAuthorityRefused,
    PartialMotifReason,
    PartialMotifRetentionRequest,
    certify_partial_motif,
    classify_frozen_motifs,
    continuation_summary,
    reload_and_validate_certification,
    write_or_reload_continuation,
)
from torment_service.substrate.migration.snapshot import create_snapshot_manifest
from torment_service.substrate.schema import create_schema


def _native_id():
    return generate_native_id()


def _insert(connection, table: str, value, label: str, *, reserved: bool = False) -> None:
    connection.execute(
        f"INSERT INTO {table} VALUES ({'?,?,0' if reserved else '?,?'})",
        (native_id_to_bytes(value), label),
    )


def _node(eid: int) -> dict[str, object]:
    return {"eid": eid, "text": f"partial-authority fixture node {eid}"}


def _motif(motif_id: str, members: list[int], *, contributors: list[str] | None = None) -> dict[str, object]:
    return {
        "motif_id": motif_id,
        "domain_id": "domain",
        "label": f"motif {motif_id}",
        "centroid": [0.25, -0.5],
        "strength": 0.7,
        "stability_score": 0.8,
        "contributing_agents": ["alpha"] if contributors is None else contributors,
        "created_ts": 1,
        "last_active_ts": 2,
        "members": members,
    }


def _snapshot_nodes(tmp_path: Path, *, name: str, namespace, source_key: str, eids: tuple[int, ...]):
    root = tmp_path / name
    root.mkdir()
    (root / "nodes.jsonl").write_text(
        "".join(json.dumps(_node(eid), separators=(",", ":")) + "\n" for eid in eids),
        encoding="utf-8",
    )
    manifest_path = tmp_path / f"{name}-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=namespace,
        legacy_source_namespace_key=source_key,
    )
    return root, manifest_path, manifest


def _snapshot_motif(tmp_path: Path, *, name: str, namespace, motif: dict[str, object]):
    root = tmp_path / name
    path = root / "workspaces" / "ws" / "domains" / "domain"
    path.mkdir(parents=True)
    (path / "motifs.json").write_text(
        json.dumps({"motifs": {motif["motif_id"]: motif}}, separators=(",", ":")),
        encoding="utf-8",
    )
    manifest_path = tmp_path / f"{name}-manifest.json"
    create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=namespace,
        legacy_source_namespace_key="p1:partial:source",
    )
    return root, manifest_path


@pytest.fixture
def authority_fixture(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "authority.db")
    connection = qualified.connection
    metadata = create_schema(connection)
    object_identity, unknown_scope, idempotency = _native_id(), _native_id(), _native_id()
    source_one, source_two = _native_id(), _native_id()
    _insert(connection, "identity_namespaces", object_identity, "partial-objects", reserved=True)
    _insert(connection, "semantic_scopes", unknown_scope, "partial-unknown", reserved=True)
    _insert(connection, "idempotency_namespaces", idempotency, "partial-idempotency")
    _insert(connection, "legacy_source_namespaces", source_one, "p1:partial:one", reserved=True)
    _insert(connection, "legacy_source_namespaces", source_two, "p1:partial:two", reserved=True)
    admission = NativeLegacyObjectAdmissionService(connection)
    for name, namespace, source_key, eids in (
        ("nodes-one", source_one, "p1:partial:one", (1, 2)),
        ("nodes-two", source_two, "p1:partial:two", (1,)),
    ):
        root, manifest_path, _ = _snapshot_nodes(
            tmp_path, name=name, namespace=namespace, source_key=source_key, eids=eids,
        )
        admission.admit_nodes_current_state(
            snapshot_root=root,
            manifest_path=manifest_path,
            idempotency_namespace_id=idempotency,
            object_identity_namespace_id=object_identity,
            unknown_semantic_scope_id=unknown_scope,
        )
    return {
        "qualified": qualified,
        "connection": connection,
        "core_id": UUID(bytes=metadata.core_id),
        "source_one": source_one,
        "source_two": source_two,
        "scope_key": {"workspace_id": "ws", "scope_kind": "SHARED", "agent_id": None, "domain_id": "domain"},
    }


def _classified(authority_fixture, tmp_path: Path, *, name: str, members: list[int], namespaces, contributors=None):
    root, manifest_path = _snapshot_motif(
        tmp_path,
        name=name,
        namespace=authority_fixture["source_one"],
        motif=_motif(name, members, contributors=contributors),
    )
    values = classify_frozen_motifs(
        authority_fixture["connection"],
        snapshot_root=root,
        manifest_path=manifest_path,
        scope_key=authority_fixture["scope_key"],
        eligible_member_source_namespace_ids=namespaces,
    )
    assert len(values) == 1
    return values[0], root, manifest_path


def test_b1f_terminal_dispositions_are_all_or_nothing(authority_fixture, tmp_path: Path) -> None:
    source_one, source_two = authority_fixture["source_one"], authority_fixture["source_two"]
    exact, _, _ = _classified(authority_fixture, tmp_path, name="m1", members=[2], namespaces=(source_one,))
    multiplicity, _, _ = _classified(authority_fixture, tmp_path, name="m2", members=[2, 2], namespaces=(source_one,))
    ambiguous, _, _ = _classified(authority_fixture, tmp_path, name="m3", members=[1], namespaces=(source_one, source_two))
    both, _, _ = _classified(authority_fixture, tmp_path, name="m4", members=[1, 1], namespaces=(source_two, source_one))
    zero_member, _, _ = _classified(authority_fixture, tmp_path, name="m0", members=[], namespaces=(source_one,))
    zero_candidate, _, _ = _classified(authority_fixture, tmp_path, name="block", members=[99], namespaces=(source_one, source_two))

    assert exact.disposition is MotifSemanticDisposition.EXACT_ADMITTED
    assert multiplicity.disposition is MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED
    assert multiplicity.partial_reason is PartialMotifReason.MULTIPLICITY_INCOMPATIBLE
    assert ambiguous.disposition is MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED
    assert ambiguous.partial_reason is PartialMotifReason.IDENTITY_AMBIGUOUS
    assert both.disposition is MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED
    assert both.partial_reason is PartialMotifReason.BOTH
    assert zero_member.disposition is MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED
    assert zero_candidate.disposition is MotifSemanticDisposition.BLOCKING_QUARANTINE
    assert zero_candidate.blocking_code == "ZERO_CANDIDATE_PRESENT"


def test_partial_certificate_round_trip_is_source_only_and_b4p_is_null_projection(authority_fixture, tmp_path: Path) -> None:
    source_one, source_two = authority_fixture["source_one"], authority_fixture["source_two"]
    disposition, root, manifest_path = _classified(
        authority_fixture, tmp_path, name="partial", members=[1, 1], namespaces=(source_two, source_one), contributors=["zeta", "alpha"],
    )
    b1m_digest = "a" * 64
    certificate = certify_partial_motif(
        disposition,
        b1m_identity_universe_digest=b1m_digest,
        normal_admission_record_id=None,
        normal_quarantine_record_id=None,
    )
    encoded = json.dumps(certificate.payload, sort_keys=True)
    assert not {"native_object_id", "candidate_object_ids", "candidate_namespace_ids", "chosen_candidate", "resolution_status"}.intersection(certificate.payload)
    assert "LEGACY_CORE_NODE" not in encoded

    continuation = write_or_reload_continuation(
        directory=tmp_path / "continuation",
        predecessor_carrier_sha256="b" * 64,
        b1m_identity_universe_digest=b1m_digest,
        b1f_disposition_digest="c" * 64,
        certifications=(certificate,),
    )
    replay = reload_and_validate_certification(
        authority_fixture["connection"],
        continuation_record_path=continuation,
        certification_digest=certificate.digest,
        snapshot_root=root,
        manifest_path=manifest_path,
        eligible_member_source_namespace_ids=(source_one, source_two),
        b1m_identity_universe_digest=b1m_digest,
    )
    assert replay == certificate
    with pytest.raises(PartialMotifAuthorityRefused, match="P3_B1M_IDENTITY_UNIVERSE_DRIFT"):
        reload_and_validate_certification(
            authority_fixture["connection"], continuation_record_path=continuation,
            certification_digest=certificate.digest, snapshot_root=root, manifest_path=manifest_path,
            eligible_member_source_namespace_ids=(source_one, source_two), b1m_identity_universe_digest="d" * 64,
        )

    proof = NativePartialMotifAuthorityRetentionService(authority_fixture["connection"]).prove_retention(
        PartialMotifRetentionRequest(
            continuation_record_path=continuation,
            certification_digest=certificate.digest,
            snapshot_root=root,
            manifest_path=manifest_path,
            expected_native_core_id=authority_fixture["core_id"],
            eligible_member_source_namespace_ids=(source_two, source_one),
            b1m_identity_universe_digest=b1m_digest,
        )
    )
    assert (proof.derived_motif_count, proof.motif_id_alias_count, proof.membership_count) == (0, 0, 0)
    assert continuation_summary(continuation) == {"partial_certification_count": 1, "b4p_count": 1}
    assert NativePartialMotifAuthorityRetentionService(authority_fixture["connection"]).prove_retention(
        PartialMotifRetentionRequest(
            continuation_record_path=continuation, certification_digest=certificate.digest,
            snapshot_root=root, manifest_path=manifest_path, expected_native_core_id=authority_fixture["core_id"],
            eligible_member_source_namespace_ids=(source_one, source_two), b1m_identity_universe_digest=b1m_digest,
        )
    ) == proof
