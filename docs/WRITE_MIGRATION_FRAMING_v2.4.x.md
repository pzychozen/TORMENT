# TORMENT 2.4.x — Write Migration Framing (Step 6)

## Status

**Ratified 2026-04-11.** All six decisions were signed off and the
implementation plan was written against them. **Commit A of step 6 has
landed** on branch `v2.4.x-step6-commit-a` — the read-only surface
(two-gate decision pipeline, cursor, review queue, dry-run report, CLI,
recursion-guard refusal path, admission-policy drift check) is live
and green. Commit B (the row-rewrite path) is the next unit of work
under its own review. See `docs/WRITE_MIGRATION_IMPLEMENTATION_PLAN_v2.4.x.md`
for the commit A / commit B split, and `docs/ADMISSION_POLICY_v2.4.x.md`
for the live admission rule set.

This framing document is preserved as the ratified source of truth for
the six decisions and is not itself subject to change — subsequent
doctrine revisions happen in `docs/ADMISSION_POLICY_v2.4.x.md` under
its own version history table, not by editing this doc.

---

The sections below were written before ratification and are preserved
verbatim.

## Original framing-pass status (pre-ratification)

Framing pass only. No code, no schema changes, no data touches, no greps
against real stored data until this document is ratified. Implementation
does not begin until the open decisions at the end of this doc have been
explicitly signed off.

## Thesis

**Post hoc provenance reconstruction, for future admissibility, with
epistemic recovery and ancestry admission treated as separate gates.**

## Anchor

**A migrated row is not merely rewritten metadata; it is a future-safe
ancestor candidate.**

---

## Why this framing

Up to and including step 5, every change to the TORMENT provenance
corridor has operated on either new writes (events captured as they
happen) or dead-code cleanup (removing logic that was never
load-bearing). Step 6 is the first step where the provenance corridor
will be modified on **existing stored rows** — rows whose original
provenance was either absent, malformed, or carried in a legacy shape
that predates ProvenanceV1.

That makes step 6 categorically different from steps 1 through 5. Every
prior step tightened how new data enters the corridor. Step 6 decides
whether existing data is allowed into the corridor at all, and under
what reconstruction.

The tempting framing is "cleanup" or "normalization" — we have old
rows, we rewrite them into the new shape, done. That framing is wrong,
because of this single property:

> Once a migrated row carries `source_type == "memory"` (or any other
> admissible source_type), it enters the admissible ancestry corridor
> for the bounded-DFS guard in `cognition/recursion_guard.py`.

The guard walks ancestors and admits any node whose source_type is in
the safe set. A row written by the migration is **indistinguishable**
from a row written by actual user_input capture, from the guard's
perspective, unless we explicitly build a distinction. That means the
migration's normalization rules *are* an ancestry-admission policy, not
a data-cleanup pass.

The doctrinal consequence is the two-gate separation. Every qualifying
legacy row must pass through two distinct decisions, not one:

1. **Epistemic recovery gate.** *What can we honestly reconstruct
   about this row's provenance?* This is an honesty question. What is
   knowable from the row itself, its neighbors, and corpus metadata,
   without inference that exceeds the evidence. A row with a bare
   string `"collective"` is recoverable as "originally a collective
   echo." A row with no provenance field at all is recoverable as
   "unknown." A row synthesized during a debugging session has no
   honest origin to recover.
2. **Ancestry admission gate.** *Given that reconstruction, should this
   row be admitted as a future-safe ancestor?* This is a policy
   question. Even when recovery yields a clean answer, admission can
   be refused on doctrinal grounds. Strong recovery does not imply
   strong admission. A row recovered as "originally a collective echo"
   has strong recovery but **must** fail admission — the guard rejects
   collective_echo anywhere in the walk window, and the migration must
   not create a backdoor around that rejection.

The asymmetry between the two gates is load-bearing:

- A row can pass gate 1 and fail gate 2. (We know what it is; we are
  deliberately declining to admit it.)
- A row cannot pass gate 2 without passing gate 1. (Admission without
  honest recovery is laundering, which is what step 5's guard exists
  to prevent.)

If the two gates are collapsed into one decision, best-effort
reconstruction quietly upgrades itself to admissible truth. That is the
failure mode this framing exists to prevent.

---

## Question 1 — Which exact legacy rows qualify for migration?

Under the two-gate framing, this splits into two sub-questions:

- **1a.** Which rows are honestly recoverable at all?
- **1b.** Of those recoverable, which should be authorized to become
  future-safe ancestor candidates?

