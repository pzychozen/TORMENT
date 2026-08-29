"""Native UUIDv4 identity codec for the substrate.

SQLite storage is always the 16-byte UUID representation; textual UUIDs are
diagnostic/API boundary values only.
"""

from __future__ import annotations

import uuid
from typing import Final

from .errors import SubstrateIdentifierError


NATIVE_ID_BYTE_LENGTH: Final[int] = 16


def generate_native_id() -> uuid.UUID:
    """Return a new native UUIDv4 without embedding timestamp semantics."""
    return uuid.uuid4()


def native_id_to_bytes(value: uuid.UUID) -> bytes:
    """Encode a UUID as the exact 16-byte SQLite BLOB representation."""
    return _require_uuid4(value).bytes


def native_id_from_bytes(value: bytes | bytearray | memoryview) -> uuid.UUID:
    """Decode exactly 16 bytes into a native UUID."""
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise SubstrateIdentifierError("native ID bytes are required")
    raw = bytes(value)
    if len(raw) != NATIVE_ID_BYTE_LENGTH:
        raise SubstrateIdentifierError(
            f"native ID must contain {NATIVE_ID_BYTE_LENGTH} bytes, got {len(raw)}"
        )
    return _require_uuid4(uuid.UUID(bytes=raw))


def native_id_to_text(value: uuid.UUID) -> str:
    """Return canonical lowercase UUID text for diagnostics and APIs."""
    return str(_require_uuid4(value))


def native_id_from_text(value: str) -> uuid.UUID:
    """Parse only canonical lowercase hyphenated UUID text."""
    if not isinstance(value, str):
        raise SubstrateIdentifierError("native ID text must be a string")
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, ValueError) as exc:
        raise SubstrateIdentifierError("native ID text is not a valid UUID") from exc
    if value != str(parsed):
        raise SubstrateIdentifierError("native ID text must use canonical UUID form")
    return _require_uuid4(parsed)


def native_id_bytes_from_text(value: str) -> bytes:
    """Parse canonical UUID text and return its 16-byte storage representation."""
    return native_id_to_bytes(native_id_from_text(value))


def native_id_text_from_bytes(value: bytes | bytearray | memoryview) -> str:
    """Decode native-ID bytes and return canonical UUID text."""
    return native_id_to_text(native_id_from_bytes(value))


def _require_uuid4(value: uuid.UUID) -> uuid.UUID:
    if not isinstance(value, uuid.UUID):
        raise SubstrateIdentifierError("native ID must be a UUID instance")
    if value.version != 4:
        raise SubstrateIdentifierError("native IDs must be UUIDv4")
    return value
