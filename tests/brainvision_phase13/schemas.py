"""Canonical manifest and synthetic-result schema mechanics for Phase 13."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Final


BLOCK_IDS: Final[tuple[str, ...]] = tuple(f"E{number}" for number in range(1, 13))
TOP_LEVEL_PASS: Final = "V1A_QUALIFICATION_PASS"
TOP_LEVEL_FAIL: Final = "V1A_QUALIFICATION_FAIL"
TOP_LEVEL_INVALID: Final = "V1A_QUALIFICATION_INVALID"
FAIL_SCIENTIFIC: Final = "FAIL_SCIENTIFIC"
FAIL_IMPLEMENTATION: Final = "FAIL_IMPLEMENTATION"
INVALID_ADMINISTRATION: Final = "INVALID_ADMINISTRATION"
INVALID_ENVIRONMENT: Final = "INVALID_ENVIRONMENT"


def canonical_json_bytes(value: object) -> bytes:
    """Encode a test-only manifest with deterministic ASCII JSON."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256_hex(value: bytes) -> str:
    if type(value) is not bytes:
        raise TypeError("value must be bytes")
    return sha256(value).hexdigest()


def require_exact_block_ids(blocks: Mapping[str, object]) -> None:
    if tuple(blocks) != BLOCK_IDS:
        raise ValueError("Phase-13 blocks must be exactly E1 through E12 in order")


@dataclass(frozen=True, kw_only=True)
class SyntheticBlockResult:
    """A synthetic unit-test input; it is never qualification evidence."""

    block_id: str
    outcome: str
    subcode: str | None = None

    def __post_init__(self) -> None:
        if self.block_id not in BLOCK_IDS:
            raise ValueError("unknown Phase-13 block")
        if self.outcome not in {"PASS", "FAIL", "UNEXECUTED"}:
            raise ValueError("unsupported synthetic block outcome")
        if self.outcome == "FAIL" and self.subcode not in {
            FAIL_SCIENTIFIC,
            FAIL_IMPLEMENTATION,
        }:
            raise ValueError("FAIL requires a frozen FAIL subcode")
        if self.outcome != "FAIL" and self.subcode is not None:
            raise ValueError("only FAIL may carry a FAIL subcode")


@dataclass(frozen=True, kw_only=True)
class TaxonomyDecision:
    """Pure aggregation result for unit tests and later external grading."""

    top_level: str | None
    subcode: str | None
    block_results: tuple[SyntheticBlockResult, ...]


@dataclass(frozen=True, kw_only=True)
class ExecutionDefect:
    """Safe, bounded description of a post-start test-instrument defect."""

    block_id: str
    operation_index: int | None
    operation: str | None
    arm: str | None
    exception_class: str
    field: str | None = None
    reason: str | None = None
    durable_committed: bool | None = None
    invalid_subcode: str = INVALID_ADMINISTRATION

    def __post_init__(self) -> None:
        if self.block_id not in BLOCK_IDS or self.invalid_subcode not in {
            INVALID_ADMINISTRATION,
            INVALID_ENVIRONMENT,
        }:
            raise ValueError("invalid bounded execution defect")


@dataclass(frozen=True, kw_only=True)
class BlockExecutionEvidence:
    """Ungraded operation evidence returned by the live backend for one block."""

    block_id: str
    operations: tuple[object, ...]
    complete: bool = True
    defect: ExecutionDefect | None = None

    def __post_init__(self) -> None:
        if self.block_id not in BLOCK_IDS:
            raise ValueError("unknown Phase-13 block")
        if self.complete != (self.defect is None):
            raise ValueError("complete block evidence must agree with defect presence")


def aggregate_taxonomy(
    results: Iterable[SyntheticBlockResult],
    *,
    administration_defect_after_start: bool = False,
    environment_prevented_completion: bool = False,
) -> TaxonomyDecision:
    """Apply the frozen PASS/FAIL/INVALID precedence without executing blocks."""
    collected = tuple(results)
    failures = tuple(item for item in collected if item.outcome == "FAIL")
    if failures:
        subcode = (
            FAIL_SCIENTIFIC
            if any(item.subcode == FAIL_SCIENTIFIC for item in failures)
            else FAIL_IMPLEMENTATION
        )
        return TaxonomyDecision(
            top_level=TOP_LEVEL_FAIL,
            subcode=subcode,
            block_results=collected,
        )
    if administration_defect_after_start:
        return TaxonomyDecision(
            top_level=TOP_LEVEL_INVALID,
            subcode=INVALID_ADMINISTRATION,
            block_results=collected,
        )
    if environment_prevented_completion:
        return TaxonomyDecision(
            top_level=TOP_LEVEL_INVALID,
            subcode=INVALID_ENVIRONMENT,
            block_results=collected,
        )
    if tuple(item.block_id for item in collected) != BLOCK_IDS:
        raise ValueError("PASS requires exactly one result for each required block")
    if any(item.outcome != "PASS" for item in collected):
        raise ValueError("incomplete non-failure administration has no taxonomy result")
    return TaxonomyDecision(
        top_level=TOP_LEVEL_PASS,
        subcode=None,
        block_results=collected,
    )


__all__ = (
    "BLOCK_IDS",
    "BlockExecutionEvidence",
    "ExecutionDefect",
    "FAIL_IMPLEMENTATION",
    "FAIL_SCIENTIFIC",
    "INVALID_ADMINISTRATION",
    "INVALID_ENVIRONMENT",
    "SyntheticBlockResult",
    "TOP_LEVEL_FAIL",
    "TOP_LEVEL_INVALID",
    "TOP_LEVEL_PASS",
    "TaxonomyDecision",
    "aggregate_taxonomy",
    "canonical_json_bytes",
    "require_exact_block_ids",
    "sha256_hex",
)
