"""Lossless, non-authoritative trajectory persistence format V2.

The V2 frame identity is ``(epoch, frame_seq)``.  Native logical ``step`` is
diagnostic metadata only and may legitimately repeat between complete frames.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

import numpy as np


FORMAT_VERSION = 2
SCHEMA_VERSION = "trajectory-v2.2"
CODEC_VERSION = "none-v1"
RETENTION_POLICY_FULL_V1 = "full_v1"
CHUNK_STEPS = 64
CHUNK_MAX_BYTES = 32 * 1024 * 1024
MAGIC = b"TRJ2BIN\x00"
CHUNK_HEADER = struct.Struct("<8sHHQQ")  # magic, version, codec, sequence, epoch
STEP_HEADER = struct.Struct("<BQQQIIQ32s")  # tag, frame_seq, step, ts, n, expected, epoch, digest
DYNAMIC_RECORD = struct.Struct("<Q6d")  # EID and exact float64 pos/vel, 56 bytes
FRAME_STEP = 1


class TrajectoryV2Error(RuntimeError):
    """Base V2 persistence error."""


class TrajectoryIntegrityError(TrajectoryV2Error):
    """Raised when canonical V2 history is incomplete or invalid."""


@dataclass(frozen=True)
class TrajectoryPathsV2:
    root: Path

    @property
    def base(self) -> Path:
        return self.root / "trajectories" / "v2"

    @property
    def chunks(self) -> Path:
        return self.base / "chunks"

    @property
    def genesis(self) -> Path:
        return self.base / "entity_genesis.jsonl"

    @property
    def manifest(self) -> Path:
        return self.base / "manifest.jsonl"

    @property
    def boundaries(self) -> Path:
        return self.base / "boundaries.jsonl"

    @property
    def diagnostics(self) -> Path:
        return self.base / "diagnostics.jsonl"

    def ensure_dirs(self) -> None:
        self.chunks.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class EntityGenesisV2:
    eid: int
    born_step: int
    channel: int
    pos0: Tuple[float, float, float]
    vel0: Tuple[float, float, float]

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "ENTITY_GENESIS", "schema_version": SCHEMA_VERSION, "eid": int(self.eid),
                "born_step": int(self.born_step), "channel": int(self.channel),
                "pos0": list(self.pos0), "vel0": list(self.vel0)}


@dataclass(frozen=True)
class DynamicRecordV2:
    eid: int
    pos: Tuple[float, float, float]
    vel: Tuple[float, float, float]

    def pack(self) -> bytes:
        return DYNAMIC_RECORD.pack(int(self.eid), *[float(v) for v in (*self.pos, *self.vel)])

    @classmethod
    def unpack(cls, raw: bytes) -> "DynamicRecordV2":
        if len(raw) != DYNAMIC_RECORD.size:
            raise TrajectoryIntegrityError("dynamic record has incorrect width")
        values = DYNAMIC_RECORD.unpack(raw)
        return cls(int(values[0]), (float(values[1]), float(values[2]), float(values[3])),
                   (float(values[4]), float(values[5]), float(values[6])))


@dataclass(frozen=True)
class StepFrameV2:
    """A full emitted frame; ``step`` is not an identity nor ordering key."""

    frame_seq: int
    step: int
    wall_ts_ns: int
    expected_population: int
    epoch: int
    expected_eid_digest: bytes
    records: Tuple[DynamicRecordV2, ...]

    @property
    def record_count(self) -> int:
        return len(self.records)

    def pack(self) -> bytes:
        return STEP_HEADER.pack(FRAME_STEP, int(self.frame_seq), int(self.step), int(self.wall_ts_ns),
                                int(self.record_count), int(self.expected_population), int(self.epoch),
                                bytes(self.expected_eid_digest)) + b"".join(record.pack() for record in self.records)


@dataclass(frozen=True)
class ChunkManifestEntryV2:
    seq: int
    epoch: int
    path: str
    frame_seq_from: int
    frame_seq_to: int
    frame_count: int
    step_from: int
    step_to: int
    record_count: int
    expected_record_count: int
    expected_population_min: int
    expected_population_max: int
    schema_version: str
    codec_version: str
    retention_policy: str
    chunk_sha256: str
    previous_chunk_sha256: str
    closed_ts_ns: int

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "TRAJECTORY_CHUNK", "seq": int(self.seq), "epoch": int(self.epoch),
                "path": self.path, "frame_seq_from": int(self.frame_seq_from),
                "frame_seq_to": int(self.frame_seq_to), "frame_count": int(self.frame_count),
                "step_from": int(self.step_from), "step_to": int(self.step_to),
                "record_count": int(self.record_count), "expected_record_count": int(self.expected_record_count),
                "expected_population_min": int(self.expected_population_min),
                "expected_population_max": int(self.expected_population_max),
                "schema_version": self.schema_version, "codec_version": self.codec_version,
                "retention_policy": self.retention_policy, "chunk_sha256": self.chunk_sha256,
                "previous_chunk_sha256": self.previous_chunk_sha256, "closed_ts_ns": int(self.closed_ts_ns)}


@dataclass(frozen=True)
class TrajectoryWriteResultV2:
    ok: bool
    status: str
    step: Optional[int] = None
    frame_seq: Optional[int] = None
    detail: str = ""


@dataclass
class VerificationReportV2:
    valid: bool = True
    checked_chunks: int = 0
    checked_steps: int = 0
    checked_records: int = 0
    active_open_tails: int = 0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    notices: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, code: str, detail: str, **extra: Any) -> None:
        self.valid = False
        self.issues.append({"code": code, "detail": detail, **extra})

    def note(self, code: str, detail: str, **extra: Any) -> None:
        self.notices.append({"code": code, "detail": detail, **extra})

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "checked_chunks": self.checked_chunks,
                "checked_steps": self.checked_steps, "checked_records": self.checked_records,
                "active_open_tails": self.active_open_tails, "issues": self.issues, "notices": self.notices}


def _path_is_within(path: Path, base: Path) -> bool:
    """Return whether resolved *path* remains under resolved *base*."""
    normalized_path = os.path.normcase(str(path))
    normalized_base = os.path.normcase(str(base))
    return normalized_path == normalized_base or normalized_path.startswith(normalized_base + os.sep)


def _canonical_chunks_root(paths: TrajectoryPathsV2) -> Path:
    """Resolve and verify that the chunks root itself remains under V2 base."""
    base = paths.base.resolve()
    chunks = paths.chunks.resolve()
    if chunks == base or not _path_is_within(chunks, base):
        raise TrajectoryIntegrityError("trajectory chunks root escapes trajectory base")
    return chunks


def _iter_physical_chunk_paths(
    paths: TrajectoryPathsV2,
    pattern: str,
    *,
    report: Optional[VerificationReportV2] = None,
) -> Iterator[Path]:
    """Yield recursively discovered chunks only when physically contained.

    A Windows directory junction can be traversed by ``Path.rglob``. Resolve
    each discovered candidate back against the original physical chunks root
    before its name, header, or content can influence trajectory state.
    """
    chunks_root = _canonical_chunks_root(paths)
    if not chunks_root.is_dir():
        return
    for candidate in chunks_root.rglob(pattern):
        try:
            resolved = candidate.resolve()
        except OSError as exc:
            if report is None:
                raise TrajectoryIntegrityError(
                    f"unable to resolve discovered chunk path: {candidate}"
                ) from exc
            report.add(
                "DISCOVERED_CHUNK_PATH_INVALID",
                "filesystem-discovered chunk path is unreadable",
                path=str(candidate),
            )
            continue
        if not _path_is_within(resolved, chunks_root):
            if report is None:
                raise TrajectoryIntegrityError(
                    f"discovered chunk path escapes canonical chunks root: {candidate}"
                )
            report.add(
                "DISCOVERED_CHUNK_PATH_INVALID",
                "filesystem-discovered chunk path escapes canonical chunks root",
                path=str(candidate),
                resolved_path=str(resolved),
            )
            continue
        yield resolved


def _vec3(value: Any) -> Tuple[float, float, float]:
    arr = np.asarray(value, dtype=np.float64).reshape(3)
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def eid_digest(eids: Iterable[int]) -> bytes:
    return hashlib.sha256(b"".join(struct.pack("<Q", eid) for eid in sorted(int(e) for e in eids))).digest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _append_jsonl(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise TrajectoryIntegrityError(f"invalid JSONL at {path}:{number}: {exc}") from exc
            if not isinstance(value, dict):
                raise TrajectoryIntegrityError(f"non-object JSONL record at {path}:{number}")
            yield value


def _has_persisted_trajectory_artifacts(paths: TrajectoryPathsV2) -> bool:
    for path in (paths.manifest, paths.genesis, paths.boundaries, paths.diagnostics):
        try:
            if path.exists():
                return True
        except OSError:
            return True
    try:
        if paths.chunks.exists() and not paths.chunks.is_dir():
            return True
        return any(path.is_file() for path in _iter_physical_chunk_paths(paths, "*"))
    except OSError:
        return True


class TrajectoryChunkReaderV2:
    """Read one V2 chunk, including a current tail when requested by live verification."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def header(self) -> Tuple[int, int]:
        with self.path.open("rb") as handle:
            raw_header = handle.read(CHUNK_HEADER.size)
        if len(raw_header) != CHUNK_HEADER.size:
            raise TrajectoryIntegrityError(f"truncated chunk header: {self.path}")
        magic, version, codec, seq, epoch = CHUNK_HEADER.unpack(raw_header)
        if magic != MAGIC:
            raise TrajectoryIntegrityError(f"invalid chunk magic: {self.path}")
        if version != FORMAT_VERSION or codec != 0:
            raise TrajectoryIntegrityError(f"unsupported chunk version/codec: {self.path}")
        return int(seq), int(epoch)

    def iter_steps(self) -> Iterator[StepFrameV2]:
        with self.path.open("rb") as handle:
            raw_header = handle.read(CHUNK_HEADER.size)
            if len(raw_header) != CHUNK_HEADER.size:
                raise TrajectoryIntegrityError(f"truncated chunk header: {self.path}")
            magic, version, codec, _seq, _epoch = CHUNK_HEADER.unpack(raw_header)
            if magic != MAGIC or version != FORMAT_VERSION or codec != 0:
                raise TrajectoryIntegrityError(f"unsupported chunk version/codec: {self.path}")
            while True:
                raw_frame = handle.read(STEP_HEADER.size)
                if not raw_frame:
                    break
                if len(raw_frame) != STEP_HEADER.size:
                    raise TrajectoryIntegrityError(f"truncated frame header: {self.path}")
                tag, frame_seq, step, ts_ns, count, expected, epoch, digest = STEP_HEADER.unpack(raw_frame)
                if tag != FRAME_STEP:
                    raise TrajectoryIntegrityError(f"unknown frame tag {tag}: {self.path}")
                raw_records = handle.read(int(count) * DYNAMIC_RECORD.size)
                if len(raw_records) != int(count) * DYNAMIC_RECORD.size:
                    raise TrajectoryIntegrityError(f"truncated dynamic records at frame_seq {frame_seq}: {self.path}")
                records = tuple(DynamicRecordV2.unpack(raw_records[index:index + DYNAMIC_RECORD.size])
                                for index in range(0, len(raw_records), DYNAMIC_RECORD.size))
                yield StepFrameV2(int(frame_seq), int(step), int(ts_ns), int(expected), int(epoch), bytes(digest), records)


