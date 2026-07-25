from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import os
import sys

import durable_evidence_primary_writer_v0_3 as primary_writer
import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


PUBLICATION_AUTHORITY_NOT_ATTEMPTED = "PUBLICATION_AUTHORITY_NOT_ATTEMPTED"
PUBLICATION_AUTHORITY_CONSUMED = "PUBLICATION_AUTHORITY_CONSUMED"
PUBLICATION_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED = (
    "PUBLICATION_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED"
)
PUBLICATION_AUTHORITY_ATTEMPT_STATE_INDETERMINATE = (
    "PUBLICATION_AUTHORITY_ATTEMPT_STATE_INDETERMINATE"
)

PUBLICATION_COMPLETED = "PUBLICATION_COMPLETED"
PUBLICATION_AUTHORIZATION_VALIDATION_FAILED = (
    "PUBLICATION_AUTHORIZATION_VALIDATION_FAILED"
)
PUBLICATION_CHAIN_GENESIS_WRITE_FAILED = "PUBLICATION_CHAIN_GENESIS_WRITE_FAILED"
PUBLICATION_ATTEMPTED_WRITE_FAILED = "PUBLICATION_ATTEMPTED_WRITE_FAILED"
PUBLICATION_CHAIN_IDENTITY_COLLISION = "PUBLICATION_CHAIN_IDENTITY_COLLISION"
PUBLICATION_STAGING_DIRECTORY_COLLISION = "PUBLICATION_STAGING_DIRECTORY_COLLISION"
PUBLICATION_FINAL_DIRECTORY_COLLISION = "PUBLICATION_FINAL_DIRECTORY_COLLISION"
PUBLICATION_STAGING_INCOMPLETE = "PUBLICATION_STAGING_INCOMPLETE"
PUBLICATION_VERIFICATION_FAILED = "PUBLICATION_VERIFICATION_FAILED"
PUBLICATION_STAGING_DURABILITY_UNCONFIRMED = (
    "PUBLICATION_STAGING_DURABILITY_UNCONFIRMED"
)
PUBLICATION_PROMOTION_FAILED = "PUBLICATION_PROMOTION_FAILED"
PUBLICATION_PROMOTION_OUTCOME_INDETERMINATE = (
    "PUBLICATION_PROMOTION_OUTCOME_INDETERMINATE"
)
PUBLICATION_FINAL_DIRECTORY_INVALID = "PUBLICATION_FINAL_DIRECTORY_INVALID"
PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED = (
    "PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED"
)
PUBLICATION_TERMINAL_STATUS_WRITE_FAILED = "PUBLICATION_TERMINAL_STATUS_WRITE_FAILED"
PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED = (
    "PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED"
)
PUBLICATION_STAGING_SPACE_BUDGET_UNAVAILABLE = (
    "PUBLICATION_STAGING_SPACE_BUDGET_UNAVAILABLE"
)
PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE = (
    "PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE"
)

STAGING_CAPACITY_CONFIRMED = "STAGING_CAPACITY_CONFIRMED"
STAGING_CAPACITY_UNAVAILABLE = "STAGING_CAPACITY_UNAVAILABLE"
STAGING_CAPACITY_INDETERMINATE = "STAGING_CAPACITY_INDETERMINATE"
_STAGING_CAPACITY_RESPONSE_KEYS = (
    "status",
    "required_bytes",
    "available_bytes",
    "detail",
)
_J1_RESOURCE_CLASSIFICATIONS = {
    schema.RESOURCE_LIMIT_EXCEEDED: PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED,
    schema.ARTIFACT_SIZE_LIMIT_EXCEEDED: PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED,
    schema.ARTIFACT_SET_SIZE_LIMIT_EXCEEDED: (
        PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
    ),
    schema.SUMMARY_SIZE_LIMIT_EXCEEDED: PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED,
    schema.CANONICAL_STRUCTURE_LIMIT_EXCEEDED: (
        PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
    ),
    schema.STRING_SIZE_LIMIT_EXCEEDED: PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED,
    schema.INTEGER_MAGNITUDE_LIMIT_EXCEEDED: (
        PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
    ),
    schema.RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH: (
        PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
    ),
    schema.STAGING_SPACE_BUDGET_UNAVAILABLE: (
        PUBLICATION_STAGING_SPACE_BUDGET_UNAVAILABLE
    ),
    schema.RESOURCE_ADMISSIBILITY_INDETERMINATE: (
        PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE
    ),
}

PUBLICATION_CHAIN_ROOT = ".iososv_v0_3.publication_chain"
PUBLICATION_STAGING_ROOT = ".iososv_v0_3.publication_staging"
PUBLICATION_FINAL_ROOT = "iososv_v0_3.publication"


class PublicationEvidenceError(ValueError):
    pass


class PublicationAuthorityReuseDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class PublicationBeginState:
    execution_identity: str
    publication_projection_authorization_identity: str
    publication_projection_identity: str
    publication_chain_identity: str
    state: str
    reuse_permission_consumed: bool
    protected_mutation_permitted: bool


@dataclass(frozen=True)
class PublicationRecordWriteEvidence:
    logical_record: dict[str, Any]
    stored_record_object: dict[str, Any]
    write_result: primary_writer.ImmutableWriteResult


@dataclass(frozen=True)
class PublicationPaths:
    chain_directory: Path
    staging_directory: Path
    final_directory: Path


