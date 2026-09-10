"""Frozen crash-tail behavior; the audit below never declares a root SEALED.

The read-only test composition is also used by Stage 4R3 administration on
preserved R2 artifacts. It accepts only the bounded witness with one complete,
prior-epoch crash partial, unchanged against an independently captured hash,
and a closed successor. Ordinary V2 verifiers/readers remain unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from torment_service.kernel.trajectory_v2 import (
    TrajectoryChunkReaderV2,
    TrajectoryIntegrityError,
    TrajectoryPathsV2,
    TrajectoryV2Verifier,
    TrajectoryV2Writer,
    VerificationReportV2,
    iter_v2_boundaries,
    iter_v2_dynamic_records,
    sha256_file,
)
from torment_service.substrate.native_trajectory_evidence_runtime import NativeTrajectoryEvidenceRuntime
from torment_service.substrate.trajectory_writer_handoff import TrajectoryHandoffRefused
from tests.test_trajectory_writer_handoff import _complete


def _jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _require(condition, detail):
    if not condition:
        raise TrajectoryIntegrityError(detail)


def inspect_retained_crash(root: Path, *, expected_orphan_sha256: str) -> dict:
    """Account for the bounded crash witness without changing verifier meaning.

    Sealed entries reuse the production entry/frame/hash checks. Sequence holes
    are accounted for by the physical orphan, never by putting it in the hash
    chain. Both full-root verifier failures and consumer refusals are retained.
    This is a test/evidence predicate, not a production mode or recovery API.
    """
    verifier = TrajectoryV2Verifier(str(root))
    paths = verifier.paths
    reports = {mode: verifier.verify(mode=mode).to_dict() for mode in ("sealed", "live")}
    partials = list(paths.chunks.rglob("*.partial"))
    _require(len(partials) == 1, "bounded audit requires exactly one retained partial")
    partial = partials[0]
    _require(sha256_file(partial) == expected_orphan_sha256, "orphan differs from independent pre-crash hash")

    checked = VerificationReportV2()
    chunks_root = verifier._physical_chunks_root(checked)
    _require(chunks_root is not None, "invalid physical chunks root")
    _require(partial.resolve().is_relative_to(chunks_root), "orphan escapes physical chunks root")
    entries = verifier._manifest_entries(checked)
    boundaries, boundary_valid = verifier._boundary_records(checked)
    _require(boundary_valid and checked.valid, "invalid manifest or boundary evidence")
    epochs = [int(b["epoch"]) for b in boundaries if b.get("type") == "EPOCH_START"]
    _require(epochs and epochs == sorted(set(epochs)), "epoch boundaries must strictly increase")
    orphan_seq, orphan_epoch = TrajectoryChunkReaderV2(partial).header()
    _require(orphan_epoch in epochs and orphan_epoch < epochs[-1], "partial is not a prior-epoch orphan")
    relative = partial.relative_to(paths.base).as_posix()
    diagnostics = _jsonl(paths.diagnostics)
    _require(any(d.get("code") == "ORPHANED_CRASH_PARTIAL" and d.get("path") == relative
                 and d.get("partial_epoch") == orphan_epoch and d.get("epoch") in epochs
                 and int(d["epoch"]) > orphan_epoch for d in diagnostics), "orphan lacks matching restart diagnostic")

    genesis = _jsonl(paths.genesis)
    _require(all(g.get("type") == "ENTITY_GENESIS" for g in genesis), "invalid genesis type")
    genesis_eids = {int(g["eid"]) for g in genesis}
    _require(len(genesis_eids) == len(genesis), "duplicate genesis identity")
    expected_frames: dict[int, int] = {}
    previous_sha = ""
    manifested = set()
    physical_order = [(orphan_seq, orphan_epoch)]
    sequences = []
    expected_gaps = []
    expected_seq = 1
    prefix_entries = []
    for entry in entries:
        seq, epoch = int(entry["seq"]), int(entry["epoch"])
        chunk = (paths.base / entry["path"]).resolve()
        _require(chunk.suffix == ".trj2" and chunk != partial.resolve(), "partial cannot be a sealed manifest entry")
        _require(chunk not in manifested, "duplicate manifest path")
        _require(epoch in epochs, "manifest epoch has no boundary")
        manifested.add(chunk)
        physical_order.append((seq, epoch))
        sequences.append(seq)
        if seq != expected_seq:
            expected_gaps.append(("MANIFEST_SEQUENCE_GAP", expected_seq, seq))
        expected_seq = seq + 1
        previous_sha, checked_epoch = verifier._check_entry(
            checked, entry, previous_sha=previous_sha, expected_frames=expected_frames,
            genesis_eids=genesis_eids, chunks_root=chunks_root,
        )
        _require(checked.valid and checked_epoch == epoch, "sealed entry/frame/hash verification failed")
        if seq < orphan_seq:
            prefix_entries.append(entry)
    _require(entries and sequences == sorted(set(sequences)), "manifest order must strictly increase")
    _require(any(int(e["epoch"]) > orphan_epoch for e in entries), "no closed successor evidence")
    _require(manifested == {p.resolve() for p in paths.chunks.rglob("*.trj2")}, "unmanifested closed chunk")
    physical_order.sort()
    _require([s for s, _ in physical_order] == list(range(1, len(physical_order) + 1)), "unaccounted physical sequence gap/duplicate")
    _require([e for _, e in physical_order] == sorted(e for _, e in physical_order), "physical epoch order regressed")

    orphan_frames = list(TrajectoryChunkReaderV2(partial).iter_steps())
    _require(orphan_frames, "orphan contains no complete frame")
    orphan_check = VerificationReportV2()
    verifier._check_frames(orphan_check, orphan_frames, epoch=orphan_epoch,
                           expected_frame_seq=expected_frames.get(orphan_epoch, 1),
                           genesis_eids=genesis_eids, location=str(partial))
    _require(orphan_check.valid, "orphan structural frame check failed")
    for mode, report in reports.items():
        code = "INCOMPLETE_FINAL_CHUNK" if mode == "sealed" else "ORPHANED_CRASH_PARTIAL"
        expected = [*expected_gaps, (code, None, None)]
        actual = [(i["code"], i.get("expected"), i.get("actual")) for i in report["issues"]]
        _require(not report["valid"] and actual == expected, "unexpected full-root verifier result")
        _require(report["active_open_tails"] == 0, "orphan was classified as active")
        for consumer in (iter_v2_dynamic_records, iter_v2_boundaries):
            iterator = consumer(str(root), mode=mode)
            try:
                next(iterator)
            except TrajectoryIntegrityError:
                pass
            else:
                raise TrajectoryIntegrityError("consumer did not refuse before yielding crash-root evidence")

    return {
        "recovery_evidence_accounted": True,
        "whole_root_sealed": False,
        "whole_root_verifiers": reports,
        "sealed_entries": entries,
        "sealed_entry_checks": checked.to_dict(),
        "pre_crash_sealed_prefix_count": len(prefix_entries),
        "pre_crash_sealed_prefix_hashes": [e["chunk_sha256"] for e in prefix_entries],
        "orphan": {"path": relative, "sha256": sha256_file(partial), "seq": orphan_seq,
                   "epoch": orphan_epoch, "frames": len(orphan_frames), "records": orphan_check.checked_records,
                   "classified": True, "referenced_by_sealed_manifest": False},
        "physical_sequence_accounted": True,
        "ordinary_consumers_refused_before_yield": True,
    }


def _entity(eid=7):
    return SimpleNamespace(eid=eid, pos=(1.0, 2.0, 3.0), vel=(0.1, 0.2, 0.3), vel0=(0.1, 0.2, 0.3),
                           born_step=0, channel=1, alive=True, payload={})


def _crash_witness(root, *, prefix):
    first = TrajectoryV2Writer(str(root))
    if prefix:
        assert first.write_step([_entity()], 1).ok
        assert first.finalize_chunk().ok
    paths = TrajectoryPathsV2(root)
    prior_entries = _jsonl(paths.manifest) if paths.manifest.exists() else []
    prior_hashes = {e["path"]: sha256_file(paths.base / e["path"]) for e in prior_entries}
    assert first.write_step([_entity()], 2).ok
    partial = first._chunk_partial
    original = partial.read_bytes()
    # Model loss of the process handle, without invoking the application seal.
    first._chunk_handle.close()
    first._chunk_handle = None
    second = TrajectoryV2Writer(str(root))
    assert second.epoch == first.epoch + 1
    assert second.write_step([_entity()], 3).ok
    assert second._chunk_partial != partial
    assert second.close().ok
    assert partial.read_bytes() == original
    assert _jsonl(paths.manifest)[:len(prior_entries)] == prior_entries
    assert all(sha256_file(paths.base / p) == h for p, h in prior_hashes.items())
    return partial


def test_clean_live_tail_and_clean_close_keep_distinct_verifier_meanings(tmp_path):
    writer = TrajectoryV2Writer(str(tmp_path))
    assert writer.write_step([_entity()], 1).ok
    partial = writer._chunk_partial
    live = TrajectoryV2Verifier(str(tmp_path)).verify(mode="live")
    assert live.valid and live.active_open_tails == 1
    assert [n["code"] for n in live.notices] == ["ACTIVE_OPEN_TAIL"]
    assert not TrajectoryV2Verifier(str(tmp_path)).verify(mode="sealed").valid
    with pytest.raises(TrajectoryIntegrityError, match="not a prior-epoch orphan"):
        inspect_retained_crash(tmp_path, expected_orphan_sha256=sha256_file(partial))
    assert writer.close().ok
    assert not partial.exists()
    assert TrajectoryV2Verifier(str(tmp_path)).verify(mode="sealed").valid
    assert len(list(iter_v2_dynamic_records(str(tmp_path)))) == 1


@pytest.mark.parametrize("prefix", [False, True])
def test_crash_retention_preserves_prefix_and_never_claims_sealed(tmp_path, prefix):
    partial = _crash_witness(tmp_path, prefix=prefix)
    audit = inspect_retained_crash(tmp_path, expected_orphan_sha256=sha256_file(partial))
    assert audit["pre_crash_sealed_prefix_count"] == int(prefix)
    assert audit["sealed_entry_checks"]["checked_chunks"] == 1 + int(prefix)
    assert audit["recovery_evidence_accounted"] and not audit["whole_root_sealed"]
    assert audit["ordinary_consumers_refused_before_yield"]


@pytest.mark.parametrize("damage", ["orphan_changed", "manifest_links", "unaccounted_sequence",
                                    "manifest_partial", "missing_diagnostic", "missing_boundary",
                                    "closed_chunk_changed", "truncated_orphan", "unmanifested_closed"])
def test_bounded_audit_refuses_unaccounted_or_malformed_evidence(tmp_path, damage):
    original = tmp_path / "retained"
    partial = _crash_witness(original, prefix=True)
    expected_hash = sha256_file(partial)
    original_hash = expected_hash
    altered = tmp_path / "adversarial_copy"
    shutil.copytree(original, altered)
    paths = TrajectoryPathsV2(altered)
    orphan = next(paths.chunks.rglob("*.partial"))
    entries = _jsonl(paths.manifest)
    if damage == "orphan_changed":
        orphan.write_bytes(orphan.read_bytes() + b"extra")
    elif damage == "manifest_links":
        entries[-1]["previous_chunk_sha256"] = "0" * 64
    elif damage == "unaccounted_sequence":
        entries[-1]["seq"] += 1
    elif damage == "manifest_partial":
        entries[-1]["path"] = orphan.relative_to(paths.base).as_posix()
        entries[-1]["chunk_sha256"] = sha256_file(orphan)
    elif damage == "missing_diagnostic":
        paths.diagnostics.write_text("", encoding="utf-8")
    elif damage == "missing_boundary":
        paths.boundaries.write_text("", encoding="utf-8")
    elif damage == "closed_chunk_changed":
        chunk = paths.base / entries[0]["path"]
        chunk.write_bytes(chunk.read_bytes() + b"extra")
    elif damage == "truncated_orphan":
        orphan.write_bytes(orphan.read_bytes()[:-1])
        expected_hash = sha256_file(orphan)  # Still must fail structural validation.
    elif damage == "unmanifested_closed":
        (paths.chunks / "unmanifested.trj2").write_bytes((paths.base / entries[0]["path"]).read_bytes())
    paths.manifest.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    with pytest.raises(TrajectoryIntegrityError):
        inspect_retained_crash(altered, expected_orphan_sha256=expected_hash)
    assert sha256_file(partial) == original_hash


def test_new_native_session_fences_predecessor_without_adopting_its_tail(tmp_path):
    coordinator, scope, _binding, _legacy, old_token, _receipt = _complete(tmp_path)
    root = Path(scope.artifact_root)
    with coordinator.authorize_effect(old_token, "trajectory_writer_initialize"):
        old_writer = TrajectoryV2Writer(str(root))
    with coordinator.authorize_effect(old_token, "trajectory_v2_step"):
        assert old_writer.write_step([_entity()], 1).ok
    partial = old_writer._chunk_partial
    original = partial.read_bytes()
    old_writer._chunk_handle.close()
    old_writer._chunk_handle = None
    current = NativeTrajectoryEvidenceRuntime(root_dir=str(root), trajectory_format="v2")
    token = current._trajectory_authority.token
    assert token.generation > old_token.generation
    assert token.session_identity != old_token.session_identity
    assert coordinator.record_for_scope(scope=scope)["native_session_identity"] == token.session_identity
    entered = False
    with pytest.raises(TrajectoryHandoffRefused):
        with coordinator.authorize_effect(old_token, "trajectory_v2_step"):
            entered = True
            old_writer.write_step([_entity()], 2)
    assert not entered
    current.write_step([_entity()], step=3)
    current.close()
    assert partial.read_bytes() == original
    audit = inspect_retained_crash(root, expected_orphan_sha256=sha256_file(partial))
    assert audit["recovery_evidence_accounted"]
    with pytest.raises(TrajectoryHandoffRefused):
        coordinator.legacy_writer(scope=scope, writer_identity="LEGACY_MEMORY_GRAPH")
