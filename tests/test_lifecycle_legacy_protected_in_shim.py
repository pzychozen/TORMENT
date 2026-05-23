"""tests/test_lifecycle_legacy_protected_in_shim.py

Q2-D Slice 2 tests: the H1a read shim now composes with the Q2-D Slice 1
derivation helper to recognize legacy protected markers on rows that
pre-date the Q2 lifecycle envelope.

After this slice, ``read_lifecycle_envelope`` has three branches:

  1. Non-dict payload          → raise LifecycleStateError
  2. Present non-null envelope → validate-and-return (explicit wins)
  3. Absent or explicit None
     a. legacy protected markers present → derived PROTECTED envelope
     b. otherwise                         → canonical UNSET envelope

This file tests the composition. The Slice 1 derivation helper is tested
in isolation in ``tests/test_protected_lifecycle_derivation.py``; the
existing H1a shim contract is tested in
``tests/test_lifecycle_migration_shim.py`` (zero changes required there
because the existing tests use payloads without protected markers).

Hard scope (also encoded in test assertions where relevant):

* explicit envelope wins over legacy markers in this slice; disagreement
  detection is Slice 4.
* H1c write stamp is unchanged; new rows with legacy protected markers
  but no explicit envelope still get stamped UNSET at write time
  (Hazard B remains, Slice 3 fixes).
* no protected reader migration; no compression/governance behavior
  change.
"""
from __future__ import annotations

import copy
import os
import sys
import time
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
    SideChannel,
    assert_lifecycle_row_authoritative,
    read_lifecycle_envelope,
    validate_lifecycle_envelope,
)


FIXED_AT = 1_716_300_000


def _explicit_envelope_dict(
    state: LifecycleState = LifecycleState.RELEASED,
    via: LifecycleSetVia = LifecycleSetVia.RELEASE_PROMOTION,
    actor: LifecycleActor = LifecycleActor.OPERATOR,
) -> Dict[str, Any]:
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(actor=actor, via=via, at=FIXED_AT),
        history_ref=None,
    ).to_dict()


def _join_required_envelope_dict() -> Dict[str, Any]:
    return LifecycleStatus(
        state=LifecycleState.REVIEW_PENDING,
        is_authoritative_on_row=False,
        requires_join=LifecycleJoinTarget(
            side_channel=SideChannel.REVIEW_QUEUE, join_key="eid",
        ),
        set_by=LifecycleSetBy(
            actor=LifecycleActor.MIGRATION,
            via=LifecycleSetVia.GATE1_REFUSAL,
            at=FIXED_AT,
        ),
        history_ref=None,
    ).to_dict()


# ===========================================================================
# Section A -- marker matrix: each legacy marker on a payload with no
# explicit envelope produces a PROTECTED envelope via the shim.
# ===========================================================================


# (label, payload, expected_via)
MARKER_CASES = [
    ("canon_true", {"canon": True}, "canon_set"),
    ("kind_seed", {"kind": "seed"}, "seed_plant"),
    ("kind_identity", {"kind": "identity"}, "seed_plant"),
    ("kind_core_identity", {"kind": "core_identity"}, "seed_plant"),
    ("tier_core_identity", {"tier": "core_identity"}, "tier_set"),
    ("srg_is_crystal_true",
     {"srg": {"is_crystal": True}}, "srg_crystal"),
    ("governance_protected_true",
     {"governance": {"protected": True}}, "governance_flag"),
]


@pytest.mark.parametrize("label,payload,expected_via", MARKER_CASES)
def test_legacy_marker_alone_yields_protected_through_shim(
    label, payload, expected_via,
):
    """Section A core: each marker on a payload with no explicit envelope
    produces a row-authoritative PROTECTED envelope via the shim, with
    ``actor=MIGRATION`` (read-time interpretation) and the
    marker-specific via.
    """
    env = read_lifecycle_envelope(payload, now=FIXED_AT)
    assert env.state is LifecycleState.PROTECTED, (
        f"{label!r} should yield PROTECTED via shim"
    )
    assert env.is_authoritative_on_row is True
    assert env.requires_join is None
    assert env.history_ref is None
    assert env.set_by.actor is LifecycleActor.MIGRATION
    assert env.set_by.via.value == expected_via
    assert env.set_by.at == FIXED_AT


# ===========================================================================
# Section B -- non-protected and explicit-envelope behavior
# ===========================================================================


