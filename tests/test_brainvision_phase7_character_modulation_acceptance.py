"""Preregistered formal Phase-7 character-modulation acceptance instrument.

This file is intentionally not executed until the separately authorized first
formal Phase-7 administration.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import brainvision.character_modulation as modulation
from brainvision.fixtures import D0, DA, DB, descriptor_fixture_hashes
from brainvision.projection import (
    ACCEPTANCE_RELEVANT_FIELD_SETS,
    PROJECTION_ID,
    project_vhe_state,
    within_projection_quantum,
)
from brainvision.vhe import OPERATOR_ID, PersistentContext, fresh_vhe_state, update_vhe_state


MANIFEST_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "brainvision_phase7_character_modulation_acceptance_manifest.json"
)
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
_FIXTURES = {"d0": D0, "dA": DA, "dB": DB}


def _failure(detail: str) -> None:
    raise AssertionError(f"{MANIFEST['administration']['primary_failure_verdict']}: {detail}")


def _require(condition: bool, detail: str) -> None:
    if not condition:
        _failure(detail)


def _descriptor(reference: str):
    _require(
        MANIFEST["descriptor_references"][reference] == f"phase_2_fixture:{reference}",
        f"descriptor reference mismatch for {reference}",
    )
    return _FIXTURES[reference]


def _reconstruct_baseline(events: list[dict[str, object]]):
    state = fresh_vhe_state()
    committed_time_ns = 0
    results = []
    for event in events:
        event_time_ns = event["active_time_ns"]
        _require(type(event_time_ns) is int, "non-integer event time")
        _require(event_time_ns >= committed_time_ns, "non-monotonic event time")
        result = update_vhe_state(
            state=state,
            descriptor=_descriptor(event["descriptor"]),
            semantic_event_class=event["semantic_event_class"],
            prior_committed_active_time_ns=committed_time_ns,
            elapsed_active_time_ns=event_time_ns - committed_time_ns,
        )
        state = result.state
        committed_time_ns = event_time_ns
        results.append(result)
    return state, committed_time_ns, tuple(results)


def _reconstruct_modulated(events: list[dict[str, object]], theta: int):
    state = fresh_vhe_state()
    committed_time_ns = 0
    results = []
    for event in events:
        event_time_ns = event["active_time_ns"]
        _require(type(event_time_ns) is int, "non-integer event time")
        _require(event_time_ns >= committed_time_ns, "non-monotonic event time")
        result = modulation.update_vhe_state_with_character_modulation(
            state=state,
            descriptor=_descriptor(event["descriptor"]),
            semantic_event_class=event["semantic_event_class"],
            prior_committed_active_time_ns=committed_time_ns,
            elapsed_active_time_ns=event_time_ns - committed_time_ns,
            theta=theta,
        )
        state = result.state
        committed_time_ns = event_time_ns
        results.append(result)
    return state, committed_time_ns, tuple(results)


def _history(name: str, theta: int):
    history = MANIFEST["histories"][name]
    state, committed_time_ns, results = _reconstruct_modulated(history["events"], theta)
    return state, committed_time_ns, results, history["pure_read_elapsed_after_final_event_ns"]


def test_phase7_administration_guard_authorities_and_matrix_bindings() -> None:
    authorities = MANIFEST["frozen_authorities"]
    _require(
        MANIFEST["schema_id"] == "brainvision.phase7.character_modulation_acceptance_manifest.v1",
        "incorrect manifest schema identity",
    )
    _require(MANIFEST["phase"] == 7, "incorrect phase")
    _require(
        MANIFEST["phase7_specification"]["path"]
        == "docs/TORMENT_BRAINVISION_PHASE_7_CHARACTER_MODULATION_SPECIFICATION_v1.0.md",
        "incorrect Phase-7 specification path",
    )
    _require(
        MANIFEST["phase7_specification"]["implementation_commit"]
        == "4ae28a5930868dbe79b9d1c1ff0539fd9c2d712a",
        "incorrect implementation commit binding",
    )
    _require(authorities["base_operator_id"] == OPERATOR_ID, "base operator identity mismatch")
    _require(
        authorities["base_projection_id"] == PROJECTION_ID,
        "base projection identity mismatch",
    )
    _require(
        authorities["modulation_mapping_core_sha256"]
        == modulation.MODULATION_MAPPING_CORE_SHA256,
        "modulation mapping SHA mismatch",
    )
    _require(
        authorities["modulation_mapping_id"] == modulation.MODULATION_MAPPING_ID,
        "modulation mapping identity mismatch",
    )
    _require(
        authorities["modulation_profile_schema_id"] == modulation.MODULATION_PROFILE_SCHEMA_ID,
        "modulation profile schema mismatch",
    )
    _require(authorities["theta_v1"] == list(modulation.THETA_V1), "theta domain mismatch")
    _require(authorities["theta_0"] == modulation.THETA_0, "neutral theta mismatch")
    _require(
        authorities["product_horizon_ns"] == 300_000_000_000,
        "product horizon mismatch",
    )
    _require(
        authorities["phase_2_fixture_hashes"] == descriptor_fixture_hashes(),
        "Phase-2 fixture hash mismatch",
    )
    _require(
        MANIFEST["formal_relevant_projection_fields"]
        == {
            "primary_current_equality": list(
                ACCEPTANCE_RELEVANT_FIELD_SETS["retained_current_equality"]
            ),
            "primary_retained_history": list(
                ACCEPTANCE_RELEVANT_FIELD_SETS["retained_history_difference"]
            ),
            "order_current_equality": list(
                ACCEPTANCE_RELEVANT_FIELD_SETS["order_current_equality"]
            ),
            "order_trajectory": list(
                ACCEPTANCE_RELEVANT_FIELD_SETS["order_history_difference"]
            ),
        },
        "formal relevant projection field bindings mismatch",
    )
    for theta in authorities["theta_v1"]:
        _require(
            authorities["modulation_profile_ids"][str(theta).replace("1", "+1") if theta == 1 else str(theta)]
            == modulation.modulation_profile_id(theta),
            f"profile identity mismatch for theta {theta}",
        )
    projection = project_vhe_state(fresh_vhe_state(), 0)
    _require(
        list(projection.to_dict()) == authorities["projection_payload_fields"],
        "projection payload field set mismatch",
    )
    _require("theta" not in projection.to_dict(), "projection unexpectedly carries theta")
    _require(
        "modulation_profile_id" not in projection.to_dict(),
        "projection unexpectedly carries modulation profile",
    )


def test_phase7_structural_neutral_dispatch_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    guard = MANIFEST["structural_neutral_dispatch_guard"]
    sentinel = object()
    calls = []

    def baseline_sentinel(**kwargs):
        calls.append(kwargs)
        return sentinel

    monkeypatch.setattr(modulation, "update_vhe_state", baseline_sentinel)
    result = modulation.update_vhe_state_with_character_modulation(
        state=fresh_vhe_state(),
        descriptor=_descriptor(guard["descriptor"]),
        semantic_event_class=guard["semantic_event_class"],
        prior_committed_active_time_ns=guard["prior_committed_active_time_ns"],
        elapsed_active_time_ns=guard["active_time_ns"] - guard["prior_committed_active_time_ns"],
        theta=guard["theta"],
    )
    _require(result is sentinel, "neutral path did not return direct baseline result")
    _require(len(calls) == 1, "neutral path did not make exactly one baseline dispatch")


def test_phase7_neutral_is_bit_identical_to_baseline_on_preregistered_cases() -> None:
    for case in MANIFEST["neutral_baseline_cases"]:
        baseline_state = fresh_vhe_state()
        neutral_state = fresh_vhe_state()
        committed_time_ns = 0
        for event in case["events"]:
            event_time_ns = event["active_time_ns"]
            baseline = update_vhe_state(
                state=baseline_state,
                descriptor=_descriptor(event["descriptor"]),
                semantic_event_class=event["semantic_event_class"],
                prior_committed_active_time_ns=committed_time_ns,
                elapsed_active_time_ns=event_time_ns - committed_time_ns,
            )
            neutral = modulation.update_vhe_state_with_character_modulation(
                state=neutral_state,
                descriptor=_descriptor(event["descriptor"]),
                semantic_event_class=event["semantic_event_class"],
                prior_committed_active_time_ns=committed_time_ns,
                elapsed_active_time_ns=event_time_ns - committed_time_ns,
                theta=MANIFEST["frozen_authorities"]["theta_0"],
            )
            _require(neutral == baseline, f"neutral result mismatch in {case['case_id']}")
            _require(neutral.state == baseline.state, f"neutral state mismatch in {case['case_id']}")
            _require(
                neutral.state.fast_trace == baseline.state.fast_trace,
                f"neutral FastTrace mismatch in {case['case_id']}",
            )
            _require(
                neutral.state.persistent_context == baseline.state.persistent_context,
                f"neutral PersistentContext mismatch in {case['case_id']}",
            )
            _require(
                neutral.state.semantic_register == baseline.state.semantic_register,
                f"neutral SemanticRegister mismatch in {case['case_id']}",
            )
            _require(
                neutral.write_gate_q == baseline.write_gate_q,
                f"neutral write gate mismatch in {case['case_id']}",
            )
            _require(
                neutral.clamped_orientation_q == baseline.clamped_orientation_q,
                f"neutral orientation mismatch in {case['case_id']}",
            )
            _require(
                neutral.event_active_time_ns == baseline.event_active_time_ns,
                f"neutral event time mismatch in {case['case_id']}",
            )
            baseline_state = baseline.state
            neutral_state = neutral.state
            committed_time_ns = event_time_ns


def test_phase7_primary_same_experience_character_effect() -> None:
    specification = MANIFEST["primary_same_experience"]
    history_name = specification["history_ref"]
    expected_codes = []
    for theta in MANIFEST["frozen_authorities"]["theta_v1"]:
        state, committed_time_ns, _, read_elapsed_ns = _history(history_name, theta)
        history = MANIFEST["histories"][history_name]
        _require(
            history["pure_read_target_active_time_ns"] - committed_time_ns == read_elapsed_ns,
            "H1 pure-read timing mismatch",
        )
        _require(
            history["pure_read_target_active_time_ns"] - history["retained_event_active_time_ns"]
            == MANIFEST["frozen_authorities"]["product_horizon_ns"],
            "H1 product-horizon timing mismatch",
        )
        expected = specification["expected_by_theta"][
            str(theta).replace("1", "+1") if theta == 1 else str(theta)
        ]
        _require(
            state.persistent_context
            == PersistentContext(
                luminance_q=expected["persistent_context"][0],
                contrast_q=expected["persistent_context"][1],
                orientation_q=expected["persistent_context"][2],
            ),
            f"H1 persistent context mismatch for theta {theta}",
        )
        projection = project_vhe_state(state, read_elapsed_ns)
        _require(
            projection.current_activity_code == expected["current_activity_code"],
            f"H1 current activity mismatch for theta {theta}",
        )
        _require(
            projection.retained_history_code == expected["retained_history_code"],
            f"H1 retained history mismatch for theta {theta}",
        )
        expected_codes.append(projection.retained_history_code)

    _require(expected_codes == specification["expected_direction"], "H1 direction mismatch")
    neutral_code = expected_codes[1]
    _require(
        expected_codes[0] - neutral_code
        == specification["expected_delta_from_neutral"]["-1"],
        "negative theta H1 effect mismatch",
    )
    _require(
        expected_codes[2] - neutral_code
        == specification["expected_delta_from_neutral"]["+1"],
        "positive theta H1 effect mismatch",
    )
    _require(
        abs(expected_codes[0] - neutral_code) >= specification["minimum_absolute_effect_codes"],
        "negative theta H1 effect below minimum",
    )
    _require(
        abs(expected_codes[2] - neutral_code) >= specification["minimum_absolute_effect_codes"],
        "positive theta H1 effect below minimum",
    )
    _require(specification["acceptance_margin_codes"] == 0, "incorrect frozen effect margin")


def test_phase7_full_domain_product_horizon() -> None:
    specification = MANIFEST["domain_horizon"]
    h0_name, h1_name = specification["history_refs"]
    separations = []
    for theta in MANIFEST["frozen_authorities"]["theta_v1"]:
        theta_key = str(theta).replace("1", "+1") if theta == 1 else str(theta)
        h0_state, _, _, h0_elapsed_ns = _history(h0_name, theta)
        h1_state, _, _, h1_elapsed_ns = _history(h1_name, theta)
        h0_projection = project_vhe_state(h0_state, h0_elapsed_ns)
        h1_projection = project_vhe_state(h1_state, h1_elapsed_ns)
        _require(
            within_projection_quantum(
                h0_projection,
                h1_projection,
                tuple(MANIFEST["formal_relevant_projection_fields"]["primary_current_equality"]),
            ),
            f"H0/H1 current equality mismatch for theta {theta}",
        )
        _require(
            h0_projection.current_activity_code == specification["expected_current_activity_code"],
            f"H0 current activity mismatch for theta {theta}",
        )
        _require(
            h1_projection.current_activity_code == specification["expected_current_activity_code"],
            f"H1 current activity mismatch for theta {theta}",
        )
        _require(
            h0_projection.retained_history_code
            == specification["expected_retained_history_codes"][h0_name][theta_key],
            f"H0 retained history mismatch for theta {theta}",
        )
        _require(
            h1_projection.retained_history_code
            == specification["expected_retained_history_codes"][h1_name][theta_key],
            f"H1 retained history mismatch for theta {theta}",
        )
        separation = h1_projection.retained_history_code - h0_projection.retained_history_code
        _require(
            separation == specification["expected_separation_codes"][theta_key],
            f"H0/H1 separation mismatch for theta {theta}",
        )
        separations.append(separation)
    _require(
        min(separations) == specification["minimum_domain_separation_codes"],
        "domain minimum separation mismatch",
    )
    _require(
        min(separations) >= specification["minimum_product_horizon_separation_codes"],
        "domain minimum below product horizon requirement",
    )
    _require(specification["domain_wide_margin_codes"] == 4, "incorrect frozen domain margin")


def test_phase7_order_regression_across_theta() -> None:
    specification = MANIFEST["order_regression"]
    o1_name, o2_name = specification["history_refs"]
    for theta in MANIFEST["frozen_authorities"]["theta_v1"]:
        theta_key = str(theta).replace("1", "+1") if theta == 1 else str(theta)
        o1_state, _, _, o1_elapsed_ns = _history(o1_name, theta)
        o2_state, _, _, o2_elapsed_ns = _history(o2_name, theta)
        o1_expected = specification["expected_by_theta"][theta_key][o1_name]
        o2_expected = specification["expected_by_theta"][theta_key][o2_name]
        _require(
            o1_state.persistent_context.orientation_q == o1_expected["orientation_q"],
            f"O1 orientation mismatch for theta {theta}",
        )
        _require(
            o2_state.persistent_context.orientation_q == o2_expected["orientation_q"],
            f"O2 orientation mismatch for theta {theta}",
        )
        o1_projection = project_vhe_state(o1_state, o1_elapsed_ns)
        o2_projection = project_vhe_state(o2_state, o2_elapsed_ns)
        _require(
            within_projection_quantum(
                o1_projection,
                o2_projection,
                tuple(MANIFEST["formal_relevant_projection_fields"]["order_current_equality"]),
            ),
            f"order current activity mismatch for theta {theta}",
        )
        _require(
            o1_projection.trajectory_code == o1_expected["trajectory_code"],
            f"O1 trajectory mismatch for theta {theta}",
        )
        _require(
            o2_projection.trajectory_code == o2_expected["trajectory_code"],
            f"O2 trajectory mismatch for theta {theta}",
        )
        _require(o1_projection.trajectory_code > 0, f"O1 trajectory sign mismatch for theta {theta}")
        _require(o2_projection.trajectory_code < 0, f"O2 trajectory sign mismatch for theta {theta}")
        _require(
            o1_projection.trajectory_code != o2_projection.trajectory_code,
            f"order trajectory distinction mismatch for theta {theta}",
        )
        _require(
            not within_projection_quantum(
                o1_projection,
                o2_projection,
                tuple(MANIFEST["formal_relevant_projection_fields"]["order_trajectory"]),
            ),
            f"order relevant trajectory field mismatch for theta {theta}",
        )


def test_phase7_non_modulated_dynamics_and_semantic_isolation() -> None:
    specification = MANIFEST["non_modulated_dynamics_isolation"]
    state, committed_time_ns, _ = _reconstruct_baseline(specification["state_history"])
    update = specification["update"]
    for theta in specification["theta_values"]:
        baseline = update_vhe_state(
            state=state,
            descriptor=_descriptor(update["descriptor"]),
            semantic_event_class=update["semantic_event_class"],
            prior_committed_active_time_ns=committed_time_ns,
            elapsed_active_time_ns=update["active_time_ns"] - committed_time_ns,
        )
        modulated = modulation.update_vhe_state_with_character_modulation(
            state=state,
            descriptor=_descriptor(update["descriptor"]),
            semantic_event_class=update["semantic_event_class"],
            prior_committed_active_time_ns=committed_time_ns,
            elapsed_active_time_ns=update["active_time_ns"] - committed_time_ns,
            theta=theta,
        )
        _require(
            modulated.state.fast_trace == baseline.state.fast_trace,
            f"FastTrace mismatch for theta {theta}",
        )
        _require(
            modulated.state.semantic_register == baseline.state.semantic_register,
            f"SemanticRegister mismatch for theta {theta}",
        )
        _require(
            modulated.write_gate_q == baseline.write_gate_q,
            f"write gate mismatch for theta {theta}",
        )
        _require(
            modulated.clamped_orientation_q == baseline.clamped_orientation_q,
            f"clamped orientation mismatch for theta {theta}",
        )
        _require(
            modulated.event_active_time_ns == baseline.event_active_time_ns,
            f"event time mismatch for theta {theta}",
        )

    semantic_specification = MANIFEST["semantic_dynamical_isolation"]
    for theta in semantic_specification["theta_values"]:
        dynamic_only = modulation.update_vhe_state_with_character_modulation(
            state=fresh_vhe_state(),
            descriptor=_descriptor(semantic_specification["descriptor"]),
            semantic_event_class=None,
            prior_committed_active_time_ns=semantic_specification[
                "prior_committed_active_time_ns"
            ],
            elapsed_active_time_ns=semantic_specification["elapsed_active_time_ns"],
            theta=theta,
        )
        semantic = modulation.update_vhe_state_with_character_modulation(
            state=fresh_vhe_state(),
            descriptor=_descriptor(semantic_specification["descriptor"]),
            semantic_event_class=semantic_specification["semantic_event_class"],
            prior_committed_active_time_ns=semantic_specification[
                "prior_committed_active_time_ns"
            ],
            elapsed_active_time_ns=semantic_specification["elapsed_active_time_ns"],
            theta=theta,
        )
        _require(
            semantic.state.fast_trace == dynamic_only.state.fast_trace,
            f"semantic FastTrace isolation mismatch for theta {theta}",
        )
        _require(
            semantic.state.persistent_context == dynamic_only.state.persistent_context,
            f"semantic PersistentContext isolation mismatch for theta {theta}",
        )
        _require(
            semantic.write_gate_q == dynamic_only.write_gate_q,
            f"semantic write gate isolation mismatch for theta {theta}",
        )
        _require(
            semantic.clamped_orientation_q == dynamic_only.clamped_orientation_q,
            f"semantic orientation isolation mismatch for theta {theta}",
        )
        _require(
            semantic.state.semantic_register != dynamic_only.state.semantic_register,
            f"semantic register distinction missing for theta {theta}",
        )
