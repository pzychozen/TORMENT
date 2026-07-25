from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

import durable_evidence_publication_recovery_v0_3 as recovery
import durable_evidence_schema_v0_3 as schema

from test_durable_evidence_publication_recovery_v0_3 import (
    RECOVERY_AUTHORITY,
    recovery_ledger,
    recovery_utility_identity,
    run_recovery,
    setup_final_artifacts_with_incomplete_publication_chain,
    snapshot_tree,
)
from test_durable_evidence_publication_v0_3 import (
    ConfirmedSyntheticAdapter,
    EXECUTION_IDENTITY,
    PUBLICATION_AUTHORITY,
)


def recover_direct(
    tmp_path,
    publication_result,
    bundle_payload,
    completion,
    *,
    utility_identity=None,
    expected_hashes=None,
):
    return recovery.verify_publication_recovery(
        root_path=tmp_path,
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        original_publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        original_publication_projection_identity=(
            publication_result.publication_projection_identity
        ),
        original_publication_chain_identity=publication_result.publication_chain_identity,
        publication_recovery_authorization_identity=RECOVERY_AUTHORITY,
        expected_final_artifact_sha256s=(
            expected_hashes or publication_result.artifact_sha256s
        ),
        publication_recovery_utility_identity=(
            utility_identity if utility_identity is not None else recovery_utility_identity()
        ),
        context=recovery.SyntheticPublicationRecoveryContext(),
        durability_adapter=ConfirmedSyntheticAdapter(),
    )


def policy_variant(kind: str):
    utility = recovery_utility_identity()
    identity = schema.resource_admissibility_policy_identity()
    if kind == "missing":
        utility.pop("resource_admissibility_policy_identity")
    elif kind == "malformed":
        utility["resource_admissibility_policy_identity"] = None
    elif kind == "wrong_order":
        utility["resource_admissibility_policy_identity"] = {
            "policy_sha256": identity["policy_sha256"],
            "policy_schema_identity": identity["policy_schema_identity"],
        }
    elif kind == "wrong_schema":
        utility["resource_admissibility_policy_identity"] = {
            "policy_schema_identity": "wrong",
            "policy_sha256": identity["policy_sha256"],
        }
    elif kind == "wrong_hash":
        utility["resource_admissibility_policy_identity"] = {
            "policy_schema_identity": identity["policy_schema_identity"],
            "policy_sha256": "0" * 64,
        }
    else:
        raise AssertionError(kind)
    return utility


def assert_no_recovery_completion(result):
    kinds = [item.logical_record["record_kind"] for item in result.record_writes]
    assert "PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED" not in kinds
    assert "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED" not in kinds


@pytest.mark.parametrize(
    "kind",
    ("missing", "malformed", "wrong_order", "wrong_schema", "wrong_hash"),
)
def test_recovery_policy_identity_mismatch_maps_exactly(tmp_path, kind):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    recovered = recover_direct(
        tmp_path,
        publication_result,
        bundle_payload,
        completion,
        utility_identity=policy_variant(kind),
    )
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED
    )
    assert recovered.resource_failure_code == (
        schema.RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH
    )
    assert_no_recovery_completion(recovered)


def test_correct_recovery_policy_identity_succeeds_as_separate_j2_evidence(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == recovery.PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
    assert recovered.resource_failure_code is None
    assert recovered.resource_policy_identity == schema.resource_admissibility_policy_identity()
    assert recovered.original_publication_completed_normally is False


@pytest.mark.parametrize("mutation", ("missing", "extra", "wrong"))
def test_exact_final_inventory_is_required(tmp_path, mutation):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    final_dir = publication_result.paths.final_directory
    if mutation == "missing":
        (final_dir / schema.PUBLICATION_SUMMARY_FILENAME).unlink()
    elif mutation == "extra":
        (final_dir / "extra.txt").write_bytes(b"extra\n")
    else:
        (final_dir / schema.PUBLICATION_SUMMARY_FILENAME).rename(final_dir / "wrong.txt")
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == recovery.PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID
    assert_no_recovery_completion(recovered)


def test_directory_artifact_is_rejected_as_type_invalid(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    target = publication_result.paths.final_directory / schema.PUBLICATION_SUMMARY_FILENAME
    target.unlink()
    target.mkdir()
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE
    )
    assert recovered.resource_failure_code == schema.RECOVERY_ARTIFACT_TYPE_INVALID
    assert_no_recovery_completion(recovered)


def test_symlink_artifact_is_rejected_where_host_permits(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    target = publication_result.paths.final_directory / schema.PUBLICATION_SUMMARY_FILENAME
    replacement = tmp_path / "external_symlink_target.txt"
    replacement.write_bytes(b"replacement\n")
    target.unlink()
    try:
        target.symlink_to(replacement)
    except (OSError, NotImplementedError) as exc:
        pytest.skip("host does not permit synthetic symlink creation: %s" % exc)
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE
    )
    assert recovered.resource_failure_code == schema.RECOVERY_ARTIFACT_TYPE_INVALID


def test_lstat_open_fstat_ambiguity_maps_read_indeterminate(tmp_path, monkeypatch):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )

    def indeterminate(path, max_bytes, *, over_limit_code=schema.ARTIFACT_SIZE_LIMIT_EXCEEDED):
        raise schema.RecoveryArtifactReadIndeterminateError("synthetic ambiguity")

    monkeypatch.setattr(schema, "read_file_bytes_bounded", indeterminate)
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE
    )
    assert recovered.resource_failure_code == schema.RECOVERY_ARTIFACT_READ_INDETERMINATE
    assert_no_recovery_completion(recovered)


