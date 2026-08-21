"""Frozen retained-history and order-fixture tests for Phase-4 A**."""

from __future__ import annotations

from brainvision.fixtures import D0, DA, DB
from brainvision.observation import LowLevelVisualDescriptorV1
from brainvision.vhe import (
    FAST_HORIZON_NS,
    ORDER_ORIENTATION_INTERNAL_MARGIN_Q,
    Q,
    RETAINED_HISTORY_INTERNAL_MARGIN_Q,
    PersistentContext,
    FastTrace,
    evolve_vhe_state_as_of,
    fresh_vhe_state,
    mul_q,
    normalize_descriptor,
    update_vhe_state,
)
from brainvision import vhe as vhe_module


SECOND_NS = 1_000_000_000


def _apply_history(events, *, updater=update_vhe_state):
    state = fresh_vhe_state()
    committed_time_ns = 0
    for event_time_ns, descriptor in events:
        result = updater(
            state=state,
            descriptor=descriptor,
            semantic_event_class=None,
            prior_committed_active_time_ns=committed_time_ns,
            elapsed_active_time_ns=event_time_ns - committed_time_ns,
        )
        state = result.state
        committed_time_ns = event_time_ns
    return state, committed_time_ns


def test_retained_history_fixture_at_exactly_300_active_seconds_after_da_onset() -> None:
    h0, h0_time = _apply_history(((0, D0), (SECOND_NS, D0), (2 * SECOND_NS, D0)))
    h1, h1_time = _apply_history(((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, D0)))
    assert h0_time == h1_time == 2 * SECOND_NS

    h0_read = evolve_vhe_state_as_of(h0, 299 * SECOND_NS)
    h1_read = evolve_vhe_state_as_of(h1, 299 * SECOND_NS)
    assert h0_read.persistent_context == PersistentContext(
        luminance_q=0,
        contrast_q=0,
        orientation_q=0,
    )
    assert h1_read.persistent_context == PersistentContext(
        luminance_q=500_000,
        contrast_q=0,
        orientation_q=0,
    )
    assert (
        h1_read.persistent_context.luminance_q - h0_read.persistent_context.luminance_q
    ) == RETAINED_HISTORY_INTERNAL_MARGIN_Q
    assert h0_read.fast_trace == h1_read.fast_trace == FastTrace(
        amplitude_1_q=0,
        amplitude_2_q=0,
        remaining_ns=0,
    )


def test_order_fixture_and_final_d0_are_exact() -> None:
    o1, _ = _apply_history(
        ((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, DB), (3 * SECOND_NS, D0))
    )
    o2, _ = _apply_history(
        ((0, D0), (SECOND_NS, DB), (2 * SECOND_NS, DA), (3 * SECOND_NS, D0))
    )
    assert o1.persistent_context == PersistentContext(
        luminance_q=500_000,
        contrast_q=500_000,
        orientation_q=320_000,
    )
    assert o2.persistent_context == PersistentContext(
        luminance_q=500_000,
        contrast_q=500_000,
        orientation_q=-320_000,
    )
    assert o1.persistent_context.orientation_q - o2.persistent_context.orientation_q == 640_000
    assert abs(o1.persistent_context.orientation_q - o2.persistent_context.orientation_q) >= (
        ORDER_ORIENTATION_INTERNAL_MARGIN_Q
    )
    assert o1.fast_trace == o2.fast_trace == FastTrace(
        amplitude_1_q=0,
        amplitude_2_q=0,
        remaining_ns=0,
    )


def test_c_zero_ablation_removes_the_order_witness_only_in_reference_evaluation() -> None:
    o1, _ = _apply_history(
        ((0, D0), (SECOND_NS, DA), (2 * SECOND_NS, DB), (3 * SECOND_NS, D0)),
        updater=vhe_module._update_vhe_state_with_c_zero_for_test,  # noqa: SLF001
    )
    o2, _ = _apply_history(
        ((0, D0), (SECOND_NS, DB), (2 * SECOND_NS, DA), (3 * SECOND_NS, D0)),
        updater=vhe_module._update_vhe_state_with_c_zero_for_test,  # noqa: SLF001
    )
    expected = PersistentContext(luminance_q=500_000, contrast_q=500_000, orientation_q=0)
    assert o1.persistent_context == o2.persistent_context == expected
    assert o1.fast_trace == o2.fast_trace == FastTrace(
        amplitude_1_q=0,
        amplitude_2_q=0,
        remaining_ns=0,
    )


def test_orientation_clamping_is_a_real_extreme_transition_saturation() -> None:
    negative_both = LowLevelVisualDescriptorV1(
        mean_luminance_q=250_000,
        mean_adjacent_luminance_difference_q=250_000,
    )
    positive_both = LowLevelVisualDescriptorV1(
        mean_luminance_q=750_000,
        mean_adjacent_luminance_difference_q=250_000,
    )
    assert normalize_descriptor(negative_both) == (-Q, Q)
    assert normalize_descriptor(positive_both) == (Q, Q)
    assert mul_q(-Q, Q) - mul_q(Q, Q) == -2 * Q
    state = fresh_vhe_state()
    state = update_vhe_state(
        state=state,
        descriptor=negative_both,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    ).state
    extreme = update_vhe_state(
        state=state,
        descriptor=positive_both,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    )
    assert extreme.clamped_orientation_q == -1_000_000
    assert -1_000_000 <= extreme.clamped_orientation_q <= 1_000_000
    assert FAST_HORIZON_NS == 5 * SECOND_NS
