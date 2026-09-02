"""Immutable native-ledger receipts for one public ingest operation.

These receipts are recovery evidence only.  They use the existing operation
ledger and deliberately create no semantic transition, target, output, memory
object, or representation.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping

from torment_service.ingest_orchestration import (
    PreparedFabricIngest,
    deserialize_prepared_fabric_ingest,
    serialize_prepared_fabric_ingest,
)

from .canonical_intent import canonical_intent_text
from .connection import open_existing_native_core_connection
from .errors import SubstrateIdempotencyConflict
from .ids import native_id_from_bytes, native_id_to_bytes
from .objects import execute_semantic
from .production_native_owner import NativeProductionResourceOwner
from .schema import require_current_schema


_SCHEMA = "TORMENT_PUBLIC_MUTATION_RECEIPT_V1"
_RESERVED_KIND = "NATIVE_PUBLIC_MUTATION_RECEIPT_RESERVED"
_COGNITION_STARTED_KIND = "NATIVE_PUBLIC_MUTATION_RECEIPT_COGNITION_STARTED"
_PREPARED_KIND = "NATIVE_PUBLIC_MUTATION_RECEIPT_PREPARED"
_COMPLETE_KIND = "NATIVE_PUBLIC_MUTATION_RECEIPT_COMPLETE"
_PREFIX = "NATIVE_PUBLIC_MUTATION_RECEIPT"


class PublicMutationReceiptError(RuntimeError):
    """Native public-mutation recovery evidence is malformed or unavailable."""


class PublicMutationIdempotencyConflict(PublicMutationReceiptError):
    """The same public key was reused for distinct semantic request facts."""

    status_code = 409


class PublicMutationRecoveryRequired(PublicMutationReceiptError):
    """Cognition may have begun, so safe automatic re-execution is forbidden."""

    status_code = 409


class PublicMutationRecoveryState(str, Enum):
    NEW = "NEW"
    COMMITTED_SAME_REQUEST = "COMMITTED_SAME_REQUEST"
    INCOMPLETE_RECOVERABLE = "INCOMPLETE_RECOVERABLE"
    COGNITION_OUTCOME_UNCERTAIN = "COGNITION_OUTCOME_UNCERTAIN"


@dataclass(frozen=True)
class NativePublicMutationReservation:
    """Validated immutable RESERVED facts for one public operation."""

    payload: Mapping[str, Any]

    @property
    def workspace_id(self) -> str:
        return str(self.payload["workspace_id"])

    @property
    def agent_id(self) -> str:
        return str(self.payload["agent_id"])

    @property
    def native_operation_key(self) -> str:
        return str(self.payload["native_operation_key"])

    @property
    def public_request_fingerprint(self) -> str:
        return str(self.payload["public_request_fingerprint"])

    @property
    def digest(self) -> str:
        return _digest(self.payload)


@dataclass(frozen=True)
class NativePublicMutationRecovery:
    """One pre-cognition recovery decision, with no authority to rerun itself."""

    state: PublicMutationRecoveryState
    reservation: NativePublicMutationReservation
    prepared: PreparedFabricIngest | None = None
    result: dict[str, Any] | None = None


class NativePublicMutationReceiptStore:
    """Receipt-only adapter over an admitted agent-private ledger namespace."""

    def __init__(self, owner: NativeProductionResourceOwner) -> None:
        if not isinstance(owner, NativeProductionResourceOwner):
            raise ValueError("native public receipts require an active production owner")
        self._owner = owner

    @property
    def core_id(self) -> str:
        return str(self._owner.authority_facts.core_id)

    def reserve(
        self,
        *,
        workspace_id: str,
        agent_id: str,
        operation: str,
        native_operation_key: str,
        public_request_fingerprint: str,
    ) -> NativePublicMutationReservation:
        if operation != "ingest":
            raise PublicMutationReceiptError("only public ingest receipt operations are admitted")
        for name, value in (
            ("workspace_id", workspace_id), ("agent_id", agent_id),
            ("native_operation_key", native_operation_key),
            ("public_request_fingerprint", public_request_fingerprint),
        ):
            if not isinstance(value, str) or not value:
                raise PublicMutationReceiptError(f"{name} must be non-empty text")
        prospective = {
            "schema": _SCHEMA,
            "native_core_id": self.core_id,
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "public_operation": operation,
            "native_operation_key": native_operation_key,
            "public_request_fingerprint": public_request_fingerprint,
            "public_identity_contract": "public-mutation/v1",
        }
        existing = self._read(workspace_id, agent_id, _key("RESERVED", native_operation_key))
        if existing is not None:
            reservation = _decode_reservation(existing)
            if reservation.payload != prospective:
                raise PublicMutationIdempotencyConflict("PUBLIC_IDEMPOTENCY_CONFLICT")
            return reservation
        reservation = NativePublicMutationReservation(prospective)
        try:
            with self._open(workspace_id, agent_id) as (connection, namespace):
                execute_semantic(
                    connection, namespace, _key("RESERVED", native_operation_key), _RESERVED_KIND,
                    canonical_intent_text(prospective), lambda _operation_id: reservation,
                    lambda _transaction: reservation,
                )
        except SubstrateIdempotencyConflict as exc:
            raise PublicMutationIdempotencyConflict("PUBLIC_IDEMPOTENCY_CONFLICT") from exc
        return reservation

    def recover(self, reservation: NativePublicMutationReservation) -> NativePublicMutationRecovery:
        self._require_reservation(reservation)
        complete = self._read(reservation.workspace_id, reservation.agent_id, _key("COMPLETE", reservation.native_operation_key))
        if complete is not None:
            prepared = self._read(
                reservation.workspace_id, reservation.agent_id,
                _key("PREPARED", reservation.native_operation_key),
            )
            if prepared is None:
                raise PublicMutationReceiptError("completion receipt has no PREPARED receipt")
            return NativePublicMutationRecovery(
                PublicMutationRecoveryState.COMMITTED_SAME_REQUEST, reservation,
                result=_decode_complete(
                    complete, reservation,
                    expected_prepared_digest=_decode_prepared_payload(prepared, reservation)["prepared_digest"],
                ),
            )
        prepared = self._read(reservation.workspace_id, reservation.agent_id, _key("PREPARED", reservation.native_operation_key))
        if prepared is not None:
            return NativePublicMutationRecovery(
                PublicMutationRecoveryState.INCOMPLETE_RECOVERABLE, reservation,
                prepared=_decode_prepared(prepared, reservation),
            )
        started = self._read(reservation.workspace_id, reservation.agent_id, _key("COGNITION_STARTED", reservation.native_operation_key))
        if started is not None:
            _decode_stage(started, reservation, "COGNITION_STARTED")
            return NativePublicMutationRecovery(PublicMutationRecoveryState.COGNITION_OUTCOME_UNCERTAIN, reservation)
        return NativePublicMutationRecovery(PublicMutationRecoveryState.NEW, reservation)

    def mark_cognition_started(self, reservation: NativePublicMutationReservation) -> None:
        self._write_stage(reservation, "COGNITION_STARTED")

    def write_prepared(
        self, reservation: NativePublicMutationReservation, prepared: PreparedFabricIngest,
    ) -> PreparedFabricIngest:
        self._require_reservation(reservation)
        if (
            prepared.native_operation_key != reservation.native_operation_key
            or prepared.public_request_fingerprint != reservation.public_request_fingerprint
            or prepared.workspace_id != reservation.workspace_id
            or prepared.agent_id != reservation.agent_id
        ):
            raise PublicMutationReceiptError("prepared facts do not bind the reserved public operation")
        serialized = serialize_prepared_fabric_ingest(prepared)
        payload = {
            "schema": _SCHEMA,
            "reservation_digest": reservation.digest,
            "native_operation_key": reservation.native_operation_key,
            "public_request_fingerprint": reservation.public_request_fingerprint,
            "prepared": serialized,
            "prepared_digest": _digest(serialized),
        }
        existing = self._read(reservation.workspace_id, reservation.agent_id, _key("PREPARED", reservation.native_operation_key))
        if existing is not None:
            recovered = _decode_prepared(existing, reservation)
            if serialize_prepared_fabric_ingest(recovered) != serialized:
                raise PublicMutationIdempotencyConflict("prepared facts differ for public operation")
            return recovered
        try:
            with self._open(reservation.workspace_id, reservation.agent_id) as (connection, namespace):
                execute_semantic(
                    connection, namespace, _key("PREPARED", reservation.native_operation_key), _PREPARED_KIND,
                    canonical_intent_text(payload), lambda _operation_id: prepared,
                    lambda _transaction: prepared,
                )
        except SubstrateIdempotencyConflict as exc:
            raise PublicMutationIdempotencyConflict("prepared facts differ for public operation") from exc
        return prepared

    def complete(
        self, reservation: NativePublicMutationReservation, result: Mapping[str, Any],
    ) -> dict[str, Any]:
        self._require_reservation(reservation)
        prepared_payload = self._read(reservation.workspace_id, reservation.agent_id, _key("PREPARED", reservation.native_operation_key))
        if prepared_payload is None:
            raise PublicMutationReceiptError("cannot complete public operation without PREPARED receipt")
        prepared_digest = _decode_prepared_payload(prepared_payload, reservation)["prepared_digest"]
        payload = {
            "schema": _SCHEMA,
            "reservation_digest": reservation.digest,
            "prepared_digest": prepared_digest,
            "native_operation_key": reservation.native_operation_key,
            "public_request_fingerprint": reservation.public_request_fingerprint,
            "result": dict(result),
        }
        try:
            canonical_intent_text(payload)
        except Exception as exc:
            raise PublicMutationReceiptError("public completion result is not canonical") from exc
        existing = self._read(reservation.workspace_id, reservation.agent_id, _key("COMPLETE", reservation.native_operation_key))
        if existing is not None:
            recovered = _decode_complete(
                existing, reservation, expected_prepared_digest=prepared_digest,
            )
            if recovered != payload["result"]:
                raise PublicMutationIdempotencyConflict("public completion result differs")
            return recovered
        try:
            with self._open(reservation.workspace_id, reservation.agent_id) as (connection, namespace):
                return execute_semantic(
                    connection, namespace, _key("COMPLETE", reservation.native_operation_key), _COMPLETE_KIND,
                    canonical_intent_text(payload), lambda _operation_id: dict(payload["result"]),
                    lambda _transaction: dict(payload["result"]),
                )
        except SubstrateIdempotencyConflict as exc:
            raise PublicMutationIdempotencyConflict("public completion result differs") from exc

    def _write_stage(self, reservation: NativePublicMutationReservation, stage: str) -> None:
        self._require_reservation(reservation)
        payload = {
            "schema": _SCHEMA,
            "reservation_digest": reservation.digest,
            "native_operation_key": reservation.native_operation_key,
            "public_request_fingerprint": reservation.public_request_fingerprint,
            "stage": stage,
        }
        try:
            with self._open(reservation.workspace_id, reservation.agent_id) as (connection, namespace):
                execute_semantic(
                    connection, namespace, _key(stage, reservation.native_operation_key), _COGNITION_STARTED_KIND,
                    canonical_intent_text(payload), lambda _operation_id: True, lambda _transaction: True,
                )
        except SubstrateIdempotencyConflict as exc:
            raise PublicMutationIdempotencyConflict("public receipt stage differs") from exc

    def _read(self, workspace_id: str, agent_id: str, key: str) -> str | None:
        with self._open(workspace_id, agent_id) as (connection, namespace):
            row = connection.execute(
                "SELECT canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
                (native_id_to_bytes(namespace), key),
            ).fetchone()
        return None if row is None else str(row[0])

    @contextmanager
    def _open(self, workspace_id: str, agent_id: str):
        scope = self._receipt_scope(workspace_id, agent_id)
        with open_existing_native_core_connection(self._owner.authority_facts.core_database_path) as opened:
            metadata = require_current_schema(opened.connection)
            if native_id_from_bytes(metadata.core_id) != self._owner.authority_facts.core_id:
                raise PublicMutationReceiptError("active native core differs from receipt core")
            yield opened.connection, scope.idempotency_namespace_id

    def _receipt_scope(self, workspace_id: str, agent_id: str):
        # The admitted private-agent scope exists independently of a later
        # shared-domain route.  Its idempotency namespace is recovery-key
        # ownership only; it never makes shared memory private.
        runtime = self._owner._recover_active_runtime()
        try:
            scope = runtime.lookup_private(agent_id).fabric_routing_scope
        except Exception as exc:
            raise PublicMutationReceiptError("admitted private receipt namespace is unavailable") from exc
        if scope.runtime_scope.workspace_id != workspace_id:
            raise PublicMutationReceiptError("receipt workspace is not admitted by the active owner")
        return scope

    def _require_reservation(self, reservation: NativePublicMutationReservation) -> None:
        if not isinstance(reservation, NativePublicMutationReservation):
            raise PublicMutationReceiptError("native public reservation is required")
        current = self.reserve(
            workspace_id=reservation.workspace_id, agent_id=reservation.agent_id,
            operation=str(reservation.payload["public_operation"]),
            native_operation_key=reservation.native_operation_key,
            public_request_fingerprint=reservation.public_request_fingerprint,
        )
        if current != reservation:
            raise PublicMutationReceiptError("public reservation facts differ")


def _key(stage: str, native_operation_key: str) -> str:
    return f"{_PREFIX}:{stage}:{native_operation_key}"


def _digest(payload: Mapping[str, Any]) -> str:
    return sha256(canonical_intent_text(dict(payload)).encode("utf-8")).hexdigest()


def _decode_payload(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise PublicMutationReceiptError("native public receipt is malformed") from exc
    if not isinstance(payload, dict) or canonical_intent_text(payload) != value:
        raise PublicMutationReceiptError("native public receipt is not canonical")
    if payload.get("schema") != _SCHEMA:
        raise PublicMutationReceiptError("native public receipt schema differs")
    return payload


def _decode_reservation(value: str) -> NativePublicMutationReservation:
    payload = _decode_payload(value)
    required = {
        "native_core_id", "workspace_id", "agent_id", "public_operation",
        "native_operation_key", "public_request_fingerprint", "public_identity_contract",
    }
    if not required <= payload.keys() or payload.get("public_operation") != "ingest":
        raise PublicMutationReceiptError("reserved receipt lacks immutable public facts")
    return NativePublicMutationReservation(payload)


def _decode_stage(value: str, reservation: NativePublicMutationReservation, stage: str) -> None:
    payload = _decode_payload(value)
    if (
        payload.get("stage") != stage
        or payload.get("reservation_digest") != reservation.digest
        or payload.get("native_operation_key") != reservation.native_operation_key
        or payload.get("public_request_fingerprint") != reservation.public_request_fingerprint
    ):
        raise PublicMutationReceiptError("public receipt stage differs from reservation")


def _decode_prepared_payload(value: str, reservation: NativePublicMutationReservation) -> dict[str, Any]:
    payload = _decode_payload(value)
    if (
        payload.get("reservation_digest") != reservation.digest
        or payload.get("native_operation_key") != reservation.native_operation_key
        or payload.get("public_request_fingerprint") != reservation.public_request_fingerprint
        or not isinstance(payload.get("prepared"), Mapping)
        or payload.get("prepared_digest") != _digest(payload["prepared"])
    ):
        raise PublicMutationReceiptError("prepared receipt differs from reservation")
    return payload


def _decode_prepared(value: str, reservation: NativePublicMutationReservation) -> PreparedFabricIngest:
    payload = _decode_prepared_payload(value, reservation)
    try:
        prepared = deserialize_prepared_fabric_ingest(payload["prepared"])
    except Exception as exc:
        raise PublicMutationReceiptError("prepared receipt cannot be rehydrated") from exc
    if (
        prepared.native_operation_key != reservation.native_operation_key
        or prepared.public_request_fingerprint != reservation.public_request_fingerprint
        or prepared.workspace_id != reservation.workspace_id
        or prepared.agent_id != reservation.agent_id
    ):
        raise PublicMutationReceiptError("rehydrated facts differ from reservation")
    return prepared


def _decode_complete(
    value: str,
    reservation: NativePublicMutationReservation,
    *,
    expected_prepared_digest: str | None = None,
) -> dict[str, Any]:
    payload = _decode_payload(value)
    if (
        payload.get("reservation_digest") != reservation.digest
        or payload.get("native_operation_key") != reservation.native_operation_key
        or payload.get("public_request_fingerprint") != reservation.public_request_fingerprint
        or not isinstance(payload.get("prepared_digest"), str)
        or not isinstance(payload.get("result"), dict)
    ):
        raise PublicMutationReceiptError("completion receipt differs from reservation")
    if expected_prepared_digest is not None and payload["prepared_digest"] != expected_prepared_digest:
        raise PublicMutationReceiptError("completion receipt differs from PREPARED receipt")
    return dict(payload["result"])


__all__ = [
    "NativePublicMutationReceiptStore",
    "NativePublicMutationRecovery",
    "NativePublicMutationReservation",
    "PublicMutationIdempotencyConflict",
    "PublicMutationReceiptError",
    "PublicMutationRecoveryRequired",
    "PublicMutationRecoveryState",
]
