from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import durable_evidence_primary_writer_v0_3 as primary_writer
import durable_evidence_publication_replay_v0_3 as publication_replay
import durable_evidence_schema_v0_3 as schema


PUBLICATION_RECOVERY_AUTHORITY_NOT_ATTEMPTED = (
    "PUBLICATION_RECOVERY_AUTHORITY_NOT_ATTEMPTED"
)
PUBLICATION_RECOVERY_AUTHORITY_CONSUMED = "PUBLICATION_RECOVERY_AUTHORITY_CONSUMED"
PUBLICATION_RECOVERY_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED = (
    "PUBLICATION_RECOVERY_AUTHORITY_CONSUMPTION_ATTEMPT_FAILED"
)
PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE = (
    "PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE"
)

PUBLICATION_RECOVERY_EVIDENCE_COMPLETED = "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED"
PUBLICATION_RECOVERY_AUTHORIZATION_VALIDATION_FAILED = (
    "PUBLICATION_RECOVERY_AUTHORIZATION_VALIDATION_FAILED"
)
PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED = (
    "PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED"
)
PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH = (
    "PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH"
)
PUBLICATION_RECOVERY_FINAL_DIRECTORY_MISSING = (
    "PUBLICATION_RECOVERY_FINAL_DIRECTORY_MISSING"
)
PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID = (
    "PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID"
)
PUBLICATION_RECOVERY_ARTIFACT_HASH_MISMATCH = (
    "PUBLICATION_RECOVERY_ARTIFACT_HASH_MISMATCH"
)
PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED = (
    "PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED"
)
PUBLICATION_RECOVERY_CHAIN_FORK = "PUBLICATION_RECOVERY_CHAIN_FORK"

PUBLICATION_CHAIN_ROOT = ".iososv_v0_3.publication_chain"
PUBLICATION_FINAL_ROOT = "iososv_v0_3.publication"
PUBLICATION_RECOVERY_CHAIN_ROOT = ".iososv_v0_3.publication_recovery_chain"

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


class PublicationRecoveryEvidenceError(ValueError):
    pass


class PublicationRecoveryAuthorityReuseDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class PublicationRecoveryBeginState:
    execution_identity: str
    original_publication_chain_identity: str
    publication_recovery_authorization_identity: str
    publication_recovery_chain_identity: str
    state: str
    reuse_permission_consumed: bool
    protected_mutation_permitted: bool


@dataclass(frozen=True)
class PublicationRecoveryRecordWriteEvidence:
    logical_record: dict[str, Any]
    stored_record_object: dict[str, Any]
    write_result: primary_writer.ImmutableWriteResult


@dataclass(frozen=True)
class PublicationRecoveryPaths:
    original_publication_chain_directory: Path
    final_publication_directory: Path
    recovery_chain_directory: Path


@dataclass(frozen=True)
class PublicationRecoveryResult:
    classification: str
    detail: str
    publication_recovery_chain_identity: str | None = None
    original_publication_chain_identity: str | None = None
    verified_artifact_sha256s: dict[str, str] | None = None
    record_writes: tuple[PublicationRecoveryRecordWriteEvidence, ...] = ()
    paths: PublicationRecoveryPaths | None = None
    authority_state: str = PUBLICATION_RECOVERY_AUTHORITY_NOT_ATTEMPTED
    original_publication_completed_normally: bool = False


class SyntheticPublicationRecoveryContext:
    """Live synthetic guard for single-use recovery authorization."""

    def __init__(self) -> None:
        self._begun_authorizations: set[str] = set()
        self._begun_chains: set[tuple[str, str, str]] = set()

    def begin_once(
        self,
        *,
        execution_identity: str,
        original_publication_chain_identity: str,
        publication_recovery_authorization_identity: str,
        publication_recovery_chain_identity: str,
    ) -> None:
        chain_key = (
            execution_identity,
            original_publication_chain_identity,
            publication_recovery_chain_identity,
        )
        if (
            publication_recovery_authorization_identity in self._begun_authorizations
            or chain_key in self._begun_chains
        ):
            raise PublicationRecoveryAuthorityReuseDenied(
                "publication recovery authorization reuse is denied"
            )
        self._begun_authorizations.add(publication_recovery_authorization_identity)
        self._begun_chains.add(chain_key)


