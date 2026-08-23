"""Phase-10 lawful lifecycle transition coverage."""

from pathlib import Path

import pytest

from brainvision.configuration import (
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DISABLED,
    LIFECYCLE_SUSPENDED,
    brainvision_configuration_path,
    load_brainvision_configuration,
)
from brainvision.lifecycle import BrainvisionLifecycleError, BrainvisionLifecycleManager
from brainvision.vhe_sidecar import load_vhe_sidecar, vhe_sidecar_path
from torment_service.agent_locks import AgentLockManager
from torment_service.identity import IdentityStore


WORKSPACE_ID = "workspace-a"
AGENT_ID = "agent-a"


class ManualMonotonic:
    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now


def _manager(tmp_path: Path) -> tuple[BrainvisionLifecycleManager, ManualMonotonic]:
    source = ManualMonotonic()
    identities = IdentityStore(str(tmp_path))
    identities.create(WORKSPACE_ID, AGENT_ID)
    return (
        BrainvisionLifecycleManager(
            data_dir=tmp_path,
            identity_store=identities,
            lock_manager=AgentLockManager(),
            monotonic_ns_source=source,
        ),
        source,
    )


def _configure(manager: BrainvisionLifecycleManager):
    return manager.configure_brainvision(
        WORKSPACE_ID,
        AGENT_ID,
        "camera-main",
        "descriptor-v1",
        0,
    )


def _assert_reason(error: pytest.ExceptionInfo[BrainvisionLifecycleError], reason: str) -> None:
    assert error.value.reason == reason


def test_configure_reconfigure_and_delete_start_a_new_disabled_lineage(tmp_path: Path) -> None:
    manager, _ = _manager(tmp_path)

    original = _configure(manager)
    assert original.lifecycle_status == LIFECYCLE_DISABLED
    assert original.last_accepted_source_sequence == -1
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) is None

    reconfigured = manager.reconfigure_disabled_profile(WORKSPACE_ID, AGENT_ID, 1)
    assert reconfigured.theta == 1
    assert reconfigured.modulation_profile_id != original.modulation_profile_id
    assert reconfigured.stream_identity == original.stream_identity
    assert reconfigured.adapter_contract_id == original.adapter_contract_id

    manager.delete_brainvision_configuration(WORKSPACE_ID, AGENT_ID)
    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID) is None
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) is None
    assert Path(brainvision_configuration_path(tmp_path, WORKSPACE_ID, AGENT_ID)).parent.exists()

    replacement = _configure(manager)
    assert replacement.lifecycle_status == LIFECYCLE_DISABLED
    assert replacement.last_accepted_source_sequence == -1
    assert replacement.theta == 0


def test_enable_suspend_resume_reset_disable_and_idempotence(tmp_path: Path) -> None:
    manager, source = _manager(tmp_path)
    configured = _configure(manager)

    active = manager.enable(WORKSPACE_ID, AGENT_ID)
    assert active.lifecycle_status == LIFECYCLE_ACTIVE
    assert manager.enable(WORKSPACE_ID, AGENT_ID) == active
    assert manager.runtime_count == 1

    source.now = 17
    suspended = manager.suspend(WORKSPACE_ID, AGENT_ID)
    assert suspended.lifecycle_status == LIFECYCLE_SUSPENDED
    sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert sidecar is not None
    assert sidecar.committed_active_time_ns == 17
    assert manager.suspend(WORKSPACE_ID, AGENT_ID) == suspended

    with pytest.raises(BrainvisionLifecycleError) as suspended_enable:
        manager.enable(WORKSPACE_ID, AGENT_ID)
    _assert_reason(suspended_enable, "invalid_lifecycle_transition")

    source.now = 123
    resumed = manager.resume(WORKSPACE_ID, AGENT_ID)
    assert resumed.lifecycle_status == LIFECYCLE_ACTIVE
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) == sidecar

    source.now = 130
    reset = manager.reset(WORKSPACE_ID, AGENT_ID)
    assert reset == resumed
    reset_sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert reset_sidecar is not None
    assert reset_sidecar.committed_active_time_ns == 0
    assert reset_sidecar.accepted_source_sequence == configured.last_accepted_source_sequence

    disabled = manager.disable(WORKSPACE_ID, AGENT_ID)
    assert disabled.lifecycle_status == LIFECYCLE_DISABLED
    assert manager.disable(WORKSPACE_ID, AGENT_ID) == disabled
    assert manager.runtime_count == 0
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) is None
    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID) == disabled


def test_reset_preserves_suspended_mode_and_disabled_operations_are_refused(tmp_path: Path) -> None:
    manager, source = _manager(tmp_path)
    _configure(manager)
    manager.enable(WORKSPACE_ID, AGENT_ID)
    source.now = 11
    manager.suspend(WORKSPACE_ID, AGENT_ID)

    reset = manager.reset(WORKSPACE_ID, AGENT_ID)
    assert reset.lifecycle_status == LIFECYCLE_SUSPENDED
    snapshot = manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    assert snapshot.active_time_ns == 0
    assert manager.runtime_count == 1

    manager.disable(WORKSPACE_ID, AGENT_ID)
    for operation in (
        manager.suspend,
        manager.resume,
        manager.reset,
        manager.runtime_snapshot,
    ):
        with pytest.raises(BrainvisionLifecycleError) as refusal:
            operation(WORKSPACE_ID, AGENT_ID)
        _assert_reason(refusal, "invalid_lifecycle_transition")


def test_active_profile_reconfiguration_and_delete_are_refused(tmp_path: Path) -> None:
    manager, _ = _manager(tmp_path)
    _configure(manager)
    manager.enable(WORKSPACE_ID, AGENT_ID)

    for operation in (
        lambda: manager.reconfigure_disabled_profile(WORKSPACE_ID, AGENT_ID, -1),
        lambda: manager.delete_brainvision_configuration(WORKSPACE_ID, AGENT_ID),
    ):
        with pytest.raises(BrainvisionLifecycleError) as refusal:
            operation()
        _assert_reason(refusal, "invalid_lifecycle_transition")


def test_enable_config_write_failure_leaves_a_disabled_configuration_and_orphan_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager, _ = _manager(tmp_path)
    configuration = _configure(manager)

    import brainvision.lifecycle as lifecycle_module

    def fail_configuration_write(*_: object, **__: object) -> None:
        raise OSError("configuration write failure")

    monkeypatch.setattr(lifecycle_module, "write_brainvision_configuration", fail_configuration_write)
    with pytest.raises(BrainvisionLifecycleError) as failure:
        manager.enable(WORKSPACE_ID, AGENT_ID)
    _assert_reason(failure, "durability_failure")
    assert failure.value.durable_committed is True

    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID) == configuration
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) is not None
    assert manager.runtime_count == 0


def test_disable_post_commit_sidecar_delete_failure_drops_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager, _ = _manager(tmp_path)
    _configure(manager)
    manager.enable(WORKSPACE_ID, AGENT_ID)

    def fail_delete(*_: object, **__: object) -> None:
        raise OSError("sidecar delete failure")

    monkeypatch.setattr(manager, "_delete_contained_file", fail_delete)
    with pytest.raises(BrainvisionLifecycleError) as failure:
        manager.disable(WORKSPACE_ID, AGENT_ID)
    assert failure.value.reason == "durability_failure"
    assert failure.value.durable_committed is True
    assert manager.runtime_count == 0
    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID).lifecycle_status == LIFECYCLE_DISABLED
    assert Path(vhe_sidecar_path(tmp_path, WORKSPACE_ID, AGENT_ID)).exists()
