"""Phase-11 direct FIRSTHAND_VISUAL ingress acceptance coverage."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import brainvision.ingress as ingress_module
import brainvision.lifecycle as lifecycle_module
from brainvision.character_modulation import update_vhe_state_with_character_modulation
from brainvision.clock import VISUAL_TIME_NS_PER_SECOND
from brainvision.configuration import (
    brainvision_configuration_path,
    load_brainvision_configuration,
    write_brainvision_configuration,
)
from brainvision.fixtures import D0, DA, DB
from brainvision.ingress import (
    BrainvisionIngressError,
    FirsthandVisualAdmissionReceipt,
    admit_firsthand_visual_observation,
)
from brainvision.lifecycle import BrainvisionLifecycleError, BrainvisionLifecycleManager
from brainvision.observation import (
    FirsthandVisualObservationV1,
    ObservationProvenanceType,
    derive_observation_id,
)
from brainvision.vhe import fresh_vhe_state, update_vhe_state
from brainvision.vhe_sidecar import (
    load_vhe_sidecar,
    vhe_sidecar_path,
    write_vhe_sidecar,
)
from torment_service.agent_locks import AgentLockManager
from torment_service.identity import IdentityStore


WORKSPACE_ID = "workspace-a"
AGENT_ID = "agent-a"
STREAM_ID = "camera-main"
CONTRACT_ID = "descriptor-v1"


class ManualMonotonic:
    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now


def _environment(
    root: Path,
    *,
    theta: int = 0,
    stream_identity: str = STREAM_ID,
    adapter_contract_id: str = CONTRACT_ID,
    active: bool = True,
) -> tuple[
    BrainvisionLifecycleManager,
    ManualMonotonic,
    IdentityStore,
    AgentLockManager,
]:
    clock = ManualMonotonic()
    identities = IdentityStore(str(root))
    identities.create(WORKSPACE_ID, AGENT_ID)
    locks = AgentLockManager()
    manager = BrainvisionLifecycleManager(
        data_dir=root,
        identity_store=identities,
        lock_manager=locks,
        monotonic_ns_source=clock,
    )
    manager.configure_brainvision(
        WORKSPACE_ID,
        AGENT_ID,
        stream_identity,
        adapter_contract_id,
        theta,
    )
    if active:
        manager.enable(WORKSPACE_ID, AGENT_ID)
    return manager, clock, identities, locks


def _cold_manager(
    root: Path,
    clock: ManualMonotonic,
    identities: IdentityStore,
    locks: AgentLockManager,
) -> BrainvisionLifecycleManager:
    return BrainvisionLifecycleManager(
        data_dir=root,
        identity_store=identities,
        lock_manager=locks,
        monotonic_ns_source=clock,
    )


def _observation(
    *,
    source_sequence: int = 0,
    stream_identity: str = STREAM_ID,
    adapter_contract_id: str = CONTRACT_ID,
    adapter_id: str = "adapter-a",
    descriptor: object = DA,
    source_capture_time_unix_ns: int | None = None,
    confidence_q: int | None = None,
    semantic_event_class: str | None = None,
    world_event_id: str | None = None,
) -> FirsthandVisualObservationV1:
    return FirsthandVisualObservationV1(
        provenance_type=ObservationProvenanceType.FIRSTHAND_VISUAL,
        stream_identity=stream_identity,
        source_sequence=source_sequence,
        observation_id=derive_observation_id(stream_identity, source_sequence),
        descriptor=descriptor,
        adapter_id=adapter_id,
        adapter_contract_id=adapter_contract_id,
        source_capture_time_unix_ns=source_capture_time_unix_ns,
        confidence_q=confidence_q,
        semantic_event_class=semantic_event_class,
        world_event_id=world_event_id,
    )


def _tamper_observation_id(
    observation: FirsthandVisualObservationV1,
    value: str = "bvobs1_tampered",
) -> FirsthandVisualObservationV1:
    object.__setattr__(observation, "observation_id", value)
    return observation


def _assert_ingress_error(
    error: pytest.ExceptionInfo[BrainvisionIngressError],
    field: str,
    reason: str,
) -> None:
    assert error.value.field == field
    assert error.value.reason == reason


def _runtime(manager: BrainvisionLifecycleManager):
    return manager._runtimes[(WORKSPACE_ID, AGENT_ID)]


def _durable_bytes(root: Path) -> tuple[bytes, bytes]:
    return (
        Path(brainvision_configuration_path(root, WORKSPACE_ID, AGENT_ID)).read_bytes(),
        Path(vhe_sidecar_path(root, WORKSPACE_ID, AGENT_ID)).read_bytes(),
    )


def _ingress_state_snapshot(
    root: Path, manager: BrainvisionLifecycleManager
) -> tuple[tuple[bytes, bytes], object, int]:
    runtime = _runtime(manager)
    return (
        _durable_bytes(root),
        runtime.vhe_state,
        runtime.visual_clock.committed_active_time_ns,
    )


def _assert_ingress_state_unchanged(
    root: Path,
    manager: BrainvisionLifecycleManager,
    before: tuple[tuple[bytes, bytes], object, int],
) -> None:
    durable_bytes, vhe_state, committed_active_time_ns = before
    runtime = _runtime(manager)
    assert _durable_bytes(root) == durable_bytes
    assert runtime.vhe_state == vhe_state
    assert runtime.visual_clock.committed_active_time_ns == committed_active_time_ns


def test_exact_type_admits_and_returns_only_the_minimal_receipt(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    observation = _observation()

    receipt = admit_firsthand_visual_observation(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=observation,
    )

    assert type(receipt) is FirsthandVisualAdmissionReceipt
    assert receipt.observation_id == observation.observation_id
    assert receipt.source_sequence == 0
    assert receipt.committed_active_time_ns == 0
    assert tuple(receipt.__dataclass_fields__) == (
        "observation_id",
        "source_sequence",
        "committed_active_time_ns",
    )
    with pytest.raises(FrozenInstanceError):
        receipt.source_sequence = 1
    assert load_brainvision_configuration(
        tmp_path, WORKSPACE_ID, AGENT_ID
    ).last_accepted_source_sequence == 0
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).accepted_source_sequence == 0


def test_only_the_exact_phase2_observation_type_is_accepted(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)

    class ObservationSubclass(FirsthandVisualObservationV1):
        pass

    exact = _observation()
    subclass = ObservationSubclass(
        provenance_type=exact.provenance_type,
        stream_identity=exact.stream_identity,
        source_sequence=exact.source_sequence,
        observation_id=exact.observation_id,
        descriptor=exact.descriptor,
        adapter_id=exact.adapter_id,
        adapter_contract_id=exact.adapter_contract_id,
    )
    for invalid in ({}, "{}", object(), subclass):
        with pytest.raises(BrainvisionIngressError) as refusal:
            admit_firsthand_visual_observation(
                lifecycle_manager=manager,
                workspace_id=WORKSPACE_ID,
                agent_id=AGENT_ID,
                observation=invalid,
            )
        _assert_ingress_error(refusal, "observation", "malformed_observation")


def test_unknown_agent_refusal_precedes_lock_or_brainvision_artifact_creation(
    tmp_path: Path,
) -> None:
    clock = ManualMonotonic()
    identities = IdentityStore(str(tmp_path))
    locks = AgentLockManager()
    manager = BrainvisionLifecycleManager(
        data_dir=tmp_path,
        identity_store=identities,
        lock_manager=locks,
        monotonic_ns_source=clock,
    )
    before_locks = locks.stats()["agent_locks"]

    with pytest.raises(BrainvisionLifecycleError) as refusal:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id="workspace-missing",
            agent_id="agent-missing",
            observation=_observation(),
        )

    assert refusal.value.reason == "unknown_agent"
    assert locks.stats()["agent_locks"] == before_locks
    assert manager.runtime_count == 0
    assert not (tmp_path / "workspaces" / "workspace-missing").exists()


def test_lifecycle_and_recovery_failures_propagate_without_an_operator_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, clock, identities, locks = _environment(tmp_path)
    calls = 0

    def unexpected_update(**_: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("operator must not be called")

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", unexpected_update)

    manager.suspend(WORKSPACE_ID, AGENT_ID)
    with pytest.raises(BrainvisionLifecycleError) as suspended:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    assert suspended.value.reason == "invalid_lifecycle_transition"

    manager.resume(WORKSPACE_ID, AGENT_ID)
    manager.disable(WORKSPACE_ID, AGENT_ID)
    with pytest.raises(BrainvisionLifecycleError) as disabled:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    assert disabled.value.reason == "invalid_lifecycle_transition"

    absent = _cold_manager(tmp_path, clock, identities, locks)
    manager.delete_brainvision_configuration(WORKSPACE_ID, AGENT_ID)
    with pytest.raises(BrainvisionLifecycleError) as no_configuration:
        admit_firsthand_visual_observation(
            lifecycle_manager=absent,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    assert no_configuration.value.reason == "configuration_absent"
    assert calls == 0


def test_missing_sidecar_and_config_ahead_propagate_without_operator_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, identities, locks = _environment(tmp_path)
    monkeypatch.setattr(
        ingress_module,
        "update_vhe_state_with_character_modulation",
        lambda **_: (_ for _ in ()).throw(AssertionError("operator must not run")),
    )
    Path(vhe_sidecar_path(tmp_path, WORKSPACE_ID, AGENT_ID)).unlink()
    with pytest.raises(BrainvisionLifecycleError) as missing:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    assert missing.value.reason == "sidecar_missing"

    root = tmp_path / "config-ahead"
    manager, clock, identities, locks = _environment(root)
    configuration = load_brainvision_configuration(root, WORKSPACE_ID, AGENT_ID)
    write_brainvision_configuration(
        root,
        WORKSPACE_ID,
        AGENT_ID,
        replace(configuration, last_accepted_source_sequence=1),
    )
    cold = _cold_manager(root, clock, identities, locks)
    with pytest.raises(BrainvisionLifecycleError) as ahead:
        admit_firsthand_visual_observation(
            lifecycle_manager=cold,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(source_sequence=2),
        )
    assert ahead.value.field == "sequence"
    assert ahead.value.reason == "config_ahead"


def test_admission_order_and_replay_precedence(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)

    with pytest.raises(BrainvisionIngressError) as stream:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_tamper_observation_id(
                _observation(stream_identity="camera-other", adapter_contract_id="other-v1")
            ),
        )
    _assert_ingress_error(stream, "stream_identity", "stream_identity_mismatch")

    with pytest.raises(BrainvisionIngressError) as contract:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_tamper_observation_id(_observation(adapter_contract_id="other-v1")),
        )
    _assert_ingress_error(contract, "adapter_contract_id", "adapter_contract_mismatch")

    admit_firsthand_visual_observation(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(source_sequence=0),
    )
    with pytest.raises(BrainvisionIngressError) as stale:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_tamper_observation_id(_observation(source_sequence=0)),
        )
    _assert_ingress_error(stale, "source_sequence", "refused_replay")

    fresh_manager, _, _, _ = _environment(tmp_path / "fresh")
    with pytest.raises(BrainvisionIngressError) as forged:
        admit_firsthand_visual_observation(
            lifecycle_manager=fresh_manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_tamper_observation_id(_observation(source_sequence=4)),
        )
    _assert_ingress_error(forged, "observation_id", "invalid_observation_id")


@pytest.mark.parametrize(
    ("observation", "field", "reason"),
    (
        (
            _observation(stream_identity="camera-other"),
            "stream_identity",
            "stream_identity_mismatch",
        ),
        (
            _observation(adapter_contract_id="descriptor-other"),
            "adapter_contract_id",
            "adapter_contract_mismatch",
        ),
    ),
)
def test_lineage_mismatch_refusals_preserve_reconciled_state(
    tmp_path: Path,
    observation: FirsthandVisualObservationV1,
    field: str,
    reason: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    before = _ingress_state_snapshot(tmp_path, manager)
    calls = 0

    def unexpected_update(**_: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("operator must not run")

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", unexpected_update)
    with pytest.raises(BrainvisionIngressError) as refusal:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=observation,
        )
    _assert_ingress_error(refusal, field, reason)
    assert calls == 0
    _assert_ingress_state_unchanged(tmp_path, manager, before)


@pytest.mark.parametrize("replayed_sequence", (5, 4))
def test_equal_and_below_watermark_replay_refusals_preserve_state(
    tmp_path: Path,
    replayed_sequence: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    admit_firsthand_visual_observation(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(source_sequence=5),
    )
    before = _ingress_state_snapshot(tmp_path, manager)
    calls = 0

    def unexpected_update(**_: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("operator must not run")

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", unexpected_update)
    with pytest.raises(BrainvisionIngressError) as refusal:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(source_sequence=replayed_sequence),
        )
    _assert_ingress_error(refusal, "source_sequence", "refused_replay")
    assert calls == 0
    _assert_ingress_state_unchanged(tmp_path, manager, before)


def test_fresh_forged_identity_refusal_preserves_reconciled_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    before = _ingress_state_snapshot(tmp_path, manager)
    calls = 0

    def unexpected_update(**_: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("operator must not run")

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", unexpected_update)
    with pytest.raises(BrainvisionIngressError) as refusal:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_tamper_observation_id(_observation(source_sequence=4)),
        )
    _assert_ingress_error(refusal, "observation_id", "invalid_observation_id")
    assert calls == 0
    _assert_ingress_state_unchanged(tmp_path, manager, before)


def test_sequence_gaps_are_admitted(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    receipt = admit_firsthand_visual_observation(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(source_sequence=9),
    )
    assert receipt.source_sequence == 9
    assert load_brainvision_configuration(
        tmp_path, WORKSPACE_ID, AGENT_ID
    ).last_accepted_source_sequence == 9


def test_exactly_one_elapsed_evolution_and_event_time_cutoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, clock, _, _ = _environment(tmp_path)
    seeded = update_vhe_state(
        state=fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
    ).state
    _runtime(manager).vhe_state = seeded
    sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    write_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID, replace(sidecar, vhe_state=seeded))

    clock.now = VISUAL_TIME_NS_PER_SECOND
    expected = update_vhe_state_with_character_modulation(
        state=seeded,
        descriptor=DB,
        semantic_event_class="detector:scene_change",
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=VISUAL_TIME_NS_PER_SECOND,
        theta=0,
    )
    no_elapsed = update_vhe_state_with_character_modulation(
        state=seeded,
        descriptor=DB,
        semantic_event_class="detector:scene_change",
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
        theta=0,
    )
    calls = 0
    real_update = ingress_module.update_vhe_state_with_character_modulation

    def count_update(**kwargs: object):
        nonlocal calls
        calls += 1
        return real_update(**kwargs)

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", count_update)
    receipt = admit_firsthand_visual_observation(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(
            descriptor=DB,
            semantic_event_class="detector:scene_change",
        ),
    )
    committed = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)

    assert calls == 1
    assert committed.vhe_state == expected.state
    assert committed.vhe_state != no_elapsed.state
    assert committed.committed_active_time_ns == VISUAL_TIME_NS_PER_SECOND
    assert receipt.committed_active_time_ns == VISUAL_TIME_NS_PER_SECOND
    assert expected.event_active_time_ns == VISUAL_TIME_NS_PER_SECOND


@pytest.mark.parametrize("theta", (-1, 0, 1))
def test_all_frozen_theta_values_use_the_phase7_operator(
    tmp_path: Path,
    theta: int,
) -> None:
    manager, _, _, _ = _environment(tmp_path, theta=theta)
    expected = update_vhe_state_with_character_modulation(
        state=fresh_vhe_state(),
        descriptor=DA,
        semantic_event_class=None,
        prior_committed_active_time_ns=0,
        elapsed_active_time_ns=0,
        theta=theta,
    )
    receipt = admit_firsthand_visual_observation(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(),
    )
    committed = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)

    assert committed.vhe_state == expected.state
    assert receipt.committed_active_time_ns == expected.event_active_time_ns
    if theta == 0:
        baseline = update_vhe_state(
            state=fresh_vhe_state(),
            descriptor=DA,
            semantic_event_class=None,
            prior_committed_active_time_ns=0,
            elapsed_active_time_ns=0,
        )
        assert expected == baseline


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("adapter_id", "adapter-b"),
        ("confidence_q", 750_000),
        ("source_capture_time_unix_ns", 987_654_321),
        ("world_event_id", "world-event-7"),
    ),
)
def test_provenance_metadata_is_dynamically_inert(
    tmp_path: Path,
    field: str,
    value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    left_manager, left_clock, _, _ = _environment(tmp_path / "left")
    right_manager, right_clock, _, _ = _environment(tmp_path / "right")
    left_clock.now = 41
    right_clock.now = 41
    changed = {field: value}
    captured = []
    real_update = ingress_module.update_vhe_state_with_character_modulation

    def capture_update(**kwargs: object):
        result = real_update(**kwargs)
        captured.append((kwargs["theta"], result.write_gate_q))
        return result

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", capture_update)

    left_receipt = admit_firsthand_visual_observation(
        lifecycle_manager=left_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(),
    )
    right_receipt = admit_firsthand_visual_observation(
        lifecycle_manager=right_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(**changed),
    )

    left_sidecar = load_vhe_sidecar(tmp_path / "left", WORKSPACE_ID, AGENT_ID)
    right_sidecar = load_vhe_sidecar(tmp_path / "right", WORKSPACE_ID, AGENT_ID)
    assert left_sidecar.vhe_state == right_sidecar.vhe_state
    assert left_sidecar.committed_active_time_ns == right_sidecar.committed_active_time_ns
    assert left_receipt.committed_active_time_ns == right_receipt.committed_active_time_ns
    assert left_manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID).configuration.theta == 0
    assert right_manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID).configuration.theta == 0
    assert captured == [(0, 1_000_000), (0, 1_000_000)]


def test_twin_lineages_isolate_sequence_identity_and_adapter_contract_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_manager, first_clock, _, _ = _environment(tmp_path / "first")
    second_manager, second_clock, _, _ = _environment(
        tmp_path / "second",
        adapter_contract_id="descriptor-v2",
    )
    first_clock.now = 19
    second_clock.now = 19
    captured = []
    real_update = ingress_module.update_vhe_state_with_character_modulation

    def capture_update(**kwargs: object):
        result = real_update(**kwargs)
        captured.append((kwargs["theta"], result.write_gate_q))
        return result

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", capture_update)

    first = admit_firsthand_visual_observation(
        lifecycle_manager=first_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(source_sequence=0),
    )
    second = admit_firsthand_visual_observation(
        lifecycle_manager=second_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(source_sequence=23, adapter_contract_id="descriptor-v2"),
    )
    first_sidecar = load_vhe_sidecar(tmp_path / "first", WORKSPACE_ID, AGENT_ID)
    second_sidecar = load_vhe_sidecar(tmp_path / "second", WORKSPACE_ID, AGENT_ID)

    assert first_sidecar.vhe_state == second_sidecar.vhe_state
    assert first.committed_active_time_ns == second.committed_active_time_ns == 19
    assert first_manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID).configuration.theta == 0
    assert second_manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID).configuration.theta == 0
    assert captured == [(0, 1_000_000), (0, 1_000_000)]


def test_semantic_event_only_reaches_the_frozen_register_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    null_manager, _, _, _ = _environment(tmp_path / "null")
    semantic_manager, _, _, _ = _environment(tmp_path / "semantic")
    write_gates: list[int] = []
    real_update = ingress_module.update_vhe_state_with_character_modulation

    def capture_update(**kwargs: object):
        result = real_update(**kwargs)
        write_gates.append(result.write_gate_q)
        return result

    monkeypatch.setattr(
        ingress_module,
        "update_vhe_state_with_character_modulation",
        capture_update,
    )
    admit_firsthand_visual_observation(
        lifecycle_manager=null_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(semantic_event_class=None),
    )
    admit_firsthand_visual_observation(
        lifecycle_manager=semantic_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(semantic_event_class="detector:scene_change"),
    )
    null_state = load_vhe_sidecar(tmp_path / "null", WORKSPACE_ID, AGENT_ID).vhe_state
    semantic_state = load_vhe_sidecar(
        tmp_path / "semantic", WORKSPACE_ID, AGENT_ID
    ).vhe_state

    assert null_state.semantic_register.entries == ()
    assert semantic_state.fast_trace == null_state.fast_trace
    assert semantic_state.persistent_context == null_state.persistent_context
    assert semantic_state.semantic_register.open_semantic_event_class == "detector:scene_change"
    assert write_gates == [1_000_000, 1_000_000]


def test_successor_derivation_failure_preserves_state_without_commit_or_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    before = _ingress_state_snapshot(tmp_path, manager)
    commit_calls = 0

    def fail_update(**_: object) -> object:
        raise RuntimeError("forced phase-7 derivation failure")

    def unexpected_commit(*_: object, **__: object) -> object:
        nonlocal commit_calls
        commit_calls += 1
        raise AssertionError("commit must not run")

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", fail_update)
    monkeypatch.setattr(
        lifecycle_module.BrainvisionActiveTransaction,
        "commit_successor",
        unexpected_commit,
    )
    with pytest.raises(BrainvisionIngressError) as refusal:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    _assert_ingress_error(refusal, "successor", "successor_derivation_failure")
    assert commit_calls == 0
    _assert_ingress_state_unchanged(tmp_path, manager, before)


def test_successor_time_failure_preserves_reconciled_durable_and_runtime_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    before_bytes = _durable_bytes(tmp_path)
    before_runtime = _runtime(manager).vhe_state
    real_update = ingress_module.update_vhe_state_with_character_modulation

    def wrong_event_time(**kwargs: object):
        return replace(real_update(**kwargs), event_active_time_ns=1)

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", wrong_event_time)
    with pytest.raises(BrainvisionIngressError) as refusal:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    _assert_ingress_error(refusal, "event_active_time_ns", "successor_derivation_failure")
    assert _durable_bytes(tmp_path) == before_bytes
    assert _runtime(manager).vhe_state == before_runtime


def test_sidecar_failure_preserves_state_without_a_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    before_bytes = _durable_bytes(tmp_path)
    before_runtime = _runtime(manager).vhe_state

    def fail_sidecar(*_: object, **__: object) -> None:
        raise OSError("sidecar failure")

    monkeypatch.setattr(lifecycle_module, "write_vhe_sidecar", fail_sidecar)
    with pytest.raises(BrainvisionLifecycleError) as failure:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    assert failure.value.reason == "durability_failure"
    assert _durable_bytes(tmp_path) == before_bytes
    assert _runtime(manager).vhe_state == before_runtime


def test_successful_admission_delegates_sidecar_then_configuration_then_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    before_state = _runtime(manager).vhe_state
    writes: list[str] = []
    real_sidecar = lifecycle_module.write_vhe_sidecar
    real_configuration = lifecycle_module.write_brainvision_configuration

    def record_sidecar(*args: object, **kwargs: object) -> None:
        writes.append("sidecar")
        assert _runtime(manager).vhe_state == before_state
        real_sidecar(*args, **kwargs)

    def record_configuration(*args: object, **kwargs: object) -> None:
        writes.append("configuration")
        assert _runtime(manager).vhe_state == before_state
        real_configuration(*args, **kwargs)

    monkeypatch.setattr(lifecycle_module, "write_vhe_sidecar", record_sidecar)
    monkeypatch.setattr(lifecycle_module, "write_brainvision_configuration", record_configuration)
    receipt = admit_firsthand_visual_observation(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        observation=_observation(),
    )

    assert writes == ["sidecar", "configuration"]
    assert _runtime(manager).configuration.last_accepted_source_sequence == 0
    assert _runtime(manager).vhe_state != before_state
    assert receipt.source_sequence == 0


def test_configuration_failure_recovers_without_duplicate_successor_application(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    calls = 0
    real_update = ingress_module.update_vhe_state_with_character_modulation

    def count_update(**kwargs: object):
        nonlocal calls
        calls += 1
        return real_update(**kwargs)

    def fail_configuration(*_: object, **__: object) -> None:
        raise OSError("configuration failure")

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", count_update)
    monkeypatch.setattr(lifecycle_module, "write_brainvision_configuration", fail_configuration)
    with pytest.raises(BrainvisionLifecycleError) as failure:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    assert failure.value.reason == "recovery_required"
    assert failure.value.durable_committed is True
    assert manager.runtime_count == 0
    assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).accepted_source_sequence == 0
    assert calls == 1

    monkeypatch.setattr(lifecycle_module, "write_brainvision_configuration", write_brainvision_configuration)
    with pytest.raises(BrainvisionIngressError) as replay:
        admit_firsthand_visual_observation(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
    _assert_ingress_error(replay, "source_sequence", "refused_replay")
    assert calls == 1
    assert load_brainvision_configuration(
        tmp_path, WORKSPACE_ID, AGENT_ID
    ).last_accepted_source_sequence == 0


def test_sidecar_ahead_recovery_before_refusal_is_not_an_ingress_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, clock, identities, locks = _environment(tmp_path)
    original_sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
    ahead_sidecar = replace(original_sidecar, accepted_source_sequence=4)
    write_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID, ahead_sidecar)
    before_sidecar_bytes = Path(vhe_sidecar_path(tmp_path, WORKSPACE_ID, AGENT_ID)).read_bytes()
    before_configuration = load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID)
    cold = _cold_manager(tmp_path, clock, identities, locks)
    calls = 0

    def unexpected_update(**_: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("operator must not run")

    monkeypatch.setattr(ingress_module, "update_vhe_state_with_character_modulation", unexpected_update)
    with pytest.raises(BrainvisionIngressError) as refusal:
        admit_firsthand_visual_observation(
            lifecycle_manager=cold,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(stream_identity="camera-other", source_sequence=5),
        )
    _assert_ingress_error(refusal, "stream_identity", "stream_identity_mismatch")
    assert calls == 0
    assert Path(vhe_sidecar_path(tmp_path, WORKSPACE_ID, AGENT_ID)).read_bytes() == before_sidecar_bytes
    repaired = load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID)
    assert before_configuration.last_accepted_source_sequence == -1
    assert repaired.last_accepted_source_sequence == 4
    assert cold.runtime_count == 1
