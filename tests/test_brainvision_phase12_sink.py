"""Phase-12 commit-time null/test-sink qualification coverage."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
import inspect
from pathlib import Path
from threading import Event, Thread

import pytest

import brainvision.ingress as ingress_module
import brainvision.sink as sink_module
from brainvision.configuration import (
    brainvision_configuration_path,
    load_brainvision_configuration,
    write_brainvision_configuration,
)
from brainvision.fixtures import DA
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
from brainvision.projection import BrainvisionProjectionV1, project_vhe_state
from brainvision.sink import Phase12IngressHost, Phase12SinkError, Phase12SinkMetrics
from brainvision.vhe_sidecar import load_vhe_sidecar, vhe_sidecar_path
from torment_service.agent_locks import AgentLockManager
from torment_service.identity import IdentityStore


WORKSPACE_ID = "workspace-a"
AGENT_ID = "agent-a"
STREAM_ID = "camera-main"
CONTRACT_ID = "descriptor-v1"
EXPECTED_PAYLOAD_FIELDS = {
    "schema_id",
    "projection_id",
    "operator_id",
    "current_activity_code",
    "retained_history_code",
    "present_history_relation_code",
    "trajectory_code",
    "open_event_class",
    "recurrence_code",
}


class ManualMonotonic:
    def __init__(self) -> None:
        self.now = 0

    def __call__(self) -> int:
        return self.now


class RecordingSink:
    def __init__(self) -> None:
        self.records: list[tuple[FirsthandVisualAdmissionReceipt, dict[str, object]]] = []

    def on_projection(
        self,
        receipt: FirsthandVisualAdmissionReceipt,
        projection_payload: dict[str, object],
    ) -> None:
        self.records.append((receipt, projection_payload))


class ThrowingSink:
    def __init__(self) -> None:
        self.calls = 0

    def on_projection(
        self,
        receipt: FirsthandVisualAdmissionReceipt,
        projection_payload: dict[str, object],
    ) -> None:
        del receipt, projection_payload
        self.calls += 1
        raise RuntimeError("test-only sink failure")


def _environment(
    root: Path,
    *,
    agent_id: str = AGENT_ID,
) -> tuple[BrainvisionLifecycleManager, ManualMonotonic, IdentityStore, AgentLockManager]:
    clock = ManualMonotonic()
    identities = IdentityStore(str(root))
    identities.create(WORKSPACE_ID, agent_id)
    locks = AgentLockManager()
    manager = BrainvisionLifecycleManager(
        data_dir=root,
        identity_store=identities,
        lock_manager=locks,
        monotonic_ns_source=clock,
    )
    manager.configure_brainvision(
        WORKSPACE_ID,
        agent_id,
        STREAM_ID,
        CONTRACT_ID,
        0,
    )
    manager.enable(WORKSPACE_ID, agent_id)
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
    descriptor: object = DA,
    stream_identity: str = STREAM_ID,
    adapter_contract_id: str = CONTRACT_ID,
    semantic_event_class: str | None = None,
) -> FirsthandVisualObservationV1:
    return FirsthandVisualObservationV1(
        provenance_type=ObservationProvenanceType.FIRSTHAND_VISUAL,
        stream_identity=stream_identity,
        source_sequence=source_sequence,
        observation_id=derive_observation_id(stream_identity, source_sequence),
        descriptor=descriptor,
        adapter_id="adapter-a",
        adapter_contract_id=adapter_contract_id,
        semantic_event_class=semantic_event_class,
    )


def _durable_bytes(root: Path, agent_id: str = AGENT_ID) -> tuple[bytes, bytes]:
    return (
        Path(brainvision_configuration_path(root, WORKSPACE_ID, agent_id)).read_bytes(),
        Path(vhe_sidecar_path(root, WORKSPACE_ID, agent_id)).read_bytes(),
    )


def _payload_canonical_bytes(payload: dict[str, object]) -> bytes:
    projection = BrainvisionProjectionV1(
        current_activity_code=payload["current_activity_code"],
        retained_history_code=payload["retained_history_code"],
        present_history_relation_code=payload["present_history_relation_code"],
        trajectory_code=payload["trajectory_code"],
        open_event_class=payload["open_event_class"],
        recurrence_code=payload["recurrence_code"],
    )
    assert projection.to_dict() == payload
    return projection.to_canonical_json_bytes()


def _metrics(host: Phase12IngressHost) -> Phase12SinkMetrics:
    result = host.metrics_snapshot()
    assert type(result) is Phase12SinkMetrics
    return result


def test_null_path_is_direct_phase11_ingress_without_projection_or_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host_manager, host_clock, _, _ = _environment(tmp_path / "host")
    direct_manager, direct_clock, _, _ = _environment(tmp_path / "direct")
    host_clock.now = direct_clock.now = 37
    host = Phase12IngressHost(
        lifecycle_manager=host_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )
    calls = 0

    def unexpected_projection(*_: object, **__: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("null path must not construct a projection")

    monkeypatch.setattr(sink_module, "project_vhe_state", unexpected_projection)
    try:
        hosted = host.admit(_observation())
        direct = admit_firsthand_visual_observation(
            lifecycle_manager=direct_manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            observation=_observation(),
        )
        assert hosted == direct
        assert _durable_bytes(tmp_path / "host") == _durable_bytes(tmp_path / "direct")
        assert calls == 0
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=0,
            sink_delivery_failures_total=0,
            projection_construction_failures_total=0,
        )
    finally:
        host.close()


def test_success_delivers_one_fresh_exact_phase5_payload_and_unchanged_receipt(
    tmp_path: Path,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    observation = _observation(semantic_event_class="detector:scene_change")
    try:
        receipt = host.admit(observation)
        assert len(sink.records) == 1
        delivered_receipt, payload = sink.records[0]
        assert delivered_receipt is receipt
        assert receipt == FirsthandVisualAdmissionReceipt(
            observation_id=observation.observation_id,
            source_sequence=0,
            committed_active_time_ns=0,
        )
        assert set(payload) == EXPECTED_PAYLOAD_FIELDS
        assert not ({"workspace_id", "agent_id", "theta", "vhe_state"} & set(payload))
        committed = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
        assert payload == project_vhe_state(committed.vhe_state, 0).to_dict()
        assert _payload_canonical_bytes(payload) == project_vhe_state(
            committed.vhe_state, 0
        ).to_canonical_json_bytes()
        assert _metrics(host).sink_invocations_total == 1
    finally:
        host.close()


def test_projection_is_constructed_under_agent_lock_and_callback_is_not(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, locks = _environment(tmp_path)
    agent_lock = locks.agent_lock(WORKSPACE_ID, AGENT_ID)
    assert callable(agent_lock._is_owned)
    projection_lock_states: list[bool] = []
    callback_lock_states: list[bool] = []
    real_construct = sink_module._construct_committed_projection

    class LockProbeSink:
        def on_projection(
            self,
            receipt: FirsthandVisualAdmissionReceipt,
            projection_payload: dict[str, object],
        ) -> None:
            del receipt, projection_payload
            callback_lock_states.append(agent_lock._is_owned())

    def capture_under_lock(snapshot: object) -> dict[str, object]:
        projection_lock_states.append(agent_lock._is_owned())
        return real_construct(snapshot)

    monkeypatch.setattr(sink_module, "_construct_committed_projection", capture_under_lock)
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=LockProbeSink(),
    )
    try:
        host.admit(_observation())
        assert projection_lock_states == [True]
        assert callback_lock_states == [False]
    finally:
        host.close()


def test_zero_elapsed_projection_is_fixed_before_callback_and_is_detached(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, clock, _, _ = _environment(tmp_path)
    clock.now = 11
    sink = RecordingSink()
    elapsed_values: list[int] = []
    real_project = sink_module.project_vhe_state

    def capture_elapsed(state: object, elapsed_active_time_ns: int) -> object:
        elapsed_values.append(elapsed_active_time_ns)
        return real_project(state, elapsed_active_time_ns)

    monkeypatch.setattr(sink_module, "project_vhe_state", capture_elapsed)
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    try:
        host.admit(_observation())
        payload = sink.records[0][1]
        payload["test_only_mutation"] = True
        assert elapsed_values == [0]
        assert manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID).vhe_state == load_vhe_sidecar(
            tmp_path, WORKSPACE_ID, AGENT_ID
        ).vhe_state
        assert "test_only_mutation" not in project_vhe_state(
            load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).vhe_state, 0
        ).to_dict()
    finally:
        host.close()


def test_same_agent_delivery_gate_preserves_commit_order_under_paused_callback(
    tmp_path: Path,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    started = Event()
    release = Event()
    records: list[int] = []
    errors: list[BaseException] = []

    class PausingSink:
        def on_projection(
            self,
            receipt: FirsthandVisualAdmissionReceipt,
            projection_payload: dict[str, object],
        ) -> None:
            del projection_payload
            records.append(receipt.source_sequence)
            if receipt.source_sequence == 0:
                started.set()
                assert release.wait(timeout=5)

    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=PausingSink(),
    )

    def admit(sequence: int) -> None:
        try:
            host.admit(_observation(source_sequence=sequence))
        except BaseException as error:
            errors.append(error)

    first = Thread(target=admit, args=(0,))
    second = Thread(target=admit, args=(1,))
    try:
        first.start()
        assert started.wait(timeout=5)
        second.start()
        release.set()
        first.join(timeout=5)
        second.join(timeout=5)
        assert not first.is_alive()
        assert not second.is_alive()
        assert errors == []
        assert records == [0, 1]
        assert _metrics(host).sink_invocations_total == 2
    finally:
        release.set()
        host.close()


@pytest.mark.parametrize(
    ("sink", "expected_field", "expected_reason"),
    (
        (object(), "sink", "invalid_sink"),
        (type("MissingCallback", (), {})(), "sink", "invalid_sink"),
        (type("NonCallableCallback", (), {"on_projection": None})(), "sink", "invalid_sink"),
    ),
)
def test_invalid_sink_is_refused_at_construction_without_brainvision_mutation(
    tmp_path: Path,
    sink: object,
    expected_field: str,
    expected_reason: str,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    before = _durable_bytes(tmp_path)
    with pytest.raises(Phase12SinkError) as refusal:
        Phase12IngressHost(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
            sink=sink,
        )
    assert refusal.value.field == expected_field
    assert refusal.value.reason == expected_reason
    assert _durable_bytes(tmp_path) == before


def test_callable_sink_and_none_are_accepted_and_host_has_no_agent_parameter(
    tmp_path: Path,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    callable_host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=RecordingSink(),
    )
    try:
        assert tuple(inspect.signature(callable_host.admit).parameters) == ("observation",)
    finally:
        callable_host.close()
    none_host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )
    none_host.close()


def test_same_lineage_is_unique_process_local_and_releasable(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    original = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )
    before = _durable_bytes(tmp_path)
    try:
        with pytest.raises(Phase12SinkError) as duplicate:
            Phase12IngressHost(
                lifecycle_manager=manager,
                workspace_id=WORKSPACE_ID,
                agent_id=AGENT_ID,
            )
        assert duplicate.value.field == "host"
        assert duplicate.value.reason == "duplicate_lineage"
        assert _durable_bytes(tmp_path) == before
        original.close()
        replacement = Phase12IngressHost(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
        )
        replacement.close()
    finally:
        original.close()


def test_distinct_agents_and_distinct_manager_instances_are_distinct_lineages(
    tmp_path: Path,
) -> None:
    first, _, _, _ = _environment(tmp_path / "first")
    second, _, _, _ = _environment(tmp_path / "second")
    other_agent, _, _, _ = _environment(tmp_path / "other-agent", agent_id="agent-b")
    first_host = Phase12IngressHost(
        lifecycle_manager=first,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )
    second_host = Phase12IngressHost(
        lifecycle_manager=second,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )
    other_agent_host = Phase12IngressHost(
        lifecycle_manager=other_agent,
        workspace_id=WORKSPACE_ID,
        agent_id="agent-b",
    )
    first_host.close()
    second_host.close()
    other_agent_host.close()


@pytest.mark.parametrize(
    "observation",
    (
        _observation(stream_identity="other-stream"),
        _observation(adapter_contract_id="other-contract"),
    ),
)
def test_rejections_do_not_construct_or_deliver_or_change_metrics(
    tmp_path: Path,
    observation: FirsthandVisualObservationV1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    before = _durable_bytes(tmp_path)
    projections = 0

    def unexpected_projection(*_: object, **__: object) -> object:
        nonlocal projections
        projections += 1
        raise AssertionError("refusal must precede projection")

    monkeypatch.setattr(sink_module, "project_vhe_state", unexpected_projection)
    try:
        with pytest.raises(BrainvisionIngressError):
            host.admit(observation)
        assert _durable_bytes(tmp_path) == before
        assert sink.records == []
        assert projections == 0
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=0,
            sink_delivery_failures_total=0,
            projection_construction_failures_total=0,
        )
    finally:
        host.close()


def test_replay_refusal_has_no_projection_delivery_or_second_successor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    try:
        host.admit(_observation())
        before = _durable_bytes(tmp_path)
        with pytest.raises(BrainvisionIngressError) as replay:
            host.admit(_observation())
        assert replay.value.field == "source_sequence"
        assert replay.value.reason == "refused_replay"
        assert _durable_bytes(tmp_path) == before
        assert len(sink.records) == 1
        assert _metrics(host).sink_invocations_total == 1
    finally:
        host.close()


def test_projection_construction_failure_keeps_commit_and_receipt_without_delivery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )

    def fail_projection(*_: object, **__: object) -> object:
        raise RuntimeError("injected post-commit projection failure")

    monkeypatch.setattr(sink_module, "project_vhe_state", fail_projection)
    try:
        receipt = host.admit(_observation())
        assert receipt.source_sequence == 0
        assert load_brainvision_configuration(
            tmp_path, WORKSPACE_ID, AGENT_ID
        ).last_accepted_source_sequence == 0
        assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).accepted_source_sequence == 0
        assert sink.records == []
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=0,
            sink_delivery_failures_total=0,
            projection_construction_failures_total=1,
        )
    finally:
        host.close()


def test_delivery_failure_keeps_commit_and_receipt_without_retry(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = ThrowingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    try:
        receipt = host.admit(_observation())
        assert receipt.source_sequence == 0
        assert sink.calls == 1
        assert load_brainvision_configuration(
            tmp_path, WORKSPACE_ID, AGENT_ID
        ).last_accepted_source_sequence == 0
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=0,
            sink_delivery_failures_total=1,
            projection_construction_failures_total=0,
        )
    finally:
        host.close()


def test_sink_absence_success_and_failure_leave_identical_committed_artifacts(
    tmp_path: Path,
) -> None:
    null_manager, null_clock, _, _ = _environment(tmp_path / "null")
    success_manager, success_clock, _, _ = _environment(tmp_path / "success")
    failure_manager, failure_clock, _, _ = _environment(tmp_path / "failure")
    null_clock.now = success_clock.now = failure_clock.now = 47
    success_sink = RecordingSink()
    failure_sink = ThrowingSink()
    null_host = Phase12IngressHost(
        lifecycle_manager=null_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )
    success_host = Phase12IngressHost(
        lifecycle_manager=success_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=success_sink,
    )
    failure_host = Phase12IngressHost(
        lifecycle_manager=failure_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=failure_sink,
    )
    try:
        null_receipt = null_host.admit(_observation())
        success_receipt = success_host.admit(_observation())
        failure_receipt = failure_host.admit(_observation())
        assert null_receipt == success_receipt == failure_receipt
        assert _durable_bytes(tmp_path / "null") == _durable_bytes(tmp_path / "success")
        assert _durable_bytes(tmp_path / "null") == _durable_bytes(tmp_path / "failure")
        assert _payload_canonical_bytes(success_sink.records[0][1]) == project_vhe_state(
            load_vhe_sidecar(tmp_path / "success", WORKSPACE_ID, AGENT_ID).vhe_state,
            0,
        ).to_canonical_json_bytes()
        assert failure_sink.calls == 1
    finally:
        null_host.close()
        success_host.close()
        failure_host.close()


def test_canonical_projection_bytes_and_receipt_triples_are_deterministic(
    tmp_path: Path,
) -> None:
    left_manager, left_clock, _, _ = _environment(tmp_path / "left")
    right_manager, right_clock, _, _ = _environment(tmp_path / "right")
    left_clock.now = right_clock.now = 29
    left_sink = RecordingSink()
    right_sink = RecordingSink()
    left = Phase12IngressHost(
        lifecycle_manager=left_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=left_sink,
    )
    right = Phase12IngressHost(
        lifecycle_manager=right_manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=right_sink,
    )
    try:
        left_receipt = left.admit(_observation())
        right_receipt = right.admit(_observation())
        assert (
            left_receipt.observation_id,
            left_receipt.source_sequence,
            left_receipt.committed_active_time_ns,
        ) == (
            right_receipt.observation_id,
            right_receipt.source_sequence,
            right_receipt.committed_active_time_ns,
        )
        assert _payload_canonical_bytes(left_sink.records[0][1]) == _payload_canonical_bytes(
            right_sink.records[0][1]
        )
    finally:
        left.close()
        right.close()


def test_metrics_are_immutable_process_local_and_not_persisted(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=RecordingSink(),
    )
    before = _durable_bytes(tmp_path)
    try:
        host.admit(_observation())
        metrics = _metrics(host)
        assert metrics.sink_invocations_total == 1
        with pytest.raises(FrozenInstanceError):
            metrics.sink_invocations_total = 0
        assert _durable_bytes(tmp_path) != before
        committed = _durable_bytes(tmp_path)
        assert _metrics(host) == metrics
        assert _durable_bytes(tmp_path) == committed
        assert not hasattr(host, "get_projection_now")
        assert not hasattr(host, "project_as_of")
    finally:
        host.close()


def test_lifecycle_operations_do_not_emit_sink_records(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    try:
        manager.suspend(WORKSPACE_ID, AGENT_ID)
        manager.resume(WORKSPACE_ID, AGENT_ID)
        manager.reset(WORKSPACE_ID, AGENT_ID)
        manager.disable(WORKSPACE_ID, AGENT_ID)
        assert sink.records == []
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=0,
            sink_delivery_failures_total=0,
            projection_construction_failures_total=0,
        )
    finally:
        host.close()


def test_injected_post_commit_pre_delivery_window_has_no_backfill_or_duplicate_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, clock, identities, locks = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )

    def interrupt_after_commit(*_: object, **__: object) -> object:
        raise RuntimeError("test-only post-commit pre-delivery interruption")

    monkeypatch.setattr(sink_module, "project_vhe_state", interrupt_after_commit)
    try:
        receipt = host.admit(_observation())
        assert receipt.source_sequence == 0
        assert sink.records == []
        assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).accepted_source_sequence == 0
        cold = _cold_manager(tmp_path, clock, identities, locks)
        with pytest.raises(BrainvisionIngressError) as replay:
            admit_firsthand_visual_observation(
                lifecycle_manager=cold,
                workspace_id=WORKSPACE_ID,
                agent_id=AGENT_ID,
                observation=_observation(),
            )
        assert replay.value.reason == "refused_replay"
        assert sink.records == []
        assert load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID).accepted_source_sequence == 0
    finally:
        host.close()


def test_closed_host_refuses_without_mutation_and_allows_replacement(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )
    host.close()
    before = _durable_bytes(tmp_path)
    with pytest.raises(Phase12SinkError) as refusal:
        host.admit(_observation())
    assert refusal.value.reason == "closed"
    assert _durable_bytes(tmp_path) == before
    replacement = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
    )
    replacement.close()


def test_static_isolation_and_public_surface_are_limited_to_phase12_boundary() -> None:
    tree = ast.parse(inspect.getsource(sink_module))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    assert imported_modules <= {
        "__future__",
        "dataclasses",
        "threading",
        "typing",
        "weakref",
        "brainvision.ingress",
        "brainvision.lifecycle",
        "brainvision.observation",
        "brainvision.projection",
    }
    assert sink_module.__all__ == (
        "Phase12IngressHost",
        "Phase12SinkError",
        "Phase12SinkMetrics",
    )
    source = inspect.getsource(sink_module)
    for forbidden in (
        "torment_service.fabric",
        "MemoryGraph",
        "CognitiveCore",
        "CharacterSeed",
        "CharacterState",
        "Hivermind",
        "AgentRunner",
        "generate(",
    ):
        assert forbidden not in source


def test_private_phase11_capture_seam_is_not_exported_or_a_raw_state_api() -> None:
    assert "_admit_firsthand_visual_observation_with_committed_snapshot" not in ingress_module.__all__
    assert "BrainvisionRuntimeSnapshot" not in ingress_module.__all__
    assert not hasattr(Phase12IngressHost, "runtime_snapshot")
    assert not hasattr(Phase12IngressHost, "state_snapshot")


def test_same_host_reentrant_admission_is_refused_before_phase11_and_then_recovers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    host_ref: dict[str, Phase12IngressHost] = {}
    nested_errors: list[Phase12SinkError] = []
    nested_durable_bytes: list[tuple[bytes, bytes]] = []
    callbacks: list[int] = []
    projection_calls = 0
    real_project = sink_module.project_vhe_state

    class ReentrantSink:
        def on_projection(
            self,
            receipt: FirsthandVisualAdmissionReceipt,
            projection_payload: dict[str, object],
        ) -> None:
            del projection_payload
            callbacks.append(receipt.source_sequence)
            if receipt.source_sequence != 0:
                return
            before = _durable_bytes(tmp_path)
            with pytest.raises(Phase12SinkError) as refusal:
                host_ref["host"].admit(_observation(source_sequence=1))
            nested_errors.append(refusal.value)
            nested_durable_bytes.extend((before, _durable_bytes(tmp_path)))

    def count_projection(*args: object, **kwargs: object) -> object:
        nonlocal projection_calls
        projection_calls += 1
        return real_project(*args, **kwargs)

    monkeypatch.setattr(sink_module, "project_vhe_state", count_projection)
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=ReentrantSink(),
    )
    host_ref["host"] = host
    try:
        outer = host.admit(_observation(source_sequence=0))
        assert outer.source_sequence == 0
        assert len(nested_errors) == 1
        assert nested_errors[0].field == "host"
        assert nested_errors[0].reason == "reentrant_admission"
        assert nested_durable_bytes[0] == nested_durable_bytes[1]
        assert load_brainvision_configuration(
            tmp_path, WORKSPACE_ID, AGENT_ID
        ).last_accepted_source_sequence == 0
        assert callbacks == [0]
        assert projection_calls == 1
        assert _metrics(host).sink_invocations_total == 1

        later = host.admit(_observation(source_sequence=1))
        assert later.source_sequence == 1
        assert callbacks == [0, 1]
        assert projection_calls == 2
        assert _metrics(host).sink_invocations_total == 2
    finally:
        host.close()


def test_reentrant_close_is_refused_without_releasing_lineage_until_outer_delivery_finishes(
    tmp_path: Path,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    host_ref: dict[str, Phase12IngressHost] = {}
    close_errors: list[Phase12SinkError] = []

    class ClosingSink:
        def on_projection(
            self,
            receipt: FirsthandVisualAdmissionReceipt,
            projection_payload: dict[str, object],
        ) -> None:
            del receipt, projection_payload
            with pytest.raises(Phase12SinkError) as close_refusal:
                host_ref["host"].close()
            close_errors.append(close_refusal.value)
            with pytest.raises(Phase12SinkError) as duplicate:
                Phase12IngressHost(
                    lifecycle_manager=manager,
                    workspace_id=WORKSPACE_ID,
                    agent_id=AGENT_ID,
                )
            assert duplicate.value.reason == "duplicate_lineage"

    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=ClosingSink(),
    )
    host_ref["host"] = host
    try:
        host.admit(_observation())
        assert len(close_errors) == 1
        assert close_errors[0].field == "host"
        assert close_errors[0].reason == "close_while_active"
        host.close()
        replacement = Phase12IngressHost(
            lifecycle_manager=manager,
            workspace_id=WORKSPACE_ID,
            agent_id=AGENT_ID,
        )
        replacement.close()
    finally:
        host.close()


def test_malformed_host_input_propagates_phase11_error_without_phase12_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    projections = 0

    def unexpected_projection(*_: object, **__: object) -> object:
        nonlocal projections
        projections += 1
        raise AssertionError("malformed input must not reach projection")

    monkeypatch.setattr(sink_module, "project_vhe_state", unexpected_projection)
    try:
        with pytest.raises(BrainvisionIngressError) as refusal:
            host.admit(object())
        assert refusal.value.field == "observation"
        assert refusal.value.reason == "malformed_observation"
        assert projections == 0
        assert sink.records == []
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=0,
            sink_delivery_failures_total=0,
            projection_construction_failures_total=0,
        )
    finally:
        host.close()


def test_forged_observation_id_is_refused_without_phase12_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    observation = _observation()
    object.__setattr__(observation, "observation_id", "bvobs1_tampered")
    projections = 0

    def unexpected_projection(*_: object, **__: object) -> object:
        nonlocal projections
        projections += 1
        raise AssertionError("invalid identity must not reach projection")

    monkeypatch.setattr(sink_module, "project_vhe_state", unexpected_projection)
    try:
        with pytest.raises(BrainvisionIngressError) as refusal:
            host.admit(observation)
        assert refusal.value.field == "observation_id"
        assert refusal.value.reason == "invalid_observation_id"
        assert projections == 0
        assert sink.records == []
        assert _metrics(host).sink_invocations_total == 0
    finally:
        host.close()


def test_disabled_and_suspended_hosts_propagate_lifecycle_refusals_without_phase12_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    projections = 0

    def unexpected_projection(*_: object, **__: object) -> object:
        nonlocal projections
        projections += 1
        raise AssertionError("inactive lifecycle must not reach projection")

    monkeypatch.setattr(sink_module, "project_vhe_state", unexpected_projection)
    try:
        manager.suspend(WORKSPACE_ID, AGENT_ID)
        with pytest.raises(BrainvisionLifecycleError) as suspended:
            host.admit(_observation())
        assert suspended.value.reason == "invalid_lifecycle_transition"
        manager.resume(WORKSPACE_ID, AGENT_ID)
        manager.disable(WORKSPACE_ID, AGENT_ID)
        with pytest.raises(BrainvisionLifecycleError) as disabled:
            host.admit(_observation())
        assert disabled.value.reason == "invalid_lifecycle_transition"
        assert projections == 0
        assert sink.records == []
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=0,
            sink_delivery_failures_total=0,
            projection_construction_failures_total=0,
        )
    finally:
        host.close()


def test_config_ahead_recovery_refusal_has_no_phase12_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, clock, identities, locks = _environment(tmp_path)
    configuration = load_brainvision_configuration(tmp_path, WORKSPACE_ID, AGENT_ID)
    write_brainvision_configuration(
        tmp_path,
        WORKSPACE_ID,
        AGENT_ID,
        replace(configuration, last_accepted_source_sequence=1),
    )
    cold = _cold_manager(tmp_path, clock, identities, locks)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=cold,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    projections = 0

    def unexpected_projection(*_: object, **__: object) -> object:
        nonlocal projections
        projections += 1
        raise AssertionError("hard recovery refusal must not reach projection")

    monkeypatch.setattr(sink_module, "project_vhe_state", unexpected_projection)
    try:
        with pytest.raises(BrainvisionLifecycleError) as refusal:
            host.admit(_observation(source_sequence=2))
        assert refusal.value.field == "sequence"
        assert refusal.value.reason == "config_ahead"
        assert projections == 0
        assert sink.records == []
        assert _metrics(host).sink_invocations_total == 0
    finally:
        host.close()


def test_two_agent_hosts_deliver_only_to_their_own_bound_sink(tmp_path: Path) -> None:
    manager, _, identities, _ = _environment(tmp_path)
    second_agent_id = "agent-b"
    identities.create(WORKSPACE_ID, second_agent_id)
    manager.configure_brainvision(
        WORKSPACE_ID,
        second_agent_id,
        STREAM_ID,
        CONTRACT_ID,
        0,
    )
    manager.enable(WORKSPACE_ID, second_agent_id)
    first_sink = RecordingSink()
    second_sink = RecordingSink()
    first_host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=first_sink,
    )
    second_host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=second_agent_id,
        sink=second_sink,
    )
    try:
        first_receipt = first_host.admit(_observation())
        second_receipt = second_host.admit(_observation())
        assert first_sink.records == [(first_receipt, first_sink.records[0][1])]
        assert second_sink.records == [(second_receipt, second_sink.records[0][1])]
        assert first_sink.records[0][1] is not second_sink.records[0][1]
        assert not ({"workspace_id", "agent_id"} & set(first_sink.records[0][1]))
        assert not ({"workspace_id", "agent_id"} & set(second_sink.records[0][1]))
        assert _metrics(first_host).sink_invocations_total == 1
        assert _metrics(second_host).sink_invocations_total == 1
    finally:
        first_host.close()
        second_host.close()


def test_callback_return_value_is_ignored_after_successful_delivery(tmp_path: Path) -> None:
    manager, _, _, _ = _environment(tmp_path)
    sentinel = object()

    class ReturningSink:
        def __init__(self) -> None:
            self.calls = 0

        def on_projection(
            self,
            receipt: FirsthandVisualAdmissionReceipt,
            projection_payload: dict[str, object],
        ) -> object:
            del receipt, projection_payload
            self.calls += 1
            return sentinel

    sink = ReturningSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    try:
        receipt = host.admit(_observation())
        assert receipt.source_sequence == 0
        assert sink.calls == 1
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=1,
            sink_delivery_failures_total=0,
            projection_construction_failures_total=0,
        )
        assert load_brainvision_configuration(
            tmp_path, WORKSPACE_ID, AGENT_ID
        ).last_accepted_source_sequence == 0
    finally:
        host.close()


def test_configuration_and_recovery_only_operations_never_deliver_to_phase12_sink(
    tmp_path: Path,
) -> None:
    manager, clock, identities, locks = _environment(tmp_path)
    sink = RecordingSink()
    host = Phase12IngressHost(
        lifecycle_manager=manager,
        workspace_id=WORKSPACE_ID,
        agent_id=AGENT_ID,
        sink=sink,
    )
    try:
        manager.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
        manager.suspend(WORKSPACE_ID, AGENT_ID)
        manager.disable(WORKSPACE_ID, AGENT_ID)
        manager.reconfigure_disabled_profile(WORKSPACE_ID, AGENT_ID, theta=1)
        manager.delete_brainvision_configuration(WORKSPACE_ID, AGENT_ID)
        manager.configure_brainvision(
            WORKSPACE_ID,
            AGENT_ID,
            STREAM_ID,
            CONTRACT_ID,
            0,
        )
        manager.enable(WORKSPACE_ID, AGENT_ID)
        sidecar = load_vhe_sidecar(tmp_path, WORKSPACE_ID, AGENT_ID)
        from brainvision.vhe_sidecar import write_vhe_sidecar

        write_vhe_sidecar(
            tmp_path,
            WORKSPACE_ID,
            AGENT_ID,
            replace(sidecar, accepted_source_sequence=0),
        )
        cold = _cold_manager(tmp_path, clock, identities, locks)
        cold.runtime_snapshot(WORKSPACE_ID, AGENT_ID)
        assert load_brainvision_configuration(
            tmp_path, WORKSPACE_ID, AGENT_ID
        ).last_accepted_source_sequence == 0
        assert sink.records == []
        assert _metrics(host) == Phase12SinkMetrics(
            sink_invocations_total=0,
            sink_delivery_failures_total=0,
            projection_construction_failures_total=0,
        )
    finally:
        host.close()