def test_no_marker_no_envelope_still_yields_canonical_unset():
    """H1a guarantee preserved: a payload with neither a lifecycle envelope
    nor any legacy protected marker still produces the canonical
    ``MIGRATION / UNSET_DEFAULT`` envelope. This is the regression
    guard that proves Slice 2 only intervenes when derivation matches.
    """
    env = read_lifecycle_envelope({}, now=FIXED_AT)
    assert env.state is LifecycleState.UNSET
    assert env.is_authoritative_on_row is True
    assert env.set_by.actor is LifecycleActor.MIGRATION
    assert env.set_by.via is LifecycleSetVia.UNSET_DEFAULT
    assert env.set_by.at == FIXED_AT


def test_no_marker_no_envelope_with_unrelated_fields_yields_unset():
    payload = {"text": "ordinary memory", "step": 7,
                "summary": "nothing protected", "half_life": 30}
    env = read_lifecycle_envelope(payload, now=FIXED_AT)
    assert env.state is LifecycleState.UNSET
    assert env.set_by.via is LifecycleSetVia.UNSET_DEFAULT


def test_explicit_none_lifecycle_status_can_derive_protected():
    """Missing-key and explicit-``None`` remain equivalent. Both go
    through the derivation-then-UNSET path, so a payload with
    ``lifecycle_status=None`` AND ``canon=True`` still derives
    PROTECTED, just like the missing-key case.
    """
    payload = {"canon": True, "lifecycle_status": None}
    env = read_lifecycle_envelope(payload, now=FIXED_AT)
    assert env.state is LifecycleState.PROTECTED
    assert env.set_by.via is LifecycleSetVia.CANON_SET


def test_explicit_valid_row_authoritative_envelope_wins_over_legacy_markers():
    """Slice 2 boundary lock: when a payload carries an explicit valid
    envelope AND legacy protected markers that would derive a different
    state, the explicit envelope wins silently. Disagreement detection
    is Q2-D Slice 4; this slice does NOT warn or log.
    """
    explicit = _explicit_envelope_dict(state=LifecycleState.RELEASED)
    payload = {"canon": True, "lifecycle_status": explicit}
    env = read_lifecycle_envelope(payload, now=FIXED_AT)
    # The explicit envelope wins; canon is ignored.
    assert env.state is LifecycleState.RELEASED
    assert env.set_by.via is LifecycleSetVia.RELEASE_PROMOTION
    assert env.set_by.actor is LifecycleActor.OPERATOR
    # The embedded set_by.at is preserved (no clock rewrite).
    assert env.set_by.at == FIXED_AT


def test_explicit_valid_join_required_envelope_wins_over_legacy_markers():
    """The explicit-wins rule applies to non-row-authoritative envelopes
    too. A row whose explicit envelope says REVIEW_PENDING with a
    review-queue join is returned verbatim, even if it also carries
    canon=True.
    """
    explicit = _join_required_envelope_dict()
    payload = {"canon": True, "lifecycle_status": explicit}
    env = read_lifecycle_envelope(payload, now=FIXED_AT)
    assert env.state is LifecycleState.REVIEW_PENDING
    assert env.is_authoritative_on_row is False
    assert env.requires_join is not None
    assert env.requires_join.side_channel is SideChannel.REVIEW_QUEUE


def test_explicit_malformed_envelope_raises_does_not_fall_back_to_derivation():
    """The keystone Slice 2 safety check. A malformed explicit envelope
    on a payload that ALSO carries legacy protected markers must raise
    -- the shim does NOT silently route past the corrupt envelope into
    the derivation branch. Loud failure stays loud; the H1a corruption
    contract is preserved end-to-end through Slice 2.
    """
    bad = _explicit_envelope_dict()
    bad["state"] = "totally_made_up"
    payload = {"canon": True, "lifecycle_status": bad}
    with pytest.raises(LifecycleStateError) as exc_info:
        read_lifecycle_envelope(payload, now=FIXED_AT)
    assert exc_info.value.field == "state"
    assert exc_info.value.reason == "unknown_value"


def test_explicit_envelope_set_to_non_dict_raises_does_not_derive():
    """A payload with lifecycle_status set to a non-dict (e.g. a string)
    must raise via the validator, not fall through to derivation.
    """
    payload = {"canon": True, "lifecycle_status": "released"}
    with pytest.raises(LifecycleStateError) as exc_info:
        read_lifecycle_envelope(payload, now=FIXED_AT)
    assert exc_info.value.field == "lifecycle_status"
    assert exc_info.value.reason == "not_a_dict"


# ===========================================================================
# Section C -- timestamp handling on both branches
# ===========================================================================


def test_now_is_honored_on_derived_protected_branch():
    env = read_lifecycle_envelope({"canon": True}, now=42)
    assert env.set_by.at == 42


