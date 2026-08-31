"""Frozen bounded D1 comparison helpers; no broad TORMENT-parity claim."""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from .protocol import ComparisonTolerances, D1ProtocolError, FROZEN_TOLERANCES, require_frozen_tolerances


@dataclass(frozen=True)
class ComparisonDifference:
    field: str
    legacy: Any
    native: Any
    rule: str


@dataclass(frozen=True)
class ComparisonResult:
    differences: tuple[ComparisonDifference, ...]

    @property
    def equivalent(self) -> bool:
        return not self.differences


def compare_exact_fields(legacy: Mapping[str, Any], native: Mapping[str, Any], fields: Iterable[str]) -> ComparisonResult:
    differences = [
        ComparisonDifference(field, legacy.get(field), native.get(field), "exact")
        for field in fields if legacy.get(field) != native.get(field)
    ]
    return ComparisonResult(tuple(differences))


def compare_vector(legacy: Any, native: Any, *, tolerances: ComparisonTolerances = FROZEN_TOLERANCES) -> ComparisonResult:
    require_frozen_tolerances(tolerances)
    left, right = np.asarray(legacy, dtype=np.float32).reshape(-1), np.asarray(native, dtype=np.float32).reshape(-1)
    if left.shape != right.shape or not np.allclose(left, right, rtol=tolerances.centroid_rtol, atol=tolerances.centroid_atol):
        return ComparisonResult((ComparisonDifference("vector", left.tolist(), right.tolist(), "centroid rtol=1e-6 atol=1e-7"),))
    return ComparisonResult(())


def compare_scalar(legacy: float, native: float, *, field: str, tolerances: ComparisonTolerances = FROZEN_TOLERANCES) -> ComparisonResult:
    require_frozen_tolerances(tolerances)
    if not isclose(float(legacy), float(native), rel_tol=0.0, abs_tol=tolerances.scalar_atol):
        return ComparisonResult((ComparisonDifference(field, legacy, native, "absolute tolerance 1e-6"),))
    return ComparisonResult(())


def compare_rankings(
    legacy: Sequence[tuple[Any, float]], native: Sequence[tuple[Any, float]], *, tolerances: ComparisonTolerances = FROZEN_TOLERANCES,
) -> ComparisonResult:
    require_frozen_tolerances(tolerances)
    if len(legacy) != len(native) or {item[0] for item in legacy} != {item[0] for item in native}:
        return ComparisonResult((ComparisonDifference("ranking identities", legacy, native, "same identity multiset"),))
    native_scores = dict(native)
    differences: list[ComparisonDifference] = []
    for identity, legacy_score in legacy:
        native_score = native_scores[identity]
        if not isclose(float(legacy_score), float(native_score), rel_tol=0.0, abs_tol=tolerances.retrieval_score_atol):
            differences.append(ComparisonDifference(f"ranking score:{identity}", legacy_score, native_score, "absolute tolerance 1e-6"))
    legacy_position, native_position = {identity: index for index, (identity, _) in enumerate(legacy)}, {identity: index for index, (identity, _) in enumerate(native)}
    for index, (left, left_score) in enumerate(legacy):
        for right, right_score in legacy[index + 1:]:
            if abs(float(left_score) - float(right_score)) > tolerances.ranking_order_epsilon:
                if (legacy_position[left] < legacy_position[right]) != (native_position[left] < native_position[right]):
                    differences.append(ComparisonDifference(f"ranking order:{left}/{right}", legacy_position[left], native_position[left], "order required above 1e-6 gap"))
    return ComparisonResult(tuple(differences))


def validate_native_structure(values: Mapping[str, bool]) -> None:
    required = {"uuid_uniqueness", "correct_parentage", "revision_advancement", "current_revision_ownership", "operation_ownership", "idempotency", "retry_stability"}
    if set(values) != required or not all(values.values()):
        raise D1ProtocolError("native-only structural qualification is incomplete")
