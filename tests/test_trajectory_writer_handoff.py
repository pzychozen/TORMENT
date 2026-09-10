"""Disposable production tests for the v1.2 trajectory authority coordinator."""
from __future__ import annotations

import hashlib
import multiprocessing
import os
from pathlib import Path
from uuid import uuid4

import pytest

from torment_service.substrate.migration.root_scope import RootScopeKey, RootScopeKind
from torment_service.substrate.trajectory_writer_handoff import (
    TrajectoryHandoffBinding,
    TrajectoryHandoffPhase,
    TrajectoryHandoffRefused,
    TrajectoryScopeIdentity,
    TrajectoryWriterHandoffCoordinator,
)


def _native_race_worker(
    root: str, scope: TrajectoryScopeIdentity, operation_key: str, evidence_digest: str,
    release: object, queue: object,
) -> None:
    """Spawn-safe worker: only the current post-barrier token may write."""
    coordinator = TrajectoryWriterHandoffCoordinator.open_existing(data_root=root)
    token = coordinator.admit_native_writer(
        scope=scope, operation_key=operation_key,
        native_writer_identity="NATIVE_TRAJECTORY_EVIDENCE",
        native_admission_evidence_digest=evidence_digest,
    )
    queue.put(("ready", os.getpid(), token.session_identity))
    release.wait(15.0)
    try:
        with coordinator.authorize_effect(token, "multiprocess-native-race"):
            Path(scope.artifact_root, f"native-winner-{os.getpid()}.txt").write_text("winner", encoding="utf-8")
        queue.put(("result", os.getpid(), "WROTE"))
    except TrajectoryHandoffRefused:
        queue.put(("result", os.getpid(), "REFUSED"))


def _legacy_fence_worker(
    root: str, scope: TrajectoryScopeIdentity, release: object, queue: object,
) -> None:
    """Spawn-safe legacy client that attempts a post-quiescence payload write."""
    coordinator = TrajectoryWriterHandoffCoordinator.open_existing(data_root=root)
    authority = coordinator.legacy_writer(scope=scope, writer_identity="LEGACY_MEMORY_GRAPH")
    queue.put(("ready", os.getpid(), authority.token.session_identity))
    release.wait(15.0)
    try:
        with authority.effect("trajectory_legacy_step"):
            Path(scope.artifact_root, "illegal-legacy.txt").write_text("illegal", encoding="utf-8")
        queue.put(("result", os.getpid(), "WROTE"))
    except TrajectoryHandoffRefused:
        queue.put(("result", os.getpid(), "REFUSED"))
    finally:
        authority.close()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _scope(root: Path, *, workspace: str = "ws", agent: str = "agent") -> TrajectoryScopeIdentity:
    artifact = root / "workspaces" / workspace / "agents" / agent / "private"
    artifact.mkdir(parents=True)
    return TrajectoryScopeIdentity(
        data_root_identity=f"disposable:{root.name}",
        scope_key=RootScopeKey(workspace, RootScopeKind.PRIVATE, agent_id=agent),
        legacy_source_namespace_id=uuid4(),
        artifact_root=str(artifact),
    )


def _binding() -> TrajectoryHandoffBinding:
    return TrajectoryHandoffBinding(
        corrected_core_id=uuid4(),
        p6_receipt_id=str(uuid4()),
        root_admission_envelope_digest=_digest("envelope"),
        plan_digest=_digest("plan"),
    )


def _prepared(root: Path, *, scope: TrajectoryScopeIdentity | None = None, binding: TrajectoryHandoffBinding | None = None):
    scope = scope or _scope(root)
    binding = binding or _binding()
    coordinator = TrajectoryWriterHandoffCoordinator.create(data_root=root)
    coordinator.initialize_legacy_scope(
        scope=scope,
        binding=binding,
        legacy_writer_identity="LEGACY_MEMORY_GRAPH",
        operation_key="handoff:one",
    )
    return coordinator, scope, binding


