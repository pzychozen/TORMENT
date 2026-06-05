"""tests/test_counter_contest_event.py

B2-S4 Slice tests for the Track B v0.2 CounterContestEvent vocabulary,
validator, and pure serialization.

Pure tests only. No production wiring, no filesystem, no ledger. This slice
records disagreement only and asserts no outcome: it does NOT test (parked to
later gates) target-existence validation, dangling-linkage policy,
counter-contest result routing, effective-authority resolution, or
cross-surface influence.

``CounterContestEvent`` is a provisional working name.
"""
from __future__ import annotations

import dataclasses
import json
import uuid

import pytest

from torment_service.counter_contest_event import (
    CounterContestEvent,
    CounterContestEventError,
    validate_counter_contest_event,
)
from torment_service.contest_record import ContestActor, ContestReasonClass
from torment_service.provenance_v1 import ProvenanceV1


# ── helpers ─────────────────────────────────────────────────────────


def _prov() -> ProvenanceV1:
    return ProvenanceV1.for_user_ingest(step=3, session_id="sess-1")


def _event(**over) -> CounterContestEvent:
    base = dict(
        event_id=str(uuid.uuid4()),
        target_contest_id=str(uuid.uuid4()),
        contestant_actor=ContestActor.AGENT,
        contestant_id="agent-7",
        reason_class=ContestReasonClass.MATERIAL_DISAGREEMENT,
        event_provenance=_prov(),
    )
    base.update(over)
    return CounterContestEvent(**base)


def _event_dict(**over) -> dict:
    d = dict(
        event_id=str(uuid.uuid4()),
        target_contest_id=str(uuid.uuid4()),
        contestant_actor="agent",
        contestant_id="agent-7",
        reason_class="material_disagreement",
        event_provenance=_prov().to_dict(),
    )
    d.update(over)
    return d


# ── valid construction ──────────────────────────────────────────────


def test_valid_event_construction():
    ev = _event()
    assert isinstance(ev, CounterContestEvent)
    assert _is_uuid(ev.event_id)
    assert _is_uuid(ev.target_contest_id)


def test_valid_fuller_event():
    ev = _event(
        contestant_actor=ContestActor.CHARACTER,
        reason_class=ContestReasonClass.IDENTITY_CONFLICT,
    )
    assert ev.contestant_actor is ContestActor.CHARACTER
    assert ev.reason_class is ContestReasonClass.IDENTITY_CONFLICT


def _is_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


# ── immutability ────────────────────────────────────────────────────


def test_frozen_dataclass_mutation_rejected():
    ev = _event()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.contestant_id = "someone-else"  # type: ignore[misc]


# ── event_id ────────────────────────────────────────────────────────


def test_event_id_required():
    d = _event_dict()
    del d["event_id"]
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(d)
    assert e.value.field == "event_id"
    assert e.value.reason == "missing"


def test_event_id_invalid_uuid_rejected():
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(_event_dict(event_id="not-a-uuid"))
    assert e.value.field == "event_id"
    assert e.value.reason == "not_uuid_shaped"


def test_validator_never_generates_event_id():
    # A missing event_id is an error, never silently filled.
    d = _event_dict()
    del d["event_id"]
    with pytest.raises(CounterContestEventError):
        validate_counter_contest_event(d)


# ── target_contest_id (structural shape only; existence parked) ──────


def test_target_contest_id_required():
    d = _event_dict()
    del d["target_contest_id"]
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(d)
    assert e.value.field == "target_contest_id"
    assert e.value.reason == "missing"


def test_target_contest_id_invalid_uuid_rejected():
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(_event_dict(target_contest_id="nope"))
    assert e.value.field == "target_contest_id"
    assert e.value.reason == "not_uuid_shaped"


def test_target_existence_is_not_checked():
    # A structurally valid UUID that matches no ContestRecord is accepted: the
    # event records a CLAIMED linkage; it does not prove target existence. No
    # lookup occurs at construction (existence policy is parked).
    dangling = str(uuid.uuid4())
    ev = validate_counter_contest_event(_event_dict(target_contest_id=dangling))
    assert ev.target_contest_id == dangling


# ── closed vocabularies (reused from contest_record) ────────────────


def test_unknown_contestant_actor_rejected():
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(_event_dict(contestant_actor="daemon"))
    assert e.value.field == "contestant_actor"
    assert e.value.reason == "unknown_value"


def test_unknown_reason_class_rejected():
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(_event_dict(reason_class="vibes"))
    assert e.value.field == "reason_class"
    assert e.value.reason == "unknown_value"


def test_actor_vocabulary_reused_unchanged():
    # All four contest-local actors remain valid for a counter-contest event.
    for actor in ("agent", "character", "operator", "user"):
        ev = validate_counter_contest_event(_event_dict(contestant_actor=actor))
        assert ev.contestant_actor.value == actor


