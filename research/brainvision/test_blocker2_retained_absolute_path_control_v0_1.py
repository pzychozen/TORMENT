from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest

import blocker2_retained_absolute_path_control_v0_1 as retained
import durable_evidence_schema_v0_3 as durable_schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter
import validate_windows_same_volume_no_replace_promotion_v0_1 as validation


WINDOWS_ONLY = pytest.mark.skipif(
    sys.platform != "win32",
    reason="retained result-directory profile is Windows-only",
)

AUTH_IDENTITY = "a" * 64
ASSESSMENT_IDENTITY = retained.RETAINED_RUN_ASSESSMENT_SHA256
IMPLEMENTATION_PREPARATION_AUTH_IDENTITY = (
    retained.IMPLEMENTATION_PREPARATION_AUTHORIZATION_SHA256
)
RUNTIME_CORRECTION_AUTH_IDENTITY = retained.RUNTIME_CORRECTION_AUTHORIZATION_SHA256
SYNTHETIC_HEAD = "0" * 40
MANIFEST_SHA = "c" * 64


class ConfirmingDurabilityAdapter(windows_adapter.WindowsDurabilityAdapter):
    def sync_directory_entry(
        self,
        directory_path: str,
        *,
        context: windows_adapter.DirectoryDurabilityContext | None = None,
    ) -> windows_adapter.DirectoryDurabilityResult:
        context = context or windows_adapter.DirectoryDurabilityContext()
        return windows_adapter.DirectoryDurabilityResult(
            status=durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            detail="synthetic directory durability confirmation",
            platform="synthetic",
            adapter_policy_identity=(
                durable_schema.directory_durability_policy_identity()
            ),
            target_role=context.target_role,
        )


def make_authorization(tmp_path: Path, **overrides) -> retained.RetainedAuthorization:
    values = {
        "mode": retained.RETAINED_MODE,
        "authorization_identity": AUTH_IDENTITY,
        "assessment_identity": ASSESSMENT_IDENTITY,
        "expected_branch": "main",
        "expected_head": SYNTHETIC_HEAD,
        "expected_origin_main": SYNTHETIC_HEAD,
        "result_directory": tmp_path / "retained-result",
        "fixture_root": tmp_path / "fixture-root",
        "selected_cases": retained.DEFAULT_RETAINED_CASES,
        "optional_cases": (),
        "authoritative": False,
        "allow_unrelated_outside_surfaces": False,
        "enforce_fixture_profile": False,
    }
    values.update(overrides)
    return retained.RetainedAuthorization(**values)


def source_identity_bundle():
    observations = {}
    expectations = []
    for index, relative_path in enumerate(retained.REQUIRED_SOURCE_IDENTITY_PATHS, 1):
        content = ("synthetic source %s\n" % relative_path).encode("ascii")
        observed = retained.synthetic_source_identity(
            relative_path,
            content=content,
            git_blob_oid=("%040x" % index),
        )
        observations[observed.relative_path] = observed
        expectations.append(
            retained.SourceIdentityExpectation(
                relative_path=observed.relative_path,
                checked_out_byte_sha256=observed.checked_out_byte_sha256,
                checked_out_byte_length=observed.checked_out_byte_length,
                git_blob_oid=observed.git_blob_oid,
            )
        )
    return tuple(expectations), observations


def stage_a_declaration_for_context(
    *,
    authority_root: Path,
    fixture_root: Path,
    result_parent: Path,
    source_expectations: tuple[retained.SourceIdentityExpectation, ...],
    selected_cases: tuple[str, ...] = retained.DEFAULT_RETAINED_CASES,
    optional_cases: tuple[str, ...] = (),
) -> dict[str, object]:
    case_set = retained.retained_case_set_identity(
        selected_cases=selected_cases,
        optional_cases=optional_cases,
    )
    case_declaration = retained.retained_case_set_declaration(
        selected_cases=selected_cases,
        optional_cases=optional_cases,
    )
    return retained.execution_authorization_identity_declaration(
        retained_run_assessment_identity=ASSESSMENT_IDENTITY,
        implementation_preparation_authorization_identity=(
            IMPLEMENTATION_PREPARATION_AUTH_IDENTITY
        ),
        runtime_correction_authorization_identity=(
            RUNTIME_CORRECTION_AUTH_IDENTITY
        ),
        expected_branch="main",
        expected_head=SYNTHETIC_HEAD,
        expected_origin_main=SYNTHETIC_HEAD,
        retained_orchestration_policy_sha256=retained.ABSOLUTE_POLICY_SHA256,
        native_helper_policy_sha256=retained.native_helper_policy_identity()[
            "policy_sha256"
        ],
        retained_schema_sha256=retained.retained_schema_identity()[
            "schema_sha256"
        ],
        case_set_sha256=case_set["case_set_sha256"],
        fixture_profile_sha256=retained.fixture_profile_identity()[
            "fixture_profile_sha256"
        ],
        authority_registry_root_identity=retained.path_identity_for_role(
            authority_root,
            role="authority_registry_root",
            must_exist=True,
        )["path_identity"],
        fixture_root_identity=retained.path_identity_for_role(
            fixture_root,
            role="fixture_root",
            must_exist=False,
        )["path_identity"],
        result_parent_identity=retained.path_identity_for_role(
            result_parent,
            role="result_parent",
            must_exist=True,
        )["path_identity"],
        host_identity=retained.host_profile_identity()["host_identity"],
        volume_identity=retained.volume_identity_for_path(result_parent)[
            "volume_identity"
        ],
        case_execution_order=case_declaration["native_execution_order"],
        selected_a6=retained.A6 in optional_cases,
        source_identities=source_expectations,
    )


