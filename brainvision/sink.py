"""Phase-12 bounded commit-time projection sink hosting.

This module owns no Brainvision state, persistence, lifecycle, or projection
mathematics.  It only fixes a Phase-5 projection from a successful Phase-10
commit before the agent transaction is released, then optionally delivers the
detached mapping outside that transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Final
from weakref import WeakValueDictionary

from brainvision.ingress import (
    FirsthandVisualAdmissionReceipt,
    _admit_firsthand_visual_observation_with_committed_snapshot,
    admit_firsthand_visual_observation,
)
from brainvision.lifecycle import (
    BrainvisionLifecycleManager,
    BrainvisionRuntimeSnapshot,
)
from brainvision.observation import FirsthandVisualObservationV1
from brainvision.projection import project_vhe_state


class Phase12SinkError(ValueError):
    """One Phase-12 host construction or use error."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


@dataclass(frozen=True, kw_only=True)
class Phase12SinkMetrics:
    """Immutable process-local diagnostics for one bound host."""

    sink_invocations_total: int
    sink_delivery_failures_total: int
    projection_construction_failures_total: int


@dataclass(frozen=True, kw_only=True)
class _ProjectionCapture:
    """Private result of construction while the Phase-10 lock remains held."""

    payload: dict[str, object] | None
    construction_failed: bool


_LineageKey = tuple[int, str, str]
_REGISTRY_LOCK: Final = RLock()
_LIVE_HOSTS: Final = WeakValueDictionary()


def _construct_committed_projection(
    committed_snapshot: BrainvisionRuntimeSnapshot,
) -> dict[str, object]:
    """Build one detached Phase-5 projection at the committed active time."""

    projection = project_vhe_state(committed_snapshot.vhe_state, 0)
    return dict(projection.to_dict())


class Phase12IngressHost:
    """One process-local optional sink bound to one Brainvision agent lineage."""

    def __init__(
        self,
        *,
        lifecycle_manager: BrainvisionLifecycleManager,
        workspace_id: str,
        agent_id: str,
        sink: object | None = None,
    ) -> None:
        if sink is not None and not callable(getattr(sink, "on_projection", None)):
            raise Phase12SinkError("sink", "invalid_sink")

        self._lifecycle_manager = lifecycle_manager
        self._workspace_id = workspace_id
        self._agent_id = agent_id
        self._sink = sink
        self._lineage_key: _LineageKey = (id(lifecycle_manager), workspace_id, agent_id)
        self._delivery_order_gate = RLock()
        self._admission_or_delivery_active = False
        self._closed = False
        self._sink_invocations_total = 0
        self._sink_delivery_failures_total = 0
        self._projection_construction_failures_total = 0

        with _REGISTRY_LOCK:
            incumbent = _LIVE_HOSTS.get(self._lineage_key)
            if incumbent is not None and not incumbent._closed:
                raise Phase12SinkError("host", "duplicate_lineage")
            _LIVE_HOSTS[self._lineage_key] = self

    def close(self) -> None:
        """Release this process-local host's same-lineage uniqueness claim."""

        with self._delivery_order_gate:
            if self._admission_or_delivery_active:
                raise Phase12SinkError("host", "close_while_active")
            if self._closed:
                return
            with _REGISTRY_LOCK:
                if _LIVE_HOSTS.get(self._lineage_key) is self:
                    del _LIVE_HOSTS[self._lineage_key]
            self._closed = True

    def __enter__(self) -> Phase12IngressHost:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def metrics_snapshot(self) -> Phase12SinkMetrics:
        """Return the sole immutable, non-persistent Phase-12 diagnostic view."""

        with self._delivery_order_gate:
            return Phase12SinkMetrics(
                sink_invocations_total=self._sink_invocations_total,
                sink_delivery_failures_total=self._sink_delivery_failures_total,
                projection_construction_failures_total=(
                    self._projection_construction_failures_total
                ),
            )

    def admit(
        self,
        observation: FirsthandVisualObservationV1,
    ) -> FirsthandVisualAdmissionReceipt:
        """Admit one bound observation and optionally deliver its fixed projection."""

        with self._delivery_order_gate:
            if self._closed:
                raise Phase12SinkError("host", "closed")
            if self._admission_or_delivery_active:
                raise Phase12SinkError("host", "reentrant_admission")
            self._admission_or_delivery_active = True
            try:
                if self._sink is None:
                    return admit_firsthand_visual_observation(
                        lifecycle_manager=self._lifecycle_manager,
                        workspace_id=self._workspace_id,
                        agent_id=self._agent_id,
                        observation=observation,
                    )

                def capture(
                    _receipt: FirsthandVisualAdmissionReceipt,
                    committed_snapshot: BrainvisionRuntimeSnapshot,
                ) -> _ProjectionCapture:
                    try:
                        return _ProjectionCapture(
                            payload=_construct_committed_projection(committed_snapshot),
                            construction_failed=False,
                        )
                    except Exception:
                        return _ProjectionCapture(payload=None, construction_failed=True)

                receipt, capture_result = (
                    _admit_firsthand_visual_observation_with_committed_snapshot(
                        lifecycle_manager=self._lifecycle_manager,
                        workspace_id=self._workspace_id,
                        agent_id=self._agent_id,
                        observation=observation,
                        capture_committed_snapshot=capture,
                    )
                )
                if capture_result.construction_failed:
                    self._projection_construction_failures_total += 1
                    return receipt

                payload = capture_result.payload
                if payload is None:
                    raise AssertionError("successful projection capture must include payload")
                try:
                    self._sink.on_projection(receipt, payload)
                except Exception:
                    self._sink_delivery_failures_total += 1
                else:
                    self._sink_invocations_total += 1
                return receipt
            finally:
                self._admission_or_delivery_active = False


__all__ = (
    "Phase12IngressHost",
    "Phase12SinkError",
    "Phase12SinkMetrics",
)