def test_now_is_honored_on_unset_fallback_branch():
    env = read_lifecycle_envelope({}, now=42)
    assert env.set_by.at == 42


def test_default_now_window_on_derived_protected_branch():
    before = int(time.time())
    env = read_lifecycle_envelope({"canon": True})
    after = int(time.time())
    assert isinstance(env.set_by.at, int)
    assert env.set_by.at >= before
    assert env.set_by.at <= after


def test_default_now_window_on_unset_fallback_branch():
    before = int(time.time())
    env = read_lifecycle_envelope({})
    after = int(time.time())
    assert isinstance(env.set_by.at, int)
    assert env.set_by.at >= before
    assert env.set_by.at <= after


# ===========================================================================
# Section D -- payload is never mutated, in either branch
# ===========================================================================


def test_payload_not_mutated_on_derived_protected_branch():
    payload: Dict[str, Any] = {"canon": True, "text": "x"}
    snapshot = copy.deepcopy(payload)
    read_lifecycle_envelope(payload, now=FIXED_AT)
    assert payload == snapshot
    assert "lifecycle_status" not in payload


def test_payload_not_mutated_on_unset_fallback_branch():
    payload: Dict[str, Any] = {"text": "x", "step": 1}
    snapshot = copy.deepcopy(payload)
    read_lifecycle_envelope(payload, now=FIXED_AT)
    assert payload == snapshot
    assert "lifecycle_status" not in payload


def test_payload_not_mutated_when_explicit_envelope_wins():
    explicit = _explicit_envelope_dict()
    inner_id = id(explicit)
    payload: Dict[str, Any] = {"canon": True, "lifecycle_status": explicit}
    snapshot = copy.deepcopy(payload)
    read_lifecycle_envelope(payload, now=FIXED_AT)
    assert payload == snapshot
    # The inner envelope dict's identity is unchanged (not swapped out).
    assert id(payload["lifecycle_status"]) == inner_id


# ===========================================================================
# Section E -- cross-slice composition: Q2-D derivation + Q2-F primitive
# ===========================================================================


@pytest.mark.parametrize("label,payload,expected_via", MARKER_CASES)
def test_derived_protected_envelope_passes_q2f_primitive(
    label, payload, expected_via,
):
    """Cross-slice: the envelope returned by the shim on the derived
    PROTECTED branch is row-authoritative, so the Q2-F primitive
    returns ``None`` for it. Confirms Q2-D Slice 2 + Q2-F compose
    cleanly: a legacy protected row can be passed through the
    enforcement guard with no surprises.
    """
    env = read_lifecycle_envelope(payload, now=FIXED_AT)
    assert assert_lifecycle_row_authoritative(env) is None


@pytest.mark.parametrize("label,payload,expected_via", MARKER_CASES)
def test_derived_protected_envelope_revalidates_cleanly(
    label, payload, expected_via,
):
    """Cross-slice: the envelope returned by the shim re-validates
    through ``validate_lifecycle_envelope``. No special-case shapes
    leak from the derivation-via-shim path.
    """
    env = read_lifecycle_envelope(payload, now=FIXED_AT)
    revalidated = validate_lifecycle_envelope(env.to_dict())
    assert revalidated == env


# ===========================================================================
# Section F -- H1b inspector regression: legacy protected rows now surface
# as PROTECTED rather than shim UNSET when read through resource_provenance.
# ===========================================================================


def test_h1b_lifecycle_field_helper_surfaces_protected_for_legacy_canon():
    """The operator-visible payoff of Slice 2: when the H1b
    ``_lifecycle_field_for_payload`` helper (used inside the
    ``resource_provenance`` MCP resource) processes a legacy payload
    with ``canon=True`` and no envelope, it now surfaces
    ``state="protected"`` / ``via="canon_set"`` instead of
    ``state="unset"`` / ``via="unset_default"``.

    This is the cross-slice regression test that catches silent removal
    of the Q2-D Slice 2 wiring inside the shim.
    """
    try:
        from torment_service.mcp_server import _lifecycle_field_for_payload
    except ImportError as exc:
        pytest.skip(f"mcp_server import unavailable: {exc}")

    payload = {"canon": True, "summary": "legacy protected row"}
    surfaced = _lifecycle_field_for_payload(payload)
    assert "error" not in surfaced
    assert surfaced["state"] == "protected"
    assert surfaced["set_by"]["actor"] == "migration"
    assert surfaced["set_by"]["via"] == "canon_set"
    # And explicitly: this is NOT the H1a shim's pure-UNSET shape.
    assert surfaced["set_by"]["via"] != "unset_default"
