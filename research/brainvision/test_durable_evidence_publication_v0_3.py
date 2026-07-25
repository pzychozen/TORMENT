from __future__ import annotations

import json
from pathlib import Path

import pytest

import durable_evidence_durability_v0_3 as durability
import durable_evidence_publication_v0_3 as publication
import durable_evidence_publication_replay_v0_3 as publication_replay
import durable_evidence_scientific_result_v0_3 as scientific_result
import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter
import durable_evidence_primary_writer_v0_3 as writer


EXECUTION_IDENTITY = "8" * 64
SCIENTIFIC_AUTHORITY = "9" * 64
PUBLICATION_AUTHORITY = "a" * 64
SECOND_PUBLICATION_AUTHORITY = "b" * 64


class ConfirmedSyntheticAdapter(windows_adapter.WindowsDurabilityAdapter):
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def sync_directory_entry(self, directory_path: str, *, context=None):
        target_role = (
            context.target_role
            if context is not None
            else schema.ARTIFACT_PARENT_DIRECTORY
        )
        self.calls.append((target_role, directory_path))
        return windows_adapter.DirectoryDurabilityResult(
            status=windows_adapter.DIRECTORY_DURABILITY_CONFIRMED,
            detail="synthetic publication test adapter",
            adapter_policy_identity=schema.directory_durability_policy_identity(),
            target_role=target_role,
        )


class RoleStatusSyntheticAdapter(ConfirmedSyntheticAdapter):
    def __init__(
        self,
        status_by_role: dict[str, tuple[str, str | None]],
        *,
        default_status: str = windows_adapter.DIRECTORY_DURABILITY_CONFIRMED,
        default_failure_code: str | None = None,
    ) -> None:
        super().__init__()
        self.status_by_role = dict(status_by_role)
        self.default_status = default_status
        self.default_failure_code = default_failure_code

    def sync_directory_entry(self, directory_path: str, *, context=None):
        target_role = (
            context.target_role
            if context is not None
            else schema.ARTIFACT_PARENT_DIRECTORY
        )
        status, failure_code = self.status_by_role.get(
            target_role,
            (self.default_status, self.default_failure_code),
        )
        self.calls.append((target_role, directory_path))
        return windows_adapter.DirectoryDurabilityResult(
            status=status,
            detail="synthetic role-specific publication test adapter",
            failure_code=failure_code,
            adapter_policy_identity=schema.directory_durability_policy_identity(),
            target_role=target_role,
        )


class PositiveTestStagingCapacityAdapter:
    def check_staging_capacity(self, *, required_bytes: int):
        return {
            "status": publication.STAGING_CAPACITY_CONFIRMED,
            "required_bytes": required_bytes,
            "available_bytes": required_bytes,
            "detail": "pytest-local synthetic staging capacity",
        }


