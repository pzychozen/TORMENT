# torment_service/migration/constants.py
"""
String-stable identifiers for the WRITE_MIGRATION two-gate model.

All values in this module are **stable strings** — they appear in stored
rows, cursor files, review-queue entries, dry-run reports, logs, and tests.
Changing a value here is a corpus migration event, not a refactor.

Storage sentinels
-----------------

``SOURCE_GATE1_UNRECOVERABLE`` is a **storage sentinel**, not an admissible
origin class. It exists so that rows that failed gate 1 can be stored in
the uniform ProvenanceV1 schema (rather than left in a pre-migration
shape) while remaining definitively non-admissible under gate 2.

- It MUST be registered in ``ProvenanceV1.VALID_SOURCE_TYPES`` so rows
  carrying it can be constructed at all.
- It MUST be registered in
  ``cognition.recursion_guard._REJECTED_SOURCE_TYPES_IN_WALK`` so the
  bounded-DFS ancestry guard rejects it on sight, at any depth, with no
  recovery path.
- It MUST NEVER be produced by live ingest paths (``direct_ingest``,
  ``cognition_writeback``, ``tool_ingest``, ``collective_reingest``). Live
  producers have no reason to emit it; only the migration writes it.
- It MUST NEVER appear in ``_SAFE_SOURCE_TYPES_IN_WALK`` — that would
  defeat the entire gate-2 refusal discipline.

The name ``gate1_unrecoverable`` is deliberately verbose so it cannot be
mistaken for a real origin class by a reader skimming a stored row.

Admission reason vocabulary
---------------------------

The ``ADMISSION_REASON_*`` constants are the stable enumeration of refusal
reasons recorded in ``ProvenanceV1.admission_reason``. Each reason maps to
exactly one rule in ``docs/ADMISSION_POLICY_v2.4.x.md`` and one branch in
``gate2_admission.decide_admission``. Adding or removing a value here is a
doctrine change and requires bumping ``ADMISSION_POLICY_VERSION``.

Write-path identifiers
----------------------

``WRITE_MIGRATION`` is re-exported from ``torment_service.provenance_v1``
for call-site convenience. Its canonical definition lives in that module
so it participates in ``VALID_WRITE_PATHS`` enforcement.
"""
from __future__ import annotations

# ── Storage sentinel ─────────────────────────────────────────────────

#: Storage sentinel recorded in ``source_type`` on gate-1 FAIL rows so
#: they live in the uniform ProvenanceV1 schema. NOT an admissible origin
#: class. See module docstring.
SOURCE_GATE1_UNRECOVERABLE = "gate1_unrecoverable"


# ── Gate-1 recovery outcome vocabulary ───────────────────────────────

GATE1_OUTCOME_SKIP    = "SKIP"      # Already canonical — no migration needed
GATE1_OUTCOME_RECOVER = "RECOVER"   # Original provenance honestly reconstructed
GATE1_OUTCOME_FAIL    = "FAIL"      # Not honestly recoverable — stored under sentinel


# ── Gate-1 row classification vocabulary ─────────────────────────────
#
# One class_id per row in the Question-1a recovery table in
# ``docs/WRITE_MIGRATION_FRAMING_v2.4.x.md``. Numbering is stable and
# appears in cursor entries and dry-run reports.

GATE1_CLASS_ALREADY_CANONICAL     = 1  # Well-formed ProvenanceV1 dict
GATE1_CLASS_LEGACY_BARE_STRING    = 2  # Bare string (maps to source_type)
GATE1_CLASS_DICT_TRUNCATED        = 3  # Valid source_type, missing parent_eids
GATE1_CLASS_DICT_INVALID_TYPE     = 4  # Invalid or missing source_type
GATE1_CLASS_NULL_OR_EMPTY         = 5  # None / null / empty string
GATE1_CLASS_DEPRECATED_VOCABULARY = 6  # source_type not in VALID_SOURCE_TYPES
GATE1_CLASS_ZERO_EVENT_ARTIFACT   = 7  # Debug / test / synthesis artifact

GATE1_CLASSES = frozenset({
    GATE1_CLASS_ALREADY_CANONICAL,
    GATE1_CLASS_LEGACY_BARE_STRING,
    GATE1_CLASS_DICT_TRUNCATED,
    GATE1_CLASS_DICT_INVALID_TYPE,
    GATE1_CLASS_NULL_OR_EMPTY,
    GATE1_CLASS_DEPRECATED_VOCABULARY,
    GATE1_CLASS_ZERO_EVENT_ARTIFACT,
})


