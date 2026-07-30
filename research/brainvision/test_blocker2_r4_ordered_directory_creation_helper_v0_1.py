from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from datetime import timezone
from datetime import timedelta
import errno
from pathlib import Path
import subprocess
import sys

import pytest

import blocker2_r4_ordered_directory_creation_helper_v0_1 as helper
import validate_windows_same_volume_no_replace_promotion_v0_1 as validation


HEAD = "8970e83370627afb3e8fee296ceb4b6d0fd2b575"
GOVERNED_PREFIX = r"C:\TORMENT\brainvision_authoritative_inputs"
TEST_ROOT = r"C:\TORMENT_R4_TEST"


def path_model_from_raw_root(raw_root: str) -> helper.PathModel:
    c1 = raw_root + r"\brainvision_authoritative_inputs_test"
    c2 = c1 + r"\blocker2_s3b_v0_3"
    c3 = c2 + r"\r4_prepare_paths"
    return helper.PathModel(
        required_root=raw_root,
        components=(c1, c2, c3),
        evidence_record_path=(
            c3 + r"\r4_prepare_paths_path_creation_evidence_record_v0_1.canonical.json"
        ),
        canonical_input_path=(
            c3 + r"\r4_prepare_paths_authorization_input_v0_1.canonical.json"
        ),
    )


TEST_PATH_MODEL = path_model_from_raw_root(TEST_ROOT)
COMPONENT_1, COMPONENT_2, COMPONENT_3 = TEST_PATH_MODEL.components


def active_authority() -> helper.AuthorityAssertions:
    return helper.AuthorityAssertions(
        window_open=True,
        authority_a_active=True,
        authority_b_active=True,
        authority_c_active=False,
        authority_d_active=False,
        authority_e_active=False,
    )


def clean_repo(**overrides) -> helper.RepositoryState:
    values = {
        "branch": "main",
        "head": HEAD,
        "origin_main": HEAD,
        "index_lock_present": False,
        "staged_changes": (),
        "unstaged_tracked_changes": (),
        "unmerged_entries": (),
        "untracked_entries": (helper.KNOWN_INERT_UNTRACKED_DRAFT,),
    }
    values.update(overrides)
    return helper.RepositoryState(**values)


def identity(index: int, *, volume: int = 101) -> helper.ObjectIdentity:
    return helper.ObjectIdentity(
        volume_serial_number=volume,
        file_index_high=0,
        file_index_low=index,
    )


class FakeAdapter:
    def __init__(self, *, path_model: helper.PathModel = TEST_PATH_MODEL):
        self.path_model = path_model
        self.identities = {path_model.required_root: identity(1)}
        self.files = set()
        self.reparse = set()
        self.open_failures = {}
        self.open_exceptions = {}
        self.absence_exceptions = {}
        self.absence_overrides = {}
        self.open_calls = []
        self.absence_calls = []
        self.closed_paths = []
        self.profile_overrides = {}
        self.create_calls = []
        self.cleanup_calls = []
        self._next_identity = 10
        self.on_before_create = None
        self.on_after_create = None

    def add_dir(self, raw_path: str) -> None:
        self._next_identity += 1
        self.identities[raw_path] = identity(self._next_identity)

    def add_file(self, raw_path: str) -> None:
        self.files.add(raw_path)

    def add_reparse(self, raw_path: str) -> None:
        self.identities[raw_path] = identity(900 + len(self.reparse))
        self.reparse.add(raw_path)

    def change_identity(self, raw_path: str) -> None:
        self._next_identity += 1
        self.identities[raw_path] = identity(self._next_identity)

    def open_directory(self, raw_path: str) -> helper.OpenDirectoryResult:
        self.open_calls.append(raw_path)
        exceptions = self.open_exceptions.get(raw_path)
        if exceptions:
            raise exceptions.pop(0)
        failures = self.open_failures.get(raw_path)
        if failures:
            return helper.OpenDirectoryResult(opened=False, error=failures.pop(0))
        if raw_path in self.identities:
            return helper.OpenDirectoryResult(
                opened=True,
                handle=helper.DirectoryHandle(
                    self._handle_evidence(raw_path),
                    close_callback=lambda path=raw_path: self.closed_paths.append(path),
                ),
            )
        if raw_path in self.files:
            return helper.OpenDirectoryResult(
                opened=True,
                handle=helper.DirectoryHandle(
                    self._handle_evidence(raw_path, is_directory=False),
                    close_callback=lambda path=raw_path: self.closed_paths.append(path),
                ),
            )
        return helper.OpenDirectoryResult(
            opened=False,
            error=helper.NativeError(
                validation.ERROR_FILE_NOT_FOUND,
                "ERROR_FILE_NOT_FOUND",
                "missing",
            ),
        )

    def check_absent(
        self,
        raw_path: str,
        *,
        allow_missing_ancestor: bool = False,
    ) -> helper.AbsenceResult:
        self.absence_calls.append(raw_path)
        exceptions = self.absence_exceptions.get(raw_path)
        if exceptions:
            raise exceptions.pop(0)
        override = self.absence_overrides.get(raw_path)
        if override is not None:
            return override
        if raw_path in self.identities:
            return helper.AbsenceResult(
                False,
                "handle_opened_target_pre_exists",
                pre_existing_kind="directory",
            )
        if raw_path in self.files:
            return helper.AbsenceResult(
                False,
                "handle_opened_target_pre_exists",
                pre_existing_kind="file",
            )
        parent = parent_of(raw_path)
        if parent not in self.identities:
            if allow_missing_ancestor:
                return helper.AbsenceResult(
                    True,
                    "ancestor_absent",
                    validation.ERROR_PATH_NOT_FOUND,
                    "ERROR_PATH_NOT_FOUND",
                )
            return helper.AbsenceResult(
                False,
                "parent_or_ancestor_absent",
                validation.ERROR_PATH_NOT_FOUND,
                "ERROR_PATH_NOT_FOUND",
            )
        return helper.AbsenceResult(
            True,
            "final_child_absent",
            validation.ERROR_FILE_NOT_FOUND,
            "ERROR_FILE_NOT_FOUND",
        )

    def mkdir(self, raw_path: str) -> None:
        self.create_calls.append(raw_path)
        if self.on_before_create is not None:
            self.on_before_create(raw_path)
        if raw_path in self.files or raw_path in self.identities:
            raise FileExistsError(errno.EEXIST, "exists", raw_path)
        parent = parent_of(raw_path)
        if parent not in self.identities:
            raise FileNotFoundError(errno.ENOENT, "missing parent", raw_path)
        self.add_dir(raw_path)
        if self.on_after_create is not None:
            self.on_after_create(raw_path)

    def _handle_evidence(
        self,
        raw_path: str,
        *,
        is_directory: bool = True,
    ) -> helper.DirectoryHandleEvidence:
        ident = self.identities.get(raw_path, identity(777))
        profile = self.profile_overrides.get(
            raw_path,
            helper.VolumeProfile(
                drive_type=validation.DRIVE_FIXED,
                filesystem_name="NTFS",
                volume_serial_number=ident.volume_serial_number,
            ),
        )
        return helper.DirectoryHandleEvidence(
            raw_path=raw_path,
            identity=ident,
            volume_profile=profile,
            is_directory=is_directory,
            is_reparse_point=raw_path in self.reparse,
            attributes_source="synthetic",
            native_handle_source="synthetic",
            share_limitations="synthetic handle does not prevent rename/delete",
        )