@dataclass(frozen=True)
class PublicationProjectionResult:
    classification: str
    detail: str
    publication_projection_identity: str | None = None
    publication_chain_identity: str | None = None
    artifact_sha256s: dict[str, str] | None = None
    paths: PublicationPaths | None = None
    record_writes: tuple[PublicationRecordWriteEvidence, ...] = ()
    authority_state: str = PUBLICATION_AUTHORITY_NOT_ATTEMPTED
    resource_failure_code: str | None = None
    resource_policy_identity: dict[str, Any] | None = None
    required_staging_bytes: int | None = None
    available_staging_bytes: int | None = None
    directory_durability_policy_identity: dict[str, Any] | None = None
    directory_durability_failure_code: str | None = None


@dataclass(frozen=True)
class StagingCapacityAdmission:
    status: str
    required_bytes: int
    available_bytes: int | None
    detail: str


class FailClosedStagingCapacityAdapter:
    def check_staging_capacity(self, *, required_bytes: int) -> dict[str, Any]:
        return {
            "status": STAGING_CAPACITY_INDETERMINATE,
            "required_bytes": required_bytes,
            "available_bytes": None,
            "detail": "staging capacity was not explicitly confirmed",
        }


class SyntheticPublicationContext:
    """Live synthetic guard; durable replay is the post-event source of truth."""

    def __init__(self) -> None:
        self._begun_authorizations: set[str] = set()
        self._begun_chains: set[tuple[str, str, str, str]] = set()

    def begin_once(
        self,
        *,
        execution_identity: str,
        publication_projection_authorization_identity: str,
        publication_projection_identity: str,
        publication_chain_identity: str,
    ) -> None:
        chain_key = (
            execution_identity,
            publication_projection_authorization_identity,
            publication_projection_identity,
            publication_chain_identity,
        )
        if (
            publication_projection_authorization_identity in self._begun_authorizations
            or chain_key in self._begun_chains
        ):
            raise PublicationAuthorityReuseDenied(
                "publication authorization reuse is denied"
            )
        self._begun_authorizations.add(publication_projection_authorization_identity)
        self._begun_chains.add(chain_key)


class SyntheticPublicationInvocation:
    def __init__(
        self,
        *,
        execution_identity: str,
        publication_projection_authorization_identity: str,
        publication_projection_identity: str,
        publication_chain_identity: str,
        context: SyntheticPublicationContext,
    ) -> None:
        _validate_hex64(execution_identity, "execution_identity")
        _validate_hex64(
            publication_projection_authorization_identity,
            "publication_projection_authorization_identity",
        )
        _validate_hex64(publication_projection_identity, "publication_projection_identity")
        _validate_hex64(publication_chain_identity, "publication_chain_identity")
        if not isinstance(context, SyntheticPublicationContext):
            raise PublicationEvidenceError("SyntheticPublicationContext is required")
        self.execution_identity = execution_identity
        self.publication_projection_authorization_identity = (
            publication_projection_authorization_identity
        )
        self.publication_projection_identity = publication_projection_identity
        self.publication_chain_identity = publication_chain_identity
        self._context = context
        self._begun = False

    @property
    def live_state(self) -> str:
        if self._begun:
            return PUBLICATION_AUTHORITY_CONSUMED
        return PUBLICATION_AUTHORITY_NOT_ATTEMPTED

    @property
    def reuse_permission_consumed(self) -> bool:
        return self._begun

    def begin(self) -> PublicationBeginState:
        if self._begun:
            raise PublicationAuthorityReuseDenied(
                "publication authorization reuse is denied"
            )
        self._context.begin_once(
            execution_identity=self.execution_identity,
            publication_projection_authorization_identity=(
                self.publication_projection_authorization_identity
            ),
            publication_projection_identity=self.publication_projection_identity,
            publication_chain_identity=self.publication_chain_identity,
        )
        self._begun = True
        return PublicationBeginState(
            execution_identity=self.execution_identity,
            publication_projection_authorization_identity=(
                self.publication_projection_authorization_identity
            ),
            publication_projection_identity=self.publication_projection_identity,
            publication_chain_identity=self.publication_chain_identity,
            state=PUBLICATION_AUTHORITY_CONSUMED,
            reuse_permission_consumed=True,
            protected_mutation_permitted=True,
        )


def publication_paths(
    root_path: str | Path, publication_chain_identity: str
) -> PublicationPaths:
    _validate_hex64(publication_chain_identity, "publication_chain_identity")
    root = _validated_root(root_path)
    return PublicationPaths(
        chain_directory=_owned_child(root, PUBLICATION_CHAIN_ROOT, publication_chain_identity),
        staging_directory=_owned_child(
            root, PUBLICATION_STAGING_ROOT, publication_chain_identity
        ),
        final_directory=_owned_child(root, PUBLICATION_FINAL_ROOT, publication_chain_identity),
    )


def build_publication_authority_accepted_logical_record(
    *,
    execution_identity: str,
    scientific_execution_authorization_identity: str,
    bundle_payload_sha256: str,
    scientific_completion_logical_record_sha256: str,
    publication_projection_authorization_identity: str,
    publication_projection_identity: str,
    publication_chain_identity: str,
    publication_recipe_identity: str,
    publication_utility_identities: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "execution_identity": execution_identity,
        "scientific_execution_authorization_identity": (
            scientific_execution_authorization_identity
        ),
        "bundle_payload_sha256": bundle_payload_sha256,
        "scientific_completion_logical_record_sha256": (
            scientific_completion_logical_record_sha256
        ),
        "publication_projection_authorization_identity": (
            publication_projection_authorization_identity
        ),
        "publication_projection_identity": publication_projection_identity,
        "publication_chain_identity": publication_chain_identity,
        "publication_recipe_identity": publication_recipe_identity,
        "publication_utility_identities": dict(publication_utility_identities),
        "expected_artifact_filenames": list(schema.PUBLICATION_ARTIFACT_FILENAMES),
    }
    return schema.build_publication_logical_record(
        record_kind="PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED",
        sequence_number=0,
        execution_identity=execution_identity,
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_chain_identity=publication_chain_identity,
        predecessor_logical_record_sha256=(
            schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        ),
        payload=payload,
    )


