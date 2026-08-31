"""Immutable L0 file and retained-side-store fingerprinting."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .protocol import D1ProtocolError, canonical_json, sha256_value


CHARACTER_BASELINE_PROFILE = "CHARACTER_BEARING"
CORE_CHARACTER_FREE_BASELINE_PROFILE = "CORE_CHARACTER_FREE"


@dataclass(frozen=True)
class FileManifestEntry:
    relative_path: str
    byte_length: int
    sha256: str


@dataclass(frozen=True)
class JsonEvidence:
    relative_path: str
    sha256: str
    value: dict[str, Any]


@dataclass(frozen=True)
class LegacyBaselineFingerprint:
    root: str
    workspace_id: str
    agent_id: str
    baseline_profile: str
    files: tuple[FileManifestEntry, ...]
    workspace_embedding_lock: JsonEvidence
    identity: JsonEvidence
    character_seed: JsonEvidence | None
    character_state: JsonEvidence | None
    private_memory_rows_sha256: str
    embedding_evidence_sha256: str
    motif_state_sha256: str
    retained_side_store_inventory: tuple[tuple[str, str], ...]

    @property
    def digest(self) -> str:
        return sha256_value(asdict(self))


def recursive_file_manifest(root: str | Path) -> tuple[FileManifestEntry, ...]:
    base = Path(root).resolve()
    if not base.is_dir():
        raise D1ProtocolError("baseline root must exist and be a directory")
    entries: list[FileManifestEntry] = []
    for path in sorted(base.rglob("*")):
        if path.is_symlink():
            raise D1ProtocolError(f"baseline contains a symlink: {path}")
        if not path.is_file():
            continue
        payload = path.read_bytes()
        entries.append(FileManifestEntry(path.relative_to(base).as_posix(), len(payload), hashlib.sha256(payload).hexdigest()))
    return tuple(entries)


def _json_evidence(root: Path, relative_path: str) -> JsonEvidence:
    path = root / relative_path
    if not path.is_file():
        raise D1ProtocolError(f"required baseline evidence is absent: {relative_path}")
    payload = path.read_bytes()
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise D1ProtocolError(f"required baseline evidence is invalid JSON: {relative_path}") from exc
    if not isinstance(decoded, dict):
        raise D1ProtocolError(f"required baseline evidence is not an object: {relative_path}")
    return JsonEvidence(relative_path, hashlib.sha256(payload).hexdigest(), decoded)


def _combined_hash(entries: tuple[FileManifestEntry, ...], predicate) -> str:
    selected = [(entry.relative_path, entry.sha256) for entry in entries if predicate(entry.relative_path)]
    if not selected:
        raise D1ProtocolError("baseline lacks required evidence family")
    return sha256_value(selected)


def fingerprint_legacy_baseline(
    *,
    root: str | Path,
    workspace_id: str,
    agent_id: str,
    domain_id: str = "research",
    character_seed_required: bool = True,
) -> LegacyBaselineFingerprint:
    """Fingerprint a cleanly stopped, dedicated legacy L0 data root.

    This only reads regular files.  The complete recursive manifest catches any
    side store not named by the structured evidence summaries below.
    """
    if not all(isinstance(value, str) and value for value in (workspace_id, agent_id, domain_id)):
        raise D1ProtocolError("baseline workspace, agent, and domain IDs are required")
    base = Path(root).resolve()
    files = recursive_file_manifest(base)
    prefix = f"workspaces/{workspace_id}/"
    workspace_lock = _json_evidence(base, prefix + "workspace_meta.json")
    identity = _json_evidence(base, prefix + f"agents/{agent_id}/identity.json")
    seed = identity.value.get("seed", {})
    character_seed: JsonEvidence | None = None
    character_state: JsonEvidence | None = None
    if character_seed_required:
        seed_id = seed.get("seed_id") if isinstance(seed, dict) else None
        if not isinstance(seed_id, str) or not seed_id:
            raise D1ProtocolError("identity has no frozen Character seed ID")
        character_seed = _json_evidence(base, prefix + f"seeds/{seed_id}/seed.json")
        character_state = _json_evidence(base, prefix + f"agents/{agent_id}/character_state.json")
        baseline_profile = CHARACTER_BASELINE_PROFILE
    else:
        if not isinstance(seed, dict):
            raise D1ProtocolError("Character-free core identity seed carrier is malformed")
        if any(str(seed.get(key, "") or "").strip() for key in ("seed_id", "seed_text", "character_name")):
            raise D1ProtocolError("Character-free core baseline contains active Character seed evidence")
        if (base / (prefix + f"agents/{agent_id}/character_state.json")).exists() or (base / (prefix + "seeds")).exists():
            raise D1ProtocolError("Character-free core baseline contains Character planting artifacts")
        baseline_profile = CORE_CHARACTER_FREE_BASELINE_PROFILE
    private_prefix = prefix + f"agents/{agent_id}/private/"
    domain_prefix = prefix + f"domains/{domain_id}/"
    private_rows = _combined_hash(files, lambda path: path == private_prefix + "nodes.jsonl")
    embedding_evidence = _combined_hash(files, lambda path: path.startswith(private_prefix + "embeddings/"))
    motif_state = _combined_hash(files, lambda path: path == domain_prefix + "motifs.json")
    retained = tuple(
        (entry.relative_path, entry.sha256)
        for entry in files
        if entry.relative_path.startswith(prefix)
        and not entry.relative_path.startswith(private_prefix)
        and not entry.relative_path.startswith(domain_prefix + "shared/")
        and entry.relative_path not in {
            workspace_lock.relative_path,
            identity.relative_path,
            *(value.relative_path for value in (character_seed, character_state) if value is not None),
        }
    )
    return LegacyBaselineFingerprint(
        root=str(base), workspace_id=workspace_id, agent_id=agent_id,
        baseline_profile=baseline_profile, files=files,
        workspace_embedding_lock=workspace_lock, identity=identity,
        character_seed=character_seed, character_state=character_state,
        private_memory_rows_sha256=private_rows,
        embedding_evidence_sha256=embedding_evidence,
        motif_state_sha256=motif_state,
        retained_side_store_inventory=retained,
    )


def verify_legacy_baseline(fingerprint: LegacyBaselineFingerprint) -> None:
    current = fingerprint_legacy_baseline(
        root=fingerprint.root, workspace_id=fingerprint.workspace_id, agent_id=fingerprint.agent_id,
        character_seed_required=(fingerprint.baseline_profile == CHARACTER_BASELINE_PROFILE),
    )
    if current.digest != fingerprint.digest:
        raise D1ProtocolError("L0 bytes changed after its baseline fingerprint was frozen")
