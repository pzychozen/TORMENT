"""Native process-local SRG overlays and typed successor materialization.

The process owner deliberately contains no SQLite handle, database path, or
authority selector. A short-lived adapter binds an already-open qualified
connection to that owner, then may offer one exact-current overlay as input to
the next legitimate memory successor operation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
import threading
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from torment_service.memory_runtime_access import RuntimeMemoryView
from torment_service.srg_runtime_state import SRGTransientRuntimePort

from .canonical_intent import canonical_intent_text
from .compat import LegacyMemoryView, NativeMemoryCompatibilityFacade
from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from .schema import require_current_schema


@dataclass(frozen=True)
class _NativeSRGOverlay:
    revision_id: UUID
    srg_state: Mapping[str, Any]
    collision_report: Mapping[str, Any] | None


@dataclass(frozen=True)
class SRGSuccessorMaterialization:
    """A typed, exact-predecessor input to one ordinary memory successor.

    The snapshot has no publication behavior. It can contribute only the
    legacy live-payload fields ``srg`` and ``srg_collision`` to a caller's
    already-authorized successor state.
    """

    predecessor_revision_id: UUID
    predecessor_revision_ordinal: int
    effective_srg_state: Mapping[str, Any]
    effective_collision_report: Mapping[str, Any] | None
    canonical_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.predecessor_revision_id, UUID):
            raise ValueError("predecessor_revision_id must be a UUID")
        if (
            not isinstance(self.predecessor_revision_ordinal, int)
            or isinstance(self.predecessor_revision_ordinal, bool)
            or self.predecessor_revision_ordinal < 1
        ):
            raise ValueError("predecessor_revision_ordinal must be a positive integer")
        state = _freeze_mapping(self.effective_srg_state, field="effective SRG state")
        report = (
            None if self.effective_collision_report is None else _freeze_mapping(
                self.effective_collision_report, field="effective SRG collision report"
            )
        )
        object.__setattr__(self, "effective_srg_state", state)
        object.__setattr__(self, "effective_collision_report", report)
        if (
            not isinstance(self.canonical_digest, str)
            or len(self.canonical_digest) != 64
            or any(character not in "0123456789abcdef" for character in self.canonical_digest)
        ):
            raise ValueError("canonical_digest must be a lowercase SHA-256 hex digest")
        if self.canonical_digest != _materialization_digest(
            self.predecessor_revision_id,
            self.predecessor_revision_ordinal,
            state,
            report,
        ):
            raise ValueError("canonical_digest does not match the materialization contents")

    @classmethod
    def create(
        cls,
        *,
        predecessor_revision_id: UUID,
        predecessor_revision_ordinal: int,
        effective_srg_state: Mapping[str, Any],
        effective_collision_report: Mapping[str, Any] | None,
    ) -> "SRGSuccessorMaterialization":
        state = _freeze_mapping(effective_srg_state, field="effective SRG state")
        report = (
            None if effective_collision_report is None else _freeze_mapping(
                effective_collision_report, field="effective SRG collision report"
            )
        )
        return cls(
            predecessor_revision_id,
            predecessor_revision_ordinal,
            state,
            report,
            _materialization_digest(
                predecessor_revision_id, predecessor_revision_ordinal, state, report
            ),
        )

    @classmethod
    def from_intent(cls, value: object) -> "SRGSuccessorMaterialization":
        if not isinstance(value, Mapping):
            raise ValueError("srg materialization intent must be an object")
        return cls(
            predecessor_revision_id=UUID(str(value["predecessor_revision_id"])),
            predecessor_revision_ordinal=int(value["predecessor_revision_ordinal"]),
            effective_srg_state=value["effective_srg_state"],
            effective_collision_report=value.get("effective_collision_report"),
            canonical_digest=str(value["canonical_digest"]),
        )

    def intent(self) -> dict[str, Any]:
        return {
            "predecessor_revision_id": str(self.predecessor_revision_id),
            "predecessor_revision_ordinal": self.predecessor_revision_ordinal,
            "effective_srg_state": _thaw(self.effective_srg_state),
            "effective_collision_report": _thaw(self.effective_collision_report),
            "canonical_digest": self.canonical_digest,
        }

    def payload_contribution(self) -> dict[str, Any]:
        contribution = {"srg": _thaw(self.effective_srg_state)}
        if self.effective_collision_report is not None:
            contribution["srg_collision"] = _thaw(self.effective_collision_report)
        return contribution

    def validates_predecessor(self, *, revision_id: UUID, revision_ordinal: int) -> bool:
        return (
            self.predecessor_revision_id == revision_id
            and self.predecessor_revision_ordinal == revision_ordinal
        )


class NativeSRGProcessState:
    """Process-owned SRG overlays and exact revision witnesses, without I/O."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._overlays: dict[tuple[UUID, UUID, int], _NativeSRGOverlay] = {}
        self._observed_revisions: dict[tuple[UUID, UUID, int], UUID] = {}

    def observe(
        self, *, core_id: UUID, namespace: UUID, eid: int, revision_id: UUID
    ) -> _NativeSRGOverlay | None:
        key = _overlay_key(core_id, namespace, eid)
        with self._lock:
            overlay = self._overlays.get(key)
            if overlay is None:
                return None
            observed = self._observed_revisions.get(key)
            if observed is not None and observed != revision_id:
                raise SubstrateInvariantViolation("native SRG current revision changed under runtime state")
            if overlay is not None and overlay.revision_id != revision_id:
                raise SubstrateInvariantViolation(
                    "native SRG overlay is stale against current revision"
                )
            return overlay

    def set_overlay(
        self,
        *,
        core_id: UUID,
        namespace: UUID,
        eid: int,
        revision_id: UUID,
        srg_state: Mapping[str, Any],
        collision_report: Mapping[str, Any] | None,
    ) -> None:
        key = _overlay_key(core_id, namespace, eid)
        with self._lock:
            observed = self._observed_revisions.get(key)
            if observed is not None and observed != revision_id:
                raise SubstrateInvariantViolation(
                    "native SRG current revision changed under runtime state"
                )
            self._observed_revisions[key] = revision_id
            self._overlays[key] = _NativeSRGOverlay(
                revision_id,
                _freeze_mapping(srg_state, field="native transient srg state"),
                None if collision_report is None else _freeze_mapping(
                    collision_report, field="native transient collision report"
                ),
            )

    def consume_if_matching(
        self,
        *,
        core_id: UUID,
        namespace: UUID,
        eid: int,
        materialization: SRGSuccessorMaterialization,
    ) -> None:
        key = _overlay_key(core_id, namespace, eid)
        with self._lock:
            overlay = self._overlays.get(key)
            if overlay is None:
                return
            candidate = SRGSuccessorMaterialization.create(
                predecessor_revision_id=overlay.revision_id,
                predecessor_revision_ordinal=materialization.predecessor_revision_ordinal,
                effective_srg_state=overlay.srg_state,
                effective_collision_report=overlay.collision_report,
            )
            if candidate.canonical_digest != materialization.canonical_digest:
                raise SubstrateInvariantViolation(
                    "native SRG overlay differs from the durable materialization intent"
                )
            self._overlays.pop(key)
            self._observed_revisions.pop(key, None)


