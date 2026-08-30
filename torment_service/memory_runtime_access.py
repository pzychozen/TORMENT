"""Backend-neutral, read-only memory facts for post-write consumers.

This module deliberately knows nothing about the substrate.  It exposes the
small current/read/search surface that post-write consumers need and adapts an
already-selected legacy :class:`MemoryGraph` without reloading it.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Literal, Mapping, Protocol, runtime_checkable

import numpy as np

from torment_service.embedding_store import load_embedding
from torment_service.governance import resolve_governance


_STRUCTURAL_PAYLOAD_KEYS = frozenset({
    "semantic_scope_id", "scope", "lifecycle", "lifecycle_state", "lifecycle_status",
    "lifecycle_authoritative", "governance", "governance_state", "authority_category",
    "authorization", "provenance", "provenance_id", "identity_namespace_id", "object_id",
    "object_kind", "eid", "revision", "revision_id", "object_revision_id",
    "object_revision_ordinal", "predecessor", "predecessor_revision_id",
    "predecessor_revision_ordinal", "representation", "representation_id", "readiness",
    "representation_readiness", "integrity", "integrity_expectation", "integrity_measurement",
    "reconciliation", "operation_id", "transition_id", "embedding_ref",
})


@dataclass(frozen=True)
class RuntimeMemoryGovernanceView:
    """Effective governance facts plus whether their carrier was explicit."""

    protected: bool
    non_shareable: bool
    collective_export_blocked: bool
    collective_reingest_blocked: bool
    decay_accelerated: bool
    structurally_explicit: bool


@dataclass(frozen=True)
class RuntimeMemoryProvenanceView:
    """The small, already-frozen provenance projection needed post-write."""

    source_type: str | None
    source_channel: str | None
    write_path: str | None
    collective_echo: bool
    structurally_explicit: bool


@dataclass(frozen=True)
class RuntimeMemoryView:
    """An immutable current-memory projection with no backend identities."""

    eid: int
    summary: str
    memory_type: str
    memory_class: str
    strength: float
    confidence: float
    payload: Mapping[str, Any]
    governance: RuntimeMemoryGovernanceView
    provenance: RuntimeMemoryProvenanceView


@dataclass(frozen=True)
class RuntimeMemorySearchHit:
    """One existing backend search result and its current-memory projection."""

    view: RuntimeMemoryView
    raw_score: float
    score: float
    decay_factor: float

    @property
    def eid(self) -> int:
        return self.view.eid


RuntimeMemorySearchStatus = Literal["SEARCHABLE", "ZERO_NORM"]


@dataclass(frozen=True)
class RuntimeMemorySearchOutcome:
    """A classified post-write query result, independent of backend quirks."""

    status: RuntimeMemorySearchStatus
    hits: tuple[RuntimeMemorySearchHit, ...]

    def __post_init__(self) -> None:
        if self.status not in {"SEARCHABLE", "ZERO_NORM"}:
            raise ValueError("runtime memory search status is invalid")
        if not isinstance(self.hits, tuple) or any(not isinstance(hit, RuntimeMemorySearchHit) for hit in self.hits):
            raise ValueError("runtime memory search hits must be an immutable hit tuple")
        if self.status == "ZERO_NORM" and self.hits:
            raise ValueError("a zero-norm query cannot have search hits")


@dataclass(frozen=True)
class RuntimeMemoryEmbedding:
    """Byte-exact qualified geometry, with an optional safe array projection."""

    dtype: str
    dimension: int
    payload_bytes: bytes
    byte_length: int
    payload_sha256: str

    def __post_init__(self) -> None:
        if self.dtype != "float32":
            raise ValueError("runtime memory embeddings must be float32")
        if not isinstance(self.dimension, int) or isinstance(self.dimension, bool) or self.dimension < 1:
            raise ValueError("runtime memory embedding dimension must be positive")
        if not isinstance(self.payload_bytes, bytes):
            raise ValueError("runtime memory embedding payload must be bytes")
        if self.byte_length != len(self.payload_bytes) or self.byte_length != self.dimension * 4:
            raise ValueError("runtime memory embedding byte length contradicts its dimension")
        if self.payload_sha256 != sha256(self.payload_bytes).hexdigest():
            raise ValueError("runtime memory embedding hash contradicts its bytes")

    @classmethod
    def from_float32_vector(cls, vector: Any, *, expected_dimension: int) -> "RuntimeMemoryEmbedding":
        if not isinstance(expected_dimension, int) or isinstance(expected_dimension, bool) or expected_dimension < 1:
            raise ValueError("expected_dimension must be a positive integer")
        try:
            value = np.asarray(vector, dtype=np.float32).reshape(-1)
        except (TypeError, ValueError) as exc:
            raise ValueError("embedding must be a one-dimensional numeric vector") from exc
        if value.size != expected_dimension:
            raise ValueError("embedding dimension does not match the requested dimension")
        if not np.all(np.isfinite(value)):
            raise ValueError("embedding contains non-finite values")
        payload = np.ascontiguousarray(value, dtype=np.float32).tobytes(order="C")
        return cls("float32", expected_dimension, payload, len(payload), sha256(payload).hexdigest())

    def as_float32(self) -> np.ndarray:
        """Return a fresh, immutable vector without exposing the byte witness."""
        vector = np.frombuffer(self.payload_bytes, dtype=np.float32).copy()
        vector.setflags(write=False)
        return vector


@runtime_checkable
class PostWriteMemoryReadPort(Protocol):
    def get_current(self, eid: int) -> RuntimeMemoryView | None: ...

    def search_by_embedding(
        self, embedding: Any, *, top_k: int, user_id: str | None = None,
    ) -> RuntimeMemorySearchOutcome: ...

    def read_current_embedding(
        self, eid: int, *, expected_dimension: int,
    ) -> RuntimeMemoryEmbedding | None: ...


@runtime_checkable
class PostWriteMemoryEnumerationPort(Protocol):
    """A separate, intentionally unqualified capability for SRG iteration."""

    def list_current(self) -> tuple[RuntimeMemoryView, ...]: ...


class LegacyPostWriteMemoryAccess:
    """Read-only adapter over one exact in-memory legacy ``MemoryGraph``."""

    def __init__(self, graph: Any, *, expected_dimension: int) -> None:
        if not isinstance(expected_dimension, int) or isinstance(expected_dimension, bool) or expected_dimension < 1:
            raise ValueError("expected_dimension must be a positive integer")
        if not hasattr(graph, "entities") or not hasattr(graph, "search_by_embedding"):
            raise ValueError("graph must be the selected MemoryGraph-like read source")
        self._graph = graph
        self._expected_dimension = expected_dimension

    def get_current(self, eid: int) -> RuntimeMemoryView | None:
        entity = self._graph.entities.get(int(eid))
        if entity is None:
            return None
        payload = getattr(entity, "payload", None)
        if not isinstance(payload, Mapping):
            raise ValueError("legacy memory payload must be a mapping")
        return runtime_memory_view_from_legacy_payload(int(eid), payload)

    def list_current(self) -> tuple[RuntimeMemoryView, ...]:
        """Return the selected graph's current entities in insertion order."""
        views: list[RuntimeMemoryView] = []
        seen: set[int] = set()
        for object_id in self._graph.entities:
            if not isinstance(object_id, int) or isinstance(object_id, bool) or object_id < 0:
                raise ValueError("legacy current-memory enumeration has an invalid EID")
            if object_id in seen:
                raise ValueError("legacy current-memory enumeration has a duplicate EID")
            view = self.get_current(object_id)
            if view is None:
                raise ValueError("legacy current-memory enumeration lost an entity")
            seen.add(object_id)
            views.append(view)
        return tuple(views)

    def search_by_embedding(
        self, embedding: Any, *, top_k: int, user_id: str | None = None,
    ) -> RuntimeMemorySearchOutcome:
        status = classify_post_write_query(embedding, expected_dimension=self._expected_dimension)
        if status == "ZERO_NORM":
            return RuntimeMemorySearchOutcome(status, ())
        # MemoryGraph remains the sole owner of its query normalization,
        # top-k-before-filter behavior, decay, and ranking.
        results = self._graph.search_by_embedding(embedding, top_k=top_k, user_id=user_id)
        hits: list[RuntimeMemorySearchHit] = []
        for result in results:
            eid = int(result["eid"])
            view = self.get_current(eid)
            if view is None:
                continue
            hits.append(RuntimeMemorySearchHit(
                view=view,
                raw_score=float(result.get("raw_score", result["score"])),
                score=float(result["score"]),
                decay_factor=float(result.get("decay_factor", 1.0)),
            ))
        return RuntimeMemorySearchOutcome(status, tuple(hits))

    def read_current_embedding(
        self, eid: int, *, expected_dimension: int,
    ) -> RuntimeMemoryEmbedding | None:
        _require_adapter_dimension(expected_dimension, self._expected_dimension)
        entity = self._graph.entities.get(int(eid))
        if entity is None:
            return None
        payload = getattr(entity, "payload", None)
        if not isinstance(payload, Mapping):
            raise ValueError("legacy memory payload must be a mapping")
        vector = load_embedding(
            int(eid), dict(payload), getattr(self._graph, "_shard_reader", None), self._graph.data_dir,
        )
        if vector is None:
            return None
        return RuntimeMemoryEmbedding.from_float32_vector(vector, expected_dimension=expected_dimension)


