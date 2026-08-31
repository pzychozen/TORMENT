"""Frozen, evidence-bounded governance translation for legacy core rows.

This is intentionally narrower than the legacy runtime resolver: it accepts
only a *missing* governance carrier on an otherwise nested legacy node row.
Partial, malformed, or second-carrier governance evidence remains unresolved.
"""
from __future__ import annotations

from typing import Any

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.governance import resolve_governance


LEGACY_ABSENT_GOVERNANCE_DEFAULT_V1 = "LEGACY_ABSENT_GOVERNANCE_DEFAULT_V1"
GOVERNANCE_FIELDS = (
    "protected",
    "non_shareable",
    "collective_export_blocked",
    "collective_reingest_blocked",
    "decay_accelerated",
)


def exact_governance_values(payload: dict[str, Any] | None) -> tuple[bool, ...] | str | None:
    """Return exact five-flag evidence; do not apply legacy defaults here."""
    if payload is None or "governance" not in payload:
        return None
    raw = payload["governance"]
    if not isinstance(raw, dict) or set(raw) != set(GOVERNANCE_FIELDS):
        return "INVALID"
    values = tuple(raw[name] for name in GOVERNANCE_FIELDS)
    return values if all(type(value) is bool for value in values) else "INVALID"


def derivable_absent_governance_values(
    raw_row: dict[str, Any] | None,
    payload: dict[str, Any] | None,
) -> tuple[bool, ...] | None:
    """Apply the frozen legacy absent-governance rule, or decline to derive.

    The caller separately establishes that lifecycle evidence is valid.  This
    helper never treats a null, partial, malformed, or outer-carrier value as
    absence, and it uses the production resolver rather than duplicating its
    default semantics.
    """
    if not isinstance(raw_row, dict) or not isinstance(payload, dict):
        return None
    if raw_row.get("payload") is not payload:
        return None
    if "governance" in raw_row or "governance" in payload:
        return None
    resolved = resolve_governance(payload)
    if resolved != MemoryGovernanceFlags():
        return None
    values = tuple(getattr(resolved, field) for field in GOVERNANCE_FIELDS)
    return values if all(type(value) is bool for value in values) else None
