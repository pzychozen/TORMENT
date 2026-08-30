"""Frozen canonical text selection shared by runtime embedding bootstraps."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from ..canonical_intent import canonical_intent_text


class CanonicalEmbeddingInputUnavailable(ValueError):
    """The qualified payload does not expose one exact embedding input string."""


@dataclass(frozen=True)
class CanonicalEmbeddingInput:
    """The exact field, text, and administrative digest supplied to an embedder."""

    field: str
    text: str
    digest: str


def select_canonical_embedding_input(payload: dict[str, Any]) -> CanonicalEmbeddingInput:
    """Select ``summary`` first and otherwise ``text`` without coercion or trimming."""
    if not isinstance(payload, dict):
        raise CanonicalEmbeddingInputUnavailable("payload must be a mapping")
    for field in ("summary", "text"):
        if field in payload:
            value = payload[field]
            if not isinstance(value, str):
                raise CanonicalEmbeddingInputUnavailable(f"{field} must be an exact string")
            return CanonicalEmbeddingInput(
                field=field,
                text=value,
                digest=hashlib.sha256(
                    canonical_intent_text({"field": field, "value": value}).encode("utf-8")
                ).hexdigest(),
            )
    raise CanonicalEmbeddingInputUnavailable("payload has neither summary nor text")


def require_embedding_input_continuity(
    r1_payload: dict[str, Any], r2_payload: dict[str, Any]
) -> CanonicalEmbeddingInput:
    """Require the B3A legacy-selected input to survive unchanged into B2 R2."""
    source = select_canonical_embedding_input(r1_payload)
    if r2_payload.get(source.field) != source.text:
        raise CanonicalEmbeddingInputUnavailable("B2 changed the selected legacy embedding input")
    return source


__all__ = [
    "CanonicalEmbeddingInput",
    "CanonicalEmbeddingInputUnavailable",
    "require_embedding_input_continuity",
    "select_canonical_embedding_input",
]