def build_publication_attempted_logical_record(
    *,
    execution_identity: str,
    publication_projection_authorization_identity: str,
    publication_projection_identity: str,
    publication_chain_identity: str,
    predecessor_logical_record_sha256: str,
) -> dict[str, Any]:
    payload = {
        "publication_projection_identity": publication_projection_identity,
        "publication_chain_identity": publication_chain_identity,
        "artifact_filenames": list(schema.PUBLICATION_ARTIFACT_FILENAMES),
    }
    return schema.build_publication_logical_record(
        record_kind="PUBLICATION_ATTEMPTED",
        sequence_number=1,
        execution_identity=execution_identity,
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_chain_identity=publication_chain_identity,
        predecessor_logical_record_sha256=predecessor_logical_record_sha256,
        payload=payload,
    )


def build_publication_completed_logical_record(
    *,
    execution_identity: str,
    publication_projection_authorization_identity: str,
    publication_projection_identity: str,
    publication_chain_identity: str,
    predecessor_logical_record_sha256: str,
    artifact_sha256s: Mapping[str, str],
) -> dict[str, Any]:
    schema.validate_publication_artifact_sha256s(artifact_sha256s)
    payload = {
        "publication_projection_identity": publication_projection_identity,
        "publication_chain_identity": publication_chain_identity,
        "artifact_sha256s": {
            name: artifact_sha256s[name]
            for name in schema.PUBLICATION_ARTIFACT_FILENAMES
        },
    }
    return schema.build_publication_logical_record(
        record_kind="PUBLICATION_COMPLETED",
        sequence_number=2,
        execution_identity=execution_identity,
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_chain_identity=publication_chain_identity,
        predecessor_logical_record_sha256=predecessor_logical_record_sha256,
        payload=payload,
    )