def build_block_for_context(
    *,
    authority_root: Path,
    fixture_root: Path,
    result_parent: Path,
    source_expectations: tuple[retained.SourceIdentityExpectation, ...],
    selected_cases: tuple[str, ...] = retained.DEFAULT_RETAINED_CASES,
    optional_cases: tuple[str, ...] = (),
) -> retained.ExecutionAuthorizationIdentityBlock:
    return retained.build_execution_authorization_identity_block(
        assessment_identity=ASSESSMENT_IDENTITY,
        implementation_preparation_authorization_identity=(
            IMPLEMENTATION_PREPARATION_AUTH_IDENTITY
        ),
        runtime_correction_authorization_identity=(
            RUNTIME_CORRECTION_AUTH_IDENTITY
        ),
        expected_branch="main",
        expected_head=SYNTHETIC_HEAD,
        expected_origin_main=SYNTHETIC_HEAD,
        fixture_root=fixture_root,
        authority_registry_root=authority_root,
        source_identities=source_expectations,
        result_parent=result_parent,
        selected_cases=selected_cases,
        optional_cases=optional_cases,
    )


def make_authoritative_authorization(
    tmp_path: Path,
    **overrides,
) -> tuple[retained.RetainedAuthorization, dict[str, retained.SourceIdentity]]:
    authority_root = overrides.pop("authority_registry_root", tmp_path / "authority")
    authority_root.mkdir(exist_ok=True)
    requested_result_directory = overrides.pop("result_directory", None)
    result_parent = overrides.pop(
        "result_parent",
        (
            Path(requested_result_directory).parent
            if requested_result_directory is not None
            else tmp_path / "authoritative-results"
        ),
    )
    Path(result_parent).mkdir(parents=True, exist_ok=True)
    source_expectations, source_observations = source_identity_bundle()
    requested_authorization_identity = overrides.pop("authorization_identity", None)
    values = {
        "mode": retained.RETAINED_MODE,
        "assessment_identity": ASSESSMENT_IDENTITY,
        "expected_branch": "main",
        "expected_head": SYNTHETIC_HEAD,
        "expected_origin_main": SYNTHETIC_HEAD,
        "fixture_root": tmp_path / "authoritative-fixture",
        "selected_cases": retained.DEFAULT_RETAINED_CASES,
        "optional_cases": (),
        "authoritative": True,
        "allow_unrelated_outside_surfaces": False,
        "enforce_fixture_profile": False,
    }
    values.update(overrides)
    block = retained.build_execution_authorization_identity_block(
        assessment_identity=values["assessment_identity"],
        implementation_preparation_authorization_identity=(
            IMPLEMENTATION_PREPARATION_AUTH_IDENTITY
        ),
        runtime_correction_authorization_identity=RUNTIME_CORRECTION_AUTH_IDENTITY,
        expected_branch=values["expected_branch"],
        expected_head=values["expected_head"],
        expected_origin_main=values["expected_origin_main"],
        fixture_root=values["fixture_root"],
        authority_registry_root=authority_root,
        source_identities=source_expectations,
        result_parent=result_parent,
        result_directory=requested_result_directory,
        selected_cases=values["selected_cases"],
        optional_cases=values["optional_cases"],
        authorization_identity=requested_authorization_identity,
    )
    values["authorization_identity"] = block.execution_authorization_identity
    values["result_directory"] = (
        Path(requested_result_directory)
        if requested_result_directory is not None
        else retained.derive_result_directory(
            result_parent,
            block.execution_authorization_identity,
        )
    )
    values["execution_authorization"] = block
    return retained.RetainedAuthorization(**values), source_observations


def clean_repo_state() -> retained.RepositoryState:
    return retained.synthetic_clean_repository_state(
        branch="main",
        head=SYNTHETIC_HEAD,
        origin_main=SYNTHETIC_HEAD,
    )


def test_execution_authorization_declaration_is_stage_a_only(tmp_path):
    authority_root = tmp_path / "stage-a-authority"
    authority_root.mkdir()
    fixture_root = tmp_path / "stage-a-fixture"
    result_parent = tmp_path / "stage-a-results"
    result_parent.mkdir()
    source_expectations, _observations = source_identity_bundle()

    declaration = stage_a_declaration_for_context(
        authority_root=authority_root,
        fixture_root=fixture_root,
        result_parent=result_parent,
        source_expectations=source_expectations,
    )
    block = build_block_for_context(
        authority_root=authority_root,
        fixture_root=fixture_root,
        result_parent=result_parent,
        source_expectations=source_expectations,
    )
    result_dir = retained.derive_result_directory(
        result_parent,
        block.execution_authorization_identity,
    )

    assert declaration["schema"] == retained.RETAINED_EXECUTION_AUTHORIZATION_IDENTITY_SCHEMA
    assert "result_directory_identity" not in declaration
    assert "run_identity" not in declaration
    assert declaration["result_directory_derivation_rule"]["rule"] == (
        retained.RESULT_DIRECTORY_DERIVATION_RULE
    )
    assert block.execution_authorization_identity == (
        retained.execution_authorization_identity_from_declaration(declaration)
    )
    assert result_dir == result_parent.resolve() / block.execution_authorization_identity
    assert block.result_directory_identity == (
        retained.result_directory_identity(result_dir)["path_identity"]
    )

    run_declaration = retained.run_identity_declaration(
        execution_authorization_identity=block.execution_authorization_identity,
        expected_branch=block.expected_branch,
        expected_head=block.expected_head,
        expected_origin_main=block.expected_origin_main,
        case_set_sha256=block.case_set_sha256,
        case_execution_order=retained.retained_case_set_declaration()[
            "native_execution_order"
        ],
        fixture_root_identity=block.fixture_root_identity,
        result_parent_identity=block.result_parent_identity,
        result_directory_identity=block.result_directory_identity,
        authority_registry_root_identity=block.authority_registry_root_identity,
        selected_a6=block.selected_a6,
    )
    assert run_declaration["schema"] == retained.RETAINED_RUN_IDENTITY_SCHEMA
    assert run_declaration["execution_authorization_identity"] == (
        block.execution_authorization_identity
    )
    assert block.run_identity == retained.run_identity_from_declaration(
        run_declaration
    )


