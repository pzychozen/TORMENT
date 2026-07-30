from __future__ import annotations

from dataclasses import asdict
import hashlib
import os
from pathlib import Path

import pytest

import blocker2_r4_authority_b_evidence_publisher_v0_1 as publisher
import blocker2_r4_ordered_directory_creation_helper_v0_1 as helper
import durable_evidence_schema_v0_3 as durable_schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


HEAD = "d75598ae42a9b0294e021285f1d4061784653e4e"


def path_model(tmp_path: Path) -> helper.PathModel:
    root = tmp_path / "r4-root"
    c1 = root / "brainvision_authoritative_inputs_test"
    c2 = c1 / "blocker2_s3b_v0_3"
    c3 = c2 / "r4_prepare_paths"
    return helper.PathModel(
        required_root=str(root),
        components=(str(c1), str(c2), str(c3)),
        evidence_record_path=str(
            c3 / "r4_prepare_paths_path_creation_evidence_record_v0_1.canonical.json"
        ),
        canonical_input_path=str(
            c3 / "r4_prepare_paths_authorization_input_v0_1.canonical.json"
        ),
    )


def make_parent_dirs(model: helper.PathModel) -> None:
    Path(model.evidence_record_path).parent.mkdir(parents=True, exist_ok=True)


def parent_text(raw_path: str) -> str:
    return str(Path(raw_path).parent)


def authority_assertions() -> helper.AuthorityAssertions:
    return helper.AuthorityAssertions(
        window_open=True,
        authority_a_active=True,
        authority_b_active=True,
        authority_c_active=False,
        authority_d_active=False,
        authority_e_active=False,
    )


def identity(index: int) -> helper.ObjectIdentity:
    return helper.ObjectIdentity(
        volume_serial_number=1001,
        file_index_high=0,
        file_index_low=index,
    )


class FakeNativeAdapter:
    def __init__(self, model: helper.PathModel) -> None:
        self.model = model
        self.directories = {
            model.required_root,
            *model.components,
            parent_text(model.evidence_record_path),
        }
        self.files: set[str] = set()
        self.absence_overrides = {}
        self.absence_exceptions = {}
        self.open_fail = set()
        self.closed = []
        self.opened = []
        self.absence_calls = []

    def open_directory(self, raw_path: str) -> helper.OpenDirectoryResult:
        self._reject_governed(raw_path)
        self.opened.append(raw_path)
        if raw_path in self.open_fail or raw_path not in self.directories:
            return helper.OpenDirectoryResult(
                opened=False,
                error=helper.NativeError(3, "ERROR_PATH_NOT_FOUND", "missing"),
            )
        ident = identity(len(self.opened))
        evidence = helper.DirectoryHandleEvidence(
            raw_path=raw_path,
            identity=ident,
            volume_profile=helper.VolumeProfile(
                drive_type=3,
                filesystem_name="NTFS",
                volume_serial_number=ident.volume_serial_number,
            ),
            is_directory=True,
            is_reparse_point=False,
            attributes_source="synthetic",
            native_handle_source="synthetic",
            share_limitations="synthetic",
        )
        return helper.OpenDirectoryResult(
            opened=True,
            handle=helper.DirectoryHandle(
                evidence=evidence,
                close_callback=lambda path=raw_path: self.closed.append(path),
            ),
        )

    def check_absent(
        self,
        raw_path: str,
        *,
        allow_missing_ancestor: bool = False,
    ) -> helper.AbsenceResult:
        self._reject_governed(raw_path)
        self.absence_calls.append(raw_path)
        if raw_path in self.absence_exceptions:
            raise self.absence_exceptions[raw_path]
        if raw_path in self.absence_overrides:
            return self.absence_overrides[raw_path]
        if raw_path in self.files or raw_path in self.directories:
            kind = "directory" if raw_path in self.directories else "file"
            return helper.AbsenceResult(
                positively_absent=False,
                basis="pre_existing",
                pre_existing_kind=kind,
            )
        if parent_text(raw_path) not in self.directories and not allow_missing_ancestor:
            return helper.AbsenceResult(
                positively_absent=False,
                basis="parent_missing",
                native_error_code=3,
                native_error_name="ERROR_PATH_NOT_FOUND",
            )
        return helper.AbsenceResult(
            positively_absent=True,
            basis="synthetic_positive_absence",
            native_error_code=2,
            native_error_name="ERROR_FILE_NOT_FOUND",
        )

    def _reject_governed(self, raw_path: str) -> None:
        assert not raw_path.casefold().startswith(publisher.GOVERNED_PREFIX.casefold())


