"""Narrow, durable Character target-geometry rebaseline orchestration.

The semantic state owner remains :class:`torment_service.character.CharacterStore`.
This module only binds one ratified, two-field transition to P6 evidence and
records redacted predecessor/successor digests so retry never becomes a second
Character mutation.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import threading
import time
from typing import Iterator
from uuid import UUID

from torment_service.character import CharacterSeed, CharacterState, CharacterStore

from .errors import DeploymentAuthorityError


_CONTRACT = "TORMENT_CHARACTER_TARGET_GEOMETRY_REBASELINE"
_VERSION = 1
_DISPOSITION = "RECOMPUTE_TARGET_GEOMETRY_BASELINE"
_DB_RELATIVE_PATH = Path("substrate") / "character_baseline_disposition" / "operations.sqlite"
_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


class CharacterBaselineRefused(DeploymentAuthorityError):
    """The exact Character predecessor, successor, or P6 binding is absent."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _require_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise CharacterBaselineRefused(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise CharacterBaselineRefused(f"{label} must be bounded non-empty text")
    return value


def _state_payload(state: CharacterState, *, include_updated_ts: bool) -> dict[str, object]:
    payload = dict(state.to_dict())
    if not include_updated_ts:
        payload.pop("updated_ts", None)
    return payload


def character_state_observation_digest(state: CharacterState) -> str:
    """Digest all persisted state fields, including the owner timestamp."""
    return _digest(_state_payload(state, include_updated_ts=True))


def character_state_semantic_digest(state: CharacterState) -> str:
    """Digest Character semantics; ``updated_ts`` is expressly non-semantic."""
    return _digest(_state_payload(state, include_updated_ts=False))


def character_seed_digest(seed: CharacterSeed) -> str:
    return _digest(seed.to_dict())


@dataclass(frozen=True)
class QualifiedTargetGeometry:
    """Only the native reader's bounded target-geometry result is accepted."""

    target_representation_identity: str
    ordered_native_memory_digest: str
    native_seed_geometry_digest: str
    expected_dimension: int
    distance_to_seed: float

    def __post_init__(self) -> None:
        _require_text(self.target_representation_identity, "target_representation_identity")
        _require_digest(self.ordered_native_memory_digest, "ordered_native_memory_digest")
        _require_digest(self.native_seed_geometry_digest, "native_seed_geometry_digest")
        if not isinstance(self.expected_dimension, int) or isinstance(self.expected_dimension, bool) or self.expected_dimension < 1:
            raise CharacterBaselineRefused("expected_dimension must be positive")
        if not isinstance(self.distance_to_seed, (int, float)) or isinstance(self.distance_to_seed, bool):
            raise CharacterBaselineRefused("distance_to_seed must be numeric")
        if not math.isfinite(float(self.distance_to_seed)):
            raise CharacterBaselineRefused("distance_to_seed must be finite")

    def payload(self) -> dict[str, object]:
        return {
            "target_representation_identity": self.target_representation_identity,
            "ordered_native_memory_digest": self.ordered_native_memory_digest,
            "native_seed_geometry_digest": self.native_seed_geometry_digest,
            "expected_dimension": self.expected_dimension,
            "distance_to_seed": float(self.distance_to_seed),
        }

    @property
    def digest(self) -> str:
        return _digest(self.payload())


@dataclass(frozen=True)
class CharacterBaselineBinding:
    corrected_core_id: UUID
    p6_receipt_id: str
    root_admission_envelope_digest: str
    plan_digest: str
    disposition: str = _DISPOSITION

    def __post_init__(self) -> None:
        if not isinstance(self.corrected_core_id, UUID):
            raise CharacterBaselineRefused("corrected_core_id must be UUID")
        _require_text(self.p6_receipt_id, "p6_receipt_id")
        _require_digest(self.root_admission_envelope_digest, "root_admission_envelope_digest")
        _require_digest(self.plan_digest, "plan_digest")
        if self.disposition != _DISPOSITION:
            raise CharacterBaselineRefused("Character baseline disposition is frozen")

    def payload(self) -> dict[str, str]:
        return {
            "corrected_core_id": str(self.corrected_core_id),
            "p6_receipt_id": self.p6_receipt_id,
            "root_admission_envelope_digest": self.root_admission_envelope_digest,
            "plan_digest": self.plan_digest,
            "disposition": self.disposition,
        }


