"""Owner-bounded explicit source evidence for generalized root admission.

The manifest names only declared sources.  It intentionally has no recursive
workspace walk and creates no snapshot, core, selector, admission, or durable
scope record.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Final

from torment_service.pathing import safe_join, validate_structural_path_component

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateConfigurationError, SubstrateEvidenceIntegrityMismatch
from .root_scope import RootScopeKey, RootScopeKind


EXPLICIT_SOURCE_MANIFEST_SCHEMA: Final[str] = "TORMENT_ROOT_EXPLICIT_SOURCE_MANIFEST"
EXPLICIT_SOURCE_MANIFEST_VERSION: Final[int] = 1
_SHA256_HEX_LENGTH: Final[int] = 64


class SourceOwnerClass(StrEnum):
    WORKSPACE_IDENTITY_METADATA = "WORKSPACE_IDENTITY_METADATA"
    DOMAIN_DECLARATION = "DOMAIN_DECLARATION"
    DOMAIN_POLICY = "DOMAIN_POLICY"
    BRIDGE_OWNER_EVIDENCE = "BRIDGE_OWNER_EVIDENCE"
    PRIVATE_GRAPH_SOURCE = "PRIVATE_GRAPH_SOURCE"
    SHARED_GRAPH_SOURCE = "SHARED_GRAPH_SOURCE"
    EMBEDDING_MANIFEST = "EMBEDDING_MANIFEST"
    EMBEDDING_SHARD_OR_MAP = "EMBEDDING_SHARD_OR_MAP"
    LEGACY_REPRESENTATION_ARTIFACT = "LEGACY_REPRESENTATION_ARTIFACT"
    METADATA_LESS_PER_EID_LEGACY_REPRESENTATION = (
        "METADATA_LESS_PER_EID_LEGACY_REPRESENTATION"
    )
    MOTIF_SOURCE = "MOTIF_SOURCE"
    EXTERNAL_OWNER_OBSERVATION = "EXTERNAL_OWNER_OBSERVATION"


class EvidenceSemanticRole(StrEnum):
    WORKSPACE_META = "WORKSPACE_META"
    DOMAINS = "DOMAINS"
    DOMAIN_POLICY = "DOMAIN_POLICY"
    BRIDGES = "BRIDGES"
    NODES = "NODES"
    EDGES = "EDGES"
    EMBEDDING_MANIFEST = "EMBEDDING_MANIFEST"
    EMBEDDING_SHARD_OR_MAP = "EMBEDDING_SHARD_OR_MAP"
    LEGACY_REPRESENTATION = "LEGACY_REPRESENTATION"
    MOTIFS = "MOTIFS"
    EXTERNAL_OBSERVATION = "EXTERNAL_OBSERVATION"


class EvidenceOwnerBoundaryKind(StrEnum):
    WORKSPACE = "WORKSPACE"
    AGENT = "AGENT"
    DOMAIN = "DOMAIN"
    PRIVATE_SCOPE = "PRIVATE_SCOPE"
    SHARED_SCOPE = "SHARED_SCOPE"


class EvidencePresenceExpectation(StrEnum):
    EXPECTED_PRESENT = "EXPECTED_PRESENT"
    EXPECTED_ABSENT = "EXPECTED_ABSENT"


class EvidenceAbsenceReason(StrEnum):
    EMPTY_GRAPH = "EMPTY_GRAPH"
    UNMATERIALIZED_DECLARATION = "UNMATERIALIZED_DECLARATION"
    METADATA_LESS_SOURCE_SHAPE = "METADATA_LESS_SOURCE_SHAPE"
    OPTIONAL_EDGE_SOURCE = "OPTIONAL_EDGE_SOURCE"


class ExplicitSourceEvidenceError(SubstrateConfigurationError):
    """Raised for malformed or unsafe explicit source-manifest input."""


class ExplicitSourceEvidenceDrift(SubstrateEvidenceIntegrityMismatch):
    """Raised when a declared present or absent source no longer matches."""


@dataclass(frozen=True)
class EvidenceOwnerBoundary:
    """A canonical owner root under ``data_root/workspaces/<workspace_id>``."""

    workspace_id: str
    boundary_kind: EvidenceOwnerBoundaryKind
    agent_id: str | None = None
    domain_id: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.workspace_id, "workspace_id")
        if not isinstance(self.boundary_kind, EvidenceOwnerBoundaryKind):
            raise ExplicitSourceEvidenceError("boundary_kind must be EvidenceOwnerBoundaryKind")
        if self.boundary_kind in {EvidenceOwnerBoundaryKind.AGENT, EvidenceOwnerBoundaryKind.PRIVATE_SCOPE}:
            _identifier(self.agent_id, "agent_id")
            if self.domain_id is not None:
                raise ExplicitSourceEvidenceError("agent/private boundary forbids domain_id")
        elif self.boundary_kind in {EvidenceOwnerBoundaryKind.DOMAIN, EvidenceOwnerBoundaryKind.SHARED_SCOPE}:
            _identifier(self.domain_id, "domain_id")
            if self.agent_id is not None:
                raise ExplicitSourceEvidenceError("domain/shared boundary forbids agent_id")
        elif self.agent_id is not None or self.domain_id is not None:
            raise ExplicitSourceEvidenceError("workspace boundary forbids agent_id and domain_id")

    @property
    def scope_key(self) -> RootScopeKey | None:
        if self.boundary_kind is EvidenceOwnerBoundaryKind.PRIVATE_SCOPE:
            return RootScopeKey(self.workspace_id, RootScopeKind.PRIVATE, agent_id=self.agent_id)
        if self.boundary_kind is EvidenceOwnerBoundaryKind.SHARED_SCOPE:
            return RootScopeKey(self.workspace_id, RootScopeKind.SHARED, domain_id=self.domain_id)
        return None

    @property
    def relative_parts(self) -> tuple[str, ...]:
        if self.boundary_kind is EvidenceOwnerBoundaryKind.WORKSPACE:
            return ("workspaces", self.workspace_id)
        if self.boundary_kind is EvidenceOwnerBoundaryKind.AGENT:
            return ("workspaces", self.workspace_id, "agents", self.agent_id or "")
        if self.boundary_kind is EvidenceOwnerBoundaryKind.DOMAIN:
            return ("workspaces", self.workspace_id, "domains", self.domain_id or "")
        if self.boundary_kind is EvidenceOwnerBoundaryKind.PRIVATE_SCOPE:
            return ("workspaces", self.workspace_id, "agents", self.agent_id or "", "private")
        return ("workspaces", self.workspace_id, "domains", self.domain_id or "", "shared")

    @property
    def canonical_key(self) -> tuple[str, str, str, str]:
        return (
            self.workspace_id,
            self.boundary_kind.value,
            self.agent_id or "",
            self.domain_id or "",
        )

    def identity_payload(self) -> dict[str, str | None]:
        return {
            "workspace_id": self.workspace_id,
            "boundary_kind": self.boundary_kind.value,
            "agent_id": self.agent_id,
            "domain_id": self.domain_id,
        }


@dataclass(frozen=True)
class ExplicitSourceEvidence:
    """One immutable present/absent source expectation under one owner."""

    owner_class: SourceOwnerClass
    owner_boundary: EvidenceOwnerBoundary
    canonical_locator: str
    semantic_role: EvidenceSemanticRole
    presence_expectation: EvidencePresenceExpectation
    scope_key: RootScopeKey | None = None
    byte_length: int | None = None
    sha256_hex: str | None = None
    absence_reason: EvidenceAbsenceReason | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.owner_class, SourceOwnerClass):
            raise ExplicitSourceEvidenceError("owner_class must be SourceOwnerClass")
        if not isinstance(self.owner_boundary, EvidenceOwnerBoundary):
            raise ExplicitSourceEvidenceError("owner_boundary must be EvidenceOwnerBoundary")
        if not isinstance(self.semantic_role, EvidenceSemanticRole):
            raise ExplicitSourceEvidenceError("semantic_role must be EvidenceSemanticRole")
        if not isinstance(self.presence_expectation, EvidencePresenceExpectation):
            raise ExplicitSourceEvidenceError("presence_expectation must be EvidencePresenceExpectation")
        canonical_locator = _canonical_locator(self.canonical_locator)
        object.__setattr__(self, "canonical_locator", canonical_locator)
        _validate_owner_role_boundary(self.owner_class, self.semantic_role, self.owner_boundary)
        _validate_scope_binding(self.scope_key, self.owner_boundary)
        if self.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT:
            if self.absence_reason is not None:
                raise ExplicitSourceEvidenceError("present evidence forbids absence_reason")
            if not isinstance(self.byte_length, int) or isinstance(self.byte_length, bool) or self.byte_length < 0:
                raise ExplicitSourceEvidenceError("present evidence byte_length must be non-negative")
            _sha256(self.sha256_hex)
        else:
            if self.byte_length is not None or self.sha256_hex is not None:
                raise ExplicitSourceEvidenceError("absent evidence forbids byte_length and sha256_hex")
            if not isinstance(self.absence_reason, EvidenceAbsenceReason):
                raise ExplicitSourceEvidenceError("absent evidence requires an explicit absence_reason")
            _validate_absence_reason(self.semantic_role, self.absence_reason)

    @property
    def canonical_key(self) -> tuple[object, ...]:
        return (
            *self.owner_boundary.canonical_key,
            self.canonical_locator,
            self.owner_class.value,
            self.semantic_role.value,
            self.presence_expectation.value,
            self.scope_key.canonical_key if self.scope_key is not None else ("", "", ""),
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "owner_class": self.owner_class.value,
            "owner_boundary": self.owner_boundary.identity_payload(),
            "canonical_locator": self.canonical_locator,
            "semantic_role": self.semantic_role.value,
            "presence_expectation": self.presence_expectation.value,
            "scope_key": self.scope_key.identity_payload() if self.scope_key is not None else None,
            "byte_length": self.byte_length,
            "sha256_hex": self.sha256_hex,
            "absence_reason": self.absence_reason.value if self.absence_reason is not None else None,
        }


@dataclass(frozen=True)
class RootEvidenceManifest:
    """Canonical, owner-bounded evidence identity for one root description."""

    entries: tuple[ExplicitSourceEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or not self.entries:
            raise ExplicitSourceEvidenceError("manifest entries must be a non-empty tuple")
        if any(not isinstance(entry, ExplicitSourceEvidence) for entry in self.entries):
            raise ExplicitSourceEvidenceError("manifest entries must be ExplicitSourceEvidence")
        ordered = tuple(sorted(self.entries, key=lambda entry: entry.canonical_key))
        duplicate_keys = [entry.canonical_key for entry in ordered]
        if len(set(duplicate_keys)) != len(duplicate_keys):
            raise ExplicitSourceEvidenceError("manifest contains duplicate owner-relative evidence")
        object.__setattr__(self, "entries", ordered)

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": EXPLICIT_SOURCE_MANIFEST_SCHEMA,
            "version": EXPLICIT_SOURCE_MANIFEST_VERSION,
            "entries": [entry.identity_payload() for entry in self.entries],
        }

    @property
    def canonical_text(self) -> str:
        return canonical_intent_text(self.canonical_payload)

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_text.encode("utf-8")).hexdigest()

    def verify(self, *, data_root: str | Path) -> "RootEvidenceVerification":
        return verify_explicit_source_manifest(self, data_root=data_root)


@dataclass(frozen=True)
class RootEvidenceVerification:
    manifest_digest: str
    verified_present_entries: tuple[ExplicitSourceEvidence, ...]
    verified_absent_entries: tuple[ExplicitSourceEvidence, ...]
    observed_data_root: Path


def capture_present_source_evidence(
    *,
    data_root: str | Path,
    owner_class: SourceOwnerClass,
    owner_boundary: EvidenceOwnerBoundary,
    canonical_locator: str,
    semantic_role: EvidenceSemanticRole,
    scope_key: RootScopeKey | None = None,
) -> ExplicitSourceEvidence:
    """Capture one declared fixture/source file without traversing its owner."""
    _validate_owner_role_boundary(owner_class, semantic_role, owner_boundary)
    _validate_scope_binding(scope_key, owner_boundary)
    path = _resolve_evidence_path(data_root, owner_boundary, canonical_locator)
    if not path.is_file():
        raise ExplicitSourceEvidenceError("declared present evidence is not a regular file")
    payload = path.read_bytes()
    return ExplicitSourceEvidence(
        owner_class=owner_class,
        owner_boundary=owner_boundary,
        canonical_locator=canonical_locator,
        semantic_role=semantic_role,
        presence_expectation=EvidencePresenceExpectation.EXPECTED_PRESENT,
        scope_key=scope_key,
        byte_length=len(payload),
        sha256_hex=hashlib.sha256(payload).hexdigest(),
    )


def resolve_explicit_source_evidence_path(
    *,
    data_root: str | Path,
    evidence: ExplicitSourceEvidence,
) -> Path:
    """Resolve one declared source through the shared owner-containment doctrine."""
    if not isinstance(evidence, ExplicitSourceEvidence):
        raise ExplicitSourceEvidenceError("evidence must be ExplicitSourceEvidence")
    return _resolve_evidence_path(data_root, evidence.owner_boundary, evidence.canonical_locator)


def verify_explicit_source_manifest(
    manifest: RootEvidenceManifest,
    *,
    data_root: str | Path,
) -> RootEvidenceVerification:
    """Read only manifest-declared locators and reject any observed drift."""
    if not isinstance(manifest, RootEvidenceManifest):
        raise ExplicitSourceEvidenceError("manifest must be RootEvidenceManifest")
    root = _data_root(data_root)
    present: list[ExplicitSourceEvidence] = []
    absent: list[ExplicitSourceEvidence] = []
    for entry in manifest.entries:
        path = _resolve_evidence_path(root, entry.owner_boundary, entry.canonical_locator)
        if entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT:
            if path.exists():
                raise ExplicitSourceEvidenceDrift(
                    f"expected-absent evidence was created: {entry.canonical_locator}"
                )
            absent.append(entry)
            continue
        if not path.is_file():
            raise ExplicitSourceEvidenceDrift(
                f"required evidence is missing or not a regular file: {entry.canonical_locator}"
            )
        payload = path.read_bytes()
        if len(payload) != entry.byte_length or hashlib.sha256(payload).hexdigest() != entry.sha256_hex:
            raise ExplicitSourceEvidenceDrift(
                f"declared evidence drifted: {entry.canonical_locator}"
            )
        present.append(entry)
    return RootEvidenceVerification(manifest.digest, tuple(present), tuple(absent), root)


def write_explicit_source_manifest(manifest: RootEvidenceManifest, path: str | Path) -> None:
    """Persist canonical manifest evidence outside any admission side effect."""
    if not isinstance(manifest, RootEvidenceManifest):
        raise ExplicitSourceEvidenceError("manifest must be RootEvidenceManifest")
    destination = Path(path).expanduser().resolve()
    payload = {"manifest_digest": manifest.digest, "manifest": manifest.canonical_payload}
    destination.write_text(canonical_intent_text(payload) + "\n", encoding="utf-8", newline="\n")


def load_explicit_source_manifest(path: str | Path) -> RootEvidenceManifest:
    """Re-open a canonical manifest and prove its recorded digest is intact."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise ExplicitSourceEvidenceError("explicit source manifest file was not found")
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExplicitSourceEvidenceError("explicit source manifest is not valid JSON") from exc
    if not isinstance(raw, dict) or set(raw) != {"manifest_digest", "manifest"}:
        raise ExplicitSourceEvidenceError("explicit source manifest wrapper is malformed")
    manifest = _manifest_from_payload(raw["manifest"])
    if raw["manifest_digest"] != manifest.digest:
        raise ExplicitSourceEvidenceDrift("explicit source manifest digest does not match its payload")
    return manifest