def project_publication(
    *,
    root_path: str | Path,
    bundle_payload: Mapping[str, Any],
    scientific_completion_logical_record: Mapping[str, Any],
    publication_projection_authorization_identity: str,
    publication_utility_identities: Mapping[str, Any],
    context: SyntheticPublicationContext,
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None = None,
    promotion_adapter: windows_adapter.SameVolumeNoReplacePromotionAdapter | None = None,
    staging_capacity_adapter: object | None = None,
    writer_attempt_identities: Sequence[str] = (
        "0" * 32,
        "1" * 32,
        "2" * 32,
        "3" * 32,
    ),
    expected_publication_projection_identity: str | None = None,
    expected_publication_chain_identity: str | None = None,
    synthetic_fault_point: str | None = None,
) -> PublicationProjectionResult:
    if _has_null_policy_identity(publication_utility_identities):
        return _pre_anchor_resource_result(
            schema.RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH,
            "resource admissibility policy identity mismatch",
        )
    try:
        anchor = validate_publication_anchor(
            bundle_payload=bundle_payload,
            scientific_completion_logical_record=scientific_completion_logical_record,
            publication_projection_authorization_identity=(
                publication_projection_authorization_identity
            ),
            publication_utility_identities=publication_utility_identities,
            expected_publication_projection_identity=(
                expected_publication_projection_identity
            ),
            expected_publication_chain_identity=expected_publication_chain_identity,
        )
        attempts = _writer_attempts(writer_attempt_identities, 3)
        paths = publication_paths(root_path, anchor["publication_chain_identity"])
    except (schema.EvidenceValidationError, PublicationEvidenceError) as exc:
        return PublicationProjectionResult(
            classification=PUBLICATION_AUTHORIZATION_VALIDATION_FAILED,
            detail=str(exc),
        )

    invocation = SyntheticPublicationInvocation(
        execution_identity=anchor["execution_identity"],
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        context=context,
    )
    invocation.begin()

    if synthetic_fault_point == "publication_authority_genesis_write_failure":
        return PublicationProjectionResult(
            classification=PUBLICATION_CHAIN_GENESIS_WRITE_FAILED,
            detail="synthetic publication genesis write failure",
            publication_projection_identity=anchor["publication_projection_identity"],
            publication_chain_identity=anchor["publication_chain_identity"],
            paths=paths,
            authority_state=PUBLICATION_AUTHORITY_CONSUMED,
        )
    if paths.chain_directory.exists():
        return _result(
            PUBLICATION_CHAIN_IDENTITY_COLLISION,
            "publication chain directory already exists",
            anchor,
            paths,
        )
    try:
        paths.chain_directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return _result(
            PUBLICATION_CHAIN_IDENTITY_COLLISION,
            "publication chain directory already exists",
            anchor,
            paths,
        )

    record_writes: list[PublicationRecordWriteEvidence] = []
    genesis_record = build_publication_authority_accepted_logical_record(
        execution_identity=anchor["execution_identity"],
        scientific_execution_authorization_identity=(
            anchor["scientific_execution_authorization_identity"]
        ),
        bundle_payload_sha256=anchor["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=(
            anchor["scientific_completion_logical_record_sha256"]
        ),
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        publication_recipe_identity=anchor["publication_recipe_identity"],
        publication_utility_identities=publication_utility_identities,
    )
    genesis = _write_publication_record(
        paths.chain_directory,
        genesis_record,
        writer_attempt_identity=attempts[0],
        durability_adapter=durability_adapter,
    )
    if genesis is None or not _durable(genesis):
        return _result(
            PUBLICATION_CHAIN_GENESIS_WRITE_FAILED,
            "PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED was not durably accepted",
            anchor,
            paths,
            record_writes=record_writes + ([genesis] if genesis is not None else []),
        )
    record_writes.append(genesis)

    if synthetic_fault_point in (
        "after_publication_genesis_before_attempted",
        "before_publication_attempted_write",
    ):
        return _result(
            PUBLICATION_ATTEMPTED_WRITE_FAILED,
            "synthetic failure before PUBLICATION_ATTEMPTED",
            anchor,
            paths,
            record_writes=record_writes,
        )
    attempted_record = build_publication_attempted_logical_record(
        execution_identity=anchor["execution_identity"],
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        predecessor_logical_record_sha256=genesis.logical_record["logical_record_sha256"],
    )
    attempted = _write_publication_record(
        paths.chain_directory,
        attempted_record,
        writer_attempt_identity=attempts[1],
        durability_adapter=durability_adapter,
    )
    if attempted is None or not _durable(attempted):
        return _result(
            PUBLICATION_ATTEMPTED_WRITE_FAILED,
            "PUBLICATION_ATTEMPTED was not durably accepted",
            anchor,
            paths,
            record_writes=record_writes + ([attempted] if attempted is not None else []),
        )
    record_writes.append(attempted)

    try:
        policy_identity = _publication_policy_identity(publication_utility_identities)
        directory_policy_identity = _publication_directory_policy_identity(
            publication_utility_identities
        )
        schema.canonical_json_bytes_bounded(
            bundle_payload,
            schema.MAX_PUBLICATION_SOURCE_BUNDLE_BYTES,
        )
        artifacts = schema.publication_artifact_byte_map_for_bundle(bundle_payload)
        required_staging_bytes = schema.validate_publication_artifact_resource_map(
            artifacts
        )
    except schema.ResourceAdmissibilityError as exc:
        return _resource_result(
            _failure_code(exc),
            str(exc),
            anchor,
            paths,
            record_writes=record_writes,
        )
    except (MemoryError, OverflowError) as exc:
        return _resource_result(
            schema.RESOURCE_ADMISSIBILITY_INDETERMINATE,
            "publication resource admission became indeterminate",
            anchor,
            paths,
            record_writes=record_writes,
        )

    capacity = _validate_staging_capacity_admission(
        staging_capacity_adapter,
        required_staging_bytes,
    )
    if capacity.status != STAGING_CAPACITY_CONFIRMED:
        failure_code = schema.RESOURCE_ADMISSIBILITY_INDETERMINATE
        if capacity.status == STAGING_CAPACITY_UNAVAILABLE:
            failure_code = schema.STAGING_SPACE_BUDGET_UNAVAILABLE
        return _resource_result(
            failure_code,
            capacity.detail,
            anchor,
            paths,
            artifact_sha256s=None,
            record_writes=record_writes,
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
        )

    staging_result = _stage_publication_artifacts(
        paths.staging_directory,
        artifact_bytes_by_name=artifacts,
        bundle_payload=bundle_payload,
        durability_adapter=durability_adapter,
        synthetic_fault_point=synthetic_fault_point,
    )
    if staging_result[0] != PUBLICATION_COMPLETED:
        return _result(
            staging_result[0],
            staging_result[1],
            anchor,
            paths,
            record_writes=record_writes,
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
            directory_durability_failure_code=staging_result[3],
        )
    staging_durability = _sync_directory_target(
        durability_adapter,
        paths.staging_directory,
        schema.STAGING_DIRECTORY,
    )
    if not _directory_durability_confirmed(staging_durability):
        return _result(
            PUBLICATION_STAGING_DURABILITY_UNCONFIRMED,
            "staging directory durability was not confirmed",
            anchor,
            paths,
            artifact_sha256s=None,
            record_writes=record_writes,
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
            directory_durability_failure_code=(
                _directory_durability_failure_code(staging_durability)
            ),
        )
    try:
        observed = _read_artifact_directory(paths.staging_directory)
        staging_hashes = schema.validate_publication_artifact_byte_map(
            observed, bundle_payload=bundle_payload
        )
    except schema.PublicationArtifactError as exc:
        return _result(
            PUBLICATION_VERIFICATION_FAILED,
            str(exc),
            anchor,
            paths,
            record_writes=record_writes,
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
        )
    if paths.final_directory.exists():
        return _result(
            PUBLICATION_FINAL_DIRECTORY_COLLISION,
            "final publication directory already exists",
            anchor,
            paths,
            artifact_sha256s=staging_hashes,
            record_writes=record_writes,
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
        )
    adapter = (
        promotion_adapter
        or windows_adapter.FailClosedSameVolumeNoReplacePromotionAdapter()
    )
    promotion = adapter.promote_verified_directory_no_replace(
        str(paths.staging_directory),
        str(paths.final_directory),
    )
    if promotion.status != windows_adapter.PROMOTION_CONFIRMED:
        classification = PUBLICATION_PROMOTION_FAILED
        if synthetic_fault_point == "promotion_outcome_indeterminate":
            classification = PUBLICATION_PROMOTION_OUTCOME_INDETERMINATE
        return _result(
            classification,
            promotion.detail,
            anchor,
            paths,
            artifact_sha256s=staging_hashes,
            record_writes=record_writes,
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
        )
    try:
        final_bytes = _read_artifact_directory(paths.final_directory)
        final_hashes = schema.validate_publication_artifact_byte_map(
            final_bytes,
            bundle_payload=bundle_payload,
            expected_artifact_sha256s=staging_hashes,
        )
    except schema.PublicationArtifactError as exc:
        return _result(
            PUBLICATION_FINAL_DIRECTORY_INVALID,
            str(exc),
            anchor,
            paths,
            artifact_sha256s=staging_hashes,
            record_writes=record_writes,
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
        )

    if synthetic_fault_point == "publication_completed_write_failure":
        return _result(
            PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED,
            "synthetic PUBLICATION_COMPLETED write failure",
            anchor,
            paths,
            artifact_sha256s=final_hashes,
            record_writes=record_writes,
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
        )
    completed_record = build_publication_completed_logical_record(
        execution_identity=anchor["execution_identity"],
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        predecessor_logical_record_sha256=(
            attempted.logical_record["logical_record_sha256"]
        ),
        artifact_sha256s=final_hashes,
    )
    completed = _write_publication_record(
        paths.chain_directory,
        completed_record,
        writer_attempt_identity=attempts[2],
        durability_adapter=durability_adapter,
    )
    if completed is None or not _durable(completed):
        return _result(
            PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED,
            "PUBLICATION_COMPLETED was not durably accepted",
            anchor,
            paths,
            artifact_sha256s=final_hashes,
            record_writes=record_writes
            + ([completed] if completed is not None else []),
            resource_policy_identity=policy_identity,
            required_staging_bytes=capacity.required_bytes,
            available_staging_bytes=capacity.available_bytes,
            directory_durability_policy_identity=directory_policy_identity,
        )
    record_writes.append(completed)
    return _result(
        PUBLICATION_COMPLETED,
        "publication artifacts projected, promoted, and durably completed",
        anchor,
        paths,
        artifact_sha256s=final_hashes,
        record_writes=record_writes,
        resource_policy_identity=policy_identity,
        required_staging_bytes=capacity.required_bytes,
        available_staging_bytes=capacity.available_bytes,
        directory_durability_policy_identity=directory_policy_identity,
    )


