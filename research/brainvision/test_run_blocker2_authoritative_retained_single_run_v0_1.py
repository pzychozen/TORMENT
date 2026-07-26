from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

import blocker2_retained_absolute_path_control_v0_1 as retained
import run_blocker2_authoritative_retained_single_run_v0_1 as wrapper


HEAD = "1" * 40
DOC_BLOB = "2" * 40
DOC_SHA = "3" * 64
DOC_DECL = "4" * 64


def _source_bundle():
    expectations = []
    observations = []
    inventory = []
    for index, relative_path in enumerate(retained.REQUIRED_SOURCE_IDENTITY_PATHS, 1):
        content = ("wrapper source %s\n" % relative_path).encode("ascii")
        observed = retained.synthetic_source_identity(
            relative_path,
            content=content,
            git_blob_oid=("%040x" % index),
        )
        expectation = retained.SourceIdentityExpectation(
            relative_path=observed.relative_path,
            checked_out_byte_sha256=observed.checked_out_byte_sha256,
            checked_out_byte_length=observed.checked_out_byte_length,
            git_blob_oid=observed.git_blob_oid,
        )
        expectations.append(expectation)
        observations.append(observed.as_payload())
        item = expectation.as_payload()
        item["path"] = expectation.relative_path
        inventory.append(item)
    return tuple(expectations), observations, inventory


def _identity_provider(payload):
    items = {}
    for entry in payload["source_identity_inventory"]:
        items[entry["path"]] = wrapper.FileIdentity(
            git_blob_oid=entry["git_blob_oid"],
            checked_out_byte_sha256=entry["checked_out_byte_sha256"],
            checked_out_byte_length=entry["checked_out_byte_length"],
        )
    for entry in payload["document_identity_inventory"]:
        items[entry["path"]] = wrapper.FileIdentity(
            git_blob_oid=entry["git_blob_oid"],
            checked_out_byte_sha256=entry["checked_out_byte_sha256"],
            checked_out_byte_length=entry["checked_out_byte_length"],
        )
    return lambda path: items[path]


def _patch_roots(monkeypatch, tmp_path: Path):
    roots = {
        "authority": tmp_path / "outside" / "authority",
        "fixture": tmp_path / "outside" / "fixture",
        "result_parent": tmp_path / "outside" / "results",
    }
    monkeypatch.setattr(wrapper, "AUTHORITY_REGISTRY_ROOT", roots["authority"])
    monkeypatch.setattr(wrapper, "FIXTURE_ROOT", roots["fixture"])
    monkeypatch.setattr(wrapper, "RESULT_PARENT", roots["result_parent"])
    return roots


