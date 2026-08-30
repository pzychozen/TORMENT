"""Shared pure payload-shadow policy for compatibility and translation."""
from __future__ import annotations

from typing import Any, Mapping

from torment_service.candidate_types import CandidateShapedValue


MEMORY_STRUCTURAL_PAYLOAD_KEYS = frozenset({
    "semantic_scope_id", "scope", "lifecycle", "lifecycle_state", "lifecycle_status",
    "lifecycle_authoritative", "governance", "governance_state", "authority_category",
    "authorization", "provenance", "provenance_id", "identity_namespace_id", "object_id",
    "object_kind", "eid", "revision", "revision_id", "object_revision_id",
    "object_revision_ordinal", "predecessor", "predecessor_revision_id",
    "predecessor_revision_ordinal", "representation", "representation_id", "readiness",
    "representation_readiness", "integrity", "integrity_expectation", "integrity_measurement",
    "reconciliation", "operation_id", "transition_id",
})

RELATIONSHIP_STRUCTURAL_PAYLOAD_KEYS = MEMORY_STRUCTURAL_PAYLOAD_KEYS | frozenset({
    "relationship_id", "relationship_kind", "relationship_revision_id",
    "relationship_revision_ordinal", "endpoint", "endpoints", "endpoint_ordinal",
    "endpoint_role", "endpoint_semantic_scope_id", "source", "source_eid",
    "target", "target_eid", "binding", "binding_mode", "bound_object_revision_id",
    "bound_object_revision_ordinal", "weight", "legacy_timestamp", "authority",
    "active_authorization", "authorization_state",
})


def copy_memory_flexible_payload(
    value: Mapping[str, Any] | None, *, field: str,
) -> dict[str, Any]:
    """Copy ordinary memory fields and refuse substrate structural shadows."""
    if isinstance(value, CandidateShapedValue):
        raise TypeError(f"candidate-shaped value cannot be written as ordinary memory {field}")
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an ordinary mapping")
    copied = dict(value)
    for key, item in copied.items():
        if not isinstance(key, str):
            raise ValueError(f"{field} keys must be strings")
        if isinstance(item, CandidateShapedValue):
            raise TypeError("candidate-shaped value cannot be written into ordinary memory payload")
        if key.casefold() in MEMORY_STRUCTURAL_PAYLOAD_KEYS:
            raise ValueError(f"{field} cannot overwrite structural substrate semantics")
    return copied


def copy_relationship_flexible_payload(
    value: Mapping[str, Any] | None, *, field: str,
) -> dict[str, Any]:
    """Copy ordinary relationship fields and refuse relationship shadows."""
    if isinstance(value, CandidateShapedValue):
        raise TypeError(f"candidate-shaped value cannot be written as relationship {field}")
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an ordinary mapping")
    copied = dict(value)
    for key, item in copied.items():
        if not isinstance(key, str):
            raise ValueError(f"{field} keys must be strings")
        if isinstance(item, CandidateShapedValue):
            raise TypeError("candidate-shaped value cannot be written into relationship payload")
        if key.casefold() in RELATIONSHIP_STRUCTURAL_PAYLOAD_KEYS:
            raise ValueError(f"{field} cannot overwrite structural relationship semantics")
    return copied


__all__ = [
    "MEMORY_STRUCTURAL_PAYLOAD_KEYS",
    "RELATIONSHIP_STRUCTURAL_PAYLOAD_KEYS",
    "copy_memory_flexible_payload",
    "copy_relationship_flexible_payload",
]
