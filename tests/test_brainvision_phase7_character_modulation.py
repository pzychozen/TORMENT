"""Development conformance tests for frozen Phase-7 character modulation.

These tests are not a formal Phase-7 administration or result artifact.
"""

from __future__ import annotations

import ast
from dataclasses import fields
from hashlib import sha256
import json
from pathlib import Path

import pytest

import brainvision.character_modulation as modulation
from brainvision.fixtures import D0, DA, DB
from brainvision.observation import LowLevelVisualDescriptorV1
from brainvision.projection import PROJECTION_ID, project_vhe_state
from brainvision.vhe import (
    FAST_HORIZON_NS,
    OPERATOR_ID,
    FastTrace,
    PersistentContext,
    VheState,
    VheUpdateResult,
    VheValidationError,
    fresh_vhe_state,
    update_vhe_state,
)


SECOND_NS = 1_000_000_000
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPOSITORY_ROOT / "brainvision" / "character_modulation.py"

EXPECTED_PROFILE_IDS = {
    -1: "bvmodprof1_95cf73f228a5c02a16e13b90cf17aa46d31bbc312643f7dbf374d33816d9ad49",
    0: "bvmodprof1_9f65a350c2526bc63733e9267d7846ce4eace56a6c4ec3261bfc748a18287abc",
    1: "bvmodprof1_ceeb161b2dcb510601d85fc7b5a64eb023827bb044220b046b2c61b98be422f5",
}


def _update(
    state: VheState,
    *,
    descriptor= D0,
    semantic_event_class: str | None = None,
    prior_ns: int = 0,
    elapsed_ns: int = 0,
    theta: int = 0,
) -> VheUpdateResult:
    return modulation.update_vhe_state_with_character_modulation(
        state=state,
        descriptor=descriptor,
        semantic_event_class=semantic_event_class,
        prior_committed_active_time_ns=prior_ns,
        elapsed_active_time_ns=elapsed_ns,
        theta=theta,
    )


def _apply_history(events, *, theta: int) -> tuple[VheState, int]:
    state = fresh_vhe_state()
    committed_time_ns = 0
    for event_time_ns, descriptor in events:
        result = _update(
            state,
            descriptor=descriptor,
            prior_ns=committed_time_ns,
            elapsed_ns=event_time_ns - committed_time_ns,
            theta=theta,
        )
        state = result.state
        committed_time_ns = event_time_ns
    return state, committed_time_ns


def _exception_signature(callable_object) -> tuple[type[BaseException], str]:
    with pytest.raises(Exception) as captured:
        callable_object()
    return type(captured.value), str(captured.value)


