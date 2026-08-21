"""Preregistered deterministic Phase-6 horizon-acceptance administration.

This file is intentionally not executed until its JSON matrix and test logic
have been reviewed and the Phase-6 administration is explicitly authorized.
"""

from __future__ import annotations

import json
from pathlib import Path

from brainvision.fixtures import D0, DA, DB, descriptor_fixture_hashes
from brainvision.observation import (
    FirsthandVisualObservationV1,
    LowLevelVisualDescriptorV1,
    ObservationProvenanceType,
    derive_observation_id,
)
from brainvision.projection import (
    ACCEPTANCE_RELEVANT_FIELD_SETS,
    OPERATOR_ID,
    PROJECTION_ID,
    project_vhe_state,
    within_projection_quantum,
)
from brainvision.vhe import (
    Q,
    effective_fast_trace,
    evolve_vhe_state_as_of,
    fresh_vhe_state,
    mul_q,
    update_vhe_state,
)


MANIFEST_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "brainvision_phase6_horizon_acceptance_manifest.json"
)
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

_PHASE_2_FIXTURES = {"d0": D0, "dA": DA, "dB": DB}


def _descriptor(reference: str) -> LowLevelVisualDescriptorV1:
    raw = MANIFEST["descriptor_references"][reference]
    if isinstance(raw, str):
        assert raw == f"phase_2_fixture:{reference}"
        return _PHASE_2_FIXTURES[reference]
    assert raw["schema_id"] == MANIFEST["frozen_authorities"]["phase_2_descriptor_schema_id"]
    return LowLevelVisualDescriptorV1(
        mean_luminance_q=raw["mean_luminance_q"],
        mean_adjacent_luminance_difference_q=raw[
            "mean_adjacent_luminance_difference_q"
        ],
    )


def _reconstruct(events: list[dict[str, object]]):
    state = fresh_vhe_state()
    committed_active_time_ns = 0
    results = []
    for event in events:
        event_active_time_ns = event["active_time_ns"]
        assert type(event_active_time_ns) is int
        assert event_active_time_ns >= committed_active_time_ns
        result = update_vhe_state(
            state=state,
            descriptor=_descriptor(event["descriptor"]),
            semantic_event_class=event["semantic_event_class"],
            prior_committed_active_time_ns=committed_active_time_ns,
            elapsed_active_time_ns=event_active_time_ns - committed_active_time_ns,
        )
        state = result.state
        committed_active_time_ns = event_active_time_ns
        results.append(result)
    return state, committed_active_time_ns, tuple(results)


def _history(name: str):
    return _reconstruct(MANIFEST["histories"][name]["events"])


def _as_of_relation_raw_q(state, elapsed_active_time_ns: int) -> int:
    as_of_state = evolve_vhe_state_as_of(state, elapsed_active_time_ns)
    f_eff_1_q, f_eff_2_q = effective_fast_trace(as_of_state.fast_trace)
    context = as_of_state.persistent_context
    return min(
        max(
            mul_q(f_eff_1_q, context.luminance_q)
            + mul_q(f_eff_2_q, context.contrast_q),
            -Q,
        ),
        Q,
    )


def _assert_expected_fields(projection, expected: dict[str, int | str | None]) -> None:
    for field, expected_value in expected.items():
        assert getattr(projection, field) == expected_value