# ── scalar field rules ──────────────────────────────────────────────


def test_empty_contestant_id_rejected():
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(_event_dict(contestant_id=""))
    assert e.value.field == "contestant_id"


def test_contestant_id_required():
    d = _event_dict()
    del d["contestant_id"]
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(d)
    assert e.value.field == "contestant_id"
    assert e.value.reason == "missing"


# ── nested provenance (canonical-only, fail closed) ─────────────────


def test_event_provenance_required():
    d = _event_dict()
    del d["event_provenance"]
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(d)
    assert e.value.field == "event_provenance"
    assert e.value.reason == "missing"


def test_invalid_nested_provenance_rejected():
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(
            _event_dict(event_provenance={"source_type": "not_a_real_source"})
        )
    assert e.value.field == "event_provenance"
    assert e.value.reason == "invalid_provenance"


def test_partial_nested_provenance_rejected():
    # {"source_type": "user_input"} is constructible by ProvenanceV1.from_dict
    # but triggers default synthesis. The boundary fails closed rather than
    # accept silently-completed nested provenance.
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(
            _event_dict(event_provenance={"source_type": "user_input"})
        )
    assert e.value.field == "event_provenance"
    assert e.value.reason == "non_canonical_provenance"


def test_unknown_nested_provenance_key_rejected():
    prov_dict = _prov().to_dict()
    prov_dict["mystery_nested_key"] = "x"
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(_event_dict(event_provenance=prov_dict))
    assert e.value.field == "event_provenance"
    assert e.value.reason == "non_canonical_provenance"


def test_canonical_nested_provenance_accepted_and_round_trips():
    canonical = _prov().to_dict()
    ev = validate_counter_contest_event(_event_dict(event_provenance=canonical))
    assert ev.event_provenance.to_dict() == canonical
    assert CounterContestEvent.from_dict(ev.to_dict()) == ev


# ── fail-closed on unknown top-level keys (incl. forbidden outcome) ─


def test_unknown_top_level_key_rejected():
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(_event_dict(surprise=1))
    assert e.value.reason == "unknown_field"


@pytest.mark.parametrize(
    "forbidden",
    [
        "contest_result", "status", "effective_status", "active", "inactive",
        "overturned", "superseded", "resolved", "winner", "precedence",
        "weight", "rank", "confidence", "priority",
    ],
)
def test_forbidden_outcome_field_rejected_as_unknown(forbidden):
    # A counter-contest event asserts NO outcome. None of these fields exist on
    # the record; passing any of them fails closed as an unknown top-level key.
    with pytest.raises(CounterContestEventError) as e:
        validate_counter_contest_event(_event_dict(**{forbidden: "x"}))
    assert e.value.reason == "unknown_field"


def test_no_outcome_field_on_record():
    field_names = {f.name for f in dataclasses.fields(CounterContestEvent)}
    forbidden = {
        "contest_result", "status", "effective_status", "active", "inactive",
        "overturned", "superseded", "resolved", "winner", "precedence",
        "weight", "rank", "confidence", "priority",
    }
    assert field_names.isdisjoint(forbidden)


# ── serialization ───────────────────────────────────────────────────


def test_deterministic_to_dict_serialization():
    ev = _event()
    assert ev.to_dict() == ev.to_dict()
    assert json.dumps(ev.to_dict(), sort_keys=True) == json.dumps(
        ev.to_dict(), sort_keys=True
    )


def test_dict_round_trip_identity():
    ev = _event()
    assert CounterContestEvent.from_dict(ev.to_dict()) == ev


def test_json_round_trip_identity():
    ev = _event()
    restored = CounterContestEvent.from_dict(json.loads(json.dumps(ev.to_dict())))
    assert restored == ev


def test_jsonl_single_record_line_in_memory():
    ev = _event()
    line = json.dumps(ev.to_dict()) + "\n"
    assert line.endswith("\n")
    restored = CounterContestEvent.from_dict(json.loads(line))
    assert restored == ev


def test_nested_provenance_round_trips():
    ev = _event()
    as_dict = ev.to_dict()
    assert isinstance(as_dict["event_provenance"], dict)
    restored = CounterContestEvent.from_dict(as_dict)
    assert isinstance(restored.event_provenance, ProvenanceV1)
    assert restored.event_provenance == ev.event_provenance


def test_empty_dict_rejected():
    with pytest.raises(CounterContestEventError):
        CounterContestEvent.from_dict({})


def test_non_dict_rejected():
    with pytest.raises(CounterContestEventError):
        CounterContestEvent.from_dict(["not", "a", "dict"])  # type: ignore[arg-type]
