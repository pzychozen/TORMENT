"""Focused Phase 7F1 synthetic legacy snapshot evidence tests."""

from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3

import pytest

from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import (
    SubstrateConfigurationError,
    SubstrateEvidenceIntegrityMismatch,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    create_snapshot_manifest,
    get_inventory,
    inventory_snapshot,
    load_snapshot_manifest,
    verify_snapshot,
)
from torment_service.substrate.migration.snapshot import EVIDENCE_DIGEST_ALGORITHM
from torment_service.substrate.schema import create_schema


def _fixture_tree(tmp_path: Path) -> tuple[Path, Path, object, str]:
    capture = tmp_path / "captured-evidence"
    root = capture / "legacy-snapshot"
    root.mkdir(parents=True)
    files: dict[str, bytes] = {
        "nodes.jsonl": b'{"eid":"n-1","text":"not semantic truth"}\n',
        "edges.jsonl": b'{"source":"n-1","target":"n-2"}\n',
        "memory_events.jsonl": b'{"event":"MEMORY_CREATE"}\n',
        "embeddings/manifest.json": b'{"model":"legacy"}\n',
        "embeddings/shard_000000.map.jsonl": b'{"eid":"n-1","offset":0}\n',
        "embeddings/shard_000000.bin": b"\x00\x01\x02\x03",
        "motifs.json": b'{"motifs":[]}\n',
        "motif_events.jsonl": b'{"event":"MOTIF"}\n',
        "deep_memory_records.jsonl": b'{malformed evidence remains captured\n',
        "character_state.json": b'{"character":"legacy"}\n',
        "proposal_ledger.json": b'{"proposal":"uninterpreted"}\n',
        "accelerator.sqlite": b"SQLite evidence bytes, not an opened database",
        "misc/unrecognized.asset": b"unknown bytes survive inventory",
    }
    for locator, contents in files.items():
        path = root / locator
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    return root, capture / "snapshot-manifest.json", generate_native_id(), "synthetic-fixture-source"


def _source_fingerprint(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "native-evidence.db")
    create_schema(qualified.connection)
    return qualified


def _manifest(root: Path, manifest_path: Path, namespace_id, source_key: str):
    return create_snapshot_manifest(
        snapshot_root=root,
        manifest_path=manifest_path,
        legacy_source_namespace_id=namespace_id,
        legacy_source_namespace_key=source_key,
        capture_label="synthetic pytest evidence only",
    )


def test_manifest_roundtrip_classifies_known_and_unknown_evidence_without_source_writes(tmp_path: Path):
    root, manifest_path, namespace_id, source_key = _fixture_tree(tmp_path)
    before = _source_fingerprint(root)
    manifest = _manifest(root, manifest_path, namespace_id, source_key)
    loaded = load_snapshot_manifest(manifest_path)
    verification = verify_snapshot(snapshot_root=root, manifest=loaded)
    expected_classes = {
        "nodes.jsonl": "LEGACY_CORE_NODE_EVIDENCE",
        "edges.jsonl": "LEGACY_RELATIONSHIP_CANDIDATE_EVIDENCE",
        "memory_events.jsonl": "LEGACY_MEMORY_EVENT_EVIDENCE",
        "embeddings/manifest.json": "LEGACY_EMBEDDING_MANIFEST_EVIDENCE",
        "embeddings/shard_000000.map.jsonl": "LEGACY_EMBEDDING_MAP_EVIDENCE",
        "embeddings/shard_000000.bin": "LEGACY_EMBEDDING_NUMERIC_SHARD_EVIDENCE",
        "motifs.json": "LEGACY_MOTIF_STATE_EVIDENCE",
        "motif_events.jsonl": "LEGACY_MOTIF_EVENT_EVIDENCE",
        "deep_memory_records.jsonl": "LEGACY_DEEP_MEMORY_EVIDENCE",
        "character_state.json": "LEGACY_IDENTITY_CHARACTER_EVIDENCE",
        "proposal_ledger.json": "LEGACY_GOVERNANCE_LEDGER_EVIDENCE",
        "accelerator.sqlite": "LEGACY_ACCELERATION_EVIDENCE",
        "misc/unrecognized.asset": "UNKNOWN",
    }
    assert loaded == manifest
    assert verification.legacy_snapshot_id == manifest.legacy_snapshot_id
    assert verification.observed_snapshot_root == root.resolve()
    assert {artifact.observed_relative_locator: artifact.artifact_class for artifact in manifest.artifacts} == expected_classes
    assert {artifact.digest_algorithm for artifact in manifest.artifacts} == {EVIDENCE_DIGEST_ALGORITHM}
    assert all(artifact.byte_length >= 0 for artifact in manifest.artifacts)
    assert not manifest_path.is_relative_to(root)
    assert _source_fingerprint(root) == before


