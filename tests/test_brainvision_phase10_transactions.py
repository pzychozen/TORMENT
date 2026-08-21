"""Phase-10 staging, transaction, snapshot, and shutdown coverage."""

from dataclasses import replace
from pathlib import Path

import pytest

import brainvision.lifecycle as lifecycle_module
from brainvision.configuration import LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED, load_brainvision_configuration
from brainvision.fixtures import DA
from brainvision.lifecycle import BrainvisionLifecycleError, BrainvisionLifecycleManager
from brainvision.vhe import evolve_vhe_state_as_of, fresh_vhe_state, update_vhe_state
from brainvision.vhe_sidecar import load_vhe_sidecar, write_vhe_sidecar
from torment_service.agent_locks import AgentLockManager
from torment_service.identity import IdentityStore


WORKSPACE_ID = "workspace-a"
AGENT_ID = "agent-a"


class ManualMonotonic:
    def __init__(self) -> None:
        self.now = 0
        self.calls = 0

    def __call__(self) -> int:
        self.calls += 1
        return self.now


def _environment(tmp_path: Path):
    source = ManualMonotonic()
    identities = IdentityStore(str(tmp_path))
    identities.create(WORKSPACE_ID, AGENT_ID)
    locks = AgentLockManager()
    manager = BrainvisionLifecycleManager(
        data_dir=tmp_path,
        identity_store=identities,
        lock_manager=locks,
        monotonic_ns_source=source,
    )
    return manager, source, identities, locks


def _active_manager(tmp_path: Path):
    manager, source, identities, locks = _environment(tmp_path)
    manager.configure_brainvision(
        WORKSPACE_ID,
        AGENT_ID,
        "camera-main",
        "descriptor-v1",
        0,
    )
    manager.enable(WORKSPACE_ID, AGENT_ID)
    return manager, source, identities, locks


def _assert_reason(error: pytest.ExceptionInfo[BrainvisionLifecycleError], reason: str) -> None:
    assert error.value.reason == reason


def test_unknown_agent_is_rejected_before_lock_or_runtime_allocation(tmp_path: Path) -> None:
    source = ManualMonotonic()
    identities = IdentityStore(str(tmp_path))
    locks = AgentLockManager()
    manager = BrainvisionLifecycleManager(
        data_dir=tmp_path,
        identity_store=identities,
        lock_manager=locks,
        monotonic_ns_source=source,
    )
    before = locks.stats()["agent_locks"]

    with pytest.raises(BrainvisionLifecycleError) as unknown:
        manager.configure_brainvision(
            "workspace-missing",
            "agent-missing",
            "camera-main",
            "descriptor-v1",
            0,
        )
    _assert_reason(unknown, "unknown_agent")
    assert locks.stats()["agent_locks"] == before
    assert manager.runtime_count == 0
    assert not (tmp_path / "workspaces" / "workspace-missing").exists()


def test_identity_disappearance_after_precheck_is_rejected_under_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager, _, identities, _ = _environment(tmp_path)
    real_load = identities.load
    calls = 0

    def disappear_on_second_load(workspace_id: str, agent_id: str):
        nonlocal calls
        calls += 1
        return real_load(workspace_id, agent_id) if calls == 1 else None

    monkeypatch.setattr(identities, "load", disappear_on_second_load)
    with pytest.raises(BrainvisionLifecycleError) as disappeared:
        manager.configure_brainvision(
            WORKSPACE_ID,
            AGENT_ID,
            "camera-main",
            "descriptor-v1",
            0,
        )
    _assert_reason(disappeared, "unknown_agent")
    assert manager.runtime_count == 0


def test_staging_uses_interval_delta_not_absolute_active_time(tmp_path: Path) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    runtime = manager._runtimes[(WORKSPACE_ID, AGENT_ID)]
    seeded = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    ).state
    runtime.vhe_state = seeded
    durable_sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert durable_sidecar is not None
    write_vhe_sidecar(
        tmp_path,
        WORKSPACE_ID,
        AGENT_ID,
        replace(durable_sidecar, vhe_state=seeded),
    )

    source.now = 1_000_000_000
    manager.suspend(WORKSPACE_ID, AGENT_ID)
    first_sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert first_sidecar is not None
    expected_first = evolve_vhe_state_as_of(seeded, 1_000_000_000)
    assert first_sidecar.vhe_state == expected_first

    manager.resume(WORKSPACE_ID, AGENT_ID)
    source.now = 2_000_000_000
    manager.suspend(WORKSPACE_ID, AGENT_ID)
    second_sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert second_sidecar is not None
    assert second_sidecar.committed_active_time_ns == 2_000_000_000
    assert second_sidecar.vhe_state == evolve_vhe_state_as_of(expected_first, 1_000_000_000)


def test_suspend_sidecar_failure_preserves_live_active_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    source.now = 10
    before = manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)

    def fail_sidecar(*_: object, **__: object) -> None:
        raise OSError("sidecar failure")

    monkeypatch.setattr(lifecycle_module, "write_vhe_sidecar", fail_sidecar)
    with pytest.raises(BrainvisionLifecycleError) as failure:
        manager.suspend(WORKSPACE_ID, AGENT_ID)
    _assert_reason(failure, "durability_failure")

    after = manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    assert after == before
    assert after.configuration.lifecycle_status == LIFECYCLE_ACTIVE


