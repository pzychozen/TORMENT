"""Native process-local SRG overlay with exact current-revision witnesses."""
from __future__ import annotations

from copy import deepcopy
import sqlite3
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from torment_service.memory_runtime_access import RuntimeMemoryView
from torment_service.srg_runtime_state import SRGTransientRuntimePort

from .compat import LegacyMemoryView, NativeMemoryCompatibilityFacade
from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from .schema import require_current_schema


@dataclass(frozen=True)
class _NativeSRGOverlay:
    revision_id: UUID
    srg_state: Mapping[str, Any]
    collision_report: Mapping[str, Any] | None


class NativeSRGTransientRuntime(SRGTransientRuntimePort):
    """Per-instance transient SRG state; it never writes SQLite or a shadow."""

    def __init__(self, connection: sqlite3.Connection, *, legacy_source_namespace_id: UUID) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("connection must be an already-open sqlite connection")
        if not isinstance(legacy_source_namespace_id, UUID):
            raise ValueError("legacy_source_namespace_id must be a UUID")
        require_current_schema(connection)
        self._reads = NativeMemoryCompatibilityFacade(connection)
        self._namespace = legacy_source_namespace_id
        self._overlays: dict[int, _NativeSRGOverlay] = {}
        self._observed_revisions: dict[int, UUID] = {}

    def effective_srg_state(self, memory: RuntimeMemoryView) -> Mapping[str, Any] | None:
        source = self._observe_current(memory)
        overlay = self._overlays.get(memory.eid)
        if overlay is not None:
            return _freeze_mapping(overlay.srg_state, field="native transient srg state")
        value = source.payload.get("srg")
        if not value:
            return None
        return _freeze_mapping(value, field="native durable srg baseline")

    def effective_collision_report(self, memory: RuntimeMemoryView) -> Mapping[str, Any] | None:
        source = self._observe_current(memory)
        overlay = self._overlays.get(memory.eid)
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
        existing_source = self._observe_current(existing)
        incoming_source = self._observe_current(incoming)
        self._overlays[existing.eid] = _NativeSRGOverlay(
            existing_source.revision_id,
            _freeze_mapping(existing_state, field="existing SRG collision state"),
            self._overlays.get(existing.eid).collision_report if existing.eid in self._overlays else None,
        )
        self._overlays[incoming.eid] = _NativeSRGOverlay(
            incoming_source.revision_id,
            _freeze_mapping(incoming_state, field="incoming SRG collision state"),
            _freeze_mapping(incoming_report, field="incoming SRG collision report"),
        )

    def _observe_current(self, memory: RuntimeMemoryView) -> LegacyMemoryView:
        try:
            source = self._reads.get_memory_by_eid(
                legacy_source_namespace_id=self._namespace, eid=memory.eid,
            )
        except SubstrateObjectNotFound as exc:
            raise SubstrateInvariantViolation("native SRG memory is no longer current") from exc
        observed = self._observed_revisions.get(memory.eid)
        overlay = self._overlays.get(memory.eid)
        if observed is not None and observed != source.revision_id:
            raise SubstrateInvariantViolation("native SRG current revision changed under runtime state")
        if overlay is not None and overlay.revision_id != source.revision_id:
            raise SubstrateInvariantViolation("native SRG overlay is stale against current revision")
        self._observed_revisions[memory.eid] = source.revision_id
        return source


def _freeze_mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return MappingProxyType(deepcopy(dict(value)))


__all__ = ["NativeSRGTransientRuntime"]
