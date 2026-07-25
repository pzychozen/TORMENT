from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import durable_evidence_durability_v0_3 as durability
import durable_evidence_replay_v0_3 as replay
import durable_evidence_schema_v0_3 as schema


PUBLICATION_RECOVERY_EVIDENCE_COMPLETED = "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED"
PUBLICATION_RECOVERY_INCOMPLETE = "PUBLICATION_RECOVERY_INCOMPLETE"
PUBLICATION_RECOVERY_CHAIN_FORK = "PUBLICATION_RECOVERY_CHAIN_FORK"
PUBLICATION_RECOVERY_CHAIN_REPLAY_FAILED = "PUBLICATION_RECOVERY_CHAIN_REPLAY_FAILED"
PUBLICATION_RECOVERY_CHAIN_DURABILITY_UNCONFIRMED = (
    "PUBLICATION_RECOVERY_CHAIN_DURABILITY_UNCONFIRMED"
)
PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID = (
    "PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID"
)
PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH = (
    "PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH"
)
PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY = (
    "PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY"
)

PUBLICATION_RECOVERY_AUTHORITY_NOT_ATTEMPTED = (
    "PUBLICATION_RECOVERY_AUTHORITY_NOT_ATTEMPTED"
)
PUBLICATION_RECOVERY_AUTHORITY_CONSUMED = "PUBLICATION_RECOVERY_AUTHORITY_CONSUMED"
PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE = (
    "PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE"
)

_RECOVERY_AUTHORITY_PAYLOAD_KEYS = (
    "execution_identity",
    "scientific_execution_authorization_identity",
    "bundle_payload_sha256",
    "scientific_completion_logical_record_sha256",
    "original_publication_projection_authorization_identity",
    "original_publication_projection_identity",
    "original_publication_chain_identity",
    "publication_recovery_authorization_identity",
    "publication_recovery_chain_identity",
    "expected_final_artifacts",
    "final_publication_directory",
    "publication_recovery_utility_identity",
)
_RECOVERY_ATTEMPTED_PAYLOAD_KEYS = (
    "original_publication_chain_identity",
    "publication_recovery_chain_identity",
)
_RECOVERY_ARTIFACTS_VERIFIED_PAYLOAD_KEYS = (
    "original_publication_chain_identity",
    "final_publication_directory",
    "verified_final_artifacts",
    "artifact_source",
)
_RECOVERY_EVIDENCE_COMPLETED_PAYLOAD_KEYS = (
    "original_publication_chain_identity",
    "publication_recovery_chain_identity",
    "recovery_semantics",
)
_RECOVERY_TERMINAL_PAYLOAD_KEYS = ("terminal_classification",)


class PublicationRecoveryReplayError(ValueError):
    pass


@dataclass(frozen=True)
class PublicationRecoveryReplayResult:
    classification: str
    detail: str
    replay_classification: str
    accepted_records: tuple[dict[str, Any], ...] = ()
    verified_artifact_sha256s: dict[str, str] | None = None
    original_publication_chain_identity: str | None = None
    publication_recovery_chain_identity: str | None = None
    original_publication_completed_normally: bool = False


@dataclass(frozen=True)
class PublicationRecoveryAuthorityReplayResult:
    state: str
    reusable: bool
    detail: str
    replay_classification: str
    accepted_logical_record_sha256: str | None = None
    accepted_stored_object_sha256: str | None = None


