"""External P3 evidence for permanently partial legacy motif authority.

This module deliberately owns no SQLite semantic write.  It classifies frozen
``motifs.json`` state against the already sealed B1M EID identity universe,
retains only source facts for partial records, and produces an external B4P
null-projection proof.  In particular, it never turns an ambiguous occurrence
into a native object identity or a ``MOTIF_MEMBERSHIP`` relationship.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import sqlite3
from typing import Any, Mapping
from uuid import UUID

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateConfigurationError
from ..ids import native_id_from_bytes, native_id_to_bytes
from .snapshot import LegacyArtifact, load_snapshot_manifest, verify_snapshot


_CONTINUATION_NAME = "p3_partial_motif_authority_continuation.json"
_CONTINUATION_SCHEMA = "TORMENT_P3_PARTIAL_MOTIF_AUTHORITY_CONTINUATION"
_CONTINUATION_VERSION = 1
_OCCURRENCE_LAW = "P3_ORDERED_LEGACY_MOTIF_OCCURRENCES_V1"
_SOURCE_PAYLOAD_LAW = "P3_LEGACY_MOTIF_SOURCE_PAYLOAD_V1"
_FORBIDDEN_CERTIFICATION_KEYS = frozenset({
    "native_object_id", "candidate_object_ids", "candidate_namespace_ids",
    "chosen_candidate", "resolution_status",
})


class PartialMotifAuthorityRefused(SubstrateConfigurationError):
    """Partial motif evidence is not exact, sealed, or internally coherent."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class MotifSemanticDisposition(StrEnum):
    EXACT_ADMITTED = "EXACT_ADMITTED"
    PARTIAL_AUTHORITY_CERTIFIED = "PARTIAL_AUTHORITY_CERTIFIED"
    ZERO_MEMBER_CERTIFIED = "ZERO_MEMBER_CERTIFIED"
    BLOCKING_QUARANTINE = "BLOCKING_QUARANTINE"


class PartialMotifReason(StrEnum):
    IDENTITY_AMBIGUOUS = "IDENTITY_AMBIGUOUS"
    MULTIPLICITY_INCOMPATIBLE = "MULTIPLICITY_INCOMPATIBLE"
    BOTH = "BOTH"


@dataclass(frozen=True)
class FrozenMotifSource:
    """Validated source facts, intentionally without native member identities."""

    scope_key: dict[str, Any]
    legacy_snapshot_id: UUID
    legacy_source_namespace_id: UUID
    legacy_artifact_id: UUID
    legacy_artifact_sha256: str
    observed_relative_locator: str
    motif_id: str
    domain_id: str
    source_motif: dict[str, Any]
    ordered_occurrences: tuple[int, ...]

    @property
    def source_motif_payload_digest(self) -> str:
        return _digest({"law": _SOURCE_PAYLOAD_LAW, "motif": self.source_motif})

    @property
    def occurrence_digest(self) -> str:
        return _digest({
            "law": _OCCURRENCE_LAW,
            "motif_id": self.motif_id,
            "ordered_occurrences": [
                {"ordinal": ordinal, "raw_eid": raw_eid}
                for ordinal, raw_eid in enumerate(self.ordered_occurrences)
            ],
        })


@dataclass(frozen=True)
class MotifDisposition:
    """The B1F terminal state for one frozen semantic motif record."""

    source: FrozenMotifSource | None
    disposition: MotifSemanticDisposition
    partial_reason: PartialMotifReason | None = None
    blocking_code: str | None = None

    def __post_init__(self) -> None:
        if self.disposition is MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED:
            if self.source is None or self.partial_reason is None or self.blocking_code is not None:
                raise ValueError("partial disposition requires source and reason only")
        elif self.disposition is MotifSemanticDisposition.BLOCKING_QUARANTINE:
            if self.blocking_code is None:
                raise ValueError("blocking disposition requires a code")
        elif self.partial_reason is not None or self.blocking_code is not None:
            raise ValueError("exact and zero dispositions cannot carry partial/blocking detail")


