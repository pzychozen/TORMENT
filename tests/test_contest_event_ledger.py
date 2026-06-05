"""tests/test_contest_event_ledger.py

B2-S4 replay tests for the Track B v0.2 ContestEventLedger: append-only
counter-contest event storage and literal full-file replay only.

Pure storage truth. The reader is literal and observational: append order is
chronology only (never precedence), there is no derived status, no latest-wins,
no count-as-signal, and no target-existence lookup. Dangling linkage remains
representable, never resolved. Counter-contest result routing,
candidate_handle binding, effective authority, and retrieval/prompt/cognition/
MCP are all parked.

``CounterContestEvent`` / ``ContestEventLedger`` are provisional working names.
"""
from __future__ import annotations

import json
import uuid

import pytest

from torment_service.contest_event_ledger import (
    ContestEventLedger,
    ContestEventLedgerError,
)
from torment_service.counter_contest_event import (
    CounterContestEvent,
    CounterContestEventError,
)
from torment_service.contest_record import ContestActor, ContestReasonClass
from torment_service.provenance_v1 import ProvenanceV1


# ── helpers ─────────────────────────────────────────────────────────


def _prov() -> ProvenanceV1:
    return ProvenanceV1.for_user_ingest(step=3, session_id="sess-1")


def _event(event_id: str = None, target_contest_id: str = None, **over) -> CounterContestEvent:
    base = dict(
        event_id=event_id or str(uuid.uuid4()),
        target_contest_id=target_contest_id or str(uuid.uuid4()),
        contestant_actor=ContestActor.AGENT,
        contestant_id="agent-7",
        reason_class=ContestReasonClass.MATERIAL_DISAGREEMENT,
        event_provenance=_prov(),
    )
    base.update(over)
    return CounterContestEvent(**base)


def _ledger(tmp_path) -> ContestEventLedger:
    return ContestEventLedger(str(tmp_path), "ws1")


# ── path ─────────────────────────────────────────────────────────────


def test_workspace_scoped_contest_events_path(tmp_path):
    led = _ledger(tmp_path)
    assert led.path.endswith("contest_events.jsonl")
    assert "contest_memory" in led.path.replace("\\", "/")
    assert "ws1" in led.path.replace("\\", "/")


# ── append + literal read ───────────────────────────────────────────


def test_append_one_event(tmp_path):
    led = _ledger(tmp_path)
    ev = _event()
    led.append_event(ev)
    got = led.list_events()
    assert len(got) == 1
    assert got[0] == ev


def test_append_multiple_events(tmp_path):
    led = _ledger(tmp_path)
    evs = [_event(contestant_id=f"agent-{i}") for i in range(3)]
    for e in evs:
        led.append_event(e)
    assert led.list_events() == evs


def test_literal_read_preserves_append_order(tmp_path):
    led = _ledger(tmp_path)
    evs = [_event(contestant_id=f"agent-{i}") for i in range(5)]
    for e in evs:
        led.append_event(e)
    got = led.list_events()
    assert [e.contestant_id for e in got] == [f"agent-{i}" for i in range(5)]


def test_persisted_event_round_trips_exactly(tmp_path):
    led = _ledger(tmp_path)
    ev = _event(
        contestant_actor=ContestActor.OPERATOR,
        reason_class=ContestReasonClass.IDENTITY_CONFLICT,
    )
    led.append_event(ev)
    (got,) = led.list_events()
    assert got == ev


def test_nested_provenance_survives_round_trip(tmp_path):
    led = _ledger(tmp_path)
    ev = _event()
    led.append_event(ev)
    (got,) = led.list_events()
    assert isinstance(got.event_provenance, ProvenanceV1)
    assert got.event_provenance == ev.event_provenance


# ── writer boundary ─────────────────────────────────────────────────


def test_append_rejects_raw_dict(tmp_path):
    led = _ledger(tmp_path)
    with pytest.raises(TypeError):
        led.append_event(_event().to_dict())  # type: ignore[arg-type]
    # Nothing was written.
    assert led.list_events() == []


# ── empty / missing ─────────────────────────────────────────────────


def test_empty_ledger_returns_empty_list(tmp_path):
    led = _ledger(tmp_path)
    assert led.list_events() == []


def test_missing_file_returns_empty_list(tmp_path):
    led = ContestEventLedger(str(tmp_path), "never-written-ws")
    assert led.list_events() == []


def test_blank_lines_are_skipped(tmp_path):
    led = _ledger(tmp_path)
    led.append_event(_event())
    with open(led.path, "a", encoding="utf-8") as f:
        f.write("\n   \n")
    assert len(led.list_events()) == 1


