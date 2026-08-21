"""Focused tests for the frozen Phase-2 FIRSTHAND_VISUAL contract."""

from __future__ import annotations

import ast
import base64
import json
from pathlib import Path
import subprocess
import sys

import pytest

from brainvision.fixtures import D0, DA
from brainvision.observation import (
    DESCRIPTOR_COORDINATE_ORDER,
    DESCRIPTOR_SCHEMA_ID,
    IDENTITY_SCHEMA_ID,
    OBSERVATION_SCHEMA_ID,
    FirsthandVisualObservationV1,
    LowLevelVisualDescriptorV1,
    ObservationProvenanceType,
    ObservationValidationError,
    decode_observation_id,
    derive_observation_id,
    validate_firsthand_visual_observation,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "brainvision"


def _observation(
    *,
    descriptor: LowLevelVisualDescriptorV1 = D0,
    stream_identity: str = "cam-a",
    source_sequence: int = 7,
    adapter_id: str = "camera-adapter",
    adapter_contract_id: str = "camera-contract-v1",
    source_capture_time_unix_ns: int | None = None,
    confidence_q: int | None = None,
    semantic_event_class: str | None = None,
    world_event_id: str | None = None,
) -> FirsthandVisualObservationV1:
    return FirsthandVisualObservationV1(
        provenance_type=ObservationProvenanceType.FIRSTHAND_VISUAL,
        stream_identity=stream_identity,
        source_sequence=source_sequence,
        observation_id=derive_observation_id(stream_identity, source_sequence),
        descriptor=descriptor,
        adapter_id=adapter_id,
        adapter_contract_id=adapter_contract_id,
        source_capture_time_unix_ns=source_capture_time_unix_ns,
        confidence_q=confidence_q,
        semantic_event_class=semantic_event_class,
        world_event_id=world_event_id,
    )


def test_descriptor_is_frozen_and_uses_the_exact_schema_shape() -> None:
    descriptor = LowLevelVisualDescriptorV1(
        mean_luminance_q=500_000,
        mean_adjacent_luminance_difference_q=0,
    )
    assert descriptor.to_dict() == {
        "schema_id": DESCRIPTOR_SCHEMA_ID,
        "mean_luminance_q": 500_000,
        "mean_adjacent_luminance_difference_q": 0,
    }
    with pytest.raises(AttributeError):
        descriptor.mean_luminance_q = 1  # type: ignore[misc]


def test_descriptor_coordinate_order_is_exact_and_independent_of_json_key_order() -> None:
    assert DESCRIPTOR_COORDINATE_ORDER == (
        "mean_luminance_q",
        "mean_adjacent_luminance_difference_q",
    )


@pytest.mark.parametrize("field", ["mean_luminance_q", "mean_adjacent_luminance_difference_q"])
@pytest.mark.parametrize("value", [-1, 1_000_001, 0.0, True, "0"])
def test_descriptor_rejects_non_exact_bounded_integer_values(field: str, value: object) -> None:
    values: dict[str, object] = {
        "mean_luminance_q": 0,
        "mean_adjacent_luminance_difference_q": 0,
    }
    values[field] = value
    with pytest.raises(ObservationValidationError) as failure:
        LowLevelVisualDescriptorV1(**values)  # type: ignore[arg-type]
    assert failure.value.field == field


def test_descriptor_strict_round_trip_and_canonical_serialization() -> None:
    descriptor = LowLevelVisualDescriptorV1(
        mean_luminance_q=123_456,
        mean_adjacent_luminance_difference_q=654_321,
    )
    assert LowLevelVisualDescriptorV1.from_dict(descriptor.to_dict()) == descriptor
    assert descriptor.to_canonical_json_bytes() == (
        b'{"mean_adjacent_luminance_difference_q":654321,"mean_luminance_q":123456,'
        b'"schema_id":"brainvision.low_level_descriptor.v1"}'
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw.pop("schema_id"),
        lambda raw: raw.__setitem__("unfrozen", "value"),
        lambda raw: raw.__setitem__("schema_id", "wrong.schema"),
    ],
)
def test_descriptor_rejects_missing_unknown_or_wrong_schema(mutation: object) -> None:
    raw = D0.to_dict()
    mutation(raw)  # type: ignore[operator]
    with pytest.raises(ObservationValidationError):
        LowLevelVisualDescriptorV1.from_dict(raw)


