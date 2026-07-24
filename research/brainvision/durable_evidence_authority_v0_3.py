from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import durable_evidence_durability_v0_3 as durability
import durable_evidence_primary_writer_v0_3 as primary_writer
import durable_evidence_replay_v0_3 as replay
import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


NOT_ATTEMPTED = "NOT_ATTEMPTED"
CONSUMED = "CONSUMED"
ATTEMPT_FAILED = "ATTEMPT_FAILED"
ATTEMPT_STATE_INDETERMINATE = "ATTEMPT_STATE_INDETERMINATE"

AUTHORITY_NOT_ATTEMPTED = "AUTHORITY_NOT_ATTEMPTED"
AUTHORITY_CONSUMED = "AUTHORITY_CONSUMED"
AUTHORITY_CONSUMPTION_ATTEMPT_FAILED = "AUTHORITY_CONSUMPTION_ATTEMPT_FAILED"
AUTHORITY_ATTEMPT_STATE_INDETERMINATE = "AUTHORITY_ATTEMPT_STATE_INDETERMINATE"
AUTHORITY_CLOSED_UNEXERCISED_AFTER_CONSUMPTION_RECORD_FAILURE = (
    "AUTHORITY_CLOSED_UNEXERCISED_AFTER_CONSUMPTION_RECORD_FAILURE"
)

AUTHORITY_FAILURE_EXIT_CODE = 4


class AuthorityReuseDenied(RuntimeError):
    pass


class AuthorityEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class AuthorityBeginState:
    execution_identity: str
    scientific_execution_authorization_identity: str
    state: str
    reuse_permission_consumed: bool
    protected_mutation_permitted: bool


@dataclass(frozen=True)
class AuthorityWriteEvidence:
    logical_record: dict
    stored_record_object: dict
    write_result: primary_writer.ImmutableWriteResult


@dataclass(frozen=True)
class AuthorityReplayResult:
    state: str
    scientific_state: str
    reusable: bool
    detail: str
    replay_classification: str
    accepted_logical_record_sha256: str | None = None
    accepted_stored_object_sha256: str | None = None


class SyntheticAuthorityContext:
    """Live synthetic guard only; durable replay remains post-event authority truth."""

    def __init__(self) -> None:
        self._begun_keys: set[tuple[str, str]] = set()

    def begin_once(
        self,
        *,
        execution_identity: str,
        scientific_execution_authorization_identity: str,
    ) -> None:
        key = (execution_identity, scientific_execution_authorization_identity)
        if key in self._begun_keys:
            raise AuthorityReuseDenied("authorization reuse is denied")
        self._begun_keys.add(key)


class SyntheticProtectedInvocation:
    def __init__(
        self,
        *,
        execution_identity: str,
        scientific_execution_authorization_identity: str,
        context: SyntheticAuthorityContext,
    ) -> None:
        _validate_hex64(execution_identity, "execution_identity")
        _validate_hex64(
            scientific_execution_authorization_identity,
            "scientific_execution_authorization_identity",
        )
        if not isinstance(context, SyntheticAuthorityContext):
            raise AuthorityEvidenceError("SyntheticAuthorityContext is required")
        self.execution_identity = execution_identity
        self.scientific_execution_authorization_identity = (
            scientific_execution_authorization_identity
        )
        self._context = context
        self._begun = False

    @property
    def live_state(self) -> str:
        if self._begun:
            return CONSUMED
        return NOT_ATTEMPTED

    @property
    def reuse_permission_consumed(self) -> bool:
        return self._begun

    def begin(self) -> AuthorityBeginState:
        if self._begun:
            raise AuthorityReuseDenied("authorization reuse is denied")
        self._context.begin_once(
            execution_identity=self.execution_identity,
            scientific_execution_authorization_identity=(
                self.scientific_execution_authorization_identity
            ),
        )
        self._begun = True
        return AuthorityBeginState(
            execution_identity=self.execution_identity,
            scientific_execution_authorization_identity=(
                self.scientific_execution_authorization_identity
            ),
            state=CONSUMED,
            reuse_permission_consumed=True,
            protected_mutation_permitted=True,
        )