def _complete(root: Path, *, scope: TrajectoryScopeIdentity | None = None, binding: TrajectoryHandoffBinding | None = None):
    coordinator, scope, binding = _prepared(root, scope=scope, binding=binding)
    legacy = coordinator.legacy_writer(scope=scope, writer_identity="LEGACY_MEMORY_GRAPH")
    with legacy.effect("legacy-test-effect"):
        (Path(scope.artifact_root) / "legacy.txt").write_text("legacy", encoding="utf-8")
    coordinator.begin_quiescing(scope=scope, operation_key="handoff:one", evidence_digest=_digest("freeze-start"))
    legacy.close()
    assert coordinator.fence_legacy_after_quiescence(
        scope=scope, operation_key="handoff:one", quiescence_evidence_digest=_digest("freeze-complete"),
    ) is TrajectoryHandoffPhase.LEGACY_QUIESCED
    coordinator.begin_native_admission(scope=scope, operation_key="handoff:one", evidence_digest=_digest("native-ready"))
    native = coordinator.admit_native_writer(
        scope=scope,
        operation_key="handoff:one",
        native_writer_identity="NATIVE_TRAJECTORY_EVIDENCE",
        native_admission_evidence_digest=_digest("native-admitted"),
        session_identity="native-session-one",
    )
    with coordinator.authorize_effect(native, "native-test-effect"):
        (Path(scope.artifact_root) / "native.txt").write_text("native", encoding="utf-8")
    receipt = coordinator.complete_handoff(scope=scope, operation_key="handoff:one")
    return coordinator, scope, binding, legacy, native, receipt


def test_valid_handoff_fences_legacy_then_admits_one_native_and_receipts(tmp_path: Path):
    coordinator, scope, binding, legacy, native, receipt = _complete(tmp_path)
    assert receipt.scope == scope
    assert receipt.binding == binding
    assert coordinator.record_for_scope(scope=scope)["phase"] == "HANDOFF_COMPLETE"
    with pytest.raises(TrajectoryHandoffRefused, match="stale or non-authoritative"):
        with legacy.effect("stale-legacy"):
            pass
    with coordinator.authorize_effect(native, "native-after-receipt"):
        pass


def test_native_admission_before_legacy_quiescence_refuses(tmp_path: Path):
    coordinator, scope, _binding_value = _prepared(tmp_path)
    with pytest.raises(TrajectoryHandoffRefused, match="NATIVE_ADMITTING predecessor"):
        coordinator.admit_native_writer(
            scope=scope,
            operation_key="handoff:one",
            native_writer_identity="NATIVE_TRAJECTORY_EVIDENCE",
            native_admission_evidence_digest=_digest("native"),
        )


def test_quiescence_requires_legacy_session_close_and_settled_intents(tmp_path: Path):
    coordinator, scope, _binding_value = _prepared(tmp_path)
    legacy = coordinator.legacy_writer(scope=scope, writer_identity="LEGACY_MEMORY_GRAPH")
    coordinator.begin_quiescing(scope=scope, operation_key="handoff:one", evidence_digest=_digest("start"))
    with pytest.raises(TrajectoryHandoffRefused, match="has not acknowledged"):
        coordinator.fence_legacy_after_quiescence(
            scope=scope, operation_key="handoff:one", quiescence_evidence_digest=_digest("done"),
        )
    legacy.close()
    coordinator.fence_legacy_after_quiescence(
        scope=scope, operation_key="handoff:one", quiescence_evidence_digest=_digest("done"),
    )


def test_exact_terminal_replay_is_idempotent_and_conflicting_native_owner_refuses(tmp_path: Path):
    coordinator, scope, _binding_value, _legacy, _native, receipt = _complete(tmp_path)
    assert coordinator.complete_handoff(scope=scope, operation_key="handoff:one") == receipt
    with pytest.raises(TrajectoryHandoffRefused, match="conflicts with durable writer identity"):
        coordinator.admit_native_writer(
            scope=scope,
            operation_key="handoff:one",
            native_writer_identity="NATIVE_OTHER",
            native_admission_evidence_digest=_digest("other"),
        )


def test_partial_restart_recovers_exact_phase_without_legacy_reentry(tmp_path: Path):
    coordinator, scope, _binding_value = _prepared(tmp_path)
    legacy = coordinator.legacy_writer(scope=scope, writer_identity="LEGACY_MEMORY_GRAPH")
    coordinator.begin_quiescing(scope=scope, operation_key="handoff:one", evidence_digest=_digest("start"))
    legacy.close()
    coordinator.fence_legacy_after_quiescence(
        scope=scope, operation_key="handoff:one", quiescence_evidence_digest=_digest("done"),
    )
    recovered = TrajectoryWriterHandoffCoordinator.open_existing(data_root=tmp_path)
    assert recovered.record_for_scope(scope=scope)["phase"] == "LEGACY_QUIESCED"
    with pytest.raises(TrajectoryHandoffRefused, match="fenced or quiescing"):
        recovered.legacy_writer(scope=scope, writer_identity="LEGACY_MEMORY_GRAPH")


