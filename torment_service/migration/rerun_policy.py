# torment_service/migration/rerun_policy.py
"""
Monotonic-in-tightness re-run policy.

Decides what to do with a row when the migration is re-run and the
stored admission decision differs from the current policy's decision.

Decision table (matches ``docs/ADMISSION_POLICY_v2.4.x.md``):

    stored   | new      | decision
    ---------+----------+---------
    none     | any      | FIRST_EVALUATION
    admit    | admit    | BUMP_ONLY
    refuse   | refuse   | BUMP_ONLY
    admit    | refuse   | APPLY            (tighten — auto)
    refuse   | admit    | BLOCK_AND_REVIEW (loosen — manual)

Monotonicity is the load-bearing property: tightening applies
automatically, loosening is held for human review. This preserves the
"admission without honest recovery is laundering" invariant across
re-runs.
"""
from __future__ import annotations

from dataclasses import dataclass

from .constants import (
    ADMISSION_POLICY_VERSION,
    RERUN_DECISION_APPLY,
    RERUN_DECISION_BLOCK_AND_REVIEW,
    RERUN_DECISION_BUMP_ONLY,
    RERUN_DECISION_FIRST_EVALUATION,
)
from .gate2_admission import Gate2Result


@dataclass(frozen=True)
class StoredAdmissionState:
    """The gate-2 decision currently recorded on a row, as read from
    its stored ``ProvenanceV1`` payload."""
    admission_refused: bool
    admission_reason: str
    admission_policy_version: str

    @property
    def has_recorded_decision(self) -> bool:
        """True iff the row has a non-default admission decision on file.

        A ``default`` row (all three fields at their defaults) is
        treated as "no decision on file" so a live-ingest row can sit
        in the corpus without being treated as an explicit admission.
        """
        return (
            self.admission_refused
            or bool(self.admission_reason)
            or bool(self.admission_policy_version)
        )


@dataclass(frozen=True)
class RerunDecision:
    """What the re-run policy decided to do with a row.

    ``action`` is one of ``RERUN_DECISION_*``. ``reason`` carries the
    new gate-2 reason (for APPLY and FIRST_EVALUATION) or the stored
    reason (for BUMP_ONLY and BLOCK_AND_REVIEW) so callers have the
    authoritative string for writing back or enqueuing.
    """
    action: str
    new_admission_refused: bool
    new_admission_reason: str
    new_admission_policy_version: str


def decide_rerun(stored: StoredAdmissionState, new: Gate2Result) -> RerunDecision:
    """Compare the stored admission state against a fresh gate-2 result.

    Parameters
    ----------
    stored
        The row's current admission state, as read from its stored
        provenance payload.
    new
        The result of running gate 2 against the row under the current
        policy version.
    """
    # First-evaluation: no decision has ever been recorded on the row.
    # This is the normal state for every row in the corpus on the very
    # first migration run.
    if not stored.has_recorded_decision:
        return RerunDecision(
            action=RERUN_DECISION_FIRST_EVALUATION,
            new_admission_refused=not new.admitted,
            new_admission_reason=new.reason,
            new_admission_policy_version=new.policy_version,
        )

    stored_refused = stored.admission_refused
    new_refused = not new.admitted

    # Same outcome — bump policy version only.
    if stored_refused == new_refused:
        return RerunDecision(
            action=RERUN_DECISION_BUMP_ONLY,
            new_admission_refused=stored_refused,
            # Preserve the stored reason on bump-only so we don't
            # rewrite the audit trail for what is effectively a
            # no-op decision.
            new_admission_reason=stored.admission_reason,
            new_admission_policy_version=new.policy_version,
        )

    # Tightening: previously admitted, now refused. Applied
    # automatically.
    if not stored_refused and new_refused:
        return RerunDecision(
            action=RERUN_DECISION_APPLY,
            new_admission_refused=True,
            new_admission_reason=new.reason,
            new_admission_policy_version=new.policy_version,
        )

    # Loosening: previously refused, now admitted. Held for review.
    # The stored refusal stays in place until a human ratifies the
    # new decision. We return the stored values so callers that
    # write back continue to see the refusal, and the review queue
    # is populated separately.
    return RerunDecision(
        action=RERUN_DECISION_BLOCK_AND_REVIEW,
        new_admission_refused=stored.admission_refused,
        new_admission_reason=stored.admission_reason,
        new_admission_policy_version=stored.admission_policy_version,
    )


# ── Policy version ordering ──────────────────────────────────────────
#
# Used when the stored policy version is strictly older than the
# current one; the re-run policy re-evaluates those rows regardless of
# whether the decision would change. A row whose stored version
# *matches* the current policy is not re-evaluated at all.

def is_stale_version(stored_version: str, current_version: str = ADMISSION_POLICY_VERSION) -> bool:
    """True iff ``stored_version`` is strictly older than ``current_version``.

    Ordering rule (per ``docs/ADMISSION_POLICY_v2.4.x.md``):
      - any ``v2.5.x-*`` is newer than any ``v2.4.x-*``
      - within the same minor line, lexicographic comparison on the
        full string

    This is intentionally simple — it is not a full semver parser.
    The policy version scheme is deliberately restricted to
    ``vMAJOR.MINOR.x-stepN-suffix`` so lexicographic comparison within
    a minor line produces the correct order.
    """
    if stored_version == current_version:
        return False
    if not stored_version:
        return True  # Unset → always stale.
    stored_minor = _minor_line(stored_version)
    current_minor = _minor_line(current_version)
    if stored_minor != current_minor:
        # Cross-line comparison: any v2.5.x-* is newer than any
        # v2.4.x-*. Lexicographic on the minor-line prefix gives the
        # right answer for the ``v{major}.{minor}.x`` shape.
        return stored_minor < current_minor
    return stored_version < current_version


def _minor_line(version: str) -> str:
    """Return the ``v{major}.{minor}.x`` prefix of a policy version string.

    Non-conforming inputs return the full string so the comparison in
    ``is_stale_version`` still behaves sanely (it just falls back to
    lexicographic on the whole thing).
    """
    # Find the first '-' separator; everything before it is the minor
    # line. ``v2.4.x-step6-a`` → ``v2.4.x``.
    if "-" in version:
        return version.split("-", 1)[0]
    return version
