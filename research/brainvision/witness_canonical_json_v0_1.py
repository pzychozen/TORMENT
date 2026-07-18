"""Canonical JSON serialization, SHA-256, and payload/envelope helpers (offline; serialization ONLY).

This module contains ZERO witness mathematics. It provides deterministic canonical JSON, SHA-256 hashing, and
the nonrecursive payload/envelope pattern used by the independent higher-order witness verifier and freezer.
Canonical outputs exclude all nondeterministic metadata (no timestamps, durations, absolute/temporary paths,
host data, process IDs, or unordered environment state). stdlib only; no torment_service import; no descriptor
or generator import.

Governing specification:
  docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

SERIALIZER_NAME = "witness_canonical_json_v0_1"
SERIALIZER_VERSION = "0.1"


def canonical_json_text(value: Any) -> str:
    """Canonical JSON text: UTF-8 source, ensure_ascii, sorted keys, compact separators, no NaN/Infinity."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def canonical_json_bytes(value: Any) -> bytes:
    """Canonical JSON bytes with NO trailing newline (bytes end at the final closing token)."""
    return canonical_json_text(value).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_sha256(payload: Any) -> str:
    """SHA-256 over the canonical payload bytes (no trailing newline)."""
    return sha256_hex(canonical_json_bytes(payload))


def envelope(name: str, payload: Any) -> Dict[str, Any]:
    """Nonrecursive payload/envelope: the hash covers ONLY the payload bytes, never the envelope itself.

    Returns {name: payload, name + "_sha256": SHA256(canonical_json_bytes(payload))}. The payload must not
    contain a field named name + "_sha256"; recursive self-hashing is not permitted.
    """
    hash_field = name + "_sha256"
    if isinstance(payload, dict) and hash_field in payload:
        raise ValueError("recursive self-hash field present in payload: " + hash_field)
    return {name: payload, hash_field: payload_sha256(payload)}


def source_file_sha256(path: str) -> str:
    """SHA-256 over the raw file bytes exactly as present (no newline normalization; no path bytes hashed)."""
    with open(path, "rb") as handle:
        return sha256_hex(handle.read())


def is_lower_hex_64(value: Any) -> bool:
    """True iff value is a string of exactly 64 lowercase hexadecimal characters."""
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)