# ── Class-7 zero-event-artifact predicate ────────────────────────────
#
# Commit A ships class 7 with an **empty enumeration**. This is a
# deliberate conservative default, not an omission: at the time commit A
# lands, we have not yet run a dry-run against a real corpus to observe
# what artifact shapes actually exist, and enumerating speculative
# patterns would be a fuzzy match by another name. Decision 4 ratified
# that class 7 must be enumerated and auditable rather than fuzzy, so
# the honest starting posture is an empty list.
#
# The follow-up sequence is: commit A ships empty → dry-run against real
# corpus surfaces candidate artifact shapes → each candidate is ratified
# and added to this tuple under a new doctrine policy version → rerun
# re-evaluates affected rows under monotonic-in-tightness semantics.
#
# DO NOT add speculative patterns here. Each entry must be justified
# against an observed row in a dry-run report.
#
# Intentionally empty conservative default; exercised by tests via
# monkeypatch to prove live configuration. See
# ``tests/test_migration_gate1_recovery.py::TestClass7ZeroEventArtifact``
# for the live-configuration proof test. If static analysis ever
# flags this constant as unused, the monkeypatch test is the
# authoritative contradiction.

ZERO_EVENT_ARTIFACT_PATTERNS: tuple = tuple()  # noqa: used by gate1_recovery, dry_run, apply via import


# ── Gate-2 admission reason vocabulary ───────────────────────────────

ADMISSION_REASON_BARE_STRING_REJECTED_CLASS = "bare_string_maps_to_rejected_class"
ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET   = "source_type_in_rejected_set"
ADMISSION_REASON_ARCHIVIST_ROLE             = "archivist_role"
ADMISSION_REASON_GATE1_UNRECOVERABLE        = "gate1_unrecoverable"
ADMISSION_REASON_DEPRECATED_VOCABULARY      = "deprecated_vocabulary_no_mapping"
ADMISSION_REASON_ZERO_EVENT_ARTIFACT        = "zero_event_artifact"

ADMISSION_REASONS = frozenset({
    ADMISSION_REASON_BARE_STRING_REJECTED_CLASS,
    ADMISSION_REASON_SOURCE_TYPE_REJECTED_SET,
    ADMISSION_REASON_ARCHIVIST_ROLE,
    ADMISSION_REASON_GATE1_UNRECOVERABLE,
    ADMISSION_REASON_DEPRECATED_VOCABULARY,
    ADMISSION_REASON_ZERO_EVENT_ARTIFACT,
})


# ── Re-run policy decision vocabulary ────────────────────────────────

RERUN_DECISION_FIRST_EVALUATION  = "FIRST_EVALUATION"  # No stored decision yet
RERUN_DECISION_APPLY             = "APPLY"             # Tighten: admit→refuse
RERUN_DECISION_BUMP_ONLY         = "BUMP_ONLY"         # No change, bump version
RERUN_DECISION_BLOCK_AND_REVIEW  = "BLOCK_AND_REVIEW"  # Loosen: refuse→admit, held for review

RERUN_DECISIONS = frozenset({
    RERUN_DECISION_FIRST_EVALUATION,
    RERUN_DECISION_APPLY,
    RERUN_DECISION_BUMP_ONLY,
    RERUN_DECISION_BLOCK_AND_REVIEW,
})


# ── Admission policy version ─────────────────────────────────────────
#
# Tied to the doctrine doc revision per Decision 5 (Scheme C). Bumped
# only when the admission rule set itself changes — not on code
# refactors or test additions.
#
# Ordering rule: any ``v2.5.x-*`` is newer than any ``v2.4.x-*``; within
# a minor version, trailing suffix ``-a`` < ``-b`` < ... lexicographic.
# The CI drift check (``tests/test_admission_policy_drift.py``) enforces
# enumeration equality between this module and
# ``docs/ADMISSION_POLICY_v2.4.x.md``.

ADMISSION_POLICY_VERSION = "v2.4.x-step6-a"


# ── Cursor file layout ───────────────────────────────────────────────
#
# Per-workspace ``.torment_migration/`` subdirectory (Decision — plan
# sub-question 4). JSONL append-only so interrupted runs can resume
# from the last committed line without rewriting prior history.

CURSOR_DIRNAME      = ".torment_migration"
CURSOR_FILENAME     = "cursor.jsonl"
REVIEW_QUEUE_FILENAME = "review_queue.jsonl"