class SyntheticPublicationRecoveryInvocation:
    def __init__(
        self,
        *,
        execution_identity: str,
        original_publication_chain_identity: str,
        publication_recovery_authorization_identity: str,
        publication_recovery_chain_identity: str,
        context: SyntheticPublicationRecoveryContext,
    ) -> None:
        _validate_hex64(execution_identity, "execution_identity")
        _validate_hex64(
            original_publication_chain_identity,
            "original_publication_chain_identity",
        )
        _validate_hex64(
            publication_recovery_authorization_identity,
            "publication_recovery_authorization_identity",
        )
        _validate_hex64(
            publication_recovery_chain_identity,
            "publication_recovery_chain_identity",
        )
        if not isinstance(context, SyntheticPublicationRecoveryContext):
            raise PublicationRecoveryEvidenceError(
                "SyntheticPublicationRecoveryContext is required"
            )
        self.execution_identity = execution_identity
        self.original_publication_chain_identity = original_publication_chain_identity
        self.publication_recovery_authorization_identity = (
            publication_recovery_authorization_identity
        )
        self.publication_recovery_chain_identity = publication_recovery_chain_identity
        self._context = context
        self._begun = False

    @property
    def live_state(self) -> str:
        if self._begun:
            return PUBLICATION_RECOVERY_AUTHORITY_CONSUMED
        return PUBLICATION_RECOVERY_AUTHORITY_NOT_ATTEMPTED

    def begin(self) -> PublicationRecoveryBeginState:
        if self._begun:
            raise PublicationRecoveryAuthorityReuseDenied(
                "publication recovery authorization reuse is denied"
            )
        self._context.begin_once(
            execution_identity=self.execution_identity,
            original_publication_chain_identity=(
                self.original_publication_chain_identity
            ),
            publication_recovery_authorization_identity=(
                self.publication_recovery_authorization_identity
            ),
            publication_recovery_chain_identity=self.publication_recovery_chain_identity,
        )
        self._begun = True
        return PublicationRecoveryBeginState(
            execution_identity=self.execution_identity,
            original_publication_chain_identity=(
                self.original_publication_chain_identity
            ),
            publication_recovery_authorization_identity=(
                self.publication_recovery_authorization_identity
            ),
            publication_recovery_chain_identity=self.publication_recovery_chain_identity,
            state=PUBLICATION_RECOVERY_AUTHORITY_CONSUMED,
            reuse_permission_consumed=True,
            protected_mutation_permitted=True,
        )


def recovery_paths(
    root_path: str | Path,
    *,
    original_publication_chain_identity: str,
    publication_recovery_chain_identity: str,
) -> PublicationRecoveryPaths:
    _validate_hex64(
        original_publication_chain_identity, "original_publication_chain_identity"
    )
    _validate_hex64(
        publication_recovery_chain_identity, "publication_recovery_chain_identity"
    )
    root = _validated_root(root_path)
    return PublicationRecoveryPaths(
        original_publication_chain_directory=_owned_child(
            root, PUBLICATION_CHAIN_ROOT, original_publication_chain_identity
        ),
        final_publication_directory=_owned_child(
            root, PUBLICATION_FINAL_ROOT, original_publication_chain_identity
        ),
        recovery_chain_directory=_owned_child(
            root, PUBLICATION_RECOVERY_CHAIN_ROOT, publication_recovery_chain_identity
        ),
    )


