from __future__ import annotations

import ctypes
import math
from pathlib import Path

import pytest

import blocker2_retained_absolute_path_control_v0_1 as retained
import validate_windows_same_volume_no_replace_promotion_v0_1 as validation


def test_validation_policy_identity_is_canonical_and_stable():
    declaration = validation.validation_policy_declaration()
    first = validation.validation_policy_identity()
    second = validation.validation_policy_identity()

    assert first == second
    assert first["policy_schema_identity"] == validation.VALIDATION_POLICY_SCHEMA
    assert first["policy_sha256"] == validation.sha256_hex(
        validation.canonical_json_bytes(declaration)
    )
    assert first["policy_sha256"].islower()
    assert len(first["policy_sha256"]) == 64
    assert (
        first["policy_sha256"]
        == "df91a9bcc3c5b37e938a086801dd2bca42f0290533a6cf2682055df475f663f3"
    )


def test_absolute_path_control_policy_identity_is_canonical_and_distinct():
    declaration = validation.absolute_path_control_policy_declaration()
    first = validation.absolute_path_control_policy_identity()
    second = validation.absolute_path_control_policy_identity()

    assert first == second
    assert (
        first["policy_schema_identity"]
        == validation.ABSOLUTE_PATH_CONTROL_POLICY_SCHEMA
    )
    assert first["policy_sha256"] == validation.sha256_hex(
        validation.canonical_json_bytes(declaration)
    )
    assert first["policy_sha256"] != validation.validation_policy_identity()[
        "policy_sha256"
    ]
    assert declaration["control_mode"] == validation.ABSOLUTE_PATH_CONTROL_MODE
    assert declaration["native_contract"]["root_directory"] is None
    assert (
        declaration["file_rename_info_buffer_policy"][
            "file_name_length_excludes_terminating_nul"
        ]
        is True
    )
    assert (
        declaration["prior_rootdirectory_relative_policy_identity"]
        == validation.validation_policy_identity()
    )


def test_canonical_json_sorts_keys_and_rejects_nan():
    assert validation.canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    with pytest.raises(ValueError):
        validation.canonical_json_bytes({"x": math.nan})


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "a/b",
        "a\\b",
        "C:drive",
        "stream:name",
        "*",
        "?",
        "\\\\server",
        "\\\\?\\C:\\x",
        "x\x00y",
    ],
)
def test_final_name_validation_rejects_malformed_names(name):
    result = validation.validate_final_name(name)
    assert result.accepted is False
    assert result.reason


def test_final_name_validation_accepts_simple_utf16_name():
    result = validation.validate_final_name("final_ae")
    assert result.accepted is True
    assert result.reason is None


def test_file_rename_info_buffer_layout_and_utf16_bytes():
    root_handle = 0x12345678
    buffer = validation.build_file_rename_info_buffer(
        root_directory_handle=root_handle,
        final_name="final",
    )
    offsets = buffer.offsets
    raw = buffer.as_bytes()

    assert offsets.replace_if_exists_or_flags == 0
    assert offsets.root_directory_width in (4, 8)
    assert offsets.file_name_length_width == 4
    assert offsets.file_name > offsets.file_name_length
    assert buffer.encoded_name == b"f\x00i\x00n\x00a\x00l\x00"
    assert buffer.size == offsets.file_name + len(buffer.encoded_name)
    assert raw[offsets.file_name :] == buffer.encoded_name
    assert (
        ctypes.c_uint32.from_buffer_copy(
            raw,
            offsets.replace_if_exists_or_flags,
        ).value
        == 0
    )
    assert (
        ctypes.c_uint32.from_buffer_copy(raw, offsets.file_name_length).value
        == len(buffer.encoded_name)
    )
    assert (
        ctypes.c_void_p.from_buffer_copy(raw, offsets.root_directory).value
        == root_handle
    )


