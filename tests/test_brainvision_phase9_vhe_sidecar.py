"""Phase-9 VHE sidecar DTO, schema, and strict-validation coverage."""

from dataclasses import fields, replace
import json

import pytest

from brainvision.configuration import fresh_disabled_brainvision_configuration
from brainvision.vhe import (
    MAX_OCCURRENCE_COUNT,
    FastTrace,
    PersistentContext,
    SemanticRegister,
    SemanticRegisterEntry,
    VheState,
    VheValidationError,
    fresh_vhe_state,
)
from brainvision.vhe_sidecar import (
    VHE_SIDECAR_SCHEMA_ID,
    VheSidecarV1,
    VheSidecarValidationError,
    fresh_vhe_sidecar,
    vhe_sidecar_from_dict,
    vhe_sidecar_from_json_bytes,
)


def _configuration(*, theta: int = 0, watermark: int = -1):
    return replace(
        fresh_disabled_brainvision_configuration(
            stream_identity="camera-main",
            adapter_contract_id="descriptor-v1",
            theta=theta,
        ),
        last_accepted_source_sequence=watermark,
    )


def _sidecar(*, theta: int = 0, watermark: int = -1) -> VheSidecarV1:
    return fresh_vhe_sidecar(_configuration(theta=theta, watermark=watermark))


def _raw(*, theta: int = 0, watermark: int = -1) -> dict[str, object]:
    return _sidecar(theta=theta, watermark=watermark).to_dict()


def _semantic_state(*, entries: tuple[SemanticRegisterEntry, ...], open_token: str) -> VheState:
    return VheState(
        fast_trace=FastTrace(amplitude_1_q=500_000, amplitude_2_q=0, remaining_ns=1),
        persistent_context=PersistentContext(luminance_q=1, contrast_q=-2, orientation_q=3),
        semantic_register=SemanticRegister(entries=entries, open_semantic_event_class=open_token),
    )


def test_exact_sidecar_and_nested_field_sets() -> None:
    raw = _raw()

    assert tuple(raw) == (
        "schema_id",
        "configuration_schema_id",
        "stream_identity",
        "adapter_contract_id",
        "accepted_source_sequence",
        "expected_operator_id",
        "expected_projection_id",
        "modulation_schema_id",
        "modulation_mapping_id",
        "modulation_profile_schema_id",
        "theta",
        "modulation_profile_id",
        "committed_active_time_ns",
        "vhe_state",
    )
    assert set(raw["vhe_state"]) == {
        "fast_trace",
        "persistent_context",
        "semantic_register",
    }
    assert set(raw["vhe_state"]["fast_trace"]) == {
        "amplitude_1_q",
        "amplitude_2_q",
        "remaining_ns",
    }
    assert set(raw["vhe_state"]["persistent_context"]) == {
        "luminance_q",
        "contrast_q",
        "orientation_q",
    }
    assert set(raw["vhe_state"]["semantic_register"]) == {
        "entries",
        "open_semantic_event_class",
    }