def _primary_assert(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(
            f"{MANIFEST['primary_retained_horizon']['failure_verdict']}: {detail}"
        )


def _primary_failure(detail: str) -> None:
    _primary_assert(False, detail)


def test_phase6_administration_guard_authorities_and_matrix_bindings() -> None:
    assert MANIFEST["administration_guards"] == ["authorities_and_matrix_bindings"]
    assert MANIFEST["schema_id"] == "brainvision.phase6.horizon_acceptance_manifest.v1"
    assert MANIFEST["phase"] == 6
    assert MANIFEST["frozen_authorities"]["operator_id"] == OPERATOR_ID
    assert MANIFEST["frozen_authorities"]["projection_id"] == PROJECTION_ID
    assert MANIFEST["frozen_authorities"]["phase_2_fixtures"] == descriptor_fixture_hashes()
    assert MANIFEST["product_horizon"] == {
        "active_visual_seconds": 300,
        "active_visual_ns": 300_000_000_000,
    }
    assert MANIFEST["primary_retained_horizon"]["relevant_field_sets"] == {
        "current_equality": list(
            ACCEPTANCE_RELEVANT_FIELD_SETS["retained_current_equality"]
        ),
        "retained_difference": list(
            ACCEPTANCE_RELEVANT_FIELD_SETS["retained_history_difference"]
        ),
    }
    assert MANIFEST["mandatory_order_qualification"]["relevant_field_sets"] == {
        "current_equality": list(ACCEPTANCE_RELEVANT_FIELD_SETS["order_current_equality"]),
        "history_difference": list(
            ACCEPTANCE_RELEVANT_FIELD_SETS["order_history_difference"]
        ),
    }
    assert MANIFEST["supporting_present_history_relation"]["relevant_field_set"] == list(
        ACCEPTANCE_RELEVANT_FIELD_SETS["present_history_relation"]
    )
    assert MANIFEST["mandatory_open_event_recurrence"]["relevant_field_sets"] == {
        "open_event": list(ACCEPTANCE_RELEVANT_FIELD_SETS["open_event"]),
        "recurrence": list(ACCEPTANCE_RELEVANT_FIELD_SETS["recurrence"]),
    }


def test_phase6_primary_retained_horizon_acceptance() -> None:
    specification = MANIFEST["primary_retained_horizon"]
    try:
        h0_name, h1_name = specification["history_refs"]
        h0_state, h0_final_time_ns, _ = _history(h0_name)
        h1_state, h1_final_time_ns, _ = _history(h1_name)
        _primary_assert(h0_final_time_ns == h1_final_time_ns, "H0/H1 final times differ")
        _primary_assert(
            h1_final_time_ns == MANIFEST["histories"][h1_name]["events"][-1]["active_time_ns"],
            "H1 final committed time mismatches the preregistered schedule",
        )
        _primary_assert(
            MANIFEST["histories"][h1_name]["events"][1]["active_time_ns"]
            == specification["retained_event_active_time_ns"],
            "retained-event onset mismatches the preregistered schedule",
        )
        _primary_assert(
            specification["pure_read_target_active_time_ns"] - h1_final_time_ns
            == specification["pure_read_elapsed_after_final_event_ns"],
            "pure-read elapsed time mismatches the preregistered target",
        )
        _primary_assert(
            specification["pure_read_target_active_time_ns"]
            - specification["retained_event_active_time_ns"]
            == MANIFEST["product_horizon"]["active_visual_ns"],
            "product-horizon timing is inconsistent",
        )

        h0_projection = project_vhe_state(
            h0_state,
            specification["pure_read_elapsed_after_final_event_ns"],
        )
        h1_projection = project_vhe_state(
            h1_state,
            specification["pure_read_elapsed_after_final_event_ns"],
        )
        for history_name, projection in ((h0_name, h0_projection), (h1_name, h1_projection)):
            for field, expected_value in specification["expected"][history_name].items():
                _primary_assert(
                    getattr(projection, field) == expected_value,
                    f"unexpected {history_name} {field}",
                )

        current_fields = tuple(specification["relevant_field_sets"]["current_equality"])
        retained_fields = tuple(specification["relevant_field_sets"]["retained_difference"])
        _primary_assert(
            within_projection_quantum(h0_projection, h1_projection, current_fields),
            "current activity is not equal",
        )
        _primary_assert(
            not within_projection_quantum(h0_projection, h1_projection, retained_fields),
            "retained history is not distinguishable",
        )
        retained_separation = abs(
            h1_projection.retained_history_code - h0_projection.retained_history_code
        )
        _primary_assert(
            retained_separation == specification["expected_retained_separation"],
            "retained-history separation differs from the preregistered value",
        )
        _primary_assert(
            retained_separation >= specification["minimum_retained_separation"],
            "retained-history separation is below the frozen minimum",
        )
    except AssertionError as error:
        prefix = f"{specification['failure_verdict']}:"
        if str(error).startswith(prefix):
            raise
        _primary_failure(f"primary administration assertion: {error}")
    except Exception as error:
        _primary_failure(f"primary administration error: {error!r}")


def test_phase6_mandatory_order_qualification() -> None:
    specification = MANIFEST["mandatory_order_qualification"]
    o1_name, o2_name = specification["history_refs"]
    o1_state, _, _ = _history(o1_name)
    o2_state, _, _ = _history(o2_name)
    o1_projection = project_vhe_state(
        o1_state,
        specification["pure_read_elapsed_after_final_event_ns"],
    )
    o2_projection = project_vhe_state(
        o2_state,
        specification["pure_read_elapsed_after_final_event_ns"],
    )
    _assert_expected_fields(o1_projection, specification["expected"][o1_name])
    _assert_expected_fields(o2_projection, specification["expected"][o2_name])
    assert within_projection_quantum(
        o1_projection,
        o2_projection,
        tuple(specification["relevant_field_sets"]["current_equality"]),
    )
    assert not within_projection_quantum(
        o1_projection,
        o2_projection,
        tuple(specification["relevant_field_sets"]["history_difference"]),
    )
    assert abs(o1_projection.trajectory_code - o2_projection.trajectory_code) == specification[
        "expected_trajectory_separation"
    ]


def test_phase6_supporting_present_history_relation_coverage() -> None:
    specification = MANIFEST["supporting_present_history_relation"]
    for case in specification["cases"].values():
        if "history_ref" in case:
            state, _, _ = _history(case["history_ref"])
        else:
            state, _, _ = _reconstruct(case["events"])
        elapsed_active_time_ns = case["pure_read_elapsed_after_final_event_ns"]
        assert _as_of_relation_raw_q(state, elapsed_active_time_ns) == case[
            "expected_raw_relation_q"
        ]
        projection = project_vhe_state(state, elapsed_active_time_ns)
        assert projection.present_history_relation_code == case["expected_code"]


def test_phase6_mandatory_open_event_and_recurrence_qualification() -> None:
    specification = MANIFEST["mandatory_open_event_recurrence"]
    state = fresh_vhe_state()
    initial_fast_trace = state.fast_trace
    initial_context = state.persistent_context
    _assert_expected_fields(
        project_vhe_state(state, 0),
        specification["expected_projection_sequence"]["fresh"],
    )
    committed_active_time_ns = 0
    for event in specification["events"]:
        event_active_time_ns = event["active_time_ns"]
        result = update_vhe_state(
            state=state,
            descriptor=_descriptor(event["descriptor"]),
            semantic_event_class=event["semantic_event_class"],
            prior_committed_active_time_ns=committed_active_time_ns,
            elapsed_active_time_ns=event_active_time_ns - committed_active_time_ns,
        )
        expected = specification["under_that_fixture"]
        assert result.write_gate_q == expected["write_gate_q"]
        if expected["fast_trace_unchanged"]:
            assert result.state.fast_trace == initial_fast_trace
        if expected["persistent_context_unchanged"]:
            assert result.state.persistent_context == initial_context
        state = result.state
        committed_active_time_ns = event_active_time_ns
        _assert_expected_fields(
            project_vhe_state(state, 0),
            specification["expected_projection_sequence"][event["label"]],
        )


def test_phase6_mandatory_neutral_reset_d0_qualification() -> None:
    specification = MANIFEST["mandatory_neutral_reset_d0"]
    state = fresh_vhe_state()
    initial_state = state
    _, _, results = _reconstruct(specification["events"])
    for result in results:
        assert result.write_gate_q == specification["expected"]["write_gate_q"]
        if specification["expected"]["state_unchanged"]:
            assert result.state == initial_state


def test_phase6_mandatory_world_event_id_invariance() -> None:
    specification = MANIFEST["mandatory_world_event_id_invariance"]
    stream_identity = specification["stream_identity"]
    source_sequence = specification["source_sequence"]
    observation_id = derive_observation_id(stream_identity, source_sequence)
    observations = tuple(
        FirsthandVisualObservationV1(
            provenance_type=ObservationProvenanceType.FIRSTHAND_VISUAL,
            stream_identity=stream_identity,
            source_sequence=source_sequence,
            observation_id=observation_id,
            descriptor=_descriptor(specification["descriptor"]),
            adapter_id=specification["adapter_id"],
            adapter_contract_id=specification["adapter_contract_id"],
            world_event_id=world_event_id,
        )
        for world_event_id in specification["world_event_ids"]
    )
    assert observations[0].to_canonical_json_bytes() != observations[1].to_canonical_json_bytes()
    left = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=observations[0].descriptor,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    )
    right = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=observations[1].descriptor,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    )
    assert left.state.fast_trace == right.state.fast_trace
    assert left.state.persistent_context == right.state.persistent_context
    assert left.write_gate_q == right.write_gate_q
    left_projection = project_vhe_state(left.state, 0)
    right_projection = project_vhe_state(right.state, 0)
    for field in specification["dynamical_projection_fields"]:
        assert getattr(left_projection, field) == getattr(right_projection, field)


