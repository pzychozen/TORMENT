"""tests/test_lifecycle_legacy_marker_disagreement.py

Q2-D Slice 4 tests for ``detect_lifecycle_legacy_marker_disagreement``.

This file tests the disagreement detector in isolation. The helper
defines the law for when an explicit lifecycle envelope and the
protected derivation from legacy markers conflict on load-bearing
facts. Production wiring (H1b inspector enrichment, write-side
raising, reader migration) is deferred to later separately-ratified
slices.

Two disagreement kinds at this slice:

  STATE_MISMATCH       -- explicit state != PROTECTED, legacy markers
                          derive PROTECTED.
  AUTHORITY_MISMATCH   -- explicit state == PROTECTED, but explicit
                          envelope is NOT row-authoritative (announces
                          a side-channel join), while legacy markers
                          derive a row-authoritative PROTECTED.

Deliberately NOT a disagreement at this slice:

  PROVENANCE_DRIFT     -- both sides agree on state=PROTECTED row-auth
                          but ``set_by.via`` differs. Both sides agree
                          on load-bearing facts; via differences are
                          audit-interesting but not decision-bearing.

  actor differences    -- Slice 3 deliberately introduced MIGRATION vs
                          SYSTEM as an audit feature; not a conflict.

Out of scope for Slice 4 (and these tests):

* production wiring of any consumer
* H1b inspector field enrichment
* write-side raising on disagreement
* reader migration (governance.is_compression_protected,
  compression.derive_retention_tier)
* retroactive disk scan
* baton/R3, review-queue, closure-ledger, Q3, custom DB
"""
from __future__ import annotations

import copy
import os
import sys
from typing import Any, Dict, Optional

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleDisagreementKind,
    LifecycleHistoryRef,
    LifecycleJoinTarget,
    LifecycleLegacyMarkerDisagreement,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStateError,
    LifecycleStatus,
    SideChannel,
    derive_protected_lifecycle_from_legacy_markers,
    detect_lifecycle_legacy_marker_disagreement,
    read_lifecycle_envelope,
)


FIXED_AT = 1_716_300_000


# ---------------------------------------------------------------------------
# Local builders
# ---------------------------------------------------------------------------


def _row_authoritative_envelope_dict(
    state: LifecycleState,
    via: LifecycleSetVia,
    actor: LifecycleActor = LifecycleActor.SYSTEM,
    at: int = FIXED_AT,
) -> Dict[str, Any]:
    """Build a row-authoritative envelope dict at any state."""
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(actor=actor, via=via, at=at),
        history_ref=None,
    ).to_dict()


def _join_required_envelope_dict(
    state: LifecycleState = LifecycleState.REVIEW_PENDING,
    side_channel: SideChannel = SideChannel.REVIEW_QUEUE,
    join_key: str = "eid",
    via: LifecycleSetVia = LifecycleSetVia.GATE1_REFUSAL,
    actor: LifecycleActor = LifecycleActor.SYSTEM,
    at: int = FIXED_AT,
) -> Dict[str, Any]:
    """Build a join-required envelope dict (is_authoritative_on_row=False)."""
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=False,
        requires_join=LifecycleJoinTarget(
            side_channel=side_channel, join_key=join_key,
        ),
        set_by=LifecycleSetBy(actor=actor, via=via, at=at),
        history_ref=None,
    ).to_dict()


# ===========================================================================
# Section A -- no disagreement when no comparison is possible
# ===========================================================================


def test_returns_none_when_no_explicit_envelope():
    """No explicit envelope on the payload -> nothing to compare against
    legacy markers. Returns None even when legacy markers are present.
    """
    result = detect_lifecycle_legacy_marker_disagreement({"canon": True})
    assert result is None


def test_returns_none_when_explicit_lifecycle_status_is_none():
    """Explicit ``lifecycle_status=None`` is equivalent to missing (per
    H1a / Slice 2 ergonomics). Still no envelope to disagree with.
    """
    payload = {"lifecycle_status": None, "canon": True}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is None