def make_payload(tmp_path: Path, monkeypatch, *, mode=wrapper.PREFLIGHT_ONLY):
    roots = _patch_roots(monkeypatch, tmp_path)
    roots["authority"].mkdir(parents=True, exist_ok=True)
    roots["result_parent"].mkdir(parents=True, exist_ok=True)
    expectations, observations, inventory = _source_bundle()
    result_dir = roots["result_parent"] / "pending"
    block = retained.build_execution_authorization_identity_block(
        assessment_identity=retained.RETAINED_RUN_ASSESSMENT_SHA256,
        implementation_preparation_authorization_identity=(
            retained.IMPLEMENTATION_PREPARATION_AUTHORIZATION_SHA256
        ),
        runtime_correction_authorization_identity=(
            retained.RUNTIME_CORRECTION_AUTHORIZATION_SHA256
        ),
        expected_branch="main",
        expected_head=HEAD,
        expected_origin_main=HEAD,
        result_directory=result_dir,
        fixture_root=roots["fixture"],
        authority_registry_root=roots["authority"],
        source_identities=expectations,
    )
    result_dir = roots["result_parent"] / block.execution_authorization_identity
    block = retained.build_execution_authorization_identity_block(
        assessment_identity=retained.RETAINED_RUN_ASSESSMENT_SHA256,
        implementation_preparation_authorization_identity=(
            retained.IMPLEMENTATION_PREPARATION_AUTHORIZATION_SHA256
        ),
        runtime_correction_authorization_identity=(
            retained.RUNTIME_CORRECTION_AUTHORIZATION_SHA256
        ),
        expected_branch="main",
        expected_head=HEAD,
        expected_origin_main=HEAD,
        result_directory=result_dir,
        fixture_root=roots["fixture"],
        authority_registry_root=roots["authority"],
        source_identities=expectations,
    )
    auth = retained.RetainedAuthorization(
        mode=retained.RETAINED_MODE,
        authorization_identity=block.execution_authorization_identity,
        assessment_identity=retained.RETAINED_RUN_ASSESSMENT_SHA256,
        expected_branch="main",
        expected_head=HEAD,
        expected_origin_main=HEAD,
        result_directory=result_dir,
        fixture_root=roots["fixture"],
        selected_cases=retained.DEFAULT_RETAINED_CASES,
        optional_cases=(),
        authoritative=True,
        execution_authorization=block,
    )
    document_inventory = [
        {
            "path": "docs/exact.md",
            "git_blob_oid": DOC_BLOB,
            "checked_out_byte_sha256": DOC_SHA,
            "checked_out_byte_length": 10,
        }
    ]
    payload = {
        "schema": wrapper.SCHEMA,
        "authorization_status": "ACTIVE",
        "wrapper_mode": mode,
        "operator_identity": "Hilmir",
        "single_process_declaration": "one Windows Command Prompt process",
        "single_attempt_declaration": "one authoritative attempt",
        "real_executor_selector": wrapper.REAL_EXECUTOR_SELECTOR,
        "retained_mode": retained.RETAINED_MODE,
        "authoritative": True,
        "repository_identity": {
            "branch": "main",
            "head": HEAD,
            "origin_main": HEAD,
            "head_equals_origin_main": True,
        },
        "source_identity_inventory": inventory,
        "document_identity_inventory": document_inventory,
        "runtime_declaration_identities": wrapper.expected_runtime_identities(),
        "path_model": wrapper.derived_path_model(block.execution_authorization_identity),
        "execution_authorization_identity_block": block.as_payload(),
        "retained_authorization": auth.as_payload(),
        "repository_state": retained.synthetic_clean_repository_state(
            repo_root=tmp_path / "repo",
            branch="main",
            head=HEAD,
            origin_main=HEAD,
        ).as_payload(),
        "source_observations": observations,
        "case_set": {
            "selected_cases": list(retained.DEFAULT_RETAINED_CASES),
            "execution_order": list(retained.DEFAULT_RETAINED_CASES),
            "case_set_sha256": retained.retained_case_set_identity()["case_set_sha256"],
        },
        "a6_selected": False,
        "authorization_input_identity": {},
        "execution_authorization_document_identity": {
            "path": "docs/exact.md",
            "git_blob_oid": DOC_BLOB,
            "checked_out_byte_sha256": DOC_SHA,
            "canonical_authorization_declaration_identity": DOC_DECL,
            "authorization_status": "ACTIVE",
        },
        "fault_injection_disabled": True,
    }
    return wrapper.with_computed_authorization_input_identity(payload)


def clean_state(tmp_path):
    return retained.synthetic_clean_repository_state(
        repo_root=tmp_path / "repo",
        branch="main",
        head=HEAD,
        origin_main=HEAD,
    )