def validate_publication_anchor(
    *,
    bundle_payload: Mapping[str, Any],
    scientific_completion_logical_record: Mapping[str, Any],
    publication_projection_authorization_identity: str,
    publication_utility_identities: Mapping[str, Any],
    expected_publication_projection_identity: str | None = None,
    expected_publication_chain_identity: str | None = None,
) -> dict[str, str]:
    schema.validate_bundle_payload(bundle_payload)
    schema.validate_logical_record(
        scientific_completion_logical_record,
        expected_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
    )
    if scientific_completion_logical_record["record_kind"] != "SCIENTIFIC_COMPLETION":
        raise PublicationEvidenceError("completion anchor is not SCIENTIFIC_COMPLETION")
    completion_payload = scientific_completion_logical_record["payload"]
    schema.validate_scientific_completion_payload(completion_payload)
    _validate_hex64(
        publication_projection_authorization_identity,
        "publication_projection_authorization_identity",
    )
    if not isinstance(publication_utility_identities, Mapping):
        raise PublicationEvidenceError("publication_utility_identities must be an object")
    schema.validate_json_domain(publication_utility_identities)
    _publication_directory_policy_identity(publication_utility_identities)
    _validate_completion_payload_matches_bundle(completion_payload, bundle_payload)
    publication_recipe_identity = bundle_payload["publication_projection_source"][
        "publication_recipe_identity"
    ]
    projection_identity = schema._publication_projection_identity(
        execution_identity=bundle_payload["execution_identity"],
        bundle_payload_sha256=bundle_payload["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=(
            scientific_completion_logical_record["logical_record_sha256"]
        ),
        publication_recipe_identity=publication_recipe_identity,
        publication_utility_identities=publication_utility_identities,
    )
    if (
        expected_publication_projection_identity is not None
        and projection_identity != expected_publication_projection_identity
    ):
        raise PublicationEvidenceError("publication_projection_identity mismatch")
    chain_identity = schema.publication_chain_identity(
        publication_projection_identity=projection_identity,
        publication_projection_authorization_identity=(
            publication_projection_authorization_identity
        ),
    )
    if (
        expected_publication_chain_identity is not None
        and chain_identity != expected_publication_chain_identity
    ):
        raise PublicationEvidenceError("publication_chain_identity mismatch")
    return {
        "execution_identity": bundle_payload["execution_identity"],
        "scientific_execution_authorization_identity": bundle_payload[
            "scientific_execution_authorization_identity"
        ],
        "bundle_payload_sha256": bundle_payload["bundle_payload_sha256"],
        "scientific_completion_logical_record_sha256": (
            scientific_completion_logical_record["logical_record_sha256"]
        ),
        "publication_recipe_identity": publication_recipe_identity,
        "publication_projection_identity": projection_identity,
        "publication_chain_identity": chain_identity,
    }