def test_stage_a_mutations_and_run_only_context_are_separated(tmp_path):
    authority_root = tmp_path / "authority"
    authority_root.mkdir()
    fixture_root = tmp_path / "fixture"
    result_parent = tmp_path / "results"
    result_parent.mkdir()
    source_expectations, _observations = source_identity_bundle()

    base_block = build_block_for_context(
        authority_root=authority_root,
        fixture_root=fixture_root,
        result_parent=result_parent,
        source_expectations=source_expectations,
    )
    repeat_block = build_block_for_context(
        authority_root=authority_root,
        fixture_root=fixture_root,
        result_parent=result_parent,
        source_expectations=source_expectations,
    )
    assert repeat_block.execution_authorization_identity == (
        base_block.execution_authorization_identity
    )
    assert repeat_block.run_identity == base_block.run_identity

    other_authority = tmp_path / "other-authority"
    other_authority.mkdir()
    authority_mutation = build_block_for_context(
        authority_root=other_authority,
        fixture_root=fixture_root,
        result_parent=result_parent,
        source_expectations=source_expectations,
    )
    assert authority_mutation.execution_authorization_identity != (
        base_block.execution_authorization_identity
    )

    fixture_mutation = build_block_for_context(
        authority_root=authority_root,
        fixture_root=tmp_path / "other-fixture",
        result_parent=result_parent,
        source_expectations=source_expectations,
    )
    assert fixture_mutation.execution_authorization_identity != (
        base_block.execution_authorization_identity
    )

    other_parent = tmp_path / "other-results"
    other_parent.mkdir()
    parent_mutation = build_block_for_context(
        authority_root=authority_root,
        fixture_root=fixture_root,
        result_parent=other_parent,
        source_expectations=source_expectations,
    )
    assert parent_mutation.execution_authorization_identity != (
        base_block.execution_authorization_identity
    )

    base_declaration = stage_a_declaration_for_context(
        authority_root=authority_root,
        fixture_root=fixture_root,
        result_parent=result_parent,
        source_expectations=source_expectations,
    )
    mutated_rule_declaration = dict(base_declaration)
    mutated_rule = dict(base_declaration["result_directory_derivation_rule"])
    mutated_rule["rule"] = "result_directory = operator_supplied_child"
    mutated_rule_declaration["result_directory_derivation_rule"] = mutated_rule
    assert retained.execution_authorization_identity_from_declaration(
        mutated_rule_declaration
    ) != retained.execution_authorization_identity_from_declaration(base_declaration)

    run_declaration = retained.run_identity_declaration(
        execution_authorization_identity=base_block.execution_authorization_identity,
        expected_branch=base_block.expected_branch,
        expected_head=base_block.expected_head,
        expected_origin_main=base_block.expected_origin_main,
        case_set_sha256=base_block.case_set_sha256,
        case_execution_order=retained.retained_case_set_declaration()[
            "native_execution_order"
        ],
        fixture_root_identity=base_block.fixture_root_identity,
        result_parent_identity=base_block.result_parent_identity,
        result_directory_identity=base_block.result_directory_identity,
        authority_registry_root_identity=base_block.authority_registry_root_identity,
        selected_a6=base_block.selected_a6,
    )
    changed_result_directory = dict(run_declaration)
    changed_result_directory["result_directory_identity"] = "0" * 64
    assert retained.run_identity_from_declaration(changed_result_directory) != (
        base_block.run_identity
    )
    changed_attempt = dict(run_declaration)
    changed_attempt["single_attempt_declaration"] = "second attempt"
    assert retained.run_identity_from_declaration(changed_attempt) != (
        base_block.run_identity
    )
    assert retained.execution_authorization_identity_from_declaration(
        base_declaration
    ) == base_block.execution_authorization_identity


def test_arbitrary_result_directory_is_rejected_after_stage_a(tmp_path):
    authority_root = tmp_path / "authority"
    authority_root.mkdir()
    result_parent = tmp_path / "results"
    result_parent.mkdir()
    source_expectations, _observations = source_identity_bundle()
    block = build_block_for_context(
        authority_root=authority_root,
        fixture_root=tmp_path / "fixture",
        result_parent=result_parent,
        source_expectations=source_expectations,
    )

    with pytest.raises(retained.RetainedValidationError, match=retained.IDENTITY_MISMATCH):
        retained.build_execution_authorization_identity_block(
            assessment_identity=ASSESSMENT_IDENTITY,
            implementation_preparation_authorization_identity=(
                IMPLEMENTATION_PREPARATION_AUTH_IDENTITY
            ),
            runtime_correction_authorization_identity=(
                RUNTIME_CORRECTION_AUTH_IDENTITY
            ),
            expected_branch="main",
            expected_head=SYNTHETIC_HEAD,
            expected_origin_main=SYNTHETIC_HEAD,
            fixture_root=tmp_path / "fixture",
            authority_registry_root=authority_root,
            source_identities=source_expectations,
            result_parent=result_parent,
            result_directory=result_parent / "operator-child",
            authorization_identity=block.execution_authorization_identity,
        )


def identity() -> validation.ObjectIdentity:
    return validation.ObjectIdentity(
        volume_serial_number=100,
        file_index_high=200,
        file_index_low=300,
    )


def positive(case_id: str) -> validation.ValidationCaseResult:
    object_identity = identity()
    return validation._case_result(
        case_id,
        validation.CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE,
        "synthetic retained positive case",
        None,
        policy_identity=retained.native_helper_policy_identity(),
        source_identity_before=object_identity,
        retained_handle_identity_after=object_identity,
        final_identity_after=object_identity,
        manifest_before_sha256=MANIFEST_SHA,
        manifest_after_sha256=MANIFEST_SHA,
    )


def collision(case_id: str) -> validation.ValidationCaseResult:
    return validation._case_result(
        case_id,
        validation.CONTROL_COLLISION_OBSERVED,
        "synthetic retained no-replace collision",
        None,
        native_error_code=validation.ERROR_ALREADY_EXISTS,
        native_error_name=validation.ERROR_NAMES[validation.ERROR_ALREADY_EXISTS],
        policy_identity=retained.native_helper_policy_identity(),
        source_exists_after_native_failure=True,
        final_exists_after_native_failure=True,
        manifest_before_sha256=MANIFEST_SHA,
        manifest_after_sha256=MANIFEST_SHA,
    )


