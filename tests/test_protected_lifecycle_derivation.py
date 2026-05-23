"""tests/test_protected_lifecycle_derivation.py

Q2-D Slice 1 tests for ``derive_protected_lifecycle_from_legacy_markers``.

This file tests the derivation primitive in isolation. The helper is the
"law on the books" for mapping pre-Q2 protected markers (canon, kind,
tier, srg.is_crystal, governance.protected) onto a canonical Q2
``LifecycleStatus`` with ``state=PROTECTED``. Production wiring of the
derivation into the H1a read shim, the H1c write stamp, and the
existing protected readers is deferred to later Q2-D slices.

Central design point being tested: returning ``None`` for "no protected
marker present" -- the helper does NOT fall back to UNSET. That
distinction is exactly what prevents the H1a shim from accidentally
erasing legacy protected markers when later Q2-D slices wire the
derivation into the read path.

Out of scope for Q2-D Slice 1 (and these tests):

* production wiring of any consumer
* changes to the H1a shim or H1c stamp
* changes to ``compression.derive_retention_tier`` or
  ``governance.is_compression_protected``
* disagreement detection between supplied envelope and legacy markers
* retroactive disk migration / backfill
* baton lifecycle / closure-ledger / review-queue work
* Q3 / custom DB / schema work
"""
from __future__ import annotations

import copy
import os
import sys
import time
from typing import Any, Dict, Optional

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


from torment_service.lifecycle import (
    LifecycleActor,
    LifecycleSetBy,
    LifecycleSetVia,
    LifecycleState,
    LifecycleStateError,
    LifecycleStatus,
    assert_lifecycle_row_authoritative,
    derive_protected_lifecycle_from_legacy_markers,
    validate_lifecycle_envelope,
)


FIXED_AT = 1_716_300_000


# ===========================================================================
# Category 1 -- each marker in isolation produces state=PROTECTED with
# the expected set_by.via
# ===========================================================================


# Cases: (label, payload, expected_via_value)
MARKER_CASES = [
    ("canon",
     {"canon": True},
     "canon_set"),
    ("kind_seed",
     {"kind": "seed"},
     "seed_plant"),
    ("kind_identity",
     {"kind": "identity"},
     "seed_plant"),
    ("kind_core_identity",
     {"kind": "core_identity"},
     "seed_plant"),
    ("tier_core_identity",
     {"tier": "core_identity"},
     "tier_set"),
    ("srg_is_crystal_true",
     {"srg": {"is_crystal": True}},
     "srg_crystal"),
    ("governance_protected_true",
     {"governance": {"protected": True}},
     "governance_flag"),
]


@pytest.mark.parametrize("label,payload,expected_via", MARKER_CASES)
def test_each_marker_alone_produces_protected_with_expected_via(
    label, payload, expected_via,
):
    env = derive_protected_lifecycle_from_legacy_markers(
        payload, now=FIXED_AT,
    )
    assert env is not None, f"{label!r} should produce an envelope"
    assert env.state is LifecycleState.PROTECTED
    assert env.is_authoritative_on_row is True
    assert env.requires_join is None
    assert env.history_ref is None
    assert env.set_by.actor is LifecycleActor.MIGRATION
    assert env.set_by.via.value == expected_via
    assert env.set_by.at == FIXED_AT


# ===========================================================================
# Category 2 -- no markers returns None (NOT UNSET)
# ===========================================================================


def test_empty_payload_returns_none():
    """Critical: when no legacy protected marker is present, the helper
    returns None. It must NOT fall back to UNSET. Distinguishing
    "no protected derivation available" from "definitely unset" is the
    structural separation that prevents future Q2-D wiring slices from
    erasing legacy protected signals via the H1a shim.
    """
    result = derive_protected_lifecycle_from_legacy_markers({}, now=FIXED_AT)
    assert result is None


def test_payload_with_only_non_protected_fields_returns_none():
    payload = {
        "text": "ordinary memory",
        "step": 5,
        "summary": "nothing protected here",
        "provenance": {"source_type": "user_input"},
        "half_life": 30,
    }
    result = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert result is None