### 1a. Epistemic recovery predicate

Expected shapes of rows that might exist in the corpus (actual
distribution TBD — no greps until this framing is ratified):

| Shape | Recoverability | Notes |
|---|---|---|
| Well-formed `ProvenanceV1` dict | Already canonical | Skip entirely |
| Legacy bare string (`"memory"`, `"collective"`, etc.) | Recoverable: source_type inferred from the string; origin beyond the string is unknown | Store `legacy_bare_string=<raw>` in `notes` |
| Dict with valid source_type, missing parent_eids | Recoverable; ancestry chain truncates at this node | Guard will terminate walk cleanly here |
| Dict with invalid or missing source_type | Not recoverable without guessing | Gate-1 FAIL |
| `None` / null / empty string | Not recoverable | Gate-1 FAIL |
| Dict with source_type from a deprecated vocabulary (not in `VALID_SOURCE_TYPES`) | Recoverable only if a deterministic mapping exists | Mapping table required, or gate-1 FAIL |
| Rows with zero event backing (debug artifacts, test seeds) | Not honestly recoverable | Gate-1 FAIL |

The recovery gate is deliberately strict. "Recoverable" means: the
original provenance can be reconstructed from evidence present in or
adjacent to the row, with no inference that exceeds the evidence.
Best-effort guessing is explicitly excluded.

### 1b. Admission predicate

Of the rows that pass gate 1, admission is a separate decision:

- **Bare string → safe source_type.** `"memory"` → admit. `"tool_result"`
  → admit. `"user_input"` → admit.
- **Bare string → rejected class.** `"collective"` → REFUSE (maps to
  collective_echo). `"archivist"` → REFUSE (maps to archivist role).
  `"derived"` → REFUSE (deferred vocabulary).
- **Dict with valid source_type, truncated ancestry.** Admitted at
  depth 1 only. Guard walks to parent_eids, finds none, terminates
  the chain cleanly. No further admission decision needed.
- **Dict with source_type in the rejected set** (`collective_echo`,
  `derived`) → REFUSE regardless of other recoverability.
- **Dict with source_type = role_output, source_role = archivist** →
  REFUSE.
- **Anything else that passes gate 1** → admit with audit trail.

The refusal decision is **recorded, not silently dropped**. A refused
row stays in storage with its provenance reconstructed under gate 1
but explicitly marked as not-admissible under gate 2. This preserves
audit trail without creating ancestry backdoors.

---

## Question 2 — What the migration writes, field-by-field

Under the two-gate framing, fields split into two categories:

### Reconstruction fields (what recovery found)

- `source_type` — inferred from gate-1 analysis; canonical value from
  `VALID_SOURCE_TYPES`, or null if recovery failed
- `source_role` — inferred only when explicitly knowable (e.g. the
  original dict already carried it); otherwise null
- `parent_eids` — only preserved if the original row carried them;
  otherwise empty list
- `notes` — free-text audit trail. Must carry: the original raw
  provenance value (e.g. `legacy_bare_string="collective"`), the
  recovery method used, and the recovery timestamp. This is the
  forensic record of the reconstruction.
- `write_path` — set to `WRITE_MIGRATION` for in-place rewrites of
  existing rows, `WRITE_SYSTEM_IMPORT` for rows brought in from
  external sources

### Admission fields (what the admission gate decided)

Here is the central design decision this framing doc must surface but
not pre-commit: **how does the guard know a migrated row has been
admission-refused?**

Three options, each with trade-offs:

**Option A — Separate boolean field.** Add
`admission_refused: bool = False` to `ProvenanceV1`. The guard checks
this field early and rejects with a new `REASON_MIGRATION_REFUSED` if
true.

- Pros: clean, explicit, doesn't pollute source_type vocabulary;
  refusal reason is orthogonal to origin
- Cons: new field in `ProvenanceV1` schema (non-trivial migration
  surface of its own), new `REASON_*` constant, new gate check in the
  guard

**Option B — Reserved "quarantine" source_type.** Add a new
source_type like `SOURCE_MIGRATION_QUARANTINE = "migration_quarantine"`
and add it to `_REJECTED_SOURCE_TYPES_IN_WALK`. Refused rows are
stored with this source_type. The recovered source_type is stashed in
`notes`.

