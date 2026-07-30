from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

import blocker2_r4_ab_orchestrator_v0_1 as orchestrator
import blocker2_r4_authority_b_evidence_publisher_v0_1 as publisher
import blocker2_r4_ordered_directory_creation_helper_v0_1 as helper

from test_blocker2_r4_authority_b_evidence_publisher_v0_1 import (
    FakeDurabilityAdapter,
    FakeNativeAdapter,
    HEAD,
    helper_result_for,
    make_parent_dirs,
    path_model,
)


def operator_assertions() -> orchestrator.OperatorAssertions:
    return orchestrator.OperatorAssertions(
        window_open=True,
        authority_a_active=True,
        authority_b_active=True,
        authority_c_inactive=True,
        authority_d_inactive=True,
        authority_e_inactive=True,
        formal_hold_active=True,
        blocker_2_open=True,
        blocker_4_inactive=True,
    )


def pre_contact_helper_result_for(model: helper.PathModel) -> helper.HelperResult:
    derived_subreason = "operator_assertion_validation_failed"

    def body_mutator(evidence_body):
        evidence_body["operations"] = []
        evidence_body["aggregate"].update(
            {
                "contact_started": False,
                "opportunity_consumed": False,
                "mutation_succeeded_count": 0,
                "sequence_terminal": False,
                "full_ordered_sequence_succeeded": False,
                "classification": helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT,
                "classification_kind": helper.CLASSIFICATION_DERIVED_NON_TERMINAL,
                "committed_detail_label": helper.DETAIL_VALIDATION_FAILURE,
                "derived_subreason": {
                    "kind": "DERIVED_IMPLEMENTATION_SUBREASON",
                    "value": derived_subreason,
                },
            }
        )

    result = helper_result_for(model, body_mutator=body_mutator)
    object.__setattr__(
        result,
        "classification",
        helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT,
    )
    object.__setattr__(result, "classification_kind", helper.CLASSIFICATION_DERIVED_NON_TERMINAL)
    object.__setattr__(result, "terminal", False)
    object.__setattr__(result, "committed_detail_label", helper.DETAIL_VALIDATION_FAILURE)
    object.__setattr__(result, "derived_subreason", derived_subreason)
    object.__setattr__(result, "contact_started", False)
    object.__setattr__(result, "opportunity_consumed", False)
    object.__setattr__(result, "mutation_succeeded_count", 0)
    object.__setattr__(result, "sequence_terminal", False)
    return result


def test_successful_same_process_orchestration_stops_after_authority_b(tmp_path):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    native = FakeNativeAdapter(model)
    helper_result = helper_result_for(model)
    calls = []

    def execute_helper(**kwargs):
        calls.append(kwargs)
        return helper_result

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        native_adapter=native,
        durability_adapter=FakeDurabilityAdapter(),
        helper_executor=execute_helper,
    )

    assert result.accepted is True
    assert result.classification == publisher.AUTHORITY_B_ACCEPTED
    assert len(calls) == 1
    assert calls[0]["native_adapter"] is native
    assert calls[0]["path_model"] is model
    assert Path(model.evidence_record_path).exists()
    payload = result.as_dict()
    assert payload["authority_c_active"] is False
    assert payload["authority_d_active"] is False
    assert payload["authority_e_active"] is False
    assert "whole_record_sha256" in payload
    parsed = payload["authority_b_result"]["validation_result"]["parsed_record"]
    assert parsed["canonical_input_status"] == publisher.CANONICAL_INPUT_STATUS
    assert "canonical_input_identity" not in parsed
    assert "stored_record_sha256" not in parsed


