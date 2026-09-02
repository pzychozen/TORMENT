"""Backend-neutral carriers at the Fabric ingest storage boundary.

R1 uses these immutable carriers with the retained legacy storage algorithm.
They intentionally contain no native owner, selector, or public backend choice.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol


class FabricIngestStorageDisposition(str, Enum):
    NO_WRITE = "NO_WRITE"
    REINFORCED_EXISTING = "REINFORCED_EXISTING"
    CREATED_NEW = "CREATED_NEW"


@dataclass(frozen=True)
class PreparedFabricIngest:
    """Facts computed by TORMENT before memory authority is selected."""

    workspace_id: str
    agent_id: str
    scope: str
    domain_id: str
    logical_step: int
    summary: str
    embedding: Any
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    embedding_checksum: str
    memory_type: str
    memory_class: str
    strength: float
    confidence: float
    half_life_days: float | None
    links: tuple[str, ...]
    provenance: Mapping[str, Any]
    flexible_payload: Mapping[str, Any]
    tri_mod: Mapping[str, Any]
    debug: Mapping[str, Any]
    srg_state: Mapping[str, Any] | None
    phase_durations: Mapping[str, Any]
    affect_tag: str | None
    affect_conf: float | None
    allow_write: bool
    attach_threshold: float
    skip_packet_emission: bool
    public_request_fingerprint: str | None = None
    native_operation_key: str | None = None

    def __post_init__(self) -> None:
        # Empty summary is a legacy-valid tool-result case.  The carrier must
        # characterize the existing public contract, not strengthen it.
        for name in ("workspace_id", "agent_id", "scope", "domain_id", "memory_type", "memory_class"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty text")
        for name in ("provenance", "flexible_payload", "tri_mod", "debug", "phase_durations"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise ValueError(f"{name} must be a mapping")
            object.__setattr__(self, name, MappingProxyType(dict(value)))
        if self.srg_state is not None:
            if not isinstance(self.srg_state, Mapping):
                raise ValueError("srg_state must be a mapping or None")
            object.__setattr__(self, "srg_state", MappingProxyType(dict(self.srg_state)))
        object.__setattr__(self, "links", tuple(str(item) for item in self.links))
        # Numpy embeddings are the normal carrier.  Defensively detach and
        # make those arrays read-only so a storage adapter cannot alter facts
        # observed by post-write.  Non-array implementations retain their
        # existing value because this carrier does not impose a numeric stack.
        try:
            embedding_copy = self.embedding.copy()
            embedding_copy.setflags(write=False)
        except (AttributeError, TypeError, ValueError):
            pass
        else:
            object.__setattr__(self, "embedding", embedding_copy)


@dataclass(frozen=True)
class FabricIngestStorageOutcome:
    """Normalized result available to post-write orchestration and response assembly."""

    workspace_id: str
    agent_id: str
    scope: str
    domain_id: str
    disposition: FabricIngestStorageDisposition
    stored: bool
    eid: int | None
    motif_ids: tuple[str, ...]
    created_motif: str | None
    state_symbol: str | None
    storage_witness: Any = None

    @property
    def reinforced(self) -> bool:
        return self.disposition is FabricIngestStorageDisposition.REINFORCED_EXISTING


class FabricIngestStoragePort(Protocol):
    """The narrow storage authority seam; preparation owns no durable memory."""

    def store(self, prepared: PreparedFabricIngest) -> FabricIngestStorageOutcome: ...


class LegacyFabricIngestStorageAdapter:
    """Normalize the exact retained legacy graph/motif storage result.

    The current legacy storage algorithm remains in :mod:`fabric` so its
    duplicate, flush, motif, and conflict ordering cannot drift during this
    first extraction.  The adapter is its sole outcome handoff to post-write.
    A native adapter is intentionally not introduced in R1.
    """

    def store(
        self,
        prepared: PreparedFabricIngest,
        *,
        stored: bool,
        reinforced: bool,
        eid: int | None,
        motif_ids: tuple[str, ...] | list[str],
        created_motif: str | None,
        state_symbol: str | None,
        storage_witness: Any,
    ) -> FabricIngestStorageOutcome:
        if reinforced and not stored:
            raise ValueError("legacy reinforcement outcome must be stored")
        if not stored:
            disposition = FabricIngestStorageDisposition.NO_WRITE
        elif reinforced:
            disposition = FabricIngestStorageDisposition.REINFORCED_EXISTING
        else:
            disposition = FabricIngestStorageDisposition.CREATED_NEW
        return FabricIngestStorageOutcome(
            workspace_id=prepared.workspace_id,
            agent_id=prepared.agent_id,
            scope=prepared.scope,
            domain_id=prepared.domain_id,
            disposition=disposition,
            stored=bool(stored),
            eid=None if eid is None else int(eid),
            motif_ids=tuple(str(item) for item in motif_ids),
            created_motif=created_motif,
            state_symbol=state_symbol,
            storage_witness=storage_witness,
        )


__all__ = [
    "FabricIngestStorageDisposition",
    "FabricIngestStorageOutcome",
    "FabricIngestStoragePort",
    "LegacyFabricIngestStorageAdapter",
    "PreparedFabricIngest",
]