def test_phase6_mandatory_semantic_dynamical_isolation() -> None:
    specification = MANIFEST["mandatory_semantic_dynamical_isolation"]
    dynamic_only = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=_descriptor(specification["descriptor"]),
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    )
    semantic = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=_descriptor(specification["descriptor"]),
        semantic_event_class=specification["semantic_event_class"],
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    )
    assert dynamic_only.state.fast_trace == semantic.state.fast_trace
    assert dynamic_only.state.persistent_context == semantic.state.persistent_context
    assert dynamic_only.write_gate_q == semantic.write_gate_q
    assert dynamic_only.state.semantic_register != semantic.state.semantic_register
    dynamic_projection = project_vhe_state(dynamic_only.state, 0)
    semantic_projection = project_vhe_state(semantic.state, 0)
    for field in specification["dynamical_projection_fields"]:
        assert getattr(dynamic_projection, field) == getattr(semantic_projection, field)


def test_phase6_mandatory_pure_read_determinism() -> None:
    specification = MANIFEST["mandatory_pure_read_determinism"]
    state, _, _ = _history(specification["history_ref"])
    original_state = state
    first = project_vhe_state(state, specification["pure_read_elapsed_after_final_event_ns"])
    second = project_vhe_state(state, specification["pure_read_elapsed_after_final_event_ns"])
    assert state == original_state
    assert first.to_canonical_json_bytes() == second.to_canonical_json_bytes()


def test_phase6_mandatory_deterministic_reconstruction() -> None:
    specification = MANIFEST["mandatory_deterministic_reconstruction"]
    for history_ref in specification["history_refs"]:
        first_state, first_time_ns, _ = _history(history_ref)
        second_state, second_time_ns, _ = _history(history_ref)
        assert first_time_ns == second_time_ns
        assert first_state == second_state
        elapsed_active_time_ns = specification["pure_read_elapsed_after_final_event_ns"][
            history_ref
        ]
        assert project_vhe_state(
            first_state,
            elapsed_active_time_ns,
        ).to_canonical_json_bytes() == project_vhe_state(
            second_state,
            elapsed_active_time_ns,
        ).to_canonical_json_bytes()