def build_authority_consumed_logical_record(
    *, execution_identity: str, scientific_execution_authorization_identity: str
) -> dict:
    return schema.build_scientific_logical_record(
        record_kind=AUTHORITY_CONSUMED,
        sequence_number=0,
        execution_identity=execution_identity,
        scientific_execution_authorization_identity=(
            scientific_execution_authorization_identity
        ),
        predecessor_logical_record_sha256=(
            schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        ),
        payload={},
    )


def build_authority_consumption_failure_logical_record(
    *, execution_identity: str, scientific_execution_authorization_identity: str
) -> dict:
    return schema.build_scientific_logical_record(
        record_kind="SCIENTIFIC_TERMINAL_STATUS",
        sequence_number=0,
        execution_identity=execution_identity,
        scientific_execution_authorization_identity=(
            scientific_execution_authorization_identity
        ),
        predecessor_logical_record_sha256=(
            schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        ),
        payload={
            "terminal_classification": (
                AUTHORITY_CLOSED_UNEXERCISED_AFTER_CONSUMPTION_RECORD_FAILURE
            ),
            "exit_code": AUTHORITY_FAILURE_EXIT_CODE,
        },
    )


def build_stored_authority_consumed_record(
    *,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
    writer_attempt_identity: str,
) -> dict:
    return schema.build_stored_record_object(
        logical_record=build_authority_consumed_logical_record(
            execution_identity=execution_identity,
            scientific_execution_authorization_identity=(
                scientific_execution_authorization_identity
            ),
        ),
        writer_identity=primary_writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=writer_attempt_identity,
    )


def build_stored_authority_consumption_failure_record(
    *,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
    writer_attempt_identity: str,
) -> dict:
    return schema.build_stored_record_object(
        logical_record=build_authority_consumption_failure_logical_record(
            execution_identity=execution_identity,
            scientific_execution_authorization_identity=(
                scientific_execution_authorization_identity
            ),
        ),
        writer_identity=primary_writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=writer_attempt_identity,
    )


def write_authority_consumed_record(
    directory_path: str | Path,
    *,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
    writer_attempt_identity: str,
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None = None,
) -> AuthorityWriteEvidence:
    stored_record = build_stored_authority_consumed_record(
        execution_identity=execution_identity,
        scientific_execution_authorization_identity=(
            scientific_execution_authorization_identity
        ),
        writer_attempt_identity=writer_attempt_identity,
    )
    write_result = primary_writer.write_stored_record_object(
        directory_path,
        stored_record,
        durability_adapter=durability_adapter,
    )
    return AuthorityWriteEvidence(
        logical_record=stored_record["logical_record"],
        stored_record_object=stored_record,
        write_result=write_result,
    )


def write_authority_consumption_failure_record(
    directory_path: str | Path,
    *,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
    writer_attempt_identity: str,
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None = None,
) -> AuthorityWriteEvidence:
    stored_record = build_stored_authority_consumption_failure_record(
        execution_identity=execution_identity,
        scientific_execution_authorization_identity=(
            scientific_execution_authorization_identity
        ),
        writer_attempt_identity=writer_attempt_identity,
    )
    write_result = primary_writer.write_stored_record_object(
        directory_path,
        stored_record,
        durability_adapter=durability_adapter,
    )
    return AuthorityWriteEvidence(
        logical_record=stored_record["logical_record"],
        stored_record_object=stored_record,
        write_result=write_result,
    )


