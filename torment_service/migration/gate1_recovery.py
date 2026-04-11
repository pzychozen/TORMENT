# torment_service/migration/gate1_recovery.py
"""
Gate 1 — epistemic recovery predicate.

Answers "what can we honestly reconstruct about this row's original
provenance?" Deterministic: same input always produces the same
Gate1Result. Classifies every row into exactly one of seven classes
enumerated in ``docs/ADMISSION_POLICY_v2.4.x.md``.

This module does NOT write anything. It returns a ``Gate1Result`` that
the dry-run generator (and, in commit B, the migration writer) consume
to produce reports and ProvenanceV1 records.

Non-goals
---------
- This module does not decide admission. That is gate 2.
- This module does not know about re-run policy. That is rerun_policy.
- This module does not construct ``ProvenanceV1`` instances. The
  migration writer does that using the fields on ``Gate1Result`` plus
  the gate-2 decision.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from torment_service.provenance_v1 import (
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_DERIVED,
    SOURCE_GATE1_UNRECOVERABLE,
    SOURCE_MEMORY,
    SOURCE_ROLE_OUTPUT,
    SOURCE_TOOL_RESULT,
    SOURCE_USER_INPUT,
    VALID_SOURCE_TYPES,
)
from .constants import (
    GATE1_CLASS_ALREADY_CANONICAL,
    GATE1_CLASS_DEPRECATED_VOCABULARY,
    GATE1_CLASS_DICT_INVALID_TYPE,
    GATE1_CLASS_DICT_TRUNCATED,
    GATE1_CLASS_LEGACY_BARE_STRING,
    GATE1_CLASS_NULL_OR_EMPTY,
    GATE1_CLASS_ZERO_EVENT_ARTIFACT,
    GATE1_OUTCOME_FAIL,
    GATE1_OUTCOME_RECOVER,
    GATE1_OUTCOME_SKIP,
    ZERO_EVENT_ARTIFACT_PATTERNS,
)


# ── Bare-string recovery table ───────────────────────────────────────
#
# Bare strings observed in legacy corpora that map deterministically to
# a current canonical source_type. The mapping is case-insensitive on
# the key and strict on the value.
#
# NOTE: the sentinel is NEVER a recovery target. Gate 1 FAIL rows are
# constructed by the writer, not by the gate.

_BARE_STRING_RECOVERY: Dict[str, str] = {
    "user_input":      SOURCE_USER_INPUT,
    "role_output":     SOURCE_ROLE_OUTPUT,
    "memory":          SOURCE_MEMORY,
    "tool_result":     SOURCE_TOOL_RESULT,
    "collective_echo": SOURCE_COLLECTIVE_ECHO,
    "collective":      SOURCE_COLLECTIVE_ECHO,  # pre-rename artifact
    "derived":         SOURCE_DERIVED,
}


# ── Deprecated vocabulary mapping table ──────────────────────────────
#
# Commit A ships this empty. See docs/ADMISSION_POLICY_v2.4.x.md
# Class 6 section. Entries are added only after a dry-run against a
# real corpus surfaces candidate deprecated values, and each entry
# requires a new policy version bump.

_DEPRECATED_VOCABULARY_MAPPING: Dict[str, str] = {}


@dataclass(frozen=True)
class Gate1Result:
    """Result of applying gate 1 to a single row's raw provenance value.

    Fields
    ------
    class_id
        One of the ``GATE1_CLASS_*`` stable integers. Always set.
    outcome
        One of ``GATE1_OUTCOME_SKIP``, ``GATE1_OUTCOME_RECOVER``,
        ``GATE1_OUTCOME_FAIL``. Derived from ``class_id`` but carried
        explicitly for dry-run report clarity.
    recovered_source_type
        The canonical ``source_type`` the gate believes the row
        originally carried. ``None`` on FAIL.
    recovered_source_role
        The canonical ``source_role``, only set when the original dict
        explicitly carried it. ``None`` otherwise.
    recovered_parent_eids
        Parent EID list carried through from the original dict; empty
        list for bare-string / null / missing cases.
    recovery_notes
        Free-text audit trail. Always includes the raw original value
        and the classification path.
    raw_original
        Original raw provenance value (opaque — stored for audit).
    """
    class_id: int
    outcome: str
    recovered_source_type: Optional[str]
    recovered_source_role: Optional[str]
    recovered_parent_eids: List[int]
    recovery_notes: str
    raw_original: Any


def classify_row(raw_provenance: Any, *, eid: Optional[int] = None) -> Gate1Result:
    """Classify a single row's raw provenance into a Gate1Result.

    Parameters
    ----------
    raw_provenance
        The value stored in the row's provenance slot. May be ``None``,
        a bare string, a dict, a ``ProvenanceV1`` instance serialized
        via ``to_dict``, or any unexpected primitive.
    eid
        Optional EID of the row being classified. Used only in notes
        for audit-trail clarity; does not affect the decision.
    """
    eid_tag = f"eid={eid} " if eid is not None else ""

    # ── Class 5 — null / empty / non-provenance primitive ───────────
    #
    # Checked first so class 2 (bare string) cannot shadow an
    # empty-string row.
    if raw_provenance is None or raw_provenance == "" or raw_provenance == {}:
        return Gate1Result(
            class_id=GATE1_CLASS_NULL_OR_EMPTY,
            outcome=GATE1_OUTCOME_FAIL,
            recovered_source_type=None,
            recovered_source_role=None,
            recovered_parent_eids=[],
            recovery_notes=f"{eid_tag}null_or_empty raw={raw_provenance!r}",
            raw_original=raw_provenance,
        )

    # ── Class 2 — legacy bare string ────────────────────────────────
    if isinstance(raw_provenance, str):
        mapped = _BARE_STRING_RECOVERY.get(raw_provenance.strip().lower())
        if mapped is not None:
            return Gate1Result(
                class_id=GATE1_CLASS_LEGACY_BARE_STRING,
                outcome=GATE1_OUTCOME_RECOVER,
                recovered_source_type=mapped,
                recovered_source_role=None,
                recovered_parent_eids=[],
                recovery_notes=(
                    f"{eid_tag}legacy_bare_string={raw_provenance!r} "
                    f"mapped={mapped}"
                ),
                raw_original=raw_provenance,
            )
        # A bare string that is not a known origin class falls through
        # to class 4 (dict-invalid-type equivalent for strings).
        return Gate1Result(
            class_id=GATE1_CLASS_DICT_INVALID_TYPE,
            outcome=GATE1_OUTCOME_FAIL,
            recovered_source_type=None,
            recovered_source_role=None,
            recovered_parent_eids=[],
            recovery_notes=(
                f"{eid_tag}unrecognised_bare_string raw={raw_provenance!r}"
            ),
            raw_original=raw_provenance,
        )

    # ── Dict shapes ──────────────────────────────────────────────────
    if isinstance(raw_provenance, dict):
        # Class 7 — zero-event artifact detection.
        #
        # Commit A ships with ZERO_EVENT_ARTIFACT_PATTERNS empty, so
        # this branch never fires. Decision 4 requires enumeration,
        # not fuzzy matching; the helper walks the tuple explicitly
        # and only a dict that matches every key/value of a registered
        # pattern is classified as class 7.
        if _matches_zero_event_artifact(raw_provenance):
            return Gate1Result(
                class_id=GATE1_CLASS_ZERO_EVENT_ARTIFACT,
                outcome=GATE1_OUTCOME_FAIL,
                recovered_source_type=None,
                recovered_source_role=None,
                recovered_parent_eids=[],
                recovery_notes=f"{eid_tag}zero_event_artifact_matched",
                raw_original=raw_provenance,
            )

        source_type = raw_provenance.get("source_type")

        # Class 4 — invalid / missing source_type.
        if source_type is None:
            return Gate1Result(
                class_id=GATE1_CLASS_DICT_INVALID_TYPE,
                outcome=GATE1_OUTCOME_FAIL,
                recovered_source_type=None,
                recovered_source_role=None,
                recovered_parent_eids=[],
                recovery_notes=f"{eid_tag}missing_source_type",
                raw_original=raw_provenance,
            )

        # Class 6 — deprecated vocabulary with deterministic mapping.
        if source_type not in VALID_SOURCE_TYPES:
            mapped = _DEPRECATED_VOCABULARY_MAPPING.get(source_type)
            if mapped is not None:
                return Gate1Result(
                    class_id=GATE1_CLASS_DEPRECATED_VOCABULARY,
                    outcome=GATE1_OUTCOME_RECOVER,
                    recovered_source_type=mapped,
                    recovered_source_role=raw_provenance.get("source_role"),
                    recovered_parent_eids=_coerce_parent_eids(
                        raw_provenance.get("parent_eids")
                    ),
                    recovery_notes=(
                        f"{eid_tag}deprecated_vocabulary "
                        f"from={source_type!r} to={mapped}"
                    ),
                    raw_original=raw_provenance,
                )
            # No mapping — class 4 fail.
            return Gate1Result(
                class_id=GATE1_CLASS_DICT_INVALID_TYPE,
                outcome=GATE1_OUTCOME_FAIL,
                recovered_source_type=None,
                recovered_source_role=None,
                recovered_parent_eids=[],
                recovery_notes=(
                    f"{eid_tag}unknown_source_type raw_type={source_type!r}"
                ),
                raw_original=raw_provenance,
            )

        # Valid source_type from here on. Reject the sentinel — it must
        # never appear on a row the migration is classifying, because
        # the migration is the only writer and sentinel rows were
        # produced by a previous migration run (and must go through
        # re-run policy, not be re-classified).
        if source_type == SOURCE_GATE1_UNRECOVERABLE:
            return Gate1Result(
                class_id=GATE1_CLASS_ALREADY_CANONICAL,
                outcome=GATE1_OUTCOME_SKIP,
                recovered_source_type=source_type,
                recovered_source_role=raw_provenance.get("source_role"),
                recovered_parent_eids=_coerce_parent_eids(
                    raw_provenance.get("parent_eids")
                ),
                recovery_notes=f"{eid_tag}sentinel_row_skip",
                raw_original=raw_provenance,
            )

        parent_eids_raw = raw_provenance.get("parent_eids")
        has_parent_eids_field = "parent_eids" in raw_provenance
        parent_eids = _coerce_parent_eids(parent_eids_raw)

        # Class 1 vs class 3 — well-formed dict.
        #
        # A dict is "already canonical" (class 1) if it has a
        # schema_version string plus every required ProvenanceV1 field
        # present. A dict that is missing parent_eids entirely, or has
        # them as a non-list, is class 3 (truncated / needs
        # canonicalization).
        is_canonical = (
            has_parent_eids_field
            and isinstance(parent_eids_raw, list)
            and "schema_version" in raw_provenance
            and "write_path" in raw_provenance
        )
        if is_canonical:
            return Gate1Result(
                class_id=GATE1_CLASS_ALREADY_CANONICAL,
                outcome=GATE1_OUTCOME_SKIP,
                recovered_source_type=source_type,
                recovered_source_role=raw_provenance.get("source_role"),
                recovered_parent_eids=parent_eids,
                recovery_notes=f"{eid_tag}already_canonical",
                raw_original=raw_provenance,
            )

        return Gate1Result(
            class_id=GATE1_CLASS_DICT_TRUNCATED,
            outcome=GATE1_OUTCOME_RECOVER,
            recovered_source_type=source_type,
            recovered_source_role=raw_provenance.get("source_role"),
            recovered_parent_eids=parent_eids,
            recovery_notes=(
                f"{eid_tag}dict_truncated canonicalized_from_partial_dict"
            ),
            raw_original=raw_provenance,
        )

    # ── Anything else — list, int, object, etc. ────────────────────
    return Gate1Result(
        class_id=GATE1_CLASS_NULL_OR_EMPTY,
        outcome=GATE1_OUTCOME_FAIL,
        recovered_source_type=None,
        recovered_source_role=None,
        recovered_parent_eids=[],
        recovery_notes=(
            f"{eid_tag}non_provenance_primitive type={type(raw_provenance).__name__}"
        ),
        raw_original=raw_provenance,
    )


def _coerce_parent_eids(raw: Any) -> List[int]:
    """Best-effort coercion of a raw parent_eids value to ``list[int]``.

    Returns an empty list for None, missing, non-iterable, or
    non-integer-castable values. This helper never raises — gate 1's
    job is classification, not validation.
    """
    if raw is None:
        return []
    if not isinstance(raw, (list, tuple)):
        return []
    out: List[int] = []
    for item in raw:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            # A single bad element drops to empty — we cannot
            # honestly reconstruct a partial ancestry chain.
            return []
    return out


def _dict_matches_pattern(d: Dict[str, Any], pattern: Dict[str, Any]) -> bool:
    """True iff every key in ``pattern`` is present in ``d`` with an
    equal value. Extra keys in ``d`` are ignored.

    Used only by class 7 (zero-event artifact) detection. Patterns are
    enumerated, not fuzzy — equality is strict.
    """
    for k, v in pattern.items():
        if d.get(k) != v:
            return False
    return True


def _matches_zero_event_artifact(raw: Any) -> bool:
    """Class 7 predicate — True iff ``raw`` matches any enumerated
    zero-event artifact pattern in ``ZERO_EVENT_ARTIFACT_PATTERNS``.

    This is the single consumption site of ``ZERO_EVENT_ARTIFACT_PATTERNS``
    in the gate 1 recovery module. The constant is doctrinal and stable,
    shipped as an intentionally empty tuple in commit A — a deliberate
    conservative default documented in ``docs/ADMISSION_POLICY_v2.4.x.md``.
    Patterns are added only in response to dry-run evidence from a real
    corpus and each addition requires a policy-version bump.

    When the tuple is empty (commit A state), the loop body never
    executes and this function returns ``False`` for every input — which
    is the correct evidence-first behavior: no patterns enumerated, no
    rows classified as class 7.
    """
    if not isinstance(raw, dict):
        return False
    for pattern in ZERO_EVENT_ARTIFACT_PATTERNS:
        if _dict_matches_pattern(raw, pattern):
            return True
    return False
