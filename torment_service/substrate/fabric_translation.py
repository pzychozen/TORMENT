"""Pure structural translation for the deferred Fabric native-write seam.

This module deliberately constructs no substrate service and accepts no
connection.  It prepares immutable inputs which a later A3C2 transaction may
publish atomically; it grants no routing or persistence authority itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.provenance_v1 import ProvenanceV1

from .object_revision_governance import NativeMemoryGovernanceFacts
from .payload_policy import copy_memory_flexible_payload
from .provenance import NativeProvenanceRecord
from .runtime_binding import NativeMemoryRuntimeScope


_PRIVATE_AGENT_SCOPE = "PRIVATE_AGENT"
_SHARED_DOMAIN_SCOPE = "SHARED_DOMAIN"
_DESCRIPTIVE_PROVENANCE_FORMAT = "TORMENT_PROVENANCE_V1_DESCRIPTIVE/1"
_UNRESOLVED_LINEAGE_EVIDENCE = "UNRESOLVED_NAMESPACED_LEGACY_LINEAGE_EVIDENCE"
_CANONICAL_UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

ABSENT = "ABSENT"
RESOLVABLE_NATIVE_COMPAT_LINK = "RESOLVABLE_NATIVE_COMPAT_LINK"
QUALIFIED_COMPAT_LINK_INTENT = "QUALIFIED_COMPAT_LINK_INTENT"
UNRESOLVED_LEGACY_LINK_REFERENCE = "UNRESOLVED_LEGACY_LINK_REFERENCE"


@dataclass(frozen=True)
class QualifiedCompatibilityLinkTarget:
    """Caller-established native compatibility target, without resolution."""

    target_legacy_source_namespace_id: UUID
    target_eid: int

    def __post_init__(self) -> None:
        if not isinstance(self.target_legacy_source_namespace_id, UUID):
            raise ValueError("target_legacy_source_namespace_id must be a UUID")
        _validate_eid(self.target_eid, field="target_eid")


@dataclass(frozen=True)
class QualifiedCompatibilityLinkIntent:
    """A3C2-ready target intent; exact alias resolution remains transactional."""

    target_legacy_source_namespace_id: UUID
    target_eid: int
    classification: str = field(default=QUALIFIED_COMPAT_LINK_INTENT, init=False)


@dataclass(frozen=True)
class UnresolvedLegacyLinkReference:
    """Descriptive raw-link evidence with no semantic target identity."""

    raw_reference: str
    source_index: int
    classification: str = field(default=UNRESOLVED_LEGACY_LINK_REFERENCE, init=False)


@dataclass(frozen=True)
class FabricStructuralTranslationRequest:
    """Narrow immutable input used to prepare a native memory composition."""

    workspace_id: str
    scope: str
    legacy_source_namespace_id: UUID
    identity_namespace_id: UUID
    semantic_scope_id: UUID
    provenance: ProvenanceV1
    governance: MemoryGovernanceFlags
    agent_id: str | None = None
    domain_id: str | None = None
    raw_links: tuple[str, ...] | list[str] | None = None
    qualified_link_targets: tuple[QualifiedCompatibilityLinkTarget, ...] | list[QualifiedCompatibilityLinkTarget] = ()

    def __post_init__(self) -> None:
        _validate_request_identity(self)
        if not isinstance(self.provenance, ProvenanceV1):
            raise ValueError("provenance must be a ProvenanceV1 instance")
        if not isinstance(self.governance, MemoryGovernanceFlags):
            raise ValueError("governance must be MemoryGovernanceFlags")
        object.__setattr__(self, "raw_links", _normalise_raw_links(self.raw_links))
        object.__setattr__(
            self,
            "qualified_link_targets",
            _normalise_qualified_targets(self.qualified_link_targets),
        )


@dataclass(frozen=True)
class NativeFabricStructuralTranslation:
    """Immutable, non-persistent inputs for the future A3C2 transaction."""

    runtime_scope: NativeMemoryRuntimeScope
    semantic_scope_id: UUID
    provenance: NativeProvenanceRecord
    governance: NativeMemoryGovernanceFacts
    legacy_scope_projection: Mapping[str, str]
    link_classification: str
    qualified_link_intents: tuple[QualifiedCompatibilityLinkIntent, ...]
    unresolved_link_references: tuple[UnresolvedLegacyLinkReference, ...]


def translate_fabric_structural(
    request: FabricStructuralTranslationRequest,
) -> NativeFabricStructuralTranslation:
    """Translate validated legacy structural facts without I/O or mutation."""
    if not isinstance(request, FabricStructuralTranslationRequest):
        raise ValueError("a FabricStructuralTranslationRequest is required")
    runtime_scope = _translate_runtime_scope(request)
    provenance = translate_provenance_v1(request.provenance)
    governance = translate_governance_flags(request.governance)
    qualified_intents = tuple(
        QualifiedCompatibilityLinkIntent(
            target.target_legacy_source_namespace_id,
            target.target_eid,
        )
        for target in request.qualified_link_targets
    )
    unresolved = tuple(
        UnresolvedLegacyLinkReference(raw_reference=value, source_index=index)
        for index, value in enumerate(request.raw_links)
    )
    if unresolved:
        classification = UNRESOLVED_LEGACY_LINK_REFERENCE
    elif qualified_intents:
        classification = QUALIFIED_COMPAT_LINK_INTENT
    else:
        classification = ABSENT
    return NativeFabricStructuralTranslation(
        runtime_scope=runtime_scope,
        semantic_scope_id=request.semantic_scope_id,
        provenance=provenance,
        governance=governance,
        legacy_scope_projection=MappingProxyType(project_legacy_scope(runtime_scope)),
        link_classification=classification,
        qualified_link_intents=qualified_intents,
        unresolved_link_references=unresolved,
    )


def translate_provenance_v1(provenance: ProvenanceV1) -> NativeProvenanceRecord:
    """Map a validated ``ProvenanceV1`` to its closed-child row input."""
    if not isinstance(provenance, ProvenanceV1):
        raise ValueError("provenance must be a ProvenanceV1 instance")
    payload = _revalidate_provenance(provenance)
    capture_time_ns = _capture_time_ns(payload["created_at_ts"])
    envelope: dict[str, Any] = {
        "format": _DESCRIPTIVE_PROVENANCE_FORMAT,
        "provenance_v1": payload,
    }
    if payload["parent_eids"]:
        envelope["parent_eids_classification"] = _UNRESOLVED_LINEAGE_EVIDENCE
    return NativeProvenanceRecord(
        origin_kind="RUNTIME_PROVENANCE_V1",
        source_channel=payload["source_type"],
        source_role=payload["source_role"],
        derivation_status=payload["write_path"],
        uncertainty_state="UNKNOWN",
        source_time_ns=None,
        capture_time_ns=capture_time_ns,
        memory_role=None,
        descriptive_notes=json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ),
    )


def translate_governance_flags(
    governance: MemoryGovernanceFlags,
) -> NativeMemoryGovernanceFacts:
    """Copy every legacy governance boolean into the v1.1 typed carrier."""
    if not isinstance(governance, MemoryGovernanceFlags):
        raise ValueError("governance must be MemoryGovernanceFlags")
    facts = NativeMemoryGovernanceFacts(
        protected=governance.protected,
        non_shareable=governance.non_shareable,
        collective_export_blocked=governance.collective_export_blocked,
        collective_reingest_blocked=governance.collective_reingest_blocked,
        decay_accelerated=governance.decay_accelerated,
    )
    facts.as_storage_tuple()
    return facts


def project_legacy_governance(
    facts: NativeMemoryGovernanceFacts,
) -> MemoryGovernanceFlags:
    """Return the exact legacy-shaped governance vector for parity checks."""
    if not isinstance(facts, NativeMemoryGovernanceFacts):
        raise ValueError("facts must be NativeMemoryGovernanceFacts")
    facts.as_storage_tuple()
    return MemoryGovernanceFlags(
        protected=facts.protected,
        non_shareable=facts.non_shareable,
        collective_export_blocked=facts.collective_export_blocked,
        collective_reingest_blocked=facts.collective_reingest_blocked,
        decay_accelerated=facts.decay_accelerated,
    )


def project_legacy_scope(scope: NativeMemoryRuntimeScope) -> dict[str, str]:
    """Project a runtime scope back to the non-authoritative Fabric shape."""
    _validate_runtime_scope(scope)
    if scope.scope_kind == _PRIVATE_AGENT_SCOPE:
        return {
            "scope": "private",
            "workspace_id": scope.workspace_id,
            "agent_id": scope.agent_id or "",
        }
    return {
        "scope": "shared",
        "workspace_id": scope.workspace_id,
        "domain_id": scope.domain_id or "",
    }


def prepare_flexible_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Copy an ordinary Fabric payload while refusing structural shadows.

    The compatibility writer owns the shared forbidden-key doctrine.  This
    wrapper intentionally gives A3C2 the same pure validation without opening
    a write path or allowing a second structural-key list to drift.
    """
    return copy_memory_flexible_payload(payload, field="fabric payload")