def verify_publication_recovery(
    *,
    root_path: str | Path,
    bundle_payload: Mapping[str, Any],
    scientific_completion_logical_record: Mapping[str, Any],
    original_publication_projection_authorization_identity: str,
    original_publication_projection_identity: str,
    original_publication_chain_identity: str,
    publication_recovery_authorization_identity: str,
    expected_final_artifact_sha256s: Mapping[str, str],
    publication_recovery_utility_identity: Mapping[str, Any],
    context: SyntheticPublicationRecoveryContext,
    durability_adapter: object | None = None,
    writer_attempt_identities: Sequence[str] = (
        "4" * 32,
        "5" * 32,
        "6" * 32,
        "7" * 32,
    ),
    expected_publication_recovery_chain_identity: str | None = None,
    synthetic_fault_point: str | None = None,
) -> PublicationRecoveryResult:
    try:
        anchor = validate_publication_recovery_anchor(
            bundle_payload=bundle_payload,
            scientific_completion_logical_record=scientific_completion_logical_record,
            original_publication_projection_authorization_identity=(
                original_publication_projection_authorization_identity
            ),
            original_publication_projection_identity=(
                original_publication_projection_identity
            ),
            original_publication_chain_identity=original_publication_chain_identity,
            publication_recovery_authorization_identity=(
                publication_recovery_authorization_identity
            ),
            expected_final_artifact_sha256s=expected_final_artifact_sha256s,
            publication_recovery_utility_identity=(
                publication_recovery_utility_identity
            ),
            expected_publication_recovery_chain_identity=(
                expected_publication_recovery_chain_identity
            ),
        )
        attempts = _writer_attempts(writer_attempt_identities, 4)
        paths = recovery_paths(
            root_path,
            original_publication_chain_identity=original_publication_chain_identity,
            publication_recovery_chain_identity=(
                anchor["publication_recovery_chain_identity"]
            ),
        )
    except (schema.EvidenceValidationError, PublicationRecoveryEvidenceError) as exc:
        return PublicationRecoveryResult(
            classification=PUBLICATION_RECOVERY_AUTHORIZATION_VALIDATION_FAILED,
            detail=str(exc),
        )

    invocation = SyntheticPublicationRecoveryInvocation(
        execution_identity=anchor["execution_identity"],
        original_publication_chain_identity=original_publication_chain_identity,
        publication_recovery_authorization_identity=(
            publication_recovery_authorization_identity
        ),
        publication_recovery_chain_identity=(
            anchor["publication_recovery_chain_identity"]
        ),
        context=context,
    )
    invocation.begin()
    if synthetic_fault_point == "recovery_authority_genesis_write_failure":
        return _result(
            PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED,
            "synthetic recovery genesis write failure",
            anchor,
            paths,
        )
    if paths.recovery_chain_directory.exists():
        return _result(
            PUBLICATION_RECOVERY_CHAIN_FORK,
            "publication recovery chain directory already exists",
            anchor,
            paths,
        )
    try:
        paths.recovery_chain_directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return _result(
            PUBLICATION_RECOVERY_CHAIN_FORK,
            "publication recovery chain directory already exists",
            anchor,
            paths,
        )

    record_writes: list[PublicationRecoveryRecordWriteEvidence] = []
    genesis_record = build_recovery_authority_accepted_logical_record(
        anchor=anchor,
        expected_final_artifact_sha256s=expected_final_artifact_sha256s,
        final_publication_directory=paths.final_publication_directory,
        publication_recovery_utility_identity=publication_recovery_utility_identity,
    )
    genesis = _write_recovery_record(
        paths.recovery_chain_directory,
        genesis_record,
        writer_attempt_identity=attempts[0],
        durability_adapter=durability_adapter,
    )
    if genesis is None or not _durable(genesis):
        return _result(
            PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED,
            "PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED was not durably accepted",
            anchor,
            paths,
            record_writes=record_writes + ([genesis] if genesis is not None else []),
        )
    record_writes.append(genesis)
    if synthetic_fault_point == "publication_recovery_attempted_write_failure":
        return _result(
            PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED,
            "synthetic PUBLICATION_RECOVERY_ATTEMPTED write failure",
            anchor,
            paths,
            record_writes=record_writes,
        )
    attempted_record = build_recovery_attempted_logical_record(
        anchor=anchor,
        predecessor_logical_record_sha256=genesis.logical_record[
            "logical_record_sha256"
        ],
    )
    attempted = _write_recovery_record(
        paths.recovery_chain_directory,
        attempted_record,
        writer_attempt_identity=attempts[1],
        durability_adapter=durability_adapter,
    )
    if attempted is None or not _durable(attempted):
        return _result(
            PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED,
            "PUBLICATION_RECOVERY_ATTEMPTED was not durably accepted",
            anchor,
            paths,
            record_writes=record_writes + ([attempted] if attempted is not None else []),
        )
    record_writes.append(attempted)

    if not paths.original_publication_chain_directory.exists():
        return _result(
            PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH,
            "original publication chain directory is absent",
            anchor,
            paths,
            record_writes=record_writes,
        )
    original_replay = _classify_original_publication_chain(paths, anchor)
    if original_replay.classification in (
        publication_replay.PUBLICATION_CHAIN_FORK,
        publication_replay.PUBLICATION_CHAIN_REPLAY_FAILED,
        publication_replay.PUBLICATION_TRANSITION_ORDER_INVALID,
        publication_replay.PUBLICATION_EVIDENCE_CONTRADICTORY,
    ):
        return _result(
            PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH,
            original_replay.detail,
            anchor,
            paths,
            record_writes=record_writes,
        )
    if len(original_replay.accepted_records) < 2:
        return _result(
            PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH,
            "original publication chain has no durable attempted prefix",
            anchor,
            paths,
            record_writes=record_writes,
        )
    if not paths.final_publication_directory.exists():
        return _result(
            PUBLICATION_RECOVERY_FINAL_DIRECTORY_MISSING,
            "final publication directory is absent",
            anchor,
            paths,
            record_writes=record_writes,
        )
    try:
        final_bytes = _read_final_artifact_directory(paths.final_publication_directory)
        verified_hashes = schema.validate_publication_artifact_byte_map(
            final_bytes,
            bundle_payload=bundle_payload,
            expected_artifact_sha256s=expected_final_artifact_sha256s,
        )
    except schema.PublicationArtifactHashError as exc:
        return _result(
            PUBLICATION_RECOVERY_ARTIFACT_HASH_MISMATCH,
            str(exc),
            anchor,
            paths,
            record_writes=record_writes,
        )
    except schema.PublicationArtifactError as exc:
        return _result(
            PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID,
            str(exc),
            anchor,
            paths,
            record_writes=record_writes,
        )

    if synthetic_fault_point == "publication_recovery_artifacts_verified_write_failure":
        return _result(
            PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED,
            "synthetic PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED write failure",
            anchor,
            paths,
            verified_artifact_sha256s=verified_hashes,
            record_writes=record_writes,
        )
    artifacts_verified_record = build_recovery_artifacts_verified_logical_record(
        anchor=anchor,
        predecessor_logical_record_sha256=attempted.logical_record[
            "logical_record_sha256"
        ],
        final_publication_directory=paths.final_publication_directory,
        verified_final_artifacts=verified_hashes,
    )
    artifacts_verified = _write_recovery_record(
        paths.recovery_chain_directory,
        artifacts_verified_record,
        writer_attempt_identity=attempts[2],
        durability_adapter=durability_adapter,
    )
    if artifacts_verified is None or not _durable(artifacts_verified):
        return _result(
            PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED,
            "PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED was not durably accepted",
            anchor,
            paths,
            verified_artifact_sha256s=verified_hashes,
            record_writes=record_writes
            + ([artifacts_verified] if artifacts_verified is not None else []),
        )
    record_writes.append(artifacts_verified)
    if synthetic_fault_point == "publication_recovery_evidence_completed_write_failure":
        return _result(
            PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED,
            "synthetic PUBLICATION_RECOVERY_EVIDENCE_COMPLETED write failure",
            anchor,
            paths,
            verified_artifact_sha256s=verified_hashes,
            record_writes=record_writes,
        )
    evidence_completed_record = build_recovery_evidence_completed_logical_record(
        anchor=anchor,
        predecessor_logical_record_sha256=artifacts_verified.logical_record[
            "logical_record_sha256"
        ],
    )
    evidence_completed = _write_recovery_record(
        paths.recovery_chain_directory,
        evidence_completed_record,
        writer_attempt_identity=attempts[3],
        durability_adapter=durability_adapter,
    )
    if evidence_completed is None or not _durable(evidence_completed):
        return _result(
            PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED,
            "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED was not durably accepted",
            anchor,
            paths,
            verified_artifact_sha256s=verified_hashes,
            record_writes=record_writes
            + ([evidence_completed] if evidence_completed is not None else []),
        )
    record_writes.append(evidence_completed)
    return _result(
        PUBLICATION_RECOVERY_EVIDENCE_COMPLETED,
        "already-existing final artifacts verified under recovery evidence",
        anchor,
        paths,
        verified_artifact_sha256s=verified_hashes,
        record_writes=record_writes,
        original_publication_completed_normally=(
            original_replay.classification == publication_replay.PUBLICATION_COMPLETED
        ),
    )


