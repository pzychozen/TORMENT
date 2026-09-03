from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from torment_service.fabric import TormentFabric
from torment_service.public_runtime import (
    NATIVE_SAFE_FALLTHROUGH_SURFACES,
    PUBLIC_TORMENT_FABRIC_FALLTHROUGH_CENSUS,
    NativePublicOperationRefused,
    PublicRuntimeMode,
    PublicTormentRuntime,
    close_public_runtime,
    create_public_runtime,
)

from test_b5_a3_production_native_resource_owner import _active_fixture
from test_b5_a4r3_public_backend_selection import (
    _NativeLaneFabric,
    _configuration,
    _native_counts,
    _prime_external_identity,
)


def _native_runtime(tmp_path: Path, monkeypatch):
    """Build an active synthetic root with frozen, pre-existing external facts."""
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    root, _core, descriptor, profile, _agreement = _active_fixture(tmp_path)
    _prime_external_identity(root)
    runtime = create_public_runtime(root, _configuration(root, descriptor, profile))
    assert runtime.mode is PublicRuntimeMode.NATIVE
    return root, profile, runtime


def _assert_no_legacy_scope(root: Path, workspace_id: str, agent_id: str | None = None) -> None:
    workspace = root / "workspaces" / workspace_id
    if agent_id is None:
        assert not workspace.exists()
    else:
        assert not (workspace / "agents" / agent_id).exists()


def test_m1_native_active_get_workspace_is_fenced_before_legacy_materialization(tmp_path: Path, monkeypatch):
    root, _profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        # The explicit native route cannot turn an absent scope into a legacy
        # workspace, and the callee guard protects direct/internal use too.
        with pytest.raises(NativePublicOperationRefused):
            runtime.get_workspace("unadmitted")
        with pytest.raises(NativePublicOperationRefused, match="get_workspace materialization"):
            runtime.cognition_fabric.get_workspace("unadmitted")
        _assert_no_legacy_scope(root, "unadmitted")
    finally:
        close_public_runtime(root)


def test_m2_native_active_create_agent_is_fenced_before_legacy_materialization(tmp_path: Path, monkeypatch):
    root, _profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        with pytest.raises(NativePublicOperationRefused):
            runtime.create_agent("orchard", "unadmitted-agent")
        with pytest.raises(NativePublicOperationRefused, match="create_agent materialization"):
            runtime.cognition_fabric.create_agent("orchard", "unadmitted-agent")
        _assert_no_legacy_scope(root, "orchard", "unadmitted-agent")
        assert runtime.cognition_fabric.private_graphs == {}
    finally:
        close_public_runtime(root)


def test_m3_legacy_root_keeps_historical_workspace_and_agent_creation(tmp_path: Path, monkeypatch):
    import torment_service.public_runtime as public_runtime

    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeLaneFabric)
    root = tmp_path / "legacy-root"
    runtime = create_public_runtime(root)
    try:
        assert runtime.mode is PublicRuntimeMode.LEGACY
        workspace = runtime.get_workspace("legacy-workspace", domains=["research"])
        identity = runtime.create_agent("legacy-workspace", "legacy-agent")
        assert workspace.workspace_id == "legacy-workspace"
        assert identity.agent_id == "legacy-agent"
        assert (root / "workspaces" / "legacy-workspace").is_dir()
        assert (root / "workspaces" / "legacy-workspace" / "agents" / "legacy-agent").is_dir()
    finally:
        close_public_runtime(root)


def test_m4_admitted_native_scope_resolves_through_explicit_public_routes(tmp_path: Path, monkeypatch):
    root, _profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        workspace = runtime.get_workspace("orchard")
        identity = runtime.create_agent("orchard", "aria")
        assert workspace.workspace_id == "orchard"
        assert workspace.domains == ("archive", "research")
        assert identity.agent_id == "aria"
        assert runtime.cognition_fabric.private_graphs == {}
    finally:
        close_public_runtime(root)


def test_m5_absent_native_scope_refuses_without_legacy_or_native_membership_creation(tmp_path: Path, monkeypatch):
    root, _profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        counts_before = _native_counts(runtime)
        with pytest.raises(NativePublicOperationRefused):
            runtime.get_workspace("absent-workspace")
        with pytest.raises(NativePublicOperationRefused):
            runtime.create_agent("orchard", "absent-agent")
        assert _native_counts(runtime) == counts_before
        assert runtime._workspace_views == {}
        assert runtime.cognition_fabric.private_graphs == {}
        _assert_no_legacy_scope(root, "absent-workspace")
        _assert_no_legacy_scope(root, "orchard", "absent-agent")
    finally:
        close_public_runtime(root)


