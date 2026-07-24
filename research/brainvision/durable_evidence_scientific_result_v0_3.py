from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import durable_evidence_authority_v0_3 as authority
import durable_evidence_durability_v0_3 as durability
import durable_evidence_primary_writer_v0_3 as primary_writer
import durable_evidence_replay_v0_3 as replay
import durable_evidence_schema_v0_3 as schema


AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT = (
    "AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT"
)
ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE = "ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE"
INVALID_SCIENTIFIC_COMPLETION = "INVALID_SCIENTIFIC_COMPLETION"
NO_AUTHORITATIVE_SCIENTIFIC_RESULT = "NO_AUTHORITATIVE_SCIENTIFIC_RESULT"
CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
BYTE_VALID_DURABILITY_UNCONFIRMED = primary_writer.BYTE_VALID_DURABILITY_UNCONFIRMED


class ScientificResultEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class BundleInstance:
    path: str
    stored_bundle_object_sha256: str
    bundle_payload_sha256: str
    bundle_payload: dict


@dataclass(frozen=True)
class CompletionInstance:
    path: str
    stored_object_sha256: str
    logical_record_sha256: str
    logical_record: dict


@dataclass(frozen=True)
class RedundantBundleInstances:
    bundle_payload_sha256: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class ScientificRecognitionResult:
    classification: str
    detail: str
    scientific_result_kind: str | None = None
    bundle_payload_sha256: str | None = None
    completion_logical_record_sha256: str | None = None
    redundant_bundle_instances: tuple[RedundantBundleInstances, ...] = ()


def build_scientific_completion_payload(
    stored_bundle_object: dict,
    *,
    include_optional_forensic_hash: bool = True,
) -> dict:
    schema.validate_stored_bundle_object(stored_bundle_object)
    bundle_payload = stored_bundle_object["bundle_payload"]
    payload = {
        "scientific_result_kind": bundle_payload["scientific_result_kind"],
        "bundle_payload_sha256": bundle_payload["bundle_payload_sha256"],
        "bundle_payload_byte_length": len(schema.canonical_json_bytes(bundle_payload)),
        "bundle_schema_identity": schema.IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA,
    }
    if include_optional_forensic_hash:
        payload["accepted_stored_bundle_object_sha256"] = stored_bundle_object[
            "stored_bundle_object_sha256"
        ]
    payload.update(
        {
            "scientific_pass_count": 2,
            "two_pass_canonical_identity_status": "identical",
            "authority_consumed_status": "AUTHORITY_CONSUMED",
            "manifest_contact_attempt_count": 2,
            "manifest_read_success_count": 2,
            "implementation_identities": bundle_payload["implementation_identities"],
            "configuration_identity": bundle_payload["configuration_identity"],
            "manifest_identities": bundle_payload["manifest_identities"],
            "execution_identity": bundle_payload["execution_identity"],
            "scientific_execution_authorization_identity": bundle_payload[
                "scientific_execution_authorization_identity"
            ],
            "protocol_identity": schema.PROTOCOL_IDENTITY,
            "completion_validity": "VALID",
        }
    )
    schema.validate_scientific_completion_payload(payload)
    return payload


def build_scientific_completion_logical_record(
    stored_bundle_object: dict,
    *,
    sequence_number: int,
    predecessor_logical_record_sha256: str,
    include_optional_forensic_hash: bool = True,
) -> dict:
    payload = build_scientific_completion_payload(
        stored_bundle_object,
        include_optional_forensic_hash=include_optional_forensic_hash,
    )
    return schema.build_scientific_logical_record(
        record_kind="SCIENTIFIC_COMPLETION",
        sequence_number=sequence_number,
        execution_identity=payload["execution_identity"],
        scientific_execution_authorization_identity=payload[
            "scientific_execution_authorization_identity"
        ],
        predecessor_logical_record_sha256=predecessor_logical_record_sha256,
        payload=payload,
    )


def build_stored_scientific_completion_record(
    stored_bundle_object: dict,
    *,
    sequence_number: int,
    predecessor_logical_record_sha256: str,
    writer_attempt_identity: str,
    include_optional_forensic_hash: bool = True,
) -> dict:
    return schema.build_stored_record_object(
        logical_record=build_scientific_completion_logical_record(
            stored_bundle_object,
            sequence_number=sequence_number,
            predecessor_logical_record_sha256=predecessor_logical_record_sha256,
            include_optional_forensic_hash=include_optional_forensic_hash,
        ),
        writer_identity=primary_writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=writer_attempt_identity,
    )


