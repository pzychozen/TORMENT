from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import durable_evidence_durability_v0_3 as durability
import durable_evidence_replay_v0_3 as replay
import durable_evidence_schema_v0_3 as schema


PUBLICATION_COMPLETED = "PUBLICATION_COMPLETED"
PUBLICATION_INCOMPLETE = "PUBLICATION_INCOMPLETE"
PUBLICATION_CHAIN_FORK = "PUBLICATION_CHAIN_FORK"
PUBLICATION_CHAIN_REPLAY_FAILED = "PUBLICATION_CHAIN_REPLAY_FAILED"
PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED = (
    "PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED"
)
PUBLICATION_TRANSITION_ORDER_INVALID = "PUBLICATION_TRANSITION_ORDER_INVALID"
PUBLICATION_EVIDENCE_CONTRADICTORY = "PUBLICATION_EVIDENCE_CONTRADICTORY"

PUBLICATION_AUTHORITY_NOT_ATTEMPTED = "PUBLICATION_AUTHORITY_NOT_ATTEMPTED"
PUBLICATION_AUTHORITY_CONSUMED = "PUBLICATION_AUTHORITY_CONSUMED"
PUBLICATION_AUTHORITY_ATTEMPT_STATE_INDETERMINATE = (
    "PUBLICATION_AUTHORITY_ATTEMPT_STATE_INDETERMINATE"
)

_AUTHORITY_PAYLOAD_KEYS = (
    "execution_identity",
    "scientific_execution_authorization_identity",
    "bundle_payload_sha256",
    "scientific_completion_logical_record_sha256",
    "publication_projection_authorization_identity",
    "publication_projection_identity",
    "publication_chain_identity",
    "publication_recipe_identity",
    "publication_utility_identities",
    "expected_artifact_filenames",
)
_ATTEMPTED_PAYLOAD_KEYS = (
    "publication_projection_identity",
    "publication_chain_identity",
    "artifact_filenames",
)
_COMPLETED_PAYLOAD_KEYS = (
    "publication_projection_identity",
    "publication_chain_identity",
    "artifact_sha256s",
)
_TERMINAL_PAYLOAD_KEYS = ("terminal_classification",)


class PublicationReplayError(ValueError):
    pass


@dataclass(frozen=True)
class PublicationReplayResult:
    classification: str
    detail: str
    replay_classification: str
    accepted_records: tuple[dict[str, Any], ...] = ()
    artifact_sha256s: dict[str, str] | None = None
    publication_projection_identity: str | None = None
    publication_chain_identity: str | None = None


@dataclass(frozen=True)
class PublicationAuthorityReplayResult:
    state: str
    reusable: bool
    detail: str
    replay_classification: str
    accepted_logical_record_sha256: str | None = None
    accepted_stored_object_sha256: str | None = None