def test_identity_exact_vector_is_reversible_and_canonically_bound() -> None:
    expected_payload = (
        b'{"identity_schema":"brainvision.observation-id.v1","source_sequence":7,'
        b'"stream_identity":"cam-a"}'
    )
    expected_id = (
        "bvobs1_eyJpZGVudGl0eV9zY2hlbWEiOiJicmFpbnZpc2lvbi5vYnNlcnZhdGlvbi1pZC52MSIs"
        "InNvdXJjZV9zZXF1ZW5jZSI6Nywic3RyZWFtX2lkZW50aXR5IjoiY2FtLWEifQ"
    )
    assert json.dumps(
        {
            "identity_schema": IDENTITY_SCHEMA_ID,
            "source_sequence": 7,
            "stream_identity": "cam-a",
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii") == expected_payload
    assert derive_observation_id("cam-a", 7) == expected_id
    assert decode_observation_id(expected_id) == ("cam-a", 7)


def test_identity_changes_only_for_stream_or_sequence() -> None:
    baseline = derive_observation_id("cam-a", 7)
    assert derive_observation_id("cam-b", 7) != baseline
    assert derive_observation_id("cam-a", 8) != baseline

    changed_adapter = _observation(adapter_id="camera-adapter-v2")
    assert changed_adapter.observation_id == baseline

    changed_adapter_contract = _observation(adapter_contract_id="camera-contract-v2")
    assert changed_adapter_contract.observation_id == baseline

    changed_metadata = _observation(
        descriptor=DA,
        source_capture_time_unix_ns=1_725_000_000_000_000_000,
        confidence_q=123_456,
        semantic_event_class="detector:scene_change",
        world_event_id="external:world-17",
    )
    assert changed_metadata.observation_id == baseline


def _encode_identity_payload(payload: dict[str, object]) -> str:
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("ascii")
    ).rstrip(b"=")
    return "bvobs1_" + encoded.decode("ascii")


@pytest.mark.parametrize(
    ("observation_id", "reason"),
    [
        ("not-bvobs1", "invalid_prefix"),
        ("bvobs1_!", "invalid_base64url"),
        ("bvobs1__w", "invalid_identity_payload"),
        (
            _encode_identity_payload(
                {
                    "identity_schema": "wrong.identity.schema",
                    "source_sequence": 7,
                    "stream_identity": "cam-a",
                }
            ),
            "incorrect_identity_schema",
        ),
        (
            _encode_identity_payload(
                {
                    "identity_schema": IDENTITY_SCHEMA_ID,
                    "source_sequence": 7,
                    "stream_identity": "cam-a",
                    "unexpected": "field",
                }
            ),
            "unexpected_field_set",
        ),
        (
            _encode_identity_payload(
                {
                    "stream_identity": "cam-a",
                    "source_sequence": 7,
                    "identity_schema": IDENTITY_SCHEMA_ID,
                }
            ),
            "noncanonical_identity_encoding",
        ),
    ],
)
def test_decode_observation_id_rejects_representative_malformed_inputs(
    observation_id: str,
    reason: str,
) -> None:
    with pytest.raises(ObservationValidationError) as failure:
        decode_observation_id(observation_id)
    assert failure.value.field == "observation_id"
    assert failure.value.reason == reason


@pytest.mark.parametrize("forbidden_key", ["visual_time", "lifecycle_status", "vhe_state", "projection"])
def test_observation_rejects_adapter_supplied_later_phase_fields(forbidden_key: str) -> None:
    raw = _observation().to_dict()
    raw[forbidden_key] = "forbidden"
    with pytest.raises(ObservationValidationError) as failure:
        validate_firsthand_visual_observation(raw)
    assert failure.value.field == "observation"


def test_observation_is_frozen_has_exact_shape_and_strict_round_trip() -> None:
    observation = _observation()
    expected_keys = {
        "schema_id",
        "provenance_type",
        "stream_identity",
        "source_sequence",
        "observation_id",
        "descriptor",
        "adapter_id",
        "adapter_contract_id",
        "source_capture_time_unix_ns",
        "confidence_q",
        "semantic_event_class",
        "world_event_id",
    }
    assert set(observation.to_dict()) == expected_keys
    assert observation.to_dict()["schema_id"] == OBSERVATION_SCHEMA_ID
    assert observation.to_dict()["provenance_type"] == "FIRSTHAND_VISUAL"
    assert observation.to_dict()["source_capture_time_unix_ns"] is None
    assert observation.to_dict()["confidence_q"] is None
    assert observation.to_dict()["semantic_event_class"] is None
    assert observation.to_dict()["world_event_id"] is None
    assert FirsthandVisualObservationV1.from_dict(observation.to_dict()) == observation
    with pytest.raises(AttributeError):
        observation.source_sequence = 8  # type: ignore[misc]


def test_observation_full_canonical_serialization_is_exact() -> None:
    observation = _observation()
    assert observation.to_canonical_json_bytes() == (
        b'{"adapter_contract_id":"camera-contract-v1","adapter_id":"camera-adapter",'
        b'"confidence_q":null,"descriptor":{"mean_adjacent_luminance_difference_q":0,'
        b'"mean_luminance_q":500000,"schema_id":"brainvision.low_level_descriptor.v1"},'
        b'"observation_id":"bvobs1_eyJpZGVudGl0eV9zY2hlbWEiOiJicmFpbnZpc2lvbi5vYnNlcnZhdGlvbi1pZC52MSIs'
        b'InNvdXJjZV9zZXF1ZW5jZSI6Nywic3RyZWFtX2lkZW50aXR5IjoiY2FtLWEifQ",'
        b'"provenance_type":"FIRSTHAND_VISUAL",'
        b'"schema_id":"brainvision.firsthand_visual_observation.v1",'
        b'"semantic_event_class":null,"source_capture_time_unix_ns":null,'
        b'"source_sequence":7,"stream_identity":"cam-a","world_event_id":null}'
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provenance_type", "REPORTED_VISUAL"),
        ("stream_identity", "Cam-A"),
        ("source_sequence", True),
        ("source_sequence", -1),
        ("adapter_id", "adapter id"),
        ("adapter_contract_id", None),
        ("source_capture_time_unix_ns", 1.0),
        ("confidence_q", True),
        ("confidence_q", 1_000_001),
        ("semantic_event_class", "scene change"),
        ("world_event_id", "world event"),
    ],
)
def test_observation_rejects_invalid_values_without_coercion(field: str, value: object) -> None:
    raw = _observation().to_dict()
    raw[field] = value
    with pytest.raises(ObservationValidationError):
        FirsthandVisualObservationV1.from_dict(raw)