def parent_of(raw_path: str) -> str:
    return raw_path.rsplit("\\", 1)[0]


def run_helper(
    adapter: FakeAdapter,
    *,
    authority: helper.AuthorityAssertions | None = None,
    repo_reader=None,
    creation_primitive=None,
    utc_clock=None,
    monotonic_clock=None,
    path_model: helper.PathModel = TEST_PATH_MODEL,
    allow_test_path_model: bool = True,
):
    return helper.execute_ordered_directory_creation(
        authority=authority or active_authority(),
        accepted_invocation_head=HEAD,
        path_model=path_model,
        repository_reader=repo_reader or (lambda: clean_repo()),
        native_adapter=adapter,
        creation_primitive=creation_primitive or adapter.mkdir,
        utc_clock=utc_clock or (lambda: "2026-07-29T23:52:00.000000Z"),
        monotonic_clock=monotonic_clock or monotonic_counter(),
        allow_test_path_model=allow_test_path_model,
    )


def monotonic_counter(start: int = 1000, step: int = 10):
    values = {"current": start - step}

    def next_value() -> int:
        values["current"] += step
        return values["current"]

    return next_value


def test_canonical_body_identity_is_deterministic_and_external_only():
    evidence = {"z": [3, 2, 1], "a": {"b": True}}
    first = helper.body_identity_for_evidence_body(evidence)
    second = helper.body_identity_for_evidence_body({"a": {"b": True}, "z": [3, 2, 1]})

    assert helper.canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert first == second
    assert first["body_byte_count"] == len(helper.canonical_json_bytes(evidence))
    assert first["body_sha256"]
    assert first["whole_record_identity_stored_inside_record"] is False


def test_successful_strict_three_component_sequence_returns_unpublished_candidate():
    adapter = FakeAdapter()

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION
    assert result.classification_kind == helper.CLASSIFICATION_DERIVED_NON_TERMINAL
    assert result.terminal is False
    assert result.opportunity_consumed is True
    assert result.mutation_succeeded_count == 3
    assert adapter.create_calls == list(TEST_PATH_MODEL.components)
    assert result.evidence_body["publication_boundary"]["publishes_evidence_record"] is False
    assert "whole_record_sha256" not in result.body_identity
    for ordinal, operation in enumerate(result.evidence_body["operations"], start=1):
        assert operation["committed_required"]["ordinal"] == ordinal
        assert operation["committed_required"]["target_presence_after"] == helper.TRI_TRUE
        assert operation["committed_required"]["operator_process_result"] == (
            "os.mkdir_returned_success"
        )


def test_successful_one_component_evidence_is_exactly_one_call_for_ordinal_one():
    adapter = FakeAdapter()

    result = run_helper(adapter)

    first = result.evidence_body["operations"][0]
    assert adapter.create_calls[0] == COMPONENT_1
    assert first["derived_implementation"]["creation_call"]["attempt_count_for_ordinal"] == 1
    assert first["derived_implementation"]["creation_call"]["raw_target_passed_exactly"] == (
        COMPONENT_1
    )


def test_utc_and_monotonic_operation_timestamps_are_separate_and_ordered():
    adapter = FakeAdapter()
    utc_values = iter(
        [
            "2026-07-29T23:52:00.000000Z",
            "2026-07-29T23:52:01.000000Z",
            "2026-07-29T23:52:02.000000Z",
        ]
    )
    monotonic = monotonic_counter(start=100, step=7)

    result = run_helper(
        adapter,
        utc_clock=lambda: next(utc_values),
        monotonic_clock=monotonic,
    )

    operations = result.evidence_body["operations"]
    assert [op["committed_required"]["operation_timestamp_utc"] for op in operations] == [
        "2026-07-29T23:52:00.000000Z",
        "2026-07-29T23:52:01.000000Z",
        "2026-07-29T23:52:02.000000Z",
    ]
    assert [op["committed_required"]["operation_monotonic_ns"] for op in operations] == [
        100,
        107,
        114,
    ]


def test_timezone_aware_injected_datetime_is_canonicalized_to_utc_z():
    adapter = FakeAdapter()
    source_time = datetime(
        2026,
        7,
        29,
        18,
        52,
        0,
        123456,
        tzinfo=timezone(timedelta(hours=-5)),
    )

    result = run_helper(
        adapter,
        utc_clock=lambda: source_time,
        monotonic_clock=monotonic_counter(),
    )

    assert result.evidence_body["operations"][0]["committed_required"][
        "operation_timestamp_utc"
    ] == "2026-07-29T23:52:00.123456Z"


def test_invalid_utc_clock_value_fails_closed_before_contact():
    adapter = FakeAdapter()

    result = run_helper(adapter, utc_clock=lambda: "2026-07-29 23:52:00")

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "unexpected_exception_before_contact"
    assert result.evidence_body["aggregate"]["failure_diagnostic"]["phase"] == "clock"
    assert adapter.create_calls == []