@dataclass(frozen=True)
class PartialMotifAuthorityCertification:
    """One source-only permanent partial-authority certificate."""

    payload: dict[str, Any]
    digest: str

    @property
    def motif_id(self) -> str:
        return str(self.payload["motif_id"])


@dataclass(frozen=True)
class PartialMotifRetentionRequest:
    """B4P input.  It carries verification context, never member choices."""

    continuation_record_path: Path
    certification_digest: str
    snapshot_root: Path
    manifest_path: Path
    expected_native_core_id: UUID
    eligible_member_source_namespace_ids: tuple[UUID, ...]
    b1m_identity_universe_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.expected_native_core_id, UUID):
            raise ValueError("expected_native_core_id must be UUID")
        if not self.eligible_member_source_namespace_ids or any(
            not isinstance(value, UUID) for value in self.eligible_member_source_namespace_ids
        ):
            raise ValueError("eligible_member_source_namespace_ids must be non-empty UUIDs")
        for name in ("certification_digest", "b1m_identity_universe_digest"):
            _require_digest(getattr(self, name), name)


@dataclass(frozen=True)
class PartialMotifRetentionResult:
    certification_digest: str
    motif_id: str
    derived_motif_count: int
    motif_id_alias_count: int
    membership_count: int


def classify_frozen_motifs(
    connection: sqlite3.Connection,
    *,
    snapshot_root: str | Path,
    manifest_path: str | Path,
    scope_key: Mapping[str, Any],
    eligible_member_source_namespace_ids: tuple[UUID, ...],
) -> tuple[MotifDisposition, ...]:
    """Classify every frozen motif without writing semantic state.

    Candidate identities exist only transiently while applying the bounded
    predicate.  The returned state and all durable partial evidence omit them.
    """

    if not isinstance(connection, sqlite3.Connection):
        raise ValueError("connection must be sqlite3.Connection")
    if not eligible_member_source_namespace_ids or any(
        not isinstance(value, UUID) for value in eligible_member_source_namespace_ids
    ):
        raise ValueError("eligible_member_source_namespace_ids must be non-empty UUIDs")
    if len(set(eligible_member_source_namespace_ids)) != len(eligible_member_source_namespace_ids):
        raise ValueError("eligible_member_source_namespace_ids must be unique")
    root = Path(snapshot_root).expanduser().resolve()
    manifest = load_snapshot_manifest(manifest_path)
    try:
        verify_snapshot(snapshot_root=root, manifest=manifest)
    except Exception as exc:  # The caller owns the typed public refusal boundary.
        raise PartialMotifAuthorityRefused("P3_PARTIAL_MOTIF_SNAPSHOT_INVALID") from exc
    result: list[MotifDisposition] = []
    for artifact in manifest.artifacts:
        domain_id = _motif_registry_domain(artifact.observed_relative_locator)
        if domain_id is None:
            continue
        try:
            registry = _load_registry(root, artifact)
        except ValueError as exc:
            result.append(MotifDisposition(
                None, MotifSemanticDisposition.BLOCKING_QUARANTINE,
                blocking_code=f"INVALID_SOURCE_STATE:{exc}",
            ))
            continue
        raw_motifs = registry.get("motifs")
        if not isinstance(raw_motifs, dict):
            result.append(MotifDisposition(
                None, MotifSemanticDisposition.BLOCKING_QUARANTINE,
                blocking_code="INVALID_SOURCE_STATE:MOTIFS_MAPPING_REQUIRED",
            ))
            continue
        for motif_id, raw_motif in sorted(raw_motifs.items(), key=lambda item: str(item[0])):
            try:
                source = _frozen_source(
                    manifest=manifest, artifact=artifact, scope_key=scope_key,
                    domain_id=domain_id, motif_id=motif_id, raw_motif=raw_motif,
                )
            except ValueError as exc:
                result.append(MotifDisposition(
                    None, MotifSemanticDisposition.BLOCKING_QUARANTINE,
                    blocking_code=f"INVALID_SOURCE_STATE:{exc}",
                ))
                continue
            result.append(_classify_source(
                connection, source, eligible_member_source_namespace_ids,
            ))
    return tuple(result)