class PositiveTmpPromotionAdapter(
    windows_adapter.SameVolumeNoReplacePromotionAdapter
):
    def __init__(self, tmp_root: Path) -> None:
        self.tmp_root = tmp_root.resolve()

    def promote_verified_directory_no_replace(
        self, source_directory_path: str, destination_directory_path: str
    ):
        source = Path(source_directory_path).resolve()
        destination = Path(destination_directory_path).resolve()
        source.relative_to(self.tmp_root)
        destination.relative_to(self.tmp_root)
        if destination.exists():
            return windows_adapter.DirectoryPromotionResult(
                windows_adapter.PROMOTION_UNCONFIRMED,
                "destination exists",
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        return windows_adapter.DirectoryPromotionResult(
            windows_adapter.PROMOTION_CONFIRMED,
            "synthetic tmp-path promotion",
        )


class CorruptingPromotionAdapter(
    windows_adapter.SameVolumeNoReplacePromotionAdapter
):
    def promote_verified_directory_no_replace(
        self, source_directory_path: str, destination_directory_path: str
    ):
        source = Path(source_directory_path)
        destination = Path(destination_directory_path)
        destination.mkdir(parents=True, exist_ok=False)
        for name in schema.PUBLICATION_ARTIFACT_FILENAMES:
            payload = (source / name).read_bytes()
            if name == schema.PUBLICATION_SUMMARY_FILENAME:
                payload = b"corrupted final summary\n"
            (destination / name).write_bytes(payload)
        return windows_adapter.DirectoryPromotionResult(
            windows_adapter.PROMOTION_CONFIRMED,
            "synthetic corrupting promotion",
        )


def source_identity(source_path: str):
    return {
        "source_path": source_path,
        "git_blob": "1" * 40,
        "raw_sha256": "2" * 64,
    }


def canonical_pass_bundle(result_kind: str = "SYNTHETIC_GATE_PASSED"):
    return {
        "schema": schema.PASS_BUNDLE_SCHEMA,
        "fixed_positive": {"distinguished": True},
        "controls": {
            "malformed_and_degenerate_controls_correct": True,
            "identity_controls_correct": True,
            "nuisance_controls_correct": True,
            "method_b_full_enumeration": True,
            "sampling_used": False,
            "malformed_and_degenerate_control_cases": [
                {
                    "case": "synthetic",
                    "expected_failure_code": "CONTROLLED_INVALID",
                    "observed_failure_code": "CONTROLLED_INVALID",
                    "observed_failure_stage": "schema",
                    "correct": True,
                }
            ],
            "identity_control_cases": {
                "raw_identity_behavior": True,
                "repeat_determinism": True,
                "independently_allocated_equal_input": True,
                "affine_identity_behavior": True,
                "affine_equivalent_behavior": True,
                "affine_plus_complement_identity_behavior": True,
                "affine_plus_complement_behavior": True,
            },
            "method_b_counts": {
                "rotations": 4,
                "affine_transforms": 8,
                "affine_plus_complement_transforms": 16,
            },
            "method_b_required_counts": {
                "rotations": 4,
                "affine_transforms": 8,
                "affine_plus_complement_transforms": 16,
            },
            "method_b_unique_vectors_evaluated": 28,
        },
        "accepted_family": {
            "required_count": 8,
            "distinguished_count": 8,
            "results": [
                {
                    "family_index": 0,
                    "seed_order_position": 0,
                    "pair_duplicate_key": "synthetic-0",
                    "distinguished": True,
                }
            ],
        },
        "scientific_result_kind": result_kind,
    }


def bundle_payload_without_hash(result_kind: str = "SYNTHETIC_GATE_PASSED"):
    pass_bundle = canonical_pass_bundle(result_kind)
    return {
        "bundle_schema_identity": schema.IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA,
        "protocol_identity": schema.PROTOCOL_IDENTITY,
        "execution_identity": EXECUTION_IDENTITY,
        "scientific_execution_authorization_identity": SCIENTIFIC_AUTHORITY,
        "scientific_result_kind": result_kind,
        "pass_bundle_sha256": schema.sha256_hex(schema.canonical_json_bytes(pass_bundle)),
        "two_pass_canonical_identity_status": "identical",
        "configuration_identity": "3" * 64,
        "manifest_identities": {
            "manifest_external_sha256": "4" * 64,
            "manifest_payload_sha256": "5" * 64,
        },
        "implementation_identities": {
            "runner_identity": source_identity("research/brainvision/runner.py"),
            "runner_test_identity": source_identity("research/brainvision/test_runner.py"),
            "schema_contract_identity": source_identity("research/brainvision/schema.py"),
        },
        "descriptor_identity": source_identity("research/brainvision/descriptor.py"),
        "repository_execution_context": {
            "head": "6" * 40,
            "branch": "main",
            "python_version": "Python 3.11.15",
        },
        "publication_projection_source": {
            "current_state_snapshot": {
                "phase": "SCIENTIFIC_COMPLETE",
                "authority_consumed": True,
                "contact_armed": True,
                "manifest_contact_attempt_count": 2,
                "manifest_read_success_count": 2,
            },
            "canonical_pass_bundle": pass_bundle,
            "publication_recipe_identity": "7" * 64,
        },
    }


def bundle_and_completion(result_kind: str = "SYNTHETIC_GATE_PASSED"):
    bundle_payload = schema.build_bundle_payload(
        bundle_payload_without_hash(result_kind)
    )
    stored_bundle = schema.build_stored_bundle_object(
        bundle_payload=bundle_payload,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="0" * 32,
    )
    completion = scientific_result.build_scientific_completion_logical_record(
        stored_bundle,
        sequence_number=5,
        predecessor_logical_record_sha256="1" * 64,
    )
    return bundle_payload, completion


def publication_utility_identities():
    return {
        "publication_projector_identity": source_identity(
            "research/brainvision/durable_evidence_publication_v0_3.py"
        ),
        "publication_schema_identity": source_identity(
            "research/brainvision/durable_evidence_schema_v0_3.py"
        ),
        "resource_admissibility_policy_identity": (
            schema.resource_admissibility_policy_identity()
        ),
        "directory_durability_policy_identity": (
            schema.directory_durability_policy_identity()
        ),
    }


def project(
    tmp_path: Path,
    *,
    publication_authority: str = PUBLICATION_AUTHORITY,
    promotion_adapter=None,
    durability_adapter=None,
    staging_capacity_adapter=None,
    context=None,
    synthetic_fault_point=None,
):
    bundle_payload, completion = bundle_and_completion()
    result = publication.project_publication(
        root_path=tmp_path,
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        publication_projection_authorization_identity=publication_authority,
        publication_utility_identities=publication_utility_identities(),
        context=context or publication.SyntheticPublicationContext(),
        durability_adapter=durability_adapter or ConfirmedSyntheticAdapter(),
        promotion_adapter=promotion_adapter,
        staging_capacity_adapter=(
            staging_capacity_adapter or PositiveTestStagingCapacityAdapter()
        ),
        synthetic_fault_point=synthetic_fault_point,
    )
    return result, bundle_payload, completion


def ledger_from_publication(result):
    return durability.VerifiedDurabilityEvidence.from_immutable_write_results(
        record_writes=tuple(
            (item.stored_record_object, item.write_result)
            for item in result.record_writes
        )
    )


def final_artifact_bytes(result):
    return {
        name: (result.paths.final_directory / name).read_bytes()
        for name in schema.PUBLICATION_ARTIFACT_FILENAMES
    }


def test_publication_projects_exact_three_artifacts_and_replays(tmp_path):
    result, bundle_payload, completion = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    assert result.classification == publication.PUBLICATION_COMPLETED
    assert tuple(sorted(item.name for item in result.paths.final_directory.iterdir())) == (
        tuple(sorted(schema.PUBLICATION_ARTIFACT_FILENAMES))
    )
    artifact_bytes = final_artifact_bytes(result)
    assert schema.validate_publication_artifact_byte_map(
        artifact_bytes,
        bundle_payload=bundle_payload,
        expected_artifact_sha256s=result.artifact_sha256s,
    ) == result.artifact_sha256s
    assert artifact_bytes[schema.PUBLICATION_SUMMARY_FILENAME] == (
        b"Stage S3B v0.3 synthetic validation\n"
        b"result_kind = SYNTHETIC_GATE_PASSED\n"
        b"FORMAL_HOLD = active\n"
        b"Mode_0 = active\n"
        b"STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY\n"
    )
    result_json = json.loads(
        artifact_bytes[schema.PUBLICATION_RESULT_ARTIFACT_FILENAME].decode("utf-8")
    )
    assert tuple(result_json.keys()) == schema.PUBLICATION_RESULT_ARTIFACT_KEYS
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
        durability_evidence=ledger_from_publication(result),
    )
    assert replayed.classification == publication_replay.PUBLICATION_COMPLETED


