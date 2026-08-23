"""Phase-10 durable configuration/sidecar recovery-matrix coverage."""

from dataclasses import replace
from pathlib import Path

import pytest

from brainvision.configuration import (
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DISABLED,
    LIFECYCLE_SUSPENDED,
    load_brainvision_configuration,
    write_brainvision_configuration,
)
from brainvision.character_modulation import modulation_profile_id
from brainvision.lifecycle import BrainvisionLifecycleError, BrainvisionLifecycleManager
from brainvision.vhe_sidecar import (
    fresh_vhe_sidecar,
    load_vhe_sidecar,
    vhe_sidecar_path,
    write_vhe_sidecar,
)
from torment_service.agent_locks import AgentLockManager
from torment_service.identity import IdentityStore


WORKSPACE_ID = "workspace-a"
AGENT_ID = "agent-a"


class ManualMonotonic:
    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
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


def _cold_manager(
    root: Path,
    source: ManualMonotonic,
    identities: IdentityStore,
    locks: AgentLockManager,
) -> BrainvisionLifecycleManager:
    return BrainvisionLifecycleManager(
        data_dir=root,
        identity_store=identities,
        lock_manager=locks,
        monotonic_ns_source=source,
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


def test_no_configuration_and_no_sidecar_is_absent_without_creation(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)

    with pytest.raises(BrainvisionLifecycleError) as missing:
        manager.enable(WORKSPACE_ID, AGENT_ID)
    _assert_reason(missing, "configuration_absent")
    assert manager.runtime_count == 0
    assert not Path(vhe_sidecar_path(tmp_path, WORKSPACE_ID, AGENT_ID)).exists()


def test_no_configuration_with_sidecar_is_an_integrity_failure_without_mutation(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    candidate = _configure(manager)
    write_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID, fresh_vhe_sidecar(candidate))
    manager.delete_brainvision_configuration(WORKSPACE_ID, AGENT_ID)
    sidecar_path = Path(vhe_sidecar_path(tmp_path, WORKSPACE_ID, AGENT_ID))
    # Recreate the prohibited no-config/sidecar state directly in the temp root.
    write_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID, fresh_vhe_sidecar(candidate))

    with pytest.raises(BrainvisionLifecycleError) as failure:
        manager.enable(WORKSPACE_ID, AGENT_ID)
    _assert_reason(failure, "sidecar_integrity_failure")
    assert sidecar_path.exists()
    assert manager.runtime_count == 0


def test_disabled_equal_orphan_is_cleaned_before_disabled_reconfiguration(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    configuration = _configure(manager)
    write_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID, fresh_vhe_sidecar(configuration))

    reconfigured = manager.reconfigure_disabled_profile(WORKSPACE_ID, AGENT_ID, 1)
    assert reconfigured.lifecycle_status == LIFECYCLE_DISABLED
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) is None
    assert manager.runtime_count == 0


def test_disabled_without_sidecar_is_a_valid_runtime_absent_state(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    configuration = _configure(manager)

    reconfigured = manager.reconfigure_disabled_profile(WORKSPACE_ID, AGENT_ID, -1)
    assert configuration.lifecycle_status == LIFECYCLE_DISABLED
    assert reconfigured.lifecycle_status == LIFECYCLE_DISABLED
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) is None
    assert manager.runtime_count == 0


def test_disabled_sidecar_ahead_repairs_watermark_then_deletes_orphan(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    configuration = _configure(manager)
    sidecar = replace(fresh_vhe_sidecar(configuration), accepted_source_sequence=4)
    write_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID, sidecar)

    reconfigured = manager.reconfigure_disabled_profile(WORKSPACE_ID, AGENT_ID, 1)
    assert reconfigured.last_accepted_source_sequence == 4
    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID) == reconfigured
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) is None


def test_disabled_configuration_ahead_deletes_orphan_without_watermark_repair(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    configuration = _configure(manager)
    ahead = replace(configuration, last_accepted_source_sequence=4)
    write_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID, ahead)
    write_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID, fresh_vhe_sidecar(configuration))

    reconfigured = manager.reconfigure_disabled_profile(WORKSPACE_ID, AGENT_ID, 1)
    assert reconfigured.last_accepted_source_sequence == 4
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) is None


def test_disabled_identity_mismatch_preserves_the_orphan_for_manual_repair(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    configuration = _configure(manager)
    mismatched = fresh_vhe_sidecar(
        replace(
            configuration,
            theta=1,
            modulation_profile_id=modulation_profile_id(1),
        )
    )
    write_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID, mismatched)

    with pytest.raises(BrainvisionLifecycleError) as mismatch:
        manager.reconfigure_disabled_profile(WORKSPACE_ID, AGENT_ID, 1)
    _assert_reason(mismatch, "sidecar_integrity_failure")
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID) == mismatched


