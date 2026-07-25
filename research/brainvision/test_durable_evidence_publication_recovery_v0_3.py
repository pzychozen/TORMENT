from __future__ import annotations

from pathlib import Path

import pytest

import durable_evidence_durability_v0_3 as durability
import durable_evidence_publication_recovery_replay_v0_3 as recovery_replay
import durable_evidence_publication_recovery_v0_3 as recovery
import durable_evidence_publication_v0_3 as publication
import durable_evidence_schema_v0_3 as schema

from test_durable_evidence_publication_v0_3 import (
    ConfirmedSyntheticAdapter,
    EXECUTION_IDENTITY,
    PUBLICATION_AUTHORITY,
    PositiveTmpPromotionAdapter,
    RoleStatusSyntheticAdapter,
    project,
    source_identity,
)


RECOVERY_AUTHORITY = "c" * 64


def recovery_utility_identity():
    return {
        "publication_recovery_utility_identity": source_identity(
            "research/brainvision/durable_evidence_publication_recovery_v0_3.py"
        ),
        "publication_recovery_schema_identity": source_identity(
            "research/brainvision/durable_evidence_schema_v0_3.py"
        ),
        "resource_admissibility_policy_identity": (
            schema.resource_admissibility_policy_identity()
        ),
        "directory_durability_policy_identity": (
            schema.directory_durability_policy_identity()
        ),
    }


def recovery_ledger(result):
    return durability.VerifiedDurabilityEvidence.from_immutable_write_results(
        record_writes=tuple(
            (item.stored_record_object, item.write_result)
            for item in result.record_writes
        )
    )


def snapshot_tree(path: Path):
    return {
        item.relative_to(path).as_posix(): item.read_bytes()
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def setup_final_artifacts_with_incomplete_publication_chain(tmp_path):
    result, bundle_payload, completion = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
        synthetic_fault_point="publication_completed_write_failure",
    )
    assert result.classification == (
        publication.PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED
    )
    assert result.paths.final_directory.exists()
    assert len(result.record_writes) == 2
    return result, bundle_payload, completion


def run_recovery(
    tmp_path,
    publication_result,
    bundle_payload,
    completion,
    *,
    context=None,
    recovery_authority=RECOVERY_AUTHORITY,
    expected_hashes=None,
    original_projection_identity=None,
    durability_adapter=None,
    synthetic_fault_point=None,
):
    return recovery.verify_publication_recovery(
        root_path=tmp_path,
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        original_publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        original_publication_projection_identity=(
            original_projection_identity
            or publication_result.publication_projection_identity
        ),
        original_publication_chain_identity=publication_result.publication_chain_identity,
        publication_recovery_authorization_identity=recovery_authority,
        expected_final_artifact_sha256s=(
            expected_hashes or publication_result.artifact_sha256s
        ),
        publication_recovery_utility_identity=recovery_utility_identity(),
        context=context or recovery.SyntheticPublicationRecoveryContext(),
        durability_adapter=durability_adapter or ConfirmedSyntheticAdapter(),
        synthetic_fault_point=synthetic_fault_point,
    )


def test_recovery_verifies_existing_final_artifacts_without_claiming_normal_completion(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    original_chain_before = snapshot_tree(publication_result.paths.chain_directory)
    final_before = snapshot_tree(publication_result.paths.final_directory)
    recovered = run_recovery(
        tmp_path, publication_result, bundle_payload, completion
    )
    assert recovered.classification == recovery.PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
    assert recovered.original_publication_completed_normally is False
    assert snapshot_tree(publication_result.paths.chain_directory) == (
        original_chain_before
    )
    assert snapshot_tree(publication_result.paths.final_directory) == final_before
    replayed = recovery_replay.replay_publication_recovery_chain(
        recovered.paths.recovery_chain_directory,
        expected_execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=recovered.publication_recovery_chain_identity,
        original_publication_chain_identity=(
            publication_result.publication_chain_identity
        ),
        expected_final_artifact_sha256s=publication_result.artifact_sha256s,
        durability_evidence=recovery_ledger(recovered),
    )
    assert replayed.classification == (
        recovery_replay.PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
    )


def test_recovery_directory_durability_withholds_j2_completion(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    adapter = RoleStatusSyntheticAdapter(
        {},
        default_status=schema.DIRECTORY_DURABILITY_DENIED,
        default_failure_code=schema.DIRECTORY_OPEN_DENIED,
    )
    recovered = run_recovery(
        tmp_path,
        publication_result,
        bundle_payload,
        completion,
        durability_adapter=adapter,
    )
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED
    )
    assert recovered.directory_durability_failure_code == schema.DIRECTORY_OPEN_DENIED
    assert all(
        item.logical_record["record_kind"]
        != "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED"
        for item in recovered.record_writes
    )


def test_recovery_final_directory_missing_does_not_complete_evidence(tmp_path):
    publication_result, bundle_payload, completion = project(tmp_path)
    assert publication_result.classification == publication.PUBLICATION_PROMOTION_FAILED
    recovered = run_recovery(
        tmp_path, publication_result, bundle_payload, completion
    )
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_FINAL_DIRECTORY_MISSING
    )
    assert all(
        item.logical_record["record_kind"]
        != "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED"
        for item in recovered.record_writes
    )


