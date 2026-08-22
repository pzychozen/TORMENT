"""Exact schedule-driven clock used only by the Phase-13 instrument."""

from __future__ import annotations

from dataclasses import dataclass


def _require_ns(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{field} must be a nonnegative exact int")
    return value


@dataclass
class QualificationClock:
    """A monotonic source whose value changes only by explicit harness action."""

    _now_ns: int = 0

    def __post_init__(self) -> None:
        self._now_ns = _require_ns(self._now_ns, "initial_ns")

    def __call__(self) -> int:
        """Return the current exact time without changing it."""
        return self._now_ns

    def set_ns(self, value: int) -> None:
        """Set a future exact schedule point."""
        value = _require_ns(value, "value")
        if value < self._now_ns:
            raise ValueError("qualification clock cannot move backward")
        self._now_ns = value

    def advance_ns(self, delta: int) -> None:
        """Advance by one exact nonnegative scheduled interval."""
        self._now_ns += _require_ns(delta, "delta")


__all__ = ("QualificationClock",)
