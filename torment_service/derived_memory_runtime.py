"""Backend-neutral semantic boundary for default derived-memory work.

The post-write adapter coordinates this port after motif entropy maintenance.
The port deliberately exposes only the three legacy semantic operations; it
does not leak graph, SQLite, representation, or payload mutation primitives.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class DerivedMemoryRuntimeContext:
    """Frozen post-write facts consumed by the derived-memory boundary."""

    workspace_id: str
    agent_id: str
    domain_id: str
    step: int
    motif_ids: tuple[str, ...]
    affect_tag: str | None
    affect_conf: float | None


class DerivedMemoryRuntimePort(Protocol):
    """Closed derived-memory semantic operations; no persistence primitives."""

    def maybe_emit_identity_anchor(self, context: DerivedMemoryRuntimeContext) -> int | None:
        """Possibly create one identity anchor for the current motif pass."""

    def refine_identity_anchors(self, context: DerivedMemoryRuntimeContext) -> None:
        """Apply the legacy anchor lifecycle hygiene pass."""

    def maybe_emit_mood_drift(self, context: DerivedMemoryRuntimeContext) -> int | None:
        """Possibly write one mood-drift memory after affect side-state update."""


class DerivedMemorySideStorePort(Protocol):
    """Existing independent JSON workflow state, not substrate state."""

    def load_anchor_state(self, *, workspace_id: str, agent_id: str) -> Mapping[str, Any]: ...
    def save_anchor_state(self, *, workspace_id: str, agent_id: str, state: Mapping[str, Any]) -> None: ...
    def load_affect_state(self, *, workspace_id: str, agent_id: str) -> Mapping[str, Any]: ...
    def save_affect_state(self, *, workspace_id: str, agent_id: str, state: Mapping[str, Any]) -> None: ...


class LegacyDerivedMemoryRuntime:
    """Exact adapter over the already selected legacy Fabric objects.

    The historical methods remain their single source of policy truth.  This
    adapter merely moves their invocation out of the generic post-write
    coordinator and preserves the three independent fail-soft call sites.
    """

    def __init__(self, *, owner: Any, workspace: Any) -> None:
        self._owner = owner
        self._workspace = workspace

    def maybe_emit_identity_anchor(self, context: DerivedMemoryRuntimeContext) -> int | None:
        return self._owner._maybe_emit_identity_anchor(
            self._workspace,
            agent_id=context.agent_id,
            domain_id=context.domain_id,
            step=int(context.step),
            motif_ids=list(context.motif_ids),
        )

    def refine_identity_anchors(self, context: DerivedMemoryRuntimeContext) -> None:
        self._owner._refine_identity_anchors(
            self._workspace,
            agent_id=context.agent_id,
            domain_id=context.domain_id,
            motif_ids=list(context.motif_ids),
        )

    def maybe_emit_mood_drift(self, context: DerivedMemoryRuntimeContext) -> int | None:
        return self._owner._maybe_emit_mood_drift(
            self._workspace,
            agent_id=context.agent_id,
            domain_id=context.domain_id,
            step=int(context.step),
            affect_tag=context.affect_tag,
            affect_conf=context.affect_conf,
        )


__all__ = [
    "DerivedMemoryRuntimeContext",
    "DerivedMemoryRuntimePort",
    "DerivedMemorySideStorePort",
    "LegacyDerivedMemoryRuntime",
]