def replay_scientific_authority_state(
    chain_directory_path: str | Path,
    *,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
    durability_evidence: durability.VerifiedDurabilityEvidence | None = None,
    invocation_window_observed: bool = False,
) -> AuthorityReplayResult:
    if durability_evidence is None:
        durability_evidence = durability.VerifiedDurabilityEvidence.empty()
    if not isinstance(durability_evidence, durability.VerifiedDurabilityEvidence):
        raise AuthorityEvidenceError("VerifiedDurabilityEvidence is required")
    chain = replay.replay_chain(
        chain_directory_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=execution_identity,
        expected_authorization_identity=scientific_execution_authorization_identity,
    )
    if chain.rejected_objects:
        return _indeterminate(
            "authority evidence replay rejected an object",
            chain.classification,
        )
    if chain.classification not in (replay.VALID_LINEAR_CHAIN, replay.EMPTY_CHAIN):
        return _indeterminate(
            "authority evidence replay failed closed: %s" % chain.classification,
            chain.classification,
        )
    for instance in chain.accepted_instances:
        record = instance.logical_record
        if _is_authority_consumed_record(record):
            if durability_evidence.has_record_object(instance.stored_object_sha256):
                return AuthorityReplayResult(
                    state=CONSUMED,
                    scientific_state=AUTHORITY_CONSUMED,
                    reusable=False,
                    detail="durable AUTHORITY_CONSUMED genesis accepted",
                    replay_classification=chain.classification,
                    accepted_logical_record_sha256=record["logical_record_sha256"],
                    accepted_stored_object_sha256=instance.stored_object_sha256,
                )
            return _indeterminate(
                "AUTHORITY_CONSUMED bytes are valid but durability is unconfirmed",
                chain.classification,
            )
        if _is_authority_consumption_failure_record(record):
            if durability_evidence.has_record_object(instance.stored_object_sha256):
                return AuthorityReplayResult(
                    state=ATTEMPT_FAILED,
                    scientific_state=AUTHORITY_CONSUMPTION_ATTEMPT_FAILED,
                    reusable=False,
                    detail="durable authority-consumption failure evidence accepted",
                    replay_classification=chain.classification,
                    accepted_logical_record_sha256=record["logical_record_sha256"],
                    accepted_stored_object_sha256=instance.stored_object_sha256,
                )
            return _indeterminate(
                "authority-consumption failure bytes are valid but durability is unconfirmed",
                chain.classification,
            )
    if invocation_window_observed:
        return _indeterminate(
            "invocation window was observed but no durable authority state was proven",
            chain.classification,
        )
    if chain.accepted_instances:
        return _indeterminate(
            "scientific chain contains no valid authority-state evidence",
            chain.classification,
        )
    return AuthorityReplayResult(
        state=NOT_ATTEMPTED,
        scientific_state=AUTHORITY_NOT_ATTEMPTED,
        reusable=True,
        detail="live-only pre-begin state; no post-event reuse proof",
        replay_classification=chain.classification,
    )


def _is_authority_consumed_record(record: dict) -> bool:
    return (
        record["record_kind"] == AUTHORITY_CONSUMED
        and record["sequence_number"] == 0
        and record["predecessor_logical_record_sha256"]
        == schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        and record["payload"] == {}
    )


def _is_authority_consumption_failure_record(record: dict) -> bool:
    payload = record["payload"]
    return (
        record["record_kind"] == "SCIENTIFIC_TERMINAL_STATUS"
        and record["sequence_number"] == 0
        and record["predecessor_logical_record_sha256"]
        == schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        and tuple(payload.keys()) == ("terminal_classification", "exit_code")
        and payload["terminal_classification"]
        == AUTHORITY_CLOSED_UNEXERCISED_AFTER_CONSUMPTION_RECORD_FAILURE
        and payload["exit_code"] == AUTHORITY_FAILURE_EXIT_CODE
    )


def _indeterminate(detail: str, replay_classification: str) -> AuthorityReplayResult:
    return AuthorityReplayResult(
        state=ATTEMPT_STATE_INDETERMINATE,
        scientific_state=AUTHORITY_ATTEMPT_STATE_INDETERMINATE,
        reusable=False,
        detail=detail,
        replay_classification=replay_classification,
    )


def _validate_hex64(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise AuthorityEvidenceError("%s must be lowercase 64-hex" % label)
    if any(char not in "0123456789abcdef" for char in value):
        raise AuthorityEvidenceError("%s must be lowercase 64-hex" % label)