def replay_publication_recovery_chain(
    chain_directory_path: str | Path,
    *,
    expected_execution_identity: str,
    publication_recovery_authorization_identity: str,
    publication_recovery_chain_identity: str,
    original_publication_chain_identity: str,
    expected_final_artifact_sha256s: Mapping[str, str] | None = None,
    durability_evidence: durability.VerifiedDurabilityEvidence | None = None,
) -> PublicationRecoveryReplayResult:
    evidence = _require_durability_evidence(durability_evidence)
    chain = replay.replay_chain(
        chain_directory_path,
        expected_record_schema_identity=schema.PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=expected_execution_identity,
        expected_authorization_identity=publication_recovery_authorization_identity,
        expected_chain_identity=publication_recovery_chain_identity,
    )
    if chain.rejected_objects:
        return PublicationRecoveryReplayResult(
            classification=PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
            detail="recovery replay rejected foreign or malformed evidence",
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
        )
    if chain.classification == replay.LOGICAL_FORK:
        return PublicationRecoveryReplayResult(
            classification=PUBLICATION_RECOVERY_CHAIN_FORK,
            detail="publication recovery chain fork",
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
        )
    if chain.classification not in (replay.VALID_LINEAR_CHAIN, replay.EMPTY_CHAIN):
        return PublicationRecoveryReplayResult(
            classification=PUBLICATION_RECOVERY_CHAIN_REPLAY_FAILED,
            detail="recovery replay failed closed: %s" % chain.classification,
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
        )
    if not chain.accepted_instances:
        return PublicationRecoveryReplayResult(
            classification=PUBLICATION_RECOVERY_INCOMPLETE,
            detail="no recovery evidence",
            replay_classification=chain.classification,
        )
    transition_error = _validate_transition_shape(
        chain.accepted_records,
        original_publication_chain_identity=original_publication_chain_identity,
        publication_recovery_chain_identity=publication_recovery_chain_identity,
        expected_final_artifact_sha256s=expected_final_artifact_sha256s,
    )
    if transition_error is not None:
        return PublicationRecoveryReplayResult(
            classification=transition_error[0],
            detail=transition_error[1],
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
        )
    completed_index = _completed_index(chain.accepted_records)
    if completed_index is None:
        return PublicationRecoveryReplayResult(
            classification=PUBLICATION_RECOVERY_INCOMPLETE,
            detail="PUBLICATION_RECOVERY_EVIDENCE_COMPLETED is absent",
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
            original_publication_chain_identity=original_publication_chain_identity,
            publication_recovery_chain_identity=publication_recovery_chain_identity,
        )
    for instance in chain.accepted_instances[: completed_index + 1]:
        if not evidence.has_record_object(
            instance.stored_object_sha256,
            directory_durability_policy_identity=(
                schema.directory_durability_policy_identity()
            ),
        ):
            return PublicationRecoveryReplayResult(
                classification=PUBLICATION_RECOVERY_CHAIN_DURABILITY_UNCONFIRMED,
                detail="publication recovery record durability is unconfirmed",
                replay_classification=chain.classification,
                accepted_records=chain.accepted_records,
                original_publication_chain_identity=original_publication_chain_identity,
                publication_recovery_chain_identity=publication_recovery_chain_identity,
            )
    if len(chain.accepted_instances) > completed_index + 1:
        terminal = chain.accepted_instances[completed_index + 1]
        if not evidence.has_record_object(
            terminal.stored_object_sha256,
            directory_durability_policy_identity=(
                schema.directory_durability_policy_identity()
            ),
        ):
            return PublicationRecoveryReplayResult(
                classification=PUBLICATION_RECOVERY_CHAIN_DURABILITY_UNCONFIRMED,
                detail="publication recovery terminal durability is unconfirmed",
                replay_classification=chain.classification,
                accepted_records=chain.accepted_records,
            )
    verified = chain.accepted_records[2]["payload"]["verified_final_artifacts"]
    return PublicationRecoveryReplayResult(
        classification=PUBLICATION_RECOVERY_EVIDENCE_COMPLETED,
        detail="durable recovery evidence completed",
        replay_classification=chain.classification,
        accepted_records=chain.accepted_records,
        verified_artifact_sha256s=dict(verified),
        original_publication_chain_identity=original_publication_chain_identity,
        publication_recovery_chain_identity=publication_recovery_chain_identity,
        original_publication_completed_normally=False,
    )