def test_returns_none_when_no_legacy_protected_marker():
    """Explicit valid envelope present but no legacy protected marker
    on the payload -> no disagreement possible. Returns None for any
    explicit state.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
        actor=LifecycleActor.OPERATOR,
    )
    payload = {"lifecycle_status": explicit, "text": "ordinary memory"}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is None


# ===========================================================================
# Section B -- error and safety edges
# ===========================================================================


def test_malformed_explicit_envelope_raises_lifecycle_state_error():
    """A malformed explicit envelope must propagate via the validator,
    NOT be swallowed into a disagreement report. Corruption stays
    loud across the entire Q2 surface.
    """
    bad = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
    )
    bad["state"] = "totally_made_up"
    payload = {"lifecycle_status": bad, "canon": True}
    with pytest.raises(LifecycleStateError) as exc_info:
        detect_lifecycle_legacy_marker_disagreement(payload)
    assert exc_info.value.field == "state"
    assert exc_info.value.reason == "unknown_value"


def test_non_dict_lifecycle_status_raises_via_validator():
    """``lifecycle_status`` set to a non-dict (e.g. a string) raises
    through the validator, not coerced to a disagreement.
    """
    payload = {"lifecycle_status": "released", "canon": True}
    with pytest.raises(LifecycleStateError) as exc_info:
        detect_lifecycle_legacy_marker_disagreement(payload)
    assert exc_info.value.field == "lifecycle_status"
    assert exc_info.value.reason == "not_a_dict"


@pytest.mark.parametrize("bad_payload",
                          [None, 42, "row", [], (1, 2), 1.5])
def test_non_dict_payload_raises_lifecycle_state_error(bad_payload):
    with pytest.raises(LifecycleStateError) as exc_info:
        detect_lifecycle_legacy_marker_disagreement(bad_payload)
    assert exc_info.value.field == "payload"
    assert exc_info.value.reason == "not_a_dict"


# ===========================================================================
# Section C -- STATE_MISMATCH for each non-PROTECTED state + canon=True
# ===========================================================================


NON_PROTECTED_ROW_AUTHORITATIVE_STATES = [
    (LifecycleState.UNSET, LifecycleSetVia.UNSET_DEFAULT),
    (LifecycleState.SCRATCH, LifecycleSetVia.SCRATCH_PROMOTION),
    (LifecycleState.RELEASED, LifecycleSetVia.RELEASE_PROMOTION),
    (LifecycleState.ACTIVE, LifecycleSetVia.API),
    (LifecycleState.CONSUMED, LifecycleSetVia.BATON_CONSUME),
    (LifecycleState.ARCHIVED, LifecycleSetVia.API),
]


@pytest.mark.parametrize("state,via", NON_PROTECTED_ROW_AUTHORITATIVE_STATES)
def test_state_mismatch_for_row_authoritative_non_protected_state(state, via):
    """For each non-PROTECTED row-authoritative state, explicit envelope
    at that state plus ``canon=True`` (legacy derives PROTECTED) yields
    STATE_MISMATCH.
    """
    explicit = _row_authoritative_envelope_dict(state=state, via=via)
    payload = {"lifecycle_status": explicit, "canon": True}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is not None
    assert result.kind is LifecycleDisagreementKind.STATE_MISMATCH
    assert result.explicit_state is state
    assert result.explicit_is_authoritative_on_row is True
    assert result.explicit_via is via
    assert result.derived_via is LifecycleSetVia.CANON_SET


def test_state_mismatch_for_review_pending_join_required():
    """REVIEW_PENDING + canon=True -- STATE_MISMATCH (not
    AUTHORITY_MISMATCH). The classification is "explicit state is not
    PROTECTED" first; the authoritativity of the explicit envelope is
    a secondary fact recorded on the disagreement object.
    """
    explicit = _join_required_envelope_dict(
        state=LifecycleState.REVIEW_PENDING,
        side_channel=SideChannel.REVIEW_QUEUE,
        via=LifecycleSetVia.GATE1_REFUSAL,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is not None
    assert result.kind is LifecycleDisagreementKind.STATE_MISMATCH
    assert result.explicit_state is LifecycleState.REVIEW_PENDING
    assert result.explicit_is_authoritative_on_row is False
    assert result.derived_via is LifecycleSetVia.CANON_SET


# ===========================================================================
# Section D -- AUTHORITY_MISMATCH for PROTECTED + non-row-auth + marker
# ===========================================================================


def test_authority_mismatch_protected_review_queue_join_required():
    """Explicit PROTECTED but join-required via REVIEW_QUEUE, plus
    canon=True -> AUTHORITY_MISMATCH. Legacy markers derive
    row-authoritative PROTECTED; explicit announces a side-channel join.
    """
    explicit = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
        side_channel=SideChannel.REVIEW_QUEUE,
        via=LifecycleSetVia.GATE1_REFUSAL,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is not None
    assert result.kind is LifecycleDisagreementKind.AUTHORITY_MISMATCH
    assert result.explicit_state is LifecycleState.PROTECTED
    assert result.explicit_is_authoritative_on_row is False
    assert result.explicit_via is LifecycleSetVia.GATE1_REFUSAL
    assert result.derived_via is LifecycleSetVia.CANON_SET


def test_authority_mismatch_protected_closure_ledger_join_required():
    """Same AUTHORITY_MISMATCH classification regardless of which side
    channel the explicit envelope names.
    """
    explicit = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
        side_channel=SideChannel.CLOSURE_LEDGER,
        join_key="closure_id",
        via=LifecycleSetVia.GOVERNANCE_FLAG,
    )
    payload = {"lifecycle_status": explicit, "tier": "core_identity"}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is not None
    assert result.kind is LifecycleDisagreementKind.AUTHORITY_MISMATCH
    assert result.explicit_state is LifecycleState.PROTECTED
    assert result.explicit_is_authoritative_on_row is False
    assert result.derived_via is LifecycleSetVia.TIER_SET


def test_authority_mismatch_protected_baton_ledger_join_required():
    explicit = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
        side_channel=SideChannel.BATON_LEDGER,
        join_key="baton_id",
        via=LifecycleSetVia.BATON_CONSUME,
    )
    payload = {
        "lifecycle_status": explicit,
        "governance": {"protected": True},
    }
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is not None
    assert result.kind is LifecycleDisagreementKind.AUTHORITY_MISMATCH
    assert result.derived_via is LifecycleSetVia.GOVERNANCE_FLAG


# ===========================================================================
# Section E -- full agreement and provenance drift both return None
# ===========================================================================


def test_full_agreement_returns_none():
    """Explicit PROTECTED row-authoritative via=CANON_SET + canon=True
    -- both sides agree completely. No disagreement.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.CANON_SET,
        actor=LifecycleActor.MIGRATION,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is None


