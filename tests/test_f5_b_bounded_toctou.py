"""F5-B bounded filesystem identity-continuity regressions.

These tests exercise deterministic junction replacement before an operation's
Level-2 revalidation.  They intentionally do not attempt a concurrent swap
after the final check: this batch provides bounded detection, not a claim of
race-free or handle-pinned filesystem access.
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

import numpy as np
import pytest

from torment_service.checkpoint import (
    CheckpointContainmentError,
    _get_checkpoint_root_guard,
    _prune_old_checkpoints,
    save_checkpoint,
)
from torment_service.fabric import TormentFabric
from torment_service.kernel.model_core import ModelState
from torment_service.memory_kernel import CorridorMonitor


def _make_directory_junction(link: Path, target: Path) -> None:
    if os.name != "nt":
        pytest.skip("directory junctions are a Windows-specific regression surface")
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip("directory junction creation is unavailable on this host")


def _replace_with_junction(source: Path, target: Path) -> Path:
    parked = source.with_name(source.name + "_parked")
    source.rename(parked)
    _make_directory_junction(source, target)
    return parked


def _restore_replaced_directory(source: Path, parked: Path) -> None:
    if source.exists():
        # rmdir removes the junction itself, never its target.
        os.rmdir(source)
    parked.rename(source)


def _model_state() -> ModelState:
    return ModelState(
        Omega=np.array([1 + 0j, 0 + 1j], dtype=np.complex128),
        phi_index=1,
        cycle_stage=0,
        identity_state=0,
        z=0.1,
        t=1.0,
        step=1,
    )


def _save(data_dir: Path, step: int, *, max_checkpoints: int = 10) -> str:
    path = save_checkpoint(
        data_dir=str(data_dir),
        workspace_id="ws_f5b",
        agent_id="agent_f5b",
        step=step,
        model_state=_model_state(),
        corridor_monitor=CorridorMonitor(),
        max_checkpoints=max_checkpoints,
    )
    assert path is not None
    return path


def _seed_clone_job(fabric: TormentFabric, job_id: str, started_ts: float) -> None:
    fabric._clone_jobs[job_id] = {
        "job_id": job_id,
        "started_ts": started_ts,
        "updated_ts": started_ts,
        "status": "done",
        "phase": "done",
    }
    fabric._persist_job("clone", job_id)


def _persisted_job_fabric(tmp_path: Path, monkeypatch) -> TormentFabric:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")
    monkeypatch.setenv("TORMENT_JOB_PERSIST", "1")
    monkeypatch.setenv("TORMENT_JOB_MAX", "1")
    return TormentFabric(str(tmp_path / "data"))


def test_checkpoint_write_substitution_is_distinct_and_recovers(tmp_path, caplog):
    data_dir = tmp_path / "data"
    original = _save(data_dir, 1)
    private_dir = Path(original).parent.parent
    outside = tmp_path / "outside"
    outside.mkdir()
    parked = _replace_with_junction(private_dir, outside)
    try:
        with caplog.at_level(logging.ERROR, logger="torment.checkpoint"):
            with pytest.raises(CheckpointContainmentError):
                _save(data_dir, 2)
        assert not (outside / "checkpoints" / "checkpoint_000002.json").exists()
        assert "security_incident=filesystem_containment_substitution" in caplog.text
        assert "operation=write" in caplog.text
        assert str(outside) not in caplog.text
    finally:
        _restore_replaced_directory(private_dir, parked)

    recovered = _save(data_dir, 3)
    assert Path(recovered).is_file()


def test_checkpoint_prune_substitution_aborts_without_outside_delete(tmp_path, caplog):
    data_dir = tmp_path / "data"
    _save(data_dir, 1)
    _save(data_dir, 2)
    _save(data_dir, 3)
    guard = _get_checkpoint_root_guard(str(data_dir), "ws_f5b", "agent_f5b")
    checkpoint_dir = Path(guard.checkpoint_root.canonical_path)
    private_dir = checkpoint_dir.parent
    outside = tmp_path / "outside"
    outside_checkpoints = outside / "checkpoints"
    outside_checkpoints.mkdir(parents=True)
    outside_one = outside_checkpoints / "checkpoint_000001.json"
    outside_two = outside_checkpoints / "checkpoint_000002.json"
    outside_one.write_text("outside-one", encoding="utf-8")
    outside_two.write_text("outside-two", encoding="utf-8")
    parked = _replace_with_junction(private_dir, outside)
    try:
        with caplog.at_level(logging.ERROR, logger="torment.checkpoint"):
            with pytest.raises(CheckpointContainmentError):
                _prune_old_checkpoints(guard, 1)
        assert outside_one.read_text(encoding="utf-8") == "outside-one"
        assert outside_two.read_text(encoding="utf-8") == "outside-two"
        assert "security_incident=filesystem_containment_substitution" in caplog.text
        assert "operation=prune" in caplog.text
        assert str(outside) not in caplog.text
    finally:
        _restore_replaced_directory(private_dir, parked)


def test_persisted_job_sweep_substitution_aborts_and_recovers(tmp_path, monkeypatch, caplog):
    fabric = _persisted_job_fabric(tmp_path, monkeypatch)
    try:
        _seed_clone_job(fabric, "old", 1.0)
        _seed_clone_job(fabric, "new", 2.0)
        jobs_root = Path(fabric._jobs_root)
        outside = tmp_path / "outside"
        outside_clone = outside / "clone"
        outside_clone.mkdir(parents=True)
        (outside / "repair").mkdir()
        outside_old = outside_clone / "old.json"
        outside_old.write_text("outside-old", encoding="utf-8")
        parked = _replace_with_junction(jobs_root, outside)
        try:
            with caplog.at_level(logging.ERROR, logger="torment.clone"):
                assert fabric._prune_jobs("clone") is False
            assert outside_old.read_text(encoding="utf-8") == "outside-old"
            assert "old" in fabric._clone_jobs
            assert fabric._last_persisted_job_security_incident == {
                "event": "filesystem_containment_substitution",
                "subsystem": "persisted_job",
                "operation": "sweep",
                "failure_class": "identity_continuity",
            }
            assert "security_incident=filesystem_containment_substitution" in caplog.text
            assert str(outside) not in caplog.text
        finally:
            _restore_replaced_directory(jobs_root, parked)

        assert fabric._prune_jobs("clone") is True
        assert "old" not in fabric._clone_jobs
        assert "new" in fabric._clone_jobs
        assert not (jobs_root / "clone" / "old.json").exists()
        assert outside_old.read_text(encoding="utf-8") == "outside-old"
    finally:
        fabric.close()


def test_persisted_job_normal_retention_remains_best_effort(tmp_path, monkeypatch):
    fabric = _persisted_job_fabric(tmp_path, monkeypatch)
    try:
        _seed_clone_job(fabric, "old", 1.0)
        _seed_clone_job(fabric, "new", 2.0)
        assert fabric._prune_jobs("clone") is True
        assert set(fabric._clone_jobs) == {"new"}
        assert (Path(fabric._jobs_root) / "clone" / "new.json").is_file()
        assert not (Path(fabric._jobs_root) / "clone" / "old.json").exists()
    finally:
        fabric.close()
