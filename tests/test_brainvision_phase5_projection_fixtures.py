"""Frozen Phase-5 retained, order, relation, and semantic fixtures."""

from __future__ import annotations

from brainvision.fixtures import D0, DA, DB
from brainvision.observation import LowLevelVisualDescriptorV1
from brainvision.projection import project_vhe_state
from brainvision.vhe import (
    FAST_HORIZON_NS,
    FastTrace,
    PersistentContext,
    VheState,
    effective_fast_trace,
    fresh_vhe_state,
    mul_q,
    update_vhe_state,
)


SECOND_NS = 1_000_000_000


def _apply_history(events):
    state = fresh_vhe_state()
    committed_time_ns = 0
    for event_time_ns, descriptor in events:
        result = update_vhe_state(
            state=state,
            descriptor=descriptor,
            semantic_event_class=None,
            prior_committed_active_time_ns=committed_time_ns,
            elapsed_active_time_ns=event_time_ns - committed_time_ns,
        )
        state = result.state
        committed_time_ns = event_time_ns
    return state, committed_time_ns


def _relation_raw_q(state) -> int:
    f_eff_1_q, f_eff_2_q = effective_fast_trace(state.fast_trace)
    return mul_q(f_eff_1_q, state.persistent_context.luminance_q) + mul_q(
        f_eff_2_q,
        state.persistent_context.contrast_q,
    )


def test_retained_history_fixture_projects_zero_vs_eight_with_equal_current() -> None:
    h0, h0_time = _apply_history(((0, D0), (SECOND_NS, D0), (2 * SECOND_NS, D0)))
    h1, h1_time = _apply_history(((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, D0)))
    assert h0_time == h1_time == 2 * SECOND_NS

    h0_projection = project_vhe_state(h0, 299 * SECOND_NS)
    h1_projection = project_vhe_state(h1, 299 * SECOND_NS)

    assert h0_projection.current_activity_code == h1_projection.current_activity_code == 0
    assert h0_projection.retained_history_code == 0
    assert h1_projection.retained_history_code == 8
    assert h1_projection.retained_history_code - h0_projection.retained_history_code == 8
    assert h1_projection.retained_history_code - h0_projection.retained_history_code >= 2


def test_order_fixture_projects_plus_five_vs_minus_five_through_trajectory_only() -> None:
    o1, _ = _apply_history(
        ((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, DB), (3 * SECOND_NS, D0))
    )
    o2, _ = _apply_history(
        ((0, D0), (SECOND_NS, DB), (2 * SECOND_NS, DA), (3 * SECOND_NS, D0))
    )

    o1_projection = project_vhe_state(o1, 0)
    o2_projection = project_vhe_state(o2, 0)

    assert o1_projection.current_activity_code == o2_projection.current_activity_code == 0
    assert o1_projection.retained_history_code == o2_projection.retained_history_code == 8
    assert o1_projection.present_history_relation_code == o2_projection.present_history_relation_code == 0
    assert o1_projection.trajectory_code == 5
    assert o2_projection.trajectory_code == -5
    assert o1_projection.trajectory_code - o2_projection.trajectory_code == 10