def test_deterministic_clocks_produce_deterministic_canonical_identity():
    first = run_helper(FakeAdapter())
    second = run_helper(FakeAdapter())

    assert first.body_identity == second.body_identity


@pytest.mark.parametrize(
    "authority",
    [
        helper.AuthorityAssertions(False, True, True, False, False, False),
        helper.AuthorityAssertions(True, False, True, False, False, False),
        helper.AuthorityAssertions(True, True, False, False, False, False),
        helper.AuthorityAssertions(True, True, True, True, False, False),
    ],
)
def test_authority_mismatch_fails_before_contact_without_consumption(authority):
    adapter = FakeAdapter()

    result = run_helper(adapter, authority=authority)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.opportunity_consumed is False
    assert result.contact_started is False
    assert adapter.create_calls == []


@pytest.mark.parametrize(
    "bad_path",
    [
        r"C:\TORMENT\bad ",
        r"C:\TORMENT\bad.",
        r"C:/TORMENT/bad",
        r"\\server\share\bad",
        r"\\?\C:\TORMENT\bad",
        r"C:relative\bad",
        r"C:\TORMENT\.\bad",
        r"C:\TORMENT\bad:stream",
        r"C:\TORMENT\bad*",
        r"C:\TORMENT\bad<",
    ],
)
def test_raw_path_validation_rejects_unsafe_forms_before_contact(bad_path):
    path_model = helper.PathModel(
        required_root=TEST_ROOT,
        components=(bad_path, COMPONENT_2, COMPONENT_3),
        evidence_record_path=TEST_PATH_MODEL.evidence_record_path,
        canonical_input_path=TEST_PATH_MODEL.canonical_input_path,
    )
    adapter = FakeAdapter(path_model=path_model)

    result = run_helper(adapter, path_model=path_model, allow_test_path_model=True)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.committed_detail_label == helper.DETAIL_PATH_MISMATCH
    assert adapter.create_calls == []


def test_governed_mode_requires_exact_uppercase_c_drive_literal():
    assert (
        helper._validate_raw_path_text(r"D:\TORMENT\bad", allow_test_path_model=False)
        == "drive_not_exact_literal_C"
    )
    assert (
        helper._validate_raw_path_text(r"c:\TORMENT\bad", allow_test_path_model=False)
        == "drive_not_exact_literal_C"
    )


def test_missing_parent_fails_without_contact():
    adapter = FakeAdapter()
    adapter.identities.pop(TEST_PATH_MODEL.required_root)

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.committed_detail_label == helper.DETAIL_PARENT_ABSENT
    assert adapter.create_calls == []


@pytest.mark.parametrize("kind", ["directory", "file", "reparse"])
def test_pre_existing_target_variants_fail_before_create(kind):
    adapter = FakeAdapter()
    if kind == "directory":
        adapter.add_dir(COMPONENT_1)
    elif kind == "file":
        adapter.add_file(COMPONENT_1)
    else:
        adapter.add_reparse(COMPONENT_1)

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.committed_detail_label == helper.DETAIL_CHILD_PRE_EXISTS
    assert adapter.create_calls == []


def test_parent_reparse_fails_closed_before_create():
    adapter = FakeAdapter()
    adapter.add_reparse(TEST_PATH_MODEL.required_root)

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.committed_detail_label == helper.DETAIL_REPARSE_OR_ALIAS
    assert adapter.create_calls == []


@pytest.mark.parametrize(
    "absence",
    [
        helper.AbsenceResult(
            False,
            "indeterminate_absence",
            validation.ERROR_ACCESS_DENIED,
            "ERROR_ACCESS_DENIED",
        ),
        helper.AbsenceResult(
            False,
            "indeterminate_absence",
            validation.ERROR_SHARING_VIOLATION,
            "ERROR_SHARING_VIOLATION",
        ),
        helper.AbsenceResult(
            False,
            "indeterminate_absence",
            validation.ERROR_INVALID_NAME,
            "ERROR_INVALID_NAME",
        ),
    ],
)
def test_target_inaccessible_or_indeterminate_absence_fails_before_contact(absence):
    adapter = FakeAdapter()
    adapter.absence_overrides[COMPONENT_1] = absence

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.opportunity_consumed is False
    assert adapter.create_calls == []


def test_file_exists_after_positive_absence_is_partial_and_not_success():
    adapter = FakeAdapter()

    def concurrent_create(raw_path: str) -> None:
        adapter.add_dir(raw_path)

    adapter.on_before_create = concurrent_create

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.committed_detail_label == helper.DETAIL_CHILD_PRE_EXISTS
    assert result.opportunity_consumed is True
    assert adapter.create_calls == [COMPONENT_1]


def test_other_oserror_followed_by_target_presence_remains_failure():
    adapter = FakeAdapter()

    def failing_create(raw_path: str) -> None:
        adapter.create_calls.append(raw_path)
        adapter.add_dir(raw_path)
        raise OSError(errno.EACCES, "synthetic access failure")

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=TEST_PATH_MODEL,
        repository_reader=lambda: clean_repo(),
        native_adapter=adapter,
        creation_primitive=failing_create,
        utc_clock=lambda: "2026-07-29T23:52:00.000000Z",
        monotonic_clock=monotonic_counter(),
        allow_test_path_model=True,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "create_call_failed_no_success_conversion"
    assert result.mutation_succeeded_count == 0


def test_post_create_identity_failure_is_partial_terminal():
    adapter = FakeAdapter()
    adapter.open_failures[COMPONENT_1] = [
        helper.NativeError(None, "NATIVE_IDENTITY_FAILED", "identity unavailable")
    ]

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "post_create_child_identity_unavailable"
    assert result.mutation_succeeded_count == 1


def test_parent_identity_drift_after_create_fails_partial():
    adapter = FakeAdapter()

    def drift_parent(raw_path: str) -> None:
        adapter.change_identity(TEST_PATH_MODEL.required_root)

    adapter.on_after_create = drift_parent

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "parent_identity_drift"
    assert result.mutation_succeeded_count == 1