def test_frozen_mapping_and_profile_identities_are_exact_and_canonical() -> None:
    assert modulation.MODULATION_SCHEMA_ID == "brainvision.character_modulation.v1"
    assert modulation.MODULATION_PROFILE_SCHEMA_ID == "brainvision.character_modulation.profile.v1"
    assert modulation.MODULATION_MAPPING_CORE_SHA256 == (
        "f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb"
    )
    assert modulation.MODULATION_MAPPING_ID == (
        "bvmodmap1_f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb"
    )
    assert modulation.BASE_OPERATOR_ID == OPERATOR_ID
    assert modulation.BASE_PROJECTION_ID == PROJECTION_ID

    core = modulation.modulation_mapping_core()
    assert modulation.MODULATION_MAPPING_CORE_CANONICAL_BYTES == json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    assert modulation.MODULATION_MAPPING_CORE_SHA256 == sha256(
        modulation.MODULATION_MAPPING_CORE_CANONICAL_BYTES
    ).hexdigest()
    assert modulation.MODULATION_MAPPING_ID == (
        modulation.MODULATION_MAPPING_ID_PREFIX + modulation.MODULATION_MAPPING_CORE_SHA256
    )
    assert "modulation_mapping_id" not in core

    for theta, expected_profile_id in EXPECTED_PROFILE_IDS.items():
        profile_core = modulation.modulation_profile_core(theta)
        assert profile_core == {
            "mapping_id": modulation.MODULATION_MAPPING_ID,
            "schema_id": modulation.MODULATION_PROFILE_SCHEMA_ID,
            "theta": theta,
        }
        canonical_bytes = modulation.modulation_profile_canonical_bytes(theta)
        assert canonical_bytes == json.dumps(
            profile_core,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        assert modulation.modulation_profile_id(theta) == expected_profile_id
        assert modulation.modulation_profile_id(theta) == (
            modulation.MODULATION_PROFILE_ID_PREFIX + sha256(canonical_bytes).hexdigest()
        )
        assert "operator_id" not in profile_core
        assert "projection_id" not in profile_core


def test_manifest_and_profile_views_cannot_mutate_identity_authority() -> None:
    original_bytes = modulation.MODULATION_MAPPING_CORE_CANONICAL_BYTES
    core_view = modulation.modulation_mapping_core()
    core_view["c_theta"]["expression"] = "tampered"  # type: ignore[index]
    full_view = modulation.modulation_mapping_manifest()
    full_view["modulation_mapping_id"] = "tampered"
    profile_view = modulation.modulation_profile_manifest(-1)
    profile_view["theta"] = 1

    assert modulation.MODULATION_MAPPING_CORE_CANONICAL_BYTES == original_bytes
    assert modulation.modulation_mapping_core()["c_theta"]["expression"] == (
        "C(theta)=500000+125000*theta"
    )
    assert modulation.modulation_mapping_manifest()["modulation_mapping_id"] == (
        modulation.MODULATION_MAPPING_ID
    )
    assert modulation.modulation_profile_manifest(-1)["theta"] == -1
    assert modulation.modulation_profile_id(-1) == EXPECTED_PROFILE_IDS[-1]


@pytest.mark.parametrize(
    ("theta", "expected_blend_q"),
    [(-1, 375_000), (0, 500_000), (1, 625_000)],
)
def test_theta_domain_and_effective_context_blend_are_exact(
    theta: int,
    expected_blend_q: int,
) -> None:
    assert modulation.validate_theta(theta) == theta
    assert modulation.effective_context_blend_q(theta) == expected_blend_q


@pytest.mark.parametrize(
    "theta",
    [True, False, -2, 2, -1.0, 0.0, 1.0, None, "-1", "0", "+1"],
)
def test_theta_validation_rejects_noncanonical_values_before_baseline_update(
    monkeypatch: pytest.MonkeyPatch,
    theta: object,
) -> None:
    def fail_if_called(**_kwargs):
        raise AssertionError("baseline update must not run for invalid theta")

    monkeypatch.setattr(modulation, "update_vhe_state", fail_if_called)
    with pytest.raises(modulation.CharacterModulationValidationError):
        modulation.update_vhe_state_with_character_modulation(
            state=fresh_vhe_state(),
            descriptor=D0,
            semantic_event_class=None,
            prior_committed_active_time_ns=0,
            elapsed_active_time_ns=0,
            theta=theta,  # type: ignore[arg-type]
        )


def test_neutral_structurally_dispatches_to_the_frozen_baseline_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    calls = []

    def baseline_sentinel(**kwargs):
        calls.append(kwargs)
        return sentinel

    monkeypatch.setattr(modulation, "update_vhe_state", baseline_sentinel)
    result = modulation.update_vhe_state_with_character_modulation(
        state=fresh_vhe_state(),
        descriptor=D0,
        semantic_event_class=None,
        prior_committed_active_time_ns=17,
        elapsed_active_time_ns=23,
        theta=0,
    )
    assert result is sentinel
    assert calls == [
        {
            "state": fresh_vhe_state(),
            "descriptor": D0,
            "semantic_event_class": None,
            "prior_committed_active_time_ns": 17,
            "elapsed_active_time_ns": 23,
        }
    ]


def test_neutral_results_are_complete_baseline_results_over_representative_history() -> None:
    events = (
        (0, D0, None),
        (SECOND_NS, DA, "detector:scene_change"),
        (2 * SECOND_NS, DB, "detector:motion"),
        (3 * SECOND_NS, D0, None),
    )
    baseline_state = fresh_vhe_state()
    neutral_state = fresh_vhe_state()
    committed_time_ns = 0
    for event_time_ns, descriptor, semantic_event_class in events:
        baseline = update_vhe_state(
            state=baseline_state,
            descriptor=descriptor,
            semantic_event_class=semantic_event_class,
            prior_committed_active_time_ns=committed_time_ns,
            elapsed_active_time_ns=event_time_ns - committed_time_ns,
        )
        neutral = _update(
            neutral_state,
            descriptor=descriptor,
            semantic_event_class=semantic_event_class,
            prior_ns=committed_time_ns,
            elapsed_ns=event_time_ns - committed_time_ns,
            theta=0,
        )
        assert neutral == baseline
        baseline_state = baseline.state
        neutral_state = neutral.state
        committed_time_ns = event_time_ns


def test_neutral_preserves_baseline_validation_behavior() -> None:
    invalid_cases = (
        {
            "state": object(),
            "descriptor": D0,
            "semantic_event_class": None,
            "prior_committed_active_time_ns": 0,
            "elapsed_active_time_ns": 0,
        },
        {
            "state": fresh_vhe_state(),
            "descriptor": object(),
            "semantic_event_class": None,
            "prior_committed_active_time_ns": 0,
            "elapsed_active_time_ns": 0,
        },
        {
            "state": fresh_vhe_state(),
            "descriptor": D0,
            "semantic_event_class": None,
            "prior_committed_active_time_ns": 0,
            "elapsed_active_time_ns": -1,
        },
        {
            "state": fresh_vhe_state(),
            "descriptor": D0,
            "semantic_event_class": "invalid semantic token",
            "prior_committed_active_time_ns": 0,
            "elapsed_active_time_ns": 0,
        },
    )
    for arguments in invalid_cases:
        baseline_error = _exception_signature(lambda: update_vhe_state(**arguments))
        neutral_error = _exception_signature(
            lambda: modulation.update_vhe_state_with_character_modulation(
                **arguments,
                theta=0,
            )
        )
        assert neutral_error == baseline_error
        assert neutral_error[0] is VheValidationError


def test_h1_primary_prediction_and_projection_direction_are_exact() -> None:
    events = ((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, D0))
    expected_contexts = {
        -1: PersistentContext(luminance_q=375_000, contrast_q=0, orientation_q=0),
        0: PersistentContext(luminance_q=500_000, contrast_q=0, orientation_q=0),
        1: PersistentContext(luminance_q=625_000, contrast_q=0, orientation_q=0),
    }
    projections = {}
    for theta in modulation.THETA_V1:
        state, committed_time_ns = _apply_history(events, theta=theta)
        assert committed_time_ns == 2 * SECOND_NS
        assert state.persistent_context == expected_contexts[theta]
        projection = project_vhe_state(state, 299 * SECOND_NS)
        assert projection.current_activity_code == 0
        projections[theta] = projection

    assert [projections[theta].retained_history_code for theta in modulation.THETA_V1] == [
        6,
        8,
        10,
    ]
    assert projections[-1].retained_history_code - projections[0].retained_history_code == -2
    assert projections[1].retained_history_code - projections[0].retained_history_code == 2


def test_h0_product_horizon_holds_across_the_complete_theta_domain() -> None:
    h0_events = ((0, D0), (SECOND_NS, D0), (2 * SECOND_NS, D0))
    h1_events = ((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, D0))
    separations = []
    for theta in modulation.THETA_V1:
        h0_state, _ = _apply_history(h0_events, theta=theta)
        h1_state, _ = _apply_history(h1_events, theta=theta)
        h0_projection = project_vhe_state(h0_state, 299 * SECOND_NS)
        h1_projection = project_vhe_state(h1_state, 299 * SECOND_NS)
        assert h0_projection.current_activity_code == 0
        assert h0_projection.retained_history_code == 0
        assert h1_projection.current_activity_code == 0
        separations.append(
            h1_projection.retained_history_code - h0_projection.retained_history_code
        )
    assert separations == [6, 8, 10]
    assert min(separations) == 6
    assert min(separations) >= 2


def test_order_regression_predictions_are_exact_across_theta_domain() -> None:
    o1_events = ((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, DB), (3 * SECOND_NS, D0))
    o2_events = ((0, D0), (SECOND_NS, DB), (2 * SECOND_NS, DA), (3 * SECOND_NS, D0))
    expected = {
        -1: (240_000, -240_000, 4, -4),
        0: (320_000, -320_000, 5, -5),
        1: (400_000, -400_000, 6, -6),
    }
    for theta in modulation.THETA_V1:
        o1_state, _ = _apply_history(o1_events, theta=theta)
        o2_state, _ = _apply_history(o2_events, theta=theta)
        expected_o1_orientation, expected_o2_orientation, expected_o1_code, expected_o2_code = (
            expected[theta]
        )
        assert o1_state.persistent_context.orientation_q == expected_o1_orientation
        assert o2_state.persistent_context.orientation_q == expected_o2_orientation
        o1_projection = project_vhe_state(o1_state, 0)
        o2_projection = project_vhe_state(o2_state, 0)
        assert o1_projection.current_activity_code == o2_projection.current_activity_code
        assert o1_projection.trajectory_code == expected_o1_code
        assert o2_projection.trajectory_code == expected_o2_code
        assert o1_projection.trajectory_code > 0
        assert o2_projection.trajectory_code < 0
        assert o1_projection.trajectory_code != o2_projection.trajectory_code


@pytest.mark.parametrize("theta", [-1, 1])
def test_non_neutral_preserves_all_baseline_owned_outputs(theta: int) -> None:
    initial_state = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class="detector:scene_change",
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    ).state
    baseline = update_vhe_state(
        state=initial_state,
        descriptor=DB,
        semantic_event_class="detector:motion",
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=SECOND_NS,
    )
    modulated = _update(
        initial_state,
        descriptor=DB,
        semantic_event_class="detector:motion",
        prior_ns=0,
        elapsed_ns=SECOND_NS,
        theta=theta,
    )
    assert modulated.state.fast_trace == baseline.state.fast_trace
    assert modulated.state.semantic_register == baseline.state.semantic_register
    assert modulated.write_gate_q == baseline.write_gate_q
    assert modulated.clamped_orientation_q == baseline.clamped_orientation_q
    assert modulated.event_active_time_ns == baseline.event_active_time_ns
    assert modulated.state.persistent_context != baseline.state.persistent_context