def test_present_history_relation_fixtures_are_lawful_and_exact() -> None:
    _, h1_time = _apply_history(((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, D0)))
    h1, _ = _apply_history(((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, D0)))
    no_current_as_of = project_vhe_state(h1, 299 * SECOND_NS)
    assert h1_time == 2 * SECOND_NS
    assert no_current_as_of.current_activity_code == 0
    assert no_current_as_of.present_history_relation_code == 0

    aligned_result = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    )
    assert _relation_raw_q(aligned_result.state) == 500_000
    assert project_vhe_state(aligned_result.state, 0).present_history_relation_code == 8

    negative_luminance = LowLevelVisualDescriptorV1(
        mean_luminance_q=250_000,
        mean_adjacent_luminance_difference_q=0,
    )
    half_positive_luminance = LowLevelVisualDescriptorV1(
        mean_luminance_q=625_000,
        mean_adjacent_luminance_difference_q=0,
    )
    after_negative = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=negative_luminance,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    ).state
    opposed_result = update_vhe_state(
        state=after_negative,
        descriptor=half_positive_luminance,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=SECOND_NS,
    )
    assert opposed_result.state.fast_trace == FastTrace(
        amplitude_1_q=500_000,
        amplitude_2_q=0,
        remaining_ns=FAST_HORIZON_NS,
    )
    assert opposed_result.state.persistent_context == PersistentContext(
        luminance_q=-375_000,
        contrast_q=0,
        orientation_q=0,
    )
    assert _relation_raw_q(opposed_result.state) == -187_500
    assert project_vhe_state(opposed_result.state, 0).present_history_relation_code == -3

    weak_contrast = LowLevelVisualDescriptorV1(
        mean_luminance_q=500_000,
        mean_adjacent_luminance_difference_q=2_000,
    )
    after_a = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    ).state
    orthogonal_result = update_vhe_state(
        state=after_a,
        descriptor=weak_contrast,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    )
    assert orthogonal_result.state.fast_trace == FastTrace(
        amplitude_1_q=0,
        amplitude_2_q=8_000,
        remaining_ns=FAST_HORIZON_NS,
    )
    assert orthogonal_result.state.persistent_context == PersistentContext(
        luminance_q=500_000,
        contrast_q=0,
        orientation_q=0,
    )
    assert _relation_raw_q(orthogonal_result.state) == 0
    assert project_vhe_state(orthogonal_result.state, 0).present_history_relation_code == 0


def test_current_and_retained_codes_bind_their_distinct_max_source_formulas() -> None:
    state = VheState(
        fast_trace=FastTrace(
            amplitude_1_q=500_000,
            amplitude_2_q=500_000,
            remaining_ns=FAST_HORIZON_NS,
        ),
        persistent_context=PersistentContext(
            luminance_q=100_000,
            contrast_q=200_000,
            orientation_q=-750_000,
        ),
        semantic_register=fresh_vhe_state().semantic_register,
    )

    projection = project_vhe_state(state, 0)
    assert projection.current_activity_code == 8
    assert projection.retained_history_code == 12


def test_d0_only_semantic_fixtures_change_only_r_and_semantic_projection_fields() -> None:
    fresh = fresh_vhe_state()
    fresh_projection = project_vhe_state(fresh, 0)
    assert fresh_projection.open_event_class is None
    assert fresh_projection.recurrence_code == 0

    first = update_vhe_state(
        state=fresh,
        descriptor=D0,
        semantic_event_class="detector:scene_change",
        prior_committed_active_time_ns=10,
        elapsed_active_time_ns=7,
    )
    assert first.write_gate_q == 0
    assert first.state.fast_trace == fresh.fast_trace
    assert first.state.persistent_context == fresh.persistent_context
    first_projection = project_vhe_state(first.state, 0)
    assert first_projection.open_event_class == "detector:scene_change"
    assert first_projection.recurrence_code == 1

    repeated = update_vhe_state(
        state=first.state,
        descriptor=D0,
        semantic_event_class="detector:scene_change",
        prior_committed_active_time_ns=17,
        elapsed_active_time_ns=23,
    )
    assert repeated.write_gate_q == 0
    assert repeated.state.fast_trace == first.state.fast_trace
    assert repeated.state.persistent_context == first.state.persistent_context
    repeated_projection = project_vhe_state(repeated.state, 0)
    assert repeated_projection.open_event_class == "detector:scene_change"
    assert repeated_projection.recurrence_code == 2

    new_token = update_vhe_state(
        state=repeated.state,
        descriptor=D0,
        semantic_event_class="detector:motion",
        prior_committed_active_time_ns=40,
        elapsed_active_time_ns=5,
    )
    assert new_token.write_gate_q == 0
    assert new_token.state.fast_trace == repeated.state.fast_trace
    assert new_token.state.persistent_context == repeated.state.persistent_context
    new_projection = project_vhe_state(new_token.state, 0)
    assert new_projection.open_event_class == "detector:motion"
    assert new_projection.recurrence_code == 1
