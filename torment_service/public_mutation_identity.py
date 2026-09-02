"""Public mutation identity, deliberately distinct from request tracing.

This module owns the one opaque caller-key contract shared by REST, Spine,
and MCP.  It has no backend-selection authority and does not persist state.
Native routing receives only the derived digest key, never the caller token.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


_MAX_PUBLIC_MUTATION_KEY_LENGTH = 256
_DERIVATION_CONTRACT = "public-mutation/v1"


class PublicMutationKeyError(ValueError):
    """A caller supplied an unsafe or malformed idempotency token."""


@dataclass(frozen=True)
class PublicMutationKey:
    """An opaque, exact caller identity for one public mutation retry set."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise PublicMutationKeyError("idempotency key must be non-empty when supplied")
        if len(self.value) > _MAX_PUBLIC_MUTATION_KEY_LENGTH:
            raise PublicMutationKeyError(
                f"idempotency key exceeds {_MAX_PUBLIC_MUTATION_KEY_LENGTH} characters"
            )
        if any(ord(char) < 32 or ord(char) == 127 for char in self.value):
            raise PublicMutationKeyError("idempotency key must not contain control characters")


def normalize_public_mutation_key(value: str | None) -> PublicMutationKey | None:
    """Validate an optional transport value without trimming or rewriting it."""

    if value is None:
        return None
    return PublicMutationKey(value)


def canonical_public_request_fingerprint(
    *, operation: str, workspace_id: str, agent_id: str, semantic_payload: Mapping[str, Any]
) -> str:
    """Fingerprint semantic public inputs, excluding trace/timestamp carriers."""

    value = {
        "contract": _DERIVATION_CONTRACT,
        "operation": str(operation),
        "workspace_id": str(workspace_id),
        "agent_id": str(agent_id),
        "semantic_payload": dict(semantic_payload),
    }
    try:
        encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise PublicMutationKeyError("public mutation request is not canonically representable") from exc
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def derive_native_operation_key(
    *, operation: str, workspace_id: str, agent_id: str, key: PublicMutationKey
) -> str:
    """Derive the private native namespace key without exposing caller input."""

    encoded = json.dumps(
        {
            "contract": _DERIVATION_CONTRACT,
            "operation": str(operation),
            "workspace_id": str(workspace_id),
            "agent_id": str(agent_id),
            "caller_key": key.value,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )
    return f"{_DERIVATION_CONTRACT}/{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


__all__ = [
    "PublicMutationKey",
    "PublicMutationKeyError",
    "canonical_public_request_fingerprint",
    "derive_native_operation_key",
    "normalize_public_mutation_key",
]