def validate_completion_against_bundle(
    completion_logical_record: dict,
    matching_bundle_instances: Iterable[BundleInstance],
    *,
    durability_evidence: durability.VerifiedDurabilityEvidence,
) -> None:
    schema.validate_logical_record(completion_logical_record)
    if completion_logical_record["record_kind"] != "SCIENTIFIC_COMPLETION":
        raise ScientificResultEvidenceError("record is not SCIENTIFIC_COMPLETION")
    payload = completion_logical_record["payload"]
    schema.validate_scientific_completion_payload(payload)
    bundle_instances = tuple(matching_bundle_instances)
    if not bundle_instances:
        raise ScientificResultEvidenceError("matching bundle is absent")
    bundle_hashes = {item.bundle_payload_sha256 for item in bundle_instances}
    if len(bundle_hashes) != 1:
        raise ScientificResultEvidenceError("matching bundle identity is not unique")
    bundle_payload_sha256 = next(iter(bundle_hashes))
    if payload["bundle_payload_sha256"] != bundle_payload_sha256:
        raise ScientificResultEvidenceError("bundle_payload_sha256 mismatch")
    bundle_payload = bundle_instances[0].bundle_payload
    if payload["bundle_payload_byte_length"] != len(
        schema.canonical_json_bytes(bundle_payload)
    ):
        raise ScientificResultEvidenceError("bundle byte length mismatch")
    if payload["bundle_schema_identity"] != bundle_payload["bundle_schema_identity"]:
        raise ScientificResultEvidenceError("bundle schema identity mismatch")
    if payload["scientific_result_kind"] != bundle_payload["scientific_result_kind"]:
        raise ScientificResultEvidenceError("scientific_result_kind mismatch")
    if payload["two_pass_canonical_identity_status"] != (
        bundle_payload["two_pass_canonical_identity_status"]
    ):
        raise ScientificResultEvidenceError("two-pass identity status mismatch")
    for key in (
        "implementation_identities",
        "configuration_identity",
        "manifest_identities",
        "execution_identity",
        "scientific_execution_authorization_identity",
        "protocol_identity",
    ):
        if payload[key] != bundle_payload[key]:
            raise ScientificResultEvidenceError("%s mismatch" % key)
    if "accepted_stored_bundle_object_sha256" in payload:
        selected_hash = payload["accepted_stored_bundle_object_sha256"]
        accepted_hashes = {item.stored_bundle_object_sha256 for item in bundle_instances}
        if selected_hash not in accepted_hashes:
            raise ScientificResultEvidenceError(
                "accepted_stored_bundle_object_sha256 mismatch"
            )
        if not durability_evidence.has_bundle_object(selected_hash):
            raise ScientificResultEvidenceError(
                "selected stored bundle durability is unconfirmed"
            )


