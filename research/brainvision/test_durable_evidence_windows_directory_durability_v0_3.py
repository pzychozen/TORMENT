from __future__ import annotations

from dataclasses import replace
import hashlib
from types import SimpleNamespace

import pytest

import durable_evidence_durability_v0_3 as durability
import durable_evidence_primary_writer_v0_3 as writer
import durable_evidence_publication_recovery_v0_3 as recovery
import durable_evidence_publication_replay_v0_3 as publication_replay
import durable_evidence_publication_v0_3 as publication
import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter

from test_durable_evidence_publication_recovery_v0_3 import (
    RECOVERY_AUTHORITY,
    run_recovery,
    setup_final_artifacts_with_incomplete_publication_chain,
)
from test_durable_evidence_publication_v0_3 import (
    EXECUTION_IDENTITY,
    PUBLICATION_AUTHORITY,
    PositiveTmpPromotionAdapter,
    RoleStatusSyntheticAdapter,
    project,
)


class SyntheticDirectoryAdapter(windows_adapter.WindowsDurabilityAdapter):
    def __init__(
        self,
        *,
        status: str,
        failure_code: str | None,
        policy_identity: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.failure_code = failure_code
        self.policy_identity = policy_identity

    def sync_directory_entry(self, directory_path: str, *, context=None):
        target_role = (
            context.target_role
            if context is not None
            else schema.ARTIFACT_PARENT_DIRECTORY
        )
        return windows_adapter.DirectoryDurabilityResult(
            status=self.status,
            detail="synthetic directory durability result",
            failure_code=self.failure_code,
            adapter_policy_identity=(
                self.policy_identity
                if self.policy_identity is not None
                else schema.directory_durability_policy_identity()
            ),
            target_role=target_role,
        )


class FakeTargetAdmissionKernel32:
    def __init__(self, attributes: int, error_code: int = 0) -> None:
        self.attributes = attributes
        self.error_code = error_code

    def GetDriveTypeW(self, root):
        return windows_adapter.DRIVE_FIXED

    def GetVolumeInformationW(
        self,
        root,
        volume_name,
        volume_name_size,
        serial,
        max_component,
        flags,
        filesystem_name,
        filesystem_name_size,
    ):
        filesystem_name.value = "NTFS"
        return True

    def GetFileAttributesW(self, path):
        return self.attributes

    def GetLastError(self):
        return self.error_code


def _stored_record():
    logical_record = schema.build_scientific_logical_record(
        record_kind="MANIFEST_CONTACT_ATTEMPT",
        sequence_number=1,
        execution_identity="8" * 64,
        scientific_execution_authorization_identity="9" * 64,
        predecessor_logical_record_sha256="a" * 64,
        payload={"pass_index": 1},
    )
    return schema.build_stored_record_object(
        logical_record=logical_record,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="1" * 32,
    )


def _foreign_directory_policy_identity():
    return {
        "policy_schema_identity": schema.DIRECTORY_DURABILITY_POLICY_SCHEMA,
        "policy_sha256": "f" * 64,
    }


def _ledger_under_directory_policy(record_writes, directory_policy_identity):
    return durability.VerifiedDurabilityEvidence.from_immutable_write_results(
        record_writes=tuple(
            (
                stored,
                replace(
                    write_result,
                    directory_durability_policy_identity=directory_policy_identity,
                ),
            )
            for stored, write_result in record_writes
        ),
        expected_directory_durability_policy_identity=directory_policy_identity,
    )


def test_directory_policy_identity_is_canonical_and_stable():
    declaration = schema.directory_durability_policy_declaration()
    digest = hashlib.sha256(schema.canonical_json_bytes(declaration)).hexdigest()
    identity = schema.directory_durability_policy_identity()
    assert digest == schema.directory_durability_policy_sha256()
    assert identity == {
        "policy_schema_identity": schema.DIRECTORY_DURABILITY_POLICY_SCHEMA,
        "policy_sha256": digest,
    }
    schema.validate_directory_durability_policy_identity(identity)
    assert tuple(declaration.keys()) == (
        schema.DIRECTORY_DURABILITY_POLICY_DECLARATION_KEYS
    )


def test_fail_closed_default_adapter_reports_absent_policy_bound_result():
    context = windows_adapter.DirectoryDurabilityContext(
        target_role=schema.STAGING_DIRECTORY
    )
    result = windows_adapter.FailClosedWindowsDurabilityAdapter().sync_directory_entry(
        "synthetic",
        context=context,
    )
    assert result.status == schema.DIRECTORY_DURABILITY_UNSUPPORTED
    assert result.failure_code == schema.ADAPTER_ABSENT
    assert result.adapter_policy_identity == schema.directory_durability_policy_identity()
    assert result.target_role == schema.STAGING_DIRECTORY


def test_non_windows_adapter_invocation_fails_closed(monkeypatch):
    monkeypatch.setattr(windows_adapter.sys, "platform", "linux")
    result = windows_adapter.Win32DirectoryDurabilityAdapter().sync_directory_entry(
        "/tmp/synthetic",
        context=windows_adapter.DirectoryDurabilityContext(
            target_role=schema.STAGING_PARENT_DIRECTORY
        ),
    )
    assert result.status == schema.DIRECTORY_DURABILITY_UNSUPPORTED
    assert result.failure_code == schema.NON_WINDOWS_PLATFORM
    assert result.platform == "linux"


@pytest.mark.parametrize(
    "error_code, phase, expected_status, expected_failure",
    (
        (
            windows_adapter.ERROR_ACCESS_DENIED,
            "open",
            schema.DIRECTORY_DURABILITY_DENIED,
            schema.DIRECTORY_OPEN_DENIED,
        ),
        (
            windows_adapter.ERROR_INVALID_PARAMETER,
            "flush",
            schema.DIRECTORY_DURABILITY_OPERATION_FAILED,
            schema.DIRECTORY_FLUSH_FAILED,
        ),
        (
            windows_adapter.ERROR_NOT_SUPPORTED,
            "flush",
            schema.DIRECTORY_DURABILITY_UNSUPPORTED,
            schema.DIRECTORY_FLUSH_UNSUPPORTED,
        ),
        (
            windows_adapter.ERROR_FILE_NOT_FOUND,
            "open",
            schema.DIRECTORY_DURABILITY_TARGET_INVALID,
            schema.TARGET_MISSING,
        ),
        (
            999999,
            "flush",
            schema.DIRECTORY_DURABILITY_INDETERMINATE,
            schema.UNKNOWN_NATIVE_ERROR,
        ),
    ),
)
def test_native_error_mapping_preserves_numeric_code(
    error_code, phase, expected_status, expected_failure
):
    context = windows_adapter.DirectoryDurabilityContext()
    result = windows_adapter._native_failure(error_code, phase, context)
    assert result.status == expected_status
    assert result.failure_code == expected_failure
    assert result.native_error_code == error_code
    if error_code == 999999:
        assert result.native_error_name is None


@pytest.mark.parametrize(
    "attributes, error_code, expected_status, expected_failure",
    (
        (
            windows_adapter.INVALID_FILE_ATTRIBUTES,
            windows_adapter.ERROR_FILE_NOT_FOUND,
            schema.DIRECTORY_DURABILITY_TARGET_INVALID,
            schema.TARGET_MISSING,
        ),
        (0, 0, schema.DIRECTORY_DURABILITY_TARGET_INVALID, schema.TARGET_NOT_DIRECTORY),
        (
            windows_adapter.FILE_ATTRIBUTE_DIRECTORY
            | windows_adapter.FILE_ATTRIBUTE_REPARSE_POINT,
            0,
            schema.DIRECTORY_DURABILITY_TARGET_INVALID,
            schema.TARGET_REPARSE_POINT,
        ),
    ),
)
def test_target_admission_failures_are_classified(
    tmp_path, monkeypatch, attributes, error_code, expected_status, expected_failure
):
    monkeypatch.setattr(windows_adapter.sys, "platform", "win32")
    monkeypatch.setattr(
        windows_adapter.sys,
        "getwindowsversion",
        lambda: SimpleNamespace(major=10, product_type=1),
    )
    monkeypatch.setattr(
        windows_adapter,
        "_kernel32",
        lambda: FakeTargetAdmissionKernel32(attributes, error_code),
    )
    result = windows_adapter.Win32DirectoryDurabilityAdapter().sync_directory_entry(
        str(tmp_path / "target"),
        context=windows_adapter.DirectoryDurabilityContext(
            target_role=schema.STAGING_DIRECTORY
        ),
    )
    assert result.status == expected_status
    assert result.failure_code == expected_failure
    assert result.target_role == schema.STAGING_DIRECTORY


@pytest.mark.parametrize(
    "status, failure_code",
    (
        (schema.DIRECTORY_DURABILITY_UNSUPPORTED, schema.ADAPTER_ABSENT),
        (schema.DIRECTORY_DURABILITY_DENIED, schema.DIRECTORY_OPEN_DENIED),
        (schema.DIRECTORY_DURABILITY_INDETERMINATE, schema.UNKNOWN_NATIVE_ERROR),
        (schema.DIRECTORY_DURABILITY_TARGET_INVALID, schema.TARGET_MISSING),
        (schema.DIRECTORY_DURABILITY_IDENTITY_CHANGED, schema.TARGET_IDENTITY_CHANGED),
        (schema.DIRECTORY_DURABILITY_OPERATION_FAILED, schema.DIRECTORY_FLUSH_FAILED),
    ),
)
def test_non_confirmed_statuses_withhold_primary_writer_completion(
    tmp_path, status, failure_code
):
    result = writer.write_stored_record_object(
        tmp_path,
        _stored_record(),
        durability_adapter=SyntheticDirectoryAdapter(
            status=status,
            failure_code=failure_code,
        ),
    )
    assert result.authoritative_status == writer.BYTE_VALID_DURABILITY_UNCONFIRMED
    assert result.directory_durability_failure_code == failure_code


def test_directory_policy_mismatch_withholds_primary_writer_completion(tmp_path):
    result = writer.write_stored_record_object(
        tmp_path,
        _stored_record(),
        durability_adapter=SyntheticDirectoryAdapter(
            status=schema.DIRECTORY_DURABILITY_CONFIRMED,
            failure_code=None,
            policy_identity=_foreign_directory_policy_identity(),
        ),
    )
    assert result.authoritative_status == writer.BYTE_VALID_DURABILITY_UNCONFIRMED
    assert result.directory_durability_failure_code == schema.POLICY_IDENTITY_MISMATCH


def test_confirmed_policy_bound_write_enters_verified_durability(tmp_path):
    stored = _stored_record()
    write_result = writer.write_stored_record_object(
        tmp_path,
        stored,
        durability_adapter=SyntheticDirectoryAdapter(
            status=schema.DIRECTORY_DURABILITY_CONFIRMED,
            failure_code=None,
        ),
    )
    ledger = durability.VerifiedDurabilityEvidence.from_immutable_write_results(
        record_writes=((stored, write_result),)
    )
    assert ledger.has_record_object(stored["stored_object_sha256"])


def test_j1_publication_withholds_completion_on_staged_set_denial(tmp_path):
    adapter = RoleStatusSyntheticAdapter(
        {
            schema.STAGING_DIRECTORY: (
                schema.DIRECTORY_DURABILITY_DENIED,
                schema.DIRECTORY_FLUSH_DENIED,
            )
        }
    )
    result, _, _ = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
        durability_adapter=adapter,
    )
    assert result.classification == publication.PUBLICATION_STAGING_DURABILITY_UNCONFIRMED
    assert result.directory_durability_failure_code == schema.DIRECTORY_FLUSH_DENIED