def test_unexpected_intermediate_creation_falsifier_fails_partial():
    adapter = FakeAdapter()

    def recursive_side_effect(_raw_path: str) -> None:
        adapter.add_dir(COMPONENT_2)

    adapter.on_after_create = recursive_side_effect

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.committed_detail_label == helper.DETAIL_UNEXPECTED_INTERMEDIATE
    assert result.derived_subreason == "later_component_not_absent_post_ordinal_2"


def test_chained_identity_mismatch_fails_before_next_create_after_contact():
    adapter = FakeAdapter()

    repo_calls = 0

    def repo_reader() -> helper.RepositoryState:
        nonlocal repo_calls
        repo_calls += 1
        if repo_calls == 2:
            adapter.change_identity(COMPONENT_1)
        return clean_repo()

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=TEST_PATH_MODEL,
        repository_reader=repo_reader,
        native_adapter=adapter,
        creation_primitive=adapter.mkdir,
        utc_clock=lambda: "2026-07-29T23:52:00.000000Z",
        monotonic_clock=monotonic_counter(),
        allow_test_path_model=True,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "chained_identity_mismatch"
    assert adapter.create_calls == [COMPONENT_1]


def test_repository_drift_before_contact_does_not_consume():
    adapter = FakeAdapter()

    result = run_helper(adapter, repo_reader=lambda: clean_repo(head="bad"))

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "head_drift"
    assert result.opportunity_consumed is False
    assert adapter.create_calls == []


def test_repository_drift_after_contact_is_partial_terminal():
    adapter = FakeAdapter()
    states = [clean_repo(), clean_repo(index_lock_present=True)]

    result = run_helper(adapter, repo_reader=lambda: states.pop(0))

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "index_lock_present"
    assert result.mutation_succeeded_count == 1


