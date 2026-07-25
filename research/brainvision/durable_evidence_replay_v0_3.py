from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os

import durable_evidence_schema_v0_3 as schema


VALID_LINEAR_CHAIN = "VALID_LINEAR_CHAIN"
EMPTY_CHAIN = "EMPTY_CHAIN"
REDUNDANT_PHYSICAL_INSTANCES = "REDUNDANT_PHYSICAL_INSTANCES"
LOGICAL_FORK = "LOGICAL_FORK"
PREDECESSOR_MISMATCH = "PREDECESSOR_MISMATCH"
SEQUENCE_GAP = "SEQUENCE_GAP"
CROSS_CHAIN_OBJECT = "CROSS_CHAIN_OBJECT"
CROSS_IDENTITY_OBJECT = "CROSS_IDENTITY_OBJECT"
INVALID_CANONICAL_BYTES = "INVALID_CANONICAL_BYTES"
INVALID_PHYSICAL_OBJECT_IDENTITY = "INVALID_PHYSICAL_OBJECT_IDENTITY"


@dataclass(frozen=True)
class RejectedObject:
    path: str
    classification: str
    detail: str


@dataclass(frozen=True)
class StoredRecordInstance:
    path: str
    stored_object_sha256: str
    logical_record_sha256: str
    writer_attempt_identity: str
    logical_record: dict[str, Any]


@dataclass(frozen=True)
class RedundantPhysicalInstances:
    logical_record_sha256: str
    paths: tuple[str, ...]
    classification: str = REDUNDANT_PHYSICAL_INSTANCES


@dataclass(frozen=True)
class ReplayResult:
    classification: str
    accepted_records: tuple[dict[str, Any], ...]
    accepted_instances: tuple[StoredRecordInstance, ...]
    redundant_instances: tuple[RedundantPhysicalInstances, ...]
    rejected_objects: tuple[RejectedObject, ...]


def replay_chain(
    chain_directory_path: str | Path,
    *,
    expected_record_schema_identity: str,
    expected_execution_identity: str | None = None,
    expected_authorization_identity: str | None = None,
    expected_chain_identity: str | None = None,
) -> ReplayResult:
    candidates: list[StoredRecordInstance] = []
    rejected: list[RejectedObject] = []
    for path in sorted(Path(chain_directory_path).glob("*.json"), key=lambda item: item.name):
        try:
            raw = _read_bytes(path)
            stored_object = schema.load_canonical_json_bytes(
                raw, max_bytes=schema.MAX_STORED_RECORD_OBJECT_BYTES
            )
        except schema.EvidenceValidationError as exc:
            rejected.append(
                RejectedObject(str(path), INVALID_CANONICAL_BYTES, str(exc))
            )
            continue
        try:
            schema.validate_stored_record_object(stored_object)
        except schema.StoredObjectIdentityError as exc:
            rejected.append(
                RejectedObject(str(path), INVALID_PHYSICAL_OBJECT_IDENTITY, str(exc))
            )
            continue
        except schema.EvidenceValidationError as exc:
            rejected.append(
                RejectedObject(str(path), INVALID_PHYSICAL_OBJECT_IDENTITY, str(exc))
            )
            continue

        logical_record = stored_object["logical_record"]
        if logical_record["record_schema_identity"] != expected_record_schema_identity:
            rejected.append(
                RejectedObject(
                    str(path),
                    CROSS_CHAIN_OBJECT,
                    "record_schema_identity mismatch",
                )
            )
            continue
        if (
            expected_execution_identity is not None
            and logical_record["execution_identity"] != expected_execution_identity
        ):
            rejected.append(
                RejectedObject(str(path), CROSS_IDENTITY_OBJECT, "execution_identity mismatch")
            )
            continue
        if (
            expected_authorization_identity is not None
            and schema.record_authorization_identity(logical_record)
            != expected_authorization_identity
        ):
            rejected.append(
                RejectedObject(
                    str(path),
                    CROSS_IDENTITY_OBJECT,
                    "authorization identity mismatch",
                )
            )
            continue
        if (
            expected_chain_identity is not None
            and schema.record_chain_identity(logical_record) != expected_chain_identity
        ):
            rejected.append(
                RejectedObject(str(path), CROSS_IDENTITY_OBJECT, "chain identity mismatch")
            )
            continue
        candidates.append(
            StoredRecordInstance(
                path=str(path),
                stored_object_sha256=stored_object["stored_object_sha256"],
                logical_record_sha256=stored_object["logical_record_sha256"],
                writer_attempt_identity=stored_object["writer_attempt_identity"],
                logical_record=logical_record,
            )
        )

    chain_result = _replay_matching_candidates(candidates, rejected)
    if chain_result.classification in (VALID_LINEAR_CHAIN, EMPTY_CHAIN):
        fatal_rejection = _first_fatal_rejection(rejected)
        if fatal_rejection is not None:
            return ReplayResult(
                classification=fatal_rejection.classification,
                accepted_records=chain_result.accepted_records,
                accepted_instances=chain_result.accepted_instances,
                redundant_instances=chain_result.redundant_instances,
                rejected_objects=tuple(rejected),
            )
    return chain_result