def _stage_publication_artifacts(
    staging_directory: Path,
    *,
    artifact_bytes_by_name: Mapping[str, bytes],
    bundle_payload: Mapping[str, Any],
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None,
    synthetic_fault_point: str | None,
) -> tuple[str, str, dict[str, str] | None, str | None]:
    if staging_directory.exists():
        return (
            PUBLICATION_STAGING_DIRECTORY_COLLISION,
            "staging directory already exists",
            None,
            None,
        )
    try:
        staging_directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return (
            PUBLICATION_STAGING_DIRECTORY_COLLISION,
            "staging directory already exists",
            None,
            None,
        )
    parent_durability = _sync_directory_target(
        durability_adapter,
        staging_directory.parent,
        schema.STAGING_PARENT_DIRECTORY,
    )
    if not _directory_durability_confirmed(parent_durability):
        return (
            PUBLICATION_STAGING_DURABILITY_UNCONFIRMED,
            "staging parent directory durability was not confirmed",
            None,
            _directory_durability_failure_code(parent_durability),
        )
    artifacts = dict(artifact_bytes_by_name)
    for index, (name, payload) in enumerate(artifacts.items()):
        if synthetic_fault_point == "staging_verification_failure" and index == 2:
            payload = b"synthetic invalid publication artifact\n"
        destination = staging_directory / name
        try:
            with destination.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            return (PUBLICATION_STAGING_INCOMPLETE, str(exc), None, None)
        readback = destination.read_bytes()
        if readback != payload:
            return (
                PUBLICATION_STAGING_INCOMPLETE,
                "staging read-back mismatch",
                None,
                None,
            )
        if synthetic_fault_point == "failure_after_one_artifact" and index == 0:
            return (
                PUBLICATION_STAGING_INCOMPLETE,
                "synthetic failure after one artifact",
                None,
                None,
            )
    if synthetic_fault_point == "failure_after_all_artifacts_before_verification":
        return (
            PUBLICATION_STAGING_INCOMPLETE,
            "synthetic failure before staging verification",
            None,
            None,
        )
    return (PUBLICATION_COMPLETED, "staging artifacts written", None, None)


def _read_artifact_directory(directory_path: Path) -> dict[str, bytes]:
    if not directory_path.exists() or not directory_path.is_dir():
        raise schema.PublicationArtifactError("publication artifact directory is absent")
    names = tuple(sorted(item.name for item in directory_path.iterdir()))
    expected = tuple(sorted(schema.PUBLICATION_ARTIFACT_FILENAMES))
    if names != expected:
        raise schema.PublicationArtifactError("publication artifact inventory mismatch")
    artifacts: dict[str, bytes] = {}
    for name in schema.PUBLICATION_ARTIFACT_FILENAMES:
        limit = schema.MAX_PUBLICATION_RESULT_ARTIFACT_BYTES
        over_limit_code = schema.ARTIFACT_SIZE_LIMIT_EXCEEDED
        if name == schema.PUBLICATION_EXECUTION_ENVELOPE_FILENAME:
            limit = schema.MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES
        elif name == schema.PUBLICATION_SUMMARY_FILENAME:
            limit = schema.MAX_PUBLICATION_SUMMARY_BYTES
            over_limit_code = schema.SUMMARY_SIZE_LIMIT_EXCEEDED
        try:
            artifacts[name] = schema.read_file_bytes_bounded(
                directory_path / name,
                limit,
                over_limit_code=over_limit_code,
            )
        except schema.ResourceAdmissibilityError as exc:
            raise schema.PublicationArtifactError(str(exc)) from exc
    return artifacts


def _write_publication_record(
    directory_path: Path,
    logical_record: dict[str, Any],
    *,
    writer_attempt_identity: str,
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None,
) -> PublicationRecordWriteEvidence | None:
    try:
        stored_record = schema.build_stored_record_object(
            logical_record=logical_record,
            writer_identity=primary_writer.PRIMARY_WRITER_IDENTITY,
            writer_attempt_identity=writer_attempt_identity,
        )
        write_result = primary_writer.write_stored_record_object(
            directory_path,
            stored_record,
            durability_adapter=durability_adapter,
        )
    except (schema.EvidenceValidationError, primary_writer.ImmutableWriteError):
        return None
    return PublicationRecordWriteEvidence(
        logical_record=stored_record["logical_record"],
        stored_record_object=stored_record,
        write_result=write_result,
    )


def _validate_completion_payload_matches_bundle(
    completion_payload: Mapping[str, Any], bundle_payload: Mapping[str, Any]
) -> None:
    expected_pairs = (
        ("scientific_result_kind", "scientific_result_kind"),
        ("bundle_payload_sha256", "bundle_payload_sha256"),
        ("bundle_schema_identity", "bundle_schema_identity"),
        ("two_pass_canonical_identity_status", "two_pass_canonical_identity_status"),
        ("implementation_identities", "implementation_identities"),
        ("configuration_identity", "configuration_identity"),
        ("manifest_identities", "manifest_identities"),
        ("execution_identity", "execution_identity"),
        (
            "scientific_execution_authorization_identity",
            "scientific_execution_authorization_identity",
        ),
        ("protocol_identity", "protocol_identity"),
    )
    for completion_key, bundle_key in expected_pairs:
        if completion_payload[completion_key] != bundle_payload[bundle_key]:
            raise PublicationEvidenceError("%s mismatch" % completion_key)
    if completion_payload["bundle_payload_byte_length"] != len(
        schema.canonical_json_bytes(bundle_payload)
    ):
        raise PublicationEvidenceError("bundle_payload_byte_length mismatch")
    if completion_payload["authority_consumed_status"] != "AUTHORITY_CONSUMED":
        raise PublicationEvidenceError("scientific authority was not consumed")


def _writer_attempts(values: Sequence[str], required: int) -> tuple[str, ...]:
    if len(values) < required:
        raise PublicationEvidenceError("not enough writer attempt identities")
    attempts = tuple(values[:required])
    for index, value in enumerate(attempts):
        _validate_hex32(value, "writer_attempt_identity[%d]" % index)
    return attempts


