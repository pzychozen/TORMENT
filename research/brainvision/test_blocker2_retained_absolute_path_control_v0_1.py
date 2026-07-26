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
ASSESSMENT_IDENTITY = "b" * 64
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


def clean_repo_state() -> retained.RepositoryState:
    return retained.synthetic_clean_repository_state(
        branch="main",
        head=SYNTHETIC_HEAD,
        origin_main=SYNTHETIC_HEAD,
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
        policy_identity=retained.authorized_absolute_path_control_policy_identity(),
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
        policy_identity=retained.authorized_absolute_path_control_policy_identity(),
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
            policy_identity=retained.authorized_absolute_path_control_policy_identity(),
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

    authoritative_auth = make_authorization(tmp_path, authoritative=True)
    admitted = retained.build_terminal_record(
        authorization=authoritative_auth,
        terminal_state=retained.RUN_COMPLETE,
        gate_consumed=True,
        native_invocation_started=True,
        retained_execution=True,
        primary_failure="NONE",
        detail="synthetic admitted",
        case_outcomes=outcomes,
        gate_artifact=fake_gate_artifact(),
        artifact_state=retained.completed_artifact_state(),
    )
    retained.validate_terminal_record(admitted)

    no_native = dict(admitted)
    no_native["native_invocation_started"] = False
    with pytest.raises(retained.RetainedValidationError):
        retained.validate_terminal_record(no_native)

    pending_artifact = dict(admitted)
    pending_artifact["artifact_state"] = retained.pending_artifact_state()
    with pytest.raises(retained.RetainedValidationError):
        retained.validate_terminal_record(pending_artifact)

    failed_state = dict(admitted)
    failed_state["terminal_state"] = retained.RUN_FAILED
    with pytest.raises(retained.RetainedValidationError):
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
    assert authoritative.primary_failure == retained.AUTHORITATIVE_RUN_NOT_AUTHORIZED
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
    assert result.primary_failure == retained.TERMINAL_ARTIFACT_REVERIFY_FAILURE
    assert result.retained_execution is False
