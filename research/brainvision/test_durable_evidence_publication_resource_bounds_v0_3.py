from __future__ import annotations

from dataclasses import fields

import pytest

import durable_evidence_publication_v0_3 as publication
import durable_evidence_schema_v0_3 as schema

from test_durable_evidence_publication_v0_3 import (
    ConfirmedSyntheticAdapter,
    PUBLICATION_AUTHORITY,
    PositiveTmpPromotionAdapter,
    bundle_and_completion,
    publication_utility_identities,
)


class CapacityAdapter:
    def __init__(self, factory):
        self.factory = factory
        self.calls: list[int] = []

    def check_staging_capacity(self, *, required_bytes: int):
        self.calls.append(required_bytes)
        return self.factory(required_bytes)


class ExplodingPromotionAdapter:
    def promote_verified_directory_no_replace(self, source_directory_path, destination_directory_path):
        raise AssertionError("promotion must not be reached before resource admission")


def response(status, required_bytes, available_bytes, detail="synthetic capacity"):
    return {
        "status": status,
        "required_bytes": required_bytes,
        "available_bytes": available_bytes,
        "detail": detail,
    }


def publish(
    tmp_path,
    *,
    utility_identities=None,
    capacity_adapter=None,
    promotion_adapter=None,
    bundle_payload=None,
    completion=None,
):
    if bundle_payload is None:
        bundle_payload, completion = bundle_and_completion()
    assert completion is not None
    return publication.project_publication(
        root_path=tmp_path,
        bundle_payload=bundle_payload,
        scientific_completion_logical_record=completion,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_utility_identities=(
            utility_identities if utility_identities is not None else publication_utility_identities()
        ),
        context=publication.SyntheticPublicationContext(),
        durability_adapter=ConfirmedSyntheticAdapter(),
        promotion_adapter=promotion_adapter,
        staging_capacity_adapter=capacity_adapter,
    )


def confirmed(extra_available: int = 0):
    return CapacityAdapter(
        lambda required: response(
            publication.STAGING_CAPACITY_CONFIRMED,
            required,
            required + extra_available,
        )
    )


def assert_pre_staging_rejection(result, code):
    assert result.resource_failure_code == code
    if result.paths is not None:
        assert not result.paths.staging_directory.exists()
        assert not result.paths.final_directory.exists()
    assert all(
        item.logical_record["record_kind"] != "PUBLICATION_COMPLETED"
        for item in result.record_writes
    )


def policy_variant(kind: str):
    utility = publication_utility_identities()
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


@pytest.mark.parametrize(
    "kind",
    ("missing", "malformed", "wrong_order", "wrong_schema", "wrong_hash"),
)
def test_policy_identity_mismatch_fails_before_staging(tmp_path, kind):
    result = publish(
        tmp_path,
        utility_identities=policy_variant(kind),
        capacity_adapter=confirmed(),
        promotion_adapter=ExplodingPromotionAdapter(),
    )
    assert result.classification == publication.PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
    assert_pre_staging_rejection(
        result,
        schema.RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH,
    )