def test_observation_rejects_missing_unknown_or_mismatched_identity() -> None:
    missing = _observation().to_dict()
    missing.pop("adapter_contract_id")
    with pytest.raises(ObservationValidationError):
        FirsthandVisualObservationV1.from_dict(missing)

    unknown = _observation().to_dict()
    unknown["admitted"] = True
    with pytest.raises(ObservationValidationError):
        FirsthandVisualObservationV1.from_dict(unknown)

    mismatched = _observation().to_dict()
    mismatched["observation_id"] = derive_observation_id("cam-a", 8)
    with pytest.raises(ObservationValidationError) as failure:
        FirsthandVisualObservationV1.from_dict(mismatched)
    assert failure.value.field == "observation_id"


def test_phase2_modules_are_isolated_from_research_and_runtime() -> None:
    code = """
import json
import sys
import brainvision.observation
import brainvision.fixtures
print(json.dumps(sorted(sys.modules)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    loaded = json.loads(completed.stdout)
    prohibited_prefixes = (
        "research.brainvision",
        "torment_service",
        "cognition",
        "memory",
        "srg",
        "hivermind",
    )
    assert not any(name.startswith(prohibited_prefixes) for name in loaded)


def test_phase2_source_has_no_phase3_or_runtime_implementation() -> None:
    allowed_stdlib_imports = {
        "__future__",
        "base64",
        "collections.abc",
        "dataclasses",
        "json",
        "re",
        "enum",
        "typing",
        "hashlib",
    }
    for path in (PACKAGE_ROOT / "observation.py", PACKAGE_ROOT / "fixtures.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
        normalized_imports = {name.lstrip(".") for name in imports}
        assert all(
            name in allowed_stdlib_imports or name == "brainvision.observation"
            for name in normalized_imports
        )

        declared_names = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert not declared_names & {
            "VisualClock",
            "VHE",
            "Projection",
            "BrainvisionConfig",
            "BrainvisionSidecar",
            "BrainvisionRegistry",
            "ingest_visual_observation",
        }