def success_results(
    _fixture_root: Path,
    case_order: tuple[str, ...],
) -> tuple[validation.ValidationCaseResult, ...]:
    by_case = {
        retained.A1: positive(retained.A1_CASE_ID),
        retained.A2: collision(retained.A2_CASE_ID),
        retained.A3: collision(retained.A3_CASE_ID),
        retained.A5: positive(retained.A5_CASE_ID),
        retained.A6: validation._case_result(
            retained.A6_CASE_ID,
            validation.CONTROL_NATIVE_ERROR_INDETERMINATE,
            "synthetic optional native diagnostic",
            validation.NATIVE_RENAME_FAILED,
            native_error_code=validation.ERROR_INVALID_PARAMETER,
            native_error_name=validation.ERROR_NAMES[validation.ERROR_INVALID_PARAMETER],
            policy_identity=retained.native_helper_policy_identity(),
        ),
    }
    return tuple(by_case[case] for case in case_order)


def fake_gate_artifact() -> retained.ImmutableArtifactWriteResult:
    return retained.ImmutableArtifactWriteResult(
        path="C:\\synthetic\\gate_entry.canonical.json",
        byte_length=10,
        sha256="d" * 64,
        directory_sync={
            "status": durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            "detail": "synthetic",
            "target_role": durable_schema.ARTIFACT_PARENT_DIRECTORY,
        },
        reread_verified=True,
        hash_verified=True,
    )


def fake_global_artifact() -> retained.ImmutableArtifactWriteResult:
    return retained.ImmutableArtifactWriteResult(
        path="C:\\synthetic\\authority\\aaaaaaaa.global_authority_entry.canonical.json",
        byte_length=10,
        sha256="e" * 64,
        directory_sync={
            "status": durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            "detail": "synthetic",
            "target_role": durable_schema.ARTIFACT_PARENT_DIRECTORY,
        },
        reread_verified=True,
        hash_verified=True,
    )


def fake_run_result_artifact() -> retained.ImmutableArtifactWriteResult:
    return retained.ImmutableArtifactWriteResult(
        path="C:\\synthetic\\run_result.canonical.json",
        byte_length=10,
        sha256="f" * 64,
        directory_sync={
            "status": durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            "detail": "synthetic",
            "target_role": durable_schema.ARTIFACT_PARENT_DIRECTORY,
        },
        reread_verified=True,
        hash_verified=True,
    )


def test_retained_mode_is_explicit_and_not_an_absolute_mode(tmp_path):
    assert retained.require_retained_mode(retained.RETAINED_MODE) == retained.RETAINED_MODE
    with pytest.raises(retained.RetainedValidationError):
        retained.require_retained_mode(validation.ABSOLUTE_PATH_CONTROL_MODE)
    with pytest.raises(validation.ValidationError):
        validation.require_absolute_path_control_mode(retained.RETAINED_MODE)
    with pytest.raises(retained.RetainedValidationError):
        retained.preflight_retained_authorization(
            make_authorization(
                tmp_path,
                mode=validation.ABSOLUTE_PATH_CONTROL_MODE,
            ),
            repository_state=clean_repo_state(),
        )


def test_case_selection_binds_a1_a2_a3_a5_and_keeps_a6_optional():
    assert retained.evidence_chain_declaration()["records"] == [
        "GLOBAL_AUTHORITY_ENTRY",
        "LOCAL_GATE_ENTRY",
        "RUN_RESULT",
        "RETAINED_COMPLETION",
    ]
    assert len(retained.evidence_chain_identity()["evidence_chain_sha256"]) == 64
    assert (
        len(
            retained.authority_registry_profile_identity()[
                "authority_registry_profile_sha256"
            ]
        )
        == 64
    )
    declaration = retained.retained_case_set_declaration()
    assert declaration["completion_gating_cases"] == ["A1", "A2", "A3", "A5"]
    assert declaration["native_execution_order"] == ["A1", "A2", "A3", "A5"]

    with_a6 = retained.retained_case_set_declaration(optional_cases=(retained.A6,))
    assert with_a6["native_execution_order"] == ["A1", "A2", "A3", "A5", "A6"]
    assert with_a6["optional_non_gating_cases"] == ["A6"]

    for rejected in (retained.A4, retained.A7, retained.A8):
        with pytest.raises(retained.RetainedValidationError):
            retained.validate_case_selection(
                retained.COMPLETION_GATING_CASES + (rejected,)
            )
    with pytest.raises(retained.RetainedValidationError):
        retained.validate_case_selection(
            (retained.A1, retained.A2, retained.A3, retained.A5, retained.A6)
        )


def test_policy_identity_rejects_rootdirectory_relative_substitution():
    policy = retained.validate_policy_identity(
        retained.authorized_absolute_path_control_policy_identity()
    )
    assert policy["policy_sha256"] == retained.ABSOLUTE_POLICY_SHA256
    native = retained.validate_native_helper_policy_identity(
        retained.native_helper_policy_identity()
    )
    assert native["policy_sha256"] == (
        validation.absolute_path_control_policy_identity()["policy_sha256"]
    )

    with pytest.raises(retained.RetainedValidationError):
        retained.validate_policy_identity(
            {"policy_sha256": retained.ROOTDIRECTORY_RELATIVE_POLICY_SHA256}
        )
    if (
        validation.absolute_path_control_policy_identity()["policy_sha256"]
        != retained.ABSOLUTE_POLICY_SHA256
    ):
        with pytest.raises(retained.RetainedValidationError):
            retained.validate_policy_identity(
                validation.absolute_path_control_policy_identity()
            )
        with pytest.raises(retained.RetainedValidationError):
            retained.validate_native_helper_policy_identity(
                retained.authorized_absolute_path_control_policy_identity()
            )


def test_canonical_json_rejects_float_null_duplicates_and_noncanonical_bytes():
    assert retained.canonical_json_bytes({"b": 1, "a": 2}) == b'{"a":2,"b":1}'
    with pytest.raises(retained.RetainedValidationError):
        retained.canonical_json_bytes({"bad": 1.25})
    with pytest.raises(retained.RetainedValidationError):
        retained.canonical_json_bytes({"bad": None})
    with pytest.raises(retained.RetainedValidationError):
        retained.load_canonical_json_bytes(b'{"a":1,"a":2}')
    with pytest.raises(retained.RetainedValidationError):
        retained.load_canonical_json_bytes(b'{"b":1,"a":2}')


