"""Versioned, read-only capture manifests for frozen legacy evidence.

The manifest is deliberately external to its source tree.  It gives random
UUIDv4 identities durable homes so moving a captured tree never changes its
snapshot or artifact identity.  Its digest is evidence-capture metadata only;
it is not a universal semantic integrity algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
from typing import Final
from uuid import UUID

from ..errors import (
    SubstrateConfigurationError,
    SubstrateEvidenceIntegrityMismatch,
    SubstrateIdentifierError,
    SubstrateSnapshotManifestError,
)
from ..ids import generate_native_id, native_id_from_text, native_id_to_text


SNAPSHOT_MANIFEST_SCHEMA: Final[str] = "TORMENT_LEGACY_SNAPSHOT_MANIFEST"
SNAPSHOT_MANIFEST_VERSION: Final[int] = 1
EVIDENCE_DIGEST_ALGORITHM: Final[str] = "SHA256"
EVIDENCE_DIGEST_ENCODING: Final[str] = "HEX_LOWER"


@dataclass(frozen=True)
class LegacyArtifact:
    """One captured file's evidence identity and observed bytes."""

    artifact_id: UUID
    artifact_class: str
    observed_relative_locator: str
    byte_length: int
    digest_algorithm: str
    digest_hex: str


@dataclass(frozen=True)
class LegacySnapshotManifest:
    """The stable, portable identity record for one already-frozen capture."""

    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    legacy_source_namespace_key: str
    captured_at_ns: int
    artifacts: tuple[LegacyArtifact, ...]
    capture_label: str | None = None


@dataclass(frozen=True)
class SnapshotVerification:
    """Successful verification of all bytes named by one manifest."""

    legacy_snapshot_id: UUID
    verified_artifact_ids: tuple[UUID, ...]
    observed_snapshot_root: Path


def create_snapshot_manifest(
    *,
    snapshot_root: str | Path,
    manifest_path: str | Path,
    legacy_source_namespace_id: UUID,
    legacy_source_namespace_key: str,
    capture_label: str | None = None,
) -> LegacySnapshotManifest:
    """Capture an explicit frozen tree into an external deterministic manifest.

    This function reads source files only.  The caller owns snapshot creation;
    a supplied mutable production path is not treated as a snapshot by magic.
    """
    root = _snapshot_root(snapshot_root)
    destination = _external_manifest_path(manifest_path, root)
    _validate_source_namespace(legacy_source_namespace_id, legacy_source_namespace_key)
    if capture_label is not None and not isinstance(capture_label, str):
        raise SubstrateConfigurationError("snapshot capture label must be a string when supplied")
    if destination.exists():
        raise SubstrateConfigurationError("snapshot manifest destination already exists")

    artifacts = tuple(
        LegacyArtifact(
            artifact_id=generate_native_id(),
            artifact_class=classify_artifact(relative_locator),
            observed_relative_locator=relative_locator,
            byte_length=byte_length,
            digest_algorithm=EVIDENCE_DIGEST_ALGORITHM,
            digest_hex=digest_hex,
        )
        for relative_locator, byte_length, digest_hex in _capture_files(root)
    )
    manifest = LegacySnapshotManifest(
        legacy_snapshot_id=generate_native_id(),
        legacy_source_namespace_id=legacy_source_namespace_id,
        legacy_source_namespace_key=legacy_source_namespace_key,
        captured_at_ns=time.time_ns(),
        artifacts=artifacts,
        capture_label=capture_label,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_manifest_text(manifest), encoding="utf-8", newline="\n")
    return manifest


def load_snapshot_manifest(manifest_path: str | Path) -> LegacySnapshotManifest:
    """Load and validate a manifest without reading any source artifact bytes."""
    path = Path(manifest_path).expanduser().resolve()
    if not path.is_file():
        raise SubstrateSnapshotManifestError("snapshot manifest file was not found")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SubstrateSnapshotManifestError("snapshot manifest is not valid UTF-8 JSON") from exc
    return _manifest_from_data(raw)