def runtime_memory_view_from_legacy_payload(eid: int, payload: Mapping[str, Any]) -> RuntimeMemoryView:
    """Project legacy payload facts without mutating or exposing that payload."""
    if not isinstance(eid, int) or isinstance(eid, bool) or eid < 0:
        raise ValueError("eid must be a non-negative integer")
    if not isinstance(payload, Mapping):
        raise ValueError("legacy memory payload must be a mapping")
    governance = resolve_governance(dict(payload))
    provenance = _legacy_provenance(payload)
    return RuntimeMemoryView(
        eid=eid,
        summary=_legacy_text(payload.get("summary", payload.get("text")), default=""),
        memory_type=_legacy_text(payload.get("type", payload.get("mtype")), default="memory"),
        memory_class=_legacy_text(payload.get("memory_class"), default="core"),
        strength=_legacy_number(payload.get("strength")),
        confidence=_legacy_number(payload.get("confidence")),
        payload=project_runtime_payload(payload),
        governance=RuntimeMemoryGovernanceView(
            protected=bool(governance.protected),
            non_shareable=bool(governance.non_shareable),
            collective_export_blocked=bool(governance.collective_export_blocked),
            collective_reingest_blocked=bool(governance.collective_reingest_blocked),
            decay_accelerated=bool(governance.decay_accelerated),
            structurally_explicit=isinstance(payload.get("governance"), Mapping),
        ),
        provenance=provenance,
    )