def test_absolute_path_file_rename_info_buffer_uses_null_root_and_utf16_path():
    absolute_destination = "C:\\TORMENT\\codex_pytest_tmp_abs_control\\dest\\final"
    buffer = validation.build_absolute_path_file_rename_info_buffer(
        absolute_destination_path=absolute_destination,
    )
    offsets = buffer.offsets
    raw = buffer.as_bytes()
    encoded = absolute_destination.encode("utf-16-le")

    assert buffer.final_name == absolute_destination
    assert buffer.encoded_name == encoded
    assert buffer.size == offsets.file_name + len(encoded) + 2
    assert raw[offsets.file_name : offsets.file_name + len(encoded)] == encoded
    assert raw[offsets.file_name + len(encoded) :] == b"\x00\x00"
    assert (
        ctypes.c_uint32.from_buffer_copy(
            raw,
            offsets.replace_if_exists_or_flags,
        ).value
        == 0
    )
    assert ctypes.c_void_p.from_buffer_copy(raw, offsets.root_directory).value is None
    assert (
        ctypes.c_uint32.from_buffer_copy(raw, offsets.file_name_length).value
        == len(encoded)
    )


def test_file_rename_info_buffer_rejects_overlong_name():
    name = "x" * ((validation.MAX_FINAL_NAME_UTF16_BYTES // 2) + 1)
    with pytest.raises(validation.ValidationError):
        validation.build_file_rename_info_buffer(
            root_directory_handle=1,
            final_name=name,
        )


@pytest.mark.parametrize(
    "path",
    [
        "",
        "relative\\final",
        "C:relative",
        "C:/slash/final",
        "C:\\",
        "C:\\root\\..\\escape",
        "C:\\root\\.\\final",
        "C:\\root\\stream:name",
        "C:\\root\\*",
        "\\\\server\\share\\final",
        "\\\\?\\C:\\root\\final",
        "\\\\??\\C:\\root\\final",
        "\\\\.\\C:\\root\\final",
        "\\\\?\\Volume{00000000-0000-0000-0000-000000000000}\\final",
        "C:\\root\\x\x00y",
    ],
)
def test_absolute_path_validation_rejects_unsafe_forms(path):
    result = validation.validate_absolute_win32_dos_path_text(path)
    assert result.accepted is False
    assert result.reason


def test_absolute_path_destination_derivation_is_component_bounded(tmp_path):
    if not validation._is_windows():
        pytest.skip("absolute Win32 DOS path derivation is Windows-only")
    root = tmp_path / "fixture"
    root.mkdir()
    destination_parent = root / "dest"
    destination_parent.mkdir()

    final_path, absolute_text = validation.derive_absolute_control_destination(
        fixture_root=root,
        destination_parent=destination_parent,
        final_name="final",
    )

    assert final_path == destination_parent.resolve(strict=True) / "final"
    assert "\\" in absolute_text
    assert not absolute_text.startswith("\\\\?\\")
    assert validation.validate_absolute_win32_dos_path_text(absolute_text).accepted

    sibling = tmp_path / "fixture_sibling"
    sibling.mkdir()
    with pytest.raises(validation.FixtureInvalidError):
        validation.derive_absolute_control_destination(
            fixture_root=root,
            destination_parent=sibling,
            final_name="final",
        )


def test_absolute_path_control_mode_is_explicit(tmp_path):
    assert (
        validation.require_absolute_path_control_mode(
            validation.ABSOLUTE_PATH_CONTROL_MODE
        )
        == validation.ABSOLUTE_PATH_CONTROL_MODE
    )
    with pytest.raises(validation.ValidationError):
        validation.require_absolute_path_control_mode(
            validation.ROOTDIRECTORY_RELATIVE_MODE
        )
    with pytest.raises(validation.ValidationError):
        validation.require_absolute_path_control_mode(retained.RETAINED_MODE)
    with pytest.raises(validation.ValidationError):
        validation.run_absolute_path_control_matrix(
            tmp_path,
            mode=validation.ROOTDIRECTORY_RELATIVE_MODE,
        )
    with pytest.raises(validation.ValidationError):
        validation.run_absolute_path_control_matrix(
            tmp_path,
            mode=retained.RETAINED_MODE,
        )


def test_retained_single_run_wiring_delegates_without_mode_alias(monkeypatch):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return {"delegated": True}

    monkeypatch.setattr(retained, "run_retained_single_run", fake_run)

    result = validation.run_blocker2_retained_single_run(
        "synthetic-authorization",
        case_executor="synthetic-executor",
    )

    assert result == {"delegated": True}
    assert calls == [
        (
            ("synthetic-authorization",),
            {"case_executor": "synthetic-executor"},
        )
    ]


def test_absolute_path_control_matrix_routes_a_cases_without_retained_run(
    tmp_path,
    monkeypatch,
):
    calls = []
    policy_identity = validation.absolute_path_control_policy_identity()

    def case(case_id):
        return validation._case_result(
            case_id,
            validation.CONTROL_FIXTURE_INVALID,
            "stubbed unit matrix case",
            validation.CONTROL_FIXTURE_INVALID,
            policy_identity=policy_identity,
        )

    def one(case_id):
        def run(fixture_root):
            calls.append(case_id)
            assert fixture_root == tmp_path
            return case(case_id)

        return run

    monkeypatch.setattr(
        validation,
        "validate_a1_absolute_path_positive",
        one("A1_POSITIVE_ABSOLUTE_PATH_RENAME"),
    )
    monkeypatch.setattr(
        validation,
        "validate_a2_existing_destination_directory_absolute_path",
        one("A2_EXISTING_DESTINATION_DIRECTORY"),
    )
    monkeypatch.setattr(
        validation,
        "validate_a3_existing_destination_file_absolute_path",
        one("A3_EXISTING_DESTINATION_FILE"),
    )
    monkeypatch.setattr(
        validation,
        "validate_a4_coordinated_destination_claim_absolute_path",
        one("A4_COORDINATED_DESTINATION_CLAIM"),
    )
    monkeypatch.setattr(
        validation,
        "validate_a5_absolute_path_identity_continuity",
        one("A5_SOURCE_TO_FINAL_IDENTITY_CONTINUITY"),
    )
    monkeypatch.setattr(
        validation,
        "validate_a6_absolute_path_native_error_characterization",
        one("A6_NATIVE_ERROR_CHARACTERIZATION"),
    )

    def a7(fixture_root):
        calls.append("A7_INVALID_OR_ESCAPING_ABSOLUTE_DESTINATION_REJECTED")
        assert fixture_root == tmp_path
        return (
            case("A7_INVALID_OR_ESCAPING_ABSOLUTE_DESTINATION_REJECTED"),
        )

    def a8(fixture_root, *, second_volume_root=None):
        calls.append("A8_SAME_VOLUME_MISMATCH_REJECTED")
        assert fixture_root == tmp_path
        assert second_volume_root is None
        return case("A8_SAME_VOLUME_MISMATCH_REJECTED")

    monkeypatch.setattr(
        validation,
        "validate_a7_invalid_or_escaping_absolute_destinations",
        a7,
    )
    monkeypatch.setattr(
        validation,
        "validate_a8_same_volume_mismatch_rejected",
        a8,
    )

    matrix = validation.run_absolute_path_control_matrix(
        tmp_path,
        mode=validation.ABSOLUTE_PATH_CONTROL_MODE,
    )

    assert calls == [
        "A1_POSITIVE_ABSOLUTE_PATH_RENAME",
        "A2_EXISTING_DESTINATION_DIRECTORY",
        "A3_EXISTING_DESTINATION_FILE",
        "A4_COORDINATED_DESTINATION_CLAIM",
        "A5_SOURCE_TO_FINAL_IDENTITY_CONTINUITY",
        "A6_NATIVE_ERROR_CHARACTERIZATION",
        "A7_INVALID_OR_ESCAPING_ABSOLUTE_DESTINATION_REJECTED",
        "A8_SAME_VOLUME_MISMATCH_REJECTED",
    ]
    assert [result.case_id for result in matrix] == calls
    record = validation.build_absolute_path_control_record(case_results=matrix)
    assert record["retained_execution"] is False


def test_absolute_path_control_support_and_native_status_taxonomy():
    unsupported_volume = validation.SupportProfile(
        supported=False,
        status=validation.UNSUPPORTED,
        detail="source and destination are not on the same volume",
        failure_code=validation.UNSUPPORTED_VOLUME_RELATIONSHIP,
    )

    assert (
        validation._absolute_control_support_status(unsupported_volume)
        == validation.CONTROL_SAME_VOLUME_REJECTED
    )
    assert (
        validation._absolute_control_native_failure_status(
            validation.ERROR_INVALID_PARAMETER
        )
        == validation.CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE
    )
    assert (
        validation._absolute_control_native_failure_status(
            validation.ERROR_NOT_SUPPORTED
        )
        == validation.CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL
    )
    assert (
        validation._absolute_control_native_failure_status(
            validation.ERROR_ACCESS_DENIED
        )
        == validation.CONTROL_ACCESS_REJECTED
    )
    assert (
        validation._absolute_control_native_failure_status(999999)
        == validation.CONTROL_NATIVE_ERROR_INDETERMINATE
    )


def test_absolute_path_control_fault_points_are_fail_closed():
    for fault_point in validation.ABSOLUTE_PATH_CONTROL_FAULT_POINTS:
        fault = validation.derive_absolute_control_fault_point_result(fault_point)
        assert fault.status == validation.CONTROL_FAULT_INJECTED
        assert fault.failure_code == validation.CONTROL_FAULT_INJECTED
        assert fault.native_error_code is None

    unknown = validation.derive_absolute_control_fault_point_result("A_FAULT_UNKNOWN")
    assert unknown.status == validation.CONTROL_FIXTURE_INVALID
    assert unknown.failure_code == validation.CONTROL_FAULT_INJECTED


def test_fixture_containment_rejects_outside_git_and_repo_root(tmp_path):
    root = tmp_path / "fixture"
    root.mkdir()
    child = root / "child"
    child.mkdir()
    assert validation.validate_child_path(
        child,
        fixture_root=root,
        must_exist=True,
    ) == child.resolve(strict=True)

    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(validation.FixtureInvalidError):
        validation.validate_child_path(
            outside,
            fixture_root=root,
            must_exist=True,
        )

    git_child = root / ".git" / "objects"
    git_child.mkdir(parents=True)
    with pytest.raises(validation.FixtureInvalidError):
        validation.validate_child_path(
            git_child,
            fixture_root=root,
            must_exist=True,
        )

    with pytest.raises(validation.FixtureInvalidError):
        validation.validate_fixture_root(Path(validation.__file__).resolve().parents[2])


def test_manifest_construction_hashes_regular_files_and_rejects_bounds(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "alpha.txt").write_bytes(b"alpha\n")
    nested = source / "nested"
    nested.mkdir()
    (nested / "beta.txt").write_bytes(b"beta\n")

    manifest = validation.build_content_manifest(source)
    assert manifest.entry_count == 3
    assert manifest.total_file_bytes == len(b"alpha\n") + len(b"beta\n")
    assert manifest.manifest_sha256 == validation.build_content_manifest(
        source
    ).manifest_sha256

    too_many = tmp_path / "too_many"
    too_many.mkdir()
    for index in range(validation.MAX_MANIFEST_ENTRIES + 1):
        (too_many / ("f%03d.txt" % index)).write_bytes(b"x")
    with pytest.raises(validation.FixtureInvalidError):
        validation.build_content_manifest(too_many)


def test_support_profile_fails_closed_for_missing_source_or_non_windows(tmp_path):
    root = tmp_path / "fixture"
    root.mkdir()
    destination = root / "dest"
    destination.mkdir()
    profile = validation.admit_support_profile(
        fixture_root=root,
        source_directory=root / "missing",
        destination_parent=destination,
    )
    assert profile.status in (
        validation.FIXTURE_INVALID,
        validation.SKIPPED,
        validation.UNSUPPORTED,
        validation.INDETERMINATE,
    )


def test_identity_and_manifest_result_derivation():
    identity = validation.ObjectIdentity(10, 20, 30)
    other_same_volume = validation.ObjectIdentity(10, 20, 31)
    other_volume = validation.ObjectIdentity(11, 20, 30)
    manifest = validation.ContentManifest((), 0, 0, "a" * 64)
    changed_manifest = validation.ContentManifest((), 0, 0, "b" * 64)
    probes = (
        validation.DurabilityProbe(
            "D1_FINAL_PARENT",
            validation.durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            "ok",
        ),
        validation.DurabilityProbe(
            "D2_FORMER_SOURCE_PARENT",
            validation.durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            "ok",
        ),
        validation.DurabilityProbe(
            "D3_FINAL_THEN_FORMER_PARENT_ORDER",
            validation.durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            "ok",
        ),
        validation.DurabilityProbe(
            "D3_FORMER_THEN_FINAL_PARENT_ORDER",
            validation.durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            "ok",
        ),
    )

    assert (
        validation.derive_success_status(
            source_identity_before=identity,
            retained_handle_identity_after=identity,
            final_identity_after=identity,
            manifest_before=manifest,
            manifest_after=manifest,
            durability_probes=probes,
        )
        == validation.PRIMITIVE_VALIDATION_CONFIRMED
    )
    assert (
        validation.derive_success_status(
            source_identity_before=identity,
            retained_handle_identity_after=other_same_volume,
            final_identity_after=identity,
            manifest_before=manifest,
            manifest_after=manifest,
            durability_probes=probes,
        )
        == validation.IDENTITY_MISMATCH
    )
    assert (
        validation.derive_success_status(
            source_identity_before=identity,
            retained_handle_identity_after=identity,
            final_identity_after=other_volume,
            manifest_before=manifest,
            manifest_after=manifest,
            durability_probes=probes,
        )
        == validation.CROSS_VOLUME_COPY_DETECTED
    )
    assert (
        validation.derive_success_status(
            source_identity_before=identity,
            retained_handle_identity_after=identity,
            final_identity_after=identity,
            manifest_before=manifest,
            manifest_after=changed_manifest,
            durability_probes=probes,
        )
        == validation.CONTENT_MISMATCH
    )
    assert (
        validation.derive_success_status(
            source_identity_before=identity,
            retained_handle_identity_after=identity,
            final_identity_after=identity,
            manifest_before=manifest,
            manifest_after=manifest,
            durability_probes=(),
        )
        == validation.DURABILITY_UNCONFIRMED
    )


def test_unknown_native_error_and_fault_point_results_are_retained():
    case = validation._case_result(
        "UNKNOWN_NATIVE",
        validation.INDETERMINATE,
        "unknown native failure",
        validation.NATIVE_RENAME_FAILED,
        native_error_code=999999,
        native_error_name=None,
    )
    assert case.native_error_code == 999999
    assert case.native_error_name is None

    for fault_point in validation.FAULT_POINTS:
        fault = validation.derive_fault_point_result(fault_point)
        assert fault.status == validation.INDETERMINATE
        assert fault.failure_code == validation.FAULT_INJECTED

    unknown = validation.derive_fault_point_result("F0_UNKNOWN")
    assert unknown.status == validation.FIXTURE_INVALID


def test_native_error_classification_keeps_error_87_indeterminate():
    assert (
        validation._native_rename_failure_status(validation.ERROR_INVALID_PARAMETER)
        == validation.INDETERMINATE
    )
    assert (
        validation._native_rename_failure_status(validation.ERROR_NOT_SUPPORTED)
        == validation.UNSUPPORTED
    )
    detail = validation._native_rename_failure_detail(validation.ERROR_INVALID_PARAMETER)
    assert "cause remains unresolved" in detail
    assert "RootDirectory-relative contract rejection" in detail
    assert "destination-parent access/setup requirement" in detail
    assert "another valid native parameter constraint" in detail


def test_invalid_fixture_does_not_write_temporary_record(tmp_path):
    root = tmp_path / "fixture"
    root.mkdir()
    outside = tmp_path / "outside"
    target = outside / "blocker_2_promotion_validation_record_v0_1.json"
    with pytest.raises(validation.FixtureInvalidError):
        validation.write_temporary_validation_record(
            fixture_root=root,
            output_directory=outside,
            record={"case_results": []},
        )
    assert not target.exists()


def test_source_identity_helpers_include_docs_and_baseline():
    identities = validation.validation_source_identities()
    assert identities["baseline_commit"] == validation.BASELINE_COMMIT
    assert identities["runner_source_sha256"] == validation.module_source_sha256()
    assert identities["schema_source_sha256"] == validation.validation_schema_source_sha256()
    assert identities["authorization_doc_identity"]["raw_sha256"]
