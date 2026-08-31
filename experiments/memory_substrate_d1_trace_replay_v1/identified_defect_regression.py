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
import shutil
from typing import Any, Mapping

import numpy as np

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
    CoreD1SourceLocations,
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
from .half_life_input_identity import (
    RESIDUAL_FIXTURE_IDS,
    characterize_legacy_http_time_sensitivity,
    frozen_residual_half_lives,
    trace_half_life_values,
    verify_frozen_inputs_match_v1_native_artifact,
)
from .protocol import D1ProtocolError, sha256_value


REGRESSION_PROFILE = "D1_IDENTIFIED_DEFECT_REGRESSION_V1"
REGRESSION_PROFILE_V2 = "D1_IDENTIFIED_DEFECT_REGRESSION_V2"
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
    return _run_identified_defect_regression(
        work_root=work_root,
        profile=REGRESSION_PROFILE,
        use_frozen_storage_facts=False,
    )


def run_identified_defect_regression_v2(*, work_root: str | Path) -> dict[str, Any]:
    """Run D1O's same-storage-input successor to the retained V1 profile.

    V2 does not modify V1 or the historical D1 result.  It compares native
    durable scalar storage with the frozen storage-facing inputs, while the
    fresh legacy HTTP replay remains separately recorded as an upstream
    recomputation characterization.
    """
    return _run_identified_defect_regression(
        work_root=work_root,
        profile=REGRESSION_PROFILE_V2,
        use_frozen_storage_facts=True,
    )


