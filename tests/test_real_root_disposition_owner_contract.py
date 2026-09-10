"""Inert guardrails for the real-root disposition owner contract.

These fixtures model the *documented* completion gate only.  They do not
discover a deployment, open a root, write a receipt, or grant any production
authority.  Their job is to ensure that a future real verifier cannot turn the
frozen mapping into the former synthetic "non-empty outcome" success rule.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from torment_service.substrate.deployment_types import FROZEN_ROOT_GEOMETRY_DISPOSITIONS


REAL_MUTATION_REQUIRED = "REAL_MUTATION_REQUIRED"
REAL_AUTHORITY_TRANSITION_REQUIRED = "REAL_AUTHORITY_TRANSITION_REQUIRED"
REAL_RECEIPT_ONLY = "REAL_RECEIPT_ONLY"
ALREADY_SATISFIED_BY_PRIOR_PHASE = "ALREADY_SATISFIED_BY_PRIOR_PHASE"
SYNTHETIC_ONLY_NO_PRODUCTION_ANALOG = "SYNTHETIC_ONLY_NO_PRODUCTION_ANALOG"
OWNER_ABSENT_REQUIRES_NEW_ARCHITECTURE = "OWNER_ABSENT_REQUIRES_NEW_ARCHITECTURE"

_VALID_CLASSIFICATIONS = frozenset(
    {
        REAL_MUTATION_REQUIRED,
        REAL_AUTHORITY_TRANSITION_REQUIRED,
        REAL_RECEIPT_ONLY,
        ALREADY_SATISFIED_BY_PRIOR_PHASE,
        SYNTHETIC_ONLY_NO_PRODUCTION_ANALOG,
        OWNER_ABSENT_REQUIRES_NEW_ARCHITECTURE,
    }
)

# This is deliberately test-local.  It mirrors the v1.1 contract and is not a
# production registry, adapter, or selector input.
_CLASSIFICATION_BY_OWNER = {
    "bridge_registry": REAL_RECEIPT_ONLY,
    "character_active_baseline": REAL_MUTATION_REQUIRED,
    "character_drift_history": REAL_RECEIPT_ONLY,
    "character_seed": REAL_RECEIPT_ONLY,
    "checkpoint_kernel_calibration": SYNTHETIC_ONLY_NO_PRODUCTION_ANALOG,
    "conflict_role_affect_identity": REAL_RECEIPT_ONLY,
    "deep_archive_vector_state": REAL_RECEIPT_ONLY,
    "hivemind_historical_geometry_scores": REAL_RECEIPT_ONLY,
    "proposal_registry": REAL_RECEIPT_ONLY,
    "srg_payload_markers": SYNTHETIC_ONLY_NO_PRODUCTION_ANALOG,
    "world_trajectory": OWNER_ABSENT_REQUIRES_NEW_ARCHITECTURE,
}


class ContractRefused(ValueError):
    """The inert fixture's fail-closed outcome."""


@dataclass(frozen=True)
class _CompletionClaim:
    owner: str
    disposition: str
    predecessor: str
    successor: str
    reported_complete: bool
    actual_state: str
    evidence: str | None


def _expected_predecessor(owner: str) -> str:
    return f"P6_BOUND_PREDECESSOR:{owner}"


def _expected_successor(owner: str) -> str:
    return f"P6_BOUND_SUCCESSOR:{owner}"