def replay_publication_chain(
    chain_directory_path: str | Path,
    *,
    expected_execution_identity: str,
    publication_projection_authorization_identity: str,
    publication_chain_identity: str,
    publication_projection_identity: str | None = None,
    bundle_payload_sha256: str | None = None,
    scientific_completion_logical_record_sha256: str | None = None,
    expected_artifact_sha256s: Mapping[str, str] | None = None,
    durability_evidence: durability.VerifiedDurabilityEvidence | None = None,
) -> PublicationReplayResult:
    evidence = _require_durability_evidence(durability_evidence)
    chain = replay.replay_chain(
        chain_directory_path,
        expected_record_schema_identity=schema.PUBLICATION_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=expected_execution_identity,
        expected_authorization_identity=publication_projection_authorization_identity,
        expected_chain_identity=publication_chain_identity,
    )
    if chain.rejected_objects:
        return PublicationReplayResult(
            classification=PUBLICATION_EVIDENCE_CONTRADICTORY,
            detail="publication replay rejected foreign or malformed evidence",
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
        )
    if chain.classification == replay.LOGICAL_FORK:
        return PublicationReplayResult(
            classification=PUBLICATION_CHAIN_FORK,
            detail="publication chain fork",
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
        )
    if chain.classification not in (replay.VALID_LINEAR_CHAIN, replay.EMPTY_CHAIN):
        return PublicationReplayResult(
            classification=PUBLICATION_CHAIN_REPLAY_FAILED,
            detail="publication replay failed closed: %s" % chain.classification,
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
        )
    if not chain.accepted_instances:
        return PublicationReplayResult(
            classification=PUBLICATION_INCOMPLETE,
            detail="no publication evidence",
            replay_classification=chain.classification,
        )
    transition_error = _validate_transition_shape(
        chain.accepted_records,
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_chain_identity=publication_chain_identity,
        publication_projection_identity=publication_projection_identity,
        bundle_payload_sha256=bundle_payload_sha256,
        scientific_completion_logical_record_sha256=(
            scientific_completion_logical_record_sha256
        ),
        expected_artifact_sha256s=expected_artifact_sha256s,
    )
    if transition_error is not None:
        return PublicationReplayResult(
            classification=transition_error[0],
            detail=transition_error[1],
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
        )
    completed_index = _completed_index(chain.accepted_records)
    if completed_index is None:
        return PublicationReplayResult(
            classification=PUBLICATION_INCOMPLETE,
            detail="PUBLICATION_COMPLETED is absent",
            replay_classification=chain.classification,
            accepted_records=chain.accepted_records,
            publication_projection_identity=_projection_identity(chain.accepted_records),
            publication_chain_identity=publication_chain_identity,
        )
    for instance in chain.accepted_instances[: completed_index + 1]:
        if not evidence.has_record_object(
            instance.stored_object_sha256,
            directory_durability_policy_identity=(
                schema.directory_durability_policy_identity()
            ),
        ):
            return PublicationReplayResult(
                classification=PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED,
                detail="publication record durability is unconfirmed",
                replay_classification=chain.classification,
                accepted_records=chain.accepted_records,
                publication_projection_identity=_projection_identity(
                    chain.accepted_records
                ),
                publication_chain_identity=publication_chain_identity,
            )
    if len(chain.accepted_instances) > completed_index + 1:
        terminal_instance = chain.accepted_instances[completed_index + 1]
        if not evidence.has_record_object(
            terminal_instance.stored_object_sha256,
            directory_durability_policy_identity=(
                schema.directory_durability_policy_identity()
            ),
        ):
            return PublicationReplayResult(
                classification=PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED,
                detail="publication terminal durability is unconfirmed",
                replay_classification=chain.classification,
                accepted_records=chain.accepted_records,
            )
    completed_payload = chain.accepted_records[completed_index]["payload"]
    artifact_sha256s = dict(completed_payload["artifact_sha256s"])
    return PublicationReplayResult(
        classification=PUBLICATION_COMPLETED,
        detail="durable publication chain completed",
        replay_classification=chain.classification,
        accepted_records=chain.accepted_records,
        artifact_sha256s=artifact_sha256s,
        publication_projection_identity=completed_payload[
            "publication_projection_identity"
        ],
        publication_chain_identity=publication_chain_identity,
    )


