"""Process-local SRG collision state boundary.

This module is intentionally backend-neutral.  It contains the legacy live
payload provider and the consumer-facing protocol, but no substrate imports.
The native provider lives behind the substrate boundary and keeps its overlay
only in process memory.
"""
from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import Any, Mapping, MutableMapping, Protocol

from .memory_runtime_access import RuntimeMemoryView


class SRGTransientRuntimePort(Protocol):
    """Effective SRG state only; this is not a durable mutation service."""

    def effective_srg_state(self, memory: RuntimeMemoryView) -> Mapping[str, Any] | None: ...

    def effective_collision_report(self, memory: RuntimeMemoryView) -> Mapping[str, Any] | None: ...

    def apply_collision(
        self,
        *,
        existing: RuntimeMemoryView,
        incoming: RuntimeMemoryView,
        existing_state: Mapping[str, Any],
        incoming_state: Mapping[str, Any],
        incoming_report: Mapping[str, Any],
    ) -> None: ...


class LegacySRGTransientRuntime:
    """Legacy's existing process-local overlay: mutable live SeedEntity payloads."""

    def __init__(self, graph: Any) -> None:
        if not hasattr(graph, "entities"):
            raise ValueError("graph must expose selected live entities")
        self._graph = graph

    def effective_srg_state(self, memory: RuntimeMemoryView) -> Mapping[str, Any] | None:
        payload = self._payload(memory)
        value = payload.get("srg")
        if not value:
            return None
        return _freeze_mapping(value, field="legacy live srg state")

    def effective_collision_report(self, memory: RuntimeMemoryView) -> Mapping[str, Any] | None:
        payload = self._payload(memory)
        value = payload.get("srg_collision")
        if value is None:
            return None
        return _freeze_mapping(value, field="legacy live srg collision report")

    def apply_collision(
        self,
        *,
        existing: RuntimeMemoryView,
        incoming: RuntimeMemoryView,
        existing_state: Mapping[str, Any],
        incoming_state: Mapping[str, Any],
        incoming_report: Mapping[str, Any],
    ) -> None:
        # This deliberately preserves the original collision site's direct
        # in-memory payload mutation and performs no flush/update operation.
        self._mutable_payload(existing)["srg"] = deepcopy(dict(existing_state))
        own_payload = self._mutable_payload(incoming)
        own_payload["srg"] = deepcopy(dict(incoming_state))
        own_payload["srg_collision"] = deepcopy(dict(incoming_report))

    def _payload(self, memory: RuntimeMemoryView) -> Mapping[str, Any]:
        entity = self._graph.entities.get(memory.eid)
        if entity is None:
            raise ValueError("live memory disappeared during SRG processing")
        payload = getattr(entity, "payload", None)
        if not isinstance(payload, Mapping):
            raise ValueError("live memory payload is not a mapping")
        return payload

    def _mutable_payload(self, memory: RuntimeMemoryView) -> MutableMapping[str, Any]:
        payload = self._payload(memory)
        if not isinstance(payload, MutableMapping):
            raise ValueError("live memory payload is not mutable")
        return payload


def _freeze_mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return MappingProxyType(deepcopy(dict(value)))


__all__ = ["LegacySRGTransientRuntime", "SRGTransientRuntimePort"]
