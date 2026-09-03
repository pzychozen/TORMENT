"""Backend-neutral carriers at the Fabric ingest storage boundary.

R1 uses these immutable carriers with the retained legacy storage algorithm.
They intentionally contain no native owner, selector, or public backend choice.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping, Protocol

import numpy as np


_PREPARED_INGEST_RECEIPT_SCHEMA = "TORMENT_PREPARED_FABRIC_INGEST_V1"


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
    promotion_score: float = 0.0
    stability_delta: float = 0.0
    suppress_canon: bool = False
    affect_classification_completed: bool = False
    frozen_created_ts: int = 0
    frozen_last_active_ts: int = 0
    frozen_last_reinforced_ts: int = 0
    prior_symbol: str = ""
    prior_symbol_trace: tuple[str, ...] = ()
    prior_motif_id: str = ""
    prior_tension: float = 0.0
    domain_ranked: tuple[Mapping[str, Any], ...] = ()
    write_intent: bool = False
    signal_half_life_days: float = 0.0
    in_corridor: bool = False
    survival_steps: float = 0.0
    tearing_risk: float = 0.0
    half_life_multiplier: float = 1.0

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
        object.__setattr__(self, "prior_symbol_trace", tuple(str(item) for item in self.prior_symbol_trace))
        if not isinstance(self.domain_ranked, (tuple, list)) or any(
            not isinstance(item, Mapping) for item in self.domain_ranked
        ):
            raise ValueError("domain_ranked must be a sequence of mappings")
        object.__setattr__(
            self, "domain_ranked", tuple(MappingProxyType(dict(item)) for item in self.domain_ranked),
        )
        if type(self.write_intent) is not bool:
            raise ValueError("write_intent must be a boolean")
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


class PreparedFabricIngestReceiptError(ValueError):
    """A prepared-ingest receipt is malformed, non-canonical, or unsafe."""


def serialize_prepared_fabric_ingest(prepared: PreparedFabricIngest) -> dict[str, Any]:
    """Return the versioned canonical-receipt payload for prepared ingest facts.

    The vector is always converted to finite little-endian float32 bytes.  No
    text rendering is used, so recovery cannot accidentally alter the vector
    that was already used for routing and the write gate.
    """

    if not isinstance(prepared, PreparedFabricIngest):
        raise PreparedFabricIngestReceiptError("prepared receipt requires PreparedFabricIngest")
    try:
        embedding = np.asarray(prepared.embedding, dtype="<f4").reshape(-1)
    except (TypeError, ValueError) as exc:
        raise PreparedFabricIngestReceiptError("prepared embedding is not float32-compatible") from exc
    if embedding.size != prepared.embedding_dimension or not np.all(np.isfinite(embedding)):
        raise PreparedFabricIngestReceiptError("prepared embedding violates dimension or finite-vector law")
    raw_embedding = embedding.tobytes(order="C")
    payload = {
        "schema": _PREPARED_INGEST_RECEIPT_SCHEMA,
        "embedding": {
            "dtype": "float32-le",
            "dimension": int(embedding.size),
            "payload_b64": base64.b64encode(raw_embedding).decode("ascii"),
            "sha256": hashlib.sha256(raw_embedding).hexdigest(),
        },
        "facts": {
            "workspace_id": prepared.workspace_id,
            "agent_id": prepared.agent_id,
            "scope": prepared.scope,
            "domain_id": prepared.domain_id,
            "logical_step": int(prepared.logical_step),
            "summary": prepared.summary,
            "embedding_provider": prepared.embedding_provider,
            "embedding_model": prepared.embedding_model,
            "embedding_dimension": int(prepared.embedding_dimension),
            "embedding_checksum": prepared.embedding_checksum,
            "memory_type": prepared.memory_type,
            "memory_class": prepared.memory_class,
            "strength": float(prepared.strength),
            "confidence": float(prepared.confidence),
            "half_life_days": prepared.half_life_days,
            "links": list(prepared.links),
            "provenance": dict(prepared.provenance),
            "flexible_payload": dict(prepared.flexible_payload),
            "tri_mod": dict(prepared.tri_mod),
            "debug": dict(prepared.debug),
            "srg_state": None if prepared.srg_state is None else dict(prepared.srg_state),
            "phase_durations": dict(prepared.phase_durations),
            "affect_tag": prepared.affect_tag,
            "affect_conf": prepared.affect_conf,
            "allow_write": bool(prepared.allow_write),
            "attach_threshold": float(prepared.attach_threshold),
            "skip_packet_emission": bool(prepared.skip_packet_emission),
            "public_request_fingerprint": prepared.public_request_fingerprint,
            "native_operation_key": prepared.native_operation_key,
            "promotion_score": float(prepared.promotion_score),
            "stability_delta": float(prepared.stability_delta),
            "suppress_canon": bool(prepared.suppress_canon),
            "affect_classification_completed": bool(prepared.affect_classification_completed),
            "frozen_created_ts": int(prepared.frozen_created_ts),
            "frozen_last_active_ts": int(prepared.frozen_last_active_ts),
            "frozen_last_reinforced_ts": int(prepared.frozen_last_reinforced_ts),
            "prior_symbol": prepared.prior_symbol,
            "prior_symbol_trace": list(prepared.prior_symbol_trace),
            "prior_motif_id": prepared.prior_motif_id,
            "prior_tension": float(prepared.prior_tension),
            "domain_ranked": [dict(item) for item in prepared.domain_ranked],
            "write_intent": prepared.write_intent,
            "signal_half_life_days": float(prepared.signal_half_life_days),
            "in_corridor": prepared.in_corridor,
            "survival_steps": float(prepared.survival_steps),
            "tearing_risk": float(prepared.tearing_risk),
            "half_life_multiplier": float(prepared.half_life_multiplier),
        },
    }
    try:
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise PreparedFabricIngestReceiptError("prepared facts are not canonically serializable") from exc
    return payload


def deserialize_prepared_fabric_ingest(payload: Mapping[str, Any]) -> PreparedFabricIngest:
    """Validate and rehydrate exactly one receipt-produced prepared carrier."""

    if not isinstance(payload, Mapping) or payload.get("schema") != _PREPARED_INGEST_RECEIPT_SCHEMA:
        raise PreparedFabricIngestReceiptError("prepared receipt schema differs")
    try:
        encoded, facts = payload["embedding"], payload["facts"]
        if not isinstance(encoded, Mapping) or not isinstance(facts, Mapping):
            raise TypeError
        if encoded.get("dtype") != "float32-le":
            raise ValueError
        dimension = int(encoded["dimension"])
        raw = base64.b64decode(str(encoded["payload_b64"]), validate=True)
        if dimension < 1 or len(raw) != dimension * 4:
            raise ValueError
        if hashlib.sha256(raw).hexdigest() != encoded["sha256"]:
            raise ValueError
        embedding = np.frombuffer(raw, dtype="<f4").copy()
        if embedding.size != dimension or not np.all(np.isfinite(embedding)):
            raise ValueError
        prepared = PreparedFabricIngest(
            workspace_id=str(facts["workspace_id"]), agent_id=str(facts["agent_id"]),
            scope=str(facts["scope"]), domain_id=str(facts["domain_id"]),
            logical_step=int(facts["logical_step"]), summary=str(facts["summary"]),
            embedding=embedding, embedding_provider=str(facts["embedding_provider"]),
            embedding_model=str(facts["embedding_model"]), embedding_dimension=int(facts["embedding_dimension"]),
            embedding_checksum=str(facts["embedding_checksum"]), memory_type=str(facts["memory_type"]),
            memory_class=str(facts["memory_class"]), strength=float(facts["strength"]),
            confidence=float(facts["confidence"]),
            half_life_days=(None if facts["half_life_days"] is None else float(facts["half_life_days"])),
            links=tuple(facts["links"]), provenance=dict(facts["provenance"]),
            flexible_payload=dict(facts["flexible_payload"]), tri_mod=dict(facts["tri_mod"]),
            debug=dict(facts["debug"]),
            srg_state=(None if facts["srg_state"] is None else dict(facts["srg_state"])),
            phase_durations=dict(facts["phase_durations"]), affect_tag=facts["affect_tag"],
            affect_conf=(None if facts["affect_conf"] is None else float(facts["affect_conf"])),
            allow_write=bool(facts["allow_write"]), attach_threshold=float(facts["attach_threshold"]),
            skip_packet_emission=bool(facts["skip_packet_emission"]),
            public_request_fingerprint=facts["public_request_fingerprint"],
            native_operation_key=facts["native_operation_key"], promotion_score=float(facts["promotion_score"]),
            stability_delta=float(facts["stability_delta"]), suppress_canon=bool(facts["suppress_canon"]),
            affect_classification_completed=bool(facts["affect_classification_completed"]),
            frozen_created_ts=int(facts["frozen_created_ts"]),
            frozen_last_active_ts=int(facts["frozen_last_active_ts"]),
            frozen_last_reinforced_ts=int(facts["frozen_last_reinforced_ts"]),
            prior_symbol=str(facts["prior_symbol"]), prior_symbol_trace=tuple(facts["prior_symbol_trace"]),
            prior_motif_id=str(facts["prior_motif_id"]), prior_tension=float(facts["prior_tension"]),
            domain_ranked=tuple(dict(item) for item in facts["domain_ranked"]),
            write_intent=facts["write_intent"], signal_half_life_days=float(facts["signal_half_life_days"]),
            in_corridor=facts["in_corridor"], survival_steps=float(facts["survival_steps"]),
            tearing_risk=float(facts["tearing_risk"]),
            half_life_multiplier=float(facts["half_life_multiplier"]),
        )
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise PreparedFabricIngestReceiptError("prepared receipt is malformed") from exc
    if prepared.embedding_dimension != dimension:
        raise PreparedFabricIngestReceiptError("prepared receipt dimension differs")
    return prepared


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
    # Primary outcome evidence is observational.  It deliberately does not
    # select the post-write path: legacy branches distinguish ordinary
    # NO_WRITE from a failed canonical flush.
    primary_outcome_witness: Any = None
    post_write_eligible: bool = True
    failure_code: str | None = None

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
    "PreparedFabricIngestReceiptError",
    "PreparedFabricIngest",
    "deserialize_prepared_fabric_ingest",
    "serialize_prepared_fabric_ingest",
]