def test_valid_canonical_input_round_trips(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    path = tmp_path / "input.json"
    path.write_bytes(wrapper.canonical_json_bytes(payload))

    loaded, raw = wrapper.load_canonical_json_file(path)

    assert loaded == payload
    assert wrapper.sha256_hex(raw)


def test_noncanonical_input_rejected(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    path = tmp_path / "pretty.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(wrapper.WrapperValidationError) as exc:
        wrapper.load_canonical_json_file(path)

    assert exc.value.terminal_label == wrapper.INVALID_AUTHORIZATION_INPUT


def test_duplicate_keys_rejected(tmp_path):
    path = tmp_path / "dup.json"
    path.write_bytes(b'{"a":1,"a":2}')

    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.load_canonical_json_file(path)


def test_unknown_and_missing_fields_rejected(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    payload["extra"] = True
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )

    payload = make_payload(tmp_path, monkeypatch)
    del payload["operator_identity"]
    payload = wrapper.with_computed_authorization_input_identity(payload)
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )


def test_placeholder_and_wrong_input_identity_rejected(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    payload["source_identity_inventory"][0]["git_blob_oid"] = retained.UNAVAILABLE_UNTIL_COMMIT
    payload = wrapper.with_computed_authorization_input_identity(payload)
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )

    payload = make_payload(tmp_path, monkeypatch)
    payload["authorization_input_identity"]["authorization_input_sha256"] = "5" * 64
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )


def test_wrong_authorization_document_identity_rejected(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    payload["execution_authorization_document_identity"]["checked_out_byte_sha256"] = "6" * 64
    payload = wrapper.with_computed_authorization_input_identity(payload)

    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )


def test_preflight_only_accepts_complete_synthetic_input(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    Path(payload["path_model"]["fixture_root"]).mkdir(parents=True, exist_ok=True)

    result = wrapper.preflight_only(
        payload,
        file_identity_provider=_identity_provider(payload),
        repository_state=clean_state(tmp_path),
        repo_root=tmp_path / "repo",
    )

    assert result["terminal_label"] == wrapper.PREFLIGHT_ACCEPTED_UNCONSUMED
    assert result["authority_consumed"] is False
    assert result["retained_execution"] is False
    assert not Path(payload["path_model"]["result_directory"]).exists()
    assert not Path(payload["path_model"]["global_authority_entry_path"]).exists()


def test_preflight_rejects_existing_result_and_global_entry(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    Path(payload["path_model"]["fixture_root"]).mkdir(parents=True, exist_ok=True)
    Path(payload["path_model"]["result_directory"]).mkdir(parents=True)

    result = wrapper.preflight_only(
        payload,
        file_identity_provider=_identity_provider(payload),
        repository_state=clean_state(tmp_path),
        repo_root=tmp_path / "repo",
    )
    assert result["terminal_label"] == wrapper.PREFLIGHT_REJECTED_UNCONSUMED

    payload = make_payload(tmp_path, monkeypatch)
    Path(payload["path_model"]["fixture_root"]).mkdir(parents=True, exist_ok=True)
    Path(payload["path_model"]["global_authority_entry_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(payload["path_model"]["global_authority_entry_path"]).write_text("x", encoding="ascii")
    result = wrapper.preflight_only(
        payload,
        file_identity_provider=_identity_provider(payload),
        repository_state=clean_state(tmp_path),
        repo_root=tmp_path / "repo",
    )
    assert result["terminal_label"] == wrapper.PREFLIGHT_REJECTED_UNCONSUMED


def test_wrong_repo_source_document_runtime_and_path_identity_rejected(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    bad_state = retained.synthetic_clean_repository_state(
        repo_root=tmp_path / "repo",
        branch="main",
        head="7" * 40,
        origin_main="7" * 40,
    )
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=bad_state,
        )

    payload = make_payload(tmp_path, monkeypatch)
    payload["runtime_declaration_identities"]["case_set_sha256"] = "8" * 64
    payload = wrapper.with_computed_authorization_input_identity(payload)
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )

    payload = make_payload(tmp_path, monkeypatch)
    payload["path_model"]["result_directory"] = str(tmp_path / "other")
    payload = wrapper.with_computed_authorization_input_identity(payload)
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )


def test_execute_mode_isolation_rejects_inactive_synthetic_fault_a6_and_wrong_selector(
    tmp_path,
    monkeypatch,
):
    payload = make_payload(tmp_path, monkeypatch, mode=wrapper.EXECUTE_EXACT_SINGLE_RUN)
    payload["authorization_status"] = "PREPARED_NOT_ACTIVE"
    payload["execution_authorization_document_identity"]["authorization_status"] = "PREPARED_NOT_ACTIVE"
    payload = wrapper.with_computed_authorization_input_identity(payload)
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.EXECUTE_EXACT_SINGLE_RUN,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )

    for key, value in (
        ("real_executor_selector", "SYNTHETIC"),
        ("fault_injection_disabled", False),
        ("a6_selected", True),
    ):
        payload = make_payload(tmp_path, monkeypatch, mode=wrapper.EXECUTE_EXACT_SINGLE_RUN)
        payload[key] = value
        payload = wrapper.with_computed_authorization_input_identity(payload)
        with pytest.raises(wrapper.WrapperValidationError):
            wrapper.validate_authorization_payload(
                payload,
                mode=wrapper.EXECUTE_EXACT_SINGLE_RUN,
                file_identity_provider=_identity_provider(payload),
                repository_state=clean_state(tmp_path),
            )


def test_wrong_case_order_and_generic_callable_selector_rejected(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    payload["case_set"]["execution_order"] = ["A1", "A3", "A2", "A5"]
    payload = wrapper.with_computed_authorization_input_identity(payload)
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )

    payload = make_payload(tmp_path, monkeypatch)
    payload["real_executor_selector"] = "module:function"
    payload = wrapper.with_computed_authorization_input_identity(payload)
    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode=wrapper.PREFLIGHT_ONLY,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )


