"""File-backed administrative checkpoints for future real-admission runs.

This module retains process-administration status outside a caller-supplied
data root.  It is not a production runtime, source adapter, writer-freeze
authority, SQLite API, or admission/cutover implementation.  In particular,
it never opens the data root or determines whether a future operation may run.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
import os
from pathlib import Path
import re
import time
from typing import Any
from uuid import uuid4


_STATE_FILENAME = "administration_state.json"
_EVENTS_FILENAME = "administration_events.jsonl"
_STATE_CONTRACT = "TORMENT_FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_STATE"
_EVENT_CONTRACT = "TORMENT_FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_EVENT"
_VERSION = 1
_OPERATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class FileBackedRealAdmissionAdministrationRefused(RuntimeError):
    """The administrative result destination or state is unsafe to use."""


class FileBackedRealAdmissionAdministrationWriteError(RuntimeError):
    """A checkpoint write failed; the prior canonical state remains current."""


class RealAdmissionAdministrationState(StrEnum):
    """Durable administrative milestones, never admission authority."""

    RUNNER_STARTED = "RUNNER_STARTED"
    PRECHECK_STARTED = "PRECHECK_STARTED"
    PRECHECK_PASS = "PRECHECK_PASS"
    PRECHECK_REFUSED = "PRECHECK_REFUSED"
    CAPTURE_STARTED = "CAPTURE_STARTED"
    CAPTURE_RETURNED = "CAPTURE_RETURNED"
    CAPTURE_REFUSED = "CAPTURE_REFUSED"
    CAPTURE_EXCEPTION = "CAPTURE_EXCEPTION"
    DIRECT_PREPARATION_PASS = "DIRECT_PREPARATION_PASS"
    DIRECT_PREPARATION_REFUSED = "DIRECT_PREPARATION_REFUSED"
    P1_NOT_AUTHORIZED = "P1_NOT_AUTHORIZED"
    P1_READY = "P1_READY"
    P1_STARTED = "P1_STARTED"
    P1_PASS = "P1_PASS"
    P1_FAILED_AFTER_DURABLE_STATE = "P1_FAILED_AFTER_DURABLE_STATE"
    FINAL_VERIFICATION_PASS = "FINAL_VERIFICATION_PASS"
    FINAL_STOP = "FINAL_STOP"
    ADMINISTRATION_EXCEPTION = "ADMINISTRATION_EXCEPTION"


_ALLOWED_NEXT: dict[RealAdmissionAdministrationState | None, frozenset[RealAdmissionAdministrationState]] = {
    None: frozenset({RealAdmissionAdministrationState.RUNNER_STARTED}),
    RealAdmissionAdministrationState.RUNNER_STARTED: frozenset({
        RealAdmissionAdministrationState.PRECHECK_STARTED,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.PRECHECK_STARTED: frozenset({
        RealAdmissionAdministrationState.PRECHECK_PASS,
        RealAdmissionAdministrationState.PRECHECK_REFUSED,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.PRECHECK_PASS: frozenset({
        RealAdmissionAdministrationState.CAPTURE_STARTED,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.PRECHECK_REFUSED: frozenset({
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.CAPTURE_STARTED: frozenset({
        RealAdmissionAdministrationState.CAPTURE_RETURNED,
        RealAdmissionAdministrationState.CAPTURE_REFUSED,
        RealAdmissionAdministrationState.CAPTURE_EXCEPTION,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.CAPTURE_RETURNED: frozenset({
        RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
        RealAdmissionAdministrationState.DIRECT_PREPARATION_REFUSED,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.CAPTURE_REFUSED: frozenset({
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.CAPTURE_EXCEPTION: frozenset({
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS: frozenset({
        RealAdmissionAdministrationState.P1_NOT_AUTHORIZED,
        RealAdmissionAdministrationState.P1_READY,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.DIRECT_PREPARATION_REFUSED: frozenset({
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.P1_NOT_AUTHORIZED: frozenset({
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.P1_READY: frozenset({
        RealAdmissionAdministrationState.P1_STARTED,
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.P1_STARTED: frozenset({
        RealAdmissionAdministrationState.P1_PASS,
        RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.P1_PASS: frozenset({
        RealAdmissionAdministrationState.FINAL_VERIFICATION_PASS,
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE: frozenset({
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.FINAL_VERIFICATION_PASS: frozenset({
        RealAdmissionAdministrationState.FINAL_STOP,
        RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION,
    }),
    RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION: frozenset({
        RealAdmissionAdministrationState.FINAL_STOP,
    }),
    RealAdmissionAdministrationState.FINAL_STOP: frozenset(),
}


@dataclass(frozen=True)
class RealAdmissionAdministrationCheckpoint:
    """One complete canonical administrative state, retained outside ``data/``."""

    operation_id: str
    state: RealAdmissionAdministrationState
    sequence: int
    recorded_at_ns: int
    detail: object | None = None

    def __post_init__(self) -> None:
        _require_operation_id(self.operation_id)
        if not isinstance(self.state, RealAdmissionAdministrationState):
            raise FileBackedRealAdmissionAdministrationRefused("administration state must be typed")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 1:
            raise FileBackedRealAdmissionAdministrationRefused("administration sequence must be a positive integer")
        if not isinstance(self.recorded_at_ns, int) or isinstance(self.recorded_at_ns, bool) or self.recorded_at_ns < 1:
            raise FileBackedRealAdmissionAdministrationRefused("administration timestamp must be a positive integer")
        _canonical_json_value(self.detail, "administration detail")

    def payload(self) -> dict[str, object]:
        return {
            "contract": _STATE_CONTRACT,
            "version": _VERSION,
            "operation_id": self.operation_id,
            "state": self.state.value,
            "sequence": self.sequence,
            "recorded_at_ns": self.recorded_at_ns,
            "detail": _canonical_json_value(self.detail, "administration detail"),
        }


class FileBackedRealAdmissionAdministrationRunner:
    """Atomically retain an operator-owned run ledger outside the data root.

    The caller owns every actual precheck, capture, preparation, P1, and final
    verification.  This class only records their supplied state transitions.
    """

    def __init__(
        self,
        *,
        data_root: str | Path,
        result_directory: str | Path,
        operation_id: str,
        append_events: bool = True,
    ) -> None:
        _require_operation_id(operation_id)
        if not isinstance(append_events, bool):
            raise FileBackedRealAdmissionAdministrationRefused("append_events must be boolean")
        self._data_root = _resolve_path(data_root, "data_root")
        requested_result_directory = _resolve_path(result_directory, "result_directory")
        if _is_within(requested_result_directory, self._data_root):
            raise FileBackedRealAdmissionAdministrationRefused(
                "administration result directory must resolve outside data_root"
            )
        try:
            requested_result_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise FileBackedRealAdmissionAdministrationWriteError(
                "administration result directory cannot be created"
            ) from exc
        self._result_directory = requested_result_directory.resolve()
        if _is_within(self._result_directory, self._data_root):
            raise FileBackedRealAdmissionAdministrationRefused(
                "administration result directory resolved inside data_root"
            )
        if not self._result_directory.is_dir():
            raise FileBackedRealAdmissionAdministrationWriteError(
                "administration result directory is not a directory"
            )
        self._operation_id = operation_id
        self._append_events = append_events
        self._current = self._load_current_if_present()

    @property
    def result_directory(self) -> Path:
        return self._result_directory

    @property
    def state_path(self) -> Path:
        return self._result_directory / _STATE_FILENAME

    @property
    def events_path(self) -> Path:
        return self._result_directory / _EVENTS_FILENAME

    @property
    def current_checkpoint(self) -> RealAdmissionAdministrationCheckpoint | None:
        return self._current

    def checkpoint(
        self,
        state: RealAdmissionAdministrationState,
        *,
        detail: object | None = None,
    ) -> RealAdmissionAdministrationCheckpoint:
        """Atomically replace the canonical state, then append non-authoritative evidence."""

        if not isinstance(state, RealAdmissionAdministrationState):
            raise FileBackedRealAdmissionAdministrationRefused("administration checkpoint state must be typed")
        prior_state = None if self._current is None else self._current.state
        if state not in _ALLOWED_NEXT[prior_state]:
            prior = "NONE" if prior_state is None else prior_state.value
            raise FileBackedRealAdmissionAdministrationRefused(
                f"administration transition is not allowed: {prior} -> {state.value}"
            )
        checkpoint = RealAdmissionAdministrationCheckpoint(
            operation_id=self._operation_id,
            state=state,
            sequence=1 if self._current is None else self._current.sequence + 1,
            recorded_at_ns=time.time_ns(),
            detail=detail,
        )
        self._write_current_state(checkpoint)
        self._current = checkpoint
        if self._append_events:
            self._append_event(checkpoint)
        return checkpoint

    def record_administration_exception(
        self,
        exception: BaseException,
        *,
        detail: object | None = None,
    ) -> RealAdmissionAdministrationCheckpoint:
        """Retain a bounded exception description without assigning new authority."""

        if not isinstance(exception, BaseException):
            raise FileBackedRealAdmissionAdministrationRefused("exception record requires BaseException")
        value: dict[str, object] = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
        }
        if detail is not None:
            value["detail"] = _canonical_json_value(detail, "administration exception detail")
        return self.checkpoint(RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION, detail=value)

    def _load_current_if_present(self) -> RealAdmissionAdministrationCheckpoint | None:
        path = self.state_path
        if not path.exists():
            return None
        if path.is_symlink() or not path.is_file():
            raise FileBackedRealAdmissionAdministrationRefused("administration state path must be a regular file")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise FileBackedRealAdmissionAdministrationRefused("administration state cannot be read") from exc
        checkpoint = _checkpoint_from_bytes(raw)
        if checkpoint.operation_id != self._operation_id:
            raise FileBackedRealAdmissionAdministrationRefused(
                "administration state operation_id does not match requested operation"
            )
        return checkpoint

    def _write_current_state(self, checkpoint: RealAdmissionAdministrationCheckpoint) -> None:
        payload = _canonical_bytes(checkpoint.payload())
        temporary_path = self._result_directory / f".{_STATE_FILENAME}.{uuid4().hex}.tmp"
        try:
            with temporary_path.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.state_path)
        except OSError as exc:
            try:
                if temporary_path.exists():
                    temporary_path.unlink()
            except OSError:
                pass
            raise FileBackedRealAdmissionAdministrationWriteError(
                "administration state atomic checkpoint failed; prior state remains authoritative"
            ) from exc

    def _append_event(self, checkpoint: RealAdmissionAdministrationCheckpoint) -> None:
        event_path = self.events_path
        if event_path.is_symlink() or (event_path.exists() and not event_path.is_file()):
            raise FileBackedRealAdmissionAdministrationRefused(
                "administration event path must be absent or a regular non-symlink file"
            )
        event = {
            "contract": _EVENT_CONTRACT,
            "version": _VERSION,
            "operation_id": checkpoint.operation_id,
            "state": checkpoint.state.value,
            "sequence": checkpoint.sequence,
            "recorded_at_ns": checkpoint.recorded_at_ns,
        }
        try:
            with event_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(_canonical_json(event) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise FileBackedRealAdmissionAdministrationWriteError(
                "administration state was checkpointed but event append failed"
            ) from exc


def _checkpoint_from_bytes(raw: bytes) -> RealAdmissionAdministrationCheckpoint:
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FileBackedRealAdmissionAdministrationRefused("administration state is not valid JSON") from exc
    required = {
        "contract", "version", "operation_id", "state", "sequence", "recorded_at_ns", "detail",
    }
    if not isinstance(decoded, dict) or set(decoded) != required:
        raise FileBackedRealAdmissionAdministrationRefused("administration state shape is invalid")
    if decoded["contract"] != _STATE_CONTRACT or decoded["version"] != _VERSION:
        raise FileBackedRealAdmissionAdministrationRefused("administration state contract is unsupported")
    try:
        checkpoint = RealAdmissionAdministrationCheckpoint(
            operation_id=decoded["operation_id"],
            state=RealAdmissionAdministrationState(decoded["state"]),
            sequence=decoded["sequence"],
            recorded_at_ns=decoded["recorded_at_ns"],
            detail=decoded["detail"],
        )
    except (TypeError, ValueError) as exc:
        raise FileBackedRealAdmissionAdministrationRefused("administration state values are invalid") from exc
    if raw != _canonical_bytes(checkpoint.payload()):
        raise FileBackedRealAdmissionAdministrationRefused("administration state is noncanonical")
    return checkpoint


def _resolve_path(value: str | Path, label: str) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise FileBackedRealAdmissionAdministrationRefused(f"{label} must be an explicit non-empty path")
    return Path(value).expanduser().resolve(strict=False)


def _is_within(candidate: Path, root: Path) -> bool:
    return candidate == root or root in candidate.parents


def _require_operation_id(value: object) -> None:
    if not isinstance(value, str) or not _OPERATION_ID_RE.fullmatch(value):
        raise FileBackedRealAdmissionAdministrationRefused(
            "operation_id must use 1-128 ASCII letters, digits, dots, underscores, or hyphens"
        )


def _canonical_json_value(value: object | None, label: str) -> object | None:
    try:
        return json.loads(_canonical_json(value))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FileBackedRealAdmissionAdministrationRefused(f"{label} must be JSON-serializable") from exc


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"), sort_keys=True)


def _canonical_bytes(value: object) -> bytes:
    return (_canonical_json(value) + "\n").encode("utf-8")


__all__ = [
    "FileBackedRealAdmissionAdministrationRefused",
    "FileBackedRealAdmissionAdministrationRunner",
    "FileBackedRealAdmissionAdministrationWriteError",
    "RealAdmissionAdministrationCheckpoint",
    "RealAdmissionAdministrationState",
]