def _translate_runtime_scope(
    request: FabricStructuralTranslationRequest,
) -> NativeMemoryRuntimeScope:
    if request.scope == "private":
        scope_kind = _PRIVATE_AGENT_SCOPE
    elif request.scope == "shared":
        scope_kind = _SHARED_DOMAIN_SCOPE
    else:  # Request validation keeps this branch defensive for mutated DTOs.
        raise ValueError("scope must be 'private' or 'shared'")
    scope = NativeMemoryRuntimeScope(
        workspace_id=request.workspace_id,
        scope_kind=scope_kind,
        legacy_source_namespace_id=request.legacy_source_namespace_id,
        identity_namespace_id=request.identity_namespace_id,
        semantic_scope_id=request.semantic_scope_id,
        agent_id=request.agent_id,
        domain_id=request.domain_id,
    )
    _validate_runtime_scope(scope)
    return scope


def _validate_request_identity(request: FabricStructuralTranslationRequest) -> None:
    if not isinstance(request.workspace_id, str) or not request.workspace_id:
        raise ValueError("workspace_id must be a non-empty string")
    for field_name in (
        "legacy_source_namespace_id",
        "identity_namespace_id",
        "semantic_scope_id",
    ):
        if not isinstance(getattr(request, field_name), UUID):
            raise ValueError(f"{field_name} must be a UUID")
    if request.scope == "private":
        if not isinstance(request.agent_id, str) or not request.agent_id:
            raise ValueError("private scope requires a non-empty agent_id")
        if request.domain_id is not None:
            raise ValueError("private scope cannot carry domain_id")
    elif request.scope == "shared":
        if not isinstance(request.domain_id, str) or not request.domain_id:
            raise ValueError("shared scope requires a non-empty domain_id")
        if request.agent_id is not None:
            raise ValueError("shared scope cannot carry agent_id")
    else:
        raise ValueError("scope must be 'private' or 'shared'")