def test_payload_with_non_triggering_marker_values_returns_none():
    """Markers present but not at protected values must return None."""
    payload = {
        "canon": False,
        "kind": "episode",
        "tier": "relational",
        "srg": {"is_crystal": False},
        "governance": {"non_shareable": True, "protected": False},
    }
    result = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert result is None


# ===========================================================================
# Category 3 -- canonical precedence: canon > kind/type > tier > srg > gov
# ===========================================================================


def test_precedence_canon_beats_kind():
    payload = {"canon": True, "kind": "identity"}
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert env.set_by.via is LifecycleSetVia.CANON_SET


def test_precedence_canon_beats_all_others():
    payload = {
        "canon": True,
        "kind": "identity",
        "tier": "core_identity",
        "srg": {"is_crystal": True},
        "governance": {"protected": True},
    }
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert env.set_by.via is LifecycleSetVia.CANON_SET


def test_precedence_kind_beats_tier():
    payload = {"kind": "identity", "tier": "core_identity"}
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert env.set_by.via is LifecycleSetVia.SEED_PLANT


def test_precedence_tier_beats_srg():
    payload = {"tier": "core_identity", "srg": {"is_crystal": True}}
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert env.set_by.via is LifecycleSetVia.TIER_SET


def test_precedence_srg_beats_governance():
    payload = {
        "srg": {"is_crystal": True},
        "governance": {"protected": True},
    }
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert env.set_by.via is LifecycleSetVia.SRG_CRYSTAL


# ===========================================================================
# Category 4 -- kind protected values all map to SEED_PLANT (Slice 1
# legacy-marker mapping; not a semantic claim)
# ===========================================================================


@pytest.mark.parametrize("kind_value", ["seed", "identity", "core_identity"])
def test_each_protected_kind_value_triggers(kind_value):
    env = derive_protected_lifecycle_from_legacy_markers(
        {"kind": kind_value}, now=FIXED_AT,
    )
    assert env is not None
    assert env.set_by.via is LifecycleSetVia.SEED_PLANT


@pytest.mark.parametrize("kind_value", ["episode", "relational", "random",
                                          "anchor", "core"])
def test_non_protected_kind_values_do_not_trigger(kind_value):
    env = derive_protected_lifecycle_from_legacy_markers(
        {"kind": kind_value}, now=FIXED_AT,
    )
    assert env is None


# ===========================================================================
# Category 5 -- payload["type"] fallback when "kind" is absent
# ===========================================================================


@pytest.mark.parametrize("type_value", ["seed", "identity", "core_identity"])
def test_type_fallback_when_kind_absent(type_value):
    """When ``kind`` is absent but ``type`` carries a protected value,
    the derivation honors ``type`` as fallback -- matching
    ``compression.derive_retention_tier``'s existing behavior.
    """
    env = derive_protected_lifecycle_from_legacy_markers(
        {"type": type_value}, now=FIXED_AT,
    )
    assert env is not None
    assert env.set_by.via is LifecycleSetVia.SEED_PLANT


def test_kind_wins_over_type_when_both_present():
    """When both keys are present, ``kind`` is the authoritative read --
    the fallback is only consulted when ``kind`` is absent.
    """
    payload = {"kind": "episode", "type": "identity"}
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    # kind="episode" is not protected; type="identity" is, but only as
    # a fallback when kind is absent. Therefore: no derivation.
    assert env is None


# ===========================================================================
# Category 6 -- tier=core_identity triggers; other tier values do not
# ===========================================================================


@pytest.mark.parametrize("tier_value",
                           ["relational", "echo", "identity",
                            "tool_result", "situational", ""])
def test_non_core_identity_tiers_do_not_trigger(tier_value):
    env = derive_protected_lifecycle_from_legacy_markers(
        {"tier": tier_value}, now=FIXED_AT,
    )
    assert env is None


# ===========================================================================
# Category 7 -- non-dict / malformed srg is silently ignored
# ===========================================================================


@pytest.mark.parametrize("bad_srg", [None, "not a dict", 42, [],
                                       ["is_crystal", True]])