def test_unexpected_untracked_state_fails_before_contact():
    adapter = FakeAdapter()

    result = run_helper(
        adapter,
        repo_reader=lambda: clean_repo(untracked_entries=("unexpected.txt",)),
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "unexpected_untracked_state"


def test_operator_interruption_before_contact_does_not_consume():
    adapter = FakeAdapter()

    def interrupt():
        raise KeyboardInterrupt()

    result = run_helper(adapter, repo_reader=interrupt)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "operator_interruption_before_contact"
    assert result.opportunity_consumed is False


def test_operator_interruption_after_contact_is_partial():
    adapter = FakeAdapter()

    def interrupting_create(_raw_path: str) -> None:
        adapter.create_calls.append(_raw_path)
        raise KeyboardInterrupt()

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=TEST_PATH_MODEL,
        repository_reader=lambda: clean_repo(),
        native_adapter=adapter,
        creation_primitive=interrupting_create,
        utc_clock=lambda: "2026-07-29T23:52:00.000000Z",
        monotonic_clock=monotonic_counter(),
        allow_test_path_model=True,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "operator_interruption_after_contact"
    assert result.opportunity_consumed is True


def test_no_recursive_pathlib_exist_ok_retry_or_cleanup_source_terms():
    source = Path(helper.__file__).read_text()

    assert "Path.mkdir" not in source
    assert source.count("os.mkdir(") == 1
    assert "parents=True" not in source
    assert "exist_ok=True" not in source
    assert "rmtree" not in source
    assert "remove(" not in source
    assert "unlink(" not in source


def test_derived_subreason_is_labelled_in_evidence_body():
    adapter = FakeAdapter()
    adapter.absence_overrides[COMPONENT_1] = helper.AbsenceResult(
        False,
        "indeterminate_absence",
        validation.ERROR_ACCESS_DENIED,
        "ERROR_ACCESS_DENIED",
    )

    result = run_helper(adapter)

    subreason = result.evidence_body["aggregate"]["derived_subreason"]
    assert subreason["kind"] == "DERIVED_IMPLEMENTATION_SUBREASON"
    assert subreason["value"] == "target_not_positively_absent"


def test_default_adapter_fails_closed_on_non_windows(monkeypatch):
    monkeypatch.setattr(helper.validation, "_is_windows", lambda: False)

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=TEST_PATH_MODEL,
        repository_reader=lambda: clean_repo(),
        utc_clock=lambda: "2026-07-29T23:52:00.000000Z",
        monotonic_clock=monotonic_counter(),
        allow_test_path_model=True,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "parent_open_failed"


def path_model_variant(
    *,
    required_root: str = TEST_ROOT,
    component_1: str = COMPONENT_1,
    component_2: str = COMPONENT_2,
    component_3: str = COMPONENT_3,
    evidence_record_path: str = TEST_PATH_MODEL.evidence_record_path,
    canonical_input_path: str = TEST_PATH_MODEL.canonical_input_path,
) -> helper.PathModel:
    return helper.PathModel(
        required_root=required_root,
        components=(component_1, component_2, component_3),
        evidence_record_path=evidence_record_path,
        canonical_input_path=canonical_input_path,
    )


@pytest.mark.parametrize(
    "path_model",
    [
        path_model_variant(component_1=helper.GOVERNED_COMPONENT_1),
        path_model_variant(component_2=helper.GOVERNED_COMPONENT_2),
        path_model_variant(component_3=helper.GOVERNED_COMPONENT_3),
        path_model_variant(component_1=r"c:\torment\BrainVision_Authoritative_Inputs"),
        path_model_variant(component_1=helper.GOVERNED_COMPONENT_1 + "\\"),
        path_model_variant(
            evidence_record_path=helper.GOVERNED_COMPONENT_1 + r"\record.json"
        ),
        path_model_variant(
            canonical_input_path=helper.GOVERNED_COMPONENT_1 + r"\input.json"
        ),
    ],
)
def test_test_mode_denies_governed_prefix_before_any_seam_contact(path_model):
    adapter = FakeAdapter(path_model=path_model)

    def forbidden_repo_reader():
        raise AssertionError("repository reader must not be contacted")

    def forbidden_create(_raw_path: str) -> None:
        raise AssertionError("creation primitive must not be contacted")

    def forbidden_utc_clock():
        raise AssertionError("UTC clock must not be contacted")

    def forbidden_monotonic_clock():
        raise AssertionError("monotonic clock must not be contacted")

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=path_model,
        repository_reader=forbidden_repo_reader,
        native_adapter=adapter,
        creation_primitive=forbidden_create,
        utc_clock=forbidden_utc_clock,
        monotonic_clock=forbidden_monotonic_clock,
        allow_test_path_model=True,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.committed_detail_label == helper.DETAIL_PATH_MISMATCH
    assert result.derived_subreason == "governed_path_forbidden_in_test_mode"
    assert result.contact_started is False
    assert result.opportunity_consumed is False
    assert result.mutation_succeeded_count == 0
    assert adapter.open_calls == []
    assert adapter.absence_calls == []
    assert adapter.create_calls == []


def test_unrelated_scratch_path_remains_allowed_in_test_mode():
    adapter = FakeAdapter()

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION
    assert adapter.create_calls == list(TEST_PATH_MODEL.components)


@pytest.mark.parametrize(
    "authority",
    [
        helper.AuthorityAssertions(False, True, True, False, False, False),
        helper.AuthorityAssertions(True, False, True, False, False, False),
        helper.AuthorityAssertions(True, True, False, False, False, False),
        helper.AuthorityAssertions(True, True, True, True, False, False),
        helper.AuthorityAssertions(True, True, True, False, True, False),
        helper.AuthorityAssertions(True, True, True, False, False, True),
    ],
)
def test_authority_state_is_returned_honestly_for_each_gate_mismatch(authority):
    adapter = FakeAdapter()

    result = run_helper(adapter, authority=authority)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.authority_active is False
    assert result.required_authority_gate_satisfied is False
    assert result.authority_assertions_observed == asdict(authority)
    assert result.evidence_body["authority_state"]["authority_assertions_observed"] == (
        asdict(authority)
    )


def test_not_started_requires_positive_absence_proof_for_required_paths():
    adapter = FakeAdapter()

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=TEST_PATH_MODEL,
        native_adapter=adapter,
        allow_test_path_model=True,
        prove_not_started_absence=True,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_NOT_STARTED
    assert result.classification_kind == helper.CLASSIFICATION_COMMITTED_TERMINAL
    assert result.terminal is True
    proof = result.evidence_body["aggregate"]["not_started_absence_checks"]
    assert [item["label"] for item in proof] == [
        "component_1",
        "component_2",
        "component_3",
        "evidence_record_path",
    ]
    assert result.evidence_body["aggregate"]["canonical_input_absence_observation"][
        "required_for_not_started"
    ] is False


def test_not_started_absence_indeterminate_remains_pre_contact_abort():
    adapter = FakeAdapter()
    adapter.absence_overrides[COMPONENT_2] = helper.AbsenceResult(
        False,
        "indeterminate_absence",
        validation.ERROR_ACCESS_DENIED,
        "ERROR_ACCESS_DENIED",
    )

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=TEST_PATH_MODEL,
        native_adapter=adapter,
        allow_test_path_model=True,
        prove_not_started_absence=True,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "not_started_absence_not_proven"


def test_evidence_record_preexisting_prevents_not_started_label():
    adapter = FakeAdapter()
    adapter.add_file(TEST_PATH_MODEL.evidence_record_path)

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=TEST_PATH_MODEL,
        native_adapter=adapter,
        allow_test_path_model=True,
        prove_not_started_absence=True,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.committed_detail_label == helper.DETAIL_CHILD_PRE_EXISTS


def test_success_evidence_splits_intermediate_and_sibling_claims():
    adapter = FakeAdapter()

    result = run_helper(adapter)

    first = result.evidence_body["operations"][0]["committed_required"]
    assert first["unexpected_intermediate_creation_check"] == "PASS"
    assert first["unexpected_intermediate_creation_method"] == (
        "later_component_absence_falsifier_and_chained_identity"
    )
    assert first["unexpected_sibling_creation_check"] == "NOT_PERFORMED"
    assert first["unexpected_sibling_creation_check_class"] == (
        "OPTIONAL_DIAGNOSTIC_NOT_OBSERVED"
    )
    assert "unexpected_sibling_or_intermediate_creation_check" not in first


def test_default_seams_are_identified_as_authoritative_without_contact():
    result = helper.execute_ordered_directory_creation(
        authority=helper.AuthorityAssertions(False, True, True, False, False, False),
        accepted_invocation_head=HEAD,
    )

    seams = result.evidence_body["execution_seams"]
    assert result.execution_mode == helper.EXECUTION_MODE_AUTHORITATIVE_DEFAULT
    assert seams["execution_mode"] == helper.EXECUTION_MODE_AUTHORITATIVE_DEFAULT
    assert seams["custom_seams_present"] is False
    assert seams["native_adapter_class"] == "Win32DirectoryAdapter"
    assert seams["repository_reader_qualname"] == "read_repository_state"
    assert seams["creation_primitive_qualname"] == "_default_creation_primitive"
    assert seams["utc_clock_qualname"] == "_default_utc_clock"
    assert seams["monotonic_clock_qualname"] == "_default_monotonic_clock"


@pytest.mark.parametrize(
    "attribute_name, replacement, expected_key",
    [
        (
            "_default_creation_primitive",
            lambda _raw_path: (_ for _ in ()).throw(
                AssertionError("creation primitive must not run")
            ),
            "creation_primitive_qualname",
        ),
        (
            "read_repository_state",
            lambda _root=".": (_ for _ in ()).throw(
                AssertionError("repository reader must not run")
            ),
            "repository_reader_qualname",
        ),
        (
            "_default_utc_clock",
            lambda: (_ for _ in ()).throw(AssertionError("UTC clock must not run")),
            "utc_clock_qualname",
        ),
        (
            "_default_monotonic_clock",
            lambda: (_ for _ in ()).throw(
                AssertionError("monotonic clock must not run")
            ),
            "monotonic_clock_qualname",
        ),
    ],
)
def test_monkeypatched_authoritative_default_callable_seams_are_rejected_before_contact(
    monkeypatch,
    attribute_name,
    replacement,
    expected_key,
):
    monkeypatch.setattr(helper, attribute_name, replacement)

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.execution_mode == helper.EXECUTION_MODE_UNSUPPORTED_CUSTOM
    assert result.derived_subreason == "authoritative_default_seam_identity_mismatch"
    assert expected_key in result.evidence_body["aggregate"]["failure_diagnostic"][
        "mismatched_seams"
    ]


def test_monkeypatched_authoritative_default_adapter_class_is_rejected_before_contact(
    monkeypatch,
):
    class PoisonAdapter:
        def open_directory(self, _raw_path):
            raise AssertionError("adapter must not be contacted")

    monkeypatch.setattr(helper, "Win32DirectoryAdapter", PoisonAdapter)

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.execution_mode == helper.EXECUTION_MODE_UNSUPPORTED_CUSTOM
    assert result.derived_subreason == "authoritative_default_seam_identity_mismatch"
    assert "native_adapter_class" in result.evidence_body["aggregate"][
        "failure_diagnostic"
    ]["mismatched_seams"]


@pytest.mark.parametrize(
    "kwargs, expected_flag",
    [
        ({"creation_primitive": lambda _raw: None}, "creation_primitive"),
        ({"native_adapter": FakeAdapter()}, "native_adapter"),
        ({"repository_reader": lambda: clean_repo()}, "repository_reader"),
        ({"utc_clock": lambda: "2026-07-29T23:52:00.000000Z"}, "utc_clock"),
        ({"monotonic_clock": lambda: 123}, "monotonic_clock"),
    ],
)
def test_custom_seams_are_identified_in_test_mode_without_contact(kwargs, expected_flag):
    result = helper.execute_ordered_directory_creation(
        authority=helper.AuthorityAssertions(False, True, True, False, False, False),
        accepted_invocation_head=HEAD,
        path_model=TEST_PATH_MODEL,
        allow_test_path_model=True,
        **kwargs,
    )

    seams = result.evidence_body["execution_seams"]
    assert result.execution_mode == helper.EXECUTION_MODE_TEST_OR_CUSTOM
    assert seams["execution_mode"] == helper.EXECUTION_MODE_TEST_OR_CUSTOM
    assert seams["seam_injection"][expected_flag] is True
    assert seams["custom_seams_present"] is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"creation_primitive": lambda _raw: None},
        {"native_adapter": FakeAdapter(path_model=helper.GOVERNED_PATH_MODEL)},
        {"repository_reader": lambda: clean_repo()},
        {"utc_clock": lambda: "2026-07-29T23:52:00.000000Z"},
        {"monotonic_clock": lambda: 123},
    ],
)
def test_governed_path_with_custom_seam_fails_before_contact(kwargs):
    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        **kwargs,
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "custom_seam_forbidden_for_governed_path_model"
    assert result.execution_mode == helper.EXECUTION_MODE_UNSUPPORTED_CUSTOM
    if "native_adapter" in kwargs:
        assert kwargs["native_adapter"].open_calls == []