def test_zero_gain_d0_is_context_neutral_for_every_admitted_theta() -> None:
    fresh = fresh_vhe_state()
    for theta in modulation.THETA_V1:
        result = _update(fresh, descriptor=D0, theta=theta)
        assert result.write_gate_q == 0
        assert result.state.persistent_context == fresh.persistent_context


@pytest.mark.parametrize("theta", [-1, 0, 1])
def test_semantic_input_is_dynamically_isolated_for_every_theta(theta: int) -> None:
    dynamic_only = _update(
        fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class=None,
        prior_ns=101,
        elapsed_ns=23,
        theta=theta,
    )
    semantic = _update(
        fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class="detector:scene_change",
        prior_ns=101,
        elapsed_ns=23,
        theta=theta,
    )
    assert semantic.state.fast_trace == dynamic_only.state.fast_trace
    assert semantic.state.persistent_context == dynamic_only.state.persistent_context
    assert semantic.write_gate_q == dynamic_only.write_gate_q
    assert semantic.clamped_orientation_q == dynamic_only.clamped_orientation_q
    assert semantic.state.semantic_register != dynamic_only.state.semantic_register


def test_representative_s_edge_matrix_stays_inside_the_frozen_cube() -> None:
    negative_luminance = LowLevelVisualDescriptorV1(
        mean_luminance_q=250_000,
        mean_adjacent_luminance_difference_q=0,
    )
    zero_trace = FastTrace(amplitude_1_q=0, amplitude_2_q=0, remaining_ns=0)
    positive_orientation_trace = FastTrace(
        amplitude_1_q=1_000_000,
        amplitude_2_q=0,
        remaining_ns=FAST_HORIZON_NS,
    )
    negative_orientation_trace = FastTrace(
        amplitude_1_q=0,
        amplitude_2_q=1_000_000,
        remaining_ns=FAST_HORIZON_NS,
    )
    register = fresh_vhe_state().semantic_register
    contexts = (
        PersistentContext(luminance_q=-1_000_000, contrast_q=-1_000_000, orientation_q=-1_000_000),
        PersistentContext(luminance_q=0, contrast_q=0, orientation_q=0),
        PersistentContext(luminance_q=1_000_000, contrast_q=1_000_000, orientation_q=1_000_000),
    )
    cases = [
        (zero_trace, descriptor)
        for descriptor in (negative_luminance, D0, DA, DB)
    ] + [
        (positive_orientation_trace, DB),
        (negative_orientation_trace, DA),
    ]
    for context in contexts:
        for trace, descriptor in cases:
            state = VheState(
                fast_trace=trace,
                persistent_context=context,
                semantic_register=register,
            )
            for theta in modulation.THETA_V1:
                next_context = _update(state, descriptor=descriptor, theta=theta).state.persistent_context
                assert -1_000_000 <= next_context.luminance_q <= 1_000_000
                assert -1_000_000 <= next_context.contrast_q <= 1_000_000
                assert -1_000_000 <= next_context.orientation_q <= 1_000_000


