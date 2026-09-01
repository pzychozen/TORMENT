"""Process-local native world state for qualified A3D routing.

The owner in this module deliberately contains no SQLite handle, database
path, selector, or durable mutation authority.  A short-lived adapter binds an
already-qualified connection only long enough to verify current native memory
truth and synchronize the process-local world.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import logging
import sqlite3
import threading
from typing import Any, Iterator, Mapping
from uuid import UUID

import numpy as np

from torment_service.kernel.seed_entities import SeedWorld
from torment_service.kernel.seed_trajectory_analysis import classify_trajectory
from torment_service.world_runtime import WorldRuntimePort

from .canonical_intent import canonical_intent_text
from .compat import LegacyMemoryView, NativeMemoryCompatibilityFacade
from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from .native_memory_runtime_access import NativePostWriteMemoryAccess
from .schema import require_current_schema


log = logging.getLogger("torment.substrate.native_world")


@dataclass
class NativeWorldEntity:
    """A SeedWorld-compatible entity whose origin facts may be unavailable.

    Rehydrated native rows have no invented ``born_step`` or ``channel``.  The
    existing SeedWorld physics and trajectory mathematics do not consume those
    two facts, so ``None`` keeps that evidence boundary explicit.
    """

    eid: int
    born_step: int | None
    channel: int | None
    pos: np.ndarray
    vel: np.ndarray
    vel0: np.ndarray
    payload: dict[str, Any]
    trail: list[np.ndarray] = field(default_factory=list)
    alive: bool = True
    r_history: list[float] = field(default_factory=list)
    z_history: list[float] = field(default_factory=list)
    x_history: list[float] = field(default_factory=list)
    y_history: list[float] = field(default_factory=list)

    def push_trail(self, maxlen: int = 200) -> None:
        self.trail.append(self.pos.copy())
        if len(self.trail) > maxlen:
            self.trail.pop(0)


@dataclass(frozen=True)
class WorldDiagnosticSuccessorMaterialization:
    """Typed process-local trajectory fields for one authorized successor."""

    predecessor_revision_id: UUID
    predecessor_revision_ordinal: int
    traj_label: str
    traj_last_classify_step: int
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
        if not isinstance(self.traj_label, str):
            raise ValueError("traj_label must be text")
        if (
            not isinstance(self.traj_last_classify_step, int)
            or isinstance(self.traj_last_classify_step, bool)
            or self.traj_last_classify_step < 0
        ):
            raise ValueError("traj_last_classify_step must be a non-negative integer")
        if self.canonical_digest != _diagnostic_digest(
            self.predecessor_revision_id,
            self.predecessor_revision_ordinal,
            self.traj_label,
            self.traj_last_classify_step,
        ):
            raise ValueError("canonical_digest does not match world diagnostic materialization")

    @classmethod
    def create(
        cls,
        *,
        predecessor_revision_id: UUID,
        predecessor_revision_ordinal: int,
        traj_label: str,
        traj_last_classify_step: int,
    ) -> "WorldDiagnosticSuccessorMaterialization":
        return cls(
            predecessor_revision_id,
            predecessor_revision_ordinal,
            traj_label,
            traj_last_classify_step,
            _diagnostic_digest(
                predecessor_revision_id,
                predecessor_revision_ordinal,
                traj_label,
                traj_last_classify_step,
            ),
        )

    @classmethod
    def from_intent(cls, value: object) -> "WorldDiagnosticSuccessorMaterialization":
        if not isinstance(value, Mapping):
            raise ValueError("world diagnostic materialization intent must be an object")
        return cls(
            predecessor_revision_id=UUID(str(value["predecessor_revision_id"])),
            predecessor_revision_ordinal=int(value["predecessor_revision_ordinal"]),
            traj_label=str(value["traj_label"]),
            traj_last_classify_step=int(value["traj_last_classify_step"]),
            canonical_digest=str(value["canonical_digest"]),
        )

    def intent(self) -> dict[str, Any]:
        return {
            "predecessor_revision_id": str(self.predecessor_revision_id),
            "predecessor_revision_ordinal": self.predecessor_revision_ordinal,
            "traj_label": self.traj_label,
            "traj_last_classify_step": self.traj_last_classify_step,
            "canonical_digest": self.canonical_digest,
        }

    def payload_contribution(self) -> dict[str, Any]:
        return {
            "traj_label": self.traj_label,
            "traj_last_classify_step": self.traj_last_classify_step,
        }

    def validates_predecessor(self, *, revision_id: UUID, revision_ordinal: int) -> bool:
        return (
            self.predecessor_revision_id == revision_id
            and self.predecessor_revision_ordinal == revision_ordinal
        )


@dataclass(frozen=True)
class NativeWorldRuntimeSnapshot:
    """Read-only diagnostic view; it grants no routing or mutation authority."""

    eids: tuple[int, ...]
    positions: tuple[tuple[float, float, float], ...]
    velocities: tuple[tuple[float, float, float], ...]
    trail_lengths: tuple[int, ...]
    history_lengths: tuple[int, ...]
    born_steps: tuple[int | None, ...]
    channels: tuple[int | None, ...]
    classifications: tuple[tuple[str, int] | None, ...]


@dataclass(frozen=True)
class _WorldDiagnosticOverlay:
    revision_id: UUID
    revision_ordinal: int
    traj_label: str
    traj_last_classify_step: int


@dataclass
class _WorldEntry:
    entity: NativeWorldEntity
    object_id: UUID
    revision_id: UUID
    revision_ordinal: int
    diagnostic: _WorldDiagnosticOverlay | None = None


@dataclass
class _WorldScope:
    world: SeedWorld = field(default_factory=SeedWorld)
    entries: dict[int, _WorldEntry] = field(default_factory=dict)


class NativeWorldProcessState:
    """Reusable process-owned worlds, keyed only by core and source namespace."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._scopes: dict[tuple[UUID, UUID], _WorldScope] = {}

    @contextmanager
    def locked_scope(
        self, *, core_id: UUID, namespace: UUID
    ) -> Iterator[_WorldScope | None]:
        """Internal adapter coordination; no I/O resource is retained."""
        key = (core_id, namespace)
        with self._lock:
            yield self._scopes.get(key)

    def initialize(
        self, *, core_id: UUID, namespace: UUID, scope: _WorldScope) -> None:
        key = (core_id, namespace)
        with self._lock:
            if key in self._scopes:
                raise SubstrateInvariantViolation("native world scope was initialized concurrently")
            self._scopes[key] = scope