def replay_publication_recovery_authority_state(
    chain_directory_path: str | Path,
    *,
    expected_execution_identity: str,
    publication_recovery_authorization_identity: str,
    publication_recovery_chain_identity: str,
    durability_evidence: durability.VerifiedDurabilityEvidence | None = None,
    invocation_window_observed: bool = False,
) -> PublicationRecoveryAuthorityReplayResult:
    evidence = _require_durability_evidence(durability_evidence)
    chain = replay.replay_chain(
        chain_directory_path,
        expected_record_schema_identity=schema.PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=expected_execution_identity,
        expected_authorization_identity=publication_recovery_authorization_identity,
        expected_chain_identity=publication_recovery_chain_identity,
    )
    if chain.rejected_objects or chain.classification not in (
        replay.VALID_LINEAR_CHAIN,
        replay.EMPTY_CHAIN,
    ):
        return _authority_indeterminate(
            "publication recovery authority replay failed closed",
            chain.classification,
        )
    if chain.accepted_instances:
        first = chain.accepted_instances[0]
        record = first.logical_record
        if (
            record["record_kind"] == "PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED"
            and record["sequence_number"] == 0
            and record["predecessor_logical_record_sha256"]
            == schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        ):
            if evidence.has_record_object(
                first.stored_object_sha256,
                directory_durability_policy_identity=(
                    schema.directory_durability_policy_identity()
                ),
            ):
                return PublicationRecoveryAuthorityReplayResult(
                    state=PUBLICATION_RECOVERY_AUTHORITY_CONSUMED,
                    reusable=False,
                    detail=(
                        "durable PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED accepted"
                    ),
                    replay_classification=chain.classification,
                    accepted_logical_record_sha256=record["logical_record_sha256"],
                    accepted_stored_object_sha256=first.stored_object_sha256,
                )
            return _authority_indeterminate(
                "recovery authority bytes are valid but durability is unconfirmed",
                chain.classification,
            )
        return _authority_indeterminate(
            "recovery chain does not begin with authority acceptance",
            chain.classification,
        )
    if invocation_window_observed:
        return _authority_indeterminate(
            "recovery invocation window observed without durable genesis",
            chain.classification,
        )
    return PublicationRecoveryAuthorityReplayResult(
        state=PUBLICATION_RECOVERY_AUTHORITY_NOT_ATTEMPTED,
        reusable=True,
        detail="live-only pre-begin state",
        replay_classification=chain.classification,
    )


def _validate_transition_shape(
    records: tuple[dict[str, Any], ...],
    *,
    original_publication_chain_identity: str,
    publication_recovery_chain_identity: str,
    expected_final_artifact_sha256s: Mapping[str, str] | None,
) -> tuple[str, str] | None:
    required_kinds = (
        "PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED",
        "PUBLICATION_RECOVERY_ATTEMPTED",
        "PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED",
        "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED",
    )
    if len(records) < 2:
        return (
            PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
            "recovery chain is missing required attempted prefix",
        )
    for index, record in enumerate(records[: min(len(records), len(required_kinds))]):
        expected_predecessor = schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        if index > 0:
            expected_predecessor = records[index - 1]["logical_record_sha256"]
        if record["predecessor_logical_record_sha256"] != expected_predecessor:
            return (
                PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
                "recovery predecessor mismatch at sequence %d" % index,
            )
        if record["sequence_number"] != index:
            return (
                PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
                "recovery sequence mismatch at sequence %d" % index,
            )
        if record["record_kind"] != required_kinds[index]:
            return (
                PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
                "recovery transition mismatch at sequence %d" % index,
            )
    genesis_error = _validate_genesis_payload(
        records[0]["payload"],
        original_publication_chain_identity=original_publication_chain_identity,
        publication_recovery_chain_identity=publication_recovery_chain_identity,
        expected_final_artifact_sha256s=expected_final_artifact_sha256s,
    )
    if genesis_error is not None:
        return genesis_error
    attempted_payload = records[1]["payload"]
    if tuple(attempted_payload.keys()) != _RECOVERY_ATTEMPTED_PAYLOAD_KEYS:
        return (
            PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
            "recovery attempted payload shape mismatch",
        )
    if attempted_payload["original_publication_chain_identity"] != (
        original_publication_chain_identity
    ):
        return (
            PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH,
            "recovery attempted original-chain mismatch",
        )
    if attempted_payload["publication_recovery_chain_identity"] != (
        publication_recovery_chain_identity
    ):
        return (
            PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
            "recovery attempted chain mismatch",
        )
    if len(records) == 2:
        return None
    artifacts_payload = records[2]["payload"]
    if tuple(artifacts_payload.keys()) != _RECOVERY_ARTIFACTS_VERIFIED_PAYLOAD_KEYS:
        return (
            PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
            "recovery artifacts payload shape mismatch",
        )
    if artifacts_payload["original_publication_chain_identity"] != (
        original_publication_chain_identity
    ):
        return (
            PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH,
            "recovery artifacts original-chain mismatch",
        )
    if artifacts_payload["artifact_source"] != (
        "already_existing_final_publication_directory"
    ):
        return (
            PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
            "recovery artifact source mismatch",
        )
    try:
        schema.validate_publication_artifact_sha256s(
            artifacts_payload["verified_final_artifacts"]
        )
    except schema.EvidenceValidationError as exc:
        return (PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID, str(exc))
    if expected_final_artifact_sha256s is not None:
        schema.validate_publication_artifact_sha256s(expected_final_artifact_sha256s)
        if artifacts_payload["verified_final_artifacts"] != dict(
            expected_final_artifact_sha256s
        ):
            return (
                PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
                "recovery verified artifact hash mismatch",
            )
    if len(records) == 3:
        return None
    completed_payload = records[3]["payload"]
    if tuple(completed_payload.keys()) != _RECOVERY_EVIDENCE_COMPLETED_PAYLOAD_KEYS:
        return (
            PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
            "recovery completed payload shape mismatch",
        )
    if completed_payload["original_publication_chain_identity"] != (
        original_publication_chain_identity
    ):
        return (
            PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH,
            "recovery completed original-chain mismatch",
        )
    if completed_payload["publication_recovery_chain_identity"] != (
        publication_recovery_chain_identity
    ):
        return (
            PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
            "recovery completed chain mismatch",
        )
    if completed_payload["recovery_semantics"] != (
        "final_artifacts_verified_under_separate_recovery_evidence_only"
    ):
        return (
            PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
            "recovery semantics mismatch",
        )
    if len(records) > 4:
        terminal = records[4]
        if terminal["record_kind"] != "PUBLICATION_RECOVERY_TERMINAL_STATUS":
            return (
                PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
                "unexpected recovery evidence after evidence completion",
            )
        if terminal["sequence_number"] != 4:
            return (
                PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
                "recovery terminal sequence mismatch",
            )
        if (
            terminal["predecessor_logical_record_sha256"]
            != records[3]["logical_record_sha256"]
        ):
            return (
                PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
                "recovery terminal predecessor mismatch",
            )
        if tuple(terminal["payload"].keys()) != _RECOVERY_TERMINAL_PAYLOAD_KEYS:
            return (
                PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
                "recovery terminal payload shape mismatch",
            )
        if len(records) > 5:
            return (
                PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
                "recovery evidence appears after terminal status",
            )
    return None