def test_m6_native_public_fallthrough_materializer_is_refused_before_effect(tmp_path: Path, monkeypatch):
    root, _profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        # feedback previously delegated through __getattr__ and then called
        # Fabric.create_agent/get_workspace.  It is now refused at delegation.
        with pytest.raises(NativePublicOperationRefused, match="feedback"):
            runtime.feedback("unadmitted", "agent", [], False)
        _assert_no_legacy_scope(root, "unadmitted", "agent")
    finally:
        close_public_runtime(root)


def test_m7_native_mode_keeps_no_generic_safe_fallthrough(tmp_path: Path, monkeypatch):
    root, _profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        assert NATIVE_SAFE_FALLTHROUGH_SURFACES == frozenset()
        with pytest.raises(NativePublicOperationRefused, match="list_workspaces_meta"):
            runtime.list_workspaces_meta()
    finally:
        close_public_runtime(root)


def test_m8_nominal_legacy_read_cannot_materialize_a_native_workspace(tmp_path: Path, monkeypatch):
    root, _profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        # memory_chain is a nominal read whose legacy implementation obtains a
        # workspace lazily.  Refusal happens before that implementation runs.
        with pytest.raises(NativePublicOperationRefused, match="memory_chain"):
            runtime.memory_chain("read-absent", 1)
        _assert_no_legacy_scope(root, "read-absent")
    finally:
        close_public_runtime(root)


def test_m9_stale_native_profile_refuses_without_legacy_fallback(tmp_path: Path, monkeypatch):
    root, profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        # Establish a cached view first: revalidation must still happen before
        # an existing process-local view is returned.
        assert runtime.get_workspace("orchard").workspace_id == "orchard"
        runtime.native_owner._effective_profile = replace(  # type: ignore[union-attr]
            profile,
            external_owner_digest="f" * 64,
        )
        with pytest.raises(NativePublicOperationRefused, match="root/profile authority is absent or stale"):
            runtime.get_workspace("orchard")
        assert runtime.cognition_fabric.private_graphs == {}
    finally:
        close_public_runtime(root)


def test_m10_native_public_create_never_treats_caller_data_as_admission_authority(tmp_path: Path, monkeypatch):
    root, _profile, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        with pytest.raises(NativePublicOperationRefused, match="agent creation"):
            runtime.create_agent("orchard", "witness-agent", seed={"witness": "caller-supplied"})
        _assert_no_legacy_scope(root, "orchard", "witness-agent")
        assert runtime.cognition_fabric.private_graphs == {}
    finally:
        close_public_runtime(root)


def test_m10_rest_creation_and_legacy_maintenance_routes_are_unclassified_in_native_mode():
    from torment_service.app import _native_rest_route_is_classified

    for method, path in (
        ("POST", "/workspace/create"),
        ("POST", "/workspace/clone"),
        ("POST", "/agent/create"),
        ("POST", "/domain/approve_suggestion"),
        ("POST", "/proposals/process"),
        ("GET", "/workspaces/meta"),
    ):
        assert not _native_rest_route_is_classified(method, path)


def test_m11_same_workspace_shape_is_legacy_materializing_or_native_refusal_by_selector_mode(tmp_path: Path, monkeypatch):
    native_root, _profile, native_runtime = _native_runtime(tmp_path / "native", monkeypatch)
    legacy_root = tmp_path / "legacy"
    legacy_runtime = create_public_runtime(legacy_root)
    try:
        with pytest.raises(NativePublicOperationRefused):
            native_runtime.get_workspace("same-shape")
        legacy_workspace = legacy_runtime.get_workspace("same-shape", domains=["research"])
        assert legacy_workspace.workspace_id == "same-shape"
        assert not (native_root / "workspaces" / "same-shape").exists()
        assert (legacy_root / "workspaces" / "same-shape").is_dir()
    finally:
        close_public_runtime(native_root)
        close_public_runtime(legacy_root)


def test_m12_fallthrough_census_matches_every_declared_public_fabric_member():
    public_fabric_members = {
        name
        for name, value in vars(TormentFabric).items()
        if not name.startswith("_")
        and (callable(value) or isinstance(value, property))
        and name not in vars(PublicTormentRuntime)
    }
    assert public_fabric_members == PUBLIC_TORMENT_FABRIC_FALLTHROUGH_CENSUS
