"""tests/test_lifecycle_migration_shim.py

Q2-H1a tests for the read-side lifecycle migration shim,
``read_lifecycle_envelope``.

Per the ratified Q2-H1a plan:

* Missing or explicitly-null ``lifecycle_status`` resolves to the canonical
  row-authoritative UNSET envelope (actor=migration, via=unset_default).
* A present, valid envelope round-trips through the helper unchanged, and
  its embedded ``set_by.at`` is preserved (the ``now=`` parameter is
  ignored when the payload already carries an envelope).
* A present but malformed envelope MUST raise; the shim never downgrades
  corruption to UNSET. This is the safety edge of the helper.
* The helper is read-only: it never mutates the input payload.

Out of scope for H1a (and these tests):

* Production wiring (no consumer reads the envelope yet).
* Persistence / writeback of the derived envelope.
* Side-channel joins (Q2-E).
* Protected dual-source collapse (Q2-D).
* Enforcement primitive (Q2-F).
* State-to-authority pairing.
"""
from __future__ import annotations

import copy
import time
from typing import Any, Dict

import pytest

from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleJoinTarget,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStateError,
    LifecycleStatus,
    SideChannel,
    read_lifecycle_envelope,
    validate_lifecycle_envelope,
)


# ---------------------------------------------------------------------------
# Local builders (mirror tests/test_lifecycle_envelope.py to keep the H1a
# slice diff self-contained without cross-file imports).
# ---------------------------------------------------------------------------


FIXED_NOW = 1_716_300_000


def _live_envelope_dict() -> Dict[str, Any]:
    """A row-authoritative envelope serialized to its canonical dict shape."""
    return LifecycleStatus(
        state=LifecycleState.RELEASED,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(
            actor=LifecycleActor.OPERATOR,
            via=LifecycleSetVia.RELEASE_PROMOTION,
            at=FIXED_NOW,
        ),
        history_ref=None,
    ).to_dict()


def _join_required_envelope_dict() -> Dict[str, Any]:
    """A join-required envelope serialized to its canonical dict shape."""
    return LifecycleStatus(
        state=LifecycleState.REVIEW_PENDING,
        is_authoritative_on_row=False,
        requires_join=LifecycleJoinTarget(
            side_channel=SideChannel.REVIEW_QUEUE, join_key="eid",
        ),
        set_by=LifecycleSetBy(
            actor=LifecycleActor.MIGRATION,
            via=LifecycleSetVia.GATE1_REFUSAL,
            at=FIXED_NOW,
        ),
        history_ref=None,
    ).to_dict()


# ===========================================================================
# Category 1 -- absent envelope -> canonical UNSET (framing P1 #8 / P2 #12)
# ===========================================================================


def test_returns_unset_envelope_when_key_missing():
    env = read_lifecycle_envelope({}, now=FIXED_NOW)
    assert env.state is LifecycleState.UNSET
    assert env.is_authoritative_on_row is True
    assert env.requires_join is None
    assert env.history_ref is None
    assert env.set_by.actor is LifecycleActor.MIGRATION
    assert env.set_by.via is LifecycleSetVia.UNSET_DEFAULT
    assert env.set_by.at == FIXED_NOW


def test_returns_unset_envelope_when_value_is_none():
    """Explicit-None and missing-key are treated identically per the
    ratified H1a design call: both mean 'legacy row, no lifecycle was
    ever written.'
    """
    env = read_lifecycle_envelope({"lifecycle_status": None}, now=FIXED_NOW)
    assert env.state is LifecycleState.UNSET
    assert env.is_authoritative_on_row is True
    assert env.requires_join is None
    assert env.set_by.actor is LifecycleActor.MIGRATION
    assert env.set_by.via is LifecycleSetVia.UNSET_DEFAULT
    assert env.set_by.at == FIXED_NOW


def test_unset_envelope_ignores_unrelated_payload_fields():
    """The shim's derivation must not depend on any other payload fields.
    A sparse legacy row is the common case and must work.
    """
    payload = {"id": "mem_001", "content": "...", "score": 0.42}
    env = read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert env.state is LifecycleState.UNSET
    assert env.set_by.via is LifecycleSetVia.UNSET_DEFAULT


# ===========================================================================
# Category 2 -- timestamp handling
# ===========================================================================


def test_uses_provided_now_for_set_by_at():
    env = read_lifecycle_envelope({}, now=42)
    assert env.set_by.at == 42


def test_defaults_now_to_real_timestamp_when_omitted():
    """When `now` is not passed, the helper must populate `set_by.at` with
    `int(time.time())`. We sandwich the call between two wall-clock reads
    and accept any integer in [before, after] to avoid flake on slow CI.
    """
    before = int(time.time())
    env = read_lifecycle_envelope({})
    after = int(time.time())
    assert isinstance(env.set_by.at, int)
    assert env.set_by.at >= before
    assert env.set_by.at <= after


def test_now_is_ignored_when_payload_already_has_envelope():
    """A present envelope's set_by.at MUST NOT be overwritten by `now=`.
    The shim's `now` parameter only feeds the synthesized UNSET envelope.
    """
    payload = {"lifecycle_status": _live_envelope_dict()}
    env = read_lifecycle_envelope(payload, now=999_999_999)
    assert env.set_by.at == FIXED_NOW  # the embedded value, not `now`


