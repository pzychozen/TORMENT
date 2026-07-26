from __future__ import annotations

from pathlib import Path
import sys

import pytest

import run_blocker2_authoritative_retained_single_run_v0_1 as wrapper
from test_run_blocker2_authoritative_retained_single_run_v0_1 import (
    _identity_provider,
    clean_state,
    make_payload,
)


WINDOWS_ONLY = pytest.mark.skipif(
    sys.platform != "win32",
    reason="BLOCKER-2 operator path preparation profile is Windows-only",
)


@WINDOWS_ONLY
def test_prepare_paths_creates_only_fixed_roots_and_no_evidence(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch, mode=wrapper.PREPARE_PATHS)

    result = wrapper.prepare_paths(
        payload,
        file_identity_provider=_identity_provider(payload),
        repository_state=clean_state(tmp_path),
        repo_root=tmp_path / "repo",
    )

    assert result["terminal_label"] == wrapper.PREPARATION_COMPLETE
    assert result["authoritative"] is False
    assert result["retained_execution"] is False
    assert result["authority_consumed"] is False
    assert Path(payload["path_model"]["authority_registry_root"]).is_dir()
    assert Path(payload["path_model"]["fixture_root"]).is_dir()
    assert Path(payload["path_model"]["result_parent"]).is_dir()
    assert not Path(payload["path_model"]["result_directory"]).exists()
    assert not Path(payload["path_model"]["global_authority_entry_path"]).exists()
    assert not Path(payload["path_model"]["local_gate_path"]).exists()
    assert not Path(payload["path_model"]["run_result_path"]).exists()
    assert not Path(payload["path_model"]["retained_completion_path"]).exists()
    assert result["path_preparation"]["authority_registry_root"]["volume"]["drive_type"] == "DRIVE_FIXED"
    assert result["path_preparation"]["authority_registry_root"]["volume"][
        "filesystem_name"
    ].upper() == "NTFS"


@WINDOWS_ONLY
def test_prepare_paths_rejects_repository_contained_roots(tmp_path, monkeypatch):
    payload = make_payload(tmp_path, monkeypatch, mode=wrapper.PREPARE_PATHS)
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(wrapper, "AUTHORITY_REGISTRY_ROOT", repo / "authority")
    monkeypatch.setattr(wrapper, "FIXTURE_ROOT", tmp_path / "outside" / "fixture")
    monkeypatch.setattr(wrapper, "RESULT_PARENT", tmp_path / "outside" / "results")
    payload["path_model"] = wrapper.derived_path_model(
        payload["retained_authorization"]["authorization_identity"]
    )
    payload = wrapper.with_computed_authorization_input_identity(payload)

    with pytest.raises(wrapper.WrapperValidationError):
        wrapper.prepare_paths(
            payload,
            file_identity_provider=_identity_provider(payload),
            repository_state=clean_state(tmp_path),
            repo_root=repo,
        )


@WINDOWS_ONLY
def test_preflight_only_after_prepare_does_not_call_native_or_create_evidence(
    tmp_path,
    monkeypatch,
):
    payload = make_payload(tmp_path, monkeypatch, mode=wrapper.PREPARE_PATHS)
    wrapper.prepare_paths(
        payload,
        file_identity_provider=_identity_provider(payload),
        repository_state=clean_state(tmp_path),
        repo_root=tmp_path / "repo",
    )
    payload = dict(payload)
    payload["wrapper_mode"] = wrapper.PREFLIGHT_ONLY
    payload = wrapper.with_computed_authorization_input_identity(payload)

    result = wrapper.preflight_only(
        payload,
        file_identity_provider=_identity_provider(payload),
        repository_state=clean_state(tmp_path),
        repo_root=tmp_path / "repo",
    )

    assert result["terminal_label"] == wrapper.PREFLIGHT_ACCEPTED_UNCONSUMED
    assert not Path(payload["path_model"]["result_directory"]).exists()
    assert not Path(payload["path_model"]["global_authority_entry_path"]).exists()
    assert not Path(payload["path_model"]["local_gate_path"]).exists()
    assert not Path(payload["path_model"]["run_result_path"]).exists()
    assert not Path(payload["path_model"]["retained_completion_path"]).exists()
