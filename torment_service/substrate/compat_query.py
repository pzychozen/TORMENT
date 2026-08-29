"""Injected-embedder text-query compatibility adapter.

This module owns only ephemeral query derivation.  Native eligibility,
ranking, revision alignment, integrity withholding, and result projection are
all delegated to :meth:`NativeMemoryCompatibilityFacade.search_by_embedding`.
No embedder is selected or constructed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

import numpy as np

from .compat import CompatibilityEmbeddingSearchResult, NativeMemoryCompatibilityFacade


_QUALIFIED_REPRESENTATION_CLASS = "COMPAT_EMBEDDING"
_QUALIFIED_GENERATION = 1
_QUALIFIED_DERIVATION_CONTRACT = "compat-embedding-v1"
_QUALIFIED_ENCODING = "RAW_VECTOR"
_QUALIFIED_DTYPE = "float32"


class QueryEmbedder(Protocol):
    """The minimal caller-owned capability required to derive a text query."""

    dim: int
    provider: str
    model: str

    def embed(self, text: str) -> Any:
        """Return one one-dimensional numeric vector for ``text``."""


@dataclass(frozen=True)
class CompatibilityQueryLane:
    """Explicit derivation identity and native representation lane for a query.

    Provider and model are supplied by the caller because the durable
    representation metadata is not an executable provider-selection policy.
    Every field is deliberately required so a caller cannot silently search an
    arbitrary READY representation or assume equal dimensions imply geometry
    compatibility.
    """

    provider: str
    model: str
    dimension: int
    representation_class: str
    generation: int
    derivation_contract_version: str
    encoding_id: str
    dtype: str


def search_text(
    *,
    facade: NativeMemoryCompatibilityFacade,
    legacy_source_namespace_id: UUID,
    query_text: str | None,
    embedder: QueryEmbedder | None,
    lane: CompatibilityQueryLane,
    top_k: int = 8,
    user_id: str | None = None,
    min_score: float | None = None,
    type_filter: tuple[str, ...] | list[str] | None = None,
) -> tuple[CompatibilityEmbeddingSearchResult, ...]:
    """Derive one ephemeral query vector and delegate native search unchanged.

    A blank query returns an empty result without inspecting the embedder or
    opening a candidate scan.  A nonblank query validates the caller-declared
    embedder identity and geometry before invoking ``embed`` exactly once.
    ``search_by_embedding`` remains the sole owner of all stored-vector search
    semantics and numerics validation.
    """

    normalized_query = _normalize_query_text(query_text)
    if not normalized_query:
        return ()
    _validate_lane(lane)
    declared_dimension = _validate_embedder(embedder, lane)

    # This is intentionally the only call to the injected derivation
    # dependency.  The resulting vector never enters the native semantic core.
    returned_vector = embedder.embed(normalized_query)
    query_vector = _validate_returned_dimension(returned_vector, declared_dimension)

    return facade.search_by_embedding(
        legacy_source_namespace_id=legacy_source_namespace_id,
        embedding=query_vector,
        dimension=lane.dimension,
        representation_class=lane.representation_class,
        generation=lane.generation,
        derivation_contract_version=lane.derivation_contract_version,
        encoding_id=lane.encoding_id,
        dtype=lane.dtype,
        top_k=top_k,
        user_id=user_id,
        min_score=min_score,
        type_filter=type_filter,
    )


def _normalize_query_text(query_text: str | None) -> str:
    if query_text is None:
        return ""
    if not isinstance(query_text, str):
        raise ValueError("query_text must be a string or None")
    return query_text.strip()


def _validate_lane(lane: CompatibilityQueryLane) -> None:
    if not isinstance(lane, CompatibilityQueryLane):
        raise ValueError("lane must be a CompatibilityQueryLane")
    if not isinstance(lane.provider, str) or not lane.provider:
        raise ValueError("lane provider must be a non-empty string")
    if not isinstance(lane.model, str) or not lane.model:
        raise ValueError("lane model must be a non-empty string")
    if not isinstance(lane.dimension, int) or isinstance(lane.dimension, bool) or lane.dimension < 1:
        raise ValueError("lane dimension must be a positive integer")
    if (
        lane.representation_class,
        lane.generation,
        lane.derivation_contract_version,
        lane.encoding_id,
        lane.dtype,
    ) != (
        _QUALIFIED_REPRESENTATION_CLASS,
        _QUALIFIED_GENERATION,
        _QUALIFIED_DERIVATION_CONTRACT,
        _QUALIFIED_ENCODING,
        _QUALIFIED_DTYPE,
    ):
        raise ValueError("only the qualified COMPAT_EMBEDDING/1 RAW_VECTOR float32 lane is supported")


def _validate_embedder(embedder: QueryEmbedder | None, lane: CompatibilityQueryLane) -> int:
    if embedder is None:
        raise ValueError("an injected embedder is required for a nonblank query")
    if getattr(embedder, "provider", None) != lane.provider:
        raise ValueError("injected embedder provider does not match the requested query lane")
    if getattr(embedder, "model", None) != lane.model:
        raise ValueError("injected embedder model does not match the requested query lane")
    declared_dimension = getattr(embedder, "dim", None)
    if (
        not isinstance(declared_dimension, int)
        or isinstance(declared_dimension, bool)
        or declared_dimension < 1
    ):
        raise ValueError("injected embedder dim must be a positive integer")
    if declared_dimension != lane.dimension:
        raise ValueError("injected embedder dimension does not match the requested query lane")
    embed = getattr(embedder, "embed", None)
    if not callable(embed):
        raise ValueError("injected embedder must provide a callable embed method")
    return declared_dimension


def _validate_returned_dimension(vector: Any, declared_dimension: int) -> np.ndarray:
    try:
        query_vector = np.asarray(vector)
    except (TypeError, ValueError) as exc:
        raise ValueError("injected embedder returned an invalid query vector") from exc
    if query_vector.ndim != 1 or query_vector.size != declared_dimension:
        raise ValueError("injected embedder returned a vector with the wrong dimension")
    return query_vector
