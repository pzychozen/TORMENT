"""tests/test_contest_record.py

B2-S2 Slice-0 tests for the Track B v0.2 ContestRecord vocabulary,
validator, and pure serialization.

Pure tests only. No production wiring, no filesystem, no ledger. This slice
does NOT test (deferred to later slices): ledger write/read/replay,
counter-contest linkage, candidate_handle -> eid binding, operator-refuse
live enforcement, effective-authority resolution, cross-surface influence.

``ContestRecord`` is a provisional working name.
"""
from __future__ import annotations

import dataclasses
import json
import uuid

import pytest

from torment_service.contest_record import (
    ContestActor,
    ContestReasonClass,
    ContestRecord,
    ContestRecordError,
    ContestResult,
    ContestScope,
    MIN_VALID_EID,
    validate_contest_record,
)
from torment_service.provenance_v1 import ProvenanceV1


# ── helpers ─────────────────────────────────────────────────────────


def _prov() -> ProvenanceV1:
    return ProvenanceV1.for_user_ingest(step=3, session_id="sess-1")


def _eid_record(**over) -> ContestRecord:
    base = dict(
        contest_id=str(uuid.uuid4()),
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


def _eid_dict(**over) -> dict:
    d = dict(
        contest_id=str(uuid.uuid4()),
        contest_scope="agent",
        contestant_actor="agent",
        contestant_id="agent-7",
        reason_class="material_disagreement",
        contest_result="low-authority",
        original_memory_preserved=True,
        contest_provenance=_prov().to_dict(),
        contested_eid=5,
    )
    d.update(over)
    return d


def _handle_dict(**over) -> dict:
    d = _eid_dict()
    d.pop("contested_eid", None)
    d["candidate_handle"] = str(uuid.uuid4())
    d.update(over)
    return d


# ── valid construction ──────────────────────────────────────────────


def test_valid_contested_eid_target_record():
    rec = _eid_record()
    assert isinstance(rec, ContestRecord)
    assert rec.contested_eid == 5
    assert rec.candidate_handle is None


def test_valid_candidate_handle_target_record():
    rec = _eid_record(contested_eid=None, candidate_handle=str(uuid.uuid4()))
    assert isinstance(rec, ContestRecord)
    assert rec.contested_eid is None
    assert rec.candidate_handle is not None


def test_valid_fuller_record():
    rec = _eid_record(
        contest_scope=ContestScope.CHARACTER,
        contestant_actor=ContestActor.CHARACTER,
        reason_class=ContestReasonClass.IDENTITY_CONFLICT,
        contest_result=ContestResult.RELEASED,
        contest_reason="conflicts with established persona canon",
    )
    assert rec.contest_reason == "conflicts with established persona canon"
    assert rec.contest_result is ContestResult.RELEASED


# ── serialization ───────────────────────────────────────────────────


def test_deterministic_to_dict_serialization():
    rec = _eid_record()
    assert rec.to_dict() == rec.to_dict()
    # JSON form is deterministic under stable key ordering.
    assert json.dumps(rec.to_dict(), sort_keys=True) == json.dumps(
        rec.to_dict(), sort_keys=True
    )


def test_dict_round_trip_identity():
    rec = _eid_record()
    assert ContestRecord.from_dict(rec.to_dict()) == rec


def test_dict_round_trip_identity_handle_target():
    rec = _eid_record(contested_eid=None, candidate_handle=str(uuid.uuid4()))
    assert ContestRecord.from_dict(rec.to_dict()) == rec


def test_json_round_trip_identity():
    rec = _eid_record(contest_reason="material dispute")
    restored = ContestRecord.from_dict(json.loads(json.dumps(rec.to_dict())))
    assert restored == rec


def test_jsonl_single_record_line_in_memory():
    rec = _eid_record()
    line = json.dumps(rec.to_dict()) + "\n"
    assert line.endswith("\n")
    restored = ContestRecord.from_dict(json.loads(line))
    assert restored == rec


def test_nested_provenance_round_trips():
    rec = _eid_record()
    as_dict = rec.to_dict()
    assert isinstance(as_dict["contest_provenance"], dict)
    restored = ContestRecord.from_dict(as_dict)
    assert isinstance(restored.contest_provenance, ProvenanceV1)
    assert restored.contest_provenance == rec.contest_provenance


# ── contest_id ──────────────────────────────────────────────────────


def test_contest_id_required():
    d = _eid_dict()
    del d["contest_id"]
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(d)
    assert e.value.field == "contest_id"
    assert e.value.reason == "missing"


def test_contest_id_invalid_uuid_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contest_id="not-a-uuid"))
    assert e.value.field == "contest_id"
    assert e.value.reason == "not_uuid_shaped"


