"""Focused contract tests for the frozen Phase-5 relational projection."""

from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from brainvision.fixtures import DA
from brainvision.projection import (
    ACCEPTANCE_RELEVANT_FIELD_SETS,
    BrainvisionProjectionV1,
    CURRENT_ACTIVITY_ROLE,
    OPEN_EVENT_ROLE,
    OPERATOR_ID,
    PRESENT_HISTORY_RELATION_ROLE,
    PROJECTION_ALGORITHM_ID,
    PROJECTION_HALF_QUANTUM_Q,
    PROJECTION_ID,
    PROJECTION_MANIFEST_CORE_CANONICAL_BYTES,
    PROJECTION_MANIFEST_CORE_SHA256,
    PROJECTION_QUANTUM_Q,
    PROJECTION_SCHEMA_ID,
    PROJECTION_STEPS,
    ProjectionValidationError,
    RECURRENCE_ROLE,
    RETAINED_HISTORY_ROLE,
    ROLE_BINDINGS,
    TRAJECTORY_ROLE,
    project_vhe_state,
    projection_manifest,
    projection_manifest_core,
    signed_code,
    unsigned_code,
    within_projection_quantum,
)
from brainvision.vhe import FAST_HORIZON_NS, fresh_vhe_state, update_vhe_state


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROJECTION_PATH = REPOSITORY_ROOT / "brainvision" / "projection.py"


def test_frozen_identity_and_exact_canonical_projection_dto() -> None:
    assert PROJECTION_SCHEMA_ID == "brainvision.projection.v1"
    assert PROJECTION_ALGORITHM_ID == "brainvision.projection.fixed16-relational.v1"
    assert PROJECTION_MANIFEST_CORE_SHA256 == (
        "c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f"
    )
    assert PROJECTION_ID == (
        "bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f"
    )
    projection = BrainvisionProjectionV1(
        current_activity_code=0,
        retained_history_code=0,
        present_history_relation_code=0,
        trajectory_code=0,
        open_event_class=None,
        recurrence_code=0,
    )
    assert projection.to_dict() == {
        "schema_id": "brainvision.projection.v1",
        "projection_id": PROJECTION_ID,
        "operator_id": "bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb",
        "current_activity_code": 0,
        "retained_history_code": 0,
        "present_history_relation_code": 0,
        "trajectory_code": 0,
        "open_event_class": None,
        "recurrence_code": 0,
    }
    assert projection.to_canonical_json_bytes() == (
        b'{"current_activity_code":0,"open_event_class":null,"operator_id":'
        b'"bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb",'
        b'"present_history_relation_code":0,"projection_id":'
        b'"bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f",'
        b'"recurrence_code":0,"retained_history_code":0,"schema_id":'
        b'"brainvision.projection.v1","trajectory_code":0}'
    )
    assert set(projection.to_dict()) == {
        "schema_id",
        "projection_id",
        "operator_id",
        "current_activity_code",
        "retained_history_code",
        "present_history_relation_code",
        "trajectory_code",
        "open_event_class",
        "recurrence_code",
    }


def test_exact_quantizer_domains_zero_bins_and_half_even_ties() -> None:
    assert PROJECTION_STEPS == 16
    assert PROJECTION_QUANTUM_Q == 62_500
    assert PROJECTION_HALF_QUANTUM_Q == 31_250

    assert unsigned_code(0) == 0
    assert unsigned_code(31_250) == 0
    assert unsigned_code(31_251) == 1
    assert unsigned_code(93_750) == 2
    assert unsigned_code(1_000_000) == 16

    assert signed_code(-1_000_000) == -16
    assert signed_code(-31_251) == -1
    assert signed_code(-31_250) == 0
    assert signed_code(0) == 0
    assert signed_code(31_250) == 0
    assert signed_code(31_251) == 1
    assert signed_code(93_750) == 2
    assert signed_code(1_000_000) == 16
    for value_q in (0, 1, 31_250, 31_251, 187_500, 500_000, 999_999, 1_000_000):
        assert signed_code(-value_q) == -signed_code(value_q)


