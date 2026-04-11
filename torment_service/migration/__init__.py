# torment_service/migration/__init__.py
"""
TORMENT v2.4.x WRITE_MIGRATION package.

Step 6, commit A — ships the machinery for the write-migration two-gate model
in **dry-run only** mode. No write path is present in commit A by design; a
dedicated commit B lands the actual rewrite path under the same framing
discipline used in step 5 for the archivist gate.

Modules
-------
- ``constants``    : storage sentinels and string-stable identifiers used by
                     the migration. Includes ``SOURCE_GATE1_UNRECOVERABLE``,
                     which is a **storage sentinel, not an admissible origin
                     class** — see module docstring.
- ``gate1_recovery``: epistemic recovery predicate (what we can honestly
                     reconstruct about a row's original provenance).
- ``gate2_admission``: ancestry admission predicate (whether a recovered row
                     should be authorized as a future-safe ancestor).
- ``rerun_policy`` : monotonic-in-tightness re-run decision table.
- ``cursor``       : append-only JSONL cursor for effectively-once resume.
- ``review_queue`` : append-only JSONL review queue for block-and-review
                     loosening decisions.
- ``dry_run``      : report generator producing the four-section minimum
                     artifact ratified in Decision 6.
- ``cli``          : ``torment-migration`` entry point with ``dry-run`` and
                     ``status`` commands only. No ``apply`` in commit A.

Doctrine
--------
See ``docs/ADMISSION_POLICY_v2.4.x.md`` for the authoritative admission rule
set and policy-version scheme. See ``docs/WRITE_MIGRATION_FRAMING_v2.4.x.md``
for the original two-gate framing and the six ratified decisions this
implementation honors.

See ``docs/WRITE_MIGRATION_IMPLEMENTATION_PLAN_v2.4.x.md`` for the commit A /
commit B split and the exhaustive file-level change list.
"""
