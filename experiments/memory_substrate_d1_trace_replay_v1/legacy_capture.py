"""Freeze storage-facing legacy facts while keeping legacy answers separate."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Callable, Mapping

import numpy as np

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.runtime_binding import NativeRepresentationLane

from .protocol import D1ProtocolError, sha256_value


@dataclass(frozen=True)
class LegacyStorageFacingFacts:
    """Only facts legitimately accepted by the current native route contract."""

    fixture_id: str
    workspace_id: str
    agent_id: str
    scope: str
    domain_id: str
    native_operation_key: str
    text: str
    summary: str
    embedding: Any = field(repr=False, compare=False)
    embedder_lane: NativeRepresentationLane
    memory_type: str
    memory_class: str
    strength: float
    confidence: float
    half_life_days: float
    logical_step: int
    created_ts: int
    last_active_ts: int
    last_reinforced_ts: int
    provenance: ProvenanceV1
    governance: MemoryGovernanceFlags
    flexible_payload: Mapping[str, Any] = field(default_factory=dict)
    attach_threshold: float = 0.76
    stability_delta: float = 0.0
    prior_symbol: str = ""
    prior_symbol_trace: tuple[str, ...] = ()
    prior_motif_id: str = ""
    prior_tension: float = 0.0
    last_tool_refresh_ts: int | None = None
    contradiction_guard: Callable[[str, str, float], bool] | None = field(default=None, repr=False, compare=False)
    tri_mod: Mapping[str, float] = field(default_factory=dict)
    debug: Mapping[str, Any] = field(default_factory=dict)
    srg_state: Mapping[str, Any] | None = None
    phase_durations: Mapping[str, Any] = field(default_factory=dict)
    affect_tag: str | None = None
    affect_conf: float | None = None
    skip_packet_emission: bool = False

    def __post_init__(self) -> None:
        if self.scope != "private" or self.domain_id != "research":
            raise D1ProtocolError("initial D1 replay is private research only")
        if not isinstance(self.fixture_id, str) or not self.fixture_id or not isinstance(self.native_operation_key, str) or not self.native_operation_key:
            raise D1ProtocolError("D1 facts require fixture and stable operation keys")
        vector = np.ascontiguousarray(np.asarray(self.embedding, dtype=np.float32).reshape(-1))
        if vector.size != self.embedder_lane.dimension or not np.isfinite(vector).all():
            raise D1ProtocolError("D1 replay requires finite exact-lane float32 embedding evidence")
        vector.setflags(write=False)
        object.__setattr__(self, "embedding", vector)
        object.__setattr__(self, "flexible_payload", dict(self.flexible_payload))
        object.__setattr__(self, "tri_mod", dict(self.tri_mod))
        object.__setattr__(self, "debug", dict(self.debug))
        object.__setattr__(self, "phase_durations", dict(self.phase_durations))
        object.__setattr__(self, "prior_symbol_trace", tuple(self.prior_symbol_trace))
        if self.flexible_payload.get("links") not in (None, (), []):
            raise D1ProtocolError("D1 does not admit deferred raw-link behavior")

    @property
    def embedding_bytes(self) -> bytes:
        return self.embedding.tobytes(order="C")

    @property
    def embedding_sha256(self) -> str:
        return hashlib.sha256(self.embedding_bytes).hexdigest()

    @property
    def request_digest(self) -> str:
        return sha256_value({
            "fixture_id": self.fixture_id, "workspace_id": self.workspace_id,
            "agent_id": self.agent_id, "scope": self.scope, "domain_id": self.domain_id,
            "operation_key": self.native_operation_key, "text": self.text, "summary": self.summary,
            "embedding_sha256": self.embedding_sha256, "lane": self.embedder_lane.__dict__,
            "memory_type": self.memory_type, "memory_class": self.memory_class,
            "strength": self.strength, "confidence": self.confidence, "half_life_days": self.half_life_days,
            "logical_step": self.logical_step, "created_ts": self.created_ts,
            "last_active_ts": self.last_active_ts, "last_reinforced_ts": self.last_reinforced_ts,
            "provenance": self.provenance.to_dict(), "governance": self.governance.__dict__,
            "payload": dict(self.flexible_payload), "attach_threshold": self.attach_threshold,
            "stability_delta": self.stability_delta, "prior_symbol": self.prior_symbol,
            "prior_symbol_trace": self.prior_symbol_trace, "prior_motif_id": self.prior_motif_id,
            "prior_tension": self.prior_tension, "last_tool_refresh_ts": self.last_tool_refresh_ts,
        })


@dataclass(frozen=True)
class LegacyObservedOutcome:
    """Comparison evidence only; this must never become a native route input."""

    stored: bool
    reinforced: bool
    eid: int | None
    motif_ids: tuple[str, ...] = ()
    created_motif: str | None = None
    conflict_target_eid: int | None = None
    retained_side_store_observations: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LegacyCapturedEvent:
    storage_facts: LegacyStorageFacingFacts
    observed_outcome: LegacyObservedOutcome

    def native_input(self) -> LegacyStorageFacingFacts:
        """Return facts only; legacy CREATE/REINFORCE answers are inaccessible here."""
        return self.storage_facts


def require_no_forced_reinforcement_target(value: Mapping[str, Any]) -> None:
    forbidden = {"reinforcement_target_eid", "legacy_reinforcement_target_eid", "selected_reinforcement_eid"}
    found = sorted(forbidden.intersection(value))
    if found:
        raise D1ProtocolError(f"D1 may not supply a legacy reinforcement answer: {found}")