def recognize_scientific_result(
    *,
    bundle_directory_path: str | Path,
    scientific_chain_directory_path: str | Path,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
    durability_evidence: durability.VerifiedDurabilityEvidence | None = None,
) -> ScientificRecognitionResult:
    if durability_evidence is None:
        durability_evidence = durability.VerifiedDurabilityEvidence.empty()
    if not isinstance(durability_evidence, durability.VerifiedDurabilityEvidence):
        raise ScientificResultEvidenceError("VerifiedDurabilityEvidence is required")
    bundles, bundle_rejections = _load_bundle_instances(
        bundle_directory_path,
        execution_identity=execution_identity,
        scientific_execution_authorization_identity=(
            scientific_execution_authorization_identity
        ),
    )
    chain = replay.replay_chain(
        scientific_chain_directory_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=execution_identity,
        expected_authorization_identity=scientific_execution_authorization_identity,
    )
    if bundle_rejections or chain.rejected_objects:
        return ScientificRecognitionResult(
            classification=CONTRADICTORY_EVIDENCE,
            detail="malformed, foreign, or invalid evidence cannot be hidden",
        )
    if chain.classification not in (replay.VALID_LINEAR_CHAIN, replay.EMPTY_CHAIN):
        return ScientificRecognitionResult(
            classification=CONTRADICTORY_EVIDENCE,
            detail="scientific chain replay failed closed: %s" % chain.classification,
        )

    chain_status, completion, chain_detail = _exact_completion_chain(
        chain,
        durability_evidence=durability_evidence,
    )
    if chain_status == CONTRADICTORY_EVIDENCE:
        return ScientificRecognitionResult(
            classification=CONTRADICTORY_EVIDENCE,
            detail=chain_detail,
        )
    if chain_status == BYTE_VALID_DURABILITY_UNCONFIRMED:
        return ScientificRecognitionResult(
            classification=BYTE_VALID_DURABILITY_UNCONFIRMED,
            detail=chain_detail,
        )
    if chain_status == INVALID_SCIENTIFIC_COMPLETION:
        return ScientificRecognitionResult(
            classification=INVALID_SCIENTIFIC_COMPLETION,
            detail=chain_detail,
            completion_logical_record_sha256=(
                completion.logical_record_sha256 if completion is not None else None
            ),
        )

    grouped_bundles: dict[str, list[BundleInstance]] = {}
    for instance in bundles:
        grouped_bundles.setdefault(instance.bundle_payload_sha256, []).append(instance)
    if len(grouped_bundles) > 1:
        return ScientificRecognitionResult(
            classification=CONTRADICTORY_EVIDENCE,
            detail="different bundle payload identities claim the same result position",
        )

    redundant = tuple(
        RedundantBundleInstances(
            bundle_payload_sha256=bundle_hash,
            paths=tuple(item.path for item in sorted(group, key=lambda value: value.path)),
        )
        for bundle_hash, group in sorted(grouped_bundles.items())
        if len(group) > 1
    )

    if not bundles and completion is None:
        return ScientificRecognitionResult(
            classification=NO_AUTHORITATIVE_SCIENTIFIC_RESULT,
            detail="no bundle or completion evidence was accepted",
        )
    if bundles and completion is None:
        if not _has_durable_bundle(bundles, durability_evidence):
            return ScientificRecognitionResult(
                classification=BYTE_VALID_DURABILITY_UNCONFIRMED,
                detail="bundle bytes are valid but durability is unconfirmed",
                redundant_bundle_instances=redundant,
            )
        bundle = bundles[0]
        return ScientificRecognitionResult(
            classification=ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE,
            detail="valid bundle has no linked SCIENTIFIC_COMPLETION",
            scientific_result_kind=bundle.bundle_payload["scientific_result_kind"],
            bundle_payload_sha256=bundle.bundle_payload_sha256,
            redundant_bundle_instances=redundant,
        )
    if completion is not None and not bundles:
        return ScientificRecognitionResult(
            classification=INVALID_SCIENTIFIC_COMPLETION,
            detail="SCIENTIFIC_COMPLETION has no matching bundle",
            completion_logical_record_sha256=completion.logical_record_sha256,
        )

    if completion is None:
        return ScientificRecognitionResult(
            classification=NO_AUTHORITATIVE_SCIENTIFIC_RESULT,
            detail="no SCIENTIFIC_COMPLETION evidence was accepted",
            redundant_bundle_instances=redundant,
        )

    try:
        validate_completion_against_bundle(
            completion.logical_record,
            bundles,
            durability_evidence=durability_evidence,
        )
    except (schema.EvidenceValidationError, ScientificResultEvidenceError) as exc:
        return ScientificRecognitionResult(
            classification=INVALID_SCIENTIFIC_COMPLETION,
            detail=str(exc),
            completion_logical_record_sha256=completion.logical_record_sha256,
            redundant_bundle_instances=redundant,
        )

    bundle = bundles[0]
    if not _has_durable_bundle(bundles, durability_evidence):
        return ScientificRecognitionResult(
            classification=BYTE_VALID_DURABILITY_UNCONFIRMED,
            detail="bundle durability is unconfirmed",
            bundle_payload_sha256=bundle.bundle_payload_sha256,
            completion_logical_record_sha256=completion.logical_record_sha256,
            redundant_bundle_instances=redundant,
        )
    if not durability_evidence.has_record_object(completion.stored_object_sha256):
        return ScientificRecognitionResult(
            classification=BYTE_VALID_DURABILITY_UNCONFIRMED,
            detail="SCIENTIFIC_COMPLETION durability is unconfirmed",
            bundle_payload_sha256=bundle.bundle_payload_sha256,
            completion_logical_record_sha256=completion.logical_record_sha256,
            redundant_bundle_instances=redundant,
        )
    authority_result = authority.replay_scientific_authority_state(
        scientific_chain_directory_path,
        execution_identity=execution_identity,
        scientific_execution_authorization_identity=(
            scientific_execution_authorization_identity
        ),
        durability_evidence=durability_evidence,
        invocation_window_observed=True,
    )
    if authority_result.state != authority.CONSUMED:
        classification = NO_AUTHORITATIVE_SCIENTIFIC_RESULT
        if "unconfirmed" in authority_result.detail:
            classification = BYTE_VALID_DURABILITY_UNCONFIRMED
        elif authority_result.replay_classification not in (
            replay.VALID_LINEAR_CHAIN,
            replay.EMPTY_CHAIN,
        ):
            classification = CONTRADICTORY_EVIDENCE
        return ScientificRecognitionResult(
            classification=classification,
            detail="authority replay did not prove CONSUMED: %s"
            % authority_result.detail,
            bundle_payload_sha256=bundle.bundle_payload_sha256,
            completion_logical_record_sha256=completion.logical_record_sha256,
            redundant_bundle_instances=redundant,
        )
    if completion.logical_record["payload"]["authority_consumed_status"] != (
        "AUTHORITY_CONSUMED"
    ):
        return ScientificRecognitionResult(
            classification=INVALID_SCIENTIFIC_COMPLETION,
            detail="completion authority status disagrees with replay",
            completion_logical_record_sha256=completion.logical_record_sha256,
            redundant_bundle_instances=redundant,
        )
    return ScientificRecognitionResult(
        classification=AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT,
        detail="verified immutable bundle plus linked SCIENTIFIC_COMPLETION",
        scientific_result_kind=bundle.bundle_payload["scientific_result_kind"],
        bundle_payload_sha256=bundle.bundle_payload_sha256,
        completion_logical_record_sha256=completion.logical_record_sha256,
        redundant_bundle_instances=redundant,
    )


