from __future__ import annotations

from pathlib import Path
import sys

import pytest

import blocker2_retained_absolute_path_control_v0_1 as retained
import durable_evidence_schema_v0_3 as durable_schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter
import validate_windows_same_volume_no_replace_promotion_v0_1 as validation


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="BLOCKER-2 retained preparation integration is Windows-only",
)

AUTH_IDENTITY = "1" * 64
ASSESSMENT_IDENTITY = "2" * 64
SYNTHETIC_HEAD = "0" * 40
MANIFEST_SHA = "3" * 64


def make_authorization(tmp_path: Path) -> retained.RetainedAuthorization:
    return retained.RetainedAuthorization(
        mode=retained.RETAINED_MODE,
        authorization_identity=AUTH_IDENTITY,
        assessment_identity=ASSESSMENT_IDENTITY,
        expected_branch="main",
        expected_head=SYNTHETIC_HEAD,
        expected_origin_main=SYNTHETIC_HEAD,
        result_directory=tmp_path / "retained-integration-result",
        fixture_root=tmp_path / "retained-integration-fixture",
        selected_cases=retained.DEFAULT_RETAINED_CASES,
        optional_cases=(),
        authoritative=False,
        enforce_fixture_profile=False,
    )


def clean_repo_state() -> retained.RepositoryState:
    return retained.synthetic_clean_repository_state(
        branch="main",
        head=SYNTHETIC_HEAD,
        origin_main=SYNTHETIC_HEAD,
    )


def object_identity() -> validation.ObjectIdentity:
    return validation.ObjectIdentity(
        volume_serial_number=7,
        file_index_high=8,
        file_index_low=9,
    )


def positive(case_id: str) -> validation.ValidationCaseResult:
    identity = object_identity()
    return validation._case_result(
        case_id,
        validation.CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE,
        "synthetic integration positive",
        None,
        policy_identity=retained.native_helper_policy_identity(),
        source_identity_before=identity,
        retained_handle_identity_after=identity,
        final_identity_after=identity,
        manifest_before_sha256=MANIFEST_SHA,
        manifest_after_sha256=MANIFEST_SHA,
    )


def collision(case_id: str) -> validation.ValidationCaseResult:
    return validation._case_result(
        case_id,
        validation.CONTROL_COLLISION_OBSERVED,
        "synthetic integration no-replace collision",
        None,
        native_error_code=validation.ERROR_ALREADY_EXISTS,
        native_error_name=validation.ERROR_NAMES[validation.ERROR_ALREADY_EXISTS],
        policy_identity=retained.native_helper_policy_identity(),
        source_exists_after_native_failure=True,
        final_exists_after_native_failure=True,
        manifest_before_sha256=MANIFEST_SHA,
        manifest_after_sha256=MANIFEST_SHA,
    )


def selected_results(
    _fixture_root: Path,
    case_order: tuple[str, ...],
) -> tuple[validation.ValidationCaseResult, ...]:
    by_case = {
        retained.A1: positive(retained.A1_CASE_ID),
        retained.A2: collision(retained.A2_CASE_ID),
        retained.A3: collision(retained.A3_CASE_ID),
        retained.A5: positive(retained.A5_CASE_ID),
    }
    return tuple(by_case[case] for case in case_order)


def durability_adapter_or_skip(tmp_path: Path) -> windows_adapter.Win32DirectoryDurabilityAdapter:
    adapter = windows_adapter.Win32DirectoryDurabilityAdapter()
    probe = adapter.sync_directory_entry(
        str(tmp_path),
        context=windows_adapter.DirectoryDurabilityContext(
            target_role=durable_schema.ARTIFACT_PARENT_DIRECTORY
        ),
    )
    if probe.status != durable_schema.DIRECTORY_DURABILITY_CONFIRMED:
        pytest.skip("directory durability unavailable: %s" % probe.detail)
    return adapter