def test_phase7_does_not_expand_recursive_state_or_result_shapes() -> None:
    assert [field.name for field in fields(VheState)] == [
        "fast_trace",
        "persistent_context",
        "semantic_register",
    ]
    assert [field.name for field in fields(VheUpdateResult)] == [
        "state",
        "write_gate_q",
        "clamped_orientation_q",
        "event_active_time_ns",
    ]
    assert "theta" not in VheState.__dataclass_fields__
    assert "theta" not in VheUpdateResult.__dataclass_fields__
    assert "modulation_profile_id" not in VheState.__dataclass_fields__
    assert "modulation_profile_id" not in VheUpdateResult.__dataclass_fields__


def test_phase5_projection_identity_and_schema_remain_unchanged_for_non_neutral_states() -> None:
    state, _ = _apply_history(((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, D0)), theta=1)
    projection = project_vhe_state(state, 299 * SECOND_NS)
    assert projection.schema_id == "brainvision.projection.v1"
    assert projection.projection_id == PROJECTION_ID
    assert projection.operator_id == OPERATOR_ID
    assert "theta" not in projection.to_dict()
    assert "modulation_profile_id" not in projection.to_dict()
    assert "modulation_mapping_id" not in projection.to_dict()


def test_phase7_module_imports_are_isolated_from_runtime_and_later_phases() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert {name.lstrip(".") for name in imports} <= {
        "__future__",
        "hashlib",
        "json",
        "typing",
        "brainvision.projection",
        "brainvision.vhe",
    }

    declared_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not declared_names & {
        "BrainvisionConfig",
        "BrainvisionSidecar",
        "BrainvisionRegistry",
        "ingest_visual_observation",
        "configure_character_modulation",
    }
