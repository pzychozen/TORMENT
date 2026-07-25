from __future__ import annotations

from pathlib import Path

import pytest

import durable_evidence_durability_v0_3 as durability
import durable_evidence_publication_recovery_replay_v0_3 as recovery_replay
import durable_evidence_publication_recovery_v0_3 as recovery
import durable_evidence_schema_v0_3 as schema
import durable_evidence_primary_writer_v0_3 as writer

from test_durable_evidence_publication_recovery_v0_3 import (
    RECOVERY_AUTHORITY,
    recovery_ledger,
    recovery_utility_identity,
    run_recovery,
    setup_final_artifacts_with_incomplete_publication_chain,
)
from test_durable_evidence_publication_v0_3 import (
    ConfirmedSyntheticAdapter,
    EXECUTION_IDENTITY,
    PUBLICATION_AUTHORITY,
)


def _write_record(path: Path, logical_record: dict, attempt: str):
    stored = schema.build_stored_record_object(
        logical_record=logical_record,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=attempt,
    )
    result = writer.write_stored_record_object(
        path,
        stored,
        durability_adapter=ConfirmedSyntheticAdapter(),
    )
    return stored, result


def _ledger(*pairs):
    return durability.VerifiedDurabilityEvidence.from_immutable_write_results(
        record_writes=pairs
    )


def _recovery_anchor(publication_result, bundle_payload, completion):
    return recovery.validate_publication_recovery_anchor(
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        original_publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        original_publication_projection_identity=(
            publication_result.publication_projection_identity
        ),
        original_publication_chain_identity=publication_result.publication_chain_identity,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        expected_final_artifact_sha256s=publication_result.artifact_sha256s,
        publication_recovery_utility_identity=recovery_utility_identity(),
    )


