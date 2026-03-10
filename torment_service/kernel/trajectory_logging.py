# trajectory_logging.py
from __future__ import annotations

import os, json, time
from typing import Any, Dict, Optional
import numpy as np


def _now_ts() -> int:
    return int(time.time())

class TrajectoryLogger:
    """
    Lightweight append-only trajectory logger.
    Writes per-step kinematics snapshots to trajectories.jsonl.

    This is intentionally simple:
      - No heavy aggregation
      - No coupling back into the kernel
      - Just persistent telemetry for later analysis/plots
    """
    def __init__(self, root_dir: str, filename: str = "trajectories.jsonl") -> None:
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)
        self.path = os.path.join(self.root_dir, filename)

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

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")