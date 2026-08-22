"""Detached, manifest-driven Phase-13 evidence grader.

This module intentionally has no import path to the execution backend or to
production ingress. It receives an already-written detached evidence package
and applies only the closed comparison vocabulary declared below.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Final

from brainvision_phase13.schemas import (
    BLOCK_IDS,
    FAIL_IMPLEMENTATION,
    FAIL_SCIENTIFIC,
    INVALID_ADMINISTRATION,
    INVALID_ENVIRONMENT,
    SyntheticBlockResult,
    TaxonomyDecision,
    aggregate_taxonomy,
    canonical_json_bytes,
)


PASS: Final = "PASS"
FAIL: Final = "FAIL"
INVALID: Final = "INVALID"
CRITERION_RELATIONS: Final[frozenset[str]] = frozenset(
    {
        "EXACT",
        "NOT_EQUAL",
        "CANONICAL_BYTES_EQUAL",
        "CANONICAL_BYTES_NOT_EQUAL",
        "MAPPING_EXACT",
        "ALL_FIELDS_EQUAL",
        "ALL_FIELDS_NOT_EQUAL",
        "ALL_PRESENT_RECORDS_FIELD_EXACT",
        "ALL_ARM_RECORDS_FIELD_EXACT",
        "AUTHORITY_ONLY_STRUCTURAL_REPRODUCTION_REFERENCE",
        "LESS_THAN",
        "PRESENT",
    }
)
_RAW_SELECTOR_FRAGMENTS: Final[tuple[str, ...]] = (
    "VheState",
    "FastTrace",
    "PersistentContext",
    "SemanticRegister",
    "runtime_snapshot.vhe_state",
    "amplitude",
    "remaining_ns",
    "write_gate",
    "gain",
    "orientation",
)
_NOT_APPLICABLE: Final = object()


@dataclass(frozen=True, kw_only=True)
class CriterionResult:
    criterion_id: str
    status: str
    relation: str
    evidence_refs: tuple[str, ...]
    failure_class: str


@dataclass(frozen=True, kw_only=True)
class GradedBlockResult:
    block_id: str
    status: str
    presentation_status: str
    subcode: str | None
    criterion_results: tuple[CriterionResult, ...]
    evidence_refs: tuple[str, ...]

    def synthetic_taxonomy_result(self) -> SyntheticBlockResult:
        return SyntheticBlockResult(
            block_id=self.block_id,
            outcome=("PASS" if self.status == PASS else "FAIL" if self.status == FAIL else "UNEXECUTED"),
            subcode=self.subcode if self.status == FAIL else None,
        )


@dataclass(frozen=True, kw_only=True)
class GradingRecord:
    manifest_sha256: str
    evidence_sha256: str
    blocks: tuple[GradedBlockResult, ...]
    taxonomy: TaxonomyDecision

    def to_canonical_bytes(self) -> bytes:
        return canonical_json_bytes(
            {
                "blocks": [
                    {
                        "block_id": block.block_id,
                        "criterion_results": [
                            {
                                "criterion_id": item.criterion_id,
                                "evidence_refs": list(item.evidence_refs),
                                "failure_class": item.failure_class,
                                "relation": item.relation,
                                "status": item.status,
                            }
                            for item in block.criterion_results
                        ],
                        "evidence_refs": list(block.evidence_refs),
                        "presentation_status": block.presentation_status,
                        "status": block.status,
                        "subcode": block.subcode,
                    }
                    for block in self.blocks
                ],
                "evidence_sha256": self.evidence_sha256,
                "manifest_sha256": self.manifest_sha256,
                "taxonomy": {"subcode": self.taxonomy.subcode, "top_level": self.taxonomy.top_level},
            }
        )


def validate_evidence_selector(selector: str) -> None:
    """Reject raw recursive-state selector paths before they can be graded."""
    if type(selector) is not str or not selector or selector.startswith("."):
        raise ValueError("criterion selector must be a nonempty relative path")
    if any(fragment.casefold() in selector.casefold() for fragment in _RAW_SELECTOR_FRAGMENTS):
        raise ValueError(f"raw-state selector is prohibited: {selector}")


def _resolve(mapping: Mapping[str, object], selector: str) -> object:
    validate_evidence_selector(selector)
    value: object = mapping
    for segment in selector.split("."):
        if isinstance(value, Mapping) and segment in value:
            value = value[segment]
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and segment.isdecimal():
            index = int(segment)
            if 0 <= index < len(value):
                value = value[index]
            else:
                raise KeyError(selector)
        else:
            raise KeyError(selector)
    return value


def _metric_value_or_not_applicable(record: Mapping[str, object], field_path: str) -> object:
    """Resolve a metric field only for structurally metric-bearing evidence."""

    if not field_path.startswith("metrics.") or "metrics" not in record:
        raise KeyError(field_path)
    metrics = record["metrics"]
    if metrics is None:
        return _NOT_APPLICABLE
    if not isinstance(metrics, Mapping):
        raise KeyError(field_path)
    return _resolve(record, field_path)


def _metric_records_field_exact(
    records: Sequence[object],
    *,
    field_path: str,
    expected: object,
) -> bool:
    """Require exact values from every applicable metric-bearing record."""

    observed = 0
    for record in records:
        if not isinstance(record, Mapping):
            return False
        try:
            value = _metric_value_or_not_applicable(record, field_path)
        except KeyError:
            return False
        if value is _NOT_APPLICABLE:
            continue
        observed += 1
        if value != expected:
            return False
    return observed > 0


def _comparison_passes(
    relation: str,
    actual_values: tuple[object, ...],
    criterion: Mapping[str, object],
) -> bool:
    expected = criterion.get("expected_value")
    if relation == "EXACT":
        return len(actual_values) == 1 and actual_values[0] == expected
    if relation == "NOT_EQUAL":
        return len(actual_values) == 2 and actual_values[0] != actual_values[1]
    if relation == "CANONICAL_BYTES_EQUAL":
        return len(actual_values) == 2 and actual_values[0] == actual_values[1]
    if relation == "CANONICAL_BYTES_NOT_EQUAL":
        return len(actual_values) == 2 and actual_values[0] != actual_values[1]
    if relation == "MAPPING_EXACT":
        return len(actual_values) == 1 and actual_values[0] == expected
    if relation == "PRESENT":
        return len(actual_values) == 1 and actual_values[0] is not None
    if relation == "LESS_THAN":
        return len(actual_values) == 2 and actual_values[0] < actual_values[1]
    if relation == "ALL_FIELDS_EQUAL":
        fields = criterion.get("fields")
        if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes)) or len(actual_values) != 2:
            return False
        return all(
            isinstance(actual_values[0], Mapping)
            and isinstance(actual_values[1], Mapping)
            and actual_values[0].get(field) == actual_values[1].get(field)
            for field in fields
        )
    if relation == "ALL_FIELDS_NOT_EQUAL":
        fields = criterion.get("fields")
        if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes)) or len(actual_values) != 2:
            return False
        return all(
            isinstance(actual_values[0], Mapping)
            and isinstance(actual_values[1], Mapping)
            and actual_values[0].get(field) != actual_values[1].get(field)
            for field in fields
        )
    if relation == "ALL_PRESENT_RECORDS_FIELD_EXACT":
        field_path = criterion.get("field_path")
        if (
            len(actual_values) != 1
            or not isinstance(actual_values[0], Sequence)
            or isinstance(actual_values[0], (str, bytes))
            or type(field_path) is not str
        ):
            return False
        return _metric_records_field_exact(
            actual_values[0], field_path=field_path, expected=expected
        )
    if relation == "ALL_ARM_RECORDS_FIELD_EXACT":
        field_path = criterion.get("field_path")
        if (
            len(actual_values) != 1
            or not isinstance(actual_values[0], Mapping)
            or type(field_path) is not str
        ):
            return False
        records: list[object] = []
        for arm in actual_values[0].values():
            if not isinstance(arm, Mapping) or not isinstance(arm.get("records"), Sequence):
                return False
            records.extend(arm["records"])
        return _metric_records_field_exact(
            records, field_path=field_path, expected=expected
        )
    raise ValueError(f"unknown criterion relation: {relation}")


def _grade_criterion(
    criterion: Mapping[str, object], evidence: Mapping[str, object]
) -> CriterionResult:
    criterion_id = criterion.get("criterion_id")
    relation = criterion.get("relation")
    failure_class = criterion.get("failure_class")
    selectors = criterion.get("actual_selectors")
    if (
        type(criterion_id) is not str
        or relation not in CRITERION_RELATIONS
        or failure_class not in {FAIL_SCIENTIFIC, FAIL_IMPLEMENTATION, INVALID_ADMINISTRATION}
        or not isinstance(selectors, Sequence)
        or isinstance(selectors, (str, bytes))
        or any(type(selector) is not str for selector in selectors)
    ):
        raise ValueError("malformed frozen criterion")
    if relation == "AUTHORITY_ONLY_STRUCTURAL_REPRODUCTION_REFERENCE":
        reference = criterion.get("authority_reference")
        passed = isinstance(reference, Mapping) and bool(reference)
        return CriterionResult(
            criterion_id=criterion_id,
            status=PASS if passed else FAIL,
            relation=relation,
            evidence_refs=(),
            failure_class=failure_class,
        )
    try:
        actual_values = tuple(_resolve(evidence, selector) for selector in selectors)
    except KeyError:
        return CriterionResult(
            criterion_id=criterion_id,
            status=INVALID,
            relation=relation,
            evidence_refs=tuple(selectors),
            failure_class=INVALID_ADMINISTRATION,
        )
    return CriterionResult(
        criterion_id=criterion_id,
        status=PASS if _comparison_passes(relation, actual_values, criterion) else FAIL,
        relation=relation,
        evidence_refs=tuple(selectors),
        failure_class=failure_class,
    )


def grade_block(
    *, block_id: str, expected: Mapping[str, object], evidence: Mapping[str, object]
) -> GradedBlockResult:
    """Apply only criteria declared in the supplied frozen block manifest."""
    criteria_document = expected.get("criteria") if isinstance(expected, Mapping) else None
    if block_id not in BLOCK_IDS or not isinstance(evidence, Mapping) or not isinstance(criteria_document, Sequence):
        return GradedBlockResult(
            block_id=block_id,
            status=INVALID,
            presentation_status="NOT_EXECUTED",
            subcode=INVALID_ADMINISTRATION,
            criterion_results=(),
            evidence_refs=(),
        )
    execution_state = evidence.get("execution_state", "COMPLETE")
    if execution_state == "NOT_EXECUTED":
        return GradedBlockResult(
            block_id=block_id,
            status=INVALID,
            presentation_status="NOT_EXECUTED",
            subcode=INVALID_ADMINISTRATION,
            criterion_results=(),
            evidence_refs=(),
        )
    presentation_status = "INCOMPLETE" if execution_state == "INCOMPLETE" else "INVALID"
    try:
        criteria = tuple(
            _grade_criterion(item, evidence)
            for item in criteria_document
            if isinstance(item, Mapping)
        )
    except ValueError:
        return GradedBlockResult(
            block_id=block_id,
            status=INVALID,
            presentation_status=presentation_status,
            subcode=INVALID_ADMINISTRATION,
            criterion_results=(),
            evidence_refs=(),
        )
    if len(criteria) != len(criteria_document):
        return GradedBlockResult(
            block_id=block_id,
            status=INVALID,
            presentation_status=presentation_status,
            subcode=INVALID_ADMINISTRATION,
            criterion_results=criteria,
            evidence_refs=tuple(ref for item in criteria for ref in item.evidence_refs),
        )
    if execution_state != "COMPLETE":
        return GradedBlockResult(
            block_id=block_id,
            status=INVALID,
            presentation_status=presentation_status,
            subcode=INVALID_ADMINISTRATION,
            criterion_results=criteria,
            evidence_refs=tuple(ref for item in criteria for ref in item.evidence_refs),
        )
    invalid = tuple(item for item in criteria if item.status == INVALID)
    if invalid:
        return GradedBlockResult(
            block_id=block_id,
            status=INVALID,
            presentation_status=presentation_status,
            subcode=INVALID_ADMINISTRATION,
            criterion_results=criteria,
            evidence_refs=tuple(ref for item in criteria for ref in item.evidence_refs),
        )
    failures = tuple(item for item in criteria if item.status == FAIL)
    subcode = (
        FAIL_SCIENTIFIC
        if any(item.failure_class == FAIL_SCIENTIFIC for item in failures)
        else FAIL_IMPLEMENTATION if failures else None
    )
    return GradedBlockResult(
        block_id=block_id,
        status=FAIL if failures else PASS,
        presentation_status="FAIL" if failures else "PASS",
        subcode=subcode,
        criterion_results=criteria,
        evidence_refs=tuple(ref for item in criteria for ref in item.evidence_refs),
    )


def grade_evidence_package(
    *, expected_manifest: Mapping[str, object], evidence_package: Mapping[str, object], manifest_sha256: str
) -> GradingRecord:
    """Grade one complete detached package without execution, recovery, or retry."""
    expected_blocks = expected_manifest.get("blocks")
    evidence_blocks = evidence_package.get("blocks")
    if not isinstance(expected_blocks, Mapping) or not isinstance(evidence_blocks, Mapping):
        raise ValueError("expected and evidence packages require block mappings")
    blocks = tuple(
        grade_block(
            block_id=block_id,
            expected=expected_blocks[block_id],
            evidence=evidence_blocks.get(block_id, {}),
        )
        for block_id in BLOCK_IDS
    )
    failures = tuple(block.synthetic_taxonomy_result() for block in blocks if block.status == FAIL)
    if failures:
        taxonomy = aggregate_taxonomy(failures)
    elif any(block.status == INVALID for block in blocks):
        environment_defect = any(
            isinstance(evidence_blocks.get(block.block_id), Mapping)
            and isinstance(evidence_blocks[block.block_id].get("defect"), Mapping)
            and evidence_blocks[block.block_id]["defect"].get("invalid_subcode") == INVALID_ENVIRONMENT
            for block in blocks
        )
        taxonomy = TaxonomyDecision(
            top_level="V1A_QUALIFICATION_INVALID",
            subcode=INVALID_ENVIRONMENT if environment_defect else INVALID_ADMINISTRATION,
            block_results=tuple(),
        )
    else:
        taxonomy = aggregate_taxonomy(tuple(block.synthetic_taxonomy_result() for block in blocks))
    raw = canonical_json_bytes(evidence_package)
    return GradingRecord(
        manifest_sha256=manifest_sha256,
        evidence_sha256=sha256(raw).hexdigest(),
        blocks=blocks,
        taxonomy=taxonomy,
    )


__all__ = (
    "CRITERION_RELATIONS",
    "CriterionResult",
    "GradedBlockResult",
    "GradingRecord",
    "grade_block",
    "grade_evidence_package",
    "validate_evidence_selector",
)