# ── linkage filter (literal, chronology only) ───────────────────────


def test_list_events_for_contest_filters_literal_matches(tmp_path):
    led = _ledger(tmp_path)
    target = str(uuid.uuid4())
    other = str(uuid.uuid4())
    led.append_event(_event(target_contest_id=target, contestant_id="a"))
    led.append_event(_event(target_contest_id=other, contestant_id="b"))
    led.append_event(_event(target_contest_id=target, contestant_id="c"))
    got = led.list_events_for_contest(target)
    assert [e.contestant_id for e in got] == ["a", "c"]


def test_list_events_for_contest_preserves_append_order(tmp_path):
    led = _ledger(tmp_path)
    target = str(uuid.uuid4())
    for i in range(4):
        led.append_event(_event(target_contest_id=target, contestant_id=f"a{i}"))
    got = led.list_events_for_contest(target)
    assert [e.contestant_id for e in got] == [f"a{i}" for i in range(4)]


def test_structurally_valid_dangling_target_linkage_remains_representable(tmp_path):
    # A counter-contest may target a structurally valid contest_id that matches
    # no ContestRecord. The event is stored and read back literally; no
    # existence check, no resolution, no error — dangling linkage is history,
    # not a verdict.
    led = _ledger(tmp_path)
    dangling = str(uuid.uuid4())
    led.append_event(_event(target_contest_id=dangling))
    got = led.list_events_for_contest(dangling)
    assert len(got) == 1
    assert got[0].target_contest_id == dangling


def test_list_events_for_contest_unknown_target_returns_empty(tmp_path):
    led = _ledger(tmp_path)
    led.append_event(_event())  # different random target
    assert led.list_events_for_contest(str(uuid.uuid4())) == []


def test_list_events_for_contest_validates_query_uuid_shape(tmp_path):
    # The query argument is shape-validated (NOT existence-validated).
    led = _ledger(tmp_path)
    with pytest.raises(ContestEventLedgerError) as e:
        led.list_events_for_contest("not-a-uuid")
    assert e.value.reason == "bad_target_contest_id"


# ── fail-closed read posture ────────────────────────────────────────


def test_malformed_jsonl_line_raises_loudly(tmp_path):
    led = _ledger(tmp_path)
    led.append_event(_event())
    with open(led.path, "a", encoding="utf-8") as f:
        f.write("{ this is not valid json\n")
    with pytest.raises(ContestEventLedgerError) as e:
        led.list_events()
    assert e.value.reason == "malformed_line"


def test_invalid_event_line_raises_loudly(tmp_path):
    led = _ledger(tmp_path)
    with open(led.path, "a", encoding="utf-8") as f:
        # valid JSON, invalid CounterContestEvent (missing required keys)
        f.write(json.dumps({"event_id": "x"}) + "\n")
    with pytest.raises(CounterContestEventError):
        led.list_events()


def test_duplicate_event_id_raises_during_read(tmp_path):
    led = _ledger(tmp_path)
    shared = str(uuid.uuid4())
    led.append_event(_event(event_id=shared, contestant_id="a"))
    led.append_event(_event(event_id=shared, contestant_id="b"))
    with pytest.raises(ContestEventLedgerError) as e:
        led.list_events()
    assert e.value.reason == "duplicate_event_id"


def test_duplicate_event_id_not_silently_collapsed(tmp_path):
    # The append-only writer performs no dedup: both lines are on disk
    # (proving no silent collapse); the integrity violation surfaces at read.
    led = _ledger(tmp_path)
    shared = str(uuid.uuid4())
    led.append_event(_event(event_id=shared, contestant_id="a"))
    led.append_event(_event(event_id=shared, contestant_id="b"))
    with open(led.path, "r", encoding="utf-8") as f:
        nonblank = [ln for ln in f if ln.strip()]
    assert len(nonblank) == 2
    with pytest.raises(ContestEventLedgerError):
        led.list_events()


def test_duplicate_event_id_also_fails_via_filter(tmp_path):
    # list_events_for_contest replays through the same fail-closed full read,
    # so a duplicate event_id surfaces there too (no separate lenient path).
    led = _ledger(tmp_path)
    target = str(uuid.uuid4())
    shared = str(uuid.uuid4())
    led.append_event(_event(event_id=shared, target_contest_id=target))
    led.append_event(_event(event_id=shared, target_contest_id=target))
    with pytest.raises(ContestEventLedgerError):
        led.list_events_for_contest(target)