def _replay_matching_candidates(
    candidates: list[StoredRecordInstance], rejected: list[RejectedObject]
) -> ReplayResult:
    remaining = list(candidates)
    accepted_instances: list[StoredRecordInstance] = []
    accepted_records: list[dict[str, Any]] = []
    redundant: list[RedundantPhysicalInstances] = []
    predecessor = schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
    sequence_number = 0

    while True:
        matching = [
            item
            for item in remaining
            if item.logical_record["sequence_number"] == sequence_number
            and item.logical_record["predecessor_logical_record_sha256"] == predecessor
        ]
        if not matching:
            classification = _missing_link_classification(
                remaining, sequence_number, predecessor, accepted_instances
            )
            return ReplayResult(
                classification=classification,
                accepted_records=tuple(accepted_records),
                accepted_instances=tuple(accepted_instances),
                redundant_instances=tuple(redundant),
                rejected_objects=tuple(rejected),
            )
        groups: dict[str, list[StoredRecordInstance]] = {}
        for item in matching:
            groups.setdefault(item.logical_record_sha256, []).append(item)
        if len(groups) > 1:
            return ReplayResult(
                classification=LOGICAL_FORK,
                accepted_records=tuple(accepted_records),
                accepted_instances=tuple(accepted_instances),
                redundant_instances=tuple(redundant),
                rejected_objects=tuple(rejected),
            )
        logical_hash = next(iter(groups))
        group = sorted(groups[logical_hash], key=_instance_sort_key)
        accepted = group[0]
        if len(group) > 1:
            redundant.append(
                RedundantPhysicalInstances(
                    logical_record_sha256=logical_hash,
                    paths=tuple(item.path for item in group),
                )
            )
        accepted_instances.append(accepted)
        accepted_records.append(accepted.logical_record)
        remaining = [item for item in remaining if item not in matching]
        predecessor = logical_hash
        sequence_number += 1


def _missing_link_classification(
    remaining: list[StoredRecordInstance],
    sequence_number: int,
    predecessor: str,
    accepted_instances: list[StoredRecordInstance],
) -> str:
    if not remaining:
        return VALID_LINEAR_CHAIN if accepted_instances else EMPTY_CHAIN
    if any(
        item.logical_record["sequence_number"] == sequence_number
        and item.logical_record["predecessor_logical_record_sha256"] != predecessor
        for item in remaining
    ):
        return PREDECESSOR_MISMATCH
    if any(item.logical_record["sequence_number"] > sequence_number for item in remaining):
        return SEQUENCE_GAP
    return PREDECESSOR_MISMATCH


def _first_fatal_rejection(rejected: list[RejectedObject]) -> RejectedObject | None:
    severity_order = (
        INVALID_CANONICAL_BYTES,
        INVALID_PHYSICAL_OBJECT_IDENTITY,
        CROSS_CHAIN_OBJECT,
        CROSS_IDENTITY_OBJECT,
    )
    for classification in severity_order:
        for item in rejected:
            if item.classification == classification:
                return item
    return None


def _instance_sort_key(instance: StoredRecordInstance) -> tuple[str, str, str]:
    return (
        instance.logical_record_sha256,
        instance.stored_object_sha256,
        instance.path,
    )


def _read_bytes(path: Path) -> bytes:
    with open(_windows_api_path(path), "rb") as handle:
        return handle.read()


def _windows_api_path(path: Path) -> str:
    text = os.path.abspath(str(path))
    if os.name != "nt":
        return text
    prefix = "\\\\?\\"
    unc_prefix = "\\\\?\\UNC\\"
    if text.startswith(prefix):
        return text
    if text.startswith("\\\\"):
        return unc_prefix + text[2:]
    return prefix + text
