"""Phase-8 Brainvision configuration DTO and validation coverage."""

from dataclasses import fields

import pytest

from brainvision.character_modulation import modulation_profile_id
from brainvision.configuration import (
    BrainvisionConfigurationV1,
    BrainvisionConfigurationValidationError,
    CONFIGURATION_SCHEMA_ID,
    FRESH_LAST_ACCEPTED_SOURCE_SEQUENCE,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DISABLED,
    LIFECYCLE_SUSPENDED,
    MAX_LAST_ACCEPTED_SOURCE_SEQUENCE,
    configuration_from_dict,
    configuration_from_json_bytes,
    fresh_disabled_brainvision_configuration,
)


def _configuration(*, theta: int = 0) -> BrainvisionConfigurationV1:
    return fresh_disabled_brainvision_configuration(
        stream_identity="camera-main",
        adapter_contract_id="descriptor-v1",
        theta=theta,
    )


def _raw_configuration(*, theta: int = 0) -> dict[str, object]:
    return _configuration(theta=theta).to_dict()


def test_exact_field_mapping_and_canonical_bytes() -> None:
    configuration = _configuration()

    assert tuple(configuration.to_dict()) == (
        "schema_id",
        "lifecycle_status",
        "stream_identity",
        "adapter_contract_id",
        "last_accepted_source_sequence",
        "expected_operator_id",
        "expected_projection_id",
        "modulation_schema_id",
        "modulation_mapping_id",
        "modulation_profile_schema_id",
        "theta",
        "modulation_profile_id",
    )
    assert configuration.to_canonical_json_bytes() == (
        b'{"adapter_contract_id":"descriptor-v1","expected_operator_id":"'
        b'bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb",'
        b'"expected_projection_id":"bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f",'
        b'"last_accepted_source_sequence":-1,"lifecycle_status":"disabled",'
        b'"modulation_mapping_id":"bvmodmap1_f8b41a1987437410613157ae403d10ac12fbce3b34cc760f0cc8376193206aeb",'
        b'"modulation_profile_id":"bvmodprof1_9f65a350c2526bc63733e9267d7846ce4eace56a6c4ec3261bfc748a18287abc",'
        b'"modulation_profile_schema_id":"brainvision.character_modulation.profile.v1",'
        b'"modulation_schema_id":"brainvision.character_modulation.v1",'
        b'"schema_id":"brainvision.configuration.v1","stream_identity":"camera-main","theta":0}'
    )


def test_strict_round_trip_from_mapping_and_json_bytes() -> None:
    configuration = _configuration(theta=-1)

    assert configuration_from_dict(configuration.to_dict()) == configuration
    assert configuration_from_json_bytes(configuration.to_canonical_json_bytes()) == configuration


def test_json_bytes_reject_duplicate_authoritative_fields() -> None:
    duplicate_theta = _configuration().to_canonical_json_bytes().replace(
        b'"theta":0}', b'"theta":0,"theta":1}'
    )

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        configuration_from_json_bytes(duplicate_theta)

    assert (error.value.field, error.value.reason) == ("theta", "duplicate_field")


@pytest.mark.parametrize(
    "status", (LIFECYCLE_DISABLED, LIFECYCLE_ACTIVE, LIFECYCLE_SUSPENDED)
)
def test_all_frozen_lifecycle_statuses_are_accepted(status: str) -> None:
    raw = _raw_configuration()
    raw["lifecycle_status"] = status

    assert configuration_from_dict(raw).lifecycle_status == status


@pytest.mark.parametrize("status", ("reset", "unknown", "DISABLED", None))
def test_closed_lifecycle_vocabulary_rejects_nonstatus_values(status: object) -> None:
    raw = _raw_configuration()
    raw["lifecycle_status"] = status

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        configuration_from_dict(raw)

    assert (error.value.field, error.value.reason) == (
        "lifecycle_status",
        "invalid_lifecycle_status",
    )


def test_watermark_boundaries_and_fresh_value() -> None:
    assert _configuration().last_accepted_source_sequence == FRESH_LAST_ACCEPTED_SOURCE_SEQUENCE

    raw = _raw_configuration()
    raw["last_accepted_source_sequence"] = MAX_LAST_ACCEPTED_SOURCE_SEQUENCE
    assert (
        configuration_from_dict(raw).last_accepted_source_sequence
        == MAX_LAST_ACCEPTED_SOURCE_SEQUENCE
    )


