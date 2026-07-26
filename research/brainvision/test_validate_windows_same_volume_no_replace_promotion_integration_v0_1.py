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
