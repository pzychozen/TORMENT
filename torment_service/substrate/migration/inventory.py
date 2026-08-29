"""Evidence-only persistence for validated legacy snapshot manifests.

No function here creates objects, revisions, relationships, representations,
aliases, operations, semantic transitions, admission records, or quarantine.
It persists only the existing frozen legacy source/snapshot/artifact tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from uuid import UUID

from ..errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from ..ids import native_id_from_bytes, native_id_to_bytes
from ..schema import open_schema
from .snapshot import LegacyArtifact, LegacySnapshotManifest, load_snapshot_manifest, verify_snapshot


@dataclass(frozen=True)
class InventoryArtifact:
    artifact_id: UUID
    artifact_class: str
    artifact_identity: str
    observed_relative_locator: str
    byte_length: int | None
    digest_algorithm: str
    digest_hex: str


@dataclass(frozen=True)
class InventorySnapshot:
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    legacy_source_namespace_key: str
    snapshot_identity: str
    artifacts: tuple[InventoryArtifact, ...]
    observed_snapshot_root: Path | None = None


def inventory_snapshot(
    connection: sqlite3.Connection,
    *,
    snapshot_root: str | Path,
    manifest_path: str | Path,
) -> InventorySnapshot:
    """Verify a supplied frozen snapshot, then idempotently persist evidence facts."""
    manifest = load_snapshot_manifest(manifest_path)
    verification = verify_snapshot(snapshot_root=snapshot_root, manifest=manifest)
    open_schema(connection)
    connection.execute("BEGIN IMMEDIATE")
    try:
        _ensure_source_namespace(connection, manifest)
        _ensure_snapshot(connection, manifest)
        for artifact in manifest.artifacts:
            _ensure_artifact(connection, manifest, artifact)
        result = _get_inventory(connection, manifest.legacy_snapshot_id)
        connection.execute("COMMIT")
    except Exception:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise
    return InventorySnapshot(
        legacy_snapshot_id=result.legacy_snapshot_id,
        legacy_source_namespace_id=result.legacy_source_namespace_id,
        legacy_source_namespace_key=result.legacy_source_namespace_key,
        snapshot_identity=result.snapshot_identity,
        artifacts=_with_manifest_lengths(result.artifacts, manifest),
        observed_snapshot_root=verification.observed_snapshot_root,
    )


def get_inventory(connection: sqlite3.Connection, legacy_snapshot_id: UUID) -> InventorySnapshot:
    """Read persisted evidence facts only; no source scan or semantic replay occurs."""
    open_schema(connection)
    return _get_inventory(connection, legacy_snapshot_id)


def _get_inventory(connection: sqlite3.Connection, legacy_snapshot_id: UUID) -> InventorySnapshot:
    snapshot_id = native_id_to_bytes(legacy_snapshot_id)
    snapshot = connection.execute(
        """
        SELECT s.legacy_snapshot_id,s.legacy_source_namespace_id,n.source_key,s.snapshot_identity
        FROM legacy_snapshots s
        JOIN legacy_source_namespaces n USING(legacy_source_namespace_id)
        WHERE s.legacy_snapshot_id=?
        """,
        (snapshot_id,),
    ).fetchone()
    if snapshot is None:
        raise SubstrateObjectNotFound("legacy evidence snapshot was not found")
    artifacts = tuple(
        InventoryArtifact(
            artifact_id=native_id_from_bytes(row[0]),
            artifact_class=row[1],
            artifact_identity=row[2],
            observed_relative_locator=row[3],
            byte_length=None,
            digest_algorithm=row[4],
            digest_hex=bytes(row[5]).hex(),
        )
        for row in connection.execute(
            """
            SELECT legacy_artifact_id,artifact_kind,artifact_identity,observed_locator,
                   digest_algorithm,digest_value
            FROM legacy_artifacts
            WHERE legacy_snapshot_id=?
            ORDER BY artifact_identity
            """,
            (snapshot_id,),
        )
    )
    return InventorySnapshot(
        legacy_snapshot_id=native_id_from_bytes(snapshot[0]),
        legacy_source_namespace_id=native_id_from_bytes(snapshot[1]),
        legacy_source_namespace_key=snapshot[2],
        snapshot_identity=snapshot[3],
        artifacts=artifacts,
    )


def _ensure_source_namespace(connection: sqlite3.Connection, manifest: LegacySnapshotManifest) -> None:
    expected_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
    row = connection.execute(
        "SELECT legacy_source_namespace_id FROM legacy_source_namespaces WHERE source_key=?",
        (manifest.legacy_source_namespace_key,),
    ).fetchone()
    if row is None:
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (expected_id, manifest.legacy_source_namespace_key),
        )
    elif row[0] != expected_id:
        raise SubstrateInvariantViolation("legacy source namespace key resolves to another identity")


def _ensure_snapshot(connection: sqlite3.Connection, manifest: LegacySnapshotManifest) -> None:
    snapshot_id = native_id_to_bytes(manifest.legacy_snapshot_id)
    namespace_id = native_id_to_bytes(manifest.legacy_source_namespace_id)
    identity = _snapshot_identity(manifest)
    row = connection.execute(
        "SELECT legacy_source_namespace_id,snapshot_identity FROM legacy_snapshots WHERE legacy_snapshot_id=?",
        (snapshot_id,),
    ).fetchone()
    if row is None:
        connection.execute(
            "INSERT INTO legacy_snapshots VALUES (?,?,?,?)",
            (snapshot_id, namespace_id, identity, manifest.captured_at_ns),
        )
    elif row != (namespace_id, identity):
        raise SubstrateInvariantViolation("legacy snapshot identity does not match its manifest")


def _ensure_artifact(
    connection: sqlite3.Connection, manifest: LegacySnapshotManifest, artifact: LegacyArtifact
) -> None:
    artifact_id = native_id_to_bytes(artifact.artifact_id)
    expected = (
        native_id_to_bytes(manifest.legacy_snapshot_id),
        _artifact_identity(artifact),
        artifact.artifact_class,
        artifact.observed_relative_locator,
        artifact.digest_algorithm,
        bytes.fromhex(artifact.digest_hex),
    )
    row = connection.execute(
        """
        SELECT legacy_snapshot_id,artifact_identity,artifact_kind,observed_locator,
               digest_algorithm,digest_value
        FROM legacy_artifacts WHERE legacy_artifact_id=?
        """,
        (artifact_id,),
    ).fetchone()
    if row is None:
        connection.execute(
            """
            INSERT INTO legacy_artifacts(
                legacy_artifact_id,legacy_snapshot_id,artifact_identity,artifact_kind,
                observed_locator,digest_algorithm,digest_value,retained_bytes
            ) VALUES (?,?,?,?,?,?,?,NULL)
            """,
            (artifact_id, *expected),
        )
    elif row != expected:
        raise SubstrateInvariantViolation("legacy artifact identity does not match its manifest")


def _snapshot_identity(manifest: LegacySnapshotManifest) -> str:
    return f"TMS-LEGACY-SNAPSHOT-1:{manifest.legacy_snapshot_id}"


def _artifact_identity(artifact: LegacyArtifact) -> str:
    return f"TMS-LEGACY-ARTIFACT-1:{artifact.artifact_id}"


def _with_manifest_lengths(
    artifacts: tuple[InventoryArtifact, ...], manifest: LegacySnapshotManifest
) -> tuple[InventoryArtifact, ...]:
    lengths = {artifact.artifact_id: artifact.byte_length for artifact in manifest.artifacts}
    return tuple(
        InventoryArtifact(
            artifact_id=artifact.artifact_id,
            artifact_class=artifact.artifact_class,
            artifact_identity=artifact.artifact_identity,
            observed_relative_locator=artifact.observed_relative_locator,
            byte_length=lengths[artifact.artifact_id],
            digest_algorithm=artifact.digest_algorithm,
            digest_hex=artifact.digest_hex,
        )
        for artifact in artifacts
    )