def test_suspend_config_failure_adopts_the_staged_active_cutoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    source.now = 25

    def fail_configuration(*_: object, **__: object) -> None:
        raise OSError("configuration failure")

    monkeypatch.setattr(lifecycle_module, "write_brainvision_configuration", fail_configuration)
    with pytest.raises(BrainvisionLifecycleError) as failure:
        manager.suspend(WORKSPACE_ID, AGENT_ID)
    _assert_reason(failure, "durability_failure")
    assert failure.value.durable_committed is True
    sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert sidecar is not None
    assert sidecar.committed_active_time_ns == 25
    runtime = manager._runtimes[(WORKSPACE_ID, AGENT_ID)]
    assert runtime.configuration.lifecycle_status == LIFECYCLE_ACTIVE
    assert runtime.visual_clock.committed_active_time_ns == 25
    assert runtime.visual_clock.is_accumulating is True


def test_active_transaction_commits_sidecar_then_configuration_once(tmp_path: Path) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    source.now = 31
    writes: list[str] = []
    real_sidecar = lifecycle_module.write_vhe_sidecar
    real_configuration = lifecycle_module.write_brainvision_configuration

    def record_sidecar(*args: object, **kwargs: object) -> None:
        writes.append("sidecar")
        real_sidecar(*args, **kwargs)

    def record_configuration(*args: object, **kwargs: object) -> None:
        writes.append("configuration")
        real_configuration(*args, **kwargs)

    from unittest.mock import patch

    with patch.object(lifecycle_module, "write_vhe_sidecar", record_sidecar), patch.object(
        lifecycle_module, "write_brainvision_configuration", record_configuration
    ):
        with manager.active_transaction(WORKSPACE_ID, AGENT_ID) as transaction:
            assert transaction.prior_committed_active_time_ns == 0
            assert transaction.cutoff_active_time_ns == 31
            assert transaction.elapsed_active_time_ns == 31
            committed = transaction.commit_successor(transaction.base_vhe_state, 0)
            assert committed.active_time_ns == 31
            with pytest.raises(BrainvisionLifecycleError) as repeated:
                transaction.commit_successor(transaction.base_vhe_state, 0)
            _assert_reason(repeated, "transaction_already_committed")

    assert writes == ["sidecar", "configuration"]
    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID).last_accepted_source_sequence == 0
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).accepted_source_sequence == 0


def test_transaction_config_failure_drops_runtime_and_requires_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    source.now = 41

    def fail_configuration(*_: object, **__: object) -> None:
        raise OSError("configuration failure")

    monkeypatch.setattr(lifecycle_module, "write_brainvision_configuration", fail_configuration)
    with manager.active_transaction(WORKSPACE_ID, AGENT_ID) as transaction:
        with pytest.raises(BrainvisionLifecycleError) as failure:
            transaction.commit_successor(transaction.base_vhe_state, 0)
        _assert_reason(failure, "recovery_required")
        assert failure.value.durable_committed is True
        with pytest.raises(BrainvisionLifecycleError) as retry:
            transaction.commit_successor(transaction.base_vhe_state, 0)
        _assert_reason(retry, "transaction_already_committed")
    assert manager.runtime_count == 0
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).accepted_source_sequence == 0


def test_snapshot_is_pure_for_active_and_frozen_for_suspended(tmp_path: Path) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    source.now = 59
    active_snapshot = manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    runtime = manager._runtimes[(WORKSPACE_ID, AGENT_ID)]
    assert active_snapshot.active_time_ns == 59
    assert runtime.visual_clock.committed_active_time_ns == 0

    manager.suspend(WORKSPACE_ID, AGENT_ID)
    source.now = 1_000
    suspended_snapshot = manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    assert suspended_snapshot.configuration.lifecycle_status == LIFECYCLE_SUSPENDED
    assert suspended_snapshot.active_time_ns == 59


def test_resume_rebases_runtime_time_and_excludes_suspended_downtime(tmp_path: Path) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    source.now = 10
    manager.suspend(WORKSPACE_ID, AGENT_ID)

    source.now = 1_000
    manager.resume(WORKSPACE_ID, AGENT_ID)
    source.now = 1_007
    snapshot = manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    assert snapshot.active_time_ns == 17


def test_reset_sidecar_failure_preserves_runtime_and_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    source.now = 83
    before = manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)

    def fail_sidecar(*_: object, **__: object) -> None:
        raise OSError("sidecar failure")

    monkeypatch.setattr(lifecycle_module, "write_vhe_sidecar", fail_sidecar)
    with pytest.raises(BrainvisionLifecycleError) as failure:
        manager.reset(WORKSPACE_ID, AGENT_ID)
    _assert_reason(failure, "durability_failure")
    after = manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    assert after == before
    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID) == before.configuration


def test_shutdown_flushes_active_once_and_removes_active_or_suspended_runtimes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager, source, _, _ = _active_manager(tmp_path)
    source.now = 71
    writes = 0
    real_sidecar = lifecycle_module.write_vhe_sidecar

    def count_sidecar(*args: object, **kwargs: object) -> None:
        nonlocal writes
        writes += 1
        real_sidecar(*args, **kwargs)

    monkeypatch.setattr(lifecycle_module, "write_vhe_sidecar", count_sidecar)
    manager.shutdown()
    assert writes == 1
    assert manager.runtime_count == 0
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).committed_active_time_ns == 71
    manager.shutdown()
    assert writes == 1