class TrajectoryV2Writer:
    """Best-effort V2 writer; failures never propagate into cognition."""

    def __init__(self, root_dir: str, *, chunk_steps: int = CHUNK_STEPS,
                 chunk_max_bytes: int = CHUNK_MAX_BYTES) -> None:
        self.paths = TrajectoryPathsV2(Path(root_dir).resolve())
        _canonical_chunks_root(self.paths)
        self.paths.ensure_dirs()
        _canonical_chunks_root(self.paths)
        self.chunk_steps = int(chunk_steps)
        self.chunk_max_bytes = int(chunk_max_bytes)
        self._genesis_eids = self._load_genesis_eids()
        self._next_seq = self._discover_next_seq()
        self._previous_sha = self._last_manifest_sha()
        self.epoch = self._discover_next_epoch()
        self._next_frame_seq = 1
        self._chunk_handle: Optional[Any] = None
        self._chunk_partial: Optional[Path] = None
        self._chunk_seq: Optional[int] = None
        self._chunk_step_frames: List[StepFrameV2] = []
        self._report_prior_epoch_partials()
        if self._boundary_append_allowed:
            self._append_boundary("EPOCH_START", epoch=self.epoch, previous_epoch=self.epoch - 1)
        else:
            self._diagnostic("BOUNDARY_EVIDENCE_UNAVAILABLE", self._boundary_evidence_detail)

    def _load_genesis_eids(self) -> set[int]:
        try:
            return {int(record["eid"]) for record in _read_jsonl(self.paths.genesis)}
        except Exception:
            return set()

    def _discover_next_seq(self) -> int:
        highest = 0
        try:
            for record in _read_jsonl(self.paths.manifest):
                highest = max(highest, int(record.get("seq", 0)))
        except Exception:
            pass
        for suffix in ("chunk-*.partial", "chunk-*.trj2"):
            for path in _iter_physical_chunk_paths(self.paths, suffix):
                try:
                    highest = max(highest, int(path.name.split("-")[1].split(".")[0]))
                except (IndexError, ValueError):
                    continue
        return highest + 1

    def _last_manifest_sha(self) -> str:
        try:
            return next((str(record.get("chunk_sha256", ""))
                         for record in reversed(list(_read_jsonl(self.paths.manifest)))), "")
        except Exception:
            return ""

    def _boundary_epoch_evidence(self) -> Tuple[List[int], bool, str]:
        try:
            if not self.paths.boundaries.exists():
                return [], False, "boundary evidence is missing"
            if not self.paths.boundaries.is_file():
                return [], False, "boundary evidence is not a regular file"
            epochs = []
            for record in _read_jsonl(self.paths.boundaries):
                if record.get("type") != "EPOCH_START":
                    continue
                epoch = int(record.get("epoch", 0))
                if epoch < 1:
                    raise TrajectoryIntegrityError("boundary EPOCH_START epoch must be positive")
                epochs.append(epoch)
            return epochs, True, ""
        except Exception as exc:
            return [], False, f"boundary evidence is unreadable: {exc}"

    def _chunk_header_epochs(self) -> List[int]:
        epochs = []
        for suffix in ("*.trj2", "*.partial"):
            for path in _iter_physical_chunk_paths(self.paths, suffix):
                try:
                    _seq, epoch = TrajectoryChunkReaderV2(path).header()
                    if epoch >= 1:
                        epochs.append(epoch)
                except (OSError, TrajectoryIntegrityError):
                    continue
        return epochs

    def _discover_next_epoch(self) -> int:
        boundary_epochs, boundary_valid, boundary_detail = self._boundary_epoch_evidence()
        chunk_epochs = self._chunk_header_epochs()
        persisted_artifacts = _has_persisted_trajectory_artifacts(self.paths)
        self._boundary_append_allowed = boundary_valid or not persisted_artifacts
        self._boundary_evidence_detail = boundary_detail
        observed_epochs = [*boundary_epochs, *chunk_epochs]
        if observed_epochs:
            return max(observed_epochs) + 1
        if persisted_artifacts:
            raise TrajectoryIntegrityError(
                "unable to determine next trajectory epoch from persisted V2 evidence"
            )
        return 1

    def _diagnostic(self, code: str, detail: str, **extra: Any) -> None:
        try:
            _append_jsonl(self.paths.diagnostics, {"type": "TRAJECTORY_DIAGNOSTIC", "code": code,
                                                   "detail": detail, "epoch": self.epoch,
                                                   "ts_ns": time.time_ns(), **extra})
        except Exception:
            pass

    def _report_prior_epoch_partials(self) -> None:
        """Preserve crash remnants and make their orphan status explicit."""
        for partial in sorted(_iter_physical_chunk_paths(self.paths, "*.partial")):
            try:
                _seq, partial_epoch = TrajectoryChunkReaderV2(partial).header()
                if partial_epoch < self.epoch:
                    self._diagnostic("ORPHANED_CRASH_PARTIAL", "pre-existing partial belongs to a prior epoch",
                                     path=str(partial.relative_to(self.paths.base)).replace("\\", "/"),
                                     partial_epoch=partial_epoch)
            except TrajectoryIntegrityError as exc:
                self._diagnostic("UNREADABLE_PREEXISTING_PARTIAL", str(exc),
                                 path=str(partial.relative_to(self.paths.base)).replace("\\", "/"))

    def _append_boundary(self, kind: str, **extra: Any) -> None:
        try:
            _append_jsonl(self.paths.boundaries, {"type": kind, "schema_version": SCHEMA_VERSION,
                                                  "epoch": self.epoch, "ts_ns": time.time_ns(), **extra})
        except Exception as exc:
            self._diagnostic("BOUNDARY_WRITE_FAILED", str(exc), boundary_type=kind)

    @staticmethod
    def genesis_from_entity(entity: Any) -> EntityGenesisV2:
        payload = getattr(entity, "payload", {}) or {}
        return EntityGenesisV2(int(getattr(entity, "eid")), int(getattr(entity, "born_step", 0) or 0),
                               int(getattr(entity, "channel", 0) or 0),
                               _vec3(payload.get("pos", getattr(entity, "pos"))),
                               _vec3(payload.get("vel0", getattr(entity, "vel0"))))

    def write_genesis(self, entity: Any) -> TrajectoryWriteResultV2:
        try:
            genesis = self.genesis_from_entity(entity)
            if genesis.eid in self._genesis_eids:
                return TrajectoryWriteResultV2(True, "GENESIS_ALREADY_PRESENT")
            _append_jsonl(self.paths.genesis, genesis.to_dict())
            self._genesis_eids.add(genesis.eid)
            return TrajectoryWriteResultV2(True, "GENESIS_WRITTEN")
        except Exception as exc:
            self._diagnostic("GENESIS_WRITE_FAILED", str(exc), eid=getattr(entity, "eid", None))
            return TrajectoryWriteResultV2(False, "GENESIS_WRITE_FAILED", detail=str(exc))

    def mark_entity_reset(self, eid: int, *, last_observed_step: Optional[int],
                          last_observed_frame_seq: Optional[int]) -> None:
        self._append_boundary("ENTITY_KINEMATIC_RESET", eid=int(eid), cause="update_payload",
                              last_observed_step=last_observed_step,
                              last_observed_frame_seq=last_observed_frame_seq,
                              effective_frame="next_successful_frame")

    def _open_chunk(self) -> None:
        if self._chunk_handle is not None:
            return
        seq = self._next_seq
        self._next_seq += 1
        epoch_dir = self.paths.chunks / f"epoch-{self.epoch:08d}"
        epoch_dir.mkdir(parents=True, exist_ok=True)
        partial = epoch_dir / f"chunk-{seq:020d}.partial"
        handle = partial.open("xb")
        handle.write(CHUNK_HEADER.pack(MAGIC, FORMAT_VERSION, 0, seq, self.epoch))
        self._chunk_handle, self._chunk_partial, self._chunk_seq = handle, partial, seq
        self._chunk_step_frames = []

    def _frame_from_entities(self, entities: Sequence[Any], step: int) -> StepFrameV2:
        records = tuple(DynamicRecordV2(int(getattr(entity, "eid")), _vec3(getattr(entity, "pos")),
                                        _vec3(getattr(entity, "vel"))) for entity in entities)
        return StepFrameV2(self._next_frame_seq, int(step), time.time_ns(), len(entities), self.epoch,
                           eid_digest(record.eid for record in records), records)

    def write_step(self, entities: Iterable[Any], step: int) -> TrajectoryWriteResultV2:
        try:
            live = [item for item in entities if item is not None and getattr(item, "alive", True)]
            for entity in live:
                result = self.write_genesis(entity)
                if not result.ok:
                    return TrajectoryWriteResultV2(False, "STEP_INCOMPLETE", int(step), detail=result.detail)
            frame = self._frame_from_entities(live, int(step))
            raw_frame = frame.pack()
            self._open_chunk()
            assert self._chunk_handle is not None
            if self._chunk_step_frames and (len(self._chunk_step_frames) >= self.chunk_steps or
                    self._chunk_handle.tell() + len(raw_frame) > self.chunk_max_bytes):
                finalize = self.finalize_chunk()
                if not finalize.ok:
                    return TrajectoryWriteResultV2(False, "STEP_INCOMPLETE", int(step), detail=finalize.detail)
                self._open_chunk()
            assert self._chunk_handle is not None
            self._chunk_handle.write(raw_frame)
            self._chunk_handle.flush()
            self._chunk_step_frames.append(frame)
            self._next_frame_seq += 1  # only a successfully emitted frame consumes this identity
            return TrajectoryWriteResultV2(True, "STEP_COMPLETE", int(step), frame.frame_seq)
        except Exception as exc:
            self._diagnostic("STEP_WRITE_FAILED", str(exc), step=int(step))
            return TrajectoryWriteResultV2(False, "STEP_INCOMPLETE", int(step), detail=str(exc))

    def finalize_chunk(self) -> TrajectoryWriteResultV2:
        if self._chunk_handle is None:
            return TrajectoryWriteResultV2(True, "NO_OPEN_CHUNK")
        handle, partial, seq, frames = self._chunk_handle, self._chunk_partial, self._chunk_seq, tuple(self._chunk_step_frames)
        try:
            assert partial is not None and seq is not None and frames
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
            complete = partial.with_suffix(".trj2")
            os.replace(partial, complete)
            digest = sha256_file(complete)
            entry = ChunkManifestEntryV2(seq, self.epoch,
                str(complete.relative_to(self.paths.base)).replace("\\", "/"),
                frames[0].frame_seq, frames[-1].frame_seq, len(frames), frames[0].step, frames[-1].step,
                sum(frame.record_count for frame in frames), sum(frame.expected_population for frame in frames),
                min(frame.expected_population for frame in frames), max(frame.expected_population for frame in frames),
                SCHEMA_VERSION, CODEC_VERSION, RETENTION_POLICY_FULL_V1, digest, self._previous_sha, time.time_ns())
            _append_jsonl(self.paths.manifest, entry.to_dict())
            self._previous_sha = digest
            self._chunk_handle = self._chunk_partial = self._chunk_seq = None
            self._chunk_step_frames = []
            return TrajectoryWriteResultV2(True, "CHUNK_FINALIZED")
        except Exception as exc:
            try:
                if not handle.closed:
                    handle.close()
            except Exception:
                pass
            self._chunk_handle = self._chunk_partial = self._chunk_seq = None
            self._chunk_step_frames = []
            self._diagnostic("CHUNK_FINALIZE_FAILED", str(exc), seq=seq)
            return TrajectoryWriteResultV2(False, "CHUNK_FINALIZE_FAILED", detail=str(exc))

    def close(self) -> TrajectoryWriteResultV2:
        """Seal the active tail; successful close leaves no partial chunk."""
        return self.finalize_chunk()