def _load_bundle_instances(
    bundle_directory_path: str | Path,
    *,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
) -> tuple[list[BundleInstance], list[str]]:
    instances: list[BundleInstance] = []
    rejections: list[str] = []
    for path in sorted(Path(bundle_directory_path).glob("*.json"), key=lambda item: item.name):
        try:
            raw = path.read_bytes()
            stored_bundle = schema.load_canonical_json_bytes(
                raw, max_bytes=schema.MAX_STORED_BUNDLE_OBJECT_BYTES
            )
            schema.validate_stored_bundle_object(stored_bundle)
        except schema.EvidenceValidationError as exc:
            rejections.append("%s: %s" % (path, exc))
            continue
        bundle_payload = stored_bundle["bundle_payload"]
        if bundle_payload["execution_identity"] != execution_identity:
            rejections.append("%s: execution identity mismatch" % path)
            continue
        if (
            bundle_payload["scientific_execution_authorization_identity"]
            != scientific_execution_authorization_identity
        ):
            rejections.append("%s: authorization identity mismatch" % path)
            continue
        instances.append(
            BundleInstance(
                path=str(path),
                stored_bundle_object_sha256=stored_bundle[
                    "stored_bundle_object_sha256"
                ],
                bundle_payload_sha256=stored_bundle["bundle_payload_sha256"],
                bundle_payload=bundle_payload,
            )
        )
    return instances, rejections


def _has_durable_bundle(
    bundles: tuple[BundleInstance, ...] | list[BundleInstance],
    durability_evidence: durability.VerifiedDurabilityEvidence,
) -> bool:
    return any(
        durability_evidence.has_bundle_object(bundle.stored_bundle_object_sha256)
        for bundle in bundles
    )