def test_validator_never_generates_contest_id():
    # A missing contest_id is an error, never silently filled.
    d = _eid_dict()
    del d["contest_id"]
    with pytest.raises(ContestRecordError):
        validate_contest_record(d)


# ── target shape ────────────────────────────────────────────────────


def test_candidate_handle_invalid_uuid_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_handle_dict(candidate_handle="nope"))
    assert e.value.field == "candidate_handle"
    assert e.value.reason == "not_uuid_shaped"


def test_both_targets_rejected():
    d = _eid_dict(candidate_handle=str(uuid.uuid4()))
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(d)
    assert e.value.field == "target"
    assert e.value.reason == "ambiguous_target"


def test_neither_target_rejected():
    d = _eid_dict()
    del d["contested_eid"]
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(d)
    assert e.value.field == "target"
    assert e.value.reason == "missing_target"


def test_contested_eid_bool_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contested_eid=True))
    assert e.value.field == "contested_eid"
    assert e.value.reason == "must_be_int"


@pytest.mark.parametrize("bad_eid", [MIN_VALID_EID - 1, -1, -100])
def test_contested_eid_out_of_range_rejected(bad_eid):
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contested_eid=bad_eid))
    assert e.value.field == "contested_eid"
    assert e.value.reason == "out_of_range"


def test_contested_eid_minimum_accepted():
    rec = validate_contest_record(_eid_dict(contested_eid=MIN_VALID_EID))
    assert rec.contested_eid == MIN_VALID_EID


def test_contested_eid_string_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contested_eid="5"))
    assert e.value.field == "contested_eid"
    assert e.value.reason == "must_be_int"


def test_contested_eid_float_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contested_eid=5.0))
    assert e.value.field == "contested_eid"
    assert e.value.reason == "must_be_int"


# ── closed vocabularies ─────────────────────────────────────────────


def test_unknown_contest_scope_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contest_scope="planet"))
    assert e.value.field == "contest_scope"
    assert e.value.reason == "unknown_value"


def test_unknown_contestant_actor_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contestant_actor="daemon"))
    assert e.value.field == "contestant_actor"
    assert e.value.reason == "unknown_value"


def test_unknown_reason_class_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(reason_class="vibes"))
    assert e.value.field == "reason_class"
    assert e.value.reason == "unknown_value"


def test_unknown_contest_result_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contest_result="delete"))
    assert e.value.field == "contest_result"
    assert e.value.reason == "unknown_value"


# ── scalar field rules ──────────────────────────────────────────────


def test_empty_contestant_id_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contestant_id=""))
    assert e.value.field == "contestant_id"


def test_empty_contest_reason_rejected_when_present():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contest_reason=""))
    assert e.value.field == "contest_reason"


def test_original_memory_preserved_missing_rejected():
    d = _eid_dict()
    del d["original_memory_preserved"]
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(d)
    assert e.value.field == "original_memory_preserved"
    assert e.value.reason == "missing"


def test_original_memory_preserved_false_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(original_memory_preserved=False))
    assert e.value.field == "original_memory_preserved"
    assert e.value.reason == "must_be_true"


