"""Phase 7F4 synthetic integrated legacy-migration rehearsal tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3

import numpy as np
import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateEvidenceIntegrityMismatch
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.migration.rehearsal import (
    MigrationRehearsalConfig,
    NativeLegacyMigrationRehearsal,
)
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "integrated-migration-rehearsal.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    object_namespace, relationship_namespace, scope, idempotency_namespace = _id(), _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(object_namespace), "integrated-rehearsal-objects"),
    )
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(relationship_namespace), "integrated-rehearsal-relationships"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), "integrated-rehearsal-unknown-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency_namespace), "integrated-rehearsal-idempotency"),
    )
    return qualified, MigrationRehearsalConfig(
        native_core_id=_id(),
        idempotency_namespace_id=idempotency_namespace,
        object_identity_namespace_id=object_namespace,
        relationship_identity_namespace_id=relationship_namespace,
        unknown_semantic_scope_id=scope,
    )


def _json_line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def _node(eid: int, *, embedding_ref: bool = False, exported_deep: bool = False) -> dict[str, object]:
    value: dict[str, object] = {"eid": eid, "text": f"synthetic core memory {eid}"}
    if embedding_ref:
        value["embedding_ref"] = {
            "map": "embeddings/shard_000000.map.jsonl",
            "shard": "embeddings/shard_000000.npy",
            "row": 0,
            "dimension": 3,
            "dtype": "float32",
        }
    if exported_deep:
        value.update({"exported_deep": True, "exported_step": 50, "compression_route": "long_path"})
    return value


def _motif(*, members: list[int]) -> dict[str, object]:
    return {
        "motif_id": "motif-integrated-1",
        "domain_id": "reflection",
        "label": "Synthetic integrated motif",
        "centroid": [0.25, -0.5, 0.75],
        "strength": 0.7,
        "members": members,
        "contributing_agents": ["aria"],
        "stability_score": 0.8,
        "created_ts": 101,
        "last_active_ts": 102,
        "derivation_metadata": {"algorithm": "synthetic-captured-only"},
    }


def _deep(eid: int = 1) -> dict[str, object]:
    return {
        "eid": eid,
        "born_step": 11,
        "compressed_step": 50,
        "summary": "Synthetic corroborated deep summary.",
        "compression_score": 0.5,
        "original_motif_id": "motif-integrated-1",
        "memory_class": "core",
        "embedding_ref": {"shard": 9, "row": 4, "dim": 3},
        "metadata": {"workspace_id": "orchard", "captured": True},
    }


def _proposal(proposal_id: str) -> dict[str, object]:
    return {
        "proposal_id": proposal_id,
        "workspace_id": "orchard",
        "domain_id": "personal",
        "agent_id": "unadmitted-agent",
        "summary": f"Synthetic proposal {proposal_id}",
        "embedding": [0.25, -0.5, 0.75],
        "mtype": "episodic",
        "confidence": 0.9,
        "strength": 0.8,
        "created_ts": 100,
        "status": "pending",
        "half_life_days": 7.0,
    }


def _event(proposal_id: str, status: str, ts: int) -> dict[str, object]:
    return {
        "proposal_id": proposal_id,
        "workspace_id": "orchard",
        "domain_id": "personal",
        "status": status,
        "note": status,
        "ts": ts,
    }


def _write_identity(root: Path) -> None:
    identity = root / "workspaces" / "orchard" / "agents" / "aria" / "identity.json"
    identity.parent.mkdir(parents=True)
    identity.write_text(
        json.dumps(
            {
                "workspace_id": "orchard", "agent_id": "aria", "seed": {"seed_id": "aria-v1"},
                "overlay": {"write_threshold": 0.45}, "created_ts": 101, "updated_ts": 102,
            },
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    seed = root / "workspaces" / "orchard" / "seeds" / "aria-v1" / "seed.json"
    seed.parent.mkdir(parents=True)
    seed.write_text(
        json.dumps(
            {
                "seed_id": "aria-v1", "character_name": "Aria", "seed_text": "Synthetic character.",
                "seed_eids": [1], "owner_agent_id": "aria", "version": "1.0.0", "created_ts": 103,
            },
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    identity.with_name("character_state.json").write_text(
        json.dumps({"workspace_id": "orchard", "agent_id": "aria", "seed_id": "aria-v1", "drift_score": 0.4}) + "\n",
        encoding="utf-8",
    )


def _snapshot(tmp_path: Path, source_key: str, *, failure: bool = False, identity_only: bool = False):
    capture = tmp_path / source_key
    root = capture / "legacy-snapshot"
    root.mkdir(parents=True)
    _write_identity(root)
    if not identity_only:
        nodes = [
            _node(1, embedding_ref=True, exported_deep=not failure),
            _node(2),
            _node(3),
        ]
        (root / "nodes.jsonl").write_bytes(b"".join(_json_line(item) for item in nodes))
        edge = {
            "edge_id": "edge-integrated-1",
            "relationship_kind": "LEGACY_EDGE",
            "endpoints": [{"role": "SOURCE", "eid": 1}, {"role": "TARGET", "eid": 999 if failure else 2}],
        }
        (root / "edges.jsonl").write_bytes(_json_line(edge))
        (root / "memory_events.jsonl").write_bytes(b'{"event":"MEMORY_CREATE","eid":999}\n')

        embeddings = root / "embeddings"
        embeddings.mkdir()
        np.save(embeddings / "shard_000000.npy", np.array([[1.25, -2.0, 3.5]], dtype=np.float32))
        (embeddings / "manifest.json").write_bytes(_json_line({
            "encoding_id": "NUMPY_NPY", "dtype": "float32", "dimension": 3,
            "derivation_contract_version": "synthetic-embed-v1", "provider": "synthetic", "model": "synthetic",
            "shards": [{"path": "embeddings/shard_000000.npy", "map": "embeddings/shard_000000.map.jsonl"}],
        }))
        (embeddings / "shard_000000.map.jsonl").write_bytes(_json_line({
            "eid": 1, "shard": "embeddings/shard_000000.npy", "row": 0, "dimension": 4 if failure else 3,
        }))

        motif_path = root / "workspaces" / "orchard" / "domains" / "reflection" / "motifs.json"
        motif_path.parent.mkdir(parents=True)
        motif_path.write_text(json.dumps({"motifs": {"motif-integrated-1": _motif(members=[1, 999] if failure else [1, 2])}}, sort_keys=True) + "\n", encoding="utf-8")
        motif_path.with_name("motif_events.jsonl").write_bytes(b'{"event":"MOTIF_CREATED","motif_id":"evidence-only"}\n')

        deep_path = root / "workspaces" / "orchard" / "agents" / "aria" / "deep_memory" / "memories.jsonl"
        deep_path.parent.mkdir(parents=True)
        deep_path.write_bytes(_json_line(_deep()))

        proposal_path = root / "workspaces" / "orchard" / "domains" / "personal" / "proposals.jsonl"
        proposal_path.parent.mkdir(parents=True)
        proposal_path.write_bytes(b"".join(_json_line(_proposal(value)) for value in ("P1", "P2", "P3")))
        event_status = "malformed-status" if failure else "approved"
        proposal_path.with_name("proposal_events.jsonl").write_bytes(
            _json_line(_event("P2", event_status, 201)) + _json_line(_event("P3", "rejected", 202))
        )

        (root / "mystery.capture").write_bytes(b"unknown synthetic evidence\n")
        (root / "closure_ledger.jsonl").write_bytes(b'{"closure":"not a typed migration family"}\n')
        (root / "legacy_search.sqlite").write_bytes(b"synthetic acceleration evidence only\n")
    manifest_path = capture / "snapshot-manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=_id(),
        legacy_source_namespace_key=source_key,
        capture_label="synthetic Phase 7F4 integrated rehearsal only",
    )
    return root, manifest_path, manifest


def _counts(connection: sqlite3.Connection) -> tuple[int, ...]:
    return tuple(
        connection.execute(sql).fetchone()[0]
        for sql in (
            "SELECT count(*) FROM objects", "SELECT count(*) FROM object_revisions",
            "SELECT count(*) FROM relationships", "SELECT count(*) FROM relationship_revisions",
            "SELECT count(*) FROM representations", "SELECT count(*) FROM legacy_object_aliases",
            "SELECT count(*) FROM legacy_relationship_aliases", "SELECT count(*) FROM legacy_admission_records",
            "SELECT count(*) FROM semantic_transitions", "SELECT count(*) FROM operations",
        )
    )


def test_full_synthetic_rehearsal_reports_exact_counts_and_preserves_boundaries(tmp_path: Path):
    qualified, config = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, manifest = _snapshot(tmp_path, "coherent-source")
        report = NativeLegacyMigrationRehearsal(connection).run(
            snapshot_root=root, manifest_path=manifest_path, config=config
        )
        assert report.legacy_snapshot_id == manifest.legacy_snapshot_id
        assert report.execution_order == (
            "IDENTITY_CHARACTER", "CORE_OBJECT", "CORE_RELATIONSHIP", "CORE_EMBEDDING_REPRESENTATION",
            "MOTIF_DERIVATION", "DEEP_MEMORY_DERIVATION", "PROPOSAL_EFFECTIVE_STATE",
        )
        assert {item.family: (item.admitted, item.quarantined, item.unknown, item.not_admitted) for item in report.admission_counts} == {
            "IDENTITY_CHARACTER": (2, 0, 0, 0), "CORE_OBJECT": (3, 0, 0, 0),
            "CORE_RELATIONSHIP": (1, 0, 0, 0), "CORE_EMBEDDING_REPRESENTATION": (1, 0, 0, 0),
            "MOTIF_DERIVATION": (1, 0, 0, 0), "DEEP_MEMORY_DERIVATION": (1, 0, 0, 0),
            "PROPOSAL_EFFECTIVE_STATE": (3, 0, 0, 0),
        }
        assert (report.native_object_count, report.native_relationship_count, report.native_representation_count) == (9, 3, 2)
        assert (report.object_alias_count, report.relationship_alias_count, report.legacy_admission_count, report.semantic_transition_count) == (9, 1, 12, 12)
        assert dict(report.artifact_counts_by_evidence_class) == {
            "LEGACY_ACCELERATION_EVIDENCE": 1,
            "LEGACY_CORE_NODE_EVIDENCE": 1,
            "LEGACY_DEEP_MEMORY_EVIDENCE": 1,
            "LEGACY_EMBEDDING_MANIFEST_EVIDENCE": 1,
            "LEGACY_EMBEDDING_MAP_EVIDENCE": 1,
            "LEGACY_EMBEDDING_NUMERIC_SHARD_EVIDENCE": 1,
            "LEGACY_GOVERNANCE_LEDGER_EVIDENCE": 1,
            "LEGACY_IDENTITY_CHARACTER_EVIDENCE": 3,
            "LEGACY_MEMORY_EVENT_EVIDENCE": 1,
            "LEGACY_MOTIF_EVENT_EVIDENCE": 1,
            "LEGACY_MOTIF_STATE_EVIDENCE": 1,
            "LEGACY_PROPOSAL_EVENT_EVIDENCE": 1,
            "LEGACY_PROPOSAL_STATE_EVIDENCE": 1,
            "LEGACY_RELATIONSHIP_CANDIDATE_EVIDENCE": 1,
            "UNKNOWN": 1,
        }
        assert len(report.coverage) == 17
        assert report.quarantined_or_not_admitted_count == 0
        assert report.active_authorization_count == 0
        assert report.invariant_verification_result is True
        coverage = {item.observed_relative_locator: item.coverage for item in report.coverage}
        assert coverage["closure_ledger.jsonl"] == "EVIDENCE_ONLY"
        assert coverage["legacy_search.sqlite"] == "ACCELERATION_ONLY"
        assert coverage["mystery.capture"] == "UNKNOWN"
        assert coverage["workspaces/orchard/agents/aria/character_state.json"] == "EVIDENCE_ONLY"
        assert coverage["workspaces/orchard/domains/personal/proposal_events.jsonl"] == "EVIDENCE_ONLY"
        assert connection.execute("SELECT count(*) FROM representations WHERE representation_class IN ('LEGACY_EMBEDDING_CAPTURE','LEGACY_DEEP_MEMORY_CAPTURE')").fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM representation_current_state WHERE readiness='READY'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM integrity_expectations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE authority_category='ACTIVE_AUTHORIZATION'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE revision_ordinal<>1").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM relationship_revisions WHERE revision_ordinal<>1").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM semantic_transitions WHERE transition_kind LIKE '%EVENT%'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind IN ('LEGACY_CLOSURE','LEGACY_CONFLICT','LEGACY_DECISION')").fetchone()[0] == 0
        assert _counts(connection) == (9, 9, 3, 3, 2, 9, 1, 12, 12, 12)
    finally:
        qualified.close()


def test_same_and_moved_snapshot_retries_do_not_duplicate_integrated_migration(tmp_path: Path):
    qualified, config = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, "repeatable-source")
        rehearsal = NativeLegacyMigrationRehearsal(connection)
        first = rehearsal.run(snapshot_root=root, manifest_path=manifest_path, config=config)
        first_counts = _counts(connection)
        assert rehearsal.run(snapshot_root=root, manifest_path=manifest_path, config=config) == first
        assert _counts(connection) == first_counts
        moved_capture = tmp_path / "moved-capture"
        shutil.copytree(root.parent, moved_capture)
        moved = rehearsal.run(
            snapshot_root=moved_capture / root.name,
            manifest_path=moved_capture / manifest_path.name,
            config=config,
        )
        assert moved == first
        assert _counts(connection) == first_counts
    finally:
        qualified.close()


def test_mutated_snapshot_stops_before_inventory_or_semantic_admission(tmp_path: Path):
    qualified, config = _database(tmp_path)
    try:
        root, manifest_path, _ = _snapshot(tmp_path, "mutated-source")
        (root / "closure_ledger.jsonl").write_bytes(b"changed after manifest\n")
        with pytest.raises(SubstrateEvidenceIntegrityMismatch):
            NativeLegacyMigrationRehearsal(qualified.connection).run(
                snapshot_root=root, manifest_path=manifest_path, config=config
            )
        assert _counts(qualified.connection) == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        assert qualified.connection.execute("SELECT count(*) FROM legacy_snapshots").fetchone()[0] == 0
    finally:
        qualified.close()


def test_localized_defects_are_contained_without_erasing_good_source_admission(tmp_path: Path):
    qualified, config = _database(tmp_path)
    try:
        connection = qualified.connection
        root, manifest_path, _ = _snapshot(tmp_path, "localized-failure-source", failure=True)
        report = NativeLegacyMigrationRehearsal(connection).run(
            snapshot_root=root, manifest_path=manifest_path, config=config
        )
        families = {item.family: item for item in report.admission_counts}
        assert families["CORE_OBJECT"].admitted == 3
        assert families["CORE_RELATIONSHIP"].quarantined == 1
        assert families["CORE_EMBEDDING_REPRESENTATION"].quarantined == 1
        assert families["MOTIF_DERIVATION"].quarantined == 1
        assert families["DEEP_MEMORY_DERIVATION"].quarantined == 1
        assert families["PROPOSAL_EFFECTIVE_STATE"].admitted == 2
        assert families["PROPOSAL_EFFECTIVE_STATE"].quarantined == 2
        assert report.native_relationship_count == 0
        assert report.native_representation_count == 0
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind='LEGACY_CORE_NODE'").fetchone()[0] == 3
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind='LEGACY_DERIVED_MOTIF'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE authority_category='ACTIVE_AUTHORIZATION'").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM legacy_quarantine_records").fetchone()[0] >= 2
    finally:
        qualified.close()


def test_identity_only_integrated_variant_has_no_hidden_memory_dependency(tmp_path: Path):
    qualified, config = _database(tmp_path)
    try:
        root, manifest_path, _ = _snapshot(tmp_path, "identity-only-source", identity_only=True)
        report = NativeLegacyMigrationRehearsal(qualified.connection).run(
            snapshot_root=root, manifest_path=manifest_path, config=config
        )
        assert report.execution_order == ("IDENTITY_CHARACTER",)
        assert report.native_object_count == 2
        assert report.native_relationship_count == report.native_representation_count == 0
        assert report.active_authorization_count == 0
        assert report.admission_counts[0].admitted == 2
    finally:
        qualified.close()


def test_complete_fixture_keeps_same_eid_separate_across_source_namespaces(tmp_path: Path):
    qualified, config = _database(tmp_path)
    try:
        connection = qualified.connection
        root_one, manifest_one_path, manifest_one = _snapshot(tmp_path, "source-one")
        root_two, manifest_two_path, manifest_two = _snapshot(tmp_path, "source-two")
        rehearsal = NativeLegacyMigrationRehearsal(connection)
        rehearsal.run(snapshot_root=root_one, manifest_path=manifest_one_path, config=config)
        rehearsal.run(snapshot_root=root_two, manifest_path=manifest_two_path, config=config)
        resolver = NativeLegacyObjectAdmissionService(connection)
        object_one = resolver.resolve_legacy_object_alias(
            legacy_source_namespace_id=manifest_one.legacy_source_namespace_id, alias_kind="EID", alias_value="1"
        )
        object_two = resolver.resolve_legacy_object_alias(
            legacy_source_namespace_id=manifest_two.legacy_source_namespace_id, alias_kind="EID", alias_value="1"
        )
        assert object_one != object_two
        assert connection.execute("SELECT count(*) FROM legacy_object_aliases WHERE alias_kind='EID' AND alias_value='1'").fetchone()[0] == 2
    finally:
        qualified.close()
