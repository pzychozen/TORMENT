# trajectory_logging.py
from __future__ import annotations

import json, os, time
from typing import Any, Dict
import numpy as np

from ..pathing import dated_log_path, stable_filename


def _now_ts() -> int:
    return int(time.time())

class TrajectoryLogger:
    """Lightweight append-only trajectory logger.

    Writes per-step kinematics snapshots to daily-rotated JSONL files
    under ``logs/trajectories/daily/YYYY-MM-DD.jsonl``.

    When *use_daily_rotation* is ``True`` (the default), each call to
    ``log_entity`` writes to today's dated log file.  This prevents a
    single ``trajectories.jsonl`` from growing without bound and keeps
    the root directory clean.

    Set *use_daily_rotation* to ``False`` to fall back to the legacy
    single-file behaviour (useful for existing tests).
    """

    def __init__(
        self,
        root_dir: str,
        filename: str = "trajectories.jsonl",
        *,
        use_daily_rotation: bool = True,
    ) -> None:
        self.root_dir = os.path.realpath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)
        self._use_daily = use_daily_rotation
        # Legacy single-file path (used when daily rotation is off, or
        # as fallback for callers that read self.path directly).
        self.path = stable_filename(self.root_dir, filename)

    def _today_path(self) -> str:
        """Return today's dated log path, creating the directory if needed."""
        p = dated_log_path(self.root_dir, "trajectories")
        # Inline containment guard — CodeQL needs visible realpath+startswith
        rp = os.path.realpath(p)
        base = os.path.realpath(self.root_dir)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Dated log path escapes root: {rp!r}")
        os.makedirs(os.path.dirname(rp), exist_ok=True)
        return rp

    def log_entity(self, ent: Any, step: int) -> None:
        try:
            pos = np.asarray(getattr(ent, "pos", np.zeros(3)), dtype=float).reshape(3).tolist()
            vel = np.asarray(getattr(ent, "vel", np.zeros(3)), dtype=float).reshape(3).tolist()
            vel0 = np.asarray(getattr(ent, "vel0", vel), dtype=float).reshape(3).tolist()
        except Exception:
            return

        payload = getattr(ent, "payload", {}) or {}
        rec: Dict[str, Any] = {
            "ts": _now_ts(),
            "step": int(step),
            "eid": int(getattr(ent, "eid", -1)),
            "born_step": int(getattr(ent, "born_step", 0) or 0),
            "channel": int(getattr(ent, "channel", 0) or 0),
            "alive": bool(getattr(ent, "alive", True)),
            "pos": pos,
            "vel": vel,
            "vel0": vel0,
            # optional labels if you set them in payload
            "traj_label": payload.get("traj_label"),
            "traj_last_classify_step": payload.get("traj_last_classify_step"),
        }

        target = self._today_path() if self._use_daily else self.path
        # Inline containment guard at the sink
        safe_target = os.path.realpath(target)
        base = os.path.realpath(self.root_dir)
        if safe_target != base and not safe_target.startswith(base + os.sep):
            raise ValueError(f"Log path escapes root: {safe_target!r}")
        with open(safe_target, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")