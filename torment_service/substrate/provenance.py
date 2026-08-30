"""Shared immutable substrate provenance input.

The row shape is intentionally separate from the qualification writer so pure
translation code can prepare the exact closed-child input without constructing
a write-capable service.
"""
from __future__ import annotations

from dataclasses import dataclass


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


__all__ = ["NativeProvenanceRecord"]