def test_case_outcomes_require_collision_preservation_and_error_183():
    outcomes = retained.evaluate_case_results(
        success_results(Path("C:\\"), retained.CASE_EXECUTION_ORDER),
        optional_cases=(retained.A6,),
    )
    assert outcomes["gating_satisfied"] is True
    assert outcomes["optional_outcomes"]["A6"]["gating"] is False

    bad_collision = replace(
        collision(retained.A2_CASE_ID),
        native_error_code=validation.ERROR_ACCESS_DENIED,
        native_error_name=validation.ERROR_NAMES[validation.ERROR_ACCESS_DENIED],
    )
    bad = (
        positive(retained.A1_CASE_ID),
        bad_collision,
        collision(retained.A3_CASE_ID),
        positive(retained.A5_CASE_ID),
    )
    assert retained.evaluate_case_results(bad)["gating_satisfied"] is False

    missing_preservation = replace(
        collision(retained.A3_CASE_ID),
        final_exists_after_native_failure=False,
    )
    bad = (
        positive(retained.A1_CASE_ID),
        collision(retained.A2_CASE_ID),
        missing_preservation,
        positive(retained.A5_CASE_ID),
    )
    assert retained.evaluate_case_results(bad)["gating_satisfied"] is False

    for missing_field in (
        {"source_exists_after_native_failure": None},
        {"final_exists_after_native_failure": None},
    ):
        missing_recorded_evidence = replace(
            collision(retained.A3_CASE_ID),
            **missing_field,
        )
        bad = (
            positive(retained.A1_CASE_ID),
            collision(retained.A2_CASE_ID),
            missing_recorded_evidence,
            positive(retained.A5_CASE_ID),
        )
        outcomes = retained.evaluate_case_results(bad)
        assert outcomes["gating_satisfied_by_case"][retained.A1] is True
        assert outcomes["gating_satisfied_by_case"][retained.A5] is True
        assert outcomes["gating_satisfied_by_case"][retained.A3] is False
        assert outcomes["gating_satisfied"] is False


def test_terminal_record_allows_false_complete_but_rejects_early_true(tmp_path):
    auth = make_authorization(tmp_path)
    outcomes = retained.evaluate_case_results(
        success_results(Path("C:\\"), retained.DEFAULT_RETAINED_CASES)
    )
    non_authoritative = retained.build_terminal_record(
        authorization=auth,
        terminal_state=retained.RUN_COMPLETE,
        gate_consumed=True,
        native_invocation_started=True,
        retained_execution=False,
        primary_failure="NONE",
        detail="synthetic complete",
        case_outcomes=outcomes,
        gate_artifact=fake_gate_artifact(),
        artifact_state=retained.pending_artifact_state(),
    )
    retained.validate_terminal_record(non_authoritative)

    authoritative_auth, _observations = make_authoritative_authorization(tmp_path)
    run_result = retained.build_terminal_record(
        authorization=authoritative_auth,
        terminal_state=retained.RUN_COMPLETE,
        gate_consumed=True,
        native_invocation_started=True,
        retained_execution=False,
        primary_failure="NONE",
        detail="synthetic run result",
        case_outcomes=outcomes,
        gate_artifact=fake_gate_artifact(),
        artifact_state=retained.completed_artifact_state(),
        global_authority_artifact=fake_global_artifact(),
    )
    retained.validate_terminal_record(run_result)

    early_true = dict(run_result)
    early_true["retained_execution"] = True
    with pytest.raises(retained.RetainedValidationError):
        retained.validate_terminal_record(early_true)

    completion = retained.build_retained_completion_record(
        authorization=authoritative_auth,
        run_result_record=run_result,
        run_result_artifact=fake_run_result_artifact(),
        gate_artifact=fake_gate_artifact(),
        global_authority_artifact=fake_global_artifact(),
    )
    retained.validate_retained_completion_record(completion)
    assert completion["retained_execution"] is True

    no_native = dict(completion)
    no_native["run_result_hash_verified"] = False
    with pytest.raises(retained.RetainedValidationError):
        retained.validate_retained_completion_record(no_native)

    no_native = dict(run_result)
    no_native["native_invocation_started"] = False
    with pytest.raises(retained.RetainedValidationError):
        retained.validate_terminal_record(no_native)

    failed_state = dict(run_result)
    failed_state["terminal_state"] = retained.RUN_FAILED
    retained.validate_terminal_record(failed_state)


@WINDOWS_ONLY
def test_preflight_rejects_repository_identity_mismatches(tmp_path):
    branch_mismatch = replace(clean_repo_state(), branch="topic")
    head_mismatch = replace(
        clean_repo_state(),
        head="1" * 40,
        origin_main="1" * 40,
    )
    origin_main_mismatch = replace(
        clean_repo_state(),
        head="2" * 40,
        origin_main="2" * 40,
    )

    cases = (
        (make_authorization(tmp_path), branch_mismatch),
        (
            make_authorization(
                tmp_path,
                expected_origin_main="1" * 40,
            ),
            head_mismatch,
        ),
        (
            make_authorization(
                tmp_path,
                expected_head="2" * 40,
            ),
            origin_main_mismatch,
        ),
    )
    for auth, state in cases:
        with pytest.raises(
            retained.RetainedValidationError,
            match=retained.REPOSITORY_STATE_INVALID,
        ):
            retained.preflight_retained_authorization(
                auth,
                repository_state=state,
            )


@WINDOWS_ONLY
def test_run_rejects_head_origin_divergence_before_gate(tmp_path):
    called = False

    def never_called(_fixture_root: Path, _case_order: tuple[str, ...]):
        nonlocal called
        called = True
        return ()

    auth = make_authorization(
        tmp_path,
        expected_head="1" * 40,
        expected_origin_main="2" * 40,
    )
    state = retained.synthetic_clean_repository_state(
        branch="main",
        head="1" * 40,
        origin_main="2" * 40,
    )

    result = retained.run_retained_single_run(
        auth,
        case_executor=never_called,
        repository_state=state,
        durability_adapter=ConfirmingDurabilityAdapter(),
    )

    assert result.terminal_state == retained.PREFLIGHT_REJECTED
    assert result.primary_failure == retained.REPOSITORY_STATE_INVALID
    assert result.gate_consumed is False
    assert result.native_invocation_started is False
    assert called is False
    assert not auth.result_directory.exists()
    assert not (auth.result_directory / retained.GATE_ENTRY_FILENAME).exists()