def validate_publication_recovery_anchor(
    *,
    bundle_payload: Mapping[str, Any],
    scientific_completion_logical_record: Mapping[str, Any],
    original_publication_projection_authorization_identity: str,
    original_publication_projection_identity: str,
    original_publication_chain_identity: str,
    publication_recovery_authorization_identity: str,
    expected_final_artifact_sha256s: Mapping[str, str],
    publication_recovery_utility_identity: Mapping[str, Any],
    expected_publication_recovery_chain_identity: str | None = None,
) -> dict[str, str]:
    schema.validate_bundle_payload(bundle_payload)
    schema.validate_logical_record(
        scientific_completion_logical_record,
        expected_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
    )
    if scientific_completion_logical_record["record_kind"] != "SCIENTIFIC_COMPLETION":
        raise PublicationRecoveryEvidenceError(
            "completion anchor is not SCIENTIFIC_COMPLETION"
        )
    completion_payload = scientific_completion_logical_record["payload"]
    schema.validate_scientific_completion_payload(completion_payload)
    _validate_completion_payload_matches_bundle(completion_payload, bundle_payload)
    _validate_hex64(
        original_publication_projection_authorization_identity,
        "original_publication_projection_authorization_identity",
    )
    _validate_hex64(
        original_publication_projection_identity,
        "original_publication_projection_identity",
    )
    _validate_hex64(
        original_publication_chain_identity,
        "original_publication_chain_identity",
    )
    _validate_hex64(
        publication_recovery_authorization_identity,
        "publication_recovery_authorization_identity",
    )
    schema.validate_publication_artifact_sha256s(expected_final_artifact_sha256s)
    if not isinstance(publication_recovery_utility_identity, Mapping):
        raise PublicationRecoveryEvidenceError(
            "publication_recovery_utility_identity must be an object"
        )
    schema.validate_json_domain(publication_recovery_utility_identity)
    recovery_chain_identity = schema.publication_recovery_chain_identity(
        original_publication_chain_identity=original_publication_chain_identity,
        publication_recovery_authorization_identity=(
            publication_recovery_authorization_identity
        ),
    )
    if (
        expected_publication_recovery_chain_identity is not None
        and recovery_chain_identity != expected_publication_recovery_chain_identity
    ):
        raise PublicationRecoveryEvidenceError(
            "publication_recovery_chain_identity mismatch"
        )
    return {
        "execution_identity": bundle_payload["execution_identity"],
        "scientific_execution_authorization_identity": bundle_payload[
            "scientific_execution_authorization_identity"
        ],
        "bundle_payload_sha256": bundle_payload["bundle_payload_sha256"],
        "scientific_completion_logical_record_sha256": (
            scientific_completion_logical_record["logical_record_sha256"]
        ),
        "original_publication_projection_authorization_identity": (
            original_publication_projection_authorization_identity
        ),
        "original_publication_projection_identity": (
            original_publication_projection_identity
        ),
        "original_publication_chain_identity": original_publication_chain_identity,
        "publication_recovery_authorization_identity": (
            publication_recovery_authorization_identity
        ),
        "publication_recovery_chain_identity": recovery_chain_identity,
    }


