"""Read-only semantic projections for D1-identified-defect regression V1.

This module deliberately does not alter the historical D1 comparator.  It
provides a separate, narrow profile for the three comparison-surface findings
in the valid successor-002 result.  Every native provenance value is recovered
from its actual stored record; nothing is synthesized when evidence is absent.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Mapping

from torment_service.governance import resolve_governance
from torment_service.lifecycle import LifecycleState, read_lifecycle_envelope
from torment_service.provenance_v1 import ProvenanceV1

from .compare import ComparisonDifference
from .protocol import D1ProtocolError


_GOVERNANCE_FIELDS = (
    "protected",
    "non_shareable",
    "collective_export_blocked",
    "collective_reingest_blocked",
    "decay_accelerated",
)
_PROVENANCE_FIELDS = (
    "source_type",
    "source_role",
    "write_path",
    "created_at_step",
    "created_at_ts",
    "parent_eids",
    "schema_version",
)
_DESCRIPTIVE_PROVENANCE_FORMAT = "TORMENT_PROVENANCE_V1_DESCRIPTIVE/1"


class SemanticProjectionUnavailable(D1ProtocolError):
    """A required semantic fact cannot be recovered from durable evidence."""


def project_legacy_regression_semantics(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Project one actual legacy stored payload for the direct-ingest profile.

    The lifecycle projection intentionally concerns only the administered
    direct-ingest behavior.  It does not declare a global mapping between the
    legacy lifecycle envelope vocabulary and native structural states.
    """
    material = _mapping(payload, boundary="legacy stored payload")
    governance = asdict(resolve_governance(dict(material)))
    lifecycle = read_lifecycle_envelope(dict(material), now=0)
    return {
        "governance": _governance_projection(governance),
        "provenance": _provenance_projection(material.get("provenance"), boundary="legacy payload provenance"),
        "lifecycle": {
            # The actual CORE_ONLY direct-ingest rows are row-authoritative
            # `unset` rows with no join.  This is a narrow behavior witness,
            # not a string mapping from ACTIVE to ORDINARY.
            "ordinary_current_visible": (
                lifecycle.state is LifecycleState.UNSET
                and lifecycle.is_authoritative_on_row
                and lifecycle.requires_join is None
            ),
            "protected": bool(lifecycle.state is LifecycleState.PROTECTED or governance["protected"]),
            "legacy_authority_observation": {
                "state": lifecycle.state.value,
                "is_authoritative_on_row": lifecycle.is_authoritative_on_row,
                "requires_join": None if lifecycle.requires_join is None else lifecycle.requires_join.to_dict(),
            },
        },
    }