def certify_partial_motif(
    disposition: MotifDisposition,
    *,
    b1m_identity_universe_digest: str,
    normal_admission_record_id: UUID | None,
    normal_quarantine_record_id: UUID | None,
) -> PartialMotifAuthorityCertification:
    """Create the durable source-only certificate for one B1F partial."""

    if disposition.disposition is not MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED:
        raise ValueError("only partial B1F dispositions can be certified")
    source = disposition.source
    assert source is not None and disposition.partial_reason is not None
    _require_digest(b1m_identity_universe_digest, "b1m_identity_universe_digest")
    payload: dict[str, Any] = {
        "scope_key": source.scope_key,
        "legacy_snapshot_id": str(source.legacy_snapshot_id),
        "legacy_source_namespace_id": str(source.legacy_source_namespace_id),
        "legacy_artifact_id": str(source.legacy_artifact_id),
        "legacy_artifact_sha256": source.legacy_artifact_sha256,
        "observed_relative_locator": source.observed_relative_locator,
        "motif_id": source.motif_id,
        "domain_id": source.domain_id,
        "source_motif_payload_digest": source.source_motif_payload_digest,
        "authority": "PARTIAL_LEGACY_OCCURRENCE_AUTHORITY",
        "reason": disposition.partial_reason.value,
        "raw_occurrence_count": len(source.ordered_occurrences),
        "distinct_raw_eid_count": len(set(source.ordered_occurrences)),
        "duplicate_occurrence_count": len(source.ordered_occurrences) - len(set(source.ordered_occurrences)),
        "ordered_occurrences": [
            {"ordinal": ordinal, "raw_eid": raw_eid}
            for ordinal, raw_eid in enumerate(source.ordered_occurrences)
        ],
        "occurrence_digest": source.occurrence_digest,
        "b1m_identity_universe_digest": b1m_identity_universe_digest,
        "normal_admission_record_id": None if normal_admission_record_id is None else str(normal_admission_record_id),
        "normal_quarantine_record_id": None if normal_quarantine_record_id is None else str(normal_quarantine_record_id),
        "public_read_parity_qualified": False,
        "post_write_parity_qualified": False,
        "partial_motif_runtime_participation": False,
    }
    _assert_no_forbidden_certification_fields(payload)
    return PartialMotifAuthorityCertification(payload, _digest(payload))


def write_or_reload_continuation(
    *,
    directory: str | Path,
    predecessor_carrier_sha256: str,
    b1m_identity_universe_digest: str,
    b1f_disposition_digest: str,
    certifications: tuple[PartialMotifAuthorityCertification, ...],
) -> Path:
    """Persist one immutable B1F continuation, or validate its exact replay."""

    for name, value in (
        ("predecessor_carrier_sha256", predecessor_carrier_sha256),
        ("b1m_identity_universe_digest", b1m_identity_universe_digest),
        ("b1f_disposition_digest", b1f_disposition_digest),
    ):
        _require_digest(value, name)
    if len({item.digest for item in certifications}) != len(certifications):
        raise ValueError("partial certifications must have unique digests")
    root = Path(directory).expanduser().resolve()
    if root.exists() and (not root.is_dir() or root.is_symlink()):
        raise ValueError("partial continuation directory must be a normal directory")
    if not root.exists():
        if not root.parent.is_dir():
            raise ValueError("partial continuation parent must exist")
        root.mkdir()
    path = root / _CONTINUATION_NAME
    expected = {
        "predecessor_carrier_sha256": predecessor_carrier_sha256,
        "b1m_identity_universe_digest": b1m_identity_universe_digest,
        "b1f_disposition_digest": b1f_disposition_digest,
        "partial_certifications": [
            {"payload": item.payload, "digest": item.digest}
            for item in sorted(certifications, key=lambda item: item.digest)
        ],
        "b4p_proofs": [],
    }
    if path.exists():
        payload = _load_continuation(path)
        for key, value in expected.items():
            if key == "b4p_proofs":
                continue
            if payload.get(key) != value:
                raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_BINDING_MISMATCH")
        return path
    if any(root.iterdir()):
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_DESTINATION_NOT_EMPTY")
    _write_outer_record(path, expected)
    return path