def test_correct_policy_identity_and_confirmed_capacity_can_complete(tmp_path):
    result = publish(
        tmp_path,
        capacity_adapter=confirmed(),
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    assert result.classification == publication.PUBLICATION_COMPLETED
    assert result.resource_failure_code is None
    assert result.resource_policy_identity == schema.resource_admissibility_policy_identity()
    assert result.required_staging_bytes == result.available_staging_bytes


def test_source_bundle_resource_limit_failure_has_no_staging(tmp_path, monkeypatch):
    original = schema.canonical_json_bytes_bounded

    def reject_source_bundle(value, max_bytes):
        if max_bytes == schema.MAX_PUBLICATION_SOURCE_BUNDLE_BYTES:
            raise schema.ResourceStructureLimitError(
                "source bundle exceeds resource limit",
                schema.CANONICAL_STRUCTURE_LIMIT_EXCEEDED,
            )
        return original(value, max_bytes)

    monkeypatch.setattr(schema, "canonical_json_bytes_bounded", reject_source_bundle)
    result = publish(tmp_path, capacity_adapter=confirmed())
    assert result.classification == publication.PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
    assert_pre_staging_rejection(result, schema.CANONICAL_STRUCTURE_LIMIT_EXCEEDED)


@pytest.mark.parametrize(
    "name,limit_attr,code",
    (
        (
            schema.PUBLICATION_RESULT_ARTIFACT_FILENAME,
            "MAX_PUBLICATION_RESULT_ARTIFACT_BYTES",
            schema.ARTIFACT_SIZE_LIMIT_EXCEEDED,
        ),
        (
            schema.PUBLICATION_EXECUTION_ENVELOPE_FILENAME,
            "MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES",
            schema.ARTIFACT_SIZE_LIMIT_EXCEEDED,
        ),
        (
            schema.PUBLICATION_SUMMARY_FILENAME,
            "MAX_PUBLICATION_SUMMARY_BYTES",
            schema.SUMMARY_SIZE_LIMIT_EXCEEDED,
        ),
    ),
)
def test_per_artifact_limit_failures_have_no_staging(
    tmp_path, monkeypatch, name, limit_attr, code
):
    monkeypatch.setattr(schema, limit_attr, 5)
    artifacts = {
        schema.PUBLICATION_RESULT_ARTIFACT_FILENAME: b"{}",
        schema.PUBLICATION_EXECUTION_ENVELOPE_FILENAME: b"{}",
        schema.PUBLICATION_SUMMARY_FILENAME: b"ok\n",
    }
    artifacts[name] = b"x" * 6
    monkeypatch.setattr(
        schema,
        "publication_artifact_byte_map_for_bundle",
        lambda bundle_payload: artifacts,
    )
    result = publish(tmp_path, capacity_adapter=confirmed())
    assert result.classification == publication.PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
    assert_pre_staging_rejection(result, code)


def test_artifact_count_and_artifact_set_failures_have_no_staging(tmp_path, monkeypatch):
    monkeypatch.setattr(
        schema,
        "publication_artifact_byte_map_for_bundle",
        lambda bundle_payload: {schema.PUBLICATION_RESULT_ARTIFACT_FILENAME: b"{}"},
    )
    result = publish(tmp_path, capacity_adapter=confirmed())
    assert_pre_staging_rejection(result, schema.ARTIFACT_SET_SIZE_LIMIT_EXCEEDED)

    def reject_set(artifact_bytes_by_name):
        raise schema.PublicationArtifactSetSizeLimitError("aggregate too large")

    monkeypatch.setattr(schema, "publication_artifact_byte_map_for_bundle", lambda bundle_payload: {
        schema.PUBLICATION_RESULT_ARTIFACT_FILENAME: b"{}",
        schema.PUBLICATION_EXECUTION_ENVELOPE_FILENAME: b"{}",
        schema.PUBLICATION_SUMMARY_FILENAME: b"ok\n",
    })
    monkeypatch.setattr(schema, "validate_publication_artifact_resource_map", reject_set)
    second_root = tmp_path / "second"
    second_root.mkdir()
    second = publish(second_root, capacity_adapter=confirmed())
    assert_pre_staging_rejection(second, schema.ARTIFACT_SET_SIZE_LIMIT_EXCEEDED)


def test_staging_write_exact_required_bytes_are_passed_to_capacity(tmp_path, monkeypatch):
    exact = schema.MAX_PUBLICATION_STAGING_WRITE_BYTES
    monkeypatch.setattr(
        schema,
        "validate_publication_artifact_resource_map",
        lambda artifact_bytes_by_name: exact,
    )
    adapter = confirmed()
    result = publish(
        tmp_path,
        capacity_adapter=adapter,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    assert result.classification == publication.PUBLICATION_COMPLETED
    assert adapter.calls == [exact]
    assert result.required_staging_bytes == exact


@pytest.mark.parametrize(
    "adapter,classification,code",
    (
        (
            None,
            publication.PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE,
            schema.RESOURCE_ADMISSIBILITY_INDETERMINATE,
        ),
        (
            CapacityAdapter(
                lambda required: response(
                    publication.STAGING_CAPACITY_UNAVAILABLE,
                    required,
                    required - 1,
                )
            ),
            publication.PUBLICATION_STAGING_SPACE_BUDGET_UNAVAILABLE,
            schema.STAGING_SPACE_BUDGET_UNAVAILABLE,
        ),
        (
            CapacityAdapter(
                lambda required: response(
                    publication.STAGING_CAPACITY_INDETERMINATE,
                    required,
                    None,
                )
            ),
            publication.PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE,
            schema.RESOURCE_ADMISSIBILITY_INDETERMINATE,
        ),
    ),
)
def test_capacity_failures_map_exactly_and_leave_no_staging(
    tmp_path, adapter, classification, code
):
    result = publish(tmp_path, capacity_adapter=adapter)
    assert result.classification == classification
    assert_pre_staging_rejection(result, code)
    assert [item.logical_record["record_kind"] for item in result.record_writes] == [
        "PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED",
        "PUBLICATION_ATTEMPTED",
    ]


@pytest.mark.parametrize(
    "factory",
    (
        lambda required: {"status": "UNKNOWN", "required_bytes": required, "available_bytes": None, "detail": "x"},
        lambda required: response(publication.STAGING_CAPACITY_CONFIRMED, True, required),
        lambda required: response(publication.STAGING_CAPACITY_CONFIRMED, -1, required),
        lambda required: response(publication.STAGING_CAPACITY_CONFIRMED, required + 1, required + 1),
        lambda required: response(publication.STAGING_CAPACITY_CONFIRMED, required, True),
        lambda required: response(publication.STAGING_CAPACITY_CONFIRMED, required, -1),
        lambda required: response(publication.STAGING_CAPACITY_CONFIRMED, required, required - 1),
        lambda required: response(publication.STAGING_CAPACITY_UNAVAILABLE, required, required),
        lambda required: response(publication.STAGING_CAPACITY_INDETERMINATE, required, 0),
        lambda required: {"status": publication.STAGING_CAPACITY_CONFIRMED},
    ),
)
def test_malformed_capacity_responses_are_indeterminate(tmp_path, factory):
    result = publish(tmp_path, capacity_adapter=CapacityAdapter(factory))
    assert result.classification == publication.PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE
    assert_pre_staging_rejection(result, schema.RESOURCE_ADMISSIBILITY_INDETERMINATE)


def test_confirmed_capacity_above_required_bytes_succeeds(tmp_path):
    result = publish(
        tmp_path,
        capacity_adapter=confirmed(extra_available=10),
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    assert result.classification == publication.PUBLICATION_COMPLETED
    assert result.available_staging_bytes == result.required_staging_bytes + 10


def test_later_stage_classifications_are_preserved_after_positive_capacity(tmp_path):
    result = publish(tmp_path, capacity_adapter=confirmed())
    assert result.classification == publication.PUBLICATION_PROMOTION_FAILED
    assert result.paths.staging_directory.exists()
    assert result.resource_failure_code is None


def test_resource_result_fields_preserve_dataclass_prefix():
    assert [field.name for field in fields(publication.PublicationProjectionResult)[:8]] == [
        "classification",
        "detail",
        "publication_projection_identity",
        "publication_chain_identity",
        "artifact_sha256s",
        "paths",
        "record_writes",
        "authority_state",
    ]