def _manifest_from_payload(value: object) -> RootEvidenceManifest:
    if not isinstance(value, dict) or value.get("schema") != EXPLICIT_SOURCE_MANIFEST_SCHEMA:
        raise ExplicitSourceEvidenceError("explicit source manifest schema is invalid")
    if value.get("version") != EXPLICIT_SOURCE_MANIFEST_VERSION:
        raise ExplicitSourceEvidenceError("explicit source manifest version is invalid")
    entries = value.get("entries")
    if not isinstance(entries, list):
        raise ExplicitSourceEvidenceError("explicit source manifest entries are invalid")
    return RootEvidenceManifest(tuple(_entry_from_payload(entry) for entry in entries))


def _entry_from_payload(value: object) -> ExplicitSourceEvidence:
    if not isinstance(value, dict):
        raise ExplicitSourceEvidenceError("explicit source evidence entry is invalid")
    try:
        owner_raw = value["owner_boundary"]
        if not isinstance(owner_raw, dict):
            raise TypeError
        owner = EvidenceOwnerBoundary(
            workspace_id=owner_raw["workspace_id"],
            boundary_kind=EvidenceOwnerBoundaryKind(owner_raw["boundary_kind"]),
            agent_id=owner_raw.get("agent_id"),
            domain_id=owner_raw.get("domain_id"),
        )
        scope_raw = value.get("scope_key")
        scope = None
        if scope_raw is not None:
            if not isinstance(scope_raw, dict):
                raise TypeError
            scope = RootScopeKey(
                workspace_id=scope_raw["workspace_id"],
                scope_kind=RootScopeKind(scope_raw["scope_kind"]),
                agent_id=scope_raw.get("agent_id"),
                domain_id=scope_raw.get("domain_id"),
            )
        absence = value.get("absence_reason")
        return ExplicitSourceEvidence(
            owner_class=SourceOwnerClass(value["owner_class"]),
            owner_boundary=owner,
            canonical_locator=value["canonical_locator"],
            semantic_role=EvidenceSemanticRole(value["semantic_role"]),
            presence_expectation=EvidencePresenceExpectation(value["presence_expectation"]),
            scope_key=scope,
            byte_length=value.get("byte_length"),
            sha256_hex=value.get("sha256_hex"),
            absence_reason=EvidenceAbsenceReason(absence) if absence is not None else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ExplicitSourceEvidenceError("explicit source evidence entry is malformed") from exc


def _resolve_evidence_path(
    data_root: str | Path,
    owner_boundary: EvidenceOwnerBoundary,
    canonical_locator: str,
) -> Path:
    root = _data_root(data_root)
    locator_parts = _locator_parts(canonical_locator)
    try:
        boundary = Path(safe_join(str(root), *owner_boundary.relative_parts))
        return Path(safe_join(str(boundary), *locator_parts))
    except ValueError as exc:
        raise ExplicitSourceEvidenceError("evidence locator escapes its declared owner boundary") from exc


def _data_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise ExplicitSourceEvidenceError("data_root must be an explicit path")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ExplicitSourceEvidenceError("data_root must be an existing directory")
    return root


def _validate_owner_role_boundary(
    owner_class: SourceOwnerClass,
    role: EvidenceSemanticRole,
    boundary: EvidenceOwnerBoundary,
) -> None:
    expected_roles = {
        SourceOwnerClass.WORKSPACE_IDENTITY_METADATA: {EvidenceSemanticRole.WORKSPACE_META},
        SourceOwnerClass.DOMAIN_DECLARATION: {EvidenceSemanticRole.DOMAINS},
        SourceOwnerClass.DOMAIN_POLICY: {EvidenceSemanticRole.DOMAIN_POLICY},
        SourceOwnerClass.BRIDGE_OWNER_EVIDENCE: {EvidenceSemanticRole.BRIDGES},
        SourceOwnerClass.PRIVATE_GRAPH_SOURCE: {EvidenceSemanticRole.NODES, EvidenceSemanticRole.EDGES},
        SourceOwnerClass.SHARED_GRAPH_SOURCE: {EvidenceSemanticRole.NODES, EvidenceSemanticRole.EDGES},
        SourceOwnerClass.EMBEDDING_MANIFEST: {EvidenceSemanticRole.EMBEDDING_MANIFEST},
        SourceOwnerClass.EMBEDDING_SHARD_OR_MAP: {EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP},
        SourceOwnerClass.LEGACY_REPRESENTATION_ARTIFACT: {EvidenceSemanticRole.LEGACY_REPRESENTATION},
        SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION: {
            EvidenceSemanticRole.LEGACY_REPRESENTATION
        },
        SourceOwnerClass.MOTIF_SOURCE: {EvidenceSemanticRole.MOTIFS},
        SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION: {EvidenceSemanticRole.EXTERNAL_OBSERVATION},
    }
    if role not in expected_roles[owner_class]:
        raise ExplicitSourceEvidenceError("semantic_role is not valid for owner_class")
    allowed_boundaries = {
        SourceOwnerClass.WORKSPACE_IDENTITY_METADATA: {EvidenceOwnerBoundaryKind.WORKSPACE},
        SourceOwnerClass.DOMAIN_DECLARATION: {EvidenceOwnerBoundaryKind.WORKSPACE},
        SourceOwnerClass.DOMAIN_POLICY: {EvidenceOwnerBoundaryKind.WORKSPACE},
        SourceOwnerClass.BRIDGE_OWNER_EVIDENCE: {EvidenceOwnerBoundaryKind.WORKSPACE},
        SourceOwnerClass.PRIVATE_GRAPH_SOURCE: {EvidenceOwnerBoundaryKind.PRIVATE_SCOPE},
        SourceOwnerClass.SHARED_GRAPH_SOURCE: {EvidenceOwnerBoundaryKind.SHARED_SCOPE},
        SourceOwnerClass.EMBEDDING_MANIFEST: {EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, EvidenceOwnerBoundaryKind.SHARED_SCOPE},
        SourceOwnerClass.EMBEDDING_SHARD_OR_MAP: {EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, EvidenceOwnerBoundaryKind.SHARED_SCOPE},
        SourceOwnerClass.LEGACY_REPRESENTATION_ARTIFACT: {EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, EvidenceOwnerBoundaryKind.SHARED_SCOPE},
        SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION: {
            EvidenceOwnerBoundaryKind.PRIVATE_SCOPE
        },
        SourceOwnerClass.MOTIF_SOURCE: {EvidenceOwnerBoundaryKind.DOMAIN, EvidenceOwnerBoundaryKind.PRIVATE_SCOPE, EvidenceOwnerBoundaryKind.SHARED_SCOPE},
        SourceOwnerClass.EXTERNAL_OWNER_OBSERVATION: set(EvidenceOwnerBoundaryKind),
    }
    if boundary.boundary_kind not in allowed_boundaries[owner_class]:
        raise ExplicitSourceEvidenceError("owner_class is not valid under the declared owner boundary")


def _validate_scope_binding(scope_key: RootScopeKey | None, boundary: EvidenceOwnerBoundary) -> None:
    if scope_key is not None and not isinstance(scope_key, RootScopeKey):
        raise ExplicitSourceEvidenceError("scope_key must be RootScopeKey when supplied")
    if scope_key is not None and scope_key.workspace_id != boundary.workspace_id:
        raise ExplicitSourceEvidenceError("evidence scope_key crosses its owner workspace")
    boundary_scope = boundary.scope_key
    if boundary_scope is not None and scope_key != boundary_scope:
        raise ExplicitSourceEvidenceError("scope_key does not match its private/shared owner boundary")


def _validate_absence_reason(role: EvidenceSemanticRole, reason: EvidenceAbsenceReason) -> None:
    if reason is EvidenceAbsenceReason.OPTIONAL_EDGE_SOURCE and role is not EvidenceSemanticRole.EDGES:
        raise ExplicitSourceEvidenceError("OPTIONAL_EDGE_SOURCE requires EDGES semantic role")
    if reason is EvidenceAbsenceReason.EMPTY_GRAPH and role not in {
        EvidenceSemanticRole.NODES,
        EvidenceSemanticRole.EMBEDDING_MANIFEST,
        EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
    }:
        raise ExplicitSourceEvidenceError("EMPTY_GRAPH absence is not valid for this semantic role")
    if reason is EvidenceAbsenceReason.METADATA_LESS_SOURCE_SHAPE and role not in {
        EvidenceSemanticRole.EMBEDDING_MANIFEST,
        EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
        EvidenceSemanticRole.LEGACY_REPRESENTATION,
    }:
        raise ExplicitSourceEvidenceError("METADATA_LESS_SOURCE_SHAPE is not valid for this semantic role")


def _canonical_locator(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ExplicitSourceEvidenceError("canonical_locator must be non-empty text")
    if "\\" in value:
        raise ExplicitSourceEvidenceError("canonical_locator must use POSIX separators")
    parts = _locator_parts(value)
    return "/".join(parts)


def _locator_parts(value: str) -> tuple[str, ...]:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts:
        raise ExplicitSourceEvidenceError("evidence locator must be a non-empty relative path")
    parts = tuple(path.parts)
    for part in parts:
        if ":" in part:
            raise ExplicitSourceEvidenceError("evidence locator must not contain a drive-qualified component")
        try:
            validate_structural_path_component(part, "evidence locator component")
        except ValueError as exc:
            raise ExplicitSourceEvidenceError(str(exc)) from exc
    return parts


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ExplicitSourceEvidenceError(f"{label} must be non-empty text")
    try:
        return validate_structural_path_component(value, label)
    except ValueError as exc:
        raise ExplicitSourceEvidenceError(str(exc)) from exc


def _sha256(value: object) -> str:
    if not isinstance(value, str) or len(value) != _SHA256_HEX_LENGTH:
        raise ExplicitSourceEvidenceError("sha256_hex must be lowercase SHA-256 hex")
    if value.lower() != value:
        raise ExplicitSourceEvidenceError("sha256_hex must be lowercase SHA-256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ExplicitSourceEvidenceError("sha256_hex must be lowercase SHA-256 hex") from exc
    return value


__all__ = [
    "EXPLICIT_SOURCE_MANIFEST_SCHEMA",
    "EXPLICIT_SOURCE_MANIFEST_VERSION",
    "EvidenceAbsenceReason",
    "EvidenceOwnerBoundary",
    "EvidenceOwnerBoundaryKind",
    "EvidencePresenceExpectation",
    "EvidenceSemanticRole",
    "ExplicitSourceEvidence",
    "ExplicitSourceEvidenceDrift",
    "ExplicitSourceEvidenceError",
    "RootEvidenceManifest",
    "RootEvidenceVerification",
    "SourceOwnerClass",
    "capture_present_source_evidence",
    "load_explicit_source_manifest",
    "resolve_explicit_source_evidence_path",
    "verify_explicit_source_manifest",
    "write_explicit_source_manifest",
]
