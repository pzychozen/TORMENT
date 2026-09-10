"""Durable, scope-only trajectory writer authority coordination.

This module implements the production law ratified in the real-root
disposition contract v1.2.  It has no selector, memory, Character, motif,
proposal, or process-control operation.  Its sole durable concern is whether
one named trajectory writer session may make one artifact effect for one
materialized trajectory scope.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Iterator, Sequence, TYPE_CHECKING
from uuid import UUID, uuid4

from .errors import DeploymentAuthorityError

if TYPE_CHECKING:
    from .migration.root_scope import RootScopeKey


_CONTRACT = "TORMENT_TRAJECTORY_WRITER_HANDOFF"
_VERSION = 1
_DISPOSITION = "RETAIN"
_DB_RELATIVE_PATH = Path("substrate") / "trajectory_writer_handoff" / "authority.sqlite"
_LOCK_DIR_NAME = "scope_locks"
_DIGEST_HEX_LENGTH = 64
_PHASE_VALUES = tuple(
    value
    for value in (
        "LEGACY_AUTHORITATIVE",
        "QUIESCING",
        "LEGACY_QUIESCED",
        "NATIVE_ADMITTING",
        "NATIVE_AUTHORITATIVE",
        "HANDOFF_COMPLETE",
    )
)
_LOCAL_LOCKS: dict[str, threading.RLock] = {}
_LOCAL_LOCKS_GUARD = threading.Lock()
_PROCESS_SESSION_ID = f"pid:{os.getpid()}:{uuid4()}"


class TrajectoryHandoffRefused(DeploymentAuthorityError):
    """A caller lacks the exact durable authority required by the contract."""


class TrajectoryWriterFamily(StrEnum):
    LEGACY = "LEGACY"
    NATIVE = "NATIVE"


class TrajectoryHandoffPhase(StrEnum):
    LEGACY_AUTHORITATIVE = "LEGACY_AUTHORITATIVE"
    QUIESCING = "QUIESCING"
    LEGACY_QUIESCED = "LEGACY_QUIESCED"
    NATIVE_ADMITTING = "NATIVE_ADMITTING"
    NATIVE_AUTHORITATIVE = "NATIVE_AUTHORITATIVE"
    HANDOFF_COMPLETE = "HANDOFF_COMPLETE"


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise TrajectoryHandoffRefused(f"{label} must be bounded non-empty text")
    return value


def _require_digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != _DIGEST_HEX_LENGTH
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise TrajectoryHandoffRefused(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_uuid(value: object, label: str) -> UUID:
    if not isinstance(value, UUID):
        raise TrajectoryHandoffRefused(f"{label} must be a UUID")
    return value


@dataclass(frozen=True)
class TrajectoryScopeIdentity:
    """The exact v1.2 exclusivity identity for one trajectory artifact root."""

    data_root_identity: str
    scope_key: "RootScopeKey"
    legacy_source_namespace_id: UUID
    artifact_root: str

    def __post_init__(self) -> None:
        _require_text(self.data_root_identity, "data_root_identity")
        # Import lazily: importing the migration package while MemoryGraph is
        # itself importing would create a fabric/memory circular import. The
        # runtime check remains exact when a scope is actually constructed.
        from .migration.root_scope import RootScopeKey

        if not isinstance(self.scope_key, RootScopeKey):
            raise TrajectoryHandoffRefused("scope_key must be RootScopeKey")
        _require_uuid(self.legacy_source_namespace_id, "legacy_source_namespace_id")
        root = Path(self.artifact_root).expanduser().resolve()
        if not root.is_absolute():
            raise TrajectoryHandoffRefused("artifact_root must be absolute")
        object.__setattr__(self, "artifact_root", str(root))

    def payload(self) -> dict[str, object]:
        return {
            "data_root_identity": self.data_root_identity,
            "root_scope_key": self.scope_key.identity_payload(),
            "legacy_source_namespace_id": str(self.legacy_source_namespace_id),
            "artifact_root": self.artifact_root,
        }

    @property
    def exclusivity_key(self) -> str:
        return _digest(self.payload())


@dataclass(frozen=True)
class TrajectoryHandoffBinding:
    """Frozen P6/root facts that a trajectory authority record cannot alter."""

    corrected_core_id: UUID
    p6_receipt_id: str
    root_admission_envelope_digest: str
    plan_digest: str
    disposition: str = _DISPOSITION

    def __post_init__(self) -> None:
        _require_uuid(self.corrected_core_id, "corrected_core_id")
        _require_text(self.p6_receipt_id, "p6_receipt_id")
        _require_digest(self.root_admission_envelope_digest, "root_admission_envelope_digest")
        _require_digest(self.plan_digest, "plan_digest")
        if self.disposition != _DISPOSITION:
            raise TrajectoryHandoffRefused("trajectory handoff requires frozen RETAIN disposition")

    def payload(self) -> dict[str, str]:
        return {
            "corrected_core_id": str(self.corrected_core_id),
            "p6_receipt_id": self.p6_receipt_id,
            "root_admission_envelope_digest": self.root_admission_envelope_digest,
            "plan_digest": self.plan_digest,
            "disposition": self.disposition,
        }


@dataclass(frozen=True)
class TrajectoryWriterToken:
    """Opaque, fenced authority presented immediately before a write effect."""

    exclusivity_key: str
    family: TrajectoryWriterFamily
    writer_identity: str
    session_identity: str
    generation: int

    def __post_init__(self) -> None:
        _require_digest(self.exclusivity_key, "exclusivity_key")
        if not isinstance(self.family, TrajectoryWriterFamily):
            raise TrajectoryHandoffRefused("writer family must be typed")
        _require_text(self.writer_identity, "writer_identity")
        _require_text(self.session_identity, "session_identity")
        if not isinstance(self.generation, int) or isinstance(self.generation, bool) or self.generation < 1:
            raise TrajectoryHandoffRefused("writer generation must be positive")


@dataclass(frozen=True)
class TrajectoryHandoffReceipt:
    """Immutable per-scope evidence of a completed legacy-to-native transfer."""

    scope: TrajectoryScopeIdentity
    binding: TrajectoryHandoffBinding
    legacy_writer_identity: str
    legacy_quiescence_evidence_digest: str
    legacy_fence_generation: int
    native_writer_identity: str
    native_session_identity: str
    native_generation: int
    operation_key: str
    terminal_state: str = TrajectoryHandoffPhase.HANDOFF_COMPLETE.value

    def __post_init__(self) -> None:
        if not isinstance(self.scope, TrajectoryScopeIdentity):
            raise TrajectoryHandoffRefused("receipt scope must be typed")
        if not isinstance(self.binding, TrajectoryHandoffBinding):
            raise TrajectoryHandoffRefused("receipt binding must be typed")
        _require_text(self.legacy_writer_identity, "legacy_writer_identity")
        _require_digest(self.legacy_quiescence_evidence_digest, "legacy_quiescence_evidence_digest")
        _require_text(self.native_writer_identity, "native_writer_identity")
        _require_text(self.native_session_identity, "native_session_identity")
        _require_text(self.operation_key, "operation_key")
        if self.terminal_state != TrajectoryHandoffPhase.HANDOFF_COMPLETE.value:
            raise TrajectoryHandoffRefused("receipt must bind HANDOFF_COMPLETE")
        for name in ("legacy_fence_generation", "native_generation"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise TrajectoryHandoffRefused(f"{name} must be positive")

    def payload(self) -> dict[str, object]:
        return {
            "contract": _CONTRACT,
            "version": _VERSION,
            "kind": "TRAJECTORY_HANDOFF_RECEIPT",
            "scope": self.scope.payload(),
            "writer_exclusivity_key": self.scope.exclusivity_key,
            "binding": self.binding.payload(),
            "legacy_writer_identity": self.legacy_writer_identity,
            "legacy_quiescence_evidence_digest": self.legacy_quiescence_evidence_digest,
            "legacy_fence_generation": self.legacy_fence_generation,
            "native_writer_identity": self.native_writer_identity,
            "native_session_identity": self.native_session_identity,
            "native_generation": self.native_generation,
            "operation_key": self.operation_key,
            "terminal_state": self.terminal_state,
        }

    @property
    def digest(self) -> str:
        return _digest(self.payload())


@dataclass(frozen=True)
class AggregateTrajectoryReceipt:
    """Read-only aggregate proving every required trajectory scope is complete."""

    expected_scope_keys: tuple[str, ...]
    receipt_digests: tuple[str, ...]
    binding: TrajectoryHandoffBinding

    def __post_init__(self) -> None:
        if not self.expected_scope_keys or len(set(self.expected_scope_keys)) != len(self.expected_scope_keys):
            raise TrajectoryHandoffRefused("aggregate scope keys must be unique and non-empty")
        if len(self.expected_scope_keys) != len(self.receipt_digests):
            raise TrajectoryHandoffRefused("aggregate receipt count disagrees with expected scopes")
        for value in (*self.expected_scope_keys, *self.receipt_digests):
            _require_digest(value, "aggregate digest")
        if not isinstance(self.binding, TrajectoryHandoffBinding):
            raise TrajectoryHandoffRefused("aggregate binding must be typed")

    def payload(self) -> dict[str, object]:
        return {
            "contract": _CONTRACT,
            "version": _VERSION,
            "kind": "AGGREGATE_TRAJECTORY_HANDOFF_RECEIPT",
            "expected_scope_count": len(self.expected_scope_keys),
            "completed_scope_count": len(self.receipt_digests),
            "unaccounted_scope_count": 0,
            "overlapping_owner_scope_count": 0,
            "expected_scope_keys": list(self.expected_scope_keys),
            "receipt_digests": list(self.receipt_digests),
            "binding": self.binding.payload(),
        }

    @property
    def digest(self) -> str:
        return _digest(self.payload())


class TrajectoryWriteAuthority:
    """A scoped token client; it exposes no transition or selector operation."""

    def __init__(self, coordinator: "TrajectoryWriterHandoffCoordinator", token: TrajectoryWriterToken) -> None:
        self._coordinator = coordinator
        self._token = token

    @property
    def token(self) -> TrajectoryWriterToken:
        return self._token

    @contextmanager
    def effect(self, effect_kind: str) -> Iterator[None]:
        with self._coordinator.authorize_effect(self._token, effect_kind):
            yield

    def close(self) -> None:
        self._coordinator.release_writer_session(self._token)


class TrajectoryWriterHandoffCoordinator:
    """A durable, cross-process coordinator for v1.2 trajectory authority only."""

    def __init__(self, *, data_root: str | Path, create: bool = False) -> None:
        self.data_root = Path(data_root).expanduser().resolve()
        if not self.data_root.is_absolute():
            raise TrajectoryHandoffRefused("data_root must be absolute")
        self.database_path = self.data_root / _DB_RELATIVE_PATH
        self._lock_root = self.database_path.parent / _LOCK_DIR_NAME
        if create:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self._lock_root.mkdir(parents=True, exist_ok=True)
            self._initialize_database()
        elif not self.database_path.is_file():
            raise TrajectoryHandoffRefused("trajectory handoff authority database is absent")
        else:
            self._validate_database()

    @classmethod
    def create(cls, *, data_root: str | Path) -> "TrajectoryWriterHandoffCoordinator":
        return cls(data_root=data_root, create=True)

    @classmethod
    def open_existing(cls, *, data_root: str | Path) -> "TrajectoryWriterHandoffCoordinator":
        return cls(data_root=data_root, create=False)

    def initialize_legacy_scope(
        self,
        *,
        scope: TrajectoryScopeIdentity,
        binding: TrajectoryHandoffBinding,
        legacy_writer_identity: str,
        operation_key: str,
    ) -> TrajectoryHandoffPhase:
        """Create one exact legacy-authoritative record, idempotently."""

        self._validate_scope_under_root(scope)
        _require_text(legacy_writer_identity, "legacy_writer_identity")
        _require_text(operation_key, "operation_key")
        with self._scope_lock(scope.exclusivity_key), self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                existing = self._row(connection, scope.exclusivity_key)
                if existing is not None:
                    self._require_exact_scope_and_binding(existing, scope, binding)
                    if (
                        existing["legacy_writer_identity"] != legacy_writer_identity
                        or existing["operation_key"] != operation_key
                    ):
                        raise TrajectoryHandoffRefused("legacy scope initialization conflicts with durable intent")
                    connection.execute("COMMIT")
                    return TrajectoryHandoffPhase(existing["phase"])
                artifact_conflict = connection.execute(
                    "SELECT exclusivity_key FROM scope_authority WHERE artifact_root=?",
                    (scope.artifact_root,),
                ).fetchone()
                if artifact_conflict is not None:
                    raise TrajectoryHandoffRefused("another trajectory scope already owns this artifact root")
                now = time.time_ns()
                connection.execute(
                    """INSERT INTO scope_authority (
                        exclusivity_key,scope_json,artifact_root,binding_json,phase,generation,
                        legacy_writer_identity,legacy_session_identity,native_writer_identity,
                        native_session_identity,legacy_fence_generation,operation_key,
                        quiescence_evidence_digest,native_admission_evidence_digest,receipt_json,
                        created_at_ns,updated_at_ns
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, ?, NULL, NULL, NULL, ?, ?)""",
                    (
                        scope.exclusivity_key, _canonical(scope.payload()), scope.artifact_root,
                        _canonical(binding.payload()), TrajectoryHandoffPhase.LEGACY_AUTHORITATIVE.value,
                        1, legacy_writer_identity, operation_key, now, now,
                    ),
                )
                self._event(connection, scope.exclusivity_key, "INITIALIZED", operation_key, _digest(scope.payload()))
                connection.execute("COMMIT")
                return TrajectoryHandoffPhase.LEGACY_AUTHORITATIVE
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def begin_quiescing(self, *, scope: TrajectoryScopeIdentity, operation_key: str, evidence_digest: str) -> TrajectoryHandoffPhase:
        _require_text(operation_key, "operation_key")
        _require_digest(evidence_digest, "quiescing evidence digest")
        return self._transition(
            scope=scope,
            expected=TrajectoryHandoffPhase.LEGACY_AUTHORITATIVE,
            result=TrajectoryHandoffPhase.QUIESCING,
            operation_key=operation_key,
            evidence_digest=evidence_digest,
            event_kind="QUIESCING_STARTED",
        )

    def fence_legacy_after_quiescence(
        self, *, scope: TrajectoryScopeIdentity, operation_key: str, quiescence_evidence_digest: str,
    ) -> TrajectoryHandoffPhase:
        """Commit the only legacy fence after an exact, settled quiescence epoch."""

        _require_text(operation_key, "operation_key")
        _require_digest(quiescence_evidence_digest, "legacy quiescence evidence digest")
        with self._scope_lock(scope.exclusivity_key), self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._require_scope(connection, scope)
                phase = TrajectoryHandoffPhase(row["phase"])
                if phase is TrajectoryHandoffPhase.LEGACY_QUIESCED:
                    if row["operation_key"] == operation_key and row["quiescence_evidence_digest"] == quiescence_evidence_digest:
                        connection.execute("COMMIT")
                        return phase
                    raise TrajectoryHandoffRefused("legacy fence replay conflicts with durable evidence")
                if phase is not TrajectoryHandoffPhase.QUIESCING or row["operation_key"] != operation_key:
                    raise TrajectoryHandoffRefused("legacy fence requires the exact QUIESCING predecessor")
                active = row["legacy_session_identity"]
                if active is not None:
                    raise TrajectoryHandoffRefused("legacy writer session has not acknowledged quiescence")
                unsettled = connection.execute(
                    "SELECT 1 FROM write_intents WHERE exclusivity_key=? AND status='PREPARED' LIMIT 1",
                    (scope.exclusivity_key,),
                ).fetchone()
                if unsettled is not None:
                    raise TrajectoryHandoffRefused("trajectory write intent remains unsettled")
                generation = int(row["generation"]) + 1
                connection.execute(
                    """UPDATE scope_authority SET phase=?, generation=?, legacy_fence_generation=?,
                       quiescence_evidence_digest=?, updated_at_ns=? WHERE exclusivity_key=?""",
                    (
                        TrajectoryHandoffPhase.LEGACY_QUIESCED.value, generation, generation,
                        quiescence_evidence_digest, time.time_ns(), scope.exclusivity_key,
                    ),
                )
                self._event(connection, scope.exclusivity_key, "LEGACY_FENCED", operation_key, quiescence_evidence_digest)
                connection.execute("COMMIT")
                return TrajectoryHandoffPhase.LEGACY_QUIESCED
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def begin_native_admission(self, *, scope: TrajectoryScopeIdentity, operation_key: str, evidence_digest: str) -> TrajectoryHandoffPhase:
        _require_text(operation_key, "operation_key")
        _require_digest(evidence_digest, "native admission preparation evidence digest")
        return self._transition(
            scope=scope,
            expected=TrajectoryHandoffPhase.LEGACY_QUIESCED,
            result=TrajectoryHandoffPhase.NATIVE_ADMITTING,
            operation_key=operation_key,
            evidence_digest=evidence_digest,
            event_kind="NATIVE_ADMISSION_STARTED",
        )

    def admit_native_writer(
        self,
        *,
        scope: TrajectoryScopeIdentity,
        operation_key: str,
        native_writer_identity: str,
        native_admission_evidence_digest: str,
        session_identity: str | None = None,
    ) -> TrajectoryWriterToken:
        """Admit one exact native writer after the durable legacy fence."""

        _require_text(operation_key, "operation_key")
        _require_text(native_writer_identity, "native_writer_identity")
        _require_digest(native_admission_evidence_digest, "native admission evidence digest")
        session = _PROCESS_SESSION_ID if session_identity is None else _require_text(session_identity, "session_identity")
        with self._scope_lock(scope.exclusivity_key), self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._require_scope(connection, scope)
                phase = TrajectoryHandoffPhase(row["phase"])
                if phase in {TrajectoryHandoffPhase.NATIVE_AUTHORITATIVE, TrajectoryHandoffPhase.HANDOFF_COMPLETE}:
                    if (
                        row["operation_key"] == operation_key
                        and row["native_writer_identity"] == native_writer_identity
                        and row["native_admission_evidence_digest"] == native_admission_evidence_digest
                    ):
                        token = self._replace_or_reuse_native_session(connection, row, session, operation_key)
                        connection.execute("COMMIT")
                        return token
                    raise TrajectoryHandoffRefused("native admission conflicts with durable writer identity")
                if phase is not TrajectoryHandoffPhase.NATIVE_ADMITTING or row["operation_key"] != operation_key:
                    raise TrajectoryHandoffRefused("native admission requires the exact NATIVE_ADMITTING predecessor")
                generation = int(row["generation"]) + 1
                connection.execute(
                    """UPDATE scope_authority SET phase=?, generation=?, native_writer_identity=?,
                       native_session_identity=?, native_admission_evidence_digest=?, updated_at_ns=?
                       WHERE exclusivity_key=?""",
                    (
                        TrajectoryHandoffPhase.NATIVE_AUTHORITATIVE.value, generation,
                        native_writer_identity, session, native_admission_evidence_digest,
                        time.time_ns(), scope.exclusivity_key,
                    ),
                )
                self._event(connection, scope.exclusivity_key, "NATIVE_ADMITTED", operation_key, native_admission_evidence_digest)
                connection.execute("COMMIT")
                return TrajectoryWriterToken(
                    scope.exclusivity_key, TrajectoryWriterFamily.NATIVE,
                    native_writer_identity, session, generation,
                )
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def complete_handoff(self, *, scope: TrajectoryScopeIdentity, operation_key: str) -> TrajectoryHandoffReceipt:
        """Append one terminal per-scope receipt only from native authority."""

        _require_text(operation_key, "operation_key")
        with self._scope_lock(scope.exclusivity_key), self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._require_scope(connection, scope)
                phase = TrajectoryHandoffPhase(row["phase"])
                if phase is TrajectoryHandoffPhase.HANDOFF_COMPLETE:
                    receipt = self._receipt_from_row(row)
                    if receipt.operation_key != operation_key:
                        raise TrajectoryHandoffRefused("terminal handoff replay conflicts with operation key")
                    connection.execute("COMMIT")
                    return receipt
                if phase is not TrajectoryHandoffPhase.NATIVE_AUTHORITATIVE:
                    raise TrajectoryHandoffRefused("handoff receipt requires NATIVE_AUTHORITATIVE state")
                if row["native_writer_identity"] is None or row["native_session_identity"] is None:
                    raise TrajectoryHandoffRefused("native admission is incomplete")
                binding = self._binding_from_row(row)
                receipt = TrajectoryHandoffReceipt(
                    scope=scope,
                    binding=binding,
                    legacy_writer_identity=str(row["legacy_writer_identity"]),
                    legacy_quiescence_evidence_digest=str(row["quiescence_evidence_digest"]),
                    legacy_fence_generation=int(row["legacy_fence_generation"]),
                    native_writer_identity=str(row["native_writer_identity"]),
                    native_session_identity=str(row["native_session_identity"]),
                    native_generation=int(row["generation"]),
                    operation_key=operation_key,
                )
                connection.execute(
                    "UPDATE scope_authority SET phase=?, receipt_json=?, updated_at_ns=? WHERE exclusivity_key=?",
                    (
                        TrajectoryHandoffPhase.HANDOFF_COMPLETE.value, _canonical(receipt.payload()),
                        time.time_ns(), scope.exclusivity_key,
                    ),
                )
                self._event(connection, scope.exclusivity_key, "HANDOFF_COMPLETED", operation_key, receipt.digest)
                connection.execute("COMMIT")
                return receipt
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def aggregate_receipt(
        self, *, expected_scopes: Sequence[TrajectoryScopeIdentity], binding: TrajectoryHandoffBinding,
    ) -> AggregateTrajectoryReceipt:
        """Verify exact scope closure; it performs no trajectory artifact write."""

        if not isinstance(expected_scopes, Sequence) or isinstance(expected_scopes, (str, bytes)):
            raise TrajectoryHandoffRefused("expected scopes must be a sequence")
        scopes = tuple(sorted(expected_scopes, key=lambda item: item.exclusivity_key))
        if not scopes or any(not isinstance(item, TrajectoryScopeIdentity) for item in scopes):
            raise TrajectoryHandoffRefused("expected scopes must be typed and non-empty")
        if len({item.exclusivity_key for item in scopes}) != len(scopes):
            raise TrajectoryHandoffRefused("aggregate scope census has duplicate exclusivity keys")
        if len({item.artifact_root for item in scopes}) != len(scopes):
            raise TrajectoryHandoffRefused("aggregate scope census overlaps artifact roots")
        receipts: list[TrajectoryHandoffReceipt] = []
        with self._connection() as connection:
            for scope in scopes:
                row = self._require_scope(connection, scope)
                self._require_exact_scope_and_binding(row, scope, binding)
                if TrajectoryHandoffPhase(row["phase"]) is not TrajectoryHandoffPhase.HANDOFF_COMPLETE:
                    raise TrajectoryHandoffRefused("aggregate receipt requires every scope handoff completion")
                receipt = self._receipt_from_row(row)
                if receipt.binding != binding:
                    raise TrajectoryHandoffRefused("scope receipt P6/core binding disagrees with aggregate")
                if row["native_session_identity"] is None:
                    raise TrajectoryHandoffRefused("completed handoff lacks a current native writer session")
                receipts.append(receipt)
        aggregate = AggregateTrajectoryReceipt(
            expected_scope_keys=tuple(item.exclusivity_key for item in scopes),
            receipt_digests=tuple(item.digest for item in receipts),
            binding=binding,
        )
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                existing = connection.execute(
                    "SELECT receipt_json FROM aggregate_receipts WHERE aggregate_key=?", (aggregate.digest,),
                ).fetchone()
                if existing is None:
                    connection.execute(
                        "INSERT INTO aggregate_receipts VALUES (?, ?, ?)",
                        (aggregate.digest, _canonical(aggregate.payload()), time.time_ns()),
                    )
                elif existing[0] != _canonical(aggregate.payload()):
                    raise TrajectoryHandoffRefused("aggregate receipt digest collision")
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return aggregate

    def verify_aggregate_receipt_digest(self, digest: str) -> AggregateTrajectoryReceipt:
        """Read-only P7-time verification of one durable aggregate receipt.

        The verifier deliberately does not recreate, settle, or rotate any
        writer session. It proves the recorded exact census remains terminal
        and has one current native session for every scope.
        """
        _require_digest(digest, "aggregate trajectory receipt digest")
        with self._connection() as connection:
            stored = connection.execute(
                "SELECT receipt_json FROM aggregate_receipts WHERE aggregate_key=?", (digest,),
            ).fetchone()
            if stored is None:
                raise TrajectoryHandoffRefused("aggregate trajectory receipt is absent")
            try:
                payload = json.loads(str(stored["receipt_json"]))
                binding_value = payload["binding"]
                binding = TrajectoryHandoffBinding(
                    corrected_core_id=UUID(binding_value["corrected_core_id"]),
                    p6_receipt_id=binding_value["p6_receipt_id"],
                    root_admission_envelope_digest=binding_value["root_admission_envelope_digest"],
                    plan_digest=binding_value["plan_digest"], disposition=binding_value["disposition"],
                )
                keys = tuple(payload["expected_scope_keys"])
                receipt_digests = tuple(payload["receipt_digests"])
                aggregate = AggregateTrajectoryReceipt(keys, receipt_digests, binding)
            except (KeyError, TypeError, ValueError) as exc:
                raise TrajectoryHandoffRefused("aggregate trajectory receipt is malformed") from exc
            if aggregate.digest != digest or _canonical(aggregate.payload()) != _canonical(payload):
                raise TrajectoryHandoffRefused("aggregate trajectory receipt digest conflicts with payload")
            rows = [self._row(connection, key) for key in aggregate.expected_scope_keys]
            if any(row is None for row in rows):
                raise TrajectoryHandoffRefused("aggregate trajectory receipt has an unaccounted scope")
            typed_rows = [row for row in rows if row is not None]
            if any(self._binding_from_row(row) != binding for row in typed_rows):
                raise TrajectoryHandoffRefused("aggregate trajectory binding no longer matches scope")
            if any(TrajectoryHandoffPhase(row["phase"]) is not TrajectoryHandoffPhase.HANDOFF_COMPLETE for row in typed_rows):
                raise TrajectoryHandoffRefused("aggregate trajectory scope is partial")
            if any(row["native_session_identity"] is None for row in typed_rows):
                raise TrajectoryHandoffRefused("aggregate trajectory scope has no current native session")
            if tuple(self._receipt_from_row(row).digest for row in typed_rows) != aggregate.receipt_digests:
                raise TrajectoryHandoffRefused("aggregate trajectory receipt list no longer matches scopes")
            all_bound_rows = connection.execute("SELECT * FROM scope_authority").fetchall()
            bound_keys = {
                str(row["exclusivity_key"])
                for row in all_bound_rows
                if self._binding_from_row(row) == binding
            }
            if bound_keys != set(aggregate.expected_scope_keys):
                raise TrajectoryHandoffRefused("aggregate trajectory census has unaccounted or overlapping scopes")
        return aggregate

    def record_for_scope(self, *, scope: TrajectoryScopeIdentity) -> dict[str, object]:
        """Return a typed-only diagnostic projection; it grants no authority."""

        with self._connection() as connection:
            row = self._require_scope(connection, scope)
            return {
                "phase": row["phase"],
                "generation": int(row["generation"]),
                "legacy_fence_generation": row["legacy_fence_generation"],
                "native_writer_identity": row["native_writer_identity"],
                "native_session_identity": row["native_session_identity"],
                "receipt_digest": None if row["receipt_json"] is None else self._receipt_from_row(row).digest,
            }

    def legacy_writer(self, *, scope: TrajectoryScopeIdentity, writer_identity: str) -> TrajectoryWriteAuthority:
        return self._claim_writer(scope=scope, family=TrajectoryWriterFamily.LEGACY, writer_identity=writer_identity)

    def native_writer(self, *, scope: TrajectoryScopeIdentity, writer_identity: str | None = None) -> TrajectoryWriteAuthority:
        return self._claim_writer(scope=scope, family=TrajectoryWriterFamily.NATIVE, writer_identity=writer_identity)

    def authority_for_artifact_root(
        self, *, artifact_root: str | Path, family: TrajectoryWriterFamily, writer_identity: str,
    ) -> TrajectoryWriteAuthority:
        root = str(Path(artifact_root).expanduser().resolve())
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM scope_authority WHERE artifact_root=?", (root,)).fetchone()
            if row is None:
                raise TrajectoryHandoffRefused("coordinator has no scope record for trajectory artifact root")
            scope = self._scope_from_row(row)
        if family is TrajectoryWriterFamily.LEGACY:
            return self.legacy_writer(scope=scope, writer_identity=writer_identity)
        return self.native_writer(scope=scope, writer_identity=writer_identity)

    def release_writer_session(self, token: TrajectoryWriterToken) -> None:
        """Legacy close acknowledgement; native release never restores legacy authority."""

        with self._scope_lock(token.exclusivity_key), self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._row(connection, token.exclusivity_key)
                if row is None:
                    raise TrajectoryHandoffRefused("writer token names an unknown scope")
                if token.family is TrajectoryWriterFamily.LEGACY:
                    if row["legacy_session_identity"] != token.session_identity:
                        raise TrajectoryHandoffRefused("legacy session release is stale")
                    if TrajectoryHandoffPhase(row["phase"]) not in {
                        TrajectoryHandoffPhase.LEGACY_AUTHORITATIVE, TrajectoryHandoffPhase.QUIESCING,
                    }:
                        raise TrajectoryHandoffRefused("legacy session may not release after its authority was fenced")
                    connection.execute(
                        "UPDATE scope_authority SET legacy_session_identity=NULL, updated_at_ns=? WHERE exclusivity_key=?",
                        (time.time_ns(), token.exclusivity_key),
                    )
                else:
                    if row["native_session_identity"] != token.session_identity:
                        raise TrajectoryHandoffRefused("native session release is stale")
                    connection.execute(
                        "UPDATE scope_authority SET native_session_identity=NULL, updated_at_ns=? WHERE exclusivity_key=?",
                        (time.time_ns(), token.exclusivity_key),
                    )
                self._event(connection, token.exclusivity_key, "WRITER_SESSION_RELEASED", "session-release", _digest(token.session_identity))
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    @contextmanager
    def authorize_effect(self, token: TrajectoryWriterToken, effect_kind: str) -> Iterator[None]:
        """Fence one filesystem effect with durable intent and the shared scope lock."""

        _require_text(effect_kind, "effect_kind")
        intent_id = str(uuid4())
        with self._scope_lock(token.exclusivity_key), self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._row(connection, token.exclusivity_key)
                if row is None:
                    raise TrajectoryHandoffRefused("writer token names an unknown scope")
                self._validate_current_token(row, token)
                if (
                    token.family is TrajectoryWriterFamily.LEGACY
                    and TrajectoryHandoffPhase(row["phase"]) is TrajectoryHandoffPhase.QUIESCING
                    and effect_kind not in {"trajectory_v2_close", "trajectory_legacy_close"}
                ):
                    raise TrajectoryHandoffRefused("legacy quiescing permits only guarded trajectory close")
                connection.execute(
                    "INSERT INTO write_intents VALUES (?, ?, ?, ?, ?, ?, ?, 'PREPARED', ?, ?)",
                    (
                        intent_id, token.exclusivity_key, token.family.value, token.writer_identity,
                        token.session_identity, token.generation, effect_kind, time.time_ns(), None,
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
            try:
                yield
            except Exception:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        "UPDATE write_intents SET status='ABORTED', settled_at_ns=? WHERE intent_id=?",
                        (time.time_ns(), intent_id),
                    )
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                raise
            else:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        "UPDATE write_intents SET status='SETTLED', settled_at_ns=? WHERE intent_id=?",
                        (time.time_ns(), intent_id),
                    )
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise

    def _claim_writer(
        self, *, scope: TrajectoryScopeIdentity, family: TrajectoryWriterFamily, writer_identity: str | None,
    ) -> TrajectoryWriteAuthority:
        if writer_identity is not None:
            _require_text(writer_identity, "writer_identity")
        with self._scope_lock(scope.exclusivity_key), self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._require_scope(connection, scope)
                phase = TrajectoryHandoffPhase(row["phase"])
                if family is TrajectoryWriterFamily.LEGACY:
                    if phase is not TrajectoryHandoffPhase.LEGACY_AUTHORITATIVE:
                        raise TrajectoryHandoffRefused("legacy writer authority is fenced or quiescing")
                    expected = str(row["legacy_writer_identity"])
                    if writer_identity is not None and writer_identity != expected:
                        raise TrajectoryHandoffRefused("legacy writer identity disagrees with the registered slot")
                    current_session = row["legacy_session_identity"]
                    if current_session is not None and current_session != _PROCESS_SESSION_ID:
                        raise TrajectoryHandoffRefused("another legacy writer session is authoritative")
                    if current_session is None:
                        connection.execute(
                            "UPDATE scope_authority SET legacy_session_identity=?, updated_at_ns=? WHERE exclusivity_key=?",
                            (_PROCESS_SESSION_ID, time.time_ns(), scope.exclusivity_key),
                        )
                        self._event(connection, scope.exclusivity_key, "LEGACY_SESSION_CLAIMED", "legacy-session", _digest(_PROCESS_SESSION_ID))
                    token = TrajectoryWriterToken(
                        scope.exclusivity_key, family, expected, _PROCESS_SESSION_ID, int(row["generation"]),
                    )
                else:
                    if phase not in {
                        TrajectoryHandoffPhase.NATIVE_AUTHORITATIVE,
                        TrajectoryHandoffPhase.HANDOFF_COMPLETE,
                    }:
                        raise TrajectoryHandoffRefused("native writer authority has not been admitted")
                    expected = str(row["native_writer_identity"] or "")
                    if not expected:
                        raise TrajectoryHandoffRefused("native writer slot is absent")
                    if writer_identity is not None and writer_identity != expected:
                        raise TrajectoryHandoffRefused("native writer identity disagrees with admitted slot")
                    token = self._replace_or_reuse_native_session(connection, row, _PROCESS_SESSION_ID, "native-session")
                connection.execute("COMMIT")
                return TrajectoryWriteAuthority(self, token)
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def _replace_or_reuse_native_session(
        self, connection: sqlite3.Connection, row: sqlite3.Row, session: str, operation_key: str,
    ) -> TrajectoryWriterToken:
        current = row["native_session_identity"]
        generation = int(row["generation"])
        if current != session:
            generation += 1
            connection.execute(
                "UPDATE scope_authority SET native_session_identity=?, generation=?, updated_at_ns=? WHERE exclusivity_key=?",
                (session, generation, time.time_ns(), row["exclusivity_key"]),
            )
            self._event(connection, row["exclusivity_key"], "NATIVE_SESSION_FENCED_REPLACEMENT", operation_key, _digest(session))
        return TrajectoryWriterToken(
            str(row["exclusivity_key"]), TrajectoryWriterFamily.NATIVE,
            str(row["native_writer_identity"]), session, generation,
        )

    def _transition(
        self,
        *, scope: TrajectoryScopeIdentity, expected: TrajectoryHandoffPhase,
        result: TrajectoryHandoffPhase, operation_key: str, evidence_digest: str, event_kind: str,
    ) -> TrajectoryHandoffPhase:
        with self._scope_lock(scope.exclusivity_key), self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._require_scope(connection, scope)
                phase = TrajectoryHandoffPhase(row["phase"])
                if phase is result:
                    if row["operation_key"] == operation_key:
                        connection.execute("COMMIT")
                        return phase
                    raise TrajectoryHandoffRefused("handoff transition replay conflicts with operation key")
                if phase is not expected or row["operation_key"] != operation_key:
                    raise TrajectoryHandoffRefused(f"handoff transition requires {expected.value} predecessor")
                connection.execute(
                    "UPDATE scope_authority SET phase=?, updated_at_ns=? WHERE exclusivity_key=?",
                    (result.value, time.time_ns(), scope.exclusivity_key),
                )
                self._event(connection, scope.exclusivity_key, event_kind, operation_key, evidence_digest)
                connection.execute("COMMIT")
                return result
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def _validate_current_token(self, row: sqlite3.Row, token: TrajectoryWriterToken) -> None:
        phase = TrajectoryHandoffPhase(row["phase"])
        if token.family is TrajectoryWriterFamily.LEGACY:
            valid = (
                phase in {
                    TrajectoryHandoffPhase.LEGACY_AUTHORITATIVE,
                    TrajectoryHandoffPhase.QUIESCING,
                }
                and row["legacy_writer_identity"] == token.writer_identity
                and row["legacy_session_identity"] == token.session_identity
                and int(row["generation"]) == token.generation
            )
        else:
            valid = (
                phase in {TrajectoryHandoffPhase.NATIVE_AUTHORITATIVE, TrajectoryHandoffPhase.HANDOFF_COMPLETE}
                and row["native_writer_identity"] == token.writer_identity
                and row["native_session_identity"] == token.session_identity
                and int(row["generation"]) == token.generation
            )
        if not valid:
            raise TrajectoryHandoffRefused("trajectory write attempted with stale or non-authoritative token")

    def _require_scope(self, connection: sqlite3.Connection, scope: TrajectoryScopeIdentity) -> sqlite3.Row:
        self._validate_scope_under_root(scope)
        row = self._row(connection, scope.exclusivity_key)
        if row is None:
            raise TrajectoryHandoffRefused("trajectory scope is not registered")
        actual_scope = self._scope_from_row(row)
        if actual_scope != scope:
            raise TrajectoryHandoffRefused("trajectory exclusivity key payload conflicts with registered scope")
        return row

    def _require_exact_scope_and_binding(
        self, row: sqlite3.Row, scope: TrajectoryScopeIdentity, binding: TrajectoryHandoffBinding,
    ) -> None:
        if self._scope_from_row(row) != scope or self._binding_from_row(row) != binding:
            raise TrajectoryHandoffRefused("durable handoff record binding conflicts with request")

    def _scope_from_row(self, row: sqlite3.Row) -> TrajectoryScopeIdentity:
        value = json.loads(str(row["scope_json"]))
        key_value = value["root_scope_key"]
        try:
            from .migration.root_scope import RootScopeKey, RootScopeKind

            scope_key = RootScopeKey(
                workspace_id=key_value["workspace_id"],
                scope_kind=RootScopeKind(key_value["scope_kind"]),
                agent_id=key_value["agent_id"], domain_id=key_value["domain_id"],
            )
            return TrajectoryScopeIdentity(
                data_root_identity=value["data_root_identity"], scope_key=scope_key,
                legacy_source_namespace_id=UUID(value["legacy_source_namespace_id"]),
                artifact_root=value["artifact_root"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TrajectoryHandoffRefused("durable trajectory scope record is malformed") from exc

    def _binding_from_row(self, row: sqlite3.Row) -> TrajectoryHandoffBinding:
        value = json.loads(str(row["binding_json"]))
        try:
            return TrajectoryHandoffBinding(
                corrected_core_id=UUID(value["corrected_core_id"]), p6_receipt_id=value["p6_receipt_id"],
                root_admission_envelope_digest=value["root_admission_envelope_digest"],
                plan_digest=value["plan_digest"], disposition=value["disposition"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TrajectoryHandoffRefused("durable trajectory binding record is malformed") from exc

    def _receipt_from_row(self, row: sqlite3.Row) -> TrajectoryHandoffReceipt:
        raw = row["receipt_json"]
        if raw is None:
            raise TrajectoryHandoffRefused("completed handoff lacks a durable receipt")
        value = json.loads(str(raw))
        try:
            scope = self._scope_from_row(row)
            binding = self._binding_from_row(row)
            return TrajectoryHandoffReceipt(
                scope=scope, binding=binding, legacy_writer_identity=value["legacy_writer_identity"],
                legacy_quiescence_evidence_digest=value["legacy_quiescence_evidence_digest"],
                legacy_fence_generation=value["legacy_fence_generation"],
                native_writer_identity=value["native_writer_identity"],
                native_session_identity=value["native_session_identity"],
                native_generation=value["native_generation"], operation_key=value["operation_key"],
                terminal_state=value["terminal_state"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TrajectoryHandoffRefused("durable trajectory handoff receipt is malformed") from exc

    def _row(self, connection: sqlite3.Connection, key: str) -> sqlite3.Row | None:
        return connection.execute("SELECT * FROM scope_authority WHERE exclusivity_key=?", (key,)).fetchone()

    def _event(self, connection: sqlite3.Connection, key: str, kind: str, operation_key: str, evidence_digest: str) -> None:
        connection.execute(
            "INSERT INTO handoff_events (exclusivity_key,event_kind,operation_key,evidence_digest,recorded_at_ns) VALUES (?, ?, ?, ?, ?)",
            (key, kind, operation_key, evidence_digest, time.time_ns()),
        )

    def _validate_scope_under_root(self, scope: TrajectoryScopeIdentity) -> None:
        root = self.data_root
        artifact = Path(scope.artifact_root).resolve()
        if artifact == root or root not in artifact.parents:
            raise TrajectoryHandoffRefused("trajectory artifact root escapes coordinator data root")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        uri = f"{self.database_path.resolve().as_uri()}?mode=rw"
        try:
            connection = sqlite3.connect(uri, uri=True, isolation_level=None, timeout=10, check_same_thread=False)
        except sqlite3.Error as exc:
            raise TrajectoryHandoffRefused("trajectory authority database cannot be opened") from exc
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 10000")
            yield connection
        finally:
            connection.close()

    def _initialize_database(self) -> None:
        connection = sqlite3.connect(str(self.database_path), isolation_level=None, check_same_thread=False)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA synchronous = FULL")
            if connection.execute("PRAGMA synchronous").fetchone()[0] < 2:
                raise TrajectoryHandoffRefused("trajectory authority SQLite synchronous mode is inadequate")
            if str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).lower() != "wal":
                raise TrajectoryHandoffRefused("trajectory authority SQLite WAL mode is unavailable")
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS authority_metadata (
                        singleton INTEGER PRIMARY KEY CHECK (singleton=1),
                        contract TEXT NOT NULL, version INTEGER NOT NULL, data_root TEXT NOT NULL
                    ) STRICT"""
                )
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS scope_authority (
                        exclusivity_key TEXT PRIMARY KEY, scope_json TEXT NOT NULL, artifact_root TEXT NOT NULL UNIQUE,
                        binding_json TEXT NOT NULL, phase TEXT NOT NULL, generation INTEGER NOT NULL,
                        legacy_writer_identity TEXT NOT NULL, legacy_session_identity TEXT,
                        native_writer_identity TEXT, native_session_identity TEXT,
                        legacy_fence_generation INTEGER, operation_key TEXT NOT NULL,
                        quiescence_evidence_digest TEXT, native_admission_evidence_digest TEXT,
                        receipt_json TEXT, created_at_ns INTEGER NOT NULL, updated_at_ns INTEGER NOT NULL
                    ) STRICT"""
                )
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS handoff_events (
                        ordinal INTEGER PRIMARY KEY, exclusivity_key TEXT NOT NULL, event_kind TEXT NOT NULL,
                        operation_key TEXT NOT NULL, evidence_digest TEXT NOT NULL, recorded_at_ns INTEGER NOT NULL,
                        FOREIGN KEY (exclusivity_key) REFERENCES scope_authority(exclusivity_key)
                    ) STRICT"""
                )
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS write_intents (
                        intent_id TEXT PRIMARY KEY, exclusivity_key TEXT NOT NULL, writer_family TEXT NOT NULL,
                        writer_identity TEXT NOT NULL, session_identity TEXT NOT NULL, generation INTEGER NOT NULL,
                        effect_kind TEXT NOT NULL, status TEXT NOT NULL, prepared_at_ns INTEGER NOT NULL,
                        settled_at_ns INTEGER, FOREIGN KEY (exclusivity_key) REFERENCES scope_authority(exclusivity_key)
                    ) STRICT"""
                )
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS aggregate_receipts (
                        aggregate_key TEXT PRIMARY KEY, receipt_json TEXT NOT NULL, recorded_at_ns INTEGER NOT NULL
                    ) STRICT"""
                )
                existing = connection.execute("SELECT contract,version,data_root FROM authority_metadata WHERE singleton=1").fetchone()
                canonical_root = str(self.data_root)
                if existing is None:
                    connection.execute(
                        "INSERT INTO authority_metadata VALUES (1, ?, ?, ?)", (_CONTRACT, _VERSION, canonical_root),
                    )
                elif tuple(existing) != (_CONTRACT, _VERSION, canonical_root):
                    raise TrajectoryHandoffRefused("trajectory authority database metadata conflicts with this root")
                connection.execute("COMMIT")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        finally:
            connection.close()

    def _validate_database(self) -> None:
        with self._connection() as connection:
            row = connection.execute("SELECT contract,version,data_root FROM authority_metadata WHERE singleton=1").fetchone()
            if row is None or tuple(row) != (_CONTRACT, _VERSION, str(self.data_root)):
                raise TrajectoryHandoffRefused("trajectory authority database metadata is missing or incompatible")

    @contextmanager
    def _scope_lock(self, exclusivity_key: str) -> Iterator[None]:
        _require_digest(exclusivity_key, "exclusivity_key")
        with _LOCAL_LOCKS_GUARD:
            lock = _LOCAL_LOCKS.setdefault(f"{self.database_path}:{exclusivity_key}", threading.RLock())
        with lock:
            self._lock_root.mkdir(parents=True, exist_ok=True)
            # The complete exclusivity key is always rechecked from SQLite.
            # A shortened lock filename can only cause conservative extra
            # serialization on a cryptographic-prefix collision, while keeping
            # deeply nested Windows disposable roots below MAX_PATH.
            path = self._lock_root / f"{exclusivity_key[:24]}.lock"
            with path.open("a+b") as handle:
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
    def _acquire_os_lock(handle: Any) -> None:
        deadline = time.monotonic() + 10.0
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    return
                except OSError as exc:
                    if time.monotonic() >= deadline:
                        raise TrajectoryHandoffRefused("trajectory scope lock acquisition timed out") from exc
                    time.sleep(0.01)
        else:  # pragma: no cover - Windows is the production host, POSIX supports CI.
            import fcntl

            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return
                except BlockingIOError as exc:
                    if time.monotonic() >= deadline:
                        raise TrajectoryHandoffRefused("trajectory scope lock acquisition timed out") from exc
                    time.sleep(0.01)

    @staticmethod
    def _release_os_lock(handle: Any) -> None:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:  # pragma: no cover - Windows is the production host, POSIX supports CI.
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def discover_trajectory_write_authority(
    *, artifact_root: str | Path, family: TrajectoryWriterFamily, writer_identity: str,
) -> TrajectoryWriteAuthority | None:
    """Find an installed coordinator above an artifact root without creating one.

    No sidecar means this is a pre-handoff/test root and this function returns
    ``None``. Once a sidecar exists, a missing scope record is fail-closed.
    """

    root = Path(artifact_root).expanduser().resolve()
    for candidate in (root, *root.parents):
        database = candidate / _DB_RELATIVE_PATH
        if database.is_file():
            coordinator = TrajectoryWriterHandoffCoordinator.open_existing(data_root=candidate)
            return coordinator.authority_for_artifact_root(
                artifact_root=root, family=family, writer_identity=writer_identity,
            )
    return None


__all__ = [
    "AggregateTrajectoryReceipt",
    "TrajectoryHandoffBinding",
    "TrajectoryHandoffPhase",
    "TrajectoryHandoffReceipt",
    "TrajectoryHandoffRefused",
    "TrajectoryScopeIdentity",
    "TrajectoryWriteAuthority",
    "TrajectoryWriterFamily",
    "TrajectoryWriterHandoffCoordinator",
    "TrajectoryWriterToken",
    "discover_trajectory_write_authority",
]
