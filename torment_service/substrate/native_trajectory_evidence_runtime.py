"""External trajectory evidence for an already source-bound native world.

This module deliberately owns no SQLite connection, native identifier mapping,
or world mathematics.  It serializes the current process-local world entities
using the same two legacy artifact formats selected by ``MemoryGraph``.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import time
import threading
from typing import Any, Iterable
from uuid import UUID

from torment_service.kernel.trajectory_logging import TrajectoryLogger
from torment_service.kernel.trajectory_v2 import TrajectoryV2Writer


log = logging.getLogger("torment.substrate.native_trajectory_evidence")


def resolve_trajectory_format(requested: str | None = None) -> str:
    """Apply the existing ``MemoryGraph`` format-selection law exactly."""
    value = os.getenv("TORMENT_TRAJECTORY_FORMAT", "v2") if requested is None else requested
    normalized = str(value).strip().lower()
    return normalized if normalized in {"legacy", "v2"} else "legacy"


class NativeTrajectoryEvidenceRuntime:
    """Fail-soft writer for one externally owned, domain-scoped artifact root."""

    def __init__(self, *, root_dir: str, trajectory_format: str | None = None) -> None:
        if not isinstance(root_dir, str) or not root_dir:
            raise ValueError("root_dir must be non-empty text")
        self.root_dir = Path(root_dir).resolve()
        self.trajectory_format = resolve_trajectory_format(trajectory_format)
        # Preserve the legacy V2 reset-boundary facts whenever a frame is
        # actually emitted. Native has no qualified kinematic-reset writer,
        # so these facts are retained only by this external evidence owner.
        self._last_observed_step: int | None = None
        self._last_observed_frame_seq: int | None = None
        if self.trajectory_format == "v2":
            self._writer: TrajectoryV2Writer | TrajectoryLogger = TrajectoryV2Writer(str(self.root_dir))
        else:
            self._writer = TrajectoryLogger(str(self.root_dir))

    def write_genesis(self, entity: Any) -> None:
        """Write V2 birth evidence at the legacy creation boundary, if selected."""
        if self.trajectory_format != "v2":
            return
        try:
            result = self._writer.write_genesis(entity)  # type: ignore[union-attr]
            if not result.ok:
                log.debug("Trajectory V2 genesis incomplete: %s", result.detail)
        except Exception as exc:
            log.debug("Trajectory genesis skipped: %s", exc)

    def write_step(self, entities: Iterable[Any], *, step: int) -> None:
        """Write one post-physics snapshot without affecting its source world."""
        live = tuple(
            entity for entity in entities
            if entity is not None and getattr(entity, "alive", True)
        )
        if self.trajectory_format == "v2":
            try:
                result = self._writer.write_step(live, step=int(step))  # type: ignore[union-attr]
                if not result.ok:
                    log.debug("Trajectory V2 step incomplete: %s", result.detail)
                else:
                    self._last_observed_step = int(step)
                    self._last_observed_frame_seq = result.frame_seq
            except Exception as exc:
                log.debug("Trajectory V2 log skipped: %s", exc)
            return
        for entity in live:
            try:
                self._writer.log_entity(entity, step=int(step))  # type: ignore[union-attr]
            except Exception as exc:
                log.debug("Trajectory log skipped: %s", exc)

    def write_classification_event(self, entity: Any, *, step: int, label: str) -> None:
        """Append the existing non-authoritative classification event record."""
        try:
            event_path = (self.root_dir / "memory_events.jsonl").resolve()
            if event_path.parent != self.root_dir:
                raise ValueError(f"trajectory event path escapes data root: {event_path!s}")
            with event_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "type": "TRAJ_CLASSIFY",
                    "ts": int(time.time()),
                    "step": int(step),
                    "eid": int(getattr(entity, "eid")),
                    "traj_label": str(label),
                }, ensure_ascii=False) + "\n")
        except Exception as exc:
            log.debug("Traj classify event write skipped: %s", exc)

    def close(self) -> None:
        """Seal only the selected V2 tail; all close failures remain diagnostic."""
        if self.trajectory_format != "v2":
            return
        try:
            result = self._writer.close()  # type: ignore[union-attr]
            if not result.ok:
                log.debug("Trajectory V2 close incomplete: %s", result.detail)
        except Exception as exc:
            log.debug("Trajectory V2 close skipped: %s", exc)

    def reset_boundary_facts_for_testing(self) -> tuple[int | None, int | None]:
        """Expose retained V2 reset facts without adding a native reset owner."""
        return self._last_observed_step, self._last_observed_frame_seq


class NativePrivateTrajectoryEvidenceProcessState:
    """One external private trajectory writer for one native process owner.

    The exact key matches the process-local world owner: native core plus the
    qualified private source namespace. It retains no SQLite connection or
    canonical-memory authority. A production owner closes it at owner shutdown;
    request-scoped post-write adapters must not close it.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._runtimes: dict[tuple[UUID, UUID], tuple[Path, str, NativeTrajectoryEvidenceRuntime]] = {}

    def acquire(
        self,
        *,
        core_id: UUID,
        legacy_source_namespace_id: UUID,
        root_dir: str,
        trajectory_format: str,
    ) -> NativeTrajectoryEvidenceRuntime:
        if not isinstance(core_id, UUID) or not isinstance(legacy_source_namespace_id, UUID):
            raise ValueError("private trajectory process identity must use native UUID facts")
        root = Path(root_dir).resolve()
        selected_format = resolve_trajectory_format(trajectory_format)
        key = (core_id, legacy_source_namespace_id)
        with self._lock:
            existing = self._runtimes.get(key)
            if existing is not None:
                existing_root, existing_format, runtime = existing
                if existing_root != root or existing_format != selected_format:
                    raise ValueError("private trajectory process owner disagrees with its qualified external binding")
                return runtime
            runtime = NativeTrajectoryEvidenceRuntime(
                root_dir=str(root), trajectory_format=selected_format,
            )
            self._runtimes[key] = (root, selected_format, runtime)
            return runtime

    def runtime_for_testing(
        self,
        *,
        core_id: UUID,
        legacy_source_namespace_id: UUID,
    ) -> NativeTrajectoryEvidenceRuntime | None:
        """Return an identity-only test observation; it grants no write path."""
        with self._lock:
            item = self._runtimes.get((core_id, legacy_source_namespace_id))
            return None if item is None else item[2]

    def close(self) -> None:
        """Seal every private writer when its containing process owner closes."""
        with self._lock:
            runtimes = tuple(item[2] for item in self._runtimes.values())
            self._runtimes.clear()
        for runtime in runtimes:
            runtime.close()


__all__ = [
    "NativePrivateTrajectoryEvidenceProcessState",
    "NativeTrajectoryEvidenceRuntime",
    "resolve_trajectory_format",
]
