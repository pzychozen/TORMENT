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
from typing import Any, Iterable

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


__all__ = [
    "NativeTrajectoryEvidenceRuntime",
    "resolve_trajectory_format",
]