- Pros: reuses existing rejection machinery (the frozenset is now
  load-bearing as of the #688 fix); no new field; no new REASON
  constant
- Cons: pollutes the source_type vocabulary with a status marker
  (source_type is supposed to describe *origin*, not admission
  status); loses the recovered source_type from its natural field
  unless we stash it elsewhere

**Option C — Don't store refused rows at all.** The migration simply
skips refused rows; they remain in whatever pre-migration shape they
had.

- Pros: simplest; no schema changes; no new logic
- Cons: breaks audit trail; leaves the corpus in a mixed state where
  some rows are migrated and some are not; forces future migrations
  to re-inspect skipped rows; and **worst**: if the guard ever walks
  *into* a skipped row (via a parent_eids chain from a migrated row),
  it hits the same fail-closed logic that caused the step 5 crash
  path. This option **re-opens the hazard step 5 closed**.

**Recommendation: Option A.** The extra schema surface is worth paying
for. Option B conflates origin with status, and once we start using
source_type as a status field we lose the clean separation between
what-something-is and what-we-decided-to-do-with-it. Option C
reintroduces the hazard step 5 eliminated. Option A is the only choice
that preserves the doctrinal invariants.

This is exactly the decision that needs your ratification before any
code is written.

### Additional admission fields (under Option A)

- `admission_refused: bool` — the gate-2 decision
- `admission_reason: str` — human-readable reason, referencing the
  specific gate-2 rule (e.g. `"bare_string_maps_to_rejected_class"`,
  `"source_type_in_rejected_set"`, `"archivist_role"`)
- `admission_policy_version: str` — the version of the admission
  policy this decision was made under. Enables future re-evaluation
  when the policy tightens (see Question 3)

---

## Question 3 — One-shot, idempotent, or resumable?

### Why one-shot is ruled out

A one-shot migration has no story for:

- Policy tightening (future version of the admission rules)
- Corpus growth (new legacy rows discovered in neglected areas)
- Recovery improvement (better reconstruction methods developed after
  the first pass)
- Error recovery (partial failure mid-run)

All of these require the migration to be re-runnable.

### Classical idempotency doesn't quite fit

Classical idempotency says: same input → same output. Under the
two-gate model, this is wrong, because the admission gate's output can
legitimately change between runs:

- Policy tightened → a previously admitted row is now refused
- Policy loosened → a previously refused row is now admitted

The first case (tightening) is safe. The second case (loosening) is a
potential laundering vector and must not happen automatically — it
requires explicit human review.

### Recommended property: monotonic-in-tightness + resumable

The migration must satisfy two properties:

1. **Monotonic-in-tightness.** On a re-run without human review, the
   admission decision can only move in the tightening direction. If
   the stored `admission_policy_version` on a row is older than the
   current policy, the migration re-evaluates the row:
   - New decision = refuse, old = admit → **apply** the update (row
     becomes refused)
   - New decision = admit, old = refuse → **block** the update, flag
     the row for human review, leave refusal in place
   - New decision = same as old → no change, bump policy version
     pointer only

   This preserves the "admission without honest recovery is
   laundering" invariant across re-runs. Loosening requires a human
   explicitly saying "yes, I reviewed this and it's safe."

2. **Resumable.** Long-running migrations must be checkpoint-recoverable.
   The migration writes a cursor/state file that lets it continue
   from where it stopped on crash, abort, or restart. Cursor state
   records the eid of the last row processed. Safe-to-resume means:
   the migration can be aborted at any point and restarted without
   double-writing or skipping rows.

Recovery (gate 1) is purely deterministic and does **not** have the
monotonicity constraint — same input always produces the same
recovery. Only admission (gate 2) has the tightening-only property.

---

## What step 6 is NOT

Explicit scope exclusions, to prevent scope creep during implementation:

- **Not** a notes-field enrichment pass (annotating existing rows with
  retrospective metadata unrelated to provenance reconstruction)
- **Not** a schema upgrade beyond what's strictly required for the
  two-gate model (specifically excluding "tidy up the ProvenanceV1
  schema while we're in there" temptations)
- **Not** a backfill for other missing fields (missing timestamps,
  missing embeddings, etc. — those are separate passes)
- **Not** a performance or storage optimization (no compression,
  re-indexing, or vacuuming)
- **Not** a "clean up the corpus while we're in there" sweep (deleting
  test rows, removing duplicates, collapsing history)
- **Not** an activation of `SOURCE_DERIVED` (deferred vocabulary;
  stays in `_REJECTED_SOURCE_TYPES_IN_WALK`)
- **Not** a doc sweep — `docs/ROADMAP_v2.4.x.md`,
  `docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md`, and
  `docs/RECURSION_SAFETY_POLICY_v2.4.x.md` stay untouched except
  where strictly required to reference the new migration tooling
- **Not** a flip of `TORMENT_ARCHIVIST_WRITEBACK`. The gate stays at
  0. Step 6 is groundwork for a future gate-flip, not the gate-flip
  itself

If any of these get bundled in during implementation, they get split
out into their own steps with their own ratification.

---

## Prior art / input documents

- `docs/PROVENANCE_CONSTANTS_NOTES.md` — pre-step-6 scratch notes on
  the reserved constants (`SOURCE_MEMORY`, `SOURCE_DERIVED`,
  `WRITE_REFLECTION_WRITEBACK`, `WRITE_MIGRATION`,
  `WRITE_SYSTEM_IMPORT`). Provides vocabulary context and the
  "understand and connect, do not delete" stance the migration must
  honor.
- `docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md` — authoritative status
  of each constant. `WRITE_MIGRATION` and `WRITE_SYSTEM_IMPORT`
  should move from "RESERVED" to "ACTIVE (step 6)" on implementation.
- `docs/RECURSION_SAFETY_POLICY_v2.4.x.md` — the doctrine the
  migration must not violate. Particular attention to the "Why this
  exists" section added in step 5, which applies directly: the
  migration cannot create rows that let writeback "trust ancestry it
  should reject."
- `docs/RECURSION_GUARD_TUNING_v2.4.x.md` — the parameter discipline
  the migration must respect, particularly §3 on
  `_REJECTED_SOURCE_TYPES_IN_WALK`. If Option B is chosen instead of
  Option A, this doc also needs an update to register
  `SOURCE_MIGRATION_QUARANTINE`.
- `torment_service/provenance_v1.py` — the canonical schema.
  `normalize_parent` is the gate-1 helper the migration will reuse.
  Any new admission fields land here.
- `cognition/recursion_guard.py` — the enforcement point. Any
  migration design that lets refused rows flow through without the
  guard catching them is wrong.

---

## Open decisions awaiting ratification

Before any code is written, the following need explicit sign-off:

1. **Option A vs B vs C for refused rows.** Recommendation: **A**
   (separate `admission_refused` boolean field). Rationale above.
2. **Monotonic-in-tightness + resumable run semantics.**
   Recommendation: **accept both**. Rationale above.
3. **Scope of first migration run.** Does step 6 implementation cover
   `WRITE_MIGRATION` only, or both `WRITE_MIGRATION` and
   `WRITE_SYSTEM_IMPORT`? The two producers share the two-gate model
   but may need different recovery predicates — system imports pull
   from external sources that may carry their own provenance
   conventions. Recommendation: **WRITE_MIGRATION first, in its own
   commit, then WRITE_SYSTEM_IMPORT in a follow-up commit under the
   same framing**. Keeps the blast radius small.
4. **Recovery predicate strictness.** The gate-1 criteria in Question
   1a are deliberately strict. Edge cases (empty-string legacy
   provenance, dict with `source_type="unknown"`, etc.) default to
   FAIL unless there's explicit reason to admit them. Ratify or
   revise.
5. **Policy version scheme.** How is `admission_policy_version`
   named? Calendar-based? Semver? Tied to doctrine doc version?
   Recommendation: **tied to doctrine doc version**, e.g.
   `"v2.4.x-step6-a"` on first activation, bumped only when the
   admission rules themselves change. Traceable back to a specific
   doctrine doc revision.
6. **Dry-run mode as first deliverable.** Before the migration ever
   writes a single row, should there be a dry-run mode that reports
   "here is what each row in the corpus would become under the
   current policy" without making changes? Recommendation: **yes,
   dry-run first, actual writes gated behind a separate flag**. Same
   "fix before flipping" discipline used in step 5 for the archivist
   gate.

---

## Next move after this framing is ratified

1. Address any revisions requested on the framing doc
2. Produce a separate **implementation plan** that translates the
   ratified framing into concrete code changes:
   - Files to modify (with specific targets)
   - Schema changes (new fields in `ProvenanceV1`)
   - Test additions (covering the two gates, the refusal path, and
     the monotonic-in-tightness re-run behavior)
   - Doc updates (registry, tuning doc, RSP doc where the migration
     touches enforcement surface)
   - Dry-run CLI shape
3. Ratify the implementation plan
4. Begin **commit A** of step 6 implementation under the same A/B
   split discipline used in step 5 — commit A lands the new machinery
   with dry-run only; commit B lands actual writes once commit A is
   reviewed and validated against a real corpus

**No code before the implementation plan is ratified.**
**No implementation plan before this framing is ratified.**