def freeze_runtime_payload(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a detached recursive immutable projection of JSON-shaped data."""
    if not isinstance(value, Mapping):
        raise ValueError("runtime payload must be a mapping")
    frozen = _freeze_value(value)
    assert isinstance(frozen, Mapping)
    return frozen


def project_runtime_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Detach ordinary payload facts from structural and embedding carriers."""
    if not isinstance(payload, Mapping):
        raise ValueError("runtime payload must be a mapping")
    return freeze_runtime_payload({
        key: value for key, value in payload.items() if key.casefold() not in _STRUCTURAL_PAYLOAD_KEYS
    })


def classify_post_write_query(
    embedding: Any, *, expected_dimension: int,
) -> RuntimeMemorySearchStatus:
    """Classify a valid post-write query before either backend search runs.

    A finite zero-norm query has no reinforcement or conflict decision path:
    legacy would yield only zero similarities, while the native search rejects
    it.  The contract therefore reports ``ZERO_NORM`` with no hits.  Every
    other malformed vector remains invalid rather than being reclassified.
    """
    if not isinstance(expected_dimension, int) or isinstance(expected_dimension, bool) or expected_dimension < 1:
        raise ValueError("expected_dimension must be a positive integer")
    try:
        raw = np.asarray(embedding)
    except (TypeError, ValueError) as exc:
        raise ValueError("embedding must be a numeric vector") from exc
    if not np.issubdtype(raw.dtype, np.number) or np.issubdtype(raw.dtype, np.bool_):
        raise ValueError("embedding must be a numeric vector")
    try:
        query = np.asarray(raw, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise ValueError("embedding must be a numeric vector") from exc
    if query.size == 0:
        raise ValueError("embedding must be non-empty")
    if query.size != expected_dimension:
        raise ValueError("query dimension does not match this access adapter")
    if not np.all(np.isfinite(query)):
        raise ValueError("embedding must contain only finite values")
    norm = float(np.linalg.norm(query))
    if not np.isfinite(norm):
        raise ValueError("embedding must have a finite norm")
    return "ZERO_NORM" if norm == 0.0 else "SEARCHABLE"


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})
    if isinstance(value, np.ndarray):
        return tuple(_freeze_value(item) for item in value.tolist())
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_value(item) for item in value)
    if isinstance(value, np.generic):
        return value.item()
    if value is None or isinstance(value, (str, bytes, bool, int, float)):
        return value
    raise ValueError("runtime payload contains an unsupported mutable value")


def _legacy_provenance(payload: Mapping[str, Any]) -> RuntimeMemoryProvenanceView:
    raw = payload.get("provenance")
    if isinstance(raw, Mapping):
        source_type = raw.get("source_type") if isinstance(raw.get("source_type"), str) else None
        write_path = raw.get("write_path") if isinstance(raw.get("write_path"), str) else None
        return RuntimeMemoryProvenanceView(
            source_type=source_type,
            source_channel=source_type,
            write_path=write_path,
            collective_echo=source_type == "collective_echo",
            structurally_explicit=True,
        )
    if isinstance(raw, str):
        source_type = "collective_echo" if raw == "collective" else raw
        return RuntimeMemoryProvenanceView(
            source_type=source_type,
            source_channel=source_type,
            write_path=None,
            collective_echo=raw == "collective" or raw == "collective_echo",
            structurally_explicit=True,
        )
    return RuntimeMemoryProvenanceView(None, None, None, False, False)


def _legacy_text(value: Any, *, default: str) -> str:
    return value if isinstance(value, str) else default


def _legacy_number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _require_adapter_dimension(expected_dimension: int, adapter_dimension: int) -> None:
    if expected_dimension != adapter_dimension:
        raise ValueError("requested embedding dimension does not match this access adapter")


__all__ = [
    "LegacyPostWriteMemoryAccess",
    "PostWriteMemoryEnumerationPort",
    "PostWriteMemoryReadPort",
    "RuntimeMemoryEmbedding",
    "RuntimeMemoryGovernanceView",
    "RuntimeMemoryProvenanceView",
    "RuntimeMemorySearchHit",
    "RuntimeMemorySearchOutcome",
    "RuntimeMemorySearchStatus",
    "RuntimeMemoryView",
    "classify_post_write_query",
    "freeze_runtime_payload",
    "project_runtime_payload",
    "runtime_memory_view_from_legacy_payload",
]