# ===========================================================================
# Category 3 -- present envelope round-trips through the helper
# ===========================================================================


def test_returns_validated_envelope_when_present_live():
    payload = {"lifecycle_status": _live_envelope_dict()}
    env = read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert env.state is LifecycleState.RELEASED
    assert env.is_authoritative_on_row is True
    assert env.requires_join is None
    assert env.set_by.actor is LifecycleActor.OPERATOR
    assert env.set_by.via is LifecycleSetVia.RELEASE_PROMOTION


def test_returns_validated_envelope_when_present_join_required():
    payload = {"lifecycle_status": _join_required_envelope_dict()}
    env = read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert env.state is LifecycleState.REVIEW_PENDING
    assert env.is_authoritative_on_row is False
    assert env.requires_join is not None
    assert env.requires_join.side_channel is SideChannel.REVIEW_QUEUE
    assert env.requires_join.join_key == "eid"


# ===========================================================================
# Category 4 -- non-mutation guarantees
# ===========================================================================


def test_does_not_mutate_payload_when_missing():
    payload: Dict[str, Any] = {"unrelated": "data"}
    snapshot = copy.deepcopy(payload)
    read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert payload == snapshot
    assert "lifecycle_status" not in payload


def test_does_not_mutate_payload_when_value_is_none():
    payload: Dict[str, Any] = {"lifecycle_status": None, "other": 1}
    snapshot = copy.deepcopy(payload)
    read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert payload == snapshot
    assert payload["lifecycle_status"] is None


def test_does_not_mutate_payload_when_present():
    inner = _live_envelope_dict()
    inner_id = id(inner)
    payload: Dict[str, Any] = {"lifecycle_status": inner, "other": 1}
    snapshot = copy.deepcopy(payload)
    read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert payload == snapshot
    # The inner envelope dict itself must not have been swapped out.
    assert id(payload["lifecycle_status"]) == inner_id


# ===========================================================================
# Category 5 -- safety edge: malformed envelopes MUST propagate
# ===========================================================================


def test_malformed_envelope_unknown_state_propagates():
    """The keystone safety test. A present, non-null envelope that fails
    validation MUST raise; it must never be silently downgraded to UNSET.
    Silent downgrade would let a corrupt envelope masquerade as a legacy
    row, violating the Q2 invariant on read.
    """
    bad = _live_envelope_dict()
    bad["state"] = "totally_made_up"
    payload = {"lifecycle_status": bad}
    with pytest.raises(LifecycleStateError) as exc_info:
        read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert exc_info.value.field == "state"
    assert exc_info.value.reason == "unknown_value"


def test_malformed_envelope_missing_required_key_propagates():
    bad = _live_envelope_dict()
    del bad["set_by"]
    payload = {"lifecycle_status": bad}
    with pytest.raises(LifecycleStateError) as exc_info:
        read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert exc_info.value.field == "set_by"
    assert exc_info.value.reason == "missing_required_key"


def test_malformed_envelope_wrong_bool_type_propagates():
    bad = _live_envelope_dict()
    bad["is_authoritative_on_row"] = "yes"
    payload = {"lifecycle_status": bad}
    with pytest.raises(LifecycleStateError) as exc_info:
        read_lifecycle_envelope(payload, now=FIXED_NOW)
    assert exc_info.value.field == "is_authoritative_on_row"
    assert exc_info.value.reason == "must_be_bool"


@pytest.mark.parametrize("bad", ["released", 42, ["state", "released"], 1.5])
def test_envelope_that_is_not_a_dict_propagates(bad):
    """payload["lifecycle_status"] set to a non-dict, non-None value (e.g.,
    a string, list, or number) must fail validation, not coerce to UNSET.
    """
    with pytest.raises(LifecycleStateError) as exc_info:
        read_lifecycle_envelope(
            {"lifecycle_status": bad}, now=FIXED_NOW,
        )
    assert exc_info.value.field == "lifecycle_status"
    assert exc_info.value.reason == "not_a_dict"


# ===========================================================================
# Category 6 -- non-dict payload guard
# ===========================================================================


@pytest.mark.parametrize("bad", [None, 42, "row", [], (1, 2), 1.5])
def test_non_dict_payload_rejected(bad):
    with pytest.raises(LifecycleStateError) as exc_info:
        read_lifecycle_envelope(bad, now=FIXED_NOW)
    assert exc_info.value.field == "payload"
    assert exc_info.value.reason == "not_a_dict"


# ===========================================================================
# Category 7 -- shim output is itself a valid envelope
# ===========================================================================


def test_unset_envelope_round_trips_through_validator():
    """The shim must not emit special-case envelope shapes. The synthesized
    UNSET envelope must itself pass `validate_lifecycle_envelope` cleanly.
    """
    env = read_lifecycle_envelope({}, now=FIXED_NOW)
    revalidated = validate_lifecycle_envelope(env.to_dict())
    assert revalidated == env