class NativeSRGTransientRuntime(SRGTransientRuntimePort):
    """Connection-scoped adapter around a reusable process-owned SRG owner."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        legacy_source_namespace_id: UUID,
        process_state: NativeSRGProcessState | None = None,
    ) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("connection must be an already-open sqlite connection")
        if not isinstance(legacy_source_namespace_id, UUID):
            raise ValueError("legacy_source_namespace_id must be a UUID")
        metadata = require_current_schema(connection)
        self._reads = NativeMemoryCompatibilityFacade(connection)
        self._core_id = UUID(bytes=metadata.core_id)
        self._namespace = legacy_source_namespace_id
        self._process_state = process_state or NativeSRGProcessState()

    def effective_srg_state(self, memory: RuntimeMemoryView) -> Mapping[str, Any] | None:
        source, overlay = self._observe_current(memory)
        if overlay is not None:
            return _freeze_mapping(overlay.srg_state, field="native transient srg state")
        value = source.payload.get("srg")
        if not value:
            return None
        return _freeze_mapping(value, field="native durable srg baseline")

    def effective_collision_report(self, memory: RuntimeMemoryView) -> Mapping[str, Any] | None:
        source, overlay = self._observe_current(memory)
        if overlay is not None:
            if overlay.collision_report is None:
                return None
            return _freeze_mapping(overlay.collision_report, field="native transient collision report")
        value = source.payload.get("srg_collision")
        if value is None:
            return None
        return _freeze_mapping(value, field="native durable collision report")

    def apply_collision(
        self,
        *,
        existing: RuntimeMemoryView,
        incoming: RuntimeMemoryView,
        existing_state: Mapping[str, Any],
        incoming_state: Mapping[str, Any],
        incoming_report: Mapping[str, Any],
    ) -> None:
        existing_source, existing_overlay = self._observe_current(existing)
        incoming_source, _ = self._observe_current(incoming)
        self._process_state.set_overlay(
            core_id=self._core_id,
            namespace=self._namespace,
            eid=existing.eid,
            revision_id=existing_source.revision_id,
            srg_state=existing_state,
            collision_report=None if existing_overlay is None else existing_overlay.collision_report,
        )
        self._process_state.set_overlay(
            core_id=self._core_id,
            namespace=self._namespace,
            eid=incoming.eid,
            revision_id=incoming_source.revision_id,
            srg_state=incoming_state,
            collision_report=incoming_report,
        )

    def prepare_successor_materialization(
        self,
        *,
        eid: int,
        expected_revision_id: UUID,
    ) -> SRGSuccessorMaterialization | None:
        if not isinstance(eid, int) or isinstance(eid, bool) or eid < 0:
            raise ValueError("eid must be a non-negative integer")
        if not isinstance(expected_revision_id, UUID):
            raise ValueError("expected_revision_id must be a UUID")
        source = self._current_eid(eid)
        overlay = self._process_state.observe(
            core_id=self._core_id,
            namespace=self._namespace,
            eid=eid,
            revision_id=source.revision_id,
        )
        if source.revision_id != expected_revision_id:
            raise SubstrateInvariantViolation("native SRG materialization predecessor is not current")
        if overlay is None:
            return None
        return SRGSuccessorMaterialization.create(
            predecessor_revision_id=source.revision_id,
            predecessor_revision_ordinal=source.revision_ordinal,
            effective_srg_state=overlay.srg_state,
            effective_collision_report=overlay.collision_report,
        )

    def acknowledge_materialized_successor(
        self,
        materialization: SRGSuccessorMaterialization,
        *,
        eid: int,
        successor_revision_id: UUID,
    ) -> None:
        if not isinstance(materialization, SRGSuccessorMaterialization):
            raise ValueError("materialization must be SRGSuccessorMaterialization")
        if not isinstance(successor_revision_id, UUID):
            raise ValueError("successor_revision_id must be a UUID")
        source = self._current_eid(eid)
        if source.revision_id != successor_revision_id:
            raise SubstrateInvariantViolation("native SRG materialized successor is not current")
        if source.revision_ordinal != materialization.predecessor_revision_ordinal + 1:
            raise SubstrateInvariantViolation("native SRG materialized successor ordinal is invalid")
        if source.payload.get("srg") != materialization.payload_contribution()["srg"]:
            raise SubstrateInvariantViolation("native SRG materialized successor has different SRG state")
        if (
            materialization.effective_collision_report is not None
            and source.payload.get("srg_collision")
            != materialization.payload_contribution()["srg_collision"]
        ):
            raise SubstrateInvariantViolation(
                "native SRG materialized successor has different collision report"
            )
        self._process_state.consume_if_matching(
            core_id=self._core_id,
            namespace=self._namespace,
            eid=eid,
            materialization=materialization,
        )

    def _observe_current(
        self, memory: RuntimeMemoryView
    ) -> tuple[LegacyMemoryView, _NativeSRGOverlay | None]:
        source = self._current_eid(memory.eid)
        overlay = self._process_state.observe(
            core_id=self._core_id,
            namespace=self._namespace,
            eid=memory.eid,
            revision_id=source.revision_id,
        )
        return source, overlay

    def _current_eid(self, eid: int) -> LegacyMemoryView:
        try:
            return self._reads.get_memory_by_eid(
                legacy_source_namespace_id=self._namespace, eid=eid,
            )
        except SubstrateObjectNotFound as exc:
            raise SubstrateInvariantViolation("native SRG memory is no longer current") from exc


def _overlay_key(core_id: UUID, namespace: UUID, eid: int) -> tuple[UUID, UUID, int]:
    return (core_id, namespace, eid)


def _materialization_digest(
    predecessor_revision_id: UUID,
    predecessor_revision_ordinal: int,
    state: Mapping[str, Any],
    report: Mapping[str, Any] | None,
) -> str:
    return hashlib.sha256(canonical_intent_text({
        "predecessor_revision_id": str(predecessor_revision_id),
        "predecessor_revision_ordinal": predecessor_revision_ordinal,
        "effective_srg_state": _thaw(state),
        "effective_collision_report": _thaw(report),
    }).encode("utf-8")).hexdigest()


def _freeze_mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return MappingProxyType(json.loads(canonical_intent_text(value)))


def _thaw(value: object) -> Any:
    return json.loads(canonical_intent_text(value))


__all__ = [
    "NativeSRGProcessState",
    "NativeSRGTransientRuntime",
    "SRGSuccessorMaterialization",
]