def _validate_runtime_scope(scope: NativeMemoryRuntimeScope) -> None:
    if not isinstance(scope, NativeMemoryRuntimeScope):
        raise ValueError("scope must be NativeMemoryRuntimeScope")
    if not isinstance(scope.workspace_id, str) or not scope.workspace_id:
        raise ValueError("runtime scope workspace_id must be a non-empty string")
    for field_name in (
        "legacy_source_namespace_id",
        "identity_namespace_id",
        "semantic_scope_id",
    ):
        if not isinstance(getattr(scope, field_name), UUID):
            raise ValueError(f"runtime scope {field_name} must be a UUID")
    if scope.scope_kind == _PRIVATE_AGENT_SCOPE:
        if not isinstance(scope.agent_id, str) or not scope.agent_id or scope.domain_id is not None:
            raise ValueError("PRIVATE_AGENT scope requires only a non-empty agent_id")
    elif scope.scope_kind == _SHARED_DOMAIN_SCOPE:
        if not isinstance(scope.domain_id, str) or not scope.domain_id or scope.agent_id is not None:
            raise ValueError("SHARED_DOMAIN scope requires only a non-empty domain_id")
    else:
        raise ValueError("unknown runtime scope kind")


def _normalise_raw_links(value: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (tuple, list)):
        raise ValueError("raw_links must be a list or tuple of strings when supplied")
    if any(not isinstance(item, str) for item in value):
        raise ValueError("raw_links must contain only strings")
    return tuple(value)


def _normalise_qualified_targets(
    value: tuple[QualifiedCompatibilityLinkTarget, ...] | list[QualifiedCompatibilityLinkTarget],
) -> tuple[QualifiedCompatibilityLinkTarget, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError("qualified_link_targets must be a list or tuple")
    if any(not isinstance(item, QualifiedCompatibilityLinkTarget) for item in value):
        raise ValueError("qualified_link_targets must contain typed descriptors")
    return tuple(value)


def _validate_eid(value: Any, *, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")


def _revalidate_provenance(provenance: ProvenanceV1) -> dict[str, Any]:
    """Re-run the legacy validator without synthesising a translation time."""
    payload = provenance.to_dict()
    timestamp = provenance.created_at_ts
    if timestamp is None:
        validation_payload = dict(payload)
        validation_payload["created_at_ts"] = "1970-01-01T00:00:00Z"
        normalised = ProvenanceV1.from_dict(validation_payload).to_dict()
        normalised["created_at_ts"] = None
    else:
        normalised = ProvenanceV1.from_dict(payload).to_dict()
    if not isinstance(normalised.get("parent_eids"), list):
        raise ValueError("validated provenance parent_eids must be a list")
    return normalised


def _capture_time_ns(timestamp: str | None) -> int | None:
    if timestamp is None:
        return None
    if not isinstance(timestamp, str) or not _CANONICAL_UTC_TIMESTAMP.fullmatch(timestamp):
        raise ValueError("created_at_ts must be canonical UTC YYYY-MM-DDTHH:MM:SSZ")
    try:
        instant = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("created_at_ts must be a valid canonical UTC timestamp") from exc
    offset = instant - _EPOCH
    return ((offset.days * 86_400) + offset.seconds) * 1_000_000_000 + offset.microseconds * 1_000


__all__ = [
    "ABSENT",
    "QUALIFIED_COMPAT_LINK_INTENT",
    "RESOLVABLE_NATIVE_COMPAT_LINK",
    "UNRESOLVED_LEGACY_LINK_REFERENCE",
    "FabricStructuralTranslationRequest",
    "NativeFabricStructuralTranslation",
    "QualifiedCompatibilityLinkIntent",
    "QualifiedCompatibilityLinkTarget",
    "UnresolvedLegacyLinkReference",
    "prepare_flexible_payload",
    "project_legacy_governance",
    "project_legacy_scope",
    "translate_fabric_structural",
    "translate_governance_flags",
    "translate_provenance_v1",
]