def replay_publication_authority_state(
    chain_directory_path: str | Path,
    *,
    expected_execution_identity: str,
    publication_projection_authorization_identity: str,
    publication_chain_identity: str,
    durability_evidence: durability.VerifiedDurabilityEvidence | None = None,
    invocation_window_observed: bool = False,
) -> PublicationAuthorityReplayResult:
    evidence = _require_durability_evidence(durability_evidence)
    chain = replay.replay_chain(
        chain_directory_path,
        expected_record_schema_identity=schema.PUBLICATION_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=expected_execution_identity,
        expected_authorization_identity=publication_projection_authorization_identity,
        expected_chain_identity=publication_chain_identity,
    )
    if chain.rejected_objects or chain.classification not in (
        replay.VALID_LINEAR_CHAIN,
        replay.EMPTY_CHAIN,
    ):
        return _authority_indeterminate(
            "publication authority replay failed closed",
            chain.classification,
        )
    if chain.accepted_instances:
        first = chain.accepted_instances[0]
        record = first.logical_record
        if (
            record["record_kind"] == "PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED"
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
                return PublicationAuthorityReplayResult(
                    state=PUBLICATION_AUTHORITY_CONSUMED,
                    reusable=False,
                    detail=(
                        "durable PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED accepted"
                    ),
                    replay_classification=chain.classification,
                    accepted_logical_record_sha256=record["logical_record_sha256"],
                    accepted_stored_object_sha256=first.stored_object_sha256,
                )
            return _authority_indeterminate(
                "publication authority bytes are valid but durability is unconfirmed",
                chain.classification,
            )
        return _authority_indeterminate(
            "publication chain does not begin with authority acceptance",
            chain.classification,
        )
    if invocation_window_observed:
        return _authority_indeterminate(
            "publication invocation window observed without durable genesis",
            chain.classification,
        )
    return PublicationAuthorityReplayResult(
        state=PUBLICATION_AUTHORITY_NOT_ATTEMPTED,
        reusable=True,
        detail="live-only pre-begin state",
        replay_classification=chain.classification,
    )


def _validate_transition_shape(
    records: tuple[dict[str, Any], ...],
    *,
    publication_projection_authorization_identity: str,
    publication_chain_identity: str,
    publication_projection_identity: str | None,
    bundle_payload_sha256: str | None,
    scientific_completion_logical_record_sha256: str | None,
    expected_artifact_sha256s: Mapping[str, str] | None,
) -> tuple[str, str] | None:
    required = (
        "PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED",
        "PUBLICATION_ATTEMPTED",
    )
    if len(records) < len(required):
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "publication chain is missing required prefix",
        )
    for index, kind in enumerate(required):
        record = records[index]
        if record["record_kind"] != kind or record["sequence_number"] != index:
            return (
                PUBLICATION_TRANSITION_ORDER_INVALID,
                "publication transition mismatch at sequence %d" % index,
            )
        expected_predecessor = schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        if index > 0:
            expected_predecessor = records[index - 1]["logical_record_sha256"]
        if record["predecessor_logical_record_sha256"] != expected_predecessor:
            return (
                PUBLICATION_TRANSITION_ORDER_INVALID,
                "publication predecessor mismatch at sequence %d" % index,
            )
    genesis_error = _validate_genesis_payload(
        records[0]["payload"],
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_chain_identity=publication_chain_identity,
        publication_projection_identity=publication_projection_identity,
        bundle_payload_sha256=bundle_payload_sha256,
        scientific_completion_logical_record_sha256=(
            scientific_completion_logical_record_sha256
        ),
    )
    if genesis_error is not None:
        return genesis_error
    attempted_payload = records[1]["payload"]
    if tuple(attempted_payload.keys()) != _ATTEMPTED_PAYLOAD_KEYS:
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "PUBLICATION_ATTEMPTED payload shape mismatch",
        )
    if attempted_payload["publication_chain_identity"] != publication_chain_identity:
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "attempted publication chain identity mismatch",
        )
    if publication_projection_identity is not None and (
        attempted_payload["publication_projection_identity"]
        != publication_projection_identity
    ):
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "attempted publication projection identity mismatch",
        )
    if tuple(attempted_payload["artifact_filenames"]) != (
        schema.PUBLICATION_ARTIFACT_FILENAMES
    ):
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "attempted artifact filename list mismatch",
        )
    if len(records) == 2:
        return None
    completed = records[2]
    if completed["record_kind"] != "PUBLICATION_COMPLETED":
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "sequence 2 is not PUBLICATION_COMPLETED",
        )
    if completed["sequence_number"] != 2:
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "PUBLICATION_COMPLETED sequence mismatch",
        )
    if (
        completed["predecessor_logical_record_sha256"]
        != records[1]["logical_record_sha256"]
    ):
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "PUBLICATION_COMPLETED predecessor mismatch",
        )
    completion_payload = completed["payload"]
    if tuple(completion_payload.keys()) != _COMPLETED_PAYLOAD_KEYS:
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "PUBLICATION_COMPLETED payload shape mismatch",
        )
    if completion_payload["publication_chain_identity"] != publication_chain_identity:
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "completed publication chain identity mismatch",
        )
    if publication_projection_identity is not None and (
        completion_payload["publication_projection_identity"]
        != publication_projection_identity
    ):
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "completed publication projection identity mismatch",
        )
    try:
        schema.validate_publication_artifact_sha256s(
            completion_payload["artifact_sha256s"]
        )
    except schema.EvidenceValidationError as exc:
        return (PUBLICATION_TRANSITION_ORDER_INVALID, str(exc))
    if expected_artifact_sha256s is not None:
        try:
            schema.validate_publication_artifact_sha256s(expected_artifact_sha256s)
        except schema.EvidenceValidationError as exc:
            return (PUBLICATION_TRANSITION_ORDER_INVALID, str(exc))
        if completion_payload["artifact_sha256s"] != dict(expected_artifact_sha256s):
            return (
                PUBLICATION_EVIDENCE_CONTRADICTORY,
                "completed artifact SHA-256 declaration mismatch",
            )
    if len(records) > 3:
        terminal = records[3]
        if terminal["record_kind"] != "PUBLICATION_TERMINAL_STATUS":
            return (
                PUBLICATION_EVIDENCE_CONTRADICTORY,
                "unexpected publication evidence after completion",
            )
        if terminal["sequence_number"] != 3:
            return (
                PUBLICATION_TRANSITION_ORDER_INVALID,
                "publication terminal sequence mismatch",
            )
        if (
            terminal["predecessor_logical_record_sha256"]
            != completed["logical_record_sha256"]
        ):
            return (
                PUBLICATION_TRANSITION_ORDER_INVALID,
                "publication terminal predecessor mismatch",
            )
        if tuple(terminal["payload"].keys()) != _TERMINAL_PAYLOAD_KEYS:
            return (
                PUBLICATION_TRANSITION_ORDER_INVALID,
                "publication terminal payload shape mismatch",
            )
        if len(records) > 4:
            return (
                PUBLICATION_EVIDENCE_CONTRADICTORY,
                "publication evidence appears after terminal status",
            )
    return None