@WINDOWS_ONLY
def test_run_rejects_repository_index_lock_before_gate_and_preserves_lock(tmp_path):
    repo_root = tmp_path / "synthetic-repo"
    git_dir = repo_root / ".git"
    git_dir.mkdir(parents=True)
    lock_path = git_dir / "index.lock"
    lock_path.write_text("synthetic lock", encoding="ascii")
    called = False

    def never_called(_fixture_root: Path, _case_order: tuple[str, ...]):
        nonlocal called
        called = True
        return ()

    auth = make_authorization(
        tmp_path,
        result_directory=tmp_path / "retained-lock-result",
        fixture_root=tmp_path / "retained-lock-fixture",
    )
    state = retained.synthetic_clean_repository_state(
        repo_root=repo_root,
        branch="main",
        head=SYNTHETIC_HEAD,
        origin_main=SYNTHETIC_HEAD,
    )

    result = retained.run_retained_single_run(
        auth,
        case_executor=never_called,
        repository_state=state,
        durability_adapter=ConfirmingDurabilityAdapter(),
        repo_root=repo_root,
    )

    assert result.terminal_state == retained.PREFLIGHT_REJECTED
    assert result.primary_failure == retained.REPOSITORY_STATE_INVALID
    assert result.gate_consumed is False
    assert result.native_invocation_started is False
    assert called is False
    assert lock_path.exists()
    assert lock_path.read_text(encoding="ascii") == "synthetic lock"
    assert not auth.result_directory.exists()
    assert not (auth.result_directory / retained.GATE_ENTRY_FILENAME).exists()


@WINDOWS_ONLY
def test_preflight_rejects_dirty_authorized_surface_and_unrelated_by_default(tmp_path):
    auth = make_authorization(tmp_path)
    dirty_authorized = retained.RepositoryState(
        schema=retained.RETAINED_REPOSITORY_STATE_SCHEMA,
        repo_root="C:/synthetic/repo",
        branch="main",
        head=SYNTHETIC_HEAD,
        origin_main=SYNTHETIC_HEAD,
        status_lines=(" M research/brainvision/blocker2_retained_absolute_path_control_v0_1.py",),
        dirty_authorized_surfaces=(
            "research/brainvision/blocker2_retained_absolute_path_control_v0_1.py",
        ),
        dirty_unrelated_surfaces=(),
    )
    with pytest.raises(retained.RetainedValidationError):
        retained.preflight_retained_authorization(
            auth,
            repository_state=dirty_authorized,
        )

    dirty_unrelated = replace(
        clean_repo_state(),
        status_lines=("?? unrelated.txt",),
        dirty_unrelated_surfaces=("unrelated.txt",),
    )
    with pytest.raises(retained.RetainedValidationError):
        retained.preflight_retained_authorization(
            auth,
            repository_state=dirty_unrelated,
        )

    permitted = retained.preflight_retained_authorization(
        make_authorization(tmp_path, allow_unrelated_outside_surfaces=True),
        repository_state=dirty_unrelated,
    )
    assert permitted["repository_state"]["dirty_unrelated_surfaces"] == ["unrelated.txt"]


@WINDOWS_ONLY
def test_preflight_rejects_source_identity_mismatch(tmp_path):
    observed = retained.synthetic_source_identity(
        "research/brainvision/blocker2_retained_absolute_path_control_v0_1.py",
        content=b"observed",
    )
    expected = retained.SourceIdentityExpectation(
        relative_path=observed.relative_path,
        checked_out_byte_sha256="e" * 64,
        checked_out_byte_length=observed.checked_out_byte_length,
    )
    with pytest.raises(retained.RetainedValidationError):
        retained.preflight_retained_authorization(
            make_authorization(tmp_path),
            repository_state=clean_repo_state(),
            source_expectations=(expected,),
            source_observations={observed.relative_path: observed},
        )


@WINDOWS_ONLY
def test_run_refuses_authoritative_execution_and_missing_executor_before_gate(tmp_path):
    def never_called(_fixture_root: Path, _case_order: tuple[str, ...]):
        raise AssertionError("case executor must not run")

    authoritative = retained.run_retained_single_run(
        make_authorization(tmp_path, authoritative=True),
        case_executor=never_called,
        repository_state=clean_repo_state(),
        durability_adapter=ConfirmingDurabilityAdapter(),
    )
    assert authoritative.terminal_state == retained.PREFLIGHT_REJECTED
    assert authoritative.primary_failure == retained.AUTHORITATIVE_AUTHORIZATION_MISSING
    assert not Path(authoritative.result_directory).exists()

    no_executor = retained.run_retained_single_run(
        make_authorization(tmp_path, result_directory=tmp_path / "no-executor"),
        case_executor=None,
        repository_state=clean_repo_state(),
        durability_adapter=ConfirmingDurabilityAdapter(),
    )
    assert no_executor.terminal_state == retained.PREFLIGHT_REJECTED
    assert no_executor.primary_failure == retained.NATIVE_INVOCATION_NOT_CONFIGURED
    assert not Path(no_executor.result_directory).exists()


