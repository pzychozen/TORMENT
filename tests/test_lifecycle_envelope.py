"""tests/test_lifecycle_envelope.py

Slice 0 tests for the Q2 lifecycle envelope vocabulary and validator.

Per Q2-G test-category framing -- all P0 categories plus P1 history_ref
and multi-channel-mismatch categories. The P2 archived-docstring category
is handled as documentation review (not an automated test) per Q2-G
recommendation.

Slice 0 does NOT test:
  * Production wiring (no read/write sites use the envelope yet).
  * Migration shim (Q2-D).
  * Enforcement primitive ``assert_lifecycle_row_authoritative`` (Q2-F).
  * Transition-graph legality.
  * State-to-authority pairing (decision-table conformance is tested at
    the "happy path constructs" level only; per-state pairing enforcement
    is deferred to a later wiring slice).
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Dict

import pytest

from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleHistoryRef,
    LifecycleJoinTarget,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStateError,
    LifecycleStatus,
    SideChannel,
    validate_lifecycle_envelope,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _set_by(
    actor: LifecycleActor = LifecycleActor.SYSTEM,
    via: LifecycleSetVia = LifecycleSetVia.UNSET_DEFAULT,
    at: int = 1_716_300_000,
) -> LifecycleSetBy:
    return LifecycleSetBy(actor=actor, via=via, at=at)


def _join() -> LifecycleJoinTarget:
    return LifecycleJoinTarget(
        side_channel=SideChannel.REVIEW_QUEUE, join_key="eid",
    )


def _history() -> LifecycleHistoryRef:
    return LifecycleHistoryRef(
        ledger=SideChannel.BATON_LEDGER, last_event_id="evt_001",
    )


def _live(
    state: LifecycleState = LifecycleState.UNSET,
    set_by: LifecycleSetBy = None,
    history_ref: LifecycleHistoryRef = None,
) -> LifecycleStatus:
    """Construct a row-authoritative (live) envelope with sensible defaults."""
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=set_by if set_by is not None else _set_by(),
        history_ref=history_ref,
    )


def _join_required(
    state: LifecycleState = LifecycleState.REVIEW_PENDING,
    set_by: LifecycleSetBy = None,
    history_ref: LifecycleHistoryRef = None,
) -> LifecycleStatus:
    """Construct a join-required envelope with sensible defaults."""
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=False,
        requires_join=_join(),
        set_by=set_by if set_by is not None else _set_by(
            actor=LifecycleActor.MIGRATION,
            via=LifecycleSetVia.GATE1_REFUSAL,
        ),
        history_ref=history_ref,
    )


# ===========================================================================
# Category 1 -- envelope shape contract (P0)
# ===========================================================================


def test_envelope_to_dict_has_all_five_keys():
    d = _live().to_dict()
    assert set(d.keys()) == {
        "state",
        "is_authoritative_on_row",
        "requires_join",
        "set_by",
        "history_ref",
    }


# ===========================================================================
# Category 2 -- closed state vocabulary (P0)
# ===========================================================================


@pytest.mark.parametrize("state", list(LifecycleState))
def test_each_valid_state_constructs(state):
    """Every state in the ratified vocabulary must construct successfully
    when paired with valid is_authoritative_on_row / requires_join.

    review_pending is the only state whose default decision-table entry
    requires a join; all others are row-authoritative by default.
    """
    if state is LifecycleState.REVIEW_PENDING:
        env = _join_required(state=state)
    else:
        env = _live(state=state)
    assert env.state is state


def test_unknown_state_rejected_in_dict():
    d = _live().to_dict()
    d["state"] = "totally_made_up"
    with pytest.raises(LifecycleStateError) as exc_info:
        validate_lifecycle_envelope(d)
    assert exc_info.value.field == "state"
    assert exc_info.value.reason == "unknown_value"


# ===========================================================================
# Category 3 -- closed side-channel vocabulary (P0)
# ===========================================================================


@pytest.mark.parametrize("ch", list(SideChannel))
def test_each_valid_side_channel_accepted(ch):
    target = LifecycleJoinTarget(side_channel=ch, join_key="eid")
    assert target.side_channel is ch


def test_unknown_side_channel_rejected_in_dict():
    d = _join_required().to_dict()
    d["requires_join"]["side_channel"] = "made_up_channel"
    with pytest.raises(LifecycleStateError) as exc_info:
        validate_lifecycle_envelope(d)
    assert "side_channel" in exc_info.value.field
    assert exc_info.value.reason == "unknown_value"


# ===========================================================================
# Category 4 -- closed actor vocabulary (P0)
# ===========================================================================


@pytest.mark.parametrize("actor", list(LifecycleActor))
def test_each_valid_actor_accepted(actor):
    sb = LifecycleSetBy(actor=actor, via=LifecycleSetVia.API, at=1)
    assert sb.actor is actor


def test_unknown_actor_rejected_in_dict():
    d = _live().to_dict()
    d["set_by"]["actor"] = "the_council"
    with pytest.raises(LifecycleStateError) as exc_info:
        validate_lifecycle_envelope(d)
    assert exc_info.value.field == "set_by.actor"
    assert exc_info.value.reason == "unknown_value"


# ===========================================================================
# Category 5 -- closed set_by.via vocabulary (P0)
# ===========================================================================


def test_unknown_via_rejected_in_dict():
    d = _live().to_dict()
    d["set_by"]["via"] = "vibes"
    with pytest.raises(LifecycleStateError) as exc_info:
        validate_lifecycle_envelope(d)
    assert exc_info.value.field == "set_by.via"
    assert exc_info.value.reason == "unknown_value"


# ===========================================================================
# Category 6 -- authoritative-vs-join complementarity (P0)
# Four combinations: 2 legal, 2 illegal.
# ===========================================================================


def test_auth_true_with_no_join_constructs():
    env = LifecycleStatus(
        state=LifecycleState.RELEASED,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=_set_by(),
        history_ref=None,
    )
    assert env.requires_join is None


def test_auth_false_with_join_constructs():
    env = LifecycleStatus(
        state=LifecycleState.REVIEW_PENDING,
        is_authoritative_on_row=False,
        requires_join=_join(),
        set_by=_set_by(),
        history_ref=None,
    )
    assert env.requires_join is not None


def test_auth_true_with_join_rejected():
    with pytest.raises(LifecycleStateError) as exc_info:
        LifecycleStatus(
            state=LifecycleState.RELEASED,
            is_authoritative_on_row=True,
            requires_join=_join(),  # illegal -- authoritative AND join
            set_by=_set_by(),
            history_ref=None,
        )
    assert exc_info.value.reason == "must_be_null_when_authoritative"


def test_auth_false_with_no_join_rejected():
    with pytest.raises(LifecycleStateError) as exc_info:
        LifecycleStatus(
            state=LifecycleState.REVIEW_PENDING,
            is_authoritative_on_row=False,
            requires_join=None,  # illegal -- not authoritative, no join target
            set_by=_set_by(),
            history_ref=None,
        )
    assert exc_info.value.reason == "must_be_populated_when_not_authoritative"


# ===========================================================================
# Category 7 -- row-authoritative states honor the decision table (P0)
# ===========================================================================


ROW_AUTHORITATIVE_STATES = [
    s for s in LifecycleState if s is not LifecycleState.REVIEW_PENDING
]


@pytest.mark.parametrize("state", ROW_AUTHORITATIVE_STATES)
def test_row_authoritative_states_honor_table(state):
    """The 7 row-authoritative states from the Q2-C decision table all
    construct successfully with is_authoritative_on_row=True and
    requires_join=None.
    """
    env = _live(state=state)
    assert env.state is state
    assert env.is_authoritative_on_row is True
    assert env.requires_join is None


# ===========================================================================
# Category 8 -- review_pending requires review_queue (P0)
# ===========================================================================


def test_review_pending_with_review_queue_constructs():
    """The only initial join-required state must construct with
    side_channel=review_queue per the Q2-C decision table.
    """
    env = _join_required(state=LifecycleState.REVIEW_PENDING)
    assert env.state is LifecycleState.REVIEW_PENDING
    assert env.is_authoritative_on_row is False
    assert env.requires_join is not None
    assert env.requires_join.side_channel is SideChannel.REVIEW_QUEUE
    assert env.requires_join.join_key == "eid"


# ===========================================================================
# Category 9 -- unset representability (P0)
# ===========================================================================


def test_unset_default_envelope_constructs():
    """The migration-shim default envelope (state=unset, row-authoritative,
    actor=migration, via=unset_default) constructs and serializes cleanly.
    """
    env = LifecycleStatus(
        state=LifecycleState.UNSET,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(
            actor=LifecycleActor.MIGRATION,
            via=LifecycleSetVia.UNSET_DEFAULT,
            at=1_716_300_000,
        ),
        history_ref=None,
    )
    d = env.to_dict()
    assert d["state"] == "unset"
    assert d["set_by"]["actor"] == "migration"
    assert d["set_by"]["via"] == "unset_default"


# ===========================================================================
# Category 11 -- history_ref optionality (P1)
# ===========================================================================


def test_history_ref_null_accepted():
    env = _live(history_ref=None)
    assert env.history_ref is None
    assert env.to_dict()["history_ref"] is None


def test_history_ref_populated_accepted():
    env = _live(
        state=LifecycleState.CONSUMED,
        set_by=_set_by(via=LifecycleSetVia.BATON_CONSUME),
        history_ref=_history(),
    )
    assert env.history_ref is not None
    d = env.to_dict()
    assert d["history_ref"] == {
        "ledger": "baton_ledger",
        "last_event_id": "evt_001",
    }


# ===========================================================================
# Category 12 -- round-trip to_dict / from_dict (P0)
# ===========================================================================


def test_round_trip_live_envelope():
    original = _live(state=LifecycleState.PROTECTED,
                     set_by=_set_by(via=LifecycleSetVia.CANON_SET))
    d = original.to_dict()
    reconstructed = LifecycleStatus.from_dict(d)
    assert reconstructed == original
    assert reconstructed.to_dict() == d


def test_round_trip_join_required_envelope():
    original = _join_required(history_ref=_history())
    d = original.to_dict()
    reconstructed = LifecycleStatus.from_dict(d)
    assert reconstructed == original
    assert reconstructed.to_dict() == d


# ===========================================================================
# Category 13 -- frozen dataclass immutability (P0)
# ===========================================================================


@pytest.mark.parametrize("field_name", [
    "state",
    "is_authoritative_on_row",
    "requires_join",
    "set_by",
    "history_ref",
])
def test_envelope_frozen(field_name):
    env = _live()
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(env, field_name, None)


def test_nested_types_frozen():
    sb = _set_by()
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(sb, "actor", LifecycleActor.OPERATOR)

    jt = _join()
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(jt, "side_channel", SideChannel.CLOSURE_LEDGER)

    hr = _history()
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(hr, "last_event_id", "other")


# ===========================================================================
# Category 14 -- invalid envelope rejection (P0)
# ===========================================================================


@pytest.mark.parametrize("missing_key", [
    "state",
    "is_authoritative_on_row",
    "requires_join",
    "set_by",
    "history_ref",
])
def test_missing_required_field_rejected(missing_key):
    d = _live().to_dict()
    del d[missing_key]
    with pytest.raises(LifecycleStateError) as exc_info:
        validate_lifecycle_envelope(d)
    assert exc_info.value.field == missing_key
    assert exc_info.value.reason == "missing_required_key"


def test_wrong_type_for_is_authoritative_rejected():
    d = _live().to_dict()
    d["is_authoritative_on_row"] = "yes"  # string, not bool
    with pytest.raises(LifecycleStateError) as exc_info:
        validate_lifecycle_envelope(d)
    assert exc_info.value.field == "is_authoritative_on_row"
    assert exc_info.value.reason == "must_be_bool"


def test_validate_envelope_rejects_non_dict_input():
    for bad in (None, 42, "not a dict", [], (1, 2)):
        with pytest.raises(LifecycleStateError) as exc_info:
            validate_lifecycle_envelope(bad)
        assert exc_info.value.field == "lifecycle_status"
        assert exc_info.value.reason == "not_a_dict"


def test_null_set_by_rejected():
    d = _live().to_dict()
    d["set_by"] = None
    with pytest.raises(LifecycleStateError) as exc_info:
        validate_lifecycle_envelope(d)
    assert exc_info.value.field == "set_by"


# ===========================================================================
# Category 15 -- enum string serialization (P0)
# ===========================================================================


def test_enum_serializes_as_string():
    """to_dict must produce raw strings, not Enum.NAME, so JSON works."""
    env = _live(state=LifecycleState.PROTECTED)
    d = env.to_dict()
    assert d["state"] == "protected"
    assert isinstance(d["state"], str)
    # JSON-encodable end-to-end
    s = json.dumps(d)
    reloaded = json.loads(s)
    assert reloaded["state"] == "protected"
    assert reloaded["set_by"]["actor"] in {
        a.value for a in LifecycleActor
    }


# ===========================================================================
# Category 16 -- nested type round-trip (P0)
# ===========================================================================


def test_set_by_round_trip():
    original = _set_by(actor=LifecycleActor.OPERATOR,
                       via=LifecycleSetVia.API, at=42)
    reconstructed = LifecycleSetBy.from_dict(original.to_dict())
    assert reconstructed == original


def test_join_target_round_trip():
    original = LifecycleJoinTarget(
        side_channel=SideChannel.CLOSURE_LEDGER, join_key="closure_id",
    )
    reconstructed = LifecycleJoinTarget.from_dict(original.to_dict())
    assert reconstructed == original


def test_history_ref_round_trip():
    original = LifecycleHistoryRef(
        ledger=SideChannel.BATON_LEDGER, last_event_id="evt_42",
    )
    reconstructed = LifecycleHistoryRef.from_dict(original.to_dict())
    assert reconstructed == original


# ===========================================================================
# Category 17 -- multi-channel mismatch permitted (P1)
# ===========================================================================


def test_join_channel_and_history_channel_may_differ():
    """requires_join.side_channel and history_ref.ledger may name DIFFERENT
    channels per Q2-B Section 3 -- e.g., join points at review_queue for
    current status, while history_ref points at closure_ledger for
    transition history. Validator must not reject this.
    """
    env = LifecycleStatus(
        state=LifecycleState.REVIEW_PENDING,
        is_authoritative_on_row=False,
        requires_join=LifecycleJoinTarget(
            side_channel=SideChannel.REVIEW_QUEUE, join_key="eid",
        ),
        set_by=_set_by(via=LifecycleSetVia.GATE1_REFUSAL),
        history_ref=LifecycleHistoryRef(
            ledger=SideChannel.CLOSURE_LEDGER, last_event_id="evt_99",
        ),
    )
    assert env.requires_join.side_channel is SideChannel.REVIEW_QUEUE
    assert env.history_ref.ledger is SideChannel.CLOSURE_LEDGER


# ===========================================================================
# Category 18 -- set_by required-fields (P0)
# ===========================================================================


@pytest.mark.parametrize("missing", ["actor", "via", "at"])
def test_set_by_missing_field_rejected(missing):
    d = _live().to_dict()
    del d["set_by"][missing]
    with pytest.raises(LifecycleStateError) as exc_info:
        validate_lifecycle_envelope(d)
    assert exc_info.value.field == f"set_by.{missing}"
    assert exc_info.value.reason == "missing"


# ===========================================================================
# Category 19 -- set_by.at type / non-negativity (P1)
# ===========================================================================


def test_set_by_at_negative_rejected():
    with pytest.raises(LifecycleStateError) as exc_info:
        LifecycleSetBy(
            actor=LifecycleActor.SYSTEM,
            via=LifecycleSetVia.API,
            at=-1,
        )
    assert exc_info.value.field == "set_by.at"
    assert exc_info.value.reason == "must_be_non_negative"


def test_set_by_at_non_int_rejected():
    for bad in ("now", 1.5, None):
        with pytest.raises(LifecycleStateError) as exc_info:
            LifecycleSetBy(
                actor=LifecycleActor.SYSTEM,
                via=LifecycleSetVia.API,
                at=bad,
            )
        assert exc_info.value.field == "set_by.at"


# ===========================================================================
# Category 20 -- acceptance-test conformance meta-test (P0)
# ===========================================================================


def test_consumer_can_determine_status_without_guessing():
    """The Q2 invariant sentinel: given representative envelopes, a
    consumer can determine authority status and (if needed) the join
    target without external knowledge or guessing.
    """
    samples = [
        # Row-authoritative: released
        _live(state=LifecycleState.RELEASED,
              set_by=_set_by(via=LifecycleSetVia.RELEASE_PROMOTION)),
        # Row-authoritative: protected, post-collapse via canon
        _live(state=LifecycleState.PROTECTED,
              set_by=_set_by(via=LifecycleSetVia.CANON_SET)),
        # Row-authoritative: unset (migration shim default)
        _live(state=LifecycleState.UNSET,
              set_by=_set_by(actor=LifecycleActor.MIGRATION,
                             via=LifecycleSetVia.UNSET_DEFAULT)),
        # Join-required: review_pending
        _join_required(state=LifecycleState.REVIEW_PENDING),
        # Row-authoritative: consumed with baton-ledger history
        _live(state=LifecycleState.CONSUMED,
              set_by=_set_by(via=LifecycleSetVia.BATON_CONSUME),
              history_ref=_history()),
    ]
    for env in samples:
        d = env.to_dict()
        # 1. The consumer can read state without guessing.
        assert d["state"] in {s.value for s in LifecycleState}
        # 2. The consumer can determine authoritativeness directly.
        assert isinstance(d["is_authoritative_on_row"], bool)
        # 3. If not authoritative, the join target is named explicitly.
        if not d["is_authoritative_on_row"]:
            assert d["requires_join"] is not None
            assert d["requires_join"]["side_channel"] in {
                c.value for c in SideChannel
            }
            assert d["requires_join"]["join_key"]
        else:
            assert d["requires_join"] is None
        # 4. The set_by provenance is always present.
        assert d["set_by"] is not None
        assert d["set_by"]["actor"] in {a.value for a in LifecycleActor}
        assert d["set_by"]["via"] in {v.value for v in LifecycleSetVia}
        assert isinstance(d["set_by"]["at"], int)