def reload_and_validate_certification(
    connection: sqlite3.Connection,
    *,
    continuation_record_path: str | Path,
    certification_digest: str,
    snapshot_root: str | Path,
    manifest_path: str | Path,
    eligible_member_source_namespace_ids: tuple[UUID, ...],
    b1m_identity_universe_digest: str,
) -> PartialMotifAuthorityCertification:
    """Round-trip a certificate against source bytes and the sealed universe."""

    _require_digest(certification_digest, "certification_digest")
    _require_digest(b1m_identity_universe_digest, "b1m_identity_universe_digest")
    payload = _load_continuation(Path(continuation_record_path).expanduser().resolve())
    if payload.get("b1m_identity_universe_digest") != b1m_identity_universe_digest:
        raise PartialMotifAuthorityRefused("P3_B1M_IDENTITY_UNIVERSE_DRIFT")
    matches = [item for item in _certifications_from_payload(payload) if item.digest == certification_digest]
    if len(matches) != 1:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_MISSING")
    certificate = matches[0]
    _validate_certificate_shape(certificate)
    source_scope = certificate.payload["scope_key"]
    dispositions = classify_frozen_motifs(
        connection,
        snapshot_root=snapshot_root,
        manifest_path=manifest_path,
        scope_key=source_scope,
        eligible_member_source_namespace_ids=eligible_member_source_namespace_ids,
    )
    matches = [
        item for item in dispositions
        if item.source is not None
        and item.source.motif_id == certificate.payload["motif_id"]
        and str(item.source.legacy_artifact_id) == certificate.payload["legacy_artifact_id"]
    ]
    if len(matches) != 1:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_SOURCE_MISMATCH")
    disposition = matches[0]
    if (
        disposition.disposition is not MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED
        or disposition.partial_reason is None
        or disposition.partial_reason.value != certificate.payload["reason"]
    ):
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_CLASSIFIER_MISMATCH")
    expected = certify_partial_motif(
        disposition,
        b1m_identity_universe_digest=b1m_identity_universe_digest,
        normal_admission_record_id=_optional_uuid(certificate.payload.get("normal_admission_record_id")),
        normal_quarantine_record_id=_optional_uuid(certificate.payload.get("normal_quarantine_record_id")),
    )
    if expected != certificate:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_ROUND_TRIP_MISMATCH")
    return certificate