def test_inventory_is_idempotent_evidence_only_and_keeps_namespace_distinct(tmp_path: Path):
    root, manifest_path, namespace_id, source_key = _fixture_tree(tmp_path)
    manifest = _manifest(root, manifest_path, namespace_id, source_key)
    before = _source_fingerprint(root)
    qualified = _database(tmp_path)
    try:
        connection = qualified.connection
        first = inventory_snapshot(connection, snapshot_root=root, manifest_path=manifest_path)
        second = inventory_snapshot(connection, snapshot_root=root, manifest_path=manifest_path)
        stored = get_inventory(connection, manifest.legacy_snapshot_id)
        assert first == second
        assert first.legacy_snapshot_id == manifest.legacy_snapshot_id
        assert first.legacy_source_namespace_id == namespace_id
        assert first.observed_snapshot_root == root.resolve()
        assert len(first.artifacts) == len(manifest.artifacts)
        assert {artifact.artifact_id for artifact in first.artifacts} == {
            artifact.artifact_id for artifact in manifest.artifacts
        }
        assert {artifact.byte_length for artifact in first.artifacts} == {
            artifact.byte_length for artifact in manifest.artifacts
        }
        assert all(artifact.byte_length is None for artifact in stored.artifacts)
        assert connection.execute("SELECT count(*) FROM legacy_snapshots").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM legacy_artifacts").fetchone()[0] == len(manifest.artifacts)
        identity_namespace, semantic_scope = generate_native_id(), generate_native_id()
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(identity_namespace), "unrelated-identity-namespace"),
        )
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(semantic_scope), "unrelated-semantic-scope"),
        )
        assert len({namespace_id, identity_namespace, semantic_scope}) == 3
        assert connection.execute("SELECT legacy_source_namespace_id FROM legacy_source_namespaces").fetchone()[0] == native_id_to_bytes(namespace_id)
        for table in (
            "objects",
            "object_revisions",
            "relationships",
            "relationship_revisions",
            "representations",
            "semantic_transitions",
            "legacy_admission_batches",
            "legacy_admission_records",
            "legacy_admission_effects",
            "legacy_object_aliases",
            "legacy_relationship_aliases",
        ):
            assert connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
        assert _source_fingerprint(root) == before
    finally:
        qualified.close()


def test_moved_snapshot_reuses_manifest_snapshot_and_artifact_identities(tmp_path: Path):
    root, manifest_path, namespace_id, source_key = _fixture_tree(tmp_path)
    manifest = _manifest(root, manifest_path, namespace_id, source_key)
    moved_capture = tmp_path / "preserved-copy"
    shutil.copytree(root.parent, moved_capture)
    moved_root = moved_capture / root.name
    moved_manifest = moved_capture / manifest_path.name
    qualified = _database(tmp_path)
    try:
        first = inventory_snapshot(
            qualified.connection, snapshot_root=root, manifest_path=manifest_path
        )
        moved = inventory_snapshot(
            qualified.connection, snapshot_root=moved_root, manifest_path=moved_manifest
        )
        assert load_snapshot_manifest(moved_manifest) == manifest
        assert first.legacy_snapshot_id == moved.legacy_snapshot_id == manifest.legacy_snapshot_id
        assert {artifact.artifact_id for artifact in first.artifacts} == {
            artifact.artifact_id for artifact in moved.artifacts
        }
        assert {artifact.digest_hex for artifact in first.artifacts} == {
            artifact.digest_hex for artifact in moved.artifacts
        }
        assert first.observed_snapshot_root != moved.observed_snapshot_root
        assert qualified.connection.execute("SELECT count(*) FROM legacy_snapshots").fetchone()[0] == 1
        assert qualified.connection.execute("SELECT count(*) FROM legacy_artifacts").fetchone()[0] == len(manifest.artifacts)
    finally:
        qualified.close()


def test_mutated_evidence_fails_before_inventory_can_persist_it(tmp_path: Path):
    root, manifest_path, namespace_id, source_key = _fixture_tree(tmp_path)
    _manifest(root, manifest_path, namespace_id, source_key)
    (root / "nodes.jsonl").write_bytes(b'{"changed":"digest must not be blessed"}\n')
    qualified = _database(tmp_path)
    try:
        with pytest.raises(SubstrateEvidenceIntegrityMismatch, match="evidence digest mismatch"):
            inventory_snapshot(qualified.connection, snapshot_root=root, manifest_path=manifest_path)
        assert qualified.connection.execute("SELECT count(*) FROM legacy_snapshots").fetchone()[0] == 0
        assert qualified.connection.execute("SELECT count(*) FROM legacy_artifacts").fetchone()[0] == 0
        assert qualified.connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0] == 0
    finally:
        qualified.close()


def test_capture_requires_external_manifest_and_h7_admission_is_not_exposed(tmp_path: Path):
    root, _, namespace_id, source_key = _fixture_tree(tmp_path)
    with pytest.raises(SubstrateConfigurationError, match="outside the source snapshot tree"):
        _manifest(root, root / "forbidden-manifest.json", namespace_id, source_key)
    import torment_service.substrate.migration as migration

    assert not {
        "admit_legacy",
        "admit_legacy_snapshot",
        "resolve_legacy_eid",
        "create_legacy_alias",
    } & set(dir(migration))