def _durable(evidence: PublicationRecordWriteEvidence) -> bool:
    return (
        evidence.write_result.authoritative_status == primary_writer.DURABLE_ACCEPTED
        and _directory_policy_identity_matches(
            evidence.write_result.directory_durability_policy_identity
        )
    )


def _result(
    classification: str,
    detail: str,
    anchor: Mapping[str, str],
    paths: PublicationPaths,
    *,
    artifact_sha256s: dict[str, str] | None = None,
    record_writes: Sequence[PublicationRecordWriteEvidence] = (),
    resource_policy_identity: dict[str, Any] | None = None,
    required_staging_bytes: int | None = None,
    available_staging_bytes: int | None = None,
    directory_durability_policy_identity: dict[str, Any] | None = None,
    directory_durability_failure_code: str | None = None,
) -> PublicationProjectionResult:
    return PublicationProjectionResult(
        classification=classification,
        detail=detail,
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        artifact_sha256s=artifact_sha256s,
        paths=paths,
        record_writes=tuple(record_writes),
        authority_state=PUBLICATION_AUTHORITY_CONSUMED,
        resource_policy_identity=resource_policy_identity,
        required_staging_bytes=required_staging_bytes,
        available_staging_bytes=available_staging_bytes,
        directory_durability_policy_identity=(
            directory_durability_policy_identity
        ),
        directory_durability_failure_code=directory_durability_failure_code,
    )


def _resource_result(
    failure_code: str,
    detail: str,
    anchor: Mapping[str, str],
    paths: PublicationPaths,
    *,
    artifact_sha256s: dict[str, str] | None = None,
    record_writes: Sequence[PublicationRecordWriteEvidence] = (),
    resource_policy_identity: dict[str, Any] | None = None,
    required_staging_bytes: int | None = None,
    available_staging_bytes: int | None = None,
    directory_durability_policy_identity: dict[str, Any] | None = None,
    directory_durability_failure_code: str | None = None,
) -> PublicationProjectionResult:
    classification = _J1_RESOURCE_CLASSIFICATIONS[failure_code]
    return PublicationProjectionResult(
        classification=classification,
        detail=_bounded_detail(detail),
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        artifact_sha256s=artifact_sha256s,
        paths=paths,
        record_writes=tuple(record_writes),
        authority_state=PUBLICATION_AUTHORITY_CONSUMED,
        resource_failure_code=failure_code,
        resource_policy_identity=(
            resource_policy_identity or schema.resource_admissibility_policy_identity()
        ),
        required_staging_bytes=required_staging_bytes,
        available_staging_bytes=available_staging_bytes,
        directory_durability_policy_identity=(
            directory_durability_policy_identity
        ),
        directory_durability_failure_code=directory_durability_failure_code,
    )


