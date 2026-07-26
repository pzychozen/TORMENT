from __future__ import annotations

import sys

import pytest

import validate_windows_same_volume_no_replace_promotion_v0_1 as validation


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows native promotion primitive validation is explicit Windows-only",
)


def _require_supported_tmp_profile(tmp_path):
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
    return profile


def _confirmed_or_contract_rejected_indeterminate(result):
    if result.status == validation.PRIMITIVE_VALIDATION_CONFIRMED:
        return True
    if result.native_error_code == validation.ERROR_INVALID_PARAMETER:
        assert result.status == validation.INDETERMINATE
        assert "cause remains unresolved" in result.detail
        assert result.source_exists_after_native_failure is True
        assert result.source_identity_before is not None
        assert result.destination_parent_identity_before is not None
    elif result.native_error_code == validation.ERROR_NOT_SUPPORTED:
        assert result.status == validation.UNSUPPORTED
    else:
        raise AssertionError(result)
    assert result.native_error_name
    return False


def _absolute_control_confirmed_or_diagnostic(result):
    if result.status == validation.CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE:
        return True
    if result.status == validation.CONTROL_DESTINATION_REPLACED:
        assert result.failure_code == validation.CONTROL_DESTINATION_REPLACED
        return False
    if result.native_error_code is None and result.status in (
        validation.CONTROL_IDENTITY_MISMATCH,
        validation.CONTROL_CONTENT_MISMATCH,
        validation.CONTROL_NATIVE_ERROR_INDETERMINATE,
    ):
        assert result.failure_code
        return False
    if result.native_error_code == validation.ERROR_INVALID_PARAMETER:
        assert (
            result.status
            == validation.CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE
        )
        assert "indeterminate" in result.detail
        assert result.source_exists_after_native_failure is True
        assert result.source_identity_before is not None
        assert result.destination_parent_identity_before is not None
    elif result.native_error_code == validation.ERROR_NOT_SUPPORTED:
        assert result.status == validation.CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL
    elif result.native_error_code == validation.ERROR_ACCESS_DENIED:
        assert result.status == validation.CONTROL_ACCESS_REJECTED
    elif result.native_error_code in validation.COLLISION_ERROR_CODES:
        assert result.status == validation.CONTROL_COLLISION_OBSERVED
    else:
        raise AssertionError(result)
    assert result.native_error_name
    return False


def test_v1_full_chain_positive_and_v8_identity_continuity(tmp_path):
    _require_supported_tmp_profile(tmp_path)

    v1 = validation.validate_v1_full_chain_positive(tmp_path)
    if _confirmed_or_contract_rejected_indeterminate(v1):
        assert v1.source_identity_before == v1.retained_handle_identity_after
        assert v1.source_identity_before == v1.final_identity_after
        assert v1.manifest_before_sha256 == v1.manifest_after_sha256
        assert {
            probe.probe_id for probe in v1.durability_probes
        } >= {
            "D1_FINAL_PARENT",
            "D2_FORMER_SOURCE_PARENT",
            "D3_FINAL_THEN_FORMER_PARENT_ORDER",
            "D3_FORMER_THEN_FINAL_PARENT_ORDER",
            "D4_RETAINED_RENAMED_DIRECTORY_HANDLE_FLUSH",
        }

    v8 = validation.validate_v8_identity_continuity(tmp_path)
    if _confirmed_or_contract_rejected_indeterminate(v8):
        assert v8.source_identity_before == v8.retained_handle_identity_after
        assert v8.source_identity_before == v8.final_identity_after


def test_v2_v3_v4_no_replace_collision_cases(tmp_path):
    _require_supported_tmp_profile(tmp_path)

    v2 = validation.validate_v2_existing_destination_directory(tmp_path)
    if _confirmed_or_contract_rejected_indeterminate(v2):
        assert v2.native_error_code in validation.COLLISION_ERROR_CODES

    v3 = validation.validate_v3_existing_destination_file(tmp_path)
    if _confirmed_or_contract_rejected_indeterminate(v3):
        assert v3.native_error_code in validation.COLLISION_ERROR_CODES

    v4 = validation.validate_v4_coordinated_destination_claim(tmp_path)
    if _confirmed_or_contract_rejected_indeterminate(v4):
        assert v4.native_error_code in validation.COLLISION_ERROR_CODES


def test_v5_v6_reparse_fixtures_are_rejected_or_explicitly_skipped(tmp_path):
    _require_supported_tmp_profile(tmp_path)

    v5 = validation.validate_v5_source_reparse_rejected(tmp_path)
    assert v5.status in (validation.FIXTURE_INVALID, validation.SKIPPED)
    if v5.status == validation.SKIPPED:
        assert v5.skip_reason == "SYMLINK_UNAVAILABLE"

    v6 = validation.validate_v6_destination_parent_reparse_rejected(tmp_path)
    assert v6.status in (validation.FIXTURE_INVALID, validation.SKIPPED)
    if v6.status == validation.SKIPPED:
        assert v6.skip_reason == "SYMLINK_UNAVAILABLE"


def test_v7_v9_v10_v11_synthetic_and_skip_semantics(tmp_path):
    _require_supported_tmp_profile(tmp_path)

    v7 = validation.validate_v7_mutation_content_mismatch(tmp_path)
    assert v7.status == validation.CONTENT_MISMATCH
    assert v7.manifest_before_sha256 != v7.manifest_after_sha256

    for invalid_name_case in validation.validate_v9_invalid_names():
        assert invalid_name_case.status == validation.FIXTURE_INVALID
        assert invalid_name_case.failure_code == validation.NAME_INVALID

    v10 = validation.validate_v10_unsupported_profile(tmp_path)
    assert v10.status in (
        validation.FIXTURE_INVALID,
        validation.UNSUPPORTED,
        validation.INDETERMINATE,
        validation.SKIPPED,
    )

    v11 = validation.validate_v11_cross_volume_optional(tmp_path)
    assert v11.status == validation.SKIPPED
    assert v11.skip_reason == validation.SECOND_VOLUME_UNAVAILABLE