@dataclass(frozen=True)
class CharacterBaselineRequest:
    workspace_id: str
    agent_id: str
    seed_id: str
    binding: CharacterBaselineBinding
    target_geometry: QualifiedTargetGeometry
    operation_key: str

    def __post_init__(self) -> None:
        for name in ("workspace_id", "agent_id", "seed_id", "operation_key"):
            _require_text(getattr(self, name), name)
        if not isinstance(self.binding, CharacterBaselineBinding):
            raise CharacterBaselineRefused("binding must be typed")
        if not isinstance(self.target_geometry, QualifiedTargetGeometry):
            raise CharacterBaselineRefused("target_geometry must be qualified")

    def payload(self) -> dict[str, object]:
        return {
            "workspace_id": self.workspace_id,
            "agent_id": self.agent_id,
            "seed_id": self.seed_id,
            "binding": self.binding.payload(),
            "target_geometry": self.target_geometry.payload(),
            "operation_key": self.operation_key,
        }


@dataclass(frozen=True)
class CharacterBaselineReceipt:
    request: CharacterBaselineRequest
    predecessor_observation_digest: str
    predecessor_semantic_digest: str
    successor_semantic_digest: str
    seed_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.request, CharacterBaselineRequest):
            raise CharacterBaselineRefused("receipt request must be typed")
        for name in (
            "predecessor_observation_digest", "predecessor_semantic_digest",
            "successor_semantic_digest", "seed_digest",
        ):
            _require_digest(getattr(self, name), name)

    def payload(self) -> dict[str, object]:
        return {
            "contract": _CONTRACT,
            "version": _VERSION,
            "kind": "CHARACTER_TARGET_GEOMETRY_REBASELINE_RECEIPT",
            "request": self.request.payload(),
            "predecessor_observation_digest": self.predecessor_observation_digest,
            "predecessor_semantic_digest": self.predecessor_semantic_digest,
            "successor_semantic_digest": self.successor_semantic_digest,
            "seed_digest": self.seed_digest,
            "target_geometry_input_digest": self.request.target_geometry.digest,
        }

    @property
    def digest(self) -> str:
        return _digest(self.payload())