def _exact_completion_chain(
    chain: replay.ReplayResult,
    *,
    durability_evidence: durability.VerifiedDurabilityEvidence,
) -> tuple[str, CompletionInstance | None, str]:
    accepted = chain.accepted_instances
    completion_candidates = [
        instance
        for instance in accepted
        if instance.logical_record["record_kind"] == "SCIENTIFIC_COMPLETION"
    ]
    if not completion_candidates:
        return NO_AUTHORITATIVE_SCIENTIFIC_RESULT, None, "no completion"
    if len(accepted) < 6:
        return (
            INVALID_SCIENTIFIC_COMPLETION,
            _completion_instance(completion_candidates[0]),
            "scientific chain is too short for SCIENTIFIC_COMPLETION",
        )
    expected = (
        ("AUTHORITY_CONSUMED", 0, None, None),
        ("MANIFEST_CONTACT_ATTEMPT", 1, 1, 0),
        ("MANIFEST_READ_SUCCESS", 2, 1, 1),
        ("MANIFEST_CONTACT_ATTEMPT", 3, 2, 2),
        ("MANIFEST_READ_SUCCESS", 4, 2, 3),
        ("SCIENTIFIC_COMPLETION", 5, None, 4),
    )
    for index, (kind, sequence, pass_index, predecessor_index) in enumerate(expected):
        instance = accepted[index]
        record = instance.logical_record
        if record["record_kind"] != kind or record["sequence_number"] != sequence:
            return (
                INVALID_SCIENTIFIC_COMPLETION,
                _first_completion_instance(completion_candidates),
                "scientific chain transition mismatch at sequence %d" % sequence,
            )
        expected_predecessor = schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        if predecessor_index is not None:
            expected_predecessor = accepted[predecessor_index].logical_record_sha256
        if record["predecessor_logical_record_sha256"] != expected_predecessor:
            return (
                INVALID_SCIENTIFIC_COMPLETION,
                _first_completion_instance(completion_candidates),
                "scientific chain predecessor mismatch at sequence %d" % sequence,
            )
        if pass_index is not None:
            if tuple(record["payload"].keys()) != ("pass_index",):
                return (
                    INVALID_SCIENTIFIC_COMPLETION,
                    _first_completion_instance(completion_candidates),
                    "manifest pass payload shape mismatch",
                )
            if record["payload"]["pass_index"] != pass_index:
                return (
                    INVALID_SCIENTIFIC_COMPLETION,
                    _first_completion_instance(completion_candidates),
                    "manifest pass order mismatch",
                )
        if not durability_evidence.has_record_object(instance.stored_object_sha256):
            return (
                BYTE_VALID_DURABILITY_UNCONFIRMED,
                _first_completion_instance(completion_candidates),
                "scientific chain record durability is unconfirmed",
            )
    completion = _completion_instance(accepted[5])
    if completion.logical_record["payload"]["authority_consumed_status"] != (
        "AUTHORITY_CONSUMED"
    ):
        return (
            INVALID_SCIENTIFIC_COMPLETION,
            completion,
            "SCIENTIFIC_COMPLETION self-declared authority status is invalid",
        )
    for offset, instance in enumerate(accepted[6:], start=6):
        record = instance.logical_record
        if offset == 6 and record["record_kind"] == "SCIENTIFIC_TERMINAL_STATUS":
            if record["predecessor_logical_record_sha256"] != (
                completion.logical_record_sha256
            ):
                return (
                    CONTRADICTORY_EVIDENCE,
                    completion,
                    "terminal status predecessor mismatch",
                )
            continue
        return (
            CONTRADICTORY_EVIDENCE,
            completion,
            "unexpected scientific evidence after SCIENTIFIC_COMPLETION",
        )
    if completion_candidates != [accepted[5]]:
        return (
            CONTRADICTORY_EVIDENCE,
            completion,
            "conflicting SCIENTIFIC_COMPLETION records are present",
        )
    return AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT, completion, "exact chain accepted"


def _completion_instance(instance: replay.StoredRecordInstance) -> CompletionInstance:
    return CompletionInstance(
        path=instance.path,
        stored_object_sha256=instance.stored_object_sha256,
        logical_record_sha256=instance.logical_record_sha256,
        logical_record=instance.logical_record,
    )


def _first_completion_instance(
    completion_candidates: list[replay.StoredRecordInstance],
) -> CompletionInstance:
    return _completion_instance(completion_candidates[0])