def test_operator_assertions_are_required_before_authority_a_contact(tmp_path):
    model = path_model(tmp_path)
    calls = []
    native = FakeNativeAdapter(model)
    durability = FakeDurabilityAdapter()
    bad = orchestrator.OperatorAssertions(
        window_open=False,
        authority_a_active=True,
        authority_b_active=True,
        authority_c_inactive=True,
        authority_d_inactive=True,
        authority_e_inactive=True,
        formal_hold_active=True,
        blocker_2_open=True,
        blocker_4_inactive=True,
    )

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=bad,
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        native_adapter=native,
        durability_adapter=durability,
        helper_executor=lambda **kwargs: calls.append(kwargs),
    )

    assert result.accepted is False
    assert result.classification == (
        orchestrator.CORRECTED_PATH_CREATION_AB_ORCHESTRATION_PRE_CONTACT_ABORT
    )
    assert result.classification_kind == helper.CLASSIFICATION_DERIVED_NON_TERMINAL
    assert result.terminal is False
    assert result.sequence_terminal is False
    assert result.contact_started is False
    assert result.opportunity_consumed is False
    assert result.mutation_succeeded_count == 0
    assert result.failure_phase == orchestrator.FAILURE_PHASE_OPERATOR_ASSERTION_VALIDATION
    assert result.derived_subreason == "operator_assertion_false_window_open"
    assert result.authority_a_result is None
    assert result.authority_b_result is None
    assert calls == []
    assert native.opened == []
    assert native.absence_calls == []
    assert durability.calls == []
    assert not Path(model.evidence_record_path).exists()
    assert result.machine_verified_governance_assertions is False


def test_test_path_models_are_structurally_barred_from_governed_paths(tmp_path):
    calls = []
    native = FakeNativeAdapter(path_model(tmp_path))
    durability = FakeDurabilityAdapter()
    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=helper.GOVERNED_PATH_MODEL,
        allow_test_path_model=True,
        native_adapter=native,
        durability_adapter=durability,
        helper_executor=lambda **kwargs: calls.append(kwargs),
    )

    assert result.accepted is False
    assert result.classification == (
        orchestrator.CORRECTED_PATH_CREATION_AB_ORCHESTRATION_PRE_CONTACT_ABORT
    )
    assert result.classification_kind == helper.CLASSIFICATION_DERIVED_NON_TERMINAL
    assert result.terminal is False
    assert result.sequence_terminal is False
    assert result.contact_started is False
    assert result.opportunity_consumed is False
    assert result.mutation_succeeded_count == 0
    assert result.failure_phase == orchestrator.FAILURE_PHASE_TEST_PATH_MODEL_VALIDATION
    assert result.derived_subreason == "governed_path_forbidden_in_test_mode"
    assert result.authority_a_result is None
    assert result.authority_b_result is None
    assert calls == []
    assert native.opened == []
    assert native.absence_calls == []
    assert durability.calls == []


def test_helper_pre_contact_abort_is_propagated_without_authority_b_contact(tmp_path):
    model = path_model(tmp_path)
    native = FakeNativeAdapter(model)
    durability = FakeDurabilityAdapter()
    helper_result = pre_contact_helper_result_for(model)

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        native_adapter=native,
        durability_adapter=durability,
        helper_executor=lambda **kwargs: helper_result,
    )

    assert result.accepted is False
    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.classification_kind == helper_result.classification_kind
    assert result.terminal == helper_result.terminal
    assert result.sequence_terminal == helper_result.sequence_terminal
    assert result.contact_started == helper_result.contact_started
    assert result.opportunity_consumed == helper_result.opportunity_consumed
    assert result.mutation_succeeded_count == helper_result.mutation_succeeded_count
    assert result.committed_detail_label == helper_result.committed_detail_label
    assert result.derived_subreason == helper_result.derived_subreason
    assert result.authority_a_result["evidence_body"] == helper_result.evidence_body
    assert result.authority_a_result["body_identity"] == helper_result.body_identity
    assert result.authority_b_result is None
    assert native.opened == []
    assert native.absence_calls == []
    assert durability.calls == []
    assert not Path(model.evidence_record_path).exists()