def build_recovery_authority_accepted_logical_record(
    *,
    anchor: Mapping[str, str],
    expected_final_artifact_sha256s: Mapping[str, str],
    final_publication_directory: Path,
    publication_recovery_utility_identity: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "execution_identity": anchor["execution_identity"],
        "scientific_execution_authorization_identity": anchor[
            "scientific_execution_authorization_identity"
        ],
        "bundle_payload_sha256": anchor["bundle_payload_sha256"],
        "scientific_completion_logical_record_sha256": anchor[
            "scientific_completion_logical_record_sha256"
        ],
        "original_publication_projection_authorization_identity": anchor[
            "original_publication_projection_authorization_identity"
        ],
        "original_publication_projection_identity": anchor[
            "original_publication_projection_identity"
        ],
        "original_publication_chain_identity": anchor[
            "original_publication_chain_identity"
        ],
        "publication_recovery_authorization_identity": anchor[
            "publication_recovery_authorization_identity"
        ],
        "publication_recovery_chain_identity": anchor[
            "publication_recovery_chain_identity"
        ],
        "expected_final_artifacts": _ordered_artifact_sha256s(
            expected_final_artifact_sha256s
        ),
        "final_publication_directory": str(final_publication_directory),
        "publication_recovery_utility_identity": dict(
            publication_recovery_utility_identity
        ),
    }
    if tuple(payload.keys()) != _RECOVERY_AUTHORITY_PAYLOAD_KEYS:
        raise PublicationRecoveryEvidenceError("recovery genesis payload mismatch")
    return schema.build_publication_recovery_logical_record(
        record_kind="PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED",
        sequence_number=0,
        execution_identity=anchor["execution_identity"],
        publication_recovery_authorization_identity=anchor[
            "publication_recovery_authorization_identity"
        ],
        publication_recovery_chain_identity=anchor[
            "publication_recovery_chain_identity"
        ],
        predecessor_logical_record_sha256=(
            schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256
        ),
        payload=payload,
    )