def test_success_closes_all_acquired_handles_once():
    adapter = FakeAdapter()

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION
    assert len(adapter.closed_paths) == 9


@pytest.mark.parametrize(
    "phase, configure, expected_contact, expected_mutations",
    [
        (
            "parent_open",
            lambda adapter: adapter.open_exceptions.setdefault(
                TEST_PATH_MODEL.required_root,
                [RuntimeError("parent open boom")],
            ),
            False,
            0,
        ),
        (
            "target_absence",
            lambda adapter: adapter.absence_exceptions.setdefault(
                COMPONENT_1,
                [RuntimeError("absence boom")],
            ),
            False,
            0,
        ),
        (
            "clock",
            lambda adapter: None,
            False,
            0,
        ),
        (
            "creation_primitive",
            lambda adapter: None,
            True,
            0,
        ),
        (
            "child_open",
            lambda adapter: adapter.open_exceptions.setdefault(
                COMPONENT_1,
                [RuntimeError("child open boom")],
            ),
            True,
            1,
        ),
        (
            "later_component_absence_post",
            lambda adapter: setattr(
                adapter,
                "on_after_create",
                lambda _raw: adapter.absence_exceptions.setdefault(
                    COMPONENT_2,
                    [RuntimeError("later absence boom")],
                ),
            ),
            True,
            1,
        ),
    ],
)
def test_unexpected_exceptions_return_structured_result_and_close_handles(
    phase,
    configure,
    expected_contact,
    expected_mutations,
):
    adapter = FakeAdapter()
    configure(adapter)

    def create(raw_path: str) -> None:
        if phase == "creation_primitive":
            adapter.create_calls.append(raw_path)
            raise RuntimeError("creation wrapper boom")
        adapter.mkdir(raw_path)

    result = run_helper(
        adapter,
        creation_primitive=create,
        utc_clock=(
            (lambda: (_ for _ in ()).throw(RuntimeError("clock boom")))
            if phase == "clock"
            else None
        ),
    )

    assert result.classification == (
        helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
        if expected_contact
        else helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    )
    assert result.derived_subreason == (
        "unexpected_exception_after_contact"
        if expected_contact
        else "unexpected_exception_before_contact"
    )
    assert result.contact_started is expected_contact
    assert result.opportunity_consumed is expected_contact
    assert result.mutation_succeeded_count == expected_mutations
    assert result.evidence_body["aggregate"]["failure_diagnostic"]["phase"] == phase
    assert adapter.create_calls[:1] == ([COMPONENT_1] if expected_contact else [])
    assert adapter.cleanup_calls == []


def test_parent_reopen_exception_after_contact_closes_existing_handles():
    adapter = FakeAdapter()
    original_open = adapter.open_directory
    root_opens = 0

    def open_with_parent_reopen_failure(raw_path: str):
        nonlocal root_opens
        if raw_path == TEST_PATH_MODEL.required_root:
            root_opens += 1
            if root_opens == 2:
                raise RuntimeError("parent reopen boom")
        return original_open(raw_path)

    adapter.open_directory = open_with_parent_reopen_failure

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "unexpected_exception_after_contact"
    assert result.evidence_body["aggregate"]["failure_diagnostic"]["phase"] == "parent_reopen"
    assert len(adapter.closed_paths) == 2


def test_repository_reader_exception_after_contact_is_structured_partial():
    adapter = FakeAdapter()
    calls = 0

    def repo_reader():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("repository recheck boom")
        return clean_repo()

    result = run_helper(adapter, repo_reader=repo_reader)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "unexpected_exception_after_contact"
    assert result.mutation_succeeded_count == 1
    assert result.evidence_body["aggregate"]["failure_diagnostic"]["phase"] == (
        "repository_pre_state"
    )