@pytest.mark.parametrize("status", (LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED))
def test_active_or_suspended_missing_sidecar_hard_fails(tmp_path: Path, status: str) -> None:
    manager, source, _, _ = _environment(tmp_path)
    _configure(manager)
    manager.enable(WORKSPACE_ID, AGENT_ID)
    if status == LIFECYCLE_SUSPENDED:
        source.now = 1
        manager.suspend(WORKSPACE_ID, AGENT_ID)
    Path(vhe_sidecar_path(tmp_path, WORKSPACE_ID, AGENT_ID)).unlink()

    with pytest.raises(BrainvisionLifecycleError) as missing:
        manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    _assert_reason(missing, "sidecar_missing")
    assert manager.runtime_count == 0


@pytest.mark.parametrize("status", (LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED))
def test_cold_recovery_reconstructs_equal_active_and_suspended_runtimes(
    tmp_path: Path, status: str
) -> None:
    manager, source, identities, locks = _environment(tmp_path)
    _configure(manager)
    manager.enable(WORKSPACE_ID, AGENT_ID)
    if status == LIFECYCLE_SUSPENDED:
        source.now = 19
        manager.suspend(WORKSPACE_ID, AGENT_ID)

    cold = _cold_manager(tmp_path, source, identities, locks)
    snapshot = cold.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    assert snapshot.configuration.lifecycle_status == status
    assert cold.runtime_count == 1


def test_active_reconstruction_epoch_is_independent_of_first_lazy_access(tmp_path: Path) -> None:
    manager, source, identities, locks = _environment(tmp_path)
    _configure(manager)
    manager.enable(WORKSPACE_ID, AGENT_ID)

    source.now = 1_000_000_000
    with manager.active_transaction(WORKSPACE_ID, AGENT_ID) as transaction:
        initial = transaction.commit_successor(transaction.base_vhe_state, 0)
    assert initial.active_time_ns == 1_000_000_000
    manager.shutdown()

    source.now = 11_000_000_000
    recovered = _cold_manager(tmp_path, source, identities, locks)
    assert recovered.runtime_count == 0

    source.now = 12_000_000_000
    with recovered.active_transaction(WORKSPACE_ID, AGENT_ID) as transaction:
        assert transaction.prior_committed_active_time_ns == 1_000_000_000
        assert transaction.elapsed_active_time_ns == 1_000_000_000
        committed = transaction.commit_successor(transaction.base_vhe_state, 1)

    assert committed.active_time_ns == 2_000_000_000
    sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert sidecar is not None
    assert sidecar.committed_active_time_ns == 2_000_000_000


@pytest.mark.parametrize("status", (LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED))
def test_active_or_suspended_sidecar_ahead_repairs_watermark_and_reconstructs(
    tmp_path: Path, status: str
) -> None:
    manager, source, identities, locks = _environment(tmp_path)
    _configure(manager)
    configuration = manager.enable(WORKSPACE_ID, AGENT_ID)
    if status == LIFECYCLE_SUSPENDED:
        source.now = 9
        configuration = manager.suspend(WORKSPACE_ID, AGENT_ID)
    sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert sidecar is not None
    write_vhe_sidecar(
        tmp_path,
        WORKSPACE_ID,
        AGENT_ID,
        replace(sidecar, accepted_source_sequence=3),
    )

    cold = _cold_manager(tmp_path, source, identities, locks)
    snapshot = cold.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    assert snapshot.configuration.last_accepted_source_sequence == 3
    assert snapshot.configuration.lifecycle_status == status
    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID).last_accepted_source_sequence == 3
    assert configuration.last_accepted_source_sequence == -1


@pytest.mark.parametrize("status", (LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED))
def test_active_or_suspended_configuration_ahead_hard_fails_without_mutation(
    tmp_path: Path, status: str
) -> None:
    manager, source, identities, locks = _environment(tmp_path)
    _configure(manager)
    configuration = manager.enable(WORKSPACE_ID, AGENT_ID)
    if status == LIFECYCLE_SUSPENDED:
        source.now = 3
        configuration = manager.suspend(WORKSPACE_ID, AGENT_ID)
    ahead = replace(configuration, last_accepted_source_sequence=1)
    write_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID, ahead)

    cold = _cold_manager(tmp_path, source, identities, locks)
    with pytest.raises(BrainvisionLifecycleError) as ahead_failure:
        cold.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
    _assert_reason(ahead_failure, "config_ahead")
    assert load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID) == ahead
    assert cold.runtime_count == 0
