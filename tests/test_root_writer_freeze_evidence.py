from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path

import pytest

from torment_service.substrate.writer_freeze_evidence import (
    ListenerObservation,
    ListenerObservationResult,
    RootTreeStabilityObservation,
    RootWriterClass,
    RootWriterFreezeEvidenceRefused,
    RootWriterFreezeRecheck,
    WriterObservationResult,
    WriterProcessObservation,
    bind_root_writer_freeze_witness,
    capture_root_writer_freeze_evidence,
    recheck_root_writer_freeze_evidence,
    root_writer_freeze_evidence_payload_from_payload,
    snapshot_root_workspaces,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _root(tmp_path: Path, name: str = "root") -> tuple[Path, Path]:
    root = tmp_path / name
    file_path = root / "workspaces" / "ws-one" / "workspace_meta.json"
    file_path.parent.mkdir(parents=True)
    file_path.write_bytes(b"one")
    return root, file_path


def _writers(*, running: RootWriterClass | None = None) -> tuple[WriterProcessObservation, ...]:
    return tuple(
        WriterProcessObservation(
            writer_class=item,
            observation_mechanism="SYNTHETIC_OPERATOR_CENSUS_V1",
            result=(
                WriterObservationResult.RUNNING
                if item is running
                else WriterObservationResult.ABSENT
            ),
        )
        for item in RootWriterClass
    )


def _listener(result: ListenerObservationResult = ListenerObservationResult.ABSENT) -> ListenerObservation:
    return ListenerObservation(
        listener_identity="127.0.0.1:8787",
        observation_mechanism="SYNTHETIC_LISTENER_CENSUS_V1",
        result=result,
    )


def _capture(
    root: Path,
    *,
    writers: tuple[WriterProcessObservation, ...] | None = None,
    listener: ListenerObservation | None = None,
    snapshotter=snapshot_root_workspaces,
):
    clock_values = iter((2_000_000_000_000_000_000, 2_000_000_000_000_000_100, 2_000_000_000_000_000_200))
    return capture_root_writer_freeze_evidence(
        data_root=root,
        data_root_identity=f"synthetic:{root.name}",
        writer_freeze_operation_identity="synthetic-freeze-epoch",
        operator_identity="synthetic-operator",
        covered_writer_classes=writers or _writers(),
        listener_observation=listener or _listener(),
        external_owner_observation_digest=_digest("synthetic-owner"),
        expected_root_admission_description_contract="ROOT_ADMISSION_DESCRIPTION_V1",
        invalidation_rule_version="ROOT_WRITER_FREEZE_INVALIDATION_V1",
        minimum_delta_seconds=0,
        snapshotter=snapshotter,
        clock_ns=lambda: next(clock_values),
    )


def _recheck(captured) -> RootWriterFreezeRecheck:
    return RootWriterFreezeRecheck(
        covered_writer_classes=_writers(),
        listener_observation=_listener(),
        job_observation=captured.payload.job_observation,
        external_owner_observation_digest=captured.payload.external_owner_observation_digest,
    )


def test_f1_stable_root_yields_payload_witness_and_fresh_recheck(tmp_path: Path) -> None:
    root, _file_path = _root(tmp_path)
    captured = _capture(root)

    assert captured.payload.source_tree_snapshot.file_count == 1
    assert captured.witness.writer_evidence_digest == captured.payload.digest
    assert root_writer_freeze_evidence_payload_from_payload(captured.payload.payload()) == captured.payload
    assert _recheck(captured).external_owner_observation_digest == captured.payload.external_owner_observation_digest
    recheck_root_writer_freeze_evidence(
        data_root=root,
        payload=captured.payload,
        witness=captured.witness,
        recheck=_recheck(captured),
        expected_external_owner_observation_digest=captured.payload.external_owner_observation_digest,
    )


def test_f2_file_mutation_between_t0_and_t1_refuses(tmp_path: Path) -> None:
    root, file_path = _root(tmp_path)
    calls = 0

    def snapshotter(*, data_root: Path):
        nonlocal calls
        calls += 1
        result = snapshot_root_workspaces(data_root=data_root)
        if calls == 1:
            file_path.write_bytes(b"two")
        return result

    with pytest.raises(RootWriterFreezeEvidenceRefused, match="T0_T1_TREE_DRIFT"):
        _capture(root, snapshotter=snapshotter)


def test_f3_mutation_during_capture_refuses(tmp_path: Path) -> None:
    root, file_path = _root(tmp_path)
    calls = 0

    def snapshotter(*, data_root: Path):
        nonlocal calls
        calls += 1
        result = snapshot_root_workspaces(data_root=data_root)
        if calls == 2:
            file_path.write_bytes(b"two")
        return result

    with pytest.raises(RootWriterFreezeEvidenceRefused, match="T2_TREE_DRIFT"):
        _capture(root, snapshotter=snapshotter)


def test_f4_active_listener_refuses(tmp_path: Path) -> None:
    root, _file_path = _root(tmp_path)
    with pytest.raises(RootWriterFreezeEvidenceRefused, match="LISTENER"):
        _capture(root, listener=_listener(ListenerObservationResult.ACTIVE))


def test_f5_running_writer_refuses(tmp_path: Path) -> None:
    root, _file_path = _root(tmp_path)
    with pytest.raises(RootWriterFreezeEvidenceRefused, match="WRITER_NOT_STOPPED"):
        _capture(root, writers=_writers(running=RootWriterClass.MCP_SERVER))


def test_f6_nonterminal_clone_repair_job_refuses(tmp_path: Path) -> None:
    root, _file_path = _root(tmp_path)
    job = root / "jobs" / "clone" / "active.json"
    job.parent.mkdir(parents=True)
    job.write_text('{"job_id":"active","status":"running"}', encoding="utf-8")

    with pytest.raises(RootWriterFreezeEvidenceRefused, match="NONTERMINAL_JOB"):
        _capture(root)


@pytest.mark.parametrize(
    ("name", "mutate"),
    (
        ("f7_added", lambda root, path: (root / "workspaces" / "ws-one" / "added.bin").write_bytes(b"x")),
        ("f8_deleted", lambda root, path: path.unlink()),
        ("f9_renamed", lambda root, path: path.rename(path.with_name("renamed.json"))),
        ("f10_same_size_bytes", lambda root, path: path.write_bytes(b"two")),
    ),
)
def test_f7_to_f10_tree_content_path_or_count_drift_refuses(tmp_path: Path, name: str, mutate) -> None:
    root, file_path = _root(tmp_path, name)
    before = snapshot_root_workspaces(data_root=root)
    mutate(root, file_path)
    after = snapshot_root_workspaces(data_root=root)

    with pytest.raises(RootWriterFreezeEvidenceRefused, match="T0_T1_TREE_DRIFT"):
        RootTreeStabilityObservation(
            t0_ns=2_000_000_000_000_000_000,
            t1_ns=2_000_000_000_000_000_001,
            minimum_delta_seconds=0,
            snapshot_t0=before,
            snapshot_t1=after,
        )


def test_f11_restored_bytes_with_mtime_after_t0_refuses(tmp_path: Path) -> None:
    root, file_path = _root(tmp_path)
    before = snapshot_root_workspaces(data_root=root)
    # Keep a full second of separation for filesystems that quantize mtimes.
    t0_ns = before.maximum_mtime_ns + 1_000_000_000
    os.utime(file_path, ns=(t0_ns + 1_000_000_000, t0_ns + 1_000_000_000))
    after = snapshot_root_workspaces(data_root=root)

    with pytest.raises(RootWriterFreezeEvidenceRefused, match="MAX_MTIME_NOT_BEFORE_T0"):
        RootTreeStabilityObservation(
            t0_ns=t0_ns,
            t1_ns=t0_ns + 2,
            minimum_delta_seconds=0,
            snapshot_t0=before,
            snapshot_t1=after,
        )


def test_f12_byte_identical_disposable_clones_share_tree_digest_not_root_identity(tmp_path: Path) -> None:
    root_one, _ = _root(tmp_path, "clone-one")
    root_two, _ = _root(tmp_path, "clone-two")
    one = _capture(root_one)
    two = _capture(root_two)

    assert one.payload.source_tree_snapshot.tree_digest == two.payload.source_tree_snapshot.tree_digest
    assert one.payload.data_root_identity != two.payload.data_root_identity


def test_f13_unsupported_contract_or_version_refuses(tmp_path: Path) -> None:
    root, _file_path = _root(tmp_path)
    serialized = _capture(root).payload.payload()
    bad_contract = dict(serialized)
    bad_contract["contract"] = "UNSUPPORTED"
    with pytest.raises(RootWriterFreezeEvidenceRefused, match="contract is unsupported"):
        root_writer_freeze_evidence_payload_from_payload(bad_contract)
    bad_version = dict(serialized)
    bad_version["version"] = 2
    with pytest.raises(RootWriterFreezeEvidenceRefused, match="version is unsupported"):
        root_writer_freeze_evidence_payload_from_payload(bad_version)


def test_f14_witness_payload_digest_mismatch_refuses(tmp_path: Path) -> None:
    root, _file_path = _root(tmp_path)
    captured = _capture(root)
    mismatched = replace(captured.witness, writer_evidence_digest=_digest("other-evidence"))

    with pytest.raises(RootWriterFreezeEvidenceRefused, match="WITNESS_PAYLOAD_MISMATCH"):
        bind_root_writer_freeze_witness(payload=captured.payload, witness=mismatched)


def test_external_owner_recheck_drift_refuses_without_refreshing_the_epoch(tmp_path: Path) -> None:
    root, _file_path = _root(tmp_path)
    captured = _capture(root)
    changed_owner = _digest("changed-owner")
    stale_recheck = replace(_recheck(captured), external_owner_observation_digest=changed_owner)

    with pytest.raises(RootWriterFreezeEvidenceRefused, match="EXTERNAL_OWNER_DRIFT"):
        recheck_root_writer_freeze_evidence(
            data_root=root,
            payload=captured.payload,
            witness=captured.witness,
            recheck=stale_recheck,
            expected_external_owner_observation_digest=changed_owner,
        )


def test_historical_terminal_clone_repair_job_does_not_block_capture(tmp_path: Path) -> None:
    root, _file_path = _root(tmp_path)
    job = root / "jobs" / "repair" / "finished.json"
    job.parent.mkdir(parents=True)
    job.write_text('{"job_id":"finished","status":"done"}', encoding="utf-8")

    captured = _capture(root)
    assert captured.payload.job_observation.terminal_job_count == 1


def test_snapshot_refuses_symbolic_link_topology(tmp_path: Path) -> None:
    root, file_path = _root(tmp_path)
    link = file_path.with_name("linked.json")
    try:
        link.symlink_to(file_path)
    except OSError:
        pytest.skip("symbolic links are unavailable in this Windows test environment")

    with pytest.raises(RootWriterFreezeEvidenceRefused, match="symbolic link or reparse"):
        snapshot_root_workspaces(data_root=root)