def test_successful_recovery_chain_replays_as_evidence_completed(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    recovered = run_recovery(
        tmp_path, publication_result, bundle_payload, completion
    )
    replayed = recovery_replay.replay_publication_recovery_chain(
        recovered.paths.recovery_chain_directory,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=recovered.publication_recovery_chain_identity,
        original_publication_chain_identity=publication_result.publication_chain_identity,
        expected_final_artifact_sha256s=publication_result.artifact_sha256s,
        durability_evidence=recovery_ledger(recovered),
    )
    assert replayed.classification == (
        recovery_replay.PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
    )


def test_standalone_recovery_completion_is_rejected(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    anchor = _recovery_anchor(publication_result, bundle_payload, completion)
    logical = schema.build_publication_recovery_logical_record(
        record_kind="PUBLICATION_RECOVERY_EVIDENCE_COMPLETED",
        sequence_number=0,
        execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=anchor["publication_recovery_chain_identity"],
        predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={
            "original_publication_chain_identity": publication_result.publication_chain_identity,
            "publication_recovery_chain_identity": anchor[
                "publication_recovery_chain_identity"
            ],
            "recovery_semantics": (
                "final_artifacts_verified_under_separate_recovery_evidence_only"
            ),
        },
    )
    pair = _write_record(tmp_path, logical, "0" * 32)
    replayed = recovery_replay.replay_publication_recovery_chain(
        tmp_path,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=anchor["publication_recovery_chain_identity"],
        original_publication_chain_identity=publication_result.publication_chain_identity,
        durability_evidence=_ledger(pair),
    )
    assert replayed.classification == (
        recovery_replay.PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID
    )


def test_wrong_recovery_transition_order_is_rejected(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    anchor = _recovery_anchor(publication_result, bundle_payload, completion)
    paths = recovery.recovery_paths(
        tmp_path,
        original_publication_chain_identity=publication_result.publication_chain_identity,
        publication_recovery_chain_identity=anchor["publication_recovery_chain_identity"],
    )
    genesis = recovery.build_recovery_authority_accepted_logical_record(
        anchor=anchor,
        expected_final_artifact_sha256s=publication_result.artifact_sha256s,
        final_publication_directory=paths.final_publication_directory,
        publication_recovery_utility_identity=recovery_utility_identity(),
    )
    wrong = schema.build_publication_recovery_logical_record(
        record_kind="PUBLICATION_RECOVERY_EVIDENCE_COMPLETED",
        sequence_number=1,
        execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=anchor["publication_recovery_chain_identity"],
        predecessor_logical_record_sha256=genesis["logical_record_sha256"],
        payload={
            "original_publication_chain_identity": publication_result.publication_chain_identity,
            "publication_recovery_chain_identity": anchor[
                "publication_recovery_chain_identity"
            ],
            "recovery_semantics": (
                "final_artifacts_verified_under_separate_recovery_evidence_only"
            ),
        },
    )
    first_pair = _write_record(tmp_path, genesis, "0" * 32)
    second_pair = _write_record(tmp_path, wrong, "1" * 32)
    replayed = recovery_replay.replay_publication_recovery_chain(
        tmp_path,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=anchor["publication_recovery_chain_identity"],
        original_publication_chain_identity=publication_result.publication_chain_identity,
        durability_evidence=_ledger(first_pair, second_pair),
    )
    assert replayed.classification == (
        recovery_replay.PUBLICATION_RECOVERY_TRANSITION_ORDER_INVALID
    )


def test_recovery_chain_fork_fails_closed(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    anchor = _recovery_anchor(publication_result, bundle_payload, completion)
    paths = recovery.recovery_paths(
        tmp_path,
        original_publication_chain_identity=publication_result.publication_chain_identity,
        publication_recovery_chain_identity=anchor["publication_recovery_chain_identity"],
    )
    first = recovery.build_recovery_authority_accepted_logical_record(
        anchor=anchor,
        expected_final_artifact_sha256s=publication_result.artifact_sha256s,
        final_publication_directory=paths.final_publication_directory,
        publication_recovery_utility_identity=recovery_utility_identity(),
    )
    mutated_hashes = dict(publication_result.artifact_sha256s)
    mutated_hashes[schema.PUBLICATION_SUMMARY_FILENAME] = "e" * 64
    second = recovery.build_recovery_authority_accepted_logical_record(
        anchor=anchor,
        expected_final_artifact_sha256s=mutated_hashes,
        final_publication_directory=paths.final_publication_directory,
        publication_recovery_utility_identity=recovery_utility_identity(),
    )
    first_pair = _write_record(tmp_path, first, "0" * 32)
    second_pair = _write_record(tmp_path, second, "1" * 32)
    replayed = recovery_replay.replay_publication_recovery_chain(
        tmp_path,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=anchor["publication_recovery_chain_identity"],
        original_publication_chain_identity=publication_result.publication_chain_identity,
        durability_evidence=_ledger(first_pair, second_pair),
    )
    assert replayed.classification == recovery_replay.PUBLICATION_RECOVERY_CHAIN_FORK


def test_recovery_replay_requires_verified_durability(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    recovered = run_recovery(
        tmp_path, publication_result, bundle_payload, completion
    )
    replayed = recovery_replay.replay_publication_recovery_chain(
        recovered.paths.recovery_chain_directory,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=recovered.publication_recovery_chain_identity,
        original_publication_chain_identity=publication_result.publication_chain_identity,
        durability_evidence=durability.VerifiedDurabilityEvidence.empty(),
    )
    assert replayed.classification == (
        recovery_replay.PUBLICATION_RECOVERY_CHAIN_DURABILITY_UNCONFIRMED
    )


def test_recovery_replay_rejects_original_chain_mismatch(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    recovered = run_recovery(
        tmp_path, publication_result, bundle_payload, completion
    )
    replayed = recovery_replay.replay_publication_recovery_chain(
        recovered.paths.recovery_chain_directory,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=recovered.publication_recovery_chain_identity,
        original_publication_chain_identity="e" * 64,
        durability_evidence=recovery_ledger(recovered),
    )
    assert replayed.classification == (
        recovery_replay.PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH
    )


def test_recovery_raw_hash_durability_assertion_is_rejected(tmp_path):
    with pytest.raises(recovery_replay.PublicationRecoveryReplayError):
        recovery_replay.replay_publication_recovery_chain(
            tmp_path,
            expected_execution_identity=EXECUTION_IDENTITY,
            publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
            publication_recovery_chain_identity="f" * 64,
            original_publication_chain_identity="a" * 64,
            durability_evidence={"f" * 64},
        )


def test_recovery_authority_replay_missing_genesis_after_window_is_indeterminate(tmp_path):
    result = recovery_replay.replay_publication_recovery_authority_state(
        tmp_path,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity="f" * 64,
        invocation_window_observed=True,
    )
    assert result.state == (
        recovery_replay.PUBLICATION_RECOVERY_AUTHORITY_ATTEMPT_STATE_INDETERMINATE
    )
    assert result.reusable is False
