"""tests/test_lifecycle_authority_guard.py

Q2-F enforcement primitive tests.

This file tests ``assert_lifecycle_row_authoritative`` -- the Q2 analog of
the Q1 ``assert_authoritative_memory`` primitive. The file's naming
deliberately parallels ``tests/test_authority_guard.py`` to signal the
architectural parallel.

The primitive's contract is narrow:

    returning normally means ONE thing -- the row's lifecycle answer can
    be trusted at face value, without a side-channel join.

It does NOT mean any of:

    * the state is approved
    * the state is acceptable for any specific consumer use
    * the state has been verified beyond what the envelope itself announces

State acceptance is consumer policy. The primitive deliberately does not
editorialize about state. The most important test in this file is the
explicit trap-test that asserts a row-authoritative ``state=unset``
envelope returns ``None`` -- catching any future drift where someone
tightens the primitive to reject ``unset`` and conflates the two layers.

Out of scope for Q2-F (and these tests):

* production wiring of any decision-bearing consumer
* state-acceptance policy (per-consumer; not the primitive's concern)
* protected dual-source collapse (Q2-D)
* review-queue join formalization (Q2-E)
* baton-lifecycle resolution (R3)
* compression / cognition / closure / load-path changes
* Q3 affect-provenance, custom DB / schema work, broad refactor
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleHistoryRef,
    LifecycleJoinTarget,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStateError,
    LifecycleStatus,
    NonAuthoritativeLifecycleError,
    SideChannel,
    assert_lifecycle_row_authoritative,
    read_lifecycle_envelope,
    validate_lifecycle_envelope,
)


# ---------------------------------------------------------------------------
# Local builders
# ---------------------------------------------------------------------------


FIXED_AT = 1_716_300_000


def _set_by(
    actor: LifecycleActor = LifecycleActor.SYSTEM,
    via: LifecycleSetVia = LifecycleSetVia.INGEST_UNMARKED,
    at: int = FIXED_AT,
) -> LifecycleSetBy:
    return LifecycleSetBy(actor=actor, via=via, at=at)


def _row_authoritative(
    state: LifecycleState = LifecycleState.UNSET,
    set_by: LifecycleSetBy = None,
    history_ref: LifecycleHistoryRef = None,
) -> LifecycleStatus:
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=set_by if set_by is not None else _set_by(),
        history_ref=history_ref,
    )


def _join_required(
    state: LifecycleState = LifecycleState.REVIEW_PENDING,
    side_channel: SideChannel = SideChannel.REVIEW_QUEUE,
    join_key: str = "eid",
    set_by: LifecycleSetBy = None,
) -> LifecycleStatus:
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=False,
        requires_join=LifecycleJoinTarget(
            side_channel=side_channel, join_key=join_key,
        ),
        set_by=set_by if set_by is not None else _set_by(
            via=LifecycleSetVia.GATE1_REFUSAL,
        ),
        history_ref=None,
    )


# All states that the Q2-C decision table places in the row-authoritative
# default. REVIEW_PENDING is the only initial join-required state.
ROW_AUTHORITATIVE_STATES = [
    s for s in LifecycleState if s is not LifecycleState.REVIEW_PENDING
]


# ===========================================================================
# Category 1 -- row-authoritative envelopes return None
# ===========================================================================


@pytest.mark.parametrize("state", ROW_AUTHORITATIVE_STATES)
def test_row_authoritative_envelope_returns_none(state):
    """Every row-authoritative state in the ratified vocabulary returns
    ``None`` from the primitive -- including UNSET, RELEASED, PROTECTED,
    ACTIVE, CONSUMED, ARCHIVED, SCRATCH. The primitive does NOT
    editorialize on state value.
    """
    env = _row_authoritative(state=state)
    result = assert_lifecycle_row_authoritative(env)
    assert result is None


def test_returns_none_explicitly_not_just_no_exception():
    """Tighten the previous assertion: the primitive's return value must
    be exactly ``None``. A future change that accidentally returns the
    envelope (or anything else) should be caught here.
    """
    env = _row_authoritative(state=LifecycleState.RELEASED,
                              set_by=_set_by(via=LifecycleSetVia.RELEASE_PROMOTION,
                                              actor=LifecycleActor.OPERATOR))
    result = assert_lifecycle_row_authoritative(env)
    assert result is None
    # And the envelope itself was not somehow returned or mutated by reference.
    assert env.state is LifecycleState.RELEASED


# ===========================================================================
# Category 2 -- join-required envelopes raise NonAuthoritativeLifecycleError
# ===========================================================================


@pytest.mark.parametrize("side_channel", list(SideChannel))
def test_join_required_envelope_raises_for_each_side_channel(side_channel):
    """A non-row-authoritative envelope raises regardless of which side
    channel is named. All three side channels exercise the same code
    path; this confirms none of them slip through.
    """
    env = _join_required(side_channel=side_channel, join_key="eid")
    with pytest.raises(NonAuthoritativeLifecycleError) as exc_info:
        assert_lifecycle_row_authoritative(env)
    assert exc_info.value.side_channel == side_channel.value


def test_join_required_error_carries_diagnostic_attributes():
    env = _join_required(state=LifecycleState.REVIEW_PENDING,
                          side_channel=SideChannel.REVIEW_QUEUE,
                          join_key="some_specific_join_key")
    with pytest.raises(NonAuthoritativeLifecycleError) as exc_info:
        assert_lifecycle_row_authoritative(env)
    err = exc_info.value
    assert err.state == "review_pending"
    assert err.side_channel == "review_queue"
    assert err.join_key == "some_specific_join_key"


def test_join_required_error_message_names_state_channel_and_key():
    """The error's str(...) form should carry enough information that an
    operator reading a log line can pivot directly to the right side
    channel + key.
    """
    env = _join_required(state=LifecycleState.REVIEW_PENDING,
                          side_channel=SideChannel.REVIEW_QUEUE,
                          join_key="log_message_join_key")
    with pytest.raises(NonAuthoritativeLifecycleError) as exc_info:
        assert_lifecycle_row_authoritative(env)
    message = str(exc_info.value)
    assert "review_pending" in message
    assert "review_queue" in message
    assert "log_message_join_key" in message


def test_join_required_error_inherits_from_type_error():
    """Mirror of Q1's NonAuthoritativeMemoryError(TypeError). This is a
    contract violation: caller passed a structurally valid but
    non-row-authoritative envelope where a row-authoritative one was
    required. ValueError-class is reserved for LifecycleStateError
    (malformed envelope -- a data problem).
    """
    env = _join_required()
    with pytest.raises(TypeError):
        assert_lifecycle_row_authoritative(env)


# ===========================================================================
# Category 3 -- malformed envelope dicts raise LifecycleStateError
# ===========================================================================


def test_malformed_unknown_state_raises_lifecycle_state_error():
    """Malformed envelope must propagate as LifecycleStateError -- NOT
    silently downgrade to NonAuthoritativeLifecycleError or to UNSET.
    The two error categories must stay distinct.
    """
    bad = _row_authoritative().to_dict()
    bad["state"] = "totally_made_up"
    with pytest.raises(LifecycleStateError) as exc_info:
        assert_lifecycle_row_authoritative(bad)
    assert exc_info.value.field == "state"
    assert exc_info.value.reason == "unknown_value"


def test_malformed_missing_required_key_raises_lifecycle_state_error():
    bad = _row_authoritative().to_dict()
    del bad["set_by"]
    with pytest.raises(LifecycleStateError) as exc_info:
        assert_lifecycle_row_authoritative(bad)
    assert exc_info.value.field == "set_by"
    assert exc_info.value.reason == "missing_required_key"


def test_malformed_wrong_bool_type_raises_lifecycle_state_error():
    bad = _row_authoritative().to_dict()
    bad["is_authoritative_on_row"] = "yes"  # string, not bool
    with pytest.raises(LifecycleStateError) as exc_info:
        assert_lifecycle_row_authoritative(bad)
    assert exc_info.value.field == "is_authoritative_on_row"
    assert exc_info.value.reason == "must_be_bool"


def test_malformed_does_not_raise_non_authoritative_error():
    """Distinct error paths: a malformed envelope is a data problem
    (LifecycleStateError / ValueError). Non-authoritativity is a
    contract problem (NonAuthoritativeLifecycleError / TypeError).
    The two MUST stay separable.
    """
    bad = _row_authoritative().to_dict()
    bad["state"] = "totally_made_up"
    with pytest.raises(LifecycleStateError):
        assert_lifecycle_row_authoritative(bad)
    # Re-run and confirm we don't catch under the wrong type.
    with pytest.raises(LifecycleStateError):
        assert_lifecycle_row_authoritative(bad)
    # Specifically NOT a NonAuthoritativeLifecycleError
    try:
        assert_lifecycle_row_authoritative(bad)
    except NonAuthoritativeLifecycleError:
        pytest.fail(
            "Malformed envelope must NOT raise NonAuthoritativeLifecycleError"
        )
    except LifecycleStateError:
        pass  # expected


# ===========================================================================
# Category 4 -- non-dict, non-LifecycleStatus inputs raise
# ===========================================================================


@pytest.mark.parametrize("bad_input", [42, "released", 1.5, ["state"], (1, 2),
                                         object()])
def test_non_envelope_input_raises_lifecycle_state_error(bad_input):
    with pytest.raises(LifecycleStateError) as exc_info:
        assert_lifecycle_row_authoritative(bad_input)
    assert exc_info.value.field == "envelope"
    assert exc_info.value.reason == "invalid_type"


# ===========================================================================
# Category 5 -- direct None input is rejected
# ===========================================================================


def test_none_input_rejected_with_clear_field_reason():
    """None is a missing-envelope sentinel; callers with a payload should
    run read_lifecycle_envelope first. Passing None directly is a
    programming error.
    """
    with pytest.raises(LifecycleStateError) as exc_info:
        assert_lifecycle_row_authoritative(None)
    assert exc_info.value.field == "envelope"
    assert exc_info.value.reason == "must_not_be_none"


# ===========================================================================
# Category 6 -- dict and typed input produce equivalent outcomes
# ===========================================================================


def test_dict_and_typed_input_both_return_none_for_row_authoritative():
    """Both input shapes succeed equivalently when the envelope is
    row-authoritative.
    """
    env = _row_authoritative(state=LifecycleState.RELEASED,
                              set_by=_set_by(via=LifecycleSetVia.RELEASE_PROMOTION,
                                              actor=LifecycleActor.OPERATOR))
    typed_result = assert_lifecycle_row_authoritative(env)
    dict_result = assert_lifecycle_row_authoritative(env.to_dict())
    assert typed_result is None
    assert dict_result is None


def test_dict_and_typed_input_both_raise_for_join_required():
    env = _join_required()
    with pytest.raises(NonAuthoritativeLifecycleError) as typed_exc:
        assert_lifecycle_row_authoritative(env)
    with pytest.raises(NonAuthoritativeLifecycleError) as dict_exc:
        assert_lifecycle_row_authoritative(env.to_dict())
    # Same diagnostic facts for both paths.
    assert typed_exc.value.state == dict_exc.value.state
    assert typed_exc.value.side_channel == dict_exc.value.side_channel
    assert typed_exc.value.join_key == dict_exc.value.join_key


# ===========================================================================
# Category 7 -- the explicit trap test
# ===========================================================================


def test_unset_state_is_row_authoritative_and_does_not_raise():
    """The most important test in this file.

    A row-authoritative ``state=unset`` envelope MUST return ``None``.
    The primitive ONLY asserts row-authoritativity; it does NOT
    editorialize on state value. If a future change adds e.g.
    ``if env.state is LifecycleState.UNSET: raise``, that would conflate
    two distinct layers:

        Layer 1 (the primitive):  "is the row's answer trustworthy?"
        Layer 2 (consumer policy): "is the answer's state acceptable?"

    Mixing those layers is the failure mode this test exists to catch.
    A consumer that wants to reject UNSET should write:

        assert_lifecycle_row_authoritative(env)         # Q2-F
        if env.state is LifecycleState.UNSET:           # consumer policy
            raise MyConsumerPolicyError(...)
    """
    # H1a shim default shape (legacy row)
    env_shim = _row_authoritative(
        state=LifecycleState.UNSET,
        set_by=_set_by(actor=LifecycleActor.MIGRATION,
                       via=LifecycleSetVia.UNSET_DEFAULT),
    )
    assert assert_lifecycle_row_authoritative(env_shim) is None

    # H1c stamped shape (new row)
    env_stamp = _row_authoritative(
        state=LifecycleState.UNSET,
        set_by=_set_by(actor=LifecycleActor.SYSTEM,
                       via=LifecycleSetVia.INGEST_UNMARKED),
    )
    assert assert_lifecycle_row_authoritative(env_stamp) is None


# ===========================================================================
# Category 8 -- negative-guard framing
# ===========================================================================


def test_returning_normally_does_not_certify_state_acceptance():
    """The primitive's contract is *narrow*: returning normally means the
    row is authoritative for its lifecycle answer. It does NOT certify
    the state is approved, released, safe, or acceptable for any
    consumer use.

    We verify this by showing the primitive returns ``None`` for every
    row-authoritative state regardless of how "acceptable" the state
    might be in some consumer's policy:

      * UNSET     -- the H1c default; absolutely not "approved"
      * SCRATCH   -- preliminary; not approved
      * RELEASED  -- approved-feeling, but the primitive doesn't claim so
      * PROTECTED -- approved-feeling, but the primitive doesn't claim so
      * CONSUMED  -- terminal; not "safe for fresh use"
      * ARCHIVED  -- removed from active surfaces; not "fresh"

    All of them return None. State acceptability is per-consumer policy.
    """
    for state in (
        LifecycleState.UNSET,
        LifecycleState.SCRATCH,
        LifecycleState.RELEASED,
        LifecycleState.PROTECTED,
        LifecycleState.CONSUMED,
        LifecycleState.ARCHIVED,
        LifecycleState.ACTIVE,
    ):
        env = _row_authoritative(state=state)
        assert assert_lifecycle_row_authoritative(env) is None, (
            f"primitive editorialized on state={state.value!r}; this is "
            f"a regression -- state acceptance is consumer policy, not "
            f"the primitive's responsibility"
        )


# ===========================================================================
# Category 9 -- integration with the H1a read shim
# ===========================================================================


def test_legacy_payload_through_shim_then_primitive_returns_none():
    """Cross-slice composition: legacy payload → H1a shim → primitive
    returns None. The shim's job is to make legacy rows row-authoritative
    by deriving UNSET; the primitive trusts that and returns None.
    """
    legacy_payload: Dict[str, Any] = {"text": "legacy row, no envelope"}
    env = read_lifecycle_envelope(legacy_payload, now=FIXED_AT)
    # Shim derived UNSET; should be row-authoritative.
    assert env.is_authoritative_on_row is True
    assert env.state is LifecycleState.UNSET
    # Primitive returns None for this shim-derived envelope.
    assert assert_lifecycle_row_authoritative(env) is None


def test_explicit_none_payload_through_shim_then_primitive_returns_none():
    payload: Dict[str, Any] = {"lifecycle_status": None}
    env = read_lifecycle_envelope(payload, now=FIXED_AT)
    assert env.state is LifecycleState.UNSET
    assert assert_lifecycle_row_authoritative(env) is None


# ===========================================================================
# Category 10 -- integration with the H1c stamped payload
# ===========================================================================


def test_h1c_stamped_payload_through_primitive_returns_none():
    """Cross-slice composition: a payload stamped by the H1c write-site
    helper passes the Q2-F primitive cleanly. The whole Slice 0 → H1a
    → H1c → Q2-F chain composes.
    """
    try:
        from torment_service.memory_graph import _ensure_lifecycle_envelope
    except ImportError as exc:
        pytest.skip(f"memory_graph import unavailable: {exc}")
    payload: Dict[str, Any] = {"text": "fresh row"}
    _ensure_lifecycle_envelope(payload)
    env = read_lifecycle_envelope(payload)
    # H1c stamped, so row-authoritative UNSET with the SYSTEM/INGEST_UNMARKED
    # shape (distinct from the shim's MIGRATION/UNSET_DEFAULT).
    assert env.is_authoritative_on_row is True
    assert env.set_by.via is LifecycleSetVia.INGEST_UNMARKED
    assert assert_lifecycle_row_authoritative(env) is None


# ===========================================================================
# Category 11 -- corrupt present envelope through primitive raises
# LifecycleStateError, NOT NonAuthoritativeLifecycleError
# ===========================================================================


def test_corrupt_envelope_dict_through_primitive_raises_lifecycle_state_error():
    """A payload carrying a corrupt envelope, passed as a dict to the
    primitive directly, must raise LifecycleStateError (data problem),
    NOT NonAuthoritativeLifecycleError (contract problem). The error
    categories remain distinct.
    """
    corrupt = _row_authoritative().to_dict()
    corrupt["state"] = "totally_made_up"
    with pytest.raises(LifecycleStateError) as exc_info:
        assert_lifecycle_row_authoritative(corrupt)
    assert exc_info.value.field == "state"
    assert exc_info.value.reason == "unknown_value"


def test_corrupt_envelope_does_not_become_authoritative_or_join_required():
    """Extra guard: a corrupt envelope must not slip past the primitive
    in either direction -- not as a silent pass (treating UNSET-ish
    shape as row-authoritative) and not as a NonAuthoritativeLifecycle
    raise (which would imply the validator accepted the shape).
    """
    corrupt = {
        "state": "bogus",
        "is_authoritative_on_row": True,
        "requires_join": None,
        "set_by": {"actor": "operator", "via": "api", "at": 1},
        "history_ref": None,
    }
    # Must raise LifecycleStateError, not NonAuthoritativeLifecycleError,
    # and not return None.
    with pytest.raises(LifecycleStateError):
        assert_lifecycle_row_authoritative(corrupt)
