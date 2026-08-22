"""Focused deterministic tests for the isolated Phase-3 visual clock."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, fields
import json
from pathlib import Path
import subprocess
import sys

import pytest

from brainvision.clock import (
    ClockRegressionError,
    ClockStateError,
    ClockValueError,
    T_PRODUCT_V1_NS,
    T_PRODUCT_V1_SECONDS,
    VISUAL_TIME_NS_PER_SECOND,
    VisualClock,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CLOCK_PATH = REPOSITORY_ROOT / "brainvision" / "clock.py"


@dataclass
class FakeMonotonicNsSource:
    now_ns: int
    calls: int = 0

    def __call__(self) -> int:
        self.calls += 1
        return self.now_ns

    def advance(self, elapsed_ns: int) -> None:
        self.now_ns += elapsed_ns


def _clock_state(clock: VisualClock) -> tuple[int, int | None]:
    return (clock.committed_active_time_ns, clock.process_local_origin_ns)


def test_product_identity_and_exact_nanosecond_constants() -> None:
    assert VISUAL_TIME_NS_PER_SECOND == 1_000_000_000
    assert T_PRODUCT_V1_SECONDS == 300.0
    assert T_PRODUCT_V1_NS == 300_000_000_000
    assert 300 * VISUAL_TIME_NS_PER_SECOND == T_PRODUCT_V1_NS


def test_dataclass_structural_state_contains_only_committed_active_time() -> None:
    source = FakeMonotonicNsSource(now_ns=10)
    clock = VisualClock.from_active(
        committed_active_time_ns=123,
        monotonic_ns_source=source,
    )
    assert tuple(field.name for field in fields(clock)) == ("committed_active_time_ns",)
    assert asdict(clock) == {"committed_active_time_ns": 123}
    assert "process_local_origin_ns" not in asdict(clock)
    assert "monotonic_ns_source" not in asdict(clock)
    assert clock.process_local_origin_ns == 10


def test_active_construction_binds_now_and_starts_at_committed_time() -> None:
    source = FakeMonotonicNsSource(now_ns=10_000)
    clock = VisualClock.from_active(
        committed_active_time_ns=123_456_789,
        monotonic_ns_source=source,
    )
    assert source.calls == 1
    assert _clock_state(clock) == (123_456_789, 10_000)
    assert clock.read_active_time_ns() == 123_456_789


def test_active_construction_accepts_an_explicit_runtime_only_origin() -> None:
    source = FakeMonotonicNsSource(now_ns=12_000_000_000)
    clock = VisualClock.from_active(
        committed_active_time_ns=1_000_000_000,
        monotonic_ns_source=source,
        process_local_origin_ns=11_000_000_000,
    )

    assert source.calls == 0
    assert _clock_state(clock) == (1_000_000_000, 11_000_000_000)
    assert clock.read_active_time_ns() == 2_000_000_000


def test_frozen_construction_and_reads_ignore_source_movement() -> None:
    source = FakeMonotonicNsSource(now_ns=10)
    clock = VisualClock.from_frozen(
        committed_active_time_ns=123_456_789,
        monotonic_ns_source=source,
    )
    assert source.calls == 0
    source.advance(999_999)
    assert clock.read_active_time_ns() == 123_456_789
    assert source.calls == 0


def test_active_read_uses_exact_injected_elapsed_nanoseconds_and_is_pure() -> None:
    source = FakeMonotonicNsSource(now_ns=1_000)
    clock = VisualClock.from_active(monotonic_ns_source=source)
    source.advance(123_456_789)
    before = _clock_state(clock)
    assert clock.read_active_time_ns() == 123_456_789
    assert _clock_state(clock) == before
    assert clock.read_active_time_ns() == 123_456_789
    assert _clock_state(clock) == before


def test_resolve_and_rebase_commits_exactly_once() -> None:
    source = FakeMonotonicNsSource(now_ns=1_000)
    clock = VisualClock.from_active(
        committed_active_time_ns=10,
        monotonic_ns_source=source,
    )
    source.advance(77)
    assert clock.resolve_and_rebase() == 87
    assert _clock_state(clock) == (87, 1_077)
    assert clock.resolve_and_rebase() == 87
    assert _clock_state(clock) == (87, 1_077)


def test_freeze_resolves_elapsed_time_and_resume_ignores_frozen_duration() -> None:
    source = FakeMonotonicNsSource(now_ns=10)
    clock = VisualClock.from_active(monotonic_ns_source=source)
    source.advance(25)
    assert clock.freeze() == 25
    assert _clock_state(clock) == (25, None)
    source.advance(1_000_000)
    assert clock.read_active_time_ns() == 25
    clock.resume()
    assert _clock_state(clock) == (25, 1_000_035)
    source.advance(12)
    assert clock.read_active_time_ns() == 37


def test_resume_while_active_is_rejected_without_rebase() -> None:
    source = FakeMonotonicNsSource(now_ns=10)
    clock = VisualClock.from_active(monotonic_ns_source=source)
    with pytest.raises(ClockStateError) as failure:
        clock.resume()
    assert failure.value.reason == "clock_is_already_accumulating"
    assert _clock_state(clock) == (0, 10)


def test_active_reset_sets_zero_and_rebinds_origin() -> None:
    source = FakeMonotonicNsSource(now_ns=10)
    clock = VisualClock.from_active(
        committed_active_time_ns=99,
        monotonic_ns_source=source,
    )
    source.advance(45)
    clock.reset()
    assert _clock_state(clock) == (0, 55)
    assert clock.read_active_time_ns() == 0
    source.advance(8)
    assert clock.read_active_time_ns() == 8


def test_frozen_reset_sets_zero_and_remains_frozen() -> None:
    source = FakeMonotonicNsSource(now_ns=10)
    clock = VisualClock.from_frozen(
        committed_active_time_ns=99,
        monotonic_ns_source=source,
    )
    clock.reset()
    assert _clock_state(clock) == (0, None)
    source.advance(1_000)
    assert clock.read_active_time_ns() == 0
    assert source.calls == 0


def test_process_reload_excludes_downtime() -> None:
    old_source = FakeMonotonicNsSource(now_ns=100)
    old_clock = VisualClock.from_active(monotonic_ns_source=old_source)
    old_source.advance(50)
    committed = old_clock.resolve_and_rebase()
    assert committed == 50

    new_source = FakeMonotonicNsSource(now_ns=9_000_000)
    new_clock = VisualClock.from_active(
        committed_active_time_ns=committed,
        monotonic_ns_source=new_source,
    )
    assert new_clock.read_active_time_ns() == 50
    new_source.advance(17)
    assert new_clock.read_active_time_ns() == 67


def test_source_regression_is_a_hard_failure() -> None:
    source = FakeMonotonicNsSource(now_ns=100)
    clock = VisualClock.from_active(monotonic_ns_source=source)
    source.now_ns = 99
    with pytest.raises(ClockRegressionError) as failure:
        clock.read_active_time_ns()
    assert failure.value.reason == "earlier_than_process_local_origin"
    assert _clock_state(clock) == (0, 100)


@pytest.mark.parametrize("value", [True, -1, 1.0, "0"])
def test_invalid_committed_time_is_rejected(value: object) -> None:
    source = FakeMonotonicNsSource(now_ns=0)
    with pytest.raises(ClockValueError):
        VisualClock.from_active(  # type: ignore[arg-type]
            committed_active_time_ns=value,
            monotonic_ns_source=source,
        )


@pytest.mark.parametrize("source_value", [True, 1.0, "1"])
def test_non_integer_source_values_are_rejected(source_value: object) -> None:
    def invalid_source() -> object:
        return source_value

    with pytest.raises(ClockValueError) as failure:
        VisualClock.from_active(monotonic_ns_source=invalid_source)  # type: ignore[arg-type]
    assert failure.value.field == "monotonic_ns_source result"


def test_clock_has_no_wall_clock_capture_time_persistence_or_runtime_dependency() -> None:
    tree = ast.parse(CLOCK_PATH.read_text(encoding="utf-8"), filename=str(CLOCK_PATH))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert {name.lstrip(".") for name in imports} <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "time",
        "typing",
    }

    attribute_names = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }
    assert "monotonic_ns" in attribute_names
    assert "time" not in attribute_names
    assert "open" not in attribute_names


def test_clock_import_is_deterministic_and_isolated() -> None:
    code = """
import json
import sys
import brainvision.clock
print(json.dumps(sorted(sys.modules)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    loaded = json.loads(completed.stdout)
    prohibited_prefixes = (
        "research.brainvision",
        "torment_service",
        "cognition",
        "memory",
        "kernel",
        "srg",
        "hivermind",
    )
    assert not any(name.startswith(prohibited_prefixes) for name in loaded)