def test_canonical_bytes_and_strict_round_trip() -> None:
    sidecar = _sidecar(theta=-1, watermark=7)
    expected = json.dumps(
        sidecar.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")

    assert sidecar.to_canonical_json_bytes() == expected
    assert vhe_sidecar_from_dict(sidecar.to_dict()) == sidecar
    assert vhe_sidecar_from_json_bytes(sidecar.to_canonical_json_bytes()) == sidecar


@pytest.mark.parametrize(
    ("replacement", "field"),
    (
        ((b'"theta":0,', b'"theta":0,"theta":1,'), "theta"),
        ((b'"amplitude_1_q":0,', b'"amplitude_1_q":0,"amplitude_1_q":1,'), "amplitude_1_q"),
    ),
)
def test_json_bytes_reject_duplicate_top_level_and_nested_keys(
    replacement: tuple[bytes, bytes], field: str
) -> None:
    duplicate = _sidecar().to_canonical_json_bytes().replace(*replacement)

    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_json_bytes(duplicate)

    assert (error.value.field, error.value.reason) == (field, "duplicate_field")


def test_missing_unknown_and_nested_field_sets_fail_closed() -> None:
    missing = _raw()
    del missing["stream_identity"]
    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(missing)
    assert error.value.reason == "missing_field"

    unknown = _raw()
    unknown["extra"] = 1
    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(unknown)
    assert error.value.reason == "unknown_field"

    nested = _raw()
    del nested["vhe_state"]["fast_trace"]["remaining_ns"]
    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(nested)
    assert error.value.reason == "missing_field"

    nested = _raw()
    nested["vhe_state"]["persistent_context"]["extra"] = 1
    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(nested)
    assert error.value.reason == "unknown_field"


def test_schema_and_configuration_schema_are_exact() -> None:
    raw = _raw()
    raw["schema_id"] = "other"
    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(raw)
    assert (error.value.field, error.value.reason) == ("schema_id", "schema_mismatch")

    raw = _raw()
    raw["configuration_schema_id"] = "other"
    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(raw)
    assert (error.value.field, error.value.reason) == (
        "configuration_schema_id",
        "configuration_schema_mismatch",
    )


@pytest.mark.parametrize(
    ("value", "reason"),
    ((-2, "out_of_range"), ((2**63), "out_of_range"), (True, "must_be_exact_int")),
)
def test_accepted_sequence_rejects_invalid_values(value: object, reason: str) -> None:
    raw = _raw()
    raw["accepted_source_sequence"] = value

    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(raw)
    assert (error.value.field, error.value.reason) == ("accepted_source_sequence", reason)


def test_accepted_sequence_fresh_and_maximum_are_valid() -> None:
    assert _sidecar().accepted_source_sequence == -1
    assert _sidecar(watermark=(2**63) - 1).accepted_source_sequence == (2**63) - 1


def test_committed_active_time_is_exact_nonnegative_and_unbounded() -> None:
    assert replace(_sidecar(), committed_active_time_ns=10**100).committed_active_time_ns == 10**100

    for value, reason in ((-1, "must_be_nonnegative"), (True, "must_be_exact_int")):
        with pytest.raises(VheSidecarValidationError) as error:
            replace(_sidecar(), committed_active_time_ns=value)
        assert (error.value.field, error.value.reason) == ("committed_active_time_ns", reason)


@pytest.mark.parametrize("field", ("stream_identity", "adapter_contract_id"))
def test_stream_and_adapter_use_exact_phase2_identifier_syntax(field: str) -> None:
    raw = _raw()
    raw[field] = "Bad/identifier"

    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(raw)
    assert (error.value.field, error.value.reason) == (field, "invalid_identifier")


@pytest.mark.parametrize(
    ("field", "reason"),
    (
        ("expected_operator_id", "operator_identity_mismatch"),
        ("expected_projection_id", "projection_identity_mismatch"),
        ("modulation_schema_id", "modulation_schema_mismatch"),
        ("modulation_mapping_id", "modulation_mapping_mismatch"),
        ("modulation_profile_schema_id", "modulation_profile_schema_mismatch"),
    ),
)
def test_frozen_continuation_identity_fields_are_exact(field: str, reason: str) -> None:
    raw = _raw()
    raw[field] = "other"

    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(raw)
    assert (error.value.field, error.value.reason) == (field, reason)


@pytest.mark.parametrize("theta", (-1, 0, 1))
def test_all_frozen_theta_profile_pairs_are_valid(theta: int) -> None:
    assert _sidecar(theta=theta).theta == theta


def test_mismatched_theta_profile_is_rejected() -> None:
    raw = _raw(theta=-1)
    raw["theta"] = 1

    with pytest.raises(VheSidecarValidationError) as error:
        vhe_sidecar_from_dict(raw)
    assert (error.value.field, error.value.reason) == (
        "modulation_profile_id",
        "modulation_profile_mismatch",
    )


def test_fast_trace_and_persistent_context_reconstruct_frozen_runtime_types() -> None:
    raw = _raw()
    raw["vhe_state"]["fast_trace"] = {
        "amplitude_1_q": -1_000_000,
        "amplitude_2_q": 1_000_000,
        "remaining_ns": 5_000_000_000,
    }
    raw["vhe_state"]["persistent_context"] = {
        "luminance_q": -1_000_000,
        "contrast_q": 1_000_000,
        "orientation_q": 0,
    }
    sidecar = vhe_sidecar_from_dict(raw)
    assert sidecar.vhe_state.fast_trace.remaining_ns == 5_000_000_000
    assert sidecar.vhe_state.persistent_context.contrast_q == 1_000_000


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("fast_trace", "remaining_ns"), 0),
        (("persistent_context", "luminance_q"), 1_000_001),
    ),
)
def test_invalid_frozen_vhe_values_are_rejected(
    path: tuple[str, str], value: int
) -> None:
    raw = _raw()
    raw["vhe_state"][path[0]][path[1]] = value
    if path[0] == "fast_trace":
        raw["vhe_state"]["fast_trace"]["amplitude_1_q"] = 1

    with pytest.raises(VheValidationError):
        vhe_sidecar_from_dict(raw)