def test_non_dict_srg_is_ignored(bad_srg):
    env = derive_protected_lifecycle_from_legacy_markers(
        {"srg": bad_srg}, now=FIXED_AT,
    )
    assert env is None


def test_srg_dict_without_is_crystal_does_not_trigger():
    env = derive_protected_lifecycle_from_legacy_markers(
        {"srg": {"other_field": True}}, now=FIXED_AT,
    )
    assert env is None


# ===========================================================================
# Category 8 -- governance.protected triggers; other gov flags do not
# ===========================================================================


def test_governance_protected_true_triggers():
    env = derive_protected_lifecycle_from_legacy_markers(
        {"governance": {"protected": True}}, now=FIXED_AT,
    )
    assert env is not None
    assert env.set_by.via is LifecycleSetVia.GOVERNANCE_FLAG


def test_governance_other_flags_do_not_trigger():
    """Only ``governance.protected`` matters for this helper. Other
    governance flags (``non_shareable``, ``collective_export_blocked``,
    etc.) are orthogonal -- this helper is about protected status
    derivation only.
    """
    payload = {"governance": {
        "non_shareable": True,
        "collective_export_blocked": True,
        "collective_reingest_blocked": True,
        "decay_accelerated": True,
    }}
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert env is None


@pytest.mark.parametrize("bad_gov", [None, "not a dict", 42, []])
def test_non_dict_governance_is_ignored(bad_gov):
    env = derive_protected_lifecycle_from_legacy_markers(
        {"governance": bad_gov}, now=FIXED_AT,
    )
    assert env is None


# ===========================================================================
# Category 9 -- timestamp handling
# ===========================================================================


def test_now_is_honored():
    env = derive_protected_lifecycle_from_legacy_markers(
        {"canon": True}, now=42,
    )
    assert env.set_by.at == 42


def test_default_now_falls_in_recent_wall_clock_window():
    before = int(time.time())
    env = derive_protected_lifecycle_from_legacy_markers({"canon": True})
    after = int(time.time())
    assert isinstance(env.set_by.at, int)
    assert env.set_by.at >= before
    assert env.set_by.at <= after


def test_now_irrelevant_when_no_marker_present():
    """A None return short-circuits before set_by.at is constructed, so
    no envelope is built and no timestamp is allocated.
    """
    result = derive_protected_lifecycle_from_legacy_markers({}, now=999)
    assert result is None


# ===========================================================================
# Category 10 -- no mutation of input payload
# ===========================================================================


def test_payload_not_mutated_when_marker_present():
    payload: Dict[str, Any] = {"canon": True, "text": "x"}
    snapshot = copy.deepcopy(payload)
    derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert payload == snapshot


def test_payload_not_mutated_when_no_marker_present():
    payload: Dict[str, Any] = {"text": "x", "step": 1}
    snapshot = copy.deepcopy(payload)
    derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert payload == snapshot
    # And specifically: no envelope was injected into the payload.
    assert "lifecycle_status" not in payload


def test_payload_nested_dicts_not_mutated():
    """Defensive: changes to nested dicts (srg, governance) would also
    be a violation. Snapshot via deepcopy and compare.
    """
    payload: Dict[str, Any] = {
        "srg": {"is_crystal": True, "other": "data"},
        "governance": {"protected": False, "non_shareable": True},
    }
    snapshot = copy.deepcopy(payload)
    derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert payload == snapshot


# ===========================================================================
# Category 11 -- returned envelope round-trips through validator
# ===========================================================================


@pytest.mark.parametrize("payload", [c[1] for c in MARKER_CASES])
def test_returned_envelope_re_validates_cleanly(payload):
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    revalidated = validate_lifecycle_envelope(env.to_dict())
    assert revalidated == env


# ===========================================================================
# Category 12 -- returned envelope passes the Q2-F primitive
# ===========================================================================


@pytest.mark.parametrize("payload", [c[1] for c in MARKER_CASES])
def test_returned_envelope_passes_q2f_primitive(payload):
    """Cross-slice composition: every derivation result is row-authoritative
    by construction (PROTECTED is always row-authoritative per the Q2-C
    decision table), so the Q2-F primitive returns None for any
    derivation output. Confirms Q2-D + Q2-F compose cleanly.
    """
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert assert_lifecycle_row_authoritative(env) is None