def build_recovery_attempted_logical_record(
    *,
    anchor: Mapping[str, str],
    predecessor_logical_record_sha256: str,
) -> dict[str, Any]:
    payload = {
        "original_publication_chain_identity": anchor[
            "original_publication_chain_identity"
        ],
        "publication_recovery_chain_identity": anchor[
            "publication_recovery_chain_identity"
        ],
    }
    return schema.build_publication_recovery_logical_record(
        record_kind="PUBLICATION_RECOVERY_ATTEMPTED",
        sequence_number=1,
        execution_identity=anchor["execution_identity"],
        publication_recovery_authorization_identity=anchor[
            "publication_recovery_authorization_identity"
        ],
        publication_recovery_chain_identity=anchor[
            "publication_recovery_chain_identity"
        ],
        predecessor_logical_record_sha256=predecessor_logical_record_sha256,
        payload=payload,
    )


def build_recovery_artifacts_verified_logical_record(
    *,
    anchor: Mapping[str, str],
    predecessor_logical_record_sha256: str,
    final_publication_directory: Path,
    verified_final_artifacts: Mapping[str, str],
) -> dict[str, Any]:
    schema.validate_publication_artifact_sha256s(verified_final_artifacts)
    payload = {
        "original_publication_chain_identity": anchor[
            "original_publication_chain_identity"
        ],
        "final_publication_directory": str(final_publication_directory),
        "verified_final_artifacts": _ordered_artifact_sha256s(
            verified_final_artifacts
        ),
        "artifact_source": "already_existing_final_publication_directory",
    }
    if tuple(payload.keys()) != _RECOVERY_ARTIFACTS_VERIFIED_PAYLOAD_KEYS:
        raise PublicationRecoveryEvidenceError("artifacts-verified payload mismatch")
    return schema.build_publication_recovery_logical_record(
        record_kind="PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED",
        sequence_number=2,
        execution_identity=anchor["execution_identity"],
        publication_recovery_authorization_identity=anchor[
            "publication_recovery_authorization_identity"
        ],
        publication_recovery_chain_identity=anchor[
            "publication_recovery_chain_identity"
        ],
        predecessor_logical_record_sha256=predecessor_logical_record_sha256,
        payload=payload,
    )