def test_publication_directory_durability_roles_are_ordered(tmp_path):
    adapter = ConfirmedSyntheticAdapter()
    result, _, _ = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
        durability_adapter=adapter,
    )
    assert result.classification == publication.PUBLICATION_COMPLETED
    assert [role for role, _ in adapter.calls] == [
        schema.ARTIFACT_PARENT_DIRECTORY,
        schema.ARTIFACT_PARENT_DIRECTORY,
        schema.STAGING_PARENT_DIRECTORY,
        schema.STAGING_DIRECTORY,
        schema.ARTIFACT_PARENT_DIRECTORY,
    ]


def test_staged_set_directory_durability_withholds_completion(tmp_path):
    adapter = RoleStatusSyntheticAdapter(
        {
            schema.STAGING_DIRECTORY: (
                schema.DIRECTORY_DURABILITY_DENIED,
                schema.DIRECTORY_FLUSH_DENIED,
            )
        }
    )
    result, _, _ = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
        durability_adapter=adapter,
    )
    assert result.classification == publication.PUBLICATION_STAGING_DURABILITY_UNCONFIRMED
    assert result.directory_durability_failure_code == schema.DIRECTORY_FLUSH_DENIED
    assert not result.paths.final_directory.exists()
    assert all(
        item.logical_record["record_kind"] != "PUBLICATION_COMPLETED"
        for item in result.record_writes
    )


def test_projection_artifact_bytes_are_deterministic_across_independent_roots(tmp_path):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first, _, _ = project(
        first_root,
        promotion_adapter=PositiveTmpPromotionAdapter(first_root),
    )
    second, _, _ = project(
        second_root,
        promotion_adapter=PositiveTmpPromotionAdapter(second_root),
    )
    assert final_artifact_bytes(first) == final_artifact_bytes(second)
    assert first.artifact_sha256s == second.artifact_sha256s