class TrajectoryV2Verifier:
    """Validate sealed evidence or one current, structurally valid live tail."""

    def __init__(self, root_dir: str) -> None:
        self.paths = TrajectoryPathsV2(Path(root_dir).resolve())

    def _physical_chunks_root(self, report: VerificationReportV2) -> Optional[Path]:
        try:
            return _canonical_chunks_root(self.paths)
        except TrajectoryIntegrityError as exc:
            report.add("CHUNKS_ROOT_INVALID", str(exc))
            return None

    def _manifest_entries(self, report: VerificationReportV2) -> List[Dict[str, Any]]:
        try:
            return list(_read_jsonl(self.paths.manifest))
        except TrajectoryIntegrityError as exc:
            report.add("MANIFEST_INVALID", str(exc))
            return []

    def _boundary_records(self, report: VerificationReportV2) -> Tuple[List[Dict[str, Any]], bool]:
        try:
            if self.paths.boundaries.exists() and not self.paths.boundaries.is_file():
                report.add("BOUNDARIES_INVALID", "boundary evidence is not a regular file")
                return [], False
            if not self.paths.boundaries.exists():
                if _has_persisted_trajectory_artifacts(self.paths):
                    report.add("BOUNDARIES_INVALID", "boundary evidence is missing despite persisted trajectory state")
                    return [], False
                return [], True
            records = list(_read_jsonl(self.paths.boundaries))
            for record in records:
                if record.get("type") == "EPOCH_START":
                    epoch = int(record.get("epoch", 0))
                    if epoch < 1:
                        raise TrajectoryIntegrityError("boundary EPOCH_START epoch must be positive")
            return records, True
        except Exception as exc:
            report.add("BOUNDARIES_INVALID", f"boundary evidence is unreadable: {exc}")
            return [], False

    @staticmethod
    def _latest_boundary_epoch(records: Sequence[Mapping[str, Any]]) -> int:
        highest = 0
        for record in records:
            if record.get("type") == "EPOCH_START":
                highest = max(highest, int(record.get("epoch", 0)))
        return highest

    @staticmethod
    def _check_frame(report: VerificationReportV2, frame: StepFrameV2, *, epoch: int,
                     expected_frame_seq: int, genesis_eids: set[int], location: str) -> int:
        report.checked_steps += 1
        report.checked_records += frame.record_count
        if frame.epoch != epoch:
            report.add("EPOCH_MISMATCH", "frame epoch differs from chunk epoch", location=location,
                       frame_seq=frame.frame_seq)
        if frame.frame_seq != expected_frame_seq:
            report.add("FRAME_SEQUENCE_INVALID", "frame_seq must increment once per emitted frame in its epoch",
                       location=location, epoch=epoch, expected=expected_frame_seq, actual=frame.frame_seq)
        eids = [record.eid for record in frame.records]
        if frame.record_count != frame.expected_population:
            report.add("INCOMPLETE_FRAME", "record count differs from expected population", frame_seq=frame.frame_seq)
        if len(eids) != len(set(eids)):
            report.add("DUPLICATE_EID_IN_FRAME", "frame contains duplicate EID", frame_seq=frame.frame_seq)
        for eid in eids:
            if eid not in genesis_eids:
                report.add("MISSING_GENESIS", "dynamic record has no genesis record", frame_seq=frame.frame_seq, eid=eid)
        if eid_digest(eids) != frame.expected_eid_digest:
            report.add("EID_DIGEST_MISMATCH", "frame EID digest does not match records", frame_seq=frame.frame_seq)
        return expected_frame_seq + 1

    def _check_frames(self, report: VerificationReportV2, frames: Sequence[StepFrameV2], *, epoch: int,
                      expected_frame_seq: int, genesis_eids: set[int], location: str) -> int:
        for frame in frames:
            expected_frame_seq = self._check_frame(report, frame, epoch=epoch,
                                                    expected_frame_seq=expected_frame_seq,
                                                    genesis_eids=genesis_eids, location=location)
        return expected_frame_seq

    def _check_entry(self, report: VerificationReportV2, entry: Dict[str, Any], *, previous_sha: str,
                     expected_frames: Dict[int, int], genesis_eids: set[int],
                     chunks_root: Optional[Path]) -> Tuple[str, Optional[int]]:
        seq, epoch = int(entry["seq"]), int(entry["epoch"])
        if str(entry.get("schema_version", "")) != SCHEMA_VERSION:
            report.add("MANIFEST_SCHEMA_MISMATCH", "manifest entry schema does not match V2 format", seq=seq)
        if str(entry.get("previous_chunk_sha256", "")) != previous_sha:
            report.add("MANIFEST_HASH_LINK_BROKEN", "previous chunk hash does not match", seq=seq)
        chunk = (self.paths.base / str(entry["path"])).resolve()
        if chunks_root is None or not _path_is_within(chunk, chunks_root):
            report.add("CHUNK_PATH_INVALID", "manifest chunk path escapes chunks directory", seq=seq)
            return previous_sha, None
        if not chunk.is_file():
            report.add("MISSING_CHUNK", "manifest-referenced chunk is absent", seq=seq, path=str(chunk))
            return previous_sha, None
        actual_sha = sha256_file(chunk)
        if actual_sha != str(entry.get("chunk_sha256", "")):
            report.add("CORRUPT_CHUNK", "chunk sha256 mismatch", seq=seq, path=str(chunk))
            return previous_sha, None
        reader = TrajectoryChunkReaderV2(chunk)
        header_seq, header_epoch = reader.header()
        if (header_seq, header_epoch) != (seq, epoch):
            report.add("CHUNK_HEADER_IDENTITY_MISMATCH", "chunk header differs from manifest", seq=seq)
        frames = list(reader.iter_steps())
        if len(frames) != int(entry.get("frame_count", -1)):
            report.add("CHUNK_FRAME_COUNT_MISMATCH", "manifest and chunk frame count differ", seq=seq)
        if not frames:
            report.add("EMPTY_CHUNK", "manifest-referenced chunk has no frames", seq=seq)
        else:
            if frames[0].frame_seq != int(entry.get("frame_seq_from", -1)) or frames[-1].frame_seq != int(entry.get("frame_seq_to", -1)):
                report.add("CHUNK_FRAME_RANGE_MISMATCH", "manifest frame sequence range differs", seq=seq)
            if frames[0].step != int(entry.get("step_from", frames[0].step)) or frames[-1].step != int(entry.get("step_to", frames[-1].step)):
                report.add("CHUNK_STEP_RANGE_MISMATCH", "manifest logical step range differs", seq=seq)
        records = sum(frame.record_count for frame in frames)
        if records != int(entry.get("record_count", -1)):
            report.add("CHUNK_RECORD_COUNT_MISMATCH", "manifest and chunk record count differ", seq=seq)
        if records != int(entry.get("expected_record_count", -1)):
            report.add("CHUNK_EXPECTED_COUNT_MISMATCH", "chunk is not complete full_v1 history", seq=seq)
        expected_frames[epoch] = self._check_frames(report, frames, epoch=epoch,
            expected_frame_seq=expected_frames.setdefault(epoch, 1), genesis_eids=genesis_eids, location=str(chunk))
        report.checked_chunks += 1
        return actual_sha, epoch

    def _check_live_tail(self, report: VerificationReportV2, partial: Path, *, current_epoch: int,
                         expected_seq: int, expected_frames: Dict[int, int], genesis_eids: set[int]) -> None:
        try:
            reader = TrajectoryChunkReaderV2(partial)
            seq, epoch = reader.header()
            if epoch != current_epoch:
                report.add("ORPHANED_CRASH_PARTIAL", "open partial does not belong to current epoch",
                           path=str(partial), partial_epoch=epoch, current_epoch=current_epoch)
                return
            if seq != expected_seq:
                report.add("LIVE_TAIL_SEQUENCE_INVALID", "open tail sequence is not next after manifest",
                           expected=expected_seq, actual=seq)
            frames = list(reader.iter_steps())
            if not frames:
                report.add("LIVE_TAIL_EMPTY", "open tail contains no complete frame", path=str(partial))
                return
            expected_frames[epoch] = self._check_frames(report, frames, epoch=epoch,
                expected_frame_seq=expected_frames.setdefault(epoch, 1), genesis_eids=genesis_eids, location=str(partial))
            report.active_open_tails = 1
            report.note("ACTIVE_OPEN_TAIL", "current-epoch partial is structurally complete but intentionally unsealed",
                        path=str(partial), epoch=epoch, frame_count=len(frames))
        except TrajectoryIntegrityError as exc:
            report.add("LIVE_TAIL_INVALID", str(exc), path=str(partial))

    def verify(self, *, mode: str = "sealed") -> VerificationReportV2:
        mode = str(mode).strip().lower()
        if mode not in {"sealed", "live"}:
            raise ValueError("mode must be sealed or live")
        report = VerificationReportV2()
        chunks_root = self._physical_chunks_root(report)
        entries = self._manifest_entries(report)
        boundary_records, boundary_evidence_valid = self._boundary_records(report)
        latest_boundary_epoch = self._latest_boundary_epoch(boundary_records)
        genesis_eids: set[int] = set()
        try:
            for genesis in _read_jsonl(self.paths.genesis):
                if genesis.get("type") != "ENTITY_GENESIS":
                    report.add("GENESIS_TYPE_INVALID", "unexpected genesis record type")
                    continue
                eid = int(genesis["eid"])
                if eid in genesis_eids:
                    report.add("DUPLICATE_GENESIS", "EID has more than one genesis record", eid=eid)
                genesis_eids.add(eid)
        except (KeyError, TypeError, ValueError, TrajectoryIntegrityError) as exc:
            report.add("GENESIS_INVALID", str(exc))
        previous_sha, expected_seq, last_manifest_epoch = "", 1, 0
        expected_frames: Dict[int, int] = {}
        for entry in entries:
            try:
                seq = int(entry["seq"])
                if seq != expected_seq:
                    report.add("MANIFEST_SEQUENCE_GAP", "non-monotonic chunk sequence", expected=expected_seq, actual=seq)
                expected_seq = seq + 1
                previous_sha, epoch = self._check_entry(report, entry, previous_sha=previous_sha,
                    expected_frames=expected_frames, genesis_eids=genesis_eids,
                    chunks_root=chunks_root)
                if epoch is not None:
                    last_manifest_epoch = max(last_manifest_epoch, epoch)
            except (KeyError, TypeError, ValueError, TrajectoryIntegrityError) as exc:
                report.add("INVALID_CHUNK_ENTRY", str(exc), entry=entry)
        partials = (
            sorted(_iter_physical_chunk_paths(self.paths, "*.partial", report=report))
            if chunks_root is not None
            else []
        )
        if mode == "sealed":
            for partial in partials:
                report.add("INCOMPLETE_FINAL_CHUNK", "unclosed partial chunk retained", path=str(partial))
        elif partials:
            if len(partials) != 1:
                report.add("LIVE_PARTIAL_COUNT_INVALID", "live verification permits exactly one open tail", count=len(partials))
            else:
                current_epoch = max(latest_boundary_epoch, last_manifest_epoch)
                if not boundary_evidence_valid:
                    tail_epoch = None
                    try:
                        _seq, tail_epoch = TrajectoryChunkReaderV2(partials[0]).header()
                    except TrajectoryIntegrityError:
                        tail_epoch = None
                    if tail_epoch is not None:
                        current_epoch = tail_epoch
                self._check_live_tail(report, partials[0], current_epoch=current_epoch,
                                       expected_seq=expected_seq, expected_frames=expected_frames, genesis_eids=genesis_eids)
        manifested = set()
        if chunks_root is not None:
            for entry in entries:
                candidate = (self.paths.base / str(entry.get("path", ""))).resolve()
                if _path_is_within(candidate, chunks_root):
                    manifested.add(str(candidate))
            for complete in _iter_physical_chunk_paths(self.paths, "*.trj2", report=report):
                if str(complete) not in manifested:
                    report.add("ORPHAN_CHUNK", "closed chunk is not present in manifest", path=str(complete))
        return report