def _run_identified_defect_regression(
    *, work_root: str | Path, profile: str, use_frozen_storage_facts: bool,
) -> dict[str, Any]:
    if profile not in (REGRESSION_PROFILE, REGRESSION_PROFILE_V2):
        raise D1ProtocolError("D1 identified-defect profile is unknown")
    fixture = CoreFrozenFixture.load()
    validate_frozen_core_input_contract(fixture)
    frozen_half_lives = frozen_residual_half_lives(fixture) if use_frozen_storage_facts else {}
    v1_artifact_precheck = (
        verify_frozen_inputs_match_v1_native_artifact(fixture)
        if use_frozen_storage_facts else {}
    )
    same_input_values = (
        (0.5, 0.95, *(frozen_half_lives[fixture_id] for fixture_id in RESIDUAL_FIXTURE_IDS))
        if use_frozen_storage_facts else ()
    )
    root = Path(work_root).resolve()
    ports = ConcreteCoreFormalExecutionPorts(
        administration_work_root=root,
        native_session_factory=RegressionNativeArmSession,
    )
    ports.verify_frozen_sources()
    native_same_input = (
        characterize_native_same_input_half_life_storage(
            target_root=root / "D1O_SAME_INPUT_NATIVE",
            fixture=fixture,
            half_life_inputs=same_input_values,
        )
        if use_frozen_storage_facts else ()
    )
    roots = {arm.arm_id: ports.allocate_arm_roots(arm) for arm in fixture.arms}
    arm_results: dict[str, dict[str, Any]] = {}
    restart: list[dict[str, Any]] = []
    retrieval: list[dict[str, Any]] = []
    structural: list[dict[str, Any]] = []
    for arm in fixture.arms:
        result, restart_row, retrieval_row, structural_rows = _run_arm(
            ports=ports,
            arm=arm,
            roots=roots[arm.arm_id],
            frozen_scalar_inputs=use_frozen_storage_facts,
            same_input_half_lives=(
                same_input_values if use_frozen_storage_facts and arm.arm_id == "M1_CREATE" else None
            ),
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
    common = {
        "profile": REGRESSION_PROFILE,
        "original_d1_difference_count": ORIGINAL_D1_DIFFERENCE_COUNT,
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
    if profile == REGRESSION_PROFILE:
        return {
            **common,
            "regression_v1_difference_count": len(all_differences),
            "regression_v1_difference_count_by_field": _counts(all_differences, "field"),
            "regression_v1_difference_count_by_event": _counts(all_differences, "fixture_id"),
        }

    traces = _residual_half_life_traces(fixture, arm_results)
    if not all(trace["frozen_input_equals_native_durable"] for trace in traces):
        raise D1ProtocolError("D1O found a native half-life persistence defect candidate; V2 is not valid")
    legacy_same_input = arm_results["M1_CREATE"].get("same_input_legacy_storage")
    same_input = _compare_same_input_storage(
        half_life_inputs=same_input_values,
        legacy_rows=legacy_same_input,
        native_rows=native_same_input,
    )
    if any(any(items for items in row["differences"].values()) for row in same_input):
        raise D1ProtocolError("D1O same-input storage parity failed; V2 is not valid")
    return {
        **common,
        "profile": REGRESSION_PROFILE_V2,
        "regression_v2_difference_count": len(all_differences),
        "regression_v2_difference_count_by_field": _counts(all_differences, "field"),
        "regression_v2_difference_count_by_event": _counts(all_differences, "fixture_id"),
        "v1_artifact_frozen_input_precheck": v1_artifact_precheck,
        "residual_half_life_trace": traces,
        "same_input_storage_characterization": same_input,
        "legacy_http_time_sensitivity": characterize_legacy_http_time_sensitivity(
            l0_root=CoreD1SourceLocations.frozen_default().l0_root,
        ),
        "upstream_recomputation_characterization": True,
    }


def _run_arm(
    *,
    ports: ConcreteCoreFormalExecutionPorts,
    arm: CoreFrozenArm,
    roots: CoreArmRoots,
    frozen_scalar_inputs: bool,
    same_input_half_lives: tuple[float, ...] | None,
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
    same_input_legacy_storage: tuple[tuple[float, float], ...] | None = None
    try:
        if same_input_half_lives is not None:
            same_input_legacy_storage = legacy.characterize_same_input_half_life_storage(
                same_input_half_lives,
            )
        for event in arm.events:
            legacy_evidence, legacy_semantic, fresh_http_signal_half_life, fresh_http_half_life_inputs = legacy.replay_identified_defect_regression(
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
                event_storage, event_post = _compare_stored(
                    legacy_evidence,
                    native_evidence,
                    frozen_scalar_values=(
                        event.native_request()
                        if frozen_scalar_inputs and event.fixture_id in RESIDUAL_FIXTURE_IDS else None
                    ),
                )
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
                "fresh_legacy_http_signal_half_life": fresh_http_signal_half_life,
                "fresh_legacy_half_life_inputs": dict(fresh_http_half_life_inputs or {}),
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
                "same_input_legacy_storage": (
                    [list(row) for row in same_input_legacy_storage]
                    if same_input_legacy_storage is not None else None
                ),
                "storage_scalar_comparator": (
                    "frozen_half_life_for_named_03B_residuals"
                    if frozen_scalar_inputs else "fresh_legacy_durable_state"
                ),
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


def characterize_native_same_input_half_life_storage(
    *,
    target_root: str | Path,
    fixture: CoreFrozenFixture,
    half_life_inputs: tuple[float, ...],
) -> tuple[tuple[float, float], ...]:
    """Persist explicit half-life facts through the qualified native CREATE route.

    The source N0 is copied first and never opened for writes.  Each request
    carries a caller-supplied, deterministic float32 basis vector, so this
    characterization neither invokes legacy HTTP cognition nor generates an
    embedding.
    """
    root = Path(target_root).resolve()
    if root.exists() or not half_life_inputs:
        raise D1ProtocolError("D1O native same-input root must be new and inputs non-empty")
    inputs = tuple(float(item) for item in half_life_inputs)
    if any(not np.isfinite(item) or item <= 0.0 for item in inputs):
        raise D1ProtocolError("D1O native same-input half-life must be finite and positive")
    if len(inputs) > 16:
        raise D1ProtocolError("D1O native same-input inventory exceeds its bounded limit")
    source = CoreD1SourceLocations.frozen_default().n0_root
    try:
        shutil.copytree(source, root)
    except OSError as exc:
        raise CoreFormalPortFailure("D1O could not clone the qualified N0 source") from exc
    stored_events = [event for arm in fixture.arms for event in arm.events if not event.is_no_write]
    if not stored_events:
        raise D1ProtocolError("D1O fixture lacks a stored request for native CREATE characterization")
    base = _facts_from_mapping(stored_events[0].native_request())
    native = QualifiedNativeArmSession(root)
    try:
        rows: list[tuple[float, float]] = []
        for ordinal, half_life in enumerate(inputs):
            vector = np.zeros(384, dtype=np.float32)
            vector[320 + ordinal] = np.float32(1.0)
            vector.setflags(write=False)
            facts = replace(
                base,
                fixture_id=f"D1O-SAME-INPUT-{ordinal}",
                native_operation_key=f"D1O:SAME_INPUT_HALF_LIFE:{ordinal}",
                text=f"D1O same-input native half-life {ordinal}",
                summary=f"D1O same-input native half-life {ordinal}",
                embedding=vector,
                half_life_days=half_life,
                logical_step=base.logical_step + ordinal + 1,
                created_ts=base.created_ts + ordinal + 1,
                last_active_ts=base.last_active_ts + ordinal + 1,
                last_reinforced_ts=base.last_reinforced_ts + ordinal + 1,
            )
            evidence = native._replay_facts(facts)
            try:
                durable = float(evidence.storage["half_life_days"])
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                raise CoreFormalPortFailure("D1O native CREATE did not expose a durable half-life") from exc
            rows.append((half_life, durable))
        return tuple(rows)
    finally:
        native.close()


def _residual_half_life_traces(
    fixture: CoreFrozenFixture,
    arm_results: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    frozen = frozen_residual_half_lives(fixture)
    by_fixture: dict[str, Mapping[str, Any]] = {}
    for arm in arm_results.values():
        metrics = arm.get("metric_characterization")
        if not isinstance(metrics, list):
            raise D1ProtocolError("D1O arm has no metric characterization")
        for row in metrics:
            if isinstance(row, Mapping) and isinstance(row.get("fixture_id"), str):
                by_fixture[str(row["fixture_id"])] = row
    traces: list[dict[str, Any]] = []
    for fixture_id in RESIDUAL_FIXTURE_IDS:
        row = by_fixture.get(fixture_id)
        if row is None or not isinstance(row.get("legacy"), Mapping) or not isinstance(row.get("native"), Mapping):
            raise D1ProtocolError(f"D1O lacks A/B/C/D evidence for {fixture_id}")
        traces.append(trace_half_life_values(
            fixture_id=fixture_id,
            frozen_storage_fact=frozen[fixture_id],
            native_durable=row["native"].get("half_life_days"),
            fresh_legacy_durable=row["legacy"].get("half_life_days"),
            fresh_legacy_signal=row.get("fresh_legacy_http_signal_half_life"),
            fresh_legacy_half_life_inputs=row.get("fresh_legacy_half_life_inputs"),
        ))
    return traces


def _compare_same_input_storage(
    *,
    half_life_inputs: tuple[float, ...],
    legacy_rows: Any,
    native_rows: tuple[tuple[float, float], ...],
) -> list[dict[str, Any]]:
    if not isinstance(legacy_rows, list) or len(legacy_rows) != len(half_life_inputs):
        raise D1ProtocolError("D1O legacy same-input storage evidence is incomplete")
    if len(native_rows) != len(half_life_inputs):
        raise D1ProtocolError("D1O native same-input storage evidence is incomplete")
    output: list[dict[str, Any]] = []
    for ordinal, supplied in enumerate(half_life_inputs):
        legacy_row = legacy_rows[ordinal]
        if not isinstance(legacy_row, list) or len(legacy_row) != 2:
            raise D1ProtocolError("D1O legacy same-input row is malformed")
        try:
            legacy_input, legacy_durable = (float(item) for item in legacy_row)
            native_input, native_durable = (float(item) for item in native_rows[ordinal])
        except (TypeError, ValueError, OverflowError) as exc:
            raise D1ProtocolError("D1O same-input storage row is not numeric") from exc
        if legacy_input != supplied or native_input != supplied:
            raise D1ProtocolError("D1O same-input storage row changed its supplied fact")
        comparisons = {
            "input_vs_legacy_durable": _as_dicts(compare_scalar(
                supplied, legacy_durable, field="input_half_life/legacy_durable_half_life",
            )),
            "input_vs_native_durable": _as_dicts(compare_scalar(
                supplied, native_durable, field="input_half_life/native_durable_half_life",
            )),
            "legacy_durable_vs_native_durable": _as_dicts(compare_scalar(
                legacy_durable, native_durable, field="legacy_durable_half_life/native_durable_half_life",
            )),
        }
        output.append({
            "input_half_life": supplied,
            "legacy_durable_half_life": legacy_durable,
            "native_durable_half_life": native_durable,
            "differences": comparisons,
        })
    return output


def _compare_stored(
    legacy: CoreReplayEvidence,
    native: CoreReplayEvidence,
    *,
    frozen_scalar_values: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _require_fields(legacy.storage, (*_STORAGE_EXACT_FIELDS, *_STORAGE_SCALAR_FIELDS), boundary="legacy")
    _require_fields(native.storage, (*_STORAGE_EXACT_FIELDS, *_STORAGE_SCALAR_FIELDS), boundary="native")
    _require_fields(legacy.post_write, _POST_WRITE_EXACT_FIELDS, boundary="legacy post-write")
    _require_fields(native.post_write, _POST_WRITE_EXACT_FIELDS, boundary="native post-write")
    storage = _as_dicts(compare_exact_fields(legacy.storage, native.storage, _STORAGE_EXACT_FIELDS))
    for field in _STORAGE_SCALAR_FIELDS:
        left = legacy.storage[field]
        # D1O changes only the unresolved 03B half-life comparator.  The
        # strength/confidence/reinforcement comparisons retain V1's actual
        # durable-state basis; replacing their basis with pre-write signal
        # facts would widen this half-life archaeology into unrelated fields.
        if frozen_scalar_values is not None and field == "half_life_days":
            if field not in frozen_scalar_values:
                raise D1ProtocolError(f"D1O frozen storage facts lack scalar {field}")
            left = frozen_scalar_values[field]
        storage.extend(_as_dicts(compare_scalar(left, native.storage[field], field=field)))
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
    parser = argparse.ArgumentParser(description="run a bounded D1 identified-defect regression profile")
    parser.add_argument("--work-root", required=True)
    parser.add_argument("--profile", choices=("v1", "v2"), default="v1")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--summary-json-path")
    args = parser.parse_args(argv)
    result = (
        run_identified_defect_regression_v2(work_root=args.work_root)
        if args.profile == "v2" else run_identified_defect_regression_v1(work_root=args.work_root)
    )
    if args.summary:
        keys = (
            "profile", "original_d1_difference_count", "regression_v1_difference_count",
            "regression_v1_difference_count_by_field", "regression_v1_difference_count_by_event",
            "regression_v2_difference_count", "regression_v2_difference_count_by_field",
            "regression_v2_difference_count_by_event", "post_write_difference_count",
            "m4_native_contradiction_independently_created",
            "sequential_native_contradiction_independently_created",
            "residual_half_life_trace", "same_input_storage_characterization",
            "legacy_http_time_sensitivity", "formal_administration_created",
            "production_activation_changed",
        )
        result = {key: result[key] for key in keys if key in result}
    rendered = json.dumps(result, sort_keys=True)
    if args.summary_json_path is not None:
        destination = Path(args.summary_json_path).resolve()
        if destination.exists() or destination.parent != Path(args.work_root).resolve():
            raise D1ProtocolError("D1 regression summary path must be a new direct child of its disposable work root")
        destination.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ORIGINAL_D1_DIFFERENCE_COUNT", "REGRESSION_PROFILE", "REGRESSION_PROFILE_V2",
    "RegressionNativeArmSession", "characterize_native_same_input_half_life_storage",
    "native_owned_contradiction_guard", "run_identified_defect_regression_v1",
    "run_identified_defect_regression_v2",
]
