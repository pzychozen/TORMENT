"""Qualified durable recovery receipts for authorized share proposals.

This module records *only* evidence emitted after Fabric/TORMENT has already
made an authority decision.  A receipt is deliberately an operation-ledger
intent with no semantic transition, output, or target: it is recovery evidence,
not a second quorum or approval system.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import time
from contextlib import contextmanager
from typing import Any, Iterable, Mapping

from torment_service.proposals import ProposalRegistry, ShareProposal

from .canonical_intent import canonical_intent_text
from .connection import open_existing_native_core_connection
from .errors import SubstrateIdempotencyConflict
from .fabric_native_routing import NativeFabricRoutingCapability, NativeFabricRoutingScope
from .ids import native_id_from_bytes, native_id_to_bytes
from .objects import execute_semantic
from .schema import require_current_schema
from .shared_proposal_materialization import (
    AuthorizedSharedProposalOperator,
    AuthorizedSharedProposalQuorum,
    NativeSharedProposalStorageClock,
)


_RECEIPT_SCHEMA = "7G5E4D-R1"
_PREPARED_KIND = "NATIVE_AUTHORIZED_PROPOSAL_RECEIPT_PREPARED"
_COMPLETE_KIND = "NATIVE_AUTHORIZED_PROPOSAL_RECEIPT_COMPLETE"
_STAGE_KIND = "NATIVE_AUTHORIZED_PROPOSAL_RECEIPT_STAGE"
_PREPARED_PREFIX = "NATIVE_AUTHORIZED_PROPOSAL_RECEIPT:PREPARED:"
_COMPLETE_PREFIX = "NATIVE_AUTHORIZED_PROPOSAL_RECEIPT:COMPLETE:"
_STAGE_PREFIX = "NATIVE_AUTHORIZED_PROPOSAL_RECEIPT:STAGE:"


class AuthorizedProposalReceiptError(RuntimeError):
    """Raised when a qualified receipt cannot be verified or recovered."""


@dataclass(frozen=True)
class AuthorizedProposalReceipt:
    """A parsed immutable post-authority recovery witness."""

    payload: Mapping[str, Any]

    @property
    def kind(self) -> str:
        return str(self.payload["kind"])

    @property
    def workspace_id(self) -> str:
        return str(self.payload["workspace_id"])

    @property
    def domain_id(self) -> str:
        return str(self.payload["domain_id"])

    @property
    def native_storage_key(self) -> str:
        return str(self.payload["native_storage_key"])

    @property
    def source_proposal_ids(self) -> tuple[str, ...]:
        return tuple(str(value) for value in self.payload["source_proposal_ids"])

    @property
    def representative_id(self) -> str:
        return str(self.payload["representative_id"])

    @property
    def authority_agents(self) -> tuple[str, ...]:
        return tuple(str(value) for value in self.payload["authority_agents"])

    @property
    def witness(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(value) for value in self.payload["pre_conflict_witness"])

    @property
    def clock(self) -> NativeSharedProposalStorageClock:
        value = self.payload["frozen_clock"]
        return NativeSharedProposalStorageClock(
            logical_step=int(value["logical_step"]),
            created_ts=int(value["created_ts"]),
            last_active_ts=int(value["last_active_ts"]),
            last_reinforced_ts=int(value["last_reinforced_ts"]),
        )

    @property
    def policy(self) -> dict[str, Any]:
        return dict(self.payload["policy"])

    @property
    def embedding_provider(self) -> str:
        return str(self.payload["embedding_provider"])

    @property
    def embedding_model(self) -> str:
        return str(self.payload["embedding_model"])

    @property
    def process_call(self) -> dict[str, Any]:
        return dict(self.payload.get("process_call", {}))


def proposal_immutable_facts(proposal: ShareProposal) -> dict[str, Any]:
    """Facts whose drift makes recovery unsafe; mutable event fields excluded."""
    if not isinstance(proposal, ShareProposal):
        raise AuthorizedProposalReceiptError("receipt source must be a ShareProposal")
    return {
        "proposal_id": proposal.proposal_id,
        "workspace_id": proposal.workspace_id,
        "domain_id": proposal.domain_id,
        "agent_id": proposal.agent_id,
        "summary": proposal.summary,
        "embedding": [float(value) for value in proposal.embedding],
        "mtype": proposal.mtype,
        "confidence": float(proposal.confidence),
        "strength": float(proposal.strength),
        "created_ts": int(proposal.created_ts),
        "half_life_days": (
            None if proposal.half_life_days is None else float(proposal.half_life_days)
        ),
    }


def proposal_immutable_digest(proposals: Iterable[ShareProposal]) -> str:
    return sha256(
        canonical_intent_text([proposal_immutable_facts(item) for item in proposals]).encode("utf-8")
    ).hexdigest()


def verify_receipt_sources(
    receipt: AuthorizedProposalReceipt,
    registry: ProposalRegistry,
) -> tuple[ShareProposal, ...]:
    """Return current proposal records only when their immutable facts match."""
    latest = registry.apply_events()
    proposals: list[ShareProposal] = []
    for proposal_id in receipt.source_proposal_ids:
        proposal = latest.get(proposal_id)
        if proposal is None:
            raise AuthorizedProposalReceiptError(
                f"receipt source proposal is missing: {proposal_id}"
            )
        proposals.append(proposal)
    if proposal_immutable_digest(proposals) != receipt.payload["source_facts_digest"]:
        raise AuthorizedProposalReceiptError("receipt source immutable facts differ")
    if tuple(proposal.proposal_id for proposal in proposals) != receipt.source_proposal_ids:
        raise AuthorizedProposalReceiptError("receipt source order differs")
    return tuple(proposals)


class NativeAuthorizedProposalReceiptStore:
    """Receipt-only use of an already prepared qualified native core.

    It deliberately opens a short-lived core connection per ledger operation;
    no caller-supplied ordinary SQLite handle or backend selection is accepted.
    """

    def __init__(self, capability: NativeFabricRoutingCapability) -> None:
        if not isinstance(capability, NativeFabricRoutingCapability):
            raise ValueError("a prepared NativeFabricRoutingCapability is required")
        self._capability = capability

    @property
    def core_id(self) -> str:
        """Canonical identity of the one prepared core trusted by this store."""
        return str(self._capability.core_id)

    def require_current_core(self, receipt: AuthorizedProposalReceipt) -> None:
        if receipt.payload.get("native_core_id") != self.core_id:
            raise AuthorizedProposalReceiptError("receipt belongs to a different native core")

    def prepare_quorum(
        self,
        *,
        authorization: AuthorizedSharedProposalQuorum,
        authority_proposal_ids: tuple[str, ...],
        sim_threshold: float,
        min_distinct_agents: int,
        step: int | None,
        native_storage_key: str,
        pre_conflict_witness: list[dict[str, Any]],
        policy: Mapping[str, Any],
        process_call: Mapping[str, Any],
    ) -> AuthorizedProposalReceipt:
        if not isinstance(authorization, AuthorizedSharedProposalQuorum):
            raise ValueError("already-authorized quorum facts are required")
        source_ids = {proposal.proposal_id for proposal in authorization.participating_proposals}
        if (
            not authority_proposal_ids
            or any(not isinstance(item, str) or item not in source_ids for item in authority_proposal_ids)
        ):
            raise ValueError("authority_proposal_ids must be caller-emitted source facts")
        return self._prepare(
            self._quorum_payload(
                authorization=authorization,
                authority_proposal_ids=authority_proposal_ids,
                sim_threshold=sim_threshold,
                min_distinct_agents=min_distinct_agents,
                step=step,
                native_storage_key=native_storage_key,
                pre_conflict_witness=pre_conflict_witness,
                policy=policy,
                process_call=process_call,
            )
        )

    def prepare_operator(
        self,
        *,
        authorization: AuthorizedSharedProposalOperator,
        native_storage_key: str,
        policy: Mapping[str, Any],
    ) -> AuthorizedProposalReceipt:
        if not isinstance(authorization, AuthorizedSharedProposalOperator):
            raise ValueError("already-authorized operator approval facts are required")
        return self._prepare(
            self._operator_payload(
                authorization=authorization,
                native_storage_key=native_storage_key,
                policy=policy,
            )
        )

    def get(self, *, workspace_id: str, domain_id: str, native_storage_key: str) -> AuthorizedProposalReceipt | None:
        scope = self._scope(workspace_id, domain_id)
        with self._open_core() as connection:
            row = connection.execute(
                "SELECT canonical_intent_json FROM operations "
                "WHERE idempotency_namespace_id=? AND idempotency_key=?",
                (native_id_to_bytes(scope.idempotency_namespace_id), _PREPARED_PREFIX + native_storage_key),
            ).fetchone()
        if row is None:
            return None
        receipt = _decode_receipt(row[0])
        self._require_scope(receipt, workspace_id, domain_id)
        self.require_current_core(receipt)
        return receipt

    def list_incomplete_quorum(
        self, *, workspace_id: str, domain_id: str,
    ) -> list[AuthorizedProposalReceipt]:
        records: list[AuthorizedProposalReceipt] = []
        for receipt in self._list_prepared(workspace_id=workspace_id, domain_id=domain_id):
            if receipt.kind != "QUORUM":
                continue
            if self.completion(receipt) is None:
                records.append(receipt)
        return records

    def completed_quorum_for_call(
        self,
        *,
        workspace_id: str,
        domain_id: str,
        process_call: Mapping[str, Any],
    ) -> list[tuple[AuthorizedProposalReceipt, dict[str, Any]]]:
        wanted = dict(process_call)
        out: list[tuple[AuthorizedProposalReceipt, dict[str, Any]]] = []
        for receipt in self._list_prepared(workspace_id=workspace_id, domain_id=domain_id):
            if receipt.kind != "QUORUM" or receipt.process_call != wanted:
                continue
            result = self.completion(receipt)
            if result is not None:
                out.append((receipt, result))
        out.sort(key=lambda item: item[0].clock.created_ts)
        return out

    def completion(self, receipt: AuthorizedProposalReceipt) -> dict[str, Any] | None:
        self.require_current_core(receipt)
        scope = self._scope(receipt.workspace_id, receipt.domain_id)
        with self._open_core() as connection:
            row = connection.execute(
                "SELECT canonical_intent_json FROM operations "
                "WHERE idempotency_namespace_id=? AND idempotency_key=?",
                (native_id_to_bytes(scope.idempotency_namespace_id), _COMPLETE_PREFIX + receipt.native_storage_key),
            ).fetchone()
        if row is None:
            return None
        return _decode_completion(row[0], receipt)

    def complete(self, receipt: AuthorizedProposalReceipt, result: Mapping[str, Any]) -> dict[str, Any]:
        self.require_current_core(receipt)
        payload = {
            "schema": _RECEIPT_SCHEMA,
            "kind": receipt.kind,
            "native_storage_key": receipt.native_storage_key,
            "prepared_digest": _payload_digest(receipt.payload),
            "result": dict(result),
        }
        intent = canonical_intent_text(payload)
        scope = self._scope(receipt.workspace_id, receipt.domain_id)
        with self._open_core() as connection:
            try:
                return execute_semantic(
                    connection,
                    scope.idempotency_namespace_id,
                    _COMPLETE_PREFIX + receipt.native_storage_key,
                    _COMPLETE_KIND,
                    intent,
                    lambda _operation_id: dict(payload["result"]),
                    lambda _tx: dict(payload["result"]),
                )
            except SubstrateIdempotencyConflict as exc:
                raise AuthorizedProposalReceiptError("receipt completion intent differs") from exc

    def has_stage(self, receipt: AuthorizedProposalReceipt, stage: str) -> bool:
        self.require_current_core(receipt)
        scope = self._scope(receipt.workspace_id, receipt.domain_id)
        key = _stage_key(receipt.native_storage_key, stage)
        with self._open_core() as connection:
            row = connection.execute(
                "SELECT canonical_intent_json FROM operations "
                "WHERE idempotency_namespace_id=? AND idempotency_key=?",
                (native_id_to_bytes(scope.idempotency_namespace_id), key),
            ).fetchone()
        if row is None:
            return False
        _decode_stage(row[0], receipt, stage)
        return True

    def mark_stage(self, receipt: AuthorizedProposalReceipt, stage: str) -> None:
        self.require_current_core(receipt)
        if not isinstance(stage, str) or not stage or ":" in stage:
            raise ValueError("receipt stage must be non-empty text without ':'")
        payload = {
            "schema": _RECEIPT_SCHEMA,
            "kind": receipt.kind,
            "native_storage_key": receipt.native_storage_key,
            "prepared_digest": _payload_digest(receipt.payload),
            "stage": stage,
        }
        intent = canonical_intent_text(payload)
        scope = self._scope(receipt.workspace_id, receipt.domain_id)
        with self._open_core() as connection:
            try:
                execute_semantic(
                    connection,
                    scope.idempotency_namespace_id,
                    _stage_key(receipt.native_storage_key, stage),
                    _STAGE_KIND,
                    intent,
                    lambda _operation_id: None,
                    lambda _tx: None,
                )
            except SubstrateIdempotencyConflict as exc:
                raise AuthorizedProposalReceiptError("receipt stage intent differs") from exc

    def _prepare(self, payload: dict[str, Any]) -> AuthorizedProposalReceipt:
        prospective = AuthorizedProposalReceipt(payload)
        existing = self.get(
            workspace_id=prospective.workspace_id,
            domain_id=prospective.domain_id,
            native_storage_key=prospective.native_storage_key,
        )
        if existing is not None:
            if _without_clock(existing.payload) != _without_clock(payload):
                raise AuthorizedProposalReceiptError("receipt intent differs for native storage key")
            return existing
        intent = canonical_intent_text(payload)
        scope = self._scope(prospective.workspace_id, prospective.domain_id)
        with self._open_core() as connection:
            try:
                execute_semantic(
                    connection,
                    scope.idempotency_namespace_id,
                    _PREPARED_PREFIX + prospective.native_storage_key,
                    _PREPARED_KIND,
                    intent,
                    lambda _operation_id: prospective,
                    lambda _tx: prospective,
                )
            except SubstrateIdempotencyConflict as exc:
                raise AuthorizedProposalReceiptError("receipt intent differs for native storage key") from exc
        return prospective

    def _list_prepared(self, *, workspace_id: str, domain_id: str) -> list[AuthorizedProposalReceipt]:
        scope = self._scope(workspace_id, domain_id)
        with self._open_core() as connection:
            rows = connection.execute(
                "SELECT canonical_intent_json FROM operations "
                "WHERE idempotency_namespace_id=? AND operation_kind=? "
                "ORDER BY created_at_ns, idempotency_key",
                (native_id_to_bytes(scope.idempotency_namespace_id), _PREPARED_KIND),
            ).fetchall()
        receipts: list[AuthorizedProposalReceipt] = []
        for row in rows:
            receipt = _decode_receipt(row[0])
            if receipt.workspace_id == workspace_id and receipt.domain_id == domain_id:
                self.require_current_core(receipt)
                receipts.append(receipt)
        return receipts

    @contextmanager
    def _open_core(self):
        with open_existing_native_core_connection(self._capability.core_database_path) as opened:
            metadata = require_current_schema(opened.connection)
            if native_id_from_bytes(metadata.core_id) != self._capability.core_id:
                raise AuthorizedProposalReceiptError("prepared native core identity differs")
            yield opened.connection

    def _scope(self, workspace_id: str, domain_id: str) -> NativeFabricRoutingScope:
        scope = self._capability.claimed_scope(
            workspace_id=workspace_id,
            scope="shared",
            agent_id="collective",
            domain_id=domain_id,
        )
        if scope is None:
            raise AuthorizedProposalReceiptError("receipt target is not a claimed native shared scope")
        return scope

    @staticmethod
    def _require_scope(receipt: AuthorizedProposalReceipt, workspace_id: str, domain_id: str) -> None:
        if receipt.workspace_id != workspace_id or receipt.domain_id != domain_id:
            raise AuthorizedProposalReceiptError("receipt scope differs from requested recovery scope")

    def _quorum_payload(
        self,
        *,
        authorization: AuthorizedSharedProposalQuorum,
        authority_proposal_ids: tuple[str, ...],
        sim_threshold: float,
        min_distinct_agents: int,
        step: int | None,
        native_storage_key: str,
        pre_conflict_witness: list[dict[str, Any]],
        policy: Mapping[str, Any],
        process_call: Mapping[str, Any],
    ) -> dict[str, Any]:
        now = int(time.time())
        clock = NativeSharedProposalStorageClock(
            logical_step=int(step) if step is not None else now,
            created_ts=now,
            last_active_ts=now,
            last_reinforced_ts=now,
        )
        sources = tuple(authorization.participating_proposals)
        witness = [dict(item) for item in pre_conflict_witness]
        payload = {
            "schema": _RECEIPT_SCHEMA,
            "kind": "QUORUM",
            "authority_decision_owner": "TORMENT",
            "native_core_id": self.core_id,
            "workspace_id": authorization.workspace_id,
            "domain_id": authorization.domain_id,
            "source_proposal_ids": [item.proposal_id for item in sources],
            "authority_proposal_ids": list(authority_proposal_ids),
            "authority_agents": list(authorization.support_agents),
            "representative_id": authorization.representative.proposal_id,
            "sim_threshold": float(sim_threshold),
            "min_distinct_agents": int(min_distinct_agents),
            "step": None if step is None else int(step),
            "frozen_clock": {
                "logical_step": clock.logical_step,
                "created_ts": clock.created_ts,
                "last_active_ts": clock.last_active_ts,
                "last_reinforced_ts": clock.last_reinforced_ts,
            },
            "native_storage_key": native_storage_key,
            "pre_conflict_witness": witness,
            "pre_conflict_digest": _payload_digest(witness),
            "policy": dict(policy),
            "process_call": dict(process_call),
            "embedding_provider": authorization.embedding_provider,
            "embedding_model": authorization.embedding_model,
            "source_facts_digest": proposal_immutable_digest(sources),
        }
        _validate_payload(payload)
        return payload

    def _operator_payload(
        self,
        *,
        authorization: AuthorizedSharedProposalOperator,
        native_storage_key: str,
        policy: Mapping[str, Any],
    ) -> dict[str, Any]:
        now = int(time.time())
        clock = NativeSharedProposalStorageClock(now, now, now, now)
        proposal = authorization.proposal
        payload = {
            "schema": _RECEIPT_SCHEMA,
            "kind": "OPERATOR_APPROVE",
            "authority_decision_owner": "TORMENT",
            "native_core_id": self.core_id,
            "workspace_id": authorization.workspace_id,
            "domain_id": authorization.domain_id,
            "source_proposal_ids": [proposal.proposal_id],
            "authority_proposal_ids": [proposal.proposal_id],
            "authority_agents": [proposal.agent_id],
            "representative_id": proposal.proposal_id,
            "decision": "approve",
            "frozen_clock": {
                "logical_step": clock.logical_step,
                "created_ts": clock.created_ts,
                "last_active_ts": clock.last_active_ts,
                "last_reinforced_ts": clock.last_reinforced_ts,
            },
            "native_storage_key": native_storage_key,
            "pre_conflict_witness": [],
            "pre_conflict_digest": _payload_digest([]),
            "policy": dict(policy),
            "embedding_provider": authorization.embedding_provider,
            "embedding_model": authorization.embedding_model,
            "source_facts_digest": proposal_immutable_digest((proposal,)),
        }
        _validate_payload(payload)
        return payload


def _decode_receipt(value: object) -> AuthorizedProposalReceipt:
    try:
        payload = json.loads(str(value))
    except (TypeError, json.JSONDecodeError) as exc:
        raise AuthorizedProposalReceiptError("malformed prepared receipt") from exc
    if canonical_intent_text(payload) != value:
        raise AuthorizedProposalReceiptError("prepared receipt is not canonical")
    if not isinstance(payload, dict):
        raise AuthorizedProposalReceiptError("prepared receipt must be an object")
    _validate_payload(payload)
    return AuthorizedProposalReceipt(payload)


def _decode_completion(value: object, receipt: AuthorizedProposalReceipt) -> dict[str, Any]:
    payload = _decode_auxiliary(value, "completion")
    if (
        payload.get("schema") != _RECEIPT_SCHEMA
        or payload.get("kind") != receipt.kind
        or payload.get("native_storage_key") != receipt.native_storage_key
        or payload.get("prepared_digest") != _payload_digest(receipt.payload)
        or not isinstance(payload.get("result"), dict)
    ):
        raise AuthorizedProposalReceiptError("receipt completion does not match prepared receipt")
    return dict(payload["result"])


def _decode_stage(value: object, receipt: AuthorizedProposalReceipt, stage: str) -> None:
    payload = _decode_auxiliary(value, "stage")
    if (
        payload.get("schema") != _RECEIPT_SCHEMA
        or payload.get("kind") != receipt.kind
        or payload.get("native_storage_key") != receipt.native_storage_key
        or payload.get("prepared_digest") != _payload_digest(receipt.payload)
        or payload.get("stage") != stage
    ):
        raise AuthorizedProposalReceiptError("receipt stage does not match prepared receipt")


def _decode_auxiliary(value: object, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(str(value))
    except (TypeError, json.JSONDecodeError) as exc:
        raise AuthorizedProposalReceiptError(f"malformed receipt {label}") from exc
    if not isinstance(payload, dict) or canonical_intent_text(payload) != value:
        raise AuthorizedProposalReceiptError(f"receipt {label} is not canonical")
    return payload


def _validate_payload(payload: Mapping[str, Any]) -> None:
    required = {
        "schema", "kind", "authority_decision_owner", "native_core_id", "workspace_id", "domain_id",
        "source_proposal_ids", "authority_proposal_ids", "authority_agents",
        "representative_id", "frozen_clock", "native_storage_key",
        "pre_conflict_witness", "pre_conflict_digest", "policy",
        "embedding_provider", "embedding_model", "source_facts_digest",
    }
    missing = required.difference(payload)
    if missing or payload.get("schema") != _RECEIPT_SCHEMA:
        raise AuthorizedProposalReceiptError("receipt schema fields are incomplete")
    if payload.get("kind") not in {"QUORUM", "OPERATOR_APPROVE"}:
        raise AuthorizedProposalReceiptError("receipt kind is invalid")
    if payload.get("authority_decision_owner") != "TORMENT":
        raise AuthorizedProposalReceiptError("receipt authority owner is invalid")
    for field in ("native_core_id", "workspace_id", "domain_id", "representative_id", "native_storage_key", "embedding_provider", "embedding_model", "source_facts_digest", "pre_conflict_digest"):
        if not isinstance(payload.get(field), str) or not payload[field]:
            raise AuthorizedProposalReceiptError(f"receipt {field} is invalid")
    for field in ("source_proposal_ids", "authority_proposal_ids", "authority_agents"):
        values = payload.get(field)
        if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values):
            raise AuthorizedProposalReceiptError(f"receipt {field} is invalid")
    if payload["representative_id"] not in payload["source_proposal_ids"]:
        raise AuthorizedProposalReceiptError("receipt representative is not a source")
    if len(set(payload["source_proposal_ids"])) != len(payload["source_proposal_ids"]):
        raise AuthorizedProposalReceiptError("receipt source IDs are not distinct")
    if not set(payload["authority_proposal_ids"]).issubset(payload["source_proposal_ids"]):
        raise AuthorizedProposalReceiptError("receipt authority IDs are not source IDs")
    if not isinstance(payload.get("pre_conflict_witness"), list) or not isinstance(payload.get("policy"), dict):
        raise AuthorizedProposalReceiptError("receipt witness or policy is invalid")
    try:
        NativeSharedProposalStorageClock(**dict(payload["frozen_clock"]))
    except (TypeError, ValueError) as exc:
        raise AuthorizedProposalReceiptError("receipt frozen clock is invalid") from exc
    if payload["kind"] == "QUORUM":
        if not isinstance(payload.get("sim_threshold"), (int, float)) or not isinstance(payload.get("min_distinct_agents"), int):
            raise AuthorizedProposalReceiptError("quorum receipt authority knobs are invalid")
        if not isinstance(payload.get("process_call"), dict):
            raise AuthorizedProposalReceiptError("quorum receipt process call is invalid")
    elif payload.get("decision") != "approve":
        raise AuthorizedProposalReceiptError("operator receipt decision is invalid")


def _without_clock(payload: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.pop("frozen_clock", None)
    return out


def _payload_digest(value: Any) -> str:
    return sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


def _stage_key(native_storage_key: str, stage: str) -> str:
    return _STAGE_PREFIX + stage + ":" + native_storage_key


__all__ = [
    "AuthorizedProposalReceiptError",
    "AuthorizedProposalReceipt",
    "NativeAuthorizedProposalReceiptStore",
    "proposal_immutable_digest",
    "proposal_immutable_facts",
    "verify_receipt_sources",
]
