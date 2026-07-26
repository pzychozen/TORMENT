from __future__ import annotations

import ctypes
import math
from pathlib import Path

import pytest

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


def test_file_rename_info_buffer_rejects_overlong_name():
    name = "x" * ((validation.MAX_FINAL_NAME_UTF16_BYTES // 2) + 1)
    with pytest.raises(validation.ValidationError):
        validation.build_file_rename_info_buffer(
            root_directory_handle=1,
            final_name=name,
        )


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