class CharacterBaselineDispositionOwner:
    """P6-bound operation record around the retained ``CharacterStore`` owner."""

    def __init__(self, *, data_root: str | Path, store: CharacterStore) -> None:
        if not isinstance(store, CharacterStore):
            raise CharacterBaselineRefused("Character baseline requires CharacterStore")
        self._data_root = Path(data_root).expanduser().resolve()
        if not self._data_root.is_absolute():
            raise CharacterBaselineRefused("data_root must be absolute")
        if Path(store.data_dir).resolve() != self._data_root:
            raise CharacterBaselineRefused("CharacterStore must be rooted at the bound data root")
        self._store = store
        self._database = self._data_root / _DB_RELATIVE_PATH
        self._database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @property
    def database_path(self) -> Path:
        return self._database

    def execute(self, request: CharacterBaselineRequest) -> CharacterBaselineReceipt:
        if not isinstance(request, CharacterBaselineRequest):
            raise CharacterBaselineRefused("request must be typed")
        scope_key = _digest({"workspace_id": request.workspace_id, "agent_id": request.agent_id})
        with self._scope_lock(scope_key):
            existing = self._read_operation(request.operation_key)
            if existing is not None:
                return self._resume_or_replay(request, existing)
            state, seed = self._load_exact_predecessor(request)
            predecessor_observation = character_state_observation_digest(state)
            predecessor_semantic = character_state_semantic_digest(state)
            seed_observation = character_seed_digest(seed)
            successor = self._successor(state, request)
            successor_semantic = character_state_semantic_digest(successor)
            receipt = CharacterBaselineReceipt(
                request=request,
                predecessor_observation_digest=predecessor_observation,
                predecessor_semantic_digest=predecessor_semantic,
                successor_semantic_digest=successor_semantic,
                seed_digest=seed_observation,
            )
            self._record_prepared(receipt)
            # CharacterStore remains the only semantic persistence owner. The
            # narrow successor was constructed from the exact predecessor and
            # changes only the two ratified fields; save_state may update its
            # non-semantic timestamp.
            self._store.save_state(request.workspace_id, successor)
            persisted = self._store.load_state(request.workspace_id, request.agent_id)
            if persisted is None or character_state_semantic_digest(persisted) != successor_semantic:
                raise CharacterBaselineRefused("Character baseline successor was not persisted exactly")
            self._record_complete(receipt)
            return receipt

    def _load_exact_predecessor(self, request: CharacterBaselineRequest) -> tuple[CharacterState, CharacterSeed]:
        state = self._store.load_state(request.workspace_id, request.agent_id)
        seed = self._store.load_seed(request.workspace_id, request.seed_id)
        if state is None or seed is None:
            raise CharacterBaselineRefused("Character baseline predecessor state and seed are required")
        if state.workspace_id != request.workspace_id or state.agent_id != request.agent_id or state.seed_id != request.seed_id:
            raise CharacterBaselineRefused("Character baseline predecessor scope or seed disagrees")
        return state, seed

    @staticmethod
    def _successor(state: CharacterState, request: CharacterBaselineRequest) -> CharacterState:
        # ``replace`` avoids modifying the retained in-memory object before
        # the operation record makes the intended successor recoverable.
        return replace(
            state,
            distance_to_seed=float(request.target_geometry.distance_to_seed),
            drift_direction="stable",
        )

    def _resume_or_replay(self, request: CharacterBaselineRequest, row: sqlite3.Row) -> CharacterBaselineReceipt:
        receipt = self._receipt_from_json(row["receipt_json"])
        if receipt.request != request:
            raise CharacterBaselineRefused("Character baseline operation binding conflicts with durable record")
        state, seed = self._load_exact_predecessor(request)
        if character_seed_digest(seed) != receipt.seed_digest:
            raise CharacterBaselineRefused("Character baseline seed changed after operation preparation")
        semantic = character_state_semantic_digest(state)
        if row["stage"] == "COMPLETE":
            if semantic != receipt.successor_semantic_digest:
                raise CharacterBaselineRefused("Character baseline completion no longer matches successor")
            return receipt
        if row["stage"] != "PREPARED":
            raise CharacterBaselineRefused("Character baseline operation stage is invalid")
        if semantic == receipt.successor_semantic_digest:
            self._record_complete(receipt)
            return receipt
        if character_state_observation_digest(state) != receipt.predecessor_observation_digest:
            raise CharacterBaselineRefused("Character baseline partial operation has wrong predecessor")
        successor = self._successor(state, request)
        if character_state_semantic_digest(successor) != receipt.successor_semantic_digest:
            raise CharacterBaselineRefused("Character baseline prepared successor conflicts")
        self._store.save_state(request.workspace_id, successor)
        persisted = self._store.load_state(request.workspace_id, request.agent_id)
        if persisted is None or character_state_semantic_digest(persisted) != receipt.successor_semantic_digest:
            raise CharacterBaselineRefused("Character baseline retry did not persist exact successor")
        self._record_complete(receipt)
        return receipt

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database, timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS operations ("
                "operation_key TEXT PRIMARY KEY NOT NULL, request_json TEXT NOT NULL, receipt_json TEXT NOT NULL, "
                "stage TEXT NOT NULL CHECK(stage IN ('PREPARED','COMPLETE')), created_at_ns INTEGER NOT NULL, updated_at_ns INTEGER NOT NULL)"
            )

    def verify_completed_receipt_digest(self, digest: str) -> CharacterBaselineReceipt:
        """Verify a completed operation and its current exact successor state."""
        _require_digest(digest, "Character baseline receipt digest")
        matches: list[CharacterBaselineReceipt] = []
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT receipt_json FROM operations WHERE stage='COMPLETE'"
            ).fetchall()
        for row in rows:
            receipt = self._receipt_from_json(row["receipt_json"])
            if receipt.digest == digest:
                matches.append(receipt)
        if len(matches) != 1:
            raise CharacterBaselineRefused("Character baseline receipt is missing or ambiguous")
        receipt = matches[0]
        state, seed = self._load_exact_predecessor(receipt.request)
        if (
            character_seed_digest(seed) != receipt.seed_digest
            or character_state_semantic_digest(state) != receipt.successor_semantic_digest
        ):
            raise CharacterBaselineRefused("Character baseline receipt no longer proves exact successor")
        return receipt

    def _read_operation(self, operation_key: str) -> sqlite3.Row | None:
        with self._connection() as connection:
            return connection.execute("SELECT * FROM operations WHERE operation_key=?", (operation_key,)).fetchone()

    def _record_prepared(self, receipt: CharacterBaselineReceipt) -> None:
        now = time.time_ns()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "INSERT INTO operations VALUES (?, ?, ?, 'PREPARED', ?, ?)",
                    (receipt.request.operation_key, _canonical(receipt.request.payload()), _canonical(receipt.payload()), now, now),
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def _record_complete(self, receipt: CharacterBaselineReceipt) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                result = connection.execute(
                    "UPDATE operations SET stage='COMPLETE', updated_at_ns=? WHERE operation_key=? AND receipt_json=?",
                    (time.time_ns(), receipt.request.operation_key, _canonical(receipt.payload())),
                )
                if result.rowcount != 1:
                    raise CharacterBaselineRefused("Character baseline durable record conflicts")
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    @staticmethod
    def _receipt_from_json(raw: object) -> CharacterBaselineReceipt:
        if not isinstance(raw, str):
            raise CharacterBaselineRefused("Character baseline receipt record is malformed")
        try:
            value = json.loads(raw)
            request_value = value["request"]
            binding_value = request_value["binding"]
            target = request_value["target_geometry"]
            return CharacterBaselineReceipt(
                request=CharacterBaselineRequest(
                    workspace_id=request_value["workspace_id"], agent_id=request_value["agent_id"],
                    seed_id=request_value["seed_id"], operation_key=request_value["operation_key"],
                    binding=CharacterBaselineBinding(
                        corrected_core_id=UUID(binding_value["corrected_core_id"]),
                        p6_receipt_id=binding_value["p6_receipt_id"],
                        root_admission_envelope_digest=binding_value["root_admission_envelope_digest"],
                        plan_digest=binding_value["plan_digest"], disposition=binding_value["disposition"],
                    ),
                    target_geometry=QualifiedTargetGeometry(
                        target_representation_identity=target["target_representation_identity"],
                        ordered_native_memory_digest=target["ordered_native_memory_digest"],
                        native_seed_geometry_digest=target["native_seed_geometry_digest"],
                        expected_dimension=target["expected_dimension"], distance_to_seed=target["distance_to_seed"],
                    ),
                ),
                predecessor_observation_digest=value["predecessor_observation_digest"],
                predecessor_semantic_digest=value["predecessor_semantic_digest"],
                successor_semantic_digest=value["successor_semantic_digest"], seed_digest=value["seed_digest"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CharacterBaselineRefused("Character baseline receipt record is malformed") from exc

    @contextmanager
    def _scope_lock(self, scope_key: str) -> Iterator[None]:
        with _LOCKS_GUARD:
            local = _LOCKS.setdefault(scope_key, threading.RLock())
        with local:
            # This filename is only an OS-lock rendezvous name. The complete
            # SHA-256 scope identity remains in the operation record and local
            # map; truncation can only conservatively serialize a collision,
            # never grant two Character writes. It also stays below Windows'
            # path limit for deeply nested disposable roots.
            lock_path = self._database.parent / "scope_locks" / f"{scope_key[:24]}.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("a+b") as handle:
                handle.seek(0)
                if handle.read(1) == b"":
                    handle.seek(0)
                    handle.write(b"0")
                    handle.flush()
                self._acquire_os_lock(handle)
                try:
                    yield
                finally:
                    self._release_os_lock(handle)

    @staticmethod
    def _acquire_os_lock(handle: object) -> None:
        deadline = time.monotonic() + 10.0
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    handle.seek(0)  # type: ignore[union-attr]
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[union-attr]
                    return
                except OSError as exc:
                    if time.monotonic() >= deadline:
                        raise CharacterBaselineRefused("Character baseline scope lock acquisition timed out") from exc
                    time.sleep(0.01)
        else:  # pragma: no cover - CI portability only.
            import fcntl
            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore[union-attr]
                    return
                except BlockingIOError as exc:
                    if time.monotonic() >= deadline:
                        raise CharacterBaselineRefused("Character baseline scope lock acquisition timed out") from exc
                    time.sleep(0.01)

    @staticmethod
    def _release_os_lock(handle: object) -> None:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)  # type: ignore[union-attr]
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[union-attr]
        else:  # pragma: no cover - CI portability only.
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)  # type: ignore[union-attr]


__all__ = [
    "CharacterBaselineBinding", "CharacterBaselineDispositionOwner", "CharacterBaselineReceipt",
    "CharacterBaselineRefused", "CharacterBaselineRequest", "QualifiedTargetGeometry",
    "character_seed_digest", "character_state_observation_digest", "character_state_semantic_digest",
]