@pytest.mark.parametrize("value", [-1, 1_000_001, True, 1.0])
def test_unsigned_quantizer_rejects_noncanonical_values(value: object) -> None:
    with pytest.raises(ProjectionValidationError):
        unsigned_code(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [-1_000_001, 1_000_001, True, 1.0])
def test_signed_quantizer_rejects_noncanonical_values(value: object) -> None:
    with pytest.raises(ProjectionValidationError):
        signed_code(value)  # type: ignore[arg-type]


def test_projection_dto_enforces_categorical_and_quantized_domains() -> None:
    with pytest.raises(ProjectionValidationError):
        BrainvisionProjectionV1(
            current_activity_code=17,
            retained_history_code=0,
            present_history_relation_code=0,
            trajectory_code=0,
            open_event_class=None,
            recurrence_code=0,
        )
    with pytest.raises(ProjectionValidationError):
        BrainvisionProjectionV1(
            current_activity_code=0,
            retained_history_code=0,
            present_history_relation_code=0,
            trajectory_code=0,
            open_event_class=None,
            recurrence_code=1,
        )
    with pytest.raises(ProjectionValidationError):
        BrainvisionProjectionV1(
            current_activity_code=0,
            retained_history_code=0,
            present_history_relation_code=0,
            trajectory_code=0,
            open_event_class="detector:scene_change",
            recurrence_code=0,
        )


def test_projection_is_a_pure_repeatable_as_of_read() -> None:
    state = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class="detector:scene_change",
        prior_committed_active_time_ns=11,
        elapsed_active_time_ns=7,
    ).state
    original_state = state

    first = project_vhe_state(state, FAST_HORIZON_NS)
    second = project_vhe_state(state, FAST_HORIZON_NS)

    assert state == original_state
    assert first == second
    assert first.to_canonical_json_bytes() == second.to_canonical_json_bytes()
    assert first.current_activity_code == 0
    assert first.retained_history_code == 8
    assert first.open_event_class == "detector:scene_change"
    assert first.recurrence_code == 1


def test_role_bindings_relevant_sets_and_exact_comparison_are_frozen() -> None:
    assert ROLE_BINDINGS == {
        CURRENT_ACTIVITY_ROLE: ("current_activity_code",),
        RETAINED_HISTORY_ROLE: ("retained_history_code",),
        PRESENT_HISTORY_RELATION_ROLE: ("present_history_relation_code",),
        TRAJECTORY_ROLE: ("trajectory_code",),
        OPEN_EVENT_ROLE: ("open_event_class",),
        RECURRENCE_ROLE: ("recurrence_code",),
    }
    assert ACCEPTANCE_RELEVANT_FIELD_SETS == {
        "retained_current_equality": ("current_activity_code",),
        "retained_history_difference": ("retained_history_code",),
        "order_current_equality": ("current_activity_code",),
        "order_history_difference": ("trajectory_code",),
        "present_history_relation": ("present_history_relation_code",),
        "open_event": ("open_event_class",),
        "recurrence": ("recurrence_code",),
    }

    baseline = BrainvisionProjectionV1(
        current_activity_code=0,
        retained_history_code=0,
        present_history_relation_code=0,
        trajectory_code=0,
        open_event_class=None,
        recurrence_code=0,
    )
    same_current = replace(baseline, retained_history_code=1)
    same_current_again = replace(same_current, trajectory_code=1)
    assert within_projection_quantum(
        baseline,
        same_current,
        ACCEPTANCE_RELEVANT_FIELD_SETS["retained_current_equality"],
    )
    assert within_projection_quantum(
        same_current,
        same_current_again,
        ACCEPTANCE_RELEVANT_FIELD_SETS["retained_current_equality"],
    )
    assert within_projection_quantum(
        baseline,
        same_current_again,
        ACCEPTANCE_RELEVANT_FIELD_SETS["retained_current_equality"],
    )
    assert not within_projection_quantum(
        baseline,
        same_current,
        ACCEPTANCE_RELEVANT_FIELD_SETS["retained_history_difference"],
    )
    with pytest.raises(ProjectionValidationError):
        within_projection_quantum(baseline, same_current, ("unknown",))


