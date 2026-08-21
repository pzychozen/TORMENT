"""Phase-3 deterministic accounting for Brainvision-owned active visual time.

This module is an isolated clock primitive.  It contains no lifecycle,
configuration, persistence, observation admission, VHE, or runtime wiring.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Final


VISUAL_TIME_NS_PER_SECOND: Final = 1_000_000_000
T_PRODUCT_V1_SECONDS: Final = 300.0
T_PRODUCT_V1_NS: Final = 300_000_000_000

MonotonicNsSource = Callable[[], int]


class VisualClockError(RuntimeError):
    """Base error for deterministic visual-clock state failures."""

    def __init__(self, field: str, reason: str, detail: str | None = None) -> None:
        self.field = field
        self.reason = reason
        self.detail = detail
        message = f"{field}: {reason}"
        if detail is not None:
            message = f"{message} ({detail})"
        super().__init__(message)


class ClockValueError(VisualClockError, ValueError):
    """An exact-integer clock input or source value was invalid."""


class ClockRegressionError(VisualClockError):
    """The injected monotonic source moved before the bound process origin."""


class ClockStateError(VisualClockError):
    """A primitive was requested in an incompatible accumulation state."""


def _require_nonnegative_exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise ClockValueError(field, "must_be_exact_int")
    if value < 0:
        raise ClockValueError(field, "must_be_nonnegative")
    return value


def _require_exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise ClockValueError(field, "must_be_exact_int")
    return value


@dataclass(kw_only=True, init=False)
class VisualClock:
    """Committed active time plus an optional process-local monotonic origin.

    ``process_local_origin_ns is None`` means the clock is frozen.  Origins are
    process-local values and are deliberately not a persistence representation.
    """

    committed_active_time_ns: int

    def __init__(
        self,
        *,
        committed_active_time_ns: int,
        process_local_origin_ns: int | None,
        monotonic_ns_source: MonotonicNsSource,
    ) -> None:
        _require_nonnegative_exact_int(
            committed_active_time_ns,
            "committed_active_time_ns",
        )
        if process_local_origin_ns is not None:
            _require_exact_int(process_local_origin_ns, "process_local_origin_ns")
        if not callable(monotonic_ns_source):
            raise ClockValueError("monotonic_ns_source", "must_be_callable")
        self.committed_active_time_ns = committed_active_time_ns
        self._process_local_origin_ns = process_local_origin_ns
        self._monotonic_ns_source = monotonic_ns_source

    @property
    def process_local_origin_ns(self) -> int | None:
        """Expose the local origin for runtime inspection without serialization."""
        return self._process_local_origin_ns

    @classmethod
    def from_active(
        cls,
        *,
        committed_active_time_ns: int = 0,
        monotonic_ns_source: MonotonicNsSource = time.monotonic_ns,
    ) -> "VisualClock":
        """Start a fresh active accumulation period at a new local origin."""
        _require_nonnegative_exact_int(
            committed_active_time_ns,
            "committed_active_time_ns",
        )
        if not callable(monotonic_ns_source):
            raise ClockValueError("monotonic_ns_source", "must_be_callable")
        origin = _require_exact_int(monotonic_ns_source(), "monotonic_ns_source result")
        return cls(
            committed_active_time_ns=committed_active_time_ns,
            process_local_origin_ns=origin,
            monotonic_ns_source=monotonic_ns_source,
        )

    @classmethod
    def from_frozen(
        cls,
        *,
        committed_active_time_ns: int = 0,
        monotonic_ns_source: MonotonicNsSource = time.monotonic_ns,
    ) -> "VisualClock":
        """Construct a frozen clock without sampling the monotonic source."""
        return cls(
            committed_active_time_ns=committed_active_time_ns,
            process_local_origin_ns=None,
            monotonic_ns_source=monotonic_ns_source,
        )

    @property
    def is_accumulating(self) -> bool:
        """Whether active visual time is currently accumulating."""
        return self.process_local_origin_ns is not None

    def _now_after_origin(self) -> int:
        """Read an exact source value and reject a process-origin regression."""
        if self._process_local_origin_ns is None:
            raise ClockStateError("process_local_origin_ns", "clock_is_frozen")
        now = _require_exact_int(self._monotonic_ns_source(), "monotonic_ns_source result")
        if now < self._process_local_origin_ns:
            raise ClockRegressionError(
                "monotonic_ns_source result",
                "earlier_than_process_local_origin",
            )
        return now

    def read_active_time_ns(self) -> int:
        """Return current visual time without mutating committed state or origin."""
        if self._process_local_origin_ns is None:
            return self.committed_active_time_ns
        return self.committed_active_time_ns + (
            self._now_after_origin() - self._process_local_origin_ns
        )

    def resolve_and_rebase(self) -> int:
        """Commit current active elapsed time and bind a fresh local origin."""
        now = self._now_after_origin()
        self.committed_active_time_ns += now - self._process_local_origin_ns
        self._process_local_origin_ns = now
        return self.committed_active_time_ns

    def freeze(self) -> int:
        """Resolve active time once and then stop accumulation."""
        if self._process_local_origin_ns is not None:
            self.resolve_and_rebase()
            self._process_local_origin_ns = None
        return self.committed_active_time_ns

    def resume(self) -> None:
        """Begin a new local accumulation period without adding frozen downtime."""
        if self._process_local_origin_ns is not None:
            raise ClockStateError("process_local_origin_ns", "clock_is_already_accumulating")
        self._process_local_origin_ns = _require_exact_int(
            self._monotonic_ns_source(),
            "monotonic_ns_source result",
        )

    def reset(self) -> None:
        """Set committed visual time to zero, preserving frozen versus active mode."""
        if self._process_local_origin_ns is None:
            self.committed_active_time_ns = 0
            return
        now = self._now_after_origin()
        self.committed_active_time_ns = 0
        self._process_local_origin_ns = now


__all__ = (
    "ClockRegressionError",
    "ClockStateError",
    "ClockValueError",
    "MonotonicNsSource",
    "T_PRODUCT_V1_NS",
    "T_PRODUCT_V1_SECONDS",
    "VISUAL_TIME_NS_PER_SECOND",
    "VisualClock",
    "VisualClockError",
)