def iter_v2_dynamic_records(root_dir: str, *, mode: str = "sealed") -> Iterator[Dict[str, Any]]:
    verifier = TrajectoryV2Verifier(root_dir)
    report = verifier.verify(mode=mode)
    if not report.valid:
        raise TrajectoryIntegrityError(json.dumps(report.to_dict(), sort_keys=True))
    for entry in _read_jsonl(verifier.paths.manifest):
        for frame in TrajectoryChunkReaderV2(verifier.paths.base / str(entry["path"])).iter_steps():
            for record in frame.records:
                yield {"step": frame.step, "frame_seq": frame.frame_seq, "eid": record.eid,
                       "epoch": frame.epoch, "wall_ts_ns": frame.wall_ts_ns,
                       "pos": list(record.pos), "vel": list(record.vel)}


def iter_v2_boundaries(root_dir: str, *, mode: str = "sealed") -> Iterator[Dict[str, Any]]:
    verifier = TrajectoryV2Verifier(root_dir)
    report = verifier.verify(mode=mode)
    if not report.valid:
        raise TrajectoryIntegrityError(json.dumps(report.to_dict(), sort_keys=True))
    yield from _read_jsonl(verifier.paths.boundaries)


__all__ = ["CHUNK_MAX_BYTES", "CHUNK_STEPS", "CODEC_VERSION", "DYNAMIC_RECORD", "DynamicRecordV2",
           "EntityGenesisV2", "FORMAT_VERSION", "RETENTION_POLICY_FULL_V1", "SCHEMA_VERSION", "StepFrameV2",
           "TrajectoryChunkReaderV2", "TrajectoryIntegrityError", "TrajectoryPathsV2", "TrajectoryV2Verifier",
           "TrajectoryV2Writer", "TrajectoryWriteResultV2", "VerificationReportV2", "eid_digest",
           "iter_v2_boundaries", "iter_v2_dynamic_records", "sha256_file"]
