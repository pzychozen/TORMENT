"""D1 identified-defect regression V1, separate from formal administration.

This is a bounded replay characterization over fresh clones of the frozen D1
fixture.  It creates no administration marker or formal result root, never
updates the original successor-002 record, and does not select a production
runtime.  Its only purpose is to prove or retain the named comparison-surface
findings against actual durable evidence.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any, Mapping

from torment_service.fabric import _detect_canon_conflict
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.object_revision_governance import NativeObjectRevisionGovernanceService

from .compare import (
    compare_exact_fields,
    compare_rankings,
    compare_scalar,
    compare_vector,
    validate_native_no_write_structure,
    validate_native_structure,
)
from .formal_core_executor import CoreFrozenArm, CoreFrozenEvent, CoreFrozenFixture, CoreReplayEvidence
from .formal_core_ports import (
    ConcreteCoreFormalExecutionPorts,
    CoreArmRoots,
    CoreFormalPortFailure,
    QualifiedNativeArmSession,
    _facts_from_mapping,
    validate_frozen_core_input_contract,
)
from .identified_defect_semantics import (
    compare_regression_semantics,
    project_frozen_provenance_intent,
    project_native_regression_semantics,
)
from .protocol import D1ProtocolError, sha256_value


REGRESSION_PROFILE = "D1_IDENTIFIED_DEFECT_REGRESSION_V1"
ORIGINAL_D1_DIFFERENCE_COUNT = 53
_STORAGE_EXACT_FIELDS = (
    "stored", "reinforced", "compatible_eid", "summary", "memory_type",
    "memory_class", "raw_representation_bytes", "motif_membership",
    "motif_geometry", "conflict",
)
_STORAGE_SCALAR_FIELDS = ("strength", "confidence", "half_life_days", "reinforcement_count")
_POST_WRITE_EXACT_FIELDS = ("qualified_post_write_outputs", "deterministic_runtime_ordering")
_NO_WRITE_STORAGE_FIELDS = (
    "stored", "reinforced", "compatible_eid", "conflict", "created_motif",
    "motif_membership", "motif_geometry",
)
_NO_WRITE_STORAGE_EXPECTED = {
    "stored": False, "reinforced": False, "compatible_eid": False,
    "conflict": None, "created_motif": None, "motif_membership": [], "motif_geometry": [],
}


def native_owned_contradiction_guard(incoming: str, existing: str, similarity: float) -> bool:
    """Use the production canon-conflict decision, with no legacy answer input."""
    return bool(_detect_canon_conflict(incoming, existing, float(similarity))[0])


class RegressionNativeArmSession(QualifiedNativeArmSession):
    """A qualified native arm whose only added input is the native guard."""

    def replay_identified_defect_regression(
        self, request: Mapping[str, Any],
    ) -> tuple[CoreReplayEvidence, Mapping[str, Any]]:
        facts = replace(
            _facts_from_mapping(request),
            contradiction_guard=native_owned_contradiction_guard,
        )
        outcome = self._replay_outcome(facts)
        assert outcome.route_attempt is not None and outcome.route_attempt.result is not None
        result = outcome.route_attempt.result
        evidence = self._evidence_for_result(facts, result, outcome.post_write_outcome)
        return evidence, self._semantic_evidence(result.eid)

    def _semantic_evidence(self, eid: int) -> Mapping[str, Any]:
        with open_existing_native_core_connection(self._database) as opened:
            connection = opened.connection
            view = NativeMemoryCompatibilityFacade(connection).get_memory_by_eid(
                legacy_source_namespace_id=self._scope.runtime.legacy_source_namespace_id,
                eid=eid,
            )
            governed = NativeObjectRevisionGovernanceService(connection).get_object_revision_governance(
                object_id=view.object_id,
                object_revision_id=view.revision_id,
                object_revision_ordinal=view.revision_ordinal,
            )
            if governed is None:
                raise CoreFormalPortFailure("native regression memory lacks revision-bound governance")
            if view.provenance_id is None:
                raise CoreFormalPortFailure("native regression memory lacks a provenance record")
            row = connection.execute(
                "SELECT origin_kind,descriptive_notes FROM provenance_records WHERE provenance_id=?",
                (view.provenance_id.bytes,),
            ).fetchone()
            if row is None:
                raise CoreFormalPortFailure("native regression provenance record is missing")
            facts = governed.facts
            return project_native_regression_semantics(
                existence_state=view.existence_state,
                lifecycle_state=view.lifecycle_state,
                lifecycle_authoritative=view.lifecycle_authoritative,
                governance={
                    "protected": facts.protected,
                    "non_shareable": facts.non_shareable,
                    "collective_export_blocked": facts.collective_export_blocked,
                    "collective_reingest_blocked": facts.collective_reingest_blocked,
                    "decay_accelerated": facts.decay_accelerated,
                },
                provenance_record={"origin_kind": row[0], "descriptive_notes": row[1]},
            )


def run_identified_defect_regression_v1(*, work_root: str | Path) -> dict[str, Any]:
    """Run the new isolated comparison profile once over six fresh arm clones."""
    fixture = CoreFrozenFixture.load()
    validate_frozen_core_input_contract(fixture)
    ports = ConcreteCoreFormalExecutionPorts(
        administration_work_root=work_root,
        native_session_factory=RegressionNativeArmSession,
    )
    ports.verify_frozen_sources()
    roots = {arm.arm_id: ports.allocate_arm_roots(arm) for arm in fixture.arms}
    arm_results: dict[str, dict[str, Any]] = {}
    restart: list[dict[str, Any]] = []
    retrieval: list[dict[str, Any]] = []
    structural: list[dict[str, Any]] = []
    for arm in fixture.arms:
        result, restart_row, retrieval_row, structural_rows = _run_arm(
            ports=ports, arm=arm, roots=roots[arm.arm_id],
        )
        arm_results[arm.arm_id] = result
        restart.append(restart_row)
        retrieval.append(retrieval_row)
        structural.extend(structural_rows)
    all_differences = [
        row
        for arm in arm_results.values()
        for row in arm["storage_differences"]
    ]
    post_write = [
        row
        for arm in arm_results.values()
        for row in arm["post_write_differences"]
    ]
    return {
        "profile": REGRESSION_PROFILE,
        "original_d1_difference_count": ORIGINAL_D1_DIFFERENCE_COUNT,
        "regression_v1_difference_count": len(all_differences),
        "regression_v1_difference_count_by_field": _counts(all_differences, "field"),
        "regression_v1_difference_count_by_event": _counts(all_differences, "fixture_id"),
        "post_write_difference_count": len(post_write),
        "post_write_difference_count_by_event": _counts(post_write, "fixture_id"),
        "arms": arm_results,
        "restart_evidence": restart,
        "retrieval_characterization": retrieval,
        "native_structural_invariants": structural,
        "m4_native_contradiction_independently_created": _m4_independent_create(arm_results),
        "sequential_native_contradiction_independently_created": _sequential_independent_create(arm_results),
        "formal_administration_created": False,
        "production_activation_changed": False,
    }


def _run_arm(
    *, ports: ConcreteCoreFormalExecutionPorts, arm: CoreFrozenArm, roots: CoreArmRoots,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    legacy = ports.open_legacy(arm, roots.legacy_root)
    try:
        native = ports.open_native(arm, roots.native_root)
    except Exception:
        legacy.close()
        raise
    storage_differences: list[dict[str, Any]] = []
    post_write_differences: list[dict[str, Any]] = []
    semantic_evidence: list[dict[str, Any]] = []
    native_outcomes: list[dict[str, Any]] = []
    metric_characterization: list[dict[str, Any]] = []
    structural: list[dict[str, Any]] = []
    try:
        for event in arm.events:
            legacy_evidence, legacy_semantic = legacy.replay_identified_defect_regression(
                event.legacy_http_request(),
            )
            _verify_legacy_expected(event, legacy_evidence)
            if event.is_no_write:
                if legacy_semantic is not None:
                    raise D1ProtocolError("M5 must not produce a legacy semantic projection")
                before = native.capture_durable_state()
                native_evidence = native.replay_no_write(event.native_request())
                after = native.capture_durable_state()
                if after != before:
                    raise D1ProtocolError("M5 NO_WRITE changed durable native storage")
                event_storage, event_post = _compare_no_write(legacy_evidence, native_evidence)
            else:
                native_evidence, native_semantic = native.replay_identified_defect_regression(event.native_request())
                if legacy_semantic is None:
                    raise D1ProtocolError("stored legacy event has no durable semantic projection")
                event_storage, event_post = _compare_stored(legacy_evidence, native_evidence)
                frozen_provenance = project_frozen_provenance_intent(
                    event.native_request()["provenance"],
                )
                semantic_differences = _as_dicts(compare_regression_semantics(
                    legacy_semantic, native_semantic, frozen_provenance=frozen_provenance,
                ))
                event_storage.extend(semantic_differences)
                semantic_evidence.append({
                    "fixture_id": event.fixture_id,
                    "frozen_provenance_intent": frozen_provenance,
                    "legacy": dict(legacy_semantic),
                    "native": dict(native_semantic),
                    "differences": semantic_differences,
                })
            native_outcomes.append({
                "fixture_id": event.fixture_id,
                "stored": native_evidence.storage.get("stored"),
                "reinforced": native_evidence.storage.get("reinforced"),
            })
            metric_characterization.append({
                "fixture_id": event.fixture_id,
                "legacy": _metric_characterization(legacy_evidence),
                "native": _metric_characterization(native_evidence),
            })
            storage_differences.extend({"fixture_id": event.fixture_id, **item} for item in event_storage)
            post_write_differences.extend({"fixture_id": event.fixture_id, **item} for item in event_post)
            if native_evidence.native_structural_invariants is None:
                raise D1ProtocolError("native regression evidence lacks structural invariants")
            if event.is_no_write:
                validate_native_no_write_structure(native_evidence.native_structural_invariants)
            else:
                validate_native_structure(native_evidence.native_structural_invariants)
            structural.append({
                "arm_id": arm.arm_id,
                "fixture_id": event.fixture_id,
                **dict(native_evidence.native_structural_invariants),
            })
        legacy_pre_restart = dict(legacy.capture_durable_state())
        legacy.restart_cleanly()
        legacy_post_restart = dict(legacy.capture_durable_state())
        native.close()
        native = ports.reopen_native(arm, roots.native_root)
        native_post_restart = dict(native.capture_durable_state())
        query = arm.events[0].query_vector()
        ranking = _as_dicts(compare_rankings(
            tuple(legacy.search_by_embedding(query)),
            tuple(native.compatibility_embedding_search(query)),
        ))
        return (
            {
                "arm_id": arm.arm_id,
                "event_order": [event.fixture_id for event in arm.events],
                "storage_differences": storage_differences,
                "post_write_differences": post_write_differences,
                "semantic_evidence": semantic_evidence,
                "native_outcomes": native_outcomes,
                "metric_characterization": metric_characterization,
                "legacy_clone_id": arm.legacy_clone_id,
                "native_clone_id": arm.native_clone_id,
            },
            {
                "arm_id": arm.arm_id,
                "legacy_pre_restart": legacy_pre_restart,
                "legacy_post_restart": legacy_post_restart,
                "native_post_restart": native_post_restart,
            },
            {
                "arm_id": arm.arm_id,
                "query_vector_sha256": sha256_value(query.tolist()),
                "ranking_differences": ranking,
                "D1_CLOSED_LOOP_QUERY_PARITY_TESTED": "NO",
            },
            structural,
        )
    finally:
        try:
            native.close()
        finally:
            legacy.close()


def _compare_stored(
    legacy: CoreReplayEvidence, native: CoreReplayEvidence,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _require_fields(legacy.storage, (*_STORAGE_EXACT_FIELDS, *_STORAGE_SCALAR_FIELDS), boundary="legacy")
    _require_fields(native.storage, (*_STORAGE_EXACT_FIELDS, *_STORAGE_SCALAR_FIELDS), boundary="native")
    _require_fields(legacy.post_write, _POST_WRITE_EXACT_FIELDS, boundary="legacy post-write")
    _require_fields(native.post_write, _POST_WRITE_EXACT_FIELDS, boundary="native post-write")
    storage = _as_dicts(compare_exact_fields(legacy.storage, native.storage, _STORAGE_EXACT_FIELDS))
    for field in _STORAGE_SCALAR_FIELDS:
        storage.extend(_as_dicts(compare_scalar(legacy.storage[field], native.storage[field], field=field)))
    storage.extend(_as_dicts(compare_vector(
        legacy.storage["raw_representation_vector"], native.storage["raw_representation_vector"],
    )))
    return storage, _as_dicts(compare_exact_fields(legacy.post_write, native.post_write, _POST_WRITE_EXACT_FIELDS))


def _compare_no_write(
    legacy: CoreReplayEvidence, native: CoreReplayEvidence,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    for boundary, evidence in (("legacy", legacy), ("native", native)):
        _require_fields(evidence.storage, _NO_WRITE_STORAGE_FIELDS, boundary=f"{boundary} M5")
        _require_fields(evidence.post_write, _POST_WRITE_EXACT_FIELDS, boundary=f"{boundary} M5 post-write")
        for field, expected in _NO_WRITE_STORAGE_EXPECTED.items():
            if evidence.storage[field] != expected:
                raise D1ProtocolError(f"{boundary} M5 does not preserve no-write truth: {field}")
    return (
        _as_dicts(compare_exact_fields(legacy.storage, native.storage, _NO_WRITE_STORAGE_FIELDS)),
        _as_dicts(compare_exact_fields(legacy.post_write, native.post_write, _POST_WRITE_EXACT_FIELDS)),
    )


def _verify_legacy_expected(event: CoreFrozenEvent, evidence: CoreReplayEvidence) -> None:
    if (
        evidence.storage.get("stored") != event.legacy_expected.get("stored")
        or evidence.storage.get("reinforced") != event.legacy_expected.get("reinforced")
    ):
        raise D1ProtocolError("legacy replay diverged from the frozen observed outcome")


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], *, boundary: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise D1ProtocolError(f"{boundary} evidence lacks required fields: {missing}")


def _as_dicts(result: Any) -> list[dict[str, Any]]:
    differences = result if isinstance(result, tuple) else result.differences
    return [asdict(item) for item in differences]


def _metric_characterization(evidence: CoreReplayEvidence) -> dict[str, Any]:
    """Record the named post-branch values without making them a new gate."""
    fields = (
        "summary", "motif_membership", "motif_geometry", "reinforcement_count",
        "strength", "confidence", "half_life_days",
    )
    return {field: evidence.storage.get(field) for field in fields}


def _counts(rows: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    output: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        output[value] = output.get(value, 0) + 1
    return dict(sorted(output.items()))


def _m4_independent_create(arms: Mapping[str, Mapping[str, Any]]) -> bool:
    return _has_independent_create(arms["M4_CONTRADICTION"], index=1)


def _sequential_independent_create(arms: Mapping[str, Mapping[str, Any]]) -> bool:
    return _has_independent_create(arms["SEQUENTIAL"], index=3)


def _has_independent_create(arm: Mapping[str, Any], *, index: int) -> bool:
    event_order = arm.get("event_order")
    outcomes = arm.get("native_outcomes")
    if not isinstance(event_order, list) or not isinstance(outcomes, list) or index >= len(event_order):
        return False
    fixture_id = event_order[index]
    matching = [row for row in outcomes if isinstance(row, Mapping) and row.get("fixture_id") == fixture_id]
    # This witness is the qualified native result itself, not a legacy EID or
    # legacy branch decision.  A contradiction event must publish a new memory
    # (stored) rather than a reinforcement successor.
    return len(matching) == 1 and matching[0].get("stored") is True and matching[0].get("reinforced") is False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="run D1 identified-defect regression V1")
    parser.add_argument("--work-root", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run_identified_defect_regression_v1(work_root=args.work_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ORIGINAL_D1_DIFFERENCE_COUNT", "REGRESSION_PROFILE", "RegressionNativeArmSession",
    "native_owned_contradiction_guard", "run_identified_defect_regression_v1",
]