class FakeDurabilityAdapter:
    def __init__(
        self,
        status: str = durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
        failure_code: str | None = None,
        policy_identity: dict[str, str] | None = None,
        raises: Exception | None = None,
    ) -> None:
        self.status = status
        self.failure_code = failure_code
        self.policy_identity = policy_identity
        self.raises = raises
        self.calls = []

    def sync_directory_entry(self, directory_path: str, *, context=None):
        self.calls.append((directory_path, context.target_role if context else None))
        if self.raises is not None:
            raise self.raises
        return windows_adapter.DirectoryDurabilityResult(
            status=self.status,
            detail="synthetic durability",
            failure_code=self.failure_code,
            adapter_policy_identity=(
                self.policy_identity
                if self.policy_identity is not None
                else durable_schema.directory_durability_policy_identity()
            ),
            target_role=context.target_role if context else None,
        )


class FakeCreateHandle:
    def __init__(
        self,
        *,
        write_result: int | Exception | None = None,
        flush_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.write_result = write_result
        self.flush_error = flush_error
        self.close_error = close_error
        self.write_calls = 0
        self.close_calls = 0
        self.backing = open(os.devnull, "wb")

    def write(self, payload: bytes):
        self.write_calls += 1
        if isinstance(self.write_result, Exception):
            raise self.write_result
        if self.write_result is None:
            return len(payload)
        return self.write_result

    def flush(self) -> None:
        if self.flush_error is not None:
            raise self.flush_error

    def fileno(self) -> int:
        return self.backing.fileno()

    def close(self) -> None:
        self.close_calls += 1
        self.backing.close()
        if self.close_error is not None:
            raise self.close_error


def helper_result_for(model: helper.PathModel, *, body_mutator=None):
    operations = []
    for index, raw_path in enumerate(model.components, start=1):
        operations.append(
            {
                "committed_required": {
                    "ordinal": index,
                    "operation_ordering": index,
                    "exact_absolute_path": raw_path,
                    "immediate_parent_path": model.parents()[index - 1],
                    "target_absence_before": {"positively_absent": True},
                    "later_component_absence_pre": [],
                    "target_presence_after": helper.TRI_TRUE,
                    "directory_type": "ordinary_directory",
                    "reparse_status": helper.TRI_FALSE,
                    "filesystem_and_drive_profile": {
                        "drive_type": 3,
                        "filesystem_name": "NTFS",
                        "volume_serial_number": 1001,
                    },
                    "volume_identity": {
                        "drive_type": 3,
                        "filesystem_name": "NTFS",
                        "volume_serial_number": 1001,
                    },
                    "directory_file_identity": {
                        "volume_serial_number": 1001,
                        "file_index_high": 0,
                        "file_index_low": index,
                    },
                    "post_create_observed_identity": {
                        "volume_serial_number": 1001,
                        "file_index_high": 0,
                        "file_index_low": index,
                    },
                    "parent_post_identity": {
                        "volume_serial_number": 1001,
                        "file_index_high": 0,
                        "file_index_low": index + 10,
                    },
                    "later_component_absence_post": [],
                    "operator_process_result": "os.mkdir_returned_success",
                    "operation_timestamp_utc": "2026-07-30T00:00:00.000000Z",
                    "operation_monotonic_ns": index,
                },
                "derived_implementation": {
                    "creation_call": {
                        "primitive": "os.mkdir",
                        "outcome": "returned_success",
                        "exclusive_create_success": True,
                    }
                },
                "optional_diagnostic": {"null_round_trip": None},
            }
        )
    evidence_body = {
        "schema": helper.EVIDENCE_BODY_SCHEMA,
        "version": helper.VERSION,
        "authority_assertions": asdict(authority_assertions()),
        "authority_state": {"required_authority_gate_satisfied": True},
        "accepted_invocation_head": HEAD,
        "path_model": model.as_dict(),
        "test_path_model": True,
        "execution_seams": {"primitive_identity": "synthetic"},
        "publication_boundary": {
            "publishes_evidence_record": False,
            "publishes_canonical_input": False,
            "invokes_runner": False,
            "successful_return_is_unpublished_record_candidate": True,
        },
        "operations": operations,
        "aggregate": {
            "contact_started": True,
            "opportunity_consumed": True,
            "mutation_succeeded_count": 3,
            "sequence_terminal": False,
            "full_ordered_sequence_succeeded": True,
        },
    }
    if body_mutator is not None:
        body_mutator(evidence_body)
    body_identity = helper.body_identity_for_evidence_body(evidence_body)
    return helper.HelperResult(
        classification=helper.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION,
        classification_kind=helper.CLASSIFICATION_DERIVED_NON_TERMINAL,
        terminal=False,
        committed_detail_label=None,
        derived_subreason=None,
        authority_active=True,
        contact_started=True,
        opportunity_consumed=True,
        mutation_succeeded_count=3,
        sequence_terminal=False,
        evidence_body=evidence_body,
        body_identity=body_identity,
        authority_assertions_observed=asdict(authority_assertions()),
        required_authority_gate_satisfied=True,
        execution_mode=helper.EXECUTION_MODE_TEST_OR_CUSTOM,
    )


def build_record(model: helper.PathModel):
    result = helper_result_for(model)
    record = publisher.build_path_creation_evidence_record(
        result,
        corrected_governance_chain_identities={"head": HEAD},
        accepted_invocation_head=HEAD,
        commit_free_window_declaration={"window": "ASSERTED_OPEN"},
        authority_assertions=authority_assertions(),
        path_model=model,
        source_identities={"test": {"sha256": "1" * 64}},
    )
    return result, record, publisher.canonical_record_bytes(record)


def test_successful_publish_validate_acceptance_uses_external_whole_identity(tmp_path):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    native = FakeNativeAdapter(model)
    helper_result, record, payload = build_record(model)

    publication = publisher.publish_record_create_new(
        raw_record_path=model.evidence_record_path,
        canonical_bytes=payload,
        durability_adapter=FakeDurabilityAdapter(),
        native_adapter=native,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
    )
    acceptance = publisher.accept_authority_b_evidence(
        publication_result=publication,
        raw_record_path=model.evidence_record_path,
        expected_canonical_bytes=payload,
        expected_helper_body_identity=helper_result.body_identity,
        expected_accepted_invocation_head=HEAD,
        native_adapter=native,
        path_model=model,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
    )

    assert publication.accepted_for_validation is True
    assert publication.write_attempt_count == 1
    assert acceptance.accepted is True
    assert acceptance.whole_record_byte_count == len(payload)
    assert acceptance.whole_record_sha256 == hashlib.sha256(payload).hexdigest()
    parsed = acceptance.validation_result.parsed_record
    assert parsed["canonical_input_status"] == publisher.CANONICAL_INPUT_STATUS
    for prohibited in publisher.PROHIBITED_RECORD_FIELDS:
        assert prohibited not in parsed
    assert "whole_record_sha256" not in parsed
    assert publisher.canonical_record_bytes(record["evidence_body"]) == (
        helper.canonical_json_bytes(record["evidence_body"])
    )
    assert record["body_identity"] == helper_result.body_identity


def test_duplicate_key_rejection_and_null_preservation():
    assert publisher.canonical_record_bytes({"a": None}) == b'{"a":null}'
    with pytest.raises(durable_schema.EvidenceValidationError):
        durable_schema.canonical_json_bytes({"a": None})
    with pytest.raises(publisher.R4CanonicalizationError):
        publisher.load_canonical_record_bytes(b'{"a":1,"a":2}')


@pytest.mark.parametrize(
    "mutator, expected",
    (
        (
            lambda result: object.__setattr__(result, "mutation_succeeded_count", 2),
            "Authority-A mutation count must be exactly three",
        ),
        (
            lambda result: result.evidence_body.__setitem__(
                "accepted_invocation_head", "0" * 40
            ),
            "accepted invocation HEAD mismatch",
        ),
        (
            lambda result: result.body_identity.__setitem__("body_sha256", "f" * 64),
            "body sha256 mismatch",
        ),
    ),
)
def test_record_construction_rejects_required_helper_mismatches(tmp_path, mutator, expected):
    model = path_model(tmp_path)
    result = helper_result_for(model)
    mutator(result)
    with pytest.raises(publisher.R4RecordConstructionError, match=expected):
        publisher.build_path_creation_evidence_record(
            result,
            corrected_governance_chain_identities={},
            accepted_invocation_head=HEAD,
            commit_free_window_declaration={},
            authority_assertions=authority_assertions(),
            path_model=model,
            source_identities={},
        )


def test_record_path_preexists_is_invalid_and_does_not_open(tmp_path):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    record_path = Path(model.evidence_record_path)
    record_path.write_bytes(b"existing")
    native = FakeNativeAdapter(model)
    native.files.add(model.evidence_record_path)
    opened = []

    result = publisher.publish_record_create_new(
        raw_record_path=model.evidence_record_path,
        canonical_bytes=b"{}",
        durability_adapter=FakeDurabilityAdapter(),
        native_adapter=native,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
        file_opener=lambda path, mode: opened.append((path, mode)),
    )

    assert result.classification == publisher.AUTHORITY_B_RECORD_INVALID
    assert result.create_new_attempted is False
    assert opened == []
    assert record_path.read_bytes() == b"existing"


def test_positive_absence_indeterminate_fails_before_contact(tmp_path):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    native = FakeNativeAdapter(model)
    native.absence_overrides[model.evidence_record_path] = helper.AbsenceResult(
        positively_absent=False,
        basis="indeterminate",
    )

    result = publisher.publish_record_create_new(
        raw_record_path=model.evidence_record_path,
        canonical_bytes=b"{}",
        durability_adapter=FakeDurabilityAdapter(),
        native_adapter=native,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
    )

    assert result.classification == publisher.AUTHORITY_B_RECORD_UNPUBLISHED
    assert result.contact_started is False


@pytest.mark.parametrize(
    "handle_factory, fsync_callable, expected_code",
    (
        (
            lambda: FakeCreateHandle(write_result=1),
            lambda fd: None,
            "RECORD_SHORT_WRITE",
        ),
        (
            lambda: FakeCreateHandle(write_result=OSError("write failed")),
            lambda fd: None,
            "RECORD_WRITE_PATH_FAILED",
        ),
        (
            lambda: FakeCreateHandle(flush_error=OSError("flush failed")),
            lambda fd: None,
            "RECORD_WRITE_PATH_FAILED",
        ),
        (
            lambda: FakeCreateHandle(),
            lambda fd: (_ for _ in ()).throw(OSError("fsync failed")),
            "RECORD_WRITE_PATH_FAILED",
        ),
        (
            lambda: FakeCreateHandle(close_error=OSError("close failed")),
            lambda fd: None,
            "RECORD_CLOSE_FAILED",
        ),
    ),
)
def test_create_new_write_path_failures_close_once(
    tmp_path, handle_factory, fsync_callable, expected_code
):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    native = FakeNativeAdapter(model)
    handle = handle_factory()

    result = publisher.publish_record_create_new(
        raw_record_path=model.evidence_record_path,
        canonical_bytes=b"{}",
        durability_adapter=FakeDurabilityAdapter(),
        native_adapter=native,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
        file_opener=lambda path, mode: handle,
        fsync_callable=fsync_callable,
    )

    assert result.classification == publisher.AUTHORITY_B_RECORD_INVALID
    assert result.failure_code == expected_code
    assert result.create_new_attempted is True
    assert handle.write_calls == 1
    assert handle.close_calls == 1


def test_exclusive_create_collision_is_invalid_and_single_attempt(tmp_path):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    native = FakeNativeAdapter(model)
    calls = []

    def collide(path, mode):
        calls.append((path, mode))
        raise FileExistsError(path)

    result = publisher.publish_record_create_new(
        raw_record_path=model.evidence_record_path,
        canonical_bytes=b"{}",
        durability_adapter=FakeDurabilityAdapter(),
        native_adapter=native,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
        file_opener=collide,
    )

    assert result.classification == publisher.AUTHORITY_B_RECORD_INVALID
    assert result.failure_code == "RECORD_CREATE_NEW_COLLISION"
    assert calls == [(model.evidence_record_path, "xb")]


@pytest.mark.parametrize(
    "adapter",
    (
        FakeDurabilityAdapter(
            durable_schema.DIRECTORY_DURABILITY_UNSUPPORTED,
            durable_schema.NON_WINDOWS_PLATFORM,
        ),
        FakeDurabilityAdapter(raises=RuntimeError("adapter exploded")),
        FakeDurabilityAdapter(
            durable_schema.DIRECTORY_DURABILITY_IDENTITY_CHANGED,
            durable_schema.TARGET_IDENTITY_CHANGED,
        ),
        FakeDurabilityAdapter(
            durable_schema.DIRECTORY_DURABILITY_CONFIRMED,
            None,
            {
                "policy_schema_identity": durable_schema.DIRECTORY_DURABILITY_POLICY_SCHEMA,
                "policy_sha256": "f" * 64,
            },
        ),
    ),
)
def test_directory_durability_nonaccepted_states_fail_closed(tmp_path, adapter):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    native = FakeNativeAdapter(model)

    result = publisher.publish_record_create_new(
        raw_record_path=model.evidence_record_path,
        canonical_bytes=b"{}",
        durability_adapter=adapter,
        native_adapter=native,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
    )

    assert result.classification == publisher.AUTHORITY_B_RECORD_INVALID
    assert result.failure_code == "RECORD_DIRECTORY_DURABILITY_UNCONFIRMED"
    assert Path(model.evidence_record_path).exists()


def test_non_windows_default_durability_fails_closed(tmp_path, monkeypatch):
    model = path_model(tmp_path)
    make_parent_dirs(model)
    native = FakeNativeAdapter(model)
    monkeypatch.setattr(publisher.sys, "platform", "linux")

    result = publisher.publish_record_create_new(
        raw_record_path=model.evidence_record_path,
        canonical_bytes=b"{}",
        native_adapter=native,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
    )

    assert result.classification == publisher.AUTHORITY_B_RECORD_INVALID
    assert result.durability_result["failure_code"] == durable_schema.ADAPTER_ABSENT


@pytest.mark.parametrize(
    "record_mutator, expected_failure",
    (
        (
            lambda record: record.__setitem__("schema", "wrong"),
            "RECORD_VALIDATION_FAILED",
        ),
        (
            lambda record: record.pop("evidence_body"),
            "RECORD_VALIDATION_FAILED",
        ),
        (
            lambda record: record["body_identity"].__setitem__("body_sha256", "f" * 64),
            "RECORD_VALIDATION_FAILED",
        ),
        (
            lambda record: record.__setitem__("accepted_invocation_head", "0" * 40),
            "RECORD_VALIDATION_FAILED",
        ),
        (
            lambda record: record.__setitem__("whole_record_sha256", "f" * 64),
            "RECORD_VALIDATION_FAILED",
        ),
    ),
)
def test_validation_rejects_malformed_stored_records(
    tmp_path, record_mutator, expected_failure
):
    model = path_model(tmp_path)
    helper_result, record, _payload = build_record(model)
    record_mutator(record)
    payload = publisher.canonical_record_bytes(record)
    native = FakeNativeAdapter(model)

    result = publisher.validate_published_record(
        raw_record_path=model.evidence_record_path,
        expected_canonical_bytes=payload,
        expected_helper_body_identity=helper_result.body_identity,
        expected_accepted_invocation_head=HEAD,
        native_adapter=native,
        path_model=model,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
        read_bytes_function=lambda path: payload,
    )

    assert result.accepted is False
    assert result.failure_code == expected_failure


@pytest.mark.parametrize(
    "payload, expected, failure",
    (
        (b'{"a":1,"a":2}', b'{"a":1,"a":2}', "RECORD_VALIDATION_FAILED"),
        (b"not-json", b"not-json", "RECORD_VALIDATION_FAILED"),
        (b"{}", b'{"expected":true}', "RECORD_STORED_BYTE_MISMATCH"),
    ),
)
def test_validation_parse_and_byte_failures(tmp_path, payload, expected, failure):
    model = path_model(tmp_path)
    helper_result = helper_result_for(model)
    native = FakeNativeAdapter(model)

    result = publisher.validate_published_record(
        raw_record_path=model.evidence_record_path,
        expected_canonical_bytes=expected,
        expected_helper_body_identity=helper_result.body_identity,
        expected_accepted_invocation_head=HEAD,
        native_adapter=native,
        path_model=model,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
        read_bytes_function=lambda path: payload,
    )

    assert result.accepted is False
    assert result.failure_code == failure


def test_validation_read_failure_path_mismatch_and_canonical_input_present(tmp_path):
    model = path_model(tmp_path)
    helper_result, _record, payload = build_record(model)
    native = FakeNativeAdapter(model)

    read_failure = publisher.validate_published_record(
        raw_record_path=model.evidence_record_path,
        expected_canonical_bytes=payload,
        expected_helper_body_identity=helper_result.body_identity,
        expected_accepted_invocation_head=HEAD,
        native_adapter=native,
        path_model=model,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
        read_bytes_function=lambda path: (_ for _ in ()).throw(OSError("read failed")),
    )
    path_mismatch = publisher.validate_published_record(
        raw_record_path=model.evidence_record_path + ".wrong",
        expected_canonical_bytes=payload,
        expected_helper_body_identity=helper_result.body_identity,
        expected_accepted_invocation_head=HEAD,
        native_adapter=native,
        path_model=model,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
    )
    native.files.add(model.canonical_input_path)
    canonical_input_present = publisher.validate_published_record(
        raw_record_path=model.evidence_record_path,
        expected_canonical_bytes=payload,
        expected_helper_body_identity=helper_result.body_identity,
        expected_accepted_invocation_head=HEAD,
        native_adapter=native,
        path_model=model,
        expected_raw_record_path=model.evidence_record_path,
        allow_test_path_model=True,
        read_bytes_function=lambda path: payload,
    )

    assert read_failure.failure_code == "RECORD_REREAD_FAILED"
    assert path_mismatch.failure_code == "RECORD_PATH_REJECTED"
    assert canonical_input_present.failure_code == "CANONICAL_INPUT_PATH_PRESENT"


def test_source_terms_pin_authority_b_publication_boundary():
    source = Path(publisher.__file__).read_text(encoding="utf-8")
    assert source.count('open(raw_record_path, "xb")') == 1
    assert "durable_evidence_primary_writer_v0_3" not in source
    assert "canonical_json_bytes" not in source
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
