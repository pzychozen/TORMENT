from __future__ import annotations

from pathlib import Path

import pytest

import durable_evidence_durability_v0_3 as durability
import durable_evidence_publication_replay_v0_3 as publication_replay
import durable_evidence_publication_v0_3 as publication
import durable_evidence_schema_v0_3 as schema
import durable_evidence_primary_writer_v0_3 as writer

from test_durable_evidence_publication_v0_3 import (
    ConfirmedSyntheticAdapter,
    EXECUTION_IDENTITY,
    PUBLICATION_AUTHORITY,
    PositiveTmpPromotionAdapter,
    bundle_and_completion,
    ledger_from_publication,
    project,
    publication_utility_identities,
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


def _anchor():
    bundle_payload, completion = bundle_and_completion()
    return (
        bundle_payload,
        completion,
        publication.validate_publication_anchor(
            bundle_payload=bundle_payload,
            scientific_completion_logical_record=completion,
            publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
            publication_utility_identities=publication_utility_identities(),
        ),
    )


def test_standalone_publication_completed_never_establishes_completion(tmp_path):
    bundle_payload, completion, anchor = _anchor()
    completed = schema.build_publication_logical_record(
        record_kind="PUBLICATION_COMPLETED",
        sequence_number=0,
        execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=anchor["publication_chain_identity"],
        predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={
            "publication_projection_identity": anchor["publication_projection_identity"],
            "publication_chain_identity": anchor["publication_chain_identity"],
            "artifact_sha256s": schema.publication_artifact_sha256s_for_bundle(
                bundle_payload
            ),
        },
    )
    stored, write_result = _write_record(tmp_path, completed, "0" * 32)
    replayed = publication_replay.replay_publication_chain(
        tmp_path,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=anchor["publication_chain_identity"],
        publication_projection_identity=anchor["publication_projection_identity"],
        bundle_payload_sha256=bundle_payload["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=completion[
            "logical_record_sha256"
        ],
        durability_evidence=_ledger((stored, write_result)),
    )
    assert replayed.classification == (
        publication_replay.PUBLICATION_TRANSITION_ORDER_INVALID
    )


def test_wrong_publication_predecessor_fails_replay(tmp_path):
    _, _, anchor = _anchor()
    genesis = publication.build_publication_authority_accepted_logical_record(
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity="9" * 64,
        bundle_payload_sha256=anchor["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=anchor[
            "scientific_completion_logical_record_sha256"
        ],
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        publication_recipe_identity=anchor["publication_recipe_identity"],
        publication_utility_identities=publication_utility_identities(),
    )
    attempted = schema.build_publication_logical_record(
        record_kind="PUBLICATION_ATTEMPTED",
        sequence_number=1,
        execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=anchor["publication_chain_identity"],
        predecessor_logical_record_sha256="f" * 64,
        payload={
            "publication_projection_identity": anchor["publication_projection_identity"],
            "publication_chain_identity": anchor["publication_chain_identity"],
            "artifact_filenames": list(schema.PUBLICATION_ARTIFACT_FILENAMES),
        },
    )
    genesis_pair = _write_record(tmp_path, genesis, "0" * 32)
    attempted_pair = _write_record(tmp_path, attempted, "1" * 32)
    replayed = publication_replay.replay_publication_chain(
        tmp_path,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=anchor["publication_chain_identity"],
        durability_evidence=_ledger(genesis_pair, attempted_pair),
    )
    assert replayed.classification == publication_replay.PUBLICATION_CHAIN_REPLAY_FAILED


def test_publication_fork_fails_closed(tmp_path):
    _, _, anchor = _anchor()
    first = publication.build_publication_authority_accepted_logical_record(
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity="9" * 64,
        bundle_payload_sha256=anchor["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=anchor[
            "scientific_completion_logical_record_sha256"
        ],
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        publication_recipe_identity=anchor["publication_recipe_identity"],
        publication_utility_identities=publication_utility_identities(),
    )
    second = publication.build_publication_authority_accepted_logical_record(
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity="9" * 64,
        bundle_payload_sha256=anchor["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=anchor[
            "scientific_completion_logical_record_sha256"
        ],
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_projection_identity=anchor["publication_projection_identity"],
        publication_chain_identity=anchor["publication_chain_identity"],
        publication_recipe_identity="e" * 64,
        publication_utility_identities=publication_utility_identities(),
    )
    first_pair = _write_record(tmp_path, first, "0" * 32)
    second_pair = _write_record(tmp_path, second, "1" * 32)
    replayed = publication_replay.replay_publication_chain(
        tmp_path,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=anchor["publication_chain_identity"],
        durability_evidence=_ledger(first_pair, second_pair),
    )
    assert replayed.classification == publication_replay.PUBLICATION_CHAIN_FORK


def test_publication_replay_requires_verified_durability(tmp_path):
    result, bundle_payload, completion = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    replayed = publication_replay.replay_publication_chain(
        result.paths.chain_directory,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=result.publication_chain_identity,
        publication_projection_identity=result.publication_projection_identity,
        bundle_payload_sha256=bundle_payload["bundle_payload_sha256"],
        scientific_completion_logical_record_sha256=completion[
            "logical_record_sha256"
        ],
        expected_artifact_sha256s=result.artifact_sha256s,
        durability_evidence=durability.VerifiedDurabilityEvidence.empty(),
    )
    assert replayed.classification == (
        publication_replay.PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED
    )


def test_raw_hash_durability_assertion_is_rejected(tmp_path):
    with pytest.raises(publication_replay.PublicationReplayError):
        publication_replay.replay_publication_chain(
            tmp_path,
            expected_execution_identity=EXECUTION_IDENTITY,
            publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
            publication_chain_identity="c" * 64,
            durability_evidence={"f" * 64},
        )


def test_valid_publication_prefix_cannot_hide_contradictory_tail(tmp_path):
    result, _, _ = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    completed = result.record_writes[-1].logical_record
    tail = schema.build_publication_logical_record(
        record_kind="PUBLICATION_ATTEMPTED",
        sequence_number=3,
        execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=result.publication_chain_identity,
        predecessor_logical_record_sha256=completed["logical_record_sha256"],
        payload={
            "publication_projection_identity": result.publication_projection_identity,
            "publication_chain_identity": result.publication_chain_identity,
            "artifact_filenames": list(schema.PUBLICATION_ARTIFACT_FILENAMES),
        },
    )
    tail_pair = _write_record(result.paths.chain_directory, tail, "9" * 32)
    ledger = durability.VerifiedDurabilityEvidence.from_immutable_write_results(
        record_writes=tuple(
            (item.stored_record_object, item.write_result)
            for item in result.record_writes
        )
        + (tail_pair,)
    )
    replayed = publication_replay.replay_publication_chain(
        result.paths.chain_directory,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=result.publication_chain_identity,
        durability_evidence=ledger,
    )
    assert replayed.classification == (
        publication_replay.PUBLICATION_EVIDENCE_CONTRADICTORY
    )


def test_publication_authority_replay_missing_genesis_after_window_is_indeterminate(tmp_path):
    result = publication_replay.replay_publication_authority_state(
        tmp_path,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity="c" * 64,
        invocation_window_observed=True,
    )
    assert result.state == (
        publication_replay.PUBLICATION_AUTHORITY_ATTEMPT_STATE_INDETERMINATE
    )
    assert result.reusable is False


def test_publication_authority_replay_proves_consumed_only_when_durable(tmp_path):
    result, _, _ = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    replayed = publication_replay.replay_publication_authority_state(
        result.paths.chain_directory,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=result.publication_chain_identity,
        durability_evidence=ledger_from_publication(result),
        invocation_window_observed=True,
    )
    assert replayed.state == publication_replay.PUBLICATION_AUTHORITY_CONSUMED
    assert replayed.reusable is False