def test_v12_native_error_retention_and_matrix_record(tmp_path):
    _require_supported_tmp_profile(tmp_path)

    v12 = validation.validate_v12_native_error_retention(tmp_path)
    assert v12.status in (
        validation.PRIMITIVE_VALIDATION_CONFIRMED,
        validation.INDETERMINATE,
        validation.UNSUPPORTED,
    )
    assert v12.native_error_code in (
        *validation.COLLISION_ERROR_CODES,
        validation.ERROR_INVALID_PARAMETER,
        validation.ERROR_NOT_SUPPORTED,
    )
    assert v12.native_error_name

    matrix_root = tmp_path / "matrix"
    matrix_root.mkdir()
    _require_supported_tmp_profile(matrix_root)
    matrix = validation.run_validation_matrix(matrix_root)
    case_ids = {case.case_id for case in matrix}
    assert "V1_FULL_CHAIN_POSITIVE" in case_ids
    assert "V12_NATIVE_ERROR_RETENTION" in case_ids
    assert any(
        case.status == validation.SKIPPED
        and case.skip_reason == validation.SECOND_VOLUME_UNAVAILABLE
        for case in matrix
    )

    record = validation.build_validation_record(case_results=matrix)
    written = validation.write_temporary_validation_record(
        fixture_root=matrix_root,
        output_directory=matrix_root / "tmp_results",
        record=record,
    )
    assert written.exists()
    assert written.parent == matrix_root / "tmp_results"


def test_a1_a5_absolute_path_positive_and_identity(tmp_path):
    _require_supported_tmp_profile(tmp_path)

    a1 = validation.validate_a1_absolute_path_positive(tmp_path)
    if _absolute_control_confirmed_or_diagnostic(a1):
        assert a1.source_identity_before == a1.retained_handle_identity_after
        assert a1.source_identity_before == a1.final_identity_after
        assert a1.manifest_before_sha256 == a1.manifest_after_sha256
        assert a1.durability_probes == ()

    a5 = validation.validate_a5_absolute_path_identity_continuity(tmp_path)
    if _absolute_control_confirmed_or_diagnostic(a5):
        assert a5.source_identity_before == a5.retained_handle_identity_after
        assert a5.source_identity_before == a5.final_identity_after
        assert a5.durability_probes == ()


def test_a2_a3_a4_absolute_path_collisions(tmp_path):
    _require_supported_tmp_profile(tmp_path)

    a2 = validation.validate_a2_existing_destination_directory_absolute_path(tmp_path)
    _absolute_control_confirmed_or_diagnostic(a2)
    if a2.status == validation.CONTROL_COLLISION_OBSERVED:
        assert a2.native_error_code in validation.COLLISION_ERROR_CODES

    a3 = validation.validate_a3_existing_destination_file_absolute_path(tmp_path)
    _absolute_control_confirmed_or_diagnostic(a3)
    if a3.status == validation.CONTROL_COLLISION_OBSERVED:
        assert a3.native_error_code in validation.COLLISION_ERROR_CODES

    a4 = validation.validate_a4_coordinated_destination_claim_absolute_path(tmp_path)
    _absolute_control_confirmed_or_diagnostic(a4)
    if a4.status == validation.CONTROL_COLLISION_OBSERVED:
        assert a4.native_error_code in validation.COLLISION_ERROR_CODES


def test_a6_a7_a8_absolute_path_error_and_gating(tmp_path):
    _require_supported_tmp_profile(tmp_path)

    a6 = validation.validate_a6_absolute_path_native_error_characterization(tmp_path)
    assert a6.status in validation.CONTROL_STATUS_TAXONOMY
    if a6.status == validation.CONTROL_DESTINATION_REPLACED:
        assert a6.native_error_code is None
        assert a6.failure_code == validation.CONTROL_DESTINATION_REPLACED
    elif a6.native_error_code is None:
        assert a6.status in (
            validation.CONTROL_IDENTITY_MISMATCH,
            validation.CONTROL_CONTENT_MISMATCH,
            validation.CONTROL_NATIVE_ERROR_INDETERMINATE,
        )
        assert a6.failure_code
    else:
        assert a6.native_error_code in (
            *validation.COLLISION_ERROR_CODES,
            validation.ERROR_INVALID_PARAMETER,
            validation.ERROR_NOT_SUPPORTED,
            validation.ERROR_ACCESS_DENIED,
        )
        assert a6.native_error_name

    a7_results = validation.validate_a7_invalid_or_escaping_absolute_destinations(
        tmp_path,
    )
    assert all(
        result.status
        in (validation.CONTROL_FIXTURE_INVALID, validation.CONTROL_CONTAINMENT_REJECTED)
        for result in a7_results
    )
    assert all(result.native_error_code is None for result in a7_results)

    a8 = validation.validate_a8_same_volume_mismatch_rejected(tmp_path)
    assert a8.status == validation.CONTROL_SKIPPED_FIXTURE_UNAVAILABLE
    assert a8.skip_reason == validation.SECOND_VOLUME_UNAVAILABLE

    record = validation.build_absolute_path_control_record(
        case_results=(a6, *a7_results, a8),
    )
    assert record["control_mode"] == validation.ABSOLUTE_PATH_CONTROL_MODE
    assert record["retained_execution"] is False