def test_original_memory_preserved_one_rejected():
    # 1 is truthy and == True, but `is True` is False; must fail closed.
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(original_memory_preserved=1))
    assert e.value.field == "original_memory_preserved"
    assert e.value.reason == "must_be_true"


# ── nested provenance ───────────────────────────────────────────────


def test_invalid_nested_provenance_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(
            _eid_dict(contest_provenance={"source_type": "not_a_real_source"})
        )
    assert e.value.field == "contest_provenance"
    assert e.value.reason == "invalid_provenance"


def test_partial_contest_provenance_dict_rejected():
    # {"source_type": "user_input"} is constructible by ProvenanceV1.from_dict
    # but triggers default synthesis (schema_version, write_path,
    # created_at_ts, ...). The ContestRecord boundary must fail closed rather
    # than accept the silently-completed nested provenance.
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(
            _eid_dict(contest_provenance={"source_type": "user_input"})
        )
    assert e.value.field == "contest_provenance"
    assert e.value.reason == "non_canonical_provenance"


def test_canonical_contest_provenance_dict_accepted_and_round_trips():
    # A canonical ProvenanceV1 serialization is accepted and survives the
    # full ContestRecord round trip. (Boundary requires canonical nested
    # serialization; ProvenanceV1 behavior is not redesigned globally.)
    canonical = _prov().to_dict()
    rec = validate_contest_record(_eid_dict(contest_provenance=canonical))
    assert rec.contest_provenance.to_dict() == canonical
    assert ContestRecord.from_dict(rec.to_dict()) == rec


def test_contest_provenance_unknown_nested_key_rejected():
    # ProvenanceV1.from_dict silently drops unknown keys; the canonical
    # equality guard catches that drop at the ContestRecord boundary.
    prov_dict = _prov().to_dict()
    prov_dict["mystery_nested_key"] = "x"
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(contest_provenance=prov_dict))
    assert e.value.field == "contest_provenance"
    assert e.value.reason == "non_canonical_provenance"


# ── fail-closed on unknown top-level keys ───────────────────────────


def test_unknown_top_level_key_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(_eid_dict(surprise=1))
    assert e.value.reason == "unknown_field"


# ── prohibition-only authorization rule ─────────────────────────────


def test_non_operator_refuse_rejected():
    with pytest.raises(ContestRecordError) as e:
        validate_contest_record(
            _eid_dict(contestant_actor="agent", contest_result="refuse")
        )
    assert e.value.field == "contest_result"
    assert e.value.reason == "refuse_requires_operator"


def test_operator_refuse_accepted_as_vocabulary_only():
    # Vocabulary validity ONLY. Passing the validator is NOT authorization
    # for any live effect: operator actor is necessary-but-not-sufficient,
    # and this slice grants no authorization and performs no enforcement.
    rec = validate_contest_record(
        _eid_dict(contestant_actor="operator", contest_result="refuse")
    )
    assert rec.contest_result is ContestResult.REFUSE
    assert rec.contestant_actor is ContestActor.OPERATOR


# ── declared-only vocabulary members ────────────────────────────────


def test_workspace_scope_accepted_as_declared_vocabulary_only():
    # Accepted as declared vocabulary; runtime behavior remains deferred.
    rec = validate_contest_record(_eid_dict(contest_scope="workspace"))
    assert rec.contest_scope is ContestScope.WORKSPACE


def test_user_actor_accepted_as_declared_vocabulary_only():
    # Accepted as declared vocabulary; deferred to Cluster 3.
    rec = validate_contest_record(_eid_dict(contestant_actor="user"))
    assert rec.contestant_actor is ContestActor.USER


# ── immutability ────────────────────────────────────────────────────


def test_frozen_dataclass_mutation_rejected():
    rec = _eid_record()
    with pytest.raises(dataclasses.FrozenInstanceError):
        rec.contest_result = ContestResult.AUDIT_ONLY  # type: ignore[misc]