def _validate_genesis_payload(
    payload: Mapping[str, Any],
    *,
    original_publication_chain_identity: str,
    publication_recovery_chain_identity: str,
    expected_final_artifact_sha256s: Mapping[str, str] | None,
) -> tuple[str, str] | None:
    if tuple(payload.keys()) != _RECOVERY_AUTHORITY_PAYLOAD_KEYS:
        return (
            PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID,
            "recovery genesis payload shape mismatch",
        )
    if payload["original_publication_chain_identity"] != (
        original_publication_chain_identity
    ):
        return (
            PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH,
            "recovery genesis original-chain mismatch",
        )
    if payload["publication_recovery_chain_identity"] != (
        publication_recovery_chain_identity
    ):
        return (
            PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
            "recovery genesis chain mismatch",
        )
    try:
        schema.validate_publication_artifact_sha256s(
            payload["expected_final_artifacts"]
        )
    except schema.EvidenceValidationError as exc:
        return (PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID, str(exc))
    if expected_final_artifact_sha256s is not None:
        schema.validate_publication_artifact_sha256s(expected_final_artifact_sha256s)
        if payload["expected_final_artifacts"] != dict(expected_final_artifact_sha256s):
            return (
                PUBLICATION_RECOVERY_EVIDENCE_CONTRADICTORY,
                "recovery expected artifact hash mismatch",
            )
    return None


def _completed_index(records: tuple[dict[str, Any], ...]) -> int | None:
    for index, record in enumerate(records):
        if record["record_kind"] == "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED":
            return index
    return None


def _authority_indeterminate(
    detail: str, replay_classification: str
) -> PublicationRecoveryAuthorityReplayResult:
    return PublicationRecoveryAuthorityReplayResult(
        state=PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE,
        reusable=False,
        detail=detail,
        replay_classification=replay_classification,
    )


def _require_durability_evidence(
    durability_evidence: durability.VerifiedDurabilityEvidence | None,
) -> durability.VerifiedDurabilityEvidence:
    if durability_evidence is None:
        return durability.VerifiedDurabilityEvidence.empty()
    if not isinstance(durability_evidence, durability.VerifiedDurabilityEvidence):
        raise PublicationRecoveryReplayError("VerifiedDurabilityEvidence is required")
    return durability_evidence