def verify_snapshot(
    *, snapshot_root: str | Path, manifest: LegacySnapshotManifest
) -> SnapshotVerification:
    """Read each recorded artifact and fail if any observed bytes changed."""
    root = _snapshot_root(snapshot_root)
    _validate_manifest(manifest)
    mismatches: list[str] = []
    for artifact in manifest.artifacts:
        path = _artifact_path(root, artifact.observed_relative_locator)
        if not path.is_file() or path.is_symlink():
            mismatches.append(f"{artifact.artifact_id}: artifact is missing or is not a regular file")
            continue
        byte_length, digest_hex = _digest_file(path)
        if (
            byte_length != artifact.byte_length
            or artifact.digest_algorithm != EVIDENCE_DIGEST_ALGORITHM
            or digest_hex != artifact.digest_hex
        ):
            mismatches.append(f"{artifact.artifact_id}: evidence digest mismatch")
    if mismatches:
        raise SubstrateEvidenceIntegrityMismatch("; ".join(mismatches))
    return SnapshotVerification(
        legacy_snapshot_id=manifest.legacy_snapshot_id,
        verified_artifact_ids=tuple(artifact.artifact_id for artifact in manifest.artifacts),
        observed_snapshot_root=root,
    )


def classify_artifact(relative_locator: str) -> str:
    """Recognize legacy artifact families only as non-semantic evidence classes."""
    path = PurePosixPath(relative_locator)
    name = path.name.lower()
    parent_names = {part.lower() for part in path.parts[:-1]}
    if name == "nodes.jsonl":
        return "LEGACY_CORE_NODE_EVIDENCE"
    if name == "edges.jsonl":
        return "LEGACY_RELATIONSHIP_CANDIDATE_EVIDENCE"
    if name == "memory_events.jsonl":
        return "LEGACY_MEMORY_EVENT_EVIDENCE"
    if "embeddings" in parent_names and name == "manifest.json":
        return "LEGACY_EMBEDDING_MANIFEST_EVIDENCE"
    if "embeddings" in parent_names and name.endswith(".map.jsonl"):
        return "LEGACY_EMBEDDING_MAP_EVIDENCE"
    if "embeddings" in parent_names and path.suffix.lower() in {
        ".bin",
        ".dat",
        ".f32",
        ".npy",
        ".npz",
    }:
        return "LEGACY_EMBEDDING_NUMERIC_SHARD_EVIDENCE"
    if name in {"motifs.json", "motif_state.json"}:
        return "LEGACY_MOTIF_STATE_EVIDENCE"
    if name in {"motif_events.jsonl", "motifs_events.jsonl"}:
        return "LEGACY_MOTIF_EVENT_EVIDENCE"
    if "deep" in name and "memory" in name:
        return "LEGACY_DEEP_MEMORY_EVIDENCE"
    if "identity" in name or "character" in name:
        return "LEGACY_IDENTITY_CHARACTER_EVIDENCE"
    if any(token in name for token in ("proposal", "closure", "conflict", "ledger")):
        return "LEGACY_GOVERNANCE_LEDGER_EVIDENCE"
    if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        return "LEGACY_ACCELERATION_EVIDENCE"
    return "UNKNOWN"


def _capture_files(root: Path) -> tuple[tuple[str, int, str], ...]:
    captured: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*"), key=lambda candidate: candidate.as_posix()):
        if path.is_symlink():
            raise SubstrateConfigurationError("snapshot source may not contain symlinks")
        if not path.is_file():
            continue
        relative_locator = path.relative_to(root).as_posix()
        byte_length, digest_hex = _digest_file(path)
        captured.append((relative_locator, byte_length, digest_hex))
    return tuple(captured)


def _digest_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    byte_length = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            byte_length += len(chunk)
            digest.update(chunk)
    return byte_length, digest.hexdigest()