# ===========================================================================
# Category 13 -- strict canon marker truth
# ===========================================================================


@pytest.mark.parametrize("bad_canon", [False, None, "yes", "true", 1, 0,
                                         "True", "1", [], {}])
def test_canon_non_literal_true_does_not_trigger(bad_canon):
    """Only literal Python ``True`` in payload["canon"] triggers the
    canon marker. Truthy-but-not-True values (``1``, ``"yes"``) do
    NOT trigger -- matches the existing
    ``compression.derive_retention_tier`` ``is True`` check exactly.
    """
    env = derive_protected_lifecycle_from_legacy_markers(
        {"canon": bad_canon}, now=FIXED_AT,
    )
    assert env is None, (
        f"canon={bad_canon!r} should NOT trigger; expected None, "
        f"got {env!r}"
    )


def test_canon_literal_true_triggers():
    env = derive_protected_lifecycle_from_legacy_markers(
        {"canon": True}, now=FIXED_AT,
    )
    assert env is not None
    assert env.set_by.via is LifecycleSetVia.CANON_SET


# ===========================================================================
# Category 14 -- helper ignores any existing lifecycle_status on payload
# ===========================================================================


def test_helper_ignores_present_valid_envelope_and_returns_derived():
    """The helper's responsibility is strictly legacy-marker derivation.
    A present ``lifecycle_status`` (whether valid or not) is ignored
    here; resolution between supplied envelope and legacy markers is
    a separate concern (Q2-D Slice 4 disagreement policy).
    """
    supplied = LifecycleStatus(
        state=LifecycleState.RELEASED,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(
            actor=LifecycleActor.OPERATOR,
            via=LifecycleSetVia.RELEASE_PROMOTION,
            at=FIXED_AT,
        ),
        history_ref=None,
    ).to_dict()
    payload = {"canon": True, "lifecycle_status": supplied}
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    # The derivation IGNORES the supplied envelope and returns the
    # legacy-derived PROTECTED envelope. Resolving the disagreement
    # ("but the supplied envelope says RELEASED!") is a future slice.
    assert env is not None
    assert env.state is LifecycleState.PROTECTED
    assert env.set_by.via is LifecycleSetVia.CANON_SET


def test_helper_ignores_present_envelope_when_no_markers_and_returns_none():
    """If a payload has a present envelope but no legacy protected markers,
    the helper still returns None -- it does not "see" the envelope.
    """
    supplied = LifecycleStatus(
        state=LifecycleState.RELEASED,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(
            actor=LifecycleActor.OPERATOR,
            via=LifecycleSetVia.RELEASE_PROMOTION,
            at=FIXED_AT,
        ),
        history_ref=None,
    ).to_dict()
    payload = {"lifecycle_status": supplied, "text": "ordinary"}
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert env is None


def test_helper_ignores_malformed_envelope_on_payload():
    """A malformed ``lifecycle_status`` on the payload does NOT cause
    this helper to raise. The helper does not look at ``lifecycle_status``
    at all; its inputs are exclusively the five legacy markers.
    Validation of any present envelope is the H1a shim's responsibility.
    """
    payload = {"canon": True, "lifecycle_status": {"state": "bogus"}}
    env = derive_protected_lifecycle_from_legacy_markers(payload, now=FIXED_AT)
    assert env is not None
    assert env.state is LifecycleState.PROTECTED


# ===========================================================================
# Category 15 -- non-dict payload raises
# ===========================================================================


@pytest.mark.parametrize("bad_payload",
                           [None, 42, "not a dict", [], (1, 2), 1.5])
def test_non_dict_payload_raises_lifecycle_state_error(bad_payload):
    with pytest.raises(LifecycleStateError) as exc_info:
        derive_protected_lifecycle_from_legacy_markers(
            bad_payload, now=FIXED_AT,
        )
    assert exc_info.value.field == "payload"
    assert exc_info.value.reason == "not_a_dict"