def project_legacy_durable_storage(
    storage: Mapping[str, Any], payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Replace only historical response-signal fields with durable payload facts."""
    output = dict(storage)
    material = _mapping(payload, boundary="legacy stored payload")
    for legacy_name, output_name in (
        ("strength", "strength"),
        ("confidence", "confidence"),
        ("half_life", "half_life_days"),
    ):
        if legacy_name not in material:
            raise SemanticProjectionUnavailable(
                f"legacy stored payload lacks required durable {legacy_name}"
            )
        try:
            output[output_name] = float(material[legacy_name])
        except (TypeError, ValueError, OverflowError) as exc:
            raise SemanticProjectionUnavailable(
                f"legacy stored payload has invalid durable {legacy_name}"
            ) from exc
    try:
        output["reinforcement_count"] = int(material.get("reinforcement_count", 0) or 0)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SemanticProjectionUnavailable(
            "legacy stored payload has invalid durable reinforcement_count"
        ) from exc
    return output


def project_native_regression_semantics(
    *,
    existence_state: str,
    lifecycle_state: str,
    lifecycle_authoritative: bool,
    governance: Mapping[str, Any],
    provenance_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Recover the native behavioral projection from exact current revision facts."""
    facts = _governance_projection(governance)
    return {
        "governance": facts,
        "provenance": _native_provenance_projection(provenance_record),
        "lifecycle": {
            "ordinary_current_visible": (
                existence_state == "EXISTS" and lifecycle_state == "ORDINARY"
            ),
            "protected": facts["protected"],
            # This is retained as evidence only. Native has no named
            # lifecycle side-channel join representation to compare directly
            # to the legacy envelope's row/join authority.
            "native_authority_observation": {
                "existence_state": existence_state,
                "lifecycle_state": lifecycle_state,
                "lifecycle_authoritative": bool(lifecycle_authoritative),
                "named_join_representation": None,
            },
        },
    }


def compare_regression_semantics(
    legacy: Mapping[str, Any], native: Mapping[str, Any], *, frozen_provenance: Mapping[str, Any],
) -> tuple[ComparisonDifference, ...]:
    """Compare exactly the supported behavior facts of this narrow profile.

    A fresh ordinary legacy HTTP write stamps its own wall-clock
    ``created_at_ts``.  The immutable fixture's ProvenanceV1 value is the
    administered intent, so it is the only valid comparator for native
    retained provenance.  The fresh legacy payload remains recorded as an
    archaeological observation, not rewritten or discarded.
    """
    differences: list[ComparisonDifference] = []
    for field in _GOVERNANCE_FIELDS:
        left, right = legacy["governance"][field], native["governance"][field]
        if left != right:
            differences.append(ComparisonDifference(f"governance.{field}", left, right, "exact boolean"))
    expected_provenance = project_frozen_provenance_intent(frozen_provenance)
    for field in _PROVENANCE_FIELDS:
        left, right = expected_provenance[field], native["provenance"][field]
        if left != right:
            differences.append(ComparisonDifference(f"provenance.{field}", left, right, "exact retained intent"))
    for field in ("ordinary_current_visible", "protected"):
        left, right = legacy["lifecycle"][field], native["lifecycle"][field]
        if left != right:
            differences.append(ComparisonDifference(f"lifecycle.{field}", left, right, "direct-ingest behavior"))
    return tuple(differences)


def project_frozen_provenance_intent(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the sealed ProvenanceV1 intent without consulting a live row."""
    return _provenance_projection(value, boundary="frozen ProvenanceV1 intent")


def _native_provenance_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    value = _mapping(record, boundary="native provenance record")
    if value.get("origin_kind") != "RUNTIME_PROVENANCE_V1":
        raise SemanticProjectionUnavailable("native provenance record is not a ProvenanceV1 translation")
    raw = value.get("descriptive_notes")
    if not isinstance(raw, str) or not raw:
        raise SemanticProjectionUnavailable("native provenance record lacks retained descriptive evidence")
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SemanticProjectionUnavailable("native retained provenance evidence is not JSON") from exc
    if not isinstance(envelope, dict) or envelope.get("format") != _DESCRIPTIVE_PROVENANCE_FORMAT:
        raise SemanticProjectionUnavailable("native retained provenance evidence has an unknown format")
    return _provenance_projection(envelope.get("provenance_v1"), boundary="native retained ProvenanceV1 evidence")


def _provenance_projection(value: Any, *, boundary: str) -> dict[str, Any]:
    source = _mapping(value, boundary=boundary)
    try:
        canonical = ProvenanceV1.from_dict(dict(source)).to_dict()
    except (TypeError, ValueError) as exc:
        raise SemanticProjectionUnavailable(f"{boundary} is not a valid ProvenanceV1 value") from exc
    missing = [field for field in _PROVENANCE_FIELDS if field not in canonical]
    if missing:
        raise SemanticProjectionUnavailable(f"{boundary} lacks required semantic facts: {missing}")
    return {field: canonical[field] for field in _PROVENANCE_FIELDS}


def _governance_projection(value: Mapping[str, Any]) -> dict[str, bool]:
    material = _mapping(value, boundary="governance facts")
    output: dict[str, bool] = {}
    for field in _GOVERNANCE_FIELDS:
        item = material.get(field)
        if type(item) is not bool:
            raise SemanticProjectionUnavailable(f"governance fact {field} is not an exact boolean")
        output[field] = item
    return output


def _mapping(value: Any, *, boundary: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SemanticProjectionUnavailable(f"{boundary} is not a mapping")
    return value


__all__ = [
    "SemanticProjectionUnavailable",
    "compare_regression_semantics",
    "project_legacy_durable_storage",
    "project_legacy_regression_semantics",
    "project_frozen_provenance_intent",
    "project_native_regression_semantics",
]