def _manifest_text(manifest: LegacySnapshotManifest) -> str:
    _validate_manifest(manifest)
    return json.dumps(_manifest_data(manifest), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _manifest_data(manifest: LegacySnapshotManifest) -> dict[str, object]:
    return {
        "artifacts": [
            {
                "artifact_class": artifact.artifact_class,
                "artifact_id": native_id_to_text(artifact.artifact_id),
                "byte_length": artifact.byte_length,
                "digest": {
                    "algorithm": artifact.digest_algorithm,
                    "encoding": EVIDENCE_DIGEST_ENCODING,
                    "value": artifact.digest_hex,
                },
                "observed_relative_locator": artifact.observed_relative_locator,
            }
            for artifact in manifest.artifacts
        ],
        "capture_metadata": {
            "capture_label": manifest.capture_label,
            "captured_at_ns": manifest.captured_at_ns,
        },
        "legacy_snapshot_id": native_id_to_text(manifest.legacy_snapshot_id),
        "legacy_source_namespace": {
            "legacy_source_namespace_id": native_id_to_text(manifest.legacy_source_namespace_id),
            "source_key": manifest.legacy_source_namespace_key,
        },
        "manifest_schema": SNAPSHOT_MANIFEST_SCHEMA,
        "manifest_version": SNAPSHOT_MANIFEST_VERSION,
    }


def _manifest_from_data(raw: object) -> LegacySnapshotManifest:
    if not isinstance(raw, dict):
        raise SubstrateSnapshotManifestError("snapshot manifest root must be an object")
    if raw.get("manifest_schema") != SNAPSHOT_MANIFEST_SCHEMA or raw.get(
        "manifest_version"
    ) != SNAPSHOT_MANIFEST_VERSION:
        raise SubstrateSnapshotManifestError("snapshot manifest schema version is incompatible")
    try:
        source = raw["legacy_source_namespace"]
        metadata = raw["capture_metadata"]
        artifacts_raw = raw["artifacts"]
        if not isinstance(source, dict) or not isinstance(metadata, dict) or not isinstance(artifacts_raw, list):
            raise TypeError
        artifacts = tuple(_artifact_from_data(item) for item in artifacts_raw)
        manifest = LegacySnapshotManifest(
            legacy_snapshot_id=native_id_from_text(_required_text(raw, "legacy_snapshot_id")),
            legacy_source_namespace_id=native_id_from_text(
                _required_text(source, "legacy_source_namespace_id")
            ),
            legacy_source_namespace_key=_required_text(source, "source_key"),
            captured_at_ns=_required_nonnegative_int(metadata, "captured_at_ns"),
            artifacts=artifacts,
            capture_label=_optional_text(metadata, "capture_label"),
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        SubstrateIdentifierError,
        SubstrateSnapshotManifestError,
    ) as exc:
        if isinstance(exc, SubstrateSnapshotManifestError):
            raise
        raise SubstrateSnapshotManifestError("snapshot manifest fields are malformed") from exc
    _validate_manifest(manifest)
    return manifest


def _artifact_from_data(raw: object) -> LegacyArtifact:
    if not isinstance(raw, dict):
        raise SubstrateSnapshotManifestError("snapshot artifact must be an object")
    digest = raw.get("digest")
    if not isinstance(digest, dict) or digest.get("encoding") != EVIDENCE_DIGEST_ENCODING:
        raise SubstrateSnapshotManifestError("snapshot artifact digest encoding is incompatible")
    artifact = LegacyArtifact(
        artifact_id=native_id_from_text(_required_text(raw, "artifact_id")),
        artifact_class=_required_text(raw, "artifact_class"),
        observed_relative_locator=_required_text(raw, "observed_relative_locator"),
        byte_length=_required_nonnegative_int(raw, "byte_length"),
        digest_algorithm=_required_text(digest, "algorithm"),
        digest_hex=_required_text(digest, "value"),
    )
    _validate_artifact(artifact)
    return artifact


def _validate_manifest(manifest: LegacySnapshotManifest) -> None:
    _validate_source_namespace(
        manifest.legacy_source_namespace_id, manifest.legacy_source_namespace_key
    )
    if not isinstance(manifest.captured_at_ns, int) or isinstance(manifest.captured_at_ns, bool) or manifest.captured_at_ns < 0:
        raise SubstrateSnapshotManifestError("snapshot capture timestamp is invalid")
    if manifest.capture_label is not None and not isinstance(manifest.capture_label, str):
        raise SubstrateSnapshotManifestError("snapshot capture label is invalid")
    if len({artifact.artifact_id for artifact in manifest.artifacts}) != len(manifest.artifacts):
        raise SubstrateSnapshotManifestError("snapshot manifest has duplicate artifact identities")
    if len({artifact.observed_relative_locator for artifact in manifest.artifacts}) != len(manifest.artifacts):
        raise SubstrateSnapshotManifestError("snapshot manifest has duplicate artifact locators")
    for artifact in manifest.artifacts:
        _validate_artifact(artifact)


def _validate_source_namespace(namespace_id: UUID, source_key: str) -> None:
    try:
        native_id_to_text(namespace_id)
    except Exception as exc:
        raise SubstrateSnapshotManifestError("legacy source namespace identity is invalid") from exc
    if not isinstance(source_key, str) or not source_key:
        raise SubstrateSnapshotManifestError("legacy source namespace key must be non-empty")


def _validate_artifact(artifact: LegacyArtifact) -> None:
    try:
        native_id_to_text(artifact.artifact_id)
    except Exception as exc:
        raise SubstrateSnapshotManifestError("legacy artifact identity is invalid") from exc
    if not isinstance(artifact.artifact_class, str) or not artifact.artifact_class:
        raise SubstrateSnapshotManifestError("legacy artifact class must be non-empty")
    _relative_locator(artifact.observed_relative_locator)
    if not isinstance(artifact.byte_length, int) or isinstance(artifact.byte_length, bool) or artifact.byte_length < 0:
        raise SubstrateSnapshotManifestError("legacy artifact byte length is invalid")
    if artifact.digest_algorithm != EVIDENCE_DIGEST_ALGORITHM:
        raise SubstrateSnapshotManifestError("legacy artifact digest algorithm is incompatible")
    if len(artifact.digest_hex) != hashlib.sha256().digest_size * 2 or any(
        character not in "0123456789abcdef" for character in artifact.digest_hex
    ):
        raise SubstrateSnapshotManifestError("legacy artifact digest must be lowercase SHA256 hex")


def _snapshot_root(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir() or root.is_symlink():
        raise SubstrateConfigurationError("an explicit non-symlink frozen snapshot directory is required")
    return root


def _external_manifest_path(value: str | Path, root: Path) -> Path:
    destination = Path(value).expanduser().resolve()
    if destination.suffix.lower() != ".json":
        raise SubstrateConfigurationError("snapshot manifest destination must be a JSON file")
    if destination == root or root in destination.parents:
        raise SubstrateConfigurationError("snapshot manifest must be stored outside the source snapshot tree")
    return destination


def _artifact_path(root: Path, relative_locator: str) -> Path:
    relative = _relative_locator(relative_locator)
    path = (root / relative).resolve()
    if root not in path.parents:
        raise SubstrateSnapshotManifestError("snapshot artifact locator escapes the source root")
    return path


def _relative_locator(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise SubstrateSnapshotManifestError("snapshot artifact locator must be non-empty")
    locator = PurePosixPath(value)
    if locator.is_absolute() or ".." in locator.parts or str(locator) in {".", ""}:
        raise SubstrateSnapshotManifestError("snapshot artifact locator must be relative")
    return locator


def _required_text(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise SubstrateSnapshotManifestError(f"snapshot manifest {key} must be non-empty text")
    return value


def _optional_text(mapping: dict[str, object], key: str) -> str | None:
    value = mapping.get(key)
    if value is not None and not isinstance(value, str):
        raise SubstrateSnapshotManifestError(f"snapshot manifest {key} must be text or null")
    return value


def _required_nonnegative_int(mapping: dict[str, object], key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise SubstrateSnapshotManifestError(f"snapshot manifest {key} must be non-negative integer")
    return value
