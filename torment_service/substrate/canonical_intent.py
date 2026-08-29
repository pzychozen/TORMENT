"""TMS-INTENT-1 canonical JSON encoding.

This is a reusable comparison primitive only.  It creates no operations,
timestamps, IDs, hashes, or other execution-derived metadata.
"""

from __future__ import annotations

import json
import math
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any, Final

from .errors import CanonicalIntentError


CANONICAL_INTENT_CONTRACT: Final[str] = "TMS-INTENT-1"


def canonical_intent_text(value: Any) -> str:
    """Encode a TMS-INTENT-1 value as canonical UTF-8-safe JSON text."""
    normalized = _normalize(value, path="$", active_containers=set())
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_intent_bytes(value: Any) -> bytes:
    """Encode a value as authoritative UTF-8 retry-comparison bytes."""
    return canonical_intent_text(value).encode("utf-8")


def _normalize(value: Any, *, path: str, active_containers: set[int]) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalIntentError("canonical intent cannot contain NaN or Infinity")
        return value

    if isinstance(value, Mapping):
        return _normalize_mapping(value, path=path, active_containers=active_containers)

    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, memoryview)):
        container_id = id(value)
        if container_id in active_containers:
            raise CanonicalIntentError("canonical intent cannot contain cyclic collections")
        active_containers.add(container_id)
        try:
            # List order is semantic by default.  Set-like ordering is an
            # operation-builder responsibility and is never inferred here.
            return [
                _normalize(item, path=f"{path}[{index}]", active_containers=active_containers)
                for index, item in enumerate(value)
            ]
        finally:
            active_containers.remove(container_id)

    raise CanonicalIntentError("canonical intent contains an unsupported value type")


def _normalize_mapping(
    value: Mapping[Any, Any], *, path: str, active_containers: set[int]
) -> dict[str, Any]:
    container_id = id(value)
    if container_id in active_containers:
        raise CanonicalIntentError("canonical intent cannot contain cyclic collections")
    active_containers.add(container_id)
    try:
        normalized: dict[str, Any] = {}
        for raw_key, raw_item in value.items():
            if not isinstance(raw_key, str):
                raise CanonicalIntentError("canonical intent object keys must be strings")
            key = unicodedata.normalize("NFC", raw_key)
            if key in normalized:
                raise CanonicalIntentError(
                    "canonical intent has duplicate object keys after Unicode normalization"
                )
            normalized[key] = _normalize(
                raw_item,
                path=f"{path}.{key}",
                active_containers=active_containers,
            )
        return normalized
    finally:
        active_containers.remove(container_id)