class NativeWorldRuntime(WorldRuntimePort):
    """Connection-scoped verifier and synchronizer for one native world owner."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        legacy_source_namespace_id: UUID,
        expected_dimension: int,
        process_state: NativeWorldProcessState | None = None,
    ) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("connection must be an already-open sqlite connection")
        if not isinstance(legacy_source_namespace_id, UUID):
            raise ValueError("legacy_source_namespace_id must be a UUID")
        metadata = require_current_schema(connection)
        self._core_id = UUID(bytes=metadata.core_id)
        self._namespace = legacy_source_namespace_id
        self._reads = NativeMemoryCompatibilityFacade(connection)
        self._enumeration = NativePostWriteMemoryAccess(
            connection,
            legacy_source_namespace_id=legacy_source_namespace_id,
            expected_dimension=expected_dimension,
        )
        self._process_state = process_state or NativeWorldProcessState()

    def ensure_initialized(self) -> None:
        """Load once with legacy restart semantics, then verify exact topology."""
        snapshots = self._snapshots()
        with self._process_state.locked_scope(
            core_id=self._core_id, namespace=self._namespace
        ) as scope:
            if scope is not None:
                self._assert_current(scope, snapshots)
                return
            new_scope = _WorldScope()
            for source in snapshots:
                entity = _entity_from_source(source, born_step=None, channel=None, fresh=False)
                new_scope.world.entities.append(entity)  # SeedWorld uses duck typing here.
                new_scope.entries[source.eid] = _WorldEntry(
                    entity, source.object_id, source.revision_id, source.revision_ordinal,
                )
        self._process_state.initialize(
            core_id=self._core_id, namespace=self._namespace, scope=new_scope,
        )

    def register_fresh_created(
        self,
        *,
        eid: int,
        memory_object_id: UUID,
        memory_revision_id: UUID,
        memory_revision_ordinal: int,
        born_step: int,
        channel: int = 0,
    ) -> None:
        """Register an A3C2-committed source before later representation work."""
        if not isinstance(born_step, int) or isinstance(born_step, bool) or born_step < 0:
            raise ValueError("born_step must be a non-negative integer")
        snapshots = self._snapshots()
        source = _source_for_eid(snapshots, eid)
        if (
            source.object_id != memory_object_id
            or source.revision_id != memory_revision_id
            or source.revision_ordinal != memory_revision_ordinal
        ):
            raise SubstrateInvariantViolation("fresh native world source does not match committed A3C2 result")
        with self._process_state.locked_scope(
            core_id=self._core_id, namespace=self._namespace
        ) as scope:
            if scope is None:
                raise SubstrateInvariantViolation("native world must initialize before a source operation")
            existing = scope.entries.get(eid)
            if existing is not None:
                if (
                    existing.object_id != source.object_id
                    or existing.revision_id != source.revision_id
                    or existing.revision_ordinal != source.revision_ordinal
                ):
                    raise SubstrateInvariantViolation("fresh native world registration conflicts with live topology")
                self._assert_current(scope, snapshots)
                return
            expected = tuple(scope.entries)
            actual = tuple(item.eid for item in snapshots)
            if actual != (*expected, eid):
                raise SubstrateInvariantViolation("fresh native world source is not the sole ordered topology append")
            entity = _entity_from_source(source, born_step=born_step, channel=channel, fresh=True)
            scope.world.entities.append(entity)
            scope.entries[eid] = _WorldEntry(
                entity, source.object_id, source.revision_id, source.revision_ordinal,
            )

    def synchronize_reinforcement_successor(
        self,
        *,
        eid: int,
        memory_object_id: UUID,
        predecessor_revision_id: UUID,
        predecessor_revision_ordinal: int,
        successor_revision_id: UUID,
        successor_revision_ordinal: int,
    ) -> None:
        """Apply legacy full-payload kinematic reset after an already-committed R2."""
        snapshots = self._snapshots()
        source = _source_for_eid(snapshots, eid)
        if (
            source.object_id != memory_object_id
            or source.revision_id != successor_revision_id
            or source.revision_ordinal != successor_revision_ordinal
        ):
            raise SubstrateInvariantViolation("native reinforcement successor is not exact current memory truth")
        with self._process_state.locked_scope(
            core_id=self._core_id, namespace=self._namespace
        ) as scope:
            if scope is None:
                raise SubstrateInvariantViolation("native world must initialize before a source operation")
            self._assert_topology(scope, snapshots)
            entry = scope.entries.get(eid)
            if entry is None or entry.object_id != memory_object_id:
                raise SubstrateInvariantViolation("native reinforcement target is absent from process world")
            if entry.revision_id == successor_revision_id:
                if entry.revision_ordinal != successor_revision_ordinal:
                    raise SubstrateInvariantViolation("native world successor ordinal changed unexpectedly")
                return
            if (
                entry.revision_id != predecessor_revision_id
                or entry.revision_ordinal != predecessor_revision_ordinal
            ):
                raise SubstrateInvariantViolation("native world reinforcement predecessor changed unexpectedly")
            diagnostic = entry.diagnostic
            if diagnostic is not None:
                if (
                    diagnostic.revision_id != predecessor_revision_id
                    or diagnostic.revision_ordinal != predecessor_revision_ordinal
                    or source.payload.get("traj_label") != diagnostic.traj_label
                    or source.payload.get("traj_last_classify_step") != diagnostic.traj_last_classify_step
                ):
                    raise SubstrateInvariantViolation(
                        "native world diagnostic overlay was omitted from its legitimate successor"
                    )
            entity = entry.entity
            # This is the intentional legacy quirk: an ordinary successor
            # resets live kinematics from complete durable payload, while every
            # trail/history/classification carrier remains in place.
            entity.pos = _payload_vec3(source.payload, "pos", fallback="seed_pos0")
            entity.vel = _payload_vec3(source.payload, "vel", fallback="seed_v0")
            entity.vel0 = _payload_vec3(source.payload, "vel0", fallback="vel")
            entity.payload = dict(source.payload)
            entry.revision_id = successor_revision_id
            entry.revision_ordinal = successor_revision_ordinal

    def write_trajectory_genesis_for_post_write(self, *, eid: int, evidence: Any) -> None:
        """Expose one freshly source-bound birth to an external V2 evidence sink.

        The entity is never reconstructed here and the sink receives no native
        storage authority.  The caller uses this only for a current
        ``CREATED_NEW`` route, matching the legacy V2 creation boundary.
        """
        snapshots = self._snapshots()
        with self._process_state.locked_scope(
            core_id=self._core_id, namespace=self._namespace
        ) as scope:
            if scope is None:
                raise SubstrateInvariantViolation("native world runtime is not initialized")
            self._assert_current(scope, snapshots)
            entry = scope.entries.get(int(eid))
            if entry is None:
                raise SubstrateInvariantViolation("native trajectory genesis source is absent")
            try:
                evidence.write_genesis(entry.entity)
            except Exception as exc:
                log.debug("Trajectory genesis skipped for eid=%s: %s", eid, exc)

    def advance_for_post_write(self, *, step: int) -> None:
        """Advance physics and typed diagnostic overlay without any native write."""
        self._advance_for_post_write(step=step, trajectory_evidence=None)

    def advance_for_post_write_with_trajectory_evidence(self, *, step: int, evidence: Any) -> None:
        """Advance then serialize only the current process-local world state."""
        if evidence is None:
            raise ValueError("trajectory evidence runtime is required")
        self._advance_for_post_write(step=step, trajectory_evidence=evidence)

    def _advance_for_post_write(self, *, step: int, trajectory_evidence: Any | None) -> None:
        """Keep native physics/classification ordering equal to ``MemoryGraph``."""
        snapshots = self._snapshots()
        with self._process_state.locked_scope(
            core_id=self._core_id, namespace=self._namespace
        ) as scope:
            if scope is None:
                raise SubstrateInvariantViolation("native world runtime is not initialized")
            self._assert_current(scope, snapshots)
            if any(
                entry.diagnostic is not None
                and (
                    entry.diagnostic.revision_id != entry.revision_id
                    or entry.diagnostic.revision_ordinal != entry.revision_ordinal
                )
                for entry in scope.entries.values()
            ):
                raise SubstrateInvariantViolation(
                    "native world has an unacknowledged materialized diagnostic successor"
                )
            scope.world.step()
            if trajectory_evidence is not None:
                try:
                    trajectory_evidence.write_step(tuple(scope.world.entities), step=int(step))
                except Exception as exc:
                    log.debug("Trajectory log skipped at step=%s: %s", step, exc)
            if int(step) % 50 != 0:
                return
            for eid, entry in scope.entries.items():
                entity = entry.entity
                if not entity.alive:
                    continue
                label = str(classify_trajectory(entity.r_history))
                entity.payload["traj_label"] = label
                entity.payload["traj_last_classify_step"] = int(step)
                entry.diagnostic = _WorldDiagnosticOverlay(
                    entry.revision_id, entry.revision_ordinal, label, int(step),
                )
                if trajectory_evidence is not None:
                    try:
                        trajectory_evidence.write_classification_event(
                            entity, step=int(step), label=label,
                        )
                    except Exception as exc:
                        log.debug("Traj classify event write skipped for eid=%s: %s", eid, exc)

    def prepare_successor_materialization(
        self, *, eid: int, expected_revision_id: UUID
    ) -> WorldDiagnosticSuccessorMaterialization | None:
        self.ensure_initialized()
        snapshots = self._snapshots()
        source = _source_for_eid(snapshots, eid)
        with self._process_state.locked_scope(
            core_id=self._core_id, namespace=self._namespace
        ) as scope:
            assert scope is not None
            self._assert_current(scope, snapshots)
            entry = scope.entries.get(eid)
            if entry is None or source.revision_id != expected_revision_id:
                raise SubstrateInvariantViolation("native world materialization predecessor is not current")
            diagnostic = entry.diagnostic
            if diagnostic is None:
                return None
            if (
                diagnostic.revision_id != source.revision_id
                or diagnostic.revision_ordinal != source.revision_ordinal
            ):
                raise SubstrateInvariantViolation("native world diagnostic overlay is stale")
            return WorldDiagnosticSuccessorMaterialization.create(
                predecessor_revision_id=diagnostic.revision_id,
                predecessor_revision_ordinal=diagnostic.revision_ordinal,
                traj_label=diagnostic.traj_label,
                traj_last_classify_step=diagnostic.traj_last_classify_step,
            )

    def acknowledge_materialized_successor(
        self,
        materialization: WorldDiagnosticSuccessorMaterialization,
        *,
        eid: int,
        successor_revision_id: UUID,
    ) -> None:
        if not isinstance(materialization, WorldDiagnosticSuccessorMaterialization):
            raise ValueError("materialization must be WorldDiagnosticSuccessorMaterialization")
        snapshots = self._snapshots()
        source = _source_for_eid(snapshots, eid)
        contribution = materialization.payload_contribution()
        if (
            source.revision_id != successor_revision_id
            or source.revision_ordinal != materialization.predecessor_revision_ordinal + 1
            or source.payload.get("traj_label") != contribution["traj_label"]
            or source.payload.get("traj_last_classify_step") != contribution["traj_last_classify_step"]
        ):
            raise SubstrateInvariantViolation("native world materialized successor is not exact current truth")
        with self._process_state.locked_scope(
            core_id=self._core_id, namespace=self._namespace
        ) as scope:
            if scope is None:
                raise SubstrateInvariantViolation("native world runtime is not initialized")
            self._assert_current(scope, snapshots)
            entry = scope.entries.get(eid)
            if entry is None:
                raise SubstrateInvariantViolation("native world materialized entity is absent")
            diagnostic = entry.diagnostic
            if diagnostic is None:
                return
            candidate = WorldDiagnosticSuccessorMaterialization.create(
                predecessor_revision_id=diagnostic.revision_id,
                predecessor_revision_ordinal=diagnostic.revision_ordinal,
                traj_label=diagnostic.traj_label,
                traj_last_classify_step=diagnostic.traj_last_classify_step,
            )
            if candidate.canonical_digest != materialization.canonical_digest:
                raise SubstrateInvariantViolation("native world overlay differs from durable materialization intent")
            entry.diagnostic = None

    def snapshot_for_testing(self) -> NativeWorldRuntimeSnapshot:
        """Return a detached diagnostic snapshot without exposing live entities."""
        with self._process_state.locked_scope(
            core_id=self._core_id, namespace=self._namespace
        ) as scope:
            if scope is None:
                return NativeWorldRuntimeSnapshot((), (), (), (), (), (), (), ())
            entries = tuple(scope.entries.values())
            return NativeWorldRuntimeSnapshot(
                tuple(entry.entity.eid for entry in entries),
                tuple(tuple(float(value) for value in entry.entity.pos) for entry in entries),
                tuple(tuple(float(value) for value in entry.entity.vel) for entry in entries),
                tuple(len(entry.entity.trail) for entry in entries),
                tuple(len(entry.entity.r_history) for entry in entries),
                tuple(entry.entity.born_step for entry in entries),
                tuple(entry.entity.channel for entry in entries),
                tuple(
                    None if entry.diagnostic is None else (
                        entry.diagnostic.traj_label,
                        entry.diagnostic.traj_last_classify_step,
                    )
                    for entry in entries
                ),
            )

    def _snapshots(self) -> tuple[LegacyMemoryView, ...]:
        ordered = self._enumeration.list_current()
        sources: list[LegacyMemoryView] = []
        for view in ordered:
            try:
                source = self._reads.get_memory_by_eid(
                    legacy_source_namespace_id=self._namespace, eid=view.eid,
                )
            except SubstrateObjectNotFound as exc:
                raise SubstrateInvariantViolation("native world enumeration memory disappeared") from exc
            sources.append(source)
        return tuple(sources)

    @staticmethod
    def _assert_topology(scope: _WorldScope, snapshots: tuple[LegacyMemoryView, ...]) -> None:
        if tuple(scope.entries) != tuple(source.eid for source in snapshots):
            raise SubstrateInvariantViolation("native world memory topology changed unexpectedly")
        for source in snapshots:
            entry = scope.entries.get(source.eid)
            if entry is None or entry.object_id != source.object_id:
                raise SubstrateInvariantViolation("native world memory identity changed unexpectedly")

    def _assert_current(self, scope: _WorldScope, snapshots: tuple[LegacyMemoryView, ...]) -> None:
        self._assert_topology(scope, snapshots)
        for source in snapshots:
            entry = scope.entries[source.eid]
            if (
                entry.revision_id != source.revision_id
                or entry.revision_ordinal != source.revision_ordinal
            ):
                raise SubstrateInvariantViolation("native world current revision changed outside qualified synchronization")


def _entity_from_source(
    source: LegacyMemoryView,
    *,
    born_step: int | None,
    channel: int | None,
    fresh: bool,
) -> NativeWorldEntity:
    payload = dict(source.payload)
    entity = NativeWorldEntity(
        eid=source.eid,
        born_step=born_step,
        channel=channel,
        pos=_payload_vec3(payload, "pos", fallback="seed_pos0"),
        vel=_payload_vec3(payload, "vel", fallback="seed_v0"),
        vel0=_payload_vec3(payload, "vel0", fallback="vel"),
        payload=payload,
        # ``SeedWorld.spawn`` always creates a live entity.  The payload
        # ``alive`` key governs only legacy reload, not a fresh birth.
        alive=True if fresh else bool(payload.get("alive", True)),
    )
    if fresh:
        _append_genesis_diagnostics(entity, trail_len=200)
    return entity


def _append_genesis_diagnostics(entity: NativeWorldEntity, *, trail_len: int) -> None:
    entity.r_history.append(float(np.sqrt(entity.pos[0] ** 2 + entity.pos[1] ** 2)))
    entity.z_history.append(float(entity.pos[2]))
    entity.x_history.append(float(entity.pos[0]))
    entity.y_history.append(float(entity.pos[1]))
    entity.push_trail(trail_len)


def _payload_vec3(payload: Mapping[str, Any], key: str, *, fallback: str) -> np.ndarray:
    value = payload.get(key, payload.get(fallback, np.zeros(3)))
    try:
        return np.asarray(value, dtype=float).reshape(3)
    except (TypeError, ValueError) as exc:
        raise SubstrateInvariantViolation(
            f"native world payload field {key!r} is not an exact reloadable vec3"
        ) from exc


def _source_for_eid(snapshots: tuple[LegacyMemoryView, ...], eid: int) -> LegacyMemoryView:
    matches = tuple(source for source in snapshots if source.eid == eid)
    if len(matches) != 1:
        raise SubstrateInvariantViolation("native world EID is absent or ambiguous")
    return matches[0]


def _diagnostic_digest(
    predecessor_revision_id: UUID,
    predecessor_revision_ordinal: int,
    traj_label: str,
    traj_last_classify_step: int,
) -> str:
    return hashlib.sha256(canonical_intent_text({
        "predecessor_revision_id": str(predecessor_revision_id),
        "predecessor_revision_ordinal": predecessor_revision_ordinal,
        "traj_label": traj_label,
        "traj_last_classify_step": traj_last_classify_step,
    }).encode("utf-8")).hexdigest()


__all__ = [
    "NativeWorldProcessState",
    "NativeWorldRuntime",
    "NativeWorldRuntimeSnapshot",
    "WorldDiagnosticSuccessorMaterialization",
]