def require_supported_absolute_path_profile(tmp_path: Path) -> None:
    source = tmp_path / "_support_source"
    destination = tmp_path / "_support_dest"
    if not source.exists():
        validation.make_bounded_source_tree(tmp_path, "_support_source")
    destination.mkdir(exist_ok=True)
    profile = validation.admit_support_profile(
        fixture_root=tmp_path,
        source_directory=source,
        destination_parent=destination,
    )
    if not profile.supported:
        pytest.skip(profile.detail)


def test_real_a3_collision_evidence_satisfies_retained_gate(tmp_path):
    require_supported_absolute_path_profile(tmp_path)

    real_a3 = validation.validate_a3_existing_destination_file_absolute_path(tmp_path)
    if real_a3.status != validation.CONTROL_COLLISION_OBSERVED:
        pytest.skip("A3 collision was not observed: %s" % real_a3.status)

    assert real_a3.native_error_code == validation.ERROR_ALREADY_EXISTS
    assert real_a3.native_error_name == validation.ERROR_NAMES[
        validation.ERROR_ALREADY_EXISTS
    ]
    assert real_a3.source_exists_after_native_failure is True
    assert real_a3.final_exists_after_native_failure is True
    assert real_a3.manifest_before_sha256 is not None
    assert real_a3.manifest_after_sha256 is not None
    assert real_a3.manifest_before_sha256 == real_a3.manifest_after_sha256

    outcomes = retained.evaluate_case_results(
        (
            positive(retained.A1_CASE_ID),
            collision(retained.A2_CASE_ID),
            real_a3,
            positive(retained.A5_CASE_ID),
        )
    )
    a3_envelope = next(
        case
        for case in outcomes["case_results"]
        if case["case_short"] == retained.A3
    )

    assert a3_envelope["source_final_preservation_evidence"] == {
        "source_exists_after_native_failure": True,
        "final_exists_after_native_failure": True,
    }
    assert a3_envelope["content_continuity_evidence"][
        "manifest_before_sha256"
    ] == real_a3.manifest_before_sha256
    assert a3_envelope["content_continuity_evidence"][
        "manifest_after_sha256"
    ] == real_a3.manifest_after_sha256
    assert a3_envelope["retained_case_classification"]["satisfied"] is True
    assert outcomes["gating_satisfied_by_case"][retained.A3] is True
    assert outcomes["gating_satisfied"] is True


def test_retained_preparation_persists_gate_and_terminal_without_authority(tmp_path):
    adapter = durability_adapter_or_skip(tmp_path)
    auth = make_authorization(tmp_path)
    observed_calls = []

    def executor(fixture_root: Path, case_order: tuple[str, ...]):
        observed_calls.append((fixture_root, case_order))
        return selected_results(fixture_root, case_order)

    result = retained.run_retained_single_run(
        auth,
        case_executor=executor,
        repository_state=clean_repo_state(),
        durability_adapter=adapter,
    )

    assert result.terminal_state == retained.RUN_COMPLETE
    assert result.retained_execution is False
    assert result.authoritative is False
    assert result.gate_consumed is True
    assert result.native_invocation_started is True
    assert observed_calls == [(auth.fixture_root, retained.DEFAULT_RETAINED_CASES)]

    result_dir = Path(result.result_directory)
    gate = retained.validate_gate_artifact(result_dir / retained.GATE_ENTRY_FILENAME)
    assert gate["terminal_state"] == retained.GATE_ENTERED
    assert gate["native_invocation_started"] is False
    assert gate["retained_execution"] is False

    wrapper = retained.validate_terminal_artifact(
        result_dir / retained.TERMINAL_ARTIFACT_FILENAME
    )
    terminal = wrapper["terminal_record"]
    run_result = retained.validate_run_result_artifact(
        result_dir / retained.RUN_RESULT_FILENAME
    )
    assert run_result["record_type"] == "RUN_RESULT"
    assert terminal["terminal_state"] == retained.RUN_COMPLETE
    assert terminal["case_outcomes"]["gating_satisfied"] is True
    assert terminal["retained_execution"] is False
    assert not (result_dir / retained.RETAINED_COMPLETION_FILENAME).exists()
    assert result.gate_artifact is not None
    assert result.gate_artifact.reread_verified is True
    assert result.terminal_artifact is not None
    assert result.terminal_artifact.reread_verified is True