@pytest.mark.parametrize(
    ("value", "reason"),
    (
        (-2, "out_of_range"),
        (MAX_LAST_ACCEPTED_SOURCE_SEQUENCE + 1, "out_of_range"),
        (True, "must_be_exact_int"),
        (0.0, "must_be_exact_int"),
    ),
)
def test_watermark_requires_an_exact_bounded_integer(value: object, reason: str) -> None:
    raw = _raw_configuration()
    raw["last_accepted_source_sequence"] = value

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        configuration_from_dict(raw)

    assert (error.value.field, error.value.reason) == (
        "last_accepted_source_sequence",
        reason,
    )


@pytest.mark.parametrize("field", ("stream_identity", "adapter_contract_id"))
@pytest.mark.parametrize("value", ("", "Camera", "camera/main", "camera\\main", "a" * 65, 7))
def test_stream_and_adapter_identifiers_use_the_exact_phase2_syntax(
    field: str, value: object
) -> None:
    raw = _raw_configuration()
    raw[field] = value

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        configuration_from_dict(raw)

    assert (error.value.field, error.value.reason) == (field, "invalid_identifier")


def test_missing_and_unknown_fields_fail_closed() -> None:
    missing = _raw_configuration()
    del missing["adapter_contract_id"]
    with pytest.raises(BrainvisionConfigurationValidationError) as missing_error:
        configuration_from_dict(missing)
    assert (missing_error.value.field, missing_error.value.reason) == (
        "adapter_contract_id",
        "missing_field",
    )

    unknown = _raw_configuration()
    unknown["extra"] = "not admitted"
    with pytest.raises(BrainvisionConfigurationValidationError) as unknown_error:
        configuration_from_dict(unknown)
    assert (unknown_error.value.field, unknown_error.value.reason) == (
        "extra",
        "unknown_field",
    )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("expected_operator_id", "other", "operator_identity_mismatch"),
        ("expected_projection_id", "other", "projection_identity_mismatch"),
        ("modulation_schema_id", "other", "modulation_schema_mismatch"),
        ("modulation_mapping_id", "other", "modulation_mapping_mismatch"),
        (
            "modulation_profile_schema_id",
            "other",
            "modulation_profile_schema_mismatch",
        ),
    ),
)
def test_frozen_base_and_modulation_identities_are_exact(
    field: str, value: str, reason: str
) -> None:
    raw = _raw_configuration()
    raw[field] = value

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        configuration_from_dict(raw)

    assert (error.value.field, error.value.reason) == (field, reason)


@pytest.mark.parametrize(
    ("theta", "reason"),
    ((True, "must_be_exact_int"), (0.0, "must_be_exact_int"), (-2, "out_of_range"), (2, "out_of_range")),
)
def test_theta_requires_an_exact_admitted_phase7_value(theta: object, reason: str) -> None:
    raw = _raw_configuration()
    raw["theta"] = theta

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        configuration_from_dict(raw)

    assert (error.value.field, error.value.reason) == ("theta", reason)


@pytest.mark.parametrize("theta", (-1, 0, 1))
def test_all_legal_theta_profile_pairs_are_accepted(theta: int) -> None:
    configuration = _configuration(theta=theta)

    assert configuration.theta == theta
    assert configuration.modulation_profile_id == modulation_profile_id(theta)


def test_cross_theta_profile_pair_is_rejected() -> None:
    raw = _raw_configuration(theta=-1)
    raw["theta"] = 1

    with pytest.raises(BrainvisionConfigurationValidationError) as error:
        configuration_from_dict(raw)

    assert (error.value.field, error.value.reason) == (
        "modulation_profile_id",
        "modulation_profile_mismatch",
    )


def test_fresh_builder_is_disabled_with_the_fresh_watermark() -> None:
    configuration = fresh_disabled_brainvision_configuration(
        stream_identity="camera-secondary",
        adapter_contract_id="descriptor-v2",
        theta=1,
    )

    assert configuration.lifecycle_status == LIFECYCLE_DISABLED
    assert configuration.last_accepted_source_sequence == -1
    assert configuration.schema_id == CONFIGURATION_SCHEMA_ID


def test_dto_has_no_extra_runtime_state_or_configuration_hash() -> None:
    configuration = _configuration()

    assert tuple(field.name for field in fields(BrainvisionConfigurationV1)) == (
        "lifecycle_status",
        "stream_identity",
        "adapter_contract_id",
        "last_accepted_source_sequence",
        "expected_operator_id",
        "expected_projection_id",
        "modulation_schema_id",
        "modulation_mapping_id",
        "modulation_profile_schema_id",
        "theta",
        "modulation_profile_id",
    )
    assert "configuration_id" not in configuration.to_dict()
    assert not hasattr(configuration, "configuration_id")