def test_public_role_and_relevant_field_mappings_are_immutable() -> None:
    original_bytes = PROJECTION_MANIFEST_CORE_CANONICAL_BYTES
    with pytest.raises(TypeError):
        ROLE_BINDINGS[TRAJECTORY_ROLE] = ("tampered",)  # type: ignore[index]
    with pytest.raises(TypeError):
        ACCEPTANCE_RELEVANT_FIELD_SETS["order_history_difference"] = (  # type: ignore[index]
            "tampered",
        )

    assert ROLE_BINDINGS[TRAJECTORY_ROLE] == ("trajectory_code",)
    assert ACCEPTANCE_RELEVANT_FIELD_SETS["order_history_difference"] == (
        "trajectory_code",
    )
    assert PROJECTION_MANIFEST_CORE_CANONICAL_BYTES == original_bytes
    assert PROJECTION_MANIFEST_CORE_SHA256 == (
        "c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f"
    )
    assert PROJECTION_ID == (
        "bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f"
    )


def test_manifest_is_complete_canonical_and_not_self_referential() -> None:
    core = projection_manifest_core()
    assert core["operator_id"] == OPERATOR_ID
    assert core["projection_schema_id"] == PROJECTION_SCHEMA_ID
    assert core["algorithm_id"] == PROJECTION_ALGORITHM_ID
    assert core["canonical_projection_field_specification"] == [
        "schema_id",
        "projection_id",
        "operator_id",
        "current_activity_code",
        "retained_history_code",
        "present_history_relation_code",
        "trajectory_code",
        "open_event_class",
        "recurrence_code",
    ]
    assert core["quantization"] == {
        "half_quantum_q": 31_250,
        "q": 1_000_000,
        "quantum_q": 62_500,
        "rounding_algorithm_id": "signed-quotient-remainder-half-even.v1",
        "rounding": "phase_4_signed_round_half_even",
        "signed": "RNE(PROJECTION_STEPS*q/Q),q_in[-Q,Q],output_in[-16,16]",
        "steps": 16,
        "unsigned": "RNE(PROJECTION_STEPS*q/Q),q_in[0,Q],output_in[0,16]",
        "zero_bins": {"signed": [-31_250, 31_250], "unsigned": [0, 31_250]},
    }
    assert core["clipping_rules"] == {
        "current_activity_q": "none;max_abs_f_eff_is_in[0,Q]",
        "present_history_relation_raw_q": "clamp(sum_of_two_mul_q_terms,-Q,Q)",
        "retained_history_q": "none;max_abs_S_is_in[0,Q]",
        "trajectory_q": "none;S.orientation_q_is_in[-Q,Q]",
    }
    assert core["fixture_expectations"]["semantic_recurrence"] == {
        "first": {"open_event_class": "detector:scene_change", "recurrence_code": 1},
        "fresh": {"open_event_class": None, "recurrence_code": 0},
        "initial_state": "fresh/reset neutral VHE",
        "new": {"open_event_class": "detector:motion", "recurrence_code": 1},
        "repeat": {"open_event_class": "detector:scene_change", "recurrence_code": 2},
        "transitions": "d0-only semantic observations",
        "under_that_fixture": "W=0;F/S unchanged",
    }
    assert core["role_bindings"] == {
        name: list(fields) for name, fields in ROLE_BINDINGS.items()
    }
    assert core["acceptance_relevant_field_sets"] == {
        name: list(fields) for name, fields in ACCEPTANCE_RELEVANT_FIELD_SETS.items()
    }
    assert core["pure_read"] == {
        "as_of": "evolve_vhe_state_as_of",
        "input": "committed VheState + elapsed_active_time_ns",
        "mutates_clock": False,
        "mutates_committed_vhe": False,
        "persistence_side_effect": False,
        "recursive_state": "none",
    }
    assert PROJECTION_ID not in core.values()
    assert PROJECTION_ID.encode("ascii") not in PROJECTION_MANIFEST_CORE_CANONICAL_BYTES
    assert PROJECTION_MANIFEST_CORE_CANONICAL_BYTES == json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    assert PROJECTION_MANIFEST_CORE_SHA256 == sha256(
        PROJECTION_MANIFEST_CORE_CANONICAL_BYTES
    ).hexdigest()
    assert PROJECTION_ID == "bvproj1_" + sha256(
        PROJECTION_MANIFEST_CORE_CANONICAL_BYTES
    ).hexdigest()
    assert projection_manifest()["projection_id"] == PROJECTION_ID