@WINDOWS_ONLY
def test_authoritative_identity_block_rejects_substituted_identities(tmp_path):
    auth, observations = make_authoritative_authorization(tmp_path)
    bad_schema = replace(
        auth.execution_authorization,
        retained_schema_sha256="0" * 64,
    )
    with pytest.raises(retained.RetainedValidationError):
        retained.preflight_retained_authorization(
            replace(auth, execution_authorization=bad_schema),
            repository_state=clean_repo_state(),
            source_observations=observations,
        )

    bad_correction = replace(
        auth.execution_authorization,
        runtime_correction_authorization_identity="1" * 64,
    )
    with pytest.raises(retained.RetainedValidationError):
        retained.preflight_retained_authorization(
            replace(auth, execution_authorization=bad_correction),
            repository_state=clean_repo_state(),
            source_observations=observations,
        )

    bad_placeholder = replace(
        auth.execution_authorization,
        source_identities=(
            replace(
                auth.execution_authorization.source_identities[0],
                git_blob_oid=retained.UNAVAILABLE_UNTIL_COMMIT,
            ),
        )
        + auth.execution_authorization.source_identities[1:],
    )
    with pytest.raises(retained.RetainedValidationError):
        retained.preflight_retained_authorization(
            replace(auth, execution_authorization=bad_placeholder),
            repository_state=clean_repo_state(),
            source_observations=observations,
        )


@WINDOWS_ONLY
def test_authoritative_synthetic_path_persists_chain_and_blocks_replay(tmp_path):
    calls = []

    def executor(fixture_root: Path, case_order: tuple[str, ...]):
        calls.append((fixture_root, case_order))
        return success_results(fixture_root, case_order)

    auth, observations = make_authoritative_authorization(tmp_path)
    result = retained.run_retained_single_run(
        auth,
        case_executor=executor,
        repository_state=clean_repo_state(),
        source_observations=observations,
        durability_adapter=ConfirmingDurabilityAdapter(),
    )

    assert result.terminal_state == retained.RUN_COMPLETE
    assert result.retained_execution is True
    assert result.authoritative is True
    assert result.global_authority_consumed is True
    assert result.gate_consumed is True
    assert result.native_invocation_started is True
    assert calls == [(auth.fixture_root, retained.DEFAULT_RETAINED_CASES)]

    authority_path = retained.global_authority_entry_path(auth)
    global_entry = retained.validate_global_authority_artifact(authority_path)
    assert global_entry["retained_execution"] is False
    assert global_entry["native_invocation_started"] is False

    result_dir = Path(result.result_directory)
    gate = retained.validate_gate_artifact(result_dir / retained.GATE_ENTRY_FILENAME)
    assert gate["global_authority_state"]["sha256"] == result.global_authority_artifact.sha256

    run_result = retained.validate_run_result_artifact(
        result_dir / retained.RUN_RESULT_FILENAME
    )
    assert run_result["record_type"] == "RUN_RESULT"
    assert run_result["retained_execution"] is False
    assert run_result["completion_receipt"] == "ABSENT"

    completion = retained.validate_retained_completion_artifact(
        result_dir / retained.RETAINED_COMPLETION_FILENAME
    )
    assert completion["record_type"] == "RETAINED_COMPLETION"
    assert completion["retained_execution"] is True
    assert completion["run_result_hash"] == result.run_result_artifact.sha256

    second = retained.run_retained_single_run(
        auth,
        case_executor=executor,
        repository_state=clean_repo_state(),
        source_observations=observations,
        durability_adapter=ConfirmingDurabilityAdapter(),
    )
    assert second.terminal_state == retained.PREFLIGHT_REJECTED
    assert second.primary_failure == retained.GLOBAL_AUTHORITY_ENTRY_EXISTS

    r1_global_entry_bytes = authority_path.read_bytes()
    r2_authority_root = tmp_path / "authority-r2"
    r2_authority_root.mkdir()
    r2_result_parent = tmp_path / "r2-results"
    r2_result_parent.mkdir()
    r2_legitimate_block = retained.build_execution_authorization_identity_block(
        assessment_identity=auth.assessment_identity,
        implementation_preparation_authorization_identity=(
            IMPLEMENTATION_PREPARATION_AUTH_IDENTITY
        ),
        runtime_correction_authorization_identity=RUNTIME_CORRECTION_AUTH_IDENTITY,
        expected_branch=auth.expected_branch,
        expected_head=auth.expected_head,
        expected_origin_main=auth.expected_origin_main,
        fixture_root=auth.fixture_root,
        authority_registry_root=r2_authority_root,
        source_identities=auth.execution_authorization.source_identities,
        result_parent=r2_result_parent,
        selected_cases=auth.selected_cases,
        optional_cases=auth.optional_cases,
    )
    r2_result_directory = retained.derive_result_directory(
        r2_result_parent,
        r2_legitimate_block.execution_authorization_identity,
    )
    assert r2_legitimate_block.execution_authorization_identity != (
        auth.authorization_identity
    )
    forged_r2_block = replace(
        r2_legitimate_block,
        execution_authorization_identity=auth.authorization_identity,
    )
    forged_r2_auth = replace(
        auth,
        result_directory=r2_result_directory,
        execution_authorization=forged_r2_block,
    )
    r2_calls = []

    def r2_executor(fixture_root: Path, case_order: tuple[str, ...]):
        r2_calls.append((fixture_root, case_order))
        return success_results(fixture_root, case_order)

    r2_replay = retained.run_retained_single_run(
        forged_r2_auth,
        case_executor=r2_executor,
        repository_state=clean_repo_state(),
        source_observations=observations,
        durability_adapter=ConfirmingDurabilityAdapter(),
    )
    r2_entry_path = retained.global_authority_entry_path(forged_r2_auth)
    assert r2_replay.terminal_state == retained.PREFLIGHT_REJECTED
    assert r2_replay.primary_failure == retained.GLOBAL_AUTHORITY_IDENTITY_MISMATCH
    assert r2_replay.global_authority_consumed is False
    assert r2_replay.gate_consumed is False
    assert r2_replay.native_invocation_started is False
    assert r2_calls == []
    assert not r2_entry_path.exists()
    assert not r2_result_directory.exists()
    assert not (r2_result_directory / retained.GATE_ENTRY_FILENAME).exists()
    assert not (r2_result_directory / retained.RUN_RESULT_FILENAME).exists()
    assert not (r2_result_directory / retained.RETAINED_COMPLETION_FILENAME).exists()
    assert authority_path.read_bytes() == r1_global_entry_bytes

    replay_parent = tmp_path / "replay-parent"
    replay_parent.mkdir()
    replay = retained.run_retained_single_run(
        replace(auth, result_directory=replay_parent / "result"),
        case_executor=executor,
        repository_state=clean_repo_state(),
        source_observations=observations,
        durability_adapter=ConfirmingDurabilityAdapter(),
    )
    assert replay.terminal_state == retained.PREFLIGHT_REJECTED
    assert replay.primary_failure == retained.CROSS_LOCATION_REPLAY_REJECTED

    independent_r2_auth, independent_r2_observations = make_authoritative_authorization(
        tmp_path,
        authority_registry_root=r2_authority_root,
        result_parent=r2_result_parent,
    )
    assert independent_r2_auth.authorization_identity == (
        r2_legitimate_block.execution_authorization_identity
    )
    assert independent_r2_auth.authorization_identity != auth.authorization_identity
    independent_r2 = retained.run_retained_single_run(
        independent_r2_auth,
        case_executor=r2_executor,
        repository_state=clean_repo_state(),
        source_observations=independent_r2_observations,
        durability_adapter=ConfirmingDurabilityAdapter(),
    )
    assert independent_r2.terminal_state == retained.RUN_COMPLETE
    assert independent_r2.retained_execution is True
    assert r2_calls == [
        (independent_r2_auth.fixture_root, retained.DEFAULT_RETAINED_CASES)
    ]