def test_per_artifact_limit_rejects_before_json_parse(tmp_path, monkeypatch):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    monkeypatch.setattr(schema, "MAX_PUBLICATION_RESULT_ARTIFACT_BYTES", 5)
    result_path = (
        publication_result.paths.final_directory
        / schema.PUBLICATION_RESULT_ARTIFACT_FILENAME
    )
    result_path.write_bytes(b"x" * 6)
    original_load = schema.load_canonical_json_bytes

    def fail_only_if_oversized_artifact_is_parsed(payload, max_bytes=None):
        if payload == b"x" * 6:
            raise AssertionError("parsed oversized artifact")
        return original_load(payload, max_bytes=max_bytes)

    monkeypatch.setattr(
        schema,
        "load_canonical_json_bytes",
        fail_only_if_oversized_artifact_is_parsed,
    )
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED
    )
    assert recovered.resource_failure_code == schema.ARTIFACT_SIZE_LIMIT_EXCEEDED
    assert_no_recovery_completion(recovered)


def test_cumulative_recovery_budget_maps_exactly(tmp_path, monkeypatch):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    monkeypatch.setattr(schema, "MAX_PUBLICATION_RECOVERY_VERIFICATION_BYTES", 1)
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_VERIFICATION_BUDGET_EXCEEDED
    )
    assert recovered.resource_failure_code == schema.RECOVERY_VERIFICATION_BUDGET_EXCEEDED
    assert_no_recovery_completion(recovered)


def test_artifact_set_size_code_maps_to_recovery_budget(tmp_path, monkeypatch):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )

    def reject_set(artifact_bytes_by_name):
        raise schema.PublicationArtifactSetSizeLimitError("aggregate too large")

    monkeypatch.setattr(schema, "validate_publication_artifact_resource_map", reject_set)
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_VERIFICATION_BUDGET_EXCEEDED
    )
    assert recovered.resource_failure_code == schema.ARTIFACT_SET_SIZE_LIMIT_EXCEEDED
    assert_no_recovery_completion(recovered)


def test_canonical_invalid_and_hash_mismatch_remain_existing_families(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    final_dir = publication_result.paths.final_directory
    (final_dir / schema.PUBLICATION_RESULT_ARTIFACT_FILENAME).write_bytes(
        b'{ "bad":"not canonical" }\n'
    )
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    assert recovered.classification == recovery.PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID

    second_root = tmp_path / "second"
    second_root.mkdir()
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(second_root)
    )
    (publication_result.paths.final_directory / schema.PUBLICATION_SUMMARY_FILENAME).write_bytes(
        b"synthetic but wrong summary\n"
    )
    recovered = run_recovery(second_root, publication_result, bundle_payload, completion)
    assert recovered.classification == recovery.PUBLICATION_RECOVERY_ARTIFACT_HASH_MISMATCH


def test_recovery_does_not_mutate_original_chain_or_final_artifacts_on_rejection(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    original_before = snapshot_tree(publication_result.paths.chain_directory)
    final_before = snapshot_tree(publication_result.paths.final_directory)
    recovered = recover_direct(
        tmp_path,
        publication_result,
        bundle_payload,
        completion,
        utility_identity=policy_variant("missing"),
    )
    assert recovered.classification == (
        recovery.PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED
    )
    assert snapshot_tree(publication_result.paths.chain_directory) == original_before
    assert snapshot_tree(publication_result.paths.final_directory) == final_before


def test_recovery_replay_of_successful_j2_chain_still_completes(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    recovered = run_recovery(tmp_path, publication_result, bundle_payload, completion)
    import durable_evidence_publication_recovery_replay_v0_3 as recovery_replay

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


def test_recovery_result_fields_preserve_dataclass_prefix():
    assert [field.name for field in fields(recovery.PublicationRecoveryResult)[:9]] == [
        "classification",
        "detail",
        "publication_recovery_chain_identity",
        "original_publication_chain_identity",
        "verified_artifact_sha256s",
        "record_writes",
        "paths",
        "authority_state",
        "original_publication_completed_normally",
    ]


def test_read_file_bytes_bounded_rejects_oversized_file(tmp_path):
    path = Path(tmp_path) / "artifact.bin"
    path.write_bytes(b"abcdef")
    with pytest.raises(schema.PublicationArtifactSizeLimitError):
        schema.read_file_bytes_bounded(path, 5)