def test_unknown_mode_fails_closed_before_path_creation(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch)
    payload["wrapper_mode"] = "BOGUS"
    payload = wrapper.with_computed_authorization_input_identity(payload)

    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.validate_authorization_payload(
            payload,
            mode="BOGUS",
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
        )
    assert not (tmp_path / "outside" / "new").exists()


def test_exit_mapping_and_output_are_canonical(tmp_path, monkeypatch):
    record = wrapper.result_record(
        mode=wrapper.PREFLIGHT_ONLY,
        terminal_label=wrapper.PREFLIGHT_ACCEPTED_UNCONSUMED,
        authoritative=False,
        retained_execution=False,
        authority_consumed=False,
        authorization_input_file_sha256="9" * 64,
        path_model={},
        case_set_identity="8" * 64,
        a6_selected=False,
    )

    assert wrapper.EXIT_CODES[record["terminal_label"]] == 0
    assert wrapper.canonical_json_bytes(record).decode("utf-8").startswith("{")


def test_execute_invokes_only_locked_real_executor_after_preflight(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch, mode=wrapper.EXECUTE_EXACT_SINGLE_RUN)
    Path(payload["path_model"]["fixture_root"]).mkdir(parents=True, exist_ok=True)
    calls = []

    def fake_run(authorization, **kwargs):
        calls.append(kwargs["case_executor"])
        return retained.RetainedRunResult(
            terminal_state=retained.RUN_FAILED,
            retained_execution=False,
            authoritative=True,
            global_authority_consumed=True,
            gate_consumed=False,
            native_invocation_started=False,
            primary_failure=retained.CASE_OUTCOME_REJECTED,
            detail="synthetic wrapper isolation",
            result_directory=str(authorization.result_directory),
        )

    result = wrapper.execute_exact_single_run(
        payload,
        file_identity_provider=_identity_provider(payload),
        repository_state=clean_state(tmp_path),
        repo_root=tmp_path / "repo",
        run_invoker=fake_run,
    )

    assert result["terminal_label"] == wrapper.AUTHORITATIVE_RUN_FAILED_CONSUMED
    assert calls == [retained.execute_existing_absolute_path_retained_case_set]


def test_main_rejects_unknown_argparse_mode_without_default_execution(capsys):
    with pytest.raises(SystemExit):
        wrapper._build_parser().parse_args(["--mode", "BOGUS", "--authorization-input", "x"])
