# torment_service/migration/apply.py
"""
Writer primitive for WRITE_MIGRATION commit B.

This module is the **only** place in the migration package that calls a
corpus mutation API. The single public entry point is ``apply_row``,
which rewrites a single row's provenance to reflect a gate-1 + gate-2
decision under the current admission policy.

Narrowness invariant
--------------------

``apply_row`` is strictly narrower than the dry-run reader. The dry-run
reads every row and classifies every row; ``apply_row`` refuses to
rewrite any row that does not pass six precondition re-checks at the
top of the function. A row can be visible to the dry-run (counted,
reported) and still be invisible to the writer (skipped, never
touched). The six preconditions make this narrowness a structural
property of the code rather than a comment in the docstring.

Cursor is secondary, row state is primary
-----------------------------------------

The cursor file is a resume aid. The authoritative source of truth for
"has this row been written" is the row's currently stored provenance
state. If a prior cursor entry says ``APPLIED`` but the stored row
disagrees with the expected post-apply state, the writer refuses to
silently re-apply — it logs an anomaly and skips. This keeps the
system robust against partial cursor writes, manual cursor edits, or
row-level rollbacks.

Ordering guarantee
------------------

On every successful apply, the writer calls ``graph.update_payload``
first and only appends the cursor entry once the row update has
returned. A crash between the two produces a stored row in the new
state with no cursor entry, which the next run sees as "needs
re-application under the same policy" and resolves idempotently via
the precondition-6 cross-check (stored row matches expected post-apply
state → clean skip).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from torment_service.provenance_v1 import (
    SOURCE_GATE1_UNRECOVERABLE,
    WRITE_MIGRATION,
    ProvenanceV1,
)

from .constants import (
    GATE1_CLASS_DEPRECATED_VOCABULARY,
    GATE1_CLASS_ZERO_EVENT_ARTIFACT,
    GATE1_OUTCOME_FAIL,
    GATE1_OUTCOME_RECOVER,
    GATE1_OUTCOME_SKIP,
    RERUN_DECISION_APPLY,
    RERUN_DECISION_BLOCK_AND_REVIEW,
    RERUN_DECISION_BUMP_ONLY,
    RERUN_DECISION_FIRST_EVALUATION,
    ZERO_EVENT_ARTIFACT_PATTERNS,
)
from .cursor import (
    CURSOR_ACTION_APPLIED,
    CursorEntry,
    append_entry,
    read_entries,
)
from .gate1_recovery import Gate1Result, _DEPRECATED_VOCABULARY_MAPPING
from .gate2_admission import Gate2Result
from .rerun_policy import RerunDecision
from .review_queue import ReviewEntry, append_review

logger = logging.getLogger(__name__)


# ── Writer action vocabulary ─────────────────────────────────────────
#
# Broader than the cursor action vocabulary because the writer also
# has to represent outcomes that never produce a cursor entry
# (precondition failures, anomaly skips, and bump-only skips). The
# cursor only records terminal row-state transitions; the writer's
# ApplyResult records everything the writer saw and decided.

APPLY_ACTION_APPLIED                = "APPLIED"
APPLY_ACTION_BLOCKED_REVIEW         = "BLOCKED_REVIEW"
APPLY_ACTION_SKIPPED_BUMP_ONLY      = "SKIPPED_BUMP_ONLY"
APPLY_ACTION_SKIPPED_ALREADY_APPLIED = "SKIPPED_ALREADY_APPLIED"
APPLY_ACTION_SKIPPED_PRECONDITION   = "SKIPPED_PRECONDITION"
APPLY_ACTION_SKIPPED_ANOMALY        = "SKIPPED_ANOMALY"

APPLY_ACTIONS = frozenset({
    APPLY_ACTION_APPLIED,
    APPLY_ACTION_BLOCKED_REVIEW,
    APPLY_ACTION_SKIPPED_BUMP_ONLY,
    APPLY_ACTION_SKIPPED_ALREADY_APPLIED,
    APPLY_ACTION_SKIPPED_PRECONDITION,
    APPLY_ACTION_SKIPPED_ANOMALY,
})


@dataclass(frozen=True)
class ApplyResult:
    """What the writer did (or refused to do) with a single row.

    Fields
    ------
    action
        One of the ``APPLY_ACTION_*`` constants. Always set.
    eid
        The row identifier the decision was about.
    reason
        Short machine-readable tag. Empty on ``APPLIED``; otherwise a
        stable string that names the branch the writer took. Used by
        the wet-run report and by tests to assert the writer refused
        for the specific reason expected.
    patch
        The patch the writer sent to ``graph.update_payload`` on a
        successful apply. ``None`` on every non-APPLIED action. Present
        so tests and audit tooling can verify exactly what shape the
        writer wrote without re-reading the row.
    """
    action: str
    eid: int
    reason: str
    patch: Optional[Dict[str, Any]] = field(default=None)


# ── Public entry point ───────────────────────────────────────────────

def apply_row(
    graph: Any,
    eid: int,
    stored_prov: Optional[Dict[str, Any]],
    fresh_g1: Gate1Result,
    fresh_g2: Gate2Result,
    rerun_decision: RerunDecision,
    *,
    workspace_root: str,
) -> ApplyResult:
    """Write a gate-1 + gate-2 decision to a single row.

    Parameters
    ----------
    graph
        An object exposing ``update_payload(eid, patch)``. In live runs
        this is a ``MemoryGraph``; in tests it is a stub that records
        calls without writing to disk.
    eid
        The row identifier. Caller guarantees it exists in ``graph``.
    stored_prov
        The row's currently stored provenance dict as read from
        ``graph.entities[eid].payload.get("provenance")``. May be
        ``None`` or an empty dict for pre-step-6 rows that never
        carried a provenance slot.
    fresh_g1
        The gate-1 result computed against ``stored_prov`` under the
        current policy version.
    fresh_g2
        The gate-2 result computed from ``fresh_g1``.
    rerun_decision
        The re-run policy decision derived from ``stored_prov``'s
        admission fields and ``fresh_g2``.
    workspace_root
        The workspace directory under which
        ``.torment_migration/cursor.jsonl`` and
        ``.torment_migration/review_queue.jsonl`` live.

    Returns
    -------
    ApplyResult
        Records what the writer did. The writer never raises on
        precondition failure — it returns a SKIPPED_* result so the
        orchestrator can log it and move on.
    """

    # ── Precondition 1 ──────────────────────────────────────────────
    # Stored provenance must be a dict (or None, which the writer
    # treats as "no prior provenance"). Anything else — a bare string,
    # a list, a primitive — means the row is in a shape the writer
    # does not know how to mutate safely. Dry-run classifies those
    # rows at gate 1; the writer refuses them here.
    if stored_prov is not None and not isinstance(stored_prov, dict):
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_PRECONDITION,
            eid=eid,
            reason="stored_prov_not_dict",
        )

    # ── Precondition 2 ──────────────────────────────────────────────
    # Gate-1 SKIP means the row is class 1 (already canonical). The
    # writer never touches class 1 rows because there is nothing to
    # reconstruct and the admission fields already default to the
    # live-ingest "no decision on file" state. This check lives BEFORE
    # the rerun-decision branches so that sentinel rows (which gate 1
    # also routes to SKIP) cannot be misrouted into BLOCK_AND_REVIEW
    # by a stale-version mismatch between stored refused flag and the
    # fresh gate-2 admit-on-SKIP result. This is strictly narrower than
    # the dry-run reader, which also refuses to count class 1 rows
    # under gate-2 refusal.
    if fresh_g1.outcome == GATE1_OUTCOME_SKIP:
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_PRECONDITION,
            eid=eid,
            reason="class_1_already_canonical",
        )

    # The re-run decision must be writable. BUMP_ONLY is a no-op
    # content-wise; BLOCK_AND_REVIEW is a loosening that the writer
    # refuses to apply and instead enqueues for human review; unknown
    # actions are refused defensively.
    if rerun_decision.action == RERUN_DECISION_BUMP_ONLY:
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_BUMP_ONLY,
            eid=eid,
            reason="bump_only_no_content_change",
        )
    if rerun_decision.action == RERUN_DECISION_BLOCK_AND_REVIEW:
        stored_or_empty = stored_prov or {}
        review = ReviewEntry(
            eid=eid,
            stored_admission_refused=bool(stored_or_empty.get("admission_refused", False)),
            stored_admission_reason=str(stored_or_empty.get("admission_reason", "")),
            stored_admission_policy_version=str(stored_or_empty.get("admission_policy_version", "")),
            current_admission_refused=(not fresh_g2.admitted),
            current_admission_reason=fresh_g2.reason,
            current_admission_policy_version=fresh_g2.policy_version,
            recovered_source_type=fresh_g1.recovered_source_type,
            gate1_class_id=fresh_g1.class_id,
        )
        append_review(workspace_root, review)
        return ApplyResult(
            action=APPLY_ACTION_BLOCKED_REVIEW,
            eid=eid,
            reason="block_and_review_enqueued",
        )
    if rerun_decision.action not in (
        RERUN_DECISION_APPLY,
        RERUN_DECISION_FIRST_EVALUATION,
    ):
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_PRECONDITION,
            eid=eid,
            reason=f"unknown_rerun_action:{rerun_decision.action}",
        )

    # ── Precondition 3 ──────────────────────────────────────────────
    # Monotonicity re-check. Even if the re-run policy upstream handed
    # us an APPLY, the writer independently verifies that the
    # transition is a tightening or same-tightness. Loosening
    # (refused→admitted) is refused here as a second line of defense.
    # Boolean order: refused(True) > admitted(False).
    stored_refused = bool((stored_prov or {}).get("admission_refused", False))
    new_refused = bool(rerun_decision.new_admission_refused)
    if stored_refused and not new_refused:
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_PRECONDITION,
            eid=eid,
            reason="loosening_refused_by_writer_monotonicity_check",
        )

    # ── Precondition 4 ──────────────────────────────────────────────
    # A refused decision must carry a non-empty reason and a
    # non-empty policy version. This mirrors the ProvenanceV1
    # __post_init__ invariants and catches malformed decisions before
    # they reach ``graph.update_payload``.
    if new_refused and not rerun_decision.new_admission_reason:
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_PRECONDITION,
            eid=eid,
            reason="empty_reason_for_refused_decision",
        )
    if new_refused and not rerun_decision.new_admission_policy_version:
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_PRECONDITION,
            eid=eid,
            reason="empty_policy_version_for_refused_decision",
        )

    # ── Precondition 5 ──────────────────────────────────────────────
    # Evidence gate for class 6 and class 7. If gate 1 classifies a
    # row into one of these doctrinally-empty tables, the only way
    # that can happen is if the table was populated upstream — which
    # is a cross-check against an upstream classification bug. The
    # writer refuses rather than silently rewriting, and logs a
    # warning so operators see the upstream inconsistency.
    #
    # This is the structural enforcement of the commit-B caution that
    # class 6 and class 7 must remain evidence-gated even with the
    # writer present.
    if fresh_g1.class_id == GATE1_CLASS_DEPRECATED_VOCABULARY:
        if not _DEPRECATED_VOCABULARY_MAPPING:
            logger.warning(
                "apply_row: eid=%s classified as DEPRECATED_VOCABULARY (class 6) "
                "but the mapping table is empty. Refusing to write — this indicates "
                "an upstream classification bug.",
                eid,
            )
            return ApplyResult(
                action=APPLY_ACTION_SKIPPED_PRECONDITION,
                eid=eid,
                reason="class_6_evidence_gate_table_empty",
            )
    if fresh_g1.class_id == GATE1_CLASS_ZERO_EVENT_ARTIFACT:
        if not ZERO_EVENT_ARTIFACT_PATTERNS:
            logger.warning(
                "apply_row: eid=%s classified as ZERO_EVENT_ARTIFACT (class 7) "
                "but the pattern tuple is empty. Refusing to write — this indicates "
                "an upstream classification bug.",
                eid,
            )
            return ApplyResult(
                action=APPLY_ACTION_SKIPPED_PRECONDITION,
                eid=eid,
                reason="class_7_evidence_gate_patterns_empty",
            )

    # ── Build the expected post-apply admission triple ──────────────
    #
    # This is the "primary truth" state the writer would produce if
    # it did run. Precondition 6 compares this against the stored row
    # to decide whether a prior cursor entry is trustworthy.
    expected_refused = new_refused
    expected_reason = rerun_decision.new_admission_reason
    expected_policy_version = rerun_decision.new_admission_policy_version

    # ── Precondition 6 ──────────────────────────────────────────────
    # Cursor-vs-row cross-check. The cursor is secondary; the row is
    # primary. If the cursor has a prior APPLIED entry for this eid,
    # the stored row must already match the expected post-apply
    # admission triple; if it does, we clean-skip (idempotent resume);
    # if it does not, we log an anomaly and refuse to write.
    prior_applied = _latest_applied_entry_for(workspace_root, eid)
    if prior_applied is not None:
        row_matches_expected = _admission_state_matches(
            stored_prov,
            expected_refused=expected_refused,
            expected_reason=expected_reason,
            expected_policy_version=expected_policy_version,
        )
        if row_matches_expected:
            return ApplyResult(
                action=APPLY_ACTION_SKIPPED_ALREADY_APPLIED,
                eid=eid,
                reason="already_applied_idempotent",
            )
        logger.warning(
            "apply_row: eid=%s cursor-vs-row anomaly — cursor has a prior APPLIED entry "
            "at %s under policy version %r, but stored row does not match the expected "
            "post-apply admission triple. Refusing to re-apply. "
            "stored=(refused=%r, reason=%r, version=%r) expected=(refused=%r, reason=%r, version=%r).",
            eid,
            prior_applied.committed_at,
            prior_applied.policy_version,
            (stored_prov or {}).get("admission_refused"),
            (stored_prov or {}).get("admission_reason"),
            (stored_prov or {}).get("admission_policy_version"),
            expected_refused,
            expected_reason,
            expected_policy_version,
        )
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_ANOMALY,
            eid=eid,
            reason="cursor_vs_row_mismatch",
        )

    # ── Build the patch ─────────────────────────────────────────────
    #
    # The patch is a dict merged into ``payload`` by
    # ``MemoryGraph.update_payload``. The migration always writes the
    # full provenance sub-dict (rather than merging admission fields
    # into an existing provenance dict) so that a single atomic
    # update either replaces the whole provenance slot or leaves it
    # untouched — no half-migrated provenance shapes survive.
    try:
        new_provenance_dict = _build_new_provenance_dict(
            stored_prov=stored_prov,
            fresh_g1=fresh_g1,
            expected_refused=expected_refused,
            expected_reason=expected_reason,
            expected_policy_version=expected_policy_version,
        )
    except ValueError as exc:
        logger.warning(
            "apply_row: eid=%s provenance construction failed: %s. Refusing to write.",
            eid,
            exc,
        )
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_PRECONDITION,
            eid=eid,
            reason="provenance_construction_failed",
        )

    patch: Dict[str, Any] = {"provenance": new_provenance_dict}

    # ── Write row first, then append cursor ─────────────────────────
    #
    # Ordering matters. On a crash between these two calls, the next
    # run sees a stored row in the new state with no cursor entry.
    # Precondition 6's cursor-vs-row cross-check then resolves the
    # restart cleanly: fresh classification produces the same
    # expected post-apply triple, the stored row already matches it,
    # and the writer clean-skips. The cursor entry gets written on
    # the second pass. This is the effectively-once-under-resume
    # property the plan ratified.
    try:
        graph.update_payload(eid, patch)
    except Exception as exc:
        logger.warning(
            "apply_row: eid=%s graph.update_payload failed: %s. No cursor entry appended.",
            eid,
            exc,
        )
        return ApplyResult(
            action=APPLY_ACTION_SKIPPED_ANOMALY,
            eid=eid,
            reason="update_payload_failed",
        )

    append_entry(
        workspace_root,
        CursorEntry(
            eid=eid,
            action=CURSOR_ACTION_APPLIED,
            gate1_class_id=fresh_g1.class_id,
            gate2_admitted=fresh_g2.admitted,
            policy_version=expected_policy_version,
        ),
    )

    return ApplyResult(
        action=APPLY_ACTION_APPLIED,
        eid=eid,
        reason="",
        patch=patch,
    )


# ── Private helpers ──────────────────────────────────────────────────

def _latest_applied_entry_for(workspace_root: str, eid: int) -> Optional[CursorEntry]:
    """Return the most recent ``APPLIED`` cursor entry for ``eid``, or None.

    Reads the whole cursor file and scans for APPLIED entries. For
    commit B, correctness beats optimization — the cursor file is
    expected to stay small on per-workspace corpora, and a linear
    scan keeps the semantic model simple. If real-world cursor sizes
    make this hot in a future commit, the scan can be replaced with
    an indexed read without changing the external contract.
    """
    entries = read_entries(workspace_root)
    latest: Optional[CursorEntry] = None
    for entry in entries:
        if entry.eid == eid and entry.action == CURSOR_ACTION_APPLIED:
            latest = entry
    return latest


def _admission_state_matches(
    stored_prov: Optional[Dict[str, Any]],
    *,
    expected_refused: bool,
    expected_reason: str,
    expected_policy_version: str,
) -> bool:
    """True iff the stored provenance's admission triple matches the
    expected post-apply triple exactly.

    Missing keys in ``stored_prov`` are treated as their defaults
    (``False`` / ``""`` / ``""``), matching
    ``ProvenanceV1.from_dict`` + ``to_dict`` round-trip semantics.
    """
    stored = stored_prov or {}
    return (
        bool(stored.get("admission_refused", False)) == expected_refused
        and str(stored.get("admission_reason", "")) == expected_reason
        and str(stored.get("admission_policy_version", "")) == expected_policy_version
    )


def _build_new_provenance_dict(
    *,
    stored_prov: Optional[Dict[str, Any]],
    fresh_g1: Gate1Result,
    expected_refused: bool,
    expected_reason: str,
    expected_policy_version: str,
) -> Dict[str, Any]:
    """Construct the provenance dict that will replace the row's
    provenance slot.

    The dict is produced by constructing a ``ProvenanceV1`` instance
    (which runs all the invariant checks) and serializing it via
    ``to_dict``. If the invariants fail, ``ValueError`` propagates up
    to the caller, which converts it into a SKIPPED_PRECONDITION
    result.

    Strategy
    --------
    Start from the stored provenance dict (if any), then overlay:

    - ``source_type`` / ``source_role`` / ``parent_eids`` from the
      gate-1 recovery result, for rows that were recovered.
    - ``source_type = SOURCE_GATE1_UNRECOVERABLE`` and
      ``parent_eids = []`` for rows that were gate-1 FAIL. This is
      the uniform refused shape Decision 4 ratified.
    - ``write_path = WRITE_MIGRATION`` so the row's write_path
      reflects the migration's authorship of the current provenance.
    - The admission triple (``admission_refused``,
      ``admission_reason``, ``admission_policy_version``) from the
      expected post-apply state.
    """
    base: Dict[str, Any] = dict(stored_prov or {})

    # Strip any cached admission fields from the base. The writer
    # always sets these from the expected triple; leaving stale
    # values would let the dict merge silently preserve old state.
    for key in ("admission_refused", "admission_reason", "admission_policy_version"):
        base.pop(key, None)

    # Gate-1 outcome determines the origin fields in the new shape.
    if fresh_g1.outcome == GATE1_OUTCOME_RECOVER:
        if fresh_g1.recovered_source_type is not None:
            base["source_type"] = fresh_g1.recovered_source_type
        if fresh_g1.recovered_source_role is not None:
            base["source_role"] = fresh_g1.recovered_source_role
        # recovered_parent_eids is always a list (may be empty).
        base["parent_eids"] = list(fresh_g1.recovered_parent_eids)
    elif fresh_g1.outcome == GATE1_OUTCOME_FAIL:
        # Uniform refused shape.
        base["source_type"] = SOURCE_GATE1_UNRECOVERABLE
        base["parent_eids"] = []
        # Drop any stale source_role — sentinel rows do not carry a role.
        base.pop("source_role", None)

    # The migration owns the write_path on every rewrite so audit
    # tooling can attribute the current shape to the migration.
    base["write_path"] = WRITE_MIGRATION

    # Admission triple always set from the expected state.
    base["admission_refused"] = expected_refused
    base["admission_reason"] = expected_reason
    base["admission_policy_version"] = expected_policy_version

    # Construct a ProvenanceV1 so __post_init__ invariants fire. Any
    # ValueError surfaces to the caller, which turns it into a
    # SKIPPED_PRECONDITION result rather than propagating the
    # exception into the orchestrator.
    prov = ProvenanceV1.from_dict(base)

    # Re-serialize through to_dict so the patch is JSON-safe and
    # default-valued fields are stripped consistently with every
    # other provenance write in the codebase. Note: because we set
    # the admission triple explicitly, to_dict will only strip
    # admission fields if they carry their defaults, which only
    # happens on FIRST_EVALUATION admits. That is correct — an
    # admitted row's first policy evaluation should not leave a
    # visible admission_* footprint beyond the policy version.
    serialized = prov.to_dict()

    # Preserve the invariant that admission_policy_version is always
    # present on a migration-rewritten row, even when the decision is
    # admit. This lets the re-run policy distinguish "visited by the
    # migration" from "never seen by the migration" on subsequent
    # runs. to_dict strips it when it is the default empty string,
    # which happens only if expected_policy_version itself is "". We
    # never call apply_row with an empty policy version because
    # ADMISSION_POLICY_VERSION is always set, but belt-and-braces:
    if expected_policy_version and "admission_policy_version" not in serialized:
        serialized["admission_policy_version"] = expected_policy_version

    return serialized


# ── Module re-exports for test and orchestrator convenience ─────────

__all__ = [
    "APPLY_ACTIONS",
    "APPLY_ACTION_APPLIED",
    "APPLY_ACTION_BLOCKED_REVIEW",
    "APPLY_ACTION_SKIPPED_ALREADY_APPLIED",
    "APPLY_ACTION_SKIPPED_ANOMALY",
    "APPLY_ACTION_SKIPPED_BUMP_ONLY",
    "APPLY_ACTION_SKIPPED_PRECONDITION",
    "ApplyResult",
    "apply_row",
]