def build_recovery_evidence_completed_logical_record(
    *,
    anchor: Mapping[str, str],
    predecessor_logical_record_sha256: str,
) -> dict[str, Any]:
    payload = {
        "original_publication_chain_identity": anchor[
            "original_publication_chain_identity"
        ],
        "publication_recovery_chain_identity": anchor[
            "publication_recovery_chain_identity"
        ],
        "recovery_semantics": (
            "final_artifacts_verified_under_separate_recovery_evidence_only"
        ),
    }
    if tuple(payload.keys()) != _RECOVERY_EVIDENCE_COMPLETED_PAYLOAD_KEYS:
        raise PublicationRecoveryEvidenceError("evidence-completed payload mismatch")
    return schema.build_publication_recovery_logical_record(
        record_kind="PUBLICATION_RECOVERY_EVIDENCE_COMPLETED",
        sequence_number=3,
        execution_identity=anchor["execution_identity"],
        publication_recovery_authorization_identity=anchor[
            "publication_recovery_authorization_identity"
        ],
        publication_recovery_chain_identity=anchor[
            "publication_recovery_chain_identity"
        ],
        predecessor_logical_record_sha256=predecessor_logical_record_sha256,
        payload=payload,
    )


def _classify_original_publication_chain(
    paths: PublicationRecoveryPaths, anchor: Mapping[str, str]
) -> publication_replay.PublicationReplayResult:
    return publication_replay.replay_publication_chain(
        paths.original_publication_chain_directory,
        expected_execution_identity=anchor["execution_identity"],
        publication_projection_authorization_identity=anchor[
            "original_publication_projection_authorization_identity"
        ],
        publication_chain_identity=anchor["original_publication_chain_identity"],
        publication_projection_identity=anchor[
            "original_publication_projection_identity"
        ],
        bundle_payload_sha256=anchor["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=anchor[
            "scientific_completion_logical_record_sha256"
        ],
    )


def _read_final_artifact_directory(directory_path: Path) -> dict[str, bytes]:
    if not directory_path.exists() or not directory_path.is_dir():
        raise schema.PublicationArtifactError("final publication directory is absent")
    names = tuple(sorted(item.name for item in directory_path.iterdir()))
    expected = tuple(sorted(schema.PUBLICATION_ARTIFACT_FILENAMES))
    if names != expected:
        raise schema.PublicationArtifactError("final publication inventory mismatch")
    return {
        name: (directory_path / name).read_bytes()
        for name in schema.PUBLICATION_ARTIFACT_FILENAMES
    }


def _write_recovery_record(
    directory_path: Path,
    logical_record: dict[str, Any],
    *,
    writer_attempt_identity: str,
    durability_adapter: object | None,
) -> PublicationRecoveryRecordWriteEvidence | None:
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
    return PublicationRecoveryRecordWriteEvidence(
        logical_record=stored_record["logical_record"],
        stored_record_object=stored_record,
        write_result=write_result,
    )


