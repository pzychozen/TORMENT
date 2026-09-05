"""Durable, file-backed administration records for future admission runs.

This module is deliberately outside the direct-source, writer-freeze, SQLite,
and admission authority paths.  A caller supplies all real work and this
module only atomically records its administration checkpoints in a directory
outside the caller-supplied data root.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
import json
import os
from pathlib import Path
import re
import time
from typing import Callable
from uuid import uuid4


_STATE_FILENAME = "administration_state.json"
_EVENTS_FILENAME = "administration_events.jsonl"
_STATE_CONTRACT = "TORMENT_FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_STATE"
_EVENT_CONTRACT = "TORMENT_FILE_BACKED_REAL_ADMISSION_ADMINISTRATION_EVENT"
_VERSION = 2
_OPERATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_REPOSITORY_HEAD_RE = re.compile(r"[0-9a-f]{40}\Z")


class FileBackedRealAdmissionAdministrationRefused(RuntimeError):
    """The supplied administrative context, path, or transition is unsafe."""


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


_PRE_P1_STATES = frozenset({
    RealAdmissionAdministrationState.RUNNER_STARTED,
    RealAdmissionAdministrationState.PRECHECK_STARTED,
    RealAdmissionAdministrationState.PRECHECK_PASS,
    RealAdmissionAdministrationState.PRECHECK_REFUSED,
    RealAdmissionAdministrationState.CAPTURE_STARTED,
    RealAdmissionAdministrationState.CAPTURE_RETURNED,
    RealAdmissionAdministrationState.CAPTURE_REFUSED,
    RealAdmissionAdministrationState.CAPTURE_EXCEPTION,
    RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
    RealAdmissionAdministrationState.DIRECT_PREPARATION_REFUSED,
})


@dataclass(frozen=True)
class RealAdmissionAdministrationRunContext:
    """Identity and P1-boundary facts embedded in every checkpoint."""

    operation_id: str
    expected_repository_head: str
    data_root_identity: str
    p1_authorized: bool
    p1_started: bool = False
    durable_native_state_created: bool = False

    def __post_init__(self) -> None:
        _require_operation_id(self.operation_id)
        if not isinstance(self.expected_repository_head, str) or not _REPOSITORY_HEAD_RE.fullmatch(
            self.expected_repository_head
        ):
            raise FileBackedRealAdmissionAdministrationRefused(
                "expected_repository_head must be a lowercase 40-character git object id"
            )
        _require_data_root_identity(self.data_root_identity)
        for name in ("p1_authorized", "p1_started", "durable_native_state_created"):
            if not isinstance(getattr(self, name), bool):
                raise FileBackedRealAdmissionAdministrationRefused(f"{name} must be boolean")
        if not self.p1_authorized and (self.p1_started or self.durable_native_state_created):
            raise FileBackedRealAdmissionAdministrationRefused(
                "P1 cannot be started or durable when P1 is not authorized"
            )
        if self.durable_native_state_created and not self.p1_started:
            raise FileBackedRealAdmissionAdministrationRefused(
                "durable native state requires P1_STARTED"
            )

    def payload(self) -> dict[str, object]:
        return {
            "operation_id": self.operation_id,
            "expected_repository_head": self.expected_repository_head,
            "data_root_identity": self.data_root_identity,
            "P1_authorized": self.p1_authorized,
            "P1_started": self.p1_started,
            "durable_native_state_created": self.durable_native_state_created,
        }

    def matches_requested_identity(self, requested: "RealAdmissionAdministrationRunContext") -> bool:
        return (
            self.operation_id == requested.operation_id
            and self.expected_repository_head == requested.expected_repository_head
            and self.data_root_identity == requested.data_root_identity
            and self.p1_authorized == requested.p1_authorized
        )


@dataclass(frozen=True)
class RealAdmissionAdministrationCheckpoint:
    """One complete canonical state held outside the caller's data root."""

    run_context: RealAdmissionAdministrationRunContext
    state: RealAdmissionAdministrationState
    sequence: int
    recorded_at_ns: int
    detail: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.run_context, RealAdmissionAdministrationRunContext):
            raise FileBackedRealAdmissionAdministrationRefused("administration run context must be typed")
        if not isinstance(self.state, RealAdmissionAdministrationState):
            raise FileBackedRealAdmissionAdministrationRefused("administration state must be typed")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool) or self.sequence < 1:
            raise FileBackedRealAdmissionAdministrationRefused("administration sequence must be a positive integer")
        if not isinstance(self.recorded_at_ns, int) or isinstance(self.recorded_at_ns, bool) or self.recorded_at_ns < 1:
            raise FileBackedRealAdmissionAdministrationRefused("administration timestamp must be a positive integer")
        _validate_context_for_state(self.run_context, self.state)
        _canonical_json_value(self.detail, "administration detail")

    @property
    def operation_id(self) -> str:
        return self.run_context.operation_id

    def payload(self) -> dict[str, object]:
        return {
            "contract": _STATE_CONTRACT,
            "version": _VERSION,
            "run_context": self.run_context.payload(),
            "state": self.state.value,
            "sequence": self.sequence,
            "recorded_at_ns": self.recorded_at_ns,
            "detail": _canonical_json_value(self.detail, "administration detail"),
        }