def test_authority_a_partial_failure_is_returned_without_authority_b_contact(tmp_path):
    model = path_model(tmp_path)
    partial = helper_result_for(model)
    durability = FakeDurabilityAdapter()
    object.__setattr__(
        partial,
        "classification",
        helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE,
    )
    object.__setattr__(partial, "terminal", True)
    native = FakeNativeAdapter(model)

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        native_adapter=native,
        durability_adapter=durability,
        helper_executor=lambda **kwargs: partial,
    )

    assert result.accepted is False
    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.mutation_succeeded_count == partial.mutation_succeeded_count
    assert durability.calls == []
    assert not Path(model.evidence_record_path).exists()


def test_authority_a_unexpected_exception_maps_to_partial_terminal(tmp_path):
    model = path_model(tmp_path)

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        helper_executor=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    assert result.accepted is False
    assert result.classification == publisher.AUTHORITY_A_PARTIAL
    assert result.exception["exception_type"] == "RuntimeError"


def test_inconsistent_ready_helper_result_is_not_complete_record_unpublished(tmp_path):
    model = path_model(tmp_path)
    helper_result = helper_result_for(model)
    object.__setattr__(helper_result, "mutation_succeeded_count", 2)

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        native_adapter=FakeNativeAdapter(model),
        durability_adapter=FakeDurabilityAdapter(),
        helper_executor=lambda **kwargs: helper_result,
    )

    assert result.accepted is False
    assert result.classification == helper.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION
    assert result.failure_phase == orchestrator.FAILURE_PHASE_AUTHORITY_A_RESULT
    assert result.mutation_succeeded_count == 2
    assert result.authority_a_result["evidence_body"] == helper_result.evidence_body
    assert not Path(model.evidence_record_path).exists()


def test_canonicalization_failure_after_authority_a_success_is_complete_record_unpublished(
    tmp_path,
):
    model = path_model(tmp_path)
    helper_result = helper_result_for(model)
    durability = FakeDurabilityAdapter()

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        native_adapter=FakeNativeAdapter(model),
        durability_adapter=durability,
        helper_executor=lambda **kwargs: helper_result,
        source_identities={"bad": object()},
    )

    assert result.accepted is False
    assert result.classification == publisher.AUTHORITY_B_RECORD_UNPUBLISHED
    assert result.classification_kind == helper.CLASSIFICATION_COMMITTED_TERMINAL
    assert result.terminal is True
    assert result.sequence_terminal is True
    assert result.contact_started is True
    assert result.opportunity_consumed is True
    assert result.mutation_succeeded_count == 3
    assert result.failure_phase == orchestrator.FAILURE_PHASE_AUTHORITY_B_RECORD_CONSTRUCTION
    assert durability.calls == []
    assert not Path(model.evidence_record_path).exists()


def test_unexpected_failure_after_mutation_four_leaves_record_invalid(tmp_path):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    helper_result = helper_result_for(model)

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        native_adapter=FakeNativeAdapter(model),
        durability_adapter=FakeDurabilityAdapter(),
        helper_executor=lambda **kwargs: helper_result,
        read_bytes_function=lambda path: (_ for _ in ()).throw(OSError("read failed")),
    )

    assert result.accepted is False
    assert result.classification == publisher.AUTHORITY_B_RECORD_INVALID
    assert Path(model.evidence_record_path).exists()


def test_canonical_input_presence_after_publish_blocks_acceptance(tmp_path):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    native = FakeNativeAdapter(model)
    native.files.add(model.canonical_input_path)

    result = orchestrator.execute_authority_a_and_b(
        operator_assertions=operator_assertions(),
        accepted_invocation_head=HEAD,
        path_model=model,
        allow_test_path_model=True,
        native_adapter=native,
        durability_adapter=FakeDurabilityAdapter(),
        helper_executor=lambda **kwargs: helper_result_for(model),
    )

    assert result.accepted is False
    assert result.classification == publisher.AUTHORITY_B_RECORD_INVALID
    assert result.authority_b_result["validation_result"]["failure_code"] == (
        "CANONICAL_INPUT_PATH_PRESENT"
    )