def _validate_completion_payload_matches_bundle(
    completion_payload: Mapping[str, Any], bundle_payload: Mapping[str, Any]
) -> None:
    for key in (
        "scientific_result_kind",
        "bundle_payload_sha256",
        "two_pass_canonical_identity_status",
        "implementation_identities",
        "configuration_identity",
        "manifest_identities",
        "execution_identity",
        "scientific_execution_authorization_identity",
        "protocol_identity",
    ):
        if completion_payload[key] != bundle_payload[key]:
            raise PublicationRecoveryEvidenceError("%s mismatch" % key)
    if completion_payload["bundle_schema_identity"] != bundle_payload[
        "bundle_schema_identity"
    ]:
        raise PublicationRecoveryEvidenceError("bundle schema mismatch")
    if completion_payload["bundle_payload_byte_length"] != len(
        schema.canonical_json_bytes(bundle_payload)
    ):
        raise PublicationRecoveryEvidenceError("bundle byte length mismatch")
    if completion_payload["authority_consumed_status"] != "AUTHORITY_CONSUMED":
        raise PublicationRecoveryEvidenceError("scientific authority was not consumed")


def _ordered_artifact_sha256s(values: Mapping[str, str]) -> dict[str, str]:
    schema.validate_publication_artifact_sha256s(values)
    return {name: values[name] for name in schema.PUBLICATION_ARTIFACT_FILENAMES}


def _writer_attempts(values: Sequence[str], required: int) -> tuple[str, ...]:
    if len(values) < required:
        raise PublicationRecoveryEvidenceError("not enough writer attempt identities")
    attempts = tuple(values[:required])
    for index, value in enumerate(attempts):
        _validate_hex32(value, "writer_attempt_identity[%d]" % index)
    return attempts


def _durable(evidence: PublicationRecoveryRecordWriteEvidence) -> bool:
    return evidence.write_result.authoritative_status == primary_writer.DURABLE_ACCEPTED


def _result(
    classification: str,
    detail: str,
    anchor: Mapping[str, str],
    paths: PublicationRecoveryPaths,
    *,
    verified_artifact_sha256s: dict[str, str] | None = None,
    record_writes: Sequence[PublicationRecoveryRecordWriteEvidence] = (),
    original_publication_completed_normally: bool = False,
) -> PublicationRecoveryResult:
    return PublicationRecoveryResult(
        classification=classification,
        detail=detail,
        publication_recovery_chain_identity=anchor[
            "publication_recovery_chain_identity"
        ],
        original_publication_chain_identity=anchor[
            "original_publication_chain_identity"
        ],
        verified_artifact_sha256s=verified_artifact_sha256s,
        record_writes=tuple(record_writes),
        paths=paths,
        authority_state=PUBLICATION_RECOVERY_AUTHORITY_CONSUMED,
        original_publication_completed_normally=(
            original_publication_completed_normally
        ),
    )


def _validated_root(root_path: str | Path) -> Path:
    root = Path(root_path)
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise PublicationRecoveryEvidenceError("recovery root does not exist") from exc
    if not resolved.is_dir():
        raise PublicationRecoveryEvidenceError("recovery root must be a directory")
    if root.is_symlink() or resolved.is_symlink():
        raise PublicationRecoveryEvidenceError("recovery root must not be a symlink")
    return resolved


def _owned_child(root: Path, namespace: str, leaf: str) -> Path:
    _validate_hex64(leaf, "chain leaf")
    target = root / namespace / leaf
    parent = target.parent.resolve(strict=False)
    if not _is_relative_to(parent, root):
        raise PublicationRecoveryEvidenceError("recovery path escapes supplied root")
    for existing_parent in (root / namespace, target):
        if existing_parent.exists() and existing_parent.is_symlink():
            raise PublicationRecoveryEvidenceError(
                "recovery path has symlink ambiguity"
            )
    return target


def _is_relative_to(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_hex64(value: object, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise PublicationRecoveryEvidenceError(
            "%s must be lowercase 64-hex" % label
        )
    if any(char not in "0123456789abcdef" for char in value):
        raise PublicationRecoveryEvidenceError(
            "%s must be lowercase 64-hex" % label
        )


def _validate_hex32(value: object, label: str) -> None:
    if not isinstance(value, str) or len(value) != 32:
        raise PublicationRecoveryEvidenceError(
            "%s must be lowercase 32-hex" % label
        )
    if any(char not in "0123456789abcdef" for char in value):
        raise PublicationRecoveryEvidenceError(
            "%s must be lowercase 32-hex" % label
        )