def _validate_claim(claim: _CompletionClaim) -> None:
    classification = _CLASSIFICATION_BY_OWNER.get(claim.owner)
    if classification is None:
        raise ContractRefused("unknown disposition owner")
    expected_disposition = dict(FROZEN_ROOT_GEOMETRY_DISPOSITIONS)[claim.owner]
    if claim.disposition != expected_disposition:
        raise ContractRefused("conflicting frozen transition")
    if claim.predecessor != _expected_predecessor(claim.owner):
        raise ContractRefused("wrong predecessor")
    if claim.actual_state == "PARTIAL" and claim.reported_complete:
        raise ContractRefused("partial state cannot be reported complete")
    if not claim.reported_complete:
        raise ContractRefused("disposition is incomplete")
    if classification in {
        REAL_MUTATION_REQUIRED,
        REAL_AUTHORITY_TRANSITION_REQUIRED,
        REAL_RECEIPT_ONLY,
    } and not claim.evidence:
        raise ContractRefused("completion evidence is required")
    if classification == OWNER_ABSENT_REQUIRES_NEW_ARCHITECTURE:
        raise ContractRefused("owner contract is absent")
    if classification == REAL_MUTATION_REQUIRED and claim.successor != _expected_successor(claim.owner):
        raise ContractRefused("conflicting successor")


def _p7_eligible(claims: tuple[_CompletionClaim, ...]) -> bool:
    by_owner = {claim.owner: claim for claim in claims}
    if set(by_owner) != set(_CLASSIFICATION_BY_OWNER):
        return False
    try:
        for owner in _CLASSIFICATION_BY_OWNER:
            _validate_claim(by_owner[owner])
    except ContractRefused:
        return False
    return True


def _complete_claim(owner: str, *, evidence: str | None = "receipt") -> _CompletionClaim:
    return _CompletionClaim(
        owner=owner,
        disposition=dict(FROZEN_ROOT_GEOMETRY_DISPOSITIONS)[owner],
        predecessor=_expected_predecessor(owner),
        successor=_expected_successor(owner),
        reported_complete=True,
        actual_state="COMPLETE",
        evidence=evidence,
    )


def test_fixture_covers_each_frozen_owner_once_with_a_closed_classification():
    assert set(_CLASSIFICATION_BY_OWNER) == {
        owner for owner, _disposition in FROZEN_ROOT_GEOMETRY_DISPOSITIONS
    }
    assert set(_CLASSIFICATION_BY_OWNER.values()) <= _VALID_CLASSIFICATIONS


def test_unknown_owner_is_rejected():
    claim = _CompletionClaim(
        owner="invented_owner",
        disposition="INVENTED",
        predecessor="anything",
        successor="anything",
        reported_complete=True,
        actual_state="COMPLETE",
        evidence="receipt",
    )
    with pytest.raises(ContractRefused, match="unknown disposition owner"):
        _validate_claim(claim)


def test_wrong_predecessor_is_rejected():
    claim = _complete_claim("character_active_baseline")
    claim = _CompletionClaim(**{**claim.__dict__, "predecessor": "stale-predecessor"})
    with pytest.raises(ContractRefused, match="wrong predecessor"):
        _validate_claim(claim)


def test_conflicting_transition_is_rejected():
    claim = _complete_claim("proposal_registry")
    claim = _CompletionClaim(**{**claim.__dict__, "disposition": "REWRITE_VECTORS"})
    with pytest.raises(ContractRefused, match="conflicting frozen transition"):
        _validate_claim(claim)


def test_missing_completion_evidence_is_rejected():
    with pytest.raises(ContractRefused, match="completion evidence is required"):
        _validate_claim(_complete_claim("hivemind_historical_geometry_scores", evidence=None))


def test_partial_state_cannot_be_falsely_reported_complete():
    claim = _complete_claim("character_active_baseline")
    claim = _CompletionClaim(**{**claim.__dict__, "actual_state": "PARTIAL"})
    with pytest.raises(ContractRefused, match="partial state cannot be reported complete"):
        _validate_claim(claim)


def test_p7_eligibility_rejects_a_required_disposition_that_is_incomplete():
    claims = tuple(_complete_claim(owner) for owner in _CLASSIFICATION_BY_OWNER)
    incomplete = _CompletionClaim(
        **{
            **claims[1].__dict__,
            "reported_complete": False,
            "actual_state": "NOT_STARTED",
        }
    )
    claims = (claims[0], incomplete, *claims[2:])
    assert _p7_eligible(claims) is False