def test_cli_fixed_path_binding_and_canonical_json_output():
    output = io.StringIO()
    seen = {}

    def fake_execute(**kwargs):
        seen.update(kwargs)
        return orchestrator.R4AuthorityABOrchestrationResult(
            classification=publisher.AUTHORITY_B_ACCEPTED,
            accepted=True,
            detail="accepted",
            accepted_invocation_head=kwargs["accepted_invocation_head"],
            operator_assertions=kwargs["operator_assertions"].as_dict(),
            whole_record_byte_count=12,
            whole_record_sha256="a" * 64,
        )

    exit_code = orchestrator.main(
        [
            "--accepted-invocation-head",
            HEAD,
            "--operator-assert-window-open",
            "--operator-assert-authority-a-active",
            "--operator-assert-authority-b-active",
            "--operator-assert-authority-c-inactive",
            "--operator-assert-authority-d-inactive",
            "--operator-assert-authority-e-inactive",
            "--operator-assert-formal-hold-active",
            "--operator-assert-blocker-2-open",
            "--operator-assert-blocker-4-inactive",
        ],
        execute=fake_execute,
        stdout=output,
    )
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["cli_fixed_path_binding"] is True
    assert payload["operator_assertions_do_not_activate_authority"] is True
    assert seen["path_model"] is helper.GOVERNED_PATH_MODEL
    assert seen["allow_test_path_model"] is False
    assert payload["operator_assertions"]["authority_c_inactive"] is True


def test_cli_returns_nonzero_for_nonaccepted_result():
    output = io.StringIO()

    def fake_execute(**kwargs):
        return orchestrator.R4AuthorityABOrchestrationResult(
            classification=publisher.AUTHORITY_B_RECORD_UNPUBLISHED,
            accepted=False,
            detail="not accepted",
            accepted_invocation_head=kwargs["accepted_invocation_head"],
        )

    exit_code = orchestrator.main(
        [
            "--accepted-invocation-head",
            HEAD,
            "--operator-assert-window-open",
            "--operator-assert-authority-a-active",
            "--operator-assert-authority-b-active",
            "--operator-assert-authority-c-inactive",
            "--operator-assert-authority-d-inactive",
            "--operator-assert-authority-e-inactive",
            "--operator-assert-formal-hold-active",
            "--operator-assert-blocker-2-open",
            "--operator-assert-blocker-4-inactive",
        ],
        execute=fake_execute,
        stdout=output,
    )

    assert exit_code == 1
    assert json.loads(output.getvalue())["classification"] == (
        publisher.AUTHORITY_B_RECORD_UNPUBLISHED
    )


def test_cli_requires_named_operator_assertions():
    with pytest.raises(SystemExit):
        orchestrator.main(["--accepted-invocation-head", HEAD], execute=lambda **kwargs: None)


def test_source_does_not_remap_helper_pre_contact_abort_to_committed_terminal():
    source = Path(orchestrator.__file__).read_text(encoding="utf-8")
    assert "classification == authority_a.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT" not in source
    assert "classification = publisher.AUTHORITY_B_RECORD_UNPUBLISHED" not in source


def test_source_terms_pin_orchestrator_boundary():
    source = Path(orchestrator.__file__).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "canonical_input_identity" not in source
    assert "canonical_input_publication" not in source
    assert "canonical_input_candidate" not in source
    for forbidden in (
        "mkdir",
        "Path.mkdir",
        "parents=True",
        "exist_ok=True",
        "rename",
        "os.replace",
        "replace(",
        ".replace",
        "os.remove",
        "unlink",
        "shutil",
        "NamedTemporaryFile",
    ):
        assert forbidden not in source
