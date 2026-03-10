# torment_service/phase_timer.py
"""
Phase-Cycle Time — TORMENT duration-aware memory tracking.

The kernel tracks corridor state as snapshots (in_corridor, cycle_stage,
survival_steps EMA). But EMA is a decaying proxy — it doesn't tell you
how many steps the character has been sitting in this state.

PhaseTimer provides explicit step-counting:
    - phase_duration_steps: how long since the last cycle_stage change
    - corridor_duration_steps: how long since corridor entry (0 if not in corridor)

These durations feed into:
    - Compression: sustained memories resist compression
    - Spirit return: sustained memories return warmer (more vivid)
    - Scoring: phase duration as an importance signal

PhaseTimer lives in the fabric layer (per-agent), NOT in the kernel.
The kernel's process() doesn't take a step parameter and we don't
want to change that foundational API.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PhaseTimer:
    """Per-agent phase and corridor duration tracker.

    Updated once per ingest step. Resets on phase transition
    (cycle_stage change) or corridor exit.
    """

    phase_entry_step: int = 0
    corridor_entry_step: Optional[int] = None
    current_cycle_stage: Optional[int] = None
    current_in_corridor: bool = False

    def update(
        self,
        step: int,
        in_corridor: bool,
        cycle_stage: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call once per ingest step. Returns transition info.

        Args:
            step: current ingest step number
            in_corridor: whether the kernel is currently in a corridor
            cycle_stage: current kernel cycle stage (0-11), or None

        Returns:
            Dict with transition events:
                phase_changed: True if cycle_stage changed
                prev_phase_duration: duration of the phase that just ended
                corridor_entered: True if just entered corridor
                corridor_exited: True if just exited corridor
                prev_corridor_duration: duration of the corridor that just ended
        """
        transitions: Dict[str, Any] = {}
        step = int(step)

        # --- Phase tracking ---
        if cycle_stage is not None:
            cycle_stage = int(cycle_stage)

            if self.current_cycle_stage is None:
                # First call: initialize baseline
                self.phase_entry_step = step
            elif cycle_stage != self.current_cycle_stage:
                # Phase transition
                transitions["phase_changed"] = True
                transitions["prev_phase_duration"] = step - self.phase_entry_step
                self.phase_entry_step = step

            self.current_cycle_stage = cycle_stage

        # --- Corridor tracking ---
        if in_corridor and not self.current_in_corridor:
            # Corridor entry
            self.corridor_entry_step = step
            transitions["corridor_entered"] = True

        elif not in_corridor and self.current_in_corridor:
            # Corridor exit
            if self.corridor_entry_step is not None:
                transitions["corridor_exited"] = True
                transitions["prev_corridor_duration"] = step - self.corridor_entry_step
            self.corridor_entry_step = None

        self.current_in_corridor = in_corridor
        return transitions

    def get_durations(self, current_step: int) -> Dict[str, int]:
        """Snapshot of current phase and corridor durations.

        Args:
            current_step: the current ingest step

        Returns:
            {
                "phase_duration_steps": int,
                "corridor_duration_steps": int,
            }
        """
        current_step = int(current_step)
        phase_dur = max(0, current_step - self.phase_entry_step)
        corridor_dur = 0
        if self.corridor_entry_step is not None:
            corridor_dur = max(0, current_step - self.corridor_entry_step)
        return {
            "phase_duration_steps": phase_dur,
            "corridor_duration_steps": corridor_dur,
        }

    def state_dict(self) -> Dict[str, Any]:
        """Serialize for checkpointing."""
        return {
            "phase_entry_step": self.phase_entry_step,
            "corridor_entry_step": self.corridor_entry_step,
            "current_cycle_stage": self.current_cycle_stage,
            "current_in_corridor": self.current_in_corridor,
        }

    @classmethod
    def from_state_dict(cls, d: dict) -> "PhaseTimer":
        """Restore from checkpoint."""
        return cls(
            phase_entry_step=int(d.get("phase_entry_step", 0) or 0),
            corridor_entry_step=(
                int(d["corridor_entry_step"])
                if d.get("corridor_entry_step") is not None
                else None
            ),
            current_cycle_stage=(
                int(d["current_cycle_stage"])
                if d.get("current_cycle_stage") is not None
                else None
            ),
            current_in_corridor=bool(d.get("current_in_corridor", False)),
        )