@WINDOWS_ONLY
def test_completion_fault_leaves_authority_consumed_and_result_incomplete(tmp_path):
    auth, observations = make_authoritative_authorization(tmp_path)
    result = retained.run_retained_single_run(
        auth,
        case_executor=success_results,
        repository_state=clean_repo_state(),
        source_observations=observations,
        durability_adapter=ConfirmingDurabilityAdapter(),
        fault_point=retained.FAULT_DURING_COMPLETION_REREAD,
    )

    assert result.terminal_state == retained.ARTIFACT_REVERIFY_FAILED
    assert result.global_authority_consumed is True
    assert result.gate_consumed is True
    assert result.run_result_artifact is not None
    assert result.retained_completion_artifact is None
    assert result.retained_execution is False
    assert result.primary_failure == retained.RETAINED_COMPLETION_REVERIFY_FAILURE


@WINDOWS_ONLY
def test_gate_failure_prevents_native_invocation(tmp_path):
    called = False

    def never_called(_fixture_root: Path, _case_order: tuple[str, ...]):
        nonlocal called
        called = True
        return ()

    result = retained.run_retained_single_run(
        make_authorization(tmp_path),
        case_executor=never_called,
        repository_state=clean_repo_state(),
        durability_adapter=ConfirmingDurabilityAdapter(),
        fault_point=retained.FAULT_DURING_GATE_FILE_WRITE,
    )
    assert result.terminal_state == retained.GATE_ENTRY_FAILED
    assert result.primary_failure == retained.GATE_ENTRY_WRITE_FAILURE
    assert result.gate_consumed is False
    assert result.native_invocation_started is False
    assert called is False


@WINDOWS_ONLY
def test_successful_synthetic_run_consumes_gate_and_persists_terminal(tmp_path):
    calls = []

    def executor(fixture_root: Path, case_order: tuple[str, ...]):
        calls.append((fixture_root, case_order))
        return success_results(fixture_root, case_order)

    auth = make_authorization(tmp_path)
    result = retained.run_retained_single_run(
        auth,
        case_executor=executor,
        repository_state=clean_repo_state(),
        durability_adapter=ConfirmingDurabilityAdapter(),
    )
    assert result.terminal_state == retained.RUN_COMPLETE
    assert result.retained_execution is False
    assert result.authoritative is False
    assert result.gate_consumed is True
    assert result.native_invocation_started is True
    assert calls == [(auth.fixture_root, retained.DEFAULT_RETAINED_CASES)]

    result_dir = Path(result.result_directory)
    retained.validate_gate_artifact(result_dir / retained.GATE_ENTRY_FILENAME)
    wrapper = retained.validate_terminal_artifact(
        result_dir / retained.TERMINAL_ARTIFACT_FILENAME
    )
    assert wrapper["terminal_record"]["retained_execution"] is False
    run_result = retained.validate_run_result_artifact(
        result_dir / retained.RUN_RESULT_FILENAME
    )
    assert run_result["record_type"] == "RUN_RESULT"
    assert run_result["retained_execution"] is False
    assert not (result_dir / retained.RETAINED_COMPLETION_FILENAME).exists()

    second = retained.run_retained_single_run(
        auth,
        case_executor=executor,
        repository_state=clean_repo_state(),
        durability_adapter=ConfirmingDurabilityAdapter(),
    )
    assert second.terminal_state == retained.PREFLIGHT_REJECTED
    assert second.primary_failure == retained.RESULT_DIRECTORY_NOT_ABSENT


@WINDOWS_ONLY
def test_after_gate_fault_consumes_authority_without_native_invocation(tmp_path):
    def never_called(_fixture_root: Path, _case_order: tuple[str, ...]):
        raise AssertionError("case executor must not run")

    result = retained.run_retained_single_run(
        make_authorization(tmp_path),
        case_executor=never_called,
        repository_state=clean_repo_state(),
        durability_adapter=ConfirmingDurabilityAdapter(),
        fault_point=retained.FAULT_AFTER_VERIFIED_GATE_BEFORE_NATIVE,
    )
    assert result.terminal_state == retained.RUN_FAILED
    assert result.gate_consumed is True
    assert result.native_invocation_started is False
    assert result.retained_execution is False
    assert result.terminal_artifact is not None


@WINDOWS_ONLY
def test_terminal_artifact_reverify_fault_is_fail_closed_after_native(tmp_path):
    result = retained.run_retained_single_run(
        make_authorization(tmp_path),
        case_executor=success_results,
        repository_state=clean_repo_state(),
        durability_adapter=ConfirmingDurabilityAdapter(),
        fault_point=retained.FAULT_DURING_TERMINAL_REREAD,
    )
    assert result.terminal_state == retained.ARTIFACT_REVERIFY_FAILED
    assert result.gate_consumed is True
    assert result.native_invocation_started is True
    assert result.primary_failure == retained.RUN_RESULT_REVERIFY_FAILURE
    assert result.retained_execution is False
