"""tests/test_contest_ledger.py

B2-S3 replay tests for the Track B v0.2 ContestLedger: append-only storage
and literal full-file replay only.

Pure storage truth. No counter-contest events, no event replay, no
candidate_handle binding, no per-eid status, no effective authority, no
operator-refuse enforcement, no retrieval/prompt/cognition/MCP — all parked.

ContestRecord / ContestLedger are provisional working names.
"""
from __future__ import annotations

import json
import uuid

import pytest

from torment_service.contest_ledger import ContestLedger, ContestLedgerError
from torment_service.contest_record import (
    ContestActor,
    ContestReasonClass,
    ContestRecord,
    ContestRecordError,
    ContestResult,
    ContestScope,
)
from torment_service.provenance_v1 import ProvenanceV1


# ── helpers ─────────────────────────────────────────────────────────


def _prov() -> ProvenanceV1:
    return ProvenanceV1.for_user_ingest(step=3, session_id="sess-1")


def _record(contest_id: str = None, **over) -> ContestRecord:
    base = dict(
        contest_id=contest_id or str(uuid.uuid4()),
        contest_scope=ContestScope.AGENT,
        contestant_actor=ContestActor.AGENT,
        contestant_id="agent-7",
        reason_class=ContestReasonClass.MATERIAL_DISAGREEMENT,
        contest_result=ContestResult.LOW_AUTHORITY,
        original_memory_preserved=True,
        contest_provenance=_prov(),
        contested_eid=5,
    )
    base.update(over)
    return ContestRecord(**base)


def _ledger(tmp_path) -> ContestLedger:
    return ContestLedger(str(tmp_path), "ws1")


# ── append + literal read ───────────────────────────────────────────


def test_append_one_record(tmp_path):
    led = _ledger(tmp_path)
    rec = _record()
    led.append_record(rec)
    got = led.list_records()
    assert len(got) == 1
    assert got[0] == rec


def test_append_multiple_records(tmp_path):
    led = _ledger(tmp_path)
    recs = [_record(contest_reason=f"r{i}") for i in range(3)]
    for r in recs:
        led.append_record(r)
    assert led.list_records() == recs


def test_literal_read_preserves_append_order(tmp_path):
    led = _ledger(tmp_path)
    recs = [_record(contestant_id=f"agent-{i}") for i in range(5)]
    for r in recs:
        led.append_record(r)
    got = led.list_records()
    assert [r.contestant_id for r in got] == [f"agent-{i}" for i in range(5)]


def test_persisted_record_round_trips_exactly(tmp_path):
    led = _ledger(tmp_path)
    rec = _record(
        contest_scope=ContestScope.CHARACTER,
        contestant_actor=ContestActor.OPERATOR,
        reason_class=ContestReasonClass.IDENTITY_CONFLICT,
        contest_result=ContestResult.REFUSE,
        contest_reason="persona canon conflict",
    )
    led.append_record(rec)
    (got,) = led.list_records()
    assert got == rec


def test_nested_provenance_survives_round_trip(tmp_path):
    led = _ledger(tmp_path)
    rec = _record()
    led.append_record(rec)
    (got,) = led.list_records()
    assert isinstance(got.contest_provenance, ProvenanceV1)
    assert got.contest_provenance == rec.contest_provenance


# ── writer boundary ─────────────────────────────────────────────────


def test_append_rejects_raw_dict(tmp_path):
    led = _ledger(tmp_path)
    with pytest.raises(TypeError):
        led.append_record(_record().to_dict())  # type: ignore[arg-type]
    # Nothing was written.
    assert led.list_records() == []


# ── empty / missing ─────────────────────────────────────────────────


def test_empty_ledger_returns_empty_list(tmp_path):
    led = _ledger(tmp_path)
    # File does not exist yet.
    assert led.list_records() == []


def test_blank_lines_are_skipped(tmp_path):
    led = _ledger(tmp_path)
    led.append_record(_record())
    with open(led.path, "a", encoding="utf-8") as f:
        f.write("\n   \n")
    assert len(led.list_records()) == 1


def test_missing_file_returns_empty_list(tmp_path):
    # A fresh ledger whose path was never written.
    led = ContestLedger(str(tmp_path), "never-written-ws")
    assert led.list_records() == []


# ── fail-closed read posture ────────────────────────────────────────


def test_malformed_jsonl_line_raises_loudly(tmp_path):
    led = _ledger(tmp_path)
    led.append_record(_record())
    with open(led.path, "a", encoding="utf-8") as f:
        f.write("{ this is not valid json\n")
    with pytest.raises(ContestLedgerError) as e:
        led.list_records()
    assert e.value.reason == "malformed_line"


def test_invalid_contest_record_line_raises_loudly(tmp_path):
    led = _ledger(tmp_path)
    with open(led.path, "a", encoding="utf-8") as f:
        # valid JSON, invalid ContestRecord (missing required keys)
        f.write(json.dumps({"contest_id": "x"}) + "\n")
    with pytest.raises(ContestRecordError):
        led.list_records()


def test_duplicate_contest_id_raises_during_read(tmp_path):
    led = _ledger(tmp_path)
    shared = str(uuid.uuid4())
    led.append_record(_record(contest_id=shared, contestant_id="agent-a"))
    led.append_record(_record(contest_id=shared, contestant_id="agent-b"))
    with pytest.raises(ContestLedgerError) as e:
        led.list_records()
    assert e.value.reason == "duplicate_contest_id"


def test_duplicate_contest_id_not_silently_collapsed(tmp_path):
    # The append-only writer performs no dedup: both lines are on disk
    # (proving no silent collapse); the integrity violation surfaces at read.
    led = _ledger(tmp_path)
    shared = str(uuid.uuid4())
    led.append_record(_record(contest_id=shared, contestant_id="agent-a"))
    led.append_record(_record(contest_id=shared, contestant_id="agent-b"))
    with open(led.path, "r", encoding="utf-8") as f:
        nonblank = [ln for ln in f if ln.strip()]
    assert len(nonblank) == 2
    with pytest.raises(ContestLedgerError):
        led.list_records()