def _validate_genesis_payload(
    payload: Mapping[str, Any],
    *,
    publication_projection_authorization_identity: str,
    publication_chain_identity: str,
    publication_projection_identity: str | None,
    bundle_payload_sha256: str | None,
    scientific_completion_logical_record_sha256: str | None,
) -> tuple[str, str] | None:
    if tuple(payload.keys()) != _AUTHORITY_PAYLOAD_KEYS:
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "publication authority payload shape mismatch",
        )
    if (
        payload["publication_projection_authorization_identity"]
        != publication_projection_authorization_identity
    ):
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "publication authorization identity mismatch",
        )
    if payload["publication_chain_identity"] != publication_chain_identity:
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "publication chain identity mismatch",
        )
    if publication_projection_identity is not None and (
        payload["publication_projection_identity"] != publication_projection_identity
    ):
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "publication projection identity mismatch",
        )
    if bundle_payload_sha256 is not None and (
        payload["bundle_payload_sha256"] != bundle_payload_sha256
    ):
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "bundle payload identity mismatch",
        )
    if scientific_completion_logical_record_sha256 is not None and (
        payload["scientific_completion_logical_record_sha256"]
        != scientific_completion_logical_record_sha256
    ):
        return (
            PUBLICATION_EVIDENCE_CONTRADICTORY,
            "scientific completion identity mismatch",
        )
    if tuple(payload["expected_artifact_filenames"]) != (
        schema.PUBLICATION_ARTIFACT_FILENAMES
    ):
        return (
            PUBLICATION_TRANSITION_ORDER_INVALID,
            "publication artifact filename declaration mismatch",
        )
    return None


def _completed_index(records: tuple[dict[str, Any], ...]) -> int | None:
    for index, record in enumerate(records):
        if record["record_kind"] == "PUBLICATION_COMPLETED":
            return index
    return None


def _projection_identity(records: tuple[dict[str, Any], ...]) -> str | None:
    if not records:
        return None
    payload = records[0]["payload"]
    if "publication_projection_identity" not in payload:
        return None
    return payload["publication_projection_identity"]


def _authority_indeterminate(
    detail: str, replay_classification: str
) -> PublicationAuthorityReplayResult:
    return PublicationAuthorityReplayResult(
        state=PUBLICATION_AUTHORITY_ATTEMPT_STATE_INDETERMINATE,
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
        raise PublicationReplayError("VerifiedDurabilityEvidence is required")
    return durability_evidence