def _publication_policy_identity(
    publication_utility_identities: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        identity = publication_utility_identities[
            "resource_admissibility_policy_identity"
        ]
    except (KeyError, TypeError) as exc:
        raise schema.ResourcePolicyIdentityMismatchError(
            "resource admissibility policy identity mismatch"
        ) from exc
    schema.validate_resource_admissibility_policy_identity(identity)
    return dict(identity)


def _publication_directory_policy_identity(
    publication_utility_identities: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        identity = publication_utility_identities[
            "directory_durability_policy_identity"
        ]
    except (KeyError, TypeError) as exc:
        raise schema.DirectoryDurabilityPolicyIdentityMismatchError(
            "directory durability policy identity mismatch"
        ) from exc
    schema.validate_directory_durability_policy_identity(identity)
    return dict(identity)


def _sync_directory_target(
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None,
    directory_path: Path,
    target_role: str,
) -> windows_adapter.DirectoryDurabilityResult:
    adapter = durability_adapter or windows_adapter.FailClosedWindowsDurabilityAdapter()
    context = windows_adapter.DirectoryDurabilityContext(target_role=target_role)
    try:
        return adapter.sync_directory_entry(str(directory_path), context=context)
    except Exception as exc:
        return windows_adapter.DirectoryDurabilityResult(
            status=schema.DIRECTORY_DURABILITY_INDETERMINATE,
            detail=str(exc),
            failure_code=schema.UNEXPECTED_EXCEPTION,
            platform=sys.platform,
            adapter_policy_identity=schema.directory_durability_policy_identity(),
            target_role=target_role,
        )


def _directory_durability_confirmed(
    result: windows_adapter.DirectoryDurabilityResult,
) -> bool:
    return (
        result.status == windows_adapter.DIRECTORY_DURABILITY_CONFIRMED
        and result.failure_code is None
        and _directory_policy_identity_matches(result.adapter_policy_identity)
    )


def _directory_durability_failure_code(
    result: windows_adapter.DirectoryDurabilityResult,
) -> str | None:
    if result.failure_code is not None:
        return result.failure_code
    if not _directory_policy_identity_matches(result.adapter_policy_identity):
        return schema.POLICY_IDENTITY_MISMATCH
    return None


def _directory_policy_identity_matches(value: Mapping[str, Any] | None) -> bool:
    try:
        schema.validate_directory_durability_policy_identity(value)
    except schema.EvidenceValidationError:
        return False
    return dict(value) == schema.directory_durability_policy_identity()


def _has_null_policy_identity(publication_utility_identities: Any) -> bool:
    return (
        isinstance(publication_utility_identities, Mapping)
        and "resource_admissibility_policy_identity" in publication_utility_identities
        and publication_utility_identities.get(
            "resource_admissibility_policy_identity"
        )
        is None
    )


def _pre_anchor_resource_result(failure_code: str, detail: str) -> PublicationProjectionResult:
    return PublicationProjectionResult(
        classification=_J1_RESOURCE_CLASSIFICATIONS[failure_code],
        detail=_bounded_detail(detail),
        resource_failure_code=failure_code,
        resource_policy_identity=schema.resource_admissibility_policy_identity(),
    )


def _validate_staging_capacity_admission(
    staging_capacity_adapter: object | None,
    required_bytes: int,
) -> StagingCapacityAdmission:
    if staging_capacity_adapter is None:
        staging_capacity_adapter = FailClosedStagingCapacityAdapter()
    if not hasattr(staging_capacity_adapter, "check_staging_capacity"):
        return StagingCapacityAdmission(
            STAGING_CAPACITY_INDETERMINATE,
            required_bytes,
            None,
            "staging capacity adapter is malformed",
        )
    try:
        response = staging_capacity_adapter.check_staging_capacity(
            required_bytes=required_bytes
        )
    except (MemoryError, OverflowError):
        return StagingCapacityAdmission(
            STAGING_CAPACITY_INDETERMINATE,
            required_bytes,
            None,
            "staging capacity admission became indeterminate",
        )
    return _validate_staging_capacity_response(response, required_bytes)


def _validate_staging_capacity_response(
    response: Any,
    required_bytes: int,
) -> StagingCapacityAdmission:
    if not isinstance(response, Mapping):
        return StagingCapacityAdmission(
            STAGING_CAPACITY_INDETERMINATE,
            required_bytes,
            None,
            "staging capacity response is malformed",
        )
    if tuple(response.keys()) != _STAGING_CAPACITY_RESPONSE_KEYS:
        return StagingCapacityAdmission(
            STAGING_CAPACITY_INDETERMINATE,
            required_bytes,
            None,
            "staging capacity response field set is malformed",
        )
    status = response["status"]
    returned_required = response["required_bytes"]
    available = response["available_bytes"]
    detail = response["detail"]
    if status not in (
        STAGING_CAPACITY_CONFIRMED,
        STAGING_CAPACITY_UNAVAILABLE,
        STAGING_CAPACITY_INDETERMINATE,
    ):
        return _indeterminate_capacity(required_bytes, "unknown staging capacity status")
    if type(returned_required) is not int or returned_required < 0:
        return _indeterminate_capacity(required_bytes, "invalid required staging bytes")
    if returned_required != required_bytes:
        return _indeterminate_capacity(required_bytes, "required staging bytes mismatch")
    if not isinstance(detail, str):
        return _indeterminate_capacity(required_bytes, "invalid staging capacity detail")
    bounded_detail = _bounded_detail(detail)
    if status == STAGING_CAPACITY_INDETERMINATE:
        if available is not None:
            return _indeterminate_capacity(
                required_bytes,
                "indeterminate capacity must not report available bytes",
            )
        return StagingCapacityAdmission(status, required_bytes, None, bounded_detail)
    if type(available) is not int or available < 0:
        return _indeterminate_capacity(required_bytes, "invalid available staging bytes")
    if status == STAGING_CAPACITY_CONFIRMED and available < required_bytes:
        return _indeterminate_capacity(
            required_bytes,
            "confirmed capacity is below required bytes",
        )
    if status == STAGING_CAPACITY_UNAVAILABLE and available >= required_bytes:
        return _indeterminate_capacity(
            required_bytes,
            "unavailable capacity is not below required bytes",
        )
    return StagingCapacityAdmission(status, required_bytes, available, bounded_detail)


def _indeterminate_capacity(
    required_bytes: int,
    detail: str,
) -> StagingCapacityAdmission:
    return StagingCapacityAdmission(
        STAGING_CAPACITY_INDETERMINATE,
        required_bytes,
        None,
        detail,
    )


def _failure_code(exc: schema.ResourceAdmissibilityError) -> str:
    return getattr(exc, "failure_code", schema.RESOURCE_LIMIT_EXCEEDED)


def _bounded_detail(detail: str) -> str:
    text = str(detail)
    if len(text) > 200:
        return text[:200]
    return text


def _validated_root(root_path: str | Path) -> Path:
    root = Path(root_path)
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise PublicationEvidenceError("publication root does not exist") from exc
    if not resolved.is_dir():
        raise PublicationEvidenceError("publication root must be a directory")
    if root.is_symlink() or resolved.is_symlink():
        raise PublicationEvidenceError("publication root must not be a symlink")
    return resolved


def _owned_child(root: Path, namespace: str, leaf: str) -> Path:
    _validate_hex64(leaf, "chain leaf")
    target = root / namespace / leaf
    parent = target.parent.resolve(strict=False)
    if not _is_relative_to(parent, root):
        raise PublicationEvidenceError("publication path escapes supplied root")
    for existing_parent in (root / namespace, target):
        if existing_parent.exists() and existing_parent.is_symlink():
            raise PublicationEvidenceError("publication path has symlink ambiguity")
    return target


def _is_relative_to(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_hex64(value: object, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise PublicationEvidenceError("%s must be lowercase 64-hex" % label)
    if any(char not in "0123456789abcdef" for char in value):
        raise PublicationEvidenceError("%s must be lowercase 64-hex" % label)


def _validate_hex32(value: object, label: str) -> None:
    if not isinstance(value, str) or len(value) != 32:
        raise PublicationEvidenceError("%s must be lowercase 32-hex" % label)
    if any(char not in "0123456789abcdef" for char in value):
        raise PublicationEvidenceError("%s must be lowercase 32-hex" % label)