def test_returned_manifest_objects_cannot_mutate_canonical_authority() -> None:
    original_bytes = PROJECTION_MANIFEST_CORE_CANONICAL_BYTES
    mutable_core = projection_manifest_core()
    mutable_core["field_specs"]["trajectory_code"]["source"] = "tampered"  # type: ignore[index]
    mutable_core["quantization"]["steps"] = 1  # type: ignore[index]
    mutable_full = projection_manifest()
    mutable_full["projection_id"] = "tampered"
    mutable_full["role_bindings"][CURRENT_ACTIVITY_ROLE] = ["tampered"]  # type: ignore[index]

    assert PROJECTION_MANIFEST_CORE_CANONICAL_BYTES == original_bytes
    assert projection_manifest_core()["field_specs"]["trajectory_code"]["source"] == (  # type: ignore[index]
        "signed_code(S.orientation_q)"
    )
    assert projection_manifest_core()["quantization"]["steps"] == 16  # type: ignore[index]
    assert projection_manifest()["projection_id"] == PROJECTION_ID


def test_projection_module_isolated_from_runtime_and_phase6_plus_implementation() -> None:
    tree = ast.parse(PROJECTION_PATH.read_text(encoding="utf-8"), filename=str(PROJECTION_PATH))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert {name.lstrip(".") for name in imports} <= {
        "__future__",
        "dataclasses",
        "hashlib",
        "json",
        "re",
        "types",
        "typing",
        "collections.abc",
        "brainvision.vhe",
    }

    module_global_names = {
        target.id
        for node in tree.body
        for target in (
            node.targets
            if isinstance(node, ast.Assign)
            else (node.target,)
            if isinstance(node, ast.AnnAssign)
            else ()
        )
        if isinstance(target, ast.Name)
    }
    assert not module_global_names & {
        "_ROLE_BINDINGS_DATA",
        "_ACCEPTANCE_RELEVANT_FIELD_SETS_DATA",
    }
    authority_assignments = {
        node.target.id: node.value
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
        and node.target.id
        in {"ROLE_BINDINGS", "ACCEPTANCE_RELEVANT_FIELD_SETS"}
    }
    assert set(authority_assignments) == {
        "ROLE_BINDINGS",
        "ACCEPTANCE_RELEVANT_FIELD_SETS",
    }
    for value in authority_assignments.values():
        assert isinstance(value, ast.Call)
        assert isinstance(value.func, ast.Name)
        assert value.func.id == "MappingProxyType"
        assert len(value.args) == 1
        assert isinstance(value.args[0], ast.Dict)

    declared_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not declared_names & {
        "CharacterModulation",
        "BrainvisionConfig",
        "BrainvisionSidecar",
        "BrainvisionRegistry",
        "ingest_visual_observation",
        "ProjectionAcceptance",
    }

    code = """
import json
import sys
import brainvision.projection
print(json.dumps(sorted(sys.modules)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    loaded = json.loads(completed.stdout)
    prohibited_prefixes = (
        "research.brainvision",
        "torment_service",
        "cognition",
        "memory",
        "kernel",
        "srg",
        "hivermind",
    )
    assert not any(name.startswith(prohibited_prefixes) for name in loaded)