def test_semantic_register_round_trips_sorted_entries_and_frozen_boundaries() -> None:
    first = SemanticRegisterEntry(
        semantic_event_class="detector:alpha",
        first_seen_active_time_ns=2,
        last_seen_active_time_ns=3,
        occurrence_count=1,
    )
    second = SemanticRegisterEntry(
        semantic_event_class="detector:beta",
        first_seen_active_time_ns=4,
        last_seen_active_time_ns=5,
        occurrence_count=MAX_OCCURRENCE_COUNT,
    )
    sidecar = replace(
        _sidecar(),
        committed_active_time_ns=5,
        vhe_state=_semantic_state(entries=(first, second), open_token="detector:beta"),
    )

    assert vhe_sidecar_from_dict(sidecar.to_dict()) == sidecar
    assert type(sidecar.vhe_state.semantic_register.entries) is tuple


@pytest.mark.parametrize(
    ("entries", "open_token"),
    (
        (
            [
                {
                    "semantic_event_class": "detector:beta",
                    "first_seen_active_time_ns": 0,
                    "last_seen_active_time_ns": 0,
                    "occurrence_count": 1,
                },
                {
                    "semantic_event_class": "detector:alpha",
                    "first_seen_active_time_ns": 0,
                    "last_seen_active_time_ns": 0,
                    "occurrence_count": 1,
                },
            ],
            "detector:beta",
        ),
        (
            [
                {
                    "semantic_event_class": "detector:alpha",
                    "first_seen_active_time_ns": 0,
                    "last_seen_active_time_ns": 0,
                    "occurrence_count": 1,
                },
                {
                    "semantic_event_class": "detector:alpha",
                    "first_seen_active_time_ns": 0,
                    "last_seen_active_time_ns": 0,
                    "occurrence_count": 1,
                },
            ],
            "detector:alpha",
        ),
    ),
)
def test_semantic_register_rejects_unsorted_or_duplicate_tokens(
    entries: list[dict[str, object]], open_token: str
) -> None:
    raw = _raw()
    raw["vhe_state"]["semantic_register"] = {
        "entries": entries,
        "open_semantic_event_class": open_token,
    }

    with pytest.raises(VheValidationError):
        vhe_sidecar_from_dict(raw)


def test_semantic_open_reference_timestamp_and_count_validation() -> None:
    raw = _raw()
    raw["vhe_state"]["semantic_register"] = {
        "entries": [
            {
                "semantic_event_class": "detector:alpha",
                "first_seen_active_time_ns": 2,
                "last_seen_active_time_ns": 1,
                "occurrence_count": 0,
            }
        ],
        "open_semantic_event_class": "detector:missing",
    }
    with pytest.raises(VheValidationError):
        vhe_sidecar_from_dict(raw)

    entry = SemanticRegisterEntry(
        semantic_event_class="detector:alpha",
        first_seen_active_time_ns=1,
        last_seen_active_time_ns=2,
        occurrence_count=1,
    )
    with pytest.raises(VheSidecarValidationError) as error:
        replace(
            _sidecar(),
            committed_active_time_ns=1,
            vhe_state=_semantic_state(entries=(entry,), open_token="detector:alpha"),
        )
    assert error.value.reason == "semantic_time_after_committed_time"


def test_fresh_builder_copies_configuration_sequence_and_uses_exact_fresh_state() -> None:
    configuration = _configuration(theta=1, watermark=12)
    sidecar = fresh_vhe_sidecar(configuration)

    assert sidecar.accepted_source_sequence == 12
    assert sidecar.committed_active_time_ns == 0
    assert sidecar.vhe_state == fresh_vhe_state()
    assert sidecar.stream_identity == configuration.stream_identity


def test_to_dict_is_copy_safe_and_has_no_lifecycle_projection_or_diagnostics() -> None:
    sidecar = _sidecar()
    rendered = sidecar.to_dict()
    rendered["vhe_state"]["fast_trace"]["amplitude_1_q"] = 99
    rendered["vhe_state"]["semantic_register"]["entries"].append({"extra": 1})

    assert sidecar.vhe_state == fresh_vhe_state()
    encoded = sidecar.to_canonical_json_bytes()
    for forbidden in (
        b"lifecycle_status",
        b"current_activity_code",
        b"retained_history_code",
        b"present_history_relation_code",
        b"trajectory_code",
        b"open_event_class",
        b"recurrence_code",
        b"write_gate_q",
        b"clamped_orientation_q",
    ):
        assert forbidden not in encoded


def test_dto_has_only_persisted_sidecar_state_fields() -> None:
    assert tuple(field.name for field in fields(VheSidecarV1)) == (
        "configuration_schema_id",
        "stream_identity",
        "adapter_contract_id",
        "accepted_source_sequence",
        "expected_operator_id",
        "expected_projection_id",
        "modulation_schema_id",
        "modulation_mapping_id",
        "modulation_profile_schema_id",
        "theta",
        "modulation_profile_id",
        "committed_active_time_ns",
        "vhe_state",
    )
    assert _sidecar().schema_id == VHE_SIDECAR_SCHEMA_ID