class NativePartialMotifAuthorityRetentionService:
    """B4P verification with no runtime semantic write."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("connection must be sqlite3.Connection")
        self._connection = connection

    def prove_retention(self, request: PartialMotifRetentionRequest) -> PartialMotifRetentionResult:
        if not isinstance(request, PartialMotifRetentionRequest):
            raise ValueError("request must be PartialMotifRetentionRequest")
        core = self._connection.execute("SELECT core_id FROM core_metadata WHERE singleton=1").fetchone()
        if core is None or native_id_from_bytes(core[0]) != request.expected_native_core_id:
            raise PartialMotifAuthorityRefused("P3_B4P_NATIVE_CORE_MISMATCH")
        certificate = reload_and_validate_certification(
            self._connection,
            continuation_record_path=request.continuation_record_path,
            certification_digest=request.certification_digest,
            snapshot_root=request.snapshot_root,
            manifest_path=request.manifest_path,
            eligible_member_source_namespace_ids=request.eligible_member_source_namespace_ids,
            b1m_identity_universe_digest=request.b1m_identity_universe_digest,
        )
        source_namespace = UUID(certificate.payload["legacy_source_namespace_id"])
        motif_id = certificate.motif_id
        alias_count = int(self._connection.execute(
            """SELECT count(*) FROM legacy_object_aliases
               WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?""",
            (native_id_to_bytes(source_namespace), motif_id),
        ).fetchone()[0])
        derived_count = int(self._connection.execute(
            """SELECT count(*) FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id
               WHERE a.legacy_source_namespace_id=? AND a.alias_kind='MOTIF_ID'
                 AND a.alias_value=? AND o.object_kind='LEGACY_DERIVED_MOTIF'""",
            (native_id_to_bytes(source_namespace), motif_id),
        ).fetchone()[0])
        membership_count = int(self._connection.execute(
            """SELECT count(*) FROM relationships r
               JOIN relationship_revisions v ON v.relationship_id=r.relationship_id
                    AND v.relationship_revision_id=r.current_revision_id
                    AND v.revision_ordinal=r.current_revision_ordinal
               JOIN relationship_revision_endpoints e ON e.relationship_revision_id=v.relationship_revision_id
                    AND e.endpoint_ordinal=0 AND e.endpoint_role='MOTIF'
               JOIN legacy_object_aliases a ON a.object_id=e.object_id
               WHERE r.relationship_kind='MOTIF_MEMBERSHIP'
                 AND a.legacy_source_namespace_id=? AND a.alias_kind='MOTIF_ID' AND a.alias_value=?""",
            (native_id_to_bytes(source_namespace), motif_id),
        ).fetchone()[0])
        if alias_count or derived_count or membership_count:
            raise PartialMotifAuthorityRefused("P3_PARTIAL_MOTIF_RUNTIME_LEAK")
        result = PartialMotifRetentionResult(
            request.certification_digest, motif_id, derived_count, alias_count, membership_count,
        )
        self._persist_proof(request.continuation_record_path, certificate, result)
        return result

    def _persist_proof(
        self,
        path: Path,
        certificate: PartialMotifAuthorityCertification,
        result: PartialMotifRetentionResult,
    ) -> None:
        payload = _load_continuation(path)
        proof = {
            "partial_certification_digest": certificate.digest,
            "source_motif_payload_digest": certificate.payload["source_motif_payload_digest"],
            "b1m_identity_universe_digest": certificate.payload["b1m_identity_universe_digest"],
            "derived_motif_count": result.derived_motif_count,
            "motif_id_alias_count": result.motif_id_alias_count,
            "membership_count": result.membership_count,
        }
        proofs = list(payload["b4p_proofs"])
        existing = [item for item in proofs if item.get("partial_certification_digest") == certificate.digest]
        if existing:
            if existing != [proof]:
                raise PartialMotifAuthorityRefused("P3_B4P_PROOF_MISMATCH")
            return
        proofs.append(proof)
        payload["b4p_proofs"] = sorted(proofs, key=lambda item: item["partial_certification_digest"])
        _write_outer_record(path, payload, replace_existing=True)


def continuation_summary(path: str | Path) -> dict[str, int]:
    """Return bounded counts after validating the external record envelope."""

    payload = _load_continuation(Path(path).expanduser().resolve())
    return {
        "partial_certification_count": len(_certifications_from_payload(payload)),
        "b4p_count": len(payload["b4p_proofs"]),
    }


def _classify_source(
    connection: sqlite3.Connection,
    source: FrozenMotifSource,
    namespaces: tuple[UUID, ...],
) -> MotifDisposition:
    occurrences = source.ordered_occurrences
    if not occurrences:
        return MotifDisposition(source, MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED)
    candidates = _candidate_rows(connection, namespaces, occurrences)
    if any(not rows for rows in candidates.values()):
        return MotifDisposition(
            source, MotifSemanticDisposition.BLOCKING_QUARANTINE,
            blocking_code="ZERO_CANDIDATE_PRESENT",
        )
    identity_ambiguous = any(len(rows) != 1 for rows in candidates.values())
    uniquely_resolved = [candidates[eid][0] for eid in occurrences] if not identity_ambiguous else []
    repeated_identity = len(set(uniquely_resolved)) != len(uniquely_resolved)
    raw_duplicates = len(set(occurrences)) != len(occurrences)
    multiplicity_incompatible = raw_duplicates or repeated_identity
    if not identity_ambiguous and not multiplicity_incompatible:
        return MotifDisposition(source, MotifSemanticDisposition.EXACT_ADMITTED)
    reason = (
        PartialMotifReason.BOTH if identity_ambiguous and multiplicity_incompatible else
        PartialMotifReason.IDENTITY_AMBIGUOUS if identity_ambiguous else
        PartialMotifReason.MULTIPLICITY_INCOMPATIBLE
    )
    return MotifDisposition(source, MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED, reason)


def _candidate_rows(
    connection: sqlite3.Connection, namespaces: tuple[UUID, ...], occurrences: tuple[int, ...],
) -> dict[int, tuple[bytes, ...]]:
    placeholders = ",".join("?" for _ in namespaces)
    values = tuple(native_id_to_bytes(value) for value in namespaces)
    result: dict[int, tuple[bytes, ...]] = {}
    for eid in sorted(set(occurrences)):
        rows = connection.execute(
            f"""SELECT a.object_id FROM legacy_object_aliases a
                 JOIN objects o ON o.object_id=a.object_id
                 JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
                WHERE a.legacy_source_namespace_id IN ({placeholders})
                  AND a.alias_kind='EID' AND a.alias_value=?
                  AND o.object_kind='LEGACY_CORE_NODE'
                  AND t.transition_kind='LEGACY_OBJECT_ADMISSION' AND t.origin_kind='LEGACY_ADMISSION'
                ORDER BY a.legacy_source_namespace_id,a.object_id""",
            (*values, str(eid)),
        ).fetchall()
        result[eid] = tuple(row[0] for row in rows)
    return result


def _frozen_source(
    *, manifest, artifact: LegacyArtifact, scope_key: Mapping[str, Any], domain_id: str,
    motif_id: object, raw_motif: object,
) -> FrozenMotifSource:
    if not isinstance(motif_id, str) or not motif_id or not isinstance(raw_motif, dict):
        raise ValueError("MOTIF_ID_OR_RECORD_INVALID")
    if raw_motif.get("motif_id") != motif_id:
        raise ValueError("MOTIF_ID_MISMATCH")
    if raw_motif.get("domain_id") != domain_id:
        raise ValueError("DOMAIN_MISMATCH")
    if not isinstance(raw_motif.get("label"), str):
        raise ValueError("LABEL_INVALID")
    if not _finite(raw_motif.get("strength")) or not _finite(raw_motif.get("stability_score")):
        raise ValueError("STRENGTH_OR_STABILITY_INVALID")
    centroid = raw_motif.get("centroid")
    if not isinstance(centroid, list) or not all(_finite(value) for value in centroid):
        raise ValueError("CENTROID_INVALID")
    agents = raw_motif.get("contributing_agents")
    if not isinstance(agents, list) or not all(isinstance(value, str) for value in agents):
        raise ValueError("CONTRIBUTORS_INVALID")
    if not _nonnegative(raw_motif.get("created_ts")) or not _nonnegative(raw_motif.get("last_active_ts")):
        raise ValueError("TIMESTAMP_INVALID")
    members = raw_motif.get("members")
    if not isinstance(members, list) or not all(_nonnegative(value) for value in members):
        raise ValueError("MEMBERS_INVALID")
    return FrozenMotifSource(
        dict(scope_key), manifest.legacy_snapshot_id, manifest.legacy_source_namespace_id,
        artifact.artifact_id, artifact.digest_hex, artifact.observed_relative_locator,
        motif_id, domain_id, dict(raw_motif), tuple(members),
    )


def _motif_registry_domain(locator: str) -> str | None:
    path = PurePosixPath(locator)
    parts = path.parts
    if len(parts) == 5 and parts[0] == "workspaces" and parts[2] == "domains" and path.name == "motifs.json":
        return parts[3] if parts[1] and parts[3] else None
    return None


def _load_registry(root: Path, artifact: LegacyArtifact) -> dict[str, Any]:
    if artifact.artifact_class != "LEGACY_MOTIF_STATE_EVIDENCE":
        raise ValueError("MOTIF_ARTIFACT_CLASS_INVALID")
    path = (root / artifact.observed_relative_locator).resolve()
    if root not in path.parents:
        raise ValueError("MOTIF_LOCATOR_ESCAPES_SNAPSHOT")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("MOTIF_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise ValueError("MOTIF_REGISTRY_INVALID")
    return value


def _certifications_from_payload(payload: dict[str, Any]) -> tuple[PartialMotifAuthorityCertification, ...]:
    values = payload.get("partial_certifications")
    if not isinstance(values, list):
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_SHAPE_INVALID")
    result: list[PartialMotifAuthorityCertification] = []
    for item in values:
        if not isinstance(item, dict) or set(item) != {"payload", "digest"} or not isinstance(item["payload"], dict):
            raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_SHAPE_INVALID")
        certificate = PartialMotifAuthorityCertification(item["payload"], str(item["digest"]))
        if certificate.digest != _digest(certificate.payload):
            raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_INTEGRITY_INVALID")
        _validate_certificate_shape(certificate)
        result.append(certificate)
    if len({item.digest for item in result}) != len(result):
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_DUPLICATE")
    return tuple(result)


def _validate_certificate_shape(certificate: PartialMotifAuthorityCertification) -> None:
    payload = certificate.payload
    required = {
        "scope_key", "legacy_snapshot_id", "legacy_source_namespace_id", "legacy_artifact_id",
        "legacy_artifact_sha256", "observed_relative_locator", "motif_id", "domain_id",
        "source_motif_payload_digest", "authority", "reason", "raw_occurrence_count",
        "distinct_raw_eid_count", "duplicate_occurrence_count", "ordered_occurrences",
        "occurrence_digest", "b1m_identity_universe_digest", "normal_admission_record_id",
        "normal_quarantine_record_id", "public_read_parity_qualified", "post_write_parity_qualified",
        "partial_motif_runtime_participation",
    }
    if set(payload) != required or payload.get("authority") != "PARTIAL_LEGACY_OCCURRENCE_AUTHORITY":
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_SHAPE_INVALID")
    _assert_no_forbidden_certification_fields(payload)
    for key in ("legacy_artifact_sha256", "source_motif_payload_digest", "occurrence_digest", "b1m_identity_universe_digest"):
        _require_digest(payload.get(key), key)
    try:
        UUID(payload["legacy_snapshot_id"])
        UUID(payload["legacy_source_namespace_id"])
        UUID(payload["legacy_artifact_id"])
        _optional_uuid(payload["normal_admission_record_id"])
        _optional_uuid(payload["normal_quarantine_record_id"])
        PartialMotifReason(payload["reason"])
    except (ValueError, TypeError) as exc:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_SHAPE_INVALID") from exc
    occurrences = payload["ordered_occurrences"]
    if not isinstance(occurrences, list) or any(
        not isinstance(item, dict) or set(item) != {"ordinal", "raw_eid"}
        or item["ordinal"] != index or not _nonnegative(item["raw_eid"])
        for index, item in enumerate(occurrences)
    ):
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_OCCURRENCES_INVALID")
    raw = tuple(item["raw_eid"] for item in occurrences)
    if (
        payload["raw_occurrence_count"] != len(raw)
        or payload["distinct_raw_eid_count"] != len(set(raw))
        or payload["duplicate_occurrence_count"] != len(raw) - len(set(raw))
    ):
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_COUNTS_INVALID")
    expected_occurrence_digest = _digest({
        "law": _OCCURRENCE_LAW, "motif_id": payload["motif_id"], "ordered_occurrences": occurrences,
    })
    if payload["occurrence_digest"] != expected_occurrence_digest:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_OCCURRENCE_DIGEST_INVALID")
    if payload["public_read_parity_qualified"] is not False or payload["post_write_parity_qualified"] is not False or payload["partial_motif_runtime_participation"] is not False:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_NONCLAIM_INVALID")


def _assert_no_forbidden_certification_fields(value: object) -> None:
    if isinstance(value, dict):
        if _FORBIDDEN_CERTIFICATION_KEYS.intersection(value):
            raise PartialMotifAuthorityRefused("P3_PARTIAL_CERTIFICATION_FORBIDDEN_IDENTITY_FIELD")
        for item in value.values():
            _assert_no_forbidden_certification_fields(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_certification_fields(item)


def _load_continuation(path: Path) -> dict[str, Any]:
    try:
        outer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_UNREADABLE") from exc
    if not isinstance(outer, dict) or set(outer) != {"schema", "version", "payload", "digest"}:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_SHAPE_INVALID")
    payload = outer.get("payload")
    if (
        outer.get("schema") != _CONTINUATION_SCHEMA or outer.get("version") != _CONTINUATION_VERSION
        or not isinstance(payload, dict) or outer.get("digest") != _digest(payload)
    ):
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_INTEGRITY_INVALID")
    required = {
        "predecessor_carrier_sha256", "b1m_identity_universe_digest", "b1f_disposition_digest",
        "partial_certifications", "b4p_proofs",
    }
    if set(payload) != required or not isinstance(payload["b4p_proofs"], list):
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_SHAPE_INVALID")
    for key in ("predecessor_carrier_sha256", "b1m_identity_universe_digest", "b1f_disposition_digest"):
        _require_digest(payload.get(key), key)
    _certifications_from_payload(payload)
    return payload


def _write_outer_record(path: Path, payload: dict[str, Any], *, replace_existing: bool = False) -> None:
    outer = {
        "schema": _CONTINUATION_SCHEMA,
        "version": _CONTINUATION_VERSION,
        "payload": payload,
        "digest": _digest(payload),
    }
    temporary = path.parent / f".{path.name}.pending"
    if temporary.exists():
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_TEMPORARY_EXISTS")
    if path.exists() and not replace_existing:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_ALREADY_EXISTS")
    try:
        temporary.write_text(canonical_intent_text(outer) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        raise PartialMotifAuthorityRefused("P3_PARTIAL_CONTINUATION_WRITE_FAILED") from exc


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("UUID must be text or null")
    return UUID(value)


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _nonnegative(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _require_digest(value: object, name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise PartialMotifAuthorityRefused(f"P3_PARTIAL_{name.upper()}_INVALID")
    try:
        int(value, 16)
    except ValueError as exc:
        raise PartialMotifAuthorityRefused(f"P3_PARTIAL_{name.upper()}_INVALID") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


__all__ = [
    "FrozenMotifSource",
    "MotifDisposition",
    "MotifSemanticDisposition",
    "NativePartialMotifAuthorityRetentionService",
    "PartialMotifAuthorityCertification",
    "PartialMotifAuthorityRefused",
    "PartialMotifReason",
    "PartialMotifRetentionRequest",
    "PartialMotifRetentionResult",
    "certify_partial_motif",
    "classify_frozen_motifs",
    "continuation_summary",
    "reload_and_validate_certification",
    "write_or_reload_continuation",
]