def test_different_publication_authorizations_create_different_chain_identities(tmp_path):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first, _, _ = project(
        first_root,
        promotion_adapter=PositiveTmpPromotionAdapter(first_root),
        publication_authority=PUBLICATION_AUTHORITY,
    )
    second, _, _ = project(
        second_root,
        promotion_adapter=PositiveTmpPromotionAdapter(second_root),
        publication_authority=SECOND_PUBLICATION_AUTHORITY,
    )
    assert first.publication_projection_identity == second.publication_projection_identity
    assert first.publication_chain_identity != second.publication_chain_identity


def test_no_artifacts_are_written_before_durable_attempted_record(tmp_path):
    result, _, _ = project(
        tmp_path,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
        synthetic_fault_point="before_publication_attempted_write",
    )
    assert result.classification == publication.PUBLICATION_ATTEMPTED_WRITE_FAILED
    assert not result.paths.staging_directory.exists()
    assert len(result.record_writes) == 1


def test_default_promotion_adapter_fails_closed_and_retains_staging(tmp_path):
    result, _, _ = project(tmp_path)
    assert result.classification == publication.PUBLICATION_PROMOTION_FAILED
    assert result.paths.staging_directory.exists()
    assert not result.paths.final_directory.exists()
    assert [item.logical_record["record_kind"] for item in result.record_writes] == [
        "PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED",
        "PUBLICATION_ATTEMPTED",
    ]


def test_staging_and_final_directory_collisions_fail_closed(tmp_path):
    bundle_payload, completion = bundle_and_completion()
    anchor = publication.validate_publication_anchor(
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_utility_identities=publication_utility_identities(),
    )
    paths = publication.publication_paths(tmp_path, anchor["publication_chain_identity"])
    paths.staging_directory.mkdir(parents=True)
    staging_result = publication.project_publication(
        root_path=tmp_path,
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_utility_identities=publication_utility_identities(),
        context=publication.SyntheticPublicationContext(),
        durability_adapter=ConfirmedSyntheticAdapter(),
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
        staging_capacity_adapter=PositiveTestStagingCapacityAdapter(),
    )
    assert staging_result.classification == (
        publication.PUBLICATION_STAGING_DIRECTORY_COLLISION
    )

    other_root = tmp_path / "other"
    other_root.mkdir()
    other_paths = publication.publication_paths(
        other_root, anchor["publication_chain_identity"]
    )
    other_paths.final_directory.mkdir(parents=True)
    final_result = publication.project_publication(
        root_path=other_root,
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_utility_identities=publication_utility_identities(),
        context=publication.SyntheticPublicationContext(),
        durability_adapter=ConfirmedSyntheticAdapter(),
        promotion_adapter=PositiveTmpPromotionAdapter(other_root),
        staging_capacity_adapter=PositiveTestStagingCapacityAdapter(),
    )
    assert final_result.classification == publication.PUBLICATION_FINAL_DIRECTORY_COLLISION


def test_publication_authority_reuse_is_denied_after_exception(tmp_path):
    context = publication.SyntheticPublicationContext()
    result, _, _ = project(
        tmp_path,
        context=context,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
        synthetic_fault_point="failure_after_one_artifact",
    )
    assert result.classification == publication.PUBLICATION_STAGING_INCOMPLETE
    next_root = tmp_path / "next"
    next_root.mkdir()
    with pytest.raises(publication.PublicationAuthorityReuseDenied):
        project(
            next_root,
            context=context,
            promotion_adapter=PositiveTmpPromotionAdapter(next_root),
        )


def test_publication_artifact_cross_validation_rejects_wrong_result_kind():
    bundle_payload, _ = bundle_and_completion()
    artifact_bytes = schema.publication_artifact_byte_map_for_bundle(bundle_payload)
    mutated = dict(artifact_bytes)
    result_artifact = json.loads(
        mutated[schema.PUBLICATION_RESULT_ARTIFACT_FILENAME].decode("utf-8")
    )
    result_artifact["result_kind"] = "SYNTHETIC_GATE_FAILED"
    mutated[schema.PUBLICATION_RESULT_ARTIFACT_FILENAME] = schema.canonical_json_bytes(
        result_artifact
    )
    with pytest.raises(schema.PublicationArtifactError):
        schema.validate_publication_artifact_byte_map(
            mutated, bundle_payload=bundle_payload
        )


def test_final_readback_mismatch_prevents_publication_completed(tmp_path):
    result, _, _ = project(
        tmp_path,
        promotion_adapter=CorruptingPromotionAdapter(),
    )
    assert result.classification == publication.PUBLICATION_FINAL_DIRECTORY_INVALID
    assert all(
        item.logical_record["record_kind"] != "PUBLICATION_COMPLETED"
        for item in result.record_writes
    )
