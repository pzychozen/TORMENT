from __future__ import annotations

import sys

import pytest

import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


def test_win32_directory_durability_confirms_pytest_tmp_path(tmp_path):
    if sys.platform != "win32":
        pytest.skip("isolated Windows directory durability confirmation")

    before = {item.name for item in tmp_path.iterdir()}
    target = tmp_path / "directory_durability_target"
    target.mkdir()
    result = windows_adapter.Win32DirectoryDurabilityAdapter().sync_directory_entry(
        str(target),
        context=windows_adapter.DirectoryDurabilityContext(
            target_role=schema.STAGING_DIRECTORY
        ),
    )
    if result.status != schema.DIRECTORY_DURABILITY_CONFIRMED:
        pytest.fail(
            "Windows directory durability was not confirmed: "
            "%s %s %s"
            % (result.status, result.failure_code, result.native_error_code)
        )
    assert result.failure_code is None
    assert result.adapter_policy_identity == (
        schema.directory_durability_policy_identity()
    )
    assert result.target_role == schema.STAGING_DIRECTORY
    assert result.validation_profile_identity == (
        schema.DIRECTORY_DURABILITY_VALIDATION_PROFILE_IDENTITY
    )
    assert result.target_path_identity is not None
    assert target.exists() and target.is_dir()
    assert {item.name for item in tmp_path.iterdir()} == (
        before | {"directory_durability_target"}
    )
