"""Qualified metadata-less private per-EID legacy representation evidence.

This is bounded migration-import support.  It recognizes one explicit private
``emb_<eid>.npy`` witness, retains its historical facts as UNKNOWN evidence,
and supplies the existing B3B canonical-text seam with ``REEMBED_REQUIRED``.
It never infers a provider/model, promotes the old bytes, opens SQLite, or
constructs an embedder.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from uuid import UUID

import numpy as np

from ..canonical_intent import canonical_intent_text
from ..errors import SubstrateConfigurationError, SubstrateIdempotencyConflict
from .explicit_source_evidence import (
    EvidenceAbsenceReason,
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    RootEvidenceManifest,
    SourceOwnerClass,
    resolve_explicit_source_evidence_path,
)
from .root_scope import RootScopeKey, RootScopeKind
from .runtime_embedding_input import (
    CanonicalEmbeddingInput,
    CanonicalEmbeddingInputUnavailable,
    select_canonical_embedding_input,
)
from .runtime_readiness import LegacyVectorStrategy


UNKNOWN_PROVIDER_REMAINS_UNKNOWN = True
UNKNOWN_MODEL_REMAINS_UNKNOWN = True
DIMENSION_DOES_NOT_ESTABLISH_REPRESENTATION_IDENTITY = True
UNKNOWN_LEGACY_VECTOR_CAN_BECOME_TARGET_BY_RELABEL = False

_PER_EID_FILENAME = re.compile(r"emb_(0|[1-9][0-9]*)\.npy\Z")


class MetadataLessRepresentationIdentity(StrEnum):
    UNKNOWN = "UNKNOWN"


class MetadataLessPerEidLegacySourceRefused(SubstrateConfigurationError):
    """Raised when a metadata-less source cannot enter the qualified adapter."""


@dataclass(frozen=True)
class RetainedMetadataLessLegacyVectorEvidence:
    """Immutable historical vector evidence; it is never active geometry."""

    scope_key: RootScopeKey
    legacy_eid: int
    canonical_locator: str
    byte_length: int
    sha256_hex: str
    array_dtype: str
    array_shape: tuple[int, ...]
    dimension: int
    legacy_source_namespace_id: UUID
    target_identity_namespace_id: UUID
    representation_identity: MetadataLessRepresentationIdentity = (
        MetadataLessRepresentationIdentity.UNKNOWN
    )

    def __post_init__(self) -> None:
        _private_scope(self.scope_key)
        _eid(self.legacy_eid)
        if not isinstance(self.canonical_locator, str) or not _PER_EID_FILENAME.fullmatch(
            self.canonical_locator
        ):
            raise MetadataLessPerEidLegacySourceRefused("legacy locator is not a qualified per-EID filename")
        if self.canonical_locator != f"emb_{self.legacy_eid}.npy":
            raise MetadataLessPerEidLegacySourceRefused("legacy locator EID differs from declared legacy EID")
        _nonnegative(self.byte_length, "byte_length")
        _sha256(self.sha256_hex)
        if not isinstance(self.array_dtype, str) or not self.array_dtype:
            raise MetadataLessPerEidLegacySourceRefused("array_dtype must be non-empty text")
        if (
            not isinstance(self.array_shape, tuple)
            or not self.array_shape
            or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in self.array_shape)
        ):
            raise MetadataLessPerEidLegacySourceRefused("array_shape must be a non-empty non-negative integer tuple")
        _nonnegative(self.dimension, "dimension")
        if self.array_shape != (self.dimension,) or self.dimension < 1:
            raise MetadataLessPerEidLegacySourceRefused("legacy vector must be a non-empty one-dimensional array")
        _uuid(self.legacy_source_namespace_id, "legacy_source_namespace_id")
        _uuid(self.target_identity_namespace_id, "target_identity_namespace_id")
        if self.legacy_source_namespace_id == self.target_identity_namespace_id:
            raise MetadataLessPerEidLegacySourceRefused("source and target namespaces must remain distinct")
        if self.representation_identity is not MetadataLessRepresentationIdentity.UNKNOWN:
            raise MetadataLessPerEidLegacySourceRefused("metadata-less representation identity must remain UNKNOWN")

    def identity_payload(self) -> dict[str, object]:
        return {
            "scope_key": self.scope_key.identity_payload(),
            "legacy_eid": self.legacy_eid,
            "canonical_locator": self.canonical_locator,
            "byte_length": self.byte_length,
            "sha256_hex": self.sha256_hex,
            "array_dtype": self.array_dtype,
            "array_shape": list(self.array_shape),
            "dimension": self.dimension,
            "legacy_source_namespace_id": str(self.legacy_source_namespace_id),
            "target_identity_namespace_id": str(self.target_identity_namespace_id),
            "representation_identity": self.representation_identity.value,
        }


@dataclass(frozen=True)
class MetadataLessPerEidB3BInput:
    """The only hand-off to later B3B target derivation semantics."""

    scope_key: RootScopeKey
    legacy_eid: int
    legacy_source_namespace_id: UUID
    target_identity_namespace_id: UUID
    canonical_embedding_input: CanonicalEmbeddingInput
    retained_legacy_vector: RetainedMetadataLessLegacyVectorEvidence
    source_evidence_identity: str
    legacy_vector_strategy: LegacyVectorStrategy = LegacyVectorStrategy.REEMBED_REQUIRED

    def __post_init__(self) -> None:
        _private_scope(self.scope_key)
        _eid(self.legacy_eid)
        _uuid(self.legacy_source_namespace_id, "legacy_source_namespace_id")
        _uuid(self.target_identity_namespace_id, "target_identity_namespace_id")
        if not isinstance(self.canonical_embedding_input, CanonicalEmbeddingInput):
            raise MetadataLessPerEidLegacySourceRefused("B3B input requires canonical embedding input")
        if not isinstance(self.retained_legacy_vector, RetainedMetadataLessLegacyVectorEvidence):
            raise MetadataLessPerEidLegacySourceRefused("B3B input requires retained legacy vector evidence")
        if self.retained_legacy_vector.scope_key != self.scope_key or self.retained_legacy_vector.legacy_eid != self.legacy_eid:
            raise MetadataLessPerEidLegacySourceRefused("B3B input disagrees with retained legacy vector identity")
        _sha256(self.source_evidence_identity)
        if self.legacy_vector_strategy is not LegacyVectorStrategy.REEMBED_REQUIRED:
            raise MetadataLessPerEidLegacySourceRefused("metadata-less source may only use REEMBED_REQUIRED")


@dataclass(frozen=True)
class QualifiedMetadataLessPerEidLegacySource:
    """One fully qualified metadata-less source, still inert administrative evidence."""

    scope_key: RootScopeKey
    legacy_eid: int
    legacy_source_namespace_id: UUID
    target_identity_namespace_id: UUID
    nodes_source: ExplicitSourceEvidence
    optional_edges_source: ExplicitSourceEvidence
    legacy_representation_source: ExplicitSourceEvidence
    evidence_manifest: RootEvidenceManifest
    canonical_embedding_input: CanonicalEmbeddingInput
    retained_legacy_vector: RetainedMetadataLessLegacyVectorEvidence
    source_evidence_identity: str
    representation_identity: MetadataLessRepresentationIdentity = (
        MetadataLessRepresentationIdentity.UNKNOWN
    )
    legacy_vector_strategy: LegacyVectorStrategy = LegacyVectorStrategy.REEMBED_REQUIRED

    def __post_init__(self) -> None:
        _private_scope(self.scope_key)
        _eid(self.legacy_eid)
        _uuid(self.legacy_source_namespace_id, "legacy_source_namespace_id")
        _uuid(self.target_identity_namespace_id, "target_identity_namespace_id")
        _validate_nodes_source(self.nodes_source, self.scope_key)
        _validate_optional_edges_source(self.optional_edges_source, self.scope_key)
        _validate_representation_source(self.legacy_representation_source, self.scope_key, self.legacy_eid)
        if not isinstance(self.evidence_manifest, RootEvidenceManifest):
            raise MetadataLessPerEidLegacySourceRefused("evidence_manifest must be RootEvidenceManifest")
        expected_entries = {
            self.nodes_source,
            self.optional_edges_source,
            self.legacy_representation_source,
        }
        if set(self.evidence_manifest.entries) != expected_entries:
            raise MetadataLessPerEidLegacySourceRefused("manifest must bind exactly the declared per-EID sources")
        if not isinstance(self.canonical_embedding_input, CanonicalEmbeddingInput):
            raise MetadataLessPerEidLegacySourceRefused("canonical embedding input is required")
        if not isinstance(self.retained_legacy_vector, RetainedMetadataLessLegacyVectorEvidence):
            raise MetadataLessPerEidLegacySourceRefused("retained legacy vector evidence is required")
        if (
            self.retained_legacy_vector.scope_key != self.scope_key
            or self.retained_legacy_vector.legacy_eid != self.legacy_eid
            or self.retained_legacy_vector.legacy_source_namespace_id != self.legacy_source_namespace_id
            or self.retained_legacy_vector.target_identity_namespace_id != self.target_identity_namespace_id
            or self.retained_legacy_vector.sha256_hex != self.legacy_representation_source.sha256_hex
            or self.retained_legacy_vector.byte_length != self.legacy_representation_source.byte_length
        ):
            raise MetadataLessPerEidLegacySourceRefused("retained vector evidence disagrees with declared source")
        _sha256(self.source_evidence_identity)
        if self.representation_identity is not MetadataLessRepresentationIdentity.UNKNOWN:
            raise MetadataLessPerEidLegacySourceRefused("metadata-less representation identity must remain UNKNOWN")
        if self.legacy_vector_strategy is not LegacyVectorStrategy.REEMBED_REQUIRED:
            raise MetadataLessPerEidLegacySourceRefused("metadata-less source may only use REEMBED_REQUIRED")

    @property
    def provider_identity(self) -> None:
        """No provider fact exists for this metadata-less source."""
        return None

    @property
    def model_identity(self) -> None:
        """No model fact exists for this metadata-less source."""
        return None

    @property
    def canonical_graph_source_identity(self) -> str:
        """Identity of the declared private ``nodes.jsonl`` graph source."""
        return _evidence_identity(self.nodes_source)

    @property
    def legacy_representation_evidence_identity(self) -> str:
        """Identity of the exact retained ``emb_<eid>.npy`` witness."""
        return _evidence_identity(self.legacy_representation_source)

    @property
    def b3b_input(self) -> MetadataLessPerEidB3BInput:
        """Expose canonical text and retained evidence, never legacy vector bytes."""
        return MetadataLessPerEidB3BInput(
            scope_key=self.scope_key,
            legacy_eid=self.legacy_eid,
            legacy_source_namespace_id=self.legacy_source_namespace_id,
            target_identity_namespace_id=self.target_identity_namespace_id,
            canonical_embedding_input=self.canonical_embedding_input,
            retained_legacy_vector=self.retained_legacy_vector,
            source_evidence_identity=self.source_evidence_identity,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "scope_key": self.scope_key.identity_payload(),
            "legacy_eid": self.legacy_eid,
            "legacy_source_namespace_id": str(self.legacy_source_namespace_id),
            "target_identity_namespace_id": str(self.target_identity_namespace_id),
            "nodes_source_identity": self.canonical_graph_source_identity,
            "optional_edges_source_identity": _evidence_identity(self.optional_edges_source),
            "legacy_representation_source_identity": self.legacy_representation_evidence_identity,
            "evidence_manifest_digest": self.evidence_manifest.digest,
            "canonical_embedding_input": {
                "field": self.canonical_embedding_input.field,
                "digest": self.canonical_embedding_input.digest,
            },
            "retained_legacy_vector": self.retained_legacy_vector.identity_payload(),
            "representation_identity": self.representation_identity.value,
            "legacy_vector_strategy": self.legacy_vector_strategy.value,
        }

    def recheck(self, *, data_root: str | Path) -> "QualifiedMetadataLessPerEidLegacySource":
        """Re-open only the three declared sources and refuse any drift."""
        return qualify_metadata_less_per_eid_legacy_source(
            data_root=data_root,
            scope_key=self.scope_key,
            legacy_eid=self.legacy_eid,
            legacy_source_namespace_id=self.legacy_source_namespace_id,
            target_identity_namespace_id=self.target_identity_namespace_id,
            nodes_source=self.nodes_source,
            optional_edges_source=self.optional_edges_source,
            legacy_representation_source=self.legacy_representation_source,
        )


@dataclass(frozen=True)
class MetadataLessPerEidQualificationIntent:
    """Immutable source qualification intent for later durable B3B idempotency."""

    idempotency_namespace_id: UUID
    idempotency_key: str
    source: QualifiedMetadataLessPerEidLegacySource

    def __post_init__(self) -> None:
        _uuid(self.idempotency_namespace_id, "idempotency_namespace_id")
        if not isinstance(self.idempotency_key, str) or not self.idempotency_key:
            raise MetadataLessPerEidLegacySourceRefused("idempotency_key must be non-empty text")
        if not isinstance(self.source, QualifiedMetadataLessPerEidLegacySource):
            raise MetadataLessPerEidLegacySourceRefused("source must be qualified metadata-less evidence")

    @property
    def identity_payload(self) -> dict[str, object]:
        return {
            "idempotency_namespace_id": str(self.idempotency_namespace_id),
            "idempotency_key": self.idempotency_key,
            "source": self.source.identity_payload(),
        }

    @property
    def identity_digest(self) -> str:
        return hashlib.sha256(canonical_intent_text(self.identity_payload).encode("utf-8")).hexdigest()


def require_metadata_less_qualification_retry_compatibility(
    previous: MetadataLessPerEidQualificationIntent,
    retry: MetadataLessPerEidQualificationIntent,
) -> None:
    """Refuse a changed semantic source under the same idempotency identity."""
    if not isinstance(previous, MetadataLessPerEidQualificationIntent) or not isinstance(
        retry, MetadataLessPerEidQualificationIntent
    ):
        raise MetadataLessPerEidLegacySourceRefused("qualification retry intents are required")
    previous_key = (previous.idempotency_namespace_id, previous.idempotency_key)
    retry_key = (retry.idempotency_namespace_id, retry.idempotency_key)
    if previous_key != retry_key:
        raise MetadataLessPerEidLegacySourceRefused("qualification retry does not use the same idempotency identity")
    if previous.identity_digest != retry.identity_digest:
        raise SubstrateIdempotencyConflict("metadata-less qualification intent differs")


def qualify_metadata_less_per_eid_legacy_source(
    *,
    data_root: str | Path,
    scope_key: RootScopeKey,
    legacy_eid: int,
    legacy_source_namespace_id: UUID,
    target_identity_namespace_id: UUID,
    nodes_source: ExplicitSourceEvidence,
    optional_edges_source: ExplicitSourceEvidence,
    legacy_representation_source: ExplicitSourceEvidence,
) -> QualifiedMetadataLessPerEidLegacySource:
    """Qualify one explicit metadata-less source without vector promotion."""
    _private_scope(scope_key)
    _eid(legacy_eid)
    _uuid(legacy_source_namespace_id, "legacy_source_namespace_id")
    _uuid(target_identity_namespace_id, "target_identity_namespace_id")
    if legacy_source_namespace_id == target_identity_namespace_id:
        raise MetadataLessPerEidLegacySourceRefused("source and target namespaces must remain distinct")
    _validate_nodes_source(nodes_source, scope_key)
    _validate_optional_edges_source(optional_edges_source, scope_key)
    _validate_representation_source(legacy_representation_source, scope_key, legacy_eid)
    manifest = RootEvidenceManifest((nodes_source, optional_edges_source, legacy_representation_source))
    manifest.verify(data_root=data_root)
    payload = _canonical_payload_for_eid(
        resolve_explicit_source_evidence_path(data_root=data_root, evidence=nodes_source), legacy_eid
    )
    try:
        canonical_input = select_canonical_embedding_input(payload)
    except CanonicalEmbeddingInputUnavailable as exc:
        raise MetadataLessPerEidLegacySourceRefused("canonical embedding input is unavailable") from exc
    dtype, shape, dimension = _observe_npy_vector(
        resolve_explicit_source_evidence_path(data_root=data_root, evidence=legacy_representation_source)
    )
    retained = RetainedMetadataLessLegacyVectorEvidence(
        scope_key=scope_key,
        legacy_eid=legacy_eid,
        canonical_locator=legacy_representation_source.canonical_locator,
        byte_length=legacy_representation_source.byte_length or 0,
        sha256_hex=legacy_representation_source.sha256_hex or "",
        array_dtype=dtype,
        array_shape=shape,
        dimension=dimension,
        legacy_source_namespace_id=legacy_source_namespace_id,
        target_identity_namespace_id=target_identity_namespace_id,
    )
    identity_payload = {
        "scope_key": scope_key.identity_payload(),
        "legacy_eid": legacy_eid,
        "legacy_source_namespace_id": str(legacy_source_namespace_id),
        "target_identity_namespace_id": str(target_identity_namespace_id),
        "nodes_source_identity": _evidence_identity(nodes_source),
        "optional_edges_source_identity": _evidence_identity(optional_edges_source),
        "legacy_representation_source_identity": _evidence_identity(legacy_representation_source),
        "evidence_manifest_digest": manifest.digest,
        "canonical_embedding_input": {
            "field": canonical_input.field,
            "digest": canonical_input.digest,
        },
        "retained_legacy_vector": retained.identity_payload(),
        "representation_identity": MetadataLessRepresentationIdentity.UNKNOWN.value,
        "legacy_vector_strategy": LegacyVectorStrategy.REEMBED_REQUIRED.value,
    }
    source_identity = hashlib.sha256(canonical_intent_text(identity_payload).encode("utf-8")).hexdigest()
    return QualifiedMetadataLessPerEidLegacySource(
        scope_key=scope_key,
        legacy_eid=legacy_eid,
        legacy_source_namespace_id=legacy_source_namespace_id,
        target_identity_namespace_id=target_identity_namespace_id,
        nodes_source=nodes_source,
        optional_edges_source=optional_edges_source,
        legacy_representation_source=legacy_representation_source,
        evidence_manifest=manifest,
        canonical_embedding_input=canonical_input,
        retained_legacy_vector=retained,
        source_evidence_identity=source_identity,
    )


def _validate_nodes_source(evidence: ExplicitSourceEvidence, scope_key: RootScopeKey) -> None:
    _validate_source(
        evidence,
        scope_key,
        owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
        semantic_role=EvidenceSemanticRole.NODES,
        locator="nodes.jsonl",
        expectation=EvidencePresenceExpectation.EXPECTED_PRESENT,
    )


def _validate_optional_edges_source(evidence: ExplicitSourceEvidence, scope_key: RootScopeKey) -> None:
    _validate_source(
        evidence,
        scope_key,
        owner_class=SourceOwnerClass.PRIVATE_GRAPH_SOURCE,
        semantic_role=EvidenceSemanticRole.EDGES,
        locator="edges.jsonl",
        expectation=None,
    )
    if evidence.presence_expectation is EvidencePresenceExpectation.EXPECTED_ABSENT and (
        evidence.absence_reason is not EvidenceAbsenceReason.OPTIONAL_EDGE_SOURCE
    ):
        raise MetadataLessPerEidLegacySourceRefused("absent edges source must be OPTIONAL_EDGE_SOURCE")


def _validate_representation_source(
    evidence: ExplicitSourceEvidence,
    scope_key: RootScopeKey,
    legacy_eid: int,
) -> None:
    _validate_source(
        evidence,
        scope_key,
        owner_class=SourceOwnerClass.METADATA_LESS_PER_EID_LEGACY_REPRESENTATION,
        semantic_role=EvidenceSemanticRole.LEGACY_REPRESENTATION,
        locator=f"emb_{legacy_eid}.npy",
        expectation=EvidencePresenceExpectation.EXPECTED_PRESENT,
    )


def _validate_source(
    evidence: ExplicitSourceEvidence,
    scope_key: RootScopeKey,
    *,
    owner_class: SourceOwnerClass,
    semantic_role: EvidenceSemanticRole,
    locator: str,
    expectation: EvidencePresenceExpectation | None,
) -> None:
    if not isinstance(evidence, ExplicitSourceEvidence):
        raise MetadataLessPerEidLegacySourceRefused("declared source must be explicit evidence")
    if evidence.owner_class is not owner_class or evidence.semantic_role is not semantic_role:
        raise MetadataLessPerEidLegacySourceRefused("declared source uses an unqualified owner or semantic role")
    if evidence.scope_key != scope_key:
        raise MetadataLessPerEidLegacySourceRefused("declared source does not bind the private scope")
    if evidence.canonical_locator != locator:
        raise MetadataLessPerEidLegacySourceRefused("declared source locator is not the qualified form")
    if expectation is not None and evidence.presence_expectation is not expectation:
        raise MetadataLessPerEidLegacySourceRefused("declared source has an invalid presence expectation")


def _canonical_payload_for_eid(nodes_path: Path, legacy_eid: int) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    try:
        lines = nodes_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise MetadataLessPerEidLegacySourceRefused("nodes source is not readable UTF-8 JSONL") from exc
    for ordinal, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MetadataLessPerEidLegacySourceRefused(
                f"nodes source record {ordinal} is malformed"
            ) from exc
        if not isinstance(record, dict):
            raise MetadataLessPerEidLegacySourceRefused(f"nodes source record {ordinal} is not an object")
        record_eid = record.get("eid")
        if not isinstance(record_eid, int) or isinstance(record_eid, bool) or record_eid < 0:
            raise MetadataLessPerEidLegacySourceRefused(f"nodes source record {ordinal} has an invalid EID")
        if record_eid == legacy_eid:
            payload = record.get("payload")
            if not isinstance(payload, dict):
                raise MetadataLessPerEidLegacySourceRefused("source record has no canonical payload mapping")
            matches.append(payload)
    if not matches:
        raise MetadataLessPerEidLegacySourceRefused("declared legacy EID is absent from nodes source")
    if len(matches) != 1:
        raise MetadataLessPerEidLegacySourceRefused("declared legacy EID is not unique in nodes source")
    return matches[0]


def _observe_npy_vector(path: Path) -> tuple[str, tuple[int, ...], int]:
    try:
        value = np.load(path, allow_pickle=False)
    except (OSError, ValueError) as exc:
        raise MetadataLessPerEidLegacySourceRefused("legacy representation is not a structurally valid NPY array") from exc
    if not isinstance(value, np.ndarray) or value.dtype.hasobject or value.ndim != 1 or value.shape[0] < 1:
        raise MetadataLessPerEidLegacySourceRefused("legacy representation must be a non-object one-dimensional NPY vector")
    shape = tuple(int(item) for item in value.shape)
    return (str(value.dtype), shape, shape[0])


def _evidence_identity(evidence: ExplicitSourceEvidence) -> str:
    return hashlib.sha256(canonical_intent_text(evidence.identity_payload()).encode("utf-8")).hexdigest()


def _private_scope(scope_key: object) -> RootScopeKey:
    if not isinstance(scope_key, RootScopeKey) or scope_key.scope_kind is not RootScopeKind.PRIVATE:
        raise MetadataLessPerEidLegacySourceRefused("metadata-less source requires a PRIVATE RootScopeKey")
    return scope_key


def _eid(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise MetadataLessPerEidLegacySourceRefused("legacy_eid must be a non-negative integer")
    return value


def _nonnegative(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise MetadataLessPerEidLegacySourceRefused(f"{label} must be a non-negative integer")
    return value


def _uuid(value: object, label: str) -> UUID:
    if not isinstance(value, UUID):
        raise MetadataLessPerEidLegacySourceRefused(f"{label} must be a UUID")
    return value


def _sha256(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise MetadataLessPerEidLegacySourceRefused("source SHA-256 must be lowercase hexadecimal")
    try:
        int(value, 16)
    except ValueError as exc:
        raise MetadataLessPerEidLegacySourceRefused("source SHA-256 must be lowercase hexadecimal") from exc
    return value


__all__ = [
    "DIMENSION_DOES_NOT_ESTABLISH_REPRESENTATION_IDENTITY",
    "MetadataLessPerEidB3BInput",
    "MetadataLessPerEidLegacySourceRefused",
    "MetadataLessPerEidQualificationIntent",
    "MetadataLessRepresentationIdentity",
    "QualifiedMetadataLessPerEidLegacySource",
    "RetainedMetadataLessLegacyVectorEvidence",
    "UNKNOWN_LEGACY_VECTOR_CAN_BECOME_TARGET_BY_RELABEL",
    "UNKNOWN_MODEL_REMAINS_UNKNOWN",
    "UNKNOWN_PROVIDER_REMAINS_UNKNOWN",
    "qualify_metadata_less_per_eid_legacy_source",
    "require_metadata_less_qualification_retry_compatibility",
]