def test_provenance_drift_returns_none_via_differs():
    """Both sides agree on state=PROTECTED row-authoritative, but
    ``set_by.via`` differs (explicit=SCRATCH_PROMOTION vs derived
    legacy via=CANON_SET). NOT surfaced at Slice 4. Both sides agree
    on the load-bearing facts.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.SCRATCH_PROMOTION,
        actor=LifecycleActor.OPERATOR,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is None


def test_provenance_drift_returns_none_actor_differs():
    """Slice 3 deliberately introduced MIGRATION (read-side) vs SYSTEM
    (write-side) as an audit feature. The detector ignores actor
    differences entirely. Even when actor differs alongside same
    state+authority, no disagreement is reported.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.CANON_SET,
        actor=LifecycleActor.SYSTEM,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    # The derivation helper uses actor=MIGRATION by default; the
    # explicit envelope uses actor=SYSTEM. Both agree on state +
    # authority. No disagreement.
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is None


# ===========================================================================
# Section F -- STATE_MISMATCH detected across every legacy marker source
# ===========================================================================


MARKER_PAYLOADS_AND_EXPECTED_DERIVED_VIA = [
    ({"canon": True}, LifecycleSetVia.CANON_SET),
    ({"kind": "seed"}, LifecycleSetVia.SEED_PLANT),
    ({"kind": "identity"}, LifecycleSetVia.SEED_PLANT),
    ({"kind": "core_identity"}, LifecycleSetVia.SEED_PLANT),
    ({"type": "seed"}, LifecycleSetVia.SEED_PLANT),  # type fallback
    ({"tier": "core_identity"}, LifecycleSetVia.TIER_SET),
    ({"srg": {"is_crystal": True}}, LifecycleSetVia.SRG_CRYSTAL),
    ({"governance": {"protected": True}}, LifecycleSetVia.GOVERNANCE_FLAG),
]


