"""Read-only, Class-B writer-freeze evidence for a future root admission.

This module deliberately does not establish a freeze.  An operator-controlled
procedure supplies writer and listener observations; this module validates and
binds those facts to a stable, direct filesystem observation.  It never starts
or stops a process, opens a network connection, writes below the root, or
creates a lock.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import stat
import time
from typing import Callable, TYPE_CHECKING

from .canonical_intent import canonical_intent_text
from .deployment_types import require_digest
from .errors import DeploymentAuthorityError

if TYPE_CHECKING:  # pragma: no cover - imports only support static typing.
    from .root_blocker5_binding import RootWriterFreezeWitness


class RootWriterFreezeEvidenceRefused(DeploymentAuthorityError):
    """The supplied Class-B facts do not prove a frozen writer epoch."""


class RootWriterClass(str, Enum):
    REST_SERVICE = "REST_SERVICE"
    MCP_SERVER = "MCP_SERVER"
    DIRECT_TORMENT_TOOL_OR_SCRIPT = "DIRECT_TORMENT_TOOL_OR_SCRIPT"
    AGENT_RUNNER_OR_OTHER_FABRIC_HOST = "AGENT_RUNNER_OR_OTHER_FABRIC_HOST"
    NONTERMINAL_ROOT_JOB = "NONTERMINAL_ROOT_JOB"


class WriterObservationResult(str, Enum):
    STOPPED = "STOPPED"
    ABSENT = "ABSENT"
    RUNNING = "RUNNING"
    UNRESOLVED = "UNRESOLVED"


class ListenerObservationResult(str, Enum):
    ABSENT = "ABSENT"
    ACTIVE = "ACTIVE"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class WriterProcessObservation:
    """An injected observation, not a process-management instruction."""

    writer_class: RootWriterClass
    observation_mechanism: str
    result: WriterObservationResult

    def __post_init__(self) -> None:
        if not isinstance(self.writer_class, RootWriterClass):
            raise RootWriterFreezeEvidenceRefused("writer class must be typed")
        _require_text(self.observation_mechanism, "writer observation mechanism")
        if not isinstance(self.result, WriterObservationResult):
            raise RootWriterFreezeEvidenceRefused("writer observation result must be typed")

    def payload(self) -> dict[str, str]:
        return {
            "writer_class": self.writer_class.value,
            "observation_mechanism": self.observation_mechanism,
            "result": self.result.value,
        }


@dataclass(frozen=True)
class ListenerObservation:
    """The injected observation of the configured public listener identity."""

    listener_identity: str
    observation_mechanism: str
    result: ListenerObservationResult

    def __post_init__(self) -> None:
        _require_text(self.listener_identity, "listener identity")
        _require_text(self.observation_mechanism, "listener observation mechanism")
        if not isinstance(self.result, ListenerObservationResult):
            raise RootWriterFreezeEvidenceRefused("listener observation result must be typed")

    def payload(self) -> dict[str, str]:
        return {
            "listener_identity": self.listener_identity,
            "observation_mechanism": self.observation_mechanism,
            "result": self.result.value,
        }


@dataclass(frozen=True)
class WorkspaceTreeEntry:
    relative_path: str
    size_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.relative_path, str)
            or not self.relative_path
            or "\\" in self.relative_path
            or self.relative_path.startswith("/")
            or "/../" in f"/{self.relative_path}/"
        ):
            raise RootWriterFreezeEvidenceRefused("workspace tree entry path is not canonical")
        if not isinstance(self.size_bytes, int) or self.size_bytes < 0:
            raise RootWriterFreezeEvidenceRefused("workspace tree entry size is invalid")
        require_digest(self.sha256, "workspace tree entry sha256")

    def payload(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class WorkspaceTreeSnapshot:
    """A content-sensitive snapshot limited exactly to ``workspaces/**``."""

    entries: tuple[WorkspaceTreeEntry, ...]
    tree_digest: str
    file_count: int
    maximum_mtime_ns: int

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or any(
            not isinstance(item, WorkspaceTreeEntry) for item in self.entries
        ):
            raise RootWriterFreezeEvidenceRefused("workspace tree entries must be typed")
        ordered = tuple(sorted(self.entries, key=lambda item: item.relative_path))
        if len({item.relative_path for item in ordered}) != len(ordered):
            raise RootWriterFreezeEvidenceRefused("workspace tree has duplicate relative paths")
        if self.file_count != len(ordered):
            raise RootWriterFreezeEvidenceRefused("workspace tree file count disagrees")
        if not isinstance(self.maximum_mtime_ns, int) or self.maximum_mtime_ns < 0:
            raise RootWriterFreezeEvidenceRefused("workspace tree maximum mtime is invalid")
        expected = _sha256_canonical({"entries": [item.payload() for item in ordered]})
        require_digest(self.tree_digest, "workspace tree digest")
        if self.tree_digest != expected:
            raise RootWriterFreezeEvidenceRefused("workspace tree digest does not recompute")
        object.__setattr__(self, "entries", ordered)

    def payload(self) -> dict[str, object]:
        return {
            "entries": [item.payload() for item in self.entries],
            "tree_digest": self.tree_digest,
            "file_count": self.file_count,
            "maximum_mtime_ns": self.maximum_mtime_ns,
        }


@dataclass(frozen=True)
class RootTreeStabilityObservation:
    """Two operator-timed snapshots; capture itself never sleeps."""

    t0_ns: int
    t1_ns: int
    minimum_delta_seconds: int
    snapshot_t0: WorkspaceTreeSnapshot
    snapshot_t1: WorkspaceTreeSnapshot

    def __post_init__(self) -> None:
        if not isinstance(self.t0_ns, int) or not isinstance(self.t1_ns, int) or self.t0_ns < 0:
            raise RootWriterFreezeEvidenceRefused("tree stability timestamps must be non-negative integers")
        if not isinstance(self.minimum_delta_seconds, int) or self.minimum_delta_seconds < 0:
            raise RootWriterFreezeEvidenceRefused("minimum tree stability delta must be a non-negative integer")
        if not isinstance(self.snapshot_t0, WorkspaceTreeSnapshot) or not isinstance(
            self.snapshot_t1, WorkspaceTreeSnapshot,
        ):
            raise RootWriterFreezeEvidenceRefused("tree stability snapshots must be typed")
        if self.t1_ns < self.t0_ns:
            raise RootWriterFreezeEvidenceRefused("tree stability t1 precedes t0")
        if self.t1_ns - self.t0_ns < self.minimum_delta_seconds * 1_000_000_000:
            raise RootWriterFreezeEvidenceRefused("tree stability interval is shorter than the supplied minimum")
        if (
            self.snapshot_t0.tree_digest != self.snapshot_t1.tree_digest
            or self.snapshot_t0.file_count != self.snapshot_t1.file_count
        ):
            raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_T0_T1_TREE_DRIFT")
        if max(
            self.snapshot_t0.maximum_mtime_ns,
            self.snapshot_t1.maximum_mtime_ns,
        ) >= self.t0_ns:
            raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_MAX_MTIME_NOT_BEFORE_T0")

    @property
    def delta_seconds(self) -> str:
        delta_ns = self.t1_ns - self.t0_ns
        return f"{delta_ns // 1_000_000_000}.{delta_ns % 1_000_000_000:09d}"

    def payload(self) -> dict[str, object]:
        return {
            "t0_ns": self.t0_ns,
            "t1_ns": self.t1_ns,
            "delta_s": self.delta_seconds,
            "minimum_delta_seconds": self.minimum_delta_seconds,
            **self.snapshot_t1.payload(),
        }


@dataclass(frozen=True)
class PostCaptureStabilityObservation:
    t2_ns: int
    snapshot_t2: WorkspaceTreeSnapshot

    def __post_init__(self) -> None:
        if not isinstance(self.t2_ns, int) or self.t2_ns < 0:
            raise RootWriterFreezeEvidenceRefused("post-capture timestamp must be a non-negative integer")
        if not isinstance(self.snapshot_t2, WorkspaceTreeSnapshot):
            raise RootWriterFreezeEvidenceRefused("post-capture snapshot must be typed")

    def payload(self) -> dict[str, object]:
        return {"t2_ns": self.t2_ns, **self.snapshot_t2.payload()}


@dataclass(frozen=True)
class RootJobObservation:
    """Bounded clone/repair-job status result; historical terminal jobs are benign."""

    terminal_job_count: int
    observation_mechanism: str = "ROOT_JOBS_CLONE_REPAIR_STATUS_V1"

    def __post_init__(self) -> None:
        if not isinstance(self.terminal_job_count, int) or self.terminal_job_count < 0:
            raise RootWriterFreezeEvidenceRefused("terminal job count is invalid")
        _require_text(self.observation_mechanism, "root jobs observation mechanism")

    def payload(self) -> dict[str, object]:
        return {
            "terminal_job_count": self.terminal_job_count,
            "observation_mechanism": self.observation_mechanism,
            "nonterminal_job_count": 0,
        }


@dataclass(frozen=True)
class RootWriterFreezeEvidencePayload:
    """Immutable administrative observation payload, never a freeze authority."""

    data_root_identity: str
    writer_freeze_operation_identity: str
    operator_identity: str
    covered_writer_classes: tuple[WriterProcessObservation, ...]
    listener_observation: ListenerObservation
    job_observation: RootJobObservation
    stability_observation: RootTreeStabilityObservation
    post_capture_stability: PostCaptureStabilityObservation
    external_owner_observation_digest: str
    expected_root_admission_description_contract: str
    invalidation_rule_version: str
    freeze_mechanism: str = "STOP_AND_VERIFY_V1"

    CONTRACT = "TORMENT_ROOT_WRITER_FREEZE_EVIDENCE"
    VERSION = 1

    def __post_init__(self) -> None:
        for name in (
            "data_root_identity",
            "writer_freeze_operation_identity",
            "operator_identity",
            "expected_root_admission_description_contract",
            "invalidation_rule_version",
        ):
            _require_text(getattr(self, name), name)
        if self.freeze_mechanism != "STOP_AND_VERIFY_V1":
            raise RootWriterFreezeEvidenceRefused("unsupported writer-freeze mechanism")
        observations = _validated_writer_observations(self.covered_writer_classes)
        if not isinstance(self.listener_observation, ListenerObservation):
            raise RootWriterFreezeEvidenceRefused("listener observation must be typed")
        _require_listener_absent(self.listener_observation)
        if not isinstance(self.job_observation, RootJobObservation):
            raise RootWriterFreezeEvidenceRefused("root jobs observation must be typed")
        if not isinstance(self.stability_observation, RootTreeStabilityObservation):
            raise RootWriterFreezeEvidenceRefused("tree stability observation must be typed")
        if not isinstance(self.post_capture_stability, PostCaptureStabilityObservation):
            raise RootWriterFreezeEvidenceRefused("post-capture stability observation must be typed")
        if self.post_capture_stability.t2_ns < self.stability_observation.t1_ns:
            raise RootWriterFreezeEvidenceRefused("post-capture observation precedes t1")
        if (
            self.post_capture_stability.snapshot_t2.tree_digest
            != self.stability_observation.snapshot_t1.tree_digest
        ):
            raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_T2_TREE_DRIFT")
        if observations[RootWriterClass.NONTERMINAL_ROOT_JOB].result is not WriterObservationResult.ABSENT:
            raise RootWriterFreezeEvidenceRefused("root jobs must be absent rather than merely stopped")
        require_digest(self.external_owner_observation_digest, "external owner observation digest")
        object.__setattr__(self, "covered_writer_classes", tuple(
            observations[item] for item in sorted(observations, key=lambda value: value.value)
        ))

    @property
    def digest(self) -> str:
        return _sha256_canonical(self.payload())

    @property
    def source_tree_snapshot(self) -> WorkspaceTreeSnapshot:
        return self.post_capture_stability.snapshot_t2

    def payload(self) -> dict[str, object]:
        return {
            "contract": self.CONTRACT,
            "version": self.VERSION,
            "data_root_identity": self.data_root_identity,
            "writer_freeze_operation_identity": self.writer_freeze_operation_identity,
            "operator_identity": self.operator_identity,
            "freeze_mechanism": self.freeze_mechanism,
            "covered_writer_classes": [item.payload() for item in self.covered_writer_classes],
            "listener_observation": self.listener_observation.payload(),
            "job_observation": self.job_observation.payload(),
            "stability_observation": self.stability_observation.payload(),
            "post_capture_stability": self.post_capture_stability.payload(),
            "external_owner_observation_digest": self.external_owner_observation_digest,
            "expected_root_admission_description_contract": self.expected_root_admission_description_contract,
            "invalidation_rule_version": self.invalidation_rule_version,
        }


@dataclass(frozen=True)
class RootWriterFreezeRecheck:
    """Fresh Class-B observations required at P2, P4, and immediately pre-P6."""

    covered_writer_classes: tuple[WriterProcessObservation, ...]
    listener_observation: ListenerObservation
    job_observation: RootJobObservation
    external_owner_observation_digest: str

    def __post_init__(self) -> None:
        observations = _validated_writer_observations(self.covered_writer_classes)
        if observations[RootWriterClass.NONTERMINAL_ROOT_JOB].result is not WriterObservationResult.ABSENT:
            raise RootWriterFreezeEvidenceRefused("fresh root job observation must be absent")
        if not isinstance(self.listener_observation, ListenerObservation):
            raise RootWriterFreezeEvidenceRefused("fresh listener observation must be typed")
        _require_listener_absent(self.listener_observation)
        if not isinstance(self.job_observation, RootJobObservation):
            raise RootWriterFreezeEvidenceRefused("fresh root jobs observation must be typed")
        require_digest(self.external_owner_observation_digest, "fresh external owner observation digest")
        object.__setattr__(self, "covered_writer_classes", tuple(
            observations[item] for item in sorted(observations, key=lambda value: value.value)
        ))


@dataclass(frozen=True)
class CapturedRootWriterFreezeEvidence:
    """The payload and its existing witness binding, held outside ``data/``."""

    payload: RootWriterFreezeEvidencePayload
    witness: "RootWriterFreezeWitness"

    def __post_init__(self) -> None:
        if not isinstance(self.payload, RootWriterFreezeEvidencePayload):
            raise RootWriterFreezeEvidenceRefused("captured writer freeze payload must be typed")
        bind_root_writer_freeze_witness(payload=self.payload, witness=self.witness)


def snapshot_root_workspaces(*, data_root: str | Path) -> WorkspaceTreeSnapshot:
    """Read only ``<root>/workspaces/**`` and reject every link/reparse point."""

    root = _real_root(data_root)
    workspaces = root / "workspaces"
    if not workspaces.exists():
        return _workspace_snapshot(())
    _require_real_directory(workspaces, "workspaces root")
    entries: list[tuple[WorkspaceTreeEntry, int]] = []
    _collect_workspace_files(workspaces, root, entries)
    return _workspace_snapshot(tuple(entries))


def observe_root_clone_repair_jobs(*, data_root: str | Path) -> RootJobObservation:
    """Read the established clone/repair JSON status files without changing them."""

    root = _real_root(data_root)
    jobs_root = root / "jobs"
    if not jobs_root.exists():
        return RootJobObservation(terminal_job_count=0)
    _require_real_directory(jobs_root, "jobs root")
    terminal_count = 0
    terminal_statuses = {"done", "error", "cancelled", "abandoned"}
    for kind in ("clone", "repair"):
        kind_root = jobs_root / kind
        if not kind_root.exists():
            continue
        _require_real_directory(kind_root, f"{kind} jobs root")
        for candidate in sorted(kind_root.iterdir(), key=lambda item: item.name):
            _reject_link_or_reparse(candidate, f"{kind} job entry")
            if not candidate.is_file() or candidate.suffix.lower() != ".json":
                continue
            try:
                with candidate.open("r", encoding="utf-8") as stream:
                    record = json.load(stream)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RootWriterFreezeEvidenceRefused("root job status is unreadable") from exc
            status_value = record.get("status") if isinstance(record, dict) else None
            if not isinstance(status_value, str) or status_value not in terminal_statuses:
                raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_NONTERMINAL_JOB_PRESENT")
            terminal_count += 1
    return RootJobObservation(terminal_job_count=terminal_count)


def capture_root_writer_freeze_evidence(
    *,
    data_root: str | Path,
    data_root_identity: str,
    writer_freeze_operation_identity: str,
    operator_identity: str,
    covered_writer_classes: tuple[WriterProcessObservation, ...],
    listener_observation: ListenerObservation,
    external_owner_observation_digest: str,
    expected_root_admission_description_contract: str,
    invalidation_rule_version: str,
    minimum_delta_seconds: int,
    snapshotter: Callable[..., WorkspaceTreeSnapshot] = snapshot_root_workspaces,
    job_observer: Callable[..., RootJobObservation] = observe_root_clone_repair_jobs,
    clock_ns: Callable[[], int] = time.time_ns,
) -> CapturedRootWriterFreezeEvidence:
    """Capture three direct snapshots without waiting, writing, or controlling hosts.

    The caller selects ``minimum_delta_seconds`` as part of its administration
    procedure.  A zero value is useful only for synthetic qualification; this
    helper never substitutes an arbitrary production sleep.
    """

    _real_root(data_root)
    t0_ns = _clock_value(clock_ns)
    snapshot_t0 = _snapshot(snapshotter, data_root)
    t1_ns = _clock_value(clock_ns)
    snapshot_t1 = _snapshot(snapshotter, data_root)
    stability = RootTreeStabilityObservation(
        t0_ns=t0_ns,
        t1_ns=t1_ns,
        minimum_delta_seconds=minimum_delta_seconds,
        snapshot_t0=snapshot_t0,
        snapshot_t1=snapshot_t1,
    )
    jobs = _jobs(job_observer, data_root)
    t2_ns = _clock_value(clock_ns)
    snapshot_t2 = _snapshot(snapshotter, data_root)
    payload = RootWriterFreezeEvidencePayload(
        data_root_identity=data_root_identity,
        writer_freeze_operation_identity=writer_freeze_operation_identity,
        operator_identity=operator_identity,
        covered_writer_classes=covered_writer_classes,
        listener_observation=listener_observation,
        job_observation=jobs,
        stability_observation=stability,
        post_capture_stability=PostCaptureStabilityObservation(t2_ns=t2_ns, snapshot_t2=snapshot_t2),
        external_owner_observation_digest=external_owner_observation_digest,
        expected_root_admission_description_contract=expected_root_admission_description_contract,
        invalidation_rule_version=invalidation_rule_version,
    )
    from .root_blocker5_binding import RootWriterFreezeWitness

    witness = RootWriterFreezeWitness(
        data_root_identity=data_root_identity,
        writer_freeze_operation_identity=writer_freeze_operation_identity,
        writer_evidence_digest=payload.digest,
    )
    return CapturedRootWriterFreezeEvidence(payload=payload, witness=witness)


def bind_root_writer_freeze_witness(
    *, payload: RootWriterFreezeEvidencePayload, witness: "RootWriterFreezeWitness",
) -> None:
    """Bind the payload to the pre-existing witness without minting authority."""

    from .root_blocker5_binding import RootWriterFreezeWitness

    if not isinstance(payload, RootWriterFreezeEvidencePayload) or not isinstance(
        witness, RootWriterFreezeWitness,
    ):
        raise RootWriterFreezeEvidenceRefused("writer freeze payload and witness must be typed")
    if (
        witness.data_root_identity != payload.data_root_identity
        or witness.writer_freeze_operation_identity != payload.writer_freeze_operation_identity
        or witness.writer_evidence_digest != payload.digest
    ):
        raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_WITNESS_PAYLOAD_MISMATCH")


def root_writer_freeze_evidence_payload_from_payload(value: object) -> RootWriterFreezeEvidencePayload:
    """Decode only the current exact evidence contract; malformed input never downgrades."""

    required = {
        "contract", "version", "data_root_identity", "writer_freeze_operation_identity",
        "operator_identity", "freeze_mechanism", "covered_writer_classes",
        "listener_observation", "job_observation", "stability_observation",
        "post_capture_stability", "external_owner_observation_digest",
        "expected_root_admission_description_contract", "invalidation_rule_version",
    }
    if not isinstance(value, dict) or value.get("contract") != RootWriterFreezeEvidencePayload.CONTRACT:
        raise RootWriterFreezeEvidenceRefused("writer-freeze evidence contract is unsupported")
    if value.get("version") != RootWriterFreezeEvidencePayload.VERSION:
        raise RootWriterFreezeEvidenceRefused("writer-freeze evidence version is unsupported")
    if set(value) != required:
        raise RootWriterFreezeEvidenceRefused("writer-freeze evidence payload shape is invalid")
    try:
        observations_value = value["covered_writer_classes"]
        if not isinstance(observations_value, list):
            raise ValueError("writer observations are not a list")
        observations = tuple(_writer_observation_from_payload(item) for item in observations_value)
        listener = _listener_observation_from_payload(value["listener_observation"])
        jobs = _job_observation_from_payload(value["job_observation"])
        stability_value = value["stability_observation"]
        if not isinstance(stability_value, dict):
            raise ValueError("stability is not a mapping")
        stability_required = {
            "t0_ns", "t1_ns", "delta_s", "minimum_delta_seconds", "entries",
            "tree_digest", "file_count", "maximum_mtime_ns",
        }
        if set(stability_value) != stability_required:
            raise ValueError("stability shape is invalid")
        stable_snapshot = _snapshot_from_payload(stability_value)
        stability = RootTreeStabilityObservation(
            t0_ns=stability_value["t0_ns"],
            t1_ns=stability_value["t1_ns"],
            minimum_delta_seconds=stability_value["minimum_delta_seconds"],
            snapshot_t0=stable_snapshot,
            snapshot_t1=stable_snapshot,
        )
        if stability_value["delta_s"] != stability.delta_seconds:
            raise ValueError("stability delta is noncanonical")
        post_value = value["post_capture_stability"]
        if not isinstance(post_value, dict):
            raise ValueError("post-capture stability is not a mapping")
        post_required = {"t2_ns", "entries", "tree_digest", "file_count", "maximum_mtime_ns"}
        if set(post_value) != post_required:
            raise ValueError("post-capture stability shape is invalid")
        result = RootWriterFreezeEvidencePayload(
            data_root_identity=value["data_root_identity"],
            writer_freeze_operation_identity=value["writer_freeze_operation_identity"],
            operator_identity=value["operator_identity"],
            covered_writer_classes=observations,
            listener_observation=listener,
            job_observation=jobs,
            stability_observation=stability,
            post_capture_stability=PostCaptureStabilityObservation(
                t2_ns=post_value["t2_ns"], snapshot_t2=_snapshot_from_payload(post_value),
            ),
            external_owner_observation_digest=value["external_owner_observation_digest"],
            expected_root_admission_description_contract=value[
                "expected_root_admission_description_contract"
            ],
            invalidation_rule_version=value["invalidation_rule_version"],
            freeze_mechanism=value["freeze_mechanism"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RootWriterFreezeEvidenceRefused("writer-freeze evidence payload is invalid") from exc
    if canonical_intent_text(result.payload()) != canonical_intent_text(value):
        raise RootWriterFreezeEvidenceRefused("writer-freeze evidence payload is noncanonical")
    return result


def recheck_root_writer_freeze_evidence(
    *,
    data_root: str | Path,
    payload: RootWriterFreezeEvidencePayload,
    witness: "RootWriterFreezeWitness",
    recheck: RootWriterFreezeRecheck,
    expected_external_owner_observation_digest: str,
) -> None:
    """Refuse a stale epoch; this function never refreshes evidence automatically."""

    bind_root_writer_freeze_witness(payload=payload, witness=witness)
    if not isinstance(recheck, RootWriterFreezeRecheck):
        raise RootWriterFreezeEvidenceRefused("fresh writer-freeze recheck is required")
    require_digest(expected_external_owner_observation_digest, "expected external owner digest")
    if (
        payload.external_owner_observation_digest != expected_external_owner_observation_digest
        or recheck.external_owner_observation_digest != expected_external_owner_observation_digest
    ):
        raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_EXTERNAL_OWNER_DRIFT")
    current = snapshot_root_workspaces(data_root=data_root)
    frozen = payload.source_tree_snapshot
    if (
        current.tree_digest != frozen.tree_digest
        or current.file_count != frozen.file_count
        or current.maximum_mtime_ns != frozen.maximum_mtime_ns
    ):
        raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_SOURCE_TREE_DRIFT")
    observed_jobs = observe_root_clone_repair_jobs(data_root=data_root)
    del observed_jobs  # Construction itself refuses any non-terminal clone/repair job.


def _validated_writer_observations(
    value: tuple[WriterProcessObservation, ...],
) -> dict[RootWriterClass, WriterProcessObservation]:
    if not isinstance(value, tuple) or any(not isinstance(item, WriterProcessObservation) for item in value):
        raise RootWriterFreezeEvidenceRefused("covered writer observations must be a typed tuple")
    observed = {item.writer_class: item for item in value}
    if len(observed) != len(value) or set(observed) != set(RootWriterClass):
        raise RootWriterFreezeEvidenceRefused("covered writer observations are incomplete or duplicate")
    if any(item.result not in {WriterObservationResult.STOPPED, WriterObservationResult.ABSENT} for item in observed.values()):
        raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_WRITER_NOT_STOPPED_OR_ABSENT")
    return observed


def _require_listener_absent(value: ListenerObservation) -> None:
    if value.result is not ListenerObservationResult.ABSENT:
        raise RootWriterFreezeEvidenceRefused("ROOT_WRITER_FREEZE_LISTENER_PRESENT_OR_UNRESOLVED")


def _real_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise RootWriterFreezeEvidenceRefused("writer-freeze observation requires a root path")
    candidate = Path(value).expanduser()
    _require_real_directory(candidate, "data root")
    return candidate.resolve()


def _require_real_directory(path: Path, label: str) -> None:
    _reject_link_or_reparse(path, label)
    if not path.is_dir():
        raise RootWriterFreezeEvidenceRefused(f"{label} must be a real directory")


def _reject_link_or_reparse(path: Path, label: str) -> None:
    try:
        information = path.lstat()
    except OSError as exc:
        raise RootWriterFreezeEvidenceRefused(f"{label} cannot be inspected") from exc
    attributes = getattr(information, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if stat.S_ISLNK(information.st_mode) or attributes & reparse_flag:
        raise RootWriterFreezeEvidenceRefused(f"{label} must not be a symbolic link or reparse point")


def _collect_workspace_files(
    directory: Path,
    root: Path,
    result: list[tuple[WorkspaceTreeEntry, int]],
) -> None:
    for candidate in sorted(directory.iterdir(), key=lambda item: item.name):
        _reject_link_or_reparse(candidate, "workspace tree entry")
        if candidate.is_dir():
            _collect_workspace_files(candidate, root, result)
            continue
        if not candidate.is_file():
            raise RootWriterFreezeEvidenceRefused("workspace tree contains an unsupported non-file entry")
        before = candidate.stat()
        digest = hashlib.sha256()
        try:
            with candidate.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
        except OSError as exc:
            raise RootWriterFreezeEvidenceRefused("workspace tree file cannot be read") from exc
        after = candidate.stat()
        if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
            raise RootWriterFreezeEvidenceRefused("workspace tree file changed during snapshot")
        relative = candidate.relative_to(root).as_posix()
        result.append((WorkspaceTreeEntry(relative, before.st_size, digest.hexdigest()), before.st_mtime_ns))


def _workspace_snapshot(entries: tuple[tuple[WorkspaceTreeEntry, int], ...]) -> WorkspaceTreeSnapshot:
    ordered = tuple(sorted(entries, key=lambda item: item[0].relative_path))
    tree_entries = tuple(item[0] for item in ordered)
    return WorkspaceTreeSnapshot(
        entries=tree_entries,
        tree_digest=_sha256_canonical({"entries": [item.payload() for item in tree_entries]}),
        file_count=len(tree_entries),
        maximum_mtime_ns=max((item[1] for item in ordered), default=0),
    )


def _sha256_canonical(value: object) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


def _writer_observation_from_payload(value: object) -> WriterProcessObservation:
    required = {"writer_class", "observation_mechanism", "result"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("writer observation shape is invalid")
    return WriterProcessObservation(
        writer_class=RootWriterClass(value["writer_class"]),
        observation_mechanism=value["observation_mechanism"],
        result=WriterObservationResult(value["result"]),
    )


def _listener_observation_from_payload(value: object) -> ListenerObservation:
    required = {"listener_identity", "observation_mechanism", "result"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("listener observation shape is invalid")
    return ListenerObservation(
        listener_identity=value["listener_identity"],
        observation_mechanism=value["observation_mechanism"],
        result=ListenerObservationResult(value["result"]),
    )


def _job_observation_from_payload(value: object) -> RootJobObservation:
    required = {"terminal_job_count", "observation_mechanism", "nonterminal_job_count"}
    if not isinstance(value, dict) or set(value) != required or value["nonterminal_job_count"] != 0:
        raise ValueError("root jobs observation shape is invalid")
    return RootJobObservation(
        terminal_job_count=value["terminal_job_count"],
        observation_mechanism=value["observation_mechanism"],
    )


def _snapshot_from_payload(value: object) -> WorkspaceTreeSnapshot:
    required = {"entries", "tree_digest", "file_count", "maximum_mtime_ns"}
    if not isinstance(value, dict) or not required <= set(value) or not isinstance(value["entries"], list):
        raise ValueError("workspace tree snapshot shape is invalid")
    entries = tuple(
        WorkspaceTreeEntry(
            relative_path=item["relative_path"], size_bytes=item["size_bytes"], sha256=item["sha256"],
        )
        for item in value["entries"]
        if isinstance(item, dict) and set(item) == {"relative_path", "size_bytes", "sha256"}
    )
    if len(entries) != len(value["entries"]):
        raise ValueError("workspace tree entry shape is invalid")
    return WorkspaceTreeSnapshot(
        entries=entries,
        tree_digest=value["tree_digest"],
        file_count=value["file_count"],
        maximum_mtime_ns=value["maximum_mtime_ns"],
    )


def _snapshot(
    snapshotter: Callable[..., WorkspaceTreeSnapshot], data_root: str | Path,
) -> WorkspaceTreeSnapshot:
    try:
        result = snapshotter(data_root=data_root)
    except TypeError:
        result = snapshotter(data_root)  # type: ignore[misc]
    if not isinstance(result, WorkspaceTreeSnapshot):
        raise RootWriterFreezeEvidenceRefused("snapshot observer returned an invalid result")
    return result


def _jobs(job_observer: Callable[..., RootJobObservation], data_root: str | Path) -> RootJobObservation:
    try:
        result = job_observer(data_root=data_root)
    except TypeError:
        result = job_observer(data_root)  # type: ignore[misc]
    if not isinstance(result, RootJobObservation):
        raise RootWriterFreezeEvidenceRefused("root jobs observer returned an invalid result")
    return result


def _clock_value(clock_ns: Callable[[], int]) -> int:
    value = clock_ns()
    if not isinstance(value, int) or value < 0:
        raise RootWriterFreezeEvidenceRefused("clock observer returned an invalid timestamp")
    return value


def _require_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise RootWriterFreezeEvidenceRefused(f"{label} must be bounded non-empty text")


__all__ = [
    "CapturedRootWriterFreezeEvidence",
    "ListenerObservation",
    "ListenerObservationResult",
    "PostCaptureStabilityObservation",
    "RootJobObservation",
    "RootTreeStabilityObservation",
    "RootWriterClass",
    "RootWriterFreezeEvidencePayload",
    "RootWriterFreezeEvidenceRefused",
    "RootWriterFreezeRecheck",
    "WorkspaceTreeEntry",
    "WorkspaceTreeSnapshot",
    "WriterObservationResult",
    "WriterProcessObservation",
    "bind_root_writer_freeze_witness",
    "capture_root_writer_freeze_evidence",
    "observe_root_clone_repair_jobs",
    "recheck_root_writer_freeze_evidence",
    "root_writer_freeze_evidence_payload_from_payload",
    "snapshot_root_workspaces",
]