def test_body_identity_failure_after_success_becomes_partial_terminal(monkeypatch):
    adapter = FakeAdapter()

    def raise_identity(_evidence):
        raise RuntimeError("identity boom")

    monkeypatch.setattr(helper, "body_identity_for_evidence_body", raise_identity)

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "unexpected_exception_after_contact"
    assert result.mutation_succeeded_count == 3
    assert result.body_identity["identity_unavailable"] is True


class ExplodingEvidence:
    def __init__(self, raw_path: str, *, fail_attribute: str):
        self.raw_path = raw_path
        self._fail_attribute = fail_attribute

    @property
    def identity(self):
        if self._fail_attribute == "identity":
            raise RuntimeError("identity evidence boom")
        return identity(123)

    @property
    def volume_profile(self):
        if self._fail_attribute == "volume_profile":
            raise RuntimeError("volume profile boom")
        return helper.VolumeProfile(
            drive_type=validation.DRIVE_FIXED,
            filesystem_name="NTFS",
            volume_serial_number=123,
        )

    @property
    def is_directory(self):
        return True

    @property
    def is_reparse_point(self):
        return False

    def as_dict(self):
        return {"raw_path": self.raw_path, "exploding": self._fail_attribute}


def exploding_handle(adapter: FakeAdapter, raw_path: str, fail_attribute: str):
    return helper.OpenDirectoryResult(
        opened=True,
        handle=helper.DirectoryHandle(
            ExplodingEvidence(raw_path, fail_attribute=fail_attribute),
            close_callback=lambda path=raw_path: adapter.closed_paths.append(path),
        ),
    )


@pytest.mark.parametrize(
    "fail_attribute, expected_phase",
    [
        ("identity", "parent_open"),
        ("volume_profile", "parent_open"),
    ],
)
def test_parent_evidence_extraction_exceptions_are_structured_and_closed(
    fail_attribute,
    expected_phase,
):
    adapter = FakeAdapter()
    original_open = adapter.open_directory

    def open_with_exploding_parent(raw_path: str):
        if raw_path == TEST_PATH_MODEL.required_root:
            return exploding_handle(adapter, raw_path, fail_attribute)
        return original_open(raw_path)

    adapter.open_directory = open_with_exploding_parent

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "unexpected_exception_before_contact"
    assert result.evidence_body["aggregate"]["failure_diagnostic"]["phase"] == expected_phase
    assert adapter.closed_paths == [TEST_PATH_MODEL.required_root]


def test_child_evidence_extraction_exception_after_contact_is_structured_partial():
    adapter = FakeAdapter()
    original_open = adapter.open_directory

    def open_with_exploding_child(raw_path: str):
        if raw_path == COMPONENT_1 and raw_path in adapter.identities:
            return exploding_handle(adapter, raw_path, "identity")
        return original_open(raw_path)

    adapter.open_directory = open_with_exploding_child

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "unexpected_exception_after_contact"
    assert result.evidence_body["aggregate"]["failure_diagnostic"]["phase"] == (
        "child_profile_validation"
    )
    assert set(adapter.closed_paths) == {TEST_PATH_MODEL.required_root, COMPONENT_1}


def test_parent_post_evidence_exception_after_contact_closes_all_handles():
    adapter = FakeAdapter()
    original_open = adapter.open_directory
    root_opens = 0

    def open_with_exploding_parent_post(raw_path: str):
        nonlocal root_opens
        if raw_path == TEST_PATH_MODEL.required_root:
            root_opens += 1
            if root_opens == 2:
                return exploding_handle(adapter, raw_path, "identity")
        return original_open(raw_path)

    adapter.open_directory = open_with_exploding_parent_post

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == "unexpected_exception_after_contact"
    assert result.evidence_body["aggregate"]["failure_diagnostic"]["phase"] == "parent_reopen"
    assert len(adapter.closed_paths) == 3


@pytest.mark.parametrize(
    "repo_overrides, subreason",
    [
        ({"branch": "feature"}, "branch_drift"),
        ({"origin_main": "bad"}, "origin_main_drift"),
        ({"staged_changes": ("new.txt",)}, "staged_changes_present"),
        ({"unstaged_tracked_changes": ("changed.txt",)}, "unstaged_tracked_changes_present"),
        ({"unmerged_entries": ("100644 abc 1\tfile.txt",)}, "unmerged_entries_present"),
        ({"index_lock_present": True}, "index_lock_present"),
        ({"untracked_entries": ("unexpected.txt",)}, "unexpected_untracked_state"),
    ],
)
def test_repository_drift_variants_fail_before_contact(repo_overrides, subreason):
    adapter = FakeAdapter()

    result = run_helper(adapter, repo_reader=lambda: clean_repo(**repo_overrides))

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == subreason
    assert adapter.create_calls == []


def test_read_repository_state_parses_successful_git_output():
    outputs = {
        ("symbolic-ref", "--quiet", "--short", "HEAD"): "main\n",
        ("rev-parse", "HEAD"): HEAD + "\n",
        ("rev-parse", "refs/remotes/origin/main"): HEAD + "\n",
        ("diff", "--cached", "--name-only", "--no-ext-diff"): "staged.txt\n",
        ("ls-files", "--modified", "--deleted"): "modified.txt\n",
        ("ls-files", "-u"): "100644 abc 1\tconflict.txt\n",
        ("ls-files", "--others", "--exclude-standard"): "untracked.txt\n",
    }

    def runner(command, **kwargs):
        git_args = tuple(command[4:])
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=outputs[git_args],
            stderr="",
        )

    state = helper.read_repository_state(
        TEST_ROOT,
        git_runner=runner,
        index_lock_observer=lambda _path: (_ for _ in ()).throw(FileNotFoundError()),
    )

    assert state.branch == "main"
    assert state.head == HEAD
    assert state.origin_main == HEAD
    assert state.index_lock_present is False
    assert state.index_lock_state == helper.INDEX_LOCK_ABSENT
    assert state.staged_changes == ("staged.txt",)
    assert state.unstaged_tracked_changes == ("modified.txt",)
    assert state.unmerged_entries == ("100644 abc 1\tconflict.txt",)
    assert state.untracked_entries == ("untracked.txt",)


