# torment_service/migration/gate2_admission.py
"""
Gate 2 — ancestry admission predicate.

Given a ``Gate1Result``, decides whether the recovered row should be
authorized as a future-safe ancestor. Refusal is recorded explicitly
with a stable reason string so the dry-run report, re-run policy, and
audit trail can all reason about it in the same vocabulary.

This module does NOT decide what gate 1 said — it consumes a gate-1
result. It does NOT construct ``ProvenanceV1`` instances — the
migration writer does. It does NOT decide re-run policy — that is
``rerun_policy``.

The rule order in ``decide_admission`` MUST match
``docs/ADMISSION_POLICY_v2.4.x.md`` rule ordering. The CI drift check
enforces enumeration equality on the reason set.
"""
from __future__ import annotations

from dataclasses import dataclass

from torment_service.provenance_v1 import (
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_DERIVED,
    SOURCE_ROLE_OUTPUT,
)
from .constants import (
    ADMISSION_POLICY_VERSION,
    ADMISSION_REASON_ARCHIVIST_ROLE,
    ADMISSION_REASON_BARE_STRING_REJECTED_CLASS,
    ADMISSION_REASON_DEPRECATED_VOCABULARY,
    ADMISSION_REASON_GATE1_UNRECOVERABLE,
    ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET,
    ADMISSION_REASON_ZERO_EVENT_ARTIFACT,
    GATE1_CLASS_DEPRECATED_VOCABULARY,
    GATE1_CLASS_LEGACY_BARE_STRING,
    GATE1_CLASS_ZERO_EVENT_ARTIFACT,
    GATE1_OUTCOME_FAIL,
    GATE1_OUTCOME_RECOVER,
    GATE1_OUTCOME_SKIP,
)
from .gate1_recovery import Gate1Result


# The rejected set at the gate-2 layer. Kept in sync with
# ``cognition.recursion_guard._REJECTED_SOURCE_TYPES_IN_WALK`` by the
# CI drift check so the migration cannot admit a row the guard would
# reject at writeback time.
_REJECTED_SOURCE_TYPES_AT_ADMISSION = frozenset({
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_DERIVED,
})


@dataclass(frozen=True)
class Gate2Result:
    """Result of applying gate 2 to a gate-1 result.

    Fields
    ------
    admitted
        True iff the row passes gate 2 and may enter the admissible
        ancestry corridor.
    reason
        On refusal, one of the ``ADMISSION_REASON_*`` stable strings.
        Empty string on admission.
    policy_version
        The policy version under which the decision was made. Always
        set, even for admissions, so the re-run policy can detect
        staleness on both outcomes.
    """
    admitted: bool
    reason: str
    policy_version: str


def decide_admission(g1: Gate1Result) -> Gate2Result:
    """Apply gate-2 admission rules to a gate-1 result.

    Rule order matches ``docs/ADMISSION_POLICY_v2.4.x.md`` exactly.
    First match wins.
    """

    # Canonical rows pass through without a gate-2 decision. They were
    # already admissible under the live-ingest path and the migration
    # does not revisit them.
    if g1.outcome == GATE1_OUTCOME_SKIP:
        return Gate2Result(
            admitted=True,
            reason="",
            policy_version=ADMISSION_POLICY_VERSION,
        )

    # Rule 1: gate-1 FAIL → refuse as unrecoverable, with class-7
    # (zero-event artifact) recorded under its own reason for dry-run
    # reporting clarity.
    if g1.outcome == GATE1_OUTCOME_FAIL:
        if g1.class_id == GATE1_CLASS_ZERO_EVENT_ARTIFACT:
            return Gate2Result(
                admitted=False,
                reason=ADMISSION_REASON_ZERO_EVENT_ARTIFACT,
                policy_version=ADMISSION_POLICY_VERSION,
            )
        return Gate2Result(
            admitted=False,
            reason=ADMISSION_REASON_GATE1_UNRECOVERABLE,
            policy_version=ADMISSION_POLICY_VERSION,
        )

    # From here, outcome must be RECOVER.
    assert g1.outcome == GATE1_OUTCOME_RECOVER, (
        f"unexpected gate1 outcome {g1.outcome!r}"
    )

    recovered_type = g1.recovered_source_type
    recovered_role = (g1.recovered_source_role or "").lower()

    # Rule 3: class 6 rows without a deterministic mapping never reach
    # gate 2 with outcome RECOVER (gate 1 falls them to class 4 FAIL in
    # that case). But when a mapping exists and the mapped value is in
    # the rejected set, we record that under the deprecated-vocabulary
    # reason so the dry-run report can distinguish "vocabulary gap" from
    # "legitimate rejection".
    if (
        g1.class_id == GATE1_CLASS_DEPRECATED_VOCABULARY
        and recovered_type in _REJECTED_SOURCE_TYPES_AT_ADMISSION
    ):
        return Gate2Result(
            admitted=False,
            reason=ADMISSION_REASON_DEPRECATED_VOCABULARY,
            policy_version=ADMISSION_POLICY_VERSION,
        )

    # Rule 4: legacy bare string recovered to a rejected class.
    if (
        g1.class_id == GATE1_CLASS_LEGACY_BARE_STRING
        and recovered_type in _REJECTED_SOURCE_TYPES_AT_ADMISSION
    ):
        return Gate2Result(
            admitted=False,
            reason=ADMISSION_REASON_BARE_STRING_REJECTED_CLASS,
            policy_version=ADMISSION_POLICY_VERSION,
        )

    # Rule 5: dict-truncated or already-canonical with source_type in
    # the rejected set.
    if recovered_type in _REJECTED_SOURCE_TYPES_AT_ADMISSION:
        return Gate2Result(
            admitted=False,
            reason=ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET,
            policy_version=ADMISSION_POLICY_VERSION,
        )

    # Rule 6: archivist role at any gate-2 evaluation — refuse with
    # the archivist reason.
    if recovered_type == SOURCE_ROLE_OUTPUT and "archivist" in recovered_role:
        return Gate2Result(
            admitted=False,
            reason=ADMISSION_REASON_ARCHIVIST_ROLE,
            policy_version=ADMISSION_POLICY_VERSION,
        )

    # Default: admit.
    return Gate2Result(
        admitted=True,
        reason="",
        policy_version=ADMISSION_POLICY_VERSION,
    )