@pytest.mark.parametrize(
    "marker_payload,expected_derived_via",
    MARKER_PAYLOADS_AND_EXPECTED_DERIVED_VIA,
)
def test_state_mismatch_across_every_legacy_marker_source(
    marker_payload, expected_derived_via,
):
    """For every legacy protected marker source, an explicit UNSET
    envelope produces STATE_MISMATCH with the correct ``derived_via``.
    Confirms the detector wires through the Slice 1 derivation helper
    for all five marker sources (plus the type fallback).
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    payload = {"lifecycle_status": explicit, **marker_payload}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is not None
    assert result.kind is LifecycleDisagreementKind.STATE_MISMATCH
    assert result.explicit_state is LifecycleState.UNSET
    assert result.derived_via is expected_derived_via


# ===========================================================================
# Section G -- no mutation of input payload
# ===========================================================================


def test_payload_not_mutated_when_disagreement_present():
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    payload: Dict[str, Any] = {
        "lifecycle_status": explicit,
        "canon": True,
        "text": "row with disagreement",
    }
    snapshot = copy.deepcopy(payload)
    detect_lifecycle_legacy_marker_disagreement(payload)
    assert payload == snapshot


def test_payload_not_mutated_when_no_disagreement():
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.PROTECTED,
        via=LifecycleSetVia.CANON_SET,
        actor=LifecycleActor.MIGRATION,
    )
    payload: Dict[str, Any] = {
        "lifecycle_status": explicit,
        "canon": True,
        "text": "row with full agreement",
    }
    snapshot = copy.deepcopy(payload)
    detect_lifecycle_legacy_marker_disagreement(payload)
    assert payload == snapshot


def test_payload_not_mutated_when_no_marker_present():
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.RELEASED,
        via=LifecycleSetVia.RELEASE_PROMOTION,
        actor=LifecycleActor.OPERATOR,
    )
    payload: Dict[str, Any] = {
        "lifecycle_status": explicit,
        "text": "no markers present",
    }
    snapshot = copy.deepcopy(payload)
    detect_lifecycle_legacy_marker_disagreement(payload)
    assert payload == snapshot


# ===========================================================================
# Section H -- cross-slice composition: Slice 4 is observational only
# ===========================================================================


def test_detector_does_not_affect_read_shim_for_state_mismatch_payload():
    """The keystone Slice 4 composition test. A payload that produces
    STATE_MISMATCH still reads back through the H1a / Slice 2 read shim
    as the EXPLICIT envelope verbatim -- explicit-wins is preserved.
    The detector reports the conflict; the read shim does not act on it.
    Slice 4 is observational only.
    """
    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    payload = {"lifecycle_status": explicit, "canon": True}

    # Slice 4 detector reports the conflict.
    disagreement = detect_lifecycle_legacy_marker_disagreement(payload)
    assert disagreement is not None
    assert disagreement.kind is LifecycleDisagreementKind.STATE_MISMATCH

    # Slice 2 read shim still returns the explicit envelope verbatim.
    env = read_lifecycle_envelope(payload)
    assert env.state is LifecycleState.UNSET
    assert env.is_authoritative_on_row is True
    assert env.set_by.via is LifecycleSetVia.UNSET_DEFAULT
    # No mutation: the canon marker is still on the payload, the
    # lifecycle_status is still the original explicit envelope.
    assert payload["canon"] is True
    assert payload["lifecycle_status"] == explicit


def test_detector_does_not_affect_read_shim_for_authority_mismatch_payload():
    """Same observational guarantee for AUTHORITY_MISMATCH payloads."""
    explicit = _join_required_envelope_dict(
        state=LifecycleState.PROTECTED,
        side_channel=SideChannel.REVIEW_QUEUE,
        via=LifecycleSetVia.GATE1_REFUSAL,
    )
    payload = {"lifecycle_status": explicit, "canon": True}

    disagreement = detect_lifecycle_legacy_marker_disagreement(payload)
    assert disagreement is not None
    assert disagreement.kind is LifecycleDisagreementKind.AUTHORITY_MISMATCH

    # Read shim returns the explicit join-required envelope verbatim;
    # legacy canon marker is silently ignored at this slice.
    env = read_lifecycle_envelope(payload)
    assert env.state is LifecycleState.PROTECTED
    assert env.is_authoritative_on_row is False
    assert env.requires_join is not None
    assert env.requires_join.side_channel is SideChannel.REVIEW_QUEUE


# ===========================================================================
# Section I -- the result dataclass is frozen (defensive)
# ===========================================================================


def test_disagreement_result_is_frozen():
    """The result dataclass is frozen so consumers cannot mutate fields
    after construction. Mirrors the immutability of LifecycleStatus
    and friends.
    """
    import dataclasses

    explicit = _row_authoritative_envelope_dict(
        state=LifecycleState.UNSET,
        via=LifecycleSetVia.UNSET_DEFAULT,
        actor=LifecycleActor.MIGRATION,
    )
    payload = {"lifecycle_status": explicit, "canon": True}
    result = detect_lifecycle_legacy_marker_disagreement(payload)
    assert result is not None
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.kind = LifecycleDisagreementKind.AUTHORITY_MISMATCH
