"""Shared immutable substrate provenance input.

The row shape is intentionally separate from the qualification writer so pure
translation code can prepare the exact closed-child input without constructing
a write-capable service.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


UNKNOWN_ORIGINAL_PROVENANCE_ORIGIN_KIND = "MIGRATION_LEGACY_ORIGINAL_PROVENANCE_UNKNOWN"
UNKNOWN_ORIGINAL_PROVENANCE_DERIVATION_STATUS = "structural_witness"
UNKNOWN_ORIGINAL_PROVENANCE_UNCERTAINTY_STATE = "UNKNOWN"


@dataclass(frozen=True)
class NativeProvenanceRecord:
    """Exact existing provenance-row fields for one closed child."""

    origin_kind: str
    source_channel: str | None
    source_role: str | None
    derivation_status: str
    uncertainty_state: str
    source_time_ns: int | None = None
    capture_time_ns: int | None = None
    memory_role: str | None = None
    descriptive_notes: str | None = None


def unknown_original_provenance_record() -> NativeProvenanceRecord:
    """Return the one lawful native witness for an absent legacy source.

    This row proves only the native normalization lineage.  In particular its
    null source fields must never be treated as an inferred original source.
    """
    return NativeProvenanceRecord(
        origin_kind=UNKNOWN_ORIGINAL_PROVENANCE_ORIGIN_KIND,
        source_channel=None,
        source_role=None,
        derivation_status=UNKNOWN_ORIGINAL_PROVENANCE_DERIVATION_STATUS,
        uncertainty_state=UNKNOWN_ORIGINAL_PROVENANCE_UNCERTAINTY_STATE,
    )


def is_unknown_original_provenance_values(
    origin_kind: object,
    source_channel: object,
    source_role: object,
    derivation_status: object,
    uncertainty_state: object,
    source_time_ns: object = None,
    capture_time_ns: object = None,
    memory_role: object = None,
    descriptive_notes: object = None,
) -> bool:
    """Recognize precisely the Phase-C structural provenance field contract."""
    return (
        origin_kind == UNKNOWN_ORIGINAL_PROVENANCE_ORIGIN_KIND
        and source_channel is None
        and source_role is None
        and derivation_status == UNKNOWN_ORIGINAL_PROVENANCE_DERIVATION_STATUS
        and uncertainty_state == UNKNOWN_ORIGINAL_PROVENANCE_UNCERTAINTY_STATE
        and source_time_ns is None
        and capture_time_ns is None
        and memory_role is None
        and descriptive_notes is None
    )


def requires_character_provenance_witness(payload: Mapping[str, Any] | None) -> bool:
    """Keep Character seed-shaped legacy rows on their separately qualified path."""
    return isinstance(payload, Mapping) and payload.get("type") == "seed_canon"


def is_ordinary_unknown_original_provenance_candidate(
    raw_row: Mapping[str, Any] | None,
    payload: Mapping[str, Any] | None,
) -> bool:
    """Return whether both legacy carriers expressly omit original provenance.

    Presence of malformed, descriptive, or conflicting provenance remains a
    refusal; this function deliberately recognizes absence only.  Character
    seed-shaped rows are excluded before the ordinary B2 service can derive a
    structural witness.
    """
    return (
        isinstance(raw_row, Mapping)
        and isinstance(payload, Mapping)
        and "provenance" not in raw_row
        and "provenance" not in payload
        and not requires_character_provenance_witness(payload)
    )


__all__ = [
    "NativeProvenanceRecord",
    "UNKNOWN_ORIGINAL_PROVENANCE_DERIVATION_STATUS",
    "UNKNOWN_ORIGINAL_PROVENANCE_ORIGIN_KIND",
    "UNKNOWN_ORIGINAL_PROVENANCE_UNCERTAINTY_STATE",
    "is_ordinary_unknown_original_provenance_candidate",
    "is_unknown_original_provenance_values",
    "requires_character_provenance_witness",
    "unknown_original_provenance_record",
]