@pytest.mark.parametrize(
    "mutation, expected",
    (
        ("missing", recovery.PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID),
        ("extra", recovery.PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID),
        ("wrong_filename", recovery.PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID),
        ("noncanonical", recovery.PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID),
        ("hash_mismatch", recovery.PUBLICATION_RECOVERY_ARTIFACT_HASH_MISMATCH),
    ),
)
def test_recovery_rejects_invalid_final_artifacts(tmp_path, mutation, expected):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    final_dir = publication_result.paths.final_directory
    if mutation == "missing":
        (final_dir / schema.PUBLICATION_SUMMARY_FILENAME).unlink()
    elif mutation == "extra":
        (final_dir / "unexpected.txt").write_bytes(b"unexpected\n")
    elif mutation == "wrong_filename":
        (final_dir / schema.PUBLICATION_SUMMARY_FILENAME).rename(
            final_dir / "wrong_summary.txt"
        )
    elif mutation == "noncanonical":
        (final_dir / schema.PUBLICATION_RESULT_ARTIFACT_FILENAME).write_bytes(
            b'{ "bad":"not canonical" }\n'
        )
    elif mutation == "hash_mismatch":
        (final_dir / schema.PUBLICATION_SUMMARY_FILENAME).write_bytes(
            b"synthetic but wrong summary\n"
        )
    recovered = run_recovery(
        tmp_path, publication_result, bundle_payload, completion
    )
    assert recovered.classification == expected
    assert all(
        item.logical_record["record_kind"]
        != "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED"
        for item in recovered.record_writes
    )


def test_recovery_original_chain_mismatch_fails_closed(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    recovered = run_recovery(
        tmp_path,
        publication_result,
        bundle_payload,
        completion,
        original_projection_identity="d" * 64,
    )
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_ORIGINAL_CHAIN_MISMATCH
    )


def test_recovery_authority_reuse_is_denied_after_failure(tmp_path):
    publication_result, bundle_payload, completion = project(tmp_path)
    context = recovery.SyntheticPublicationRecoveryContext()
    first = run_recovery(
        tmp_path,
        publication_result,
        bundle_payload,
        completion,
        context=context,
    )
    assert first.classification == recovery.PUBLICATION_RECOVERY_FINAL_DIRECTORY_MISSING
    with pytest.raises(recovery.PublicationRecoveryAuthorityReuseDenied):
        run_recovery(
            tmp_path,
            publication_result,
            bundle_payload,
            completion,
            context=context,
        )


def test_recovery_performs_no_artifact_mutation_under_path_sentinels(
    tmp_path, monkeypatch
):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    final_before = snapshot_tree(publication_result.paths.final_directory)

    def forbidden(*args, **kwargs):
        raise AssertionError("artifact mutation primitive was called")

    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "unlink", forbidden)
    monkeypatch.setattr(Path, "rename", forbidden)
    monkeypatch.setattr(Path, "replace", forbidden)

    recovered = run_recovery(
        tmp_path, publication_result, bundle_payload, completion
    )
    assert recovered.classification == recovery.PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
    assert snapshot_tree(publication_result.paths.final_directory) == final_before


def test_different_recovery_authorizations_create_distinct_recovery_chains(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    first = recovery.validate_publication_recovery_anchor(
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        original_publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        original_publication_projection_identity=(
            publication_result.publication_projection_identity
        ),
        original_publication_chain_identity=publication_result.publication_chain_identity,
        publication_recovery_authorization_identity="c" * 64,
        expected_final_artifact_sha256s=publication_result.artifact_sha256s,
        publication_recovery_utility_identity=recovery_utility_identity(),
    )
    second = recovery.validate_publication_recovery_anchor(
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        original_publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        original_publication_projection_identity=(
            publication_result.publication_projection_identity
        ),
        original_publication_chain_identity=publication_result.publication_chain_identity,
        publication_recovery_authorization_identity="d" * 64,
        expected_final_artifact_sha256s=publication_result.artifact_sha256s,
        publication_recovery_utility_identity=recovery_utility_identity(),
    )
    assert first["publication_recovery_chain_identity"] != (
        second["publication_recovery_chain_identity"]
    )