def test_aggregate_requires_every_exact_scope_receipt_and_no_overlap(tmp_path: Path):
    binding = _binding()
    first = _scope(tmp_path, agent="one")
    second = _scope(tmp_path, agent="two")
    coordinator, first, binding, *_rest = _complete(tmp_path, scope=first, binding=binding)
    coordinator.initialize_legacy_scope(
        scope=second, binding=binding, legacy_writer_identity="LEGACY_MEMORY_GRAPH", operation_key="handoff:one",
    )
    with pytest.raises(TrajectoryHandoffRefused, match="every scope handoff completion"):
        coordinator.aggregate_receipt(expected_scopes=(first, second), binding=binding)
    _complete(tmp_path, scope=second, binding=binding)
    aggregate = coordinator.aggregate_receipt(expected_scopes=(first, second), binding=binding)
    assert aggregate.payload()["expected_scope_count"] == 2
    assert aggregate.payload()["unaccounted_scope_count"] == 0


def test_native_session_replacement_fences_a_surviving_old_native_process(tmp_path: Path):
    coordinator, scope, _binding_value, _legacy, old_native, _receipt = _complete(tmp_path)
    replacement = coordinator.native_writer(scope=scope, writer_identity="NATIVE_TRAJECTORY_EVIDENCE")
    assert replacement.token.generation > old_native.generation
    with pytest.raises(TrajectoryHandoffRefused, match="stale or non-authoritative"):
        with coordinator.authorize_effect(old_native, "stale-native"):
            pass
    with replacement.effect("replacement-native"):
        pass


def test_two_native_processes_race_one_admission_but_only_current_generation_writes(tmp_path: Path):
    coordinator, scope, _binding_value = _prepared(tmp_path)
    coordinator.begin_quiescing(scope=scope, operation_key="handoff:one", evidence_digest=_digest("start"))
    coordinator.fence_legacy_after_quiescence(
        scope=scope, operation_key="handoff:one", quiescence_evidence_digest=_digest("done"),
    )
    coordinator.begin_native_admission(scope=scope, operation_key="handoff:one", evidence_digest=_digest("native-ready"))
    context = multiprocessing.get_context("spawn")
    release = context.Event()
    queue = context.Queue()
    processes = [context.Process(
        target=_native_race_worker,
        args=(str(tmp_path), scope, "handoff:one", _digest("native-admitted"), release, queue),
    ) for _ in range(2)]
    for process in processes:
        process.start()
    ready = [queue.get(timeout=20) for _ in processes]
    assert all(item[0] == "ready" for item in ready)
    release.set()
    results = [queue.get(timeout=20) for _ in processes]
    for process in processes:
        process.join(20)
        assert process.exitcode == 0
    assert sorted(item[2] for item in results) == ["REFUSED", "WROTE"]
    assert len(list(Path(scope.artifact_root).glob("native-winner-*.txt"))) == 1


def test_legacy_process_racing_quiescence_is_refused_before_payload_effect(tmp_path: Path):
    coordinator, scope, _binding_value = _prepared(tmp_path)
    context = multiprocessing.get_context("spawn")
    release = context.Event()
    queue = context.Queue()
    process = context.Process(target=_legacy_fence_worker, args=(str(tmp_path), scope, release, queue))
    process.start()
    ready = queue.get(timeout=20)
    assert ready[0] == "ready"
    coordinator.begin_quiescing(scope=scope, operation_key="handoff:one", evidence_digest=_digest("start"))
    release.set()
    result = queue.get(timeout=20)
    process.join(20)
    assert process.exitcode == 0
    assert result[2] == "REFUSED"
    coordinator.fence_legacy_after_quiescence(
        scope=scope, operation_key="handoff:one", quiescence_evidence_digest=_digest("done"),
    )
    assert not (Path(scope.artifact_root) / "illegal-legacy.txt").exists()