class FileBackedRealAdmissionAdministrationRunner:
    """Atomically retain caller-owned admission administration results.

    This runner does not open, enumerate, or modify ``data_root``.  It only
    resolves it to reject an administration destination contained within it.
    Callers own all precheck, capture, preparation, P1, and verification work.
    """

    def __init__(
        self,
        *,
        data_root: str | Path,
        result_directory: str | Path,
        operation_id: str,
        expected_repository_head: str,
        data_root_identity: str,
        p1_authorized: bool,
        append_events: bool = True,
    ) -> None:
        if not isinstance(append_events, bool):
            raise FileBackedRealAdmissionAdministrationRefused("append_events must be boolean")
        self._requested_context = RealAdmissionAdministrationRunContext(
            operation_id=operation_id,
            expected_repository_head=expected_repository_head,
            data_root_identity=data_root_identity,
            p1_authorized=p1_authorized,
        )
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
        """Atomically replace the canonical state, then append an optional event."""

        if not isinstance(state, RealAdmissionAdministrationState):
            raise FileBackedRealAdmissionAdministrationRefused("administration checkpoint state must be typed")
        prior_state = None if self._current is None else self._current.state
        if state not in _ALLOWED_NEXT[prior_state]:
            prior = "NONE" if prior_state is None else prior_state.value
            raise FileBackedRealAdmissionAdministrationRefused(
                f"administration transition is not allowed: {prior} -> {state.value}"
            )
        return self._persist(state, self._context_for_next_state(state), detail)

    def mark_durable_native_state_created(
        self,
        *,
        detail: object | None = None,
    ) -> RealAdmissionAdministrationCheckpoint:
        """Record the caller's durable-native-state fact while P1 is running.

        The caller creates any durable native artifact.  This method merely
        checkpoints that fact, using a second ``P1_STARTED`` record so the
        invocation boundary remains explicit and recoverable.
        """

        if self._current is None or self._current.state is not RealAdmissionAdministrationState.P1_STARTED:
            raise FileBackedRealAdmissionAdministrationRefused(
                "durable native state can only be recorded during P1_STARTED"
            )
        if self._current.run_context.durable_native_state_created:
            raise FileBackedRealAdmissionAdministrationRefused("durable native state was already recorded")
        return self._persist(
            RealAdmissionAdministrationState.P1_STARTED,
            replace(self._current.run_context, durable_native_state_created=True),
            detail,
        )

    def invoke_p1(
        self,
        callback: Callable[["FileBackedRealAdmissionAdministrationRunner"], object],
        *,
        detail: object | None = None,
    ) -> object:
        """Checkpoint ``P1_STARTED`` before a supplied, caller-owned P1 callback.

        This seam exists only to preserve ordering and durable-failure facts.
        It supplies no P1 logic, retry, cleanup, or real admission authority.
        """

        if not callable(callback):
            raise FileBackedRealAdmissionAdministrationRefused("P1 callback must be callable")
        self.checkpoint(RealAdmissionAdministrationState.P1_STARTED, detail=detail)
        try:
            return callback(self)
        except BaseException as exc:
            if self._current is not None and self._current.run_context.durable_native_state_created:
                self._persist(
                    RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE,
                    self._current.run_context,
                    _exception_detail(exc),
                )
            else:
                self.record_administration_exception(exc)
            raise

    def record_administration_exception(
        self,
        exception: BaseException,
        *,
        detail: object | None = None,
    ) -> RealAdmissionAdministrationCheckpoint:
        """Retain a bounded exception description without assigning authority."""

        if not isinstance(exception, BaseException):
            raise FileBackedRealAdmissionAdministrationRefused("exception record requires BaseException")
        value = _exception_detail(exception)
        if detail is not None:
            value["detail"] = _canonical_json_value(detail, "administration exception detail")
        return self.checkpoint(RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION, detail=value)

    def _context_for_next_state(
        self,
        state: RealAdmissionAdministrationState,
    ) -> RealAdmissionAdministrationRunContext:
        context = self._requested_context if self._current is None else self._current.run_context
        if state is RealAdmissionAdministrationState.P1_NOT_AUTHORIZED:
            if context.p1_authorized:
                raise FileBackedRealAdmissionAdministrationRefused(
                    "P1_NOT_AUTHORIZED conflicts with immutable P1 authorization"
                )
            return context
        if state is RealAdmissionAdministrationState.P1_READY:
            if not context.p1_authorized:
                raise FileBackedRealAdmissionAdministrationRefused(
                    "P1_READY requires immutable P1 authorization"
                )
            return context
        if state is RealAdmissionAdministrationState.P1_STARTED:
            if not context.p1_authorized:
                raise FileBackedRealAdmissionAdministrationRefused(
                    "P1_STARTED requires immutable P1 authorization"
                )
            return replace(context, p1_started=True)
        if state in {
            RealAdmissionAdministrationState.P1_PASS,
            RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE,
        } and not context.durable_native_state_created:
            raise FileBackedRealAdmissionAdministrationRefused(
                f"{state.value} requires a prior durable native state checkpoint"
            )
        return context

    def _persist(
        self,
        state: RealAdmissionAdministrationState,
        run_context: RealAdmissionAdministrationRunContext,
        detail: object | None,
    ) -> RealAdmissionAdministrationCheckpoint:
        checkpoint = RealAdmissionAdministrationCheckpoint(
            run_context=run_context,
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
        if not checkpoint.run_context.matches_requested_identity(self._requested_context):
            raise FileBackedRealAdmissionAdministrationRefused(
                "administration state run identity does not match requested operation, head, root, or P1 authorization"
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
        event = checkpoint.payload()
        event["contract"] = _EVENT_CONTRACT
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
    required = {"contract", "version", "run_context", "state", "sequence", "recorded_at_ns", "detail"}
    if not isinstance(decoded, dict) or set(decoded) != required:
        raise FileBackedRealAdmissionAdministrationRefused("administration state shape is invalid")
    if decoded["contract"] != _STATE_CONTRACT or decoded["version"] != _VERSION:
        raise FileBackedRealAdmissionAdministrationRefused("administration state contract is unsupported")
    try:
        checkpoint = RealAdmissionAdministrationCheckpoint(
            run_context=_run_context_from_payload(decoded["run_context"]),
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


def _run_context_from_payload(value: object) -> RealAdmissionAdministrationRunContext:
    required = {
        "operation_id",
        "expected_repository_head",
        "data_root_identity",
        "P1_authorized",
        "P1_started",
        "durable_native_state_created",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise FileBackedRealAdmissionAdministrationRefused("administration run context shape is invalid")
    return RealAdmissionAdministrationRunContext(
        operation_id=value["operation_id"],
        expected_repository_head=value["expected_repository_head"],
        data_root_identity=value["data_root_identity"],
        p1_authorized=value["P1_authorized"],
        p1_started=value["P1_started"],
        durable_native_state_created=value["durable_native_state_created"],
    )


def _validate_context_for_state(
    context: RealAdmissionAdministrationRunContext,
    state: RealAdmissionAdministrationState,
) -> None:
    if state in _PRE_P1_STATES and (context.p1_started or context.durable_native_state_created):
        raise FileBackedRealAdmissionAdministrationRefused(
            f"{state.value} cannot follow a P1 start in a canonical administration state"
        )
    if state is RealAdmissionAdministrationState.P1_NOT_AUTHORIZED:
        if context.p1_authorized or context.p1_started or context.durable_native_state_created:
            raise FileBackedRealAdmissionAdministrationRefused("P1_NOT_AUTHORIZED context is inconsistent")
    if state is RealAdmissionAdministrationState.P1_READY:
        if not context.p1_authorized or context.p1_started or context.durable_native_state_created:
            raise FileBackedRealAdmissionAdministrationRefused("P1_READY context is inconsistent")
    if state is RealAdmissionAdministrationState.P1_STARTED:
        if not context.p1_authorized or not context.p1_started:
            raise FileBackedRealAdmissionAdministrationRefused("P1_STARTED context is inconsistent")
    if state in {
        RealAdmissionAdministrationState.P1_PASS,
        RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE,
        RealAdmissionAdministrationState.FINAL_VERIFICATION_PASS,
    } and not context.durable_native_state_created:
        raise FileBackedRealAdmissionAdministrationRefused(
            f"{state.value} requires durable native state in the administration context"
        )


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


def _require_data_root_identity(value: object) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 512
        or any(ord(character) < 32 for character in value)
    ):
        raise FileBackedRealAdmissionAdministrationRefused(
            "data_root_identity must be a non-empty control-character-free string of at most 512 characters"
        )


def _exception_detail(exception: BaseException) -> dict[str, object]:
    return {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
    }


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
    "RealAdmissionAdministrationRunContext",
    "RealAdmissionAdministrationState",
]
