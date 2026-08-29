from __future__ import annotations

import uuid

import pytest

from torment_service.substrate.errors import SubstrateIdentifierError
from torment_service.substrate.ids import (
    NATIVE_ID_BYTE_LENGTH,
    generate_native_id,
    native_id_bytes_from_text,
    native_id_from_bytes,
    native_id_from_text,
    native_id_text_from_bytes,
    native_id_to_bytes,
    native_id_to_text,
)


def test_native_id_generation_is_uuid4_and_16_byte_round_trip() -> None:
    native_id = generate_native_id()

    assert native_id.version == 4
    raw = native_id_to_bytes(native_id)
    assert len(raw) == NATIVE_ID_BYTE_LENGTH
    assert native_id_from_bytes(raw) == native_id


def test_native_id_canonical_text_round_trip() -> None:
    native_id = uuid.UUID("12345678-1234-4234-9234-123456789abc")

    text = native_id_to_text(native_id)
    assert text == "12345678-1234-4234-9234-123456789abc"
    assert native_id_from_text(text) == native_id
    assert native_id_text_from_bytes(native_id_bytes_from_text(text)) == text


@pytest.mark.parametrize("value", [b"", b"short", b"x" * 15, b"x" * 17, None])
def test_native_id_rejects_invalid_byte_shape(value: object) -> None:
    with pytest.raises(SubstrateIdentifierError):
        native_id_from_bytes(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", ["not-a-uuid", "{12345678-1234-4234-9234-123456789abc}", "12345678-1234-4234-9234-123456789ABC", None])
def test_native_id_rejects_invalid_or_noncanonical_text(value: object) -> None:
    with pytest.raises(SubstrateIdentifierError):
        native_id_from_text(value)  # type: ignore[arg-type]


def test_native_id_rejects_non_v4_uuid_text_and_bytes() -> None:
    non_v4 = uuid.UUID("12345678-1234-1234-9234-123456789abc")

    with pytest.raises(SubstrateIdentifierError):
        native_id_from_text(str(non_v4))
    with pytest.raises(SubstrateIdentifierError):
        native_id_from_bytes(non_v4.bytes)