def test_j2_recovery_withholds_completion_on_record_parent_denial(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    recovered = run_recovery(
        tmp_path,
        publication_result,
        bundle_payload,
        completion,
        durability_adapter=RoleStatusSyntheticAdapter(
            {},
            default_status=schema.DIRECTORY_DURABILITY_DENIED,
            default_failure_code=schema.DIRECTORY_OPEN_DENIED,
        ),
    )
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED
    )
    assert recovered.directory_durability_failure_code == schema.DIRECTORY_OPEN_DENIED


def test_replay_rejects_foreign_directory_policy_evidence(tmp_path):
    result, bundle_payload, completion = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    foreign_policy = _foreign_directory_policy_identity()
    ledger = _ledger_under_directory_policy(
        tuple(
            (item.stored_record_object, item.write_result)
            for item in result.record_writes
        ),
        foreign_policy,
    )
    replayed = publication_replay.replay_publication_chain(
        result.paths.chain_directory,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=result.publication_chain_identity,
        publication_projection_identity=result.publication_projection_identity,
        bundle_payload_sha256=bundle_payload["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=completion[
            "logical_record_sha256"
        ],
        expected_artifact_sha256s=result.artifact_sha256s,
        durability_evidence=ledger,
    )
    assert replayed.classification == (
        publication_replay.PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED
    )