def test_read_repository_state_propagates_git_command_failure():
    def runner(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="git failed")

    with pytest.raises(subprocess.CalledProcessError):
        helper.read_repository_state(TEST_ROOT, git_runner=runner)


def successful_git_runner(command, **kwargs):
    outputs = {
        ("symbolic-ref", "--quiet", "--short", "HEAD"): "main\n",
        ("rev-parse", "HEAD"): HEAD + "\n",
        ("rev-parse", "refs/remotes/origin/main"): HEAD + "\n",
        ("diff", "--cached", "--name-only", "--no-ext-diff"): "",
        ("ls-files", "--modified", "--deleted"): "",
        ("ls-files", "-u"): "",
        ("ls-files", "--others", "--exclude-standard"): (
            helper.KNOWN_INERT_UNTRACKED_DRAFT + "\n"
        ),
    }
    return subprocess.CompletedProcess(
        command,
        0,
        stdout=outputs[tuple(command[4:])],
        stderr="",
    )


@pytest.mark.parametrize(
    "observer, state, present, error_expected",
    [
        (
            lambda _path: (_ for _ in ()).throw(FileNotFoundError()),
            helper.INDEX_LOCK_ABSENT,
            False,
            False,
        ),
        (lambda _path: object(), helper.INDEX_LOCK_PRESENT, True, False),
        (
            lambda _path: (_ for _ in ()).throw(PermissionError("denied")),
            helper.INDEX_LOCK_INDETERMINATE,
            False,
            True,
        ),
        (
            lambda _path: (_ for _ in ()).throw(OSError("odd")),
            helper.INDEX_LOCK_INDETERMINATE,
            False,
            True,
        ),
    ],
)
def test_read_repository_state_index_lock_tri_state(
    observer,
    state,
    present,
    error_expected,
):
    repo_state = helper.read_repository_state(
        TEST_ROOT,
        git_runner=successful_git_runner,
        index_lock_observer=observer,
    )

    assert repo_state.index_lock_state == state
    assert repo_state.index_lock_present is present
    assert (repo_state.index_lock_observation_error is not None) is error_expected


def test_indeterminate_index_lock_fails_closed_before_contact():
    adapter = FakeAdapter()

    result = run_helper(
        adapter,
        repo_reader=lambda: clean_repo(
            index_lock_state=helper.INDEX_LOCK_INDETERMINATE,
            index_lock_observation_error={"exception_type": "PermissionError"},
        ),
    )

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == "index_lock_indeterminate"
    assert adapter.create_calls == []


@pytest.mark.parametrize(
    "profile, subreason",
    [
        (
            helper.VolumeProfile(
                drive_type=4,
                filesystem_name="NTFS",
                volume_serial_number=101,
            ),
            "drive_not_local_fixed",
        ),
        (
            helper.VolumeProfile(
                drive_type=validation.DRIVE_FIXED,
                filesystem_name="exFAT",
                volume_serial_number=101,
            ),
            "filesystem_not_ntfs",
        ),
        (
            helper.VolumeProfile(
                drive_type=validation.DRIVE_FIXED,
                filesystem_name="NTFS",
                volume_serial_number=999,
            ),
            "volume_identity_mismatch",
        ),
    ],
)
def test_parent_profile_rejections_fail_closed_before_create(profile, subreason):
    adapter = FakeAdapter()
    adapter.profile_overrides[TEST_PATH_MODEL.required_root] = profile

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PRE_CONTACT_ABORT
    assert result.derived_subreason == subreason
    assert adapter.create_calls == []


@pytest.mark.parametrize(
    "profile, subreason",
    [
        (
            helper.VolumeProfile(
                drive_type=4,
                filesystem_name="NTFS",
                volume_serial_number=101,
            ),
            "drive_not_local_fixed",
        ),
        (
            helper.VolumeProfile(
                drive_type=validation.DRIVE_FIXED,
                filesystem_name="FAT32",
                volume_serial_number=101,
            ),
            "filesystem_not_ntfs",
        ),
        (
            helper.VolumeProfile(
                drive_type=validation.DRIVE_FIXED,
                filesystem_name="NTFS",
                volume_serial_number=500,
            ),
            "volume_identity_mismatch",
        ),
    ],
)
def test_child_profile_rejections_after_create_are_partial_terminal(
    profile,
    subreason,
):
    adapter = FakeAdapter()
    adapter.profile_overrides[COMPONENT_1] = profile

    result = run_helper(adapter)

    assert result.classification == helper.CORRECTED_PATH_CREATION_PARTIAL_TERMINAL_FAILURE
    assert result.derived_subreason == subreason
    assert result.mutation_succeeded_count == 1
    assert adapter.create_calls == [COMPONENT_1]


def scratch_path_model(root: Path) -> helper.PathModel:
    raw_root = str(root).replace("/", "\\")
    return path_model_from_raw_root(raw_root)


def guarded_mkdir(raw_path: str) -> None:
    assert not raw_path.lower().startswith(GOVERNED_PREFIX.lower())
    os_mkdir = __import__("os").mkdir
    os_mkdir(raw_path)


@pytest.mark.skipif(sys.platform != "win32", reason="native scratch check is Windows-only")
def test_windows_native_scratch_sequence_never_targets_governed_prefix(tmp_path):
    root = tmp_path / "r4-native-root"
    root.mkdir()
    path_model = scratch_path_model(root)
    assert not path_model.components[0].lower().startswith(GOVERNED_PREFIX.lower())

    result = helper.execute_ordered_directory_creation(
        authority=active_authority(),
        accepted_invocation_head=HEAD,
        path_model=path_model,
        repository_reader=lambda: clean_repo(),
        native_adapter=helper.Win32DirectoryAdapter(),
        creation_primitive=guarded_mkdir,
        utc_clock=lambda: "2026-07-29T23:52:00.000000Z",
        monotonic_clock=monotonic_counter(),
        allow_test_path_model=True,
    )
    if result.classification != helper.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION:
        pytest.skip("scratch volume does not satisfy the bounded Windows local fixed NTFS profile")

    for raw_path in path_model.components:
        assert Path(raw_path).is_dir()
